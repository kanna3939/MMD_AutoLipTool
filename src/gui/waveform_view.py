from __future__ import annotations

import math
from typing import TYPE_CHECKING

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory
from PySide6.QtCore import Qt, Signal

from gui.i18n_strings import ThemeStrings

_JP_FONT_FAMILIES = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
_FRAME_RATE = 30.0

if TYPE_CHECKING:
    from vmd_writer import VowelTimelinePoint


class WaveformView(FigureCanvas):
    pan_requested = Signal(float)

    _THEME_COLORS = {
        ThemeStrings.DARK: {
            "figure_bg": "#20262f",
            "axes_bg": "#20262f",
            "placeholder_text": "#aeb6c2",
            "waveform": "#7cc6fe",
            "axis_text": "#d8dee9",
            "grid": "#516072",
            "frame_grid": "#6b7280",
            "event_fill": "#334155",
            "event_edge": "#94a3b8",
            "label_text": "#d8dee9",
            "cursor": "#f87171",
            "spine": "#556072",
            "tick": "#b8c0cc",
        },
        ThemeStrings.LIGHT: {
            "figure_bg": "#ffffff",
            "axes_bg": "#ffffff",
            "placeholder_text": "#667085",
            "waveform": "#2c7fb8",
            "axis_text": "#344054",
            "grid": "#d0d7de",
            "frame_grid": "#98a2b3",
            "event_fill": "#dbeafe",
            "event_edge": "#93c5fd",
            "label_text": "#344054",
            "cursor": "#d62728",
            "spine": "#cbd5e1",
            "tick": "#667085",
        },
    }

    def __init__(self) -> None:
        self._figure = Figure(figsize=(5, 2), dpi=100)
        super().__init__(self._figure)

        self._axes = self._figure.add_subplot(111)
        self._samples: list[float] = []
        self._duration_sec: float = 0.0
        self._morph_events: list[VowelTimelinePoint] = []
        self._default_show_frame_grid = False
        self._default_show_vowel_labels = True
        self._default_show_event_regions = False
        self._show_frame_grid = self._default_show_frame_grid
        self._show_vowel_labels = self._default_show_vowel_labels
        self._show_event_regions = self._default_show_event_regions
        self._viewport_start_sec: float | None = None
        self._viewport_end_sec: float | None = None
        self._playback_position_sec: float | None = None
        self._playback_cursor_line: Line2D | None = None
        self._pan_drag_active = False
        self._pan_drag_last_x_sec: float | None = None
        self._pan_press_cid: int | None = None
        self._pan_move_cid: int | None = None
        self._pan_release_cid: int | None = None
        self._theme_name = ThemeStrings.DARK
        self._placeholder_message = "Waveform preview (not loaded)"
        self.setMinimumHeight(140)
        self._connect_pan_interaction()
        self.show_placeholder(self._placeholder_message)

    def set_theme(self, theme_name: str) -> None:
        resolved_theme = self._normalize_theme_name(theme_name)
        if self._theme_name == resolved_theme:
            return
        self._theme_name = resolved_theme
        if self._samples:
            self._render_waveform()
            return
        self.show_placeholder(self._placeholder_message)

    def show_placeholder(self, message: str) -> None:
        self._placeholder_message = str(message)
        self._samples = []
        self._duration_sec = 0.0
        self._viewport_start_sec = None
        self._viewport_end_sec = None
        self._playback_position_sec = None
        self._playback_cursor_line = None
        self._pan_drag_active = False
        self._pan_drag_last_x_sec = None
        self.unsetCursor()
        self._axes.clear()
        self._axes.set_xticks([])
        self._axes.set_yticks([])
        self._axes.text(
            0.5,
            0.5,
            self._placeholder_message,
            transform=self._axes.transAxes,
            ha="center",
            va="center",
            fontsize=9,
            color=self._theme_colors()["placeholder_text"],
        )
        self._apply_axes_theme()
        self._figure.tight_layout()
        self.draw_idle()

    def set_morph_events(self, events: list[VowelTimelinePoint]) -> None:
        self._morph_events = list(events)
        if self._samples:
            self._render_waveform()

    def set_morph_labels(self, labels: list[tuple[float, str]]) -> None:
        # Backward-compatible API for callers that only have (time, vowel).
        from vmd_writer import VowelTimelinePoint

        self._morph_events = [
            VowelTimelinePoint(time_sec=time_sec, vowel=vowel, duration_sec=0.0)
            for time_sec, vowel in labels
        ]
        if self._samples:
            self._render_waveform()

    def clear_morph_labels(self) -> None:
        self.set_morph_events([])

    def set_playback_position_sec(self, position_sec: float) -> None:
        if not self._samples or self._duration_sec <= 0.0:
            return

        clamped_sec = min(max(float(position_sec), 0.0), self._duration_sec)
        if (
            self._playback_position_sec is not None
            and abs(self._playback_position_sec - clamped_sec) <= 1e-6
        ):
            return

        self._playback_position_sec = clamped_sec
        if self._update_playback_cursor_line():
            self.draw_idle()
            return
        self._render_waveform()

    def clear_playback_cursor(self) -> None:
        if self._playback_position_sec is None and self._playback_cursor_line is None:
            return
        self._playback_position_sec = None
        self._playback_cursor_line = None
        if self._samples:
            self._render_waveform()
            return
        self.draw_idle()

    def set_viewport_sec(self, start_sec: float, end_sec: float) -> None:
        normalized_start, normalized_end = self._normalize_viewport_sec(start_sec, end_sec)
        if self._is_same_viewport(normalized_start, normalized_end):
            return
        self._viewport_start_sec = normalized_start
        self._viewport_end_sec = normalized_end
        if self._samples:
            self._render_waveform()
            return
        self.draw_idle()

    def clear_viewport_sec(self) -> None:
        if self._viewport_start_sec is None and self._viewport_end_sec is None:
            return
        self._viewport_start_sec = None
        self._viewport_end_sec = None
        if self._samples:
            self._render_waveform()
            return
        self.draw_idle()

    def viewport_sec(self) -> tuple[float | None, float | None]:
        return (self._viewport_start_sec, self._viewport_end_sec)

    def set_show_frame_grid(self, enabled: bool) -> None:
        enabled_bool = bool(enabled)
        if self._show_frame_grid == enabled_bool:
            return
        self._show_frame_grid = enabled_bool
        self._refresh_after_overlay_option_changed()

    def set_show_vowel_labels(self, enabled: bool) -> None:
        enabled_bool = bool(enabled)
        if self._show_vowel_labels == enabled_bool:
            return
        self._show_vowel_labels = enabled_bool
        self._refresh_after_overlay_option_changed()

    def set_show_event_regions(self, enabled: bool) -> None:
        enabled_bool = bool(enabled)
        if self._show_event_regions == enabled_bool:
            return
        self._show_event_regions = enabled_bool
        self._refresh_after_overlay_option_changed()

    def reset_overlay_visibility(self) -> None:
        changed = (
            self._show_frame_grid != self._default_show_frame_grid
            or self._show_vowel_labels != self._default_show_vowel_labels
            or self._show_event_regions != self._default_show_event_regions
        )
        self._show_frame_grid = self._default_show_frame_grid
        self._show_vowel_labels = self._default_show_vowel_labels
        self._show_event_regions = self._default_show_event_regions
        if changed:
            self._refresh_after_overlay_option_changed()

    def overlay_visibility(self) -> tuple[bool, bool, bool]:
        return (
            self._show_frame_grid,
            self._show_vowel_labels,
            self._show_event_regions,
        )

    def get_plot_area_rect(self) -> tuple[float, float, float, float] | None:
        """
        Returns the actual drawing area (plot area) of the waveform within the widget's coordinate system.
        This represents the region inside the axes, excluding ticks, labels, and padding.
        Returns:
            (x, y, width, height) in pixels relative to the widget's top-left corner,
            or None if the layout has not been computed yet.
        """
        if self._duration_sec < 0.0:
            return None

        try:
            # get_window_extent returns the bounding box in display coordinates
            # For a FigureCanvasQTAgg, the bottom-left is (0,0).
            bbox = self._axes.get_window_extent()
            
            # Matplotlib display coordinates: (0, 0) is bottom-left.
            # PySide6 widget coordinates: (0, 0) is top-left.
            # We need to invert the Y axis.
            canvas_height = self.figure.bbox.height
            
            # Convert to PySide6 coordinates
            x = bbox.x0
            y = canvas_height - bbox.y1  # Invert Y to measure from the top
            width = bbox.width
            height = bbox.height
            
            return (float(x), float(y), float(width), float(height))
        except (AttributeError, ValueError, TypeError):
            return None

    @property
    def plot_area_rect(self) -> tuple[float, float, float, float] | None:
        """
        Convenience property to access the inner plot area bounds.
        See get_plot_area_rect for details.
        """
        return self.get_plot_area_rect()

    def plot_waveform(self, samples: list[float], duration_sec: float) -> None:
        self._samples = samples
        self._duration_sec = duration_sec

        if not samples:
            self.show_placeholder("No waveform data")
            return

        self._render_waveform()

    def _render_waveform(self) -> None:
        self._axes.clear()
        self._playback_cursor_line = None
        self._apply_axes_theme()
        if self._duration_sec > 0 and len(self._samples) > 1:
            step = self._duration_sec / (len(self._samples) - 1)
            x_values = [step * index for index in range(len(self._samples))]
            self._axes.plot(
                x_values,
                self._samples,
                linewidth=0.8,
                color=self._theme_colors()["waveform"],
            )
            visible_start_sec, visible_end_sec = self._resolved_visible_range_sec()
            self._axes.set_xlim(visible_start_sec, visible_end_sec)
            self._axes.set_xlabel("Frame (30fps)")
            self._apply_frame_axis_ticks(visible_start_sec, visible_end_sec)
            self._draw_overlays()
        else:
            self._axes.plot(
                self._samples,
                linewidth=0.8,
                color=self._theme_colors()["waveform"],
            )
            self._axes.set_xlabel("Sample")

        self._axes.set_ylim(-1.05, 1.05)
        self._axes.set_ylabel("")
        self._axes.grid(
            True,
            alpha=0.3,
            linestyle="-",
            linewidth=0.5,
            color=self._theme_colors()["grid"],
        )
        self._figure.tight_layout()
        self.draw_idle()

    def _draw_overlays(self) -> None:
        if self._show_frame_grid:
            self._draw_frame_grid()
        if self._show_event_regions:
            self._draw_event_regions()
        if self._show_vowel_labels:
            self._draw_morph_labels()
        self._draw_playback_cursor()

    def _draw_frame_grid(self) -> None:
        if self._duration_sec <= 0.0:
            return
        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec()
        if visible_end_sec <= visible_start_sec:
            return
        frame_step_sec = 1.0 / _FRAME_RATE
        first_frame = int(math.floor(visible_start_sec / frame_step_sec))
        if first_frame < 0:
            first_frame = 0
        x_positions: list[float] = []
        frame_no = first_frame
        while True:
            position = frame_no * frame_step_sec
            if position > visible_end_sec + 1e-9:
                break
            if position >= visible_start_sec - 1e-9:
                x_positions.append(position)
            frame_no += 1
        if not x_positions or x_positions[-1] < visible_end_sec:
            x_positions.append(visible_end_sec)
        if not x_positions:
            return
        self._axes.vlines(
            x_positions,
            ymin=-1.05,
            ymax=1.05,
            colors=self._theme_colors()["frame_grid"],
            alpha=0.18,
            linestyles="--",
            linewidth=0.5,
            zorder=0.3,
        )

    def _draw_event_regions(self) -> None:
        if not self._morph_events:
            return
        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec()
        if visible_end_sec <= visible_start_sec:
            return
        for event in self._morph_events:
            start_sec, end_sec = self._event_bounds(event)
            if end_sec <= visible_start_sec or start_sec >= visible_end_sec:
                continue
            clamped_start = min(max(start_sec, visible_start_sec), visible_end_sec)
            clamped_end = min(max(end_sec, visible_start_sec), visible_end_sec)
            if clamped_end <= clamped_start:
                continue
            self._axes.axvspan(
                clamped_start,
                clamped_end,
                facecolor=self._theme_colors()["event_fill"],
                edgecolor=self._theme_colors()["event_edge"],
                alpha=0.22,
                linewidth=0.4,
                zorder=0.4,
            )

    def _draw_morph_labels(self) -> None:
        if not self._morph_events:
            return

        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec()
        if visible_end_sec <= visible_start_sec:
            return
        transform = blended_transform_factory(self._axes.transData, self._axes.transAxes)
        for event in self._morph_events:
            time_sec = event.time_sec
            vowel = event.vowel
            start_sec, end_sec = self._event_bounds(event)
            if end_sec < visible_start_sec or start_sec > visible_end_sec:
                continue
            clamped_time = min(max(time_sec, visible_start_sec), visible_end_sec)
            self._axes.text(
                clamped_time,
                0.98,
                vowel,
                transform=transform,
                ha="center",
                va="top",
                fontsize=9,
                color=self._theme_colors()["label_text"],
                fontfamily=_JP_FONT_FAMILIES,
            )

    def _refresh_after_overlay_option_changed(self) -> None:
        if self._samples:
            self._render_waveform()
            return
        self.draw_idle()

    def _draw_playback_cursor(self) -> None:
        if self._playback_position_sec is None or self._duration_sec <= 0.0:
            self._playback_cursor_line = None
            return
        clamped_sec = min(max(self._playback_position_sec, 0.0), self._duration_sec)
        self._playback_cursor_line = self._axes.axvline(
            x=clamped_sec,
            ymin=0.0,
            ymax=1.0,
            color=self._theme_colors()["cursor"],
            linewidth=1.2,
            alpha=0.95,
            zorder=9.0,
        )

    def _update_playback_cursor_line(self) -> bool:
        if self._playback_cursor_line is None:
            return False
        if self._playback_position_sec is None:
            return False
        if self._playback_cursor_line.axes is not self._axes:
            return False
        clamped_sec = min(max(self._playback_position_sec, 0.0), self._duration_sec)
        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec()
        is_visible = visible_start_sec <= clamped_sec <= visible_end_sec
        self._playback_cursor_line.set_xdata([clamped_sec, clamped_sec])
        self._playback_cursor_line.set_visible(is_visible)
        return True

    def _connect_pan_interaction(self) -> None:
        self._pan_press_cid = self.mpl_connect("button_press_event", self._on_pan_press_event)
        self._pan_move_cid = self.mpl_connect("motion_notify_event", self._on_pan_move_event)
        self._pan_release_cid = self.mpl_connect(
            "button_release_event", self._on_pan_release_event
        )

    def _on_pan_press_event(self, event) -> None:
        if event.button != 1:
            return
        if event.inaxes is not self._axes:
            return
        current_x_sec = self._event_x_sec_for_pan(event)
        if current_x_sec is None:
            return
        self._pan_drag_active = True
        self._pan_drag_last_x_sec = current_x_sec
        self.setCursor(Qt.ClosedHandCursor)

    def _on_pan_move_event(self, event) -> None:
        if not self._pan_drag_active:
            return
        current_x_sec = self._event_x_sec_for_pan(event)
        if current_x_sec is None:
            return
        previous_x_sec = self._pan_drag_last_x_sec
        self._pan_drag_last_x_sec = current_x_sec
        if previous_x_sec is None:
            return
        pan_delta_sec = previous_x_sec - current_x_sec
        if abs(pan_delta_sec) <= 1e-9:
            return
        self.pan_requested.emit(pan_delta_sec)

    def _on_pan_release_event(self, event) -> None:
        del event
        if not self._pan_drag_active:
            return
        self._pan_drag_active = False
        self._pan_drag_last_x_sec = None
        self.unsetCursor()

    def _event_x_sec_for_pan(self, event) -> float | None:
        if self._duration_sec <= 0.0:
            return None
        if event.xdata is None:
            return None
        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec()
        if visible_end_sec <= visible_start_sec:
            return None
        try:
            resolved_x_sec = float(event.xdata)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(resolved_x_sec):
            return None
        return min(max(resolved_x_sec, visible_start_sec), visible_end_sec)

    def _event_bounds(self, event: VowelTimelinePoint) -> tuple[float, float]:
        if event.start_sec is not None and event.end_sec is not None:
            return (event.start_sec, event.end_sec)
        half = max(event.duration_sec, 0.0) * 0.5
        return (event.time_sec - half, event.time_sec + half)

    def _normalize_viewport_sec(self, start_sec: float, end_sec: float) -> tuple[float, float]:
        normalized_start = self._normalize_non_negative_sec(start_sec)
        normalized_end = self._normalize_non_negative_sec(end_sec)
        if normalized_end < normalized_start:
            normalized_start, normalized_end = normalized_end, normalized_start
        return (normalized_start, normalized_end)

    def _normalize_non_negative_sec(self, value: float) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(resolved):
            return 0.0
        return max(resolved, 0.0)

    def _is_same_viewport(self, start_sec: float, end_sec: float) -> bool:
        if self._viewport_start_sec is None or self._viewport_end_sec is None:
            return False
        return (
            abs(start_sec - self._viewport_start_sec) <= 1e-6
            and abs(end_sec - self._viewport_end_sec) <= 1e-6
        )

    def _resolved_visible_range_sec(self) -> tuple[float, float]:
        full_start_sec = 0.0
        full_end_sec = max(self._duration_sec, 0.0)
        if full_end_sec <= full_start_sec:
            return (full_start_sec, full_start_sec)
        if self._viewport_start_sec is None or self._viewport_end_sec is None:
            return (full_start_sec, full_end_sec)
        clipped_start_sec = min(max(self._viewport_start_sec, full_start_sec), full_end_sec)
        clipped_end_sec = min(max(self._viewport_end_sec, full_start_sec), full_end_sec)
        if clipped_end_sec <= clipped_start_sec:
            return (full_start_sec, full_end_sec)
        return (clipped_start_sec, clipped_end_sec)

    def _apply_frame_axis_ticks(self, visible_start_sec: float, visible_end_sec: float) -> None:
        if visible_end_sec <= visible_start_sec:
            return
        major_frames = self._build_major_frame_ticks(visible_start_sec, visible_end_sec)
        if not major_frames:
            return
        major_tick_seconds = [frame / _FRAME_RATE for frame in major_frames]
        major_labels = [str(frame) for frame in major_frames]
        self._axes.set_xticks(major_tick_seconds)
        self._axes.set_xticklabels(major_labels)

    def _apply_axes_theme(self) -> None:
        colors = self._theme_colors()
        self._figure.patch.set_facecolor(colors["figure_bg"])
        self._axes.set_facecolor(colors["axes_bg"])
        self._axes.tick_params(axis="x", colors=colors["tick"])
        self._axes.tick_params(axis="y", colors=colors["tick"])
        self._axes.xaxis.label.set_color(colors["axis_text"])
        self._axes.yaxis.label.set_color(colors["axis_text"])
        for spine in self._axes.spines.values():
            spine.set_color(colors["spine"])

    def _theme_colors(self) -> dict[str, str]:
        return self._THEME_COLORS[self._theme_name]

    def _normalize_theme_name(self, theme_name: str) -> str:
        resolved_theme = str(theme_name).strip().lower()
        if resolved_theme not in ThemeStrings.SUPPORTED:
            return ThemeStrings.DARK
        return resolved_theme

    def _build_major_frame_ticks(self, start_sec: float, end_sec: float) -> list[int]:
        start_frame = max(0, self._seconds_to_frame_ceil(start_sec))
        end_frame = max(start_frame, self._seconds_to_frame_floor(end_sec))
        frame_span = max(end_frame - start_frame, 1)
        max_label_count = 9
        min_step = max(1, int(math.ceil(frame_span / max_label_count)))
        step_frame = self._normalized_tick_step(min_step)

        first_frame = ((start_frame + step_frame - 1) // step_frame) * step_frame
        frames: list[int] = []
        frame_no = first_frame
        while frame_no <= end_frame:
            frames.append(frame_no)
            frame_no += step_frame

        if not frames:
            return [start_frame, end_frame]
        if frames[0] != start_frame:
            frames.insert(0, start_frame)
        if frames[-1] != end_frame:
            frames.append(end_frame)
        return frames

    def _normalized_tick_step(self, minimum_step: int) -> int:
        if minimum_step <= 1:
            return 1
        magnitude = 1
        while magnitude * 10 < minimum_step:
            magnitude *= 10
        for candidate in (1, 2, 5, 10):
            step = candidate * magnitude
            if step >= minimum_step:
                return step
        return 10 * magnitude

    def _seconds_to_frame_floor(self, seconds: float) -> int:
        return int(math.floor(max(seconds, 0.0) * _FRAME_RATE + 1e-9))

    def _seconds_to_frame_ceil(self, seconds: float) -> int:
        return int(math.ceil(max(seconds, 0.0) * _FRAME_RATE - 1e-9))
