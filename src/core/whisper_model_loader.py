from __future__ import annotations

import hashlib
import io
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.whisper_models import (
    WhisperModelCatalog,
    WhisperModelSpec,
    load_whisper_model_catalog,
)


CHECKPOINT_CHUNK_SIZE = 1024 * 1024
_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


class WhisperModelLoaderError(RuntimeError):
    """Stable fail-closed error raised by the verified local checkpoint loader."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class VerifiedWhisperCheckpoint:
    model_key: str
    checkpoint_path: Path
    manifest_identity: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class LoadedWhisperModel:
    model: Any
    model_key: str
    manifest_identity: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class _VerifiedCheckpointBytes:
    data: bytes
    size_bytes: int
    sha256: str
    manifest_identity: str


def load_verified_local_checkpoint(
    checkpoint: VerifiedWhisperCheckpoint,
    *,
    catalog: WhisperModelCatalog | None = None,
    device: Any | None = None,
) -> LoadedWhisperModel:
    """Load one B2-attested checkpoint without any network or path re-open path."""
    if catalog is None:
        try:
            catalog = load_whisper_model_catalog()
        except Exception as error:
            if isinstance(error, WhisperModelLoaderError):
                raise
            raise WhisperModelLoaderError("manifest_invalid", str(error)) from error

    spec = _validate_checkpoint_contract(checkpoint, catalog)
    whisper_module = _import_whisper()
    _validate_whisper_package(whisper_module, spec.model_key)
    verified_bytes = _read_verified_checkpoint(checkpoint, spec)
    torch_module = _import_torch()
    model = _load_model_from_bytes(
        whisper_module=whisper_module,
        torch_module=torch_module,
        checkpoint_bytes=verified_bytes.data,
        alignment_heads=_get_alignment_heads(whisper_module, spec.model_key),
        device=device,
    )
    return LoadedWhisperModel(
        model=model,
        model_key=checkpoint.model_key,
        manifest_identity=checkpoint.manifest_identity,
        sha256=verified_bytes.sha256,
        size_bytes=verified_bytes.size_bytes,
    )


def _validate_checkpoint_contract(
    checkpoint: VerifiedWhisperCheckpoint,
    catalog: WhisperModelCatalog,
) -> WhisperModelSpec:
    if not isinstance(checkpoint, VerifiedWhisperCheckpoint):
        raise WhisperModelLoaderError("checkpoint_not_verified", "Loader input must be a VerifiedWhisperCheckpoint.")
    if not isinstance(checkpoint.checkpoint_path, Path):
        raise WhisperModelLoaderError("checkpoint_not_verified", "checkpoint_path must be a local Path.")
    try:
        spec = catalog.get(checkpoint.model_key)
    except Exception as error:
        raise WhisperModelLoaderError("checkpoint_not_verified", str(error)) from error
    expected_identity = catalog.manifest_identity(spec.model_key)
    if (
        checkpoint.manifest_identity != expected_identity
        or checkpoint.sha256 != spec.sha256
        or checkpoint.size_bytes != spec.size_bytes
    ):
        raise WhisperModelLoaderError(
            "checkpoint_not_verified",
            "Checkpoint metadata does not match the versioned manifest.",
        )
    return spec


def _import_whisper() -> Any:
    try:
        import whisper
    except Exception as error:
        raise WhisperModelLoaderError("whisper_package_missing", str(error)) from error
    return whisper


def _import_torch() -> Any:
    try:
        import torch
    except Exception as error:
        raise WhisperModelLoaderError("torch_package_missing", str(error)) from error
    return torch


def _validate_whisper_package(whisper_module: Any, model_key: str) -> None:
    if getattr(whisper_module, "__version__", None) != "20250625":
        raise WhisperModelLoaderError("whisper_version_mismatch", "Whisper package version must be 20250625.")
    _get_alignment_heads(whisper_module, model_key)
    if not callable(getattr(whisper_module, "ModelDimensions", None)):
        raise WhisperModelLoaderError("alignment_heads_api_missing", "Whisper ModelDimensions is unavailable.")
    if not callable(getattr(whisper_module, "Whisper", None)):
        raise WhisperModelLoaderError("alignment_heads_api_missing", "Whisper model constructor is unavailable.")


def _get_alignment_heads(whisper_module: Any, model_key: str) -> bytes:
    alignment_heads = getattr(whisper_module, "_ALIGNMENT_HEADS", None)
    if not isinstance(alignment_heads, dict):
        raise WhisperModelLoaderError("alignment_heads_api_missing", "Whisper alignment-head mapping is unavailable.")
    if model_key not in alignment_heads:
        raise WhisperModelLoaderError("alignment_heads_key_missing", f"No alignment heads for {model_key!r}.")
    model_alignment_heads = alignment_heads[model_key]
    if not isinstance(model_alignment_heads, bytes) or not model_alignment_heads:
        raise WhisperModelLoaderError(
            "alignment_heads_format_invalid",
            f"Alignment heads for {model_key!r} must be non-empty bytes.",
        )
    return model_alignment_heads


def _read_verified_checkpoint(
    checkpoint: VerifiedWhisperCheckpoint,
    spec: WhisperModelSpec,
) -> _VerifiedCheckpointBytes:
    path = checkpoint.checkpoint_path
    try:
        before_path_stat = os.lstat(path)
    except FileNotFoundError as error:
        raise WhisperModelLoaderError("checkpoint_path_invalid", f"Checkpoint does not exist: {path}") from error
    except OSError as error:
        raise WhisperModelLoaderError("checkpoint_read_failed", f"Could not inspect checkpoint: {error}") from error

    _require_regular_checkpoint_path(path, before_path_stat)

    digest = hashlib.sha256()
    buffer = bytearray()
    try:
        with path.open("rb") as stream:
            before_fd_stat = os.fstat(stream.fileno())
            if not _same_file_identity(before_path_stat, before_fd_stat):
                raise WhisperModelLoaderError(
                    "checkpoint_changed_during_revalidation",
                    "Checkpoint identity changed before reading.",
                )
            while True:
                chunk = stream.read(CHECKPOINT_CHUNK_SIZE)
                if not chunk:
                    break
                buffer.extend(chunk)
                digest.update(chunk)
            after_fd_stat = os.fstat(stream.fileno())
        try:
            after_path_stat = os.lstat(path)
        except FileNotFoundError as error:
            raise WhisperModelLoaderError(
                "checkpoint_changed_during_revalidation",
                "Checkpoint disappeared during reading.",
            ) from error
    except WhisperModelLoaderError:
        raise
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as error:
        raise WhisperModelLoaderError("checkpoint_path_invalid", f"Checkpoint path is invalid: {error}") from error
    except OSError as error:
        raise WhisperModelLoaderError("checkpoint_read_failed", f"Could not read checkpoint: {error}") from error

    if not _same_file_snapshot(before_fd_stat, after_fd_stat) or not _same_file_snapshot(after_fd_stat, after_path_stat):
        raise WhisperModelLoaderError(
            "checkpoint_changed_during_revalidation",
            "Checkpoint identity or metadata changed during reading.",
        )

    actual_size = len(buffer)
    actual_sha256 = digest.hexdigest()
    if actual_size != spec.size_bytes or actual_sha256 != spec.sha256:
        raise WhisperModelLoaderError(
            "checkpoint_integrity_mismatch",
            "Checkpoint bytes do not match the versioned manifest.",
        )

    return _VerifiedCheckpointBytes(
        data=bytes(buffer),
        size_bytes=actual_size,
        sha256=actual_sha256,
        manifest_identity=checkpoint.manifest_identity,
    )


def _require_regular_checkpoint_path(path: Path, path_stat: os.stat_result) -> None:
    if path.name.lower().endswith(".part"):
        raise WhisperModelLoaderError("checkpoint_path_invalid", "Partial checkpoint files are not loadable.")
    if not stat.S_ISREG(path_stat.st_mode):
        raise WhisperModelLoaderError("checkpoint_path_invalid", "Checkpoint must be a regular file.")
    if getattr(path_stat, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise WhisperModelLoaderError("checkpoint_path_invalid", "Checkpoint reparse points are not loadable.")


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and getattr(left, "st_file_attributes", 0) == getattr(right, "st_file_attributes", 0)
    )


def _same_file_snapshot(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        _same_file_identity(left, right)
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )


def _load_model_from_bytes(
    *,
    whisper_module: Any,
    torch_module: Any,
    checkpoint_bytes: bytes,
    alignment_heads: bytes,
    device: Any | None,
) -> Any:
    try:
        resolved_device = device
        if resolved_device is None:
            cuda = getattr(torch_module, "cuda", None)
            resolved_device = "cuda" if cuda is not None and cuda.is_available() else "cpu"
        checkpoint = torch_module.load(
            io.BytesIO(checkpoint_bytes),
            map_location=resolved_device,
            weights_only=True,
        )
        dimensions = whisper_module.ModelDimensions(**checkpoint["dims"])
        model = whisper_module.Whisper(dimensions)
        model.load_state_dict(checkpoint["model_state_dict"])
        set_alignment_heads = getattr(model, "set_alignment_heads", None)
        if not callable(set_alignment_heads):
            raise WhisperModelLoaderError(
                "alignment_heads_apply_failed",
                "Whisper model does not expose set_alignment_heads().",
            )
        try:
            set_alignment_heads(alignment_heads)
        except Exception as error:
            raise WhisperModelLoaderError("alignment_heads_apply_failed", str(error)) from error
        return model.to(resolved_device)
    except WhisperModelLoaderError:
        raise
    except Exception as error:
        raise WhisperModelLoaderError("checkpoint_bytes_load_failed", str(error)) from error
