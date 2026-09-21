from __future__ import annotations

from unittest.mock import patch

from gui_wx.ui_state import UiState
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    build_base_plan_identity,
)
from src.core.event_adjustment import empty_adjustment_snapshot
from src.core.event_adjustment_history import initialize_output_edit_history
from src.core.generation_presets import GenerationPresetStore, GenerationSettings
from src.core.output_edit_state import GenerationState, OutputEditState
from src.core.pipeline import VowelTimingPlan
from src.core.settings_store import SettingsStore
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import workspace_tempdir


def _base_input(settings: GenerationSettings | None = None) -> BaseTimingPlanInput:
    generation = settings or GenerationSettings()
    return BaseTimingPlanInput(
        timeline=(
            VowelTimelinePoint(
                0.5,
                "あ",
                value=0.5,
                start_sec=0.4,
                end_sec=0.6,
            ),
        ),
        observations=None,
        source_duration_frames=30,
        shape_parameters=ShapeParameters(
            closing_hold_frames=generation.closing_hold_frames,
            closing_softness_frames=generation.closing_softness_frames,
            long_vowel_mode=generation.long_vowel_mode,
        ),
    )


def _output_state(
    settings: GenerationSettings | None = None,
    active_preset_id: str | None = None,
) -> OutputEditState:
    base = _base_input(settings)
    identity = build_base_plan_identity(base)
    return OutputEditState(
        base_plan_identity=identity,
        adjustment_snapshot=empty_adjustment_snapshot(identity),
        generation_state=GenerationState(
            settings or GenerationSettings(),
            active_preset_id,
        ),
    )


def test_workspace_reset_clears_workspace_state_but_preserves_generation_and_app_settings():
    state = UiState(
        recent_text_files=["recent.txt"],
        recent_wav_files=["recent.wav"],
        last_text_dialog_dir="C:/text",
        theme_mode="light",
    )
    generation = GenerationState(GenerationSettings(3, 4, "decay"), "preset-id")
    state.generation_state = generation
    state.mark_analysis_success(
        VowelTimingPlan(vowels=["あ"], timeline=[], anchors=[], source="test"),
        analysis_text_content="あ",
        analysis_text_source="text_file",
    )
    output_state = _output_state(generation.generation_settings, generation.active_preset_id)
    state.output_edit_history_state = initialize_output_edit_history(output_state)
    state.selected_source_event_index = 0
    state.selected_base_plan_identity_digest = output_state.base_plan_identity.digest
    state.current_output_diagnostics_snapshot = object()

    state.reset_workspace()

    assert state.generation_state == generation
    assert state.recent_text_files == ["recent.txt"]
    assert state.recent_wav_files == ["recent.wav"]
    assert state.last_text_dialog_dir == "C:/text"
    assert state.theme_mode == "light"
    assert state.current_timing_plan is None
    assert state.output_edit_history_state is None
    assert state.current_output_diagnostics_snapshot is None
    assert state.selected_source_event_index is None
    assert state.selected_base_plan_identity_digest is None


def test_missing_and_invalid_ini_have_distinct_safe_startup_results():
    with workspace_tempdir("ms22_b6_ini_startup") as tmp_dir:
        missing_store = SettingsStore(tmp_dir / "missing.ini")
        missing = missing_store.load()
        assert missing.file_exists is False
        assert missing.load_error is None
        assert missing.settings == SettingsStore.default_settings()

        invalid_path = tmp_dir / "invalid.ini"
        invalid_path.write_text("[broken", encoding="utf-8")
        invalid = SettingsStore(invalid_path).load()
        assert invalid.file_exists is True
        assert invalid.had_error is True
        assert invalid.settings == SettingsStore.default_settings()


def test_restart_restores_only_last_successful_generation_settings():
    with workspace_tempdir("ms22_b6_restart") as tmp_dir:
        settings_path = tmp_dir / "MMD_AutoLipTool.ini"
        store = SettingsStore(settings_path)
        expected = SettingsStore.default_settings()
        expected.update(
            {
                "closing_hold_frames": 6,
                "closing_softness_frames": 8,
                "long_vowel_mode": "decay",
                "active_preset_id": None,
            }
        )
        assert store.save(expected).succeeded

        state = UiState()
        state.generation_state = GenerationState(
            GenerationSettings(6, 8, "decay"),
            None,
        )
        state.output_edit_history_state = initialize_output_edit_history(
            _output_state(GenerationSettings(6, 8, "decay"))
        )

        restarted = SettingsStore(settings_path).load()
        assert restarted.settings["closing_hold_frames"] == 6
        assert restarted.settings["closing_softness_frames"] == 8
        assert restarted.settings["long_vowel_mode"] == "decay"
        assert state.output_edit_history_state is not None
        assert UiState().output_edit_history_state is None


def test_missing_active_preset_resolves_to_custom_without_changing_settings():
    with workspace_tempdir("ms22_b6_custom_fallback") as tmp_dir:
        store = GenerationPresetStore(tmp_dir / "MMD_AutoLipTool.ini")
        settings = GenerationSettings(2, 3, "decay")
        resolution = store.resolve_active(settings, "missing-preset-id")

        assert resolution.generation_settings == settings
        assert resolution.active_preset_id is None
        assert resolution.active_preset_display_name is None
        assert resolution.source == "custom"


def test_invalid_json_keeps_builtin_presets_and_disables_user_mutation():
    with workspace_tempdir("ms22_b6_invalid_json") as tmp_dir:
        presets_path = tmp_dir / "presets.json"
        presets_path.write_text("{broken", encoding="utf-8")
        store = GenerationPresetStore(
            tmp_dir / "MMD_AutoLipTool.ini",
            presets_path=presets_path,
        )

        result = store.load()
        mutation = store.create("blocked", GenerationSettings())

        assert result.error_code == "invalid_json"
        assert result.user_presets == ()
        assert result.mutation_available is False
        assert mutation.succeeded is False
        assert mutation.error_code == "store_unavailable"
        assert len(result.built_in_presets) >= 2


def test_json_replace_failure_preserves_old_collection_and_blocks_retry():
    with workspace_tempdir("ms22_b6_json_replace") as tmp_dir:
        presets_path = tmp_dir / "presets.json"
        store = GenerationPresetStore(
            tmp_dir / "MMD_AutoLipTool.ini",
            presets_path=presets_path,
        )
        first = store.create("existing", GenerationSettings())
        assert first.succeeded
        before_bytes = presets_path.read_bytes()
        before_collection = store.user_presets

        with patch("src.core.generation_presets.os.replace", side_effect=OSError("locked")):
            failed = store.create("new", GenerationSettings(1, 2, "decay"))

        retry = store.create("retry", GenerationSettings())
        assert failed.succeeded is False
        assert failed.error_code == "replace_failed"
        assert store.user_presets == before_collection
        assert presets_path.read_bytes() == before_bytes
        assert retry.error_code == "store_unavailable"


def test_ini_save_failure_keeps_last_successful_file_and_disables_followups():
    with workspace_tempdir("ms22_b6_ini_failure") as tmp_dir:
        settings_path = tmp_dir / "MMD_AutoLipTool.ini"
        store = SettingsStore(settings_path)
        initial = SettingsStore.default_settings()
        initial["closing_hold_frames"] = 2
        assert store.save(initial).succeeded
        before_bytes = settings_path.read_bytes()

        changed = dict(initial)
        changed["closing_hold_frames"] = 7
        with patch("src.core.settings_store.os.replace", side_effect=OSError("locked")):
            failed = store.save(changed)
        followup = store.save(changed)

        assert failed.attempted is True
        assert failed.succeeded is False
        assert failed.first_failure_in_session is True
        assert followup.attempted is False
        assert followup.save_disabled is True
        assert settings_path.read_bytes() == before_bytes
        assert SettingsStore(settings_path).load().settings["closing_hold_frames"] == 2
