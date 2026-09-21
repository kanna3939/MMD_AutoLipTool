import wx

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
        self.sc_morph_limit = wx.SpinCtrlDouble(self, value="0.50", min=0.0, max=10.0, inc=0.05)
        sizer.Add(self.sc_morph_limit, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        # closing_hold_frames
        sizer.Add(wx.StaticText(self, label="開口保持:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        self.sc_hold_frames = wx.SpinCtrl(self, value="0", min=0, max=100)
        sizer.Add(self.sc_hold_frames, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer.Add(wx.StaticText(self, label="フレーム"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        # closing_softness_frames
        sizer.Add(wx.StaticText(self, label="閉口スムース:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        self.sc_softness_frames = wx.SpinCtrl(self, value="0", min=0, max=100)
        sizer.Add(self.sc_softness_frames, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer.Add(wx.StaticText(self, label="フレーム"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.SetSizer(sizer)

    # --- View Helpers ---
    def get_morph_upper_limit(self) -> float:
        return self.sc_morph_limit.GetValue()

    def set_morph_upper_limit(self, val: float):
        self.sc_morph_limit.SetValue(val)

    def get_closing_hold_frames(self) -> int:
        return self.sc_hold_frames.GetValue()

    def set_closing_hold_frames(self, val: int):
        self.sc_hold_frames.SetValue(val)

    def get_closing_softness_frames(self) -> int:
        return self.sc_softness_frames.GetValue()

    def set_closing_softness_frames(self, val: int):
        self.sc_softness_frames.SetValue(val)

    def enable_inputs(self, enabled: bool):
        """[MS14-B2] Busy時にスピナーを一括無効化する為のアシスタント"""
        self.sc_morph_limit.Enable(enabled)
        self.sc_hold_frames.Enable(enabled)
        self.sc_softness_frames.Enable(enabled)

