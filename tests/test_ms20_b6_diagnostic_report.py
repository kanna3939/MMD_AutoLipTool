from dataclasses import replace
from datetime import datetime, timezone
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core import (
    AdjustmentDiagnosticsSummary,
    AnalysisDiagnosticsSummary,
    DiagnosticItem,
    DiagnosticReportError,
    DiagnosticSeverity,
    GenerationDiagnosticsSummary,
    InputDiagnosticsSummary,
    OutputDiagnosticsSnapshot,
    SaveabilitySummary,
    build_diagnostic_report_default_filename,
    format_diagnostic_report,
    write_diagnostic_report,
)


GENERATED_AT = datetime(2026, 7, 18, 12, 34, 56, tzinfo=timezone.utc)


def _snapshot(
    *items: DiagnosticItem,
    source_audio_path: str | None = "c:/audio/Voice.WAV",
) -> OutputDiagnosticsSnapshot:
    return OutputDiagnosticsSnapshot(
        input_summary=InputDiagnosticsSummary(
            input_mode="text_audio",
            normalized_text_path=None,
            normalized_source_audio_path=source_audio_path,
            normalized_effective_wav_path="c:/cache/analysis.wav",
            text_content_present=True,
            analysis_text_present=True,
        ),
        analysis_summary=AnalysisDiagnosticsSummary(
            analysis_result_valid=True,
            analysis_pending_rebuild=False,
            timing_source="whisper_words",
            anchor_count=2,
            event_count=3,
            max_frame=42,
            timing_warning_present=False,
            observation_fallback_count=0,
        ),
        generation_summary=GenerationDiagnosticsSummary(
            vmd_model_name="AutoLipTool",
            closing_hold_frames=2,
            closing_softness_frames=1,
            fingerprint_schema_version="ms20-output-diagnostics-v1",
        ),
        saveability=SaveabilitySummary(
            vmd_save_allowed=True,
            blocking_codes=(),
            warning_codes=(),
        ),
        items=items,
        fingerprint_payload=None,
        save_state_fingerprint="sha256:test",
    )


def _item(
    severity: DiagnosticSeverity = DiagnosticSeverity.INFO,
    *,
    code: str = "analysis_ready",
    summary: str = "解析準備完了",
    detail: str = "line 1\r\nline 2",
) -> DiagnosticItem:
    return DiagnosticItem(
        code=code,
        severity=severity,
        phase="pipeline_build",
        identity_context=(
            ("values", ("float_hex", "0x1.0p+0")),
            ("category", "test"),
        ),
        summary=summary,
        detail=detail,
    )


def test_formatter_has_exact_fixed_structure_for_empty_diagnostics():
    report = format_diagnostic_report(_snapshot(), generated_at=GENERATED_AT)

    assert report == (
        "MMD AutoLipTool Diagnostic Report\n"
        "Generated At: 2026-07-18T12:34:56+00:00\n"
        "\n"
        "[Input]\n"
        "Input Mode: text_audio\n"
        "Text Path: (not available)\n"
        "Source Audio Path: c:/audio/Voice.WAV\n"
        "Effective WAV Path: c:/cache/analysis.wav\n"
        "Text Content Present: true\n"
        "Analysis Text Present: true\n"
        "\n"
        "[Analysis]\n"
        "Analysis Result Valid: true\n"
        "Analysis Pending Rebuild: false\n"
        "Timing Source: whisper_words\n"
        "Anchor Count: 2\n"
        "Event Count: 3\n"
        "Max Frame: 42\n"
        "Timing Warning Present: false\n"
        "Observation Fallback Count: 0\n"
        "\n"
        "[Whisper]\n"
        "Selected Model Key: (not available)\n"
        "Selected Model Display Name: (not available)\n"
        "Selected Manifest Identity: (not available)\n"
        "Active Model Key: (not available)\n"
        "Active Model Display Name: (not available)\n"
        "Active Manifest Identity: (not available)\n"
        "Loaded Model Key: (not available)\n"
        "Loaded Model Display Name: (not available)\n"
        "Loaded Manifest Identity: (not available)\n"
        "Analysis Model Key: (not available)\n"
        "Analysis Model Display Name: (not available)\n"
        "Analysis Manifest Identity: (not available)\n"
        "Analysis Identity Status: not_applicable\n"
        "Runtime Identity Status: not_applicable\n"
        "Manifest Schema Version: (not available)\n"
        "Package: openai-whisper==20250625\n"
        "Package Gate Status: not_checked\n"
        "Availability Scan Status: not_applicable\n"
        "Availability Scan Failure Code: (not available)\n"
        "Management Operation: idle\n"
        "Management Phase: idle\n"
        "Management Model Key: (not available)\n"
        "Management Failure Code: (not available)\n"
        "Management Cleanup Status: (not available)\n"
        "Active Config Status: not_applicable\n"
        "Active Config Reason: (not available)\n"
        "Analysis Rebuild Reason: none\n"
        "Failure Class: none\n"
        "Failure Detail Code: (not available)\n"
        "Safe Failure Notice: (not available)\n"
        "Recoverability: not_applicable\n"
        "Storage Location: 保存先を確認できません\n"
        "Projection Generation: 0\n"
        "\n"
        "[Generation]\n"
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
        "[Adjustment]\n"
        "Base Plan Identity: N/A\n"
        "Adjustment Present: no\n"
        "Adjusted Event Count: 0\n"
            "Effective Shape Count: N/A\n"
            "Effective Morph Frame Count: N/A\n"
            "Long Vowel Mode Override Count: 0\n"
        "\n"
        "[Saveability]\n"
        "VMD Save Allowed: true\n"
        "Blocking Codes: (not available)\n"
        "Warning Codes: (not available)\n"
        "Save State Fingerprint: sha256:test\n"
        "\n"
        "[Diagnostics]\n"
        "(not available)\n"
    )


def test_adjustment_section_reports_ready_counts_and_identity():
    snapshot = replace(
        _snapshot(),
        adjustment_summary=AdjustmentDiagnosticsSummary(
            base_plan_identity_digest="sha256:base",
            adjustment_present=True,
            adjusted_event_count=2,
            effective_shape_count=3,
            effective_morph_frame_count=11,
        ),
    )

    report = format_diagnostic_report(snapshot, generated_at=GENERATED_AT)

    assert (
        "[Adjustment]\n"
        "Base Plan Identity: sha256:base\n"
        "Adjustment Present: yes\n"
        "Adjusted Event Count: 2\n"
            "Effective Shape Count: 3\n"
            "Effective Morph Frame Count: 11\n"
            "Long Vowel Mode Override Count: 0\n"
        "\n"
        "[Saveability]"
    ) in report


def test_formatter_preserves_item_order_and_escapes_display_text():
    snapshot = _snapshot(
        _item(
            DiagnosticSeverity.ERROR,
            code="first",
            summary="summary\tone",
            detail="line 1\r\nline 2",
        ),
        _item(
            DiagnosticSeverity.WARNING,
            code="second",
            summary="summary\nTwo",
            detail="",
        ),
    )

    report = format_diagnostic_report(snapshot, generated_at=GENERATED_AT)

    assert report.index("Code: first") < report.index("Code: second")
    assert "Summary: summary\\tone" in report
    assert "Summary: summary\\nTwo" in report
    assert "    line 1\n    line 2" in report
    assert "    (not available)" in report
    assert 'Identity Context: {"category":"test","values":["float_hex","0x1.0p+0"]}' in report
    assert "\r" not in report
    assert report.endswith("\n")


def test_formatter_is_deterministic_and_only_timestamp_changes():
    snapshot = _snapshot(_item())
    first = format_diagnostic_report(snapshot, generated_at=GENERATED_AT)
    second = format_diagnostic_report(snapshot, generated_at=GENERATED_AT)
    later = format_diagnostic_report(
        snapshot,
        generated_at=datetime(2026, 7, 18, 12, 35, 1, tzinfo=timezone.utc),
    )

    assert first == second
    first_lines = first.splitlines()
    later_lines = later.splitlines()
    assert first_lines[0] == later_lines[0]
    assert first_lines[1] != later_lines[1]
    assert first_lines[2:] == later_lines[2:]


def test_formatter_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        format_diagnostic_report(
            _snapshot(),
            generated_at=datetime(2026, 7, 18, 12, 34, 56),
        )


@pytest.mark.parametrize(
    ("source_path", "expected"),
    [
        (r"C:\Audio\MiXeD.WAV", "MiXeD_report.txt"),
        (Path("voice.mp3"), "voice_report.txt"),
        (None, None),
        ("", None),
        (os.path.abspath(os.path.sep), None),
    ],
)
def test_default_filename_uses_original_source_stem(source_path, expected):
    assert build_diagnostic_report_default_filename(source_path) == expected


def test_writer_outputs_utf8_lf_without_bom_and_replaces_existing_file(tmp_path):
    target = tmp_path / "Voice_report.txt"
    target.write_text("old", encoding="utf-8")

    result = write_diagnostic_report(
        _snapshot(_item()),
        target,
        generated_at=GENERATED_AT,
    )
    data = target.read_bytes()

    assert result == target
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in data
    assert data.decode("utf-8").startswith("MMD AutoLipTool Diagnostic Report\n")
    assert list(tmp_path.glob("*.tmp")) == []


def test_writer_closes_temp_handles_before_replace(tmp_path):
    target = tmp_path / "report.txt"
    real_replace = os.replace

    def asserting_replace(source, destination):
        with open(source, "rb") as handle:
            assert handle.read(1)
        return real_replace(source, destination)

    with patch("src.core.diagnostic_report.os.replace", side_effect=asserting_replace):
        write_diagnostic_report(
            _snapshot(),
            target,
            generated_at=GENERATED_AT,
        )

    assert target.is_file()


def test_writer_failure_preserves_existing_target_and_cleans_temp(tmp_path):
    target = tmp_path / "report.txt"
    target.write_bytes(b"existing")

    with patch(
        "src.core.diagnostic_report.os.replace",
        side_effect=PermissionError("locked"),
    ):
        with pytest.raises(DiagnosticReportError) as error:
            write_diagnostic_report(
                _snapshot(),
                target,
                generated_at=GENERATED_AT,
            )

    assert str(error.value) == "診断レポートを安全に保存できませんでした。"
    assert "locked" not in str(error.value)
    assert isinstance(error.value.__cause__, PermissionError)
    assert str(error.value.__cause__) == "locked"
    assert target.read_bytes() == b"existing"
    assert list(tmp_path.glob("*.tmp")) == []


def test_writer_rejects_missing_parent_without_creating_it(tmp_path):
    target = tmp_path / "missing" / "report.txt"

    with pytest.raises(DiagnosticReportError) as error:
        write_diagnostic_report(
            _snapshot(),
            target,
            generated_at=GENERATED_AT,
        )

    assert str(error.value) == "診断レポートを安全に保存できませんでした。"
    assert isinstance(error.value.__cause__, OSError)
    assert "missing" in str(error.value.__cause__)
    assert not target.parent.exists()
