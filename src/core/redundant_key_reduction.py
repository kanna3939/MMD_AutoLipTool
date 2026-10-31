"""Exact, conservative reduction of redundant saved morph keys for MS33-B3."""
from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

from src.core.final_morph_key_reduction_plan import (
    FinalMorphKeyReductionPlan,
    KeyReductionInput,
    KeyReductionPlanError,
    KeyRemoval,
    ReductionPoint,
    validate_final_morph_key_reduction_plan_integrity,
)
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER


@dataclass(frozen=True, slots=True)
class KeyReductionResolution:
    input_digest: str
    points: tuple[ReductionPoint, ...]
    removals: tuple[KeyRemoval, ...]
    retained_reasons: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class KeyReductionValidationResult:
    state: str
    issues: tuple[str, ...]
    curve_checks: tuple[dict[str, object], ...]
    requirement_checks: tuple[dict[str, object], ...]
    removal_checks: tuple[dict[str, object], ...]
    protected_keys: tuple[tuple[int, str], ...]


@dataclass(frozen=True, slots=True)
class _CurveColumn:
    points: tuple[ReductionPoint, ...]
    frames: tuple[int, ...]
    canonical_values: tuple[Fraction, ...]
    saved_values: tuple[Fraction, ...]
    frame_indices: Mapping[int, int]

    def value(self, frame: int, domain: str) -> Fraction | None:
        if not self.frames or frame < self.frames[0] or frame > self.frames[-1]:
            return None
        values = self._values_for_domain(domain)
        index = bisect_left(self.frames, frame)
        if index < len(self.frames) and self.frames[index] == frame:
            return values[index]
        left_index = index - 1
        right_index = index
        ratio = Fraction(
            frame - self.frames[left_index],
            self.frames[right_index] - self.frames[left_index],
        )
        return values[left_index] + (values[right_index] - values[left_index]) * ratio

    def point_at(self, frame: int) -> ReductionPoint | None:
        index = self.frame_indices.get(frame)
        return None if index is None else self.points[index]

    def _values_for_domain(self, domain: str) -> tuple[Fraction, ...]:
        if domain == "canonical_binary64":
            return self.canonical_values
        if domain == "saved_binary32":
            return self.saved_values
        raise KeyReductionPlanError("unsupported curve domain")


@dataclass(frozen=True, slots=True)
class _CurveIndex:
    columns: Mapping[str, _CurveColumn]

    @classmethod
    def from_points(cls, points: tuple[ReductionPoint, ...]) -> _CurveIndex:
        grouped: dict[str, list[ReductionPoint]] = {
            morph: [] for morph in SEMANTIC_VOWEL_ORDER
        }
        for point in points:
            grouped[point.semantic_morph].append(point)
        columns = {
            morph: _CurveColumn(
                points=tuple(column),
                frames=tuple(point.frame_no for point in column),
                canonical_values=tuple(
                    Fraction.from_float(point.canonical_value.scalar)
                    for point in column
                ),
                saved_values=tuple(
                    Fraction.from_float(point.wire_value) for point in column
                ),
                frame_indices={
                    point.frame_no: index for index, point in enumerate(column)
                },
            )
            for morph, column in grouped.items()
        }
        return cls(columns)


def _key_order(key: tuple[int, str]) -> tuple[int, int]:
    return (key[0], SEMANTIC_VOWEL_ORDER.index(key[1]))


def _point_map(points: tuple[ReductionPoint, ...]) -> dict[tuple[int, str], ReductionPoint]:
    result: dict[tuple[int, str], ReductionPoint] = {}
    for point in points:
        if point.key in result:
            raise KeyReductionPlanError(f"duplicate reduction key: {point.key}")
        result[point.key] = point
    return result


def _validate_point_order(points: tuple[ReductionPoint, ...]) -> None:
    keys = [point.key for point in points]
    if keys != sorted(keys, key=_key_order):
        raise KeyReductionPlanError("reduction points are not in canonical frame and morph order")
    for morph in SEMANTIC_VOWEL_ORDER:
        frames = [point.frame_no for point in points if point.semantic_morph == morph]
        if frames != sorted(set(frames)):
            raise KeyReductionPlanError(f"{morph} points are not strictly ordered by frame")


def _protection_reasons(snapshot: KeyReductionInput) -> dict[tuple[int, str], tuple[str, ...]]:
    binding = snapshot.protection_binding
    if binding.get("schema_id") != "ms33-b3-protection-binding/v1":
        raise KeyReductionPlanError("protection binding schema is invalid")
    rows = binding.get("protected_keys")
    if type(rows) is not list:
        raise KeyReductionPlanError("protected_keys must be an array")
    points_by_key = _point_map(snapshot.points)
    result: dict[tuple[int, str], set[str]] = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"frame_no", "semantic_morph", "source_record_ids", "reasons"}:
            raise KeyReductionPlanError("protected key record has an invalid field set")
        frame = row["frame_no"]
        morph = row["semantic_morph"]
        ids = row["source_record_ids"]
        reasons = row["reasons"]
        if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0 or morph not in SEMANTIC_VOWEL_ORDER:
            raise KeyReductionPlanError("protected key identity is invalid")
        if type(ids) is not list or any(type(item) is not str or not item for item in ids):
            raise KeyReductionPlanError("protected key source IDs are invalid")
        if type(reasons) is not list or any(type(item) is not str or not item for item in reasons) or reasons != sorted(set(reasons)):
            raise KeyReductionPlanError("protected key reasons are invalid")
        if not reasons:
            raise KeyReductionPlanError("protected key needs at least one reason")
        key = (frame, morph)
        point = points_by_key.get(key)
        if point is None or ids != list(point.source_record_ids) or key in result:
            raise KeyReductionPlanError("protected key does not uniquely bind its source records")
        result[key] = set(reasons)
    return {key: tuple(sorted(values)) for key, values in result.items()}


def _intrinsic_protections(snapshot: KeyReductionInput) -> dict[tuple[int, str], tuple[str, ...]]:
    explicit = _protection_reasons(snapshot)
    points = snapshot.points
    by_morph: dict[str, list[ReductionPoint]] = {morph: [] for morph in SEMANTIC_VOWEL_ORDER}
    for point in points:
        by_morph[point.semantic_morph].append(point)
    reasons: dict[tuple[int, str], set[str]] = {key: set(value) for key, value in explicit.items()}
    for morph, column in by_morph.items():
        if column:
            reasons.setdefault(column[0].key, set()).add("first_key")
            reasons.setdefault(column[-1].key, set()).add("last_key")
    for point in points:
        key = point.key
        if point.requirement_ids:
            reasons.setdefault(key, set()).add("upstream_requirement")
        if point.intent_origins != ("automatic_event",) and point.intent_origins != ("automatic",):
            reasons.setdefault(key, set()).add("manual_or_unresolved_origin")
        if not point.source_record_ids:
            reasons.setdefault(key, set()).add("source_record_unresolved")
        if not point.source_ids:
            reasons.setdefault(key, set()).add("source_owner_unresolved")
        lowered = " ".join(point.point_kinds).casefold()
        if any(token in lowered for token in ("boundary", "terminal", "required_zero", "start_zero", "end_zero", "closure")):
            reasons.setdefault(key, set()).add("boundary_or_required_zero_role")
    return {key: tuple(sorted(value)) for key, value in reasons.items() if value}


def _fraction_value(point: ReductionPoint, domain: str) -> Fraction:
    if domain == "canonical_binary64":
        return Fraction.from_float(point.canonical_value.scalar)
    if domain == "saved_binary32":
        return Fraction.from_float(point.wire_value)
    raise KeyReductionPlanError("unsupported curve domain")


def _collinear(left: ReductionPoint, middle: ReductionPoint, right: ReductionPoint, domain: str) -> bool:
    left_value = _fraction_value(left, domain)
    middle_value = _fraction_value(middle, domain)
    right_value = _fraction_value(right, domain)
    return (middle_value - left_value) * (right.frame_no - left.frame_no) == (right_value - left_value) * (middle.frame_no - left.frame_no)


def _rational_proof(left: ReductionPoint, middle: ReductionPoint, right: ReductionPoint, domain: str) -> dict[str, str]:
    left_value = _fraction_value(left, domain)
    middle_value = _fraction_value(middle, domain)
    right_value = _fraction_value(right, domain)
    ratio = Fraction(middle.frame_no - left.frame_no, right.frame_no - left.frame_no)
    expected = left_value + (right_value - left_value) * ratio
    return {
        "expected_num": str(expected.numerator),
        "expected_den": str(expected.denominator),
        "observed_num": str(middle_value.numerator),
        "observed_den": str(middle_value.denominator),
    }


def _validator_value_fraction(point: ReductionPoint, domain: str) -> Fraction:
    """Decode proof operands independently from the reducer's curve helper."""
    if domain == "canonical_binary64":
        value = point.canonical_value.scalar
    elif domain == "saved_binary32":
        value = Fraction.from_float(point.wire_value)
        return value
    else:
        raise KeyReductionPlanError("unsupported curve domain")
    return Fraction.from_float(value)


def _validator_collinear(left: ReductionPoint, middle: ReductionPoint, right: ReductionPoint, domain: str) -> bool:
    left_value = _validator_value_fraction(left, domain)
    middle_value = _validator_value_fraction(middle, domain)
    right_value = _validator_value_fraction(right, domain)
    frame_span = right.frame_no - left.frame_no
    middle_offset = middle.frame_no - left.frame_no
    return (middle_value - left_value) * frame_span == (right_value - left_value) * middle_offset


def _validator_rational_proof(left: ReductionPoint, middle: ReductionPoint, right: ReductionPoint, domain: str) -> dict[str, str]:
    left_value = _validator_value_fraction(left, domain)
    middle_value = _validator_value_fraction(middle, domain)
    right_value = _validator_value_fraction(right, domain)
    frame_span = right.frame_no - left.frame_no
    middle_offset = middle.frame_no - left.frame_no
    expected = left_value + (right_value - left_value) * Fraction(middle_offset, frame_span)
    return {
        "expected_num": str(expected.numerator),
        "expected_den": str(expected.denominator),
        "observed_num": str(middle_value.numerator),
        "observed_den": str(middle_value.denominator),
    }


def resolve_redundant_keys(input_snapshot: KeyReductionInput) -> KeyReductionResolution:
    """Remove only unprotected interior keys exactly collinear in both domains."""
    if not isinstance(input_snapshot, KeyReductionInput):
        raise KeyReductionPlanError("input snapshot type is invalid")
    input_snapshot.validate_integrity()
    _validate_point_order(input_snapshot.points)
    protection = _intrinsic_protections(input_snapshot)
    output: list[ReductionPoint] = []
    removed: list[ReductionPoint] = []
    retained: list[dict[str, object]] = []
    for morph in SEMANTIC_VOWEL_ORDER:
        column = [point for point in input_snapshot.points if point.semantic_morph == morph]
        stack: list[ReductionPoint] = []
        for point in column:
            stack.append(point)
            while len(stack) >= 3:
                left, middle, right = stack[-3:]
                reasons = protection.get(middle.key, ())
                if reasons or not input_snapshot.enabled:
                    break
                scalar_equal = _collinear(left, middle, right, "canonical_binary64")
                wire_equal = _collinear(left, middle, right, "saved_binary32")
                if not (scalar_equal and wire_equal):
                    break
                removed.append(stack.pop(-2))
        output.extend(stack)
    output = sorted(output, key=lambda item: _key_order(item.key))
    removed_by_key = {point.key: point for point in removed}
    final_by_morph: dict[str, list[ReductionPoint]] = {morph: [] for morph in SEMANTIC_VOWEL_ORDER}
    for point in output:
        final_by_morph[point.semantic_morph].append(point)
    for point in input_snapshot.points:
        if point.key in removed_by_key:
            continue
        reasons = list(protection.get(point.key, ()))
        if not reasons:
            if not input_snapshot.enabled:
                reasons.append("reduction_disabled")
            else:
                column = final_by_morph[point.semantic_morph]
                index = column.index(point)
                if index == 0 or index == len(column) - 1:
                    reasons.append("curve_endpoint")
                else:
                    left, right = column[index - 1], column[index + 1]
                    scalar_equal = _collinear(left, point, right, "canonical_binary64")
                    wire_equal = _collinear(left, point, right, "saved_binary32")
                    if scalar_equal != wire_equal:
                        reasons.append("numeric_domain_disagreement")
                    elif not scalar_equal:
                        reasons.append("non_collinear")
                    else:
                        raise KeyReductionPlanError("reducer left an eligible exact-collinear point")
        retained.append({
            "key": {"frame_no": point.frame_no, "semantic_morph": point.semantic_morph},
            "reasons": sorted(set(reasons)),
        })
    removals: list[KeyRemoval] = []
    for point in sorted(removed, key=lambda item: _key_order(item.key)):
        neighbors = final_by_morph[point.semantic_morph]
        lefts = [item for item in neighbors if item.frame_no < point.frame_no]
        rights = [item for item in neighbors if item.frame_no > point.frame_no]
        if not lefts or not rights:
            raise KeyReductionPlanError("removed point has no final retained anchors")
        left, right = lefts[-1], rights[0]
        removals.append(KeyRemoval(
            point=point,
            reason="exact_collinear",
            left_anchor=left.key,
            right_anchor=right.key,
            scalar_proof=_rational_proof(left, point, right, "canonical_binary64"),
            wire_proof=_rational_proof(left, point, right, "saved_binary32"),
            policy_digest=input_snapshot.policy.policy_digest,
        ))
    return KeyReductionResolution(input_snapshot.input_digest, tuple(output), tuple(removals), tuple(retained))


def build_key_reduction_candidate(
    issuer: KeyReductionInput, resolution: KeyReductionResolution,
) -> FinalMorphKeyReductionPlan:
    if isinstance(issuer, KeyReductionInput):
        issuer.validate_integrity()
    if not isinstance(issuer, KeyReductionInput) or resolution.input_digest != issuer.input_digest:
        raise KeyReductionPlanError("resolution is not bound to this key reduction input")
    identity = {
        "source_binding": issuer.source_binding,
        "input_digest": issuer.input_digest,
        "policy_digest": issuer.policy.policy_digest,
        "protection_binding_digest": _json_digest(issuer.protection_binding),
        "enabled": issuer.enabled,
    }
    return FinalMorphKeyReductionPlan.create(
        identity=identity,
        input_snapshot=issuer,
        points=resolution.points,
        removals=resolution.removals,
        retained_reasons=resolution.retained_reasons,
        state="valid",
        issues=(),
    )


def _json_digest(value: object) -> str:
    import hashlib
    import json
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _curve_value(index: _CurveIndex, morph: str, frame: int, domain: str) -> Fraction | None:
    column = index.columns.get(morph)
    return None if column is None else column.value(frame, domain)


def _verify_curve_equality(
    before: _CurveIndex,
    after: _CurveIndex,
) -> tuple[list[dict[str, object]], list[str]]:
    checks: list[dict[str, object]] = []
    issues: list[str] = []
    for morph in SEMANTIC_VOWEL_ORDER:
        left = before.columns.get(morph)
        right = after.columns.get(morph)
        left_points = () if left is None else left.points
        right_points = () if right is None else right.points
        if not left_points and not right_points:
            checks.append({"semantic_morph": morph, "state": "equal", "breakpoints": 0})
            continue
        if (
            not left_points
            or not right_points
            or (left_points[0].frame_no, left_points[-1].frame_no)
            != (right_points[0].frame_no, right_points[-1].frame_no)
        ):
            issues.append(f"curve_domain_changed:{morph}")
            checks.append({"semantic_morph": morph, "state": "different_domain", "breakpoints": 0})
            continue
        breaks = sorted({*left.frames, *right.frames})
        for domain in ("canonical_binary64", "saved_binary32"):
            for frame in breaks:
                if _curve_value(before, morph, frame, domain) != _curve_value(after, morph, frame, domain):
                    issues.append(f"curve_value_changed:{morph}:{domain}:{frame}")
                    break
        checks.append({"semantic_morph": morph, "state": "equal" if not any(issue.startswith(f"curve_value_changed:{morph}:") for issue in issues) else "different", "breakpoints": len(breaks), "domains": ["canonical_binary64", "saved_binary32"]})
    return checks, issues


def _verify_requirements(
    curve_index: _CurveIndex,
    requirements: tuple[dict[str, object], ...],
    binding: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[str]]:
    checks: list[dict[str, object]] = []
    issues: list[str] = []
    intervals = list(binding.get("required_zero_intervals", []))
    for requirement in requirements:
        kind = requirement.get("kind")
        morph = requirement.get("semantic_morph")
        start, end = requirement.get("start_frame"), requirement.get("end_frame")
        if morph not in SEMANTIC_VOWEL_ORDER or any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)) or end < start:
            issues.append("upstream_requirement_malformed")
            continue
        intervals.append({"semantic_morph": morph, "start_frame": start, "end_frame": end, "reason": f"upstream:{requirement.get('requirement_id', kind)}"})
    seen: set[tuple[str, int, int, str]] = set()
    for row in intervals:
        morph, start, end, reason = row.get("semantic_morph"), row.get("start_frame"), row.get("end_frame"), row.get("reason")
        if morph not in SEMANTIC_VOWEL_ORDER or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (start, end)) or end < start or type(reason) is not str:
            issues.append("required_zero_interval_malformed")
            continue
        identity = (morph, start, end, reason)
        if identity in seen:
            continue
        seen.add(identity)
        start_value = _curve_value(curve_index, morph, start, "canonical_binary64")
        end_value = _curve_value(curve_index, morph, end, "canonical_binary64")
        wire_start_value = _curve_value(curve_index, morph, start, "saved_binary32")
        wire_end_value = _curve_value(curve_index, morph, end, "saved_binary32")
        explicit_required = reason.startswith("upstream:") and any(
            row.get("semantic_morph") == morph
            and row.get("start_frame") == start
            and row.get("end_frame") == end
            and (row.get("kind") == "required_zero" or row.get("endpoint_policy") == "explicit_key_exact_zero")
            for row in requirements if type(row) is dict
        )
        column = curve_index.columns.get(morph)
        start_point = None if column is None else column.point_at(start)
        end_point = None if column is None else column.point_at(end)
        zero = start_value == 0 and end_value == 0 and wire_start_value == 0 and wire_end_value == 0 and all(
            not start <= point.frame_no <= end
            or point.canonical_value.scalar == 0.0 and point.wire_value == 0.0
            for point in (() if column is None else column.points)
        )
        if explicit_required:
            zero = zero and start_point is not None and end_point is not None and start_point.canonical_value.scalar == 0.0 and end_point.canonical_value.scalar == 0.0 and start_point.wire_value == 0.0 and end_point.wire_value == 0.0
        if not zero:
            issues.append(f"required_zero_interval_changed:{morph}:{start}:{end}")
        checks.append({"semantic_morph": morph, "start_frame": start, "end_frame": end, "reason": reason, "state": "zero" if zero else "nonzero"})
    return checks, issues


def validate_key_reduction_plan(plan: FinalMorphKeyReductionPlan, issuer: KeyReductionInput) -> KeyReductionValidationResult:
    issues: list[str] = []
    curve_checks: list[dict[str, object]] = []
    requirement_checks: list[dict[str, object]] = []
    removal_checks: list[dict[str, object]] = []
    if not isinstance(plan, FinalMorphKeyReductionPlan) or not isinstance(issuer, KeyReductionInput):
        return KeyReductionValidationResult("invalid", ("plan_or_issuer_type_invalid",), (), (), (), ())
    try:
        validate_final_morph_key_reduction_plan_integrity(plan)
        issuer.validate_integrity()
        _validate_point_order(issuer.points)
        _validate_point_order(plan.points)
    except (KeyReductionPlanError, TypeError, ValueError):
        return KeyReductionValidationResult("invalid", ("plan_or_input_integrity_invalid",), (), (), (), ())
    expected_identity = {
        "source_binding": issuer.source_binding,
        "input_digest": issuer.input_digest,
        "policy_digest": issuer.policy.policy_digest,
        "protection_binding_digest": _json_digest(issuer.protection_binding),
        "enabled": issuer.enabled,
    }
    if plan.identity != expected_identity or plan.input_kind != issuer.input_kind or plan.input_digest != issuer.input_digest:
        issues.append("plan_identity_or_input_binding_mismatch")
    if plan.upstream_plan != issuer.upstream_plan or plan.upstream_requirements != issuer.upstream_requirements or plan.input_points != issuer.points:
        issues.append("upstream_or_input_snapshot_changed")
    try:
        protections = _intrinsic_protections(issuer)
        protected_keys = tuple(sorted(protections, key=_key_order))
    except (KeyReductionPlanError, TypeError, ValueError):
        protections = {}
        protected_keys = ()
        issues.append("protection_binding_invalid")
    original_curve_index = _CurveIndex.from_points(issuer.points)
    output_curve_index = _CurveIndex.from_points(plan.points)
    original_map: dict[tuple[int, str], ReductionPoint] = {}
    output_map: dict[tuple[int, str], ReductionPoint] = {}
    try:
        original_map = _point_map(issuer.points)
        output_map = _point_map(plan.points)
    except KeyReductionPlanError:
        issues.append("duplicate_key_identity")
    removed_keys = set(original_map) - set(output_map)
    added_keys = set(output_map) - set(original_map)
    if added_keys:
        issues.append("output_contains_inserted_keys")
    removal_keys = [item.point.key for item in plan.removals]
    if len(removal_keys) != len(set(removal_keys)) or removed_keys != set(removal_keys):
        issues.append("removal_set_does_not_match_key_difference")
    for key in set(original_map) & set(output_map):
        if original_map[key] != output_map[key]:
            issues.append(f"retained_point_changed:{key}")
    if removed_keys & set(protections):
        issues.append("protected_key_removed")
    curve_checks, curve_issues = _verify_curve_equality(
        original_curve_index,
        output_curve_index,
    )
    issues.extend(curve_issues)
    requirement_checks, requirement_issues = _verify_requirements(
        output_curve_index,
        issuer.upstream_requirements,
        issuer.protection_binding,
    )
    issues.extend(requirement_issues)
    for removal in plan.removals:
        key = removal.point.key
        left, right = output_map.get(removal.left_anchor), output_map.get(removal.right_anchor)
        source = original_map.get(key)
        valid = source == removal.point and left is not None and right is not None and left.semantic_morph == key[1] and right.semantic_morph == key[1] and left.frame_no < key[0] < right.frame_no and removal.policy_digest == issuer.policy.policy_digest and key not in protections
        if valid:
            valid = _validator_collinear(left, source, right, "canonical_binary64") and _validator_collinear(left, source, right, "saved_binary32")
            valid = valid and removal.scalar_proof == _validator_rational_proof(left, source, right, "canonical_binary64") and removal.wire_proof == _validator_rational_proof(left, source, right, "saved_binary32")
        if not valid:
            issues.append(f"removal_proof_invalid:{key}")
        removal_checks.append({"key": [key[0], key[1]], "state": "valid" if valid else "invalid"})
    if not issuer.enabled and (plan.points != issuer.points or plan.removals):
        issues.append("disabled_reduction_changed_input")
    retained_rows: dict[tuple[int, str], dict[str, object]] = {}
    try:
        for row in plan.retained_reasons:
            if type(row) is not dict or set(row) != {"key", "reasons"}:
                raise KeyReductionPlanError("retained reason record has an invalid field set")
            key_row = row["key"]
            if type(key_row) is not dict or set(key_row) != {"frame_no", "semantic_morph"}:
                raise KeyReductionPlanError("retained reason key is malformed")
            key = (key_row["frame_no"], key_row["semantic_morph"])
            reasons = row["reasons"]
            if key in retained_rows or type(reasons) is not list or not reasons or any(type(item) is not str or not item for item in reasons) or reasons != sorted(set(reasons)):
                raise KeyReductionPlanError("retained reason record is duplicated or empty")
            retained_rows[key] = row
        if set(retained_rows) != set(output_map):
            issues.append("retained_reason_set_does_not_match_output")
        for key, point in output_map.items():
            record = retained_rows.get(key)
            if record is None:
                continue
            actual_reasons = set(record["reasons"])
            protected_reasons = set(protections.get(key, ()))
            if protected_reasons:
                if actual_reasons != protected_reasons:
                    issues.append(f"protected_retention_reason_mismatch:{key}")
                continue
            if not issuer.enabled:
                expected_reasons = {"reduction_disabled"}
            else:
                column = output_curve_index.columns[point.semantic_morph]
                index = column.frame_indices[point.frame_no]
                if index == 0 or index == len(column.points) - 1:
                    expected_reasons = {"curve_endpoint"}
                else:
                    scalar_equal = _validator_collinear(column.points[index - 1], point, column.points[index + 1], "canonical_binary64")
                    wire_equal = _validator_collinear(column.points[index - 1], point, column.points[index + 1], "saved_binary32")
                    expected_reasons = {"numeric_domain_disagreement"} if scalar_equal != wire_equal else {"non_collinear"}
            if actual_reasons != expected_reasons:
                issues.append(f"retention_reason_mismatch:{key}")
    except (KeyReductionPlanError, KeyError, TypeError):
        issues.append("retained_reason_records_invalid")
    if issuer.enabled:
        # Independently reject any removable interior triple left in the output.
        for morph in SEMANTIC_VOWEL_ORDER:
            column = output_curve_index.columns[morph].points
            for left, middle, right in zip(column, column[1:], column[2:]):
                if middle.key not in protections and _validator_collinear(left, middle, right, "canonical_binary64") and _validator_collinear(left, middle, right, "saved_binary32"):
                    issues.append(f"reducible_key_retained:{middle.frame_no}:{morph}")
    state = "valid" if not issues and plan.state == "valid" and not plan.issues else "invalid"
    return KeyReductionValidationResult(state, tuple(dict.fromkeys(issues)), tuple(curve_checks), tuple(requirement_checks), tuple(removal_checks), protected_keys)


def reapply_key_reduction_plan(plan: FinalMorphKeyReductionPlan, issuer: KeyReductionInput) -> FinalMorphKeyReductionPlan:
    validation = validate_key_reduction_plan(plan, issuer)
    if validation.state != "valid":
        raise KeyReductionPlanError("cannot reapply an unverified key reduction plan")
    return plan


__all__ = [
    "KeyReductionResolution", "KeyReductionValidationResult", "build_key_reduction_candidate",
    "reapply_key_reduction_plan", "resolve_redundant_keys", "validate_key_reduction_plan",
]
