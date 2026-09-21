import sys
import unittest
from pathlib import Path
import wx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui_wx.preview_panel import PreviewPanel
from gui_wx.ui_state import UiState
from gui_wx.main_frame import MainFrame
from src.core.preview_transform import PreviewData, PreviewRow, PreviewSegment, PreviewControlPoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app

class TestWxMS16B6EventSelection(unittest.TestCase):
    def setUp(self):
        self.app, self.owns_app = get_or_create_wx_app(wx.App, False)
        self.frame = wx.Frame(None)
        
        segment1 = PreviewSegment(
            start_sec=1.0,
            end_sec=1.5,
            duration_sec=0.5,
            intensity=1.0,
            vowel="あ",
            shape_kind="trapezoid",
            control_points=(
                PreviewControlPoint(time_sec=1.0, value=0.0),
                PreviewControlPoint(time_sec=1.1, value=1.0),
                PreviewControlPoint(time_sec=1.4, value=1.0),
                PreviewControlPoint(time_sec=1.5, value=0.0),
            ),
            source_event_index=3,
            frame_range=(30, 45)
        )
        
        segment2 = PreviewSegment(
            start_sec=2.0,
            end_sec=2.5,
            duration_sec=0.5,
            intensity=0.8,
            vowel="い",
            shape_kind="trapezoid",
            control_points=(),
            source_event_index=5,
            frame_range=(60, 75)
        )
        
        rows = [
            PreviewRow(vowel="あ", segments=[segment1]),
            PreviewRow(vowel="い", segments=[segment2]),
            PreviewRow(vowel="う", segments=[]),
            PreviewRow(vowel="え", segments=[]),
            PreviewRow(vowel="お", segments=[]),
        ]
        self.sample_preview_data = PreviewData(rows=rows)

    def tearDown(self):
        destroy_wx_app(self.app, self.frame, owns_app=self.owns_app)

    def test_preview_panel_selection_methods(self):
        panel = PreviewPanel(self.frame)
        panel.set_preview_data(self.sample_preview_data, duration_sec=5.0)
        
        self.assertIsNone(panel.model.selected_source_event_index)
        self.assertIsNone(panel.get_selected_shape_summary())
        
        panel.set_selected_source_event_index(3)
        self.assertEqual(panel.model.selected_source_event_index, 3)
        
        summary = panel.get_selected_shape_summary()
        self.assertIsNotNone(summary)
        self.assertIn("Morph: あ", summary)
        self.assertIn("Event Index: 3", summary)
        self.assertIn("Shape: trapezoid", summary)
        self.assertIn("Frame: 30 - 45", summary)
        
        panel.set_selected_source_event_index(999)
        self.assertEqual(panel.model.selected_source_event_index, 999)
        self.assertIsNone(panel.get_selected_shape_summary())
        
        panel.clear_selection()
        self.assertIsNone(panel.model.selected_source_event_index)

    def test_preview_panel_data_update_clears_selection(self):
        panel = PreviewPanel(self.frame)
        panel.set_preview_data(self.sample_preview_data, duration_sec=5.0)
        panel.set_selected_source_event_index(3)
        self.assertEqual(panel.model.selected_source_event_index, 3)
        
        panel.set_preview_data(self.sample_preview_data, duration_sec=5.0)
        self.assertIsNone(panel.model.selected_source_event_index)

    def test_preview_panel_placeholder_clears_selection(self):
        panel = PreviewPanel(self.frame)
        panel.set_preview_data(self.sample_preview_data, duration_sec=5.0)
        panel.set_selected_source_event_index(3)
        
        panel.set_placeholder("Cleared")
        self.assertIsNone(panel.model.selected_source_event_index)

    def test_mainframe_selection_integration(self):
        main_frame = MainFrame(None)
        
        self.assertIsNone(main_frame.ui_state.selected_source_event_index)
        self.assertEqual(main_frame.right_pane.st_selected_event.GetLabel(), "選択中のイベントはありません。")
        
        main_frame.select_event_by_source_index(1)
        
        self.assertEqual(main_frame.ui_state.selected_source_event_index, 1)
        self.assertEqual(main_frame.placeholder_container.pnl_preview.model.selected_source_event_index, 1)
        self.assertEqual(main_frame.right_pane.st_selected_event.GetLabel(), "選択中のイベントはありません。")
        
        main_frame.clear_selected_event()
        self.assertIsNone(main_frame.ui_state.selected_source_event_index)
        self.assertIsNone(main_frame.placeholder_container.pnl_preview.model.selected_source_event_index)
        
        destroy_wx_app(self.app, main_frame, owns_app=False)

if __name__ == '__main__':
    unittest.main()
