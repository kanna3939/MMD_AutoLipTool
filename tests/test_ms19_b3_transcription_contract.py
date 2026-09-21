import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from src.core import WhisperTimingError, extract_transcription_text


class MS19B3TranscriptionContractTests(unittest.TestCase):
    def test_segments_text_is_primary_source(self) -> None:
        result = extract_transcription_text(
            {
                "text": "fallback text",
                "segments": [
                    {"text": " こんにちは "},
                    {"text": ""},
                    {"text": " 世界 "},
                    {"words": [{"word": "ignored"}]},
                ],
            }
        )

        self.assertEqual(result.text, "こんにちは世界")
        self.assertEqual(result.source, "segments")

    def test_raw_text_is_fallback_when_segments_have_no_text(self) -> None:
        result = extract_transcription_text(
            {
                "text": "  fallback text  ",
                "segments": [
                    {"text": "  "},
                    {"words": [{"word": "not used"}]},
                    "invalid segment",
                ],
            }
        )

        self.assertEqual(result.text, "fallback text")
        self.assertEqual(result.source, "raw_text")

    def test_words_only_result_is_not_accepted_as_initial_text(self) -> None:
        with self.assertRaises(WhisperTimingError):
            extract_transcription_text(
                {
                    "segments": [
                        {"words": [{"word": "これは使わない"}]},
                    ],
                }
            )

    def test_empty_text_raises(self) -> None:
        with self.assertRaises(WhisperTimingError):
            extract_transcription_text({"text": " ", "segments": [{"text": ""}]})


if __name__ == "__main__":
    unittest.main()
