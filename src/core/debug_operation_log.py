"""Session-scoped, bounded JSONL logging for user operations."""

from __future__ import annotations

import json
import math
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.core.analysis_debug_store import resolve_debug_root


SCHEMA_VERSION = 1
DEFAULT_QUEUE_SIZE = 1024
DEFAULT_SESSION_LIMIT_BYTES = 16 * 1024 * 1024

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:@-]{1,128}$")
_ACTION_RE = re.compile(r"^[a-z][a-z0-9_.:-]{0,95}$")
_ALLOWED_STATUSES = frozenset(
    {
        "requested",
        "started",
        "completed",
        "failed",
        "cancelled",
        "rejected",
        "noop",
        "ignored",
        "recording",
        "recording_disabled",
        "recording_stopped",
    }
)
_ALLOWED_ORIGINS = frozenset({"user", "system", "worker"})
_SAFE_PAYLOAD_KEYS = frozenset(
    {
        "input_mode",
        "has_text_input",
        "has_audio_input",
        "analysis_result_valid",
        "analysis_pending_rebuild",
        "busy",
        "is_playing",
        "changed",
        "dirty",
        "text_length",
        "vowel_length",
        "setting",
        "operation_kind",
        "before",
        "after",
        "morph_upper_limit",
        "closing_hold_frames",
        "closing_softness_frames",
        "long_vowel_mode",
        "field",
        "event_id",
        "event_index",
        "selection_event_id",
        "selected_event_index",
        "preset_id",
        "profile_id",
        "model_id",
        "model_key",
        "morph_name_set_id",
        "theme_mode",
        "entry",
        "worker_kind",
        "job_kind",
        "file_basename",
        "vowel",
        "committed",
        "history_action",
        "history_changed",
        "available",
        "result_count",
        "duration_sec",
        "sample_rate_hz",
        "channel_count",
        "zoom_factor",
        "viewport_start_sec",
        "viewport_end_sec",
        "playback_position_sec",
        "delta_sec",
        "recording_state",
        "dropped_count",
        "reason_code",
        "result_status",
        "result_context_present",
        "result_preview_present",
        "result_diagnostics_valid",
        "issue_count",
        "issue_reason_code",
        "issue_stage",
        "same_draft",
        "cancelled",
        "lifecycle_signature_matches",
        "shared_result_accepted",
    }
)
_ID_KEYS = frozenset(
    {
        "event_id",
        "selection_event_id",
        "preset_id",
        "profile_id",
        "model_id",
        "model_key",
    }
)
_FLOAT_KEYS = frozenset(
    {
        "morph_upper_limit",
        "duration_sec",
        "zoom_factor",
        "viewport_start_sec",
        "viewport_end_sec",
        "playback_position_sec",
        "delta_sec",
    }
)
_INT_KEYS = frozenset(
    {
        "text_length",
        "vowel_length",
        "closing_hold_frames",
        "closing_softness_frames",
        "event_index",
        "selected_event_index",
        "sample_rate_hz",
        "channel_count",
        "result_count",
        "dropped_count",
        "issue_count",
    }
)
_BOOL_KEYS = frozenset(
    {
        "has_text_input",
        "has_audio_input",
        "analysis_result_valid",
        "analysis_pending_rebuild",
        "busy",
        "is_playing",
        "changed",
        "dirty",
        "committed",
        "history_changed",
        "available",
        "result_context_present",
        "result_preview_present",
        "result_diagnostics_valid",
        "same_draft",
        "cancelled",
        "lifecycle_signature_matches",
        "shared_result_accepted",
    }
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _safe_token(value: object) -> str | None:
    if type(value) is not str or not _TOKEN_RE.fullmatch(value):
        return None
    return value


def _safe_action(value: object) -> str:
    if type(value) is str and _ACTION_RE.fullmatch(value):
        return value
    return "unknown_operation"


def _safe_basename(value: object) -> str | None:
    if type(value) is not str:
        return None
    basename = value.replace("\\", "/").rsplit("/", 1)[-1]
    basename = "".join(char for char in basename if ord(char) >= 32 and ord(char) != 127)
    return basename[:160] or None


def _safe_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    result: dict[str, Any] = {}
    for raw_key, value in payload.items():
        if type(raw_key) is not str or raw_key not in _SAFE_PAYLOAD_KEYS:
            continue
        if raw_key == "file_basename":
            safe_value = _safe_basename(value)
        elif raw_key in _BOOL_KEYS:
            safe_value = value if type(value) is bool else None
        elif raw_key in _INT_KEYS:
            safe_value = value if type(value) is int and value >= 0 else None
        elif raw_key in _FLOAT_KEYS:
            safe_value = (
                value
                if isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(float(value))
                else None
            )
        elif raw_key in {"before", "after"}:
            if type(value) in {int, float, bool}:
                safe_value = (
                    value
                    if type(value) is not float or math.isfinite(value)
                    else None
                )
            else:
                safe_value = _safe_token(value)
        elif raw_key in _ID_KEYS:
            safe_value = _safe_token(value)
        elif type(value) is str:
            safe_value = _safe_token(value)
        else:
            safe_value = None
        if safe_value is not None:
            result[raw_key] = safe_value
    return result


@dataclass(frozen=True, slots=True)
class OperationHandle:
    """Identity and origin captured when one user operation is requested."""

    operation_id: str
    action: str
    session_id: str
    recording_interval: int
    requested_at_monotonic: float
    source: str
    entry: str | None
    analysis_run_id: str | None = None
    analysis_result_id: str | None = None
    job_kind: str | None = None
    job_id: int | None = None
    started_at_monotonic: float | None = None


class DebugOperationRecorder:
    """Write bounded, ordered operation events on a lazily started thread."""

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        max_session_bytes: int = DEFAULT_SESSION_LIMIT_BYTES,
        on_state_change: Callable[[str, str | None, Path | None], None] | None = None,
    ) -> None:
        if type(queue_size) is not int or queue_size < 1:
            raise ValueError("queue_size must be a positive integer")
        if type(max_session_bytes) is not int or max_session_bytes < 256:
            raise ValueError("max_session_bytes must be at least 256")
        self.root = Path(root) if root is not None else resolve_debug_root()
        self.max_session_bytes = max_session_bytes
        self._queue: queue.Queue[dict[str, Any] | None] = queue.Queue(
            maxsize=queue_size
        )
        self._on_state_change = on_state_change
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._session_id: str | None = None
        self._session_started_at: float | None = None
        self._recording_interval = 0
        self._sequence = 0
        self._enabled = False
        self._closing = False
        self._closed = False
        self._shutdown_sentinel_enqueued = False
        self._capacity_reached = False
        self._state = "stopped"
        self._last_error_code: str | None = None
        self._path: Path | None = None
        self._bytes_written = 0
        self._dropped_count = 0
        self._dropped_sequence_start: int | None = None
        self._dropped_sequence_end: int | None = None

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    @property
    def session_id(self) -> str | None:
        with self._lock:
            return self._session_id

    @property
    def path(self) -> Path | None:
        with self._lock:
            return self._path

    @property
    def last_error_code(self) -> str | None:
        with self._lock:
            return self._last_error_code

    @property
    def dropped_count(self) -> int:
        with self._lock:
            return self._dropped_count

    @property
    def thread_started(self) -> bool:
        with self._lock:
            return self._thread is not None

    def set_enabled(
        self,
        enabled: bool,
        *,
        state_snapshot: Mapping[str, Any] | None = None,
    ) -> str:
        notify = False
        with self._lock:
            if self._closed:
                return self._state
            enabled = bool(enabled)
            if enabled == self._enabled:
                return self._state
            if enabled:
                if self._capacity_reached or self._last_error_code:
                    return self._state
                if self._session_id is None:
                    self._session_id = uuid.uuid4().hex
                    self._session_started_at = time.monotonic()
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                    self._path = (
                        self.root
                        / "operations"
                        / f"{stamp}_{self._session_id}.jsonl"
                    )
                self._recording_interval += 1
                self._enabled = True
                self._state = "starting"
                self._ensure_writer_locked()
                snapshot = dict(state_snapshot or {})
                run_id = snapshot.pop("analysis_run_id", None)
                result_id = snapshot.pop("analysis_result_id", None)
                self._append_event_locked(
                    "recording_enabled",
                    "recording",
                    payload=snapshot,
                    source="system",
                    analysis_run_id=run_id,
                    analysis_result_id=result_id,
                )
                notify = True
            else:
                self._append_event_locked(
                    "recording_disabled",
                    "recording_disabled",
                    payload={"recording_state": "paused"},
                    source="system",
                )
                self._enabled = False
                if self._state == "recording":
                    self._state = "paused"
                notify = True
            state = self._state
        if notify:
            self._notify_state(state)
        return state

    def begin_operation(
        self,
        action: str,
        *,
        payload: Mapping[str, Any] | None = None,
        source: str = "user",
        entry: str | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
    ) -> OperationHandle | None:
        with self._lock:
            if not self._enabled or self._closing or self._closed or self._capacity_reached:
                return None
            if self._session_id is None or self._session_started_at is None:
                return None
            now = time.monotonic()
            handle = OperationHandle(
                operation_id=uuid.uuid4().hex,
                action=_safe_action(action),
                session_id=self._session_id,
                recording_interval=self._recording_interval,
                requested_at_monotonic=now,
                source=source if source in _ALLOWED_ORIGINS else "system",
                entry=_safe_token(entry),
                analysis_run_id=_safe_token(analysis_run_id),
                analysis_result_id=_safe_token(analysis_result_id),
            )
            self._append_event_locked(
                handle.action,
                "requested",
                operation=handle,
                payload=payload,
                source=handle.source,
                entry=handle.entry,
                phase="request",
            )
            return handle

    def mark_started(
        self,
        handle: OperationHandle | None,
        *,
        job_kind: str | None = None,
        job_id: int | None = None,
        payload: Mapping[str, Any] | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
    ) -> OperationHandle | None:
        if handle is None:
            return None
        with self._lock:
            if not self._enabled or not self._is_current_session_locked(handle):
                return handle
            now = time.monotonic()
            updated = replace(
                handle,
                job_kind=_safe_token(job_kind),
                job_id=(job_id if type(job_id) is int and job_id >= 0 else None),
                started_at_monotonic=now,
                analysis_run_id=(
                    _safe_token(analysis_run_id)
                    if analysis_run_id is not None
                    else handle.analysis_run_id
                ),
                analysis_result_id=(
                    _safe_token(analysis_result_id)
                    if analysis_result_id is not None
                    else handle.analysis_result_id
                ),
            )
            self._append_event_locked(
                updated.action,
                "started",
                operation=updated,
                payload=payload,
                source="worker" if job_kind else updated.source,
                entry=updated.entry,
                phase="worker_started",
            )
            return updated

    def record_operation_phase(
        self,
        handle: OperationHandle | None,
        phase: str,
        status: str,
        *,
        job_kind: str | None = None,
        job_id: int | None = None,
        payload: Mapping[str, Any] | None = None,
        reason_code: str | None = None,
    ) -> bool:
        if handle is None:
            return False
        if status not in _ALLOWED_STATUSES:
            raise ValueError("unsupported operation log status")
        with self._lock:
            if not self._enabled or not self._is_current_session_locked(handle):
                return False
            return self._append_event_locked(
                handle.action,
                status,
                operation=replace(
                    handle,
                    job_kind=_safe_token(job_kind) or handle.job_kind,
                    job_id=(
                        job_id
                        if type(job_id) is int and job_id >= 0
                        else handle.job_id
                    ),
                ),
                payload=payload,
                source="worker" if job_kind else handle.source,
                entry=handle.entry,
                reason_code=reason_code,
                phase=phase,
            )

    def finish_operation(
        self,
        handle: OperationHandle | None,
        status: str,
        *,
        reason_code: str | None = None,
        payload: Mapping[str, Any] | None = None,
        accepted_origin: object | None = None,
    ) -> bool:
        if handle is None:
            return False
        if status not in _ALLOWED_STATUSES or status in {
            "requested",
            "started",
            "recording",
            "recording_disabled",
            "recording_stopped",
        }:
            raise ValueError("status must describe an operation result")
        with self._lock:
            if not self._enabled or not self._is_current_session_locked(handle):
                return False
            result_id = handle.analysis_result_id
            if accepted_origin is not None:
                origin_job_id = getattr(accepted_origin, "job_id", None)
                origin_run_id = getattr(accepted_origin, "source_run_id", None)
                candidate_result_id = getattr(
                    accepted_origin, "analysis_result_id", None
                )
                if (
                    type(origin_job_id) is int
                    and origin_job_id == handle.job_id
                    and origin_run_id == handle.analysis_run_id
                    and type(candidate_result_id) is str
                ):
                    result_id = _safe_token(candidate_result_id)
            completed_at = time.monotonic()
            duration_ms = None
            if handle.started_at_monotonic is not None:
                duration_ms = max(
                    0.0,
                    (completed_at - handle.started_at_monotonic) * 1000.0,
                )
            accepted = self._append_event_locked(
                handle.action,
                status,
                operation=replace(handle, analysis_result_id=result_id),
                payload=payload,
                source=handle.source,
                entry=handle.entry,
                reason_code=reason_code,
                duration_ms=duration_ms,
                phase="terminal",
            )
            return accepted

    def record_event(
        self,
        action: str,
        status: str,
        *,
        payload: Mapping[str, Any] | None = None,
        source: str = "system",
        entry: str | None = None,
        job_kind: str | None = None,
        job_id: int | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
        reason_code: str | None = None,
    ) -> bool:
        if status not in _ALLOWED_STATUSES:
            raise ValueError("unsupported operation log status")
        with self._lock:
            if not self._enabled or self._closed or self._capacity_reached:
                return False
            accepted = self._append_event_locked(
                action,
                status,
                payload=payload,
                source=source,
                entry=entry,
                job_kind=job_kind,
                job_id=job_id,
                analysis_run_id=analysis_run_id,
                analysis_result_id=analysis_result_id,
                reason_code=reason_code,
            )
            return accepted

    def flush(self, timeout: float = 1.0) -> bool:
        if timeout < 0:
            timeout = 0.0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._queue.unfinished_tasks == 0:
                return True
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        return self._queue.unfinished_tasks == 0

    def shutdown(self, timeout: float = 1.0) -> bool:
        deadline = time.monotonic() + max(0.0, timeout)
        already_closed = False
        with self._lock:
            if self._closed:
                thread = self._thread
                already_closed = True
            else:
                self._closing = True
                self._enabled = False
                if self._state not in {"unavailable", "degraded"}:
                    self._state = "stopping"
                thread = self._thread
        self._notify_state(self.state)
        if thread is None:
            with self._lock:
                self._closed = True
                if self._state != "unavailable":
                    self._state = "stopped"
            self._notify_state(self.state)
            return True

        if already_closed and self._shutdown_sentinel_enqueued:
            remaining = max(0.0, deadline - time.monotonic())
            thread.join(timeout=remaining)
            return not thread.is_alive() and self._queue.unfinished_tasks == 0

        if not already_closed:
            remaining = max(0.0, deadline - time.monotonic())
            flushed_before_exit = self.flush(timeout=remaining / 2.0)
            with self._lock:
                shutdown_recorded = False
                if self._session_id is not None and not self._capacity_reached:
                    shutdown_recorded = self._append_event_locked(
                        "operation_log_shutdown",
                        "completed",
                        source="system",
                        allow_disabled=True,
                    )
                if not shutdown_recorded and self._state not in {
                    "unavailable",
                    "degraded",
                }:
                    self._state = "degraded"
                    self._last_error_code = "OPERATION_LOG_SHUTDOWN_INCOMPLETE"
                if not flushed_before_exit and self._state not in {
                    "unavailable",
                    "degraded",
                }:
                    self._state = "degraded"
                    self._last_error_code = "OPERATION_LOG_SHUTDOWN_TIMEOUT"
                self._closed = True
            remaining = max(0.0, deadline - time.monotonic())
            self.flush(timeout=remaining / 2.0)
        remaining = max(0.0, deadline - time.monotonic())
        try:
            self._queue.put(None, timeout=remaining)
            with self._lock:
                self._shutdown_sentinel_enqueued = True
        except queue.Full:
            with self._lock:
                if self._state not in {"unavailable", "degraded"}:
                    self._state = "degraded"
                    self._last_error_code = "OPERATION_LOG_SHUTDOWN_TIMEOUT"
            self._notify_state(self.state)
            return False

        remaining = max(0.0, deadline - time.monotonic())
        thread.join(timeout=remaining)
        stopped = not thread.is_alive() and self._queue.unfinished_tasks == 0
        with self._lock:
            if stopped and self._state not in {"unavailable", "degraded"}:
                self._state = "stopped"
            elif not stopped and self._state not in {"unavailable", "degraded"}:
                self._state = "degraded"
                self._last_error_code = "OPERATION_LOG_SHUTDOWN_TIMEOUT"
        self._notify_state(self.state)
        return stopped

    def _is_current_session_locked(self, handle: OperationHandle) -> bool:
        return handle.session_id == self._session_id

    def _ensure_writer_locked(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run,
            name="debug-operation-log",
            daemon=True,
        )
        try:
            self._thread.start()
        except RuntimeError:
            self._thread = None
            self._enabled = False
            self._state = "unavailable"
            self._last_error_code = "OPERATION_LOG_THREAD_START_FAILED"
            self._notify_state(self._state)

    def _append_event_locked(
        self,
        action: str,
        status: str,
        *,
        operation: OperationHandle | None = None,
        payload: Mapping[str, Any] | None = None,
        source: str = "system",
        entry: str | None = None,
        job_kind: str | None = None,
        job_id: int | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
        reason_code: str | None = None,
        duration_ms: float | None = None,
        phase: str | None = None,
        allow_disabled: bool = False,
    ) -> bool:
        if self._session_id is None or (not self._enabled and not allow_disabled):
            return False
        self._sequence += 1
        now = time.monotonic()
        started_at = self._session_started_at or now
        event: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self._session_id,
            "recording_interval": self._recording_interval,
            "sequence": self._sequence,
            "timestamp_utc": _utc_timestamp(),
            "elapsed_ms": round(max(0.0, (now - started_at) * 1000.0), 3),
            "action": _safe_action(action),
            "status": status,
            "source": source if source in _ALLOWED_ORIGINS else "system",
        }
        if operation is not None:
            event["operation_id"] = operation.operation_id
            event["operation_recording_interval"] = operation.recording_interval
            event["action"] = operation.action
            event["source"] = operation.source
            entry = operation.entry
            job_kind = operation.job_kind or job_kind
            job_id = operation.job_id if operation.job_id is not None else job_id
            analysis_run_id = operation.analysis_run_id or analysis_run_id
            analysis_result_id = (
                operation.analysis_result_id or analysis_result_id
            )
        safe_entry = _safe_token(entry)
        if safe_entry:
            event["entry"] = safe_entry
        safe_job_kind = _safe_token(job_kind)
        if safe_job_kind:
            event["job_kind"] = safe_job_kind
        if type(job_id) is int and job_id >= 0:
            event["job_id"] = job_id
        safe_run_id = _safe_token(analysis_run_id)
        if safe_run_id:
            event["analysis_run_id"] = safe_run_id
        safe_result_id = _safe_token(analysis_result_id)
        if safe_result_id:
            event["analysis_result_id"] = safe_result_id
        safe_reason = _safe_token(reason_code)
        if safe_reason:
            event["reason_code"] = safe_reason
        safe_phase = _safe_token(phase)
        if safe_phase:
            event["phase"] = safe_phase
        if duration_ms is not None and math.isfinite(duration_ms):
            event["duration_ms"] = round(max(0.0, duration_ms), 3)
        safe_values = _safe_payload(payload)
        if safe_values:
            event["payload"] = safe_values
        if self._dropped_count:
            event["dropped_before"] = {
                "count": self._dropped_count,
                "sequence_start": self._dropped_sequence_start,
                "sequence_end": self._dropped_sequence_end,
            }
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            if self._dropped_count == 0:
                self._dropped_sequence_start = self._sequence
            self._dropped_sequence_end = self._sequence
            self._dropped_count += 1
            return False
        self._dropped_count = 0
        self._dropped_sequence_start = None
        self._dropped_sequence_end = None
        return True

    def _run(self) -> None:
        path = self._path
        if path is None:
            self._set_failed("OPERATION_LOG_PATH_UNAVAILABLE")
            self._drain_until_shutdown()
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                self._set_state_from_worker("recording" if self.enabled else "paused")
                for event in iter(self._queue.get, None):
                    try:
                        if not self._capacity_reached and self.state not in {
                            "unavailable",
                            "degraded",
                        }:
                            self._write_event(handle, event)
                    finally:
                        self._queue.task_done()
                self._queue.task_done()
                handle.flush()
        except (OSError, ValueError):
            self._set_failed("OPERATION_LOG_WRITE_FAILED")
            self._drain_until_shutdown()

    def _write_event(self, handle, event: dict[str, Any]) -> None:
        line = json.dumps(
            event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ) + "\n"
        encoded = line.encode("utf-8")
        limit_event = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self._session_id,
            "recording_interval": self._recording_interval,
            "sequence": event.get("sequence"),
            "timestamp_utc": _utc_timestamp(),
            "elapsed_ms": event.get("elapsed_ms", 0.0),
            "action": "recording_stopped",
            "status": "recording_stopped",
            "source": "system",
            "reason_code": "session_size_limit",
            "payload": {"dropped_count": self._queue.qsize() + 1},
        }
        limit_line = json.dumps(
            limit_event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        limit_bytes = limit_line.encode("utf-8")
        if (
            self._bytes_written + len(encoded) + len(limit_bytes)
            > self.max_session_bytes
        ):
            if self._bytes_written + len(limit_bytes) <= self.max_session_bytes:
                handle.write(limit_line)
                handle.flush()
                self._bytes_written += len(limit_bytes)
            with self._lock:
                self._capacity_reached = True
                self._enabled = False
                self._state = "degraded"
                self._last_error_code = "OPERATION_LOG_SIZE_LIMIT_REACHED"
            self._notify_state("degraded")
            return
        handle.write(line)
        handle.flush()
        self._bytes_written += len(encoded)

    def _drain_until_shutdown(self) -> None:
        while True:
            event = self._queue.get()
            self._queue.task_done()
            if event is None:
                return

    def _set_failed(self, error_code: str) -> None:
        with self._lock:
            self._enabled = False
            self._state = "unavailable"
            self._last_error_code = error_code
        self._notify_state("unavailable")

    def _set_state_from_worker(self, state: str) -> None:
        with self._lock:
            if self._state not in {"unavailable", "degraded"}:
                self._state = state
        self._notify_state(self.state)

    def _notify_state(self, state: str) -> None:
        callback = self._on_state_change
        if callback is None:
            return
        try:
            callback(state, self.last_error_code, self.path)
        except Exception:
            pass
