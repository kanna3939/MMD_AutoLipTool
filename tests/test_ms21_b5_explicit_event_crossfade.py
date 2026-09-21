from __future__ import annotations

from dataclasses import dataclass

import pytest

from gui_wx.selected_event_editor import build_selected_event_editor_state
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    resolve_effective_shape_plan,
    resolve_manual_crossfade_end_offset_max,
)
from src.core.event_adjustment import AdjustmentContractError, EventAdjustment
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
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
    vowel: str
    is_bridgeable_cross_vowel_transition_candidate: bool = False
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
    duration: int = 90,
    hold: int = 0,
    softness: int = 0,
) -> BaseTimingPlanInput:
    return BaseTimingPlanInput(
        timeline=points,
        observations=observations,
        source_duration_frames=duration,
        shape_parameters=ShapeParameters(hold, softness),
    )


def crossfade_input(
    *,
    target_value: float = 1.0,
    observations: tuple[Observation, ...] | None = None,
) -> BaseTimingPlanInput:
    return make_input(
        (
            Point(0.3, start_sec=0.2, end_sec=0.4),
            Point(
                0.7,
                vowel="い",
                value=target_value,
                start_sec=0.5,
                end_sec=0.9,
            ),
        ),
        observations=observations,
    )


def test_global_tail_parameters_remain_conservative_and_emit_no_manual_metadata() -> None:
    plan = resolve_effective_shape_plan(
        make_input(
            (
                Point(0.3, start_sec=0.2, end_sec=0.4),
                Point(0.7, vowel="い", start_sec=0.5, end_sec=0.9),
            ),
            hold=6,
            softness=2,
        )
    )

    source = plan.shapes[0]
    assert source.end_frame == 14
    assert plan.shapes[1].start_frame == 15
    assert plan.manual_crossfades == ()


@pytest.mark.parametrize(
    ("adjustment", "global_softness"),
    (
        (EventAdjustment(0, peak_value=0.7), 0),
        (EventAdjustment(0, start_offset_frames=-1), 0),
        (EventAdjustment(0, end_offset_frames=-1), 0),
        (EventAdjustment(0, slope_ratio=0.5), 2),
    ),
)
def test_non_trigger_event_edits_do_not_enable_manual_crossfade(
    adjustment: EventAdjustment,
    global_softness: int,
) -> None:
    base = crossfade_input()
    base_input = make_input(
        base.timeline,
        duration=base.source_duration_frames,
        softness=global_softness,
    )
    plan = resolve_effective_shape_plan(base_input, (adjustment,))

    assert plan.manual_crossfades == ()


def test_event_tail_override_creates_crossfade_and_high_keyframe_metadata() -> None:
    plan = resolve_effective_shape_plan(
        crossfade_input(),
        (EventAdjustment(0, hold_frames=6, softness_frames=2),),
    )

    source, target = plan.shapes
    assert source.end_frame == 20
    assert target.start_frame == 15
    assert target.end_frame == 27
    assert len(plan.manual_crossfades) == 1
    metadata = plan.manual_crossfades[0]
    assert metadata.source_base_event_index == 0
    assert metadata.target_base_event_index == 1
    assert (metadata.overlap_start_frame, metadata.overlap_end_frame) == (17, 19)
    assert tuple(
        (item.frame_no, item.vowel, item.value)
        for item in metadata.high_target_keyframes
    ) == ((18, "い", 1.0),)


def test_selected_editor_exposes_dynamic_range_and_notice_only_for_source() -> None:
    base_input = crossfade_input()
    plan = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, hold_frames=6, softness_frames=2),),
    )

    source_state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=1,
        source_duration_frames=base_input.source_duration_frames,
    )
    target_state = build_selected_event_editor_state(
        plan,
        1,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=1,
        source_duration_frames=base_input.source_duration_frames,
    )

    assert source_state.end_offset_max == 9
    assert source_state.crossfade_notice_header == (
        "次の口形とクロスフェードしています。"
    )
    assert source_state.crossfade_notice_lines == (
        "重複区間内で「い」の開口量が0.95以上に設定されています。",
        "意図した動きかプレビューとMMD上で確認してください。",
    )
    assert target_state.crossfade_notice_header == ""
    assert target_state.crossfade_notice_lines == ()


@pytest.mark.parametrize(
    ("target_value", "expects_notice"),
    (
        (0.949999, False),
        (0.95, True),
        (1.0, True),
        (1.2, True),
    ),
)
def test_high_target_keyframe_threshold_is_notice_only(
    target_value: float,
    expects_notice: bool,
) -> None:
    plan = resolve_effective_shape_plan(
        crossfade_input(target_value=target_value),
        (EventAdjustment(0, hold_frames=6, softness_frames=2),),
    )

    metadata = plan.manual_crossfades[0]
    assert bool(metadata.high_target_keyframes) is expects_notice
    writer_frames = build_morph_frames_from_effective_shape_plan(plan)
    assert (18, "い", target_value) in writer_frames


def test_positive_end_offset_uses_dynamic_limit_and_rejects_excess() -> None:
    base_input = crossfade_input()
    base_plan = resolve_effective_shape_plan(base_input)

    assert resolve_manual_crossfade_end_offset_max(
        base_plan,
        0,
        source_duration_frames=base_input.source_duration_frames,
    ) == 9

    allowed = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, end_offset_frames=9),),
    )
    assert allowed.shapes[0].end_frame == 21
    assert allowed.manual_crossfades

    with pytest.raises(AdjustmentContractError, match="crossfade range"):
        resolve_effective_shape_plan(
            base_input,
            (EventAdjustment(0, end_offset_frames=10),),
        )


def test_actual_overlap_requires_one_non_zero_integer_frame() -> None:
    base_input = crossfade_input()
    no_overlap = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, end_offset_frames=4),),
    )
    one_frame = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, end_offset_frames=5),),
    )

    assert no_overlap.manual_crossfades == ()
    assert len(one_frame.manual_crossfades) == 1
    assert (
        one_frame.manual_crossfades[0].overlap_start_frame,
        one_frame.manual_crossfades[0].overlap_end_frame,
    ) == (16, 16)
    assert one_frame.manual_crossfades[0].high_target_keyframes == ()


def test_zero_only_group_is_retained_but_skipped_when_selecting_target() -> None:
    base_input = make_input(
        (
            Point(0.3, start_sec=0.2, end_sec=0.4),
            Point(0.5, vowel="う", value=0.0, start_sec=0.45, end_sec=0.55),
            Point(0.7, vowel="い", value=1.0, start_sec=0.5, end_sec=0.9),
        )
    )
    plan = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, hold_frames=6),),
    )

    assert len(plan.shapes) == 3
    assert plan.shapes[1].vowel == "う"
    assert all(point.value == 0.0 for point in plan.shapes[1].control_points)
    assert plan.manual_crossfades[0].target_base_event_index == 2


def test_next_active_same_vowel_stops_target_search_and_uses_editor_fallback() -> None:
    base_input = make_input(
        (
            Point(0.3, start_sec=0.2, end_sec=0.4),
            Point(0.8, start_sec=0.6, end_sec=1.0),
            Point(1.2, vowel="い", start_sec=1.1, end_sec=1.3),
        )
    )
    plan = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, hold_frames=6),),
    )

    assert plan.manual_crossfades == ()
    assert resolve_manual_crossfade_end_offset_max(
        plan,
        0,
        source_duration_frames=base_input.source_duration_frames,
    ) == base_input.source_duration_frames - plan.base_events[0].end_frame


def test_third_active_shape_limits_manual_tail_extension() -> None:
    plan = resolve_effective_shape_plan(
        make_input(
            (
                Point(0.3, start_sec=0.2, end_sec=0.4),
                Point(0.7, vowel="い", value=1.0, start_sec=0.5, end_sec=0.9),
                Point(0.8, vowel="う", value=0.8, start_sec=0.65, end_sec=1.0),
            )
        ),
        (EventAdjustment(0, hold_frames=10),),
    )

    source = next(shape for shape in plan.shapes if 0 in shape.real_base_event_indices)
    assert source.end_frame == 19
    assert source.end_frame < plan.effective_events[2].start_frame


def test_manual_intent_subsumed_by_automatic_handoff_emits_no_metadata() -> None:
    observations = (
        Observation(0, "あ"),
        Observation(
            1,
            "う",
            is_bridgeable_cross_vowel_transition_candidate=True,
            previous_non_zero_event_index=0,
            next_non_zero_event_index=2,
            span_start_index=1,
            span_end_index=1,
        ),
        Observation(2, "い"),
    )
    base_input = make_input(
        (
            Point(0.5, start_sec=0.4, end_sec=0.6),
            Point(1.0, vowel="う", value=0.0, start_sec=0.9, end_sec=1.1),
            Point(1.5, vowel="い", value=1.0, start_sec=1.4, end_sec=1.6),
        ),
        observations=observations,
        duration=120,
    )
    automatic = resolve_effective_shape_plan(base_input)
    final = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, end_offset_frames=5),),
    )

    automatic_source = next(
        shape for shape in automatic.shapes if 0 in shape.real_base_event_indices
    )
    final_source = next(
        shape for shape in final.shapes if 0 in shape.real_base_event_indices
    )
    assert final_source.control_points == automatic_source.control_points
    assert final.manual_crossfades == ()
