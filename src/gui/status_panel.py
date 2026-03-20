from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class StatusPanel(QFrame):
    """Display-only status bar container."""

    def __init__(self, initial_text: str = "") -> None:
        super().__init__()

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setFixedHeight(36)

        self._status_label = QLabel(initial_text)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self._status_label)
        self.setLayout(layout)

    def set_status_text(self, text: str) -> None:
        self._status_label.setText(text)

    def clear_status_text(self) -> None:
        self._status_label.setText("")

    def status_text(self) -> str:
        return self._status_label.text()
