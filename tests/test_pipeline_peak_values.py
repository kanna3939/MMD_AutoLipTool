import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.audio_processing import RmsSeriesData
from core.pipeline import (
    _apply_peak_values_to_timeline,
    _build_peak_value_evaluations,
    _build_peak_value_observations,
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

    def test_observation_includes_initial_and_refined_intervals(self) -> None:
        initial_timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.2, start_sec=0.15, end_sec=0.35),
        ]
        refined_timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[0.25, 0.80],
            values=[0.4, 1.0],
        )

        observations = _build_peak_value_observations(
            timeline=refined_timeline,
            initial_timeline=initial_timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(len(observations), 1)
        observation = observations[0]
        self.assertEqual(observation.event_index, 0)
        self.assertEqual(observation.vowel, "\u3042")
        self.assertAlmostEqual(observation.initial_interval_start_sec, 0.15, places=6)
        self.assertAlmostEqual(observation.initial_interval_end_sec, 0.35, places=6)
        self.assertAlmostEqual(observation.refined_interval_start_sec, 0.20, places=6)
        self.assertAlmostEqual(observation.refined_interval_end_sec, 0.30, places=6)
        self.assertAlmostEqual(observation.global_peak, 1.0, places=6)
        self.assertEqual(observation.window_sample_count, 1)
        self.assertEqual(observation.evaluation.peak_value, observation.peak_value)

    def test_observation_reports_halo_window_and_sample_count(self) -> None:
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

        observations = _build_peak_value_observations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(len(observations), 2)
        self.assertAlmostEqual(observations[0].peak_window_end_sec, 0.33, places=6)
        self.assertEqual(observations[0].window_sample_count, 1)
        self.assertEqual(observations[0].local_peak, 0.8)
        self.assertEqual(observations[0].rms_window_times_sec, (0.32,))
        self.assertEqual(observations[0].rms_window_values, (0.8,))

    def test_observation_marks_same_vowel_one_frame_zero_gap_as_bridgeable_candidate(self) -> None:
        refined_timeline = [
            VowelTimelinePoint(time_sec=1.0, vowel="あ", peak_value=0.5, start_sec=0.8, end_sec=1.2),
            VowelTimelinePoint(time_sec=37 / 30, vowel="あ", peak_value=0.0, start_sec=37 / 30, end_sec=38 / 30),
            VowelTimelinePoint(time_sec=1.3, vowel="あ", peak_value=0.4, start_sec=1.2666667, end_sec=1.5),
        ]
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 1.3],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=refined_timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertEqual(len(observations), 3)
        self.assertTrue(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[1].is_bridgeable_micro_gap_candidate)
        self.assertFalse(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "no_peak_in_window")
        self.assertEqual(observations[1].previous_non_zero_event_index, 0)
        self.assertEqual(observations[1].next_non_zero_event_index, 2)

    def test_observation_marks_cross_vowel_zero_gap_as_transition_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 1.3],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=1.0, vowel="あ", peak_value=0.5, start_sec=0.8, end_sec=1.2),
                VowelTimelinePoint(time_sec=37 / 30, vowel="あ", peak_value=0.0, start_sec=37 / 30, end_sec=38 / 30),
                VowelTimelinePoint(time_sec=1.3, vowel="い", peak_value=0.4, start_sec=1.2666667, end_sec=1.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertFalse(observations[1].is_bridgeable_micro_gap_candidate)
        self.assertTrue(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "no_peak_in_window")

    def test_observation_marks_same_vowel_low_positive_short_segment_as_burst_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 37 / 30, 1.3],
            values=[1.0, 0.36, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=1.0, vowel="う", peak_value=0.5, start_sec=0.8, end_sec=1.2),
                VowelTimelinePoint(time_sec=37 / 30, vowel="う", peak_value=0.12, start_sec=37 / 30, end_sec=38 / 30),
                VowelTimelinePoint(time_sec=1.3, vowel="う", peak_value=0.4, start_sec=1.2666667, end_sec=1.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[1].is_same_vowel_burst_candidate)
        self.assertFalse(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "same_vowel_burst")
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 1)

    def test_observation_marks_same_vowel_low_positive_and_zero_span_with_one_frame_overlap_as_burst_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 37 / 30, 1.3],
            values=[1.0, 0.36, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=1.0, vowel="う", peak_value=0.5, start_sec=0.8, end_sec=37 / 30),
                VowelTimelinePoint(time_sec=37 / 30, vowel="う", peak_value=0.12, start_sec=36 / 30, end_sec=37 / 30),
                VowelTimelinePoint(time_sec=38 / 30, vowel="う", peak_value=0.0, start_sec=37 / 30, end_sec=38 / 30),
                VowelTimelinePoint(time_sec=1.3, vowel="う", peak_value=0.4, start_sec=38 / 30, end_sec=1.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[1].is_same_vowel_burst_candidate)
        self.assertTrue(observations[2].is_same_vowel_burst_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "same_vowel_burst")
        self.assertEqual(observations[2].bridge_candidate_reason, "same_vowel_burst")
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_marks_two_zero_same_vowel_span_as_bridgeable_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 1.5],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=1.0, vowel="あ", peak_value=0.5, start_sec=0.8, end_sec=1.23),
                VowelTimelinePoint(time_sec=37 / 30, vowel="あ", peak_value=0.0, start_sec=37 / 30, end_sec=38 / 30),
                VowelTimelinePoint(time_sec=38 / 30, vowel="あ", peak_value=0.0, start_sec=38 / 30, end_sec=39 / 30),
                VowelTimelinePoint(time_sec=1.5, vowel="あ", peak_value=0.4, start_sec=39 / 30, end_sec=1.7),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertTrue(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[2].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_marks_same_vowel_two_zero_span_with_one_frame_overlap_as_bridgeable_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 1.5],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=1.0, vowel="あ", peak_value=0.5, start_sec=0.8, end_sec=37 / 30),
                VowelTimelinePoint(time_sec=37 / 30, vowel="あ", peak_value=0.0, start_sec=36 / 30, end_sec=37 / 30),
                VowelTimelinePoint(time_sec=38 / 30, vowel="あ", peak_value=0.0, start_sec=37 / 30, end_sec=38 / 30),
                VowelTimelinePoint(time_sec=1.5, vowel="あ", peak_value=0.4, start_sec=38 / 30, end_sec=1.7),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertTrue(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[2].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_marks_same_vowel_long_zero_interval_as_bridgeable_candidate_via_representative_span(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 3.3],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="あ", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="あ", peak_value=0.0, start_sec=90 / 30, end_sec=98 / 30),
                VowelTimelinePoint(time_sec=3.3, vowel="あ", peak_value=0.4, start_sec=97 / 30, end_sec=3.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertTrue(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[1].is_bridgeable_micro_gap_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "no_peak_in_window")
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 1)

    def test_observation_marks_same_vowel_long_low_positive_interval_as_burst_candidate_via_representative_span(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 94 / 30, 3.3],
            values=[1.0, 0.36, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="う", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="う", peak_value=0.12, start_sec=90 / 30, end_sec=98 / 30),
                VowelTimelinePoint(time_sec=3.3, vowel="う", peak_value=0.4, start_sec=97 / 30, end_sec=3.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_same_vowel_micro_gap_candidate)
        self.assertTrue(observations[1].is_same_vowel_burst_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "same_vowel_burst")
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 1)

    def test_observation_marks_two_zero_cross_vowel_span_as_transition_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=2.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[1.0, 1.5],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=1.0, vowel="あ", peak_value=0.5, start_sec=0.8, end_sec=1.23),
                VowelTimelinePoint(time_sec=37 / 30, vowel="い", peak_value=0.0, start_sec=37 / 30, end_sec=38 / 30),
                VowelTimelinePoint(time_sec=38 / 30, vowel="う", peak_value=0.0, start_sec=38 / 30, end_sec=39 / 30),
                VowelTimelinePoint(time_sec=1.5, vowel="い", peak_value=0.4, start_sec=39 / 30, end_sec=1.7),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=2.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[2].is_bridgeable_cross_vowel_transition_candidate)
        self.assertTrue(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertTrue(observations[2].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_marks_cross_vowel_long_zero_interval_as_transition_candidate_via_representative_span(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 3.3],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="あ", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="い", peak_value=0.0, start_sec=90 / 30, end_sec=98 / 30),
                VowelTimelinePoint(time_sec=3.3, vowel="う", peak_value=0.4, start_sec=97 / 30, end_sec=3.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertTrue(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].bridge_candidate_reason, "no_peak_in_window")
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 1)

    def test_observation_marks_cross_vowel_long_two_zero_span_as_floor_candidate_via_representative_span(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 3.3],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="あ", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="い", peak_value=0.0, start_sec=90 / 30, end_sec=94 / 30),
                VowelTimelinePoint(time_sec=97 / 30, vowel="う", peak_value=0.0, start_sec=94 / 30, end_sec=98 / 30),
                VowelTimelinePoint(time_sec=3.3, vowel="え", peak_value=0.4, start_sec=97 / 30, end_sec=3.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[2].is_bridgeable_cross_vowel_transition_candidate)
        self.assertTrue(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertTrue(observations[2].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_marks_cross_vowel_single_zero_span_with_moderate_right_gap_as_transition_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 3.3333333],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="う", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="え", peak_value=0.0, start_sec=91 / 30, end_sec=98 / 30),
                VowelTimelinePoint(time_sec=100 / 30, vowel="お", peak_value=0.4, start_sec=99 / 30, end_sec=3.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertTrue(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 1)

    def test_observation_marks_cross_vowel_two_event_right_gap_residual_span_as_transition_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 3.4666667],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="う", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="え", peak_value=0.0, start_sec=92 / 30, end_sec=95 / 30),
                VowelTimelinePoint(time_sec=98 / 30, vowel="え", peak_value=0.0, start_sec=96 / 30, end_sec=100 / 30),
                VowelTimelinePoint(time_sec=104 / 30, vowel="お", peak_value=0.4, start_sec=103 / 30, end_sec=3.5),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertTrue(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertTrue(observations[2].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertFalse(observations[2].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_marks_cross_vowel_wide_two_event_right_gap_span_as_floor_candidate(self) -> None:
        rms_series = RmsSeriesData(
            sample_rate_hz=100,
            channel_count=1,
            duration_sec=4.0,
            window_size_samples=5,
            hop_size_samples=5,
            times_sec=[3.0, 3.5],
            values=[1.0, 0.8],
        )
        observations = _build_peak_value_observations(
            timeline=[
                VowelTimelinePoint(time_sec=3.0, vowel="あ", peak_value=0.5, start_sec=2.8, end_sec=91 / 30),
                VowelTimelinePoint(time_sec=94 / 30, vowel="い", peak_value=0.0, start_sec=92 / 30, end_sec=95 / 30),
                VowelTimelinePoint(time_sec=98 / 30, vowel="い", peak_value=0.0, start_sec=96 / 30, end_sec=100 / 30),
                VowelTimelinePoint(time_sec=104 / 30, vowel="う", peak_value=0.4, start_sec=100 / 30, end_sec=3.7),
            ],
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=4.0,
            upper_limit=0.5,
        )

        self.assertFalse(observations[1].is_bridgeable_cross_vowel_transition_candidate)
        self.assertFalse(observations[2].is_bridgeable_cross_vowel_transition_candidate)
        self.assertTrue(observations[1].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertTrue(observations[2].is_cross_vowel_zero_run_continuity_floor_candidate)
        self.assertEqual(observations[1].span_start_index, 1)
        self.assertEqual(observations[1].span_end_index, 2)
        self.assertEqual(observations[2].span_start_index, 1)
        self.assertEqual(observations[2].span_end_index, 2)

    def test_observation_reports_rms_unavailable_fallback_without_global_peak(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]

        observations = _build_peak_value_observations(
            timeline=timeline,
            rms_series=None,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
            fallback_reason="rms_unavailable",
        )

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].reason, "rms_unavailable")
        self.assertEqual(observations[0].fallback_reason, "rms_unavailable")
        self.assertIsNone(observations[0].global_peak)
        self.assertEqual(observations[0].window_sample_count, 0)
        self.assertEqual(observations[0].peak_value, 0.125)

    def test_observation_reports_global_peak_zero_with_zero_global_peak_context(self) -> None:
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
            values=[0.0, 0.0],
        )

        observations = _build_peak_value_observations(
            timeline=timeline,
            rms_series=rms_series,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
            upper_limit=0.5,
        )

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].reason, "global_peak_zero")
        self.assertIsNone(observations[0].fallback_reason)
        self.assertEqual(observations[0].global_peak, 0.0)
        self.assertEqual(observations[0].local_peak, 0.0)
        self.assertEqual(observations[0].window_sample_count, 1)
        self.assertEqual(observations[0].peak_value, 0.0)

    def test_observation_requires_matching_initial_timeline_length(self) -> None:
        timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.1, start_sec=0.20, end_sec=0.30),
        ]
        initial_timeline = [
            VowelTimelinePoint(time_sec=0.25, vowel="\u3042", duration_sec=0.2, start_sec=0.15, end_sec=0.35),
            VowelTimelinePoint(time_sec=0.45, vowel="\u3044", duration_sec=0.2, start_sec=0.35, end_sec=0.55),
        ]

        with self.assertRaises(ValueError):
            _build_peak_value_observations(
                timeline=timeline,
                initial_timeline=initial_timeline,
                rms_series=None,
                speech_start_sec=0.0,
                speech_end_sec=1.0,
                upper_limit=0.5,
            )


if __name__ == "__main__":
    unittest.main()
