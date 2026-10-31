from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

import wx

from src.core.final_output_gate import (
    SharedSaveGateResult,
    VerifiedVmdSaveRequest,
    evaluate_shared_save_gate,
)
from src.core.verified_vmd_save import (
    VerifiedVmdCancelToken,
    VerifiedVmdSaveTerminalResult,
    run_verified_vmd_save,
)
from src.gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus


@dataclass(frozen=True, slots=True)
class VerifiedVmdSaveGateInputs:
    """GUI-captured immutable values used for the worker-side final save gate."""

    current_lifecycle_signature: tuple[object, ...] | None
    confirmed_warning_fingerprint: str | None
    application_busy: bool
    analysis_pending: bool
    expected_transition_input_digest: str | None
    expected_application_binding_digest: str | None
    expected_cleanup_input_digest: str | None
    expected_cleanup_application_binding_digest: str | None

    def evaluate(self, request: VerifiedVmdSaveRequest) -> SharedSaveGateResult:
        return evaluate_shared_save_gate(
            context=request.context,
            diagnostics_snapshot=request.diagnostics_snapshot,
            current_lifecycle_signature=self.current_lifecycle_signature,
            confirmed_warning_fingerprint=self.confirmed_warning_fingerprint,
            application_busy=self.application_busy,
            analysis_pending=self.analysis_pending,
            expected_transition_input_digest=self.expected_transition_input_digest,
            expected_application_binding_digest=self.expected_application_binding_digest,
            expected_cleanup_input_digest=self.expected_cleanup_input_digest,
            expected_cleanup_application_binding_digest=(
                self.expected_cleanup_application_binding_digest
            ),
        )


class _CompletionGate:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._claimed = False

    def claim(self) -> bool:
        with self._lock:
            if self._claimed:
                return False
            self._claimed = True
            return True


class VerifiedVmdSaveWorker(threading.Thread):
    """Own the complete B4 individual VMD save transaction outside the UI thread."""

    def __init__(
        self,
        *,
        request: VerifiedVmdSaveRequest,
        pre_commit_guard: Callable[[VerifiedVmdSaveRequest, VerifiedVmdCancelToken], str],
        terminal_callback: Callable[
            [int, AudioWorkerKind, int, VerifiedVmdSaveTerminalResult], None
        ],
        error_callback: Callable[[int, AudioWorkerKind, int, Exception], None],
        gate_inputs: VerifiedVmdSaveGateInputs | None = None,
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        super().__init__(name=f"verified-vmd-save-{request.job_id}", daemon=True)
        self.request = request
        self.audio_job_id = request.job_id
        self.kind = AudioWorkerKind.VERIFIED_VMD_SAVE
        self.ticket = request.ticket
        self.pre_commit_guard = pre_commit_guard
        self.gate_inputs = gate_inputs
        self.terminal_callback = terminal_callback
        self.error_callback = error_callback
        self.call_after = call_after
        self.cancel_token = VerifiedVmdCancelToken()
        self.state = AudioWorkerState(
            audio_job_id=request.job_id,
            kind=self.kind,
            status=AudioWorkerStatus.RUNNING,
        )
        self._completion_gate = _CompletionGate()

    def cancel(self) -> bool:
        accepted = self.cancel_token.request_cancel()
        self.state.status = (
            AudioWorkerStatus.CANCELLING
            if accepted
            else AudioWorkerStatus.FINALIZING
        )
        return accepted

    def _emit_terminal(self, result: VerifiedVmdSaveTerminalResult) -> None:
        if self._completion_gate.claim():
            self.call_after(
                self.terminal_callback,
                self.audio_job_id,
                self.kind,
                self.ticket,
                result,
            )

    def _emit_error(self, error: Exception) -> None:
        if self._completion_gate.claim():
            self.call_after(
                self.error_callback,
                self.audio_job_id,
                self.kind,
                self.ticket,
                error,
            )

    def run(self) -> None:
        try:
            if self.gate_inputs is not None and not self.cancel_token.cancel_requested:
                self.cancel_token.set_phase("validating")
                try:
                    gate = self.gate_inputs.evaluate(self.request)
                except Exception:
                    gate = None
                if (
                    gate is None
                    or gate.status != "ready"
                    or gate.fingerprint != self.request.fingerprint
                ):
                    error_code = "shared_final_output_stale"
                    if (
                        gate is not None
                        and gate.status == "blocked"
                        and gate.blocking_codes
                    ):
                        error_code = gate.blocking_codes[0]
                    self._emit_terminal(
                        VerifiedVmdSaveTerminalResult(
                            job_id=self.request.job_id,
                            status="failed",
                            error_code=error_code,
                            committed=False,
                            final_path=None,
                            temporary_path=None,
                            commit_phase="gate_validation",
                            evidence=None,
                        )
                    )
                    return
            result = run_verified_vmd_save(
                self.request,
                self.cancel_token,
                self.pre_commit_guard,
            )
        except Exception as error:
            self._emit_error(error)
            return
        self._emit_terminal(result)


__all__ = ["VerifiedVmdSaveGateInputs", "VerifiedVmdSaveWorker"]
