import wx
import ctypes
import os

class PlaybackController:
    """
    [MS15-B3]
    追加依存なしで WAV を再生し、約50ms周期で位置を通知する最小コントローラ。
    バックエンドには Windows MCI (mciSendString) を使用する。
    """
    def __init__(self, update_callback, finished_callback):
        self.update_callback = update_callback
        self.finished_callback = finished_callback
        
        self._timer = wx.Timer()
        self._timer.Bind(wx.EVT_TIMER, self._on_timer)
        self._alias = "mmd_autoliptool_mci"
        
        self.winmm = ctypes.windll.winmm
        self.mciSendString = self.winmm.mciSendStringW

    def _mci_command(self, command: str) -> str:
        buf = ctypes.create_unicode_buffer(256)
        error_code = self.mciSendString(command, buf, 255, 0)
        if error_code:
            return ""
        return buf.value.strip()

    def play(self, wav_path: str) -> bool:
        self.stop() # stop existing playback

        if not wav_path or not os.path.exists(wav_path):
            return False

        # Load file
        cmd_open = f'open "{wav_path}" type waveaudio alias {self._alias}'
        if self.mciSendString(cmd_open, None, 0, 0) != 0:
            return False

        # Start playing
        cmd_play = f'play {self._alias}'
        if self.mciSendString(cmd_play, None, 0, 0) != 0:
            self.stop()
            return False

        self._timer.Start(50)
        return True

    def stop(self):
        self._timer.Stop()
        self.mciSendString(f'stop {self._alias}', None, 0, 0)
        self.mciSendString(f'close {self._alias}', None, 0, 0)

    def _on_timer(self, event):
        pos_str = self._mci_command(f'status {self._alias} position')
        mode_str = self._mci_command(f'status {self._alias} mode')
        
        if pos_str.isdigit():
            pos_sec = float(pos_str) / 1000.0
            self.update_callback(pos_sec)

        if mode_str == "stopped":
            self.stop()
            self.finished_callback()
