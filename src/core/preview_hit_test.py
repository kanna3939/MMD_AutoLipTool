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
    group_event_indices: tuple[int, ...] = ()
    shape_internal_source_tokens: tuple[int, ...] = ()
    long_vowel_source_event_index: int | None = None
    long_vowel_role: str | None = None
    long_vowel_mode: str | None = None

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
        group_indices = tuple(self.group_event_indices) or (self.base_event_index,)
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in group_indices
        ) or len(group_indices) != len(set(group_indices)) or self.base_event_index not in group_indices:
            raise ValueError("group_event_indices must include this base event")
        object.__setattr__(self, "group_event_indices", group_indices)
        tokens = tuple(self.shape_internal_source_tokens)
        if any(
            isinstance(item, bool) or not isinstance(item, int)
            for item in tokens
        ):
            raise ValueError("shape_internal_source_tokens must be integers")
        object.__setattr__(self, "shape_internal_source_tokens", tokens)
        if self.long_vowel_source_event_index is not None:
            _require_int(
                self.long_vowel_source_event_index,
                "long_vowel_source_event_index",
                non_negative=True,
            )
        if self.long_vowel_role not in {
            None,
            "source",
            "continuation",
            "terminal",
            "continuation_terminal",
        }:
            raise ValueError("long_vowel_role is unsupported")
        if self.long_vowel_mode not in {None, "hold", "decay"}:
            raise ValueError("long_vowel_mode is unsupported")
        if (self.long_vowel_role is None) != (
            self.long_vowel_source_event_index is None or self.long_vowel_mode is None
        ):
            raise ValueError("long-vowel selection metadata is incomplete")


@dataclass(frozen=True)
class PreviewCurveHitRegion:
    vowel: str
    control_points: tuple[tuple[int, float], ...]
    point_source_event_indices: tuple[tuple[int, ...], ...] = ()
    point_kinds: tuple[str, ...] = ()
    requires_source_ownership: bool = False

    def __post_init__(self) -> None:
        if self.vowel not in PREVIEW_ROW_VOWELS:
            raise ValueError(f"unsupported vowel: {self.vowel}")
        if not isinstance(self.requires_source_ownership, bool):
            raise ValueError("requires_source_ownership must be bool")
        points: list[tuple[int, float]] = []
        previous_frame: int | None = None
        for point in tuple(self.control_points):
            if not isinstance(point, (tuple, list)) or len(point) != 2:
                raise ValueError("curve control points must be frame/value pairs")
            frame_no = _require_int(point[0], "curve frame", non_negative=True)
            value = _require_finite_number(point[1], "curve value")
            if previous_frame is not None and frame_no < previous_frame:
                raise ValueError("curve control points must be frame ordered")
            points.append((frame_no, value))
            previous_frame = frame_no
        if not points:
            raise ValueError("curve control points must not be empty")
        object.__setattr__(self, "control_points", tuple(points))
        point_sources = tuple(self.point_source_event_indices)
        if point_sources and len(point_sources) != len(points):
            raise ValueError("curve point source metadata must match control points")
        if not point_sources:
            point_sources = tuple(() for _ in points)
        normalized_sources: list[tuple[int, ...]] = []
        for indices in point_sources:
            normalized = tuple(indices)
            if any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                for index in normalized
            ):
                raise ValueError("curve point source indices must be non-negative ints")
            if normalized != tuple(sorted(set(normalized))):
                raise ValueError("curve point source indices must be unique and sorted")
            normalized_sources.append(normalized)
        object.__setattr__(
            self, "point_source_event_indices", tuple(normalized_sources)
        )
        point_kinds = tuple(self.point_kinds)
        if point_kinds and len(point_kinds) != len(points):
            raise ValueError("curve point kinds must match control points")
        if not point_kinds:
            point_kinds = tuple("control" for _ in points)
        if any(type(point_kind) is not str or not point_kind for point_kind in point_kinds):
            raise ValueError("curve point kinds must be non-empty text")
        object.__setattr__(self, "point_kinds", point_kinds)

    def value_at(self, frame_no: float) -> float | None:
        points = self.control_points
        if frame_no < points[0][0] or frame_no > points[-1][0]:
            return None
        exact_values = tuple(
            value for point_frame, value in points if point_frame == frame_no
        )
        if exact_values:
            return max(exact_values)
        for (left_frame, left_value), (right_frame, right_value) in zip(
            points, points[1:]
        ):
            if left_frame < frame_no < right_frame:
                ratio = (frame_no - left_frame) / (right_frame - left_frame)
                return left_value + (right_value - left_value) * ratio
        return None

    def has_positive_value_at(self, frame_no: float) -> bool:
        value = self.value_at(frame_no)
        return value is not None and value > 0.0

    def source_event_indices_at(self, frame_no: float) -> tuple[int, ...]:
        indices: set[int] = set()
        for point_index, (point_frame, _) in enumerate(self.control_points):
            if point_frame == frame_no:
                indices.update(self.point_source_event_indices[point_index])
        if indices:
            return tuple(sorted(indices))
        for point_index, ((left_frame, left_value), (right_frame, right_value)) in enumerate(
            zip(self.control_points, self.control_points[1:])
        ):
            if left_frame < frame_no < right_frame:
                left_indices = set(self.point_source_event_indices[point_index])
                right_indices = set(self.point_source_event_indices[point_index + 1])
                if left_value <= 0.0 < right_value:
                    return tuple(sorted(right_indices))
                if right_value <= 0.0 < left_value:
                    return tuple(sorted(left_indices))
                shared_indices = left_indices & right_indices
                if shared_indices:
                    return tuple(sorted(shared_indices))
                if not left_indices:
                    return tuple(sorted(right_indices)) if left_value <= 0.0 else ()
                if not right_indices:
                    return tuple(sorted(left_indices)) if right_value <= 0.0 else ()
                return ()
        return tuple(sorted(indices))


@dataclass(frozen=True)
class PreviewHitTestInput:
    x: float
    y: float
    width: float
    height: float
    viewport_start_sec: float
    viewport_end_sec: float
    event_hit_regions: tuple[PreviewEventHitRegion, ...]
    curve_hit_regions: tuple[PreviewCurveHitRegion, ...] = ()

    def __post_init__(self) -> None:
        regions = tuple(self.event_hit_regions)
        if any(not isinstance(region, PreviewEventHitRegion) for region in regions):
            raise ValueError("event_hit_regions must contain PreviewEventHitRegion values")
        object.__setattr__(self, "event_hit_regions", regions)
        curve_regions = tuple(self.curve_hit_regions)
        if any(not isinstance(region, PreviewCurveHitRegion) for region in curve_regions):
            raise ValueError("curve_hit_regions must contain PreviewCurveHitRegion values")
        object.__setattr__(self, "curve_hit_regions", curve_regions)


@dataclass(frozen=True)
class PreviewSelectionRequest:
    base_event_index: int
    base_plan_identity_digest: str
    render_revision: int
    final_output_binding: str | None = None

    def __post_init__(self) -> None:
        _require_int(self.base_event_index, "base_event_index", non_negative=True)
        if (
            not isinstance(self.base_plan_identity_digest, str)
            or not self.base_plan_identity_digest
        ):
            raise ValueError("base_plan_identity_digest must be a non-empty string")
        _require_int(self.render_revision, "render_revision", non_negative=True)
        if self.final_output_binding is not None and (
            not isinstance(self.final_output_binding, str)
            or not self.final_output_binding
        ):
            raise ValueError("final_output_binding must be non-empty text or None")


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
    cursor_frame_position = cursor_sec * VMD_FPS
    cursor_frame = int(round(cursor_frame_position))

    lane_curves = tuple(
        region
        for region in value.curve_hit_regions
        if region.vowel == vowel
    )
    lane_height = height / len(PREVIEW_ROW_VOWELS)
    base_y = (lane_index + 1) * lane_height - 2.0
    max_curve_height = lane_height - 4.0
    for curve in reversed(lane_curves):
        curve_value = curve.value_at(cursor_frame_position)
        if (
            curve_value is None
            or curve_value <= 0.0
            or max_curve_height <= 0.0
            or not base_y - max_curve_height * curve_value <= y <= base_y
        ):
            continue
        curve_event_indices = curve.source_event_indices_at(cursor_frame_position)
        if len(curve_event_indices) == 1:
            owner = curve_event_indices[0]
            if any(
                region.vowel == vowel and region.base_event_index == owner
                for region in value.event_hit_regions
            ):
                return owner
            return None
        if not curve.requires_source_ownership and not any(curve.point_source_event_indices):
            candidates = tuple(
                region
                for region in value.event_hit_regions
                if region.vowel == vowel
                and region.start_frame <= cursor_frame <= region.end_frame
            )
        else:
            minimum_visible_value = (base_y - y) / max_curve_height
            candidates = tuple(
                region
                for region in value.event_hit_regions
                if region.vowel == vowel
                and region.start_frame <= cursor_frame <= region.end_frame
                and region.peak_value + 0.0001 >= minimum_visible_value
                and (
                    not curve_event_indices
                    or region.base_event_index in curve_event_indices
                )
            )
        return candidates[0].base_event_index if len(candidates) == 1 else None

    candidates = tuple(
        region
        for region in value.event_hit_regions
        if region.vowel == vowel
        and region.start_frame <= cursor_frame <= region.end_frame
    )
    if lane_curves:
        return candidates[0].base_event_index if len(candidates) == 1 else None
    selected = min(
        candidates,
        key=lambda region: (
            abs(cursor_frame - region.base_peak_frame),
            region.base_event_index,
        ),
        default=None,
    )
    if selected is not None:
        return selected.base_event_index
    return None


def collect_preview_hit_regions(
    rows: Sequence[object],
) -> tuple[PreviewEventHitRegion, ...]:
    """Flatten immutable hit metadata without depending on wxPython."""
    regions: list[PreviewEventHitRegion] = []
    for row in rows:
        for segment in tuple(getattr(row, "segments", ())):
            regions.extend(tuple(getattr(segment, "event_hit_regions", ())))
    return tuple(regions)


def collect_preview_curve_hit_regions(
    rows: Sequence[object],
) -> tuple[PreviewCurveHitRegion, ...]:
    """Collect the displayed curve points used for selection fallback hit-testing."""
    regions: list[PreviewCurveHitRegion] = []
    for row in rows:
        vowel = getattr(row, "vowel", None)
        for segment in tuple(getattr(row, "segments", ())):
            requires_source_ownership = (
                getattr(segment, "shape_kind", None) == "shared_final_output"
            )
            control_points = tuple(getattr(segment, "control_points", ()))
            points = tuple(
                (getattr(point, "frame_no", None), getattr(point, "value", None))
                for point in control_points
            )
            if not points:
                if requires_source_ownership:
                    raise ValueError("shared Preview curve has no control points")
                continue
            segment_indices = tuple(getattr(segment, "source_event_indices", ()))
            if not segment_indices:
                segment_indices = tuple(
                    index
                    for index in (getattr(segment, "source_event_index", None),)
                    if index is not None
                )
            point_sources = tuple(
                tuple(getattr(point, "source_event_indices", ())) or segment_indices
                for point in control_points
            )
            point_kinds = tuple(
                getattr(point, "point_kind", "control") for point in control_points
            )
            try:
                regions.append(
                    PreviewCurveHitRegion(
                        vowel,
                        points,
                        point_source_event_indices=point_sources,
                        point_kinds=point_kinds,
                        requires_source_ownership=requires_source_ownership,
                    )
                )
            except ValueError:
                if requires_source_ownership:
                    raise
                continue
    return tuple(regions)


__all__ = [
    "PREVIEW_ROW_VOWELS",
    "PreviewCurveHitRegion",
    "PreviewEventHitRegion",
    "PreviewHitTestInput",
    "PreviewSelectionRequest",
    "collect_preview_curve_hit_regions",
    "collect_preview_hit_regions",
    "hit_test_preview_event",
]
