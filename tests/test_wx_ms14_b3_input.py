import unittest
import wx
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame
from tests.helpers import destroy_wx_app, get_or_create_wx_app

class TestWXMS14B3Input(unittest.TestCase):
    """
    [MS14-B3] 入力導線と Counterpart Auto Load のテスト
    """
    @classmethod
    def setUpClass(cls):
        with patch("gui_wx.app.get_resource_path", return_value=Path("missing_splash.png")):
            cls.app, cls.owns_app = get_or_create_wx_app(AutoLipToolApp, False)

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, owns_app=cls.owns_app)

    def setUp(self):
        self.frame: MainFrame = self.app.frame
        self.frame.ui_state.selected_text_path = None
        self.frame.ui_state.selected_wav_path = None
        self.frame.ui_state.selected_text_content = ""
        self.frame.ui_state.recent_text_files.clear()
        self.frame.ui_state.recent_wav_files.clear()
        self.frame.ui_state.recent_audio_files.clear()

    @patch('gui_wx.main_frame.os.path.isfile', return_value=True)
    @patch('gui_wx.main_frame.os.path.exists', return_value=True)
    @patch('gui_wx.main_frame.os.path.isdir', return_value=False)
    @patch('gui_wx.main_frame.open')
    @patch('gui_wx.app_controller.AppController.request_open_audio_file')
    def test_open_text_file_quietly(self, mock_request_audio, mock_open, mock_isdir, mock_exists, mock_isfile):
        # Setup mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = "あいうえお"
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file

        # Execute
        test_path = "C:/mock/path.txt".replace("/", os.sep)
        self.frame._open_text_file(test_path)
        
        # Verify
        state = self.frame.ui_state
        self.assertEqual(state.selected_text_path, test_path)
        self.assertEqual(state.selected_text_content, "あいうえお")
        self.assertTrue(test_path in state.recent_text_files)
        # Should not auto-load since it was a quiet load itself
        self.assertIsNone(state.selected_wav_path)

    @patch('src.gui_wx.recent_files.os.path.exists', return_value=True)
    @patch('src.gui_wx.recent_files.os.path.isfile', return_value=True)
    @patch('gui_wx.app_controller.analyze_wav_file')
    @patch('gui_wx.app_controller.load_waveform_preview')
    @patch('gui_wx.app_controller.convert_to_analysis_wav')
    @patch('gui_wx.app_controller.probe_audio_file')
    @patch('gui_wx.app_controller.locate_ffmpeg_tools')
    @patch('gui_wx.app_controller.build_audio_input_info')
    def test_open_audio_file_quietly(self, mock_build_info, mock_locate, mock_probe, mock_convert, mock_load_preview, mock_analyze, mock_isfile, mock_exists):
        # Setup mocks
        test_path = "C:/mock/path.wav".replace("/", os.sep)
        
        mock_input_info = MagicMock()
        mock_input_info.source_path = test_path
        mock_build_info.return_value = mock_input_info
        
        mock_ffmpeg = MagicMock()
        mock_locate.return_value = mock_ffmpeg
        
        mock_probe_res = MagicMock()
        mock_probe_res.format_name = "wav"
        mock_probe_res.duration_sec = 1.0
        mock_probe.return_value = mock_probe_res
        
        mock_convert_res = MagicMock()
        mock_convert_res.analysis_wav_path = "C:/mock/cache/path.wav".replace("/", os.sep)
        mock_convert.return_value = mock_convert_res
        
        mock_preview = MagicMock()
        mock_preview.samples = []
        mock_preview.duration_sec = 1.0
        mock_load_preview.return_value = mock_preview
        
        mock_analysis = MagicMock()
        mock_analysis.sample_rate_hz = 44100
        mock_analysis.channel_count = 2
        mock_analysis.duration_sec = 1.0
        mock_analyze.return_value = mock_analysis

        # Execute
        self.frame.controller.request_open_audio_file(test_path)
        probe_worker = self.frame.controller._audio_worker
        probe_worker.join(timeout=2.0)
        self.app.ProcessPendingEvents()
        convert_worker = self.frame.controller._audio_worker
        convert_worker.join(timeout=2.0)
        self.app.ProcessPendingEvents()

        # Verify
        state = self.frame.ui_state
        self.assertEqual(state.selected_wav_path, test_path)
        self.assertEqual(state.selected_audio_input, mock_input_info)
        self.assertIsNotNone(state.selected_wav_analysis)
        self.assertTrue(test_path in state.recent_audio_files)

if __name__ == "__main__":
    unittest.main()
