from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Protocol, Sequence

from gui.i18n_strings import INTERNAL_VOWEL_ORDER

PREVIEW_ROW_VOWELS: tuple[str, str, str, str, str] = INTERNAL_VOWEL_ORDER


class TimelinePointLike(Protocol):
    vowel: str
    time_sec: float
    duration_sec: float
    start_sec: float | None
    end_sec: float | None
    peak_value: float | None
    value: float


@dataclass(frozen=True)
class PreviewSegment:
    start_sec: float
    end_sec: float
    duration_sec: float
    intensity: float
    vowel: str


@dataclass(frozen=True)
class PreviewRow:
    vowel: str
    segments: list[PreviewSegment]


@dataclass(frozen=True)
class PreviewData:
    rows: list[PreviewRow]


def empty_preview_data() -> PreviewData:
    return PreviewData(
        rows=[PreviewRow(vowel=vowel, segments=[]) for vowel in PREVIEW_ROW_VOWELS]
    )


def build_preview_data(timeline: Sequence[TimelinePointLike] | None) -> PreviewData:
    if not timeline:
        return empty_preview_data()

    rows = {row.vowel: row for row in empty_preview_data().rows}

    for point in timeline:
        vowel = str(getattr(point, "vowel", ""))
        row = rows.get(vowel)
        if row is None:
            continue

        start_sec, end_sec = _resolve_segment_bounds(point)
        segment = PreviewSegment(
            start_sec=start_sec,
            end_sec=end_sec,
            duration_sec=end_sec - start_sec,
            intensity=_resolve_intensity(point),
            vowel=vowel,
        )
        row.segments.append(segment)

    for row in rows.values():
        row.segments.sort(key=lambda segment: (segment.start_sec, segment.end_sec))

    return PreviewData(rows=[rows[vowel] for vowel in PREVIEW_ROW_VOWELS])


def _resolve_segment_bounds(point: TimelinePointLike) -> tuple[float, float]:
    start_raw = _to_finite_float(getattr(point, "start_sec", None))
    end_raw = _to_finite_float(getattr(point, "end_sec", None))

    if start_raw is None and end_raw is None:
        time_sec = _to_finite_float(getattr(point, "time_sec", None)) or 0.0
        duration_sec = _to_finite_float(getattr(point, "duration_sec", None)) or 0.0
        half = max(duration_sec, 0.0) * 0.5
        start_raw = time_sec - half
        end_raw = time_sec + half
    elif start_raw is None:
        end_raw = end_raw or 0.0
        duration_sec = _to_finite_float(getattr(point, "duration_sec", None)) or 0.0
        start_raw = end_raw - max(duration_sec, 0.0)
    elif end_raw is None:
        duration_sec = _to_finite_float(getattr(point, "duration_sec", None)) or 0.0
        end_raw = start_raw + max(duration_sec, 0.0)

    start_sec = max(float(start_raw), 0.0)
    end_sec = max(float(end_raw), start_sec)
    return start_sec, end_sec


def _resolve_intensity(point: TimelinePointLike) -> float:
    resolved = _to_finite_float(getattr(point, "peak_value", None))
    if resolved is None:
        resolved = _to_finite_float(getattr(point, "value", None))
    if resolved is None:
        resolved = 0.0
    return min(max(resolved, 0.0), 1.0)


def _to_finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(resolved):
        return None
    return resolved


__all__ = [
    "PREVIEW_ROW_VOWELS",
    "PreviewSegment",
    "PreviewRow",
    "PreviewData",
    "TimelinePointLike",
    "empty_preview_data",
    "build_preview_data",
]
