import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from src.core import (
    RmsSeriesData,
    SpeechTimingAnchor,
    WhisperTimingResult,
    analyze_wav_file,
    build_vowel_timing_plan,
)
from tests.helpers import workspace_tempdir, write_test_wav


class MS19B3TextlessPipelineTests(unittest.TestCase):
    def test_timing_plan_reuses_supplied_whisper_timing_result(self) -> None:
        with workspace_tempdir("ms19_b3_textless_pipeline") as tmp:
            wav_path = tmp / "voice.wav"
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.5,
                trail_sec=0.1,
            )
            wav_analysis = analyze_wav_file(str(wav_path))
            whisper_result = WhisperTimingResult(
                anchors=[SpeechTimingAnchor(start_sec=0.1, end_sec=0.6, text="あ")],
                raw_result={"segments": [{"start": 0.1, "end": 0.6, "text": "あ"}]},
                source="segments",
            )

            with (
                patch("src.core.pipeline.recognize_audio_timing", side_effect=AssertionError("not expected")),
                patch(
                    "src.core.pipeline.load_rms_series",
                    return_value=RmsSeriesData(
                        sample_rate_hz=100,
                        channel_count=1,
                        duration_sec=0.7,
                        window_size_samples=5,
                        hop_size_samples=5,
                        times_sec=[0.15, 0.20, 0.25, 0.30, 0.36, 0.40, 0.45],
                        values=[0.05, 0.4, 1.0, 0.8, 0.4, 0.05, 0.02],
                    ),
                ),
            ):
                plan = build_vowel_timing_plan(
                    text_content="あ",
                    wav_path=wav_path,
                    wav_analysis=wav_analysis,
                    whisper_timing_result=whisper_result,
                )

            self.assertEqual(plan.source, "whisper_segments")
            self.assertIsNone(plan.warning)
            self.assertEqual(len(plan.anchors), 1)
            self.assertEqual(len(plan.timeline), 1)
            self.assertIsNotNone(plan.observations)

    def test_supplied_whisper_result_without_in_range_anchors_uses_even_fallback(self) -> None:
        with workspace_tempdir("ms19_b3_textless_pipeline_fallback") as tmp:
            wav_path = tmp / "voice.wav"
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.5,
                trail_sec=0.1,
            )
            wav_analysis = analyze_wav_file(str(wav_path))
            whisper_result = WhisperTimingResult(
                anchors=[SpeechTimingAnchor(start_sec=1.0, end_sec=1.2, text="outside")],
                raw_result={"segments": [{"start": 1.0, "end": 1.2, "text": "outside"}]},
                source="segments",
            )

            with (
                patch("src.core.pipeline.recognize_audio_timing", side_effect=AssertionError("not expected")),
                patch(
                    "src.core.pipeline.load_rms_series",
                    return_value=RmsSeriesData(
                        sample_rate_hz=100,
                        channel_count=1,
                        duration_sec=0.7,
                        window_size_samples=5,
                        hop_size_samples=5,
                        times_sec=[],
                        values=[],
                    ),
                ),
            ):
                plan = build_vowel_timing_plan(
                    text_content="あい",
                    wav_path=wav_path,
                    wav_analysis=wav_analysis,
                    whisper_timing_result=whisper_result,
                )

            self.assertEqual(plan.source, "even_fallback")
            self.assertIsNotNone(plan.warning)
            self.assertEqual(len(plan.anchors), 0)
            self.assertEqual(len(plan.timeline), 2)


if __name__ == "__main__":
    unittest.main()
