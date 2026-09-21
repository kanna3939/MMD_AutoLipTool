import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.audio_errors import AudioProbeError, AudioErrorCode
from src.core.audio_probe import probe_audio_file, MAX_AUDIO_FILE_SIZE_BYTES
from src.core.ffprobe_runner import FfprobeRunResult

class TestAudioInputLimits(unittest.TestCase):
    def setUp(self):
        self.ffprobe_path = Path("fake_ffprobe.exe")
        self.input_path = Path("fake_input.wav")

    def _make_fake_runner(self):
        def fake_runner(ffprobe_path, input_path, timeout_sec):
            # This won't be reached if limits fail
            return FfprobeRunResult(stdout='{"format": {"duration": "10"}, "streams": [{"codec_type": "audio"}]}', stderr="", returncode=0)
        return fake_runner

    @patch("src.core.audio_probe.Path.exists")
    def test_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=self._make_fake_runner())
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.AUDIO_FILE_NOT_FOUND)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    def test_path_is_directory(self, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=self._make_fake_runner())
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.AUDIO_PATH_IS_DIRECTORY)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_file_too_large(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = MAX_AUDIO_FILE_SIZE_BYTES + 1
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=self._make_fake_runner())
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.AUDIO_FILE_TOO_LARGE)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    @patch("src.core.audio_probe.detect_audio_input_kind")
    def test_file_size_boundary(self, mock_detect, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = MAX_AUDIO_FILE_SIZE_BYTES
        mock_detect.return_value = "wav" # dummy
        
        # Should not raise file too large
        try:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=self._make_fake_runner())
        except AudioProbeError as e:
            self.assertNotEqual(e.info.code, AudioErrorCode.AUDIO_FILE_TOO_LARGE)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    @patch("src.core.audio_probe.detect_audio_input_kind")
    def test_unsupported_extension(self, mock_detect, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        mock_detect.side_effect = ValueError("Unsupported extension")
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(Path("fake_input.txt"), self.ffprobe_path, runner=self._make_fake_runner())
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.UNSUPPORTED_AUDIO_EXTENSION)

if __name__ == "__main__":
    unittest.main()
