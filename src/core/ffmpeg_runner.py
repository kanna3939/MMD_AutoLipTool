import subprocess
from dataclasses import dataclass
from pathlib import Path
from src.core.audio_errors import AudioErrorCode, make_convert_error

DEFAULT_FFMPEG_TIMEOUT_SEC = 300.0

@dataclass(frozen=True)
class FfmpegRunResult:
    stdout: str
    stderr: str
    returncode: int

def _run_ffmpeg_pcm_wav(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    channel_count: int,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> FfmpegRunResult:
    cmd = [
        str(ffmpeg_path),
        "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", str(channel_count),
        str(output_path),
    ]

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout_sec,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return FfmpegRunResult(
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode
        )

    except FileNotFoundError as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_NOT_FOUND,
            message="ffmpeg.exe が見つかりません。",
            detail=str(e)
        ) from e
    except PermissionError as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_PERMISSION_ERROR,
            message="ffmpeg.exe の実行権限がありません。",
            detail=str(e)
        ) from e
    except subprocess.TimeoutExpired as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_TIMEOUT,
            message=f"音声の変換処理がタイムアウト（{timeout_sec}秒）しました。",
            detail=f"Timeout: {e.timeout}s"
        ) from e

def _run_ffmpeg_cmd_cancellable(
    cmd: list[str],
    timeout_sec: float,
    cancel_token=None,
) -> FfmpegRunResult:
    process = None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        if cancel_token is not None:
            cancel_token.register_process(process)

        stdout, stderr = process.communicate(timeout=timeout_sec)
        return FfmpegRunResult(
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode
        )

    except FileNotFoundError as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_NOT_FOUND,
            message="ffmpeg.exe が見つかりません。",
            detail=str(e)
        ) from e
    except PermissionError as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_PERMISSION_ERROR,
            message="ffmpeg.exe の実行権限がありません。",
            detail=str(e)
        ) from e
    except subprocess.TimeoutExpired as e:
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=2.0)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_TIMEOUT,
            message=f"音声の変換処理がタイムアウト（{timeout_sec}秒）しました。",
            detail=f"Timeout: {e.timeout}s"
        ) from e
    finally:
        if process is not None and cancel_token is not None:
            cancel_token.clear_process(process)

def _build_mmd_wav_filter_args(source_channel_count: int | None) -> list[str]:
    if source_channel_count == 1:
        return ["-filter:a", "pan=stereo|c0=c0|c1=c0"]
    if source_channel_count is not None and source_channel_count >= 2:
        return ["-filter:a", "pan=stereo|c0=c0|c1=c1"]
    return []

def run_ffmpeg_analysis_wav(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> FfmpegRunResult:
    """
    Run ffmpeg to generate analysis WAV (PCM 16-bit 44.1kHz mono).
    Raises AudioConvertError on failure.
    """
    return _run_ffmpeg_pcm_wav(
        ffmpeg_path=ffmpeg_path,
        input_path=input_path,
        output_path=output_path,
        channel_count=1,
        timeout_sec=timeout_sec,
    )

def run_ffmpeg_analysis_wav_cancellable(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
    cancel_token=None,
) -> FfmpegRunResult:
    cmd = [
        str(ffmpeg_path),
        "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        str(output_path),
    ]
    return _run_ffmpeg_cmd_cancellable(cmd, timeout_sec, cancel_token=cancel_token)

def run_ffmpeg_mmd_wav(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
    source_channel_count: int | None = None,
) -> FfmpegRunResult:
    """
    Run ffmpeg to generate MMD-use WAV (PCM 16-bit 44.1kHz stereo).
    Raises AudioConvertError on process startup/timeout failures.
    """
    cmd = [
        str(ffmpeg_path),
        "-y",
        "-i", str(input_path),
        "-vn",
    ]
    cmd.extend(_build_mmd_wav_filter_args(source_channel_count))
    cmd.extend([
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-bitexact",
        str(output_path),
    ])

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout_sec,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return FfmpegRunResult(
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode
        )

    except FileNotFoundError as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_NOT_FOUND,
            message="ffmpeg.exe が見つかりません。",
            detail=str(e)
        ) from e
    except PermissionError as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_PERMISSION_ERROR,
            message="ffmpeg.exe の実行権限がありません。",
            detail=str(e)
        ) from e
    except subprocess.TimeoutExpired as e:
        raise make_convert_error(
            code=AudioErrorCode.FFMPEG_TIMEOUT,
            message=f"音声の変換処理がタイムアウト（{timeout_sec}秒）しました。",
            detail=f"Timeout: {e.timeout}s"
        ) from e

def run_ffmpeg_mmd_wav_cancellable(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
    source_channel_count: int | None = None,
    cancel_token=None,
) -> FfmpegRunResult:
    cmd = [
        str(ffmpeg_path),
        "-y",
        "-i", str(input_path),
        "-vn",
    ]
    cmd.extend(_build_mmd_wav_filter_args(source_channel_count))
    cmd.extend([
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-bitexact",
        str(output_path),
    ])
    return _run_ffmpeg_cmd_cancellable(cmd, timeout_sec, cancel_token=cancel_token)
