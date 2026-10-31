import math
import os
import uuid
import copy
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Sequence

import wx

from gui_wx.info_panel import InfoPanel
from gui_wx.placeholder_panels import PlaceholderContainer
from gui_wx.parameter_panel import ParameterPanel
from gui_wx.right_pane import (
    ModelProfileApplyRequest,
    ModelProfileCreateRequest,
    ModelProfileDeleteRequest,
    ModelProfileEditorValues,
    ModelProfilePanelItem,
    ModelProfilePanelState,
    ModelProfilePresetOption,
    ModelProfileSelectRequest,
    ModelProfileUpdateRequest,
    PresetApplyRequest,
    PresetCreateRequest,
    PresetDeleteRequest,
    PresetPanelItem,
    PresetPanelState,
    PresetSelectRequest,
    PresetUpdateRequest,
    RightPane,
    CleanupEventSelectionRequest,
    WhisperModelPanelItem,
    WhisperModelPanelState,
    WhisperModelCancelRequest,
    WhisperModelDeleteRequest,
    WhisperModelDownloadRequest,
    WhisperModelApplyRequest,
    WhisperModelSelectRequest,
    WhisperStorageRootRequest,
)
from gui_wx.ui_state import (
    INPUT_MODE_TEXT_AUDIO,
    INPUT_MODE_VOICE_ONLY,
    UiState,
    StatusKey,
    WhisperModelSelectionState,
    format_whisper_failure_notice,
)
from gui_wx.analysis_worker import AnalysisWorker, AnalysisWorkerResult
from gui_wx.analysis_rollback import (
    AnalysisParameterSnapshot,
    AnalysisRollbackSnapshot,
    can_restore_analysis_rollback,
    is_rollback_forbidden_failure_class,
)
from gui_wx.final_output_sync import (
    FinalOutputRequest,
    FinalOutputSyncCoordinator,
    apply_shared_final_output_result,
    request_shared_final_output,
)
from gui_wx.output_edit_draft_worker import (
    OutputEditDraftProjectionCoordinator,
    OutputEditDraftProjectionRequest,
    OutputEditDraftProjectionResult,
)
from gui_wx.output_diagnostics_adapter import (
    build_diagnostic_failure_input,
    build_whisper_diagnostics_summary,
    build_output_diagnostics_snapshot_from_ui_state,
    capture_shared_output_diagnostics_seed,
    resolve_source_audio_path_from_ui_state,
)
from gui_wx.playback_context import build_playback_info_context
from gui_wx.ui_sync_context import UiSyncContext, build_ui_sync_context
from gui_wx.voice_only_errors import format_voice_only_analysis_error

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    EffectiveShapePlan,
    ShapeParameters,
    apply_adjustment_update,
    build_base_plan_identity,
    resolve_effective_shape_plan,
    resolve_manual_crossfade_end_offset_max,
    source_duration_frames_from_seconds,
)
from src.core.effective_shape_diagnostics import (
    ResolverDiagnosticsCollector,
)
from src.core.event_adjustment import (
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
    canonicalize_adjustment_snapshot,
    empty_adjustment_snapshot,
)
from src.core.event_adjustment_history import AdjustmentCoalescingKey
from src.core.output_edit_state import GenerationState, OutputEditState
from src.core.output_edit_draft import (
    rebase_output_edit_history,
    source_event_keys,
)
from src.core.pipeline import reproject_peak_values_for_upper_limit
from src.core.generation_presets import BUILTIN_PRESETS, GenerationSettings
from src.core.model_profiles import ProfileGenerationOverrides
from src.core.morph_name_sets import get_builtin_morph_name_set
from src.core.model_profile_state import (
    ModelProfileResolutionStatus,
    ModelProfileState,
    ModelProfileResolutionResult,
    validate_active_profile_direct_edit,
)
from src.core.preview_hit_test import PreviewSelectionRequest
from src.core.final_morph_closure_plan import ClosureContract
from src.core.transition_evaluation import TransitionEvaluationRequest
from src.core.cleanup_evaluation import CleanupEvaluationRequest
from src.core.transition_default_policy import (
    build_adopted_transition_binding,
    resolve_default_transition_selection,
)
from src.core.cleanup_default_policy import (
    build_adopted_cleanup_binding,
    resolve_default_cleanup_selection,
)
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER
from src.core.text_processing import TextProcessingError, text_to_hiragana, hiragana_to_vowel_string, _validate_and_clean_text
from src.core.audio_processing import analyze_wav_file, WavAnalysisResult, load_waveform_preview
from src.core.preview_transform import (
    INTERNAL_VOWEL_ORDER,
    build_preview_data_from_effective_shape_plan,
)
from src.core.analysis_debug_store import AnalysisDebugStore
from src.core.analysis_debug_trace import (
    AnalysisDebugTrace,
    build_settings_provenance,
    build_debug_trace,
)
from src.core.mmd_wav_export import MMD_WAV_SPEC
from src.core.output_diagnostics import (
    VmdWriterParameters,
    shared_warning_confirmation_matches,
)
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from src.vmd_writer.writer import vmd_wire_morph_value
from src.core.delivery_package import (
    DeliveryStartGateResult,
    evaluate_delivery_start_gate,
)
from gui_wx.selected_event_editor import (
    GROUP_SHARED_FIELDS,
    SelectedEventEditBoundaryRequest,
    SelectedEventEditRequest,
    build_selected_event_editor_state,
    merge_selected_event_edit,
    reset_selected_event_adjustment,
)
from gui_wx.theme import ThemeButton, ThemeManager, ThemeMode
from gui_wx.help_about_dialogs import AboutDialog, HelpDialog
from gui_wx.vmd_save_progress_dialog import ProgressState, VmdSaveProgressDialog
from src.core import DiagnosticSeverity, OutputDiagnosticsSnapshot
from src.core.whisper_model_runtime import (
    VerifiedAnalysisModelRequest,
    WhisperModelRuntimeError,
)


_UNSET = object()
_DEBUG_PROJECTION_INPUT_CONTRACT_VERSION = "ms28-b3b-projection-input-v1"
_DEBUG_FAILURE_CODES = frozenset(
    {
        "none",
        "not_applicable",
        "base_input_unavailable",
        "duration_unavailable",
        "plan_missing",
        "invalid_plan_shape",
        "base_input_contract_error",
        "sync_context_build_failed",
        "effective_shape_plan_unavailable",
        "writer_adapter_failed",
        "identity_mismatch",
        "adjustment_snapshot_mismatch",
        "shape_parameters_mismatch",
        "timeline_metadata_invalid",
        "long_vowel_metadata_invalid",
        "observation_metadata_invalid",
        "adjustment_contract_invalid",
        "diagnostics_snapshot_unavailable",
        "writer_input_invalid",
        "unknown_contract_failure",
        "base_input_type_invalid",
        "source_duration_invalid",
        "shape_parameters_type_invalid",
        "shape_parameter_invalid",
        "long_vowel_mode_invalid",
        "long_metadata_type_invalid",
        "long_source_order_invalid",
        "long_source_unexpected",
        "long_metadata_mixed",
        "long_token_order_invalid",
        "long_active_source_mismatch",
        "long_source_vowel_mismatch",
        "numeric_type_invalid",
        "numeric_non_finite",
        "numeric_negative",
        "timeline_bounds_invalid",
        "vowel_unsupported",
        "base_frame_order_invalid",
        "long_source_missing",
        "observation_count_mismatch",
        "observation_index_mismatch",
        "observation_vowel_mismatch",
        "observation_reference_invalid",
        "observation_span_invalid",
        "observation_flag_invalid",
        "observation_bracketing_invalid",
        "observation_rms_length_mismatch",
        "observation_frame_invalid",
        "observation_range_invalid",
        "observation_overlap_invalid",
        "observation_coverage_invalid",
        "observation_provenance_invalid",
        "observation_rejection_invalid",
        "identity_contract_invalid",
        "snapshot_identity_mismatch",
        "snapshot_schema_invalid",
        "adjustment_entry_type_invalid",
        "adjustment_field_invalid",
        "adjustment_duplicate_index",
        "adjustment_index_out_of_range",
        "adjustment_field_invalid",
        "long_adjustment_ownership_invalid",
        "long_role_invalid",
        "adjusted_frame_order_invalid",
        "tail_override_non_tail",
        "slope_midpoint_missing",
        "long_terminal_order_invalid",
        "long_hold_close_conflict",
        "shape_event_missing",
        "manual_crossfade_limit_exceeded",
        "admission_index_invalid",
        "admission_vowel_invalid",
        "admission_shape_id_invalid",
        "admission_point_kind_invalid",
        "admission_source_indices_invalid",
        "admission_range_invalid",
        "admission_boundary_invalid",
        "admission_role_invalid",
        "admission_flag_invalid",
        "admission_rejection_invalid",
        "admission_enabled_reason_conflict",
        "required_zero_positive_conflict",
    }
)
_DEBUG_PHASES = frozenset(
    {
        "none",
        "base_input_build",
        "duration_selection",
        "sync_context_cache",
        "sync_context_build",
        "effective_plan_resolve",
        "effective_plan_hint_validate",
        "diagnostics_snapshot_build",
        "effective_output_prepare",
        "preview_projection",
        "writer_projection",
        "vmd_save",
        "debug_store_write",
        "unknown",
        "resolver_input",
        "shape_parameters",
        "timeline_metadata",
        "base_events",
        "long_runs",
        "observations",
        "observation_contract",
        "base_identity",
        "snapshot_canonicalize",
        "adjustment_ownership",
        "adjustment_apply",
        "handoff_candidates",
        "handoff_apply",
        "regular_shapes",
        "long_shapes",
        "manual_crossfade",
        "slope_validation",
        "silence_admission",
        "silence_rebind",
        "required_zero_conflicts",
        "normalization_contract",
        "plan_assemble",
    }
)
_DEBUG_DOMAINS = frozenset(
    {
        "none",
        "base_input",
        "duration",
        "adjustment_contract",
        "timeline_metadata",
        "long_vowel_metadata",
        "observation_metadata",
        "effective_shape",
        "diagnostics_snapshot",
        "writer_input",
        "unknown",
        "origin_shape_id",
        "effective_frame_range",
        "positive_core_frame_ranges",
        "required_zero_frame_ranges",
        "required_zero_frames",
        "positive_point_kinds",
        "source_event_indices",
        "rejection_reason_code",
        "vowel_token_index",
        "is_long_vowel_continuation",
        "long_vowel_source_token_index",
        "long_metadata",
        "vowel",
        "time_sec",
        "duration_sec",
        "start_sec",
        "end_sec",
        "peak_value",
        "timeline_bounds",
        "frame_order",
        "observations",
        "span_indices",
        "bracketing",
        "rms_window_times_sec",
        "rms_window_values",
        "local_peak",
        "adjustment_snapshot",
        "adjustment_schema",
        "adjustments",
        "base_event_index",
        "peak_value",
        "start_offset_frames",
        "end_offset_frames",
        "hold_frames",
        "softness_frames",
        "slope_ratio",
        "adjustment_ownership",
        "terminal_end_frame",
        "closing_frame",
        "real_base_event_indices",
        "end_offset_frames",
        "slope_ratio",
        "normalization_contract",
        "effective_plan",
    }
)
_DEBUG_FIELD_CODES = frozenset(
    {
        "not_applicable",
        "not_evaluated",
        "base_plan_identity",
        "adjustment_snapshot_identity",
        "shape_parameters",
        "timeline_point",
        "long_vowel_source",
        "long_vowel_role",
        "observation",
        "output_edit_history",
        "effective_plan_hint",
        "duration",
        "boundary_frame",
        "boundary_point_kind",
        "unknown",
    }
)
_DEBUG_EXCEPTION_TYPES = frozenset(
    {"not_applicable", "AdjustmentContractError", "TypeError", "ValueError", "unknown"}
)
_DEBUG_INDEX_STATUS = frozenset(
    {"available", "not_available", "not_applicable", "not_evaluated"}
)
_DEBUG_EXECUTION_STATES = frozenset(
    {"not_attempted", "attempted", "completed", "skipped", "not_evaluable"}
)
_DEBUG_EXECUTION_OUTCOMES = frozenset(
    {"success", "failed", "pending", "cancelled", "not_applicable", "not_evaluable"}
)
_DEBUG_EXECUTION_REASONS = frozenset(
    {
        "not_attempted",
        "resolver_succeeded",
        "resolver_failed",
        "resolver_skipped_cache",
        "resolver_skipped_hint",
        "diagnostics_snapshot_ready",
        "diagnostics_snapshot_unavailable",
        "preview_attempted",
        "preview_model_unavailable",
        "writer_attempted",
        "writer_adapter_failed",
        "effective_plan_not_applicable",
        "analysis_rebuild_pending",
        "save_action_not_observed",
        "save_request_pending",
        "save_action_succeeded",
        "save_action_failed",
        "operation_cancelled",
        "not_evaluable",
    }
)
_DEBUG_SILENCE_REASON_CODES = frozenset(
    {
        "not_evaluable",
        "writer_projection_unavailable",
        "silence_coverage_insufficient",
        "provenance_unavailable",
        "base_event_overlaps_silence_core",
        "required_zero_missing",
        "admission_boundary_invalid",
        "explained_manual_adjustment",
        "explained_long_vowel_decay",
        "explained_allowed_short_bridge",
        "positive_writer_control_point_and_interpolation_in_silence_core",
        "positive_writer_control_point_in_silence_core",
        "positive_writer_interpolation_in_silence_core",
        "boundary_overlap_only",
        "clear_no_positive_opening",
        "boundary_interval_unassigned",
        "cross_vowel_handoff_crosses_silence_core",
        "cross_vowel_handoff_exceeds_full_span_limit",
    }
)
_DEBUG_DOWNSTREAM_STATUS = frozenset(
    {"completed", "skipped", "not_attempted", "not_evaluated"}
)


def _debug_safe_failure_code(value: object) -> str:
    """Return an allowlisted failure code without persisting exception text."""
    if value is None:
        return "not_applicable"
    if isinstance(value, str) and value in _DEBUG_FAILURE_CODES:
        return value
    return "unknown_contract_failure"


def _debug_safe_silence_reason(value: object) -> str:
    return _debug_allowlisted(value, _DEBUG_SILENCE_REASON_CODES, "not_evaluable")


def _debug_allowlisted(value: object, allowed: frozenset[str], fallback: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    return fallback


def _debug_safe_index(value: object, fallback: str) -> int | str:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return fallback


def _debug_failure_domain(code: str) -> str:
    if code in {
        "identity_mismatch",
        "adjustment_snapshot_mismatch",
        "shape_parameters_mismatch",
        "adjustment_contract_invalid",
    }:
        return "adjustment_contract"
    if code in {"duration_unavailable"}:
        return "duration"
    if code in {"timeline_metadata_invalid"}:
        return "timeline_metadata"
    if code in {"long_vowel_metadata_invalid"}:
        return "long_vowel_metadata"
    if code in {"observation_metadata_invalid"}:
        return "observation_metadata"
    if code in {"admission_boundary_invalid"}:
        return "effective_shape"
    if code in {"diagnostics_snapshot_unavailable"}:
        return "diagnostics_snapshot"
    if code in {"writer_input_invalid", "writer_adapter_failed"}:
        return "writer_input"
    if code in {
        "base_input_unavailable",
        "plan_missing",
        "invalid_plan_shape",
        "base_input_contract_error",
    }:
        return "base_input"
    return "unknown"


def _debug_failure_context_from_error(
    error: BaseException,
    *,
    phase: str,
) -> dict[str, Any]:
    exception_type = type(error).__name__
    if exception_type not in {"AdjustmentContractError", "TypeError", "ValueError"}:
        exception_type = "unknown"
    safe_code = _debug_safe_failure_code(getattr(error, "safe_code", None))
    if safe_code in {"not_applicable", "none"}:
        safe_code = "unknown_contract_failure"
    safe_field_code = _debug_allowlisted(
        getattr(error, "safe_field_code", None),
        _DEBUG_FIELD_CODES,
        "unknown",
    )
    event_index = _debug_safe_index(
        getattr(error, "event_index", None),
        "not_available",
    )
    source_event_index = _debug_safe_index(
        getattr(error, "source_event_index", None),
        "not_available",
    )
    index_status = (
        "available"
        if isinstance(event_index, int) or isinstance(source_event_index, int)
        else "not_available"
    )
    error_phase = getattr(error, "safe_phase", None)
    return {
        "phase": _debug_allowlisted(error_phase, _DEBUG_PHASES, _debug_allowlisted(phase, _DEBUG_PHASES, "unknown")),
        "domain": _debug_failure_domain(safe_code),
        "code": safe_code,
        "exception_type": exception_type,
        "field_code": safe_field_code,
        "event_index": event_index,
        "source_event_index": source_event_index,
        "index_status": index_status,
        "observed_stage": "ui_sync_context",
    }


def _debug_success_failure_context() -> dict[str, Any]:
    return {
        "phase": "none",
        "domain": "none",
        "code": "none",
        "exception_type": "not_applicable",
        "field_code": "not_applicable",
        "event_index": "not_applicable",
        "source_event_index": "not_applicable",
        "index_status": "not_applicable",
        "observed_stage": "ui_sync_context",
    }


def _debug_safe_failure_context(value: object, *, ready: bool) -> dict[str, Any]:
    if ready:
        return _debug_success_failure_context()
    raw = value if isinstance(value, dict) else {}
    code = _debug_safe_failure_code(raw.get("code"))
    if code in {"not_applicable", "none"}:
        code = "unknown_contract_failure"
    event_index = _debug_safe_index(raw.get("event_index"), "not_available")
    source_event_index = _debug_safe_index(
        raw.get("source_event_index"),
        "not_available",
    )
    return {
        "phase": _debug_allowlisted(raw.get("phase"), _DEBUG_PHASES, "unknown"),
        "domain": _debug_allowlisted(
            raw.get("domain"),
            _DEBUG_DOMAINS,
            _debug_failure_domain(code),
        ),
        "code": code,
        "exception_type": _debug_allowlisted(
            raw.get("exception_type"),
            _DEBUG_EXCEPTION_TYPES,
            "unknown",
        ),
        "field_code": _debug_allowlisted(
            raw.get("field_code"),
            _DEBUG_FIELD_CODES,
            "unknown",
        ),
        "event_index": event_index,
        "source_event_index": source_event_index,
        "index_status": _debug_allowlisted(
            raw.get("index_status"),
            _DEBUG_INDEX_STATUS,
            "available"
            if isinstance(event_index, int) or isinstance(source_event_index, int)
            else "not_available",
        ),
        "observed_stage": _debug_allowlisted(
            raw.get("observed_stage"),
            frozenset(
                {
                    "ui_sync_context",
                    "effective_shape",
                    "preview_projection",
                    "writer_projection",
                    "vmd_save",
                    "debug_store_write",
                    "unknown",
                }
            ),
            "unknown",
        ),
    }


def _debug_boundary_admission_key(admission: object) -> str:
    boundary_only = bool(getattr(admission, "boundary_only", False))
    boundary_frame = getattr(admission, "boundary_frame", None)
    event_index = getattr(admission, "event_index", None)
    vowel = getattr(admission, "vowel", None)
    if (
        not boundary_only
        or isinstance(event_index, bool)
        or not isinstance(event_index, int)
        or not isinstance(vowel, str)
        or isinstance(boundary_frame, bool)
        or not isinstance(boundary_frame, int)
    ):
        return "not_applicable"
    origin_shape_id = getattr(admission, "origin_shape_id", None)
    shape_value = (
        str(origin_shape_id)
        if isinstance(origin_shape_id, int) and not isinstance(origin_shape_id, bool)
        else "not_available"
    )
    return (
        f"event:{event_index}|vowel:{vowel}|frame:{boundary_frame}|"
        f"shape:{shape_value}"
    )


def _debug_boundary_admission_checks(
    admission: object,
    effective_plan: object | None,
) -> dict[str, object]:
    effective_frame_range = getattr(admission, "effective_frame_range", None)
    if bool(getattr(admission, "boundary_only", False)):
        candidate_range = "zero_width"
    elif (
        isinstance(effective_frame_range, (tuple, list))
        and len(effective_frame_range) == 2
        and all(isinstance(value, int) and not isinstance(value, bool) for value in effective_frame_range)
    ):
        start_frame, end_frame = effective_frame_range
        candidate_range = (
            "zero_width"
            if start_frame == end_frame
            else "non_zero"
            if end_frame > start_frame
            else "reversed"
        )
    else:
        candidate_range = "not_available"

    event_peak_value: object = "not_available"
    event_index = getattr(admission, "event_index", None)
    candidate_events = ()
    if effective_plan is not None:
        candidate_events = (getattr(effective_plan, "effective_events", ()) or ()) + (
            getattr(effective_plan, "base_events", ()) or ()
        )
    for event in candidate_events:
        if getattr(event, "base_event_index", None) != event_index:
            continue
        peak_value = getattr(event, "peak_value", None)
        if isinstance(peak_value, (int, float)) and not isinstance(peak_value, bool) and math.isfinite(float(peak_value)):
            event_peak_value = float(peak_value)
        break

    boundary_only = bool(getattr(admission, "boundary_only", False))
    rejection_reason_code = getattr(admission, "rejection_reason_code", None)
    if boundary_only:
        decision = "accepted_boundary_only"
    elif rejection_reason_code == "admission_boundary_invalid":
        decision = "rejected_boundary_invalid"
    else:
        decision = "not_applicable"

    return {
        "candidate_range": candidate_range,
        "positive_point_kinds_empty": not bool(
            getattr(admission, "positive_point_kinds", ()) or ()
        ),
        "boundary_positive_point_kinds_empty": (
            True if boundary_only else "not_available"
        ),
        "positive_core_frame_ranges_empty": not bool(
            getattr(admission, "positive_core_frame_ranges", ()) or ()
        ),
        "matching_end_zero": True if boundary_only else "not_available",
        "shape_provenance_available": (
            bool(getattr(admission, "origin_shape_id", None) is not None)
            if boundary_only
            else "not_available"
        ),
        "boundary_relation_verified": (
            getattr(admission, "boundary_relation", "not_applicable")
            != "not_applicable"
            if boundary_only
            else "not_available"
        ),
        "event_peak_value": event_peak_value,
        "decision": decision,
    }


def _build_debug_silence_observations(
    silence_intervals: Sequence[dict],
    writer_points: Sequence[tuple[int, str, float]],
    *,
    frame_rate: int = 30,
    open_epsilon: float = 1e-9,
    observation_contracts: Sequence[object] | None = None,
    effective_plan: object | None = None,
    raw_writer_points: Sequence[tuple[int, str, float]] | None = None,
    provenance_rows: Sequence[dict] | None = None,
    unassigned_boundary_admissions: list[dict] | None = None,
) -> list[dict]:
    """Measure silence-core opening without changing the production projection."""

    def _merge_ranges(frames: Sequence[int]) -> tuple[tuple[int, int], ...]:
        ordered = sorted(set(frames))
        if not ordered:
            return ()
        ranges: list[tuple[int, int]] = []
        start = ordered[0]
        end = start + 1
        for frame_no in ordered[1:]:
            if frame_no == end:
                end += 1
                continue
            ranges.append((start, end))
            start = frame_no
            end = frame_no + 1
        ranges.append((start, end))
        return tuple(ranges)

    def _interval_frame_ranges(start_sec: float, end_sec: float) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
        core_frames: list[int] = []
        fringe_frames: list[int] = []
        first_frame = max(0, math.floor(start_sec * frame_rate) - 1)
        last_frame = math.ceil(end_sec * frame_rate) + 1
        for frame_no in range(first_frame, last_frame):
            cell_start = frame_no / frame_rate
            cell_end = (frame_no + 1) / frame_rate
            overlap_start = max(start_sec, cell_start)
            overlap_end = min(end_sec, cell_end)
            if overlap_end <= overlap_start:
                continue
            if start_sec <= cell_start and cell_end <= end_sec:
                core_frames.append(frame_no)
            else:
                fringe_frames.append(frame_no)
        return _merge_ranges(core_frames), _merge_ranges(fringe_frames)

    def _frames_in_ranges(ranges: Sequence[tuple[int, int]]) -> set[int]:
        return {frame_no for start, end in ranges for frame_no in range(start, end)}

    points_by_vowel: dict[str, dict[int, float]] = {}
    for frame_no, vowel, value in writer_points:
        if not isinstance(frame_no, int) or not isinstance(vowel, str):
            continue
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            continue
        points_by_vowel.setdefault(vowel, {})[frame_no] = float(value)

    provenance_by_key: dict[tuple[int, str], list[dict]] = {}
    if provenance_rows is not None:
        for provenance in provenance_rows:
            if not isinstance(provenance, dict):
                continue
            normalized_key = provenance.get("normalized_key")
            if not isinstance(normalized_key, (list, tuple)) or len(normalized_key) != 2:
                continue
            frame_no, vowel = normalized_key
            if isinstance(frame_no, bool) or not isinstance(frame_no, int):
                continue
            if not isinstance(vowel, str):
                continue
            provenance_by_key.setdefault((frame_no, vowel), []).append(provenance)

    def _provenance_for_keys(keys: Sequence[tuple[int, str]]) -> tuple[list[dict], list[list[object]]]:
        records: list[dict] = []
        missing: list[list[object]] = []
        seen: set[tuple[int, str, str]] = set()
        for frame_no, vowel in sorted(set(keys)):
            matches = provenance_by_key.get((frame_no, vowel), ())
            if not matches:
                missing.append([frame_no, vowel])
                continue
            for provenance in matches:
                point_id = str(provenance.get("raw_point_id", ""))
                identity = (frame_no, vowel, point_id)
                if identity in seen:
                    continue
                seen.add(identity)
                records.append(
                    {
                        "frame_no": frame_no,
                        "vowel": vowel,
                        "origin_shape_id": provenance.get("origin_shape_id"),
                        "source_event_indices": list(
                            provenance.get("source_event_indices", ()) or ()
                        ),
                        "raw_point_id": provenance.get("raw_point_id"),
                        "point_kind": provenance.get("point_kind"),
                        "required_zero": provenance.get("required_zero"),
                        "raw_key": provenance.get("raw_key"),
                        "normalized_key": provenance.get("normalized_key"),
                        "normalization_action": provenance.get("normalization_action"),
                        "origin_kind": provenance.get("origin_kind"),
                    }
                )
        return records, missing

    def _frame_range_intersects(
        frame_range: object,
        observed_frames: set[int],
    ) -> bool:
        if not isinstance(frame_range, (list, tuple)) or len(frame_range) != 2:
            return False
        start_frame, end_frame = frame_range
        if (
            isinstance(start_frame, bool)
            or not isinstance(start_frame, int)
            or isinstance(end_frame, bool)
            or not isinstance(end_frame, int)
            or end_frame <= start_frame
        ):
            return False
        return bool(observed_frames & set(range(start_frame, end_frame)))

    def _admission_payload(
        admission: object,
        *,
        assignment_status: str = "not_applicable",
    ) -> dict:
        effective_frame_range = getattr(admission, "effective_frame_range", None)
        return {
            "event_index": getattr(admission, "event_index", None),
            "vowel": getattr(admission, "vowel", None),
            "origin_shape_id": getattr(admission, "origin_shape_id", None),
            "positive_point_kinds": list(
                getattr(admission, "positive_point_kinds", ()) or ()
            ),
            "source_event_indices": list(
                getattr(admission, "source_event_indices", ()) or ()
            ),
            "effective_frame_range": (
                list(effective_frame_range) if effective_frame_range is not None else None
            ),
            "boundary_only": getattr(admission, "boundary_only", False),
            "boundary_frame": getattr(admission, "boundary_frame", None),
            "boundary_point_kind": getattr(admission, "boundary_point_kind", None),
            "boundary_relation": getattr(
                admission, "boundary_relation", "not_applicable"
            ),
            "boundary_action": getattr(
                admission, "boundary_action", "not_applicable"
            ),
            "admission_key": _debug_boundary_admission_key(admission),
            "assignment_status": assignment_status,
            "boundary_admission_checks": _debug_boundary_admission_checks(
                admission,
                effective_plan,
            ),
            "base_event_silence_core_overlap": getattr(
                admission, "base_event_silence_core_overlap", False
            ),
            "positive_core_frame_ranges": [
                list(item)
                for item in getattr(admission, "positive_core_frame_ranges", ()) or ()
            ],
            "long_vowel_role": getattr(admission, "long_vowel_role", None),
            "manual_adjustment_applied": getattr(
                admission, "manual_adjustment_applied", False
            ),
            "enabled": getattr(admission, "enabled", None),
            "rejection_reason_code": getattr(
                admission, "rejection_reason_code", None
            ),
            "required_zero_frame_ranges": [
                list(item)
                for item in getattr(admission, "required_zero_frame_ranges", ()) or ()
            ],
        }

    rows: list[dict] = []
    for interval in silence_intervals:
        if not isinstance(interval, dict):
            continue
        start_sec = interval.get("start_sec")
        end_sec = interval.get("end_sec")
        if not isinstance(start_sec, (int, float)) or not isinstance(end_sec, (int, float)):
            continue
        if end_sec <= start_sec:
            continue

        core_ranges, fringe_ranges = _interval_frame_ranges(float(start_sec), float(end_sec))
        core_frames = _frames_in_ranges(core_ranges)
        fringe_frames = _frames_in_ranges(fringe_ranges)
        positive_control_frames: list[int] = []
        positive_control_points: list[tuple[int, str]] = []
        positive_fringe_control_frames: list[int] = []
        positive_fringe_control_points: list[tuple[int, str]] = []
        positive_interpolations: list[dict] = []
        for vowel, points in points_by_vowel.items():
            ordered = sorted(points.items())
            for frame_no, value in ordered:
                if frame_no in core_frames and value > open_epsilon:
                    positive_control_frames.append(frame_no)
                    positive_control_points.append((frame_no, vowel))
                elif frame_no in fringe_frames and value > open_epsilon:
                    positive_fringe_control_frames.append(frame_no)
                    positive_fringe_control_points.append((frame_no, vowel))
            for (left_frame, left_value), (right_frame, right_value) in zip(
                ordered,
                ordered[1:],
            ):
                if right_frame <= left_frame:
                    continue
                segment_start = left_frame / frame_rate
                segment_end = right_frame / frame_rate
                overlap_start = max(float(start_sec), segment_start)
                overlap_end = min(float(end_sec), segment_end)
                if overlap_end <= overlap_start:
                    continue
                span = float(right_frame - left_frame)

                def _value_at(time_sec: float) -> float:
                    ratio = (time_sec * frame_rate - left_frame) / span
                    return left_value + ((right_value - left_value) * ratio)

                overlap_values = (_value_at(overlap_start), _value_at(overlap_end))
                max_value = max(overlap_values)
                if max_value > open_epsilon:
                    segment_frames = set(
                        range(
                            math.floor(overlap_start * frame_rate),
                            math.ceil(overlap_end * frame_rate),
                        )
                    )
                    if segment_frames & core_frames:
                        zone = "core"
                    elif segment_frames & fringe_frames:
                        zone = "fringe"
                    else:
                        zone = "unobserved"
                    positive_interpolations.append(
                        {
                            "vowel": vowel,
                            "start_sec": overlap_start,
                            "end_sec": overlap_end,
                            "max_value": max_value,
                            "source_frames": [left_frame, right_frame],
                            "zone": zone,
                        }
                    )

        positive_control_frames = sorted(set(positive_control_frames))
        positive_fringe_control_frames = sorted(set(positive_fringe_control_frames))
        positive_interpolations.sort(key=lambda item: (item["start_sec"], item["end_sec"]))
        core_interpolations = [
            item for item in positive_interpolations if item.get("zone") == "core"
        ]
        fringe_interpolations = [
            item for item in positive_interpolations if item.get("zone") == "fringe"
        ]
        has_control_opening = bool(positive_control_frames)
        has_interpolation_opening = bool(core_interpolations)
        has_fringe_opening = bool(positive_fringe_control_frames or fringe_interpolations)
        coverage_status = str(interval.get("coverage_status", "unobserved"))
        provenance_status = str(interval.get("provenance_status", "unavailable"))
        provenance_keys = list(positive_control_points) + list(positive_fringe_control_points)
        for interpolation in positive_interpolations:
            vowel = interpolation.get("vowel")
            if not isinstance(vowel, str):
                continue
            provenance_keys.extend(
                (int(frame_no), vowel)
                for frame_no in interpolation.get("source_frames", ())
                if isinstance(frame_no, int) and not isinstance(frame_no, bool)
            )
        provenance_details, missing_provenance_keys = _provenance_for_keys(provenance_keys)
        if provenance_rows is not None:
            provenance_status = (
                "complete" if not missing_provenance_keys else "unavailable"
            )

        handoff_rows = []
        handoff_contract_violation = False
        handoff_rejection_reasons: list[str] = []
        for handoff in getattr(effective_plan, "observation_handoffs", ()) or ():
            handoff_core_ranges = tuple(
                getattr(handoff, "silence_core_frame_ranges", ()) or ()
            )
            handoff_overlaps_interval = bool(
                core_frames & _frames_in_ranges(handoff_core_ranges)
            )
            handoff_rows.append(
                {
                    "span_start_index": getattr(handoff, "span_start_index", None),
                    "span_end_index": getattr(handoff, "span_end_index", None),
                    "previous_non_zero_event_index": getattr(
                        handoff, "previous_non_zero_event_index", None
                    ),
                    "next_non_zero_event_index": getattr(
                        handoff, "next_non_zero_event_index", None
                    ),
                    "candidate_kind": getattr(handoff, "candidate_kind", None),
                    "enabled": getattr(handoff, "enabled", None),
                    "full_span_start_frame": getattr(handoff, "full_span_start_frame", None),
                    "full_span_end_frame": getattr(handoff, "full_span_end_frame", None),
                    "silence_core_overlap": getattr(handoff, "silence_core_overlap", False),
                    "rejection_reason_code": getattr(handoff, "rejection_reason_code", None),
                }
            )
            rejection_reason = getattr(handoff, "rejection_reason_code", None)
            if (
                handoff_overlaps_interval
                and getattr(handoff, "silence_core_overlap", False)
                and rejection_reason
                in {
                    "cross_vowel_handoff_crosses_silence_core",
                    "required_zero_missing",
                }
            ):
                handoff_contract_violation = True
                handoff_rejection_reasons.append(str(rejection_reason))

        base_event_admission_rows: list[dict] = []
        base_event_contract_violation = False
        base_event_rejection_reasons: list[str] = []
        explained_reasons: list[str] = []
        for admission in getattr(effective_plan, "event_silence_admissions", ()) or ():
            admission_core_ranges = tuple(
                getattr(admission, "positive_core_frame_ranges", ()) or ()
            )
            admission_frame_range = getattr(admission, "effective_frame_range", None)
            admission_boundary_only = bool(
                getattr(admission, "boundary_only", False)
            )
            admission_boundary_frame = getattr(admission, "boundary_frame", None)
            boundary_belongs_to_interval = (
                admission_boundary_only
                and isinstance(admission_boundary_frame, int)
                and not isinstance(admission_boundary_frame, bool)
                and admission_boundary_frame in (core_frames | fringe_frames)
            )
            admission_overlaps_interval = bool(
                core_frames & _frames_in_ranges(admission_core_ranges)
            ) or _frame_range_intersects(admission_frame_range, core_frames | fringe_frames)
            admission_overlaps_interval = admission_overlaps_interval or boundary_belongs_to_interval
            if not admission_overlaps_interval:
                if admission_boundary_only and unassigned_boundary_admissions is not None:
                    unassigned_payload = _admission_payload(
                        admission,
                        assignment_status="unassigned",
                    )
                    unassigned_payload.update(
                        {
                            "boundary_action": "not_applicable",
                            "reason_code": _debug_safe_silence_reason(
                                "boundary_interval_unassigned"
                            ),
                        }
                    )
                    unassigned_boundary_admissions.append(unassigned_payload)
                continue
            admission_payload = _admission_payload(
                admission,
                assignment_status=(
                    "assigned_interval" if admission_boundary_only else "not_applicable"
                ),
            )
            base_event_admission_rows.append(admission_payload)
            positive_core_overlap = bool(
                core_frames & _frames_in_ranges(admission_core_ranges)
            )
            rejection_reason = admission_payload.get("rejection_reason_code")
            if (
                admission_payload.get("base_event_silence_core_overlap")
                and not admission_payload.get("enabled", True)
                and rejection_reason
                in {
                    "base_event_overlaps_silence_core",
                    "required_zero_missing",
                    "admission_boundary_invalid",
                }
                and (
                    bool(core_frames & _frames_in_ranges(admission_core_ranges))
                    or bool(admission_payload.get("required_zero_frame_ranges"))
                )
            ):
                base_event_contract_violation = True
                base_event_rejection_reasons.append(str(rejection_reason))
            elif positive_core_overlap and admission_payload.get("enabled", False):
                if admission_payload.get("manual_adjustment_applied", False):
                    explained_reasons.append("explained_manual_adjustment")
                elif admission_payload.get("long_vowel_role") is not None:
                    explained_reasons.append("explained_long_vowel_decay")

        for handoff in handoff_rows:
            if (
                handoff.get("enabled")
                and handoff.get("silence_core_overlap")
                and handoff.get("rejection_reason_code") is None
            ):
                explained_reasons.append("explained_allowed_short_bridge")

        if not writer_points:
            result = "not_evaluable"
            reason_code = "writer_projection_unavailable"
            evaluation_status = "not_evaluable"
        elif coverage_status != "complete":
            result = "not_evaluable"
            reason_code = "silence_coverage_insufficient"
            evaluation_status = "not_evaluable"
        elif provenance_status != "complete":
            result = "not_evaluable"
            reason_code = "provenance_unavailable"
            evaluation_status = "not_evaluable"
        elif base_event_contract_violation:
            result = "contract_violation"
            reason_code = base_event_rejection_reasons[0]
            evaluation_status = "evaluable"
        elif handoff_contract_violation:
            result = "contract_violation"
            reason_code = handoff_rejection_reasons[0]
            evaluation_status = "evaluable"
        elif (has_control_opening or has_interpolation_opening) and explained_reasons:
            result = "explained"
            reason_code = sorted(set(explained_reasons))[0]
            evaluation_status = "evaluable"
        elif has_control_opening and has_interpolation_opening:
            result = "suspicious"
            reason_code = "positive_writer_control_point_and_interpolation_in_silence_core"
            evaluation_status = "evaluable"
        elif has_control_opening:
            result = "suspicious"
            reason_code = "positive_writer_control_point_in_silence_core"
            evaluation_status = "evaluable"
        elif has_interpolation_opening:
            result = "suspicious"
            reason_code = "positive_writer_interpolation_in_silence_core"
            evaluation_status = "evaluable"
        elif has_fringe_opening:
            result = "clear"
            reason_code = "boundary_overlap_only"
            evaluation_status = "evaluable"
        else:
            result = "clear"
            reason_code = "clear_no_positive_opening"
            evaluation_status = "evaluable"

        rows.append(
            {
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": interval.get("duration_sec"),
                "candidate_classification": interval.get("classification"),
                "coverage_status": coverage_status,
                "provenance_status": provenance_status,
                "silence_core_frame_ranges": [list(item) for item in core_ranges],
                "boundary_fringe_frame_ranges": [list(item) for item in fringe_ranges],
                "silence_core_overlap": bool(core_ranges),
                "evaluation_status": evaluation_status,
                "result": result,
                "reason_code": _debug_safe_silence_reason(reason_code),
                "positive_frames": positive_control_frames,
                "positive_fringe_frames": positive_fringe_control_frames,
                "positive_interpolated_intervals": positive_interpolations,
                "handoffs": handoff_rows,
                "base_event_admissions": base_event_admission_rows,
                "provenance": provenance_details,
                "missing_provenance_keys": missing_provenance_keys,
                "contract_violation_reasons": sorted(
                    {
                        _debug_safe_silence_reason(reason)
                        for reason in base_event_rejection_reasons + handoff_rejection_reasons
                    }
                ),
                "explained_reasons": sorted(
                    {_debug_safe_silence_reason(reason) for reason in explained_reasons}
                ),
                "raw_writer_point_count": len(raw_writer_points or writer_points),
                "normalized_writer_point_count": len(writer_points),
            }
        )
    return rows

class AnalysisProgressDialog(wx.Dialog):
    def __init__(self, parent, on_cancel_callback):
        super().__init__(parent, title="解析実行中", style=wx.CAPTION)
        self.on_cancel_callback = on_cancel_callback
        self.cancel_requested = False
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        msg_text = wx.StaticText(self, label="リップシンク解析を実行しています...\nしばらくお待ちください。\n\n※ 歌唱・楽曲混在・環境ノイズ過多な音声では、\n　 解析に通常より時間がかかる場合があります。")
        sizer.Add(msg_text, 0, wx.ALL | wx.EXPAND, 15)
        
        self.gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        sizer.Add(self.gauge, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 15)
        
        self.phase_text = wx.StaticText(self, label="準備中")
        font = self.phase_text.GetFont()
        font.MakeBold()
        self.phase_text.SetFont(font)
        sizer.Add(self.phase_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 15)
        
        self.warning_text = wx.StaticText(self, label="")
        self.warning_text.SetForegroundColour(wx.RED)
        sizer.Add(self.warning_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 15)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_cancel = ThemeButton(self, label="分析中止")
        self.Bind(wx.EVT_BUTTON, self._on_cancel, self.btn_cancel)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_cancel, 0, wx.ALL, 10)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND)
        self.SetSizerAndFit(sizer)
        self.CenterOnParent()
        
        self.pulse_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_pulse_timer, self.pulse_timer)
        self.pulse_timer.Start(50)
        
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
        from gui_wx.theme import ThemeManager
        if hasattr(parent, 'ui_state'):
            ThemeManager.apply_theme(parent.ui_state.theme_mode, self)

    def _on_pulse_timer(self, event):
        self.gauge.Pulse()

    def _on_cancel(self, event):
        self.cancel_requested = True
        self.pulse_timer.Stop()
        self.btn_cancel.Disable()
        self.phase_text.SetLabel("中止要求中。処理終了を待っています")
        if self.on_cancel_callback:
            self.on_cancel_callback()
            
    def _on_close(self, event):
        event.Veto()
        
    def set_phase(self, phase):
        if not self.cancel_requested:
            self.phase_text.SetLabel(phase)
            
    def set_warning(self, msg):
        self.warning_text.SetLabel(msg)


class DeliveryDestinationDialog(wx.Dialog):
    """Collect a delivery parent directory and editable package directory name."""

    def __init__(
        self,
        parent,
        *,
        default_parent: str,
        default_folder: str,
        error_message: str | None = None,
    ):
        super().__init__(
            parent,
            title="MMD一括出力先",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._selection: tuple[Path, str] | None = None

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        form_sizer = wx.FlexGridSizer(cols=3, vgap=8, hgap=8)
        form_sizer.AddGrowableCol(1, 1)

        form_sizer.Add(
            wx.StaticText(self, label="親directory"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.parent_text = wx.TextCtrl(
            self,
            value=str(default_parent or ""),
            style=wx.TE_READONLY,
        )
        form_sizer.Add(self.parent_text, 1, wx.EXPAND)
        self.browse_button = ThemeButton(self, label="参照...")
        form_sizer.Add(self.browse_button, 0)

        form_sizer.Add(
            wx.StaticText(self, label="folder名"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.folder_text = wx.TextCtrl(self, value=str(default_folder or ""))
        form_sizer.Add(self.folder_text, 1, wx.EXPAND)
        form_sizer.Add((1, 1), 0)

        root_sizer.Add(form_sizer, 1, wx.ALL | wx.EXPAND, 12)
        root_sizer.Add(wx.StaticText(self, label="出力先preview"), 0, wx.LEFT | wx.RIGHT, 12)
        self.preview_text = wx.StaticText(self, label="")
        root_sizer.Add(self.preview_text, 0, wx.ALL | wx.EXPAND, 12)

        self.error_text = wx.StaticText(self, label=error_message or "")
        self.error_text.SetForegroundColour(wx.RED)
        root_sizer.Add(self.error_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        root_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 12)
        self.SetSizer(root_sizer)

        self.Bind(wx.EVT_BUTTON, self._on_browse, self.browse_button)
        self.Bind(wx.EVT_BUTTON, self._on_output, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.folder_text)

        self.SetMinSize(wx.Size(560, -1))
        self.Layout()
        self.Fit()
        self.Layout()
        self.CentreOnParent()
        self._update_preview()
        parent_state = getattr(parent, "ui_state", None)
        ThemeManager.apply_theme(
            getattr(parent_state, "theme_mode", ThemeMode.SYSTEM),
            self,
        )

    def _on_browse(self, event) -> None:
        with wx.DirDialog(
            self,
            message="MMD一括出力の親directoryを選択してください",
            defaultPath=self.parent_text.GetValue(),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.parent_text.SetValue(dialog.GetPath())
                self._update_preview()

    def _on_text_changed(self, event) -> None:
        self._update_preview()
        event.Skip()

    def _update_preview(self) -> None:
        parent_text = self.parent_text.GetValue().strip()
        folder_text = self.folder_text.GetValue()
        if not parent_text or not folder_text:
            preview = "(未入力)"
        else:
            preview = str(Path(parent_text) / folder_text)
        self.preview_text.SetLabel(preview)
        self.Layout()

    def _on_output(self, event) -> None:
        parent_text = self.parent_text.GetValue().strip()
        folder_text = self.folder_text.GetValue()
        if not parent_text or not folder_text:
            self.error_text.SetLabel("親directoryとfolder名を入力してください。")
            self.Layout()
            return
        self._selection = (Path(parent_text), folder_text)
        self.EndModal(wx.ID_OK)

    def _on_cancel(self, event) -> None:
        self._selection = None
        self.EndModal(wx.ID_CANCEL)

    def get_selection(self) -> tuple[Path, str] | None:
        return self._selection


def _debug_piecewise_value(
    points: Sequence[tuple[int, float]],
    frame_no: int,
) -> float:
    ordered = sorted(points, key=lambda item: item[0])
    if not ordered or frame_no < ordered[0][0] or frame_no > ordered[-1][0]:
        return 0.0
    for point_frame, point_value in ordered:
        if point_frame == frame_no:
            return float(point_value)
    for (left_frame, left_value), (right_frame, right_value) in zip(
        ordered,
        ordered[1:],
    ):
        if left_frame <= frame_no <= right_frame:
            span = right_frame - left_frame
            if span <= 0:
                return max(float(left_value), float(right_value))
            ratio = (frame_no - left_frame) / span
            return float(left_value) + (
                (float(right_value) - float(left_value)) * ratio
            )
    return 0.0


def _debug_silence_core_frame_ranges(
    silence_intervals: Sequence[dict],
    *,
    frame_rate: int = 30,
) -> tuple[tuple[int, int], ...]:
    frames: set[int] = set()
    for interval in silence_intervals:
        if not isinstance(interval, dict):
            continue
        start_sec = interval.get("start_sec")
        end_sec = interval.get("end_sec")
        if not isinstance(start_sec, (int, float)) or not isinstance(end_sec, (int, float)):
            continue
        if end_sec <= start_sec:
            continue
        first_frame = max(0, math.floor(float(start_sec) * frame_rate) - 1)
        last_frame = math.ceil(float(end_sec) * frame_rate) + 1
        for frame_no in range(first_frame, last_frame):
            cell_start = frame_no / frame_rate
            cell_end = (frame_no + 1) / frame_rate
            if float(start_sec) <= cell_start and cell_end <= float(end_sec):
                frames.add(frame_no)
    ordered = sorted(frames)
    if not ordered:
        return ()
    ranges: list[tuple[int, int]] = []
    start = ordered[0]
    end = start + 1
    for frame_no in ordered[1:]:
        if frame_no == end:
            end += 1
            continue
        ranges.append((start, end))
        start = frame_no
        end = frame_no + 1
    ranges.append((start, end))
    return tuple(ranges)


def _build_debug_silence_curve_comparison(
    silence_intervals: Sequence[dict],
    preview_segments_by_vowel: dict[str, Sequence[Sequence[tuple[int, float]]]],
    writer_points: Sequence[tuple[int, str, float]],
    *,
    frame_rate: int = 30,
    open_epsilon: float = 1e-9,
) -> list[dict[str, Any]]:
    writer_by_vowel: dict[str, list[tuple[int, float]]] = {}
    for frame_no, vowel, value in writer_points:
        writer_by_vowel.setdefault(str(vowel), []).append((int(frame_no), float(value)))

    rows: list[dict[str, Any]] = []
    for interval_index, interval in enumerate(silence_intervals):
        if not isinstance(interval, dict):
            continue
        core_ranges = _debug_silence_core_frame_ranges((interval,), frame_rate=frame_rate)
        for vowel in sorted(set(writer_by_vowel).union(preview_segments_by_vowel)):
            preview_segments = preview_segments_by_vowel.get(vowel, ())
            writer_curve = writer_by_vowel.get(vowel, ())
            sampled = []
            for start_frame, end_frame in core_ranges:
                for frame_no in range(start_frame, end_frame + 1):
                    preview_value = max(
                        (
                            _debug_piecewise_value(segment, frame_no)
                            for segment in preview_segments
                        ),
                        default=0.0,
                    )
                    writer_value = _debug_piecewise_value(writer_curve, frame_no)
                    sampled.append((frame_no, preview_value, writer_value))
            if not sampled:
                continue
            differences = [abs(preview - writer) for _, preview, writer in sampled]
            rows.append(
                {
                    "interval_index": interval_index,
                    "vowel": vowel,
                    "core_frame_ranges": [list(item) for item in core_ranges],
                    "sample_count": len(sampled),
                    "preview_positive_frame_count": sum(
                        value > open_epsilon for _, value, _ in sampled
                    ),
                    "writer_positive_frame_count": sum(
                        value > open_epsilon for _, _, value in sampled
                    ),
                    "max_abs_diff": max(differences, default=0.0),
                    "within_tolerance": max(differences, default=0.0) <= 1e-9,
                }
            )
    return rows


def _format_whisper_model_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024


_DEBUG_PROJECTION_VALUE_TOLERANCE = 1e-9


def _compare_debug_projection_points(
    preview_lookup: dict[tuple[int, str], float],
    writer_lookup: dict[tuple[int, str], float],
) -> tuple[str, str | None, dict[str, Any]]:
    def to_wire_value(value: float) -> float:
        scalar = float(value)
        return vmd_wire_morph_value(scalar) if math.isfinite(scalar) else scalar

    wire_preview_lookup = {
        key: to_wire_value(value) for key, value in preview_lookup.items()
    }
    wire_writer_lookup = {
        key: to_wire_value(value) for key, value in writer_lookup.items()
    }
    common_keys = sorted(set(wire_preview_lookup).intersection(wire_writer_lookup))
    comparison_points: list[dict[str, Any]] = []
    differences: list[float] = []
    for frame_no, vowel in common_keys:
        preview_value = wire_preview_lookup[(frame_no, vowel)]
        writer_value = wire_writer_lookup[(frame_no, vowel)]
        if math.isfinite(preview_value) and math.isfinite(writer_value):
            difference = abs(preview_value - writer_value)
            differences.append(difference)
            comparison_points.append(
                {
                    "frame_no": frame_no,
                    "vowel": vowel,
                    "preview_value": preview_value,
                    "writer_value": writer_value,
                    "abs_diff": difference,
                    "within_tolerance": difference
                    <= _DEBUG_PROJECTION_VALUE_TOLERANCE,
                }
            )
    missing_preview_keys = sorted(
        set(wire_writer_lookup).difference(wire_preview_lookup)
    )
    missing_writer_keys = sorted(
        set(wire_preview_lookup).difference(wire_writer_lookup)
    )
    max_abs_diff = max(differences) if differences else None
    if not common_keys:
        status = "not_evaluable"
        reason_code = "no_common_control_points"
    elif differences and max_abs_diff > _DEBUG_PROJECTION_VALUE_TOLERANCE:
        status = "contract_violation"
        reason_code = "projection_value_mismatch"
    else:
        status = "completed"
        reason_code = None
    return status, reason_code, {
        "common_point_count": len(common_keys),
        "finite_point_count": len(differences),
        "max_abs_diff": max_abs_diff,
        "within_tolerance": bool(differences)
        and max_abs_diff <= _DEBUG_PROJECTION_VALUE_TOLERANCE,
        "tolerance": _DEBUG_PROJECTION_VALUE_TOLERANCE,
        "comparison_basis": (
            "common_preview_and_writer_vmd_wire_values"
            "+sampled_silence_core_frames"
        ),
        "points": comparison_points,
        "missing_preview_count": len(missing_preview_keys),
        "missing_writer_count": len(missing_writer_keys),
        "missing_preview_keys": missing_preview_keys,
        "missing_writer_keys": missing_writer_keys,
    }


class MainFrame(wx.Frame):
    """
    MMD_AutoLipTool のメインフレーム。
    [MS13-B3]
    - 上中下3領域へレイアウトする最小骨格の上に、
    - 最小メニューバー、主要ボタン、ステータス表示の受け口を配置。
    """
    def __init__(self, *args, transition_evaluation_request=None, cleanup_evaluation_request=None, **kw):
        if transition_evaluation_request is not None and not isinstance(
            transition_evaluation_request, TransitionEvaluationRequest
        ):
            raise TypeError("transition_evaluation_request must be typed or None")
        if cleanup_evaluation_request is not None and not isinstance(
            cleanup_evaluation_request, CleanupEvaluationRequest
        ):
            raise TypeError("cleanup_evaluation_request must be typed or None")
        if cleanup_evaluation_request is not None and transition_evaluation_request is not None:
            raise ValueError("cleanup and explicit transition evaluations cannot be combined")
        if 'title' not in kw:
            kw['title'] = "MMD AutoLipTool"
        if 'size' not in kw:
            kw['size'] = (800, 600)
            
        super().__init__(*args, **kw)
        
        self.controller = None
        self._transition_evaluation_request = transition_evaluation_request
        self._cleanup_evaluation_request = cleanup_evaluation_request
        self._adopted_transition_binding = build_adopted_transition_binding()
        self._adopted_cleanup_binding = build_adopted_cleanup_binding()
        self.ui_state = UiState()
        self._current_job_id = 0
        self._cancel_requested = False
        self._progress_dialog = None
        self._vmd_save_progress_dialog: VmdSaveProgressDialog | None = None
        self._vmd_save_progress_operation_id: int | None = None
        self._timeout_timer = None
        self._worker = None
        self._analysis_info_in_progress = False
        self._active_analysis_job_id = None
        self._analysis_parameter_snapshot = None
        self._analysis_rollback_snapshot = None
        self._analysis_operation_handles: dict[int, object] = {}
        self._selected_event_notice = ""
        self._current_ui_sync_context: UiSyncContext | None = None
        self._current_ui_sync_output_state: OutputEditState | None = None
        self._current_ui_sync_failure_reason: str | None = None
        self._current_ui_sync_diagnostic: dict[str, Any] = {}
        self._last_duration_selection_diagnostic: dict[str, Any] = {
            "status": "not_recorded",
            "candidates": [],
            "selected_source": None,
            "selected_duration_sec": None,
        }
        self._diagnostics_projection_generation = 0
        self._active_preset_display_name: str | None = None
        self._projection_guard = False
        self._selected_preset_id: str | None = None
        self._preset_selection_initialized = False
        self._preset_panel_signature = None
        self._preset_panel_revision = 0
        self._selected_model_profile_id: str | None = None
        self._model_profile_selection_initialized = False
        self._model_profile_panel_signature = None
        self._model_profile_panel_revision = 0
        self._debug_store = AnalysisDebugStore()
        self._active_debug_trace: AnalysisDebugTrace | None = None
        self._accepted_debug_trace: AnalysisDebugTrace | None = None
        self._debug_save_operation_id: str | None = None
        self._debug_operation_handles: dict[str, object] = {}
        self._debug_operation_log_state = "stopped"
        self._debug_operation_log_error: str | None = None
        self._debug_operation_log_path: Path | None = None
        self._exit_prepared = False
        self._pending_exit_operation_handle = None
        self._pending_output_apply: dict[str, object] | None = None
        self._draft_projection_ticket = 0
        self._latest_draft_preview_request: OutputEditDraftProjectionRequest | None = None
        self._pending_selected_event_projection: dict[str, object] | None = None
        self._about_dialog: AboutDialog | None = None
        self._about_job_id = 0
        self._final_output_sync_coordinator = FinalOutputSyncCoordinator(
            self._on_shared_final_output_result
        )
        self._output_edit_draft_projection_coordinator = (
            OutputEditDraftProjectionCoordinator(
                self._on_output_edit_draft_projection_result
            )
        )
        self._shared_final_output_diagnostics: OutputDiagnosticsSnapshot | None = None
        self._accepted_output_preview_cache: tuple[
            object, float, str, str, tuple[object, ...]
        ] | None = None
        self._latest_shared_final_output_request: FinalOutputRequest | None = None
        
        self._init_icon()
        self._init_menu()
        self._init_ui()
        self._refresh_transition_application_status()
        self.right_pane.on_closure_restriction_selection = (
            self._on_closure_restriction_selection
        )
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_history_shortcut)
        
    def _init_icon(self):
        from resource_utils import get_resource_path
        icon_path = get_resource_path("assets/icons/MMD_AutoLipTool.ico")
        if icon_path.is_file():
            with wx.LogNull():
                icon = wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO)
                if icon.IsOk():
                    self.SetIcon(icon)
            
    def _init_menu(self):
        menubar = wx.MenuBar()
        
        # 1. ファイルメニュー
        file_menu = wx.Menu()
        self.mi_workspace_reset = file_menu.Append(
            wx.ID_ANY,
            "新規作業...\tCtrl+N",
            "現在の入力と解析結果をクリアして、新しい作業を開始します",
        )
        file_menu.AppendSeparator()
        self.mi_text_open = file_menu.Append(wx.ID_ANY, "TEXT読み込み...\tCtrl+T", "UTF-8のテキストファイルを読み込みます")
        self.mi_wav_open = file_menu.Append(wx.ID_ANY, "音声読み込み...\tCtrl+W", "音源の音声ファイル(wav/mp3/m4a)を読み込みます")
        
        # [MS14-B2] recent menu 相当
        self.recent_menu = wx.Menu()
        self.mi_recent = file_menu.AppendSubMenu(self.recent_menu, "最近開いたファイル")
        
        self.mi_vmd_save = file_menu.Append(wx.ID_ANY, "VMD保存...\tCtrl+S", "解析結果をVMDとして保存します")
        self.mi_diagnostic_report_save = file_menu.Append(
            wx.ID_ANY,
            "診断レポート保存...",
            "現在の入力・解析・生成・保存可否・診断内容をTEXTレポートとして保存します",
        )
        self.mi_mmd_delivery_export = file_menu.Append(
            wx.ID_ANY,
            "MMD一括出力...",
            "VMD、MMD用WAV、診断レポートを専用directoryへ出力します",
        )
        file_menu.AppendSeparator()
        self.mi_exit = file_menu.Append(wx.ID_EXIT, "終了(&X)", "アプリケーションを終了します")
        menubar.Append(file_menu, "ファイル(&F)")

        # 2. 編集メニュー
        edit_menu = wx.Menu()
        self.mi_adjustment_undo = edit_menu.Append(
            wx.ID_UNDO,
            "出力編集を元に戻す (Ctrl+Z)",
            "直前の出力編集を元に戻します",
        )
        self.mi_adjustment_redo = edit_menu.Append(
            wx.ID_REDO,
            "出力編集をやり直す (Ctrl+Y)",
            "元に戻した出力編集をやり直します",
        )
        edit_menu.AppendSeparator()
        self.mi_adjustment_reset_selected = edit_menu.Append(
            wx.ID_ANY,
            "選択イベントの補正をリセット",
            "選択中イベントの個別補正をリセットします",
        )
        self.mi_adjustment_reset_all = edit_menu.Append(
            wx.ID_ANY,
            "すべての個別補正をリセット",
            "現在の解析結果に対する個別補正をすべてリセットします",
        )
        menubar.Append(edit_menu, "編集(&E)")
        
        # 3. 設定/表示メニュー
        view_menu = wx.Menu()
        self.mi_settings = view_menu.Append(wx.ID_ANY, "設定(&S)...", "各種設定を行います")
        self.mi_debug_mode = view_menu.AppendCheckItem(
            wx.ID_ANY,
            "デバッグモード",
            "解析traceと操作順・変更・処理結果をdebugフォルダへ記録します（セッション限定）",
        )
        self.mi_debug_mode.Check(False)
        
        # [MS15-B5] テーマサブメニュー
        self.theme_menu = wx.Menu()
        self.mi_theme_system = self.theme_menu.AppendRadioItem(wx.ID_ANY, "システムに合わせる")
        self.mi_theme_light = self.theme_menu.AppendRadioItem(wx.ID_ANY, "ライトテーマ")
        self.mi_theme_dark = self.theme_menu.AppendRadioItem(wx.ID_ANY, "ダークテーマ")
        self.mi_theme = view_menu.AppendSubMenu(self.theme_menu, "テーマ(&T)")
        
        menubar.Append(view_menu, "設定/表示(&V)")
        
        # 4. ヘルプメニュー
        help_menu = wx.Menu()
        self.mi_help = help_menu.Append(wx.ID_ANY, "使い方(&H)...", "使い方を確認します")
        self.mi_about = help_menu.Append(wx.ID_ABOUT, "About(&A)...", "このアプリについて")
        menubar.Append(help_menu, "ヘルプ(&H)")
        
        self.SetMenuBar(menubar)
        
        # [MS13-B3] 未実装項目は無効化 / [MS14-B2] これらは update_action_states 側で管理するが、
        # メニュー自体への初期設定も一部残す（update_action_statesで再設定される）
        
        # [MS13-B5] メニューイベントのバインディング
        # UI側イベントを検知し、_open_text_file等へルーティングする
        self.Bind(wx.EVT_MENU, self._on_mi_workspace_reset, self.mi_workspace_reset)
        self.Bind(wx.EVT_MENU, lambda e: self._open_text_file(), self.mi_text_open)
        self.Bind(wx.EVT_MENU, self._on_btn_open_wav, self.mi_wav_open)
        self.Bind(wx.EVT_MENU, self._on_mi_vmd_save, self.mi_vmd_save)
        self.Bind(
            wx.EVT_MENU,
            self._on_mi_diagnostic_report_save,
            self.mi_diagnostic_report_save,
        )
        self.Bind(
            wx.EVT_MENU,
            self._on_mi_mmd_delivery_export,
            self.mi_mmd_delivery_export,
        )
        self.Bind(
            wx.EVT_MENU,
            self._on_adjustment_undo,
            self.mi_adjustment_undo,
        )
        self.Bind(
            wx.EVT_MENU,
            self._on_adjustment_redo,
            self.mi_adjustment_redo,
        )
        self.Bind(
            wx.EVT_MENU,
            self._on_adjustment_reset_selected,
            self.mi_adjustment_reset_selected,
        )
        self.Bind(
            wx.EVT_MENU,
            self._on_adjustment_reset_all,
            self.mi_adjustment_reset_all,
        )
        self.Bind(wx.EVT_MENU, self._on_mi_settings, self.mi_settings)
        self.Bind(wx.EVT_MENU, self._on_toggle_debug_mode, self.mi_debug_mode)
        
        self.Bind(wx.EVT_MENU, lambda e: self._on_change_theme(ThemeMode.SYSTEM), self.mi_theme_system)
        self.Bind(wx.EVT_MENU, lambda e: self._on_change_theme(ThemeMode.LIGHT), self.mi_theme_light)
        self.Bind(wx.EVT_MENU, lambda e: self._on_change_theme(ThemeMode.DARK), self.mi_theme_dark)
        
        self.Bind(wx.EVT_MENU, self._on_mi_help, self.mi_help)
        self.Bind(wx.EVT_MENU, self._on_mi_about, self.mi_about)
        self.Bind(wx.EVT_MENU, self._on_menu_exit, self.mi_exit)
        self.mi_help.Enable(True)
        self.mi_about.Enable(True)

    def _on_toggle_debug_mode(self, event: wx.CommandEvent):
        enabled = bool(event.IsChecked())
        self.ui_state.debug_mode_enabled = enabled
        self.mi_debug_mode.Check(enabled)
        if self.controller:
            state = self.controller.set_debug_operation_recording(
                enabled,
                state_snapshot=(self._debug_operation_state_snapshot() if enabled else None),
            )
            recorder = self.controller.operation_recorder
            self.update_debug_operation_log_state(
                state,
                recorder.last_error_code,
                recorder.path,
            )
        else:
            state = "unavailable" if enabled else "paused"
            self.update_debug_operation_log_state(
                state,
                "controller_unavailable" if enabled else None,
                None,
            )
        self.update_status(
            "デバッグ操作ログを記録中" if enabled else "デバッグ操作ログを一時停止しました"
        )

    def _debug_operation_state_snapshot(self) -> dict[str, Any]:
        state = self.ui_state
        generation_settings = state.generation_state.generation_settings
        final_output_state = state.final_output_state
        accepted_origin = final_output_state.accepted_origin
        selected_model = getattr(state.whisper_model_selection, "selected_model_key", None)
        selected_path = state.selected_text_path
        if state.selected_audio_input is not None:
            selected_path = getattr(state.selected_audio_input, "source_path", selected_path)
        profile_state = state.model_profile_state
        return {
            "input_mode": state.input_mode,
            "has_text_input": bool(state.selected_text_path and state.selected_text_content),
            "has_audio_input": bool(state.selected_audio_input or state.selected_wav_path),
            "file_basename": Path(selected_path).name if selected_path else None,
            "analysis_result_valid": bool(state.analysis_result_valid),
            "analysis_pending_rebuild": bool(state.analysis_pending_rebuild),
            "busy": bool(state.is_busy),
            "is_playing": bool(state.is_playing),
            "morph_upper_limit": state.resolved_morph_upper_limit,
            "closing_hold_frames": generation_settings.closing_hold_frames,
            "closing_softness_frames": generation_settings.closing_softness_frames,
            "long_vowel_mode": generation_settings.long_vowel_mode,
            "selected_event_index": state.selected_source_event_index,
            "preset_id": self._selected_preset_id,
            "profile_id": getattr(profile_state, "active_model_profile_id", None),
            "model_key": selected_model,
            "theme_mode": state.theme_mode,
            "analysis_run_id": getattr(accepted_origin, "source_run_id", None),
            "analysis_result_id": getattr(accepted_origin, "analysis_result_id", None),
        }

    def _begin_debug_operation(
        self,
        action: str,
        *,
        payload: dict[str, Any] | None = None,
        entry: str | None = None,
        source: str = "user",
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
        capture_current_origin: bool = True,
    ):
        if not self.controller:
            return None
        return self.controller.begin_debug_operation(
            action,
            payload=payload,
            source=source,
            entry=entry,
            analysis_run_id=analysis_run_id,
            analysis_result_id=analysis_result_id,
            capture_current_origin=capture_current_origin,
        )

    def _mark_debug_operation_started(
        self,
        handle,
        *,
        job_kind: str,
        job_id: int,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ):
        if not self.controller:
            return handle
        return self.controller.mark_debug_operation_started(
            handle,
            job_kind=job_kind,
            job_id=job_id,
            analysis_run_id=analysis_run_id,
            analysis_result_id=analysis_result_id,
            payload=payload,
        )

    def _finish_debug_operation(
        self,
        handle,
        status: str,
        *,
        reason_code: str | None = None,
        payload: dict[str, Any] | None = None,
        accepted_origin: object | None = None,
    ) -> bool:
        if not self.controller:
            return False
        return self.controller.finish_debug_operation(
            handle,
            status,
            reason_code=reason_code,
            payload=payload,
            accepted_origin=accepted_origin,
        )

    def update_debug_operation_log_state(
        self,
        state: str,
        error_code: str | None,
        path: Path | None,
    ) -> None:
        self._debug_operation_log_state = state
        self._debug_operation_log_error = error_code
        self._debug_operation_log_path = path
        suffix = f"保存先: debug/operations/{path.name}" if path else "保存先: 未確定"
        help_text = (
            "解析traceと操作順・変更・完了結果をdebugフォルダへ記録します（セッション限定）。"
            f" 状態: {state}。{suffix}"
        )
        if error_code:
            help_text += f"。理由: {error_code}"
        try:
            self.mi_debug_mode.SetHelp(help_text)
        except (AttributeError, RuntimeError):
            pass
        if state in {"unavailable", "degraded"}:
            self.update_status(
                f"デバッグ操作ログは不完全です ({error_code or state})"
            )

    def _debug_trace_for_current_projection(self) -> AnalysisDebugTrace | None:
        if not self.ui_state.debug_mode_enabled:
            return None
        trace = self._accepted_debug_trace
        if trace is None or self._analysis_info_in_progress:
            return None
        if not self.ui_state.analysis_result_valid or self.ui_state.analysis_pending_rebuild:
            return None
        accepted_origin = self.ui_state.final_output_state.accepted_origin
        if (
            accepted_origin is None
            or getattr(accepted_origin, "source_run_id", None)
            != trace.analysis_run_id
            or getattr(accepted_origin, "analysis_result_id", None)
            != trace.analysis_result_id
        ):
            return None
        return trace

    def _debug_current_analysis_state_payload(self) -> dict[str, Any]:
        state = self.ui_state
        plan = state.current_timing_plan
        return {
            "analysis_result_valid": bool(state.analysis_result_valid),
            "analysis_pending_rebuild": bool(state.analysis_pending_rebuild),
            "current_timing_plan_present": plan is not None,
            "current_timing_plan_type": (
                type(plan).__name__ if plan is not None else None
            ),
            "analysis_info_in_progress": bool(self._analysis_info_in_progress),
            "is_busy": bool(state.is_busy),
            "vmd_save_ready": bool(state.vmd_save_ready),
        }

    def _debug_contract_summary(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        plan = getattr(self.ui_state, "current_timing_plan", None)
        base_input = diagnostic.get("base_input") or {}
        timeline = getattr(plan, "timeline", None) if plan is not None else None
        timeline_count = base_input.get("timeline_count")
        if not isinstance(timeline_count, int) or isinstance(timeline_count, bool):
            timeline_count = len(timeline) if timeline is not None else None
        if isinstance(timeline_count, int) and timeline_count >= 0:
            event_index_range: list[int] | str = [0, timeline_count]
        else:
            event_index_range = "not_available"

        observations = getattr(plan, "observations", None) if plan is not None else None
        if observations is None:
            observation_count: int | str = (
                "not_available" if plan is not None else "not_evaluated"
            )
        else:
            try:
                observation_count = len(observations)
            except TypeError:
                observation_count = "not_available"

        if timeline is None:
            long_vowel_metadata = "not_evaluated"
        else:
            long_vowel_metadata = (
                "present"
                if any(
                    bool(getattr(point, "is_long_vowel_continuation", False))
                    or getattr(point, "long_vowel_source_token_index", None) is not None
                    for point in timeline
                )
                else "absent"
            )
        return {
            "timeline_count": (
                timeline_count
                if isinstance(timeline_count, int) and timeline_count >= 0
                else "not_available"
            ),
            "observation_count": observation_count,
            "long_vowel_metadata": long_vowel_metadata,
            "event_index_range": event_index_range,
            "finite_value_check": "not_evaluated",
        }

    def _debug_sync_inputs_payload(self, diagnostic: dict[str, Any]) -> dict[str, Any]:
        raw = diagnostic.get("sync_inputs")
        raw = raw if isinstance(raw, dict) else {}
        snapshot = getattr(self.ui_state, "current_adjustment_snapshot", None)
        adjustments = getattr(snapshot, "adjustments", ()) or ()
        try:
            adjustment_count = len(adjustments)
        except TypeError:
            adjustment_count = 0
        return {
            "effective_plan_hint": _debug_allowlisted(
                raw.get("effective_plan_hint"),
                frozenset({"absent", "present", "not_evaluated"}),
                "not_evaluated",
            ),
            "cache_state": _debug_allowlisted(
                raw.get("cache_state"),
                frozenset({"hit", "miss", "not_evaluated"}),
                "not_evaluated",
            ),
            "adjustment_snapshot": _debug_allowlisted(
                raw.get("adjustment_snapshot"),
                frozenset({"absent", "present", "not_evaluated"}),
                "present" if snapshot is not None else "absent",
            ),
            "adjustment_count": adjustment_count,
            "output_edit_state": _debug_allowlisted(
                raw.get("output_edit_state"),
                frozenset({"absent", "present", "not_evaluated"}),
                "present"
                if getattr(self.ui_state, "current_output_edit_state", None) is not None
                else "absent",
            ),
            "base_identity_check": _debug_allowlisted(
                raw.get("base_identity_check"),
                frozenset({"valid", "invalid", "not_evaluated"}),
                "not_evaluated",
            ),
            "shape_parameters_check": _debug_allowlisted(
                raw.get("shape_parameters_check"),
                frozenset({"valid", "invalid", "not_evaluated"}),
                "not_evaluated",
            ),
        }

    def _debug_downstream_payload(
        self,
        *,
        sync_context: UiSyncContext | None,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
        effective_writer_input_state: str,
    ) -> dict[str, str]:
        if sync_context is None or diagnostics_snapshot is None:
            return {
                "diagnostics_snapshot": (
                    "completed" if diagnostics_snapshot is not None else "not_attempted"
                ),
                "effective_shape": "not_attempted",
                "preview_projection": "not_attempted",
                "writer_projection": "not_attempted",
                "vmd_save": "not_attempted",
            }

        plan_skip_reason = self._debug_plan_skip_reason(sync_context)
        if plan_skip_reason is not None:
            return {
                "diagnostics_snapshot": "completed",
                "effective_shape": "skipped",
                "preview_projection": "skipped",
                "writer_projection": "skipped",
                "vmd_save": (
                    "completed"
                    if bool(getattr(self.ui_state, "vmd_save_ready", False))
                    else "skipped"
                ),
            }

        preview_model = getattr(
            getattr(getattr(self, "placeholder_container", None), "pnl_preview", None),
            "model",
            None,
        )
        preview_status = (
            "completed" if bool(getattr(preview_model, "is_valid", False)) else "skipped"
        )
        writer_status = {
            "ready": "completed",
            "invalid": "skipped",
            "not_applicable": "not_attempted",
        }.get(str(effective_writer_input_state), "not_evaluated")
        return {
            "diagnostics_snapshot": "completed",
            "effective_shape": "completed",
            "preview_projection": preview_status,
            "writer_projection": writer_status,
            "vmd_save": "completed"
            if bool(getattr(self.ui_state, "vmd_save_ready", False))
            else "skipped",
        }

    def _debug_plan_skip_reason(self, sync_context: UiSyncContext | None) -> str | None:
        if bool(getattr(self.ui_state, "analysis_pending_rebuild", False)):
            return "analysis_rebuild_pending"
        if (
            sync_context is not None
            and hasattr(sync_context, "effective_plan")
            and sync_context.effective_plan is None
        ):
            return "effective_plan_not_applicable"
        return None

    @staticmethod
    def _debug_execution_operation(
        state: str,
        outcome: str,
        reason_code: str,
        *,
        plan_origin: str = "not_applicable",
    ) -> dict[str, str]:
        return {
            "state": _debug_allowlisted(state, _DEBUG_EXECUTION_STATES, "not_evaluable"),
            "outcome": _debug_allowlisted(
                outcome, _DEBUG_EXECUTION_OUTCOMES, "not_evaluable"
            ),
            "reason_code": _debug_allowlisted(
                reason_code, _DEBUG_EXECUTION_REASONS, "not_evaluable"
            ),
            "plan_origin": _debug_allowlisted(
                plan_origin,
                frozenset({"resolved", "cache", "hint", "not_applicable", "unknown"}),
                "unknown",
            ),
        }

    def _debug_execution_diagnostics(
        self,
        *,
        sync_context: UiSyncContext | None,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
        effective_writer_input_state: str,
        snapshot_point: str,
        preview_result: str | None = None,
        writer_result: str | None = None,
        save_result: str | None = None,
    ) -> dict[str, Any]:
        resolver = self._current_ui_sync_diagnostic.get("resolver_diagnostics")
        attempts = resolver.get("attempts", []) if isinstance(resolver, dict) else []
        last_attempt = attempts[-1] if isinstance(attempts, list) and attempts else {}
        plan_skip_reason = self._debug_plan_skip_reason(sync_context)
        if sync_context is not None:
            plan_origin = last_attempt.get("plan_origin", "resolved")
            effective = self._debug_execution_operation(
                "completed", "success", "resolver_succeeded", plan_origin=plan_origin
            )
        elif isinstance(last_attempt, dict) and last_attempt.get("status") == "failed":
            effective = self._debug_execution_operation(
                "attempted", "failed", "resolver_failed", plan_origin="resolved"
            )
        elif isinstance(last_attempt, dict) and last_attempt.get("plan_origin") == "cache":
            effective = self._debug_execution_operation(
                "skipped", "success", "resolver_skipped_cache", plan_origin="cache"
            )
        elif isinstance(last_attempt, dict) and last_attempt.get("plan_origin") == "hint":
            effective = self._debug_execution_operation(
                "skipped", "success", "resolver_skipped_hint", plan_origin="hint"
            )
        else:
            effective = self._debug_execution_operation(
                "not_attempted", "not_evaluable", "not_attempted"
            )
        if plan_skip_reason is not None:
            effective = self._debug_execution_operation(
                "skipped",
                "not_applicable",
                plan_skip_reason,
            )

        diagnostics_operation = (
            self._debug_execution_operation(
                "completed", "success", "diagnostics_snapshot_ready"
            )
            if diagnostics_snapshot is not None
            else self._debug_execution_operation(
                "not_attempted", "not_evaluable", "diagnostics_snapshot_unavailable"
            )
        )
        if plan_skip_reason is not None and preview_result is None:
            preview_operation = self._debug_execution_operation(
                "skipped",
                "not_applicable",
                plan_skip_reason,
            )
        elif preview_result is not None:
            preview_operation = self._debug_execution_operation(
                "attempted",
                "success" if preview_result == "succeeded" else "failed",
                "preview_attempted"
                if preview_result == "succeeded"
                else "preview_model_unavailable",
            )
        else:
            preview_operation = self._debug_execution_operation(
                "not_attempted", "not_evaluable", "not_attempted"
            )

        if plan_skip_reason is not None and writer_result is None:
            writer_operation = self._debug_execution_operation(
                "skipped",
                "not_applicable",
                plan_skip_reason,
            )
        elif writer_result is not None:
            writer_operation = self._debug_execution_operation(
                "attempted",
                "success" if writer_result == "succeeded" else "failed",
                "writer_attempted"
                if writer_result == "succeeded"
                else "writer_adapter_failed",
            )
        else:
            writer_operation = self._debug_execution_operation(
                "not_attempted", "not_evaluable", "not_attempted"
            )
        save_operation = (
            self._debug_execution_operation(
                "attempted",
                "success" if save_result == "succeeded" else "failed",
                "save_action_not_observed"
                if save_result != "cancelled"
                else "operation_cancelled",
            )
            if save_result is not None
            else self._debug_execution_operation(
                "not_attempted", "not_evaluable", "not_attempted"
            )
        )
        normalized_snapshot_point = (
            snapshot_point
            if snapshot_point in {"projection_input", "projection_complete"}
            else "projection_input"
        )
        return {
            "schema_version": 1,
            "snapshot_point": normalized_snapshot_point,
            "diagnostic_snapshot_scope": (
                "pre_stage"
                if normalized_snapshot_point == "projection_input"
                else "post_stage"
            ),
            "authoritative_for_stage": normalized_snapshot_point == "projection_complete",
            "operations": {
                "diagnostics_snapshot": diagnostics_operation,
                "effective_shape": effective,
                "preview_projection": preview_operation,
                "writer_projection": writer_operation,
                "vmd_save": save_operation,
            },
            "effective_writer_input_state": _debug_allowlisted(
                effective_writer_input_state,
                frozenset({"ready", "not_applicable", "invalid"}),
                "invalid",
            ),
        }

    def _debug_projection_input_payload(
        self,
        *,
        projection_revision: int,
        sync_context: UiSyncContext | None,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
        effective_writer_input_state: str,
        effective_writer_input_failure_reason: str | None,
    ) -> dict[str, Any]:
        diagnostic = self._current_ui_sync_diagnostic
        ready = sync_context is not None and diagnostics_snapshot is not None
        analysis_state = dict(
            diagnostic.get("analysis_state")
            or self._debug_current_analysis_state_payload()
        )
        base_input = dict(diagnostic.get("base_input") or {})
        if not base_input:
            base_input = {
                "status": "available" if sync_context is not None else "unavailable",
                "failure_code": (
                    "not_applicable" if sync_context is not None else "base_input_unavailable"
                ),
                "timeline_count": "not_available",
                "observations_present": "not_evaluated",
                "duration_candidates": [],
                "duration_status": "not_evaluated",
                "duration_sec": "not_available",
            }
        base_status = _debug_allowlisted(
            base_input.get("status"),
            frozenset({"available", "unavailable", "not_evaluated"}),
            "not_evaluated",
        )
        base_failure_code = _debug_safe_failure_code(base_input.get("failure_code"))
        if base_status == "available":
            base_failure_code = "not_applicable"
        elif base_failure_code == "not_applicable":
            base_failure_code = "base_input_unavailable"
        base_input["status"] = base_status
        base_input["failure_code"] = base_failure_code
        if not isinstance(base_input.get("timeline_count"), int):
            base_input["timeline_count"] = "not_available"
        if not isinstance(base_input.get("observations_present"), bool):
            base_input["observations_present"] = "not_evaluated"
        if not isinstance(base_input.get("duration_candidates"), list):
            base_input["duration_candidates"] = []
        base_input["duration_status"] = _debug_allowlisted(
            base_input.get("duration_status"),
            frozenset({"selected", "unavailable", "not_recorded", "not_evaluated"}),
            "not_evaluated",
        )
        if not isinstance(base_input.get("duration_sec"), (int, float)):
            base_input["duration_sec"] = "not_available"
        sync_detail = dict(diagnostic.get("sync_context") or {})
        if sync_context is not None:
            sync_detail = {
                "status": "available",
                "failure_code": "not_applicable",
                "exception_type": "not_applicable",
            }
        elif not sync_detail:
            sync_detail = {
                "status": "unavailable",
                "failure_code": (
                    "base_input_unavailable"
                    if self._current_ui_sync_failure_reason
                    == "base_input_unavailable"
                    else "sync_context_build_failed"
                ),
                "exception_type": "unknown",
            }
        sync_status = _debug_allowlisted(
            sync_detail.get("status"),
            frozenset({"available", "unavailable", "not_evaluated"}),
            "not_evaluated",
        )
        sync_failure_code = _debug_safe_failure_code(sync_detail.get("failure_code"))
        if sync_status == "available":
            sync_failure_code = "not_applicable"
        elif sync_failure_code == "not_applicable":
            sync_failure_code = "sync_context_build_failed"
        sync_detail = {
            "status": sync_status,
            "failure_code": sync_failure_code,
            "exception_type": _debug_allowlisted(
                sync_detail.get("exception_type"),
                _DEBUG_EXCEPTION_TYPES,
                "unknown" if sync_status != "available" else "not_applicable",
            ),
        }

        if sync_context is None:
            if base_input.get("status") == "unavailable":
                reason_code = "base_input_unavailable"
            else:
                reason_code = "sync_context_build_failed"
            status = "unavailable"
        elif diagnostics_snapshot is None:
            reason_code = "diagnostics_snapshot_unavailable"
            status = "unavailable"
        else:
            reason_code = "projection_input_ready"
            status = "ready"

        failure_context = diagnostic.get("failure_context")
        if (
            isinstance(failure_context, dict)
            and failure_context.get("code") == "none"
            and not ready
        ):
            failure_context = None
        if not isinstance(failure_context, dict):
            if base_input.get("status") == "unavailable":
                failure_context = {
                    "phase": "base_input_build",
                    "domain": "base_input",
                    "code": base_input.get("failure_code"),
                    "exception_type": "not_applicable",
                    "field_code": "not_applicable",
                    "event_index": "not_applicable",
                    "source_event_index": "not_applicable",
                    "index_status": "not_applicable",
                    "observed_stage": "ui_sync_context",
                }
            elif not ready:
                failure_context = {
                    "phase": "diagnostics_snapshot_build"
                    if sync_context is not None
                    else "sync_context_build",
                    "domain": "diagnostics_snapshot"
                    if sync_context is not None
                    else "unknown",
                    "code": "diagnostics_snapshot_unavailable"
                    if sync_context is not None
                    else "unknown_contract_failure",
                    "exception_type": "not_applicable",
                    "field_code": "not_applicable",
                    "event_index": "not_applicable",
                    "source_event_index": "not_applicable",
                    "index_status": "not_applicable",
                    "observed_stage": "ui_sync_context",
                }
        resolver_diagnostics = diagnostic.get("resolver_diagnostics")
        if not isinstance(resolver_diagnostics, dict):
            resolver_diagnostics = {
                "diagnostic_revision": "ms28-b3c-resolver-v1",
                "capture_state": "not_available",
                "attempts": [],
                "truncation": {"limited": False},
            }
        return {
            "contract_version": _DEBUG_PROJECTION_INPUT_CONTRACT_VERSION,
            "status": status,
            "projection_revision": projection_revision,
            "analysis_state": analysis_state,
            "base_input": base_input,
            "sync_context": sync_detail,
            "diagnostics_snapshot": {
                "present": diagnostics_snapshot is not None,
            },
            "effective_writer_input": {
                "state": _debug_allowlisted(
                    effective_writer_input_state,
                    frozenset({"ready", "not_applicable", "invalid"}),
                    "invalid",
                ),
                "failure_code": _debug_safe_failure_code(
                    effective_writer_input_failure_reason
                ),
            },
            "failure_context": _debug_safe_failure_context(
                failure_context,
                ready=ready,
            ),
            "resolver_diagnostics": resolver_diagnostics,
            "execution_diagnostics": self._debug_execution_diagnostics(
                sync_context=sync_context,
                diagnostics_snapshot=diagnostics_snapshot,
                effective_writer_input_state=effective_writer_input_state,
                snapshot_point="projection_input",
            ),
            "sync_inputs": self._debug_sync_inputs_payload(diagnostic),
            "contract_summary": self._debug_contract_summary(diagnostic),
            "downstream": self._debug_downstream_payload(
                sync_context=sync_context,
                diagnostics_snapshot=diagnostics_snapshot,
                effective_writer_input_state=effective_writer_input_state,
            ),
            "reason_code": reason_code,
        }

    def _finish_debug_trace(
        self,
        trace: AnalysisDebugTrace | None,
        *,
        status: str,
        reason_code: str | None = None,
    ) -> None:
        if trace is None:
            return
        trace.record_terminal(status, reason_code=reason_code)
        self._debug_store.submit(trace)

    def record_debug_action(
        self,
        action: str,
        *,
        payload: dict | None = None,
        status: str = "completed",
    ) -> None:
        self._record_operation_from_trace_action(action, payload, status)
        trace = self._debug_trace_for_current_projection()
        if trace is None:
            return
        save_operation_id = None
        if action == "vmd_save_request":
            save_operation_id = uuid.uuid4().hex
            self._debug_save_operation_id = save_operation_id
        elif action.startswith("vmd_save_"):
            save_operation_id = self._debug_save_operation_id
        action_payload = dict(payload or {})
        if action.startswith("vmd_save_"):
            save_result = {
                "vmd_save_request": "pending",
                "vmd_save_completed": "succeeded",
                "vmd_save_failed": "failed",
                "vmd_save_cancelled": "cancelled",
            }.get(action)
            execution = self._debug_execution_diagnostics(
                sync_context=getattr(self, "_current_ui_sync_context", None),
                diagnostics_snapshot=getattr(
                    getattr(self, "ui_state", None),
                    "current_output_diagnostics_snapshot",
                    None,
                ),
                effective_writer_input_state="not_applicable",
                snapshot_point="projection_complete",
                save_result=save_result,
            )
            vmd_operation = execution["operations"]["vmd_save"]
            if save_result == "pending":
                vmd_operation.update(
                    state="attempted",
                    outcome="pending",
                    reason_code="save_request_pending",
                )
            elif save_result == "succeeded":
                vmd_operation.update(
                    state="completed",
                    outcome="success",
                    reason_code="save_action_succeeded",
                )
            elif save_result == "failed":
                vmd_operation.update(
                    state="attempted",
                    outcome="failed",
                    reason_code="save_action_failed",
                )
            elif save_result == "cancelled":
                vmd_operation.update(
                    state="attempted",
                    outcome="cancelled",
                    reason_code="operation_cancelled",
                )
            action_payload["execution_diagnostics"] = execution
        trace.record_action(
            action,
            payload=action_payload,
            status=status,
            save_operation_id=save_operation_id,
        )

    def _record_operation_from_trace_action(
        self,
        action: str,
        payload: dict | None,
        status: str,
    ) -> None:
        group = (
            str((payload or {}).get("operation_kind"))
            if action.startswith("generation_settings_")
            and (payload or {}).get("operation_kind") in {
                "generation_settings",
                "preset_apply",
            }
            else "generation_settings"
            if action.startswith("generation_settings_")
            else "vmd_save"
            if action.startswith("vmd_save_")
            else None
        )
        if group is None or self.controller is None:
            return
        safe_payload = dict(payload or {})
        reason = safe_payload.pop("reason", None) or safe_payload.pop(
            "error_code", None
        )
        raw_path = safe_payload.pop("path", None)
        if isinstance(raw_path, str):
            safe_payload["file_basename"] = Path(raw_path).name
        operation_status = {
            "requested": "requested",
            "started": "started",
            "accepted": "completed",
            "succeeded": "completed",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
            "rejected": "rejected",
            "blocked": "rejected",
            "noop": "noop",
        }.get(status, "completed")
        if action in {"generation_settings_request", "vmd_save_request"}:
            operation_handle = self._begin_debug_operation(
                group,
                payload=safe_payload,
                entry="controller",
            )
            if operation_handle is not None:
                self._debug_operation_handles[group] = operation_handle
            if status == "started":
                self.controller.record_debug_operation_phase(
                    operation_handle,
                    action,
                    "started",
                    payload=safe_payload,
                )
            return
        operation_handle = self._debug_operation_handles.get(group)
        if action == "vmd_save_writing":
            operation_handle = self.controller.mark_debug_operation_started(
                operation_handle,
                job_kind=(
                    safe_payload.get("worker_kind")
                    if isinstance(safe_payload.get("worker_kind"), str)
                    else "verified_vmd_save"
                ),
                job_id=(
                    safe_payload.get("job_id")
                    if type(safe_payload.get("job_id")) is int
                    else None
                ),
                payload={
                    key: value
                    for key, value in safe_payload.items()
                    if key != "job_id"
                },
            )
            if operation_handle is not None:
                self._debug_operation_handles[group] = operation_handle
            return
        if action in {
            "generation_settings_accepted",
            "generation_settings_rejected",
            "generation_settings_noop",
            "vmd_save_completed",
            "vmd_save_failed",
            "vmd_save_cancelled",
            "vmd_save_blocked",
        }:
            self._debug_operation_handles.pop(group, None)
            self._finish_debug_operation(
                operation_handle,
                operation_status,
                reason_code=(
                    reason
                    if isinstance(reason, str)
                    else action.removesuffix("_accepted").removesuffix("_completed")
                ),
                payload=safe_payload,
            )
            return
        if operation_handle is not None:
            self.controller.record_debug_operation_phase(
                operation_handle,
                action,
                operation_status,
                payload=safe_payload,
                reason_code=reason if isinstance(reason, str) else None,
            )
        else:
            self.controller.record_debug_operation_event(
                action,
                operation_status,
                payload=safe_payload,
                source="system",
                reason_code=reason if isinstance(reason, str) else None,
            )

    def _shutdown_debug_store(self) -> None:
        self._debug_store.flush(timeout=5.0)
        self._debug_store.shutdown(timeout=1.0)

    @staticmethod
    def _debug_shape_plan_payload(effective_plan) -> dict:
        return {
            "base_plan_identity_digest": getattr(
                getattr(effective_plan, "base_plan_identity", None),
                "digest",
                None,
            ),
            "base_event_count": len(getattr(effective_plan, "base_events", ()) or ()),
            "effective_event_count": len(getattr(effective_plan, "effective_events", ()) or ()),
            "shape_count": len(getattr(effective_plan, "shapes", ()) or ()),
            "shapes": [
                {
                    "vowel": getattr(shape, "vowel", None),
                    "shape_kind": getattr(shape, "shape_kind", None),
                    "real_base_event_indices": getattr(shape, "real_base_event_indices", ()),
                    "event_ranges": getattr(shape, "event_ranges", ()),
                    "internal_shape_source_tokens": getattr(
                        shape, "internal_shape_source_tokens", ()
                    ),
                    "fallback_reason": getattr(shape, "fallback_reason", None),
                    "silence_core_frame_ranges": [
                        list(item)
                        for item in getattr(shape, "silence_core_frame_ranges", ()) or ()
                    ],
                    "resolved_tail": (
                        {
                            "requested_hold_frames": getattr(
                                getattr(shape, "resolved_tail", None),
                                "requested_hold_frames",
                                None,
                            ),
                            "requested_softness_frames": getattr(
                                getattr(shape, "resolved_tail", None),
                                "requested_softness_frames",
                                None,
                            ),
                            "effective_hold_frames": getattr(
                                getattr(shape, "resolved_tail", None),
                                "effective_hold_frames",
                                None,
                            ),
                            "effective_softness_frames": getattr(
                                getattr(shape, "resolved_tail", None),
                                "effective_softness_frames",
                                None,
                            ),
                            "slope_ratio": getattr(
                                getattr(shape, "resolved_tail", None),
                                "slope_ratio",
                                None,
                            ),
                            "has_slope_midpoint": getattr(
                                getattr(shape, "resolved_tail", None),
                                "has_slope_midpoint",
                                None,
                            ),
                        }
                        if getattr(shape, "resolved_tail", None) is not None
                        else None
                    ),
                    "control_points": [
                        {
                            "frame_no": getattr(point, "frame_no", None),
                            "value": getattr(point, "value", None),
                            "point_kind": getattr(point, "point_kind", None),
                        }
                        for point in getattr(shape, "control_points", ()) or ()
                    ],
                }
                for shape in getattr(effective_plan, "shapes", ()) or ()
            ],
            "long_vowel_runs": [
                {
                    "source_base_event_index": getattr(run, "source_base_event_index", None),
                    "continuation_base_event_indices": getattr(
                        run, "continuation_base_event_indices", ()
                    ),
                    "terminal_base_event_index": getattr(run, "terminal_base_event_index", None),
                    "vowel": getattr(run, "vowel", None),
                    "resolved_mode": getattr(run, "resolved_mode", None),
                    "source_peak_frame": getattr(run, "source_peak_frame", None),
                    "terminal_end_frame": getattr(run, "terminal_end_frame", None),
                }
                for run in getattr(effective_plan, "long_vowel_runs", ()) or ()
            ],
            "observation_handoffs": [
                {
                    "span_start_index": getattr(handoff, "span_start_index", None),
                    "span_end_index": getattr(handoff, "span_end_index", None),
                    "previous_non_zero_event_index": getattr(
                        handoff, "previous_non_zero_event_index", None
                    ),
                    "next_non_zero_event_index": getattr(
                        handoff, "next_non_zero_event_index", None
                    ),
                    "candidate_kind": getattr(handoff, "candidate_kind", None),
                    "enabled": getattr(handoff, "enabled", None),
                    "full_span_start_frame": getattr(handoff, "full_span_start_frame", None),
                    "full_span_end_frame": getattr(handoff, "full_span_end_frame", None),
                    "silence_core_frame_ranges": getattr(
                        handoff, "silence_core_frame_ranges", ()
                    ),
                    "boundary_fringe_frame_ranges": getattr(
                        handoff, "boundary_fringe_frame_ranges", ()
                    ),
                    "silence_core_overlap": getattr(handoff, "silence_core_overlap", False),
                    "coverage_status": getattr(handoff, "coverage_status", "unobserved"),
                    "provenance_status": getattr(handoff, "provenance_status", "unavailable"),
                    "rejection_reason_code": getattr(handoff, "rejection_reason_code", None),
                }
                for handoff in getattr(effective_plan, "observation_handoffs", ()) or ()
            ],
            "event_silence_admissions": [
                {
                    "event_index": getattr(admission, "event_index", None),
                    "vowel": getattr(admission, "vowel", None),
                    "origin_shape_id": getattr(admission, "origin_shape_id", None),
                    "positive_point_kinds": list(
                        getattr(admission, "positive_point_kinds", ()) or ()
                    ),
                    "source_event_indices": list(
                        getattr(admission, "source_event_indices", ()) or ()
                    ),
                    "effective_frame_range": (
                        list(getattr(admission, "effective_frame_range", ()))
                        if getattr(admission, "effective_frame_range", None) is not None
                        else None
                    ),
                    "boundary_only": getattr(admission, "boundary_only", False),
                    "boundary_frame": getattr(admission, "boundary_frame", None),
                    "boundary_point_kind": getattr(
                        admission, "boundary_point_kind", None
                    ),
                    "boundary_relation": getattr(
                        admission, "boundary_relation", "not_applicable"
                    ),
                    "boundary_action": getattr(
                        admission, "boundary_action", "not_applicable"
                    ),
                    "admission_key": _debug_boundary_admission_key(admission),
                    "boundary_admission_checks": _debug_boundary_admission_checks(
                        admission,
                        effective_plan,
                    ),
                    "base_event_silence_core_overlap": getattr(
                        admission,
                        "base_event_silence_core_overlap",
                        False,
                    ),
                    "positive_core_frame_ranges": [
                        list(item)
                        for item in getattr(admission, "positive_core_frame_ranges", ()) or ()
                    ],
                    "long_vowel_role": getattr(admission, "long_vowel_role", None),
                    "manual_adjustment_applied": getattr(
                        admission,
                        "manual_adjustment_applied",
                        False,
                    ),
                    "enabled": getattr(admission, "enabled", None),
                    "rejection_reason_code": getattr(
                        admission,
                        "rejection_reason_code",
                        None,
                    ),
                    "required_zero_frame_ranges": [
                        list(item)
                        for item in getattr(admission, "required_zero_frame_ranges", ()) or ()
                    ],
                }
                for admission in getattr(effective_plan, "event_silence_admissions", ()) or ()
            ],
            "normalization_contract": {
                "allowed_non_zero_ranges": getattr(
                    getattr(effective_plan, "normalization_contract", None),
                    "allowed_non_zero_ranges",
                    (),
                ),
                "required_zero_frames": getattr(
                    getattr(effective_plan, "normalization_contract", None),
                    "required_zero_frames",
                    (),
                ),
                "protected_event_ranges": getattr(
                    getattr(effective_plan, "normalization_contract", None),
                    "protected_event_ranges",
                    (),
                ),
            },
            "silence_policy": getattr(
                effective_plan,
                "silence_policy",
                "acoustic_core_precedence",
            ),
            "silence_core_frame_ranges": [
                list(item)
                for item in getattr(effective_plan, "silence_core_frame_ranges", ()) or ()
            ],
            "silence_clip_records": list(
                getattr(effective_plan, "silence_clip_records", ()) or ()
            ),
            "shape_parameters": {
                "closing_hold_frames": getattr(
                    getattr(effective_plan, "shape_parameters", None),
                    "closing_hold_frames",
                    None,
                ),
                "closing_softness_frames": getattr(
                    getattr(effective_plan, "shape_parameters", None),
                    "closing_softness_frames",
                    None,
                ),
                "long_vowel_mode": getattr(
                    getattr(effective_plan, "shape_parameters", None),
                    "long_vowel_mode",
                    None,
                ),
            },
        }

    def _record_debug_projection(
        self,
        *,
        sync_context: UiSyncContext | None,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
        effective_writer_input_state: str = "not_applicable",
        effective_writer_input_failure_reason: str | None = None,
    ) -> None:
        trace = self._debug_trace_for_current_projection()
        if trace is None:
            return
        try:
            self._record_debug_projection_impl(
                sync_context=sync_context,
                diagnostics_snapshot=diagnostics_snapshot,
                effective_writer_input_state=effective_writer_input_state,
                effective_writer_input_failure_reason=(
                    effective_writer_input_failure_reason
                ),
            )
        except Exception:
            trace.mark_capture_status("degraded")
            trace.record_stage(
                "projection_comparison",
                status="not_evaluable",
                reason_code="DEBUG_INTERNAL_ERROR",
                payload={"projection_failure": "generic"},
            )

    def _record_debug_projection_impl(
        self,
        *,
        sync_context: UiSyncContext | None,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
        effective_writer_input_state: str = "not_applicable",
        effective_writer_input_failure_reason: str | None = None,
    ) -> None:
        trace = self._debug_trace_for_current_projection()
        if trace is None:
            return
        revision = trace.start_projection_revision()
        projection_input = self._debug_projection_input_payload(
            projection_revision=revision,
            sync_context=sync_context,
            diagnostics_snapshot=diagnostics_snapshot,
            effective_writer_input_state=effective_writer_input_state,
            effective_writer_input_failure_reason=(
                effective_writer_input_failure_reason
            ),
        )
        projection_input_reason = projection_input["reason_code"]
        trace.record_stage(
            "projection_input",
            reason_code=projection_input_reason,
            payload=projection_input,
        )
        if sync_context is None or diagnostics_snapshot is None:
            terminal_execution = self._debug_execution_diagnostics(
                sync_context=sync_context,
                diagnostics_snapshot=diagnostics_snapshot,
                effective_writer_input_state=effective_writer_input_state,
                snapshot_point="projection_complete",
            )
            trace.record_stage(
                "effective_shape",
                status="skipped",
                reason_code="projection_input_unavailable",
                payload={
                    "projection_revision": revision,
                    "projection_input_reason": projection_input_reason,
                },
            )
            trace.record_stage(
                "projection_comparison",
                status="not_evaluable",
                reason_code="projection_input_unavailable",
                payload={
                    "projection_revision": revision,
                    "projection_input_reason": projection_input_reason,
                    "execution_diagnostics": terminal_execution,
                },
            )
            return

        effective_plan = sync_context.effective_plan
        plan_skip_reason = self._debug_plan_skip_reason(sync_context)
        if plan_skip_reason is not None:
            trace.record_stage(
                "effective_shape",
                status="skipped",
                reason_code=plan_skip_reason,
                payload={"projection_revision": revision},
            )
            trace.record_stage(
                "preview_projection",
                status="skipped",
                reason_code=plan_skip_reason,
                payload={"projection_revision": revision},
            )
            trace.record_stage(
                "writer_projection",
                status="skipped",
                reason_code=plan_skip_reason,
                payload={"projection_revision": revision},
            )
            terminal_execution = self._debug_execution_diagnostics(
                sync_context=sync_context,
                diagnostics_snapshot=diagnostics_snapshot,
                effective_writer_input_state=effective_writer_input_state,
                snapshot_point="projection_complete",
            )
            trace.record_stage(
                "silence_observations",
                status="not_evaluable",
                reason_code=plan_skip_reason,
                payload={"projection_revision": revision, "observations": []},
            )
            trace.record_stage(
                "projection_comparison",
                status="not_evaluable",
                reason_code=plan_skip_reason,
                payload={
                    "projection_revision": revision,
                    "execution_diagnostics": terminal_execution,
                },
            )
            return

        trace.record_stage(
            "effective_shape",
            payload={
                "projection_revision": revision,
                **self._debug_shape_plan_payload(effective_plan),
            },
        )
        provenance_rows = []
        for shape_ordinal, shape in enumerate(getattr(effective_plan, "shapes", ()) or ()):
            source_event_indices = getattr(shape, "real_base_event_indices", ()) or ()
            for point_ordinal, point in enumerate(getattr(shape, "control_points", ()) or ()):
                frame_no = getattr(point, "frame_no", None)
                value = getattr(point, "value", None)
                provenance_rows.append(
                    {
                        "origin_shape_id": shape_ordinal,
                        "source_event_indices": source_event_indices,
                        "raw_point_id": f"{shape_ordinal}:{point_ordinal}",
                        "point_kind": getattr(point, "point_kind", None),
                        "required_zero": bool(value == 0),
                        "raw_key": [frame_no, getattr(shape, "vowel", None)],
                        "normalized_key": [frame_no, getattr(shape, "vowel", None)],
                        "normalization_action": "none",
                        "origin_kind": "shape_control_point",
                    }
                )
        trace.record_stage(
            "provenance",
            payload={"projection_revision": revision, "rows": provenance_rows},
        )

        preview_model = self.placeholder_container.pnl_preview.model
        preview_data = getattr(preview_model, "data", None)
        effective_digest = getattr(
            getattr(effective_plan, "base_plan_identity", None),
            "digest",
            None,
        )
        preview_identity_matches = (
            isinstance(effective_digest, str)
            and getattr(preview_model, "base_plan_identity_digest", None) == effective_digest
        )
        preview_status = (
            "ready"
            if bool(getattr(preview_model, "is_valid", False)) and preview_identity_matches
            else "unavailable"
        )
        preview_result = "succeeded" if preview_status == "ready" else "failed"
        preview_points: list[dict] = []
        preview_lookup: dict[tuple[int, str], float] = {}
        preview_segments_by_vowel: dict[str, list[tuple[tuple[int, float], ...]]] = {}
        if preview_data is not None:
            for row in getattr(preview_data, "rows", ()) or ():
                vowel = getattr(row, "vowel", None)
                for segment in getattr(row, "segments", ()) or ():
                    segment_points: list[tuple[int, float]] = []
                    for point in getattr(segment, "control_points", ()) or ():
                        frame_no = getattr(point, "frame_no", None)
                        value = getattr(point, "value", None)
                        if frame_no is None:
                            continue
                        frame_key = int(frame_no)
                        segment_points.append((frame_key, float(value)))
                        preview_lookup[(frame_key, str(vowel))] = float(value)
                        preview_points.append(
                            {
                                "frame_no": frame_key,
                                "vowel": vowel,
                                "value": value,
                                "point_kind": getattr(point, "point_kind", None),
                            }
                        )
                    if segment_points:
                        preview_segments_by_vowel.setdefault(str(vowel), []).append(
                            tuple(segment_points)
                        )
        trace.record_stage(
            "preview_projection",
            status=preview_status,
            reason_code=None if preview_status == "ready" else "preview_model_unavailable",
            payload={
                "projection_revision": revision,
                "base_plan_identity_digest": getattr(
                    getattr(effective_plan, "base_plan_identity", None),
                    "digest",
                    None,
                ),
                "model_identity_matches": preview_identity_matches,
                "point_count": len(preview_points),
                "points": preview_points,
            },
        )

        output_morph_names = self._resolved_output_morph_names()
        writer_frames: list[dict] = []
        raw_writer_points: list[tuple[int, str, float]] = []
        writer_lookup: dict[tuple[int, str], float] = {}
        normalized_writer_points: list[tuple[int, str, float]] = []
        normalized_writer_frames: list[tuple[int, str, float]] = []
        writer_result = "failed"
        try:
            raw_writer_frames = build_morph_frames_from_effective_shape_plan(
                effective_plan,
                apply_final_normalization=False,
                output_morph_names=output_morph_names,
            )
            normalized_writer_frames = build_morph_frames_from_effective_shape_plan(
                effective_plan,
                apply_final_normalization=True,
                output_morph_names=output_morph_names,
            )
            for frame_no, morph_name, value in raw_writer_frames:
                try:
                    vowel = INTERNAL_VOWEL_ORDER[output_morph_names.index(morph_name)]
                except (ValueError, IndexError):
                    vowel = None
                writer_frames.append(
                    {
                        "frame_no": frame_no,
                        "morph_name": morph_name,
                        "vowel": vowel,
                        "value": value,
                    }
                )
                if vowel is not None:
                    raw_writer_points.append((int(frame_no), vowel, float(value)))
            for frame_no, morph_name, value in normalized_writer_frames:
                try:
                    vowel = INTERNAL_VOWEL_ORDER[output_morph_names.index(morph_name)]
                except (ValueError, IndexError):
                    vowel = None
                if vowel is not None:
                    writer_lookup[(int(frame_no), vowel)] = float(value)
                    normalized_writer_points.append((int(frame_no), vowel, float(value)))
            trace.record_stage(
                "writer_projection",
                payload={
                    "projection_revision": revision,
                    "status": "ready",
                    "point_count": len(normalized_writer_frames),
                    "frames_before_normalization": writer_frames,
                    "frames_after_normalization": [
                        {
                            "frame_no": frame_no,
                            "morph_name": morph_name,
                            "value": value,
                        }
                        for frame_no, morph_name, value in normalized_writer_frames
                    ],
                    "save_state_fingerprint": diagnostics_snapshot.save_state_fingerprint,
                },
            )
            writer_result = "succeeded"
        except (AttributeError, TypeError, ValueError) as error:
            trace.record_stage(
                "writer_projection",
                status="failed",
                reason_code="writer_adapter_failed",
                payload={"projection_revision": revision, "error_type": type(error).__name__},
            )

        trace_snapshot = trace.snapshot()
        rms_records = [
            record
            for record in trace_snapshot.get("records", [])
            if record.get("stage") == "rms_load"
        ]
        rms_payload = rms_records[-1].get("payload", {}) if rms_records else {}
        silence_intervals = rms_payload.get("silence_intervals", [])
        if not isinstance(silence_intervals, list):
            silence_intervals = []
        debug_silence_intervals = [dict(interval) for interval in silence_intervals]
        observation_contracts = getattr(
            getattr(sync_context, "base_input", None),
            "observations",
            None,
        )
        debug_provenance_status = (
            "complete"
            if effective_plan is not None
            and bool(raw_writer_points)
            and observation_contracts is not None
            else "unavailable"
        )
        for interval in debug_silence_intervals:
            interval.setdefault("provenance_status", debug_provenance_status)
        unassigned_boundary_admissions: list[dict] = []
        silence_rows = _build_debug_silence_observations(
            debug_silence_intervals,
            normalized_writer_points,
            observation_contracts=observation_contracts,
            effective_plan=effective_plan,
            raw_writer_points=raw_writer_points,
            provenance_rows=provenance_rows,
            unassigned_boundary_admissions=unassigned_boundary_admissions,
        )
        silence_curve_comparison = _build_debug_silence_curve_comparison(
            debug_silence_intervals,
            preview_segments_by_vowel,
            normalized_writer_points,
        )
        trace.record_stage(
            "silence_observations",
            status="completed" if rms_records else "not_evaluable",
            reason_code=None if rms_records else "rms_unavailable",
            payload={
                "schema_version": 1,
                "contract_version": "ms28-b4-silence-v2",
                "projection_revision": revision,
                "diagnostic_threshold_rms": rms_payload.get("diagnostic_threshold_rms"),
                "open_epsilon": 1e-9,
                "frame_rate": 30,
                "observations": silence_rows,
                "unassigned_boundary_admissions": unassigned_boundary_admissions,
                "silence_policy": getattr(
                    effective_plan,
                    "silence_policy",
                    "not_available",
                ),
                "silence_core_frame_ranges": [
                    list(item)
                    for item in (
                        getattr(effective_plan, "silence_core_frame_ranges", ()) or ()
                    )
                ],
                "curve_comparison": silence_curve_comparison,
            },
        )

        (
            comparison_status,
            comparison_reason_code,
            comparison_payload,
        ) = _compare_debug_projection_points(preview_lookup, writer_lookup)
        terminal_execution = self._debug_execution_diagnostics(
            sync_context=sync_context,
            diagnostics_snapshot=diagnostics_snapshot,
            effective_writer_input_state=effective_writer_input_state,
            snapshot_point="projection_complete",
            preview_result=preview_result,
            writer_result=writer_result,
        )
        terminal_execution["operations"]["preview_projection"][
            "model_valid"
        ] = preview_status == "ready"
        trace.record_stage(
            "projection_comparison",
            status=comparison_status,
            reason_code=comparison_reason_code,
            payload={
                "projection_revision": revision,
                **comparison_payload,
                "silence_policy": getattr(
                    effective_plan,
                    "silence_policy",
                    "not_available",
                ),
                "silence_core_curve_comparison": silence_curve_comparison,
                "execution_diagnostics": terminal_execution,
            },
        )

    def _init_ui(self):
        self.root_panel = wx.Panel(self)
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._init_top_panel()
        self._init_param_panel()
        self._init_center_panel()
        self._init_bottom_panel()
        
        root_sizer.Add(self.top_panel, 0, wx.EXPAND | wx.ALL, 5)
        root_sizer.Add(self.param_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        root_sizer.Add(self.center_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        root_sizer.Add(self.bottom_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.root_panel.SetSizer(root_sizer)
        self.root_panel.Layout()
        
        self._bind_button_events()
        
        self.sync_ui_state()

    def _set_button_icon(self, button: ThemeButton, icon_filename: str, is_dark: bool):
        from resource_utils import get_resource_path
        icon_path = get_resource_path(f"assets/icons/toolbar/{icon_filename}")
        if icon_path.is_file():
            with wx.LogNull():
                img = wx.Image(str(icon_path), wx.BITMAP_TYPE_PNG)
            if img.IsOk():
                if not is_dark:
                    img.Replace(255, 255, 255, 0, 0, 0)
                img = img.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
                button.SetBitmap(wx.Bitmap(img))
                return

    def update_theme_icons(self, is_dark: bool):
        if not hasattr(self, '_button_icons'):
            return
        for btn, filename in self._button_icons.items():
            self._set_button_icon(btn, filename, is_dark)

    def _init_top_panel(self):
        self.top_panel = wx.Panel(self.root_panel)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_open_text = ThemeButton(self.top_panel, label="TEXT 読込")
        self.btn_open_wav = ThemeButton(self.top_panel, label="音声 読込")
        self.btn_process = ThemeButton(self.top_panel, label="解析実行")
        self.btn_save_vmd = ThemeButton(self.top_panel, label="VMD 保存")
        self.btn_export_mmd_wav = ThemeButton(self.top_panel, label="MMD用WAV出力")
        self.btn_export_mmd_wav.SetToolTip("MMDで読み込ませるためのWAVファイルを出力します。")
        self.btn_cancel_audio_worker = ThemeButton(self.top_panel, label="キャンセル")
        self.btn_cancel_audio_worker.SetToolTip("音声変換・出力処理をキャンセルします。")
        
        self.btn_play = ThemeButton(self.top_panel, label="")
        self.btn_play.SetToolTip("再生")
        self.btn_pause = ThemeButton(self.top_panel, label="")
        self.btn_pause.SetToolTip("一時停止")
        self.btn_stop = ThemeButton(self.top_panel, label="")
        self.btn_stop.SetToolTip("停止して先頭へ戻る")
        
        self.btn_zoom_in = ThemeButton(self.top_panel, label="")
        self.btn_zoom_in.SetToolTip("拡大")
        self.btn_zoom_out = ThemeButton(self.top_panel, label="")
        self.btn_zoom_out.SetToolTip("縮小")
        self.btn_zoom_reset = ThemeButton(self.top_panel, label="")
        self.btn_zoom_reset.SetToolTip("表示範囲を全体へ戻す")

        self._icon_only_buttons = (
            self.btn_play,
            self.btn_pause,
            self.btn_stop,
            self.btn_zoom_in,
            self.btn_zoom_out,
            self.btn_zoom_reset,
        )
        icon_button_size = self.FromDIP((32, 32))
        for button in self._icon_only_buttons:
            button.SetMinSize(icon_button_size)
            button.SetMaxSize(icon_button_size)
            button.SetSize(icon_button_size)
        
        self._button_icons = {
            self.btn_open_text: "textfileopen.png",
            self.btn_open_wav: "wavfileopen.png",
            self.btn_process: "execute.png",
            self.btn_save_vmd: "vmdsave.png",
            self.btn_play: "play.png",
            self.btn_pause: "pause.png",
            self.btn_stop: "stop.png",
            self.btn_zoom_in: "zoomin.png",
            self.btn_zoom_out: "zoomout.png",
            self.btn_zoom_reset: "zoomreset.png",
        }
        
        from gui_wx.theme import ThemeManager
        is_dark = ThemeManager.get_palette().is_dark
        self.update_theme_icons(is_dark)
        
        flags_btn = wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL
        top_sizer.Add(self.btn_open_text, 0, flags_btn, 5)
        top_sizer.Add(self.btn_open_wav, 0, flags_btn, 5)
        top_sizer.Add(self.btn_process, 0, flags_btn, 5)
        top_sizer.Add(self.btn_save_vmd, 0, flags_btn, 5)
        top_sizer.Add(self.btn_export_mmd_wav, 0, flags_btn, 5)
        top_sizer.Add(self.btn_cancel_audio_worker, 0, flags_btn, 5)
        
        top_sizer.AddSpacer(20)
        top_sizer.Add(self.btn_play, 0, flags_btn, 5)
        top_sizer.Add(self.btn_pause, 0, flags_btn, 5)
        top_sizer.Add(self.btn_stop, 0, flags_btn, 5)
        
        top_sizer.AddSpacer(20)
        top_sizer.Add(self.btn_zoom_in, 0, flags_btn, 5)
        top_sizer.Add(self.btn_zoom_out, 0, flags_btn, 5)
        top_sizer.Add(self.btn_zoom_reset, 0, flags_btn | wx.RIGHT, 5)
        
        self.top_panel.SetSizer(top_sizer)

    def _init_param_panel(self):
        self.param_panel = ParameterPanel(self.root_panel)

    def _init_center_panel(self):
        self.center_panel = wx.Panel(self.root_panel)
        center_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.info_panel = InfoPanel(self.center_panel)
        self.info_panel.bind_transcription_edit_handlers(
            self._on_transcription_apply,
            self._on_transcription_revert,
        )
        self.placeholder_container = PlaceholderContainer(self.center_panel)
        self.placeholder_container.on_pan_callback = self._on_pan_request
        self.placeholder_container.on_scrub_start_callback = (
            self._on_playback_scrub_start_request
        )
        self.placeholder_container.on_scrub_update_callback = (
            self._on_playback_scrub_update_request
        )
        self.placeholder_container.on_scrub_end_callback = (
            self._on_playback_scrub_end_request
        )
        self.placeholder_container.on_seek_callback = (
            self._on_playback_seek_request
        )
        self.placeholder_container.on_selection_request_callback = (
            self._on_preview_selection_request
        )
        self.right_pane = RightPane(self.center_panel)
        self.right_pane.on_selected_event_edit_callback = (
            self._on_selected_event_edit_request
        )
        self.right_pane.on_selected_event_edit_boundary_callback = (
            self._on_selected_event_edit_boundary_request
        )
        self.right_pane.on_selected_event_reset_callback = (
            self._on_selected_event_reset_request
        )
        self.right_pane.on_selected_event_mode_callback = (
            self._on_selected_event_edit_request
        )
        self.right_pane.on_cleanup_event_select_callback = (
            self._on_cleanup_event_selection_request
        )
        self.right_pane.on_preset_select_callback = self._on_preset_select_request
        self.right_pane.on_preset_apply_callback = self._on_preset_apply_request
        self.right_pane.on_preset_create_callback = self._on_preset_create_request
        self.right_pane.on_preset_update_callback = self._on_preset_update_request
        self.right_pane.on_preset_delete_callback = self._on_preset_delete_request
        self.right_pane.on_model_profile_select_callback = (
            self._on_model_profile_select_request
        )
        self.right_pane.on_model_profile_apply_callback = (
            self._on_model_profile_apply_request
        )
        self.right_pane.on_model_profile_create_callback = (
            self._on_model_profile_create_request
        )
        self.right_pane.on_model_profile_update_callback = (
            self._on_model_profile_update_request
        )
        self.right_pane.on_model_profile_delete_callback = (
            self._on_model_profile_delete_request
        )
        self.right_pane.on_whisper_model_select_callback = (
            self._on_whisper_model_select_request
        )
        self.right_pane.on_whisper_model_download_callback = (
            self._on_whisper_model_download_request
        )
        self.right_pane.on_whisper_model_apply_callback = (
            self._on_whisper_model_apply_request
        )
        self.right_pane.on_whisper_model_cancel_callback = (
            self._on_whisper_model_cancel_request
        )
        self.right_pane.on_whisper_model_delete_callback = (
            self._on_whisper_model_delete_request
        )
        self.right_pane.on_whisper_storage_root_callback = (
            self._on_whisper_storage_root_request
        )
        
        center_sizer.Add(self.info_panel, 1, wx.EXPAND | wx.RIGHT, 5)
        center_sizer.Add(self.placeholder_container, 3, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        center_sizer.Add(self.right_pane, 1, wx.EXPAND | wx.LEFT, 5)
        self.center_panel.SetSizer(center_sizer)

    def _on_pan_request(self, delta_sec: float):
        if self.controller:
            self.controller.request_pan(delta_sec)

    def _on_playback_scrub_start_request(self, position_sec: float) -> bool:
        if not self.controller:
            return False
        return self.controller.request_playback_scrub_start(position_sec)

    def _on_playback_scrub_update_request(self, position_sec: float):
        if self.controller:
            self.controller.request_playback_scrub_update(position_sec)

    def _on_playback_scrub_end_request(self, position_sec: float):
        if self.controller:
            self.controller.request_playback_scrub_end(position_sec)

    def _on_playback_seek_request(self, position_sec: float) -> bool:
        if not self.controller:
            return False
        return self.controller.request_playback_seek(position_sec)

    def _init_bottom_panel(self):
        self.bottom_panel = wx.Panel(self.root_panel)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.st_status_main = wx.StaticText(self.bottom_panel, label="準備完了 (WX Mode)")
        bottom_sizer.Add(self.st_status_main, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.gauge_output_edit_progress = wx.Gauge(
            self.bottom_panel,
            range=100,
            size=(100, -1),
            style=wx.GA_HORIZONTAL,
        )
        self.gauge_output_edit_progress.Hide()
        self._output_edit_progress_timer = wx.Timer(self.bottom_panel)
        self.bottom_panel.Bind(
            wx.EVT_TIMER,
            self._on_output_edit_progress_timer,
            self._output_edit_progress_timer,
        )
        bottom_sizer.Add(
            self.gauge_output_edit_progress,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT,
            8,
        )
        bottom_sizer.AddStretchSpacer(1)
        
        self.bottom_panel.SetSizer(bottom_sizer)

    def start_output_edit_progress(self) -> None:
        if not self.gauge_output_edit_progress.IsShown():
            self.gauge_output_edit_progress.Show()
            self.bottom_panel.Layout()
        if not self._output_edit_progress_timer.IsRunning():
            self._output_edit_progress_timer.Start(100)
        self.gauge_output_edit_progress.Pulse()

    def stop_output_edit_progress(self) -> None:
        if self._output_edit_progress_timer.IsRunning():
            self._output_edit_progress_timer.Stop()
        if self.gauge_output_edit_progress.IsShown():
            self.gauge_output_edit_progress.Hide()
            self.bottom_panel.Layout()

    def _on_output_edit_progress_timer(self, event) -> None:
        if self.gauge_output_edit_progress.IsShown():
            self.gauge_output_edit_progress.Pulse()

    def _bind_button_events(self):
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_text, self.btn_open_text)
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_wav, self.btn_open_wav)
        self.Bind(wx.EVT_BUTTON, self._on_btn_process, self.btn_process)
        self.Bind(wx.EVT_BUTTON, self._on_btn_save_vmd, self.btn_save_vmd)
        self.Bind(wx.EVT_BUTTON, self._on_btn_export_mmd_wav, self.btn_export_mmd_wav)
        self.Bind(wx.EVT_BUTTON, self._on_btn_cancel_audio_worker, self.btn_cancel_audio_worker)
        self.Bind(wx.EVT_BUTTON, self._on_btn_play, self.btn_play)
        self.Bind(wx.EVT_BUTTON, self._on_btn_pause, self.btn_pause)
        self.Bind(wx.EVT_BUTTON, self._on_btn_stop, self.btn_stop)
        
        self.Bind(wx.EVT_BUTTON, self._on_btn_zoom_in, self.btn_zoom_in)
        self.Bind(wx.EVT_BUTTON, self._on_btn_zoom_out, self.btn_zoom_out)
        self.Bind(wx.EVT_BUTTON, self._on_btn_zoom_reset, self.btn_zoom_reset)
        self.Bind(
            wx.EVT_BUTTON,
            self._on_apply_output_edits,
            self.param_panel.btn_apply_output_edits,
        )

    def sync_ui_state(
        self,
        *,
        effective_plan_hint: EffectiveShapePlan | None = None,
        adjustment_only: bool = False,
    ):
        """[MS15-B5] 統合UI状態同期メソッド"""
        self._invalidate_stale_shared_final_output_request()
        if self.ui_state.output_edit_draft_dirty:
            self._sync_output_edit_draft_view(
                adjustment_only=adjustment_only,
                effective_plan_hint=effective_plan_hint,
            )
            return
        self.param_panel.btn_apply_output_edits.SetLabel("変更を適用")
        self.param_panel.btn_apply_output_edits.Enable(False)
        self.param_panel.set_output_edit_status(
            self.ui_state.output_edit_apply_status or ""
        )
        sync_context = self._build_current_ui_sync_context(
            effective_plan_hint=effective_plan_hint,
        )
        self._current_ui_sync_context = sync_context
        (
            writer_state,
            effective_plan,
            failure_reason,
        ) = self.prepare_current_effective_output(sync_context=sync_context)
        if not self.ui_state.output_edit_draft_dirty:
            self._restore_accepted_output_preview_if_current(
                effective_plan,
                self._selected_audio_duration_sec() or 0.0,
            )
        diagnostics_snapshot = self.build_and_store_output_diagnostics_snapshot(
            effective_shape_plan=effective_plan,
            effective_writer_input_state=writer_state,
            effective_writer_input_failure_reason=failure_reason,
        )
        self.update_action_states(
            diagnostics_snapshot,
            sync_context=sync_context,
        )
        self.right_pane.set_selected_event_editor_revision(
            self.ui_state.selected_event_editor_revision
        )
        self._sync_preset_panel()
        self._sync_model_profile_panel()
        self._sync_whisper_model_panel(diagnostics_snapshot)
        self.update_status_display(diagnostics_snapshot)

        self.right_pane.set_info_snapshot(
            diagnostics_snapshot,
            analysis_in_progress=self._analysis_info_in_progress,
        )
        self.right_pane.set_warning_snapshot(diagnostics_snapshot)
        if not adjustment_only:
            self._sync_playback_context()

        # current_timing_planが存在しない場合（未解析やファイル変更時など）はプレビューをクリア
        if not self.ui_state.current_timing_plan:
            self.placeholder_container.clear_selection()
            self.right_pane.clear_selected_event()
            pass # _update_preview_display() handles this now, or we can handle placeholder logic there

        self._record_debug_projection(
            sync_context=sync_context,
            diagnostics_snapshot=diagnostics_snapshot,
            effective_writer_input_state=writer_state,
            effective_writer_input_failure_reason=failure_reason,
        )

        # [MS16-B6] 選択状態の同期と RightPane への反映
        self.placeholder_container.set_selected_source_event_index(self.ui_state.selected_source_event_index)
        self.update_selected_event_display(sync_context=sync_context)

        if not self.ui_state.is_busy and not self._analysis_info_in_progress:
            request_started = self.request_shared_final_output_context()
            shared_context = self.ui_state.final_output_state.current_context
            shared_snapshot = self._shared_final_output_diagnostics
            if shared_context is not None and shared_snapshot is not None:
                self.update_action_states(shared_snapshot, sync_context=sync_context)
                self.right_pane.set_info_snapshot(shared_snapshot)
                self.right_pane.set_warning_snapshot(shared_snapshot)
                self.update_status_display(shared_snapshot)
            else:
                self.btn_save_vmd.Enable(False)
                self.mi_vmd_save.Enable(False)
                self.mi_diagnostic_report_save.Enable(False)
                self.mi_mmd_delivery_export.Enable(False)
                if not request_started:
                    self._clear_shared_final_output_view(
                        "解析が必要です"
                    )
                    if isinstance(diagnostics_snapshot, OutputDiagnosticsSnapshot):
                        self.right_pane.set_info_snapshot(diagnostics_snapshot)
                        self.right_pane.set_warning_snapshot(diagnostics_snapshot)
                        self.update_status_display(diagnostics_snapshot)
        else:
            self.btn_save_vmd.Enable(False)
            self.mi_vmd_save.Enable(False)
            self.mi_diagnostic_report_save.Enable(False)
            self.mi_mmd_delivery_export.Enable(False)

        if not adjustment_only:
            self.placeholder_container.Refresh()
            self.param_panel.Refresh()

    def _sync_output_edit_draft_view(
        self,
        *,
        adjustment_only: bool,
        effective_plan_hint: EffectiveShapePlan | None = None,
    ) -> None:
        """Project draft geometry without requesting or replacing final output."""
        state = self.ui_state
        self.param_panel.btn_apply_output_edits.SetLabel(
            "適用結果を破棄"
            if self._pending_output_apply is not None
            else "変更を適用"
        )
        base_input = self._build_current_base_timing_plan_input()
        snapshot = state.current_adjustment_snapshot
        sync_context = None
        if base_input is not None and snapshot is not None:
            try:
                sync_context = build_ui_sync_context(
                    base_input,
                    snapshot,
                    effective_plan_hint=effective_plan_hint,
                    defer_resolution=effective_plan_hint is None,
                )
            except (AdjustmentContractError, TypeError, ValueError):
                state.output_edit_draft_error = "編集タイムラインを更新できません。"
            if effective_plan_hint is None and state.output_edit_draft_error is None:
                self._request_output_edit_draft_preview(base_input, snapshot)
        if sync_context is not None and sync_context.effective_plan is not None:
            self._current_ui_sync_context = sync_context
            self._update_preview_display(sync_context=sync_context)
            self.placeholder_container.set_selected_source_event_index(
                state.selected_source_event_index
            )
        self.update_selected_event_display(sync_context=sync_context)
        # While a draft is pending or invalid, keep the last valid Preview
        # model visible. Replacing it with a placeholder clears its zoom range.
        self.param_panel.set_output_edit_status(
            state.output_edit_apply_status
            or (
                "変更未適用（編集表示）"
                if state.output_edit_draft_error is None
                else state.output_edit_draft_error
            )
        )
        self.update_status_display()
        can_apply = bool(
            state.analysis_result_valid
            and not state.analysis_pending_rebuild
            and not state.is_busy
            and state.output_edit_draft_error is None
            and self._latest_draft_preview_request is None
            and self._pending_selected_event_projection is None
            and state.current_output_edit_state is not None
            and not self._selected_event_editor_has_uncommitted_input()
        )
        self.param_panel.btn_apply_output_edits.Enable(can_apply)
        self._sync_preset_panel()
        self._sync_model_profile_panel()
        if sync_context is not None and sync_context.effective_plan is not None:
            self.update_action_states(
                state.current_output_diagnostics_snapshot,
                sync_context=sync_context,
                busy_override=state.is_busy,
            )
        elif sync_context is not None:
            history_ready = bool(
                not state.is_busy
                and state.current_adjustment_snapshot is not None
                and state.current_adjustment_snapshot.base_plan_identity
                == sync_context.base_plan_identity
            )
            self.mi_adjustment_undo.Enable(
                history_ready and state.can_undo_adjustment
            )
            self.mi_adjustment_redo.Enable(
                history_ready and state.can_redo_adjustment
            )
        self.btn_save_vmd.Enable(False)
        self.mi_vmd_save.Enable(False)
        self.mi_diagnostic_report_save.Enable(False)
        self.mi_mmd_delivery_export.Enable(False)
        diagnostics_snapshot = self._shared_final_output_diagnostics
        if not isinstance(diagnostics_snapshot, OutputDiagnosticsSnapshot):
            diagnostics_snapshot = state.current_output_diagnostics_snapshot
        if isinstance(diagnostics_snapshot, OutputDiagnosticsSnapshot):
            self.right_pane.set_info_snapshot(
                diagnostics_snapshot,
                pending_edits=True,
            )
        else:
            self.right_pane.set_info_text(
                "保存前に「変更を適用」してください。",
                pending_edits=True,
                pending_diagnostics=False,
            )
        self.right_pane.set_selected_event_editor_revision(
            state.selected_event_editor_revision
        )
        if not adjustment_only and sync_context is not None and sync_context.effective_plan is not None:
            self._sync_playback_context()

    def _request_output_edit_draft_preview(
        self,
        base_input: BaseTimingPlanInput,
        snapshot,
    ) -> None:
        state = self.ui_state
        identity = build_base_plan_identity(base_input)
        current = self._latest_draft_preview_request
        if (
            current is not None
            and current.source_revision == state.output_edit_source_revision
            and current.draft_revision == state.output_edit_draft_revision
            and current.base_plan_identity_digest == identity.digest
        ):
            return
        self._draft_projection_ticket += 1
        request = OutputEditDraftProjectionRequest(
            ticket=self._draft_projection_ticket,
            source_revision=state.output_edit_source_revision,
            draft_revision=state.output_edit_draft_revision,
            base_plan_identity_digest=identity.digest,
            purpose="draft_preview",
            compute=lambda: resolve_effective_shape_plan(base_input, snapshot),
        )
        self._latest_draft_preview_request = request
        state.output_edit_apply_status = "編集タイムラインを更新中…"
        if not self._output_edit_draft_projection_coordinator.request(request):
            self._latest_draft_preview_request = None
            state.output_edit_apply_status = None
            state.output_edit_draft_error = "編集タイムラインを開始できません。"

    def _queue_selected_event_projection(
        self,
        *,
        purpose: str,
        base_input: BaseTimingPlanInput,
        snapshot,
        compute: Callable[[], object],
        operation_handle,
        payload: dict[str, object],
    ) -> bool:
        if self._pending_selected_event_projection is not None:
            return False
        state = self.ui_state
        identity = build_base_plan_identity(base_input)
        self._draft_projection_ticket += 1
        request = OutputEditDraftProjectionRequest(
            ticket=self._draft_projection_ticket,
            source_revision=state.output_edit_source_revision,
            draft_revision=state.output_edit_draft_revision,
            base_plan_identity_digest=identity.digest,
            purpose=purpose,
            compute=compute,
            payload=payload,
        )
        self._pending_selected_event_projection = {
            "request": request,
            "operation_handle": operation_handle,
            "payload": payload,
        }
        self.update_status("編集表示を計算中…")
        self.param_panel.btn_apply_output_edits.Enable(False)
        self.btn_save_vmd.Enable(False)
        self.mi_vmd_save.Enable(False)
        self.mi_diagnostic_report_save.Enable(False)
        self.mi_mmd_delivery_export.Enable(False)
        self._set_selected_event_projection_controls_enabled(False)
        if not self._output_edit_draft_projection_coordinator.request(request):
            self._pending_selected_event_projection = None
            self._set_selected_event_projection_controls_enabled(True)
            self.update_status_display()
            return False
        return True

    def _set_selected_event_projection_controls_enabled(self, enabled: bool) -> None:
        if self.ui_state.is_busy:
            enabled = False
        for control in getattr(self.right_pane, "_selected_editor_controls", {}).values():
            control.Enable(enabled)
        overlap_override = getattr(
            self.right_pane, "chk_manual_overlap_limit_override", None
        )
        editor_state = getattr(self.right_pane, "_selected_editor_state", None)
        if overlap_override is not None:
            overlap_override.Enable(
                bool(
                    enabled
                    and editor_state is not None
                    and editor_state.manual_overlap_override_enabled
                )
            )
        reset_button = getattr(self.right_pane, "btn_reset_selected_event", None)
        if reset_button is not None:
            reset_button.Enable(
                bool(enabled and editor_state is not None and editor_state.reset_enabled)
            )

    def _output_edit_snapshot_range_error(
        self,
        effective_plan: EffectiveShapePlan,
        snapshot: AdjustmentLayerSnapshot,
    ) -> str | None:
        base_input = self._build_current_base_timing_plan_input()
        if base_input is None:
            return None
        base_events = {
            event.base_event_index: event for event in effective_plan.base_events
        }
        for adjustment in snapshot.adjustments:
            if adjustment.end_offset_frames == 0:
                continue
            base_event = base_events.get(adjustment.base_event_index)
            if base_event is None:
                continue
            minimum = base_event.peak_frame - base_event.end_frame
            maximum = resolve_manual_crossfade_end_offset_max(
                effective_plan,
                adjustment.base_event_index,
                source_duration_frames=base_input.source_duration_frames,
                adjustment_snapshot=snapshot,
            )
            if adjustment.end_offset_frames < minimum or adjustment.end_offset_frames > maximum:
                return (
                    f"Event {adjustment.base_event_index}の終了offsetが許容範囲外です。"
                    f"範囲は {minimum}〜{maximum} です。"
                )
        return None

    def _finish_selected_event_projection(
        self,
        request: OutputEditDraftProjectionRequest,
        result: OutputEditDraftProjectionResult,
    ) -> None:
        pending = self._pending_selected_event_projection
        if pending is None or pending.get("request") != request:
            return
        self._pending_selected_event_projection = None
        self._set_selected_event_projection_controls_enabled(True)
        self.right_pane.clear_selected_event_edit_pending()
        payload = pending["payload"]
        operation_handle = pending["operation_handle"]
        state = self.ui_state
        current_editor_revision = payload["editor_revision"]
        if (
            state.output_edit_source_revision != request.source_revision
            or state.output_edit_draft_revision != request.draft_revision
            or state.current_timing_plan is not payload["timing_plan"]
            or state.current_adjustment_snapshot != payload["snapshot"]
            or state.selected_source_event_index != payload["event_index"]
            or state.selected_event_editor_revision != current_editor_revision
        ):
            self._finish_debug_operation(
                operation_handle,
                "ignored",
                reason_code="stale_selected_event_projection",
            )
            self.update_status_display()
            return
        if result.error is not None:
            requested_snapshot = payload.get("requested_snapshot")
            if (
                request.purpose == "selected_event_edit"
                and getattr(result.error, "safe_code", None)
                == "manual_crossfade_limit_exceeded"
                and isinstance(requested_snapshot, AdjustmentLayerSnapshot)
                and state.commit_adjustment_snapshot(
                    requested_snapshot,
                    expected_base_plan_identity_digest=(
                        request.base_plan_identity_digest
                    ),
                    coalesce_key=payload.get("coalescing_key"),
                )
            ):
                state.output_edit_draft_error = (
                    "制限OFFでは終了offsetが許容範囲外です。"
                    "終了offsetを範囲内へ戻すか、制限を再解除してください。"
                )
                self._selected_event_notice = "範囲外の値を編集draftに保持しています。"
                self.sync_ui_state(adjustment_only=True)
                self._finish_debug_operation(
                    operation_handle,
                    "completed",
                    reason_code="out_of_range_draft_retained",
                    payload={
                        "event_index": payload["event_index"],
                        "field": payload["field"],
                        "draft_retained": True,
                        "apply_blocked": True,
                    },
                )
                return
            message = (
                "補正をリセットできません。"
                if request.purpose == "selected_event_reset"
                else "補正を適用できません。"
            )
            self.update_selected_event_display(
                sync_context=self._current_ui_sync_context
            )
            self.right_pane.set_selected_event_editor_error(message)
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=(
                    "reset_contract_rejected"
                    if request.purpose == "selected_event_reset"
                    else "edit_contract_rejected"
                ),
                payload={"event_index": payload["event_index"]},
            )
            self.update_status_display()
            return
        update_result = result.value
        if not hasattr(update_result, "canonical_snapshot") or not hasattr(
            update_result, "effective_plan"
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="draft_projection_result_invalid",
            )
            self.update_status_display()
            return
        if update_result.canonical_snapshot == payload["snapshot"]:
            self.sync_ui_state(
                effective_plan_hint=update_result.effective_plan,
                adjustment_only=True,
            )
            self._finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="same_value",
                payload={"event_index": payload["event_index"], "changed": False},
            )
            return
        if not state.commit_adjustment_snapshot(
            update_result.canonical_snapshot,
            expected_base_plan_identity_digest=request.base_plan_identity_digest,
            coalesce_key=payload.get("coalescing_key"),
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="edit_not_committed",
                payload={"event_index": payload["event_index"]},
            )
            self.update_status_display()
            return
        state.output_edit_draft_error = self._output_edit_snapshot_range_error(
            update_result.effective_plan,
            update_result.canonical_snapshot,
        )
        if (
            request.purpose == "selected_event_reset"
            and not state.output_edit_draft_dirty
        ):
            state.require_output_edit_apply_for_current_state()
        if request.purpose == "selected_event_reset":
            notices = ["選択イベントの出力編集をリセットしました。"]
            if update_result.removed_tail_override_event_indices:
                notices.append("group変更により他イベントの末尾補正も解除しました。")
            if state.has_event_adjustments:
                notices.append(
                    "他イベントの編集も保持しています。VMDへの反映は「変更を適用」後です。"
                )
            self._selected_event_notice = "\n".join(notices)
            action = "selected_event_reset"
            reason_code = "event_adjustment_reset"
        else:
            notices = []
            if update_result.removed_tail_override_event_indices:
                indices = ", ".join(
                    str(index)
                    for index in update_result.removed_tail_override_event_indices
                )
                notices.append(f"group変更によりEvent {indices}の末尾補正を解除しました。")
            if update_result.removed_slope_override_event_indices:
                indices = ", ".join(
                    str(index)
                    for index in update_result.removed_slope_override_event_indices
                )
                notices.append(
                    "閉口スムーズが反映されなくなったため、"
                    f"Event {indices}の閉口傾斜比を解除しました。"
                )
            notices.append(
                "編集表示へ反映しました。VMDへの反映は「変更を適用」後です。"
                if state.output_edit_draft_dirty
                else "適用済みの値へ戻しました。"
            )
            self._selected_event_notice = "\n".join(notices)
            action = "selected_event_edit"
            reason_code = "edit_applied"
        self.sync_ui_state(
            effective_plan_hint=update_result.effective_plan,
            adjustment_only=True,
        )
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code=reason_code,
            payload={
                "event_index": payload["event_index"],
                "field": payload.get("field"),
                "changed": True,
                **(
                    {"before": payload.get("before_value"), "after": payload.get("after_value")}
                    if action == "selected_event_edit"
                    else {}
                ),
            },
        )

    def _on_output_edit_draft_projection_result(
        self,
        request: OutputEditDraftProjectionRequest,
        result: OutputEditDraftProjectionResult,
    ) -> None:
        if request.purpose == "draft_preview":
            if self._latest_draft_preview_request != request:
                return
            self._latest_draft_preview_request = None
            state = self.ui_state
            if (
                state.output_edit_source_revision != request.source_revision
                or state.output_edit_draft_revision != request.draft_revision
                or not state.output_edit_draft_dirty
            ):
                return
            state.output_edit_apply_status = None
            if result.error is not None or not isinstance(result.value, EffectiveShapePlan):
                state.output_edit_draft_error = "編集タイムラインを更新できません。"
                self._sync_output_edit_draft_view(adjustment_only=True)
                return
            snapshot = state.current_adjustment_snapshot
            state.output_edit_draft_error = (
                None
                if snapshot is None
                else self._output_edit_snapshot_range_error(
                    result.value,
                    snapshot,
                )
            )
            self._sync_output_edit_draft_view(
                adjustment_only=True,
                effective_plan_hint=result.value,
            )
            return
        self._finish_selected_event_projection(request, result)

    def _capture_final_output_lifecycle_signature(
        self,
        *,
        output_state: OutputEditState | None = None,
        timing_plan=None,
        model_profile_state: ModelProfileState | None = None,
    ) -> tuple[object, ...]:
        state = self.ui_state
        applied_state = output_state or state.applied_output_edit_state
        if applied_state is None:
            applied_state = state.current_output_edit_state
        applied_profile = model_profile_state or (
            state.output_edit_draft_baseline.model_profile_state
            if state.output_edit_draft_baseline is not None
            else state.model_profile_state
        )
        applied_generation = (
            state.generation_state
            if applied_state is None
            else applied_state.generation_state
        )
        signature_plan = timing_plan or state.current_timing_plan
        applied_upper_limit = (
            state.resolved_morph_upper_limit
            if applied_state is None
            else applied_state.morph_upper_limit
        )
        applied_adjustment_snapshot = (
            state.current_adjustment_snapshot
            if applied_state is None
            else applied_state.adjustment_snapshot
        )
        applied_output_names = get_builtin_morph_name_set(
            applied_generation.resolved_morph_name_set_id
        ).output_names
        selected_analysis_wav = (
            None
            if state.selected_analysis_wav is None
            else getattr(state.selected_analysis_wav, "analysis_wav_path", None)
        )
        profile = applied_profile
        evaluation_request = getattr(self, "_transition_evaluation_request", None)
        transition_request_binding = (
            None
            if evaluation_request is None
            else (
                evaluation_request.policy.policy_digest,
                evaluation_request.b1_contract_sha256,
                evaluation_request.evaluation_session_id,
                evaluation_request.input_manifest_sha256,
            )
        )
        default_selection = self._current_default_transition_selection()
        cleanup_request = getattr(self, "_cleanup_evaluation_request", None)
        acoustic_snapshot = getattr(
            signature_plan,
            "transition_acoustic_snapshot",
            None,
        )
        transition_acoustic_digest = getattr(
            acoustic_snapshot,
            "content_digest",
            None,
        )
        return (
            state.input_mode,
            state.selected_text_path,
            state.selected_wav_path,
            selected_analysis_wav,
            state.selected_text_content,
            state.analysis_text_content,
            state.transcription_text,
            id(signature_plan),
            state.analysis_result_valid,
            state.analysis_pending_rebuild,
            applied_adjustment_snapshot,
            applied_generation,
            profile.active_model_profile_id,
            profile.active_profile_baseline_preset_id,
            profile.resolution_status,
            profile.resolution_reason_code,
            applied_upper_limit,
            applied_output_names,
            applied_generation.generation_settings.closing_hold_frames,
            applied_generation.generation_settings.closing_softness_frames,
            transition_request_binding,
            None if default_selection is None else default_selection.selection_digest,
            (
                None
                if self._current_default_cleanup_selection() is None
                else self._current_default_cleanup_selection().selection_digest
            ),
            transition_acoustic_digest,
            None if cleanup_request is None else cleanup_request.request_digest,
        )

    def _invalidate_stale_shared_final_output_request(self) -> None:
        signature = self._capture_final_output_lifecycle_signature()
        lifecycle = self.ui_state.final_output_state
        pending = self._latest_shared_final_output_request
        pending_apply = self._pending_output_apply
        if (
            pending is not None
            and pending_apply is not None
            and pending_apply.get("request") == pending
        ):
            # The candidate apply has its own lifecycle. Keep the last accepted
            # applied context intact until the candidate succeeds or fails.
            return
        if (
            pending is not None
            and pending.snapshot.lifecycle_signature != signature
        ):
            lifecycle.invalidate_context()
            self._latest_shared_final_output_request = None
            self.right_pane.clear_shared_final_output_restrictions()
            self.right_pane.clear_transition_summary()
            self.right_pane.clear_cleanup_event_choices()
        current = lifecycle.current_context
        if current is None and self._shared_final_output_diagnostics is not None:
            self._shared_final_output_diagnostics = None
            self.right_pane.clear_transition_summary()
            self.right_pane.clear_cleanup_event_choices()
        if (
            current is not None
            and getattr(current, "lifecycle_signature", None) != signature
        ):
            lifecycle.invalidate_context()
            self._shared_final_output_diagnostics = None
            self.right_pane.clear_shared_final_output_restrictions()
            self.right_pane.clear_transition_summary()
            self.right_pane.clear_cleanup_event_choices()

    def _remember_accepted_output_preview(
        self,
        context,
        preview_data,
        duration_sec: float,
    ) -> None:
        lifecycle_signature = getattr(context, "lifecycle_signature", None)
        input_identity = getattr(context, "input_identity", None)
        identity = getattr(context, "identity", None)
        if (
            not isinstance(lifecycle_signature, tuple)
            or input_identity is None
            or identity is None
        ):
            self._accepted_output_preview_cache = None
            return
        self._accepted_output_preview_cache = (
            preview_data,
            duration_sec,
            input_identity.base_plan_digest,
            identity.binding_digest,
            lifecycle_signature,
        )

    def _restore_accepted_output_preview_if_current(
        self,
        effective_plan,
        duration_sec: float,
    ) -> bool:
        state = self.ui_state
        context = state.final_output_state.current_context
        cache = self._accepted_output_preview_cache
        current_output = state.current_output_edit_state
        applied_output = state.applied_output_edit_state
        if (
            state.output_edit_draft_dirty
            or context is None
            or cache is None
            or current_output is None
            or current_output != applied_output
        ):
            return False
        preview_data, cached_duration, base_digest, binding, lifecycle_signature = (
            cache
        )
        identity = context.identity
        expected_signature = self._capture_final_output_lifecycle_signature()
        if (
            context.lifecycle_signature != lifecycle_signature
            or lifecycle_signature != expected_signature
            or context.input_identity.base_plan_digest != base_digest
            or identity.binding_digest != binding
            or getattr(
                getattr(effective_plan, "base_plan_identity", None),
                "digest",
                None,
            )
            != base_digest
            or cached_duration != duration_sec
        ):
            return False
        self.placeholder_container.set_identity_aware_preview_data(
            preview_data,
            cached_duration,
            base_digest,
            final_output_binding=binding,
        )
        preview_model = self.placeholder_container.pnl_preview.model
        selected_index = state.selected_source_event_index
        if (
            selected_index is not None
            and state.selected_base_plan_identity_digest == base_digest
            and preview_model.find_event_hit_region(selected_index) is not None
        ):
            self.placeholder_container.set_selected_source_event_index(
                selected_index
            )
        return True

    def _clear_shared_final_output_view(self, message: str) -> None:
        self._shared_final_output_diagnostics = None
        self._accepted_output_preview_cache = None
        self.btn_save_vmd.Enable(False)
        self.mi_vmd_save.Enable(False)
        self.mi_diagnostic_report_save.Enable(False)
        self.mi_mmd_delivery_export.Enable(False)
        self.placeholder_container.set_preview_placeholder_text(message)
        self.right_pane.clear_shared_final_output_restrictions()
        self.right_pane.clear_transition_summary()
        self.right_pane.clear_cleanup_event_choices()
        self.right_pane.set_info_text(message)
        self.right_pane.clear_warnings()

    def request_shared_final_output_context(
        self,
        *,
        closure_contract: ClosureContract | None = None,
    ) -> bool:
        """Request the shared producer used by Preview, diagnostics, and saves."""
        state = self.ui_state
        if (
            state.output_edit_draft_dirty
            or self._pending_output_apply is not None
            or self._pending_selected_event_projection is not None
        ):
            return False
        self._refresh_transition_application_status()
        had_shared_context = state.final_output_state.current_context is not None
        current_context = state.final_output_state.current_context
        current_identity = getattr(current_context, "identity", None)
        if (
            current_context is not None
            and getattr(current_context, "lifecycle_signature", None)
            == self._capture_final_output_lifecycle_signature()
            and current_identity is not None
            and self._shared_final_output_diagnostics is not None
            and self._shared_final_output_diagnostics.shared_final_output_identity
            == current_identity
            and self.placeholder_container.pnl_preview.model.final_output_binding
            == current_identity.binding_digest
        ):
            return True
        sync_context = self._build_current_ui_sync_context()
        adjustment_snapshot = state.current_adjustment_snapshot
        if sync_context is None or adjustment_snapshot is None:
            state.final_output_state.invalidate_context()
            if had_shared_context:
                self._clear_shared_final_output_view(
                    "共有最終出力を現在条件で採用できません。"
                )
            return False
        try:
            diagnostics_seed = capture_shared_output_diagnostics_seed(
                state,
                generation_state=state.generation_state,
                active_preset_display_name=self._active_preset_display_name,
                output_morph_names=self._resolved_output_morph_names(),
                projection_generation=self._diagnostics_projection_generation,
            )
        except (AttributeError, TypeError, ValueError):
            state.final_output_state.invalidate_context()
            if had_shared_context:
                self._clear_shared_final_output_view(
                    "共有最終出力を現在条件で採用できません。"
                )
            return False
        analysis_wav_path = (
            None
            if state.selected_analysis_wav is None
            else getattr(state.selected_analysis_wav, "analysis_wav_path", None)
        )
        request = request_shared_final_output(
            lifecycle=state.final_output_state,
            coordinator=self._final_output_sync_coordinator,
            input_mode=state.input_mode,
            base_input=sync_context.base_input,
            adjustment_snapshot=adjustment_snapshot,
            effective_plan=sync_context.effective_plan,
            resolved_profile_id=state.model_profile_state.active_model_profile_id,
            output_morph_names=self._resolved_output_morph_names(),
            source_audio_path=state.selected_wav_path,
            analysis_wav_path=analysis_wav_path,
            text_path=state.selected_text_path,
            analysis_result_valid=state.analysis_result_valid,
            analysis_pending_rebuild=state.analysis_pending_rebuild,
            is_busy=state.is_busy or self._analysis_info_in_progress,
            closure_contract=closure_contract,
            lifecycle_signature=self._capture_final_output_lifecycle_signature(),
            diagnostics_seed=diagnostics_seed,
            transition_evaluation_request=self._transition_evaluation_request,
            default_transition_selection=self._current_default_transition_selection(),
            cleanup_evaluation_request=self._cleanup_evaluation_request,
            default_cleanup_selection=self._current_default_cleanup_selection(),
            transition_acoustic_snapshot=(
                getattr(state.current_timing_plan, "transition_acoustic_snapshot", None)
                if (
                    self._transition_evaluation_request is not None
                    or self._bounded_candidate_enabled()
                )
                else None
            ),
        )
        self._latest_shared_final_output_request = request
        if request is not None:
            self._shared_final_output_diagnostics = None
            self.btn_save_vmd.Enable(False)
            self.mi_vmd_save.Enable(False)
            self.mi_diagnostic_report_save.Enable(False)
            self.mi_mmd_delivery_export.Enable(False)
            self.placeholder_container.set_preview_placeholder_text(
                "解析結果出力を準備中", loading=True
            )
            self.right_pane.clear_shared_final_output_restrictions()
            self.right_pane.clear_transition_summary()
            self.right_pane.clear_cleanup_event_choices()
            self.right_pane.set_info_text(
                "共有最終出力: 検証中。診断と保存可否は未確定です。"
            )
            self.right_pane.clear_warnings()
        elif had_shared_context:
            self._clear_shared_final_output_view(
                "共有最終出力を現在条件で採用できません。"
            )
        return request is not None

    def shared_final_output_warning_confirmation_matches(self) -> bool:
        """Check the B3 warning acknowledgement without touching legacy save state."""
        state = self.ui_state
        context = state.final_output_state.current_context
        snapshot = self._shared_final_output_diagnostics
        if (
            state.is_busy
            or state.analysis_pending_rebuild
            or context is None
            or getattr(context, "lifecycle_signature", None)
            != self._capture_final_output_lifecycle_signature()
            or snapshot is None
            or snapshot.shared_final_output_identity != context.identity
        ):
            return False
        return shared_warning_confirmation_matches(
            snapshot,
            state.confirmed_shared_warning_fingerprint,
        )

    def _matches_current_shared_final_output_binding(
        self,
        requested_binding: str | None,
        *,
        coalescing_token: int | None = None,
    ) -> bool:
        if self.ui_state.output_edit_draft_dirty:
            return requested_binding is None
        context = self.ui_state.final_output_state.current_context
        if context is None:
            if requested_binding is None:
                return True
            active_gesture = self.right_pane._selected_editor_active_gesture
            return (
                coalescing_token is not None
                and active_gesture is not None
                and active_gesture.coalescing_token == coalescing_token
                and active_gesture.final_output_binding == requested_binding
            )
        identity = getattr(context, "identity", None)
        return (
            identity is not None
            and requested_binding == identity.binding_digest
            and getattr(context, "lifecycle_signature", None)
            == self._capture_final_output_lifecycle_signature()
        )

    def _on_apply_output_edits(self, event) -> None:
        event.Skip()
        state = self.ui_state
        if self._pending_output_apply is not None:
            self._pending_output_apply["cancelled"] = True
            self._final_output_sync_coordinator.cancel(
                self._pending_output_apply["request"]
            )
            state.output_edit_apply_status = "適用結果を破棄しています…"
            self.param_panel.btn_apply_output_edits.Enable(False)
            self.param_panel.set_output_edit_status(
                state.output_edit_apply_status
            )
            return
        if (
            state.is_busy
            or self._pending_selected_event_projection is not None
            or not state.output_edit_draft_dirty
            or state.output_edit_draft_error is not None
            or not state.analysis_result_valid
            or state.analysis_pending_rebuild
            or self._selected_event_editor_has_uncommitted_input()
            or self._pending_output_apply is not None
        ):
            return
        state.finish_current_output_edit_coalescing()
        draft_output = state.current_output_edit_state
        draft_plan = self._current_output_edit_draft_timing_plan()
        draft_profile = state.draft_model_profile_state
        if draft_output is None or draft_plan is None:
            self.param_panel.set_output_edit_status("変更を適用できません。解析結果を確認してください。")
            return
        base_input = self._build_base_timing_plan_input_for_plan(
            draft_plan,
            generation_state=draft_output.generation_state,
        )
        if base_input is None or not self._rebase_output_edit_draft(base_input):
            self.param_panel.set_output_edit_status("編集内容を解析イベントへ対応付けできません。")
            return
        draft_output = state.current_output_edit_state
        history = state.output_edit_history_state
        if draft_output is None or history is None:
            self.param_panel.set_output_edit_status("編集履歴を利用できません。")
            return
        operation_handle = self._begin_debug_operation(
            "output_edit_apply",
            payload={
                "source_revision": state.output_edit_source_revision,
                "draft_revision": state.output_edit_draft_revision,
            },
            entry="parameter_panel",
        )
        try:
            candidate_identity = build_base_plan_identity(base_input)
            if draft_output.adjustment_snapshot.base_plan_identity != candidate_identity:
                raise AdjustmentContractError("draft adjustment identity differs from apply base")
            candidate_lifecycle = copy.deepcopy(state.final_output_state)
            accepted_origin = candidate_lifecycle.accepted_origin
            if accepted_origin is None:
                raise AdjustmentContractError("accepted analysis origin is unavailable")
            candidate_lifecycle.accepted_origin = replace(
                accepted_origin,
                base_plan_digest=candidate_identity.digest,
            )
            candidate_lifecycle.manual_snapshot = draft_output.adjustment_snapshot
            candidate_lifecycle.manual_snapshot_known = True
            candidate_lifecycle.manual_snapshot_base_digest = (
                candidate_identity.digest
            )
            candidate_lifecycle.manual_revision = (
                0 if candidate_lifecycle.manual_revision is None
                else candidate_lifecycle.manual_revision + 1
            )
            candidate_lifecycle.unavailable_reason = None
            candidate_lifecycle.invalidate_context()
            output_names = get_builtin_morph_name_set(
                draft_output.generation_state.resolved_morph_name_set_id
            ).output_names
            diagnostics_seed = capture_shared_output_diagnostics_seed(
                state,
                generation_state=draft_output.generation_state,
                timing_plan=draft_plan,
                adjustment_snapshot=draft_output.adjustment_snapshot,
                active_preset_display_name=self._active_preset_display_name,
                output_morph_names=output_names,
                projection_generation=self._diagnostics_projection_generation,
            )
            lifecycle_signature = self._capture_final_output_lifecycle_signature(
                output_state=draft_output,
                timing_plan=draft_plan,
                model_profile_state=draft_profile,
            )
            request = request_shared_final_output(
                lifecycle=candidate_lifecycle,
                coordinator=self._final_output_sync_coordinator,
                input_mode=state.input_mode,
                base_input=base_input,
                adjustment_snapshot=draft_output.adjustment_snapshot,
                effective_plan=None,
                resolved_profile_id=draft_profile.active_model_profile_id,
                output_morph_names=output_names,
                source_audio_path=state.selected_wav_path,
                analysis_wav_path=(
                    None
                    if state.selected_analysis_wav is None
                    else getattr(state.selected_analysis_wav, "analysis_wav_path", None)
                ),
                text_path=state.selected_text_path,
                analysis_result_valid=state.analysis_result_valid,
                analysis_pending_rebuild=state.analysis_pending_rebuild,
                is_busy=False,
                lifecycle_signature=lifecycle_signature,
                diagnostics_seed=diagnostics_seed,
                transition_evaluation_request=self._transition_evaluation_request,
                default_transition_selection=self._current_default_transition_selection(),
                cleanup_evaluation_request=self._cleanup_evaluation_request,
                default_cleanup_selection=self._current_default_cleanup_selection(),
                resolve_effective_plan_in_worker=True,
                transition_acoustic_snapshot=(
                    getattr(state.current_timing_plan, "transition_acoustic_snapshot", None)
                    if (
                        self._transition_evaluation_request is not None
                        or self._bounded_candidate_enabled()
                    )
                    else None
                ),
            )
        except (AdjustmentContractError, AttributeError, TypeError, ValueError, RuntimeError):
            request = None
        if request is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="apply_request_unavailable",
            )
            self.param_panel.set_output_edit_status("変更を適用できませんでした。編集内容は保持されています。")
            self.right_pane.set_info_text("共有最終出力を開始できませんでした。編集内容は保持されています。")
            return
        self._pending_output_apply = {
            "request": request,
            "lifecycle": candidate_lifecycle,
            "output_state": draft_output,
            "timing_plan": draft_plan,
            "model_profile_state": draft_profile,
            "history": history,
            "source_revision": state.output_edit_source_revision,
            "draft_revision": state.output_edit_draft_revision,
            "previous_status_key": (
                StatusKey.ANALYSIS_READY
                if state.status_key == StatusKey.BUSY
                else state.status_key
            ),
            "operation_handle": operation_handle,
            "cancelled": False,
        }
        self._latest_shared_final_output_request = request
        state.output_edit_apply_status = "変更を適用中…"
        state.set_busy(True, preserve_final_output_context=True)
        self.sync_ui_state(adjustment_only=True)
        self.param_panel.btn_apply_output_edits.SetLabel("適用結果を破棄")
        self.param_panel.btn_apply_output_edits.Enable(True)
        self.param_panel.set_output_edit_status("変更を適用中…")
        self.start_output_edit_progress()
        self.right_pane.set_info_text("変更を適用中です。")

    def _finish_output_edit_apply(self, request, result) -> None:
        pending = self._pending_output_apply
        if pending is None or pending.get("request") != request:
            return
        state = self.ui_state
        same_draft = (
            pending.get("source_revision") == state.output_edit_source_revision
            and pending.get("draft_revision") == state.output_edit_draft_revision
        )
        lifecycle = pending.get("lifecycle")
        try:
            current_apply_signature = self._capture_final_output_lifecycle_signature(
                output_state=pending.get("output_state"),
                timing_plan=pending.get("timing_plan"),
                model_profile_state=pending.get("model_profile_state"),
            )
        except (AttributeError, TypeError, ValueError):
            current_apply_signature = None
        was_cancelled = bool(pending.get("cancelled"))
        lifecycle_signature_matches = (
            current_apply_signature == request.snapshot.lifecycle_signature
        )
        result_status = getattr(result, "status", None)
        result_context_present = getattr(result, "context", None) is not None
        result_preview_present = getattr(result, "preview_data", None) is not None
        result_diagnostics_valid = isinstance(
            getattr(result, "diagnostics_snapshot", None),
            OutputDiagnosticsSnapshot,
        )
        result_issues = getattr(result, "issues", ())
        first_issue = (
            result_issues[0]
            if isinstance(result_issues, (tuple, list)) and result_issues
            else None
        )
        apply_diagnostic_payload = {
            "same_draft": same_draft,
            "cancelled": was_cancelled,
            "lifecycle_signature_matches": lifecycle_signature_matches,
            "result_status": result_status,
            "result_context_present": result_context_present,
            "result_preview_present": result_preview_present,
            "result_diagnostics_valid": result_diagnostics_valid,
            "issue_count": (
                len(result_issues)
                if isinstance(result_issues, (tuple, list))
                else None
            ),
            "issue_reason_code": getattr(first_issue, "reason_code", None),
            "issue_stage": getattr(first_issue, "stage", None),
        }
        acceptance_preconditions = bool(
            same_draft
            and not was_cancelled
            and lifecycle_signature_matches
            and result_status == "valid"
            and result_context_present
            and result_preview_present
            and result_diagnostics_valid
            and lifecycle is not None
        )
        shared_result_accepted = bool(
            acceptance_preconditions
            and apply_shared_final_output_result(
                lifecycle=lifecycle,
                request=request,
                result=result,
                current_lifecycle_signature=current_apply_signature,
            )
        )
        apply_diagnostic_payload["shared_result_accepted"] = (
            shared_result_accepted if acceptance_preconditions else None
        )
        accepted = acceptance_preconditions and shared_result_accepted
        if was_cancelled:
            apply_failure_reason = "output_edit_apply_discarded"
        elif not same_draft:
            apply_failure_reason = "output_edit_apply_stale"
        elif not lifecycle_signature_matches:
            apply_failure_reason = "output_edit_lifecycle_signature_mismatch"
        elif result_status != "valid":
            apply_failure_reason = (
                f"output_edit_result_{result_status}"
                if result_status in {"invalid", "unavailable", "stale"}
                else "output_edit_result_status_unknown"
            )
        elif not result_context_present:
            apply_failure_reason = "output_edit_result_context_missing"
        elif not result_preview_present:
            apply_failure_reason = "output_edit_result_preview_missing"
        elif not result_diagnostics_valid:
            apply_failure_reason = "output_edit_result_diagnostics_invalid"
        elif lifecycle is None:
            apply_failure_reason = "output_edit_result_lifecycle_missing"
        else:
            apply_failure_reason = "output_edit_result_contract_rejected"
        if accepted:
            state.final_output_state = lifecycle
            state.current_timing_plan = pending["timing_plan"]
            output_state = pending["output_state"]
            state.generation_state = output_state.generation_state
            state.resolved_morph_upper_limit = output_state.morph_upper_limit
            state.model_profile_state = pending["model_profile_state"]
            state.output_edit_history_state = pending["history"]
            state._sync_legacy_adjustment_history()
            state.set_busy(False, preserve_final_output_context=True)
            if state.status_key == StatusKey.BUSY:
                state.status_key = pending.get("previous_status_key", StatusKey.IDLE)
            state.clear_output_edit_draft()
            state.initialize_output_edit_draft_baseline()
            if state.selected_source_event_index is not None:
                state.selected_base_plan_identity_digest = output_state.base_plan_identity.digest
            self._shared_final_output_diagnostics = result.diagnostics_snapshot
            duration_sec = self._selected_audio_duration_sec() or 0.0
            self._remember_accepted_output_preview(
                result.context,
                result.preview_data,
                duration_sec,
            )
            self.placeholder_container.set_identity_aware_preview_data(
                result.preview_data,
                duration_sec,
                result.context.input_identity.base_plan_digest,
                final_output_binding=result.context.identity.binding_digest,
            )
            preview_model = self.placeholder_container.pnl_preview.model
            if (
                state.selected_source_event_index is not None
                and preview_model.find_event_hit_region(
                    state.selected_source_event_index
                ) is not None
            ):
                self.placeholder_container.set_selected_source_event_index(
                    state.selected_source_event_index
                )
            else:
                state.clear_selection()
            self.right_pane.set_info_snapshot(result.diagnostics_snapshot)
            self.right_pane.set_warning_snapshot(result.diagnostics_snapshot)
            self._update_cleanup_event_choices(result.context)
            self._selected_preset_id = state.generation_state.active_preset_id
            self._selected_model_profile_id = state.model_profile_state.active_model_profile_id
            self._project_generation_controls()
            if self.controller:
                self.controller.request_settings_save()
            self.param_panel.set_output_edit_status("")
            self._finish_debug_operation(
                pending.get("operation_handle"),
                "completed",
                reason_code="output_edit_apply_succeeded",
                payload=apply_diagnostic_payload,
            )
        else:
            state.set_busy(False, preserve_final_output_context=True)
            if state.status_key == StatusKey.BUSY:
                state.status_key = pending.get("previous_status_key", StatusKey.IDLE)
            state.output_edit_apply_status = (
                "適用結果を破棄しました。編集内容は保持されています。"
                if was_cancelled
                else "適用に失敗しました。編集内容は保持されています。"
            )
            self.param_panel.set_output_edit_status(
                state.output_edit_apply_status
            )
            self.right_pane.set_info_text(
                state.output_edit_apply_status
                if was_cancelled
                else "変更を適用できませんでした。編集内容を確認して再試行してください。"
            )
            self._finish_debug_operation(
                pending.get("operation_handle"),
                "cancelled" if was_cancelled else "failed" if same_draft else "ignored",
                reason_code=apply_failure_reason,
                payload=apply_diagnostic_payload,
            )
        effective_plan_hint = None
        if accepted:
            legacy_context = getattr(
                getattr(result.context, "issuer_context", None),
                "legacy_context",
                None,
            )
            candidate_plan = getattr(
                legacy_context,
                "effective_plan_snapshot",
                None,
            )
            if isinstance(candidate_plan, EffectiveShapePlan):
                effective_plan_hint = candidate_plan
        self._pending_output_apply = None
        self.stop_output_edit_progress()
        if self._latest_shared_final_output_request == request:
            self._latest_shared_final_output_request = None
        self.sync_ui_state(effective_plan_hint=effective_plan_hint)

    def _on_shared_final_output_result(
        self,
        request: FinalOutputRequest,
        result,
    ) -> None:
        if request == self._latest_shared_final_output_request:
            self._latest_shared_final_output_request = None
        pending_apply = self._pending_output_apply
        if pending_apply is not None and pending_apply.get("request") == request:
            self._finish_output_edit_apply(request, result)
            return
        if pending_apply is not None:
            lifecycle = self.ui_state.final_output_state
            current_signature = self._capture_final_output_lifecycle_signature()
            if (
                result.status == "valid"
                and result.context is not None
                and request.snapshot.lifecycle_signature == current_signature
                and lifecycle.is_current_request(
                    request.snapshot.ticket,
                    request.snapshot.lifecycle_epoch,
                )
            ):
                apply_shared_final_output_result(
                    lifecycle=lifecycle,
                    request=request,
                    result=result,
                    current_lifecycle_signature=current_signature,
                )
            return
        if self.ui_state.output_edit_draft_dirty:
            lifecycle = self.ui_state.final_output_state
            current_signature = self._capture_final_output_lifecycle_signature()
            if (
                result.status == "valid"
                and result.context is not None
                and request.snapshot.lifecycle_signature == current_signature
                and lifecycle.is_current_request(
                    request.snapshot.ticket,
                    request.snapshot.lifecycle_epoch,
                )
            ):
                apply_shared_final_output_result(
                    lifecycle=lifecycle,
                    request=request,
                    result=result,
                    current_lifecycle_signature=current_signature,
                )
            return
        if result.status != "valid" or result.context is None:
            lifecycle = self.ui_state.final_output_state
            if (
                lifecycle.is_current_request(
                    request.snapshot.ticket,
                    request.snapshot.lifecycle_epoch,
                )
                and request.snapshot.lifecycle_signature
                == self._capture_final_output_lifecycle_signature()
            ):
                detail = ", ".join(
                    issue.reason_code for issue in result.issues
                ) or result.status
                self._clear_shared_final_output_view(
                    "共有最終出力を生成できませんでした。"
                )
                if isinstance(result.diagnostics_snapshot, OutputDiagnosticsSnapshot):
                    self.right_pane.set_info_snapshot(result.diagnostics_snapshot)
                    self.right_pane.set_warning_snapshot(result.diagnostics_snapshot)
                else:
                    self.right_pane.set_info_text(
                        f"共有最終出力を利用できません: {detail}"
                    )
                self.btn_save_vmd.Enable(False)
                self.mi_vmd_save.Enable(False)
                self.mi_diagnostic_report_save.Enable(False)
                self.mi_mmd_delivery_export.Enable(False)
            return
        context = result.context
        current_signature = self._capture_final_output_lifecycle_signature()
        if (
            request.snapshot.lifecycle_signature != current_signature
            or not self.ui_state.final_output_state.is_current_request(
                request.snapshot.ticket,
                request.snapshot.lifecycle_epoch,
            )
        ):
            if self.ui_state.final_output_state.is_current_request(
                request.snapshot.ticket,
                request.snapshot.lifecycle_epoch,
            ):
                self.ui_state.final_output_state.invalidate_context()
                self._clear_shared_final_output_view(
                    "共有最終出力の要求時状態が変わったため、結果を破棄しました。"
                )
            return
        preview_data = result.preview_data
        diagnostics_snapshot = result.diagnostics_snapshot
        if (
            preview_data is None
            or not isinstance(diagnostics_snapshot, OutputDiagnosticsSnapshot)
        ):
            self.ui_state.final_output_state.invalidate_context()
            self._clear_shared_final_output_view(
                "共有最終出力を生成できませんでした。"
            )
            return
        if not apply_shared_final_output_result(
            lifecycle=self.ui_state.final_output_state,
            request=request,
            result=result,
            current_lifecycle_signature=self._capture_final_output_lifecycle_signature(),
        ):
            if self.ui_state.final_output_state.is_current_request(
                request.snapshot.ticket,
                request.snapshot.lifecycle_epoch,
            ):
                self.ui_state.final_output_state.invalidate_context()
                self._clear_shared_final_output_view(
                    "共有最終出力を現在条件で採用できません。"
                )
            return
        self._shared_final_output_diagnostics = diagnostics_snapshot
        duration_sec = self._selected_audio_duration_sec() or 0.0
        self._remember_accepted_output_preview(
            context,
            preview_data,
            duration_sec,
        )
        try:
            self.placeholder_container.set_identity_aware_preview_data(
                preview_data,
                duration_sec,
                context.input_identity.base_plan_digest,
                final_output_binding=context.identity.binding_digest,
            )
            preview_model = self.placeholder_container.pnl_preview.model
            selected_index = self.ui_state.selected_source_event_index
            if (
                selected_index is not None
                and self.ui_state.selected_base_plan_identity_digest
                == context.input_identity.base_plan_digest
                and preview_model.find_event_hit_region(selected_index) is not None
            ):
                self.placeholder_container.set_selected_source_event_index(
                    selected_index
                )
            self.right_pane.set_info_snapshot(
                diagnostics_snapshot,
                transition_label=(
                    "自動整理：比較候補"
                    if context.cleanup_binding is not None
                    else "自動母音遷移"
                    if context.default_selection is not None
                    else "候補遷移"
                ),
            )
            self.right_pane.set_warning_snapshot(diagnostics_snapshot)
            self.update_action_states(diagnostics_snapshot)
            self.update_selected_event_display()
            self._update_cleanup_event_choices(context)
            self.placeholder_container.Refresh()
        except Exception:
            self.ui_state.final_output_state.invalidate_context()
            self._clear_shared_final_output_view(
                "共有最終出力の表示を更新できませんでした。"
            )

    def _update_cleanup_event_choices(self, context) -> None:
        cleanup = getattr(context, "cleanup_binding", None)
        if cleanup is None:
            self.right_pane.clear_cleanup_event_choices()
            return
        affected: dict[int, set[str]] = {}
        if cleanup.event_plan is not None:
            for decision in cleanup.event_plan.decisions:
                if decision.action != "suppress_event":
                    continue
                for index in decision.source_event_indices:
                    affected.setdefault(index, set()).add("イベント寄与を整理")
        if cleanup.reduction_plan is not None:
            for removal in cleanup.reduction_plan.removals:
                for index in removal.point.source_event_indices:
                    affected.setdefault(index, set()).add("キーを削減")
        source_events = {item.base_event_index: item for item in context.source_events}
        choices: list[tuple[str, int]] = []
        for index in sorted(affected):
            event = source_events.get(index)
            if event is None:
                continue
            reasons = "・".join(sorted(affected[index]))
            choices.append((
                f"No.{index + 1} / {event.vowel} / {event.start_frame}–{event.end_frame}f（{reasons}）",
                index,
            ))
        self.right_pane.set_cleanup_event_choices(
            binding_digest=context.identity.binding_digest,
            ticket=context.ticket,
            lifecycle_epoch=context.lifecycle_epoch,
            items=tuple(choices),
            busy=self.ui_state.is_busy or self._analysis_info_in_progress,
        )

    def _on_cleanup_event_selection_request(
        self, request: CleanupEventSelectionRequest
    ) -> None:
        state = self.ui_state
        context = state.final_output_state.current_context
        if (
            not isinstance(request, CleanupEventSelectionRequest)
            or context is None
            or context.cleanup_binding is None
            or state.is_busy
            or self._analysis_info_in_progress
            or self._selected_event_editor_has_uncommitted_input()
            or self.right_pane._selected_editor_active_gesture is not None
            or request.binding_digest != context.identity.binding_digest
            or request.ticket != context.ticket
            or request.lifecycle_epoch != context.lifecycle_epoch
            or context.lifecycle_signature != self._capture_final_output_lifecycle_signature()
            or not self._matches_current_shared_final_output_binding(request.binding_digest)
        ):
            return
        event = next(
            (item for item in context.source_events if item.base_event_index == request.base_event_index),
            None,
        )
        preview = self.placeholder_container.pnl_preview.model
        if (
            event is None
            or not preview.is_valid
            or preview.final_output_binding != request.binding_digest
            or preview.find_event_hit_region(request.base_event_index) is None
        ):
            return
        base_digest = context.input_identity.base_plan_digest
        valid_indices = tuple(item.base_event_index for item in context.source_events)
        if not state.commit_selected_source_event_index(
            request.base_event_index,
            requested_base_plan_identity_digest=base_digest,
            current_base_plan_identity_digest=base_digest,
            valid_base_event_indices=valid_indices,
        ):
            return
        self.placeholder_container.set_selected_source_event_index(request.base_event_index)
        self.placeholder_container.pnl_preview.set_playback_position_sec(event.peak_frame / 30.0)
        self.update_selected_event_display()
        self.right_pane.show_selected_event_tab()

    def _on_closure_restriction_selection(self, binding: str, target) -> None:
        context = self.ui_state.final_output_state.current_context
        identity = getattr(context, "identity", None)
        if (
            identity is None
            or identity.binding_digest != binding
            or getattr(target, "restriction", None) is None
            or getattr(target, "event", None) is None
        ):
            return
        if getattr(context, "lifecycle_signature", None) != (
            self._capture_final_output_lifecycle_signature()
        ):
            return
        event = target.event
        valid_indices = tuple(
            region.base_event_index
            for region in self.placeholder_container.pnl_preview.model.get_event_hit_regions()
        )
        if event.base_event_index not in valid_indices:
            return
        digest = context.input_identity.base_plan_digest
        self._finish_current_adjustment_gesture()
        committed = self.ui_state.commit_selected_source_event_index(
            event.base_event_index,
            requested_base_plan_identity_digest=digest,
            current_base_plan_identity_digest=digest,
            valid_base_event_indices=valid_indices,
        )
        if not committed:
            return
        self.placeholder_container.set_selected_source_event_index(
            event.base_event_index
        )
        self.placeholder_container.pnl_preview.set_playback_position_sec(
            target.restriction.frame_no / 30.0
        )
        self.update_selected_event_display()
        self.right_pane.show_selected_event_tab()

    def _sync_whisper_model_panel(
        self,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None = None,
    ) -> None:
        if diagnostics_snapshot is None:
            diagnostics_snapshot = self.ui_state.current_output_diagnostics_snapshot
        if diagnostics_snapshot is None:
            return
        summary = diagnostics_snapshot.whisper_summary
        items = tuple(
            WhisperModelPanelItem(
                model_key=item.model_key,
                display_name=item.display_name,
                size_bytes=item.size_bytes,
                vram_hint=item.vram_hint,
                speed_hint=item.speed_hint,
                recommended_use=item.recommended_use,
                artifact_status=item.availability_status,
                failure_code=item.availability_failure_code,
                manifest_identity=item.expected_manifest_identity,
                expected_manifest_identity=item.expected_manifest_identity,
            )
            for item in summary.models
        )
        selected_model_key = summary.selected_model_key or "small"
        active_model_key = summary.active_model_key or "small"
        self.right_pane.set_whisper_model_panel_state(
            WhisperModelPanelState(
                items=items,
                selected_model_key=selected_model_key,
                active_model_key=active_model_key,
                active_manifest_identity=summary.active_manifest_identity or "",
                storage_root_display=summary.storage_location_display,
                availability_scan_status=summary.availability_scan_status,
                availability_scan_failure_code=summary.availability_scan_failure_code,
                notice=summary.safe_failure_notice,
                busy=summary.application_busy,
                management_busy=summary.management_busy,
                management_operation=summary.management_operation,
                management_phase=summary.management_phase,
                management_job_id=summary.management_job_id,
                management_model_key=summary.management_model_key,
                management_received_bytes=summary.management_received_bytes,
                management_expected_bytes=summary.management_expected_bytes,
                management_failure_code=summary.management_failure_code,
                management_failure_detail=summary.safe_failure_notice or None,
                management_cleanup_status=summary.management_cleanup_status,
                active_config_status=summary.active_config_status,
                panel_revision=summary.panel_revision,
                loaded_model_key=summary.loaded_model_key,
                loaded_manifest_identity=summary.loaded_manifest_identity,
                analysis_model_key=summary.analysis_model_key,
                analysis_manifest_identity=summary.analysis_manifest_identity,
                analysis_identity_status=summary.analysis_identity_status,
                runtime_identity_status=summary.runtime_identity_status,
                package_version=summary.package_version,
                package_gate_status=summary.package_gate_status,
                active_config_reason=summary.active_config_reason,
            )
        )

    def _build_current_ui_sync_context(
        self,
        *,
        effective_plan_hint: EffectiveShapePlan | None = None,
    ) -> UiSyncContext | None:
        state = self.ui_state
        plan = state.current_timing_plan
        self._current_ui_sync_diagnostic = {
            "analysis_state": self._debug_current_analysis_state_payload(),
            "base_input": {
                "status": "not_evaluated",
                "failure_code": None,
                "timeline_count": (
                    len(getattr(plan, "timeline", ()) or ())
                    if plan is not None
                    else None
                ),
                "observations_present": (
                    bool(getattr(plan, "observations", None))
                    if plan is not None
                    else None
                ),
                "duration_candidates": [],
                "duration_status": "not_recorded",
                "duration_sec": None,
            },
            "sync_context": {
                "status": "not_evaluated",
                "failure_code": None,
                "exception_type": None,
            },
            "failure_context": _debug_success_failure_context(),
            "sync_inputs": {
                "effective_plan_hint": (
                    "present" if effective_plan_hint is not None else "absent"
                ),
                "cache_state": "not_evaluated",
                "adjustment_snapshot": (
                    "present"
                    if state.current_adjustment_snapshot is not None
                    else "absent"
                ),
                "adjustment_count": len(
                    getattr(state.current_adjustment_snapshot, "adjustments", ()) or ()
                ),
                "output_edit_state": (
                    "present"
                    if state.current_output_edit_state is not None
                    else "absent"
                ),
                "base_identity_check": "not_evaluated",
                "shape_parameters_check": "not_evaluated",
            },
        }
        debug_trace = self._debug_trace_for_current_projection()
        resolver_diagnostics = (
            ResolverDiagnosticsCollector(enabled=True)
            if debug_trace is not None
            else None
        )
        if resolver_diagnostics is not None:
            self._current_ui_sync_diagnostic[
                "resolver_diagnostics"
            ] = resolver_diagnostics.snapshot()
        if (
            not state.analysis_result_valid
            or state.analysis_pending_rebuild
            or state.current_timing_plan is None
        ):
            self._current_ui_sync_context = None
            self._current_ui_sync_output_state = None
            self._current_ui_sync_failure_reason = "analysis_state_unavailable"
            return None
        base_input = self._build_current_base_timing_plan_input()
        if base_input is None:
            self._current_ui_sync_context = None
            self._current_ui_sync_output_state = None
            self._current_ui_sync_failure_reason = "base_input_unavailable"
            self._current_ui_sync_diagnostic["failure_context"] = {
                "phase": "base_input_build",
                "domain": "base_input",
                "code": "base_input_unavailable",
                "exception_type": "not_applicable",
                "field_code": "not_applicable",
                "event_index": "not_applicable",
                "source_event_index": "not_applicable",
                "index_status": "not_applicable",
                "observed_stage": "ui_sync_context",
            }
            duration_diagnostic = dict(self._last_duration_selection_diagnostic)
            plan = state.current_timing_plan
            if plan is None:
                base_failure_code = "plan_missing"
            elif duration_diagnostic.get("status") == "unavailable":
                base_failure_code = "duration_unavailable"
            else:
                base_failure_code = "base_input_contract_error"
            self._current_ui_sync_diagnostic["base_input"] = {
                "status": "unavailable",
                "failure_code": base_failure_code,
                "timeline_count": (
                    len(getattr(plan, "timeline", ()) or ())
                    if plan is not None
                    else None
                ),
                "observations_present": (
                    bool(getattr(plan, "observations", None))
                    if plan is not None
                    else None
                ),
                "duration_candidates": duration_diagnostic.get(
                    "candidates", []
                ),
                "duration_status": duration_diagnostic.get(
                    "status", "not_recorded"
                ),
                "duration_sec": duration_diagnostic.get(
                    "selected_duration_sec"
                ),
            }
            self._current_ui_sync_diagnostic["sync_context"] = {
                "status": "unavailable",
                "failure_code": "base_input_unavailable",
                "exception_type": None,
            }
            return None
        duration_diagnostic = dict(self._last_duration_selection_diagnostic)
        self._current_ui_sync_diagnostic["base_input"] = {
            "status": "available",
            "failure_code": None,
            "timeline_count": len(base_input.timeline),
            "observations_present": base_input.observations is not None,
            "duration_candidates": duration_diagnostic.get("candidates", []),
            "duration_status": duration_diagnostic.get(
                "status", "not_recorded"
            ),
            "duration_sec": duration_diagnostic.get("selected_duration_sec"),
        }
        if self._bounded_candidate_enabled():
            identity = build_base_plan_identity(base_input)
            snapshot = state.current_adjustment_snapshot
            if snapshot is None:
                snapshot = empty_adjustment_snapshot(identity)
                state.initialize_adjustment_history(snapshot,
                    expected_base_plan_identity_digest=identity.digest)
            elif snapshot.base_plan_identity != identity:
                self._current_ui_sync_failure_reason = "bounded_source_identity_mismatch"
                return None
            current = state.final_output_state.current_context
            effective = None
            default_selection = self._current_default_transition_selection()
            if (current is not None and current.transition_binding is not None
                    and (
                        (
                            self._transition_evaluation_request is not None
                            and current.transition_binding.evaluation_request == self._transition_evaluation_request
                        )
                        or (
                            self._transition_evaluation_request is None
                            and current.transition_binding.default_selection == default_selection
                        )
                    )
                    and current.issuer_context.legacy_context.base_input == base_input
                    and current.issuer_context.legacy_context.adjustment_snapshot == snapshot):
                effective = current.issuer_context.legacy_context.effective_plan_snapshot
            context = UiSyncContext(base_input, identity, effective)
            self._current_ui_sync_context = context
            self._current_ui_sync_failure_reason = None
            return context
        cached = self._current_ui_sync_context
        current_output_state = state.current_output_edit_state
        self._current_ui_sync_diagnostic["sync_inputs"]["cache_state"] = "miss"
        if effective_plan_hint is None and cached is not None:
            if (
                self._current_ui_sync_output_state == current_output_state
                and cached.base_input == base_input
                and cached.effective_plan.canonical_adjustment_snapshot
                == state.current_adjustment_snapshot
                and cached.effective_plan.shape_parameters
                == base_input.shape_parameters
            ):
                self._current_ui_sync_failure_reason = None
                self._current_ui_sync_diagnostic["sync_inputs"]["cache_state"] = "hit"
                self._current_ui_sync_diagnostic["failure_context"] = (
                    _debug_success_failure_context()
                )
                self._current_ui_sync_diagnostic["sync_context"] = {
                    "status": "available",
                    "failure_code": None,
                    "exception_type": None,
                }
                if resolver_diagnostics is not None:
                    resolver_diagnostics.start_attempt(
                        caller="ui_sync_context", plan_origin="cache"
                    )
                    resolver_diagnostics.mark_plan_origin("cache")
                    self._current_ui_sync_diagnostic[
                        "resolver_diagnostics"
                    ] = resolver_diagnostics.snapshot()
                return cached
        if effective_plan_hint is not None and resolver_diagnostics is not None:
            resolver_diagnostics.start_attempt(
                caller="ui_sync_context", plan_origin="hint"
            )
        try:
            context = build_ui_sync_context(
                base_input,
                state.current_adjustment_snapshot,
                effective_plan_hint=effective_plan_hint,
                diagnostics=resolver_diagnostics,
            )
        except (AdjustmentContractError, TypeError, ValueError) as error:
            self._current_ui_sync_context = None
            self._current_ui_sync_output_state = None
            self._current_ui_sync_failure_reason = (
                f"{type(error).__name__}: {error}"
            )
            self._current_ui_sync_diagnostic["failure_context"] = (
                _debug_failure_context_from_error(
                    error,
                    phase=(
                        "effective_plan_hint_validate"
                        if effective_plan_hint is not None
                        else "effective_plan_resolve"
                    ),
                )
            )
            field_code = getattr(error, "safe_field_code", None)
            if field_code == "base_plan_identity":
                self._current_ui_sync_diagnostic["sync_inputs"][
                    "base_identity_check"
                ] = "invalid"
            elif field_code == "shape_parameters":
                self._current_ui_sync_diagnostic["sync_inputs"][
                    "shape_parameters_check"
                ] = "invalid"
            self._current_ui_sync_diagnostic["sync_context"] = {
                "status": "unavailable",
                "failure_code": "sync_context_build_failed",
                "exception_type": type(error).__name__,
            }
            if resolver_diagnostics is not None:
                self._current_ui_sync_diagnostic[
                    "resolver_diagnostics"
                ] = resolver_diagnostics.snapshot()
            return None
        if state.output_edit_history_state is None:
            state.initialize_adjustment_history(
                context.effective_plan.canonical_adjustment_snapshot,
                expected_base_plan_identity_digest=(
                    context.base_plan_identity.digest
                ),
            )
        self._current_ui_sync_context = context
        self._current_ui_sync_output_state = state.current_output_edit_state
        self._current_ui_sync_failure_reason = None
        self._current_ui_sync_diagnostic["failure_context"] = (
            _debug_success_failure_context()
        )
        if effective_plan_hint is not None:
            self._current_ui_sync_diagnostic["sync_inputs"][
                "base_identity_check"
            ] = "valid"
            self._current_ui_sync_diagnostic["sync_inputs"][
                "shape_parameters_check"
            ] = "valid"
        self._current_ui_sync_diagnostic["sync_context"] = {
            "status": "available",
            "failure_code": None,
            "exception_type": None,
        }
        if resolver_diagnostics is not None:
            if effective_plan_hint is not None:
                resolver_diagnostics.mark_plan_origin("hint")
            self._current_ui_sync_diagnostic[
                "resolver_diagnostics"
            ] = resolver_diagnostics.snapshot()
        return context

    def _build_pure_current_ui_sync_context(self) -> UiSyncContext | None:
        """Build the current effective context without changing UI/session state."""
        state = self.ui_state
        if (
            not state.analysis_result_valid
            or state.analysis_pending_rebuild
            or state.current_timing_plan is None
        ):
            return None
        base_input = self._build_current_base_timing_plan_input()
        if base_input is None:
            return None
        if self._bounded_candidate_enabled():
            current = self.ui_state.final_output_state.current_context
            if current is None or current.issuer_context.legacy_context.base_input != base_input:
                return None
            return UiSyncContext(base_input, build_base_plan_identity(base_input),
                                 current.issuer_context.legacy_context.effective_plan_snapshot)
        try:
            return build_ui_sync_context(
                base_input,
                state.current_adjustment_snapshot,
            )
        except (AdjustmentContractError, TypeError, ValueError):
            return None

    def prepare_current_effective_output(
        self,
        *,
        sync_context: UiSyncContext | None = None,
    ) -> tuple[str, EffectiveShapePlan | None, str | None]:
        """Resolve one immutable effective plan for diagnostics and VMD saving."""
        state = self.ui_state
        if (
            self._analysis_info_in_progress
            or not state.analysis_result_valid
            or state.analysis_pending_rebuild
            or not state.vmd_save_ready
        ):
            return "not_applicable", None, None

        if sync_context is None:
            sync_context = self._build_current_ui_sync_context()
        if sync_context is None:
            return (
                "invalid",
                None,
                self._current_ui_sync_failure_reason
                or "effective_shape_plan_unavailable",
            )
        if sync_context.effective_plan is None:
            return "not_applicable", None, None
        return "ready", sync_context.effective_plan, None

    def capture_current_delivery_state(
        self,
        *,
        ffmpeg_path: str | Path | None = None,
        confirmed_warning_save_state_fingerprint: str | None = None,
    ) -> DeliveryStartGateResult:
        """Capture a delivery candidate from the accepted shared final output."""
        state = self.ui_state
        source_audio_path = resolve_source_audio_path_from_ui_state(state)
        audio_probe = state.selected_audio_probe
        writer_parameters = VmdWriterParameters(
            vmd_model_name="AutoLipTool",
            closing_hold_frames=self.get_closing_hold_frames(),
            closing_softness_frames=self.get_closing_softness_frames(),
        )
        confirmed = (
            state.confirmed_shared_warning_fingerprint
            if confirmed_warning_save_state_fingerprint is None
            else confirmed_warning_save_state_fingerprint
        )
        shared_context = state.final_output_state.current_context
        shared_snapshot = getattr(self, "_shared_final_output_diagnostics", None)
        effective_shape_plan = (
            None
            if shared_context is None
            else shared_context.issuer_context.legacy_context.effective_plan_snapshot
        )
        output_morph_names = (
            None
            if shared_context is None
            else tuple(name for _, name in shared_context.input_identity.output_mapping)
        )
        lifecycle_signature = self._capture_final_output_lifecycle_signature()
        return evaluate_delivery_start_gate(
            effective_shape_plan=effective_shape_plan,
            diagnostics_snapshot=shared_snapshot,
            audio_probe=audio_probe,
            source_audio_path=source_audio_path,
            mmd_wav_spec=MMD_WAV_SPEC,
            ffmpeg_path=ffmpeg_path,
            writer_parameters=writer_parameters,
            output_morph_names=output_morph_names,
            effective_writer_input_state=(
                "ready" if shared_context is not None else "not_applicable"
            ),
            confirmed_warning_save_state_fingerprint=confirmed,
            application_busy=(
                state.is_busy
                or state.output_edit_draft_dirty
                or self._pending_selected_event_projection is not None
            ),
            analysis_in_progress=self._analysis_info_in_progress,
            projection_kind="shared_final_output",
            shared_final_output_context=shared_context,
            shared_lifecycle_signature=lifecycle_signature,
            expected_transition_input_digest=(
                state.final_output_state.expected_transition_input_digest
            ),
            expected_application_binding_digest=(
                state.final_output_state.expected_application_binding_digest
            ),
            expected_cleanup_input_digest=(
                getattr(
                    getattr(state.final_output_state.current_context, "input_identity", None),
                    "cleanup_input_digest",
                    None,
                )
            ),
            expected_cleanup_application_binding_digest=(
                state.final_output_state.expected_cleanup_application_binding_digest
            ),
        )

    def build_and_store_output_diagnostics_snapshot(
        self,
        *,
        effective_shape_plan: EffectiveShapePlan | None = None,
        effective_writer_input_state: str | None = None,
        effective_writer_input_failure_reason: str | None = None,
        output_morph_names: Sequence[str] | None = None,
    ) -> OutputDiagnosticsSnapshot:
        """Build diagnostics from the same effective plan used by VMD saving."""
        self.ui_state.refresh_input_mode()
        if effective_writer_input_state is None:
            (
                effective_writer_input_state,
                effective_shape_plan,
                effective_writer_input_failure_reason,
            ) = self.prepare_current_effective_output()
        self._diagnostics_projection_generation += 1
        snapshot = build_output_diagnostics_snapshot_from_ui_state(
            self.ui_state,
            closing_hold_frames=self.get_closing_hold_frames(),
            closing_softness_frames=self.get_closing_softness_frames(),
            analysis_in_progress=self._analysis_info_in_progress,
            effective_shape_plan=effective_shape_plan,
            effective_writer_input_state=effective_writer_input_state,
            effective_writer_input_failure_reason=(
                effective_writer_input_failure_reason
            ),
            generation_state=self.ui_state.generation_state,
            active_preset_display_name=self._active_preset_display_name,
            output_morph_names=(
                self._resolved_output_morph_names()
                if output_morph_names is None
                else output_morph_names
            ),
            projection_generation=self._diagnostics_projection_generation,
        )
        self.ui_state.current_output_diagnostics_snapshot = snapshot
        return snapshot

    def build_current_delivery_commit_snapshot(
        self,
    ) -> OutputDiagnosticsSnapshot | None:
        """Build a commit-time diagnostics snapshot without projection side effects."""
        sync_context = self._build_pure_current_ui_sync_context()
        if sync_context is None:
            return None
        writer_state, effective_plan, failure_reason = (
            self.prepare_current_effective_output(sync_context=sync_context)
        )
        if effective_plan is None and writer_state != "ready":
            return None
        return build_output_diagnostics_snapshot_from_ui_state(
            self.ui_state,
            closing_hold_frames=self.get_closing_hold_frames(),
            closing_softness_frames=self.get_closing_softness_frames(),
            analysis_in_progress=self._analysis_info_in_progress,
            effective_shape_plan=effective_plan,
            effective_writer_input_state=writer_state,
            effective_writer_input_failure_reason=failure_reason,
            generation_state=self.ui_state.generation_state,
            active_preset_display_name=self._active_preset_display_name,
            output_morph_names=self._resolved_output_morph_names(),
            projection_generation=self._diagnostics_projection_generation,
        )

    def show_vmd_save_progress(
        self,
        operation_id: int,
        *,
        on_cancel: Callable[[], object],
        get_progress_state: Callable[[], ProgressState],
    ) -> bool:
        if self._vmd_save_progress_dialog is not None:
            return False
        dialog = VmdSaveProgressDialog(
            self,
            on_cancel=on_cancel,
            get_progress_state=get_progress_state,
        )
        self._vmd_save_progress_dialog = dialog
        self._vmd_save_progress_operation_id = operation_id
        dialog.show()
        return True

    def suspend_vmd_save_progress(self, operation_id: int) -> None:
        if self._vmd_save_progress_operation_id != operation_id:
            return
        if self._vmd_save_progress_dialog is not None:
            self._vmd_save_progress_dialog.suspend()

    def resume_vmd_save_progress(self, operation_id: int) -> None:
        if self._vmd_save_progress_operation_id != operation_id:
            return
        if self._vmd_save_progress_dialog is not None:
            self._vmd_save_progress_dialog.resume()

    def close_vmd_save_progress(self, operation_id: int) -> None:
        if self._vmd_save_progress_operation_id != operation_id:
            return
        dialog = self._vmd_save_progress_dialog
        self._vmd_save_progress_dialog = None
        self._vmd_save_progress_operation_id = None
        if dialog is not None:
            dialog.close()

    def update_vmd_save_action_states(self) -> None:
        snapshot = self._shared_final_output_diagnostics
        sync_context = self._current_ui_sync_context
        if snapshot is None or sync_context is None:
            return
        self.update_action_states(
            snapshot,
            sync_context=sync_context,
            busy_override=self.ui_state.is_busy,
        )

    def update_audio_worker_action_states(self) -> None:
        snapshot = self._shared_final_output_diagnostics
        sync_context = self._current_ui_sync_context
        if snapshot is not None and sync_context is not None:
            self.update_action_states(
                snapshot,
                sync_context=sync_context,
                busy_override=self.ui_state.is_busy,
            )
            return

        state = self.ui_state
        busy = state.is_busy
        self.btn_open_text.Enable(not busy)
        self.btn_open_wav.Enable(not busy)
        self.mi_workspace_reset.Enable(not busy)
        self.mi_text_open.Enable(not busy)
        self.mi_wav_open.Enable(not busy)

        for item in (
            self.mi_vmd_save,
            self.mi_diagnostic_report_save,
            self.mi_mmd_delivery_export,
            self.mi_adjustment_undo,
            self.mi_adjustment_redo,
            self.mi_adjustment_reset_selected,
            self.mi_adjustment_reset_all,
        ):
            item.Enable(False)

        self.param_panel.enable_inputs(
            not busy and state.draft_model_profile_state.active_model_profile_id is None
        )
        self.btn_process.Enable(state.analysis_start_ready and not busy)
        self.btn_save_vmd.Enable(False)
        transcription_edit_enabled = bool(
            state.input_mode == INPUT_MODE_VOICE_ONLY
            and state.transcription_text
            and not busy
        )
        self.info_panel.set_text_preview_editable(transcription_edit_enabled)
        self.info_panel.set_transcription_edit_controls_enabled(
            transcription_edit_enabled
        )
        self.btn_export_mmd_wav.Enable(state.mmd_wav_export_ready and not busy)
        self.btn_cancel_audio_worker.Enable(state.audio_worker_cancel_available)
        self._update_playback_action_states()

        self._update_zoom_action_states()

        self.mi_settings.Enable(False)
        self.mi_help.Enable(True)
        self.mi_about.Enable(True)

    def _update_playback_action_states(self, *, busy_override: bool | None = None) -> None:
        state = self.ui_state
        busy = bool(state.is_busy if busy_override is None else busy_override)
        self.btn_play.Enable(
            state.playback_ready and not busy and not state.is_playing
        )
        self.btn_pause.Enable(state.is_playing and not busy)
        self.btn_stop.Enable(state.playback_active)

    def sync_playback_controls(self) -> None:
        """Update transport button states without rebuilding unrelated UI."""
        self._update_playback_action_states()

    def _update_zoom_action_states(self) -> None:
        if self.controller:
            zoom_state = self.controller.get_zoom_action_state()
            self.btn_zoom_in.Enable(zoom_state["zoom_in"])
            self.btn_zoom_out.Enable(zoom_state["zoom_out"])
            self.btn_zoom_reset.Enable(zoom_state["zoom_reset"])
        else:
            self.btn_zoom_in.Enable(False)
            self.btn_zoom_out.Enable(False)
            self.btn_zoom_reset.Enable(False)

    def sync_zoom_controls(self) -> None:
        """Update Zoom button states without rebuilding unrelated UI."""
        self._update_zoom_action_states()

    def update_action_states(
        self,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None = None,
        *,
        sync_context: UiSyncContext | None = None,
        busy_override: bool | None = None,
    ):
        """
        [MS14-B2] UiState に基づき、UI コントロールの有効/無効を判定・反映する
        """
        state = self.ui_state
        draft_dirty = state.output_edit_draft_dirty
        busy = (
            busy_override
            if busy_override is not None
            else (
                diagnostics_snapshot.whisper_summary.application_busy
                if diagnostics_snapshot
                else state.is_busy
            )
        )
        shared_context = state.final_output_state.current_context
        shared_ready = bool(
            shared_context is not None
            and self._shared_final_output_diagnostics is not None
            and self._shared_final_output_diagnostics.shared_final_output_identity
            == shared_context.identity
            and getattr(shared_context, "lifecycle_signature", None)
            == self._capture_final_output_lifecycle_signature()
        )
        if sync_context is None:
            sync_context = self._build_current_ui_sync_context()
        if diagnostics_snapshot is None:
            writer_state, effective_plan, failure_reason = (
                self.prepare_current_effective_output(
                    sync_context=sync_context,
                )
            )
            diagnostics_snapshot = self.build_and_store_output_diagnostics_snapshot(
                effective_shape_plan=effective_plan,
                effective_writer_input_state=writer_state,
                effective_writer_input_failure_reason=failure_reason,
            )

        # --- 基本入力 (busy 中のみ lock) ---
        self.btn_open_text.Enable(not busy)
        self.btn_open_wav.Enable(not busy)

        self.mi_workspace_reset.Enable(not busy)
        self.mi_text_open.Enable(not busy)
        self.mi_wav_open.Enable(not busy)
        
        # recent menu slot (MS14-B2 lock対象)
        self.mi_text_open.Enable(not busy)
        self.mi_wav_open.Enable(not busy)
        self.mi_vmd_save.Enable(
            diagnostics_snapshot.saveability.vmd_save_allowed
            and not busy
            and shared_ready
            and not draft_dirty
        )
        source_audio_path = resolve_source_audio_path_from_ui_state(state)
        self.mi_diagnostic_report_save.Enable(
            not busy
            and shared_ready
            and not draft_dirty
            and source_audio_path is not None
            and bool(source_audio_path.stem)
        )
        self.mi_mmd_delivery_export.Enable(
            not busy
            and shared_ready
            and not draft_dirty
            and source_audio_path is not None
            and bool(source_audio_path.stem)
            and diagnostics_snapshot.saveability.vmd_save_allowed
        )

        snapshot = state.current_adjustment_snapshot
        adjustment_history_ready = bool(
            not busy
            and sync_context is not None
            and snapshot is not None
            and snapshot.base_plan_identity == sync_context.base_plan_identity
        )
        self.mi_adjustment_undo.Enable(
            adjustment_history_ready and state.can_undo_adjustment
        )
        self.mi_adjustment_redo.Enable(
            adjustment_history_ready and state.can_redo_adjustment
        )
        selected_adjustment_ready = bool(
            adjustment_history_ready
            and state.selected_source_event_index is not None
            and state.selected_base_plan_identity_digest
            == state.current_adjustment_snapshot.base_plan_identity.digest
            and any(
                adjustment.base_event_index
                == state.selected_source_event_index
                for adjustment in state.current_adjustment_snapshot.adjustments
            )
        )
        self.mi_adjustment_reset_selected.Enable(selected_adjustment_ready)
        self.mi_adjustment_reset_all.Enable(
            adjustment_history_ready and state.has_event_adjustments
        )
        
        # --- パラメータ入力 (busy / active profile時ロック) ---
        self.param_panel.enable_inputs(
            not busy and state.draft_model_profile_state.active_model_profile_id is None
        )
        self.param_panel.btn_apply_output_edits.Enable(
            draft_dirty
            and not busy
            and state.output_edit_draft_error is None
            and state.analysis_result_valid
            and not self._selected_event_editor_has_uncommitted_input()
        )

        # --- 解析実行 ---
        whisper_runtime_valid = (
            diagnostics_snapshot.whisper_summary.runtime_identity_status
            not in {"incomplete", "mismatch"}
        )
        can_analyze = state.analysis_start_ready and whisper_runtime_valid
        self.btn_process.Enable(can_analyze and not busy and not draft_dirty)

        # --- VMD 保存 ---
        self.btn_save_vmd.Enable(
            diagnostics_snapshot.saveability.vmd_save_allowed
            and not busy
            and shared_ready
            and not draft_dirty
        )

        # --- MS19-B5 書き起こし編集 ---
        transcription_edit_enabled = bool(
            not busy
            and diagnostics_snapshot.whisper_summary.transcription_edit_available
        )
        self.info_panel.set_text_preview_editable(transcription_edit_enabled)
        self.info_panel.set_transcription_edit_controls_enabled(transcription_edit_enabled)

        # --- MMD用WAV 出力 ---
        self.btn_export_mmd_wav.Enable(state.mmd_wav_export_ready and not busy)
        self.btn_cancel_audio_worker.Enable(state.audio_worker_cancel_available)

        self._update_playback_action_states(busy_override=busy)
        
        # [MS15-B5] Zoom UI の仮開放
        self._update_zoom_action_states()
        
        # 設定・ヘルプ
        self.mi_settings.Enable(False)
        self.mi_help.Enable(True)
        self.mi_about.Enable(True)

    def _reject_unapplied_output_edit(self) -> bool:
        if self._pending_selected_event_projection is not None:
            message = "選択イベントの編集表示を計算しています。完了後にもう一度操作してください。"
            self.right_pane.set_info_text(message)
            self.param_panel.set_output_edit_status("編集表示を更新中…")
            return True
        if not self.ui_state.output_edit_draft_dirty:
            return False
        message = "先に変更を適用するか、Undo / Redoで適用済みの内容へ戻してください。"
        self.right_pane.set_info_text(message)
        self.param_panel.set_output_edit_status("変更未適用")
        return True

    def _preset_store_items(self):
        if self.controller and hasattr(self.controller, "preset_store"):
            store = self.controller.preset_store
            return tuple(store.built_in_presets) + tuple(store.user_presets)
        return tuple(BUILTIN_PRESETS)

    def _sync_preset_panel(self) -> None:
        store = self.controller.preset_store if self.controller and hasattr(self.controller, "preset_store") else None
        items = tuple(
            PresetPanelItem(
                id=item.id,
                display_name=item.display_name,
                source=item.source,
                generation_settings=item.generation_settings,
            )
            for item in self._preset_store_items()
        )
        valid_ids = {item.id for item in items}
        active_state = (
            self.ui_state.current_output_edit_state.generation_state
            if self.ui_state.output_edit_draft_dirty
            and self.ui_state.current_output_edit_state is not None
            else self.ui_state.generation_state
        )
        active_id = active_state.active_preset_id
        active_display_name = self._active_preset_display_name
        if store is not None:
            resolution = store.resolve_active(
                active_state.generation_settings,
                active_id,
            )
            active_id = resolution.active_preset_id
            active_display_name = resolution.active_preset_display_name
            if active_id != active_state.active_preset_id:
                self._active_preset_display_name = active_display_name
        if not self._preset_selection_initialized:
            self._selected_preset_id = active_id if active_id in valid_ids else None
            self._preset_selection_initialized = True
        elif self.ui_state.output_edit_draft_dirty:
            self._selected_preset_id = active_id if active_id in valid_ids else None
        elif self._selected_preset_id is not None and self._selected_preset_id not in valid_ids:
            self._selected_preset_id = active_id if active_id in valid_ids else None

        load_error_code = None
        load_error_message = None
        mutation_available = True
        if store is not None:
            mutation_available = store.mutation_available
            load_result = store.last_load_result
            if load_result is not None and not load_result.mutation_available:
                load_error_code = load_result.error_code
                load_error_message = self._format_preset_load_error(load_result.error_code)

        signature = (
            tuple(
                (item.id, item.display_name, item.source, item.generation_settings)
                for item in items
            ),
            self._selected_preset_id,
            active_id,
            active_display_name,
            active_state.generation_settings,
            mutation_available,
            load_error_code,
            load_error_message,
        )
        if signature != self._preset_panel_signature:
            self._preset_panel_revision += 1
            self._preset_panel_signature = signature
        self.right_pane.set_preset_panel_state(
            PresetPanelState(
                items=items,
                selected_preset_id=self._selected_preset_id,
                active_preset_id=active_id,
                active_preset_display_name=active_display_name,
                active_generation_settings=active_state.generation_settings,
                mutation_available=mutation_available,
                load_error_code=load_error_code,
                load_error_message=load_error_message,
                busy=self.ui_state.is_busy,
                panel_revision=self._preset_panel_revision,
            )
        )

    def _profile_store_items(self):
        if self.controller and hasattr(self.controller, "profile_store"):
            return tuple(self.controller.profile_store.user_profiles)
        return ()

    def _sync_model_profile_panel(self) -> None:
        profile_store = (
            self.controller.profile_store
            if self.controller and hasattr(self.controller, "profile_store")
            else None
        )
        profiles = self._profile_store_items()
        preset_items = self._preset_store_items()
        preset_options = tuple(
            ModelProfilePresetOption(
                id=item.id,
                display_name=item.display_name,
                source=item.source,
                generation_settings=item.generation_settings,
            )
            for item in preset_items
        )
        preset_by_id = {item.id: item for item in preset_items}
        profile_items = []
        for profile in profiles:
            morph_name_set = get_builtin_morph_name_set(profile.morph_name_set_id)
            default_preset = preset_by_id.get(profile.default_preset_id)
            profile_items.append(
                ModelProfilePanelItem(
                    id=profile.id,
                    display_name=profile.display_name,
                    morph_name_set_id=profile.morph_name_set_id,
                    morph_name_set_display_name=morph_name_set.display_name,
                    output_names=tuple(morph_name_set.output_names),
                    morph_upper_limit=profile.morph_upper_limit,
                    generation_overrides=profile.generation_overrides,
                    default_preset_id=profile.default_preset_id,
                    default_preset_display_name=(
                        None if default_preset is None else default_preset.display_name
                    ),
                    default_preset_available=default_preset is not None,
                )
            )
        items = tuple(profile_items)
        valid_ids = {item.id for item in items}
        draft_profile_state = self.ui_state.draft_model_profile_state
        draft_generation_state = (
            self.ui_state.current_output_edit_state.generation_state
            if self.ui_state.output_edit_draft_dirty
            and self.ui_state.current_output_edit_state is not None
            else self.ui_state.generation_state
        )
        active_profile_id = draft_profile_state.active_model_profile_id
        if not self._model_profile_selection_initialized:
            self._selected_model_profile_id = (
                active_profile_id if active_profile_id in valid_ids else None
            )
            self._model_profile_selection_initialized = True
        elif self.ui_state.output_edit_draft_dirty:
            self._selected_model_profile_id = (
                active_profile_id if active_profile_id in valid_ids else None
            )
        elif self._selected_model_profile_id not in valid_ids and self._selected_model_profile_id is not None:
            self._selected_model_profile_id = (
                active_profile_id if active_profile_id in valid_ids else None
            )

        if active_profile_id is not None:
            self._sync_profile_display_names_from_state()
        active_profile_display_name = self.ui_state.active_model_profile_display_name
        active_baseline_id = (
            draft_profile_state.active_profile_baseline_preset_id
        )
        active_baseline = preset_by_id.get(active_baseline_id)
        active_preset_id = draft_generation_state.active_preset_id
        active_preset = preset_by_id.get(active_preset_id)
        active_morph_name_set = get_builtin_morph_name_set(
            draft_generation_state.resolved_morph_name_set_id
        )
        load_error_code = None
        load_error_message = None
        mutation_available = True
        if profile_store is not None:
            mutation_available = profile_store.mutation_available
            load_result = profile_store.last_load_result
            if load_result is not None and not load_result.mutation_available:
                load_error_code = load_result.error_code
                load_error_message = self._format_model_profile_load_error(
                    load_result.error_code
                )

        signature = (
            tuple(
                (
                    item.id,
                    item.display_name,
                    item.morph_name_set_id,
                    item.output_names,
                    item.morph_upper_limit,
                    item.generation_overrides,
                    item.default_preset_id,
                    item.default_preset_display_name,
                    item.default_preset_available,
                )
                for item in items
            ),
            tuple(
                (item.id, item.display_name, item.source, item.generation_settings)
                for item in preset_options
            ),
            self._selected_model_profile_id,
            active_profile_id,
            active_profile_display_name,
            active_preset_id,
            None if active_preset is None else active_preset.display_name,
            active_baseline_id,
            None if active_baseline is None else active_baseline.display_name,
            self.ui_state.model_profile_state.resolution_status.value,
            self.ui_state.model_profile_state.resolution_reason_code,
            self.ui_state.generation_state.generation_settings,
            self.ui_state.resolved_morph_upper_limit,
            active_morph_name_set.set_id,
            active_morph_name_set.output_names,
            mutation_available,
            load_error_code,
            load_error_message,
            self.ui_state.is_busy,
        )
        if signature != self._model_profile_panel_signature:
            self._model_profile_panel_revision += 1
            self._model_profile_panel_signature = signature
        self.right_pane.set_model_profile_panel_state(
            ModelProfilePanelState(
                items=items,
                preset_options=preset_options,
                selected_profile_id=self._selected_model_profile_id,
                active_profile_id=active_profile_id,
                active_profile_display_name=active_profile_display_name,
                active_preset_id=(
                    None
                    if active_profile_id is not None or active_preset is None
                    else active_preset.id
                ),
                active_preset_display_name=(
                    None
                    if active_profile_id is not None or active_preset is None
                    else active_preset.display_name
                ),
                active_baseline_preset_id=active_baseline_id,
                active_baseline_preset_display_name=(
                    None if active_baseline is None else active_baseline.display_name
                ),
                active_morph_name_set_id=active_morph_name_set.set_id,
                active_morph_name_set_display_name=active_morph_name_set.display_name,
                active_output_names=tuple(active_morph_name_set.output_names),
                active_generation_settings=self.ui_state.generation_state.generation_settings,
                active_morph_upper_limit=float(self.ui_state.resolved_morph_upper_limit),
                resolution_status=self.ui_state.model_profile_state.resolution_status.value,
                resolution_reason=self.ui_state.model_profile_state.resolution_reason_code,
                mutation_available=mutation_available,
                load_error_code=load_error_code,
                load_error_message=load_error_message,
                busy=self.ui_state.is_busy,
                panel_revision=self._model_profile_panel_revision,
            )
        )

    def _model_profile_request_is_current(
        self,
        expected_panel_revision: int,
        *,
        expected_editor_revision: int | None = None,
    ) -> bool:
        state = self.ui_state
        if state.is_busy or expected_panel_revision != self._model_profile_panel_revision:
            return False
        if (
            expected_editor_revision is not None
            and expected_editor_revision != state.selected_event_editor_revision
        ):
            return False
        if self._selected_event_editor_has_uncommitted_input():
            return False
        return True

    def _set_model_profile_notice(self, message: str) -> None:
        self.right_pane.set_model_profile_panel_notice(message)

    @staticmethod
    def _format_model_profile_load_error(error_code: str | None) -> str | None:
        messages = {
            "invalid_json": "profiles.jsonの形式が不正です。プロファイルなしで継続します。",
            "unsupported_schema": "profiles.jsonのschema versionに対応していません。プロファイルなしで継続します。",
            "invalid_schema": "profiles.jsonの内容が不正です。プロファイルなしで継続します。",
            "read_failed": "profiles.jsonを読み込めません。プロファイルなしで継続します。",
            "duplicate_id": "profiles.jsonに重複したIDがあります。プロファイルなしで継続します。",
            "duplicate_display_name": "profiles.jsonに重複した表示名があります。プロファイルなしで継続します。",
            "limit_exceeded": "profiles.jsonのプロファイル数が上限を超えています。プロファイルなしで継続します。",
        }
        return messages.get(error_code) if error_code else None

    @staticmethod
    def _format_model_profile_mutation_error(result) -> str:
        messages = {
            "invalid_input": "入力値を確認してください。",
            "duplicate_display_name": "同じ表示名のモデルプロファイルが既にあります。",
            "duplicate_id": "モデルプロファイルIDが重複しています。",
            "limit_exceeded": "モデルプロファイルは100件までです。",
            "profile_not_found": "対象のモデルプロファイルが見つかりません。",
            "preset_reference_not_found": "基準プリセットが見つかりません。",
            "active_profile_locked": "適用中のプロファイルは名前変更以外できません。",
            "store_not_loaded": "モデルプロファイルがまだ読み込まれていません。",
            "store_unavailable": "モデルプロファイルは現在変更できません。",
            "write_failed": "profiles.jsonの保存に失敗しました。現在の状態を保持します。",
            "replace_failed": "profiles.jsonの保存確定に失敗しました。現在の状態を保持します。",
        }
        return messages.get(result.error_code, "モデルプロファイルを変更できませんでした。")

    @staticmethod
    def _format_model_profile_apply_error(resolution) -> str:
        messages = {
            "profile_not_found": "選択したモデルプロファイルが見つかりません。",
            "profile_default_preset_not_found": "基準プリセットが見つからないため適用できません。",
            "preset_not_found": "選択したプリセットが見つかりません。",
            "invalid_input": "モデルプロファイルの入力を確認してください。",
        }
        return messages.get(
            getattr(resolution, "error_code", None),
            "モデルプロファイルを適用できませんでした。現在の状態を保持しています。",
        )

    def _preset_request_is_current(
        self,
        expected_panel_revision: int,
        *,
        expected_editor_revision: int | None = None,
    ) -> bool:
        state = self.ui_state
        if state.is_busy or expected_panel_revision != self._preset_panel_revision:
            return False
        if (
            expected_editor_revision is not None
            and expected_editor_revision != state.selected_event_editor_revision
        ):
            return False
        if self._selected_event_editor_has_uncommitted_input():
            return False
        return True

    def _set_preset_notice(self, message: str) -> None:
        self.right_pane.set_preset_panel_notice(message)

    @staticmethod
    def _format_preset_mutation_error(result) -> str:
        messages = {
            "invalid_input": "入力値を確認してください。",
            "duplicate_display_name": "同じ表示名のプリセットが既にあります。",
            "duplicate_id": "プリセットIDが重複しています。",
            "limit_exceeded": "ユーザープリセットは100件までです。",
            "preset_not_found": "対象のユーザープリセットが見つかりません。",
            "builtin_read_only": "組み込みプリセットは変更できません。",
            "write_failed": "プリセットの保存に失敗しました。ユーザー操作を確認してください。",
            "replace_failed": "プリセットの保存確定に失敗しました。ユーザー操作を確認してください。",
            "store_unavailable": "ユーザープリセットは現在変更できません。組み込みプリセットは利用できます。",
        }
        return messages.get(result.error_code, "プリセット操作に失敗しました。現在の状態を保持しています。")

    @staticmethod
    def _format_preset_load_error(error_code: str | None) -> str | None:
        messages = {
            "invalid_json": "presets.jsonの形式が不正です。組み込みプリセットを継続利用できます。",
            "unsupported_schema": "presets.jsonのschema versionに対応していません。組み込みプリセットを継続利用できます。",
            "invalid_schema": "presets.jsonの内容が不正です。組み込みプリセットを継続利用できます。",
            "read_failed": "presets.jsonを読み込めません。組み込みプリセットを継続利用できます。",
            "duplicate_id": "presets.jsonに重複したIDがあります。組み込みプリセットを継続利用できます。",
            "duplicate_display_name": "presets.jsonに重複した表示名があります。組み込みプリセットを継続利用できます。",
            "limit_exceeded": "presets.jsonのユーザープリセット数が上限を超えています。組み込みプリセットを継続利用できます。",
        }
        return messages.get(error_code) if error_code else None

    def _on_preset_select_request(self, request: PresetSelectRequest):
        if not isinstance(request, PresetSelectRequest):
            return
        operation_handle = self._begin_debug_operation(
            "generation_preset_select",
            payload={"preset_id": request.selected_preset_id},
            entry="preset_panel",
        )
        if self.ui_state.is_busy or request.expected_panel_revision != self._preset_panel_revision:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if self.ui_state.is_busy else "stale_panel_request"),
            )
            return
        valid_ids = {item.id for item in self._preset_store_items()}
        if request.selected_preset_id is not None and request.selected_preset_id not in valid_ids:
            self._set_preset_notice("選択したプリセットは現在利用できません。")
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="preset_unavailable",
            )
            return
        changed = request.selected_preset_id != self._selected_preset_id
        self._selected_preset_id = request.selected_preset_id
        self._set_preset_notice("")
        self._sync_preset_panel()
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "noop",
            reason_code="preset_selected" if changed else "preset_selection_unchanged",
            payload={"preset_id": request.selected_preset_id, "changed": changed},
        )

    def _on_preset_apply_request(self, request: PresetApplyRequest):
        if not isinstance(request, PresetApplyRequest):
            return
        if self._reject_unapplied_output_edit():
            return
        if not self._preset_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            return
        if request.preset_id != self._selected_preset_id:
            return
        preset = self.controller.lookup_generation_preset(request.preset_id) if self.controller else None
        if preset is None:
            self._set_preset_notice("選択したプリセットは現在利用できません。")
            self._sync_preset_panel()
            return
        current_output = self.ui_state.current_output_edit_state
        current = (
            current_output.generation_state
            if self.ui_state.output_edit_draft_dirty and current_output is not None
            else self.ui_state.generation_state
        )
        if (
            current.active_preset_id == preset.id
            and current.generation_settings == preset.generation_settings
        ):
            self._set_preset_notice("選択中のプリセットは既に適用されています。")
            self.controller.record_debug_operation_event(
                "generation_preset_apply",
                "noop",
                source="user",
                entry="preset_panel",
                payload={"preset_id": preset.id, "changed": False},
                reason_code="preset_already_active",
            )
            return
        if self.ui_state.model_profile_state.active_model_profile_id is not None:
            applied = self.apply_active_model_profile_preset(preset.id)
        else:
            applied = self.apply_preset_generation(
                preset.generation_settings,
                preset.id,
                preset.display_name,
            )
        if not applied:
            self._set_preset_notice("プリセットを適用できませんでした。現在の状態を保持しています。")
            return
        self._selected_preset_id = preset.id
        self._set_preset_notice("プリセットを適用しました。")
        self._sync_preset_panel()

    def _on_preset_create_request(self, request: PresetCreateRequest):
        if not isinstance(request, PresetCreateRequest):
            return
        operation_handle = self._begin_debug_operation(
            "generation_preset_create",
            payload={"setting": "generation_preset"},
            entry="preset_panel",
        )
        if not self._preset_request_is_current(request.expected_panel_revision):
            self._finish_debug_operation(
                operation_handle, "ignored", reason_code="stale_panel_request"
            )
            return
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="controller_unavailable"
            )
            return
        before_ids = {item.id for item in self.controller.preset_store.user_presets}
        result = self.controller.create_generation_preset(
            request.display_name,
            request.generation_settings,
        )
        if not result.succeeded:
            self._set_preset_notice(self._format_preset_mutation_error(result))
            self._sync_preset_panel()
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=getattr(result, "error_code", None) or "preset_create_rejected",
            )
            return
        created = next((item for item in result.user_presets if item.id not in before_ids), None)
        self._selected_preset_id = created.id if created is not None else self._selected_preset_id
        self._set_preset_notice("ユーザープリセットを作成しました。Applyで出力へ反映できます。")
        self._sync_preset_panel()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="preset_created",
            payload={"preset_id": getattr(created, "id", None), "changed": True},
        )

    def _normalize_active_preset_after_mutation(self) -> None:
        if self.controller is None:
            return
        store = self.controller.preset_store
        current = self.ui_state.generation_state
        previous_display_name = self._active_preset_display_name
        resolution = store.resolve_active(
            current.generation_settings,
            current.active_preset_id,
        )
        self._active_preset_display_name = resolution.active_preset_display_name
        if resolution.active_preset_id == current.active_preset_id:
            if self._active_preset_display_name != previous_display_name:
                self.sync_ui_state(adjustment_only=True)
            return

        def normalize_generation_state(generation_state):
            resolved = store.resolve_active(
                generation_state.generation_settings,
                generation_state.active_preset_id,
            )
            return GenerationState(
                generation_settings=resolved.generation_settings,
                active_preset_id=resolved.active_preset_id,
                resolved_morph_name_set_id=(
                    generation_state.resolved_morph_name_set_id
                ),
            )

        history = self.ui_state.output_edit_history_state
        if history is not None:
            if not self.ui_state.normalize_output_edit_history(normalize_generation_state):
                self._active_preset_display_name = previous_display_name
                return
        else:
            self.ui_state.generation_state = GenerationState(
                generation_settings=current.generation_settings,
                active_preset_id=None,
                resolved_morph_name_set_id=current.resolved_morph_name_set_id,
            )
        self._active_preset_display_name = None
        self.controller.request_settings_save()
        self.sync_ui_state(adjustment_only=True)

    def _on_preset_update_request(self, request: PresetUpdateRequest):
        if not isinstance(request, PresetUpdateRequest):
            return
        operation_handle = self._begin_debug_operation(
            "generation_preset_update",
            payload={"preset_id": request.preset_id},
            entry="preset_panel",
        )
        if not self._preset_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            self._finish_debug_operation(
                operation_handle, "ignored", reason_code="stale_panel_request"
            )
            return
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="controller_unavailable"
            )
            return
        target = self.controller.lookup_generation_preset(request.preset_id)
        if target is None or target.source != "user":
            self._set_preset_notice("組み込みプリセットは変更できません。")
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="preset_not_user_owned",
            )
            return
        result = self.controller.update_generation_preset(
            request.preset_id,
            request.display_name,
            request.generation_settings,
        )
        if not result.succeeded:
            self._set_preset_notice(self._format_preset_mutation_error(result))
            self._sync_preset_panel()
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=getattr(result, "error_code", None) or "preset_update_rejected",
            )
            return
        self._selected_preset_id = request.preset_id
        self._normalize_active_preset_after_mutation()
        self._set_preset_notice("ユーザープリセットを更新しました。必要ならApplyしてください。")
        self._sync_preset_panel()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="preset_updated",
            payload={"preset_id": request.preset_id, "changed": True},
        )

    def _on_preset_delete_request(self, request: PresetDeleteRequest):
        if not isinstance(request, PresetDeleteRequest):
            return
        operation_handle = self._begin_debug_operation(
            "generation_preset_delete",
            payload={"preset_id": request.preset_id},
            entry="preset_panel",
        )
        if not self._preset_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            self._finish_debug_operation(
                operation_handle, "ignored", reason_code="stale_panel_request"
            )
            return
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="controller_unavailable"
            )
            return
        target = self.controller.lookup_generation_preset(request.preset_id)
        if target is None or target.source != "user":
            self._set_preset_notice("組み込みプリセットは削除できません。")
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="preset_not_user_owned",
            )
            return
        result = self.controller.delete_generation_preset(request.preset_id)
        if not result.succeeded:
            self._set_preset_notice(self._format_preset_mutation_error(result))
            self._sync_preset_panel()
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=getattr(result, "error_code", None) or "preset_delete_rejected",
            )
            return
        self._normalize_active_preset_after_mutation()
        active_id = self.ui_state.generation_state.active_preset_id
        self._selected_preset_id = active_id if active_id != request.preset_id else None
        self._set_preset_notice("ユーザープリセットを削除しました。")
        self._sync_preset_panel()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="preset_deleted",
            payload={"preset_id": request.preset_id, "changed": True},
        )

    def _on_model_profile_select_request(
        self,
        request: ModelProfileSelectRequest,
    ) -> None:
        if not isinstance(request, ModelProfileSelectRequest):
            return
        operation_handle = self._begin_debug_operation(
            "model_profile_select",
            payload={"profile_id": request.selected_profile_id},
            entry="profile_panel",
        )
        if (
            self.ui_state.is_busy
            or request.expected_panel_revision != self._model_profile_panel_revision
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if self.ui_state.is_busy else "stale_panel_request"),
            )
            return
        valid_ids = {item.id for item in self._profile_store_items()}
        if (
            request.selected_profile_id is not None
            and request.selected_profile_id not in valid_ids
        ):
            self._set_model_profile_notice("選択したモデルプロファイルは現在利用できません。")
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_profile_unavailable",
            )
            return
        changed = request.selected_profile_id != self._selected_model_profile_id
        self._selected_model_profile_id = request.selected_profile_id
        self._set_model_profile_notice("")
        self._sync_model_profile_panel()
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "noop",
            reason_code=("model_profile_selected" if changed else "selection_unchanged"),
            payload={"profile_id": request.selected_profile_id, "changed": changed},
        )

    def _on_whisper_model_select_request(
        self,
        request: WhisperModelSelectRequest,
    ) -> None:
        if not isinstance(request, WhisperModelSelectRequest):
            return
        state = self.ui_state.whisper_model_selection
        operation_handle = self._begin_debug_operation(
            "whisper_model_select",
            payload={"model_key": request.selected_model_key},
            entry="whisper_model_panel",
        )
        if (
            self.ui_state.is_busy
            or state.management_busy
            or request.expected_panel_revision != state.panel_revision
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=(
                    "busy"
                    if self.ui_state.is_busy or state.management_busy
                    else "stale_panel_request"
                ),
            )
            return
        valid_keys = {spec.model_key for spec in state.model_specs}
        if request.selected_model_key not in valid_keys:
            self.ui_state.whisper_model_selection = replace(
                state,
                notice="選択したWhisperモデルは現在利用できません。",
            )
            self.sync_ui_state(adjustment_only=True)
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="whisper_model_unavailable",
            )
            return
        if request.selected_model_key == state.selected_model_key:
            self._finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="model_already_selected",
                payload={"model_key": request.selected_model_key},
            )
            return
        self.ui_state.whisper_model_selection = replace(
            state,
            selected_model_key=request.selected_model_key,
            notice="候補を選択しました。Download & Verify後に適用できます。",
            panel_revision=state.panel_revision + 1,
        )
        if self.controller is not None:
            self.controller.request_settings_save()
        self.sync_ui_state(adjustment_only=True)
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="whisper_model_selected",
            payload={"model_key": request.selected_model_key, "changed": True},
        )

    def _on_whisper_model_download_request(
        self,
        request: WhisperModelDownloadRequest,
    ) -> None:
        if not isinstance(request, WhisperModelDownloadRequest):
            return
        operation_handle = self._begin_debug_operation(
            "whisper_model_download",
            payload={"model_key": request.model_key},
            entry="whisper_model_panel",
        )
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )
            return
        state = self.ui_state.whisper_model_selection
        spec = next(
            (item for item in state.model_specs if item.model_key == request.model_key),
            None,
        )
        if spec is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_key_unsupported",
            )
            return
        message = (
            f"{spec.display_name} を取得して検証します。\n\n"
            f"サイズ: {_format_whisper_model_size(spec.size_bytes)}\n"
            f"保存先: {state.storage_location_display}\n"
            "公式サイトへ接続し、取得中は一時ファイルを使用します。\n"
            "キャンセルまたは通信失敗時は、最初から再取得します。\n\n"
            "開始しますか？"
        )
        if wx.MessageBox(
            message,
            "Whisperモデルの取得確認",
            wx.YES_NO | wx.ICON_INFORMATION,
        ) != wx.YES:
            self._finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="download_confirmation_declined",
            )
            return
        self.controller.start_whisper_model_download(
            request.model_key,
            request.expected_panel_revision,
            confirmed=True,
            operation_handle=operation_handle,
        )

    def _on_whisper_model_apply_request(
        self,
        request: WhisperModelApplyRequest,
    ) -> None:
        if not isinstance(request, WhisperModelApplyRequest):
            return
        operation_handle = self._begin_debug_operation(
            "whisper_model_apply",
            payload={"model_key": request.model_key},
            entry="whisper_model_panel",
        )
        if self._reject_unapplied_output_edit():
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="unapplied_output_edits",
            )
            return
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )
            return
        state = self.ui_state.whisper_model_selection
        item = next(
            (item for item in state.model_specs if item.model_key == request.model_key),
            None,
        )
        if item is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_key_unsupported",
            )
            return
        if wx.MessageBox(
            f"{item.display_name} を次回解析に適用します。\n\n"
            "適用後は現在の解析結果を無効化し、確認済みモデルで再解析します。\n"
            "適用しますか？",
            "Whisperモデル適用確認",
            wx.YES_NO | wx.ICON_INFORMATION,
        ) != wx.YES:
            self._finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="model_apply_confirmation_declined",
            )
            return
        self.controller.start_whisper_model_apply(
            request.model_key,
            request.expected_panel_revision,
            operation_handle=operation_handle,
        )

    def _on_whisper_model_cancel_request(
        self,
        request: WhisperModelCancelRequest,
    ) -> None:
        if not isinstance(request, WhisperModelCancelRequest):
            return
        if self.controller is not None:
            self.controller.request_cancel_whisper_management(
                request.job_id,
                request.expected_panel_revision,
            )

    def _on_whisper_model_delete_request(
        self,
        request: WhisperModelDeleteRequest,
    ) -> None:
        if not isinstance(request, WhisperModelDeleteRequest):
            return
        operation_handle = self._begin_debug_operation(
            "whisper_model_delete",
            payload={"model_key": request.model_key},
            entry="whisper_model_panel",
        )
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )
            return
        state = self.ui_state.whisper_model_selection
        item = next(
            (item for item in state.model_specs if item.model_key == request.model_key),
            None,
        )
        if item is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_key_unsupported",
            )
            return
        if wx.MessageBox(
            f"{item.display_name} の検証済みモデルを削除します。\n\n"
            "現在の解析で使用中の場合は削除できません。\n"
            "削除後は必要に応じて、明示的に再取得してください。\n\n"
            "削除しますか？",
            "Whisperモデルの削除確認",
            wx.YES_NO | wx.ICON_WARNING,
        ) != wx.YES:
            self._finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="model_delete_confirmation_declined",
            )
            return
        self.controller.start_whisper_model_delete(
            request.model_key,
            request.expected_panel_revision,
            confirmed=True,
            operation_handle=operation_handle,
        )

    def _on_whisper_storage_root_request(
        self,
        request: WhisperStorageRootRequest,
    ) -> None:
        if not isinstance(request, WhisperStorageRootRequest):
            return
        operation_handle = self._begin_debug_operation(
            "whisper_storage_root_change",
            entry="whisper_model_panel",
        )
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )
            return
        state = self.ui_state.whisper_model_selection
        dialog = wx.DirDialog(
            self,
            "Whisperモデルの保存先を選択",
            defaultPath=state.storage_root_display or "",
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                self._finish_debug_operation(
                    operation_handle,
                    "cancelled",
                    reason_code="directory_dialog_cancelled",
                )
                return
            selected_path = dialog.GetPath()
        finally:
            dialog.Destroy()
        if not selected_path:
            self._finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="empty_directory_selection",
            )
            return
        if wx.MessageBox(
            f"Whisperモデルの保存先を次へ変更します。\n\n{selected_path}\n\n"
            "この変更ではネットワーク接続やモデル取得は開始しません。\n"
            "保存先を変更しますか？",
            "Whisperモデル保存先の確認",
            wx.YES_NO | wx.ICON_INFORMATION,
        ) != wx.YES:
            self._finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="storage_root_confirmation_declined",
            )
            return
        changed = self.controller.change_whisper_storage_root(
            selected_path,
            request.expected_panel_revision,
            confirmed=True,
        )
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "rejected",
            reason_code="storage_root_changed" if changed else "storage_root_change_rejected",
            payload={"changed": bool(changed)},
        )

    def _on_model_profile_apply_request(
        self,
        request: ModelProfileApplyRequest,
    ) -> None:
        if not isinstance(request, ModelProfileApplyRequest):
            return
        if self._reject_unapplied_output_edit():
            return
        if not self._model_profile_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            return
        if request.profile_id != self._selected_model_profile_id:
            return
        if request.profile_id is None:
            if self.ui_state.model_profile_state.active_model_profile_id is None:
                self._set_model_profile_notice("プロファイルなし（日本語5母音）は既に適用されています。")
                return
            applied = self.apply_no_model_profile()
            success_message = "プロファイルなし（日本語5母音）を適用しました。"
        else:
            profile = (
                self.controller.lookup_model_profile(request.profile_id)
                if self.controller is not None
                else None
            )
            if profile is None:
                self._set_model_profile_notice("選択したモデルプロファイルは現在利用できません。")
                self._sync_model_profile_panel()
                return
            item = next(
                (
                    item
                    for item in self.right_pane.get_model_profile_panel_state().items
                    if item.id == request.profile_id
                ),
                None,
            )
            if item is None or not item.default_preset_available:
                self._set_model_profile_notice(
                    "基準プリセットが見つからないため適用できません。Updateで修復してください。"
                )
                return
            if self.controller is None:
                return
            resolution = self.controller.resolve_model_profile_apply(request.profile_id)
            applied = self._commit_resolved_model_profile(resolution)
            if not applied:
                self._set_model_profile_notice(
                    self._format_model_profile_apply_error(resolution)
                )
                return
            success_message = f"モデルプロファイル「{profile.display_name}」を適用しました。"
        if not applied:
            self._set_model_profile_notice("モデルプロファイルを適用できませんでした。現在の状態を保持しています。")
            return
        self._set_model_profile_notice(success_message)
        self.sync_ui_state()

    def _on_model_profile_create_request(
        self,
        request: ModelProfileCreateRequest,
    ) -> None:
        if not isinstance(request, ModelProfileCreateRequest):
            return
        values = request.values
        operation_handle = self._begin_debug_operation(
            "model_profile_create",
            payload={
                "morph_name_set_id": values.morph_name_set_id,
                "morph_upper_limit": values.morph_upper_limit,
                "preset_id": values.default_preset_id,
            },
            entry="profile_panel",
        )
        if not self._model_profile_request_is_current(request.expected_panel_revision):
            self._finish_debug_operation(
                operation_handle, "ignored", reason_code="stale_panel_request"
            )
            return
        if self.controller is None:
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="controller_unavailable"
            )
            return
        before_ids = {item.id for item in self.controller.profile_store.user_profiles}
        result = self.controller.create_model_profile_from_values(
            values.display_name,
            values.morph_name_set_id,
            values.morph_upper_limit,
            values.generation_overrides,
            values.default_preset_id,
        )
        if not result.succeeded:
            self._set_model_profile_notice(self._format_model_profile_mutation_error(result))
            self._sync_model_profile_panel()
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=getattr(result, "error_code", None) or "model_profile_create_rejected",
            )
            return
        created_ids = [
            item.id for item in result.user_profiles if item.id not in before_ids
        ]
        if len(created_ids) == 1:
            self._selected_model_profile_id = created_ids[0]
            self._set_model_profile_notice(
                "モデルプロファイルを作成しました。Applyで出力へ反映できます。"
            )
        else:
            self._set_model_profile_notice(
                "作成結果のIDを一意に確認できませんでした。選択は変更していません。"
            )
        self._sync_model_profile_panel()
        self._finish_debug_operation(
            operation_handle,
            "completed" if len(created_ids) == 1 else "failed",
            reason_code=(
                "model_profile_created"
                if len(created_ids) == 1
                else "created_profile_identity_unavailable"
            ),
            payload={
                "profile_id": created_ids[0] if len(created_ids) == 1 else None,
                "changed": len(created_ids) == 1,
            },
        )

    def _on_model_profile_update_request(
        self,
        request: ModelProfileUpdateRequest,
    ) -> None:
        if not isinstance(request, ModelProfileUpdateRequest):
            return
        values = request.values
        operation_handle = self._begin_debug_operation(
            "model_profile_update",
            payload={
                "profile_id": request.profile_id,
                "morph_name_set_id": values.morph_name_set_id,
                "morph_upper_limit": values.morph_upper_limit,
                "preset_id": values.default_preset_id,
            },
            entry="profile_panel",
        )
        if not self._model_profile_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            self._finish_debug_operation(
                operation_handle, "ignored", reason_code="stale_panel_request"
            )
            return
        if request.profile_id != self._selected_model_profile_id or self.controller is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=(
                    "controller_unavailable"
                    if self.controller is None
                    else "model_profile_selection_changed"
                ),
            )
            return
        result = self.controller.update_model_profile_from_values(
            request.profile_id,
            values.display_name,
            values.morph_name_set_id,
            values.morph_upper_limit,
            values.generation_overrides,
            values.default_preset_id,
        )
        if not result.succeeded:
            self._set_model_profile_notice(self._format_model_profile_mutation_error(result))
            self._sync_model_profile_panel()
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=getattr(result, "error_code", None) or "model_profile_update_rejected",
            )
            return
        self._selected_model_profile_id = request.profile_id
        if self.ui_state.model_profile_state.active_model_profile_id == request.profile_id:
            self._sync_profile_display_names_from_state()
        self._set_model_profile_notice("モデルプロファイルを更新しました。必要ならApplyしてください。")
        self.sync_ui_state()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="model_profile_updated",
            payload={"profile_id": request.profile_id, "changed": True},
        )

    def _on_model_profile_delete_request(
        self,
        request: ModelProfileDeleteRequest,
    ) -> None:
        if not isinstance(request, ModelProfileDeleteRequest):
            return
        operation_handle = self._begin_debug_operation(
            "model_profile_delete",
            payload={"profile_id": request.profile_id},
            entry="profile_panel",
        )
        if not self._model_profile_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            self._finish_debug_operation(
                operation_handle, "ignored", reason_code="stale_panel_request"
            )
            return
        if request.profile_id != self._selected_model_profile_id or self.controller is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=(
                    "controller_unavailable"
                    if self.controller is None
                    else "model_profile_selection_changed"
                ),
            )
            return
        result = self.controller.delete_model_profile(request.profile_id)
        if not result.succeeded:
            self._set_model_profile_notice(self._format_model_profile_mutation_error(result))
            self._sync_model_profile_panel()
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=getattr(result, "error_code", None) or "model_profile_delete_rejected",
            )
            return
        valid_ids = {item.id for item in result.user_profiles}
        active_id = self.ui_state.model_profile_state.active_model_profile_id
        self._selected_model_profile_id = active_id if active_id in valid_ids else None
        self._set_model_profile_notice("モデルプロファイルを削除しました。")
        self.sync_ui_state()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="model_profile_deleted",
            payload={"profile_id": request.profile_id, "changed": True},
        )


    def update_status_display(
        self,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None = None,
    ):
        """
        [MS14-B2] StatusKey に基づいてステータスバーの文言を更新
        """
        key = self.ui_state.status_key
        
        msg_map = {
            StatusKey.IDLE: "待機中",
            StatusKey.INPUT_MISSING: "TEXT および 音声ファイル を読み込んでください",
            StatusKey.READY_FOR_ANALYSIS: "解析実行が可能です",
            StatusKey.ANALYSIS_INVALIDATED: "入力が変更されました (再解析が必要)",
            StatusKey.BUSY: "処理中...",
            StatusKey.ANALYSIS_READY: "解析完了 (VMD出力可能)",
            StatusKey.ANALYSIS_CANCELLED: "解析をキャンセルしました",
            StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK: (
                "解析に失敗しました（前回結果を表示中・保存不可）"
            ),
        }
        
        msg = msg_map.get(key, "...")
        self.update_status(msg)
        
    def set_controller(self, controller):
        """[MS13-B5] アプリのコントローラーをセットし、各種操作要求を委譲する口を設ける"""
        self.controller = controller

    def update_status(self, message: str):
        """[MS13-B5] UI上のステータス表示更新を一元化する共通入口"""
        if self.st_status_main.GetLabel() != message:
            self.st_status_main.SetLabel(message)

    def get_status_text(self) -> str:
        """[MS13-B5] 最小限の View Accessor (将来取得が必要になった場合の整理用)"""
        return self.st_status_main.GetLabel()

    # --- MS14-B1 View Helpers ---
    def set_text_path(self, path: str):
        self.info_panel.set_text_path(path)
        
    def set_wav_path(self, path: str):
        self.info_panel.set_wav_path(path)
        
    def set_text_preview(self, text: str):
        self.info_panel.set_text_preview(text)
        
    def set_hiragana_preview(self, text: str):
        self.info_panel.set_hiragana_preview(text)
        
    def set_vowel_preview(self, text: str):
        self.info_panel.set_vowel_preview(text)
        
    def set_wav_info(self, info: str):
        self.info_panel.set_wav_info(info)

    def set_waveform_placeholder_text(self, text: str):
        self.placeholder_container.set_waveform_placeholder_text(text)
        
    def set_preview_placeholder_text(self, text: str):
        self.placeholder_container.set_preview_placeholder_text(text)
        
    def set_playback_position_sec(self, position_sec: float | None):
        """Update the waveform and Preview cursors without refreshing Info."""
        self.placeholder_container.set_playback_position_sec(position_sec)

    def sync_playback_context(self) -> None:
        """Refresh the RightPane playback context at explicit sync points."""
        self._sync_playback_context()

    def _sync_playback_context(self):
        state = self.ui_state
        plan = state.current_timing_plan
        timeline = getattr(plan, "timeline", None) if plan is not None else None
        context = build_playback_info_context(
            is_playing=state.is_playing,
            is_paused=state.is_paused,
            position_sec=state.playback_position_sec,
            timeline=timeline,
            analysis_result_valid=state.analysis_result_valid,
            analysis_pending_rebuild=state.analysis_pending_rebuild,
        )
        self.right_pane.set_playback_context(context)

    def clear_playback_cursor(self):
        """[MS15-B3] 再生位置をクリアする"""
        self.placeholder_container.clear_playback_cursor()

    def invalidate_analysis_job(self):
        """Discard late analysis callbacks without reusing a prior job ID."""
        self._current_job_id += 1
        self._active_analysis_job_id = None
        self._analysis_parameter_snapshot = None
        self._analysis_rollback_snapshot = None

    def reset_workspace_display(self):
        """Restore workspace-specific widgets to their initial display."""
        self._accepted_debug_trace = None
        self._transition_evaluation_request = None
        self._cleanup_evaluation_request = None
        self.right_pane.clear_transition_candidate_status()
        self._refresh_transition_application_status()
        self.right_pane.clear_transition_summary()
        self.info_panel.reset_workspace_display()
        self.placeholder_container.set_waveform_placeholder_text("WAVファイルが読み込まれていません")
        self.placeholder_container.set_preview_placeholder_text("未解析")
        self.placeholder_container.clear_playback_cursor()
        self.placeholder_container.clear_selection()
        self._selected_event_notice = ""
        self.right_pane.clear_selected_event()

    def confirm_workspace_reset(self) -> bool:
        result = wx.MessageBox(
            "現在の入力と解析結果をクリアして、新しい作業を開始します。\n"
            "元のTEXT・音声ファイルと、保存済みファイルは削除されません。\n\n"
            "続行しますか？",
            "新規作業",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        return result == wx.YES

    # --- MS16-B6 Selection Helpers ---
    def select_event_by_source_index(self, index: int | None):
        """[MS16-B6] イベントの選択状態を設定する"""
        if index != self.ui_state.selected_source_event_index:
            self._finish_current_adjustment_gesture()
        self._selected_event_notice = ""
        self.ui_state.set_selected_source_event_index(index)
        self.placeholder_container.set_selected_source_event_index(index)
        self.update_selected_event_display()

    def clear_selected_event(self):
        """[MS16-B6] イベントの選択状態をクリアする"""
        if self.ui_state.selected_source_event_index is not None:
            self._finish_current_adjustment_gesture()
        self._selected_event_notice = ""
        self.ui_state.clear_selection()
        self.placeholder_container.clear_selection()
        self.update_selected_event_display()

    def _on_preview_selection_request(self, request: PreviewSelectionRequest):
        """Validate and commit a canonical Preview click without trusting stale wx state."""
        if not isinstance(request, PreviewSelectionRequest):
            return
        operation_handle = self._begin_debug_operation(
            "event_selection",
            payload={"event_index": request.base_event_index},
            entry="preview",
        )

        def finish_selection(status: str, reason_code: str) -> None:
            self._finish_debug_operation(
                operation_handle,
                status,
                reason_code=reason_code,
                payload={"event_index": request.base_event_index},
            )

        if self.ui_state.is_busy:
            finish_selection("rejected", "busy")
            return
        preview_model = self.placeholder_container.pnl_preview.model
        if (
            not preview_model.is_valid
            or request.render_revision != preview_model.render_revision
            or request.base_plan_identity_digest != preview_model.base_plan_identity_digest
            or request.final_output_binding != preview_model.final_output_binding
        ):
            finish_selection("ignored", "stale_preview_selection")
            return
        if not self._matches_current_shared_final_output_binding(
            request.final_output_binding
        ):
            finish_selection("ignored", "stale_output_binding")
            return
        base_input = self._build_current_base_timing_plan_input()
        if base_input is None:
            finish_selection("rejected", "base_plan_unavailable")
            return
        try:
            current_digest = build_base_plan_identity(base_input).digest
        except Exception:
            finish_selection("rejected", "base_plan_identity_unavailable")
            return
        valid_indices = tuple(
            region.base_event_index for region in preview_model.get_event_hit_regions()
        )
        if (
            request.base_event_index in valid_indices
            and request.base_event_index
            != self.ui_state.selected_source_event_index
        ):
            self._finish_current_adjustment_gesture()
        committed = self.ui_state.commit_selected_source_event_index(
            request.base_event_index,
            requested_base_plan_identity_digest=request.base_plan_identity_digest,
            current_base_plan_identity_digest=current_digest,
            valid_base_event_indices=valid_indices,
        )
        if not committed:
            finish_selection("ignored", "selection_not_committed")
            return
        self._selected_event_notice = ""
        self.placeholder_container.set_selected_source_event_index(request.base_event_index)
        self.update_selected_event_display()
        self.right_pane.show_selected_event_tab()
        finish_selection(
            "completed" if request.base_event_index is not None else "noop",
            "event_selected" if request.base_event_index is not None else "selection_cleared",
        )

    def update_selected_event_display(
        self,
        *,
        sync_context: UiSyncContext | None = None,
    ):
        """Reflect canonical B4 editor state or the legacy B3 summary."""
        state = self.ui_state
        selected_index = state.selected_source_event_index
        selected_digest = state.selected_base_plan_identity_digest
        if selected_index is not None and selected_digest:
            if sync_context is None:
                if state.output_edit_draft_dirty:
                    sync_context = self._current_ui_sync_context
                else:
                    sync_context = self._build_current_ui_sync_context()
            effective_plan = (
                None if sync_context is None else sync_context.effective_plan
            )
            base_input = None if sync_context is None else sync_context.base_input
            if effective_plan is None:
                cached_context = getattr(self, "_current_ui_sync_context", None)
                cached_plan = getattr(cached_context, "effective_plan", None)
                cached_base_input = getattr(cached_context, "base_input", None)
                if (
                    isinstance(cached_plan, EffectiveShapePlan)
                    and cached_plan.base_plan_identity.digest == selected_digest
                    and isinstance(cached_base_input, BaseTimingPlanInput)
                ):
                    effective_plan = cached_plan
                    base_input = cached_base_input
            if effective_plan is None:
                shared_context = state.final_output_state.current_context
                legacy_context = getattr(
                    getattr(shared_context, "issuer_context", None),
                    "legacy_context",
                    None,
                )
                accepted_plan = getattr(
                    legacy_context, "effective_plan_snapshot", None
                )
                accepted_base_input = getattr(legacy_context, "base_input", None)
                if (
                    isinstance(accepted_plan, EffectiveShapePlan)
                    and accepted_plan.base_plan_identity.digest == selected_digest
                    and isinstance(accepted_base_input, BaseTimingPlanInput)
                ):
                    effective_plan = accepted_plan
                    base_input = accepted_base_input
            if effective_plan is not None and base_input is not None:
                shared_context = state.final_output_state.current_context
                shared_identity = getattr(shared_context, "identity", None)
                final_output_binding = (
                    shared_identity.binding_digest
                    if shared_identity is not None
                    and self._matches_current_shared_final_output_binding(
                        shared_identity.binding_digest
                    )
                    else None
                )
                try:
                    editor_state = build_selected_event_editor_state(
                        effective_plan,
                        selected_index,
                        expected_base_identity_digest=selected_digest,
                        editor_revision=state.selected_event_editor_revision,
                        source_duration_frames=base_input.source_duration_frames,
                        adjustment_snapshot=state.current_adjustment_snapshot,
                        final_output_binding=final_output_binding,
                    )
                    self.right_pane.set_selected_event_editor_state(
                        editor_state,
                        busy=state.is_busy,
                        operation_notice=self._selected_event_notice,
                    )
                    return
                except (AdjustmentContractError, ValueError):
                    pass
        summary = self.placeholder_container.get_selected_shape_summary()
        if summary:
            self.right_pane.set_selected_event_summary(summary)
        else:
            self.right_pane.clear_selected_event()

    def _current_default_transition_selection(self):
        if getattr(self, "_transition_evaluation_request", None) is not None:
            return None
        binding = getattr(self, "_adopted_transition_binding", None)
        if binding is None:
            return None
        return resolve_default_transition_selection(binding, self.ui_state.input_mode)

    def _current_default_cleanup_selection(self):
        if (
            getattr(self, "_transition_evaluation_request", None) is not None
            or getattr(self, "_cleanup_evaluation_request", None) is not None
        ):
            return None
        binding = getattr(self, "_adopted_cleanup_binding", None)
        if binding is None:
            return None
        names = self._resolved_output_morph_names()
        mapping = tuple(zip(SEMANTIC_VOWEL_ORDER, names))
        profile = getattr(self.ui_state, "model_profile_state", None)
        return resolve_default_cleanup_selection(
            binding,
            input_mode=self.ui_state.input_mode,
            profile_id=getattr(profile, "active_model_profile_id", None),
            output_mapping=mapping,
        )

    def _refresh_transition_application_status(self) -> None:
        cleanup_request = getattr(self, "_cleanup_evaluation_request", None)
        if cleanup_request is not None:
            self.right_pane.set_transition_candidate_status(
                f"自動整理：比較候補（{cleanup_request.variant}）"
            )
            return
        if self._transition_evaluation_request is not None:
            self.right_pane.set_transition_candidate_status(
                "自動母音遷移：候補検証中"
            )
            return
        selection = self._current_default_transition_selection()
        if selection is None:
            self.right_pane.clear_transition_candidate_status()
            return
        if selection.selection_kind == "transition":
            cleanup_selection = self._current_default_cleanup_selection()
            if cleanup_selection is not None and cleanup_selection.selection_kind == "cleanup":
                status = "自動母音遷移：適用（採択scope）／自動キー整理：適用（曲線同一の場合のみ）"
            else:
                status = "自動母音遷移：適用（採択scope）"
        else:
            cleanup_selection = self._current_default_cleanup_selection()
            if cleanup_selection is not None and cleanup_selection.selection_kind == "cleanup":
                status = f"自動母音遷移：対象外（{selection.reason}）／自動キー整理：適用（曲線同一の場合のみ）"
            else:
                status = f"自動母音遷移：対象外（{selection.reason}）"
        self.right_pane.set_transition_candidate_status(status)

    def _bounded_candidate_enabled(self):
        from src.core.cross_vowel_transition import TRANSITION_POLICY_V2
        request = getattr(self, "_transition_evaluation_request", None)
        if request is not None:
            return request.policy.policy_id == TRANSITION_POLICY_V2
        selection = self._current_default_transition_selection()
        return selection is not None and selection.selection_kind == "transition"

    def _resolve_current_effective_plan(self, base_input: BaseTimingPlanInput):
        identity = build_base_plan_identity(base_input)
        snapshot = self.ui_state.current_adjustment_snapshot
        if snapshot is None:
            snapshot = empty_adjustment_snapshot(identity)
            self.ui_state.set_current_adjustment_snapshot(
                snapshot,
                expected_base_plan_identity_digest=identity.digest,
            )
        elif snapshot.base_plan_identity != identity:
            raise AdjustmentContractError("adjustment snapshot base identity mismatch")
        if self._bounded_candidate_enabled():
            return None
        return resolve_effective_shape_plan(base_input, snapshot)

    @staticmethod
    def _build_adjustment_coalescing_key(
        *,
        base_identity_digest: str,
        base_event_index: int,
        field: str,
        coalescing_token: int,
    ) -> AdjustmentCoalescingKey:
        return AdjustmentCoalescingKey(
            base_plan_identity_digest=base_identity_digest,
            base_event_index=base_event_index,
            field=field,
            gesture_token=coalescing_token,
        )

    def _adjustment_history_matches_current_base(
        self,
        sync_context: UiSyncContext | None = None,
    ) -> bool:
        snapshot = self.ui_state.current_adjustment_snapshot
        if sync_context is None:
            base_input = self._build_current_base_timing_plan_input()
            if snapshot is None or base_input is None:
                return False
            try:
                return snapshot.base_plan_identity == build_base_plan_identity(base_input)
            except (AdjustmentContractError, TypeError, ValueError):
                return False
        if snapshot is None:
            return False
        return snapshot.base_plan_identity == sync_context.base_plan_identity

    def _finish_current_adjustment_gesture(self) -> bool:
        changed = self.ui_state.finish_current_adjustment_coalescing()
        self.right_pane.clear_selected_event_gesture_state()
        return changed

    def _on_selected_event_edit_boundary_request(
        self,
        request: SelectedEventEditBoundaryRequest,
    ):
        state = self.ui_state
        if not isinstance(request, SelectedEventEditBoundaryRequest):
            return
        if (
            state.is_busy
            or request.base_event_index != state.selected_source_event_index
            or request.base_identity_digest
            != state.selected_base_plan_identity_digest
        ):
            return
        try:
            key = self._build_adjustment_coalescing_key(
                base_identity_digest=request.base_identity_digest,
                base_event_index=request.base_event_index,
                field=request.field,
                coalescing_token=request.coalescing_token,
            )
        except (AdjustmentContractError, TypeError, ValueError):
            return
        if state.finish_adjustment_coalescing(key):
            self.sync_ui_state(adjustment_only=True)

    def _selected_event_editor_has_uncommitted_input(self) -> bool:
        if not self.right_pane.selected_event_editor_has_dirty_input():
            return False
        self.right_pane.set_selected_event_editor_error(
            "Enterで値を確定するか、入力内容を修正してください。"
        )
        return True

    def _perform_adjustment_history_navigation(self, *, redo: bool) -> bool:
        state = self.ui_state
        operation_handle = self._begin_debug_operation(
            "adjustment_redo" if redo else "adjustment_undo",
            payload={"history_action": "redo" if redo else "undo"},
            entry="shortcut_or_button",
        )
        if (
            state.is_busy
            or self._pending_selected_event_projection is not None
            or not self._adjustment_history_matches_current_base()
            or self._selected_event_editor_has_uncommitted_input()
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if state.is_busy else "history_unavailable"),
                payload={"history_action": "redo" if redo else "undo"},
            )
            return False
        self._finish_current_adjustment_gesture()
        before_persistent_projection = self._persistent_generation_projection()
        if self.controller and hasattr(self.controller, "preset_store"):
            def normalize_generation_state(generation_state):
                resolution = self.controller.preset_store.resolve_active(
                    generation_state.generation_settings,
                    generation_state.active_preset_id,
                )
                return GenerationState(
                    generation_settings=resolution.generation_settings,
                    active_preset_id=resolution.active_preset_id,
                    resolved_morph_name_set_id=(
                        generation_state.resolved_morph_name_set_id
                    ),
                )

            state.normalize_output_edit_history(normalize_generation_state)
        changed = (
            state.redo_output_edit_state()
            if redo
            else state.undo_output_edit_state()
        )
        if not changed:
            self.update_action_states()
            self._finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="history_unchanged",
                payload={
                    "history_action": "redo" if redo else "undo",
                    "history_changed": False,
                },
            )
            return False
        current_draft_base = self._build_current_base_timing_plan_input()
        if (
            current_draft_base is not None
            and state.output_edit_history_state is not None
            and not self._rebase_output_edit_draft(current_draft_base)
        ):
            state.output_edit_draft_error = (
                "Undo / Redo後の編集履歴を解析イベントへ対応付けできません。"
            )
        self._selected_event_notice = (
            "出力編集をやり直しました。"
            if redo
            else "出力編集を元に戻しました。"
        )
        if self.controller and self.controller.active_preset_resolution is not None:
            resolution = self.controller.preset_store.resolve_active(
                state.generation_state.generation_settings,
                state.generation_state.active_preset_id,
            )
            self._active_preset_display_name = resolution.active_preset_display_name
        self._sync_profile_display_names_from_state()
        self._project_output_edit_controls()
        self.sync_ui_state(adjustment_only=True)
        if (
            self.controller
            and before_persistent_projection != self._persistent_generation_projection()
        ):
            self.controller.request_settings_save()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="history_changed",
            payload={
                "history_action": "redo" if redo else "undo",
                "history_changed": True,
            },
        )
        return True

    def _persistent_generation_projection(self):
        state = self.ui_state
        profile = state.model_profile_state
        generation = state.generation_state
        return (
            profile.active_model_profile_id,
            profile.active_profile_baseline_preset_id,
            generation.generation_settings,
            generation.active_preset_id,
        )

    def _sync_profile_display_names_from_state(self) -> None:
        profile_state = (
            self.ui_state.draft_model_profile_state
            if self.ui_state.output_edit_draft_dirty
            else self.ui_state.model_profile_state
        )
        profile_id = profile_state.active_model_profile_id
        baseline_id = profile_state.active_profile_baseline_preset_id
        if self.controller is None or profile_id is None:
            self.ui_state.active_model_profile_display_name = None
            self.ui_state.baseline_preset_display_name = None
            return
        profile = self.controller.lookup_model_profile(profile_id)
        baseline = self.controller.lookup_generation_preset(baseline_id)
        self.ui_state.active_model_profile_display_name = (
            None if profile is None else profile.display_name
        )
        self.ui_state.baseline_preset_display_name = (
            None if baseline is None else baseline.display_name
        )

    def _on_adjustment_undo(self, event):
        self._perform_adjustment_history_navigation(redo=False)

    def _on_adjustment_redo(self, event):
        self._perform_adjustment_history_navigation(redo=True)

    def _on_history_shortcut(self, event):
        if (
            not event.ControlDown()
            or event.AltDown()
            or event.ShiftDown()
            or event.GetKeyCode() not in (ord("Z"), ord("Y"))
        ):
            event.Skip()
            return
        focused = wx.Window.FindFocus()
        if self.right_pane.is_selected_event_editor_window(focused):
            if self._selected_event_editor_has_uncommitted_input():
                return
        elif isinstance(focused, (wx.TextCtrl, wx.ComboBox)):
            event.Skip()
            return
        self._perform_adjustment_history_navigation(
            redo=event.GetKeyCode() == ord("Y")
        )

    def _on_adjustment_reset_selected(self, event):
        state = self.ui_state
        if (
            state.selected_source_event_index is None
            or state.selected_base_plan_identity_digest is None
        ):
            return
        self._on_selected_event_reset_request(
            state.selected_source_event_index,
            state.selected_base_plan_identity_digest,
            state.selected_event_editor_revision,
        )

    def _on_adjustment_reset_all(self, event):
        state = self.ui_state
        operation_handle = self._begin_debug_operation(
            "adjustments_reset_all",
            entry="button",
        )
        if (
            state.is_busy
            or self._pending_selected_event_projection is not None
            or not state.has_event_adjustments
            or not self._adjustment_history_matches_current_base()
            or self._selected_event_editor_has_uncommitted_input()
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if state.is_busy else "reset_unavailable"),
            )
            return
        snapshot = state.current_adjustment_snapshot
        if snapshot is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="adjustment_snapshot_unavailable",
            )
            return
        self._finish_current_adjustment_gesture()
        reset_snapshot = empty_adjustment_snapshot(snapshot.base_plan_identity)
        if not state.commit_adjustment_snapshot(
            reset_snapshot,
            expected_base_plan_identity_digest=(
                snapshot.base_plan_identity.digest
            ),
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="reset_not_committed",
            )
            return
        if not state.output_edit_draft_dirty:
            state.require_output_edit_apply_for_current_state()
        self._selected_event_notice = "すべての出力編集をリセットしました。"
        self.sync_ui_state(adjustment_only=True)
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="adjustments_reset",
            payload={"changed": True},
        )

    def _on_selected_event_edit_request(self, request: SelectedEventEditRequest):
        state = self.ui_state
        if not isinstance(request, SelectedEventEditRequest):
            return
        operation_handle = self._begin_debug_operation(
            "selected_event_edit",
            payload={
                "event_index": request.base_event_index,
                "field": request.field,
                "after": request.value,
            },
            entry="selected_event_editor",
        )

        def finish_edit(status: str, reason_code: str, *, changed: bool = False, before=None) -> None:
            self.right_pane.clear_selected_event_edit_pending()
            payload = {
                "event_index": request.base_event_index,
                "field": request.field,
                "after": request.value,
                "changed": changed,
            }
            if before is not None:
                payload["before"] = before
            self._finish_debug_operation(
                operation_handle,
                status,
                reason_code=reason_code,
                payload=payload,
            )

        if state.is_busy:
            finish_edit("rejected", "busy")
            return
        if self._pending_selected_event_projection is not None:
            finish_edit("rejected", "draft_projection_pending")
            return
        if (
            request.base_event_index != state.selected_source_event_index
            or request.base_identity_digest
            != state.selected_base_plan_identity_digest
            or request.editor_revision != state.selected_event_editor_revision
            or not self._matches_current_shared_final_output_binding(
                request.final_output_binding,
                coalescing_token=request.coalescing_token,
            )
        ):
            finish_edit("ignored", "stale_selected_event_edit")
            return
        base_input = self._build_current_base_timing_plan_input()
        snapshot = state.current_adjustment_snapshot
        if base_input is None or snapshot is None:
            finish_edit("rejected", "adjustment_snapshot_unavailable")
            return
        editor_state = getattr(self.right_pane, "_selected_editor_state", None)
        requested_field_names = {
            "peak_value": "requested_peak_value",
            "start_offset_frames": "requested_start_offset_frames",
            "end_offset_frames": "requested_end_offset_frames",
            "hold_frames": "requested_hold_frames",
            "softness_frames": "requested_softness_frames",
            "slope_ratio": "requested_slope_ratio",
            "long_vowel_mode": "requested_long_vowel_mode",
            "manual_overlap_limit_override": "requested_manual_overlap_limit_override",
        }
        before_value = getattr(
            editor_state,
            requested_field_names.get(request.field, ""),
            None,
        )
        if before_value is None:
            current_adjustment = next(
                (
                    item
                    for item in snapshot.adjustments
                    if item.base_event_index == request.base_event_index
                ),
                None,
            )
            before_value = (
                None
                if current_adjustment is None
                else getattr(current_adjustment, request.field, None)
            )
        try:
            adjustment_target_base_event_index = (
                editor_state.group_tail_base_event_index
                if editor_state is not None and request.field in GROUP_SHARED_FIELDS
                else request.base_event_index
            )
            requested_change = merge_selected_event_edit(
                snapshot,
                request,
                adjustment_target_base_event_index=(
                    adjustment_target_base_event_index
                ),
            )
            requested_adjustments = {
                item.base_event_index: item for item in snapshot.adjustments
            }
            requested_adjustments[
                requested_change.base_event_index
            ] = requested_change
            requested_snapshot = canonicalize_adjustment_snapshot(
                snapshot.base_plan_identity,
                requested_adjustments.values(),
                base_peak_values=tuple(
                    float(getattr(point, "peak_value", getattr(point, "value", 0.0)))
                    for point in base_input.timeline
                ),
                closing_hold_frames=base_input.shape_parameters.closing_hold_frames,
                closing_softness_frames=base_input.shape_parameters.closing_softness_frames,
            )
        except (AdjustmentContractError, TypeError, ValueError) as error:
            message = f"補正を適用できません: {error}"
            self.right_pane.set_selected_event_editor_error(
                message
            )
            finish_edit("rejected", "edit_contract_rejected", before=before_value)
            return
        coalesce_key = None
        if request.coalescing_token is not None:
            try:
                coalesce_key = self._build_adjustment_coalescing_key(
                    base_identity_digest=request.base_identity_digest,
                    base_event_index=adjustment_target_base_event_index,
                    field=request.field,
                    coalescing_token=request.coalescing_token,
                )
            except (AdjustmentContractError, TypeError, ValueError):
                finish_edit("rejected", "edit_coalescing_invalid", before=before_value)
                return
        bounded_candidate_enabled = self._bounded_candidate_enabled()
        started = self._queue_selected_event_projection(
            purpose="selected_event_edit",
            base_input=base_input,
            snapshot=snapshot,
            compute=lambda: apply_adjustment_update(
                base_input,
                snapshot,
                requested_change,
                defer_automatic_zero_conflicts=bounded_candidate_enabled,
            ),
            operation_handle=operation_handle,
            payload={
                "event_index": request.base_event_index,
                "field": request.field,
                "before_value": before_value,
                "after_value": request.value,
                "snapshot": snapshot,
                "requested_snapshot": requested_snapshot,
                "timing_plan": state.current_timing_plan,
                "editor_revision": state.selected_event_editor_revision,
                "coalescing_key": coalesce_key,
            },
        )
        if not started:
            finish_edit("rejected", "draft_projection_pending", before=before_value)

    def _on_selected_event_reset_request(
        self,
        base_event_index: int,
        base_identity_digest: str,
        editor_revision: int,
        final_output_binding: str | None = None,
    ):
        state = self.ui_state
        operation_handle = self._begin_debug_operation(
            "selected_event_reset",
            payload={"event_index": base_event_index},
            entry="selected_event_editor",
        )
        if self._pending_selected_event_projection is not None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="draft_projection_pending",
            )
            return
        if (
            state.is_busy
            or base_event_index != state.selected_source_event_index
            or base_identity_digest != state.selected_base_plan_identity_digest
            or editor_revision != state.selected_event_editor_revision
            or not self._matches_current_shared_final_output_binding(
                final_output_binding
            )
        ):
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if state.is_busy else "stale_selected_event_reset"),
            )
            return
        self._finish_current_adjustment_gesture()
        base_input = self._build_current_base_timing_plan_input()
        snapshot = state.current_adjustment_snapshot
        if base_input is None or snapshot is None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="adjustment_snapshot_unavailable",
            )
            return
        bounded_candidate_enabled = self._bounded_candidate_enabled()
        started = self._queue_selected_event_projection(
            purpose="selected_event_reset",
            base_input=base_input,
            snapshot=snapshot,
            compute=lambda: apply_adjustment_update(
                base_input,
                snapshot,
                reset_selected_event_adjustment(snapshot, base_event_index),
                defer_automatic_zero_conflicts=bounded_candidate_enabled,
            ),
            operation_handle=operation_handle,
            payload={
                "event_index": base_event_index,
                "snapshot": snapshot,
                "timing_plan": state.current_timing_plan,
                "editor_revision": state.selected_event_editor_revision,
            },
        )
        if not started:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="draft_projection_pending",
            )
        
    def get_morph_upper_limit(self) -> float:
        return self.param_panel.get_morph_upper_limit()
        
    def set_morph_upper_limit(self, val: float):
        changed = self.ui_state.resolved_morph_upper_limit != val
        self.param_panel.set_morph_upper_limit(val)
        if not self._projection_guard:
            self.ui_state.resolved_morph_upper_limit = val
            if changed:
                self.ui_state.final_output_state.invalidate_context()
        
    def get_closing_hold_frames(self) -> int:
        return self.param_panel.get_closing_hold_frames()
        
    def set_closing_hold_frames(self, val: int):
        changed = self.param_panel.get_closing_hold_frames() != val
        self.param_panel.set_closing_hold_frames(val)
        if changed:
            self.ui_state.final_output_state.invalidate_context()
        
    def get_closing_softness_frames(self) -> int:
        return self.param_panel.get_closing_softness_frames()
        
    def set_closing_softness_frames(self, val: int):
        changed = self.param_panel.get_closing_softness_frames() != val
        self.param_panel.set_closing_softness_frames(val)
        if changed:
            self.ui_state.final_output_state.invalidate_context()

    def apply_generation_state(
        self,
        generation_state: GenerationState,
        *,
        active_preset_display_name: str | None = None,
    ) -> bool:
        if not isinstance(generation_state, GenerationState):
            return False
        if generation_state != self.ui_state.generation_state:
            self.ui_state.final_output_state.invalidate_context()
        self.ui_state.generation_state = generation_state
        self._active_preset_display_name = active_preset_display_name
        self._project_generation_controls()
        return True

    def _commit_resolved_model_profile(
        self,
        resolution,
        *,
        request_save: bool = True,
    ) -> bool:
        if not isinstance(resolution, ModelProfileResolutionResult):
            return False
        if resolution.resolution is None:
            return False
        resolved = resolution.resolution
        current_state = self.ui_state.generation_state
        upper_changed = (
            self.ui_state.resolved_morph_upper_limit != resolved.morph_upper_limit
        )
        candidate_generation = GenerationState(
            generation_settings=resolved.generation_settings,
            active_preset_id=resolved.active_preset_id,
            resolved_morph_name_set_id=resolved.morph_name_set.set_id,
        )
        output_changed = candidate_generation != current_state
        profile_changed = self.ui_state.model_profile_state != (
            resolved.model_profile_state
        )
        if not upper_changed and not output_changed and not profile_changed:
            self._active_preset_display_name = resolved.active_preset_display_name
            self.ui_state.active_model_profile_display_name = (
                resolved.active_profile_display_name
            )
            self.ui_state.baseline_preset_display_name = (
                resolved.baseline_preset_display_name
            )
            return True

        if upper_changed:
            self.ui_state.resolved_morph_upper_limit = resolved.morph_upper_limit
            self._projection_guard = True
            try:
                self.set_morph_upper_limit(resolved.morph_upper_limit)
            finally:
                self._projection_guard = False
            self.ui_state.generation_state = candidate_generation
            self.ui_state.resolved_morph_upper_limit = (
                self.ui_state.current_output_edit_state.morph_upper_limit
                if self.ui_state.current_output_edit_state is not None
                else self.ui_state.resolved_morph_upper_limit
            )
            self.ui_state.model_profile_state = resolved.model_profile_state
            self.ui_state.active_model_profile_display_name = (
                resolved.active_profile_display_name
            )
            self.ui_state.baseline_preset_display_name = (
                resolved.baseline_preset_display_name
            )
            self._active_preset_display_name = resolved.active_preset_display_name
            self.ui_state.clear_adjustment_history()
            if self.ui_state.analysis_result_valid:
                self.ui_state.invalidate_analysis()
            self._project_generation_controls()
            self.sync_ui_state()
        else:
            base_input = self._build_current_base_timing_plan_input()
            if (
                base_input is not None
                and self.ui_state.analysis_result_valid
                and not self.ui_state.analysis_pending_rebuild
            ):
                snapshot = self.ui_state.current_adjustment_snapshot
                if snapshot is None:
                    snapshot = empty_adjustment_snapshot(build_base_plan_identity(base_input))
                try:
                    sync_context = build_ui_sync_context(base_input, snapshot,
                        defer_resolution=self._bounded_candidate_enabled())
                    candidate_output = OutputEditState(
                        base_plan_identity=sync_context.base_plan_identity,
                        adjustment_snapshot=snapshot,
                        generation_state=candidate_generation,
                        morph_upper_limit=resolved.morph_upper_limit,
                    )
                except (AdjustmentContractError, TypeError, ValueError):
                    return False
                if not self.ui_state.commit_output_edit_state(
                    candidate_output,
                    model_profile_state=resolved.model_profile_state,
                ):
                    return False
            else:
                self.ui_state.generation_state = candidate_generation
                self.ui_state.model_profile_state = resolved.model_profile_state
                self.ui_state.clear_adjustment_history()
            self.ui_state.resolved_morph_upper_limit = resolved.morph_upper_limit
            self.ui_state.active_model_profile_display_name = (
                resolved.active_profile_display_name
            )
            self.ui_state.baseline_preset_display_name = (
                resolved.baseline_preset_display_name
            )
            self._active_preset_display_name = resolved.active_preset_display_name
            # This path is reached only by an explicit, clean profile action.
            # Keep its prior context in history, but adopt the success as the
            # new applied baseline.
            self.ui_state.generation_state = candidate_generation
            self.ui_state.model_profile_state = resolved.model_profile_state
            if self.ui_state.analysis_result_valid:
                self.ui_state.initialize_output_edit_draft_baseline()
            self._project_generation_controls()
            self.sync_ui_state(adjustment_only=True)
        if request_save and self.controller:
            self.controller.request_settings_save()
        return True

    def apply_model_profile(self, profile_id: str) -> bool:
        operation_handle = self._begin_debug_operation(
            "model_profile_apply",
            payload={"profile_id": profile_id},
            entry="profile_panel",
        )
        if self._reject_unapplied_output_edit():
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="unapplied_output_edits"
            )
            return False
        if self.controller is None or self.ui_state.is_busy:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if self.ui_state.is_busy else "controller_unavailable"),
            )
            return False
        resolution = self.controller.resolve_model_profile_apply(profile_id)
        changed = self._commit_resolved_model_profile(resolution)
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "rejected",
            reason_code="model_profile_applied" if changed else "model_profile_apply_rejected",
            payload={"profile_id": profile_id, "changed": changed},
        )
        return changed

    def apply_no_model_profile(self) -> bool:
        operation_handle = self._begin_debug_operation(
            "model_profile_clear",
            payload={
                "profile_id": self.ui_state.model_profile_state.active_model_profile_id
            },
            entry="profile_panel",
        )
        if self._reject_unapplied_output_edit():
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="unapplied_output_edits"
            )
            return False
        if self.controller is None or self.ui_state.is_busy:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if self.ui_state.is_busy else "controller_unavailable"),
            )
            return False
        resolution = self.controller.resolve_no_profile()
        changed = self._commit_resolved_model_profile(resolution)
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "rejected",
            reason_code="model_profile_cleared" if changed else "model_profile_clear_rejected",
            payload={"changed": changed},
        )
        return changed

    def apply_active_model_profile_preset(self, preset_id: str) -> bool:
        operation_handle = self._begin_debug_operation(
            "model_profile_preset_apply",
            payload={
                "profile_id": self.ui_state.model_profile_state.active_model_profile_id,
                "preset_id": preset_id,
            },
            entry="profile_panel",
        )
        if self._reject_unapplied_output_edit():
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="unapplied_output_edits"
            )
            return False
        if self.controller is None or self.ui_state.is_busy:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if self.ui_state.is_busy else "controller_unavailable"),
            )
            return False
        resolution = self.controller.resolve_active_profile_preset_apply(preset_id)
        changed = self._commit_resolved_model_profile(resolution)
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "rejected",
            reason_code=(
                "model_profile_preset_applied"
                if changed
                else "model_profile_preset_apply_rejected"
            ),
            payload={
                "profile_id": self.ui_state.model_profile_state.active_model_profile_id,
                "preset_id": preset_id,
                "changed": changed,
            },
        )
        return changed

    def _project_generation_controls(self) -> None:
        settings = self.ui_state.generation_state.generation_settings
        self._projection_guard = True
        try:
            self.set_closing_hold_frames(settings.closing_hold_frames)
            self.set_closing_softness_frames(settings.closing_softness_frames)
        finally:
            self._projection_guard = False

    def _project_output_edit_controls(self) -> None:
        state = self.ui_state
        output_state = state.current_output_edit_state
        settings = (
            state.generation_state.generation_settings
            if output_state is None
            else output_state.generation_state.generation_settings
        )
        upper_limit = (
            state.resolved_morph_upper_limit
            if output_state is None
            else output_state.morph_upper_limit
        )
        self._projection_guard = True
        try:
            if self.param_panel.get_morph_upper_limit() != upper_limit:
                self.set_morph_upper_limit(upper_limit)
            if self.param_panel.get_closing_hold_frames() != settings.closing_hold_frames:
                self.set_closing_hold_frames(settings.closing_hold_frames)
            if (
                self.param_panel.get_closing_softness_frames()
                != settings.closing_softness_frames
            ):
                self.set_closing_softness_frames(settings.closing_softness_frames)
        finally:
            self._projection_guard = False

    def _generation_settings_from_controls(self) -> GenerationSettings:
        output_state = self.ui_state.current_output_edit_state
        current = (
            output_state.generation_state.generation_settings
            if self.ui_state.output_edit_draft_dirty and output_state is not None
            else self.ui_state.generation_state.generation_settings
        )
        return GenerationSettings(
            closing_hold_frames=self.get_closing_hold_frames(),
            closing_softness_frames=self.get_closing_softness_frames(),
            long_vowel_mode=current.long_vowel_mode,
        )

    def commit_generation_settings(
        self,
        generation_settings: GenerationSettings,
        *,
        active_preset_id: str | None | object = _UNSET,
        active_preset_display_name: str | None | object = _UNSET,
        request_save: bool = True,
    ) -> bool:
        if (
            self.ui_state.is_busy
            or self._pending_selected_event_projection is not None
            or not isinstance(generation_settings, GenerationSettings)
        ):
            return False
        current_output = self.ui_state.current_output_edit_state
        current = (
            current_output.generation_state
            if self.ui_state.output_edit_draft_dirty and current_output is not None
            else self.ui_state.generation_state
        )
        debug_payload = {
            "operation_kind": (
                "preset_apply"
                if active_preset_id is not _UNSET
                else "generation_settings"
            ),
            "closing_hold_frames": generation_settings.closing_hold_frames,
            "closing_softness_frames": generation_settings.closing_softness_frames,
            "long_vowel_mode": generation_settings.long_vowel_mode,
        }
        if active_preset_id is not _UNSET and active_preset_id is not None:
            debug_payload["preset_id"] = active_preset_id
        self.record_debug_action(
            "generation_settings_request",
            payload=debug_payload,
            status="started",
        )
        if generation_settings == current.generation_settings:
            if active_preset_id is _UNSET or active_preset_id == current.active_preset_id:
                self.record_debug_action(
                    "generation_settings_noop",
                    payload={"reason": "same_value"},
                    status="noop",
                )
                return False
        requested_id = None if active_preset_id is _UNSET else active_preset_id
        if (
            generation_settings == current.generation_settings
            and requested_id == current.active_preset_id
        ):
            return False
        candidate_generation = GenerationState(
            generation_settings=generation_settings,
            active_preset_id=requested_id,
            resolved_morph_name_set_id=current.resolved_morph_name_set_id,
        )
        try:
            direct_edit_guard = validate_active_profile_direct_edit(
                current_model_profile_state=self.ui_state.draft_model_profile_state,
                current_generation_settings=current.generation_settings,
                candidate_generation_settings=generation_settings,
                current_morph_upper_limit=(
                    current_output.morph_upper_limit
                    if current_output is not None
                    else self.ui_state.resolved_morph_upper_limit
                ),
                candidate_morph_upper_limit=(
                    current_output.morph_upper_limit
                    if current_output is not None
                    else self.ui_state.resolved_morph_upper_limit
                ),
            )
        except (TypeError, ValueError):
            self._project_generation_controls()
            self.record_debug_action(
                "generation_settings_rejected",
                payload={"reason": "profile_guard_input_invalid"},
                status="rejected",
            )
            return False
        if not direct_edit_guard.allowed:
            self._project_generation_controls()
            self.record_debug_action(
                "generation_settings_rejected",
                payload={"reason": "profile_guard_rejected"},
                status="rejected",
            )
            return False
        state = self.ui_state
        if state.output_edit_draft_dirty and active_preset_id is not _UNSET:
            self.right_pane.set_info_text(
                "先に変更を適用するか、Undo / Redoで適用済みの内容へ戻してください。"
            )
            self.record_debug_action(
                "generation_settings_rejected",
                payload={"reason": "unapplied_output_edits"},
                status="rejected",
            )
            return False
        if (
            active_preset_id is _UNSET
            and state.analysis_result_valid
            and not state.analysis_pending_rebuild
            and state.current_timing_plan is not None
        ):
            if state.output_edit_draft_baseline is None:
                state.initialize_output_edit_draft_baseline()
            draft_output = state.current_output_edit_state
            if draft_output is None:
                self.record_debug_action(
                    "generation_settings_rejected",
                    payload={"reason": "output_edit_history_unavailable"},
                    status="rejected",
                )
                return False
            base_input = self._build_current_base_timing_plan_input()
            if base_input is None:
                state.output_edit_apply_status = "現在の解析結果を編集表示へ反映できません。"
                self._project_output_edit_controls()
                self.sync_ui_state(adjustment_only=True)
                return False
            history_before_draft = state.output_edit_history_state
            try:
                draft_base = BaseTimingPlanInput(
                    timeline=base_input.timeline,
                    observations=base_input.observations,
                    source_duration_frames=base_input.source_duration_frames,
                    shape_parameters=ShapeParameters(
                        closing_hold_frames=generation_settings.closing_hold_frames,
                        closing_softness_frames=generation_settings.closing_softness_frames,
                        long_vowel_mode=generation_settings.long_vowel_mode,
                    ),
                )
                if not self._rebase_output_edit_draft(draft_base):
                    raise AdjustmentContractError("draft history could not be rebased")
                rebased_output = state.current_output_edit_state
                if rebased_output is None:
                    raise AdjustmentContractError("draft history is unavailable")
                candidate_output = OutputEditState(
                    base_plan_identity=rebased_output.base_plan_identity,
                    adjustment_snapshot=rebased_output.adjustment_snapshot,
                    generation_state=candidate_generation,
                    morph_upper_limit=rebased_output.morph_upper_limit,
                )
                if not state.commit_output_edit_state(
                    candidate_output,
                    model_profile_state=state.draft_model_profile_state,
                ):
                    raise AdjustmentContractError("draft history rejected the edit")
            except (AdjustmentContractError, TypeError, ValueError):
                state.output_edit_history_state = history_before_draft
                state._sync_legacy_adjustment_history()
                state.output_edit_apply_status = "設定を編集表示へ反映できませんでした。"
                self._project_output_edit_controls()
                self.record_debug_action(
                    "generation_settings_rejected",
                    payload={"reason": "draft_projection_failed"},
                    status="rejected",
                )
                self.sync_ui_state(adjustment_only=True)
                return False
            state.mark_output_edit_draft_changed()
            self.sync_ui_state(adjustment_only=True)
            self.record_debug_action(
                "generation_settings_drafted",
                payload=debug_payload,
                status="accepted",
            )
            return True
        state.clear_output_edit_draft()
        base_input = self._build_current_base_timing_plan_input()
        sync_context = None
        effective_plan = None
        if base_input is not None and self.ui_state.analysis_result_valid and not self.ui_state.analysis_pending_rebuild:
            snapshot = self.ui_state.current_adjustment_snapshot
            if snapshot is None:
                identity = build_base_plan_identity(base_input)
                snapshot = empty_adjustment_snapshot(identity)
            candidate_base = BaseTimingPlanInput(
                timeline=base_input.timeline,
                observations=base_input.observations,
                source_duration_frames=base_input.source_duration_frames,
                shape_parameters=ShapeParameters(
                    closing_hold_frames=generation_settings.closing_hold_frames,
                    closing_softness_frames=generation_settings.closing_softness_frames,
                    long_vowel_mode=generation_settings.long_vowel_mode,
                ),
            )
            try:
                effective_plan = (None if self._bounded_candidate_enabled() else
                                  resolve_effective_shape_plan(candidate_base, snapshot))
                sync_context = build_ui_sync_context(
                    candidate_base,
                    snapshot,
                    effective_plan_hint=effective_plan,
                    defer_resolution=self._bounded_candidate_enabled(),
                )
                candidate_output = OutputEditState(
                    base_plan_identity=sync_context.base_plan_identity,
                    adjustment_snapshot=snapshot,
                    generation_state=candidate_generation,
                    morph_upper_limit=self.ui_state.resolved_morph_upper_limit,
                )
            except (AdjustmentContractError, TypeError, ValueError):
                self._project_generation_controls()
                self.record_debug_action(
                    "generation_settings_rejected",
                    payload={"reason": "effective_shape_projection_failed"},
                    status="rejected",
                )
                return False
            if self.ui_state.output_edit_history_state is None:
                self.ui_state.initialize_adjustment_history(
                    snapshot,
                    expected_base_plan_identity_digest=sync_context.base_plan_identity.digest,
                )
            if not self.ui_state.commit_output_edit_state(candidate_output):
                self._project_generation_controls()
                self.record_debug_action(
                    "generation_settings_rejected",
                    payload={"reason": "output_edit_commit_rejected"},
                    status="rejected",
                )
                return False
            self.ui_state.generation_state = candidate_generation
            self._active_preset_display_name = (
                self._active_preset_display_name
                if active_preset_display_name is _UNSET
                and requested_id == current.active_preset_id
                else (
                    None
                    if active_preset_display_name is _UNSET
                    else active_preset_display_name
                )
            )
            self._project_generation_controls()
            self.ui_state.initialize_output_edit_draft_baseline()
            self.sync_ui_state(
                effective_plan_hint=effective_plan,
                adjustment_only=True,
            )
        else:
            self.ui_state.generation_state = candidate_generation
            self._active_preset_display_name = (
                self._active_preset_display_name
                if active_preset_display_name is _UNSET
                and requested_id == current.active_preset_id
                else (
                    None
                    if active_preset_display_name is _UNSET
                    else active_preset_display_name
                )
            )
            self._project_generation_controls()
            self.sync_ui_state()
        self.record_debug_action(
            "generation_settings_accepted",
            payload=debug_payload,
            status="accepted",
        )
        if request_save and self.controller:
            self.controller.request_settings_save()
        return True

    def apply_preset_generation(
        self,
        generation_settings: GenerationSettings,
        preset_id: str,
        display_name: str,
    ) -> bool:
        if type(preset_id) is not str or not preset_id:
            return False
        return self.commit_generation_settings(
            generation_settings,
            active_preset_id=preset_id,
            active_preset_display_name=display_name,
        )

    def show_vmd_save_dialog_and_get_path(self, default_dir: str):
        with wx.FileDialog(
            self,
            message="VMDファイルの保存先を指定してください",
            defaultDir=default_dir,
            wildcard="VMD files (*.vmd)|*.vmd",
            style=wx.FD_SAVE
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return None
            path = dialog.GetPath()
            if Path(path).suffix.lower() != ".vmd":
                path += '.vmd'
            return path

    def confirm_vmd_overwrite(self, path: str) -> bool:
        return wx.MessageBox(
            f"既存のVMDファイルを置き換えますか？\n\n{path}",
            "VMD上書きの確認",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            self,
        ) == wx.YES

    def confirm_vmd_save_warnings(
        self,
        snapshot: OutputDiagnosticsSnapshot,
    ) -> bool:
        summaries = tuple(
            item.summary
            for item in snapshot.items
            if item.severity is DiagnosticSeverity.WARNING
        )
        warning_lines = "\n".join(f"・{summary}" for summary in summaries)
        message = (
            "VMD出力に確認が必要な警告があります。\n"
            "RightPaneのWarningタブで詳細を確認できます。\n\n"
            f"{warning_lines}\n\n"
            "この状態でVMD保存を続行しますか？"
        )
        result = wx.MessageBox(
            message,
            "VMD保存前の確認",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
        )
        return result == wx.YES

    def show_mmd_wav_save_dialog_and_get_path(self, default_dir: str, default_name: str) -> str | None:
        with wx.FileDialog(
            self,
            message="MMD用WAVファイルの保存先を指定してください",
            defaultDir=default_dir,
            defaultFile=default_name,
            wildcard="WAVファイル (*.wav)|*.wav|すべてのファイル (*.*)|*.*",
            style=wx.FD_SAVE,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return None
            path = dialog.GetPath()
            if not path.lower().endswith(".wav"):
                path += ".wav"

        if os.path.exists(path):
            result = wx.MessageBox(
                "同名のWAVファイルが既に存在します。\n上書きしますか？",
                "上書き確認",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            if result != wx.YES:
                return None
        return path

    def show_mmd_wav_export_completed(self, output_path: str | os.PathLike[str]) -> None:
        absolute_path = Path(os.path.abspath(os.fspath(output_path)))
        message = (
            "MMD用WAVを出力しました。\n\n"
            f"ファイル名: {absolute_path.name}\n"
            f"フルパス: {absolute_path}"
        )
        dialog = wx.MessageDialog(
            self,
            message,
            "MMD用WAV出力完了",
            wx.OK | wx.ICON_INFORMATION,
        )
        try:
            dialog.ShowModal()
        finally:
            dialog.Destroy()

    def show_diagnostic_report_save_dialog_and_get_path(
        self,
        default_dir: str,
        default_name: str,
    ) -> str | None:
        with wx.FileDialog(
            self,
            message="診断レポートの保存先を指定してください",
            defaultDir=default_dir,
            defaultFile=default_name,
            wildcard="テキストファイル (*.txt)|*.txt|すべてのファイル (*.*)|*.*",
            style=wx.FD_SAVE,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return None
            path = dialog.GetPath()
            if not path.lower().endswith(".txt"):
                path += ".txt"

        if os.path.exists(path):
            result = wx.MessageBox(
                "同名の診断レポートが既に存在します。\n上書きしますか？",
                "上書き確認",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            if result != wx.YES:
                return None
        return path

    def show_delivery_destination_dialog(
        self,
        default_parent: str,
        default_folder: str,
        *,
        error_message: str | None = None,
    ) -> tuple[Path, str] | None:
        dialog = DeliveryDestinationDialog(
            self,
            default_parent=default_parent,
            default_folder=default_folder,
            error_message=error_message,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return None
            return dialog.get_selection()
        finally:
            dialog.Destroy()

    def confirm_long_audio_processing(self, duration_sec: float) -> bool:
        result = wx.MessageBox(
            f"音声の長さが {duration_sec:.1f} 秒あります。\n処理に時間がかかる可能性があります。続行しますか？",
            "長時間処理の確認",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            self,
        )
        return result == wx.YES

    def _build_recent_menus(self):
        st = self.ui_state
        from src.gui_wx.recent_files import RecentFilesManager
        rm = RecentFilesManager(st)
        
        valid_texts = rm.get_valid_text_files()
        valid_audios = rm.get_valid_audio_files()
        
        for item in self.recent_menu.GetMenuItems():
            self.recent_menu.Delete(item)
            
        for p in valid_texts:
            item = self.recent_menu.Append(wx.ID_ANY, f"TEXT: {os.path.basename(p)}")
            self.Bind(wx.EVT_MENU, lambda e, path=p: self._on_recent_text(path), item)
            
        if valid_texts and valid_audios:
            self.recent_menu.AppendSeparator()
            
        for p in valid_audios:
            item = self.recent_menu.Append(wx.ID_ANY, f"Audio: {os.path.basename(p)}")
            self.Bind(wx.EVT_MENU, lambda e, path=p: self._on_recent_audio(path), item)

        if self.controller:
            self.controller.request_settings_save()

    def _on_recent_text(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            wx.MessageBox("指定された履歴ファイルが見つかりません。", "読込エラー", wx.OK | wx.ICON_WARNING)
            self._build_recent_menus()
            return
        self._open_text_file(quiet_path=path)

    def _on_recent_audio(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            wx.MessageBox("指定された履歴ファイルが見つかりません。", "読込エラー", wx.OK | wx.ICON_WARNING)
            self._build_recent_menus()
            return
        if self.controller:
            self.controller.request_open_audio_file(path)
        
    def get_closing_softness_frames(self) -> int:
        return self.param_panel.get_closing_softness_frames()
        
    def set_closing_softness_frames(self, val: int):
        self.param_panel.set_closing_softness_frames(val)

    def _on_menu_exit(self, _event: wx.CommandEvent) -> None:
        """Route the File menu command through wx's close-event lifecycle."""
        self.Close()

    def _on_close(self, event: wx.CloseEvent):
        operation_handle = self._pending_exit_operation_handle
        if operation_handle is None:
            operation_handle = self._begin_debug_operation(
                "application_exit",
                entry="window_close",
            )

        def finish_close_attempt(status: str, reason_code: str) -> None:
            self._finish_debug_operation(
                operation_handle,
                status,
                reason_code=reason_code,
            )
            self._pending_exit_operation_handle = None
            if self.controller:
                self.controller.set_pending_exit_operation(None)

        if self.controller and self.controller.verified_vmd_save_may_be_active:
            if self.controller._verified_vmd_close_pending:
                event.Veto()
                return
            res = wx.MessageBox(
                "検証済みVMDを保存中です。キャンセルまたは確定完了まで待って終了しますか？",
                "終了の確認",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            if res != wx.YES:
                event.Veto()
                finish_close_attempt("cancelled", "close_confirmation_declined")
                return
            event.Veto()
            self._pending_exit_operation_handle = operation_handle
            self.controller.set_pending_exit_operation(operation_handle)
            self.controller.request_close_verified_vmd_save()
            return
        if self.controller and self.controller.delivery_may_be_active:
            if self.controller.delivery_close_pending:
                event.Veto()
                return
            if self.controller.is_delivery_active():
                res = wx.MessageBox(
                    "MMD一括出力中です。処理を中止または確定完了まで待って終了しますか？",
                    "終了の確認",
                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                    self,
                )
                if res != wx.YES:
                    event.Veto()
                    finish_close_attempt("cancelled", "close_confirmation_declined")
                    return
                event.Veto()
                self._pending_exit_operation_handle = operation_handle
                self.controller.set_pending_exit_operation(operation_handle)
                self.controller.request_close_delivery()
                return
            event.Veto()
            self.controller.set_pending_exit_operation(operation_handle)
            accepted = self.controller.request_exit()
            if not accepted:
                self._pending_exit_operation_handle = None
                self.controller.set_pending_exit_operation(None)
            return

        if getattr(self, 'ui_state', None) and self.ui_state.is_busy:
            if self.ui_state.audio_worker_active:
                res = wx.MessageBox(
                    "音声処理中です。中止してアプリケーションを終了しますか？",
                    "終了の確認",
                    wx.YES_NO | wx.ICON_QUESTION,
                    self
                )
                if res == wx.NO:
                    event.Veto()
                    finish_close_attempt("cancelled", "close_confirmation_declined")
                    return
                if self.controller:
                    self.controller.request_cancel_audio_worker()
            elif getattr(self, '_cancel_requested', False):
                res = wx.MessageBox(
                    "中止要求中ですが、アプリケーションを終了しますか？\n(終了するとそのまま閉じます)",
                    "終了の確認", 
                    wx.YES_NO | wx.ICON_QUESTION, 
                    self
                )
                if res == wx.NO:
                    event.Veto()
                    finish_close_attempt("cancelled", "close_confirmation_declined")
                    return
            else:
                res = wx.MessageBox(
                    "解析実行中です。中止してアプリケーションを終了しますか？",
                    "終了の確認",
                    wx.YES_NO | wx.ICON_QUESTION,
                    self
                )
                if res == wx.NO:
                    event.Veto()
                    finish_close_attempt("cancelled", "close_confirmation_declined")
                    return
                self._cancel_requested = True

        if self.controller:
            self.controller.set_pending_exit_operation(operation_handle)
            accepted = self.controller.request_exit()
            if not accepted:
                event.Veto()
                self._pending_exit_operation_handle = None
                self.controller.set_pending_exit_operation(None)
        else:
            self.prepare_for_confirmed_exit()
            self.Destroy()

    def prepare_for_confirmed_exit(self) -> None:
        if self._exit_prepared:
            return
        self._exit_prepared = True
        self.stop_output_edit_progress()
        self.right_pane.prepare_for_shutdown()
        active_job_id = self._active_analysis_job_id
        if self._analysis_info_in_progress or self._current_job_id is not None:
            self._current_job_id = None
            self._cleanup_analysis_job()
        if active_job_id is not None:
            self._finish_analysis_operation(
                active_job_id,
                "cancelled",
                reason_code="application_exit",
            )
            self._complete_analysis_terminal()
        if self._active_debug_trace is not None:
            active_trace = self._active_debug_trace
            self._active_debug_trace = None
            self._finish_debug_trace(
                active_trace,
                status="cancelled",
                reason_code="application_exit",
            )
        self._final_output_sync_coordinator.close()
        self._output_edit_draft_projection_coordinator.close()
        self.ui_state.final_output_state.invalidate(reason="application_shutdown")
        self._shutdown_debug_store()
        self.close_about_dialog()

    # --- UI Event Handlers ([MS13-B5] UI イベントを Action Sink へ流す) ---
    # --- メニューイベントハンドラはボタン側と同じ_openメソッドを呼ぶため削除 ---
    # def _on_mi_text_open(self, event) ... は直接 lambda 等で割り当てる

    def _on_mi_vmd_save(self, event):
        if self.controller: self.controller.request_save_vmd()

    def _on_mi_diagnostic_report_save(self, event):
        if self.controller:
            self.controller.request_save_diagnostic_report()

    def _on_mi_mmd_delivery_export(self, event):
        if self.controller:
            self.controller.request_export_delivery_package()

    def _on_mi_settings(self, event):
        if self.controller: self.controller.request_open_settings_dialog()

    def show_help_dialog(self) -> None:
        dialog = HelpDialog(self)
        try:
            dialog.ShowModal()
        finally:
            try:
                if not dialog.IsBeingDeleted():
                    dialog.Destroy()
            except RuntimeError:
                pass

    def show_about_dialog(self) -> None:
        existing = self._about_dialog
        if existing is not None:
            try:
                if not existing.IsBeingDeleted():
                    existing.Raise()
                    existing.SetFocus()
                    return
            except RuntimeError:
                pass
            self._about_dialog = None

        self._about_job_id += 1
        dialog = AboutDialog(self, job_id=self._about_job_id)
        self._about_dialog = dialog

        def clear_about_dialog(event: wx.WindowDestroyEvent) -> None:
            if self._about_dialog is dialog:
                self._about_dialog = None
            event.Skip()

        dialog.Bind(wx.EVT_WINDOW_DESTROY, clear_about_dialog)
        dialog.Show()

    def close_about_dialog(self) -> None:
        dialog = self._about_dialog
        if dialog is None:
            return
        try:
            if not dialog.IsBeingDeleted():
                dialog.Close()
        except RuntimeError:
            pass
        finally:
            self._about_dialog = None

    def _on_mi_help(self, event):
        if self.controller: self.controller.request_open_help()

    def _on_mi_about(self, event):
        if self.controller: self.controller.request_show_about()

    def _on_btn_open_text(self, event):
        self._open_text_file()

    def _on_btn_open_wav(self, event):
        self._open_audio_file()

    def _open_wav_file(self, quiet_path: str = None):
        """[Legacy] Delegate old WAV open hook to the MS17 audio open path."""
        if quiet_path is not None and not self.controller:
            analysis = analyze_wav_file(quiet_path)
            self.ui_state.selected_wav_path = quiet_path
            self.ui_state.selected_wav_analysis = analysis
            self.ui_state.last_wav_dialog_dir = os.path.dirname(quiet_path)
            self.ui_state.last_audio_dialog_dir = os.path.dirname(quiet_path)
            self.set_wav_path(os.path.basename(quiet_path))
            self.set_wav_info(
                f"Sample Rate: {analysis.sample_rate_hz}Hz\n"
                f"Channels: {analysis.channel_count}\n"
                f"Duration: {analysis.duration_sec:.2f}s"
            )
            self.ui_state.refresh_input_mode()
            if self.ui_state.analysis_start_ready:
                self.ui_state.mark_ready_for_analysis()
            else:
                self.ui_state.status_key = StatusKey.INPUT_MISSING
            self.sync_ui_state()
            return
        self._open_audio_file(quiet_path=quiet_path)
        
    def _open_audio_file(self, quiet_path: str = None):
        """ [MS17-B6] 音声ファイルを開き、Controllerへ処理を委譲する """
        operation_handle = None
        if quiet_path is None:
            operation_handle = self._begin_debug_operation(
                "audio_input_open",
                entry="file_dialog",
            )
            dialog_dir = self.ui_state.last_audio_dialog_dir or self.ui_state.last_wav_dialog_dir or ""
            with wx.FileDialog(
                self,
                message="音声ファイルを選択してください",
                defaultDir=dialog_dir,
                wildcard="Audio files (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    self._finish_debug_operation(
                        operation_handle,
                        "cancelled",
                        reason_code="file_dialog_cancelled",
                    )
                    return
                path = file_dialog.GetPath()
        else:
            path = quiet_path

        if not path:
            self._finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="empty_path",
            )
            return
            
        if self.controller:
            if operation_handle is None:
                operation_handle = self._begin_debug_operation(
                    "audio_input_open",
                    payload={"file_basename": os.path.basename(path)},
                    entry="recent_file",
                )
            self.controller.request_open_audio_file(
                path,
                _operation_handle=operation_handle,
                _entry="recent_file" if quiet_path is not None else "file_dialog",
            )
        else:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )
    def _open_text_file(self, quiet_path: str = None, auto_load_counterpart: bool = True):
        """ [MS14-B3] TEXTファイルを開き、処理してGUIに反映する """
        operation_handle = self._begin_debug_operation(
            "text_input_open",
            entry="recent_file" if quiet_path is not None else "file_dialog",
        )
        if quiet_path is None:
            dialog_dir = self.ui_state.last_text_dialog_dir or ""
            with wx.FileDialog(
                self,
                message="テキストファイルを選択してください",
                defaultDir=dialog_dir,
                wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    self._finish_debug_operation(
                        operation_handle,
                        "cancelled",
                        reason_code="file_dialog_cancelled",
                    )
                    return
                path = file_dialog.GetPath()
                self.ui_state.last_text_dialog_dir = file_dialog.GetDirectory()
        else:
            path = quiet_path

        # 妥当性確認
        if not path:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="empty_path",
            )
            return
        if not os.path.exists(path):
            if not quiet_path:
                wx.MessageBox("指定されたファイルが見つかりません。", "エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="input_file_missing",
            )
            return
        if os.path.isdir(path):
            if not quiet_path:
                wx.MessageBox("ファイルではなくディレクトリが選択されました。", "エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="input_not_file",
            )
            return

        # 読込ループ (想定外例外、UnicodeDecodeErrorを捕捉)
        text_content = ""
        try:
            for enc in ["utf-8-sig", "utf-8"]:
                try:
                    with open(path, "r", encoding=enc) as f:
                        text_content = f.read()
                    break
                except UnicodeDecodeError:
                    pass
            else:
                raise ValueError("未対応のエンコーディング")
        except Exception as e:
            if not quiet_path:
                wx.MessageBox(f"テキストの読み込み処理でエラーが発生しました。\n{e}", "読込エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="text_read_failed",
            )
            return

        # 変換
        try:
            clean_text = _validate_and_clean_text(text_content)
            hiragana = text_to_hiragana(text_content)
            vowel = hiragana_to_vowel_string(hiragana)
        except TextProcessingError as e:
            if not quiet_path:
                wx.MessageBox(f"テキストの変換処理でエラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="text_processing_failed",
            )
            return
        except Exception as e:
            if not quiet_path:
                wx.MessageBox(f"想定外の変換エラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="text_processing_failed",
            )
            return

        # State 更新
        if self.controller:
            self.controller.invalidate_audio_job_for_input_change()
        self.ui_state.selected_text_path = path
        self.ui_state.last_text_dialog_dir = os.path.dirname(path)
        self.ui_state.selected_text_content = clean_text
        self.ui_state.selected_hiragana_content = hiragana
        self.ui_state.selected_vowel_content = vowel
        self.ui_state.input_mode = INPUT_MODE_TEXT_AUDIO
        self.ui_state.clear_transcription_state()
        self.ui_state.invalidate_analysis()
        self.placeholder_container.set_preview_placeholder_text("テキストが変更されました。\n再解析が必要です。")

        # RECENT更新
        if path in self.ui_state.recent_text_files:
            self.ui_state.recent_text_files.remove(path)
        self.ui_state.recent_text_files.insert(0, path)
        self._build_recent_menus()
        if self.controller:
            self.controller.request_settings_save()

        # UI 反映
        basename = os.path.basename(path)
        self.info_panel.set_text_path(basename)
        self.info_panel.set_text_preview(clean_text)
        self.info_panel.set_hiragana_preview(hiragana)
        self.info_panel.set_vowel_preview(vowel)

        # Action State & Status 更新
        # auto load 試行前に一旦更新し、GUI全体の整合性を担保
        if self.ui_state.analysis_start_ready:
            self.ui_state.mark_ready_for_analysis()
        self.sync_ui_state()
        self._finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="text_input_loaded",
            payload={
                "file_basename": os.path.basename(path),
                "changed": True,
                "text_length": len(clean_text),
                "vowel_length": len(vowel),
            },
        )

        # Counterpart auto load
        if auto_load_counterpart:
            stem = Path(path).stem
            dir_path = Path(path).parent
            # .wav, .mp3, .m4a の順に探す
            for ext in [".wav", ".mp3", ".m4a"]:
                audio_path = str(dir_path / (stem + ext))
                if os.path.exists(audio_path):
                    if self.controller:
                        self.controller.request_open_audio_file(
                            audio_path,
                            _source="system",
                            _entry="text_counterpart",
                        )
                    break

    def show_audio_open_dialog(self) -> str | None:
        """ [MS17-B6] 音声ファイル選択ダイアログを表示 """
        dialog_dir = self.ui_state.last_audio_dialog_dir or self.ui_state.last_wav_dialog_dir or ""
        with wx.FileDialog(
            self,
            message="音声ファイルを選択してください",
            defaultDir=dialog_dir,
            wildcard="音声ファイル (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|WAVファイル (*.wav)|*.wav|MP3ファイル (*.mp3)|*.mp3|M4Aファイル (*.m4a)|*.m4a|すべてのファイル (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return None
            return file_dialog.GetPath()

    def _update_voice_only_text_previews(self, text: str):
        hiragana = text_to_hiragana(text)
        vowel = hiragana_to_vowel_string(hiragana)
        self.ui_state.selected_hiragana_content = hiragana
        self.ui_state.selected_vowel_content = vowel
        self.info_panel.set_text_preview(text)
        self.info_panel.set_hiragana_preview(hiragana)
        self.info_panel.set_vowel_preview(vowel)
        return hiragana, vowel

    def _on_transcription_apply(self, event):
        operation_handle = self._begin_debug_operation(
            "transcription_apply",
            payload={"text_length": len(self.info_panel.get_text_preview())},
            entry="button",
        )
        if self._reject_unapplied_output_edit():
            self._finish_debug_operation(
                operation_handle, "rejected", reason_code="unapplied_output_edits"
            )
            return
        if self.ui_state.input_mode != INPUT_MODE_VOICE_ONLY:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="voice_only_mode_required",
            )
            return
        edited_text = self.info_panel.get_text_preview()
        try:
            clean_text = _validate_and_clean_text(edited_text)
            self._update_voice_only_text_previews(clean_text)
        except TextProcessingError as e:
            wx.MessageBox(f"書き起こしテキストの変換処理でエラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="transcription_validation_failed",
            )
            return
        except Exception as e:
            wx.MessageBox(f"想定外の変換エラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="transcription_processing_failed",
            )
            return

        changed = clean_text != self.ui_state.transcription_text
        if changed:
            self.ui_state.apply_transcription_edit(clean_text)
            self.placeholder_container.set_preview_placeholder_text(
                "書き起こしが編集されました。\n再解析が必要です。"
            )
        else:
            self.ui_state.transcription_edit_dirty = False
        self.sync_ui_state()
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "noop",
            reason_code="transcription_applied" if changed else "no_change",
            payload={"changed": changed, "text_length": len(clean_text)},
        )

    def _on_transcription_revert(self, event):
        operation_handle = self._begin_debug_operation(
            "transcription_revert",
            entry="button",
        )
        if self.ui_state.input_mode != INPUT_MODE_VOICE_ONLY:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="voice_only_mode_required",
            )
            return
        original_text = self.ui_state.transcription_original_text
        if not original_text:
            self._finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="original_transcription_unavailable",
            )
            return
        try:
            self._update_voice_only_text_previews(original_text)
        except Exception as e:
            wx.MessageBox(f"書き起こしテキストの復元に失敗しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            self._finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="transcription_revert_failed",
            )
            return

        changed = self.ui_state.transcription_text != original_text
        if changed:
            self.ui_state.revert_transcription_edit()
            self.placeholder_container.set_preview_placeholder_text(
                "書き起こしを元に戻しました。\n再解析が必要です。"
            )
        else:
            self.ui_state.transcription_edit_dirty = False
        self.sync_ui_state()
        self._finish_debug_operation(
            operation_handle,
            "completed" if changed else "noop",
            reason_code="transcription_reverted" if changed else "no_change",
            payload={"changed": changed, "text_length": len(original_text)},
        )

    def _on_btn_process(self, event):
        self._run_analysis()

    def _capture_analysis_parameters(
        self,
        *,
        morph_upper_limit: float | None = None,
    ) -> AnalysisParameterSnapshot | None:
        try:
            return AnalysisParameterSnapshot(
                morph_upper_limit=(
                    self.get_morph_upper_limit()
                    if morph_upper_limit is None
                    else morph_upper_limit
                ),
            )
        except (TypeError, ValueError):
            return None

    def _build_base_timing_plan_input_for_plan(
        self,
        plan,
        *,
        generation_state: GenerationState | None = None,
    ) -> BaseTimingPlanInput | None:
        duration_sec = self._selected_audio_duration_sec()
        if plan is None or duration_sec is None:
            return None
        resolved_generation = generation_state or self.ui_state.generation_state
        try:
            return BaseTimingPlanInput(
                timeline=tuple(plan.timeline),
                observations=(
                    None
                    if not plan.observations
                    else tuple(plan.observations)
                ),
                source_duration_frames=source_duration_frames_from_seconds(
                    duration_sec
                ),
                shape_parameters=ShapeParameters(
                    closing_hold_frames=resolved_generation.generation_settings.closing_hold_frames,
                    closing_softness_frames=resolved_generation.generation_settings.closing_softness_frames,
                    long_vowel_mode=resolved_generation.generation_settings.long_vowel_mode,
                ),
            )
        except (AttributeError, TypeError, ValueError):
            return None

    def _selected_audio_duration_sec(self) -> float | None:
        """Return the best available duration for the current audio input.

        ``selected_wav_analysis`` is normally populated after the analysis WAV
        worker completes.  If that derived field is unavailable, the same
        loaded audio still retains duration metadata on the analysis-WAV or
        source-probe record.  The timing-plan contract needs only a finite
        non-negative duration, so use those metadata sources in precedence
        order instead of treating a valid timing plan as preview-less.
        """
        candidates = (
            ("selected_wav_analysis", self.ui_state.selected_wav_analysis),
            ("selected_analysis_wav", self.ui_state.selected_analysis_wav),
            ("selected_audio_probe", self.ui_state.selected_audio_probe),
        )
        observations = []
        for source_name, metadata in candidates:
            value = getattr(metadata, "duration_sec", None)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                observations.append({"source": source_name, "status": "invalid"})
                continue
            normalized = float(value)
            if math.isfinite(normalized) and normalized >= 0.0:
                observations.append(
                    {
                        "source": source_name,
                        "status": "candidate",
                        "duration_sec": normalized,
                    }
                )
                self._last_duration_selection_diagnostic = {
                    "status": "selected",
                    "candidates": [dict(item) for item in observations],
                    "selected_source": source_name,
                    "selected_duration_sec": normalized,
                }
                trace = self._debug_trace_for_current_projection()
                if trace is not None:
                    trace.record_stage(
                        "gui_duration_selection",
                        payload={
                            "candidates": observations,
                            "selected_source": source_name,
                            "selected_duration_sec": normalized,
                        },
                    )
                return normalized
            observations.append({"source": source_name, "status": "non_finite_or_negative"})
        self._last_duration_selection_diagnostic = {
            "status": "unavailable",
            "candidates": [dict(item) for item in observations],
            "selected_source": None,
            "selected_duration_sec": None,
        }
        trace = self._debug_trace_for_current_projection()
        if trace is not None:
            trace.record_stage(
                "gui_duration_selection",
                status="not_evaluable",
                reason_code="duration_unavailable",
                payload={"candidates": observations},
            )
        return None

    def _capture_analysis_rollback_snapshot(
        self,
        *,
        job_id: int,
        parameters: AnalysisParameterSnapshot,
    ) -> AnalysisRollbackSnapshot | None:
        state = self.ui_state
        if (
            not state.analysis_result_valid
            or state.analysis_pending_rebuild
            or state.current_timing_plan is None
            or state.has_pending_adjustment_change
        ):
            return None
        context = self._build_current_ui_sync_context()
        if context is None:
            return None
        history = state.adjustment_history_state
        selected_index = state.selected_source_event_index
        selected_digest = state.selected_base_plan_identity_digest
        if selected_index is not None and (
            selected_digest != context.base_plan_identity.digest
        ):
            return None
        try:
            return AnalysisRollbackSnapshot(
                job_id=job_id,
                timing_plan=state.current_timing_plan,
                base_plan_identity=context.base_plan_identity,
                adjustment_history_state=history,
                selected_source_event_index=selected_index,
                selected_base_plan_identity_digest=selected_digest,
                prior_diagnostic_failure=state.current_diagnostic_failure,
                parameters=parameters,
                output_edit_history_state=state.output_edit_history_state,
                generation_state=state.generation_state,
                model_profile_state=state.model_profile_state,
                model_key=state.whisper_model_selection.analysis_whisper_model_key,
                manifest_identity=(
                    state.whisper_model_selection.analysis_whisper_manifest_identity
                ),
            )
        except (TypeError, ValueError):
            return None

    def _can_restore_analysis_rollback(
        self,
        job_id: int,
        snapshot: AnalysisRollbackSnapshot | None,
        parameters: AnalysisParameterSnapshot | None,
    ) -> bool:
        comparison_input = (
            None
            if snapshot is None
            else self._build_base_timing_plan_input_for_plan(
                snapshot.timing_plan
            )
        )
        return can_restore_analysis_rollback(
            snapshot,
            job_id=job_id,
            comparison_base_input=comparison_input,
            current_parameters=parameters,
            current_model_profile_state=self.ui_state.model_profile_state,
            current_model_key=self.ui_state.whisper_model_selection.analysis_whisper_model_key,
            current_manifest_identity=(
                self.ui_state.whisper_model_selection.analysis_whisper_manifest_identity
            ),
        )

    def _restore_analysis_rollback(
        self,
        snapshot: AnalysisRollbackSnapshot,
    ):
        state = self.ui_state
        state.current_timing_plan = snapshot.timing_plan
        state.analysis_result_valid = True
        state.analysis_pending_rebuild = False
        state.adjustment_history_state = snapshot.adjustment_history_state
        state.output_edit_history_state = snapshot.output_edit_history_state
        state._observe_final_output_manual_snapshot()
        if snapshot.generation_state is not None:
            state.generation_state = snapshot.generation_state
            self._project_generation_controls()
        if snapshot.model_profile_state is not None:
            state.model_profile_state = snapshot.model_profile_state
        if snapshot.output_edit_history_state is not None:
            state._sync_legacy_adjustment_history()
        state.selected_source_event_index = snapshot.selected_source_event_index
        state.selected_base_plan_identity_digest = (
            snapshot.selected_base_plan_identity_digest
        )
        state.selected_event_editor_revision += 1

    def _is_current_analysis_terminal(self, job_id: int) -> bool:
        return bool(
            self
            and job_id == self._current_job_id
            and job_id == self._active_analysis_job_id
        )

    def _complete_analysis_terminal(self):
        pending_job_id = self._active_analysis_job_id
        if pending_job_id is not None:
            self.ui_state.final_output_state.discard_pending_analysis(
                job_id=pending_job_id
            )
        self._active_analysis_job_id = None
        self._analysis_parameter_snapshot = None
        self._analysis_rollback_snapshot = None

    def _finish_analysis_operation(
        self,
        job_id: int,
        status: str,
        *,
        reason_code: str,
        accepted_origin: object | None = None,
    ) -> None:
        handle = self._analysis_operation_handles.pop(job_id, None)
        if self.controller is None:
            return
        if handle is not None:
            self._finish_debug_operation(
                handle,
                status,
                reason_code=reason_code,
                accepted_origin=accepted_origin,
            )
            return
        matching_origin = accepted_origin
        if getattr(matching_origin, "job_id", None) != job_id:
            matching_origin = None
            final_state = self.ui_state.final_output_state
            for candidate in (
                getattr(final_state, "pending_origin", None),
                getattr(final_state, "accepted_origin", None),
            ):
                if getattr(candidate, "job_id", None) == job_id:
                    matching_origin = candidate
                    break
        self.controller.record_debug_operation_event(
            "analysis_run",
            "ignored" if status == "ignored" else status,
            source="worker",
            job_kind="analysis",
            job_id=job_id,
            analysis_run_id=getattr(matching_origin, "source_run_id", None),
            analysis_result_id=getattr(
                matching_origin,
                "analysis_result_id",
                None,
            ),
            reason_code=reason_code if handle is None else "start_not_recorded",
        )

    def _run_analysis(self):
        """ [MS14-B4] 解析実行の非同期起動 """
        if self._reject_unapplied_output_edit():
            return
        operation_handle = self._begin_debug_operation(
            "analysis_run",
            payload={
                "input_mode": self.ui_state.input_mode,
                "has_text_input": bool(self.ui_state.selected_text_content),
                "has_audio_input": bool(self.ui_state.audio_for_analysis_ready),
                "analysis_result_valid": bool(self.ui_state.analysis_result_valid),
            },
            entry="button",
            capture_current_origin=False,
        )

        def reject_request(reason_code: str) -> None:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=reason_code,
            )

        # 開始前の前提条件確認
        self.ui_state.refresh_input_mode()
        if self.ui_state.input_mode == INPUT_MODE_TEXT_AUDIO and not (
            self.ui_state.selected_text_path and self.ui_state.selected_text_content
        ):
            wx.MessageBox("TEXTが設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            reject_request("text_input_missing")
            return
        if not self.ui_state.audio_for_analysis_ready:
            wx.MessageBox("音声ファイルが設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            reject_request("audio_input_missing")
            return
        if not self.ui_state.analysis_start_ready:
            wx.MessageBox("解析に必要な入力が揃っていません。", "エラー", wx.OK | wx.ICON_ERROR)
            reject_request("analysis_inputs_incomplete")
            return
        whisper_summary = build_whisper_diagnostics_summary(
            self.ui_state,
            analysis_result_valid=self.ui_state.analysis_result_valid,
            analysis_pending_rebuild=self.ui_state.analysis_pending_rebuild,
            analysis_in_progress=False,
        )
        if whisper_summary.runtime_identity_status in {"incomplete", "mismatch"}:
            self.ui_state.whisper_model_selection = replace(
                self.ui_state.whisper_model_selection,
                whisper_failure_class="integrity_mismatch",
                whisper_failure_detail_code="runtime_identity_mismatch",
                whisper_failure_detail=None,
            )
            self.sync_ui_state(adjustment_only=True)
            wx.MessageBox(
                "Whisperモデルの実行状態を確認できないため、解析を開始できません。",
                "Whisperモデル確認エラー",
                wx.OK | wx.ICON_ERROR,
            )
            reject_request("runtime_identity_mismatch")
            return
        if (
            self.ui_state.input_mode == INPUT_MODE_VOICE_ONLY
            and self.info_panel.is_text_preview_editable()
            and self.info_panel.get_text_preview() != self.ui_state.transcription_text
        ):
            wx.MessageBox(
                "書き起こしテキストに未適用の編集があります。\n[適用] を押してから再解析してください。",
                "確認",
                wx.OK | wx.ICON_WARNING,
            )
            reject_request("transcription_edit_unapplied")
            return
        if self.ui_state.is_busy:
            reject_request("busy")
            return  # 二重実行防止
        if self._selected_event_editor_has_uncommitted_input():
            reject_request("selected_event_edit_uncommitted")
            return

        try:
            if self.controller is None:
                raise WhisperModelRuntimeError(
                    "model_unavailable",
                    "Whisper model controller is not available.",
                    failure_class="model_unavailable",
                )
            whisper_model_request = (
                self.controller.build_active_whisper_model_request()
            )
            if not isinstance(
                whisper_model_request,
                VerifiedAnalysisModelRequest,
            ):
                raise WhisperModelRuntimeError(
                    "model_unavailable",
                    "No verified Whisper model request was produced.",
                    failure_class="model_unavailable",
                )
        except WhisperModelRuntimeError as error:
            self.ui_state.whisper_model_selection = replace(
                self.ui_state.whisper_model_selection,
                whisper_failure_class=error.failure_class,
                whisper_failure_detail_code=error.code,
                whisper_failure_detail=str(error),
            )
            self.sync_ui_state(adjustment_only=True)
            wx.MessageBox(
                "解析に使用できる確認済みWhisperモデルがありません。\n"
                f"{format_whisper_failure_notice(error.code)}",
                "Whisperモデル確認エラー",
                wx.OK | wx.ICON_ERROR,
            )
            reject_request(error.code)
            return

        transcription_text_override = None
        retained_whisper_timing_result = None
        reuse_retained_timing = False
        if (
            self.ui_state.input_mode == INPUT_MODE_VOICE_ONLY
            and self.ui_state.analysis_pending_rebuild
            and self.ui_state.whisper_model_selection.analysis_rebuild_reason
            == "transcription_edit"
            and self.ui_state.analysis_text_content
        ):
            if self.ui_state.transcription_timing_result is None:
                wx.MessageBox(
                    "編集済みテキストを再解析するためのWhisper timing resultがありません。",
                    "エラー",
                    wx.OK | wx.ICON_ERROR,
                )
                reject_request("retained_timing_unavailable")
                return
            transcription_text_override = self.ui_state.analysis_text_content
            retained_whisper_timing_result = self.ui_state.transcription_timing_result
            reuse_retained_timing = True
            
        # UIからパラメータを取得
        upper_limit = self.ui_state.resolved_morph_upper_limit
        parameters = self._capture_analysis_parameters(
            morph_upper_limit=upper_limit,
        )
        if parameters is None:
            wx.MessageBox(
                "解析パラメータが不正です。",
                "エラー",
                wx.OK | wx.ICON_ERROR,
            )
            reject_request("analysis_parameters_invalid")
            return

        selected_analysis_wav = self.ui_state.selected_analysis_wav
        selected_analysis_wav_path = (
            None
            if selected_analysis_wav is None
            else getattr(selected_analysis_wav, "analysis_wav_path", None)
        )
        if selected_analysis_wav_path:
            try:
                wav_path = os.fspath(selected_analysis_wav_path)
            except TypeError:
                wav_path = None
        else:
            wav_path = self.ui_state.selected_wav_path
        if not isinstance(wav_path, str) or not wav_path:
            wx.MessageBox(
                "解析に使用する音声ファイルのパスを確認できません。音声を選択し直してください。",
                "エラー",
                wx.OK | wx.ICON_ERROR,
            )
            reject_request("analysis_audio_path_unavailable")
            return

        self._current_job_id += 1
        self._finish_current_adjustment_gesture()
        self._analysis_rollback_snapshot = (
            self._capture_analysis_rollback_snapshot(
                job_id=self._current_job_id,
                parameters=parameters,
            )
        )
        self._active_analysis_job_id = self._current_job_id
        self._analysis_parameter_snapshot = parameters
        self._cancel_requested = False
        self.ui_state.clear_output_diagnostics_state()

        if self.controller and self.ui_state.playback_active:
            self.controller.request_playback_stop(
                _source="system",
                _reason_code="analysis_started",
            )

        # Busy状態の開始
        self._analysis_info_in_progress = True
        self.ui_state.set_busy(True)
        self.sync_ui_state()
        
        self._progress_dialog = AnalysisProgressDialog(self, on_cancel_callback=self._on_analysis_cancel)
        self._progress_dialog.Show()

        analysis_text = (
            self.ui_state.selected_text_content
            or transcription_text_override
            or self.ui_state.analysis_text_content
        )
        final_output_origin = self.ui_state.final_output_state.begin_analysis(
            job_id=self._current_job_id,
            input_mode=self.ui_state.input_mode,
            source_audio_path=self.ui_state.selected_wav_path,
            analysis_wav_path=wav_path,
            text_path=self.ui_state.selected_text_path,
            analysis_text=analysis_text,
        )
        operation_handle = self._mark_debug_operation_started(
            operation_handle,
            job_kind="analysis",
            job_id=self._current_job_id,
            analysis_run_id=getattr(final_output_origin, "source_run_id", None),
            payload={"input_mode": self.ui_state.input_mode},
        )
        if operation_handle is not None:
            self._analysis_operation_handles[self._current_job_id] = operation_handle
        self.ui_state.confirmed_shared_warning_fingerprint = None

        if self._active_debug_trace is not None:
            self._finish_debug_trace(
                self._active_debug_trace,
                status="discarded",
                reason_code="superseded_before_terminal_callback",
            )
        self._active_debug_trace = None
        if self.ui_state.debug_mode_enabled:
            self._active_debug_trace = build_debug_trace(
                input_mode=self.ui_state.input_mode,
                job_id=self._current_job_id,
                source_audio_path=self.ui_state.selected_wav_path,
                analysis_wav_path=wav_path,
                text_path=self.ui_state.selected_text_path,
                analysis_text=analysis_text,
                model_identity=None,
                timing_source=self.ui_state.transcription_timing_source or "pending",
                selected_model_key=self.ui_state.whisper_model_selection.active_model_key,
                selected_wav_analysis=self.ui_state.selected_wav_analysis,
                settings_provenance=build_settings_provenance(
                    settings_store=(
                        self.controller.settings_store
                        if self.controller is not None
                        else None
                    ),
                    generation_settings=self.ui_state.generation_state.generation_settings,
                    active_preset_id=self.ui_state.generation_state.active_preset_id,
                    active_model_profile_id=(
                        self.ui_state.model_profile_state.active_model_profile_id
                    ),
                ),
                analysis_run_id=final_output_origin.source_run_id,
            )
            self._active_debug_trace.record_stage(
                "input_snapshot",
                payload={
                    "input_mode": self.ui_state.input_mode,
                    "job_id": self._current_job_id,
                    "has_text": bool(self.ui_state.selected_text_content),
                    "has_audio": bool(wav_path),
                    "timing_source": self.ui_state.transcription_timing_source or "pending",
                },
            )
            self._debug_store.submit(self._active_debug_trace)

        # worker起動
        self._worker = AnalysisWorker(
            job_id=self._current_job_id,
            callback=self._on_analysis_success,
            error_callback=self._on_analysis_error,
            phase_callback=self._on_analysis_phase,
            text_content=self.ui_state.selected_text_content,
            wav_path=wav_path,
            wav_analysis=self.ui_state.selected_wav_analysis,
            whisper_model_request=whisper_model_request,
            whisper_runtime=(
                self.controller.whisper_model_runtime
                if self.controller is not None
                else None
            ),
            upper_limit=upper_limit,
            input_mode=self.ui_state.input_mode,
            transcription_text_override=transcription_text_override,
            retained_whisper_timing_result=retained_whisper_timing_result,
            reuse_retained_timing=reuse_retained_timing,
            debug_trace=self._active_debug_trace,
            collect_transition_acoustics=(
                self._transition_evaluation_request is not None
                or self._bounded_candidate_enabled()
            ),
        )
        try:
            self._worker.start()
        except Exception:
            self._finish_analysis_operation(
                self._current_job_id,
                "failed",
                reason_code="analysis_worker_start_failed",
            )
            raise

        if self._timeout_timer:
            self._timeout_timer.Destroy()
        self._timeout_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timeout_warning, self._timeout_timer)
        self._timeout_timer.Start(150000, wx.TIMER_ONE_SHOT)

    def _on_analysis_cancel(self):
        self._cancel_requested = True
        job_id = self._active_analysis_job_id
        if self.controller and job_id is not None:
            handle = self._analysis_operation_handles.get(job_id)
            self.controller.record_debug_operation_phase(
                handle,
                "analysis_cancel_request",
                "requested",
                job_kind="analysis",
                job_id=job_id,
            )
        if self._timeout_timer:
            self._timeout_timer.Stop()

    def _on_analysis_phase(self, job_id, phase_name):
        if not self: return
        if not self._is_current_analysis_terminal(job_id): return
        if self._progress_dialog:
            self._progress_dialog.set_phase(phase_name)

    def _on_timeout_warning(self, event):
        if not self: return
        if self._cancel_requested: return
        if self._progress_dialog:
            self._progress_dialog.set_warning("※ 処理が長時間続いています。中止が必要な場合は [分析中止] を押してください。")

    def _cleanup_analysis_job(self):
        self._analysis_info_in_progress = False
        if self._progress_dialog:
            self._progress_dialog.Destroy()
            self._progress_dialog = None
        if self._timeout_timer:
            self._timeout_timer.Stop()
            self._timeout_timer.Destroy()
            self._timeout_timer = None
        self._worker = None

    def _finish_analysis_cancelled(
        self,
        job_id: int | None = None,
        snapshot: AnalysisRollbackSnapshot | None = None,
        parameters: AnalysisParameterSnapshot | None = None,
        debug_trace: AnalysisDebugTrace | None = None,
    ):
        if job_id is None:
            job_id = self._current_job_id
        if snapshot is None:
            snapshot = self._analysis_rollback_snapshot
        if parameters is None:
            parameters = self._capture_analysis_parameters()
        state = self.ui_state
        restored = self._can_restore_analysis_rollback(
            job_id,
            snapshot,
            parameters,
        )
        self._complete_analysis_terminal()
        if restored and snapshot is not None:
            self._restore_analysis_rollback(snapshot)
            state.current_diagnostic_failure = (
                snapshot.prior_diagnostic_failure
            )
            state.whisper_model_selection = replace(
                state.whisper_model_selection,
                whisper_failure_class="none",
                whisper_failure_detail_code=None,
                whisper_failure_detail=None,
            )
            state.analysis_cancelled = (
                snapshot.prior_diagnostic_failure is None
            )
            state.status_key = (
                StatusKey.ANALYSIS_CANCELLED
                if snapshot.prior_diagnostic_failure is None
                else StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK
            )
        else:
            model_changed = bool(
                snapshot is not None
                and (
                    state.whisper_model_selection.active_model_key
                    != snapshot.model_key
                    or state.whisper_model_selection.active_manifest_identity
                    != snapshot.manifest_identity
                )
            )
            if model_changed:
                state.invalidate_analysis()
                state.whisper_model_selection = replace(
                    state.whisper_model_selection,
                    analysis_rebuild_reason="model_changed",
                    whisper_failure_class="cancelled",
                    whisper_failure_detail_code="analysis_cancelled",
                    whisper_failure_detail=None,
                    analysis_whisper_model_key=None,
                    analysis_whisper_manifest_identity=None,
                    retained_whisper_model_key=None,
                    retained_whisper_timing_model_identity=None,
                )
            else:
                state.analysis_cancelled = True
                state.status_key = StatusKey.ANALYSIS_CANCELLED
        state.set_busy(False)
        self.sync_ui_state()
        self._finish_debug_trace(
            debug_trace,
            status="cancelled",
            reason_code="analysis_cancelled",
        )
        if job_id is not None:
            self._finish_analysis_operation(
                job_id,
                "cancelled",
                reason_code="analysis_cancelled",
            )

    def _finish_analysis_parameter_mismatch(
        self,
        debug_trace: AnalysisDebugTrace | None = None,
    ):
        job_id = self._active_analysis_job_id
        self._complete_analysis_terminal()
        self.ui_state.invalidate_analysis()
        self.ui_state.set_busy(False)
        self.sync_ui_state()
        self._finish_debug_trace(
            debug_trace,
            status="failed",
            reason_code="analysis_parameter_mismatch",
        )
        if job_id is not None:
            self._finish_analysis_operation(
                job_id,
                "failed",
                reason_code="analysis_parameter_mismatch",
            )

    def _on_analysis_success(self, job_id, result):
        """ [MS14-B4] 解析成功時のコールバック """
        if not self._is_current_analysis_terminal(job_id):
            self._finish_analysis_operation(
                job_id,
                "ignored",
                reason_code="stale_analysis_result",
            )
            return

        debug_trace = getattr(result, "debug_trace", None) or self._active_debug_trace
        self._active_debug_trace = None
        snapshot = self._analysis_rollback_snapshot
        expected_parameters = self._analysis_parameter_snapshot
        current_parameters = self._capture_analysis_parameters()
        self._cleanup_analysis_job()
        if current_parameters != expected_parameters:
            self._finish_analysis_parameter_mismatch(debug_trace)
            return
        if self._cancel_requested:
            self._finish_analysis_cancelled(
                job_id,
                snapshot,
                current_parameters,
                debug_trace,
            )
            return

        if isinstance(result, AnalysisWorkerResult):
            if result.model_identity is not None:
                active_state = self.ui_state.whisper_model_selection
                if (
                    result.model_identity.model_key
                    != active_state.active_model_key
                    or result.model_identity.manifest_identity
                    != active_state.active_manifest_identity
                ):
                    self.ui_state.invalidate_analysis()
                    self.ui_state.whisper_model_selection = replace(
                        active_state,
                        whisper_failure_class="integrity_mismatch",
                        whisper_failure_detail_code="runtime_identity_mismatch",
                        whisper_failure_detail=None,
                        analysis_whisper_model_key=None,
                        analysis_whisper_manifest_identity=None,
                        loaded_whisper_model_key=None,
                        loaded_whisper_manifest_identity=None,
                    )
                    self.ui_state.set_busy(False)
                    self._complete_analysis_terminal()
                    self.sync_ui_state()
                    self._finish_debug_trace(
                        debug_trace,
                        status="failed",
                        reason_code="runtime_identity_mismatch",
                    )
                    self._finish_analysis_operation(
                        job_id,
                        "failed",
                        reason_code="runtime_identity_mismatch",
                    )
                    wx.MessageBox(
                        "解析結果のWhisperモデルidentityが現在の設定と一致しません。",
                        "Whisperモデル確認エラー",
                        wx.OK | wx.ICON_ERROR,
                    )
                    return
            plan = result.timing_plan
            transcription_original_text = None
            transcription_is_edited = False
            if result.input_mode == INPUT_MODE_VOICE_ONLY:
                transcription_is_edited = result.analysis_text_source == "user_edited_transcription"
                if transcription_is_edited:
                    transcription_original_text = self.ui_state.transcription_original_text or result.transcription_text
                else:
                    transcription_original_text = result.transcription_text
            self.ui_state.mark_analysis_success(
                plan,
                input_mode=result.input_mode,
                analysis_text_content=result.analysis_text_content,
                analysis_text_source=result.analysis_text_source,
                transcription_text=result.transcription_text,
                transcription_source=result.transcription_source,
                transcription_timing_source=result.transcription_timing_source,
                transcription_original_text=transcription_original_text,
                transcription_is_edited=transcription_is_edited,
                transcription_timing_result=result.whisper_timing_result,
            )
            self.ui_state.whisper_model_selection = replace(
                self.ui_state.whisper_model_selection,
                loaded_whisper_model_key=(
                    result.model_identity.model_key
                    if result.model_identity is not None
                    else None
                ),
                loaded_whisper_manifest_identity=(
                    result.model_identity.manifest_identity
                    if result.model_identity is not None
                    else None
                ),
                analysis_whisper_model_key=(
                    result.model_identity.model_key
                    if result.model_identity is not None
                    else None
                ),
                analysis_whisper_manifest_identity=(
                    result.model_identity.manifest_identity
                    if result.model_identity is not None
                    else None
                ),
                retained_whisper_timing_model_identity=(
                    result.model_identity.manifest_identity
                    if result.model_identity is not None
                    else None
                ),
                retained_whisper_model_key=(
                    result.model_identity.model_key
                    if result.model_identity is not None
                    else None
                ),
                analysis_rebuild_reason="none",
                whisper_failure_class="none",
                whisper_failure_detail_code=None,
                whisper_failure_detail=None,
            )
            if result.input_mode == INPUT_MODE_VOICE_ONLY:
                self._update_voice_only_text_previews(result.transcription_text)
        else:
            plan = result
            self.ui_state.mark_analysis_success(
                plan,
                input_mode=INPUT_MODE_TEXT_AUDIO,
                analysis_text_content=self.ui_state.selected_text_content,
                analysis_text_source="text_file",
            )

        self._accepted_debug_trace = None
        if debug_trace is not None:
            analysis_result_id = debug_trace.adopt()
        else:
            analysis_result_id = uuid.uuid4().hex
        self._project_generation_controls()
        base_input = self._build_current_base_timing_plan_input()
        if base_input is not None:
            try:
                self._resolve_current_effective_plan(base_input)
            except (AdjustmentContractError, TypeError, ValueError):
                pass
        accepted_origin = self.ui_state.final_output_state.accept_analysis(
            job_id=job_id,
            adjustment_snapshot=self.ui_state.current_adjustment_snapshot,
            analysis_result_id=analysis_result_id,
        )
        if accepted_origin is not None:
            self.ui_state.initialize_output_edit_draft_baseline()
        if (
            debug_trace is not None
            and accepted_origin is not None
            and debug_trace.analysis_run_id == accepted_origin.source_run_id
            and debug_trace.analysis_result_id == accepted_origin.analysis_result_id
        ):
            self._accepted_debug_trace = debug_trace
        self.ui_state.set_busy(False)
        self._complete_analysis_terminal()
        self._selected_event_notice = ""
        self.sync_ui_state()
        self._finish_debug_trace(
            debug_trace,
            status="completed",
            reason_code="analysis_accepted",
        )
        self._finish_analysis_operation(
            job_id,
            "completed",
            reason_code=(
                "analysis_accepted"
                if accepted_origin is not None
                else "analysis_result_origin_unavailable"
            ),
            accepted_origin=accepted_origin,
        )
        if self.controller:
            self.controller.flush_pending_save()
            
    def _update_preview_display(
        self,
        *,
        sync_context: UiSyncContext | None = None,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None = None,
    ):
        if diagnostics_snapshot is None:
            diagnostics_snapshot = self.ui_state.current_output_diagnostics_snapshot
        plan = self.ui_state.current_timing_plan
        output_morph_names = self._resolved_output_morph_names()
        if diagnostics_snapshot is not None:
            preview_status = diagnostics_snapshot.whisper_summary.preview_projection_status
            if preview_status != "ready":
                self.ui_state.clear_selection()
                message = (
                    "再解析が必要です"
                    if preview_status == "analysis_required"
                    else "Preview表示に必要な解析結果がありません"
                )
                self.placeholder_container.set_preview_placeholder_text(
                    message,
                    output_morph_names=output_morph_names,
                )
                return
        if not plan:
            self._selected_event_notice = ""
            self.ui_state.clear_selection()
            self.placeholder_container.set_preview_placeholder_text(
                "未解析（テキストまたはWavが変更されました）",
                output_morph_names=output_morph_names,
            )
            return

        duration_sec = self._selected_audio_duration_sec()
        if duration_sec is None:
            duration_sec = 0.0
        if sync_context is None:
            sync_context = self._build_current_ui_sync_context()
        if sync_context is None:
            self.ui_state.clear_selection()
            if self._current_ui_sync_failure_reason == "base_input_unavailable":
                message = "Preview表示に必要な音声情報がありません"
            else:
                message = "Preview形状を生成できませんでした"
            self.placeholder_container.set_preview_placeholder_text(
                f"[解析結果あり]\n({message})",
                output_morph_names=output_morph_names,
            )
            return
        if self._restore_accepted_output_preview_if_current(
            sync_context.effective_plan,
            duration_sec,
        ):
            return
        try:
            effective_plan = sync_context.effective_plan
            preview_data = build_preview_data_from_effective_shape_plan(
                effective_plan,
                output_morph_names=output_morph_names,
            )
            preview_model = self.placeholder_container.pnl_preview.model
            current_digest = effective_plan.base_plan_identity.digest
            if self.ui_state.output_edit_draft_dirty:
                baseline = self.ui_state.output_edit_draft_baseline
                try:
                    current_keys = source_event_keys(plan.timeline)
                except (AdjustmentContractError, TypeError, ValueError):
                    current_keys = ()
                if (
                    baseline is not None
                    and current_keys == baseline.source_event_keys
                    and self.ui_state.selected_source_event_index is not None
                    and self.ui_state.selected_source_event_index < len(current_keys)
                ):
                    self.ui_state.selected_base_plan_identity_digest = current_digest
                else:
                    self.ui_state.clear_selection()
            elif (
                preview_model.base_plan_identity_digest is not None
                and preview_model.base_plan_identity_digest != current_digest
            ) or (
                self.ui_state.selected_base_plan_identity_digest is not None
                and self.ui_state.selected_base_plan_identity_digest != current_digest
            ):
                self.ui_state.clear_selection()
            self.placeholder_container.set_identity_aware_preview_data(
                preview_data,
                duration_sec,
                current_digest,
            )
        except Exception as e:
            self.ui_state.clear_selection()
            self.placeholder_container.set_preview_placeholder_text(
                f"[解析結果あり]\n(Preview表示エラー: {e})",
                output_morph_names=output_morph_names,
            )

    def _resolved_output_morph_names(self) -> tuple[str, ...]:
        output_state = self.ui_state.current_output_edit_state
        generation_state = (
            output_state.generation_state
            if self.ui_state.output_edit_draft_dirty and output_state is not None
            else self.ui_state.generation_state
        )
        return get_builtin_morph_name_set(
            generation_state.resolved_morph_name_set_id
        ).output_names

    def _build_current_base_timing_plan_input(self) -> BaseTimingPlanInput | None:
        state = self.ui_state
        plan = self._current_output_edit_draft_timing_plan()
        return self._build_base_timing_plan_input_for_plan(
            plan,
            generation_state=(
                state.current_output_edit_state.generation_state
                if state.output_edit_draft_dirty
                and state.current_output_edit_state is not None
                else state.generation_state
            ),
        )

    def _current_output_edit_draft_timing_plan(self):
        state = self.ui_state
        current = state.current_output_edit_state
        baseline = state.output_edit_draft_baseline
        if not state.output_edit_draft_dirty or current is None or baseline is None:
            return state.current_timing_plan
        if current.morph_upper_limit == baseline.output_state.morph_upper_limit:
            state.output_edit_draft_timing_plan = None
            state.output_edit_draft_timing_upper_limit = None
            return state.current_timing_plan
        if (
            state.output_edit_draft_timing_plan is not None
            and state.output_edit_draft_timing_upper_limit == current.morph_upper_limit
        ):
            return state.output_edit_draft_timing_plan
        try:
            projected = reproject_peak_values_for_upper_limit(
                state.current_timing_plan,
                current.morph_upper_limit,
            )
        except (AttributeError, TypeError, ValueError):
            state.output_edit_draft_error = "モーフ最大値の編集表示を更新できません。"
            return None
        state.output_edit_draft_timing_plan = projected
        state.output_edit_draft_timing_upper_limit = current.morph_upper_limit
        return projected

    def _rebase_output_edit_draft(
        self,
        base_input: BaseTimingPlanInput,
    ) -> bool:
        state = self.ui_state
        history = state.output_edit_history_state
        if history is None:
            return False
        baseline = state.output_edit_draft_baseline
        try:
            keys = (
                baseline.source_event_keys
                if baseline is not None
                else source_event_keys(
                    getattr(state.current_timing_plan, "timeline", ()) or ()
                )
            )
            rebased, _ = rebase_output_edit_history(
                history,
                keys,
                base_input,
            )
        except (AdjustmentContractError, TypeError, ValueError):
            return False
        state.output_edit_history_state = rebased
        state._sync_legacy_adjustment_history()
        return True

    def _on_analysis_error(self, job_id, error):
        """ [MS14-B4] 解析失敗時のコールバック """
        if not self._is_current_analysis_terminal(job_id):
            self._finish_analysis_operation(
                job_id,
                "ignored",
                reason_code="stale_analysis_error",
            )
            return

        debug_trace = self._active_debug_trace
        self._active_debug_trace = None
        failed_input_mode = self.ui_state.input_mode
        snapshot = self._analysis_rollback_snapshot
        expected_parameters = self._analysis_parameter_snapshot
        current_parameters = self._capture_analysis_parameters()
        self._cleanup_analysis_job()
        if current_parameters != expected_parameters:
            self._finish_analysis_parameter_mismatch(debug_trace)
            return
        if self._cancel_requested:
            self._finish_analysis_cancelled(
                job_id,
                snapshot,
                current_parameters,
                debug_trace,
            )
            return

        diagnostic_failure = build_diagnostic_failure_input(
            error,
            input_mode=failed_input_mode,
        )
        failure_class = getattr(error, "failure_class", None)
        detail_code = getattr(error, "detail_code", None) or getattr(error, "code", None)
        if not isinstance(failure_class, str):
            failure_class = "none"
        if not isinstance(detail_code, str) or not detail_code:
            detail_code = error.__class__.__name__
        else:
            detail_code = getattr(error, "detail_code", None) or getattr(error, "code", None)
        blocked_failure = is_rollback_forbidden_failure_class(failure_class)
        restored = (not blocked_failure) and self._can_restore_analysis_rollback(
            job_id,
            snapshot,
            current_parameters,
        )
        self._complete_analysis_terminal()
        if restored and snapshot is not None:
            self._restore_analysis_rollback(snapshot)
            self.ui_state.clear_output_diagnostics_state()
            self.ui_state.status_key = (
                StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK
            )
        else:
            self.ui_state.invalidate_analysis()
        self.ui_state.current_diagnostic_failure = diagnostic_failure
        self.ui_state.whisper_model_selection = replace(
            self.ui_state.whisper_model_selection,
            whisper_failure_class=failure_class,
            whisper_failure_detail_code=detail_code,
            whisper_failure_detail=str(error),
            analysis_whisper_model_key=None,
            analysis_whisper_manifest_identity=None,
            retained_whisper_model_key=None,
            retained_whisper_timing_model_identity=None,
        )
        self.ui_state.set_busy(False)
        self.sync_ui_state()
        self._finish_debug_trace(
            debug_trace,
            status="failed",
            reason_code=detail_code,
        )
        self._finish_analysis_operation(
            job_id,
            "failed",
            reason_code=detail_code,
        )
        if self.controller:
            self.controller.flush_pending_save()
        if failed_input_mode == INPUT_MODE_VOICE_ONLY:
            message = format_voice_only_analysis_error(error)
            title = "音声のみ解析エラー"
        else:
            message = (
                "解析中にエラーが発生しました。\n"
                f"{diagnostic_failure.summary}\n{diagnostic_failure.detail}"
            )
            title = "エラー"
        wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)

    def _on_btn_save_vmd(self, event):
        if self.controller: self.controller.request_save_vmd()

    def _on_mi_workspace_reset(self, event):
        operation_handle = self._begin_debug_operation(
            "workspace_reset",
            payload={
                "has_text_input": bool(self.ui_state.selected_text_path),
                "has_audio_input": bool(
                    self.ui_state.selected_audio_input or self.ui_state.selected_wav_path
                ),
            },
            entry="menu",
        )
        if self.ui_state.is_busy:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="busy",
            )
            return
        if self.ui_state.has_workspace_user_data and not self.confirm_workspace_reset():
            self._finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="workspace_reset_confirmation_declined",
            )
            return
        if self.controller:
            self.controller.request_reset_workspace(operation_handle)
        else:
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )

    def _on_btn_export_mmd_wav(self, event):
        if self.controller: self.controller.request_export_mmd_wav()

    def _on_btn_cancel_audio_worker(self, event):
        if self.controller: self.controller.request_cancel_audio_worker()

    def _on_btn_play(self, event):
        if self.controller: self.controller.request_playback_play()

    def _on_btn_pause(self, event):
        if self.controller: self.controller.request_playback_pause()

    def _on_btn_stop(self, event):
        if self.controller: self.controller.request_playback_stop()

    def _on_btn_zoom_in(self, event):
        if self.controller: self.controller.request_zoom_in()

    def _on_btn_zoom_out(self, event):
        if self.controller: self.controller.request_zoom_out()

    def _on_btn_zoom_reset(self, event):
        if self.controller: self.controller.request_zoom_reset()

    def _on_change_theme(self, mode: str):
        if self.controller: self.controller.request_change_theme(mode)
        
    def apply_theme(self, mode: str):
        """[MS15-B5] テーマを適用し、主要コンポーネントを再描画する"""
        ThemeManager.apply_theme(mode, self)
        self.right_pane.refresh_info_attention_style()
        self.right_pane.refresh_warning_styles()
        self.right_pane.refresh_selected_event_editor_styles()
        self.right_pane.refresh_preset_styles()
        self.right_pane.refresh_whisper_model_styles()
        self.update_theme_icons(ThemeManager.get_palette().is_dark)
        
        # Radio Itemのチェック状態を合わせる
        if mode == ThemeMode.SYSTEM:
            self.mi_theme_system.Check(True)
        elif mode == ThemeMode.LIGHT:
            self.mi_theme_light.Check(True)
        elif mode == ThemeMode.DARK:
            self.mi_theme_dark.Check(True)
            
        # 波形やプレビューなどの再描画
        if hasattr(self, 'placeholder_container'):
            if hasattr(self.placeholder_container, 'pnl_waveform'):
                self.placeholder_container.pnl_waveform.Refresh()
            if hasattr(self.placeholder_container, 'pnl_preview'):
                self.placeholder_container.pnl_preview.Refresh()
            self.placeholder_container.Refresh()
        if self._about_dialog is not None:
            try:
                if not self._about_dialog.IsBeingDeleted():
                    self._about_dialog.apply_theme(mode)
            except RuntimeError:
                self._about_dialog = None
        self.Refresh()

    def apply_settings(
        self,
        settings: dict,
        *,
        generation_state: GenerationState | None = None,
        active_preset_display_name: str | None = None,
        model_profile_state=None,
        active_model_profile_display_name: str | None = None,
        baseline_preset_display_name: str | None = None,
        resolved_morph_upper_limit: float | None = None,
        whisper_model_selection_state: WhisperModelSelectionState | None = None,
    ):
        """
        [MS13-B4] 起動時の設定反映。
        B3の時点で存在する wx 側の UI (メインフレームのサイズ等) に対してのみ設定を反映します。
        未配置の control (スプリッター等) への適用はスキップします。
        """
        # --- 1. ウィンドウ関連の設定適用 ---
        raw_width = settings.get("window_width")
        raw_height = settings.get("window_height")
        
        width = raw_width if isinstance(raw_width, int) and raw_width > 0 else 800
        height = raw_height if isinstance(raw_height, int) and raw_height > 0 else 600
        
        self.SetSize(wx.Size(width, height))
        self.Centre(wx.BOTH)
        
        # --- 2. B3 までの実在 UI に関する設定 ---
        # (現在、操作ボタンなどの表示状態に直接影響する初期設定項目はないため、ここで完了とする。)
        
        # [MS14-B5] 初期設定からrecent等を反映し、メニュー再構築する 
        # ui_stateにロードされた設定を反映
        self.ui_state.recent_text_files = settings.get("recent_text_files", [])
        self.ui_state.recent_wav_files = settings.get("recent_wav_files", [])
        self.ui_state.recent_audio_files = settings.get("recent_audio_files", [])
        self.ui_state.last_vmd_output_dir = settings.get("last_vmd_output_dir", "")
        self.ui_state.last_mmd_wav_export_dir = settings.get("last_mmd_wav_export_dir", "")
        self.ui_state.last_text_dialog_dir = settings.get("last_text_dialog_dir", "")
        self.ui_state.last_wav_dialog_dir = settings.get("last_wav_dialog_dir", "")
        self.ui_state.last_audio_dialog_dir = settings.get("last_audio_dialog_dir", "")
        
        # [MS15-B5] テーマの復元
        self.ui_state.theme_mode = settings.get("theme", ThemeMode.SYSTEM)
        self.apply_theme(self.ui_state.theme_mode)
        
        # invalid recent除去とメニュー構築（※この時点でのpruneによるsaveは最初の安全なタイミングに任せる）
        self._build_recent_menus()
        
        # パラメータ復元
        limit = settings.get("morph_upper_limit", 0.9)
        if resolved_morph_upper_limit is not None:
            limit = resolved_morph_upper_limit
        self._projection_guard = True
        try:
            self.set_morph_upper_limit(limit)
            self.ui_state.resolved_morph_upper_limit = limit
            if generation_state is None:
                generation_state = GenerationState(
                    generation_settings=GenerationSettings(
                        closing_hold_frames=settings.get("closing_hold_frames", 0),
                        closing_softness_frames=settings.get("closing_softness_frames", 0),
                        long_vowel_mode=settings.get("long_vowel_mode", "hold"),
                    ),
                    active_preset_id=settings.get("active_preset_id"),
                )
            self.ui_state.generation_state = generation_state
            if whisper_model_selection_state is not None:
                self.ui_state.whisper_model_selection = whisper_model_selection_state
            if model_profile_state is not None:
                self.ui_state.model_profile_state = model_profile_state
                self.ui_state.active_model_profile_display_name = (
                    active_model_profile_display_name
                )
                self.ui_state.baseline_preset_display_name = baseline_preset_display_name
            else:
                # Legacy callers may omit the MS23 profile projection.  Keep
                # the fallback generation state coherent instead of retaining
                # an active profile with missing display metadata.
                self.ui_state.model_profile_state = ModelProfileState(
                    active_model_profile_id=None,
                    active_profile_baseline_preset_id=None,
                    resolution_status=ModelProfileResolutionStatus.NO_PROFILE,
                )
                self.ui_state.active_model_profile_display_name = None
                self.ui_state.baseline_preset_display_name = None
            self._active_preset_display_name = active_preset_display_name
            self.set_closing_hold_frames(
                generation_state.generation_settings.closing_hold_frames
            )
            self.set_closing_softness_frames(
                generation_state.generation_settings.closing_softness_frames
            )
        finally:
            self._projection_guard = False
        
        # Parameter変更時のsaveコールバック
        self.param_panel.sc_morph_limit.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_morph_upper_changed)
        self.param_panel.sc_morph_limit.Bind(wx.EVT_TEXT, self._on_morph_upper_changed)
        self.param_panel.sc_hold_frames.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_output_setting_changed)
        self.param_panel.sc_hold_frames.Bind(wx.EVT_TEXT, self._on_output_setting_changed)
        self.param_panel.sc_softness_frames.Bind(wx.EVT_SPINCTRLDOUBLE, self._on_output_setting_changed)
        self.param_panel.sc_softness_frames.Bind(wx.EVT_TEXT, self._on_output_setting_changed)
        self.sync_ui_state()

    def _on_param_changed(self, event):
        # Compatibility entry point for existing callers/tests.
        self._on_morph_upper_changed(event)

    def _on_morph_upper_changed(self, event):
        event.Skip()
        if self._projection_guard:
            return
        state = self.ui_state
        previous_state = state.current_output_edit_state
        previous_upper = (
            state.resolved_morph_upper_limit
            if previous_state is None
            else previous_state.morph_upper_limit
        )
        candidate_upper = self.get_morph_upper_limit()
        operation_handle = self._begin_debug_operation(
            "morph_upper_limit_change",
            payload={"before": previous_upper, "after": candidate_upper},
            entry="parameter_control",
        )
        if self._pending_selected_event_projection is not None:
            self._projection_guard = True
            try:
                self.set_morph_upper_limit(previous_upper)
            finally:
                self._projection_guard = False
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="draft_projection_pending",
            )
            return
        try:
            direct_edit_guard = validate_active_profile_direct_edit(
                current_model_profile_state=state.draft_model_profile_state,
                current_generation_settings=(
                    previous_state.generation_state.generation_settings
                    if previous_state is not None
                    else state.generation_state.generation_settings
                ),
                candidate_generation_settings=(
                    previous_state.generation_state.generation_settings
                    if previous_state is not None
                    else state.generation_state.generation_settings
                ),
                current_morph_upper_limit=previous_upper,
                candidate_morph_upper_limit=candidate_upper,
            )
        except (TypeError, ValueError):
            direct_edit_guard = None
        if direct_edit_guard is None or not direct_edit_guard.allowed:
            self._projection_guard = True
            try:
                self.set_morph_upper_limit(previous_upper)
            finally:
                self._projection_guard = False
            self._finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=(
                    "profile_guard_input_invalid"
                    if direct_edit_guard is None
                    else direct_edit_guard.reason_code
                ),
                payload={"before": previous_upper, "after": candidate_upper},
            )
            return
        if candidate_upper == previous_upper:
            self._finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="morph_upper_limit_unchanged",
                payload={"before": previous_upper, "after": candidate_upper},
            )
            return
        if (
            state.analysis_result_valid
            and not state.analysis_pending_rebuild
            and state.current_timing_plan is not None
        ):
            if state.output_edit_draft_baseline is None:
                state.initialize_output_edit_draft_baseline()
            current_output = state.current_output_edit_state
            if current_output is None:
                state.output_edit_draft_error = "編集履歴を利用できません。"
                self._finish_debug_operation(
                    operation_handle,
                    "rejected",
                    reason_code="output_edit_history_unavailable",
                )
                return
            history_before_draft = state.output_edit_history_state
            try:
                draft_plan = reproject_peak_values_for_upper_limit(
                    state.current_timing_plan,
                    candidate_upper,
                )
                target_base = self._build_base_timing_plan_input_for_plan(
                    draft_plan,
                    generation_state=current_output.generation_state,
                )
                if target_base is None or not self._rebase_output_edit_draft(target_base):
                    raise AdjustmentContractError("draft base could not be rebased")
                rebased_output = state.current_output_edit_state
                if rebased_output is None:
                    raise AdjustmentContractError("draft history is unavailable")
                candidate_output = OutputEditState(
                    base_plan_identity=rebased_output.base_plan_identity,
                    adjustment_snapshot=rebased_output.adjustment_snapshot,
                    generation_state=rebased_output.generation_state,
                    morph_upper_limit=candidate_upper,
                )
                if not state.commit_output_edit_state(
                    candidate_output,
                    model_profile_state=state.draft_model_profile_state,
                ):
                    raise AdjustmentContractError("draft history rejected the edit")
                state.output_edit_draft_timing_plan = draft_plan
                state.output_edit_draft_timing_upper_limit = candidate_upper
                state.mark_output_edit_draft_changed()
            except (AdjustmentContractError, TypeError, ValueError):
                state.output_edit_history_state = history_before_draft
                state._sync_legacy_adjustment_history()
                state.output_edit_apply_status = "モーフ最大値を編集表示へ反映できませんでした。"
                self._projection_guard = True
                try:
                    self.set_morph_upper_limit(previous_upper)
                finally:
                    self._projection_guard = False
                self._finish_debug_operation(
                    operation_handle,
                    "rejected",
                    reason_code="draft_projection_failed",
                    payload={"before": previous_upper, "after": candidate_upper},
                )
                self.sync_ui_state(adjustment_only=True)
                return
            self.sync_ui_state(adjustment_only=True)
        else:
            state.resolved_morph_upper_limit = candidate_upper
            state.clear_output_diagnostics_state()
            if state.status_key == StatusKey.ANALYSIS_CANCELLED:
                state.status_key = (
                    StatusKey.READY_FOR_ANALYSIS
                    if state.analysis_start_ready
                    else StatusKey.INPUT_MISSING
                )
            self.sync_ui_state()
            if self.controller:
                self.controller.request_settings_save()
        self._finish_debug_operation(
            operation_handle,
            "completed" if candidate_upper != previous_upper else "noop",
            reason_code=(
                "morph_upper_limit_changed"
                if candidate_upper != previous_upper
                else "morph_upper_limit_unchanged"
            ),
            payload={
                "before": previous_upper,
                "after": candidate_upper,
                "changed": candidate_upper != previous_upper,
            },
        )

    def _on_output_setting_changed(self, event):
        event.Skip()
        if self._projection_guard:
            return
        try:
            settings = self._generation_settings_from_controls()
        except (TypeError, ValueError):
            self._project_generation_controls()
            return
        self.commit_generation_settings(settings)
