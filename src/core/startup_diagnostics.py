"""Low-risk, local startup diagnostics for the wx application."""

from __future__ import annotations

import ctypes
import json
import ntpath
import os
import re
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Mapping
from uuid import uuid4


SCHEMA_VERSION = 1
MAX_EVENT_BYTES = 8 * 1024
MAX_RUN_BYTES = 256 * 1024
MAX_RUN_COUNT = 10
MAX_TOTAL_BYTES = 5 * 1024 * 1024
SCAN_SLOW_THRESHOLD_MS = 120_000

_DRIVE_FIXED = 3
_DRIVE_RAMDISK = 6
_MANAGED_LOG_NAME = re.compile(
    r"^startup-\d{8}T\d{6}Z-[0-9a-f]{32}\.jsonl$"
)
_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")

_ALLOWED_STAGES = frozenset(
    {
        "entrypoint",
        "wx_import",
        "app_construct",
        "app_init",
        "splash",
        "splash_setup",
        "main_frame_create",
        "controller_create",
        "controller_bind",
        "startup_state_load",
        "settings_apply",
        "availability_scan",
        "main_frame_show",
        "main_loop",
        "event_loop",
        "logging",
        "diagnostics",
    }
)
_ALLOWED_EVENTS = frozenset(
    {
        "process_entry",
        "stage_started",
        "stage_completed",
        "stage_failed",
        "main_loop_started",
        "main_loop_completed",
        "splash_missing",
        "splash_shown",
        "splash_destroyed",
        "splash_cleanup_failed",
        "main_frame_shown",
        "startup_settings_classified",
        "startup_ready_callback_scheduled",
        "startup_ready",
        "scan_requested",
        "scan_worker_started",
        "scan_not_started",
        "scan_succeeded",
        "scan_failed",
        "scan_stale",
        "scan_slow",
        "scan_pending_at_shutdown",
        "callback_ignored_after_shutdown",
        "storage_fallback",
        "logger_disabled",
        "log_limit_reached",
        "retention_delete_failed",
        "diagnostic_check_failed",
    }
)
_ALLOWED_STATUSES = frozenset(
    {
        "started",
        "completed",
        "failed",
        "succeeded",
        "pending",
        "stale",
        "not_started",
        "shown",
        "scheduled",
        "ready",
        "warning",
        "ignored",
        "disabled",
        "skipped",
        "destroyed",
    }
)
_ALLOWED_FAILURE_CODES = frozenset(
    {
        "unknown_failure",
        "wx_import_failed",
        "wx_app_create_failed",
        "wx_app_init_failed",
        "main_loop_failed",
        "splash_setup_failed",
        "splash_cleanup_failed",
        "main_frame_create_failed",
        "main_frame_show_failed",
        "main_frame_not_visible",
        "controller_create_failed",
        "controller_bind_failed",
        "startup_state_load_failed",
        "settings_apply_failed",
        "availability_scan_failed",
        "scan_start_rejected",
        "manifest_invalid",
        "storage_path_invalid",
        "storage_path_remote",
        "settings_error",
        "settings_defaults",
        "settings_loaded",
        "preflight_failed",
        "logger_write_failed",
        "logger_retention_failed",
        "log_limit_reached",
        "stage_order_invalid",
        "stage_duplicate",
        "stage_unmatched",
        "startup_ready_before_frame",
        "startup_ready_duplicate",
        "scan_start_duplicate",
        "scan_start_without_request",
        "scan_result_without_start",
        "scan_terminal_duplicate",
    }
)
_ALLOWED_REASON_CODES = frozenset(
    {
        "primary_unavailable",
        "primary_write_failed",
        "local_path_rejected",
        "store_unavailable",
        "controller_unavailable",
        "shutdown",
        "already_started",
        "start_rejected",
        "preflight_failed",
        "manifest_invalid",
        "storage_path_invalid",
        "storage_path_remote",
        "settings_error",
        "settings_defaults",
        "settings_loaded",
    }
)
_STAGE_ORDER = (
    "wx_import",
    "app_construct",
    "splash_setup",
    "main_frame_create",
    "controller_create",
    "controller_bind",
    "startup_state_load",
    "settings_apply",
    "main_frame_show",
)


def _windows_drive_type(root: str) -> int:
    """Return the Windows drive type, failing closed when it cannot be read."""
    try:
        get_drive_type = ctypes.windll.kernel32.GetDriveTypeW  # type: ignore[attr-defined]
        get_drive_type.argtypes = [ctypes.c_wchar_p]
        get_drive_type.restype = ctypes.c_uint
        return int(get_drive_type(root))
    except (AttributeError, OSError, TypeError, ValueError):
        return 0


def is_local_storage_path(
    raw_path: str | os.PathLike[str] | None,
    *,
    drive_type_getter=None,
) -> bool:
    """Accept only absolute local paths, rejecting UNC and mapped remote drives."""
    if raw_path is None:
        return False
    try:
        value = os.fspath(raw_path)
    except (TypeError, ValueError):
        return False
    if not isinstance(value, str) or not value.strip():
        return False
    if value.startswith(("\\\\", "//")):
        return False

    if os.name != "nt":
        return Path(value).is_absolute()

    if not ntpath.isabs(value):
        return False
    drive, _ = ntpath.splitdrive(value)
    if not drive or drive.startswith("\\\\"):
        return False
    getter = drive_type_getter or _windows_drive_type
    try:
        return getter(f"{drive}\\") in {_DRIVE_FIXED, _DRIVE_RAMDISK}
    except Exception:
        return False


def _new_log_location(
    raw_root: str | None,
    *,
    target: str,
    filename: str,
    drive_type_getter=None,
) -> tuple[Path, str] | None:
    if not raw_root or not is_local_storage_path(
        raw_root,
        drive_type_getter=drive_type_getter,
    ):
        return None

    try:
        directory = (
            Path(raw_root) / "MMD_AutoLipTool" / "logs" / "startup"
        ).resolve(strict=False)
        if not is_local_storage_path(
            directory,
            drive_type_getter=drive_type_getter,
        ):
            return None
        directory.mkdir(parents=True, exist_ok=True)
        directory = directory.resolve(strict=True)
        if not is_local_storage_path(
            directory,
            drive_type_getter=drive_type_getter,
        ):
            return None
        log_path = directory / filename
        with log_path.open("xb"):
            pass
    except (OSError, RuntimeError, ValueError):
        return None
    return log_path, target


def create_startup_diagnostics(
    environ: Mapping[str, str] | None = None,
    *,
    drive_type_getter=None,
) -> "StartupDiagnostics":
    """Create a persistent logger when a local user-writable path is available."""
    environment = os.environ if environ is None else environ
    session_id = uuid4().hex
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"startup-{timestamp}-{session_id}.jsonl"

    primary = _new_log_location(
        environment.get("LOCALAPPDATA"),
        target="local_app_data",
        filename=filename,
        drive_type_getter=drive_type_getter,
    )
    if primary is not None:
        logger = StartupDiagnostics(
            primary[0],
            primary[1],
            session_id,
            fallback_root=environment.get("TEMP"),
            drive_type_getter=drive_type_getter,
        )
        if logger._prune_managed_logs():
            logger._retention_failure_logged = True
            logger.log_event(
                "logging",
                "retention_delete_failed",
                "warning",
                failure_code="logger_retention_failed",
            )
        return logger

    fallback = _new_log_location(
        environment.get("TEMP"),
        target="temp",
        filename=filename,
        drive_type_getter=drive_type_getter,
    )
    if fallback is not None:
        logger = StartupDiagnostics(fallback[0], fallback[1], session_id)
        if logger._prune_managed_logs():
            logger._retention_failure_logged = True
            logger.log_event(
                "logging",
                "retention_delete_failed",
                "warning",
                failure_code="logger_retention_failed",
            )
        logger.log_event(
            "logging",
            "storage_fallback",
            "warning",
            reason_code="primary_unavailable",
        )
        return logger

    return StartupDiagnostics(None, None, session_id)


class StartupDiagnostics:
    """Append-only, allowlisted JSONL startup events with fail-open behavior."""

    def __init__(
        self,
        log_path: Path | None,
        storage_target: str | None,
        session_id: str,
        *,
        fallback_root: str | None = None,
        drive_type_getter=None,
    ) -> None:
        self._log_path = log_path
        self._storage_target = storage_target
        self._fallback_root = fallback_root if storage_target == "local_app_data" else None
        self._drive_type_getter = drive_type_getter
        self._session_id = session_id
        self._enabled = log_path is not None and storage_target in {
            "local_app_data",
            "temp",
        }
        self._stopped = not self._enabled
        self._started_ns = time.monotonic_ns()
        self._event_id = 0
        self._run_bytes = self._current_size()
        self._lock = threading.RLock()
        self._stage_states: dict[str, str] = {}
        self._last_stage_order = -1
        self._main_frame_shown = False
        self._startup_ready = False
        self._pending_scan_requests = 0
        self._scan_jobs: dict[tuple[int, int], str] = {}
        self._scan_slow_logged: set[tuple[int, int]] = set()
        self._shutdown_callbacks_logged: set[tuple[int, int]] = set()
        self._retention_failure_logged = False

    @property
    def enabled(self) -> bool:
        return self._enabled and not self._stopped

    def _current_size(self) -> int:
        if self._log_path is None:
            return 0
        try:
            return self._log_path.stat().st_size
        except OSError:
            return 0

    def _base_record(self, stage: str, event: str, status: str) -> dict[str, object]:
        with self._lock:
            self._event_id += 1
            event_id = self._event_id
        now = datetime.now(timezone.utc)
        return {
            "schema_version": SCHEMA_VERSION,
            "event_id": event_id,
            "session_id": self._session_id,
            "timestamp_utc": now.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "elapsed_ms": max(0, (time.monotonic_ns() - self._started_ns) // 1_000_000),
            "storage_target": self._storage_target,
            "stage": stage,
            "event": event,
            "status": status,
        }

    @staticmethod
    def _safe_exception_type(error: BaseException | None) -> str | None:
        if error is None:
            return None
        name = type(error).__name__
        return name if _TOKEN.fullmatch(name) else "Exception"

    @staticmethod
    def _safe_nonnegative_int(value: int | None) -> int | None:
        if type(value) is not int or value < 0 or value > 2**31 - 1:
            return None
        return value

    def _serialize_event(
        self,
        stage: str,
        event: str,
        status: str,
        *,
        duration_ms: int | None = None,
        failure_code: str | None = None,
        exception: BaseException | None = None,
        reason_code: str | None = None,
        job_id: int | None = None,
        scan_generation: int | None = None,
    ) -> bytes | None:
        if (
            stage not in _ALLOWED_STAGES
            or event not in _ALLOWED_EVENTS
            or status not in _ALLOWED_STATUSES
        ):
            return None
        record = self._base_record(stage, event, status)
        safe_duration = self._safe_nonnegative_int(duration_ms)
        if safe_duration is not None:
            record["duration_ms"] = safe_duration
        if failure_code in _ALLOWED_FAILURE_CODES:
            record["failure_code"] = failure_code
        safe_exception = self._safe_exception_type(exception)
        if safe_exception is not None:
            record["exception_type"] = safe_exception
        if reason_code in _ALLOWED_REASON_CODES:
            record["reason_code"] = reason_code
        safe_job_id = self._safe_nonnegative_int(job_id)
        if safe_job_id is not None:
            record["job_id"] = safe_job_id
        safe_generation = self._safe_nonnegative_int(scan_generation)
        if safe_generation is not None:
            record["scan_generation"] = safe_generation
        try:
            line = json.dumps(
                record,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8") + b"\n"
        except (TypeError, ValueError):
            return None
        if len(line) > MAX_EVENT_BYTES:
            return None
        return line

    def log_event(
        self,
        stage: str,
        event: str,
        status: str,
        *,
        duration_ms: int | None = None,
        failure_code: str | None = None,
        exception: BaseException | None = None,
        reason_code: str | None = None,
        job_id: int | None = None,
        scan_generation: int | None = None,
    ) -> bool:
        if not self._enabled or self._stopped or self._log_path is None:
            return False
        with self._lock:
            try:
                line = self._serialize_event(
                    stage,
                    event,
                    status,
                    duration_ms=duration_ms,
                    failure_code=failure_code,
                    exception=exception,
                    reason_code=reason_code,
                    job_id=job_id,
                    scan_generation=scan_generation,
                )
            except Exception:
                self._stopped = True
                return False
            if line is None:
                return False
            if self._run_bytes + len(line) > MAX_RUN_BYTES:
                self._write_limit_reached_locked()
                self._stopped = True
                return False
            if not self._write_line_locked(line):
                if not self._activate_fallback_locked():
                    self._stopped = True
                    return False
                line = self._serialize_event(
                    stage,
                    event,
                    status,
                    duration_ms=duration_ms,
                    failure_code=failure_code,
                    exception=exception,
                    reason_code=reason_code,
                    job_id=job_id,
                    scan_generation=scan_generation,
                )
                if line is None or self._run_bytes + len(line) > MAX_RUN_BYTES:
                    self._write_limit_reached_locked()
                    self._stopped = True
                    return False
                if not self._write_line_locked(line):
                    self._stopped = True
                    return False
            self._run_bytes += len(line)
            if self._prune_managed_logs() and not self._retention_failure_logged:
                self._retention_failure_logged = True
                self._write_internal_event_locked(
                    "logging",
                    "retention_delete_failed",
                    "warning",
                    failure_code="logger_retention_failed",
                )
            return True

    def _activate_fallback_locked(self) -> bool:
        if (
            self._fallback_root is None
            or self._log_path is None
            or self._storage_target != "local_app_data"
        ):
            return False
        fallback = _new_log_location(
            self._fallback_root,
            target="temp",
            filename=self._log_path.name,
            drive_type_getter=self._drive_type_getter,
        )
        self._fallback_root = None
        if fallback is None:
            return False
        self._log_path, self._storage_target = fallback
        fallback_line = self._serialize_event(
            "logging",
            "storage_fallback",
            "warning",
            reason_code="primary_write_failed",
        )
        if (
            fallback_line is None
            or self._run_bytes + len(fallback_line) > MAX_RUN_BYTES
            or not self._write_line_locked(fallback_line)
        ):
            return False
        self._run_bytes += len(fallback_line)
        if self._prune_managed_logs() and not self._retention_failure_logged:
            self._retention_failure_logged = True
            self._write_internal_event_locked(
                "logging",
                "retention_delete_failed",
                "warning",
                failure_code="logger_retention_failed",
            )
        return True

    def _write_line_locked(self, line: bytes) -> bool:
        if self._log_path is None:
            return False
        try:
            with self._log_path.open("ab") as stream:
                stream.write(line)
            return True
        except OSError:
            return False

    def _write_internal_event_locked(
        self,
        stage: str,
        event: str,
        status: str,
        *,
        failure_code: str | None = None,
    ) -> None:
        line = self._serialize_event(
            stage,
            event,
            status,
            failure_code=failure_code,
        )
        if line is None or self._run_bytes + len(line) > MAX_RUN_BYTES:
            return
        if self._write_line_locked(line):
            self._run_bytes += len(line)

    def _write_limit_reached_locked(self) -> None:
        self._write_internal_event_locked(
            "logging",
            "log_limit_reached",
            "warning",
            failure_code="log_limit_reached",
        )

    def _prune_managed_logs(self) -> bool:
        if self._log_path is None:
            return False
        directory = self._log_path.parent
        try:
            entries = [
                path
                for path in directory.iterdir()
                if _MANAGED_LOG_NAME.fullmatch(path.name)
                and not path.is_symlink()
                and path.is_file()
            ]
        except OSError:
            return True

        measured: list[tuple[int, int, Path]] = []
        try:
            for path in entries:
                stat = path.stat()
                measured.append((stat.st_mtime_ns, stat.st_size, path))
        except OSError:
            return True
        measured.sort(key=lambda item: item[0], reverse=True)
        total_bytes = sum(size for _, size, _ in measured)
        count = len(measured)
        failed = False
        for _, size, path in reversed(measured):
            if count <= MAX_RUN_COUNT and total_bytes <= MAX_TOTAL_BYTES:
                break
            if path == self._log_path:
                continue
            try:
                path.unlink()
            except OSError:
                failed = True
                continue
            count -= 1
            total_bytes -= size
        return failed or count > MAX_RUN_COUNT or total_bytes > MAX_TOTAL_BYTES

    @contextmanager
    def stage(self, stage: str, *, failure_code: str) -> Iterator[None]:
        start_ns = time.monotonic_ns()
        order_index = _STAGE_ORDER.index(stage) if stage in _STAGE_ORDER else None
        with self._lock:
            if stage in self._stage_states:
                self._diagnostic_failure_locked("stage_duplicate")
            else:
                self._stage_states[stage] = "started"
            if order_index is not None:
                if order_index < self._last_stage_order:
                    self._diagnostic_failure_locked("stage_order_invalid")
                self._last_stage_order = max(self._last_stage_order, order_index)
        self.log_event(stage, "stage_started", "started")
        try:
            yield
        except BaseException as error:
            self._finish_stage(
                stage,
                "failed",
                start_ns,
                failure_code=failure_code,
                exception=error,
            )
            raise
        else:
            self._finish_stage(stage, "completed", start_ns)

    def _finish_stage(
        self,
        stage: str,
        status: str,
        start_ns: int,
        *,
        failure_code: str | None = None,
        exception: BaseException | None = None,
    ) -> None:
        with self._lock:
            if self._stage_states.get(stage) != "started":
                self._diagnostic_failure_locked("stage_unmatched")
                return
            self._stage_states[stage] = status
        duration_ms = max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
        event = "stage_failed" if status == "failed" else "stage_completed"
        self.log_event(
            stage,
            event,
            status,
            duration_ms=duration_ms,
            failure_code=failure_code,
            exception=exception,
        )

    def _diagnostic_failure_locked(self, failure_code: str) -> None:
        self.log_event(
            "diagnostics",
            "diagnostic_check_failed",
            "warning",
            failure_code=failure_code,
        )

    def record_main_frame_shown(self) -> None:
        with self._lock:
            if self._main_frame_shown:
                self._diagnostic_failure_locked("stage_duplicate")
                return
            self._main_frame_shown = True
        self.log_event("main_frame_show", "main_frame_shown", "shown")

    def record_startup_ready_callback_scheduled(self) -> None:
        self.log_event(
            "event_loop",
            "startup_ready_callback_scheduled",
            "scheduled",
        )

    def record_startup_ready(self) -> None:
        with self._lock:
            if not self._main_frame_shown:
                self._diagnostic_failure_locked("startup_ready_before_frame")
                return
            if self._startup_ready:
                self._diagnostic_failure_locked("startup_ready_duplicate")
                return
            self._startup_ready = True
        self.log_event("event_loop", "startup_ready", "ready")

    def record_scan_requested(self) -> None:
        with self._lock:
            self._pending_scan_requests += 1
        self.log_event("availability_scan", "scan_requested", "started")

    def record_scan_started(self, job_id: int, scan_generation: int) -> None:
        key = (job_id, scan_generation)
        started_without_request = False
        with self._lock:
            if key in self._scan_jobs:
                self._diagnostic_failure_locked("scan_start_duplicate")
                return
            self._scan_jobs[key] = "pending"
            if self._pending_scan_requests > 0:
                self._pending_scan_requests -= 1
            else:
                started_without_request = True
        if started_without_request:
            self.log_event(
                "diagnostics",
                "diagnostic_check_failed",
                "warning",
                failure_code="scan_start_without_request",
                job_id=job_id,
                scan_generation=scan_generation,
            )
        self.log_event(
            "availability_scan",
            "scan_worker_started",
            "pending",
            job_id=job_id,
            scan_generation=scan_generation,
        )

    def record_scan_not_started(
        self,
        reason_code: str,
        *,
        failure_code: str | None = None,
    ) -> None:
        with self._lock:
            if self._pending_scan_requests <= 0:
                self._diagnostic_failure_locked("scan_start_duplicate")
                return
            self._pending_scan_requests -= 1
        self.log_event(
            "availability_scan",
            "scan_not_started",
            "not_started",
            failure_code=failure_code,
            reason_code=reason_code,
        )

    def record_scan_slow(self, job_id: int, scan_generation: int) -> None:
        key = (job_id, scan_generation)
        with self._lock:
            if self._scan_jobs.get(key) != "pending" or key in self._scan_slow_logged:
                return
            self._scan_slow_logged.add(key)
        self.log_event(
            "availability_scan",
            "scan_slow",
            "warning",
            job_id=job_id,
            scan_generation=scan_generation,
        )

    def record_scan_result(
        self,
        job_id: int,
        scan_generation: int,
        *,
        succeeded: bool,
        failure_code: str | None = None,
    ) -> None:
        key = (job_id, scan_generation)
        with self._lock:
            if self._scan_jobs.get(key) != "pending":
                self._diagnostic_failure_locked("scan_result_without_start")
                return
            self._scan_jobs[key] = "succeeded" if succeeded else "failed"
        self.log_event(
            "availability_scan",
            "scan_succeeded" if succeeded else "scan_failed",
            "succeeded" if succeeded else "failed",
            failure_code=None if succeeded else failure_code,
            job_id=job_id,
            scan_generation=scan_generation,
        )

    def record_scan_stale(self, job_id: int, scan_generation: int) -> None:
        key = (job_id, scan_generation)
        with self._lock:
            current = self._scan_jobs.get(key)
            if current == "pending":
                self._scan_jobs[key] = "stale"
            elif current is not None:
                self._diagnostic_failure_locked("scan_terminal_duplicate")
                return
        self.log_event(
            "availability_scan",
            "scan_stale",
            "stale",
            job_id=job_id,
            scan_generation=scan_generation,
        )

    def record_scan_pending_at_shutdown(
        self,
        job_id: int,
        scan_generation: int,
    ) -> None:
        key = (job_id, scan_generation)
        with self._lock:
            if self._scan_jobs.get(key) != "pending":
                return
            self._scan_jobs[key] = "pending_at_shutdown"
        self.log_event(
            "availability_scan",
            "scan_pending_at_shutdown",
            "pending",
            job_id=job_id,
            scan_generation=scan_generation,
        )

    def record_callback_ignored_after_shutdown(
        self,
        job_id: int,
        scan_generation: int,
    ) -> None:
        key = (job_id, scan_generation)
        with self._lock:
            if key in self._shutdown_callbacks_logged:
                return
            self._shutdown_callbacks_logged.add(key)
        self.log_event(
            "availability_scan",
            "callback_ignored_after_shutdown",
            "ignored",
            job_id=job_id,
            scan_generation=scan_generation,
        )


__all__ = [
    "MAX_EVENT_BYTES",
    "MAX_RUN_BYTES",
    "MAX_RUN_COUNT",
    "MAX_TOTAL_BYTES",
    "SCAN_SLOW_THRESHOLD_MS",
    "StartupDiagnostics",
    "create_startup_diagnostics",
    "is_local_storage_path",
]
