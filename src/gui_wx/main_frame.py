import wx

class MainFrame(wx.Frame):
    """
    MMD_AutoLipTool のメインフレーム。
    [MS13-B2] 内部にルートパネルを持ち、上中下の3領域へレイアウトする最小骨格を担います。
    """
    def __init__(self, *args, **kw):
        if 'title' not in kw:
            kw['title'] = "MMD AutoLipTool"
        if 'size' not in kw:
            kw['size'] = (800, 600)
            
        super().__init__(*args, **kw)
        
        self._init_ui()
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
    def _init_ui(self):
        # ルートパネル (今後のSizerベースレイアウトの基盤)
        self.root_panel = wx.Panel(self)
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 1. 上部操作域 (Top Area)
        self.top_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_label = wx.StaticText(self.top_panel, label="[Placeholder] 上部操作域")
        top_sizer.Add(top_label, 0, wx.ALL, 5)
        self.top_panel.SetSizer(top_sizer)
        
        # 2. 中央主領域 (Center Area)
        # 中央領域が画面全体の残りの領域をすべて占有するように proportion=1 とする
        self.center_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        center_sizer = wx.BoxSizer(wx.VERTICAL)
        center_label = wx.StaticText(self.center_panel, label="[Placeholder] 中央主領域")
        center_sizer.Add(center_label, 0, wx.ALL, 5)
        self.center_panel.SetSizer(center_sizer)
        
        # 3. 下部ステータス域 (Bottom Area)
        self.bottom_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_label = wx.StaticText(self.bottom_panel, label="[Placeholder] 下部ステータス域")
        bottom_sizer.Add(bottom_label, 0, wx.ALL, 5)
        self.bottom_panel.SetSizer(bottom_sizer)
        
        # ルートサイザーへの各領域の組み込み
        # 上部: 高さ固定 (proportion=0), 左右に広がる (wx.EXPAND)
        root_sizer.Add(self.top_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 中央: 主領域として残りの縦幅を埋める (proportion=1), 左右に広がる (wx.EXPAND)
        root_sizer.Add(self.center_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # 下部: 高さ固定 (proportion=0), 左右に広がる (wx.EXPAND)
        root_sizer.Add(self.bottom_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.root_panel.SetSizer(root_sizer)
        
    def _on_close(self, event: wx.CloseEvent):
        # 現時点では単にウィンドウを破棄するのみ。
        # 後続ブロックにて終了確認処理などを追加します。
        self.Destroy()
