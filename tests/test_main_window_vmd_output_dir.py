import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox

from core import PipelineError
from gui.main_window import MainWindow
from gui.settings_store import SettingsStore
from tests.helpers import workspace_tempdir


class MainWindowVmdOutputDirTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()
        self.window.selected_text_path = "input.txt"
        self.window.selected_wav_path = "input.wav"
        self.window.selected_vowel_content = "あ"
        self.window.current_timing_plan = SimpleNamespace(
            timeline=[],
            source="provided",
            anchors=[],
            observations=[],
        )

    def tearDown(self) -> None:
        self.window.close()

    def test_export_uses_remembered_vmd_output_dir_as_save_dialog_initial_dir(self) -> None:
        with workspace_tempdir("main_window_vmd_output_initial_dir") as tmp_dir:
            self.window.last_vmd_output_dir = str(tmp_dir)

            with patch(
                "gui.main_window.QFileDialog.getSaveFileName",
                return_value=("", ""),
            ) as mocked_dialog:
                self.window._export_vmd()

        self.assertEqual(mocked_dialog.call_args.args[2], str(tmp_dir))

    def test_successful_export_updates_and_persists_last_vmd_output_dir(self) -> None:
        with workspace_tempdir("main_window_vmd_output_success") as tmp_dir:
            settings_path = tmp_dir / "MMD_AutoLipTool.ini"
            output_dir = tmp_dir / "exports"
            output_dir.mkdir()
            output_path = output_dir / "out.vmd"
            store = SettingsStore(settings_path)
            window = MainWindow(
                startup_settings=store.load().settings,
                settings_store=store,
            )
            window.selected_text_path = "input.txt"
            window.selected_wav_path = "input.wav"
            window.selected_vowel_content = "あ"
            window.current_timing_plan = SimpleNamespace(
                timeline=[],
                source="provided",
                anchors=[],
                observations=[],
            )

            try:
                pipeline_result = SimpleNamespace(
                    output_path=output_path,
                    timing_source="provided",
                )
                with (
                    patch(
                        "gui.main_window.QFileDialog.getSaveFileName",
                        return_value=(str(output_path), ""),
                    ),
                    patch(
                        "gui.main_window.generate_vmd_from_text_wav",
                        return_value=pipeline_result,
                    ),
                    patch.object(QMessageBox, "information"),
                ):
                    window._export_vmd()

                self.assertEqual(window.last_vmd_output_dir, str(output_dir))
                self.assertEqual(
                    store.load().settings["last_vmd_output_dir"],
                    str(output_dir),
                )
            finally:
                window.close()

    def test_canceled_export_does_not_update_last_vmd_output_dir(self) -> None:
        with workspace_tempdir("main_window_vmd_output_cancel") as tmp_dir:
            self.window.last_vmd_output_dir = str(tmp_dir)

            with patch(
                "gui.main_window.QFileDialog.getSaveFileName",
                return_value=("", ""),
            ):
                self.window._export_vmd()

        self.assertEqual(self.window.last_vmd_output_dir, str(tmp_dir))

    def test_failed_export_does_not_update_last_vmd_output_dir(self) -> None:
        with workspace_tempdir("main_window_vmd_output_failure") as tmp_dir:
            remembered_dir = tmp_dir / "remembered"
            remembered_dir.mkdir()
            failed_dir = tmp_dir / "failed"
            failed_dir.mkdir()
            failed_path = failed_dir / "out.vmd"
            self.window.last_vmd_output_dir = str(remembered_dir)

            with (
                patch(
                    "gui.main_window.QFileDialog.getSaveFileName",
                    return_value=(str(failed_path), ""),
                ),
                patch(
                    "gui.main_window.generate_vmd_from_text_wav",
                    side_effect=PipelineError("boom"),
                ),
                patch.object(QMessageBox, "warning"),
            ):
                self.window._export_vmd()

        self.assertEqual(self.window.last_vmd_output_dir, str(remembered_dir))


if __name__ == "__main__":
    unittest.main()
