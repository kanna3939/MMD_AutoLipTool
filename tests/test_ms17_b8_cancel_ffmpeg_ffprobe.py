import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from gui_wx.worker_state import terminate_then_kill
from src.core.ffmpeg_runner import run_ffmpeg_analysis_wav_cancellable
from src.core.ffprobe_runner import run_ffprobe_json_cancellable


class StubbornProcess:
    def __init__(self):
        self.terminated = False
        self.killed = False

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        raise TimeoutError()

    def kill(self):
        self.killed = True


def test_terminate_then_kill_uses_kill_when_process_survives_grace_period():
    process = StubbornProcess()

    terminate_then_kill(process, grace_sec=0.0)

    assert process.terminated is True
    assert process.killed is True


@patch("src.core.ffmpeg_runner.subprocess.Popen")
def test_cancellable_ffmpeg_runner_uses_popen(mock_popen):
    process = MagicMock()
    process.communicate.return_value = ("", "ok")
    process.returncode = 0
    mock_popen.return_value = process

    result = run_ffmpeg_analysis_wav_cancellable(
        ffmpeg_path=Path("ffmpeg.exe"),
        input_path=Path("input.mp3"),
        output_path=Path("output.wav"),
    )

    assert result.returncode == 0
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0][0] == "ffmpeg.exe"
    assert kwargs["shell"] is False
    assert subprocess.PIPE == kwargs["stdout"]


@patch("src.core.ffprobe_runner.subprocess.Popen")
def test_cancellable_ffprobe_runner_uses_popen(mock_popen):
    process = MagicMock()
    process.communicate.return_value = ('{"format": {}}', "")
    process.returncode = 0
    mock_popen.return_value = process

    result = run_ffprobe_json_cancellable(
        ffprobe_path=Path("ffprobe.exe"),
        input_path=Path("input.wav"),
    )

    assert result.returncode == 0
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0][0] == "ffprobe.exe"
    assert "-print_format" in args[0]
    assert kwargs["shell"] is False
