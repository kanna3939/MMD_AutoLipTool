import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import _build_interval_morph_frames


class VmdWriterIntervalTests(unittest.TestCase):
    def test_softness_zero_preserves_existing_ms11_2_shape(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=0)
        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.5),
                (33, "あ", 0.5),
                (36, "あ", 0.0),
            ],
        )

    def test_trapezoid_frames_use_ms11_2_four_point_shape_for_long_interval(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.5),
                (33, "あ", 0.5),
                (36, "あ", 0.0),
            ],
        )

    def test_trapezoid_uses_decayed_peak_end_value_from_observation(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(
            points,
            observations=[
                SimpleNamespace(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    is_bridgeable_same_vowel_micro_gap_candidate=False,
                    is_bridgeable_cross_vowel_transition_candidate=False,
                    local_peak=1.0,
                    previous_non_zero_event_index=None,
                    next_non_zero_event_index=None,
                    span_start_index=None,
                    span_end_index=None,
                    rms_window_times_sec=(1.09, 1.2),
                    rms_window_values=(1.0, 0.3),
                )
            ],
        )
        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.5),
                (33, "あ", 0.15),
                (36, "あ", 0.0),
            ],
        )

    def test_zero_peak_cross_vowel_candidate_uses_continuity_floor(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="い",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
                peak_value=0.0,
                value=0.0,
            )
        ]

        frames = _build_interval_morph_frames(
            points,
            observations=[
                SimpleNamespace(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    is_bridgeable_same_vowel_micro_gap_candidate=False,
                    is_bridgeable_cross_vowel_transition_candidate=True,
                    local_peak=None,
                    previous_non_zero_event_index=None,
                    next_non_zero_event_index=None,
                    span_start_index=None,
                    span_end_index=None,
                    rms_window_times_sec=(),
                    rms_window_values=(),
                )
            ],
        )
        self.assertEqual(
            frames,
            [
                (24, "い", 0.0),
                (27, "い", 0.1),
                (33, "い", 0.1),
                (36, "い", 0.0),
            ],
        )

    def test_time_sec_is_reflected_as_top_center_basis(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4666667,
                start_sec=0.7,
                end_sec=1.1666667,
            )
        ]

        frames = _build_interval_morph_frames(points)

        self.assertEqual(frames[1][0] + frames[2][0], 60)
        self.assertEqual(
            frames,
            [
                (21, "あ", 0.0),
                (28, "あ", 0.5),
                (32, "あ", 0.5),
                (35, "あ", 0.0),
            ],
        )

    def test_long_interval_uses_asymmetric_shoulders(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4666667,
                start_sec=0.7,
                end_sec=1.1666667,
            )
        ]

        frames = _build_interval_morph_frames(points)
        left_shoulder_width = frames[1][0] - frames[0][0]
        right_shoulder_width = frames[3][0] - frames[2][0]

        self.assertNotEqual(left_shoulder_width, right_shoulder_width)
        self.assertGreater(left_shoulder_width, right_shoulder_width)

    def test_exact_four_frame_interval_keeps_top_segment(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.1333334,
                start_sec=0.9333333,
                end_sec=1.0666667,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (29, "あ", 0.5),
                (31, "あ", 0.5),
                (32, "あ", 0.0),
            ],
        )

    def test_short_interval_falls_back_to_existing_triangle(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.099,
                start_sec=0.95,
                end_sec=1.049,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (31, "あ", 0.0),
            ],
        )

    def test_zero_interval_uses_legacy_peak_fallback(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.0,
                start_sec=1.0,
                end_sec=1.0,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (32, "あ", 0.0),
            ],
        )

    def test_peak_fallback_closing_softness_extends_only_final_closing_edge(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.0,
                start_sec=1.0,
                end_sec=1.0,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=3)

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (31, "あ", 0.35),
                (34, "あ", 0.0),
            ],
        )

    def test_peak_fallback_closing_hold_adds_hold_before_final_closing_edge(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.0,
                start_sec=1.0,
                end_sec=1.0,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_hold_frames=3)

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (33, "あ", 0.5),
                (34, "あ", 0.0),
            ],
        )

    def test_peak_fallback_closing_hold_and_softness_apply_in_order(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.0,
                start_sec=1.0,
                end_sec=1.0,
            )
        ]

        frames = _build_interval_morph_frames(
            points,
            closing_hold_frames=3,
            closing_softness_frames=2,
        )

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (33, "あ", 0.5),
                (34, "あ", 0.35),
                (36, "あ", 0.0),
            ],
        )

    def test_peak_fallback_closing_softness_clamps_before_following_shape_start(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.0,
                start_sec=1.0,
                end_sec=1.0,
            ),
            VowelTimelinePoint(
                time_sec=34 / 30,
                vowel="あ",
                duration_sec=0.0,
                start_sec=34 / 30,
                end_sec=34 / 30,
            ),
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=10)

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (31, "あ", 0.35),
                (32, "あ", 0.0),
                (33, "あ", 0.0),
                (34, "あ", 0.5),
                (35, "あ", 0.35),
                (45, "あ", 0.0),
            ],
        )

    def test_ms11_2_closing_softness_inserts_midpoint_before_end_zero(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=3)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.5),
                (33, "あ", 0.5),
                (34, "あ", 0.35),
                (37, "あ", 0.0),
            ],
        )

    def test_ms11_2_closing_hold_keeps_top_then_drops_to_zero(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_hold_frames=3)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.5),
                (36, "あ", 0.5),
                (37, "あ", 0.0),
            ],
        )

    def test_legacy_triangle_closing_softness_adds_70_percent_midpoint(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.099,
                start_sec=0.95,
                end_sec=1.049,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=3)

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (31, "あ", 0.35),
                (34, "あ", 0.0),
            ],
        )

    def test_legacy_triangle_closing_hold_adds_plateau_before_end_zero(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.099,
                start_sec=0.95,
                end_sec=1.049,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_hold_frames=3)

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (33, "あ", 0.5),
                (34, "あ", 0.0),
            ],
        )

    def test_legacy_symmetric_trapezoid_closing_softness_adds_midpoint(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=31 / 30,
                vowel="あ",
                duration_sec=(34 - 30) / 30,
                start_sec=30 / 30,
                end_sec=34 / 30,
            )
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=3)

        self.assertEqual(
            frames,
            [
                (30, "あ", 0.0),
                (31, "あ", 0.5),
                (32, "あ", 0.5),
                (33, "あ", 0.35),
                (36, "あ", 0.0),
            ],
        )

    def test_closing_softness_clamps_before_following_shape_start(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            ),
            VowelTimelinePoint(
                time_sec=1.25,
                vowel="あ",
                duration_sec=0.099,
                start_sec=1.22,
                end_sec=1.319,
            ),
        ]

        frames = _build_interval_morph_frames(points, closing_softness_frames=3)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.5),
                (33, "あ", 0.5),
                (34, "あ", 0.35),
                (36, "あ", 0.0),
                (37, "あ", 0.0),
                (38, "あ", 0.5),
                (39, "あ", 0.35),
                (42, "あ", 0.0),
            ],
        )

    def test_zero_peak_event_is_not_used_as_clamp_blocker(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.0,
                start_sec=1.0,
                end_sec=1.0,
                peak_value=0.5,
                value=0.5,
            ),
            VowelTimelinePoint(
                time_sec=34 / 30,
                vowel="あ",
                duration_sec=0.0,
                start_sec=34 / 30,
                end_sec=34 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=50 / 30,
                vowel="い",
                duration_sec=0.0,
                start_sec=50 / 30,
                end_sec=50 / 30,
                peak_value=0.5,
                value=0.5,
            ),
        ]

        frames = _build_interval_morph_frames(
            points,
            closing_hold_frames=3,
            closing_softness_frames=4,
        )

        self.assertEqual(
            frames,
            [
                (28, "あ", 0.0),
                (30, "あ", 0.5),
                (33, "あ", 0.5),
                (34, "あ", 0.35),
                (38, "あ", 0.0),
                (48, "い", 0.0),
                (50, "い", 0.5),
                (53, "い", 0.5),
                (54, "い", 0.35),
                (58, "い", 0.0),
            ],
        )

    def test_same_vowel_bridge_candidate_is_skipped_from_grouping_and_produces_multi_point_shape(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
                peak_value=0.4,
                value=0.4,
            ),
            VowelTimelinePoint(
                time_sec=37 / 30,
                vowel="あ",
                duration_sec=1 / 30,
                start_sec=37 / 30,
                end_sec=38 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=1.3,
                vowel="あ",
                duration_sec=0.4,
                start_sec=1.1,
                end_sec=1.5,
                peak_value=0.3,
                value=0.3,
            ),
        ]
        observations = [
            SimpleNamespace(
                event_index=0,
                is_bridgeable_micro_gap_candidate=False,
                previous_non_zero_event_index=None,
                next_non_zero_event_index=2,
            ),
            SimpleNamespace(
                event_index=1,
                is_bridgeable_micro_gap_candidate=True,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=2,
            ),
            SimpleNamespace(
                event_index=2,
                is_bridgeable_micro_gap_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=None,
            ),
        ]

        frames = _build_interval_morph_frames(points, observations=observations)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (30, "あ", 0.4),
                (34, "あ", 0.105),
                (39, "あ", 0.3),
                (45, "あ", 0.0),
            ],
        )

    def test_cross_vowel_transition_candidate_extends_previous_end_and_advances_next_start(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
                peak_value=0.4,
                value=0.4,
            ),
            VowelTimelinePoint(
                time_sec=37 / 30,
                vowel="あ",
                duration_sec=1 / 30,
                start_sec=37 / 30,
                end_sec=38 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=1.3,
                vowel="い",
                duration_sec=7 / 30,
                start_sec=38 / 30,
                end_sec=45 / 30,
                peak_value=0.35,
                value=0.35,
            ),
        ]
        observations = [
            SimpleNamespace(
                event_index=0,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=None,
                next_non_zero_event_index=2,
            ),
            SimpleNamespace(
                event_index=1,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=True,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=2,
            ),
            SimpleNamespace(
                event_index=2,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=None,
            ),
        ]

        frames = _build_interval_morph_frames(points, observations=observations)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.4),
                (33, "あ", 0.4),
                (35, "あ", 0.0),
                (37, "あ", 0.1),
                (37, "い", 0.0),
                (38, "あ", 0.0),
                (38, "い", 0.35),
                (39, "あ", 0.0),
                (40, "い", 0.35),
                (45, "い", 0.0),
            ],
        )

    def test_same_vowel_two_zero_span_inserts_bridge_top_and_produces_multi_valley_shape(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=13 / 30,
                start_sec=24 / 30,
                end_sec=37 / 30,
                peak_value=0.4,
                value=0.4,
            ),
            VowelTimelinePoint(
                time_sec=37 / 30,
                vowel="あ",
                duration_sec=1 / 30,
                start_sec=37 / 30,
                end_sec=38 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=38 / 30,
                vowel="あ",
                duration_sec=1 / 30,
                start_sec=38 / 30,
                end_sec=39 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=42 / 30,
                vowel="あ",
                duration_sec=9 / 30,
                start_sec=39 / 30,
                end_sec=48 / 30,
                peak_value=0.3,
                value=0.3,
            ),
        ]
        observations = [
            SimpleNamespace(
                event_index=0,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=None,
                next_non_zero_event_index=3,
            ),
            SimpleNamespace(
                event_index=1,
                is_bridgeable_micro_gap_candidate=True,
                is_bridgeable_same_vowel_micro_gap_candidate=True,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=3,
                span_start_index=1,
                span_end_index=2,
            ),
            SimpleNamespace(
                event_index=2,
                is_bridgeable_micro_gap_candidate=True,
                is_bridgeable_same_vowel_micro_gap_candidate=True,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=3,
                span_start_index=1,
                span_end_index=2,
            ),
            SimpleNamespace(
                event_index=3,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=None,
            ),
        ]

        frames = _build_interval_morph_frames(points, observations=observations)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (30, "あ", 0.4),
                (34, "あ", 0.08399999999999999),
                (38, "あ", 0.24),
                (40, "あ", 0.08399999999999999),
                (42, "あ", 0.3),
                (48, "あ", 0.0),
            ],
        )

    def test_same_vowel_low_positive_short_segment_is_absorbed_as_burst(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="う",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
                peak_value=0.4,
                value=0.4,
            ),
            VowelTimelinePoint(
                time_sec=37 / 30,
                vowel="う",
                duration_sec=1 / 30,
                start_sec=37 / 30,
                end_sec=38 / 30,
                peak_value=0.12,
                value=0.12,
            ),
            VowelTimelinePoint(
                time_sec=1.3,
                vowel="う",
                duration_sec=0.4,
                start_sec=1.1,
                end_sec=1.5,
                peak_value=0.3,
                value=0.3,
            ),
        ]
        observations = [
            SimpleNamespace(
                event_index=0,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_same_vowel_burst_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=None,
                next_non_zero_event_index=2,
            ),
            SimpleNamespace(
                event_index=1,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_same_vowel_burst_candidate=True,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=2,
                span_start_index=1,
                span_end_index=1,
            ),
            SimpleNamespace(
                event_index=2,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_same_vowel_burst_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=None,
            ),
        ]

        frames = _build_interval_morph_frames(points, observations=observations)

        self.assertEqual(
            frames,
            [
                (24, "う", 0.0),
                (30, "う", 0.4),
                (34, "う", 0.105),
                (39, "う", 0.3),
                (45, "う", 0.0),
            ],
        )

    def test_cross_vowel_two_zero_span_extends_previous_end_to_span_end_and_next_start_to_span_start(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=13 / 30,
                start_sec=24 / 30,
                end_sec=37 / 30,
                peak_value=0.4,
                value=0.4,
            ),
            VowelTimelinePoint(
                time_sec=37 / 30,
                vowel="い",
                duration_sec=1 / 30,
                start_sec=37 / 30,
                end_sec=38 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=38 / 30,
                vowel="う",
                duration_sec=1 / 30,
                start_sec=38 / 30,
                end_sec=39 / 30,
                peak_value=0.0,
                value=0.0,
            ),
            VowelTimelinePoint(
                time_sec=42 / 30,
                vowel="い",
                duration_sec=9 / 30,
                start_sec=39 / 30,
                end_sec=48 / 30,
                peak_value=0.35,
                value=0.35,
            ),
        ]
        observations = [
            SimpleNamespace(
                event_index=0,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=None,
                next_non_zero_event_index=3,
            ),
            SimpleNamespace(
                event_index=1,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                is_cross_vowel_zero_run_continuity_floor_candidate=True,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=3,
                span_start_index=1,
                span_end_index=2,
            ),
            SimpleNamespace(
                event_index=2,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                is_cross_vowel_zero_run_continuity_floor_candidate=True,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=3,
                span_start_index=1,
                span_end_index=2,
            ),
            SimpleNamespace(
                event_index=3,
                is_bridgeable_micro_gap_candidate=False,
                is_bridgeable_same_vowel_micro_gap_candidate=False,
                is_bridgeable_cross_vowel_transition_candidate=False,
                previous_non_zero_event_index=0,
                next_non_zero_event_index=None,
            ),
        ]

        frames = _build_interval_morph_frames(points, observations=observations)

        self.assertEqual(
            frames,
            [
                (24, "あ", 0.0),
                (27, "あ", 0.4),
                (33, "あ", 0.4),
                (35, "い", 0.0),
                (36, "う", 0.0),
                (37, "あ", 0.0),
                (37, "い", 0.1),
                (38, "う", 0.1),
                (39, "い", 0.0),
                (39, "い", 0.0),
                (40, "う", 0.0),
                (41, "い", 0.35),
                (43, "い", 0.35),
                (48, "い", 0.0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
