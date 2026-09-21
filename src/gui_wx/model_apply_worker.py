from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

import wx

from src.core.whisper_model_runtime import (
    VerifiedAnalysisModelRequest,
    WhisperModelCandidate,
    WhisperModelRuntime,
)


MODEL_APPLY_STATUS_READY = "ready"
MODEL_APPLY_STATUS_CANCELLED = "cancelled"
MODEL_APPLY_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class WhisperModelApplyResult:
    job_id: int
    model_key: str
    status: str
    candidate: WhisperModelCandidate | None = None
    failure_code: str | None = None
    failure_detail: str = ""


class WhisperModelApplyWorker(threading.Thread):
    """Prepare one verified candidate without blocking the wx UI thread."""

    def __init__(
        self,
        *,
        job_id: int,
        request: VerifiedAnalysisModelRequest,
        runtime: WhisperModelRuntime,
        result_callback: Callable[[WhisperModelApplyResult], None],
        cancel_event: threading.Event | None = None,
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        super().__init__(name=f"whisper-model-apply-{job_id}", daemon=True)
        self.job_id = job_id
        self.request = request
        self.runtime = runtime
        self.result_callback = result_callback
        self.cancel_event = cancel_event or threading.Event()
        self.call_after = call_after

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        candidate: WhisperModelCandidate | None = None
        try:
            if self.cancel_event.is_set():
                self._deliver(
                    WhisperModelApplyResult(
                        self.job_id,
                        self.request.identity.model_key,
                        MODEL_APPLY_STATUS_CANCELLED,
                    )
                )
                return
            candidate = self.runtime.prepare_candidate(self.request)
            if self.cancel_event.is_set():
                self.runtime.reject_candidate(candidate)
                self._deliver(
                    WhisperModelApplyResult(
                        self.job_id,
                        self.request.identity.model_key,
                        MODEL_APPLY_STATUS_CANCELLED,
                    )
                )
                return
            self._deliver(
                WhisperModelApplyResult(
                    self.job_id,
                    self.request.identity.model_key,
                    MODEL_APPLY_STATUS_READY,
                    candidate=candidate,
                )
            )
        except Exception as error:
            if candidate is not None:
                try:
                    self.runtime.reject_candidate(candidate)
                except Exception:
                    pass
            self._deliver(
                WhisperModelApplyResult(
                    self.job_id,
                    self.request.identity.model_key,
                    MODEL_APPLY_STATUS_FAILED,
                    failure_code=getattr(error, "code", None) or error.__class__.__name__,
                    failure_detail=str(error),
                )
            )

    def _deliver(self, result: WhisperModelApplyResult) -> None:
        self.call_after(self.result_callback, result)


__all__ = [
    "MODEL_APPLY_STATUS_CANCELLED",
    "MODEL_APPLY_STATUS_FAILED",
    "MODEL_APPLY_STATUS_READY",
    "WhisperModelApplyResult",
    "WhisperModelApplyWorker",
]
