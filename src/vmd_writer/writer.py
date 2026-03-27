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
) -> Path:
    points = _normalize_timeline(timeline)
    allowed_non_zero_ranges = _build_allowed_non_zero_ranges(points)
    protected_event_ranges = _build_protected_event_ranges(points)
    morph_frames, protected_ms11_2_specs = _build_interval_morph_frames_with_metadata(points)
    required_zero_frames = _build_required_zero_frames(points)
    if apply_final_normalization:
        morph_frames = _apply_final_morph_frame_normalization(
            morph_frames,
            protected_ms11_2_specs=protected_ms11_2_specs,
            protected_event_ranges=protected_event_ranges,
            allowed_non_zero_ranges=allowed_non_zero_ranges,
            required_zero_frames=required_zero_frames,
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
) -> list[MorphFrame]:
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
) -> list[MorphFrame]:
    expanded, _ = _build_interval_morph_frames_with_metadata(points)
    return expanded


def _build_interval_morph_frames_with_metadata(
    points: list[VowelTimelinePoint],
) -> tuple[list[MorphFrame], list[AsymmetricTrapezoidSpec]]:
    expanded_with_flags: list[_MorphFrameWithFlags] = []
    protected_ms11_2_specs: list[AsymmetricTrapezoidSpec] = []
    for index, point in enumerate(points):
        spec = _build_interval_trapezoid_spec(
            point,
            source_event_index=index,
        )
        if spec is None:
            for frame_no, vowel, value in _build_peak_morph_frames([point]):
                expanded_with_flags.append((frame_no, vowel, value, False))
            continue
        expanded_with_flags.extend(_expand_trapezoid_spec_to_morph_frames(spec))
        if _is_protectable_ms11_2_spec(spec):
            protected_ms11_2_specs.append(spec)

    expanded_with_flags = _shift_conflicting_rise_start_zeros(expanded_with_flags)
    expanded = [(frame_no, vowel, value) for frame_no, vowel, value, _ in expanded_with_flags]

    expanded.sort(key=lambda x: x[0])
    return expanded, protected_ms11_2_specs


def _build_interval_trapezoid_spec(
    point: VowelTimelinePoint,
    *,
    source_event_index: int | None = None,
) -> AsymmetricTrapezoidSpec | None:
    peak_value = _point_peak_value(point)
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
