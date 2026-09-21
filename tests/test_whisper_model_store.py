from __future__ import annotations

import hashlib
import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core.whisper_model_store import (
    ARTIFACT_INVALID_PATH,
    ARTIFACT_INVALID_SHA256,
    ARTIFACT_INVALID_SIZE,
    ARTIFACT_MISSING,
    ARTIFACT_PARTIAL,
    ARTIFACT_VERIFIED,
    FREE_SPACE_RESERVE_BYTES,
    OwnershipReleasePermit,
    WhisperModelStore,
    _issue_ownership_release_permit_for_testing,
    default_whisper_models_dir,
    resolve_whisper_models_dir,
)
from src.core.whisper_models import WhisperModelCatalog, WhisperModelSpec


class _StoreFixture:
    content = b"verified fake Whisper model bytes"

    @classmethod
    def catalog(cls) -> WhisperModelCatalog:
        sha256 = hashlib.sha256(cls.content).hexdigest()
        spec = WhisperModelSpec(
            model_key="small",
            display_name="Whisper small",
            multilingual=True,
            japanese_supported=True,
            official_url=(
                "https://openaipublic.azureedge.net/main/whisper/models/"
                f"{sha256}/small.pt"
            ),
            filename="small.pt",
            sha256=sha256,
            size_bytes=len(cls.content),
            vram_hint="test",
            speed_hint="test",
            recommended_use="test",
        )
        return WhisperModelCatalog(
            schema_version=1,
            openai_whisper_version="20250625",
            default_model_key="small",
            models=(spec,),
        )


class WhisperModelStoreTests(unittest.TestCase):
    def _store(self, root: Path) -> WhisperModelStore:
        return WhisperModelStore(root, catalog=_StoreFixture.catalog())

    def test_default_root_is_absolute_models_directory_without_creation(self) -> None:
        resolution = resolve_whisper_models_dir("")

        self.assertTrue(resolution.succeeded)
        self.assertTrue(resolution.used_default)
        self.assertEqual(resolution.resolved_path, default_whisper_models_dir())
        self.assertTrue(resolution.resolved_path.is_absolute())
        self.assertEqual(resolution.resolved_path.name, "models")

    def test_frozen_default_root_is_executable_adjacent_and_not_meipass(self) -> None:
        with patch.object(sys, "frozen", True, create=True), patch.object(
            sys,
            "executable",
            r"C:\Program Files\MMD AutoLipTool\MMD_AutoLipTool.exe",
        ), patch.object(sys, "_MEIPASS", r"C:\Temp\_MEI123", create=True):
            root = default_whisper_models_dir()

        self.assertEqual(root, Path(r"C:\Program Files\MMD AutoLipTool\models"))
        self.assertNotIn("_MEI", str(root))

    def test_invalid_remote_relative_url_and_device_paths_fail_closed(self) -> None:
        cases = (
            ("relative-models", "storage_path_invalid"),
            (r"\\server\share\models", "storage_path_remote"),
            ("https://example.invalid/models", "storage_path_invalid"),
            (r"\\?\C:\models", "storage_path_invalid"),
            (r"\\.\C:\models", "storage_path_invalid"),
        )
        for value, expected_code in cases:
            with self.subTest(value=value):
                resolution = resolve_whisper_models_dir(value)
                self.assertFalse(resolution.succeeded)
                self.assertEqual(resolution.failure_code, expected_code)

    def test_scan_missing_does_not_create_storage_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "missing-models"
            store = self._store(root)

            availability = store.scan("small")

        self.assertEqual(availability.artifact_status, ARTIFACT_MISSING)
        self.assertFalse(root.exists())

    def test_scan_partial_verified_and_stale_partial_are_separate_axes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            partial_path = store.staging_path("small")
            partial_path.write_bytes(_StoreFixture.content[:5])
            partial = store.scan("small")
            final_path = root / "small.pt"
            final_path.write_bytes(_StoreFixture.content)
            verified = store.scan("small")

        self.assertEqual(partial.artifact_status, ARTIFACT_PARTIAL)
        self.assertTrue(partial.partial_present)
        self.assertIsNone(partial.verified_checkpoint)
        self.assertEqual(verified.artifact_status, ARTIFACT_VERIFIED)
        self.assertTrue(verified.partial_present)
        self.assertIsNotNone(verified.verified_checkpoint)
        self.assertEqual(verified.verified_checkpoint.checkpoint_path, final_path)

    def test_invalid_size_and_sha256_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            final_path = root / "small.pt"
            final_path.write_bytes(b"short")
            invalid_size = store.scan("small")
            final_path.write_bytes(b"X" * len(_StoreFixture.content))
            invalid_sha = store.scan("small")

        self.assertEqual(invalid_size.artifact_status, ARTIFACT_INVALID_SIZE)
        self.assertEqual(invalid_size.failure_code, "model_size_mismatch")
        self.assertEqual(invalid_sha.artifact_status, ARTIFACT_INVALID_SHA256)
        self.assertEqual(invalid_sha.failure_code, "model_sha256_mismatch")

    def test_read_failure_and_identity_change_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            final_path = root / "small.pt"
            final_path.write_bytes(_StoreFixture.content)
            with patch.object(Path, "open", side_effect=PermissionError("denied")):
                read_failure = store.scan("small")

            replacement = root / "replacement.pt"
            replacement.write_bytes(b"replacement")
            original_open = Path.open

            def open_and_replace(path: Path, *args: object, **kwargs: object):
                stream = original_open(path, *args, **kwargs)
                os.replace(replacement, final_path)
                return stream

            with patch.object(Path, "open", side_effect=open_and_replace):
                identity_change = store.scan("small")

        self.assertEqual(read_failure.artifact_status, "read_failed")
        self.assertEqual(read_failure.failure_code, "model_read_failed")
        self.assertEqual(identity_change.artifact_status, "read_failed")
        self.assertEqual(identity_change.failure_code, "model_changed_during_verification")

    def test_directory_and_symlink_final_artifacts_are_not_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            final_path = root / "small.pt"
            final_path.mkdir()
            directory_result = store.scan("small")
            final_path.rmdir()

            target = root / "target.pt"
            target.write_bytes(_StoreFixture.content)
            try:
                os.symlink(target, final_path)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            symlink_result = store.scan("small")

        self.assertEqual(directory_result.artifact_status, ARTIFACT_INVALID_PATH)
        self.assertEqual(symlink_result.artifact_status, ARTIFACT_INVALID_PATH)
        self.assertIsNone(symlink_result.verified_checkpoint)

    def test_symlink_storage_root_is_rejected_before_drive_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            target = base / "target"
            target.mkdir()
            linked_root = base / "linked"
            try:
                os.symlink(target, linked_root, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")

            resolution = resolve_whisper_models_dir(str(linked_root))

        self.assertFalse(resolution.succeeded)
        self.assertEqual(resolution.failure_code, "storage_path_invalid")

    def test_preflight_creates_root_checks_space_and_does_not_use_network(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "models"
            store = self._store(root)
            with patch("urllib.request.urlopen") as urlopen:
                result = store.preflight_download("small")
            root_exists = root.is_dir()
            remaining_files = list(root.iterdir())

        self.assertTrue(result.succeeded)
        self.assertTrue(root_exists)
        self.assertEqual(result.required_bytes, len(_StoreFixture.content) + FREE_SPACE_RESERVE_BYTES)
        self.assertIsNotNone(result.free_bytes)
        self.assertGreaterEqual(result.free_bytes, result.required_bytes)
        self.assertTrue(result.staging_path.name.endswith(".part"))
        urlopen.assert_not_called()
        self.assertEqual(remaining_files, [])

    def test_preflight_rejects_unknown_or_insufficient_free_space(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "models"
            store = self._store(root)
            with patch(
                "src.core.whisper_model_store.shutil.disk_usage",
                side_effect=OSError("unknown"),
            ):
                unknown = store.preflight_download("small")

            with patch(
                "src.core.whisper_model_store.shutil.disk_usage",
                return_value=SimpleNamespace(free=0),
            ):
                insufficient = store.preflight_download("small")

        self.assertFalse(unknown.succeeded)
        self.assertEqual(unknown.failure_code, "storage_free_space_unknown")
        self.assertFalse(insufficient.succeeded)
        self.assertEqual(insufficient.failure_code, "storage_free_space_insufficient")

    def test_preflight_rejects_non_regular_existing_staging_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            partial_path = store.staging_path("small")
            partial_path.mkdir()

            result = store.preflight_download("small")

        self.assertFalse(result.succeeded)
        self.assertEqual(result.failure_code, "model_invalid_path")

    def test_promote_is_model_key_only_and_revalidates_after_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            partial_path = store.staging_path("small")
            partial_path.write_bytes(_StoreFixture.content)

            parameters = inspect.signature(store.promote_verified_staging).parameters
            result = store.promote_verified_staging("small")

        self.assertEqual(tuple(parameters), ("model_key",))
        self.assertEqual(result.model_key, "small")
        self.assertEqual(result.checkpoint_path.name, "small.pt")
        self.assertFalse(partial_path.exists())

    def test_promote_failure_preserves_existing_final_and_cleans_canonical_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            final_path = root / "small.pt"
            partial_path = store.staging_path("small")
            final_path.write_bytes(b"old-final")
            partial_path.write_bytes(_StoreFixture.content)
            with patch("src.core.whisper_model_store.os.replace", side_effect=OSError("locked")):
                result = store.promote_verified_staging("small")

            final_bytes = final_path.read_bytes()

        self.assertEqual(result.failure_code, "model_promote_failed")
        self.assertEqual(final_bytes, b"old-final")
        self.assertFalse(partial_path.exists())

    def test_discard_staging_only_removes_canonical_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            partial_path = store.staging_path("small")
            partial_path.write_bytes(b"partial")
            outside_path = root.parent / "outside-partial.pt.part"
            outside_path.write_bytes(b"outside")
            result = store.discard_staging("small")

        self.assertTrue(result.succeeded)
        self.assertEqual(result.status, "cleaned")
        self.assertFalse(partial_path.exists())
        self.assertTrue(outside_path.exists())
        outside_path.unlink()

    def test_delete_requires_opaque_matching_single_use_permit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            final_path = root / "small.pt"
            final_path.write_bytes(_StoreFixture.content)
            availability = store.scan("small")
            self.assertIsNotNone(availability.file_path)
            self.assertIsNotNone(availability.manifest_identity)

            blocked = store.delete_model("small", None)
            shaped = SimpleNamespace()
            shaped_result = store.delete_model("small", shaped)  # type: ignore[arg-type]
            permit = _issue_ownership_release_permit_for_testing(
                model_key="small",
                manifest_identity=availability.manifest_identity,
                artifact_id=str(availability.file_path.resolve(strict=False)),
            )
            deleted = store.delete_model("small", permit)
            reused = store.delete_model("small", permit)

        self.assertFalse(blocked.succeeded)
        self.assertEqual(blocked.failure_code, "delete_blocked_ownership")
        self.assertFalse(shaped_result.succeeded)
        self.assertEqual(shaped_result.failure_code, "delete_blocked_ownership")
        self.assertIsInstance(permit, OwnershipReleasePermit)
        self.assertTrue(deleted.succeeded)
        self.assertEqual(deleted.availability.artifact_status, ARTIFACT_MISSING)
        self.assertFalse(final_path.exists())
        self.assertFalse(reused.succeeded)
        self.assertEqual(reused.failure_code, "delete_blocked_ownership")

    def test_delete_failure_consumes_valid_permit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = self._store(root)
            final_path = root / "small.pt"
            final_path.write_bytes(_StoreFixture.content)
            availability = store.scan("small")
            permit = _issue_ownership_release_permit_for_testing(
                model_key="small",
                manifest_identity=availability.manifest_identity,
                artifact_id=str(final_path.resolve(strict=False)),
            )
            with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
                failed = store.delete_model("small", permit)
            reused = store.delete_model("small", permit)

        self.assertFalse(failed.succeeded)
        self.assertEqual(failed.failure_code, "delete_failed")
        self.assertFalse(reused.succeeded)
        self.assertEqual(reused.failure_code, "delete_blocked_ownership")


if __name__ == "__main__":
    unittest.main()
