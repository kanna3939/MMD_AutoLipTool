import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import wx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.app_controller import AppController
from gui_wx.analysis_worker import AnalysisWorker
from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import INPUT_MODE_VOICE_ONLY, UiState
from gui_wx.voice_only_errors import classify_voice_only_analysis_error
from src.core import (
    ModelIdentity,
    RuntimeCacheIdentity,
    VerifiedAnalysisModelRequest,
    VowelTimingPlan,
    WhisperModelRuntime,
    WhisperModelSession,
)
from src.core.whisper_model_loader import VerifiedWhisperCheckpoint
from src.core.whisper_models import load_whisper_model_catalog
from src.core.text_processing import TextProcessingError
from src.core.whisper_timing import WhisperTimingError
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _runtime_request() -> tuple[WhisperModelRuntime, VerifiedAnalysisModelRequest]:
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
    return runtime, request


class MS19B7VoiceOnlyErrorHandlingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)
        cls.frame = MainFrame(None)
        cls.controller = AppController(cls.frame)
        cls.frame.set_controller(cls.controller)

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, cls.frame, owns_app=cls.owns_app)

    def setUp(self):
        self.frame.ui_state = UiState()
        self.frame._current_job_id = 19
        self.frame._cancel_requested = False
        self.frame._progress_dialog = None
        self.frame._timeout_timer = None
        self.frame._worker = None

    def test_voice_only_errors_are_classified(self):
        cases = (
            (WhisperTimingError("Whisper transcription failed: missing ffmpeg"), "voice_only_whisper_failed"),
            (WhisperTimingError("Whisper returned no usable transcription text."), "voice_only_transcription_empty"),
            (WhisperTimingError("Whisper returned no usable timing anchors."), "voice_only_timing_anchor_failed"),
            (TextProcessingError("pyopenjtalk conversion failed"), "voice_only_text_conversion_failed"),
            (ValueError("No vowels extracted from TEXT."), "voice_only_vowel_empty"),
            (ValueError("編集済み書き起こしテキストが空です。"), "voice_only_edited_text_empty"),
            (ValueError("保持済みのWhisper timing resultがありません。"), "voice_only_timing_plan_invalid"),
        )

        for error, expected_category in cases:
            with self.subTest(expected_category=expected_category):
                presentation = classify_voice_only_analysis_error(error)
                self.assertEqual(presentation.category, expected_category)
                self.assertTrue(presentation.summary)
                self.assertTrue(presentation.action)

    def test_user_docs_describe_voice_only_workflow(self):
        repo_root = Path(__file__).resolve().parent.parent
        readme = (repo_root / "README.md").read_text(encoding="utf-8")
        distribution_readme = (repo_root / "readme_mmdautolip.txt").read_text(encoding="utf-8")

        for content in (readme, distribution_readme):
            self.assertIn("音声のみ入力", content)
            self.assertIn("書き起こし", content)
            self.assertIn("再解析", content)

    @patch("gui_wx.analysis_worker.wx.CallAfter", side_effect=lambda fn, *args: fn(*args))
    @patch("gui_wx.analysis_worker.recognize_audio_timing")
    def test_whisper_failure_does_not_call_success_callback(self, mock_recognize, _mock_call_after):
        callback = MagicMock()
        error_callback = MagicMock()
        error = WhisperTimingError("Whisper transcription failed: missing ffmpeg")
        mock_recognize.side_effect = error
        runtime, request = _runtime_request()
        worker = AnalysisWorker(
            job_id=19,
            callback=callback,
            error_callback=error_callback,
            phase_callback=None,
            text_content="",
            wav_path="voice.wav",
            wav_analysis=MagicMock(),
            input_mode=INPUT_MODE_VOICE_ONLY,
            whisper_model_request=request,
            whisper_runtime=runtime,
        )

        worker.run()

        callback.assert_not_called()
        error_callback.assert_called_once_with(19, error)

    @patch("gui_wx.analysis_worker.wx.CallAfter", side_effect=lambda fn, *args: fn(*args))
    def test_empty_edited_text_does_not_call_success_callback(self, _mock_call_after):
        callback = MagicMock()
        error_callback = MagicMock()
        runtime, request = _runtime_request()
        worker = AnalysisWorker(
            job_id=20,
            callback=callback,
            error_callback=error_callback,
            phase_callback=None,
            text_content="",
            wav_path="voice.wav",
            wav_analysis=MagicMock(),
            input_mode=INPUT_MODE_VOICE_ONLY,
            transcription_text_override="   ",
            retained_whisper_timing_result=MagicMock(),
            reuse_retained_timing=True,
            whisper_model_request=request,
            whisper_runtime=runtime,
        )

        worker.run()

        callback.assert_not_called()
        error_callback.assert_called_once()
        self.assertIn("編集済み書き起こしテキストが空", str(error_callback.call_args.args[1]))

    @patch("gui_wx.main_frame.wx.MessageBox")
    def test_analysis_error_invalidates_plan_and_preserves_edited_text(self, mock_message_box):
        state = self.frame.ui_state
        state.input_mode = INPUT_MODE_VOICE_ONLY
        state.selected_wav_path = "dummy.wav"
        state.transcription_text = "編集済みテキスト"
        state.analysis_text_content = "編集済みテキスト"
        state.analysis_text_source = "user_edited_transcription"
        state.analysis_result_valid = True
        state.current_timing_plan = MagicMock()
        state.set_busy(True)
        self.frame._active_analysis_job_id = 19
        self.frame._analysis_parameter_snapshot = (
            self.frame._capture_analysis_parameters()
        )

        self.frame._on_analysis_error(19, TextProcessingError("conversion failed"))

        self.assertFalse(state.is_busy)
        self.assertFalse(state.analysis_result_valid)
        self.assertTrue(state.analysis_pending_rebuild)
        self.assertIsNone(state.current_timing_plan)
        self.assertEqual(state.transcription_text, "編集済みテキスト")
        self.assertEqual(state.analysis_text_source, "user_edited_transcription")
        self.assertFalse(state.vmd_save_ready)
        self.assertIsNotNone(state.current_diagnostic_failure)
        self.assertEqual(
            state.current_diagnostic_failure.code,
            "voice_only_text_conversion_failed",
        )
        self.assertIn("[ERROR]", self.frame.right_pane.get_warning_text())
        self.assertIn("日本語読み変換", self.frame.right_pane.get_warning_text())
        message, title, _style = mock_message_box.call_args.args
        self.assertEqual(title, "音声のみ解析エラー")
        self.assertIn("日本語読み変換", message)
        self.assertIn("再解析", message)

    @patch("gui_wx.app_controller.wx.MessageBox")
    @patch("gui_wx.app_controller.generate_vmd_from_timing_plan")
    def test_vmd_save_failure_preserves_analysis_result(self, mock_generate, mock_message_box):
        state = self.frame.ui_state
        state.selected_wav_path = "dummy.wav"
        state.selected_wav_analysis = MagicMock()
        state.selected_wav_analysis.duration_sec = 1.0
        state.last_vmd_output_dir = "previous"
        plan = VowelTimingPlan(
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
        state.mark_analysis_success(
            plan,
            input_mode=INPUT_MODE_VOICE_ONLY,
            analysis_text_content="あいうえお",
            analysis_text_source="whisper_transcription",
            transcription_text="あいうえお",
            transcription_source="segments",
            transcription_timing_source="segments",
        )
        self.frame.show_vmd_save_dialog_and_get_path = MagicMock(return_value="failed.vmd")
        mock_generate.side_effect = OSError("permission denied")

        self.controller.request_save_vmd()

        self.assertTrue(state.analysis_result_valid)
        self.assertIs(state.current_timing_plan, plan)
        self.assertTrue(state.vmd_save_ready)
        self.assertEqual(state.last_vmd_output_dir, "previous")
        message, title, _style = mock_message_box.call_args.args
        self.assertEqual(title, "保存エラー")
        self.assertIn("別の保存先", message)
        self.assertIn("permission denied", message)


if __name__ == "__main__":
    unittest.main()
