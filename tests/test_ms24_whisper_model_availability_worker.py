from __future__ import annotations

from src.core.whisper_model_store import WhisperModelStore
from src.gui_wx.whisper_availability_worker import WhisperAvailabilityWorker
from tests.helpers import workspace_tempdir


def test_worker_scans_local_store_without_creating_missing_root() -> None:
    with workspace_tempdir("ms24_b3_worker_root") as tmp_dir:
        model_root = (tmp_dir / "models").resolve()
        store = WhisperModelStore(model_root)
        results = []
        worker = WhisperAvailabilityWorker(
            job_id=11,
            scan_generation=7,
            store=store,
            result_callback=results.append,
            call_after=lambda callback, result: callback(result),
        )

        worker.run()

        assert worker.daemon is True
        assert len(results) == 1
        assert results[0].job_id == 11
        assert results[0].scan_generation == 7
        assert results[0].succeeded is True
        assert tuple(item.artifact_status for item in results[0].availability) == (
            "missing",
            "missing",
            "missing",
        )
        assert model_root.exists() is False


def test_worker_stabilizes_unexpected_scan_failure_without_ui_raw_message() -> None:
    class FailingStore:
        def scan_all(self):
            raise OSError("secret C:\\private\\models\\small.pt")

    results = []
    worker = WhisperAvailabilityWorker(
        job_id=12,
        scan_generation=8,
        store=FailingStore(),
        result_callback=results.append,
        call_after=lambda callback, result: callback(result),
    )

    worker.run()

    assert len(results) == 1
    assert results[0].succeeded is False
    assert results[0].failure_code == "availability_scan_failed"
    assert "secret C:\\private\\models\\small.pt" in results[0].failure_detail
