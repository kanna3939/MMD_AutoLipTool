from __future__ import annotations

import pytest
import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.right_pane import (
    PresetApplyRequest,
    PresetCreateRequest,
    PresetDeleteRequest,
    PresetPanelItem,
    PresetPanelState,
    PresetSelectRequest,
    PresetUpdateRequest,
)
from src.core.generation_presets import (
    BUILTIN_LONG_VOWEL_DECAY_ID,
    GenerationPresetStore,
    GenerationSettings,
)
from src.core.settings_store import SettingsStore
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir
from tests.test_wx_ms21_b6_undo_redo import make_ready_frame


def _attach_controller(frame: MainFrame, tmp_dir):
    settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
    preset_store = GenerationPresetStore(settings_store=settings_store)
    controller = AppController(
        frame,
        settings_store=settings_store,
        preset_store=preset_store,
    )
    frame.set_controller(controller)
    controller.load_startup_state()
    frame.sync_ui_state()
    return controller


class _Event:
    def Skip(self) -> None:
        return None


def test_panel_uses_stable_ids_and_selection_does_not_apply_output() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b5_panel") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        initial_settings = frame.ui_state.generation_state.generation_settings
        initial_plan = frame.ui_state.current_timing_plan
        initial_history = frame.ui_state.output_edit_history_state
        revision = frame._preset_panel_revision

        frame._on_preset_select_request(
            PresetSelectRequest(BUILTIN_LONG_VOWEL_DECAY_ID, revision)
        )

        assert frame._selected_preset_id == BUILTIN_LONG_VOWEL_DECAY_ID
        assert frame.ui_state.generation_state.generation_settings == initial_settings
        assert frame.ui_state.current_timing_plan is initial_plan
        assert frame.ui_state.output_edit_history_state == initial_history
        assert frame.right_pane.choice_preset.GetString(1).startswith("[組み込み]")
        assert controller.preset_store.user_presets == ()
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_builtin_apply_is_explicit_and_preserves_analysis() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b5_apply") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        initial_plan = frame.ui_state.current_timing_plan
        frame._on_preset_select_request(
            PresetSelectRequest(
                BUILTIN_LONG_VOWEL_DECAY_ID,
                frame._preset_panel_revision,
            )
        )
        frame.right_pane._on_apply_preset(_Event())

        assert frame.ui_state.current_timing_plan is initial_plan
        assert frame.ui_state.generation_state.active_preset_id == BUILTIN_LONG_VOWEL_DECAY_ID
        assert frame.ui_state.generation_state.generation_settings.long_vowel_mode == "decay"
        assert "適用しました" in frame.right_pane.st_preset_notice.GetLabel()
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_create_does_not_change_output_and_update_active_normalizes_to_custom() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b5_mutation") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        before_plan = frame.ui_state.current_timing_plan
        frame._on_preset_create_request(
            PresetCreateRequest(
                "ユーザー長音",
                GenerationSettings(3, 4, "decay"),
                frame._preset_panel_revision,
            )
        )
        user_id = frame._selected_preset_id
        assert user_id is not None
        assert frame.ui_state.current_timing_plan is before_plan
        assert frame.ui_state.generation_state.active_preset_id is None

        frame._on_preset_apply_request(
            PresetApplyRequest(
                user_id,
                frame._preset_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )
        old_settings = frame.ui_state.generation_state.generation_settings
        assert frame.ui_state.generation_state.active_preset_id == user_id
        frame._on_preset_update_request(
            PresetUpdateRequest(
                user_id,
                "ユーザー長音変更",
                GenerationSettings(8, 9, "hold"),
                frame._preset_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )

        assert frame.ui_state.generation_state.generation_settings == old_settings
        assert frame.ui_state.generation_state.active_preset_id is None
        history = frame.ui_state.output_edit_history_state
        assert history is not None
        all_states = [history.current_state, *[item.before_state for item in history.undo_transactions], *[item.after_state for item in history.undo_transactions]]
        assert all(state.generation_state.active_preset_id != user_id for state in all_states)
        assert controller.preset_store.user_presets[0].display_name == "ユーザー長音変更"
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_active_same_settings_rename_keeps_identity_and_delete_normalizes_history() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b5_active_delete") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        settings = GenerationSettings(2, 3, "hold")
        frame._on_preset_create_request(
            PresetCreateRequest("保持プリセット", settings, frame._preset_panel_revision)
        )
        user_id = frame._selected_preset_id
        assert user_id is not None
        frame._on_preset_apply_request(
            PresetApplyRequest(
                user_id,
                frame._preset_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )
        history_before_rename = frame.ui_state.output_edit_history_state
        frame._on_preset_update_request(
            PresetUpdateRequest(
                user_id,
                "保持プリセット改名",
                settings,
                frame._preset_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )
        assert frame.ui_state.generation_state.active_preset_id == user_id
        assert frame._active_preset_display_name == "保持プリセット改名"
        assert (
            frame.ui_state.current_output_diagnostics_snapshot.generation_summary.active_preset_display_name
            == "保持プリセット改名"
        )
        assert frame.ui_state.output_edit_history_state is history_before_rename

        frame._on_preset_delete_request(
            PresetDeleteRequest(
                user_id,
                frame._preset_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )
        assert frame.ui_state.generation_state.active_preset_id is None
        assert frame.ui_state.generation_state.generation_settings == settings
        assert frame._selected_preset_id is None
        history = frame.ui_state.output_edit_history_state
        assert history is not None
        all_states = [
            history.current_state,
            *[item.before_state for item in history.undo_transactions],
            *[item.after_state for item in history.undo_transactions],
        ]
        assert all(state.generation_state.active_preset_id != user_id for state in all_states)
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_invalid_json_keeps_builtin_and_locks_user_mutation() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b5_invalid") as tmp_dir:
        settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
        presets_path = tmp_dir / "presets.json"
        presets_path.write_text("{broken", encoding="utf-8")
        preset_store = GenerationPresetStore(
            settings_store=settings_store,
            presets_path=presets_path,
        )
        controller = AppController(
            frame,
            settings_store=settings_store,
            preset_store=preset_store,
        )
        frame.set_controller(controller)
        controller.load_startup_state()
        frame.sync_ui_state()

        assert preset_store.mutation_available is False
        assert frame.right_pane.choice_preset.GetString(1).startswith("[組み込み]")
        assert frame.right_pane.btn_create_preset.IsEnabled() is False
        frame._on_preset_select_request(
            PresetSelectRequest(
                BUILTIN_LONG_VOWEL_DECAY_ID,
                frame._preset_panel_revision,
            )
        )
        assert frame.right_pane.btn_apply_preset.IsEnabled() is True
        assert "組み込みプリセットを継続利用できます" in frame.right_pane.st_preset_notice.GetLabel()
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_stale_apply_request_does_not_change_generation_state() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b5_stale") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        before = frame.ui_state.generation_state
        frame._on_preset_apply_request(
            PresetApplyRequest(
                BUILTIN_LONG_VOWEL_DECAY_ID,
                frame._preset_panel_revision - 1,
                frame.ui_state.selected_event_editor_revision,
            )
        )
        assert frame.ui_state.generation_state == before
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_panel_state_rejects_active_custom_display_name() -> None:
    with pytest.raises(ValueError):
        PresetPanelState(
            items=(
                PresetPanelItem(
                    "id",
                    "name",
                    "user",
                    GenerationSettings(),
                ),
            ),
            active_preset_id=None,
            active_preset_display_name="name",
        )
