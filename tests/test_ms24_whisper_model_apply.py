from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.model_apply_worker import (
    MODEL_APPLY_STATUS_CANCELLED,
    MODEL_APPLY_STATUS_READY,
    WhisperModelApplyResult,
)
from src.core.generation_presets import GenerationPresetStore
from src.core.settings_store import SettingsStore
from src.core.whisper_model_loader import VerifiedWhisperCheckpoint
from src.core.whisper_model_runtime import (
    ModelIdentity,
    RuntimeCacheIdentity,
    WhisperModelCandidate,
    WhisperModelSession,
)
from src.core.whisper_model_store import ARTIFACT_VERIFIED, ModelAvailability
from src.core import VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir


class _FakeApplyWorker:
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


def _load_controller(frame: MainFrame, tmp_dir: Path) -> AppController:
    settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
    settings = SettingsStore.default_settings()
    settings["whisper_models_dir"] = str((tmp_dir / "models").resolve())
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


def _availability(controller: AppController, tmp_dir: Path, model_key: str) -> ModelAvailability:
    manifest_identity = controller.whisper_model_catalog.manifest_identity(model_key)
    checkpoint = VerifiedWhisperCheckpoint(
        model_key=model_key,
        checkpoint_path=tmp_dir / "models" / f"{model_key}.pt",
        manifest_identity=manifest_identity,
        sha256="a" * 64,
        size_bytes=123,
    )
    return ModelAvailability(
        model_key=model_key,
        artifact_status=ARTIFACT_VERIFIED,
        manifest_identity=manifest_identity,
        storage_root=tmp_dir / "models",
        file_path=checkpoint.checkpoint_path,
        partial_path=None,
        partial_present=False,
        actual_size_bytes=123,
        observed_sha256="a" * 64,
        failure_code=None,
        verified_checkpoint=checkpoint,
    )


def _candidate(controller: AppController, model_key: str) -> WhisperModelCandidate:
    identity = ModelIdentity(
        model_key=model_key,
        manifest_identity=controller.whisper_model_catalog.manifest_identity(model_key),
    )
    cache_identity = RuntimeCacheIdentity(
        model_key=model_key,
        canonical_storage_root="C:\\models",
        manifest_identity=identity.manifest_identity,
    )
    session = WhisperModelSession(
        model=MagicMock(),
        identity=identity,
        cache_identity=cache_identity,
        session_id="candidate-session",
    )
    return WhisperModelCandidate(session=session, generation=1)


def _prepare_state(controller: AppController, frame: MainFrame, tmp_dir: Path) -> None:
    state = frame.ui_state.whisper_model_selection
    small = _availability(controller, tmp_dir, "small")
    medium = _availability(controller, tmp_dir, "medium")
    frame.ui_state.whisper_model_selection = replace(
        state,
        availability=(small, medium),
        availability_scan_status="succeeded",
        selected_model_key="medium",
        active_model_key="small",
        active_manifest_identity=controller.whisper_model_catalog.manifest_identity("small"),
        panel_revision=state.panel_revision + 1,
    )


def test_apply_commits_settings_only_after_candidate_is_ready_and_invalidates_analysis() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    try:
        with workspace_tempdir("ms24_b5_apply") as tmp_dir:
            controller = _load_controller(frame, tmp_dir)
            _prepare_state(controller, frame, tmp_dir)
            frame.ui_state.current_timing_plan = VowelTimingPlan(
                vowels=["あ"],
                timeline=[
                    VowelTimelinePoint(
                        time_sec=0.1,
                        vowel="あ",
                        duration_sec=0.1,
                        start_sec=0.05,
                        end_sec=0.15,
                    )
                ],
                anchors=[],
                source="test",
                observations=[],
            )
            frame.ui_state.analysis_result_valid = True
            frame.ui_state.analysis_pending_rebuild = False
            panel_revision = frame.ui_state.whisper_model_selection.panel_revision
            _FakeApplyWorker.instances.clear()
            with patch("gui_wx.app_controller.WhisperModelApplyWorker", _FakeApplyWorker):
                assert controller.start_whisper_model_apply("medium", panel_revision) is True

            state = frame.ui_state.whisper_model_selection
            assert state.management_busy is True
            assert _FakeApplyWorker.instances[0].started is True
            candidate = _candidate(controller, "medium")
            session = candidate.session
            controller.whisper_model_runtime.commit_candidate = MagicMock(return_value=session)
            controller.whisper_model_runtime.reject_candidate = MagicMock()
            controller._on_whisper_model_apply_result(
                WhisperModelApplyResult(
                    job_id=state.management_job_id,
                    model_key="medium",
                    status=MODEL_APPLY_STATUS_READY,
                    candidate=candidate,
                )
            )

            applied = frame.ui_state.whisper_model_selection
            assert applied.active_model_key == "medium"
            assert applied.loaded_whisper_model_key == "medium"
            assert applied.analysis_rebuild_reason == "model_changed"
            assert applied.management_busy is False
            assert frame.ui_state.current_timing_plan is None
            assert frame.ui_state.analysis_result_valid is False
            saved = controller.settings_store.load().settings
            assert saved["active_whisper_model_key"] == "medium"
            assert saved["selected_whisper_model_key"] == "medium"
            assert saved["active_whisper_manifest_identity"] == session.identity.manifest_identity
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)


def test_apply_cancel_does_not_change_active_identity_and_is_cancelable_from_management_button() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    try:
        with workspace_tempdir("ms24_b5_apply_cancel") as tmp_dir:
            controller = _load_controller(frame, tmp_dir)
            _prepare_state(controller, frame, tmp_dir)
            before = frame.ui_state.whisper_model_selection
            _FakeApplyWorker.instances.clear()
            with patch("gui_wx.app_controller.WhisperModelApplyWorker", _FakeApplyWorker):
                assert controller.start_whisper_model_apply("medium", before.panel_revision) is True
                state = frame.ui_state.whisper_model_selection
                assert controller.request_cancel_whisper_management(
                    state.management_job_id,
                    state.panel_revision,
                ) is True
                assert _FakeApplyWorker.instances[0].cancelled is True

                controller._on_whisper_model_apply_result(
                    WhisperModelApplyResult(
                        job_id=state.management_job_id,
                        model_key="medium",
                        status=MODEL_APPLY_STATUS_CANCELLED,
                    )
                )

            after = frame.ui_state.whisper_model_selection
            assert after.active_model_key == before.active_model_key
            assert after.active_manifest_identity == before.active_manifest_identity
            assert after.management_busy is False
            assert after.management_failure_code == "model_apply_cancelled"
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)


def test_apply_same_verified_active_model_is_rejected() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    try:
        with workspace_tempdir("ms24_b5_apply_same") as tmp_dir:
            controller = _load_controller(frame, tmp_dir)
            state = frame.ui_state.whisper_model_selection
            small = _availability(controller, tmp_dir, "small")
            frame.ui_state.whisper_model_selection = replace(
                state,
                availability=(small,),
                availability_scan_status="succeeded",
                selected_model_key="small",
                active_model_key="small",
                active_manifest_identity=small.manifest_identity,
            )
            assert controller.start_whisper_model_apply(
                "small",
                frame.ui_state.whisper_model_selection.panel_revision,
            ) is False
    finally:
        destroy_wx_app(app, frame, owns_app=owns_app)
