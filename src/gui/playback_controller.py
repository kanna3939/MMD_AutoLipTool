from __future__ import annotations

from pathlib import Path
import math

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class PlaybackController(QObject):
    """Minimal playback core for MS8C phase 1.

    Responsibilities:
    - keep playback state
    - control WAV playback start/stop
    - expose second-based playback position
    - reset position to 0.0 sec on start and on normal end
    """

    source_path_changed = Signal(str)
    playback_active_changed = Signal(bool)
    playback_started = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()
    position_sec_changed = Signal(float)
    playback_error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._audio_output = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio_output)

        self._source_path: Path | None = None
        self._is_ready = False
        self._is_playing = False
        self._position_sec = 0.0

        self._player.positionChanged.connect(self._on_position_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.errorOccurred.connect(self._on_error_occurred)

    def set_wav_path(self, wav_path: str | Path | None) -> bool:
        """Set playback source path.

        Returns True when a playable WAV source is accepted.
        """
        if wav_path is None:
            self.clear_source()
            return False

        normalized = str(wav_path).strip()
        if not normalized:
            self.clear_source()
            return False

        path = Path(normalized)
        if path.suffix.lower() != ".wav":
            self.playback_error.emit("WAV file is required for playback.")
            return False
        if not path.exists() or not path.is_file():
            self.playback_error.emit(f"WAV file not found: {path}")
            return False

        self.stop_playback()
        self._source_path = path
        self._is_ready = True
        self._player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.reset_position()
        self.source_path_changed.emit(str(path))
        return True

    def clear_source(self) -> None:
        self.stop_playback()
        self._source_path = None
        self._is_ready = False
        self._player.setSource(QUrl())
        self.reset_position()
        self.source_path_changed.emit("")

    def can_start_playback(self) -> bool:
        return self._is_ready and self._source_path is not None

    def start_playback(self) -> bool:
        """Start playback from 0.0 sec (frame 0 equivalent)."""
        if not self.can_start_playback():
            return False
        self.reset_position()
        self._player.play()
        return True

    def stop_playback(self) -> None:
        self._player.stop()
        self.reset_position()

    def reset_position(self) -> None:
        self._player.setPosition(0)
        self._set_position_sec(0.0)

    def is_playing(self) -> bool:
        return self._is_playing

    def is_ready(self) -> bool:
        return self._is_ready

    def current_position_sec(self) -> float:
        return self._position_sec

    def source_path(self) -> Path | None:
        return self._source_path

    def _on_position_changed(self, position_ms: int) -> None:
        seconds = max(float(position_ms) / 1000.0, 0.0)
        self._set_position_sec(seconds)

    def _on_playback_state_changed(self, playback_state: QMediaPlayer.PlaybackState) -> None:
        is_playing = playback_state == QMediaPlayer.PlaybackState.PlayingState
        if is_playing == self._is_playing:
            return

        self._is_playing = is_playing
        self.playback_active_changed.emit(self._is_playing)
        if self._is_playing:
            self.playback_started.emit()
            return
        self.playback_stopped.emit()

    def _on_media_status_changed(self, media_status: QMediaPlayer.MediaStatus) -> None:
        if media_status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        self.playback_finished.emit()
        self.stop_playback()

    def _on_error_occurred(self, _error: QMediaPlayer.Error, _message: str) -> None:
        message = self._player.errorString().strip() or "Playback error."
        self.playback_error.emit(message)

    def _set_position_sec(self, seconds: float) -> None:
        resolved = max(float(seconds), 0.0)
        if math.isclose(resolved, self._position_sec, rel_tol=0.0, abs_tol=1e-6):
            return
        self._position_sec = resolved
        self.position_sec_changed.emit(self._position_sec)


__all__ = ["PlaybackController"]
