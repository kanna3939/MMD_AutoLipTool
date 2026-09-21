import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from src.core.ffmpeg_runner import run_ffmpeg_analysis_wav, FfmpegRunResult
from src.core.audio_errors import AudioConvertError, AudioErrorCode

class TestFfmpegRunner(unittest.TestCase):
    def setUp(self):
        self.ffmpeg_path = Path("fake_ffmpeg.exe")
        self.input_path = Path("input.mp3")
        self.output_path = Path("output.wav")

    @patch("subprocess.run")
    def test_run_ffmpeg_success(self, mock_run):
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.stderr = "some ffmpeg output"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = run_ffmpeg_analysis_wav(
            ffmpeg_path=self.ffmpeg_path,
            input_path=self.input_path,
            output_path=self.output_path
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "some ffmpeg output")
        
        # Verify the command
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertEqual(cmd[0], str(self.ffmpeg_path))
        self.assertIn("-y", cmd)
        self.assertIn(str(self.input_path), cmd)
        self.assertIn(str(self.output_path), cmd)
        self.assertIn("-acodec", cmd)
        self.assertIn("pcm_s16le", cmd)

    @patch("subprocess.run")
    def test_run_ffmpeg_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("not found")

        with self.assertRaises(AudioConvertError) as cm:
            run_ffmpeg_analysis_wav(self.ffmpeg_path, self.input_path, self.output_path)
            
        self.assertEqual(cm.exception.info.code, AudioErrorCode.FFMPEG_NOT_FOUND)

    @patch("subprocess.run")
    def test_run_ffmpeg_permission_error(self, mock_run):
        mock_run.side_effect = PermissionError("access denied")

        with self.assertRaises(AudioConvertError) as cm:
            run_ffmpeg_analysis_wav(self.ffmpeg_path, self.input_path, self.output_path)
            
        self.assertEqual(cm.exception.info.code, AudioErrorCode.FFMPEG_PERMISSION_ERROR)

    @patch("subprocess.run")
    def test_run_ffmpeg_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=10)

        with self.assertRaises(AudioConvertError) as cm:
            run_ffmpeg_analysis_wav(self.ffmpeg_path, self.input_path, self.output_path, timeout_sec=10)
            
        self.assertEqual(cm.exception.info.code, AudioErrorCode.FFMPEG_TIMEOUT)

if __name__ == '__main__':
    unittest.main()
