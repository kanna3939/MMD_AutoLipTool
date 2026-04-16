import unittest
import wx
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import UiState, StatusKey

class TestWXMS14B2State(unittest.TestCase):
    """
    [MS14-B2] UI State and Action Check.
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
        # Reset state before each test
        self.frame.ui_state = UiState()
        self.frame.update_action_states()
        self.frame.update_status_display()

    def test_ms14_b2_state_initialization(self):
        state = self.frame.ui_state
        self.assertIsNone(state.selected_text_path)
        self.assertIsNone(state.current_timing_plan)
        self.assertFalse(state.is_busy)
        self.assertFalse(state.analysis_result_valid)
        self.assertEqual(state.status_key, StatusKey.IDLE)
        
        # Action states at init
        self.assertTrue(self.frame.btn_open_text.IsEnabled())
        self.assertTrue(self.frame.btn_open_wav.IsEnabled())
        self.assertFalse(self.frame.btn_process.IsEnabled())  # No text/wav yet
        self.assertFalse(self.frame.btn_save_vmd.IsEnabled())  # No analysis yet

    def test_ms14_b2_action_state_ready_to_analyze(self):
        state = self.frame.ui_state
        state.selected_text_path = "dummy.txt"
        state.selected_wav_path = "dummy.wav"
        state.mark_ready_for_analysis()
        self.frame.update_action_states()

        self.assertTrue(self.frame.btn_process.IsEnabled())
        self.assertFalse(self.frame.btn_save_vmd.IsEnabled())

    def test_ms14_b2_busy_lock(self):
        state = self.frame.ui_state
        state.selected_text_path = "dummy.txt"
        state.selected_wav_path = "dummy.wav"

        state.set_busy(True)
        self.frame.update_action_states()

        # Busy lock should disable main actions
        self.assertFalse(self.frame.btn_open_text.IsEnabled())
        self.assertFalse(self.frame.btn_process.IsEnabled())
        self.assertFalse(self.frame.param_panel.sc_morph_limit.IsEnabled())

        state.set_busy(False)
        self.frame.update_action_states()
        
        self.assertTrue(self.frame.btn_open_text.IsEnabled())
        self.assertTrue(self.frame.btn_process.IsEnabled())
        self.assertTrue(self.frame.param_panel.sc_morph_limit.IsEnabled())


    def test_ms14_b2_invalidation(self):
        state = self.frame.ui_state
        state.selected_text_path = "dummy.txt"
        state.selected_wav_path = "dummy.wav"
        
        state.mark_analysis_success("dummy_timing_plan")
        self.frame.update_action_states()
        
        self.assertTrue(self.frame.btn_save_vmd.IsEnabled())
        self.assertTrue(state.analysis_result_valid)
        
        # Simulate parameter change -> invalidate
        state.invalidate_analysis()
        self.frame.update_action_states()
        
        self.assertFalse(self.frame.btn_save_vmd.IsEnabled())
        self.assertFalse(state.analysis_result_valid)
        self.assertTrue(state.analysis_pending_rebuild)
        self.assertTrue(self.frame.btn_process.IsEnabled())

if __name__ == "__main__":
    unittest.main()
