import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import _build_interval_morph_frames


class VmdWriterIntervalTests(unittest.TestCase):
    def test_trapezoid_frames_use_start_end_bounds(self) -> None:
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
                (26, "あ", 0.5),
                (34, "あ", 0.5),
                (36, "あ", 0.0),
            ],
        )

    def test_short_interval_falls_back_to_triangle(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                duration_sec=0.06,
                start_sec=0.97,
                end_sec=1.03,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (29, "あ", 0.0),
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


if __name__ == "__main__":
    unittest.main()
