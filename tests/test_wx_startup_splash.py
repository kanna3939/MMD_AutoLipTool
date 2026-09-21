import unittest
from unittest.mock import patch
import wx
from pathlib import Path

from gui_wx.app import AutoLipToolApp
from tests.helpers import destroy_wx_app

class TestWxStartupSplash(unittest.TestCase):
    def setUp(self):
        self.app = None

    def tearDown(self):
        if self.app is not None:
            destroy_wx_app(self.app)
        self.app = None

    def test_app_init_without_crashing_when_asset_missing(self):
        with patch("gui_wx.app.get_resource_path", return_value=Path("missing_splash.png")), \
             patch("gui_wx.app.MainFrame.Show"), \
             patch("gui_wx.app.wx.CallAfter"), \
             patch("gui_wx.app.time.time", side_effect=[100.0, 100.0]):
            self.app = AutoLipToolApp(False)
            self.assertTrue(True)

    def test_fast_startup_uses_call_later_for_minimum_splash_duration(self):
        fake_path = Path("assets/MMD_AutoLipTool_splash.png")
        self.assertTrue(fake_path.is_file())

        with patch("gui_wx.app.get_resource_path", return_value=fake_path), \
             patch("gui_wx.app.wx.adv.SplashScreen") as splash_class, \
             patch("gui_wx.app.MainFrame.Show") as show, \
             patch("gui_wx.app.wx.CallLater") as mock_call_later, \
             patch("gui_wx.app.wx.CallAfter"), \
             patch("gui_wx.app.time.time", side_effect=[100.0, 100.25]):
            self.app = AutoLipToolApp(False)
            splash_class.return_value.Show.assert_called_once()
            show.assert_not_called()
            mock_call_later.assert_called_once()
            delay, callback = mock_call_later.call_args.args
            self.assertEqual(delay, 1250)

            callback()
            show.assert_called_once()
            splash_class.return_value.Destroy.assert_called_once()

    def test_slow_startup_shows_main_frame_immediately_and_destroys_splash(self):
        fake_path = Path("assets/MMD_AutoLipTool_splash.png")
        self.assertTrue(fake_path.is_file())

        with patch("gui_wx.app.get_resource_path", return_value=fake_path), \
             patch("gui_wx.app.wx.adv.SplashScreen") as splash_class, \
             patch("gui_wx.app.MainFrame.Show") as show, \
             patch("gui_wx.app.wx.CallLater") as mock_call_later, \
             patch("gui_wx.app.wx.CallAfter"), \
             patch("gui_wx.app.time.time", side_effect=[200.0, 201.6]):
            self.app = AutoLipToolApp(False)

            splash_class.return_value.Show.assert_called_once()
            show.assert_called_once()
            mock_call_later.assert_not_called()
            splash_class.return_value.Destroy.assert_called_once()

if __name__ == '__main__':
    unittest.main()
