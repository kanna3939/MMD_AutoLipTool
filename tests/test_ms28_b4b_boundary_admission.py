from types import SimpleNamespace

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    EffectiveShapeEvent,
    EventSilenceAdmission,
    _boundary_relation_for_event,
    resolve_effective_shape_plan,
)
from src.core.effective_shape_diagnostics import ResolverDiagnosticsCollector
from src.core.event_adjustment import AdjustmentContractError
from src.core.pipeline import _build_peak_value_observations
from src.gui_wx.main_frame import (
    MainFrame,
    _build_debug_silence_observations,
    _debug_boundary_admission_checks,
    _debug_failure_context_from_error,
    _debug_safe_silence_reason,
)
from src.vmd_writer import VowelTimelinePoint


def _boundary_timeline(
    *,
    next_start_sec: float = 1.0,
    previous_end_sec: float = 1.0,
    boundary_peak_value: float = 0.0,
) -> tuple[VowelTimelinePoint, ...]:
    return (
        VowelTimelinePoint(
            time_sec=0.8,
            vowel="い",
            value=0.5,
            start_sec=0.7,
            end_sec=previous_end_sec,
        ),
        VowelTimelinePoint(
            time_sec=1.0,
            vowel="あ",
            value=0.0,
            start_sec=1.0,
            end_sec=1.0,
            peak_value=boundary_peak_value,
        ),
        VowelTimelinePoint(
            time_sec=next_start_sec + 0.1,
            vowel="う",
            value=0.5,
            start_sec=next_start_sec,
            end_sec=next_start_sec + 0.3,
        ),
    )


def _boundary_plan(
    *,
    next_start_sec: float = 1.0,
    previous_end_sec: float = 1.0,
    boundary_peak_value: float = 0.0,
):
    return resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=_boundary_timeline(
                next_start_sec=next_start_sec,
                previous_end_sec=previous_end_sec,
                boundary_peak_value=boundary_peak_value,
            ),
            observations=None,
            source_duration_frames=120,
        )
    )


def test_zero_width_end_zero_is_boundary_only_and_required_zero_is_preserved() -> None:
    plan = _boundary_plan()

    admission = plan.event_silence_admissions[1]
    assert admission.enabled is True
    assert admission.boundary_only is True
    assert admission.effective_frame_range is None
    assert admission.boundary_frame == 30
    assert admission.boundary_point_kind == "end_zero"
    assert admission.boundary_relation == "different_vowel_boundary"
    assert admission.boundary_action == "preserved_zero_keyframe"
    assert ("あ", 30) in plan.normalization_contract.required_zero_frames

    zero_shape = next(shape for shape in plan.shapes if shape.vowel == "あ")
    assert [(point.frame_no, point.value, point.point_kind) for point in zero_shape.control_points] == [
        (30, 0.0, "end_zero")
    ]


def test_positive_upstream_peak_with_end_zero_only_shape_is_boundary_only() -> None:
    plan = _boundary_plan(boundary_peak_value=0.2181)

    admission = plan.event_silence_admissions[1]
    assert admission.enabled is True
    assert admission.boundary_only is True
    assert admission.boundary_frame == 30
    assert admission.positive_point_kinds == ()
    assert admission.positive_core_frame_ranges == ()

    zero_shape = next(shape for shape in plan.shapes if shape.vowel == "あ")
    assert [(point.frame_no, point.value, point.point_kind) for point in zero_shape.control_points] == [
        (30, 0.0, "end_zero")
    ]


def test_boundary_relation_prioritizes_same_vowel_same_frame() -> None:
    events = (
        EffectiveShapeEvent(
            base_event_index=10,
            vowel="い",
            start_frame=20,
            peak_frame=25,
            end_frame=30,
            peak_value=0.5,
        ),
        EffectiveShapeEvent(
            base_event_index=11,
            vowel="あ",
            start_frame=30,
            peak_frame=30,
            end_frame=30,
            peak_value=0.0,
        ),
        EffectiveShapeEvent(
            base_event_index=12,
            vowel="あ",
            start_frame=30,
            peak_frame=35,
            end_frame=40,
            peak_value=0.5,
        ),
    )

    assert _boundary_relation_for_event(events, events[1], 30) == "same_vowel_same_frame"


def test_pipeline_observation_records_zero_width_boundary_input() -> None:
    point = VowelTimelinePoint(
        time_sec=1.0,
        vowel="あ",
        value=0.0,
        start_sec=1.0,
        end_sec=1.0,
    )

    observations = _build_peak_value_observations(
        timeline=(point,),
        rms_series=None,
        speech_start_sec=0.0,
        speech_end_sec=2.0,
        upper_limit=0.0,
    )

    assert observations[0].boundary_only is True
    assert observations[0].boundary_frame == 30
    assert observations[0].boundary_point_kind == "end_zero"


@pytest.mark.parametrize(
    ("boundary_frame", "peak_value"),
    [(151, 0.0), (380, 0.2181), (420, 0.2755)],
)
def test_reported_zero_width_frames_reach_effective_shape_plan(
    boundary_frame: int,
    peak_value: float,
) -> None:
    boundary_sec = boundary_frame / 30.0
    timeline = (
        VowelTimelinePoint(
            time_sec=boundary_sec - 0.2,
            vowel="い",
            value=0.5,
            start_sec=boundary_sec - 0.3,
            end_sec=boundary_sec,
        ),
        VowelTimelinePoint(
            time_sec=boundary_sec,
            vowel="あ",
            value=0.0,
            start_sec=boundary_sec,
            end_sec=boundary_sec,
            peak_value=peak_value,
        ),
        VowelTimelinePoint(
            time_sec=boundary_sec + 0.1,
            vowel="う",
            value=0.5,
            start_sec=boundary_sec,
            end_sec=boundary_sec + 0.3,
        ),
    )

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=timeline,
            observations=None,
            source_duration_frames=boundary_frame + 30,
        )
    )

    admission = plan.event_silence_admissions[1]
    assert admission.boundary_only is True
    assert admission.boundary_frame == boundary_frame
    assert ("あ", boundary_frame) in plan.normalization_contract.required_zero_frames


def test_zero_width_end_zero_with_positive_gap_is_classified_as_silence_gap() -> None:
    plan = _boundary_plan(next_start_sec=1.2, previous_end_sec=0.9)

    admission = plan.event_silence_admissions[1]
    assert admission.boundary_only is True
    assert admission.boundary_relation == "silence_gap"
    assert admission.boundary_action == "preserved_zero_keyframe"


def test_zero_width_without_verified_boundary_fails_closed() -> None:
    timeline = (
        VowelTimelinePoint(
            time_sec=1.0,
            vowel="あ",
            value=0.0,
            start_sec=1.0,
            end_sec=1.0,
        ),
    )

    with pytest.raises(AdjustmentContractError) as exc_info:
        resolve_effective_shape_plan(
            BaseTimingPlanInput(
                timeline=timeline,
                observations=None,
                source_duration_frames=60,
            )
        )

    assert exc_info.value.safe_code == "admission_boundary_invalid"


def test_zero_width_positive_peak_does_not_become_boundary_only() -> None:
    with pytest.raises(AdjustmentContractError) as exc_info:
        resolve_effective_shape_plan(
            BaseTimingPlanInput(
                timeline=_boundary_timeline(),
                observations=(
                    SimpleNamespace(
                        event_index=0,
                        vowel="い",
                        silence_core_frame_ranges=(),
                        positive_core_frame_ranges=(),
                        base_event_silence_core_overlap=False,
                    ),
                    SimpleNamespace(
                        event_index=1,
                        vowel="あ",
                        silence_core_frame_ranges=(),
                        positive_core_frame_ranges=((30, 31),),
                        base_event_silence_core_overlap=True,
                    ),
                    SimpleNamespace(
                        event_index=2,
                        vowel="う",
                        silence_core_frame_ranges=(),
                        positive_core_frame_ranges=(),
                        base_event_silence_core_overlap=False,
                    ),
                ),
                source_duration_frames=120,
            )
        )

    assert exc_info.value.safe_code == "admission_boundary_invalid"


def test_boundary_checks_record_positive_event_peak_and_rejection_reason() -> None:
    collector = ResolverDiagnosticsCollector()
    with pytest.raises(AdjustmentContractError):
        resolve_effective_shape_plan(
            BaseTimingPlanInput(
                timeline=_boundary_timeline(boundary_peak_value=0.2755),
                observations=(
                    SimpleNamespace(
                        event_index=0,
                        vowel="い",
                        silence_core_frame_ranges=(),
                        positive_core_frame_ranges=(),
                        base_event_silence_core_overlap=False,
                    ),
                    SimpleNamespace(
                        event_index=1,
                        vowel="あ",
                        silence_core_frame_ranges=(),
                        positive_core_frame_ranges=((30, 31),),
                        base_event_silence_core_overlap=True,
                    ),
                    SimpleNamespace(
                        event_index=2,
                        vowel="う",
                        silence_core_frame_ranges=(),
                        positive_core_frame_ranges=(),
                        base_event_silence_core_overlap=False,
                    ),
                ),
                source_duration_frames=120,
            ),
            diagnostics=collector,
        )

    checks = collector.snapshot()["attempts"][0]["failure"]["details"][
        "admission_candidate"
    ]["boundary_admission_checks"]
    assert checks["event_peak_value"] == pytest.approx(0.2755)
    assert checks["candidate_range"] == "zero_width"
    assert checks["positive_core_frame_ranges_empty"] is False
    assert checks["decision"] == "rejected_boundary_invalid"


def test_b4b_debug_allowlists_keep_boundary_failure_context_and_cross_vowel_reason() -> None:
    error = AdjustmentContractError(
        "boundary contract failure",
        safe_code="admission_boundary_invalid",
        safe_field_code="boundary_frame",
        safe_phase="silence_admission",
        event_index=77,
    )

    context = _debug_failure_context_from_error(error, phase="silence_admission")
    assert context["domain"] == "effective_shape"
    assert context["field_code"] == "boundary_frame"
    assert context["event_index"] == 77
    assert (
        _debug_safe_silence_reason("cross_vowel_handoff_crosses_silence_core")
        == "cross_vowel_handoff_crosses_silence_core"
    )
    assert (
        _debug_safe_silence_reason("cross_vowel_handoff_exceeds_full_span_limit")
        == "cross_vowel_handoff_exceeds_full_span_limit"
    )


def test_boundary_admission_is_present_in_interval_debug_rows() -> None:
    plan = _boundary_plan()
    rows = _build_debug_silence_observations(
        [
            {
                "start_sec": 1.0,
                "end_sec": 1.1,
                "coverage_status": "complete",
                "provenance_status": "complete",
            }
        ],
        [(30, "あ", 0.0)],
        effective_plan=plan,
    )

    boundary_row = next(
        row for row in rows[0]["base_event_admissions"] if row["boundary_only"]
    )
    assert boundary_row["boundary_frame"] == 30
    assert boundary_row["boundary_point_kind"] == "end_zero"
    assert boundary_row["boundary_relation"] == "different_vowel_boundary"
    assert boundary_row["boundary_action"] == "preserved_zero_keyframe"
    assert boundary_row["assignment_status"] == "assigned_interval"
    assert boundary_row["admission_key"].startswith("event:1|vowel:あ|frame:30|")
    assert boundary_row["boundary_admission_checks"] == {
        "candidate_range": "zero_width",
        "positive_point_kinds_empty": True,
        "boundary_positive_point_kinds_empty": True,
        "positive_core_frame_ranges_empty": True,
        "matching_end_zero": True,
        "shape_provenance_available": True,
        "boundary_relation_verified": True,
        "event_peak_value": 0.0,
        "decision": "accepted_boundary_only",
    }


def test_effective_shape_debug_payload_keeps_boundary_diagnostics() -> None:
    plan = _boundary_plan(boundary_peak_value=0.2181)

    payload = MainFrame._debug_shape_plan_payload(plan)
    admission = payload["event_silence_admissions"][1]

    assert admission["boundary_only"] is True
    assert admission["boundary_frame"] == 30
    assert admission["boundary_point_kind"] == "end_zero"
    assert admission["admission_key"].startswith("event:1|vowel:あ|frame:30|")
    assert admission["boundary_admission_checks"]["event_peak_value"] == 0.2181
    assert admission["boundary_admission_checks"]["decision"] == "accepted_boundary_only"


def test_boundary_diagnostics_use_fixed_not_available_for_missing_upstream_data() -> None:
    admission = EventSilenceAdmission(
        event_index=7,
        vowel="あ",
        boundary_only=True,
        boundary_frame=12,
        boundary_point_kind="end_zero",
        boundary_relation="silence_gap",
        boundary_action="preserved_zero_keyframe",
    )

    checks = _debug_boundary_admission_checks(admission, None)

    assert checks["event_peak_value"] == "not_available"
    assert checks["shape_provenance_available"] is False
    assert checks["boundary_relation_verified"] is True
    assert checks["decision"] == "accepted_boundary_only"


def test_unassigned_boundary_is_returned_without_interval_reassignment() -> None:
    plan = _boundary_plan()
    unassigned: list[dict] = []
    rows = _build_debug_silence_observations(
        [
            {
                "start_sec": 2.0,
                "end_sec": 2.1,
                "coverage_status": "complete",
                "provenance_status": "complete",
            }
        ],
        [(60, "あ", 0.0)],
        effective_plan=plan,
        unassigned_boundary_admissions=unassigned,
    )

    assert rows[0]["base_event_admissions"] == []
    assert len(unassigned) == 1
    assert unassigned[0]["boundary_frame"] == 30
    assert unassigned[0]["assignment_status"] == "unassigned"
    assert unassigned[0]["boundary_action"] == "not_applicable"
    assert unassigned[0]["boundary_relation"] == "different_vowel_boundary"
    assert unassigned[0]["admission_key"].startswith("event:1|vowel:あ|frame:30|")
    assert (
        unassigned[0]["boundary_admission_checks"]["decision"]
        == "accepted_boundary_only"
    )
    assert unassigned[0]["reason_code"] == "boundary_interval_unassigned"
