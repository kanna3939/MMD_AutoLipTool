import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from src.core.audio_errors import AudioErrorCode, make_audio_error
from src.core.audio_input import detect_audio_input_kind
from src.core.ffprobe_runner import FfprobeRunResult, run_ffprobe_json

logger = logging.getLogger(__name__)

MAX_AUDIO_FILE_SIZE_BYTES = 500 * 1024 * 1024
MAX_AUDIO_DURATION_SEC = 15 * 60.0
DEFAULT_FFPROBE_TIMEOUT_SEC = 30.0

@dataclass(frozen=True)
class AudioStreamInfo:
    codec_name: str | None
    sample_rate_hz: int | None
    channel_count: int | None
    duration_sec: float | None

@dataclass(frozen=True)
class AudioProbeResult:
    source_path: Path
    file_size_bytes: int
    duration_sec: float
    format_name: str | None
    audio_stream: AudioStreamInfo

def probe_audio_file(
    input_path: str | Path,
    ffprobe_path: str | Path,
    *,
    runner: Callable[..., FfprobeRunResult] | None = None,
    timeout_sec: float = DEFAULT_FFPROBE_TIMEOUT_SEC,
) -> AudioProbeResult:
    """
    Inspect an audio file using ffprobe.
    Raises AudioProbeError on failure.
    """
    path_obj = Path(input_path)
    
    # 1. Existence check
    if not path_obj.exists():
        raise make_audio_error(AudioErrorCode.AUDIO_FILE_NOT_FOUND, f"ファイルが見つかりません: {path_obj.name}")
        
    # 2. Directory check
    if path_obj.is_dir():
        raise make_audio_error(AudioErrorCode.AUDIO_PATH_IS_DIRECTORY, f"フォルダが指定されています: {path_obj.name}")
        
    # 3. File size check
    file_size_bytes = path_obj.stat().st_size
    if file_size_bytes > MAX_AUDIO_FILE_SIZE_BYTES:
        raise make_audio_error(
            AudioErrorCode.AUDIO_FILE_TOO_LARGE,
            "ファイルサイズが500MBを超えています。",
            detail=f"{file_size_bytes} bytes"
        )
        
    # 4. Extension check
    try:
        detect_audio_input_kind(path_obj)
    except ValueError as e:
        raise make_audio_error(
            AudioErrorCode.UNSUPPORTED_AUDIO_EXTENSION,
            "対応していない音声ファイル形式です。",
            detail=str(e)
        ) from e

    # 5. Run ffprobe
    if runner is None:
        runner = run_ffprobe_json
        
    result = runner(
        ffprobe_path=Path(ffprobe_path),
        input_path=path_obj,
        timeout_sec=timeout_sec
    )
    
    if result.returncode != 0:
        # truncate stderr for message to avoid huge dialogs
        stderr_snippet = result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
        raise make_audio_error(
            AudioErrorCode.FFPROBE_EXECUTION_FAILED,
            "音声ファイルの解析に失敗しました。",
            detail=f"returncode={result.returncode}, stderr={stderr_snippet}"
        )
        
    # 6. Parse JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise make_audio_error(
            AudioErrorCode.FFPROBE_INVALID_JSON,
            "音声ファイルの解析結果を読み取れませんでした。",
            detail=f"JSONDecodeError: {str(e)}"
        ) from e

    # 7. Extract streams and format
    streams = data.get("streams", [])
    format_info = data.get("format", {})
    
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if not audio_streams:
        raise make_audio_error(
            AudioErrorCode.AUDIO_STREAM_NOT_FOUND,
            "ファイルに音声ストリームが含まれていません。"
        )
        
    audio_stream = audio_streams[0]
    
    # 8. Extract duration
    duration_str = format_info.get("duration")
    if duration_str is None:
        duration_str = audio_stream.get("duration")
        
    if duration_str is None:
        raise make_audio_error(
            AudioErrorCode.AUDIO_DURATION_MISSING,
            "音声の長さを取得できませんでした。"
        )
        
    try:
        duration_sec = float(duration_str)
    except ValueError as e:
        raise make_audio_error(
            AudioErrorCode.AUDIO_DURATION_MISSING,
            "音声の長さの形式が不正です。",
            detail=str(e)
        ) from e
        
    # 9. Duration limits check
    if duration_sec > MAX_AUDIO_DURATION_SEC:
        raise make_audio_error(
            AudioErrorCode.AUDIO_DURATION_TOO_LONG,
            "音声の長さが15分を超えています。",
            detail=f"{duration_sec} sec"
        )

    def _parse_int(val: Any) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except ValueError:
            return None

    def _parse_float(val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    stream_info = AudioStreamInfo(
        codec_name=audio_stream.get("codec_name"),
        sample_rate_hz=_parse_int(audio_stream.get("sample_rate")),
        channel_count=_parse_int(audio_stream.get("channels")),
        duration_sec=_parse_float(audio_stream.get("duration")),
    )
    
    return AudioProbeResult(
        source_path=path_obj,
        file_size_bytes=file_size_bytes,
        duration_sec=duration_sec,
        format_name=format_info.get("format_name"),
        audio_stream=stream_info
    )
