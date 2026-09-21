from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.ffmpeg_locator import locate_ffmpeg_tools
from src.core.whisper_model_runtime import (
    ModelIdentity,
    WhisperModelSession,
    classify_whisper_failure,
)


class WhisperTimingError(ValueError):
    """Recoverable error while extracting timing anchors with Whisper."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "whisper_timing_failed",
        failure_class: str = "transcribe_failure",
    ) -> None:
        self.code = code
        self.failure_class = failure_class
        super().__init__(message)


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
    model_identity: ModelIdentity | None = None


@dataclass(frozen=True)
class TranscriptionTextResult:
    text: str
    source: str


def recognize_audio(
    wav_path: str | Path,
    *,
    model_session: WhisperModelSession | None = None,
    language: str = "ja",
    fp16: bool = False,
    word_timestamps: bool = True,
) -> dict[str, Any]:
    """Run Whisper transcription through a verified runtime session only."""
    if not isinstance(model_session, WhisperModelSession):
        raise WhisperTimingError(
            "A verified Whisper model session is required.",
            code="model_request_missing",
            failure_class="model_unavailable",
        )
    model = model_session.model
    path = Path(wav_path)
    if not path.exists():
        raise WhisperTimingError(
            f"WAV file not found: {path}",
            code="audio_input_missing",
            failure_class="transcribe_failure",
        )

    try:
        with _prepend_located_ffmpeg_to_path():
            result = model.transcribe(
                str(path),
                language=language,
                fp16=fp16,
                word_timestamps=word_timestamps,
            )
    except Exception as error:
        failure_class, code = classify_whisper_failure(error)
        if failure_class == "transcribe_failure":
            code = "whisper_transcribe_failed"
        raise WhisperTimingError(
            f"Whisper transcription failed: {error}",
            code=code,
            failure_class=failure_class,
        ) from error

    if not isinstance(result, dict):
        raise WhisperTimingError(
            "Whisper transcription returned an unexpected result type.",
            code="whisper_result_invalid",
            failure_class="transcribe_failure",
        )
    return result


@contextmanager
def _prepend_located_ffmpeg_to_path():
    """
    Ensure openai-whisper can find ffmpeg when the app uses repo-local FFmpeg/bin.
    """
    tools = locate_ffmpeg_tools()
    ffmpeg_path = tools.ffmpeg.path
    if ffmpeg_path is None:
        yield
        return

    ffmpeg_dir = str(ffmpeg_path.parent)
    original_path = os.environ.get("PATH", "")
    path_parts = original_path.split(os.pathsep) if original_path else []
    if ffmpeg_dir in path_parts:
        yield
        return

    os.environ["PATH"] = ffmpeg_dir + (os.pathsep + original_path if original_path else "")
    try:
        yield
    finally:
        os.environ["PATH"] = original_path


def extract_transcription_text(result: dict[str, Any]) -> TranscriptionTextResult:
    """Extract the initial text body for voice-only input from a Whisper result."""
    segment_texts = _extract_segment_texts(result)
    if segment_texts:
        return TranscriptionTextResult(text="".join(segment_texts), source="segments")

    raw_text = result.get("text")
    if isinstance(raw_text, str):
        text = raw_text.strip()
        if text:
            return TranscriptionTextResult(text=text, source="raw_text")

    raise WhisperTimingError(
        "Whisper returned no usable transcription text.",
        code="whisper_result_invalid",
        failure_class="none",
    )


def extract_timing_anchors(result: dict[str, Any]) -> list[SpeechTimingAnchor]:
    """Extract timing anchors from a Whisper result (words first, then segments)."""
    anchors = _extract_word_anchors(result)
    if anchors:
        return anchors
    return _extract_segment_anchors(result)


def recognize_audio_timing(
    wav_path: str | Path,
    *,
    model_session: WhisperModelSession | None = None,
    language: str = "ja",
    fp16: bool = False,
) -> WhisperTimingResult:
    """
    Recognize WAV and return usable timing anchors.

    Priority:
    1) word timestamps
    2) segment timestamps fallback
    """
    if not isinstance(model_session, WhisperModelSession):
        raise WhisperTimingError(
            "A verified Whisper model session is required.",
            code="model_request_missing",
            failure_class="model_unavailable",
        )

    result_with_words = recognize_audio(
        wav_path,
        model_session=model_session,
        language=language,
        fp16=fp16,
        word_timestamps=True,
    )
    word_anchors = _extract_word_anchors(result_with_words)
    segment_anchors_from_word_run = _extract_segment_anchors(result_with_words)
    if word_anchors:
        # If words are too sparse while segments exist, prefer segment anchors
        # to avoid near-even distribution over a single long interval.
        if len(word_anchors) <= 1 and len(segment_anchors_from_word_run) > len(word_anchors):
            return WhisperTimingResult(
                anchors=segment_anchors_from_word_run,
                raw_result=result_with_words,
                source="segments",
                model_identity=model_session.identity,
            )
        return WhisperTimingResult(
            anchors=word_anchors,
            raw_result=result_with_words,
            source="words",
            model_identity=model_session.identity,
        )
    if segment_anchors_from_word_run:
        return WhisperTimingResult(
            anchors=segment_anchors_from_word_run,
            raw_result=result_with_words,
            source="segments",
            model_identity=model_session.identity,
        )

    # A valid result with no anchors is the only condition that permits the
    # segment-only retry.  Loader, device, memory, transcribe, FFmpeg, and
    # network exceptions have already escaped above and are never retried.
    result_with_segments = recognize_audio(
        wav_path,
        model_session=model_session,
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
            model_identity=model_session.identity,
        )
    raise WhisperTimingError(
        "Whisper returned no usable timing anchors.",
        code="whisper_no_segments",
        failure_class="none",
    )


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


def _extract_segment_texts(result: dict[str, Any]) -> list[str]:
    segments = result.get("segments")
    if not isinstance(segments, list):
        return []

    texts: list[str] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        text = segment.get("text")
        if not isinstance(text, str):
            continue
        text_value = text.strip()
        if text_value:
            texts.append(text_value)
    return texts


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
