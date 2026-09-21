from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.core.delivery_package import (
    DeliveryArtifactOperations,
    DeliveryCommitAuthorization,
    DeliveryContractError,
    DeliveryCancelToken,
    build_delivery_start_context,
    orchestrate_delivery_package,
)
from tests.test_ms25_b1_delivery_contract import _evaluate_ready


def _context(tmp_path: Path, folder_name: str = "delivery"):
    result, _ = _evaluate_ready(tmp_path)
    current_state = result.candidate_state
    assert current_state is not None
    return build_delivery_start_context(
        current_state,
        tmp_path,
        folder_name,
        datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
    )


def _operations(events, callback=None):
    def make_operation(kind):
        def operation(context, output_path, cancel_token):
            events.append((kind, context, output_path, cancel_token))
            if callback is not None:
                callback(kind, context, output_path, cancel_token)
            else:
                output_path.write_bytes(f"{kind}-artifact".encode("ascii"))

        return operation

    return DeliveryArtifactOperations(
        generate_and_validate_vmd=make_operation("vmd"),
        generate_and_validate_mmd_wav=make_operation("mmd_wav"),
        generate_and_validate_report=make_operation("report"),
    )


def _authorized_guard(calls):
    def guard(request, cancel_token):
        calls.append((request, cancel_token))
        return DeliveryCommitAuthorization(
            job_id=request.job_id,
            start_fingerprint=request.start_fingerprint,
            decision="authorized",
        )

    return guard


def test_success_generates_three_artifacts_in_fixed_order_and_commits_once(tmp_path):
    events = []
    guard_calls = []
    context = _context(tmp_path, "delivery folder")
    final_path = tmp_path / "delivery folder"
    final_existed_during_callbacks = []

    def record_callback(kind, callback_context, output_path, cancel_token):
        final_existed_during_callbacks.append(final_path.exists())
        output_path.write_bytes(f"{kind}-artifact".encode("ascii"))

    result = orchestrate_delivery_package(
        job_id=17,
        start_context=context,
        artifact_operations=_operations(events, record_callback),
        pre_commit_guard=_authorized_guard(guard_calls),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "success"
    assert result.committed is True
    assert result.final_path == final_path
    assert result.staging_path is None
    assert result.commit_phase == "committed"
    assert result.cleanup_status == "not_required"
    assert [kind for kind, *_ in events] == ["vmd", "mmd_wav", "report"]
    assert len(guard_calls) == 1
    assert set(path.name for path in final_path.iterdir()) == {
        "音声 sample_lip.vmd",
        "音声 sample_mmd.wav",
        "音声 sample_report.txt",
    }
    assert all(event[2].parent.parent == tmp_path.resolve() for event in events)
    assert final_existed_during_callbacks == [False, False, False]


def test_staging_name_is_opaque_and_callbacks_receive_only_staging_paths(tmp_path):
    events = []
    context = _context(tmp_path, "chosen folder")

    result = orchestrate_delivery_package(
        job_id=18,
        start_context=context,
        artifact_operations=_operations(events),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.committed is True
    assert all(
        "chosen folder" not in event[2].parent.name
        and "音声 sample" not in event[2].parent.name
        for event in events
    )
    assert all(event[2].parent.parent == tmp_path.resolve() for event in events)


def test_artifact_failure_cleans_staging_and_keeps_final_absent(tmp_path):
    events = []

    def fail_vmd(kind, context, output_path, cancel_token):
        raise DeliveryContractError("vmd_write_failed", "writer failed")

    result = orchestrate_delivery_package(
        job_id=19,
        start_context=_context(tmp_path),
        artifact_operations=_operations(events, fail_vmd),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "vmd_write_failed"
    assert result.committed is False
    assert result.final_path is None
    assert result.staging_path is None
    assert result.cleanup_status == "completed"
    assert result.artifact_phase == "vmd"
    assert not (tmp_path / "delivery").exists()
    assert [kind for kind, *_ in events] == ["vmd"]


def test_missing_artifact_after_normal_return_is_validation_failure(tmp_path):
    events = []

    def no_output(kind, context, output_path, cancel_token):
        return None

    result = orchestrate_delivery_package(
        job_id=20,
        start_context=_context(tmp_path),
        artifact_operations=_operations(events, no_output),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "vmd_validation_failed"
    assert result.cleanup_status == "completed"
    assert result.final_path is None


def test_extra_staging_entry_is_not_committed(tmp_path):
    events = []

    def add_extra_file(kind, context, output_path, cancel_token):
        output_path.write_bytes(kind.encode("ascii"))
        if kind == "report":
            (output_path.parent / "unexpected.tmp").write_bytes(b"extra")

    result = orchestrate_delivery_package(
        job_id=21,
        start_context=_context(tmp_path),
        artifact_operations=_operations(events, add_extra_file),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "delivery_staging_contents_invalid"
    assert result.cleanup_status == "completed"
    assert result.final_path is None
    assert not (tmp_path / "delivery").exists()


def test_cancel_before_generation_does_not_call_operations_or_guard(tmp_path):
    events = []
    guard_calls = []
    cancel_token = DeliveryCancelToken()
    assert cancel_token.request_cancel() is True

    result = orchestrate_delivery_package(
        job_id=22,
        start_context=_context(tmp_path),
        artifact_operations=_operations(events),
        pre_commit_guard=_authorized_guard(guard_calls),
        cancel_token=cancel_token,
    )

    assert result.primary_status == "cancelled"
    assert result.primary_error_code == "output_cancelled"
    assert result.cleanup_status == "not_required"
    assert events == []
    assert guard_calls == []


@pytest.mark.parametrize("decision", ["stale", "invalid_job", "closing"])
def test_guard_denial_does_not_commit(tmp_path, decision):
    def guard(request, cancel_token):
        return DeliveryCommitAuthorization(
            job_id=request.job_id,
            start_fingerprint=request.start_fingerprint,
            decision=decision,
        )

    result = orchestrate_delivery_package(
        job_id=23,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=guard,
        cancel_token=DeliveryCancelToken(),
    )

    expected_code = {
        "stale": "delivery_state_stale",
        "invalid_job": "delivery_job_invalid",
        "closing": "output_cancelled",
    }[decision]
    assert result.primary_error_code == expected_code
    assert result.primary_status == ("cancelled" if decision == "closing" else "failed")
    assert result.final_path is None
    assert result.cleanup_status == "completed"


def test_malformed_guard_result_fails_closed(tmp_path):
    result = orchestrate_delivery_package(
        job_id=24,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=lambda request, cancel_token: None,
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "delivery_commit_authorization_invalid"
    assert result.cleanup_status == "completed"
