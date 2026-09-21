from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gui_wx.app_controller import AppController
from gui_wx.ui_state import UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus
from src.core.delivery_package import (
    DeliveryCommitAuthorization,
    DeliveryTerminalResult,
)
from tests.test_ms25_b1_delivery_contract import _evaluate_ready


class FakeView:
    def __init__(self, *, gate=None):
        self.ui_state = UiState()
        self.statuses = []
        self.sync_count = 0
        self.gate = gate
        self.capture_calls = []
        self.dialog_calls = []
        self.warning_confirmations = 0
        self.long_audio_confirmations = 0

    def update_status(self, message):
        self.statuses.append(message)

    def sync_ui_state(self):
        self.sync_count += 1

    def capture_current_delivery_state(self, **kwargs):
        self.capture_calls.append(kwargs)
        return self.gate

    def show_delivery_destination_dialog(self, parent, folder, **kwargs):
        self.dialog_calls.append((parent, folder, kwargs))
        return self.dialog_selection

    def confirm_vmd_save_warnings(self, snapshot):
        self.warning_confirmations += 1
        return True

    def confirm_long_audio_processing(self, duration):
        self.long_audio_confirmations += 1
        return True


def _controller(view: FakeView) -> AppController:
    controller = AppController.__new__(AppController)
    controller.view = view
    controller._is_shutting_down = False
    controller._audio_worker = None
    controller._delivery_worker = None
    controller._delivery_parent_directory_session = None
    controller._active_delivery_binding = None
    controller._delivery_close_pending = False
    controller._delivery_terminal_received = False
    controller._audio_worker_previous_status_key = None
    controller.update_status = lambda message: view.update_status(message)
    return controller


def test_delivery_start_uses_latest_ready_context_and_session_parent(tmp_path):
    gate, values = _evaluate_ready(tmp_path)
    view = FakeView(gate=gate)
    view.ui_state.last_vmd_output_dir = str(tmp_path)
    view.ui_state.selected_audio_input = SimpleNamespace(
        source_path=values["source_audio_path"]
    )
    view.dialog_selection = (tmp_path, "chosen folder")
    controller = _controller(view)
    captured = {}

    def capture_worker_start(**kwargs):
        captured.update(kwargs)
        return True

    controller._start_delivery_worker = capture_worker_start

    tools = SimpleNamespace(ffmpeg=SimpleNamespace(path=values["ffmpeg_path"]))
    with patch("gui_wx.app_controller.locate_ffmpeg_tools", return_value=tools), patch(
        "gui_wx.app_controller.build_delivery_artifact_operations",
        return_value=object(),
    ):
        assert controller.request_export_delivery_package() is True

    assert captured["start_context"].folder_name == "chosen folder"
    assert captured["start_context"].parent_directory == tmp_path
    assert controller._delivery_parent_directory_session == tmp_path
    assert len(view.capture_calls) == 2
    assert view.long_audio_confirmations == 0


def test_delivery_cancel_after_commit_started_enters_finalizing():
    view = FakeView()
    worker = MagicMock()
    worker.cancel.return_value = False
    view.ui_state.current_audio_job_id = 4
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=4,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = _controller(view)
    controller._delivery_worker = worker
    controller._active_delivery_binding = (
        4,
        AudioWorkerKind.DELIVERY_PACKAGE,
        9,
    )

    assert controller.request_cancel_audio_worker() is False
    assert view.ui_state.audio_worker_state.status == AudioWorkerStatus.FINALIZING
    assert view.ui_state.audio_worker_active
    assert not view.ui_state.audio_worker_cancel_available


def test_delivery_terminal_releases_busy_and_ignores_duplicate():
    view = FakeView()
    view.ui_state.current_audio_job_id = 4
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=4,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.FINALIZING,
    )
    controller = _controller(view)
    controller._delivery_worker = MagicMock()
    controller._active_delivery_binding = (
        4,
        AudioWorkerKind.DELIVERY_PACKAGE,
        9,
    )
    result = DeliveryTerminalResult(
        job_id=4,
        primary_status="success",
        primary_error_code=None,
        committed=True,
        final_path=Path("C:/delivery"),
        staging_path=None,
        cleanup_status="not_required",
        commit_phase="committed",
        artifact_phase="report",
    )

    with patch("gui_wx.app_controller.wx.MessageBox") as message_box:
        controller._on_delivery_worker_terminal(
            4,
            AudioWorkerKind.DELIVERY_PACKAGE,
            9,
            result,
        )
        controller._on_delivery_worker_terminal(
            4,
            AudioWorkerKind.DELIVERY_PACKAGE,
            9,
            result,
        )

    assert view.ui_state.is_busy is False
    assert view.ui_state.audio_worker_state.status == AudioWorkerStatus.COMPLETED
    assert controller._delivery_worker is None
    assert controller._active_delivery_binding is None
    assert message_box.call_count == 0


def test_commit_guard_returns_exact_authorization_for_matching_binding(tmp_path):
    gate, values = _evaluate_ready(tmp_path)
    current_state = gate.candidate_state
    assert current_state is not None
    from datetime import datetime, timezone
    from src.core.delivery_package import build_delivery_start_context

    start_context = build_delivery_start_context(
        current_state,
        tmp_path,
        "delivery",
        datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
    )
    view = FakeView()
    view.ui_state.current_audio_job_id = 17
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=17,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.RUNNING,
    )
    view.build_current_delivery_commit_snapshot = lambda: current_state.diagnostics_snapshot
    controller = _controller(view)
    controller._delivery_worker = MagicMock()
    controller._active_delivery_binding = (
        17,
        AudioWorkerKind.DELIVERY_PACKAGE,
        current_state.projection_generation,
    )
    guard = controller._build_delivery_pre_commit_guard(
        start_context,
        current_state.projection_generation,
    )
    request = SimpleNamespace(
        job_id=17,
        start_fingerprint=current_state.start_fingerprint,
    )
    token = SimpleNamespace(cancel_requested=False)
    with patch(
        "gui_wx.app_controller.wx.CallAfter",
        side_effect=lambda callback, *args: callback(*args),
    ):
        authorization = guard(request, token)

    assert isinstance(authorization, DeliveryCommitAuthorization)
    assert authorization.job_id == request.job_id
    assert authorization.start_fingerprint == request.start_fingerprint
    assert authorization.decision == "authorized"


def test_delivery_start_ignores_finished_generic_worker_reference():
    view = FakeView()
    controller = _controller(view)
    controller._audio_worker = MagicMock()
    controller._build_delivery_pre_commit_guard = MagicMock(
        return_value=lambda request, token: None
    )

    with patch("gui_wx.app_controller.DeliveryPackageWorker") as worker_type:
        assert controller._start_delivery_worker(
            audio_job_id=18,
            projection_generation=3,
            start_context=object(),
            artifact_operations=object(),
        ) is True

    worker_type.assert_called_once()
    worker_type.return_value.start.assert_called_once()
    assert view.ui_state.audio_worker_active


def test_delivery_start_rejects_active_generic_worker_state():
    view = FakeView()
    view.ui_state.current_audio_job_id = 19
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=19,
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )
    view.ui_state.is_busy = True
    controller = _controller(view)
    controller._audio_worker = MagicMock()
    controller._show_delivery_error = MagicMock()

    assert controller._start_delivery_worker(
        audio_job_id=20,
        projection_generation=4,
        start_context=object(),
        artifact_operations=object(),
    ) is False

    controller._show_delivery_error.assert_called_once_with("delivery_busy")


def test_cancel_active_generic_worker_without_reference_fails_closed():
    view = FakeView()
    view.ui_state.current_audio_job_id = 21
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=21,
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = _controller(view)
    controller._audio_worker = None

    assert controller.request_cancel_audio_worker() is False
    assert view.ui_state.is_busy
    assert view.ui_state.audio_worker_active
    assert view.statuses[-1] == (
        "音声処理の状態を確認できないため、キャンセルを実行できません。"
    )


def test_exit_active_generic_worker_without_reference_is_not_allowed():
    view = FakeView()
    view.ui_state.current_audio_job_id = 22
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=22,
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = _controller(view)
    controller._audio_worker = None

    assert controller.request_exit() is False
    assert controller.view is view
    assert view.statuses[-1] == (
        "音声処理の状態を確認できないため、終了を実行できません。"
    )


def test_delivery_active_state_is_detected_without_worker_reference():
    view = FakeView()
    view.ui_state.current_audio_job_id = 23
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=23,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = _controller(view)
    controller._delivery_worker = None
    controller._active_delivery_binding = (
        23,
        AudioWorkerKind.DELIVERY_PACKAGE,
        5,
    )
    controller._show_delivery_error = MagicMock()

    assert controller.is_delivery_active()
    assert controller.request_cancel_audio_worker() is False
    assert view.ui_state.audio_worker_active
    controller._show_delivery_error.assert_called_once_with(
        "delivery_worker_reference_missing"
    )
