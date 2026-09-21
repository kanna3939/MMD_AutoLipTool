from __future__ import annotations

from unittest.mock import patch

import pytest
import wx

from gui_wx.ui_sync_context import resolve_effective_shape_plan
from tests.helpers import destroy_wx_app, get_or_create_wx_app
from tests.test_wx_ms21_b6_undo_redo import (
    edit_selected,
    make_ready_frame,
    select_event,
)


@pytest.fixture(scope="module", autouse=True)
def wx_app():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    try:
        yield app
    finally:
        destroy_wx_app(app, owns_app=owns_app)


def test_full_sync_resolves_effective_plan_once(wx_app):
    app = wx_app
    frame = make_ready_frame()
    select_event(frame, 0)

    with patch(
        "gui_wx.ui_sync_context.resolve_effective_shape_plan",
        wraps=resolve_effective_shape_plan,
    ) as resolver:
        frame.sync_ui_state()

    # B4 reuses the immutable context produced by the preceding full sync.
    assert resolver.call_count == 0
    destroy_wx_app(app, frame, owns_app=False)


def test_edit_hint_skips_resolver_and_adjustment_only_broad_refresh(wx_app):
    app = wx_app
    frame = make_ready_frame()
    select_event(frame, 0)

    with (
        patch(
            "gui_wx.ui_sync_context.resolve_effective_shape_plan",
            wraps=resolve_effective_shape_plan,
        ) as resolver,
        patch.object(frame, "_sync_playback_context") as playback_sync,
        patch.object(frame.placeholder_container, "Refresh") as broad_refresh,
        patch.object(frame.param_panel, "Refresh") as parameter_refresh,
    ):
        edit_selected(frame, "peak_value", 0.8)

    resolver.assert_not_called()
    playback_sync.assert_not_called()
    broad_refresh.assert_not_called()
    parameter_refresh.assert_not_called()
    destroy_wx_app(app, frame, owns_app=False)


def test_unchanged_info_snapshot_skips_wrap_and_layout(wx_app):
    app = wx_app
    frame = make_ready_frame()
    snapshot = frame.ui_state.current_output_diagnostics_snapshot
    assert snapshot is not None

    frame.right_pane.set_info_snapshot(snapshot)
    with patch.object(frame.right_pane, "_update_wrap") as update_wrap:
        frame.right_pane.set_info_snapshot(snapshot)

    update_wrap.assert_not_called()
    destroy_wx_app(app, frame, owns_app=False)
