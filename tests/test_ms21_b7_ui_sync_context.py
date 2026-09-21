from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from gui_wx.ui_sync_context import build_ui_sync_context
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    resolve_effective_shape_plan,
)


@dataclass(frozen=True)
class Point:
    time_sec: float
    vowel: str = "あ"
    value: float = 0.5
    duration_sec: float = 0.2


def make_base_input():
    return BaseTimingPlanInput(
        timeline=(Point(0.5),),
        observations=None,
        source_duration_frames=90,
        shape_parameters=ShapeParameters(2, 1),
    )


def test_context_resolves_once_and_exposes_canonical_snapshot():
    base_input = make_base_input()
    with patch(
        "gui_wx.ui_sync_context.resolve_effective_shape_plan",
        wraps=resolve_effective_shape_plan,
    ) as resolver:
        context = build_ui_sync_context(base_input, None)

    assert resolver.call_count == 1
    assert context.base_plan_identity == context.effective_plan.base_plan_identity
    assert (
        context.effective_plan.canonical_adjustment_snapshot.base_plan_identity
        == context.base_plan_identity
    )


def test_matching_hint_skips_resolver_and_stale_hint_is_rejected():
    base_input = make_base_input()
    hint = resolve_effective_shape_plan(base_input)
    snapshot = hint.canonical_adjustment_snapshot
    with patch(
        "gui_wx.ui_sync_context.resolve_effective_shape_plan"
    ) as resolver:
        context = build_ui_sync_context(
            base_input,
            snapshot,
            effective_plan_hint=hint,
        )
    resolver.assert_not_called()
    assert context.effective_plan is hint

    other_input = BaseTimingPlanInput(
        timeline=(Point(0.7),),
        observations=None,
        source_duration_frames=90,
        shape_parameters=ShapeParameters(2, 1),
    )
    with pytest.raises(ValueError, match="base identity mismatch"):
        build_ui_sync_context(
            other_input,
            snapshot,
            effective_plan_hint=hint,
        )
