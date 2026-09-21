from __future__ import annotations

import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import wx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.help_about_dialogs import AUTHOR_CONTACT_URL, AboutDialog, HelpDialog
from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.system_info_worker import SystemInfoWorkerResult
from gui_wx.theme import ThemeMode
from src.core.system_info import NOT_AVAILABLE, NOT_LOADED, SystemInfoSnapshot


class _FakeWorker:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.job_id = kwargs["job_id"]
        self.state = "pending"
        self.cancelled_job_id = None
        self.__class__.instances.append(self)

    def start(self):
        self.state = "running"

    def cancel(self, job_id=None):
        self.cancelled_job_id = job_id
        self.state = "cancelled"
        return True


class _CloseEvent:
    def Skip(self, *args):
        return None


class TestMS28B5HelpAbout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App.Get() or wx.App(False)
        cls.parent = wx.Frame(None)
        cls.parent.ui_state = SimpleNamespace(theme_mode=ThemeMode.LIGHT)

    @classmethod
    def tearDownClass(cls):
        if cls.parent is not None and not cls.parent.IsBeingDeleted():
            cls.parent.Destroy()
        if wx.App.Get() is cls.app:
            cls.app.ProcessPendingEvents()

    def test_help_text_is_embedded_read_only_and_scrollable(self):
        dialog = HelpDialog(self.parent)
        try:
            self.assertFalse(dialog.text_ctrl.IsEditable())
            self.assertIn("## 基本的な使い方", dialog.text_ctrl.GetValue())
            self.assertIn("## 選択イベントの操作", dialog.text_ctrl.GetValue())
            self.assertIn("WAV、MP3、M4A", dialog.text_ctrl.GetValue())
            self.assertIn("次のような場面", dialog.text_ctrl.GetValue())
            self.assertIn("TEXT＋音声・音声のみのどちらの解析でも", dialog.text_ctrl.GetValue())
        finally:
            dialog.Destroy()

    def test_about_applies_snapshot_format_and_author_link(self):
        _FakeWorker.instances.clear()
        dialog = AboutDialog(
            self.parent,
            job_id=12,
            worker_factory=_FakeWorker,
            call_after=lambda callback, result: None,
        )
        try:
            snapshot = SystemInfoSnapshot(
                app_version="1.0.0",
                whisper_version=NOT_LOADED,
                whisper_status=NOT_LOADED,
                ffmpeg_version="7.1.1",
                cpu_name="Test CPU",
                cpu_logical_count=16,
                memory_total_gib="32.0 GiB",
                gpu_names=("GPU A", "GPU B"),
            )
            dialog._on_worker_success(
                SystemInfoWorkerResult(
                    job_id=12,
                    state="completed",
                    snapshot=snapshot,
                )
            )
            self.assertEqual(dialog._value_labels["app_version"].GetLabel(), "Ver. 1.0.0")
            self.assertEqual(dialog._value_labels["whisper_status"].GetLabel(), NOT_LOADED)
            self.assertEqual(dialog._value_labels["gpu_names"].GetLabel(), "GPU A\nGPU B")
            self.assertEqual(dialog.author_link.GetURL(), AUTHOR_CONTACT_URL)

            with patch("gui_wx.help_about_dialogs.webbrowser.open", return_value=True) as open_browser:
                dialog._on_author_link(Mock())
            open_browser.assert_called_once_with(AUTHOR_CONTACT_URL)
        finally:
            dialog.Destroy()

    def test_about_callback_for_closed_dialog_is_ignored(self):
        _FakeWorker.instances.clear()
        dialog = AboutDialog(
            self.parent,
            job_id=13,
            worker_factory=_FakeWorker,
            call_after=lambda callback, result: None,
        )
        try:
            dialog._on_close(_CloseEvent())
            result = SystemInfoWorkerResult(
                job_id=13,
                state="completed",
                snapshot=SystemInfoSnapshot(
                    app_version="1.0.0",
                    whisper_version="20250625",
                    whisper_status="loaded",
                    ffmpeg_version="7.1.1",
                    cpu_name="CPU",
                    cpu_logical_count=8,
                    memory_total_gib="16.0 GiB",
                    gpu_names=("GPU",),
                ),
            )
            dialog._on_worker_success(result)
            self.assertEqual(dialog._value_labels["app_version"].GetLabel(), "取得中...")
            self.assertEqual(_FakeWorker.instances[0].cancelled_job_id, 13)
        finally:
            if not dialog.IsBeingDeleted():
                dialog.Destroy()

    def test_help_about_menu_items_stay_enabled_while_busy(self):
        frame = MainFrame(None)
        try:
            frame.ui_state.set_busy(True)
            frame.update_action_states()
            self.assertTrue(frame.mi_help.IsEnabled())
            self.assertTrue(frame.mi_about.IsEnabled())
        finally:
            frame.Destroy()

    def test_controller_routes_help_and_about_to_view(self):
        view = Mock()
        controller = AppController.__new__(AppController)
        controller.view = view
        controller._is_shutting_down = False

        controller.request_open_help()
        controller.request_show_about()

        view.show_help_dialog.assert_called_once_with()
        view.show_about_dialog.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
