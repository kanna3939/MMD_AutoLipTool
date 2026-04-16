import unittest
import wx
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui_wx.app import AutoLipToolApp
from gui_wx.main_frame import MainFrame

class TestWXMS14B3Input(unittest.TestCase):
    """
    [MS14-B3] 入力導線と Counterpart Auto Load のテスト
    """
    @classmethod
    def setUpClass(cls):
        cls.app = AutoLipToolApp(False)

    @classmethod
    def tearDownClass(cls):
        if cls.app.frame:
            cls.app.frame.Destroy()
        wx.CallAfter(cls.app.ExitMainLoop)
        cls.app.MainLoop()

    def setUp(self):
        self.frame: MainFrame = self.app.frame
        self.frame.ui_state.selected_text_path = None
        self.frame.ui_state.selected_wav_path = None
        self.frame.ui_state.selected_text_content = ""
        self.frame.ui_state.recent_text_files.clear()
        self.frame.ui_state.recent_wav_files.clear()

    @patch('gui_wx.main_frame.os.path.exists', return_value=True)
    @patch('gui_wx.main_frame.os.path.isdir', return_value=False)
    @patch('gui_wx.main_frame.open')
    def test_open_text_file_quietly(self, mock_open, mock_isdir, mock_exists):
        # Setup mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = "あいうえお"
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file

        # Execute
        self.frame._open_text_file("C:/mock/path.txt")
        
        # Verify
        state = self.frame.ui_state
        self.assertEqual(state.selected_text_path, "C:/mock/path.txt")
        self.assertEqual(state.selected_text_content, "あいうえお")
        self.assertTrue("C:/mock/path.txt" in state.recent_text_files)
        # Should not auto-load since it was a quiet load itself
        self.assertIsNone(state.selected_wav_path)

    @patch('gui_wx.main_frame.analyze_wav_file')
    @patch('gui_wx.main_frame.os.path.exists', return_value=True)
    @patch('gui_wx.main_frame.os.path.isdir', return_value=False)
    def test_open_wav_file_quietly(self, mock_isdir, mock_exists, mock_analyze):
        mock_analysis = MagicMock()
        mock_analysis.sample_rate = 44100
        mock_analysis.channels = 2
        mock_analysis.duration_sec = 1.0
        mock_analyze.return_value = mock_analysis

        # Execute
        self.frame._open_wav_file("C:/mock/path.wav")

        # Verify
        state = self.frame.ui_state
        self.assertEqual(state.selected_wav_path, "C:/mock/path.wav")
        self.assertIsNotNone(state.selected_wav_analysis)
        self.assertTrue("C:/mock/path.wav" in state.recent_wav_files)

if __name__ == "__main__":
    unittest.main()
