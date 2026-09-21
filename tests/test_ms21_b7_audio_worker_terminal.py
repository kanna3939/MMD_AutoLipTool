from __future__ import annotations

from gui_wx.app_controller import AppController
from gui_wx.ui_state import UiState
from gui_wx.worker_state import (
    AudioWorkerKind,
    AudioWorkerState,
    AudioWorkerStatus,
)


class FakeView:
    def __init__(self):
        self.ui_state = UiState()


def make_controller(
    *,
    kind: AudioWorkerKind,
    status: AudioWorkerStatus,
) -> AppController:
    controller = AppController.__new__(AppController)
    controller.view = FakeView()
    controller._is_shutting_down = False
    controller.view.ui_state.current_audio_job_id = 4
    controller.view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=4,
        kind=kind,
        status=status,
    )
    return controller


def test_result_requires_current_job_kind_and_running_status():
    controller = make_controller(
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )

    assert controller._is_current_audio_worker_result(
        4,
        AudioWorkerKind.PROBE,
    )
    assert not controller._is_current_audio_worker_result(
        3,
        AudioWorkerKind.PROBE,
    )
    assert not controller._is_current_audio_worker_result(
        4,
        AudioWorkerKind.ANALYSIS_WAV,
    )


def test_duplicate_terminal_results_are_rejected():
    for status in (
        AudioWorkerStatus.COMPLETED,
        AudioWorkerStatus.FAILED,
        AudioWorkerStatus.CANCELLED,
        AudioWorkerStatus.DISCARDED,
    ):
        controller = make_controller(
            kind=AudioWorkerKind.MMD_WAV,
            status=status,
        )
        assert not controller._is_current_audio_worker_result(
            4,
            AudioWorkerKind.MMD_WAV,
        )
