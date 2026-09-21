from __future__ import annotations

import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol
from urllib.parse import urlsplit

from .whisper_model_loader import VerifiedWhisperCheckpoint
from .whisper_model_store import (
    StoragePreflight,
    StoreFailure,
    WhisperModelStore,
)
from .whisper_models import (
    EXPECTED_WHISPER_VERSION,
    WhisperModelCatalog,
    WhisperModelSpec,
)


DOWNLOAD_PHASE_DOWNLOADING = "downloading"
DOWNLOAD_PHASE_VERIFYING = "verifying"
DOWNLOAD_STATUS_SUCCEEDED = "succeeded"
DOWNLOAD_STATUS_CANCELLED = "cancelled"
DOWNLOAD_STATUS_FAILED = "failed"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
DEFAULT_DOWNLOAD_TIMEOUT_SEC = 30.0
_OFFICIAL_MODEL_HOST = "openaipublic.azureedge.net"
_OFFICIAL_MODEL_PATH_PREFIX = "/main/whisper/models/"


class HttpResponse(Protocol):
    status: int
    headers: Mapping[str, str]

    def read(self, amount: int) -> bytes:
        ...

    def close(self) -> None:
        ...


class HttpTransport(Protocol):
    def __call__(self, url: str, timeout: float) -> HttpResponse:
        ...


@dataclass(frozen=True)
class DownloadProgress:
    model_key: str
    phase: str
    received_bytes: int
    expected_bytes: int


@dataclass(frozen=True)
class DownloadResult:
    model_key: str
    status: str
    checkpoint: VerifiedWhisperCheckpoint | None = None
    failure_code: str | None = None
    failure_detail: str = ""
    cleanup_status: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == DOWNLOAD_STATUS_SUCCEEDED and self.checkpoint is not None


class RedirectRejectedError(RuntimeError):
    """Raised when the official model endpoint returns an HTTP redirect."""


class _RejectRedirectHandler(urllib.request.HTTPRedirectHandler):
    def _reject(self, code: int) -> None:
        raise RedirectRejectedError(f"HTTP redirect was rejected (status {code}).")

    def http_error_301(self, req, fp, code, msg, headers):
        self._reject(code)

    def http_error_302(self, req, fp, code, msg, headers):
        self._reject(code)

    def http_error_303(self, req, fp, code, msg, headers):
        self._reject(code)

    def http_error_307(self, req, fp, code, msg, headers):
        self._reject(code)

    def http_error_308(self, req, fp, code, msg, headers):
        self._reject(code)


class _UrllibResponse:
    def __init__(self, response) -> None:
        self._response = response
        self.status = int(response.getcode() or 0)
        self.headers = {
            str(key): str(value)
            for key, value in response.headers.items()
        }

    def read(self, amount: int) -> bytes:
        return self._response.read(amount)

    def close(self) -> None:
        self._response.close()


def urllib_http_transport(url: str, timeout: float) -> HttpResponse:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept-Encoding": "identity"},
    )
    opener = urllib.request.build_opener(_RejectRedirectHandler())
    return _UrllibResponse(opener.open(request, timeout=timeout))


def download_model(
    model_key: str,
    *,
    catalog: WhisperModelCatalog,
    store: WhisperModelStore,
    preflight: StoragePreflight,
    cancel_event: threading.Event | None = None,
    progress_callback: Callable[[DownloadProgress], None] | None = None,
    transport: HttpTransport | None = None,
    timeout_sec: float = DEFAULT_DOWNLOAD_TIMEOUT_SEC,
) -> DownloadResult:
    """Download one manifest artifact into B2's canonical staging path."""
    if catalog.openai_whisper_version != EXPECTED_WHISPER_VERSION:
        return _failed(
            model_key,
            "manifest_version_mismatch",
            "Whisper manifest version does not match the supported runtime version.",
        )
    try:
        spec = catalog.get(model_key)
    except Exception as error:
        return _failed(model_key, "model_key_unsupported", _safe_detail(error))

    invalid_spec = _validate_spec(spec)
    if invalid_spec is not None:
        return _failed(model_key, "manifest_invalid", invalid_spec)

    if not preflight.succeeded or preflight.model_key != model_key:
        return _failed(
            model_key,
            preflight.failure_code or "storage_preflight_failed",
            preflight.message or "Whisper model storage preflight did not succeed.",
        )
    if preflight.staging_path is None:
        return _failed(model_key, "storage_preflight_failed", "Canonical staging path is missing.")

    try:
        canonical_staging = store.staging_path(model_key)
    except Exception as error:
        return _failed(model_key, "storage_path_invalid", _safe_detail(error))
    if canonical_staging != preflight.staging_path:
        return _failed(
            model_key,
            "storage_path_invalid",
            "Preflight staging path is not the canonical B2 staging path.",
        )

    if cancel_event is not None and cancel_event.is_set():
        return _cancelled_after_cleanup(model_key, store)

    http_transport = transport or urllib_http_transport
    response: HttpResponse | None = None
    try:
        try:
            response = http_transport(spec.official_url, timeout_sec)
        except RedirectRejectedError as error:
            return _failed_with_cleanup(
                model_key,
                "download_redirect_rejected",
                _safe_detail(error),
                store,
            )
        except urllib.error.HTTPError as error:
            if 300 <= int(error.code) < 400:
                return _failed_with_cleanup(
                    model_key,
                    "download_redirect_rejected",
                    "HTTP redirect was rejected.",
                    store,
                )
            return _failed_with_cleanup(
                model_key,
                "download_http_status",
                f"HTTP status {error.code}.",
                store,
            )
        except Exception as error:
            return _failed_with_cleanup(
                model_key,
                "download_connection_failed",
                _safe_detail(error),
                store,
            )

        if response.status in {301, 302, 303, 307, 308}:
            return _failed_with_cleanup(
                model_key,
                "download_redirect_rejected",
                f"HTTP redirect was rejected (status {response.status}).",
                store,
            )
        if response.status != 200:
            return _failed_with_cleanup(
                model_key,
                "download_http_status",
                f"HTTP status {response.status}.",
                store,
            )

        content_length = _get_header(response.headers, "Content-Length")
        parsed_length = _parse_content_length(content_length)
        if parsed_length is None:
            return _failed_with_cleanup(
                model_key,
                "download_content_length_invalid",
                "Content-Length is missing or invalid.",
                store,
            )
        if parsed_length != spec.size_bytes:
            return _failed_with_cleanup(
                model_key,
                "download_content_length_mismatch",
                "Content-Length does not match the manifest exact size.",
                store,
            )

        _emit_progress(progress_callback, model_key, DOWNLOAD_PHASE_DOWNLOADING, 0, spec.size_bytes)
        received = 0
        stream_failure_code: str | None = None
        stream_failure_detail = ""
        try:
            with canonical_staging.open("wb") as staging:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        stream_failure_code = DOWNLOAD_STATUS_CANCELLED
                        stream_failure_detail = "Download was cancelled."
                        break
                    try:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                    except Exception as error:
                        stream_failure_code = "download_read_failed"
                        stream_failure_detail = _safe_detail(error)
                        break
                    if chunk == b"":
                        break
                    if not isinstance(chunk, bytes):
                        stream_failure_code = "download_read_failed"
                        stream_failure_detail = "HTTP response returned a non-bytes chunk."
                        break
                    received += len(chunk)
                    if received > spec.size_bytes:
                        stream_failure_code = "download_overrun"
                        stream_failure_detail = (
                            "Received bytes exceed the manifest exact size."
                        )
                        break
                    staging.write(chunk)
                    _emit_progress(
                        progress_callback,
                        model_key,
                        DOWNLOAD_PHASE_DOWNLOADING,
                        received,
                        spec.size_bytes,
                    )
                staging.flush()
        except OSError as error:
            stream_failure_code = "storage_write_failed"
            stream_failure_detail = _safe_detail(error)

        if stream_failure_code == DOWNLOAD_STATUS_CANCELLED:
            return _cancelled_after_cleanup(model_key, store)
        if stream_failure_code is not None:
            return _failed_with_cleanup(
                model_key,
                stream_failure_code,
                stream_failure_detail,
                store,
            )

        if received != spec.size_bytes:
            return _failed_with_cleanup(
                model_key,
                "download_short_read",
                "Received bytes do not match the manifest exact size.",
                store,
            )
        _emit_progress(progress_callback, model_key, DOWNLOAD_PHASE_VERIFYING, received, spec.size_bytes)
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

    try:
        checkpoint_result = store.promote_verified_staging(model_key)
    except Exception as error:
        return _failed_with_cleanup(
            model_key,
            "model_promote_failed",
            _safe_detail(error),
            store,
        )
    if isinstance(checkpoint_result, VerifiedWhisperCheckpoint):
        _emit_progress(progress_callback, model_key, DOWNLOAD_PHASE_VERIFYING, spec.size_bytes, spec.size_bytes)
        return DownloadResult(
            model_key=model_key,
            status=DOWNLOAD_STATUS_SUCCEEDED,
            checkpoint=checkpoint_result,
            cleanup_status="promoted",
        )
    assert isinstance(checkpoint_result, StoreFailure)
    return DownloadResult(
        model_key=model_key,
        status=DOWNLOAD_STATUS_FAILED,
        failure_code=checkpoint_result.failure_code,
        failure_detail=checkpoint_result.message,
        cleanup_status="handled_by_store",
    )


def _validate_spec(spec: WhisperModelSpec) -> str | None:
    parsed = urlsplit(spec.official_url)
    if (
        isinstance(spec.size_bytes, bool)
        or not isinstance(spec.size_bytes, int)
        or spec.size_bytes <= 0
        or parsed.scheme != "https"
        or parsed.netloc != _OFFICIAL_MODEL_HOST
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        != f"{_OFFICIAL_MODEL_PATH_PREFIX}{spec.sha256}/{spec.filename}"
    ):
        return "Manifest URL is not an official fixed model URL."
    return None


def _get_header(headers: Mapping[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if str(key).lower() == lowered:
            return str(value).strip()
    return None


def _parse_content_length(value: str | None) -> int | None:
    if value is None or not value or not value.isdigit():
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _emit_progress(
    callback: Callable[[DownloadProgress], None] | None,
    model_key: str,
    phase: str,
    received_bytes: int,
    expected_bytes: int,
) -> None:
    if callback is not None:
        callback(
            DownloadProgress(
                model_key=model_key,
                phase=phase,
                received_bytes=received_bytes,
                expected_bytes=expected_bytes,
            )
        )


def _failed(model_key: str, failure_code: str, detail: str) -> DownloadResult:
    return DownloadResult(
        model_key=model_key,
        status=DOWNLOAD_STATUS_FAILED,
        failure_code=failure_code,
        failure_detail=detail,
    )


def _failed_with_cleanup(
    model_key: str,
    failure_code: str,
    detail: str,
    store: WhisperModelStore,
) -> DownloadResult:
    cleanup = store.discard_staging(model_key)
    cleanup_detail = detail
    if not cleanup.succeeded:
        cleanup_detail = f"{detail} Staging cleanup failed: {cleanup.message}"
    return DownloadResult(
        model_key=model_key,
        status=DOWNLOAD_STATUS_FAILED,
        failure_code=failure_code,
        failure_detail=cleanup_detail,
        cleanup_status=cleanup.status,
    )


def _cancelled_after_cleanup(model_key: str, store: WhisperModelStore) -> DownloadResult:
    cleanup = store.discard_staging(model_key)
    detail = "Download was cancelled."
    failure_code = None
    if not cleanup.succeeded:
        detail = f"{detail} Staging cleanup failed: {cleanup.message}"
        failure_code = "cleanup_failed"
    return DownloadResult(
        model_key=model_key,
        status=DOWNLOAD_STATUS_CANCELLED,
        failure_code=failure_code,
        failure_detail=detail,
        cleanup_status=cleanup.status,
    )


def _safe_detail(error: BaseException) -> str:
    message = str(error).strip()
    return message or error.__class__.__name__


__all__ = [
    "DEFAULT_DOWNLOAD_TIMEOUT_SEC",
    "DOWNLOAD_PHASE_DOWNLOADING",
    "DOWNLOAD_PHASE_VERIFYING",
    "DOWNLOAD_STATUS_CANCELLED",
    "DOWNLOAD_STATUS_FAILED",
    "DOWNLOAD_STATUS_SUCCEEDED",
    "DownloadProgress",
    "DownloadResult",
    "HttpResponse",
    "HttpTransport",
    "RedirectRejectedError",
    "download_model",
    "urllib_http_transport",
]
