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


def write_morph_vmd(
    output_path: str | Path,
    timeline: Iterable[VowelTimelinePoint | tuple[float, str] | tuple[float, str, float]],
    model_name: str = "AutoLipTool",
) -> Path:
    points = _normalize_timeline(timeline)
    morph_frames = _build_peak_morph_frames(points)
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
    timeline: Iterable[VowelTimelinePoint | tuple[float, str] | tuple[float, str, float]],
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
        else:
            raise ValueError("Timeline point must be VowelTimelinePoint or tuple(time_sec, vowel[, value]).")

        if point.vowel not in SUPPORTED_MORPHS:
            raise ValueError(f"Unsupported vowel morph: {point.vowel}")
        if point.time_sec < 0:
            raise ValueError("time_sec must be >= 0")
        if point.value < 0:
            raise ValueError("value must be >= 0")

        clamped_value = min(point.value, MAX_MORPH_VALUE)
        normalized.append(
            VowelTimelinePoint(time_sec=point.time_sec, vowel=point.vowel, value=clamped_value)
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


def _sec_to_frame(time_sec: float) -> int:
    return int(round(time_sec * VMD_FPS))


def _encode_shift_jis_fixed(text: str, size: int) -> bytes:
    raw = text.encode("shift_jis")
    return _pad_bytes(raw, size)


def _pad_bytes(raw: bytes, size: int) -> bytes:
    if len(raw) > size:
        return raw[:size]
    return raw + (b"\x00" * (size - len(raw)))
