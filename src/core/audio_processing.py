from dataclasses import dataclass
import wave


@dataclass(frozen=True)
class WavAnalysisResult:
    sample_rate_hz: int
    frame_count: int
    channel_count: int
    duration_sec: float
    leading_silence_end_sec: float
    trailing_silence_start_sec: float
    speech_start_sec: float
    speech_end_sec: float
    has_speech: bool


def analyze_wav_file(file_path: str, silence_threshold: float = 0.02) -> WavAnalysisResult:
    if not 0.0 <= silence_threshold <= 1.0:
        raise ValueError("silence_threshold must be between 0.0 and 1.0")

    try:
        with wave.open(file_path, "rb") as wav_file:
            if wav_file.getcomptype() != "NONE":
                raise ValueError("Only uncompressed PCM WAV is supported")

            sample_rate_hz = wav_file.getframerate()
            if sample_rate_hz <= 0:
                raise ValueError("Invalid WAV sample rate")

            frame_count = wav_file.getnframes()
            channel_count = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            if sample_width not in (1, 2, 3, 4):
                raise ValueError(f"Unsupported sample width: {sample_width} bytes")

            raw_frames = wav_file.readframes(frame_count)
    except (wave.Error, EOFError) as error:
        raise ValueError(f"Invalid WAV file: {error}") from error

    duration_sec = frame_count / sample_rate_hz
    speech_range = _detect_speech_frame_range(
        raw_frames=raw_frames,
        frame_count=frame_count,
        channel_count=channel_count,
        sample_width=sample_width,
        silence_threshold=silence_threshold,
    )

    if speech_range is None:
        return WavAnalysisResult(
            sample_rate_hz=sample_rate_hz,
            frame_count=frame_count,
            channel_count=channel_count,
            duration_sec=duration_sec,
            leading_silence_end_sec=duration_sec,
            trailing_silence_start_sec=0.0,
            speech_start_sec=0.0,
            speech_end_sec=0.0,
            has_speech=False,
        )

    first_speech_frame, last_speech_frame = speech_range
    speech_start_sec = first_speech_frame / sample_rate_hz
    speech_end_sec = (last_speech_frame + 1) / sample_rate_hz

    return WavAnalysisResult(
        sample_rate_hz=sample_rate_hz,
        frame_count=frame_count,
        channel_count=channel_count,
        duration_sec=duration_sec,
        leading_silence_end_sec=speech_start_sec,
        trailing_silence_start_sec=speech_end_sec,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        has_speech=True,
    )


def _detect_speech_frame_range(
    raw_frames: bytes,
    frame_count: int,
    channel_count: int,
    sample_width: int,
    silence_threshold: float,
) -> tuple[int, int] | None:
    frame_size = sample_width * channel_count
    available_frames = min(frame_count, len(raw_frames) // frame_size)
    if available_frames <= 0:
        return None

    first_speech_frame: int | None = None
    last_speech_frame: int | None = None
    offset = 0

    for frame_index in range(available_frames):
        frame = raw_frames[offset : offset + frame_size]
        offset += frame_size
        normalized_peak = _frame_peak(frame, channel_count=channel_count, sample_width=sample_width)
        if normalized_peak > silence_threshold:
            if first_speech_frame is None:
                first_speech_frame = frame_index
            last_speech_frame = frame_index

    if first_speech_frame is None or last_speech_frame is None:
        return None
    return first_speech_frame, last_speech_frame


def _frame_peak(frame: bytes, channel_count: int, sample_width: int) -> float:
    max_abs_value = 0
    scale = _pcm_scale(sample_width)

    for channel_index in range(channel_count):
        start = channel_index * sample_width
        end = start + sample_width
        sample_value = _decode_pcm_sample(frame[start:end], sample_width=sample_width)
        abs_value = abs(sample_value)
        if abs_value > max_abs_value:
            max_abs_value = abs_value

    return max_abs_value / scale if scale else 0.0


def _pcm_scale(sample_width: int) -> int:
    if sample_width == 1:
        return 128
    if sample_width == 2:
        return 32768
    if sample_width == 3:
        return 8388608
    if sample_width == 4:
        return 2147483648
    raise ValueError(f"Unsupported sample width: {sample_width} bytes")


def _decode_pcm_sample(sample_bytes: bytes, sample_width: int) -> int:
    if sample_width == 1:
        # 8-bit PCM is unsigned.
        return sample_bytes[0] - 128

    if sample_width == 2:
        return int.from_bytes(sample_bytes, byteorder="little", signed=True)

    if sample_width == 3:
        unsigned_value = int.from_bytes(sample_bytes, byteorder="little", signed=False)
        if unsigned_value & 0x800000:
            return unsigned_value - 0x1000000
        return unsigned_value

    if sample_width == 4:
        return int.from_bytes(sample_bytes, byteorder="little", signed=True)

    raise ValueError(f"Unsupported sample width: {sample_width} bytes")
