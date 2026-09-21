from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import os
import stat
from types import SimpleNamespace

import pytest

import src.core.delivery_package as delivery_package
from src.core.delivery_package import (
    DeliveryArtifactNames,
    DeliveryContractError,
    build_delivery_start_context,
    validate_delivery_destination,
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


def test_validated_destination_preserves_names_and_direct_child(tmp_path):
    destination = validate_delivery_destination(_context(tmp_path, "my delivery"))

    assert destination.parent_directory == tmp_path.resolve()
    assert destination.folder_name == "my delivery"
    assert destination.final_directory == tmp_path / "my delivery"
    assert tuple(kind for kind, _ in destination.final_artifact_paths) == (
        "vmd",
        "mmd_wav",
        "report",
    )
    assert tuple(path.name for _, path in destination.final_artifact_paths) == (
        "音声 sample_lip.vmd",
        "音声 sample_mmd.wav",
        "音声 sample_report.txt",
    )


@pytest.mark.parametrize(
    "folder_name",
    [
        ".",
        "..",
        "bad/name",
        "bad\\name",
        "bad:name",
        "bad*name",
        "trailing ",
        "trailing.",
        "CON",
        "con.txt",
        "NUL.tar.gz",
        "COM1",
        "com¹",
        "CONIN$",
        "CLOCK$",
        "bad\x00name",
        "bad\ud800name",
    ],
)
def test_invalid_windows_folder_names_are_rejected(tmp_path, folder_name):
    context = _context(tmp_path)

    invalid_context = replace(context, folder_name=folder_name)

    with pytest.raises(DeliveryContractError) as error:
        validate_delivery_destination(invalid_context)

    assert error.value.code == "output_path_invalid"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("a" * 255, "a" * 255),
        ("😀" * 127, "😀" * 127),
    ],
)
def test_component_utf16_boundary_is_accepted(value, expected):
    assert delivery_package._validate_delivery_component(value, "component") == expected


@pytest.mark.parametrize(
    "value",
    ["a" * 256, "😀" * 128, "\ud800"],
)
def test_component_utf16_boundary_is_rejected(value):
    with pytest.raises(DeliveryContractError) as error:
        delivery_package._validate_delivery_component(value, "component")

    assert error.value.code == "output_path_invalid"


def test_absolute_path_length_boundary_is_exact():
    accepted = Path("C:\\" + "a" * 237)
    rejected = Path("C:\\" + "a" * 238)

    assert delivery_package._utf16_code_units(str(accepted)) == 240
    delivery_package._validate_delivery_absolute_path(accepted, "path")
    with pytest.raises(DeliveryContractError) as error:
        delivery_package._validate_delivery_absolute_path(rejected, "path")
    assert error.value.code == "output_path_invalid"


@pytest.mark.parametrize("path_kind", ["missing", "file"])
def test_invalid_parent_is_rejected(tmp_path, path_kind):
    if path_kind == "missing":
        parent = tmp_path / "missing"
    else:
        parent = tmp_path / "parent-file"
        parent.write_bytes(b"parent")

    with pytest.raises(DeliveryContractError) as error:
        validate_delivery_destination(_context(tmp_path, "delivery").__class__(
            current_state=_context(tmp_path, "delivery").current_state,
            parent_directory=parent,
            folder_name="delivery",
            report_generated_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
        ))

    assert error.value.code == "output_parent_invalid"


def test_relative_and_namespace_parents_are_rejected(tmp_path):
    context = _context(tmp_path)
    relative = replace(context, parent_directory=Path("relative-parent"))
    with pytest.raises(DeliveryContractError) as relative_error:
        validate_delivery_destination(relative)
    assert relative_error.value.code == "output_parent_invalid"

    namespace = replace(context, parent_directory=Path(r"\\?\C:\output"))
    with pytest.raises(DeliveryContractError) as namespace_error:
        validate_delivery_destination(namespace)
    assert namespace_error.value.code == "output_parent_invalid"


@pytest.mark.parametrize("existing_kind", ["empty_directory", "non_empty_directory", "file"])
def test_existing_final_entry_is_always_collision(tmp_path, existing_kind):
    final_path = tmp_path / "delivery"
    if existing_kind == "empty_directory":
        final_path.mkdir()
    elif existing_kind == "non_empty_directory":
        final_path.mkdir()
        (final_path / "keep.txt").write_bytes(b"keep")
    else:
        final_path.write_bytes(b"keep")

    with pytest.raises(DeliveryContractError) as error:
        validate_delivery_destination(_context(tmp_path))

    assert error.value.code == "output_destination_collision"
    if existing_kind == "non_empty_directory":
        assert (final_path / "keep.txt").read_bytes() == b"keep"
    elif existing_kind == "file":
        assert final_path.read_bytes() == b"keep"


@pytest.mark.parametrize("broken", [False, True])
def test_symlink_final_entry_is_collision_when_supported(tmp_path, broken):
    target = tmp_path / "target"
    if not broken:
        target.mkdir()
    final_path = tmp_path / "delivery"
    try:
        final_path.symlink_to(target, target_is_directory=not broken)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(DeliveryContractError) as error:
        validate_delivery_destination(_context(tmp_path))

    assert error.value.code == "output_destination_collision"
    assert final_path.is_symlink()


def test_lstat_inspection_error_fails_closed(tmp_path, monkeypatch):
    context = _context(tmp_path)
    final_path = tmp_path / "delivery"
    real_lstat = os.lstat

    def failing_lstat(path):
        if Path(path) == final_path:
            raise PermissionError("inspection denied")
        return real_lstat(path)

    monkeypatch.setattr(delivery_package.os, "lstat", failing_lstat)

    with pytest.raises(DeliveryContractError) as error:
        validate_delivery_destination(context)

    assert error.value.code == "output_permission_denied"


def test_reparse_attribute_is_collision_without_following_target(tmp_path, monkeypatch):
    context = _context(tmp_path)
    final_path = tmp_path / "delivery"
    real_lstat = os.lstat
    reparse_stat = SimpleNamespace(
        st_mode=stat.S_IFDIR,
        st_file_attributes=delivery_package._REPARSE_POINT_ATTRIBUTE,
    )

    def reparse_lstat(path):
        if Path(path) == final_path:
            return reparse_stat
        return real_lstat(path)

    monkeypatch.setattr(delivery_package.os, "lstat", reparse_lstat)

    with pytest.raises(DeliveryContractError) as error:
        validate_delivery_destination(context)

    assert error.value.code == "output_destination_collision"
