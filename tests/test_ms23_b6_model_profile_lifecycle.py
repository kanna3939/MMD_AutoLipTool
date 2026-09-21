from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.effective_shape_plan import BasePlanIdentity
from src.core.event_adjustment import ADJUSTMENT_SNAPSHOT_SCHEMA, AdjustmentLayerSnapshot
from src.core.effective_shape_plan import BaseTimingPlanInput, resolve_effective_shape_plan
from src.core.generation_presets import (
    BUILTIN_PRESETS,
    GenerationPresetStore,
    GenerationSettings,
)
from src.core.diagnostic_report import format_diagnostic_report
from src.core.model_profile_state import (
    ModelProfileResolutionStatus,
    ModelProfileState,
    resolve_model_profile_apply,
    resolve_no_profile,
    resolve_startup_model_profile,
    validate_generation_preset_mutation,
    validate_model_profile_mutation,
)
from src.core.model_profiles import (
    ModelProfile,
    ModelProfileStore,
    ProfileGenerationOverrides,
)
from src.core.morph_name_sets import (
    JAPANESE_MORPH_NAME_SET_ID,
    JAPANESE_OUTPUT_NAMES,
    LATIN_MORPH_NAME_SET_ID,
    LATIN_OUTPUT_NAMES,
)
from src.core.output_diagnostics import (
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    EffectiveMorphFrameInput,
    EffectiveWriterInput,
    build_output_diagnostics_snapshot,
    VmdWriterParameters,
)
from src.core.output_edit_state import GenerationState, OutputEditState
from src.core.preview_transform import (
    build_preview_data_from_effective_shape_plan,
    empty_preview_data,
)
from src.core.settings_store import SettingsStore
from gui_wx.app_controller import AppController
from src.gui_wx.main_frame import MainFrame
from src.gui_wx.ui_state import UiState
from src.vmd_writer import VowelTimelinePoint, write_morph_frames_vmd
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir
from tests.test_wx_ms21_b6_undo_redo import make_ready_frame

import wx


PROFILE_ID = "11111111-1111-4111-8111-111111111111"
PROFILE_ID_2 = "22222222-2222-4222-8222-222222222222"
USER_PRESET_ID = "33333333-3333-4333-8333-333333333333"


@dataclass(frozen=True)
class _TimelinePoint:
    time_sec: float
    vowel: str = "あ"
    value: float = 0.5
    peak_value: float | None = None
    duration_sec: float = 0.2
    start_sec: float | None = None
    end_sec: float | None = None


def _profile(
    *,
    profile_id: str = PROFILE_ID,
    display_name: str = "Latin profile",
    morph_name_set_id: str = LATIN_MORPH_NAME_SET_ID,
    morph_upper_limit: float | None = 0.8,
    default_preset_id: str = "builtin:standard-hold",
    overrides: ProfileGenerationOverrides | None = None,
) -> ModelProfile:
    return ModelProfile(
        id=profile_id,
        display_name=display_name,
        morph_name_set_id=morph_name_set_id,
        morph_upper_limit=morph_upper_limit,
        generation_overrides=(
            ProfileGenerationOverrides() if overrides is None else overrides
        ),
        default_preset_id=default_preset_id,
    )


def _effective_plan():
    return resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(_TimelinePoint(0.3, start_sec=0.2, end_sec=0.4),),
            observations=None,
            source_duration_frames=60,
        )
    )


def _diagnostic_input(
    effective_writer_input: EffectiveWriterInput | None,
    *,
    input_mode: str = "text_audio",
    profile_id: str | None = None,
    profile_display_name: str | None = None,
    baseline_id: str | None = None,
    baseline_display_name: str | None = None,
    resolution_status: str = "no_profile",
    resolution_reason: str | None = None,
    morph_name_set_id: str = JAPANESE_MORPH_NAME_SET_ID,
    morph_name_set_display_name: str = "日本語5母音",
    timing_plan: DiagnosticTimingPlanInput | None = None,
) -> DiagnosticSnapshotInput:
    if timing_plan is None:
        timing_plan = DiagnosticTimingPlanInput(
            vowels=("あ",),
            timeline=(
                VowelTimelinePoint(
                    time_sec=0.3,
                    vowel="あ",
                    value=0.4,
                    duration_sec=0.2,
                    start_sec=0.2,
                    end_sec=0.4,
                ),
            ),
            anchors=(),
            source="test",
            observations=(),
        )
    return DiagnosticSnapshotInput(
        input_mode=input_mode,
        text_path=Path("input.txt") if input_mode == "text_audio" else None,
        text_content_present=input_mode == "text_audio",
        source_audio_path=Path("voice.wav"),
        effective_wav_path=Path("analysis.wav"),
        analysis_text_present=True,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
        timing_plan=timing_plan,
        existing_vmd_save_ready=effective_writer_input is not None,
        writer_parameters=VmdWriterParameters(),
        effective_writer_input_state=(
            "ready" if effective_writer_input is not None else "not_applicable"
        ),
        effective_writer_input=effective_writer_input,
        active_model_profile_id=profile_id,
        active_model_profile_display_name=profile_display_name,
        active_profile_baseline_preset_id=baseline_id,
        baseline_preset_display_name=baseline_display_name,
        model_profile_resolution_status=resolution_status,
        model_profile_resolution_reason_code=resolution_reason,
        resolved_morph_name_set_id=morph_name_set_id,
        resolved_morph_name_set_display_name=morph_name_set_display_name,
    )


def _effective_writer_input(output_names: tuple[str, ...]) -> EffectiveWriterInput:
    plan = _effective_plan()
    frames = build_morph_frames_from_effective_shape_plan(
        plan,
        apply_final_normalization=False,
        output_morph_names=output_names,
    )
    return EffectiveWriterInput(
        shape_count=len(plan.shapes),
        morph_frames=tuple(
            EffectiveMorphFrameInput(frame_no, name, value)
            for frame_no, name, value in frames
        ),
        tails=(),
        allowed_morph_names=output_names,
    )


def _output(*, adjustment_value: float | None = None) -> OutputEditState:
    identity = BasePlanIdentity("ms23-b6-test-v1", ("base",), "base")
    adjustments = ()
    if adjustment_value is not None:
        from src.core.event_adjustment import EventAdjustment

        adjustments = (EventAdjustment(0, peak_value=adjustment_value),)
    return OutputEditState(
        identity,
        AdjustmentLayerSnapshot(ADJUSTMENT_SNAPSHOT_SCHEMA, identity, adjustments),
        GenerationState(GenerationSettings()),
    )


def _profile_state(profile_id: str | None, baseline_id: str | None) -> ModelProfileState:
    return ModelProfileState(
        active_model_profile_id=profile_id,
        active_profile_baseline_preset_id=baseline_id,
        resolution_status=(
            ModelProfileResolutionStatus.RESOLVED
            if profile_id is not None
            else ModelProfileResolutionStatus.NO_PROFILE
        ),
    )


def test_ui_state_profile_context_is_atomic_through_undo_and_redo() -> None:
    output = _output()
    no_profile = _profile_state(None, None)
    active_profile = _profile_state("profile", "baseline")
    state = UiState(model_profile_state=no_profile)

    assert state.initialize_output_edit_history_state(output) is True
    assert (
        state.commit_output_edit_state(
            output,
            model_profile_state=active_profile,
        )
        is True
    )

    assert state.undo_output_edit_state() is True
    assert state.model_profile_state == no_profile
    assert state.output_edit_history_state is not None
    assert state.output_edit_history_state.current_model_profile_state == no_profile

    assert state.redo_output_edit_state() is True
    assert state.output_edit_history_state.current_model_profile_state == active_profile
    assert state.model_profile_state == active_profile


def test_main_frame_history_navigation_reprojects_profile_context() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    try:
        with workspace_tempdir("ms23_b6_main_history") as tmp_dir:
            settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            preset_store = GenerationPresetStore(
                settings_store=settings_store,
                presets_path=tmp_dir / "presets.json",
            )
            profile_store = ModelProfileStore(
                settings_store=settings_store,
                profiles_path=tmp_dir / "profiles.json",
            )
            controller = AppController(
                frame,
                settings_store=settings_store,
                preset_store=preset_store,
                profile_store=profile_store,
            )
            frame.set_controller(controller)
            controller.load_startup_state()
            frame.sync_ui_state()
            profile_store.create(
                "Profile",
                LATIN_MORPH_NAME_SET_ID,
                0.8,
                ProfileGenerationOverrides(),
                "builtin:standard-hold",
                profile_id=PROFILE_ID,
            )

            output = frame.ui_state.current_output_edit_state
            assert output is not None
            no_profile = _profile_state(None, None)
            active_profile = _profile_state(PROFILE_ID, "builtin:standard-hold")
            frame.ui_state.model_profile_state = no_profile
            assert (
                frame.ui_state.commit_output_edit_state(
                    output,
                    model_profile_state=active_profile,
                )
                is True
            )
            assert frame._perform_adjustment_history_navigation(redo=False) is True
            assert frame.ui_state.model_profile_state == no_profile

            assert frame._perform_adjustment_history_navigation(redo=True) is True
            assert frame.ui_state.model_profile_state == active_profile
            assert (
                frame.ui_state.output_edit_history_state.current_model_profile_state
                == active_profile
            )
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)


def test_profile_resolution_keeps_japanese_default_and_latin_profile_names() -> None:
    profile = _profile()
    latin = resolve_model_profile_apply(
        requested_profile_id=profile.id,
        application_morph_upper_limit=0.5,
        profiles=(profile,),
        presets=BUILTIN_PRESETS,
    )
    no_profile = resolve_no_profile(
        current_generation_settings=BUILTIN_PRESETS[0].generation_settings,
        current_morph_upper_limit=0.5,
        presets=BUILTIN_PRESETS,
    )

    assert latin.resolution is not None
    assert latin.resolution.morph_name_set.output_names == LATIN_OUTPUT_NAMES
    assert no_profile.resolution is not None
    assert no_profile.resolution.morph_name_set.output_names == JAPANESE_OUTPUT_NAMES
    assert (
        no_profile.resolution.model_profile_state.resolution_status
        is ModelProfileResolutionStatus.NO_PROFILE
    )


def test_writer_preview_diagnostics_and_report_share_resolved_latin_contract() -> None:
    plan = _effective_plan()
    japanese_frames = build_morph_frames_from_effective_shape_plan(
        plan,
        apply_final_normalization=False,
        output_morph_names=JAPANESE_OUTPUT_NAMES,
    )
    latin_frames = build_morph_frames_from_effective_shape_plan(
        plan,
        apply_final_normalization=False,
        output_morph_names=LATIN_OUTPUT_NAMES,
    )
    preview = build_preview_data_from_effective_shape_plan(
        plan,
        output_morph_names=LATIN_OUTPUT_NAMES,
    )
    latin_input = _effective_writer_input(LATIN_OUTPUT_NAMES)
    latin_snapshot = build_output_diagnostics_snapshot(
        _diagnostic_input(
            latin_input,
            profile_id="profile",
            profile_display_name="Latin profile",
            baseline_id="builtin:standard-hold",
            baseline_display_name="標準（ホールド）",
            resolution_status="resolved",
            morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
            morph_name_set_display_name="英字5母音",
        )
    )

    assert tuple((frame_no, value) for frame_no, _, value in japanese_frames) == tuple(
        (frame_no, value) for frame_no, _, value in latin_frames
    )
    assert {name for _, name, _ in latin_frames} == {"A"}
    assert [row.display_name for row in preview.rows] == list(LATIN_OUTPUT_NAMES)
    assert latin_snapshot.generation_summary.resolved_morph_name_set_id == (
        LATIN_MORPH_NAME_SET_ID
    )
    assert latin_snapshot.save_state_fingerprint is not None

    report = format_diagnostic_report(
        latin_snapshot,
        generated_at=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
    )
    assert "Active Model Profile ID: profile" in report
    assert "Resolved Morph Name Set ID: builtin:latin-vowels" in report
    assert "Resolved Morph Name Set Display Name: 英字5母音" in report

    renamed_input = replace(
        _diagnostic_input(
            latin_input,
            profile_id="profile",
            profile_display_name="Latin profile",
            baseline_id="builtin:standard-hold",
            baseline_display_name="標準（ホールド）",
            resolution_status="resolved",
            morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
            morph_name_set_display_name="英字5母音",
        ),
        active_model_profile_display_name="Renamed Latin profile",
    )
    renamed_snapshot = build_output_diagnostics_snapshot(renamed_input)
    assert renamed_snapshot.save_state_fingerprint == latin_snapshot.save_state_fingerprint


def test_text_and_voice_only_writer_inputs_keep_same_resolved_names(tmp_path: Path) -> None:
    latin_input = _effective_writer_input(LATIN_OUTPUT_NAMES)
    text_snapshot = build_output_diagnostics_snapshot(
        _diagnostic_input(
            latin_input,
            input_mode="text_audio",
            profile_id="profile",
            profile_display_name="Latin profile",
            baseline_id="builtin:standard-hold",
            baseline_display_name="標準（ホールド）",
            resolution_status="resolved",
            morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
            morph_name_set_display_name="英字5母音",
        )
    )
    voice_snapshot = build_output_diagnostics_snapshot(
        _diagnostic_input(
            latin_input,
            input_mode="voice_only",
            profile_id="profile",
            profile_display_name="Latin profile",
            baseline_id="builtin:standard-hold",
            baseline_display_name="標準（ホールド）",
            resolution_status="resolved",
            morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
            morph_name_set_display_name="英字5母音",
        )
    )
    text_path = tmp_path / "text.vmd"
    voice_path = tmp_path / "voice-only.vmd"
    write_morph_frames_vmd(
        text_path,
        tuple(
            (frame.frame_no, frame.morph_name, frame.value)
            for frame in latin_input.morph_frames
        ),
        output_morph_names=LATIN_OUTPUT_NAMES,
    )
    write_morph_frames_vmd(
        voice_path,
        tuple(
            (frame.frame_no, frame.morph_name, frame.value)
            for frame in latin_input.morph_frames
        ),
        output_morph_names=LATIN_OUTPUT_NAMES,
    )

    assert text_snapshot.generation_summary.resolved_morph_name_set_id == (
        voice_snapshot.generation_summary.resolved_morph_name_set_id
    )
    assert text_snapshot.fingerprint_payload is not None
    assert voice_snapshot.fingerprint_payload is not None
    assert text_path.exists() and voice_path.exists()


def test_empty_and_invalid_output_keep_latin_preview_labels_and_fail_closed() -> None:
    empty = empty_preview_data(output_morph_names=LATIN_OUTPUT_NAMES)
    invalid_input = replace(
        _diagnostic_input(None),
        analysis_result_valid=False,
        timing_plan=None,
        effective_writer_input_state="invalid",
        existing_vmd_save_ready=False,
    )
    invalid_snapshot = build_output_diagnostics_snapshot(invalid_input)

    assert [row.display_name for row in empty.rows] == list(LATIN_OUTPUT_NAMES)
    assert invalid_snapshot.save_state_fingerprint is None
    assert invalid_snapshot.saveability.vmd_save_allowed is False


def test_startup_profile_matrix_fails_closed_without_partial_import(tmp_path: Path) -> None:
    settings_store = SettingsStore(tmp_path / "MMD_AutoLipTool.ini")
    preset_store = GenerationPresetStore(
        settings_store=settings_store,
        presets_path=tmp_path / "presets.json",
    )
    profile_store = ModelProfileStore(
        settings_store=settings_store,
        profiles_path=tmp_path / "profiles.json",
    )
    preset_result = preset_store.load()
    profile_store.load()
    created = profile_store.create(
        "Latin profile",
        LATIN_MORPH_NAME_SET_ID,
        0.8,
        ProfileGenerationOverrides(2, 3, "decay"),
        "builtin:standard-hold",
        profile_id=PROFILE_ID,
    )
    assert created.succeeded is True
    profile_result = profile_store.load()

    valid = resolve_startup_model_profile(
        application_generation_settings=GenerationSettings(),
        application_morph_upper_limit=0.5,
        raw_active_preset_id=None,
        raw_active_model_profile_id=PROFILE_ID,
        raw_active_profile_baseline_preset_id="builtin:standard-hold",
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )
    missing_baseline = resolve_startup_model_profile(
        application_generation_settings=GenerationSettings(),
        application_morph_upper_limit=0.5,
        raw_active_preset_id=None,
        raw_active_model_profile_id=PROFILE_ID,
        raw_active_profile_baseline_preset_id=USER_PRESET_ID,
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )
    missing_profile = resolve_startup_model_profile(
        application_generation_settings=GenerationSettings(),
        application_morph_upper_limit=0.5,
        raw_active_preset_id=None,
        raw_active_model_profile_id=PROFILE_ID_2,
        raw_active_profile_baseline_preset_id=None,
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )

    profile_store.profiles_path.write_text("{broken", encoding="utf-8")
    broken_result = profile_store.load()
    broken = resolve_startup_model_profile(
        application_generation_settings=GenerationSettings(),
        application_morph_upper_limit=0.5,
        raw_active_preset_id=None,
        raw_active_model_profile_id=PROFILE_ID,
        raw_active_profile_baseline_preset_id=None,
        profile_load_result=broken_result,
        preset_load_result=preset_result,
    )

    assert valid.resolution.model_profile_state.resolution_status is ModelProfileResolutionStatus.RESOLVED
    assert missing_baseline.resolution.model_profile_state.resolution_status is ModelProfileResolutionStatus.FALLBACK_PROFILE_DEFAULT
    assert missing_profile.resolution.model_profile_state.resolution_status is ModelProfileResolutionStatus.FALLBACK_NO_PROFILE
    assert missing_profile.resolution.model_profile_state.resolution_reason_code == "active_profile_not_found"
    assert broken.resolution.model_profile_state.resolution_reason_code == "profile_store_unavailable"
    assert broken.resolution.model_profile_state.active_model_profile_id is None


def test_profile_and_preset_guards_reject_active_or_referenced_mutations(tmp_path: Path) -> None:
    settings_store = SettingsStore(tmp_path / "MMD_AutoLipTool.ini")
    preset_store = GenerationPresetStore(
        settings_store=settings_store,
        presets_path=tmp_path / "presets.json",
    )
    profile_store = ModelProfileStore(
        settings_store=settings_store,
        profiles_path=tmp_path / "profiles.json",
    )
    preset_store.load()
    profile_store.load()
    user_preset = preset_store.create(
        "参照プリセット",
        GenerationSettings(4, 5, "hold"),
        preset_id=USER_PRESET_ID,
    ).user_presets[0]
    profile = profile_store.create(
        "参照プロファイル",
        JAPANESE_MORPH_NAME_SET_ID,
        0.5,
        ProfileGenerationOverrides(),
        user_preset.id,
        profile_id=PROFILE_ID,
    ).user_profiles[0]
    profile_result = profile_store.load()
    preset_result = preset_store.load()
    current = _profile_state(PROFILE_ID, "builtin:standard-hold")

    referenced = validate_generation_preset_mutation(
        operation="delete",
        target_preset_id=user_preset.id,
        candidate_preset=None,
        current_model_profile_state=current,
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )
    active_delete = validate_model_profile_mutation(
        operation="delete",
        target_profile_id=profile.id,
        candidate_profile=None,
        current_model_profile_state=current,
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )

    assert referenced.allowed is False
    assert referenced.error_code == "preset_referenced_by_profile"
    assert active_delete.allowed is False
    assert active_delete.error_code == "active_profile_locked"


def test_profile_store_write_failure_keeps_previous_file_and_state(tmp_path: Path) -> None:
    store = ModelProfileStore(
        settings_path=tmp_path / "MMD_AutoLipTool.ini",
        profiles_path=tmp_path / "profiles.json",
    )
    store.load()
    created = store.create(
        "既存プロファイル",
        JAPANESE_MORPH_NAME_SET_ID,
        0.5,
        ProfileGenerationOverrides(),
        "builtin:standard-hold",
        profile_id=PROFILE_ID,
    )
    before_bytes = store.profiles_path.read_bytes()

    with patch("src.core.model_profiles.os.replace", side_effect=OSError("replace failed")):
        failed = store.create(
            "新規プロファイル",
            JAPANESE_MORPH_NAME_SET_ID,
            0.5,
            ProfileGenerationOverrides(),
            "builtin:standard-hold",
        )

    assert created.succeeded is True
    assert failed.succeeded is False
    assert failed.error_code == "replace_failed"
    assert store.profiles_path.read_bytes() == before_bytes
    assert tuple(profile.display_name for profile in store.user_profiles) == (
        "既存プロファイル",
    )


def test_workspace_reset_clears_workspace_but_preserves_profile_projection() -> None:
    active_profile = _profile_state("profile", "baseline")
    generation = GenerationState(GenerationSettings(7, 8, "decay"))
    state = UiState(model_profile_state=active_profile, generation_state=generation)
    state.current_timing_plan = object()
    state.analysis_result_valid = True
    state.analysis_cancelled = True
    state.current_output_diagnostics_snapshot = object()
    assert state.initialize_output_edit_history_state(_output()) is True

    state.reset_workspace()

    assert state.current_timing_plan is None
    assert state.analysis_result_valid is False
    assert state.analysis_cancelled is False
    assert state.current_output_diagnostics_snapshot is None
    assert state.output_edit_history_state is None
    assert state.model_profile_state == active_profile
    assert state.generation_state == generation


@pytest.mark.parametrize("mode", ["hold", "decay"])
def test_same_vowel_long_vowel_preview_remains_buildable_for_both_modes(mode: str) -> None:
    from src.core.effective_shape_plan import ShapeParameters

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(
                VowelTimelinePoint(
                    0.2,
                    "あ",
                    value=0.6,
                    duration_sec=0.2,
                    start_sec=0.1,
                    end_sec=0.3,
                    vowel_token_index=0,
                ),
                VowelTimelinePoint(
                    0.5,
                    "あ",
                    value=0.4,
                    duration_sec=0.2,
                    start_sec=0.4,
                    end_sec=0.6,
                    vowel_token_index=1,
                    is_long_vowel_continuation=True,
                    long_vowel_source_token_index=0,
                ),
            ),
            observations=None,
            source_duration_frames=30,
            shape_parameters=ShapeParameters(long_vowel_mode=mode),
        )
    )
    preview = build_preview_data_from_effective_shape_plan(plan)

    assert preview.rows[0].segments
    assert plan.shapes
