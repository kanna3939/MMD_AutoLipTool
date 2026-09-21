from __future__ import annotations

from dataclasses import dataclass

import pytest

from gui_wx.selected_event_editor import (
    SelectedEventEditRequest,
    build_selected_event_editor_state,
    merge_selected_event_edit,
)
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    apply_adjustment_update,
    build_base_plan_identity,
    resolve_effective_shape_plan,
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


def make_input(
    points: tuple[Point, ...],
    *,
    duration: int = 180,
    hold: int = 0,
    softness: int = 0,
) -> BaseTimingPlanInput:
    return BaseTimingPlanInput(
        timeline=points,
        observations=None,
        source_duration_frames=duration,
        shape_parameters=ShapeParameters(hold, softness),
    )


def test_plan_exposes_base_events_and_resolved_tail_metadata() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.1),
            Point(1.2, start_sec=1.1, end_sec=1.3),
            Point(1.7, vowel="い", start_sec=1.6, end_sec=1.8),
        ),
        hold=4,
        softness=3,
    )
    plan = resolve_effective_shape_plan(base_input)

    assert tuple(event.base_event_index for event in plan.base_events) == (0, 1, 2)
    grouped = next(shape for shape in plan.shapes if shape.real_base_event_indices == (0, 1))
    assert grouped.resolved_tail is not None
    assert grouped.resolved_tail.tail_base_event_index == 1
    assert grouped.resolved_tail.requested_hold_frames == 4
    assert grouped.resolved_tail.requested_softness_frames == 3
    last_event = plan.effective_events[1]
    next_event = plan.effective_events[2]
    assert grouped.resolved_tail.available_extension_frames == max(
        0,
        (next_event.start_frame - 1) - last_event.end_frame,
    )
    assert grouped.resolved_tail.has_slope_midpoint is True


def test_editor_state_distinguishes_base_adjustment_and_effective_values() -> None:
    base_input = make_input(
        (Point(1.0, start_sec=0.8, end_sec=1.2, value=0.5),),
        duration=90,
        hold=2,
        softness=3,
    )
    plan = resolve_effective_shape_plan(
        base_input,
        (
            EventAdjustment(
                0,
                peak_value=0.8,
                start_offset_frames=-2,
                end_offset_frames=3,
                hold_frames=4,
                softness_frames=5,
                slope_ratio=0.5,
            ),
        ),
    )
    state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=7,
        source_duration_frames=base_input.source_duration_frames,
    )

    assert state.base_peak_value == 0.5
    assert state.requested_peak_value == 0.8
    assert state.effective_peak_value == 0.8
    assert state.requested_start_offset_frames == -2
    assert state.effective_start_frame == state.base_start_frame - 2
    assert state.requested_hold_frames == 4
    assert state.effective_hold_frames == 4
    assert state.slope_enabled is True
    assert state.reset_enabled is True
    assert state.editor_revision == 7


def test_middle_event_disables_tail_and_identity_mismatch_fails_closed() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.1),
            Point(1.2, start_sec=1.1, end_sec=1.3),
        ),
        softness=2,
    )
    plan = resolve_effective_shape_plan(base_input)
    state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=1,
        source_duration_frames=base_input.source_duration_frames,
    )
    assert state.is_group_tail is False
    assert state.slope_enabled is False
    assert state.hold_is_limited is False
    assert state.softness_is_limited is False
    assert state.effect_notice_header == ""
    assert state.effect_notice_lines == ()
    assert state.slope_helper_text == ""

    with pytest.raises(AdjustmentContractError, match="identity"):
        build_selected_event_editor_state(
            plan,
            0,
            expected_base_identity_digest="stale",
            editor_revision=1,
            source_duration_frames=base_input.source_duration_frames,
        )


def test_merge_changes_one_field_and_preserves_other_fields() -> None:
    base_input = make_input((Point(1.0),), softness=2)
    identity = build_base_plan_identity(base_input)
    snapshot = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, peak_value=0.7, hold_frames=3),),
    ).canonical_adjustment_snapshot
    request = SelectedEventEditRequest(
        base_event_index=0,
        base_identity_digest=identity.digest,
        editor_revision=2,
        field="softness_frames",
        value=4,
    )

    merged = merge_selected_event_edit(snapshot, request)

    assert merged.peak_value == 0.7
    assert merged.hold_frames == 3
    assert merged.softness_frames == 4


def test_update_removes_slope_when_effective_midpoint_disappears() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.0),
            Point(1.1, vowel="い", start_sec=1.1, end_sec=1.2),
        ),
        duration=90,
        softness=3,
    )
    current = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, slope_ratio=0.5),),
    ).canonical_adjustment_snapshot

    result = apply_adjustment_update(
        base_input,
        current,
        EventAdjustment(1, start_offset_frames=-2),
    )

    assert result.removed_tail_override_event_indices == ()
    assert result.removed_slope_override_event_indices == (0,)
    assert all(
        item.slope_ratio is None
        for item in result.canonical_snapshot.adjustments
    )


def test_direct_resolver_rejects_slope_without_actual_midpoint() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.0),
            Point(1.1, vowel="い", start_sec=1.1, end_sec=1.2),
        ),
        softness=3,
    )
    with pytest.raises(AdjustmentContractError, match="midpoint"):
        resolve_effective_shape_plan(
            base_input,
            (
                EventAdjustment(0, slope_ratio=0.5),
                EventAdjustment(1, start_offset_frames=-2),
            ),
        )


def test_empty_snapshot_editor_is_reset_disabled() -> None:
    base_input = make_input((Point(1.0),), softness=2)
    identity = build_base_plan_identity(base_input)
    plan = resolve_effective_shape_plan(
        base_input,
        empty_adjustment_snapshot(identity),
    )
    state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=identity.digest,
        editor_revision=0,
        source_duration_frames=base_input.source_duration_frames,
    )
    assert state.reset_enabled is False


def test_global_tail_settings_explain_limited_effect_without_internal_terms() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.0),
            Point(1.1, vowel="い", start_sec=1.1, end_sec=1.2),
        ),
        hold=5,
        softness=5,
    )
    plan = resolve_effective_shape_plan(base_input)
    state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=0,
        source_duration_frames=base_input.source_duration_frames,
    )

    assert state.hold_overridden is False
    assert state.softness_overridden is False
    assert state.available_extension_frames == 2
    assert state.effective_hold_frames == 2
    assert state.effective_softness_frames == 0
    assert state.hold_is_limited is True
    assert state.softness_is_limited is True
    assert state.effect_notice_header == (
        "次の口形までの間隔が短いため、設定値を一部だけ反映しています。"
    )
    assert state.effect_notice_lines == (
        "開口保持: 設定 5 → 反映 2 フレーム",
        "閉口スムーズ: 設定 5 → 反映 0 フレーム",
        "閉口スムーズが反映されないため、"
        "傾斜比は現在のプレビューには反映されません。",
    )
    assert len(state.effect_notice_lines) == len(set(state.effect_notice_lines))
    assert state.slope_helper_text == ""
    notice_text = "\n".join(
        (state.effect_notice_header, *state.effect_notice_lines)
    )
    for internal_term in (
        "tail",
        "clamp",
        "midpoint",
        "canonical",
        "snapshot",
        "resolver",
        "補正値",
    ):
        assert internal_term not in notice_text


def test_event_override_uses_same_limited_effect_notice_contract() -> None:
    base_input = make_input(
        (
            Point(1.0, start_sec=0.9, end_sec=1.0),
            Point(1.1, vowel="い", start_sec=1.1, end_sec=1.2),
        ),
    )
    plan = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(0, hold_frames=5, softness_frames=5),),
    )
    state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=0,
        source_duration_frames=base_input.source_duration_frames,
    )

    assert state.hold_overridden is True
    assert state.softness_overridden is True
    assert state.effect_notice_header
    assert state.effect_notice_lines[:2] == (
        "開口保持: 設定 5 → 反映 3 フレーム",
        "閉口スムーズ: 設定 5 → 反映 0 フレーム",
    )


def test_zero_softness_uses_normal_slope_helper_without_attention_notice() -> None:
    base_input = make_input((Point(1.0),), hold=2, softness=0)
    plan = resolve_effective_shape_plan(base_input)
    state = build_selected_event_editor_state(
        plan,
        0,
        expected_base_identity_digest=plan.base_plan_identity.digest,
        editor_revision=0,
        source_duration_frames=base_input.source_duration_frames,
    )

    assert state.available_extension_frames is None
    assert state.effect_notice_header == ""
    assert state.effect_notice_lines == ()
    assert state.slope_helper_text == (
        "傾斜比を調整するには、閉口スムーズを1フレーム以上にしてください。"
    )
