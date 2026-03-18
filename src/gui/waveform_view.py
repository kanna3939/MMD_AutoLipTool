from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
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
        self.setMinimumHeight(140)
        self.show_placeholder("Waveform preview (not loaded)")

    def show_placeholder(self, message: str) -> None:
        self._samples = []
        self._duration_sec = 0.0
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

    def plot_waveform(self, samples: list[float], duration_sec: float) -> None:
        self._samples = samples
        self._duration_sec = duration_sec

        if not samples:
            self.show_placeholder("No waveform data")
            return

        self._render_waveform()

    def _render_waveform(self) -> None:
        self._axes.clear()
        if self._duration_sec > 0 and len(self._samples) > 1:
            step = self._duration_sec / (len(self._samples) - 1)
            x_values = [step * index for index in range(len(self._samples))]
            self._axes.plot(x_values, self._samples, linewidth=0.8, color="#2c7fb8")
            self._axes.set_xlim(0.0, self._duration_sec)
            self._axes.set_xlabel("Time (s)")
            self._draw_morph_labels()
        else:
            self._axes.plot(self._samples, linewidth=0.8, color="#2c7fb8")
            self._axes.set_xlabel("Sample")

        self._axes.set_ylim(-1.05, 1.05)
        self._axes.set_ylabel("Amp")
        self._axes.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self._figure.tight_layout()
        self.draw_idle()

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

    def _event_bounds(self, event: VowelTimelinePoint) -> tuple[float, float]:
        if event.start_sec is not None and event.end_sec is not None:
            return (event.start_sec, event.end_sec)
        half = max(event.duration_sec, 0.0) * 0.5
        return (event.time_sec - half, event.time_sec + half)
