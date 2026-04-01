from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from core.audio_processing import RmsSeriesData, WavAnalysisResult, analyze_wav_file, load_rms_series
from core.text_processing import text_to_vowel_sequence
from core.whisper_timing import (
    SpeechTimingAnchor,
    WhisperTimingError,
    recognize_audio_timing,
)
from vmd_writer import VowelTimelinePoint, write_morph_vmd

_MIN_EVENT_DURATION_SEC = 1e-6
_RMS_BOUNDARY_SEARCH_SEC = 0.08
_RMS_THRESHOLD_RATIO = 0.35
_RMS_ABS_MIN_THRESHOLD = 0.01
_RMS_MIN_REFINED_DURATION_SEC = 0.03
_RMS_MAX_ADJACENT_OVERLAP_SEC = 0.02
_PEAK_WINDOW_HALO_SEC = 0.03
_RMS_UNAVAILABLE_FALLBACK_RATIO = 0.25
_DEFAULT_MORPH_UPPER_LIMIT = 0.5
_SAME_VOWEL_BURST_LOW_POSITIVE_MAX = 0.2
_SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES = 2
_SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES = 1
_SAME_VOWEL_REPRESENTATIVE_HALF_WIDTH_FRAMES = 1
_CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES = 2
_CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES = 5
_CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES = 1
_CROSS_VOWEL_REPRESENTATIVE_HALF_WIDTH_FRAMES = 1
_CROSS_VOWEL_RIGHT_GAP_RESIDUAL_MAX_FRAMES = 4
_CROSS_VOWEL_RIGHT_GAP_RESIDUAL_MAX_SPAN_FRAMES = 7
_CROSS_VOWEL_FLOOR_RESIDUAL_MAX_SPAN_FRAMES = 7
_CROSS_VOWEL_FLOOR_RESIDUAL_MAX_RIGHT_GAP_FRAMES = 3
_CROSS_VOWEL_FLOOR_RESIDUAL_MAX_END_TIME_GAP_FRAMES = 2


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
    observations: list[PeakValueObservation] | None = None


@dataclass(frozen=True)
class VowelTimingPlan:
    vowels: list[str]
    timeline: list[VowelTimelinePoint]
    anchors: list[SpeechTimingAnchor]
    source: str
    warning: str | None = None
    observations: list[PeakValueObservation] | None = None


@dataclass(frozen=True)
class PeakValueEvaluation:
    interval_start_sec: float
    interval_end_sec: float
    peak_window_start_sec: float
    peak_window_end_sec: float
    local_peak: float | None
    peak_value: float
    reason: str | None = None


@dataclass(frozen=True)
class PeakValueObservation:
    event_index: int
    vowel: str
    time_sec: float
    initial_interval_start_sec: float
    initial_interval_end_sec: float
    refined_interval_start_sec: float
    refined_interval_end_sec: float
    peak_window_start_sec: float
    peak_window_end_sec: float
    local_peak: float | None
    global_peak: float | None
    peak_value: float
    reason: str | None
    fallback_reason: str | None
    window_sample_count: int
    evaluation: PeakValueEvaluation
    rms_window_times_sec: tuple[float, ...] = ()
    rms_window_values: tuple[float, ...] = ()
    is_bridgeable_same_vowel_micro_gap_candidate: bool = False
    is_same_vowel_burst_candidate: bool = False
    is_bridgeable_cross_vowel_transition_candidate: bool = False
    is_cross_vowel_zero_run_continuity_floor_candidate: bool = False
    is_bridgeable_micro_gap_candidate: bool = False
    bridge_candidate_reason: str | None = None
    previous_non_zero_event_index: int | None = None
    next_non_zero_event_index: int | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None


@dataclass(frozen=True)
class _ObservedTimelineBuildResult:
    timeline: list[VowelTimelinePoint]
    observations: list[PeakValueObservation] | None = None


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
        start_sec, end_sec = _even_interval_bounds(
            start_sec=speech_start_sec,
            end_sec=speech_end_sec,
            index=index,
            count=count,
        )
        duration_sec = _ensure_positive_duration(end_sec - start_sec)
        timeline.append(
            VowelTimelinePoint(
                time_sec=time_sec,
                vowel=vowel,
                duration_sec=duration_sec,
                start_sec=start_sec,
                end_sec=end_sec,
            )
        )
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
            start_sec, end_sec = _even_interval_bounds_with_margin(
                start_sec=anchor.start_sec,
                end_sec=anchor.end_sec,
                index=local_index,
                count=count,
            )
            duration_sec = _ensure_positive_duration(end_sec - start_sec)
            timeline.append(
                VowelTimelinePoint(
                    time_sec=time_sec,
                    vowel=vowels[vowel_index],
                    duration_sec=duration_sec,
                    start_sec=start_sec,
                    end_sec=end_sec,
                )
            )
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
    upper_limit: float = _DEFAULT_MORPH_UPPER_LIMIT,
) -> VowelTimingPlan:
    if upper_limit < 0.0:
        raise ValueError("upper_limit must be >= 0.0.")

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

    initial_timeline = build_anchor_based_vowel_timeline(
        vowels=vowels,
        timing_anchors=anchors,
        speech_start_sec=wav_analysis.speech_start_sec,
        speech_end_sec=wav_analysis.speech_end_sec,
    )
    observed_timeline = _refine_timeline_intervals_with_observations(
        timeline=initial_timeline,
        wav_path=wav_path,
        speech_start_sec=wav_analysis.speech_start_sec,
        speech_end_sec=wav_analysis.speech_end_sec,
        upper_limit=upper_limit,
    )

    return VowelTimingPlan(
        vowels=vowels,
        timeline=observed_timeline.timeline,
        anchors=anchors,
        source=timing_source,
        warning=warning,
        observations=observed_timeline.observations,
    )


def generate_vmd_from_text_wav(
    text_path: str | Path,
    wav_path: str | Path,
    output_path: str | Path,
    *,
    silence_threshold: float = 0.02,
    model_name: str = "AutoLipTool",
    timing_plan: VowelTimingPlan | None = None,
    upper_limit: float = _DEFAULT_MORPH_UPPER_LIMIT,
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
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

    resolved_timing_plan = timing_plan
    if resolved_timing_plan is None:
        try:
            resolved_timing_plan = build_vowel_timing_plan(
                text_content=text_content,
                wav_path=wav_file,
                wav_analysis=wav_analysis,
                whisper_model_name="small",
                upper_limit=upper_limit,
            )
        except ValueError as error:
            raise PipelineError(f"Failed to build vowel timeline: {error}") from error
    elif not resolved_timing_plan.timeline:
        raise PipelineError("Provided timing plan has no timeline points.")
    elif _timeline_has_non_positive_duration(resolved_timing_plan.timeline):
        resolved_timing_plan = VowelTimingPlan(
            vowels=resolved_timing_plan.vowels,
            timeline=_infer_durations_from_midpoints(
                resolved_timing_plan.timeline,
                speech_start_sec=wav_analysis.speech_start_sec,
                speech_end_sec=wav_analysis.speech_end_sec,
            ),
            anchors=resolved_timing_plan.anchors,
            source=resolved_timing_plan.source,
            warning=resolved_timing_plan.warning,
            observations=None,
        )

    try:
        write_morph_vmd(
            output_path=out_file,
            timeline=resolved_timing_plan.timeline,
            model_name=model_name,
            observations=resolved_timing_plan.observations,
            closing_hold_frames=closing_hold_frames,
            closing_softness_frames=closing_softness_frames,
        )
    except OSError as error:
        raise PipelineError(f"Failed to save VMD file: {error}") from error

    return PipelineResult(
        text_path=text_file,
        wav_path=wav_file,
        output_path=out_file,
        vowels=resolved_timing_plan.vowels,
        timeline=resolved_timing_plan.timeline,
        wav_analysis=wav_analysis,
        timing_anchors=resolved_timing_plan.anchors,
        timing_source=resolved_timing_plan.source,
        timing_warning=resolved_timing_plan.warning,
        observations=resolved_timing_plan.observations,
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


def _timeline_has_non_positive_duration(timeline: Sequence[VowelTimelinePoint]) -> bool:
    return any(point.duration_sec <= 0 for point in timeline)


def _refine_timeline_intervals_with_rms(
    *,
    timeline: Sequence[VowelTimelinePoint],
    wav_path: str | Path,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
) -> list[VowelTimelinePoint]:
    return _refine_timeline_intervals_with_observations(
        timeline=timeline,
        wav_path=wav_path,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=upper_limit,
    ).timeline


def _refine_timeline_intervals_with_observations(
    *,
    timeline: Sequence[VowelTimelinePoint],
    wav_path: str | Path,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
) -> _ObservedTimelineBuildResult:
    if not timeline:
        return _ObservedTimelineBuildResult(timeline=[], observations=[])

    clamped_upper_limit = max(0.0, upper_limit)
    initial_timeline = list(timeline)

    try:
        rms_series = load_rms_series(str(wav_path), stereo_mode="average")
    except (ValueError, OSError, EOFError):
        timeline_with_peak_values = _apply_peak_values_to_timeline(
            timeline=initial_timeline,
            rms_series=None,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
            upper_limit=clamped_upper_limit,
            fallback_reason="rms_unavailable",
        )
        observations = _build_peak_value_observations(
            timeline=timeline_with_peak_values,
            initial_timeline=initial_timeline,
            rms_series=None,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
            upper_limit=clamped_upper_limit,
            fallback_reason="rms_unavailable",
        )
        return _ObservedTimelineBuildResult(
            timeline=timeline_with_peak_values,
            observations=observations,
        )

    refined_timeline = _refine_intervals_by_rms_series(
        timeline=initial_timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
    )
    timeline_with_peak_values = _apply_peak_values_to_timeline(
        timeline=refined_timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=clamped_upper_limit,
    )
    observations = _build_peak_value_observations(
        timeline=timeline_with_peak_values,
        initial_timeline=initial_timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=clamped_upper_limit,
    )
    return _ObservedTimelineBuildResult(
        timeline=timeline_with_peak_values,
        observations=observations,
    )


def _refine_intervals_by_rms_series(
    *,
    timeline: Sequence[VowelTimelinePoint],
    rms_series: RmsSeriesData,
    speech_start_sec: float,
    speech_end_sec: float,
) -> list[VowelTimelinePoint]:
    if not timeline:
        return []
    if not rms_series.times_sec or not rms_series.values:
        return list(timeline)

    if speech_end_sec < speech_start_sec:
        speech_start_sec, speech_end_sec = speech_end_sec, speech_start_sec

    refined: list[VowelTimelinePoint] = []
    for point in timeline:
        base_start_sec = (
            point.start_sec
            if point.start_sec is not None
            else (point.time_sec - (point.duration_sec * 0.5))
        )
        base_end_sec = (
            point.end_sec
            if point.end_sec is not None
            else (point.time_sec + (point.duration_sec * 0.5))
        )
        if base_end_sec < base_start_sec:
            base_end_sec = base_start_sec

        search_start_sec = max(speech_start_sec, base_start_sec - _RMS_BOUNDARY_SEARCH_SEC)
        search_end_sec = min(speech_end_sec, base_end_sec + _RMS_BOUNDARY_SEARCH_SEC)
        local_peak = _rms_local_peak(
            times_sec=rms_series.times_sec,
            values=rms_series.values,
            start_sec=search_start_sec,
            end_sec=search_end_sec,
        )
        if local_peak <= _RMS_ABS_MIN_THRESHOLD:
            refined.append(
                VowelTimelinePoint(
                    time_sec=point.time_sec,
                    vowel=point.vowel,
                    value=point.value,
                    duration_sec=point.duration_sec,
                    start_sec=base_start_sec,
                    end_sec=base_end_sec,
                )
            )
            continue

        threshold = max(local_peak * _RMS_THRESHOLD_RATIO, _RMS_ABS_MIN_THRESHOLD)
        start_candidate = _first_rms_above(
            times_sec=rms_series.times_sec,
            values=rms_series.values,
            start_sec=search_start_sec,
            end_sec=point.time_sec,
            threshold=threshold,
        )
        end_candidate = _last_rms_above(
            times_sec=rms_series.times_sec,
            values=rms_series.values,
            start_sec=point.time_sec,
            end_sec=search_end_sec,
            threshold=threshold,
        )

        refined_start_sec = base_start_sec if start_candidate is None else start_candidate
        refined_end_sec = base_end_sec if end_candidate is None else end_candidate
        refined_start_sec = min(refined_start_sec, point.time_sec)
        refined_end_sec = max(refined_end_sec, point.time_sec)
        refined_start_sec = max(speech_start_sec, refined_start_sec)
        refined_end_sec = min(speech_end_sec, refined_end_sec)
        refined_start_sec, refined_end_sec = _ensure_min_interval(
            start_sec=refined_start_sec,
            end_sec=refined_end_sec,
            center_sec=point.time_sec,
            min_duration_sec=_RMS_MIN_REFINED_DURATION_SEC,
            lower_bound_sec=speech_start_sec,
            upper_bound_sec=speech_end_sec,
        )

        refined.append(
            VowelTimelinePoint(
                time_sec=point.time_sec,
                vowel=point.vowel,
                value=point.value,
                duration_sec=refined_end_sec - refined_start_sec,
                start_sec=refined_start_sec,
                end_sec=refined_end_sec,
            )
        )

    return _resolve_adjacent_interval_conflicts(
        timeline=refined,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
    )


def _apply_peak_values_to_timeline(
    *,
    timeline: Sequence[VowelTimelinePoint],
    rms_series: RmsSeriesData | None,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
    fallback_reason: str | None = None,
) -> list[VowelTimelinePoint]:
    evaluations = _build_peak_value_evaluations(
        timeline=timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=upper_limit,
        fallback_reason=fallback_reason,
    )
    return [
        _with_peak_value(point=point, peak_value=evaluation.peak_value)
        for point, evaluation in zip(timeline, evaluations)
    ]


def _build_peak_value_evaluations(
    *,
    timeline: Sequence[VowelTimelinePoint],
    rms_series: RmsSeriesData | None,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
    fallback_reason: str | None = None,
) -> list[PeakValueEvaluation]:
    if not timeline:
        return []

    clamped_upper_limit = max(0.0, upper_limit)
    if clamped_upper_limit <= 0.0:
        return [
            PeakValueEvaluation(
                interval_start_sec=interval_start_sec,
                interval_end_sec=interval_end_sec,
                peak_window_start_sec=interval_start_sec,
                peak_window_end_sec=interval_end_sec,
                local_peak=None,
                peak_value=0.0,
            )
            for interval_start_sec, interval_end_sec in (
                _event_interval(point) for point in timeline
            )
        ]

    if fallback_reason == "rms_unavailable":
        fallback_peak_value = round(clamped_upper_limit * _RMS_UNAVAILABLE_FALLBACK_RATIO, 4)
        return [
            PeakValueEvaluation(
                interval_start_sec=interval_start_sec,
                interval_end_sec=interval_end_sec,
                peak_window_start_sec=interval_start_sec,
                peak_window_end_sec=interval_end_sec,
                local_peak=None,
                peak_value=fallback_peak_value,
                reason="rms_unavailable",
            )
            for interval_start_sec, interval_end_sec in (
                _event_interval(point) for point in timeline
            )
        ]

    if rms_series is None or not rms_series.times_sec or not rms_series.values:
        return [
            PeakValueEvaluation(
                interval_start_sec=interval_start_sec,
                interval_end_sec=interval_end_sec,
                peak_window_start_sec=interval_start_sec,
                peak_window_end_sec=interval_end_sec,
                local_peak=None,
                peak_value=0.0,
                reason="global_peak_zero",
            )
            for interval_start_sec, interval_end_sec in (
                _event_interval(point) for point in timeline
            )
        ]

    global_peak = _rms_local_peak(
        times_sec=rms_series.times_sec,
        values=rms_series.values,
        start_sec=speech_start_sec,
        end_sec=speech_end_sec,
    )
    if global_peak <= 0.0:
        return [
            PeakValueEvaluation(
                interval_start_sec=interval_start_sec,
                interval_end_sec=interval_end_sec,
                peak_window_start_sec=interval_start_sec,
                peak_window_end_sec=interval_end_sec,
                local_peak=0.0,
                peak_value=0.0,
                reason="global_peak_zero",
            )
            for interval_start_sec, interval_end_sec in (
                _event_interval(point) for point in timeline
            )
        ]

    evaluations: list[PeakValueEvaluation] = []
    for index, point in enumerate(timeline):
        interval_start_sec, interval_end_sec = _event_interval(point)
        peak_window_start_sec, peak_window_end_sec = _build_peak_window(
            timeline=timeline,
            index=index,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
        )
        window_samples = _rms_samples_in_window(
            times_sec=rms_series.times_sec,
            values=rms_series.values,
            start_sec=peak_window_start_sec,
            end_sec=peak_window_end_sec,
        )
        local_peak = max(window_samples) if window_samples else None
        zero_reason = _classify_peak_zero_reason(
            local_peak=local_peak,
            global_peak=global_peak,
        )
        if zero_reason is None:
            normalized_peak = local_peak / global_peak
            peak_value = max(
                0.0,
                min(clamped_upper_limit, round(clamped_upper_limit * normalized_peak, 4)),
            )
        else:
            peak_value = 0.0
        evaluations.append(
            PeakValueEvaluation(
                interval_start_sec=interval_start_sec,
                interval_end_sec=interval_end_sec,
                peak_window_start_sec=peak_window_start_sec,
                peak_window_end_sec=peak_window_end_sec,
                local_peak=local_peak,
                peak_value=peak_value,
                reason=zero_reason,
            )
        )

    return evaluations


def _build_peak_value_observations(
    *,
    timeline: Sequence[VowelTimelinePoint],
    rms_series: RmsSeriesData | None,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
    fallback_reason: str | None = None,
    initial_timeline: Sequence[VowelTimelinePoint] | None = None,
) -> list[PeakValueObservation]:
    if not timeline:
        return []
    if initial_timeline is not None and len(initial_timeline) != len(timeline):
        raise ValueError("initial_timeline must have the same length as timeline.")

    evaluations = _build_peak_value_evaluations(
        timeline=timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=upper_limit,
        fallback_reason=fallback_reason,
    )
    global_peak = _observation_global_peak(
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        fallback_reason=fallback_reason,
    )

    observations: list[PeakValueObservation] = []
    for index, (point, evaluation) in enumerate(zip(timeline, evaluations)):
        initial_point = point if initial_timeline is None else initial_timeline[index]
        initial_interval_start_sec, initial_interval_end_sec = _event_interval(initial_point)
        window_samples = _rms_samples_in_window(
            times_sec=() if rms_series is None else rms_series.times_sec,
            values=() if rms_series is None else rms_series.values,
            start_sec=evaluation.peak_window_start_sec,
            end_sec=evaluation.peak_window_end_sec,
        )
        window_sample_pairs = _rms_sample_pairs_in_window(
            times_sec=() if rms_series is None else rms_series.times_sec,
            values=() if rms_series is None else rms_series.values,
            start_sec=evaluation.peak_window_start_sec,
            end_sec=evaluation.peak_window_end_sec,
        )
        observations.append(
            PeakValueObservation(
                event_index=index,
                vowel=point.vowel,
                time_sec=point.time_sec,
                initial_interval_start_sec=initial_interval_start_sec,
                initial_interval_end_sec=initial_interval_end_sec,
                refined_interval_start_sec=evaluation.interval_start_sec,
                refined_interval_end_sec=evaluation.interval_end_sec,
                peak_window_start_sec=evaluation.peak_window_start_sec,
                peak_window_end_sec=evaluation.peak_window_end_sec,
                local_peak=evaluation.local_peak,
                global_peak=global_peak,
                peak_value=evaluation.peak_value,
                reason=evaluation.reason,
                fallback_reason=fallback_reason,
                window_sample_count=len(window_samples),
                evaluation=evaluation,
                rms_window_times_sec=tuple(time_sec for time_sec, _ in window_sample_pairs),
                rms_window_values=tuple(value for _, value in window_sample_pairs),
            )
        )
    return _annotate_micro_gap_bridge_candidates(observations)


def _annotate_micro_gap_bridge_candidates(
    observations: Sequence[PeakValueObservation],
) -> list[PeakValueObservation]:
    if not observations:
        return []

    span_candidates = _build_bridgeable_zero_run_span_candidates(observations)
    same_vowel_burst_candidates = _build_same_vowel_burst_span_candidates(observations)
    annotated: list[PeakValueObservation] = []
    for index, observation in enumerate(observations):
        previous_non_zero_event_index = _previous_non_zero_event_index(
            observations,
            index,
        )
        next_non_zero_event_index = _next_non_zero_event_index(
            observations,
            index,
        )
        bridge_candidate_reason = _resolve_bridge_candidate_reason(observation)
        span_candidate = span_candidates.get(index)
        same_vowel_burst_span = same_vowel_burst_candidates.get(index)
        is_bridgeable_same_vowel_candidate = span_candidate == "same_vowel"
        is_same_vowel_burst_candidate = same_vowel_burst_span is not None
        is_bridgeable_cross_vowel_candidate = span_candidate == "cross_vowel_transition"
        is_cross_vowel_zero_run_floor_candidate = span_candidate == "cross_vowel_floor"
        if span_candidate is not None:
            span_start_index = _resolve_span_boundary_index(
                observations,
                index=index,
                direction=-1,
            )
            span_end_index = _resolve_span_boundary_index(
                observations,
                index=index,
                direction=1,
            )
        elif same_vowel_burst_span is not None:
            span_start_index, span_end_index = same_vowel_burst_span
        else:
            span_start_index = None
            span_end_index = None
        if bridge_candidate_reason is None and same_vowel_burst_span is not None:
            resolved_bridge_candidate_reason = "same_vowel_burst"
        elif (
            is_bridgeable_same_vowel_candidate
            or is_bridgeable_cross_vowel_candidate
            or is_cross_vowel_zero_run_floor_candidate
        ):
            resolved_bridge_candidate_reason = bridge_candidate_reason
        else:
            resolved_bridge_candidate_reason = None
        annotated.append(
            PeakValueObservation(
                event_index=observation.event_index,
                vowel=observation.vowel,
                time_sec=observation.time_sec,
                initial_interval_start_sec=observation.initial_interval_start_sec,
                initial_interval_end_sec=observation.initial_interval_end_sec,
                refined_interval_start_sec=observation.refined_interval_start_sec,
                refined_interval_end_sec=observation.refined_interval_end_sec,
                peak_window_start_sec=observation.peak_window_start_sec,
                peak_window_end_sec=observation.peak_window_end_sec,
                local_peak=observation.local_peak,
                global_peak=observation.global_peak,
                peak_value=observation.peak_value,
                reason=observation.reason,
                fallback_reason=observation.fallback_reason,
                window_sample_count=observation.window_sample_count,
                evaluation=observation.evaluation,
                rms_window_times_sec=observation.rms_window_times_sec,
                rms_window_values=observation.rms_window_values,
                is_bridgeable_same_vowel_micro_gap_candidate=is_bridgeable_same_vowel_candidate,
                is_same_vowel_burst_candidate=is_same_vowel_burst_candidate,
                is_bridgeable_cross_vowel_transition_candidate=is_bridgeable_cross_vowel_candidate,
                is_cross_vowel_zero_run_continuity_floor_candidate=is_cross_vowel_zero_run_floor_candidate,
                is_bridgeable_micro_gap_candidate=is_bridgeable_same_vowel_candidate,
                bridge_candidate_reason=resolved_bridge_candidate_reason,
                previous_non_zero_event_index=previous_non_zero_event_index,
                next_non_zero_event_index=next_non_zero_event_index,
                span_start_index=span_start_index,
                span_end_index=span_end_index,
            )
        )
    return annotated


def _build_same_vowel_burst_span_candidates(
    observations: Sequence[PeakValueObservation],
) -> dict[int, tuple[int, int]]:
    candidates: dict[int, tuple[int, int]] = {}
    index = 0
    while index < len(observations):
        if not _is_same_vowel_burst_segment_candidate(observations[index]):
            index += 1
            continue

        span_start_index = index
        span_end_index = index
        while (
            span_end_index + 1 < len(observations)
            and _is_same_vowel_burst_segment_candidate(observations[span_end_index + 1])
        ):
            span_end_index += 1

        if _is_same_vowel_burst_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
        ):
            for span_index in range(span_start_index, span_end_index + 1):
                candidates[span_index] = (span_start_index, span_end_index)

        index = span_end_index + 1

    return candidates


def _build_bridgeable_zero_run_span_candidates(
    observations: Sequence[PeakValueObservation],
) -> dict[int, str]:
    candidate_kinds_by_index: dict[int, str] = {}
    index = 0
    while index < len(observations):
        if _resolve_bridge_candidate_reason(observations[index]) is None:
            index += 1
            continue

        span_start_index = index
        span_end_index = index
        while (
            span_end_index + 1 < len(observations)
            and _resolve_bridge_candidate_reason(observations[span_end_index + 1]) is not None
        ):
            span_end_index += 1

        span_kind = _classify_bridgeable_zero_run_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
        )
        if span_kind is not None:
            for span_index in range(span_start_index, span_end_index + 1):
                candidate_kinds_by_index[span_index] = span_kind

        index = span_end_index + 1

    return candidate_kinds_by_index


def _resolve_span_boundary_index(
    observations: Sequence[PeakValueObservation],
    *,
    index: int,
    direction: int,
) -> int:
    boundary_index = index
    current_reason = _resolve_bridge_candidate_reason(observations[index])
    while 0 <= boundary_index + direction < len(observations):
        next_index = boundary_index + direction
        if _resolve_bridge_candidate_reason(observations[next_index]) is None:
            break
        boundary_index = next_index
    return boundary_index


def _classify_bridgeable_zero_run_span(
    *,
    observations: Sequence[PeakValueObservation],
    span_start_index: int,
    span_end_index: int,
) -> str | None:
    span_count = (span_end_index - span_start_index) + 1
    if span_count <= 0 or span_count > 2:
        return None

    previous_non_zero_event_index = _previous_non_zero_event_index(
        observations,
        span_start_index,
    )
    next_non_zero_event_index = _next_non_zero_event_index(
        observations,
        span_end_index,
    )
    if previous_non_zero_event_index is None or next_non_zero_event_index is None:
        return None
    if previous_non_zero_event_index >= span_start_index:
        return None
    if next_non_zero_event_index <= span_end_index:
        return None

    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]
    span_start_observation = observations[span_start_index]
    span_end_observation = observations[span_end_index]

    previous_start_frame = _seconds_to_frame(previous_observation.refined_interval_start_sec)
    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
    next_end_frame = _seconds_to_frame(next_observation.refined_interval_end_sec)
    span_start_frame = _seconds_to_frame(span_start_observation.refined_interval_start_sec)
    span_end_frame = _seconds_to_frame(span_end_observation.refined_interval_end_sec)

    if (previous_end_frame - previous_start_frame) < 2:
        return None
    if (next_end_frame - next_start_frame) < 2:
        return None

    if previous_observation.vowel == next_observation.vowel:
        representative_start_frame, representative_end_frame = _resolve_same_vowel_candidate_span_frames(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
        )
        if (
            representative_end_frame - representative_start_frame
        ) > _SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
            return None
        if (
            previous_end_frame - representative_start_frame
        ) > _SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
            return None
        if (
            representative_end_frame - next_start_frame
        ) > _SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
            return None
        if (
            representative_start_frame - previous_end_frame
        ) > _SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
            return None
        if (
            next_start_frame - representative_end_frame
        ) > _SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
            return None
        return "same_vowel"
    representative_start_frame, representative_end_frame = _resolve_cross_vowel_candidate_span_frames(
        observations=observations,
        span_start_index=span_start_index,
        span_end_index=span_end_index,
        previous_non_zero_event_index=previous_non_zero_event_index,
        next_non_zero_event_index=next_non_zero_event_index,
    )
    cross_vowel_max_span_frames = (
        _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES
        if span_count == 1
        else _CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES
    )
    if (
        representative_end_frame - representative_start_frame
    ) > cross_vowel_max_span_frames:
        if _is_cross_vowel_right_gap_residual_transition_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
            representative_start_frame=representative_start_frame,
            representative_end_frame=representative_end_frame,
        ):
            return "cross_vowel_transition"
        if _is_cross_vowel_floor_residual_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
            representative_start_frame=representative_start_frame,
            representative_end_frame=representative_end_frame,
        ):
            return "cross_vowel_floor"
        return None
    if (
        previous_end_frame - representative_start_frame
    ) > _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return None
    if (
        representative_end_frame - next_start_frame
    ) > _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return None
    if (
        representative_start_frame - previous_end_frame
    ) > _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        return None
    if (
        next_start_frame - representative_end_frame
    ) > _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        if _is_cross_vowel_right_gap_residual_transition_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
            representative_start_frame=representative_start_frame,
            representative_end_frame=representative_end_frame,
        ):
            return "cross_vowel_transition"
        if _is_cross_vowel_floor_residual_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
            representative_start_frame=representative_start_frame,
            representative_end_frame=representative_end_frame,
        ):
            return "cross_vowel_floor"
        return None
    if span_count == 1:
        return "cross_vowel_transition"
    return "cross_vowel_floor"


def _resolve_bridge_candidate_reason(
    observation: PeakValueObservation,
) -> str | None:
    if observation.peak_value > 0.0:
        return None
    if observation.reason in {"no_peak_in_window", "below_rel_threshold"}:
        return observation.reason
    return None


def _is_same_vowel_burst_segment_candidate(observation: PeakValueObservation) -> bool:
    if observation.peak_value < 0.0:
        return False
    if observation.peak_value <= 0.0:
        return _resolve_bridge_candidate_reason(observation) is not None
    return observation.peak_value <= _SAME_VOWEL_BURST_LOW_POSITIVE_MAX


def _is_same_vowel_burst_span(
    *,
    observations: Sequence[PeakValueObservation],
    span_start_index: int,
    span_end_index: int,
) -> bool:
    span_count = (span_end_index - span_start_index) + 1
    if span_count <= 0 or span_count > 2:
        return False

    previous_non_zero_event_index = _previous_non_zero_event_index(observations, span_start_index)
    next_non_zero_event_index = _next_non_zero_event_index(observations, span_end_index)
    if previous_non_zero_event_index is None or next_non_zero_event_index is None:
        return False
    if previous_non_zero_event_index >= span_start_index:
        return False
    if next_non_zero_event_index <= span_end_index:
        return False

    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]
    if previous_observation.vowel != next_observation.vowel:
        return False

    span_start_observation = observations[span_start_index]
    span_end_observation = observations[span_end_index]
    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
    span_start_frame = _seconds_to_frame(span_start_observation.refined_interval_start_sec)
    span_end_frame = _seconds_to_frame(span_end_observation.refined_interval_end_sec)

    representative_start_frame, representative_end_frame = _resolve_same_vowel_candidate_span_frames(
        observations=observations,
        span_start_index=span_start_index,
        span_end_index=span_end_index,
        previous_non_zero_event_index=previous_non_zero_event_index,
        next_non_zero_event_index=next_non_zero_event_index,
    )

    if (
        representative_end_frame - representative_start_frame
    ) > _SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    if (
        previous_end_frame - representative_start_frame
    ) > _SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return False
    if (
        representative_end_frame - next_start_frame
    ) > _SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return False
    if (
        representative_start_frame - previous_end_frame
    ) > _SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    if (
        next_start_frame - representative_end_frame
    ) > _SAME_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    return True


def _is_cross_vowel_right_gap_residual_transition_span(
    *,
    observations: Sequence[PeakValueObservation],
    span_start_index: int,
    span_end_index: int,
    previous_non_zero_event_index: int,
    next_non_zero_event_index: int,
    representative_start_frame: int,
    representative_end_frame: int,
) -> bool:
    span_count = (span_end_index - span_start_index) + 1
    if span_count <= 0 or span_count > 2:
        return False

    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]
    if previous_observation.vowel == next_observation.vowel:
        return False

    for span_index in range(span_start_index, span_end_index + 1):
        if _resolve_bridge_candidate_reason(observations[span_index]) is None:
            return False

    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
    representative_span_frames = representative_end_frame - representative_start_frame
    right_gap_frames = next_start_frame - representative_end_frame

    if representative_span_frames > _CROSS_VOWEL_RIGHT_GAP_RESIDUAL_MAX_SPAN_FRAMES:
        return False
    if (previous_end_frame - representative_start_frame) > _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return False
    if (representative_start_frame - previous_end_frame) > _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    if right_gap_frames <= _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    if right_gap_frames > _CROSS_VOWEL_RIGHT_GAP_RESIDUAL_MAX_FRAMES:
        return False
    return True


def _is_cross_vowel_floor_residual_span(
    *,
    observations: Sequence[PeakValueObservation],
    span_start_index: int,
    span_end_index: int,
    previous_non_zero_event_index: int,
    next_non_zero_event_index: int,
    representative_start_frame: int,
    representative_end_frame: int,
) -> bool:
    span_count = (span_end_index - span_start_index) + 1
    if span_count != 2:
        return False

    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]
    if previous_observation.vowel == next_observation.vowel:
        return False

    for span_index in range(span_start_index, span_end_index + 1):
        if _resolve_bridge_candidate_reason(observations[span_index]) is None:
            return False

    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
    next_initial_start_frame = _seconds_to_frame(next_observation.initial_interval_start_sec)
    span_start_observation = observations[span_start_index]
    span_end_observation = observations[span_end_index]
    span_start_time_frame = _seconds_to_frame(span_start_observation.time_sec)
    span_end_time_frame = _seconds_to_frame(span_end_observation.time_sec)
    span_end_initial_end_frame = _seconds_to_frame(span_end_observation.initial_interval_end_sec)
    representative_span_frames = representative_end_frame - representative_start_frame
    right_gap_refined_frames = next_start_frame - representative_end_frame
    right_gap_initial_frames = next_initial_start_frame - representative_end_frame

    if representative_span_frames <= _CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    if representative_span_frames > _CROSS_VOWEL_FLOOR_RESIDUAL_MAX_SPAN_FRAMES:
        if not (
            0 <= (span_start_time_frame - previous_end_frame) <= _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES
            and 0 <= (next_initial_start_frame - span_end_time_frame) <= _CROSS_VOWEL_FLOOR_RESIDUAL_MAX_END_TIME_GAP_FRAMES
            and (next_initial_start_frame - span_end_initial_end_frame) <= 0
        ):
            return False
    if (previous_end_frame - representative_start_frame) > _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return False
    if right_gap_refined_frames > _CROSS_VOWEL_FLOOR_RESIDUAL_MAX_RIGHT_GAP_FRAMES:
        return False
    if right_gap_initial_frames > _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES:
        return False
    return True


def _resolve_same_vowel_candidate_span_frames(
    *,
    observations: Sequence[PeakValueObservation],
    span_start_index: int,
    span_end_index: int,
    previous_non_zero_event_index: int,
    next_non_zero_event_index: int,
) -> tuple[int, int]:
    span_start_observation = observations[span_start_index]
    span_end_observation = observations[span_end_index]
    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]

    span_start_frame = _seconds_to_frame(span_start_observation.refined_interval_start_sec)
    span_end_frame = _seconds_to_frame(span_end_observation.refined_interval_end_sec)
    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)

    time_based_start_frame = (
        _seconds_to_frame(span_start_observation.time_sec)
        - _SAME_VOWEL_REPRESENTATIVE_HALF_WIDTH_FRAMES
    )
    time_based_end_frame = (
        _seconds_to_frame(span_end_observation.time_sec)
        + _SAME_VOWEL_REPRESENTATIVE_HALF_WIDTH_FRAMES
    )

    representative_start_frame = max(
        span_start_frame,
        time_based_start_frame,
        previous_end_frame - _SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES,
    )
    representative_end_frame = min(
        span_end_frame,
        time_based_end_frame,
        next_start_frame + _SAME_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES,
    )

    if representative_end_frame < representative_start_frame:
        midpoint_frame = round(
            (
                _seconds_to_frame(span_start_observation.time_sec)
                + _seconds_to_frame(span_end_observation.time_sec)
            )
            * 0.5
        )
        midpoint_frame = max(midpoint_frame, previous_end_frame)
        midpoint_frame = min(midpoint_frame, next_start_frame)
        representative_start_frame = midpoint_frame
        representative_end_frame = midpoint_frame

    return representative_start_frame, representative_end_frame


def _resolve_cross_vowel_candidate_span_frames(
    *,
    observations: Sequence[PeakValueObservation],
    span_start_index: int,
    span_end_index: int,
    previous_non_zero_event_index: int,
    next_non_zero_event_index: int,
) -> tuple[int, int]:
    span_start_observation = observations[span_start_index]
    span_end_observation = observations[span_end_index]
    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]

    span_start_frame = _seconds_to_frame(span_start_observation.refined_interval_start_sec)
    span_end_frame = _seconds_to_frame(span_end_observation.refined_interval_end_sec)
    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)

    time_based_start_frame = (
        _seconds_to_frame(span_start_observation.time_sec)
        - _CROSS_VOWEL_REPRESENTATIVE_HALF_WIDTH_FRAMES
    )
    time_based_end_frame = (
        _seconds_to_frame(span_end_observation.time_sec)
        + _CROSS_VOWEL_REPRESENTATIVE_HALF_WIDTH_FRAMES
    )

    representative_start_frame = max(
        span_start_frame,
        time_based_start_frame,
        previous_end_frame - _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES,
    )
    representative_end_frame = min(
        span_end_frame,
        time_based_end_frame,
        next_start_frame + _CROSS_VOWEL_MAX_CANDIDATE_OVERLAP_FRAMES,
    )

    if representative_end_frame < representative_start_frame:
        midpoint_frame = round(
            (
                _seconds_to_frame(span_start_observation.time_sec)
                + _seconds_to_frame(span_end_observation.time_sec)
            )
            * 0.5
        )
        midpoint_frame = max(midpoint_frame, previous_end_frame)
        midpoint_frame = min(midpoint_frame, next_start_frame)
        representative_start_frame = midpoint_frame
        representative_end_frame = midpoint_frame

    return representative_start_frame, representative_end_frame


def _previous_non_zero_event_index(
    observations: Sequence[PeakValueObservation],
    index: int,
) -> int | None:
    for previous_index in range(index - 1, -1, -1):
        if observations[previous_index].peak_value > 0.0:
            return previous_index
    return None


def _next_non_zero_event_index(
    observations: Sequence[PeakValueObservation],
    index: int,
) -> int | None:
    for next_index in range(index + 1, len(observations)):
        if observations[next_index].peak_value > 0.0:
            return next_index
    return None


def _is_bridgeable_same_vowel_micro_gap_candidate(
    *,
    observations: Sequence[PeakValueObservation],
    index: int,
    bridge_candidate_reason: str | None,
    previous_non_zero_event_index: int | None,
    next_non_zero_event_index: int | None,
) -> bool:
    if bridge_candidate_reason is None:
        return False
    if previous_non_zero_event_index is None or next_non_zero_event_index is None:
        return False
    if previous_non_zero_event_index != index - 1:
        return False
    if next_non_zero_event_index != index + 1:
        return False

    current_observation = observations[index]
    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]

    if previous_observation.vowel != current_observation.vowel:
        return False
    if next_observation.vowel != current_observation.vowel:
        return False

    current_start_frame = _seconds_to_frame(current_observation.refined_interval_start_sec)
    current_end_frame = _seconds_to_frame(current_observation.refined_interval_end_sec)
    current_span_frames = max(0, current_end_frame - current_start_frame)
    if current_span_frames > 1:
        return False

    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
    if current_start_frame < previous_end_frame:
        return False
    if next_start_frame < current_end_frame:
        return False

    return (
        (current_start_frame - previous_end_frame) <= 1
        and (next_start_frame - current_end_frame) <= 1
    )


def _is_bridgeable_cross_vowel_transition_candidate(
    *,
    observations: Sequence[PeakValueObservation],
    index: int,
    bridge_candidate_reason: str | None,
    previous_non_zero_event_index: int | None,
    next_non_zero_event_index: int | None,
) -> bool:
    if bridge_candidate_reason is None:
        return False
    if previous_non_zero_event_index is None or next_non_zero_event_index is None:
        return False
    if previous_non_zero_event_index != index - 1:
        return False
    if next_non_zero_event_index != index + 1:
        return False

    current_observation = observations[index]
    previous_observation = observations[previous_non_zero_event_index]
    next_observation = observations[next_non_zero_event_index]

    if previous_observation.vowel == next_observation.vowel:
        return False

    current_start_frame = _seconds_to_frame(current_observation.refined_interval_start_sec)
    current_end_frame = _seconds_to_frame(current_observation.refined_interval_end_sec)
    current_span_frames = max(0, current_end_frame - current_start_frame)
    if current_span_frames > 1:
        return False

    previous_start_frame = _seconds_to_frame(previous_observation.refined_interval_start_sec)
    previous_end_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
    next_start_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
    next_end_frame = _seconds_to_frame(next_observation.refined_interval_end_sec)

    if (previous_end_frame - previous_start_frame) < 2:
        return False
    if (next_end_frame - next_start_frame) < 2:
        return False

    if current_start_frame < previous_end_frame:
        return False
    if next_start_frame < current_end_frame:
        return False

    return (
        (current_start_frame - previous_end_frame) <= 1
        and (next_start_frame - current_end_frame) <= 1
    )


def _seconds_to_frame(time_sec: float) -> int:
    return int(round(float(time_sec) * 30.0))


def _observation_global_peak(
    *,
    rms_series: RmsSeriesData | None,
    speech_start_sec: float,
    speech_end_sec: float,
    fallback_reason: str | None = None,
) -> float | None:
    if fallback_reason == "rms_unavailable":
        return None
    if rms_series is None or not rms_series.times_sec or not rms_series.values:
        return 0.0
    return _rms_local_peak(
        times_sec=rms_series.times_sec,
        values=rms_series.values,
        start_sec=speech_start_sec,
        end_sec=speech_end_sec,
    )


def _with_peak_value(*, point: VowelTimelinePoint, peak_value: float) -> VowelTimelinePoint:
    return VowelTimelinePoint(
        time_sec=point.time_sec,
        vowel=point.vowel,
        value=peak_value,
        peak_value=peak_value,
        duration_sec=point.duration_sec,
        start_sec=point.start_sec,
        end_sec=point.end_sec,
    )


def _rms_local_peak(
    *,
    times_sec: Sequence[float],
    values: Sequence[float],
    start_sec: float,
    end_sec: float,
) -> float:
    peak = 0.0
    for time_sec, value in zip(times_sec, values):
        if time_sec < start_sec or time_sec > end_sec:
            continue
        if value > peak:
            peak = value
    return peak


def _first_rms_above(
    *,
    times_sec: Sequence[float],
    values: Sequence[float],
    start_sec: float,
    end_sec: float,
    threshold: float,
) -> float | None:
    if end_sec < start_sec:
        return None
    for time_sec, value in zip(times_sec, values):
        if time_sec < start_sec:
            continue
        if time_sec > end_sec:
            break
        if value >= threshold:
            return time_sec
    return None


def _last_rms_above(
    *,
    times_sec: Sequence[float],
    values: Sequence[float],
    start_sec: float,
    end_sec: float,
    threshold: float,
) -> float | None:
    if end_sec < start_sec:
        return None
    last: float | None = None
    for time_sec, value in zip(times_sec, values):
        if time_sec < start_sec:
            continue
        if time_sec > end_sec:
            break
        if value >= threshold:
            last = time_sec
    return last


def _ensure_min_interval(
    *,
    start_sec: float,
    end_sec: float,
    center_sec: float,
    min_duration_sec: float,
    lower_bound_sec: float,
    upper_bound_sec: float,
) -> tuple[float, float]:
    if end_sec < start_sec:
        end_sec = start_sec

    start_sec = min(start_sec, center_sec)
    end_sec = max(end_sec, center_sec)
    duration_sec = end_sec - start_sec
    if duration_sec >= min_duration_sec:
        return start_sec, end_sec

    half = min_duration_sec * 0.5
    expanded_start = center_sec - half
    expanded_end = center_sec + half

    if expanded_start < lower_bound_sec:
        shift = lower_bound_sec - expanded_start
        expanded_start += shift
        expanded_end += shift
    if expanded_end > upper_bound_sec:
        shift = expanded_end - upper_bound_sec
        expanded_start -= shift
        expanded_end -= shift

    expanded_start = max(lower_bound_sec, expanded_start)
    expanded_end = min(upper_bound_sec, expanded_end)
    expanded_start = min(expanded_start, center_sec)
    expanded_end = max(expanded_end, center_sec)
    if expanded_end < expanded_start:
        expanded_end = expanded_start
    return expanded_start, expanded_end


def _event_interval(point: VowelTimelinePoint) -> tuple[float, float]:
    start_sec = point.start_sec
    end_sec = point.end_sec
    if start_sec is None and end_sec is None:
        half = max(point.duration_sec, 0.0) * 0.5
        return (point.time_sec - half, point.time_sec + half)
    if start_sec is None:
        end_sec = float(end_sec)
        return (min(point.time_sec, end_sec), end_sec)
    if end_sec is None:
        start_sec = float(start_sec)
        return (start_sec, max(point.time_sec, start_sec))
    return (float(start_sec), float(end_sec))


def _build_peak_window(
    *,
    timeline: Sequence[VowelTimelinePoint],
    index: int,
    speech_start_sec: float,
    speech_end_sec: float,
) -> tuple[float, float]:
    interval_start_sec, interval_end_sec = _event_interval(timeline[index])
    window_start_sec = max(speech_start_sec, interval_start_sec - _PEAK_WINDOW_HALO_SEC)
    window_end_sec = min(speech_end_sec, interval_end_sec + _PEAK_WINDOW_HALO_SEC)

    if index > 0:
        prev_start_sec, prev_end_sec = _event_interval(timeline[index - 1])
        del prev_start_sec
        left_clip_sec = (prev_end_sec + interval_start_sec) * 0.5
        window_start_sec = max(window_start_sec, left_clip_sec)

    if index + 1 < len(timeline):
        next_start_sec, next_end_sec = _event_interval(timeline[index + 1])
        del next_end_sec
        right_clip_sec = (interval_end_sec + next_start_sec) * 0.5
        window_end_sec = min(window_end_sec, right_clip_sec)

    if window_end_sec < window_start_sec:
        midpoint_sec = (window_start_sec + window_end_sec) * 0.5
        window_start_sec = midpoint_sec
        window_end_sec = midpoint_sec
    return (window_start_sec, window_end_sec)


def _rms_samples_in_window(
    *,
    times_sec: Sequence[float],
    values: Sequence[float],
    start_sec: float,
    end_sec: float,
) -> list[float]:
    if end_sec < start_sec:
        return []
    return [
        value
        for time_sec, value in zip(times_sec, values)
        if start_sec <= time_sec <= end_sec
    ]


def _rms_sample_pairs_in_window(
    *,
    times_sec: Sequence[float],
    values: Sequence[float],
    start_sec: float,
    end_sec: float,
) -> list[tuple[float, float]]:
    if end_sec < start_sec:
        return []
    return [
        (float(time_sec), float(value))
        for time_sec, value in zip(times_sec, values)
        if start_sec <= time_sec <= end_sec
    ]


def _classify_peak_zero_reason(
    *,
    local_peak: float | None,
    global_peak: float,
) -> str | None:
    if local_peak is None:
        return "no_peak_in_window"
    if local_peak < _RMS_ABS_MIN_THRESHOLD:
        return "below_abs_threshold"
    if (local_peak / global_peak) < _RMS_THRESHOLD_RATIO:
        return "below_rel_threshold"
    return None


def _resolve_adjacent_interval_conflicts(
    *,
    timeline: Sequence[VowelTimelinePoint],
    speech_start_sec: float,
    speech_end_sec: float,
) -> list[VowelTimelinePoint]:
    if not timeline:
        return []

    first_start_sec, first_end_sec = _event_interval(timeline[0])
    resolved: list[VowelTimelinePoint] = [
        VowelTimelinePoint(
            time_sec=timeline[0].time_sec,
            vowel=timeline[0].vowel,
            value=timeline[0].value,
            duration_sec=timeline[0].duration_sec,
            start_sec=max(speech_start_sec, first_start_sec),
            end_sec=min(speech_end_sec, first_end_sec),
        )
    ]

    for point in timeline[1:]:
        prev = resolved[-1]
        prev_start, prev_end = _event_interval(prev)
        curr_start, curr_end = _event_interval(point)
        min_curr_start = prev.end_sec - _RMS_MAX_ADJACENT_OVERLAP_SEC

        if curr_start < min_curr_start:
            if point.time_sec >= min_curr_start:
                curr_start = min_curr_start
            else:
                prev_end = min(prev_end, point.time_sec + _RMS_MAX_ADJACENT_OVERLAP_SEC)
                prev_end = max(prev.time_sec, prev_end)
                resolved[-1] = VowelTimelinePoint(
                    time_sec=prev.time_sec,
                    vowel=prev.vowel,
                    value=prev.value,
                    duration_sec=prev_end - prev_start,
                    start_sec=prev_start,
                    end_sec=prev_end,
                )
                min_curr_start = resolved[-1].end_sec - _RMS_MAX_ADJACENT_OVERLAP_SEC
                curr_start = max(curr_start, min(min_curr_start, point.time_sec))

        curr_start = max(speech_start_sec, min(curr_start, point.time_sec))
        curr_end = min(speech_end_sec, max(curr_end, point.time_sec))
        curr_start, curr_end = _ensure_min_interval(
            start_sec=curr_start,
            end_sec=curr_end,
            center_sec=point.time_sec,
            min_duration_sec=_RMS_MIN_REFINED_DURATION_SEC,
            lower_bound_sec=speech_start_sec,
            upper_bound_sec=speech_end_sec,
        )

        if curr_start < resolved[-1].end_sec - _RMS_MAX_ADJACENT_OVERLAP_SEC:
            curr_start = resolved[-1].end_sec - _RMS_MAX_ADJACENT_OVERLAP_SEC
            curr_start = min(curr_start, point.time_sec)
            curr_end = max(curr_end, point.time_sec)

        resolved.append(
            VowelTimelinePoint(
                time_sec=point.time_sec,
                vowel=point.vowel,
                value=point.value,
                duration_sec=curr_end - curr_start,
                start_sec=curr_start,
                end_sec=curr_end,
            )
        )

    return resolved


def _infer_durations_from_midpoints(
    timeline: Sequence[VowelTimelinePoint],
    *,
    speech_start_sec: float,
    speech_end_sec: float,
) -> list[VowelTimelinePoint]:
    if not timeline:
        return []

    if speech_end_sec < speech_start_sec:
        speech_start_sec, speech_end_sec = speech_end_sec, speech_start_sec

    ordered = sorted(enumerate(timeline), key=lambda item: item[1].time_sec)
    by_original_index: dict[int, VowelTimelinePoint] = {}

    for ordered_index, (original_index, point) in enumerate(ordered):
        prev_time_sec = (
            ordered[ordered_index - 1][1].time_sec if ordered_index > 0 else None
        )
        next_time_sec = (
            ordered[ordered_index + 1][1].time_sec
            if ordered_index + 1 < len(ordered)
            else None
        )

        left_boundary_sec = (
            speech_start_sec
            if prev_time_sec is None
            else (prev_time_sec + point.time_sec) * 0.5
        )
        right_boundary_sec = (
            speech_end_sec
            if next_time_sec is None
            else (point.time_sec + next_time_sec) * 0.5
        )

        # Keep representative time unchanged and derive only duration.
        left_boundary_sec = min(left_boundary_sec, point.time_sec)
        right_boundary_sec = max(right_boundary_sec, point.time_sec)

        by_original_index[original_index] = VowelTimelinePoint(
            time_sec=point.time_sec,
            vowel=point.vowel,
            value=point.value,
            duration_sec=_ensure_positive_duration(right_boundary_sec - left_boundary_sec),
            start_sec=left_boundary_sec,
            end_sec=right_boundary_sec,
        )

    return [by_original_index[index] for index in range(len(timeline))]


def _ensure_positive_duration(duration_sec: float) -> float:
    if duration_sec > _MIN_EVENT_DURATION_SEC:
        return duration_sec
    return _MIN_EVENT_DURATION_SEC


def _even_interval_bounds(start_sec: float, end_sec: float, index: int, count: int) -> tuple[float, float]:
    if count <= 0:
        return (start_sec, start_sec + _MIN_EVENT_DURATION_SEC)
    if end_sec <= start_sec:
        return (start_sec, start_sec + _MIN_EVENT_DURATION_SEC)

    step_sec = (end_sec - start_sec) / count
    interval_start = start_sec + (step_sec * index)
    interval_end = start_sec + (step_sec * (index + 1))
    if index + 1 >= count:
        interval_end = end_sec
    if interval_end <= interval_start:
        interval_end = interval_start + _MIN_EVENT_DURATION_SEC
    return (interval_start, interval_end)


def _even_interval_bounds_with_margin(
    start_sec: float,
    end_sec: float,
    index: int,
    count: int,
) -> tuple[float, float]:
    if count <= 0:
        return (start_sec, start_sec + _MIN_EVENT_DURATION_SEC)
    if end_sec <= start_sec:
        return (start_sec, start_sec + _MIN_EVENT_DURATION_SEC)

    span_sec = end_sec - start_sec
    edge_margin_sec = min(0.012, span_sec * 0.2)
    inner_start = start_sec + edge_margin_sec
    inner_end = end_sec - edge_margin_sec
    if inner_end <= inner_start:
        return _even_interval_bounds(start_sec=start_sec, end_sec=end_sec, index=index, count=count)

    step_sec = (inner_end - inner_start) / count
    interval_start = inner_start + (step_sec * index)
    interval_end = inner_start + (step_sec * (index + 1))
    if interval_end <= interval_start:
        interval_end = interval_start + _MIN_EVENT_DURATION_SEC
    return (interval_start, interval_end)


def _even_time_in_interval(start_sec: float, end_sec: float, index: int, count: int) -> float:
    if count <= 0:
        raise ValueError("count must be > 0")
    if end_sec <= start_sec:
        return start_sec

    span_sec = end_sec - start_sec
    edge_margin_sec = min(0.012, span_sec * 0.2)
    inner_start = start_sec + edge_margin_sec
    inner_end = end_sec - edge_margin_sec
    if inner_end <= inner_start:
        return (start_sec + end_sec) * 0.5

    step = (inner_end - inner_start) / count
    time_sec = inner_start + (step * (index + 0.5))
    if time_sec < inner_start:
        return inner_start
    if time_sec > inner_end:
        return inner_end
    return time_sec
