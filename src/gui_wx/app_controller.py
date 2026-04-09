import wx

class WorkerHooks:
    """
    [MS13-B5] 将来の非同期処理 (Worker/Thread) との接続スタブ。
    実処理は含めず、将来 thread 等からコールバックされる口として用意する。
    """
    def __init__(self, controller):
        self.controller = controller

    def start_analysis_worker(self):
        self.controller.update_status("Worker: 解析開始要求を受理しました (Stub)")

    def on_analysis_progress(self, current: int, total: int):
        self.controller.update_status(f"Worker: 進捗 {current}/{total} (Stub)")

    def on_analysis_success(self, result):
        self.controller.update_status("Worker: 解析完了 (Stub)")

    def on_analysis_error(self, error: Exception):
        self.controller.update_status(f"Worker: エラー発生 {error} (Stub)")


class AppController:
    """
    [MS13-B5] アプリケーション全体の操作要求（Action Sink）を受け付けるコントローラー領域のスタブ。
    MainFrame側のUIイベントハンドラから呼び出され、今後のマイルストーンで実処理本体に差し替えられる。
    """
    def __init__(self, view):
        self.view = view
        self.worker_hooks = WorkerHooks(self)

    def update_status(self, message: str):
        """GUIのステータス更新をViewへ委譲する"""
        if self.view:
            self.view.update_status(message)

    # --- File Operations ---
    def request_select_text(self):
        self.update_status("TEXTファイル選択要求 (Stub)")

    def request_select_wav(self):
        self.update_status("WAVファイル選択要求 (Stub)")

    def request_save_vmd(self):
        self.update_status("VMD保存要求 (Stub)")

    # --- Analysis ---
    def request_run_analysis(self):
        self.update_status("解析実行要求 (Stub)")
        # 実装時(MS14以降)に self.worker_hooks.start_analysis_worker() などを呼ぶ

    # --- Playback ---
    def request_playback_play(self):
        self.update_status("再生要求 (Stub)")

    def request_playback_pause(self):
        self.update_status("一時停止要求 (Stub)")

    def request_playback_stop(self):
        self.update_status("停止要求 (Stub)")

    # --- Application State ---
    def request_open_settings_dialog(self):
        self.update_status("設定画面表示要求 (Stub)")
        
    def request_open_help(self):
        self.update_status("ヘルプ表示要求 (Stub)")

    def request_show_about(self):
        self.update_status("About表示要求 (Stub)")
        
    def request_exit(self):
        # 現段階では単にウィンドウを閉じる要求を通す
        if self.view:
            self.view.Destroy()

    # --- Settings Hooks ---
    def on_settings_changed(self):
        """将来設定が変更された際にUI等へ再反映を促す通知口"""
        self.update_status("設定変更通知受信 (Stub)")

    def request_settings_save(self):
        """将来設定を保存する際の呼び出し口"""
        self.update_status("設定保存要求 (Stub)")

    def reapply_settings_to_view(self):
        """設定をUIに再反映するための入口（B4の反映処理を再呼出するなど）"""
        pass
