import wx
from gui_wx.theme import ThemeButton

class ParameterPanel(wx.Panel):
    """
    [MS14-B1] 口パラメータ入力行。
    morph_upper_limit, closing_hold_frames, closing_softness_frames を配置する。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # morph_upper_limit
        sizer.Add(wx.StaticText(self, label="モーフ最大値:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.sc_morph_limit = wx.SpinCtrlDouble(self, value="0.90", min=0.0, max=10.0, inc=0.05)
        sizer.Add(self.sc_morph_limit, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        # closing_hold_frames
        sizer.Add(wx.StaticText(self, label="開口保持:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        self.sc_hold_frames = wx.SpinCtrlDouble(
            self,
            value="0",
            min=0,
            max=100,
            inc=1.0,
        )
        self.sc_hold_frames.SetDigits(0)
        self.sc_hold_frames.SetMinSize(self.sc_morph_limit.GetBestSize())
        sizer.Add(self.sc_hold_frames, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer.Add(wx.StaticText(self, label="フレーム"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        # closing_softness_frames
        sizer.Add(wx.StaticText(self, label="閉口スムース:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        self.sc_softness_frames = wx.SpinCtrlDouble(
            self,
            value="0",
            min=0,
            max=100,
            inc=1.0,
        )
        self.sc_softness_frames.SetDigits(0)
        self.sc_softness_frames.SetMinSize(self.sc_morph_limit.GetBestSize())
        sizer.Add(self.sc_softness_frames, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer.Add(wx.StaticText(self, label="フレーム"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.btn_apply_output_edits = ThemeButton(self, label="変更を適用")
        self.btn_apply_output_edits.Enable(False)
        sizer.Add(self.btn_apply_output_edits, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        self.st_output_edit_status = wx.StaticText(self, label="")
        sizer.Add(
            self.st_output_edit_status,
            1,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT,
            8,
        )

        self.SetSizer(sizer)

    def set_output_edit_status(self, text: str) -> None:
        if self.st_output_edit_status.GetLabel() != text:
            self.st_output_edit_status.SetLabel(text)

    # --- View Helpers ---
    def get_morph_upper_limit(self) -> float:
        return self.sc_morph_limit.GetValue()

    def set_morph_upper_limit(self, val: float):
        self.sc_morph_limit.SetValue(val)

    def get_closing_hold_frames(self) -> int:
        return int(round(self.sc_hold_frames.GetValue()))

    def set_closing_hold_frames(self, val: int):
        self.sc_hold_frames.SetValue(val)

    def get_closing_softness_frames(self) -> int:
        return int(round(self.sc_softness_frames.GetValue()))

    def set_closing_softness_frames(self, val: int):
        self.sc_softness_frames.SetValue(val)

    def enable_inputs(self, enabled: bool):
        """[MS14-B2] Busy時にスピナーを一括無効化する為のアシスタント"""
        self.sc_morph_limit.Enable(enabled)
        self.sc_hold_frames.Enable(enabled)
        self.sc_softness_frames.Enable(enabled)
        if not enabled:
            self.btn_apply_output_edits.Enable(False)

