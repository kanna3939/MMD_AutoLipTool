from pathlib import Path

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
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
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

        layout = QVBoxLayout()

        self.text_button = QPushButton("TEXT\u8aad\u307f\u8fbc\u307f")
        self.wav_button = QPushButton("WAV\u8aad\u307f\u8fbc\u307f")
        self.output_button = QPushButton("\u51fa\u529b")

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

        self.text_button.clicked.connect(self._select_text_file)
        self.wav_button.clicked.connect(self._select_wav_file)
        self.output_button.clicked.connect(self._export_vmd)

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
        layout.addWidget(self.output_button)
        layout.addWidget(self.output_status_label)

        self.setLayout(layout)

    def _select_text_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e",
            "",
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            text_content = Path(file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.current_timing_plan = None
            self._show_warning(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="UTF-8\u306eTEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u3044\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )
            return
        except OSError as error:
            self.current_timing_plan = None
            self._show_warning(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )
            return

        self.selected_text_path = file_path
        self.selected_text_content = text_content
        self.current_timing_plan = None
        self.text_path_label.setText(f"TEXT: {Path(file_path).name}")
        try:
            self._refresh_text_processing_views()
        except TextProcessingError as error:
            self.selected_hiragana_content = ""
            self.selected_vowel_content = ""
            self.current_timing_plan = None
            self.hiragana_preview.setPlainText("(\u3072\u3089\u304c\u306a\u5909\u63db\u306b\u5931\u6557\u3057\u307e\u3057\u305f)")
            self.vowel_preview.setPlainText("(\u6bcd\u97f3\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")
            self.wav_waveform_view.clear_morph_labels()
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message=f"TEXT\u3092\u304b\u306a/\u3072\u3089\u304c\u306a\u306b\u5909\u63db\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return
        self._refresh_waveform_morph_labels()
        self._set_ready_status()

    def _select_wav_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "WAV\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e",
            "",
            "WAV Files (*.wav);;All Files (*)",
        )
        if not file_path:
            return

        try:
            wav_info = analyze_wav_file(file_path)
        except (ValueError, OSError, EOFError) as error:
            self.selected_wav_analysis = None
            self.current_timing_plan = None
            self.wav_waveform_view.clear_morph_labels()
            self.wav_waveform_view.show_placeholder("Waveform preview (load failed)")
            self._show_warning(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u30d5\u30a1\u30a4\u30eb\u3092\u89e3\u6790\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )
            return

        try:
            waveform_preview = load_waveform_preview(file_path, max_points=3000, stereo_mode="average")
        except (ValueError, OSError, EOFError) as error:
            self.selected_wav_analysis = None
            self.current_timing_plan = None
            self.wav_waveform_view.clear_morph_labels()
            self.wav_waveform_view.show_placeholder("Waveform preview (load failed)")
            self._show_warning(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u6ce2\u5f62\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )
            return

        self.selected_wav_path = file_path
        self.selected_wav_analysis = wav_info
        self.current_timing_plan = None
        self.wav_path_label.setText(f"WAV: {Path(file_path).name}")
        self.wav_info_label.setText(
            "WAV\u60c5\u5831: "
            f"\u30d5\u30a1\u30a4\u30eb\u540d={Path(file_path).name} / "
            f"\u518d\u751f\u6642\u9593={wav_info.duration_sec:.3f}s / "
            f"\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u5468\u6ce2\u6570={wav_info.sample_rate_hz}Hz / "
            f"\u767a\u8a71={wav_info.speech_start_sec:.3f}s-{wav_info.speech_end_sec:.3f}s"
        )
        self.wav_waveform_view.plot_waveform(
            waveform_preview.samples,
            waveform_preview.duration_sec,
        )
        self._refresh_waveform_morph_labels()
        self._set_ready_status()

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

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "VMD\u30d5\u30a1\u30a4\u30eb\u306e\u4fdd\u5b58\u5148\u3092\u9078\u629e",
            "",
            "VMD Files (*.vmd);;All Files (*)",
        )
        if not output_path:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u30ad\u30e3\u30f3\u30bb\u30eb")
            return

        out_path = Path(output_path)
        if out_path.suffix.lower() != ".vmd":
            out_path = out_path.with_suffix(".vmd")

        try:
            timing_plan = self._ensure_timing_plan()
            result = generate_vmd_from_text_wav(
                text_path=self.selected_text_path,
                wav_path=self.selected_wav_path,
                output_path=out_path,
                timing_plan=timing_plan,
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

    def _ensure_timing_plan(self) -> VowelTimingPlan:
        if self.current_timing_plan is not None:
            return self.current_timing_plan
        if not self.selected_text_content:
            raise ValueError("TEXT \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002")
        if not self.selected_wav_analysis or not self.selected_wav_path:
            raise ValueError("WAV \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002")
        timing_plan = build_vowel_timing_plan(
            text_content=self.selected_text_content,
            wav_path=self.selected_wav_path,
            wav_analysis=self.selected_wav_analysis,
            whisper_model_name="small",
        )
        self.current_timing_plan = timing_plan
        return timing_plan

    def _set_ready_status(self) -> None:
        if not self.current_timing_plan:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u5165\u529b\u6e96\u5099\u4e2d")
            return

        timing_source = self.current_timing_plan.source
        if timing_source.startswith("whisper_"):
            timing_label = "Whisper\u533a\u9593\u914d\u5206"
        else:
            timing_label = "\u5747\u7b49\u914d\u5206(\u30d5\u30a9\u30fc\u30eb\u30d0\u30c3\u30af)"
        self._set_output_status(
            f"\u51fa\u529b\u72b6\u614b: \u5165\u529b\u6e96\u5099\u4e2d ({timing_label} / \u533a\u9593={len(self.current_timing_plan.anchors)} / \u6bcd\u97f3={len(self.current_timing_plan.timeline)})"
        )
