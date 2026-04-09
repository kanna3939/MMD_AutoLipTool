import unittest
import wx
import sys
import os

# パス追加: srcフォルダをモジュール検索パスに含む
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame
from gui_wx.app_controller import AppController

class TestMS13Integration(unittest.TestCase):
    """
    [MS13-B6] wx GUI 最小基盤の構造的無矛盾テスト(Light Integration Check)
    起動から初期化、イベントのルーティング先が安全に結合しているかを検証します。
    """
    @classmethod
    def setUpClass(cls):
        # UI描画を防ぐため、Falseを指定してwx.Appを手動初期化
        cls.app = AutoLipToolApp(False)

    @classmethod
    def tearDownClass(cls):
        # 破棄
        if cls.app.frame:
            cls.app.frame.Destroy()
        wx.CallAfter(cls.app.ExitMainLoop)
        cls.app.MainLoop()

    def test_boot_path_integration(self):
        """ B1-B5が統合されたアプリ起動が成功しているか """
        self.assertIsInstance(self.app.frame, MainFrame)
        self.assertIsInstance(self.app.controller, AppController)

    def test_ui_structure_exists(self):
        """ B2/B3の3分割UIが形成されているか """
        frame = self.app.frame
        self.assertIsNotNone(frame.top_panel)
        self.assertIsNotNone(frame.center_panel)
        self.assertIsNotNone(frame.bottom_panel)
        
        # Disabled items preservation
        self.assertFalse(frame.btn_process.IsEnabled())
        self.assertFalse(frame.mi_settings.IsEnabled())

    def test_settings_load_fallback_exists(self):
        """ B4の適用処理メソッドが存在し、クラッシュしないか """
        # fallback用の空辞書でも通るか
        try:
            self.app.frame.apply_settings({})
        except Exception as e:
            self.fail(f"apply_settings failed with exception: {e}")

    def test_future_hook_routing(self):
        """ B5のControllerとWorkerStubが接続されているか """
        self.assertIsNotNone(self.app.frame.controller)
        self.assertIsNotNone(self.app.controller.worker_hooks)
        
        # Method signature checks (Stub calling)
        try:
            self.app.controller.request_run_analysis()
            msg = self.app.frame.get_status_text()
            self.assertIn("解析実行要求 (Stub)", msg)
        except Exception as e:
            self.fail(f"Stub routing failed: {e}")

if __name__ == "__main__":
    unittest.main()
