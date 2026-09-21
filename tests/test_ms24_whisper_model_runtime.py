import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core import (
    ModelIdentity,
    RuntimeCacheIdentity,
    VerifiedAnalysisModelRequest,
    WhisperModelRuntime,
    WhisperModelRuntimeError,
    build_verified_analysis_model_request,
    classify_whisper_failure,
)
from src.core.whisper_model_loader import (
    LoadedWhisperModel,
    VerifiedWhisperCheckpoint,
    WhisperModelLoaderError,
)
from src.core.whisper_model_store import ARTIFACT_VERIFIED, ModelAvailability
from src.core.whisper_models import load_whisper_model_catalog


class _FakeModel:
    def __init__(self, label: str) -> None:
        self.label = label
        self.to_calls: list[str] = []

    def to(self, device: str) -> None:
        self.to_calls.append(device)


class WhisperModelRuntimeTests(unittest.TestCase):
    @staticmethod
    def _request(model_key: str, root: str = "C:/models") -> VerifiedAnalysisModelRequest:
        manifest_identity = f"manifest-{model_key}"
        identity = ModelIdentity(model_key=model_key, manifest_identity=manifest_identity)
        checkpoint = VerifiedWhisperCheckpoint(
            model_key=model_key,
            checkpoint_path=Path(root) / f"{model_key}.pt",
            manifest_identity=manifest_identity,
            sha256="a" * 64,
            size_bytes=123,
        )
        return VerifiedAnalysisModelRequest(
            identity=identity,
            cache_identity=RuntimeCacheIdentity(
                model_key=model_key,
                canonical_storage_root=str(Path(root).resolve(strict=False)),
                manifest_identity=manifest_identity,
            ),
            verified_checkpoint=checkpoint,
        )

    def test_runtime_keeps_one_active_model_and_reuses_matching_session(self) -> None:
        loaded_models: list[_FakeModel] = []

        def loader(checkpoint, *, catalog):
            model = _FakeModel(checkpoint.model_key)
            loaded_models.append(model)
            return LoadedWhisperModel(
                model=model,
                model_key=checkpoint.model_key,
                manifest_identity=checkpoint.manifest_identity,
                sha256=checkpoint.sha256,
                size_bytes=checkpoint.size_bytes,
            )

        runtime = WhisperModelRuntime(catalog=load_whisper_model_catalog(), loader=loader)
        small_request = self._request("small")
        medium_request = self._request("medium")

        first = runtime.acquire(small_request)
        reused = runtime.acquire(small_request)
        self.assertIs(first, reused)
        self.assertEqual(len(loaded_models), 1)

        with self.assertRaises(WhisperModelRuntimeError) as context:
            runtime.acquire(medium_request)
        self.assertEqual(context.exception.code, "runtime_busy")
        self.assertEqual(context.exception.failure_class, "cancelled")

        runtime.release(first)
        runtime.release(reused)
        switched = runtime.acquire(medium_request)
        self.assertEqual(switched.identity.model_key, "medium")
        self.assertEqual(loaded_models[0].to_calls, ["cpu"])
        runtime.release(switched)
        self.assertTrue(runtime.unload())
        self.assertEqual(loaded_models[1].to_calls, ["cpu"])
        self.assertIsNone(runtime.active_session)

    def test_runtime_candidate_is_manager_owned_until_commit_or_reject(self) -> None:
        loaded_models: list[_FakeModel] = []

        def loader(checkpoint, *, catalog):
            model = _FakeModel(checkpoint.model_key)
            loaded_models.append(model)
            return LoadedWhisperModel(
                model=model,
                model_key=checkpoint.model_key,
                manifest_identity=checkpoint.manifest_identity,
                sha256=checkpoint.sha256,
                size_bytes=checkpoint.size_bytes,
            )

        runtime = WhisperModelRuntime(catalog=load_whisper_model_catalog(), loader=loader)
        runtime.acquire(self._request("small"))
        old_session = runtime.active_session
        self.assertIsNotNone(old_session)
        runtime.release(old_session)

        candidate = runtime.prepare_candidate(self._request("turbo"))
        self.assertIsNone(runtime.active_session)
        self.assertIs(runtime.candidate_session, candidate)
        self.assertEqual(loaded_models[0].to_calls, ["cpu"])

        committed = runtime.commit_candidate(candidate)
        self.assertIs(committed, candidate.session)
        self.assertIs(runtime.active_session, committed)
        self.assertIsNone(runtime.candidate_session)

        runtime.release(committed)
        self.assertTrue(runtime.unload())
        self.assertEqual(loaded_models[1].to_calls, ["cpu"])

        rejected = runtime.prepare_candidate(self._request("small"))
        runtime.reject_candidate(rejected)
        self.assertEqual(loaded_models[2].to_calls, ["cpu"])
        with self.assertRaises(WhisperModelRuntimeError) as context:
            runtime.reject_candidate(rejected)
        self.assertEqual(context.exception.code, "candidate_stale")

    def test_runtime_does_not_unload_or_switch_while_a_lease_is_active(self) -> None:
        loader = Mock()
        model = _FakeModel("small")
        request = self._request("small")
        loader.return_value = LoadedWhisperModel(
            model=model,
            model_key="small",
            manifest_identity="manifest-small",
            sha256="a" * 64,
            size_bytes=123,
        )
        runtime = WhisperModelRuntime(catalog=load_whisper_model_catalog(), loader=loader)
        session = runtime.acquire(request)

        self.assertFalse(runtime.unload())
        self.assertIs(runtime.active_session, session)
        with self.assertRaises(WhisperModelRuntimeError) as context:
            runtime.prepare_candidate(self._request("medium"))
        self.assertEqual(context.exception.code, "runtime_busy")
        self.assertEqual(model.to_calls, [])

        runtime.release(session)
        self.assertEqual(model.to_calls, ["cpu"])

    def test_loader_failures_preserve_detail_and_upper_failure_class(self) -> None:
        def loader(checkpoint, *, catalog):
            raise WhisperModelLoaderError("whisper_version_mismatch", "wrong package")

        runtime = WhisperModelRuntime(catalog=load_whisper_model_catalog(), loader=loader)
        with self.assertRaises(WhisperModelRuntimeError) as context:
            runtime.acquire(self._request("small"))
        self.assertEqual(context.exception.code, "whisper_version_mismatch")
        self.assertEqual(context.exception.failure_class, "load_failure")

        def unknown_loader(checkpoint, *, catalog):
            raise RuntimeError("device setup failed")

        unknown_runtime = WhisperModelRuntime(
            catalog=load_whisper_model_catalog(),
            loader=unknown_loader,
        )
        with self.assertRaises(WhisperModelRuntimeError) as unknown_context:
            unknown_runtime.acquire(self._request("small"))
        self.assertEqual(unknown_context.exception.failure_class, "load_failure")

        try:
            try:
                raise MemoryError("CUDA out of memory")
            except MemoryError as cause:
                raise WhisperModelLoaderError("checkpoint_bytes_load_failed", "checkpoint load failed") from cause
        except WhisperModelLoaderError as error:
            self.assertEqual(classify_whisper_failure(error), ("memory_failure", "checkpoint_bytes_load_failed"))

    def test_verified_request_uses_availability_identity_and_canonical_root(self) -> None:
        checkpoint = VerifiedWhisperCheckpoint(
            model_key="small",
            checkpoint_path=Path("C:/models/small.pt"),
            manifest_identity="manifest-small",
            sha256="a" * 64,
            size_bytes=123,
        )
        availability = ModelAvailability(
            model_key="small",
            artifact_status=ARTIFACT_VERIFIED,
            manifest_identity="manifest-small",
            storage_root=Path("C:/models/../models"),
            file_path=checkpoint.checkpoint_path,
            partial_path=None,
            partial_present=False,
            actual_size_bytes=123,
            observed_sha256="a" * 64,
            failure_code=None,
            verified_checkpoint=checkpoint,
        )

        request = build_verified_analysis_model_request(availability)
        self.assertEqual(request.identity.model_key, "small")
        self.assertEqual(request.identity.manifest_identity, "manifest-small")
        self.assertEqual(
            request.cache_identity.canonical_storage_root,
            str(Path("C:/models").resolve(strict=False)),
        )

    def test_runtime_owns_the_production_delete_permit_issuer(self) -> None:
        runtime = WhisperModelRuntime(catalog=load_whisper_model_catalog(), loader=Mock())
        permit = runtime.issue_ownership_release_permit(
            model_key="small",
            manifest_identity="manifest-small",
            artifact_id="artifact-small",
        )
        self.assertTrue(
            permit._consume_for(
                model_key="small",
                manifest_identity="manifest-small",
                artifact_id="artifact-small",
            )
        )
        self.assertFalse(
            permit._consume_for(
                model_key="small",
                manifest_identity="manifest-small",
                artifact_id="artifact-small",
            )
        )


if __name__ == "__main__":
    unittest.main()
