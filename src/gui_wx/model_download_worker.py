from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Protocol

import wx

from src.core.whisper_model_downloader import (
    DownloadProgress,
    DownloadResult,
    download_model,
)
from src.core.whisper_model_store import (
    DeleteResult,
    OwnershipReleasePermit,
    StoragePreflight,
    WhisperModelStore,
)
from src.core.whisper_models import WhisperModelCatalog


MODEL_MANAGEMENT_OPERATION_DOWNLOAD = "download"
MODEL_MANAGEMENT_OPERATION_DELETE = "delete"
MODEL_MANAGEMENT_STATUS_SUCCEEDED = "succeeded"
MODEL_MANAGEMENT_STATUS_CANCELLED = "cancelled"
MODEL_MANAGEMENT_STATUS_FAILED = "failed"
MODEL_MANAGEMENT_STATUS_BLOCKED = "blocked"


class OwnershipPermitProvider(Protocol):
    def __call__(self, model_key: str) -> OwnershipReleasePermit | None:
        ...


@dataclass(frozen=True)
class ModelManagementProgress:
    job_id: int
    operation: str
    model_key: str
    phase: str
    received_bytes: int = 0
    expected_bytes: int = 0


@dataclass(frozen=True)
class ModelManagementResult:
    job_id: int
    operation: str
    model_key: str
    status: str
    failure_code: str | None = None
    failure_detail: str = ""
    cleanup_status: str | None = None
    download_result: DownloadResult | None = None
    delete_result: DeleteResult | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == MODEL_MANAGEMENT_STATUS_SUCCEEDED


class WhisperModelManagementWorker(threading.Thread):
    """Run one download or ownership-gated delete outside the wx UI thread."""

    def __init__(
        self,
        *,
        job_id: int,
        operation: str,
        model_key: str,
        catalog: WhisperModelCatalog,
        store: WhisperModelStore,
        preflight: StoragePreflight | None = None,
        cancel_event: threading.Event | None = None,
        result_callback: Callable[[ModelManagementResult], None],
        progress_callback: Callable[[ModelManagementProgress], None] | None = None,
        ownership_provider: OwnershipPermitProvider | None = None,
        transport=None,
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        super().__init__(name=f"whisper-model-{operation}-{job_id}", daemon=True)
        if operation not in {
            MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
            MODEL_MANAGEMENT_OPERATION_DELETE,
        }:
            raise ValueError("unsupported model management operation")
        self.job_id = job_id
        self.operation = operation
        self.model_key = model_key
        self.catalog = catalog
        self.store = store
        self.preflight = preflight
        self.cancel_event = cancel_event or threading.Event()
        self.result_callback = result_callback
        self.progress_callback = progress_callback
        self.ownership_provider = ownership_provider
        self.transport = transport
        self.call_after = call_after

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        if self.operation == MODEL_MANAGEMENT_OPERATION_DOWNLOAD:
            self._run_download()
        else:
            self._run_delete()

    def _run_download(self) -> None:
        if self.preflight is None:
            self._deliver_result(
                ModelManagementResult(
                    job_id=self.job_id,
                    operation=self.operation,
                    model_key=self.model_key,
                    status=MODEL_MANAGEMENT_STATUS_FAILED,
                    failure_code="storage_preflight_failed",
                    failure_detail="Download preflight is missing.",
                )
            )
            return
        try:
            result = download_model(
                self.model_key,
                catalog=self.catalog,
                store=self.store,
                preflight=self.preflight,
                cancel_event=self.cancel_event,
                progress_callback=self._on_download_progress,
                transport=self.transport,
            )
        except Exception as error:
            self._deliver_result(
                ModelManagementResult(
                    job_id=self.job_id,
                    operation=self.operation,
                    model_key=self.model_key,
                    status=MODEL_MANAGEMENT_STATUS_FAILED,
                    failure_code="download_worker_failed",
                    failure_detail=_summarize_exception(error),
                )
            )
            return
        self._deliver_result(_download_management_result(self.job_id, result))

    def _run_delete(self) -> None:
        if self.cancel_event.is_set():
            self._deliver_result(
                _cancelled_result(self.job_id, self.operation, self.model_key)
            )
            return
        if self.ownership_provider is None:
            self._deliver_result(
                ModelManagementResult(
                    job_id=self.job_id,
                    operation=self.operation,
                    model_key=self.model_key,
                    status=MODEL_MANAGEMENT_STATUS_BLOCKED,
                    failure_code="delete_blocked_ownership",
                    failure_detail="Ownership release provider is not configured.",
                )
            )
            return
        try:
            permit = self.ownership_provider(self.model_key)
        except Exception as error:
            self._deliver_result(
                ModelManagementResult(
                    job_id=self.job_id,
                    operation=self.operation,
                    model_key=self.model_key,
                    status=MODEL_MANAGEMENT_STATUS_FAILED,
                    failure_code="delete_ownership_provider_failed",
                    failure_detail=_summarize_exception(error),
                )
            )
            return
        if not isinstance(permit, OwnershipReleasePermit):
            self._deliver_result(
                ModelManagementResult(
                    job_id=self.job_id,
                    operation=self.operation,
                    model_key=self.model_key,
                    status=MODEL_MANAGEMENT_STATUS_BLOCKED,
                    failure_code="delete_blocked_ownership",
                    failure_detail="Ownership release provider did not issue a permit.",
                )
            )
            return
        try:
            result = self.store.delete_model(self.model_key, permit)
        except Exception as error:
            self._deliver_result(
                ModelManagementResult(
                    job_id=self.job_id,
                    operation=self.operation,
                    model_key=self.model_key,
                    status=MODEL_MANAGEMENT_STATUS_FAILED,
                    failure_code="delete_failed",
                    failure_detail=_summarize_exception(error),
                )
            )
            return
        self._deliver_result(_delete_management_result(self.job_id, self.model_key, result))

    def _on_download_progress(self, progress: DownloadProgress) -> None:
        if self.progress_callback is None:
            return
        self.call_after(
            self.progress_callback,
            ModelManagementProgress(
                job_id=self.job_id,
                operation=self.operation,
                model_key=progress.model_key,
                phase=progress.phase,
                received_bytes=progress.received_bytes,
                expected_bytes=progress.expected_bytes,
            ),
        )

    def _deliver_result(self, result: ModelManagementResult) -> None:
        self.call_after(self.result_callback, result)


def _download_management_result(job_id: int, result: DownloadResult) -> ModelManagementResult:
    status = {
        "succeeded": MODEL_MANAGEMENT_STATUS_SUCCEEDED,
        "cancelled": MODEL_MANAGEMENT_STATUS_CANCELLED,
        "failed": MODEL_MANAGEMENT_STATUS_FAILED,
    }.get(result.status, MODEL_MANAGEMENT_STATUS_FAILED)
    return ModelManagementResult(
        job_id=job_id,
        operation=MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
        model_key=result.model_key,
        status=status,
        failure_code=result.failure_code,
        failure_detail=result.failure_detail,
        cleanup_status=result.cleanup_status,
        download_result=result,
    )


def _delete_management_result(
    job_id: int,
    model_key: str,
    result: DeleteResult,
) -> ModelManagementResult:
    status = (
        MODEL_MANAGEMENT_STATUS_SUCCEEDED
        if result.succeeded
        else MODEL_MANAGEMENT_STATUS_BLOCKED
        if result.status == "blocked"
        else MODEL_MANAGEMENT_STATUS_FAILED
    )
    return ModelManagementResult(
        job_id=job_id,
        operation=MODEL_MANAGEMENT_OPERATION_DELETE,
        model_key=model_key,
        status=status,
        failure_code=result.failure_code,
        failure_detail=result.message,
        delete_result=result,
    )


def _cancelled_result(job_id: int, operation: str, model_key: str) -> ModelManagementResult:
    return ModelManagementResult(
        job_id=job_id,
        operation=operation,
        model_key=model_key,
        status=MODEL_MANAGEMENT_STATUS_CANCELLED,
        failure_detail="Model management was cancelled.",
    )


def _summarize_exception(error: BaseException) -> str:
    message = str(error).strip()
    if message:
        return f"{error.__class__.__name__}: {message}"
    return error.__class__.__name__


__all__ = [
    "MODEL_MANAGEMENT_OPERATION_DELETE",
    "MODEL_MANAGEMENT_OPERATION_DOWNLOAD",
    "MODEL_MANAGEMENT_STATUS_BLOCKED",
    "MODEL_MANAGEMENT_STATUS_CANCELLED",
    "MODEL_MANAGEMENT_STATUS_FAILED",
    "MODEL_MANAGEMENT_STATUS_SUCCEEDED",
    "ModelManagementProgress",
    "ModelManagementResult",
    "WhisperModelManagementWorker",
]
