import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox

from core import VowelTimingPlan
from gui.main_window import MainWindow


class MainWindowProcessingResponsivenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()
        self.window.selected_text_path = "input.txt"
        self.window.selected_text_content = "あ"
        self.window.selected_wav_path = "input.wav"
        self.window.selected_vowel_content = "あ"
        self.window.selected_wav_analysis = SimpleNamespace(has_speech=True)

    def tearDown(self) -> None:
        self.window.close()

    def test_run_processing_starts_worker_and_keeps_busy_state(self) -> None:
        with patch.object(self.window, "_start_processing_worker") as mocked_start_worker:
            self.window._run_processing()

        mocked_start_worker.assert_called_once()
        self.assertTrue(self.window._is_processing)
        self.assertEqual(
            self.window.status_panel.status_text(),
            self.window._status_text("PROCESSING"),
        )
        self.assertFalse(self.window.process_button.isEnabled())

    def test_processing_worker_success_applies_timing_plan_and_ends_session(self) -> None:
        timing_plan = VowelTimingPlan(
            vowels=["あ"],
            timeline=[],
            anchors=[],
            source="provided",
            observations=[],
        )

        self.window._begin_processing_session()
        self.window._processing_worker = object()  # type: ignore[assignment]
        self.window._processing_worker_thread = object()  # type: ignore[assignment]

        with (
            patch.object(self.window.wav_waveform_view, "set_morph_events") as mocked_set_events,
            patch.object(
                self.window, "_update_preview_from_current_timing_plan"
            ) as mocked_update_preview,
            patch.object(self.window, "_set_ready_status") as mocked_ready_status,
            patch.object(self.window, "_play_analysis_completion_sound"),
        ):
            self.window._on_processing_worker_succeeded(timing_plan)

        self.assertIs(self.window.current_timing_plan, timing_plan)
        mocked_set_events.assert_called_once_with(timing_plan.timeline)
        mocked_update_preview.assert_called_once()
        mocked_ready_status.assert_called_once()
        self.assertFalse(self.window._is_processing)
        self.assertIsNone(self.window._processing_worker)
        self.assertIsNone(self.window._processing_worker_thread)

    def test_processing_worker_failure_shows_warning_and_ends_session(self) -> None:
        self.window.current_timing_plan = VowelTimingPlan(
            vowels=["あ"],
            timeline=[],
            anchors=[],
            source="provided",
            observations=[],
        )
        self.window._begin_processing_session()
        self.window._processing_worker = object()  # type: ignore[assignment]
        self.window._processing_worker_thread = object()  # type: ignore[assignment]

        with (
            patch.object(self.window, "_invalidate_current_timing_plan") as mocked_invalidate,
            patch.object(
                self.window.wav_waveform_view, "clear_morph_labels"
            ) as mocked_clear_labels,
            patch.object(QMessageBox, "warning") as mocked_warning,
            patch.object(self.window, "_play_analysis_completion_sound"),
        ):
            self.window._on_processing_worker_failed(ValueError("boom"))

        mocked_invalidate.assert_called_once()
        mocked_clear_labels.assert_called_once()
        mocked_warning.assert_called_once()
        self.assertFalse(self.window._is_processing)
        self.assertIsNone(self.window._processing_worker)
        self.assertIsNone(self.window._processing_worker_thread)


if __name__ == "__main__":
    unittest.main()
