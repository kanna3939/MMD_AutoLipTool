import unittest
import wx

from gui_wx.right_pane import RightPane
from tests.helpers import destroy_wx_app, get_or_create_wx_app

class TestWxMS16B3RightPane(unittest.TestCase):
    def setUp(self):
        self.app, self.owns_app = get_or_create_wx_app(wx.App, False)
        self.frame = wx.Frame(None, title="Test Frame")

    def tearDown(self):
        destroy_wx_app(self.app, self.frame, owns_app=self.owns_app)

    def test_right_pane_initialization(self):
        """RightPaneが正常に初期化され、必要なタブが存在することを確認する"""
        pane = RightPane(self.frame)
        self.assertIsNotNone(pane)
        self.assertIsNotNone(pane.notebook)
        
        # タブの数を検証 (Info, Warning, 選択イベント, プリセット, モデルプロファイル, Whisperモデル)
        self.assertEqual(pane.notebook.GetPageCount(), 6)
        
        self.assertEqual(pane.notebook.GetPageText(0), "Info")
        self.assertEqual(pane.notebook.GetPageText(1), "Warning")
        self.assertEqual(pane.notebook.GetPageText(2), "選択イベント")
        self.assertEqual(pane.notebook.GetPageText(3), "プリセット")
        self.assertEqual(pane.notebook.GetPageText(4), "モデルプロファイル")
        self.assertEqual(pane.notebook.GetPageText(5), "Whisperモデル")

    def test_view_helpers(self):
        """各タブの View Helper の動作を確認する"""
        pane = RightPane(self.frame)
        
        # Info
        pane.set_info_text("テストInfo")
        self.assertEqual(pane.st_info.GetLabel(), "テストInfo")
        pane.clear_info()
        self.assertEqual(pane.st_info.GetLabel(), "")
        self.assertEqual(pane.get_playback_context_text(), "")

        # Warning
        pane.set_warnings(["警告1", "警告2"])
        self.assertIn("警告1", pane.get_warning_text())
        self.assertIn("警告2", pane.get_warning_text())
        pane.clear_warnings()
        self.assertEqual(pane.get_warning_text(), "現在の診断はありません。")

        # 選択イベント
        pane.set_selected_event_summary("イベント選択済")
        self.assertEqual(pane.st_selected_event.GetLabel(), "イベント選択済")
        pane.clear_selected_event()
        self.assertEqual(pane.st_selected_event.GetLabel(), "選択中のイベントはありません。")

        # プリセット
        pane.set_preset_summary("プリセット1")
        self.assertEqual(pane.st_preset.GetLabel(), "プリセット1")
        pane.clear_preset_summary()
        self.assertIn("後続マイルストーン", pane.st_preset.GetLabel())

        # モデルプロファイル
        pane.set_model_profile_summary("プロファイル1")
        self.assertEqual(pane.st_model_profile.GetLabel(), "プロファイル1")
        pane.clear_model_profile_summary()
        self.assertIn("後続マイルストーン", pane.st_model_profile.GetLabel())

    def test_show_selected_event_tab_resolves_page_without_emitting_event(self):
        pane = RightPane(self.frame)
        extra_page = wx.Panel(pane.notebook)
        pane.notebook.InsertPage(0, extra_page, "追加")
        pane.notebook.ChangeSelection(
            pane.notebook.FindPage(pane.panel_info)
        )
        page_changes = []
        pane.notebook.Bind(
            wx.EVT_NOTEBOOK_PAGE_CHANGED,
            lambda event: page_changes.append(event.GetSelection()),
        )

        pane.show_selected_event_tab()

        selected_page = pane.notebook.FindPage(pane.panel_selected_event)
        self.assertNotEqual(selected_page, 2)
        self.assertEqual(pane.notebook.GetSelection(), selected_page)
        self.assertEqual(page_changes, [])

        pane.show_selected_event_tab()
        self.assertEqual(pane.notebook.GetSelection(), selected_page)
        self.assertEqual(page_changes, [])

if __name__ == '__main__':
    unittest.main()
