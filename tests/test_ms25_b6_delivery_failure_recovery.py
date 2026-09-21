from __future__ import annotations

import shutil
import threading

import pytest

import src.core.delivery_package as delivery_package
from src.core.delivery_package import (
    DeliveryCancelToken,
    DeliveryContractError,
    orchestrate_delivery_package,
)
from tests.test_ms25_b2_delivery_orchestration import (
    _authorized_guard,
    _context,
    _operations,
)


def _faulting_operations(failing_kind, error):
    def callback(kind, context, output_path, cancel_token):
        if kind == failing_kind:
            raise error
        output_path.write_bytes(kind.encode("ascii"))

    return _operations([], callback)


@pytest.mark.parametrize("failing_kind", ["vmd", "mmd_wav", "report"])
def test_permission_fault_is_classified_and_stops_at_failing_artifact(
    tmp_path,
    failing_kind,
):
    result = orchestrate_delivery_package(
        job_id=610 + ("vmd", "mmd_wav", "report").index(failing_kind),
        start_context=_context(tmp_path),
        artifact_operations=_faulting_operations(
            failing_kind,
            PermissionError("write denied"),
        ),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "output_permission_denied"
    assert result.artifact_phase == failing_kind
    assert result.cleanup_status == "completed"
    assert result.final_path is None
    assert not (tmp_path / "delivery").exists()


def test_non_os_commit_failure_keeps_generic_commit_code(tmp_path, monkeypatch):
    def fail_rename(staging_path, destination_path):
        raise RuntimeError("synthetic non-OS commit failure")

    monkeypatch.setattr(delivery_package.os, "rename", fail_rename)

    result = orchestrate_delivery_package(
        job_id=620,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "delivery_commit_failed"
    assert result.commit_phase == "commit_failed"
    assert result.cleanup_status == "completed"
    assert result.final_path is None
    assert not (tmp_path / "delivery").exists()


def test_commit_failure_is_not_reclassified_by_late_cancel(tmp_path, monkeypatch):
    cancel_token = DeliveryCancelToken()
    cancel_results = []
    cancel_threads = []

    def fail_rename(staging_path, destination_path):
        cancel_thread = threading.Thread(
            target=lambda: cancel_results.append(cancel_token.request_cancel())
        )
        cancel_threads.append(cancel_thread)
        cancel_thread.start()
        raise RuntimeError("commit failed after linearization")

    monkeypatch.setattr(delivery_package.os, "rename", fail_rename)

    result = orchestrate_delivery_package(
        job_id=621,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=cancel_token,
    )
    for cancel_thread in cancel_threads:
        cancel_thread.join(timeout=1.0)

    assert result.primary_status == "failed"
    assert result.primary_error_code == "delivery_commit_failed"
    assert result.primary_status != "cancelled"
    assert result.cleanup_status == "completed"
    assert cancel_results == [False]


def test_unexpected_exception_after_staging_owns_a_terminal_result(
    tmp_path,
    monkeypatch,
):
    def fail_contents(staging):
        raise RuntimeError("unexpected contents inspection failure")

    monkeypatch.setattr(delivery_package, "_validate_staging_contents", fail_contents)

    result = orchestrate_delivery_package(
        job_id=630,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "delivery_worker_failed"
    assert result.cleanup_status == "completed"
    assert result.final_path is None
    assert result.staging_path is None


def test_cleanup_unexpected_exception_becomes_partial_cleanup_failure(
    tmp_path,
    monkeypatch,
):
    def fail_cleanup(staging_path, parent_directory):
        raise RuntimeError("cleanup helper failed unexpectedly")

    def fail_vmd(kind, context, output_path, cancel_token):
        raise DeliveryContractError("vmd_write_failed", "synthetic writer failure")

    monkeypatch.setattr(delivery_package, "_cleanup_owned_staging", fail_cleanup)

    result = orchestrate_delivery_package(
        job_id=631,
        start_context=_context(tmp_path),
        artifact_operations=_operations([], fail_vmd),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "vmd_write_failed"
    assert result.cleanup_status == "partial_output_cleanup_failed"
    assert result.staging_path is not None
    assert result.staging_path.exists()


def test_primary_failure_is_preserved_when_cleanup_returns_false(
    tmp_path,
    monkeypatch,
):
    def fail_cleanup(staging_path, parent_directory):
        return False

    def fail_vmd(kind, context, output_path, cancel_token):
        raise DeliveryContractError("vmd_write_failed", "synthetic writer failure")

    monkeypatch.setattr(delivery_package, "_cleanup_owned_staging", fail_cleanup)

    result = orchestrate_delivery_package(
        job_id=632,
        start_context=_context(tmp_path),
        artifact_operations=_operations([], fail_vmd),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_error_code == "vmd_write_failed"
    assert result.cleanup_status == "partial_output_cleanup_failed"
    assert result.staging_path is not None
    assert result.staging_path.exists()


def test_replaced_staging_directory_is_rejected_and_not_deleted(
    tmp_path,
):
    replacement_marker = tmp_path / "replacement-marker.txt"
    replacement_marker.write_bytes(b"outside-marker")
    replacement_root = {}

    def replace_staging(kind, context, output_path, cancel_token):
        output_path.write_bytes(kind.encode("ascii"))
        if kind == "vmd":
            original_root = output_path.parent
            shutil.rmtree(original_root)
            original_root.mkdir()
            (original_root / "replacement.txt").write_bytes(b"replacement")
            replacement_root["path"] = original_root

    result = orchestrate_delivery_package(
        job_id=640,
        start_context=_context(tmp_path),
        artifact_operations=_operations([], replace_staging),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "output_staging_invalid"
    assert result.cleanup_status == "partial_output_cleanup_failed"
    assert result.staging_path == replacement_root["path"]
    assert (replacement_root["path"] / "replacement.txt").read_bytes() == b"replacement"
    assert replacement_marker.read_bytes() == b"outside-marker"


def test_missing_staging_is_treated_as_successful_cleanup(tmp_path):
    def remove_staging(kind, context, output_path, cancel_token):
        if kind == "vmd":
            shutil.rmtree(output_path.parent)

    result = orchestrate_delivery_package(
        job_id=641,
        start_context=_context(tmp_path),
        artifact_operations=_operations([], remove_staging),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "output_staging_invalid"
    assert result.cleanup_status == "completed"
    assert result.staging_path is None
