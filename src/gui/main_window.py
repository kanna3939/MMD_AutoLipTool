import os
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

from PySide6.QtCore import Qt
from core import (
    PipelineError,
    TextProcessingError,
    VowelTimingPlan,
    WavAnalysisResult,
    analyze_wav_file,
    build_vowel_timing_plan,
    generate_vmd_from_text_wav,
    hiragana_to_vowel_string,
    load_waveform_preview,
    text_to_hiragana,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from gui.waveform_view import WaveformView


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MMD AutoLip Tool")
        self.resize(760, 560)

        self.selected_text_path: str | None = None
        self.selected_wav_path: str | None = None
        self.selected_text_content: str = ""
        self.selected_hiragana_content: str = ""
        self.selected_vowel_content: str = ""
        self.selected_wav_analysis: WavAnalysisResult | None = None
        self.current_timing_plan: VowelTimingPlan | None = None
        self.last_text_dialog_dir: str | None = None
        self.last_wav_dialog_dir: str | None = None
        self._is_processing = False
        self._processing_dialog: QProgressDialog | None = None
        self._recent_file_limit = 10
        self.recent_text_files: list[str] = []
        self.recent_wav_files: list[str] = []

        layout = QVBoxLayout()
        self.menu_bar = self._build_menu_bar()
        layout.setMenuBar(self.menu_bar)

        self.text_button = QPushButton("TEXT\u8aad\u307f\u8fbc\u307f")
        self.wav_button = QPushButton("WAV\u8aad\u307f\u8fbc\u307f")
        self.process_button = QPushButton("\u51e6\u7406\u5b9f\u884c")
        self.output_button = QPushButton("\u51fa\u529b")
        self.morph_upper_limit_label = QLabel("\u30e2\u30fc\u30d5\u4e0a\u9650\u5024")
        self.morph_upper_limit_input = QDoubleSpinBox()
        self.morph_upper_limit_input.setRange(0.0, 10.0)
        self.morph_upper_limit_input.setDecimals(4)
        self.morph_upper_limit_input.setSingleStep(0.05)
        self.morph_upper_limit_input.setValue(0.5)

        self.text_path_label = QLabel("TEXT: \u672a\u9078\u629e")
        self.wav_path_label = QLabel("WAV: \u672a\u9078\u629e")
        self.text_preview_label = QLabel("TEXT\u5168\u6587\u78ba\u8a8d")
        self.text_preview = QPlainTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText(
            "\u3053\u3053\u306bTEXT\u30d5\u30a1\u30a4\u30eb\u306e\u5168\u6587\u304c\u8868\u793a\u3055\u308c\u307e\u3059"
        )
        self.hiragana_preview_label = QLabel("\u3072\u3089\u304c\u306a\u5909\u63db\u78ba\u8a8d")
        self.hiragana_preview = QPlainTextEdit()
        self.hiragana_preview.setReadOnly(True)
        self.hiragana_preview.setPlaceholderText(
            "\u3053\u3053\u306b\u3072\u3089\u304c\u306a\u5909\u63db\u5f8c\u306eTEXT\u304c\u8868\u793a\u3055\u308c\u307e\u3059"
        )
        self.vowel_preview_label = QLabel("\u6bcd\u97f3\u5909\u63db\u78ba\u8a8d")
        self.vowel_preview = QPlainTextEdit()
        self.vowel_preview.setReadOnly(True)
        self.vowel_preview.setPlaceholderText(
            "\u3053\u3053\u306b\u6bcd\u97f3\u5909\u63db\u7d50\u679c\u304c\u8868\u793a\u3055\u308c\u307e\u3059"
        )
        self.wav_info_label = QLabel(
            "WAV\u60c5\u5831: \u672a\u8aad\u307f\u8fbc\u307f"
        )
        self.wav_waveform_view = WaveformView()
        self.output_status_label = QLabel("\u51fa\u529b\u72b6\u614b: \u672a\u5b9f\u884c")
        self._sync_view_action_checks()

        self.text_button.clicked.connect(self._open_text_file)
        self.wav_button.clicked.connect(self._open_wav_file)
        self.process_button.clicked.connect(self._run_processing_requested)
        self.output_button.clicked.connect(self._save_vmd_file)
        self.morph_upper_limit_input.valueChanged.connect(self._on_morph_upper_limit_changed)

        morph_upper_limit_layout = QHBoxLayout()
        morph_upper_limit_layout.addWidget(self.morph_upper_limit_label)
        morph_upper_limit_layout.addWidget(self.morph_upper_limit_input)

        layout.addWidget(self.text_button)
        layout.addWidget(self.text_path_label)
        layout.addWidget(self.text_preview_label)
        layout.addWidget(self.text_preview)
        layout.addWidget(self.hiragana_preview_label)
        layout.addWidget(self.hiragana_preview)
        layout.addWidget(self.vowel_preview_label)
        layout.addWidget(self.vowel_preview)
        layout.addWidget(self.wav_button)
        layout.addWidget(self.wav_path_label)
        layout.addWidget(self.wav_info_label)
        layout.addWidget(self.wav_waveform_view)
        layout.addWidget(self.process_button)
        layout.addLayout(morph_upper_limit_layout)
        layout.addWidget(self.output_button)
        layout.addWidget(self.output_status_label)

        self.setLayout(layout)
        self._update_action_states()

    # Common GUI entry points (buttons and menu actions should share these).
    def _open_text_file(self) -> None:
        self._select_text_file()

    def _open_wav_file(self) -> None:
        self._select_wav_file()

    def _run_processing_requested(self) -> None:
        if self._is_processing:
            return
        self._run_processing()

    def _run_reanalysis_requested(self) -> None:
        if self._is_processing:
            return
        self._run_processing()

    def _save_vmd_file(self) -> None:
        self._export_vmd()

    def _close_application(self) -> None:
        self.close()

    def _ensure_processing_dialog(self) -> QProgressDialog:
        if self._processing_dialog is None:
            dialog = QProgressDialog("処理中です...", "", 0, 0, self)
            dialog.setWindowTitle("処理中")
            dialog.setCancelButton(None)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.setAutoClose(False)
            dialog.setAutoReset(False)
            dialog.setMinimumDuration(0)
            dialog.setValue(0)
            dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
            dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            self._processing_dialog = dialog
        return self._processing_dialog

    def _show_processing_dialog(self) -> None:
        dialog = self._ensure_processing_dialog()
        dialog.setRange(0, 0)
        dialog.setValue(0)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _hide_processing_dialog(self) -> None:
        if self._processing_dialog is None:
            return
        self._processing_dialog.hide()

    def _begin_processing_session(self) -> None:
        self._is_processing = True
        self._update_action_states()
        self._set_output_status("出力状態: 解析中")
        self._show_processing_dialog()
        QApplication.processEvents()

    def _end_processing_session(self) -> None:
        self._hide_processing_dialog()
        self._is_processing = False
        if self.output_status_label.text() == "出力状態: 解析中":
            self._set_output_status("出力状態: 失敗")
        self._update_action_states()

    def _show_version_info(self) -> None:
        pyopenjtalk_version = self._resolve_installed_version(["pyopenjtalk"])
        whisper_version = self._resolve_installed_version(["openai-whisper", "whisper"])
        QMessageBox.information(
            self,
            "バージョン情報",
            "\n".join(
                [
                    "MMD AutoLip Tool Ver 0.3.4.1",
                    f"pyopenjtalk: {pyopenjtalk_version}",
                    f"whisper: {whisper_version}",
                ]
            ),
        )

    def _resolve_installed_version(self, package_names: list[str]) -> str:
        for package_name in package_names:
            try:
                return package_version(package_name)
            except PackageNotFoundError:
                continue
        return "not installed"

    def _build_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar(self)

        file_menu = menu_bar.addMenu("File")
        self.action_open_text = QAction("TEXT\u3092\u958b\u304f", self)
        self.action_open_wav = QAction("WAV\u3092\u958b\u304f", self)
        self.action_save_vmd = QAction("VMD\u3092\u4fdd\u5b58", self)
        self.action_exit = QAction("\u7d42\u4e86", self)
        file_menu.addAction(self.action_open_text)
        file_menu.addAction(self.action_open_wav)
        self.menu_recent_text = file_menu.addMenu("\u6700\u8fd1\u4f7f\u3063\u305fTEXT")
        self.menu_recent_wav = file_menu.addMenu("\u6700\u8fd1\u4f7f\u3063\u305fWAV")
        file_menu.addSeparator()
        file_menu.addAction(self.action_save_vmd)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        run_menu = menu_bar.addMenu("Run")
        self.action_run_processing = QAction("\u51e6\u7406\u5b9f\u884c", self)
        self.action_reanalyze = QAction("\u518d\u89e3\u6790", self)
        run_menu.addAction(self.action_run_processing)
        run_menu.addAction(self.action_reanalyze)

        view_menu = menu_bar.addMenu("View")
        self.action_show_30fps_lines = QAction("30fps\u7e26\u7dda\u3092\u8868\u793a", self)
        self.action_show_vowel_labels = QAction("\u6bcd\u97f3\u30e9\u30d9\u30eb\u3092\u8868\u793a", self)
        self.action_show_event_ranges = QAction("\u30a4\u30d9\u30f3\u30c8\u533a\u9593\u3092\u8868\u793a", self)
        self.action_reset_waveform_view = QAction("\u6ce2\u5f62\u8868\u793a\u3092\u521d\u671f\u5316", self)
        self.action_show_30fps_lines.setCheckable(True)
        self.action_show_vowel_labels.setCheckable(True)
        self.action_show_event_ranges.setCheckable(True)
        view_menu.addAction(self.action_show_30fps_lines)
        view_menu.addAction(self.action_show_vowel_labels)
        view_menu.addAction(self.action_show_event_ranges)
        view_menu.addSeparator()
        view_menu.addAction(self.action_reset_waveform_view)

        help_menu = menu_bar.addMenu("Help")
        self.action_show_version = QAction("\u30d0\u30fc\u30b8\u30e7\u30f3\u60c5\u5831", self)
        help_menu.addAction(self.action_show_version)

        self._connect_menu_actions()
        self._refresh_recent_file_menus()

        return menu_bar

    def _connect_menu_actions(self) -> None:
        self.action_open_text.triggered.connect(self._open_text_file)
        self.action_open_wav.triggered.connect(self._open_wav_file)
        self.action_save_vmd.triggered.connect(self._save_vmd_file)
        self.action_exit.triggered.connect(self._close_application)
        self.action_run_processing.triggered.connect(self._run_processing_requested)
        self.action_reanalyze.triggered.connect(self._run_reanalysis_requested)
        self.action_show_30fps_lines.toggled.connect(self._on_show_30fps_lines_toggled)
        self.action_show_vowel_labels.toggled.connect(self._on_show_vowel_labels_toggled)
        self.action_show_event_ranges.toggled.connect(self._on_show_event_ranges_toggled)
        self.action_reset_waveform_view.triggered.connect(self._reset_waveform_view_options)
        self.action_show_version.triggered.connect(self._show_version_info)

    def _sync_view_action_checks(self) -> None:
        show_frame_grid, show_vowel_labels, show_event_regions = (
            self.wav_waveform_view.overlay_visibility()
        )
        for action, checked in (
            (self.action_show_30fps_lines, show_frame_grid),
            (self.action_show_vowel_labels, show_vowel_labels),
            (self.action_show_event_ranges, show_event_regions),
        ):
            previous_blocked = action.blockSignals(True)
            action.setChecked(checked)
            action.blockSignals(previous_blocked)

    def _on_show_30fps_lines_toggled(self, checked: bool) -> None:
        self.wav_waveform_view.set_show_frame_grid(checked)

    def _on_show_vowel_labels_toggled(self, checked: bool) -> None:
        self.wav_waveform_view.set_show_vowel_labels(checked)

    def _on_show_event_ranges_toggled(self, checked: bool) -> None:
        self.wav_waveform_view.set_show_event_regions(checked)

    def _reset_waveform_view_options(self) -> None:
        self.wav_waveform_view.reset_overlay_visibility()
        self._sync_view_action_checks()

    def _resolve_text_dialog_initial_dir(self) -> str:
        return self._resolve_dialog_initial_dir(self.last_text_dialog_dir)

    def _resolve_wav_dialog_initial_dir(self) -> str:
        return self._resolve_dialog_initial_dir(self.last_wav_dialog_dir)

    def _resolve_dialog_initial_dir(self, remembered_dir: str | None) -> str:
        fallback_dir = ""
        if remembered_dir is None:
            return fallback_dir

        normalized_dir = remembered_dir.strip()
        if not normalized_dir:
            return fallback_dir

        try:
            if not os.path.exists(normalized_dir):
                return fallback_dir
            if not os.path.isdir(normalized_dir):
                return fallback_dir
        except OSError:
            return fallback_dir

        return normalized_dir

    def _resolve_counterpart_path(self, primary_path: str | Path) -> Path | None:
        if isinstance(primary_path, str):
            normalized_path = primary_path.strip()
            if not normalized_path:
                return None
            base_path = Path(normalized_path)
        else:
            base_path = Path(primary_path)

        suffix = base_path.suffix.lower()
        if suffix == ".txt":
            return base_path.with_suffix(".wav")
        if suffix == ".wav":
            return base_path.with_suffix(".txt")
        return None

    def _try_autocomplete_counterpart_load(self, primary_path: str | Path) -> None:
        """Try one counterpart load after the primary load has already succeeded."""
        counterpart_path = self._resolve_counterpart_path(primary_path)
        if counterpart_path is None:
            return

        counterpart_suffix = counterpart_path.suffix.lower()
        if counterpart_suffix == ".txt":
            if self.selected_text_path:
                return
        elif counterpart_suffix == ".wav":
            if self.selected_wav_path:
                return
        else:
            return

        try:
            if not counterpart_path.exists() or counterpart_path.is_dir():
                return
        except OSError:
            return

        if counterpart_suffix == ".txt":
            if self._load_text_file(str(counterpart_path), suppress_warning=True):
                self.last_text_dialog_dir = str(counterpart_path.parent)
            return
        if counterpart_suffix == ".wav":
            if self._load_wav_file(str(counterpart_path), suppress_warning=True):
                self.last_wav_dialog_dir = str(counterpart_path.parent)

    def _select_text_file(self) -> None:
        initial_dir = self._resolve_text_dialog_initial_dir()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e",
            initial_dir,
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return
        if self._load_text_file(file_path):
            self.last_text_dialog_dir = str(Path(file_path).parent)
            self._try_autocomplete_counterpart_load(file_path)

    def _reset_text_analysis_state(self) -> None:
        self.current_timing_plan = None
        self.wav_waveform_view.clear_morph_labels()

    def _show_text_conversion_failed_previews(self) -> None:
        self.selected_hiragana_content = ""
        self.selected_vowel_content = ""
        self.hiragana_preview.setPlainText("(\u3072\u3089\u304c\u306a\u5909\u63db\u306b\u5931\u6557\u3057\u307e\u3057\u305f)")
        self.vowel_preview.setPlainText("(\u6bcd\u97f3\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")

    def _load_text_file(self, file_path: str, *, suppress_warning: bool = False) -> bool:
        def _fail_text_load(*, title: str, message: str, status: str) -> bool:
            if suppress_warning:
                return False
            self._reset_text_analysis_state()
            self._show_warning(
                title=title,
                message=message,
                status=status,
            )
            return False

        normalized_path = file_path.strip()
        if not normalized_path:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="TEXT\u30d5\u30a1\u30a4\u30eb\u306e\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )

        text_path = Path(normalized_path)
        try:
            if not text_path.exists():
                return _fail_text_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="TEXT\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
                    status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
                )
            if text_path.is_dir():
                return _fail_text_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="TEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u304f\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
                    status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
                )
        except OSError as error:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"TEXT\u30d5\u30a1\u30a4\u30eb\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )

        try:
            text_content = text_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="UTF-8\u306eTEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u3044\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )
        except OSError as error:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )

        previous_text_state = None
        if suppress_warning:
            previous_text_state = {
                "selected_text_path": self.selected_text_path,
                "selected_text_content": self.selected_text_content,
                "selected_hiragana_content": self.selected_hiragana_content,
                "selected_vowel_content": self.selected_vowel_content,
                "current_timing_plan": self.current_timing_plan,
                "text_path_label": self.text_path_label.text(),
                "text_preview": self.text_preview.toPlainText(),
                "hiragana_preview": self.hiragana_preview.toPlainText(),
                "vowel_preview": self.vowel_preview.toPlainText(),
            }

        def _restore_text_state_on_silent_failure() -> None:
            if previous_text_state is None:
                return
            self.selected_text_path = previous_text_state["selected_text_path"]
            self.selected_text_content = previous_text_state["selected_text_content"]
            self.selected_hiragana_content = previous_text_state["selected_hiragana_content"]
            self.selected_vowel_content = previous_text_state["selected_vowel_content"]
            self.current_timing_plan = previous_text_state["current_timing_plan"]
            self.text_path_label.setText(previous_text_state["text_path_label"])
            self.text_preview.setPlainText(previous_text_state["text_preview"])
            self.hiragana_preview.setPlainText(previous_text_state["hiragana_preview"])
            self.vowel_preview.setPlainText(previous_text_state["vowel_preview"])

        if not text_content:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self.selected_hiragana_content = ""
            self.selected_vowel_content = ""
            self.hiragana_preview.setPlainText("(\u3072\u3089\u304c\u306a\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")
            self.vowel_preview.setPlainText("(\u6bcd\u97f3\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message="TEXT\u30d5\u30a1\u30a4\u30eb\u304c\u7a7a\u3067\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return False

        self.selected_text_path = normalized_path
        self.selected_text_content = text_content
        self.current_timing_plan = None
        self.text_path_label.setText(f"TEXT: {text_path.name}")
        try:
            self._refresh_text_processing_views()
        except TextProcessingError as error:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self._show_text_conversion_failed_previews()
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message=f"TEXT\u3092\u304b\u306a/\u3072\u3089\u304c\u306a\u306b\u5909\u63db\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return False
        except Exception as error:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self._show_text_conversion_failed_previews()
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"TEXT\u8aad\u307f\u8fbc\u307f\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )
            return False

        if not self.selected_vowel_content:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message="\u6bcd\u97f3\u3092\u62bd\u51fa\u3067\u304d\u308b\u6587\u5b57\u304c\u3042\u308a\u307e\u305b\u3093\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return False

        self.wav_waveform_view.clear_morph_labels()
        self._set_ready_status()
        self._add_recent_text_file(normalized_path)
        return True

    def _select_wav_file(self) -> None:
        initial_dir = self._resolve_wav_dialog_initial_dir()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "WAV\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e",
            initial_dir,
            "WAV Files (*.wav);;All Files (*)",
        )
        if not file_path:
            return
        if self._load_wav_file(file_path):
            self.last_wav_dialog_dir = str(Path(file_path).parent)
            self._try_autocomplete_counterpart_load(file_path)

    def _reset_wav_load_state(self, placeholder_message: str = "Waveform preview (load failed)") -> None:
        self.selected_wav_path = None
        self.selected_wav_analysis = None
        self.current_timing_plan = None
        self.wav_path_label.setText("WAV: \u672a\u9078\u629e")
        self.wav_info_label.setText("WAV\u60c5\u5831: \u672a\u8aad\u307f\u8fbc\u307f")
        self.wav_waveform_view.clear_morph_labels()
        self.wav_waveform_view.show_placeholder(placeholder_message)

    def _validate_wav_load_result(self, wav_info: WavAnalysisResult, waveform_preview) -> str | None:
        if wav_info.sample_rate_hz <= 0:
            return "WAV\u306e\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u5468\u6ce2\u6570\u304c\u7121\u52b9\u3067\u3059\u3002"
        if wav_info.frame_count < 0:
            return "WAV\u306e\u30d5\u30ec\u30fc\u30e0\u6570\u304c\u7121\u52b9\u3067\u3059\u3002"
        if wav_info.duration_sec < 0.0:
            return "WAV\u306e\u518d\u751f\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
        if wav_info.has_speech:
            if wav_info.speech_start_sec < 0.0:
                return "WAV\u306e\u767a\u8a71\u958b\u59cb\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
            if wav_info.speech_end_sec <= wav_info.speech_start_sec:
                return "WAV\u306e\u767a\u8a71\u533a\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
            if wav_info.speech_end_sec > (wav_info.duration_sec + 1e-9):
                return "WAV\u306e\u767a\u8a71\u7d42\u4e86\u6642\u9593\u304c\u518d\u751f\u6642\u9593\u3092\u8d85\u3048\u3066\u3044\u307e\u3059\u3002"
        if waveform_preview.duration_sec < 0.0:
            return "WAV\u6ce2\u5f62\u306e\u518d\u751f\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
        if waveform_preview.duration_sec > 0.0 and not waveform_preview.samples:
            return "WAV\u6ce2\u5f62\u306e\u8868\u793a\u30c7\u30fc\u30bf\u304c\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3002"
        return None

    def _load_wav_file(self, file_path: str, *, suppress_warning: bool = False) -> bool:
        def _fail_wav_load(*, title: str, message: str, status: str) -> bool:
            if suppress_warning:
                return False
            self._reset_wav_load_state()
            self._show_warning(
                title=title,
                message=message,
                status=status,
            )
            return False

        normalized_path = file_path.strip()
        if not normalized_path:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="WAV\u30d5\u30a1\u30a4\u30eb\u306e\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        wav_path = Path(normalized_path)
        try:
            if not wav_path.exists():
                return _fail_wav_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="WAV\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
                    status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
                )
            if wav_path.is_dir():
                return _fail_wav_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="WAV\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u304f\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
                    status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
                )
        except OSError as error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u30d5\u30a1\u30a4\u30eb\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        try:
            wav_info = analyze_wav_file(normalized_path)
        except (ValueError, OSError, EOFError) as error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u30d5\u30a1\u30a4\u30eb\u3092\u89e3\u6790\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )
        except Exception as error:
            return _fail_wav_load(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"WAV\u89e3\u6790\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        try:
            waveform_preview = load_waveform_preview(
                normalized_path,
                max_points=3000,
                stereo_mode="average",
            )
        except (ValueError, OSError, EOFError) as error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u6ce2\u5f62\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )
        except Exception as error:
            return _fail_wav_load(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"WAV\u6ce2\u5f62\u53d6\u5f97\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        wav_load_error = self._validate_wav_load_result(wav_info, waveform_preview)
        if wav_load_error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u60c5\u5831\u304c\u7121\u52b9\u3067\u3059: {wav_load_error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        self.selected_wav_path = normalized_path
        self.selected_wav_analysis = wav_info
        self.current_timing_plan = None
        self.wav_path_label.setText(f"WAV: {wav_path.name}")
        self.wav_info_label.setText(
            "WAV\u60c5\u5831: "
            f"\u30d5\u30a1\u30a4\u30eb\u540d={wav_path.name} / "
            f"\u518d\u751f\u6642\u9593={wav_info.duration_sec:.3f}s / "
            f"\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u5468\u6ce2\u6570={wav_info.sample_rate_hz}Hz / "
            f"\u767a\u8a71={wav_info.speech_start_sec:.3f}s-{wav_info.speech_end_sec:.3f}s"
        )
        self.wav_waveform_view.plot_waveform(
            waveform_preview.samples,
            waveform_preview.duration_sec,
        )
        self.wav_waveform_view.clear_morph_labels()
        self._set_ready_status()
        self._add_recent_wav_file(normalized_path)
        return True

    def _open_recent_text_file(self, file_path: str) -> None:
        try:
            recent_path_error = self._validate_recent_file_path(
                file_path=file_path,
                expected_suffix=".txt",
            )
            if recent_path_error:
                self._remove_recent_text_file(file_path)
                self._show_warning(
                    title="読み込みエラー",
                    message=f"最近使ったTEXTを開けません: {recent_path_error}",
                    status="出力状態: TEXT読込失敗",
                )
                return
            if self._load_text_file(file_path):
                self.last_text_dialog_dir = str(Path(file_path).parent)
                self._try_autocomplete_counterpart_load(file_path)
                return
            self._remove_recent_text_file(file_path)
            return
        except Exception as error:
            self._remove_recent_text_file(file_path)
            self._reset_text_analysis_state()
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"最近使ったTEXTの読み込み中に予期しないエラーが発生しました: {error}",
                status="出力状態: TEXT読込失敗",
            )

    def _open_recent_wav_file(self, file_path: str) -> None:
        try:
            recent_path_error = self._validate_recent_file_path(
                file_path=file_path,
                expected_suffix=".wav",
            )
            if recent_path_error:
                self._remove_recent_wav_file(file_path)
                self._show_warning(
                    title="読み込みエラー",
                    message=f"最近使ったWAVを開けません: {recent_path_error}",
                    status="出力状態: WAV読込失敗",
                )
                return
            if self._load_wav_file(file_path):
                self.last_wav_dialog_dir = str(Path(file_path).parent)
                self._try_autocomplete_counterpart_load(file_path)
                return
            self._remove_recent_wav_file(file_path)
            return
        except Exception as error:
            self._remove_recent_wav_file(file_path)
            self._reset_wav_load_state()
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"最近使ったWAVの読み込み中に予期しないエラーが発生しました: {error}",
                status="出力状態: WAV読込失敗",
            )

    def _add_recent_text_file(self, file_path: str) -> None:
        self._remember_recent_file(self.recent_text_files, file_path)
        self._refresh_recent_text_menu()

    def _add_recent_wav_file(self, file_path: str) -> None:
        self._remember_recent_file(self.recent_wav_files, file_path)
        self._refresh_recent_wav_menu()

    def _remove_recent_text_file(self, file_path: str) -> None:
        if self._remove_recent_file(self.recent_text_files, file_path):
            self._refresh_recent_text_menu()

    def _remove_recent_wav_file(self, file_path: str) -> None:
        if self._remove_recent_file(self.recent_wav_files, file_path):
            self._refresh_recent_wav_menu()

    def _remember_recent_file(self, recent_files: list[str], file_path: str) -> None:
        normalized_target = self._normalize_recent_path(file_path)
        recent_files[:] = [
            existing_path
            for existing_path in recent_files
            if self._normalize_recent_path(existing_path) != normalized_target
        ]
        recent_files.insert(0, file_path)
        if len(recent_files) > self._recent_file_limit:
            del recent_files[self._recent_file_limit :]

    def _remove_recent_file(self, recent_files: list[str], file_path: str) -> bool:
        normalized_target = self._normalize_recent_path(file_path)
        original_size = len(recent_files)
        recent_files[:] = [
            existing_path
            for existing_path in recent_files
            if self._normalize_recent_path(existing_path) != normalized_target
        ]
        return len(recent_files) != original_size

    def _normalize_recent_path(self, file_path: str) -> str:
        return os.path.normcase(os.path.normpath(file_path))

    def _validate_recent_file_path(
        self,
        *,
        file_path: str,
        expected_suffix: str,
    ) -> str | None:
        normalized_path = file_path.strip()
        if not normalized_path:
            return "履歴パスが空です。"

        path = Path(normalized_path)
        try:
            if not path.exists():
                return "ファイルが存在しません。"
            if path.is_dir():
                return "フォルダが指定されています。"
        except OSError as error:
            return f"ファイル確認中にエラーが発生しました: {error}"

        if path.suffix.lower() != expected_suffix:
            return f"{expected_suffix} ファイルではありません。"

        return None

    def _refresh_recent_file_menus(self) -> None:
        self._refresh_recent_text_menu()
        self._refresh_recent_wav_menu()

    def _refresh_recent_text_menu(self) -> None:
        self._refresh_recent_menu(
            menu=self.menu_recent_text,
            recent_files=self.recent_text_files,
            on_selected=self._open_recent_text_file,
        )

    def _refresh_recent_wav_menu(self) -> None:
        self._refresh_recent_menu(
            menu=self.menu_recent_wav,
            recent_files=self.recent_wav_files,
            on_selected=self._open_recent_wav_file,
        )

    def _refresh_recent_menu(
        self,
        menu,
        recent_files: list[str],
        on_selected,
    ) -> None:
        menu.clear()
        if not recent_files:
            empty_action = QAction("(\u5c65\u6b74\u306a\u3057)", self)
            empty_action.setEnabled(False)
            menu.addAction(empty_action)
            menu.setEnabled(False)
            return
        menu.setEnabled(True)
        for recent_path in recent_files:
            action = QAction(recent_path, self)
            action.triggered.connect(
                lambda _checked=False, selected_path=recent_path: on_selected(selected_path)
            )
            menu.addAction(action)

    def _resolve_vmd_output_path(self, raw_output_path: str) -> Path | None:
        normalized_output_path = raw_output_path.strip()
        if not normalized_output_path:
            self._show_warning(
                title="出力エラー",
                message="VMDの保存先パスが空です。",
                status="出力状態: 失敗",
            )
            return None

        out_path = Path(normalized_output_path)
        try:
            if out_path.suffix.lower() != ".vmd":
                out_path = out_path.with_suffix(".vmd")
        except ValueError:
            self._show_warning(
                title="出力エラー",
                message="VMDの保存先パスが不正です。",
                status="出力状態: 失敗",
            )
            return None

        final_output_path = str(out_path).strip()
        if not final_output_path:
            self._show_warning(
                title="出力エラー",
                message="VMDの保存先パスが不正です。",
                status="出力状態: 失敗",
            )
            return None

        out_path = Path(final_output_path)
        try:
            if out_path.exists() and out_path.is_dir():
                self._show_warning(
                    title="出力エラー",
                    message="保存先にフォルダが指定されています。ファイル名を指定してください。",
                    status="出力状態: 失敗",
                )
                return None

            parent_dir = out_path.parent
            if not str(parent_dir).strip():
                self._show_warning(
                    title="出力エラー",
                    message="保存先フォルダが不正です。",
                    status="出力状態: 失敗",
                )
                return None
            if parent_dir.exists() and not parent_dir.is_dir():
                self._show_warning(
                    title="出力エラー",
                    message="保存先フォルダが不正です。",
                    status="出力状態: 失敗",
                )
                return None
        except OSError as error:
            self._show_warning(
                title="出力エラー",
                message=f"保存先の確認中にエラーが発生しました: {error}",
                status="出力状態: 失敗",
            )
            return None

        return out_path

    def _export_vmd(self) -> None:
        if self.selected_text_path and self.selected_wav_path and not self.selected_vowel_content:
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u304b\u3089\u6709\u52b9\u306a\u3072\u3089\u304c\u306a/\u6bcd\u97f3\u5217\u3092\u751f\u6210\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002TEXT\u3092\u898b\u76f4\u3057\u3066\u518d\u8aad\u307f\u8fbc\u307f\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return

        if not self._has_required_inputs():
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u3068WAV\u306e\u4e21\u65b9\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u5165\u529b\u4e0d\u8db3",
            )
            return

        if self.current_timing_plan is None:
            self._show_warning(
                title="\u672a\u89e3\u6790",
                message="\u51e6\u7406\u5b9f\u884c\u30dc\u30bf\u30f3\u3067\u89e3\u6790\u3057\u3066\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u89e3\u6790\u672a\u5b9f\u884c",
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "VMD\u30d5\u30a1\u30a4\u30eb\u306e\u4fdd\u5b58\u5148\u3092\u9078\u629e",
            "",
            "VMD Files (*.vmd);;All Files (*)",
        )
        if not output_path:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u30ad\u30e3\u30f3\u30bb\u30eb")
            return

        out_path = self._resolve_vmd_output_path(output_path)
        if out_path is None:
            return

        try:
            timing_plan = self._ensure_timing_plan()
            result = generate_vmd_from_text_wav(
                text_path=self.selected_text_path,
                wav_path=self.selected_wav_path,
                output_path=out_path,
                timing_plan=timing_plan,
                upper_limit=self._current_upper_limit(),
            )
            self.current_timing_plan = timing_plan
        except ValueError as error:
            self._show_warning(
                title="\u51fa\u529b\u30a8\u30e9\u30fc",
                message=f"\u6bcd\u97f3\u30bf\u30a4\u30df\u30f3\u30b0\u3092\u6c7a\u5b9a\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return
        except PipelineError as error:
            self._show_warning(
                title="\u51fa\u529b\u30a8\u30e9\u30fc",
                message=f"VMD\u306e\u51fa\u529b\u306b\u5931\u6557\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return
        except OSError as error:
            self._show_warning(
                title="\u51fa\u529b\u30a8\u30e9\u30fc",
                message=f"VMD\u4fdd\u5b58\u6642\u306b\u30d5\u30a1\u30a4\u30eb\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return
        except Exception as error:
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"\u51e6\u7406\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return

        QMessageBox.information(
            self,
            "\u51fa\u529b\u5b8c\u4e86",
            f"VMD\u3092\u51fa\u529b\u3057\u307e\u3057\u305f:\\n{result.output_path}",
        )
        timing_label = "Whisper\u6642\u9593\u30a2\u30f3\u30ab\u30fc"
        if not result.timing_source.startswith("whisper_"):
            timing_label = "\u5747\u7b49\u914d\u5206(\u30d5\u30a9\u30fc\u30eb\u30d0\u30c3\u30af)"

        self._set_output_status(
            f"\u51fa\u529b\u72b6\u614b: \u6210\u529f ({result.output_path.name} / {timing_label})"
        )

    def _run_processing(self) -> None:
        if self._is_processing:
            return
        if not self.selected_text_content:
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51e6\u7406\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u5165\u529b\u4e0d\u8db3",
            )
            return
        if not self.selected_wav_analysis or not self.selected_wav_path:
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="WAV\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51e6\u7406\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u5165\u529b\u4e0d\u8db3",
            )
            return
        if not self.selected_vowel_content:
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u304b\u3089\u6709\u52b9\u306a\u3072\u3089\u304c\u306a/\u6bcd\u97f3\u5217\u3092\u751f\u6210\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return

        self._begin_processing_session()
        try:
            self._refresh_waveform_morph_labels()
            if self.current_timing_plan is None:
                self._show_warning(
                    title="\u51e6\u7406\u30a8\u30e9\u30fc",
                    message="\u97f3\u58f0\u51e6\u7406\u306b\u5931\u6557\u3057\u307e\u3057\u305f\u3002",
                    status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
                )
                return
            self._set_ready_status()
        finally:
            self._end_processing_session()

    def _has_required_inputs(self) -> bool:
        return bool(self.selected_text_path and self.selected_wav_path)

    def _set_output_status(self, text: str) -> None:
        self.output_status_label.setText(text)

    def _refresh_text_processing_views(self) -> None:
        self.text_preview.setPlainText(self.selected_text_content)

        self.selected_hiragana_content = text_to_hiragana(self.selected_text_content)
        self.hiragana_preview.setPlainText(self.selected_hiragana_content)

        self.selected_vowel_content = hiragana_to_vowel_string(self.selected_hiragana_content)
        if self.selected_vowel_content:
            self.vowel_preview.setPlainText(self.selected_vowel_content)
        else:
            self.vowel_preview.setPlainText("(\u6bcd\u97f3\u306e\u62bd\u51fa\u7d50\u679c\u306f\u3042\u308a\u307e\u305b\u3093)")

    def _refresh_waveform_morph_labels(self) -> None:
        if (
            not self.selected_wav_analysis
            or not self.selected_text_content
            or not self.selected_wav_path
        ):
            self.current_timing_plan = None
            self.wav_waveform_view.clear_morph_labels()
            return

        if not self.selected_wav_analysis.has_speech:
            self.current_timing_plan = None
            self.wav_waveform_view.clear_morph_labels()
            return

        try:
            timing_plan = build_vowel_timing_plan(
                text_content=self.selected_text_content,
                wav_path=self.selected_wav_path,
                wav_analysis=self.selected_wav_analysis,
                whisper_model_name="small",
                upper_limit=self._current_upper_limit(),
            )
        except ValueError:
            self.current_timing_plan = None
            self.wav_waveform_view.clear_morph_labels()
            return

        self.current_timing_plan = timing_plan
        self.wav_waveform_view.set_morph_events(timing_plan.timeline)

    def _show_warning(self, title: str, message: str, status: str | None = None) -> None:
        QMessageBox.warning(self, title, message)
        if status:
            self._set_output_status(status)
        self._update_action_states()

    def _ensure_timing_plan(self) -> VowelTimingPlan:
        if self.current_timing_plan is not None:
            return self.current_timing_plan
        if not self.selected_text_content:
            raise ValueError("TEXT \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002")
        if not self.selected_wav_analysis or not self.selected_wav_path:
            raise ValueError("WAV \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002")
        raise ValueError(
            "\u89e3\u6790\u304c\u307e\u3060\u5b9f\u884c\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002"
            "\u300c\u51e6\u7406\u5b9f\u884c\u300d\u3092\u62bc\u3057\u3066\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002"
        )

    def _on_morph_upper_limit_changed(self, _: float) -> None:
        self.current_timing_plan = None
        self.wav_waveform_view.clear_morph_labels()
        self._set_ready_status()

    def _current_upper_limit(self) -> float:
        return float(self.morph_upper_limit_input.value())

    def _set_ready_status(self) -> None:
        text_loaded = bool(self.selected_text_path)
        wav_loaded = bool(self.selected_wav_path and self.selected_wav_analysis is not None)
        self._update_action_states()

        if text_loaded and wav_loaded and not self.current_timing_plan:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u89e3\u6790\u672a\u5b9f\u884c (TEXT/WAV\u8aad\u8fbc\u6e08\u307f)")
            return
        if text_loaded and not wav_loaded:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u5165\u529b\u6e96\u5099\u4e2d (TEXT\u8aad\u8fbc\u6e08\u307f / WAV\u672a\u8aad\u8fbc)")
            return
        if wav_loaded and not text_loaded:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u5165\u529b\u6e96\u5099\u4e2d (WAV\u8aad\u8fbc\u6e08\u307f / TEXT\u672a\u8aad\u8fbc)")
            return
        if not self.current_timing_plan:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u5165\u529b\u6e96\u5099\u4e2d (TEXT/WAV\u672a\u8aad\u8fbc)")
            return

        timing_source = self.current_timing_plan.source
        if timing_source.startswith("whisper_"):
            timing_label = "Whisper\u533a\u9593\u914d\u5206"
        else:
            timing_label = "\u5747\u7b49\u914d\u5206(\u30d5\u30a9\u30fc\u30eb\u30d0\u30c3\u30af)"
        self._set_output_status(
            f"\u51fa\u529b\u72b6\u614b: \u89e3\u6790\u5b9f\u884c\u6e08\u307f ({timing_label} / \u533a\u9593={len(self.current_timing_plan.anchors)} / \u6bcd\u97f3={len(self.current_timing_plan.timeline)})"
        )

    def _update_action_states(self) -> None:
        action_states = self._build_normal_action_states()
        action_states = self._apply_processing_lock_overrides(action_states)
        self._apply_action_states(action_states)

    def _build_normal_action_states(self) -> dict[str, bool]:
        has_text = bool(self.selected_text_content and self.selected_vowel_content)
        has_wav = bool(self.selected_wav_path and self.selected_wav_analysis is not None)
        has_recent_text = bool(self.recent_text_files)
        has_recent_wav = bool(self.recent_wav_files)
        can_run = has_text and has_wav
        can_save = can_run and self.current_timing_plan is not None

        return {
            "can_open_text": True,
            "can_open_wav": True,
            "can_open_recent_text": has_recent_text,
            "can_open_recent_wav": has_recent_wav,
            "can_adjust_morph_upper_limit": True,
            "can_run": can_run,
            "can_save": can_save,
        }

    def _apply_processing_lock_overrides(self, action_states: dict[str, bool]) -> dict[str, bool]:
        if not self._is_processing:
            return action_states
        locked_states = action_states.copy()
        locked_states["can_open_text"] = False
        locked_states["can_open_wav"] = False
        locked_states["can_open_recent_text"] = False
        locked_states["can_open_recent_wav"] = False
        locked_states["can_adjust_morph_upper_limit"] = False
        locked_states["can_run"] = False
        locked_states["can_save"] = False
        return locked_states

    def _apply_action_states(self, action_states: dict[str, bool]) -> None:
        can_open_text = action_states["can_open_text"]
        can_open_wav = action_states["can_open_wav"]
        can_open_recent_text = action_states["can_open_recent_text"]
        can_open_recent_wav = action_states["can_open_recent_wav"]
        can_adjust_morph_upper_limit = action_states["can_adjust_morph_upper_limit"]
        can_run = action_states["can_run"]
        can_save = action_states["can_save"]

        self.text_button.setEnabled(can_open_text)
        self.wav_button.setEnabled(can_open_wav)
        self.action_open_text.setEnabled(can_open_text)
        self.action_open_wav.setEnabled(can_open_wav)
        self.menu_recent_text.setEnabled(can_open_recent_text)
        self.menu_recent_wav.setEnabled(can_open_recent_wav)
        for action in self.menu_recent_text.actions():
            action.setEnabled(can_open_recent_text)
        for action in self.menu_recent_wav.actions():
            action.setEnabled(can_open_recent_wav)
        self.morph_upper_limit_input.setEnabled(can_adjust_morph_upper_limit)

        self.process_button.setEnabled(can_run)
        self.output_button.setEnabled(can_save)
        self.action_run_processing.setEnabled(can_run)
        self.action_reanalyze.setEnabled(can_run)
        self.action_save_vmd.setEnabled(can_save)
