from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QScrollBar,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from gui.i18n_strings import (
    ClosingSoftnessStrings,
    LeftInfoPanelStrings,
    LipHoldStrings,
    MorphUpperLimitStrings,
    RightDisplayStrings,
)
from gui.preview_area import PreviewArea
from gui.waveform_view import WaveformView

_PANEL_SECTION_SPACING = 6
_PANEL_STACK_SPACING = 6
_MORPH_ROW_SPACING = 6
_NUMERIC_INPUT_DISPLAY_WIDTH = 96
_LIP_HOLD_INPUT_DISPLAY_WIDTH = 56
_CLOSING_SOFTNESS_INPUT_DISPLAY_WIDTH = 56
_MORPH_STEP_BUTTON_WIDTH = 24


class LeftInfoPanel(QWidget):
    """Display-oriented panel for the left information area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LeftInfoPanel")
        self._section_title_labels: dict[str, QLabel] = {}

        self.text_path_label = QLabel(LeftInfoPanelStrings.LABEL_TEXT_PATH, self)
        self.wav_path_label = QLabel(LeftInfoPanelStrings.LABEL_WAV_PATH, self)
        self.text_path_label.setWordWrap(False)
        self.wav_path_label.setWordWrap(False)
        self._apply_font9(self.text_path_label)
        self._apply_font9(self.wav_path_label)

        self.text_preview_label = QLabel(LeftInfoPanelStrings.LABEL_TEXT_PREVIEW, self)
        self._apply_font9(self.text_preview_label)
        self.text_preview = QPlainTextEdit(self)
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText(LeftInfoPanelStrings.PLACEHOLDER_TEXT_PREVIEW)

        self.hiragana_preview_label = QLabel(LeftInfoPanelStrings.LABEL_HIRAGANA_PREVIEW, self)
        self._apply_font9(self.hiragana_preview_label)
        self.hiragana_preview = QPlainTextEdit(self)
        self.hiragana_preview.setReadOnly(True)
        self.hiragana_preview.setPlaceholderText(
            LeftInfoPanelStrings.PLACEHOLDER_HIRAGANA_PREVIEW
        )

        self.vowel_preview_label = QLabel(LeftInfoPanelStrings.LABEL_VOWEL_PREVIEW, self)
        self._apply_font9(self.vowel_preview_label)
        self.vowel_preview = QPlainTextEdit(self)
        self.vowel_preview.setReadOnly(True)
        self.vowel_preview.setPlaceholderText(LeftInfoPanelStrings.PLACEHOLDER_VOWEL_PREVIEW)

        self.wav_info_label = QLabel(LeftInfoPanelStrings.LABEL_WAV_INFO, self)
        self.wav_info_label.setWordWrap(True)
        self._apply_font9(self.wav_info_label)
        self.wav_info_label.setMinimumHeight(36)

        self._configure_preview_edit(self.text_preview)
        self._configure_preview_edit(self.hiragana_preview)
        self._configure_preview_edit(self.vowel_preview)

        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(_PANEL_STACK_SPACING)
        inner_layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_FILES,
                [
                    self.text_path_label,
                    self.wav_path_label,
                ],
                section_key="files",
            )
        )
        inner_layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_TEXT,
                [
                    self.text_preview_label,
                    self.text_preview,
                ],
                section_key="text",
            )
        )
        inner_layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_CONVERSION,
                [
                    self.hiragana_preview_label,
                    self.hiragana_preview,
                    self.vowel_preview_label,
                    self.vowel_preview,
                ],
                section_key="conversion",
            )
        )
        inner_layout.addWidget(
            self._create_section(
                LeftInfoPanelStrings.SECTION_TITLE_AUDIO,
                [
                    self.wav_info_label,
                ],
                section_key="audio",
            )
        )
        inner_layout.addStretch(1)

        inner_widget = QWidget(self)
        inner_widget.setObjectName("LeftInfoInnerWidget")
        inner_widget.setLayout(inner_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(inner_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def _apply_font9(self, widget: QWidget) -> None:
        current_style = widget.styleSheet()
        widget.setStyleSheet(current_style + " font-size: 9pt;")

    def _configure_preview_edit(self, widget: QPlainTextEdit) -> None:
        self._apply_font9(widget)
        widget.setFixedHeight(80)
        widget.setTabChangesFocus(True)

    def _create_section(
        self,
        title: str,
        widgets: list[QWidget],
        *,
        section_key: str,
    ) -> QWidget:
        section = QWidget(self)
        section.setObjectName("InfoSection")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_PANEL_SECTION_SPACING)
        layout.addWidget(self._create_section_header(title, section_key))
        for widget in widgets:
            layout.addWidget(widget)
        section.setLayout(layout)
        return section

    def _create_section_header(self, title: str, key: str | None = None) -> QWidget:
        header = QWidget(self)
        header.setObjectName("SectionHeader")

        title_label = QLabel(title, header)
        title_label.setObjectName("SectionTitle")
        if key is not None:
            self._section_title_labels[key] = title_label
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

    def apply_language(self, language: str) -> None:
        strings = LeftInfoPanelStrings.for_language(language)
        self._section_title_labels["files"].setText(strings["SECTION_TITLE_FILES"])
        self._section_title_labels["text"].setText(strings["SECTION_TITLE_TEXT"])
        self._section_title_labels["conversion"].setText(strings["SECTION_TITLE_CONVERSION"])
        self._section_title_labels["audio"].setText(strings["SECTION_TITLE_AUDIO"])
        self.text_path_label.setText(strings["LABEL_TEXT_PATH"])
        self.wav_path_label.setText(strings["LABEL_WAV_PATH"])
        self.text_preview_label.setText(strings["LABEL_TEXT_PREVIEW"])
        self.hiragana_preview_label.setText(strings["LABEL_HIRAGANA_PREVIEW"])
        self.vowel_preview_label.setText(strings["LABEL_VOWEL_PREVIEW"])
        self.wav_info_label.setText(strings["LABEL_WAV_INFO"])
        self.text_preview.setPlaceholderText(strings["PLACEHOLDER_TEXT_PREVIEW"])
        self.hiragana_preview.setPlaceholderText(strings["PLACEHOLDER_HIRAGANA_PREVIEW"])
        self.vowel_preview.setPlaceholderText(strings["PLACEHOLDER_VOWEL_PREVIEW"])

    def retranslate_ui(self, language: str) -> None:
        self.apply_language(language)


class RightDisplayContainer(QWidget):
    """Display-oriented container for waveform and preview areas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RightDisplayContainer")
        self._section_title_labels: dict[str, QLabel] = {}

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
                section_key="waveform",
            )
        )
        layout.addWidget(
            self._create_section(
                RightDisplayStrings.SECTION_TITLE_PREVIEW,
                self.preview_area,
                stretch=2,
                section_key="preview",
            )
        )
        layout.addWidget(self.viewport_scrollbar)
        self.setLayout(layout)

    def _create_section(
        self,
        title: str,
        content_widget: QWidget,
        *,
        stretch: int,
        section_key: str,
    ) -> QWidget:
        section = QWidget(self)
        section.setObjectName("DisplaySection")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_PANEL_SECTION_SPACING)
        layout.addWidget(self._create_section_header(title, section_key))
        layout.addWidget(content_widget, stretch)
        section.setLayout(layout)
        return section

    def _create_section_header(self, title: str, key: str) -> QWidget:
        header = QWidget(self)
        header.setObjectName("SectionHeader")

        title_label = QLabel(title, header)
        title_label.setObjectName("SectionTitle")
        self._section_title_labels[key] = title_label
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

    def apply_language(self, language: str) -> None:
        strings = RightDisplayStrings.for_language(language)
        self._section_title_labels["waveform"].setText(strings["SECTION_TITLE_WAVEFORM"])
        self._section_title_labels["preview"].setText(strings["SECTION_TITLE_PREVIEW"])
        self.preview_area.retranslate_ui(language)

    def retranslate_ui(self, language: str) -> None:
        self.apply_language(language)


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
    """Thin display-only row for morph max, lip hold, and closing softness controls."""

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
        self.input.setToolTip(MorphUpperLimitStrings.INPUT_TOOLTIP)

        self.decrement_button = QToolButton(self)
        self.decrement_button.setObjectName("MorphStepButton")
        self.decrement_button.setText("-")
        self.decrement_button.setToolTip(MorphUpperLimitStrings.DECREMENT_TOOLTIP)
        self.decrement_button.setAutoRaise(False)
        self.decrement_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.decrement_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.decrement_button.clicked.connect(self.input.stepDown)

        self.increment_button = QToolButton(self)
        self.increment_button.setObjectName("MorphStepButton")
        self.increment_button.setText("+")
        self.increment_button.setToolTip(MorphUpperLimitStrings.INCREMENT_TOOLTIP)
        self.increment_button.setAutoRaise(False)
        self.increment_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.increment_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.increment_button.clicked.connect(self.input.stepUp)

        self.lip_hold_label = QLabel(LipHoldStrings.LABEL, self)
        self.lip_hold_input = QSpinBox(self)
        self.lip_hold_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.lip_hold_input.setRange(0, 999999)
        self.lip_hold_input.setSingleStep(1)
        self.lip_hold_input.setValue(0)
        self.lip_hold_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lip_hold_input.setMinimumWidth(_LIP_HOLD_INPUT_DISPLAY_WIDTH)
        self.lip_hold_input.setMaximumWidth(_LIP_HOLD_INPUT_DISPLAY_WIDTH)
        self.lip_hold_input.setToolTip(LipHoldStrings.INPUT_TOOLTIP)

        self.lip_hold_decrement_button = QToolButton(self)
        self.lip_hold_decrement_button.setObjectName("MorphStepButton")
        self.lip_hold_decrement_button.setText("-")
        self.lip_hold_decrement_button.setToolTip(LipHoldStrings.DECREMENT_TOOLTIP)
        self.lip_hold_decrement_button.setAutoRaise(False)
        self.lip_hold_decrement_button.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )
        self.lip_hold_decrement_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.lip_hold_decrement_button.clicked.connect(self.lip_hold_input.stepDown)

        self.lip_hold_increment_button = QToolButton(self)
        self.lip_hold_increment_button.setObjectName("MorphStepButton")
        self.lip_hold_increment_button.setText("+")
        self.lip_hold_increment_button.setToolTip(LipHoldStrings.INCREMENT_TOOLTIP)
        self.lip_hold_increment_button.setAutoRaise(False)
        self.lip_hold_increment_button.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )
        self.lip_hold_increment_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.lip_hold_increment_button.clicked.connect(self.lip_hold_input.stepUp)

        self.lip_hold_unit_label = QLabel(LipHoldStrings.UNIT, self)

        self.closing_softness_label = QLabel(ClosingSoftnessStrings.LABEL, self)
        self.closing_softness_input = QSpinBox(self)
        self.closing_softness_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.closing_softness_input.setRange(0, 999999)
        self.closing_softness_input.setSingleStep(1)
        self.closing_softness_input.setValue(0)
        self.closing_softness_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.closing_softness_input.setMinimumWidth(_CLOSING_SOFTNESS_INPUT_DISPLAY_WIDTH)
        self.closing_softness_input.setMaximumWidth(_CLOSING_SOFTNESS_INPUT_DISPLAY_WIDTH)
        self.closing_softness_input.setToolTip(ClosingSoftnessStrings.INPUT_TOOLTIP)

        self.closing_softness_decrement_button = QToolButton(self)
        self.closing_softness_decrement_button.setObjectName("MorphStepButton")
        self.closing_softness_decrement_button.setText("-")
        self.closing_softness_decrement_button.setToolTip(
            ClosingSoftnessStrings.DECREMENT_TOOLTIP
        )
        self.closing_softness_decrement_button.setAutoRaise(False)
        self.closing_softness_decrement_button.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )
        self.closing_softness_decrement_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.closing_softness_decrement_button.clicked.connect(
            self.closing_softness_input.stepDown
        )

        self.closing_softness_increment_button = QToolButton(self)
        self.closing_softness_increment_button.setObjectName("MorphStepButton")
        self.closing_softness_increment_button.setText("+")
        self.closing_softness_increment_button.setToolTip(
            ClosingSoftnessStrings.INCREMENT_TOOLTIP
        )
        self.closing_softness_increment_button.setAutoRaise(False)
        self.closing_softness_increment_button.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )
        self.closing_softness_increment_button.setFixedWidth(_MORPH_STEP_BUTTON_WIDTH)
        self.closing_softness_increment_button.clicked.connect(
            self.closing_softness_input.stepUp
        )

        self.closing_softness_unit_label = QLabel(ClosingSoftnessStrings.UNIT, self)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_MORPH_ROW_SPACING)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.decrement_button)
        layout.addWidget(self.increment_button)
        layout.addSpacing(_MORPH_ROW_SPACING * 2)
        layout.addWidget(self.lip_hold_label)
        layout.addWidget(self.lip_hold_input)
        layout.addWidget(self.lip_hold_decrement_button)
        layout.addWidget(self.lip_hold_increment_button)
        layout.addWidget(self.lip_hold_unit_label)
        layout.addSpacing(_MORPH_ROW_SPACING * 2)
        layout.addWidget(self.closing_softness_label)
        layout.addWidget(self.closing_softness_input)
        layout.addWidget(self.closing_softness_decrement_button)
        layout.addWidget(self.closing_softness_increment_button)
        layout.addWidget(self.closing_softness_unit_label)
        layout.addStretch(1)
        self.setLayout(layout)

    def apply_language(self, language: str) -> None:
        morph_strings = MorphUpperLimitStrings.for_language(language)
        self.label.setText(morph_strings["LABEL"])
        self.input.setToolTip(morph_strings["INPUT_TOOLTIP"])
        self.decrement_button.setToolTip(morph_strings["DECREMENT_TOOLTIP"])
        self.increment_button.setToolTip(morph_strings["INCREMENT_TOOLTIP"])

        lip_hold_strings = LipHoldStrings.for_language(language)
        self.lip_hold_label.setText(lip_hold_strings["LABEL"])
        self.lip_hold_input.setToolTip(lip_hold_strings["INPUT_TOOLTIP"])
        self.lip_hold_decrement_button.setToolTip(
            lip_hold_strings["DECREMENT_TOOLTIP"]
        )
        self.lip_hold_increment_button.setToolTip(
            lip_hold_strings["INCREMENT_TOOLTIP"]
        )
        self.lip_hold_unit_label.setText(lip_hold_strings["UNIT"])

        closing_softness_strings = ClosingSoftnessStrings.for_language(language)
        self.closing_softness_label.setText(closing_softness_strings["LABEL"])
        self.closing_softness_input.setToolTip(closing_softness_strings["INPUT_TOOLTIP"])
        self.closing_softness_decrement_button.setToolTip(
            closing_softness_strings["DECREMENT_TOOLTIP"]
        )
        self.closing_softness_increment_button.setToolTip(
            closing_softness_strings["INCREMENT_TOOLTIP"]
        )
        self.closing_softness_unit_label.setText(closing_softness_strings["UNIT"])

    def set_morph_controls_enabled(self, enabled: bool) -> None:
        self.input.setEnabled(enabled)
        self.decrement_button.setEnabled(enabled)
        self.increment_button.setEnabled(enabled)

    def set_lip_hold_controls_enabled(self, enabled: bool) -> None:
        self.lip_hold_input.setEnabled(enabled)
        self.lip_hold_decrement_button.setEnabled(enabled)
        self.lip_hold_increment_button.setEnabled(enabled)
        self.lip_hold_unit_label.setEnabled(enabled)

    def set_closing_softness_controls_enabled(self, enabled: bool) -> None:
        self.closing_softness_input.setEnabled(enabled)
        self.closing_softness_decrement_button.setEnabled(enabled)
        self.closing_softness_increment_button.setEnabled(enabled)
        self.closing_softness_unit_label.setEnabled(enabled)

    def retranslate_ui(self, language: str) -> None:
        self.apply_language(language)
