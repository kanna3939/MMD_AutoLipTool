from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


PREVIEW_ROW_VOWELS = ("あ", "い", "う", "え", "お")
VMD_FPS = 30


def _require_int(value: object, field_name: str, *, non_negative: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if non_negative and value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _require_finite_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be a finite number")
    return normalized


@dataclass(frozen=True)
class PreviewEventHitRegion:
    base_event_index: int
    vowel: str
    start_frame: int
    base_peak_frame: int
    end_frame: int
    peak_value: float

    def __post_init__(self) -> None:
        _require_int(self.base_event_index, "base_event_index", non_negative=True)
        if self.vowel not in PREVIEW_ROW_VOWELS:
            raise ValueError(f"unsupported vowel: {self.vowel}")
        start_frame = _require_int(self.start_frame, "start_frame", non_negative=True)
        peak_frame = _require_int(
            self.base_peak_frame, "base_peak_frame", non_negative=True
        )
        end_frame = _require_int(self.end_frame, "end_frame", non_negative=True)
        if not start_frame <= peak_frame <= end_frame:
            raise ValueError("event frames must satisfy start <= peak <= end")
        peak_value = _require_finite_number(self.peak_value, "peak_value")
        if peak_value < 0.0:
            raise ValueError("peak_value must be non-negative")


@dataclass(frozen=True)
class PreviewHitTestInput:
    x: float
    y: float
    width: float
    height: float
    viewport_start_sec: float
    viewport_end_sec: float
    event_hit_regions: tuple[PreviewEventHitRegion, ...]

    def __post_init__(self) -> None:
        regions = tuple(self.event_hit_regions)
        if any(not isinstance(region, PreviewEventHitRegion) for region in regions):
            raise ValueError("event_hit_regions must contain PreviewEventHitRegion values")
        object.__setattr__(self, "event_hit_regions", regions)


@dataclass(frozen=True)
class PreviewSelectionRequest:
    base_event_index: int
    base_plan_identity_digest: str
    render_revision: int

    def __post_init__(self) -> None:
        _require_int(self.base_event_index, "base_event_index", non_negative=True)
        if (
            not isinstance(self.base_plan_identity_digest, str)
            or not self.base_plan_identity_digest
        ):
            raise ValueError("base_plan_identity_digest must be a non-empty string")
        _require_int(self.render_revision, "render_revision", non_negative=True)


def hit_test_preview_event(value: PreviewHitTestInput) -> int | None:
    """Return the canonical base event at a Preview position, or ``None``."""
    if not isinstance(value, PreviewHitTestInput):
        return None
    try:
        x = _require_finite_number(value.x, "x")
        y = _require_finite_number(value.y, "y")
        width = _require_finite_number(value.width, "width")
        height = _require_finite_number(value.height, "height")
        viewport_start = _require_finite_number(
            value.viewport_start_sec, "viewport_start_sec"
        )
        viewport_end = _require_finite_number(
            value.viewport_end_sec, "viewport_end_sec"
        )
    except ValueError:
        return None

    if (
        width <= 0.0
        or height <= 0.0
        or viewport_start < 0.0
        or viewport_end <= viewport_start
        or not 0.0 <= x < width
        or not 0.0 <= y < height
    ):
        return None

    lane_index = min(int(y * len(PREVIEW_ROW_VOWELS) / height), 4)
    vowel = PREVIEW_ROW_VOWELS[lane_index]
    cursor_sec = viewport_start + (x / width) * (viewport_end - viewport_start)
    cursor_frame = int(round(cursor_sec * VMD_FPS))
    candidates = (
        region
        for region in value.event_hit_regions
        if region.vowel == vowel
        and region.start_frame <= cursor_frame <= region.end_frame
    )
    selected = min(
        candidates,
        key=lambda region: (
            abs(cursor_frame - region.base_peak_frame),
            region.base_event_index,
        ),
        default=None,
    )
    return None if selected is None else selected.base_event_index


def collect_preview_hit_regions(
    rows: Sequence[object],
) -> tuple[PreviewEventHitRegion, ...]:
    """Flatten immutable hit metadata without depending on wxPython."""
    regions: list[PreviewEventHitRegion] = []
    for row in rows:
        for segment in tuple(getattr(row, "segments", ())):
            regions.extend(tuple(getattr(segment, "event_hit_regions", ())))
    return tuple(regions)


__all__ = [
    "PREVIEW_ROW_VOWELS",
    "PreviewEventHitRegion",
    "PreviewHitTestInput",
    "PreviewSelectionRequest",
    "collect_preview_hit_regions",
    "hit_test_preview_event",
]
