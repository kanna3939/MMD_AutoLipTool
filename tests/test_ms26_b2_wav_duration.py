from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import struct
from types import SimpleNamespace
import wave

import pytest

from tests.ms26_wav_duration_helpers import (
    WavDurationValidationError,
    assert_conversion_result_identity,
    assert_source_identity,
    compare_wav_durations,
    measure_pcm_wav,
    sha256_file,
)


def _write_pcm_frames(path: Path, *, frames: int, channels: int = 1, rate_hz: int = 44100) -> None:
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(2)
        writer.setframerate(rate_hz)
        writer.writeframes(b"\0\0" * frames * channels)


def _write_raw_wav(
    path: Path,
    *,
    data: bytes,
    declared_data_size: int | None = None,
    channels: int = 1,
    rate_hz: int = 44100,
    sample_width_bytes: int = 2,
    audio_format: int = 1,
) -> None:
    data_size = len(data) if declared_data_size is None else declared_data_size
    block_align = channels * sample_width_bytes
    byte_rate = rate_hz * block_align
    fmt_payload = struct.pack(
        "<HHIIHH",
        audio_format,
        channels,
        rate_hz,
        byte_rate,
        block_align,
        sample_width_bytes * 8,
    )
    body = (
        b"WAVE"
        + b"fmt "
        + struct.pack("<I", len(fmt_payload))
        + fmt_payload
        + b"data"
        + struct.pack("<I", data_size)
        + data
    )
    path.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)


@pytest.mark.parametrize("difference_frames", [0, 2204, 2205, -2204, -2205])
def test_duration_threshold_accepts_same_and_boundary_values(
    tmp_path: Path,
    difference_frames: int,
) -> None:
    analysis_path = tmp_path / f"analysis_{difference_frames}.wav"
    mmd_path = tmp_path / f"mmd_{difference_frames}.wav"
    analysis_frames = 44100
    mmd_frames = analysis_frames + difference_frames
    _write_pcm_frames(analysis_path, frames=analysis_frames, channels=1)
    _write_pcm_frames(mmd_path, frames=mmd_frames, channels=2)

    comparison = compare_wav_durations(analysis_path, mmd_path)

    assert comparison.difference <= Fraction(1, 20)
    assert comparison.analysis.rate_hz == 44100
    assert comparison.mmd.rate_hz == 44100


@pytest.mark.parametrize("difference_frames", [2206, -2206])
def test_duration_threshold_rejects_one_sample_over_boundary(
    tmp_path: Path,
    difference_frames: int,
) -> None:
    analysis_path = tmp_path / f"analysis_over_{difference_frames}.wav"
    mmd_path = tmp_path / f"mmd_over_{difference_frames}.wav"
    _write_pcm_frames(analysis_path, frames=44100, channels=1)
    _write_pcm_frames(mmd_path, frames=44100 + difference_frames, channels=2)

    with pytest.raises(WavDurationValidationError, match="exceeds threshold"):
        compare_wav_durations(analysis_path, mmd_path)


def test_same_sample_difference_is_rejected_when_rate_is_invalid(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.wav"
    mmd_path = tmp_path / "mmd.wav"
    _write_pcm_frames(analysis_path, frames=44100, channels=1, rate_hz=48000)
    _write_pcm_frames(mmd_path, frames=44100, channels=2)

    with pytest.raises(WavDurationValidationError, match="unexpected sample rate"):
        compare_wav_durations(analysis_path, mmd_path)


@pytest.mark.parametrize(
    ("channels", "role"),
    [(3, "analysis"), (1, "mmd")],
)
def test_role_specific_channel_contract_is_enforced(
    tmp_path: Path,
    channels: int,
    role: str,
) -> None:
    path = tmp_path / f"wrong_{role}.wav"
    _write_pcm_frames(path, frames=44100, channels=channels)

    with pytest.raises(WavDurationValidationError, match="unexpected channel count"):
        measure_pcm_wav(path, role=role)


def test_sample_width_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "sample_width_8.wav"
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(1)
        writer.setframerate(44100)
        writer.writeframes(b"\0" * 44100)

    with pytest.raises(WavDurationValidationError, match="sample width"):
        measure_pcm_wav(path, role="analysis")


@pytest.mark.parametrize(
    ("role", "channels", "data_size"),
    [("analysis", 1, 3), ("mmd", 2, 5)],
)
def test_partial_data_frame_tail_is_rejected(
    tmp_path: Path,
    role: str,
    channels: int,
    data_size: int,
) -> None:
    path = tmp_path / f"partial_tail_{role}.wav"
    _write_raw_wav(
        path,
        data=b"\0" * data_size,
        declared_data_size=data_size,
        channels=channels,
    )

    with pytest.raises(WavDurationValidationError, match="incomplete frame tail"):
        measure_pcm_wav(path, role=role)


@pytest.mark.parametrize(
    "case_name",
    ["missing", "broken_header", "empty_data", "truncated_data", "non_pcm", "zero_rate"],
)
def test_invalid_or_unreadable_wav_is_rejected(tmp_path: Path, case_name: str) -> None:
    path = tmp_path / f"{case_name}.wav"
    if case_name == "missing":
        pass
    elif case_name == "broken_header":
        path.write_bytes(b"not a wave")
    elif case_name == "empty_data":
        _write_raw_wav(path, data=b"", declared_data_size=0)
    elif case_name == "truncated_data":
        _write_raw_wav(path, data=b"\0\0", declared_data_size=8)
    elif case_name == "non_pcm":
        _write_raw_wav(path, data=b"\0\0", audio_format=6)
    elif case_name == "zero_rate":
        _write_raw_wav(path, data=b"\0\0", rate_hz=0)
    else:
        raise AssertionError(f"unhandled case {case_name}")

    with pytest.raises(WavDurationValidationError):
        measure_pcm_wav(path, role="analysis")


def test_directory_and_wave_permission_failures_are_not_silent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(WavDurationValidationError, match="not a file"):
        measure_pcm_wav(tmp_path, role="analysis")

    def denied_open(*args: object, **kwargs: object) -> None:
        raise PermissionError("test permission denial")

    unreadable_path = tmp_path / "unreadable.wav"
    unreadable_path.write_bytes(b"fixture")
    monkeypatch.setattr("tests.ms26_wav_duration_helpers.wave.open", denied_open)
    with pytest.raises(WavDurationValidationError, match="unreadable"):
        measure_pcm_wav(unreadable_path, role="analysis")


def test_same_output_path_is_rejected_before_double_measurement(tmp_path: Path) -> None:
    path = tmp_path / "same.wav"
    _write_pcm_frames(path, frames=44100, channels=1)

    with pytest.raises(WavDurationValidationError, match="distinct"):
        compare_wav_durations(path, path)


def test_reversed_roles_are_rejected(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.wav"
    mmd_path = tmp_path / "mmd.wav"
    _write_pcm_frames(analysis_path, frames=44100, channels=1)
    _write_pcm_frames(mmd_path, frames=44100, channels=2)

    with pytest.raises(WavDurationValidationError, match="unexpected channel count"):
        compare_wav_durations(mmd_path, analysis_path)


def test_source_identity_and_distinct_outputs_are_checked(tmp_path: Path) -> None:
    source_path = tmp_path / "source.wav"
    analysis_path = tmp_path / "analysis.wav"
    mmd_path = tmp_path / "mmd.wav"
    for path in (source_path, analysis_path, mmd_path):
        path.write_bytes(b"fixture")

    good_analysis = SimpleNamespace(
        source_path=source_path,
        analysis_wav_path=analysis_path,
    )
    good_mmd = SimpleNamespace(source_path=source_path, mmd_wav_path=mmd_path)
    assert_conversion_result_identity(source_path, good_analysis, good_mmd)

    mismatched = SimpleNamespace(
        source_path=tmp_path / "other.wav",
        analysis_wav_path=analysis_path,
    )
    with pytest.raises(WavDurationValidationError, match="identity mismatch"):
        assert_conversion_result_identity(source_path, mismatched, good_mmd)

    same_output = SimpleNamespace(source_path=source_path, mmd_wav_path=analysis_path)
    with pytest.raises(WavDurationValidationError, match="distinct"):
        assert_conversion_result_identity(source_path, good_analysis, same_output)


def test_source_hash_identity_detects_replacement(tmp_path: Path) -> None:
    source_path = tmp_path / "source.wav"
    source_path.write_bytes(b"original source bytes")
    expected_sha256 = sha256_file(source_path)

    source_path.write_bytes(b"replacement source bytes")

    with pytest.raises(WavDurationValidationError, match="source identity mismatch"):
        assert_source_identity(source_path, expected_sha256)


def test_equal_result_metadata_does_not_mask_longer_wav(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.wav"
    mmd_path = tmp_path / "mmd.wav"
    _write_pcm_frames(analysis_path, frames=44100, channels=1)
    _write_pcm_frames(mmd_path, frames=44100 + 2206, channels=2)
    analysis_result = SimpleNamespace(
        source_path=tmp_path / "source.wav",
        analysis_wav_path=analysis_path,
        duration_sec=1.0,
    )
    mmd_result = SimpleNamespace(
        source_path=tmp_path / "source.wav",
        mmd_wav_path=mmd_path,
        duration_sec=1.0,
    )
    assert analysis_result.duration_sec == mmd_result.duration_sec

    with pytest.raises(WavDurationValidationError, match="exceeds threshold"):
        compare_wav_durations(analysis_path, mmd_path)
