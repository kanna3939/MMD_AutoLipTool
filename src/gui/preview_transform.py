from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Protocol, Sequence

from gui.i18n_strings import INTERNAL_VOWEL_ORDER
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import (
    AsymmetricTrapezoidSpec,
    GroupedNearbyVowelEvents,
    MultiPointEnvelopeSpec,
    SUPPORTED_MORPHS,
    VMD_FPS,
    _apply_closing_hold_to_trapezoid_spec,
    _apply_closing_softness_to_trapezoid_spec,
    _apply_cross_vowel_transition_candidates_to_points,
    _build_same_vowel_span_adjusted_points,
    _build_adjusted_trapezoid_spec,
    _build_existing_point_morph_frames_with_metadata,
    _build_ms11_3_group_morph_frames_with_spec,
    _event_start_frame,
    _first_non_zero_shape_start_frame_in_group,
    _group_nearby_same_vowel_events_with_source_indices,
    _is_ms11_3_attemptable_group,
    _normalize_closing_hold_frames,
    _normalize_closing_softness_frames,
    _resolve_effective_final_closing_hold_frames,
    _resolve_effective_final_closing_softness_frames,
)

PREVIEW_ROW_VOWELS: tuple[str, str, str, str, str] = INTERNAL_VOWEL_ORDER


class TimelinePointLike(Protocol):
    vowel: str
    time_sec: float
    duration_sec: float
    start_sec: float | None
    end_sec: float | None
    peak_value: float | None
    value: float


class ObservationLike(Protocol):
    event_index: int
    is_bridgeable_micro_gap_candidate: bool
    is_bridgeable_same_vowel_micro_gap_candidate: bool
    is_same_vowel_burst_candidate: bool
    is_bridgeable_cross_vowel_transition_candidate: bool
    is_cross_vowel_zero_run_continuity_floor_candidate: bool
    local_peak: float | None
    previous_non_zero_event_index: int | None
    next_non_zero_event_index: int | None
    span_start_index: int | None
    span_end_index: int | None
    rms_window_times_sec: Sequence[float]
    rms_window_values: Sequence[float]


@dataclass(frozen=True)
class PreviewControlPoint:
    time_sec: float
    value: float
    point_kind: str = "control"
    frame_no: int | None = None


@dataclass(frozen=True)
class PreviewSegment:
    start_sec: float
    end_sec: float
    duration_sec: float
    intensity: float
    vowel: str
    shape_kind: str = "empty"
    control_points: tuple[PreviewControlPoint, ...] = ()


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


def build_preview_data(
    timeline: Sequence[TimelinePointLike] | None,
    *,
    observations: Sequence[ObservationLike] | None = None,
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
) -> PreviewData:
    """writer と同じ shape semantics を Preview 用に再構成する。"""
    if not timeline:
        return empty_preview_data()

    normalized_points = _normalize_preview_timeline_points(timeline)
    if not normalized_points:
        return empty_preview_data()

    rows = {row.vowel: row for row in empty_preview_data().rows}
    normalized_closing_hold_frames = _normalize_closing_hold_frames(
        closing_hold_frames
    )
    normalized_closing_softness_frames = _normalize_closing_softness_frames(
        closing_softness_frames
    )

    grouped_points, grouped_source_indices = _build_preview_points_for_grouping(
        normalized_points,
        observations=observations,
    )
    grouped_events = _group_nearby_same_vowel_events_with_source_indices(
        grouped_points,
        grouped_source_indices,
    )
    for grouped_event_index, grouped_event in enumerate(grouped_events):
        next_group_start_frame = _next_group_start_frame_for_preview(
            grouped_events,
            grouped_event_index,
        )

        multi_point_segment = _build_preview_segment_from_multi_point_group(
            grouped_event,
            closing_hold_frames=normalized_closing_hold_frames,
            closing_softness_frames=normalized_closing_softness_frames,
            next_shape_start_frame=next_group_start_frame,
        )
        if multi_point_segment is not None:
            rows[multi_point_segment.vowel].segments.append(multi_point_segment)
            continue

        for segment in _build_preview_segments_from_existing_group(
            grouped_event,
            observations=observations,
            closing_hold_frames=normalized_closing_hold_frames,
            closing_softness_frames=normalized_closing_softness_frames,
            next_group_start_frame=next_group_start_frame,
        ):
            rows[segment.vowel].segments.append(segment)

    for row in rows.values():
        row.segments.sort(key=lambda segment: (segment.start_sec, segment.end_sec))

    return PreviewData(rows=[rows[vowel] for vowel in PREVIEW_ROW_VOWELS])


def _normalize_preview_timeline_points(
    timeline: Sequence[TimelinePointLike],
) -> list[VowelTimelinePoint]:
    normalized: list[VowelTimelinePoint] = []
    for point in timeline:
        vowel = str(getattr(point, "vowel", ""))
        if vowel not in SUPPORTED_MORPHS:
            continue

        time_sec = _to_finite_float(getattr(point, "time_sec", None))
        if time_sec is None or time_sec < 0.0:
            continue

        duration_sec = _to_finite_float(getattr(point, "duration_sec", None))
        if duration_sec is None:
            duration_sec = 0.0

        start_sec = _to_finite_float(getattr(point, "start_sec", None))
        end_sec = _to_finite_float(getattr(point, "end_sec", None))
        peak_value = _resolve_intensity(point)

        try:
            normalized.append(
                VowelTimelinePoint(
                    time_sec=time_sec,
                    vowel=vowel,
                    value=peak_value,
                    peak_value=peak_value,
                    duration_sec=max(duration_sec, 0.0),
                    start_sec=start_sec,
                    end_sec=end_sec,
                )
            )
        except (TypeError, ValueError):
            continue

    normalized.sort(key=lambda point: (point.time_sec, point.start_sec, point.end_sec))
    return normalized


def _build_preview_segment_from_multi_point_group(
    grouped_events: GroupedNearbyVowelEvents,
    *,
    closing_hold_frames: int,
    closing_softness_frames: int,
    next_shape_start_frame: int | None,
) -> PreviewSegment | None:
    if not _is_ms11_3_attemptable_group(grouped_events):
        return None

    effective_closing_hold_frames = _resolve_effective_final_closing_hold_frames(
        closing_hold_frames=closing_hold_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    effective_closing_softness_frames = _resolve_effective_final_closing_softness_frames(
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    result = _build_ms11_3_group_morph_frames_with_spec(
        grouped_events,
        closing_hold_frames=effective_closing_hold_frames,
        closing_softness_frames=effective_closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    if result is None:
        return None

    _, spec = result
    return _preview_segment_from_multi_point_spec(spec)


def _build_preview_segments_from_existing_group(
    grouped_events: GroupedNearbyVowelEvents,
    *,
    observations: Sequence[ObservationLike] | None,
    closing_hold_frames: int,
    closing_softness_frames: int,
    next_group_start_frame: int | None,
) -> list[PreviewSegment]:
    segments: list[PreviewSegment] = []
    point_count = len(grouped_events.points)
    for point_index, (source_event_index, point) in enumerate(
        zip(grouped_events.source_event_indices, grouped_events.points)
    ):
        next_shape_start_frame = next_group_start_frame
        if point_index + 1 < point_count:
            intra_group_next_shape_start_frame = _first_non_zero_shape_start_frame_in_group(
                grouped_events,
                start_point_index=point_index + 1,
            )
            if intra_group_next_shape_start_frame is not None:
                next_shape_start_frame = intra_group_next_shape_start_frame

        segment = _build_preview_segment_from_existing_point(
            point,
            source_event_index=source_event_index,
            observations=observations,
            closing_hold_frames=closing_hold_frames,
            closing_softness_frames=closing_softness_frames,
            next_shape_start_frame=next_shape_start_frame,
        )
        if segment is not None:
            segments.append(segment)
    return segments


def _build_preview_segment_from_existing_point(
    point: VowelTimelinePoint,
    *,
    source_event_index: int | None,
    observations: Sequence[ObservationLike] | None,
    closing_hold_frames: int,
    closing_softness_frames: int,
    next_shape_start_frame: int | None,
) -> PreviewSegment | None:
    effective_closing_hold_frames = _resolve_effective_final_closing_hold_frames(
        closing_hold_frames=closing_hold_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    effective_closing_softness_frames = _resolve_effective_final_closing_softness_frames(
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    spec = _build_adjusted_trapezoid_spec(
        point,
        source_event_index=source_event_index,
        observations=observations,
    )
    if spec is not None:
        softened_spec = _apply_closing_softness_to_trapezoid_spec(
            _apply_closing_hold_to_trapezoid_spec(
                spec,
                closing_hold_frames=effective_closing_hold_frames,
                next_shape_start_frame=next_shape_start_frame,
            ),
            closing_softness_frames=effective_closing_softness_frames,
            next_shape_start_frame=next_shape_start_frame,
        )
        return _preview_segment_from_trapezoid_spec(softened_spec)

    expanded_with_flags, _, _ = _build_existing_point_morph_frames_with_metadata(
        point,
        source_event_index=source_event_index,
        observations=observations,
        closing_hold_frames=effective_closing_hold_frames,
        closing_softness_frames=effective_closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    if not expanded_with_flags:
        return None

    control_points = _fallback_preview_control_points(expanded_with_flags)
    return _build_preview_segment(
        vowel=point.vowel,
        shape_kind="peak_fallback",
        control_points=control_points,
    )


def _preview_segment_from_trapezoid_spec(
    spec: AsymmetricTrapezoidSpec,
) -> PreviewSegment:
    control_points: list[PreviewControlPoint] = [
        PreviewControlPoint(
            time_sec=_frame_to_seconds(spec.start_frame),
            value=0.0,
            point_kind="start_zero",
            frame_no=spec.start_frame,
        ),
        PreviewControlPoint(
            time_sec=_frame_to_seconds(spec.peak_start_frame),
            value=spec.peak_value,
            point_kind="top",
            frame_no=spec.peak_start_frame,
        ),
    ]
    if spec.peak_end_frame != spec.peak_start_frame:
        control_points.append(
            PreviewControlPoint(
                time_sec=_frame_to_seconds(spec.peak_end_frame),
                value=spec.peak_value if spec.peak_end_value is None else spec.peak_end_value,
                point_kind="top",
                frame_no=spec.peak_end_frame,
            )
        )
    if spec.closing_hold_frame is not None and spec.closing_hold_value is not None:
        control_points.append(
            PreviewControlPoint(
                time_sec=_frame_to_seconds(spec.closing_hold_frame),
                value=max(0.0, min(spec.closing_hold_value, 1.0)),
                point_kind="hold",
                frame_no=spec.closing_hold_frame,
            )
        )
    if spec.closing_mid_frame is not None and spec.closing_mid_value is not None:
        control_points.append(
            PreviewControlPoint(
                time_sec=_frame_to_seconds(spec.closing_mid_frame),
                value=max(0.0, min(spec.closing_mid_value, 1.0)),
                point_kind="slope_mid",
                frame_no=spec.closing_mid_frame,
            )
        )
    control_points.append(
        PreviewControlPoint(
            time_sec=_frame_to_seconds(spec.end_frame),
            value=0.0,
            point_kind="end_zero",
            frame_no=spec.end_frame,
        )
    )
    return _build_preview_segment(
        vowel=spec.vowel,
        shape_kind=spec.shape_kind,
        control_points=tuple(control_points),
    )


def _preview_segment_from_multi_point_spec(
    spec: MultiPointEnvelopeSpec,
) -> PreviewSegment:
    control_points = tuple(
        PreviewControlPoint(
            time_sec=_frame_to_seconds(point.frame_no),
            value=max(0.0, min(point.value, 1.0)),
            point_kind=point.point_kind,
            frame_no=point.frame_no,
        )
        for point in spec.control_points
    )
    return _build_preview_segment(
        vowel=spec.vowel,
        shape_kind=spec.shape_kind,
        control_points=control_points,
    )


def _build_preview_segment(
    *,
    vowel: str,
    shape_kind: str,
    control_points: tuple[PreviewControlPoint, ...],
) -> PreviewSegment:
    if not control_points:
        return PreviewSegment(
            start_sec=0.0,
            end_sec=0.0,
            duration_sec=0.0,
            intensity=0.0,
            vowel=vowel,
            shape_kind=shape_kind,
            control_points=(),
        )

    start_sec = control_points[0].time_sec
    end_sec = control_points[-1].time_sec
    intensity = max((point.value for point in control_points), default=0.0)
    return PreviewSegment(
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=max(end_sec - start_sec, 0.0),
        intensity=max(0.0, min(intensity, 1.0)),
        vowel=vowel,
        shape_kind=shape_kind,
        control_points=control_points,
    )


def _next_group_start_frame_for_preview(
    grouped_events: list[GroupedNearbyVowelEvents],
    current_group_index: int,
) -> int | None:
    for next_group in grouped_events[current_group_index + 1 :]:
        next_start_frame = _first_non_zero_shape_start_frame_in_group(next_group)
        if next_start_frame is not None:
            return next_start_frame
    return None


def _fallback_point_kind(index: int, point_count: int) -> str:
    if point_count <= 0:
        return "control"
    if index == 0:
        return "start_zero"
    if index + 1 == point_count:
        return "end_zero"
    return "top"


def _fallback_preview_control_points(
    expanded_with_flags: Sequence[tuple[int, str, float, bool]],
) -> tuple[PreviewControlPoint, ...]:
    if not expanded_with_flags:
        return ()

    internal_values = [float(value) for _, _, value, _ in expanded_with_flags[1:-1]]
    highest_internal_value = max(internal_values, default=0.0)
    control_points: list[PreviewControlPoint] = []
    point_count = len(expanded_with_flags)
    for index, (frame_no, _, value, _) in enumerate(expanded_with_flags):
        normalized_value = max(0.0, min(float(value), 1.0))
        point_kind = _fallback_point_kind(index, point_count)
        if (
            0 < index < point_count - 1
            and normalized_value > 0.0
            and normalized_value < highest_internal_value - 1e-9
        ):
            point_kind = "slope_mid"
        control_points.append(
            PreviewControlPoint(
                time_sec=_frame_to_seconds(frame_no),
                value=normalized_value,
                point_kind=point_kind,
                frame_no=frame_no,
            )
        )
    return tuple(control_points)


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


def _frame_to_seconds(frame_no: int) -> float:
    return max(float(frame_no), 0.0) / VMD_FPS


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


def _build_preview_points_for_grouping(
    normalized_points: Sequence[VowelTimelinePoint],
    *,
    observations: Sequence[ObservationLike] | None = None,
) -> tuple[list[VowelTimelinePoint], tuple[int, ...]]:
    # Preview 側も writer と同じ observation family を使い、
    # export と同じ grouping 入力 semantics を再利用する。
    if not normalized_points:
        return [], ()
    adjusted_points = _apply_cross_vowel_transition_candidates_to_points(
        normalized_points,
        observations=observations,
    )
    if not observations:
        return adjusted_points, tuple(range(len(adjusted_points)))
    return _build_same_vowel_span_adjusted_points(
        adjusted_points,
        observations=observations,
    )


def _collect_preview_bridge_candidate_indices(
    points: Sequence[VowelTimelinePoint],
    observations: Sequence[ObservationLike],
) -> set[int]:
    candidate_indices: set[int] = set()
    if len(points) != len(observations):
        return candidate_indices

    for index, (point, observation) in enumerate(zip(points, observations)):
        if not getattr(observation, "is_bridgeable_micro_gap_candidate", False):
            continue
        previous_index = getattr(observation, "previous_non_zero_event_index", None)
        next_index = getattr(observation, "next_non_zero_event_index", None)
        if previous_index != index - 1 or next_index != index + 1:
            continue
        if previous_index is None or next_index is None:
            continue
        if points[previous_index].vowel != point.vowel:
            continue
        if points[next_index].vowel != point.vowel:
            continue
        candidate_indices.add(index)
    return candidate_indices


__all__ = [
    "PREVIEW_ROW_VOWELS",
    "PreviewControlPoint",
    "PreviewSegment",
    "PreviewRow",
    "PreviewData",
    "TimelinePointLike",
    "ObservationLike",
    "empty_preview_data",
    "build_preview_data",
]
