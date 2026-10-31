from __future__ import annotations

import hashlib
import os
import stat
import tempfile
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Literal

from src.core.final_output_gate import (
    VerifiedVmdSaveRequest,
    validate_shared_save_request,
    validate_shared_output_readback,
)
from src.vmd_writer.verified_morph_output import (
    VerifiedMorphOutputError,
    VerifiedVmdEvidence,
    validate_verified_morph_readback,
    verify_evidence_unchanged,
    write_verified_morph_vmd,
)


SaveStatus = Literal["committed", "failed", "cancelled"]


def _validate_request_readback(
    request: VerifiedVmdSaveRequest,
    output_path: Path,
    projection,
) -> VerifiedVmdEvidence:
    if request.context.transition_binding is not None or request.context.cleanup_binding is not None:
        return validate_shared_output_readback(
            request.context,
            output_path,
            model_name=request.model_name,
        )
    return validate_verified_morph_readback(
        output_path,
        projection,
        request.context.candidate.plan,
        model_name=request.model_name,
    )


class VerifiedVmdSaveError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class VerifiedVmdSaveTerminalResult:
    job_id: int
    status: SaveStatus
    error_code: str | None
    committed: bool
    final_path: Path | None
    temporary_path: Path | None
    commit_phase: str
    evidence: VerifiedVmdEvidence | None
    cleanup_error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"committed", "failed", "cancelled"}:
            raise ValueError("save status is invalid")
        if self.status == "committed" and not self.committed:
            raise ValueError("committed status requires a committed file")
        if self.committed and self.final_path is None:
            raise ValueError("committed save requires a final path")


class VerifiedVmdCancelToken:
    """Cancellation token with a clear pre-commit/commit boundary."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._commit_started = False
        self._commit_result: str | None = None
        self._phase = "created"

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    @property
    def commit_started(self) -> bool:
        with self._lock:
            return self._commit_started

    @property
    def commit_result(self) -> str | None:
        with self._lock:
            return self._commit_result

    @property
    def phase(self) -> str:
        with self._lock:
            return self._phase

    def request_cancel(self) -> bool:
        with self._lock:
            if self._commit_started:
                return False
            self._cancel_requested = True
            return True

    def set_phase(self, phase: str) -> None:
        with self._lock:
            self._phase = phase

    def begin_commit(self) -> bool:
        with self._lock:
            if self._cancel_requested:
                return False
            self._commit_started = True
            self._phase = "commit_started"
            return True

    def set_commit_result(self, result: str) -> None:
        with self._lock:
            self._commit_result = result
            self._phase = result


def capture_vmd_file_identity(
    path: str | Path,
) -> tuple[int | None, int | None, int | None, int] | None:
    target = Path(path)
    try:
        file_stat = target.lstat()
    except FileNotFoundError:
        return None
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise VerifiedVmdSaveError("output_path_inspection_failed", "save path cannot be inspected") from error
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise VerifiedVmdSaveError("output_path_invalid", "save path is not a regular file")
    size = int(file_stat.st_size)
    if size < 0:
        raise VerifiedVmdSaveError("output_path_inspection_failed", "save path size is invalid")
    return (
        getattr(file_stat, "st_dev", None),
        getattr(file_stat, "st_ino", None),
        getattr(file_stat, "st_mtime_ns", None),
        size,
    )


def _path_key(value: str | Path) -> str:
    try:
        return os.path.normcase(str(Path(value).resolve(strict=False)))
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise VerifiedVmdSaveError("output_path_invalid", "save path is invalid") from error


def _validate_request_target(request: VerifiedVmdSaveRequest) -> Path:
    try:
        target = Path(os.path.abspath(request.final_path))
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise VerifiedVmdSaveError("output_path_invalid", "save path is invalid") from error
    if target.suffix.lower() != ".vmd":
        raise VerifiedVmdSaveError("output_path_invalid", "save path must end in .vmd")
    try:
        path_units = len(str(target).encode("utf-16-le", errors="strict")) // 2
    except UnicodeEncodeError as error:
        raise VerifiedVmdSaveError("output_path_invalid", "save path contains invalid Unicode") from error
    if path_units > 240:
        raise VerifiedVmdSaveError("output_path_too_long", "save path exceeds the Windows path budget")
    try:
        parent = target.parent
        if not parent.is_dir():
            raise VerifiedVmdSaveError("output_parent_invalid", "save directory does not exist")
    except VerifiedVmdSaveError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise VerifiedVmdSaveError("output_path_invalid", "save path is invalid") from error
    protected_paths = {
        _path_key(path)
        for path in (
            request.context.input_identity.source_audio_path,
            request.context.input_identity.analysis_wav_path,
            request.context.input_identity.normalized_text_path,
            *request.protected_paths,
        )
        if path is not None
    }
    if _path_key(target) in protected_paths:
        raise VerifiedVmdSaveError("output_path_invalid", "save path overlaps an input file")
    return target


def validate_vmd_save_target(request: VerifiedVmdSaveRequest) -> Path:
    """Validate the selected destination before the owning save job is started."""
    if not isinstance(request, VerifiedVmdSaveRequest):
        raise TypeError("request must be VerifiedVmdSaveRequest")
    return _validate_request_target(request)


def _owned_file_identity(path: Path) -> tuple[int | None, int | None]:
    file_stat = path.stat()
    return getattr(file_stat, "st_dev", None), getattr(file_stat, "st_ino", None)


def _cleanup_owned_temporary(
    path: Path | None,
    owner_identity: tuple[int | None, int | None] | None,
) -> str | None:
    if path is None or owner_identity is None:
        return None
    try:
        current_identity = _owned_file_identity(path)
        if current_identity != owner_identity:
            return "owned temporary identity changed; cleanup skipped"
        path.unlink()
        return None
    except FileNotFoundError:
        return None
    except OSError as error:
        return f"{type(error).__name__}: {error}"


def run_verified_vmd_save(
    request: VerifiedVmdSaveRequest,
    cancel_token: VerifiedVmdCancelToken,
    pre_commit_guard: Callable[[VerifiedVmdSaveRequest, VerifiedVmdCancelToken], str],
) -> VerifiedVmdSaveTerminalResult:
    """Create, verify, and atomically commit one shared-output VMD."""
    temporary_path: Path | None = None
    owner_identity: tuple[int | None, int | None] | None = None
    evidence: VerifiedVmdEvidence | None = None
    phase = "before_write"

    def finish(result: VerifiedVmdSaveTerminalResult) -> VerifiedVmdSaveTerminalResult:
        if cancel_token.commit_result == "committed":
            return result
        cleanup_error = _cleanup_owned_temporary(temporary_path, owner_identity)
        if cleanup_error is None:
            return replace(result, temporary_path=None)
        return replace(
            result,
            temporary_path=temporary_path,
            cleanup_error=cleanup_error,
        )

    if not isinstance(request, VerifiedVmdSaveRequest):
        raise TypeError("request must be VerifiedVmdSaveRequest")
    if not isinstance(cancel_token, VerifiedVmdCancelToken):
        raise TypeError("cancel_token must be VerifiedVmdCancelToken")
    try:
        if not callable(pre_commit_guard):
            raise VerifiedVmdSaveError("delivery_commit_guard_failed", "save guard is unavailable")
        if cancel_token.cancel_requested:
            return finish(VerifiedVmdSaveTerminalResult(
                request.job_id, "cancelled", "output_cancelled", False, None, None,
                "before_write", None,
            ))
        projection = validate_shared_save_request(request)
        final_path = _validate_request_target(request)
        current_final_identity = capture_vmd_file_identity(final_path)
        if current_final_identity != request.expected_existing_file_identity:
            raise VerifiedVmdSaveError("output_destination_collision", "save path changed after confirmation")
        if current_final_identity is not None and not request.overwrite_authorized:
            raise VerifiedVmdSaveError("output_destination_collision", "overwrite consent is missing")

        cancel_token.set_phase("creating_temporary")
        try:
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{final_path.name}.",
                suffix=".ms31-b4.tmp",
                dir=final_path.parent,
            )
            temporary_path = Path(temp_name)
            owner_identity = _owned_file_identity(temporary_path)
            os.close(fd)
        except OSError as error:
            raise VerifiedVmdSaveError("output_permission_denied", "temporary VMD cannot be created") from error

        if cancel_token.cancel_requested:
            return finish(VerifiedVmdSaveTerminalResult(
                request.job_id, "cancelled", "output_cancelled", False, None,
                temporary_path, "before_write", None,
            ))
        phase = "writing"
        cancel_token.set_phase(phase)
        try:
            write_verified_morph_vmd(
                temporary_path,
                projection,
                model_name=request.model_name,
            )
        except (OSError, VerifiedMorphOutputError, TypeError, ValueError) as error:
            raise VerifiedVmdSaveError("vmd_write_failed", "verified VMD writing failed") from error

        if cancel_token.cancel_requested:
            return finish(VerifiedVmdSaveTerminalResult(
                request.job_id, "cancelled", "output_cancelled", False, None,
                temporary_path, "before_readback", None,
            ))
        phase = "readback"
        cancel_token.set_phase(phase)
        try:
            evidence = _validate_request_readback(
                request,
                temporary_path,
                projection,
            )
        except (OSError, VerifiedMorphOutputError, TypeError, ValueError) as error:
            raise VerifiedVmdSaveError("vmd_validation_failed", "verified VMD readback failed") from error
        if not verify_evidence_unchanged(evidence):
            raise VerifiedVmdSaveError("vmd_validation_failed", "verified temporary VMD changed after readback")
        if _owned_file_identity(temporary_path) != owner_identity:
            raise VerifiedVmdSaveError("vmd_validation_failed", "temporary VMD ownership changed")
        if cancel_token.cancel_requested:
            return finish(VerifiedVmdSaveTerminalResult(
                request.job_id, "cancelled", "output_cancelled", False, None,
                temporary_path, "before_commit", evidence,
            ))

        phase = "awaiting_commit_guard"
        cancel_token.set_phase(phase)
        try:
            decision = pre_commit_guard(request, cancel_token)
        except Exception as error:
            raise VerifiedVmdSaveError("delivery_commit_guard_failed", "save commit guard failed") from error
        if decision in {"cancelled", "closing"} or cancel_token.cancel_requested:
            return finish(VerifiedVmdSaveTerminalResult(
                request.job_id, "cancelled", "output_cancelled", False, None,
                temporary_path, phase, evidence,
            ))
        if decision != "authorized":
            raise VerifiedVmdSaveError("delivery_state_stale", "save state changed before commit")

        phase = "before_commit"
        if not verify_evidence_unchanged(evidence):
            raise VerifiedVmdSaveError("vmd_validation_failed", "temporary VMD changed before commit")
        current_final_identity = capture_vmd_file_identity(final_path)
        if current_final_identity != request.expected_existing_file_identity:
            raise VerifiedVmdSaveError("output_destination_collision", "save path changed before commit")
        if cancel_token.cancel_requested or not cancel_token.begin_commit():
            return VerifiedVmdSaveTerminalResult(
                request.job_id, "cancelled", "output_cancelled", False, None,
                temporary_path, phase, evidence,
            )

        try:
            if request.expected_existing_file_identity is None:
                os.rename(temporary_path, final_path)
            else:
                os.replace(temporary_path, final_path)
        except FileExistsError as error:
            cancel_token.set_commit_result("commit_failed")
            raise VerifiedVmdSaveError("output_destination_collision", "save path appeared before commit") from error
        except PermissionError as error:
            cancel_token.set_commit_result("commit_failed")
            raise VerifiedVmdSaveError("output_permission_denied", "save destination could not be committed") from error
        except OSError as error:
            cancel_token.set_commit_result("commit_failed")
            raise VerifiedVmdSaveError("delivery_commit_failed", "verified VMD could not be committed") from error

        cancel_token.set_commit_result("committed")
        temporary_path = None
        evidence = None
        final_evidence = _validate_request_readback(
            request,
            final_path,
            projection,
        )
        if not verify_evidence_unchanged(final_evidence):
            return finish(VerifiedVmdSaveTerminalResult(
                request.job_id,
                "failed",
                "vmd_validation_failed",
                True,
                final_path,
                None,
                "committed",
                final_evidence,
            ))
        return finish(VerifiedVmdSaveTerminalResult(
            request.job_id,
            "committed",
            None,
            True,
            final_path,
            None,
            "committed",
            final_evidence,
        ))
    except VerifiedVmdSaveError as error:
        return finish(VerifiedVmdSaveTerminalResult(
            request.job_id,
            "failed",
            error.code,
            cancel_token.commit_result == "committed",
            request.final_path if cancel_token.commit_result == "committed" else None,
            temporary_path,
            cancel_token.phase if cancel_token.commit_started else phase,
            evidence,
        ))
    except Exception as error:
        return finish(VerifiedVmdSaveTerminalResult(
            request.job_id,
            "failed",
            "vmd_write_failed" if phase in {"before_write", "writing"} else "vmd_validation_failed",
            cancel_token.commit_result == "committed",
            request.final_path if cancel_token.commit_result == "committed" else None,
            temporary_path,
            cancel_token.phase if cancel_token.commit_started else phase,
            evidence,
        ))


__all__ = [
    "VerifiedVmdCancelToken",
    "VerifiedVmdSaveError",
    "VerifiedVmdSaveTerminalResult",
    "capture_vmd_file_identity",
    "run_verified_vmd_save",
    "validate_vmd_save_target",
]
