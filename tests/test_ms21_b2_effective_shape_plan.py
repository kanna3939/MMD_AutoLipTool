from __future__ import annotations

from dataclasses import dataclass
import math

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    apply_adjustment_update,
    build_base_plan_identity,
    resolve_effective_shape_plan,
    source_duration_frames_from_seconds,
)
from src.core.event_adjustment import (
    AdjustmentContractError,
    EventAdjustment,
    empty_adjustment_snapshot,
)


@dataclass(frozen=True)
class Point:
    time_sec: float
    vowel: str = "あ"
    value: float = 0.5
    peak_value: float | None = None
    duration_sec: float = 0.2
    start_sec: float | None = None
    end_sec: float | None = None


@dataclass(frozen=True)
class Observation:
    event_index: int
    vowel: str = "あ"
    is_bridgeable_micro_gap_candidate: bool = False
    is_bridgeable_same_vowel_micro_gap_candidate: bool = False
    is_same_vowel_burst_candidate: bool = False
    is_bridgeable_cross_vowel_transition_candidate: bool = False
    is_cross_vowel_zero_run_continuity_floor_candidate: bool = False
    local_peak: float | None = None
    previous_non_zero_event_index: int | None = None
    next_non_zero_event_index: int | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None
    rms_window_times_sec: tuple[float, ...] = ()
    rms_window_values: tuple[float, ...] = ()


def make_input(
    points: tuple[Point, ...],
    *,
    observations: tuple[Observation, ...] | None = None,
    duration: int = 180,
    hold: int = 0,
    softness: int = 0,
) -> BaseTimingPlanInput:
    return BaseTimingPlanInput(
        timeline=points,
        observations=observations,
        source_duration_frames=duration,
        shape_parameters=ShapeParameters(hold, softness),
    )


def test_source_duration_conversion_and_invalid_values() -> None:
    assert source_duration_frames_from_seconds(1.25) == 38
    for value in (None, True, -0.1, math.nan, math.inf):
        with pytest.raises(AdjustmentContractError):
            source_duration_frames_from_seconds(value)


def test_empty_and_observation_none_inputs_are_supported() -> None:
    empty = resolve_effective_shape_plan(make_input((), observations=()))
    assert empty.shapes == ()
    plan = resolve_effective_shape_plan(make_input((Point(1.0),)))
    assert plan.observation_handoffs == ()
    assert plan.effective_events[0].base_event_index == 0


def test_non_empty_timeline_rejects_present_empty_observations() -> None:
    with pytest.raises(AdjustmentContractError, match="length"):
        resolve_effective_shape_plan(make_input((Point(1.0),), observations=()))


@pytest.mark.parametrize(
    "field_value",
    [True, -1, 3],
)
def test_candidate_reference_is_validated_before_lookup(field_value: object) -> None:
    points = (Point(0.5), Point(1.0), Point(1.5))
    observations = (
        Observation(0),
        Observation(
            1,
            is_bridgeable_micro_gap_candidate=True,
            previous_non_zero_event_index=0,
            next_non_zero_event_index=2,
            span_start_index=field_value,  # type: ignore[arg-type]
            span_end_index=1,
        ),
        Observation(2),
    )
    with pytest.raises(AdjustmentContractError) as exc_info:
        resolve_effective_shape_plan(make_input(points, observations=observations))
    assert not isinstance(exc_info.value, IndexError)


def test_candidate_span_and_bracketing_order_are_rejected() -> None:
    points = (Point(0.5), Point(1.0), Point(1.5))
    invalid = (
        Observation(0),
        Observation(
            1,
            is_bridgeable_micro_gap_candidate=True,
            previous_non_zero_event_index=1,
            next_non_zero_event_index=2,
            span_start_index=1,
            span_end_index=1,
        ),
        Observation(2),
    )
    with pytest.raises(AdjustmentContractError, match="bracketing"):
        resolve_effective_shape_plan(make_input(points, observations=invalid))


def test_peak_and_interval_adjustments_preserve_base_input() -> None:
    points = (Point(1.0, start_sec=0.8, end_sec=1.2),)
    base_input = make_input(points)
    before = tuple(points)
    plan = resolve_effective_shape_plan(
        base_input,
        [EventAdjustment(0, peak_value=2.0, start_offset_frames=-1, end_offset_frames=2)],
    )
    event = plan.effective_events[0]
    assert event.peak_value == 2.0
    assert event.start_frame == 23
    assert event.end_frame == 38
    assert tuple(points) == before


def test_invalid_adjustment_frame_order_and_identity_mismatch_are_rejected() -> None:
    base_input = make_input((Point(1.0, start_sec=0.8, end_sec=1.2),))
    with pytest.raises(AdjustmentContractError, match="frame ordering"):
        resolve_effective_shape_plan(base_input, [EventAdjustment(0, start_offset_frames=10)])
    other = make_input((Point(2.0, start_sec=1.8, end_sec=2.2),))
    stale = empty_adjustment_snapshot(build_base_plan_identity(other))
    with pytest.raises(AdjustmentContractError, match="identity mismatch"):
        resolve_effective_shape_plan(base_input, stale)


def test_grouping_keeps_all_real_provenance() -> None:
    plan = resolve_effective_shape_plan(
        make_input(
            (
                Point(1.0, start_sec=0.9, end_sec=1.1),
                Point(1.2, start_sec=1.1, end_sec=1.3),
            )
        )
    )
    assert len(plan.shapes) == 1
    assert plan.shapes[0].real_base_event_indices == (0, 1)
    assert len(plan.shapes[0].event_ranges) == 2


def test_middle_tail_override_is_rejected() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.1),
            Point(1.2, start_sec=1.1, end_sec=1.3),
        )
    )
    with pytest.raises(AdjustmentContractError, match="group tail"):
        resolve_effective_shape_plan(base_input, [EventAdjustment(0, hold_frames=2)])


def test_slope_override_requires_softness_midpoint() -> None:
    base_input = make_input((Point(1.0),), softness=0)
    with pytest.raises(AdjustmentContractError, match="midpoint"):
        resolve_effective_shape_plan(base_input, [EventAdjustment(0, slope_ratio=0.5)])


def test_candidate_provenance_uses_negative_token_and_adjustment_disables_candidate() -> None:
    points = (
        Point(0.5),
        Point(1.0),
        Point(1.2),
        Point(1.7),
    )
    observations = (
        Observation(0),
        Observation(
            1,
            is_same_vowel_burst_candidate=True,
            previous_non_zero_event_index=0,
            next_non_zero_event_index=3,
            span_start_index=1,
            span_end_index=2,
        ),
        Observation(
            2,
            is_same_vowel_burst_candidate=True,
            previous_non_zero_event_index=0,
            next_non_zero_event_index=3,
            span_start_index=1,
            span_end_index=2,
        ),
        Observation(3),
    )
    base_input = make_input(points, observations=observations)
    automatic = resolve_effective_shape_plan(base_input)
    candidate = next(
        shape for shape in automatic.shapes if shape.internal_shape_source_tokens
    )
    assert candidate.internal_shape_source_tokens == (-1,)
    assert candidate.real_base_event_indices == (1, 2)

    adjusted = resolve_effective_shape_plan(
        base_input, [EventAdjustment(1, peak_value=0.8)]
    )
    assert adjusted.observation_handoffs[0].enabled is False
    assert not any(shape.internal_shape_source_tokens for shape in adjusted.shapes)


def test_cross_vowel_candidate_handoff_updates_boundaries_unless_adjusted() -> None:
    points = (
        Point(0.5, vowel="あ", start_sec=0.4, end_sec=0.6),
        Point(1.0, vowel="う", value=0.0, start_sec=0.9, end_sec=1.1),
        Point(1.5, vowel="い", start_sec=1.4, end_sec=1.6),
    )
    observations = (
        Observation(0, vowel="あ"),
        Observation(
            1,
            vowel="う",
            is_bridgeable_cross_vowel_transition_candidate=True,
            previous_non_zero_event_index=0,
            next_non_zero_event_index=2,
        ),
        Observation(2, vowel="い"),
    )
    base_input = make_input(points, observations=observations)
    automatic = resolve_effective_shape_plan(base_input)
    by_index = {event.base_event_index: event for event in automatic.effective_events}
    assert by_index[0].end_frame == 33
    assert by_index[2].start_frame == 27

    adjusted = resolve_effective_shape_plan(
        base_input, [EventAdjustment(1, end_offset_frames=1)]
    )
    by_index = {event.base_event_index: event for event in adjusted.effective_events}
    assert by_index[0].end_frame == 18
    assert by_index[2].start_frame == 42


def test_update_removes_tail_override_when_event_becomes_middle() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.0),
            Point(1.3, start_sec=1.3, end_sec=1.4),
        )
    )
    identity = build_base_plan_identity(base_input)
    current = resolve_effective_shape_plan(
        base_input, [EventAdjustment(0, hold_frames=2)]
    ).canonical_adjustment_snapshot
    result = apply_adjustment_update(
        base_input,
        current,
        EventAdjustment(1, start_offset_frames=-6),
    )
    assert result.removed_tail_override_event_indices == (0,)
    assert all(item.base_event_index != 0 for item in result.canonical_snapshot.adjustments)
    assert result.canonical_snapshot.base_plan_identity == identity


def test_final_tail_may_exceed_duration_but_next_shape_clamps() -> None:
    final = resolve_effective_shape_plan(
        make_input((Point(1.0, start_sec=0.9, end_sec=1.0),), duration=30, hold=3, softness=2)
    )
    assert final.shapes[0].end_frame > 30
    with_next = resolve_effective_shape_plan(
        make_input(
            (
                Point(0.5, start_sec=0.4, end_sec=0.6),
                Point(0.7, vowel="い", start_sec=0.7, end_sec=0.8),
            ),
            duration=30,
            hold=10,
            softness=10,
        )
    )
    assert with_next.shapes[0].end_frame <= with_next.shapes[1].start_frame
