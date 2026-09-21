from dataclasses import replace

from src.core.whisper_models import load_whisper_model_catalog
from src.gui_wx.ui_state import (
    UiState,
    WhisperModelSelectionState,
    format_whisper_failure_notice,
)


def test_selection_state_keeps_active_and_analysis_identities_separate() -> None:
    catalog = load_whisper_model_catalog()
    state = WhisperModelSelectionState(
        model_specs=catalog.models,
        selected_model_key="small",
        active_model_key="small",
        active_manifest_identity=catalog.manifest_identity("small"),
        loaded_whisper_model_key="small",
        analysis_whisper_model_key="small",
        retained_whisper_timing_model_identity=catalog.manifest_identity("small"),
        analysis_rebuild_reason="none",
        panel_revision=3,
    )

    selected = replace(
        state,
        selected_model_key="turbo",
        panel_revision=4,
    )

    assert selected.selected_model_key == "turbo"
    assert selected.active_model_key == "small"
    assert selected.active_manifest_identity == state.active_manifest_identity
    assert selected.loaded_whisper_model_key == "small"
    assert selected.analysis_whisper_model_key == "small"
    assert selected.retained_whisper_timing_model_identity == (
        state.retained_whisper_timing_model_identity
    )
    assert selected.analysis_rebuild_reason == "none"


def test_workspace_reset_preserves_whisper_selection_state() -> None:
    catalog = load_whisper_model_catalog()
    whisper_state = WhisperModelSelectionState(
        model_specs=catalog.models,
        selected_model_key="medium",
        active_model_key="small",
        active_manifest_identity=catalog.manifest_identity("small"),
    )
    ui_state = UiState(whisper_model_selection=whisper_state)
    ui_state.selected_text_content = "作業中"

    ui_state.reset_workspace()

    assert ui_state.whisper_model_selection == whisper_state


def test_unknown_failure_code_uses_safe_generic_notice() -> None:
    notice = format_whisper_failure_notice("unknown-code")

    assert "unknown-code" not in notice
    assert "詳細" in notice
