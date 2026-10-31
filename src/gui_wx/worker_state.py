from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any


PROCESS_TERMINATE_GRACE_SEC = 2.0
LONG_AUDIO_CONFIRMATION_THRESHOLD_SEC = 300.0


class AudioWorkerKind(str, Enum):
    PROBE = "probe"
    ANALYSIS_WAV = "analysis_wav"
    MMD_WAV = "mmd_wav"
    VERIFIED_VMD_SAVE = "verified_vmd_save"
    DELIVERY_PACKAGE = "delivery_package"


class AudioWorkerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    CANCELLING = "cancelling"
    FINALIZING = "finalizing"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCARDED = "discarded"


@dataclass
class AudioWorkerState:
    audio_job_id: int
    kind: AudioWorkerKind
    status: AudioWorkerStatus
    message: str = ""

    @property
    def is_active(self) -> bool:
        return self.status in {
            AudioWorkerStatus.RUNNING,
            AudioWorkerStatus.CANCELLING,
            AudioWorkerStatus.FINALIZING,
        }


class CancelToken:
    def __init__(self, grace_sec: float = PROCESS_TERMINATE_GRACE_SEC):
        self._grace_sec = grace_sec
        self._cancel_requested = False
        self._process: Any = None
        self._lock = threading.Lock()

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    def register_process(self, process: Any) -> None:
        should_cancel = False
        with self._lock:
            self._process = process
            should_cancel = self._cancel_requested
        if should_cancel:
            self._terminate_process_async(process)

    def clear_process(self, process: Any) -> None:
        with self._lock:
            if self._process is process:
                self._process = None

    def request_cancel(self) -> None:
        process = None
        with self._lock:
            self._cancel_requested = True
            process = self._process
        if process is not None:
            self._terminate_process_async(process)

    def _terminate_process_async(self, process: Any) -> None:
        thread = threading.Thread(
            target=terminate_then_kill,
            args=(process, self._grace_sec),
            daemon=True,
        )
        thread.start()


def terminate_then_kill(process: Any, grace_sec: float = PROCESS_TERMINATE_GRACE_SEC) -> None:
    try:
        if process.poll() is None:
            process.terminate()
    except Exception:
        return

    try:
        process.wait(timeout=grace_sec)
        return
    except Exception:
        pass

    try:
        if process.poll() is None:
            process.kill()
    except Exception:
        pass
