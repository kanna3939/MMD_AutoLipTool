import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.audio_errors import AudioProbeError, AudioErrorCode
from src.core.audio_probe import probe_audio_file
from src.core.ffprobe_runner import FfprobeRunResult

class TestAudioProbe(unittest.TestCase):
    def setUp(self):
        self.ffprobe_path = Path("fake_ffprobe.exe")
        self.input_path = Path("fake_input.wav")

    def _make_fake_runner(self, stdout: str, returncode: int = 0):
        def fake_runner(ffprobe_path, input_path, timeout_sec):
            return FfprobeRunResult(stdout=stdout, stderr="", returncode=returncode)
        return fake_runner

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_success_format_duration(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        valid_json = json.dumps({
            "format": {"duration": "120.5", "format_name": "wav"},
            "streams": [{"codec_type": "audio", "codec_name": "pcm_s16le", "sample_rate": "44100", "channels": 2}]
        })
        runner = self._make_fake_runner(stdout=valid_json)
        
        result = probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
        self.assertEqual(result.duration_sec, 120.5)
        self.assertEqual(result.format_name, "wav")
        self.assertEqual(result.audio_stream.codec_name, "pcm_s16le")
        self.assertEqual(result.audio_stream.sample_rate_hz, 44100)
        self.assertEqual(result.audio_stream.channel_count, 2)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_success_stream_duration(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        valid_json = json.dumps({
            "format": {"format_name": "wav"},
            "streams": [{"codec_type": "audio", "duration": "100.0"}]
        })
        runner = self._make_fake_runner(stdout=valid_json)
        
        result = probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
        self.assertEqual(result.duration_sec, 100.0)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_no_audio_stream(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        valid_json = json.dumps({
            "format": {"duration": "10.0"},
            "streams": [{"codec_type": "video"}]
        })
        runner = self._make_fake_runner(stdout=valid_json)
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.AUDIO_STREAM_NOT_FOUND)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_duration_missing(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        valid_json = json.dumps({
            "format": {},
            "streams": [{"codec_type": "audio"}]
        })
        runner = self._make_fake_runner(stdout=valid_json)
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.AUDIO_DURATION_MISSING)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_duration_too_long(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        valid_json = json.dumps({
            "format": {"duration": "900.1"},
            "streams": [{"codec_type": "audio"}]
        })
        runner = self._make_fake_runner(stdout=valid_json)
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.AUDIO_DURATION_TOO_LONG)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_invalid_json(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        runner = self._make_fake_runner(stdout="not a json")
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.FFPROBE_INVALID_JSON)

    @patch("src.core.audio_probe.Path.exists")
    @patch("src.core.audio_probe.Path.is_dir")
    @patch("src.core.audio_probe.Path.stat")
    def test_execution_failed(self, mock_stat, mock_is_dir, mock_exists):
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        mock_stat.return_value.st_size = 1024
        
        runner = self._make_fake_runner(stdout="", returncode=1)
        
        with self.assertRaises(AudioProbeError) as ctx:
            probe_audio_file(self.input_path, self.ffprobe_path, runner=runner)
            
        self.assertEqual(ctx.exception.info.code, AudioErrorCode.FFPROBE_EXECUTION_FAILED)

if __name__ == "__main__":
    unittest.main()
