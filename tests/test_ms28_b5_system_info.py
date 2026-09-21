from __future__ import annotations

import io
import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core import system_info
from src.core.system_info import (
    NOT_AVAILABLE,
    NOT_LOADED,
    SystemInfoSnapshot,
    collect_system_info,
)
from gui_wx.system_info_worker import SystemInfoWorker


class _FakeProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = 0
        self.killed = False

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class _TimeoutProcess(_FakeProcess):
    def __init__(self) -> None:
        super().__init__()
        self.wait_calls = 0

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.wait_calls == 1:
            raise system_info.subprocess.TimeoutExpired("fake", timeout)
        return self.returncode


class TestMS28B5SystemInfo(unittest.TestCase):
    def test_collect_system_info_keeps_fixed_partial_failure_values(self):
        with (
            patch.object(system_info, "_collect_app_version", return_value="1.0.0"),
            patch.object(
                system_info,
                "_collect_whisper_info",
                return_value=(NOT_LOADED, NOT_LOADED),
            ),
            patch.object(
                system_info,
                "_collect_ffmpeg_version",
                return_value=NOT_AVAILABLE,
            ),
            patch.object(system_info, "_collect_cpu_name", return_value="CPU"),
            patch.object(system_info, "_collect_cpu_logical_count", return_value=8),
            patch.object(
                system_info,
                "_collect_memory_total_gib",
                return_value=NOT_AVAILABLE,
            ),
            patch.object(
                system_info,
                "_collect_gpu_names",
                return_value=(NOT_AVAILABLE,),
            ),
        ):
            snapshot = collect_system_info()

        self.assertEqual(snapshot.app_version, "1.0.0")
        self.assertEqual(snapshot.whisper_status, NOT_LOADED)
        self.assertEqual(snapshot.ffmpeg_version, NOT_AVAILABLE)
        self.assertEqual(snapshot.cpu_logical_count, 8)
        self.assertEqual(snapshot.memory_total_gib, NOT_AVAILABLE)
        self.assertEqual(snapshot.gpu_names, (NOT_AVAILABLE,))

    def test_whisper_is_not_imported_for_about(self):
        with patch.dict(sys.modules, {}, clear=False):
            sys.modules.pop("whisper", None)
            self.assertEqual(system_info._collect_whisper_info(), (NOT_LOADED, NOT_LOADED))

    def test_whisper_loaded_version_is_reported(self):
        module = SimpleNamespace(__version__="20250625")
        with patch.dict(sys.modules, {"whisper": module}):
            self.assertEqual(
                system_info._collect_whisper_info(),
                ("20250625", "loaded"),
            )

    def test_gpu_names_are_deduplicated(self):
        process = _FakeProcess(stdout=b"GPU A\r\nGPU A\r\nGPU B\r\n")
        with (
            patch.object(system_info.shutil, "which", return_value="powershell.exe"),
            patch.object(system_info, "_run_external_command", return_value=system_info._ProcessResult(0, process.stdout.getvalue(), b"")),
        ):
            self.assertEqual(system_info._collect_gpu_names(), ("GPU A", "GPU B"))

    def test_external_command_uses_fixed_windowless_process_and_caps_output(self):
        process = _FakeProcess(stdout=b"x" * 10, stderr=b"y" * 2)
        with patch.object(system_info.subprocess, "Popen", return_value=process) as popen:
            result = system_info._run_external_command(
                ("fixed.exe", "-version"),
                output_limit=4,
            )

        kwargs = popen.call_args.kwargs
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["stdin"], system_info.subprocess.DEVNULL)
        self.assertEqual(kwargs["creationflags"], getattr(system_info.subprocess, "CREATE_NO_WINDOW", 0))
        self.assertIsNotNone(result)
        self.assertEqual(len(result.stdout), 4)
        self.assertTrue(result.output_exceeded)

    def test_external_command_timeout_is_reported(self):
        process = _TimeoutProcess()
        with patch.object(system_info.subprocess, "Popen", return_value=process):
            result = system_info._run_external_command(("fixed.exe", "-version"))

        self.assertTrue(result.timed_out)
        self.assertTrue(process.killed)

    def test_worker_success_uses_call_after(self):
        snapshot = SystemInfoSnapshot(
            app_version="1.0.0",
            whisper_version=NOT_LOADED,
            whisper_status=NOT_LOADED,
            ffmpeg_version=NOT_AVAILABLE,
            cpu_name="CPU",
            cpu_logical_count=8,
            memory_total_gib="16.0 GiB",
            gpu_names=("GPU",),
        )
        callbacks = []
        worker = SystemInfoWorker(
            job_id=4,
            collector=lambda: snapshot,
            success_callback=lambda result: callbacks.append(("success", result)),
            failure_callback=lambda result: callbacks.append(("failure", result)),
            call_after=lambda callback, result: callback(result),
        )
        worker.run()

        self.assertEqual(worker.state, "completed")
        self.assertEqual(callbacks[0][0], "success")
        self.assertEqual(callbacks[0][1].snapshot, snapshot)

    def test_worker_unexpected_exception_returns_fixed_unavailable_snapshot(self):
        callbacks = []
        worker = SystemInfoWorker(
            job_id=5,
            collector=lambda: (_ for _ in ()).throw(RuntimeError("secret detail")),
            success_callback=lambda result: callbacks.append(("success", result)),
            failure_callback=lambda result: callbacks.append(("failure", result)),
            call_after=lambda callback, result: callback(result),
        )
        worker.run()

        result = callbacks[0][1]
        self.assertEqual(callbacks[0][0], "failure")
        self.assertEqual(result.reason, "system_info_unavailable")
        self.assertEqual(result.snapshot.cpu_name, NOT_AVAILABLE)

    def test_worker_cancel_discards_late_result(self):
        callbacks = []
        worker = SystemInfoWorker(
            job_id=6,
            collector=lambda: SystemInfoSnapshot(
                app_version="1.0.0",
                whisper_version=NOT_LOADED,
                whisper_status=NOT_LOADED,
                ffmpeg_version=NOT_AVAILABLE,
                cpu_name="CPU",
                cpu_logical_count=8,
                memory_total_gib="16.0 GiB",
                gpu_names=("GPU",),
            ),
            success_callback=lambda result: callbacks.append(result),
            failure_callback=lambda result: callbacks.append(result),
            call_after=lambda callback, result: callback(result),
        )
        self.assertTrue(worker.cancel(6))
        worker.run()

        self.assertEqual(worker.state, "cancelled")
        self.assertEqual(callbacks, [])


if __name__ == "__main__":
    unittest.main()
