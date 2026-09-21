import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core import (
    PipelineError,
    generate_vmd_from_text_wav,
)
from src.core.whisper_timing import WhisperTimingError, recognize_audio
from tests.helpers import workspace_tempdir, write_test_wav


class NoImplicitDownloadTests(unittest.TestCase):
    def test_recognize_audio_requires_verified_runtime_session_before_whisper_import_path(self) -> None:
        with patch("whisper.load_model", side_effect=AssertionError("implicit model load")) as load_model:
            with self.assertRaises(WhisperTimingError) as context:
                recognize_audio("voice.wav")

        self.assertEqual(context.exception.code, "model_request_missing")
        self.assertEqual(context.exception.failure_class, "model_unavailable")
        load_model.assert_not_called()

    def test_direct_vmd_entrypoint_rejects_missing_timing_plan_without_loading_whisper(self) -> None:
        with workspace_tempdir("no_implicit_download") as tmp:
            text_path = tmp / "input.txt"
            wav_path = tmp / "voice.wav"
            output_path = tmp / "out.vmd"
            text_path.write_text("あ", encoding="utf-8")
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.3,
                trail_sec=0.1,
            )

            with patch("whisper.load_model", side_effect=AssertionError("implicit model load")) as load_model:
                with self.assertRaises(PipelineError) as context:
                    generate_vmd_from_text_wav(text_path, wav_path, output_path)

            self.assertEqual(context.exception.error_code, "timing_plan_build_failed")
            self.assertEqual(context.exception.detail_code, "analysis_request_missing")
            self.assertFalse(output_path.exists())
            load_model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
