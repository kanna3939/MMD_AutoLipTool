from types import SimpleNamespace
from pathlib import Path

from gui_wx.app_controller import AppController
from gui_wx.ui_state import UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus


class FakeView:
    def __init__(self):
        self.ui_state = UiState()
        self.status = ""
        self.synced = False

    def update_status(self, message):
        self.status = message

    def sync_ui_state(self):
        self.synced = True

    def show_mmd_wav_save_dialog_and_get_path(self, default_dir, default_name):
        return "out.wav"

    def confirm_long_audio_processing(self, duration_sec):
        return True


def test_late_analysis_wav_result_is_discarded_when_audio_job_id_differs():
    view = FakeView()
    view.ui_state.current_audio_job_id = 2
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=2,
        kind=AudioWorkerKind.PROBE,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = AppController.__new__(AppController)
    controller.view = view

    controller._on_analysis_wav_success(
        1,
        {
            "path": "old.wav",
            "input_info": SimpleNamespace(source_path="old.wav"),
            "probe_result": SimpleNamespace(format_name="wav"),
            "analysis_wav_result": object(),
            "waveform_data": SimpleNamespace(samples=[1], duration_sec=1.0),
            "analysis": SimpleNamespace(
                duration_sec=1.0,
                sample_rate_hz=44100,
                channel_count=1,
            ),
        },
    )

    assert view.ui_state.selected_audio_input is None
    assert view.status == ""
    assert view.synced is False


def test_late_mmd_wav_result_is_discarded_when_new_export_job_started():
    view = FakeView()
    view.ui_state.current_audio_job_id = 3
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=3,
        kind=AudioWorkerKind.MMD_WAV,
        status=AudioWorkerStatus.RUNNING,
    )
    controller = AppController.__new__(AppController)
    controller.view = view

    controller._on_mmd_wav_success(
        2,
        SimpleNamespace(mmd_wav_path="old_mmd.wav"),
    )

    assert view.ui_state.last_mmd_wav_output_path is None
    assert view.status == ""
    assert view.synced is False


def test_audio_worker_callback_is_discarded_during_shutdown():
    view = FakeView()
    view.ui_state.current_audio_job_id = 1
    view.ui_state.audio_worker_state = AudioWorkerState(
        audio_job_id=1,
        kind=AudioWorkerKind.MMD_WAV,
        status=AudioWorkerStatus.CANCELLING,
    )
    controller = AppController.__new__(AppController)
    controller.view = view
    controller._is_shutting_down = True

    controller._on_audio_worker_cancelled(1, AudioWorkerKind.MMD_WAV)

    assert view.status == ""
    assert view.synced is False


def test_mmd_wav_export_issues_new_job_id_for_each_export(monkeypatch):
    view = FakeView()
    view.ui_state.current_audio_job_id = 5
    view.ui_state.selected_analysis_wav = object()
    view.ui_state.selected_audio_input = SimpleNamespace(source_path=Path("song.wav"))
    view.ui_state.selected_audio_probe = SimpleNamespace(duration_sec=10.0)
    controller = AppController.__new__(AppController)
    controller.view = view

    captured = {}

    def fake_start(audio_job_id, kind, task, message):
        captured["audio_job_id"] = audio_job_id
        captured["kind"] = kind

    controller._start_audio_worker = fake_start
    controller._confirm_long_audio_if_needed = lambda duration_sec: True
    monkeypatch.setattr(
        "gui_wx.app_controller.locate_ffmpeg_tools",
        lambda: SimpleNamespace(ffmpeg=SimpleNamespace(path=Path("ffmpeg.exe"))),
    )

    controller.request_export_mmd_wav()

    assert captured["audio_job_id"] == 6
    assert view.ui_state.current_audio_job_id == 6
    assert captured["kind"] == AudioWorkerKind.MMD_WAV
