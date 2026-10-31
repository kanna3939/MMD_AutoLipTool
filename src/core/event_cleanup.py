"""MS33-B2 conservative event contribution cleanup policy and independent checks."""
from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from src.core.final_morph_cleanup_plan import (
    CleanupChange,
    CleanupDecision,
    CleanupPlanError,
    CleanupPoint,
    FinalMorphCleanupPlan,
    create_final_morph_cleanup_plan,
    validate_final_morph_cleanup_plan_integrity,
)


POLICY_SCHEMA = "event-cleanup-policy/v1"
_ALLOWED_ACTIONS = {"suppress_event", "protected_keep", "uncertain_keep", "out_of_scope", "disabled_keep"}
_SAFE_POINT_KINDS = {"start_zero", "top", "end_zero"}


class EventCleanupError(ValueError):
    """Raised for invalid policy or input bindings."""


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise EventCleanupError("cleanup data is not canonical JSON") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _required_text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise EventCleanupError(f"{name} must be non-empty text")
    return value


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise EventCleanupError(f"{name} must be a finite number")
    return float(value)


@dataclass(frozen=True, slots=True)
class CleanupParameter:
    name: str
    operator: str
    value: float
    unit: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "operator": self.operator, "value": self.value, "unit": self.unit}


@dataclass(frozen=True, slots=True)
class EventCleanupPolicy:
    contract_digest: str
    comparison_digest: str
    proposal_id: str
    parameters: tuple[CleanupParameter, ...]
    scope: str
    protections: tuple[str, ...]
    unknown_rules: tuple[str, ...]
    allowed_changes: tuple[dict[str, object], ...]
    real_cases: tuple[dict[str, object], ...]
    valid_low_controls: tuple[dict[str, object], ...]
    policy_digest: str
    schema_id: str = POLICY_SCHEMA

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "contract_digest": self.contract_digest,
            "comparison_digest": self.comparison_digest,
            "proposal_id": self.proposal_id,
            "parameters": [item.to_dict() for item in self.parameters],
            "scope": self.scope,
            "protections": list(self.protections),
            "unknown_rules": list(self.unknown_rules),
            "allowed_changes": [dict(item) for item in self.allowed_changes],
            "real_cases": [dict(item) for item in self.real_cases],
            "valid_low_controls": [dict(item) for item in self.valid_low_controls],
            "policy_digest": self.policy_digest,
        }

    def parameter_map(self) -> dict[str, CleanupParameter]:
        return {item.name: item for item in self.parameters}


def _policy_payload(*, contract_digest: str, comparison_digest: str, proposal_id: str, parameters: tuple[CleanupParameter, ...], scope: str, protections: tuple[str, ...], unknown_rules: tuple[str, ...], allowed_changes: tuple[dict[str, object], ...], real_cases: tuple[dict[str, object], ...], valid_low_controls: tuple[dict[str, object], ...]) -> dict[str, object]:
    return {
        "schema_id": POLICY_SCHEMA,
        "contract_digest": contract_digest,
        "comparison_digest": comparison_digest,
        "proposal_id": proposal_id,
        "parameters": [item.to_dict() for item in parameters],
        "scope": scope,
        "protections": list(protections),
        "unknown_rules": list(unknown_rules),
        "allowed_changes": list(allowed_changes),
        "real_cases": list(real_cases),
        "valid_low_controls": list(valid_low_controls),
    }


def build_event_cleanup_policy(contract: Mapping[str, object], *, contract_digest: str, comparison_digest: str) -> EventCleanupPolicy:
    """Freeze adopted B1 event fields without filling in missing policy values."""
    if type(contract) is not dict or contract.get("schema_id") != "ms33-b1-contract/v1":
        raise EventCleanupError("B1 contract schema is invalid")
    event = contract.get("event_contract")
    required = {"status", "comparison_ref", "proposal_id", "adopted_parameters", "scope", "real_cases", "valid_low_controls", "protection_rules", "unknown_rules", "allowed_changes", "independent_cases", "observations", "handoff", "missing"}
    if type(event) is not dict or set(event) != required or event.get("status") != "adopted":
        raise EventCleanupError("B1 event contract is incomplete or not adopted")
    _required_text(contract_digest, "contract_digest")
    _required_text(comparison_digest, "comparison_digest")
    parameters_value = event["adopted_parameters"]
    if type(parameters_value) is not list or not parameters_value:
        raise EventCleanupError("adopted_parameters must be a non-empty array")
    parameters: list[CleanupParameter] = []
    seen_names: set[str] = set()
    for item in parameters_value:
        if type(item) is not dict or not {"name", "operator", "value", "unit"}.issubset(item):
            raise EventCleanupError("B1 adopted parameter is malformed")
        name = _required_text(item["name"], "parameter.name")
        operator = _required_text(item["operator"], "parameter.operator")
        if operator != "<=" or name in seen_names:
            raise EventCleanupError("B1 event comparison operator or parameter name is unsupported")
        value = _finite_number(item["value"], f"parameter.{name}.value")
        parameters.append(CleanupParameter(name, operator, value, _required_text(item["unit"], f"parameter.{name}.unit")))
        seen_names.add(name)
    for name in ("real_cases", "valid_low_controls", "allowed_changes"):
        if type(event[name]) is not list:
            raise EventCleanupError(f"B1 {name} must be an array")
    for name in ("protection_rules", "unknown_rules"):
        if type(event[name]) is not list or any(type(item) is not str or not item.strip() for item in event[name]):
            raise EventCleanupError(f"B1 {name} must contain non-empty text")
    allowed_fields = {"semantic_morph", "frame_start", "frame_end", "reason"}
    for row in event["allowed_changes"]:
        if type(row) is not dict or set(row) != allowed_fields:
            raise EventCleanupError("B1 allowed_changes record is malformed")
        if row["semantic_morph"] not in {"あ", "い", "う", "え", "お"} or type(row["reason"]) is not str or not row["reason"].strip():
            raise EventCleanupError("B1 allowed_changes record has invalid text")
        for key in ("frame_start", "frame_end"):
            if isinstance(row[key], bool) or not isinstance(row[key], int) or row[key] < 0:
                raise EventCleanupError("B1 allowed_changes frame is invalid")
        if row["frame_start"] > row["frame_end"]:
            raise EventCleanupError("B1 allowed_changes interval is reversed")
    normalized_records: list[tuple[dict[str, object], ...]] = []
    for name in ("real_cases", "valid_low_controls"):
        rows: list[dict[str, object]] = []
        seen: set[str] = set()
        for row in event[name]:
            expected_fields = {"record_id", "case_id", "frame_no", "semantic_morph", "reason"}
            if type(row) is not dict or set(row) != expected_fields:
                raise EventCleanupError(f"B1 {name} record is malformed")
            record_id = _required_text(row["record_id"], f"{name}.record_id")
            _required_text(row["case_id"], f"{name}.case_id")
            _required_text(row["reason"], f"{name}.reason")
            if record_id in seen or row["semantic_morph"] not in {"あ", "い", "う", "え", "お"} or isinstance(row["frame_no"], bool) or not isinstance(row["frame_no"], int) or row["frame_no"] < 0:
                raise EventCleanupError(f"B1 {name} has duplicate or invalid record")
            seen.add(record_id)
            rows.append(dict(row))
        normalized_records.append(tuple(rows))
    parameters_tuple = tuple(parameters)
    allowed = tuple(dict(row) for row in event["allowed_changes"])
    payload = _policy_payload(
        contract_digest=contract_digest, comparison_digest=comparison_digest,
        proposal_id=_required_text(event["proposal_id"], "proposal_id"), parameters=parameters_tuple,
        scope=_required_text(event["scope"], "scope"), protections=tuple(event["protection_rules"]),
        unknown_rules=tuple(event["unknown_rules"]), allowed_changes=allowed,
        real_cases=normalized_records[0], valid_low_controls=normalized_records[1],
    )
    policy = EventCleanupPolicy(
        contract_digest, comparison_digest, event["proposal_id"], parameters_tuple, event["scope"],
        tuple(event["protection_rules"]), tuple(event["unknown_rules"]), allowed,
        normalized_records[0], normalized_records[1], _digest(payload),
    )
    validate_event_cleanup_policy(policy)
    return policy


def validate_event_cleanup_policy(policy: EventCleanupPolicy) -> None:
    if not isinstance(policy, EventCleanupPolicy) or policy.schema_id != POLICY_SCHEMA:
        raise EventCleanupError("cleanup policy schema or type is invalid")
    if not policy.contract_digest or not policy.comparison_digest or not policy.proposal_id or not policy.scope:
        raise EventCleanupError("cleanup policy identity is incomplete")
    supported_parameters = {"max_canonical_units", "max_duration_sec", "max_mean_rms"}
    if not policy.parameters or any(not isinstance(item, CleanupParameter) or item.name not in supported_parameters or item.operator != "<=" or not item.unit or not math.isfinite(item.value) for item in policy.parameters):
        raise EventCleanupError("cleanup policy contains an unsupported adopted parameter")
    if len({item.name for item in policy.parameters}) != len(policy.parameters):
        raise EventCleanupError("cleanup policy parameter names are duplicated")
    for name, rows in (("protections", policy.protections), ("unknown_rules", policy.unknown_rules)):
        if type(rows) is not tuple or any(type(item) is not str or not item.strip() for item in rows):
            raise EventCleanupError(f"cleanup policy {name} are malformed")
    for row in policy.allowed_changes:
        if type(row) is not dict or set(row) != {"semantic_morph", "frame_start", "frame_end", "reason"}:
            raise EventCleanupError("cleanup policy allowed_changes record is malformed")
        if row["semantic_morph"] not in {"あ", "い", "う", "え", "お"} or type(row["reason"]) is not str or not row["reason"].strip():
            raise EventCleanupError("cleanup policy allowed_changes text is invalid")
        start, end = row["frame_start"], row["frame_end"]
        if isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int) or start < 0 or end < start:
            raise EventCleanupError("cleanup policy allowed_changes interval is invalid")
    for name, rows in (("real_cases", policy.real_cases), ("valid_low_controls", policy.valid_low_controls)):
        if type(rows) is not tuple:
            raise EventCleanupError(f"cleanup policy {name} are malformed")
        seen: set[str] = set()
        for row in rows:
            fields = {"record_id", "case_id", "frame_no", "semantic_morph", "reason"}
            if type(row) is not dict or set(row) != fields:
                raise EventCleanupError(f"cleanup policy {name} record is malformed")
            record_id = row["record_id"]
            if type(record_id) is not str or not record_id or record_id in seen or type(row["case_id"]) is not str or not row["case_id"] or type(row["reason"]) is not str or not row["reason"].strip():
                raise EventCleanupError(f"cleanup policy {name} record identity is invalid")
            if row["semantic_morph"] not in {"あ", "い", "う", "え", "お"} or isinstance(row["frame_no"], bool) or not isinstance(row["frame_no"], int) or row["frame_no"] < 0:
                raise EventCleanupError(f"cleanup policy {name} record frame or morph is invalid")
            seen.add(record_id)
    payload = _policy_payload(
        contract_digest=policy.contract_digest,
        comparison_digest=policy.comparison_digest,
        proposal_id=policy.proposal_id,
        parameters=policy.parameters,
        scope=policy.scope,
        protections=policy.protections,
        unknown_rules=policy.unknown_rules,
        allowed_changes=policy.allowed_changes,
        real_cases=policy.real_cases,
        valid_low_controls=policy.valid_low_controls,
    )
    if _digest(payload) != policy.policy_digest:
        raise EventCleanupError("cleanup policy digest does not match its adopted fields")


@dataclass(frozen=True, slots=True)
class EventCleanupInput:
    case_id: str
    source_binding: dict[str, object]
    original_transition_plan: dict[str, object]
    original_requirements: tuple[dict[str, object], ...]
    original_points: tuple[CleanupPoint, ...]
    event_rows: tuple[dict[str, object], ...]
    control_rows: tuple[dict[str, object], ...]
    policy: EventCleanupPolicy
    enabled: bool = True
    input_digest: str = ""

    def __post_init__(self) -> None:
        _required_text(self.case_id, "case_id")
        if type(self.source_binding) is not dict or type(self.original_transition_plan) is not dict:
            raise EventCleanupError("source binding and original transition plan must be objects")
        if type(self.original_requirements) is not tuple or any(type(row) is not dict for row in self.original_requirements):
            raise EventCleanupError("original_requirements must be a tuple of objects")
        if type(self.original_points) is not tuple or not all(isinstance(item, CleanupPoint) for item in self.original_points):
            raise EventCleanupError("original_points must be a tuple of CleanupPoint")
        if type(self.event_rows) is not tuple or any(type(row) is not dict for row in self.event_rows):
            raise EventCleanupError("event_rows must be a tuple of objects")
        if type(self.control_rows) is not tuple or any(type(row) is not dict for row in self.control_rows):
            raise EventCleanupError("control_rows must be a tuple of objects")
        if type(self.enabled) is not bool:
            raise EventCleanupError("enabled must be a boolean")
        if not isinstance(self.policy, EventCleanupPolicy):
            raise EventCleanupError("policy type is invalid")

    def computed_digest(self) -> str:
        return _digest({
            "case_id": self.case_id,
            "source_binding": self.source_binding,
            "original_transition_plan": self.original_transition_plan,
            "original_requirements": list(self.original_requirements),
            "original_points": [item.to_dict() for item in self.original_points],
            "event_rows": list(self.event_rows),
            "control_rows": list(self.control_rows),
            "policy_digest": self.policy.policy_digest,
            "enabled": self.enabled,
        })


@dataclass(frozen=True, slots=True)
class CleanupResolution:
    input_digest: str
    decisions: tuple[CleanupDecision, ...]
    eligible_keys_by_event: tuple[tuple[str, tuple[tuple[int, str], ...]], ...]


@dataclass(frozen=True, slots=True)
class CleanupValidationResult:
    state: str
    issues: tuple[str, ...]
    suppression_checks: tuple[dict[str, object], ...]


def _record_real_case(event: Mapping[str, object], policy: EventCleanupPolicy) -> dict[str, object] | None:
    record_id = event.get("record_id")
    case_id = event.get("case_id")
    if type(case_id) is not str and type(record_id) is str and ":event:" in record_id:
        case_id = record_id.partition(":event:")[0]
    matches = [row for row in policy.real_cases if row.get("record_id") == record_id]
    if len(matches) != 1:
        return None
    row = matches[0]
    if row.get("case_id") != case_id or row.get("semantic_morph") != event.get("semantic_morph") or row.get("frame_no") != event.get("frame_no"):
        return None
    return row


def _metric_classification(event: Mapping[str, object], policy: EventCleanupPolicy) -> tuple[str, tuple[str, ...]]:
    protections = event.get("protection_reasons", [])
    uncertainties = event.get("uncertainty_reasons", [])
    if type(protections) is not list or type(uncertainties) is not list:
        return "uncertain_keep", ("invalid_protection_metadata",)
    if protections:
        return "protected_keep", tuple(str(item) for item in protections)
    if uncertainties:
        return "uncertain_keep", tuple(str(item) for item in uncertainties)
    values = event.get("values", {})
    timing = event.get("timing", {})
    acoustic = event.get("acoustic", {})
    values = values if type(values) is dict else {}
    timing = timing if type(timing) is dict else {}
    acoustic = acoustic if type(acoustic) is dict else {}
    evidence: list[str] = []
    parameters = policy.parameter_map()
    for parameter_name, raw_value, complete in (
        ("max_canonical_units", values.get("canonical_units"), True),
        ("max_duration_sec", timing.get("duration_sec"), True),
        ("max_mean_rms", acoustic.get("mean_rms"), acoustic.get("coverage_status") == "complete"),
    ):
        if parameter_name not in parameters:
            continue
        if raw_value is None or not complete:
            return "uncertain_keep", (f"metric_unavailable:{parameter_name}",)
        if parameter_name == "max_canonical_units" and (isinstance(raw_value, bool) or not isinstance(raw_value, int)):
            return "uncertain_keep", (f"metric_invalid:{parameter_name}",)
        try:
            measured = _finite_number(raw_value, parameter_name)
        except EventCleanupError:
            return "uncertain_keep", (f"metric_invalid:{parameter_name}",)
        if measured > parameters[parameter_name].value:
            return "uncertain_keep", (f"above_adopted_bound:{parameter_name}",)
        evidence.append(f"{parameter_name}<={parameters[parameter_name].value}")
    if not evidence:
        return "uncertain_keep", ("no_adopted_classifier_metrics",)
    return "removal_candidate", tuple(evidence)


def _event_control_points(event: Mapping[str, object], controls: tuple[dict[str, object], ...]) -> tuple[list[dict[str, object]], str | None]:
    indices = event.get("source_event_indices")
    if type(indices) is not list or len(indices) != 1 or isinstance(indices[0], bool) or not isinstance(indices[0], int):
        return [], "source_event_identity_not_singleton"
    source_index = indices[0]
    morph = event.get("semantic_morph")
    rows = [row for row in controls if row.get("semantic_morph") == morph and type(row.get("source_event_indices")) is list and source_index in row["source_event_indices"]]
    shape_ordinals = {row.get("shape_ordinal") for row in rows}
    if len(shape_ordinals) != 1 or None in shape_ordinals:
        return [], "shared_or_unresolved_shape"
    shape_ordinal = next(iter(shape_ordinals))
    shape_rows = [row for row in controls if row.get("shape_ordinal") == shape_ordinal and row.get("semantic_morph") == morph]
    if not shape_rows or any(row.get("source_event_indices") != [source_index] for row in shape_rows):
        return [], "shared_shape_keep"
    for row in shape_rows:
        kinds = row.get("point_kinds")
        origins = row.get("intent_origins")
        protections = row.get("protection_reasons")
        if type(kinds) is not list or not kinds or any(kind not in _SAFE_POINT_KINDS for kind in kinds):
            return [], "protected_role_keep"
        if type(origins) is not list or any(origin not in {"automatic_event"} for origin in origins):
            return [], "manual_or_unknown_origin_keep"
        if type(protections) is list and protections:
            return [], "upstream_protected_keep"
    zeros = [row for row in shape_rows if _row_wire_value(row) == 0.0 and set(row.get("point_kinds", [])) & {"start_zero", "end_zero"}]
    if len(zeros) < 2:
        return [], "shape_zero_boundaries_missing"
    if any(_row_wire_value(row) > 0.0 and set(row.get("point_kinds", [])) != {"top"} for row in shape_rows):
        return [], "non_top_positive_role_keep"
    return shape_rows, None


def _row_wire_value(row: Mapping[str, object]) -> float:
    values = row.get("values")
    canonical = values.get("canonical") if type(values) is dict else None
    raw = canonical.get("binary32_hex") if type(canonical) is dict else None
    if type(raw) is not str:
        return math.nan
    try:
        data = bytes.fromhex(raw)
        if len(data) != 4:
            return math.nan
        result = struct.unpack("<f", data)[0]
    except ValueError:
        return math.nan
    return result if math.isfinite(result) else math.nan


def _allowed_interval(event: Mapping[str, object], policy: EventCleanupPolicy) -> tuple[int, int] | None:
    morph = event.get("semantic_morph")
    start = event.get("timing", {}).get("start_frame") if type(event.get("timing")) is dict else None
    end = event.get("timing", {}).get("end_frame") if type(event.get("timing")) is dict else None
    if isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int):
        return None
    for row in policy.allowed_changes:
        if row["semantic_morph"] == morph and row["frame_start"] <= start and end <= row["frame_end"]:
            return row["frame_start"], row["frame_end"]
    return None


def _overlaps_valid_low_control(event: Mapping[str, object], keys: tuple[tuple[int, str], ...], policy: EventCleanupPolicy) -> bool:
    record_id = event.get("record_id")
    case_id = event.get("case_id")
    if type(case_id) is not str and type(record_id) is str and ":event:" in record_id:
        case_id = record_id.partition(":event:")[0]
    target_keys = set(keys)
    return any(
        row.get("case_id") == case_id
        and (row.get("frame_no"), row.get("semantic_morph")) in target_keys
        for row in policy.valid_low_controls
    )


def _derive_event_keys(event: Mapping[str, object], controls: tuple[dict[str, object], ...], original_points: tuple[CleanupPoint, ...], policy: EventCleanupPolicy) -> tuple[str | None, int | None, tuple[int, int] | None, tuple[tuple[int, str], ...], tuple[str, ...]]:
    real = _record_real_case(event, policy)
    if real is None:
        return "not_b1_adopted_event", None, None, (), ()
    classification, metric_evidence = _metric_classification(event, policy)
    if classification != "removal_candidate":
        return ",".join(metric_evidence) or classification, None, None, (), metric_evidence
    allowed_interval = _allowed_interval(event, policy)
    if allowed_interval is None:
        return "outside_adopted_frame_scope", None, None, (), metric_evidence
    shape_rows, reason = _event_control_points(event, controls)
    if reason is not None:
        return reason, None, None, (), metric_evidence
    source_index = event["source_event_indices"][0]
    morph = str(event["semantic_morph"])
    zeros = sorted(int(row["frame_no"]) for row in shape_rows if _row_wire_value(row) == 0.0 and set(row.get("point_kinds", [])) & {"start_zero", "end_zero"})
    interval = (zeros[0], zeros[-1])
    if interval[0] < allowed_interval[0] or interval[1] > allowed_interval[1]:
        return "influence_interval_outside_adopted_scope", None, interval, (), metric_evidence
    candidates = [point for point in original_points if point.semantic_morph == morph and interval[0] <= point.frame_no <= interval[1] and source_index in point.source_event_indices]
    if any(point.source_event_indices != (source_index,) for point in candidates):
        return "shared_morph_contribution_keep", None, interval, (), metric_evidence
    keys = tuple(sorted((point.frame_no, point.semantic_morph) for point in candidates if point.wire_value > 0.0))
    if not keys:
        return "no_positive_wire_contribution", None, interval, (), metric_evidence
    event_top_frames = {int(row["frame_no"]) for row in shape_rows if "top" in row.get("point_kinds", []) and _row_wire_value(row) > 0.0}
    if not {frame for frame, _ in keys}.issubset(event_top_frames):
        return "final_positive_key_not_owned_top", None, interval, (), metric_evidence
    if _overlaps_valid_low_control(event, keys, policy):
        return "valid_low_control_keep", None, interval, (), metric_evidence
    return None, next(iter({row["shape_ordinal"] for row in shape_rows})), interval, keys, metric_evidence


def resolve_event_cleanup(input_snapshot: EventCleanupInput) -> CleanupResolution:
    if not isinstance(input_snapshot, EventCleanupInput):
        raise EventCleanupError("event cleanup input is invalid")
    validate_event_cleanup_policy(input_snapshot.policy)
    input_digest = input_snapshot.computed_digest()
    if input_snapshot.input_digest and input_snapshot.input_digest != input_digest:
        raise EventCleanupError("event cleanup input digest mismatch")
    decisions: list[CleanupDecision] = []
    keys_by_event: list[tuple[str, tuple[tuple[int, str], ...]]] = []
    for event in sorted(input_snapshot.event_rows, key=lambda row: str(row.get("record_id", ""))):
        event_id = _required_text(event.get("record_id"), "event.record_id")
        indices = tuple(event.get("source_event_indices", ()))
        if not input_snapshot.enabled:
            action, reasons, shape, interval, keys, evidence = "disabled_keep", ("cleanup_disabled",), None, None, (), ()
        else:
            reason, shape, interval, keys, evidence = _derive_event_keys(event, input_snapshot.control_rows, input_snapshot.original_points, input_snapshot.policy)
            if reason is None:
                action, reasons = "suppress_event", ("b1_adopted_candidate_in_initial_safe_scope",)
                keys_by_event.append((event_id, keys))
            else:
                shape = None
                source_protection = event.get("protection_reasons")
                source_uncertainty = event.get("uncertainty_reasons")
                if type(source_protection) is list and source_protection:
                    action, reasons = "protected_keep", tuple(str(item) for item in source_protection)
                elif type(source_uncertainty) is list and source_uncertainty:
                    action, reasons = "uncertain_keep", tuple(str(item) for item in source_uncertainty)
                elif reason in {"shared_or_unresolved_shape", "shared_shape_keep", "shared_morph_contribution_keep", "protected_role_keep", "manual_or_unknown_origin_keep", "upstream_protected_keep", "shape_zero_boundaries_missing", "non_top_positive_role_keep", "final_positive_key_not_owned_top", "valid_low_control_keep"}:
                    action, reasons = "protected_keep", (reason,)
                elif reason.startswith("metric_unavailable") or reason.startswith("metric_invalid") or reason.startswith("above_adopted_bound") or reason == "no_adopted_classifier_metrics":
                    action, reasons = "uncertain_keep", (reason,)
                else:
                    action, reasons = "out_of_scope", (reason,)
                keys = ()
            if action != "suppress_event" and interval is None:
                interval = None
        decisions.append(CleanupDecision(event_id, indices, shape, action, reasons, tuple(evidence), interval, keys))
    return CleanupResolution(input_digest, tuple(decisions), tuple(keys_by_event))


def build_event_cleanup_candidate(issuer: EventCleanupInput, resolution: CleanupResolution) -> FinalMorphCleanupPlan:
    if not isinstance(issuer, EventCleanupInput) or not isinstance(resolution, CleanupResolution):
        raise EventCleanupError("cleanup issuer or resolution is invalid")
    validate_event_cleanup_policy(issuer.policy)
    expected_digest = issuer.computed_digest()
    if resolution.input_digest != expected_digest:
        raise EventCleanupError("cleanup resolution belongs to a different input")
    points_by_key = {(point.frame_no, point.semantic_morph): point for point in issuer.original_points}
    changed_keys: set[tuple[int, str]] = set()
    changes: list[CleanupChange] = []
    for decision in resolution.decisions:
        if decision.action != "suppress_event":
            continue
        for key in decision.changed_keys:
            if key in changed_keys or key not in points_by_key:
                raise EventCleanupError("cleanup resolution has duplicate or missing change keys")
            changed_keys.add(key)
            before = points_by_key[key]
            if before.wire_value <= 0.0:
                raise EventCleanupError("suppression target has no positive saved-wire contribution")
            changes.append(CleanupChange(
                event_id=decision.event_id, frame_no=before.frame_no, semantic_morph=before.semantic_morph,
                before_canonical=before.canonical_value, after_canonical=0.0,
                before_binary32_hex=before.binary32_hex, after_binary32_hex="00000000",
                reason="suppress complete isolated automatic event contribution",
                policy_digest=issuer.policy.policy_digest, source_ids=before.source_ids,
                requirement_ids=before.requirement_ids,
            ))
    candidate_points = tuple(
        CleanupPoint(
            point.frame_no, point.semantic_morph,
            0.0 if (point.frame_no, point.semantic_morph) in changed_keys else point.canonical_value,
            "00000000" if (point.frame_no, point.semantic_morph) in changed_keys else point.binary32_hex,
            0.0 if (point.frame_no, point.semantic_morph) in changed_keys else point.wire_value,
            point.source_ids, point.source_event_indices, point.point_kinds, point.intent_origins, point.requirement_ids, point.shape_ordinal,
        )
        for point in issuer.original_points
    )
    mapping = issuer.source_binding.get("output_mapping")
    if type(mapping) not in (list, tuple):
        raise EventCleanupError("source binding output_mapping is missing")
    identity = dict(issuer.source_binding)
    identity.update({"policy_digest": issuer.policy.policy_digest, "input_digest": expected_digest, "enabled": issuer.enabled, "output_mapping": mapping})
    return create_final_morph_cleanup_plan(
        identity=identity,
        original_transition_plan=issuer.original_transition_plan,
        original_requirements=issuer.original_requirements,
        decisions=resolution.decisions,
        points=candidate_points,
        changes=tuple(changes),
        state="valid",
        issues=(),
        output_mapping=mapping,
    )


def _evaluate_curve(points: tuple[CleanupPoint, ...], morph: str, frame: int) -> Fraction:
    curve = [point for point in points if point.semantic_morph == morph]
    if not curve or frame < curve[0].frame_no or frame > curve[-1].frame_no:
        raise EventCleanupError("required frame is outside the cleanup curve domain")
    for point in curve:
        if point.frame_no == frame:
            return Fraction.from_float(point.wire_value)
    for left, right in zip(curve, curve[1:]):
        if left.frame_no < frame < right.frame_no:
            ratio = Fraction(frame - left.frame_no, right.frame_no - left.frame_no)
            return Fraction.from_float(left.wire_value) + ratio * (Fraction.from_float(right.wire_value) - Fraction.from_float(left.wire_value))
    raise EventCleanupError("could not evaluate cleanup curve")


def _verify_requirements(points: tuple[CleanupPoint, ...], requirements: tuple[dict[str, object], ...]) -> list[str]:
    issues: list[str] = []
    for requirement in requirements:
        morph = requirement.get("semantic_morph")
        start = requirement.get("start_frame")
        end = requirement.get("end_frame")
        kind = requirement.get("kind")
        if morph not in {"あ", "い", "う", "え", "お"} or isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int) or start > end:
            issues.append("original_requirement_malformed")
            continue
        try:
            if kind == "required_zero":
                if _evaluate_curve(points, morph, start) != 0:
                    issues.append(f"required_zero_nonzero:{requirement.get('requirement_id')}")
                if requirement.get("endpoint_policy") == "explicit_key_exact_zero" and not any(point.semantic_morph == morph and point.frame_no == start and point.binary32_hex == "00000000" for point in points):
                    issues.append(f"required_zero_key_missing:{requirement.get('requirement_id')}")
            elif kind in {"per_morph_closure", "silence_core"}:
                if _evaluate_curve(points, morph, start) != 0 or _evaluate_curve(points, morph, end) != 0:
                    issues.append(f"zero_interval_boundary_nonzero:{requirement.get('requirement_id')}")
                if any(point.semantic_morph == morph and start <= point.frame_no <= end and point.wire_value != 0.0 for point in points):
                    issues.append(f"zero_interval_contains_positive_key:{requirement.get('requirement_id')}")
            else:
                issues.append(f"unknown_requirement_kind:{kind}")
        except EventCleanupError:
            issues.append(f"requirement_outside_wire_domain:{requirement.get('requirement_id')}")
    return issues


def _independent_expected(input_snapshot: EventCleanupInput) -> tuple[CleanupDecision, ...]:
    """Rebuild event eligibility without the producer's selection helpers."""
    parameters = {item.name: item for item in input_snapshot.policy.parameters}

    def saved_wire_value(row: Mapping[str, object]) -> float:
        values = row.get("values")
        canonical = values.get("canonical") if type(values) is dict else None
        encoded = canonical.get("binary32_hex") if type(canonical) is dict else None
        if type(encoded) is not str:
            return math.nan
        try:
            wire = bytes.fromhex(encoded)
            if len(wire) != 4:
                return math.nan
            decoded = struct.unpack("<f", wire)[0]
        except (ValueError, struct.error):
            return math.nan
        return decoded if math.isfinite(decoded) else math.nan

    def classify_from_source(event: Mapping[str, object]) -> tuple[str, tuple[str, ...]]:
        protections = event.get("protection_reasons", [])
        uncertainties = event.get("uncertainty_reasons", [])
        if type(protections) is not list or type(uncertainties) is not list:
            return "uncertain_keep", ("invalid_protection_metadata",)
        if protections:
            return "protected_keep", tuple(str(item) for item in protections)
        if uncertainties:
            return "uncertain_keep", tuple(str(item) for item in uncertainties)
        values = event.get("values")
        timing = event.get("timing")
        acoustic = event.get("acoustic")
        values = values if type(values) is dict else {}
        timing = timing if type(timing) is dict else {}
        acoustic = acoustic if type(acoustic) is dict else {}
        evidence: list[str] = []
        metrics = (
            ("max_canonical_units", values.get("canonical_units"), True),
            ("max_duration_sec", timing.get("duration_sec"), True),
            ("max_mean_rms", acoustic.get("mean_rms"), acoustic.get("coverage_status") == "complete"),
        )
        for name, raw, complete in metrics:
            parameter = parameters.get(name)
            if parameter is None:
                continue
            if raw is None or not complete:
                return "uncertain_keep", (f"metric_unavailable:{name}",)
            if name == "max_canonical_units" and (isinstance(raw, bool) or not isinstance(raw, int)):
                return "uncertain_keep", (f"metric_invalid:{name}",)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
                return "uncertain_keep", (f"metric_invalid:{name}",)
            if float(raw) > parameter.value:
                return "uncertain_keep", (f"above_adopted_bound:{name}",)
            evidence.append(f"{name}<={parameter.value}")
        if not evidence:
            return "uncertain_keep", ("no_adopted_classifier_metrics",)
        return "removal_candidate", tuple(evidence)

    def source_shape(event: Mapping[str, object]) -> tuple[list[dict[str, object]], str | None]:
        indices = event.get("source_event_indices")
        if type(indices) is not list or len(indices) != 1 or isinstance(indices[0], bool) or not isinstance(indices[0], int):
            return [], "source_event_identity_not_singleton"
        source_index = indices[0]
        morph = event.get("semantic_morph")
        owned = [
            row for row in input_snapshot.control_rows
            if row.get("semantic_morph") == morph
            and type(row.get("source_event_indices")) is list
            and source_index in row["source_event_indices"]
        ]
        ordinals = {row.get("shape_ordinal") for row in owned}
        if len(ordinals) != 1 or None in ordinals:
            return [], "shared_or_unresolved_shape"
        ordinal = next(iter(ordinals))
        shape = [
            row for row in input_snapshot.control_rows
            if row.get("shape_ordinal") == ordinal and row.get("semantic_morph") == morph
        ]
        if not shape or any(row.get("source_event_indices") != [source_index] for row in shape):
            return [], "shared_shape_keep"
        for row in shape:
            kinds = row.get("point_kinds")
            origins = row.get("intent_origins")
            protections = row.get("protection_reasons")
            if type(kinds) is not list or not kinds or any(kind not in _SAFE_POINT_KINDS for kind in kinds):
                return [], "protected_role_keep"
            if type(origins) is not list or any(origin not in {"automatic_event"} for origin in origins):
                return [], "manual_or_unknown_origin_keep"
            if type(protections) is list and protections:
                return [], "upstream_protected_keep"
        boundaries = [
            row for row in shape
            if saved_wire_value(row) == 0.0
            and set(row.get("point_kinds", [])) & {"start_zero", "end_zero"}
        ]
        if len(boundaries) < 2:
            return [], "shape_zero_boundaries_missing"
        if any(
            saved_wire_value(row) > 0.0 and set(row.get("point_kinds", [])) != {"top"}
            for row in shape
        ):
            return [], "non_top_positive_role_keep"
        return shape, None

    def adopted_interval(event: Mapping[str, object]) -> tuple[int, int] | None:
        timing = event.get("timing")
        timing = timing if type(timing) is dict else {}
        start = timing.get("start_frame")
        end = timing.get("end_frame")
        if isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int):
            return None
        for allowed in input_snapshot.policy.allowed_changes:
            if (
                allowed["semantic_morph"] == event.get("semantic_morph")
                and allowed["frame_start"] <= start
                and end <= allowed["frame_end"]
            ):
                return allowed["frame_start"], allowed["frame_end"]
        return None

    def has_valid_low_overlap(event: Mapping[str, object], keys: tuple[tuple[int, str], ...]) -> bool:
        record_id = event.get("record_id")
        case_id = event.get("case_id")
        if type(case_id) is not str and type(record_id) is str and ":event:" in record_id:
            case_id = record_id.partition(":event:")[0]
        selected = set(keys)
        return any(
            row.get("case_id") == case_id
            and (row.get("frame_no"), row.get("semantic_morph")) in selected
            for row in input_snapshot.policy.valid_low_controls
        )

    expected: list[CleanupDecision] = []
    for event in sorted(input_snapshot.event_rows, key=lambda row: str(row.get("record_id", ""))):
        event_id = str(event.get("record_id", ""))
        indices = tuple(event.get("source_event_indices", ()))
        if not input_snapshot.enabled:
            expected.append(CleanupDecision(event_id, indices, None, "disabled_keep", ("cleanup_disabled",), (), None, ()))
            continue
        # Re-derive using the adopted contract rows and full source metadata. This path
        # intentionally does not consume producer decisions or change records.
        event_case_id = event.get("case_id")
        if type(event_case_id) is not str and ":event:" in event_id:
            event_case_id = event_id.partition(":event:")[0]
        real_rows = [row for row in input_snapshot.policy.real_cases if row["record_id"] == event_id and row["case_id"] == event_case_id and row["semantic_morph"] == event.get("semantic_morph") and row["frame_no"] == event.get("frame_no")]
        if len(real_rows) != 1:
            protections = event.get("protection_reasons")
            if type(protections) is list and protections:
                expected.append(CleanupDecision(event_id, indices, None, "protected_keep", tuple(str(item) for item in protections), (), None, ()))
            elif type(event.get("uncertainty_reasons")) is list and event.get("uncertainty_reasons"):
                expected.append(CleanupDecision(event_id, indices, None, "uncertain_keep", tuple(str(item) for item in event["uncertainty_reasons"]), (), None, ()))
            else:
                expected.append(CleanupDecision(event_id, indices, None, "out_of_scope", ("not_b1_adopted_event",), (), None, ()))
            continue
        class_name, metric_evidence = classify_from_source(event)
        if class_name != "removal_candidate":
            protections = event.get("protection_reasons")
            uncertainties = event.get("uncertainty_reasons")
            if type(protections) is list and protections:
                action, reasons = "protected_keep", tuple(str(item) for item in protections)
            elif type(uncertainties) is list and uncertainties:
                action, reasons = "uncertain_keep", tuple(str(item) for item in uncertainties)
            elif metric_evidence[0] in {"protected_keep", "protected_role_keep", "manual_or_unknown_origin_keep", "upstream_protected_keep"}:
                action, reasons = "protected_keep", metric_evidence
            elif metric_evidence[0].startswith(("metric_unavailable", "metric_invalid", "above_adopted_bound")) or metric_evidence[0] == "no_adopted_classifier_metrics":
                action, reasons = "uncertain_keep", metric_evidence
            else:
                action, reasons = "out_of_scope", metric_evidence
            expected.append(CleanupDecision(event_id, indices, None, action, reasons, metric_evidence, None, ()))
            continue
        frame_range = adopted_interval(event)
        control_rows, control_issue = source_shape(event)
        if frame_range is None or control_issue is not None:
            reason = "outside_adopted_frame_scope" if frame_range is None else control_issue
            action = "protected_keep" if reason and ("shared" in reason or "protected" in reason or "manual" in reason or "zero_boundaries" in reason or "top_positive" in reason) else "out_of_scope"
            expected.append(CleanupDecision(event_id, indices, None, action, (str(reason),), metric_evidence, None, ()))
            continue
        source_index = indices[0]
        zeros = sorted(int(row["frame_no"]) for row in control_rows if saved_wire_value(row) == 0.0 and set(row.get("point_kinds", [])) & {"start_zero", "end_zero"})
        interval = (zeros[0], zeros[-1])
        if interval[0] < frame_range[0] or interval[1] > frame_range[1]:
            expected.append(CleanupDecision(event_id, indices, None, "out_of_scope", ("influence_interval_outside_adopted_scope",), metric_evidence, interval, ()))
            continue
        owned = [point for point in input_snapshot.original_points if point.semantic_morph == event.get("semantic_morph") and interval[0] <= point.frame_no <= interval[1] and source_index in point.source_event_indices]
        if any(point.source_event_indices != (source_index,) for point in owned):
            expected.append(CleanupDecision(event_id, indices, None, "protected_keep", ("shared_morph_contribution_keep",), metric_evidence, interval, ()))
            continue
        keys = tuple(sorted((point.frame_no, point.semantic_morph) for point in owned if point.wire_value > 0.0))
        if not keys:
            expected.append(CleanupDecision(event_id, indices, None, "out_of_scope", ("no_positive_wire_contribution",), metric_evidence, interval, ()))
            continue
        top_frames = {int(row["frame_no"]) for row in control_rows if "top" in row.get("point_kinds", []) and saved_wire_value(row) > 0.0}
        if not {frame for frame, _morph in keys}.issubset(top_frames):
            expected.append(CleanupDecision(event_id, indices, None, "protected_keep", ("final_positive_key_not_owned_top",), metric_evidence, interval, ()))
            continue
        if has_valid_low_overlap(event, keys):
            expected.append(CleanupDecision(event_id, indices, None, "protected_keep", ("valid_low_control_keep",), metric_evidence, interval, ()))
            continue
        shape_ordinal = control_rows[0].get("shape_ordinal")
        expected.append(CleanupDecision(event_id, indices, shape_ordinal, "suppress_event", ("b1_adopted_candidate_in_initial_safe_scope",), metric_evidence, interval, keys))
    return tuple(expected)


def validate_event_cleanup_plan(plan: FinalMorphCleanupPlan, issuer: EventCleanupInput) -> CleanupValidationResult:
    """Independently verify allowed keys, continuous saved curves and all original obligations."""
    issues: list[str] = []
    checks: list[dict[str, object]] = []
    if not isinstance(plan, FinalMorphCleanupPlan) or not isinstance(issuer, EventCleanupInput):
        return CleanupValidationResult("invalid", ("plan_or_issuer_type_invalid",), ())
    try:
        validate_event_cleanup_policy(issuer.policy)
    except EventCleanupError:
        return CleanupValidationResult("invalid", ("cleanup_policy_invalid",), ())
    try:
        validate_final_morph_cleanup_plan_integrity(plan)
    except CleanupPlanError:
        issues.append("plan_integrity_invalid")
    expected_input_digest = issuer.computed_digest()
    expected_identity = dict(issuer.source_binding)
    expected_mapping = issuer.source_binding.get("output_mapping")
    if type(expected_mapping) not in (list, tuple):
        issues.append("source_output_mapping_missing")
    expected_identity.update({
        "policy_digest": issuer.policy.policy_digest,
        "input_digest": expected_input_digest,
        "enabled": issuer.enabled,
        "output_mapping": expected_mapping,
    })
    if type(plan.identity) is not dict or plan.identity != expected_identity:
        issues.append("plan_identity_binding_mismatch")
    if plan.original_transition_plan != issuer.original_transition_plan or plan.original_requirements != issuer.original_requirements:
        issues.append("original_plan_or_requirements_changed")
    expected_decisions = _independent_expected(issuer)
    if plan.decisions != expected_decisions:
        issues.append("decision_does_not_match_independent_source_replay")
    original = {(point.frame_no, point.semantic_morph): point for point in issuer.original_points}
    candidate = {(point.frame_no, point.semantic_morph): point for point in plan.points}
    if set(original) != set(candidate):
        issues.append("key_set_or_frame_changed")
    changes_by_key: dict[tuple[int, str], list[CleanupChange]] = {}
    for change in plan.changes:
        changes_by_key.setdefault((change.frame_no, change.semantic_morph), []).append(change)
    expected_change_keys: set[tuple[int, str]] = set()
    for decision in expected_decisions:
        if decision.action != "suppress_event":
            continue
        p_e = set(decision.changed_keys)
        expected_change_keys.update(p_e)
        if not p_e:
            issues.append(f"suppression_without_target_keys:{decision.event_id}")
            continue
        witness = [original[key] for key in sorted(p_e) if key in original and original[key].wire_value > 0.0]
        if { (point.frame_no, point.semantic_morph) for point in witness } != p_e:
            issues.append(f"suppression_positive_witness_incomplete:{decision.event_id}")
            continue
        interval = decision.influence_interval
        event_row = next((row for row in issuer.event_rows if row.get("record_id") == decision.event_id), None)
        morph = event_row.get("semantic_morph") if type(event_row) is dict else None
        after_zero = interval is not None and type(morph) is str and _continuous_interval_zero(tuple(plan.points), morph, interval)
        actual = {key for key, rows in changes_by_key.items() if len(rows) == 1 and rows[0].event_id == decision.event_id}
        if actual != p_e or actual != {key for key in expected_change_keys if key in p_e}:
            issues.append(f"suppression_change_set_mismatch:{decision.event_id}")
        if not after_zero:
            issues.append(f"suppression_interval_not_zero:{decision.event_id}")
        for key in p_e:
            before = original.get(key)
            after = candidate.get(key)
            rows = changes_by_key.get(key, [])
            if before is None or after is None or len(rows) != 1:
                issues.append(f"suppression_change_record_missing:{decision.event_id}:{key}")
                continue
            change = rows[0]
            if (change.before_canonical != before.canonical_value or change.before_binary32_hex != before.binary32_hex or change.after_canonical != 0.0 or change.after_binary32_hex != "00000000" or change.policy_digest != issuer.policy.policy_digest or change.source_ids != before.source_ids or change.requirement_ids != before.requirement_ids):
                issues.append(f"suppression_change_record_mismatch:{decision.event_id}:{key}")
            if after.canonical_value != 0.0 or after.binary32_hex != "00000000" or after.wire_value != 0.0:
                issues.append(f"suppression_target_not_zero:{decision.event_id}:{key}")
        checks.append({"event_id": decision.event_id, "influence_interval": list(interval or ()), "expected_positive_keys": [[f, m] for f, m in sorted(p_e)], "actual_changed_keys": [[f, m] for f, m in sorted(actual)], "before_positive_witness": [{"frame_no": point.frame_no, "semantic_morph": point.semantic_morph, "binary32_hex": point.binary32_hex} for point in witness], "after_zero_verified": bool(after_zero)})
    if set(changes_by_key) != expected_change_keys or any(len(rows) != 1 for rows in changes_by_key.values()):
        issues.append("unrecorded_duplicate_or_extra_change")
    for key in set(original) & set(candidate):
        before, after = original[key], candidate[key]
        if key not in expected_change_keys:
            if before != after:
                issues.append(f"unauthorized_point_change:{key}")
        else:
            if after.frame_no != before.frame_no or after.semantic_morph != before.semantic_morph or after.source_ids != before.source_ids or after.source_event_indices != before.source_event_indices or after.point_kinds != before.point_kinds or after.intent_origins != before.intent_origins or after.requirement_ids != before.requirement_ids or after.shape_ordinal != before.shape_ordinal:
                issues.append(f"changed_point_metadata:{key}")
            if after.wire_value > before.wire_value:
                issues.append(f"candidate_value_increased:{key}")
    issues.extend(_verify_requirements(tuple(plan.points), issuer.original_requirements))
    state = "valid" if not issues and plan.state == "valid" and not plan.issues else "invalid"
    return CleanupValidationResult(state, tuple(dict.fromkeys(issues)), tuple(checks if state == "valid" else checks))


def _continuous_interval_zero(points: tuple[CleanupPoint, ...], morph: str, interval: tuple[int, int]) -> bool:
    start, end = interval
    try:
        if _evaluate_curve(points, morph, start) != 0 or _evaluate_curve(points, morph, end) != 0:
            return False
    except EventCleanupError:
        return False
    return not any(point.semantic_morph == morph and start <= point.frame_no <= end and point.wire_value != 0.0 for point in points)


__all__ = ["CleanupParameter", "CleanupResolution", "CleanupValidationResult", "EventCleanupError", "EventCleanupInput", "EventCleanupPolicy", "POLICY_SCHEMA", "build_event_cleanup_candidate", "build_event_cleanup_policy", "resolve_event_cleanup", "validate_event_cleanup_plan", "validate_event_cleanup_policy"]
