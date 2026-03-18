from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class WaveformView(FigureCanvas):
    def __init__(self) -> None:
        self._figure = Figure(figsize=(5, 2), dpi=100)
        super().__init__(self._figure)

        self._axes = self._figure.add_subplot(111)
        self.setMinimumHeight(140)
        self.show_placeholder("Waveform preview (not loaded)")

    def show_placeholder(self, message: str) -> None:
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

    def plot_waveform(self, samples: list[float], duration_sec: float) -> None:
        if not samples:
            self.show_placeholder("No waveform data")
            return

        self._axes.clear()
        if duration_sec > 0 and len(samples) > 1:
            step = duration_sec / (len(samples) - 1)
            x_values = [step * index for index in range(len(samples))]
            self._axes.plot(x_values, samples, linewidth=0.8, color="#2c7fb8")
            self._axes.set_xlim(0.0, duration_sec)
            self._axes.set_xlabel("Time (s)")
        else:
            self._axes.plot(samples, linewidth=0.8, color="#2c7fb8")
            self._axes.set_xlabel("Sample")

        self._axes.set_ylim(-1.05, 1.05)
        self._axes.set_ylabel("Amp")
        self._axes.grid(True, alpha=0.25, linestyle="-", linewidth=0.5)
        self._figure.tight_layout()
        self.draw_idle()
