import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import (
    _calculate_grouping_gap_sec,
    _group_nearby_same_vowel_events,
)


class VmdWriterGroupingTests(unittest.TestCase):
    def test_same_vowel_two_points_are_grouped(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", start_sec=0.90, end_sec=1.02),
            VowelTimelinePoint(time_sec=1.08, vowel="\u3042", start_sec=1.03, end_sec=1.16),
        ]

        grouped = _group_nearby_same_vowel_events(points)

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0].vowel, "\u3042")
        self.assertEqual(grouped[0].source_event_indices, (0, 1))
        self.assertEqual(tuple(point.time_sec for point in grouped[0].points), (1.00, 1.08))

    def test_same_vowel_three_points_are_grouped(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", start_sec=0.90, end_sec=1.02),
            VowelTimelinePoint(time_sec=1.08, vowel="\u3042", start_sec=1.03, end_sec=1.16),
            VowelTimelinePoint(time_sec=1.18, vowel="\u3042", start_sec=1.17, end_sec=1.28),
        ]

        grouped = _group_nearby_same_vowel_events(points)

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0].source_event_indices, (0, 1, 2))

    def test_gap_exceeded_splits_group(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", start_sec=0.90, end_sec=1.00),
            VowelTimelinePoint(time_sec=1.30, vowel="\u3042", start_sec=1.20, end_sec=1.40),
        ]

        gap_sec = _calculate_grouping_gap_sec(points[0], points[1])
        grouped = _group_nearby_same_vowel_events(points)

        self.assertGreater(gap_sec, 4.0 / 30.0)
        self.assertEqual(len(grouped), 2)
        self.assertEqual(grouped[0].source_event_indices, (0,))
        self.assertEqual(grouped[1].source_event_indices, (1,))

    def test_frame_based_lightweight_invalidity_splits_group(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.000, vowel="\u3042", start_sec=0.95, end_sec=1.04),
            VowelTimelinePoint(time_sec=1.010, vowel="\u3042", start_sec=0.96, end_sec=1.05),
        ]

        grouped = _group_nearby_same_vowel_events(points)

        self.assertEqual(len(grouped), 2)
        self.assertEqual(grouped[0].source_event_indices, (0,))
        self.assertEqual(grouped[1].source_event_indices, (1,))

    def test_different_vowels_are_not_grouped(self) -> None:
        points = [
            VowelTimelinePoint(time_sec=1.00, vowel="\u3042", start_sec=0.90, end_sec=1.02),
            VowelTimelinePoint(time_sec=1.08, vowel="\u3044", start_sec=1.03, end_sec=1.16),
        ]

        grouped = _group_nearby_same_vowel_events(points)

        self.assertEqual(len(grouped), 2)
        self.assertEqual(grouped[0].vowel, "\u3042")
        self.assertEqual(grouped[1].vowel, "\u3044")


if __name__ == "__main__":
    unittest.main()
