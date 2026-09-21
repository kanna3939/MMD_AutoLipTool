import wx
import ctypes
import os
import shutil
import tempfile
from pathlib import Path


def _mci_accepts_filename(path: str | Path) -> bool:
    path_obj = Path(path)
    suffix = path_obj.suffix
    return len(path_obj.stem) <= 8 and len(suffix) <= 4

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
        self._playback_temp_dir = None
        self._playback_path = None
        
        self.winmm = ctypes.windll.winmm
        self.mciSendString = self.winmm.mciSendStringW

    def _mci_command(self, command: str) -> str:
        buf = ctypes.create_unicode_buffer(256)
        error_code = self.mciSendString(command, buf, 255, 0)
        if error_code:
            return ""
        return buf.value.strip()

    def _prepare_playback_path(self, wav_path: str | Path) -> str:
        path = Path(wav_path)
        if _mci_accepts_filename(path):
            self._playback_path = str(path)
            return self._playback_path

        temp_dir = tempfile.mkdtemp(prefix="mat_mci_")
        temp_path = Path(temp_dir) / "p.wav"
        shutil.copyfile(path, temp_path)
        self._playback_temp_dir = temp_dir
        self._playback_path = str(temp_path)
        return self._playback_path

    def _cleanup_prepared_path(self):
        self._playback_path = None
        if not self._playback_temp_dir:
            return
        try:
            shutil.rmtree(self._playback_temp_dir)
        except OSError:
            pass
        finally:
            self._playback_temp_dir = None

    def play(self, wav_path: str) -> bool:
        self.stop() # stop existing playback

        if not wav_path or not os.path.exists(wav_path):
            return False
        try:
            playback_path = self._prepare_playback_path(wav_path)
        except OSError:
            return False

        # Load file
        cmd_open = f'open "{playback_path}" type waveaudio alias {self._alias}'
        if self.mciSendString(cmd_open, None, 0, 0) != 0:
            self._cleanup_prepared_path()
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
        self._cleanup_prepared_path()

    def _on_timer(self, event):
        pos_str = self._mci_command(f'status {self._alias} position')
        mode_str = self._mci_command(f'status {self._alias} mode')
        
        if pos_str.isdigit():
            pos_sec = float(pos_str) / 1000.0
            self.update_callback(pos_sec)

        if mode_str == "stopped":
            self.stop()
            self.finished_callback()
