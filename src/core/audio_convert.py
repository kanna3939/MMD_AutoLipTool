from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import logging

from src.core.audio_errors import AudioErrorCode, make_convert_error
from src.core.audio_probe import AudioProbeResult
from src.core.audio_cache import (
    generate_analysis_wav_path,
    ensure_cache_dir_exists,
    cleanup_partial_file,
    get_analysis_wav_dir
)
from src.core.ffmpeg_runner import (
    FfmpegRunResult,
    run_ffmpeg_analysis_wav,
    DEFAULT_FFMPEG_TIMEOUT_SEC
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AnalysisWavSpec:
    codec: str
    sample_rate_hz: int
    channel_count: int

@dataclass(frozen=True)
class AnalysisWavResult:
    source_path: Path
    analysis_wav_path: Path
    spec: AnalysisWavSpec
    duration_sec: float | None
    file_size_bytes: int | None

def convert_to_analysis_wav(
    probe_result: AudioProbeResult,
    ffmpeg_path: str | Path,
    *,
    cache_dir: Path | None = None,
    runner: Callable[..., FfmpegRunResult] | None = None,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> AnalysisWavResult:
    """
    Generate an analysis WAV file using ffmpeg based on the provided probe result.
    Raises AudioConvertError on failure.
    """
    if cache_dir is None:
        cache_dir = get_analysis_wav_dir()
        
    try:
        ensure_cache_dir_exists(cache_dir)
    except OSError as e:
        raise make_convert_error(
            AudioErrorCode.ANALYSIS_WAV_CACHE_DIR_FAILED,
            "解析用音声の保存先フォルダを作成できませんでした。",
            detail=str(e)
        ) from e

    source_path = probe_result.source_path
    output_path = generate_analysis_wav_path(
        source_path=source_path,
        file_size_bytes=probe_result.file_size_bytes,
        cache_dir=cache_dir
    )

    if runner is None:
        runner = run_ffmpeg_analysis_wav

    ffmpeg_path_obj = Path(ffmpeg_path)
    
    try:
        result = runner(
            ffmpeg_path=ffmpeg_path_obj,
            input_path=source_path,
            output_path=output_path,
            timeout_sec=timeout_sec
        )
    except Exception as e:
        # e.g., AudioConvertError from ffmpeg_runner
        cleanup_partial_file(output_path)
        raise

    if result.returncode != 0:
        cleanup_partial_file(output_path)
        stderr_snippet = result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
        raise make_convert_error(
            AudioErrorCode.FFMPEG_EXECUTION_FAILED,
            "解析用音声への変換に失敗しました。",
            detail=f"returncode={result.returncode}, stderr={stderr_snippet}"
        )

    if not output_path.exists() or not output_path.is_file():
        cleanup_partial_file(output_path)
        raise make_convert_error(
            AudioErrorCode.ANALYSIS_WAV_OUTPUT_FAILED,
            "変換後の音声ファイルが生成されませんでした。"
        )

    out_size = output_path.stat().st_size
    if out_size == 0:
        cleanup_partial_file(output_path)
        raise make_convert_error(
            AudioErrorCode.ANALYSIS_WAV_GENERATION_FAILED,
            "変換後の音声ファイルが空です。"
        )

    # Fixed spec for analysis WAV
    spec = AnalysisWavSpec(
        codec="pcm_s16le",
        sample_rate_hz=44100,
        channel_count=1
    )

    return AnalysisWavResult(
        source_path=source_path,
        analysis_wav_path=output_path,
        spec=spec,
        duration_sec=probe_result.duration_sec,
        file_size_bytes=out_size
    )
