from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Iterable

VMD_FPS = 30
MAX_MORPH_VALUE = 0.5
SUPPORTED_MORPHS = ("\u3042", "\u3044", "\u3046", "\u3048", "\u304a")
PEAK_SIDE_FRAME_OFFSET = 2

_VMD_HEADER = b"Vocaloid Motion Data 0002"


@dataclass(frozen=True)
class VowelTimelinePoint:
    time_sec: float
    vowel: str
    value: float = MAX_MORPH_VALUE
    duration_sec: float = 0.0
    start_sec: float | None = None
    end_sec: float | None = None

    def __post_init__(self) -> None:
        time_sec = float(self.time_sec)
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
        object.__setattr__(self, "duration_sec", duration_sec)
        object.__setattr__(self, "start_sec", start_sec)
        object.__setattr__(self, "end_sec", end_sec)


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
) -> Path:
    points = _normalize_timeline(timeline)
    morph_frames = _build_interval_morph_frames(points)
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
            fp.write(struct.pack("<f", value))

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
    return write_morph_vmd(output_path=output_path, timeline=dummy_timeline, model_name=model_name)


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
        if point.value < 0:
            raise ValueError("value must be >= 0")
        if point.duration_sec < 0:
            raise ValueError("duration_sec must be >= 0")
        if point.start_sec > point.end_sec:
            raise ValueError("start_sec must be <= end_sec")
        if not (point.start_sec <= point.time_sec <= point.end_sec):
            raise ValueError("time_sec must be inside [start_sec, end_sec]")

        clamped_value = min(point.value, MAX_MORPH_VALUE)
        normalized.append(
            VowelTimelinePoint(
                time_sec=point.time_sec,
                vowel=point.vowel,
                value=clamped_value,
                duration_sec=point.duration_sec,
                start_sec=point.start_sec,
                end_sec=point.end_sec,
            )
        )

    normalized.sort(key=lambda x: x.time_sec)
    return normalized


def _build_peak_morph_frames(
    points: list[VowelTimelinePoint],
) -> list[tuple[int, str, float]]:
    expanded: list[tuple[int, str, float]] = []
    for point in points:
        center_frame = _sec_to_frame(point.time_sec)
        before_frame = max(0, center_frame - PEAK_SIDE_FRAME_OFFSET)
        after_frame = center_frame + PEAK_SIDE_FRAME_OFFSET

        expanded.append((before_frame, point.vowel, 0.0))
        expanded.append((center_frame, point.vowel, point.value))
        expanded.append((after_frame, point.vowel, 0.0))

    expanded.sort(key=lambda x: x[0])
    return expanded


def _build_interval_morph_frames(
    points: list[VowelTimelinePoint],
) -> list[tuple[int, str, float]]:
    expanded: list[tuple[int, str, float]] = []
    for point in points:
        start_sec, end_sec = _event_bounds(point)
        center_frame = _sec_to_frame(point.time_sec)
        start_frame = _sec_to_frame(start_sec)
        end_frame = _sec_to_frame(end_sec)

        if end_frame <= start_frame:
            expanded.extend(_build_peak_morph_frames([point]))
            continue

        rise_end_frame = min(center_frame, start_frame + PEAK_SIDE_FRAME_OFFSET)
        fall_start_frame = max(center_frame, end_frame - PEAK_SIDE_FRAME_OFFSET)

        if fall_start_frame <= rise_end_frame:
            peak_frame = center_frame
            if peak_frame <= start_frame:
                peak_frame = min(start_frame + 1, end_frame)
            if peak_frame >= end_frame:
                peak_frame = max(end_frame - 1, start_frame)

            if peak_frame <= start_frame or peak_frame >= end_frame:
                expanded.extend(_build_peak_morph_frames([point]))
                continue

            expanded.append((start_frame, point.vowel, 0.0))
            expanded.append((peak_frame, point.vowel, point.value))
            expanded.append((end_frame, point.vowel, 0.0))
            continue

        expanded.append((start_frame, point.vowel, 0.0))
        expanded.append((rise_end_frame, point.vowel, point.value))
        expanded.append((fall_start_frame, point.vowel, point.value))
        expanded.append((end_frame, point.vowel, 0.0))

    expanded.sort(key=lambda x: x[0])
    return expanded


def _event_bounds(point: VowelTimelinePoint) -> tuple[float, float]:
    if point.start_sec is not None and point.end_sec is not None:
        return (point.start_sec, point.end_sec)
    half = max(point.duration_sec, 0.0) * 0.5
    return (point.time_sec - half, point.time_sec + half)


def _sec_to_frame(time_sec: float) -> int:
    return int(round(time_sec * VMD_FPS))


def _encode_shift_jis_fixed(text: str, size: int) -> bytes:
    raw = text.encode("shift_jis")
    return _pad_bytes(raw, size)


def _pad_bytes(raw: bytes, size: int) -> bytes:
    if len(raw) > size:
        return raw[:size]
    return raw + (b"\x00" * (size - len(raw)))
