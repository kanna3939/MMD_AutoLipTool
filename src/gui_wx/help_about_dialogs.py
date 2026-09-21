from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from typing import Callable

import wx
import wx.adv

from app_version import format_app_version_display
from gui_wx.theme import ThemeManager, ThemeMode
from resource_utils import get_resource_path
from src.core.system_info import (
    NOT_AVAILABLE,
    SystemInfoSnapshot,
)
from gui_wx.system_info_worker import SystemInfoWorker, SystemInfoWorkerResult


AUTHOR_CONTACT_URL = "https://x.com/kanna3939"
USAGE_GUIDE_RESOURCE = "assets/usage_guide.json"
USAGE_GUIDE_LOAD_FAILURE_TEXT = (
    "使い方を読み込めませんでした。\n\n"
    "アプリケーションの配布内容を確認してください。"
)

def load_usage_guide_text(resource_path: Path | None = None) -> str:
    path = resource_path or get_resource_path(USAGE_GUIDE_RESOURCE)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return USAGE_GUIDE_LOAD_FAILURE_TEXT

    if not isinstance(payload, dict):
        return USAGE_GUIDE_LOAD_FAILURE_TEXT
    lines = payload.get("lines")
    if not isinstance(lines, list) or not lines or not all(isinstance(line, str) for line in lines):
        return USAGE_GUIDE_LOAD_FAILURE_TEXT

    content = "\n".join(lines)
    if not content.strip():
        return USAGE_GUIDE_LOAD_FAILURE_TEXT
    return content


USAGE_GUIDE_TEXT = load_usage_guide_text()


def _theme_mode_for(parent: wx.Window) -> str:
    state = getattr(parent, "ui_state", None)
    return getattr(state, "theme_mode", ThemeMode.SYSTEM)


class HelpDialog(wx.Dialog):
    """Read-only popup for the B5 usage guide."""

    def __init__(
        self,
        parent: wx.Window,
    ) -> None:
        super().__init__(
            parent,
            title="使い方",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.text_ctrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
        )
        self.text_ctrl.SetMinSize(wx.Size(720, 520))
        self.text_ctrl.SetValue(USAGE_GUIDE_TEXT)
        self.text_ctrl.SetInsertionPoint(0)

        close_button = wx.Button(self, wx.ID_CLOSE, "閉じる")
        self.Bind(wx.EVT_BUTTON, self._on_close_button, close_button)

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        root_sizer.Add(self.text_ctrl, 1, wx.ALL | wx.EXPAND, 12)
        root_sizer.Add(close_button, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.SetSizer(root_sizer)
        self.SetMinSize(wx.Size(760, 600))
        self.Layout()
        self.CentreOnParent()
        self.apply_theme(_theme_mode_for(parent))

    def apply_theme(self, mode: str) -> None:
        ThemeManager.apply_theme(mode, self)

    def _on_close_button(self, event: wx.CommandEvent) -> None:
        self.EndModal(wx.ID_CLOSE)


class AboutDialog(wx.Dialog):
    """Display-only About dialog with asynchronously collected system information."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        job_id: int,
        collector: Callable[[], SystemInfoSnapshot] | None = None,
        worker_factory: Callable[..., SystemInfoWorker] = SystemInfoWorker,
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        super().__init__(
            parent,
            title="About MMD AutoLipTool",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._job_id = job_id
        self._closed = False
        self._worker: SystemInfoWorker | None = None
        self._worker_factory = worker_factory
        self._call_after = call_after
        self._collector = collector
        self._value_labels: dict[str, wx.StaticText] = {}

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, label="MMD AutoLipTool")
        title_font = title.GetFont()
        title_font.MakeBold()
        title.SetFont(title_font)
        root_sizer.Add(title, 0, wx.ALL, 12)

        info_sizer = wx.FlexGridSizer(cols=2, vgap=8, hgap=14)
        info_sizer.AddGrowableCol(1, 1)
        for key, label in (
            ("app_version", "アプリケーションversion"),
            ("whisper_status", "Whisper状態"),
            ("whisper_version", "Whisper version"),
            ("ffmpeg_version", "FFmpeg version"),
            ("cpu_name", "CPU"),
            ("cpu_logical_count", "CPU論理プロセッサ数"),
            ("memory_total_gib", "物理メモリ"),
            ("gpu_names", "GPU"),
        ):
            info_sizer.Add(wx.StaticText(self, label=label), 0, wx.ALIGN_TOP)
            value = wx.StaticText(self, label="取得中...")
            value.Wrap(460)
            self._value_labels[key] = value
            info_sizer.Add(value, 1, wx.EXPAND)
        root_sizer.Add(info_sizer, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 12)

        root_sizer.Add(wx.StaticLine(self), 0, wx.ALL | wx.EXPAND, 12)
        self.author_link = wx.adv.HyperlinkCtrl(
            self,
            wx.ID_ANY,
            AUTHOR_CONTACT_URL,
            AUTHOR_CONTACT_URL,
        )
        self.Bind(wx.adv.EVT_HYPERLINK, self._on_author_link, self.author_link)
        root_sizer.Add(self.author_link, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        close_button = wx.Button(self, wx.ID_CLOSE, "閉じる")
        self.Bind(wx.EVT_BUTTON, self._on_close_button, close_button)
        root_sizer.Add(close_button, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(root_sizer)
        self.SetMinSize(wx.Size(660, 420))
        self.Layout()
        self.CentreOnParent()
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.apply_theme(_theme_mode_for(parent))
        self._start_worker()

    def apply_theme(self, mode: str) -> None:
        ThemeManager.apply_theme(mode, self)

    def _start_worker(self) -> None:
        kwargs = {
            "job_id": self._job_id,
            "success_callback": self._on_worker_success,
            "failure_callback": self._on_worker_failure,
            "call_after": self._call_after,
        }
        if self._collector is not None:
            kwargs["collector"] = self._collector
        self._worker = self._worker_factory(**kwargs)
        self._worker.start()

    def _callback_is_current(self, result: SystemInfoWorkerResult) -> bool:
        if self._closed or result.job_id != self._job_id:
            return False
        try:
            return not self.IsBeingDeleted()
        except RuntimeError:
            return False

    def _on_worker_success(self, result: SystemInfoWorkerResult) -> None:
        if self._callback_is_current(result):
            self._apply_snapshot(result.snapshot)

    def _on_worker_failure(self, result: SystemInfoWorkerResult) -> None:
        if self._callback_is_current(result):
            self._apply_snapshot(result.snapshot)

    def _apply_snapshot(self, snapshot: SystemInfoSnapshot) -> None:
        app_version = snapshot.app_version
        if app_version != NOT_AVAILABLE:
            app_version = format_app_version_display(app_version)
        self._set_value("app_version", app_version)
        self._set_value("whisper_status", snapshot.whisper_status)
        self._set_value("whisper_version", snapshot.whisper_version)
        self._set_value("ffmpeg_version", snapshot.ffmpeg_version)
        self._set_value("cpu_name", snapshot.cpu_name)
        self._set_value("cpu_logical_count", str(snapshot.cpu_logical_count))
        self._set_value("memory_total_gib", snapshot.memory_total_gib)
        self._set_value("gpu_names", "\n".join(snapshot.gpu_names))
        self.Layout()

    def _set_value(self, key: str, value: str) -> None:
        label = self._value_labels.get(key)
        if label is None:
            return
        label.SetLabel(str(value))
        label.Wrap(460)

    def _on_author_link(self, event: wx.adv.HyperlinkEvent) -> None:
        webbrowser.open(AUTHOR_CONTACT_URL)
        event.Skip(False)

    def _on_close_button(self, event: wx.CommandEvent) -> None:
        self.Close()

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self._closed:
            event.Skip()
            return
        self._closed = True
        if self._worker is not None:
            self._worker.cancel(self._job_id)
        self._worker = None
        event.Skip()


__all__ = [
    "AUTHOR_CONTACT_URL",
    "AboutDialog",
    "HelpDialog",
    "USAGE_GUIDE_LOAD_FAILURE_TEXT",
    "USAGE_GUIDE_RESOURCE",
    "USAGE_GUIDE_TEXT",
    "load_usage_guide_text",
]
