from __future__ import annotations

from collections.abc import Mapping
from math import floor

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractButton,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gui.i18n_strings import OperationPanelStrings


class OperationPanel(QWidget):
    """Display-oriented operation panel with grouped buttons."""

    open_text_requested = Signal()
    open_wav_requested = Signal()
    run_processing_requested = Signal()
    save_requested = Signal()
    play_requested = Signal()
    stop_requested = Signal()
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()

    _FILE_GROUP = ("text", "wav")
    _PROCESS_GROUP = ("run", "save")
    _PLAYBACK_GROUP = ("play", "stop", "zoom_in", "zoom_out")
    _GROUP_ORDER = (_FILE_GROUP, _PROCESS_GROUP, _PLAYBACK_GROUP)

    _BUTTON_SPECS = {
        "text": {
            "text": OperationPanelStrings.BUTTON_TEXTS["text"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["text"],
            "icon": QStyle.StandardPixmap.SP_DialogOpenButton,
        },
        "wav": {
            "text": OperationPanelStrings.BUTTON_TEXTS["wav"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["wav"],
            "icon": QStyle.StandardPixmap.SP_MediaVolume,
        },
        "run": {
            "text": OperationPanelStrings.BUTTON_TEXTS["run"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["run"],
            "icon": QStyle.StandardPixmap.SP_MediaPlay,
        },
        "save": {
            "text": OperationPanelStrings.BUTTON_TEXTS["save"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["save"],
            "icon": QStyle.StandardPixmap.SP_DialogSaveButton,
        },
        "play": {
            "text": OperationPanelStrings.BUTTON_TEXTS["play"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["play"],
            "icon": QStyle.StandardPixmap.SP_MediaPlay,
        },
        "stop": {
            "text": OperationPanelStrings.BUTTON_TEXTS["stop"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["stop"],
            "icon": QStyle.StandardPixmap.SP_MediaStop,
        },
        "zoom_in": {
            "text": OperationPanelStrings.BUTTON_TEXTS["zoom_in"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["zoom_in"],
            "icon": QStyle.StandardPixmap.SP_ArrowUp,
        },
        "zoom_out": {
            "text": OperationPanelStrings.BUTTON_TEXTS["zoom_out"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["zoom_out"],
            "icon": QStyle.StandardPixmap.SP_ArrowDown,
        },
    }

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("OperationPanel")
        self._current_columns: int | None = None
        self._relayout_pending = False

        self._group_containers: list[QWidget] = []
        self._group_layout = QGridLayout()
        self._group_layout.setContentsMargins(0, 0, 0, 0)
        self._group_layout.setHorizontalSpacing(12)
        self._group_layout.setVerticalSpacing(12)

        self.text_button = self._create_button("text")
        self.wav_button = self._create_button("wav")
        self.process_button = self._create_button("run")
        self.output_button = self._create_button("save")
        self.play_button = self._create_button("play")
        self.stop_button = self._create_button("stop")
        self.zoom_in_button = self._create_button("zoom_in")
        self.zoom_out_button = self._create_button("zoom_out")

        self._group_containers = [
            self._create_group_container(button_names) for button_names in self._GROUP_ORDER
        ]

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addLayout(self._group_layout)
        self.setLayout(root_layout)

        self._connect_button_signals()
        self._relayout_groups_if_needed(force=True)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._relayout_pending:
            return
        self._relayout_pending = True
        QTimer.singleShot(0, self._relayout_groups_if_needed)

    def _create_button(self, name: str) -> QToolButton:
        spec = self._BUTTON_SPECS[name]
        button = QToolButton(self)
        button.setObjectName("OperationButton")
        button.setText(spec["text"])
        button.setToolTip(spec["tooltip"])
        button.setIcon(self._resolve_icon(spec["icon"]))
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setAutoRaise(False)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setMinimumSize(88, 64)
        return button

    def _resolve_icon(self, standard_pixmap: QStyle.StandardPixmap):
        # Standard icon lookup is centralized so assets-based replacement can be added later.
        return self.style().standardIcon(standard_pixmap)

    def _create_group_container(self, button_names: tuple[str, ...]) -> QWidget:
        container = QWidget(self)
        container.setObjectName("OperationGroup")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for button_name in button_names:
            layout.addWidget(self.button_map()[button_name])
        container.setLayout(layout)
        return container

    def _calculate_columns(self) -> int:
        available_width = max(self.contentsRect().width(), 0)
        if available_width <= 0:
            return 1

        group_widths = [container.sizeHint().width() for container in self._group_containers]
        widest_group = max(group_widths, default=1)
        horizontal_gap = self._group_layout.horizontalSpacing()
        return max(
            1,
            min(
                len(self._group_containers),
                floor((available_width + horizontal_gap) / max(widest_group + horizontal_gap, 1)),
            ),
        )

    def _relayout_groups_if_needed(self, force: bool = False) -> None:
        self._relayout_pending = False
        columns = self._calculate_columns()
        if not force and columns == self._current_columns:
            return
        self._current_columns = columns
        self._relayout_groups(columns)

    def _relayout_groups(self, columns: int) -> None:
        while self._group_layout.count():
            item = self._group_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()

        for index, container in enumerate(self._group_containers):
            row = index // columns
            column = index % columns
            self._group_layout.addWidget(container, row, column)
            container.show()

        for column in range(columns):
            self._group_layout.setColumnStretch(column, 1)

    def _connect_button_signals(self) -> None:
        self.text_button.clicked.connect(self.open_text_requested.emit)
        self.wav_button.clicked.connect(self.open_wav_requested.emit)
        self.process_button.clicked.connect(self.run_processing_requested.emit)
        self.output_button.clicked.connect(self.save_requested.emit)
        self.play_button.clicked.connect(self.play_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.zoom_in_button.clicked.connect(self.zoom_in_requested.emit)
        self.zoom_out_button.clicked.connect(self.zoom_out_requested.emit)

    def button_map(self) -> dict[str, QAbstractButton]:
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
