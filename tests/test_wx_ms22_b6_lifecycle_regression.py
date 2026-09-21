from __future__ import annotations

from unittest.mock import patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.analysis_worker import AnalysisWorkerResult
from gui_wx.right_pane import PresetCreateRequest
from gui_wx.ui_state import INPUT_MODE_VOICE_ONLY
from src.core.generation_presets import (
    BUILTIN_LONG_VOWEL_DECAY_ID,
    GenerationPresetStore,
    GenerationSettings,
)
from src.core.settings_store import SettingsStore
from src.core.pipeline import VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
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


def _plan(vowel: str = "う") -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=[vowel],
        timeline=[
            VowelTimelinePoint(
                2.0,
                vowel,
                value=0.7,
                start_sec=1.8,
                end_sec=2.2,
            )
        ],
        anchors=[],
        source="b6-test",
    )


def _begin_terminal_callback(frame: MainFrame, job_id: int) -> None:
    frame._current_job_id = job_id
    frame._active_analysis_job_id = job_id
    frame._analysis_parameter_snapshot = frame._capture_analysis_parameters()
    frame._analysis_rollback_snapshot = None


def test_text_success_replaces_base_and_initializes_new_output_history() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_text_success") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        old_plan = frame.ui_state.current_timing_plan
        _begin_terminal_callback(frame, 41)

        frame._on_analysis_success(
            41,
            AnalysisWorkerResult(
                timing_plan=_plan(),
                input_mode="text_audio",
                analysis_text_content="う",
                analysis_text_source="text_file",
            ),
        )

        assert old_plan is not frame.ui_state.current_timing_plan
        assert frame.ui_state.current_timing_plan == _plan()
        assert frame.ui_state.analysis_result_valid is True
        assert frame.ui_state.output_edit_history_state is not None
        assert frame.ui_state.output_edit_history_state.current_state.base_plan_identity == (
            frame.ui_state.current_output_edit_state.base_plan_identity
        )
        assert frame.ui_state.selected_source_event_index is None
        assert frame.ui_state.is_busy is False
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_voice_only_success_keeps_transcription_and_timing_source() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_voice_success") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        frame.ui_state.selected_text_path = None
        frame.ui_state.selected_text_content = ""
        frame.ui_state.refresh_input_mode()
        assert frame.ui_state.input_mode == INPUT_MODE_VOICE_ONLY
        _begin_terminal_callback(frame, 42)

        frame._on_analysis_success(
            42,
            AnalysisWorkerResult(
                timing_plan=_plan("あ"),
                input_mode=INPUT_MODE_VOICE_ONLY,
                analysis_text_content="あー",
                analysis_text_source="whisper_transcription",
                transcription_text="あー",
                transcription_source="whisper",
                transcription_timing_source="whisper-segments",
                whisper_timing_result=object(),
            ),
        )

        assert frame.ui_state.input_mode == INPUT_MODE_VOICE_ONLY
        assert frame.ui_state.transcription_text == "あー"
        assert frame.ui_state.transcription_original_text == "あー"
        assert frame.ui_state.transcription_timing_source == "whisper-segments"
        assert frame.ui_state.analysis_text_source == "whisper_transcription"
        assert frame.ui_state.analysis_result_valid is True
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_failure_restores_current_job_rollback_and_keeps_diagnostic_failure() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_rollback") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        old_plan = frame.ui_state.current_timing_plan
        parameters = frame._capture_analysis_parameters()
        assert parameters is not None
        snapshot = frame._capture_analysis_rollback_snapshot(
            job_id=43,
            parameters=parameters,
        )
        assert snapshot is not None
        frame._current_job_id = 43
        frame._active_analysis_job_id = 43
        frame._analysis_parameter_snapshot = parameters
        frame._analysis_rollback_snapshot = snapshot

        with patch("wx.MessageBox"):
            frame._on_analysis_error(43, RuntimeError("analysis failed"))

        assert frame.ui_state.current_timing_plan is old_plan
        assert frame.ui_state.analysis_result_valid is True
        assert frame.ui_state.output_edit_history_state == snapshot.output_edit_history_state
        assert frame.ui_state.current_diagnostic_failure is not None
        assert frame.ui_state.is_busy is False
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_morph_upper_mismatch_discards_result_and_invalidates_base_bound_state() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_mismatch") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        _begin_terminal_callback(frame, 44)
        frame.set_morph_upper_limit(0.8)

        frame._on_analysis_success(
            44,
            AnalysisWorkerResult(
                timing_plan=_plan(),
                input_mode="text_audio",
                analysis_text_content="う",
                analysis_text_source="text_file",
            ),
        )

        assert frame.ui_state.analysis_result_valid is False
        assert frame.ui_state.current_timing_plan is None
        assert frame.ui_state.output_edit_history_state is None
        assert frame.ui_state.analysis_pending_rebuild is True
        assert frame.ui_state.is_busy is False
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_late_callback_is_a_noop_for_output_history_and_diagnostics() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_late_callback") as tmp_dir:
        _attach_controller(frame, tmp_dir)
        _begin_terminal_callback(frame, 45)
        before_plan = frame.ui_state.current_timing_plan
        before_history = frame.ui_state.output_edit_history_state
        before_status = frame.ui_state.status_key

        frame._on_analysis_success(
            44,
            AnalysisWorkerResult(
                timing_plan=_plan(),
                input_mode="text_audio",
                analysis_text_content="う",
                analysis_text_source="text_file",
            ),
        )

        assert frame.ui_state.current_timing_plan is before_plan
        assert frame.ui_state.output_edit_history_state == before_history
        assert frame.ui_state.status_key == before_status
        assert frame._active_analysis_job_id == 45
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_workspace_reset_preserves_generation_but_clears_analysis_workspace() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_reset") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        assert controller.apply_generation_preset(BUILTIN_LONG_VOWEL_DECAY_ID)
        generation_before = frame.ui_state.generation_state

        assert controller.request_reset_workspace() is True

        assert frame.ui_state.generation_state == generation_before
        assert frame.ui_state.current_timing_plan is None
        assert frame.ui_state.output_edit_history_state is None
        assert frame.ui_state.selected_source_event_index is None
        assert frame.ui_state.current_diagnostic_failure is None
        assert frame.ui_state.confirmed_warning_save_state_fingerprint is None
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_invalid_ini_startup_uses_safe_defaults_without_session_state() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    with workspace_tempdir("ms22_b6_invalid_ini_gui") as tmp_dir:
        settings_path = tmp_dir / "MMD_AutoLipTool.ini"
        settings_path.write_text("[broken", encoding="utf-8")
        settings_store = SettingsStore(settings_path)
        preset_store = GenerationPresetStore(settings_store=settings_store)
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
        )

        assert startup["settings_result"].had_error is True
        assert frame.ui_state.generation_state.generation_settings == GenerationSettings()
        assert frame.ui_state.generation_state.active_preset_id is None
        assert frame.ui_state.current_timing_plan is None
        assert frame.ui_state.output_edit_history_state is None
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_preset_write_failure_preserves_output_and_disables_user_mutation() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    with workspace_tempdir("ms22_b6_preset_failure_gui") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        before_plan = frame.ui_state.current_timing_plan
        before_history = frame.ui_state.output_edit_history_state
        before_generation = frame.ui_state.generation_state

        with patch("src.core.generation_presets.os.replace", side_effect=OSError("locked")):
            frame._on_preset_create_request(
                PresetCreateRequest(
                    "失敗プリセット",
                    GenerationSettings(3, 4, "decay"),
                    frame._preset_panel_revision,
                )
            )

        assert controller.preset_store.mutation_available is False
        assert frame.ui_state.current_timing_plan is before_plan
        assert frame.ui_state.output_edit_history_state == before_history
        assert frame.ui_state.generation_state == before_generation
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_shutdown_stops_coalesced_save_timer_before_frame_destruction() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    with workspace_tempdir("ms22_b6_shutdown") as tmp_dir:
        controller = _attach_controller(frame, tmp_dir)
        controller.request_settings_save()
        assert controller._pending_save is True
        assert controller._coalesced_save_timer.IsRunning() is True

        controller.request_exit()

        assert controller.view is None
        assert controller._coalesced_save_timer.IsRunning() is False
    destroy_wx_app(app, frame, owns_app=owns_app)
