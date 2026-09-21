import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.audio_errors import AudioConvertError, AudioErrorCode
from src.core.audio_probe import AudioProbeResult, AudioStreamInfo
from src.core.ffmpeg_runner import FfmpegRunResult, run_ffmpeg_mmd_wav
from src.core.mmd_wav_export import MMD_WAV_SPEC, export_mmd_wav


def write_wav(path: Path, *, channels: int = 2, sample_rate: int = 44100, bits: int = 16) -> None:
    data_size = channels * 2
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    with path.open("wb") as fh:
        fh.write(b"RIFF")
        fh.write(struct.pack("<I", 36 + data_size))
        fh.write(b"WAVE")
        fh.write(b"fmt ")
        fh.write(struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits))
        fh.write(b"data")
        fh.write(struct.pack("<I", data_size))
        fh.write(b"\0" * data_size)


class TestMmdWavExport(unittest.TestCase):
    def _probe_result(self, source_path: Path) -> AudioProbeResult:
        return AudioProbeResult(
            source_path=source_path,
            file_size_bytes=source_path.stat().st_size,
            duration_sec=1.0,
            format_name="mp3",
            audio_stream=AudioStreamInfo(
                codec_name="mp3",
                sample_rate_hz=44100,
                channel_count=2,
                duration_sec=1.0,
            ),
        )

    def test_export_success_uses_source_audio_and_stereo_spec(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_path = tmp / "source.mp3"
            source_path.write_bytes(b"source")
            output_path = tmp / "source_mmd.wav"

            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec, source_channel_count):
                self.assertEqual(input_path, source_path)
                self.assertEqual(source_channel_count, 2)
                write_wav(output_path)
                return FfmpegRunResult(stdout="", stderr="", returncode=0)

            result = export_mmd_wav(
                probe_result=self._probe_result(source_path),
                ffmpeg_path=Path("ffmpeg.exe"),
                output_path=output_path,
                runner=fake_runner,
            )

            self.assertEqual(result.source_path, source_path)
            self.assertEqual(result.mmd_wav_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertEqual(result.spec, MMD_WAV_SPEC)
            self.assertEqual(result.spec.channel_count, 2)

    def test_runner_command_uses_stereo_output(self):
        with patch("subprocess.run") as mock_run:
            process = MagicMock()
            process.stdout = ""
            process.stderr = ""
            process.returncode = 0
            mock_run.return_value = process

            run_ffmpeg_mmd_wav(
                ffmpeg_path=Path("ffmpeg.exe"),
                input_path=Path("input.m4a"),
                output_path=Path("output.wav"),
            )

            cmd = mock_run.call_args.args[0]
            self.assertIn("-acodec", cmd)
            self.assertIn("pcm_s16le", cmd)
            self.assertIn("-ar", cmd)
            self.assertIn("44100", cmd)
            self.assertIn("-bitexact", cmd)
            ac_index = cmd.index("-ac")
            self.assertEqual(cmd[ac_index + 1], "2")

    def test_runner_command_uses_ch1_ch2_only_for_multichannel_input(self):
        with patch("subprocess.run") as mock_run:
            process = MagicMock()
            process.stdout = ""
            process.stderr = ""
            process.returncode = 0
            mock_run.return_value = process

            run_ffmpeg_mmd_wav(
                ffmpeg_path=Path("ffmpeg.exe"),
                input_path=Path("input.wav"),
                output_path=Path("output.wav"),
                source_channel_count=3,
            )

            cmd = mock_run.call_args.args[0]
            self.assertIn("-filter:a", cmd)
            filter_index = cmd.index("-filter:a")
            self.assertEqual(cmd[filter_index + 1], "pan=stereo|c0=c0|c1=c1")

    def test_runner_command_duplicates_mono_input_to_stereo(self):
        with patch("subprocess.run") as mock_run:
            process = MagicMock()
            process.stdout = ""
            process.stderr = ""
            process.returncode = 0
            mock_run.return_value = process

            run_ffmpeg_mmd_wav(
                ffmpeg_path=Path("ffmpeg.exe"),
                input_path=Path("input.wav"),
                output_path=Path("output.wav"),
                source_channel_count=1,
            )

            cmd = mock_run.call_args.args[0]
            self.assertIn("-filter:a", cmd)
            filter_index = cmd.index("-filter:a")
            self.assertEqual(cmd[filter_index + 1], "pan=stereo|c0=c0|c1=c0")

    def test_rejects_same_source_and_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "source.wav"
            source_path.write_bytes(b"source")

            with self.assertRaises(AudioConvertError) as cm:
                export_mmd_wav(
                    probe_result=self._probe_result(source_path),
                    ffmpeg_path=Path("ffmpeg.exe"),
                    output_path=source_path,
                    runner=lambda **kwargs: FfmpegRunResult("", "", 0),
                )

            self.assertEqual(cm.exception.info.code, AudioErrorCode.MMD_WAV_OUTPUT_PATH_INVALID)

    def test_rejects_mono_mmd_wav_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_path = tmp / "source.mp3"
            source_path.write_bytes(b"source")

            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec, source_channel_count):
                write_wav(output_path, channels=1)
                return FfmpegRunResult(stdout="", stderr="", returncode=0)

            with self.assertRaises(AudioConvertError) as cm:
                export_mmd_wav(
                    probe_result=self._probe_result(source_path),
                    ffmpeg_path=Path("ffmpeg.exe"),
                    output_path=tmp / "source_mmd.wav",
                    runner=fake_runner,
                )

            self.assertEqual(cm.exception.info.code, AudioErrorCode.MMD_WAV_VALIDATION_FAILED)


if __name__ == "__main__":
    unittest.main()
