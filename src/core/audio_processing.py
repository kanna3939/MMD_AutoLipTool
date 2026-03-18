from dataclasses import dataclass
from math import sqrt
import wave

RMS_WINDOW_MS = 25.0
RMS_HOP_MS = 10.0
RMS_SMOOTHING_FRAMES = 3


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


@dataclass(frozen=True)
class WaveformPreviewData:
    sample_rate_hz: int
    channel_count: int
    duration_sec: float
    samples: list[float]


@dataclass(frozen=True)
class RmsSeriesData:
    sample_rate_hz: int
    channel_count: int
    duration_sec: float
    window_size_samples: int
    hop_size_samples: int
    times_sec: list[float]
    values: list[float]


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


def load_waveform_preview(
    file_path: str,
    max_points: int = 3000,
    stereo_mode: str = "average",
) -> WaveformPreviewData:
    if max_points <= 0:
        raise ValueError("max_points must be > 0")
    if stereo_mode not in ("average", "left"):
        raise ValueError("stereo_mode must be 'average' or 'left'")

    sample_rate_hz, frame_count, channel_count, sample_width, raw_frames = _read_wav_pcm(file_path)

    mono_samples = _decode_mono_samples(
        raw_frames=raw_frames,
        frame_count=frame_count,
        channel_count=channel_count,
        sample_width=sample_width,
        stereo_mode=stereo_mode,
    )
    preview_samples = _downsample_samples(mono_samples, max_points=max_points)

    return WaveformPreviewData(
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        duration_sec=frame_count / sample_rate_hz,
        samples=preview_samples,
    )


def load_rms_series(
    file_path: str,
    *,
    window_ms: float = RMS_WINDOW_MS,
    hop_ms: float = RMS_HOP_MS,
    stereo_mode: str = "average",
    smoothing_frames: int = RMS_SMOOTHING_FRAMES,
) -> RmsSeriesData:
    if window_ms <= 0:
        raise ValueError("window_ms must be > 0")
    if hop_ms <= 0:
        raise ValueError("hop_ms must be > 0")
    if stereo_mode not in ("average", "left"):
        raise ValueError("stereo_mode must be 'average' or 'left'")
    if smoothing_frames <= 0:
        raise ValueError("smoothing_frames must be > 0")

    sample_rate_hz, frame_count, channel_count, sample_width, raw_frames = _read_wav_pcm(file_path)
    mono_samples = _decode_mono_samples(
        raw_frames=raw_frames,
        frame_count=frame_count,
        channel_count=channel_count,
        sample_width=sample_width,
        stereo_mode=stereo_mode,
    )

    window_size_samples = max(1, int(round(sample_rate_hz * (window_ms / 1000.0))))
    hop_size_samples = max(1, int(round(sample_rate_hz * (hop_ms / 1000.0))))
    times_sec, values = _compute_rms_windows(
        samples=mono_samples,
        sample_rate_hz=sample_rate_hz,
        window_size_samples=window_size_samples,
        hop_size_samples=hop_size_samples,
    )

    if smoothing_frames > 1 and values:
        values = _smooth_series(values, smoothing_frames)

    return RmsSeriesData(
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        duration_sec=frame_count / sample_rate_hz,
        window_size_samples=window_size_samples,
        hop_size_samples=hop_size_samples,
        times_sec=times_sec,
        values=values,
    )


def _read_wav_pcm(file_path: str) -> tuple[int, int, int, int, bytes]:
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

    return sample_rate_hz, frame_count, channel_count, sample_width, raw_frames


def _compute_rms_windows(
    *,
    samples: list[float],
    sample_rate_hz: int,
    window_size_samples: int,
    hop_size_samples: int,
) -> tuple[list[float], list[float]]:
    if not samples:
        return [], []

    times_sec: list[float] = []
    values: list[float] = []
    sample_count = len(samples)

    for start in range(0, sample_count, hop_size_samples):
        end = min(start + window_size_samples, sample_count)
        if end <= start:
            break

        window = samples[start:end]
        mean_square = sum(sample * sample for sample in window) / len(window)
        rms_value = sqrt(mean_square)
        center_sample = start + (len(window) * 0.5)
        times_sec.append(center_sample / sample_rate_hz)
        values.append(rms_value)

        if end >= sample_count:
            break

    return times_sec, values


def _smooth_series(values: list[float], smoothing_frames: int) -> list[float]:
    if smoothing_frames <= 1 or not values:
        return values

    half = smoothing_frames // 2
    smoothed: list[float] = []
    for index in range(len(values)):
        start = max(0, index - half)
        end = min(len(values), index + half + 1)
        chunk = values[start:end]
        smoothed.append(sum(chunk) / len(chunk))
    return smoothed


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


def _decode_mono_samples(
    raw_frames: bytes,
    frame_count: int,
    channel_count: int,
    sample_width: int,
    stereo_mode: str,
) -> list[float]:
    frame_size = sample_width * channel_count
    available_frames = min(frame_count, len(raw_frames) // frame_size)
    if available_frames <= 0:
        return []

    scale = _pcm_scale(sample_width)
    samples: list[float] = []
    offset = 0

    for _ in range(available_frames):
        frame = raw_frames[offset : offset + frame_size]
        offset += frame_size

        channel_values: list[int] = []
        for channel_index in range(channel_count):
            start = channel_index * sample_width
            end = start + sample_width
            channel_values.append(_decode_pcm_sample(frame[start:end], sample_width=sample_width))

        if channel_count == 1 or stereo_mode == "left":
            mono = channel_values[0]
        else:
            mono = int(sum(channel_values) / channel_count)

        normalized = mono / scale if scale else 0.0
        if normalized > 1.0:
            normalized = 1.0
        if normalized < -1.0:
            normalized = -1.0
        samples.append(normalized)

    return samples


def _downsample_samples(samples: list[float], max_points: int) -> list[float]:
    if len(samples) <= max_points:
        return samples

    sampled: list[float] = []
    step = len(samples) / max_points
    for index in range(max_points):
        src_index = int(index * step)
        if src_index >= len(samples):
            src_index = len(samples) - 1
        sampled.append(samples[src_index])
    return sampled


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
