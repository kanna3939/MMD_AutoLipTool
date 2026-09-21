from unittest.mock import patch

import pytest
import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.output_diagnostics_adapter import (
    build_diagnostic_failure_input,
    build_output_diagnostics_snapshot_from_ui_state,
)
from gui_wx.right_pane import RightPane
from gui_wx.theme import ThemeManager
from gui_wx.ui_state import (
    INPUT_MODE_TEXT_AUDIO,
    INPUT_MODE_VOICE_ONLY,
    UiState,
)
from src.core import (
    AnalysisDiagnosticsSummary,
    DiagnosticFailureInput,
    DiagnosticItem,
    DiagnosticSeverity,
    GenerationDiagnosticsSummary,
    InputDiagnosticsSummary,
    OutputDiagnosticsSnapshot,
    SaveabilitySummary,
)
from src.core.whisper_timing import WhisperTimingError
from tests.helpers import destroy_wx_app, get_or_create_wx_app


@pytest.fixture(scope="module", autouse=True)
def wx_app():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    try:
        yield app
    finally:
        destroy_wx_app(app, owns_app=owns_app)


def _snapshot(
    *items: DiagnosticItem,
    allowed: bool = True,
    fingerprint: str | None = "sha256:test",
) -> OutputDiagnosticsSnapshot:
    blocking_codes = tuple(
        item.code for item in items if item.severity is DiagnosticSeverity.ERROR
    )
    warning_codes = tuple(
        item.code for item in items if item.severity is DiagnosticSeverity.WARNING
    )
    return OutputDiagnosticsSnapshot(
        input_summary=InputDiagnosticsSummary(
            input_mode="text_audio",
            normalized_text_path=None,
            normalized_source_audio_path=None,
            normalized_effective_wav_path=None,
            text_content_present=False,
            analysis_text_present=False,
        ),
        analysis_summary=AnalysisDiagnosticsSummary(
            analysis_result_valid=allowed,
            analysis_pending_rebuild=False,
            timing_source=None,
            anchor_count=0,
            event_count=0,
            max_frame=None,
            timing_warning_present=bool(warning_codes),
            observation_fallback_count=0,
        ),
        generation_summary=GenerationDiagnosticsSummary(
            vmd_model_name="AutoLipTool",
            closing_hold_frames=0,
            closing_softness_frames=0,
            fingerprint_schema_version="ms20-output-diagnostics-v1",
        ),
        saveability=SaveabilitySummary(
            vmd_save_allowed=allowed and not blocking_codes,
            blocking_codes=blocking_codes,
            warning_codes=warning_codes,
        ),
        items=items,
        fingerprint_payload=None,
        save_state_fingerprint=fingerprint,
    )


def _item(severity: DiagnosticSeverity, code: str) -> DiagnosticItem:
    return DiagnosticItem(
        code=code,
        severity=severity,
        phase="pipeline_build",
        summary=f"{code} summary",
        detail=f"{code} detail",
    )


class _SaveView:
    def __init__(self, snapshot: OutputDiagnosticsSnapshot):
        self.ui_state = UiState()
        self.ui_state.analysis_result_valid = True
        self.ui_state.current_timing_plan = object()
        self.ui_state.selected_text_path = "input.txt"
        self.ui_state.selected_wav_path = "input.wav"
        self.snapshot = snapshot
        self.save_path = "output.vmd"
        self.status = ""
        self.dialog_calls = 0
        self.confirm_calls = 0
        self.confirm_result = True

    def Bind(self, *args, **kwargs):
        pass

    def update_status(self, message):
        self.status = message

    def prepare_current_effective_output(self):
        return "ready", self, None

    def build_and_store_output_diagnostics_snapshot(self, **kwargs):
        self.ui_state.current_output_diagnostics_snapshot = self.snapshot
        return self.snapshot

    def confirm_vmd_save_warnings(self, snapshot):
        self.confirm_calls += 1
        return self.confirm_result

    def show_vmd_save_dialog_and_get_path(self, default_dir):
        self.dialog_calls += 1
        return self.save_path

    def get_closing_hold_frames(self):
        return 2

    def get_closing_softness_frames(self):
        return 1

    def get_morph_upper_limit(self):
        return 0.75

    def clear_playback_cursor(self):
        pass

    def set_playback_position_sec(self, position):
        pass


def test_failure_display_fields_do_not_change_fingerprint_identity():
    first = DiagnosticFailureInput(
        code="whisper_failed",
        source_severity="error",
        phase="whisper_transcribe",
        recoverability="retry_possible",
        identity_context=(("exception_type", "WhisperTimingError"),),
        summary="first summary",
        detail="first detail",
    )
    second = DiagnosticFailureInput(
        code=first.code,
        source_severity=first.source_severity,
        phase=first.phase,
        recoverability=first.recoverability,
        identity_context=first.identity_context,
        summary="changed summary",
        detail="changed detail",
    )
    first_item = build_output_diagnostics_snapshot_from_ui_state(
        UiState(current_diagnostic_failure=first)
    ).items
    second_item = build_output_diagnostics_snapshot_from_ui_state(
        UiState(current_diagnostic_failure=second)
    ).items

    first_failure = next(item for item in first_item if item.code == "analysis_failure")
    second_failure = next(item for item in second_item if item.code == "analysis_failure")
    assert first_failure.summary == "first summary"
    assert first_failure.detail == "first detail"
    assert second_failure.summary == "changed summary"
    assert first_failure.identity_context == second_failure.identity_context


def test_voice_only_error_adapter_uses_stable_identity_without_message():
    error = WhisperTimingError("no usable transcription text: volatile detail")
    failure = build_diagnostic_failure_input(error, input_mode=INPUT_MODE_VOICE_ONLY)

    assert failure.code == "voice_only_transcription_empty"
    assert failure.phase == "whisper_transcribe"
    assert "volatile detail" not in repr(failure.identity_context)
    assert "volatile detail" not in failure.detail
    assert failure.detail == failure.summary or "発話が明瞭" in failure.detail


def test_uistate_diagnostics_lifecycle_and_workspace_confirmation():
    state = UiState()
    state.current_diagnostic_failure = build_diagnostic_failure_input(
        RuntimeError("failed"),
        input_mode="text_audio",
    )
    state.current_output_diagnostics_snapshot = _snapshot()
    state.confirmed_warning_save_state_fingerprint = "sha256:old"
    assert not state.has_workspace_user_data

    state.invalidate_analysis()
    assert state.current_diagnostic_failure is None
    assert state.current_output_diagnostics_snapshot is None
    assert state.confirmed_warning_save_state_fingerprint is None

    state.current_diagnostic_failure = build_diagnostic_failure_input(
        RuntimeError("failed again"),
        input_mode="text_audio",
    )
    state.confirmed_warning_save_state_fingerprint = "sha256:old"
    state.mark_analysis_success(object())
    assert state.current_diagnostic_failure is None
    assert state.confirmed_warning_save_state_fingerprint is None

    state.current_diagnostic_failure = build_diagnostic_failure_input(
        RuntimeError("reset failure"),
        input_mode="text_audio",
    )
    state.current_output_diagnostics_snapshot = _snapshot()
    state.confirmed_warning_save_state_fingerprint = "sha256:reset"
    state.reset_workspace()
    assert state.current_diagnostic_failure is None
    assert state.current_output_diagnostics_snapshot is None
    assert state.confirmed_warning_save_state_fingerprint is None


def test_warning_panel_displays_all_severities_in_snapshot_order(wx_app):
    frame = wx.Frame(None)
    pane = RightPane(frame)
    snapshot = _snapshot(
        _item(DiagnosticSeverity.ERROR, "error_code"),
        _item(DiagnosticSeverity.WARNING, "warning_code"),
        _item(DiagnosticSeverity.INFO, "info_code"),
        allowed=False,
    )
    pane.set_warning_snapshot(snapshot)

    labels = pane.get_warning_row_labels()
    assert [summary for summary, _ in labels] == [
        "[ERROR] error_code summary",
        "[WARNING] warning_code summary",
        "[INFO] info_code summary",
    ]
    assert all(detail.endswith(" detail") for _, detail in labels)
    assert all(row[1].GetFont().GetWeight() == wx.FONTWEIGHT_BOLD for row in pane._warning_rows)
    destroy_wx_app(wx_app, frame, owns_app=False)


def test_warning_panel_reuses_rows_and_reapplies_theme(wx_app):
    frame = wx.Frame(None)
    pane = RightPane(frame)
    snapshot = _snapshot(
        _item(DiagnosticSeverity.ERROR, "error_code"),
        _item(DiagnosticSeverity.WARNING, "warning_code"),
        _item(DiagnosticSeverity.INFO, "info_code"),
        allowed=False,
    )
    pane.set_warning_snapshot(snapshot)
    original_label = pane._warning_rows[0][1]
    pane.set_warning_snapshot(snapshot)
    assert pane._warning_rows[0][1] is original_label

    ThemeManager.apply_theme("light", frame)
    pane.refresh_warning_styles()
    palette = ThemeManager.get_palette()
    assert pane._warning_rows[0][1].GetForegroundColour() == palette.error_text
    assert pane._warning_rows[1][1].GetForegroundColour() == palette.attention_text
    assert pane._warning_rows[2][1].GetForegroundColour() == palette.text_fg

    ThemeManager.apply_theme("dark", frame)
    pane.refresh_warning_styles()
    palette = ThemeManager.get_palette()
    assert pane._warning_rows[0][1].GetForegroundColour() == palette.error_text
    assert pane._warning_rows[1][1].GetForegroundColour() == palette.attention_text
    destroy_wx_app(wx_app, frame, owns_app=False)


def test_main_frame_sync_resolves_input_mode_and_builds_snapshot_once(wx_app):
    frame = MainFrame(None)
    state = frame.ui_state
    state.selected_text_path = None
    state.selected_text_content = ""
    state.selected_wav_path = "voice.wav"
    state.selected_wav_analysis = object()
    state.input_mode = INPUT_MODE_TEXT_AUDIO

    with patch(
        "gui_wx.main_frame.build_output_diagnostics_snapshot_from_ui_state",
        wraps=build_output_diagnostics_snapshot_from_ui_state,
    ) as builder:
        frame.sync_ui_state()

    assert builder.call_count == 1
    assert state.input_mode == INPUT_MODE_VOICE_ONLY
    assert state.current_output_diagnostics_snapshot is not None
    assert state.current_output_diagnostics_snapshot.input_summary.input_mode == INPUT_MODE_VOICE_ONLY
    assert frame.right_pane.get_warning_text()
    destroy_wx_app(wx_app, frame, owns_app=False)


def test_error_snapshot_blocks_controller_before_dialog():
    view = _SaveView(_snapshot(_item(DiagnosticSeverity.ERROR, "blocked"), allowed=False))
    controller = AppController(view)
    with patch("gui_wx.app_controller.generate_vmd_from_text_wav") as writer:
        controller.request_save_vmd()
    assert view.dialog_calls == 0
    writer.assert_not_called()
    assert view.status == "VMD保存不可"


def test_warning_yes_is_reused_for_same_fingerprint():
    view = _SaveView(_snapshot(_item(DiagnosticSeverity.WARNING, "fallback")))
    controller = AppController(view)
    with patch("gui_wx.app_controller.generate_vmd_from_text_wav") as writer:
        controller.request_save_vmd()
        controller.request_save_vmd()
    assert view.confirm_calls == 1
    assert view.dialog_calls == 2
    assert writer.call_count == 2
    assert view.ui_state.confirmed_warning_save_state_fingerprint == "sha256:test"


def test_warning_no_does_not_confirm_or_open_save_dialog():
    view = _SaveView(_snapshot(_item(DiagnosticSeverity.WARNING, "fallback")))
    view.confirm_result = False
    controller = AppController(view)
    controller.request_save_vmd()
    controller.request_save_vmd()
    assert view.confirm_calls == 2
    assert view.dialog_calls == 0
    assert view.ui_state.confirmed_warning_save_state_fingerprint is None


def test_warning_fingerprint_change_requires_confirmation_again():
    view = _SaveView(_snapshot(_item(DiagnosticSeverity.WARNING, "fallback")))
    controller = AppController(view)
    with patch("gui_wx.app_controller.generate_vmd_from_text_wav"):
        controller.request_save_vmd()
        view.snapshot = _snapshot(
            _item(DiagnosticSeverity.WARNING, "fallback"),
            fingerprint="sha256:changed",
        )
        controller.request_save_vmd()
    assert view.confirm_calls == 2
    assert view.ui_state.confirmed_warning_save_state_fingerprint == "sha256:changed"


def test_warning_confirmation_survives_path_cancel_and_writer_failure():
    view = _SaveView(_snapshot(_item(DiagnosticSeverity.WARNING, "fallback")))
    controller = AppController(view)
    view.save_path = None
    controller.request_save_vmd()
    assert view.ui_state.confirmed_warning_save_state_fingerprint == "sha256:test"

    view.save_path = "output.vmd"
    original_plan = view.ui_state.current_timing_plan
    with patch(
        "gui_wx.app_controller.generate_vmd_from_text_wav",
        side_effect=OSError("write failed"),
    ), patch("gui_wx.app_controller.wx.MessageBox"):
        controller.request_save_vmd()
    assert view.confirm_calls == 1
    assert view.ui_state.current_timing_plan is original_plan
    assert view.ui_state.analysis_result_valid
    assert view.ui_state.confirmed_warning_save_state_fingerprint == "sha256:test"
    assert view.status == "VMD保存失敗"


def test_warning_without_fingerprint_fails_closed():
    view = _SaveView(
        _snapshot(
            _item(DiagnosticSeverity.WARNING, "fallback"),
            fingerprint=None,
        )
    )
    controller = AppController(view)
    controller.request_save_vmd()
    assert view.confirm_calls == 0
    assert view.dialog_calls == 0
    assert view.status == "VMD保存不可"
