from dataclasses import replace
from datetime import datetime, timezone
import os
from pathlib import Path
import struct

import pytest

import src.core.delivery_artifacts as delivery_artifacts
from src.core.delivery_package import (
    DeliveryCommitAuthorization,
    DeliveryContractError,
    DeliveryCancelToken,
    build_delivery_start_context,
    orchestrate_delivery_package,
)
from src.core.diagnostic_report import format_diagnostic_report
from src.core.ffmpeg_runner import FfmpegRunResult
from src.vmd_writer.validator import VmdReadbackValidationError
from tests.test_ms25_b1_delivery_contract import _evaluate_ready


def _context(tmp_path: Path):
    result, _ = _evaluate_ready(tmp_path)
    current_state = result.candidate_state
    assert current_state is not None
    return build_delivery_start_context(
        current_state,
        tmp_path,
        "delivery",
        datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
    )


def _write_wav(
    path: Path,
    *,
    channels: int = 2,
    sample_rate: int = 44100,
    bits: int = 16,
    data_size: int | None = None,
) -> None:
    if data_size is None:
        data_size = channels * 2
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    with path.open("wb") as handle:
        handle.write(b"RIFF")
        handle.write(struct.pack("<I", 36 + data_size))
        handle.write(b"WAVE")
        handle.write(b"fmt ")
        handle.write(
            struct.pack(
                "<IHHIIHH",
                16,
                1,
                channels,
                sample_rate,
                byte_rate,
                block_align,
                bits,
            )
        )
        handle.write(b"data")
        handle.write(struct.pack("<I", data_size))
        handle.write(b"\0" * data_size)


def _authorized_guard(request, cancel_token):
    return DeliveryCommitAuthorization(
        job_id=request.job_id,
        start_fingerprint=request.start_fingerprint,
        decision="authorized",
    )


def test_factory_returns_three_gui_independent_operations():
    operations = delivery_artifacts.build_delivery_artifact_operations()

    assert callable(operations.generate_and_validate_vmd)
    assert callable(operations.generate_and_validate_mmd_wav)
    assert callable(operations.generate_and_validate_report)
    assert operations.generate_and_validate_vmd.__module__ == delivery_artifacts.__name__


def test_vmd_operation_generates_and_validates_current_effective_plan(tmp_path):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery.vmd"

    delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_vmd(
        context,
        output_path,
        DeliveryCancelToken(),
    )

    assert output_path.is_file()
    assert output_path.stat().st_size >= 74


def test_vmd_operation_builds_one_frame_tuple_for_writer_and_validator(
    tmp_path,
    monkeypatch,
):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery.vmd"
    frames = delivery_artifacts.build_morph_frames_from_effective_shape_plan(
        context.current_state.effective_shape_plan,
        output_morph_names=context.current_state.output_morph_names,
    )
    writer_calls = []
    validator_calls = []

    monkeypatch.setattr(
        delivery_artifacts,
        "build_morph_frames_from_effective_shape_plan",
        lambda *args, **kwargs: frames,
    )
    monkeypatch.setattr(
        delivery_artifacts,
        "write_morph_frames_vmd",
        lambda **kwargs: writer_calls.append(kwargs),
    )
    monkeypatch.setattr(
        delivery_artifacts,
        "validate_morph_vmd_readback",
        lambda *args, **kwargs: validator_calls.append((args, kwargs)),
    )
    delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_vmd(
        context,
        output_path,
        DeliveryCancelToken(),
    )

    assert len(writer_calls) == 1
    assert writer_calls[0]["morph_frames"] is frames
    assert len(validator_calls) == 1
    assert validator_calls[0][1]["expected_morph_frames"] is frames


def test_vmd_write_and_validation_errors_have_separate_codes(tmp_path, monkeypatch):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery.vmd"
    operations = delivery_artifacts.build_delivery_artifact_operations()

    monkeypatch.setattr(
        delivery_artifacts,
        "write_morph_frames_vmd",
        lambda **kwargs: (_ for _ in ()).throw(OSError("write failure")),
    )
    with pytest.raises(DeliveryContractError) as write_error:
        operations.generate_and_validate_vmd(
            context,
            output_path,
            DeliveryCancelToken(),
        )
    assert write_error.value.code == "vmd_write_failed"

    monkeypatch.setattr(
        delivery_artifacts,
        "write_morph_frames_vmd",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        delivery_artifacts,
        "validate_morph_vmd_readback",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            VmdReadbackValidationError("invalid")
        ),
    )
    with pytest.raises(DeliveryContractError) as validation_error:
        operations.generate_and_validate_vmd(
            context,
            output_path,
            DeliveryCancelToken(),
        )
    assert validation_error.value.code == "vmd_validation_failed"


def test_mmd_wav_operation_uses_original_source_and_same_cancel_token(
    tmp_path,
    monkeypatch,
):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery.wav"
    cancel_token = DeliveryCancelToken()
    runner_calls = []

    def fake_runner(**kwargs):
        runner_calls.append(kwargs)
        _write_wav(kwargs["output_path"])
        return FfmpegRunResult(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(
        delivery_artifacts,
        "run_ffmpeg_mmd_wav_cancellable",
        fake_runner,
    )
    delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_mmd_wav(
        context,
        output_path,
        cancel_token,
    )

    assert len(runner_calls) == 1
    assert runner_calls[0]["input_path"] == context.current_state.audio_probe.source_path
    assert runner_calls[0]["input_path"] != Path(
        context.current_state.audio_probe.source_path
    ).with_name("analysis.wav")
    assert runner_calls[0]["cancel_token"] is cancel_token
    assert output_path.is_file()
    assert output_path.stat().st_size > 0


def test_mmd_wav_operation_accepts_relative_source_path_after_normalization(
    tmp_path,
    monkeypatch,
):
    context = _context(tmp_path)
    source_path = Path(context.current_state.audio_probe.source_path)
    monkeypatch.chdir(tmp_path)
    relative_source_path = Path(os.path.relpath(source_path, Path.cwd()))
    probe = replace(
        context.current_state.audio_probe,
        source_path=relative_source_path,
    )
    current_state = replace(context.current_state, audio_probe=probe)
    context = replace(context, current_state=current_state)
    output_path = tmp_path / "relative_delivery.wav"

    def fake_runner(**kwargs):
        _write_wav(kwargs["output_path"])
        return FfmpegRunResult(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(
        delivery_artifacts,
        "run_ffmpeg_mmd_wav_cancellable",
        fake_runner,
    )
    delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_mmd_wav(
        context,
        output_path,
        DeliveryCancelToken(),
    )

    assert output_path.is_file()


def test_mmd_wav_operation_rejects_source_change_before_runner(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source_path = Path(context.current_state.audio_probe.source_path)
    source_path.write_bytes(b"changed source")
    runner_calls = []

    monkeypatch.setattr(
        delivery_artifacts,
        "run_ffmpeg_mmd_wav_cancellable",
        lambda **kwargs: runner_calls.append(kwargs),
    )

    with pytest.raises(DeliveryContractError) as error:
        delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_mmd_wav(
            context,
            tmp_path / "delivery.wav",
            DeliveryCancelToken(),
        )

    assert error.value.code == "source_audio_changed"
    assert runner_calls == []


def test_mmd_wav_operation_rejects_source_change_after_export(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source_path = Path(context.current_state.audio_probe.source_path)

    def fake_runner(**kwargs):
        _write_wav(kwargs["output_path"])
        source_path.write_bytes(b"changed after export")
        return FfmpegRunResult(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(
        delivery_artifacts,
        "run_ffmpeg_mmd_wav_cancellable",
        fake_runner,
    )

    with pytest.raises(DeliveryContractError) as error:
        delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_mmd_wav(
            context,
            tmp_path / "delivery.wav",
            DeliveryCancelToken(),
        )

    assert error.value.code == "source_audio_changed"


@pytest.mark.parametrize(
    ("channels", "runner_returncode", "expected_code"),
    [
        (1, 0, "mmd_wav_validation_failed"),
        (2, 1, "mmd_wav_write_failed"),
    ],
)
def test_mmd_wav_operation_separates_validation_and_write_failures(
    tmp_path,
    monkeypatch,
    channels,
    runner_returncode,
    expected_code,
):
    context = _context(tmp_path)

    def fake_runner(**kwargs):
        if runner_returncode == 0:
            _write_wav(kwargs["output_path"], channels=channels)
        return FfmpegRunResult(stdout="", stderr="failed", returncode=runner_returncode)

    monkeypatch.setattr(
        delivery_artifacts,
        "run_ffmpeg_mmd_wav_cancellable",
        fake_runner,
    )

    with pytest.raises(DeliveryContractError) as error:
        delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_mmd_wav(
            context,
            tmp_path / "delivery.wav",
            DeliveryCancelToken(),
        )

    assert error.value.code == expected_code


def test_report_operation_uses_same_snapshot_and_timestamp(tmp_path, monkeypatch):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery.txt"
    seen = {}
    original_format = delivery_artifacts.format_diagnostic_report
    original_write = delivery_artifacts.write_diagnostic_report

    def tracking_format(snapshot, *, generated_at):
        seen["format"] = (snapshot, generated_at)
        return original_format(snapshot, generated_at=generated_at)

    def tracking_write(snapshot, path, *, generated_at):
        seen["write"] = (snapshot, generated_at)
        return original_write(snapshot, path, generated_at=generated_at)

    monkeypatch.setattr(delivery_artifacts, "format_diagnostic_report", tracking_format)
    monkeypatch.setattr(delivery_artifacts, "write_diagnostic_report", tracking_write)

    delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_report(
        context,
        output_path,
        DeliveryCancelToken(),
    )

    assert seen["format"] == seen["write"]
    assert output_path.read_bytes() == original_format(
        context.current_state.diagnostics_snapshot,
        generated_at=context.report_generated_at,
    ).encode("utf-8")


def test_report_operation_separates_write_and_validation_failure(tmp_path, monkeypatch):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery.txt"

    def corrupted_writer(snapshot, path, *, generated_at):
        path.write_bytes(b"corrupted\r\n")
        return path

    monkeypatch.setattr(delivery_artifacts, "write_diagnostic_report", corrupted_writer)

    with pytest.raises(DeliveryContractError) as error:
        delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_report(
            context,
            output_path,
            DeliveryCancelToken(),
        )

    assert error.value.code == "report_validation_failed"


def test_b2_orchestration_commits_actual_three_artifacts(tmp_path, monkeypatch):
    context = _context(tmp_path)

    def fake_runner(**kwargs):
        _write_wav(kwargs["output_path"])
        return FfmpegRunResult(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(
        delivery_artifacts,
        "run_ffmpeg_mmd_wav_cancellable",
        fake_runner,
    )
    result = orchestrate_delivery_package(
        job_id=301,
        start_context=context,
        artifact_operations=delivery_artifacts.build_delivery_artifact_operations(),
        pre_commit_guard=_authorized_guard,
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "success"
    assert result.committed is True
    final_path = tmp_path / "delivery"
    assert set(path.name for path in final_path.iterdir()) == {
        "音声 sample_lip.vmd",
        "音声 sample_mmd.wav",
        "音声 sample_report.txt",
    }


def test_b2_orchestration_cleans_staging_after_vmd_validation_failure(
    tmp_path,
    monkeypatch,
):
    context = _context(tmp_path)
    monkeypatch.setattr(
        delivery_artifacts,
        "validate_morph_vmd_readback",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            VmdReadbackValidationError("invalid VMD")
        ),
    )

    result = orchestrate_delivery_package(
        job_id=302,
        start_context=context,
        artifact_operations=delivery_artifacts.build_delivery_artifact_operations(),
        pre_commit_guard=_authorized_guard,
        cancel_token=DeliveryCancelToken(),
    )

    assert result.primary_status == "failed"
    assert result.primary_error_code == "vmd_validation_failed"
    assert result.committed is False
    assert result.final_path is None
    assert result.cleanup_status == "completed"
    assert not (tmp_path / "delivery").exists()
