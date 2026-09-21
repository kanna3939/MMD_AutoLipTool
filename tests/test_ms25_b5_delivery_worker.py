from __future__ import annotations

from pathlib import Path

from gui_wx.audio_worker import DeliveryPackageWorker
from gui_wx.ui_state import UiState
from gui_wx.worker_state import (
    AudioWorkerKind,
    AudioWorkerState,
    AudioWorkerStatus,
)
from src.core.delivery_package import DeliveryTerminalResult


def _success_result(job_id: int) -> DeliveryTerminalResult:
    return DeliveryTerminalResult(
        job_id=job_id,
        primary_status="success",
        primary_error_code=None,
        committed=True,
        final_path=Path("C:/delivery"),
        staging_path=None,
        cleanup_status="not_required",
        commit_phase="committed",
        artifact_phase="report",
    )


def _worker(*, task, callbacks):
    return DeliveryPackageWorker(
        audio_job_id=17,
        projection_generation=8,
        task=task,
        terminal_callback=lambda *args: callbacks.append(("terminal", args)),
        error_callback=lambda *args: callbacks.append(("error", args)),
        call_after=lambda callback, *args: callback(*args),
    )


def test_delivery_state_is_active_and_cancelable_until_finalizing():
    state = UiState()
    state.audio_worker_state = AudioWorkerState(
        audio_job_id=1,
        kind=AudioWorkerKind.DELIVERY_PACKAGE,
        status=AudioWorkerStatus.RUNNING,
    )
    assert state.audio_worker_active
    assert state.audio_worker_cancel_available

    state.audio_worker_state.status = AudioWorkerStatus.FINALIZING
    assert state.audio_worker_active
    assert not state.audio_worker_cancel_available


def test_worker_passes_delivery_token_and_emits_one_terminal_callback():
    callbacks = []
    received_tokens = []

    def task(cancel_token):
        received_tokens.append(cancel_token)
        return _success_result(17)

    worker = _worker(task=task, callbacks=callbacks)
    worker.run()
    worker._emit_terminal(_success_result(17))

    assert len(received_tokens) == 1
    assert len(callbacks) == 1
    kind, args = callbacks[0]
    assert kind == "terminal"
    assert args[:3] == (17, AudioWorkerKind.DELIVERY_PACKAGE, 8)
    assert args[3].committed is True


def test_late_cancel_does_not_reclassify_committed_success():
    callbacks = []
    worker = _worker(task=lambda token: _success_result(17), callbacks=callbacks)

    assert worker.cancel() is True
    worker.run()

    assert len(callbacks) == 1
    assert callbacks[0][0] == "terminal"
    assert callbacks[0][1][3].committed is True


def test_worker_harness_error_uses_error_callback_once():
    callbacks = []
    worker = _worker(
        task=lambda token: (_ for _ in ()).throw(RuntimeError("harness")),
        callbacks=callbacks,
    )

    worker.run()
    worker._emit_error(RuntimeError("duplicate"))

    assert len(callbacks) == 1
    assert callbacks[0][0] == "error"
    assert callbacks[0][1][:3] == (17, AudioWorkerKind.DELIVERY_PACKAGE, 8)


def test_cancel_returns_false_after_commit_started_and_marks_finalizing():
    callbacks = []
    worker = _worker(task=lambda token: _success_result(17), callbacks=callbacks)

    with worker.cancel_token._commit_lock:
        assert worker.cancel_token._begin_commit_locked()
    assert worker.cancel() is False
    assert worker.state.status == AudioWorkerStatus.FINALIZING
