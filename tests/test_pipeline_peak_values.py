import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.audio_processing import RmsSeriesData
from core.pipeline import (
    _apply_peak_values_to_timeline,
    _build_peak_value_evaluations,
    _refine_timeline_intervals_with_rms,
)
from vmd_writer import VowelTimelinePoint


class PipelinePeakValueTests(unittest.TestCase):
    def test_peak_values_are_clamped_to_upper_limit(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
            VowelTimelinePoint(time_sec=0.75, vowel="\u3044", duration_sec=0.1, start_sec=0.70, end_sec=0.80),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.25, 0.75],
            values=[0.4, 1.0],
        )

        with_peak = _apply_peak_values_to_timeline(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(len(with_peak), 2)
        self.assertTrue(all(0.0 <= point.peak_value <= 0.5 for point in with_peak))
        self.assertLess(with_peak[0].peak_value, with_peak[1].peak_value)

    def test_load_rms_series_failure_uses_low_fixed_fallback(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]

        with patch("core.pipeline.load_rms_series", side_effect=OSError("mocked")):
            refined = _refine_timeline_intervals_with_rms(
                timeline=timeline,
                wav_path="dummy.wav",
                speech_start_sec=0.0,
                speech_end_sec=1.0,
                upper_limit=0.5,
            )

        self.assertEqual(refined[0].peak_value, 0.125)
        self.assertEqual(refined[0].value, 0.125)

    def test_global_peak_zero_forces_zero_peak_values(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.25, 0.75],
            values=[0.0, 0.0],
        )

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(evaluations[0].peak_value, 0.0)
        self.assertEqual(evaluations[0].reason, "global_peak_zero")

    def test_upper_limit_zero_forces_zero_peak_values(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.25, 0.75],
            values=[0.4, 1.0],
        )

        with_peak = _apply_peak_values_to_timeline(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.0,
        )

        self.assertEqual(with_peak[0].peak_value, 0.0)
        self.assertEqual(with_peak[0].value, 0.0)

    def test_peak_window_can_pick_peak_in_halo_outside_interval(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
            VowelTimelinePoint(time_sec=0.45, vowel="\u3044", duration_sec=0.1, start_sec=0.40, end_sec=0.50),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.32, 0.45, 0.80],
            values=[0.8, 0.3, 1.0],
        )

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertAlmostEqual(evaluations[0].peak_window_end_sec, 0.33, places=6)
        self.assertEqual(evaluations[0].local_peak, 0.8)
        self.assertIsNone(evaluations[0].reason)
        self.assertGreater(evaluations[0].peak_value, 0.0)

    def test_no_peak_in_window_reason_is_reported(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.60, 0.80],
            values=[1.0, 0.5],
        )

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(evaluations[0].peak_value, 0.0)
        self.assertEqual(evaluations[0].reason, "no_peak_in_window")

    def test_below_abs_threshold_reason_is_reported(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.25, 0.80],
            values=[0.009, 1.0],
        )

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(evaluations[0].peak_value, 0.0)
        self.assertEqual(evaluations[0].reason, "below_abs_threshold")

    def test_below_rel_threshold_reason_is_reported(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.25, 0.80],
            values=[0.2, 1.0],
        )

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(evaluations[0].peak_value, 0.0)
        self.assertEqual(evaluations[0].reason, "below_rel_threshold")

    def test_reason_priority_prefers_rms_unavailable(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=None,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
            fallback_reason="rms_unavailable",
        )

        self.assertEqual(evaluations[0].reason, "rms_unavailable")
        self.assertEqual(evaluations[0].peak_value, 0.125)

    def test_reason_priority_prefers_global_peak_zero_over_no_peak_in_window(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.60],
            values=[0.0],
        )

        evaluations = _build_peak_value_evaluations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(evaluations[0].reason, "global_peak_zero")


if __name__ == "__main__":
    unittest.main()
