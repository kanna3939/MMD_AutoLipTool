from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeControlPoint,
    ShapeParameters,
    apply_adjustment_update,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import AdjustmentContractError, EventAdjustment
from src.core.pipeline import (
    _refine_timeline_intervals_with_observations,
    _repair_resolver_same_morph_boundaries,
    build_even_vowel_timeline,
)
from src.core.preview_transform import (
    build_preview_data_from_effective_shape_plan,
)
from src.core.text_processing import hiragana_to_vowel_tokens
from src.vmd_writer import VowelTimelinePoint
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)


def _long_input(*, mode: str = "hold", hold: int = 0, softness: int = 0) -> BaseTimingPlanInput:
    points = (
        VowelTimelinePoint(0.2, "あ", value=0.6, duration_sec=0.2, start_sec=0.1, end_sec=0.3, vowel_token_index=0),
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
    )
    return BaseTimingPlanInput(
        points,
        None,
        30,
        ShapeParameters(hold, softness, mode),
    )


def _regular_before_long_input(*, hold: int = 1, softness: int = 1) -> BaseTimingPlanInput:
    points = (
        VowelTimelinePoint(
            0.1,
            "あ",
            value=0.6,
            duration_sec=0.2,
            start_sec=0.0,
            end_sec=0.2,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            8 / 30,
            "あ",
            value=0.4,
            duration_sec=0.2,
            start_sec=6 / 30,
            end_sec=10 / 30,
            vowel_token_index=1,
        ),
        VowelTimelinePoint(
            12 / 30,
            "あ",
            value=0.4,
            duration_sec=0.2,
            start_sec=10 / 30,
            end_sec=15 / 30,
            vowel_token_index=2,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=1,
        ),
    )
    return BaseTimingPlanInput(
        points,
        None,
        30,
        ShapeParameters(hold, softness),
    )


def _consecutive_long_input(*, hold: int = 1, softness: int = 1) -> BaseTimingPlanInput:
    points = (
        VowelTimelinePoint(
            6 / 30,
            "あ",
            value=0.6,
            duration_sec=8 / 30,
            start_sec=0.0,
            end_sec=8 / 30,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            9 / 30,
            "あ",
            value=0.4,
            duration_sec=2 / 30,
            start_sec=8 / 30,
            end_sec=10 / 30,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
        VowelTimelinePoint(
            12 / 30,
            "あ",
            value=0.5,
            duration_sec=4 / 30,
            start_sec=11 / 30,
            end_sec=15 / 30,
            vowel_token_index=2,
        ),
        VowelTimelinePoint(
            16 / 30,
            "あ",
            value=0.3,
            duration_sec=4 / 30,
            start_sec=15 / 30,
            end_sec=19 / 30,
            vowel_token_index=3,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=2,
        ),
    )
    return BaseTimingPlanInput(
        points,
        None,
        30,
        ShapeParameters(hold, softness),
    )


def _adjacent_long_boundary_timeline(*, start: int, peak: int, end: int) -> tuple[VowelTimelinePoint, ...]:
    return (
        VowelTimelinePoint(
            6 / 30,
            "あ",
            value=0.6,
            duration_sec=10 / 30,
            start_sec=0.0,
            end_sec=10 / 30,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            14 / 30,
            "あ",
            value=0.4,
            duration_sec=8 / 30,
            start_sec=10 / 30,
            end_sec=18 / 30,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
        VowelTimelinePoint(
            peak / 30,
            "あ",
            value=0.5,
            duration_sec=(end - start) / 30,
            start_sec=start / 30,
            end_sec=end / 30,
            vowel_token_index=2,
        ),
        VowelTimelinePoint(
            (end + 2) / 30,
            "あ",
            value=0.3,
            duration_sec=2 / 30,
            start_sec=end / 30,
            end_sec=(end + 2) / 30,
            vowel_token_index=3,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=2,
        ),
    )


def _interleaved_long_boundary_timeline(*, start: int) -> tuple[VowelTimelinePoint, ...]:
    return (
        VowelTimelinePoint(
            6 / 30,
            "あ",
            value=0.6,
            duration_sec=10 / 30,
            start_sec=0.0,
            end_sec=10 / 30,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            14 / 30,
            "あ",
            value=0.4,
            duration_sec=8 / 30,
            start_sec=10 / 30,
            end_sec=18 / 30,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
        VowelTimelinePoint(
            18 / 30,
            "い",
            value=0.2,
            duration_sec=2 / 30,
            start_sec=18 / 30,
            end_sec=20 / 30,
            vowel_token_index=2,
        ),
        VowelTimelinePoint(
            19 / 30,
            "あ",
            value=0.5,
            duration_sec=(24 - start) / 30,
            start_sec=start / 30,
            end_sec=24 / 30,
            vowel_token_index=3,
        ),
        VowelTimelinePoint(
            26 / 30,
            "あ",
            value=0.3,
            duration_sec=2 / 30,
            start_sec=24 / 30,
            end_sec=26 / 30,
            vowel_token_index=4,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=3,
        ),
    )


def _chained_long_boundary_timeline(
    *,
    with_continuation: bool = True,
) -> tuple[VowelTimelinePoint, ...]:
    points = [
        VowelTimelinePoint(
            6 / 30,
            "あ",
            value=0.6,
            duration_sec=10 / 30,
            start_sec=0.0,
            end_sec=10 / 30,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            14 / 30,
            "あ",
            value=0.4,
            duration_sec=8 / 30,
            start_sec=10 / 30,
            end_sec=18 / 30,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
        VowelTimelinePoint(
            18 / 30,
            "あ",
            value=0.5,
            duration_sec=2 / 30,
            start_sec=17 / 30,
            end_sec=19 / 30,
            vowel_token_index=2,
        ),
    ]
    if with_continuation:
        points.append(
            VowelTimelinePoint(
                21 / 30,
                "あ",
                value=0.3,
                duration_sec=2 / 30,
                start_sec=19 / 30,
                end_sec=21 / 30,
                vowel_token_index=3,
                is_long_vowel_continuation=True,
                long_vowel_source_token_index=2,
            )
        )
    return tuple(points)


def test_regular_tail_uses_long_source_as_successor_boundary() -> None:
    plan = resolve_effective_shape_plan(_regular_before_long_input())
    regular_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0,))

    assert regular_shape.resolved_tail is not None
    assert regular_shape.resolved_tail.requested_hold_frames == 1
    assert regular_shape.resolved_tail.requested_softness_frames == 1
    assert regular_shape.resolved_tail.effective_hold_frames == 0
    assert regular_shape.resolved_tail.effective_softness_frames == 0
    assert regular_shape.resolved_tail.available_extension_frames == 0


def test_regular_tail_preserves_nonzero_controls_when_gap_is_available() -> None:
    points = (
        VowelTimelinePoint(
            0.1,
            "あ",
            value=0.6,
            duration_sec=0.2,
            start_sec=0.0,
            end_sec=0.2,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            14 / 30,
            "あ",
            value=0.4,
            duration_sec=0.2,
            start_sec=12 / 30,
            end_sec=16 / 30,
            vowel_token_index=1,
        ),
        VowelTimelinePoint(
            18 / 30,
            "あ",
            value=0.4,
            duration_sec=0.2,
            start_sec=16 / 30,
            end_sec=21 / 30,
            vowel_token_index=2,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=1,
        ),
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(points, None, 30, ShapeParameters(1, 1))
    )
    regular_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0,))

    assert regular_shape.resolved_tail is not None
    assert regular_shape.resolved_tail.available_extension_frames == 5
    assert regular_shape.resolved_tail.effective_hold_frames == 1
    assert regular_shape.resolved_tail.effective_softness_frames == 1


def test_long_run_uses_next_long_source_as_successor_boundary() -> None:
    plan = resolve_effective_shape_plan(_consecutive_long_input())
    first_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0, 1))

    assert first_shape.resolved_tail is not None
    assert first_shape.resolved_tail.requested_hold_frames == 1
    assert first_shape.resolved_tail.requested_softness_frames == 1
    assert first_shape.resolved_tail.effective_hold_frames == 1
    assert first_shape.resolved_tail.effective_softness_frames == 0
    assert first_shape.resolved_tail.available_extension_frames == 0


def test_same_frame_long_handoff_emits_shared_zero_boundary() -> None:
    points = (
        VowelTimelinePoint(
            160 / 30,
            "あ",
            value=0.6,
            duration_sec=15 / 30,
            start_sec=145 / 30,
            end_sec=165 / 30,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            168 / 30,
            "あ",
            value=0.4,
            duration_sec=5 / 30,
            start_sec=165 / 30,
            end_sec=170 / 30,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
        VowelTimelinePoint(
            175 / 30,
            "あ",
            value=0.5,
            duration_sec=10 / 30,
            start_sec=170 / 30,
            end_sec=180 / 30,
            vowel_token_index=2,
        ),
        VowelTimelinePoint(
            184 / 30,
            "あ",
            value=0.3,
            duration_sec=9 / 30,
            start_sec=180 / 30,
            end_sec=189 / 30,
            vowel_token_index=3,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=2,
        ),
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            points,
            None,
            210,
            ShapeParameters(closing_hold_frames=1, closing_softness_frames=1),
        )
    )

    first_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0, 1))
    second_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (2, 3))
    assert [(point.frame_no, point.value, point.point_kind) for point in first_shape.control_points] == [
        (145, 0.0, "start_zero"),
        (160, 0.6, "top"),
        (170, 0.0, "end_zero"),
    ]
    assert second_shape.control_points[0] == ShapeControlPoint(170, 0.0, "start_zero")

    preview = build_preview_data_from_effective_shape_plan(plan)
    frames = build_morph_frames_from_effective_shape_plan(plan, apply_final_normalization=False)
    assert (170, "あ", 0.0) in frames
    assert any(
        segment.frame_range is not None and segment.frame_range[0] == 170
        for row in preview.rows
        for segment in row.segments
        if segment.vowel == "あ"
    )


@pytest.mark.parametrize(
    ("start", "peak", "end", "expected_start", "expected_peak"),
    [
        (19, 20, 24, 19, 20),
        (19, 19, 24, 19, 20),
        (17, 21, 24, 19, 21),
        (17, 19, 24, 19, 20),
        (20, 20, 24, 20, 20),
    ],
    ids=("normal", "peak_collision", "start_intrusion", "start_and_peak_collision", "collision_free_equal"),
)
def test_pipeline_applies_b2_adjacent_long_boundary_contract(
    start: int,
    peak: int,
    end: int,
    expected_start: int,
    expected_peak: int,
) -> None:
    repaired = _repair_resolver_same_morph_boundaries(
        _adjacent_long_boundary_timeline(start=start, peak=peak, end=end)
    )

    assert round(repaired[2].start_sec * 30) == expected_start
    assert round(repaired[2].time_sec * 30) == expected_peak
    assert round(repaired[2].end_sec * 30) == end
    assert repaired[2].duration_sec == repaired[2].end_sec - repaired[2].start_sec
    assert _repair_resolver_same_morph_boundaries(repaired) == repaired


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_raw_resolver_same_frame_handoff_uses_canonical_zero(mode: str) -> None:
    timeline = _adjacent_long_boundary_timeline(start=18, peak=19, end=24)
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline,
            None,
            30,
            ShapeParameters(long_vowel_mode=mode),
        )
    )

    first_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0, 1))
    second_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (2, 3))
    assert first_shape.control_points[-1] == ShapeControlPoint(18, 0.0, "end_zero")
    assert second_shape.control_points[0] == ShapeControlPoint(18, 0.0, "start_zero")
    assert any(point.frame_no == 19 and point.value > 0.0 for point in second_shape.control_points)
    assert not any(
        point.frame_no == 18 and point.value > 0.0
        for shape in plan.shapes
        for point in shape.control_points
    )


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_raw_resolver_same_frame_peak_conflict_fails_closed(mode: str) -> None:
    timeline = _adjacent_long_boundary_timeline(start=18, peak=18, end=24)

    with pytest.raises(AdjustmentContractError, match="required zero"):
        resolve_effective_shape_plan(
            BaseTimingPlanInput(
                timeline,
                None,
                30,
                ShapeParameters(long_vowel_mode=mode),
            )
        )


@pytest.mark.parametrize("end", (24, 19))
@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_pipeline_repairs_same_frame_peak_when_room_exists(mode: str, end: int) -> None:
    repaired = _repair_resolver_same_morph_boundaries(
        _adjacent_long_boundary_timeline(start=18, peak=18, end=end)
    )
    assert round(repaired[2].start_sec * 30) == 18
    assert round(repaired[2].time_sec * 30) == 19
    assert round(repaired[2].end_sec * 30) == end

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            tuple(repaired),
            None,
            30,
            ShapeParameters(long_vowel_mode=mode),
        )
    )
    assert plan.shapes


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_pipeline_same_frame_peak_without_room_fails_closed(mode: str) -> None:
    timeline = _adjacent_long_boundary_timeline(start=18, peak=18, end=18)
    repaired = _repair_resolver_same_morph_boundaries(timeline)
    assert repaired == list(timeline)

    with pytest.raises(AdjustmentContractError, match="required zero"):
        resolve_effective_shape_plan(
            BaseTimingPlanInput(
                tuple(repaired),
                None,
                30,
                ShapeParameters(long_vowel_mode=mode),
            )
        )


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_collision_free_equal_start_peak_resolves_without_opening_zero(mode: str) -> None:
    timeline = _adjacent_long_boundary_timeline(start=20, peak=20, end=24)
    repaired = _repair_resolver_same_morph_boundaries(timeline)
    assert repaired == list(timeline)

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            tuple(repaired),
            None,
            30,
            ShapeParameters(long_vowel_mode=mode),
        )
    )
    second_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (2, 3))
    assert not any(point.point_kind == "start_zero" for point in second_shape.control_points)
    assert ShapeControlPoint(20, 0.5, "top") in second_shape.control_points


@pytest.mark.parametrize(("start", "expected_start", "expected_peak"), [(18, 18, 19), (17, 18, 19)])
def test_b2_interleaved_boundary_keeps_existing_contract(
    start: int,
    expected_start: int,
    expected_peak: int,
) -> None:
    timeline = _interleaved_long_boundary_timeline(start=start)
    repaired = _repair_resolver_same_morph_boundaries(timeline)

    assert round(repaired[3].start_sec * 30) == expected_start
    assert round(repaired[3].time_sec * 30) == expected_peak
    assert repaired[2] == timeline[2]
    assert repaired[4] == timeline[4]


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_chained_long_source_uses_compact_handoff(mode: str) -> None:
    timeline = _chained_long_boundary_timeline()
    repaired = _repair_resolver_same_morph_boundaries(timeline)

    assert round(repaired[2].start_sec * 30) == 18
    assert round(repaired[2].time_sec * 30) == 19
    assert round(repaired[2].end_sec * 30) == 19
    assert repaired[3] == timeline[3]
    assert _repair_resolver_same_morph_boundaries(repaired) == repaired

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            tuple(repaired),
            None,
            30,
            ShapeParameters(long_vowel_mode=mode),
        )
    )
    first_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0, 1))
    chained_shape = next(shape for shape in plan.shapes if shape.real_base_event_indices == (2, 3))
    assert first_shape.control_points[-1] == ShapeControlPoint(18, 0.0, "end_zero")
    assert ShapeControlPoint(18, 0.0, "start_zero") in chained_shape.control_points
    assert ShapeControlPoint(19, 0.5, "top") in chained_shape.control_points
    assert plan.effective_events[3].long_vowel_source_token_index == 2

    preview = build_preview_data_from_effective_shape_plan(plan)
    preview_points = sorted(
        (point.frame_no, segment.vowel, point.value)
        for row in preview.rows
        for segment in row.segments
        for point in segment.control_points
    )
    writer_points = sorted(
        build_morph_frames_from_effective_shape_plan(
            plan,
            apply_final_normalization=False,
        )
    )
    assert preview_points == writer_points


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_b2_without_chained_continuation_remains_fail_closed(mode: str) -> None:
    timeline = _chained_long_boundary_timeline(with_continuation=False)
    repaired = _repair_resolver_same_morph_boundaries(timeline)
    assert repaired == list(timeline)

    with pytest.raises(
        AdjustmentContractError,
        match="required zero|long-vowel hold cannot close before the next shape",
    ):
        resolve_effective_shape_plan(
            BaseTimingPlanInput(
                tuple(repaired),
                None,
                30,
                ShapeParameters(long_vowel_mode=mode),
            )
        )


def test_default_hold_has_terminal_plateau_and_post_terminal_zero() -> None:
    plan = resolve_effective_shape_plan(_long_input())
    shape = plan.shapes[0]
    assert shape.shape_kind == "long_vowel_hold"
    assert shape.real_base_event_indices == (0, 1)
    assert [(point.frame_no, point.value, point.point_kind) for point in shape.control_points] == [
        (3, 0.0, "start_zero"),
        (6, 0.6, "top"),
        (18, 0.6, "top"),
        (19, 0.0, "end_zero"),
    ]
    assert plan.long_vowel_runs[0].resolved_mode == "hold"


def test_decay_is_single_linear_segment_with_exact_zero_and_latent_tail() -> None:
    plan = resolve_effective_shape_plan(_long_input(mode="decay", hold=2, softness=3), [EventAdjustment(1, slope_ratio=0.4)])
    shape = plan.shapes[0]
    assert shape.shape_kind == "long_vowel_decay"
    assert [(point.frame_no, point.value, point.point_kind) for point in shape.control_points] == [
        (3, 0.0, "start_zero"),
        (6, 0.6, "top"),
        (18, 0.0, "end_zero"),
    ]
    assert shape.control_points[-1].value == 0.0
    assert shape.resolved_tail is not None
    assert shape.resolved_tail.requested_hold_frames == 2
    assert shape.resolved_tail.requested_softness_frames == 3
    assert shape.resolved_tail.effective_hold_frames == 0
    assert not shape.resolved_tail.has_slope_midpoint


def test_terminal_mode_override_wins_over_global_mode() -> None:
    plan = resolve_effective_shape_plan(
        _long_input(mode="hold"),
        [EventAdjustment(1, long_vowel_mode="decay")],
    )
    assert plan.shapes[0].shape_kind == "long_vowel_decay"
    assert plan.canonical_adjustment_snapshot.adjustments[0].long_vowel_mode == "decay"


@pytest.mark.parametrize(
    "adjustment",
    [
        EventAdjustment(0, end_offset_frames=1),
        EventAdjustment(0, hold_frames=1),
        EventAdjustment(1, peak_value=0.8),
        EventAdjustment(1, start_offset_frames=-1),
        EventAdjustment(0, long_vowel_mode="hold"),
    ],
)
def test_long_run_adjustment_ownership_is_enforced(adjustment: EventAdjustment) -> None:
    with pytest.raises(AdjustmentContractError):
        resolve_effective_shape_plan(_long_input(), [adjustment])


def test_same_morph_required_zero_positive_conflict_is_rejected() -> None:
    base = _long_input(mode="decay")
    next_point = VowelTimelinePoint(0.6, "あ", value=0.7, duration_sec=0.06, start_sec=17 / 30, end_sec=19 / 30, vowel_token_index=2)
    with pytest.raises(AdjustmentContractError, match="required zero"):
        resolve_effective_shape_plan(
            BaseTimingPlanInput(base.timeline + (next_point,), None, 30, base.shape_parameters)
        )


def test_same_vowel_without_marker_stays_regular_group() -> None:
    points = (
        VowelTimelinePoint(0.2, "あ", value=0.6, duration_sec=0.2, start_sec=0.1, end_sec=0.3),
        VowelTimelinePoint(0.5, "あ", value=0.4, duration_sec=0.2, start_sec=0.4, end_sec=0.6),
    )
    plan = resolve_effective_shape_plan(BaseTimingPlanInput(points, None, 30))
    assert plan.long_vowel_runs == ()
    assert plan.shapes[0].shape_kind in {"multi_point_envelope", "asymmetric_trapezoid"}


def test_even_fallback_long_terminal_and_next_same_vowel_peak_conflict() -> None:
    tokens = hiragana_to_vowel_tokens("あーあ")
    timeline = build_even_vowel_timeline(
        [token.vowel for token in tokens],
        0.0,
        1.5,
        tokens=tokens,
    )
    with pytest.raises(AdjustmentContractError, match="required zero"):
        resolve_effective_shape_plan(BaseTimingPlanInput(tuple(timeline), None, 45, ShapeParameters(long_vowel_mode="decay")))


def test_pipeline_repairs_long_terminal_and_next_same_vowel_for_preview() -> None:
    tokens = hiragana_to_vowel_tokens("あーあ")
    raw_timeline = build_even_vowel_timeline(
        [token.vowel for token in tokens],
        0.0,
        1.5,
        tokens=tokens,
    )
    with patch(
        "src.core.pipeline.load_rms_series",
        side_effect=OSError("mocked RMS failure"),
    ):
        observed = _refine_timeline_intervals_with_observations(
            timeline=raw_timeline,
            wav_path="dummy.wav",
            speech_start_sec=0.0,
            speech_end_sec=1.5,
            upper_limit=0.5,
        )

    terminal_end_frame = round(observed.timeline[1].end_sec * 30)
    next_start_frame = round(observed.timeline[2].start_sec * 30)
    next_peak_frame = round(observed.timeline[2].time_sec * 30)
    assert next_start_frame == terminal_end_frame + 1
    assert next_peak_frame > next_start_frame

    for mode in ("hold", "decay"):
        plan = resolve_effective_shape_plan(
            BaseTimingPlanInput(
                tuple(observed.timeline),
                tuple(observed.observations or ()),
                45,
                ShapeParameters(long_vowel_mode=mode),
            )
        )
        preview = build_preview_data_from_effective_shape_plan(plan)
        source_indices = {
            source_index
            for row in preview.rows
            for segment in row.segments
            for source_index in segment.source_event_indices
        }
        assert source_indices == {0, 1, 2}
        preview_points = sorted(
            (point.frame_no, segment.vowel, point.value)
            for row in preview.rows
            for segment in row.segments
            for point in segment.control_points
        )
        writer_points = sorted(
            build_morph_frames_from_effective_shape_plan(
                plan,
                apply_final_normalization=False,
            )
        )
        assert preview_points == writer_points


def test_pipeline_repairs_consecutive_same_vowel_long_runs_for_preview() -> None:
    timeline = (
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
        VowelTimelinePoint(
            0.6,
            "あ",
            value=0.5,
            duration_sec=0.2,
            start_sec=17 / 30,
            end_sec=0.8,
            vowel_token_index=2,
        ),
        VowelTimelinePoint(
            0.9,
            "あ",
            value=0.3,
            duration_sec=0.2,
            start_sec=0.8,
            end_sec=1.0,
            vowel_token_index=3,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=2,
        ),
    )
    with patch(
        "src.core.pipeline.load_rms_series",
        side_effect=OSError("mocked RMS failure"),
    ):
        observed = _refine_timeline_intervals_with_observations(
            timeline=timeline,
            wav_path="dummy.wav",
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.6,
        )

    previous_terminal_end_frame = round(observed.timeline[1].end_sec * 30)
    next_long_source_start_frame = round(observed.timeline[2].start_sec * 30)
    next_long_source_peak_frame = round(observed.timeline[2].time_sec * 30)
    assert next_long_source_start_frame == previous_terminal_end_frame + 1
    assert next_long_source_peak_frame > next_long_source_start_frame

    for mode in ("hold", "decay"):
        plan = resolve_effective_shape_plan(
            BaseTimingPlanInput(
                tuple(observed.timeline),
                tuple(observed.observations or ()),
                30,
                ShapeParameters(long_vowel_mode=mode),
            )
        )
        preview = build_preview_data_from_effective_shape_plan(plan)
        assert {
            source_index
            for row in preview.rows
            for segment in row.segments
            for source_index in segment.source_event_indices
        } == {0, 1, 2, 3}


def test_pipeline_repairs_regular_same_vowel_before_long_source() -> None:
    tokens = hiragana_to_vowel_tokens("ああー")
    raw_timeline = build_even_vowel_timeline(
        [token.vowel for token in tokens],
        0.0,
        1.5,
        tokens=tokens,
    )
    with patch(
        "src.core.pipeline.load_rms_series",
        side_effect=OSError("mocked RMS failure"),
    ):
        observed = _refine_timeline_intervals_with_observations(
            timeline=raw_timeline,
            wav_path="dummy.wav",
            speech_start_sec=0.0,
            speech_end_sec=1.5,
            upper_limit=0.5,
        )

    previous_end_frame = round(observed.timeline[0].end_sec * 30)
    long_start_frame = round(observed.timeline[1].start_sec * 30)
    long_peak_frame = round(observed.timeline[1].time_sec * 30)
    assert long_start_frame == previous_end_frame
    assert long_peak_frame > long_start_frame

    for mode in ("hold", "decay"):
        plan = resolve_effective_shape_plan(
            BaseTimingPlanInput(
                tuple(observed.timeline),
                tuple(observed.observations or ()),
                45,
                ShapeParameters(long_vowel_mode=mode),
            )
        )
        preview = build_preview_data_from_effective_shape_plan(plan)
        assert {
            source_index
            for row in preview.rows
            for segment in row.segments
            for source_index in segment.source_event_indices
        } == {0, 1, 2}


def test_pipeline_repairs_interleaved_same_morph_overlap() -> None:
    raw_timeline = [
        VowelTimelinePoint(
            0.2,
            "あ",
            value=0.6,
            duration_sec=0.4,
            start_sec=0.1,
            end_sec=0.5,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            0.5,
            "い",
            value=0.4,
            duration_sec=0.1,
            start_sec=0.45,
            end_sec=0.55,
            vowel_token_index=1,
        ),
        VowelTimelinePoint(
            16 / 30,
            "あ",
            value=0.5,
            duration_sec=6 / 30,
            start_sec=14 / 30,
            end_sec=20 / 30,
            vowel_token_index=2,
        ),
    ]
    with pytest.raises(AdjustmentContractError, match="required zero"):
        resolve_effective_shape_plan(
            BaseTimingPlanInput(tuple(raw_timeline), None, 30)
        )

    with patch(
        "src.core.pipeline.load_rms_series",
        side_effect=OSError("mocked RMS failure"),
    ):
        observed = _refine_timeline_intervals_with_observations(
            timeline=raw_timeline,
            wav_path="dummy.wav",
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

    previous_end_frame = round(observed.timeline[0].end_sec * 30)
    next_start_frame = round(observed.timeline[2].start_sec * 30)
    next_peak_frame = round(observed.timeline[2].time_sec * 30)
    assert next_start_frame == previous_end_frame
    assert next_peak_frame > next_start_frame

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            tuple(observed.timeline),
            tuple(observed.observations or ()),
            30,
        )
    )
    preview = build_preview_data_from_effective_shape_plan(plan)
    assert {
        source_index
        for row in preview.rows
        for segment in row.segments
        for source_index in segment.source_event_indices
    } == {0, 1, 2}


def test_different_morph_same_frame_zero_is_allowed() -> None:
    base = _long_input(mode="decay")
    next_point = VowelTimelinePoint(0.6, "い", value=0.7, duration_sec=0.06, start_sec=17 / 30, end_sec=19 / 30, vowel_token_index=2)
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(base.timeline + (next_point,), None, 30, base.shape_parameters)
    )
    assert {shape.vowel for shape in plan.shapes} == {"あ", "い"}
