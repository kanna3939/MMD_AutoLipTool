import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import (
    _build_interval_morph_frames,
    _build_interval_morph_frames_with_metadata,
    _build_grouped_nearby_vowel_events,
    _build_multi_point_envelope_spec_from_group,
    _build_top_control_points_for_group,
    _compute_ms11_3_valley_value,
    _expand_multi_point_envelope_spec_to_morph_frames,
)


class VmdWriterMultiPointShapeTests(unittest.TestCase):
    def test_two_point_group_generates_multi_point_shape(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.30, start_sec=1.03, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )

        result = _build_multi_point_envelope_spec_from_group(grouped)

        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.spec)
        self.assertEqual(
            tuple(point.point_kind for point in result.spec.control_points),
            ("start_zero", "top", "valley", "top", "end_zero"),
        )

    def test_three_point_group_generates_shape_with_multiple_tops_and_valleys(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.30, start_sec=1.03, end_sec=1.16),
                VowelTimelinePoint(time_sec=1.18, vowel="\u3042", peak_value=0.35, start_sec=1.17, end_sec=1.28),
            ),
            source_event_indices=(0, 1, 2),
        )

        result = _build_multi_point_envelope_spec_from_group(grouped)

        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.spec)
        self.assertEqual(
            tuple(point.point_kind for point in result.spec.control_points),
            ("start_zero", "top", "valley", "top", "valley", "top", "end_zero"),
        )

    def test_peak_difference_is_reflected_in_top_heights(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.42, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.18, start_sec=1.03, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )

        top_points = _build_top_control_points_for_group(grouped)

        self.assertEqual(tuple(point.value for point in top_points), (0.42, 0.18))

    def test_valley_does_not_fall_to_zero(self) -> None:
        valley_value = _compute_ms11_3_valley_value(0.40, 0.30)

        self.assertIsNotNone(valley_value)
        self.assertGreater(valley_value, 0.0)
        self.assertGreaterEqual(valley_value, 0.05)

    def test_valley_condition_failure_returns_invalid_shape(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.05, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.05, start_sec=1.03, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )

        result = _build_multi_point_envelope_spec_from_group(grouped)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.failure_reason, "valley_generation_failed")

    def test_frame_order_breakage_returns_invalid_shape(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.000, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.05),
                VowelTimelinePoint(time_sec=1.010, vowel="\u3042", peak_value=0.30, start_sec=0.95, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )

        result = _build_multi_point_envelope_spec_from_group(grouped)

        self.assertFalse(result.is_valid)
        self.assertIn(
            result.failure_reason,
            {
                "valley_generation_failed",
                "control_points_collapsed_to_same_frame",
                "minimal_spec_invalid",
                "valley_not_between_adjacent_tops",
            },
        )

    def test_control_points_expand_to_morph_frames_with_boundary_zeros_and_non_zero_valley(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.30, start_sec=1.03, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )
        build_result = _build_multi_point_envelope_spec_from_group(grouped)

        self.assertTrue(build_result.is_valid)
        expansion_result = _expand_multi_point_envelope_spec_to_morph_frames(build_result.spec)

        self.assertTrue(expansion_result.is_valid)
        self.assertEqual(expansion_result.frames[0][2], 0.0)
        self.assertEqual(expansion_result.frames[-1][2], 0.0)
        self.assertTrue(all(frame[1] == "\u3042" for frame in expansion_result.frames))
        self.assertTrue(any(frame[2] > 0.0 and frame[2] < 0.30 for frame in expansion_result.frames))

    def test_three_top_shape_expands_to_distinct_frames(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.30, start_sec=1.03, end_sec=1.16),
                VowelTimelinePoint(time_sec=1.18, vowel="\u3042", peak_value=0.35, start_sec=1.17, end_sec=1.28),
            ),
            source_event_indices=(0, 1, 2),
        )
        build_result = _build_multi_point_envelope_spec_from_group(grouped)

        self.assertTrue(build_result.is_valid)
        expansion_result = _expand_multi_point_envelope_spec_to_morph_frames(build_result.spec)

        self.assertTrue(expansion_result.is_valid)
        self.assertEqual(len(expansion_result.frames), 7)
        self.assertEqual(
            tuple(frame_no for frame_no, _, _ in expansion_result.frames),
            tuple(sorted(frame_no for frame_no, _, _ in expansion_result.frames)),
        )

    def test_frame_order_breakage_causes_expansion_failure(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.30, start_sec=1.03, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )
        build_result = _build_multi_point_envelope_spec_from_group(grouped)
        broken_spec = build_result.spec.__class__(
            vowel=build_result.spec.vowel,
            control_points=tuple(reversed(build_result.spec.control_points)),
            source_event_indices=build_result.spec.source_event_indices,
            shape_kind=build_result.spec.shape_kind,
            protection_mode=build_result.spec.protection_mode,
            is_ms11_3_generated=build_result.spec.is_ms11_3_generated,
            event_ranges=build_result.spec.event_ranges,
        )

        expansion_result = _expand_multi_point_envelope_spec_to_morph_frames(broken_spec)

        self.assertFalse(expansion_result.is_valid)
        self.assertEqual(expansion_result.failure_reason, "control_point_frame_order_invalid")

    def test_same_frame_collision_causes_expansion_failure(self) -> None:
        grouped = _build_grouped_nearby_vowel_events(
            points=(
                VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.90, end_sec=1.02),
                VowelTimelinePoint(time_sec=1.08, vowel="\u3042", peak_value=0.30, start_sec=1.03, end_sec=1.16),
            ),
            source_event_indices=(0, 1),
        )
        build_result = _build_multi_point_envelope_spec_from_group(grouped)
        points = list(build_result.spec.control_points)
        points[1] = points[1].__class__(
            frame_no=points[0].frame_no,
            value=points[1].value,
            point_kind=points[1].point_kind,
        )
        broken_spec = build_result.spec.__class__(
            vowel=build_result.spec.vowel,
            control_points=tuple(points),
            source_event_indices=build_result.spec.source_event_indices,
            shape_kind=build_result.spec.shape_kind,
            protection_mode=build_result.spec.protection_mode,
            is_ms11_3_generated=build_result.spec.is_ms11_3_generated,
            event_ranges=build_result.spec.event_ranges,
        )

        expansion_result = _expand_multi_point_envelope_spec_to_morph_frames(broken_spec)

        self.assertFalse(expansion_result.is_valid)
        self.assertTrue(expansion_result.failure_reason.startswith("control_point_frame_collision:"))

    def test_interval_builder_uses_ms11_3_frames_when_multi_point_shape_is_valid(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.80, end_sec=1.20),
            VowelTimelinePoint(time_sec=1.30, vowel="\u3042", peak_value=0.30, start_sec=1.10, end_sec=1.50),
        ]

        frames, protected_specs = _build_interval_morph_frames_with_metadata(points)

        self.assertEqual(
            frames,
            [
                (24, "\u3042", 0.0),
                (30, "\u3042", 0.4),
                (34, "\u3042", 0.105),
                (39, "\u3042", 0.3),
                (45, "\u3042", 0.0),
            ],
        )
        self.assertEqual(protected_specs, [])

    def test_interval_builder_falls_back_to_ms11_2_when_ms11_3_shape_is_invalid(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.05, start_sec=0.80, end_sec=1.20),
            VowelTimelinePoint(time_sec=1.30, vowel="\u3042", peak_value=0.05, start_sec=1.22, end_sec=1.62),
        ]

        frames, protected_specs = _build_interval_morph_frames_with_metadata(points)

        self.assertEqual(
            frames,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.05),
                (33, "\u3042", 0.05),
                (36, "\u3042", 0.0),
                (37, "\u3042", 0.0),
                (38, "\u3042", 0.05),
                (40, "\u3042", 0.05),
                (49, "\u3042", 0.0),
            ],
        )
        self.assertEqual(
            tuple(spec.shape_kind for spec in protected_specs),
            ("ms11_2_asymmetric_trapezoid", "ms11_2_asymmetric_trapezoid"),
        )

    def test_interval_builder_falls_back_to_legacy_when_ms11_2_is_also_invalid(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.05, start_sec=0.98, end_sec=1.02),
            VowelTimelinePoint(time_sec=1.10, vowel="\u3042", peak_value=0.05, start_sec=1.08, end_sec=1.12),
        ]

        frames, protected_specs = _build_interval_morph_frames_with_metadata(points)

        self.assertEqual(
            frames,
            [
                (29, "\u3042", 0.0),
                (30, "\u3042", 0.05),
                (31, "\u3042", 0.0),
                (32, "\u3042", 0.0),
                (33, "\u3042", 0.05),
                (34, "\u3042", 0.0),
            ],
        )
        self.assertEqual(protected_specs, [])

    def test_short_interval_existing_fallback_remains_unchanged(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3042",
                duration_sec=0.099,
                start_sec=0.95,
                end_sec=1.049,
            )
        ]

        frames = _build_interval_morph_frames(points)

        self.assertEqual(
            frames,
            [
                (28, "\u3042", 0.0),
                (30, "\u3042", 0.5),
                (31, "\u3042", 0.0),
            ],
        )

    def test_interval_builder_keeps_ms11_3_success_and_fallback_shapes_in_mixed_case(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", peak_value=0.40, start_sec=0.80, end_sec=1.20),
            VowelTimelinePoint(time_sec=1.30, vowel="\u3042", peak_value=0.30, start_sec=1.10, end_sec=1.50),
            VowelTimelinePoint(time_sec=1.80, vowel="\u3044", peak_value=0.50, start_sec=1.78, end_sec=1.82),
        ]

        frames, protected_specs = _build_interval_morph_frames_with_metadata(points)

        self.assertEqual(
            frames,
            [
                (24, "\u3042", 0.0),
                (30, "\u3042", 0.4),
                (34, "\u3042", 0.105),
                (39, "\u3042", 0.3),
                (45, "\u3042", 0.0),
                (53, "\u3044", 0.0),
                (54, "\u3044", 0.5),
                (55, "\u3044", 0.0),
            ],
        )
        self.assertEqual(protected_specs, [])


if __name__ == "__main__":
    unittest.main()
