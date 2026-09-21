import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.audio_errors import AudioProbeError, AudioErrorCode
from src.core.ffprobe_runner import run_ffprobe_json

class TestFfprobeRunner(unittest.TestCase):
    def setUp(self):
        self.ffprobe_path = Path("fake_ffprobe.exe")
        self.input_path = Path("fake_input.wav")

    @patch("src.core.ffprobe_runner.subprocess.run")
    def test_success(self, mock_run):
        mock_process = MagicMock()
        mock_process.stdout = '{"format": {}}'
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        result = run_ffprobe_json(self.ffprobe_path, self.input_path)
        
        self.assertEqual(result.stdout, '{"format": {}}')
        self.assertEqual(result.returncode, 0)
        
        # Verify shell=False is used
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertFalse(kwargs.get("shell", True)) # default should be false or explicitly False
        self.assertIn("-print_format", args[0])
        self.assertIn("json", args[0])

    @patch("src.core.ffprobe_runner.subprocess.run")
    def test_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("Executable not found")
        
        with self.assertRaises(AudioProbeError) as ctx:
            run_ffprobe_json(self.ffprobe_path, self.input_path)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.FFPROBE_NOT_FOUND)

    @patch("src.core.ffprobe_runner.subprocess.run")
    def test_permission_error(self, mock_run):
        mock_run.side_effect = PermissionError("Access denied")
        
        with self.assertRaises(AudioProbeError) as ctx:
            run_ffprobe_json(self.ffprobe_path, self.input_path)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.FFPROBE_PERMISSION_ERROR)

    @patch("src.core.ffprobe_runner.subprocess.run")
    def test_timeout_expired(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=30.0)
        
        with self.assertRaises(AudioProbeError) as ctx:
            run_ffprobe_json(self.ffprobe_path, self.input_path)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.FFPROBE_TIMEOUT)

if __name__ == "__main__":
    unittest.main()
