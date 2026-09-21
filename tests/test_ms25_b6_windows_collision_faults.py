from __future__ import annotations

import ctypes
import ctypes.wintypes
import errno
import os
from pathlib import Path
import stat
import subprocess

import pytest

import src.core.delivery_package as delivery_package
from src.core.delivery_package import (
    DeliveryCancelToken,
    DeliveryCommitAuthorization,
    DeliveryContractError,
    orchestrate_delivery_package,
    validate_delivery_destination,
)
from tests.test_ms25_b2_delivery_orchestration import (
    _authorized_guard,
    _context,
    _operations,
)


def _winerror(code: int) -> OSError:
    error = OSError(f"synthetic Windows error {code}")
    error.winerror = code
    return error


@pytest.mark.parametrize(
    ("error", "default_code", "expected_code"),
    [
        (PermissionError("denied"), "vmd_write_failed", "output_permission_denied"),
        (_winerror(5), "delivery_commit_failed", "output_permission_denied"),
        (_winerror(32), "delivery_commit_failed", "output_file_locked"),
        (_winerror(33), "delivery_commit_failed", "output_file_locked"),
        (OSError(errno.ENAMETOOLONG, "too long"), "vmd_write_failed", "output_path_invalid"),
        (_winerror(123), "vmd_write_failed", "output_path_invalid"),
        (RuntimeError("other I/O failure"), "vmd_write_failed", "vmd_write_failed"),
    ],
)
def test_os_fault_classification_uses_structured_fields(
    error,
    default_code,
    expected_code,
):
    assert (
        delivery_package._delivery_os_error_code(error, default_code)
        == expected_code
    )


def test_cause_chain_permission_is_classified_without_message_matching():
    cause = PermissionError("locale-independent cause")
    error = RuntimeError("wrapper message is not inspected")
    error.__cause__ = cause

    assert (
        delivery_package._delivery_exception_code(error, "delivery_commit_failed")
        == "output_permission_denied"
    )


def test_rename_collision_wins_over_permission_error_and_preserves_existing_entry(
    tmp_path,
    monkeypatch,
):
    final_path = tmp_path / "delivery"
    marker = final_path / "existing.txt"

    def fail_after_creating_destination(staging_path, destination_path):
        final_path.mkdir()
        marker.write_bytes(b"existing-bytes")
        raise _winerror(5)

    monkeypatch.setattr(
        delivery_package.os,
        "rename",
        fail_after_creating_destination,
    )

    result = orchestrate_delivery_package(
        job_id=601,
        start_context=_context(tmp_path),
        artifact_operations=_operations([]),
        pre_commit_guard=_authorized_guard([]),
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "output_destination_collision"
    assert result.commit_phase == "commit_failed"
    assert marker.read_bytes() == b"existing-bytes"


@pytest.mark.skipif(os.name != "nt", reason="Windows reparse-point gate")
def test_actual_junction_is_a_collision_and_target_is_not_touched(tmp_path):
    target = tmp_path / "junction-target"
    target.mkdir()
    marker = target / "marker.txt"
    marker.write_bytes(b"junction-target")
    junction = tmp_path / "delivery"

    completed = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.skip(
            "junction creation unavailable: "
            + (completed.stderr or completed.stdout).strip()
        )

    try:
        with pytest.raises(DeliveryContractError) as error:
            validate_delivery_destination(_context(tmp_path))
        assert error.value.code == "output_destination_collision"
        assert marker.read_bytes() == b"junction-target"
    finally:
        os.rmdir(junction)


def _open_directory_without_delete_sharing(path: Path):
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.HANDLE,
    ]
    create_file.restype = ctypes.wintypes.HANDLE
    handle = create_file(
        str(path),
        0x80000000,
        0x00000003,
        None,
        3,
        0x02000000,
        None,
    )
    if handle == ctypes.c_void_p(-1).value:
        return None, ctypes.get_last_error()
    return handle, None


@pytest.mark.skipif(os.name != "nt", reason="Windows sharing gate")
def test_actual_staging_handle_without_delete_sharing_is_classified_as_locked(
    tmp_path,
):
    handles = []
    open_error = []

    def lock_report(kind, context, output_path, cancel_token):
        output_path.write_bytes(kind.encode("ascii"))
        if kind == "report":
            handle, error_code = _open_directory_without_delete_sharing(
                output_path.parent
            )
            if handle is None:
                open_error.append(error_code)
            else:
                handles.append(handle)

    try:
        result = orchestrate_delivery_package(
            job_id=602,
            start_context=_context(tmp_path),
            artifact_operations=_operations([], lock_report),
            pre_commit_guard=_authorized_guard([]),
            cancel_token=DeliveryCancelToken(),
        )
        if not handles:
            pytest.skip(
                "directory sharing lock unavailable: "
                + str(open_error[0] if open_error else "unknown")
            )
        assert result.primary_status == "failed"
        assert result.primary_error_code == "output_file_locked"
        assert result.commit_phase == "commit_failed"
        assert result.final_path is None
    finally:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        for handle in handles:
            kernel32.CloseHandle(handle)
