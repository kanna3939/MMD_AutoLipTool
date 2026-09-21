import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import wx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.analysis_worker import AnalysisWorkerResult
from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import INPUT_MODE_VOICE_ONLY, UiState
from src.core import SpeechTimingAnchor, VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _timing_plan() -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.1,
                vowel="あ",
                duration_sec=0.1,
                start_sec=0.05,
                end_sec=0.15,
            )
        ],
        anchors=[SpeechTimingAnchor(start_sec=0.05, end_sec=0.15, text="あ")],
        source="whisper_segments",
        observations=[],
    )


class MS19B4VoiceOnlyGuiStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)
        cls.frame = MainFrame(None)
        cls.controller = AppController(cls.frame)
        cls.frame.set_controller(cls.controller)
        cls.app.controller = cls.controller

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, cls.frame, owns_app=cls.owns_app)
        cls.frame = None
        cls.controller = None

    def setUp(self):
        self.frame: MainFrame = self.__class__.frame
        self.frame.ui_state = UiState()
        self.frame._analysis_info_in_progress = False
        self.frame.update_action_states()
        self.frame.update_status_display()

    def test_voice_only_audio_input_enables_analysis_button(self):
        state = self.frame.ui_state
        state.selected_text_path = None
        state.selected_text_content = ""
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0

        self.frame.update_action_states()

        self.assertEqual(state.input_mode, INPUT_MODE_VOICE_ONLY)
        self.assertTrue(self.frame.btn_process.IsEnabled())

    def test_voice_only_analysis_result_enables_vmd_save(self):
        state = self.frame.ui_state
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
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
        self.assertTrue(self.frame.mi_vmd_save.IsEnabled())

    def test_voice_only_save_request_writes_vmd_from_timing_plan(self):
        state = self.frame.ui_state
        state.selected_text_path = None
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
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
        self.frame.show_vmd_save_dialog_and_get_path = MagicMock(return_value="out.vmd")

        with (
            patch("gui_wx.app_controller.generate_vmd_from_text_wav") as mock_generate_text,
            patch("gui_wx.app_controller.generate_vmd_from_timing_plan") as mock_generate_plan,
        ):
            self.app.controller.request_save_vmd()

        self.frame.show_vmd_save_dialog_and_get_path.assert_called_once()
        mock_generate_text.assert_not_called()
        mock_generate_plan.assert_called_once()
        self.assertEqual(mock_generate_plan.call_args.kwargs["wav_path"], "dummy.wav")
        self.assertEqual(mock_generate_plan.call_args.kwargs["output_path"], "out.vmd")
        self.assertIs(mock_generate_plan.call_args.kwargs["timing_plan"], plan)

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_run_analysis_voice_only_starts_worker_in_voice_only_mode(
        self,
        mock_worker_class,
        mock_progress_dialog,
    ):
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance
        state = self.frame.ui_state
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0

        with patch.object(
            self.controller,
            "build_active_whisper_model_request",
            return_value=MagicMock(),
        ):
            self.frame._run_analysis()

        self.assertTrue(state.is_busy)
        self.assertEqual(mock_worker_class.call_args.kwargs["input_mode"], INPUT_MODE_VOICE_ONLY)
        self.assertTrue(mock_worker_instance.start.called)

    def test_voice_only_analysis_success_updates_transcription_state(self):
        state = self.frame.ui_state
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        self.frame._current_job_id = 19
        self.frame._active_analysis_job_id = 19
        self.frame._analysis_parameter_snapshot = (
            self.frame._capture_analysis_parameters()
        )
        plan = _timing_plan()
        result = AnalysisWorkerResult(
            timing_plan=plan,
            input_mode=INPUT_MODE_VOICE_ONLY,
            analysis_text_content="あいう",
            analysis_text_source="whisper_transcription",
            transcription_text="あいう",
            transcription_source="segments",
            transcription_timing_source="segments",
        )

        self.frame._on_analysis_success(19, result)

        self.assertFalse(state.is_busy)
        self.assertTrue(state.analysis_result_valid)
        self.assertIs(state.current_timing_plan, plan)
        self.assertEqual(state.transcription_text, "あいう")
        self.assertEqual(state.analysis_text_content, "あいう")
        self.assertEqual(state.input_mode, INPUT_MODE_VOICE_ONLY)
        self.frame.update_action_states()
        self.assertTrue(self.frame.btn_save_vmd.IsEnabled())


if __name__ == "__main__":
    unittest.main()
