import struct
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import build_even_vowel_timeline, generate_vmd_from_text_wav
from helpers import workspace_tempdir, write_test_wav
from vmd_writer import write_dummy_morph_vmd


class PipelineAndVmdTests(unittest.TestCase):
    def test_even_vowel_timeline_distribution(self) -> None:
        vowels = ["\u3042", "\u3044", "\u3046", "\u3048", "\u304a"]
        timeline = build_even_vowel_timeline(vowels, speech_start_sec=0.2, speech_end_sec=1.2)

        self.assertEqual(len(timeline), len(vowels))
        self.assertEqual([p.vowel for p in timeline], vowels)
        self.assertAlmostEqual(timeline[0].time_sec, 0.2, places=3)
        self.assertAlmostEqual(timeline[1].time_sec, 0.4, places=3)
        self.assertAlmostEqual(timeline[2].time_sec, 0.6, places=3)
        self.assertAlmostEqual(timeline[3].time_sec, 0.8, places=3)
        self.assertAlmostEqual(timeline[4].time_sec, 1.0, places=3)

    def test_generate_vmd_from_text_and_wav(self) -> None:
        with workspace_tempdir("pipeline_vmd") as tmp:
            text_path = tmp / "input.txt"
            wav_path = tmp / "voice.wav"
            out_path = tmp / "out.vmd"

            text_path.write_text("\u3042\u3044\u3046\u3048\u304a", encoding="utf-8")
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.2,
                speech_sec=0.5,
                trail_sec=0.2,
            )

            result = generate_vmd_from_text_wav(text_path, wav_path, out_path)

            self.assertTrue(result.output_path.exists())
            self.assertEqual(len(result.vowels), len(result.timeline))
            self.assertTrue(result.wav_analysis.has_speech)
            self.assertEqual(result.output_path.suffix.lower(), ".vmd")

    def test_dummy_vmd_output_minimum_shape(self) -> None:
        with workspace_tempdir("dummy_vmd") as tmp_dir:
            out_path = tmp_dir / "dummy.vmd"
            write_dummy_morph_vmd(out_path)

            data = out_path.read_bytes()
            header = data[:30].rstrip(b"\x00")
            bone_count = struct.unpack("<I", data[50:54])[0]
            morph_count = struct.unpack("<I", data[54:58])[0]

            self.assertEqual(header, b"Vocaloid Motion Data 0002")
            self.assertEqual(bone_count, 0)
            self.assertEqual(morph_count, 15)


if __name__ == "__main__":
    unittest.main()
