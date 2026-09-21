import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow
from gui.preview_transform import empty_preview_data
from tests.helpers import workspace_tempdir


class DummyTimelinePoint:
    def __init__(
        self,
        *,
        vowel: str = "あ",
        time_sec: float = 0.2,
        duration_sec: float = 0.1,
        start_sec: float = 0.15,
        end_sec: float = 0.25,
        peak_value: float = 0.5,
        value: float = 0.5,
    ) -> None:
        self.vowel = vowel
        self.time_sec = time_sec
        self.duration_sec = duration_sec
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.peak_value = peak_value
        self.value = value


class MainWindowClosingSoftnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    def test_closing_softness_labels_are_localized_with_unit(self) -> None:
        self.window.morph_upper_limit_row.apply_language("ja")
        self.assertEqual(self.window.lip_hold_label.text(), "開口保持")
        self.assertEqual(self.window.lip_hold_unit_label.text(), "フレーム")
        self.assertEqual(self.window.closing_softness_label.text(), "閉口スムース")
        self.assertEqual(self.window.closing_softness_unit_label.text(), "フレーム")

        self.window.morph_upper_limit_row.apply_language("en")
        self.assertEqual(self.window.lip_hold_label.text(), "Lip Hold")
        self.assertEqual(self.window.lip_hold_unit_label.text(), "Frame")
        self.assertEqual(self.window.closing_softness_label.text(), "Closing Smooth")
        self.assertEqual(self.window.closing_softness_unit_label.text(), "Frame")

    def test_lip_hold_change_updates_preview_without_reanalysis_or_invalidation(self) -> None:
        original_plan = SimpleNamespace(
            timeline=[DummyTimelinePoint()],
            source="provided",
            anchors=[],
            observations=[],
        )
        self.window.current_timing_plan = original_plan

        with (
            patch("gui.main_window.build_preview_data", return_value=empty_preview_data()) as mocked_build_preview,
            patch("gui.main_window.build_vowel_timing_plan", side_effect=AssertionError("not expected")),
        ):
            self.window.lip_hold_input.setValue(2)

        self.assertIs(self.window.current_timing_plan, original_plan)
        mocked_build_preview.assert_called_once_with(
            original_plan.timeline,
            observations=original_plan.observations,
            closing_hold_frames=2,
            closing_softness_frames=0,
        )

    def test_closing_softness_change_updates_preview_without_reanalysis_or_invalidation(self) -> None:
        original_plan = SimpleNamespace(
            timeline=[DummyTimelinePoint()],
            source="provided",
            anchors=[],
            observations=[],
        )
        self.window.current_timing_plan = original_plan

        with (
            patch("gui.main_window.build_preview_data", return_value=empty_preview_data()) as mocked_build_preview,
            patch("gui.main_window.build_vowel_timing_plan", side_effect=AssertionError("not expected")),
        ):
            self.window.closing_softness_input.setValue(3)

        self.assertIs(self.window.current_timing_plan, original_plan)
        mocked_build_preview.assert_called_once_with(
            original_plan.timeline,
            observations=original_plan.observations,
            closing_hold_frames=0,
            closing_softness_frames=3,
        )

    def test_preview_update_uses_single_current_lip_hold_accessor(self) -> None:
        self.window.current_timing_plan = SimpleNamespace(
            timeline=[DummyTimelinePoint()],
            source="provided",
            anchors=[],
            observations=[],
        )

        with (
            patch.object(self.window, "_current_closing_hold_frames", return_value=6) as mocked_hold_accessor,
            patch.object(self.window, "_current_closing_softness_frames", return_value=4) as mocked_softness_accessor,
            patch("gui.main_window.build_preview_data", return_value=empty_preview_data()) as mocked_build_preview,
        ):
            self.window._update_preview_from_current_timing_plan()

        mocked_hold_accessor.assert_called_once()
        mocked_softness_accessor.assert_called_once()
        mocked_build_preview.assert_called_once_with(
            self.window.current_timing_plan.timeline,
            observations=self.window.current_timing_plan.observations,
            closing_hold_frames=6,
            closing_softness_frames=4,
        )

    def test_preview_update_uses_single_current_closing_softness_accessor(self) -> None:
        self.window.current_timing_plan = SimpleNamespace(
            timeline=[DummyTimelinePoint()],
            source="provided",
            anchors=[],
            observations=[],
        )

        with (
            patch.object(self.window, "_current_closing_softness_frames", return_value=4) as mocked_accessor,
            patch("gui.main_window.build_preview_data", return_value=empty_preview_data()) as mocked_build_preview,
        ):
            self.window._update_preview_from_current_timing_plan()

        mocked_accessor.assert_called_once()
        mocked_build_preview.assert_called_once_with(
            self.window.current_timing_plan.timeline,
            observations=self.window.current_timing_plan.observations,
            closing_hold_frames=0,
            closing_softness_frames=4,
        )

    def test_export_uses_same_current_closing_shape_accessors(self) -> None:
        self.window.selected_text_path = "input.txt"
        self.window.selected_wav_path = "input.wav"
        self.window.selected_vowel_content = "あ"
        self.window.current_timing_plan = SimpleNamespace(
            timeline=[DummyTimelinePoint()],
            source="provided",
            anchors=[],
        )

        with workspace_tempdir("main_window_closing_softness") as tmp_dir:
            output_path = tmp_dir / "out.vmd"
            pipeline_result = SimpleNamespace(
                output_path=output_path,
                timing_source="provided",
            )

            with (
                patch("gui.main_window.QFileDialog.getSaveFileName", return_value=(str(output_path), "")),
                patch("gui.main_window.generate_vmd_from_text_wav", return_value=pipeline_result) as mocked_generate,
                patch.object(self.window, "_current_closing_hold_frames", return_value=8) as mocked_hold_accessor,
                patch.object(self.window, "_current_closing_softness_frames", return_value=5) as mocked_accessor,
                patch.object(QMessageBox, "information"),
            ):
                self.window._export_vmd()

        mocked_hold_accessor.assert_called_once()
        mocked_accessor.assert_called_once()
        self.assertEqual(
            mocked_generate.call_args.kwargs["closing_hold_frames"],
            8,
        )
        self.assertEqual(
            mocked_generate.call_args.kwargs["closing_softness_frames"],
            5,
        )

    def test_processing_lock_disables_closing_softness_controls(self) -> None:
        self.window._apply_action_states(
            {
                "can_open_text": True,
                "can_open_wav": True,
                "can_open_recent_text": True,
                "can_open_recent_wav": True,
                "can_adjust_morph_upper_limit": True,
                "can_adjust_lip_hold": False,
                "can_adjust_closing_softness": False,
                "can_run": True,
                "can_save": True,
                "can_play": True,
                "can_stop": True,
                "can_zoom_in": True,
                "can_zoom_out": True,
            }
        )

        self.assertFalse(self.window.lip_hold_input.isEnabled())
        self.assertFalse(
            self.window.morph_upper_limit_row.lip_hold_decrement_button.isEnabled()
        )
        self.assertFalse(
            self.window.morph_upper_limit_row.lip_hold_increment_button.isEnabled()
        )
        self.assertFalse(self.window.closing_softness_input.isEnabled())
        self.assertFalse(
            self.window.morph_upper_limit_row.closing_softness_decrement_button.isEnabled()
        )
        self.assertFalse(
            self.window.morph_upper_limit_row.closing_softness_increment_button.isEnabled()
        )


if __name__ == "__main__":
    unittest.main()
