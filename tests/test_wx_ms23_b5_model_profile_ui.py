from __future__ import annotations

from unittest.mock import patch

import wx

from gui_wx.analysis_worker import AnalysisWorkerResult
from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.right_pane import (
    ModelProfileApplyRequest,
    ModelProfileCreateRequest,
    ModelProfileEditorValues,
    ModelProfileSelectRequest,
)
from src.core.generation_presets import GenerationPresetStore
from src.core.model_profiles import ProfileGenerationOverrides
from src.core.morph_name_sets import LATIN_MORPH_NAME_SET_ID
from src.core.pipeline import VowelTimingPlan
from src.core.settings_store import SettingsStore
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir
from tests.test_wx_ms21_b6_undo_redo import make_ready_frame


class _Event:
    def Skip(self) -> None:
        return None


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


def _values(name: str = "英字モデル") -> ModelProfileEditorValues:
    return ModelProfileEditorValues(
        display_name=name,
        morph_name_set_id=LATIN_MORPH_NAME_SET_ID,
        morph_upper_limit=None,
        generation_overrides=ProfileGenerationOverrides(),
        default_preset_id="builtin:standard-hold",
    )


def _create_through_frame(frame: MainFrame, name: str = "英字モデル") -> str:
    revision = frame._model_profile_panel_revision
    frame._on_model_profile_create_request(
        ModelProfileCreateRequest(_values(name), revision)
    )
    selected = frame.right_pane.get_model_profile_panel_state().selected_profile_id
    assert selected is not None
    return selected


def test_select_is_preview_only_and_create_selects_without_apply() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_select") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        before_generation = frame.ui_state.generation_state
        before_plan = frame.ui_state.current_timing_plan
        before_history = frame.ui_state.output_edit_history_state
        profile_id = _create_through_frame(frame)

        assert frame.ui_state.generation_state == before_generation
        assert frame.ui_state.current_timing_plan is before_plan
        assert frame.ui_state.output_edit_history_state == before_history
        assert frame.ui_state.model_profile_state.active_model_profile_id is None
        assert controller.lookup_model_profile(profile_id) is not None

        frame._on_model_profile_select_request(
            ModelProfileSelectRequest(
                None,
                frame._model_profile_panel_revision,
            )
        )
        assert frame.right_pane.get_model_profile_panel_state().selected_profile_id is None
        assert frame.ui_state.generation_state == before_generation
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_apply_profile_and_no_profile_projection_lock_and_restore_controls() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_apply") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        profile_id = _create_through_frame(frame)
        frame._on_model_profile_apply_request(
            ModelProfileApplyRequest(
                profile_id,
                frame._model_profile_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )

        assert frame.ui_state.model_profile_state.active_model_profile_id == profile_id
        assert frame.ui_state.generation_state.resolved_morph_name_set_id == LATIN_MORPH_NAME_SET_ID
        assert frame.param_panel.sc_morph_limit.IsEnabled() is False
        assert frame.right_pane.btn_delete_model_profile.IsEnabled() is False
        assert frame.right_pane.btn_update_model_profile.IsEnabled() is True
        assert controller.lookup_model_profile(profile_id).display_name == "英字モデル"

        frame._on_model_profile_select_request(
            ModelProfileSelectRequest(None, frame._model_profile_panel_revision)
        )
        frame._on_model_profile_apply_request(
            ModelProfileApplyRequest(
                None,
                frame._model_profile_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )
        assert frame.ui_state.model_profile_state.active_model_profile_id is None
        assert frame.ui_state.generation_state.resolved_morph_name_set_id == "builtin:japanese-vowels"
        assert frame.param_panel.sc_morph_limit.IsEnabled() is True
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_create_uses_inherit_first_values_and_cancel_is_non_mutating() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_dialog") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        captured = {}

        def capture_dialog(**kwargs):
            captured.update(kwargs)
            return None

        before_ids = tuple(frame.controller.profile_store.user_profiles)
        before_generation = frame.ui_state.generation_state
        with patch.object(frame.right_pane, "_show_model_profile_dialog", side_effect=capture_dialog):
            frame.right_pane._on_create_model_profile(_Event())

        initial = captured["initial_values"]
        assert initial.display_name == ""
        assert initial.morph_name_set_id == "builtin:japanese-vowels"
        assert initial.morph_upper_limit is None
        assert initial.generation_overrides == ProfileGenerationOverrides()
        assert initial.default_preset_id == "builtin:standard-hold"
        assert tuple(frame.controller.profile_store.user_profiles) == before_ids
        assert frame.ui_state.generation_state == before_generation
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_delete_button_removes_selected_profile_after_wx_yes() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_delete") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        profile_id = _create_through_frame(frame)
        profile = controller.lookup_model_profile(profile_id)
        assert profile is not None

        with patch("wx.MessageBox", return_value=wx.ID_YES):
            frame.right_pane._on_delete_model_profile(_Event())

        assert controller.lookup_model_profile(profile_id) is None
        assert profile.display_name not in frame.right_pane.choice_model_profile.GetStrings()
        assert frame.right_pane.choice_model_profile.GetSelection() == 0
        assert profile_id not in {
            item.id
            for item in frame.right_pane.get_model_profile_panel_state().items
        }
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_latin_morph_names_remain_visible_after_reanalysis_success() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_latin_reanalysis") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        profile_id = _create_through_frame(frame)
        frame._on_model_profile_apply_request(
            ModelProfileApplyRequest(
                profile_id,
                frame._model_profile_panel_revision,
                frame.ui_state.selected_event_editor_revision,
            )
        )

        frame._current_job_id = 1
        frame._active_analysis_job_id = 1
        frame._analysis_parameter_snapshot = frame._capture_analysis_parameters()
        result = AnalysisWorkerResult(
            timing_plan=VowelTimingPlan(
                vowels=["あ", "い"],
                timeline=[
                    VowelTimelinePoint(
                        1.0,
                        "あ",
                        value=0.6,
                        start_sec=0.8,
                        end_sec=1.1,
                    ),
                    VowelTimelinePoint(
                        1.4,
                        "い",
                        value=0.4,
                        start_sec=1.2,
                        end_sec=1.6,
                    ),
                ],
                anchors=[],
                source="reanalysis-test",
                observations=None,
            ),
            input_mode="text_audio",
            analysis_text_content="あい",
            analysis_text_source="text_file",
        )

        frame._on_analysis_success(1, result)

        model = frame.placeholder_container.pnl_preview.model
        assert tuple(row.display_name for row in model.data.rows) == (
            "A",
            "I",
            "U",
            "E",
            "O",
        )
        assert sum(len(row.segments) for row in model.data.rows) == 2
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_profile_editor_dialog_constructs_spin_double_with_wx_api() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_dialog_spin") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        state = frame.right_pane.get_model_profile_panel_state()
        values = ModelProfileEditorValues(
            display_name="",
            morph_name_set_id="builtin:japanese-vowels",
            morph_upper_limit=None,
            generation_overrides=ProfileGenerationOverrides(),
            default_preset_id="builtin:standard-hold",
        )
        with patch.object(wx.Dialog, "ShowModal", return_value=wx.ID_CANCEL):
            result = frame.right_pane._show_model_profile_dialog(
                title="モデルプロファイルを作成",
                initial_values=values,
                current_upper=state.active_morph_upper_limit,
                current_settings=state.active_generation_settings,
                active_locked=False,
            )
        assert result is None
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_stale_profile_request_and_broken_profile_file_fail_closed() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b5_wx_failure") as tmp_dir:
        profiles_path = tmp_dir / "profiles.json"
        profiles_path.write_text("{broken", encoding="utf-8")
        settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
        preset_store = GenerationPresetStore(
            settings_store=settings_store,
            presets_path=tmp_dir / "presets.json",
        )
        from src.core.model_profiles import ModelProfileStore

        controller = AppController(
            frame,
            settings_store=settings_store,
            preset_store=preset_store,
            profile_store=ModelProfileStore(
                settings_store=settings_store,
                profiles_path=profiles_path,
            ),
        )
        frame.set_controller(controller)
        controller.load_startup_state()
        frame.sync_ui_state()

        before = frame.ui_state.generation_state
        stale_revision = frame._model_profile_panel_revision - 1
        frame._on_model_profile_apply_request(
            ModelProfileApplyRequest(None, stale_revision, frame.ui_state.selected_event_editor_revision)
        )
        assert frame.ui_state.generation_state == before
        assert controller.profile_store.mutation_available is False
        assert frame.right_pane.btn_create_model_profile.IsEnabled() is False
        assert frame.right_pane.choice_model_profile.GetCount() == 1
    destroy_wx_app(app, frame, owns_app=owns_app)
