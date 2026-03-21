from dataclasses import dataclass
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "gui"))
from preview_transform import PREVIEW_ROW_VOWELS, build_preview_data


@dataclass
class DummyTimelinePoint:
    vowel: str
    time_sec: float
    duration_sec: float
    start_sec: float | None
    end_sec: float | None
    peak_value: float | None
    value: float


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
        self.assertEqual(row_map["う"].segments[0].intensity, 0.0)


if __name__ == "__main__":
    unittest.main()
