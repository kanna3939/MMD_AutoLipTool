from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from core.audio_processing import WavAnalysisResult, analyze_wav_file
from core.text_processing import text_to_vowel_sequence
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

    vowels = text_to_vowel_sequence(text_content)
    if not vowels:
        raise PipelineError("No vowels extracted from TEXT.")

    try:
        wav_analysis = analyze_wav_file(str(wav_file), silence_threshold=silence_threshold)
    except (ValueError, OSError) as error:
        raise PipelineError(f"Failed to analyze WAV file: {error}") from error
    if not wav_analysis.has_speech:
        raise PipelineError("No speech interval detected in WAV.")

    try:
        timeline = build_even_vowel_timeline(
            vowels=vowels,
            speech_start_sec=wav_analysis.speech_start_sec,
            speech_end_sec=wav_analysis.speech_end_sec,
        )
    except ValueError as error:
        raise PipelineError(f"Failed to build vowel timeline: {error}") from error

    try:
        write_morph_vmd(output_path=out_file, timeline=timeline, model_name=model_name)
    except OSError as error:
        raise PipelineError(f"Failed to save VMD file: {error}") from error

    return PipelineResult(
        text_path=text_file,
        wav_path=wav_file,
        output_path=out_file,
        vowels=vowels,
        timeline=timeline,
        wav_analysis=wav_analysis,
    )
