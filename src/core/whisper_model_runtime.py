from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from .whisper_model_loader import (
    LoadedWhisperModel,
    VerifiedWhisperCheckpoint,
    load_verified_local_checkpoint,
)
from .whisper_model_store import (
    OwnershipReleasePermit,
    _issue_ownership_release_permit_for_runtime,
)
from .whisper_models import WhisperModelCatalog, load_whisper_model_catalog


WHISPER_FAILURE_CLASSES = frozenset(
    {
        "none",
        "model_unavailable",
        "integrity_mismatch",
        "load_failure",
        "memory_failure",
        "transcribe_failure",
        "cancelled",
    }
)


class WhisperModelRuntimeError(RuntimeError):
    """Fail-closed error raised by the verified local model runtime."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        failure_class: str = "load_failure",
    ) -> None:
        if failure_class not in WHISPER_FAILURE_CLASSES:
            raise ValueError(f"unsupported Whisper failure class: {failure_class}")
        self.code = code
        self.failure_class = failure_class
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class ModelIdentity:
    model_key: str
    manifest_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.model_key, str) or not self.model_key:
            raise ValueError("model_key must be a non-empty string")
        if not isinstance(self.manifest_identity, str) or not self.manifest_identity:
            raise ValueError("manifest_identity must be a non-empty string")


@dataclass(frozen=True)
class RuntimeCacheIdentity:
    model_key: str
    canonical_storage_root: str
    manifest_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.model_key, str) or not self.model_key:
            raise ValueError("model_key must be a non-empty string")
        if not isinstance(self.canonical_storage_root, str) or not self.canonical_storage_root:
            raise ValueError("canonical_storage_root must be a non-empty string")
        if not isinstance(self.manifest_identity, str) or not self.manifest_identity:
            raise ValueError("manifest_identity must be a non-empty string")


@dataclass(frozen=True)
class VerifiedAnalysisModelRequest:
    identity: ModelIdentity
    cache_identity: RuntimeCacheIdentity
    verified_checkpoint: VerifiedWhisperCheckpoint

    def __post_init__(self) -> None:
        checkpoint = self.verified_checkpoint
        if not isinstance(checkpoint, VerifiedWhisperCheckpoint):
            raise ValueError("verified_checkpoint must be a VerifiedWhisperCheckpoint")
        if checkpoint.model_key != self.identity.model_key:
            raise ValueError("checkpoint model key does not match request identity")
        if checkpoint.manifest_identity != self.identity.manifest_identity:
            raise ValueError("checkpoint manifest identity does not match request identity")
        if self.cache_identity.model_key != self.identity.model_key:
            raise ValueError("cache model key does not match request identity")
        if self.cache_identity.manifest_identity != self.identity.manifest_identity:
            raise ValueError("cache manifest identity does not match request identity")


@dataclass(frozen=True)
class WhisperModelSession:
    model: Any
    identity: ModelIdentity
    cache_identity: RuntimeCacheIdentity
    session_id: str


@dataclass(frozen=True)
class WhisperModelCandidate:
    session: WhisperModelSession
    generation: int

    @property
    def candidate_session_id(self) -> str:
        return self.session.session_id


@dataclass
class _RuntimeOwner:
    session: WhisperModelSession
    leases: int = 0
    unload_requested: bool = False


def build_verified_analysis_model_request(
    availability: Any,
) -> VerifiedAnalysisModelRequest:
    """Build a runtime request from a B2 ``ModelAvailability`` DTO only."""
    if availability is None or not getattr(availability, "is_verified", False):
        code = getattr(availability, "failure_code", None) or "model_unavailable"
        raise WhisperModelRuntimeError(
            code,
            getattr(availability, "message", None)
            or "Whisper model availability is not verified.",
            failure_class="model_unavailable",
        )
    checkpoint = getattr(availability, "verified_checkpoint", None)
    if not isinstance(checkpoint, VerifiedWhisperCheckpoint):
        raise WhisperModelRuntimeError(
            "checkpoint_not_verified",
            "Verified availability did not contain a verified checkpoint.",
            failure_class="model_unavailable",
        )
    model_key = getattr(availability, "model_key", None)
    manifest_identity = getattr(availability, "manifest_identity", None)
    if checkpoint.model_key != model_key or checkpoint.manifest_identity != manifest_identity:
        raise WhisperModelRuntimeError(
            "model_identity_mismatch",
            "Availability and checkpoint identities do not match.",
            failure_class="integrity_mismatch",
        )
    storage_root = getattr(availability, "storage_root", None)
    if not isinstance(storage_root, Path):
        raise WhisperModelRuntimeError(
            "storage_path_invalid",
            "Verified availability has no local storage root.",
            failure_class="model_unavailable",
        )
    canonical_root = str(storage_root.resolve(strict=False))
    identity = ModelIdentity(model_key, manifest_identity)
    cache_identity = RuntimeCacheIdentity(
        model_key=model_key,
        canonical_storage_root=canonical_root,
        manifest_identity=manifest_identity,
    )
    return VerifiedAnalysisModelRequest(
        identity=identity,
        cache_identity=cache_identity,
        verified_checkpoint=checkpoint,
    )


def classify_whisper_failure(
    error: BaseException,
    *,
    default_failure_class: str = "transcribe_failure",
) -> tuple[str, str]:
    """Return the fixed B5 upper class and preserve the most specific code."""
    if default_failure_class not in WHISPER_FAILURE_CLASSES:
        raise ValueError(f"unsupported default Whisper failure class: {default_failure_class}")
    chain: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__

    if any(_is_memory_error(item) for item in chain):
        return "memory_failure", _error_code(error)

    codes = {_error_code(item) for item in chain}
    if codes & {
        "checkpoint_integrity_mismatch",
        "checkpoint_changed_during_revalidation",
        "model_size_mismatch",
        "model_sha256_mismatch",
        "model_changed_during_verification",
    }:
        return "integrity_mismatch", _error_code(error)
    if codes & {
        "model_missing",
        "model_partial",
        "model_key_unsupported",
        "model_invalid_path",
        "model_read_failed",
        "storage_path_invalid",
        "storage_path_remote",
        "model_unavailable",
        "checkpoint_not_verified",
    }:
        return "model_unavailable", _error_code(error)
    if codes & {
        "load_failed",
        "checkpoint_path_invalid",
        "checkpoint_read_failed",
        "manifest_invalid",
        "whisper_package_missing",
        "torch_package_missing",
        "whisper_version_mismatch",
        "alignment_heads_api_missing",
        "alignment_heads_key_missing",
        "alignment_heads_format_invalid",
        "alignment_heads_apply_failed",
        "checkpoint_bytes_load_failed",
        "whisper_model_load_failed",
    }:
        return "load_failure", _error_code(error)
    if codes & {"whisper_transcribe_failed", "transcribe_failure"}:
        return "transcribe_failure", _error_code(error)
    return default_failure_class, _error_code(error)


def _error_code(error: BaseException) -> str:
    code = getattr(error, "code", None)
    if isinstance(code, str) and code:
        return code
    return error.__class__.__name__


def _is_memory_error(error: BaseException) -> bool:
    if isinstance(error, MemoryError):
        return True
    text = str(error).lower()
    return "out of memory" in text or "cuda error: out of memory" in text


class WhisperModelRuntime:
    """Thread-safe single-active owner for verified local Whisper models."""

    def __init__(
        self,
        *,
        catalog: WhisperModelCatalog | None = None,
        loader: Callable[..., LoadedWhisperModel] = load_verified_local_checkpoint,
    ) -> None:
        self.catalog = catalog or load_whisper_model_catalog()
        self._loader = loader
        self._lock = RLock()
        self._owner: _RuntimeOwner | None = None
        self._candidate: WhisperModelCandidate | None = None
        self._generation = 0
        self._shutting_down = False

    @property
    def active_session(self) -> WhisperModelSession | None:
        with self._lock:
            return self._owner.session if self._owner is not None else None

    @property
    def candidate_session(self) -> WhisperModelCandidate | None:
        with self._lock:
            return self._candidate

    @property
    def is_shutting_down(self) -> bool:
        with self._lock:
            return self._shutting_down

    def acquire(self, request: VerifiedAnalysisModelRequest) -> WhisperModelSession:
        """Load or reuse the one active verified model and acquire one lease."""
        self._validate_request(request)
        with self._lock:
            if self._shutting_down:
                raise WhisperModelRuntimeError(
                    "shutdown",
                    "Whisper model runtime is shutting down.",
                    failure_class="cancelled",
                )
            owner = self._owner
            if owner is not None:
                if owner.session.cache_identity == request.cache_identity:
                    owner.leases += 1
                    return owner.session
                if owner.leases:
                    raise WhisperModelRuntimeError(
                        "runtime_busy",
                        "The active Whisper model is still in use.",
                        failure_class="cancelled",
                    )
                self._evict_owner_locked()
            session = self._load_request(request)
            self._owner = _RuntimeOwner(session=session, leases=1)
            return session

    def release(self, session: WhisperModelSession) -> None:
        with self._lock:
            owner = self._owner
            if owner is None or owner.session.session_id != session.session_id:
                return
            owner.leases = max(0, owner.leases - 1)
            if owner.leases == 0 and owner.unload_requested:
                self._evict_owner_locked()

    def prepare_candidate(self, request: VerifiedAnalysisModelRequest) -> WhisperModelCandidate:
        """Evict the old owner before loading a candidate, never two models at once."""
        self._validate_request(request)
        with self._lock:
            if self._shutting_down:
                raise WhisperModelRuntimeError(
                    "shutdown",
                    "Whisper model runtime is shutting down.",
                    failure_class="cancelled",
                )
            if self._candidate is not None:
                self._reject_candidate_locked(self._candidate)
            if self._owner is not None:
                if self._owner.leases:
                    raise WhisperModelRuntimeError(
                        "runtime_busy",
                        "The active Whisper model is still in use.",
                        failure_class="cancelled",
                    )
                self._evict_owner_locked()
            session = self._load_request(request)
            self._generation += 1
            candidate = WhisperModelCandidate(session=session, generation=self._generation)
            self._candidate = candidate
            return candidate

    def commit_candidate(self, candidate: WhisperModelCandidate) -> WhisperModelSession:
        with self._lock:
            self._require_candidate_locked(candidate)
            self._owner = _RuntimeOwner(session=candidate.session)
            self._candidate = None
            return candidate.session

    def reject_candidate(self, candidate: WhisperModelCandidate) -> None:
        with self._lock:
            self._require_candidate_locked(candidate)
            self._reject_candidate_locked(candidate)

    def unload(self) -> bool:
        """Request explicit unload; return false when a lease defers cleanup."""
        with self._lock:
            if self._owner is None:
                return True
            if self._owner.leases:
                self._owner.unload_requested = True
                return False
            self._evict_owner_locked()
            return True

    def begin_shutdown(self) -> bool:
        with self._lock:
            self._shutting_down = True
            if self._candidate is not None:
                self._reject_candidate_locked(self._candidate)
            return self.unload()

    def issue_ownership_release_permit(
        self,
        *,
        model_key: str,
        manifest_identity: str,
        artifact_id: str,
    ) -> OwnershipReleasePermit:
        """B5-only production issuer seam for the B4 delete worker."""
        return _issue_ownership_release_permit_for_runtime(
            model_key=model_key,
            manifest_identity=manifest_identity,
            artifact_id=artifact_id,
        )

    def _load_request(self, request: VerifiedAnalysisModelRequest) -> WhisperModelSession:
        try:
            loaded = self._loader(
                request.verified_checkpoint,
                catalog=self.catalog,
            )
        except Exception as error:
            failure_class, code = classify_whisper_failure(
                error,
                default_failure_class="load_failure",
            )
            raise WhisperModelRuntimeError(
                code,
                str(error),
                failure_class=failure_class,
            ) from error
        if not isinstance(loaded, LoadedWhisperModel):
            raise WhisperModelRuntimeError(
                "load_failed",
                "Verified loader returned an invalid loaded model.",
                failure_class="load_failure",
            )
        if loaded.model_key != request.identity.model_key or loaded.manifest_identity != request.identity.manifest_identity:
            self._cleanup_model(loaded.model)
            raise WhisperModelRuntimeError(
                "model_identity_mismatch",
                "Loaded model identity does not match the verified request.",
                failure_class="integrity_mismatch",
            )
        return WhisperModelSession(
            model=loaded.model,
            identity=request.identity,
            cache_identity=request.cache_identity,
            session_id=uuid4().hex,
        )

    def _validate_request(self, request: VerifiedAnalysisModelRequest) -> None:
        if not isinstance(request, VerifiedAnalysisModelRequest):
            raise WhisperModelRuntimeError(
                "model_request_missing",
                "A verified analysis model request is required.",
                failure_class="model_unavailable",
            )

    def _require_candidate_locked(self, candidate: WhisperModelCandidate) -> None:
        if self._candidate is None or self._candidate != candidate:
            raise WhisperModelRuntimeError(
                "candidate_stale",
                "Whisper model candidate is stale or already finalized.",
                failure_class="cancelled",
            )

    def _reject_candidate_locked(self, candidate: WhisperModelCandidate) -> None:
        if self._candidate is not None and self._candidate == candidate:
            self._cleanup_model(candidate.session.model)
            self._candidate = None

    def _evict_owner_locked(self) -> None:
        owner = self._owner
        if owner is None:
            return
        self._cleanup_model(owner.session.model)
        self._owner = None

    @staticmethod
    def _cleanup_model(model: Any) -> None:
        try:
            to_method = getattr(model, "to", None)
            if callable(to_method):
                to_method("cpu")
        except Exception:
            pass
        try:
            import torch

            cuda = getattr(torch, "cuda", None)
            empty_cache = getattr(cuda, "empty_cache", None)
            if callable(empty_cache):
                empty_cache()
            ipc_collect = getattr(cuda, "ipc_collect", None)
            if callable(ipc_collect):
                ipc_collect()
        except Exception:
            pass


__all__ = [
    "ModelIdentity",
    "RuntimeCacheIdentity",
    "VerifiedAnalysisModelRequest",
    "WhisperModelCandidate",
    "WhisperModelRuntime",
    "WhisperModelRuntimeError",
    "WhisperModelSession",
    "WHISPER_FAILURE_CLASSES",
    "build_verified_analysis_model_request",
    "classify_whisper_failure",
]
