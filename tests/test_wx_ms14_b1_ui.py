import unittest
import wx
import sys
import os
from pathlib import Path
from unittest.mock import patch

# パス追加: srcフォルダをモジュール検索パスに含む
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame
from tests.helpers import destroy_wx_app, get_or_create_wx_app

class TestWXMS14B1UI(unittest.TestCase):
    """
    [MS14-B1] UI 骨格拡充 の確認。
    - サブパネルの存在
    - 情報パネル/プレースホルダ/パラメータ の確保
    - Disabled ポリシーの維持
    - ヘルパーの存在とクラッシュ耐性
    """
    @classmethod
    def setUpClass(cls):
        # UI描画を防ぐため、Falseを指定してwx.Appを手動初期化
        # Splashの遅延CallLaterはこのUI骨格テストの責務外なので、
        # teardown後にnative callbackが残らないよう生成時だけ止める。
        with patch("gui_wx.app.get_resource_path", return_value=Path("missing_splash.png")):
            cls.app, cls.owns_app = get_or_create_wx_app(AutoLipToolApp, False)

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, owns_app=cls.owns_app)

    def test_ms14_b1_widget_existence(self):
        frame: MainFrame = self.app.frame
        self.assertIsNotNone(frame.info_panel)
        self.assertIsNotNone(frame.placeholder_container)
        self.assertIsNotNone(frame.param_panel)

        # パラメータのアクセス可否
        self.assertTrue(hasattr(frame.param_panel, 'sc_morph_limit'))
        self.assertTrue(hasattr(frame.param_panel, 'sc_hold_frames'))
        self.assertTrue(hasattr(frame.param_panel, 'sc_softness_frames'))

    def test_ms14_b1_disabled_policy(self):
        """ [MS14-B2] により主要アクションは状態依存になったため、常時無効化を保証するのは再生系のみ """
        frame: MainFrame = self.app.frame
        self.assertFalse(frame.btn_play.IsEnabled())
        self.assertFalse(frame.btn_stop.IsEnabled())

    def test_ms14_b1_view_helpers(self):
        """ [MS14-B1] Setter/Helperの存在と動作(クラッシュしないこと) """
        frame: MainFrame = self.app.frame
        
        # 情報パネル系のヘルパー
        try:
            frame.set_text_path("C:/fake/path.txt")
            frame.set_wav_path("D:/fake/audio.wav")
            frame.set_text_preview("こんにちは")
            frame.set_hiragana_preview("こんにちは")
            frame.set_vowel_preview("お・ん・い・い・あ")
            frame.set_wav_info("44100Hz 16bit Stereo")
            
            frame.set_waveform_placeholder_text("Waveform Update")
            frame.set_preview_placeholder_text("Preview Update")
        except Exception as e:
            self.fail(f"View Helper setting text properties failed: {e}")

        # パラメータ系のヘルパー
        try:
            original_val = frame.get_morph_upper_limit()
            frame.set_morph_upper_limit(0.8)
            self.assertAlmostEqual(frame.get_morph_upper_limit(), 0.8)
            frame.set_morph_upper_limit(original_val)

            original_hold = frame.get_closing_hold_frames()
            frame.set_closing_hold_frames(10)
            self.assertEqual(frame.get_closing_hold_frames(), 10)
            frame.set_closing_hold_frames(original_hold)

            original_soft = frame.get_closing_softness_frames()
            frame.set_closing_softness_frames(5)
            self.assertEqual(frame.get_closing_softness_frames(), 5)
            frame.set_closing_softness_frames(original_soft)
        except Exception as e:
            self.fail(f"View Helper for parameters failed: {e}")

if __name__ == "__main__":
    unittest.main()
