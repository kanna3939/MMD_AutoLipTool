from __future__ import annotations

from dataclasses import dataclass, replace
import math
import struct
from typing import Any, Protocol, Sequence

from src.core.preview_hit_test import PreviewEventHitRegion
from src.core.morph_name_sets import (
    SEMANTIC_VOWEL_ORDER,
    validate_output_morph_names,
)

INTERNAL_VOWEL_ORDER = SEMANTIC_VOWEL_ORDER
from src.vmd_writer import VowelTimelinePoint
from src.vmd_writer.legacy_shape_compat import (
    AsymmetricTrapezoidSpec,
    GroupedNearbyVowelEvents,
    MultiPointEnvelopeSpec,
    MORPH_FRAME_OPEN_EPSILON,
    SUPPORTED_MORPHS,
    VMD_FPS,
    apply_closing_hold_to_trapezoid_spec,
    apply_closing_softness_to_trapezoid_spec,
    apply_cross_vowel_transition_candidates_to_points,
    build_same_vowel_span_adjusted_points,
    build_adjusted_trapezoid_spec,
    build_existing_point_morph_frames_with_metadata,
    build_ms11_3_group_morph_frames_with_spec,
    first_non_zero_shape_start_frame_in_group,
    group_nearby_same_vowel_events_with_source_indices,
    is_ms11_3_attemptable_group,
    normalize_closing_hold_frames,
    normalize_closing_softness_frames,
    resolve_effective_final_closing_hold_frames,
    resolve_effective_final_closing_softness_frames,
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
    vowel_token_index: int | None
    is_long_vowel_continuation: bool
    long_vowel_source_token_index: int | None


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
    source_event_indices: tuple[int, ...] = ()


@dataclass(frozen=True)
class PreviewSegment:
    start_sec: float
    end_sec: float
    duration_sec: float
    intensity: float
    vowel: str
    shape_kind: str = "empty"
    control_points: tuple[PreviewControlPoint, ...] = ()
    source_event_index: int | None = None
    frame_range: tuple[int, int] | None = None
    value_range: tuple[float, float] | None = None
    fallback_reason: str | None = None
    is_zero_peak: bool = False
    is_short_span: bool = False
    source_event_indices: tuple[int, ...] = ()
    event_ranges: tuple[tuple[int, int], ...] = ()
    internal_shape_source_tokens: tuple[int, ...] = ()
    event_hit_regions: tuple[PreviewEventHitRegion, ...] = ()
    display_name: str | None = None


@dataclass(frozen=True)
class PreviewRow:
    vowel: str
    segments: list[PreviewSegment]
    display_name: str | None = None


@dataclass(frozen=True)
class PreviewData:
    rows: list[PreviewRow]
    selection_regions: tuple[PreviewEventHitRegion, ...] = ()
    final_output_binding: str | None = None


def _display_name_for_vowel(
    vowel: str,
    output_morph_names: tuple[str, ...],
) -> str:
    try:
        index = INTERNAL_VOWEL_ORDER.index(vowel)
    except ValueError as error:
        raise ValueError(f"Unsupported semantic vowel: {vowel!r}") from error
    return output_morph_names[index]


def _with_display_name(
    segment: PreviewSegment,
    output_morph_names: tuple[str, ...],
) -> PreviewSegment:
    return replace(
        segment,
        display_name=_display_name_for_vowel(segment.vowel, output_morph_names),
    )


def empty_preview_data(
    *,
    output_morph_names: Sequence[str] = INTERNAL_VOWEL_ORDER,
) -> PreviewData:
    normalized_output_morph_names = validate_output_morph_names(output_morph_names)
    return PreviewData(
        rows=[
            PreviewRow(
                vowel=vowel,
                segments=[],
                display_name=_display_name_for_vowel(
                    vowel,
                    normalized_output_morph_names,
                ),
            )
            for vowel in PREVIEW_ROW_VOWELS
        ]
    )


def build_preview_data_from_effective_shape_plan(
    effective_plan: Any,
    *,
    output_morph_names: Sequence[str] = INTERNAL_VOWEL_ORDER,
) -> PreviewData:
    """Convert a resolved MS21 shape plan without recalculating its shape."""
    normalized_output_morph_names = validate_output_morph_names(output_morph_names)
    rows = {
        row.vowel: row
        for row in empty_preview_data(
            output_morph_names=normalized_output_morph_names
        ).rows
    }
    effective_events = tuple(getattr(effective_plan, "effective_events", ()))
    events_by_index: dict[int, object] = {}
    for event in effective_events:
        base_event_index = getattr(event, "base_event_index", None)
        if (
            isinstance(base_event_index, bool)
            or not isinstance(base_event_index, int)
            or base_event_index < 0
            or base_event_index in events_by_index
        ):
            raise ValueError("effective events require unique non-negative base indices")
        events_by_index[base_event_index] = event
    claimed_event_indices: set[int] = set()
    for shape in tuple(getattr(effective_plan, "shapes", ())):
        vowel = str(getattr(shape, "vowel", ""))
        if vowel not in rows:
            raise ValueError(f"Unsupported vowel morph: {vowel}")
        control_points = tuple(
            PreviewControlPoint(
                time_sec=max(float(point.frame_no), 0.0) / VMD_FPS,
                value=float(point.value),
                point_kind=str(point.point_kind),
                frame_no=int(point.frame_no),
            )
            for point in tuple(getattr(shape, "control_points", ()))
        )
        if not control_points:
            continue
        raw_source_event_indices = tuple(
            getattr(shape, "real_base_event_indices", ())
        )
        if any(
            isinstance(index, bool) or not isinstance(index, int) or index < 0
            for index in raw_source_event_indices
        ):
            raise ValueError("shape provenance requires non-negative integer indices")
        source_event_indices = tuple(raw_source_event_indices)
        raw_event_ranges = tuple(getattr(shape, "event_ranges", ()))
        event_ranges: list[tuple[int, int]] = []
        for event_range in raw_event_ranges:
            if not isinstance(event_range, (tuple, list)) or len(event_range) != 2:
                raise ValueError("shape event range must contain start and end frames")
            start_frame, end_frame = event_range
            if (
                isinstance(start_frame, bool)
                or not isinstance(start_frame, int)
                or isinstance(end_frame, bool)
                or not isinstance(end_frame, int)
                or start_frame < 0
                or end_frame < start_frame
            ):
                raise ValueError("shape event range must be ordered non-negative integers")
            event_ranges.append((start_frame, end_frame))
        event_ranges_tuple = tuple(event_ranges)
        if len(source_event_indices) != len(event_ranges_tuple):
            raise ValueError("shape provenance indices and event ranges must have equal length")
        event_hit_regions: list[PreviewEventHitRegion] = []
        for source_event_index, (start_frame, end_frame) in zip(
            source_event_indices, event_ranges_tuple
        ):
            if source_event_index in claimed_event_indices:
                raise ValueError("base event is referenced by more than one shape")
            claimed_event_indices.add(source_event_index)
            event = events_by_index.get(source_event_index)
            if event is None:
                raise ValueError("shape provenance references an unknown base event")
            event_vowel = str(getattr(event, "vowel", ""))
            event_start = int(getattr(event, "start_frame"))
            event_peak = int(getattr(event, "peak_frame"))
            event_end = int(getattr(event, "end_frame"))
            if event_vowel != vowel or (start_frame, end_frame) != (event_start, event_end):
                raise ValueError("shape provenance does not match its effective event")
            event_hit_regions.append(
                PreviewEventHitRegion(
                    base_event_index=source_event_index,
                    vowel=event_vowel,
                    start_frame=event_start,
                    base_peak_frame=event_peak,
                    end_frame=event_end,
                    peak_value=float(getattr(event, "peak_value")),
                )
            )
        values = tuple(point.value for point in control_points)
        start_sec = control_points[0].time_sec
        end_sec = control_points[-1].time_sec
        rows[vowel].segments.append(
            PreviewSegment(
                start_sec=start_sec,
                end_sec=end_sec,
                duration_sec=max(end_sec - start_sec, 0.0),
                intensity=max(values),
                vowel=vowel,
                shape_kind=str(getattr(shape, "shape_kind", "effective_shape")),
                control_points=control_points,
                source_event_index=(source_event_indices[0] if source_event_indices else None),
                frame_range=(control_points[0].frame_no, control_points[-1].frame_no),
                value_range=(min(values), max(values)),
                fallback_reason=getattr(shape, "fallback_reason", None),
                is_zero_peak=max(values) <= MORPH_FRAME_OPEN_EPSILON,
                is_short_span=(control_points[-1].frame_no - control_points[0].frame_no) <= 1,
                source_event_indices=source_event_indices,
                event_ranges=event_ranges_tuple,
                internal_shape_source_tokens=tuple(
                    int(token)
                    for token in getattr(shape, "internal_shape_source_tokens", ())
                ),
                event_hit_regions=tuple(event_hit_regions),
                display_name=_display_name_for_vowel(
                    vowel,
                    normalized_output_morph_names,
                ),
            )
        )
    for row in rows.values():
        row.segments.sort(key=lambda segment: (segment.start_sec, segment.end_sec))
    return PreviewData(rows=[rows[vowel] for vowel in PREVIEW_ROW_VOWELS])


def build_preview_data_from_shared_final_output(context: Any) -> PreviewData:
    """Build curve geometry and event selection metadata from one B2 context."""
    from src.core.final_output_projection import shared_output_consumer_view

    view = shared_output_consumer_view(context)
    return _build_preview_data_from_validated_consumer_view(context, view)


def _build_preview_data_from_validated_consumer_view(
    context: Any,
    view: Any,
) -> PreviewData:
    from src.vmd_writer.final_morph_closure_adapter import candidate_closure_value

    identity = view.identity
    candidate = view.candidate
    if (
        identity is None
        or candidate is None
        or getattr(candidate, "state", None) != "valid"
        or getattr(candidate, "plan", None) is None
    ):
        raise ValueError("a valid shared final-output context is required")
    binding = getattr(identity, "binding_digest", None)
    if not isinstance(binding, str) or not binding:
        raise ValueError("shared final-output identity is invalid")
    output_mapping = tuple(
        output_name
        for _, output_name in getattr(identity.input_identity, "output_mapping", ())
    )
    normalized_names = validate_output_morph_names(output_mapping)
    rows = {
        row.vowel: row
        for row in empty_preview_data(output_morph_names=normalized_names).rows
    }
    plan = candidate.plan
    issuer_evidence = getattr(
        getattr(getattr(context, "issuer_context", None), "legacy_context", None),
        "issuer_evidence",
        None,
    )
    if issuer_evidence is None:
        raise ValueError("shared Preview requires source selection evidence")
    source_events_by_index = {
        event.base_event_index: event for event in view.source_events
    }
    if len(source_events_by_index) != len(view.source_events):
        raise ValueError("shared Preview source event indices are duplicated")
    source_events_by_id: dict[str, tuple[int, ...]] = {
        f"source:event:{event_index}": (event_index,)
        for event_index in source_events_by_index
    }
    source_point_kinds_by_id: dict[str, str] = {}
    transition_owner_by_point: dict[tuple[str, int], int] = {}
    transition_binding = view.transition_binding
    if transition_binding is not None:
        for decision in transition_binding.resolution.decisions:
            if decision.state != "applied":
                continue
            key = (decision.next_morph, decision.candidate_start_frame)
            if key in transition_owner_by_point:
                raise ValueError("shared Preview transition point has ambiguous event ownership")
            transition_owner_by_point[key] = decision.next_event_index
    for shape in issuer_evidence.shapes:
        shape_events = tuple(
            source_events_by_index[event_index]
            for event_index in shape.base_event_indices
            if event_index in source_events_by_index
        )
        if (
            not shape_events
            or len(shape_events) != len(shape.base_event_indices)
            or len(set(shape.base_event_indices)) != len(shape.base_event_indices)
            or any(event.vowel != shape.semantic_morph for event in shape_events)
        ):
            raise ValueError("shared Preview shape ownership is incomplete")
        shape_source_id = f"source:shape:{shape.shape_ordinal}"
        if shape_source_id in source_events_by_id:
            raise ValueError("shared Preview shape ownership is duplicated")
        source_events_by_id[shape_source_id] = tuple(shape.base_event_indices)
        tail_event_index = shape.terminal_base_event_index
        ordered_events = tuple(
            sorted(shape_events, key=lambda event: (event.peak_frame, event.base_event_index))
        )
        for point in shape.points:
            source_id = (
                f"source:shape:{shape.shape_ordinal}:"
                f"point:{point.point_ordinal}"
            )
            if source_id in source_events_by_id:
                raise ValueError("shared Preview shape point ownership is duplicated")
            source_point_kinds_by_id[source_id] = point.point_kind
            matching_events = ()
            if point.point_kind == "silence_core_zero":
                pass
            elif len(shape_events) == 1:
                matching_events = shape_events
            elif point.point_kind == "top":
                matching_events = tuple(
                    event
                    for event in shape_events
                    if event.peak_frame == point.frame_no
                )
                if not matching_events:
                    matching_events = tuple(
                        event
                        for event in shape_events
                        if event.end_frame == point.frame_no
                    )
            elif point.point_kind == "start_zero":
                matching_events = tuple(
                    event
                    for event in ordered_events[:1]
                    if event.start_frame == point.frame_no
                )
            elif point.point_kind == "valley":
                for left_event, right_event in zip(ordered_events, ordered_events[1:]):
                    if left_event.peak_frame <= point.frame_no <= right_event.peak_frame:
                        matching_events = (left_event, right_event)
                        break
            elif point.point_kind in {"hold", "slope_mid", "end_zero"}:
                matching_events = tuple(
                    event
                    for event in shape_events
                    if event.base_event_index == tail_event_index
                )
            # Several source events can legitimately share a frame or a shape
            # point. Keep every explicit match; the hit test declines a click
            # whose point ownership cannot be narrowed to one event.
            source_events_by_id[source_id] = tuple(
                sorted(event.base_event_index for event in matching_events)
            )
    for vowel in PREVIEW_ROW_VOWELS:
        cleanup_points = tuple(
            point for point in view.final_points if point.semantic_morph == vowel
        )
        key_points = (
            cleanup_points
            if view.cleanup_binding is not None
            else tuple(point for point in plan.points if point.semantic_morph == vowel)
        )
        if not key_points:
            continue
        first_frame = key_points[0].frame_no
        last_frame = key_points[-1].frame_no
        control_points: list[PreviewControlPoint] = []
        for key_point in key_points:
            frame_no = key_point.frame_no
            if view.cleanup_binding is not None:
                value = struct.unpack("<f", bytes.fromhex(key_point.binary32_hex))[0]
            else:
                value = candidate_closure_value(plan, vowel, frame_no)
            if value is None:
                raise ValueError("shared final key lies outside its closed domain")
            source_ids = tuple(key_point.source_ids)
            missing_shape_points = () if view.cleanup_binding is not None else tuple(
                source_id for source_id in source_ids
                if source_id.startswith("source:shape:")
                and ":point:" in source_id
                and source_id not in source_events_by_id
            )
            transition_owner = transition_owner_by_point.get(
                (vowel, key_point.frame_no)
            )
            if missing_shape_points and transition_owner is None:
                raise ValueError("shared Preview source point is missing")
            source_event_indices = (
                tuple(key_point.source_event_indices)
                if view.cleanup_binding is not None
                else (transition_owner,)
                if transition_owner is not None
                else tuple(
                    sorted(
                        {
                            event_index
                            for source_id in source_ids
                            for event_index in source_events_by_id.get(source_id, ())
                        }
                    )
                )
            )
            source_point_kinds = (
                set(key_point.point_kinds)
                if view.cleanup_binding is not None
                else {
                    source_point_kinds_by_id[source_id]
                    for source_id in source_ids
                    if source_id in source_point_kinds_by_id
                }
            )
            if "top" in source_point_kinds and float(value) > MORPH_FRAME_OPEN_EPSILON:
                point_kind = "top"
            elif len(source_point_kinds) == 1:
                point_kind = next(iter(source_point_kinds))
            else:
                point_kind = "shared_final_curve"
            control_points.append(
                PreviewControlPoint(
                    time_sec=frame_no / VMD_FPS,
                    value=float(value),
                    point_kind=point_kind,
                    frame_no=frame_no,
                    source_event_indices=source_event_indices,
                )
            )
        values = tuple(point.value for point in control_points)
        rows[vowel].segments.append(
            PreviewSegment(
                start_sec=control_points[0].time_sec,
                end_sec=control_points[-1].time_sec,
                duration_sec=max(
                    control_points[-1].time_sec - control_points[0].time_sec,
                    0.0,
                ),
                intensity=max(values),
                vowel=vowel,
                shape_kind="shared_final_output",
                control_points=tuple(control_points),
                frame_range=(first_frame, last_frame),
                value_range=(min(values), max(values)),
                is_zero_peak=max(values) <= MORPH_FRAME_OPEN_EPSILON,
                is_short_span=(last_frame - first_frame) <= 1,
                display_name=_display_name_for_vowel(vowel, normalized_names),
            )
        )
    selection_regions = tuple(
        PreviewEventHitRegion(
            base_event_index=event.base_event_index,
            vowel=event.vowel,
            start_frame=event.start_frame,
            base_peak_frame=event.peak_frame,
            end_frame=event.end_frame,
            peak_value=event.peak_value,
            group_event_indices=event.group_event_indices,
            shape_internal_source_tokens=event.shape_internal_source_tokens,
            long_vowel_source_event_index=event.long_vowel_source_event_index,
            long_vowel_role=event.long_vowel_role,
            long_vowel_mode=event.long_vowel_mode,
        )
        for event in view.source_events
    )
    return PreviewData(
        rows=[rows[vowel] for vowel in PREVIEW_ROW_VOWELS],
        selection_regions=selection_regions,
        final_output_binding=binding,
    )


def build_preview_data(
    timeline: Sequence[TimelinePointLike] | None,
    *,
    observations: Sequence[ObservationLike] | None = None,
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
    output_morph_names: Sequence[str] = INTERNAL_VOWEL_ORDER,
) -> PreviewData:
    """writer と同じ shape semantics を Preview 用に再構成する。"""
    normalized_output_morph_names = validate_output_morph_names(output_morph_names)
    if not timeline:
        return empty_preview_data(output_morph_names=normalized_output_morph_names)

    normalized_points = _normalize_preview_timeline_points(timeline)
    if not normalized_points:
        return empty_preview_data(output_morph_names=normalized_output_morph_names)

    rows = {
        row.vowel: row
        for row in empty_preview_data(
            output_morph_names=normalized_output_morph_names
        ).rows
    }
    normalized_closing_hold_frames = normalize_closing_hold_frames(
        closing_hold_frames
    )
    normalized_closing_softness_frames = normalize_closing_softness_frames(
        closing_softness_frames
    )

    grouped_points, grouped_source_indices = _build_preview_points_for_grouping(
        normalized_points,
        observations=observations,
    )
    grouped_events = group_nearby_same_vowel_events_with_source_indices(
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
            rows[multi_point_segment.vowel].segments.append(
                _with_display_name(multi_point_segment, normalized_output_morph_names)
            )
            continue

        for segment in _build_preview_segments_from_existing_group(
            grouped_event,
            observations=observations,
            closing_hold_frames=normalized_closing_hold_frames,
            closing_softness_frames=normalized_closing_softness_frames,
            next_group_start_frame=next_group_start_frame,
        ):
            rows[segment.vowel].segments.append(
                _with_display_name(segment, normalized_output_morph_names)
            )

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
                    vowel_token_index=getattr(point, "vowel_token_index", None),
                    is_long_vowel_continuation=getattr(point, "is_long_vowel_continuation", False),
                    long_vowel_source_token_index=getattr(point, "long_vowel_source_token_index", None),
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
    if not is_ms11_3_attemptable_group(grouped_events):
        return None

    effective_closing_hold_frames = resolve_effective_final_closing_hold_frames(
        closing_hold_frames=closing_hold_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    effective_closing_softness_frames = resolve_effective_final_closing_softness_frames(
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    result = build_ms11_3_group_morph_frames_with_spec(
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
            intra_group_next_shape_start_frame = first_non_zero_shape_start_frame_in_group(
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
    effective_closing_hold_frames = resolve_effective_final_closing_hold_frames(
        closing_hold_frames=closing_hold_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    effective_closing_softness_frames = resolve_effective_final_closing_softness_frames(
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    spec = build_adjusted_trapezoid_spec(
        point,
        source_event_index=source_event_index,
        observations=observations,
    )
    if spec is not None:
        softened_spec = apply_closing_softness_to_trapezoid_spec(
            apply_closing_hold_to_trapezoid_spec(
                spec,
                closing_hold_frames=effective_closing_hold_frames,
                next_shape_start_frame=next_shape_start_frame,
            ),
            closing_softness_frames=effective_closing_softness_frames,
            next_shape_start_frame=next_shape_start_frame,
        )
        return _preview_segment_from_trapezoid_spec(softened_spec)

    expanded_with_flags, _, _ = build_existing_point_morph_frames_with_metadata(
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
        source_event_index=source_event_index,
        fallback_reason="fallback_expansion",
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
        source_event_index=spec.source_event_index,
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
        source_event_index=spec.source_event_indices[0] if spec.source_event_indices else None,
    )


def _build_preview_segment(
    *,
    vowel: str,
    shape_kind: str,
    control_points: tuple[PreviewControlPoint, ...],
    source_event_index: int | None = None,
    fallback_reason: str | None = None,
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
            source_event_index=source_event_index,
            fallback_reason=fallback_reason,
        )

    start_sec = control_points[0].time_sec
    end_sec = control_points[-1].time_sec
    intensity = max((point.value for point in control_points), default=0.0)
    
    frame_numbers = [cp.frame_no for cp in control_points if cp.frame_no is not None]
    frame_range = (min(frame_numbers), max(frame_numbers)) if frame_numbers else None
    
    values = [cp.value for cp in control_points]
    value_range = (min(values), max(values)) if values else None
    
    is_zero_peak = intensity <= 1e-9
    is_short_span = frame_range is not None and (frame_range[1] - frame_range[0]) <= 2

    return PreviewSegment(
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=max(end_sec - start_sec, 0.0),
        intensity=max(0.0, min(intensity, 1.0)),
        vowel=vowel,
        shape_kind="zero_peak" if is_zero_peak and shape_kind != "empty" else shape_kind,
        control_points=control_points,
        source_event_index=source_event_index,
        frame_range=frame_range,
        value_range=value_range,
        fallback_reason=fallback_reason,
        is_zero_peak=is_zero_peak,
        is_short_span=is_short_span,
    )


def _next_group_start_frame_for_preview(
    grouped_events: list[GroupedNearbyVowelEvents],
    current_group_index: int,
) -> int | None:
    for next_group in grouped_events[current_group_index + 1 :]:
        next_start_frame = first_non_zero_shape_start_frame_in_group(next_group)
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
    adjusted_points = apply_cross_vowel_transition_candidates_to_points(
        normalized_points,
        observations=observations,
    )
    if not observations:
        return adjusted_points, tuple(range(len(adjusted_points)))
    return build_same_vowel_span_adjusted_points(
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
    "PreviewEventHitRegion",
    "TimelinePointLike",
    "ObservationLike",
    "empty_preview_data",
    "build_preview_data",
    "build_preview_data_from_effective_shape_plan",
    "build_preview_data_from_shared_final_output",
]
