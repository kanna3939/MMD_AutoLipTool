from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.transforms import blended_transform_factory

_JP_FONT_FAMILIES = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]


class WaveformView(FigureCanvas):
    def __init__(self) -> None:
        self._figure = Figure(figsize=(5, 2), dpi=100)
        super().__init__(self._figure)

        self._axes = self._figure.add_subplot(111)
        self._samples: list[float] = []
        self._duration_sec: float = 0.0
        self._morph_labels: list[tuple[float, str]] = []
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

    def set_morph_labels(self, labels: list[tuple[float, str]]) -> None:
        self._morph_labels = labels
        if self._samples:
            self._render_waveform()

    def clear_morph_labels(self) -> None:
        self.set_morph_labels([])

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
        if not self._morph_labels:
            return

        transform = blended_transform_factory(self._axes.transData, self._axes.transAxes)
        for time_sec, vowel in self._morph_labels:
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
