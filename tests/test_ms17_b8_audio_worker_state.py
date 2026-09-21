from gui_wx.ui_state import UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus


def test_audio_job_id_increments_and_matches_current_job():
    state = UiState()

    first = state.next_audio_job_id()
    second = state.next_audio_job_id()

    assert first == 1
    assert second == 2
    assert state.is_current_audio_job(second) is True
    assert state.is_current_audio_job(first) is False


def test_audio_worker_active_only_for_running_or_cancelling():
    state = UiState()

    state.audio_worker_state = AudioWorkerState(
        audio_job_id=1,
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )
    assert state.audio_worker_active is True

    state.audio_worker_state.status = AudioWorkerStatus.CANCELLING
    assert state.audio_worker_active is True

    state.audio_worker_state.status = AudioWorkerStatus.COMPLETED
    assert state.audio_worker_active is False
