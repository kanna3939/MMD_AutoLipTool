from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

from gui_wx.ui_state import UiState, format_whisper_failure_notice
from gui_wx.voice_only_errors import classify_voice_only_analysis_error
from src.core import (
    DiagnosticFailureInput,
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    EffectiveMorphFrameInput,
    EffectiveTailInput,
    EffectiveWriterInput,
    EffectiveWriterInputState,
    OutputDiagnosticsSnapshot,
    WhisperDiagnosticsSummary,
    WhisperModelDiagnosticsItem,
    VmdWriterParameters,
    VowelTimingPlan,
    build_output_diagnostics_snapshot,
    evaluate_whisper_identity_status,
    resolve_vmd_writer_timing_plan,
    GenerationState,
)
from src.core.generation_presets import GenerationSettings
from src.core.event_adjustment import AdjustmentLayerSnapshot
from src.core.morph_name_sets import (
    JAPANESE_OUTPUT_NAMES,
    get_builtin_morph_name_set,
    validate_output_morph_names,
)
from src.core.pipeline import PipelineError
from src.core.text_processing import TextProcessingError
from src.core.whisper_timing import WhisperTimingError
from src.core.whisper_model_runtime import WhisperModelRuntimeError
from src.core.whisper_models import (
    EXPECTED_WHISPER_VERSION,
    MANIFEST_SCHEMA_VERSION,
    build_manifest_identity,
)
from src.core.transition_diagnostics import build_transition_diagnostic_summary
from src.core.final_output_projection import shared_output_consumer_view
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)


def _optional_path(value: Any) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)


def resolve_source_audio_path_from_ui_state(state: UiState) -> Path | None:
    """Resolve the original source audio path without normalizing its case."""
    source_path = None
    if state.selected_audio_input is not None:
        source_path = getattr(state.selected_audio_input, "source_path", None)
    return _optional_path(source_path or state.selected_wav_path)


def _effective_wav_path(state: UiState) -> Path | None:
    analysis_wav_path = None
    if state.selected_analysis_wav is not None:
        analysis_wav_path = getattr(state.selected_analysis_wav, "analysis_wav_path", None)
    return _optional_path(analysis_wav_path or state.selected_wav_path)


def _safe_storage_projection(state: UiState) -> tuple[str, str]:
    kind = getattr(state.whisper_model_selection, "storage_location_kind", None)
    display = getattr(state.whisper_model_selection, "storage_location_display", None)
    raw_path = state.whisper_model_selection.storage_root_display
    if kind in {"default", "user_specified"} and display:
        return kind, display
    if not raw_path:
        if kind == "not_applicable":
            return "not_applicable", "保存先を確認できません"
        return "unresolved", "保存先を確認できません"
    tail = Path(raw_path).name
    if kind == "default":
        return "default", "既定保存先 (models)"
    if tail and tail not in {".", "\\", "/"}:
        return "user_specified", f"ユーザー指定 ({tail})"
    return "user_specified", "ユーザー指定"


def _model_display_name(specs: Sequence[Any], model_key: str | None) -> str | None:
    if model_key is None:
        return None
    item = next((spec for spec in specs if spec.model_key == model_key), None)
    return None if item is None else item.display_name


def _safe_whisper_notice(failure_class: str, detail_code: str | None) -> str:
    if failure_class == "cancelled":
        return "解析をキャンセルしました。必要に応じて再解析してください。"
    if failure_class == "integrity_mismatch":
        return "Whisperモデルの検証に失敗しました。モデルを確認して再解析してください。"
    if failure_class == "memory_failure":
        return "Whisperモデルを読み込むメモリが不足しました。別のモデルを選択してください。"
    if failure_class == "transcribe_failure":
        return "Whisperの書き起こしに失敗しました。音声とモデルを確認して再解析してください。"
    if failure_class == "load_failure":
        return "Whisperモデルの読み込みに失敗しました。モデルを確認してください。"
    if failure_class == "model_unavailable":
        return format_whisper_failure_notice(detail_code or "model_unavailable")
    return format_whisper_failure_notice(detail_code)


def build_whisper_diagnostics_summary(
    state: UiState,
    *,
    analysis_result_valid: bool,
    analysis_pending_rebuild: bool,
    analysis_in_progress: bool,
    preview_projection_status: str | None = None,
) -> WhisperDiagnosticsSummary:
    """Project B3/B5 state to one immutable, safe diagnostics summary."""
    selection = state.whisper_model_selection
    specs = tuple(selection.model_specs)
    availability_by_key = {item.model_key: item for item in selection.availability}
    model_items = tuple(
        WhisperModelDiagnosticsItem(
            model_key=spec.model_key,
            display_name=spec.display_name,
            size_bytes=spec.size_bytes,
            vram_hint=spec.vram_hint,
            speed_hint=spec.speed_hint,
            recommended_use=spec.recommended_use,
            expected_manifest_identity=build_manifest_identity(
                EXPECTED_WHISPER_VERSION,
                spec.model_key,
                spec.sha256,
            ),
            availability_status=(
                availability_by_key[spec.model_key].artifact_status
                if spec.model_key in availability_by_key
                else "unknown"
            ),
            availability_failure_code=(
                availability_by_key[spec.model_key].failure_code
                if spec.model_key in availability_by_key
                else None
            ),
        )
        for spec in specs
    )
    spec_by_key = {spec.model_key: spec for spec in specs}
    selected_spec = spec_by_key.get(selection.selected_model_key)
    active_spec = spec_by_key.get(selection.active_model_key)
    selected_availability = availability_by_key.get(selection.selected_model_key)
    active_availability = availability_by_key.get(selection.active_model_key)
    selected_key = selection.selected_model_key if selected_spec is not None else None
    active_key = selection.active_model_key if active_spec is not None else None
    active_identity = selection.active_manifest_identity or None
    loaded_key = (
        selection.loaded_whisper_model_key
        if selection.loaded_whisper_model_key in spec_by_key
        else None
    )
    loaded_identity = selection.loaded_whisper_manifest_identity
    analysis_key = (
        selection.analysis_whisper_model_key
        if selection.analysis_whisper_model_key in spec_by_key
        else None
    )
    analysis_identity = selection.analysis_whisper_manifest_identity
    failure_class = selection.whisper_failure_class
    detail_code = selection.whisper_failure_detail_code
    storage_kind, storage_display = _safe_storage_projection(state)
    analysis_identity_status = evaluate_whisper_identity_status(
        active_key,
        active_identity,
        analysis_key,
        analysis_identity,
    )
    runtime_identity_status = evaluate_whisper_identity_status(
        active_key,
        active_identity,
        loaded_key,
        loaded_identity,
        unloaded_is_distinct=bool(specs),
    )
    if not specs and not active_identity:
        analysis_identity_status = "not_applicable"
        runtime_identity_status = "not_applicable"
    if analysis_identity_status in {"incomplete", "mismatch"}:
        preview_projection_status = "analysis_required"
    gate_failure_codes = {
        "whisper_version_mismatch",
        "package_missing",
        "package_import_failed",
        "manifest_version_mismatch",
    }
    if detail_code in gate_failure_codes:
        package_gate_status = "failed"
    elif loaded_key is not None and loaded_identity:
        package_gate_status = "passed"
    else:
        package_gate_status = "not_checked"
    if preview_projection_status is None:
        if analysis_in_progress or analysis_pending_rebuild:
            preview_projection_status = "analysis_required"
        elif analysis_result_valid and state.current_timing_plan is not None:
            preview_projection_status = "ready"
        else:
            preview_projection_status = "unavailable"
    if failure_class == "none":
        recoverability = "not_applicable"
    elif failure_class == "cancelled":
        recoverability = "cancelled_by_user"
    elif detail_code in {"storage_write_failed", "settings_save_failed"}:
        recoverability = "select_file_again"
    else:
        recoverability = "retry_possible"
    package_version = EXPECTED_WHISPER_VERSION
    return WhisperDiagnosticsSummary(
        models=model_items,
        selected_model_key=selected_key,
        selected_model_display_name=(None if selected_spec is None else selected_spec.display_name),
        selected_manifest_identity=(
            None
            if selected_spec is None
            else build_manifest_identity(
                EXPECTED_WHISPER_VERSION,
                selected_spec.model_key,
                selected_spec.sha256,
            )
        ),
        selected_availability_status=(
            None if selected_availability is None else selected_availability.artifact_status
        ),
        active_model_key=active_key,
        active_model_display_name=(None if active_spec is None else active_spec.display_name),
        active_manifest_identity=active_identity,
        active_availability_status=(
            None if active_availability is None else active_availability.artifact_status
        ),
        loaded_model_key=loaded_key,
        loaded_model_display_name=_model_display_name(specs, loaded_key),
        loaded_manifest_identity=loaded_identity,
        analysis_model_key=analysis_key,
        analysis_model_display_name=_model_display_name(specs, analysis_key),
        analysis_manifest_identity=analysis_identity,
        manifest_schema_version=(MANIFEST_SCHEMA_VERSION if specs else None),
        package_version=package_version,
        package_gate_status=package_gate_status,
        availability_scan_status=(
            selection.availability_scan_status if specs else "not_applicable"
        ),
        availability_scan_failure_code=selection.availability_scan_failure_code,
        management_operation=selection.management_operation,
        management_phase=selection.management_phase,
        management_busy=selection.management_busy,
        management_job_id=selection.management_job_id,
        management_model_key=selection.management_model_key,
        management_received_bytes=selection.management_received_bytes,
        management_expected_bytes=selection.management_expected_bytes,
        management_failure_code=selection.management_failure_code,
        management_cleanup_status=selection.management_cleanup_status,
        active_config_status=(
            selection.active_config_status if specs else "not_applicable"
        ),
        active_config_reason=(selection.active_config_reason if specs else None),
        panel_revision=selection.panel_revision,
        analysis_rebuild_reason=selection.analysis_rebuild_reason,
        failure_class=failure_class,
        failure_detail_code=detail_code,
        safe_failure_notice=_safe_whisper_notice(failure_class, detail_code)
        if failure_class != "none"
        else "",
        recoverability=recoverability,
        analysis_identity_status=analysis_identity_status,
        runtime_identity_status=runtime_identity_status,
        storage_location_kind=storage_kind,
        storage_location_display=storage_display,
        application_busy=state.is_busy,
        transcription_text_present=bool(state.transcription_text),
        transcription_edit_available=bool(
            state.input_mode == "voice_only"
            and state.transcription_text
            and not state.is_busy
        ),
        preview_projection_status=preview_projection_status,
    )


def build_diagnostic_failure_input(
    error: Exception,
    *,
    input_mode: str,
) -> DiagnosticFailureInput:
    """Convert an analysis exception into a stable, UI-independent failure DTO."""
    exception_type = type(error).__name__
    is_whisper_error = isinstance(error, (WhisperTimingError, WhisperModelRuntimeError))
    if isinstance(error, WhisperModelRuntimeError):
        phase = "whisper_model_runtime"
    elif isinstance(error, WhisperTimingError):
        phase = "whisper_transcribe"
    elif isinstance(error, TextProcessingError):
        phase = "text_convert"
    else:
        phase = "pipeline_build"

    if input_mode == "voice_only":
        presentation = classify_voice_only_analysis_error(error)
        code = presentation.category
        summary = presentation.summary
        action = presentation.action
    else:
        if is_whisper_error:
            code = "text_audio_whisper_failed"
            summary = "音声タイミング解析に失敗しました。"
            action = "音声ファイルとWhisperの状態を確認して再解析してください。"
        elif isinstance(error, TextProcessingError):
            code = "text_audio_text_conversion_failed"
            summary = "TEXTの日本語読み変換に失敗しました。"
            action = "TEXTの内容と文字コードを確認して再解析してください。"
        elif isinstance(error, PipelineError):
            code = "text_audio_pipeline_failed"
            summary = "リップシンク解析結果を生成できませんでした。"
            action = "入力内容を確認して再解析してください。"
        else:
            code = "text_audio_analysis_failed"
            summary = "解析を完了できませんでした。"
            action = "入力内容を確認して再解析してください。"

    if is_whisper_error:
        detail = action
    else:
        detail = f"{action}\n詳細 ({exception_type}): {error}"
    failure_class = getattr(error, "failure_class", "transcribe_failure")
    recoverability = (
        "cancelled_by_user"
        if failure_class == "cancelled"
        else "retry_possible"
    )
    return DiagnosticFailureInput(
        code=code,
        source_severity="error",
        phase=phase,
        recoverability=recoverability,
        identity_context=(
            ("category", code),
            ("exception_type", exception_type),
        ),
        summary=summary,
        detail=detail,
    )


def _diagnostic_timing_plan(
    state: UiState,
    *,
    analysis_in_progress: bool,
) -> DiagnosticTimingPlanInput | None:
    if analysis_in_progress or state.current_timing_plan is None:
        return None

    timing_plan = state.current_timing_plan
    if not isinstance(timing_plan, VowelTimingPlan):
        raise ValueError("current_timing_plan must be VowelTimingPlan")

    resolved_timing_plan = timing_plan
    if any(point.duration_sec <= 0.0 for point in timing_plan.timeline):
        wav_analysis = state.selected_wav_analysis
        if wav_analysis is None:
            raise ValueError(
                "selected_wav_analysis is required for non-positive timeline durations"
            )
        speech_start_sec = getattr(wav_analysis, "speech_start_sec", None)
        speech_end_sec = getattr(wav_analysis, "speech_end_sec", None)
        if speech_start_sec is None or speech_end_sec is None:
            raise ValueError(
                "speech interval is required for non-positive timeline durations"
            )
        resolved_timing_plan = resolve_vmd_writer_timing_plan(
            timing_plan,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
        )

    return DiagnosticTimingPlanInput.from_timing_plan(resolved_timing_plan)


def build_output_diagnostics_snapshot_from_ui_state(
    state: UiState,
    *,
    vmd_model_name: str = "AutoLipTool",
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
    analysis_in_progress: bool = False,
    effective_shape_plan: object | None = None,
    effective_writer_input_state: EffectiveWriterInputState = "not_applicable",
    effective_writer_input_failure_reason: str | None = None,
    generation_state: GenerationState | None = None,
    active_preset_display_name: str | None = None,
    output_morph_names: Sequence[str] = JAPANESE_OUTPUT_NAMES,
    projection_generation: int = 0,
    shared_final_output_context: object | None = None,
) -> OutputDiagnosticsSnapshot:
    """Build the B2 diagnostics snapshot for the current wx workspace state."""
    normalized_output_morph_names = validate_output_morph_names(output_morph_names)
    resolved_morph_name_set = next(
        item
        for item in (
            get_builtin_morph_name_set("builtin:japanese-vowels"),
            get_builtin_morph_name_set("builtin:latin-vowels"),
        )
        if item.output_names == normalized_output_morph_names
    )
    timing_plan = _diagnostic_timing_plan(
        state,
        analysis_in_progress=analysis_in_progress,
    )
    if analysis_in_progress:
        analysis_result_valid = False
        analysis_pending_rebuild = bool(
            state.analysis_result_valid or state.analysis_pending_rebuild
        )
        existing_vmd_save_ready = False
    else:
        analysis_result_valid = state.analysis_result_valid
        analysis_pending_rebuild = state.analysis_pending_rebuild
        existing_vmd_save_ready = state.vmd_save_ready

    effective_writer_input: EffectiveWriterInput | None = None
    base_plan_identity_digest: str | None = None
    resolved_effective_state = effective_writer_input_state
    resolved_failure_reason = effective_writer_input_failure_reason
    shared_identity = None
    shared_restrictions: tuple[object, ...] = ()
    shared_restriction_event_targets: tuple[object, ...] = ()
    if shared_final_output_context is not None:
        candidate = getattr(shared_final_output_context, "candidate", None)
        projection = getattr(shared_final_output_context, "projection", None)
        identity = getattr(shared_final_output_context, "identity", None)
        issuer_context = getattr(shared_final_output_context, "issuer_context", None)
        if (
            candidate is None
            or getattr(candidate, "state", None) != "valid"
            or getattr(candidate, "plan", None) is None
            or projection is None
            or identity is None
            or issuer_context is None
        ):
            raise ValueError("shared final-output context is invalid")
        legacy_context = issuer_context.legacy_context
        effective_shape_plan = legacy_context.effective_plan_snapshot
        if effective_shape_plan is None:
            raise ValueError("shared final-output effective plan is missing")
        expected_names = tuple(name for _, name in identity.input_identity.output_mapping)
        if expected_names != normalized_output_morph_names:
            raise ValueError("shared final-output mapping differs from diagnostics mapping")
        shared_identity = identity
        shared_restrictions = tuple(candidate.plan.restrictions)
        shared_restriction_event_targets = tuple(
            shared_final_output_context.restriction_event_targets
        )
        resolved_effective_state = "ready"
        resolved_failure_reason = None
    if effective_shape_plan is not None:
        identity = getattr(effective_shape_plan, "base_plan_identity", None)
        base_plan_identity_digest = getattr(identity, "digest", None)
    if resolved_effective_state == "ready":
        try:
            if effective_shape_plan is None:
                raise ValueError("effective_shape_plan is required for ready state")
            if shared_final_output_context is not None:
                morph_frames = tuple(
                    (
                        int(point.frame_no),
                        str(point.output_morph_name),
                        float(point.binary32_value),
                    )
                    for point in shared_final_output_context.projection.wire_points
                )
            else:
                morph_frames = build_morph_frames_from_effective_shape_plan(
                    effective_shape_plan,
                    output_morph_names=normalized_output_morph_names,
                )
            tails: list[EffectiveTailInput] = []
            for shape_ordinal, shape in enumerate(effective_shape_plan.shapes):
                tail = shape.resolved_tail
                if tail is None:
                    continue
                tails.append(
                    EffectiveTailInput(
                        shape_ordinal=shape_ordinal,
                        vowel=shape.vowel,
                        effective_hold_frames=tail.effective_hold_frames,
                        effective_softness_frames=tail.effective_softness_frames,
                        effective_slope_ratio=tail.slope_ratio,
                        has_slope_midpoint=tail.has_slope_midpoint,
                    )
                )
            effective_writer_input = EffectiveWriterInput(
                shape_count=len(effective_shape_plan.shapes),
                morph_frames=tuple(
                    EffectiveMorphFrameInput(
                        frame_no=frame_no,
                        morph_name=morph_name,
                        value=value,
                    )
                    for frame_no, morph_name, value in morph_frames
                ),
                tails=tuple(tails),
                allowed_morph_names=normalized_output_morph_names,
            )
        except (AttributeError, TypeError, ValueError):
            resolved_effective_state = "invalid"
            resolved_failure_reason = "adapter_failed"

    resolved_generation_state = generation_state
    if resolved_generation_state is None:
        try:
            resolved_generation_state = GenerationState(
                GenerationSettings(
                    closing_hold_frames=closing_hold_frames,
                    closing_softness_frames=closing_softness_frames,
                    long_vowel_mode=state.generation_state.generation_settings.long_vowel_mode,
                ),
                state.generation_state.active_preset_id,
            )
        except (AttributeError, TypeError, ValueError):
            resolved_generation_state = GenerationState(GenerationSettings())
    generation_settings = resolved_generation_state.generation_settings
    adjustment_snapshot = state.current_adjustment_snapshot
    adjusted_event_count = (
        0
        if adjustment_snapshot is None
        else len(adjustment_snapshot.adjustments)
    )
    effective_hold_run_count: int | None = None
    effective_decay_run_count: int | None = None
    if resolved_effective_state == "ready" and effective_shape_plan is not None:
        effective_hold_run_count = sum(
            1
            for run in effective_shape_plan.long_vowel_runs
            if run.resolved_mode == "hold"
        )
        effective_decay_run_count = sum(
            1
            for run in effective_shape_plan.long_vowel_runs
            if run.resolved_mode == "decay"
        )
    resolved_active_preset_id = resolved_generation_state.active_preset_id
    if resolved_active_preset_id is not None and active_preset_display_name is None:
        resolved_active_preset_id = None
    resolved_active_preset_display_name = (
        active_preset_display_name
        if resolved_active_preset_id is not None
        else None
    )
    preview_projection_status = (
        "analysis_required"
        if analysis_in_progress or analysis_pending_rebuild
        else (
            "ready"
            if analysis_result_valid and state.current_timing_plan is not None
            else "unavailable"
        )
    )
    whisper_summary = build_whisper_diagnostics_summary(
        state,
        analysis_result_valid=analysis_result_valid,
        analysis_pending_rebuild=analysis_pending_rebuild,
        analysis_in_progress=analysis_in_progress,
        preview_projection_status=preview_projection_status,
    )
    snapshot_input = DiagnosticSnapshotInput(
        input_mode=state.input_mode,
        text_path=_optional_path(state.selected_text_path),
        text_content_present=bool(state.selected_text_content),
        source_audio_path=resolve_source_audio_path_from_ui_state(state),
        effective_wav_path=_effective_wav_path(state),
        analysis_text_present=bool(
            state.analysis_text_content or state.transcription_text
        ),
        analysis_result_valid=analysis_result_valid,
        analysis_pending_rebuild=analysis_pending_rebuild,
        timing_plan=timing_plan,
        existing_vmd_save_ready=existing_vmd_save_ready,
        writer_parameters=VmdWriterParameters(
            vmd_model_name=vmd_model_name,
            closing_hold_frames=generation_settings.closing_hold_frames,
            closing_softness_frames=generation_settings.closing_softness_frames,
        ),
        failure=state.current_diagnostic_failure,
        analysis_cancelled=state.analysis_cancelled,
        effective_writer_input_state=resolved_effective_state,
        effective_writer_input=effective_writer_input,
        effective_writer_input_failure_reason=resolved_failure_reason,
        base_plan_identity_digest=base_plan_identity_digest,
        adjustment_present=adjusted_event_count > 0,
        adjusted_event_count=adjusted_event_count,
        active_long_vowel_mode=generation_settings.long_vowel_mode,
        active_preset_id=resolved_active_preset_id,
        active_preset_display_name=resolved_active_preset_display_name,
        effective_long_vowel_hold_run_count=effective_hold_run_count,
        effective_long_vowel_decay_run_count=effective_decay_run_count,
        active_model_profile_id=state.model_profile_state.active_model_profile_id,
        active_model_profile_display_name=state.active_model_profile_display_name,
        active_profile_baseline_preset_id=(
            state.model_profile_state.active_profile_baseline_preset_id
        ),
        baseline_preset_display_name=state.baseline_preset_display_name,
        model_profile_resolution_status=(
            state.model_profile_state.resolution_status.value
        ),
        model_profile_resolution_reason_code=(
            state.model_profile_state.resolution_reason_code
        ),
        resolved_morph_name_set_id=resolved_morph_name_set.set_id,
        resolved_morph_name_set_display_name=resolved_morph_name_set.display_name,
        long_vowel_mode_override_count=(
            0
            if adjustment_snapshot is None
            else sum(
                1
                for item in adjustment_snapshot.adjustments
                if item.long_vowel_mode is not None
            )
        ),
        whisper_summary=whisper_summary,
        projection_generation=projection_generation,
        shared_final_output_identity=shared_identity,
        shared_final_output_restrictions=shared_restrictions,
        shared_final_output_restriction_event_targets=(
            shared_restriction_event_targets
        ),
    )
    return build_output_diagnostics_snapshot(snapshot_input)


def capture_shared_output_diagnostics_seed(
    state: UiState,
    *,
    vmd_model_name: str = "AutoLipTool",
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
    generation_state: GenerationState | None = None,
    timing_plan=None,
    adjustment_snapshot: AdjustmentLayerSnapshot | None = None,
    active_preset_display_name: str | None = None,
    output_morph_names: Sequence[str] = JAPANESE_OUTPUT_NAMES,
    projection_generation: int = 0,
) -> DiagnosticSnapshotInput:
    """Capture immutable diagnostic inputs before the B3 worker starts."""
    normalized_names = validate_output_morph_names(output_morph_names)
    name_set = next(
        item
        for item in (
            get_builtin_morph_name_set("builtin:japanese-vowels"),
            get_builtin_morph_name_set("builtin:latin-vowels"),
        )
        if item.output_names == normalized_names
    )
    resolved_generation_state = generation_state or state.generation_state
    settings = resolved_generation_state.generation_settings
    resolved_adjustment_snapshot = (
        state.current_adjustment_snapshot
        if adjustment_snapshot is None
        else adjustment_snapshot
    )
    active_preset_id = resolved_generation_state.active_preset_id
    if active_preset_id is not None and active_preset_display_name is None:
        active_preset_id = None
    return DiagnosticSnapshotInput(
        input_mode=state.input_mode,
        text_path=_optional_path(state.selected_text_path),
        text_content_present=bool(state.selected_text_content),
        source_audio_path=resolve_source_audio_path_from_ui_state(state),
        effective_wav_path=_effective_wav_path(state),
        analysis_text_present=bool(
            state.analysis_text_content or state.transcription_text
        ),
        analysis_result_valid=state.analysis_result_valid,
        analysis_pending_rebuild=state.analysis_pending_rebuild,
        timing_plan=(
            _diagnostic_timing_plan(state, analysis_in_progress=False)
            if timing_plan is None
            else timing_plan
        ),
        existing_vmd_save_ready=state.vmd_save_ready,
        writer_parameters=VmdWriterParameters(
            vmd_model_name=vmd_model_name,
            closing_hold_frames=settings.closing_hold_frames,
            closing_softness_frames=settings.closing_softness_frames,
        ),
        failure=state.current_diagnostic_failure,
        analysis_cancelled=state.analysis_cancelled,
        effective_writer_input_state="not_applicable",
        effective_writer_input=None,
        adjustment_present=bool(
            resolved_adjustment_snapshot is not None
            and resolved_adjustment_snapshot.adjustments
        ),
        adjusted_event_count=(
            0
            if resolved_adjustment_snapshot is None
            else len(resolved_adjustment_snapshot.adjustments)
        ),
        active_long_vowel_mode=settings.long_vowel_mode,
        active_preset_id=active_preset_id,
        active_preset_display_name=(
            active_preset_display_name if active_preset_id is not None else None
        ),
        long_vowel_mode_override_count=(
            0
            if adjustment_snapshot is None
            else sum(
                1
                for item in adjustment_snapshot.adjustments
                if item.long_vowel_mode is not None
            )
        ),
        active_model_profile_id=state.model_profile_state.active_model_profile_id,
        active_model_profile_display_name=state.active_model_profile_display_name,
        active_profile_baseline_preset_id=(
            state.model_profile_state.active_profile_baseline_preset_id
        ),
        baseline_preset_display_name=state.baseline_preset_display_name,
        model_profile_resolution_status=(
            state.model_profile_state.resolution_status.value
        ),
        model_profile_resolution_reason_code=(
            state.model_profile_state.resolution_reason_code
        ),
        resolved_morph_name_set_id=name_set.set_id,
        resolved_morph_name_set_display_name=name_set.display_name,
        whisper_summary=build_whisper_diagnostics_summary(
            state,
            analysis_result_valid=state.analysis_result_valid,
            analysis_pending_rebuild=state.analysis_pending_rebuild,
            analysis_in_progress=False,
            preview_projection_status=(
                "analysis_required"
                if state.analysis_pending_rebuild
                else (
                    "ready"
                    if state.analysis_result_valid
                    and state.current_timing_plan is not None
                    else "unavailable"
                )
            ),
        ),
        projection_generation=projection_generation,
    )


def build_shared_output_diagnostics_snapshot(
    seed: DiagnosticSnapshotInput,
    shared_context: object,
) -> OutputDiagnosticsSnapshot:
    """Build B3 diagnostics from the validated shared wire projection."""
    if not isinstance(seed, DiagnosticSnapshotInput):
        raise TypeError("seed must be DiagnosticSnapshotInput")
    consumer_view = shared_output_consumer_view(shared_context)
    return _build_shared_output_diagnostics_snapshot_from_consumer_view(
        seed,
        shared_context,
        consumer_view,
    )


def _build_shared_output_diagnostics_snapshot_from_consumer_view(
    seed: DiagnosticSnapshotInput,
    shared_context: object,
    consumer_view: Any,
) -> OutputDiagnosticsSnapshot:
    candidate = consumer_view.candidate
    projection = consumer_view.projection
    identity = consumer_view.identity
    issuer_context = getattr(shared_context, "issuer_context", None)
    if (
        candidate is None
        or getattr(candidate, "state", None) != "valid"
        or getattr(candidate, "plan", None) is None
        or projection is None
        or identity is None
        or issuer_context is None
    ):
        raise ValueError("shared final-output context is invalid")
    effective_plan = issuer_context.legacy_context.effective_plan_snapshot
    if effective_plan is None:
        raise ValueError("shared final-output effective plan is missing")
    morph_frames = tuple(
        EffectiveMorphFrameInput(
            frame_no=point.frame_no,
            morph_name=point.output_morph_name,
            value=point.binary32_value,
        )
        for point in projection.wire_points
    )
    tails: list[EffectiveTailInput] = []
    for shape_ordinal, shape in enumerate(effective_plan.shapes):
        tail = shape.resolved_tail
        if tail is None:
            continue
        tails.append(
            EffectiveTailInput(
                shape_ordinal=shape_ordinal,
                vowel=shape.vowel,
                effective_hold_frames=tail.effective_hold_frames,
                effective_softness_frames=tail.effective_softness_frames,
                effective_slope_ratio=tail.slope_ratio,
                has_slope_midpoint=tail.has_slope_midpoint,
            )
        )
    effective_input = EffectiveWriterInput(
        shape_count=len(effective_plan.shapes),
        morph_frames=morph_frames,
        tails=tuple(tails),
        allowed_morph_names=tuple(name for _, name in identity.input_identity.output_mapping),
    )
    transition_binding = consumer_view.transition_binding
    cleanup_binding = consumer_view.cleanup_binding
    transition_identity = identity
    if transition_binding is not None and cleanup_binding is not None:
        transition_upstream = getattr(cleanup_binding, "upstream_context", None)
        if (
            transition_upstream is None
            or transition_upstream.transition_binding != transition_binding
        ):
            raise ValueError("cleanup transition source differs from its upstream context")
        transition_identity = transition_upstream.identity
    transition_summary = (
        None
        if transition_binding is None
        else build_transition_diagnostic_summary(transition_binding, transition_identity)
    )
    snapshot_input = replace(
        seed,
        effective_writer_input_state="ready",
        effective_writer_input=effective_input,
        effective_writer_input_failure_reason=None,
        base_plan_identity_digest=effective_plan.base_plan_identity.digest,
        effective_long_vowel_hold_run_count=sum(
            1 for run in effective_plan.long_vowel_runs if run.resolved_mode == "hold"
        ),
        effective_long_vowel_decay_run_count=sum(
            1 for run in effective_plan.long_vowel_runs if run.resolved_mode == "decay"
        ),
        shared_final_output_identity=identity,
        shared_final_output_restrictions=tuple(candidate.plan.restrictions),
        shared_final_output_restriction_event_targets=tuple(
            shared_context.restriction_event_targets
        ),
        transition_summary=transition_summary,
        cleanup_summary=consumer_view.cleanup_summary,
    )
    return build_output_diagnostics_snapshot(snapshot_input)


def build_shared_output_failure_diagnostics_snapshot(
    seed: DiagnosticSnapshotInput,
    *,
    status: str,
    issues: Sequence[Any],
) -> OutputDiagnosticsSnapshot:
    """Map a failed B2 candidate to the existing VMD-input ERROR contract."""
    if not isinstance(seed, DiagnosticSnapshotInput):
        raise TypeError("seed must be DiagnosticSnapshotInput")
    if status not in {"invalid", "unavailable", "stale"}:
        raise ValueError("status is not a shared-output failure")
    issue_details = tuple(
        f"{getattr(issue, 'reason_code', 'unknown')}"
        + (
            f" @ {getattr(issue, 'stage', 'unknown')}: {getattr(issue, 'detail', '')}"
            if getattr(issue, "detail", "")
            else ""
        )
        for issue in issues
    )
    failure_reason = f"MS31 final output {status}"
    if issue_details:
        failure_reason = f"{failure_reason}: " + "; ".join(issue_details)
    snapshot = build_output_diagnostics_snapshot(
        replace(
            seed,
            effective_writer_input_state="invalid",
            effective_writer_input=None,
            effective_writer_input_failure_reason=failure_reason,
            shared_final_output_identity=None,
            shared_final_output_restrictions=(),
            shared_final_output_restriction_event_targets=(),
        )
    )
    return replace(
        snapshot,
        items=tuple(
            replace(item, detail=failure_reason)
            if item.code == "effective_writer_input_unavailable"
            else item
            for item in snapshot.items
        ),
    )


def _display_path(value: str | None) -> str:
    return value if value is not None else "(未設定)"


def _display_bool(value: bool) -> str:
    return "あり" if value else "なし"


def _analysis_state(
    snapshot: OutputDiagnosticsSnapshot,
    *,
    analysis_in_progress: bool,
) -> str:
    summary = snapshot.analysis_summary
    if analysis_in_progress:
        return "解析中"
    if summary.analysis_pending_rebuild:
        return "再解析が必要"
    if summary.analysis_result_valid and summary.event_count > 0:
        return "解析済み"
    return "未解析"


def format_output_diagnostics_info(
    snapshot: OutputDiagnosticsSnapshot,
    *,
    analysis_in_progress: bool = False,
) -> str:
    """Format the B3 RightPane Info sections from snapshot summaries only."""
    input_summary = snapshot.input_summary
    analysis_summary = snapshot.analysis_summary
    generation_summary = snapshot.generation_summary
    whisper_summary = snapshot.whisper_summary
    saveability = snapshot.saveability
    cleanup_summary = snapshot.cleanup_summary
    if cleanup_summary is None:
        cleanup_lines = ("[自動整理候補]", "状態: 未使用")
    elif cleanup_summary.application_origin == "adopted_default":
        retained_reason_count = sum(len(reasons) for reasons in cleanup_summary.protected_reasons)
        status_text = {
            "cleanup": "通常適用（採択済み）",
            "scope_excluded": "自動整理対象外（現在の入力は採択条件外）",
            "no_applicable": "適用対象なし",
        }.get(cleanup_summary.selection_kind, "通常状態不明")
        reason_text = {
            "exact_collinear_key_reduction_adopted": "曲線を厳密に保つキー整理を採択済み",
            "input_mode_outside_adopted_scope": "現在の入力形式は採択対象外",
            "no_applicable_cleanup_component": "現在の入力に適用できる整理項目がありません",
        }.get(cleanup_summary.selection_reason, "採択条件を確認できません")
        key_text = {
            "applied": "曲線を変えずに省略したキー",
            "not_applied": "scope外のため保持したキー",
            "not_applicable": "対象外のキー",
        }.get(cleanup_summary.key_component_state, "キー")
        cleanup_lines = (
            "[自動整理]",
            f"状態: {status_text}",
            "イベント整理: 対象なし（適用するイベントがありません）",
            f"キー数: {cleanup_summary.input_key_count} → {cleanup_summary.final_key_count} 件",
            f"{key_text}: {len(cleanup_summary.removed_keys)} 件",
            f"理由: {reason_text}",
            f"保護理由の記録: {retained_reason_count} 件",
        )
    else:
        decision_counts: dict[str, int] = {}
        for _event_id, action, _reasons in cleanup_summary.event_reasons:
            decision_counts[action] = decision_counts.get(action, 0) + 1
        decision_text = "、".join(
            f"{action} {count}件" for action, count in sorted(decision_counts.items())
        ) or "イベント判定なし"
        cleanup_lines = (
            "[自動整理候補]",
            f"状態: 比較候補（{cleanup_summary.variant}）",
            f"整理イベント: {len(cleanup_summary.suppressed_event_ids)} 件",
            f"キー数: {cleanup_summary.input_key_count} → {cleanup_summary.final_key_count} 件",
            f"削減キー: {len(cleanup_summary.removed_keys)} 件",
            f"イベント判定: {decision_text}",
        )
    input_mode = {
        "text_audio": "TEXT + 音声",
        "voice_only": "音声のみ",
    }.get(input_summary.input_mode, input_summary.input_mode)

    return "\n".join(
        (
            "[入力]",
            f"入力モード: {input_mode}",
            f"TEXT: {_display_path(input_summary.normalized_text_path)}",
            f"入力音声: {_display_path(input_summary.normalized_source_audio_path)}",
            f"解析用WAV: {_display_path(input_summary.normalized_effective_wav_path)}",
            f"TEXT内容: {_display_bool(input_summary.text_content_present)}",
            f"解析テキスト: {_display_bool(input_summary.analysis_text_present)}",
            "",
            "[解析]",
            f"状態: {_analysis_state(snapshot, analysis_in_progress=analysis_in_progress)}",
            f"タイミング元: {analysis_summary.timing_source or '(未解析)'}",
            f"アンカー数: {analysis_summary.anchor_count} 件",
            f"母音イベント数: {analysis_summary.event_count} 件",
            f"最大フレーム: {analysis_summary.max_frame if analysis_summary.max_frame is not None else '(未算出)'}",
            f"タイミング警告: {_display_bool(analysis_summary.timing_warning_present)}",
            f"音量fallback数: {analysis_summary.observation_fallback_count} 件",
            "",
            "[Whisper]",
            f"選択モデル: {whisper_summary.selected_model_key or '(未設定)'} / {whisper_summary.selected_model_display_name or '(未設定)'}",
            f"現在のモデル: {whisper_summary.active_model_key or '(未設定)'} / {whisper_summary.active_model_display_name or '(未設定)'}",
            f"読み込み済み: {whisper_summary.loaded_model_key or '(なし)'}",
            f"解析結果モデル: {whisper_summary.analysis_model_key or '(なし)'}",
            f"解析identity: {whisper_summary.analysis_identity_status}",
            f"runtime identity: {whisper_summary.runtime_identity_status}",
            f"Manifest schema: {whisper_summary.manifest_schema_version if whisper_summary.manifest_schema_version is not None else '(未適用)'}",
            f"Whisper package要求版: {whisper_summary.package_name}=={whisper_summary.package_version}",
            f"package gate: {whisper_summary.package_gate_status}",
            f"保存先: {whisper_summary.storage_location_display}",
            f"管理状態: {whisper_summary.management_operation} / {whisper_summary.management_phase}",
            f"failure: {whisper_summary.failure_class} / {whisper_summary.failure_detail_code or '(なし)'}",
            f"案内: {whisper_summary.safe_failure_notice or '(なし)'}",
            "",
            "[生成]",
            f"VMDモデル名: {generation_summary.vmd_model_name}",
            f"開口保持: {generation_summary.closing_hold_frames} フレーム",
            f"閉口スムース: {generation_summary.closing_softness_frames} フレーム",
            f"長音モード: {generation_summary.active_long_vowel_mode}",
            f"プリセットID: {generation_summary.active_preset_id or '(Custom)'}",
            f"プリセット名: {generation_summary.active_preset_display_name or 'Custom'}",
            "長音hold run数: "
            f"{generation_summary.effective_long_vowel_hold_run_count if generation_summary.effective_long_vowel_hold_run_count is not None else '(未算出)'}",
            "長音decay run数: "
            f"{generation_summary.effective_long_vowel_decay_run_count if generation_summary.effective_long_vowel_decay_run_count is not None else '(未算出)'}",
            f"診断schema: {generation_summary.fingerprint_schema_version}",
            "",
            *cleanup_lines,
            "",
            "[保存可否]",
            f"VMD保存: {'可能' if saveability.vmd_save_allowed else '不可'}",
            f"保存禁止診断数: {len(saveability.blocking_codes)} 件",
            f"要確認警告数: {len(saveability.warning_codes)} 件",
            f"長音mode override数: {snapshot.adjustment_summary.long_vowel_mode_override_count} 件",
        )
    )


__all__ = [
    "build_diagnostic_failure_input",
    "build_whisper_diagnostics_summary",
    "build_output_diagnostics_snapshot_from_ui_state",
    "build_shared_output_failure_diagnostics_snapshot",
    "capture_shared_output_diagnostics_seed",
    "build_shared_output_diagnostics_snapshot",
    "resolve_source_audio_path_from_ui_state",
    "format_output_diagnostics_info",
]
