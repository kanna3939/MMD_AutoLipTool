import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.audio_processing import RmsSeriesData
from core.pipeline import _apply_peak_values_to_timeline
from vmd_writer import VowelTimelinePoint


class PipelinePeakValueTests(unittest.TestCase):
    def test_peak_values_are_clamped_to_upper_limit(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.5, start_sec=0.0, end_sec=0.5),
            VowelTimelinePoint(time_sec=0.75, vowel="\u3044", duration_sec=0.5, start_sec=0.5, end_sec=1.0),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.1, 0.3, 0.6, 0.8],
            values=[0.2, 0.4, 0.8, 1.0],
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

    def test_peak_values_fall_back_to_upper_limit_without_rms(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.5, start_sec=0.0, end_sec=0.5),
        ]

        with_peak = _apply_peak_values_to_timeline(
            timeline=timeline,
            rms_series=None,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.4321,
        )

        self.assertEqual(with_peak[0].peak_value, 0.4321)
        self.assertEqual(with_peak[0].value, 0.4321)

    def test_upper_limit_zero_forces_zero_peak_values(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.5, start_sec=0.0, end_sec=0.5),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.1, 0.3, 0.6, 0.8],
            values=[0.2, 0.4, 0.8, 1.0],
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


if __name__ == "__main__":
    unittest.main()
