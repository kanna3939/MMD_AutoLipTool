import wx
from gui_wx.waveform_panel import WaveformPanel
from gui_wx.preview_panel import PreviewPanel
from gui.preview_transform import PreviewData

class PlaceholderContainer(wx.Panel):
    """
    [MS14-B1] 右側表示プレースホルダコンテナ。
    上下2段で波形とPreviewの置き場を確保する。
    [MS15-B2] PreviewPanelを実体化し組み込み。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.pnl_waveform = WaveformPanel(self)
        self.pnl_preview = PreviewPanel(self)

        sizer.Add(self.pnl_waveform, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.pnl_preview, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    # --- View Helpers ---
    def set_waveform_data(self, samples: list[float], duration_sec: float):
        self.pnl_waveform.set_waveform_data(samples, duration_sec)

    def set_waveform_placeholder_text(self, text: str):
        self.pnl_waveform.show_placeholder(text)

    def set_preview_data(self, data: PreviewData, duration_sec: float):
        self.pnl_preview.set_preview_data(data, duration_sec)

    def set_preview_placeholder_text(self, text: str):
        self.pnl_preview.set_placeholder(text)
