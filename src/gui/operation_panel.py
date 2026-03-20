from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget


class OperationPanel(QWidget):
    """Display-only panel for top operation controls.

    This component intentionally does not decide enable/disable conditions.
    MainWindow remains the source of truth for state judgment.
    """

    open_text_requested = Signal()
    open_wav_requested = Signal()
    run_processing_requested = Signal()
    save_requested = Signal()
    play_requested = Signal()
    stop_requested = Signal()
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.text_button = QPushButton("Load TXT")
        self.wav_button = QPushButton("Load WAV")
        self.process_button = QPushButton("Execute Processing")
        self.output_button = QPushButton("Save VMD")
        self.play_button = QPushButton("Play Preview")
        self.stop_button = QPushButton("Stop Preview")
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_out_button = QPushButton("Zoom Out")

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        layout.addWidget(self.text_button, 0, 0)
        layout.addWidget(self.wav_button, 0, 1)
        layout.addWidget(self.process_button, 0, 2)
        layout.addWidget(self.output_button, 0, 3)
        layout.addWidget(self.play_button, 1, 0)
        layout.addWidget(self.stop_button, 1, 1)
        layout.addWidget(self.zoom_in_button, 1, 2)
        layout.addWidget(self.zoom_out_button, 1, 3)

        self.setLayout(layout)
        self._connect_button_signals()

    def _connect_button_signals(self) -> None:
        self.text_button.clicked.connect(self.open_text_requested.emit)
        self.wav_button.clicked.connect(self.open_wav_requested.emit)
        self.process_button.clicked.connect(self.run_processing_requested.emit)
        self.output_button.clicked.connect(self.save_requested.emit)
        self.play_button.clicked.connect(self.play_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.zoom_in_button.clicked.connect(self.zoom_in_requested.emit)
        self.zoom_out_button.clicked.connect(self.zoom_out_requested.emit)

    def button_map(self) -> dict[str, QPushButton]:
        return {
            "text": self.text_button,
            "wav": self.wav_button,
            "run": self.process_button,
            "save": self.output_button,
            "play": self.play_button,
            "stop": self.stop_button,
            "zoom_in": self.zoom_in_button,
            "zoom_out": self.zoom_out_button,
        }

    def set_button_enabled_states(self, states: Mapping[str, bool]) -> None:
        buttons = self.button_map()
        for name, enabled in states.items():
            button = buttons.get(name)
            if button is None:
                continue
            button.setEnabled(bool(enabled))

    def set_button_states(self, states: Mapping[str, bool]) -> None:
        """Backward-compatible alias for state reflection."""
        self.set_button_enabled_states(states)
