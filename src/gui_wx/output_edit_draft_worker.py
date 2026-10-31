from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any, Callable

import wx


@dataclass(frozen=True, slots=True)
class OutputEditDraftProjectionRequest:
    ticket: int
    source_revision: int
    draft_revision: int
    base_plan_identity_digest: str
    purpose: str
    compute: Callable[[], Any]
    payload: object | None = None

    def __post_init__(self) -> None:
        if isinstance(self.ticket, bool) or not isinstance(self.ticket, int) or self.ticket < 1:
            raise ValueError("ticket must be a positive integer")
        if isinstance(self.source_revision, bool) or not isinstance(self.source_revision, int) or self.source_revision < 0:
            raise ValueError("source_revision must be a non-negative integer")
        if isinstance(self.draft_revision, bool) or not isinstance(self.draft_revision, int) or self.draft_revision < 0:
            raise ValueError("draft_revision must be a non-negative integer")
        if not isinstance(self.base_plan_identity_digest, str) or not self.base_plan_identity_digest:
            raise ValueError("base_plan_identity_digest must be non-empty")
        if not isinstance(self.purpose, str) or not self.purpose:
            raise ValueError("purpose must be non-empty")
        if not callable(self.compute):
            raise ValueError("compute must be callable")


@dataclass(frozen=True, slots=True)
class OutputEditDraftProjectionResult:
    request: OutputEditDraftProjectionRequest
    value: Any = None
    error: Exception | None = None


class OutputEditDraftProjectionCoordinator:
    """Serialize draft shape calculations and keep only the newest waiting request."""

    def __init__(
        self,
        result_callback: Callable[
            [OutputEditDraftProjectionRequest, OutputEditDraftProjectionResult], None
        ],
        *,
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        if not callable(result_callback):
            raise TypeError("result_callback must be callable")
        if not callable(call_after):
            raise TypeError("call_after must be callable")
        self._result_callback = result_callback
        self._call_after = call_after
        self._lock = threading.Lock()
        self._active_request: OutputEditDraftProjectionRequest | None = None
        self._latest_request: OutputEditDraftProjectionRequest | None = None
        self._closed = False

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active_request is not None

    def request(self, request: OutputEditDraftProjectionRequest) -> bool:
        if not isinstance(request, OutputEditDraftProjectionRequest):
            raise TypeError("request must be OutputEditDraftProjectionRequest")
        start_now = False
        with self._lock:
            if self._closed:
                return False
            self._latest_request = request
            if self._active_request is None:
                self._active_request = request
                self._latest_request = None
                start_now = True
        if start_now:
            self._start_worker(request)
        return True

    def _start_worker(self, request: OutputEditDraftProjectionRequest) -> None:
        worker = threading.Thread(
            target=self._run_worker,
            args=(request,),
            name=f"output-edit-draft-{request.ticket}",
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError as error:
            self._deliver_result(
                request,
                OutputEditDraftProjectionResult(request, error=error),
            )

    def _run_worker(self, request: OutputEditDraftProjectionRequest) -> None:
        try:
            result = OutputEditDraftProjectionResult(
                request,
                value=request.compute(),
            )
        except Exception as error:
            result = OutputEditDraftProjectionResult(request, error=error)
        try:
            self._call_after(self._deliver_result, request, result)
        except Exception:
            with self._lock:
                self._closed = True
                self._active_request = None
                self._latest_request = None

    def _deliver_result(
        self,
        request: OutputEditDraftProjectionRequest,
        result: OutputEditDraftProjectionResult,
    ) -> None:
        with self._lock:
            if self._closed or self._active_request != request:
                return
        next_request: OutputEditDraftProjectionRequest | None = None
        callback_error: Exception | None = None
        try:
            self._result_callback(request, result)
        except Exception as error:
            callback_error = error
        finally:
            with self._lock:
                if self._closed:
                    self._active_request = None
                    self._latest_request = None
                else:
                    next_request = self._latest_request
                    self._latest_request = None
                    self._active_request = next_request
        if next_request is not None:
            self._start_worker(next_request)
        if callback_error is not None:
            raise callback_error

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._latest_request = None


__all__ = [
    "OutputEditDraftProjectionCoordinator",
    "OutputEditDraftProjectionRequest",
    "OutputEditDraftProjectionResult",
]
