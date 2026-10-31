"""Immutable MS33-B2 outer plan and strict JSON representation."""
from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass
from typing import Any, Mapping


PLAN_SCHEMA = "final-morph-cleanup-plan/v1"


class CleanupPlanError(ValueError):
    """Raised when a cleanup plan or one of its records is malformed."""


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CleanupPlanError("cleanup plan contains a non-canonical value") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _copy_json_object(value: object, name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise CleanupPlanError(f"{name} must be an object")
    try:
        copied = json.loads(_canonical_json(value).decode("utf-8"))
    except (TypeError, ValueError) as error:
        raise CleanupPlanError(f"{name} is not JSON-safe") from error
    return copied


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
        raise CleanupPlanError(f"{name} must be a finite non-negative number")
    return float(value)


@dataclass(frozen=True, slots=True)
class CleanupPoint:
    frame_no: int
    semantic_morph: str
    canonical_value: float
    binary32_hex: str
    wire_value: float
    source_ids: tuple[str, ...]
    source_event_indices: tuple[int, ...]
    point_kinds: tuple[str, ...]
    intent_origins: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    shape_ordinal: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.frame_no, bool) or not isinstance(self.frame_no, int) or self.frame_no < 0 or self.frame_no > 0xFFFFFFFF:
            raise CleanupPlanError("cleanup point frame is invalid")
        if self.semantic_morph not in {"あ", "い", "う", "え", "お"}:
            raise CleanupPlanError("cleanup point morph is invalid")
        canonical = _finite_nonnegative(self.canonical_value, "canonical_value")
        wire = _finite_nonnegative(self.wire_value, "wire_value")
        if type(self.binary32_hex) is not str:
            raise CleanupPlanError("binary32_hex must be text")
        try:
            raw = bytes.fromhex(self.binary32_hex)
        except ValueError as error:
            raise CleanupPlanError("binary32_hex is invalid") from error
        if len(raw) != 4 or raw.hex() != self.binary32_hex.lower():
            raise CleanupPlanError("binary32_hex is not canonical")
        decoded = struct.unpack("<f", raw)[0]
        if not math.isfinite(decoded) or decoded != wire:
            raise CleanupPlanError("wire_value does not match binary32_hex")
        if decoded == 0.0 and raw != b"\0\0\0\0":
            raise CleanupPlanError("zero wire values must use canonical positive zero")
        if canonical == 0.0 and decoded != 0.0:
            raise CleanupPlanError("canonical zero cannot have a nonzero wire value")
        for field_name in ("source_ids", "point_kinds", "intent_origins", "requirement_ids"):
            values = getattr(self, field_name)
            if type(values) is not tuple or any(type(item) is not str or not item for item in values):
                raise CleanupPlanError(f"{field_name} must be a tuple of non-empty text")
        if type(self.source_event_indices) is not tuple or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in self.source_event_indices):
            raise CleanupPlanError("source_event_indices must be a tuple of non-negative integers")
        if self.shape_ordinal is not None and (isinstance(self.shape_ordinal, bool) or not isinstance(self.shape_ordinal, int) or self.shape_ordinal < 0):
            raise CleanupPlanError("shape_ordinal is invalid")

    def to_dict(self) -> dict[str, object]:
        return {
            "frame_no": self.frame_no,
            "semantic_morph": self.semantic_morph,
            "canonical_value": self.canonical_value,
            "binary32_hex": self.binary32_hex,
            "wire_value": self.wire_value,
            "source_ids": list(self.source_ids),
            "source_event_indices": list(self.source_event_indices),
            "point_kinds": list(self.point_kinds),
            "intent_origins": list(self.intent_origins),
            "requirement_ids": list(self.requirement_ids),
            "shape_ordinal": self.shape_ordinal,
        }

    @classmethod
    def from_dict(cls, value: object) -> "CleanupPoint":
        fields = {"frame_no", "semantic_morph", "canonical_value", "binary32_hex", "wire_value", "source_ids", "source_event_indices", "point_kinds", "intent_origins", "requirement_ids", "shape_ordinal"}
        if type(value) is not dict or set(value) != fields:
            raise CleanupPlanError("cleanup point fields are invalid")
        for name in ("source_ids", "source_event_indices", "point_kinds", "intent_origins", "requirement_ids"):
            if type(value[name]) is not list:
                raise CleanupPlanError(f"cleanup point {name} must be an array")
        return cls(
            frame_no=value["frame_no"], semantic_morph=value["semantic_morph"],
            canonical_value=value["canonical_value"], binary32_hex=value["binary32_hex"], wire_value=value["wire_value"],
            source_ids=tuple(value["source_ids"]), source_event_indices=tuple(value["source_event_indices"]),
            point_kinds=tuple(value["point_kinds"]), intent_origins=tuple(value["intent_origins"]),
            requirement_ids=tuple(value["requirement_ids"]), shape_ordinal=value["shape_ordinal"],
        )


@dataclass(frozen=True, slots=True)
class CleanupDecision:
    event_id: str
    source_event_indices: tuple[int, ...]
    shape_ordinal: int | None
    action: str
    reasons: tuple[str, ...]
    evidence: tuple[str, ...]
    influence_interval: tuple[int, int] | None
    changed_keys: tuple[tuple[int, str], ...]

    def __post_init__(self) -> None:
        if not self.event_id or self.action not in {"suppress_event", "protected_keep", "uncertain_keep", "out_of_scope", "disabled_keep"}:
            raise CleanupPlanError("cleanup decision identity or action is invalid")
        if type(self.source_event_indices) is not tuple or any(isinstance(i, bool) or not isinstance(i, int) or i < 0 for i in self.source_event_indices):
            raise CleanupPlanError("decision source event indices are invalid")
        if type(self.reasons) is not tuple or type(self.evidence) is not tuple or any(type(v) is not str or not v for v in (*self.reasons, *self.evidence)):
            raise CleanupPlanError("decision reasons and evidence must be text tuples")
        if self.shape_ordinal is not None and (isinstance(self.shape_ordinal, bool) or not isinstance(self.shape_ordinal, int) or self.shape_ordinal < 0):
            raise CleanupPlanError("decision shape_ordinal is invalid")
        if self.influence_interval is not None:
            if type(self.influence_interval) is not tuple or len(self.influence_interval) != 2 or any(isinstance(v, bool) or not isinstance(v, int) for v in self.influence_interval) or self.influence_interval[0] > self.influence_interval[1]:
                raise CleanupPlanError("decision influence interval is invalid")
        if type(self.changed_keys) is not tuple or any(type(key) is not tuple or len(key) != 2 or isinstance(key[0], bool) or not isinstance(key[0], int) or key[0] < 0 or key[1] not in {"あ", "い", "う", "え", "お"} for key in self.changed_keys):
            raise CleanupPlanError("decision changed_keys are invalid")

    def to_dict(self) -> dict[str, object]:
        return {"event_id": self.event_id, "source_event_indices": list(self.source_event_indices), "shape_ordinal": self.shape_ordinal, "action": self.action, "reasons": list(self.reasons), "evidence": list(self.evidence), "influence_interval": None if self.influence_interval is None else list(self.influence_interval), "changed_keys": [[frame, morph] for frame, morph in self.changed_keys]}

    @classmethod
    def from_dict(cls, value: object) -> "CleanupDecision":
        fields = {"event_id", "source_event_indices", "shape_ordinal", "action", "reasons", "evidence", "influence_interval", "changed_keys"}
        if type(value) is not dict or set(value) != fields:
            raise CleanupPlanError("cleanup decision fields are invalid")
        for name in ("source_event_indices", "reasons", "evidence", "changed_keys"):
            if type(value[name]) is not list:
                raise CleanupPlanError(f"cleanup decision {name} must be an array")
        interval = value["influence_interval"]
        if interval is not None and type(interval) is not list:
            raise CleanupPlanError("cleanup decision influence_interval must be null or an array")
        return cls(value["event_id"], tuple(value["source_event_indices"]), value["shape_ordinal"], value["action"], tuple(value["reasons"]), tuple(value["evidence"]), None if interval is None else tuple(interval), tuple(tuple(item) for item in value["changed_keys"]))


@dataclass(frozen=True, slots=True)
class CleanupChange:
    event_id: str
    frame_no: int
    semantic_morph: str
    before_canonical: float
    after_canonical: float
    before_binary32_hex: str
    after_binary32_hex: str
    reason: str
    policy_digest: str
    source_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.event_id) is not str or not self.event_id:
            raise CleanupPlanError("cleanup change event_id is invalid")
        if isinstance(self.frame_no, bool) or not isinstance(self.frame_no, int) or self.frame_no < 0 or self.frame_no > 0xFFFFFFFF:
            raise CleanupPlanError("cleanup change frame_no is invalid")
        if self.semantic_morph not in {"あ", "い", "う", "え", "お"}:
            raise CleanupPlanError("cleanup change semantic_morph is invalid")
        before_canonical = _finite_nonnegative(self.before_canonical, "before_canonical")
        after_canonical = _finite_nonnegative(self.after_canonical, "after_canonical")
        if before_canonical <= 0.0 or after_canonical != 0.0:
            raise CleanupPlanError("cleanup change must replace a positive value with canonical zero")
        for name, value in (("before_binary32_hex", self.before_binary32_hex), ("after_binary32_hex", self.after_binary32_hex)):
            if type(value) is not str:
                raise CleanupPlanError(f"{name} must be text")
            try:
                raw = bytes.fromhex(value)
            except ValueError as error:
                raise CleanupPlanError(f"{name} is invalid") from error
            if len(raw) != 4 or raw.hex() != value.lower():
                raise CleanupPlanError(f"{name} is not canonical")
        try:
            before_wire = struct.unpack("<f", bytes.fromhex(self.before_binary32_hex))[0]
            after_wire_raw = bytes.fromhex(self.after_binary32_hex)
            after_wire = struct.unpack("<f", after_wire_raw)[0]
        except struct.error as error:
            raise CleanupPlanError("cleanup change wire value is malformed") from error
        if not math.isfinite(before_wire) or before_wire <= 0.0 or not math.isfinite(after_wire) or after_wire != 0.0 or after_wire_raw != b"\0\0\0\0":
            raise CleanupPlanError("cleanup change must replace a positive saved wire value with canonical zero")
        if type(self.reason) is not str or not self.reason.strip() or type(self.policy_digest) is not str or len(self.policy_digest) != 64 or any(ch not in "0123456789abcdef" for ch in self.policy_digest):
            raise CleanupPlanError("cleanup change reason or policy digest is invalid")
        for name, values in (("source_ids", self.source_ids), ("requirement_ids", self.requirement_ids)):
            if type(values) is not tuple or any(type(value) is not str or not value for value in values):
                raise CleanupPlanError(f"cleanup change {name} are invalid")

    def to_dict(self) -> dict[str, object]:
        return {"event_id": self.event_id, "frame_no": self.frame_no, "semantic_morph": self.semantic_morph, "before_canonical": self.before_canonical, "after_canonical": self.after_canonical, "before_binary32_hex": self.before_binary32_hex, "after_binary32_hex": self.after_binary32_hex, "reason": self.reason, "policy_digest": self.policy_digest, "source_ids": list(self.source_ids), "requirement_ids": list(self.requirement_ids)}

    @classmethod
    def from_dict(cls, value: object) -> "CleanupChange":
        fields = {"event_id", "frame_no", "semantic_morph", "before_canonical", "after_canonical", "before_binary32_hex", "after_binary32_hex", "reason", "policy_digest", "source_ids", "requirement_ids"}
        if type(value) is not dict or set(value) != fields or type(value["source_ids"]) is not list or type(value["requirement_ids"]) is not list:
            raise CleanupPlanError("cleanup change fields are invalid")
        return cls(value["event_id"], value["frame_no"], value["semantic_morph"], value["before_canonical"], value["after_canonical"], value["before_binary32_hex"], value["after_binary32_hex"], value["reason"], value["policy_digest"], tuple(value["source_ids"]), tuple(value["requirement_ids"]))


@dataclass(frozen=True, slots=True)
class FinalMorphCleanupPlan:
    identity: dict[str, Any]
    original_transition_plan: dict[str, Any]
    original_requirements: tuple[dict[str, Any], ...]
    decisions: tuple[CleanupDecision, ...]
    points: tuple[CleanupPoint, ...]
    changes: tuple[CleanupChange, ...]
    state: str
    issues: tuple[str, ...]
    semantic_digest: str
    wire_digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_id": PLAN_SCHEMA,
            "identity": self.identity,
            "original_transition_plan": self.original_transition_plan,
            "original_requirements": list(self.original_requirements),
            "decisions": [item.to_dict() for item in self.decisions],
            "points": [item.to_dict() for item in self.points],
            "changes": [item.to_dict() for item in self.changes],
            "state": self.state,
            "issues": list(self.issues),
            "semantic_digest": self.semantic_digest,
            "wire_digest": self.wire_digest,
        }


def cleanup_wire_digest(points: tuple[CleanupPoint, ...], output_mapping: object) -> str:
    if type(output_mapping) not in (list, tuple):
        raise CleanupPlanError("output_mapping must be a sequence")
    rows = [{"frame_no": item.frame_no, "semantic_morph": item.semantic_morph, "binary32_hex": item.binary32_hex} for item in points]
    return _digest({"output_mapping": output_mapping, "points": rows})


def _semantic_payload(*, identity: dict[str, Any], original_transition_plan: dict[str, Any], original_requirements: tuple[dict[str, Any], ...], decisions: tuple[CleanupDecision, ...], points: tuple[CleanupPoint, ...], changes: tuple[CleanupChange, ...], state: str, issues: tuple[str, ...]) -> dict[str, object]:
    return {"schema_id": PLAN_SCHEMA, "identity": identity, "original_transition_plan": original_transition_plan, "original_requirements": list(original_requirements), "decisions": [item.to_dict() for item in decisions], "points": [item.to_dict() for item in points], "changes": [item.to_dict() for item in changes], "state": state, "issues": list(issues)}


def create_final_morph_cleanup_plan(*, identity: Mapping[str, object], original_transition_plan: Mapping[str, object], original_requirements: tuple[dict[str, Any], ...], decisions: tuple[CleanupDecision, ...], points: tuple[CleanupPoint, ...], changes: tuple[CleanupChange, ...], state: str, issues: tuple[str, ...], output_mapping: object) -> FinalMorphCleanupPlan:
    if state not in {"valid", "invalid", "unavailable"}:
        raise CleanupPlanError("cleanup plan state is invalid")
    identity_copy = _copy_json_object(dict(identity), "identity")
    transition_copy = _copy_json_object(dict(original_transition_plan), "original_transition_plan")
    requirements_copy = tuple(_copy_json_object(item, "original requirement") for item in original_requirements)
    if type(decisions) is not tuple or type(points) is not tuple or type(changes) is not tuple:
        raise CleanupPlanError("cleanup plan records must be tuples")
    ordered_points = tuple(sorted(points, key=lambda item: (item.frame_no, "あいうえお".index(item.semantic_morph))))
    keys = [(point.frame_no, point.semantic_morph) for point in ordered_points]
    if len(keys) != len(set(keys)):
        raise CleanupPlanError("cleanup plan contains duplicate frame/morph keys")
    if tuple(points) != ordered_points:
        raise CleanupPlanError("cleanup points are not in canonical order")
    if any(not isinstance(item, CleanupDecision) for item in decisions) or any(not isinstance(item, CleanupPoint) for item in points) or any(not isinstance(item, CleanupChange) for item in changes):
        raise CleanupPlanError("cleanup plan record type is invalid")
    if type(issues) is not tuple or any(type(item) is not str or not item for item in issues):
        raise CleanupPlanError("cleanup plan issues are invalid")
    semantic = _semantic_payload(identity=identity_copy, original_transition_plan=transition_copy, original_requirements=requirements_copy, decisions=decisions, points=points, changes=changes, state=state, issues=issues)
    return FinalMorphCleanupPlan(identity_copy, transition_copy, requirements_copy, decisions, points, changes, state, issues, _digest(semantic), cleanup_wire_digest(points, output_mapping))


def read_final_morph_cleanup_plan(value: object) -> FinalMorphCleanupPlan:
    fields = {"schema_id", "identity", "original_transition_plan", "original_requirements", "decisions", "points", "changes", "state", "issues", "semantic_digest", "wire_digest"}
    if type(value) is not dict or set(value) != fields or value["schema_id"] != PLAN_SCHEMA:
        raise CleanupPlanError("cleanup plan schema or fields are invalid")
    if type(value["original_requirements"]) is not list or type(value["decisions"]) is not list or type(value["points"]) is not list or type(value["changes"]) is not list or type(value["issues"]) is not list:
        raise CleanupPlanError("cleanup plan arrays are invalid")
    points = tuple(CleanupPoint.from_dict(item) for item in value["points"])
    decisions = tuple(CleanupDecision.from_dict(item) for item in value["decisions"])
    changes = tuple(CleanupChange.from_dict(item) for item in value["changes"])
    plan = create_final_morph_cleanup_plan(
        identity=value["identity"], original_transition_plan=value["original_transition_plan"],
        original_requirements=tuple(value["original_requirements"]), decisions=decisions, points=points,
        changes=changes, state=value["state"], issues=tuple(value["issues"]),
        output_mapping=value["identity"].get("output_mapping") if type(value["identity"]) is dict else None,
    )
    if plan.semantic_digest != value["semantic_digest"] or plan.wire_digest != value["wire_digest"]:
        raise CleanupPlanError("cleanup plan digest does not match its content")
    return plan


def validate_final_morph_cleanup_plan_integrity(plan: FinalMorphCleanupPlan) -> None:
    if not isinstance(plan, FinalMorphCleanupPlan):
        raise CleanupPlanError("cleanup plan type is invalid")
    rebuilt = create_final_morph_cleanup_plan(
        identity=plan.identity, original_transition_plan=plan.original_transition_plan,
        original_requirements=plan.original_requirements, decisions=plan.decisions, points=plan.points,
        changes=plan.changes, state=plan.state, issues=plan.issues,
        output_mapping=plan.identity.get("output_mapping"),
    )
    if rebuilt.semantic_digest != plan.semantic_digest or rebuilt.wire_digest != plan.wire_digest:
        raise CleanupPlanError("cleanup plan integrity check failed")


__all__ = ["CleanupChange", "CleanupDecision", "CleanupPlanError", "CleanupPoint", "FinalMorphCleanupPlan", "PLAN_SCHEMA", "cleanup_wire_digest", "create_final_morph_cleanup_plan", "read_final_morph_cleanup_plan", "validate_final_morph_cleanup_plan_integrity"]
