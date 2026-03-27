import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import _build_interval_morph_frames


class VmdWriterIntervalTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
