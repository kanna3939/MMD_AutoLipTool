from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import wx

from gui_wx.main_frame import MainFrame
from gui_wx.output_diagnostics_adapter import build_diagnostic_failure_input
from gui_wx.selected_event_editor import SelectedEventEditRequest
from gui_wx.ui_state import StatusKey
from src.core.audio_processing import WavAnalysisResult
from src.core.pipeline import VowelTimingPlan
from src.core.preview_hit_test import PreviewSelectionRequest
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def make_ready_frame() -> MainFrame:
    frame = MainFrame(None)
    frame.ui_state.selected_text_path = "input.txt"
    frame.ui_state.selected_text_content = "あい"
    frame.ui_state.selected_wav_path = "input.wav"
    frame.ui_state.selected_wav_analysis = WavAnalysisResult(
        sample_rate_hz=44100,
        frame_count=441000,
        channel_count=1,
        duration_sec=10.0,
        leading_silence_end_sec=0.0,
        trailing_silence_start_sec=10.0,
        speech_start_sec=0.0,
        speech_end_sec=10.0,
        has_speech=True,
    )
    frame.ui_state.mark_analysis_success(
        VowelTimingPlan(
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
            source="test",
            observations=None,
        ),
        analysis_text_content="あい",
        analysis_text_source="text_file",
    )
    frame.sync_ui_state()
    return frame


def select_and_edit(frame: MainFrame):
    model = frame.placeholder_container.pnl_preview.model
    frame._on_preview_selection_request(
        PreviewSelectionRequest(
            0,
            model.base_plan_identity_digest,
            model.render_revision,
        )
    )
    editor = frame.right_pane._selected_editor_state
    assert editor is not None
    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=editor.base_event_index,
            base_identity_digest=editor.base_identity_digest,
            editor_revision=editor.editor_revision,
            field="peak_value",
            value=0.8,
        )
    )


def begin_fake_analysis(frame: MainFrame):
    frame._current_job_id += 1
    parameters = frame._capture_analysis_parameters()
    assert parameters is not None
    snapshot = frame._capture_analysis_rollback_snapshot(
        job_id=frame._current_job_id,
        parameters=parameters,
    )
    frame._analysis_parameter_snapshot = parameters
    frame._analysis_rollback_snapshot = snapshot
    frame._active_analysis_job_id = frame._current_job_id
    frame._cancel_requested = False
    frame.ui_state.clear_output_diagnostics_state()
    frame._analysis_info_in_progress = True
    frame.ui_state.set_busy(True)
    return frame._current_job_id, snapshot


def test_failure_restores_adjustment_and_retry_cancel_preserves_error():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_and_edit(frame)
    job_id, snapshot = begin_fake_analysis(frame)
    assert snapshot is not None

    with patch("gui_wx.main_frame.wx.MessageBox") as message_box:
        frame._on_analysis_error(job_id, RuntimeError("analysis failed"))

    message_box.assert_called_once()

    assert frame.ui_state.analysis_result_valid is True
    assert frame.ui_state.has_event_adjustments is True
    assert frame.ui_state.current_diagnostic_failure is not None
    assert frame.ui_state.status_key == StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK
    assert any(
        item.severity.value == "ERROR"
        for item in frame.ui_state.current_output_diagnostics_snapshot.items
    )
    assert (
        frame.ui_state.current_output_diagnostics_snapshot
        .saveability.vmd_save_allowed
        is False
    )

    prior_failure = frame.ui_state.current_diagnostic_failure
    retry_job_id, retry_snapshot = begin_fake_analysis(frame)
    assert retry_snapshot is not None
    frame._cancel_requested = True
    frame._on_analysis_success(
        retry_job_id,
        retry_snapshot.timing_plan,
    )

    assert frame.ui_state.current_diagnostic_failure == prior_failure
    assert frame.ui_state.analysis_cancelled is False
    assert frame.ui_state.status_key == StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK
    assert any(
        item.severity.value == "ERROR"
        for item in frame.ui_state.current_output_diagnostics_snapshot.items
    )

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_dirty_editor_rejects_analysis_before_state_changes():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_and_edit(frame)
    frame.ui_state.current_diagnostic_failure = (
        build_diagnostic_failure_input(
            RuntimeError("prior"),
            input_mode=frame.ui_state.input_mode,
        )
    )
    editor = frame.right_pane._selected_editor_state
    assert editor is not None
    frame.right_pane._selected_editor_controls["peak_value"].ChangeValue("0.9")
    old_job_id = frame._current_job_id
    prior_failure = frame.ui_state.current_diagnostic_failure

    with patch("gui_wx.main_frame.AnalysisWorker") as worker:
        frame._run_analysis()

    worker.assert_not_called()
    assert frame._current_job_id == old_job_id
    assert frame.ui_state.current_diagnostic_failure == prior_failure
    assert frame.ui_state.is_busy is False
    assert (
        frame.right_pane.st_selected_event_validation.GetLabel()
        == "Enterで値を確定するか、入力内容を修正してください。"
    )

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_output_only_parameter_change_keeps_analysis_and_rollback():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_and_edit(frame)
    old_plan = frame.ui_state.current_timing_plan
    from src.core.generation_presets import GenerationSettings

    current_settings = frame.ui_state.generation_state.generation_settings
    assert frame.commit_generation_settings(
        GenerationSettings(
            closing_hold_frames=current_settings.closing_hold_frames + 1,
            closing_softness_frames=current_settings.closing_softness_frames,
            long_vowel_mode=current_settings.long_vowel_mode,
        ),
        request_save=False,
    )
    job_id, snapshot = begin_fake_analysis(frame)
    assert snapshot is not None

    frame._on_analysis_success(job_id, old_plan)

    assert frame.ui_state.analysis_result_valid is True
    assert frame.ui_state.current_timing_plan is old_plan
    assert frame.ui_state.has_event_adjustments is False
    assert frame.ui_state.status_key == StatusKey.ANALYSIS_READY
    assert frame.ui_state.is_busy is False

    destroy_wx_app(app, frame, owns_app=owns_app)
