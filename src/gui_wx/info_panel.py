import wx
from gui_wx.theme import ThemeButton, ThemeManager

class InfoPanel(wx.Panel):
    """
    [MS14-B1] 左側情報パネル。
    TEXT/WAVのパス、パース結果プレビュー、WAV情報を表示する。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._ms33c_theme_border = True
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self._init_ui()

    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        ThemeManager.draw_border(dc, self.GetClientRect(), self)

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # TEXT info
        self.st_text_path = wx.StaticText(self, label="TEXT: (未選択)")
        editable_tc_style = wx.TE_MULTILINE | wx.BORDER_SIMPLE
        readonly_tc_style = wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE
        self.tc_text_preview = wx.TextCtrl(self, style=editable_tc_style)
        self.tc_text_preview.SetEditable(False)
        self._text_preview_editable = False
        self.tc_hiragana_preview = wx.TextCtrl(self, style=readonly_tc_style)
        self.tc_vowel_preview = wx.TextCtrl(self, style=readonly_tc_style)
        self.btn_apply_transcription_edit = ThemeButton(self, label="適用")
        self.btn_revert_transcription_edit = ThemeButton(self, label="元に戻す")
        self.set_transcription_edit_controls_enabled(False)

        # WAV info
        self.st_wav_path = wx.StaticText(self, label="WAV: (未選択)")
        self.tc_wav_info = wx.TextCtrl(self, style=readonly_tc_style)

        sizer.Add(self.st_text_path, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.StaticText(self, label="テキスト:"), 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.tc_text_preview, 1, wx.ALL | wx.EXPAND, 5)
        edit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        edit_sizer.AddStretchSpacer()
        edit_sizer.Add(self.btn_apply_transcription_edit, 0, wx.RIGHT, 5)
        edit_sizer.Add(self.btn_revert_transcription_edit, 0)
        sizer.Add(edit_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
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

    def get_text_preview(self) -> str:
        return self.tc_text_preview.GetValue()

    def set_text_preview_editable(self, enabled: bool):
        self._text_preview_editable = bool(enabled)
        self.tc_text_preview.SetEditable(self._text_preview_editable)

    def is_text_preview_editable(self) -> bool:
        return self._text_preview_editable

    def set_transcription_edit_controls_enabled(self, enabled: bool):
        self.btn_apply_transcription_edit.Enable(enabled)
        self.btn_revert_transcription_edit.Enable(enabled)

    def bind_transcription_edit_handlers(self, apply_handler, revert_handler):
        self.Bind(wx.EVT_BUTTON, apply_handler, self.btn_apply_transcription_edit)
        self.Bind(wx.EVT_BUTTON, revert_handler, self.btn_revert_transcription_edit)

    def set_hiragana_preview(self, text: str):
        self.tc_hiragana_preview.SetValue(text)

    def set_vowel_preview(self, text: str):
        self.tc_vowel_preview.SetValue(text)

    def set_wav_info(self, info: str):
        self.tc_wav_info.SetValue(info)

    def reset_workspace_display(self):
        """Restore all workspace-specific fields to their initial display."""
        self.st_text_path.SetLabel("TEXT: (未選択)")
        self.st_wav_path.SetLabel("WAV: (未選択)")
        self.set_text_preview("")
        self.set_hiragana_preview("")
        self.set_vowel_preview("")
        self.set_wav_info("")
        self.set_text_preview_editable(False)
        self.set_transcription_edit_controls_enabled(False)
