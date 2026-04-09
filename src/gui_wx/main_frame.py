import wx

class MainFrame(wx.Frame):
    """
    MMD_AutoLipTool のメインフレーム。
    [MS13-B1] メニューやステータスバー等のレイアウトはB2以降で実装するため、
    このクラスは起動用として「クラッシュしない空のフレーム」を維持します。
    """
    def __init__(self, *args, **kw):
        if 'title' not in kw:
            kw['title'] = "MMD AutoLipTool"
        if 'size' not in kw:
            kw['size'] = (800, 600)
            
        super().__init__(*args, **kw)
        
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
    def _on_close(self, event: wx.CloseEvent):
        # 現時点では単にウィンドウを破棄するのみ。
        # 後続ブロックにて終了確認処理などを追加します。
        self.Destroy()
