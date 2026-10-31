"""Strict, UI-independent capture contracts for MS31-B1 evidence."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from src.core.canonical_morph_value import POLICY_ID
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    build_base_plan_identity,
)
from src.core.event_adjustment import AdjustmentLayerSnapshot
from src.core.final_morph_plan import CURVE_POLICY_ID
from src.core.final_morph_producer import make_identity_context
from src.core.model_profile_state import ModelProfileResolutionStatus, ModelProfileState
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from src.vmd_writer.final_morph_legacy_bridge import capture_issuer_evidence
from src.vmd_writer.writer import _finalize_morph_value


SNAPSHOT_SCHEMA = "final-morph-snapshot/v1"
CAPTURE_LEDGER_SCHEMA = "ms31-capture-ledger/v1"
OBSERVATIONS_SCHEMA = "ms31-closure-observations/v1"
CAPTURE_EXPECTATIONS_SCHEMA = "ms31-capture-expectations/v1"
CROSSFADE_POLICY_ID = "effective-shape-manual-crossfade/v1"


class CaptureContractError(ValueError):
    """Raised when a capture is incomplete or contradictory."""


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise CaptureContractError(f"{field_name} must be non-empty text")
    return value


def _require_int(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise CaptureContractError(f"{field_name} must be an integer >= {minimum}")
    return value


def _require_sha256(value: object, field_name: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise CaptureContractError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise CaptureContractError(f"{field_name} must use lowercase hex")
    return value


def _json_value(value: object, *, path: str = "value") -> Any:
    """Convert only known immutable data to JSON values; never fall back to repr."""
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CaptureContractError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise CaptureContractError(f"{path} contains a non-text mapping key")
        return {key: _json_value(value[key], path=f"{path}.{key}") for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_json_value(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _json_value(getattr(value, item.name), path=f"{path}.{item.name}")
            for item in fields(value)
        }
    raise CaptureContractError(f"{path} contains unsupported type {type(value).__name__}")


def _canonical_digest_value(value: object) -> Any:
    """Encode floats by their exact binary64 value for stable operation hashes."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CaptureContractError("snapshot contains a non-finite float")
        return {"binary64": value.hex()}
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise CaptureContractError("snapshot mapping keys must be text")
        return {key: _canonical_digest_value(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_canonical_digest_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _canonical_digest_value(getattr(value, item.name))
            for item in fields(value)
        }
    raise CaptureContractError(f"snapshot contains unsupported type {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            _json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise CaptureContractError(f"value cannot be serialized as canonical JSON: {error}") from error


def snapshot_digest(value: object) -> str:
    payload = json.dumps(
        _canonical_digest_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_profile_resolution(profile_state: object) -> dict[str, object]:
    """Return truthful profile provenance or reject a no-profile fallback."""
    if not isinstance(profile_state, ModelProfileState):
        raise CaptureContractError("profile_state must be ModelProfileState")
    status = profile_state.resolution_status
    profile_id = profile_state.active_model_profile_id
    baseline_id = profile_state.active_profile_baseline_preset_id
    reason = profile_state.resolution_reason_code
    if status is ModelProfileResolutionStatus.NO_PROFILE:
        if profile_id is not None or baseline_id is not None or reason is not None:
            raise CaptureContractError("NO_PROFILE state contains profile identity")
    elif status is ModelProfileResolutionStatus.FALLBACK_NO_PROFILE:
        raise CaptureContractError("profile resolution fell back to no profile")
    elif status in {
        ModelProfileResolutionStatus.RESOLVED,
        ModelProfileResolutionStatus.FALLBACK_PROFILE_DEFAULT,
    }:
        if type(profile_id) is not str or not profile_id:
            raise CaptureContractError("resolved profile state has no active profile ID")
        if type(baseline_id) is not str or not baseline_id:
            raise CaptureContractError("resolved profile state has no baseline preset ID")
    else:
        raise CaptureContractError("profile resolution status is unsupported")
    return {
        "active_model_profile_id": profile_id,
        "active_profile_baseline_preset_id": baseline_id,
        "resolution_status": status.value,
        "resolution_reason_code": reason,
    }


@dataclass(frozen=True, slots=True)
class CaptureOrigin:
    """Analysis identity tied to one adopted run and its exact input files."""

    source_run_id: str
    analysis_generation: int
    analysis_result_id: str
    input_mode: str
    audio_sha256: str
    text_sha256: str | None

    def __post_init__(self) -> None:
        _require_text(self.source_run_id, "source_run_id")
        _require_int(self.analysis_generation, "analysis_generation")
        _require_text(self.analysis_result_id, "analysis_result_id")
        if type(self.input_mode) is not str or self.input_mode not in {"text_audio", "voice_only"}:
            raise CaptureContractError("input_mode is unsupported")
        _require_sha256(self.audio_sha256, "audio_sha256")
        if self.input_mode == "text_audio":
            _require_sha256(self.text_sha256, "text_sha256")
        elif self.text_sha256 is not None:
            raise CaptureContractError("voice_only origin must not include a text hash")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_run_id": self.source_run_id,
            "analysis_generation": self.analysis_generation,
            "analysis_result_id": self.analysis_result_id,
            "input_mode": self.input_mode,
            "audio_sha256": self.audio_sha256,
            "text_sha256": self.text_sha256,
        }


class CaptureSessionLedger:
    """Append-only manual-operation revision ledger for one capture session."""

    __slots__ = ("origin", "initial_snapshot_digest", "manual_revision", "entries", "_current_digest")

    def __init__(self, *, origin: CaptureOrigin, initial_snapshot: object) -> None:
        if not isinstance(origin, CaptureOrigin):
            raise CaptureContractError("origin must be CaptureOrigin")
        adjustments = getattr(initial_snapshot, "adjustments", None)
        identity = getattr(initial_snapshot, "base_plan_identity", None)
        if adjustments != () or identity is None:
            raise CaptureContractError("ledger must begin from an explicitly empty adjustment snapshot")
        self.origin = origin
        self.initial_snapshot_digest = snapshot_digest(initial_snapshot)
        self.manual_revision = 0
        self._current_digest = self.initial_snapshot_digest
        self.entries: list[dict[str, object]] = [
            {
                "sequence": 0,
                "operation": "initial_empty_snapshot",
                "outcome": "observed",
                "before_snapshot_digest": None,
                "after_snapshot_digest": self.initial_snapshot_digest,
                "manual_revision": 0,
                "source_run_id": origin.source_run_id,
                "analysis_generation": origin.analysis_generation,
            }
        ]

    def record_operation(
        self,
        *,
        operation: str,
        outcome: str,
        before_snapshot: object,
        after_snapshot: object,
        origin: CaptureOrigin,
    ) -> int:
        _require_text(operation, "operation")
        if type(outcome) is not str or outcome not in {"committed", "rejected", "no_op"}:
            raise CaptureContractError("operation outcome is unsupported")
        if not isinstance(origin, CaptureOrigin) or origin.to_dict() != self.origin.to_dict():
            raise CaptureContractError("operation belongs to a different capture origin")
        before_digest = snapshot_digest(before_snapshot)
        after_digest = snapshot_digest(after_snapshot)
        if before_digest != self._current_digest:
            raise CaptureContractError("operation before snapshot does not match ledger head")
        changed = before_digest != after_digest
        if outcome == "committed" and not changed:
            raise CaptureContractError("committed operation did not change the snapshot")
        if outcome in {"rejected", "no_op"} and changed:
            raise CaptureContractError("rejected or no-op operation changed the snapshot")
        if changed:
            self.manual_revision += 1
            self._current_digest = after_digest
        self.entries.append(
            {
                "sequence": len(self.entries),
                "operation": operation,
                "outcome": outcome,
                "before_snapshot_digest": before_digest,
                "after_snapshot_digest": after_digest,
                "manual_revision": self.manual_revision,
                "source_run_id": self.origin.source_run_id,
                "analysis_generation": self.origin.analysis_generation,
            }
        )
        return self.manual_revision

    def assert_current(self, snapshot: object, origin: CaptureOrigin) -> None:
        if not isinstance(origin, CaptureOrigin) or origin.to_dict() != self.origin.to_dict():
            raise CaptureContractError("current projection belongs to a different capture origin")
        if snapshot_digest(snapshot) != self._current_digest:
            raise CaptureContractError("current adjustment snapshot differs from the ledger head")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_id": CAPTURE_LEDGER_SCHEMA,
            "origin": self.origin.to_dict(),
            "initial_snapshot_digest": self.initial_snapshot_digest,
            "manual_revision": self.manual_revision,
            "entries": list(self.entries),
        }


def build_captured_snapshot(
    *,
    trace: object,
    base_input: BaseTimingPlanInput,
    adjustment_snapshot: AdjustmentLayerSnapshot,
    effective_plan_snapshot: object,
    manual_revision: int,
    resolved_profile_id: str | None,
    morph_name_set_id: str,
) -> dict[str, object]:
    """Bind complete typed analysis inputs to their adopted debug trace."""
    if not isinstance(base_input, BaseTimingPlanInput):
        raise CaptureContractError("base_input must be BaseTimingPlanInput")
    if not isinstance(adjustment_snapshot, AdjustmentLayerSnapshot):
        raise CaptureContractError("adjustment_snapshot must be explicit and typed")
    source_run_id = getattr(trace, "analysis_run_id", None)
    job_id = getattr(trace, "job_id", None)
    result_id = getattr(trace, "analysis_result_id", None)
    if type(source_run_id) is not str or not source_run_id:
        raise CaptureContractError("adopted trace has no analysis_run_id")
    _require_int(job_id, "trace.job_id")
    if type(result_id) is not str or not result_id:
        raise CaptureContractError("adopted trace has no analysis_result_id")
    if getattr(trace, "capture_status", None) != "completed":
        raise CaptureContractError("adopted trace is not complete")
    if getattr(getattr(trace, "owner", None), "analysis_result_id", None) != result_id:
        raise CaptureContractError("trace owner does not identify its adopted analysis result")
    if effective_plan_snapshot is None:
        raise CaptureContractError("effective plan is missing")
    expected_base_identity = build_base_plan_identity(base_input)
    effective_base_identity = getattr(effective_plan_snapshot, "base_plan_identity", None)
    if expected_base_identity != getattr(adjustment_snapshot, "base_plan_identity", None):
        raise CaptureContractError("adjustment snapshot does not belong to base input")
    if expected_base_identity != effective_base_identity:
        raise CaptureContractError("effective plan does not belong to base input")
    if getattr(effective_plan_snapshot, "canonical_adjustment_snapshot", None) != adjustment_snapshot:
        raise CaptureContractError("effective plan does not match current adjustment snapshot")
    _require_int(manual_revision, "manual_revision")
    identity = make_identity_context(
        source_run_id=source_run_id,
        analysis_generation=job_id,
        manual_revision=manual_revision,
        base_input=base_input,
        effective_plan_snapshot=effective_plan_snapshot,
        resolved_profile_id=resolved_profile_id,
        morph_name_set_id=morph_name_set_id,
        numeric_policy_id=POLICY_ID,
        curve_policy_id=CURVE_POLICY_ID,
        silence_policy_id=getattr(effective_plan_snapshot, "silence_policy", None),
        crossfade_policy_id=CROSSFADE_POLICY_ID,
    )
    issuer_evidence = capture_issuer_evidence(
        effective_plan_snapshot,
        source_run_id=source_run_id,
        analysis_generation=job_id,
        manual_revision=manual_revision,
    )
    return {
        "schema_id": SNAPSHOT_SCHEMA,
        "input_kind": "captured_snapshot",
        "identity_context": identity,
        "base_input": base_input,
        "adjustment_snapshot": adjustment_snapshot,
        "effective_plan_snapshot": effective_plan_snapshot,
        "issuer_evidence": issuer_evidence,
    }


def export_full_snapshot(snapshot: object) -> bytes:
    """Serialize the exact MS30 seven-field snapshot shape with binary64 fidelity."""
    if not isinstance(snapshot, Mapping):
        raise CaptureContractError("snapshot must be a mapping")
    expected = {
        "schema_id",
        "input_kind",
        "identity_context",
        "base_input",
        "adjustment_snapshot",
        "effective_plan_snapshot",
        "issuer_evidence",
    }
    if set(snapshot) != expected:
        raise CaptureContractError("snapshot has missing or unknown fields")
    if snapshot["schema_id"] != SNAPSHOT_SCHEMA or snapshot["input_kind"] != "captured_snapshot":
        raise CaptureContractError("snapshot schema or input kind is unsupported")
    payload = canonical_json_bytes(snapshot)
    round_trip = json.loads(payload.decode("utf-8"))
    if _json_binary64_tree(snapshot) != _json_binary64_tree(round_trip):
        raise CaptureContractError("snapshot JSON round-trip changed a binary64 value")
    return payload


def _json_binary64_tree(value: object) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CaptureContractError("snapshot contains a non-finite float")
        return value.hex()
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise CaptureContractError("snapshot mapping keys must be text")
        return {key: _json_binary64_tree(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_json_binary64_tree(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _json_binary64_tree(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    raise CaptureContractError(f"snapshot contains unsupported type {type(value).__name__}")


def build_capture_baseline(
    effective_plan: object,
    *,
    output_morph_names: tuple[str, ...],
) -> dict[str, object]:
    """Build the old-writer scalar and binary32 baseline independently of MS30."""
    frames = build_morph_frames_from_effective_shape_plan(
        effective_plan,
        apply_final_normalization=True,
        output_morph_names=output_morph_names,
    )
    points: list[dict[str, object]] = []
    for frame_no, morph_name, raw_value in frames:
        value = _finalize_morph_value(raw_value)
        binary32 = struct.pack("<f", value).hex()
        points.append(
            {
                "frame_no": frame_no,
                "semantic_morph": next(
                    semantic
                    for semantic, output_name in zip(("あ", "い", "う", "え", "お"), output_morph_names)
                    if output_name == morph_name
                ),
                "output_morph_name": morph_name,
                "value_hex": value.hex(),
                "binary32_hex": binary32,
            }
        )
    return {
        "schema_id": "final-morph-shadow-baseline/v1",
        "points": points,
    }


def build_capture_observations(
    *,
    origin: CaptureOrigin,
    effective_plan: object,
    preview_points: object,
    writer_before_normalization: object,
    writer_after_normalization: object,
    saved_vmd_readback: object | None,
) -> dict[str, object]:
    """Capture existing source-event, shape, closure, and output observations."""
    if not isinstance(origin, CaptureOrigin):
        raise CaptureContractError("origin must be CaptureOrigin")
    shapes = tuple(getattr(effective_plan, "shapes", ()))
    contract = getattr(effective_plan, "normalization_contract", None)
    if contract is None:
        raise CaptureContractError("effective plan has no normalization contract")
    return {
        "schema_id": OBSERVATIONS_SCHEMA,
        "origin": origin.to_dict(),
        "reproduction": {
            "status": "not_evaluable",
            "scope": [],
            "reason": "symptom expectations have not been independently reviewed",
        },
        "effective_events": _json_value(getattr(effective_plan, "effective_events", ())),
        "base_events": _json_value(getattr(effective_plan, "base_events", ())),
        "shapes": [
            {
                "shape_ordinal": ordinal,
                "semantic_morph": getattr(shape, "vowel", None),
                "shape_kind": getattr(shape, "shape_kind", None),
                "event_ranges": _json_value(getattr(shape, "event_ranges", ())),
                "source_event_indices": _json_value(getattr(shape, "real_base_event_indices", ())),
                "control_points": [
                    {
                        "frame_no": getattr(point, "frame_no", None),
                        "value_hex": float(getattr(point, "value")).hex(),
                        "point_kind": getattr(point, "point_kind", None),
                    }
                    for point in tuple(getattr(shape, "control_points", ()))
                ],
                "resolved_tail": _json_value(getattr(shape, "resolved_tail", None)),
            }
            for ordinal, shape in enumerate(shapes)
        ],
        "normalization_contract": _json_value(contract),
        "silence_core_frame_ranges": _json_value(
            getattr(effective_plan, "silence_core_frame_ranges", ())
        ),
        "silence_policy": getattr(effective_plan, "silence_policy", None),
        "preview_points": _json_value(preview_points),
        "writer_frames_before_normalization": _json_value(writer_before_normalization),
        "writer_frames_after_normalization": _json_value(writer_after_normalization),
        "saved_vmd_readback": _json_value(saved_vmd_readback),
    }


__all__ = [
    "CAPTURE_EXPECTATIONS_SCHEMA",
    "CAPTURE_LEDGER_SCHEMA",
    "CaptureContractError",
    "CaptureOrigin",
    "CaptureSessionLedger",
    "OBSERVATIONS_SCHEMA",
    "SNAPSHOT_SCHEMA",
    "build_capture_baseline",
    "build_capture_observations",
    "build_captured_snapshot",
    "capture_profile_resolution",
    "canonical_json_bytes",
    "export_full_snapshot",
    "sha256_file",
    "snapshot_digest",
]
