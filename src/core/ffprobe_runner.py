import subprocess
from dataclasses import dataclass
from pathlib import Path
from src.core.audio_errors import AudioErrorCode, make_audio_error

@dataclass(frozen=True)
class FfprobeRunResult:
    stdout: str
    stderr: str
    returncode: int

def run_ffprobe_json(
    ffprobe_path: Path,
    input_path: Path,
    timeout_sec: float = 30.0,
) -> FfprobeRunResult:
    """
    Run ffprobe and return the result.
    Raises AudioProbeError on FileNotFoundError, PermissionError, TimeoutExpired.
    """
    cmd = [
        str(ffprobe_path),
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(input_path),
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
        return FfprobeRunResult(
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode
        )
        
    except FileNotFoundError as e:
        raise make_audio_error(
            code=AudioErrorCode.FFPROBE_NOT_FOUND,
            message="ffprobe.exe が見つかりません。",
            detail=str(e)
        ) from e
    except PermissionError as e:
        raise make_audio_error(
            code=AudioErrorCode.FFPROBE_PERMISSION_ERROR,
            message="ffprobe.exe の実行権限がありません。",
            detail=str(e)
        ) from e
    except subprocess.TimeoutExpired as e:
        raise make_audio_error(
            code=AudioErrorCode.FFPROBE_TIMEOUT,
            message=f"音声ファイルの解析がタイムアウト（{timeout_sec}秒）しました。",
            detail=f"Timeout: {e.timeout}s"
        ) from e

def run_ffprobe_json_cancellable(
    ffprobe_path: Path,
    input_path: Path,
    timeout_sec: float = 30.0,
    cancel_token=None,
) -> FfprobeRunResult:
    cmd = [
        str(ffprobe_path),
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(input_path),
    ]

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
        return FfprobeRunResult(
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode
        )

    except FileNotFoundError as e:
        raise make_audio_error(
            code=AudioErrorCode.FFPROBE_NOT_FOUND,
            message="ffprobe.exe が見つかりません。",
            detail=str(e)
        ) from e
    except PermissionError as e:
        raise make_audio_error(
            code=AudioErrorCode.FFPROBE_PERMISSION_ERROR,
            message="ffprobe.exe の実行権限がありません。",
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
        raise make_audio_error(
            code=AudioErrorCode.FFPROBE_TIMEOUT,
            message=f"音声ファイルの解析がタイムアウト（{timeout_sec}秒）しました。",
            detail=f"Timeout: {e.timeout}s"
        ) from e
    finally:
        if process is not None and cancel_token is not None:
            cancel_token.clear_process(process)
