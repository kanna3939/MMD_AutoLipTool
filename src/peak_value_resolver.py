from __future__ import annotations

from dataclasses import dataclass
import math


MORPH_FRAME_OPEN_EPSILON = 1e-9


@dataclass(frozen=True)
class PeakValueResolution:
    value: float
    used_observation: bool
    fallback_reason: str | None = None


def _finite_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        normalized = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return normalized if math.isfinite(normalized) else None


def _fallback(opening_peak: float, reason: str) -> PeakValueResolution:
    return PeakValueResolution(
        value=opening_peak,
        used_observation=False,
        fallback_reason=reason,
    )


def resolve_close_peak_value(
    observation: object | None,
    *,
    peak_end_frame: int,
    opening_peak: float,
    frame_rate: int,
) -> PeakValueResolution:
    """Resolve a source event's close-side peak from its RMS observation."""

    opening_value = _finite_float(opening_peak)
    if opening_value is None or opening_value < 0.0:
        return PeakValueResolution(0.0, False, "opening_peak_invalid")
    if (
        isinstance(peak_end_frame, bool)
        or not isinstance(peak_end_frame, int)
        or peak_end_frame < 0
    ):
        return _fallback(opening_value, "peak_end_frame_invalid")
    if isinstance(frame_rate, bool) or not isinstance(frame_rate, int) or frame_rate <= 0:
        return _fallback(opening_value, "frame_rate_invalid")
    if observation is None:
        return _fallback(opening_value, "observation_missing")

    local_peak = _finite_float(getattr(observation, "local_peak", None))
    if local_peak is None or local_peak <= 0.0:
        return _fallback(opening_value, "local_peak_invalid")

    raw_times = getattr(observation, "rms_window_times_sec", None)
    raw_values = getattr(observation, "rms_window_values", None)
    if raw_times is None or raw_values is None:
        return _fallback(opening_value, "rms_window_missing")
    try:
        times = tuple(_finite_float(value) for value in raw_times)
        values = tuple(_finite_float(value) for value in raw_values)
    except TypeError:
        return _fallback(opening_value, "rms_window_invalid")
    if not times or not values:
        return _fallback(opening_value, "rms_window_empty")
    if len(times) != len(values):
        return _fallback(opening_value, "rms_window_length_mismatch")
    if any(value is None or value < 0.0 for value in times):
        return _fallback(opening_value, "rms_time_invalid")
    if any(value is None or value < 0.0 for value in values):
        return _fallback(opening_value, "rms_value_invalid")

    normalized_times = tuple(float(value) for value in times if value is not None)
    normalized_values = tuple(float(value) for value in values if value is not None)
    target_sec = peak_end_frame / frame_rate
    forward_indices = [
        index for index, time_sec in enumerate(normalized_times)
        if time_sec >= target_sec
    ]
    if forward_indices:
        selected_index = min(forward_indices, key=normalized_times.__getitem__)
    else:
        selected_index = len(normalized_times) - 1

    selected_value = normalized_values[selected_index]
    if selected_value <= 0.0:
        return _fallback(opening_value, "selected_rms_non_positive")

    smoothed_value = selected_value
    if selected_index + 1 < len(normalized_values):
        smoothed_value = (
            selected_value * 0.75
            + normalized_values[selected_index + 1] * 0.25
        )

    normalized_ratio = min(1.0, smoothed_value / local_peak)
    decayed_value = round(opening_value * normalized_ratio, 4)
    resolved_value = max(
        MORPH_FRAME_OPEN_EPSILON,
        min(opening_value, decayed_value),
    )
    return PeakValueResolution(resolved_value, True)
