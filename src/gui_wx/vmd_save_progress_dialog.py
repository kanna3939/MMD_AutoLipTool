from __future__ import annotations

from collections.abc import Callable

import wx

from gui_wx.theme import ThemeManager


ProgressState = tuple[str, bool] | None


class VmdSaveProgressDialog(wx.Dialog):
    """Small modeless progress view for one verified VMD save operation."""

    def __init__(
        self,
        parent: wx.Window,
        *,
        on_cancel: Callable[[], object],
        get_progress_state: Callable[[], ProgressState],
    ) -> None:
        super().__init__(
            parent,
            title="VMD保存",
            style=wx.DEFAULT_DIALOG_STYLE & ~wx.RESIZE_BORDER,
        )
        self._on_cancel_callback = on_cancel
        self._get_progress_state = get_progress_state
        self._cancel_requested = False
        self._destroying = False

        root = wx.BoxSizer(wx.VERTICAL)
        self.message = wx.StaticText(
            self,
            label="VMDファイルを保存しています。しばらくお待ちください。",
        )
        root.Add(self.message, 0, wx.ALL | wx.EXPAND, self.FromDIP(14))

        self.gauge = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        root.Add(
            self.gauge,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            self.FromDIP(14),
        )

        self.phase_text = wx.StaticText(self, label="保存準備中…")
        root.Add(
            self.phase_text,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            self.FromDIP(14),
        )

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.AddStretchSpacer()
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, label="キャンセル")
        buttons.Add(self.cancel_button, 0, wx.ALL, self.FromDIP(8))
        root.Add(buttons, 0, wx.EXPAND)

        self.SetSizerAndFit(root)
        size = self.GetSize()
        minimum_width = self.FromDIP(360)
        self.SetMinSize(wx.Size(minimum_width, size.height))
        if size.width < minimum_width:
            self.SetSize((minimum_width, size.height))
        self.CenterOnParent()

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, self.cancel_button)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

        ThemeManager.apply_theme(parent.ui_state.theme_mode, self)

    def show(self) -> None:
        if not self.IsShown():
            self.Show()
        if not self._timer.IsRunning():
            self._timer.Start(100)

    def suspend(self) -> None:
        if self._timer.IsRunning():
            self._timer.Stop()
        self.Hide()

    def resume(self) -> None:
        if self._destroying:
            return
        self.Show()
        self.Raise()
        if not self._timer.IsRunning():
            self._timer.Start(100)

    def close(self) -> None:
        if self._destroying:
            return
        self._destroying = True
        if self._timer.IsRunning():
            self._timer.Stop()
        self.Destroy()

    def _on_timer(self, _event: wx.TimerEvent) -> None:
        if self._destroying or not self.IsShown():
            return
        try:
            state = self._get_progress_state()
        except Exception:
            state = None
        if state is not None:
            phase, cancel_enabled = state
            self.phase_text.SetLabel(phase)
            self.cancel_button.Enable(cancel_enabled and not self._cancel_requested)
        self.gauge.Pulse()

    def _request_cancel(self) -> None:
        if self._cancel_requested or self._destroying:
            return
        self._cancel_requested = True
        self.cancel_button.Disable()
        self.phase_text.SetLabel("キャンセル中です。処理終了を待っています…")
        try:
            self._on_cancel_callback()
        except Exception:
            # The owning controller reports operation failures through its normal
            # terminal path. Keep the progress window visible until that result.
            pass

    def _on_cancel(self, _event: wx.CommandEvent) -> None:
        self._request_cancel()

    def _on_close(self, event: wx.CloseEvent) -> None:
        if event.CanVeto():
            event.Veto()
        self._request_cancel()

    def _on_char_hook(self, event: wx.KeyEvent) -> None:
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._request_cancel()
            return
        event.Skip()


__all__ = ["VmdSaveProgressDialog"]
