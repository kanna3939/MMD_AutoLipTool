import unittest
from pathlib import Path
import sys
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import analyze_wav_file
from helpers import workspace_tempdir, write_test_wav


class AudioProcessingTests(unittest.TestCase):
    def test_wav_basic_info_is_loaded(self) -> None:
        with workspace_tempdir("audio_basic") as tmp_dir:
            wav_path = tmp_dir / "basic.wav"
            write_test_wav(
                wav_path,
                sample_rate=44100,
                lead_sec=0.1,
                speech_sec=0.4,
                trail_sec=0.1,
            )

            result = analyze_wav_file(str(wav_path))

            self.assertEqual(result.sample_rate_hz, 44100)
            self.assertEqual(result.channel_count, 1)
            self.assertGreater(result.frame_count, 0)
            self.assertAlmostEqual(result.duration_sec, 0.6, places=2)

    def test_speech_interval_is_detected_from_leading_and_trailing_silence(self) -> None:
        with workspace_tempdir("audio_speech") as tmp_dir:
            wav_path = tmp_dir / "speech.wav"
            write_test_wav(
                wav_path,
                sample_rate=48000,
                lead_sec=0.2,
                speech_sec=0.6,
                trail_sec=0.3,
            )

            result = analyze_wav_file(str(wav_path), silence_threshold=0.02)

            self.assertTrue(result.has_speech)
            self.assertAlmostEqual(result.leading_silence_end_sec, 0.2, places=2)
            self.assertAlmostEqual(result.trailing_silence_start_sec, 0.8, places=2)
            self.assertAlmostEqual(result.speech_start_sec, 0.2, places=2)
            self.assertAlmostEqual(result.speech_end_sec, 0.8, places=2)

    def test_silence_only_wav_is_handled(self) -> None:
        with workspace_tempdir("audio_silence") as tmp_dir:
            wav_path = tmp_dir / "silence.wav"
            with wave.open(str(wav_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(44100)
                wav_file.writeframes(b"\x00\x00" * 44100)

            result = analyze_wav_file(str(wav_path))
            self.assertFalse(result.has_speech)
            self.assertAlmostEqual(result.duration_sec, 1.0, places=2)
            self.assertAlmostEqual(result.leading_silence_end_sec, 1.0, places=2)
            self.assertAlmostEqual(result.trailing_silence_start_sec, 0.0, places=2)


if __name__ == "__main__":
    unittest.main()
