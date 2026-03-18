import wave
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MMD AutoLip Tool")
        self.resize(760, 560)

        self.selected_text_path: str | None = None
        self.selected_wav_path: str | None = None

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
        self.wav_info_label = QLabel(
            "WAV\u60c5\u5831: \u672a\u8aad\u307f\u8fbc\u307f"
        )
        self.wav_preview_label = QLabel(
            "\u6ce2\u5f62\u8868\u793a\u9818\u57df\uff08\u672a\u5b9f\u88c5\uff09"
        )
        self.wav_preview_label.setMinimumHeight(120)
        self.wav_preview_label.setStyleSheet("border: 1px solid #888; padding: 8px;")

        self.text_button.clicked.connect(self._select_text_file)
        self.wav_button.clicked.connect(self._select_wav_file)

        layout.addWidget(self.text_button)
        layout.addWidget(self.text_path_label)
        layout.addWidget(self.text_preview_label)
        layout.addWidget(self.text_preview)
        layout.addWidget(self.wav_button)
        layout.addWidget(self.wav_path_label)
        layout.addWidget(self.wav_info_label)
        layout.addWidget(self.wav_preview_label)
        layout.addWidget(self.output_button)

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
            QMessageBox.warning(
                self,
                "\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                "UTF-8\u306eTEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u3044\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002",
            )
            return
        except OSError as error:
            QMessageBox.warning(
                self,
                "\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                f"TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
            )
            return

        self.selected_text_path = file_path
        self.text_path_label.setText(f"TEXT: {Path(file_path).name}")
        self.text_preview.setPlainText(text_content)

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
            wav_info = self._load_wav_info(file_path)
        except (wave.Error, OSError, EOFError) as error:
            QMessageBox.warning(
                self,
                "\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                f"WAV\u30d5\u30a1\u30a4\u30eb\u3092\u89e3\u6790\u3067\u304d\u307e\u305b\u3093: {error}",
            )
            return

        self.selected_wav_path = file_path
        self.wav_path_label.setText(f"WAV: {Path(file_path).name}")
        self.wav_info_label.setText(
            "WAV\u60c5\u5831: "
            f"\u30d5\u30a1\u30a4\u30eb\u540d={Path(file_path).name} / "
            f"\u518d\u751f\u6642\u9593={wav_info['duration_sec']:.3f}s / "
            f"\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u5468\u6ce2\u6570={wav_info['sample_rate_hz']}Hz"
        )
        self.wav_preview_label.setText(
            "\u6ce2\u5f62\u8868\u793a\u9818\u57df\uff08\u672a\u5b9f\u88c5\uff09\n"
            f"\u30b5\u30f3\u30d7\u30eb\u6570: {wav_info['frame_count']} / "
            f"\u30c1\u30e3\u30f3\u30cd\u30eb\u6570: {wav_info['channel_count']}"
        )

    def _load_wav_info(self, file_path: str) -> dict[str, float | int]:
        with wave.open(file_path, "rb") as wav_file:
            sample_rate_hz = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            channel_count = wav_file.getnchannels()
            duration_sec = frame_count / sample_rate_hz if sample_rate_hz else 0.0

        return {
            "sample_rate_hz": sample_rate_hz,
            "frame_count": frame_count,
            "channel_count": channel_count,
            "duration_sec": duration_sec,
        }
