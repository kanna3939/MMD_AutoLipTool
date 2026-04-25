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

    def zoom_in(self):
        if self.duration_sec <= 0: return
        if self.zoom_factor < 8:
            self.zoom_factor *= 2
            self._apply_zoom_from_center()

    def zoom_out(self):
        if self.duration_sec <= 0: return
        if self.zoom_factor > 1:
            self.zoom_factor //= 2
            self._apply_zoom_from_center()

    def reset_zoom(self):
        self.zoom_factor = 1
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = self.duration_sec
        self._notify()

    def _apply_zoom_from_center(self):
        """[MS15-B4] Zoom anchor is current viewport center"""
        center_sec = (self.viewport_start_sec + self.viewport_end_sec) / 2.0
        self._resolve_viewport(center_sec, anchor_ratio=0.5)

    def update_playback_position(self, pos_sec: float):
        """[MS15-B4] Auto-follow logic."""
        if self.duration_sec <= 0 or self.zoom_factor == 1:
            return

        span = self.viewport_end_sec - self.viewport_start_sec
        if span <= 0:
            return

        # Trigger at 80%
        threshold_sec = self.viewport_start_sec + span * 0.8
        if pos_sec >= threshold_sec or pos_sec < self.viewport_start_sec:
            # Re-center at 60%
            self._resolve_viewport(pos_sec, anchor_ratio=0.6)

    def _resolve_viewport(self, anchor_time_sec: float, anchor_ratio: float):
        """[MS15-B4] Resolve viewport with constraints"""
        requested_span = self.duration_sec / self.zoom_factor
        min_span = min(self.duration_sec, 0.25)
        effective_span = max(requested_span, min_span)

        if effective_span >= self.duration_sec:
            self.viewport_start_sec = 0.0
            self.viewport_end_sec = self.duration_sec
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

        self.viewport_start_sec = new_start
        self.viewport_end_sec = new_end
        self._notify()

    def _notify(self):
        if self.on_viewport_changed:
            self.on_viewport_changed(self.viewport_start_sec, self.viewport_end_sec)
