from __future__ import annotations

import math

from PySide6.QtCore import QObject, Signal


class ViewSync(QObject):
    """Minimal second-based position sync hub for MS8C phase 1."""

    shared_position_sec_changed = Signal(float)
    shared_position_reset = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._shared_position_sec = 0.0

    def update_shared_position_sec(self, position_sec: float) -> None:
        resolved = max(float(position_sec), 0.0)
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


__all__ = ["ViewSync"]
