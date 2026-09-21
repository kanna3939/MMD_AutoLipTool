"""Test-only WAV duration and result-identity oracles for MS26-B2."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import struct
import wave


MAX_DURATION_DIFFERENCE = Fraction(1, 20)
_ROLE_CHANNELS = {"analysis": 1, "mmd": 2}


class WavDurationValidationError(AssertionError):
    """Raised when a test WAV cannot satisfy the MS26-B2 oracle."""


@dataclass(frozen=True)
class WavMeasurement:
    role: str
    path: Path
    frames: int
    rate_hz: int
    channels: int
    sample_width_bytes: int

    @property
    def duration(self) -> Fraction:
        return Fraction(self.frames, self.rate_hz)


@dataclass(frozen=True)
class WavDurationComparison:
    analysis: WavMeasurement
    mmd: WavMeasurement
    difference: Fraction


def _fail(role: str, path: Path, reason: str, **details: object) -> None:
    detail_text = ", ".join(f"{key}={value!r}" for key, value in details.items())
    suffix = f" ({detail_text})" if detail_text else ""
    raise WavDurationValidationError(f"{role} WAV {path}: {reason}{suffix}")


def _read_declared_data_size(path: Path, role: str, block_align: int) -> int:
    """Read the RIFF data chunk so wave's floor division cannot hide a tail."""

    raw = path.read_bytes()
    if len(raw) < 12 or raw[0:4] != b"RIFF" or raw[8:12] != b"WAVE":
        _fail(role, path, "RIFF/WAVE header is invalid")

    cursor = 12
    while cursor + 8 <= len(raw):
        chunk_id = raw[cursor : cursor + 4]
        chunk_size = struct.unpack_from("<I", raw, cursor + 4)[0]
        payload_start = cursor + 8
        payload_end = payload_start + chunk_size
        if payload_end > len(raw):
            _fail(
                role,
                path,
                "WAV chunk payload is truncated",
                chunk=chunk_id,
                declared_bytes=chunk_size,
                available_bytes=max(0, len(raw) - payload_start),
            )
        if chunk_id == b"data":
            if block_align <= 0:
                _fail(role, path, "WAV block alignment must be positive", block_align=block_align)
            if chunk_size % block_align != 0:
                _fail(
                    role,
                    path,
                    "WAV data has an incomplete frame tail",
                    declared_data_bytes=chunk_size,
                    block_align=block_align,
                    remainder=chunk_size % block_align,
                )
            return chunk_size
        cursor = payload_end + (chunk_size % 2)

    _fail(role, path, "WAV data chunk is missing")


def measure_pcm_wav(path: str | Path, *, role: str) -> WavMeasurement:
    """Read a generated PCM WAV independently from conversion result metadata."""

    wav_path = Path(path)
    if role not in _ROLE_CHANNELS:
        raise WavDurationValidationError(f"unknown WAV role: {role!r}")
    if not wav_path.exists():
        _fail(role, wav_path, "file does not exist")
    if not wav_path.is_file():
        _fail(role, wav_path, "path is not a file")

    try:
        with wave.open(str(wav_path), "rb") as reader:
            compression = reader.getcomptype()
            channels = reader.getnchannels()
            rate_hz = reader.getframerate()
            sample_width_bytes = reader.getsampwidth()
            frames = reader.getnframes()

            if compression != "NONE":
                _fail(role, wav_path, "WAV is not uncompressed PCM", compression=compression)
            if channels <= 0:
                _fail(role, wav_path, "channel count must be positive", channels=channels)
            if rate_hz <= 0:
                _fail(role, wav_path, "sample rate must be positive", rate_hz=rate_hz)
            if sample_width_bytes != 2:
                _fail(
                    role,
                    wav_path,
                    "sample width must be 2 bytes",
                    sample_width_bytes=sample_width_bytes,
                )
            if channels != _ROLE_CHANNELS[role]:
                _fail(
                    role,
                    wav_path,
                    "unexpected channel count",
                    channels=channels,
                    expected_channels=_ROLE_CHANNELS[role],
                )
            if rate_hz != 44100:
                _fail(role, wav_path, "unexpected sample rate", rate_hz=rate_hz)
            declared_data_bytes = _read_declared_data_size(
                wav_path,
                role,
                channels * sample_width_bytes,
            )
            if frames <= 0:
                _fail(role, wav_path, "WAV data is empty", frames=frames)

            raw_frames = reader.readframes(frames)
            expected_bytes = frames * channels * sample_width_bytes
            actual_bytes = len(raw_frames)
            if declared_data_bytes != expected_bytes:
                _fail(
                    role,
                    wav_path,
                    "WAV frame count does not cover the declared data chunk",
                    frames=frames,
                    expected_bytes=expected_bytes,
                    declared_data_bytes=declared_data_bytes,
                )
            if actual_bytes != declared_data_bytes:
                _fail(
                    role,
                    wav_path,
                    "WAV data is truncated or frame alignment is invalid",
                    frames=frames,
                    expected_bytes=declared_data_bytes,
                    actual_bytes=actual_bytes,
                )
    except WavDurationValidationError:
        raise
    except (EOFError, OSError, wave.Error) as error:
        _fail(role, wav_path, "WAV is unreadable or has an invalid header", error=str(error))

    return WavMeasurement(
        role=role,
        path=wav_path,
        frames=frames,
        rate_hz=rate_hz,
        channels=channels,
        sample_width_bytes=sample_width_bytes,
    )


def compare_wav_durations(
    analysis_path: str | Path,
    mmd_path: str | Path,
    *,
    max_difference: Fraction = MAX_DURATION_DIFFERENCE,
) -> WavDurationComparison:
    """Measure both output files and apply the exact fractional threshold."""

    analysis = Path(analysis_path)
    mmd = Path(mmd_path)
    if analysis.resolve() == mmd.resolve():
        raise WavDurationValidationError(
            f"analysis and mmd WAV paths must be distinct: {analysis}"
        )

    analysis_measurement = measure_pcm_wav(analysis, role="analysis")
    mmd_measurement = measure_pcm_wav(mmd, role="mmd")
    difference = abs(analysis_measurement.duration - mmd_measurement.duration)
    if difference > max_difference:
        raise WavDurationValidationError(
            "WAV duration difference exceeds threshold "
            f"(analysis={analysis_measurement.duration}, "
            f"mmd={mmd_measurement.duration}, difference={difference}, "
            f"max_difference={max_difference})"
        )
    return WavDurationComparison(
        analysis=analysis_measurement,
        mmd=mmd_measurement,
        difference=difference,
    )


def assert_conversion_result_identity(
    source_path: str | Path,
    analysis_result: object,
    mmd_result: object,
) -> None:
    """Check source and output path identity without trusting duration metadata."""

    expected_source = Path(source_path).resolve()
    try:
        analysis_source = Path(analysis_result.source_path).resolve()
        mmd_source = Path(mmd_result.source_path).resolve()
        analysis_output = Path(analysis_result.analysis_wav_path).resolve()
        mmd_output = Path(mmd_result.mmd_wav_path).resolve()
    except AttributeError as error:
        raise WavDurationValidationError(
            f"conversion result is missing an expected path field: {error}"
        ) from error

    if analysis_source != expected_source:
        raise WavDurationValidationError(
            f"analysis source identity mismatch: expected={expected_source}, "
            f"actual={analysis_source}"
        )
    if mmd_source != expected_source:
        raise WavDurationValidationError(
            f"mmd source identity mismatch: expected={expected_source}, actual={mmd_source}"
        )
    if analysis_output == mmd_output:
        raise WavDurationValidationError(
            f"analysis and mmd output paths must be distinct: {analysis_output}"
        )
    if analysis_output == expected_source or mmd_output == expected_source:
        raise WavDurationValidationError(
            "a conversion output path must not replace the source audio"
        )


def sha256_file(path: str | Path) -> str:
    """Return a test-only source identity digest."""

    source_path = Path(path)
    if not source_path.exists() or not source_path.is_file():
        raise WavDurationValidationError(
            f"source identity path is missing or not a file: {source_path}"
        )
    digest = hashlib.sha256()
    try:
        with source_path.open("rb") as source_file:
            for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise WavDurationValidationError(
            f"source identity could not be read: {source_path}: {error}"
        ) from error
    return digest.hexdigest()


def assert_source_identity(path: str | Path, expected_sha256: str) -> None:
    """Fail when the source bytes changed since the pre-probe identity check."""

    source_path = Path(path)
    actual_sha256 = sha256_file(source_path)
    if actual_sha256 != expected_sha256:
        raise WavDurationValidationError(
            f"source identity mismatch: path={source_path}, "
            f"expected_sha256={expected_sha256}, actual_sha256={actual_sha256}"
        )


def write_test_pcm_wav(
    path: str | Path,
    *,
    duration_sec: float,
    sample_rate_hz: int,
    channel_count: int,
) -> int:
    """Create a deterministic, non-silent PCM fixture and return frame count."""

    wav_path = Path(path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = round(duration_sec * sample_rate_hz)
    with wave.open(str(wav_path), "wb") as writer:
        writer.setnchannels(channel_count)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate_hz)
        frames = bytearray()
        for frame_index in range(frame_count):
            for channel_index in range(channel_count):
                frequency_hz = 220.0 + channel_index * 110.0
                value = int(
                    12000
                    * math.sin(
                        2.0
                        * math.pi
                        * frequency_hz
                        * frame_index
                        / sample_rate_hz
                    )
                )
                frames.extend(value.to_bytes(2, "little", signed=True))
        writer.writeframes(bytes(frames))
    return frame_count
