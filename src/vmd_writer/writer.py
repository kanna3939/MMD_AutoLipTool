from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Iterable

VMD_FPS = 30
MAX_MORPH_VALUE = 0.5
SUPPORTED_MORPHS = ("\u3042", "\u3044", "\u3046", "\u3048", "\u304a")
PEAK_SIDE_FRAME_OFFSET = 2
MAX_MORPH_FRAMES = 22000
MORPH_FRAME_OPEN_EPSILON = 1e-9
ISOLATED_OPEN_MAX_LENGTH_FRAMES = 3
ISOLATED_OPEN_MAX_PEAK_VALUE = MAX_MORPH_VALUE
MORPH_PULSE_MAX_LENGTH_FRAMES = 1
ENVELOPE_POINT_KINDS = ("start_zero", "top", "valley", "end_zero")

_VMD_HEADER = b"Vocaloid Motion Data 0002"
MorphFrame = tuple[int, str, float]
_MorphFrameWithFlags = tuple[int, str, float, bool]


@dataclass(frozen=True)
class VowelTimelinePoint:
    time_sec: float
    vowel: str
    value: float = MAX_MORPH_VALUE
    duration_sec: float = 0.0
    start_sec: float | None = None
    end_sec: float | None = None
    peak_value: float | None = None

    def __post_init__(self) -> None:
        time_sec = float(self.time_sec)
        peak_value = self.peak_value
        if peak_value is None:
            peak_value = float(self.value)
        else:
            peak_value = float(peak_value)
        duration_sec = max(float(self.duration_sec), 0.0)
        start_sec = self.start_sec
        end_sec = self.end_sec

        if start_sec is None and end_sec is None:
            if duration_sec > 0.0:
                half = duration_sec * 0.5
                start_sec = time_sec - half
                end_sec = time_sec + half
            else:
                start_sec = time_sec
                end_sec = time_sec
        elif start_sec is None:
            end_sec = float(end_sec)
            start_sec = end_sec - duration_sec if duration_sec > 0.0 else min(time_sec, end_sec)
        elif end_sec is None:
            start_sec = float(start_sec)
            end_sec = start_sec + duration_sec if duration_sec > 0.0 else max(time_sec, start_sec)
        else:
            start_sec = float(start_sec)
            end_sec = float(end_sec)

        if end_sec < start_sec:
            end_sec = start_sec
        if time_sec < start_sec:
            start_sec = time_sec
        if time_sec > end_sec:
            end_sec = time_sec

        interval_duration_sec = end_sec - start_sec
        if duration_sec <= 0.0:
            duration_sec = interval_duration_sec
        else:
            duration_sec = interval_duration_sec

        object.__setattr__(self, "time_sec", time_sec)
        object.__setattr__(self, "value", peak_value)
        object.__setattr__(self, "peak_value", peak_value)
        object.__setattr__(self, "duration_sec", duration_sec)
        object.__setattr__(self, "start_sec", start_sec)
        object.__setattr__(self, "end_sec", end_sec)


@dataclass(frozen=True)
class AsymmetricTrapezoidSpec:
    # MS11-2 single-top trapezoid spec. This remains the current active shape
    # format and is intentionally kept stable while MS11-3 specs are added.
    vowel: str
    start_frame: int
    peak_start_frame: int
    peak_end_frame: int
    end_frame: int
    peak_value: float
    # Keep the metadata minimal for MS11-2 Phase 2 while leaving a stable
    # place for later normalization-protection wiring in MS11-1-connected work.
    source_event_index: int | None = None
    is_ms11_2_generated: bool = True
    shape_kind: str = "asymmetric_trapezoid"
    protection_mode: str | None = None


@dataclass(frozen=True)
class EnvelopeControlPoint:
    # MS11-3 control point. The generation and expansion logic is intentionally
    # left for later tasks; this task only defines the internal contract.
    frame_no: int
    value: float
    point_kind: str

    def __post_init__(self) -> None:
        frame_no = int(self.frame_no)
        value = float(self.value)
        point_kind = _normalize_envelope_point_kind(self.point_kind)

        object.__setattr__(self, "frame_no", frame_no)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "point_kind", point_kind)


@dataclass(frozen=True)
class MultiPointEnvelopeSpec:
    # MS11-3 multi-point envelope spec. It is intentionally not connected to
    # the current write path yet; later tasks will use it for grouping,
    # expansion, and normalization-protection wiring.
    vowel: str
    control_points: tuple[EnvelopeControlPoint, ...]
    source_event_indices: tuple[int, ...]
    shape_kind: str = "ms11_3_multi_point_envelope"
    protection_mode: str | None = None
    is_ms11_3_generated: bool = True
    event_ranges: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        if self.vowel not in SUPPORTED_MORPHS:
            raise ValueError(f"Unsupported vowel morph: {self.vowel}")

        control_points = tuple(
            point if isinstance(point, EnvelopeControlPoint) else EnvelopeControlPoint(*point)
            for point in self.control_points
        )
        source_event_indices = tuple(int(index) for index in self.source_event_indices)
        event_ranges = tuple(
            _normalize_frame_range(range_start, range_end)
            for range_start, range_end in self.event_ranges
        )

        object.__setattr__(self, "control_points", control_points)
        object.__setattr__(self, "source_event_indices", source_event_indices)
        object.__setattr__(self, "event_ranges", event_ranges)

    @property
    def start_frame(self) -> int:
        return _control_point_frame_bounds(self.control_points)[0]

    @property
    def end_frame(self) -> int:
        return _control_point_frame_bounds(self.control_points)[1]


@dataclass(frozen=True)
class GroupedNearbyVowelEvents:
    # MS11-3 grouping candidate. This is intentionally lighter than the final
    # envelope spec and exists so later tasks can separate grouping from actual
    # control-point generation.
    vowel: str
    points: tuple[VowelTimelinePoint, ...]
    source_event_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.vowel not in SUPPORTED_MORPHS:
            raise ValueError(f"Unsupported vowel morph: {self.vowel}")

        points = tuple(self.points)
        source_event_indices = tuple(int(index) for index in self.source_event_indices)
        if not points:
            raise ValueError("points must not be empty")
        if len(points) != len(source_event_indices):
            raise ValueError("points and source_event_indices must have the same length")
        if any(point.vowel != self.vowel for point in points):
            raise ValueError("all grouped points must share the same vowel")

        object.__setattr__(self, "points", points)
        object.__setattr__(self, "source_event_indices", source_event_indices)

    @property
    def event_ranges(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            _normalize_frame_range(
                _sec_to_frame(_event_bounds(point)[0]),
                _sec_to_frame(_event_bounds(point)[1]),
            )
            for point in self.points
        )


@dataclass(frozen=True)
class MultiPointEnvelopeBuildResult:
    # Temporary build result for MS11-3 shape generation. Later tasks can use
    # failure_reason to decide whether to fall back to MS11-2 or legacy shapes.
    spec: MultiPointEnvelopeSpec | None
    failure_reason: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.spec is not None and self.failure_reason is None


@dataclass(frozen=True)
class MultiPointEnvelopeExpansionResult:
    # Temporary expansion result for MS11-3. Later tasks can connect this to
    # fallback and protection wiring without changing the MorphFrame contract.
    frames: tuple[MorphFrame, ...] = ()
    failure_reason: str | None = None

    @property
    def is_valid(self) -> bool:
        return bool(self.frames) and self.failure_reason is None


@dataclass(frozen=True)
class FinalNormalizationMetadata:
    protected_ms11_2_specs: tuple[AsymmetricTrapezoidSpec, ...] = ()
    protected_envelope_ranges: dict[str, list[tuple[int, int]]] | None = None
    allowed_non_zero_ranges: dict[str, list[tuple[int, int]]] | None = None
    required_zero_frames: dict[str, set[int]] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "protected_ms11_2_specs",
            tuple(self.protected_ms11_2_specs),
        )
        object.__setattr__(
            self,
            "protected_envelope_ranges",
            _normalize_frame_range_mapping(self.protected_envelope_ranges),
        )
        object.__setattr__(
            self,
            "allowed_non_zero_ranges",
            _normalize_frame_range_mapping(self.allowed_non_zero_ranges),
        )
        object.__setattr__(
            self,
            "required_zero_frames",
            _normalize_required_zero_frames(self.required_zero_frames),
        )


@dataclass(frozen=True)
class MorphFrameOpenState:
    # This state exists only to answer whether the mouth is open/closed
    # across all vowel morphs at each final frame.
    frame_values: dict[int, dict[str, float]]
    open_values: dict[int, float]
    epsilon: float = MORPH_FRAME_OPEN_EPSILON

    def value_at(self, frame_no: int, vowel: str) -> float:
        return self.frame_values.get(frame_no, {}).get(vowel, 0.0)

    def open_value_at(self, frame_no: int) -> float:
        return self.open_values.get(frame_no, 0.0)

    def is_open_frame(self, frame_no: int) -> bool:
        return self.open_value_at(frame_no) > self.epsilon

    def is_closed_frame(self, frame_no: int) -> bool:
        return self.open_value_at(frame_no) <= self.epsilon


@dataclass(frozen=True)
class MouthOpenInterval:
    start_frame: int
    end_frame: int
    is_open: bool
    peak_open_value: float

    @property
    def length_frames(self) -> int:
        return (self.end_frame - self.start_frame) + 1


@dataclass(frozen=True)
class IsolatedShortOpenCandidate:
    start_frame: int
    end_frame: int
    length_frames: int
    peak_open_value: float
    previous_interval_is_closed: bool
    next_interval_is_closed: bool


@dataclass(frozen=True)
class MorphShortPulseCandidate:
    vowel: str
    start_frame: int
    end_frame: int
    length_frames: int


def _normalize_envelope_point_kind(point_kind: str) -> str:
    normalized_point_kind = str(point_kind)
    if normalized_point_kind not in ENVELOPE_POINT_KINDS:
        raise ValueError(
            f"point_kind must be one of {ENVELOPE_POINT_KINDS}, got: {normalized_point_kind}"
        )
    return normalized_point_kind


def _normalize_frame_range(start_frame: int, end_frame: int) -> tuple[int, int]:
    normalized_start_frame = int(start_frame)
    normalized_end_frame = int(end_frame)
    if normalized_end_frame < normalized_start_frame:
        raise ValueError("event range end_frame must be >= start_frame")
    return (normalized_start_frame, normalized_end_frame)


def _normalize_frame_range_mapping(
    ranges_by_vowel: dict[str, list[tuple[int, int]]] | None,
) -> dict[str, list[tuple[int, int]]]:
    if not ranges_by_vowel:
        return {}

    normalized_ranges: dict[str, list[tuple[int, int]]] = {}
    for vowel, ranges in ranges_by_vowel.items():
        normalized_ranges[vowel] = [
            _normalize_frame_range(start_frame, end_frame)
            for start_frame, end_frame in ranges
        ]
    return normalized_ranges


def _normalize_required_zero_frames(
    required_zero_frames: dict[str, set[int]] | None,
) -> dict[str, set[int]]:
    if not required_zero_frames:
        return {}

    normalized_required_zero_frames: dict[str, set[int]] = {}
    for vowel, frame_numbers in required_zero_frames.items():
        normalized_required_zero_frames[vowel] = {
            int(frame_no)
            for frame_no in frame_numbers
        }
    return normalized_required_zero_frames


def _control_point_frame_bounds(
    control_points: tuple[EnvelopeControlPoint, ...] | list[EnvelopeControlPoint],
) -> tuple[int, int]:
    if not control_points:
        raise ValueError("control_points must not be empty")

    frame_numbers = [point.frame_no for point in control_points]
    return (min(frame_numbers), max(frame_numbers))


def _is_minimally_valid_multi_point_envelope_spec(
    spec: MultiPointEnvelopeSpec,
) -> bool:
    control_points = spec.control_points
    if not control_points:
        return False

    point_kinds = tuple(point.point_kind for point in control_points)
    if point_kinds[0] != "start_zero":
        return False
    if point_kinds[-1] != "end_zero":
        return False
    if "top" not in point_kinds:
        return False

    frame_numbers = [point.frame_no for point in control_points]
    if frame_numbers != sorted(frame_numbers):
        return False

    return True


def _group_nearby_same_vowel_events(
    points: list[VowelTimelinePoint],
) -> list[GroupedNearbyVowelEvents]:
    if not points:
        return []

    grouped_events: list[GroupedNearbyVowelEvents] = []
    current_group_points: list[VowelTimelinePoint] = [points[0]]
    current_group_indices: list[int] = [0]

    for next_index, next_point in enumerate(points[1:], start=1):
        candidate_failure = _evaluate_grouping_candidate_failure(
            current_group_points=current_group_points,
            current_group_indices=current_group_indices,
            next_index=next_index,
            next_point=next_point,
        )
        if candidate_failure is None:
            current_group_points.append(next_point)
            current_group_indices.append(next_index)
            continue

        grouped_events.append(
            _build_grouped_nearby_vowel_events(
                current_group_points,
                current_group_indices,
            )
        )
        current_group_points = [next_point]
        current_group_indices = [next_index]

    grouped_events.append(
        _build_grouped_nearby_vowel_events(
            current_group_points,
            current_group_indices,
        )
    )
    return grouped_events


def _build_grouped_nearby_vowel_events(
    points: list[VowelTimelinePoint] | tuple[VowelTimelinePoint, ...],
    source_event_indices: list[int] | tuple[int, ...],
) -> GroupedNearbyVowelEvents:
    normalized_points = tuple(points)
    if not normalized_points:
        raise ValueError("points must not be empty")
    return GroupedNearbyVowelEvents(
        vowel=normalized_points[0].vowel,
        points=normalized_points,
        source_event_indices=tuple(source_event_indices),
    )


def _evaluate_grouping_candidate_failure(
    *,
    current_group_points: list[VowelTimelinePoint],
    current_group_indices: list[int],
    next_index: int,
    next_point: VowelTimelinePoint,
) -> str | None:
    previous_point = current_group_points[-1]
    candidate_points = tuple(current_group_points) + (next_point,)
    candidate_indices = tuple(current_group_indices) + (next_index,)

    # Fixed first-fail order for MS11-3 grouping.
    if previous_point.vowel != next_point.vowel:
        return "vowel_mismatch"
    if _calculate_grouping_gap_sec(previous_point, next_point) > (4.0 / VMD_FPS):
        return "gap_sec_exceeded"
    if not _is_frame_gap_or_rounding_viable(previous_point, next_point):
        return "frame_gap_or_rounding_invalid"
    if not _is_lightweight_global_multi_point_candidate_viable(candidate_points):
        return "global_collapse"
    if _is_obviously_incompatible_with_group_protection_requirements(
        candidate_points=candidate_points,
        source_event_indices=candidate_indices,
    ):
        return "protection_incompatible"

    return None


def _calculate_grouping_gap_sec(
    previous_point: VowelTimelinePoint,
    next_point: VowelTimelinePoint,
) -> float:
    previous_start_sec, previous_end_sec = _event_bounds(previous_point)
    next_start_sec, _ = _event_bounds(next_point)
    return max(0.0, next_start_sec - previous_end_sec)


def _event_frame_triplet(point: VowelTimelinePoint) -> tuple[int, int, int]:
    start_sec, end_sec = _event_bounds(point)
    return (
        _sec_to_frame(start_sec),
        _sec_to_frame(point.time_sec),
        _sec_to_frame(end_sec),
    )


def _is_frame_gap_or_rounding_viable(
    previous_point: VowelTimelinePoint,
    next_point: VowelTimelinePoint,
) -> bool:
    prev_start_frame, prev_center_frame, prev_end_frame = _event_frame_triplet(previous_point)
    next_start_frame, next_center_frame, next_end_frame = _event_frame_triplet(next_point)

    if next_center_frame <= prev_center_frame:
        return False
    if next_end_frame <= prev_end_frame:
        return False
    if next_start_frame < prev_start_frame:
        return False
    return True


def _is_lightweight_global_multi_point_candidate_viable(
    candidate_points: tuple[VowelTimelinePoint, ...],
) -> bool:
    if len(candidate_points) < 2:
        return True

    center_frames = [_event_frame_triplet(point)[1] for point in candidate_points]
    if len(set(center_frames)) < 2:
        return False

    first_start_frame, first_center_frame, _ = _event_frame_triplet(candidate_points[0])
    _, last_center_frame, last_end_frame = _event_frame_triplet(candidate_points[-1])
    if first_start_frame >= first_center_frame:
        return False
    if last_center_frame >= last_end_frame:
        return False

    return True


def _is_obviously_incompatible_with_group_protection_requirements(
    *,
    candidate_points: tuple[VowelTimelinePoint, ...],
    source_event_indices: tuple[int, ...],
) -> bool:
    if len(source_event_indices) != len(set(source_event_indices)):
        return True

    for point in candidate_points:
        start_frame, _, end_frame = _event_frame_triplet(point)
        if end_frame < start_frame:
            return True

    return False


def _build_multi_point_envelope_spec_from_group(
    grouped_events: GroupedNearbyVowelEvents,
) -> MultiPointEnvelopeBuildResult:
    start_zero_frame, end_zero_frame = _determine_group_envelope_boundary_frames(grouped_events)
    top_control_points = _build_top_control_points_for_group(grouped_events)
    if len(top_control_points) < 2:
        return MultiPointEnvelopeBuildResult(
            spec=None,
            failure_reason="insufficient_top_points",
        )

    valley_control_points = _build_valley_control_points_between_tops(top_control_points)
    if valley_control_points is None:
        return MultiPointEnvelopeBuildResult(
            spec=None,
            failure_reason="valley_generation_failed",
        )

    control_points = _build_multi_point_control_points(
        start_zero_frame=start_zero_frame,
        top_control_points=top_control_points,
        valley_control_points=valley_control_points,
        end_zero_frame=end_zero_frame,
    )
    local_failure = _check_multi_point_shape_local_collapse(control_points)
    if local_failure is not None:
        return MultiPointEnvelopeBuildResult(
            spec=None,
            failure_reason=local_failure,
        )

    spec = MultiPointEnvelopeSpec(
        vowel=grouped_events.vowel,
        control_points=control_points,
        source_event_indices=grouped_events.source_event_indices,
        protection_mode="envelope_range",
        event_ranges=grouped_events.event_ranges,
    )
    global_failure = _check_multi_point_shape_global_collapse(spec)
    if global_failure is not None:
        return MultiPointEnvelopeBuildResult(
            spec=None,
            failure_reason=global_failure,
        )

    return MultiPointEnvelopeBuildResult(spec=spec)


def _determine_group_envelope_boundary_frames(
    grouped_events: GroupedNearbyVowelEvents,
) -> tuple[int, int]:
    first_start_frame = _sec_to_frame(_event_bounds(grouped_events.points[0])[0])
    last_end_frame = _sec_to_frame(_event_bounds(grouped_events.points[-1])[1])
    return (first_start_frame, last_end_frame)


def _build_top_control_points_for_group(
    grouped_events: GroupedNearbyVowelEvents,
) -> tuple[EnvelopeControlPoint, ...]:
    return tuple(
        EnvelopeControlPoint(
            frame_no=_sec_to_frame(point.time_sec),
            value=_sanitize_top_peak_value(_point_peak_value(point)),
            point_kind="top",
        )
        for point in grouped_events.points
    )


def _sanitize_top_peak_value(peak_value: float) -> float:
    return max(float(peak_value), 0.0)


def _build_valley_control_points_between_tops(
    top_control_points: tuple[EnvelopeControlPoint, ...],
) -> tuple[EnvelopeControlPoint, ...] | None:
    valley_control_points: list[EnvelopeControlPoint] = []
    for left_top, right_top in zip(top_control_points, top_control_points[1:]):
        valley_frame = _determine_valley_frame(left_top, right_top)
        if valley_frame is None:
            return None
        valley_value = _compute_ms11_3_valley_value(left_top.value, right_top.value)
        if valley_value is None:
            return None
        valley_control_points.append(
            EnvelopeControlPoint(
                frame_no=valley_frame,
                value=valley_value,
                point_kind="valley",
            )
        )
    return tuple(valley_control_points)


def _determine_valley_frame(
    left_top: EnvelopeControlPoint,
    right_top: EnvelopeControlPoint,
) -> int | None:
    if right_top.frame_no <= left_top.frame_no + 1:
        return None
    midpoint_frame = (left_top.frame_no + right_top.frame_no) // 2
    if midpoint_frame <= left_top.frame_no:
        midpoint_frame = left_top.frame_no + 1
    if midpoint_frame >= right_top.frame_no:
        midpoint_frame = right_top.frame_no - 1
    if not (left_top.frame_no < midpoint_frame < right_top.frame_no):
        return None
    return midpoint_frame


def _compute_ms11_3_valley_value(
    left_peak_value: float,
    right_peak_value: float,
) -> float | None:
    normalized_left_peak = max(float(left_peak_value), 0.0)
    normalized_right_peak = max(float(right_peak_value), 0.0)
    lower_peak = min(normalized_left_peak, normalized_right_peak)
    lower_bound = 0.05
    upper_bound = lower_peak - 0.01
    if upper_bound <= lower_bound:
        return None
    valley_value = lower_peak * 0.35
    valley_value = max(lower_bound, valley_value)
    valley_value = min(upper_bound, valley_value)
    if valley_value <= 0.0:
        return None
    return valley_value


def _build_multi_point_control_points(
    *,
    start_zero_frame: int,
    top_control_points: tuple[EnvelopeControlPoint, ...],
    valley_control_points: tuple[EnvelopeControlPoint, ...],
    end_zero_frame: int,
) -> tuple[EnvelopeControlPoint, ...]:
    control_points: list[EnvelopeControlPoint] = [
        EnvelopeControlPoint(
            frame_no=start_zero_frame,
            value=0.0,
            point_kind="start_zero",
        )
    ]
    for index, top_control_point in enumerate(top_control_points):
        control_points.append(top_control_point)
        if index < len(valley_control_points):
            control_points.append(valley_control_points[index])
    control_points.append(
        EnvelopeControlPoint(
            frame_no=end_zero_frame,
            value=0.0,
            point_kind="end_zero",
        )
    )
    return tuple(control_points)


def _check_multi_point_shape_local_collapse(
    control_points: tuple[EnvelopeControlPoint, ...],
) -> str | None:
    for left_point, right_point in zip(control_points, control_points[1:]):
        if right_point.frame_no < left_point.frame_no:
            return "frame_order_reversed"
        if right_point.frame_no == left_point.frame_no:
            return "control_points_collapsed_to_same_frame"
        if left_point.point_kind in {"top", "valley"} and right_point.point_kind in {"top", "valley"}:
            if right_point.frame_no - left_point.frame_no <= 0:
                return "top_or_valley_width_zero"
    return None


def _check_multi_point_shape_global_collapse(
    spec: MultiPointEnvelopeSpec,
) -> str | None:
    if not _is_minimally_valid_multi_point_envelope_spec(spec):
        return "minimal_spec_invalid"

    point_kinds = tuple(point.point_kind for point in spec.control_points)
    top_control_points = tuple(
        point for point in spec.control_points
        if point.point_kind == "top"
    )
    valley_control_points = tuple(
        point for point in spec.control_points
        if point.point_kind == "valley"
    )
    if len(top_control_points) < 2:
        return "top_count_below_multi_point_threshold"
    if len(valley_control_points) != len(top_control_points) - 1:
        return "valley_count_mismatch"
    if point_kinds[0] != "start_zero" or point_kinds[-1] != "end_zero":
        return "missing_boundary_zeros"

    first_top_frame = top_control_points[0].frame_no
    last_top_frame = top_control_points[-1].frame_no
    if spec.start_frame >= first_top_frame:
        return "start_zero_not_before_first_top"
    if spec.end_frame <= last_top_frame:
        return "end_zero_not_after_last_top"
    if spec.end_frame - spec.start_frame < 3:
        return "insufficient_envelope_width"

    for valley_point, left_top, right_top in zip(
        valley_control_points,
        top_control_points,
        top_control_points[1:],
    ):
        if valley_point.value <= 0.0:
            return "valley_not_non_zero"
        if not (left_top.frame_no < valley_point.frame_no < right_top.frame_no):
            return "valley_not_between_adjacent_tops"

    return None


def _expand_multi_point_envelope_spec_to_morph_frames(
    spec: MultiPointEnvelopeSpec,
) -> MultiPointEnvelopeExpansionResult:
    order_failure = _validate_multi_point_control_point_order_for_expansion(spec.control_points)
    if order_failure is not None:
        return MultiPointEnvelopeExpansionResult(failure_reason=order_failure)

    collision_failure = _detect_multi_point_control_point_frame_collisions(spec.control_points)
    if collision_failure is not None:
        return MultiPointEnvelopeExpansionResult(failure_reason=collision_failure)

    frames = tuple(
        _convert_envelope_control_point_to_morph_frame(spec.vowel, point)
        for point in spec.control_points
    )
    frames = _prune_redundant_multi_point_morph_frames(frames)
    if not frames:
        return MultiPointEnvelopeExpansionResult(failure_reason="expansion_pruned_all_frames")

    frame_sequence_failure = _validate_expanded_multi_point_morph_frames(frames)
    if frame_sequence_failure is not None:
        return MultiPointEnvelopeExpansionResult(failure_reason=frame_sequence_failure)

    return MultiPointEnvelopeExpansionResult(frames=frames)


def _validate_multi_point_control_point_order_for_expansion(
    control_points: tuple[EnvelopeControlPoint, ...],
) -> str | None:
    if not control_points:
        return "control_points_empty"

    frame_numbers = [point.frame_no for point in control_points]
    if frame_numbers != sorted(frame_numbers):
        return "control_point_frame_order_invalid"

    if control_points[0].point_kind != "start_zero":
        return "missing_start_zero"
    if control_points[-1].point_kind != "end_zero":
        return "missing_end_zero"

    return None


def _detect_multi_point_control_point_frame_collisions(
    control_points: tuple[EnvelopeControlPoint, ...],
) -> str | None:
    for left_point, right_point in zip(control_points, control_points[1:]):
        if left_point.frame_no == right_point.frame_no:
            return f"control_point_frame_collision:{left_point.point_kind}:{right_point.point_kind}"
    return None


def _convert_envelope_control_point_to_morph_frame(
    vowel: str,
    point: EnvelopeControlPoint,
) -> MorphFrame:
    if point.point_kind in {"start_zero", "end_zero"}:
        return (point.frame_no, vowel, 0.0)
    return (point.frame_no, vowel, point.value)


def _prune_redundant_multi_point_morph_frames(
    frames: tuple[MorphFrame, ...],
) -> tuple[MorphFrame, ...]:
    if not frames:
        return ()

    pruned_frames: list[MorphFrame] = [frames[0]]
    for frame in frames[1:]:
        previous_frame = pruned_frames[-1]
        if frame[0] == previous_frame[0] and frame[2] == previous_frame[2]:
            continue
        pruned_frames.append(frame)
    return tuple(pruned_frames)


def _validate_expanded_multi_point_morph_frames(
    frames: tuple[MorphFrame, ...],
) -> str | None:
    if not frames:
        return "expanded_frames_empty"

    for left_frame, right_frame in zip(frames, frames[1:]):
        if right_frame[0] < left_frame[0]:
            return "expanded_frame_order_invalid"
        if right_frame[0] == left_frame[0]:
            return "expanded_frame_collision"

    first_frame_no, _, first_value = frames[0]
    last_frame_no, _, last_value = frames[-1]
    if first_value != 0.0:
        return "expanded_start_zero_missing"
    if last_value != 0.0:
        return "expanded_end_zero_missing"
    if last_frame_no <= first_frame_no:
        return "expanded_frame_span_invalid"

    return None


def write_morph_vmd(
    output_path: str | Path,
    timeline: Iterable[
        VowelTimelinePoint
        | tuple[float, str]
        | tuple[float, str, float]
        | tuple[float, str, float, float]
        | tuple[float, str, float, float, float, float]
    ],
    model_name: str = "AutoLipTool",
    *,
    apply_final_normalization: bool = True,
    closing_softness_frames: int = 0,
) -> Path:
    normalized_closing_softness_frames = _normalize_closing_softness_frames(
        closing_softness_frames
    )
    points = _normalize_timeline(timeline)
    morph_frames, normalization_metadata = _build_interval_morph_frames_with_normalization_metadata(
        points,
        closing_softness_frames=normalized_closing_softness_frames,
    )
    if apply_final_normalization:
        morph_frames = _apply_final_morph_frame_normalization(
            morph_frames,
            protected_ms11_2_specs=list(normalization_metadata.protected_ms11_2_specs),
            protected_event_ranges=normalization_metadata.protected_envelope_ranges,
            allowed_non_zero_ranges=normalization_metadata.allowed_non_zero_ranges,
            required_zero_frames=normalization_metadata.required_zero_frames,
        )
    if len(morph_frames) > MAX_MORPH_FRAMES:
        raise ValueError(f"Generated morph frames ({len(morph_frames)}) exceed the maximum limit of {MAX_MORPH_FRAMES}.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("wb") as fp:
        fp.write(_pad_bytes(_VMD_HEADER, 30))
        fp.write(_encode_shift_jis_fixed(model_name, 20))

        # Bone keyframe count: 0 (this writer outputs morph frames only).
        fp.write(struct.pack("<I", 0))

        fp.write(struct.pack("<I", len(morph_frames)))
        for frame_no, vowel, value in morph_frames:
            fp.write(_encode_shift_jis_fixed(vowel, 15))
            fp.write(struct.pack("<I", frame_no))
            fp.write(struct.pack("<f", _finalize_morph_value(value)))

        # Camera / Light / Self-shadow / IK keyframe counts: all 0.
        fp.write(struct.pack("<I", 0))
        fp.write(struct.pack("<I", 0))
        fp.write(struct.pack("<I", 0))
        fp.write(struct.pack("<I", 0))

    return output


def write_dummy_morph_vmd(output_path: str | Path, model_name: str = "AutoLipTool") -> Path:
    dummy_timeline = [
        VowelTimelinePoint(0.0, "\u3042"),
        VowelTimelinePoint(0.10, "\u3044"),
        VowelTimelinePoint(0.20, "\u3046"),
        VowelTimelinePoint(0.30, "\u3048"),
        VowelTimelinePoint(0.40, "\u304a"),
    ]
    return write_morph_vmd(
        output_path=output_path,
        timeline=dummy_timeline,
        model_name=model_name,
        apply_final_normalization=False,
    )


def _normalize_timeline(
    timeline: Iterable[
        VowelTimelinePoint
        | tuple[float, str]
        | tuple[float, str, float]
        | tuple[float, str, float, float]
        | tuple[float, str, float, float, float, float]
    ],
) -> list[VowelTimelinePoint]:
    normalized: list[VowelTimelinePoint] = []
    for raw_point in timeline:
        if isinstance(raw_point, VowelTimelinePoint):
            point = raw_point
        elif len(raw_point) == 2:
            time_sec, vowel = raw_point
            point = VowelTimelinePoint(time_sec=float(time_sec), vowel=vowel)
        elif len(raw_point) == 3:
            time_sec, vowel, value = raw_point
            point = VowelTimelinePoint(time_sec=float(time_sec), vowel=vowel, value=float(value))
        elif len(raw_point) == 4:
            time_sec, vowel, value, duration_sec = raw_point
            point = VowelTimelinePoint(
                time_sec=float(time_sec),
                vowel=vowel,
                value=float(value),
                duration_sec=float(duration_sec),
            )
        elif len(raw_point) == 6:
            time_sec, vowel, value, duration_sec, start_sec, end_sec = raw_point
            point = VowelTimelinePoint(
                time_sec=float(time_sec),
                vowel=vowel,
                value=float(value),
                duration_sec=float(duration_sec),
                start_sec=float(start_sec),
                end_sec=float(end_sec),
            )
        else:
            raise ValueError(
                "Timeline point must be VowelTimelinePoint or tuple(time_sec, vowel[, value[, duration_sec[, start_sec, end_sec]]])."
            )

        if point.vowel not in SUPPORTED_MORPHS:
            raise ValueError(f"Unsupported vowel morph: {point.vowel}")
        if point.time_sec < 0:
            raise ValueError("time_sec must be >= 0")
        point_peak_value = _point_peak_value(point)
        if point_peak_value < 0:
            raise ValueError("peak_value must be >= 0")
        if point.duration_sec < 0:
            raise ValueError("duration_sec must be >= 0")
        if point.start_sec > point.end_sec:
            raise ValueError("start_sec must be <= end_sec")
        if not (point.start_sec <= point.time_sec <= point.end_sec):
            raise ValueError("time_sec must be inside [start_sec, end_sec]")

        clamped_value = point_peak_value
        normalized.append(
            VowelTimelinePoint(
                time_sec=point.time_sec,
                vowel=point.vowel,
                value=clamped_value,
                peak_value=clamped_value,
                duration_sec=point.duration_sec,
                start_sec=point.start_sec,
                end_sec=point.end_sec,
            )
        )

    normalized.sort(key=lambda x: x.time_sec)
    return normalized


def _build_peak_morph_frames(
    points: list[VowelTimelinePoint],
    *,
    closing_softness_frames: int = 0,
    next_shape_start_frame: int | None = None,
) -> list[MorphFrame]:
    del closing_softness_frames
    del next_shape_start_frame
    expanded: list[MorphFrame] = []
    for point in points:
        peak_value = _point_peak_value(point)
        center_frame = _sec_to_frame(point.time_sec)
        before_frame = max(0, center_frame - PEAK_SIDE_FRAME_OFFSET)
        after_frame = center_frame + PEAK_SIDE_FRAME_OFFSET

        expanded.append((before_frame, point.vowel, 0.0))
        expanded.append((center_frame, point.vowel, peak_value))
        expanded.append((after_frame, point.vowel, 0.0))

    expanded.sort(key=lambda x: x[0])
    return expanded


def _build_interval_morph_frames(
    points: list[VowelTimelinePoint],
    *,
    closing_softness_frames: int = 0,
) -> list[MorphFrame]:
    expanded, _ = _build_interval_morph_frames_with_metadata(
        points,
        closing_softness_frames=closing_softness_frames,
    )
    return expanded


def _build_interval_morph_frames_with_metadata(
    points: list[VowelTimelinePoint],
    *,
    closing_softness_frames: int = 0,
) -> tuple[list[MorphFrame], list[AsymmetricTrapezoidSpec]]:
    expanded, normalization_metadata = _build_interval_morph_frames_with_normalization_metadata(
        points,
        closing_softness_frames=closing_softness_frames,
    )
    return expanded, list(normalization_metadata.protected_ms11_2_specs)


def _build_interval_morph_frames_with_normalization_metadata(
    points: list[VowelTimelinePoint],
    *,
    closing_softness_frames: int = 0,
) -> tuple[list[MorphFrame], FinalNormalizationMetadata]:
    normalized_closing_softness_frames = _normalize_closing_softness_frames(
        closing_softness_frames
    )
    expanded_with_flags: list[_MorphFrameWithFlags] = []
    protected_ms11_2_specs: list[AsymmetricTrapezoidSpec] = []
    protected_envelope_ranges: dict[str, list[tuple[int, int]]] = {}
    allowed_non_zero_ranges: dict[str, list[tuple[int, int]]] = {}
    grouped_events = _group_nearby_same_vowel_events(points)
    for grouped_event_index, grouped_event in enumerate(grouped_events):
        next_shape_start_frame = _next_group_start_frame(
            grouped_events,
            grouped_event_index,
        )
        ms11_3_result = _build_ms11_3_group_morph_frames_with_spec(
            grouped_event,
            closing_softness_frames=normalized_closing_softness_frames,
            next_shape_start_frame=next_shape_start_frame,
        )
        if ms11_3_result is not None:
            ms11_3_frames_with_flags, ms11_3_spec = ms11_3_result
            expanded_with_flags.extend(ms11_3_frames_with_flags)
            if _is_protectable_ms11_3_spec(ms11_3_spec):
                _append_frame_range(
                    protected_envelope_ranges,
                    ms11_3_spec.vowel,
                    ms11_3_spec.start_frame,
                    ms11_3_spec.end_frame,
                )
            _append_frame_range(
                allowed_non_zero_ranges,
                ms11_3_spec.vowel,
                ms11_3_spec.start_frame,
                ms11_3_spec.end_frame,
            )
            continue

        (
            fallback_frames_with_flags,
            fallback_protected_specs,
            fallback_protected_ranges,
            fallback_allowed_ranges,
        ) = _build_existing_group_morph_frames_with_metadata(
            grouped_event,
            closing_softness_frames=normalized_closing_softness_frames,
            next_group_start_frame=next_shape_start_frame,
        )
        expanded_with_flags.extend(fallback_frames_with_flags)
        protected_ms11_2_specs.extend(fallback_protected_specs)
        for vowel, start_frame, end_frame in fallback_protected_ranges:
            _append_frame_range(
                protected_envelope_ranges,
                vowel,
                start_frame,
                end_frame,
            )
        for vowel, start_frame, end_frame in fallback_allowed_ranges:
            _append_frame_range(
                allowed_non_zero_ranges,
                vowel,
                start_frame,
                end_frame,
            )

    _append_protected_ms11_2_envelope_ranges(
        protected_envelope_ranges,
        protected_ms11_2_specs,
    )

    expanded_with_flags = _shift_conflicting_rise_start_zeros(expanded_with_flags)
    required_zero_frames = _build_required_zero_frames_from_expanded_with_flags(expanded_with_flags)
    expanded = [(frame_no, vowel, value) for frame_no, vowel, value, _ in expanded_with_flags]

    expanded.sort(key=lambda x: x[0])
    return expanded, FinalNormalizationMetadata(
        protected_ms11_2_specs=tuple(protected_ms11_2_specs),
        protected_envelope_ranges=protected_envelope_ranges,
        allowed_non_zero_ranges=allowed_non_zero_ranges,
        required_zero_frames=required_zero_frames,
    )


def _build_ms11_3_group_morph_frames_with_flags(
    grouped_events: GroupedNearbyVowelEvents,
    *,
    closing_softness_frames: int = 0,
    next_shape_start_frame: int | None = None,
) -> list[_MorphFrameWithFlags] | None:
    result = _build_ms11_3_group_morph_frames_with_spec(
        grouped_events,
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    if result is None:
        return None
    return result[0]


def _build_ms11_3_group_morph_frames_with_spec(
    grouped_events: GroupedNearbyVowelEvents,
    *,
    closing_softness_frames: int = 0,
    next_shape_start_frame: int | None = None,
) -> tuple[list[_MorphFrameWithFlags], MultiPointEnvelopeSpec] | None:
    if not _is_ms11_3_attemptable_group(grouped_events):
        return None

    build_result = _build_multi_point_envelope_spec_from_group(grouped_events)
    if not build_result.is_valid or build_result.spec is None:
        return None

    softened_spec = _apply_closing_softness_to_multi_point_envelope_spec(
        build_result.spec,
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )

    expansion_result = _expand_multi_point_envelope_spec_to_morph_frames(softened_spec)
    if not expansion_result.is_valid:
        return None

    adoption_failure = _validate_ms11_3_shape_adoption(
        softened_spec,
        expansion_result.frames,
    )
    if adoption_failure is not None:
        return None

    return _convert_multi_point_frames_to_flagged_frames(expansion_result.frames), softened_spec


def _is_ms11_3_attemptable_group(
    grouped_events: GroupedNearbyVowelEvents,
) -> bool:
    if len(grouped_events.points) < 2:
        return False

    for source_event_index, point in zip(grouped_events.source_event_indices, grouped_events.points):
        spec = _build_interval_trapezoid_spec(
            point,
            source_event_index=source_event_index,
        )
        if spec is None:
            return False
        if spec.shape_kind != "ms11_2_asymmetric_trapezoid":
            return False

    return True


def _validate_ms11_3_shape_adoption(
    spec: MultiPointEnvelopeSpec,
    frames: tuple[MorphFrame, ...],
) -> str | None:
    if not _is_minimally_valid_multi_point_envelope_spec(spec):
        return "minimal_spec_invalid"

    top_control_points = tuple(
        point for point in spec.control_points
        if point.point_kind == "top"
    )
    valley_control_points = tuple(
        point for point in spec.control_points
        if point.point_kind == "valley"
    )
    if len(top_control_points) < 2:
        return "top_count_below_multi_point_threshold"
    if len(valley_control_points) != len(top_control_points) - 1:
        return "valley_count_mismatch"

    frame_validation_failure = _validate_expanded_multi_point_morph_frames(frames)
    if frame_validation_failure is not None:
        return frame_validation_failure

    frame_numbers = [frame_no for frame_no, _, _ in frames]
    if len(frame_numbers) != len(set(frame_numbers)):
        return "expanded_frame_collision"
    if frames[0][2] != 0.0:
        return "expanded_start_zero_missing"
    if frames[-1][2] != 0.0:
        return "expanded_end_zero_missing"
    if frames[-1][0] - frames[0][0] < 3:
        return "insufficient_envelope_width"

    for valley_point in valley_control_points:
        if valley_point.value <= 0.0:
            return "valley_not_non_zero"

    return None


def _is_protectable_ms11_3_spec(spec: MultiPointEnvelopeSpec) -> bool:
    return (
        spec.is_ms11_3_generated
        and spec.shape_kind == "ms11_3_multi_point_envelope"
        and _check_multi_point_shape_global_collapse(spec) is None
    )


def _convert_multi_point_frames_to_flagged_frames(
    frames: tuple[MorphFrame, ...],
) -> list[_MorphFrameWithFlags]:
    flagged_frames: list[_MorphFrameWithFlags] = []
    for index, (frame_no, vowel, value) in enumerate(frames):
        is_rise_start_zero = index == 0 and value == 0.0
        flagged_frames.append((frame_no, vowel, value, is_rise_start_zero))
    return flagged_frames


def _append_frame_range(
    frame_ranges_by_vowel: dict[str, list[tuple[int, int]]],
    vowel: str,
    start_frame: int,
    end_frame: int,
) -> None:
    frame_ranges_by_vowel.setdefault(vowel, []).append(
        _normalize_frame_range(start_frame, end_frame)
    )


def _append_group_allowed_non_zero_ranges(
    allowed_non_zero_ranges: dict[str, list[tuple[int, int]]],
    grouped_events: GroupedNearbyVowelEvents,
) -> None:
    for point in grouped_events.points:
        start_sec, end_sec = _event_bounds(point)
        _append_frame_range(
            allowed_non_zero_ranges,
            point.vowel,
            _sec_to_frame(start_sec),
            _sec_to_frame(end_sec),
        )


def _append_protected_ms11_2_envelope_ranges(
    protected_envelope_ranges: dict[str, list[tuple[int, int]]],
    protected_ms11_2_specs: list[AsymmetricTrapezoidSpec],
) -> None:
    for spec in protected_ms11_2_specs:
        _append_frame_range(
            protected_envelope_ranges,
            spec.vowel,
            spec.start_frame,
            spec.end_frame,
        )


def _build_required_zero_frames_from_expanded_with_flags(
    expanded_with_flags: list[_MorphFrameWithFlags],
) -> dict[str, set[int]]:
    required_zero_frames: dict[str, set[int]] = {}
    for frame_no, vowel, value, _ in expanded_with_flags:
        if value <= MORPH_FRAME_OPEN_EPSILON:
            required_zero_frames.setdefault(vowel, set()).add(frame_no)
    return required_zero_frames


def _build_existing_group_morph_frames_with_metadata(
    grouped_events: GroupedNearbyVowelEvents,
    *,
    closing_softness_frames: int = 0,
    next_group_start_frame: int | None = None,
) -> tuple[
    list[_MorphFrameWithFlags],
    list[AsymmetricTrapezoidSpec],
    list[tuple[str, int, int]],
    list[tuple[str, int, int]],
]:
    expanded_with_flags: list[_MorphFrameWithFlags] = []
    protected_ms11_2_specs: list[AsymmetricTrapezoidSpec] = []
    protected_fallback_ranges: list[tuple[str, int, int]] = []
    allowed_ranges: list[tuple[str, int, int]] = []

    point_count = len(grouped_events.points)
    for point_index, (source_event_index, point) in enumerate(
        zip(grouped_events.source_event_indices, grouped_events.points)
    ):
        next_shape_start_frame = next_group_start_frame
        if point_index + 1 < point_count:
            next_shape_start_frame = _event_start_frame(grouped_events.points[point_index + 1])
        (
            point_frames_with_flags,
            protected_spec,
            protected_range,
        ) = _build_existing_point_morph_frames_with_metadata(
            point,
            source_event_index=source_event_index,
            closing_softness_frames=closing_softness_frames,
            next_shape_start_frame=next_shape_start_frame,
        )
        expanded_with_flags.extend(point_frames_with_flags)
        if protected_spec is not None:
            protected_ms11_2_specs.append(protected_spec)
            allowed_ranges.append(
                (protected_spec.vowel, protected_spec.start_frame, protected_spec.end_frame)
            )
        if protected_range is not None:
            protected_fallback_ranges.append((point.vowel, protected_range[0], protected_range[1]))
            allowed_ranges.append((point.vowel, protected_range[0], protected_range[1]))

    return expanded_with_flags, protected_ms11_2_specs, protected_fallback_ranges, allowed_ranges


def _build_existing_point_morph_frames_with_metadata(
    point: VowelTimelinePoint,
    *,
    source_event_index: int | None = None,
    closing_softness_frames: int = 0,
    next_shape_start_frame: int | None = None,
) -> tuple[
    list[_MorphFrameWithFlags],
    AsymmetricTrapezoidSpec | None,
    tuple[int, int] | None,
]:
    if _point_peak_value(point) <= MORPH_FRAME_OPEN_EPSILON:
        return [], None, None

    spec = _build_interval_trapezoid_spec(
        point,
        source_event_index=source_event_index,
    )
    if spec is None:
        fallback_frames_with_flags = [
            (frame_no, vowel, value, False)
            for frame_no, vowel, value in _build_peak_morph_frames(
                [point],
                closing_softness_frames=closing_softness_frames,
                next_shape_start_frame=next_shape_start_frame,
            )
        ]
        return (
            fallback_frames_with_flags,
            None,
            _fallback_frame_range_from_expanded_with_flags(fallback_frames_with_flags),
        )

    spec = _apply_closing_softness_to_trapezoid_spec(
        spec,
        closing_softness_frames=closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    protected_spec = spec if _is_protectable_ms11_2_spec(spec) else None
    expanded_frames_with_flags = _expand_trapezoid_spec_to_morph_frames(spec)
    protected_range = None
    if protected_spec is None:
        protected_range = _fallback_frame_range_from_expanded_with_flags(expanded_frames_with_flags)
    return expanded_frames_with_flags, protected_spec, protected_range


def _build_interval_trapezoid_spec(
    point: VowelTimelinePoint,
    *,
    source_event_index: int | None = None,
) -> AsymmetricTrapezoidSpec | None:
    peak_value = _point_peak_value(point)
    if peak_value <= MORPH_FRAME_OPEN_EPSILON:
        return None

    start_sec, end_sec = _event_bounds(point)
    center_frame = _sec_to_frame(point.time_sec)
    start_frame = _sec_to_frame(start_sec)
    end_frame = _sec_to_frame(end_sec)
    total_span_frames = end_frame - start_frame
    left_available_frames = center_frame - start_frame
    right_available_frames = end_frame - center_frame

    if not _should_use_ms11_2_trapezoid(total_span_frames):
        return _build_short_interval_fallback_spec(
            point=point,
            peak_value=peak_value,
            start_frame=start_frame,
            center_frame=center_frame,
            end_frame=end_frame,
            source_event_index=source_event_index,
        )

    # MS11-2 treats time_sec as the midpoint of the top edge after frame rounding.
    # We keep at least one frame on both shoulders and require a non-zero top width.
    max_centered_half_width = min(
        left_available_frames - 1,
        right_available_frames - 1,
    )
    if max_centered_half_width < 1:
        return _build_legacy_interval_trapezoid_spec(
            point=point,
            peak_value=peak_value,
            start_frame=start_frame,
            center_frame=center_frame,
            end_frame=end_frame,
            source_event_index=source_event_index,
        )

    relative_top_half_width = min(left_available_frames, right_available_frames) // 2
    top_half_width = max(1, min(relative_top_half_width, max_centered_half_width))

    peak_start_frame = center_frame - top_half_width
    peak_end_frame = center_frame + top_half_width

    if not (start_frame < peak_start_frame <= peak_end_frame < end_frame):
        return _build_legacy_interval_trapezoid_spec(
            point=point,
            peak_value=peak_value,
            start_frame=start_frame,
            center_frame=center_frame,
            end_frame=end_frame,
            source_event_index=source_event_index,
        )

    return AsymmetricTrapezoidSpec(
        vowel=point.vowel,
        start_frame=start_frame,
        peak_start_frame=peak_start_frame,
        peak_end_frame=peak_end_frame,
        end_frame=end_frame,
        peak_value=peak_value,
        source_event_index=source_event_index,
        shape_kind="ms11_2_asymmetric_trapezoid",
    )


def _should_use_ms11_2_trapezoid(total_span_frames: int) -> bool:
    return total_span_frames >= 4


def _build_short_interval_fallback_spec(
    *,
    point: VowelTimelinePoint,
    peak_value: float,
    start_frame: int,
    center_frame: int,
    end_frame: int,
    source_event_index: int | None = None,
) -> AsymmetricTrapezoidSpec | None:
    return _build_legacy_interval_trapezoid_spec(
        point=point,
        peak_value=peak_value,
        start_frame=start_frame,
        center_frame=center_frame,
        end_frame=end_frame,
        source_event_index=source_event_index,
    )


def _build_legacy_interval_trapezoid_spec(
    *,
    point: VowelTimelinePoint,
    peak_value: float,
    start_frame: int,
    center_frame: int,
    end_frame: int,
    source_event_index: int | None = None,
) -> AsymmetricTrapezoidSpec | None:
    if end_frame <= start_frame:
        return None

    rise_end_frame = min(center_frame, start_frame + PEAK_SIDE_FRAME_OFFSET)
    fall_start_frame = max(center_frame, end_frame - PEAK_SIDE_FRAME_OFFSET)

    if fall_start_frame <= rise_end_frame:
        peak_frame = center_frame
        if peak_frame <= start_frame:
            peak_frame = min(start_frame + 1, end_frame)
        if peak_frame >= end_frame:
            peak_frame = max(end_frame - 1, start_frame)

        if peak_frame <= start_frame or peak_frame >= end_frame:
            return None

        return AsymmetricTrapezoidSpec(
            vowel=point.vowel,
            start_frame=start_frame,
            peak_start_frame=peak_frame,
            peak_end_frame=peak_frame,
            end_frame=end_frame,
            peak_value=peak_value,
            source_event_index=source_event_index,
            shape_kind="legacy_triangle",
        )

    return AsymmetricTrapezoidSpec(
        vowel=point.vowel,
        start_frame=start_frame,
        peak_start_frame=rise_end_frame,
        peak_end_frame=fall_start_frame,
        end_frame=end_frame,
        peak_value=peak_value,
        source_event_index=source_event_index,
        shape_kind="legacy_symmetric_trapezoid",
    )


def _expand_trapezoid_spec_to_morph_frames(
    spec: AsymmetricTrapezoidSpec,
) -> list[_MorphFrameWithFlags]:
    if spec.shape_kind == "legacy_triangle":
        return [
            (spec.start_frame, spec.vowel, 0.0, True),
            (spec.peak_start_frame, spec.vowel, spec.peak_value, False),
            (spec.end_frame, spec.vowel, 0.0, False),
        ]

    if spec.shape_kind == "legacy_symmetric_trapezoid":
        return [
            (spec.start_frame, spec.vowel, 0.0, True),
            (spec.peak_start_frame, spec.vowel, spec.peak_value, False),
            (spec.peak_end_frame, spec.vowel, spec.peak_value, False),
            (spec.end_frame, spec.vowel, 0.0, False),
        ]

    if _is_expandable_four_point_trapezoid_spec(spec):
        return [
            (spec.start_frame, spec.vowel, 0.0, True),
            (spec.peak_start_frame, spec.vowel, spec.peak_value, False),
            (spec.peak_end_frame, spec.vowel, spec.peak_value, False),
            (spec.end_frame, spec.vowel, 0.0, False),
        ]

    safe_peak_frame = min(
        max(spec.start_frame + 1, min(spec.peak_start_frame, spec.peak_end_frame)),
        spec.end_frame - 1,
    )
    if spec.start_frame < safe_peak_frame < spec.end_frame:
        return [
            (spec.start_frame, spec.vowel, 0.0, True),
            (safe_peak_frame, spec.vowel, spec.peak_value, False),
            (spec.end_frame, spec.vowel, 0.0, False),
        ]

    return [
        (spec.start_frame, spec.vowel, 0.0, True),
        (spec.end_frame, spec.vowel, 0.0, False),
    ]


def _normalize_closing_softness_frames(closing_softness_frames: int) -> int:
    normalized_closing_softness_frames = int(closing_softness_frames)
    if normalized_closing_softness_frames < 0:
        raise ValueError("closing_softness_frames must be >= 0")
    return normalized_closing_softness_frames


def _event_start_frame(point: VowelTimelinePoint) -> int:
    start_sec, _ = _event_bounds(point)
    return _sec_to_frame(start_sec)


def _next_group_start_frame(
    grouped_events: list[GroupedNearbyVowelEvents],
    current_group_index: int,
) -> int | None:
    next_group_index = current_group_index + 1
    if next_group_index >= len(grouped_events):
        return None
    return _event_start_frame(grouped_events[next_group_index].points[0])


def _resolve_softened_end_frame(
    *,
    fall_start_frame: int,
    end_frame: int,
    closing_softness_frames: int,
    next_shape_start_frame: int | None = None,
) -> int:
    if closing_softness_frames <= 0:
        return end_frame

    softened_end_frame = end_frame + closing_softness_frames
    if next_shape_start_frame is not None:
        softened_end_frame = min(softened_end_frame, next_shape_start_frame - 1)
    return max(end_frame, max(fall_start_frame + 1, softened_end_frame))


def _apply_closing_softness_to_trapezoid_spec(
    spec: AsymmetricTrapezoidSpec,
    *,
    closing_softness_frames: int,
    next_shape_start_frame: int | None = None,
) -> AsymmetricTrapezoidSpec:
    normalized_closing_softness_frames = _normalize_closing_softness_frames(
        closing_softness_frames
    )
    if normalized_closing_softness_frames == 0:
        return spec

    softened_end_frame = _resolve_softened_end_frame(
        fall_start_frame=spec.peak_end_frame,
        end_frame=spec.end_frame,
        closing_softness_frames=normalized_closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    if softened_end_frame == spec.end_frame:
        return spec

    return AsymmetricTrapezoidSpec(
        vowel=spec.vowel,
        start_frame=spec.start_frame,
        peak_start_frame=spec.peak_start_frame,
        peak_end_frame=spec.peak_end_frame,
        end_frame=softened_end_frame,
        peak_value=spec.peak_value,
        source_event_index=spec.source_event_index,
        is_ms11_2_generated=spec.is_ms11_2_generated,
        shape_kind=spec.shape_kind,
        protection_mode=spec.protection_mode,
    )


def _apply_closing_softness_to_multi_point_envelope_spec(
    spec: MultiPointEnvelopeSpec,
    *,
    closing_softness_frames: int,
    next_shape_start_frame: int | None = None,
) -> MultiPointEnvelopeSpec:
    normalized_closing_softness_frames = _normalize_closing_softness_frames(
        closing_softness_frames
    )
    if normalized_closing_softness_frames == 0:
        return spec
    if len(spec.control_points) < 2:
        return spec

    final_non_zero_point = spec.control_points[-2]
    final_end_zero_point = spec.control_points[-1]
    softened_end_frame = _resolve_softened_end_frame(
        fall_start_frame=final_non_zero_point.frame_no,
        end_frame=final_end_zero_point.frame_no,
        closing_softness_frames=normalized_closing_softness_frames,
        next_shape_start_frame=next_shape_start_frame,
    )
    if softened_end_frame == final_end_zero_point.frame_no:
        return spec

    softened_control_points = list(spec.control_points)
    softened_control_points[-1] = EnvelopeControlPoint(
        frame_no=softened_end_frame,
        value=final_end_zero_point.value,
        point_kind=final_end_zero_point.point_kind,
    )
    return MultiPointEnvelopeSpec(
        vowel=spec.vowel,
        control_points=tuple(softened_control_points),
        source_event_indices=spec.source_event_indices,
        shape_kind=spec.shape_kind,
        protection_mode=spec.protection_mode,
        is_ms11_3_generated=spec.is_ms11_3_generated,
        event_ranges=spec.event_ranges,
    )


def _is_expandable_four_point_trapezoid_spec(
    spec: AsymmetricTrapezoidSpec,
) -> bool:
    return (
        spec.start_frame < spec.peak_start_frame
        and spec.peak_start_frame <= spec.peak_end_frame
        and spec.peak_end_frame < spec.end_frame
    )


def _is_protectable_ms11_2_spec(spec: AsymmetricTrapezoidSpec) -> bool:
    return spec.is_ms11_2_generated and spec.shape_kind == "ms11_2_asymmetric_trapezoid"


def _fallback_frame_range_from_expanded_with_flags(
    frames: list[_MorphFrameWithFlags],
) -> tuple[int, int] | None:
    if not frames:
        return None
    if not any(value > MORPH_FRAME_OPEN_EPSILON for _, _, value, _ in frames):
        return None

    frame_numbers = [frame_no for frame_no, _, _, _ in frames]
    return _normalize_frame_range(min(frame_numbers), max(frame_numbers))


def _apply_final_morph_frame_normalization(
    frames: list[MorphFrame],
    *,
    protected_ms11_2_specs: list[AsymmetricTrapezoidSpec] | None = None,
    protected_event_ranges: dict[str, list[tuple[int, int]]] | None = None,
    allowed_non_zero_ranges: dict[str, list[tuple[int, int]]] | None = None,
    required_zero_frames: dict[str, set[int]] | None = None,
) -> list[MorphFrame]:
    # MS11-1 processing order:
    # 1. generate morph frames
    # 2. apply existing same-frame collision handling
    # 3. merge duplicate (morph_name, frame_no) keys
    # 4. build mouth-open state across all vowels
    # 5. normalize isolated short open segments
    # 6. optionally normalize per-morph short pulses
    # 7. final sort before writing
    normalized_frames = _merge_duplicate_morph_frames(frames)
    active_protected_specs = _filter_active_ms11_2_protected_specs(
        normalized_frames,
        protected_ms11_2_specs,
    )
    open_state = _build_morph_frame_open_state(normalized_frames)
    normalized_frames = _normalize_isolated_short_open_segments(
        normalized_frames,
        open_state,
        active_protected_specs=active_protected_specs,
        protected_event_ranges=protected_event_ranges,
    )
    active_protected_specs = _filter_active_ms11_2_protected_specs(
        normalized_frames,
        protected_ms11_2_specs,
    )
    open_state = _build_morph_frame_open_state(normalized_frames)
    normalized_frames = _normalize_short_morph_pulses(
        normalized_frames,
        open_state,
        active_protected_specs=active_protected_specs,
        protected_event_ranges=protected_event_ranges,
    )
    normalized_frames = _remove_non_zero_outside_allowed_ranges(
        normalized_frames,
        allowed_non_zero_ranges=allowed_non_zero_ranges,
    )
    normalized_frames = _prune_redundant_zero_morph_frames(
        normalized_frames,
        required_zero_frames=required_zero_frames,
    )
    normalized_frames = _merge_duplicate_morph_frames(normalized_frames)
    return _sort_morph_frames(normalized_frames)


def _merge_duplicate_morph_frames(frames: list[MorphFrame]) -> list[MorphFrame]:
    merged_by_key: dict[tuple[str, int], float] = {}
    for frame_no, vowel, value in frames:
        key = (vowel, frame_no)
        existing_value = merged_by_key.get(key)
        if existing_value is None:
            merged_by_key[key] = value
            continue

        if value > 0.0:
            if existing_value > 0.0:
                merged_by_key[key] = max(existing_value, value)
            else:
                merged_by_key[key] = value
            continue

        if existing_value > 0.0:
            continue

        merged_by_key[key] = 0.0

    return [
        (frame_no, vowel, merged_value)
        for (vowel, frame_no), merged_value in merged_by_key.items()
    ]


def _build_morph_frame_open_state(frames: list[MorphFrame]) -> MorphFrameOpenState:
    frame_values: dict[int, dict[str, float]] = {}
    open_values: dict[int, float] = {}
    for frame_no, vowel, value in frames:
        per_vowel_values = frame_values.setdefault(
            frame_no,
            _empty_morph_frame_values(),
        )
        per_vowel_values[vowel] = value
        open_values[frame_no] = max(per_vowel_values.values())
    return MorphFrameOpenState(
        frame_values=frame_values,
        open_values=open_values,
        epsilon=MORPH_FRAME_OPEN_EPSILON,
    )


def _filter_active_ms11_2_protected_specs(
    frames: list[MorphFrame],
    protected_specs: list[AsymmetricTrapezoidSpec] | None,
) -> list[AsymmetricTrapezoidSpec]:
    if not protected_specs:
        return []

    frame_lookup = {(vowel, frame_no): value for frame_no, vowel, value in frames}
    active_specs: list[AsymmetricTrapezoidSpec] = []
    for spec in protected_specs:
        if not _is_protectable_ms11_2_spec(spec):
            continue
        if not _is_expandable_four_point_trapezoid_spec(spec):
            continue

        start_value = frame_lookup.get((spec.vowel, spec.start_frame))
        peak_start_value = frame_lookup.get((spec.vowel, spec.peak_start_frame))
        peak_end_value = frame_lookup.get((spec.vowel, spec.peak_end_frame))
        end_value = frame_lookup.get((spec.vowel, spec.end_frame))

        if start_value is None or end_value is None:
            continue
        if start_value > MORPH_FRAME_OPEN_EPSILON:
            continue
        if end_value > MORPH_FRAME_OPEN_EPSILON:
            continue
        if peak_start_value is None or peak_start_value <= MORPH_FRAME_OPEN_EPSILON:
            continue
        if peak_end_value is None or peak_end_value <= MORPH_FRAME_OPEN_EPSILON:
            continue

        active_specs.append(spec)
    return active_specs


def _normalize_isolated_short_open_segments(
    frames: list[MorphFrame],
    open_state: MorphFrameOpenState,
    *,
    active_protected_specs: list[AsymmetricTrapezoidSpec] | None = None,
    protected_event_ranges: dict[str, list[tuple[int, int]]] | None = None,
) -> list[MorphFrame]:
    candidates = _detect_isolated_short_open_candidates(open_state)
    if not candidates:
        return list(frames)
    return _suppress_isolated_short_open_candidates(
        frames,
        candidates,
        active_protected_specs=active_protected_specs,
        protected_event_ranges=protected_event_ranges,
    )


def _normalize_short_morph_pulses(
    frames: list[MorphFrame],
    open_state: MorphFrameOpenState,
    *,
    active_protected_specs: list[AsymmetricTrapezoidSpec] | None = None,
    protected_event_ranges: dict[str, list[tuple[int, int]]] | None = None,
) -> list[MorphFrame]:
    candidates = _detect_short_morph_pulse_candidates(open_state)
    if not candidates:
        return list(frames)
    return _suppress_short_morph_pulse_candidates(
        frames,
        candidates,
        active_protected_specs=active_protected_specs,
        protected_event_ranges=protected_event_ranges,
    )


def _sort_morph_frames(frames: list[MorphFrame]) -> list[MorphFrame]:
    return sorted(frames, key=lambda frame: (frame[0], frame[1], frame[2]))


def _empty_morph_frame_values() -> dict[str, float]:
    return {morph_name: 0.0 for morph_name in SUPPORTED_MORPHS}


def _extract_mouth_open_intervals(open_state: MorphFrameOpenState) -> list[MouthOpenInterval]:
    if not open_state.open_values:
        return []

    frames = sorted(open_state.open_values)
    intervals: list[MouthOpenInterval] = []
    interval_start = frames[0]
    interval_end = frames[0]
    interval_is_open = open_state.is_open_frame(frames[0])
    interval_peak = open_state.open_value_at(frames[0])

    for frame_no in frames[1:]:
        frame_is_open = open_state.is_open_frame(frame_no)
        frame_open_value = open_state.open_value_at(frame_no)
        is_contiguous = frame_no == (interval_end + 1)

        if is_contiguous and frame_is_open == interval_is_open:
            interval_end = frame_no
            interval_peak = max(interval_peak, frame_open_value)
            continue

        intervals.append(
            MouthOpenInterval(
                start_frame=interval_start,
                end_frame=interval_end,
                is_open=interval_is_open,
                peak_open_value=interval_peak,
            )
        )
        interval_start = frame_no
        interval_end = frame_no
        interval_is_open = frame_is_open
        interval_peak = frame_open_value

    intervals.append(
        MouthOpenInterval(
            start_frame=interval_start,
            end_frame=interval_end,
            is_open=interval_is_open,
            peak_open_value=interval_peak,
        )
    )
    return intervals


def _detect_isolated_short_open_candidates(
    open_state: MorphFrameOpenState,
) -> list[IsolatedShortOpenCandidate]:
    intervals = _extract_mouth_open_intervals(open_state)
    candidates: list[IsolatedShortOpenCandidate] = []
    for index in range(1, len(intervals) - 1):
        previous_interval = intervals[index - 1]
        current_interval = intervals[index]
        next_interval = intervals[index + 1]

        if not current_interval.is_open:
            continue
        if not previous_interval.is_open and not next_interval.is_open:
            if current_interval.length_frames <= ISOLATED_OPEN_MAX_LENGTH_FRAMES:
                if current_interval.peak_open_value <= ISOLATED_OPEN_MAX_PEAK_VALUE:
                    candidates.append(
                        IsolatedShortOpenCandidate(
                            start_frame=current_interval.start_frame,
                            end_frame=current_interval.end_frame,
                            length_frames=current_interval.length_frames,
                            peak_open_value=current_interval.peak_open_value,
                            previous_interval_is_closed=True,
                            next_interval_is_closed=True,
                        )
                    )
    return candidates


def _suppress_isolated_short_open_candidates(
    frames: list[MorphFrame],
    candidates: list[IsolatedShortOpenCandidate],
    *,
    active_protected_specs: list[AsymmetricTrapezoidSpec] | None = None,
    protected_event_ranges: dict[str, list[tuple[int, int]]] | None = None,
) -> list[MorphFrame]:
    active_protected_specs = active_protected_specs or []
    protected_event_ranges = protected_event_ranges or {}
    suppressed_frame_ranges = {
        frame_no
        for candidate in candidates
        if not _candidate_overlaps_protected_ms11_2_shape(
            candidate.start_frame,
            candidate.end_frame,
            active_protected_specs,
        )
        if not _candidate_overlaps_protected_event_range(
            candidate.start_frame,
            candidate.end_frame,
            protected_event_ranges,
        )
        for frame_no in range(candidate.start_frame, candidate.end_frame + 1)
    }
    if not suppressed_frame_ranges:
        return list(frames)

    suppressed_frames: list[MorphFrame] = []
    for frame_no, vowel, value in frames:
        if frame_no in suppressed_frame_ranges and value > 0.0:
            suppressed_frames.append((frame_no, vowel, 0.0))
            continue
        suppressed_frames.append((frame_no, vowel, value))
    return suppressed_frames


def _detect_short_morph_pulse_candidates(
    open_state: MorphFrameOpenState,
) -> list[MorphShortPulseCandidate]:
    overall_open_intervals = [
        interval for interval in _extract_mouth_open_intervals(open_state)
        if interval.is_open
    ]
    candidates: list[MorphShortPulseCandidate] = []
    for vowel in SUPPORTED_MORPHS:
        for start_frame, end_frame in _extract_per_morph_open_intervals(open_state, vowel):
            length_frames = (end_frame - start_frame) + 1
            if length_frames > MORPH_PULSE_MAX_LENGTH_FRAMES:
                continue
            if not _is_short_morph_pulse_removable(
                open_state=open_state,
                vowel=vowel,
                start_frame=start_frame,
                end_frame=end_frame,
                overall_open_intervals=overall_open_intervals,
            ):
                continue
            candidates.append(
                MorphShortPulseCandidate(
                    vowel=vowel,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    length_frames=length_frames,
                )
            )
    return candidates


def _extract_per_morph_open_intervals(
    open_state: MorphFrameOpenState,
    vowel: str,
) -> list[tuple[int, int]]:
    frames = sorted(open_state.frame_values)
    intervals: list[tuple[int, int]] = []
    interval_start: int | None = None
    interval_end: int | None = None

    for frame_no in frames:
        if open_state.value_at(frame_no, vowel) <= open_state.epsilon:
            if interval_start is not None and interval_end is not None:
                intervals.append((interval_start, interval_end))
                interval_start = None
                interval_end = None
            continue

        if interval_start is None:
            interval_start = frame_no
            interval_end = frame_no
            continue

        if frame_no == (interval_end + 1):
            interval_end = frame_no
            continue

        intervals.append((interval_start, interval_end))
        interval_start = frame_no
        interval_end = frame_no

    if interval_start is not None and interval_end is not None:
        intervals.append((interval_start, interval_end))
    return intervals


def _is_short_morph_pulse_removable(
    *,
    open_state: MorphFrameOpenState,
    vowel: str,
    start_frame: int,
    end_frame: int,
    overall_open_intervals: list[MouthOpenInterval],
) -> bool:
    containing_interval = None
    for interval in overall_open_intervals:
        if interval.start_frame <= start_frame and interval.end_frame >= end_frame:
            containing_interval = interval
            break
    if containing_interval is None:
        return False
    if containing_interval.start_frame >= start_frame:
        return False
    if containing_interval.end_frame <= end_frame:
        return False

    for frame_no in range(start_frame, end_frame + 1):
        if not _can_remove_morph_value_without_changing_open_state(
            open_state=open_state,
            frame_no=frame_no,
            vowel=vowel,
        ):
            return False
    return True


def _can_remove_morph_value_without_changing_open_state(
    *,
    open_state: MorphFrameOpenState,
    frame_no: int,
    vowel: str,
) -> bool:
    if open_state.value_at(frame_no, vowel) <= open_state.epsilon:
        return False
    other_open_value = max(
        open_state.value_at(frame_no, other_vowel)
        for other_vowel in SUPPORTED_MORPHS
        if other_vowel != vowel
    )
    if other_open_value <= open_state.epsilon:
        return False
    return other_open_value >= open_state.value_at(frame_no, vowel)


def _suppress_short_morph_pulse_candidates(
    frames: list[MorphFrame],
    candidates: list[MorphShortPulseCandidate],
    *,
    active_protected_specs: list[AsymmetricTrapezoidSpec] | None = None,
    protected_event_ranges: dict[str, list[tuple[int, int]]] | None = None,
) -> list[MorphFrame]:
    active_protected_specs = active_protected_specs or []
    protected_event_ranges = protected_event_ranges or {}
    suppressed_keys = {
        (candidate.vowel, frame_no)
        for candidate in candidates
        if not _candidate_overlaps_protected_ms11_2_shape(
            candidate.start_frame,
            candidate.end_frame,
            active_protected_specs,
            vowel=candidate.vowel,
        )
        if not _candidate_overlaps_protected_event_range(
            candidate.start_frame,
            candidate.end_frame,
            protected_event_ranges,
            vowel=candidate.vowel,
        )
        for frame_no in range(candidate.start_frame, candidate.end_frame + 1)
    }
    if not suppressed_keys:
        return list(frames)

    suppressed_frames: list[MorphFrame] = []
    for frame_no, vowel, value in frames:
        if (vowel, frame_no) in suppressed_keys and value > 0.0:
            suppressed_frames.append((frame_no, vowel, 0.0))
            continue
        suppressed_frames.append((frame_no, vowel, value))
    return suppressed_frames


def _candidate_overlaps_protected_ms11_2_shape(
    start_frame: int,
    end_frame: int,
    protected_specs: list[AsymmetricTrapezoidSpec],
    *,
    vowel: str | None = None,
) -> bool:
    for spec in protected_specs:
        if vowel is not None and spec.vowel != vowel:
            continue
        if start_frame <= spec.end_frame and end_frame >= spec.start_frame:
            return True
    return False


def _build_allowed_non_zero_ranges(
    points: list[VowelTimelinePoint],
) -> dict[str, list[tuple[int, int]]]:
    allowed_ranges: dict[str, list[tuple[int, int]]] = {}
    for point in points:
        start_sec, end_sec = _event_bounds(point)
        start_frame = _sec_to_frame(start_sec)
        end_frame = _sec_to_frame(end_sec)
        allowed_ranges.setdefault(point.vowel, []).append((start_frame, end_frame))
    return allowed_ranges


def _build_protected_event_ranges(
    points: list[VowelTimelinePoint],
) -> dict[str, list[tuple[int, int]]]:
    return _build_allowed_non_zero_ranges(points)


def _build_required_zero_frames(
    points: list[VowelTimelinePoint],
) -> dict[str, set[int]]:
    required_zero_frames: dict[str, set[int]] = {}
    expanded_with_flags: list[_MorphFrameWithFlags] = []
    for point in points:
        spec = _build_interval_trapezoid_spec(point)
        if spec is None:
            peak_frames = _build_peak_morph_frames([point])
            expanded_with_flags.extend(
                (frame_no, vowel, value, False)
                for frame_no, vowel, value in peak_frames
            )
            continue
        expanded_with_flags.extend(_expand_trapezoid_spec_to_morph_frames(spec))

    expanded_with_flags = _shift_conflicting_rise_start_zeros(expanded_with_flags)
    for frame_no, vowel, value, _ in expanded_with_flags:
        if value <= MORPH_FRAME_OPEN_EPSILON:
            required_zero_frames.setdefault(vowel, set()).add(frame_no)
    return required_zero_frames


def _remove_non_zero_outside_allowed_ranges(
    frames: list[MorphFrame],
    *,
    allowed_non_zero_ranges: dict[str, list[tuple[int, int]]] | None = None,
) -> list[MorphFrame]:
    if not allowed_non_zero_ranges:
        return list(frames)

    filtered_frames: list[MorphFrame] = []
    for frame_no, vowel, value in frames:
        if value > MORPH_FRAME_OPEN_EPSILON and not _is_frame_in_allowed_non_zero_range(
            frame_no,
            vowel,
            allowed_non_zero_ranges,
        ):
            continue
        filtered_frames.append((frame_no, vowel, value))
    return filtered_frames


def _is_frame_in_allowed_non_zero_range(
    frame_no: int,
    vowel: str,
    allowed_non_zero_ranges: dict[str, list[tuple[int, int]]],
) -> bool:
    return any(
        start_frame <= frame_no <= end_frame
        for start_frame, end_frame in allowed_non_zero_ranges.get(vowel, [])
    )


def _prune_redundant_zero_morph_frames(
    frames: list[MorphFrame],
    *,
    required_zero_frames: dict[str, set[int]] | None = None,
) -> list[MorphFrame]:
    if not required_zero_frames:
        return list(frames)

    pruned_frames: list[MorphFrame] = []
    for frame_no, vowel, value in frames:
        if value > MORPH_FRAME_OPEN_EPSILON:
            pruned_frames.append((frame_no, vowel, value))
            continue
        if frame_no in required_zero_frames.get(vowel, set()):
            pruned_frames.append((frame_no, vowel, value))
    return pruned_frames


def _candidate_overlaps_protected_event_range(
    start_frame: int,
    end_frame: int,
    protected_event_ranges: dict[str, list[tuple[int, int]]],
    *,
    vowel: str | None = None,
) -> bool:
    if vowel is not None:
        ranges = protected_event_ranges.get(vowel, [])
        return any(start_frame <= range_end and end_frame >= range_start for range_start, range_end in ranges)

    return any(
        start_frame <= range_end and end_frame >= range_start
        for ranges in protected_event_ranges.values()
        for range_start, range_end in ranges
    )


def _shift_conflicting_rise_start_zeros(
    frames: list[tuple[int, str, float, bool]],
) -> list[tuple[int, str, float, bool]]:
    # Resolve same-frame 0/non-zero collision only for rise-start zero keys.
    non_zero_at_frame = {
        (vowel, frame_no)
        for frame_no, vowel, value, _ in frames
        if value > 0.0
    }

    adjusted: list[tuple[int, str, float, bool]] = []
    for frame_no, vowel, value, is_rise_start_zero in frames:
        if is_rise_start_zero and (vowel, frame_no) in non_zero_at_frame:
            adjusted.append((max(0, frame_no - 1), vowel, value, is_rise_start_zero))
            continue
        adjusted.append((frame_no, vowel, value, is_rise_start_zero))
    return adjusted


def _event_bounds(point: VowelTimelinePoint) -> tuple[float, float]:
    if point.start_sec is not None and point.end_sec is not None:
        return (point.start_sec, point.end_sec)
    half = max(point.duration_sec, 0.0) * 0.5
    return (point.time_sec - half, point.time_sec + half)


def _point_peak_value(point: VowelTimelinePoint) -> float:
    if point.peak_value is not None:
        return float(point.peak_value)
    return float(point.value)


def _finalize_morph_value(value: float) -> float:
    # Round only once at VMD write boundary when more than 4 decimals remain.
    if value <= 0.0:
        return 0.0
    rounded = round(float(value), 4)
    if abs(value - rounded) <= 1e-12:
        return float(value)
    return rounded


def _sec_to_frame(time_sec: float) -> int:
    return int(round(time_sec * VMD_FPS))


def _encode_shift_jis_fixed(text: str, size: int) -> bytes:
    raw = text.encode("shift_jis")
    return _pad_bytes(raw, size)


def _pad_bytes(raw: bytes, size: int) -> bytes:
    if len(raw) > size:
        return raw[:size]
    return raw + (b"\x00" * (size - len(raw)))
