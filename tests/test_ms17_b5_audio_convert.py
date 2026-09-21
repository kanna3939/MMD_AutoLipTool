import unittest
from pathlib import Path
import tempfile
from unittest.mock import MagicMock

from src.core.audio_convert import convert_to_analysis_wav
from src.core.audio_probe import AudioProbeResult, AudioStreamInfo
from src.core.audio_errors import AudioConvertError, AudioErrorCode
from src.core.ffmpeg_runner import FfmpegRunResult

class TestAudioConvert(unittest.TestCase):
    def setUp(self):
        self.ffmpeg_path = Path("fake_ffmpeg.exe")
        self.source_path = Path("C:/path/to/input.mp3")
        
        self.stream_info = AudioStreamInfo(
            codec_name="mp3",
            sample_rate_hz=44100,
            channel_count=2,
            duration_sec=120.0
        )
        
        self.probe_result = AudioProbeResult(
            source_path=self.source_path,
            file_size_bytes=1024 * 1024,
            duration_sec=120.0,
            format_name="mp3",
            audio_stream=self.stream_info
        )

    def test_convert_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec):
                # Create a dummy output file
                output_path.write_text("dummy wav content")
                return FfmpegRunResult(stdout="", stderr="", returncode=0)

            result = convert_to_analysis_wav(
                probe_result=self.probe_result,
                ffmpeg_path=self.ffmpeg_path,
                cache_dir=cache_dir,
                runner=fake_runner
            )
            
            self.assertEqual(result.source_path, self.source_path)
            self.assertTrue(result.analysis_wav_path.exists())
            self.assertEqual(result.spec.codec, "pcm_s16le")
            self.assertEqual(result.spec.sample_rate_hz, 44100)
            self.assertEqual(result.spec.channel_count, 1)
            self.assertEqual(result.duration_sec, 120.0)
            self.assertGreater(result.file_size_bytes, 0)

    def test_convert_execution_failed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec):
                # FFmpeg fails, creates partial file
                output_path.write_text("partial content")
                return FfmpegRunResult(stdout="", stderr="some error", returncode=1)

            with self.assertRaises(AudioConvertError) as cm:
                convert_to_analysis_wav(
                    probe_result=self.probe_result,
                    ffmpeg_path=self.ffmpeg_path,
                    cache_dir=cache_dir,
                    runner=fake_runner
                )
            
            self.assertEqual(cm.exception.info.code, AudioErrorCode.FFMPEG_EXECUTION_FAILED)
            
            # Check cleanup
            cache_files = list(cache_dir.glob("*.wav"))
            self.assertEqual(len(cache_files), 0, "Partial files should be cleaned up")

    def test_convert_output_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec):
                # FFmpeg succeeds but no file is created
                return FfmpegRunResult(stdout="", stderr="", returncode=0)

            with self.assertRaises(AudioConvertError) as cm:
                convert_to_analysis_wav(
                    probe_result=self.probe_result,
                    ffmpeg_path=self.ffmpeg_path,
                    cache_dir=cache_dir,
                    runner=fake_runner
                )
            
            self.assertEqual(cm.exception.info.code, AudioErrorCode.ANALYSIS_WAV_OUTPUT_FAILED)

    def test_convert_output_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec):
                # FFmpeg succeeds but creates 0-byte file
                output_path.touch()
                return FfmpegRunResult(stdout="", stderr="", returncode=0)

            with self.assertRaises(AudioConvertError) as cm:
                convert_to_analysis_wav(
                    probe_result=self.probe_result,
                    ffmpeg_path=self.ffmpeg_path,
                    cache_dir=cache_dir,
                    runner=fake_runner
                )
            
            self.assertEqual(cm.exception.info.code, AudioErrorCode.ANALYSIS_WAV_GENERATION_FAILED)
            
            # Check cleanup
            cache_files = list(cache_dir.glob("*.wav"))
            self.assertEqual(len(cache_files), 0, "Empty files should be cleaned up")

    def test_convert_runner_exception_cleanup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            def fake_runner(ffmpeg_path, input_path, output_path, timeout_sec):
                # Runner throws exception, creates partial file
                output_path.write_text("partial")
                raise Exception("unexpected runner error")

            with self.assertRaises(Exception):
                convert_to_analysis_wav(
                    probe_result=self.probe_result,
                    ffmpeg_path=self.ffmpeg_path,
                    cache_dir=cache_dir,
                    runner=fake_runner
                )
            
            # Check cleanup
            cache_files = list(cache_dir.glob("*.wav"))
            self.assertEqual(len(cache_files), 0, "Partial files should be cleaned up on exception")

if __name__ == '__main__':
    unittest.main()
