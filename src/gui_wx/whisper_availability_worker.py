from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

import wx

from src.core.whisper_model_store import ModelAvailability, WhisperModelStore


@dataclass(frozen=True)
class WhisperAvailabilityScanResult:
    """Result delivered from the B3 local-only availability scan."""

    job_id: int
    scan_generation: int
    availability: tuple[ModelAvailability, ...] = ()
    failure_code: str | None = None
    failure_detail: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.failure_code is None


class WhisperAvailabilityWorker(threading.Thread):
    """Run only WhisperModelStore.scan_all() away from the wx UI thread."""

    def __init__(
        self,
        *,
        job_id: int,
        scan_generation: int,
        store: WhisperModelStore,
        result_callback: Callable[[WhisperAvailabilityScanResult], None],
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        super().__init__(name=f"whisper-availability-{job_id}", daemon=True)
        self.job_id = job_id
        self.scan_generation = scan_generation
        self.store = store
        self.result_callback = result_callback
        self.call_after = call_after

    def run(self) -> None:
        try:
            availability = tuple(self.store.scan_all())
        except Exception as error:
            result = WhisperAvailabilityScanResult(
                job_id=self.job_id,
                scan_generation=self.scan_generation,
                failure_code="availability_scan_failed",
                failure_detail=_summarize_exception(error),
            )
        else:
            result = WhisperAvailabilityScanResult(
                job_id=self.job_id,
                scan_generation=self.scan_generation,
                availability=availability,
            )
        self.call_after(self.result_callback, result)


def _summarize_exception(error: BaseException) -> str:
    message = str(error).strip()
    if message:
        return f"{error.__class__.__name__}: {message}"
    return error.__class__.__name__


__all__ = [
    "WhisperAvailabilityScanResult",
    "WhisperAvailabilityWorker",
]
