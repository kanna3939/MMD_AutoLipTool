from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

_JP_FONT_FAMILIES = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]

if TYPE_CHECKING:
    from vmd_writer import VowelTimelinePoint


class WaveformView(FigureCanvas):
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
        self._playback_position_sec: float | None = None
        self._playback_cursor_line: Line2D | None = None
        self.setMinimumHeight(140)
        self.show_placeholder("Waveform preview (not loaded)")

    def show_placeholder(self, message: str) -> None:
        self._samples = []
        self._duration_sec = 0.0
        self._playback_position_sec = None
        self._playback_cursor_line = None
        self._axes.clear()
        self._axes.set_xticks([])
        self._axes.set_yticks([])
        self._axes.text(
            0.5,
            0.5,
            message,
            transform=self._axes.transAxes,
            ha="center",
            va="center",
            fontsize=9,
            color="#666666",
        )
        self._axes.set_frame_on(True)
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
        if self._duration_sec > 0 and len(self._samples) > 1:
            step = self._duration_sec / (len(self._samples) - 1)
            x_values = [step * index for index in range(len(self._samples))]
            self._axes.plot(x_values, self._samples, linewidth=0.8, color="#2c7fb8")
            self._axes.set_xlim(0.0, self._duration_sec)
            self._axes.set_xlabel("Time (s)")
            self._draw_overlays()
        else:
            self._axes.plot(self._samples, linewidth=0.8, color="#2c7fb8")
            self._axes.set_xlabel("Sample")

        self._axes.set_ylim(-1.05, 1.05)
        self._axes.set_ylabel("Amp")
        self._axes.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
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
        frame_step_sec = 1.0 / 30.0
        frame_count = int(self._duration_sec / frame_step_sec)
        x_positions = [index * frame_step_sec for index in range(frame_count + 1)]
        if not x_positions or x_positions[-1] < self._duration_sec:
            x_positions.append(self._duration_sec)
        if not x_positions:
            return
        self._axes.vlines(
            x_positions,
            ymin=-1.05,
            ymax=1.05,
            colors="#888888",
            alpha=0.18,
            linestyles="--",
            linewidth=0.5,
            zorder=0.3,
        )

    def _draw_event_regions(self) -> None:
        if not self._morph_events:
            return
        for event in self._morph_events:
            start_sec, end_sec = self._event_bounds(event)
            if end_sec <= 0.0 or start_sec >= self._duration_sec:
                continue
            clamped_start = min(max(start_sec, 0.0), self._duration_sec)
            clamped_end = min(max(end_sec, 0.0), self._duration_sec)
            if clamped_end <= clamped_start:
                continue
            self._axes.axvspan(
                clamped_start,
                clamped_end,
                facecolor="#f0f4ff",
                edgecolor="#9bb0d9",
                alpha=0.22,
                linewidth=0.4,
                zorder=0.4,
            )

    def _draw_morph_labels(self) -> None:
        if not self._morph_events:
            return

        transform = blended_transform_factory(self._axes.transData, self._axes.transAxes)
        for event in self._morph_events:
            time_sec = event.time_sec
            vowel = event.vowel
            start_sec, end_sec = self._event_bounds(event)
            if end_sec < 0.0 or start_sec > self._duration_sec:
                continue
            clamped_time = min(max(time_sec, 0.0), self._duration_sec)
            self._axes.text(
                clamped_time,
                0.98,
                vowel,
                transform=transform,
                ha="center",
                va="top",
                fontsize=9,
                color="#444444",
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
            color="#d62728",
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
        self._playback_cursor_line.set_xdata([clamped_sec, clamped_sec])
        self._playback_cursor_line.set_visible(True)
        return True

    def _event_bounds(self, event: VowelTimelinePoint) -> tuple[float, float]:
        if event.start_sec is not None and event.end_sec is not None:
            return (event.start_sec, event.end_sec)
        half = max(event.duration_sec, 0.0) * 0.5
        return (event.time_sec - half, event.time_sec + half)
