from __future__ import annotations

import wx

from gui_wx.app_controller import AppController
from src.core.model_profiles import ProfileGenerationOverrides
from src.core.settings_store import SettingsStore
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir
from tests.test_wx_ms21_b6_undo_redo import make_ready_frame


PROFILE_ID = "33333333-3333-4333-8333-333333333333"


def test_profile_apply_and_undo_restore_profile_context() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms23_b4_profile_runtime") as tmp_dir:
        settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
        controller = AppController(frame, settings_store=settings_store)
        frame.set_controller(controller)
        controller.load_startup_state()
        frame.sync_ui_state()
        created = controller.profile_store.create(
            "Latin profile",
            "builtin:latin-vowels",
            None,
            ProfileGenerationOverrides(),
            "builtin:standard-hold",
            profile_id=PROFILE_ID,
        )
        assert created.succeeded

        assert frame.apply_model_profile(PROFILE_ID) is True
        assert frame.ui_state.analysis_result_valid is True
        assert frame.ui_state.model_profile_state.active_model_profile_id == PROFILE_ID
        assert frame.ui_state.generation_state.active_preset_id is None
        assert frame.ui_state.generation_state.resolved_morph_name_set_id == "builtin:latin-vowels"
        assert frame.ui_state.output_edit_history_state.current_model_profile_state == (
            frame.ui_state.model_profile_state
        )

        assert frame._perform_adjustment_history_navigation(redo=False) is True
        assert frame.ui_state.model_profile_state.active_model_profile_id is None
        assert frame.ui_state.generation_state.resolved_morph_name_set_id == "builtin:japanese-vowels"
    destroy_wx_app(app, frame, owns_app=owns_app)
