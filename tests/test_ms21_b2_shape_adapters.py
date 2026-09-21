from __future__ import annotations

from dataclasses import dataclass
import subprocess
import sys

from src.core.effective_shape_plan import (
    MORPH_FRAME_OPEN_EPSILON,
    SUPPORTED_MORPHS,
    VMD_FPS,
    BaseTimingPlanInput,
    ShapeParameters,
    resolve_effective_shape_plan,
)
from src.core.preview_transform import build_preview_data_from_effective_shape_plan
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from src.vmd_writer.writer import (
    MORPH_FRAME_OPEN_EPSILON as WRITER_EPSILON,
    SUPPORTED_MORPHS as WRITER_MORPHS,
    VMD_FPS as WRITER_FPS,
    VowelTimelinePoint,
    _build_interval_morph_frames,
    _build_morph_frames_from_effective_shape_plan,
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


def make_plan():
    return resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(Point(1.0, start_sec=0.8, end_sec=1.2),),
            observations=None,
            source_duration_frames=60,
        )
    )


def test_preview_and_writer_consume_same_control_points() -> None:
    plan = make_plan()
    preview = build_preview_data_from_effective_shape_plan(plan)
    segment = preview.rows[0].segments[0]
    writer_frames = build_morph_frames_from_effective_shape_plan(
        plan, apply_final_normalization=False
    )
    assert tuple(point.frame_no for point in segment.control_points) == tuple(
        frame_no for frame_no, _, _ in writer_frames
    )
    assert segment.source_event_indices == (0,)
    assert segment.source_event_index == 0


def test_writer_compatibility_wrapper_uses_structural_plan() -> None:
    plan = make_plan()
    direct = build_morph_frames_from_effective_shape_plan(
        plan, apply_final_normalization=False
    )
    wrapped = _build_morph_frames_from_effective_shape_plan(
        plan, apply_final_normalization=False
    )
    assert wrapped == direct


def test_base_only_single_shape_matches_legacy_frames_with_tail() -> None:
    point = VowelTimelinePoint(
        1.0,
        "あ",
        value=0.5,
        duration_sec=0.4,
        start_sec=0.8,
        end_sec=1.2,
    )
    legacy = tuple(
        _build_interval_morph_frames(
            [point], closing_hold_frames=3, closing_softness_frames=2
        )
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(point,),
            observations=None,
            source_duration_frames=60,
            shape_parameters=ShapeParameters(3, 2),
        )
    )
    assert (
        build_morph_frames_from_effective_shape_plan(
            plan, apply_final_normalization=False
        )
        == legacy
    )


def test_base_only_multi_source_shape_matches_legacy_frames() -> None:
    points = (
        VowelTimelinePoint(1.0, "あ", value=0.5, start_sec=0.9, end_sec=1.1),
        VowelTimelinePoint(1.2, "あ", value=0.4, start_sec=1.1, end_sec=1.3),
    )
    legacy = tuple(_build_interval_morph_frames(list(points)))
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=points,
            observations=None,
            source_duration_frames=60,
        )
    )
    assert (
        build_morph_frames_from_effective_shape_plan(
            plan, apply_final_normalization=False
        )
        == legacy
    )


def test_shared_compatibility_constants_do_not_drift() -> None:
    assert VMD_FPS == WRITER_FPS
    assert SUPPORTED_MORPHS == WRITER_MORPHS
    assert MORPH_FRAME_OPEN_EPSILON == WRITER_EPSILON


def test_fresh_process_import_orders_and_mixed_namespace() -> None:
    commands = (
        "import src.vmd_writer; import src.vmd_writer.effective_shape_adapter; import src.core.effective_shape_plan",
        "import src.core.effective_shape_plan; import src.vmd_writer.effective_shape_adapter; import src.vmd_writer",
        "import vmd_writer.writer as tw; import src.vmd_writer as sv; assert tw.VowelTimelinePoint is not sv.VowelTimelinePoint",
    )
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-c", command],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
