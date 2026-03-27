import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import (
    MORPH_FRAME_OPEN_EPSILON,
    _apply_final_morph_frame_normalization,
    _build_interval_morph_frames,
    _build_interval_morph_frames_with_metadata,
    _build_morph_frame_open_state,
    _detect_isolated_short_open_candidates,
    _detect_short_morph_pulse_candidates,
    _extract_mouth_open_intervals,
    _merge_duplicate_morph_frames,
    _normalize_isolated_short_open_segments,
    _normalize_short_morph_pulses,
    _prune_redundant_zero_morph_frames,
)


class VmdWriterZeroGuardTests(unittest.TestCase):
    def test_rise_start_zero_moves_back_one_frame_on_same_frame_collision(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3048",
                duration_sec=0.4,
                start_sec=1.0,
                end_sec=1.4,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (29, "\u3048", 0.0),
                (30, "\u3048", 0.5),
                (40, "\u3048", 0.5),
                (42, "\u3048", 0.0),
            ],
        )

    def test_frame_zero_collision_does_not_create_negative_frame(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=0.0,
                vowel="\u3048",
                duration_sec=0.2,
                start_sec=0.0,
                end_sec=0.2,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertTrue(all(frame_no >= 0 for frame_no, _, _ in frames))
        self.assertIn((0, "\u3048", 0.0), frames)
        self.assertIn((0, "\u3048", 0.5), frames)

    def test_duplicate_merge_prefers_non_zero_and_max_value(self) -> None:
        frames = [
            (52, "\u3042", 0.0),
            (52, "\u3042", 0.3968),
            (52, "\u3042", 0.2),
            (83, "\u3042", 0.0),
            (83, "\u3042", 0.0),
        ]

        merged = _merge_duplicate_morph_frames(frames)

        self.assertEqual(
            sorted(merged),
            [
                (52, "\u3042", 0.3968),
                (83, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_makes_morph_frame_keys_unique(self) -> None:
        frames = [
            (0, "\u3042", 0.0),
            (0, "\u3042", 0.5),
            (10, "\u3042", 0.2),
            (10, "\u3042", 0.4),
            (10, "\u3042", 0.0),
        ]

        normalized = _apply_final_morph_frame_normalization(frames)
        keys = [(frame_no, vowel) for frame_no, vowel, _ in normalized]

        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(
            normalized,
            [
                (0, "\u3042", 0.5),
                (10, "\u3042", 0.4),
            ],
        )

    def test_open_state_provides_per_vowel_values_and_max_open_value(self) -> None:
        frames = [
            (10, "\u3042", 0.4),
            (10, "\u3044", 0.25),
            (11, "\u3042", 0.0),
        ]

        open_state = _build_morph_frame_open_state(frames)

        self.assertEqual(open_state.value_at(10, "\u3042"), 0.4)
        self.assertEqual(open_state.value_at(10, "\u3044"), 0.25)
        self.assertEqual(open_state.value_at(10, "\u3046"), 0.0)
        self.assertEqual(open_state.open_value_at(10), 0.4)
        self.assertTrue(open_state.is_open_frame(10))
        self.assertTrue(open_state.is_closed_frame(11))

    def test_open_state_uses_epsilon_for_open_closed_queries(self) -> None:
        frames = [
            (20, "\u3042", MORPH_FRAME_OPEN_EPSILON),
            (21, "\u3042", MORPH_FRAME_OPEN_EPSILON * 2.0),
        ]

        open_state = _build_morph_frame_open_state(frames)

        self.assertTrue(open_state.is_closed_frame(20))
        self.assertFalse(open_state.is_open_frame(20))
        self.assertTrue(open_state.is_open_frame(21))
        self.assertFalse(open_state.is_closed_frame(21))

    def test_extract_mouth_open_intervals_groups_open_and_closed_ranges(self) -> None:
        frames = [
            (10, "\u3042", 0.0),
            (11, "\u3042", 0.3),
            (12, "\u3042", 0.25),
            (13, "\u3042", 0.0),
        ]

        open_state = _build_morph_frame_open_state(frames)
        intervals = _extract_mouth_open_intervals(open_state)

        self.assertEqual(
            [(interval.start_frame, interval.end_frame, interval.is_open) for interval in intervals],
            [
                (10, 10, False),
                (11, 12, True),
                (13, 13, False),
            ],
        )
        self.assertEqual(intervals[1].peak_open_value, 0.3)
        self.assertEqual(intervals[1].length_frames, 2)

    def test_detect_isolated_short_open_candidates_uses_global_open_state(self) -> None:
        frames = [
            (20, "\u3042", 0.0),
            (21, "\u3042", 0.35),
            (22, "\u3042", 0.0),
        ]

        open_state = _build_morph_frame_open_state(frames)
        candidates = _detect_isolated_short_open_candidates(open_state)

        self.assertEqual(len(candidates), 1)
        self.assertEqual((candidates[0].start_frame, candidates[0].end_frame), (21, 21))
        self.assertEqual(candidates[0].length_frames, 1)
        self.assertEqual(candidates[0].peak_open_value, 0.35)
        self.assertTrue(candidates[0].previous_interval_is_closed)
        self.assertTrue(candidates[0].next_interval_is_closed)

    def test_detect_isolated_short_open_candidates_does_not_misclassify_when_other_morph_is_open(self) -> None:
        frames = [
            (30, "\u3042", 0.0),
            (30, "\u3044", 0.25),
            (31, "\u3042", 0.2),
            (31, "\u3044", 0.25),
            (32, "\u3042", 0.0),
            (32, "\u3044", 0.25),
        ]

        open_state = _build_morph_frame_open_state(frames)
        candidates = _detect_isolated_short_open_candidates(open_state)

        self.assertEqual(candidates, [])

    def test_normalize_isolated_short_open_segments_zeroes_candidate_frames(self) -> None:
        frames = [
            (20, "\u3042", 0.0),
            (21, "\u3042", 0.35),
            (22, "\u3042", 0.0),
        ]

        open_state = _build_morph_frame_open_state(frames)
        normalized = _normalize_isolated_short_open_segments(frames, open_state)

        self.assertEqual(
            normalized,
            [
                (20, "\u3042", 0.0),
                (21, "\u3042", 0.0),
                (22, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_suppresses_isolated_short_open_candidate(self) -> None:
        frames = [
            (0, "\u3042", 0.0),
            (1, "\u3042", 0.3),
            (2, "\u3042", 0.0),
        ]

        normalized = _apply_final_morph_frame_normalization(frames)

        self.assertEqual(
            normalized,
            [
                (0, "\u3042", 0.0),
                (1, "\u3042", 0.0),
                (2, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_keeps_global_open_when_other_morph_sustains_mouth_open(self) -> None:
        frames = [
            (10, "\u3042", 0.0),
            (10, "\u3044", 0.25),
            (11, "\u3042", 0.2),
            (11, "\u3044", 0.25),
            (12, "\u3042", 0.0),
            (12, "\u3044", 0.25),
        ]

        normalized = _apply_final_morph_frame_normalization(frames)

        self.assertEqual(
            normalized,
            [
                (10, "\u3042", 0.0),
                (10, "\u3044", 0.25),
                (11, "\u3042", 0.0),
                (11, "\u3044", 0.25),
                (12, "\u3042", 0.0),
                (12, "\u3044", 0.25),
            ],
        )

    def test_detect_short_morph_pulse_candidates_when_global_open_stays_open(self) -> None:
        frames = [
            (40, "\u3044", 0.35),
            (41, "\u3042", 0.2),
            (41, "\u3044", 0.35),
            (42, "\u3044", 0.35),
        ]

        open_state = _build_morph_frame_open_state(frames)
        candidates = _detect_short_morph_pulse_candidates(open_state)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].vowel, "\u3042")
        self.assertEqual((candidates[0].start_frame, candidates[0].end_frame), (41, 41))

    def test_normalize_short_morph_pulses_zeroes_only_removable_morph_pulse(self) -> None:
        frames = [
            (40, "\u3044", 0.35),
            (41, "\u3042", 0.2),
            (41, "\u3044", 0.35),
            (42, "\u3044", 0.35),
        ]

        open_state = _build_morph_frame_open_state(frames)
        normalized = _normalize_short_morph_pulses(frames, open_state)

        self.assertEqual(
            normalized,
            [
                (40, "\u3044", 0.35),
                (41, "\u3042", 0.0),
                (41, "\u3044", 0.35),
                (42, "\u3044", 0.35),
            ],
        )

    def test_short_morph_pulse_is_not_removed_when_it_would_change_global_open_state(self) -> None:
        frames = [
            (50, "\u3042", 0.35),
            (51, "\u3042", 0.5),
            (52, "\u3042", 0.35),
        ]

        open_state = _build_morph_frame_open_state(frames)
        candidates = _detect_short_morph_pulse_candidates(open_state)
        normalized = _normalize_short_morph_pulses(frames, open_state)

        self.assertEqual(candidates, [])
        self.assertEqual(normalized, frames)

    def test_final_normalization_keeps_non_isolated_short_open_when_interval_is_long_enough(self) -> None:
        frames = [
            (60, "\u3042", 0.0),
            (61, "\u3042", 0.3),
            (62, "\u3042", 0.3),
            (63, "\u3042", 0.3),
            (64, "\u3042", 0.3),
            (65, "\u3042", 0.0),
        ]

        normalized = _apply_final_morph_frame_normalization(frames)

        self.assertEqual(normalized, frames)

    def test_final_normalization_merges_same_frame_collisions_caused_by_30fps_rounding(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=0.333,
                vowel="\u3042",
                peak_value=0.2,
                duration_sec=0.0,
                start_sec=0.333,
                end_sec=0.333,
            ),
            VowelTimelinePoint(
                time_sec=0.334,
                vowel="\u3042",
                peak_value=0.4,
                duration_sec=0.0,
                start_sec=0.334,
                end_sec=0.334,
            ),
        ]

        raw_frames = _build_interval_morph_frames(points)
        normalized = _apply_final_morph_frame_normalization(raw_frames)
        keys = [(frame_no, vowel) for frame_no, vowel, _ in normalized]

        self.assertGreater(len(raw_frames), len(set((frame_no, vowel) for frame_no, vowel, _ in raw_frames)))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(
            [(frame_no, vowel) for frame_no, vowel, _ in normalized],
            [
                (8, "\u3042"),
                (10, "\u3042"),
                (12, "\u3042"),
            ],
        )

    def test_final_normalization_keeps_valid_ms11_2_shape_when_protection_metadata_is_passed(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3042",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        raw_frames, protected_specs = _build_interval_morph_frames_with_metadata(points)
        normalized = _apply_final_morph_frame_normalization(
            raw_frames,
            protected_ms11_2_specs=protected_specs,
        )

        self.assertEqual(
            normalized,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.5),
                (33, "\u3042", 0.5),
                (36, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_still_suppresses_broken_short_shape_without_valid_ms11_2_top(self) -> None:
        frames = [
            (24, "\u3042", 0.0),
            (27, "\u3042", 0.5),
            (36, "\u3042", 0.0),
        ]

        normalized = _apply_final_morph_frame_normalization(frames)

        self.assertEqual(
            normalized,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.0),
                (36, "\u3042", 0.0),
            ],
        )

    def test_prune_redundant_zero_morph_frames_keeps_only_required_boundary_zeros(self) -> None:
        frames = [
            (24, "\u3042", 0.0),
            (27, "\u3042", 0.0),
            (33, "\u3042", 0.5),
            (36, "\u3042", 0.0),
        ]

        normalized = _prune_redundant_zero_morph_frames(
            frames,
            required_zero_frames={"\u3042": {24, 36}},
        )

        self.assertEqual(
            normalized,
            [
                (24, "\u3042", 0.0),
                (33, "\u3042", 0.5),
                (36, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_removes_non_zero_outside_allowed_ranges(self) -> None:
        frames = [
            (24, "\u3042", 0.0),
            (27, "\u3042", 0.5),
            (33, "\u3042", 0.5),
            (36, "\u3042", 0.0),
            (40, "\u3042", 0.2),
        ]

        normalized = _apply_final_morph_frame_normalization(
            frames,
            allowed_non_zero_ranges={"\u3042": [(24, 36)]},
            required_zero_frames={"\u3042": {24, 36}},
        )

        self.assertEqual(
            normalized,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.5),
                (33, "\u3042", 0.5),
                (36, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_keeps_short_fallback_peak_when_event_range_is_protected(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3042",
                duration_sec=0.099,
                start_sec=0.95,
                end_sec=1.049,
            )
        ]

        raw_frames, protected_specs = _build_interval_morph_frames_with_metadata(points)
        normalized = _apply_final_morph_frame_normalization(
            raw_frames,
            protected_ms11_2_specs=protected_specs,
            protected_event_ranges={"\u3042": [(28, 31)]},
            allowed_non_zero_ranges={"\u3042": [(28, 31)]},
            required_zero_frames={"\u3042": {28, 31}},
        )

        self.assertEqual(
            normalized,
            [
                (28, "\u3042", 0.0),
                (30, "\u3042", 0.5),
                (31, "\u3042", 0.0),
            ],
        )

    def test_final_normalization_keeps_nearby_fallback_peak_alongside_ms11_2_shape(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3048",
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            ),
            VowelTimelinePoint(
                time_sec=1.25,
                vowel="\u3048",
                duration_sec=0.099,
                start_sec=1.22,
                end_sec=1.319,
            ),
        ]

        raw_frames, protected_specs = _build_interval_morph_frames_with_metadata(points)
        normalized = _apply_final_morph_frame_normalization(
            raw_frames,
            protected_ms11_2_specs=protected_specs,
            protected_event_ranges={"\u3048": [(24, 36), (37, 40)]},
            allowed_non_zero_ranges={"\u3048": [(24, 36), (37, 40)]},
            required_zero_frames={"\u3048": {24, 36, 37, 40}},
        )

        self.assertEqual(
            normalized,
            [
                (24, "\u3048", 0.0),
                (27, "\u3048", 0.5),
                (33, "\u3048", 0.5),
                (36, "\u3048", 0.0),
                (37, "\u3048", 0.0),
                (38, "\u3048", 0.5),
                (40, "\u3048", 0.0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
