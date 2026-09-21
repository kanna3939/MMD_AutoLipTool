import tempfile
from pathlib import Path
from unittest.mock import patch

import wx

from gui_wx.main_frame import MainFrame


class FakeFileDialog:
    selected_path = ""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ShowModal(self):
        return wx.ID_OK

    def GetPath(self):
        return self.selected_path


def test_overwrite_confirm_no_returns_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "existing.wav"
        output_path.write_bytes(b"existing")
        FakeFileDialog.selected_path = str(output_path)

        with patch("gui_wx.main_frame.wx.FileDialog", FakeFileDialog), \
             patch("gui_wx.main_frame.wx.MessageBox", return_value=wx.NO):
            path = MainFrame.show_mmd_wav_save_dialog_and_get_path(object(), tmpdir, "input_mmd.wav")

        assert path is None


def test_overwrite_confirm_yes_returns_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "existing.wav"
        output_path.write_bytes(b"existing")
        FakeFileDialog.selected_path = str(output_path)

        with patch("gui_wx.main_frame.wx.FileDialog", FakeFileDialog), \
             patch("gui_wx.main_frame.wx.MessageBox", return_value=wx.YES):
            path = MainFrame.show_mmd_wav_save_dialog_and_get_path(object(), tmpdir, "input_mmd.wav")

        assert path == str(output_path)
