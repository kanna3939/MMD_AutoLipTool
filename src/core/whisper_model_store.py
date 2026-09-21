from __future__ import annotations

import ctypes
import hashlib
import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile
from uuid import uuid4

from .settings_store import SettingsStore
from .whisper_model_loader import VerifiedWhisperCheckpoint
from .whisper_models import WhisperModelCatalog, WhisperModelSpec, load_whisper_model_catalog


CHECKPOINT_CHUNK_SIZE = 1024 * 1024
FREE_SPACE_RESERVE_BYTES = 64 * 1024 * 1024
_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
_DRIVE_UNKNOWN = 0
_DRIVE_NO_ROOT_DIR = 1
_DRIVE_REMOVABLE = 2
_DRIVE_FIXED = 3
_DRIVE_REMOTE = 4
_DRIVE_CDROM = 5
_DRIVE_RAMDISK = 6

ARTIFACT_MISSING = "missing"
ARTIFACT_PARTIAL = "partial"
ARTIFACT_VERIFIED = "verified"
ARTIFACT_INVALID_PATH = "invalid_path"
ARTIFACT_INVALID_SIZE = "invalid_size"
ARTIFACT_INVALID_SHA256 = "invalid_sha256"
ARTIFACT_READ_FAILED = "read_failed"
ARTIFACT_UNSUPPORTED = "unsupported"


class WhisperModelStoreError(RuntimeError):
    """Stable error for APIs that cannot return a structured operation result."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class StorageRootResolution:
    resolved_path: Path | None
    failure_code: str | None = None
    message: str | None = None
    used_default: bool = False

    @property
    def succeeded(self) -> bool:
        return self.resolved_path is not None and self.failure_code is None

    @property
    def path(self) -> Path | None:
        return self.resolved_path


@dataclass(frozen=True)
class StoreFailure:
    failure_code: str
    message: str
    model_key: str | None = None
    artifact_status: str | None = None
    path: Path | None = None
    actual_size_bytes: int | None = None
    observed_sha256: str | None = None


@dataclass(frozen=True)
class ModelAvailability:
    model_key: str
    artifact_status: str
    manifest_identity: str | None
    storage_root: Path
    file_path: Path | None
    partial_path: Path | None
    partial_present: bool
    actual_size_bytes: int | None
    observed_sha256: str | None
    failure_code: str | None
    verified_checkpoint: VerifiedWhisperCheckpoint | None
    message: str = ""

    @property
    def is_verified(self) -> bool:
        return self.artifact_status == ARTIFACT_VERIFIED and self.verified_checkpoint is not None


@dataclass(frozen=True)
class StoragePreflight:
    succeeded: bool
    model_key: str
    storage_root: Path
    staging_path: Path | None
    required_bytes: int | None
    free_bytes: int | None
    failure_code: str | None
    message: str = ""


@dataclass(frozen=True)
class StagingCleanupResult:
    succeeded: bool
    status: str
    path: Path | None
    failure_code: str | None
    message: str = ""


@dataclass(frozen=True)
class DeleteResult:
    succeeded: bool
    status: str
    file_path: Path | None
    availability: ModelAvailability | None
    failure_code: str | None
    message: str = ""


_PERMIT_ISSUER_TOKEN = object()


class OwnershipReleasePermit:
    """Opaque, single-use capability issued by the future B5 ownership boundary."""

    __slots__ = (
        "_issuer_token",
        "_model_key",
        "_manifest_identity",
        "_artifact_id",
        "_nonce",
        "_consumed",
    )

    def __init__(
        self,
        issuer_token: object,
        *,
        model_key: str,
        manifest_identity: str,
        artifact_id: str,
    ) -> None:
        if issuer_token is not _PERMIT_ISSUER_TOKEN:
            raise TypeError("OwnershipReleasePermit can only be created by its issuer boundary.")
        self._issuer_token = issuer_token
        self._model_key = model_key
        self._manifest_identity = manifest_identity
        self._artifact_id = artifact_id
        self._nonce = uuid4().hex
        self._consumed = False

    def _consume_for(self, *, model_key: str, manifest_identity: str, artifact_id: str) -> bool:
        if type(self) is not OwnershipReleasePermit:
            return False
        if self._issuer_token is not _PERMIT_ISSUER_TOKEN or self._consumed:
            return False
        if (
            self._model_key != model_key
            or self._manifest_identity != manifest_identity
            or self._artifact_id != artifact_id
            or not self._nonce
        ):
            return False
        self._consumed = True
        return True


def _issue_ownership_release_permit_for_testing(
    *,
    model_key: str,
    manifest_identity: str,
    artifact_id: str,
) -> OwnershipReleasePermit:
    """Test-only seam until MS24-B5 owns the production issuer boundary."""
    return OwnershipReleasePermit(
        _PERMIT_ISSUER_TOKEN,
        model_key=model_key,
        manifest_identity=manifest_identity,
        artifact_id=artifact_id,
    )


def _issue_ownership_release_permit_for_runtime(
    *,
    model_key: str,
    manifest_identity: str,
    artifact_id: str,
) -> OwnershipReleasePermit:
    """Private B5 runtime-only issuer; not part of the public store API."""
    return OwnershipReleasePermit(
        _PERMIT_ISSUER_TOKEN,
        model_key=model_key,
        manifest_identity=manifest_identity,
        artifact_id=artifact_id,
    )


@dataclass(frozen=True)
class _FileInspection:
    status: str
    failure_code: str | None
    message: str
    actual_size_bytes: int | None = None
    observed_sha256: str | None = None
    final_path_stat: os.stat_result | None = None


def default_whisper_models_dir() -> Path:
    """Return the persistent source or frozen application-adjacent model root."""
    return SettingsStore.default_settings_path().resolve().parent / "models"


def resolve_whisper_models_dir(configured_value: str | None) -> StorageRootResolution:
    """Resolve and validate a configured local model root without creating it."""
    used_default = configured_value is None or (
        isinstance(configured_value, str) and not configured_value.strip()
    )
    if used_default:
        return _validate_storage_root(default_whisper_models_dir(), used_default=True)
    if not isinstance(configured_value, str):
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message="Whisper model storage path must be a string.",
        )

    raw_value = configured_value.strip()
    if _looks_like_remote_or_device_path(raw_value):
        failure_code = "storage_path_remote" if _looks_like_remote_path(raw_value) else "storage_path_invalid"
        return StorageRootResolution(
            resolved_path=None,
            failure_code=failure_code,
            message="Whisper model storage path is not a permitted local path.",
        )

    try:
        path = Path(raw_value)
    except (OSError, TypeError, ValueError) as error:
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message=f"Whisper model storage path is invalid: {error}",
        )
    if not _is_absolute_windows_path(raw_value, path):
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message="Whisper model storage path must be an absolute local path.",
        )
    return _validate_storage_root(path, used_default=False)


class WhisperModelStore:
    """UI-independent local storage and integrity boundary for Whisper models."""

    def __init__(
        self,
        storage_root: Path | None = None,
        *,
        catalog: WhisperModelCatalog | None = None,
    ) -> None:
        self.catalog = catalog or load_whisper_model_catalog()
        self._configured_root = Path(storage_root) if storage_root is not None else default_whisper_models_dir()
        initial_resolution = _validate_storage_root(self._configured_root, used_default=storage_root is None)
        self.storage_root = initial_resolution.resolved_path or self._configured_root

    def scan(self, model_key: str) -> ModelAvailability:
        spec, paths, failure = self._resolve_model_paths(model_key)
        if failure is not None:
            return self._availability_for_failure(model_key, spec, paths, failure)
        assert spec is not None
        assert paths is not None
        root, final_path, partial_path = paths
        partial_present = _path_exists_or_link(partial_path)
        if not root.exists():
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_PARTIAL if partial_present else ARTIFACT_MISSING,
                failure_code="model_partial" if partial_present else "model_missing",
                message="Only a partial artifact is present." if partial_present else "Model artifact is not present.",
            )

        inspection = _inspect_file(final_path, allow_partial=False)
        if inspection.status == "missing":
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_PARTIAL if partial_present else ARTIFACT_MISSING,
                failure_code="model_partial" if partial_present else "model_missing",
                message="Only a partial artifact is present." if partial_present else "Model artifact is not present.",
            )
        if inspection.status == "invalid_path":
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_INVALID_PATH,
                failure_code="model_invalid_path",
                message=inspection.message,
            )
        if inspection.status == "changed":
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_READ_FAILED,
                failure_code="model_changed_during_verification",
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
                message=inspection.message,
            )
        if inspection.status == "read_failed":
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_READ_FAILED,
                failure_code="model_read_failed",
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
                message=inspection.message,
            )

        assert inspection.status == "valid"
        if inspection.actual_size_bytes != spec.size_bytes:
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_INVALID_SIZE,
                failure_code="model_size_mismatch",
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
                message="Model artifact size does not match the manifest.",
            )
        if inspection.observed_sha256 != spec.sha256:
            return self._availability(
                model_key=model_key,
                spec=spec,
                root=root,
                final_path=final_path,
                partial_path=partial_path,
                partial_present=partial_present,
                artifact_status=ARTIFACT_INVALID_SHA256,
                failure_code="model_sha256_mismatch",
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
                message="Model artifact SHA256 does not match the manifest.",
            )

        checkpoint = VerifiedWhisperCheckpoint(
            model_key=model_key,
            checkpoint_path=final_path,
            manifest_identity=self.catalog.manifest_identity(model_key),
            sha256=spec.sha256,
            size_bytes=spec.size_bytes,
        )
        return self._availability(
            model_key=model_key,
            spec=spec,
            root=root,
            final_path=final_path,
            partial_path=partial_path,
            partial_present=partial_present,
            artifact_status=ARTIFACT_VERIFIED,
            failure_code=None,
            actual_size_bytes=inspection.actual_size_bytes,
            observed_sha256=inspection.observed_sha256,
            verified_checkpoint=checkpoint,
            message="Model artifact is verified.",
        )

    def scan_all(self) -> tuple[ModelAvailability, ...]:
        return tuple(self.scan(spec.model_key) for spec in self.catalog.models)

    def verify_checkpoint(self, model_key: str) -> VerifiedWhisperCheckpoint | StoreFailure:
        availability = self.scan(model_key)
        if availability.verified_checkpoint is not None:
            return availability.verified_checkpoint
        return StoreFailure(
            failure_code=availability.failure_code or "model_read_failed",
            message=availability.message or "Whisper model checkpoint is not verified.",
            model_key=model_key,
            artifact_status=availability.artifact_status,
            path=availability.file_path,
            actual_size_bytes=availability.actual_size_bytes,
            observed_sha256=availability.observed_sha256,
        )

    def preflight_download(self, model_key: str) -> StoragePreflight:
        spec, paths, failure = self._resolve_model_paths(model_key)
        if failure is not None:
            return self._preflight_failure(model_key, paths, failure)
        assert spec is not None
        assert paths is not None
        root, _, partial_path = paths

        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            return StoragePreflight(
                succeeded=False,
                model_key=model_key,
                storage_root=root,
                staging_path=partial_path,
                required_bytes=spec.size_bytes + FREE_SPACE_RESERVE_BYTES,
                free_bytes=None,
                failure_code="storage_not_writable",
                message=f"Could not create the Whisper model storage directory: {error}",
            )

        refreshed_root = _validate_storage_root(root, used_default=False)
        if not refreshed_root.succeeded or refreshed_root.resolved_path is None:
            return StoragePreflight(
                succeeded=False,
                model_key=model_key,
                storage_root=root,
                staging_path=partial_path,
                required_bytes=spec.size_bytes + FREE_SPACE_RESERVE_BYTES,
                free_bytes=None,
                failure_code=refreshed_root.failure_code or "storage_path_invalid",
                message=refreshed_root.message or "Storage root failed local-only validation after creation.",
            )
        root = refreshed_root.resolved_path
        partial_path = root / partial_path.name

        staging_failure = _validate_staging_destination(partial_path)
        if staging_failure is not None:
            return StoragePreflight(
                succeeded=False,
                model_key=model_key,
                storage_root=root,
                staging_path=partial_path,
                required_bytes=spec.size_bytes + FREE_SPACE_RESERVE_BYTES,
                free_bytes=None,
                failure_code=staging_failure[0],
                message=staging_failure[1],
            )

        probe_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="wb",
                delete=False,
                dir=str(root),
                prefix="mmd_autoliptool_model_probe_",
                suffix=".tmp",
            ) as probe:
                probe_path = Path(probe.name)
                probe.write(b"probe")
                probe.flush()
            probe_path.unlink()
        except OSError as error:
            if probe_path is not None:
                try:
                    probe_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return StoragePreflight(
                succeeded=False,
                model_key=model_key,
                storage_root=root,
                staging_path=partial_path,
                required_bytes=spec.size_bytes + FREE_SPACE_RESERVE_BYTES,
                free_bytes=None,
                failure_code="storage_not_writable",
                message=f"Whisper model storage write probe failed: {error}",
            )

        required_bytes = spec.size_bytes + FREE_SPACE_RESERVE_BYTES
        try:
            free_bytes = int(shutil.disk_usage(root).free)
        except OSError as error:
            return StoragePreflight(
                succeeded=False,
                model_key=model_key,
                storage_root=root,
                staging_path=partial_path,
                required_bytes=required_bytes,
                free_bytes=None,
                failure_code="storage_free_space_unknown",
                message=f"Could not determine free space for Whisper model storage: {error}",
            )
        if free_bytes < required_bytes:
            return StoragePreflight(
                succeeded=False,
                model_key=model_key,
                storage_root=root,
                staging_path=partial_path,
                required_bytes=required_bytes,
                free_bytes=free_bytes,
                failure_code="storage_free_space_insufficient",
                message="Whisper model storage does not have enough free space.",
            )
        return StoragePreflight(
            succeeded=True,
            model_key=model_key,
            storage_root=root,
            staging_path=partial_path,
            required_bytes=required_bytes,
            free_bytes=free_bytes,
            failure_code=None,
            message="Whisper model storage preflight succeeded.",
        )

    def staging_path(self, model_key: str) -> Path:
        _, paths, failure = self._resolve_model_paths(model_key)
        if failure is not None or paths is None:
            raise WhisperModelStoreError(
                failure.failure_code if failure is not None else "storage_path_invalid",
                failure.message if failure is not None else "Could not resolve staging path.",
            )
        staging_failure = _validate_staging_destination(paths[2])
        if staging_failure is not None:
            raise WhisperModelStoreError(staging_failure[0], staging_failure[1])
        return paths[2]

    def discard_staging(self, model_key: str) -> StagingCleanupResult:
        _, paths, failure = self._resolve_model_paths(model_key)
        if failure is not None or paths is None:
            return StagingCleanupResult(
                succeeded=False,
                status="failed",
                path=paths[2] if paths is not None else None,
                failure_code=failure.failure_code if failure is not None else "storage_path_invalid",
                message=failure.message if failure is not None else "Could not resolve staging path.",
            )
        partial_path = paths[2]
        if not _path_exists_or_link(partial_path):
            return StagingCleanupResult(
                succeeded=True,
                status="missing",
                path=partial_path,
                failure_code=None,
                message="Canonical staging artifact was already absent.",
            )
        try:
            path_stat = os.lstat(partial_path)
        except OSError as error:
            return StagingCleanupResult(
                succeeded=False,
                status="failed",
                path=partial_path,
                failure_code="delete_failed",
                message=f"Could not inspect canonical staging artifact: {error}",
            )
        if _is_reparse_point(path_stat) or not stat.S_ISREG(path_stat.st_mode):
            return StagingCleanupResult(
                succeeded=False,
                status="failed",
                path=partial_path,
                failure_code="model_invalid_path",
                message="Canonical staging artifact is not a regular non-reparse file.",
            )
        try:
            partial_path.unlink()
        except OSError as error:
            return StagingCleanupResult(
                succeeded=False,
                status="failed",
                path=partial_path,
                failure_code="delete_failed",
                message=f"Could not delete canonical staging artifact: {error}",
            )
        return StagingCleanupResult(
            succeeded=True,
            status="cleaned",
            path=partial_path,
            failure_code=None,
            message="Canonical staging artifact was deleted.",
        )

    def promote_verified_staging(self, model_key: str) -> VerifiedWhisperCheckpoint | StoreFailure:
        spec, paths, failure = self._resolve_model_paths(model_key)
        if failure is not None:
            return failure
        assert spec is not None
        assert paths is not None
        root, final_path, partial_path = paths
        if not _path_exists_or_link(partial_path):
            return StoreFailure(
                failure_code="model_missing",
                message="Canonical staging artifact is missing.",
                model_key=model_key,
                artifact_status=ARTIFACT_MISSING,
                path=partial_path,
            )

        inspection = _inspect_file(partial_path, allow_partial=True)
        validation_failure = self._inspection_failure(
            model_key=model_key,
            path=partial_path,
            spec=spec,
            inspection=inspection,
        )
        if validation_failure is not None:
            cleanup = self.discard_staging(model_key)
            return StoreFailure(
                failure_code=validation_failure.failure_code,
                message=self._with_cleanup_message(validation_failure.message, cleanup),
                model_key=model_key,
                artifact_status=validation_failure.artifact_status,
                path=partial_path,
                actual_size_bytes=validation_failure.actual_size_bytes,
                observed_sha256=validation_failure.observed_sha256,
            )

        assert inspection.final_path_stat is not None
        try:
            current_partial_stat = os.lstat(partial_path)
        except OSError as error:
            cleanup = self.discard_staging(model_key)
            return StoreFailure(
                failure_code="model_changed_during_verification",
                message=self._with_cleanup_message(
                    f"Canonical staging artifact changed before promote: {error}", cleanup
                ),
                model_key=model_key,
                artifact_status=ARTIFACT_READ_FAILED,
                path=partial_path,
            )
        if not _same_file_snapshot(inspection.final_path_stat, current_partial_stat):
            cleanup = self.discard_staging(model_key)
            return StoreFailure(
                failure_code="model_changed_during_verification",
                message=self._with_cleanup_message(
                    "Canonical staging artifact changed before promote.", cleanup
                ),
                model_key=model_key,
                artifact_status=ARTIFACT_READ_FAILED,
                path=partial_path,
            )

        if _path_exists_or_link(final_path):
            try:
                final_stat = os.lstat(final_path)
            except OSError as error:
                cleanup = self.discard_staging(model_key)
                return StoreFailure(
                    failure_code="model_promote_failed",
                    message=self._with_cleanup_message(
                        f"Could not inspect existing final artifact: {error}", cleanup
                    ),
                    model_key=model_key,
                    artifact_status=ARTIFACT_INVALID_PATH,
                    path=final_path,
                )
            if _is_reparse_point(final_stat) or not stat.S_ISREG(final_stat.st_mode):
                cleanup = self.discard_staging(model_key)
                return StoreFailure(
                    failure_code="model_promote_failed",
                    message=self._with_cleanup_message(
                        "Existing final artifact is not a regular non-reparse file.", cleanup
                    ),
                    model_key=model_key,
                    artifact_status=ARTIFACT_INVALID_PATH,
                    path=final_path,
                )

        try:
            os.replace(partial_path, final_path)
        except OSError as error:
            cleanup = self.discard_staging(model_key)
            return StoreFailure(
                failure_code="model_promote_failed",
                message=self._with_cleanup_message(f"Atomic model promote failed: {error}", cleanup),
                model_key=model_key,
                artifact_status=ARTIFACT_READ_FAILED,
                path=final_path,
            )

        availability = self.scan(model_key)
        if availability.verified_checkpoint is not None:
            return availability.verified_checkpoint
        return StoreFailure(
            failure_code="model_promote_failed",
            message=f"Post-promote verification failed: {availability.message}",
            model_key=model_key,
            artifact_status=availability.artifact_status,
            path=final_path,
            actual_size_bytes=availability.actual_size_bytes,
            observed_sha256=availability.observed_sha256,
        )

    def delete_model(
        self,
        model_key: str,
        permit: OwnershipReleasePermit | None,
    ) -> DeleteResult:
        spec, paths, failure = self._resolve_model_paths(model_key)
        if failure is not None or paths is None or spec is None:
            return DeleteResult(
                succeeded=False,
                status="failed",
                file_path=paths[1] if paths is not None else None,
                availability=None,
                failure_code=failure.failure_code if failure is not None else "storage_path_invalid",
                message=failure.message if failure is not None else "Could not resolve model path.",
            )
        root, final_path, _ = paths
        target_id = _artifact_id(final_path)
        if type(permit) is not OwnershipReleasePermit or not permit._consume_for(
            model_key=model_key,
            manifest_identity=self.catalog.manifest_identity(model_key),
            artifact_id=target_id,
        ):
            return DeleteResult(
                succeeded=False,
                status="blocked",
                file_path=final_path,
                availability=self.scan(model_key),
                failure_code="delete_blocked_ownership",
                message="Model ownership release permit is missing, invalid, mismatched, or already consumed.",
            )

        if not _path_exists_or_link(final_path):
            availability = self.scan(model_key)
            return DeleteResult(
                succeeded=True,
                status="missing",
                file_path=final_path,
                availability=availability,
                failure_code=None,
                message="Model artifact was already absent.",
            )
        try:
            path_stat = os.lstat(final_path)
        except OSError as error:
            return DeleteResult(
                succeeded=False,
                status="failed",
                file_path=final_path,
                availability=None,
                failure_code="delete_failed",
                message=f"Could not inspect model artifact before delete: {error}",
            )
        if _is_reparse_point(path_stat) or not stat.S_ISREG(path_stat.st_mode):
            return DeleteResult(
                succeeded=False,
                status="failed",
                file_path=final_path,
                availability=self.scan(model_key),
                failure_code="delete_failed",
                message="Model artifact is not a regular non-reparse file.",
            )
        try:
            final_path.unlink()
        except OSError as error:
            return DeleteResult(
                succeeded=False,
                status="failed",
                file_path=final_path,
                availability=self.scan(model_key),
                failure_code="delete_failed",
                message=f"Could not delete model artifact: {error}",
            )
        availability = self.scan(model_key)
        return DeleteResult(
            succeeded=True,
            status="deleted",
            file_path=final_path,
            availability=availability,
            failure_code=None,
            message="Model artifact was deleted.",
        )

    def _resolve_model_paths(
        self,
        model_key: str,
    ) -> tuple[WhisperModelSpec | None, tuple[Path, Path, Path] | None, StoreFailure | None]:
        try:
            spec = self.catalog.get(model_key)
        except Exception as error:
            return (
                None,
                None,
                StoreFailure(
                    failure_code="model_key_unsupported",
                    message=str(error),
                    model_key=model_key,
                    artifact_status=ARTIFACT_UNSUPPORTED,
                ),
            )
        root_resolution = _validate_storage_root(self._configured_root, used_default=False)
        if not root_resolution.succeeded or root_resolution.resolved_path is None:
            return (
                spec,
                None,
                StoreFailure(
                    failure_code=root_resolution.failure_code or "storage_path_invalid",
                    message=root_resolution.message or "Whisper model storage path is invalid.",
                    model_key=model_key,
                    artifact_status=ARTIFACT_INVALID_PATH,
                ),
            )
        root = root_resolution.resolved_path
        if not _is_safe_manifest_filename(spec.filename):
            return (
                spec,
                None,
                StoreFailure(
                    failure_code="model_invalid_path",
                    message="Manifest filename is not a canonical single filename.",
                    model_key=model_key,
                    artifact_status=ARTIFACT_INVALID_PATH,
                ),
            )
        final_path = root / spec.filename
        partial_path = root / f"{spec.filename}.part"
        return spec, (root, final_path, partial_path), None

    def _availability_for_failure(
        self,
        model_key: str,
        spec: WhisperModelSpec | None,
        paths: tuple[Path, Path, Path] | None,
        failure: StoreFailure,
    ) -> ModelAvailability:
        root = paths[0] if paths is not None else self.storage_root
        final_path = paths[1] if paths is not None else None
        partial_path = paths[2] if paths is not None else None
        return self._availability(
            model_key=model_key,
            spec=spec,
            root=root,
            final_path=final_path,
            partial_path=partial_path,
            partial_present=_path_exists_or_link(partial_path) if partial_path is not None else False,
            artifact_status=failure.artifact_status or ARTIFACT_INVALID_PATH,
            failure_code=failure.failure_code,
            actual_size_bytes=failure.actual_size_bytes,
            observed_sha256=failure.observed_sha256,
            message=failure.message,
        )

    def _availability(
        self,
        *,
        model_key: str,
        spec: WhisperModelSpec | None,
        root: Path,
        final_path: Path | None,
        partial_path: Path | None,
        partial_present: bool,
        artifact_status: str,
        failure_code: str | None,
        actual_size_bytes: int | None = None,
        observed_sha256: str | None = None,
        verified_checkpoint: VerifiedWhisperCheckpoint | None = None,
        message: str = "",
    ) -> ModelAvailability:
        manifest_identity = None
        if spec is not None:
            manifest_identity = self.catalog.manifest_identity(spec.model_key)
        return ModelAvailability(
            model_key=model_key,
            artifact_status=artifact_status,
            manifest_identity=manifest_identity,
            storage_root=root,
            file_path=final_path,
            partial_path=partial_path,
            partial_present=partial_present,
            actual_size_bytes=actual_size_bytes,
            observed_sha256=observed_sha256,
            failure_code=failure_code,
            verified_checkpoint=verified_checkpoint,
            message=message,
        )

    def _preflight_failure(
        self,
        model_key: str,
        paths: tuple[Path, Path, Path] | None,
        failure: StoreFailure,
    ) -> StoragePreflight:
        root = paths[0] if paths is not None else self.storage_root
        staging = paths[2] if paths is not None else None
        return StoragePreflight(
            succeeded=False,
            model_key=model_key,
            storage_root=root,
            staging_path=staging,
            required_bytes=None,
            free_bytes=None,
            failure_code=failure.failure_code,
            message=failure.message,
        )

    @staticmethod
    def _inspection_failure(
        *,
        model_key: str,
        path: Path,
        spec: WhisperModelSpec,
        inspection: _FileInspection,
    ) -> StoreFailure | None:
        if inspection.status == "missing":
            return StoreFailure(
                failure_code="model_missing",
                message="Canonical staging artifact is missing.",
                model_key=model_key,
                artifact_status=ARTIFACT_MISSING,
                path=path,
            )
        if inspection.status == "invalid_path":
            return StoreFailure(
                failure_code="model_invalid_path",
                message=inspection.message,
                model_key=model_key,
                artifact_status=ARTIFACT_INVALID_PATH,
                path=path,
            )
        if inspection.status == "changed":
            return StoreFailure(
                failure_code="model_changed_during_verification",
                message=inspection.message,
                model_key=model_key,
                artifact_status=ARTIFACT_READ_FAILED,
                path=path,
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
            )
        if inspection.status == "read_failed":
            return StoreFailure(
                failure_code="model_read_failed",
                message=inspection.message,
                model_key=model_key,
                artifact_status=ARTIFACT_READ_FAILED,
                path=path,
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
            )
        if inspection.actual_size_bytes != spec.size_bytes:
            return StoreFailure(
                failure_code="model_size_mismatch",
                message="Staging artifact size does not match the manifest.",
                model_key=model_key,
                artifact_status=ARTIFACT_INVALID_SIZE,
                path=path,
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
            )
        if inspection.observed_sha256 != spec.sha256:
            return StoreFailure(
                failure_code="model_sha256_mismatch",
                message="Staging artifact SHA256 does not match the manifest.",
                model_key=model_key,
                artifact_status=ARTIFACT_INVALID_SHA256,
                path=path,
                actual_size_bytes=inspection.actual_size_bytes,
                observed_sha256=inspection.observed_sha256,
            )
        return None

    @staticmethod
    def _with_cleanup_message(message: str, cleanup: StagingCleanupResult) -> str:
        if cleanup.succeeded:
            return f"{message} Staging cleanup: {cleanup.status}."
        return f"{message} Staging cleanup failed: {cleanup.message}"


def _validate_storage_root(path: Path, *, used_default: bool) -> StorageRootResolution:
    try:
        normalized = Path(os.path.abspath(path))
    except (OSError, TypeError, ValueError) as error:
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message=f"Whisper model storage path is invalid: {error}",
            used_default=used_default,
        )
    if not _is_absolute_windows_path(str(path), normalized):
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message="Whisper model storage path must be absolute.",
            used_default=used_default,
        )
    if _looks_like_remote_or_device_path(str(path)):
        failure_code = "storage_path_remote" if _looks_like_remote_path(str(path)) else "storage_path_invalid"
        return StorageRootResolution(
            resolved_path=None,
            failure_code=failure_code,
            message="Whisper model storage path is not a permitted local path.",
            used_default=used_default,
        )
    component_failure = _validate_existing_components(normalized)
    if component_failure is not None:
        return StorageRootResolution(
            resolved_path=None,
            failure_code=component_failure[0],
            message=component_failure[1],
            used_default=used_default,
        )
    try:
        canonical = normalized.resolve(strict=False)
    except OSError as error:
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message=f"Could not canonicalize Whisper model storage path: {error}",
            used_default=used_default,
        )
    if canonical.exists() and not canonical.is_dir():
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message="Whisper model storage root is not a directory.",
            used_default=used_default,
        )
    drive_type = _get_drive_type(canonical)
    if drive_type == _DRIVE_REMOTE:
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_remote",
            message="Network drives are not permitted for Whisper model storage.",
            used_default=used_default,
        )
    if drive_type not in (_DRIVE_FIXED, _DRIVE_REMOVABLE):
        return StorageRootResolution(
            resolved_path=None,
            failure_code="storage_path_invalid",
            message="Whisper model storage must be on a local fixed or removable drive.",
            used_default=used_default,
        )
    return StorageRootResolution(
        resolved_path=canonical,
        failure_code=None,
        message=None,
        used_default=used_default,
    )


def _validate_existing_components(path: Path) -> tuple[str, str] | None:
    parts = path.parts
    if not parts:
        return ("storage_path_invalid", "Whisper model storage path has no root.")
    current = Path(parts[0])
    try:
        current_stat = os.lstat(current)
    except OSError as error:
        return ("storage_path_invalid", f"Could not inspect storage path root: {error}")
    if _is_reparse_point(current_stat) or current.is_symlink():
        return ("storage_path_invalid", "Whisper model storage path contains a reparse point or symlink.")
    for component in parts[1:]:
        current = current / component
        try:
            current_stat = os.lstat(current)
        except FileNotFoundError:
            break
        except OSError as error:
            return ("storage_path_invalid", f"Could not inspect storage path component: {error}")
        if _is_reparse_point(current_stat) or current.is_symlink():
            return ("storage_path_invalid", "Whisper model storage path contains a reparse point or symlink.")
    return None


def _get_drive_type(path: Path) -> int:
    if os.name != "nt":
        return _DRIVE_FIXED
    try:
        return int(ctypes.windll.kernel32.GetDriveTypeW(str(path.anchor)))
    except (AttributeError, OSError, TypeError, ValueError):
        return _DRIVE_UNKNOWN


def _is_absolute_windows_path(raw_value: str, path: Path) -> bool:
    try:
        windows_path = PureWindowsPath(raw_value)
        return path.is_absolute() and windows_path.is_absolute()
    except (TypeError, ValueError):
        return False


def _looks_like_remote_or_device_path(raw_value: str) -> bool:
    normalized = raw_value.replace("/", "\\")
    lowered = normalized.lower()
    return normalized.startswith("\\\\") or lowered.startswith("\\\\?\\") or lowered.startswith("\\\\.\\")


def _looks_like_remote_path(raw_value: str) -> bool:
    normalized = raw_value.replace("/", "\\")
    lowered = normalized.lower()
    return normalized.startswith("\\\\") and not lowered.startswith(("\\\\?\\", "\\\\.\\"))


def _is_safe_manifest_filename(filename: str) -> bool:
    if not filename or filename in {".", ".."}:
        return False
    if "/" in filename or "\\" in filename:
        return False
    return Path(filename).name == filename


def _path_exists_or_link(path: Path | None) -> bool:
    if path is None:
        return False
    try:
        return path.exists() or path.is_symlink()
    except OSError:
        return True


def _validate_staging_destination(path: Path) -> tuple[str, str] | None:
    if not _path_exists_or_link(path):
        return None
    try:
        path_stat = os.lstat(path)
    except OSError as error:
        return ("model_invalid_path", f"Could not inspect canonical staging destination: {error}")
    if _is_reparse_point(path_stat) or not stat.S_ISREG(path_stat.st_mode):
        return (
            "model_invalid_path",
            "Canonical staging destination is not a regular non-reparse file.",
        )
    return None


def _is_reparse_point(path_stat: os.stat_result) -> bool:
    return bool(getattr(path_stat, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT)


def _inspect_file(path: Path, *, allow_partial: bool) -> _FileInspection:
    try:
        before_path_stat = os.lstat(path)
    except FileNotFoundError:
        return _FileInspection("missing", None, "File is missing.")
    except OSError as error:
        return _FileInspection("read_failed", "model_read_failed", f"Could not inspect file: {error}")

    if (not allow_partial and path.name.lower().endswith(".part")) or _is_reparse_point(before_path_stat):
        return _FileInspection("invalid_path", "model_invalid_path", "File is a partial or reparse path.")
    if not stat.S_ISREG(before_path_stat.st_mode):
        return _FileInspection("invalid_path", "model_invalid_path", "File is not a regular file.")

    digest = hashlib.sha256()
    actual_size = 0
    before_fd_stat: os.stat_result | None = None
    after_fd_stat: os.stat_result | None = None
    try:
        with path.open("rb") as stream:
            before_fd_stat = os.fstat(stream.fileno())
            if not _same_file_identity(before_path_stat, before_fd_stat):
                return _FileInspection(
                    "changed",
                    "model_changed_during_verification",
                    "File identity changed before reading.",
                )
            while True:
                chunk = stream.read(CHECKPOINT_CHUNK_SIZE)
                if not chunk:
                    break
                actual_size += len(chunk)
                digest.update(chunk)
            after_fd_stat = os.fstat(stream.fileno())
        after_path_stat = os.lstat(path)
    except FileNotFoundError:
        return _FileInspection(
            "changed",
            "model_changed_during_verification",
            "File disappeared during verification.",
            actual_size_bytes=actual_size,
            observed_sha256=digest.hexdigest(),
        )
    except OSError as error:
        return _FileInspection(
            "read_failed",
            "model_read_failed",
            f"Could not read file: {error}",
            actual_size_bytes=actual_size,
            observed_sha256=digest.hexdigest() if actual_size else None,
        )

    if before_fd_stat is None or after_fd_stat is None or not _same_file_snapshot(before_fd_stat, after_fd_stat):
        return _FileInspection(
            "changed",
            "model_changed_during_verification",
            "File identity or metadata changed during verification.",
            actual_size_bytes=actual_size,
            observed_sha256=digest.hexdigest(),
            final_path_stat=after_path_stat,
        )
    if not _same_file_snapshot(after_fd_stat, after_path_stat):
        return _FileInspection(
            "changed",
            "model_changed_during_verification",
            "File identity or metadata changed after verification.",
            actual_size_bytes=actual_size,
            observed_sha256=digest.hexdigest(),
            final_path_stat=after_path_stat,
        )
    return _FileInspection(
        "valid",
        None,
        "File verification completed.",
        actual_size_bytes=actual_size,
        observed_sha256=digest.hexdigest(),
        final_path_stat=after_path_stat,
    )


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


def _artifact_id(path: Path) -> str:
    return str(path.resolve(strict=False))


__all__ = [
    "ARTIFACT_INVALID_PATH",
    "ARTIFACT_INVALID_SHA256",
    "ARTIFACT_INVALID_SIZE",
    "ARTIFACT_MISSING",
    "ARTIFACT_PARTIAL",
    "ARTIFACT_READ_FAILED",
    "ARTIFACT_UNSUPPORTED",
    "ARTIFACT_VERIFIED",
    "DeleteResult",
    "FREE_SPACE_RESERVE_BYTES",
    "ModelAvailability",
    "OwnershipReleasePermit",
    "StagingCleanupResult",
    "StoragePreflight",
    "StorageRootResolution",
    "StoreFailure",
    "WhisperModelStore",
    "WhisperModelStoreError",
    "default_whisper_models_dir",
    "resolve_whisper_models_dir",
]
