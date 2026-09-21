from __future__ import annotations

from pathlib import Path

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from tests.helpers import destroy_wx_app, get_or_create_wx_app


ROOT_RUNTIME_FILES = (
    Path("profiles.json"),
    Path("presets.json"),
    Path("MMD_AutoLipTool.ini"),
)


def _snapshot_runtime_files() -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.is_file() else None
        for path in ROOT_RUNTIME_FILES
    }


def test_reused_app_is_not_destroyed_and_teardown_is_repeatable() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = wx.Frame(None)

    destroy_wx_app(app, frame, owns_app=False)
    assert wx.App.Get() is app

    destroy_wx_app(app, frame, owns_app=False)
    destroy_wx_app(app, owns_app=owns_app)
    destroy_wx_app(app, owns_app=owns_app)


def test_pending_save_teardown_does_not_write_root_runtime_files() -> None:
    before = _snapshot_runtime_files()
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    controller = AppController(frame)
    frame.set_controller(controller)
    controller.request_settings_save()

    destroy_wx_app(app, frame, owns_app=owns_app)

    after = _snapshot_runtime_files()
    assert after == before
