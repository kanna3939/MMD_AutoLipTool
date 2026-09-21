from __future__ import annotations

from dataclasses import dataclass
import json

import pytest

from src.core.effective_shape_diagnostics import (
    ResolverDiagnosticsCollector,
    serialize_admission_detail,
)
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import AdjustmentContractError


@dataclass(frozen=True)
class Point:
    time_sec: float
    vowel: str = "あ"
    value: float = 0.5
    duration_sec: float = 0.2
    start_sec: float | None = None
    end_sec: float | None = None


def _input(*points: Point, observations=None) -> BaseTimingPlanInput:
    return BaseTimingPlanInput(
        timeline=points,
        observations=observations,
        source_duration_frames=180,
        shape_parameters=ShapeParameters(),
    )


def test_successful_resolution_records_primary_and_comparison_passes() -> None:
    collector = ResolverDiagnosticsCollector()
    base = _input(Point(0.5), Point(1.0))

    expected = resolve_effective_shape_plan(base)
    actual = resolve_effective_shape_plan(base, diagnostics=collector)

    assert actual == expected
    snapshot = collector.snapshot()
    assert snapshot["diagnostic_revision"] == "ms28-b3c-resolver-v1"
    assert snapshot["capture_state"] == "complete"
    assert snapshot["attempt_count"] == 1
    attempt = snapshot["attempts"][0]
    assert attempt["status"] == "completed"
    assert attempt["plan_origin"] == "resolved"
    assert any(
        row["phase"] == "base_events" and row["pass_kind"] == "primary"
        for row in attempt["phase_records"]
    )
    assert any(
        row["phase"] == "adjustment_apply"
        and row["pass_kind"] == "manual_comparison"
        for row in attempt["phase_records"]
    )


def test_invalid_timeline_keeps_leaf_code_and_local_event_context() -> None:
    collector = ResolverDiagnosticsCollector()
    with pytest.raises(AdjustmentContractError) as exc_info:
        resolve_effective_shape_plan(_input(Point(0.5, vowel="not-a-vowel")), diagnostics=collector)

    error = exc_info.value
    assert error.safe_code == "vowel_unsupported"
    assert error.safe_phase == "base_events"
    assert error.safe_field_code == "vowel"
    snapshot = collector.snapshot()
    failure = snapshot["attempts"][0]["failure"]
    assert failure["failure_code"] == "vowel_unsupported"
    assert failure["phase"] == "base_events"
    assert failure["field_code"] == "vowel"
    assert failure["event_index"] == 0
    assert failure["event_role"] == "subject"


def test_observation_failure_is_not_collapsed_to_ui_boundary_code() -> None:
    collector = ResolverDiagnosticsCollector()
    with pytest.raises(AdjustmentContractError) as exc_info:
        resolve_effective_shape_plan(
            _input(Point(0.5), observations=()),
            diagnostics=collector,
        )

    assert exc_info.value.safe_code == "observation_count_mismatch"
    assert exc_info.value.safe_phase == "observations"
    failure = collector.snapshot()["attempts"][0]["failure"]
    assert failure["failure_code"] == "observation_count_mismatch"
    assert failure["details"]["expected_count"] == 1
    assert failure["details"]["observed_count"] == 0


def test_admission_failure_keeps_constructor_boundary_detail() -> None:
    collector = ResolverDiagnosticsCollector()
    with pytest.raises(AdjustmentContractError) as exc_info:
        resolve_effective_shape_plan(
            _input(Point(0.5, duration_sec=0.0)),
            diagnostics=collector,
        )

    assert exc_info.value.safe_code == "admission_boundary_invalid"
    failure = collector.snapshot()["attempts"][0]["failure"]
    assert failure["details_availability"] == "available"
    details = failure["details"]
    assert details["detail_revision"] == "ms28-b3c-admission-detail-v1"
    assert details["detail_capture_state"] == "available"
    assert details["event_context"]["event_index"] == 0
    assert details["event_context"]["effective_event_range"] == [15, 15]
    assert details["event_context"]["event_range_status"] == "zero_width"
    assert details["range_derivation"]["effective_range_before_validation"] == [15, 15]
    assert details["admission_candidate"]["shape_provenance"]
    assert details["event_context"]["adjacent"]["previous_event_index"] == "not_applicable"


def test_admission_detail_serializer_is_bounded_and_keeps_legacy_details() -> None:
    detail = {
        "detail_capture_state": "available",
        "section_status": {
            "event_context": {"state": "available", "reason": "not_applicable"},
            "admission_candidate": {"state": "available", "reason": "not_applicable"},
            "range_derivation": {"state": "available", "reason": "not_applicable"},
        },
        "event_context": {
            "event_index": 0,
            "vowel": "あ",
            "effective_event_range": (10, 20),
        },
        "admission_candidate": {
            "shape_provenance": [
                {
                    "shape_ordinal": index,
                    "shape_kind": "asymmetric_trapezoid",
                    "real_base_event_indices": (0,),
                    "event_range": (10, 20),
                    "shape_range": (10, 20),
                    "control_points": [
                        {"frame_no": point, "value": 0.5, "point_kind": "top"}
                        for point in range(20)
                    ],
                }
                for index in range(20)
            ]
        },
        "range_derivation": {
            "effective_range_before_validation": (10, 20),
        },
    }
    serialized = serialize_admission_detail(detail)
    assert serialized["admission_candidate"]["shape_provenance"]["recorded"] == 16
    assert serialized["admission_candidate"]["shape_provenance"]["total"] == 20
    assert serialized["admission_candidate"]["shape_provenance"]["truncated"] is True
    assert len(
        serialized["admission_candidate"]["shape_provenance"]["items"][0]["control_points"]["items"]
    ) == 16
    assert serialized["detail_capture_state"] == "partial"
    assert serialized["unavailable_reason"] == "truncated"
    assert "private" not in json.dumps(serialized, ensure_ascii=False)

    collector = ResolverDiagnosticsCollector()
    error = AdjustmentContractError(
        "private path C:/secret/input.txt",
        safe_code="admission_range_invalid",
        safe_field_code="effective_frame_range",
        safe_phase="silence_admission",
        safe_details={"expected_count": 1},
    )
    collector.start_attempt()
    collector.phase_started("silence_admission")
    collector.phase_failed(
        "silence_admission",
        error,
        failure_detail=detail,
        fallback_code="admission_range_invalid",
    )
    failure = collector.snapshot()["attempts"][0]["failure"]
    assert failure["details"]["expected_count"] == 1
    assert failure["details"]["detail_revision"] == "ms28-b3c-admission-detail-v1"
    assert "private path" not in json.dumps(failure, ensure_ascii=False)


def test_collector_is_bounded_and_does_not_store_raw_error_text() -> None:
    collector = ResolverDiagnosticsCollector(max_phase_records=1, max_attempts=1)
    collector.start_attempt()
    collector.phase_started("base_events")
    error = AdjustmentContractError(
        "private path C:/secret/input.txt",
        safe_code="vowel_unsupported",
        safe_field_code="vowel",
        safe_phase="base_events",
        safe_details={"value": float("inf"), "private": "do-not-store"},
    )
    collector.phase_failed("base_events", error, fallback_code="unknown_contract_failure")
    collector.start_attempt()
    payload = json.dumps(collector.snapshot(), ensure_ascii=False)
    assert "private path" not in payload
    assert "C:/secret" not in payload
    assert "do-not-store" not in payload
    assert "not_available" in payload
    assert collector.snapshot()["truncation"]["limited"] is True


def test_disabled_collector_has_no_attempt_history_and_same_result() -> None:
    base = _input(Point(0.5))
    disabled = ResolverDiagnosticsCollector(enabled=False)
    assert resolve_effective_shape_plan(base, diagnostics=disabled) == resolve_effective_shape_plan(base)
    assert disabled.snapshot()["capture_state"] == "disabled"
    assert disabled.snapshot()["attempts"] == []
