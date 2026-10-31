import wx
from typing import Callable

class ViewportController:
    """
    [MS15-B4] Canonical Shared Viewport Controller.
    Manages the single source of truth for the viewport and handles zoom/auto-follow logic.
    """
    def __init__(self, on_viewport_changed: Callable[[float, float], None]):
        self.on_viewport_changed = on_viewport_changed
        self.duration_sec = 0.0
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = 0.0
        self.zoom_factor = 1  # 1, 2, 4, 8

    def set_duration(self, duration_sec: float):
        """[MS15-B4] Update duration and reset viewport to full range."""
        self.duration_sec = max(0.0, duration_sec)
        self.reset_zoom()

    def zoom_in(self, *, playback_position_sec: float | None = None):
        if self.duration_sec <= 0: return
        if self.zoom_factor < 8:
            self.zoom_factor *= 2
            self._apply_zoom(playback_position_sec)

    def zoom_out(self, *, playback_position_sec: float | None = None):
        if self.duration_sec <= 0: return
        if self.zoom_factor > 1:
            self.zoom_factor //= 2
            self._apply_zoom(playback_position_sec)

    def _apply_zoom(self, playback_position_sec: float | None):
        if playback_position_sec is not None:
            self._resolve_viewport(playback_position_sec, anchor_ratio=0.5)
        else:
            self._apply_zoom_from_center()

    def reset_zoom(self):
        changed = (
            self.zoom_factor != 1
            or self.viewport_start_sec != 0.0
            or self.viewport_end_sec != self.duration_sec
        )
        self.zoom_factor = 1
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = self.duration_sec
        if changed:
            self._notify()

    def pan(self, delta_sec: float):
        if self.duration_sec <= 0 or self.zoom_factor == 1: return
        span = self.viewport_end_sec - self.viewport_start_sec
        new_start = self.viewport_start_sec + delta_sec
        new_end = self.viewport_end_sec + delta_sec

        if new_start < 0.0:
            new_start = 0.0
            new_end = span
        elif new_end > self.duration_sec:
            new_end = self.duration_sec
            new_start = self.duration_sec - span

        self.viewport_start_sec = new_start
        self.viewport_end_sec = new_end
        self._notify()

    def _apply_zoom_from_center(self):
        """[MS15-B4] Zoom anchor is current viewport center"""
        center_sec = (self.viewport_start_sec + self.viewport_end_sec) / 2.0
        self._resolve_viewport(center_sec, anchor_ratio=0.5)

    def update_playback_position(self, pos_sec: float, *, allow_backward: bool = False):
        """Follow forward playback; optionally follow backward waveform scrubs."""
        if self.duration_sec <= 0 or self.zoom_factor == 1:
            return

        span = self.viewport_end_sec - self.viewport_start_sec
        if span <= 0:
            return

        left_threshold_sec = self.viewport_start_sec + span * 0.2
        right_threshold_sec = self.viewport_start_sec + span * 0.8
        if pos_sec >= right_threshold_sec or pos_sec < self.viewport_start_sec:
            # Keep the playback cursor near the requested left-side anchor.
            self._resolve_viewport(pos_sec, anchor_ratio=0.2)
        elif (
            allow_backward
            and pos_sec <= left_threshold_sec
            and self.viewport_start_sec > 0.0
        ):
            # Scrubbing back toward the left edge must move the shared viewport too.
            self._resolve_viewport(pos_sec, anchor_ratio=0.4)

    def ensure_position_visible(self, position_sec: float) -> bool:
        """Move the current zoom window only when the position is outside it."""
        if self.duration_sec <= 0:
            return False
        position = max(0.0, min(self.duration_sec, float(position_sec)))
        if self.viewport_start_sec <= position <= self.viewport_end_sec:
            return False
        self._resolve_viewport(position, anchor_ratio=0.0)
        return True

    def _resolve_viewport(self, anchor_time_sec: float, anchor_ratio: float):
        """[MS15-B4] Resolve viewport with constraints"""
        requested_span = self.duration_sec / self.zoom_factor
        min_span = min(self.duration_sec, 0.25)
        effective_span = max(requested_span, min_span)

        if effective_span >= self.duration_sec:
            changed = (
                self.viewport_start_sec != 0.0
                or self.viewport_end_sec != self.duration_sec
            )
            self.viewport_start_sec = 0.0
            self.viewport_end_sec = self.duration_sec
            if changed:
                self._notify()
            return

        # Calculate new start based on anchor
        new_start = anchor_time_sec - (effective_span * anchor_ratio)
        new_end = new_start + effective_span

        # Clamp to bounds (priority 1)
        if new_start < 0.0:
            new_start = 0.0
            new_end = effective_span
        elif new_end > self.duration_sec:
            new_end = self.duration_sec
            new_start = max(0.0, self.duration_sec - effective_span)

        changed = (
            self.viewport_start_sec != new_start
            or self.viewport_end_sec != new_end
        )
        self.viewport_start_sec = new_start
        self.viewport_end_sec = new_end
        if changed:
            self._notify()

    def _notify(self):
        if self.on_viewport_changed:
            self.on_viewport_changed(self.viewport_start_sec, self.viewport_end_sec)
