from __future__ import annotations

from unittest.mock import patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.right_pane import WhisperModelSelectRequest
from src.core.generation_presets import GenerationPresetStore
from src.core.settings_store import SettingsStore
from gui_wx.whisper_availability_worker import WhisperAvailabilityScanResult
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir


def _load_startup(
    frame: MainFrame,
    tmp_dir,
    *,
    storage_root: str | None = None,
    settings_overrides: dict | None = None,
):
    settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
    settings = SettingsStore.default_settings()
    if storage_root is not None:
        settings["whisper_models_dir"] = storage_root
    if settings_overrides:
        settings.update(settings_overrides)
    if storage_root is not None or settings_overrides:
        assert settings_store.save(settings).succeeded
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
    startup = controller.load_startup_state()
    frame.apply_settings(
        startup["settings"],
        generation_state=startup["generation_state"],
        active_preset_display_name=startup["active_preset_display_name"],
        model_profile_state=startup["model_profile_state"],
        active_model_profile_display_name=startup[
            "active_model_profile_display_name"
        ],
        baseline_preset_display_name=startup["baseline_preset_display_name"],
        resolved_morph_upper_limit=startup["resolved_morph_upper_limit"],
        whisper_model_selection_state=startup["whisper_model_selection_state"],
    )
    return controller, startup


def test_whisper_candidate_selection_is_not_apply_or_analysis_mutation() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    with workspace_tempdir("ms24_b3_wx_selection") as tmp_dir:
        controller, _ = _load_startup(
            frame,
            tmp_dir,
            storage_root=str((tmp_dir / "models").resolve()),
        )
        before_active = frame.ui_state.whisper_model_selection.active_model_key
        before_analysis = frame.ui_state.analysis_result_valid
        before_revision = frame.ui_state.whisper_model_selection.panel_revision
        panel = frame.right_pane.get_whisper_model_panel_state()

        frame._on_whisper_model_select_request(
            WhisperModelSelectRequest("turbo", panel.panel_revision)
        )

        selected = frame.ui_state.whisper_model_selection
        assert selected.selected_model_key == "turbo"
        assert selected.active_model_key == before_active
        assert selected.availability_scan_status == "pending"
        assert frame.ui_state.analysis_result_valid is before_analysis
        assert selected.panel_revision == before_revision + 1
        assert controller._pending_save is True
        assert frame.right_pane.notebook.FindPage(frame.right_pane.panel_whisper_model) >= 0

        stale_before = frame.ui_state.whisper_model_selection
        frame._on_whisper_model_select_request(
            WhisperModelSelectRequest("medium", panel.panel_revision)
        )
        assert frame.ui_state.whisper_model_selection == stale_before

        frame.ui_state.set_busy(True)
        busy_before = frame.ui_state.whisper_model_selection
        frame._on_whisper_model_select_request(
            WhisperModelSelectRequest("medium", busy_before.panel_revision)
        )
        assert frame.ui_state.whisper_model_selection == busy_before
        frame.ui_state.set_busy(False)
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_invalid_explicit_storage_root_fails_closed_without_worker_or_raw_notice() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    with workspace_tempdir("ms24_b3_invalid_root") as tmp_dir:
        controller, _ = _load_startup(
            frame,
            tmp_dir,
            storage_root=r"\\server\share\models",
        )

        state = frame.ui_state.whisper_model_selection
        assert state.availability_scan_status == "failed"
        assert state.availability_scan_failure_code == "storage_path_remote"
        assert controller.whisper_model_store is None
        assert "ネットワーク" in state.notice
        assert "share" not in frame.right_pane.st_whisper_model_notice.GetLabel()
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_active_manifest_mismatch_is_visible_without_silent_fallback() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    with workspace_tempdir("ms24_b3_active_mismatch") as tmp_dir:
        _, _ = _load_startup(
            frame,
            tmp_dir,
            storage_root=str((tmp_dir / "models").resolve()),
            settings_overrides={
                "active_whisper_model_key": "medium",
                "active_whisper_manifest_identity": "not-the-medium-identity",
            },
        )

        state = frame.ui_state.whisper_model_selection
        assert state.active_model_key == "medium"
        assert state.active_manifest_identity == "not-the-medium-identity"
        assert state.active_config_status == "invalid"
        assert "設定" in state.notice
        assert frame.right_pane.st_whisper_model_active.GetLabel().startswith(
            "現在: 設定不整合"
        )
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_scan_generation_is_independent_from_candidate_panel_revision() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    with workspace_tempdir("ms24_b3_scan_generation") as tmp_dir:
        controller, _ = _load_startup(
            frame,
            tmp_dir,
            storage_root=str((tmp_dir / "models").resolve()),
        )

        class FakeWorker:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.started = False

            def start(self):
                self.started = True

        with patch("gui_wx.app_controller.WhisperAvailabilityWorker", FakeWorker):
            assert controller.start_whisper_availability_scan() is True

        before = frame.ui_state.whisper_model_selection
        frame._on_whisper_model_select_request(
            WhisperModelSelectRequest("turbo", before.panel_revision)
        )
        after_selection = frame.ui_state.whisper_model_selection
        assert after_selection.panel_revision == before.panel_revision + 1

        controller._on_whisper_availability_scan_result(
            WhisperAvailabilityScanResult(
                job_id=after_selection.availability_scan_job_id,
                scan_generation=after_selection.availability_scan_generation,
                availability=(),
            )
        )

        after_scan = frame.ui_state.whisper_model_selection
        assert after_scan.selected_model_key == "turbo"
        assert after_scan.panel_revision == after_selection.panel_revision
        assert after_scan.availability_scan_status == "succeeded"
    destroy_wx_app(app, frame, owns_app=owns_app)
