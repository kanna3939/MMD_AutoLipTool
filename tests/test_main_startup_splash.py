import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

import main


class MainStartupSplashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_create_and_show_splash_returns_none_when_asset_is_missing(self) -> None:
        fake_path = Path("missing_splash.png")

        with patch("main.get_resource_path", return_value=fake_path):
            session = main._create_and_show_splash(self._app)

        self.assertIsNone(session)

    def test_create_and_show_splash_shows_splash_and_processes_events(self) -> None:
        fake_path = Path("assets/MMD_AutoLipTool_splash.png")
        fake_splash = Mock()
        fake_pixmap = Mock()
        fake_pixmap.isNull.return_value = False

        with (
            patch("main.get_resource_path", return_value=fake_path),
            patch.object(Path, "exists", return_value=True),
            patch("main.QPixmap", return_value=fake_pixmap),
            patch("main._decorate_splash_pixmap", return_value=fake_pixmap) as mocked_decorate,
            patch("main.QSplashScreen", return_value=fake_splash),
            patch("main.time.monotonic", return_value=12.5),
            patch.object(self._app, "processEvents") as mocked_process_events,
        ):
            session = main._create_and_show_splash(self._app)

        self.assertIsNotNone(session)
        self.assertEqual(session.shown_at_sec, 12.5)
        mocked_decorate.assert_called_once()
        fake_splash.show.assert_called_once()
        mocked_process_events.assert_called_once()

    def test_build_splash_version_text_uses_ver_prefix(self) -> None:
        with patch("main.resolve_app_version", return_value="0.3.8.0"):
            text = main._build_splash_version_text()

        self.assertEqual(text, "Ver. 0.3.8.0")

    def test_decorate_splash_pixmap_draws_version_text(self) -> None:
        pixmap = Mock()
        pixmap.width.return_value = 800
        pixmap.height.return_value = 220
        copied_pixmap = Mock()
        copied_pixmap.width.return_value = 800
        copied_pixmap.height.return_value = 220
        fake_painter = Mock()
        fake_painter.font.return_value = QFont()

        with (
            patch("main.QPixmap", return_value=copied_pixmap),
            patch("main.QPainter", return_value=fake_painter),
        ):
            result = main._decorate_splash_pixmap(pixmap, "Ver. 0.3.8.0")

        self.assertIs(result, copied_pixmap)
        draw_rect, draw_flags, draw_text = fake_painter.drawText.call_args.args
        self.assertEqual(draw_text, "Ver. 0.3.8.0")
        self.assertGreater(draw_rect.x(), 0)
        self.assertGreater(draw_rect.y(), 0)
        self.assertGreater(draw_rect.width(), 0)
        self.assertGreater(draw_rect.height(), 0)
        self.assertTrue(draw_flags)
        fake_painter.end.assert_called_once()

    def test_remaining_splash_display_ms_clamps_to_zero(self) -> None:
        with patch("main.time.monotonic", return_value=11.0):
            remaining = main._remaining_splash_display_ms(
                10.0,
                minimum_display_ms=350,
            )

        self.assertEqual(remaining, 0)

    def test_finish_splash_when_ready_waits_for_remaining_display_time(self) -> None:
        fake_splash = Mock()
        fake_window = Mock()
        splash_session = main._SplashDisplaySession(
            splash=fake_splash,
            shown_at_sec=10.0,
        )

        with (
            patch.object(self._app, "processEvents") as mocked_process_events,
            patch("main.time.monotonic", return_value=10.1),
            patch("main.QTimer.singleShot") as mocked_single_shot,
        ):
            main._finish_splash_when_ready(self._app, splash_session, fake_window)

        mocked_process_events.assert_called_once()
        delay_ms, callback = mocked_single_shot.call_args.args
        self.assertGreaterEqual(delay_ms, 249)
        self.assertLessEqual(delay_ms, 251)
        callback()
        fake_splash.finish.assert_called_once_with(fake_window)


if __name__ == "__main__":
    unittest.main()
