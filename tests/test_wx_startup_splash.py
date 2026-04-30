import unittest
from unittest.mock import patch, Mock
import wx
import time
from pathlib import Path

from gui_wx.app import AutoLipToolApp

class TestWxStartupSplash(unittest.TestCase):
    def setUp(self):
        self.app = wx.App.Get()
        if not self.app:
            self.app = wx.App(False)
            
    def test_app_init_without_crashing_when_asset_missing(self):
        # 存在しないパスをモックしてクラッシュしないかテスト
        with patch("gui_wx.app.get_resource_path", return_value=Path("missing_splash.png")):
            with patch("gui_wx.app.MainFrame.Show"):
                app = AutoLipToolApp(False)
                # エラーにならずに起動できること
                self.assertTrue(True)
                
    def test_app_init_with_splash(self):
        # 実在するスプラッシュのパスをモック
        fake_path = Path("assets/MMD_AutoLipTool_splash.png")
        
        with patch("gui_wx.app.get_resource_path", return_value=fake_path), \
             patch("gui_wx.app.wx.adv.SplashScreen.Show") as mock_splash_show, \
             patch("gui_wx.app.MainFrame.Show"), \
             patch("gui_wx.app.wx.CallLater") as mock_call_later:
            
            app = AutoLipToolApp(False)
            
            if fake_path.is_file():
                # SplashScreen.Show が呼ばれたか
                mock_splash_show.assert_called_once()
                # CallLater が呼ばれたか（1500msの遅延）
                mock_call_later.assert_called_once()
                
                args, _ = mock_call_later.call_args
                delay = args[0]
                self.assertGreaterEqual(delay, 0)
                self.assertLessEqual(delay, 1500)

if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()
