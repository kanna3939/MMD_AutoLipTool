import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.analysis_worker import AnalysisWorker, AnalysisWorkerResult
from gui_wx.ui_state import INPUT_MODE_VOICE_ONLY
from src.core import (
    ModelIdentity,
    RuntimeCacheIdentity,
    SpeechTimingAnchor,
    TranscriptionTextResult,
    VerifiedAnalysisModelRequest,
    WhisperModelRuntime,
    WhisperModelSession,
    WhisperTimingResult,
)
from src.core.analysis_debug_trace import build_debug_trace
from src.core.whisper_model_loader import VerifiedWhisperCheckpoint


class MS19B4AnalysisWorkerVoiceOnlyTests(unittest.TestCase):
    def test_voice_only_worker_reuses_single_whisper_timing_result(self):
        callback = MagicMock()
        error_callback = MagicMock()
        phase_callback = MagicMock()
        wav_analysis = MagicMock()
        timing_plan = MagicMock()
        timing_plan.source = "whisper_words"
        debug_trace = build_debug_trace(
            input_mode=INPUT_MODE_VOICE_ONLY,
            job_id=7,
            source_audio_path=None,
            analysis_wav_path=None,
            text_path=None,
            analysis_text="",
            model_identity=None,
            timing_source="pending",
            selected_model_key="small",
            selected_wav_analysis=None,
        )
        whisper_result = WhisperTimingResult(
            anchors=[SpeechTimingAnchor(start_sec=0.1, end_sec=0.5, text="あ")],
            raw_result={"segments": [{"start": 0.1, "end": 0.5, "text": "あいう"}]},
            source="segments",
        )
        identity = ModelIdentity("small", "test-manifest")
        session = WhisperModelSession(
            model=object(),
            identity=identity,
            cache_identity=RuntimeCacheIdentity("small", "C:\\models", "test-manifest"),
            session_id="test-session",
        )
        request = VerifiedAnalysisModelRequest(
            identity=identity,
            cache_identity=session.cache_identity,
            verified_checkpoint=VerifiedWhisperCheckpoint(
                model_key="small",
                checkpoint_path=Path("model.bin"),
                manifest_identity="test-manifest",
                sha256="0" * 64,
                size_bytes=1,
            ),
        )
        runtime = WhisperModelRuntime()
        runtime.acquire = MagicMock(return_value=session)
        runtime.release = MagicMock()

        worker = AnalysisWorker(
            job_id=7,
            callback=callback,
            error_callback=error_callback,
            phase_callback=phase_callback,
            text_content="",
            wav_path="voice.wav",
            wav_analysis=wav_analysis,
            whisper_model_request=request,
            whisper_runtime=runtime,
            input_mode=INPUT_MODE_VOICE_ONLY,
            debug_trace=debug_trace,
        )

        with (
            patch("gui_wx.analysis_worker.wx.CallAfter", side_effect=lambda fn, *args: fn(*args)),
            patch("gui_wx.analysis_worker.recognize_audio_timing", return_value=whisper_result) as mock_recognize,
            patch(
                "gui_wx.analysis_worker.extract_transcription_text",
                return_value=TranscriptionTextResult(text="あいう", source="segments"),
            ) as mock_extract,
            patch("gui_wx.analysis_worker.build_vowel_timing_plan", return_value=timing_plan) as mock_build,
        ):
            worker.run()

        error_callback.assert_not_called()
        mock_recognize.assert_called_once_with(
            wav_path="voice.wav",
            model_session=session,
            language="ja",
            fp16=False,
        )
        mock_extract.assert_called_once_with(whisper_result.raw_result)
        mock_build.assert_called_once()
        build_kwargs = mock_build.call_args.kwargs
        self.assertEqual(build_kwargs["text_content"], "あいう")
        self.assertIs(build_kwargs["whisper_timing_result"], whisper_result)
        self.assertIs(build_kwargs["whisper_model_session"], session)

        callback.assert_called_once()
        job_id, result = callback.call_args.args
        self.assertEqual(job_id, 7)
        self.assertIsInstance(result, AnalysisWorkerResult)
        self.assertIs(result.timing_plan, timing_plan)
        self.assertEqual(result.input_mode, INPUT_MODE_VOICE_ONLY)
        self.assertEqual(result.transcription_text, "あいう")
        self.assertEqual(result.transcription_source, "segments")
        self.assertEqual(result.transcription_timing_source, "segments")
        self.assertIs(result.whisper_timing_result, whisper_result)
        identity = debug_trace.snapshot()["input_identity"]
        self.assertEqual(identity["analysis_text"]["source"], "whisper_transcription")
        self.assertEqual(identity["timing"]["source"], "whisper_words")
        self.assertEqual(identity["model"]["model_key"], "small")
        self.assertEqual(identity["model"]["manifest_identity"], "test-manifest")


if __name__ == "__main__":
    unittest.main()
