import unittest
import wx
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import INPUT_MODE_VOICE_ONLY, UiState, StatusKey
from src.core import VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _timing_plan():
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.1,
                vowel="あ",
                duration_sec=0.1,
                start_sec=0.1,
                end_sec=0.2,
            )
        ],
        anchors=[],
        source="test",
        observations=[],
    )

class TestWXMS14B2State(unittest.TestCase):
    """
    [MS14-B2] UI State and Action Check.
    """
    @classmethod
    def setUpClass(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)
        cls.frame = MainFrame(None)
        cls.controller = AppController(cls.frame)
        cls.frame.set_controller(cls.controller)

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, cls.frame, owns_app=cls.owns_app)
        cls.frame = None
        cls.controller = None

    def setUp(self):
        self.frame: MainFrame = self.__class__.frame
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
        state.selected_text_content = "あいうえお"
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        state.mark_ready_for_analysis()
        self.frame.update_action_states()

        self.assertTrue(self.frame.btn_process.IsEnabled())
        self.assertFalse(self.frame.btn_save_vmd.IsEnabled())

    def test_ms14_b2_busy_lock(self):
        state = self.frame.ui_state
        state.selected_text_path = "dummy.txt"
        state.selected_text_content = "あいうえお"
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0

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
        state.selected_text_content = "あいうえお"
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        
        state.mark_analysis_success(_timing_plan())
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

    def test_ms19_b6_voice_only_analysis_enables_vmd_save(self):
        state = self.frame.ui_state
        state.selected_text_path = None
        state.selected_text_content = ""
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        state.refresh_input_mode()

        self.frame.update_action_states()
        self.assertTrue(self.frame.btn_process.IsEnabled())
        plan = _timing_plan()

        state.mark_analysis_success(
            plan,
            input_mode=INPUT_MODE_VOICE_ONLY,
            analysis_text_content="あいうえお",
            analysis_text_source="whisper_transcription",
            transcription_text="あいうえお",
            transcription_source="segments",
            transcription_timing_source="segments",
        )
        self.frame.update_action_states()

        self.assertTrue(state.analysis_result_valid)
        self.assertTrue(self.frame.btn_save_vmd.IsEnabled())

if __name__ == "__main__":
    unittest.main()
