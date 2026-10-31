"""Immutable, source-bound acoustic evidence for MS32 transitions."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.core.audio_processing import (
    RMS_HOP_MS,
    RMS_SMOOTHING_FRAMES,
    RMS_WINDOW_MS,
    RmsSeriesData,
)

TRANSITION_ACOUSTIC_SCHEMA = "transition-acoustic-snapshot/v1"
TRANSITION_ACOUSTIC_DIAGNOSTIC_THRESHOLD_RMS = 0.01
_SNAPSHOT_FIELDS = frozenset(
    {
        "schema_id",
        "state",
        "reason",
        "analysis_wav_sha256",
        "source_sha256_before",
        "source_sha256_after",
        "duration_sec",
        "sample_rate_hz",
        "channel_count",
        "window_size_samples",
        "hop_size_samples",
        "rms_window_ms",
        "rms_hop_ms",
        "smoothing_frames",
        "stereo_mode",
        "diagnostic_threshold_rms",
        "times_sec",
        "values",
        "coverage_intervals_sec",
        "content_digest",
    }
)


class TransitionAcousticError(ValueError):
    """Raised when an acoustic snapshot violates its strict contract."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite_float(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TransitionAcousticError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise TransitionAcousticError(f"{field} must be a finite number")
    return result


def _optional_nonnegative_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TransitionAcousticError(f"{field} must be a non-negative integer or null")
    return value


def _canonical_payload(snapshot: "TransitionAcousticSnapshot") -> dict[str, Any]:
    return {
        "schema_id": snapshot.schema_id,
        "state": snapshot.state,
        "reason": snapshot.reason,
        "analysis_wav_sha256": snapshot.analysis_wav_sha256,
        "source_sha256_before": snapshot.source_sha256_before,
        "source_sha256_after": snapshot.source_sha256_after,
        "duration_sec": snapshot.duration_sec,
        "sample_rate_hz": snapshot.sample_rate_hz,
        "channel_count": snapshot.channel_count,
        "window_size_samples": snapshot.window_size_samples,
        "hop_size_samples": snapshot.hop_size_samples,
        "rms_window_ms": snapshot.rms_window_ms,
        "rms_hop_ms": snapshot.rms_hop_ms,
        "smoothing_frames": snapshot.smoothing_frames,
        "stereo_mode": snapshot.stereo_mode,
        "diagnostic_threshold_rms": snapshot.diagnostic_threshold_rms,
        "times_sec": list(snapshot.times_sec),
        "values": list(snapshot.values),
        "coverage_intervals_sec": [list(interval) for interval in snapshot.coverage_intervals_sec],
    }


def _digest_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class TransitionAcousticSnapshot:
    state: str
    reason: str | None
    analysis_wav_sha256: str | None
    source_sha256_before: str | None
    source_sha256_after: str | None
    duration_sec: float | None
    sample_rate_hz: int | None
    channel_count: int | None
    window_size_samples: int | None
    hop_size_samples: int | None
    rms_window_ms: float
    rms_hop_ms: float
    smoothing_frames: int
    stereo_mode: str
    diagnostic_threshold_rms: float
    times_sec: tuple[float, ...]
    values: tuple[float, ...]
    coverage_intervals_sec: tuple[tuple[float, float], ...]
    schema_id: str = TRANSITION_ACOUSTIC_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "times_sec", tuple(self.times_sec))
        object.__setattr__(self, "values", tuple(self.values))
        object.__setattr__(
            self,
            "coverage_intervals_sec",
            tuple((start, end) for start, end in self.coverage_intervals_sec),
        )
        if self.schema_id != TRANSITION_ACOUSTIC_SCHEMA:
            raise TransitionAcousticError("unknown acoustic snapshot schema")
        if self.state not in {"observed", "unobserved", "invalid"}:
            raise TransitionAcousticError("unknown acoustic snapshot state")
        if (self.state == "observed") != (self.reason is None):
            raise TransitionAcousticError("observed state and reason disagree")
        if self.reason is not None and (not isinstance(self.reason, str) or not self.reason):
            raise TransitionAcousticError("reason must be a non-empty string or null")
        for name in ("analysis_wav_sha256", "source_sha256_before", "source_sha256_after"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str)
                or len(value) != 64
                or any(char not in "0123456789abcdef" for char in value)
            ):
                raise TransitionAcousticError(f"{name} must be a lowercase SHA-256 or null")
        if self.analysis_wav_sha256 is not None and self.analysis_wav_sha256 != self.source_sha256_before:
            raise TransitionAcousticError("analysis WAV identity must be the pre-read source hash")
        if self.duration_sec is not None:
            duration = _finite_float(self.duration_sec, "duration_sec")
            if duration < 0.0:
                raise TransitionAcousticError("duration_sec must be non-negative")
            object.__setattr__(self, "duration_sec", duration)
        for name in ("sample_rate_hz", "channel_count", "window_size_samples", "hop_size_samples"):
            _optional_nonnegative_int(getattr(self, name), name)
        for name in ("rms_window_ms", "rms_hop_ms", "diagnostic_threshold_rms"):
            value = _finite_float(getattr(self, name), name)
            if value < 0.0:
                raise TransitionAcousticError(f"{name} must be non-negative")
            object.__setattr__(self, name, value)
        if isinstance(self.smoothing_frames, bool) or not isinstance(self.smoothing_frames, int) or self.smoothing_frames < 1:
            raise TransitionAcousticError("smoothing_frames must be a positive integer")
        if self.stereo_mode != "average":
            raise TransitionAcousticError("transition acoustic stereo mode must be average")
        if len(self.times_sec) != len(self.values) or len(self.times_sec) != len(self.coverage_intervals_sec):
            raise TransitionAcousticError("RMS values, times, and coverage lengths must match")
        previous_time = -math.inf
        for index, (time_sec, value, interval) in enumerate(
            zip(self.times_sec, self.values, self.coverage_intervals_sec)
        ):
            center = _finite_float(time_sec, f"times_sec[{index}]")
            rms = _finite_float(value, f"values[{index}]")
            start = _finite_float(interval[0], f"coverage_intervals_sec[{index}][0]")
            end = _finite_float(interval[1], f"coverage_intervals_sec[{index}][1]")
            if center <= previous_time or center < 0.0 or rms < 0.0 or start < 0.0 or end < start:
                raise TransitionAcousticError("RMS samples must be finite, non-negative, ordered, and covered")
            if self.duration_sec is not None and (center > self.duration_sec or end > self.duration_sec + 1e-9):
                raise TransitionAcousticError("RMS sample exceeds analysis WAV duration")
            previous_time = center
        if self.state == "observed":
            if not self.analysis_wav_sha256 or not self.times_sec:
                raise TransitionAcousticError("observed snapshot requires source identity and RMS samples")
            if self.sample_rate_hz is None or self.sample_rate_hz <= 0:
                raise TransitionAcousticError("observed snapshot requires a positive sample rate")
            if self.channel_count is None or self.channel_count <= 0:
                raise TransitionAcousticError("observed snapshot requires a positive channel count")

    @property
    def content_digest(self) -> str:
        return _digest_payload(_canonical_payload(self))

    def to_dict(self) -> dict[str, Any]:
        payload = _canonical_payload(self)
        return {**payload, "content_digest": _digest_payload(payload)}


def build_transition_acoustic_snapshot(
    *,
    rms_series: RmsSeriesData | None,
    source_sha256_before: str | None,
    source_sha256_after: str | None,
    duration_sec: float | None,
    reason: str | None = None,
) -> TransitionAcousticSnapshot:
    if source_sha256_before is not None and source_sha256_after is not None and source_sha256_before != source_sha256_after:
        return TransitionAcousticSnapshot(
            state="invalid",
            reason="analysis_wav_changed_during_capture",
            analysis_wav_sha256=source_sha256_before,
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            duration_sec=duration_sec,
            sample_rate_hz=None,
            channel_count=None,
            window_size_samples=None,
            hop_size_samples=None,
            rms_window_ms=RMS_WINDOW_MS,
            rms_hop_ms=RMS_HOP_MS,
            smoothing_frames=RMS_SMOOTHING_FRAMES,
            stereo_mode="average",
            diagnostic_threshold_rms=TRANSITION_ACOUSTIC_DIAGNOSTIC_THRESHOLD_RMS,
            times_sec=(),
            values=(),
            coverage_intervals_sec=(),
        )
    if source_sha256_before is None or source_sha256_after is None:
        return TransitionAcousticSnapshot(
            state="unobserved",
            reason="analysis_wav_identity_unavailable",
            analysis_wav_sha256=source_sha256_before,
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            duration_sec=duration_sec,
            sample_rate_hz=None,
            channel_count=None,
            window_size_samples=None,
            hop_size_samples=None,
            rms_window_ms=RMS_WINDOW_MS,
            rms_hop_ms=RMS_HOP_MS,
            smoothing_frames=RMS_SMOOTHING_FRAMES,
            stereo_mode="average",
            diagnostic_threshold_rms=TRANSITION_ACOUSTIC_DIAGNOSTIC_THRESHOLD_RMS,
            times_sec=(),
            values=(),
            coverage_intervals_sec=(),
        )
    if rms_series is None:
        return TransitionAcousticSnapshot(
            state="unobserved",
            reason=reason or "rms_unavailable",
            analysis_wav_sha256=source_sha256_before,
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            duration_sec=duration_sec,
            sample_rate_hz=None,
            channel_count=None,
            window_size_samples=None,
            hop_size_samples=None,
            rms_window_ms=RMS_WINDOW_MS,
            rms_hop_ms=RMS_HOP_MS,
            smoothing_frames=RMS_SMOOTHING_FRAMES,
            stereo_mode="average",
            diagnostic_threshold_rms=TRANSITION_ACOUSTIC_DIAGNOSTIC_THRESHOLD_RMS,
            times_sec=(),
            values=(),
            coverage_intervals_sec=(),
        )


    try:
        times = tuple(_finite_float(value, f"times_sec[{index}]") for index, value in enumerate(rms_series.times_sec))
        values = tuple(_finite_float(value, f"values[{index}]") for index, value in enumerate(rms_series.values))
        if len(times) != len(values) or not times:
            raise TransitionAcousticError("invalid_rms_series_lengths")
        if isinstance(rms_series.sample_rate_hz, bool) or not isinstance(rms_series.sample_rate_hz, int):
            raise TransitionAcousticError("invalid_rms_sample_rate")
        if isinstance(rms_series.window_size_samples, bool) or not isinstance(rms_series.window_size_samples, int):
            raise TransitionAcousticError("invalid_rms_window_size")
        if isinstance(rms_series.hop_size_samples, bool) or not isinstance(rms_series.hop_size_samples, int):
            raise TransitionAcousticError("invalid_rms_hop_size")
        sample_rate = rms_series.sample_rate_hz
        if sample_rate <= 0:
            raise TransitionAcousticError("invalid_rms_sample_rate")
        if rms_series.window_size_samples <= 0 or rms_series.hop_size_samples <= 0:
            raise TransitionAcousticError("invalid_rms_window_or_hop")
        window_sec = rms_series.window_size_samples / sample_rate
        duration = None if duration_sec is None else _finite_float(duration_sec, "duration_sec")
        coverage: list[tuple[float, float]] = []
        for center in times:
            start = max(0.0, center - window_sec / 2.0)
            end = center + window_sec / 2.0
            if duration is not None:
                end = min(duration, end)
            coverage.append((start, end))
        return TransitionAcousticSnapshot(
            state="observed",
            reason=None,
            analysis_wav_sha256=source_sha256_before,
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            duration_sec=duration,
            sample_rate_hz=sample_rate,
            channel_count=int(rms_series.channel_count),
            window_size_samples=int(rms_series.window_size_samples),
            hop_size_samples=int(rms_series.hop_size_samples),
            rms_window_ms=RMS_WINDOW_MS,
            rms_hop_ms=RMS_HOP_MS,
            smoothing_frames=RMS_SMOOTHING_FRAMES,
            stereo_mode="average",
            diagnostic_threshold_rms=TRANSITION_ACOUSTIC_DIAGNOSTIC_THRESHOLD_RMS,
            times_sec=times,
            values=values,
            coverage_intervals_sec=tuple(coverage),
        )
    except (TransitionAcousticError, TypeError, ValueError, OverflowError):
        return TransitionAcousticSnapshot(
            state="invalid",
            reason="invalid_rms_series",
            analysis_wav_sha256=source_sha256_before,
            source_sha256_before=source_sha256_before,
            source_sha256_after=source_sha256_after,
            duration_sec=duration_sec,
            sample_rate_hz=None,
            channel_count=None,
            window_size_samples=None,
            hop_size_samples=None,
            rms_window_ms=RMS_WINDOW_MS,
            rms_hop_ms=RMS_HOP_MS,
            smoothing_frames=RMS_SMOOTHING_FRAMES,
            stereo_mode="average",
            diagnostic_threshold_rms=TRANSITION_ACOUSTIC_DIAGNOSTIC_THRESHOLD_RMS,
            times_sec=(),
            values=(),
            coverage_intervals_sec=(),
        )


def rebind_transition_acoustic_source(
    snapshot: TransitionAcousticSnapshot,
    *,
    source_sha256_after: str | None,
) -> TransitionAcousticSnapshot:
    """Close the acquisition window after later pipeline alignment work."""
    from dataclasses import replace

    if source_sha256_after is None:
        return replace(
            snapshot,
            state="unobserved",
            reason="analysis_wav_identity_verification_unavailable",
            source_sha256_after=None,
            times_sec=(),
            values=(),
            coverage_intervals_sec=(),
        )
    if snapshot.source_sha256_before != source_sha256_after:
        return replace(
            snapshot,
            state="invalid",
            reason="analysis_wav_changed_during_capture",
            source_sha256_after=source_sha256_after,
        )
    return replace(snapshot, source_sha256_after=source_sha256_after)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TransitionAcousticError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_transition_acoustic_snapshot(data: str | bytes | Mapping[str, Any]) -> TransitionAcousticSnapshot:
    if isinstance(data, (str, bytes)):
        try:
            raw = json.loads(data, object_pairs_hook=_reject_duplicate_keys, parse_constant=lambda value: (_ for _ in ()).throw(TransitionAcousticError(f"invalid numeric constant: {value}")))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransitionAcousticError("invalid acoustic snapshot JSON") from error
    else:
        raw = dict(data)
    if not isinstance(raw, dict) or set(raw) != _SNAPSHOT_FIELDS:
        raise TransitionAcousticError("acoustic snapshot fields do not match the strict schema")
    if raw["schema_id"] != TRANSITION_ACOUSTIC_SCHEMA:
        raise TransitionAcousticError("unknown acoustic snapshot schema")
    if not isinstance(raw["times_sec"], list) or not isinstance(raw["values"], list):
        raise TransitionAcousticError("RMS samples must be JSON arrays")
    if not isinstance(raw["coverage_intervals_sec"], list) or any(
        not isinstance(interval, list) or len(interval) != 2 for interval in raw["coverage_intervals_sec"]
    ):
        raise TransitionAcousticError("coverage intervals must be pairs")
    snapshot = TransitionAcousticSnapshot(
        state=raw["state"],
        reason=raw["reason"],
        analysis_wav_sha256=raw["analysis_wav_sha256"],
        source_sha256_before=raw["source_sha256_before"],
        source_sha256_after=raw["source_sha256_after"],
        duration_sec=raw["duration_sec"],
        sample_rate_hz=raw["sample_rate_hz"],
        channel_count=raw["channel_count"],
        window_size_samples=raw["window_size_samples"],
        hop_size_samples=raw["hop_size_samples"],
        rms_window_ms=raw["rms_window_ms"],
        rms_hop_ms=raw["rms_hop_ms"],
        smoothing_frames=raw["smoothing_frames"],
        stereo_mode=raw["stereo_mode"],
        diagnostic_threshold_rms=raw["diagnostic_threshold_rms"],
        times_sec=tuple(raw["times_sec"]),
        values=tuple(raw["values"]),
        coverage_intervals_sec=tuple(tuple(interval) for interval in raw["coverage_intervals_sec"]),
        schema_id=raw["schema_id"],
    )
    if raw["content_digest"] != snapshot.content_digest:
        raise TransitionAcousticError("acoustic snapshot digest mismatch")
    return snapshot


def measure_acoustic_window(
    snapshot: TransitionAcousticSnapshot,
    *,
    start_sec: float,
    end_sec: float,
) -> tuple[bool, float | None, str | None]:
    """Return policy eligibility, local peak ratio, and a stable reason code."""
    start = _finite_float(start_sec, "start_sec")
    end = _finite_float(end_sec, "end_sec")
    if snapshot.state == "invalid":
        return False, None, "acoustic_snapshot_invalid"
    if snapshot.state != "observed":
        return False, None, "rms_unobserved"
    if end <= start:
        return False, None, "zero_duration_window"
    covering = sorted(
        interval
        for interval in snapshot.coverage_intervals_sec
        if interval[1] > start and interval[0] < end
    )
    cursor = start
    for interval_start, interval_end in covering:
        if interval_start > cursor + 1e-9:
            return False, None, "incomplete_rms_coverage"
        cursor = max(cursor, interval_end)
        if cursor >= end - 1e-9:
            break
    if cursor < end - 1e-9:
        return False, None, "incomplete_rms_coverage"
    samples = [
        value
        for time_sec, value in zip(snapshot.times_sec, snapshot.values)
        if start - 1e-9 <= time_sec <= end + 1e-9
    ]
    if not samples:
        return False, None, "zero_sample_window"
    if any(value <= snapshot.diagnostic_threshold_rms for value in samples):
        return False, None, "rms_at_or_below_diagnostic_threshold"
    maximum = max(samples)
    ratio = min(samples) / maximum if maximum > 0.0 else 0.0
    if ratio < 0.81:
        return False, ratio, "continuity_below_threshold"
    return True, ratio, None

