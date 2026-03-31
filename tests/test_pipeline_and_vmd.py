import struct
import unittest
from pathlib import Path
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import (
    SpeechTimingAnchor,
    VowelTimingPlan,
    WhisperTimingError,
    build_anchor_based_vowel_timeline,
    build_even_vowel_timeline,
    build_vowel_timing_plan,
    generate_vmd_from_text_wav,
)
from core.audio_processing import RmsSeriesData, analyze_wav_file
from helpers import workspace_tempdir, write_test_wav
from vmd_writer import VowelTimelinePoint, write_dummy_morph_vmd


class PipelineAndVmdTests(unittest.TestCase):
    def test_even_vowel_timeline_distribution(self) -> None:
        vowels = ["\u3042", "\u3044", "\u3046", "\u3048", "\u304a"]
        timeline = build_even_vowel_timeline(vowels, speech_start_sec=0.2, speech_end_sec=1.2)

        self.assertEqual(len(timeline), len(vowels))
        self.assertEqual([p.vowel for p in timeline], vowels)
        self.assertAlmostEqual(timeline[0].time_sec, 0.2, places=3)
        self.assertAlmostEqual(timeline[1].time_sec, 0.4, places=3)
        self.assertAlmostEqual(timeline[2].time_sec, 0.6, places=3)
        self.assertAlmostEqual(timeline[3].time_sec, 0.8, places=3)
        self.assertAlmostEqual(timeline[4].time_sec, 1.0, places=3)
        self.assertTrue(all(point.duration_sec > 0 for point in timeline))
        self.assertAlmostEqual(timeline[0].duration_sec, 0.2, places=3)
        self.assertTrue(all(point.start_sec <= point.time_sec <= point.end_sec for point in timeline))
        self.assertTrue(
            all(abs((point.end_sec - point.start_sec) - point.duration_sec) < 1e-9 for point in timeline)
        )

    def test_generate_vmd_from_text_and_wav(self) -> None:
        with workspace_tempdir("pipeline_vmd") as tmp:
            text_path = tmp / "input.txt"
            wav_path = tmp / "voice.wav"
            out_path = tmp / "out.vmd"

            text_path.write_text("\u3042\u3044\u3046\u3048\u304a", encoding="utf-8")
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.2,
                speech_sec=0.5,
                trail_sec=0.2,
            )

            result = generate_vmd_from_text_wav(text_path, wav_path, out_path)

            self.assertTrue(result.output_path.exists())
            self.assertEqual(len(result.vowels), len(result.timeline))
            self.assertTrue(result.wav_analysis.has_speech)
            self.assertEqual(result.output_path.suffix.lower(), ".vmd")
            self.assertIsNotNone(result.observations)
            self.assertEqual(len(result.observations), len(result.timeline))

    def test_anchor_based_timeline_uses_local_intervals(self) -> None:
        vowels = ["\u3042", "\u3044", "\u3046", "\u3048", "\u304a"]
        anchors = [
            SpeechTimingAnchor(start_sec=0.2, end_sec=0.4, text="A"),
            SpeechTimingAnchor(start_sec=0.6, end_sec=1.0, text="B"),
        ]
        timeline = build_anchor_based_vowel_timeline(
            vowels=vowels,
            timing_anchors=anchors,
            speech_start_sec=0.2,
            speech_end_sec=1.0,
        )

        self.assertEqual(len(timeline), len(vowels))
        self.assertTrue(all(0.2 <= point.time_sec <= 1.0 for point in timeline))
        self.assertTrue(all(point.time_sec < 0.4 for point in timeline[:2]))
        self.assertTrue(all(point.time_sec >= 0.6 for point in timeline[2:]))
        self.assertTrue(all(point.duration_sec > 0 for point in timeline))
        self.assertTrue(all(point.start_sec <= point.time_sec <= point.end_sec for point in timeline))
        self.assertTrue(
            all(abs((point.end_sec - point.start_sec) - point.duration_sec) < 1e-9 for point in timeline)
        )

    @patch("core.pipeline.recognize_audio_timing", side_effect=WhisperTimingError("mock failure"))
    def test_timing_plan_falls_back_to_even_when_whisper_fails(self, _: object) -> None:
        with workspace_tempdir("timing_plan_fallback") as tmp:
            wav_path = tmp / "voice.wav"
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.5,
                trail_sec=0.1,
            )
            wav_analysis = analyze_wav_file(str(wav_path))
            plan = build_vowel_timing_plan(
                text_content="\u3042\u3044\u3046\u3048\u304a",
                wav_path=wav_path,
                wav_analysis=wav_analysis,
            )

            self.assertEqual(plan.source, "even_fallback")
            self.assertEqual(len(plan.timeline), 5)
            self.assertIsNotNone(plan.warning)
            self.assertIsNotNone(plan.observations)
            self.assertEqual(len(plan.observations), 5)

    def test_timing_plan_exposes_observations_from_main_flow(self) -> None:
        with workspace_tempdir("timing_plan_observations") as tmp:
            wav_path = tmp / "voice.wav"
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.5,
                trail_sec=0.1,
            )
            wav_analysis = analyze_wav_file(str(wav_path))

            mocked_whisper_result = Mock(
                anchors=[SpeechTimingAnchor(start_sec=0.1, end_sec=0.6, text="a")],
                source="words",
            )

            with (
                patch("core.pipeline.recognize_audio_timing", return_value=mocked_whisper_result),
                patch(
                    "core.pipeline.load_rms_series",
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
                )

            self.assertEqual(plan.source, "whisper_words")
            self.assertEqual(len(plan.timeline), 1)
            self.assertIsNotNone(plan.observations)
            self.assertEqual(len(plan.observations), 1)

            observation = plan.observations[0]
            self.assertEqual(observation.vowel, plan.vowels[0])
            self.assertAlmostEqual(observation.initial_interval_start_sec, 0.112, places=3)
            self.assertAlmostEqual(observation.initial_interval_end_sec, 0.588, places=3)
            self.assertAlmostEqual(observation.refined_interval_start_sec, 0.20, places=3)
            self.assertAlmostEqual(observation.refined_interval_end_sec, 0.36, places=3)
            self.assertEqual(observation.evaluation.peak_value, observation.peak_value)
            self.assertEqual(observation.reason, observation.evaluation.reason)

    def test_dummy_vmd_output_minimum_shape(self) -> None:
        with workspace_tempdir("dummy_vmd") as tmp_dir:
            out_path = tmp_dir / "dummy.vmd"
            write_dummy_morph_vmd(out_path)

            data = out_path.read_bytes()
            header = data[:30].rstrip(b"\x00")
            bone_count = struct.unpack("<I", data[50:54])[0]
            morph_count = struct.unpack("<I", data[54:58])[0]

            self.assertEqual(header, b"Vocaloid Motion Data 0002")
            self.assertEqual(bone_count, 0)
            self.assertEqual(morph_count, 15)

    def test_generate_vmd_uses_provided_timing_plan_and_clears_observations_after_duration_inference(self) -> None:
        with workspace_tempdir("provided_plan") as tmp:
            text_path = tmp / "input.txt"
            wav_path = tmp / "voice.wav"
            out_path = tmp / "out.vmd"

            text_path.write_text("あいうえお", encoding="utf-8")
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.6,
                trail_sec=0.1,
            )

            provided_timeline = [
                VowelTimelinePoint(time_sec=0.2, vowel="あ"),
                VowelTimelinePoint(time_sec=0.35, vowel="い"),
                VowelTimelinePoint(time_sec=0.52, vowel="う"),
            ]
            provided_plan = VowelTimingPlan(
                vowels=["あ", "い", "う"],
                timeline=provided_timeline,
                anchors=[SpeechTimingAnchor(start_sec=0.15, end_sec=0.6, text="test")],
                source="whisper_words",
                warning=None,
                observations=[],
            )

            with patch("core.pipeline.build_vowel_timing_plan", side_effect=AssertionError("not expected")):
                result = generate_vmd_from_text_wav(
                    text_path=text_path,
                    wav_path=wav_path,
                    output_path=out_path,
                    timing_plan=provided_plan,
                )

            self.assertEqual(
                [(point.time_sec, point.vowel) for point in result.timeline],
                [(point.time_sec, point.vowel) for point in provided_timeline],
            )
            self.assertTrue(all(point.duration_sec > 0 for point in result.timeline))
            self.assertTrue(all(point.start_sec <= point.time_sec <= point.end_sec for point in result.timeline))
            self.assertEqual(result.vowels, ["あ", "い", "う"])
            self.assertEqual(result.timing_source, "whisper_words")
            self.assertIsNone(result.observations)
            self.assertTrue(result.output_path.exists())

    def test_generate_vmd_preserves_observations_when_provided_timing_plan_is_used_as_is(self) -> None:
        with workspace_tempdir("provided_plan_direct") as tmp:
            text_path = tmp / "input.txt"
            wav_path = tmp / "voice.wav"
            out_path = tmp / "out.vmd"

            text_path.write_text("あいうえお", encoding="utf-8")
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.6,
                trail_sec=0.1,
            )

            provided_timeline = [
                VowelTimelinePoint(time_sec=0.2, vowel="あ", duration_sec=0.1, start_sec=0.15, end_sec=0.25),
                VowelTimelinePoint(time_sec=0.35, vowel="い", duration_sec=0.1, start_sec=0.30, end_sec=0.40),
                VowelTimelinePoint(time_sec=0.52, vowel="う", duration_sec=0.1, start_sec=0.47, end_sec=0.57),
            ]
            provided_observations: list[object] = []
            provided_plan = VowelTimingPlan(
                vowels=["あ", "い", "う"],
                timeline=provided_timeline,
                anchors=[SpeechTimingAnchor(start_sec=0.15, end_sec=0.6, text="test")],
                source="whisper_words",
                warning=None,
                observations=provided_observations,
            )

            with patch("core.pipeline.build_vowel_timing_plan", side_effect=AssertionError("not expected")):
                result = generate_vmd_from_text_wav(
                    text_path=text_path,
                    wav_path=wav_path,
                    output_path=out_path,
                    timing_plan=provided_plan,
                )

            self.assertEqual(
                [(point.time_sec, point.vowel) for point in result.timeline],
                [(point.time_sec, point.vowel) for point in provided_timeline],
            )
            self.assertEqual(result.observations, provided_observations)
            self.assertTrue(result.output_path.exists())

    def test_generate_vmd_passes_closing_softness_frames_to_writer(self) -> None:
        with workspace_tempdir("pipeline_softness_handoff") as tmp:
            text_path = tmp / "input.txt"
            wav_path = tmp / "voice.wav"
            out_path = tmp / "out.vmd"

            text_path.write_text("あ", encoding="utf-8")
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.3,
                trail_sec=0.1,
            )

            provided_timeline = [
                VowelTimelinePoint(
                    time_sec=0.2,
                    vowel="あ",
                    duration_sec=0.1,
                    start_sec=0.15,
                    end_sec=0.25,
                )
            ]
            provided_plan = VowelTimingPlan(
                vowels=["あ"],
                timeline=provided_timeline,
                anchors=[SpeechTimingAnchor(start_sec=0.15, end_sec=0.25, text="test")],
                source="provided",
                warning=None,
                observations=[],
            )

            with (
                patch("core.pipeline.build_vowel_timing_plan", side_effect=AssertionError("not expected")),
                patch("core.pipeline.write_morph_vmd", return_value=out_path) as mocked_write_morph_vmd,
            ):
                generate_vmd_from_text_wav(
                    text_path=text_path,
                    wav_path=wav_path,
                    output_path=out_path,
                    timing_plan=provided_plan,
                    closing_softness_frames=3,
                )

            mocked_write_morph_vmd.assert_called_once()
            self.assertEqual(
                mocked_write_morph_vmd.call_args.kwargs["closing_softness_frames"],
                3,
            )


if __name__ == "__main__":
    unittest.main()
