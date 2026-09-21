import math
import os
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

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
from gui_wx.output_diagnostics_adapter import (
    build_diagnostic_failure_input,
    build_whisper_diagnostics_summary,
    build_output_diagnostics_snapshot_from_ui_state,
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
    source_duration_frames_from_seconds,
)
from src.core.effective_shape_diagnostics import (
    ResolverDiagnosticsCollector,
)
from src.core.event_adjustment import AdjustmentContractError, empty_adjustment_snapshot
from src.core.event_adjustment_history import AdjustmentCoalescingKey
from src.core.output_edit_state import GenerationState, OutputEditState
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
from src.core.output_diagnostics import VmdWriterParameters
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from src.core.delivery_package import (
    DeliveryStartGateResult,
    evaluate_delivery_start_gate,
)
from gui_wx.selected_event_editor import (
    SelectedEventEditBoundaryRequest,
    SelectedEventEditRequest,
    build_selected_event_editor_state,
    merge_selected_event_edit,
    reset_selected_event_adjustment,
)
from gui_wx.theme import ThemeManager, ThemeMode
from gui_wx.help_about_dialogs import AboutDialog, HelpDialog
from src.core import DiagnosticSeverity, OutputDiagnosticsSnapshot
from src.core.whisper_model_runtime import WhisperModelRuntimeError


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
        self.btn_cancel = wx.Button(self, label="分析中止")
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
        self.browse_button = wx.Button(self, label="参照...")
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


class MainFrame(wx.Frame):
    """
    MMD_AutoLipTool のメインフレーム。
    [MS13-B3]
    - 上中下3領域へレイアウトする最小骨格の上に、
    - 最小メニューバー、主要ボタン、ステータス表示の受け口を配置。
    """
    def __init__(self, *args, **kw):
        if 'title' not in kw:
            kw['title'] = "MMD AutoLipTool"
        if 'size' not in kw:
            kw['size'] = (800, 600)
            
        super().__init__(*args, **kw)
        
        self.controller = None
        self.ui_state = UiState()
        self._current_job_id = 0
        self._cancel_requested = False
        self._progress_dialog = None
        self._timeout_timer = None
        self._worker = None
        self._analysis_info_in_progress = False
        self._active_analysis_job_id = None
        self._analysis_parameter_snapshot = None
        self._analysis_rollback_snapshot = None
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
        self._about_dialog: AboutDialog | None = None
        self._about_job_id = 0
        
        self._init_icon()
        self._init_menu()
        self._init_ui()
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
            "解析後の中間状態とPreview/Writer投影をdebugフォルダへ記録します（セッション限定）",
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
        self.Bind(wx.EVT_MENU, self._on_close, self.mi_exit)
        self.mi_help.Enable(True)
        self.mi_about.Enable(True)

    def _on_toggle_debug_mode(self, event: wx.CommandEvent):
        enabled = bool(event.IsChecked())
        self.ui_state.debug_mode_enabled = enabled
        self.mi_debug_mode.Check(enabled)

    def _debug_trace_for_current_projection(self) -> AnalysisDebugTrace | None:
        if not self.ui_state.debug_mode_enabled:
            return None
        trace = self._accepted_debug_trace
        if trace is None or self._analysis_info_in_progress:
            return None
        if not self.ui_state.analysis_result_valid or self.ui_state.analysis_pending_rebuild:
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

        diagnostics_operation = (
            self._debug_execution_operation(
                "completed", "success", "diagnostics_snapshot_ready"
            )
            if diagnostics_snapshot is not None
            else self._debug_execution_operation(
                "not_attempted", "not_evaluable", "diagnostics_snapshot_unavailable"
            )
        )
        preview_operation = (
            self._debug_execution_operation(
                "attempted",
                "success" if preview_result == "succeeded" else "failed",
                "preview_attempted"
                if preview_result == "succeeded"
                else "preview_model_unavailable",
            )
            if preview_result is not None
            else self._debug_execution_operation(
                "not_attempted", "not_evaluable", "not_attempted"
            )
        )
        writer_operation = (
            self._debug_execution_operation(
                "attempted",
                "success" if writer_result == "succeeded" else "failed",
                "writer_attempted"
                if writer_result == "succeeded"
                else "writer_adapter_failed",
            )
            if writer_result is not None
            else self._debug_execution_operation(
                "not_attempted", "not_evaluable", "not_attempted"
            )
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

        common_keys = sorted(set(preview_lookup).intersection(writer_lookup))
        comparison_points = []
        differences = []
        for frame_no, vowel in common_keys:
            preview_value = preview_lookup[(frame_no, vowel)]
            writer_value = writer_lookup[(frame_no, vowel)]
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
                        "within_tolerance": difference <= 1e-9,
                    }
                )
        missing_preview_keys = sorted(set(writer_lookup).difference(preview_lookup))
        missing_writer_keys = sorted(set(preview_lookup).difference(writer_lookup))
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
            status=(
                "not_evaluable"
                if not common_keys
                else (
                    "contract_violation"
                    if differences and max(differences) > 1e-9
                    else "completed"
                )
            ),
            reason_code=(
                "no_common_control_points"
                if not common_keys
                else ("projection_value_mismatch" if differences and max(differences) > 1e-9 else None)
            ),
            payload={
                "projection_revision": revision,
                "common_point_count": len(common_keys),
                "finite_point_count": len(differences),
                "max_abs_diff": max(differences) if differences else None,
                "within_tolerance": bool(differences) and max(differences) <= 1e-9,
                "tolerance": 1e-9,
                "comparison_basis": (
                    "common_raw_preview_and_normalized_writer_points"
                    "+sampled_silence_core_frames"
                ),
                "silence_policy": getattr(
                    effective_plan,
                    "silence_policy",
                    "not_available",
                ),
                "silence_core_curve_comparison": silence_curve_comparison,
                "points": comparison_points,
                "missing_preview_count": len(missing_preview_keys),
                "missing_writer_count": len(missing_writer_keys),
                "missing_preview_keys": missing_preview_keys,
                "missing_writer_keys": missing_writer_keys,
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

    def _set_button_icon(self, button: wx.Button, icon_filename: str, is_dark: bool):
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

    def update_theme_icons(self, is_dark: bool):
        if not hasattr(self, '_button_icons'):
            return
        for btn, filename in self._button_icons.items():
            self._set_button_icon(btn, filename, is_dark)

    def _init_top_panel(self):
        self.top_panel = wx.Panel(self.root_panel)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_open_text = wx.Button(self.top_panel, label="TEXT 読込")
        self.btn_open_wav = wx.Button(self.top_panel, label="音声 読込")
        self.btn_process = wx.Button(self.top_panel, label="解析実行")
        self.btn_save_vmd = wx.Button(self.top_panel, label="VMD 保存")
        self.btn_export_mmd_wav = wx.Button(self.top_panel, label="MMD用WAV出力")
        self.btn_export_mmd_wav.SetToolTip("MMDで読み込ませるためのWAVファイルを出力します。")
        self.btn_cancel_audio_worker = wx.Button(self.top_panel, label="キャンセル")
        self.btn_cancel_audio_worker.SetToolTip("音声変換・出力処理をキャンセルします。")
        
        self.btn_play = wx.Button(self.top_panel, label="Play")
        self.btn_stop = wx.Button(self.top_panel, label="Stop")
        
        self.btn_zoom_in = wx.Button(self.top_panel, label="Zoom In")
        self.btn_zoom_out = wx.Button(self.top_panel, label="Zoom Out")
        self.btn_zoom_reset = wx.Button(self.top_panel, label="Reset Zoom")
        
        self._button_icons = {
            self.btn_open_text: "textfileopen.png",
            self.btn_open_wav: "wavfileopen.png",
            self.btn_process: "execute.png",
            self.btn_save_vmd: "vmdsave.png",
            self.btn_play: "play.png",
            self.btn_stop: "stop.png",
            self.btn_zoom_in: "zoomin.png",
            self.btn_zoom_out: "zoomout.png"
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
        top_sizer.Add(self.btn_stop, 0, flags_btn | wx.RIGHT, 5)
        
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

    def _init_bottom_panel(self):
        self.bottom_panel = wx.Panel(self.root_panel)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.st_status_main = wx.StaticText(self.bottom_panel, label="準備完了 (WX Mode)")
        bottom_sizer.Add(self.st_status_main, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.bottom_panel.SetSizer(bottom_sizer)

    def _bind_button_events(self):
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_text, self.btn_open_text)
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_wav, self.btn_open_wav)
        self.Bind(wx.EVT_BUTTON, self._on_btn_process, self.btn_process)
        self.Bind(wx.EVT_BUTTON, self._on_btn_save_vmd, self.btn_save_vmd)
        self.Bind(wx.EVT_BUTTON, self._on_btn_export_mmd_wav, self.btn_export_mmd_wav)
        self.Bind(wx.EVT_BUTTON, self._on_btn_cancel_audio_worker, self.btn_cancel_audio_worker)
        self.Bind(wx.EVT_BUTTON, self._on_btn_play, self.btn_play)
        self.Bind(wx.EVT_BUTTON, self._on_btn_stop, self.btn_stop)
        
        self.Bind(wx.EVT_BUTTON, self._on_btn_zoom_in, self.btn_zoom_in)
        self.Bind(wx.EVT_BUTTON, self._on_btn_zoom_out, self.btn_zoom_out)
        self.Bind(wx.EVT_BUTTON, self._on_btn_zoom_reset, self.btn_zoom_reset)

    def sync_ui_state(
        self,
        *,
        effective_plan_hint: EffectiveShapePlan | None = None,
        adjustment_only: bool = False,
    ):
        """[MS15-B5] 統合UI状態同期メソッド"""
        sync_context = self._build_current_ui_sync_context(
            effective_plan_hint=effective_plan_hint,
        )
        self._current_ui_sync_context = sync_context
        (
            writer_state,
            effective_plan,
            failure_reason,
        ) = self.prepare_current_effective_output(sync_context=sync_context)
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

        self._update_preview_display(
            sync_context=sync_context,
            diagnostics_snapshot=diagnostics_snapshot,
        )
        self._record_debug_projection(
            sync_context=sync_context,
            diagnostics_snapshot=diagnostics_snapshot,
            effective_writer_input_state=writer_state,
            effective_writer_input_failure_reason=failure_reason,
        )

        # [MS16-B6] 選択状態の同期と RightPane への反映
        self.placeholder_container.set_selected_source_event_index(self.ui_state.selected_source_event_index)
        self.update_selected_event_display(sync_context=sync_context)

        if not adjustment_only:
            self.placeholder_container.Refresh()
            self.param_panel.Refresh()

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
        return "ready", sync_context.effective_plan, None

    def capture_current_delivery_state(
        self,
        *,
        ffmpeg_path: str | Path | None = None,
        confirmed_warning_save_state_fingerprint: str | None = None,
    ) -> DeliveryStartGateResult:
        """Capture one immutable B1 delivery candidate from the current UI state."""
        state = self.ui_state
        source_audio_path = resolve_source_audio_path_from_ui_state(state)
        audio_probe = state.selected_audio_probe
        writer_parameters = VmdWriterParameters(
            vmd_model_name="AutoLipTool",
            closing_hold_frames=self.get_closing_hold_frames(),
            closing_softness_frames=self.get_closing_softness_frames(),
        )
        if confirmed_warning_save_state_fingerprint is None:
            confirmed_warning_save_state_fingerprint = (
                state.confirmed_warning_save_state_fingerprint
            )

        if state.is_busy:
            return evaluate_delivery_start_gate(
                effective_shape_plan=None,
                diagnostics_snapshot=state.current_output_diagnostics_snapshot,
                audio_probe=audio_probe,
                source_audio_path=source_audio_path,
                mmd_wav_spec=MMD_WAV_SPEC,
                ffmpeg_path=ffmpeg_path,
                writer_parameters=writer_parameters,
                output_morph_names=None,
                effective_writer_input_state="not_applicable",
                confirmed_warning_save_state_fingerprint=(
                    confirmed_warning_save_state_fingerprint
                ),
                application_busy=True,
                analysis_in_progress=self._analysis_info_in_progress,
            )

        sync_context = self._build_current_ui_sync_context()
        if sync_context is None:
            effective_writer_input_state = "invalid"
            effective_shape_plan = None
            effective_writer_input_failure_reason = (
                self._current_ui_sync_failure_reason
                or "effective_shape_plan_unavailable"
            )
        else:
            (
                effective_writer_input_state,
                effective_shape_plan,
                effective_writer_input_failure_reason,
            ) = self.prepare_current_effective_output(sync_context=sync_context)

        output_morph_names = (
            self._resolved_output_morph_names()
            if effective_shape_plan is not None
            else None
        )
        try:
            snapshot = self.build_and_store_output_diagnostics_snapshot(
                effective_shape_plan=effective_shape_plan,
                effective_writer_input_state=effective_writer_input_state,
                effective_writer_input_failure_reason=(
                    effective_writer_input_failure_reason
                ),
                output_morph_names=output_morph_names,
            )
        except (AttributeError, TypeError, ValueError):
            snapshot = None
        return evaluate_delivery_start_gate(
            effective_shape_plan=effective_shape_plan,
            diagnostics_snapshot=snapshot,
            audio_probe=audio_probe,
            source_audio_path=source_audio_path,
            mmd_wav_spec=MMD_WAV_SPEC,
            ffmpeg_path=ffmpeg_path,
            writer_parameters=writer_parameters,
            output_morph_names=output_morph_names,
            effective_writer_input_state=effective_writer_input_state,
            confirmed_warning_save_state_fingerprint=(
                confirmed_warning_save_state_fingerprint
            ),
            application_busy=state.is_busy,
            analysis_in_progress=self._analysis_info_in_progress,
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

    def update_action_states(
        self,
        diagnostics_snapshot: OutputDiagnosticsSnapshot | None = None,
        *,
        sync_context: UiSyncContext | None = None,
    ):
        """
        [MS14-B2] UiState に基づき、UI コントロールの有効/無効を判定・反映する
        """
        state = self.ui_state
        busy = diagnostics_snapshot.whisper_summary.application_busy if diagnostics_snapshot else state.is_busy
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
            diagnostics_snapshot.saveability.vmd_save_allowed and not busy
        )
        source_audio_path = resolve_source_audio_path_from_ui_state(state)
        self.mi_diagnostic_report_save.Enable(
            not busy
            and source_audio_path is not None
            and bool(source_audio_path.stem)
        )
        self.mi_mmd_delivery_export.Enable(
            not busy
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
            not busy and state.model_profile_state.active_model_profile_id is None
        )

        # --- 解析実行 ---
        whisper_runtime_valid = (
            diagnostics_snapshot.whisper_summary.runtime_identity_status
            not in {"incomplete", "mismatch"}
        )
        can_analyze = state.analysis_start_ready and whisper_runtime_valid
        self.btn_process.Enable(can_analyze and not busy)

        # --- VMD 保存 ---
        self.btn_save_vmd.Enable(
            diagnostics_snapshot.saveability.vmd_save_allowed and not busy
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

        # [MS15-B5] 再生系の仮開放 ---
        can_play = state.playback_ready and not busy and not state.is_playing
        can_stop = state.is_playing # busy中もストップは可能とする
        self.btn_play.Enable(can_play)
        self.btn_stop.Enable(can_stop)
        
        # [MS15-B5] Zoom UI の仮開放
        if self.controller:
            zoom_state = self.controller.get_zoom_action_state()
            self.btn_zoom_in.Enable(zoom_state["zoom_in"])
            self.btn_zoom_out.Enable(zoom_state["zoom_out"])
            self.btn_zoom_reset.Enable(zoom_state["zoom_reset"])
        else:
            self.btn_zoom_in.Enable(False)
            self.btn_zoom_out.Enable(False)
            self.btn_zoom_reset.Enable(False)
        
        # 設定・ヘルプ
        self.mi_settings.Enable(False)
        self.mi_help.Enable(True)
        self.mi_about.Enable(True)

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
        active_state = self.ui_state.generation_state
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
        active_profile_id = self.ui_state.model_profile_state.active_model_profile_id
        if not self._model_profile_selection_initialized:
            self._selected_model_profile_id = (
                active_profile_id if active_profile_id in valid_ids else None
            )
            self._model_profile_selection_initialized = True
        elif self._selected_model_profile_id not in valid_ids and self._selected_model_profile_id is not None:
            self._selected_model_profile_id = (
                active_profile_id if active_profile_id in valid_ids else None
            )

        if active_profile_id is not None:
            self._sync_profile_display_names_from_state()
        active_profile_display_name = self.ui_state.active_model_profile_display_name
        active_baseline_id = (
            self.ui_state.model_profile_state.active_profile_baseline_preset_id
        )
        active_baseline = preset_by_id.get(active_baseline_id)
        active_preset_id = self.ui_state.generation_state.active_preset_id
        active_preset = preset_by_id.get(active_preset_id)
        active_morph_name_set = get_builtin_morph_name_set(
            self.ui_state.generation_state.resolved_morph_name_set_id
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
        if self.ui_state.is_busy or request.expected_panel_revision != self._preset_panel_revision:
            return
        valid_ids = {item.id for item in self._preset_store_items()}
        if request.selected_preset_id is not None and request.selected_preset_id not in valid_ids:
            self._set_preset_notice("選択したプリセットは現在利用できません。")
            return
        self._selected_preset_id = request.selected_preset_id
        self._set_preset_notice("")
        self._sync_preset_panel()

    def _on_preset_apply_request(self, request: PresetApplyRequest):
        if not isinstance(request, PresetApplyRequest):
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
        current = self.ui_state.generation_state
        if (
            current.active_preset_id == preset.id
            and current.generation_settings == preset.generation_settings
        ):
            self._set_preset_notice("選択中のプリセットは既に適用されています。")
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
        if not self._preset_request_is_current(request.expected_panel_revision):
            return
        if self.controller is None:
            return
        before_ids = {item.id for item in self.controller.preset_store.user_presets}
        result = self.controller.create_generation_preset(
            request.display_name,
            request.generation_settings,
        )
        if not result.succeeded:
            self._set_preset_notice(self._format_preset_mutation_error(result))
            self._sync_preset_panel()
            return
        created = next((item for item in result.user_presets if item.id not in before_ids), None)
        self._selected_preset_id = created.id if created is not None else self._selected_preset_id
        self._set_preset_notice("ユーザープリセットを作成しました。Applyで出力へ反映できます。")
        self._sync_preset_panel()

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
        if not self._preset_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            return
        if self.controller is None:
            return
        target = self.controller.lookup_generation_preset(request.preset_id)
        if target is None or target.source != "user":
            self._set_preset_notice("組み込みプリセットは変更できません。")
            return
        result = self.controller.update_generation_preset(
            request.preset_id,
            request.display_name,
            request.generation_settings,
        )
        if not result.succeeded:
            self._set_preset_notice(self._format_preset_mutation_error(result))
            self._sync_preset_panel()
            return
        self._selected_preset_id = request.preset_id
        self._normalize_active_preset_after_mutation()
        self._set_preset_notice("ユーザープリセットを更新しました。必要ならApplyしてください。")
        self._sync_preset_panel()

    def _on_preset_delete_request(self, request: PresetDeleteRequest):
        if not isinstance(request, PresetDeleteRequest):
            return
        if not self._preset_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            return
        if self.controller is None:
            return
        target = self.controller.lookup_generation_preset(request.preset_id)
        if target is None or target.source != "user":
            self._set_preset_notice("組み込みプリセットは削除できません。")
            return
        result = self.controller.delete_generation_preset(request.preset_id)
        if not result.succeeded:
            self._set_preset_notice(self._format_preset_mutation_error(result))
            self._sync_preset_panel()
            return
        self._normalize_active_preset_after_mutation()
        active_id = self.ui_state.generation_state.active_preset_id
        self._selected_preset_id = active_id if active_id != request.preset_id else None
        self._set_preset_notice("ユーザープリセットを削除しました。")
        self._sync_preset_panel()

    def _on_model_profile_select_request(
        self,
        request: ModelProfileSelectRequest,
    ) -> None:
        if not isinstance(request, ModelProfileSelectRequest):
            return
        if (
            self.ui_state.is_busy
            or request.expected_panel_revision != self._model_profile_panel_revision
        ):
            return
        valid_ids = {item.id for item in self._profile_store_items()}
        if (
            request.selected_profile_id is not None
            and request.selected_profile_id not in valid_ids
        ):
            self._set_model_profile_notice("選択したモデルプロファイルは現在利用できません。")
            return
        self._selected_model_profile_id = request.selected_profile_id
        self._set_model_profile_notice("")
        self._sync_model_profile_panel()

    def _on_whisper_model_select_request(
        self,
        request: WhisperModelSelectRequest,
    ) -> None:
        if not isinstance(request, WhisperModelSelectRequest):
            return
        state = self.ui_state.whisper_model_selection
        if (
            self.ui_state.is_busy
            or state.management_busy
            or request.expected_panel_revision != state.panel_revision
        ):
            return
        valid_keys = {spec.model_key for spec in state.model_specs}
        if request.selected_model_key not in valid_keys:
            self.ui_state.whisper_model_selection = replace(
                state,
                notice="選択したWhisperモデルは現在利用できません。",
            )
            self.sync_ui_state(adjustment_only=True)
            return
        if request.selected_model_key == state.selected_model_key:
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

    def _on_whisper_model_download_request(
        self,
        request: WhisperModelDownloadRequest,
    ) -> None:
        if not isinstance(request, WhisperModelDownloadRequest):
            return
        if self.controller is None:
            return
        state = self.ui_state.whisper_model_selection
        spec = next(
            (item for item in state.model_specs if item.model_key == request.model_key),
            None,
        )
        if spec is None:
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
            return
        self.controller.start_whisper_model_download(
            request.model_key,
            request.expected_panel_revision,
            confirmed=True,
        )

    def _on_whisper_model_apply_request(
        self,
        request: WhisperModelApplyRequest,
    ) -> None:
        if not isinstance(request, WhisperModelApplyRequest):
            return
        if self.controller is None:
            return
        state = self.ui_state.whisper_model_selection
        item = next(
            (item for item in state.model_specs if item.model_key == request.model_key),
            None,
        )
        if item is None:
            return
        if wx.MessageBox(
            f"{item.display_name} を次回解析に適用します。\n\n"
            "適用後は現在の解析結果を無効化し、確認済みモデルで再解析します。\n"
            "適用しますか？",
            "Whisperモデル適用確認",
            wx.YES_NO | wx.ICON_INFORMATION,
        ) != wx.YES:
            return
        self.controller.start_whisper_model_apply(
            request.model_key,
            request.expected_panel_revision,
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
        if self.controller is None:
            return
        state = self.ui_state.whisper_model_selection
        item = next(
            (item for item in state.model_specs if item.model_key == request.model_key),
            None,
        )
        if item is None:
            return
        if wx.MessageBox(
            f"{item.display_name} の検証済みモデルを削除します。\n\n"
            "現在の解析で使用中の場合は削除できません。\n"
            "削除後は必要に応じて、明示的に再取得してください。\n\n"
            "削除しますか？",
            "Whisperモデルの削除確認",
            wx.YES_NO | wx.ICON_WARNING,
        ) != wx.YES:
            return
        self.controller.start_whisper_model_delete(
            request.model_key,
            request.expected_panel_revision,
            confirmed=True,
        )

    def _on_whisper_storage_root_request(
        self,
        request: WhisperStorageRootRequest,
    ) -> None:
        if not isinstance(request, WhisperStorageRootRequest):
            return
        if self.controller is None:
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
                return
            selected_path = dialog.GetPath()
        finally:
            dialog.Destroy()
        if not selected_path:
            return
        if wx.MessageBox(
            f"Whisperモデルの保存先を次へ変更します。\n\n{selected_path}\n\n"
            "この変更ではネットワーク接続やモデル取得は開始しません。\n"
            "保存先を変更しますか？",
            "Whisperモデル保存先の確認",
            wx.YES_NO | wx.ICON_INFORMATION,
        ) != wx.YES:
            return
        self.controller.change_whisper_storage_root(
            selected_path,
            request.expected_panel_revision,
            confirmed=True,
        )

    def _on_model_profile_apply_request(
        self,
        request: ModelProfileApplyRequest,
    ) -> None:
        if not isinstance(request, ModelProfileApplyRequest):
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
        if not self._model_profile_request_is_current(request.expected_panel_revision):
            return
        if self.controller is None:
            return
        before_ids = {item.id for item in self.controller.profile_store.user_profiles}
        values = request.values
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

    def _on_model_profile_update_request(
        self,
        request: ModelProfileUpdateRequest,
    ) -> None:
        if not isinstance(request, ModelProfileUpdateRequest):
            return
        if not self._model_profile_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            return
        if request.profile_id != self._selected_model_profile_id or self.controller is None:
            return
        values = request.values
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
            return
        self._selected_model_profile_id = request.profile_id
        if self.ui_state.model_profile_state.active_model_profile_id == request.profile_id:
            self._sync_profile_display_names_from_state()
        self._set_model_profile_notice("モデルプロファイルを更新しました。必要ならApplyしてください。")
        self.sync_ui_state()

    def _on_model_profile_delete_request(
        self,
        request: ModelProfileDeleteRequest,
    ) -> None:
        if not isinstance(request, ModelProfileDeleteRequest):
            return
        if not self._model_profile_request_is_current(
            request.expected_panel_revision,
            expected_editor_revision=request.expected_editor_revision,
        ):
            return
        if request.profile_id != self._selected_model_profile_id or self.controller is None:
            return
        result = self.controller.delete_model_profile(request.profile_id)
        if not result.succeeded:
            self._set_model_profile_notice(self._format_model_profile_mutation_error(result))
            self._sync_model_profile_panel()
            return
        valid_ids = {item.id for item in result.user_profiles}
        active_id = self.ui_state.model_profile_state.active_model_profile_id
        self._selected_model_profile_id = active_id if active_id in valid_ids else None
        self._set_model_profile_notice("モデルプロファイルを削除しました。")
        self.sync_ui_state()


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
        """[MS15-B3] 再生位置を waveform と Preview の両方へ通知する"""
        self.placeholder_container.set_playback_position_sec(position_sec)
        self._sync_playback_context()

    def _sync_playback_context(self):
        state = self.ui_state
        plan = state.current_timing_plan
        timeline = getattr(plan, "timeline", None) if plan is not None else None
        context = build_playback_info_context(
            is_playing=state.is_playing,
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
        if not isinstance(request, PreviewSelectionRequest) or self.ui_state.is_busy:
            return
        preview_model = self.placeholder_container.pnl_preview.model
        if (
            not preview_model.is_valid
            or request.render_revision != preview_model.render_revision
            or request.base_plan_identity_digest != preview_model.base_plan_identity_digest
        ):
            return
        base_input = self._build_current_base_timing_plan_input()
        if base_input is None:
            return
        try:
            current_digest = build_base_plan_identity(base_input).digest
        except Exception:
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
            return
        self._selected_event_notice = ""
        self.placeholder_container.set_selected_source_event_index(request.base_event_index)
        self.update_selected_event_display()
        self.right_pane.show_selected_event_tab()

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
                sync_context = self._build_current_ui_sync_context()
            if sync_context is not None:
                try:
                    editor_state = build_selected_event_editor_state(
                        sync_context.effective_plan,
                        selected_index,
                        expected_base_identity_digest=selected_digest,
                        editor_revision=state.selected_event_editor_revision,
                        source_duration_frames=(
                            sync_context.base_input.source_duration_frames
                        ),
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
            sync_context = self._build_current_ui_sync_context()
        if snapshot is None or sync_context is None:
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
        if (
            state.is_busy
            or not self._adjustment_history_matches_current_base()
            or self._selected_event_editor_has_uncommitted_input()
        ):
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
            return False
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
        self.sync_ui_state(adjustment_only=True)
        if (
            self.controller
            and before_persistent_projection != self._persistent_generation_projection()
        ):
            self.controller.request_settings_save()
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
        profile_id = self.ui_state.model_profile_state.active_model_profile_id
        baseline_id = self.ui_state.model_profile_state.active_profile_baseline_preset_id
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
        if (
            state.is_busy
            or not state.has_event_adjustments
            or not self._adjustment_history_matches_current_base()
            or self._selected_event_editor_has_uncommitted_input()
        ):
            return
        snapshot = state.current_adjustment_snapshot
        if snapshot is None:
            return
        self._finish_current_adjustment_gesture()
        reset_snapshot = empty_adjustment_snapshot(snapshot.base_plan_identity)
        if not state.commit_adjustment_snapshot(
            reset_snapshot,
            expected_base_plan_identity_digest=(
                snapshot.base_plan_identity.digest
            ),
        ):
            return
        self._selected_event_notice = "すべての出力編集をリセットしました。"
        self.sync_ui_state(adjustment_only=True)

    def _on_selected_event_edit_request(self, request: SelectedEventEditRequest):
        state = self.ui_state
        if not isinstance(request, SelectedEventEditRequest) or state.is_busy:
            return
        if (
            request.base_event_index != state.selected_source_event_index
            or request.base_identity_digest
            != state.selected_base_plan_identity_digest
            or request.editor_revision != state.selected_event_editor_revision
        ):
            return
        base_input = self._build_current_base_timing_plan_input()
        snapshot = state.current_adjustment_snapshot
        if base_input is None or snapshot is None:
            return
        try:
            requested_change = merge_selected_event_edit(snapshot, request)
            result = apply_adjustment_update(
                base_input,
                snapshot,
                requested_change,
            )
        except (AdjustmentContractError, TypeError, ValueError) as error:
            message = f"補正を適用できません: {error}"
            self.update_selected_event_display()
            self.right_pane.set_selected_event_editor_error(
                message
            )
            return
        if result.canonical_snapshot == snapshot:
            self.update_selected_event_display()
            return
        notice_parts = []
        if result.removed_tail_override_event_indices:
            indices = ", ".join(
                str(index)
                for index in result.removed_tail_override_event_indices
            )
            notice_parts.append(
                f"group変更によりEvent {indices}の末尾補正を解除しました。"
            )
        if result.removed_slope_override_event_indices:
            indices = ", ".join(
                str(index)
                for index in result.removed_slope_override_event_indices
            )
            notice_parts.append(
                "閉口スムーズが反映されなくなったため、"
                f"Event {indices}の閉口傾斜比を解除しました。"
            )
        notice_parts.append("出力編集はPreviewとVMD保存へ反映されます。")
        coalesce_key = None
        if request.coalescing_token is not None:
            try:
                coalesce_key = self._build_adjustment_coalescing_key(
                    base_identity_digest=request.base_identity_digest,
                    base_event_index=request.base_event_index,
                    field=request.field,
                    coalescing_token=request.coalescing_token,
                )
            except (AdjustmentContractError, TypeError, ValueError):
                return
        if not state.commit_adjustment_snapshot(
            result.canonical_snapshot,
            expected_base_plan_identity_digest=request.base_identity_digest,
            coalesce_key=coalesce_key,
        ):
            return
        self._selected_event_notice = "\n".join(notice_parts)
        self.sync_ui_state(
            effective_plan_hint=result.effective_plan,
            adjustment_only=True,
        )

    def _on_selected_event_reset_request(
        self,
        base_event_index: int,
        base_identity_digest: str,
        editor_revision: int,
    ):
        state = self.ui_state
        if (
            state.is_busy
            or base_event_index != state.selected_source_event_index
            or base_identity_digest != state.selected_base_plan_identity_digest
            or editor_revision != state.selected_event_editor_revision
        ):
            return
        base_input = self._build_current_base_timing_plan_input()
        snapshot = state.current_adjustment_snapshot
        if base_input is None or snapshot is None:
            return
        self._finish_current_adjustment_gesture()
        try:
            result = apply_adjustment_update(
                base_input,
                snapshot,
                reset_selected_event_adjustment(snapshot, base_event_index),
            )
        except (AdjustmentContractError, TypeError, ValueError) as error:
            message = f"補正をリセットできません: {error}"
            self.update_selected_event_display()
            self.right_pane.set_selected_event_editor_error(
                message
            )
            return
        if result.canonical_snapshot == snapshot:
            return
        if not state.commit_adjustment_snapshot(
            result.canonical_snapshot,
            expected_base_plan_identity_digest=base_identity_digest,
        ):
            return
        notices = ["選択イベントの出力編集をリセットしました。"]
        if result.removed_tail_override_event_indices:
            notices.append("group変更により他イベントの末尾補正も解除しました。")
        if state.has_event_adjustments:
            notices.append(
                "他イベントの出力編集はPreviewとVMD保存へ反映されます。"
            )
        self._selected_event_notice = "\n".join(notices)
        self.sync_ui_state(
            effective_plan_hint=result.effective_plan,
            adjustment_only=True,
        )
        
    def get_morph_upper_limit(self) -> float:
        return self.param_panel.get_morph_upper_limit()
        
    def set_morph_upper_limit(self, val: float):
        self.param_panel.set_morph_upper_limit(val)
        if not self._projection_guard:
            self.ui_state.resolved_morph_upper_limit = val
        
    def get_closing_hold_frames(self) -> int:
        return self.param_panel.get_closing_hold_frames()
        
    def set_closing_hold_frames(self, val: int):
        self.param_panel.set_closing_hold_frames(val)
        
    def get_closing_softness_frames(self) -> int:
        return self.param_panel.get_closing_softness_frames()
        
    def set_closing_softness_frames(self, val: int):
        self.param_panel.set_closing_softness_frames(val)

    def apply_generation_state(
        self,
        generation_state: GenerationState,
        *,
        active_preset_display_name: str | None = None,
    ) -> bool:
        if not isinstance(generation_state, GenerationState):
            return False
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
                    sync_context = build_ui_sync_context(base_input, snapshot)
                    candidate_output = OutputEditState(
                        base_plan_identity=sync_context.base_plan_identity,
                        adjustment_snapshot=snapshot,
                        generation_state=candidate_generation,
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
            self._project_generation_controls()
            self.sync_ui_state(adjustment_only=True)
        if request_save and self.controller:
            self.controller.request_settings_save()
        return True

    def apply_model_profile(self, profile_id: str) -> bool:
        if self.controller is None or self.ui_state.is_busy:
            return False
        resolution = self.controller.resolve_model_profile_apply(profile_id)
        return self._commit_resolved_model_profile(resolution)

    def apply_no_model_profile(self) -> bool:
        if self.controller is None or self.ui_state.is_busy:
            return False
        resolution = self.controller.resolve_no_profile()
        return self._commit_resolved_model_profile(resolution)

    def apply_active_model_profile_preset(self, preset_id: str) -> bool:
        if self.controller is None or self.ui_state.is_busy:
            return False
        resolution = self.controller.resolve_active_profile_preset_apply(preset_id)
        return self._commit_resolved_model_profile(resolution)

    def _project_generation_controls(self) -> None:
        settings = self.ui_state.generation_state.generation_settings
        self._projection_guard = True
        try:
            self.set_closing_hold_frames(settings.closing_hold_frames)
            self.set_closing_softness_frames(settings.closing_softness_frames)
        finally:
            self._projection_guard = False

    def _generation_settings_from_controls(self) -> GenerationSettings:
        current = self.ui_state.generation_state.generation_settings
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
        if self.ui_state.is_busy or not isinstance(generation_settings, GenerationSettings):
            return False
        debug_payload = {
            "closing_hold_frames": generation_settings.closing_hold_frames,
            "closing_softness_frames": generation_settings.closing_softness_frames,
            "long_vowel_mode": generation_settings.long_vowel_mode,
        }
        self.record_debug_action(
            "generation_settings_request",
            payload=debug_payload,
            status="started",
        )
        current = self.ui_state.generation_state
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
                current_model_profile_state=self.ui_state.model_profile_state,
                current_generation_settings=current.generation_settings,
                candidate_generation_settings=generation_settings,
                current_morph_upper_limit=self.ui_state.resolved_morph_upper_limit,
                candidate_morph_upper_limit=self.ui_state.resolved_morph_upper_limit,
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
                effective_plan = resolve_effective_shape_plan(candidate_base, snapshot)
                sync_context = build_ui_sync_context(
                    candidate_base,
                    snapshot,
                    effective_plan_hint=effective_plan,
                )
                candidate_output = OutputEditState(
                    base_plan_identity=sync_context.base_plan_identity,
                    adjustment_snapshot=snapshot,
                    generation_state=candidate_generation,
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
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return None
            path = dialog.GetPath()
            if not path.endswith('.vmd'):
                path += '.vmd'
            return path

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

    def _on_close(self, event: wx.Event):
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
                    return
                event.Veto()
                self.controller.request_close_delivery()
                return
            event.Veto()
            self.controller.request_exit()
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
                    return
                self._cancel_requested = True
                
            self._current_job_id = None
            self._cleanup_analysis_job()

        if self._active_debug_trace is not None:
            active_trace = self._active_debug_trace
            self._active_debug_trace = None
            self._finish_debug_trace(
                active_trace,
                status="cancelled",
                reason_code="application_exit",
            )
        self._shutdown_debug_store()
        self.close_about_dialog()

        if self.controller:
            self.controller.request_exit()
        else:
            self.Destroy()

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
        if quiet_path is None:
            dialog_dir = self.ui_state.last_audio_dialog_dir or self.ui_state.last_wav_dialog_dir or ""
            with wx.FileDialog(
                self,
                message="音声ファイルを選択してください",
                defaultDir=dialog_dir,
                wildcard="Audio files (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                path = file_dialog.GetPath()
        else:
            path = quiet_path

        if not path:
            return
            
        if self.controller:
            self.controller.request_open_audio_file(path)
    def _open_text_file(self, quiet_path: str = None, auto_load_counterpart: bool = True):
        """ [MS14-B3] TEXTファイルを開き、処理してGUIに反映する """
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
                    return
                path = file_dialog.GetPath()
                self.ui_state.last_text_dialog_dir = file_dialog.GetDirectory()
        else:
            path = quiet_path

        # 妥当性確認
        if not path:
            return
        if not os.path.exists(path):
            if not quiet_path:
                wx.MessageBox("指定されたファイルが見つかりません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if os.path.isdir(path):
            if not quiet_path:
                wx.MessageBox("ファイルではなくディレクトリが選択されました。", "エラー", wx.OK | wx.ICON_ERROR)
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
            return

        # 変換
        try:
            clean_text = _validate_and_clean_text(text_content)
            hiragana = text_to_hiragana(text_content)
            vowel = hiragana_to_vowel_string(hiragana)
        except TextProcessingError as e:
            if not quiet_path:
                wx.MessageBox(f"テキストの変換処理でエラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            return
        except Exception as e:
            if not quiet_path:
                wx.MessageBox(f"想定外の変換エラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
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

        # Counterpart auto load
        if auto_load_counterpart:
            stem = Path(path).stem
            dir_path = Path(path).parent
            # .wav, .mp3, .m4a の順に探す
            for ext in [".wav", ".mp3", ".m4a"]:
                audio_path = str(dir_path / (stem + ext))
                if os.path.exists(audio_path):
                    if self.controller:
                        self.controller.request_open_audio_file(audio_path)
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
        if self.ui_state.input_mode != INPUT_MODE_VOICE_ONLY:
            return
        edited_text = self.info_panel.get_text_preview()
        try:
            clean_text = _validate_and_clean_text(edited_text)
            self._update_voice_only_text_previews(clean_text)
        except TextProcessingError as e:
            wx.MessageBox(f"書き起こしテキストの変換処理でエラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            return
        except Exception as e:
            wx.MessageBox(f"想定外の変換エラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            return

        if clean_text != self.ui_state.transcription_text:
            self.ui_state.apply_transcription_edit(clean_text)
            self.placeholder_container.set_preview_placeholder_text(
                "書き起こしが編集されました。\n再解析が必要です。"
            )
        else:
            self.ui_state.transcription_edit_dirty = False
        self.sync_ui_state()

    def _on_transcription_revert(self, event):
        if self.ui_state.input_mode != INPUT_MODE_VOICE_ONLY:
            return
        original_text = self.ui_state.transcription_original_text
        if not original_text:
            return
        try:
            self._update_voice_only_text_previews(original_text)
        except Exception as e:
            wx.MessageBox(f"書き起こしテキストの復元に失敗しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            return

        if self.ui_state.transcription_text != original_text:
            self.ui_state.revert_transcription_edit()
            self.placeholder_container.set_preview_placeholder_text(
                "書き起こしを元に戻しました。\n再解析が必要です。"
            )
        else:
            self.ui_state.transcription_edit_dirty = False
        self.sync_ui_state()

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
    ) -> BaseTimingPlanInput | None:
        duration_sec = self._selected_audio_duration_sec()
        if plan is None or duration_sec is None:
            return None
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
                    closing_hold_frames=self.ui_state.generation_state.generation_settings.closing_hold_frames,
                    closing_softness_frames=self.ui_state.generation_state.generation_settings.closing_softness_frames,
                    long_vowel_mode=self.ui_state.generation_state.generation_settings.long_vowel_mode,
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
        self._active_analysis_job_id = None
        self._analysis_parameter_snapshot = None
        self._analysis_rollback_snapshot = None

    def _run_analysis(self):
        """ [MS14-B4] 解析実行の非同期起動 """
        # 開始前の前提条件確認
        self.ui_state.refresh_input_mode()
        if self.ui_state.input_mode == INPUT_MODE_TEXT_AUDIO and not (
            self.ui_state.selected_text_path and self.ui_state.selected_text_content
        ):
            wx.MessageBox("TEXTが設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if not self.ui_state.audio_for_analysis_ready:
            wx.MessageBox("音声ファイルが設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if not self.ui_state.analysis_start_ready:
            wx.MessageBox("解析に必要な入力が揃っていません。", "エラー", wx.OK | wx.ICON_ERROR)
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
            return
        if self.ui_state.is_busy:
            return  # 二重実行防止
        if self._selected_event_editor_has_uncommitted_input():
            return

        whisper_model_request = None
        if self.controller is not None:
            try:
                whisper_model_request = self.controller.build_active_whisper_model_request()
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

        if self.controller and getattr(self.ui_state, 'is_playing', False):
            self.controller.request_playback_stop()

        # Busy状態の開始
        self._analysis_info_in_progress = True
        self.ui_state.set_busy(True)
        self.sync_ui_state()
        
        self._progress_dialog = AnalysisProgressDialog(self, on_cancel_callback=self._on_analysis_cancel)
        self._progress_dialog.Show()

        # [MS17-B6] 解析用WAVを優先使用
        wav_path = self.ui_state.selected_wav_path
        if self.ui_state.selected_analysis_wav:
            wav_path = self.ui_state.selected_analysis_wav.analysis_wav_path

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
                analysis_text=self.ui_state.selected_text_content
                or transcription_text_override
                or self.ui_state.analysis_text_content,
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
        )
        self._worker.start()

        if self._timeout_timer:
            self._timeout_timer.Destroy()
        self._timeout_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timeout_warning, self._timeout_timer)
        self._timeout_timer.Start(150000, wx.TIMER_ONE_SHOT)

    def _on_analysis_cancel(self):
        self._cancel_requested = True
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

    def _finish_analysis_parameter_mismatch(
        self,
        debug_trace: AnalysisDebugTrace | None = None,
    ):
        self._complete_analysis_terminal()
        self.ui_state.invalidate_analysis()
        self.ui_state.set_busy(False)
        self.sync_ui_state()
        self._finish_debug_trace(
            debug_trace,
            status="failed",
            reason_code="analysis_parameter_mismatch",
        )

    def _on_analysis_success(self, job_id, result):
        """ [MS14-B4] 解析成功時のコールバック """
        if not self._is_current_analysis_terminal(job_id):
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

        self.ui_state.set_busy(False)
        self._complete_analysis_terminal()
        self._selected_event_notice = ""
        if debug_trace is not None:
            debug_trace.adopt()
            self._accepted_debug_trace = debug_trace
        self._project_generation_controls()
        self.sync_ui_state()
        self._finish_debug_trace(
            debug_trace,
            status="completed",
            reason_code="analysis_accepted",
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
        try:
            effective_plan = sync_context.effective_plan
            preview_data = build_preview_data_from_effective_shape_plan(
                effective_plan,
                output_morph_names=output_morph_names,
            )
            preview_model = self.placeholder_container.pnl_preview.model
            current_digest = effective_plan.base_plan_identity.digest
            if (
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
        return get_builtin_morph_name_set(
            self.ui_state.generation_state.resolved_morph_name_set_id
        ).output_names

    def _build_current_base_timing_plan_input(self) -> BaseTimingPlanInput | None:
        return self._build_base_timing_plan_input_for_plan(
            self.ui_state.current_timing_plan
        )

    def _on_analysis_error(self, job_id, error):
        """ [MS14-B4] 解析失敗時のコールバック """
        if not self._is_current_analysis_terminal(job_id):
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
        if self.ui_state.is_busy:
            return
        if self.ui_state.has_workspace_user_data and not self.confirm_workspace_reset():
            return
        if self.controller:
            self.controller.request_reset_workspace()

    def _on_btn_export_mmd_wav(self, event):
        if self.controller: self.controller.request_export_mmd_wav()

    def _on_btn_cancel_audio_worker(self, event):
        if self.controller: self.controller.request_cancel_audio_worker()

    def _on_btn_play(self, event):
        if self.controller: self.controller.request_playback_play()

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
        limit = settings.get("morph_upper_limit", 0.5)
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
        self.param_panel.sc_hold_frames.Bind(wx.EVT_SPINCTRL, self._on_output_setting_changed)
        self.param_panel.sc_hold_frames.Bind(wx.EVT_TEXT, self._on_output_setting_changed)
        self.param_panel.sc_softness_frames.Bind(wx.EVT_SPINCTRL, self._on_output_setting_changed)
        self.param_panel.sc_softness_frames.Bind(wx.EVT_TEXT, self._on_output_setting_changed)
        self.sync_ui_state()

    def _on_param_changed(self, event):
        # Compatibility entry point for existing callers/tests.
        self._on_morph_upper_changed(event)

    def _on_morph_upper_changed(self, event):
        event.Skip()
        if self._projection_guard:
            return
        candidate_upper = self.get_morph_upper_limit()
        try:
            direct_edit_guard = validate_active_profile_direct_edit(
                current_model_profile_state=self.ui_state.model_profile_state,
                current_generation_settings=self.ui_state.generation_state.generation_settings,
                candidate_generation_settings=self.ui_state.generation_state.generation_settings,
                current_morph_upper_limit=self.ui_state.resolved_morph_upper_limit,
                candidate_morph_upper_limit=candidate_upper,
            )
        except (TypeError, ValueError):
            direct_edit_guard = None
        if direct_edit_guard is None or not direct_edit_guard.allowed:
            self._projection_guard = True
            try:
                self.set_morph_upper_limit(self.ui_state.resolved_morph_upper_limit)
            finally:
                self._projection_guard = False
            return
        self.ui_state.resolved_morph_upper_limit = candidate_upper
        if self.controller:
            self.controller.invalidate_audio_job_for_input_change()
        if self.ui_state.analysis_result_valid:
            self.ui_state.invalidate_analysis()
        else:
            self.ui_state.clear_output_diagnostics_state()
            if self.ui_state.status_key == StatusKey.ANALYSIS_CANCELLED:
                self.ui_state.status_key = (
                    StatusKey.READY_FOR_ANALYSIS
                    if self.ui_state.analysis_start_ready
                    else StatusKey.INPUT_MISSING
                )
        self.sync_ui_state()
        if self.controller:
            self.controller.request_settings_save()

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
