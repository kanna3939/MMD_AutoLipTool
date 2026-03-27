import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vmd_writer import VowelTimelinePoint
from vmd_writer.writer import _build_interval_morph_frames, _finalize_morph_value


class VmdWriterPeakValueTests(unittest.TestCase):
    def test_interval_non_zero_keys_use_peak_value(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3042",
                value=0.5,
                peak_value=0.3212,
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.3212),
                (33, "\u3042", 0.3212),
                (36, "\u3042", 0.0),
            ],
        )

    def test_peak_value_falls_back_to_value_when_missing(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3042",
                value=0.27,
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.27),
                (33, "\u3042", 0.27),
                (36, "\u3042", 0.0),
            ],
        )

    def test_peak_value_zero_keeps_timeline_stable(self) -> None:
        points = [
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="\u3042",
                peak_value=0.0,
                duration_sec=0.4,
                start_sec=0.8,
                end_sec=1.2,
            )
        ]

        frames = _build_interval_morph_frames(points)
        self.assertEqual(
            frames,
            [
                (24, "\u3042", 0.0),
                (27, "\u3042", 0.0),
                (33, "\u3042", 0.0),
                (36, "\u3042", 0.0),
            ],
        )

    def test_finalize_morph_value_rounds_only_when_needed(self) -> None:
        self.assertEqual(_finalize_morph_value(0.123456), 0.1235)
        self.assertEqual(_finalize_morph_value(0.1234), 0.1234)
        self.assertEqual(_finalize_morph_value(0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
