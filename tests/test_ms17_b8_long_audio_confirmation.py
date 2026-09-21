from types import SimpleNamespace

from gui_wx.app_controller import AppController
from gui_wx.ui_state import StatusKey, UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus


class FakeView:
    def __init__(self):
        self.ui_state = UiState()
        self.confirm_calls = []
        self.status = ""

    def confirm_long_audio_processing(self, duration_sec):
        self.confirm_calls.append(duration_sec)
        return False

    def sync_ui_state(self):
        pass

    def update_status(self, message):
        self.status = message


def test_long_audio_confirmation_cancel_stops_before_analysis_wav_worker():
    view = FakeView()
    view.ui_state.current_audio_job_id = 1
    view.ui_state.status_key = StatusKey.ANALYSIS_INVALIDATED
    view.ui_state.set_busy(True)
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=1,
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )

    controller = AppController.__new__(AppController)
    controller.view = view
    controller._audio_worker = object()
    controller._audio_worker_previous_status_key = StatusKey.ANALYSIS_INVALIDATED

    result = {
        "path": "long.wav",
        "input_info": object(),
        "ffmpeg_tools": object(),
        "probe_result": SimpleNamespace(duration_sec=301.0),
    }

    controller._on_audio_probe_success(1, result)

    assert view.confirm_calls == [301.0]
    assert view.ui_state.is_busy is False
    assert view.ui_state.audio_worker_state.status == AudioWorkerStatus.CANCELLED
    assert view.status == "音声読み込みをキャンセルしました"
