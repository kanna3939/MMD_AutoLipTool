import struct
from pathlib import Path

import pytest

from src.core.morph_name_sets import JAPANESE_OUTPUT_NAMES, LATIN_OUTPUT_NAMES
from src.vmd_writer.validator import (
    VmdReadbackValidationError,
    validate_morph_vmd_readback,
)
from src.vmd_writer.writer import MAX_MORPH_FRAMES, write_morph_frames_vmd


def _write_valid_vmd(
    path: Path,
    *,
    frames=((0, "あ", 0.0), (2, "い", 0.12345)),
    model_name="AutoLipTool",
    output_names=JAPANESE_OUTPUT_NAMES,
) -> None:
    write_morph_frames_vmd(
        path,
        frames,
        model_name=model_name,
        output_morph_names=output_names,
    )


def _assert_valid(
    path: Path,
    *,
    frames=((0, "あ", 0.0), (2, "い", 0.12345)),
    model_name="AutoLipTool",
    output_names=JAPANESE_OUTPUT_NAMES,
) -> None:
    validate_morph_vmd_readback(
        path,
        expected_model_name=model_name,
        expected_morph_frames=frames,
        expected_output_morph_names=output_names,
    )


def test_validates_empty_japanese_vmd(tmp_path):
    path = tmp_path / "empty.vmd"
    _write_valid_vmd(path, frames=())

    _assert_valid(path, frames=())


def test_validates_japanese_and_latin_morph_names(tmp_path):
    japanese_path = tmp_path / "japanese.vmd"
    latin_path = tmp_path / "latin.vmd"
    japanese_frames = ((0, "あ", 0.25), (4, "お", 0.12567))
    latin_frames = ((0, "A", 0.25), (4, "O", 0.12567))
    _write_valid_vmd(
        japanese_path,
        frames=japanese_frames,
        output_names=JAPANESE_OUTPUT_NAMES,
    )
    _write_valid_vmd(
        latin_path,
        frames=latin_frames,
        output_names=LATIN_OUTPUT_NAMES,
    )

    _assert_valid(
        japanese_path,
        frames=japanese_frames,
        output_names=JAPANESE_OUTPUT_NAMES,
    )
    _assert_valid(
        latin_path,
        frames=latin_frames,
        output_names=LATIN_OUTPUT_NAMES,
    )


@pytest.mark.parametrize(
    ("offset", "replacement"),
    [
        (0, b"X"),
        (50, struct.pack("<I", 1)),
        (54, struct.pack("<I", 3)),
    ],
)
def test_rejects_header_bone_or_morph_count_mismatch(tmp_path, offset, replacement):
    path = tmp_path / "broken.vmd"
    _write_valid_vmd(path)
    data = bytearray(path.read_bytes())
    data[offset : offset + len(replacement)] = replacement
    path.write_bytes(data)

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data[:-1],
        lambda data: data + b"\x00",
        lambda data: data.__setitem__(58, data[58] ^ 0x01),
        lambda data: data.__setitem__(58 + 15, 7),
        lambda data: data.__setitem__(58 + 19, data[58 + 19] ^ 0x01),
    ],
)
def test_rejects_truncated_extra_or_record_corruption(tmp_path, mutator):
    path = tmp_path / "broken.vmd"
    _write_valid_vmd(path)
    data = bytearray(path.read_bytes())
    result = mutator(data)
    if isinstance(result, bytearray):
        data = result
    path.write_bytes(data)

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path)


@pytest.mark.parametrize("tail_index", range(4))
def test_rejects_nonzero_tail_section(tmp_path, tail_index):
    path = tmp_path / "broken.vmd"
    _write_valid_vmd(path)
    data = bytearray(path.read_bytes())
    tail_offset = 58 + (23 * 2) + (tail_index * 4)
    data[tail_offset : tail_offset + 4] = struct.pack("<I", 1)
    path.write_bytes(data)

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path)


@pytest.mark.parametrize(
    "frames",
    [
        ((-1, "あ", 0.1),),
        ((0x100000000, "あ", 0.1),),
        ((0, "unsupported", 0.1),),
        ((0, "あ", float("nan")),),
        ((0, "あ", float("inf")),),
        ((0, "あ", -0.1),),
    ],
)
def test_rejects_invalid_expected_frames(tmp_path, frames):
    path = tmp_path / "empty.vmd"
    _write_valid_vmd(path, frames=())

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path, frames=frames)


def test_rejects_malformed_expected_count_before_reading_records(tmp_path):
    path = tmp_path / "empty.vmd"
    _write_valid_vmd(path, frames=())
    data = bytearray(path.read_bytes())
    data[54:58] = struct.pack("<I", 0xFFFFFFFF)
    path.write_bytes(data)

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path, frames=())


def test_rejects_expected_frame_count_above_bound(tmp_path):
    path = tmp_path / "empty.vmd"
    _write_valid_vmd(path, frames=())
    frames = [(index, "あ", 0.0) for index in range(MAX_MORPH_FRAMES + 1)]

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path, frames=frames)


@pytest.mark.parametrize(
    "model_name",
    ["", "bad\x00name", "あ" * 11, "😀"],
)
def test_rejects_invalid_expected_model_field(tmp_path, model_name):
    path = tmp_path / "model.vmd"
    _write_valid_vmd(path)

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(path, model_name=model_name)


def test_rejects_non_builtin_output_names(tmp_path):
    path = tmp_path / "names.vmd"
    _write_valid_vmd(path)

    with pytest.raises(VmdReadbackValidationError):
        _assert_valid(
            path,
            output_names=("a", "i", "u", "e", "o"),
        )
