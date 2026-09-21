import os
from pathlib import Path
import threading

import pytest

import src.core.delivery_package as delivery_package
from src.core.delivery_package import (
    DeliveryCancelToken,
    DeliveryCommitAuthorization,
    DeliveryTerminalResult,
    orchestrate_delivery_package,
)
from tests.test_ms25_b2_delivery_orchestration import (
    _authorized_guard,
    _context,
    _operations,
)


def test_guard_receives_exact_job_fingerprint_and_final_path_once(tmp_path):
    calls = []
    context = _context(tmp_path)
    final_path = tmp_path / "delivery"

    def guard(request, cancel_token):
        calls.append((request, cancel_token))
        return DeliveryCommitAuthorization(
            job_id=request.job_id,
            start_fingerprint=request.start_fingerprint,
            decision="authorized",
        )

    result = orchestrate_delivery_package(
        job_id=31,
        start_context=context,
        artifact_operations=_operations([]),
        pre_commit_guard=guard,
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "success"
    assert len(calls) == 1
    request, token = calls[0]
    assert request.job_id == 31
    assert request.start_fingerprint == context.current_state.start_fingerprint
    assert request.final_directory == final_path
    assert token.phase == "committed"


@pytest.mark.parametrize("mismatch", ["job", "fingerprint"])
def test_authorization_identity_mismatch_fails_closed(tmp_path, mismatch):
    context = _context(tmp_path)

    def guard(request, cancel_token):
        return DeliveryCommitAuthorization(
            job_id=request.job_id + 1 if mismatch == "job" else request.job_id,
            start_fingerprint=(
                "sha256:mismatch"
                if mismatch == "fingerprint"
                else request.start_fingerprint
            ),
            decision="authorized",
        )

    result = orchestrate_delivery_package(
        job_id=32,
        start_context=context,
        artifact_operations=_operations([]),
        pre_commit_guard=guard,
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "delivery_commit_authorization_invalid"
    assert result.committed is False
    assert result.final_path is None
    assert result.cleanup_status == "completed"


def test_cancel_during_guard_prevents_commit(tmp_path):
    token = DeliveryCancelToken()

    def guard(request, cancel_token):
        assert cancel_token is token
        assert cancel_token.request_cancel() is True
        return DeliveryCommitAuthorization(
            job_id=request.job_id,
            start_fingerprint=request.start_fingerprint,
            decision="authorized",
        )

    result = orchestrate_delivery_package(
        job_id=33,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=guard,
        cancel_token=token,
    )

    assert result.primary_status == "cancelled"
    assert result.primary_error_code == "output_cancelled"
    assert result.committed is False
    assert result.final_path is None
    assert result.cleanup_status == "completed"


def test_cancel_during_artifact_operation_cleans_staging(tmp_path):
    token = DeliveryCancelToken()

    def cancel_after_vmd(kind, context, output_path, cancel_token):
        output_path.write_bytes(b"vmd")
        if kind == "vmd":
            assert cancel_token.request_cancel() is True

    result = orchestrate_delivery_package(
        job_id=34,
        start_context=_context(tmp_path),
        artifact_operations=_operations([], cancel_after_vmd),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=token,
    )

    assert result.primary_status == "cancelled"
    assert result.primary_error_code == "output_cancelled"
    assert result.cleanup_status == "completed"
    assert result.final_path is None


def test_destination_created_after_preflight_is_not_replaced(tmp_path, monkeypatch):
    real_rename = delivery_package.os.rename
    final_path = tmp_path / "delivery"

    def race_rename(staging_path, destination_path):
        assert destination_path == final_path
        final_path.mkdir()
        (final_path / "keep.txt").write_bytes(b"keep")
        return real_rename(staging_path, destination_path)

    monkeypatch.setattr(delivery_package.os, "rename", race_rename)

    result = orchestrate_delivery_package(
        job_id=35,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "output_destination_collision"
    assert result.committed is False
    assert result.cleanup_status == "completed"
    assert (final_path / "keep.txt").read_bytes() == b"keep"
    assert not any(
        path.name.startswith(".MMD_AutoLipTool.delivery-")
        for path in tmp_path.iterdir()
    )


def test_rename_failure_without_destination_is_failed_and_cleaned(tmp_path, monkeypatch):
    def fail_rename(staging_path, destination_path):
        raise PermissionError("rename denied")

    monkeypatch.setattr(delivery_package.os, "rename", fail_rename)

    result = orchestrate_delivery_package(
        job_id=36,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "output_permission_denied"
    assert result.commit_phase == "commit_failed"
    assert result.cleanup_status == "completed"
    assert result.final_path is None


def test_late_cancel_cannot_overwrite_committed_success(tmp_path, monkeypatch):
    real_rename = delivery_package.os.rename
    rename_started = threading.Event()
    release_rename = threading.Event()
    cancel_finished = threading.Event()
    cancel_results = []
    result_holder = []
    token = DeliveryCancelToken()

    def blocking_rename(staging_path, destination_path):
        rename_started.set()
        assert release_rename.wait(timeout=2.0)
        return real_rename(staging_path, destination_path)

    def run_orchestration():
        result_holder.append(
            orchestrate_delivery_package(
                job_id=37,
                start_context=_context(tmp_path),
                artifact_operations=_operations([]),
                pre_commit_guard=_authorized_guard([]),
                cancel_token=token,
            )
        )

    def request_cancel():
        cancel_results.append(token.request_cancel())
        cancel_finished.set()

    monkeypatch.setattr(delivery_package.os, "rename", blocking_rename)
    worker = threading.Thread(target=run_orchestration)
    worker.start()
    assert rename_started.wait(timeout=2.0)

    cancel_thread = threading.Thread(target=request_cancel)
    cancel_thread.start()
    assert not cancel_finished.wait(timeout=0.1)
    release_rename.set()
    worker.join(timeout=2.0)
    cancel_thread.join(timeout=2.0)

    assert len(result_holder) == 1
    assert result_holder[0].primary_status == "success"
    assert result_holder[0].committed is True
    assert cancel_results == [False]


def test_cleanup_failure_preserves_primary_error_and_staging_path(tmp_path, monkeypatch):
    real_cleanup = delivery_package._cleanup_owned_staging
    cleanup_calls = []

    def fail_first_cleanup(staging_path, parent_directory):
        cleanup_calls.append(staging_path)
        if len(cleanup_calls) == 1:
            return False
        return real_cleanup(staging_path, parent_directory)

    def fail_vmd(kind, context, output_path, cancel_token):
        raise RuntimeError("expected failure")

    monkeypatch.setattr(
        delivery_package,
        "_cleanup_owned_staging",
        fail_first_cleanup,
    )
    result = orchestrate_delivery_package(
        job_id=38,
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
    assert real_cleanup(result.staging_path, tmp_path.resolve()) is True


def test_cancel_token_process_bridge_terminates_registered_process():
    terminated = threading.Event()

    class FakeProcess:
        def poll(self):
            return None if not terminated.is_set() else 0

        def terminate(self):
            terminated.set()

        def wait(self, timeout):
            assert terminated.wait(timeout=timeout)

        def kill(self):
            terminated.set()

    token = DeliveryCancelToken(grace_sec=0.0)
    process = FakeProcess()
    token.register_process(process)

    assert token.request_cancel() is True
    assert terminated.wait(timeout=1.0)


def test_terminal_result_rejects_success_with_inconsistent_fields(tmp_path):
    with pytest.raises(ValueError):
        DeliveryTerminalResult(
            job_id=39,
            primary_status="success",
            primary_error_code=None,
            committed=True,
            final_path=tmp_path / "final",
            staging_path=tmp_path / "staging",
            cleanup_status="not_required",
            commit_phase="committed",
            artifact_phase="report",
        )
