from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from app_version import resolve_app_version
from src.core.ffmpeg_locator import locate_ffmpeg_tools


NOT_AVAILABLE = "not_available"
NOT_LOADED = "not_loaded"
LOADED = "loaded"
SYSTEM_INFO_UNAVAILABLE = "system_info_unavailable"
FFMPEG_TIMEOUT_SEC = 3.0
EXTERNAL_OUTPUT_LIMIT_BYTES = 64 * 1024

_GPU_QUERY = (
    "Get-CimInstance -ClassName Win32_VideoController "
    "| Select-Object -ExpandProperty Name"
)
_FFMPEG_VERSION_PATTERN = re.compile(r"^\s*ffmpeg\s+version\s+(\S+)", re.IGNORECASE)
_READ_CHUNK_SIZE = 4096

@dataclass(frozen=True)
class SystemInfoSnapshot:
    """Immutable, display-only runtime information for the About dialog."""

    app_version: str
    whisper_version: str
    whisper_status: Literal["loaded", "not_loaded", "not_available"]
    ffmpeg_version: str
    cpu_name: str
    cpu_logical_count: int | str
    memory_total_gib: str
    gpu_names: tuple[str, ...]


@dataclass(frozen=True)
class _ProcessResult:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool = False
    output_exceeded: bool = False


class _BoundedCapture:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.data = bytearray()
        self.exceeded = False

    def append(self, chunk: bytes) -> None:
        remaining = self.limit - len(self.data)
        if remaining > 0:
            self.data.extend(chunk[:remaining])
        if len(chunk) > remaining:
            self.exceeded = True


def unavailable_snapshot() -> SystemInfoSnapshot:
    return SystemInfoSnapshot(
        app_version=NOT_AVAILABLE,
        whisper_version=NOT_AVAILABLE,
        whisper_status=NOT_AVAILABLE,
        ffmpeg_version=NOT_AVAILABLE,
        cpu_name=NOT_AVAILABLE,
        cpu_logical_count=NOT_AVAILABLE,
        memory_total_gib=NOT_AVAILABLE,
        gpu_names=(NOT_AVAILABLE,),
    )


def _read_stream(stream, capture: _BoundedCapture) -> None:
    try:
        while True:
            chunk = stream.read(_READ_CHUNK_SIZE)
            if not chunk:
                return
            capture.append(chunk)
    except (OSError, ValueError):
        return


def _run_external_command(
    args: Sequence[str],
    *,
    timeout_sec: float = FFMPEG_TIMEOUT_SEC,
    output_limit: int = EXTERNAL_OUTPUT_LIMIT_BYTES,
) -> _ProcessResult | None:
    """Run a fixed local command while bounding retained stdout/stderr."""
    try:
        process = subprocess.Popen(
            list(args),
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, ValueError):
        return None

    stdout_capture = _BoundedCapture(output_limit)
    stderr_capture = _BoundedCapture(output_limit)
    stdout_thread = threading.Thread(
        target=_read_stream,
        args=(process.stdout, stdout_capture),
        name="system-info-stdout",
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_read_stream,
        args=(process.stderr, stderr_capture),
        name="system-info-stderr",
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    timed_out = False
    try:
        returncode = process.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            process.kill()
        except OSError:
            pass
        try:
            returncode = process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            returncode = None

    stdout_thread.join(timeout=1.0)
    stderr_thread.join(timeout=1.0)
    return _ProcessResult(
        returncode=returncode,
        stdout=bytes(stdout_capture.data),
        stderr=bytes(stderr_capture.data),
        timed_out=timed_out,
        output_exceeded=stdout_capture.exceeded or stderr_capture.exceeded,
    )


def _decode_output(value: bytes) -> str:
    return value.decode("utf-8", errors="replace")


def _collect_app_version() -> str:
    try:
        value = resolve_app_version()
    except Exception:
        return NOT_AVAILABLE
    if isinstance(value, str) and value.strip():
        return value.strip()
    return NOT_AVAILABLE


def _collect_whisper_info() -> tuple[str, Literal["loaded", "not_loaded", "not_available"]]:
    module = sys.modules.get("whisper")
    if module is None:
        return NOT_LOADED, NOT_LOADED
    try:
        value = getattr(module, "__version__", None)
    except Exception:
        return NOT_AVAILABLE, NOT_AVAILABLE
    if isinstance(value, str) and value.strip():
        return value.strip(), LOADED
    return NOT_AVAILABLE, NOT_AVAILABLE


def _collect_ffmpeg_version() -> str:
    try:
        locator = locate_ffmpeg_tools()
        path = locator.ffmpeg.path
    except Exception:
        return NOT_AVAILABLE
    if not isinstance(path, Path) or not path.is_file():
        return NOT_AVAILABLE

    result = _run_external_command((str(path), "-version"))
    if (
        result is None
        or result.returncode != 0
        or result.timed_out
        or result.output_exceeded
    ):
        return NOT_AVAILABLE

    output = "\n".join((_decode_output(result.stdout), _decode_output(result.stderr)))
    for line in output.splitlines():
        match = _FFMPEG_VERSION_PATTERN.match(line)
        if match:
            return match.group(1)
    return NOT_AVAILABLE


def _collect_cpu_name() -> str:
    for candidate in (
        lambda: platform.processor(),
        lambda: platform.uname().processor,
    ):
        try:
            value = candidate()
        except Exception:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
    return NOT_AVAILABLE


def _collect_cpu_logical_count() -> int | str:
    try:
        value = os.cpu_count()
    except Exception:
        return NOT_AVAILABLE
    return value if isinstance(value, int) and value > 0 else NOT_AVAILABLE


def _read_physical_memory_bytes() -> int | None:
    if os.name != "nt":
        return None

    class _MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    try:
        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        value = int(status.ullTotalPhys)
    except (AttributeError, OSError, TypeError, ValueError):
        return None
    return value if value > 0 else None


def _collect_memory_total_gib() -> str:
    value = _read_physical_memory_bytes()
    if value is None:
        return NOT_AVAILABLE
    return f"{value / (1024 ** 3):.1f} GiB"


def _collect_gpu_names() -> tuple[str, ...]:
    executable = shutil.which("powershell.exe")
    if not executable:
        return (NOT_AVAILABLE,)
    result = _run_external_command(
        (
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            _GPU_QUERY,
        )
    )
    if (
        result is None
        or result.returncode != 0
        or result.timed_out
        or result.output_exceeded
    ):
        return (NOT_AVAILABLE,)

    names: list[str] = []
    for line in _decode_output(result.stdout).splitlines():
        name = line.strip()
        if name and name not in names:
            names.append(name)
    return tuple(names) if names else (NOT_AVAILABLE,)


def collect_system_info() -> SystemInfoSnapshot:
    whisper_version, whisper_status = _collect_whisper_info()
    return SystemInfoSnapshot(
        app_version=_collect_app_version(),
        whisper_version=whisper_version,
        whisper_status=whisper_status,
        ffmpeg_version=_collect_ffmpeg_version(),
        cpu_name=_collect_cpu_name(),
        cpu_logical_count=_collect_cpu_logical_count(),
        memory_total_gib=_collect_memory_total_gib(),
        gpu_names=_collect_gpu_names(),
    )


__all__ = [
    "EXTERNAL_OUTPUT_LIMIT_BYTES",
    "FFMPEG_TIMEOUT_SEC",
    "LOADED",
    "NOT_AVAILABLE",
    "NOT_LOADED",
    "SYSTEM_INFO_UNAVAILABLE",
    "SystemInfoSnapshot",
    "collect_system_info",
    "unavailable_snapshot",
]
