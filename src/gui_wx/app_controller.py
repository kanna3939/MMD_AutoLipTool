import wx
import os
from gui.settings_store import SettingsStore
from core import generate_vmd_from_text_wav

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
    def __init__(self, view):
        self.view = view
        self.worker_hooks = WorkerHooks(self)
        self.settings_store = SettingsStore()
        
        self._coalesced_save_timer = wx.Timer()
        self.view.Bind(wx.EVT_TIMER, self._on_save_timer, self._coalesced_save_timer)
        self._pending_save = False
        self._first_save_failure = False

    def update_status(self, message: str):
        if self.view:
            self.view.update_status(message)

    def _on_save_timer(self, event):
        self.flush_pending_save()

    def flush_pending_save(self, is_closing=False):
        if not self._pending_save or not self.view:
            return
            
        if self.view.ui_state.is_busy:
            return
            
        self._pending_save = False
        st = self.view.ui_state
        settings_dict = {
            "recent_text_files": st.recent_text_files,
            "recent_wav_files": st.recent_wav_files,
            "last_vmd_output_dir": st.last_vmd_output_dir or "",
            "last_text_dialog_dir": st.last_text_dialog_dir or "",
            "last_wav_dialog_dir": st.last_wav_dialog_dir or "",
            "morph_upper_limit": self.view.get_morph_upper_limit(),
            "closing_hold_frames": self.view.get_closing_hold_frames(),
            "closing_softness_frames": self.view.get_closing_softness_frames(),
        }
        
        result = self.settings_store.save(settings_dict)
        if not result.succeeded:
            if not is_closing and not self._first_save_failure:
                self._first_save_failure = True
                wx.MessageBox(f"設定の保存に失敗しました。\n{result.error_message}", "保存エラー", wx.OK | wx.ICON_WARNING)
        else:
            self._first_save_failure = False

    def request_select_text(self):
        self.update_status("TEXTファイル選択要求 (Stub)")

    def request_select_wav(self):
        self.update_status("WAVファイル選択要求 (Stub)")

    def request_save_vmd(self):
        if not self.view: return
        st = self.view.ui_state
        if not st.analysis_result_valid or not st.current_timing_plan:
            return
        if st.is_busy:
            return
            
        default_dir = st.last_vmd_output_dir or ""
        path = self.view.show_vmd_save_dialog_and_get_path(default_dir)
        if not path:
            return
            
        try:
            generate_vmd_from_text_wav(
                text_path=st.selected_text_path,
                wav_path=st.selected_wav_path,
                output_path=path,
                timing_plan=st.current_timing_plan,
                closing_hold_frames=self.view.get_closing_hold_frames(),
                closing_softness_frames=self.view.get_closing_softness_frames(),
                upper_limit=self.view.get_morph_upper_limit()
            )
        except Exception as e:
            wx.MessageBox(f"VMDファイルの保存に失敗しました。\n{e}", "保存エラー", wx.OK | wx.ICON_ERROR)
            self.update_status("VMD保存失敗")
            return
            
        st.last_vmd_output_dir = os.path.dirname(path)
        self.update_status("VMD保存成功")
        self.request_settings_save()

    def request_run_analysis(self):
        self.update_status("解析実行要求 (Stub)")

    def request_playback_play(self):
        self.update_status("再生要求 (Stub)")

    def request_playback_pause(self):
        self.update_status("一時停止要求 (Stub)")

    def request_playback_stop(self):
        self.update_status("停止要求 (Stub)")

    def request_open_settings_dialog(self):
        self.update_status("設定画面表示要求 (Stub)")
        
    def request_open_help(self):
        self.update_status("ヘルプ表示要求 (Stub)")

    def request_show_about(self):
        self.update_status("About表示要求 (Stub)")
        
    def request_exit(self):
        if self._pending_save:
            if self.view: 
                self.view.ui_state.set_busy(False)
            self.flush_pending_save(is_closing=True)
            
        if self.view:
            self.view.Destroy()

    def on_settings_changed(self):
        self.request_settings_save()

    def request_settings_save(self):
        self._pending_save = True
        self._coalesced_save_timer.Start(500, wx.TIMER_ONE_SHOT)

    def reapply_settings_to_view(self):
        pass
