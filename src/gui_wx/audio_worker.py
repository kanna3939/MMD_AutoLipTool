from __future__ import annotations

import threading
from typing import Callable, Any

import wx

from src.core.delivery_package import DeliveryCancelToken, DeliveryTerminalResult
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus, CancelToken


class _DeliveryCompletionGate:
    def __init__(self) -> None:
        self._claimed = False
        self._lock = threading.Lock()

    def claim(self) -> bool:
        with self._lock:
            if self._claimed:
                return False
            self._claimed = True
            return True


class AudioWorker(threading.Thread):
    def __init__(
        self,
        *,
        audio_job_id: int,
        kind: AudioWorkerKind,
        task: Callable[[CancelToken], Any],
        success_callback: Callable[[int, AudioWorkerKind, Any], None],
        error_callback: Callable[[int, AudioWorkerKind, Exception], None],
        cancelled_callback: Callable[[int, AudioWorkerKind], None],
        call_after: Callable[..., None] = wx.CallAfter,
    ):
        super().__init__()
        self.daemon = True
        self.audio_job_id = audio_job_id
        self.kind = kind
        self.task = task
        self.success_callback = success_callback
        self.error_callback = error_callback
        self.cancelled_callback = cancelled_callback
        self.call_after = call_after
        self.cancel_token = CancelToken()
        self.state = AudioWorkerState(
            audio_job_id=audio_job_id,
            kind=kind,
            status=AudioWorkerStatus.RUNNING,
        )

    def cancel(self) -> None:
        self.state.status = AudioWorkerStatus.CANCELLING
        self.cancel_token.request_cancel()

    def run(self) -> None:
        if self.cancel_token.cancel_requested:
            self.call_after(self.cancelled_callback, self.audio_job_id, self.kind)
            return

        try:
            result = self.task(self.cancel_token)
        except Exception as error:
            if self.cancel_token.cancel_requested:
                self.call_after(self.cancelled_callback, self.audio_job_id, self.kind)
            else:
                self.call_after(self.error_callback, self.audio_job_id, self.kind, error)
            return

        if self.cancel_token.cancel_requested:
            self.call_after(self.cancelled_callback, self.audio_job_id, self.kind)
            return

        self.call_after(self.success_callback, self.audio_job_id, self.kind, result)


class DeliveryPackageWorker(threading.Thread):
    """Run the transactional delivery orchestration outside the UI thread."""

    def __init__(
        self,
        *,
        audio_job_id: int,
        projection_generation: int,
        task: Callable[[DeliveryCancelToken], DeliveryTerminalResult],
        terminal_callback: Callable[
            [int, AudioWorkerKind, int, DeliveryTerminalResult], None
        ],
        error_callback: Callable[[int, AudioWorkerKind, int, Exception], None],
        call_after: Callable[..., None] = wx.CallAfter,
    ):
        super().__init__()
        self.daemon = True
        self.audio_job_id = audio_job_id
        self.kind = AudioWorkerKind.DELIVERY_PACKAGE
        self.projection_generation = projection_generation
        self.task = task
        self.terminal_callback = terminal_callback
        self.error_callback = error_callback
        self.call_after = call_after
        self.cancel_token = DeliveryCancelToken()
        self.state = AudioWorkerState(
            audio_job_id=audio_job_id,
            kind=self.kind,
            status=AudioWorkerStatus.RUNNING,
        )
        self._completion_gate = _DeliveryCompletionGate()

    def cancel(self) -> bool:
        accepted = self.cancel_token.request_cancel()
        if accepted:
            self.state.status = AudioWorkerStatus.CANCELLING
        else:
            self.state.status = AudioWorkerStatus.FINALIZING
        return accepted

    def _emit_terminal(self, result: DeliveryTerminalResult) -> None:
        if not self._completion_gate.claim():
            return
        self.call_after(
            self.terminal_callback,
            self.audio_job_id,
            self.kind,
            self.projection_generation,
            result,
        )

    def _emit_error(self, error: Exception) -> None:
        if not self._completion_gate.claim():
            return
        self.call_after(
            self.error_callback,
            self.audio_job_id,
            self.kind,
            self.projection_generation,
            error,
        )

    def _unexpected_terminal(self, _error: Exception) -> DeliveryTerminalResult:
        phase = self.cancel_token.phase
        commit_phase = (
            "awaiting_commit_guard"
            if phase == "awaiting_commit_guard"
            else "commit_started"
            if phase == "commit_started"
            else "commit_failed"
            if phase == "commit_failed"
            else "before_commit"
        )
        return DeliveryTerminalResult(
            job_id=self.audio_job_id,
            primary_status="failed",
            primary_error_code="delivery_worker_failed",
            committed=False,
            final_path=None,
            staging_path=None,
            cleanup_status="not_required",
            commit_phase=commit_phase,
            artifact_phase=None,
        )

    def run(self) -> None:
        try:
            result = self.task(self.cancel_token)
        except Exception as error:
            if self.cancel_token.phase == "created":
                self._emit_error(error)
            else:
                self._emit_terminal(self._unexpected_terminal(error))
            return

        if not isinstance(result, DeliveryTerminalResult):
            self._emit_error(TypeError("delivery task returned an invalid terminal result"))
            return
        self._emit_terminal(result)
