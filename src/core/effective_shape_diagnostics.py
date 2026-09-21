"""Bounded, privacy-safe diagnostics for effective-shape resolution.

This module deliberately has no GUI, trace-store, or audio dependencies.  The
resolver can therefore receive a collector as an optional observer without
changing its return value, cache identity, or error message.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


RESOLVER_DIAGNOSTIC_REVISION = "ms28-b3c-resolver-v1"
MAX_PHASE_RECORDS = 128
MAX_ATTEMPTS = 16
MAX_DETAILS = 8
MAX_COLLECTION = 32
ADMISSION_DETAIL_REVISION = "ms28-b3c-admission-detail-v1"
ADMISSION_MAX_SHAPES = 16
ADMISSION_MAX_CONTROL_POINTS = 16
ADMISSION_MAX_RANGES = 32

PHASES = frozenset(
    {
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
PASS_KINDS = frozenset(
    {
        "primary",
        "identity_validation",
        "silence_rebuild",
        "manual_comparison",
        "not_applicable",
    }
)
FAILURE_CODES = frozenset(
    {
        "none",
        "not_applicable",
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
EVENT_ROLES = frozenset(
    {
        "subject",
        "neighbor",
        "source",
        "terminal",
        "continuation",
        "long_source",
        "related_event",
        "positive_event_peak",
        "positive_shape_anchor",
        "required_zero_shape_anchor",
        "not_applicable",
        "not_available",
        "unknown",
    }
)
EXCEPTION_TYPES = frozenset(
    {"AdjustmentContractError", "TypeError", "ValueError", "IndexError", "unknown"}
)

ADMISSION_DETAIL_STATES = frozenset(
    {"available", "partial", "not_available", "not_applicable"}
)
ADMISSION_DETAIL_REASONS = frozenset(
    {"not_available", "value_not_observed", "owner_mismatch", "truncated"}
)
ADMISSION_SECTION_REASONS = ADMISSION_DETAIL_REASONS | {"not_applicable"}
ADMISSION_RANGE_STATUS = frozenset(
    {"valid", "zero_width", "reversed", "unavailable"}
)
ADMISSION_LONG_ROLES = frozenset(
    {"long_source", "intermediate_continuation", "terminal_continuation", "not_applicable", "not_available"}
)
ADMISSION_SHAPE_KINDS = frozenset(
    {
        "multi_point_envelope",
        "asymmetric_trapezoid",
        "long_vowel_decay",
        "long_vowel_hold",
        "not_available",
    }
)
ADMISSION_POINT_KINDS = frozenset(
    {"start_zero", "top", "valley", "hold", "slope_mid", "end_zero", "not_available"}
)
ADMISSION_BOUNDARY_RELATIONS = frozenset(
    {
        "same_vowel_same_frame",
        "silence_gap",
        "different_vowel_boundary",
        "not_applicable",
        "not_available",
    }
)
ADMISSION_BOUNDARY_ACTIONS = frozenset(
    {"preserved_zero_keyframe", "not_applicable", "not_available"}
)
ADMISSION_REJECTION_REASONS = frozenset(
    {
        "base_event_overlaps_silence_core",
        "required_zero_missing",
        "admission_boundary_invalid",
        "not_applicable",
        "not_available",
    }
)
ADMISSION_VOWELS = frozenset({"あ", "い", "う", "え", "お"})
ADMISSION_BOUNDARY_CHECK_RANGE = frozenset(
    {"valid", "zero_width", "reversed", "unavailable"}
)
ADMISSION_BOUNDARY_CHECK_DECISIONS = frozenset(
    {"accepted_boundary_only", "rejected_boundary_invalid", "not_applicable"}
)

_DETAIL_KEYS = frozenset(
    {
        "event_index",
        "source_event_index",
        "event_role",
        "source_event_role",
        "neighbor_event_index",
        "neighbor_event_role",
        "frame_start",
        "frame_end",
        "start_frame",
        "peak_frame",
        "end_frame",
        "value",
        "neighbor_value",
        "range_start",
        "range_end",
        "count",
        "expected_count",
        "observed_count",
        "status",
        "reason_code",
    }
)


def _safe_enum(value: object, allowed: frozenset[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def _safe_index(value: object) -> int | str:
    if isinstance(value, bool):
        return "not_available"
    if isinstance(value, int) and value >= 0:
        return value
    return "not_available"


def _safe_optional_index(value: object, *, missing: str = "not_applicable") -> int | str:
    return missing if value is None else _safe_index(value)


def _safe_scalar(value: object) -> int | float | bool | str | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return "not_available"
    if isinstance(value, int) and not isinstance(value, bool):
        return value if abs(value) <= 2**31 else "not_available"
    if isinstance(value, float):
        return value if math.isfinite(value) else "not_available"
    return "not_available"


def safe_details(value: object, *, limit: int = MAX_DETAILS) -> dict[str, object]:
    """Return only fixed diagnostic keys and JSON-safe primitive values."""

    if not isinstance(value, dict):
        return {}
    result: dict[str, object] = {}
    for key in sorted(value, key=lambda item: str(item)):
        if len(result) >= max(0, limit):
            break
        key_text = key if isinstance(key, str) else ""
        if key_text not in _DETAIL_KEYS:
            continue
        item = value[key]
        if key_text.endswith("event_index") or key_text == "event_index":
            result[key_text] = _safe_index(item)
        elif key_text.endswith("event_role") or key_text == "event_role":
            result[key_text] = _safe_enum(item, EVENT_ROLES, "unknown")
        elif key_text == "status":
            result[key_text] = _safe_enum(
                item,
                frozenset({"available", "unavailable", "complete", "partial", "unknown"}),
                "unknown",
            )
        elif key_text == "reason_code":
            result[key_text] = _safe_enum(
                item,
                frozenset(
                    {
                        "required_zero_positive_conflict",
                        "base_event_overlaps_silence_core",
                        "required_zero_missing",
                    }
                ),
                "unknown",
            )
        else:
            result[key_text] = _safe_scalar(item)
    return result


def _safe_optional_scalar(value: object) -> int | float | bool | str:
    safe = _safe_scalar(value)
    return "not_available" if safe is None else safe


def _safe_admission_vowel(value: object) -> str:
    return value if isinstance(value, str) and value in ADMISSION_VOWELS else "not_available"


def _safe_admission_range(value: object) -> list[int] | str:
    if isinstance(value, Mapping):
        start = value.get("start_frame")
        end = value.get("end_frame")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) != 2:
            return "not_available"
        start, end = value
    else:
        return "not_available"
    if (
        isinstance(start, bool)
        or not isinstance(start, int)
        or isinstance(end, bool)
        or not isinstance(end, int)
        or abs(start) > 2**31
        or abs(end) > 2**31
    ):
        return "not_available"
    return [start, end]


def _safe_admission_raw_range(value: object) -> dict[str, int | float | str]:
    source = value if isinstance(value, Mapping) else {}
    result: dict[str, int | float | str] = {}
    for key in ("start_sec", "end_sec"):
        result[key] = _safe_optional_scalar(source.get(key))
    for key in ("start_frame", "peak_frame", "end_frame"):
        result[key] = _safe_index(source.get(key))
    return result


def _safe_admission_collection(
    value: object,
    *,
    limit: int,
    item_serializer,
) -> dict[str, object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return {"items": [], "total": 0, "recorded": 0, "truncated": False}
    total = len(value)
    bounded_limit = max(0, limit)
    result: list[object] = []
    for item in value[:bounded_limit]:
        try:
            result.append(item_serializer(item))
        except Exception:
            result.append("not_available")
    return {
        "items": result,
        "total": total,
        "recorded": len(result),
        "truncated": total > bounded_limit,
    }


def _safe_boundary_admission_checks(value: object) -> dict[str, object]:
    source = value if isinstance(value, Mapping) else {}

    def safe_bool_or_unavailable(item: object) -> bool | str:
        return item if isinstance(item, bool) else "not_available"

    peak_value = _safe_scalar(source.get("event_peak_value"))
    if not isinstance(peak_value, (int, float)) or isinstance(peak_value, bool):
        peak_value = "not_available"
    return {
        "candidate_range": _safe_enum(
            source.get("candidate_range"),
            ADMISSION_BOUNDARY_CHECK_RANGE,
            "unavailable",
        ),
        "positive_point_kinds_empty": safe_bool_or_unavailable(
            source.get("positive_point_kinds_empty")
        ),
        "boundary_positive_point_kinds_empty": safe_bool_or_unavailable(
            source.get("boundary_positive_point_kinds_empty")
        ),
        "positive_core_frame_ranges_empty": safe_bool_or_unavailable(
            source.get("positive_core_frame_ranges_empty")
        ),
        "matching_end_zero": safe_bool_or_unavailable(source.get("matching_end_zero")),
        "shape_provenance_available": safe_bool_or_unavailable(
            source.get("shape_provenance_available")
        ),
        "boundary_relation_verified": safe_bool_or_unavailable(
            source.get("boundary_relation_verified")
        ),
        "event_peak_value": peak_value,
        "decision": _safe_enum(
            source.get("decision"),
            ADMISSION_BOUNDARY_CHECK_DECISIONS,
            "not_applicable",
        ),
    }


def _safe_admission_section_status(value: object) -> dict[str, dict[str, str]]:
    source = value if isinstance(value, Mapping) else {}
    result: dict[str, dict[str, str]] = {}
    for section in ("event_context", "admission_candidate", "range_derivation"):
        item = source.get(section)
        item_map = item if isinstance(item, Mapping) else {}
        state = _safe_enum(
            item_map.get("state"),
            ADMISSION_DETAIL_STATES,
            "not_available",
        )
        reason = _safe_enum(
            item_map.get("reason"),
            ADMISSION_SECTION_REASONS,
            "not_available",
        )
        result[section] = {"state": state, "reason": reason}
    return result


def _admission_capture_state(section_status: Mapping[str, Mapping[str, str]]) -> str:
    states = [
        item.get("state", "not_available")
        for item in section_status.values()
        if isinstance(item, Mapping)
    ]
    if states and all(state in {"available", "not_applicable"} for state in states):
        return "available"
    if any(state in {"available", "partial"} for state in states):
        return "partial"
    return "not_available"


def serialize_admission_detail(value: object) -> dict[str, object]:
    """Serialize the fixed, bounded B3C admission detail payload.

    The caller supplies values already observed at the admission boundary.
    This function only allowlists and bounds them; it never re-runs resolver
    logic or serializes arbitrary objects.
    """

    try:
        source = value if isinstance(value, Mapping) else {}
        section_status = _safe_admission_section_status(source.get("section_status"))
        event_source = source.get("event_context")
        event_context = event_source if isinstance(event_source, Mapping) else {}
        adjacent_source = event_context.get("adjacent")
        adjacent = adjacent_source if isinstance(adjacent_source, Mapping) else {}

        candidate_source = source.get("admission_candidate")
        candidate = candidate_source if isinstance(candidate_source, Mapping) else {}
        range_source = source.get("range_derivation")
        range_derivation = range_source if isinstance(range_source, Mapping) else {}
        safe_event_index = _safe_index(event_context.get("event_index"))
        safe_vowel = _safe_admission_vowel(event_context.get("vowel"))
        safe_effective_event_range = _safe_admission_range(
            event_context.get("effective_event_range")
        )
        safe_event_range_status = _safe_enum(
            event_context.get("event_range_status"),
            ADMISSION_RANGE_STATUS,
            "unavailable",
        )
        safe_effective_range = _safe_admission_range(
            range_derivation.get("effective_range_before_validation")
        )
        if section_status["event_context"]["state"] == "available" and (
            safe_event_index == "not_available"
            or safe_vowel == "not_available"
            or safe_effective_event_range == "not_available"
            or safe_event_range_status == "unavailable"
        ):
            section_status["event_context"] = {
                "state": "partial",
                "reason": "value_not_observed",
            }
        if section_status["admission_candidate"]["state"] == "available" and (
            _safe_index(candidate.get("shape_match_count")) == "not_available"
        ):
            section_status["admission_candidate"] = {
                "state": "partial",
                "reason": "value_not_observed",
            }
        if section_status["range_derivation"]["state"] == "available" and (
            safe_effective_range == "not_available"
        ):
            section_status["range_derivation"] = {
                "state": "partial",
                "reason": "value_not_observed",
            }
        def collection_truncated(item: object, limit: int) -> bool:
            return (
                isinstance(item, Sequence)
                and not isinstance(item, (str, bytes, bytearray))
                and len(item) > limit
            )

        event_truncated = collection_truncated(event_context.get("adjacent_ranges"), 2)
        candidate_truncated = any(
            collection_truncated(candidate.get(field_name), limit)
            for field_name, limit in (
                ("source_event_indices", ADMISSION_MAX_RANGES),
                ("shape_provenance", ADMISSION_MAX_SHAPES),
                ("positive_point_kinds", ADMISSION_MAX_CONTROL_POINTS),
                ("positive_core_frame_ranges", ADMISSION_MAX_RANGES),
                ("observed_positive_core_frame_ranges", ADMISSION_MAX_RANGES),
                ("required_zero_frame_ranges", ADMISSION_MAX_RANGES),
            )
        )
        range_truncated = collection_truncated(
            range_derivation.get("shape_event_ranges"), ADMISSION_MAX_RANGES
        )
        if event_truncated:
            section_status["event_context"] = {
                "state": "partial",
                "reason": "truncated",
            }
        if candidate_truncated:
            section_status["admission_candidate"] = {
                "state": "partial",
                "reason": "truncated",
            }
        if range_truncated:
            section_status["range_derivation"] = {
                "state": "partial",
                "reason": "truncated",
            }
        derived_capture_state = _admission_capture_state(section_status)
        requested_capture_state = _safe_enum(
            source.get("detail_capture_state"),
            frozenset({"available", "partial", "not_available"}),
            derived_capture_state,
        )
        if "not_available" in {derived_capture_state, requested_capture_state}:
            capture_state = "not_available"
        elif "partial" in {derived_capture_state, requested_capture_state}:
            capture_state = "partial"
        else:
            capture_state = "available"
        unavailable_reason = _safe_enum(
            source.get("unavailable_reason"),
            ADMISSION_DETAIL_REASONS,
            "not_available" if capture_state != "available" else "not_applicable",
        )
        if capture_state != "available" and (
            event_truncated or candidate_truncated or range_truncated
        ):
            unavailable_reason = "truncated"

        def serialize_adjacent_range(item: object) -> dict[str, object]:
            item_map = item if isinstance(item, Mapping) else {}
            return {
                "event_index": _safe_index(item_map.get("event_index")),
                "vowel": _safe_admission_vowel(item_map.get("vowel")),
                "range": _safe_admission_range(item_map.get("range")),
            }

        def serialize_shape(item: object) -> dict[str, object]:
            item_map = item if isinstance(item, Mapping) else {}

            def serialize_control_point(point: object) -> dict[str, object]:
                point_map = point if isinstance(point, Mapping) else {}
                return {
                    "frame_no": _safe_index(point_map.get("frame_no")),
                    "value": _safe_optional_scalar(point_map.get("value")),
                    "point_kind": _safe_enum(
                        point_map.get("point_kind"),
                        ADMISSION_POINT_KINDS,
                        "not_available",
                    ),
                }

            return {
                "shape_ordinal": _safe_index(item_map.get("shape_ordinal")),
                "shape_kind": _safe_enum(
                    item_map.get("shape_kind"),
                    ADMISSION_SHAPE_KINDS,
                    "not_available",
                ),
                "real_base_event_indices": _safe_admission_collection(
                    item_map.get("real_base_event_indices"),
                    limit=ADMISSION_MAX_RANGES,
                    item_serializer=_safe_index,
                ),
                "event_range": _safe_admission_range(item_map.get("event_range")),
                "shape_range": _safe_admission_range(item_map.get("shape_range")),
                "control_points": _safe_admission_collection(
                    item_map.get("control_points"),
                    limit=ADMISSION_MAX_CONTROL_POINTS,
                    item_serializer=serialize_control_point,
                ),
            }

        return {
            "detail_revision": ADMISSION_DETAIL_REVISION,
            "detail_capture_state": capture_state,
            "unavailable_reason": unavailable_reason,
            "section_status": section_status,
            "event_context": {
                "event_index": safe_event_index,
                "vowel": safe_vowel,
                "raw_range": _safe_admission_raw_range(event_context.get("raw_range")),
                "effective_event_range": safe_effective_event_range,
                "event_range_status": safe_event_range_status,
                "adjacent": {
                    "previous_event_index": _safe_optional_index(
                        adjacent.get("previous_event_index")
                    ),
                    "next_event_index": _safe_optional_index(
                        adjacent.get("next_event_index")
                    ),
                },
                "adjacent_ranges": _safe_admission_collection(
                    event_context.get("adjacent_ranges"),
                    limit=2,
                    item_serializer=serialize_adjacent_range,
                ),
                "long_vowel_role": _safe_enum(
                    event_context.get("long_vowel_role"),
                    ADMISSION_LONG_ROLES,
                    "not_applicable",
                ),
                "long_vowel_source_event_index": _safe_optional_index(
                    event_context.get("long_vowel_source_event_index")
                ),
            },
            "admission_candidate": {
                "origin_shape_id": _safe_index(candidate.get("origin_shape_id")),
                "source_event_indices": _safe_admission_collection(
                    candidate.get("source_event_indices"),
                    limit=ADMISSION_MAX_RANGES,
                    item_serializer=_safe_index,
                ),
                "shape_match_count": _safe_index(candidate.get("shape_match_count")),
                "shape_provenance": _safe_admission_collection(
                    candidate.get("shape_provenance"),
                    limit=ADMISSION_MAX_SHAPES,
                    item_serializer=serialize_shape,
                ),
                "positive_point_kinds": _safe_admission_collection(
                    candidate.get("positive_point_kinds"),
                    limit=ADMISSION_MAX_CONTROL_POINTS,
                    item_serializer=lambda item: _safe_enum(
                        item,
                        ADMISSION_POINT_KINDS,
                        "not_available",
                    ),
                ),
                "positive_core_frame_ranges": _safe_admission_collection(
                    candidate.get("positive_core_frame_ranges"),
                    limit=ADMISSION_MAX_RANGES,
                    item_serializer=_safe_admission_range,
                ),
                "observed_positive_core_frame_ranges": _safe_admission_collection(
                    candidate.get("observed_positive_core_frame_ranges"),
                    limit=ADMISSION_MAX_RANGES,
                    item_serializer=_safe_admission_range,
                ),
                "required_zero_frame_ranges": _safe_admission_collection(
                    candidate.get("required_zero_frame_ranges"),
                    limit=ADMISSION_MAX_RANGES,
                    item_serializer=_safe_admission_range,
                ),
                "boundary_only": (
                    candidate.get("boundary_only")
                    if isinstance(candidate.get("boundary_only"), bool)
                    else "not_available"
                ),
                "boundary_frame": _safe_optional_index(
                    candidate.get("boundary_frame")
                ),
                "boundary_point_kind": _safe_enum(
                    candidate.get("boundary_point_kind"),
                    ADMISSION_POINT_KINDS | {"not_applicable"},
                    "not_applicable",
                ),
                "boundary_relation": _safe_enum(
                    candidate.get("boundary_relation"),
                    ADMISSION_BOUNDARY_RELATIONS,
                    "not_applicable",
                ),
                "boundary_action": _safe_enum(
                    candidate.get("boundary_action"),
                    ADMISSION_BOUNDARY_ACTIONS,
                    "not_applicable",
                ),
                "boundary_admission_checks": _safe_boundary_admission_checks(
                    candidate.get("boundary_admission_checks")
                ),
                "base_event_silence_core_overlap": (
                    candidate.get("base_event_silence_core_overlap")
                    if isinstance(candidate.get("base_event_silence_core_overlap"), bool)
                    else "not_available"
                ),
                "manual_adjustment_applied": (
                    candidate.get("manual_adjustment_applied")
                    if isinstance(candidate.get("manual_adjustment_applied"), bool)
                    else "not_available"
                ),
                "enabled": (
                    candidate.get("enabled")
                    if isinstance(candidate.get("enabled"), bool)
                    else "not_available"
                ),
                "rejection_reason_code": _safe_enum(
                    candidate.get("rejection_reason_code"),
                    ADMISSION_REJECTION_REASONS,
                    "not_applicable",
                ),
            },
            "range_derivation": {
                "raw_event_range": _safe_admission_range(
                    range_derivation.get("raw_event_range")
                ),
                "shape_event_ranges": _safe_admission_collection(
                    range_derivation.get("shape_event_ranges"),
                    limit=ADMISSION_MAX_RANGES,
                    item_serializer=_safe_admission_range,
                ),
                "effective_range_before_validation": safe_effective_range,
                "range_inputs_status": _safe_enum(
                    range_derivation.get("range_inputs_status"),
                    frozenset({"observed", "valid", "invalid", "not_available"}),
                    "not_available",
                ),
            },
        }
    except Exception:
        return {
            "detail_revision": ADMISSION_DETAIL_REVISION,
            "detail_capture_state": "not_available",
            "unavailable_reason": "not_available",
            "section_status": {
                section: {"state": "not_available", "reason": "not_available"}
                for section in ("event_context", "admission_candidate", "range_derivation")
            },
        }


FIELD_CODES = frozenset(
    {
        "unknown",
        "base_input",
        "source_duration_frames",
        "shape_parameters",
        "closing_hold_frames",
        "closing_softness_frames",
        "long_vowel_mode",
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
        "event_index",
        "span_indices",
        "bracketing",
        "rms_window_times_sec",
        "rms_window_values",
        "local_peak",
        "full_span_start_frame",
        "full_span_end_frame",
        "silence_core_frame_ranges",
        "boundary_fringe_frame_ranges",
        "silence_core_overlap",
        "coverage_status",
        "provenance_status",
        "bridge_rejection_reason_code",
        "base_plan_identity",
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
        "long_vowel_role",
        "terminal_end_frame",
        "closing_frame",
        "real_base_event_indices",
        "end_offset_frames",
        "slope_ratio",
        "effective_frame_range",
        "positive_core_frame_ranges",
        "required_zero_frame_ranges",
        "positive_point_kinds",
        "source_event_indices",
        "rejection_reason_code",
        "origin_shape_id",
        "positive_point_kinds",
        "source_event_indices",
        "required_zero_frames",
        "normalization_contract",
        "effective_plan",
    }
)


def _safe_exception_type(error: object) -> str:
    name = type(error).__name__
    return name if name in EXCEPTION_TYPES else "unknown"


def _safe_failure(
    error: object,
    *,
    phase: str,
    pass_kind: str,
    fallback_code: str,
    failure_detail: object | None = None,
) -> dict[str, object]:
    safe_code = getattr(error, "safe_code", None)
    safe_field = getattr(error, "safe_field_code", None)
    safe_phase = getattr(error, "safe_phase", None)
    safe_pass = getattr(error, "safe_pass_kind", None)
    legacy_raw_details = getattr(error, "safe_details", None)
    details = safe_details(legacy_raw_details)
    if failure_detail is not None:
        structured_details = serialize_admission_detail(failure_detail)
        for key, value in structured_details.items():
            if key not in details:
                details[key] = value
        detail_state = structured_details.get("detail_capture_state", "not_available")
        details_availability = (
            detail_state if detail_state in ADMISSION_DETAIL_STATES else "not_available"
        )
    else:
        details_availability = (
            "available" if isinstance(legacy_raw_details, dict) else "not_available"
        )
    return {
        "failure_code": _safe_enum(safe_code, FAILURE_CODES, _safe_enum(fallback_code, FAILURE_CODES, "unknown_contract_failure")),
        "phase": _safe_enum(safe_phase, PHASES, phase),
        "pass_kind": _safe_enum(safe_pass, PASS_KINDS, pass_kind),
        "field_code": _safe_enum(safe_field, FIELD_CODES, "unknown"),
        "event_index": _safe_index(getattr(error, "event_index", None)),
        "source_event_index": _safe_index(getattr(error, "source_event_index", None)),
        "event_role": _safe_enum(getattr(error, "event_role", None), EVENT_ROLES, "not_applicable"),
        "source_event_role": _safe_enum(
            getattr(error, "source_event_role", None), EVENT_ROLES, "not_applicable"
        ),
        "exception_type": _safe_exception_type(error),
        "details": details,
        "details_availability": details_availability,
    }


class ResolverDiagnosticsCollector:
    """Collect resolver progress without becoming part of product state."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_phase_records: int = MAX_PHASE_RECORDS,
        max_attempts: int = MAX_ATTEMPTS,
        max_details: int = MAX_DETAILS,
        max_collection: int = MAX_COLLECTION,
    ) -> None:
        self.enabled = bool(enabled)
        self._max_phase_records = max(1, int(max_phase_records))
        self._max_attempts = max(1, int(max_attempts))
        self._max_details = max(1, int(max_details))
        self._max_collection = max(1, int(max_collection))
        self._attempts: list[dict[str, object]] = []
        self._current: dict[str, object] | None = None
        self._truncated = False

    def _guard(self, callback, default=None):
        if not self.enabled:
            return default
        try:
            return callback()
        except Exception:
            # Diagnostics must never replace a product result or exception.
            self._truncated = True
            return default

    def start_attempt(self, *, caller: str = "resolver", plan_origin: str = "resolved") -> None:
        def record() -> None:
            if len(self._attempts) >= self._max_attempts:
                self._truncated = True
                self._current = None
                return
            self._current = {
                "attempt_index": len(self._attempts) + 1,
                "caller": caller if caller in {"resolver", "ui_sync_context", "unknown"} else "unknown",
                "plan_origin": plan_origin
                if plan_origin in {"resolved", "cache", "hint", "unknown"}
                else "unknown",
                "status": "attempted",
                "phase_records": [],
                "failure": None,
                "summary": {},
            }
            self._attempts.append(self._current)

        self._guard(record)

    def set_input_summary(self, **values: object) -> None:
        def record() -> None:
            if self._current is None:
                return
            summary = self._current["summary"]
            if not isinstance(summary, dict):
                summary = {}
                self._current["summary"] = summary
            for key, value in values.items():
                if key in {"timeline_count", "observation_count", "source_duration_frames"}:
                    summary[key] = _safe_index(value)
                elif key in {"observations_present", "timeline_present"}:
                    summary[key] = value if isinstance(value, bool) else "not_available"
                elif key in {"phase", "status"}:
                    summary[key] = _safe_scalar(value)

        self._guard(record)

    def phase_started(
        self,
        phase: str,
        *,
        pass_kind: str = "primary",
        details: dict[str, object] | None = None,
    ) -> None:
        def record() -> None:
            if self._current is None:
                return
            phase_name = _safe_enum(phase, PHASES, "resolver_input")
            pass_name = _safe_enum(pass_kind, PASS_KINDS, "not_applicable")
            records = self._current["phase_records"]
            if not isinstance(records, list):
                return
            existing = next(
                (
                    item
                    for item in records
                    if item.get("phase") == phase_name and item.get("pass_kind") == pass_name
                ),
                None,
            )
            if existing is None:
                if len(records) >= self._max_phase_records:
                    self._truncated = True
                    return
                existing = {
                    "phase": phase_name,
                    "pass_kind": pass_name,
                    "first_observation": len(records) + 1,
                    "last_observation": len(records) + 1,
                    "attempted_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "event_count": 0,
                    "details": {},
                    "failure": None,
                }
                records.append(existing)
            existing["attempted_count"] = int(existing["attempted_count"]) + 1
            existing["last_observation"] = len(records)
            if isinstance(details, dict):
                existing["details"] = safe_details(details, limit=self._max_details)

        self._guard(record)

    def phase_completed(self, phase: str, *, pass_kind: str = "primary", event_count: int | None = None) -> None:
        def record() -> None:
            if self._current is None:
                return
            records = self._current["phase_records"]
            if not isinstance(records, list):
                return
            phase_name = _safe_enum(phase, PHASES, "resolver_input")
            pass_name = _safe_enum(pass_kind, PASS_KINDS, "not_applicable")
            item = next(
                (row for row in records if row.get("phase") == phase_name and row.get("pass_kind") == pass_name),
                None,
            )
            if item is None:
                return
            item["completed_count"] = int(item["completed_count"]) + 1
            if isinstance(event_count, int) and event_count >= 0:
                item["event_count"] = min(self._max_collection, event_count)

        self._guard(record)

    def phase_failed(
        self,
        phase: str,
        error: object,
        *,
        pass_kind: str = "primary",
        fallback_code: str = "unknown_contract_failure",
        failure_detail: object | None = None,
    ) -> None:
        def record() -> None:
            if self._current is None:
                return
            phase_name = _safe_enum(phase, PHASES, "resolver_input")
            pass_name = _safe_enum(pass_kind, PASS_KINDS, "not_applicable")
            records = self._current["phase_records"]
            if isinstance(records, list):
                item = next(
                    (
                        row
                        for row in records
                        if row.get("phase") == phase_name and row.get("pass_kind") == pass_name
                    ),
                    None,
                )
                if item is not None:
                    item["failed_count"] = int(item["failed_count"]) + 1
                    if item.get("failure") is None:
                        item["failure"] = _safe_failure(
                            error,
                            phase=phase_name,
                            pass_kind=pass_name,
                            fallback_code=fallback_code,
                            failure_detail=failure_detail,
                        )
            self._current["status"] = "failed"
            self._current["failure"] = _safe_failure(
                error,
                phase=phase_name,
                pass_kind=pass_name,
                fallback_code=fallback_code,
                failure_detail=failure_detail,
            )

        self._guard(record)

    def complete_attempt(self, *, status: str = "completed") -> None:
        def record() -> None:
            if self._current is not None and self._current.get("status") != "failed":
                self._current["status"] = status if status in {"completed", "not_evaluable"} else "completed"

        self._guard(record)

    def mark_plan_origin(self, plan_origin: str) -> None:
        def record() -> None:
            if self._current is not None and plan_origin in {"cache", "hint", "unknown"}:
                self._current["plan_origin"] = plan_origin
                self._current["status"] = "completed"

        self._guard(record)

    def snapshot(self) -> dict[str, object]:
        if not self.enabled:
            return {
                "diagnostic_revision": RESOLVER_DIAGNOSTIC_REVISION,
                "capture_state": "disabled",
                "attempts": [],
                "truncation": {"limited": False},
            }

        def make() -> dict[str, object]:
            return {
                "diagnostic_revision": RESOLVER_DIAGNOSTIC_REVISION,
                "capture_state": "limited" if self._truncated else "complete",
                "attempt_count": len(self._attempts),
                "attempts": self._attempts[: self._max_attempts],
                "truncation": {"limited": bool(self._truncated)},
            }

        result = self._guard(make, default={})
        return result if isinstance(result, dict) else {}


def ensure_safe_failure_metadata(
    error: object,
    *,
    phase: str,
    pass_kind: str,
    fallback_code: str = "unknown_contract_failure",
    field_code: str = "unknown",
) -> object:
    """Fill missing safe metadata without parsing messages or replacing errors."""

    if getattr(error, "safe_code", None) is None:
        try:
            error.safe_code = fallback_code
        except Exception:
            pass
    if getattr(error, "safe_field_code", None) is None:
        try:
            error.safe_field_code = field_code
        except Exception:
            pass
    if getattr(error, "safe_phase", None) is None:
        try:
            error.safe_phase = _safe_enum(phase, PHASES, "resolver_input")
        except Exception:
            pass
    if getattr(error, "safe_pass_kind", None) is None:
        try:
            error.safe_pass_kind = _safe_enum(pass_kind, PASS_KINDS, "not_applicable")
        except Exception:
            pass
    return error
