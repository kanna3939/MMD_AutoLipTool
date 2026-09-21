import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core.preview_transform import (
    PreviewControlPoint,
    PreviewSegment,
    _build_preview_segment,
)

class PreviewContractTests(unittest.TestCase):
    def test_build_preview_segment_sets_shape_kind_and_zero_peak(self) -> None:
        points = (
            PreviewControlPoint(0.0, 0.0, "start_zero", 0),
            PreviewControlPoint(0.1, 0.0, "top", 3),
            PreviewControlPoint(0.2, 0.0, "end_zero", 6),
        )
        segment = _build_preview_segment(
            vowel="あ",
            shape_kind="trapezoid",
            control_points=points,
            source_event_index=1,
        )

        self.assertEqual(segment.vowel, "あ")
        self.assertEqual(segment.shape_kind, "zero_peak")
        self.assertTrue(segment.is_zero_peak)
        self.assertEqual(segment.source_event_index, 1)

    def test_build_preview_segment_calculates_ranges(self) -> None:
        points = (
            PreviewControlPoint(0.0, 0.0, "start_zero", 0),
            PreviewControlPoint(0.1, 0.5, "top", 3),
            PreviewControlPoint(0.2, 0.0, "end_zero", 6),
        )
        segment = _build_preview_segment(
            vowel="い",
            shape_kind="triangle",
            control_points=points,
            source_event_index=2,
            fallback_reason="test",
        )

        self.assertEqual(segment.vowel, "い")
        self.assertEqual(segment.shape_kind, "triangle")
        self.assertFalse(segment.is_zero_peak)
        self.assertEqual(segment.source_event_index, 2)
        self.assertEqual(segment.frame_range, (0, 6))
        self.assertEqual(segment.value_range, (0.0, 0.5))
        self.assertEqual(segment.fallback_reason, "test")
        self.assertFalse(segment.is_short_span)

    def test_build_preview_segment_detects_short_span(self) -> None:
        points = (
            PreviewControlPoint(0.0, 0.0, "start_zero", 10),
            PreviewControlPoint(0.1, 0.5, "top", 11),
            PreviewControlPoint(0.2, 0.0, "end_zero", 12),
        )
        segment = _build_preview_segment(
            vowel="う",
            shape_kind="short_fallback",
            control_points=points,
            source_event_index=3,
        )

        self.assertTrue(segment.is_short_span)
        self.assertEqual(segment.frame_range, (10, 12))

if __name__ == "__main__":
    unittest.main()
