import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.whisper_timing import recognize_audio_timing


class WhisperTimingTests(unittest.TestCase):
    @patch("core.whisper_timing.recognize_audio")
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

        result = recognize_audio_timing("dummy.wav")

        self.assertEqual(result.source, "segments")
        self.assertEqual(len(result.anchors), 2)
        self.assertAlmostEqual(result.anchors[0].start_sec, 0.0, places=3)
        self.assertAlmostEqual(result.anchors[0].end_sec, 1.8, places=3)

    @patch("core.whisper_timing.recognize_audio")
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

        result = recognize_audio_timing("dummy.wav")

        self.assertEqual(result.source, "words")
        self.assertEqual(len(result.anchors), 3)


if __name__ == "__main__":
    unittest.main()
