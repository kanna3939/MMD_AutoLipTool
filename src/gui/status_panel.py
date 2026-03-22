from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from gui.i18n_strings import StatusPanelStrings


class StatusPanel(QFrame):
    """Display-oriented status bar with status and message areas."""

    def __init__(self, initial_text: str = "") -> None:
        super().__init__()
        self.setObjectName("StatusPanel")

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setFixedHeight(36)
        self._status_text = ""

        self._state_label = QLabel("")
        self._state_label.setObjectName("StatusStateLabel")
        self._state_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._state_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self._state_label.setMinimumWidth(120)

        self._message_label = QLabel("")
        self._message_label.setObjectName("StatusMessageLabel")
        self._message_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        layout.addWidget(self._state_label)
        layout.addWidget(self._message_label, 1)
        self.setLayout(layout)

        self.set_status_text(initial_text)

    def set_status_text(self, text: str) -> None:
        normalized_text = str(text)
        self._status_text = normalized_text
        state_text, message_text = self._split_status_text(normalized_text)
        self._state_label.setText(state_text)
        self._message_label.setText(message_text)

    def clear_status_text(self) -> None:
        self._status_text = ""
        self._state_label.setText("")
        self._message_label.setText("")

    def status_text(self) -> str:
        return self._status_text

    def state_text(self) -> str:
        return self._state_label.text()

    def message_text(self) -> str:
        return self._message_label.text()

    def _split_status_text(self, text: str) -> tuple[str, str]:
        normalized = text.strip()
        if not normalized:
            return ("", "")

        if normalized.startswith(StatusPanelStrings.STATUS_PREFIX):
            body = normalized.removeprefix(StatusPanelStrings.STATUS_PREFIX).strip()
            if " (" in body and body.endswith(")"):
                state_text, detail = body.split(" (", 1)
                return (state_text.strip(), detail[:-1].strip())
            return (body, "")

        return (StatusPanelStrings.FALLBACK_STATE_LABEL, normalized)
