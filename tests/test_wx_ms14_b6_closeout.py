import unittest
import wx
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame

class TestWXMS14B6Closeout(unittest.TestCase):
    """
    [MS14-B6] B5Bで追加された cancel, timeout, late callbackの動作保証(Closeout)
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
    def test_soft_cancel_discards_result(self, mock_worker_class, mock_progress_dialog):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        
        self.frame._run_analysis()
        self.assertTrue(self.frame.ui_state.is_busy)
        
        # Simulate soft cancel
        self.frame._on_analysis_cancel()
        self.assertTrue(self.frame._cancel_requested)
        
        # Simulate worker sending success
        mock_plan = MagicMock()
        self.frame._on_analysis_success(self.frame._current_job_id, mock_plan)
        
        # Verify busy ended but result is discarded
        self.assertFalse(self.frame.ui_state.is_busy)
        self.assertFalse(self.frame.ui_state.analysis_result_valid)
        self.assertIsNone(self.frame.ui_state.current_timing_plan)

    @patch('gui_wx.main_frame.wx.ProgressDialog')
    @patch('gui_wx.main_frame.AnalysisWorker')
    def test_late_callback_discard(self, mock_worker_class, mock_progress_dialog):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        
        self.frame._run_analysis()
        
        # Save old job id
        old_job_id = self.frame._current_job_id
        
        # Simulate starting a new job somehow (e.g. state reset)
        self.frame._current_job_id += 1
        
        # Simulate old job sending success
        mock_plan = MagicMock()
        self.frame._on_analysis_success(old_job_id, mock_plan)
        
        # Result should not be accepted
        self.assertFalse(self.frame.ui_state.analysis_result_valid)
        self.assertIsNone(self.frame.ui_state.current_timing_plan)

    @patch('gui_wx.main_frame.wx.ProgressDialog')
    @patch('gui_wx.main_frame.AnalysisWorker')
    def test_timeout_warning_updates_ui(self, mock_worker_class, mock_progress_dialog):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        
        self.frame._run_analysis()
        
        # Verify dialog created
        self.assertIsNotNone(self.frame._progress_dialog)
        self.frame._progress_dialog.set_warning = MagicMock()
        
        # Fire timeout warning manually (simulate dummy timer)
        self.frame._on_timeout_warning(None)
        
        # Should call set_warning on dialog
        self.frame._progress_dialog.set_warning.assert_called_once()
        self.assertTrue(self.frame.ui_state.is_busy) # still busy
        self.assertFalse(self.frame._cancel_requested)

if __name__ == "__main__":
    unittest.main()
