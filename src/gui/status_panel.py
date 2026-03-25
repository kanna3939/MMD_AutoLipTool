from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from gui.i18n_strings import SUPPORTED_LANGUAGES, StatusPanelStrings

_STATUS_PANEL_HORIZONTAL_MARGIN = 6
_STATUS_PANEL_VERTICAL_MARGIN = 4
_STATUS_PANEL_SPACING = 6


class StatusPanel(QFrame):
    """Display-oriented status bar with status and message areas."""

    def __init__(self, initial_text: str = "") -> None:
        super().__init__()
        self.setObjectName("StatusPanel")

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setFixedHeight(36)
        self._status_text = ""
        self._status_prefix = StatusPanelStrings.STATUS_PREFIX
        self._fallback_state_label = StatusPanelStrings.FALLBACK_STATE_LABEL

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
        layout.setContentsMargins(
            _STATUS_PANEL_HORIZONTAL_MARGIN,
            _STATUS_PANEL_VERTICAL_MARGIN,
            _STATUS_PANEL_HORIZONTAL_MARGIN,
            _STATUS_PANEL_VERTICAL_MARGIN,
        )
        layout.setSpacing(_STATUS_PANEL_SPACING)
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

    def apply_language(self, language: str) -> None:
        strings = StatusPanelStrings.for_language(language)
        self._status_prefix = strings["STATUS_PREFIX"]
        self._fallback_state_label = strings["FALLBACK_STATE_LABEL"]
        if self._status_text:
            self.set_status_text(self._status_text)

    def retranslate_ui(self, language: str) -> None:
        self.apply_language(language)

    def _split_status_text(self, text: str) -> tuple[str, str]:
        normalized = text.strip()
        if not normalized:
            return ("", "")

        for known_prefix in self._known_status_prefixes():
            if not normalized.startswith(known_prefix):
                continue
            body = normalized.removeprefix(known_prefix).strip()
            if " (" in body and body.endswith(")"):
                state_text, detail = body.split(" (", 1)
                return (state_text.strip(), detail[:-1].strip())
            return (body, "")

        return (self._fallback_state_label, normalized)

    def _known_status_prefixes(self) -> tuple[str, ...]:
        prefixes = [self._status_prefix]
        for language in SUPPORTED_LANGUAGES:
            candidate = StatusPanelStrings.for_language(language)["STATUS_PREFIX"]
            if candidate not in prefixes:
                prefixes.append(candidate)
        return tuple(prefixes)
