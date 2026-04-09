import wx

class MainFrame(wx.Frame):
    """
    MMD_AutoLipTool のメインフレーム。
    [MS13-B3]
    - 上中下3領域へレイアウトする最小骨格の上に、
    - 最小メニューバー、主要ボタン、ステータス表示の受け口を配置。
    """
    def __init__(self, *args, **kw):
        if 'title' not in kw:
            kw['title'] = "MMD AutoLipTool"
        if 'size' not in kw:
            kw['size'] = (800, 600)
            
        super().__init__(*args, **kw)
        
        self.controller = None
        
        self._init_menu()
        self._init_ui()
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
    def _init_menu(self):
        menubar = wx.MenuBar()
        
        # 1. ファイルメニュー
        file_menu = wx.Menu()
        self.mi_text_open = file_menu.Append(wx.ID_ANY, "TEXT読み込み...\tCtrl+T", "UTF-8のテキストファイルを読み込みます")
        self.mi_wav_open = file_menu.Append(wx.ID_ANY, "WAV読み込み...\tCtrl+W", "音源のWAVファイルを読み込みます")
        self.mi_vmd_save = file_menu.Append(wx.ID_ANY, "VMD保存...\tCtrl+S", "解析結果をVMDとして保存します")
        file_menu.AppendSeparator()
        self.mi_exit = file_menu.Append(wx.ID_EXIT, "終了(&X)", "アプリケーションを終了します")
        menubar.Append(file_menu, "ファイル(&F)")
        
        # 2. 設定/表示メニュー
        view_menu = wx.Menu()
        self.mi_settings = view_menu.Append(wx.ID_ANY, "設定(&S)...", "各種設定を行います")
        menubar.Append(view_menu, "設定/表示(&V)")
        
        # 3. ヘルプメニュー
        help_menu = wx.Menu()
        self.mi_help = help_menu.Append(wx.ID_ANY, "使い方(&H)...", "使い方を確認します")
        self.mi_about = help_menu.Append(wx.ID_ABOUT, "About(&A)...", "このアプリについて")
        menubar.Append(help_menu, "ヘルプ(&H)")
        
        self.SetMenuBar(menubar)
        
        # [MS13-B3] 未実装項目は無効化(Disabled)とする
        self.mi_text_open.Enable(False)
        self.mi_wav_open.Enable(False)
        self.mi_vmd_save.Enable(False)
        self.mi_settings.Enable(False)
        self.mi_help.Enable(False)
        self.mi_about.Enable(False)
        
        # [MS13-B5] メニューイベントのバインディング
        # UI側イベントを検知し、分離された _on_mi_* ハンドラへルーティングする
        self.Bind(wx.EVT_MENU, self._on_mi_text_open, self.mi_text_open)
        self.Bind(wx.EVT_MENU, self._on_mi_wav_open, self.mi_wav_open)
        self.Bind(wx.EVT_MENU, self._on_mi_vmd_save, self.mi_vmd_save)
        self.Bind(wx.EVT_MENU, self._on_mi_settings, self.mi_settings)
        self.Bind(wx.EVT_MENU, self._on_mi_help, self.mi_help)
        self.Bind(wx.EVT_MENU, self._on_mi_about, self.mi_about)
        self.Bind(wx.EVT_MENU, self._on_close, self.mi_exit)

    def _init_ui(self):
        self.root_panel = wx.Panel(self)
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- 1. 上部操作域 (Top Area) ---
        self.top_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 主要操作ボタン群の配置
        self.btn_open_text = wx.Button(self.top_panel, label="TEXT 読込")
        self.btn_open_wav = wx.Button(self.top_panel, label="WAV 読込")
        self.btn_process = wx.Button(self.top_panel, label="解析実行")
        self.btn_save_vmd = wx.Button(self.top_panel, label="VMD 保存")
        
        self.btn_play = wx.Button(self.top_panel, label="Play")
        self.btn_stop = wx.Button(self.top_panel, label="Stop")
        
        # [MS13-B3] 未実装ボタンは無効化(Disabled)とする
        self.btn_open_text.Disable()
        self.btn_open_wav.Disable()
        self.btn_process.Disable()
        self.btn_save_vmd.Disable()
        self.btn_play.Disable()
        self.btn_stop.Disable()
        
        # レイアウト追加
        flags_btn = wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL
        top_sizer.Add(self.btn_open_text, 0, flags_btn, 5)
        top_sizer.Add(self.btn_open_wav, 0, flags_btn, 5)
        top_sizer.Add(self.btn_process, 0, flags_btn, 5)
        top_sizer.Add(self.btn_save_vmd, 0, flags_btn, 5)
        
        # 再生ボタン群の置き場 (B3方針に基づき見せるだけ)
        top_sizer.AddSpacer(20)
        top_sizer.Add(self.btn_play, 0, flags_btn, 5)
        top_sizer.Add(self.btn_stop, 0, flags_btn | wx.RIGHT, 5)
        
        self.top_panel.SetSizer(top_sizer)
        
        # --- 2. 中央主領域 (Center Area) ---
        self.center_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        center_sizer = wx.BoxSizer(wx.VERTICAL)
        center_label = wx.StaticText(self.center_panel, label="[Placeholder] 波形 / Preview エリア")
        center_sizer.Add(center_label, 0, wx.ALL, 5)
        self.center_panel.SetSizer(center_sizer)
        
        # --- 3. 下部ステータス域 (Bottom Area) ---
        self.bottom_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        # 将来拡張(進捗バー等)しやすいよう水平Sizerを採用
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.st_status_main = wx.StaticText(self.bottom_panel, label="準備完了 (WX Mode)")
        
        # 左側に主要ステータス、右側に可変幅などの拡張余地を残すレイアウト設計
        bottom_sizer.Add(self.st_status_main, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.bottom_panel.SetSizer(bottom_sizer)
        
        # --- ルートサイザーへの各領域の組み込み ---
        # 上部: 高さ固定 (proportion=0)
        root_sizer.Add(self.top_panel, 0, wx.EXPAND | wx.ALL, 5)
        # 中央: 主領域として残りの縦幅を埋める (proportion=1)
        root_sizer.Add(self.center_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        # 下部: 高さ固定 (proportion=0)
        root_sizer.Add(self.bottom_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.root_panel.SetSizer(root_sizer)
        
        # [MS13-B5] 実要素はDisabledのままだが、将来の拡張に備えてイベントバインドは済ませておく
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_text, self.btn_open_text)
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_wav, self.btn_open_wav)
        self.Bind(wx.EVT_BUTTON, self._on_btn_process, self.btn_process)
        self.Bind(wx.EVT_BUTTON, self._on_btn_save_vmd, self.btn_save_vmd)
        self.Bind(wx.EVT_BUTTON, self._on_btn_play, self.btn_play)
        self.Bind(wx.EVT_BUTTON, self._on_btn_stop, self.btn_stop)
        
    def set_controller(self, controller):
        """[MS13-B5] アプリのコントローラーをセットし、各種操作要求を委譲する口を設ける"""
        self.controller = controller

    def update_status(self, message: str):
        """[MS13-B5] UI上のステータス表示更新を一元化する共通入口"""
        self.st_status_main.SetLabel(message)

    def get_status_text(self) -> str:
        """[MS13-B5] 最小限の View Accessor (将来取得が必要になった場合の整理用)"""
        return self.st_status_main.GetLabel()

    def _on_close(self, event: wx.Event):
        if self.controller:
            self.controller.request_exit()
        else:
            self.Destroy()

    # --- UI Event Handlers ([MS13-B5] UI イベントを Action Sink へ流す) ---
    def _on_mi_text_open(self, event):
        if self.controller: self.controller.request_select_text()

    def _on_mi_wav_open(self, event):
        if self.controller: self.controller.request_select_wav()

    def _on_mi_vmd_save(self, event):
        if self.controller: self.controller.request_save_vmd()

    def _on_mi_settings(self, event):
        if self.controller: self.controller.request_open_settings_dialog()

    def _on_mi_help(self, event):
        if self.controller: self.controller.request_open_help()

    def _on_mi_about(self, event):
        if self.controller: self.controller.request_show_about()

    def _on_btn_open_text(self, event):
        if self.controller: self.controller.request_select_text()

    def _on_btn_open_wav(self, event):
        if self.controller: self.controller.request_select_wav()

    def _on_btn_process(self, event):
        if self.controller: self.controller.request_run_analysis()

    def _on_btn_save_vmd(self, event):
        if self.controller: self.controller.request_save_vmd()

    def _on_btn_play(self, event):
        if self.controller: self.controller.request_playback_play()

    def _on_btn_stop(self, event):
        if self.controller: self.controller.request_playback_stop()

    def apply_settings(self, settings: dict):
        """
        [MS13-B4] 起動時の設定反映。
        B3の時点で存在する wx 側の UI (メインフレームのサイズ等) に対してのみ設定を反映します。
        未配置の control (スプリッター等) への適用はスキップします。
        """
        # --- 1. ウィンドウ関連の設定適用 ---
        raw_width = settings.get("window_width")
        raw_height = settings.get("window_height")
        
        width = raw_width if isinstance(raw_width, int) and raw_width > 0 else 800
        height = raw_height if isinstance(raw_height, int) and raw_height > 0 else 600
        
        self.SetSize(wx.Size(width, height))
        self.Centre(wx.BOTH)
        
        # --- 2. B3 までの実在 UI に関する設定 ---
        # (現在、操作ボタンなどの表示状態に直接影響する初期設定項目はないため、ここで完了とする。)
        pass
