import wx
import os
from pathlib import Path

from gui_wx.info_panel import InfoPanel
from gui_wx.placeholder_panels import PlaceholderContainer
from gui_wx.parameter_panel import ParameterPanel
from gui_wx.ui_state import UiState, StatusKey
from gui_wx.analysis_worker import AnalysisWorker

from core.text_processing import TextProcessingError, text_to_hiragana, hiragana_to_vowel_string, _validate_and_clean_text
from core.audio_processing import analyze_wav_file, WavAnalysisResult

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
        self.ui_state = UiState()
        
        self._init_menu()
        self._init_ui()
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
    def _init_menu(self):
        menubar = wx.MenuBar()
        
        # 1. ファイルメニュー
        file_menu = wx.Menu()
        self.mi_text_open = file_menu.Append(wx.ID_ANY, "TEXT読み込み...\tCtrl+T", "UTF-8のテキストファイルを読み込みます")
        self.mi_wav_open = file_menu.Append(wx.ID_ANY, "WAV読み込み...\tCtrl+W", "音源のWAVファイルを読み込みます")
        
        # [MS14-B2] recent menu 相当
        self.recent_menu = wx.Menu()
        self.mi_recent = file_menu.AppendSubMenu(self.recent_menu, "最近開いたファイル")
        
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
        
        # [MS13-B3] 未実装項目は無効化 / [MS14-B2] これらは update_action_states 側で管理するが、
        # メニュー自体への初期設定も一部残す（update_action_statesで再設定される）
        
        # [MS13-B5] メニューイベントのバインディング
        # UI側イベントを検知し、_open_text_file等へルーティングする
        self.Bind(wx.EVT_MENU, lambda e: self._open_text_file(), self.mi_text_open)
        self.Bind(wx.EVT_MENU, lambda e: self._open_wav_file(), self.mi_wav_open)
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
        
        # ※ 各ボタンのEnable/Disableは _init_ui の最後にある update_action_states() にて一括管理する
        
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
        
        # --- 1.5. パラメータ入力行 (Parameter Area) [MS14-B1] ---
        self.param_panel = ParameterPanel(self.root_panel)
        
        # --- 2. 中央主領域 (Center Area) [MS14-B1] ---
        self.center_panel = wx.Panel(self.root_panel)
        center_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左側情報パネルと右側プレースホルダコンテナを配置
        self.info_panel = InfoPanel(self.center_panel)
        self.placeholder_container = PlaceholderContainer(self.center_panel)
        
        # 1:2程度の幅比率で配置
        center_sizer.Add(self.info_panel, 1, wx.EXPAND | wx.RIGHT, 5)
        center_sizer.Add(self.placeholder_container, 2, wx.EXPAND | wx.LEFT, 5)
        self.center_panel.SetSizer(center_sizer)
        
        # --- 3. 下部ステータス域 (Bottom Area) ---
        self.bottom_panel = wx.Panel(self.root_panel, style=wx.BORDER_SIMPLE)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.st_status_main = wx.StaticText(self.bottom_panel, label="準備完了 (WX Mode)")
        
        # 左側に主要ステータス、右側に可変幅などの拡張余地を残すレイアウト設計
        bottom_sizer.Add(self.st_status_main, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.bottom_panel.SetSizer(bottom_sizer)
        
        # --- ルートサイザーへの各領域の組み込み ---
        root_sizer.Add(self.top_panel, 0, wx.EXPAND | wx.ALL, 5)
        root_sizer.Add(self.param_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        root_sizer.Add(self.center_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        root_sizer.Add(self.bottom_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.root_panel.SetSizer(root_sizer)
        self.root_panel.Layout()
        
        # [MS13-B5] 実要素へのイベントバインド
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_text, self.btn_open_text)
        self.Bind(wx.EVT_BUTTON, self._on_btn_open_wav, self.btn_open_wav)
        self.Bind(wx.EVT_BUTTON, self._on_btn_process, self.btn_process)
        self.Bind(wx.EVT_BUTTON, self._on_btn_save_vmd, self.btn_save_vmd)
        self.Bind(wx.EVT_BUTTON, self._on_btn_play, self.btn_play)
        self.Bind(wx.EVT_BUTTON, self._on_btn_stop, self.btn_stop)
        
        # [MS14-B2] UI生成後に Action State と Status表示を状態に合わせて初期化
        self.update_action_states()
        self.update_status_display()

    def update_action_states(self):
        """
        [MS14-B2] UiState に基づき、UI コントロールの有効/無効を判定・反映する
        """
        state = self.ui_state
        busy = state.is_busy

        # --- 基本入力 (busy 中のみ lock) ---
        self.btn_open_text.Enable(not busy)
        self.btn_open_wav.Enable(not busy)
        
        self.mi_text_open.Enable(not busy)
        self.mi_wav_open.Enable(not busy)
        
        # recent menu slot (MS14-B2 lock対象)
        self.mi_recent.Enable(not busy)
        
        # --- パラメータ入力 (busy時ロック) ---
        self.param_panel.enable_inputs(not busy)

        # --- 解析実行 ---
        # TEXT と WAV の両方のパスが揃っている場合のみ有効 (かつ非busy)
        can_analyze = bool(state.selected_text_path and state.selected_wav_path)
        self.btn_process.Enable(can_analyze and not busy)

        # --- VMD 保存 ---
        # 解析結果が有効な場合のみ有効 (かつ非busy)
        self.btn_save_vmd.Enable(state.analysis_result_valid and not busy)
        self.mi_vmd_save.Enable(state.analysis_result_valid and not busy)

        # --- B2時点の未実装項目 (常時disabled) ---
        # 将来の再生系
        self.btn_play.Enable(False)
        self.btn_stop.Enable(False)
        # 設定・ヘルプ
        self.mi_settings.Enable(False)
        self.mi_help.Enable(False)
        self.mi_about.Enable(False)


    def update_status_display(self):
        """
        [MS14-B2] StatusKey に基づいてステータスバーの文言を更新
        """
        key = self.ui_state.status_key
        
        msg_map = {
            StatusKey.IDLE: "準備完了 (WX Mode)",
            StatusKey.INPUT_MISSING: "TEXT および WAV を読み込んでください",
            StatusKey.READY_FOR_ANALYSIS: "準備完了 (解析を実行できます)",
            StatusKey.ANALYSIS_INVALIDATED: "入力が変更されました (再解析が必要)",
            StatusKey.BUSY: "処理中...",
            StatusKey.ANALYSIS_READY: "解析完了 (VMD出力可能)"
        }
        
        msg = msg_map.get(key, "...")
        self.update_status(msg)
        
    def set_controller(self, controller):
        """[MS13-B5] アプリのコントローラーをセットし、各種操作要求を委譲する口を設ける"""
        self.controller = controller

    def update_status(self, message: str):
        """[MS13-B5] UI上のステータス表示更新を一元化する共通入口"""
        self.st_status_main.SetLabel(message)

    def get_status_text(self) -> str:
        """[MS13-B5] 最小限の View Accessor (将来取得が必要になった場合の整理用)"""
        return self.st_status_main.GetLabel()

    # --- MS14-B1 View Helpers ---
    def set_text_path(self, path: str):
        self.info_panel.set_text_path(path)
        
    def set_wav_path(self, path: str):
        self.info_panel.set_wav_path(path)
        
    def set_text_preview(self, text: str):
        self.info_panel.set_text_preview(text)
        
    def set_hiragana_preview(self, text: str):
        self.info_panel.set_hiragana_preview(text)
        
    def set_vowel_preview(self, text: str):
        self.info_panel.set_vowel_preview(text)
        
    def set_wav_info(self, info: str):
        self.info_panel.set_wav_info(info)

    def set_waveform_placeholder_text(self, text: str):
        self.placeholder_container.set_waveform_placeholder_text(text)
        
    def set_preview_placeholder_text(self, text: str):
        self.placeholder_container.set_preview_placeholder_text(text)
        
    def get_morph_upper_limit(self) -> float:
        return self.param_panel.get_morph_upper_limit()
        
    def set_morph_upper_limit(self, val: float):
        self.param_panel.set_morph_upper_limit(val)
        
    def get_closing_hold_frames(self) -> int:
        return self.param_panel.get_closing_hold_frames()
        
    def set_closing_hold_frames(self, val: int):
        self.param_panel.set_closing_hold_frames(val)
        
    def get_closing_softness_frames(self) -> int:
        return self.param_panel.get_closing_softness_frames()
        
    def set_closing_softness_frames(self, val: int):
        self.param_panel.set_closing_softness_frames(val)

    def show_vmd_save_dialog_and_get_path(self, default_dir: str):
        with wx.FileDialog(
            self,
            message="VMDファイルの保存先を指定してください",
            defaultDir=default_dir,
            wildcard="VMD files (*.vmd)|*.vmd",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return None
            path = dialog.GetPath()
            if not path.endswith('.vmd'):
                path += '.vmd'
            return path

    def _build_recent_menus(self):
        st = self.ui_state
        pruned = False
        
        valid_texts = []
        for p in st.recent_text_files:
            if os.path.exists(p) and os.path.isfile(p):
                valid_texts.append(p)
            elif p:
                pruned = True
                
        valid_wavs = []
        for p in st.recent_wav_files:
            if os.path.exists(p) and os.path.isfile(p):
                valid_wavs.append(p)
            elif p:
                pruned = True
                
        st.recent_text_files = valid_texts
        st.recent_wav_files = valid_wavs
        
        for item in self.recent_menu.GetMenuItems():
            self.recent_menu.Delete(item)
            
        for p in valid_texts:
            item = self.recent_menu.Append(wx.ID_ANY, f"TEXT: {os.path.basename(p)}")
            self.Bind(wx.EVT_MENU, lambda e, path=p: self._on_recent_text(path), item)
            
        if valid_texts and valid_wavs:
            self.recent_menu.AppendSeparator()
            
        for p in valid_wavs:
            item = self.recent_menu.Append(wx.ID_ANY, f"WAV: {os.path.basename(p)}")
            self.Bind(wx.EVT_MENU, lambda e, path=p: self._on_recent_wav(path), item)
            
        if pruned and self.controller:
            self.controller.request_settings_save()

    def _on_recent_text(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            wx.MessageBox("指定された履歴ファイルが見つかりません。", "読込エラー", wx.OK | wx.ICON_WARNING)
            self._build_recent_menus()
            return
        self._open_text_file(quiet_path=path)

    def _on_recent_wav(self, path):
        if not os.path.exists(path) or not os.path.isfile(path):
            wx.MessageBox("指定された履歴ファイルが見つかりません。", "読込エラー", wx.OK | wx.ICON_WARNING)
            self._build_recent_menus()
            return
        self._open_wav_file(quiet_path=path)
        
    def get_closing_softness_frames(self) -> int:
        return self.param_panel.get_closing_softness_frames()
        
    def set_closing_softness_frames(self, val: int):
        self.param_panel.set_closing_softness_frames(val)

    def _on_close(self, event: wx.Event):
        if self.controller:
            self.controller.request_exit()
        else:
            self.Destroy()

    # --- UI Event Handlers ([MS13-B5] UI イベントを Action Sink へ流す) ---
    # --- メニューイベントハンドラはボタン側と同じ_openメソッドを呼ぶため削除 ---
    # def _on_mi_text_open(self, event) ... は直接 lambda 等で割り当てる

    def _on_mi_vmd_save(self, event):
        if self.controller: self.controller.request_save_vmd()

    def _on_mi_settings(self, event):
        if self.controller: self.controller.request_open_settings_dialog()

    def _on_mi_help(self, event):
        if self.controller: self.controller.request_open_help()

    def _on_mi_about(self, event):
        if self.controller: self.controller.request_show_about()

    def _on_btn_open_text(self, event):
        self._open_text_file()

    def _on_btn_open_wav(self, event):
        self._open_wav_file()
        
    def _open_text_file(self, quiet_path: str = None):
        """ [MS14-B3] TEXTファイルを開き、処理してGUIに反映する """
        if quiet_path is None:
            dialog_dir = self.ui_state.last_text_dialog_dir or ""
            with wx.FileDialog(
                self,
                message="テキストファイルを選択してください",
                defaultDir=dialog_dir,
                wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                path = file_dialog.GetPath()
                self.ui_state.last_text_dialog_dir = file_dialog.GetDirectory()
        else:
            path = quiet_path

        # 妥当性確認
        if not path:
            return
        if not os.path.exists(path):
            if not quiet_path:
                wx.MessageBox("指定されたファイルが見つかりません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if os.path.isdir(path):
            if not quiet_path:
                wx.MessageBox("ファイルではなくディレクトリが選択されました。", "エラー", wx.OK | wx.ICON_ERROR)
            return

        # 読込ループ (想定外例外、UnicodeDecodeErrorを捕捉)
        text_content = ""
        try:
            for enc in ["utf-8-sig", "utf-8"]:
                try:
                    with open(path, "r", encoding=enc) as f:
                        text_content = f.read()
                    break
                except UnicodeDecodeError:
                    pass
            else:
                raise ValueError("未対応のエンコーディング")
        except Exception as e:
            if not quiet_path:
                wx.MessageBox(f"テキストの読み込み処理でエラーが発生しました。\n{e}", "読込エラー", wx.OK | wx.ICON_ERROR)
            return

        # 変換
        try:
            clean_text = _validate_and_clean_text(text_content)
            hiragana = text_to_hiragana(text_content)
            vowel = hiragana_to_vowel_string(hiragana)
        except TextProcessingError as e:
            if not quiet_path:
                wx.MessageBox(f"テキストの変換処理でエラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            return
        except Exception as e:
            if not quiet_path:
                wx.MessageBox(f"想定外の変換エラーが発生しました。\n{e}", "変換エラー", wx.OK | wx.ICON_ERROR)
            return

        # State 更新
        self.ui_state.selected_text_path = path
        self.ui_state.last_text_dialog_dir = os.path.dirname(path)
        self.ui_state.selected_text_content = clean_text
        self.ui_state.selected_hiragana_content = hiragana
        self.ui_state.selected_vowel_content = vowel
        self.ui_state.invalidate_analysis()

        # RECENT更新
        if path in self.ui_state.recent_text_files:
            self.ui_state.recent_text_files.remove(path)
        self.ui_state.recent_text_files.insert(0, path)
        self._build_recent_menus()
        if self.controller:
            self.controller.request_settings_save()

        # UI 反映
        basename = os.path.basename(path)
        self.info_panel.set_text_path(basename)
        self.info_panel.set_text_preview(clean_text)
        self.info_panel.set_hiragana_preview(hiragana)
        self.info_panel.set_vowel_preview(vowel)

        # Action State & Status 更新
        # auto load 試行前に一旦更新し、GUI全体の整合性を担保
        if self.ui_state.selected_wav_path:
            self.ui_state.mark_ready_for_analysis()
        self.update_action_states()
        self.update_status_display()

        # Counterpart auto load (quiet_path == Noneの主導線の時のみ1回実行し、既読でないなら)
        if quiet_path is None:
            stem = Path(path).stem
            wav_path = str(Path(path).with_name(stem + ".wav"))
            if not self.ui_state.selected_wav_path:
                self._open_wav_file(quiet_path=wav_path)

    def _open_wav_file(self, quiet_path: str = None):
        """ [MS14-B3] WAVファイルを開き、処理してGUIに反映する """
        if quiet_path is None:
            dialog_dir = self.ui_state.last_wav_dialog_dir or ""
            with wx.FileDialog(
                self,
                message="WAVファイルを選択してください",
                defaultDir=dialog_dir,
                wildcard="Wav files (*.wav)|*.wav|All files (*.*)|*.*",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                path = file_dialog.GetPath()
                self.ui_state.last_wav_dialog_dir = file_dialog.GetDirectory()
        else:
            path = quiet_path

        # 妥当性確認
        if not path:
            return
        if not os.path.exists(path):
            if not quiet_path:
                wx.MessageBox("指定されたファイルが見つかりません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if os.path.isdir(path):
            if not quiet_path:
                wx.MessageBox("ファイルではなくディレクトリが選択されました。", "エラー", wx.OK | wx.ICON_ERROR)
            return

        # 解析
        try:
            analysis = analyze_wav_file(path)
        except Exception as e:
            if not quiet_path:
                wx.MessageBox(f"WAVの解析に失敗しました。\n{e}", "解析エラー", wx.OK | wx.ICON_ERROR)
            return

        # State 更新
        self.ui_state.selected_wav_path = path
        self.ui_state.last_wav_dialog_dir = os.path.dirname(path)
        self.ui_state.selected_wav_analysis = analysis
        self.ui_state.invalidate_analysis()

        # RECENT更新
        if path in self.ui_state.recent_wav_files:
            self.ui_state.recent_wav_files.remove(path)
        self.ui_state.recent_wav_files.insert(0, path)
        self._build_recent_menus()
        if self.controller:
            self.controller.request_settings_save()

        # UI 反映
        basename = os.path.basename(path)
        self.info_panel.set_wav_path(basename)
        info_text = f"Sample Rate: {analysis.sample_rate_hz}Hz\nChannels: {analysis.channel_count}\nDuration: {analysis.duration_sec:.2f}s"
        self.info_panel.set_wav_info(info_text)
        self.placeholder_container.set_waveform_placeholder_text(f"{basename}\n(MS15で波形描画予定)")

        if self.ui_state.selected_text_path:
            self.ui_state.mark_ready_for_analysis()
        self.update_action_states()
        self.update_status_display()

        # Counterpart auto load (主導線のみ)
        if quiet_path is None:
            stem = Path(path).stem
            text_path = str(Path(path).with_name(stem + ".txt"))
            if not self.ui_state.selected_text_path:
                self._open_text_file(quiet_path=text_path)

    def _on_btn_process(self, event):
        self._run_analysis()

    def _run_analysis(self):
        """ [MS14-B4] 解析実行の非同期起動 """
        # 開始前の前提条件確認
        if not self.ui_state.selected_text_content:
            wx.MessageBox("TEXTが設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if not self.ui_state.selected_wav_path or not self.ui_state.selected_wav_analysis:
            wx.MessageBox("WAVが設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if self.ui_state.is_busy:
            return  # 二重実行防止
            
        # UIからパラメータを取得
        upper_limit = self.param_panel.get_morph_upper_limit()

        # Busy状態の開始
        self.ui_state.set_busy(True)
        self.update_action_states()
        self.update_status_display()
        
        # 不要なダイアログを出さずにUI操作をブロックするため進捗表示(不定)
        self._progress_dialog = wx.ProgressDialog(
            "解析実行中",
            "リップシンク解析を実行しています...\nしばらくお待ちください。",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )
        self._progress_dialog.Pulse()

        # worker起動
        self._worker = AnalysisWorker(
            callback=self._on_analysis_success,
            error_callback=self._on_analysis_error,
            text_content=self.ui_state.selected_text_content,
            wav_path=self.ui_state.selected_wav_path,
            wav_analysis=self.ui_state.selected_wav_analysis,
            upper_limit=upper_limit
        )
        self._worker.start()

    def _on_analysis_success(self, plan):
        """ [MS14-B4] 解析成功時のコールバック """
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.Destroy()
            self._progress_dialog = None
            
        self.ui_state.mark_analysis_success(plan)
        basename = os.path.basename(self.ui_state.selected_wav_path) if self.ui_state.selected_wav_path else ""
        self.placeholder_container.set_preview_placeholder_text(f"[解析結果あり]\n(MS15でPreview描画予定)")
        self.ui_state.set_busy(False)
        self.update_action_states()
        self.update_status_display()
        self._worker = None
        if self.controller:
            self.controller.flush_pending_save()
        
    def _on_analysis_error(self, error):
        """ [MS14-B4] 解析失敗時のコールバック """
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.Destroy()
            self._progress_dialog = None
            
        self.ui_state.invalidate_analysis()
        self.placeholder_container.set_preview_placeholder_text("[Placeholder] Preview エリア")
        self.ui_state.set_busy(False)
        self.update_action_states()
        self.update_status_display()
        self._worker = None
        if self.controller:
            self.controller.flush_pending_save()
        wx.MessageBox(f"解析中にエラーが発生しました。\n{error}", "エラー", wx.OK | wx.ICON_ERROR)

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
        
        # [MS14-B5] 初期設定からrecent等を反映し、メニュー再構築する 
        # ui_stateにロードされた設定を反映
        self.ui_state.recent_text_files = settings.get("recent_text_files", [])
        self.ui_state.recent_wav_files = settings.get("recent_wav_files", [])
        self.ui_state.last_vmd_output_dir = settings.get("last_vmd_output_dir", "")
        self.ui_state.last_text_dialog_dir = settings.get("last_text_dialog_dir", "")
        self.ui_state.last_wav_dialog_dir = settings.get("last_wav_dialog_dir", "")
        
        # invalid recent除去とメニュー構築（※この時点でのpruneによるsaveは最初の安全なタイミングに任せる）
        self._build_recent_menus()
        
        # パラメータ復元
        limit = settings.get("morph_upper_limit", 0.5)
        self.set_morph_upper_limit(limit)
        hold = settings.get("closing_hold_frames", 0)
        self.set_closing_hold_frames(hold)
        soft = settings.get("closing_softness_frames", 0)
        self.set_closing_softness_frames(soft)
        
        # Parameter変更時のsaveコールバック
        self.param_panel.sc_morph_limit.Bind(wx.EVT_SPINCTRLDOUBLE, lambda e: self._on_param_changed(e))
        self.param_panel.sc_morph_limit.Bind(wx.EVT_TEXT, lambda e: self._on_param_changed(e))
        self.param_panel.sc_hold_frames.Bind(wx.EVT_SPINCTRL, lambda e: self._on_param_changed(e))
        self.param_panel.sc_hold_frames.Bind(wx.EVT_TEXT, lambda e: self._on_param_changed(e))
        self.param_panel.sc_softness_frames.Bind(wx.EVT_SPINCTRL, lambda e: self._on_param_changed(e))
        self.param_panel.sc_softness_frames.Bind(wx.EVT_TEXT, lambda e: self._on_param_changed(e))

    def _on_param_changed(self, event):
        event.Skip()
        if self.controller:
            self.controller.request_settings_save()
