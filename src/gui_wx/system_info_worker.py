from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import wx

from src.core.system_info import (
    SYSTEM_INFO_UNAVAILABLE,
    SystemInfoSnapshot,
    collect_system_info,
    unavailable_snapshot,
)


WorkerState = Literal["pending", "running", "completed", "failed", "cancelled"]


@dataclass(frozen=True)
class SystemInfoWorkerResult:
    job_id: int
    state: Literal["completed", "failed"]
    snapshot: SystemInfoSnapshot
    reason: str | None = None


class SystemInfoWorker(threading.Thread):
    """Collect About information without blocking the wx UI thread."""

    def __init__(
        self,
        *,
        job_id: int,
        collector: Callable[[], SystemInfoSnapshot] = collect_system_info,
        success_callback: Callable[[SystemInfoWorkerResult], None],
        failure_callback: Callable[[SystemInfoWorkerResult], None],
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        super().__init__(name=f"system-info-{job_id}", daemon=True)
        self.job_id = job_id
        self.collector = collector
        self.success_callback = success_callback
        self.failure_callback = failure_callback
        self.call_after = call_after
        self._state: WorkerState = "pending"
        self._lock = threading.Lock()

    @property
    def state(self) -> WorkerState:
        with self._lock:
            return self._state

    def cancel(self, job_id: int | None = None) -> bool:
        with self._lock:
            if job_id is not None and job_id != self.job_id:
                return False
            if self._state not in {"pending", "running"}:
                return False
            self._state = "cancelled"
            return True

    def run(self) -> None:
        with self._lock:
            if self._state == "cancelled":
                return
            self._state = "running"

        try:
            snapshot = self.collector()
        except Exception:
            result = SystemInfoWorkerResult(
                job_id=self.job_id,
                state="failed",
                snapshot=unavailable_snapshot(),
                reason=SYSTEM_INFO_UNAVAILABLE,
            )
            callback = self.failure_callback
        else:
            result = SystemInfoWorkerResult(
                job_id=self.job_id,
                state="completed",
                snapshot=snapshot,
            )
            callback = self.success_callback

        with self._lock:
            if self._state == "cancelled":
                return
            self._state = result.state
        try:
            self.call_after(callback, result)
        except RuntimeError:
            # The wx application may already be shutting down.
            return


__all__ = ["SystemInfoWorker", "SystemInfoWorkerResult", "WorkerState"]
