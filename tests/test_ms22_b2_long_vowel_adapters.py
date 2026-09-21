from __future__ import annotations

from src.core.effective_shape_plan import BaseTimingPlanInput, ShapeParameters, resolve_effective_shape_plan
from src.core.preview_transform import build_preview_data_from_effective_shape_plan
from src.vmd_writer import VowelTimelinePoint
from src.vmd_writer.effective_shape_adapter import build_morph_frames_from_effective_shape_plan


def _plan(mode: str):
    points = (
        VowelTimelinePoint(0.2, "あ", value=0.5, duration_sec=0.2, start_sec=0.1, end_sec=0.3, vowel_token_index=0),
        VowelTimelinePoint(0.5, "あ", value=0.4, duration_sec=0.2, start_sec=0.4, end_sec=0.6, vowel_token_index=1, is_long_vowel_continuation=True, long_vowel_source_token_index=0),
    )
    return resolve_effective_shape_plan(BaseTimingPlanInput(points, None, 30, ShapeParameters(long_vowel_mode=mode)))


def test_preview_and_writer_consume_same_decay_control_points() -> None:
    plan = _plan("decay")
    preview = build_preview_data_from_effective_shape_plan(plan)
    preview_points = [
        (point.frame_no, point.value)
        for segment in preview.rows[0].segments
        for point in segment.control_points
    ]
    writer_points = [(frame_no, value) for frame_no, vowel, value in build_morph_frames_from_effective_shape_plan(plan, apply_final_normalization=False) if vowel == "あ"]
    assert preview_points == writer_points
    assert writer_points[-1] == (18, 0.0)


def test_hold_and_decay_shapes_keep_non_none_tail_metadata() -> None:
    for mode in ("hold", "decay"):
        shape = _plan(mode).shapes[0]
        assert shape.resolved_tail is not None
