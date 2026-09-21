from __future__ import annotations

import hashlib
import tempfile
import threading
import unittest
from pathlib import Path

from src.core.whisper_model_downloader import DOWNLOAD_STATUS_CANCELLED
from src.core.whisper_model_store import (
    ARTIFACT_VERIFIED,
    WhisperModelStore,
    _issue_ownership_release_permit_for_testing,
)
from src.core.whisper_models import WhisperModelCatalog, WhisperModelSpec
from src.gui_wx.model_download_worker import (
    MODEL_MANAGEMENT_OPERATION_DELETE,
    MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
    MODEL_MANAGEMENT_STATUS_BLOCKED,
    MODEL_MANAGEMENT_STATUS_CANCELLED,
    MODEL_MANAGEMENT_STATUS_SUCCEEDED,
    ModelManagementResult,
    WhisperModelManagementWorker,
)


class _WorkerFixture:
    content = b"verified fake Whisper model bytes"

    @classmethod
    def catalog(cls) -> WhisperModelCatalog:
        digest = hashlib.sha256(cls.content).hexdigest()
        spec = WhisperModelSpec(
            model_key="small",
            display_name="Whisper small",
            multilingual=True,
            japanese_supported=True,
            official_url=(
                "https://openaipublic.azureedge.net/main/whisper/models/"
                f"{digest}/small.pt"
            ),
            filename="small.pt",
            sha256=digest,
            size_bytes=len(cls.content),
            vram_hint="test",
            speed_hint="test",
            recommended_use="test",
        )
        return WhisperModelCatalog(1, "20250625", "small", (spec,))


class _Response:
    status = 200

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.offset = 0
        self.headers = {"Content-Length": str(len(body))}

    def read(self, amount: int) -> bytes:
        chunk = self.body[self.offset : self.offset + amount]
        self.offset += len(chunk)
        return chunk

    def close(self) -> None:
        pass


class ModelDownloadWorkerTests(unittest.TestCase):
    def test_download_worker_dispatches_progress_and_one_terminal_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog = _WorkerFixture.catalog()
            store = WhisperModelStore(Path(temporary_directory), catalog=catalog)
            preflight = store.preflight_download("small")
            results: list[ModelManagementResult] = []
            progress = []
            worker = WhisperModelManagementWorker(
                job_id=7,
                operation=MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
                model_key="small",
                catalog=catalog,
                store=store,
                preflight=preflight,
                result_callback=results.append,
                progress_callback=progress.append,
                transport=lambda url, timeout: _Response(_WorkerFixture.content),
                call_after=lambda callback, *args: callback(*args),
            )
            worker.run()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, MODEL_MANAGEMENT_STATUS_SUCCEEDED)
            self.assertTrue(progress)

    def test_cancelled_download_returns_cancelled_terminal_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog = _WorkerFixture.catalog()
            store = WhisperModelStore(Path(temporary_directory), catalog=catalog)
            preflight = store.preflight_download("small")
            cancel_event = threading.Event()
            cancel_event.set()
            results: list[ModelManagementResult] = []
            worker = WhisperModelManagementWorker(
                job_id=8,
                operation=MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
                model_key="small",
                catalog=catalog,
                store=store,
                preflight=preflight,
                cancel_event=cancel_event,
                result_callback=results.append,
                call_after=lambda callback, *args: callback(*args),
            )
            worker.run()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, MODEL_MANAGEMENT_STATUS_CANCELLED)
            self.assertEqual(results[0].download_result.status, DOWNLOAD_STATUS_CANCELLED)

    def test_delete_without_provider_is_blocked_without_filesystem_delete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog = _WorkerFixture.catalog()
            root = Path(temporary_directory)
            store = WhisperModelStore(root, catalog=catalog)
            (root / "small.pt").write_bytes(_WorkerFixture.content)
            results: list[ModelManagementResult] = []
            worker = WhisperModelManagementWorker(
                job_id=9,
                operation=MODEL_MANAGEMENT_OPERATION_DELETE,
                model_key="small",
                catalog=catalog,
                store=store,
                result_callback=results.append,
                call_after=lambda callback, *args: callback(*args),
            )
            worker.run()

            self.assertEqual(results[0].status, MODEL_MANAGEMENT_STATUS_BLOCKED)
            self.assertTrue((root / "small.pt").exists())

    def test_delete_uses_opaque_permit_provider_and_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog = _WorkerFixture.catalog()
            root = Path(temporary_directory)
            store = WhisperModelStore(root, catalog=catalog)
            final_path = root / "small.pt"
            final_path.write_bytes(_WorkerFixture.content)
            self.assertEqual(store.scan("small").artifact_status, ARTIFACT_VERIFIED)
            permit = _issue_ownership_release_permit_for_testing(
                model_key="small",
                manifest_identity=catalog.manifest_identity("small"),
                artifact_id=str(final_path.resolve()),
            )
            results: list[ModelManagementResult] = []
            worker = WhisperModelManagementWorker(
                job_id=10,
                operation=MODEL_MANAGEMENT_OPERATION_DELETE,
                model_key="small",
                catalog=catalog,
                store=store,
                result_callback=results.append,
                ownership_provider=lambda model_key: permit,
                call_after=lambda callback, *args: callback(*args),
            )
            worker.run()

            self.assertEqual(results[0].status, MODEL_MANAGEMENT_STATUS_SUCCEEDED)
            self.assertFalse(final_path.exists())


if __name__ == "__main__":
    unittest.main()
