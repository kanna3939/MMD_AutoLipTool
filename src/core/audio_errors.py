from dataclasses import dataclass
from enum import Enum

class AudioErrorCode(str, Enum):
    AUDIO_FILE_NOT_FOUND = "audio_file_not_found"
    AUDIO_PATH_IS_DIRECTORY = "audio_path_is_directory"
    AUDIO_FILE_TOO_LARGE = "audio_file_too_large"
    UNSUPPORTED_AUDIO_EXTENSION = "unsupported_audio_extension"
    FFPROBE_NOT_FOUND = "ffprobe_not_found"
    FFPROBE_PERMISSION_ERROR = "ffprobe_permission_error"
    FFPROBE_TIMEOUT = "ffprobe_timeout"
    FFPROBE_EXECUTION_FAILED = "ffprobe_execution_failed"
    FFPROBE_INVALID_JSON = "ffprobe_invalid_json"
    AUDIO_STREAM_NOT_FOUND = "audio_stream_not_found"
    AUDIO_DURATION_MISSING = "audio_duration_missing"
    AUDIO_DURATION_TOO_LONG = "audio_duration_too_long"
    AUDIO_PROBE_FAILED = "audio_probe_failed"

    FFMPEG_NOT_FOUND = "ffmpeg_not_found"
    FFMPEG_PERMISSION_ERROR = "ffmpeg_permission_error"
    FFMPEG_TIMEOUT = "ffmpeg_timeout"
    FFMPEG_EXECUTION_FAILED = "ffmpeg_execution_failed"

    ANALYSIS_WAV_CACHE_DIR_FAILED = "analysis_wav_cache_dir_failed"
    ANALYSIS_WAV_OUTPUT_FAILED = "analysis_wav_output_failed"
    ANALYSIS_WAV_CLEANUP_FAILED = "analysis_wav_cleanup_failed"
    ANALYSIS_WAV_GENERATION_FAILED = "analysis_wav_generation_failed"

    MMD_WAV_SOURCE_MISSING = "mmd_wav_source_missing"
    MMD_WAV_OUTPUT_PATH_INVALID = "mmd_wav_output_path_invalid"
    MMD_WAV_PERMISSION_ERROR = "mmd_wav_permission_error"
    MMD_WAV_EXPORT_FAILED = "mmd_wav_export_failed"
    MMD_WAV_OUTPUT_FAILED = "mmd_wav_output_failed"
    MMD_WAV_VALIDATION_FAILED = "mmd_wav_validation_failed"
    MMD_WAV_CLEANUP_FAILED = "mmd_wav_cleanup_failed"
    MMD_WAV_REPLACE_FAILED = "mmd_wav_replace_failed"

@dataclass(frozen=True)
class AudioErrorInfo:
    code: AudioErrorCode
    message: str
    detail: str | None = None

class AudioProbeError(Exception):
    def __init__(self, info: AudioErrorInfo):
        self.info = info
        super().__init__(info.message)

def make_audio_error(
    code: AudioErrorCode,
    message: str,
    detail: str | None = None,
) -> AudioProbeError:
    return AudioProbeError(AudioErrorInfo(code=code, message=message, detail=detail))

class AudioConvertError(Exception):
    def __init__(self, info: AudioErrorInfo):
        self.info = info
        super().__init__(info.message)

def make_convert_error(
    code: AudioErrorCode,
    message: str,
    detail: str | None = None,
) -> AudioConvertError:
    return AudioConvertError(AudioErrorInfo(code=code, message=message, detail=detail))
