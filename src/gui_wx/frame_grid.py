"""Pure frame-grid tick generation for the 30 fps GUI timeline."""

from __future__ import annotations

from dataclasses import dataclass
import math


FRAME_RATE = 30
_MIN_MINOR_SPACING_PX = 6.0
_MIN_MAJOR_SPACING_PX = 40.0
_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class FrameGridTick:
    frame_no: int
    x: float
    is_major: bool
    is_minor: bool
    label_allowed: bool


def _nice_step_1_2_5(minimum: float) -> int | None:
    if not math.isfinite(minimum):
        return None

    required = max(1.0, minimum)
    magnitude = 1
    while True:
        for multiplier in (1, 2, 5):
            candidate = multiplier * magnitude
            if candidate >= required:
                return candidate
        magnitude *= 10


def _first_multiple_at_or_after(value: int, step: int) -> int:
    return ((value + step - 1) // step) * step


def calculate_frame_grid_ticks(
    viewport_start_sec: float,
    viewport_end_sec: float,
    audio_duration_sec: float,
    panel_width_px: float,
    *,
    enabled: bool = True,
) -> tuple[FrameGridTick, ...]:
    """Return visible integer-frame ticks, or an empty tuple when hidden/invalid.

    Grid positions remain anchored to frame zero. The viewport itself is never
    rounded, and the complete audio range is intentionally grid-free.
    """
    if not enabled:
        return ()

    try:
        start_sec = float(viewport_start_sec)
        end_sec = float(viewport_end_sec)
        duration_sec = float(audio_duration_sec)
        width_px = float(panel_width_px)
    except (TypeError, ValueError, OverflowError):
        return ()

    if not all(math.isfinite(value) for value in (start_sec, end_sec, duration_sec, width_px)):
        return ()
    if duration_sec <= 0.0 or width_px <= 0.0 or end_sec <= start_sec:
        return ()
    if start_sec <= _EPSILON and end_sec >= duration_sec - _EPSILON:
        return ()

    visible_start_sec = max(0.0, start_sec)
    visible_end_sec = min(duration_sec, end_sec)
    if visible_end_sec < visible_start_sec:
        return ()

    span_sec = end_sec - start_sec
    pixels_per_frame = width_px / (span_sec * FRAME_RATE)
    if not math.isfinite(pixels_per_frame) or pixels_per_frame <= 0.0:
        return ()

    scaled_start = visible_start_sec * FRAME_RATE
    scaled_end = visible_end_sec * FRAME_RATE
    scaled_duration = duration_sec * FRAME_RATE
    if not all(math.isfinite(value) for value in (scaled_start, scaled_end, scaled_duration)):
        return ()

    first_frame = max(0, math.ceil(scaled_start - _EPSILON))
    last_frame = min(
        math.floor(scaled_duration + _EPSILON),
        math.floor(scaled_end + _EPSILON),
    )
    if last_frame < first_frame:
        return ()

    minor_step = _nice_step_1_2_5(_MIN_MINOR_SPACING_PX / pixels_per_frame)
    pixels_per_second = pixels_per_frame * FRAME_RATE
    if not math.isfinite(pixels_per_second) or pixels_per_second <= 0.0:
        return ()

    major_step_seconds = _nice_step_1_2_5(
        max(
            1.0,
            _MIN_MAJOR_SPACING_PX / pixels_per_second,
        )
    )
    if minor_step is None or major_step_seconds is None:
        return ()
    major_step_frames = major_step_seconds * FRAME_RATE

    first_minor = _first_multiple_at_or_after(first_frame, minor_step)
    minor_frames = set(range(first_minor, last_frame + 1, minor_step))
    first_major = _first_multiple_at_or_after(first_frame, major_step_frames)
    major_frames = set(range(first_major, last_frame + 1, major_step_frames))

    visible_minor_frames = {
        frame_no
        for frame_no in minor_frames
        if frame_no not in major_frames
        and all(
            abs(frame_no - major_frame) * pixels_per_frame >= _MIN_MINOR_SPACING_PX
            for major_frame in major_frames
        )
    }

    frame_numbers = sorted(major_frames | visible_minor_frames)
    ticks: list[FrameGridTick] = []
    for frame_no in frame_numbers:
        time_sec = frame_no / FRAME_RATE
        x = ((time_sec - start_sec) / span_sec) * width_px
        x = min(width_px, max(0.0, x))
        is_major = frame_no in major_frames
        ticks.append(
            FrameGridTick(
                frame_no=frame_no,
                x=x,
                is_major=is_major,
                is_minor=not is_major,
                label_allowed=is_major,
            )
        )
    return tuple(ticks)
