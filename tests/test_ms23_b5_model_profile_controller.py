from __future__ import annotations

import uuid

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from src.core.generation_presets import GenerationPresetStore, GenerationSettings
from src.core.model_profiles import ProfileGenerationOverrides
from src.core.morph_name_sets import JAPANESE_MORPH_NAME_SET_ID, LATIN_MORPH_NAME_SET_ID
from src.core.settings_store import SettingsStore
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir
from tests.test_wx_ms21_b6_undo_redo import make_ready_frame
import wx


def _attach_controller(frame: MainFrame, tmp_dir):
    settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
    preset_store = GenerationPresetStore(
        settings_store=settings_store,
        presets_path=tmp_dir / "presets.json",
    )
    controller = AppController(
        frame,
        settings_store=settings_store,
        preset_store=preset_store,
    )
    frame.set_controller(controller)
    controller.load_startup_state()
    frame.sync_ui_state()
    return controller


def _create_profile(controller: AppController, name: str = "モデルA"):
    return controller.create_model_profile_from_values(
        name,
        JAPANESE_MORPH_NAME_SET_ID,
        None,
        ProfileGenerationOverrides(),
        "builtin:standard-hold",
    )


def test_create_facade_generates_one_canonical_id_and_keeps_runtime_state() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_controller_create") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        before_generation = frame.ui_state.generation_state
        before_profile_state = frame.ui_state.model_profile_state
        result = _create_profile(controller)

        assert result.succeeded is True
        assert len(result.user_profiles) == 1
        profile_id = result.user_profiles[0].id
        assert str(uuid.UUID(profile_id)) == profile_id
        assert controller.profile_store.user_profiles[0].id == profile_id
        assert frame.ui_state.generation_state == before_generation
        assert frame.ui_state.model_profile_state == before_profile_state
        assert frame.ui_state.resolved_morph_upper_limit == 0.5
        assert controller.profile_store.profiles_path.exists()
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_invalid_facade_input_is_non_mutating() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_controller_invalid") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        result = controller.create_model_profile_from_values(
            "不正",
            "builtin:unknown",
            None,
            ProfileGenerationOverrides(),
            "builtin:standard-hold",
        )

        assert result.succeeded is False
        assert result.error_code == "invalid_input"
        assert controller.profile_store.user_profiles == ()
        assert controller.profile_store.profiles_path.exists() is False
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_active_profile_allows_rename_only_and_rejects_value_update_delete() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_controller_active") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        created = _create_profile(controller)
        profile_id = created.user_profiles[0].id
        assert frame.apply_model_profile(profile_id) is True
        before_state = frame.ui_state.model_profile_state

        rename = controller.update_model_profile_from_values(
            profile_id,
            "モデルA改名",
            JAPANESE_MORPH_NAME_SET_ID,
            None,
            ProfileGenerationOverrides(),
            "builtin:standard-hold",
        )
        assert rename.succeeded is True
        assert controller.lookup_model_profile(profile_id).display_name == "モデルA改名"
        assert frame.ui_state.model_profile_state == before_state

        value_update = controller.update_model_profile_from_values(
            profile_id,
            "モデルA値変更",
            LATIN_MORPH_NAME_SET_ID,
            0.8,
            ProfileGenerationOverrides(2, None, "decay"),
            "builtin:standard-hold",
        )
        assert value_update.succeeded is False
        assert value_update.error_code == "active_profile_locked"
        deleted = controller.delete_model_profile(profile_id)
        assert deleted.succeeded is False
        assert deleted.error_code == "active_profile_locked"
        assert frame.ui_state.model_profile_state == before_state
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_inactive_crud_does_not_apply_output() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_controller_inactive") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        before_generation = frame.ui_state.generation_state
        before_profile_state = frame.ui_state.model_profile_state
        created = _create_profile(controller)
        profile_id = created.user_profiles[0].id
        updated = controller.update_model_profile_from_values(
            profile_id,
            "モデルA更新",
            LATIN_MORPH_NAME_SET_ID,
            0.7,
            ProfileGenerationOverrides(None, 4, "decay"),
            "builtin:standard-hold",
        )
        assert updated.succeeded is True
        deleted = controller.delete_model_profile(profile_id)
        assert deleted.succeeded is True
        assert frame.ui_state.generation_state == before_generation
        assert frame.ui_state.model_profile_state == before_profile_state
    destroy_wx_app(app, frame, owns_app=owns_app)
