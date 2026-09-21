from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    build_base_plan_identity,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import empty_adjustment_snapshot
from src.core.pipeline import (
    PeakValueEvaluation,
    PeakValueObservation,
    VowelTimingPlan,
    _repair_resolver_same_morph_boundaries,
)
from src.core.preview_transform import build_preview_data_from_effective_shape_plan
from src.vmd_writer import VowelTimelinePoint
from src.vmd_writer.effective_shape_adapter import build_morph_frames_from_effective_shape_plan


def _b2_adjacent_long_boundary_timeline() -> tuple[VowelTimelinePoint, ...]:
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
            19 / 30,
            "あ",
            value=0.5,
            duration_sec=6 / 30,
            start_sec=18 / 30,
            end_sec=24 / 30,
            vowel_token_index=2,
        ),
        VowelTimelinePoint(
            26 / 30,
            "あ",
            value=0.3,
            duration_sec=2 / 30,
            start_sec=24 / 30,
            end_sec=26 / 30,
            vowel_token_index=3,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=2,
        ),
    )


def _b2_chained_long_boundary_timeline() -> tuple[VowelTimelinePoint, ...]:
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
            "あ",
            value=0.5,
            duration_sec=2 / 30,
            start_sec=17 / 30,
            end_sec=19 / 30,
            vowel_token_index=2,
        ),
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
        ),
    )


def test_real_pipeline_contract_reaches_preview_with_one_canonical_identity() -> None:
    point = VowelTimelinePoint(
        time_sec=1.0,
        vowel="あ",
        value=0.6,
        peak_value=0.6,
        duration_sec=0.4,
        start_sec=0.8,
        end_sec=1.2,
    )
    evaluation = PeakValueEvaluation(0.8, 1.2, 0.8, 1.2, 0.6, 0.6)
    observation = PeakValueObservation(
        event_index=0,
        vowel="あ",
        time_sec=1.0,
        initial_interval_start_sec=0.8,
        initial_interval_end_sec=1.2,
        refined_interval_start_sec=0.8,
        refined_interval_end_sec=1.2,
        peak_window_start_sec=0.8,
        peak_window_end_sec=1.2,
        local_peak=0.6,
        global_peak=0.6,
        peak_value=0.6,
        reason=None,
        fallback_reason=None,
        window_sample_count=4,
        evaluation=evaluation,
        rms_window_times_sec=(0.8, 0.9, 1.0, 1.1),
        rms_window_values=(0.1, 0.4, 0.6, 0.2),
    )
    pipeline_plan = VowelTimingPlan(
        vowels=["あ"],
        timeline=[point],
        anchors=[],
        source="integration_test",
        observations=[observation],
    )
    base_input = BaseTimingPlanInput(
        timeline=tuple(pipeline_plan.timeline),
        observations=tuple(pipeline_plan.observations or ()),
        source_duration_frames=60,
        shape_parameters=ShapeParameters(),
    )
    identity = build_base_plan_identity(base_input)
    effective_plan = resolve_effective_shape_plan(
        base_input,
        empty_adjustment_snapshot(identity),
    )
    preview = build_preview_data_from_effective_shape_plan(effective_plan)

    segment = preview.rows[0].segments[0]
    assert effective_plan.base_plan_identity == identity
    assert len(pipeline_plan.timeline) == len(effective_plan.effective_events) == 1
    assert segment.source_event_indices == (0,)
    assert segment.event_hit_regions[0].base_event_index == 0
    assert segment.event_hit_regions[0].base_peak_frame == 30
    assert segment.event_hit_regions[0].peak_value == 0.6


def test_preview_adapter_rejects_duplicate_shape_provenance() -> None:
    point = VowelTimelinePoint(
        time_sec=1.0,
        vowel="あ",
        value=0.5,
        start_sec=0.8,
        end_sec=1.2,
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(point,),
            observations=None,
            source_duration_frames=60,
        )
    )
    malformed = replace(plan, shapes=(plan.shapes[0], plan.shapes[0]))
    with pytest.raises(ValueError, match="more than one shape"):
        build_preview_data_from_effective_shape_plan(malformed)


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_ms28_b2_pipeline_same_frame_handoff_preserves_start(mode: str) -> None:
    timeline = _b2_adjacent_long_boundary_timeline()
    repaired = _repair_resolver_same_morph_boundaries(timeline)

    assert round(repaired[2].start_sec * 30) == 18
    assert round(repaired[2].time_sec * 30) == 19
    assert repaired[2].end_sec == timeline[2].end_sec

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            tuple(repaired),
            None,
            30,
            ShapeParameters(long_vowel_mode=mode),
        )
    )
    preview = build_preview_data_from_effective_shape_plan(plan)
    writer_points = sorted(
        build_morph_frames_from_effective_shape_plan(
            plan,
            apply_final_normalization=False,
        )
    )
    preview_points = sorted(
        (point.frame_no, segment.vowel, point.value)
        for row in preview.rows
        for segment in row.segments
        for point in segment.control_points
    )

    assert preview_points == writer_points
    assert (18, "あ", 0.0) in writer_points
    assert (19, "あ", 0.5) in writer_points


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_ms28_b2_pipeline_chained_long_source_uses_compact_handoff(mode: str) -> None:
    timeline = _b2_chained_long_boundary_timeline()
    repaired = _repair_resolver_same_morph_boundaries(timeline)

    assert round(repaired[2].start_sec * 30) == 18
    assert round(repaired[2].time_sec * 30) == 19
    assert round(repaired[2].end_sec * 30) == 19
    assert repaired[3] == timeline[3]

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            tuple(repaired),
            None,
            30,
            ShapeParameters(long_vowel_mode=mode),
        )
    )
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
    assert (18, "あ", 0.0) in writer_points
    assert (19, "あ", 0.5) in writer_points
    assert plan.effective_events[3].long_vowel_source_token_index == 2
