import wx

class InfoPanel(wx.Panel):
    """
    [MS14-B1] 左側情報パネル。
    TEXT/WAVのパス、パース結果プレビュー、WAV情報を表示する。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # TEXT info
        self.st_text_path = wx.StaticText(self, label="TEXT: (未選択)")
        self.tc_text_preview = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc_hiragana_preview = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc_vowel_preview = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        # WAV info
        self.st_wav_path = wx.StaticText(self, label="WAV: (未選択)")
        self.tc_wav_info = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        sizer.Add(self.st_text_path, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.StaticText(self, label="テキスト:"), 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.tc_text_preview, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.StaticText(self, label="ひらがな:"), 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.tc_hiragana_preview, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.StaticText(self, label="母音:"), 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.tc_vowel_preview, 1, wx.ALL | wx.EXPAND, 5)

        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(self.st_wav_path, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.StaticText(self, label="WAV情報:"), 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.tc_wav_info, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer)

    # --- View Helpers ---
    def set_text_path(self, path: str):
        self.st_text_path.SetLabel(f"TEXT: {path}")

    def set_wav_path(self, path: str):
        self.st_wav_path.SetLabel(f"WAV: {path}")

    def set_text_preview(self, text: str):
        self.tc_text_preview.SetValue(text)

    def set_hiragana_preview(self, text: str):
        self.tc_hiragana_preview.SetValue(text)

    def set_vowel_preview(self, text: str):
        self.tc_vowel_preview.SetValue(text)

    def set_wav_info(self, info: str):
        self.tc_wav_info.SetValue(info)
