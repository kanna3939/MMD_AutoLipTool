import unittest
import os
import tempfile
from types import SimpleNamespace
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from src.core.whisper_model_runtime import (
    ModelIdentity,
    RuntimeCacheIdentity,
    WhisperModelSession,
)
from src.core.whisper_timing import (
    WhisperTimingError,
    recognize_audio,
    recognize_audio_timing,
)


def _session(model) -> WhisperModelSession:
    identity = ModelIdentity("small", "test-manifest")
    return WhisperModelSession(
        model=model,
        identity=identity,
        cache_identity=RuntimeCacheIdentity("small", "C:\\models", "test-manifest"),
        session_id="test-session",
    )


class WhisperTimingTests(unittest.TestCase):
    def test_recognize_audio_temporarily_exposes_located_ffmpeg_to_whisper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wav_path = tmp_path / "voice.wav"
            wav_path.write_bytes(b"dummy")
            ffmpeg_dir = tmp_path / "FFmpeg" / "bin"
            ffmpeg_dir.mkdir(parents=True)
            ffmpeg_path = ffmpeg_dir / "ffmpeg.exe"
            ffmpeg_path.write_bytes(b"dummy")
            original_path = os.environ.get("PATH", "")
            test_case = self

            class DummyModel:
                def transcribe(self, path: str, **kwargs):
                    test_case.assertTrue(os.environ["PATH"].split(os.pathsep)[0] == str(ffmpeg_dir))
                    test_case.assertEqual(path, str(wav_path))
                    return {"text": "ok", "segments": []}

            with patch(
                "src.core.whisper_timing.locate_ffmpeg_tools",
                return_value=SimpleNamespace(ffmpeg=SimpleNamespace(path=ffmpeg_path)),
            ):
                result = recognize_audio(
                    wav_path,
                    model_session=_session(DummyModel()),
                )

            self.assertEqual(result["text"], "ok")
            self.assertEqual(os.environ.get("PATH", ""), original_path)

    @patch("src.core.whisper_timing.recognize_audio")
    def test_segment_fallback_from_word_run_when_words_are_sparse(self, mock_recognize_audio: object) -> None:
        mock_recognize_audio.return_value = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.8,
                    "text": "あいうえお",
                    "words": [{"start": 0.1, "end": 1.7, "word": "あいうえお"}],
                },
                {
                    "start": 1.9,
                    "end": 2.6,
                    "text": "テスト",
                    "words": [],
                },
            ]
        }

        result = recognize_audio_timing("dummy.wav", model_session=_session(object()))

        self.assertEqual(result.source, "segments")
        self.assertEqual(len(result.anchors), 2)
        self.assertAlmostEqual(result.anchors[0].start_sec, 0.0, places=3)
        self.assertAlmostEqual(result.anchors[0].end_sec, 1.8, places=3)
        self.assertEqual(mock_recognize_audio.call_count, 1)
        self.assertTrue(mock_recognize_audio.call_args.kwargs["word_timestamps"])

    @patch("src.core.whisper_timing.recognize_audio")
    def test_words_are_preferred_when_multiple_word_anchors_exist(self, mock_recognize_audio: object) -> None:
        mock_recognize_audio.return_value = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "abc",
                    "words": [
                        {"start": 0.05, "end": 0.3, "word": "a"},
                        {"start": 0.35, "end": 0.65, "word": "b"},
                        {"start": 0.7, "end": 0.95, "word": "c"},
                    ],
                }
            ]
        }

        result = recognize_audio_timing("dummy.wav", model_session=_session(object()))

        self.assertEqual(result.source, "words")
        self.assertEqual(len(result.anchors), 3)

    @patch("src.core.whisper_timing.recognize_audio")
    def test_infrastructure_failure_does_not_retry_segment_only(self, mock_recognize_audio: object) -> None:
        mock_recognize_audio.side_effect = WhisperTimingError(
            "word timestamp failure",
            code="whisper_transcribe_failed",
            failure_class="transcribe_failure",
        )

        with self.assertRaises(WhisperTimingError) as context:
            recognize_audio_timing("dummy.wav", model_session=_session(object()))

        self.assertEqual(context.exception.code, "whisper_transcribe_failed")
        self.assertEqual(mock_recognize_audio.call_count, 1)

    @patch("src.core.whisper_timing.recognize_audio")
    def test_retry_with_segment_only_when_first_run_has_no_usable_anchors(self, mock_recognize_audio: object) -> None:
        mock_recognize_audio.side_effect = [
            {"segments": []},
            {"segments": [{"start": 0.2, "end": 0.9, "text": "い"}]},
        ]

        result = recognize_audio_timing("dummy.wav", model_session=_session(object()))

        self.assertEqual(result.source, "segments")
        self.assertEqual(
            [call.kwargs["word_timestamps"] for call in mock_recognize_audio.call_args_list],
            [True, False],
        )


if __name__ == "__main__":
    unittest.main()
