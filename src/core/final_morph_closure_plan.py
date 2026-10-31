from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, fields, is_dataclass
from typing import Any

try:
    from src.core.canonical_morph_value import CanonicalMorphValue
    from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.canonical_morph_value", "src.core.morph_name_sets"}:
        raise
    from core.canonical_morph_value import CanonicalMorphValue
    from core.morph_name_sets import SEMANTIC_VOWEL_ORDER


SCHEMA_ID = "final-morph-closure-plan/v1"
CLOSURE_POLICY_ID = "ms31-per-morph-closure/v2"
CURVE_POLICY_ID = "ms31-piecewise-linear-closed-domain/v1"
NUMERIC_POLICY_ID = "legacy-compatible-q10000/v1"
STAGES = (
    "issuer_admission",
    "requirement_derivation",
    "legacy_candidate_binding",
    "automatic_shape_reresolution",
    "closure_zero_materialization",
    "collision_resolution",
    "numeric_canonicalization",
    "independent_validation",
)
ISSUE_REASONS = frozenset(
    {
        "input_invalid",
        "provenance_missing",
        "capture_unavailable",
        "collision_unresolved",
        "required_zero_missing",
        "silence_core_violation",
        "terminal_evidence_missing",
        "protected_change_unexplained",
        "numeric_invalid",
        "wire_unrepresentable",
        "mapping_invalid",
        "identity_mismatch",
        "baseline_mismatch",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class ClosurePlanError(ValueError):
    pass


def _require_text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise ClosurePlanError(f"{name} must be non-empty text")
    return value


def _require_int(value: object, name: str, *, maximum: int = 0xFFFFFFFF) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ClosurePlanError(f"{name} must be an integer in the supported frame range")
    return value


def _require_hash(value: object, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ClosurePlanError(f"{name} must be a lowercase sha256 digest")
    return value


def _unique_text(values: object, name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ClosurePlanError(f"{name} must be a tuple")
    items = tuple(_require_text(item, f"{name} item") for item in values)
    if items != tuple(sorted(set(items))):
        raise ClosurePlanError(f"{name} must be sorted and unique")
    return items


@dataclass(frozen=True, slots=True)
class ClosureContract:
    schema_id: str = SCHEMA_ID
    closure_policy_id: str = CLOSURE_POLICY_ID
    curve_policy_id: str = CURVE_POLICY_ID
    numeric_policy_id: str = NUMERIC_POLICY_ID

    def __post_init__(self) -> None:
        if self.schema_id != SCHEMA_ID:
            raise ClosurePlanError("closure schema is unsupported")
        if self.closure_policy_id != CLOSURE_POLICY_ID:
            raise ClosurePlanError("closure policy is unsupported")
        if self.curve_policy_id != CURVE_POLICY_ID:
            raise ClosurePlanError("curve policy is unsupported")
        if self.numeric_policy_id != NUMERIC_POLICY_ID:
            raise ClosurePlanError("numeric policy is unsupported")

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical_json(_dataclass_payload(self)).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ClosureIdentityContext:
    source_run_id: str
    analysis_generation: int
    manual_revision: int
    base_plan_digest: str
    adjustment_snapshot_digest: str
    effective_plan_digest: str
    baseline_digest: str
    resolved_profile_id: str | None
    output_mapping: tuple[tuple[str, str], ...]
    numeric_policy_id: str
    silence_policy_id: str
    crossfade_policy_id: str
    closure_policy_id: str
    contract_digest: str

    def __post_init__(self) -> None:
        _require_text(self.source_run_id, "source_run_id")
        _require_int(self.analysis_generation, "analysis_generation")
        _require_int(self.manual_revision, "manual_revision")
        for name in ("base_plan_digest", "adjustment_snapshot_digest", "effective_plan_digest", "baseline_digest", "contract_digest"):
            _require_hash(getattr(self, name), name)
        if self.resolved_profile_id is not None:
            _require_text(self.resolved_profile_id, "resolved_profile_id")
        if not isinstance(self.output_mapping, tuple) or len(self.output_mapping) != len(SEMANTIC_VOWEL_ORDER):
            raise ClosurePlanError("output_mapping must define every semantic vowel")
        semantics: list[str] = []
        names: list[str] = []
        for item in self.output_mapping:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ClosurePlanError("output_mapping entries must be pairs")
            semantic, output_name = item
            _require_text(semantic, "output_mapping semantic")
            _require_text(output_name, "output_mapping name")
            semantics.append(semantic)
            names.append(output_name)
        if tuple(semantics) != SEMANTIC_VOWEL_ORDER or len(set(names)) != len(names):
            raise ClosurePlanError("output_mapping semantic order or names are invalid")
        if self.resolved_profile_id is None and tuple(names) != SEMANTIC_VOWEL_ORDER:
            raise ClosurePlanError("no-profile identity must use Japanese output names")
        for name in ("numeric_policy_id", "silence_policy_id", "crossfade_policy_id", "closure_policy_id"):
            _require_text(getattr(self, name), name)
        if self.numeric_policy_id != NUMERIC_POLICY_ID or self.closure_policy_id != CLOSURE_POLICY_ID:
            raise ClosurePlanError("identity policy is unsupported")


@dataclass(frozen=True, slots=True)
class ClosureRequirement:
    requirement_id: str
    kind: str
    semantic_morph: str
    start_frame: int
    end_frame: int
    endpoint_policy: str
    source_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.requirement_id, "requirement_id")
        if self.kind not in {"per_morph_closure", "silence_core", "required_zero"}:
            raise ClosurePlanError("requirement kind is unsupported")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosurePlanError("requirement semantic morph is unsupported")
        _require_int(self.start_frame, "start_frame")
        _require_int(self.end_frame, "end_frame")
        if self.end_frame < self.start_frame:
            raise ClosurePlanError("requirement range is reversed")
        if self.endpoint_policy not in {"closed_exact_zero", "explicit_key_exact_zero"}:
            raise ClosurePlanError("requirement endpoint policy is unsupported")
        _unique_text(self.source_ids, "source_ids")
        _require_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class ClosureTransformation:
    transformation_id: str
    stage: str
    ordinal: int
    operation: str
    semantic_morph: str | None
    frame_no: int | None
    before_value_hex: str | None
    after_value_hex: str | None
    source_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    protection_status: str

    def __post_init__(self) -> None:
        _require_text(self.transformation_id, "transformation_id")
        if self.stage not in STAGES[1:]:
            raise ClosurePlanError("transformation stage is unsupported")
        _require_int(self.ordinal, "ordinal", maximum=0x7FFFFFFF)
        _require_text(self.operation, "operation")
        if self.semantic_morph is not None and self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosurePlanError("transformation semantic morph is unsupported")
        if self.frame_no is not None:
            _require_int(self.frame_no, "frame_no")
        for name in ("before_value_hex", "after_value_hex"):
            value = getattr(self, name)
            if value is not None:
                try:
                    scalar = float.fromhex(value)
                except (TypeError, ValueError, OverflowError) as error:
                    raise ClosurePlanError(f"{name} must be a canonical float.hex string") from error
                if not math.isfinite(scalar) or scalar.hex() != value:
                    raise ClosurePlanError(f"{name} must be a canonical finite float.hex string")
        _unique_text(self.source_ids, "source_ids")
        _unique_text(self.requirement_ids, "requirement_ids")
        _require_text(self.protection_status, "protection_status")


@dataclass(frozen=True, slots=True)
class ClosureRestriction:
    restriction_id: str
    semantic_morph: str
    frame_no: int
    requested_value_hex: str
    effective_value_hex: str
    reason: str
    source_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.restriction_id, "restriction_id")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosurePlanError("restriction semantic morph is unsupported")
        _require_int(self.frame_no, "frame_no")
        for name in ("requested_value_hex", "effective_value_hex"):
            value = getattr(self, name)
            try:
                scalar = float.fromhex(value)
            except (TypeError, ValueError, OverflowError) as error:
                raise ClosurePlanError(f"{name} must be a canonical float.hex string") from error
            if not math.isfinite(scalar) or scalar.hex() != value:
                raise ClosurePlanError(f"{name} must be a canonical finite float.hex string")
        _require_text(self.reason, "reason")
        _unique_text(self.source_ids, "source_ids")


@dataclass(frozen=True, slots=True)
class ClosureIssue:
    reason_code: str
    stage: str
    detail: str
    semantic_morph: str | None = None
    frame_range: tuple[int, int] | None = None
    source_ids: tuple[str, ...] = ()
    requirement_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.reason_code not in ISSUE_REASONS:
            raise ClosurePlanError("issue reason is unsupported")
        _require_text(self.stage, "issue stage")
        _require_text(self.detail, "issue detail")
        if self.semantic_morph is not None and self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosurePlanError("issue semantic morph is unsupported")
        if self.frame_range is not None:
            if not isinstance(self.frame_range, tuple) or len(self.frame_range) != 2:
                raise ClosurePlanError("frame_range must be a pair")
            _require_int(self.frame_range[0], "frame range start")
            _require_int(self.frame_range[1], "frame range end")
            if self.frame_range[1] < self.frame_range[0]:
                raise ClosurePlanError("issue frame range is reversed")
        _unique_text(self.source_ids, "source_ids")
        _unique_text(self.requirement_ids, "requirement_ids")


@dataclass(frozen=True, slots=True)
class ClosurePoint:
    point_id: str
    record_id: str
    frame_no: int
    semantic_morph: str
    value: CanonicalMorphValue
    source_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    origin: str
    point_kinds: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.point_id, "point_id")
        _require_text(self.record_id, "record_id")
        _require_int(self.frame_no, "frame_no")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosurePlanError("point semantic morph is unsupported")
        if not isinstance(self.value, CanonicalMorphValue):
            raise ClosurePlanError("point value must be CanonicalMorphValue")
        _unique_text(self.source_ids, "source_ids")
        _unique_text(self.requirement_ids, "requirement_ids")
        if self.origin not in {"automatic", "manual", "unknown", "mixed"}:
            raise ClosurePlanError("point origin is unsupported")
        _unique_text(self.point_kinds, "point_kinds")


@dataclass(frozen=True, slots=True)
class ClosurePlan:
    schema_id: str
    contract: ClosureContract
    identity_context: ClosureIdentityContext
    state: str
    requirements: tuple[ClosureRequirement, ...]
    transformations: tuple[ClosureTransformation, ...]
    restrictions: tuple[ClosureRestriction, ...]
    points: tuple[ClosurePoint, ...]
    issues: tuple[ClosureIssue, ...]
    semantic_digest: str
    wire_digest: str

    def __post_init__(self) -> None:
        if self.schema_id != SCHEMA_ID or not isinstance(self.contract, ClosureContract):
            raise ClosurePlanError("plan schema or contract is invalid")
        if not isinstance(self.identity_context, ClosureIdentityContext):
            raise ClosurePlanError("identity_context is invalid")
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise ClosurePlanError("plan state is unsupported")
        for name, kind in (
            ("requirements", ClosureRequirement),
            ("transformations", ClosureTransformation),
            ("restrictions", ClosureRestriction),
            ("points", ClosurePoint),
            ("issues", ClosureIssue),
        ):
            value = getattr(self, name)
            if not isinstance(value, tuple) or any(not isinstance(item, kind) for item in value):
                raise ClosurePlanError(f"{name} contains an invalid value")
        _require_hash(self.semantic_digest, "semantic_digest")
        _require_hash(self.wire_digest, "wire_digest")
        if self.identity_context.contract_digest != self.contract.digest:
            raise ClosurePlanError("identity contract digest does not match contract")
        keys = [(point.frame_no, point.semantic_morph) for point in self.points]
        if keys != sorted(keys, key=lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1]))):
            raise ClosurePlanError("plan points are not in canonical order")
        if len(keys) != len(set(keys)):
            raise ClosurePlanError("plan points contain duplicate semantic keys")
        requirement_order = {"per_morph_closure": 0, "silence_core": 1, "required_zero": 2}
        expected_requirements = tuple(sorted(self.requirements, key=lambda item: (requirement_order[item.kind], SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.start_frame, item.end_frame, item.requirement_id)))
        if self.requirements != expected_requirements:
            raise ClosurePlanError("requirements are not in canonical order")
        if len({item.requirement_id for item in self.requirements}) != len(self.requirements):
            raise ClosurePlanError("requirement IDs are not unique")
        stage_indices = [STAGES.index(item.stage) for item in self.transformations]
        if stage_indices != sorted(stage_indices):
            raise ClosurePlanError("transformations do not follow the fixed stage order")
        for stage in STAGES[1:]:
            stage_items = tuple(item for item in self.transformations if item.stage == stage)
            if not stage_items or tuple(item.ordinal for item in stage_items) != tuple(range(len(stage_items))):
                raise ClosurePlanError("every transformation stage needs contiguous ordered records")
        if len({item.transformation_id for item in self.transformations}) != len(self.transformations):
            raise ClosurePlanError("transformation IDs are not unique")
        restriction_order = tuple(sorted(self.restrictions, key=lambda item: (SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.frame_no, item.restriction_id)))
        if self.restrictions != restriction_order or len({item.restriction_id for item in self.restrictions}) != len(self.restrictions):
            raise ClosurePlanError("restrictions are not canonical or unique")
        issue_order = tuple(sorted(self.issues, key=lambda item: (STAGES.index(item.stage) if item.stage in STAGES else len(STAGES), item.reason_code, item.semantic_morph or "", item.frame_range or (-1, -1), item.detail)))
        if self.issues != issue_order:
            raise ClosurePlanError("issues are not in canonical order")

    def to_dict(self, *, include_digests: bool = True) -> dict[str, Any]:
        payload = _plan_payload(self, include_digests=include_digests)
        return payload

    def to_json(self) -> str:
        validate_closure_plan_integrity(self)
        return _canonical_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class ClosureBuildResult:
    state: str
    plan: ClosurePlan | None
    issues: tuple[ClosureIssue, ...]

    def __post_init__(self) -> None:
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise ClosurePlanError("result state is unsupported")
        if self.plan is not None and not isinstance(self.plan, ClosurePlan):
            raise ClosurePlanError("result plan is invalid")
        if not isinstance(self.issues, tuple) or any(not isinstance(item, ClosureIssue) for item in self.issues):
            raise ClosurePlanError("result issues are invalid")
        if self.plan is not None and self.plan.state != self.state:
            raise ClosurePlanError("result state differs from its plan")


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _dataclass_payload(value: object) -> Any:
    if isinstance(value, CanonicalMorphValue):
        return value.to_dict()
    if is_dataclass(value):
        return {item.name: _dataclass_payload(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple):
        return [_dataclass_payload(item) for item in value]
    if isinstance(value, list):
        return [_dataclass_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _dataclass_payload(value[key]) for key in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ClosurePlanError("payload contains a non-finite float")
        return {"binary64": value.hex()}
    return value


def _plan_payload(plan: ClosurePlan, *, include_digests: bool) -> dict[str, Any]:
    result = {
        "schema_id": plan.schema_id,
        "contract": _dataclass_payload(plan.contract),
        "identity_context": _dataclass_payload(plan.identity_context),
        "state": plan.state,
        "requirements": _dataclass_payload(plan.requirements),
        "transformations": _dataclass_payload(plan.transformations),
        "restrictions": _dataclass_payload(plan.restrictions),
        "points": _dataclass_payload(plan.points),
        "issues": _dataclass_payload(plan.issues),
    }
    if include_digests:
        result["semantic_digest"] = plan.semantic_digest
        result["wire_digest"] = plan.wire_digest
    return result


def _wire_digest(points: tuple[ClosurePoint, ...], mapping: tuple[tuple[str, str], ...]) -> str:
    names = dict(mapping)
    payload = [
        [names[point.semantic_morph], point.frame_no, point.value.binary32_hex]
        for point in points
    ]
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def closure_wire_digest(points: tuple[ClosurePoint, ...], mapping: tuple[tuple[str, str], ...]) -> str:
    return _wire_digest(points, mapping)


def create_closure_plan(
    *,
    contract: ClosureContract,
    identity_context: ClosureIdentityContext,
    state: str,
    requirements: tuple[ClosureRequirement, ...],
    transformations: tuple[ClosureTransformation, ...],
    restrictions: tuple[ClosureRestriction, ...],
    points: tuple[ClosurePoint, ...],
    issues: tuple[ClosureIssue, ...],
) -> ClosurePlan:
    ordered_points = tuple(sorted(points, key=lambda item: (item.frame_no, SEMANTIC_VOWEL_ORDER.index(item.semantic_morph))))
    requirement_order = {"per_morph_closure": 0, "silence_core": 1, "required_zero": 2}
    ordered_requirements = tuple(sorted(requirements, key=lambda item: (requirement_order[item.kind], SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.start_frame, item.end_frame, item.requirement_id)))
    ordered_transformations = tuple(sorted(transformations, key=lambda item: (STAGES.index(item.stage), item.ordinal)))
    ordered_restrictions = tuple(sorted(restrictions, key=lambda item: (SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.frame_no, item.restriction_id)))
    ordered_issues = tuple(sorted(issues, key=lambda item: (STAGES.index(item.stage) if item.stage in STAGES else len(STAGES), item.reason_code, item.semantic_morph or "", item.frame_range or (-1, -1), item.detail)))
    provisional = ClosurePlan(
        SCHEMA_ID,
        contract,
        identity_context,
        state,
        ordered_requirements,
        ordered_transformations,
        ordered_restrictions,
        ordered_points,
        ordered_issues,
        "0" * 64,
        "0" * 64,
    )
    semantic = hashlib.sha256(_canonical_json(_plan_payload(provisional, include_digests=False)).encode("utf-8")).hexdigest()
    wire = _wire_digest(ordered_points, identity_context.output_mapping)
    return ClosurePlan(
        SCHEMA_ID,
        contract,
        identity_context,
        state,
        ordered_requirements,
        ordered_transformations,
        ordered_restrictions,
        ordered_points,
        ordered_issues,
        semantic,
        wire,
    )


def validate_closure_plan_integrity(plan: ClosurePlan) -> None:
    if not isinstance(plan, ClosurePlan):
        raise ClosurePlanError("closure plan is invalid")
    semantic = hashlib.sha256(_canonical_json(_plan_payload(plan, include_digests=False)).encode("utf-8")).hexdigest()
    if semantic != plan.semantic_digest:
        raise ClosurePlanError("semantic digest does not match plan payload")
    if _wire_digest(plan.points, plan.identity_context.output_mapping) != plan.wire_digest:
        raise ClosurePlanError("wire digest does not match plan points")


def _strict_object(value: object, fields_set: set[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields_set:
        raise ClosurePlanError(f"{name} has missing or unknown fields")
    return value


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ClosurePlanError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def closure_plan_from_json(value: str) -> ClosurePlan:
    try:
        payload = json.loads(value, object_pairs_hook=_reject_duplicate_pairs, parse_constant=lambda item: (_ for _ in ()).throw(ClosurePlanError(f"invalid number: {item}")))
    except (json.JSONDecodeError, TypeError) as error:
        raise ClosurePlanError("closure plan JSON is invalid") from error
    root = _strict_object(payload, {"schema_id", "contract", "identity_context", "state", "requirements", "transformations", "restrictions", "points", "issues", "semantic_digest", "wire_digest"}, "plan")
    contract_data = _strict_object(root["contract"], {"schema_id", "closure_policy_id", "curve_policy_id", "numeric_policy_id"}, "contract")
    contract = ClosureContract(**contract_data)
    identity_data = _strict_object(root["identity_context"], {"source_run_id", "analysis_generation", "manual_revision", "base_plan_digest", "adjustment_snapshot_digest", "effective_plan_digest", "baseline_digest", "resolved_profile_id", "output_mapping", "numeric_policy_id", "silence_policy_id", "crossfade_policy_id", "closure_policy_id", "contract_digest"}, "identity_context")
    identity_data["output_mapping"] = tuple(tuple(item) for item in identity_data["output_mapping"])
    identity = ClosureIdentityContext(**identity_data)
    requirements = tuple(ClosureRequirement(**{**_strict_object(item, {"requirement_id", "kind", "semantic_morph", "start_frame", "end_frame", "endpoint_policy", "source_ids", "reason"}, "requirement"), "source_ids": tuple(item["source_ids"])}) for item in root["requirements"])
    transformations = tuple(ClosureTransformation(**{**_strict_object(item, {"transformation_id", "stage", "ordinal", "operation", "semantic_morph", "frame_no", "before_value_hex", "after_value_hex", "source_ids", "requirement_ids", "protection_status"}, "transformation"), "source_ids": tuple(item["source_ids"]), "requirement_ids": tuple(item["requirement_ids"])}) for item in root["transformations"])
    restrictions = tuple(ClosureRestriction(**{**_strict_object(item, {"restriction_id", "semantic_morph", "frame_no", "requested_value_hex", "effective_value_hex", "reason", "source_ids"}, "restriction"), "source_ids": tuple(item["source_ids"])}) for item in root["restrictions"])
    issues = tuple(ClosureIssue(**{**_strict_object(item, {"reason_code", "stage", "detail", "semantic_morph", "frame_range", "source_ids", "requirement_ids"}, "issue"), "frame_range": None if item["frame_range"] is None else tuple(item["frame_range"]), "source_ids": tuple(item["source_ids"]), "requirement_ids": tuple(item["requirement_ids"])}) for item in root["issues"])
    points: list[ClosurePoint] = []
    for item_obj in root["points"]:
        item = _strict_object(item_obj, {"point_id", "record_id", "frame_no", "semantic_morph", "value", "source_ids", "requirement_ids", "origin", "point_kinds"}, "point")
        value_data = item["value"]
        points.append(ClosurePoint(
            point_id=item["point_id"], record_id=item["record_id"], frame_no=item["frame_no"], semantic_morph=item["semantic_morph"],
            value=CanonicalMorphValue.from_dict(value_data), source_ids=tuple(item["source_ids"]), requirement_ids=tuple(item["requirement_ids"]), origin=item["origin"], point_kinds=tuple(item["point_kinds"]),
        ))
    plan = ClosurePlan(
        schema_id=root["schema_id"], contract=contract, identity_context=identity, state=root["state"], requirements=requirements,
        transformations=transformations, restrictions=restrictions, points=tuple(points), issues=issues,
        semantic_digest=root["semantic_digest"], wire_digest=root["wire_digest"],
    )
    validate_closure_plan_integrity(plan)
    if plan.to_json() != value:
        raise ClosurePlanError("closure plan JSON is not canonical")
    return plan


__all__ = [
    "CLOSURE_POLICY_ID", "CURVE_POLICY_ID", "NUMERIC_POLICY_ID", "SCHEMA_ID", "STAGES", "ClosureBuildResult",
    "ClosureContract", "ClosureIdentityContext", "ClosureIssue", "ClosurePlan", "ClosurePlanError", "ClosurePoint",
    "ClosureRequirement", "ClosureRestriction", "ClosureTransformation", "closure_plan_from_json", "create_closure_plan",
    "closure_wire_digest", "validate_closure_plan_integrity",
]
