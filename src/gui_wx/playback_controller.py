import ctypes
import math
import os
import shutil
import tempfile
from pathlib import Path

import wx


_POSITION_TIMER_MS = 33
_SCRUB_TIMER_MS = 35
_SCRUB_FRAME_MS = 66


def _mci_accepts_filename(path: str | Path) -> bool:
    path_obj = Path(path)
    suffix = path_obj.suffix
    return len(path_obj.stem) <= 8 and len(suffix) <= 4


class PlaybackController:
    """WAV playback through Windows MCI with millisecond position reporting."""

    def __init__(self, update_callback, finished_callback):
        self.update_callback = update_callback
        self.finished_callback = finished_callback

        self._timer = wx.Timer()
        self._timer.Bind(wx.EVT_TIMER, self._on_timer)
        self._scrub_timer = wx.Timer()
        self._scrub_timer.Bind(wx.EVT_TIMER, self._on_scrub_timer)
        self._alias = "mmd_autoliptool_mci"
        self._playback_temp_dir = None
        self._playback_path = None
        self._track_length_ms = None
        self._alias_open = False
        self._is_playing = False
        self._is_paused = False
        self._is_scrubbing = False
        self._scrub_failed = False
        self._pending_scrub_position_sec = None

        self.winmm = ctypes.windll.winmm
        self.mciSendString = self.winmm.mciSendStringW

    def _mci_send(self, command: str, *, with_result: bool = False):
        buf = ctypes.create_unicode_buffer(256) if with_result else None
        error_code = self.mciSendString(
            command,
            buf,
            255 if buf is not None else 0,
            0,
        )
        if with_result:
            return error_code == 0, buf.value.strip() if error_code == 0 else ""
        return error_code == 0

    def _mci_command(self, command: str) -> str:
        """Compatibility helper for status queries."""
        _succeeded, result = self._mci_send(command, with_result=True)
        return result

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

    @staticmethod
    def _position_ms(position_sec: float) -> int:
        try:
            value = float(position_sec)
        except (TypeError, ValueError, OverflowError):
            value = 0.0
        if not math.isfinite(value):
            value = 0.0
        return max(0, int(round(value * 1000.0)))

    def _open(self, wav_path: str | Path) -> bool:
        if not wav_path or not os.path.exists(wav_path):
            return False
        try:
            playback_path = self._prepare_playback_path(wav_path)
        except OSError:
            return False

        cmd_open = f'open "{playback_path}" type waveaudio alias {self._alias}'
        if not self._mci_send(cmd_open):
            self._cleanup_prepared_path()
            return False
        self._alias_open = True

        # MCI positions are device-format dependent. The UI contract uses seconds,
        # so all positions sent to and read from this alias are milliseconds.
        if not self._mci_send(f"set {self._alias} time format milliseconds"):
            self._close_alias()
            self._cleanup_prepared_path()
            return False
        length = self._mci_command(f"status {self._alias} length")
        self._track_length_ms = int(length) if length.isdigit() else None
        return True

    def _close_alias(self):
        if not self._alias_open:
            return
        self._mci_send(f"stop {self._alias}")
        self._mci_send(f"close {self._alias}")
        self._alias_open = False

    def _play_from(self, position_sec: float, *, track_position: bool) -> bool:
        if not self._alias_open:
            return False
        position_ms = self._position_ms(position_sec)
        if not self._mci_send(f"play {self._alias} from {position_ms}"):
            return False
        self._is_playing = True
        self._is_paused = False
        if track_position:
            self._timer.Start(_POSITION_TIMER_MS)
        return True

    def play(self, wav_path: str) -> bool:
        """Open a source and start it from the beginning."""
        self.stop()
        if not self._open(wav_path):
            return False
        if not self._play_from(0.0, track_position=True):
            self.stop()
            return False
        return True

    def pause(self) -> bool:
        if not self._alias_open or not self._is_playing:
            return False
        self._timer.Stop()
        if not self._mci_send(f"pause {self._alias}"):
            self._timer.Start(_POSITION_TIMER_MS)
            return False
        self._is_playing = False
        self._is_paused = True
        return True

    def resume(self, position_sec: float) -> bool:
        """Resume a paused device, or play from a position after an MCI seek."""
        if not self._alias_open:
            return False
        self._timer.Stop()
        mode = self._mci_command(f"status {self._alias} mode").lower()
        if mode == "paused":
            succeeded = self._mci_send(f"resume {self._alias}")
            if succeeded:
                self._is_playing = True
                self._is_paused = False
                self._timer.Start(_POSITION_TIMER_MS)
                return True
        elif mode == "stopped":
            if self._play_from(position_sec, track_position=True):
                return True
        return False

    def seek(self, wav_path: str, position_sec: float) -> bool:
        """Open a source and position it without starting audio output."""
        self.stop()
        if not self._open(wav_path):
            return False
        position_ms = self._position_ms(position_sec)
        if self._track_length_ms is not None:
            position_ms = min(position_ms, self._track_length_ms)
        if not self._mci_send(f"seek {self._alias} to {position_ms}"):
            self.stop()
            return False
        self._is_paused = True
        return True

    def get_position_sec(self) -> float | None:
        if not self._alias_open:
            return None
        position = self._mci_command(f"status {self._alias} position")
        if not position.isdigit():
            return None
        return int(position) / 1000.0

    def _play_scrub_frame(self, position_sec: float) -> bool:
        if not self._alias_open:
            return False
        start_ms = self._position_ms(position_sec)
        if self._track_length_ms is not None:
            frame_ms = min(_SCRUB_FRAME_MS, self._track_length_ms)
            if frame_ms <= 0:
                self._is_playing = False
                self._is_paused = False
                return True
            start_ms = min(start_ms, self._track_length_ms - frame_ms)
            end_ms = start_ms + frame_ms
        else:
            end_ms = start_ms + _SCRUB_FRAME_MS
        if not self._mci_send(
            f"play {self._alias} from {start_ms} to {end_ms}"
        ):
            return False
        self._is_playing = True
        self._is_paused = False
        self._scrub_timer.Start(_SCRUB_FRAME_MS, oneShot=True)
        return True

    def begin_scrub(self, wav_path: str, position_sec: float) -> bool:
        """Replace current playback and start audio at the first drag position."""
        self.stop()
        if not self._open(wav_path):
            return False
        self._is_scrubbing = True
        self._scrub_failed = False
        if not self._play_scrub_frame(position_sec):
            self.stop()
            return False
        return True

    def scrub_to(self, position_sec: float):
        if not self._is_scrubbing or self._scrub_failed:
            return
        self._pending_scrub_position_sec = max(0.0, float(position_sec))
        if not self._scrub_timer.IsRunning():
            self._scrub_timer.Start(_SCRUB_TIMER_MS, oneShot=True)

    def _on_scrub_timer(self, event):
        if not self._is_scrubbing or not self._alias_open or self._scrub_failed:
            self._scrub_timer.Stop()
            return

        if self._is_playing:
            mode = self._mci_command(f"status {self._alias} mode").lower()
            if mode != "stopped":
                self._scrub_timer.Start(_SCRUB_TIMER_MS, oneShot=True)
                return
            self._is_playing = False

        if self._pending_scrub_position_sec is None:
            self._scrub_timer.Stop()
            return

        position_sec = self._pending_scrub_position_sec
        self._pending_scrub_position_sec = None
        if not self._play_scrub_frame(position_sec):
            self._scrub_failed = True
            self._is_playing = False
            self._scrub_timer.Stop()
            return

    def finish_scrub(self, position_sec: float) -> bool:
        """Leave the alias open at the final position without audio output."""
        self._scrub_timer.Stop()
        self._pending_scrub_position_sec = None
        if not self._is_scrubbing or self._scrub_failed or not self._alias_open:
            self._is_scrubbing = False
            return False
        self._mci_send(f"stop {self._alias}")
        if not self._mci_send(
            f"seek {self._alias} to {self._position_ms(position_sec)}"
        ):
            self._is_scrubbing = False
            return False
        self._is_scrubbing = False
        self._is_playing = False
        self._is_paused = True
        return True

    def stop(self):
        self._timer.Stop()
        self._scrub_timer.Stop()
        self._pending_scrub_position_sec = None
        self._close_alias()
        self._cleanup_prepared_path()
        self._track_length_ms = None
        self._is_playing = False
        self._is_paused = False
        self._is_scrubbing = False
        self._scrub_failed = False

    def _on_timer(self, event):
        if not self._alias_open or not self._is_playing:
            return

        position_sec = self.get_position_sec()
        mode = self._mci_command(f"status {self._alias} mode").lower()
        if position_sec is not None:
            self.update_callback(position_sec)

        # Timer polling is paused around seek and pause operations, so a stopped
        # mode here means playback reached its natural end.
        if mode == "stopped":
            self.stop()
            self.finished_callback()
