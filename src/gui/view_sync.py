from __future__ import annotations

import math

from PySide6.QtCore import QObject, Signal


class ViewSync(QObject):
    """Second-based shared state hub.

    MS8C:
    - shared playback position sync
    MS8D-2 phase 1:
    - shared viewport range sync (start/end seconds)
    """

    shared_position_sec_changed = Signal(float)
    shared_position_reset = Signal()
    shared_viewport_sec_changed = Signal(float, float)
    shared_viewport_reset = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._shared_position_sec = 0.0
        self._shared_viewport_start_sec = 0.0
        self._shared_viewport_end_sec = 0.0

    def update_shared_position_sec(self, position_sec: float) -> None:
        resolved = self._normalize_non_negative_sec(position_sec)
        if math.isclose(resolved, self._shared_position_sec, rel_tol=0.0, abs_tol=1e-6):
            return
        self._shared_position_sec = resolved
        self.shared_position_sec_changed.emit(self._shared_position_sec)

    def reset_shared_position(self) -> None:
        was_non_zero = not math.isclose(
            self._shared_position_sec, 0.0, rel_tol=0.0, abs_tol=1e-6
        )
        self._shared_position_sec = 0.0
        if was_non_zero:
            self.shared_position_sec_changed.emit(0.0)
        self.shared_position_reset.emit()

    def shared_position_sec(self) -> float:
        return self._shared_position_sec

    def update_shared_viewport_sec(self, start_sec: float, end_sec: float) -> None:
        normalized_start, normalized_end = self._normalize_viewport_sec(start_sec, end_sec)
        if self._is_same_viewport(normalized_start, normalized_end):
            return
        self._shared_viewport_start_sec = normalized_start
        self._shared_viewport_end_sec = normalized_end
        self.shared_viewport_sec_changed.emit(
            self._shared_viewport_start_sec,
            self._shared_viewport_end_sec,
        )

    def reset_shared_viewport(self) -> None:
        was_non_zero = not self._is_same_viewport(0.0, 0.0)
        self._shared_viewport_start_sec = 0.0
        self._shared_viewport_end_sec = 0.0
        if was_non_zero:
            self.shared_viewport_sec_changed.emit(0.0, 0.0)
        self.shared_viewport_reset.emit()

    def shared_viewport_sec(self) -> tuple[float, float]:
        return (self._shared_viewport_start_sec, self._shared_viewport_end_sec)

    def _normalize_non_negative_sec(self, value: float) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(resolved):
            return 0.0
        return max(resolved, 0.0)

    def _normalize_viewport_sec(self, start_sec: float, end_sec: float) -> tuple[float, float]:
        normalized_start = self._normalize_non_negative_sec(start_sec)
        normalized_end = self._normalize_non_negative_sec(end_sec)
        if normalized_end < normalized_start:
            normalized_start, normalized_end = normalized_end, normalized_start
        return (normalized_start, normalized_end)

    def _is_same_viewport(self, start_sec: float, end_sec: float) -> bool:
        return math.isclose(
            start_sec, self._shared_viewport_start_sec, rel_tol=0.0, abs_tol=1e-6
        ) and math.isclose(end_sec, self._shared_viewport_end_sec, rel_tol=0.0, abs_tol=1e-6)


__all__ = ["ViewSync"]
