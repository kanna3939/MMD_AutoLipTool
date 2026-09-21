from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from src.vmd_writer import SUPPORTED_MORPHS, VMD_FPS, VowelTimelinePoint


@dataclass(frozen=True)
class PlaybackInfoContext:
    is_playing: bool
    position_sec: float
    frame_no: int
    current_vowel: str | None


def build_playback_info_context(
    *,
    is_playing: bool,
    position_sec: object,
    timeline: Iterable[object] | None = None,
    analysis_result_valid: bool = False,
    analysis_pending_rebuild: bool = False,
) -> PlaybackInfoContext:
    normalized_position, position_is_valid = _normalize_position(position_sec)
    playing = bool(is_playing)
    if not playing:
        normalized_position = 0.0

    frame_no = max(0, int(round(normalized_position * VMD_FPS)))
    current_vowel = None
    if (
        playing
        and position_is_valid
        and analysis_result_valid
        and not analysis_pending_rebuild
    ):
        current_vowel = _resolve_current_vowel(
            normalized_position,
            frame_no,
            timeline,
        )

    return PlaybackInfoContext(
        is_playing=playing,
        position_sec=normalized_position,
        frame_no=frame_no,
        current_vowel=current_vowel,
    )


def format_playback_info_context(context: PlaybackInfoContext) -> str:
    vowel_text = context.current_vowel or "(なし)"
    return "\n".join(
        (
            "[再生]",
            f"再生位置: {context.position_sec:.2f} 秒",
            f"現在フレーム: {context.frame_no}",
            f"現在母音: {vowel_text}",
        )
    )


def _normalize_position(value: object) -> tuple[float, bool]:
    try:
        position = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0.0, False
    if not math.isfinite(position):
        return 0.0, False
    return max(0.0, position), True


def _resolve_current_vowel(
    position_sec: float,
    frame_no: int,
    timeline: Iterable[object] | None,
) -> str | None:
    if timeline is None:
        return None
    try:
        points = enumerate(timeline)
    except TypeError:
        return None

    candidates: list[tuple[float, float, int, str]] = []
    try:
        for index, point in points:
            candidate = _active_candidate(point, position_sec, frame_no, index)
            if candidate is not None:
                candidates.append(candidate)
    except TypeError:
        return None

    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], -item[1], -item[2]))[3]


def _active_candidate(
    point: object,
    position_sec: float,
    frame_no: int,
    index: int,
) -> tuple[float, float, int, str] | None:
    if not isinstance(point, VowelTimelinePoint):
        return None
    if point.vowel not in SUPPORTED_MORPHS:
        return None

    try:
        time_sec = float(point.time_sec)
        start_sec = float(point.start_sec)
        end_sec = float(point.end_sec)
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(value) for value in (time_sec, start_sec, end_sec)):
        return None
    if end_sec < start_sec or time_sec < start_sec or time_sec > end_sec:
        return None

    if start_sec == end_sec:
        is_active = frame_no == int(round(time_sec * VMD_FPS))
    else:
        is_active = start_sec <= position_sec < end_sec
    if not is_active:
        return None

    return (abs(position_sec - time_sec), time_sec, index, point.vowel)


__all__ = [
    "PlaybackInfoContext",
    "build_playback_info_context",
    "format_playback_info_context",
]
