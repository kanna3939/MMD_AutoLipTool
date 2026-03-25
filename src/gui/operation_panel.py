from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractButton,
    QHBoxLayout,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gui.i18n_strings import OperationPanelStrings

_OPERATION_PANEL_ICON_SIZE = QSize(24, 24)
_OPERATION_PANEL_GROUP_SPACING = 4
_OPERATION_PANEL_LAYOUT_SPACING = 6
_OPERATION_PANEL_MARGIN = 4
_OPERATION_BUTTON_MIN_WIDTH = 96
_OPERATION_BUTTON_MAX_WIDTH = 118
_OPERATION_BUTTON_MIN_HEIGHT = 64
_OPERATION_BUTTON_TALL_HEIGHT = 74
_SINGLE_LINE_BUTTONS = {"text", "wav", "run"}
_TOOLBAR_ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons" / "toolbar"


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
    _TALL_BUTTONS = {"run", "save"}

    _BUTTON_SPECS = {
        "text": {
            "text": OperationPanelStrings.BUTTON_TEXTS["text"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["text"],
            "icon": QStyle.StandardPixmap.SP_DialogOpenButton,
            "icon_file": "textfileopen.png",
        },
        "wav": {
            "text": OperationPanelStrings.BUTTON_TEXTS["wav"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["wav"],
            "icon": QStyle.StandardPixmap.SP_MediaVolume,
            "icon_file": "wavfileopen.png",
        },
        "run": {
            "text": OperationPanelStrings.BUTTON_TEXTS["run"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["run"],
            "icon": QStyle.StandardPixmap.SP_MediaPlay,
            "icon_file": "execute.png",
        },
        "save": {
            "text": OperationPanelStrings.BUTTON_TEXTS["save"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["save"],
            "icon": QStyle.StandardPixmap.SP_DialogSaveButton,
            "icon_file": "vmdsave.png",
        },
        "play": {
            "text": OperationPanelStrings.BUTTON_TEXTS["play"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["play"],
            "icon": QStyle.StandardPixmap.SP_MediaPlay,
            "icon_file": "play.png",
        },
        "stop": {
            "text": OperationPanelStrings.BUTTON_TEXTS["stop"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["stop"],
            "icon": QStyle.StandardPixmap.SP_MediaStop,
            "icon_file": "stop.png",
        },
        "zoom_in": {
            "text": OperationPanelStrings.BUTTON_TEXTS["zoom_in"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["zoom_in"],
            "icon": QStyle.StandardPixmap.SP_ArrowUp,
            "icon_file": "zoomin.png",
        },
        "zoom_out": {
            "text": OperationPanelStrings.BUTTON_TEXTS["zoom_out"],
            "tooltip": OperationPanelStrings.BUTTON_TOOLTIPS["zoom_out"],
            "icon": QStyle.StandardPixmap.SP_ArrowDown,
            "icon_file": "zoomout.png",
        },
    }

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("OperationPanel")
        self._relayout_pending = False

        self._group_containers: list[QWidget] = []
        self._root_layout = QVBoxLayout()
        self._root_layout.setContentsMargins(
            _OPERATION_PANEL_MARGIN,
            _OPERATION_PANEL_MARGIN,
            _OPERATION_PANEL_MARGIN,
            _OPERATION_PANEL_MARGIN,
        )
        self._root_layout.setSpacing(_OPERATION_PANEL_LAYOUT_SPACING)

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

        self._first_row_widget = QWidget(self)
        self._first_row_layout = self._build_row_layout(self._first_row_widget)
        self._second_row_widget = QWidget(self)
        self._second_row_layout = self._build_row_layout(self._second_row_widget)
        self._root_layout.addWidget(self._first_row_widget)
        self._root_layout.addWidget(self._second_row_widget)
        self.setLayout(self._root_layout)

        self._connect_button_signals()
        self._relayout_groups_if_needed(force=True)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._relayout_pending:
            return
        self._relayout_pending = True
        QTimer.singleShot(0, self._relayout_groups_if_needed)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._relayout_pending:
            return
        self._relayout_pending = True
        QTimer.singleShot(0, self._relayout_groups_if_needed)

    def _create_button(self, name: str) -> QToolButton:
        spec = self._BUTTON_SPECS[name]
        button = QToolButton(self)
        button.setObjectName("OperationButton")
        button.setText(self._normalized_button_text(name, spec["text"]))
        button.setToolTip(spec["tooltip"])
        button.setIcon(self._resolve_icon(spec["icon"], spec.get("icon_file")))
        button.setIconSize(_OPERATION_PANEL_ICON_SIZE)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setAutoRaise(False)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        minimum_height = (
            _OPERATION_BUTTON_TALL_HEIGHT
            if name in self._TALL_BUTTONS
            else _OPERATION_BUTTON_MIN_HEIGHT
        )
        button.setMinimumSize(_OPERATION_BUTTON_MIN_WIDTH, minimum_height)
        button.setMaximumWidth(_OPERATION_BUTTON_MAX_WIDTH)
        if name in self._TALL_BUTTONS:
            button.setFixedHeight(_OPERATION_BUTTON_TALL_HEIGHT)
        return button

    def _resolve_icon(
        self,
        standard_pixmap: QStyle.StandardPixmap,
        icon_file_name: str | None,
    ) -> QIcon:
        if icon_file_name:
            icon_path = _TOOLBAR_ICON_DIR / icon_file_name
            if icon_path.is_file():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    return icon
        return self.style().standardIcon(standard_pixmap)

    def _create_group_container(self, button_names: tuple[str, ...]) -> QWidget:
        container = QWidget(self)
        container.setObjectName("OperationGroup")
        container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_OPERATION_PANEL_GROUP_SPACING)
        for button_name in button_names:
            layout.addWidget(self.button_map()[button_name])
        container.setLayout(layout)
        return container

    def _build_row_layout(self, row_widget: QWidget) -> QHBoxLayout:
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(_OPERATION_PANEL_LAYOUT_SPACING)
        row_widget.setLayout(row_layout)
        row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return row_layout

    def _relayout_groups_if_needed(self, force: bool = False) -> None:
        self._relayout_pending = False
        self._relayout_groups()
        self.updateGeometry()

    def _relayout_groups(self) -> None:
        self._clear_row_layout(self._first_row_layout)
        self._clear_row_layout(self._second_row_layout)

        available_width = max(self.contentsRect().width() - (_OPERATION_PANEL_MARGIN * 2), 1)
        first_row, second_row = self._build_group_rows(available_width)

        self._populate_row_layout(self._first_row_layout, first_row)
        self._populate_row_layout(self._second_row_layout, second_row)
        self._first_row_widget.setVisible(bool(first_row))
        self._second_row_widget.setVisible(bool(second_row))
        for container in first_row + second_row:
            container.show()

    def _clear_row_layout(self, row_layout: QHBoxLayout) -> None:
        while row_layout.count():
            item = row_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self)

    def _build_group_rows(self, available_width: int) -> tuple[list[QWidget], list[QWidget]]:
        rows: list[list[QWidget]] = [[], []]
        row_widths = [0, 0]
        row_index = 0

        for container in self._group_containers:
            container_width = max(container.sizeHint().width(), 1)
            spacing = _OPERATION_PANEL_LAYOUT_SPACING if rows[row_index] else 0
            next_width = row_widths[row_index] + spacing + container_width
            if rows[row_index] and next_width > available_width and row_index == 0:
                row_index = 1
                spacing = 0
                next_width = container_width
            rows[row_index].append(container)
            row_widths[row_index] = next_width

        return (rows[0], rows[1])

    def _populate_row_layout(self, row_layout: QHBoxLayout, row_groups: list[QWidget]) -> None:
        for container in row_groups:
            container.show()
            row_layout.addWidget(container, 0, Qt.AlignLeft | Qt.AlignTop)
        row_layout.addStretch(1)

    def _normalized_button_text(self, name: str, text: str) -> str:
        resolved_text = str(text)
        if name not in _SINGLE_LINE_BUTTONS:
            return resolved_text
        return resolved_text.replace("\n", "")

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

    def apply_language(self, language: str) -> None:
        button_texts = OperationPanelStrings.button_texts(language)
        button_tooltips = OperationPanelStrings.button_tooltips(language)
        for name, button in self.button_map().items():
            button.setText(self._normalized_button_text(name, button_texts[name]))
            button.setToolTip(button_tooltips[name])

    def retranslate_ui(self, language: str) -> None:
        self.apply_language(language)
