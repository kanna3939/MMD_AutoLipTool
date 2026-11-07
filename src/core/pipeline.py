from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Sequence

from src.core.audio_processing import RmsSeriesData, WavAnalysisResult, analyze_wav_file, load_rms_series
from src.core.text_processing import (
    VowelToken,
    text_to_vowel_tokens,
)
from src.core.transition_acoustic import (
    TransitionAcousticSnapshot,
    build_transition_acoustic_snapshot,
    rebind_transition_acoustic_source,
    sha256_file,
)
from src.core.morph_name_sets import JAPANESE_OUTPUT_NAMES, validate_output_morph_names
from src.peak_value_resolver import MORPH_FRAME_OPEN_EPSILON
from src.core.whisper_timing import (
    SpeechTimingAnchor,
    WhisperTimingError,
    WhisperTimingResult,
    recognize_audio_timing,
)
from src.core.whisper_model_runtime import WhisperModelSession
from src.vmd_writer import (
    VMD_FPS,
    VowelTimelinePoint,
    write_morph_frames_vmd,
    write_morph_vmd,
)
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)


def _debug_record(trace: Any, method_name: str, *args: Any, **kwargs: Any) -> None:
    """Keep debug capture non-blocking and non-fatal to the analysis path."""
    if trace is None:
        return
    try:
        method = getattr(trace, method_name, None)
        if method is not None:
            method(*args, **kwargs)
    except Exception:
        return


def _debug_rms_payload(
    rms_series: RmsSeriesData,
    *,
    speech_start_sec: float,
    speech_end_sec: float,
) -> dict[str, object]:
    """Build B3-only RMS coverage/silence observations without changing RMS use."""
    threshold = 0.01
    minimum_silence_sec = 0.10
    hop_sec = (
        rms_series.hop_size_samples / rms_series.sample_rate_hz
        if rms_series.sample_rate_hz
        else 0.0
    )
    coverage: list[dict[str, object]] = []
    candidates: list[tuple[float, float]] = []
    for time_sec, value in zip(rms_series.times_sec, rms_series.values):
        if not isinstance(time_sec, (int, float)) or not math.isfinite(float(time_sec)):
            continue
        center = float(time_sec)
        start = max(float(speech_start_sec), center - hop_sec / 2.0)
        end = min(float(speech_end_sec), center + hop_sec / 2.0)
        if end <= start:
            continue
        finite = isinstance(value, (int, float)) and math.isfinite(float(value))
        entry = {
            "start_sec": start,
            "end_sec": end,
            "center_sec": center,
            "observed": finite,
            "reason": None if finite else "non_finite_rms",
        }
        coverage.append(entry)
        if finite and float(value) < threshold:
            candidates.append((start, end))

    merged: list[list[float]] = []
    for start, end in candidates:
        if merged and start <= merged[-1][1] + max(hop_sec * 1.5, 1e-9):
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    silence_intervals = [
        {
            "start_sec": start,
            "end_sec": end,
            "duration_sec": end - start,
            "classification": (
                "silence_candidate"
                if end - start >= minimum_silence_sec
                else "short_gap_observation"
            ),
        }
        for start, end in merged
    ]
    observed_coverage = [
        (float(entry["start_sec"]), float(entry["end_sec"]))
        for entry in coverage
        if entry.get("observed")
        and isinstance(entry.get("start_sec"), (int, float))
        and isinstance(entry.get("end_sec"), (int, float))
        and float(entry["end_sec"]) > float(entry["start_sec"])
    ]
    for interval in silence_intervals:
        interval_start = float(interval["start_sec"])
        interval_end = float(interval["end_sec"])
        cursor = interval_start
        for coverage_start, coverage_end in sorted(observed_coverage):
            if coverage_end <= cursor:
                continue
            if coverage_start > cursor + 1e-9:
                break
            cursor = max(cursor, coverage_end)
            if cursor >= interval_end - 1e-9:
                break
        if cursor >= interval_end - 1e-9:
            interval["coverage_status"] = "complete"
        elif cursor > interval_start + 1e-9:
            interval["coverage_status"] = "partial"
        else:
            interval["coverage_status"] = "unobserved"
        interval["provenance_status"] = "unavailable"
        interval["source_stage"] = "rms_load"
    return {
        "diagnostic_threshold_rms": threshold,
        "minimum_silence_duration_sec": minimum_silence_sec,
        "coverage_policy": "sample_center_plus_minus_half_hop_clipped_to_speech",
        "coverage": coverage,
        "silence_intervals": silence_intervals,
        "unobserved_policy": "gaps_are_not_filled_as_silence",
    }

_MIN_EVENT_DURATION_SEC = 1e-6
_RMS_BOUNDARY_SEARCH_SEC = 0.08
_TEXT_ANCHOR_TAIL_PAD_SEC = 0.16
_RMS_INTERVAL_THRESHOLD_RATIO = 0.12
_RMS_ABS_MIN_THRESHOLD = 0.01
_RMS_MIN_REFINED_DURATION_SEC = 0.03
_RMS_MAX_ADJACENT_OVERLAP_SEC = 0.02
_PEAK_WINDOW_HALO_SEC = 0.03
_RMS_UNAVAILABLE_FALLBACK_RATIO = 0.25
_DEFAULT_MORPH_UPPER_LIMIT = 0.9
_MORPH_FRAME_OPEN_EPSILON = MORPH_FRAME_OPEN_EPSILON
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


def _timeline_metadata_kwargs(point: VowelTimelinePoint) -> dict[str, object]:
    return {
        "vowel_token_index": point.vowel_token_index,
        "is_long_vowel_continuation": point.is_long_vowel_continuation,
        "long_vowel_source_token_index": point.long_vowel_source_token_index,
    }


def _validate_token_sequence(
    tokens: Sequence[VowelToken],
    vowels: Sequence[str],
) -> None:
    if len(tokens) != len(vowels):
        raise ValueError("tokens must match vowels one-to-one")
    for index, (token, vowel) in enumerate(zip(tokens, vowels)):
        if getattr(token, "vowel", None) != vowel:
            raise ValueError("tokens must match vowels one-to-one")
        if getattr(token, "token_index", None) != index:
            raise ValueError("tokens must have contiguous token indexes")
        continuation = getattr(token, "is_long_vowel_continuation", False)
        source = getattr(token, "long_vowel_source_token_index", None)
        if not isinstance(continuation, bool):
            raise ValueError("token continuation flag must be bool")
        if continuation:
            if isinstance(source, bool) or not isinstance(source, int) or source < 0 or source >= index:
                raise ValueError("token continuation source must point backwards")
        elif source is not None:
            raise ValueError("non-continuation token cannot carry a source")


def _repair_long_vowel_same_morph_boundaries(
    timeline: Sequence[VowelTimelinePoint],
    *,
    debug_trace: Any = None,
    debug_call_site: str = "unknown",
) -> list[VowelTimelinePoint]:
    """Keep explicit long runs resolvable at adjacent same-morph boundaries.

    RMS interval refinement may place a regular same-vowel event on the exact
    frame where an isolated long run must close.  The shared resolver correctly
    rejects a required zero and a positive peak on the same morph/frame, but a
    successful analysis must not manufacture that conflict.  Preserve the long
    terminal frame and move only the neighbouring opening edge/peak when the
    interval has enough room.  Unrepairable short spans remain unchanged so the
    resolver continues to fail closed.
    """
    repaired = list(timeline)
    if len(repaired) < 2:
        _debug_record(
            debug_trace,
            "record_boundary_repair",
            repair_function="long_boundary",
            call_site=debug_call_site,
            before=timeline,
            after=repaired,
        )
        return repaired

    timeline_end_frame = max(
        int(round(float(point.end_sec) * VMD_FPS))
        for point in repaired
    )

    long_source_indices = {
        point.long_vowel_source_token_index
        for point in repaired
        if point.is_long_vowel_continuation
        and point.long_vowel_source_token_index is not None
    }
    continuation_indices = {
        index
        for index, point in enumerate(repaired)
        if point.is_long_vowel_continuation
    }
    long_indices = long_source_indices | continuation_indices
    terminal_indices_by_source: dict[int, int] = {}
    for index, point in enumerate(repaired):
        if (
            point.is_long_vowel_continuation
            and point.long_vowel_source_token_index is not None
        ):
            terminal_indices_by_source[point.long_vowel_source_token_index] = index
    terminal_indices = set(terminal_indices_by_source.values())

    for index in range(1, len(repaired)):
        previous = repaired[index - 1]
        current = repaired[index]
        if previous.vowel != current.vowel:
            continue

        previous_end_frame = int(round(float(previous.end_sec) * VMD_FPS))
        current_start_frame = int(round(float(current.start_sec) * VMD_FPS))
        current_peak_frame = int(round(float(current.time_sec) * VMD_FPS))
        current_end_frame = int(round(float(current.end_sec) * VMD_FPS))

        # A regular event after a long run starts one frame after the long
        # terminal.  This leaves the terminal zero intact in decay mode and
        # shares the post-terminal closing zero in hold mode.
        if index - 1 in terminal_indices and index not in long_indices:
            required_start_frame = previous_end_frame + 1
            required_peak_frame = max(
                current_peak_frame,
                required_start_frame + 1,
            )
            required_end_frame = max(
                current_end_frame,
                required_peak_frame + 1,
            )
            if (
                (
                    current_start_frame < required_start_frame
                    or current_peak_frame < required_peak_frame
                    or current_end_frame < required_end_frame
                )
                and required_end_frame <= timeline_end_frame
            ):
                start_sec = required_start_frame / VMD_FPS
                end_sec = required_end_frame / VMD_FPS
                repaired[index] = replace(
                    current,
                    start_sec=start_sec,
                    time_sec=required_peak_frame / VMD_FPS,
                    end_sec=end_sec,
                    duration_sec=end_sec - start_sec,
                )
            continue

        # A long source after a same-vowel event begins from the preceding
        # zero boundary and reaches its positive peak afterwards.  A source
        # immediately following a long terminal has a stricter boundary
        # contract: preserve an exact same-frame handoff, repair start
        # intrusion, and move only the peak that collides with the normal
        # post-terminal closing zero.  When that source also owns a
        # continuation and the normal repair would exceed its end, use the
        # B2 compact handoff: share the preceding terminal frame as the
        # canonical zero and place the positive peak at the next frame.
        # Other same-vowel long-source cases retain the existing B1 repair
        # behavior.
        if index in long_source_indices:
            if index - 1 in terminal_indices:
                if current_start_frame == previous_end_frame:
                    required_start_frame = previous_end_frame
                    required_peak_frame = max(
                        current_peak_frame,
                        required_start_frame + 1,
                    )
                elif current_start_frame < previous_end_frame:
                    required_start_frame = previous_end_frame + 1
                    required_peak_frame = max(
                        current_peak_frame,
                        required_start_frame + 1,
                    )
                elif (
                    current_start_frame == previous_end_frame + 1
                    and current_peak_frame == previous_end_frame + 1
                ):
                    required_start_frame = current_start_frame
                    required_peak_frame = previous_end_frame + 2
                else:
                    continue

                if (
                    current_start_frame < previous_end_frame
                    and required_peak_frame > current_end_frame
                    and index in terminal_indices_by_source
                ):
                    compact_start_frame = previous_end_frame
                    compact_peak_frame = max(
                        current_peak_frame,
                        compact_start_frame + 1,
                    )
                    if (
                        compact_start_frame <= compact_peak_frame <= current_end_frame
                        and compact_start_frame <= timeline_end_frame
                    ):
                        start_sec = compact_start_frame / VMD_FPS
                        repaired[index] = replace(
                            current,
                            start_sec=start_sec,
                            time_sec=compact_peak_frame / VMD_FPS,
                            duration_sec=float(current.end_sec) - start_sec,
                        )
                    continue

                if (
                    required_start_frame < required_peak_frame
                    and required_peak_frame <= current_end_frame
                ):
                    start_sec = required_start_frame / VMD_FPS
                    repaired[index] = replace(
                        current,
                        start_sec=start_sec,
                        time_sec=required_peak_frame / VMD_FPS,
                        duration_sec=float(current.end_sec) - start_sec,
                    )
                continue

            required_start_frame = max(current_start_frame, previous_end_frame)
            required_peak_frame = max(
                current_peak_frame,
                required_start_frame + 1,
            )
            if (
                current_peak_frame <= previous_end_frame
                and required_peak_frame <= current_end_frame
            ):
                start_sec = required_start_frame / VMD_FPS
                repaired[index] = replace(
                    current,
                    start_sec=start_sec,
                    time_sec=required_peak_frame / VMD_FPS,
                    duration_sec=float(current.end_sec) - start_sec,
                )

    _debug_record(
        debug_trace,
        "record_boundary_repair",
        repair_function="long_boundary",
        call_site=debug_call_site,
        before=timeline,
        after=repaired,
    )
    return repaired


def _repair_interleaved_same_morph_boundaries(
    timeline: Sequence[VowelTimelinePoint],
    *,
    debug_trace: Any = None,
    debug_call_site: str = "unknown",
) -> list[VowelTimelinePoint]:
    """Keep separated events of the same morph resolvable after RMS refinement.

    Events separated by another vowel are emitted as different shapes.  RMS
    refinement can make the later interval begin before the earlier same-morph
    interval has reached its required zero frame.  Move only the later opening
    edge (and, when necessary, its peak) to that zero boundary.  Adjacent
    same-vowel events remain untouched because the resolver intentionally
    combines them into one envelope.
    """
    repaired = list(timeline)
    if len(repaired) < 3:
        _debug_record(
            debug_trace,
            "record_boundary_repair",
            repair_function="interleaved_boundary",
            call_site=debug_call_site,
            before=timeline,
            after=repaired,
        )
        return repaired

    previous_index_by_vowel: dict[str, int] = {}

    for index, current in enumerate(repaired):
        previous_index = previous_index_by_vowel.get(current.vowel)
        previous_index_by_vowel[current.vowel] = index
        if previous_index is None or previous_index == index - 1:
            continue
        if current.is_long_vowel_continuation:
            continue

        previous = repaired[previous_index]
        previous_end_frame = int(round(float(previous.end_sec) * VMD_FPS))
        current_start_frame = int(round(float(current.start_sec) * VMD_FPS))
        if current_start_frame >= previous_end_frame:
            continue

        current_peak_frame = int(round(float(current.time_sec) * VMD_FPS))
        current_end_frame = int(round(float(current.end_sec) * VMD_FPS))
        required_start_frame = previous_end_frame
        required_peak_frame = max(
            current_peak_frame,
            required_start_frame + 1,
        )
        if required_peak_frame >= current_end_frame:
            continue

        start_sec = required_start_frame / VMD_FPS
        repaired[index] = replace(
            current,
            start_sec=start_sec,
            time_sec=required_peak_frame / VMD_FPS,
            duration_sec=float(current.end_sec) - start_sec,
        )

    _debug_record(
        debug_trace,
        "record_boundary_repair",
        repair_function="interleaved_boundary",
        call_site=debug_call_site,
        before=timeline,
        after=repaired,
    )
    return repaired


def _repair_resolver_same_morph_boundaries(
    timeline: Sequence[VowelTimelinePoint],
    *,
    debug_trace: Any = None,
    debug_call_site: str = "unknown",
) -> list[VowelTimelinePoint]:
    return _repair_interleaved_same_morph_boundaries(
        _repair_long_vowel_same_morph_boundaries(
            timeline,
            debug_trace=debug_trace,
            debug_call_site=debug_call_site,
        ),
        debug_trace=debug_trace,
        debug_call_site=debug_call_site,
    )


class PipelineError(ValueError):
    """Recoverable pipeline error for GUI-facing messaging."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        detail_code: str | None = None,
        failure_class: str = "none",
    ) -> None:
        self.error_code = error_code
        self.detail_code = detail_code
        self.failure_class = failure_class
        super().__init__(message)


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
class VmdGenerationResult:
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
    transition_acoustic_snapshot: TransitionAcousticSnapshot | None = None
    source_silence_intervals: tuple[tuple[float, float, str, str, str], ...] = ()


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
class _PeakSampleSelection:
    sample_time_sec: float | None
    sample_value: float | None
    frame_no: int | None
    reason: str
    source_frame_blocked: bool = False


@dataclass(frozen=True)
class PeakValueObservation:
    """pipeline が確定した observation 契約の正本。"""
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
    full_span_start_frame: int | None = None
    full_span_end_frame: int | None = None
    silence_core_frame_ranges: tuple[tuple[int, int], ...] = ()
    boundary_fringe_frame_ranges: tuple[tuple[int, int], ...] = ()
    silence_core_overlap: bool = False
    coverage_status: str = "unobserved"
    provenance_status: str = "unavailable"
    bridge_rejection_reason_code: str | None = None
    base_event_silence_core_overlap: bool = False
    positive_core_frame_ranges: tuple[tuple[int, int], ...] = ()
    long_vowel_role: str | None = None
    manual_adjustment_applied: bool = False
    base_event_rejection_reason_code: str | None = None
    boundary_only: bool = False
    boundary_frame: int | None = None
    boundary_point_kind: str | None = None


@dataclass(frozen=True)
class _ObservedTimelineBuildResult:
    timeline: list[VowelTimelinePoint]
    observations: list[PeakValueObservation] | None = None
    transition_acoustic_snapshot: TransitionAcousticSnapshot | None = None
    source_silence_intervals: tuple[tuple[float, float, str, str, str], ...] = ()


@dataclass(frozen=True)
class _ObservationCandidateContract:
    """downstream へ handoff する candidate 判定の読み取り専用 view."""

    previous_non_zero_event_index: int | None
    next_non_zero_event_index: int | None
    span_start_index: int | None
    span_end_index: int | None
    is_bridgeable_same_vowel_candidate: bool
    is_same_vowel_burst_candidate: bool
    is_bridgeable_cross_vowel_candidate: bool
    is_cross_vowel_zero_run_floor_candidate: bool
    resolved_bridge_candidate_reason: str | None


def build_even_vowel_timeline(
    vowels: Sequence[str],
    speech_start_sec: float,
    speech_end_sec: float,
    *,
    tokens: Sequence[VowelToken] | None = None,
) -> list[VowelTimelinePoint]:
    if not vowels:
        raise ValueError("No vowels to allocate.")
    if speech_start_sec < 0 or speech_end_sec < 0:
        raise ValueError("Speech interval must be non-negative.")
    if speech_end_sec < speech_start_sec:
        raise ValueError("speech_end_sec must be >= speech_start_sec.")

    duration_sec = speech_end_sec - speech_start_sec
    count = len(vowels)
    if tokens is not None:
        _validate_token_sequence(tokens, vowels)
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
                **({
                    "vowel_token_index": tokens[index].token_index,
                    "is_long_vowel_continuation": tokens[index].is_long_vowel_continuation,
                    "long_vowel_source_token_index": tokens[index].long_vowel_source_token_index,
                } if tokens is not None else {}),
            )
        )
    return timeline


def build_anchor_based_vowel_timeline(
    vowels: Sequence[str],
    timing_anchors: Sequence[SpeechTimingAnchor],
    speech_start_sec: float,
    speech_end_sec: float,
    *,
    tokens: Sequence[VowelToken] | None = None,
    source_timing_anchors: Sequence[SpeechTimingAnchor] | None = None,
    timing_source: str | None = None,
    source_text: str | None = None,
    debug_trace: Any = None,
) -> list[VowelTimelinePoint]:
    if not vowels:
        raise ValueError("No vowels to allocate.")
    if tokens is not None:
        _validate_token_sequence(tokens, vowels)
    if speech_start_sec < 0 or speech_end_sec < 0:
        raise ValueError("Speech interval must be non-negative.")
    if speech_end_sec < speech_start_sec:
        raise ValueError("speech_end_sec must be >= speech_start_sec.")

    clipped_anchors = _clip_anchors_to_speech_interval(
        timing_anchors=timing_anchors,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
    )

    source_anchors = timing_anchors if source_timing_anchors is None else source_timing_anchors
    source_anchor_records = [
        {
            "source_anchor_index": index,
            "start_sec": anchor.start_sec,
            "end_sec": anchor.end_sec,
        }
        for index, anchor in enumerate(source_anchors)
    ]

    source_anchor_candidates: list[dict[str, Any]] = []
    for source_index, anchor in enumerate(source_anchors):
        clipped_start_sec = max(anchor.start_sec, speech_start_sec)
        clipped_end_sec = min(anchor.end_sec, speech_end_sec)
        if clipped_end_sec > clipped_start_sec:
            source_anchor_candidates.append(
                {
                    "source_anchor_index": source_index,
                    "start_sec": clipped_start_sec,
                    "end_sec": clipped_end_sec,
                }
            )

    matched_source_anchor_indexes: set[int] = set()
    used_anchor_records: list[dict[str, Any]] = []
    for used_anchor_index, anchor in enumerate(clipped_anchors):
        source_anchor_index = next(
            (
                candidate["source_anchor_index"]
                for candidate in source_anchor_candidates
                if candidate["source_anchor_index"] not in matched_source_anchor_indexes
                and candidate["start_sec"] == anchor.start_sec
                and candidate["end_sec"] == anchor.end_sec
            ),
            None,
        )
        if source_anchor_index is not None:
            matched_source_anchor_indexes.add(source_anchor_index)
        used_anchor_records.append(
            {
                "used_anchor_index": used_anchor_index,
                "source_anchor_index": source_anchor_index,
                "start_sec": anchor.start_sec,
                "end_sec": anchor.end_sec,
                "assignments": [],
            }
        )

    def record_fallback(
        status: str,
        fallback_timeline: Sequence[VowelTimelinePoint],
        *,
        allocation_strategy: str = "duration_weighted",
        lexical_anchor_matches: Sequence[dict[str, int]] = (),
    ) -> None:
        _debug_record(
            debug_trace,
            "record_stage",
            "timing_anchor_allocation",
            payload={
                "timing_source": timing_source or "unspecified",
                "allocation_status": status,
                "allocation_strategy": allocation_strategy,
                "lexical_anchor_matches": list(lexical_anchor_matches),
                "source_anchors": source_anchor_records,
                "used_anchors": used_anchor_records,
                "fallback_assignments": [
                    {
                        "event_index": index,
                        "vowel": point.vowel,
                        "token_index": (
                            tokens[index].token_index if tokens is not None else index
                        ),
                        "time_sec": point.time_sec,
                    }
                    for index, point in enumerate(fallback_timeline)
                ],
            },
        )

    if not clipped_anchors:
        fallback_timeline = build_even_vowel_timeline(
            vowels=vowels,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
            tokens=tokens,
        )
        record_fallback("no_usable_anchors_even_fallback", fallback_timeline)
        return fallback_timeline

    allocation, allocation_strategy, lexical_anchor_matches = (
        _allocate_vowels_to_anchors_with_source_text(
            vowels=vowels,
            tokens=tokens,
            anchors=clipped_anchors,
            source_text=source_text,
        )
    )
    text_matched_anchor_indexes = {
        item["anchor_index"]
        for item in lexical_anchor_matches
        if "anchor_index" in item
    }
    timeline: list[VowelTimelinePoint] = []
    vowel_index = 0
    for anchor_index, (anchor, count) in enumerate(zip(clipped_anchors, allocation)):
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
            if (
                anchor_index in text_matched_anchor_indexes
                and local_index == count - 1
            ):
                end_sec = min(
                    speech_end_sec,
                    end_sec + _TEXT_ANCHOR_TAIL_PAD_SEC,
                )
            duration_sec = _ensure_positive_duration(end_sec - start_sec)
            timeline.append(
                VowelTimelinePoint(
                    time_sec=time_sec,
                    vowel=vowels[vowel_index],
                    duration_sec=duration_sec,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    **({
                        "vowel_token_index": tokens[vowel_index].token_index,
                        "is_long_vowel_continuation": tokens[vowel_index].is_long_vowel_continuation,
                        "long_vowel_source_token_index": tokens[vowel_index].long_vowel_source_token_index,
                    } if tokens is not None else {}),
                )
            )
            used_anchor_records[anchor_index]["assignments"].append(
                {
                    "event_index": len(timeline) - 1,
                    "vowel": vowels[vowel_index],
                    "token_index": (
                        tokens[vowel_index].token_index if tokens is not None else vowel_index
                    ),
                }
            )
            vowel_index += 1

    if vowel_index != len(vowels):
        # Safety fallback in case the allocation and generation diverge.
        fallback_timeline = build_even_vowel_timeline(
            vowels=vowels,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
            tokens=tokens,
        )
        record_fallback(
            "allocation_safety_even_fallback",
            fallback_timeline,
            allocation_strategy=allocation_strategy,
            lexical_anchor_matches=lexical_anchor_matches,
        )
        return fallback_timeline

    _debug_record(
        debug_trace,
        "record_stage",
        "timing_anchor_allocation",
        payload={
            "timing_source": timing_source or "unspecified",
            "allocation_status": "anchors_allocated",
            "allocation_strategy": allocation_strategy,
            "lexical_anchor_matches": lexical_anchor_matches,
            "source_anchors": source_anchor_records,
            "used_anchors": used_anchor_records,
            "fallback_assignments": [],
        },
    )
    return timeline


def build_vowel_timing_plan(
    *,
    text_content: str,
    wav_path: str | Path,
    wav_analysis: WavAnalysisResult,
    whisper_model_session: WhisperModelSession | None = None,
    upper_limit: float = _DEFAULT_MORPH_UPPER_LIMIT,
    phase_callback: Callable[[str], None] | None = None,
    whisper_timing_result: WhisperTimingResult | None = None,
    debug_trace: Any = None,
    collect_transition_acoustics: bool = False,
) -> VowelTimingPlan:
    if phase_callback: phase_callback("音声入力確認中")
    if type(collect_transition_acoustics) is not bool:
        raise ValueError("collect_transition_acoustics must be a boolean")
    if upper_limit < 0.0:
        raise ValueError("upper_limit must be >= 0.0.")

    tokens = text_to_vowel_tokens(text_content)
    _debug_record(
        debug_trace,
        "set_analysis_text",
        text_content,
        source="provided",
    )
    vowels = [token.vowel for token in tokens]
    if not vowels:
        raise ValueError("No vowels extracted from TEXT.")
    if not wav_analysis.has_speech:
        raise ValueError("No speech interval detected in WAV.")

    anchors: list[SpeechTimingAnchor] = []
    source_timing_anchors: list[SpeechTimingAnchor] = []
    timing_source = "even_fallback"
    warning: str | None = None

    if phase_callback: phase_callback("Whisper 解析中")
    if whisper_timing_result is None:
        if whisper_model_session is None:
            raise PipelineError(
                "Verified Whisper model session is required for analysis.",
                error_code="timing_plan_build_failed",
                detail_code="analysis_request_missing",
                failure_class="model_unavailable",
            )
        try:
            whisper_result = recognize_audio_timing(
                wav_path=wav_path,
                model_session=whisper_model_session,
                language="ja",
                fp16=False,
            )
            source_timing_anchors = list(whisper_result.anchors)
            anchors, timing_source, warning = _resolve_whisper_timing_result(
                whisper_result=whisper_result,
                wav_analysis=wav_analysis,
            )
        except WhisperTimingError as error:
            if error.failure_class == "none":
                warning = str(error)
            else:
                raise PipelineError(
                    f"Whisper analysis failed: {error}",
                    error_code="whisper_analysis_failed",
                    detail_code=error.code,
                    failure_class=error.failure_class,
                ) from error
    else:
        if (
            whisper_model_session is not None
            and whisper_timing_result.model_identity is not None
            and whisper_timing_result.model_identity != whisper_model_session.identity
        ):
            raise PipelineError(
                "Supplied Whisper timing result belongs to a different model.",
                error_code="whisper_analysis_failed",
                detail_code="model_identity_mismatch",
                failure_class="integrity_mismatch",
            )
        source_timing_anchors = list(whisper_timing_result.anchors)
        anchors, timing_source, warning = _resolve_whisper_timing_result(
            whisper_result=whisper_timing_result,
            wav_analysis=wav_analysis,
        )

    if phase_callback: phase_callback("母音タイミング整形中")
    initial_timeline = build_anchor_based_vowel_timeline(
        vowels=vowels,
        timing_anchors=anchors,
        speech_start_sec=wav_analysis.speech_start_sec,
        speech_end_sec=wav_analysis.speech_end_sec,
        tokens=tokens,
        source_timing_anchors=source_timing_anchors,
        timing_source=timing_source,
        source_text=text_content,
        debug_trace=debug_trace,
    )
    _debug_record(
        debug_trace,
        "record_stage",
        "input_snapshot",
        payload={
            "input_mode": "analysis",
            "text_source": "provided",
            "timing_source": timing_source,
            "duration_sec": wav_analysis.duration_sec,
            "has_speech": wav_analysis.has_speech,
            "speech_start_sec": wav_analysis.speech_start_sec,
            "speech_end_sec": wav_analysis.speech_end_sec,
        },
    )
    _debug_record(debug_trace, "record_timeline", "timeline_initial", initial_timeline)
    
    if phase_callback: phase_callback("結果反映中")
    observed_timeline = _refine_timeline_intervals_with_observations(
        timeline=initial_timeline,
        wav_path=wav_path,
        speech_start_sec=wav_analysis.speech_start_sec,
        speech_end_sec=wav_analysis.speech_end_sec,
        upper_limit=upper_limit,
        debug_trace=debug_trace,
        collect_transition_acoustics=collect_transition_acoustics,
    )
    _, alignment_strategy, lexical_anchor_matches = (
        _allocate_vowels_to_anchors_with_source_text(
            vowels=vowels,
            tokens=tokens,
            anchors=anchors,
            source_text=text_content,
        )
    )
    if alignment_strategy == "source_text_phonetic_anchor_match":
        observed_timeline = _align_source_text_anchor_peaks(
            observed=observed_timeline,
            wav_path=wav_path,
            anchors=anchors,
            lexical_anchor_matches=lexical_anchor_matches,
        )

    transition_acoustic_snapshot = observed_timeline.transition_acoustic_snapshot
    if collect_transition_acoustics and transition_acoustic_snapshot is not None:
        try:
            final_source_sha256 = sha256_file(wav_path)
        except OSError:
            final_source_sha256 = None
        transition_acoustic_snapshot = rebind_transition_acoustic_source(
            transition_acoustic_snapshot,
            source_sha256_after=final_source_sha256,
        )

    return VowelTimingPlan(
        vowels=vowels,
        timeline=observed_timeline.timeline,
        anchors=anchors,
        source=timing_source,
        warning=warning,
        observations=observed_timeline.observations,
        transition_acoustic_snapshot=transition_acoustic_snapshot,
        source_silence_intervals=observed_timeline.source_silence_intervals,
    )


def _align_source_text_anchor_peaks(
    *,
    observed: _ObservedTimelineBuildResult,
    wav_path: str | Path,
    anchors: Sequence[SpeechTimingAnchor],
    lexical_anchor_matches: Sequence[dict[str, int]],
) -> _ObservedTimelineBuildResult:
    """Place text-matched vowels on their local acoustic peaks when ordered."""
    if not observed.observations:
        return observed

    rms_series = load_rms_series(str(wav_path))
    observation_by_event = {
        observation.event_index: observation
        for observation in observed.observations
    }
    points = list(observed.timeline)
    observations = list(observed.observations)
    observation_index_by_event = {
        observation.event_index: index
        for index, observation in enumerate(observations)
    }

    for match in lexical_anchor_matches:
        if not (match.get("phonetic_match") or match.get("kana_anchor_peak")):
            continue
        anchor_index = match.get("anchor_index")
        if anchor_index is None or not 0 <= anchor_index < len(anchors):
            continue
        target_token_index = match["token_end"] - 1
        anchor = anchors[anchor_index]
        if match.get("phonetic_match"):
            search_start_sec = anchor.end_sec - _PEAK_WINDOW_HALO_SEC
            search_end_sec = (
                anchor.end_sec
                + _TEXT_ANCHOR_TAIL_PAD_SEC
                + _PEAK_WINDOW_HALO_SEC
            )
        else:
            search_start_sec = anchor.start_sec - _RMS_BOUNDARY_SEARCH_SEC
            search_end_sec = anchor.end_sec

        for event_index, point in enumerate(points):
            if point.vowel_token_index != target_token_index:
                continue
            observation = observation_by_event.get(event_index)
            if observation is None or observation.peak_value <= 0.0:
                break
            candidates = [
                (time_sec, rms_value)
                for time_sec, rms_value in zip(
                    rms_series.times_sec,
                    rms_series.values,
                )
                if search_start_sec <= time_sec <= search_end_sec
                and math.isfinite(time_sec)
                and math.isfinite(rms_value)
            ]
            if not candidates:
                break
            peak_time_sec, peak_rms = max(candidates, key=lambda item: item[1])
            if peak_rms <= _RMS_ABS_MIN_THRESHOLD:
                break
            peak_frame = _seconds_to_frame(peak_time_sec)
            if any(
                start_frame <= peak_frame <= end_frame
                for start_frame, end_frame in observation.silence_core_frame_ranges
            ):
                break
            previous_frame = (
                None
                if event_index == 0
                else _seconds_to_frame(points[event_index - 1].time_sec)
            )
            next_frame = (
                None
                if event_index + 1 >= len(points)
                else _seconds_to_frame(points[event_index + 1].time_sec)
            )
            if (
                (previous_frame is not None and peak_frame < previous_frame)
                or (next_frame is not None and peak_frame > next_frame)
            ):
                break

            aligned_time_sec = peak_frame / VMD_FPS
            refined_start_sec = observation.refined_interval_start_sec
            refined_end_sec = observation.refined_interval_end_sec
            event_start_frame, event_end_frame = _event_frame_range(
                refined_start_sec,
                refined_end_sec,
            )
            # Keep a short text-matched event from extending its positive shape
            # across the next silence core after its acoustic peak.
            silence_start_frame = next(
                (
                    start_frame
                    for start_frame, _end_frame in observation.silence_core_frame_ranges
                    if peak_frame < start_frame < event_end_frame
                    and event_start_frame < start_frame
                ),
                None,
            )
            if silence_start_frame is not None:
                clipped_end_sec = silence_start_frame / VMD_FPS
                if clipped_end_sec > max(refined_start_sec, aligned_time_sec):
                    refined_end_sec = clipped_end_sec

            points[event_index] = replace(
                point,
                time_sec=aligned_time_sec,
                start_sec=refined_start_sec,
                end_sec=refined_end_sec,
                duration_sec=max(0.0, refined_end_sec - refined_start_sec),
            )
            observation_index = observation_index_by_event.get(event_index)
            if observation_index is not None:
                updated_observation = observations[observation_index]
                updated_evaluation = replace(
                    updated_observation.evaluation,
                    interval_end_sec=refined_end_sec,
                    peak_window_end_sec=min(
                        updated_observation.evaluation.peak_window_end_sec,
                        refined_end_sec,
                    ),
                )
                observations[observation_index] = replace(
                    updated_observation,
                    time_sec=aligned_time_sec,
                    refined_interval_end_sec=refined_end_sec,
                    peak_window_end_sec=min(
                        updated_observation.peak_window_end_sec,
                        refined_end_sec,
                    ),
                    evaluation=updated_evaluation,
                )
            break

    return _ObservedTimelineBuildResult(
        timeline=points,
        observations=observations,
        transition_acoustic_snapshot=observed.transition_acoustic_snapshot,
        source_silence_intervals=observed.source_silence_intervals,
    )


def _resolve_whisper_timing_result(
    *,
    whisper_result: WhisperTimingResult,
    wav_analysis: WavAnalysisResult,
) -> tuple[list[SpeechTimingAnchor], str, str | None]:
    anchors = _clip_anchors_to_speech_interval(
        timing_anchors=whisper_result.anchors,
        speech_start_sec=wav_analysis.speech_start_sec,
        speech_end_sec=wav_analysis.speech_end_sec,
    )
    if anchors:
        return anchors, f"whisper_{whisper_result.source}", None
    return [], "even_fallback", "Whisper returned no anchors inside the detected speech interval."


def resolve_vmd_writer_timing_plan(
    timing_plan: VowelTimingPlan,
    *,
    speech_start_sec: float,
    speech_end_sec: float,
) -> VowelTimingPlan:
    """Return the exact timing plan shape used immediately before VMD writing.

    Caller-supplied plans historically received a last-minute duration repair in
    both VMD entry points.  Keeping that boundary in one pure helper lets core
    diagnostics fingerprint the same timeline and observation state that the
    writer receives, without changing the timing algorithm itself.
    """
    if not _timeline_has_non_positive_duration(timing_plan.timeline):
        return timing_plan

    return VowelTimingPlan(
        vowels=timing_plan.vowels,
        timeline=_infer_durations_from_midpoints(
            timing_plan.timeline,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
        ),
        anchors=timing_plan.anchors,
        source=timing_plan.source,
        warning=timing_plan.warning,
        observations=None,
        transition_acoustic_snapshot=timing_plan.transition_acoustic_snapshot,
        source_silence_intervals=timing_plan.source_silence_intervals,
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
    effective_shape_plan: object | None = None,
    output_morph_names: Sequence[str] = JAPANESE_OUTPUT_NAMES,
) -> PipelineResult:
    normalized_output_morph_names = validate_output_morph_names(output_morph_names)
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
        raise PipelineError(
            "A verified timing plan is required before VMD writing.",
            error_code="timing_plan_build_failed",
            detail_code="analysis_request_missing",
            failure_class="model_unavailable",
        )
    elif not resolved_timing_plan.timeline:
        raise PipelineError("Provided timing plan has no timeline points.")
    elif resolved_timing_plan.timeline:
        resolved_timing_plan = resolve_vmd_writer_timing_plan(
            resolved_timing_plan,
            speech_start_sec=wav_analysis.speech_start_sec,
            speech_end_sec=wav_analysis.speech_end_sec,
        )

    try:
        if effective_shape_plan is None:
            writer_kwargs = {
                "output_path": out_file,
                "timeline": resolved_timing_plan.timeline,
                "model_name": model_name,
                "observations": resolved_timing_plan.observations,
                "closing_hold_frames": closing_hold_frames,
                "closing_softness_frames": closing_softness_frames,
            }
            if normalized_output_morph_names != JAPANESE_OUTPUT_NAMES:
                writer_kwargs["output_morph_names"] = normalized_output_morph_names
            write_morph_vmd(**writer_kwargs)
        else:
            morph_frames = build_morph_frames_from_effective_shape_plan(
                effective_shape_plan
            )
            writer_kwargs = {
                "output_path": out_file,
                "morph_frames": morph_frames,
                "model_name": model_name,
            }
            if normalized_output_morph_names != JAPANESE_OUTPUT_NAMES:
                writer_kwargs["output_morph_names"] = normalized_output_morph_names
            write_morph_frames_vmd(**writer_kwargs)
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


def generate_vmd_from_timing_plan(
    wav_path: str | Path,
    output_path: str | Path,
    *,
    timing_plan: VowelTimingPlan,
    silence_threshold: float = 0.02,
    model_name: str = "AutoLipTool",
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
    effective_shape_plan: object | None = None,
    output_morph_names: Sequence[str] = JAPANESE_OUTPUT_NAMES,
) -> VmdGenerationResult:
    normalized_output_morph_names = validate_output_morph_names(output_morph_names)
    wav_file = Path(wav_path)
    out_file = Path(output_path)

    if not wav_file.exists():
        raise PipelineError(f"WAV file not found: {wav_file}")
    if not timing_plan.timeline:
        raise PipelineError("Provided timing plan has no timeline points.")

    try:
        wav_analysis = analyze_wav_file(str(wav_file), silence_threshold=silence_threshold)
    except (ValueError, OSError) as error:
        raise PipelineError(f"Failed to analyze WAV file: {error}") from error

    resolved_timing_plan = timing_plan
    if resolved_timing_plan.timeline:
        resolved_timing_plan = resolve_vmd_writer_timing_plan(
            resolved_timing_plan,
            speech_start_sec=wav_analysis.speech_start_sec,
            speech_end_sec=wav_analysis.speech_end_sec,
        )

    try:
        if effective_shape_plan is None:
            writer_kwargs = {
                "output_path": out_file,
                "timeline": resolved_timing_plan.timeline,
                "model_name": model_name,
                "observations": resolved_timing_plan.observations,
                "closing_hold_frames": closing_hold_frames,
                "closing_softness_frames": closing_softness_frames,
            }
            if normalized_output_morph_names != JAPANESE_OUTPUT_NAMES:
                writer_kwargs["output_morph_names"] = normalized_output_morph_names
            write_morph_vmd(**writer_kwargs)
        else:
            morph_frames = build_morph_frames_from_effective_shape_plan(
                effective_shape_plan
            )
            writer_kwargs = {
                "output_path": out_file,
                "morph_frames": morph_frames,
                "model_name": model_name,
            }
            if normalized_output_morph_names != JAPANESE_OUTPUT_NAMES:
                writer_kwargs["output_morph_names"] = normalized_output_morph_names
            write_morph_frames_vmd(**writer_kwargs)
    except OSError as error:
        raise PipelineError(f"Failed to save VMD file: {error}") from error

    return VmdGenerationResult(
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


def _allocate_vowels_to_anchors_with_source_text(
    *,
    vowels: Sequence[str],
    tokens: Sequence[VowelToken] | None,
    anchors: Sequence[SpeechTimingAnchor],
    source_text: str | None,
) -> tuple[list[int], str, list[dict[str, int]]]:
    """Use reliable text or unique phonetic matches to constrain anchor counts."""
    duration_allocation = _allocate_vowels_to_anchors(len(vowels), anchors)
    if not source_text or not tokens or len(tokens) != len(vowels):
        return duration_allocation, "duration_weighted", []

    normalized_source = unicodedata.normalize("NFKC", source_text)
    searchable_source = normalized_source.casefold()
    source_token_vowels = [token.vowel for token in tokens]
    matches: list[tuple[int, int, int]] = []
    search_cursor = 0
    previous_token_end = 0
    phonetic_match_found = False

    for anchor_index, anchor in enumerate(anchors):
        anchor_text = unicodedata.normalize("NFKC", anchor.text.strip())
        searchable_anchor = anchor_text.casefold()
        if not _is_reliable_anchor_text(searchable_anchor):
            continue

        source_char_start = searchable_source.find(searchable_anchor, search_cursor)
        if source_char_start < 0:
            if _is_kana_anchor_text(anchor_text):
                try:
                    anchor_vowels = [
                        token.vowel for token in text_to_vowel_tokens(anchor_text)
                    ]
                except ValueError:
                    anchor_vowels = []
                if (
                    len(anchor_vowels) >= 3
                    and (anchor.end_sec - anchor.start_sec) * VMD_FPS
                    >= len(anchor_vowels) * 2
                ):
                    candidate_starts = [
                        token_start
                        for token_start in range(
                            previous_token_end,
                            len(source_token_vowels) - len(anchor_vowels) + 1,
                        )
                        if source_token_vowels[
                            token_start : token_start + len(anchor_vowels)
                        ]
                        == anchor_vowels
                    ]
                    if len(candidate_starts) == 1:
                        token_start = candidate_starts[0]
                        token_end = token_start + len(anchor_vowels)
                        matches.append((anchor_index, token_start, token_end))
                        previous_token_end = token_end
                        phonetic_match_found = True
                        break
            continue
        source_char_end = source_char_start + len(searchable_anchor)
        try:
            anchor_vowels = [
                token.vowel
                for token in text_to_vowel_tokens(
                    normalized_source[source_char_start:source_char_end]
                )
            ]
            if (
                len(anchor_vowels) < 3
                or (anchor.end_sec - anchor.start_sec) * VMD_FPS
                < len(anchor_vowels) * 2
            ):
                continue
            token_start = (
                0
                if source_char_start == 0
                else len(text_to_vowel_tokens(normalized_source[:source_char_start]))
            )
            token_end = len(
                text_to_vowel_tokens(normalized_source[:source_char_end])
            )
        except ValueError:
            continue

        if (
            token_start < previous_token_end
            or token_end <= token_start
            or token_end > len(source_token_vowels)
            or source_token_vowels[token_start:token_end] != anchor_vowels
        ):
            continue

        matches.append((anchor_index, token_start, token_end))
        search_cursor = source_char_end
        previous_token_end = token_end

    if not matches:
        return duration_allocation, "duration_weighted", []

    if phonetic_match_found and len(matches) == 1:
        anchor_index, token_start, token_end = matches[0]
        target_count = token_end - token_start
        prefix_count = sum(duration_allocation[:anchor_index])
        prefix_delta = token_start - prefix_count
        if (
            abs(prefix_delta) > 1
            or (anchors[anchor_index].end_sec - anchors[anchor_index].start_sec)
            * VMD_FPS < target_count * 2
        ):
            return duration_allocation, "duration_weighted", []

        allocation = list(duration_allocation)
        if prefix_delta > 0:
            candidate_indexes = [
                index
                for index in range(anchor_index - 1, -1, -1)
                if (anchors[index].end_sec - anchors[index].start_sec) * VMD_FPS
                >= (allocation[index] + prefix_delta) * 2
            ]
            if not candidate_indexes:
                return duration_allocation, "duration_weighted", []
            allocation[candidate_indexes[0]] += prefix_delta
        elif prefix_delta < 0:
            remaining = -prefix_delta
            for index in range(anchor_index - 1, -1, -1):
                moved = min(allocation[index], remaining)
                allocation[index] -= moved
                remaining -= moved
                if remaining == 0:
                    break
            if remaining:
                return duration_allocation, "duration_weighted", []

        allocation[anchor_index] = target_count
        trailing_target = len(tokens) - sum(allocation[: anchor_index + 1])
        trailing_current = sum(duration_allocation[anchor_index + 1 :])
        if trailing_target > trailing_current:
            return duration_allocation, "duration_weighted", []
        remaining = trailing_current - trailing_target
        for index in range(anchor_index + 1, len(anchors)):
            moved = min(allocation[index], remaining)
            allocation[index] -= moved
            remaining -= moved
            if remaining == 0:
                break
        if remaining or sum(allocation) != len(tokens):
            return duration_allocation, "duration_weighted", []
        phonetic_record = {
            "anchor_index": anchor_index,
            "token_start": token_start,
            "token_end": token_end,
            "phonetic_match": 1,
        }
        allocation, local_anchor_records = _apply_local_text_anchor_run(
            allocation=allocation,
            tokens=tokens,
            anchors=anchors,
            source_text=searchable_source,
            source_token_vowels=source_token_vowels,
            after_anchor_index=anchor_index,
        )
        return (
            allocation,
            "source_text_phonetic_anchor_match",
            [phonetic_record, *local_anchor_records],
        )

    allocation = [0] * len(anchors)
    match_records: list[dict[str, int]] = []
    previous_anchor_index = -1
    previous_token_end = 0
    for anchor_index, token_start, token_end in matches:
        unmatched_anchor_indexes = range(previous_anchor_index + 1, anchor_index)
        unmatched_token_count = token_start - previous_token_end
        if unmatched_token_count and not unmatched_anchor_indexes:
            return duration_allocation, "duration_weighted", []
        if unmatched_anchor_indexes:
            indexes = list(unmatched_anchor_indexes)
            regional_counts = _allocate_vowels_to_anchors(
                unmatched_token_count,
                [anchors[index] for index in indexes],
            )
            for index, count in zip(indexes, regional_counts):
                allocation[index] = count

        allocation[anchor_index] = token_end - token_start
        match_records.append(
            {
                "anchor_index": anchor_index,
                "token_start": token_start,
                "token_end": token_end,
            }
        )
        previous_anchor_index = anchor_index
        previous_token_end = token_end

    trailing_anchor_indexes = range(previous_anchor_index + 1, len(anchors))
    trailing_token_count = len(tokens) - previous_token_end
    if trailing_token_count and not trailing_anchor_indexes:
        return duration_allocation, "duration_weighted", []
    if trailing_anchor_indexes:
        indexes = list(trailing_anchor_indexes)
        regional_counts = _allocate_vowels_to_anchors(
            trailing_token_count,
            [anchors[index] for index in indexes],
        )
        for index, count in zip(indexes, regional_counts):
            allocation[index] = count

    if sum(allocation) != len(tokens):
        return duration_allocation, "duration_weighted", []
    return allocation, "source_text_anchor_matches", match_records


def _apply_local_text_anchor_run(
    *,
    allocation: list[int],
    tokens: Sequence[VowelToken],
    anchors: Sequence[SpeechTimingAnchor],
    source_text: str,
    source_token_vowels: Sequence[str],
    after_anchor_index: int,
) -> tuple[list[int], list[dict[str, int]]]:
    """Align a short kana boundary and its following exact word run locally."""
    for kana_anchor_index in range(after_anchor_index + 1, len(anchors)):
        kana_text = unicodedata.normalize(
            "NFKC", anchors[kana_anchor_index].text.strip()
        )
        previous_text = unicodedata.normalize(
            "NFKC", anchors[kana_anchor_index - 1].text.strip()
        )
        if (
            len(kana_text) != 1
            or not _is_kana_anchor_text(kana_text)
            or not any(
                0x3400 <= ord(char) <= 0x4DBF
                or 0x4E00 <= ord(char) <= 0x9FFF
                or 0xF900 <= ord(char) <= 0xFAFF
                for char in previous_text
            )
            or f"{previous_text}{kana_text}".casefold() not in source_text
        ):
            continue
        try:
            kana_vowels = [
                token.vowel for token in text_to_vowel_tokens(kana_text)
            ]
        except ValueError:
            continue
        if len(kana_vowels) != 1:
            continue

        expected_start = sum(allocation[:kana_anchor_index])
        candidate_starts = [
            token_start
            for token_start in range(max(0, expected_start - 1), expected_start + 1)
            if source_token_vowels[
                token_start : token_start + len(kana_vowels)
            ]
            == kana_vowels
        ]
        if len(candidate_starts) != 1:
            continue
        kana_token_start = candidate_starts[0]
        prefix_delta = kana_token_start - expected_start
        if abs(prefix_delta) > 1:
            continue
        if (
            (anchors[kana_anchor_index].end_sec - anchors[kana_anchor_index].start_sec)
            * VMD_FPS
            < len(kana_vowels) * 2
        ):
            continue

        adjusted = list(allocation)
        if prefix_delta < 0:
            remaining = -prefix_delta
            for index in range(kana_anchor_index - 1, -1, -1):
                moved = min(adjusted[index], remaining)
                adjusted[index] -= moved
                remaining -= moved
                if remaining == 0:
                    break
            if remaining:
                continue
        elif prefix_delta > 0:
            candidate_indexes = [
                index
                for index in range(kana_anchor_index - 1, -1, -1)
                if (anchors[index].end_sec - anchors[index].start_sec) * VMD_FPS
                >= (adjusted[index] + prefix_delta) * 2
            ]
            if not candidate_indexes:
                continue
            adjusted[candidate_indexes[0]] += prefix_delta
        adjusted[kana_anchor_index] = len(kana_vowels)
        run_start = kana_anchor_index + 1
        run_match: tuple[int, int, list[int]] | None = None
        max_run_length = min(7, len(anchors) - run_start)
        for run_length in range(max_run_length, 1, -1):
            run = anchors[run_start : run_start + run_length]
            run_texts = [
                unicodedata.normalize("NFKC", anchor.text.strip())
                for anchor in run
            ]
            if not all(_is_reliable_anchor_text(text) for text in run_texts):
                continue
            joined_text = "".join(run_texts)
            if source_text.count(joined_text.casefold()) != 1:
                continue
            try:
                per_anchor_vowels = [
                    [token.vowel for token in text_to_vowel_tokens(text)]
                    for text in run_texts
                ]
                run_vowels = [
                    token.vowel for token in text_to_vowel_tokens(joined_text)
                ]
            except ValueError:
                continue
            if (
                len(run_vowels) < 3
                or [vowel for values in per_anchor_vowels for vowel in values]
                != run_vowels
                or any(
                    (anchor.end_sec - anchor.start_sec) * VMD_FPS
                    < len(values) * 2
                    for anchor, values in zip(run, per_anchor_vowels)
                )
            ):
                continue
            expected_run_start = sum(adjusted[:run_start])
            candidate_run_starts = [
                token_start
                for token_start in range(
                    max(0, expected_run_start - 2),
                    min(
                        len(source_token_vowels) - len(run_vowels),
                        expected_run_start + 2,
                    )
                    + 1,
                )
                if source_token_vowels[
                    token_start : token_start + len(run_vowels)
                ]
                == run_vowels
            ]
            if (
                len(candidate_run_starts) != 1
                or candidate_run_starts[0] != expected_run_start
            ):
                continue
            run_match = (
                run_length,
                candidate_run_starts[0],
                [len(values) for values in per_anchor_vowels],
            )
            break

        if run_match is None:
            continue
        run_length, run_token_start, run_counts = run_match
        run_end = run_start + run_length - 1
        for index, count in zip(range(run_start, run_end + 1), run_counts):
            adjusted[index] = count
        run_token_end = run_token_start + sum(run_counts)
        trailing_anchor_indexes = list(range(run_end + 1, len(anchors)))
        trailing_token_count = len(tokens) - run_token_end
        if trailing_token_count and not trailing_anchor_indexes:
            continue
        if trailing_anchor_indexes:
            trailing_counts = _allocate_vowels_to_anchors(
                trailing_token_count,
                [anchors[index] for index in trailing_anchor_indexes],
            )
            for index, count in zip(trailing_anchor_indexes, trailing_counts):
                adjusted[index] = count
        if sum(adjusted) != len(tokens):
            continue

        return adjusted, [
            {
                "anchor_index": kana_anchor_index,
                "token_start": kana_token_start,
                "token_end": kana_token_start + len(kana_vowels),
                "kana_anchor_peak": 1,
            },
            {
                "anchor_start_index": run_start,
                "anchor_end_index": run_end,
                "token_start": run_token_start,
                "token_end": run_token_end,
                "local_anchor_run": 1,
            },
        ]
    return allocation, []


def _is_reliable_anchor_text(text: str) -> bool:
    if not text:
        return False
    if len(text) >= 2:
        return True
    codepoint = ord(text[0])
    return (
        0x3040 <= codepoint <= 0x309F
        or 0x30A0 <= codepoint <= 0x30FF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _is_kana_anchor_text(text: str) -> bool:
    return bool(text) and all(
        0x3040 <= ord(char) <= 0x309F
        or 0x30A0 <= ord(char) <= 0x30FF
        or char == "ー"
        for char in text
    )


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
    debug_trace: Any = None,
    collect_transition_acoustics: bool = False,
) -> _ObservedTimelineBuildResult:
    if not timeline:
        snapshot = None
        if collect_transition_acoustics:
            try:
                source_before = sha256_file(wav_path)
            except OSError:
                source_before = None
            try:
                source_after = sha256_file(wav_path)
            except OSError:
                source_after = None
            snapshot = build_transition_acoustic_snapshot(
                rms_series=None,
                source_sha256_before=source_before,
                source_sha256_after=source_after,
                duration_sec=None,
                reason="empty_timeline",
            )
        return _ObservedTimelineBuildResult(
            timeline=[],
            observations=[],
            transition_acoustic_snapshot=snapshot,
        )

    clamped_upper_limit = max(0.0, upper_limit)
    initial_timeline = _repair_resolver_same_morph_boundaries(
        timeline,
        debug_trace=debug_trace,
        debug_call_site="pre_rms",
    )
    _debug_record(debug_trace, "record_timeline", "timeline_pre_rms", initial_timeline)

    source_sha256_before = None
    if collect_transition_acoustics:
        try:
            source_sha256_before = sha256_file(wav_path)
        except OSError:
            source_sha256_before = None

    try:
        rms_series = load_rms_series(str(wav_path), stereo_mode="average")
    except (ValueError, OSError, EOFError):
        snapshot = None
        if collect_transition_acoustics:
            try:
                source_sha256_after = sha256_file(wav_path)
            except OSError:
                source_sha256_after = None
            snapshot = build_transition_acoustic_snapshot(
                rms_series=None,
                source_sha256_before=source_sha256_before,
                source_sha256_after=source_sha256_after,
                duration_sec=None,
                reason="rms_unavailable",
            )
        _debug_record(
            debug_trace,
            "record_stage",
            "rms_load",
            status="skipped",
            reason_code="rms_unavailable",
        )
        timeline_with_peak_values = _apply_peak_values_to_timeline(
            timeline=initial_timeline,
            rms_series=None,
            speech_start_sec=speech_start_sec,
            speech_end_sec=speech_end_sec,
            upper_limit=clamped_upper_limit,
            fallback_reason="rms_unavailable",
            debug_trace=debug_trace,
        )
        _debug_record(
            debug_trace,
            "record_timeline",
            "timeline_post_rms_raw",
            timeline_with_peak_values,
            status="skipped",
            reason_code="rms_unavailable",
        )
        _debug_record(
            debug_trace,
            "record_stage",
            "rms_refine",
            status="skipped",
            reason_code="rms_unavailable",
        )
        for skipped_stage in (
            "post_rms.long_boundary",
            "post_rms.interleaved_boundary",
        ):
            _debug_record(
                debug_trace,
                "record_stage",
                skipped_stage,
                status="skipped",
                reason_code="rms_unavailable",
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
        _debug_record(
            debug_trace,
            "record_observations",
            observations,
            fallback_reason="rms_unavailable",
        )
        return _ObservedTimelineBuildResult(
            timeline=timeline_with_peak_values,
            observations=observations,
            transition_acoustic_snapshot=snapshot,
        )

    snapshot = None
    if collect_transition_acoustics:
        try:
            source_sha256_after = sha256_file(wav_path)
        except OSError:
            source_sha256_after = None
        snapshot = build_transition_acoustic_snapshot(
            rms_series=rms_series,
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            duration_sec=rms_series.duration_sec,
        )

    rms_debug_payload = _debug_rms_payload(
        rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
    )
    _debug_record(
        debug_trace,
        "record_stage",
        "rms_load",
        payload={
            "sample_count": len(rms_series.times_sec),
            "sample_rate_hz": rms_series.sample_rate_hz,
            "window_size_samples": rms_series.window_size_samples,
            "hop_size_samples": rms_series.hop_size_samples,
            "window_sec": (
                rms_series.window_size_samples / rms_series.sample_rate_hz
                if rms_series.sample_rate_hz
                else None
            ),
            "hop_sec": (
                rms_series.hop_size_samples / rms_series.sample_rate_hz
                if rms_series.sample_rate_hz
                else None
            ),
            "times_sec": rms_series.times_sec,
            "values": rms_series.values,
            **rms_debug_payload,
        },
    )
    refined_before_post = _refine_intervals_by_rms_series(
        timeline=initial_timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
    )
    _debug_record(debug_trace, "record_timeline", "rms_refine", refined_before_post)
    refined_timeline = _repair_resolver_same_morph_boundaries(
        refined_before_post,
        debug_trace=debug_trace,
        debug_call_site="post_rms",
    )
    _debug_record(debug_trace, "record_timeline", "timeline_post_rms_raw", refined_timeline)
    silence_intervals = (
        rms_debug_payload.get("silence_intervals", [])
        if isinstance(rms_debug_payload.get("silence_intervals", []), list)
        else []
    )
    source_silence_intervals = tuple(
        (
            float(item["start_sec"]),
            float(item["end_sec"]),
            str(item.get("classification", "unknown")),
            str(item.get("coverage_status", "unobserved")),
            str(item.get("provenance_status", "unavailable")),
        )
        for item in silence_intervals
        if isinstance(item, dict)
        and isinstance(item.get("start_sec"), (int, float))
        and isinstance(item.get("end_sec"), (int, float))
        and math.isfinite(float(item["start_sec"]))
        and math.isfinite(float(item["end_sec"]))
        and float(item["end_sec"]) > float(item["start_sec"])
    )
    timeline_with_peak_values = _apply_peak_values_to_timeline(
        timeline=refined_timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=clamped_upper_limit,
        silence_intervals=silence_intervals,
        debug_trace=debug_trace,
    )
    _debug_record(
        debug_trace,
        "record_timeline",
        "peak_evaluation",
        timeline_with_peak_values,
    )
    observations = _build_peak_value_observations(
        timeline=timeline_with_peak_values,
        initial_timeline=initial_timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=clamped_upper_limit,
        silence_intervals=silence_intervals,
    )
    _debug_record(debug_trace, "record_observations", observations)
    return _ObservedTimelineBuildResult(
        timeline=timeline_with_peak_values,
        observations=observations,
        transition_acoustic_snapshot=snapshot,
        source_silence_intervals=source_silence_intervals,
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
                    **_timeline_metadata_kwargs(point),
                )
            )
            continue

        threshold = max(local_peak * _RMS_INTERVAL_THRESHOLD_RATIO, _RMS_ABS_MIN_THRESHOLD)
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
                **_timeline_metadata_kwargs(point),
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
    silence_intervals: Sequence[dict] | None = None,
    debug_trace: Any = None,
) -> list[VowelTimelinePoint]:
    evaluations = _build_peak_value_evaluations(
        timeline=timeline,
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        upper_limit=upper_limit,
        fallback_reason=fallback_reason,
        silence_intervals=silence_intervals,
    )
    updated: list[VowelTimelinePoint] = []
    assignment_records: list[dict[str, Any]] = []
    for index, (point, evaluation) in enumerate(zip(timeline, evaluations)):
        selection = _select_peak_sample_for_event(
            times_sec=() if rms_series is None else rms_series.times_sec,
            values=() if rms_series is None else rms_series.values,
            source_time_sec=point.time_sec,
            peak_window_start_sec=evaluation.peak_window_start_sec,
            peak_window_end_sec=evaluation.peak_window_end_sec,
            interval_start_sec=evaluation.interval_start_sec,
            interval_end_sec=evaluation.interval_end_sec,
            silence_intervals=silence_intervals,
        )
        peak_time_sec = point.time_sec
        assignment_reason = selection.reason
        if (
            evaluation.peak_value > 0.0
            and selection.source_frame_blocked
            and selection.frame_no is not None
        ):
            previous_frame = (
                None if index == 0 else _seconds_to_frame(timeline[index - 1].time_sec)
            )
            next_frame = (
                None
                if index + 1 >= len(timeline)
                else _seconds_to_frame(timeline[index + 1].time_sec)
            )
            if (
                (previous_frame is None or selection.frame_no >= previous_frame)
                and (next_frame is None or selection.frame_no <= next_frame)
            ):
                peak_time_sec = selection.frame_no / VMD_FPS
                assignment_reason = "rms_peak_frame"
            else:
                assignment_reason = "event_order_conflict"
        elif evaluation.peak_value <= 0.0:
            assignment_reason = evaluation.reason or "peak_value_not_positive"
        elif selection.frame_no is not None:
            assignment_reason = "source_frame_not_in_silence_core"
        updated.append(
            _with_peak_value(
                point=point,
                peak_value=evaluation.peak_value,
                time_sec=peak_time_sec,
            )
        )
        assignment_records.append(
            {
                "event_index": index,
                "vowel": point.vowel,
                "source_time_sec": point.time_sec,
                "peak_sample_time_sec": selection.sample_time_sec,
                "peak_frame": selection.frame_no,
                "assigned_time_sec": peak_time_sec,
                "reason": assignment_reason,
            }
        )
    _debug_record(
        debug_trace,
        "record_stage",
        "peak_time_assignment",
        payload={"events": assignment_records},
    )
    return updated


def _build_peak_value_evaluations(
    *,
    timeline: Sequence[VowelTimelinePoint],
    rms_series: RmsSeriesData | None,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
    fallback_reason: str | None = None,
    silence_intervals: Sequence[dict] | None = None,
    source_timeline: Sequence[VowelTimelinePoint] | None = None,
) -> list[PeakValueEvaluation]:
    if not timeline:
        return []
    if source_timeline is not None and len(source_timeline) != len(timeline):
        raise ValueError("source_timeline must have the same length as timeline.")

    clamped_upper_limit = max(0.0, upper_limit)
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
        selection = _select_peak_sample_for_event(
            times_sec=rms_series.times_sec,
            values=rms_series.values,
            source_time_sec=(
                point.time_sec
                if source_timeline is None
                else source_timeline[index].time_sec
            ),
            peak_window_start_sec=peak_window_start_sec,
            peak_window_end_sec=peak_window_end_sec,
            interval_start_sec=interval_start_sec,
            interval_end_sec=interval_end_sec,
            silence_intervals=silence_intervals,
        )
        window_samples = _rms_samples_in_window(
            times_sec=rms_series.times_sec,
            values=rms_series.values,
            start_sec=peak_window_start_sec,
            end_sec=peak_window_end_sec,
        )
        if selection.source_frame_blocked and selection.frame_no is not None:
            local_peak = selection.sample_value
            zero_reason = _classify_peak_zero_reason(
                local_peak=local_peak,
            )
        elif selection.source_frame_blocked and selection.reason == "silence_core_only":
            local_peak = selection.sample_value
            zero_reason = "silence_core_precedence"
        else:
            local_peak = max(window_samples) if window_samples else None
            zero_reason = _classify_peak_zero_reason(
                local_peak=local_peak,
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


def _merge_frame_ranges(frames: Sequence[int]) -> tuple[tuple[int, int], ...]:
    ordered = sorted(set(int(frame) for frame in frames))
    if not ordered:
        return ()
    ranges: list[tuple[int, int]] = []
    start = ordered[0]
    end = start + 1
    for frame in ordered[1:]:
        if frame == end:
            end += 1
            continue
        ranges.append((start, end))
        start = frame
        end = frame + 1
    ranges.append((start, end))
    return tuple(ranges)


def _silence_frame_ranges_for_span(
    silence_intervals: Sequence[dict] | None,
    *,
    span_start_frame: int,
    span_end_frame: int,
    frame_rate: int = 30,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    if not silence_intervals or span_end_frame <= span_start_frame:
        return (), ()

    core_frames: list[int] = []
    fringe_frames: list[int] = []
    for interval in silence_intervals:
        if not isinstance(interval, dict):
            continue
        start_sec = interval.get("start_sec")
        end_sec = interval.get("end_sec")
        if not isinstance(start_sec, (int, float)) or not isinstance(end_sec, (int, float)):
            continue
        if not math.isfinite(float(start_sec)) or not math.isfinite(float(end_sec)):
            continue
        if float(end_sec) <= float(start_sec):
            continue
        first_frame = max(span_start_frame, math.floor(float(start_sec) * frame_rate) - 1)
        last_frame = min(span_end_frame, math.ceil(float(end_sec) * frame_rate) + 1)
        for frame_no in range(first_frame, last_frame):
            cell_start = frame_no / frame_rate
            cell_end = (frame_no + 1) / frame_rate
            overlap_start = max(cell_start, float(start_sec))
            overlap_end = min(cell_end, float(end_sec))
            if overlap_end <= overlap_start:
                continue
            if float(start_sec) <= cell_start and cell_end <= float(end_sec):
                core_frames.append(frame_no)
            else:
                fringe_frames.append(frame_no)
    return _merge_frame_ranges(core_frames), _merge_frame_ranges(fringe_frames)


def _timeline_long_vowel_roles(
    timeline: Sequence[VowelTimelinePoint],
) -> tuple[str | None, ...]:
    roles: list[str | None] = [None] * len(timeline)
    continuations_by_source: dict[int, list[int]] = {}
    for index, point in enumerate(timeline):
        if (
            point.is_long_vowel_continuation
            and point.long_vowel_source_token_index is not None
        ):
            continuations_by_source.setdefault(
                point.long_vowel_source_token_index,
                [],
            ).append(index)
    for source_index, continuation_indices in continuations_by_source.items():
        if 0 <= source_index < len(roles):
            roles[source_index] = "long_source"
        for continuation_index in continuation_indices[:-1]:
            roles[continuation_index] = "intermediate_continuation"
        if continuation_indices:
            roles[continuation_indices[-1]] = "terminal_continuation"
    return tuple(roles)


def _event_frame_range(
    start_sec: float,
    end_sec: float,
    *,
    frame_rate: int = 30,
) -> tuple[int, int]:
    start_frame = max(0, math.floor(float(start_sec) * frame_rate))
    end_frame = max(start_frame + 1, math.ceil(float(end_sec) * frame_rate))
    return start_frame, end_frame


def _observation_boundary_fields(
    start_sec: float,
    end_sec: float,
    peak_value: float,
    *,
    frame_rate: int = 30,
) -> tuple[bool, int | None, str | None]:
    if not all(math.isfinite(float(value)) for value in (start_sec, end_sec, peak_value)):
        return False, None, None
    start_frame = int(round(float(start_sec) * frame_rate))
    end_frame = int(round(float(end_sec) * frame_rate))
    if start_frame != end_frame or peak_value > _MORPH_FRAME_OPEN_EPSILON:
        return False, None, None
    return True, start_frame, "end_zero"


def _build_peak_value_observations(
    *,
    timeline: Sequence[VowelTimelinePoint],
    rms_series: RmsSeriesData | None,
    speech_start_sec: float,
    speech_end_sec: float,
    upper_limit: float,
    fallback_reason: str | None = None,
    initial_timeline: Sequence[VowelTimelinePoint] | None = None,
    silence_intervals: Sequence[dict] | None = None,
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
        silence_intervals=silence_intervals,
        source_timeline=initial_timeline,
    )
    global_peak = _observation_global_peak(
        rms_series=rms_series,
        speech_start_sec=speech_start_sec,
        speech_end_sec=speech_end_sec,
        fallback_reason=fallback_reason,
    )

    long_vowel_roles = _timeline_long_vowel_roles(timeline)
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
        boundary_only, boundary_frame, boundary_point_kind = _observation_boundary_fields(
            evaluation.interval_start_sec,
            evaluation.interval_end_sec,
            evaluation.peak_value,
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
                long_vowel_role=long_vowel_roles[index],
                boundary_only=boundary_only,
                boundary_frame=boundary_frame,
                boundary_point_kind=boundary_point_kind,
            )
        )
    return _annotate_micro_gap_bridge_candidates(
        observations,
        silence_intervals=silence_intervals,
    )


def _annotate_micro_gap_bridge_candidates(
    observations: Sequence[PeakValueObservation],
    *,
    silence_intervals: Sequence[dict] | None = None,
) -> list[PeakValueObservation]:
    # MS11-11:
    # ここでは shape を決めず、writer / preview が解釈する candidate family と
    # span 境界だけを observation 契約へ固定する。
    if not observations:
        return []

    span_candidates = _build_bridgeable_zero_run_span_candidates(observations)
    same_vowel_burst_candidates = _build_same_vowel_burst_span_candidates(observations)
    annotated: list[PeakValueObservation] = []
    for index, observation in enumerate(observations):
        contract = _resolve_observation_candidate_contract(
            observations=observations,
            index=index,
            span_candidates=span_candidates,
            same_vowel_burst_candidates=same_vowel_burst_candidates,
        )
        full_span_start_frame: int | None = None
        full_span_end_frame: int | None = None
        silence_core_frame_ranges: tuple[tuple[int, int], ...] = ()
        boundary_fringe_frame_ranges: tuple[tuple[int, int], ...] = ()
        silence_core_overlap = False
        coverage_status = "complete" if silence_intervals is not None else "unobserved"
        provenance_status = "unavailable"
        bridge_rejection_reason_code: str | None = None
        base_event_silence_core_overlap = False
        positive_core_frame_ranges: tuple[tuple[int, int], ...] = ()
        base_event_rejection_reason_code: str | None = None
        event_start_frame, event_end_frame = _event_frame_range(
            observation.refined_interval_start_sec,
            observation.refined_interval_end_sec,
        )
        (
            base_core_frame_ranges,
            _base_boundary_fringe_frame_ranges,
        ) = _silence_frame_ranges_for_span(
            silence_intervals,
            span_start_frame=event_start_frame,
            span_end_frame=event_end_frame,
        )
        base_event_silence_core_overlap = bool(base_core_frame_ranges)
        peak_frame = _seconds_to_frame(observation.time_sec)
        if (
            observation.peak_value > _MORPH_FRAME_OPEN_EPSILON
            and any(
                start <= peak_frame < end
                for start, end in base_core_frame_ranges
            )
        ):
            positive_core_frame_ranges = ((peak_frame, peak_frame + 1),)
            base_event_rejection_reason_code = "base_event_overlaps_silence_core"
        previous_index = contract.previous_non_zero_event_index
        next_index = contract.next_non_zero_event_index
        if previous_index is not None and next_index is not None:
            previous_observation = observations[previous_index]
            next_observation = observations[next_index]
            full_span_start_frame = _seconds_to_frame(previous_observation.refined_interval_end_sec)
            full_span_end_frame = _seconds_to_frame(next_observation.refined_interval_start_sec)
            provenance_status = "complete"
            (
                silence_core_frame_ranges,
                boundary_fringe_frame_ranges,
            ) = _silence_frame_ranges_for_span(
                silence_intervals,
                span_start_frame=full_span_start_frame,
                span_end_frame=full_span_end_frame,
            )
            silence_core_overlap = bool(silence_core_frame_ranges)
            is_cross_vowel = previous_observation.vowel != next_observation.vowel
            if is_cross_vowel and silence_core_overlap:
                bridge_rejection_reason_code = "cross_vowel_handoff_crosses_silence_core"
            elif (
                is_cross_vowel
                and not contract.is_bridgeable_cross_vowel_candidate
                and not contract.is_cross_vowel_zero_run_floor_candidate
                and full_span_end_frame - full_span_start_frame
                > _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES
            ):
                bridge_rejection_reason_code = "cross_vowel_handoff_exceeds_full_span_limit"
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
                is_bridgeable_same_vowel_micro_gap_candidate=contract.is_bridgeable_same_vowel_candidate,
                is_same_vowel_burst_candidate=contract.is_same_vowel_burst_candidate,
                is_bridgeable_cross_vowel_transition_candidate=contract.is_bridgeable_cross_vowel_candidate,
                is_cross_vowel_zero_run_continuity_floor_candidate=contract.is_cross_vowel_zero_run_floor_candidate,
                is_bridgeable_micro_gap_candidate=contract.is_bridgeable_same_vowel_candidate,
                bridge_candidate_reason=contract.resolved_bridge_candidate_reason,
                previous_non_zero_event_index=contract.previous_non_zero_event_index,
                next_non_zero_event_index=contract.next_non_zero_event_index,
                span_start_index=contract.span_start_index,
                span_end_index=contract.span_end_index,
                full_span_start_frame=full_span_start_frame,
                full_span_end_frame=full_span_end_frame,
                silence_core_frame_ranges=silence_core_frame_ranges,
                boundary_fringe_frame_ranges=boundary_fringe_frame_ranges,
                silence_core_overlap=silence_core_overlap,
                coverage_status=coverage_status,
                provenance_status=provenance_status,
                bridge_rejection_reason_code=bridge_rejection_reason_code,
                base_event_silence_core_overlap=base_event_silence_core_overlap,
                positive_core_frame_ranges=positive_core_frame_ranges,
                long_vowel_role=observation.long_vowel_role,
                manual_adjustment_applied=observation.manual_adjustment_applied,
                base_event_rejection_reason_code=base_event_rejection_reason_code,
                boundary_only=observation.boundary_only,
                boundary_frame=observation.boundary_frame,
                boundary_point_kind=observation.boundary_point_kind,
            )
        )
    return annotated


def reproject_peak_values_for_upper_limit(
    timing_plan: VowelTimingPlan,
    upper_limit: float,
) -> VowelTimingPlan:
    """Re-evaluate stored peak evidence without rerunning text or audio analysis."""
    if not isinstance(timing_plan, VowelTimingPlan):
        raise TypeError("timing_plan must be a VowelTimingPlan")
    if isinstance(upper_limit, bool) or not isinstance(upper_limit, (int, float)):
        raise ValueError("upper_limit must be a finite number between 0 and 10")
    normalized_limit = float(upper_limit)
    if not math.isfinite(normalized_limit) or not 0.0 <= normalized_limit <= 10.0:
        raise ValueError("upper_limit must be a finite number between 0 and 10")
    observations = timing_plan.observations
    if observations is None or len(observations) != len(timing_plan.timeline):
        raise ValueError("upper-independent peak observations are unavailable")

    projected_timeline: list[VowelTimelinePoint] = []
    projected_observations: list[PeakValueObservation] = []
    for index, (point, observation) in enumerate(
        zip(timing_plan.timeline, observations)
    ):
        if observation.event_index != index or observation.vowel != point.vowel:
            raise ValueError("peak observations do not match source events")
        evaluation = observation.evaluation
        reason: str | None
        if observation.fallback_reason == "rms_unavailable":
            peak_value = round(
                normalized_limit * _RMS_UNAVAILABLE_FALLBACK_RATIO,
                4,
            )
            reason = "rms_unavailable"
        else:
            local_peak = evaluation.local_peak
            global_peak = observation.global_peak
            if global_peak is None or not math.isfinite(float(global_peak)):
                raise ValueError(
                    f"global peak evidence is unavailable for source event {index}"
                )
            normalized_global_peak = float(global_peak)
            if normalized_global_peak < 0.0:
                raise ValueError(
                    f"global peak evidence is invalid for source event {index}"
                )
            if normalized_global_peak == 0.0:
                reason = "global_peak_zero"
                peak_value = 0.0
            else:
                reason = _classify_peak_zero_reason(
                    local_peak=local_peak,
                )
                if reason is not None:
                    peak_value = 0.0
                else:
                    normalized_peak = float(local_peak) / normalized_global_peak
                    peak_value = max(
                        0.0,
                        min(
                            normalized_limit,
                            round(normalized_limit * normalized_peak, 4),
                        ),
                    )
        updated_evaluation = replace(
            evaluation,
            peak_value=peak_value,
            reason=reason,
        )
        updated_observation = replace(
            observation,
            peak_value=peak_value,
            reason=reason,
            evaluation=updated_evaluation,
        )
        projected_observations.append(updated_observation)
        projected_timeline.append(
            replace(point, value=peak_value, peak_value=peak_value)
        )

    silence_intervals = [
        {
            "start_sec": start_sec,
            "end_sec": end_sec,
            "classification": classification,
            "coverage_status": coverage_status,
            "provenance_status": provenance_status,
        }
        for (
            start_sec,
            end_sec,
            classification,
            coverage_status,
            provenance_status,
        ) in timing_plan.source_silence_intervals
    ]
    annotated = _annotate_micro_gap_bridge_candidates(
        projected_observations,
        silence_intervals=silence_intervals,
    )
    return replace(
        timing_plan,
        timeline=projected_timeline,
        observations=annotated,
    )


def _resolve_observation_candidate_contract(
    *,
    observations: Sequence[PeakValueObservation],
    index: int,
    span_candidates: dict[int, str],
    same_vowel_burst_candidates: dict[int, tuple[int, int]],
) -> _ObservationCandidateContract:
    previous_non_zero_event_index = _previous_non_zero_event_index(observations, index)
    next_non_zero_event_index = _next_non_zero_event_index(observations, index)
    observation = observations[index]
    bridge_candidate_reason = _resolve_bridge_candidate_reason(observation)
    span_candidate = span_candidates.get(index)
    same_vowel_burst_span = same_vowel_burst_candidates.get(index)
    is_bridgeable_same_vowel_candidate = span_candidate == "same_vowel"
    is_same_vowel_burst_candidate = same_vowel_burst_span is not None
    is_bridgeable_cross_vowel_candidate = span_candidate == "cross_vowel_transition"
    is_cross_vowel_zero_run_floor_candidate = span_candidate == "cross_vowel_floor"
    has_cross_vowel_context = (
        previous_non_zero_event_index is not None
        and next_non_zero_event_index is not None
        and observations[previous_non_zero_event_index].vowel
        != observations[next_non_zero_event_index].vowel
        and bridge_candidate_reason is not None
    )
    if span_candidate is not None or has_cross_vowel_context:
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
    elif has_cross_vowel_context:
        resolved_bridge_candidate_reason = bridge_candidate_reason
    else:
        resolved_bridge_candidate_reason = None
    return _ObservationCandidateContract(
        previous_non_zero_event_index=previous_non_zero_event_index,
        next_non_zero_event_index=next_non_zero_event_index,
        span_start_index=span_start_index,
        span_end_index=span_end_index,
        is_bridgeable_same_vowel_candidate=is_bridgeable_same_vowel_candidate,
        is_same_vowel_burst_candidate=is_same_vowel_burst_candidate,
        is_bridgeable_cross_vowel_candidate=is_bridgeable_cross_vowel_candidate,
        is_cross_vowel_zero_run_floor_candidate=is_cross_vowel_zero_run_floor_candidate,
        resolved_bridge_candidate_reason=resolved_bridge_candidate_reason,
    )


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
    full_span_frames = next_start_frame - previous_end_frame
    if full_span_frames < 0:
        return None
    cross_vowel_max_span_frames = (
        _CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES
        if span_count == 1
        else _CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES
    )
    if full_span_frames > cross_vowel_max_span_frames:
        if _is_cross_vowel_right_gap_residual_transition_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
            full_span_frames=full_span_frames,
        ):
            return "cross_vowel_transition"
        if _is_cross_vowel_floor_residual_span(
            observations=observations,
            span_start_index=span_start_index,
            span_end_index=span_end_index,
            previous_non_zero_event_index=previous_non_zero_event_index,
            next_non_zero_event_index=next_non_zero_event_index,
            full_span_frames=full_span_frames,
        ):
            return "cross_vowel_floor"
        return None
    representative_start_frame, representative_end_frame = _resolve_cross_vowel_candidate_span_frames(
        observations=observations,
        span_start_index=span_start_index,
        span_end_index=span_end_index,
        previous_non_zero_event_index=previous_non_zero_event_index,
        next_non_zero_event_index=next_non_zero_event_index,
    )
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
        return None
    if span_count == 1:
        return "cross_vowel_transition"
    return "cross_vowel_floor"


def _resolve_bridge_candidate_reason(
    observation: PeakValueObservation,
) -> str | None:
    if observation.peak_value > 0.0:
        return None
    if observation.reason == "no_peak_in_window":
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
    full_span_frames: int,
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
    representative_start_frame, representative_end_frame = _resolve_cross_vowel_candidate_span_frames(
        observations=observations,
        span_start_index=span_start_index,
        span_end_index=span_end_index,
        previous_non_zero_event_index=previous_non_zero_event_index,
        next_non_zero_event_index=next_non_zero_event_index,
    )
    right_gap_frames = next_start_frame - representative_end_frame

    if full_span_frames > _CROSS_VOWEL_RIGHT_GAP_RESIDUAL_MAX_SPAN_FRAMES:
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
    full_span_frames: int,
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
    representative_start_frame, representative_end_frame = _resolve_cross_vowel_candidate_span_frames(
        observations=observations,
        span_start_index=span_start_index,
        span_end_index=span_end_index,
        previous_non_zero_event_index=previous_non_zero_event_index,
        next_non_zero_event_index=next_non_zero_event_index,
    )
    right_gap_refined_frames = next_start_frame - representative_end_frame
    right_gap_initial_frames = next_initial_start_frame - representative_end_frame

    if full_span_frames <= _CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES:
        return False
    if full_span_frames > _CROSS_VOWEL_FLOOR_RESIDUAL_MAX_SPAN_FRAMES:
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


def _with_peak_value(
    *,
    point: VowelTimelinePoint,
    peak_value: float,
    time_sec: float | None = None,
) -> VowelTimelinePoint:
    return VowelTimelinePoint(
        time_sec=point.time_sec if time_sec is None else time_sec,
        vowel=point.vowel,
        value=peak_value,
        peak_value=peak_value,
        duration_sec=point.duration_sec,
        start_sec=point.start_sec,
        end_sec=point.end_sec,
        **_timeline_metadata_kwargs(point),
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


def _select_peak_sample_for_event(
    *,
    times_sec: Sequence[float],
    values: Sequence[float],
    source_time_sec: float,
    peak_window_start_sec: float,
    peak_window_end_sec: float,
    interval_start_sec: float,
    interval_end_sec: float,
    silence_intervals: Sequence[dict] | None,
) -> _PeakSampleSelection:
    window_pairs = _rms_sample_pairs_in_window(
        times_sec=times_sec,
        values=values,
        start_sec=peak_window_start_sec,
        end_sec=peak_window_end_sec,
    )
    if not window_pairs:
        return _PeakSampleSelection(None, None, None, "no_sample")

    event_pairs = [
        pair
        for pair in window_pairs
        if interval_start_sec <= pair[0] <= interval_end_sec
    ]
    if not event_pairs:
        sample_time_sec, sample_value = max(
            window_pairs,
            key=lambda pair: (pair[1], -pair[0]),
        )
        return _PeakSampleSelection(
            sample_time_sec,
            sample_value,
            None,
            "window_halo",
        )

    span_start_frame = _seconds_to_frame(interval_start_sec)
    span_end_frame = _seconds_to_frame(interval_end_sec)
    if span_end_frame <= span_start_frame:
        span_end_frame = span_start_frame + 1
    silence_core_ranges, _ = _silence_frame_ranges_for_span(
        silence_intervals,
        span_start_frame=span_start_frame,
        span_end_frame=span_end_frame,
    )
    # Match the frame quantization used when VMD keys are written.
    source_frame = _seconds_to_frame(source_time_sec)
    source_frame_blocked = any(
        start_frame <= source_frame < end_frame
        for start_frame, end_frame in silence_core_ranges
    )

    eligible: list[tuple[float, float, int]] = []
    protected_event_samples: list[tuple[float, float]] = []
    for sample_time_sec, sample_value in event_pairs:
        # RMS samples are grouped into 30 fps frame bins. Use the bin number
        # here, then express the selected center as an exact frame time below.
        frame_no = math.floor(sample_time_sec * VMD_FPS)
        frame_time_sec = frame_no / VMD_FPS
        if not interval_start_sec <= frame_time_sec <= interval_end_sec:
            continue
        in_core_or_boundary = any(
            start_frame <= frame_no < end_frame
            for start_frame, end_frame in silence_core_ranges
        )
        if in_core_or_boundary:
            protected_event_samples.append((sample_time_sec, sample_value))
            continue
        eligible.append((sample_time_sec, sample_value, frame_no))

    if eligible:
        sample_time_sec, sample_value, frame_no = max(
            eligible,
            key=lambda sample: (sample[1], -sample[0]),
        )
        return _PeakSampleSelection(
            sample_time_sec,
            sample_value,
            frame_no,
            "event_peak",
            source_frame_blocked,
        )

    if protected_event_samples and len(protected_event_samples) == len(event_pairs):
        sample_time_sec, sample_value = max(
            protected_event_samples,
            key=lambda pair: (pair[1], -pair[0]),
        )
        return _PeakSampleSelection(
            sample_time_sec,
            sample_value,
            None,
            "silence_core_only",
            source_frame_blocked,
        )

    sample_time_sec, sample_value = max(
        event_pairs,
        key=lambda pair: (pair[1], -pair[0]),
    )
    return _PeakSampleSelection(
        sample_time_sec,
        sample_value,
        None,
        "frame_outside_interval",
        source_frame_blocked,
    )


def _classify_peak_zero_reason(
    *,
    local_peak: float | None,
) -> str | None:
    if local_peak is None:
        return "no_peak_in_window"
    if local_peak < _RMS_ABS_MIN_THRESHOLD:
        return "below_abs_threshold"
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
            **_timeline_metadata_kwargs(timeline[0]),
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
                    **_timeline_metadata_kwargs(prev),
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
                **_timeline_metadata_kwargs(point),
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
            **_timeline_metadata_kwargs(point),
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
