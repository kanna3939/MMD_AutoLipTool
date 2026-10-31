"""Immutable-by-contract records for MS33-B3 redundant-key reduction."""
from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from src.core.canonical_morph_value import CanonicalMorphValue, CanonicalMorphValueError
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER


POLICY_SCHEMA = "key-reduction-policy/v1"
INPUT_SCHEMA = "key-reduction-input/v1"
PLAN_SCHEMA = "final-morph-key-reduction-plan/v1"
_POINT_FIELDS = frozenset({
    "frame_no", "semantic_morph", "output_morph_name", "canonical_value",
    "binary32_hex", "source_ids", "source_record_ids", "source_event_indices",
    "point_kinds", "intent_origins", "requirement_ids", "shape_ordinal",
})
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class KeyReductionPlanError(ValueError):
    """Raised when an MS33-B3 record is malformed or inconsistent."""


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise KeyReductionPlanError("record is not canonical JSON") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise KeyReductionPlanError(f"{name} must be text")
    return value


def _require_int(value: object, name: str, *, maximum: int = 0xFFFFFFFF) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
        raise KeyReductionPlanError(f"{name} must be a non-negative integer")
    return value


def _require_hash(value: object, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise KeyReductionPlanError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _require_text_tuple(value: object, name: str) -> tuple[str, ...]:
    if type(value) not in (tuple, list) or any(type(item) is not str or not item for item in value):
        raise KeyReductionPlanError(f"{name} must be an array of non-empty text")
    values = tuple(value)
    if len(set(values)) != len(values):
        raise KeyReductionPlanError(f"{name} contains duplicates")
    return values


def _copy_json_object(value: object, name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise KeyReductionPlanError(f"{name} must be an object")
    try:
        copied = json.loads(_canonical_json(value))
    except (json.JSONDecodeError, KeyReductionPlanError) as error:
        raise KeyReductionPlanError(f"{name} is not JSON data") from error
    if type(copied) is not dict:
        raise KeyReductionPlanError(f"{name} must be an object")
    return copied


def _reject_constant(value: str) -> None:
    raise KeyReductionPlanError(f"invalid JSON numeric constant: {value}")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise KeyReductionPlanError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _strict_object(value: object, fields: frozenset[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise KeyReductionPlanError(f"{name} has an invalid field set")
    return value


@dataclass(frozen=True, slots=True)
class KeyReductionPolicy:
    policy_id: str
    key_contract_digest: str
    protections: tuple[dict[str, object], ...]
    curve_domains: tuple[str, ...]
    algorithm_id: str
    enabled: bool
    policy_digest: str
    schema_id: str = POLICY_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != POLICY_SCHEMA:
            raise KeyReductionPlanError("unsupported key reduction policy schema")
        _require_text(self.policy_id, "policy_id")
        _require_hash(self.key_contract_digest, "key_contract_digest")
        if type(self.protections) is not tuple or any(type(item) is not dict for item in self.protections):
            raise KeyReductionPlanError("protections must be a tuple of objects")
        object.__setattr__(self, "protections", tuple(_copy_json_object(item, "protections") for item in self.protections))
        if self.curve_domains != ("canonical_binary64", "saved_binary32"):
            raise KeyReductionPlanError("unsupported curve domains")
        if self.algorithm_id != "exact-collinear-stack/v1":
            raise KeyReductionPlanError("unsupported reduction algorithm")
        if type(self.enabled) is not bool:
            raise KeyReductionPlanError("enabled must be a boolean")
        self.validate_integrity()

    def validate_integrity(self) -> None:
        _require_hash(self.policy_digest, "policy_digest")
        if _digest(self._payload(include_digest=False)) != self.policy_digest:
            raise KeyReductionPlanError("policy digest does not match its content")

    def _payload(self, *, include_digest: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_id": self.schema_id,
            "policy_id": self.policy_id,
            "key_contract_digest": self.key_contract_digest,
            "protections": [_copy_json_object(item, "protections") for item in self.protections],
            "curve_domains": list(self.curve_domains),
            "algorithm_id": self.algorithm_id,
            "enabled": self.enabled,
        }
        if include_digest:
            value["policy_digest"] = self.policy_digest
        return value

    def to_dict(self) -> dict[str, object]:
        return self._payload()

    @classmethod
    def create(
        cls, *, policy_id: str, key_contract: Mapping[str, object], protections: tuple[dict[str, object], ...], enabled: bool = True,
    ) -> "KeyReductionPolicy":
        key_digest = _digest(dict(key_contract))
        payload = {
            "schema_id": POLICY_SCHEMA,
            "policy_id": policy_id,
            "key_contract_digest": key_digest,
            "protections": list(protections),
            "curve_domains": ["canonical_binary64", "saved_binary32"],
            "algorithm_id": "exact-collinear-stack/v1",
            "enabled": enabled,
        }
        return cls(
            policy_id=policy_id,
            key_contract_digest=key_digest,
            protections=tuple(_copy_json_object(item, "protections") for item in protections),
            curve_domains=("canonical_binary64", "saved_binary32"),
            algorithm_id="exact-collinear-stack/v1",
            enabled=enabled,
            policy_digest=_digest(payload),
        )


@dataclass(frozen=True, slots=True)
class ReductionPoint:
    frame_no: int
    semantic_morph: str
    output_morph_name: str
    canonical_value: CanonicalMorphValue
    source_ids: tuple[str, ...]
    source_record_ids: tuple[str, ...]
    source_event_indices: tuple[int, ...]
    point_kinds: tuple[str, ...]
    intent_origins: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    shape_ordinal: int | None = None

    def __post_init__(self) -> None:
        _require_int(self.frame_no, "frame_no")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise KeyReductionPlanError("semantic_morph is unsupported")
        _require_text(self.output_morph_name, "output_morph_name")
        if not isinstance(self.canonical_value, CanonicalMorphValue):
            raise KeyReductionPlanError("canonical_value must be CanonicalMorphValue")
        for name in ("source_ids", "source_record_ids", "point_kinds", "intent_origins", "requirement_ids"):
            _require_text_tuple(getattr(self, name), name)
        if type(self.source_event_indices) is not tuple or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in self.source_event_indices):
            raise KeyReductionPlanError("source_event_indices must be a tuple of non-negative integers")
        if len(set(self.source_event_indices)) != len(self.source_event_indices):
            raise KeyReductionPlanError("source_event_indices contains duplicates")
        if self.shape_ordinal is not None:
            _require_int(self.shape_ordinal, "shape_ordinal")

    @property
    def key(self) -> tuple[int, str]:
        return (self.frame_no, self.semantic_morph)

    @property
    def wire_value(self) -> float:
        return struct.unpack("<f", self.canonical_value.binary32_bytes)[0]

    def to_dict(self) -> dict[str, object]:
        return {
            "frame_no": self.frame_no,
            "semantic_morph": self.semantic_morph,
            "output_morph_name": self.output_morph_name,
            "canonical_value": self.canonical_value.to_dict(),
            "binary32_hex": self.canonical_value.binary32_hex,
            "source_ids": list(self.source_ids),
            "source_record_ids": list(self.source_record_ids),
            "source_event_indices": list(self.source_event_indices),
            "point_kinds": list(self.point_kinds),
            "intent_origins": list(self.intent_origins),
            "requirement_ids": list(self.requirement_ids),
            "shape_ordinal": self.shape_ordinal,
        }

    @classmethod
    def from_dict(cls, value: object) -> "ReductionPoint":
        row = _strict_object(value, _POINT_FIELDS, "reduction point")
        canonical = CanonicalMorphValue.from_dict(row["canonical_value"])
        if row["binary32_hex"] != canonical.binary32_hex:
            raise KeyReductionPlanError("point binary32 value differs from its canonical value")
        try:
            return cls(
                frame_no=row["frame_no"], semantic_morph=row["semantic_morph"], output_morph_name=row["output_morph_name"],
                canonical_value=canonical,
                source_ids=_require_text_tuple(row["source_ids"], "source_ids"),
                source_record_ids=_require_text_tuple(row["source_record_ids"], "source_record_ids"),
                source_event_indices=tuple(row["source_event_indices"]),
                point_kinds=_require_text_tuple(row["point_kinds"], "point_kinds"),
                intent_origins=_require_text_tuple(row["intent_origins"], "intent_origins"),
                requirement_ids=_require_text_tuple(row["requirement_ids"], "requirement_ids"),
                shape_ordinal=row["shape_ordinal"],
            )
        except (TypeError, CanonicalMorphValueError) as error:
            raise KeyReductionPlanError("reduction point is invalid") from error


@dataclass(frozen=True, slots=True)
class KeyRemoval:
    point: ReductionPoint
    reason: str
    left_anchor: tuple[int, str]
    right_anchor: tuple[int, str]
    scalar_proof: dict[str, str]
    wire_proof: dict[str, str]
    policy_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.point, ReductionPoint):
            raise KeyReductionPlanError("removed point is invalid")
        if self.reason != "exact_collinear":
            raise KeyReductionPlanError("unsupported key removal reason")
        if type(self.left_anchor) is not tuple or type(self.right_anchor) is not tuple or len(self.left_anchor) != 2 or len(self.right_anchor) != 2:
            raise KeyReductionPlanError("removal anchors are malformed")
        if type(self.left_anchor[0]) is not int or type(self.right_anchor[0]) is not int:
            raise KeyReductionPlanError("removal anchor frame is invalid")
        if self.left_anchor[1] not in SEMANTIC_VOWEL_ORDER or self.right_anchor[1] not in SEMANTIC_VOWEL_ORDER:
            raise KeyReductionPlanError("removal anchor morph is invalid")
        if self.left_anchor[1] != self.point.semantic_morph or self.right_anchor[1] != self.point.semantic_morph or not self.left_anchor[0] < self.point.frame_no < self.right_anchor[0]:
            raise KeyReductionPlanError("removal anchors do not bracket the removed point")
        if type(self.scalar_proof) is not dict or type(self.wire_proof) is not dict:
            raise KeyReductionPlanError("removal proof is malformed")
        _validate_rational_proof(self.scalar_proof)
        _validate_rational_proof(self.wire_proof)
        _require_hash(self.policy_digest, "removal policy_digest")

    def to_dict(self) -> dict[str, object]:
        return {
            "key": {"frame_no": self.point.frame_no, "semantic_morph": self.point.semantic_morph},
            "original_point": self.point.to_dict(),
            "reason": self.reason,
            "left_anchor": {"frame_no": self.left_anchor[0], "semantic_morph": self.left_anchor[1]},
            "right_anchor": {"frame_no": self.right_anchor[0], "semantic_morph": self.right_anchor[1]},
            "scalar_proof": dict(self.scalar_proof),
            "wire_proof": dict(self.wire_proof),
            "source_ids": list(self.point.source_ids),
            "policy_digest": self.policy_digest,
        }


@dataclass(frozen=True, slots=True)
class KeyReductionInput:
    input_kind: str
    source_binding: dict[str, object]
    upstream_plan: dict[str, object]
    upstream_requirements: tuple[dict[str, object], ...]
    points: tuple[ReductionPoint, ...]
    upstream_wire_digest: str
    protection_binding: dict[str, object]
    policy: KeyReductionPolicy
    enabled: bool
    input_digest: str
    schema_id: str = INPUT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != INPUT_SCHEMA or self.input_kind not in {"ms32_baseline", "event_cleanup"}:
            raise KeyReductionPlanError("input schema or kind is unsupported")
        if type(self.source_binding) is not dict or type(self.upstream_plan) is not dict or type(self.protection_binding) is not dict:
            raise KeyReductionPlanError("input bindings must be objects")
        if type(self.upstream_requirements) is not tuple or any(type(row) is not dict for row in self.upstream_requirements):
            raise KeyReductionPlanError("upstream_requirements must be a tuple of objects")
        object.__setattr__(self, "source_binding", _copy_json_object(self.source_binding, "source_binding"))
        object.__setattr__(self, "upstream_plan", _copy_json_object(self.upstream_plan, "upstream_plan"))
        object.__setattr__(
            self,
            "upstream_requirements",
            tuple(_copy_json_object(row, "upstream_requirements") for row in self.upstream_requirements),
        )
        object.__setattr__(self, "protection_binding", _copy_json_object(self.protection_binding, "protection_binding"))
        if type(self.points) is not tuple or any(not isinstance(item, ReductionPoint) for item in self.points):
            raise KeyReductionPlanError("input points are invalid")
        point_keys = [(item.frame_no, item.semantic_morph) for item in self.points]
        ordered_keys = sorted(point_keys, key=lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1])))
        if point_keys != ordered_keys or len(point_keys) != len(set(point_keys)):
            raise KeyReductionPlanError("input points are duplicated or not in canonical order")
        _require_hash(self.upstream_wire_digest, "upstream_wire_digest")
        if _wire_digest(self.points) != self.upstream_wire_digest:
            raise KeyReductionPlanError("upstream wire digest does not match its points")
        if not isinstance(self.policy, KeyReductionPolicy) or type(self.enabled) is not bool:
            raise KeyReductionPlanError("input policy or enabled flag is invalid")
        self.validate_integrity()

    def validate_integrity(self) -> None:
        if not isinstance(self.policy, KeyReductionPolicy):
            raise KeyReductionPlanError("input policy is invalid")
        self.policy.validate_integrity()
        _require_hash(self.upstream_wire_digest, "upstream_wire_digest")
        if _wire_digest(self.points) != self.upstream_wire_digest:
            raise KeyReductionPlanError("upstream wire digest does not match its points")
        _require_hash(self.input_digest, "input_digest")
        if _digest(self._payload(include_digest=False)) != self.input_digest:
            raise KeyReductionPlanError("input digest does not match its content")

    def _payload(self, *, include_digest: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_id": self.schema_id,
            "input_kind": self.input_kind,
            "source_binding": _copy_json_object(self.source_binding, "source_binding"),
            "upstream_plan": _copy_json_object(self.upstream_plan, "upstream_plan"),
            "upstream_requirements": [_copy_json_object(row, "upstream_requirements") for row in self.upstream_requirements],
            "points": [item.to_dict() for item in self.points],
            "upstream_wire_digest": self.upstream_wire_digest,
            "protection_binding": _copy_json_object(self.protection_binding, "protection_binding"),
            "policy": self.policy.to_dict(),
            "enabled": self.enabled,
        }
        if include_digest:
            value["input_digest"] = self.input_digest
        return value

    def to_dict(self) -> dict[str, object]:
        return self._payload()

    @classmethod
    def create(
        cls, *, input_kind: str, source_binding: Mapping[str, object], upstream_plan: Mapping[str, object],
        upstream_requirements: tuple[dict[str, object], ...], points: tuple[ReductionPoint, ...],
        protection_binding: Mapping[str, object], policy: KeyReductionPolicy, enabled: bool,
    ) -> "KeyReductionInput":
        copied_requirements = tuple(_copy_json_object(row, "upstream_requirements") for row in upstream_requirements)
        payload = {
            "schema_id": INPUT_SCHEMA,
            "input_kind": input_kind,
            "source_binding": _copy_json_object(dict(source_binding), "source_binding"),
            "upstream_plan": _copy_json_object(dict(upstream_plan), "upstream_plan"),
            "upstream_requirements": [_copy_json_object(row, "upstream_requirements") for row in copied_requirements],
            "points": [item.to_dict() for item in points],
            "upstream_wire_digest": _wire_digest(points),
            "protection_binding": _copy_json_object(dict(protection_binding), "protection_binding"),
            "policy": policy.to_dict(),
            "enabled": enabled,
        }
        return cls(
            input_kind=input_kind,
            source_binding=payload["source_binding"],
            upstream_plan=payload["upstream_plan"],
            upstream_requirements=copied_requirements,
            points=points,
            upstream_wire_digest=payload["upstream_wire_digest"],
            protection_binding=payload["protection_binding"],
            policy=policy,
            enabled=enabled,
            input_digest=_digest(payload),
        )


@dataclass(frozen=True, slots=True)
class FinalMorphKeyReductionPlan:
    identity: dict[str, object]
    input_kind: str
    input_digest: str
    upstream_plan: dict[str, object]
    upstream_requirements: tuple[dict[str, object], ...]
    input_points: tuple[ReductionPoint, ...]
    points: tuple[ReductionPoint, ...]
    removals: tuple[KeyRemoval, ...]
    retained_reasons: tuple[dict[str, object], ...]
    state: str
    issues: tuple[str, ...]
    semantic_digest: str
    wire_digest: str
    schema_id: str = PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != PLAN_SCHEMA or self.input_kind not in {"ms32_baseline", "event_cleanup"}:
            raise KeyReductionPlanError("plan schema or input kind is unsupported")
        if type(self.identity) is not dict or type(self.upstream_plan) is not dict:
            raise KeyReductionPlanError("plan identity or upstream plan is invalid")
        for name in ("input_digest", "semantic_digest", "wire_digest"):
            _require_hash(getattr(self, name), name)
        if type(self.upstream_requirements) is not tuple or any(type(row) is not dict for row in self.upstream_requirements):
            raise KeyReductionPlanError("plan requirements are invalid")
        if type(self.input_points) is not tuple or type(self.points) is not tuple or any(not isinstance(point, ReductionPoint) for point in (*self.input_points, *self.points)):
            raise KeyReductionPlanError("plan point records are invalid")
        for name, points in (("input", self.input_points), ("output", self.points)):
            keys = [(point.frame_no, point.semantic_morph) for point in points]
            ordered = sorted(keys, key=lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1])))
            if keys != ordered or len(keys) != len(set(keys)):
                raise KeyReductionPlanError(f"plan {name} points are duplicated or not canonical")
        if type(self.removals) is not tuple or any(not isinstance(item, KeyRemoval) for item in self.removals):
            raise KeyReductionPlanError("plan removal records are invalid")
        removal_keys = [item.point.key for item in self.removals]
        if removal_keys != sorted(removal_keys, key=lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1]))) or len(removal_keys) != len(set(removal_keys)):
            raise KeyReductionPlanError("plan removal records are duplicated or not canonical")
        if type(self.retained_reasons) is not tuple or any(type(row) is not dict for row in self.retained_reasons):
            raise KeyReductionPlanError("retained reasons are invalid")
        retained_keys: list[tuple[int, str]] = []
        for row in self.retained_reasons:
            key = row.get("key")
            if type(key) is not dict or set(key) != {"frame_no", "semantic_morph"}:
                raise KeyReductionPlanError("plan retained reason key is invalid")
            frame, morph = key["frame_no"], key["semantic_morph"]
            if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0 or morph not in SEMANTIC_VOWEL_ORDER:
                raise KeyReductionPlanError("plan retained reason key identity is invalid")
            retained_keys.append((frame, morph))
        if retained_keys != sorted(retained_keys, key=lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1]))) or len(retained_keys) != len(set(retained_keys)):
            raise KeyReductionPlanError("plan retained reason records are duplicated or not canonical")
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise KeyReductionPlanError("plan state is invalid")
        if type(self.issues) is not tuple or any(type(item) is not str for item in self.issues):
            raise KeyReductionPlanError("plan issues are invalid")
        if _digest(self._payload(include_digests=False)) != self.semantic_digest:
            raise KeyReductionPlanError("plan semantic digest does not match its content")
        if _wire_digest(self.points) != self.wire_digest:
            raise KeyReductionPlanError("plan wire digest does not match its points")

    def _payload(self, *, include_digests: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_id": self.schema_id,
            "identity": self.identity,
            "input_kind": self.input_kind,
            "input_digest": self.input_digest,
            "upstream_plan": self.upstream_plan,
            "upstream_requirements": list(self.upstream_requirements),
            "input_points": [item.to_dict() for item in self.input_points],
            "points": [item.to_dict() for item in self.points],
            "removals": [item.to_dict() for item in self.removals],
            "retained_reasons": list(self.retained_reasons),
            "state": self.state,
            "issues": list(self.issues),
        }
        if include_digests:
            value["semantic_digest"] = self.semantic_digest
            value["wire_digest"] = self.wire_digest
        return value

    def to_dict(self) -> dict[str, object]:
        return self._payload()

    @classmethod
    def create(
        cls, *, identity: Mapping[str, object], input_snapshot: KeyReductionInput,
        points: tuple[ReductionPoint, ...], removals: tuple[KeyRemoval, ...],
        retained_reasons: tuple[dict[str, object], ...], state: str, issues: tuple[str, ...],
    ) -> "FinalMorphKeyReductionPlan":
        copied_identity = _copy_json_object(dict(identity), "identity")
        copied_upstream = _copy_json_object(input_snapshot.upstream_plan, "upstream_plan")
        wire_digest = _wire_digest(points)
        payload = {
            "schema_id": PLAN_SCHEMA,
            "identity": copied_identity,
            "input_kind": input_snapshot.input_kind,
            "input_digest": input_snapshot.input_digest,
            "upstream_plan": copied_upstream,
            "upstream_requirements": list(input_snapshot.upstream_requirements),
            "input_points": [item.to_dict() for item in input_snapshot.points],
            "points": [item.to_dict() for item in points],
            "removals": [item.to_dict() for item in removals],
            "retained_reasons": list(retained_reasons),
            "state": state,
            "issues": list(issues),
        }
        return cls(
            identity=copied_identity,
            input_kind=input_snapshot.input_kind,
            input_digest=input_snapshot.input_digest,
            upstream_plan=copied_upstream,
            upstream_requirements=input_snapshot.upstream_requirements,
            input_points=input_snapshot.points,
            points=points,
            removals=removals,
            retained_reasons=retained_reasons,
            state=state,
            issues=issues,
            semantic_digest=_digest(payload),
            wire_digest=wire_digest,
        )


def _wire_digest(points: tuple[ReductionPoint, ...]) -> str:
    return _digest([
        {"frame_no": item.frame_no, "semantic_morph": item.semantic_morph, "output_morph_name": item.output_morph_name, "binary32_hex": item.canonical_value.binary32_hex}
        for item in points
    ])


def _validate_rational_proof(value: dict[str, str]) -> None:
    fields = {"expected_num", "expected_den", "observed_num", "observed_den"}
    if set(value) != fields or any(type(item) is not str for item in value.values()):
        raise KeyReductionPlanError("rational proof fields are invalid")
    parsed: dict[str, int] = {}
    for name, raw in value.items():
        try:
            number = int(raw)
        except ValueError as error:
            raise KeyReductionPlanError("rational proof integer is invalid") from error
        if str(number) != raw:
            raise KeyReductionPlanError("rational proof integer is not canonical")
        parsed[name] = number
    for prefix in ("expected", "observed"):
        numerator = parsed[f"{prefix}_num"]
        denominator = parsed[f"{prefix}_den"]
        if denominator <= 0 or Fraction(numerator, denominator).numerator != numerator or Fraction(numerator, denominator).denominator != denominator:
            raise KeyReductionPlanError("rational proof fraction is not normalized")
    if Fraction(parsed["expected_num"], parsed["expected_den"]) != Fraction(parsed["observed_num"], parsed["observed_den"]):
        raise KeyReductionPlanError("rational proof does not prove equality")


def read_key_reduction_input(value: object) -> KeyReductionInput:
    if type(value) is str:
        try:
            value = json.loads(value, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
        except (json.JSONDecodeError, KeyReductionPlanError) as error:
            raise KeyReductionPlanError("serialized key reduction input is invalid JSON") from error
    row = _strict_object(value, frozenset({
        "schema_id", "input_kind", "source_binding", "upstream_plan", "upstream_requirements",
        "points", "upstream_wire_digest", "protection_binding", "policy", "enabled", "input_digest",
    }), "key reduction input")
    policy_row = _strict_object(row["policy"], frozenset({
        "schema_id", "policy_id", "key_contract_digest", "protections", "curve_domains",
        "algorithm_id", "enabled", "policy_digest",
    }), "key reduction policy")
    if type(policy_row["protections"]) is not list or type(policy_row["curve_domains"]) is not list:
        raise KeyReductionPlanError("key reduction policy arrays are malformed")
    if type(row["upstream_requirements"]) is not list or any(type(item) is not dict for item in row["upstream_requirements"]):
        raise KeyReductionPlanError("key reduction input requirements are malformed")
    if type(row["points"]) is not list:
        raise KeyReductionPlanError("key reduction input points are malformed")
    policy = KeyReductionPolicy(
        policy_id=policy_row["policy_id"],
        key_contract_digest=policy_row["key_contract_digest"],
        protections=tuple(policy_row["protections"]),
        curve_domains=tuple(policy_row["curve_domains"]),
        algorithm_id=policy_row["algorithm_id"],
        enabled=policy_row["enabled"],
        policy_digest=policy_row["policy_digest"],
        schema_id=policy_row["schema_id"],
    )
    return KeyReductionInput(
        input_kind=row["input_kind"],
        source_binding=_copy_json_object(row["source_binding"], "source_binding"),
        upstream_plan=_copy_json_object(row["upstream_plan"], "upstream_plan"),
        upstream_requirements=tuple(row["upstream_requirements"]),
        points=tuple(ReductionPoint.from_dict(item) for item in row["points"]),
        upstream_wire_digest=row["upstream_wire_digest"],
        protection_binding=_copy_json_object(row["protection_binding"], "protection_binding"),
        policy=policy,
        enabled=row["enabled"],
        input_digest=row["input_digest"],
        schema_id=row["schema_id"],
    )


def read_final_morph_key_reduction_plan(value: object) -> FinalMorphKeyReductionPlan:
    if type(value) is str:
        try:
            value = json.loads(value, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
        except (json.JSONDecodeError, KeyReductionPlanError) as error:
            raise KeyReductionPlanError("serialized key reduction plan is invalid JSON") from error
    row = _strict_object(value, frozenset({
        "schema_id", "identity", "input_kind", "input_digest", "upstream_plan", "upstream_requirements",
        "input_points", "points", "removals", "retained_reasons", "state", "issues", "semantic_digest", "wire_digest",
    }), "key reduction plan")
    if type(row["upstream_requirements"]) is not list or type(row["input_points"]) is not list or type(row["points"]) is not list or type(row["removals"]) is not list or type(row["retained_reasons"]) is not list or type(row["issues"]) is not list:
        raise KeyReductionPlanError("key reduction plan arrays are malformed")
    removals: list[KeyRemoval] = []
    for removal in row["removals"]:
        item = _strict_object(removal, frozenset({"key", "original_point", "reason", "left_anchor", "right_anchor", "scalar_proof", "wire_proof", "source_ids", "policy_digest"}), "key removal")
        key = _strict_object(item["key"], frozenset({"frame_no", "semantic_morph"}), "removal key")
        left = _strict_object(item["left_anchor"], frozenset({"frame_no", "semantic_morph"}), "left anchor")
        right = _strict_object(item["right_anchor"], frozenset({"frame_no", "semantic_morph"}), "right anchor")
        point = ReductionPoint.from_dict(item["original_point"])
        if key != {"frame_no": point.frame_no, "semantic_morph": point.semantic_morph} or item["source_ids"] != list(point.source_ids):
            raise KeyReductionPlanError("key removal identity differs from its point")
        removals.append(KeyRemoval(
            point=point, reason=item["reason"],
            left_anchor=(left["frame_no"], left["semantic_morph"]),
            right_anchor=(right["frame_no"], right["semantic_morph"]),
            scalar_proof=item["scalar_proof"], wire_proof=item["wire_proof"], policy_digest=item["policy_digest"],
        ))
    return FinalMorphKeyReductionPlan(
        identity=_copy_json_object(row["identity"], "identity"),
        input_kind=row["input_kind"], input_digest=row["input_digest"], upstream_plan=_copy_json_object(row["upstream_plan"], "upstream_plan"),
        upstream_requirements=tuple(row["upstream_requirements"]),
        input_points=tuple(ReductionPoint.from_dict(item) for item in row["input_points"]),
        points=tuple(ReductionPoint.from_dict(item) for item in row["points"]), removals=tuple(removals),
        retained_reasons=tuple(row["retained_reasons"]), state=row["state"], issues=tuple(row["issues"]),
        semantic_digest=row["semantic_digest"], wire_digest=row["wire_digest"], schema_id=row["schema_id"],
    )


def validate_final_morph_key_reduction_plan_integrity(plan: FinalMorphKeyReductionPlan) -> None:
    if not isinstance(plan, FinalMorphKeyReductionPlan):
        raise KeyReductionPlanError("key reduction plan is invalid")
    # Construction recomputes both digests and validates all nested records.
    FinalMorphKeyReductionPlan(
        identity=plan.identity, input_kind=plan.input_kind, input_digest=plan.input_digest,
        upstream_plan=plan.upstream_plan, upstream_requirements=plan.upstream_requirements,
        input_points=plan.input_points, points=plan.points, removals=plan.removals,
        retained_reasons=plan.retained_reasons, state=plan.state, issues=plan.issues,
        semantic_digest=plan.semantic_digest, wire_digest=plan.wire_digest,
    )


__all__ = [
    "FinalMorphKeyReductionPlan", "INPUT_SCHEMA", "KeyReductionInput", "KeyReductionPlanError",
    "KeyReductionPolicy", "KeyRemoval", "PLAN_SCHEMA", "POLICY_SCHEMA", "ReductionPoint",
    "read_final_morph_key_reduction_plan", "read_key_reduction_input", "validate_final_morph_key_reduction_plan_integrity",
]
