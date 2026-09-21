from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
import math

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    build_base_plan_identity,
)
from src.core.event_adjustment import (
    AdjustmentContractError,
    EventAdjustment,
    canonicalize_adjustment_snapshot,
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


def make_input(*points: Point) -> BaseTimingPlanInput:
    return BaseTimingPlanInput(
        timeline=points,
        observations=None,
        source_duration_frames=120,
        shape_parameters=ShapeParameters(closing_hold_frames=2, closing_softness_frames=3),
    )


def test_base_identity_is_stable_and_copies_payload() -> None:
    left = build_base_plan_identity(make_input(Point(1.0)))
    right = build_base_plan_identity(make_input(Point(1.0)))
    assert left == right
    assert left.digest == right.digest
    assert left.canonical_payload == right.canonical_payload


def test_base_identity_uses_float_hex_and_observation_state() -> None:
    base_input = make_input(Point(0.1))
    identity = build_base_plan_identity(base_input)
    assert float(0.1).hex() in str(identity.canonical_payload)
    assert "none" in identity.canonical_payload


def test_event_adjustment_is_frozen() -> None:
    adjustment = EventAdjustment(base_event_index=0, peak_value=0.8)
    with pytest.raises(FrozenInstanceError):
        adjustment.peak_value = 0.2  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"base_event_index": True}, "base_event_index"),
        ({"base_event_index": -1}, "base_event_index"),
        ({"base_event_index": 0, "start_offset_frames": True}, "start_offset_frames"),
        ({"base_event_index": 0, "hold_frames": 101}, "hold_frames"),
        ({"base_event_index": 0, "softness_frames": -1}, "softness_frames"),
        ({"base_event_index": 0, "slope_ratio": 1.01}, "slope_ratio"),
        ({"base_event_index": 0, "peak_value": math.inf}, "peak_value"),
    ],
)
def test_event_adjustment_rejects_invalid_fields(kwargs: dict[str, object], field: str) -> None:
    with pytest.raises(AdjustmentContractError, match=field):
        EventAdjustment(**kwargs)  # type: ignore[arg-type]


def test_canonical_snapshot_orders_and_preserves_explicit_tail_intent() -> None:
    base_input = make_input(Point(1.0), Point(2.0, vowel="い"))
    identity = build_base_plan_identity(base_input)
    snapshot = canonicalize_adjustment_snapshot(
        identity,
        [
            EventAdjustment(base_event_index=1, peak_value=0.8),
            EventAdjustment(
                base_event_index=0,
                peak_value=0.5,
                hold_frames=2,
                softness_frames=3,
                slope_ratio=0.7,
            ),
        ],
        base_peak_values=(0.5, 0.5),
        closing_hold_frames=2,
        closing_softness_frames=3,
    )
    assert tuple(item.base_event_index for item in snapshot.adjustments) == (0, 1)
    assert snapshot.adjustments[0].peak_value is None
    assert snapshot.adjustments[0].hold_frames == 2
    assert snapshot.adjustments[0].softness_frames == 3
    assert snapshot.adjustments[0].slope_ratio is None
    assert snapshot.adjustments[1].peak_value == 0.8


def test_canonical_snapshot_copies_requested_collection() -> None:
    base_input = make_input(Point(1.0))
    identity = build_base_plan_identity(base_input)
    requested = [EventAdjustment(base_event_index=0, peak_value=0.8)]
    snapshot = canonicalize_adjustment_snapshot(
        identity,
        requested,
        base_peak_values=(0.5,),
        closing_hold_frames=2,
        closing_softness_frames=3,
    )
    requested.clear()
    assert len(snapshot.adjustments) == 1


def test_canonical_snapshot_rejects_duplicate_and_stale_indices() -> None:
    identity = build_base_plan_identity(make_input(Point(1.0)))
    with pytest.raises(AdjustmentContractError, match="duplicate"):
        canonicalize_adjustment_snapshot(
            identity,
            [EventAdjustment(0, peak_value=0.6), EventAdjustment(0, peak_value=0.7)],
            base_peak_values=(0.5,),
            closing_hold_frames=0,
            closing_softness_frames=0,
        )
    with pytest.raises(AdjustmentContractError, match="stale"):
        canonicalize_adjustment_snapshot(
            identity,
            [EventAdjustment(1, peak_value=0.6)],
            base_peak_values=(0.5,),
            closing_hold_frames=0,
            closing_softness_frames=0,
        )
