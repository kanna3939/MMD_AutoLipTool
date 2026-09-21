from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

import src.core.diagnostic_report as diagnostic_report
import src.core.delivery_artifacts as delivery_artifacts
from src.core.delivery_package import DeliveryCancelToken
from src.core.diagnostic_report import (
    DiagnosticReportError,
    format_diagnostic_report,
    write_diagnostic_report,
)
from src.core.morph_name_sets import LATIN_MORPH_NAME_SET_ID
from src.core.output_diagnostics import WhisperDiagnosticsSummary
from tests.test_ms20_b6_diagnostic_report import GENERATED_AT, _item, _snapshot
from tests.test_ms25_b3_delivery_artifacts import _context


def _generation_identity_block(report: str) -> str:
    return report.split("[Generation]\n", 1)[1].split("[Adjustment]\n", 1)[0]


def test_default_report_has_complete_japanese_identity_block():
    report = format_diagnostic_report(_snapshot(), generated_at=GENERATED_AT)

    assert _generation_identity_block(report) == (
        "VMD Model Name: AutoLipTool\n"
        "Closing Hold Frames: 2\n"
        "Closing Softness Frames: 1\n"
        "Fingerprint Schema Version: ms20-output-diagnostics-v1\n"
        "Active Long Vowel Mode: hold\n"
        "Active Preset ID: N/A\n"
        "Active Preset Display Name: Custom\n"
        "Effective Long Vowel Hold Run Count: N/A\n"
        "Effective Long Vowel Decay Run Count: N/A\n"
        "Active Model Profile ID: N/A\n"
        "Active Model Profile Display Name: (not available)\n"
        "Active Profile Baseline Preset ID: N/A\n"
        "Baseline Preset Display Name: (not available)\n"
        "Model Profile Resolution Status: no_profile\n"
        "Model Profile Resolution Reason: (not available)\n"
        "Resolved Morph Name Set ID: builtin:japanese-vowels\n"
        "Resolved Morph Name Set Display Name: 日本語5母音\n"
        "Resolved Morph Names (Ordered): あ / い / う / え / お\n"
        "\n"
    )


def test_latin_profile_report_keeps_profile_and_morph_identity_separate():
    snapshot = _snapshot()
    generation_summary = replace(
        snapshot.generation_summary,
        active_preset_id="preset:latin",
        active_preset_display_name="Latin preset",
        active_model_profile_id="profile:latin",
        active_model_profile_display_name="Latin profile",
        active_profile_baseline_preset_id="preset:latin-baseline",
        baseline_preset_display_name="Latin baseline",
        model_profile_resolution_status="resolved",
        model_profile_resolution_reason_code=None,
        resolved_morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
        resolved_morph_name_set_display_name="英字5母音",
    )
    report = format_diagnostic_report(
        replace(snapshot, generation_summary=generation_summary),
        generated_at=GENERATED_AT,
    )

    assert "Active Preset ID: preset:latin\n" in report
    assert "Active Profile Baseline Preset ID: preset:latin-baseline\n" in report
    assert "Model Profile Resolution Status: resolved\n" in report
    assert "Resolved Morph Name Set ID: builtin:latin-vowels\n" in report
    assert "Resolved Morph Name Set Display Name: 英字5母音\n" in report
    assert "Resolved Morph Names (Ordered): A / I / U / E / O\n" in report
    assert report.index("Active Preset ID: preset:latin") < report.index(
        "Active Profile Baseline Preset ID: preset:latin-baseline"
    )


def test_fallback_no_profile_preserves_status_and_reason():
    snapshot = _snapshot()
    generation_summary = replace(
        snapshot.generation_summary,
        model_profile_resolution_status="fallback_no_profile",
        model_profile_resolution_reason_code="active_profile_not_found",
        resolved_morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
        resolved_morph_name_set_display_name="英字5母音",
    )
    report = format_diagnostic_report(
        replace(snapshot, generation_summary=generation_summary),
        generated_at=GENERATED_AT,
    )

    assert "Active Model Profile ID: N/A\n" in report
    assert "Model Profile Resolution Status: fallback_no_profile\n" in report
    assert "Model Profile Resolution Reason: active_profile_not_found\n" in report
    assert "Resolved Morph Names (Ordered): A / I / U / E / O\n" in report


def test_whisper_identity_uses_four_independent_key_display_manifest_fields():
    whisper_summary = WhisperDiagnosticsSummary(
        selected_model_key="selected-key",
        selected_model_display_name="Selected Display",
        selected_manifest_identity="manifest-selected",
        active_model_key="active-key",
        active_model_display_name="Active Display",
        active_manifest_identity="manifest-active",
        loaded_model_key="loaded-key",
        loaded_model_display_name="Loaded\tDisplay",
        loaded_manifest_identity="manifest-loaded",
        analysis_model_key="analysis-key",
        analysis_model_display_name="Analysis Display",
        analysis_manifest_identity="manifest-analysis",
        manifest_schema_version=2,
        package_gate_status="passed",
        analysis_identity_status="mismatch",
        runtime_identity_status="unloaded",
    )
    snapshot = replace(_snapshot(), whisper_summary=whisper_summary)

    report = format_diagnostic_report(snapshot, generated_at=GENERATED_AT)

    assert "Selected Model Key: selected-key\n" in report
    assert "Selected Model Display Name: Selected Display\n" in report
    assert "Selected Manifest Identity: manifest-selected\n" in report
    assert "Active Model Key: active-key\n" in report
    assert "Active Model Display Name: Active Display\n" in report
    assert "Active Manifest Identity: manifest-active\n" in report
    assert "Loaded Model Key: loaded-key\n" in report
    assert "Loaded Model Display Name: Loaded\\tDisplay\n" in report
    assert "Loaded Manifest Identity: manifest-loaded\n" in report
    assert "Analysis Model Key: analysis-key\n" in report
    assert "Analysis Model Display Name: Analysis Display\n" in report
    assert "Analysis Manifest Identity: manifest-analysis\n" in report
    assert "Analysis Identity Status: mismatch\n" in report
    assert "Runtime Identity Status: unloaded\n" in report
    assert "Loaded Model Display Name: Active Display" not in report
    assert "Analysis Model Display Name: Active Display" not in report


def test_formatter_does_not_change_snapshot_or_fingerprint():
    snapshot = _snapshot(_item())
    fingerprint_payload = snapshot.fingerprint_payload
    save_state_fingerprint = snapshot.save_state_fingerprint

    format_diagnostic_report(snapshot, generated_at=GENERATED_AT)

    assert snapshot.fingerprint_payload is fingerprint_payload
    assert snapshot.save_state_fingerprint == save_state_fingerprint


def test_writer_failure_has_fixed_safe_message_and_preserves_cause(tmp_path: Path):
    target = tmp_path / "report.txt"
    target.write_bytes(b"existing")

    with patch(
        "src.core.diagnostic_report.os.replace",
        side_effect=PermissionError(r"C:\secret\locked-report.txt"),
    ):
        with pytest.raises(DiagnosticReportError) as error:
            write_diagnostic_report(
                _snapshot(),
                target,
                generated_at=GENERATED_AT,
            )

    assert str(error.value) == "診断レポートを安全に保存できませんでした。"
    assert r"C:\secret\locked-report.txt" not in str(error.value)
    assert isinstance(error.value.__cause__, PermissionError)
    assert str(error.value.__cause__) == r"C:\secret\locked-report.txt"
    assert target.read_bytes() == b"existing"
    assert list(tmp_path.glob("*.tmp")) == []


def test_invalid_morph_lookup_fails_closed_for_formatter_and_writer(
    tmp_path: Path,
    monkeypatch,
):
    def fail_lookup(_set_id):
        raise ValueError("unknown morph set")

    monkeypatch.setattr(diagnostic_report, "get_builtin_morph_name_set", fail_lookup)

    with pytest.raises(ValueError, match="unknown morph set"):
        format_diagnostic_report(_snapshot(), generated_at=GENERATED_AT)

    with pytest.raises(DiagnosticReportError) as error:
        write_diagnostic_report(
            _snapshot(),
            tmp_path / "report.txt",
            generated_at=GENERATED_AT,
        )

    assert str(error.value) == "診断レポートを安全に保存できませんでした。"
    assert isinstance(error.value.__cause__, ValueError)
    assert str(error.value.__cause__) == "unknown morph set"


def test_b3_delivery_report_contains_b4_identity_and_exact_formatter_bytes(tmp_path):
    context = _context(tmp_path)
    output_path = tmp_path / "delivery-report.txt"

    delivery_artifacts.build_delivery_artifact_operations().generate_and_validate_report(
        context,
        output_path,
        DeliveryCancelToken(),
    )

    expected = format_diagnostic_report(
        context.current_state.diagnostics_snapshot,
        generated_at=context.report_generated_at,
    ).encode("utf-8")
    assert output_path.read_bytes() == expected
    report = output_path.read_text(encoding="utf-8")
    assert "Active Model Profile ID: N/A\n" in report
    assert "Resolved Morph Names (Ordered): あ / い / う / え / お\n" in report
    assert "Loaded Model Display Name: (not available)\n" in report
    assert "Analysis Model Display Name: (not available)\n" in report
    assert "Projection Generation: 4\n" in report
    assert context.current_state.diagnostics_snapshot.save_state_fingerprint == (
        context.current_state.start_fingerprint
    )
