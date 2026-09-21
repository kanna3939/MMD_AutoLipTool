from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from gui_wx.app_controller import (
    AppController,
    _DELIVERY_ERROR_MESSAGES,
)
from gui_wx.ui_state import UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus
from src.core.delivery_package import DeliveryTerminalResult
from tests.test_ms25_b5_delivery_gui import FakeView, _controller


def test_safe_messages_cover_b6_os_and_cleanup_codes():
    for code in (
        "output_permission_denied",
        "output_file_locked",
        "output_path_invalid",
        "output_path_inspection_failed",
        "output_destination_collision",
        "partial_output_cleanup_failed",
    ):
        assert _DELIVERY_ERROR_MESSAGES[code]


def test_delivery_worker_reference_prevents_generic_close_reentry():
    view = FakeView()
    controller = _controller(view)
    worker = MagicMock()
    controller._delivery_worker = worker

    assert controller.delivery_may_be_active is True
    assert controller.request_exit() is False
    worker.cancel.assert_called_once_with()
    assert controller.view is view
    assert controller.delivery_close_pending is True


def test_orphaned_delivery_binding_reconciles_once_before_close():
    view = FakeView()
    view.ui_state.current_audio_job_id = 701
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=701,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = _controller(view)
    controller._active_delivery_binding = (
        701,
        AudioWorkerKind.DELIVERY_PACKAGE,
        1,
    )

    assert controller.delivery_may_be_active is True
    assert controller._reconcile_delivery_close_state() is True
    assert controller.delivery_may_be_active is False
    assert view.ui_state.is_busy is False
    assert view.ui_state.audio_worker_state.status == AudioWorkerStatus.FAILED
    sync_count = view.sync_count

    assert controller._reconcile_delivery_close_state() is True
    assert view.sync_count == sync_count


def test_close_pending_cleanup_warning_omits_staging_path():
    view = FakeView()
    view.ui_state.current_audio_job_id = 702
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=702,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.FINALIZING,
    )
    controller = _controller(view)
    controller._delivery_worker = MagicMock()
    controller._active_delivery_binding = (
        702,
        AudioWorkerKind.DELIVERY_PACKAGE,
        2,
    )
    controller._delivery_close_pending = True
    controller.request_exit = MagicMock(return_value=True)
    residual = Path("C:/private/.MMD_AutoLipTool.delivery-secret.staging")
    result = DeliveryTerminalResult(
        job_id=702,
        primary_status="failed",
        primary_error_code="output_file_locked",
        committed=False,
        final_path=None,
        staging_path=residual,
        cleanup_status="partial_output_cleanup_failed",
        commit_phase="commit_failed",
        artifact_phase="report",
    )

    with patch("gui_wx.app_controller.wx.MessageBox") as message_box:
        controller._on_delivery_worker_terminal(
            702,
            AudioWorkerKind.DELIVERY_PACKAGE,
            2,
            result,
        )

    assert message_box.call_count == 1
    warning_text = message_box.call_args.args[0]
    assert "cleanup" in warning_text
    assert str(residual) not in warning_text
    controller.request_exit.assert_called_once_with()


def test_wrong_terminal_binding_does_not_clear_delivery_busy_state():
    view = FakeView()
    view.ui_state.current_audio_job_id = 703
    view.ui_state.is_busy = True
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=703,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = _controller(view)
    controller._delivery_worker = MagicMock()
    controller._active_delivery_binding = (
        703,
        AudioWorkerKind.DELIVERY_PACKAGE,
        3,
    )
    result = DeliveryTerminalResult(
        job_id=703,
        primary_status="failed",
        primary_error_code="delivery_worker_failed",
        committed=False,
        final_path=None,
        staging_path=None,
        cleanup_status="not_required",
        commit_phase="before_commit",
        artifact_phase=None,
    )

    controller._on_delivery_worker_terminal(
        703,
        AudioWorkerKind.DELIVERY_PACKAGE,
        999,
        result,
    )

    assert view.ui_state.is_busy is True
    assert controller.delivery_may_be_active is True
    assert controller._delivery_worker is not None
