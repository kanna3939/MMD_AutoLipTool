from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui_wx.output_diagnostics_adapter import (  # noqa: E402
    build_output_diagnostics_snapshot_from_ui_state,
    build_whisper_diagnostics_summary,
)
from gui_wx.ui_state import UiState, WhisperModelSelectionState  # noqa: E402
from src.core import (  # noqa: E402
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    VmdWriterParameters,
    WhisperDiagnosticsSummary,
    WhisperModelDiagnosticsItem,
    VowelTimingPlan,
    build_output_diagnostics_snapshot,
    evaluate_whisper_identity_status,
)
from src.core.pipeline import PeakValueEvaluation, PeakValueObservation  # noqa: E402
from src.core.whisper_models import load_whisper_model_catalog  # noqa: E402
from src.core.whisper_timing import SpeechTimingAnchor  # noqa: E402
from src.vmd_writer import VowelTimelinePoint  # noqa: E402


def _plan() -> DiagnosticTimingPlanInput:
    return DiagnosticTimingPlanInput(
        vowels=("あ",),
        timeline=(
            VowelTimelinePoint(
                time_sec=0.1,
                vowel="あ",
                value=0.3,
                duration_sec=0.2,
                start_sec=0.0,
                end_sec=0.2,
            ),
        ),
        anchors=(SpeechTimingAnchor(start_sec=0.0, end_sec=0.2, text="a"),),
        source="whisper_words",
        observations=(),
    )


def _snapshot_input(summary: WhisperDiagnosticsSummary) -> DiagnosticSnapshotInput:
    return DiagnosticSnapshotInput(
        input_mode="text_audio",
        text_path=Path("input.txt"),
        text_content_present=True,
        source_audio_path=Path("voice.wav"),
        effective_wav_path=Path("voice.wav"),
        analysis_text_present=True,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
        timing_plan=_plan(),
        existing_vmd_save_ready=True,
        writer_parameters=VmdWriterParameters(),
        whisper_summary=summary,
        projection_generation=7,
    )


def test_summary_is_immutable_and_snapshot_preserves_exact_generation():
    summary = WhisperDiagnosticsSummary()
    with pytest.raises(FrozenInstanceError):
        summary.package_version = "other"  # type: ignore[misc]

    snapshot = build_output_diagnostics_snapshot(_snapshot_input(summary))
    assert snapshot.whisper_summary is summary
    assert snapshot.projection_generation == 7
    assert snapshot.whisper_summary.analysis_identity_status == "not_applicable"


def test_identity_status_separates_missing_unloaded_and_mismatch():
    assert evaluate_whisper_identity_status(None, None, None, None) == "not_applicable"
    assert evaluate_whisper_identity_status(
        "small", "manifest-a", None, None, unloaded_is_distinct=True
    ) == "unloaded"
    assert evaluate_whisper_identity_status(
        "small", "manifest-a", "medium", "manifest-b"
    ) == "mismatch"
    assert evaluate_whisper_identity_status(
        "small", "manifest-a", "small", "manifest-a"
    ) == "consistent"


def test_candidate_and_management_summary_do_not_change_fingerprint():
    base = WhisperDiagnosticsSummary(
        models=(
            WhisperModelDiagnosticsItem(
                model_key="small",
                display_name="Small",
                size_bytes=10,
                vram_hint="low",
                speed_hint="fast",
                recommended_use="test",
                expected_manifest_identity="manifest-small",
            ),
        ),
        selected_model_key="small",
        active_model_key="small",
        active_manifest_identity="manifest-small",
        analysis_model_key="small",
        analysis_manifest_identity="manifest-small",
        analysis_identity_status="consistent",
        runtime_identity_status="unloaded",
    )
    candidate = replace(
        base,
        selected_model_key="medium",
        selected_model_display_name="Medium",
        management_busy=True,
        management_operation="download",
        management_phase="downloading",
        panel_revision=9,
        storage_location_display="ユーザー指定 (models)",
    )
    first = build_output_diagnostics_snapshot(_snapshot_input(base))
    second = build_output_diagnostics_snapshot(_snapshot_input(candidate))
    assert first.saveability.vmd_save_allowed
    assert second.saveability.vmd_save_allowed
    assert first.items == second.items
    assert first.fingerprint_payload == second.fingerprint_payload
    assert first.save_state_fingerprint == second.save_state_fingerprint


def test_semantic_identity_mismatch_is_fail_closed():
    summary = WhisperDiagnosticsSummary(
        active_model_key="small",
        active_manifest_identity="manifest-small",
        analysis_model_key="medium",
        analysis_manifest_identity="manifest-medium",
        analysis_identity_status="mismatch",
    )
    snapshot = build_output_diagnostics_snapshot(_snapshot_input(summary))
    assert "analysis_rebuild_required" in snapshot.saveability.blocking_codes
    assert not snapshot.saveability.vmd_save_allowed


def test_adapter_summary_has_model_roles_and_safe_storage_projection():
    catalog = load_whisper_model_catalog()
    active_identity = catalog.manifest_identity("small")
    state = UiState(
        whisper_model_selection=WhisperModelSelectionState(
            model_specs=catalog.models,
            selected_model_key="medium",
            active_model_key="small",
            active_manifest_identity=active_identity,
            loaded_whisper_model_key="small",
            loaded_whisper_manifest_identity=active_identity,
            analysis_whisper_model_key="small",
            analysis_whisper_manifest_identity=active_identity,
            storage_root_display=r"C:\private\models",
        ),
    )
    summary = build_whisper_diagnostics_summary(
        state,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
        analysis_in_progress=False,
    )
    assert summary.selected_model_key == "medium"
    assert summary.active_model_key == "small"
    assert summary.loaded_model_key == "small"
    assert summary.analysis_identity_status == "consistent"
    assert summary.runtime_identity_status == "consistent"
    assert r"C:\private\models" not in summary.storage_location_display


def test_adapter_does_not_copy_raw_whisper_exception_to_failure_detail():
    from src.core.whisper_timing import WhisperTimingError
    from gui_wx.output_diagnostics_adapter import build_diagnostic_failure_input

    failure = build_diagnostic_failure_input(
        WhisperTimingError("secret-token-and-path"),
        input_mode="text_audio",
    )
    assert "secret-token-and-path" not in failure.detail
    assert "Whisper" in failure.detail
