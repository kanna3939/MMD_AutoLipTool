import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow


class MainWindowVersionInfoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    def test_show_version_info_uses_shared_app_version_source(self) -> None:
        with (
            patch("gui.main_window.resolve_app_version", return_value="0.3.7.1") as mocked_app_version,
            patch("gui.main_window.resolve_installed_version", side_effect=["1.0.0", "2.0.0"]),
            patch.object(QMessageBox, "information") as mocked_information,
        ):
            self.window._show_version_info()

        mocked_app_version.assert_called_once()
        message = mocked_information.call_args.args[2]
        self.assertIn("0.3.7.1", message)
        self.assertIn("1.0.0", message)
        self.assertIn("2.0.0", message)


if __name__ == "__main__":
    unittest.main()
