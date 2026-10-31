"""Shared, independently validated MS33-B4 final-output bindings."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Callable

from src.core.canonical_morph_value import CanonicalMorphValue
from src.core.cleanup_evaluation import (
    CleanupEvaluationRequest,
    verify_cleanup_artifact_content,
)
from src.core.cleanup_default_policy import (
    DefaultCleanupSelection,
    resolve_current_key_protections,
)
from src.core.event_cleanup import (
    CleanupPoint,
    EventCleanupInput,
    build_event_cleanup_candidate,
    resolve_event_cleanup,
    validate_event_cleanup_plan,
)
from src.core.final_morph_cleanup_plan import FinalMorphCleanupPlan
from src.core.final_morph_closure_plan import ClosurePlan
from src.core.final_morph_capture import snapshot_digest
from src.core.final_morph_plan import effective_plan_snapshot_digest
from src.core.effective_shape_plan import _build_effective_shape_plan
from src.core.final_morph_key_reduction_plan import (
    FinalMorphKeyReductionPlan,
    KeyReductionInput,
    ReductionPoint,
)
from src.core.final_output_projection import (
    FinalOutputIdentity,
    FinalOutputInputIdentity,
    SharedFinalOutputContext,
)
from src.core.cross_vowel_transition import TRANSITION_POLICY_V2
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER
from src.core.redundant_key_reduction import (
    build_key_reduction_candidate,
    resolve_redundant_keys,
    validate_key_reduction_plan,
)
from src.vmd_writer.final_morph_closure_adapter import ClosureProjection, ClosureWirePoint
from src.vmd_writer.final_morph_cleanup_adapter import project_validated_cleanup_plan
from src.vmd_writer.final_morph_key_reduction_adapter import project_validated_key_reduction_plan


class CleanupSharedOutputError(ValueError):
    """Raised when a candidate cannot be bound to its verified MS32 source."""


_ZERO_VALUE = CanonicalMorphValue.from_dict({
    "policy_id": "legacy-compatible-q10000/v1",
    "quantum": 10000,
    "units": "0",
    "value_kind": "quantized",
    "legacy_value_hex": None,
    "binary32_hex": "00000000",
    "wire_underflow": False,
})
_SHAPE_ORDINAL_RE = re.compile(r":shape:(\d+):point:")
_EVENT_SOURCE_RE = re.compile(r"^source:event:(\d+)$")
_B1_SHAPE_RECORD_RE = re.compile(r":shape:(\d+):point:(\d+)\Z")
_B1_FINAL_RECORD_RE = re.compile(r":final:(\d+):(\d+):([あいうえお])\Z")
_B1_EVENT_RECORD_RE = re.compile(r":event:(\d+)\Z")


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CleanupSharedOutputError("cleanup binding is not canonical JSON") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _canonical_lifecycle_value(value: object) -> object:
    """Encode the UI lifecycle signature's immutable values as strict JSON."""
    if isinstance(value, Enum):
        return {
            "enum_type": f"{type(value).__module__}.{type(value).__qualname__}",
            "value": _canonical_lifecycle_value(value.value),
        }
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CleanupSharedOutputError("cleanup lifecycle signature contains a non-finite float")
        return value
    if isinstance(value, Path):
        return {
            "path_type": f"{type(value).__module__}.{type(value).__qualname__}",
            "path": os.fspath(value),
        }
    if isinstance(value, tuple):
        return {"tuple": [_canonical_lifecycle_value(item) for item in value]}
    if isinstance(value, list):
        return {"list": [_canonical_lifecycle_value(item) for item in value]}
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise CleanupSharedOutputError("cleanup lifecycle signature contains a non-text key")
        return {
            "mapping": {
                key: _canonical_lifecycle_value(value[key])
                for key in sorted(value)
            }
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "dataclass_type": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {
                item.name: _canonical_lifecycle_value(getattr(value, item.name))
                for item in fields(value)
            },
        }
    raise CleanupSharedOutputError(
        f"cleanup lifecycle signature contains unsupported type {type(value).__name__}"
    )


def _check_cancelled(cancelled: Callable[[], bool] | None) -> None:
    if cancelled is not None and cancelled():
        raise CleanupSharedOutputError("cleanup candidate generation was cancelled")


@dataclass(frozen=True, slots=True)
class CleanupPointView:
    frame_no: int
    semantic_morph: str
    canonical_value: float
    binary32_hex: str
    source_ids: tuple[str, ...]
    source_event_indices: tuple[int, ...]
    point_kinds: tuple[str, ...]
    intent_origins: tuple[str, ...]
    requirement_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.frame_no, bool) or not isinstance(self.frame_no, int) or self.frame_no < 0:
            raise CleanupSharedOutputError("final point frame is invalid")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise CleanupSharedOutputError("final point morph is invalid")
        if (
            isinstance(self.canonical_value, bool)
            or not isinstance(self.canonical_value, (int, float))
            or not math.isfinite(float(self.canonical_value))
            or self.canonical_value < 0.0
        ):
            raise CleanupSharedOutputError("final point value is invalid")
        if type(self.binary32_hex) is not str:
            raise CleanupSharedOutputError("final point wire value is invalid")
        try:
            raw = bytes.fromhex(self.binary32_hex)
        except ValueError as error:
            raise CleanupSharedOutputError("final point wire bytes are invalid") from error
        try:
            expected = struct.pack("<f", float(self.canonical_value))
        except (OverflowError, struct.error) as error:
            raise CleanupSharedOutputError("final point wire value is invalid") from error
        decoded = struct.unpack("<f", raw)[0] if len(raw) == 4 else math.nan
        if len(raw) != 4 or raw != expected or not math.isfinite(decoded) or decoded < 0.0:
            raise CleanupSharedOutputError("final point wire bytes are invalid")
        for name in ("source_ids", "point_kinds", "intent_origins", "requirement_ids"):
            rows = getattr(self, name)
            if type(rows) is not tuple or any(type(item) is not str or not item for item in rows):
                raise CleanupSharedOutputError(f"final point {name} are invalid")
        if type(self.source_event_indices) is not tuple or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in self.source_event_indices
        ):
            raise CleanupSharedOutputError("final point event indices are invalid")


@dataclass(frozen=True, slots=True)
class CleanupSharedSummary:
    schema_id: str
    final_binding: str
    variant: str
    policy_digests: tuple[str, str]
    source_event_count: int
    suppressed_event_ids: tuple[str, ...]
    input_key_count: int
    final_key_count: int
    removed_keys: tuple[tuple[int, str], ...]
    event_reasons: tuple[tuple[str, str, tuple[str, ...]], ...]
    protected_reasons: tuple[tuple[str, ...], ...]
    summary_digest: str
    application_origin: str = "evaluation"
    event_component_state: str = "evaluated"
    key_component_state: str = "evaluated"
    selection_kind: str = "evaluation"
    selection_reason: str = "explicit_evaluation_request"

    def __post_init__(self) -> None:
        if self.schema_id != "cleanup-shared-summary/v1":
            raise CleanupSharedOutputError("cleanup summary schema is unsupported")
        if type(self.final_binding) is not str or len(self.final_binding) != 64:
            raise CleanupSharedOutputError("cleanup summary final binding is invalid")
        if any(character not in "0123456789abcdef" for character in self.final_binding):
            raise CleanupSharedOutputError("cleanup summary final binding is invalid")
        if self.variant not in {"baseline", "keys_only", "events_only", "events_and_keys"}:
            raise CleanupSharedOutputError("cleanup summary variant is invalid")
        if type(self.policy_digests) is not tuple or len(self.policy_digests) != 2:
            raise CleanupSharedOutputError("cleanup summary policies are invalid")
        if any(type(item) is not str or len(item) != 64 for item in self.policy_digests):
            raise CleanupSharedOutputError("cleanup summary policy digest is invalid")
        for name in ("source_event_count", "input_key_count", "final_key_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise CleanupSharedOutputError(f"cleanup summary {name} is invalid")
        if self.final_key_count > self.input_key_count:
            raise CleanupSharedOutputError("cleanup summary final key count exceeds input")
        if type(self.suppressed_event_ids) is not tuple or type(self.removed_keys) is not tuple:
            raise CleanupSharedOutputError("cleanup summary result lists are invalid")
        if type(self.event_reasons) is not tuple or type(self.protected_reasons) is not tuple:
            raise CleanupSharedOutputError("cleanup summary reasons are invalid")
        if self._computed_digest() != self.summary_digest:
            raise CleanupSharedOutputError("cleanup summary digest differs from its content")
        if self.application_origin not in {"evaluation", "adopted_default"}:
            raise CleanupSharedOutputError("cleanup summary application origin is invalid")
        if self.application_origin == "adopted_default" and (
            self.event_component_state != "not_applicable"
            or self.key_component_state not in {"applied", "not_applied", "not_applicable"}
            or self.selection_kind not in {"cleanup", "scope_excluded", "no_applicable"}
            or type(self.selection_reason) is not str
            or not self.selection_reason
        ):
            raise CleanupSharedOutputError("default cleanup summary component state is invalid")

    def _payload(self) -> dict[str, object]:
        payload = {
            "schema_id": self.schema_id,
            "final_binding": self.final_binding,
            "variant": self.variant,
            "policy_digests": list(self.policy_digests),
            "source_event_count": self.source_event_count,
            "suppressed_event_ids": list(self.suppressed_event_ids),
            "input_key_count": self.input_key_count,
            "final_key_count": self.final_key_count,
            "removed_keys": [[frame, morph] for frame, morph in self.removed_keys],
            "event_reasons": [
                {"event_id": event_id, "action": action, "reasons": list(reasons)}
                for event_id, action, reasons in self.event_reasons
            ],
            "protected_reasons": [list(rows) for rows in self.protected_reasons],
        }
        if self.application_origin == "adopted_default":
            payload["application_origin"] = self.application_origin
            payload["event_component_state"] = self.event_component_state
            payload["key_component_state"] = self.key_component_state
            payload["selection_kind"] = self.selection_kind
            payload["selection_reason"] = self.selection_reason
        return payload

    def _computed_digest(self) -> str:
        return _digest(self._payload())

    def to_dict(self) -> dict[str, object]:
        return {**self._payload(), "summary_digest": self.summary_digest}


@dataclass(frozen=True, slots=True)
class CleanupSharedOutputBinding:
    request: CleanupEvaluationRequest | None
    default_selection: DefaultCleanupSelection | None
    input_digest: str
    upstream_context: SharedFinalOutputContext
    event_issuer: EventCleanupInput | None
    event_plan: FinalMorphCleanupPlan | None
    reduction_issuer: KeyReductionInput | None
    reduction_plan: FinalMorphKeyReductionPlan | None
    final_plan: object
    final_plan_kind: str
    final_projection: ClosureProjection
    final_points: tuple[CleanupPointView, ...]
    summary: CleanupSharedSummary

    def __post_init__(self) -> None:
        if self.request is not None and not isinstance(self.request, CleanupEvaluationRequest):
            raise CleanupSharedOutputError("cleanup request is invalid")
        if self.default_selection is not None and not isinstance(
            self.default_selection, DefaultCleanupSelection
        ):
            raise CleanupSharedOutputError("default cleanup selection is invalid")
        if (self.request is None) == (self.default_selection is None):
            raise CleanupSharedOutputError("cleanup binding needs exactly one request or default selection")
        if type(self.input_digest) is not str or len(self.input_digest) != 64:
            raise CleanupSharedOutputError("cleanup input digest is invalid")
        if not isinstance(self.upstream_context, SharedFinalOutputContext):
            raise CleanupSharedOutputError("upstream context is invalid")
        if self.upstream_context.cleanup_binding is not None:
            raise CleanupSharedOutputError("recursive cleanup contexts are not supported")
        if self.final_plan_kind not in {"upstream", "event_cleanup", "key_reduction"}:
            raise CleanupSharedOutputError("cleanup final plan kind is invalid")
        if not isinstance(self.final_projection, ClosureProjection):
            raise CleanupSharedOutputError("cleanup final projection is invalid")
        if type(self.final_points) is not tuple or any(
            not isinstance(item, CleanupPointView) for item in self.final_points
        ):
            raise CleanupSharedOutputError("cleanup final point view is invalid")
        if not isinstance(self.summary, CleanupSharedSummary):
            raise CleanupSharedOutputError("cleanup summary is invalid")
        if self.request is not None and self.summary.application_origin != "evaluation":
            raise CleanupSharedOutputError("evaluation cleanup summary origin is invalid")
        if self.default_selection is not None and self.summary.application_origin != "adopted_default":
            raise CleanupSharedOutputError("default cleanup summary origin is invalid")


def _input_digest(
    upstream: SharedFinalOutputContext,
    request: CleanupEvaluationRequest | None,
    default_selection: DefaultCleanupSelection | None = None,
) -> str:
    if (request is None) == (default_selection is None):
        raise CleanupSharedOutputError("cleanup input digest needs exactly one selection source")
    if request is not None:
        payload = {
            "schema_id": "cleanup-shared-input/v1",
            "request_digest": request.request_digest,
            "upstream_binding": upstream.identity.binding_digest,
            "upstream_input_binding": upstream.input_identity.semantic_binding,
            "ticket": upstream.ticket,
            "lifecycle_epoch": upstream.lifecycle_epoch,
            "lifecycle_signature": _canonical_lifecycle_value(
                upstream.lifecycle_signature or ()
            ),
        }
    else:
        payload = {
            "schema_id": "cleanup-default-shared-input/v1",
            "default_selection_digest": default_selection.selection_digest,
            "upstream_binding": upstream.identity.binding_digest,
            "upstream_input_binding": upstream.input_identity.semantic_binding,
            "ticket": upstream.ticket,
            "lifecycle_epoch": upstream.lifecycle_epoch,
            "lifecycle_signature": _canonical_lifecycle_value(
                upstream.lifecycle_signature or ()
            ),
        }
    return _digest(payload)


def _read_locked_b1_bundle(
    request: CleanupEvaluationRequest,
    source_refs: dict[str, object],
    historical_identity: dict[str, object],
) -> tuple[object, object, dict[str, object], dict[str, object]]:
    """Recheck the accepted B1 plan/VMD/readback bundle attached to a locked case."""
    from src.core.final_morph_transition_plan import (
        TransitionPlanError,
        read_final_morph_transition_plan,
    )

    def strict_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise CleanupSharedOutputError("locked B1 evidence contains a duplicate JSON field")
            result[key] = value
        return result

    def read_ref(role: str) -> tuple[Path, dict[str, object]]:
        reference = source_refs.get(role)
        if reference is None:
            raise CleanupSharedOutputError(f"locked B1 {role} reference is missing")
        try:
            verify_cleanup_artifact_content(reference)
            path = Path(reference.path).resolve(strict=True)
            value = json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=strict_pairs,
                parse_constant=lambda _value: (_ for _ in ()).throw(
                    CleanupSharedOutputError("locked B1 evidence contains a non-finite number")
                ),
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise CleanupSharedOutputError(f"locked B1 {role} evidence cannot be read") from error
        if type(value) is not dict:
            raise CleanupSharedOutputError(f"locked B1 {role} evidence is not an object")
        return path, value

    for role in (
        "capture_manifest", "baseline_plan", "baseline_vmd", "baseline_readback",
        "b1_research", "b1_audit",
    ):
        reference = source_refs.get(role)
        if reference is None:
            raise CleanupSharedOutputError(f"locked B1 {role} reference is missing")
        try:
            verify_cleanup_artifact_content(reference)
        except ValueError as error:
            raise CleanupSharedOutputError(f"locked B1 {role} reference is invalid") from error
    research_ref = source_refs["b1_research"]
    audit_ref = source_refs["b1_audit"]
    if research_ref not in request.b1_contract_refs or audit_ref not in request.b1_contract_refs:
        raise CleanupSharedOutputError("locked B1 accepted audit/research refs are not request-bound")
    research_path, research = read_ref("b1_research")
    _audit_path, audit = read_ref("b1_audit")
    if (
        research.get("schema_id") != "ms33-b1-research/v1"
        or research.get("status") != "complete"
        or type(research.get("run_id")) is not str
        or audit.get("schema_id") != "ms33-b1-contract-check/v1"
        or audit.get("exit_code") != 0
        or audit.get("issues") != []
        or audit.get("insufficient") != []
    ):
        raise CleanupSharedOutputError("locked B1 audit/research is not accepted")
    acceptance = audit.get("acceptance")
    gates = audit.get("gates")
    gate_states = {
        row.get("gate_id"): row.get("status") for row in gates if type(row) is dict
    } if type(gates) is list else {}
    audit_research = audit.get("input_refs", {}).get("research") if type(audit.get("input_refs")) is dict else None
    research_ref_dict = research_ref.to_dict()
    if (
        type(acceptance) is not dict
        or acceptance.get("b1") != "complete"
        or acceptance.get("G33-01") != "established"
        or acceptance.get("G33-01K") != "established"
        or any(gate_states.get(gate) != "established" for gate in ("G33-00", "G33-01", "G33-01K"))
        or type(audit_research) is not dict
        or audit_research != research_ref_dict
    ):
        raise CleanupSharedOutputError("locked B1 audit does not bind its accepted research run")
    research_cases = research.get("cases")
    if type(research_cases) is not list:
        raise CleanupSharedOutputError("locked B1 research cases are missing")
    matches = [row for row in research_cases if type(row) is dict and row.get("case_id") == request.case_id]
    if len(matches) != 1:
        raise CleanupSharedOutputError("locked B1 research case is missing or duplicated")
    case = matches[0]
    if case.get("technical_state") != "valid":
        raise CleanupSharedOutputError("locked B1 research case is not valid")
    case_sources = case.get("source_refs")
    if type(case_sources) is not dict:
        raise CleanupSharedOutputError("locked B1 research source refs are missing")
    for role in ("analysis_trace", "analysis_wav", "full_snapshot", "source_audio", "source_text"):
        reference = source_refs.get(role)
        expected = case_sources.get(role)
        if reference is None:
            if expected is not None:
                raise CleanupSharedOutputError(f"locked B1 research source ref differs: {role}")
            continue
        if type(expected) is not dict or reference.to_dict() != expected:
            raise CleanupSharedOutputError(f"locked B1 research source ref differs: {role}")

    expected_case_root = research_path.parent / "cases" / request.case_id
    expected_artifacts = {
        "baseline_plan": (case.get("plan_ref"), expected_case_root / "baseline-plan.json"),
        "baseline_vmd": (case.get("vmd_ref"), expected_case_root / "baseline.vmd"),
        "baseline_readback": (case.get("readback_ref"), expected_case_root / "readback.json"),
    }
    for role, (research_value, expected_path) in expected_artifacts.items():
        reference = source_refs.get(role)
        if (
            reference is None
            or type(research_value) is not dict
            or reference.to_dict() != research_value
            or Path(reference.path).resolve(strict=True) != expected_path.resolve(strict=True)
        ):
            raise CleanupSharedOutputError(f"locked B1 {role} does not match its accepted case/run")

    full_snapshot_ref = source_refs.get("full_snapshot")
    capture_ref = source_refs.get("capture_manifest")
    if full_snapshot_ref is None or capture_ref is None:
        raise CleanupSharedOutputError("locked B1 capture/full-snapshot refs are missing")
    expected_capture_path = Path(full_snapshot_ref.path).resolve(strict=True).parent / "capture-manifest.json"
    if Path(capture_ref.path).resolve(strict=True) != expected_capture_path.resolve(strict=True):
        raise CleanupSharedOutputError("locked B1 capture manifest belongs to a different source case")
    _capture_path, capture = read_ref("capture_manifest")
    if (
        capture.get("schema_id") != "ms31-capture-evidence/v1"
        or capture.get("case_id") != Path(full_snapshot_ref.path).resolve(strict=True).parent.name
        or capture.get("scenario_case_id") != capture.get("case_id")
        or capture.get("input_mode") != case.get("input_mode")
    ):
        raise CleanupSharedOutputError("locked B1 capture manifest differs from the accepted source case")

    optional = case.get("optional_artifacts")
    reference_result = optional.get("reference_vmd") if type(optional) is dict else None
    requested_reference = reference_result.get("requested_ref") if type(reference_result) is dict else None
    historical = source_refs.get("historical_reference_vmd")
    if requested_reference is None:
        if historical is not None:
            raise CleanupSharedOutputError("locked B1 historical VMD is not in the accepted research record")
    elif type(requested_reference) is not dict or historical is None or historical.to_dict() != requested_reference:
        raise CleanupSharedOutputError("locked B1 historical VMD differs from accepted research")

    plan_path = Path(source_refs["baseline_plan"].path).resolve(strict=True)
    try:
        plan = read_final_morph_transition_plan(plan_path.read_bytes())
    except (OSError, TransitionPlanError) as error:
        raise CleanupSharedOutputError("locked B1 baseline plan is invalid") from error
    if plan.state != "valid" or plan.issues:
        raise CleanupSharedOutputError("locked B1 baseline plan is not valid")
    _readback_path, readback = read_ref("baseline_readback")
    if (
        readback.get("schema_id") != "ms33-b1-readback/v1"
        or readback.get("status") != "passed"
        or readback.get("plan_digest") != plan.semantic_digest
        or readback.get("wire_digest") != plan.identity_context.closure_wire_digest
        or type(readback.get("projection_digest")) is not str
        or type(readback.get("verified_transition_count")) is not int
        or type(readback.get("measurements")) is not list
        or readback.get("verified_transition_count") != len(readback.get("measurements", ()))
    ):
        raise CleanupSharedOutputError("locked B1 readback does not match its baseline plan")

    lineage = plan.identity_context.source_lineage
    source_identity = case.get("source_identity")
    settings = case.get("settings")
    policy = settings.get("policy") if type(settings) is dict else None
    if type(source_identity) is not dict or type(policy) is not dict:
        raise CleanupSharedOutputError("locked B1 source identity or policy is missing")
    if any(
        source_identity.get(key) != historical_identity.get(key)
        for key in (
            "source_run_id", "analysis_generation", "base_plan_digest", "effective_plan_digest",
            "manual_revision", "resolved_profile_id", "output_mapping",
        )
    ):
        raise CleanupSharedOutputError("locked B1 historical snapshot differs from its accepted research case")
    audio_ref = source_refs.get("source_audio")
    wav_ref = source_refs.get("analysis_wav")
    text_ref = source_refs.get("source_text")
    capture_origin = capture.get("origin")
    capture_hashes = capture.get("input_hashes")
    capture_records = capture.get("artifact_records")
    capture_record_map = (
        {row.get("role"): row for row in capture_records if type(row) is dict}
        if type(capture_records) is list else {}
    )
    expected_capture_inputs = {
        "audio": None if audio_ref is None else audio_ref.sha256,
        "text": None if text_ref is None else text_ref.sha256,
    }
    if (
        type(capture_origin) is not dict
        or type(capture_hashes) is not dict
        or any(capture_hashes.get(key) != value for key, value in expected_capture_inputs.items())
        or capture_origin.get("source_run_id") != source_identity.get("source_run_id")
        or capture_origin.get("analysis_generation") != source_identity.get("analysis_generation")
        or capture_origin.get("audio_sha256") != expected_capture_inputs["audio"]
        or capture_origin.get("text_sha256") != expected_capture_inputs["text"]
        or capture.get("effective_plan_digest_before_after") != historical_identity.get("effective_plan_digest")
        or capture.get("resolved_profile_id") != historical_identity.get("resolved_profile_id")
        or type(capture_records) is not list
        or len(capture_record_map) != len(capture_records)
    ):
        raise CleanupSharedOutputError("locked B1 capture identity differs from its accepted source")
    for role, expected_ref in (
        ("full_snapshot", source_refs.get("full_snapshot")),
        ("analysis_trace", source_refs.get("analysis_trace")),
        ("saved_vmd", historical),
    ):
        record = capture_record_map.get(role)
        if expected_ref is None:
            if record is not None:
                raise CleanupSharedOutputError(f"locked B1 capture has an unreferenced {role}")
            continue
        if type(record) is not dict or type(record.get("path")) is not str:
            raise CleanupSharedOutputError(f"locked B1 capture lacks its {role} record")
        artifact_path = (Path(capture_ref.path).resolve(strict=True).parent / record["path"]).resolve(strict=True)
        actual = artifact_path.read_bytes()
        if (
            not artifact_path.is_relative_to(Path(capture_ref.path).resolve(strict=True).parent)
            or record.get("role") != role
            or record.get("sha256") != hashlib.sha256(actual).hexdigest()
            or record.get("bytes") != len(actual)
            or hashlib.sha256(actual).hexdigest() != expected_ref.sha256
            or len(actual) != expected_ref.bytes
        ):
            raise CleanupSharedOutputError(f"locked B1 capture {role} differs from its accepted ref")
    if (
        plan.identity_context.baseline_effective_digest != lineage.effective_plan_digest
        or lineage.source_kind != "replayed_capture"
        or lineage.origin_kind != "captured_snapshot"
        or lineage.run_id != source_identity.get("source_run_id")
        or lineage.origin_identity != f"{source_identity.get('source_run_id')}/{source_identity.get('analysis_generation')}"
        or lineage.analysis_generation != str(source_identity.get("analysis_generation"))
        or lineage.input_mode != case.get("input_mode")
        or lineage.original_source_sha256 != full_snapshot_ref.sha256
        or lineage.capture_manifest_sha256 != capture_ref.sha256
        or lineage.base_plan_digest != source_identity.get("base_plan_digest")
        or lineage.manual_revision != source_identity.get("manual_revision")
        or lineage.output_mapping != tuple(tuple(pair) for pair in source_identity.get("output_mapping", ()))
        or lineage.analysis_wav_sha256 != (None if wav_ref is None else wav_ref.sha256)
        or settings.get("analysis_wav_digest") != (None if wav_ref is None else wav_ref.sha256)
        or settings.get("source_audio_digest") != (None if audio_ref is None else audio_ref.sha256)
        or settings.get("source_text_digest") != (None if text_ref is None else text_ref.sha256)
        or lineage.current_runtime_sha256 != case.get("runtime_digest")
        or lineage.current_runtime_sha256 != research.get("runtime_digest")
        or lineage.policy_digest != policy.get("policy_digest")
        or policy.get("policy_id") != "ms32-cross-vowel-transition/evaluation-v2"
        or plan.identity_context.policy_digest != lineage.policy_digest
        or plan.identity_context.acoustic_digest != settings.get("acoustic_digest")
        or lineage.acoustic_evidence_digest != settings.get("acoustic_digest")
    ):
        raise CleanupSharedOutputError("locked B1 baseline lineage differs from its accepted source identity")
    return plan, lineage, case, capture


def _validate_source_snapshot(
    upstream: SharedFinalOutputContext,
    request: CleanupEvaluationRequest,
    source_snapshot: object,
) -> None:
    """Tie the worker's typed request to the exact UI snapshot that produced upstream."""
    identity = upstream.input_identity
    origin = getattr(source_snapshot, "origin", None)
    adjustment_snapshot = getattr(source_snapshot, "adjustment_snapshot", None)
    cleanup_request = getattr(source_snapshot, "cleanup_evaluation_request", None)
    if origin is None or adjustment_snapshot is None or cleanup_request != request:
        raise CleanupSharedOutputError("cleanup source snapshot is missing or differs from its request")

    def normalized(value: object) -> str | None:
        if value is None:
            return None
        if type(value) is not str or not value:
            raise CleanupSharedOutputError("cleanup source snapshot contains an invalid path")
        return os.path.normcase(os.path.abspath(os.path.normpath(value)))

    checks = (
        (identity.source_run_id, getattr(origin, "source_run_id", None)),
        (identity.job_id, getattr(origin, "job_id", None)),
        (identity.analysis_generation, getattr(origin, "analysis_generation", None)),
        (identity.manual_revision, getattr(source_snapshot, "manual_revision", None)),
        (identity.input_mode, getattr(source_snapshot, "input_mode", None)),
        (identity.input_binding_digest, getattr(origin, "input_binding_digest", None)),
        (identity.base_plan_digest, getattr(origin, "base_plan_digest", None)),
        (identity.adjustment_snapshot_digest, snapshot_digest(adjustment_snapshot)),
        (identity.resolved_profile_id, getattr(source_snapshot, "resolved_profile_id", None)),
        (identity.source_audio_path, normalized(getattr(source_snapshot, "source_audio_path", None))),
        (identity.analysis_wav_path, normalized(getattr(source_snapshot, "analysis_wav_path", None))),
        (identity.normalized_text_path, normalized(getattr(source_snapshot, "normalized_text_path", None))),
        (upstream.ticket, getattr(source_snapshot, "ticket", None)),
        (upstream.lifecycle_epoch, getattr(source_snapshot, "lifecycle_epoch", None)),
        (upstream.lifecycle_signature, getattr(source_snapshot, "lifecycle_signature", None)),
        (upstream.default_selection, getattr(source_snapshot, "default_transition_selection", None)),
    )
    if any(actual != expected for actual, expected in checks):
        raise CleanupSharedOutputError("cleanup source snapshot differs from the validated upstream context")

    effective_plan = getattr(source_snapshot, "effective_plan", None)
    if effective_plan is None:
        default_selection = upstream.default_selection
        selection_policy = getattr(
            getattr(getattr(default_selection, "binding", None), "policy", None),
            "policy_id",
            None,
        )
        if (
            getattr(default_selection, "selection_kind", None) == "transition"
            and selection_policy == TRANSITION_POLICY_V2
        ):
            # The bounded v2 route resolves its effective plan in the upstream
            # builder, so its first request has no pre-transition plan here.
            legacy_context = getattr(upstream.issuer_context, "legacy_context", None)
            effective_plan = getattr(
                legacy_context, "effective_plan_snapshot", None
            )
    expected_effective_digest = (
        None if effective_plan is None else effective_plan_snapshot_digest(effective_plan)
    )
    if identity.effective_plan_digest != expected_effective_digest:
        raise CleanupSharedOutputError("cleanup effective plan differs from its source snapshot")
    names = getattr(source_snapshot, "output_morph_names", None)
    if type(names) is not tuple or len(names) != len(SEMANTIC_VOWEL_ORDER):
        raise CleanupSharedOutputError("cleanup output mapping is missing from its source snapshot")
    expected_mapping = tuple(zip(SEMANTIC_VOWEL_ORDER, names))
    if identity.output_mapping != expected_mapping:
        raise CleanupSharedOutputError("cleanup output mapping differs from its source snapshot")
    contract = getattr(source_snapshot, "closure_contract", None)
    if getattr(contract, "digest", None) != identity.closure_contract_digest:
        raise CleanupSharedOutputError("cleanup closure contract differs from its source snapshot")
    transition_digest = (
        None if upstream.transition_binding is None
        else upstream.transition_binding.input_snapshot.input_digest
    )
    if identity.transition_input_digest != transition_digest:
        raise CleanupSharedOutputError("cleanup transition input differs from its source snapshot")
    application_digest = (
        None if upstream.default_selection is None
        else upstream.default_selection.selection_digest
    )
    if identity.application_binding_digest != application_digest:
        raise CleanupSharedOutputError("cleanup application selection differs from its source snapshot")

    source_refs = dict(request.case_source_refs)
    if source_refs:
        def strict_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise CleanupSharedOutputError("locked B1 snapshot contains a duplicate field")
                result[key] = value
            return result

        for role in ("analysis_trace", "full_snapshot"):
            try:
                verify_cleanup_artifact_content(source_refs[role])
            except (KeyError, ValueError) as error:
                raise CleanupSharedOutputError(f"locked B1 {role} reference is invalid") from error
        try:
            full_snapshot_payload = Path(source_refs["full_snapshot"].path).read_bytes()
            if (
                len(full_snapshot_payload) != source_refs["full_snapshot"].bytes
                or hashlib.sha256(full_snapshot_payload).hexdigest() != source_refs["full_snapshot"].sha256
            ):
                raise CleanupSharedOutputError("locked B1 full snapshot changed after verification")
            full_snapshot = json.loads(
                full_snapshot_payload.decode("utf-8"),
                object_pairs_hook=strict_pairs,
                parse_constant=lambda _value: (_ for _ in ()).throw(
                    CleanupSharedOutputError("locked B1 snapshot contains a non-finite number")
                ),
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CleanupSharedOutputError("locked B1 full snapshot cannot be read") from error
        if type(full_snapshot) is not dict or full_snapshot.get("schema_id") != "final-morph-snapshot/v1":
            raise CleanupSharedOutputError("locked B1 full snapshot schema is invalid")
        source_identity = full_snapshot.get("identity_context")
        if type(source_identity) is not dict:
            raise CleanupSharedOutputError("locked B1 full snapshot identity is missing")
        expected_identity_fields = {
            "source_run_id", "analysis_generation", "base_plan_digest", "effective_plan_digest",
            "manual_revision", "resolved_profile_id", "output_mapping", "numeric_policy_id",
            "curve_policy_id", "silence_policy_id", "crossfade_policy_id",
        }
        if set(source_identity) != expected_identity_fields:
            raise CleanupSharedOutputError("locked B1 full snapshot identity fields are invalid")
        locked_identity = identity
        transition_binding = upstream.transition_binding
        default_selection = upstream.default_selection
        selection_policy_id = getattr(
            getattr(getattr(default_selection, "binding", None), "policy", None),
            "policy_id",
            None,
        )
        if (
            transition_binding is not None
            and getattr(default_selection, "selection_kind", None) == "transition"
            and selection_policy_id == TRANSITION_POLICY_V2
        ):
            # Compare B1 provenance to the pre-transition source captured by the
            # validated bounded issuer. B1 records the source plan with zero
            # conflicts deferred, so its accepted digest must be rebuilt using
            # the same preparation mode.
            preparation = getattr(transition_binding.issuer_context, "preparation", None)
            locked_identity = getattr(preparation, "source_identity", None)
            if locked_identity is None:
                raise CleanupSharedOutputError(
                    "bounded transition source identity is unavailable"
                )
            source_plan = _build_effective_shape_plan(
                preparation.base_input,
                preparation.adjustment_snapshot,
                _defer_zero_conflicts=True,
            )
            locked_identity = replace(
                locked_identity,
                effective_plan_digest=effective_plan_snapshot_digest(source_plan),
                silence_policy_id=source_plan.silence_policy,
            )
        current_mapping = [
            [semantic, name] for semantic, name in locked_identity.output_mapping
        ]
        source_identity_match = (
            locked_identity.source_run_id == source_identity["source_run_id"]
            and locked_identity.analysis_generation == source_identity["analysis_generation"]
            and locked_identity.base_plan_digest == source_identity["base_plan_digest"]
            and locked_identity.manual_revision == source_identity["manual_revision"]
            and current_mapping == source_identity["output_mapping"]
        )
        if not source_identity_match:
            raise CleanupSharedOutputError(
                "current MS32 source lineage differs from the locked B1 full snapshot identity"
            )
        baseline_plan, baseline_lineage, baseline_case, _capture = _read_locked_b1_bundle(
            request, source_refs, source_identity,
        )
        transition_input_snapshot = (
            None if upstream.transition_binding is None
            else upstream.transition_binding.input_snapshot
        )
        expected_policy_digest = getattr(
            getattr(transition_input_snapshot, "policy", None), "policy_digest", None,
        )
        expected_acoustic_digest = getattr(
            getattr(transition_input_snapshot, "acoustic", None), "content_digest", None,
        )
        source_profile_id = getattr(source_snapshot, "resolved_profile_id", None)
        if (
            baseline_case.get("input_mode") != getattr(source_snapshot, "input_mode", None)
            or baseline_lineage.effective_plan_digest != locked_identity.effective_plan_digest
            or baseline_lineage.run_id != locked_identity.source_run_id
            or baseline_lineage.analysis_generation != str(locked_identity.analysis_generation)
            or baseline_lineage.base_plan_digest != locked_identity.base_plan_digest
            or baseline_lineage.manual_revision != locked_identity.manual_revision
            or tuple(tuple(pair) for pair in baseline_lineage.output_mapping) != tuple(locked_identity.output_mapping)
            or baseline_lineage.resolved_profile_id != source_profile_id
            or (expected_policy_digest is not None and baseline_lineage.policy_digest != expected_policy_digest)
            or (expected_acoustic_digest is not None and baseline_plan.identity_context.acoustic_digest != expected_acoustic_digest)
        ):
            raise CleanupSharedOutputError(
                "pre-transition effective plan differs from the accepted B1 baseline lineage"
            )
        for role, field_name in (
            ("source_audio", "source_audio_path"),
            ("analysis_wav", "analysis_wav_path"),
            ("source_text", "normalized_text_path"),
        ):
            reference = source_refs.get(role)
            current_path = getattr(source_snapshot, field_name, None)
            if reference is None:
                if current_path is not None:
                    raise CleanupSharedOutputError(f"cleanup source snapshot has an unlocked {role}")
                continue
            try:
                verify_cleanup_artifact_content(reference)
            except ValueError as error:
                raise CleanupSharedOutputError(f"locked B1 {role} reference is invalid") from error
            if current_path is None:
                raise CleanupSharedOutputError(f"cleanup source {role} is missing from the current snapshot")
            try:
                current_file = Path(current_path).resolve(strict=True)
                before = current_file.stat()
                payload = current_file.read_bytes()
                after = current_file.stat()
            except OSError as error:
                raise CleanupSharedOutputError(f"cleanup source {role} cannot be read") from error
            if (
                getattr(before, "st_mtime_ns", None) != getattr(after, "st_mtime_ns", None)
                or before.st_size != after.st_size
                or len(payload) != reference.bytes
                or after.st_size != reference.bytes
                or hashlib.sha256(payload).hexdigest() != reference.sha256
            ):
                raise CleanupSharedOutputError(f"cleanup source {role} differs from its B1 lock")


def _event_source_map(context: SharedFinalOutputContext) -> dict[str, tuple[int, ...]]:
    result: dict[str, tuple[int, ...]] = {}
    evidence = getattr(context.issuer_context.legacy_context, "issuer_evidence", None)
    for shape in tuple(getattr(evidence, "shapes", ())):
        indices = tuple(getattr(shape, "base_event_indices", ()))
        ordinal = getattr(shape, "shape_ordinal", None)
        for point in tuple(getattr(shape, "points", ())):
            point_ordinal = getattr(point, "point_ordinal", None)
            if ordinal is None or point_ordinal is None:
                continue
            result[f"source:shape:{ordinal}:point:{point_ordinal}"] = indices
        if ordinal is not None:
            result[f"source:shape:{ordinal}"] = indices
    for event in context.source_events:
        result[f"source:event:{event.base_event_index}"] = (event.base_event_index,)
    return result


def _point_source_indices(source_ids: tuple[str, ...], source_map: dict[str, tuple[int, ...]]) -> tuple[int, ...]:
    values: set[int] = set()
    for source_id in source_ids:
        values.update(source_map.get(source_id, ()))
        match = _EVENT_SOURCE_RE.fullmatch(source_id)
        if match is not None:
            values.add(int(match.group(1)))
    return tuple(sorted(values))


def _shape_ordinal(record_id: str) -> int | None:
    match = _SHAPE_ORDINAL_RE.search(record_id)
    return None if match is None else int(match.group(1))


def _closure_plan(upstream: SharedFinalOutputContext) -> ClosurePlan:
    plan = upstream.candidate.plan
    if not isinstance(plan, ClosurePlan) or plan.state != "valid":
        raise CleanupSharedOutputError("verified MS32 closure plan is unavailable")
    return plan


def _closure_requirement_rows(plan: ClosurePlan) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "requirement_id": item.requirement_id,
            "kind": item.kind,
            "semantic_morph": item.semantic_morph,
            "start_frame": item.start_frame,
            "end_frame": item.end_frame,
            "endpoint_policy": item.endpoint_policy,
            "source_ids": list(item.source_ids),
            "reason": item.reason,
        }
        for item in plan.requirements
    )


def _source_binding(upstream: SharedFinalOutputContext, request: CleanupEvaluationRequest) -> dict[str, object]:
    identity = upstream.input_identity
    return {
        "schema_id": "ms33-b4-source-binding/v1",
        "case_id": request.case_id,
        "source_run_id": identity.source_run_id,
        "analysis_generation": identity.analysis_generation,
        "manual_revision": identity.manual_revision,
        "input_mode": identity.input_mode,
        "input_binding_digest": identity.input_binding_digest,
        "base_plan_digest": identity.base_plan_digest,
        "adjustment_snapshot_digest": identity.adjustment_snapshot_digest,
        "effective_plan_digest": identity.effective_plan_digest,
        "resolved_profile_id": identity.resolved_profile_id,
        "output_mapping": [[semantic, name] for semantic, name in identity.output_mapping],
        "numeric_policy_id": identity.numeric_policy_id,
        "curve_policy_id": identity.curve_policy_id,
        "silence_policy_id": identity.silence_policy_id,
        "crossfade_policy_id": identity.crossfade_policy_id,
        "closure_contract_digest": identity.closure_contract_digest,
        "baseline_digest": identity.baseline_digest,
        "transition_input_digest": identity.transition_input_digest,
        "application_binding_digest": identity.application_binding_digest,
        "upstream_binding_digest": upstream.identity.binding_digest,
    }


def _event_input(upstream: SharedFinalOutputContext, request: CleanupEvaluationRequest) -> EventCleanupInput:
    plan = _closure_plan(upstream)
    source_map = _event_source_map(upstream)
    mapping = dict(plan.identity_context.output_mapping)
    points: list[CleanupPoint] = []
    for point in plan.points:
        points.append(CleanupPoint(
            frame_no=point.frame_no,
            semantic_morph=point.semantic_morph,
            canonical_value=point.value.scalar,
            binary32_hex=point.value.binary32_hex,
            wire_value=struct.unpack("<f", point.value.binary32_bytes)[0],
            source_ids=point.source_ids,
            source_event_indices=_point_source_indices(point.source_ids, source_map),
            point_kinds=point.point_kinds,
            intent_origins=(point.origin,),
            requirement_ids=point.requirement_ids,
            shape_ordinal=_shape_ordinal(point.record_id),
        ))
    event_rows: list[dict[str, object]] = []
    for event in upstream.source_events:
        event_rows.append({
            "record_id": f"{request.case_id}:event:{event.base_event_index}",
            "record_kind": "event",
            "case_id": request.case_id,
            "source_event_indices": [event.base_event_index],
            "semantic_morph": event.vowel,
            "frame_no": event.peak_frame,
            "values": {},
            "timing": {
                "start_frame": event.start_frame,
                "peak_frame": event.peak_frame,
                "end_frame": event.end_frame,
            },
            "acoustic": {"coverage_status": "unavailable"},
            "protection_reasons": [],
            "uncertainty_reasons": ["live_metric_evidence_not_captured"],
        })
    controls: list[dict[str, object]] = []
    for point in plan.points:
        indices = _point_source_indices(point.source_ids, source_map)
        controls.append({
            "record_id": point.record_id,
            "record_kind": "control_point",
            "case_id": request.case_id,
            "source_event_indices": list(indices),
            "shape_ordinal": _shape_ordinal(point.record_id),
            "semantic_morph": point.semantic_morph,
            "frame_no": point.frame_no,
            "point_kinds": list(point.point_kinds),
            "intent_origins": [point.origin],
            "values": {
                "canonical": {"binary32_hex": point.value.binary32_hex},
            },
            "protection_reasons": ["non_automatic_origin"] if point.origin != "automatic" else [],
            "uncertainty_reasons": [],
        })
    original_plan: dict[str, object]
    if upstream.transition_binding is not None:
        original_plan = upstream.transition_binding.plan.to_dict()
    else:
        original_plan = {
            "schema_id": "ms32-baseline-upstream/v1",
            "state": "valid",
            "closure_plan": plan.to_dict(),
        }
    return EventCleanupInput(
        case_id=request.case_id,
        source_binding=_source_binding(upstream, request),
        original_transition_plan=original_plan,
        original_requirements=_closure_requirement_rows(plan),
        original_points=tuple(points),
        event_rows=tuple(event_rows),
        control_rows=tuple(controls),
        policy=request.event_policy,
        enabled=True,
    )


def _reduction_points_from_cleanup(
    upstream: SharedFinalOutputContext,
    request: CleanupEvaluationRequest | None,
    event_plan: FinalMorphCleanupPlan | None,
) -> tuple[ReductionPoint, ...]:
    closure = _closure_plan(upstream)
    mapping = dict(closure.identity_context.output_mapping)
    if event_plan is None:
        rows = tuple((point.frame_no, point.semantic_morph, point.value, point.source_ids,
                      point.requirement_ids, point.origin, point.point_kinds, point.record_id)
                     for point in closure.points)
    else:
        rows = tuple((point.frame_no, point.semantic_morph,
                      _ZERO_VALUE if point.canonical_value == 0.0 else next(
                          source.value for source in closure.points
                          if source.frame_no == point.frame_no and source.semantic_morph == point.semantic_morph
                      ),
                      point.source_ids, point.requirement_ids,
                      point.intent_origins[0] if point.intent_origins else "unknown",
                      point.point_kinds,
                      next(source.record_id for source in closure.points
                           if source.frame_no == point.frame_no and source.semantic_morph == point.semantic_morph))
                     for point in event_plan.points)
    source_map = _event_source_map(upstream)
    return tuple(
        ReductionPoint(
            frame_no=frame,
            semantic_morph=morph,
            output_morph_name=mapping[morph],
            canonical_value=value,
            source_ids=tuple(source_ids),
            source_record_ids=(record_id,),
            source_event_indices=_point_source_indices(tuple(source_ids), source_map),
            point_kinds=tuple(point_kinds),
            intent_origins=(origin,),
            requirement_ids=tuple(requirements),
            shape_ordinal=_shape_ordinal(record_id),
        )
        for frame, morph, value, source_ids, requirements, origin, point_kinds, record_id in rows
    )


def _key_protection_binding(
    request: CleanupEvaluationRequest,
    points: tuple[ReductionPoint, ...],
    requirements: tuple[dict[str, object], ...],
) -> dict[str, object]:
    point_by_id = {record_id: point for point in points for record_id in point.source_record_ids}
    protected: dict[tuple[int, str], set[str]] = {}
    for row in request.key_policy.protections:
        record_ids = row.get("record_ids", [])
        kind = row.get("kind", "contract_protection")
        if type(record_ids) is not list or type(kind) is not str:
            raise CleanupSharedOutputError("B1 key protection contract is malformed")
        for record_id in record_ids:
            if type(record_id) is not str or not record_id.startswith(f"{request.case_id}:"):
                continue
            point = point_by_id.get(record_id)
            if point is not None:
                protected.setdefault(point.key, set()).add(f"b1_contract:{kind}")
                continue
            shape_match = _B1_SHAPE_RECORD_RE.search(record_id)
            final_match = _B1_FINAL_RECORD_RE.search(record_id)
            event_match = _B1_EVENT_RECORD_RE.search(record_id)
            matched: tuple[ReductionPoint, ...] = ()
            if shape_match is not None:
                source_id = f"source:shape:{shape_match.group(1)}:point:{shape_match.group(2)}"
                matched = tuple(candidate for candidate in points if source_id in candidate.source_ids)
            elif final_match is not None:
                start, end, morph = int(final_match.group(1)), int(final_match.group(2)), final_match.group(3)
                if start > end:
                    raise CleanupSharedOutputError("B1 final-key protection interval is reversed")
                matched = tuple(
                    candidate for candidate in points
                    if candidate.semantic_morph == morph and start <= candidate.frame_no <= end
                )
            elif event_match is not None:
                event_index = int(event_match.group(1))
                matched = tuple(
                    candidate for candidate in points
                    if event_index in candidate.source_event_indices
                )
            if not matched:
                raise CleanupSharedOutputError(
                    f"B1 protection record does not map to current source: {record_id}"
                )
            for candidate in matched:
                protected.setdefault(candidate.key, set()).add(f"b1_contract:{kind}")
    protected_rows = [
        {
            "frame_no": point.frame_no,
            "semantic_morph": point.semantic_morph,
            "source_record_ids": list(point.source_record_ids),
            "reasons": sorted(protected[point.key]),
        }
        for point in points if point.key in protected
    ]
    required_zero_intervals = [
        {
            "semantic_morph": row["semantic_morph"],
            "start_frame": row["start_frame"],
            "end_frame": row["end_frame"],
            "reason": f"upstream:{row.get('requirement_id', row.get('kind', 'requirement'))}",
        }
        for row in requirements
        if row.get("kind") in {"per_morph_closure", "silence_core"}
    ]
    return {
        "schema_id": "ms33-b3-protection-binding/v1",
        "protected_keys": protected_rows,
        "required_zero_intervals": required_zero_intervals,
    }


def _reduction_input(
    upstream: SharedFinalOutputContext,
    request: CleanupEvaluationRequest,
    event_plan: FinalMorphCleanupPlan | None,
) -> KeyReductionInput:
    points = _reduction_points_from_cleanup(upstream, request, event_plan)
    closure = _closure_plan(upstream)
    requirements = _closure_requirement_rows(closure)
    if event_plan is not None:
        upstream_plan: dict[str, object] = {
            "schema_id": "ms33-b2-event-cleanup-upstream/v1",
            "plan": event_plan.to_dict(),
        }
    else:
        upstream_plan = {
            "schema_id": "ms32-baseline-upstream/v1",
            "plan": closure.to_dict(),
        }
    source = _source_binding(upstream, request)
    source["b2_plan_digest"] = None if event_plan is None else event_plan.semantic_digest
    source["b2_input_digest"] = None if event_plan is None else event_plan.identity["input_digest"]
    return KeyReductionInput.create(
        input_kind="ms32_baseline" if event_plan is None else "event_cleanup",
        source_binding=source,
        upstream_plan=upstream_plan,
        upstream_requirements=requirements,
        points=points,
        protection_binding=_key_protection_binding(request, points, requirements),
        policy=request.key_policy,
        enabled=True,
    )


def _reduction_projection(plan: FinalMorphKeyReductionPlan, issuer: KeyReductionInput) -> ClosureProjection:
    projected = project_validated_key_reduction_plan(plan, issuer)
    by_key = {(point.frame_no, point.semantic_morph): point for point in plan.points}
    semantic_points: list[tuple[int, str, float]] = []
    wire_points: list[ClosureWirePoint] = []
    deltas: list[tuple[int, str, float]] = []
    for wire in projected.wire_points:
        point = by_key[(wire.frame_no, wire.semantic_morph)]
        scalar = point.canonical_value.scalar
        semantic_points.append((wire.frame_no, wire.semantic_morph, scalar))
        wire_points.append(wire)
        if wire.binary32_value != scalar:
            deltas.append((wire.frame_no, wire.semantic_morph, wire.binary32_value - scalar))
    return ClosureProjection(tuple(semantic_points), tuple(wire_points), projected.wire_digest, tuple(deltas))


def _final_points(
    plan: object,
    source_map: dict[str, tuple[int, ...]],
) -> tuple[CleanupPointView, ...]:
    if isinstance(plan, ClosurePlan):
        rows = (
            (point.frame_no, point.semantic_morph, point.value.scalar, point.value.binary32_hex,
             point.source_ids, point.point_kinds, (point.origin,), point.requirement_ids)
            for point in plan.points
        )
    elif isinstance(plan, FinalMorphCleanupPlan):
        rows = (
            (point.frame_no, point.semantic_morph, point.canonical_value, point.binary32_hex,
             point.source_ids, point.point_kinds, point.intent_origins, point.requirement_ids)
            for point in plan.points
        )
    elif isinstance(plan, FinalMorphKeyReductionPlan):
        rows = (
            (point.frame_no, point.semantic_morph, point.canonical_value.scalar,
             point.canonical_value.binary32_hex, point.source_ids, point.point_kinds,
             point.intent_origins, point.requirement_ids)
            for point in plan.points
        )
    else:
        raise CleanupSharedOutputError("final plan type is unsupported")
    result = tuple(
        CleanupPointView(
            frame_no=frame,
            semantic_morph=morph,
            canonical_value=canonical,
            binary32_hex=binary32,
            source_ids=tuple(source_ids),
            source_event_indices=_point_source_indices(tuple(source_ids), source_map),
            point_kinds=tuple(point_kinds),
            intent_origins=tuple(origins),
            requirement_ids=tuple(requirements),
        )
        for frame, morph, canonical, binary32, source_ids, point_kinds, origins, requirements in rows
    )
    keys = [(item.frame_no, SEMANTIC_VOWEL_ORDER.index(item.semantic_morph)) for item in result]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise CleanupSharedOutputError("final point view is unordered or duplicated")
    return result


def _summary(
    *, request: CleanupEvaluationRequest | None,
    default_selection: DefaultCleanupSelection | None,
    final_identity: FinalOutputIdentity,
    event_issuer: EventCleanupInput | None, event_plan: FinalMorphCleanupPlan | None,
    reduction_issuer: KeyReductionInput | None, reduction_plan: FinalMorphKeyReductionPlan | None,
    final_points: tuple[CleanupPointView, ...], source_event_count: int,
) -> CleanupSharedSummary:
    if (request is None) == (default_selection is None):
        raise CleanupSharedOutputError("cleanup summary needs exactly one selection source")
    if request is not None:
        policy_digests = (request.event_policy.policy_digest, request.key_policy.policy_digest)
        variant = request.variant
        application_origin = "evaluation"
        event_state = "evaluated"
        key_state = "evaluated"
    else:
        key_applied = default_selection.selection_kind == "cleanup"
        policy_digests = (
            _digest({"schema_id": "ms33-event-component/v1", "state": "not_applicable"}),
            default_selection.binding.key_policy.policy_digest
            if key_applied
            else _digest({
                "schema_id": "ms33-key-component/v1",
                "state": default_selection.key_state,
            }),
        )
        variant = "keys_only" if key_applied else "baseline"
        application_origin = "adopted_default"
        event_state = "not_applicable"
        key_state = "applied" if key_applied else default_selection.key_state
        selection_kind = default_selection.selection_kind
        selection_reason = default_selection.reason
    if request is not None:
        selection_kind = "evaluation"
        selection_reason = "explicit_evaluation_request"
    decisions = () if event_plan is None else tuple(
        (item.event_id, item.action, item.reasons) for item in event_plan.decisions
    )
    suppressions = () if event_plan is None else tuple(
        item.event_id for item in event_plan.decisions if item.action == "suppress_event"
    )
    removals = () if reduction_plan is None else tuple(
        item.point.key for item in reduction_plan.removals
    )
    protected_reasons = () if reduction_plan is None else tuple(
        tuple(str(value) for value in row.get("reasons", ()))
        for row in reduction_issuer.protection_binding.get("protected_keys", ())
        if type(row) is dict
    )
    payload = {
        "schema_id": "cleanup-shared-summary/v1",
        "final_binding": final_identity.binding_digest,
        "variant": variant,
        "policy_digests": list(policy_digests),
        "source_event_count": source_event_count,
        "suppressed_event_ids": list(suppressions),
        "input_key_count": len(event_issuer.original_points) if event_issuer is not None else (
            len(reduction_issuer.points) if reduction_issuer is not None else len(final_points)
        ),
        "final_key_count": len(final_points),
        "removed_keys": [[frame, morph] for frame, morph in removals],
        "event_reasons": [
            {"event_id": event_id, "action": action, "reasons": list(reasons)}
            for event_id, action, reasons in decisions
        ],
        "protected_reasons": [list(rows) for rows in protected_reasons],
    }
    if application_origin == "adopted_default":
        payload.update({
            "application_origin": application_origin,
            "event_component_state": event_state,
            "key_component_state": key_state,
            "selection_kind": selection_kind,
            "selection_reason": selection_reason,
        })
    return CleanupSharedSummary(
        schema_id="cleanup-shared-summary/v1",
        final_binding=final_identity.binding_digest,
        variant=variant,
        policy_digests=policy_digests,
        source_event_count=source_event_count,
        suppressed_event_ids=suppressions,
        input_key_count=int(payload["input_key_count"]),
        final_key_count=len(final_points),
        removed_keys=removals,
        event_reasons=decisions,
        protected_reasons=protected_reasons,
        summary_digest=_digest(payload),
        application_origin=application_origin,
        event_component_state=event_state,
        key_component_state=key_state,
        selection_kind=selection_kind,
        selection_reason=selection_reason,
    )


def build_cleanup_shared_output(
    upstream: SharedFinalOutputContext,
    request: CleanupEvaluationRequest,
    source_snapshot: object | None = None,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> SharedFinalOutputContext:
    """Apply the explicitly selected B2/B3 variant to one already-validated MS32 context."""
    if not isinstance(upstream, SharedFinalOutputContext) or not isinstance(request, CleanupEvaluationRequest):
        raise CleanupSharedOutputError("upstream context and typed cleanup request are required")
    if upstream.cleanup_binding is not None:
        raise CleanupSharedOutputError("cleanup cannot be recursively applied")
    if source_snapshot is not None:
        _validate_source_snapshot(upstream, request, source_snapshot)
    _check_cancelled(cancelled)
    input_digest = _input_digest(upstream, request)
    event_issuer: EventCleanupInput | None = None
    event_plan: FinalMorphCleanupPlan | None = None
    reduction_issuer: KeyReductionInput | None = None
    reduction_plan: FinalMorphKeyReductionPlan | None = None
    final_plan: object = _closure_plan(upstream)
    final_kind = "upstream"
    final_projection = upstream.projection

    if request.variant in {"events_only", "events_and_keys"}:
        event_issuer = _event_input(upstream, request)
        resolution = resolve_event_cleanup(event_issuer)
        event_plan = build_event_cleanup_candidate(event_issuer, resolution)
        validation = validate_event_cleanup_plan(event_plan, event_issuer)
        if validation.state != "valid" or validation.issues:
            raise CleanupSharedOutputError("B2 event cleanup plan failed independent validation")
        final_projection = project_validated_cleanup_plan(event_plan, event_issuer).closure_projection
        final_plan = event_plan
        final_kind = "event_cleanup"
        _check_cancelled(cancelled)

    if request.variant in {"keys_only", "events_and_keys"}:
        reduction_issuer = _reduction_input(upstream, request, event_plan)
        reduction_resolution = resolve_redundant_keys(reduction_issuer)
        reduction_plan = build_key_reduction_candidate(reduction_issuer, reduction_resolution)
        validation = validate_key_reduction_plan(reduction_plan, reduction_issuer)
        if validation.state != "valid" or validation.issues:
            raise CleanupSharedOutputError("B3 key reduction plan failed independent validation")
        final_projection = _reduction_projection(reduction_plan, reduction_issuer)
        final_plan = reduction_plan
        final_kind = "key_reduction"
        _check_cancelled(cancelled)

    if request.variant == "baseline":
        final_plan = (
            upstream.transition_binding.plan
            if upstream.transition_binding is not None
            else _closure_plan(upstream)
        )
        final_kind = "upstream"
        final_projection = upstream.projection

    final_input_identity = replace(
        upstream.input_identity,
        cleanup_input_digest=input_digest,
    )
    final_plan_row = final_plan.to_dict()
    final_identity = FinalOutputIdentity(
        input_identity=final_input_identity,
        plan_schema_id=final_plan_row["schema_id"],
        curve_policy_id=upstream.identity.curve_policy_id,
        semantic_digest=final_plan_row["semantic_digest"],
        wire_digest=final_projection.wire_digest,
    )
    final_points = _final_points(final_plan if isinstance(final_plan, ClosurePlan) else (
        _closure_plan(upstream) if final_kind == "upstream" else final_plan
    ), _event_source_map(upstream))
    summary = _summary(
        request=request,
        default_selection=None,
        final_identity=final_identity,
        event_issuer=event_issuer,
        event_plan=event_plan,
        reduction_issuer=reduction_issuer,
        reduction_plan=reduction_plan,
        final_points=final_points,
        source_event_count=len(upstream.source_events),
    )
    binding = CleanupSharedOutputBinding(
        request=request,
        default_selection=None,
        input_digest=input_digest,
        upstream_context=upstream,
        event_issuer=event_issuer,
        event_plan=event_plan,
        reduction_issuer=reduction_issuer,
        reduction_plan=reduction_plan,
        final_plan=final_plan,
        final_plan_kind=final_kind,
        final_projection=final_projection,
        final_points=final_points,
        summary=summary,
    )
    context = SharedFinalOutputContext(
        input_identity=final_input_identity,
        identity=final_identity,
        issuer_context=upstream.issuer_context,
        candidate=upstream.candidate,
        projection=final_projection,
        source_events=upstream.source_events,
        restriction_event_targets=upstream.restriction_event_targets,
        ticket=upstream.ticket,
        lifecycle_epoch=upstream.lifecycle_epoch,
        lifecycle_signature=upstream.lifecycle_signature,
        transition_binding=upstream.transition_binding,
        default_selection=upstream.default_selection,
        cleanup_binding=binding,
    )
    validate_cleanup_shared_binding(binding)
    return context


def _default_cleanup_source_binding(
    upstream: SharedFinalOutputContext,
    selection: DefaultCleanupSelection,
) -> dict[str, object]:
    identity = upstream.input_identity
    return {
        "schema_id": "ms33-b5-live-source-binding/v1",
        "source_run_id": identity.source_run_id,
        "job_id": identity.job_id,
        "analysis_generation": identity.analysis_generation,
        "manual_revision": identity.manual_revision,
        "input_mode": identity.input_mode,
        "input_binding_digest": identity.input_binding_digest,
        "base_plan_digest": identity.base_plan_digest,
        "adjustment_snapshot_digest": identity.adjustment_snapshot_digest,
        "effective_plan_digest": identity.effective_plan_digest,
        "profile_id": identity.resolved_profile_id,
        "output_mapping": [[semantic, name] for semantic, name in identity.output_mapping],
        "numeric_policy_id": identity.numeric_policy_id,
        "curve_policy_id": identity.curve_policy_id,
        "silence_policy_id": identity.silence_policy_id,
        "crossfade_policy_id": identity.crossfade_policy_id,
        "closure_contract_digest": identity.closure_contract_digest,
        "baseline_digest": identity.baseline_digest,
        "transition_input_digest": identity.transition_input_digest,
        "application_binding_digest": identity.application_binding_digest,
        "upstream_binding_digest": upstream.identity.binding_digest,
        "default_selection_digest": selection.selection_digest,
    }


def _validate_default_cleanup_source(
    upstream: SharedFinalOutputContext,
    selection: DefaultCleanupSelection,
    source_snapshot: object | None,
) -> None:
    identity = upstream.input_identity
    if (
        selection.input_mode != identity.input_mode
        or selection.profile_id != identity.resolved_profile_id
        or selection.output_mapping != identity.output_mapping
    ):
        raise CleanupSharedOutputError("default cleanup selection differs from current input identity")
    if source_snapshot is None:
        return
    if (
        getattr(source_snapshot, "default_cleanup_selection", None) != selection
        or getattr(source_snapshot, "input_mode", None) != identity.input_mode
        or getattr(source_snapshot, "resolved_profile_id", None) != identity.resolved_profile_id
        or tuple(zip(SEMANTIC_VOWEL_ORDER, getattr(source_snapshot, "output_morph_names", ())))
        != identity.output_mapping
        or getattr(source_snapshot, "default_transition_selection", None) != upstream.default_selection
        or getattr(source_snapshot, "ticket", None) != upstream.ticket
        or getattr(source_snapshot, "lifecycle_epoch", None) != upstream.lifecycle_epoch
        or getattr(source_snapshot, "lifecycle_signature", None) != upstream.lifecycle_signature
    ):
        raise CleanupSharedOutputError("default cleanup source snapshot differs from current input")


def build_default_cleanup_shared_output(
    upstream: SharedFinalOutputContext,
    selection: DefaultCleanupSelection,
    source_snapshot: object | None = None,
    *,
    cancelled: Callable[[], bool] | None = None,
) -> SharedFinalOutputContext:
    """Apply only the adopted exact-key reduction to a fresh MS32 context."""
    if not isinstance(upstream, SharedFinalOutputContext):
        raise CleanupSharedOutputError("upstream context is invalid")
    if not isinstance(selection, DefaultCleanupSelection):
        raise CleanupSharedOutputError("default cleanup selection is invalid")
    if upstream.cleanup_binding is not None or upstream.input_identity.cleanup_input_digest is not None:
        raise CleanupSharedOutputError("cleanup cannot be recursively applied")
    _validate_default_cleanup_source(upstream, selection, source_snapshot)
    _check_cancelled(cancelled)

    closure = _closure_plan(upstream)
    if selection.selection_kind in {"scope_excluded", "no_applicable"}:
        final_plan: object = (
            upstream.transition_binding.plan
            if upstream.transition_binding is not None
            else closure
        )
        final_projection = upstream.projection
        final_kind = "upstream"
        final_input_identity = replace(
            upstream.input_identity,
            cleanup_input_digest=_input_digest(upstream, None, selection),
            cleanup_application_binding_digest=selection.selection_digest,
        )
        final_plan_row = final_plan.to_dict()
        final_identity = FinalOutputIdentity(
            input_identity=final_input_identity,
            plan_schema_id=final_plan_row["schema_id"],
            curve_policy_id=upstream.identity.curve_policy_id,
            semantic_digest=final_plan_row["semantic_digest"],
            wire_digest=final_projection.wire_digest,
        )
        final_points = _final_points(closure, _event_source_map(upstream))
        summary = _summary(
            request=None,
            default_selection=selection,
            final_identity=final_identity,
            event_issuer=None,
            event_plan=None,
            reduction_issuer=None,
            reduction_plan=None,
            final_points=final_points,
            source_event_count=len(upstream.source_events),
        )
        binding = CleanupSharedOutputBinding(
            request=None,
            default_selection=selection,
            input_digest=_input_digest(upstream, None, selection),
            upstream_context=upstream,
            event_issuer=None,
            event_plan=None,
            reduction_issuer=None,
            reduction_plan=None,
            final_plan=final_plan,
            final_plan_kind=final_kind,
            final_projection=final_projection,
            final_points=final_points,
            summary=summary,
        )
        context = SharedFinalOutputContext(
            input_identity=final_input_identity,
            identity=final_identity,
            issuer_context=upstream.issuer_context,
            candidate=upstream.candidate,
            projection=final_projection,
            source_events=upstream.source_events,
            restriction_event_targets=upstream.restriction_event_targets,
            ticket=upstream.ticket,
            lifecycle_epoch=upstream.lifecycle_epoch,
            lifecycle_signature=upstream.lifecycle_signature,
            transition_binding=upstream.transition_binding,
            default_selection=upstream.default_selection,
            cleanup_binding=binding,
        )
        validate_cleanup_shared_binding(binding)
        return context
    if selection.selection_kind != "cleanup":
        raise CleanupSharedOutputError("default cleanup selection kind is unsupported")

    points = _reduction_points_from_cleanup(upstream, None, None)
    requirements = _closure_requirement_rows(closure)
    try:
        protection_binding = resolve_current_key_protections(points, requirements)
        reduction_issuer = KeyReductionInput.create(
            input_kind="ms32_baseline",
            source_binding=_default_cleanup_source_binding(upstream, selection),
            upstream_plan={
                "schema_id": "ms32-baseline-upstream/v1",
                "plan": closure.to_dict(),
            },
            upstream_requirements=requirements,
            points=points,
            protection_binding=protection_binding,
            policy=selection.binding.key_policy,
            enabled=True,
        )
    except (TypeError, ValueError) as error:
        raise CleanupSharedOutputError("current cleanup source or protections are invalid") from error
    reduction_resolution = resolve_redundant_keys(reduction_issuer)
    reduction_plan = build_key_reduction_candidate(reduction_issuer, reduction_resolution)
    validation = validate_key_reduction_plan(reduction_plan, reduction_issuer)
    if validation.state != "valid" or validation.issues:
        raise CleanupSharedOutputError("default exact-key reduction failed independent validation")
    _check_cancelled(cancelled)

    final_projection = _reduction_projection(reduction_plan, reduction_issuer)
    final_input_identity = replace(
        upstream.input_identity,
        cleanup_input_digest=_input_digest(upstream, None, selection),
        cleanup_application_binding_digest=selection.selection_digest,
    )
    final_plan_row = reduction_plan.to_dict()
    final_identity = FinalOutputIdentity(
        input_identity=final_input_identity,
        plan_schema_id=final_plan_row["schema_id"],
        curve_policy_id=upstream.identity.curve_policy_id,
        semantic_digest=final_plan_row["semantic_digest"],
        wire_digest=final_projection.wire_digest,
    )
    final_points = _final_points(reduction_plan, _event_source_map(upstream))
    summary = _summary(
        request=None,
        default_selection=selection,
        final_identity=final_identity,
        event_issuer=None,
        event_plan=None,
        reduction_issuer=reduction_issuer,
        reduction_plan=reduction_plan,
        final_points=final_points,
        source_event_count=len(upstream.source_events),
    )
    binding = CleanupSharedOutputBinding(
        request=None,
        default_selection=selection,
        input_digest=_input_digest(upstream, None, selection),
        upstream_context=upstream,
        event_issuer=None,
        event_plan=None,
        reduction_issuer=reduction_issuer,
        reduction_plan=reduction_plan,
        final_plan=reduction_plan,
        final_plan_kind="key_reduction",
        final_projection=final_projection,
        final_points=final_points,
        summary=summary,
    )
    context = SharedFinalOutputContext(
        input_identity=final_input_identity,
        identity=final_identity,
        issuer_context=upstream.issuer_context,
        candidate=upstream.candidate,
        projection=final_projection,
        source_events=upstream.source_events,
        restriction_event_targets=upstream.restriction_event_targets,
        ticket=upstream.ticket,
        lifecycle_epoch=upstream.lifecycle_epoch,
        lifecycle_signature=upstream.lifecycle_signature,
        transition_binding=upstream.transition_binding,
        default_selection=upstream.default_selection,
        cleanup_binding=binding,
    )
    validate_cleanup_shared_binding(binding)
    return context


def _validate_default_cleanup_binding(binding: CleanupSharedOutputBinding) -> None:
    selection = binding.default_selection
    upstream = binding.upstream_context
    if not isinstance(selection, DefaultCleanupSelection) or binding.request is not None:
        raise CleanupSharedOutputError("default cleanup binding selection is invalid")
    from src.core.final_output_projection import shared_output_consumer_view

    shared_output_consumer_view(upstream)
    if (
        upstream.cleanup_binding is not None
        or upstream.input_identity.cleanup_input_digest is not None
        or upstream.input_identity.cleanup_application_binding_digest is not None
        or binding.input_digest != _input_digest(upstream, None, selection)
    ):
        raise CleanupSharedOutputError("default cleanup input binding differs from its current source")
    _validate_default_cleanup_source(upstream, selection, None)
    if binding.event_issuer is not None or binding.event_plan is not None:
        raise CleanupSharedOutputError("event cleanup is forbidden by the adopted default")
    if selection.selection_kind in {"scope_excluded", "no_applicable"}:
        expected_plan: object = (
            upstream.transition_binding.plan
            if upstream.transition_binding is not None
            else _closure_plan(upstream)
        )
        expected_points = _final_points(_closure_plan(upstream), _event_source_map(upstream))
        if (
            binding.reduction_issuer is not None
            or binding.reduction_plan is not None
            or binding.final_plan != expected_plan
            or binding.final_plan_kind != "upstream"
            or binding.final_projection != upstream.projection
            or binding.final_points != expected_points
        ):
            raise CleanupSharedOutputError("non-applicable default must preserve the upstream output")
        final_input_identity = replace(
            upstream.input_identity,
            cleanup_input_digest=binding.input_digest,
            cleanup_application_binding_digest=selection.selection_digest,
        )
        final_plan_row = expected_plan.to_dict()
        final_identity = FinalOutputIdentity(
            input_identity=final_input_identity,
            plan_schema_id=final_plan_row["schema_id"],
            curve_policy_id=upstream.identity.curve_policy_id,
            semantic_digest=final_plan_row["semantic_digest"],
            wire_digest=upstream.projection.wire_digest,
        )
        expected_summary = _summary(
            request=None,
            default_selection=selection,
            final_identity=final_identity,
            event_issuer=None,
            event_plan=None,
            reduction_issuer=None,
            reduction_plan=None,
            final_points=expected_points,
            source_event_count=len(upstream.source_events),
        )
        if binding.summary != expected_summary:
            raise CleanupSharedOutputError("non-applicable default summary differs from its source")
        return
    if selection.selection_kind != "cleanup":
        raise CleanupSharedOutputError("default cleanup selection kind is unsupported")
    issuer, plan = binding.reduction_issuer, binding.reduction_plan
    if not isinstance(issuer, KeyReductionInput) or not isinstance(plan, FinalMorphKeyReductionPlan):
        raise CleanupSharedOutputError("default key reduction issuer or plan is missing")
    if issuer.policy != selection.binding.key_policy or issuer.input_kind != "ms32_baseline":
        raise CleanupSharedOutputError("default key reduction policy or source kind differs")
    expected_protection_binding = resolve_current_key_protections(
        issuer.points, issuer.upstream_requirements
    )
    if issuer.protection_binding != expected_protection_binding:
        raise CleanupSharedOutputError("default protections differ from current source metadata")
    validation = validate_key_reduction_plan(plan, issuer)
    if validation.state != "valid" or validation.issues:
        raise CleanupSharedOutputError("default key reduction no longer validates against its source")
    if binding.final_plan != plan or binding.final_plan_kind != "key_reduction":
        raise CleanupSharedOutputError("default final plan differs from the key reduction plan")
    projected = _reduction_projection(plan, issuer)
    if binding.final_projection != projected or binding.final_projection.wire_digest != projected.wire_digest:
        raise CleanupSharedOutputError("default final projection differs from its validated plan")
    expected_points = _final_points(plan, _event_source_map(upstream))
    if binding.final_points != expected_points:
        raise CleanupSharedOutputError("default final point view differs from its validated plan")
    input_identity = replace(
        upstream.input_identity,
        cleanup_input_digest=binding.input_digest,
        cleanup_application_binding_digest=selection.selection_digest,
    )
    final_plan_row = plan.to_dict()
    final_identity = FinalOutputIdentity(
        input_identity=input_identity,
        plan_schema_id=final_plan_row["schema_id"],
        curve_policy_id=upstream.identity.curve_policy_id,
        semantic_digest=final_plan_row["semantic_digest"],
        wire_digest=projected.wire_digest,
    )
    expected_summary = _summary(
        request=None,
        default_selection=selection,
        final_identity=final_identity,
        event_issuer=None,
        event_plan=None,
        reduction_issuer=issuer,
        reduction_plan=plan,
        final_points=expected_points,
        source_event_count=len(upstream.source_events),
    )
    if binding.summary != expected_summary:
        raise CleanupSharedOutputError("default cleanup summary differs from its validated plan")


def validate_cleanup_shared_binding(binding: CleanupSharedOutputBinding) -> None:
    """Re-run the B2/B3 issuer checks and confirm the final projection and summary."""
    if not isinstance(binding, CleanupSharedOutputBinding):
        raise CleanupSharedOutputError("cleanup binding type is invalid")
    if binding.default_selection is not None:
        _validate_default_cleanup_binding(binding)
        return
    request = binding.request
    if not isinstance(request, CleanupEvaluationRequest):
        raise CleanupSharedOutputError("evaluation cleanup request is missing")
    upstream = binding.upstream_context
    from src.core.final_output_projection import shared_output_consumer_view

    shared_output_consumer_view(upstream)
    if binding.input_digest != _input_digest(upstream, request):
        raise CleanupSharedOutputError("cleanup input digest differs from the captured source")
    if request.variant in {"events_only", "events_and_keys"}:
        if binding.event_issuer is None or binding.event_plan is None:
            raise CleanupSharedOutputError("required B2 issuer or plan is missing")
        if binding.event_issuer.policy != request.event_policy:
            raise CleanupSharedOutputError("B2 issuer policy differs from the request")
        event_validation = validate_event_cleanup_plan(binding.event_plan, binding.event_issuer)
        if event_validation.state != "valid" or event_validation.issues:
            raise CleanupSharedOutputError("B2 plan no longer validates against its source")
    elif binding.event_issuer is not None or binding.event_plan is not None:
        raise CleanupSharedOutputError("unexpected B2 issuer or plan for this variant")

    if request.variant in {"keys_only", "events_and_keys"}:
        if binding.reduction_issuer is None or binding.reduction_plan is None:
            raise CleanupSharedOutputError("required B3 issuer or plan is missing")
        if binding.reduction_issuer.policy != request.key_policy:
            raise CleanupSharedOutputError("B3 issuer policy differs from the request")
        reduction_validation = validate_key_reduction_plan(binding.reduction_plan, binding.reduction_issuer)
        if reduction_validation.state != "valid" or reduction_validation.issues:
            raise CleanupSharedOutputError("B3 plan no longer validates against its source")
        projected = _reduction_projection(binding.reduction_plan, binding.reduction_issuer)
        expected_plan: object = binding.reduction_plan
    elif binding.reduction_issuer is not None or binding.reduction_plan is not None:
        raise CleanupSharedOutputError("unexpected B3 issuer or plan for this variant")
    elif binding.event_plan is not None:
        projected = project_validated_cleanup_plan(binding.event_plan, binding.event_issuer).closure_projection
        expected_plan = binding.event_plan
    else:
        upstream_view = upstream.projection
        projected = upstream_view
        expected_plan = upstream.transition_binding.plan if upstream.transition_binding is not None else _closure_plan(upstream)

    if (
        binding.final_plan != expected_plan
        or binding.final_projection != projected
        or binding.final_projection.wire_digest != projected.wire_digest
    ):
        raise CleanupSharedOutputError("final plan differs from its independently validated projection")
    expected_points = _final_points(
        _closure_plan(upstream) if binding.final_plan_kind == "upstream" else binding.final_plan,
        _event_source_map(upstream),
    )
    if expected_points != binding.final_points:
        raise CleanupSharedOutputError("final semantic point view differs from the final plan")
    final_plan_row = binding.final_plan.to_dict()
    final_identity = FinalOutputIdentity(
        input_identity=replace(upstream.input_identity, cleanup_input_digest=binding.input_digest),
        plan_schema_id=final_plan_row["schema_id"],
        curve_policy_id=upstream.identity.curve_policy_id,
        semantic_digest=final_plan_row["semantic_digest"],
        wire_digest=binding.final_projection.wire_digest,
    )
    expected_summary = _summary(
        request=request,
        default_selection=None,
        final_identity=final_identity,
        event_issuer=binding.event_issuer,
        event_plan=binding.event_plan,
        reduction_issuer=binding.reduction_issuer,
        reduction_plan=binding.reduction_plan,
        final_points=binding.final_points,
        source_event_count=len(upstream.source_events),
    )
    if binding.summary != expected_summary:
        raise CleanupSharedOutputError("cleanup summary differs from its validated plans")


__all__ = [
    "CleanupPointView",
    "CleanupSharedOutputBinding",
    "CleanupSharedOutputError",
    "CleanupSharedSummary",
    "build_default_cleanup_shared_output",
    "build_cleanup_shared_output",
    "validate_cleanup_shared_binding",
]
