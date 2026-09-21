from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.whisper_availability_worker import WhisperAvailabilityScanResult
from src.core.generation_presets import GenerationPresetStore
from src.core.settings_store import SettingsStore
from gui_wx.model_download_worker import (
    MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
    MODEL_MANAGEMENT_STATUS_SUCCEEDED,
    ModelManagementResult,
)
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir


def _load_controller(frame: MainFrame, tmp_dir: Path, settings: dict | None = None):
    settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
    if settings:
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
        active_model_profile_display_name=startup["active_model_profile_display_name"],
        baseline_preset_display_name=startup["baseline_preset_display_name"],
        resolved_morph_upper_limit=startup["resolved_morph_upper_limit"],
        whisper_model_selection_state=startup["whisper_model_selection_state"],
    )
    return controller


class _FakeAvailabilityWorker:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True


class _FakeManagementWorker:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False
        self.cancelled = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True


def test_rescan_is_reusable_and_invalidates_old_scan_result() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    try:
        with workspace_tempdir("ms24_b4_rescan") as tmp_dir:
            settings = SettingsStore.default_settings()
            settings["whisper_models_dir"] = str((tmp_dir / "models").resolve())
            controller = _load_controller(frame, tmp_dir, settings)
            _FakeAvailabilityWorker.instances.clear()
            with patch(
                "gui_wx.app_controller.WhisperAvailabilityWorker",
                _FakeAvailabilityWorker,
            ):
                assert controller.start_whisper_availability_scan() is True
                first = frame.ui_state.whisper_model_selection
                assert controller.start_whisper_availability_rescan() is True
                second = frame.ui_state.whisper_model_selection

            assert len(_FakeAvailabilityWorker.instances) == 2
            assert second.availability_scan_job_id > first.availability_scan_job_id
            stale = WhisperAvailabilityScanResult(
                job_id=first.availability_scan_job_id,
                scan_generation=first.availability_scan_generation,
                availability=(),
            )
            controller._on_whisper_availability_scan_result(stale)
            assert frame.ui_state.whisper_model_selection.availability_scan_job_id == (
                second.availability_scan_job_id
            )
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)


def test_storage_root_change_merges_settings_and_keeps_model_identities() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    try:
        with workspace_tempdir("ms24_b4_storage_root") as tmp_dir:
            settings = SettingsStore.default_settings()
            settings.update(
                {
                    "theme": "system",
                    "window_width": 1440,
                    "recent_text_files": [r"C:\work\sample.txt"],
                    "whisper_models_dir": str((tmp_dir / "old_models").resolve()),
                }
            )
            controller = _load_controller(frame, tmp_dir, settings)
            before = frame.ui_state.whisper_model_selection
            new_root = (tmp_dir / "new_models").resolve()
            _FakeAvailabilityWorker.instances.clear()
            with patch(
                "gui_wx.app_controller.WhisperAvailabilityWorker",
                _FakeAvailabilityWorker,
            ):
                assert controller.change_whisper_storage_root(
                    str(new_root),
                    before.panel_revision,
                    confirmed=True,
                ) is True

            loaded = controller.settings_store.load().settings
            after = frame.ui_state.whisper_model_selection
            assert loaded["theme"] == "system"
            assert loaded["window_width"] == 1440
            assert loaded["recent_text_files"] == [r"C:\work\sample.txt"]
            assert loaded["whisper_models_dir"] == str(new_root.resolve())
            assert after.storage_root_display == str(new_root.resolve())
            assert after.selected_model_key == before.selected_model_key
            assert after.active_model_key == before.active_model_key
            assert after.active_manifest_identity == before.active_manifest_identity
            assert after.availability_scan_status == "pending"
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)


def test_download_requires_confirmation_and_does_not_change_active_identity() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    try:
        with workspace_tempdir("ms24_b4_download_request") as tmp_dir:
            settings = SettingsStore.default_settings()
            settings["whisper_models_dir"] = str((tmp_dir / "models").resolve())
            controller = _load_controller(frame, tmp_dir, settings)
            before = frame.ui_state.whisper_model_selection
            panel = frame.right_pane.get_whisper_model_panel_state()
            _FakeManagementWorker.instances.clear()
            with patch(
                "gui_wx.app_controller.WhisperModelManagementWorker",
                _FakeManagementWorker,
            ):
                assert controller.start_whisper_model_download(
                    "small",
                    panel.panel_revision,
                    confirmed=False,
                ) is False
                assert not _FakeManagementWorker.instances
                assert controller.start_whisper_model_download(
                    "small",
                    panel.panel_revision,
                    confirmed=True,
                ) is True

            current = frame.ui_state.whisper_model_selection
            assert current.management_busy is True
            assert current.management_operation == MODEL_MANAGEMENT_OPERATION_DOWNLOAD
            assert current.active_model_key == before.active_model_key
            assert current.analysis_whisper_model_key == before.analysis_whisper_model_key
            assert _FakeManagementWorker.instances[0].started is True
            job_id = current.management_job_id
            controller._on_whisper_management_result(
                ModelManagementResult(
                    job_id=job_id,
                    operation=MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
                    model_key="small",
                    status=MODEL_MANAGEMENT_STATUS_SUCCEEDED,
                    cleanup_status="promoted",
                )
            )
            after = frame.ui_state.whisper_model_selection
            assert after.active_model_key == before.active_model_key
            assert after.analysis_whisper_model_key == before.analysis_whisper_model_key
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)
