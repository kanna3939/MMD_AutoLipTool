import tempfile
import unittest
from pathlib import Path

from src.core.audio_errors import AudioConvertError, AudioErrorCode
from src.core.audio_probe import AudioProbeResult, AudioStreamInfo
from src.core.ffmpeg_runner import FfmpegRunResult
from src.core.mmd_wav_export import export_mmd_wav


class TestMmdWavFailureCleanup(unittest.TestCase):
    def _probe_result(self, source_path: Path) -> AudioProbeResult:
        return AudioProbeResult(
            source_path=source_path,
            file_size_bytes=source_path.stat().st_size,
            duration_sec=1.0,
            format_name="mp3",
            audio_stream=AudioStreamInfo("mp3", 44100, 2, 1.0),
        )

    def test_failed_runner_removes_temp_file_and_keeps_existing_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_path = tmp / "source.mp3"
            output_path = tmp / "source_mmd.wav"
            source_path.write_bytes(b"source")
            output_path.write_bytes(b"existing")

            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec, source_channel_count):
                output_path.write_bytes(b"partial")
                return FfmpegRunResult(stdout="", stderr="failed", returncode=1)

            with self.assertRaises(AudioConvertError) as cm:
                export_mmd_wav(
                    probe_result=self._probe_result(source_path),
                    ffmpeg_path=Path("ffmpeg.exe"),
                    output_path=output_path,
                    runner=fake_runner,
                )

            self.assertEqual(cm.exception.info.code, AudioErrorCode.MMD_WAV_EXPORT_FAILED)
            self.assertEqual(output_path.read_bytes(), b"existing")
            self.assertEqual(list(tmp.glob("*.tmp_mmd.wav")), [])

    def test_invalid_wav_output_is_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_path = tmp / "source.mp3"
            output_path = tmp / "source_mmd.wav"
            source_path.write_bytes(b"source")

            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec, source_channel_count):
                output_path.write_bytes(b"not a wav")
                return FfmpegRunResult(stdout="", stderr="", returncode=0)

            with self.assertRaises(AudioConvertError) as cm:
                export_mmd_wav(
                    probe_result=self._probe_result(source_path),
                    ffmpeg_path=Path("ffmpeg.exe"),
                    output_path=output_path,
                    runner=fake_runner,
                )

            self.assertEqual(cm.exception.info.code, AudioErrorCode.MMD_WAV_VALIDATION_FAILED)
            self.assertFalse(output_path.exists())
            self.assertEqual(list(tmp.glob("*.tmp_mmd.wav")), [])


if __name__ == "__main__":
    unittest.main()
