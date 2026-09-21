from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.output_diagnostics_adapter import (
    resolve_source_audio_path_from_ui_state,
)
from gui_wx.ui_state import UiState
from src.core import (
    AnalysisDiagnosticsSummary,
    DiagnosticItem,
    DiagnosticReportError,
    DiagnosticSeverity,
    GenerationDiagnosticsSummary,
    InputDiagnosticsSummary,
    OutputDiagnosticsSnapshot,
    SaveabilitySummary,
)
from tests.helpers import destroy_wx_app, get_or_create_wx_app


@pytest.fixture(scope="module", autouse=True)
def wx_app():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    try:
        yield app
    finally:
        destroy_wx_app(app, owns_app=owns_app)


def _snapshot(
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
) -> OutputDiagnosticsSnapshot:
    item = DiagnosticItem(
        code="analysis_not_ready",
        severity=severity,
        phase="pipeline_build",
        summary="解析結果がありません。",
        detail="再解析してください。",
    )
    allowed = severity is not DiagnosticSeverity.ERROR
    return OutputDiagnosticsSnapshot(
        input_summary=InputDiagnosticsSummary(
            input_mode="text_audio",
            normalized_text_path=None,
            normalized_source_audio_path="c:/audio/mixed.wav",
            normalized_effective_wav_path="c:/audio/mixed.wav",
            text_content_present=False,
            analysis_text_present=False,
        ),
        analysis_summary=AnalysisDiagnosticsSummary(
            analysis_result_valid=False,
            analysis_pending_rebuild=False,
            timing_source=None,
            anchor_count=0,
            event_count=0,
            max_frame=None,
            timing_warning_present=False,
            observation_fallback_count=0,
        ),
        generation_summary=GenerationDiagnosticsSummary(
            vmd_model_name="AutoLipTool",
            closing_hold_frames=0,
            closing_softness_frames=0,
            fingerprint_schema_version="ms20-output-diagnostics-v1",
        ),
        saveability=SaveabilitySummary(
            vmd_save_allowed=allowed,
            blocking_codes=() if allowed else (item.code,),
            warning_codes=(item.code,) if severity is DiagnosticSeverity.WARNING else (),
        ),
        items=(item,),
        fingerprint_payload=None,
        save_state_fingerprint="sha256:test" if allowed else None,
    )


class _ReportView:
    def __init__(self, snapshot: OutputDiagnosticsSnapshot):
        self.ui_state = UiState()
        self.ui_state.selected_wav_path = r"C:\Audio\MiXeD.WAV"
        self.snapshot = snapshot
        self.dialog_calls: list[tuple[str, str]] = []
        self.output_path: str | None = r"C:\Output\MiXeD_report.txt"
        self.status = ""

    def Bind(self, *args, **kwargs):
        pass

    def update_status(self, message):
        self.status = message

    def build_and_store_output_diagnostics_snapshot(self):
        self.ui_state.current_output_diagnostics_snapshot = self.snapshot
        return self.snapshot

    def show_diagnostic_report_save_dialog_and_get_path(
        self,
        default_dir,
        default_name,
    ):
        self.dialog_calls.append((default_dir, default_name))
        return self.output_path

    def clear_playback_cursor(self):
        pass

    def set_playback_position_sec(self, position):
        pass


class _FakeFileDialog:
    selected_path = ""
    result = wx.ID_OK
    last_kwargs = None

    def __init__(self, *args, **kwargs):
        type(self).last_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ShowModal(self):
        return self.result

    def GetPath(self):
        return self.selected_path


def test_source_audio_resolver_prefers_original_audio_input_path():
    state = UiState()
    state.selected_wav_path = Path("fallback.wav")
    state.selected_audio_input = SimpleNamespace(source_path=Path("Original.MP3"))

    assert resolve_source_audio_path_from_ui_state(state) == Path("Original.MP3")

    state.selected_audio_input = None
    assert resolve_source_audio_path_from_ui_state(state) == Path("fallback.wav")


def test_report_menu_is_independent_from_vmd_saveability(wx_app):
    frame = MainFrame(None)
    try:
        frame.ui_state.selected_wav_path = "input.wav"
        frame.update_action_states()

        assert frame.mi_diagnostic_report_save.IsEnabled()
        assert not frame.mi_vmd_save.IsEnabled()

        frame.ui_state.set_busy(True)
        frame.update_action_states()
        assert not frame.mi_diagnostic_report_save.IsEnabled()

        frame.ui_state.set_busy(False)
        frame.ui_state.reset_workspace()
        frame.update_action_states()
        assert not frame.mi_diagnostic_report_save.IsEnabled()
    finally:
        destroy_wx_app(wx_app, frame, owns_app=False)


def test_report_dialog_uses_defaults_and_appends_txt(tmp_path):
    _FakeFileDialog.selected_path = str(tmp_path / "result")
    _FakeFileDialog.result = wx.ID_OK

    with patch("gui_wx.main_frame.wx.FileDialog", _FakeFileDialog):
        path = MainFrame.show_diagnostic_report_save_dialog_and_get_path(
            object(),
            str(tmp_path),
            "MiXeD_report.txt",
        )

    assert path == str(tmp_path / "result.txt")
    assert _FakeFileDialog.last_kwargs["defaultDir"] == str(tmp_path)
    assert _FakeFileDialog.last_kwargs["defaultFile"] == "MiXeD_report.txt"
    assert _FakeFileDialog.last_kwargs["style"] == wx.FD_SAVE


def test_report_dialog_does_not_duplicate_uppercase_extension(tmp_path):
    _FakeFileDialog.selected_path = str(tmp_path / "result.TXT")
    _FakeFileDialog.result = wx.ID_OK

    with patch("gui_wx.main_frame.wx.FileDialog", _FakeFileDialog):
        path = MainFrame.show_diagnostic_report_save_dialog_and_get_path(
            object(),
            str(tmp_path),
            "input_report.txt",
        )

    assert path == str(tmp_path / "result.TXT")


def test_report_dialog_cancel_and_overwrite_rejection_do_not_return_path(tmp_path):
    _FakeFileDialog.selected_path = str(tmp_path / "result.txt")
    _FakeFileDialog.result = wx.ID_CANCEL
    with patch("gui_wx.main_frame.wx.FileDialog", _FakeFileDialog):
        assert MainFrame.show_diagnostic_report_save_dialog_and_get_path(
            object(),
            str(tmp_path),
            "input_report.txt",
        ) is None

    target = tmp_path / "result.txt"
    target.write_text("existing", encoding="utf-8")
    _FakeFileDialog.result = wx.ID_OK
    with patch("gui_wx.main_frame.wx.FileDialog", _FakeFileDialog):
        with patch("gui_wx.main_frame.wx.MessageBox", return_value=wx.NO):
            assert MainFrame.show_diagnostic_report_save_dialog_and_get_path(
                object(),
                str(tmp_path),
                "input_report.txt",
            ) is None
    assert target.read_text(encoding="utf-8") == "existing"


def test_controller_saves_error_snapshot_without_vmd_warning_confirmation():
    snapshot = _snapshot(DiagnosticSeverity.ERROR)
    view = _ReportView(snapshot)
    controller = AppController(view)

    with patch("gui_wx.app_controller.write_diagnostic_report") as writer:
        controller.request_save_diagnostic_report()

    writer.assert_called_once()
    assert writer.call_args.args[0] is snapshot
    assert writer.call_args.args[1] == view.output_path
    assert writer.call_args.kwargs["generated_at"].utcoffset() is not None
    assert view.dialog_calls == [(r"C:\Audio", "MiXeD_report.txt")]
    assert view.status == "診断レポート保存成功"
    assert view.ui_state.current_output_diagnostics_snapshot is snapshot
    assert view.ui_state.confirmed_warning_save_state_fingerprint is None


def test_controller_warning_report_does_not_use_vmd_confirmation():
    snapshot = _snapshot(DiagnosticSeverity.WARNING)
    view = _ReportView(snapshot)
    controller = AppController(view)

    with patch("gui_wx.app_controller.write_diagnostic_report") as writer:
        controller.request_save_diagnostic_report()

    writer.assert_called_once()
    assert view.status == "診断レポート保存成功"


def test_controller_guards_busy_and_missing_source_before_dialog():
    view = _ReportView(_snapshot())
    controller = AppController(view)
    view.ui_state.set_busy(True)

    with patch("gui_wx.app_controller.write_diagnostic_report") as writer:
        controller.request_save_diagnostic_report()
    writer.assert_not_called()
    assert view.dialog_calls == []

    view.ui_state.set_busy(False)
    view.ui_state.selected_wav_path = None
    with patch("gui_wx.app_controller.write_diagnostic_report") as writer:
        controller.request_save_diagnostic_report()
    writer.assert_not_called()
    assert view.dialog_calls == []
    assert view.status == "診断レポート保存不可"


def test_controller_cancel_does_not_write():
    view = _ReportView(_snapshot())
    view.output_path = None
    controller = AppController(view)

    with patch("gui_wx.app_controller.write_diagnostic_report") as writer:
        controller.request_save_diagnostic_report()

    writer.assert_not_called()
    assert view.status == "診断レポート保存をキャンセルしました"


def test_controller_writer_failure_preserves_diagnostics_state():
    snapshot = _snapshot()
    view = _ReportView(snapshot)
    view.ui_state.current_diagnostic_failure = object()
    view.ui_state.current_timing_plan = object()
    view.ui_state.confirmed_warning_save_state_fingerprint = "sha256:confirmed"
    controller = AppController(view)

    with patch(
        "gui_wx.app_controller.write_diagnostic_report",
        side_effect=DiagnosticReportError("診断レポートを安全に保存できませんでした。"),
    ):
        with patch("gui_wx.app_controller.wx.MessageBox") as message_box:
            controller.request_save_diagnostic_report()

    message_box.assert_called_once()
    assert "診断レポートを安全に保存できませんでした。" in message_box.call_args.args[0]
    assert "locked" not in message_box.call_args.args[0]
    assert view.status == "診断レポート保存失敗"
    assert view.ui_state.current_output_diagnostics_snapshot is snapshot
    assert view.ui_state.current_diagnostic_failure is not None
    assert view.ui_state.current_timing_plan is not None
    assert (
        view.ui_state.confirmed_warning_save_state_fingerprint
        == "sha256:confirmed"
    )
