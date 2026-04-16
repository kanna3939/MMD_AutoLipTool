import wx

class PlaceholderContainer(wx.Panel):
    """
    [MS14-B1] 右側表示プレースホルダコンテナ。
    上下2段で波形とPreviewの置き場を確保する。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.pnl_waveform = wx.Panel(self, style=wx.BORDER_SIMPLE)
        wf_sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_waveform = wx.StaticText(self.pnl_waveform, label="[Placeholder] 波形エリア")
        wf_sizer.Add(self.st_waveform, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        self.pnl_waveform.SetSizer(wf_sizer)

        self.pnl_preview = wx.Panel(self, style=wx.BORDER_SIMPLE)
        pv_sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_preview = wx.StaticText(self.pnl_preview, label="[Placeholder] Preview エリア")
        pv_sizer.Add(self.st_preview, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        self.pnl_preview.SetSizer(pv_sizer)

        sizer.Add(self.pnl_waveform, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.pnl_preview, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    # --- View Helpers ---
    def set_waveform_placeholder_text(self, text: str):
        self.st_waveform.SetLabel(text)
        self.pnl_waveform.Layout()

    def set_preview_placeholder_text(self, text: str):
        self.st_preview.SetLabel(text)
        self.pnl_preview.Layout()
