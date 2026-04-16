import unittest
import wx
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame

class TestWXMS14B4Analysis(unittest.TestCase):
    """
    [MS14-B4] 解析実行と Worker の非同期動作・二重防止のテスト
    """
    @classmethod
    def setUpClass(cls):
        cls.app = AutoLipToolApp(False)

    @classmethod
    def tearDownClass(cls):
        if cls.app.frame:
            cls.app.frame.Destroy()
        wx.CallAfter(cls.app.ExitMainLoop)
        cls.app.MainLoop()

    def setUp(self):
        self.frame: MainFrame = self.app.frame
        self.frame.ui_state.selected_text_content = "あいうえお"
        self.frame.ui_state.selected_wav_path = "dummy.wav"
        self.frame.ui_state.selected_wav_analysis = MagicMock()
        self.frame.ui_state.set_busy(False)
        self.frame.ui_state.invalidate_analysis()

    @patch('gui_wx.main_frame.wx.ProgressDialog')
    @patch('gui_wx.main_frame.AnalysisWorker')
    def test_run_analysis_success_state(self, mock_worker_class, mock_progress_dialog):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        
        # Action
        self.frame._run_analysis()
        
        # Verify busy state applied
        self.assertTrue(self.frame.ui_state.is_busy)
        self.assertTrue(mock_worker_instance.start.called)
        
        # Simulate worker success
        mock_plan = MagicMock()
        self.frame._on_analysis_success(mock_plan)
        
        # Verify
        self.assertFalse(self.frame.ui_state.is_busy)
        self.assertTrue(self.frame.ui_state.analysis_result_valid)
        self.assertEqual(self.frame.ui_state.current_timing_plan, mock_plan)

    @patch('gui_wx.main_frame.wx.ProgressDialog')
    @patch('gui_wx.main_frame.wx.MessageBox')
    @patch('gui_wx.main_frame.AnalysisWorker')
    def test_run_analysis_error_state(self, mock_worker_class, mock_msgbox, mock_progress_dialog):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        
        # Action
        self.frame._run_analysis()
        
        # Simulate worker error
        self.frame._on_analysis_error("Mock Exception")
        
        # Verify state
        self.assertFalse(self.frame.ui_state.is_busy)
        self.assertFalse(self.frame.ui_state.analysis_result_valid)
        self.assertIsNone(self.frame.ui_state.current_timing_plan)
        # Verify input was kept
        self.assertEqual(self.frame.ui_state.selected_text_content, "あいうえお")
        # Verify message box for error was called
        self.assertTrue(mock_msgbox.called)

    @patch('gui_wx.main_frame.wx.ProgressDialog')
    @patch('gui_wx.main_frame.AnalysisWorker')
    def test_double_start_guard(self, mock_worker_class, mock_progress_dialog):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        
        # Already busy
        self.frame.ui_state.set_busy(True)
        
        # Attempt run
        self.frame._run_analysis()
        
        # Verify worker not launched
        self.assertFalse(mock_worker_instance.start.called)

if __name__ == "__main__":
    unittest.main()
