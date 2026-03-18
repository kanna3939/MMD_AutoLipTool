import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import _build_interval_morph_frames


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


if __name__ == "__main__":
    unittest.main()
