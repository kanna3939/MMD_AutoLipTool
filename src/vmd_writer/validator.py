from __future__ import annotations

import math
from pathlib import Path
import struct
from typing import Sequence

from src.core.morph_name_sets import validate_output_morph_names

from .writer import (
    MAX_MORPH_FRAMES,
    _finalize_morph_value,
    _pad_bytes,
)


_VMD_HEADER = b"Vocaloid Motion Data 0002"
_MODEL_FIELD_SIZE = 20
_MORPH_NAME_FIELD_SIZE = 15
_MORPH_RECORD_SIZE = 23
_VMD_FIXED_TAIL_SIZE = 16
_VMD_PREFIX_SIZE = 30 + _MODEL_FIELD_SIZE + 4 + 4


class VmdReadbackValidationError(ValueError):
    """Raised when a production VMD file does not match its expected output."""


def _fail(message: str) -> None:
    raise VmdReadbackValidationError(message)


def _fixed_text_bytes(value: object, *, field_name: str, size: int) -> bytes:
    if type(value) is not str or not value:
        _fail(f"{field_name} must be a non-empty string")
    if any(
        ord(character) < 0x20 or ord(character) == 0x7F
        for character in value
    ):
        _fail(f"{field_name} contains a control character")
    try:
        encoded = value.encode("shift_jis")
    except UnicodeEncodeError as error:
        raise VmdReadbackValidationError(
            f"{field_name} cannot be encoded as Shift_JIS"
        ) from error
    if len(encoded) > size:
        _fail(f"{field_name} exceeds its fixed field")
    return _pad_bytes(encoded, size)


def _read_u32(data: bytes, offset: int, field_name: str) -> int:
    if offset < 0 or offset + 4 > len(data):
        _fail(f"{field_name} is truncated")
    try:
        return struct.unpack_from("<I", data, offset)[0]
    except struct.error as error:
        raise VmdReadbackValidationError(
            f"{field_name} is malformed"
        ) from error


def _prepare_expected_frames(
    expected_morph_frames: Sequence[tuple[int, str, float]],
    expected_output_morph_names: tuple[str, ...],
) -> tuple[tuple[int, str, bytes, bytes], ...]:
    try:
        frames = tuple(expected_morph_frames)
    except TypeError as error:
        raise VmdReadbackValidationError(
            "expected_morph_frames must be a sequence"
        ) from error

    if len(frames) > MAX_MORPH_FRAMES:
        _fail("expected morph frame count exceeds the maximum")

    prepared: list[tuple[int, str, bytes, bytes]] = []
    for index, frame in enumerate(frames):
        if not isinstance(frame, (tuple, list)) or len(frame) != 3:
            _fail(f"expected_morph_frames[{index}] is malformed")
        frame_no, morph_name, value = frame
        if (
            isinstance(frame_no, bool)
            or not isinstance(frame_no, int)
            or frame_no < 0
            or frame_no > 0xFFFFFFFF
        ):
            _fail(f"expected_morph_frames[{index}] has an invalid frame")
        if type(morph_name) is not str or morph_name not in expected_output_morph_names:
            _fail(f"expected_morph_frames[{index}] has an invalid morph name")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0.0
        ):
            _fail(f"expected_morph_frames[{index}] has an invalid value")
        try:
            expected_value_bytes = struct.pack(
                "<f",
                _finalize_morph_value(float(value)),
            )
        except (OverflowError, struct.error) as error:
            raise VmdReadbackValidationError(
                f"expected_morph_frames[{index}] value cannot be serialized"
            ) from error
        expected_name_bytes = _fixed_text_bytes(
            morph_name,
            field_name=f"expected_morph_frames[{index}].morph_name",
            size=_MORPH_NAME_FIELD_SIZE,
        )
        prepared.append(
            (frame_no, morph_name, expected_name_bytes, expected_value_bytes)
        )
    return tuple(prepared)


def validate_morph_vmd_readback(
    path: str | Path,
    *,
    expected_model_name: str,
    expected_morph_frames: Sequence[tuple[int, str, float]],
    expected_output_morph_names: Sequence[str],
) -> None:
    """Validate a morph-only VMD against the exact expected serialization."""
    try:
        output_path = Path(path)
    except (TypeError, ValueError) as error:
        raise VmdReadbackValidationError("VMD path is invalid") from error

    try:
        normalized_output_names = validate_output_morph_names(
            expected_output_morph_names
        )
    except (TypeError, ValueError) as error:
        raise VmdReadbackValidationError(
            "expected output morph names are invalid"
        ) from error

    expected_model_bytes = _fixed_text_bytes(
        expected_model_name,
        field_name="expected_model_name",
        size=_MODEL_FIELD_SIZE,
    )
    prepared_frames = _prepare_expected_frames(
        expected_morph_frames,
        normalized_output_names,
    )
    expected_size = (
        _VMD_PREFIX_SIZE
        + (_MORPH_RECORD_SIZE * len(prepared_frames))
        + _VMD_FIXED_TAIL_SIZE
    )

    try:
        if not output_path.is_file():
            _fail("VMD output is not a regular file")
        data = output_path.read_bytes()
    except VmdReadbackValidationError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VmdReadbackValidationError(
            "VMD output could not be read"
        ) from error

    if len(data) != expected_size:
        if len(data) < expected_size:
            _fail("VMD output is truncated")
        _fail("VMD output contains unexpected trailing data")

    expected_header = _pad_bytes(_VMD_HEADER, 30)
    if data[0:30] != expected_header:
        _fail("VMD header does not match")
    if data[30:50] != expected_model_bytes:
        _fail("VMD model field does not match")
    if _read_u32(data, 50, "bone frame count") != 0:
        _fail("VMD bone frame count is not zero")
    if _read_u32(data, 54, "morph frame count") != len(prepared_frames):
        _fail("VMD morph frame count does not match")

    cursor = 58
    for index, (
        expected_frame_no,
        _morph_name,
        expected_name_bytes,
        expected_value_bytes,
    ) in enumerate(prepared_frames):
        if cursor + _MORPH_RECORD_SIZE > len(data):
            _fail(f"VMD morph record {index} is truncated")
        actual_name_bytes = data[cursor : cursor + _MORPH_NAME_FIELD_SIZE]
        if actual_name_bytes != expected_name_bytes:
            _fail(f"VMD morph record {index} name does not match")
        actual_frame_no = _read_u32(data, cursor + 15, f"morph record {index} frame")
        if actual_frame_no != expected_frame_no:
            _fail(f"VMD morph record {index} frame does not match")
        actual_value_bytes = data[cursor + 19 : cursor + 23]
        try:
            actual_value = struct.unpack("<f", actual_value_bytes)[0]
        except struct.error as error:
            raise VmdReadbackValidationError(
                f"VMD morph record {index} value is malformed"
            ) from error
        if not math.isfinite(actual_value) or actual_value < 0.0:
            _fail(f"VMD morph record {index} value is invalid")
        if actual_value_bytes != expected_value_bytes:
            _fail(f"VMD morph record {index} value does not match")
        cursor += _MORPH_RECORD_SIZE

    for section_name in ("camera", "light", "self-shadow", "IK"):
        if _read_u32(data, cursor, f"{section_name} frame count") != 0:
            _fail(f"VMD {section_name} frame count is not zero")
        cursor += 4

    if cursor != len(data):
        _fail("VMD output does not end at EOF")
