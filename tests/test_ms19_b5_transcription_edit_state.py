import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import wx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.analysis_worker import AnalysisWorker
from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, INPUT_MODE_VOICE_ONLY, UiState
from src.core import (
    ModelIdentity,
    RuntimeCacheIdentity,
    SpeechTimingAnchor,
    VerifiedAnalysisModelRequest,
    VowelTimingPlan,
    WhisperModelRuntime,
    WhisperModelSession,
    WhisperTimingResult,
)
from src.core.whisper_model_loader import VerifiedWhisperCheckpoint
from src.core.whisper_models import load_whisper_model_catalog
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _timing_result(identity: ModelIdentity | None = None) -> WhisperTimingResult:
    return WhisperTimingResult(
        anchors=[SpeechTimingAnchor(start_sec=0.1, end_sec=0.4, text="あ")],
        raw_result={"segments": [{"start": 0.1, "end": 0.4, "text": "あいう"}]},
        source="segments",
        model_identity=identity,
    )


def _runtime_request() -> tuple[WhisperModelRuntime, VerifiedAnalysisModelRequest, WhisperModelSession]:
    identity = ModelIdentity(model_key="small", manifest_identity="manifest-small")
    checkpoint = VerifiedWhisperCheckpoint(
        model_key="small",
        checkpoint_path=Path("C:/models/small.pt"),
        manifest_identity="manifest-small",
        sha256="a" * 64,
        size_bytes=123,
    )
    request = VerifiedAnalysisModelRequest(
        identity=identity,
        cache_identity=RuntimeCacheIdentity(
            model_key="small",
            canonical_storage_root=str(Path("C:/models").resolve(strict=False)),
            manifest_identity="manifest-small",
        ),
        verified_checkpoint=checkpoint,
    )
    session = WhisperModelSession(
        model=MagicMock(),
        identity=identity,
        cache_identity=request.cache_identity,
        session_id="test-session",
    )
    runtime = WhisperModelRuntime(catalog=load_whisper_model_catalog(), loader=MagicMock())
    runtime.acquire = MagicMock(return_value=session)
    runtime.release = MagicMock()
    return runtime, request, session


def _timing_plan(*, with_event: bool = True) -> VowelTimingPlan:
    timeline = []
    if with_event:
        timeline.append(
            VowelTimelinePoint(
                time_sec=0.1,
                vowel="あ",
                duration_sec=0.1,
                start_sec=0.1,
                end_sec=0.2,
            )
        )
    return VowelTimingPlan(
        vowels=["あ"] if with_event else [],
        timeline=timeline,
        anchors=[],
        source="test",
        observations=[],
    )


class MS19B5TranscriptionEditGuiStateTests(unittest.TestCase):
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
        self.frame.update_action_states()
        self.frame.update_status_display()

    def _mark_voice_only_success(self):
        state = self.frame.ui_state
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        plan = _timing_plan()
        timing_result = _timing_result()
        state.mark_analysis_success(
            plan,
            input_mode=INPUT_MODE_VOICE_ONLY,
            analysis_text_content="あいう",
            analysis_text_source="whisper_transcription",
            transcription_text="あいう",
            transcription_source="segments",
            transcription_timing_source="segments",
            transcription_original_text="あいう",
            transcription_timing_result=timing_result,
        )
        self.frame._update_voice_only_text_previews("あいう")
        self.frame.update_action_states()
        return timing_result

    def test_voice_only_success_enables_transcription_edit_controls(self):
        self._mark_voice_only_success()

        self.assertTrue(self.frame.info_panel.is_text_preview_editable())
        self.assertTrue(self.frame.info_panel.btn_apply_transcription_edit.IsEnabled())
        self.assertTrue(self.frame.info_panel.btn_revert_transcription_edit.IsEnabled())

    def test_text_audio_preview_remains_readonly(self):
        state = self.frame.ui_state
        state.selected_text_path = "text.txt"
        state.selected_text_content = "あいう"
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        state.mark_analysis_success(
            _timing_plan(with_event=False),
            input_mode=INPUT_MODE_TEXT_AUDIO,
            analysis_text_content="あいう",
            analysis_text_source="text_file",
        )

        self.frame.update_action_states()

        self.assertFalse(self.frame.info_panel.is_text_preview_editable())
        self.assertFalse(self.frame.info_panel.btn_apply_transcription_edit.IsEnabled())
        self.assertFalse(self.frame.info_panel.btn_revert_transcription_edit.IsEnabled())

    def test_apply_transcription_edit_updates_state_and_invalidates_plan(self):
        timing_result = self._mark_voice_only_success()
        self.frame.info_panel.set_text_preview("あお")

        self.frame._on_transcription_apply(None)

        state = self.frame.ui_state
        self.assertEqual(state.transcription_text, "あお")
        self.assertEqual(state.analysis_text_content, "あお")
        self.assertEqual(state.analysis_text_source, "user_edited_transcription")
        self.assertTrue(state.transcription_is_edited)
        self.assertFalse(state.analysis_result_valid)
        self.assertIsNone(state.current_timing_plan)
        self.assertTrue(state.analysis_pending_rebuild)
        self.assertIs(state.transcription_timing_result, timing_result)
        self.assertEqual(self.frame.info_panel.get_text_preview(), "あお")
        self.frame.update_action_states()
        self.assertFalse(self.frame.btn_save_vmd.IsEnabled())

    def test_edited_reanalysis_success_enables_vmd_save(self):
        timing_result = self._mark_voice_only_success()
        self.frame.info_panel.set_text_preview("あお")
        self.frame._on_transcription_apply(None)
        edited_plan = _timing_plan()

        self.frame.ui_state.mark_analysis_success(
            edited_plan,
            input_mode=INPUT_MODE_VOICE_ONLY,
            analysis_text_content="あお",
            analysis_text_source="user_edited_transcription",
            transcription_text="あお",
            transcription_source="user_edited_transcription",
            transcription_timing_source="segments",
            transcription_original_text="あいう",
            transcription_is_edited=True,
            transcription_timing_result=timing_result,
        )
        self.frame.update_action_states()

        self.assertFalse(self.frame.ui_state.analysis_pending_rebuild)
        self.assertIs(self.frame.ui_state.current_timing_plan, edited_plan)
        self.assertTrue(self.frame.btn_save_vmd.IsEnabled())

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_edited_reanalysis_starts_worker_with_retained_timing(
        self,
        mock_worker_class,
        mock_progress_dialog,
    ):
        timing_result = self._mark_voice_only_success()
        self.frame.info_panel.set_text_preview("あお")
        self.frame._on_transcription_apply(None)
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        with patch.object(
            self.controller,
            "build_active_whisper_model_request",
            return_value=MagicMock(),
        ):
            self.frame._run_analysis()

        kwargs = mock_worker_class.call_args.kwargs
        self.assertEqual(kwargs["input_mode"], INPUT_MODE_VOICE_ONLY)
        self.assertEqual(kwargs["transcription_text_override"], "あお")
        self.assertIs(kwargs["retained_whisper_timing_result"], timing_result)
        self.assertTrue(kwargs["reuse_retained_timing"])
        self.assertTrue(mock_worker_instance.start.called)
        self.frame._cleanup_analysis_job()
        self.frame.ui_state.set_busy(False)


class MS19B5AnalysisWorkerTests(unittest.TestCase):
    def test_worker_reuses_retained_timing_for_edited_text(self):
        callback = MagicMock()
        error_callback = MagicMock()
        runtime, request, session = _runtime_request()
        timing_result = _timing_result(session.identity)
        timing_plan = MagicMock()
        worker = AnalysisWorker(
            job_id=8,
            callback=callback,
            error_callback=error_callback,
            phase_callback=MagicMock(),
            text_content="",
            wav_path="voice.wav",
            wav_analysis=MagicMock(),
            input_mode=INPUT_MODE_VOICE_ONLY,
            transcription_text_override="あお",
            retained_whisper_timing_result=timing_result,
            reuse_retained_timing=True,
            whisper_model_request=request,
            whisper_runtime=runtime,
        )

        with (
            patch("gui_wx.analysis_worker.wx.CallAfter", side_effect=lambda fn, *args: fn(*args)),
            patch("gui_wx.analysis_worker.recognize_audio_timing", side_effect=AssertionError("not expected")),
            patch("gui_wx.analysis_worker.build_vowel_timing_plan", return_value=timing_plan) as mock_build,
        ):
            worker.run()

        error_callback.assert_not_called()
        mock_build.assert_called_once()
        build_kwargs = mock_build.call_args.kwargs
        self.assertEqual(build_kwargs["text_content"], "あお")
        self.assertIs(build_kwargs["whisper_timing_result"], timing_result)
        job_id, result = callback.call_args.args
        self.assertEqual(job_id, 8)
        self.assertIs(result.timing_plan, timing_plan)
        self.assertEqual(result.analysis_text_source, "user_edited_transcription")
        self.assertEqual(result.transcription_text, "あお")
        self.assertEqual(result.transcription_source, "user_edited_transcription")
        self.assertIs(result.whisper_timing_result, timing_result)

    def test_worker_fails_when_reuse_requested_without_timing_result(self):
        callback = MagicMock()
        error_callback = MagicMock()
        worker = AnalysisWorker(
            job_id=9,
            callback=callback,
            error_callback=error_callback,
            phase_callback=MagicMock(),
            text_content="",
            wav_path="voice.wav",
            wav_analysis=MagicMock(),
            input_mode=INPUT_MODE_VOICE_ONLY,
            transcription_text_override="あお",
            retained_whisper_timing_result=None,
            reuse_retained_timing=True,
        )

        with patch("gui_wx.analysis_worker.wx.CallAfter", side_effect=lambda fn, *args: fn(*args)):
            worker.run()

        callback.assert_not_called()
        error_callback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
