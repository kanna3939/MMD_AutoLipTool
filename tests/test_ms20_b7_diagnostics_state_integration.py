from unittest.mock import MagicMock, patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.output_diagnostics_adapter import build_output_diagnostics_snapshot_from_ui_state
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, StatusKey, UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus
from src.core import DiagnosticFailureInput, VowelTimingPlan
from src.core.audio_processing import WavAnalysisResult
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _wav_analysis() -> WavAnalysisResult:
    return WavAnalysisResult(
        sample_rate_hz=44100,
        frame_count=44100,
        channel_count=1,
        duration_sec=1.0,
        leading_silence_end_sec=0.1,
        trailing_silence_start_sec=0.9,
        speech_start_sec=0.1,
        speech_end_sec=0.9,
        has_speech=True,
    )


def _timing_plan() -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.2,
                vowel="あ",
                duration_sec=0.2,
                start_sec=0.1,
                end_sec=0.3,
            )
        ],
        anchors=[],
        source="even_fallback",
        observations=[],
    )


def _ready_state(*, with_plan: bool = True) -> UiState:
    state = UiState(
        selected_text_path="input.txt",
        selected_text_content="あ",
        selected_wav_path="voice.wav",
        selected_wav_analysis=_wav_analysis(),
    )
    if with_plan:
        state.mark_analysis_success(
            _timing_plan(),
            input_mode=INPUT_MODE_TEXT_AUDIO,
            analysis_text_content="あ",
            analysis_text_source="text_file",
        )
    else:
        state.mark_ready_for_analysis()
    return state


def _failure() -> DiagnosticFailureInput:
    return DiagnosticFailureInput(
        code="analysis_failure",
        source_severity="error",
        phase="analysis",
        recoverability="retry_possible",
        summary="解析失敗",
    )


def test_diagnostics_clear_discards_every_workspace_local_diagnostic():
    state = _ready_state()
    state.current_diagnostic_failure = _failure()
    state.current_output_diagnostics_snapshot = (
        build_output_diagnostics_snapshot_from_ui_state(state)
    )
    state.confirmed_warning_save_state_fingerprint = "sha256:test"
    state.analysis_cancelled = True

    state.clear_output_diagnostics_state()

    assert state.current_diagnostic_failure is None
    assert state.current_output_diagnostics_snapshot is None
    assert state.confirmed_warning_save_state_fingerprint is None
    assert state.analysis_cancelled is False


def test_adapter_emits_non_blocking_cancel_info_for_reusable_result():
    state = _ready_state()
    state.analysis_cancelled = True

    snapshot = build_output_diagnostics_snapshot_from_ui_state(state)

    assert "analysis_cancelled" in {item.code for item in snapshot.items}
    assert snapshot.saveability.vmd_save_allowed is True


class _AudioView:
    def __init__(self):
        self.ui_state = UiState()
        self.status_messages: list[str] = []
        self.sync_count = 0

    def update_status(self, message: str):
        self.status_messages.append(message)

    def sync_ui_state(self):
        self.sync_count += 1


def _audio_controller(
    *,
    status: AudioWorkerStatus,
    kind: AudioWorkerKind = AudioWorkerKind.PROBE,
) -> tuple[AppController, _AudioView]:
    view = _AudioView()
    view.ui_state.current_audio_job_id = 7
    view.ui_state.status_key = StatusKey.BUSY
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=7,
        kind=kind,
        status=status,
    )
    controller = AppController.__new__(AppController)
    controller.view = view
    controller._is_shutting_down = False
    controller._audio_worker_previous_status_key = StatusKey.READY_FOR_ANALYSIS
    return controller, view


def test_current_audio_cancel_callback_finishes_cancelling_worker_once():
    controller, view = _audio_controller(status=AudioWorkerStatus.CANCELLING)

    controller._on_audio_worker_cancelled(7, AudioWorkerKind.PROBE)

    assert view.ui_state.is_busy is False
    assert view.ui_state.status_key == StatusKey.READY_FOR_ANALYSIS
    assert view.ui_state.audio_worker_state.status == AudioWorkerStatus.CANCELLED
    assert view.sync_count == 1

    controller._on_audio_worker_cancelled(7, AudioWorkerKind.PROBE)

    assert view.sync_count == 1


def test_audio_cancel_callback_rejects_kind_mismatch():
    controller, view = _audio_controller(status=AudioWorkerStatus.CANCELLING)

    controller._on_audio_worker_cancelled(7, AudioWorkerKind.MMD_WAV)

    assert view.ui_state.is_busy is True
    assert view.ui_state.audio_worker_state.status == AudioWorkerStatus.CANCELLING
    assert view.sync_count == 0


def test_late_audio_cancel_callback_does_not_change_current_state():
    controller, view = _audio_controller(status=AudioWorkerStatus.CANCELLING)
    before_worker_state = view.ui_state.audio_worker_state

    controller._on_audio_worker_cancelled(6, AudioWorkerKind.PROBE)

    assert view.ui_state.is_busy is True
    assert view.ui_state.audio_worker_state is before_worker_state
    assert view.sync_count == 0


class TestMS20B7AnalysisCancellationIntegration:
    @classmethod
    def setup_class(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)

    @classmethod
    def teardown_class(cls):
        destroy_wx_app(cls.app, owns_app=cls.owns_app)

    def setup_method(self):
        self.frame = MainFrame(None)
        self.controller = AppController(self.frame)
        self.controller.build_active_whisper_model_request = MagicMock(
            return_value=MagicMock()
        )
        self.frame.set_controller(self.controller)

    def teardown_method(self):
        destroy_wx_app(self.app, self.frame, owns_app=False)

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_cancel_request_keeps_busy_until_current_worker_terminates(
        self,
        mock_worker_class,
        mock_dialog_class,
    ):
        mock_worker_class.return_value = MagicMock()
        self.frame.ui_state = _ready_state()
        self.frame.sync_ui_state()

        self.frame._run_analysis()
        self.frame._on_analysis_cancel()

        assert self.frame._cancel_requested is True
        assert self.frame.ui_state.is_busy is True
        assert self.frame.ui_state.analysis_cancelled is False
        assert self.frame.ui_state.status_key == StatusKey.BUSY

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_terminal_cancel_restores_old_result_with_stable_cancelled_status(
        self,
        mock_worker_class,
        mock_dialog_class,
    ):
        mock_worker_class.return_value = MagicMock()
        self.frame.ui_state = _ready_state()
        old_plan = self.frame.ui_state.current_timing_plan
        self.frame.sync_ui_state()
        self.frame._run_analysis()
        self.frame._on_analysis_cancel()

        self.frame._on_analysis_success(self.frame._current_job_id, MagicMock())

        snapshot = self.frame.ui_state.current_output_diagnostics_snapshot
        assert self.frame.ui_state.current_timing_plan is old_plan
        assert self.frame.ui_state.analysis_cancelled is True
        assert self.frame.ui_state.is_busy is False
        assert self.frame.ui_state.status_key == StatusKey.ANALYSIS_CANCELLED
        assert self.frame.get_status_text() == "解析をキャンセルしました"
        assert "analysis_cancelled" in {item.code for item in snapshot.items}
        assert snapshot.saveability.vmd_save_allowed is True

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_terminal_cancel_without_old_result_keeps_blocking_error_primary(
        self,
        mock_worker_class,
        mock_dialog_class,
    ):
        mock_worker_class.return_value = MagicMock()
        self.frame.ui_state = _ready_state(with_plan=False)
        self.frame.sync_ui_state()
        self.frame._run_analysis()
        self.frame._on_analysis_cancel()

        self.frame._on_analysis_error(
            self.frame._current_job_id,
            RuntimeError("cancelled"),
        )

        snapshot = self.frame.ui_state.current_output_diagnostics_snapshot
        codes = {item.code for item in snapshot.items}
        assert self.frame.ui_state.analysis_cancelled is True
        assert self.frame.ui_state.status_key == StatusKey.ANALYSIS_CANCELLED
        assert "analysis_cancelled" not in codes
        assert snapshot.saveability.vmd_save_allowed is False

    def test_parameter_change_clears_stale_diagnostics_without_valid_result(self):
        self.frame.ui_state = _ready_state(with_plan=False)
        self.frame.ui_state.current_diagnostic_failure = _failure()
        self.frame.ui_state.current_output_diagnostics_snapshot = (
            build_output_diagnostics_snapshot_from_ui_state(self.frame.ui_state)
        )
        self.frame.ui_state.confirmed_warning_save_state_fingerprint = "sha256:test"
        self.frame.ui_state.analysis_cancelled = True
        self.frame.ui_state.status_key = StatusKey.ANALYSIS_CANCELLED

        self.frame._on_param_changed(MagicMock())

        assert self.frame.ui_state.current_diagnostic_failure is None
        assert self.frame.ui_state.confirmed_warning_save_state_fingerprint is None
        assert self.frame.ui_state.analysis_cancelled is False
        assert self.frame.ui_state.status_key == StatusKey.READY_FOR_ANALYSIS

    def test_workspace_reset_clears_cancelled_state(self):
        state = _ready_state()
        state.analysis_cancelled = True
        state.status_key = StatusKey.ANALYSIS_CANCELLED

        state.reset_workspace()

        assert state.analysis_cancelled is False
        assert state.status_key == StatusKey.IDLE

    def test_late_analysis_callbacks_preserve_all_diagnostics_state(self):
        self.frame.ui_state = _ready_state()
        self.frame.ui_state.analysis_cancelled = True
        self.frame.ui_state.status_key = StatusKey.ANALYSIS_CANCELLED
        self.frame.sync_ui_state()
        self.frame.ui_state.confirmed_warning_save_state_fingerprint = "sha256:test"
        self.frame._current_job_id = 10
        before = (
            self.frame.ui_state.current_timing_plan,
            self.frame.ui_state.current_diagnostic_failure,
            self.frame.ui_state.current_output_diagnostics_snapshot,
            self.frame.ui_state.confirmed_warning_save_state_fingerprint,
            self.frame.ui_state.analysis_cancelled,
            self.frame.ui_state.status_key,
            self.frame.right_pane.get_info_text(),
            self.frame.right_pane.get_warning_text(),
            self.frame.get_status_text(),
        )

        self.frame._on_analysis_success(9, _timing_plan())
        self.frame._on_analysis_error(9, RuntimeError("late"))

        after = (
            self.frame.ui_state.current_timing_plan,
            self.frame.ui_state.current_diagnostic_failure,
            self.frame.ui_state.current_output_diagnostics_snapshot,
            self.frame.ui_state.confirmed_warning_save_state_fingerprint,
            self.frame.ui_state.analysis_cancelled,
            self.frame.ui_state.status_key,
            self.frame.right_pane.get_info_text(),
            self.frame.right_pane.get_warning_text(),
            self.frame.get_status_text(),
        )
        assert after == before
