import tempfile
from pathlib import Path
from unittest.mock import patch

import wx

from gui_wx.main_frame import MainFrame


class FakeFileDialog:
    selected_path = ""
    result = wx.ID_OK

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ShowModal(self):
        return self.result

    def GetPath(self):
        return self.selected_path


def test_mmd_wav_save_dialog_appends_wav_extension():
    with tempfile.TemporaryDirectory() as tmpdir:
        FakeFileDialog.selected_path = str(Path(tmpdir) / "output")
        FakeFileDialog.result = wx.ID_OK

        with patch("gui_wx.main_frame.wx.FileDialog", FakeFileDialog):
            path = MainFrame.show_mmd_wav_save_dialog_and_get_path(object(), tmpdir, "input_mmd.wav")

        assert path == str(Path(tmpdir) / "output.wav")


def test_mmd_wav_save_dialog_cancel_returns_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        FakeFileDialog.selected_path = str(Path(tmpdir) / "output.wav")
        FakeFileDialog.result = wx.ID_CANCEL

        with patch("gui_wx.main_frame.wx.FileDialog", FakeFileDialog):
            path = MainFrame.show_mmd_wav_save_dialog_and_get_path(object(), tmpdir, "input_mmd.wav")

        assert path is None
