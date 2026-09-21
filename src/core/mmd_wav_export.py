from __future__ import annotations

import os
import struct
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.core.audio_errors import AudioErrorCode, make_convert_error
from src.core.audio_probe import AudioProbeResult
from src.core.ffmpeg_runner import (
    DEFAULT_FFMPEG_TIMEOUT_SEC,
    FfmpegRunResult,
    run_ffmpeg_mmd_wav,
)


@dataclass(frozen=True)
class MmdWavSpec:
    codec: str
    sample_rate_hz: int
    channel_count: int


@dataclass(frozen=True)
class MmdWavExportResult:
    source_path: Path
    mmd_wav_path: Path
    spec: MmdWavSpec
    duration_sec: float | None
    file_size_bytes: int | None


MMD_WAV_SPEC = MmdWavSpec(
    codec="pcm_s16le",
    sample_rate_hz=44100,
    channel_count=2,
)


def export_mmd_wav(
    probe_result: AudioProbeResult,
    ffmpeg_path: str | Path,
    output_path: str | Path,
    *,
    runner: Callable[..., FfmpegRunResult] | None = None,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> MmdWavExportResult:
    """
    Export a user-facing MMD-use WAV from the original input audio.

    The analysis WAV remains an internal mono source; this function always uses
    probe_result.source_path and writes a stereo MMD-compatible WAV.
    """
    source_path = Path(probe_result.source_path)
    target_path = Path(output_path)

    _validate_export_paths(source_path, target_path)
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as error:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_PERMISSION_ERROR,
            "MMD用WAVの保存先フォルダを作成できませんでした。",
            detail=str(error),
        ) from error
    except OSError as error:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_OUTPUT_PATH_INVALID,
            "MMD用WAVの保存先フォルダを作成できませんでした。",
            detail=str(error),
        ) from error

    tmp_path = _build_temp_output_path(target_path)
    if runner is None:
        runner = run_ffmpeg_mmd_wav

    try:
        result = runner(
            ffmpeg_path=Path(ffmpeg_path),
            input_path=source_path,
            output_path=tmp_path,
            timeout_sec=timeout_sec,
            source_channel_count=probe_result.audio_stream.channel_count,
        )

        if result.returncode != 0:
            raise make_convert_error(
                AudioErrorCode.MMD_WAV_EXPORT_FAILED,
                "MMD用WAVの生成に失敗しました。",
                detail=_format_runner_failure(result),
            )

        _validate_mmd_wav_file(tmp_path)

        try:
            os.replace(tmp_path, target_path)
        except PermissionError as error:
            raise make_convert_error(
                AudioErrorCode.MMD_WAV_PERMISSION_ERROR,
                "MMD用WAVの保存先へ書き込む権限がありません。",
                detail=str(error),
            ) from error
        except OSError as error:
            raise make_convert_error(
                AudioErrorCode.MMD_WAV_REPLACE_FAILED,
                "MMD用WAVの保存に失敗しました。",
                detail=str(error),
            ) from error

    except Exception:
        _cleanup_partial_file(tmp_path)
        raise

    file_size_bytes = target_path.stat().st_size if target_path.exists() else None
    return MmdWavExportResult(
        source_path=source_path,
        mmd_wav_path=target_path,
        spec=MMD_WAV_SPEC,
        duration_sec=probe_result.duration_sec,
        file_size_bytes=file_size_bytes,
    )


def _validate_export_paths(source_path: Path, output_path: Path) -> None:
    if not source_path.exists() or not source_path.is_file():
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_SOURCE_MISSING,
            "元の音声ファイルが見つかりません。音声を読み込み直してください。",
            detail=str(source_path),
        )

    if output_path.exists() and output_path.is_dir():
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_OUTPUT_PATH_INVALID,
            "MMD用WAVの保存先にフォルダが指定されています。",
            detail=str(output_path),
        )

    if source_path.resolve() == output_path.resolve():
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_OUTPUT_PATH_INVALID,
            "元の音声ファイルと同じパスへMMD用WAVを出力することはできません。",
            detail=str(output_path),
        )


def _build_temp_output_path(output_path: Path) -> Path:
    token = uuid.uuid4().hex[:8]
    return output_path.with_name(f"{output_path.stem}_{token}.tmp_mmd.wav")


def _format_runner_failure(result: FfmpegRunResult) -> str:
    stderr = result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
    return f"returncode={result.returncode}, stderr={stderr}"


def _cleanup_partial_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _validate_mmd_wav_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_OUTPUT_FAILED,
            "MMD用WAVファイルが生成されませんでした。",
            detail=str(path),
        )

    data = path.read_bytes()
    if len(data) < 44:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail="WAV header is too short.",
        )

    if data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail="RIFF/WAVE header is missing.",
        )

    first_chunk = data[12:16]
    if first_chunk != b"fmt ":
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"First chunk is not fmt: {first_chunk!r}",
        )

    fmt_size = _read_u32le(data, 16)
    if fmt_size != 16:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"fmt chunk size is {fmt_size}.",
        )

    fmt_start = 20
    audio_format = _read_u16le(data, fmt_start)
    channel_count = _read_u16le(data, fmt_start + 2)
    sample_rate_hz = _read_u32le(data, fmt_start + 4)
    bits_per_sample = _read_u16le(data, fmt_start + 14)

    if audio_format != 1:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"audio format is {audio_format}.",
        )
    if channel_count != MMD_WAV_SPEC.channel_count:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"channel count is {channel_count}.",
        )
    if sample_rate_hz != MMD_WAV_SPEC.sample_rate_hz:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"sample rate is {sample_rate_hz}.",
        )
    if bits_per_sample != 16:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"bits per sample is {bits_per_sample}.",
        )

    data_chunk_size = _find_data_chunk_size(data, 20 + fmt_size)
    if data_chunk_size <= 0:
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail="data chunk is missing or empty.",
        )


def _find_data_chunk_size(data: bytes, offset: int) -> int:
    cursor = offset
    while cursor + 8 <= len(data):
        chunk_id = data[cursor:cursor + 4]
        chunk_size = _read_u32le(data, cursor + 4)
        if chunk_id == b"data":
            return chunk_size
        raise make_convert_error(
            AudioErrorCode.MMD_WAV_VALIDATION_FAILED,
            "MMD用WAVの検証に失敗しました。",
            detail=f"Unexpected chunk before data: {chunk_id!r}",
        )
    return 0


def _read_u16le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _read_u32le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]
