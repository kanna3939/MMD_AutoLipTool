"""Safe, session-local tracing for MS28-B3 analysis diagnostics.

The trace object deliberately stores only primitive diagnostic data.  Input
paths and text are kept in memory only long enough for the debug store to
derive a basename, size, and digest; they are never part of a serialized
payload.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import math
import os
import platform
import re
import sys
import threading
import tomllib
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = 1
DEBUG_VOWEL_ORDER = ("あ", "い", "う", "え", "お")
_BLOCKED_KEY_PARTS = (
    "absolute_path",
    "model_path",
    "transcription_text",
    "text_content",
    "exception_detail",
    "traceback",
    "raw_result",
)
_ANALYSIS_TEXT_SOURCE_PRIORITY = {
    "initial_snapshot": 0,
    "provided": 1,
    "text_file": 2,
    "whisper_transcription": 3,
    "user_edited_transcription": 4,
}


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _folder_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def _sanitize_basename(value: str) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)
    value = value.replace("/", "_").replace("\\", "_")
    return value[:160]


def _safe_value(value: Any, *, key: str = "") -> Any:
    lowered_key = key.lower()
    if any(part in lowered_key for part in _BLOCKED_KEY_PARTS):
        return None
    if lowered_key.endswith("path") or lowered_key.endswith("_path"):
        return None
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            safe_key = str(raw_key)
            safe_value = _safe_value(raw_value, key=safe_key)
            if safe_value is not None:
                result[safe_key] = safe_value
        return result
    if isinstance(value, (tuple, list)):
        return [item for item in (_safe_value(item, key=key) for item in value) if item is not None]
    return None


def safe_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    value = _safe_value(payload or {})
    return value if isinstance(value, dict) else {}


def _file_identity(path_value: str | Path | None) -> dict[str, Any]:
    if not path_value:
        return {"status": "not_applicable"}
    path = Path(path_value)
    result: dict[str, Any] = {
        "file_basename": _sanitize_basename(path.name),
        "status": "unavailable",
    }
    try:
        stat = path.stat()
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        result.update(
            {
                "status": "observed",
                "bytes": int(stat.st_size),
                "sha256": digest.hexdigest(),
                "hash_observed_at": _timestamp(),
            }
        )
    except (OSError, ValueError):
        result["hash_observed_at"] = _timestamp()
    return result


def _model_identity(model_identity: Any) -> dict[str, Any]:
    if model_identity is None:
        return {"status": "unavailable"}
    result = {
        "model_key": getattr(model_identity, "model_key", None),
        "manifest_identity": getattr(model_identity, "manifest_identity", None),
        "package_version": getattr(model_identity, "package_version", None),
    }
    safe = safe_payload(result)
    return safe or {"status": "unavailable"}


def _resolve_app_version() -> str:
    try:
        return importlib.metadata.version("mmd-autolip-tool")
    except importlib.metadata.PackageNotFoundError:
        pass

    candidates = [Path(__file__).resolve().parents[2] / "pyproject.toml"]
    if getattr(sys, "frozen", False) and sys.executable:
        candidates.append(Path(sys.executable).resolve().parent / "pyproject.toml")
    for candidate in candidates:
        try:
            with candidate.open("rb") as handle:
                project = tomllib.load(handle).get("project", {})
            version = project.get("version") if isinstance(project, dict) else None
            if isinstance(version, str) and version.strip():
                return version.strip()
        except (OSError, tomllib.TOMLDecodeError):
            continue
    return "unavailable"


def _runtime_identity() -> dict[str, Any]:
    executable_basename = "unavailable"
    if sys.executable:
        executable_basename = _sanitize_basename(Path(sys.executable).name) or "unavailable"
    raw_build_id = os.environ.get("MMD_AUTOLIPTOOL_BUILD_ID", "")
    build_identifier = (
        raw_build_id
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,96}", raw_build_id)
        else "unavailable"
    )
    return {
        "execution_mode": "frozen" if getattr(sys, "frozen", False) else "source",
        "executable_basename": executable_basename,
        "python_version": platform.python_version(),
        "app_version": _resolve_app_version(),
        "build_identifier": build_identifier,
    }


def build_settings_provenance(
    *,
    settings_store: Any = None,
    generation_settings: Any = None,
    active_preset_id: str | None = None,
    active_model_profile_id: str | None = None,
) -> dict[str, Any]:
    """Return privacy-safe evidence about the settings used by an analysis."""

    settings_path = getattr(settings_store, "settings_path", None)
    file_info: dict[str, Any] = {
        "status": "not_available",
        "basename": "not_available",
        "scope": "not_available",
        "sha256": "not_available",
    }
    if settings_path:
        path = Path(settings_path)
        file_info["basename"] = _sanitize_basename(path.name) or "not_available"
        if getattr(sys, "frozen", False):
            file_info["scope"] = "frozen_executable_dir"
        else:
            file_info["scope"] = "source_repo_root"
        try:
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            file_info.update({"status": "observed", "sha256": digest.hexdigest()})
        except (OSError, ValueError):
            file_info["status"] = "missing_or_unreadable"

    generation = {
        "closing_hold_frames": getattr(generation_settings, "closing_hold_frames", "not_available"),
        "closing_softness_frames": getattr(
            generation_settings,
            "closing_softness_frames",
            "not_available",
        ),
        "long_vowel_mode": getattr(generation_settings, "long_vowel_mode", "not_available"),
    }
    return {
        "settings_file": file_info,
        "effective_generation_settings": safe_payload(generation),
        "active_preset_id": active_preset_id if active_preset_id is not None else "not_available",
        "active_model_profile_id": (
            active_model_profile_id
            if active_model_profile_id is not None
            else "not_available"
        ),
    }


@dataclass(frozen=True)
class DebugOwnerContext:
    owner_kind: str
    analysis_run_id: str
    analysis_result_id: str | None = None
    projection_revision: int | None = None
    action_id: str | None = None
    save_operation_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "owner_kind": self.owner_kind,
            "analysis_run_id": self.analysis_run_id,
            "analysis_result_id": self.analysis_result_id,
            "projection_revision": self.projection_revision,
            "action_id": self.action_id,
            "save_operation_id": self.save_operation_id,
        }


class AnalysisDebugTrace:
    """Thread-safe in-memory trace with a non-blocking persistence callback."""

    def __init__(
        self,
        *,
        input_mode: str,
        job_id: int | None,
        source_audio_path: str | Path | None = None,
        analysis_wav_path: str | Path | None = None,
        text_path: str | Path | None = None,
        analysis_text: str = "",
        model_identity: Any = None,
        timing_source: str | None = None,
        selected_model_key: str | None = None,
        selected_wav_analysis: Any = None,
        settings_provenance: Mapping[str, Any] | None = None,
    ) -> None:
        self.analysis_run_id = uuid.uuid4().hex
        self.folder_timestamp = _folder_timestamp()
        self.started_at = _timestamp()
        self.input_mode = str(input_mode)
        self.job_id = job_id if isinstance(job_id, int) and not isinstance(job_id, bool) else None
        self.record_enabled = True
        self.capture_status = "recording"
        self.runtime_identity = _runtime_identity()
        self._source_audio_path = str(source_audio_path) if source_audio_path else None
        self._analysis_wav_path = str(analysis_wav_path) if analysis_wav_path else None
        self._text_path = str(text_path) if text_path else None
        self._analysis_text_digest = hashlib.sha256(analysis_text.encode("utf-8")).hexdigest()
        self._analysis_text_length = len(analysis_text)
        self._analysis_text_source = "initial_snapshot"
        self._model_identity = model_identity
        self._timing_source = timing_source
        self._selected_model_key = selected_model_key
        self._selected_wav_analysis = selected_wav_analysis
        self.settings_provenance = safe_payload(settings_provenance)
        self._records: list[dict[str, Any]] = []
        self._events: list[dict[str, Any]] = []
        self._record_sequence = 0
        self._analysis_result_id: str | None = None
        self._projection_revision: int | None = None
        self._lock = threading.RLock()
        self._sink: Callable[["AnalysisDebugTrace"], bool] | None = None

    @property
    def owner(self) -> DebugOwnerContext:
        return DebugOwnerContext(
            owner_kind=("analysis_result" if self._analysis_result_id else "analysis_run"),
            analysis_run_id=self.analysis_run_id,
            analysis_result_id=self._analysis_result_id,
            projection_revision=self._projection_revision,
        )

    @property
    def analysis_result_id(self) -> str | None:
        return self._analysis_result_id

    @property
    def projection_revision(self) -> int | None:
        return self._projection_revision

    def attach_sink(self, sink: Callable[["AnalysisDebugTrace"], bool] | None) -> None:
        self._sink = sink

    def _notify(self) -> None:
        sink = self._sink
        if sink is None:
            return
        try:
            sink(self)
        except Exception:
            self.mark_capture_status("degraded", notify=False)

    def mark_capture_status(self, status: str, *, notify: bool = True) -> None:
        if status not in {"recording", "completed", "degraded", "unavailable"}:
            status = "degraded"
        with self._lock:
            self.capture_status = status
        if notify:
            self._notify()

    def set_analysis_text(self, text: str, *, source: str) -> None:
        if not isinstance(text, str):
            return
        normalized_source = str(source)
        with self._lock:
            self._analysis_text_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            self._analysis_text_length = len(text)
            current_priority = _ANALYSIS_TEXT_SOURCE_PRIORITY.get(
                self._analysis_text_source,
                0,
            )
            next_priority = _ANALYSIS_TEXT_SOURCE_PRIORITY.get(normalized_source, 0)
            if next_priority >= current_priority:
                self._analysis_text_source = normalized_source
        self._notify()

    def set_model_identity(self, model_identity: Any) -> None:
        if model_identity is None:
            return
        with self._lock:
            self._model_identity = model_identity
        self._notify()

    def set_timing_source(self, timing_source: str | None) -> None:
        if not isinstance(timing_source, str) or not timing_source.strip():
            return
        with self._lock:
            self._timing_source = timing_source.strip()
        self._notify()

    def record_stage(
        self,
        stage: str,
        *,
        status: str = "completed",
        payload: Mapping[str, Any] | None = None,
        reason_code: str | None = None,
        owner: DebugOwnerContext | None = None,
    ) -> None:
        with self._lock:
            self._record_sequence += 1
            record = {
                "schema_version": SCHEMA_VERSION,
                **(owner or self.owner).as_dict(),
                "record_sequence": self._record_sequence,
                "stage": str(stage),
                "status": str(status),
                "recorded_at": _timestamp(),
                "reason_code": reason_code,
                "payload": safe_payload(payload),
            }
            self._records.append(record)
        self._notify()

    def record_timeline(
        self,
        stage: str,
        timeline: Sequence[Any],
        *,
        status: str = "completed",
        reason_code: str | None = None,
        call_site: str | None = None,
    ) -> None:
        def _frame(value: Any) -> int | None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            normalized = float(value)
            return int(round(normalized * 30.0)) if math.isfinite(normalized) else None

        points: list[dict[str, Any]] = []
        for index, point in enumerate(timeline):
            points.append(
                {
                    "event_index": index,
                    "vowel": getattr(point, "vowel", None),
                    "time_sec": getattr(point, "time_sec", None),
                    "start_sec": getattr(point, "start_sec", None),
                    "end_sec": getattr(point, "end_sec", None),
                    "start_frame": _frame(getattr(point, "start_sec", None)),
                    "peak_frame": _frame(getattr(point, "time_sec", None)),
                    "end_frame": _frame(getattr(point, "end_sec", None)),
                    "duration_sec": getattr(point, "duration_sec", None),
                    "value": getattr(point, "value", None),
                    "peak_value": getattr(point, "peak_value", None),
                    "vowel_token_index": getattr(point, "vowel_token_index", None),
                    "is_long_vowel_continuation": getattr(point, "is_long_vowel_continuation", False),
                    "long_role": getattr(point, "long_vowel_role", None),
                    "long_vowel_source_token_index": getattr(
                        point, "long_vowel_source_token_index", None
                    ),
                }
            )
        self.record_stage(
            stage,
            status=status,
            reason_code=reason_code,
            payload={"call_site": call_site, "timeline": points},
        )

    def record_boundary_repair(
        self,
        *,
        repair_function: str,
        call_site: str,
        before: Sequence[Any],
        after: Sequence[Any],
    ) -> None:
        def _point_payload(point: Any) -> dict[str, Any]:
            return {
                "vowel": getattr(point, "vowel", None),
                "time_sec": getattr(point, "time_sec", None),
                "start_sec": getattr(point, "start_sec", None),
                "end_sec": getattr(point, "end_sec", None),
                "duration_sec": getattr(point, "duration_sec", None),
                "value": getattr(point, "value", None),
                "peak_value": getattr(point, "peak_value", None),
                "vowel_token_index": getattr(point, "vowel_token_index", None),
                "is_long_vowel_continuation": getattr(
                    point, "is_long_vowel_continuation", False
                ),
                "long_vowel_source_token_index": getattr(
                    point, "long_vowel_source_token_index", None
                ),
                "long_role": getattr(point, "long_vowel_role", None),
            }

        changed_indices = [
            index
            for index, (before_point, after_point) in enumerate(zip(before, after))
            if before_point != after_point
        ]
        self.record_stage(
            f"{call_site}.{repair_function}",
            payload={
                "repair_function": repair_function,
                "call_site": call_site,
                "before_count": len(before),
                "after_count": len(after),
                "before": [_point_payload(point) for point in before],
                "after": [_point_payload(point) for point in after],
                "changed": bool(changed_indices),
                "changed_indices": changed_indices,
                "reason_code": "changed" if changed_indices else "already_satisfied_or_unrepairable",
            },
        )

    def record_observations(self, observations: Sequence[Any], *, fallback_reason: str | None = None) -> None:
        def _silence_classification(item: Any) -> str:
            reason = getattr(item, "reason", None)
            item_peak = getattr(item, "peak_value", None)
            if fallback_reason == "rms_unavailable":
                return "not_evaluable"
            if reason in {"global_peak_zero", "rms_unavailable"}:
                return "explained"
            if isinstance(item_peak, (int, float)) and math.isfinite(float(item_peak)):
                return "suspicious" if float(item_peak) <= 0.0 else "not_applicable"
            return "not_evaluable"

        payload = {
            "fallback_reason": fallback_reason,
            "observations": [
                {
                    "event_index": getattr(item, "event_index", None),
                    "vowel": getattr(item, "vowel", None),
                    "time_sec": getattr(item, "time_sec", None),
                    "initial_interval_start_sec": getattr(item, "initial_interval_start_sec", None),
                    "initial_interval_end_sec": getattr(item, "initial_interval_end_sec", None),
                    "refined_interval_start_sec": getattr(item, "refined_interval_start_sec", None),
                    "refined_interval_end_sec": getattr(item, "refined_interval_end_sec", None),
                    "peak_window_start_sec": getattr(item, "peak_window_start_sec", None),
                    "peak_window_end_sec": getattr(item, "peak_window_end_sec", None),
                    "local_peak": getattr(item, "local_peak", None),
                    "global_peak": getattr(item, "global_peak", None),
                    "peak_value": getattr(item, "peak_value", None),
                    "reason": getattr(item, "reason", None),
                    "is_same_vowel_bridge_candidate": getattr(
                        item, "is_bridgeable_same_vowel_micro_gap_candidate", False
                    ),
                    "is_cross_vowel_transition_candidate": getattr(
                        item, "is_bridgeable_cross_vowel_transition_candidate", False
                    ),
                    "is_burst_candidate": getattr(item, "is_same_vowel_burst_candidate", False),
                    "long_role": getattr(item, "long_vowel_role", None),
                    "is_cross_vowel_zero_run_continuity_floor_candidate": getattr(
                        item, "is_cross_vowel_zero_run_continuity_floor_candidate", False
                    ),
                    "is_bridgeable_micro_gap_candidate": getattr(
                        item, "is_bridgeable_micro_gap_candidate", False
                    ),
                    "bridge_candidate_reason": getattr(item, "bridge_candidate_reason", None),
                    "previous_non_zero_event_index": getattr(
                        item, "previous_non_zero_event_index", None
                    ),
                    "next_non_zero_event_index": getattr(item, "next_non_zero_event_index", None),
                    "span_start_index": getattr(item, "span_start_index", None),
                    "span_end_index": getattr(item, "span_end_index", None),
                    "silence_classification": _silence_classification(item),
                }
                for item in observations
            ],
        }
        self.record_stage("observations", payload=payload)

    def adopt(self) -> str:
        with self._lock:
            if self._analysis_result_id is None:
                self._analysis_result_id = uuid.uuid4().hex
            result_id = self._analysis_result_id
        self.record_stage(
            "analysis_acceptance",
            payload={"decision": "adopted", "analysis_result_id": result_id},
        )
        return result_id

    def record_terminal(self, status: str, *, reason_code: str | None = None) -> None:
        self.record_stage("analysis_acceptance", status=status, reason_code=reason_code)
        self.mark_capture_status("completed")

    def start_projection_revision(self) -> int:
        with self._lock:
            self._projection_revision = 1 if self._projection_revision is None else self._projection_revision + 1
            revision = self._projection_revision
        self.record_stage(
            "projection_revision",
            payload={"projection_revision": revision},
        )
        return revision

    def record_action(
        self,
        action: str,
        *,
        payload: Mapping[str, Any] | None = None,
        status: str = "completed",
        save_operation_id: str | None = None,
    ) -> str:
        action_id = uuid.uuid4().hex
        owner = DebugOwnerContext(
            owner_kind="analysis_result",
            analysis_run_id=self.analysis_run_id,
            analysis_result_id=self._analysis_result_id,
            projection_revision=self._projection_revision,
            action_id=action_id,
            save_operation_id=save_operation_id,
        )
        self.record_stage(
            "vmd_file_save" if action.startswith("vmd_save_") else "gui_generation_request",
            status=status,
            owner=owner,
            payload={"action": action, **(payload or {})},
        )
        return action_id

    def snapshot(self, *, include_file_identity: bool = False) -> dict[str, Any]:
        with self._lock:
            records = [dict(record) for record in self._records]
            events = [dict(event) for event in self._events]
            capture_status = self.capture_status
            analysis_text_digest = self._analysis_text_digest
            analysis_text_length = self._analysis_text_length
            analysis_text_source = self._analysis_text_source
        input_identity: dict[str, Any] = {
            "source_audio": {"status": "deferred"},
            "analysis_wav": {"status": "deferred"},
            "text_file": {"status": "deferred"},
            "analysis_text": {
                "sha256": analysis_text_digest,
                "character_count": analysis_text_length,
                "source": analysis_text_source,
            },
            "timing": {"source": self._timing_source or "unknown"},
            "model": _model_identity(self._model_identity),
        }
        if include_file_identity:
            input_identity["source_audio"] = _file_identity(self._source_audio_path)
            input_identity["analysis_wav"] = _file_identity(self._analysis_wav_path)
            input_identity["text_file"] = _file_identity(self._text_path)
            if self._selected_wav_analysis is not None:
                input_identity["audio_metadata"] = safe_payload(
                    {
                        "duration_sec": getattr(self._selected_wav_analysis, "duration_sec", None),
                        "sample_rate_hz": getattr(self._selected_wav_analysis, "sample_rate_hz", None),
                        "channel_count": getattr(self._selected_wav_analysis, "channel_count", None),
                        "has_speech": getattr(self._selected_wav_analysis, "has_speech", None),
                        "speech_start_sec": getattr(self._selected_wav_analysis, "speech_start_sec", None),
                        "speech_end_sec": getattr(self._selected_wav_analysis, "speech_end_sec", None),
                    }
                )
        return {
            "schema_version": SCHEMA_VERSION,
            "owner": self.owner.as_dict(),
            "analysis_run_id": self.analysis_run_id,
            "analysis_result_id": self._analysis_result_id,
            "input_mode": self.input_mode,
            "job_id": self.job_id,
            "record_enabled": self.record_enabled,
            "debug_mode_snapshot": True,
            "started_at": self.started_at,
            "capture_status": capture_status,
            "runtime_identity": dict(self.runtime_identity),
            "settings_provenance": dict(self.settings_provenance),
            "input_identity": input_identity,
            "selected_model_key": self._selected_model_key,
            "records": records,
            "events": events,
        }


def build_debug_trace(
    *,
    input_mode: str,
    job_id: int,
    source_audio_path: str | Path | None,
    analysis_wav_path: str | Path | None,
    text_path: str | Path | None,
    analysis_text: str,
    model_identity: Any,
    timing_source: str | None,
    selected_model_key: str | None,
    selected_wav_analysis: Any,
    settings_provenance: Mapping[str, Any] | None = None,
) -> AnalysisDebugTrace:
    return AnalysisDebugTrace(
        input_mode=input_mode,
        job_id=job_id,
        source_audio_path=source_audio_path,
        analysis_wav_path=analysis_wav_path,
        text_path=text_path,
        analysis_text=analysis_text,
        model_identity=model_identity,
        timing_source=timing_source,
        selected_model_key=selected_model_key,
        selected_wav_analysis=selected_wav_analysis,
        settings_provenance=settings_provenance,
    )
