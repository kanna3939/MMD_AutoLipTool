from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollBar,
    QSizePolicy,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gui.i18n_strings import (
    LeftInfoPanelStrings,
    MorphUpperLimitStrings,
    RightDisplayStrings,
)
from gui.preview_area import PreviewArea
from gui.waveform_view import WaveformView

_PANEL_SECTION_SPACING = 6
_PANEL_STACK_SPACING = 6
_MORPH_ROW_SPACING = 6
_NUMERIC_INPUT_DISPLAY_WIDTH = 96
_MORPH_STEP_BUTTON_WIDTH = 24


class LeftInfoPanel(QWidget):
    """Display-oriented panel for the left information area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LeftInfoPanel")

        self.text_path_label = QLabel(LeftInfoPanelStrings.LABEL_TEXT_PATH, self)
        self.wav_path_label = QLabel(LeftInfoPanelStrings.LABEL_WAV_PATH, self)
        self.text_path_label.setWordWrap(False)
        self.wav_path_label.setWordWrap(False)

        self.text_preview_label = QLabel(LeftInfoPanelStrings.LABEL_TEXT_PREVIEW, self)
        self.text_preview = QPlainTextEdit(self)
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText(LeftInfoPanelStrings.PLACEHOLDER_TEXT_PREVIEW)

        self.hiragana_preview_label = QLabel(LeftInfoPanelStrings.LABEL_HIRAGANA_PREVIEW, self)
        self.hiragana_preview = QPlainTextEdit(self)
        self.hiragana_preview.setReadOnly(True)
        self.hiragana_preview.setPlaceholderText(
            LeftInfoPanelStrings.PLACEHOLDER_HIRAGANA_PREVIEW
        )

        self.vowel_preview_label = QLabel(LeftInfoPanelStrings.LABEL_VOWEL_PREVIEW, self)
        self.vowel_preview = QPlainTextEdit(self)
        self.vowel_preview.setReadOnly(True)
        self.vowel_preview.setPlaceholderText(LeftInfoPanelStrings.PLACEHOLDER_VOWEL_PREVIEW)

        self.wav_info_label = QLabel(LeftInfoPanelStrings.LABEL_WAV_INFO, self)
        self.wav_info_label.setWordWrap(True)

        self._configure_preview_edit(self.text_preview)
        self._configure_preview_edit(self.hiragana_preview)
        self._configure_preview_edit(self.vowel_preview)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_PANEL_STACK_SPACING)
        layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_FILES,
                [
                    self.text_path_label,
                    self.wav_path_label,
                ],
            )
        )
        layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_TEXT,
                [
                    self.text_preview_label,
                    self.text_preview,
                ],
            )
        )
        layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_CONVERSION,
                [
                    self.hiragana_preview_label,
                    self.hiragana_preview,
                    self.vowel_preview_label,
                    self.vowel_preview,
                ],
            )
        )
        layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_AUDIO,
                [
                    self.wav_info_label,
                ],
            )
        )
        layout.addStretch(1)
        self.setLayout(layout)

    def _configure_preview_edit(self, widget: QPlainTextEdit) -> None:
        widget.setMinimumHeight(84)
        widget.setTabChangesFocus(True)

    def _create_section(self, title: str, widgets: list[QWidget]) -> QWidget:
        section = QWidget(self)
        section.setObjectName("InfoSection")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_PANEL_SECTION_SPACING)
        layout.addWidget(self._create_section_header(title))
        for widget in widgets:
            layout.addWidget(widget)
        section.setLayout(layout)
        return section

    def _create_section_header(self, title: str) -> QWidget:
        header = QWidget(self)
        header.setObjectName("SectionHeader")

        title_label = QLabel(title, header)
        title_label.setObjectName("SectionTitle")
        divider = QFrame(header)
        divider.setObjectName("SectionDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(title_label)
        layout.addWidget(divider)
        header.setLayout(layout)
        return header


class RightDisplayContainer(QWidget):
    """Display-oriented container for waveform and preview areas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RightDisplayContainer")

        self.wav_waveform_view = WaveformView()
        self.preview_area = PreviewArea()
        self.viewport_scrollbar = QScrollBar(Qt.Horizontal, self)
        self.viewport_scrollbar.setObjectName("RightViewportScrollBar")
        self.viewport_scrollbar.setEnabled(False)
        self.viewport_scrollbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.viewport_scrollbar.setMinimumHeight(20)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_PANEL_STACK_SPACING)
        layout.addWidget(
            self._create_section(
                RightDisplayStrings.SECTION_TITLE_WAVEFORM,
                self.wav_waveform_view,
                stretch=3,
            )
        )
        layout.addWidget(
            self._create_section(
                RightDisplayStrings.SECTION_TITLE_PREVIEW,
                self.preview_area,
                stretch=2,
            )
        )
        layout.addWidget(self.viewport_scrollbar)
        self.setLayout(layout)

    def _create_section(self, title: str, content_widget: QWidget, *, stretch: int) -> QWidget:
        section = QWidget(self)
        section.setObjectName("DisplaySection")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_PANEL_SECTION_SPACING)
        layout.addWidget(self._create_section_header(title))
        layout.addWidget(content_widget, stretch)
        section.setLayout(layout)
        return section

    def _create_section_header(self, title: str) -> QWidget:
        header = QWidget(self)
        header.setObjectName("SectionHeader")

        title_label = QLabel(title, header)
        title_label.setObjectName("SectionTitle")
        divider = QFrame(header)
        divider.setObjectName("SectionDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(title_label)
        layout.addWidget(divider)
        header.setLayout(layout)
        return header


class CenterContentContainer(QWidget):
    """Thin display-only container that owns the central splitter."""

    def __init__(
        self,
        left_info_panel: QWidget,
        right_display_container: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CenterContentContainer")

        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setObjectName("CenterSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(left_info_panel)
        self.splitter.addWidget(right_display_container)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)
        self.setLayout(layout)


class MorphUpperLimitRow(QWidget):
    """Thin display-only row for the morph upper limit controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MorphUpperLimitRow")

        self.label = QLabel(MorphUpperLimitStrings.LABEL, self)
        self.input = QDoubleSpinBox(self)
        self.input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.input.setRange(0.0, 10.0)
        self.input.setDecimals(4)
        self.input.setSingleStep(0.05)
        self.input.setValue(0.5)
        self.input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.input.setMinimumWidth(_NUMERIC_INPUT_DISPLAY_WIDTH)
        self.input.setMaximumWidth(_NUMERIC_INPUT_DISPLAY_WIDTH)

        self.decrement_button = QToolButton(self)
        self.decrement_button.setObjectName("MorphStepButton")
        self.decrement_button.setText("-")
        self.decrement_button.setAutoRaise(False)
        self.decrement_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.decrement_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.decrement_button.clicked.connect(self.input.stepDown)

        self.increment_button = QToolButton(self)
        self.increment_button.setObjectName("MorphStepButton")
        self.increment_button.setText("+")
        self.increment_button.setAutoRaise(False)
        self.increment_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.increment_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.increment_button.clicked.connect(self.input.stepUp)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_MORPH_ROW_SPACING)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.decrement_button)
        layout.addWidget(self.increment_button)
        layout.addStretch(1)
        self.setLayout(layout)
