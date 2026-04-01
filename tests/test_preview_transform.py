from dataclasses import dataclass
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui.preview_transform import PREVIEW_ROW_VOWELS, build_preview_data


@dataclass
class DummyTimelinePoint:
    vowel: str
    time_sec: float
    duration_sec: float
    start_sec: float | None
    end_sec: float | None
    peak_value: float | None
    value: float


@dataclass
class DummyObservation:
    event_index: int
    is_bridgeable_micro_gap_candidate: bool
    is_bridgeable_same_vowel_micro_gap_candidate: bool = False
    is_same_vowel_burst_candidate: bool = False
    is_bridgeable_cross_vowel_transition_candidate: bool = False
    is_cross_vowel_zero_run_continuity_floor_candidate: bool = False
    local_peak: float | None = None
    previous_non_zero_event_index: int | None = None
    next_non_zero_event_index: int | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None
    rms_window_times_sec: tuple[float, ...] = ()
    rms_window_values: tuple[float, ...] = ()


class PreviewTransformTests(unittest.TestCase):
    def test_empty_input_returns_fixed_five_rows(self) -> None:
        preview_data = build_preview_data(None)

        self.assertEqual([row.vowel for row in preview_data.rows], list(PREVIEW_ROW_VOWELS))
        self.assertTrue(all(len(row.segments) == 0 for row in preview_data.rows))

    def test_vowels_are_grouped_into_fixed_rows_only(self) -> None:
        timeline = [
            DummyTimelinePoint(
                vowel="あ",
                time_sec=0.2,
                duration_sec=0.1,
                start_sec=0.15,
                end_sec=0.25,
                peak_value=0.4,
                value=0.1,
            ),
            DummyTimelinePoint(
                vowel="お",
                time_sec=1.0,
                duration_sec=0.2,
                start_sec=0.9,
                end_sec=1.1,
                peak_value=0.7,
                value=0.3,
            ),
            DummyTimelinePoint(
                vowel="x",
                time_sec=1.5,
                duration_sec=0.2,
                start_sec=1.4,
                end_sec=1.6,
                peak_value=0.5,
                value=0.5,
            ),
        ]

        preview_data = build_preview_data(timeline)
        row_map = {row.vowel: row for row in preview_data.rows}

        self.assertEqual(len(row_map["あ"].segments), 1)
        self.assertEqual(len(row_map["お"].segments), 1)
        self.assertEqual(len(row_map["い"].segments), 0)
        self.assertEqual(len(row_map["う"].segments), 0)
        self.assertEqual(len(row_map["え"].segments), 0)

    def test_intensity_uses_peak_then_value_then_zero_and_caps_at_one(self) -> None:
        timeline = [
            DummyTimelinePoint(
                vowel="あ",
                time_sec=0.1,
                duration_sec=0.1,
                start_sec=0.0,
                end_sec=0.1,
                peak_value=1.7,
                value=0.2,
            ),
            DummyTimelinePoint(
                vowel="い",
                time_sec=0.2,
                duration_sec=0.1,
                start_sec=0.1,
                end_sec=0.2,
                peak_value=None,
                value=0.6,
            ),
            DummyTimelinePoint(
                vowel="う",
                time_sec=0.3,
                duration_sec=0.1,
                start_sec=0.2,
                end_sec=0.3,
                peak_value=None,
                value=float("nan"),
            ),
        ]

        preview_data = build_preview_data(timeline)
        row_map = {row.vowel: row for row in preview_data.rows}

        self.assertEqual(row_map["あ"].segments[0].intensity, 1.0)
        self.assertEqual(row_map["い"].segments[0].intensity, 0.6)
        self.assertEqual(len(row_map["う"].segments), 0)

    def test_ms11_2_trapezoid_segment_uses_four_control_points(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ]
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_2_asymmetric_trapezoid")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 27, 33, 36),
        )
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "top", "end_zero"),
        )

    def test_trapezoid_preview_uses_decayed_peak_end_value_from_observation(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            observations=[
                DummyObservation(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    local_peak=1.0,
                    rms_window_times_sec=(1.09, 1.2),
                    rms_window_values=(1.0, 0.3),
                )
            ],
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.5, 0.15, 0.0),
        )

    def test_trapezoid_preview_top_end_is_slightly_lowered_when_following_rms_is_lower(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            observations=[
                DummyObservation(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    local_peak=1.0,
                    rms_window_times_sec=(1.09, 1.1, 1.2),
                    rms_window_values=(1.0, 0.8, 0.4),
                )
            ],
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.5, 0.35, 0.0),
        )

    def test_trapezoid_preview_top_end_drop_is_softened_when_following_rms_recovers(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            observations=[
                DummyObservation(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    local_peak=1.0,
                    rms_window_times_sec=(1.09, 1.1, 1.2),
                    rms_window_values=(1.0, 0.1, 0.5),
                )
            ],
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.5, 0.1, 0.0),
        )

    def test_zero_peak_cross_vowel_candidate_uses_continuity_floor_in_preview(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="い",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.0,
                    value=0.0,
                )
            ],
            observations=[
                DummyObservation(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    is_bridgeable_cross_vowel_transition_candidate=True,
                )
            ],
        )

        segment = preview_data.rows[1].segments[0]
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.1, 0.1, 0.0),
        )

    def test_legacy_triangle_and_symmetric_trapezoid_are_distinguished(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.099,
                    start_sec=0.95,
                    end_sec=1.049,
                    peak_value=0.5,
                    value=0.5,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=31 / 30,
                    duration_sec=(34 - 30) / 30,
                    start_sec=30 / 30,
                    end_sec=34 / 30,
                    peak_value=0.5,
                    value=0.5,
                ),
            ]
        )

        segment_kinds = tuple(segment.shape_kind for segment in preview_data.rows[0].segments)
        self.assertEqual(
            segment_kinds,
            ("legacy_triangle", "legacy_symmetric_trapezoid"),
        )

    def test_multi_point_segment_exposes_valley_and_multiple_tops(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.30,
                    duration_sec=0.4,
                    start_sec=1.10,
                    end_sec=1.50,
                    peak_value=0.30,
                    value=0.30,
                ),
            ]
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_3_multi_point_envelope")
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "valley", "top", "end_zero"),
        )
        valley_point = segment.control_points[2]
        self.assertGreater(valley_point.value, 0.0)
        self.assertLess(valley_point.value, segment.control_points[1].value)

    def test_closing_softness_adds_midpoint_for_trapezoid(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            closing_softness_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 27, 33, 38, 39),
        )
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "top", "slope_mid", "end_zero"),
        )

    def test_closing_hold_extends_final_non_zero_and_end_zero_for_trapezoid(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            closing_hold_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 27, 33, 38, 39),
        )

    def test_closing_hold_preview_preserves_decayed_peak_end_value_for_trapezoid(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            observations=[
                DummyObservation(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    local_peak=1.0,
                    rms_window_times_sec=(1.09, 1.2),
                    rms_window_values=(1.0, 0.3),
                )
            ],
            closing_hold_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.5, 0.15, 0.15, 0.0),
        )

    def test_closing_softness_preview_uses_decayed_peak_end_value_for_midpoint(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            observations=[
                DummyObservation(
                    event_index=0,
                    is_bridgeable_micro_gap_candidate=False,
                    local_peak=1.0,
                    rms_window_times_sec=(1.09, 1.2),
                    rms_window_values=(1.0, 0.3),
                )
            ],
            closing_softness_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.5, 0.15, 0.105, 0.0),
        )

    def test_closing_hold_does_not_change_non_final_preview_interval_width(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.4,
                    start_sec=0.8,
                    end_sec=1.2,
                    peak_value=0.5,
                    value=0.5,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.5,
                    duration_sec=0.4,
                    start_sec=1.3,
                    end_sec=1.7,
                    peak_value=0.5,
                    value=0.5,
                ),
            ],
            closing_hold_frames=3,
        )

        self.assertEqual(len(preview_data.rows[0].segments), 1)
        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 37, 45, 53, 54),
        )

    def test_closing_softness_adds_final_midpoint_for_multi_point(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.30,
                    duration_sec=0.4,
                    start_sec=1.10,
                    end_sec=1.50,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            closing_softness_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 34, 39, 47, 48),
        )
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "valley", "top", "slope_mid", "end_zero"),
        )

    def test_closing_hold_adds_final_hold_point_for_multi_point(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.30,
                    duration_sec=0.4,
                    start_sec=1.10,
                    end_sec=1.50,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            closing_hold_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 34, 39, 47, 48),
        )

    def test_peak_fallback_closing_softness_adds_midpoint(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.0,
                    start_sec=1.0,
                    end_sec=1.0,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            closing_softness_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "peak_fallback")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (28, 30, 34, 35),
        )
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "slope_mid", "end_zero"),
        )

    def test_peak_fallback_closing_hold_adds_hold_top_before_final_end_zero(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.0,
                    start_sec=1.0,
                    end_sec=1.0,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            closing_hold_frames=3,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "peak_fallback")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (28, 30, 34, 35),
        )
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "top", "end_zero"),
        )

    def test_peak_fallback_hold_and_softness_apply_in_order(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.0,
                    start_sec=1.0,
                    end_sec=1.0,
                    peak_value=0.5,
                    value=0.5,
                )
            ],
            closing_hold_frames=3,
            closing_softness_frames=2,
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (28, 30, 34, 36, 37),
        )
        self.assertEqual(
            tuple(point.point_kind for point in segment.control_points),
            ("start_zero", "top", "top", "slope_mid", "end_zero"),
        )

    def test_peak_fallback_closing_softness_uses_available_extension_before_following_shape(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.0,
                    start_sec=1.0,
                    end_sec=1.0,
                    peak_value=0.5,
                    value=0.5,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=34 / 30,
                    duration_sec=0.0,
                    start_sec=34 / 30,
                    end_sec=34 / 30,
                    peak_value=0.5,
                    value=0.5,
                ),
            ],
            closing_softness_frames=10,
        )

        segments = preview_data.rows[0].segments
        self.assertEqual(len(segments), 2)
        self.assertEqual(
            tuple(point.frame_no for point in segments[0].control_points),
            (28, 30, 32, 33),
        )
        self.assertEqual(
            tuple(point.frame_no for point in segments[1].control_points),
            (32, 34, 45, 46),
        )

    def test_zero_peak_event_is_not_used_as_preview_clamp_blocker(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.0,
                    duration_sec=0.0,
                    start_sec=1.0,
                    end_sec=1.0,
                    peak_value=0.5,
                    value=0.5,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=34 / 30,
                    duration_sec=0.0,
                    start_sec=34 / 30,
                    end_sec=34 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="い",
                    time_sec=50 / 30,
                    duration_sec=0.0,
                    start_sec=50 / 30,
                    end_sec=50 / 30,
                    peak_value=0.5,
                    value=0.5,
                ),
            ],
            closing_hold_frames=3,
            closing_softness_frames=4,
        )

        row_map = {row.vowel: row for row in preview_data.rows}
        self.assertEqual(
            tuple(point.frame_no for point in row_map["あ"].segments[0].control_points),
            (28, 30, 34, 38, 39),
        )
        self.assertEqual(
            tuple(point.frame_no for point in row_map["い"].segments[0].control_points),
            (48, 50, 54, 58, 59),
        )

    def test_closing_softness_uses_only_available_extension_even_in_mixed_case(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.30,
                    duration_sec=0.4,
                    start_sec=1.10,
                    end_sec=1.50,
                    peak_value=0.30,
                    value=0.30,
                ),
                DummyTimelinePoint(
                    vowel="い",
                    time_sec=1.55,
                    duration_sec=0.1,
                    start_sec=1.52,
                    end_sec=1.62,
                    peak_value=0.50,
                    value=0.50,
                ),
            ],
            closing_softness_frames=10,
        )

        row_map = {row.vowel: row for row in preview_data.rows}
        self.assertEqual(
            tuple(point.frame_no for point in row_map["あ"].segments[0].control_points),
            (24, 30, 34, 39, 45),
        )
        self.assertEqual(len(row_map["い"].segments), 1)
        self.assertGreaterEqual(row_map["い"].segments[0].start_sec, 45 / 30)

    def test_same_vowel_bridge_candidate_uses_multi_point_preview_shape(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=37 / 30,
                    duration_sec=1 / 30,
                    start_sec=37 / 30,
                    end_sec=38 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.30,
                    duration_sec=0.4,
                    start_sec=1.10,
                    end_sec=1.50,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, next_non_zero_event_index=2),
                DummyObservation(event_index=1, is_bridgeable_micro_gap_candidate=True, previous_non_zero_event_index=0, next_non_zero_event_index=2),
                DummyObservation(event_index=2, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0),
            ],
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_3_multi_point_envelope")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 33, 37, 39),
        )
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.4, 0.06824999999999999, 0.195, 0.0),
        )

    def test_cross_vowel_transition_candidate_shifts_preview_boundaries_without_same_vowel_grouping(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=37 / 30,
                    duration_sec=1 / 30,
                    start_sec=37 / 30,
                    end_sec=38 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="い",
                    time_sec=1.30,
                    duration_sec=7 / 30,
                    start_sec=38 / 30,
                    end_sec=45 / 30,
                    peak_value=0.35,
                    value=0.35,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, next_non_zero_event_index=2),
                DummyObservation(
                    event_index=1,
                    is_bridgeable_micro_gap_candidate=False,
                    is_bridgeable_cross_vowel_transition_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=2,
                ),
                DummyObservation(event_index=2, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0),
            ],
        )

        row_map = {row.vowel: row for row in preview_data.rows}
        a_segment = row_map["あ"].segments[0]
        i_segment = row_map["い"].segments[0]

        self.assertEqual(a_segment.shape_kind, "ms11_2_asymmetric_trapezoid")
        self.assertEqual(i_segment.shape_kind, "ms11_2_asymmetric_trapezoid")
        self.assertEqual(
            tuple(point.frame_no for point in a_segment.control_points),
            (24, 27, 33, 38),
        )
        self.assertEqual(
            tuple(point.frame_no for point in i_segment.control_points),
            (37, 38, 40, 45),
        )

    def test_same_vowel_two_zero_span_uses_multi_valley_preview_shape(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=13 / 30,
                    start_sec=24 / 30,
                    end_sec=37 / 30,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=37 / 30,
                    duration_sec=1 / 30,
                    start_sec=37 / 30,
                    end_sec=38 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=38 / 30,
                    duration_sec=1 / 30,
                    start_sec=38 / 30,
                    end_sec=39 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=42 / 30,
                    duration_sec=9 / 30,
                    start_sec=39 / 30,
                    end_sec=48 / 30,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, next_non_zero_event_index=3),
                DummyObservation(
                    event_index=1,
                    is_bridgeable_micro_gap_candidate=True,
                    is_bridgeable_same_vowel_micro_gap_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=3,
                    span_start_index=1,
                    span_end_index=2,
                ),
                DummyObservation(
                    event_index=2,
                    is_bridgeable_micro_gap_candidate=True,
                    is_bridgeable_same_vowel_micro_gap_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=3,
                    span_start_index=1,
                    span_end_index=2,
                ),
                DummyObservation(event_index=3, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0),
            ],
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_3_multi_point_envelope")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 34, 38, 40, 42, 48),
        )
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.4, 0.06824999999999999, 0.195, 0.06824999999999999, 0.3, 0.0),
        )

    def test_same_vowel_low_positive_short_segment_uses_burst_smoothed_preview_shape(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=1.00,
                    duration_sec=0.4,
                    start_sec=0.80,
                    end_sec=1.20,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=37 / 30,
                    duration_sec=1 / 30,
                    start_sec=37 / 30,
                    end_sec=38 / 30,
                    peak_value=0.12,
                    value=0.12,
                ),
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=1.30,
                    duration_sec=0.4,
                    start_sec=1.10,
                    end_sec=1.50,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, next_non_zero_event_index=2),
                DummyObservation(
                    event_index=1,
                    is_bridgeable_micro_gap_candidate=False,
                    is_same_vowel_burst_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=2,
                    span_start_index=1,
                    span_end_index=1,
                ),
                DummyObservation(event_index=2, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0),
            ],
        )

        segment = preview_data.rows[2].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_3_multi_point_envelope")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 33, 37, 39),
        )
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.4, 0.05, 0.12, 0.0),
        )

    def test_same_vowel_low_positive_and_zero_span_uses_smoothed_sub_peak_preview_shape(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=1.00,
                    duration_sec=13 / 30,
                    start_sec=24 / 30,
                    end_sec=37 / 30,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=37 / 30,
                    duration_sec=1 / 30,
                    start_sec=37 / 30,
                    end_sec=38 / 30,
                    peak_value=0.12,
                    value=0.12,
                ),
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=38 / 30,
                    duration_sec=1 / 30,
                    start_sec=38 / 30,
                    end_sec=39 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=42 / 30,
                    duration_sec=9 / 30,
                    start_sec=39 / 30,
                    end_sec=48 / 30,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=None, next_non_zero_event_index=3),
                DummyObservation(
                    event_index=1,
                    is_bridgeable_micro_gap_candidate=False,
                    is_same_vowel_burst_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=3,
                    span_start_index=1,
                    span_end_index=2,
                ),
                DummyObservation(
                    event_index=2,
                    is_bridgeable_micro_gap_candidate=False,
                    is_same_vowel_burst_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=3,
                    span_start_index=1,
                    span_end_index=2,
                ),
                DummyObservation(event_index=3, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0, next_non_zero_event_index=None),
            ],
        )

        segment = preview_data.rows[2].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_3_multi_point_envelope")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 33, 37, 39, 42, 48),
        )
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.4, 0.05, 0.12, 0.05, 0.3, 0.0),
        )

    def test_same_vowel_single_zero_span_uses_bridge_preview_shape(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=13 / 30,
                    start_sec=24 / 30,
                    end_sec=37 / 30,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=37 / 30,
                    duration_sec=8 / 30,
                    start_sec=30 / 30,
                    end_sec=38 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=42 / 30,
                    duration_sec=9 / 30,
                    start_sec=39 / 30,
                    end_sec=48 / 30,
                    peak_value=0.30,
                    value=0.30,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=None, next_non_zero_event_index=2),
                DummyObservation(
                    event_index=1,
                    is_bridgeable_micro_gap_candidate=True,
                    is_bridgeable_same_vowel_micro_gap_candidate=True,
                    is_same_vowel_burst_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=2,
                    span_start_index=1,
                    span_end_index=1,
                ),
                DummyObservation(event_index=2, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0, next_non_zero_event_index=None),
            ],
        )

        segment = preview_data.rows[0].segments[0]
        self.assertEqual(segment.shape_kind, "ms11_3_multi_point_envelope")
        self.assertEqual(
            tuple(point.frame_no for point in segment.control_points),
            (24, 30, 33, 37, 39, 42, 48),
        )
        self.assertEqual(
            tuple(point.value for point in segment.control_points),
            (0.0, 0.4, 0.06824999999999999, 0.195, 0.06824999999999999, 0.3, 0.0),
        )

    def test_cross_vowel_two_zero_span_shifts_preview_boundaries(self) -> None:
        preview_data = build_preview_data(
            [
                DummyTimelinePoint(
                    vowel="あ",
                    time_sec=1.00,
                    duration_sec=13 / 30,
                    start_sec=24 / 30,
                    end_sec=37 / 30,
                    peak_value=0.40,
                    value=0.40,
                ),
                DummyTimelinePoint(
                    vowel="い",
                    time_sec=37 / 30,
                    duration_sec=1 / 30,
                    start_sec=37 / 30,
                    end_sec=38 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="う",
                    time_sec=38 / 30,
                    duration_sec=1 / 30,
                    start_sec=38 / 30,
                    end_sec=39 / 30,
                    peak_value=0.0,
                    value=0.0,
                ),
                DummyTimelinePoint(
                    vowel="い",
                    time_sec=42 / 30,
                    duration_sec=9 / 30,
                    start_sec=39 / 30,
                    end_sec=48 / 30,
                    peak_value=0.35,
                    value=0.35,
                ),
            ],
            observations=[
                DummyObservation(event_index=0, is_bridgeable_micro_gap_candidate=False, next_non_zero_event_index=3),
                DummyObservation(
                    event_index=1,
                    is_bridgeable_micro_gap_candidate=False,
                    is_bridgeable_cross_vowel_transition_candidate=False,
                    is_cross_vowel_zero_run_continuity_floor_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=3,
                    span_start_index=1,
                    span_end_index=2,
                ),
                DummyObservation(
                    event_index=2,
                    is_bridgeable_micro_gap_candidate=False,
                    is_bridgeable_cross_vowel_transition_candidate=False,
                    is_cross_vowel_zero_run_continuity_floor_candidate=True,
                    previous_non_zero_event_index=0,
                    next_non_zero_event_index=3,
                    span_start_index=1,
                    span_end_index=2,
                ),
                DummyObservation(event_index=3, is_bridgeable_micro_gap_candidate=False, previous_non_zero_event_index=0),
            ],
        )

        row_map = {row.vowel: row for row in preview_data.rows}
        a_segment = row_map["あ"].segments[0]
        i_floor_segment = row_map["い"].segments[0]
        i_main_segment = row_map["い"].segments[1]
        u_floor_segment = row_map["う"].segments[0]
        self.assertEqual(
            tuple(point.frame_no for point in a_segment.control_points),
            (24, 27, 33, 37),
        )
        self.assertEqual(
            tuple(point.frame_no for point in i_floor_segment.control_points),
            (35, 37, 39),
        )
        self.assertEqual(
            tuple(point.frame_no for point in i_main_segment.control_points),
            (39, 41, 43, 48),
        )
        self.assertEqual(
            tuple(point.frame_no for point in u_floor_segment.control_points),
            (36, 38, 40),
        )


if __name__ == "__main__":
    unittest.main()
