"""Single-owner, best-effort persistence for MS28-B3 debug traces."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import queue
import re
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from src.core.analysis_debug_trace import AnalysisDebugTrace, safe_payload


EVENT_COLUMNS = (
    "schema_version",
    "analysis_run_id",
    "analysis_result_id",
    "projection_revision",
    "stage",
    "event_index",
    "vowel",
    "start_sec",
    "time_sec",
    "end_sec",
    "start_frame",
    "peak_frame",
    "end_frame",
    "peak_value",
    "local_peak",
    "global_peak",
    "zero_reason",
    "fallback_reason",
    "same_vowel_bridge",
    "cross_vowel_bridge",
    "burst_candidate",
    "long_role",
    "long_source_index",
    "shape_group_ids",
)

_CANONICAL_ARTIFACTS = {
    "audio_analysis": "audio_analysis.json",
    "rms_load": "rms_analysis.json",
    "whisper_timing": "whisper_timing.json",
    "timeline_initial": "timeline_initial.json",
    "pre_rms": "timeline_pre_rms.json",
    "post_rms": "timeline_post_rms_raw.json",
    "timeline_pre_rms": "timeline_pre_rms.json",
    "timeline_post_rms_raw": "timeline_post_rms_raw.json",
    "rms_refine": "timeline_refined.json",
    "timeline_refined": "timeline_refined.json",
    "peak_evaluation": "peak_observations.json",
    "observations": "peak_observations.json",
    "boundary_repairs": "boundary_repairs.json",
    "silence_observations": "silence_observations.json",
}

_PROJECTION_ARTIFACTS = {
    "projection_input": "projection_input.json",
    "effective_shape": "effective_shape_plan.json",
    "preview_projection": "preview_controls.json",
    "writer_projection": "writer_frames.json",
    "provenance": "provenance.json",
    "projection_comparison": "comparison.json",
    "silence_observations": "silence_observations.json",
}


def resolve_debug_root(*, module_file: str | Path | None = None) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "debug"
    source = Path(module_file or __file__).resolve()
    return source.parents[2] / "debug"


def _safe_stage_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:96] or "stage"


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _write_text_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _digest_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


class AnalysisDebugStore:
    """Persist trace snapshots on one daemon I/O thread without blocking callers."""

    def __init__(self, root: str | Path | None = None, *, queue_size: int = 64) -> None:
        self.root = Path(root) if root is not None else resolve_debug_root()
        self._queue: queue.Queue[AnalysisDebugTrace | None] = queue.Queue(maxsize=queue_size)
        self._thread = threading.Thread(target=self._run, name="analysis-debug-store", daemon=True)
        self._started = False
        self._shutdown = False
        self._lock = threading.Lock()
        self._pending_runs: dict[str, dict[str, Any]] = {}
        self.last_error_code: str | None = None
        self.dropped_count = 0

    def _ensure_started(self) -> None:
        with self._lock:
            if not self._started:
                self._started = True
                self._thread.start()

    def submit(self, trace: AnalysisDebugTrace | None) -> bool:
        if trace is None or not trace.record_enabled or self._shutdown:
            return False
        self._ensure_started()
        trace.attach_sink(self.submit)
        run_id = trace.analysis_run_id
        with self._lock:
            pending = self._pending_runs.get(run_id)
            if pending is not None:
                pending["dirty"] = True
                return True
            self._pending_runs[run_id] = {"trace": trace, "dirty": False}
        try:
            self._queue.put_nowait(trace)
            return True
        except queue.Full:
            with self._lock:
                self._pending_runs.pop(run_id, None)
            self.dropped_count += 1
            trace.mark_capture_status("degraded", notify=False)
            return False

    def flush(self, timeout: float = 5.0) -> bool:
        if not self._started:
            return True
        deadline = time.monotonic() + max(0.0, timeout)
        while self._queue.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.01)
        return self._queue.unfinished_tasks == 0

    def shutdown(self, timeout: float = 1.0) -> None:
        self._shutdown = True
        if not self._started:
            return
        try:
            self._queue.put(None, timeout=max(0.01, timeout))
        except queue.Full:
            return
        self._thread.join(timeout=max(0.01, timeout))

    def _run(self) -> None:
        while True:
            trace = self._queue.get()
            try:
                if trace is None:
                    return
                self._write_trace(trace)
            except Exception:
                self.last_error_code = "DEBUG_STORE_WRITE_FAILED"
                if trace is not None:
                    trace.mark_capture_status("unavailable", notify=False)
            finally:
                if trace is not None:
                    self._resubmit_if_dirty(trace)
                self._queue.task_done()

    def _resubmit_if_dirty(self, trace: AnalysisDebugTrace) -> None:
        run_id = trace.analysis_run_id
        with self._lock:
            pending = self._pending_runs.get(run_id)
            if pending is None:
                return
            if not pending["dirty"] or self._shutdown:
                self._pending_runs.pop(run_id, None)
                return
            pending["dirty"] = False
            try:
                self._queue.put_nowait(trace)
            except queue.Full:
                self._pending_runs.pop(run_id, None)
                self.dropped_count += 1
                trace.mark_capture_status("degraded", notify=False)

    def _write_trace(self, trace: AnalysisDebugTrace) -> None:
        snapshot = trace.snapshot(include_file_identity=True)
        run_dir = self.root / f"{trace.folder_timestamp}_{trace.analysis_run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        records = snapshot.get("records", [])
        artifacts: list[str] = []
        artifact_sequences: dict[str, int | None] = {}
        canonical_written: set[str] = set()
        projection_revisions: set[int] = set()
        boundary_records: list[dict[str, Any]] = []
        save_records: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            sequence = record.get("record_sequence")
            stage = str(record.get("stage") or "stage")
            stage_path = run_dir / "stages" / f"{int(sequence or 0):06d}_{_safe_stage_name(stage)}.json"
            _write_json_atomic(stage_path, safe_payload(record))
            stage_relative = str(stage_path.relative_to(run_dir))
            artifacts.append(stage_relative)
            artifact_sequences[stage_relative] = sequence
            if "boundary" in stage:
                boundary_records.append(safe_payload(record))
            canonical_name = _CANONICAL_ARTIFACTS.get(stage)
            if canonical_name and canonical_name not in canonical_written:
                canonical_path = run_dir / canonical_name
                _write_json_atomic(canonical_path, safe_payload(record.get("payload", {})))
                canonical_written.add(canonical_name)
                artifacts.append(canonical_name)
                artifact_sequences[canonical_name] = sequence
            projection_revision = record.get("projection_revision")
            projection_name = _PROJECTION_ARTIFACTS.get(stage)
            if isinstance(projection_revision, int) and projection_revision > 0:
                projection_revisions.add(projection_revision)
                if projection_name:
                    projection_path = (
                        run_dir
                        / "projections"
                        / str(projection_revision)
                        / projection_name
                    )
                    _write_json_atomic(projection_path, safe_payload(record.get("payload", {})))
                    projection_relative = str(projection_path.relative_to(run_dir))
                    artifacts.append(projection_relative)
                    artifact_sequences[projection_relative] = sequence
            action_id = record.get("action_id")
            if stage in {"gui_generation_request", "vmd_file_save"} and isinstance(action_id, str) and action_id:
                action_path = run_dir / "gui_actions" / f"{_safe_stage_name(action_id)}.json"
                _write_json_atomic(action_path, safe_payload(record))
                action_relative = str(action_path.relative_to(run_dir))
                artifacts.append(action_relative)
                artifact_sequences[action_relative] = sequence
                save_operation_id = record.get("save_operation_id")
                if isinstance(save_operation_id, str) and save_operation_id:
                    save_records.setdefault(save_operation_id, []).append(safe_payload(record))

        for save_operation_id, operation_records in save_records.items():
            save_path = run_dir / "saves" / f"{_safe_stage_name(save_operation_id)}.json"
            _write_json_atomic(
                save_path,
                {
                    "save_operation_id": save_operation_id,
                    "records": operation_records,
                },
            )
            save_relative = str(save_path.relative_to(run_dir))
            artifacts.append(save_relative)
            artifact_sequences[save_relative] = None

        if boundary_records:
            boundary_path = run_dir / "boundary_repairs.json"
            _write_json_atomic(boundary_path, {"repairs": boundary_records})
            artifacts.append("boundary_repairs.json")
            artifact_sequences["boundary_repairs.json"] = None

        events_path = run_dir / "events.csv"
        self._write_events(events_path, snapshot)
        artifacts.append("events.csv")
        artifact_sequences["events.csv"] = None
        for revision in sorted(projection_revisions):
            projection_events_path = run_dir / "projections" / str(revision) / "events.csv"
            self._write_events(
                projection_events_path,
                snapshot,
                projection_revision=revision,
            )
            projection_events_relative = str(projection_events_path.relative_to(run_dir))
            artifacts.append(projection_events_relative)
            artifact_sequences[projection_events_relative] = None
        diagnostics_path = run_dir / "diagnostics.txt"
        _write_text_atomic(diagnostics_path, self._diagnostics_text(snapshot))
        artifacts.append("diagnostics.txt")
        artifact_sequences["diagnostics.txt"] = None

        manifest = dict(snapshot)
        manifest.pop("records", None)
        manifest.pop("events", None)
        manifest["stage_status"] = [
            {
                "record_sequence": record.get("record_sequence"),
                "stage": record.get("stage"),
                "status": record.get("status"),
                "reason_code": record.get("reason_code"),
                "projection_revision": record.get("projection_revision"),
                "action_id": record.get("action_id"),
                "save_operation_id": record.get("save_operation_id"),
            }
            for record in records
        ]
        manifest["artifact_files"] = self._artifact_metadata(
            run_dir,
            artifacts,
            artifact_sequences=artifact_sequences,
        )
        manifest["capture_status"] = "degraded" if self.dropped_count else snapshot.get("capture_status")
        _write_json_atomic(run_dir / "manifest.json", safe_payload(manifest))

    def _artifact_metadata(
        self,
        run_dir: Path,
        artifacts: list[str],
        *,
        artifact_sequences: dict[str, int | None] | None = None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for relative_name in sorted(set(artifacts)):
            path = run_dir / relative_name
            try:
                size, digest = _digest_file(path)
            except OSError:
                continue
            result.append(
                {
                    "relative_name": relative_name,
                    "bytes": size,
                    "sha256": digest,
                    "record_sequence": (
                        artifact_sequences.get(relative_name)
                        if artifact_sequences is not None
                        else None
                    ),
                }
            )
        return result

    def _write_events(
        self,
        path: Path,
        snapshot: dict[str, Any],
        *,
        projection_revision: int | None = None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        for record in snapshot.get("records", []):
            if projection_revision is not None and record.get("projection_revision") != projection_revision:
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            timeline = payload.get("timeline")
            observations = payload.get("observations")
            items = timeline if isinstance(timeline, list) else observations if isinstance(observations, list) else []
            for item in items:
                if not isinstance(item, dict):
                    continue
                rows.append(
                    {
                        "schema_version": snapshot.get("schema_version"),
                        "analysis_run_id": snapshot.get("analysis_run_id"),
                        "analysis_result_id": snapshot.get("analysis_result_id"),
                        "projection_revision": record.get("projection_revision"),
                        "stage": record.get("stage"),
                        "event_index": item.get("event_index"),
                        "vowel": item.get("vowel"),
                        "start_sec": item.get("start_sec"),
                        "time_sec": item.get("time_sec"),
                        "end_sec": item.get("end_sec"),
                        "start_frame": item.get("start_frame"),
                        "peak_frame": item.get("peak_frame"),
                        "end_frame": item.get("end_frame"),
                        "peak_value": item.get("peak_value"),
                        "local_peak": item.get("local_peak"),
                        "global_peak": item.get("global_peak"),
                        "zero_reason": item.get("reason"),
                        "fallback_reason": payload.get("fallback_reason"),
                        "same_vowel_bridge": item.get("is_same_vowel_bridge_candidate"),
                        "cross_vowel_bridge": item.get("is_cross_vowel_transition_candidate"),
                        "burst_candidate": item.get("is_burst_candidate"),
                        "long_role": item.get("long_role"),
                        "long_source_index": item.get("long_vowel_source_token_index"),
                        "shape_group_ids": item.get("shape_group_ids"),
                    }
                )
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                writer = csv.DictWriter(handle, fieldnames=EVENT_COLUMNS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            os.replace(temp_name, path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    @staticmethod
    def _diagnostics_text(snapshot: dict[str, Any]) -> str:
        lines = [
            "MS28-B3 Analysis Debug Trace",
            f"analysis_run_id={snapshot.get('analysis_run_id')}",
            f"capture_status={snapshot.get('capture_status')}",
        ]
        for record in snapshot.get("records", []):
            lines.append(
                "sequence={sequence} stage={stage} status={status} reason={reason}".format(
                    sequence=record.get("record_sequence", ""),
                    stage=record.get("stage", ""),
                    status=record.get("status", ""),
                    reason=record.get("reason_code", ""),
                )
            )
        return "\n".join(lines) + "\n"
