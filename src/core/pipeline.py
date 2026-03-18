from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from core.audio_processing import WavAnalysisResult, analyze_wav_file
from core.text_processing import text_to_vowel_sequence
from core.whisper_timing import (
    SpeechTimingAnchor,
    WhisperTimingError,
    recognize_audio_timing,
)
from vmd_writer import VowelTimelinePoint, write_morph_vmd


class PipelineError(ValueError):
    """Recoverable pipeline error for GUI-facing messaging."""


@dataclass(frozen=True)
class PipelineResult:
    text_path: Path
    wav_path: Path
    output_path: Path
    vowels: list[str]
    timeline: list[VowelTimelinePoint]
    wav_analysis: WavAnalysisResult
    timing_anchors: list[SpeechTimingAnchor]
    timing_source: str
    timing_warning: str | None = None


@dataclass(frozen=True)
class VowelTimingPlan:
    vowels: list[str]
    timeline: list[VowelTimelinePoint]
    anchors: list[SpeechTimingAnchor]
    source: str
    warning: str | None = None


def build_even_vowel_timeline(
    vowels: Sequence[str],
    speech_start_sec: float,
    speech_end_sec: float,
) -> list[VowelTimelinePoint]:
    if not vowels:
        raise ValueError("No vowels to allocate.")
    if speech_start_sec < 0 or speech_end_sec < 0:
        raise ValueError("Speech interval must be non-negative.")
    if speech_end_sec < speech_start_sec:
        raise ValueError("speech_end_sec must be >= speech_start_sec.")

    duration_sec = speech_end_sec - speech_start_sec
    count = len(vowels)
    step_sec = duration_sec / count if count else 0.0

    timeline: list[VowelTimelinePoint] = []
    for index, vowel in enumerate(vowels):
        time_sec = speech_start_sec + (step_sec * index)
        timeline.append(VowelTimelinePoint(time_sec=time_sec, vowel=vowel))
    return timeline


def build_anchor_based_vowel_timeline(
    vowels: Sequence[str],
    timing_anchors: Sequence[SpeechTimingAnchor],
    speech_start_sec: float,
    speech_end_sec: float,
) -> list[VowelTimelinePoint]:
    if not vowels:
        raise ValueError("No vowels to allocate.")
    if speech_start_sec < 0 or speech_end_sec < 0:
        raise ValueError("Speech interval must be non-negative.")
    if speech_end_sec < speech_start_sec:
        raise ValueError("speech_end_sec must be >= speech_start_sec.")

    clipped_anchors = _clip_anchors_to_speech_interval(
        timing_anchors=timing_anchors,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
    )
    if not clipped_anchors:
        return build_even_vowel_timeline(
            vowels=vowels,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
        )

    allocation = _allocate_vowels_to_anchors(len(vowels), clipped_anchors)
    timeline: list[VowelTimelinePoint] = []
    vowel_index = 0
    for anchor, count in zip(clipped_anchors, allocation):
        for local_index in range(count):
            if vowel_index >= len(vowels):
                break
            time_sec = _even_time_in_interval(
                start_sec=anchor.start_sec,
                end_sec=anchor.end_sec,
                index=local_index,
                count=count,
            )
            timeline.append(VowelTimelinePoint(time_sec=time_sec, vowel=vowels[vowel_index]))
            vowel_index += 1

    if vowel_index != len(vowels):
        # Safety fallback in case the allocation and generation diverge.
        return build_even_vowel_timeline(
            vowels=vowels,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
        )
    return timeline


def build_vowel_timing_plan(
    *,
    text_content: str,
    wav_path: str | Path,
    wav_analysis: WavAnalysisResult,
    whisper_model_name: str = "small",
) -> VowelTimingPlan:
    vowels = text_to_vowel_sequence(text_content)
    if not vowels:
        raise ValueError("No vowels extracted from TEXT.")
    if not wav_analysis.has_speech:
        raise ValueError("No speech interval detected in WAV.")

    anchors: list[SpeechTimingAnchor] = []
    timing_source = "even_fallback"
    warning: str | None = None

    try:
        whisper_result = recognize_audio_timing(
            wav_path=wav_path,
            model_name=whisper_model_name,
            language="ja",
            fp16=False,
        )
        anchors = _clip_anchors_to_speech_interval(
            timing_anchors=whisper_result.anchors,
            speech_start_sec=wav_analysis.speech_start_sec,
            speech_end_sec=wav_analysis.speech_end_sec,
        )
        if anchors:
            timing_source = f"whisper_{whisper_result.source}"
        else:
            warning = "Whisper returned no anchors inside the detected speech interval."
    except WhisperTimingError as error:
        warning = str(error)

    timeline = build_anchor_based_vowel_timeline(
        vowels=vowels,
        timing_anchors=anchors,
        speech_start_sec=wav_analysis.speech_start_sec,
        speech_end_sec=wav_analysis.speech_end_sec,
    )

    return VowelTimingPlan(
        vowels=vowels,
        timeline=timeline,
        anchors=anchors,
        source=timing_source,
        warning=warning,
    )


def generate_vmd_from_text_wav(
    text_path: str | Path,
    wav_path: str | Path,
    output_path: str | Path,
    *,
    silence_threshold: float = 0.02,
    model_name: str = "AutoLipTool",
) -> PipelineResult:
    text_file = Path(text_path)
    wav_file = Path(wav_path)
    out_file = Path(output_path)

    if not text_file.exists():
        raise PipelineError(f"TEXT file not found: {text_file}")
    if not wav_file.exists():
        raise PipelineError(f"WAV file not found: {wav_file}")

    try:
        text_content = text_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise PipelineError("TEXT file is not valid UTF-8.") from error
    except OSError as error:
        raise PipelineError(f"Failed to read TEXT file: {error}") from error

    try:
        wav_analysis = analyze_wav_file(str(wav_file), silence_threshold=silence_threshold)
    except (ValueError, OSError) as error:
        raise PipelineError(f"Failed to analyze WAV file: {error}") from error

    try:
        timing_plan = build_vowel_timing_plan(
            text_content=text_content,
            wav_path=wav_file,
            wav_analysis=wav_analysis,
            whisper_model_name="small",
        )
    except ValueError as error:
        raise PipelineError(f"Failed to build vowel timeline: {error}") from error

    try:
        write_morph_vmd(output_path=out_file, timeline=timing_plan.timeline, model_name=model_name)
    except OSError as error:
        raise PipelineError(f"Failed to save VMD file: {error}") from error

    return PipelineResult(
        text_path=text_file,
        wav_path=wav_file,
        output_path=out_file,
        vowels=timing_plan.vowels,
        timeline=timing_plan.timeline,
        wav_analysis=wav_analysis,
        timing_anchors=timing_plan.anchors,
        timing_source=timing_plan.source,
        timing_warning=timing_plan.warning,
    )


def _clip_anchors_to_speech_interval(
    timing_anchors: Sequence[SpeechTimingAnchor],
    speech_start_sec: float,
    speech_end_sec: float,
) -> list[SpeechTimingAnchor]:
    clipped: list[SpeechTimingAnchor] = []
    for anchor in sorted(timing_anchors, key=lambda x: x.start_sec):
        start_sec = max(anchor.start_sec, speech_start_sec)
        end_sec = min(anchor.end_sec, speech_end_sec)
        if end_sec <= start_sec:
            continue
        clipped.append(
            SpeechTimingAnchor(
                start_sec=start_sec,
                end_sec=end_sec,
                text=anchor.text,
            )
        )
    return clipped


def _allocate_vowels_to_anchors(
    vowel_count: int,
    anchors: Sequence[SpeechTimingAnchor],
) -> list[int]:
    anchor_count = len(anchors)
    if vowel_count <= 0 or anchor_count <= 0:
        return [0] * anchor_count

    durations = [max(anchor.end_sec - anchor.start_sec, 0.0) for anchor in anchors]

    if vowel_count < anchor_count:
        allocation = [0] * anchor_count
        order = sorted(
            range(anchor_count),
            key=lambda i: (durations[i], -i),
            reverse=True,
        )
        for index in order[:vowel_count]:
            allocation[index] = 1
        return allocation

    allocation = [1] * anchor_count
    remaining = vowel_count - anchor_count
    if remaining == 0:
        return allocation

    duration_sum = sum(durations)
    if duration_sum <= 0:
        weights = [1.0] * anchor_count
    else:
        weights = durations

    weight_sum = sum(weights)
    scaled = [(weight / weight_sum) * remaining for weight in weights]
    floors = [int(value) for value in scaled]

    for index, base in enumerate(floors):
        allocation[index] += base

    leftover = remaining - sum(floors)
    if leftover <= 0:
        return allocation

    fractions = [scaled[i] - floors[i] for i in range(anchor_count)]
    order = sorted(
        range(anchor_count),
        key=lambda i: (fractions[i], weights[i], -i),
        reverse=True,
    )
    for index in order[:leftover]:
        allocation[index] += 1
    return allocation


def _even_time_in_interval(start_sec: float, end_sec: float, index: int, count: int) -> float:
    if count <= 0:
        raise ValueError("count must be > 0")
    if end_sec <= start_sec:
        return start_sec

    step = (end_sec - start_sec) / count
    time_sec = start_sec + (step * (index + 0.5))
    if time_sec < start_sec:
        return start_sec
    if time_sec > end_sec:
        return end_sec
    return time_sec
