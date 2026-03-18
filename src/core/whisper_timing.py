from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


class WhisperTimingError(ValueError):
    """Recoverable error while extracting timing anchors with Whisper."""


@dataclass(frozen=True)
class SpeechTimingAnchor:
    start_sec: float
    end_sec: float
    text: str


@dataclass(frozen=True)
class WhisperTimingResult:
    anchors: list[SpeechTimingAnchor]
    raw_result: dict[str, Any]
    source: str


def recognize_audio(
    wav_path: str | Path,
    *,
    model_name: str = "small",
    language: str = "ja",
    fp16: bool = False,
    word_timestamps: bool = True,
) -> dict[str, Any]:
    """Run Whisper transcription and return the raw result dict."""
    model = _load_whisper_model(model_name)
    path = Path(wav_path)
    if not path.exists():
        raise WhisperTimingError(f"WAV file not found: {path}")

    try:
        result = model.transcribe(
            str(path),
            language=language,
            fp16=fp16,
            word_timestamps=word_timestamps,
        )
    except Exception as error:
        raise WhisperTimingError(f"Whisper transcription failed: {error}") from error

    if not isinstance(result, dict):
        raise WhisperTimingError("Whisper transcription returned an unexpected result type.")
    return result


def extract_timing_anchors(result: dict[str, Any]) -> list[SpeechTimingAnchor]:
    """Extract timing anchors from a Whisper result (words first, then segments)."""
    anchors = _extract_word_anchors(result)
    if anchors:
        return anchors
    return _extract_segment_anchors(result)


def recognize_audio_timing(
    wav_path: str | Path,
    *,
    model_name: str = "small",
    language: str = "ja",
    fp16: bool = False,
) -> WhisperTimingResult:
    """
    Recognize WAV and return usable timing anchors.

    Priority:
    1) word timestamps
    2) segment timestamps fallback
    """
    first_error: Exception | None = None

    try:
        result_with_words = recognize_audio(
            wav_path,
            model_name=model_name,
            language=language,
            fp16=fp16,
            word_timestamps=True,
        )
        word_anchors = _extract_word_anchors(result_with_words)
        segment_anchors_from_word_run = _extract_segment_anchors(result_with_words)
        if word_anchors:
            # If words are too sparse while segments exist, prefer segment anchors
            # to avoid near-even distribution over a single long interval.
            if (
                len(word_anchors) <= 1
                and len(segment_anchors_from_word_run) > len(word_anchors)
            ):
                return WhisperTimingResult(
                    anchors=segment_anchors_from_word_run,
                    raw_result=result_with_words,
                    source="segments",
                )
            return WhisperTimingResult(
                anchors=word_anchors,
                raw_result=result_with_words,
                source="words",
            )
        if segment_anchors_from_word_run:
            return WhisperTimingResult(
                anchors=segment_anchors_from_word_run,
                raw_result=result_with_words,
                source="segments",
            )
    except Exception as error:
        first_error = error

    try:
        result_with_segments = recognize_audio(
            wav_path,
            model_name=model_name,
            language=language,
            fp16=fp16,
            word_timestamps=False,
        )
        segment_anchors = _extract_segment_anchors(result_with_segments)
        if segment_anchors:
            return WhisperTimingResult(
                anchors=segment_anchors,
                raw_result=result_with_segments,
                source="segments",
            )
    except Exception as error:
        if first_error is None:
            first_error = error

    if first_error is not None:
        raise WhisperTimingError(f"Failed to get timing anchors from Whisper: {first_error}") from first_error
    raise WhisperTimingError("Whisper returned no usable timing anchors.")


@lru_cache(maxsize=2)
def _load_whisper_model(model_name: str):
    try:
        import whisper
    except Exception as error:
        raise WhisperTimingError(f"Failed to import whisper: {error}") from error

    try:
        return whisper.load_model(model_name)
    except Exception as error:
        raise WhisperTimingError(f"Failed to load Whisper model '{model_name}': {error}") from error


def _extract_word_anchors(result: dict[str, Any]) -> list[SpeechTimingAnchor]:
    segments = result.get("segments")
    if not isinstance(segments, list):
        return []

    anchors: list[SpeechTimingAnchor] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        words = segment.get("words")
        if not isinstance(words, list):
            continue
        for word in words:
            if not isinstance(word, dict):
                continue
            anchor = _anchor_from_entry(
                start=word.get("start"),
                end=word.get("end"),
                text=word.get("word", ""),
            )
            if anchor is not None:
                anchors.append(anchor)
    return anchors


def _extract_segment_anchors(result: dict[str, Any]) -> list[SpeechTimingAnchor]:
    segments = result.get("segments")
    if not isinstance(segments, list):
        return []

    anchors: list[SpeechTimingAnchor] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        anchor = _anchor_from_entry(
            start=segment.get("start"),
            end=segment.get("end"),
            text=segment.get("text", ""),
        )
        if anchor is not None:
            anchors.append(anchor)
    return anchors


def _anchor_from_entry(start: Any, end: Any, text: Any) -> SpeechTimingAnchor | None:
    try:
        start_sec = float(start)
        end_sec = float(end)
    except (TypeError, ValueError):
        return None

    if start_sec < 0:
        start_sec = 0.0
    if end_sec < start_sec:
        return None
    if end_sec == start_sec:
        return None

    text_value = str(text).strip()
    return SpeechTimingAnchor(start_sec=start_sec, end_sec=end_sec, text=text_value)
