"""Immutable, UI-independent MS30 FinalMorphPlan contracts."""

from __future__ import annotations

import sys

_module_alias = __name__[4:] if __name__.startswith("src.") else "src." + __name__
sys.modules.setdefault(_module_alias, sys.modules[__name__])

import hashlib
import json
import math
import re
import struct
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Any

try:
    from src.core.canonical_morph_value import CanonicalMorphValue, POLICY_ID
    from src.core.morph_name_sets import (
        SEMANTIC_VOWEL_ORDER,
        validate_output_morph_names,
    )
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.canonical_morph_value", "src.core.morph_name_sets"}:
        raise
    from core.canonical_morph_value import CanonicalMorphValue, POLICY_ID
    from core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names


SCHEMA_ID = "final-morph-plan/v1"
CURVE_POLICY_ID = "legacy-writer-curve/v1"
STAGES = (
    "raw_shape",
    "legacy_input",
    "legacy_merge_initial",
    "legacy_short_global",
    "legacy_short_morph",
    "legacy_allowed_range",
    "legacy_zero_prune",
    "legacy_merge_final",
    "canonical",
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
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_SEMANTIC_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UNITS_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_HEX4_RE = re.compile(r"[0-9a-f]{8}\Z")
_FLOAT_HEX_RE = re.compile(
    r"(?:0x[0-9a-f]+(?:\.[0-9a-f]*)?|0x\.[0-9a-f]+)p[+-][0-9]+\Z"
)


class FinalMorphPlanError(ValueError):
    """Raised when a plan DTO or its canonical representation is invalid."""


def _require_int(value: object, name: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise FinalMorphPlanError(f"{name} must be an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise FinalMorphPlanError(f"{name} must be an integer <= {maximum}")
    return value


def _require_text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise FinalMorphPlanError(f"{name} must be text")
    return value


def _require_hash(value: object, name: str) -> str:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise FinalMorphPlanError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _require_tuple(value: object, name: str) -> tuple[Any, ...]:
    if not isinstance(value, tuple):
        raise FinalMorphPlanError(f"{name} must be a tuple")
    return value


def _sorted_unique_text(values: object, name: str) -> tuple[str, ...]:
    items = _require_tuple(values, name)
    if any(type(item) is not str or not item for item in items):
        raise FinalMorphPlanError(f"{name} must contain non-empty strings")
    if items != tuple(sorted(set(items))):
        raise FinalMorphPlanError(f"{name} must be unique and sorted")
    return items


def _validate_mapping(mapping: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(mapping, tuple) or len(mapping) != len(SEMANTIC_VOWEL_ORDER):
        raise FinalMorphPlanError("output_mapping must be a five-pair tuple")
    semantics: list[str] = []
    names: list[str] = []
    for pair in mapping:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise FinalMorphPlanError("output_mapping entries must be pairs")
        semantic, name = pair
        if type(semantic) is not str or type(name) is not str:
            raise FinalMorphPlanError("output_mapping entries must be text pairs")
        semantics.append(semantic)
        names.append(name)
    if tuple(semantics) != SEMANTIC_VOWEL_ORDER:
        raise FinalMorphPlanError("output_mapping must use the fixed semantic vowel order")
    try:
        validated_names = validate_output_morph_names(tuple(names))
    except ValueError as error:
        raise FinalMorphPlanError("output_mapping must use a built-in five-vowel set") from error
    if validated_names != tuple(names):
        raise FinalMorphPlanError("output_mapping is not canonical")
    return tuple(zip(semantics, names))


@dataclass(frozen=True, slots=True)
class FinalMorphIdentityContext:
    source_run_id: str
    analysis_generation: int
    base_plan_digest: str
    effective_plan_digest: str
    manual_revision: int
    resolved_profile_id: str | None
    output_mapping: tuple[tuple[str, str], ...]
    numeric_policy_id: str
    curve_policy_id: str
    silence_policy_id: str
    crossfade_policy_id: str

    def __post_init__(self) -> None:
        _require_text(self.source_run_id, "source_run_id")
        _require_int(self.analysis_generation, "analysis_generation")
        _require_hash(self.base_plan_digest, "base_plan_digest")
        _require_hash(self.effective_plan_digest, "effective_plan_digest")
        _require_int(self.manual_revision, "manual_revision")
        if self.resolved_profile_id is not None:
            _require_text(self.resolved_profile_id, "resolved_profile_id")
        object.__setattr__(self, "output_mapping", _validate_mapping(self.output_mapping))
        if self.resolved_profile_id is None and tuple(
            name for _, name in self.output_mapping
        ) != SEMANTIC_VOWEL_ORDER:
            raise FinalMorphPlanError("no-profile identity must use Japanese output names")
        for name in (
            "numeric_policy_id",
            "curve_policy_id",
            "silence_policy_id",
            "crossfade_policy_id",
        ):
            _require_text(getattr(self, name), name)
        if self.numeric_policy_id != POLICY_ID:
            raise FinalMorphPlanError("numeric_policy_id does not match the B1 policy")
        if self.curve_policy_id != CURVE_POLICY_ID:
            raise FinalMorphPlanError("curve_policy_id is unsupported")


class _FrozenSnapshotDict(dict[str, Any]):
    """Dict-compatible immutable snapshot mapping with safe deepcopy behavior."""

    def __init__(self, values: Mapping[str, Any]) -> None:
        dict.__init__(self, values)

    @staticmethod
    def _immutable(*args: object, **kwargs: object) -> None:
        raise TypeError("snapshot mappings are immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable

    def __deepcopy__(self, memo: dict[int, object]) -> _FrozenSnapshotDict:
        memo[id(self)] = self
        return self


@dataclass(frozen=True, slots=True)
class _FrozenOpaqueSnapshotValue:
    type_name: str


def _deep_freeze_snapshot(value: object) -> object:
    if value is None or type(value) in {str, bool, int, float, bytes}:
        return value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise FinalMorphPlanError("snapshot mapping keys must be text")
        return _FrozenSnapshotDict(
            {key: _deep_freeze_snapshot(value[key]) for key in value}
        )
    if isinstance(value, (tuple, list)):
        return tuple(_deep_freeze_snapshot(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze_snapshot(item) for item in value)
    if is_dataclass(value):
        params = getattr(type(value), "__dataclass_params__", None)
        if params is None or not params.frozen:
            return _FrozenOpaqueSnapshotValue(type(value).__name__)
        frozen_fields = {
            item.name: _deep_freeze_snapshot(getattr(value, item.name))
            for item in fields(value)
            if item.init
        }
        frozen = replace(value, **frozen_fields)
        for item in fields(value):
            if not item.init:
                object.__setattr__(
                    frozen,
                    item.name,
                    _deep_freeze_snapshot(getattr(value, item.name)),
                )
        return frozen
    # Unsupported resolver-owned objects must not survive as mutable aliases.
    # Their type remains diagnosable while the validator classifies missing
    # issuer fields as unavailable.
    return _FrozenOpaqueSnapshotValue(type(value).__name__)


@dataclass(frozen=True, slots=True)
class FinalMorphReplayStage:
    stage: str
    records: tuple[MorphPointRecord, ...]

    def __post_init__(self) -> None:
        if self.stage not in STAGES:
            raise FinalMorphPlanError("replay stage is unsupported")
        object.__setattr__(self, "records", _require_tuple(self.records, "records"))
        if any(
            not isinstance(record, MorphPointRecord) or record.stage != self.stage
            for record in self.records
        ):
            raise FinalMorphPlanError("replay stage records are invalid")


@dataclass(frozen=True, slots=True)
class FinalMorphReplayEvidence:
    """Immutable bridge capture used to bind every candidate stage and baseline."""

    stages: tuple[FinalMorphReplayStage, ...]
    sources: tuple[MorphPointSource, ...]
    requirements: tuple[MorphRequirement, ...]
    transformations: tuple[MorphTransformation, ...]
    baseline_points: tuple[tuple[int, str, float], ...]
    baseline_wire_values: tuple[tuple[int, str, str], ...]
    capture_issues: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "stages",
            "sources",
            "requirements",
            "transformations",
            "baseline_points",
            "baseline_wire_values",
            "capture_issues",
        ):
            object.__setattr__(self, name, _require_tuple(getattr(self, name), name))
        if tuple(item.stage for item in self.stages) != STAGES:
            raise FinalMorphPlanError("replay evidence must contain every ordered stage")
        if any(not isinstance(item, MorphPointSource) for item in self.sources):
            raise FinalMorphPlanError("replay sources are invalid")
        if any(not isinstance(item, MorphRequirement) for item in self.requirements):
            raise FinalMorphPlanError("replay requirements are invalid")
        if any(not isinstance(item, MorphTransformation) for item in self.transformations):
            raise FinalMorphPlanError("replay transformations are invalid")


@dataclass(frozen=True, slots=True)
class FinalMorphFullSnapshotIssuerContext:
    """Complete, separately supplied B2 issuer context.

    The nested values are copied at construction so later mutation of a
    resolver-owned object cannot rewrite the evidence being validated.
    Missing fields remain representable and are classified as unavailable by
    the pure validator; present but contradictory fields are invalid.
    """

    input_kind: str | None
    identity_context: FinalMorphIdentityContext | None
    base_input: object | None
    adjustment_snapshot: object | None
    effective_plan_snapshot: object | None
    issuer_evidence: object | None
    replay_evidence: FinalMorphReplayEvidence | object | None = None

    def __post_init__(self) -> None:
        for name in (
            "base_input",
            "adjustment_snapshot",
            "effective_plan_snapshot",
            "issuer_evidence",
            "replay_evidence",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _deep_freeze_snapshot(value))


def canonical_snapshot_value(value: object) -> Any:
    """Stable named-field form used by the legacy replay identity contract."""
    if value is None or type(value) in {str, bool, int}:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FinalMorphPlanError("snapshot contains a non-finite float")
        return {"binary64": value.hex()}
    if isinstance(value, (tuple, list)):
        return [canonical_snapshot_value(item) for item in value]
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise FinalMorphPlanError("snapshot mapping keys must be text")
        return {key: canonical_snapshot_value(value[key]) for key in sorted(value)}
    if is_dataclass(value):
        return {
            item.name: canonical_snapshot_value(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, (set, frozenset)):
        encoded = [canonical_snapshot_value(item) for item in value]
        return sorted(encoded, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    raise FinalMorphPlanError(f"unsupported snapshot value: {type(value).__name__}")


def resolved_shape_terminal(
    shape: object,
    effective_events: tuple[object, ...],
) -> tuple[int | None, int | None, bool]:
    """Check an existing terminal against event ownership and recorded tail.

    This verifies a resolved position; it never chooses a repair frame.
    """
    points = tuple(getattr(shape, "control_points", ()))
    terminal = points[-1] if points else None
    frame = None if terminal is None else getattr(terminal, "frame_no", None)
    owners = tuple(getattr(shape, "real_base_event_indices", ()))
    tail = getattr(shape, "resolved_tail", None)
    tail_index = getattr(tail, "tail_base_event_index", None)
    if tail_index is None and len(owners) == 1:
        tail_index = owners[0]
    if terminal is None or tail_index is None:
        return frame, tail_index, False
    by_index = {getattr(event, "base_event_index", None): event for event in effective_events}
    event = by_index.get(tail_index)
    semantic = getattr(shape, "vowel", None)
    if (
        event is None
        or getattr(event, "vowel", None) != semantic
        or (owners and tail_index not in owners)
        or any(
            index not in by_index or getattr(by_index[index], "vowel", None) != semantic
            for index in owners
        )
    ):
        return frame, tail_index, False
    end = getattr(event, "end_frame", None)
    hold = 0 if tail is None else getattr(tail, "effective_hold_frames", None)
    softness = 0 if tail is None else getattr(tail, "effective_softness_frames", None)
    if any(type(value) is not int or value < 0 for value in (end, hold, softness)):
        return frame, tail_index, False
    if owners and any(getattr(by_index[index], "end_frame", end + 1) > end for index in owners):
        return frame, tail_index, False
    resolved = (
        getattr(terminal, "point_kind", None) == "end_zero"
        and getattr(terminal, "value", None) == 0.0
        and frame == end + hold + softness
    )
    return frame, tail_index, resolved


def required_zero_event_indices(
    effective_plan: object, semantic: str, frame_no: int,
) -> tuple[int, ...]:
    """Collect real event owners from both shape points and admissions."""
    owners: set[int] = set()
    events = tuple(getattr(effective_plan, "effective_events", ()))
    for shape in getattr(effective_plan, "shapes", ()):
        if getattr(shape, "vowel", None) != semantic:
            continue
        if any(getattr(point, "frame_no", None) == frame_no for point in shape.control_points):
            owners.update(shape.real_base_event_indices)
            terminal_frame, tail_index, resolved = resolved_shape_terminal(shape, events)
            if resolved and terminal_frame == frame_no and tail_index is not None:
                owners.add(tail_index)
            elif resolved and not shape.real_base_event_indices and tail_index is not None:
                # Unknown intent is not proof of automatic intent. A separately
                # resolved, single-event range can still own a required zero.
                tail_event = next(event for event in events if event.base_event_index == tail_index)
                if tuple(shape.event_ranges) == ((tail_event.start_frame, tail_event.end_frame),) and (
                    tail_event.start_frame <= frame_no <= terminal_frame
                ):
                    owners.add(tail_index)
    for admission in getattr(effective_plan, "event_silence_admissions", ()):
        if admission.vowel == semantic and any(
            start <= frame_no < end for start, end in admission.required_zero_frame_ranges
        ):
            owners.update(admission.source_event_indices)
    return tuple(sorted(owners))


def is_global_silence_zero(effective_plan: object, frame_no: int) -> bool:
    """Core endpoints are explicit zero boundaries in the existing contract."""
    return any(start <= frame_no <= end for start, end in effective_plan.silence_core_frame_ranges)


def effective_plan_snapshot_digest(effective_plan: object) -> str:
    """Digest every named field that defines a frozen EffectiveShapePlan."""
    selected = {
        name: getattr(effective_plan, name)
        for name in (
            "base_plan_identity",
            "canonical_adjustment_snapshot",
            "base_events",
            "effective_events",
            "shapes",
            "observation_handoffs",
            "normalization_contract",
            "event_silence_admissions",
            "manual_crossfades",
            "long_vowel_runs",
            "shape_parameters",
            "silence_policy",
            "silence_core_frame_ranges",
            "silence_clip_records",
        )
    }
    payload = canonical_snapshot_value(selected)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class FinalMorphPoint:
    point_id: str
    record_id: str
    frame_no: int
    semantic_morph: str
    value: CanonicalMorphValue
    source_ids: tuple[str, ...]
    required_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.point_id, "point_id")
        _require_text(self.record_id, "record_id")
        _require_int(self.frame_no, "frame_no", maximum=0xFFFFFFFF)
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise FinalMorphPlanError("semantic_morph is unsupported")
        if not isinstance(self.value, CanonicalMorphValue):
            raise FinalMorphPlanError("value must be CanonicalMorphValue")
        object.__setattr__(self, "source_ids", _sorted_unique_text(self.source_ids, "source_ids"))
        object.__setattr__(
            self,
            "required_reasons",
            _sorted_unique_text(self.required_reasons, "required_reasons"),
        )


@dataclass(frozen=True, slots=True)
class MorphPointRecord:
    record_id: str
    stage: str
    ordinal: int
    frame_no: int
    semantic_morph: str
    value_hex: str
    source_ids: tuple[str, ...]
    required_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.record_id, "record_id")
        if self.stage not in STAGES:
            raise FinalMorphPlanError("record stage is unsupported")
        _require_int(self.ordinal, "ordinal")
        _require_int(self.frame_no, "frame_no", maximum=0xFFFFFFFF)
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise FinalMorphPlanError("semantic_morph is unsupported")
        _require_text(self.value_hex, "value_hex")
        try:
            value = float.fromhex(self.value_hex)
        except (TypeError, ValueError, OverflowError) as error:
            raise FinalMorphPlanError("value_hex must be a canonical finite float.hex string") from error
        if not math.isfinite(value) or value.hex() != self.value_hex:
            raise FinalMorphPlanError("value_hex must be a canonical finite float.hex string")
        object.__setattr__(self, "source_ids", _sorted_unique_text(self.source_ids, "source_ids"))
        object.__setattr__(
            self,
            "required_reasons",
            _sorted_unique_text(self.required_reasons, "required_reasons"),
        )


@dataclass(frozen=True, slots=True)
class MorphPointSource:
    source_id: str
    issuer_kind: str
    issuer_id: str
    shape_ordinal: int | None
    point_ordinal: int | None
    base_event_indices: tuple[int, ...]
    point_kind: str
    intent_origin: str

    def __post_init__(self) -> None:
        _require_text(self.source_id, "source_id")
        if self.issuer_kind not in {"shape_point", "requirement"}:
            raise FinalMorphPlanError("issuer_kind is unsupported")
        _require_text(self.issuer_id, "issuer_id")
        _require_text(self.point_kind, "point_kind")
        if self.intent_origin not in {"automatic", "manual", "unknown"}:
            raise FinalMorphPlanError("intent_origin is unsupported")
        indices = _require_tuple(self.base_event_indices, "base_event_indices")
        for item in indices:
            _require_int(item, "base_event_indices item")
        if indices != tuple(sorted(set(indices))):
            raise FinalMorphPlanError("base_event_indices must be unique and sorted")
        if self.issuer_kind == "shape_point":
            _require_int(self.shape_ordinal, "shape_ordinal")
            _require_int(self.point_ordinal, "point_ordinal")
            if self.issuer_id != self.source_id:
                raise FinalMorphPlanError("shape_point issuer_id must equal source_id")
        else:
            if self.shape_ordinal is not None or self.point_ordinal is not None:
                raise FinalMorphPlanError("requirement source ordinals must be null")


@dataclass(frozen=True, slots=True)
class MorphRequirement:
    requirement_id: str
    kind: str
    semantic_morph: str
    start_frame: int
    end_frame: int
    source_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.requirement_id, "requirement_id")
        if self.kind not in {"required_zero", "silence_core", "per_morph_terminal"}:
            raise FinalMorphPlanError("requirement kind is unsupported")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise FinalMorphPlanError("requirement semantic_morph is unsupported")
        _require_int(self.start_frame, "start_frame", maximum=0xFFFFFFFF)
        _require_int(self.end_frame, "end_frame", maximum=0xFFFFFFFF)
        if self.end_frame < self.start_frame:
            raise FinalMorphPlanError("requirement frame range is reversed")
        object.__setattr__(self, "source_ids", _sorted_unique_text(self.source_ids, "source_ids"))
        _require_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class MorphTransformation:
    transformation_id: str
    stage: str
    ordinal: int
    reason: str
    input_record_ids: tuple[str, ...]
    output_record_ids: tuple[str, ...]
    protection_status: str

    def __post_init__(self) -> None:
        _require_text(self.transformation_id, "transformation_id")
        if self.stage not in STAGES[1:]:
            raise FinalMorphPlanError("transformation stage is unsupported")
        _require_int(self.ordinal, "ordinal")
        _require_text(self.reason, "reason")
        object.__setattr__(
            self,
            "input_record_ids",
            _sorted_unique_text(self.input_record_ids, "input_record_ids"),
        )
        object.__setattr__(
            self,
            "output_record_ids",
            _sorted_unique_text(self.output_record_ids, "output_record_ids"),
        )
        _require_text(self.protection_status, "protection_status")


@dataclass(frozen=True, slots=True)
class FinalMorphIssue:
    reason: str
    stage: str
    point_ids: tuple[str, ...] = ()
    requirement_ids: tuple[str, ...] = ()
    semantic_morph: str | None = None
    frame_range: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        if self.reason not in ISSUE_REASONS:
            raise FinalMorphPlanError("issue reason is unsupported")
        _require_text(self.stage, "stage")
        object.__setattr__(self, "point_ids", _sorted_unique_text(self.point_ids, "point_ids"))
        object.__setattr__(
            self,
            "requirement_ids",
            _sorted_unique_text(self.requirement_ids, "requirement_ids"),
        )
        if self.semantic_morph is not None and self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise FinalMorphPlanError("issue semantic_morph is unsupported")
        if self.frame_range is not None:
            if not isinstance(self.frame_range, tuple) or len(self.frame_range) != 2:
                raise FinalMorphPlanError("frame_range must be a two-item tuple or None")
            _require_int(self.frame_range[0], "frame_range start", maximum=0xFFFFFFFF)
            _require_int(self.frame_range[1], "frame_range end", maximum=0xFFFFFFFF)
            if self.frame_range[1] < self.frame_range[0]:
                raise FinalMorphPlanError("frame_range is reversed")


@dataclass(frozen=True, slots=True)
class FinalMorphPlan:
    schema_id: str
    identity_context: FinalMorphIdentityContext
    points: tuple[FinalMorphPoint, ...]
    point_records: tuple[MorphPointRecord, ...]
    source_records: tuple[MorphPointSource, ...]
    requirements: tuple[MorphRequirement, ...]
    transformations: tuple[MorphTransformation, ...]
    output_mapping: tuple[tuple[str, str], ...]
    semantic_digest: str
    wire_digest: str

    def __post_init__(self) -> None:
        if self.schema_id != SCHEMA_ID:
            raise FinalMorphPlanError("schema_id is unsupported")
        if not isinstance(self.identity_context, FinalMorphIdentityContext):
            raise FinalMorphPlanError("identity_context has an invalid type")
        for name in ("points", "point_records", "source_records", "requirements", "transformations"):
            value = _require_tuple(getattr(self, name), name)
            object.__setattr__(self, name, value)
        if any(not isinstance(item, FinalMorphPoint) for item in self.points):
            raise FinalMorphPlanError("points contain an invalid DTO")
        if any(not isinstance(item, MorphPointRecord) for item in self.point_records):
            raise FinalMorphPlanError("point_records contain an invalid DTO")
        if any(not isinstance(item, MorphPointSource) for item in self.source_records):
            raise FinalMorphPlanError("source_records contain an invalid DTO")
        if any(not isinstance(item, MorphRequirement) for item in self.requirements):
            raise FinalMorphPlanError("requirements contain an invalid DTO")
        if any(not isinstance(item, MorphTransformation) for item in self.transformations):
            raise FinalMorphPlanError("transformations contain an invalid DTO")
        object.__setattr__(self, "output_mapping", _validate_mapping(self.output_mapping))
        if type(self.semantic_digest) is not str or _SEMANTIC_DIGEST_RE.fullmatch(self.semantic_digest) is None:
            raise FinalMorphPlanError("semantic_digest must be sha256-prefixed lowercase hex")
        _require_hash(self.wire_digest, "wire_digest")
        if self.output_mapping != self.identity_context.output_mapping:
            raise FinalMorphPlanError("plan mapping differs from identity mapping")

    def to_dict(self) -> dict[str, Any]:
        return _plan_payload(self, include_digests=True)

    def to_json(self) -> str:
        validate_plan_integrity(self)
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: object) -> "FinalMorphPlan":
        if type(value) is not dict:
            raise FinalMorphPlanError("plan must be a JSON object")
        expected = {
            "schema_id",
            "identity_context",
            "points",
            "point_records",
            "source_records",
            "requirements",
            "transformations",
            "output_mapping",
            "semantic_digest",
            "wire_digest",
        }
        if set(value) != expected:
            raise FinalMorphPlanError("plan has an unknown or missing field")
        mapping = _mapping_from_json(value["output_mapping"])
        plan = cls(
            schema_id=value["schema_id"],
            identity_context=_identity_from_dict(value["identity_context"]),
            points=tuple(_point_from_dict(item) for item in _list(value["points"], "points")),
            point_records=tuple(
                _record_from_dict(item) for item in _list(value["point_records"], "point_records")
            ),
            source_records=tuple(
                _source_from_dict(item) for item in _list(value["source_records"], "source_records")
            ),
            requirements=tuple(
                _requirement_from_dict(item) for item in _list(value["requirements"], "requirements")
            ),
            transformations=tuple(
                _transformation_from_dict(item)
                for item in _list(value["transformations"], "transformations")
            ),
            output_mapping=mapping,
            semantic_digest=value["semantic_digest"],
            wire_digest=value["wire_digest"],
        )
        validate_plan_integrity(plan)
        return plan

    @classmethod
    def from_json(cls, value: object) -> "FinalMorphPlan":
        if type(value) is not str:
            raise FinalMorphPlanError("serialized plan must be text")

        def reject_constant(constant: str) -> None:
            raise FinalMorphPlanError(f"invalid JSON numeric constant: {constant}")

        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, item in pairs:
                if key in result:
                    raise FinalMorphPlanError("serialized plan contains duplicate object keys")
                result[key] = item
            return result

        try:
            data = json.loads(
                value,
                parse_constant=reject_constant,
                object_pairs_hook=reject_duplicates,
            )
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise FinalMorphPlanError("serialized plan is invalid JSON") from error
        plan = cls.from_dict(data)
        validate_plan_integrity(plan)
        if plan.to_json() != value:
            raise FinalMorphPlanError("serialized plan is not canonical JSON")
        return plan


@dataclass(frozen=True, slots=True)
class FinalMorphBuildResult:
    state: str
    plan: FinalMorphPlan | None
    baseline_points: tuple[tuple[int, str, float], ...]
    issues: tuple[FinalMorphIssue, ...]
    issuer_evidence: object | None = None

    def __post_init__(self) -> None:
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise FinalMorphPlanError("build result state is unsupported")
        object.__setattr__(self, "baseline_points", tuple(self.baseline_points))
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.state == "valid" and self.plan is None:
            raise FinalMorphPlanError("valid build result must include a plan")


def _list(value: object, name: str) -> list[Any]:
    if type(value) is not list:
        raise FinalMorphPlanError(f"{name} must be a JSON array")
    return value


def _object(value: object, name: str, fields: set[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise FinalMorphPlanError(f"{name} has an unknown or missing field")
    return value


def _json_tuple(values: tuple[Any, ...]) -> list[Any]:
    return list(values)


def _identity_dict(identity: FinalMorphIdentityContext) -> dict[str, Any]:
    return {
        "source_run_id": identity.source_run_id,
        "analysis_generation": identity.analysis_generation,
        "base_plan_digest": identity.base_plan_digest,
        "effective_plan_digest": identity.effective_plan_digest,
        "manual_revision": identity.manual_revision,
        "resolved_profile_id": identity.resolved_profile_id,
        "output_mapping": [[left, right] for left, right in identity.output_mapping],
        "numeric_policy_id": identity.numeric_policy_id,
        "curve_policy_id": identity.curve_policy_id,
        "silence_policy_id": identity.silence_policy_id,
        "crossfade_policy_id": identity.crossfade_policy_id,
    }


def _point_dict(point: FinalMorphPoint) -> dict[str, Any]:
    return {
        "point_id": point.point_id,
        "record_id": point.record_id,
        "frame_no": point.frame_no,
        "semantic_morph": point.semantic_morph,
        "value": point.value.to_dict(),
        "source_ids": _json_tuple(point.source_ids),
        "required_reasons": _json_tuple(point.required_reasons),
    }


def _record_dict(record: MorphPointRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "stage": record.stage,
        "ordinal": record.ordinal,
        "frame_no": record.frame_no,
        "semantic_morph": record.semantic_morph,
        "value_hex": record.value_hex,
        "source_ids": _json_tuple(record.source_ids),
        "required_reasons": _json_tuple(record.required_reasons),
    }


def _source_dict(source: MorphPointSource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "issuer_kind": source.issuer_kind,
        "issuer_id": source.issuer_id,
        "shape_ordinal": source.shape_ordinal,
        "point_ordinal": source.point_ordinal,
        "base_event_indices": _json_tuple(source.base_event_indices),
        "point_kind": source.point_kind,
        "intent_origin": source.intent_origin,
    }


def _requirement_dict(requirement: MorphRequirement) -> dict[str, Any]:
    return {
        "requirement_id": requirement.requirement_id,
        "kind": requirement.kind,
        "semantic_morph": requirement.semantic_morph,
        "start_frame": requirement.start_frame,
        "end_frame": requirement.end_frame,
        "source_ids": _json_tuple(requirement.source_ids),
        "reason": requirement.reason,
    }


def _transformation_dict(transformation: MorphTransformation) -> dict[str, Any]:
    return {
        "transformation_id": transformation.transformation_id,
        "stage": transformation.stage,
        "ordinal": transformation.ordinal,
        "reason": transformation.reason,
        "input_record_ids": _json_tuple(transformation.input_record_ids),
        "output_record_ids": _json_tuple(transformation.output_record_ids),
        "protection_status": transformation.protection_status,
    }


def _plan_payload(plan: FinalMorphPlan, *, include_digests: bool) -> dict[str, Any]:
    payload = {
        "schema_id": plan.schema_id,
        "identity_context": _identity_dict(plan.identity_context),
        "points": [_point_dict(item) for item in plan.points],
        "point_records": [_record_dict(item) for item in plan.point_records],
        "source_records": [_source_dict(item) for item in plan.source_records],
        "requirements": [_requirement_dict(item) for item in plan.requirements],
        "transformations": [_transformation_dict(item) for item in plan.transformations],
        "output_mapping": [[left, right] for left, right in plan.output_mapping],
    }
    if include_digests:
        payload["semantic_digest"] = plan.semantic_digest
        payload["wire_digest"] = plan.wire_digest
    return payload


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def semantic_digest_for_payload(payload: dict[str, Any]) -> str:
    semantic_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"semantic_digest", "wire_digest"}
    }
    return "sha256:" + hashlib.sha256(_canonical_json(semantic_payload).encode("utf-8")).hexdigest()


def wire_digest_for_points(
    points: tuple[FinalMorphPoint, ...],
    output_mapping: tuple[tuple[str, str], ...],
) -> str:
    mapping = dict(_validate_mapping(output_mapping))
    wire = bytearray()
    for point in points:
        if point.frame_no > 0xFFFFFFFF:
            raise FinalMorphPlanError("frame_no is outside the VMD uint32 range")
        name = mapping[point.semantic_morph]
        try:
            encoded_name = name.encode("shift_jis")
        except UnicodeEncodeError as error:
            raise FinalMorphPlanError("mapped name is not representable in Shift-JIS") from error
        if len(encoded_name) > 15:
            raise FinalMorphPlanError("mapped name exceeds the VMD 15-byte field")
        wire.extend(struct.pack("<I", point.frame_no))
        wire.extend(encoded_name + b"\x00" * (15 - len(encoded_name)))
        wire.extend(point.value.binary32_bytes)
    return hashlib.sha256(bytes(wire)).hexdigest()


def validate_plan_integrity(plan: FinalMorphPlan) -> None:
    if not isinstance(plan, FinalMorphPlan):
        raise FinalMorphPlanError("plan must be FinalMorphPlan")
    semantic_order = {semantic: index for index, semantic in enumerate(SEMANTIC_VOWEL_ORDER)}
    if plan.points != tuple(
        sorted(plan.points, key=lambda item: (item.frame_no, semantic_order[item.semantic_morph]))
    ):
        raise FinalMorphPlanError("points are not in canonical frame and semantic order")
    if plan.point_records != tuple(
        sorted(plan.point_records, key=lambda item: (STAGES.index(item.stage), item.ordinal))
    ):
        raise FinalMorphPlanError("point_records are not in canonical stage and ordinal order")
    if plan.source_records != tuple(sorted(plan.source_records, key=lambda item: item.source_id)):
        raise FinalMorphPlanError("source_records are not in source_id order")
    if plan.requirements != tuple(sorted(plan.requirements, key=lambda item: item.requirement_id)):
        raise FinalMorphPlanError("requirements are not in requirement_id order")
    if plan.transformations != tuple(
        sorted(plan.transformations, key=lambda item: (STAGES.index(item.stage), item.ordinal))
    ):
        raise FinalMorphPlanError("transformations are not in canonical stage and ordinal order")
    record_ids = [item.record_id for item in plan.point_records]
    source_ids = [item.source_id for item in plan.source_records]
    requirement_ids = [item.requirement_id for item in plan.requirements]
    if len(record_ids) != len(set(record_ids)) or len(source_ids) != len(set(source_ids)):
        raise FinalMorphPlanError("record or source identifiers are duplicated")
    if len(requirement_ids) != len(set(requirement_ids)):
        raise FinalMorphPlanError("requirement identifiers are duplicated")
    record_ordinals: dict[str, list[int]] = {}
    for record in plan.point_records:
        record_ordinals.setdefault(record.stage, []).append(record.ordinal)
        if record.record_id != f"record:{record.stage}:{record.ordinal}":
            raise FinalMorphPlanError("record_id does not match its stage and ordinal")
    if any(
        ordinals != list(range(len(ordinals)))
        for ordinals in record_ordinals.values()
    ):
        raise FinalMorphPlanError("point record ordinals are not contiguous")
    point_ids = [item.point_id for item in plan.points]
    point_keys = [(item.frame_no, item.semantic_morph) for item in plan.points]
    if len(point_ids) != len(set(point_ids)) or len(point_keys) != len(set(point_keys)):
        raise FinalMorphPlanError("point identifiers or semantic keys are duplicated")
    transform_ids = [item.transformation_id for item in plan.transformations]
    if len(transform_ids) != len(set(transform_ids)):
        raise FinalMorphPlanError("transformation identifiers are duplicated")
    transformation_ordinals: dict[str, list[int]] = {}
    record_by_id = {item.record_id: item for item in plan.point_records}
    previous_stage = {STAGES[index]: STAGES[index - 1] for index in range(1, len(STAGES))}
    for transformation in plan.transformations:
        transformation_ordinals.setdefault(transformation.stage, []).append(
            transformation.ordinal
        )
        if transformation.transformation_id != (
            f"transform:{transformation.stage}:{transformation.ordinal}"
        ):
            raise FinalMorphPlanError(
                "transformation_id does not match its stage and ordinal"
            )
        for record_id in transformation.input_record_ids:
            record = record_by_id.get(record_id)
            if record is None or record.stage != previous_stage[transformation.stage]:
                raise FinalMorphPlanError("transformation input record is missing or out of stage")
        for record_id in transformation.output_record_ids:
            record = record_by_id.get(record_id)
            if record is None or record.stage != transformation.stage:
                raise FinalMorphPlanError("transformation output record is missing or out of stage")
    for stage, predecessor in previous_stage.items():
        transitions = tuple(
            item for item in plan.transformations if item.stage == stage
        )
        expected_inputs = [
            item.record_id for item in plan.point_records if item.stage == predecessor
        ]
        expected_outputs = [
            item.record_id for item in plan.point_records if item.stage == stage
        ]
        actual_inputs = [
            record_id for item in transitions for record_id in item.input_record_ids
        ]
        actual_outputs = [
            record_id for item in transitions for record_id in item.output_record_ids
        ]
        if sorted(actual_inputs) != sorted(expected_inputs) or sorted(actual_outputs) != sorted(
            expected_outputs
        ):
            raise FinalMorphPlanError(
                f"transformations do not provide complete {stage} stage coverage"
            )
    if any(
        ordinals != list(range(len(ordinals)))
        for ordinals in transformation_ordinals.values()
    ):
        raise FinalMorphPlanError("transformation ordinals are not contiguous")
    source_id_set = set(source_ids)
    if any(
        source_id not in source_id_set
        for record in plan.point_records
        for source_id in record.source_ids
    ) or any(
        source_id not in source_id_set
        for requirement in plan.requirements
        for source_id in requirement.source_ids
    ):
        raise FinalMorphPlanError("a record or requirement references a missing source")
    canonical_records = {
        item.record_id: item for item in plan.point_records if item.stage == "canonical"
    }
    if set(canonical_records) != {item.record_id for item in plan.points}:
        raise FinalMorphPlanError("points do not reference the complete canonical record set")
    for point in plan.points:
        record = canonical_records[point.record_id]
        if (
            point.point_id != f"key:{point.semantic_morph}:{point.frame_no}"
            or record.record_id != f"record:canonical:{record.ordinal}"
            or record.frame_no != point.frame_no
            or record.semantic_morph != point.semantic_morph
            or record.value_hex != point.value.scalar.hex()
            or record.source_ids != point.source_ids
            or record.required_reasons != point.required_reasons
        ):
            raise FinalMorphPlanError("point differs from its canonical record")
    payload = _plan_payload(plan, include_digests=False)
    expected_semantic = semantic_digest_for_payload(payload)
    if plan.semantic_digest != expected_semantic:
        raise FinalMorphPlanError("semantic_digest does not match the plan payload")
    expected_wire = wire_digest_for_points(plan.points, plan.output_mapping)
    if plan.wire_digest != expected_wire:
        raise FinalMorphPlanError("wire_digest does not match the mapped binary32 points")
    if plan.identity_context.output_mapping != plan.output_mapping:
        raise FinalMorphPlanError("identity mapping does not match plan mapping")


def validate_final_morph_plan(
    plan: FinalMorphPlan,
    issuer_context: FinalMorphFullSnapshotIssuerContext | None,
) -> tuple[FinalMorphIssue, ...]:
    """Validate a plan against separately supplied complete issuer context."""
    try:
        from src.core.final_morph_producer import validate_final_morph_plan as validate
    except ModuleNotFoundError as error:
        if error.name not in {"src", "src.core", "src.core.final_morph_producer"}:
            raise
        from core.final_morph_producer import validate_final_morph_plan as validate

    return validate(plan, issuer_context)


def create_plan(
    *,
    identity_context: FinalMorphIdentityContext,
    points: tuple[FinalMorphPoint, ...],
    point_records: tuple[MorphPointRecord, ...],
    source_records: tuple[MorphPointSource, ...],
    requirements: tuple[MorphRequirement, ...],
    transformations: tuple[MorphTransformation, ...],
) -> FinalMorphPlan:
    """Create a plan and derive both digests from the exact frozen payload."""
    provisional = FinalMorphPlan(
        schema_id=SCHEMA_ID,
        identity_context=identity_context,
        points=points,
        point_records=point_records,
        source_records=source_records,
        requirements=requirements,
        transformations=transformations,
        output_mapping=identity_context.output_mapping,
        semantic_digest="sha256:" + "0" * 64,
        wire_digest="0" * 64,
    )
    wire_digest = wire_digest_for_points(provisional.points, provisional.output_mapping)
    semantic_digest = semantic_digest_for_payload(
        _plan_payload(provisional, include_digests=False)
    )
    result = FinalMorphPlan(
        schema_id=SCHEMA_ID,
        identity_context=identity_context,
        points=points,
        point_records=point_records,
        source_records=source_records,
        requirements=requirements,
        transformations=transformations,
        output_mapping=identity_context.output_mapping,
        semantic_digest=semantic_digest,
        wire_digest=wire_digest,
    )
    validate_plan_integrity(result)
    return result


def _mapping_from_json(value: object) -> tuple[tuple[str, str], ...]:
    rows = _list(value, "output_mapping")
    if len(rows) != len(SEMANTIC_VOWEL_ORDER):
        raise FinalMorphPlanError("output_mapping must contain five pairs")
    pairs: list[tuple[str, str]] = []
    for row in rows:
        if type(row) is not list or len(row) != 2:
            raise FinalMorphPlanError("output_mapping must use pair arrays")
        pairs.append((row[0], row[1]))
    return _validate_mapping(tuple(pairs))


def _identity_from_dict(value: object) -> FinalMorphIdentityContext:
    fields = {
        "source_run_id",
        "analysis_generation",
        "base_plan_digest",
        "effective_plan_digest",
        "manual_revision",
        "resolved_profile_id",
        "output_mapping",
        "numeric_policy_id",
        "curve_policy_id",
        "silence_policy_id",
        "crossfade_policy_id",
    }
    obj = _object(value, "identity_context", fields)
    return FinalMorphIdentityContext(
        source_run_id=obj["source_run_id"],
        analysis_generation=obj["analysis_generation"],
        base_plan_digest=obj["base_plan_digest"],
        effective_plan_digest=obj["effective_plan_digest"],
        manual_revision=obj["manual_revision"],
        resolved_profile_id=obj["resolved_profile_id"],
        output_mapping=_mapping_from_json(obj["output_mapping"]),
        numeric_policy_id=obj["numeric_policy_id"],
        curve_policy_id=obj["curve_policy_id"],
        silence_policy_id=obj["silence_policy_id"],
        crossfade_policy_id=obj["crossfade_policy_id"],
    )


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    rows = _list(value, name)
    return tuple(rows)


def _point_from_dict(value: object) -> FinalMorphPoint:
    fields = {"point_id", "record_id", "frame_no", "semantic_morph", "value", "source_ids", "required_reasons"}
    obj = _object(value, "point", fields)
    try:
        from src.core.canonical_morph_value import CanonicalMorphValueError
    except ModuleNotFoundError as error:
        if error.name not in {"src", "src.core", "src.core.canonical_morph_value"}:
            raise
        from core.canonical_morph_value import CanonicalMorphValueError

    try:
        numeric = CanonicalMorphValue.from_dict(obj["value"])
    except (CanonicalMorphValueError, TypeError, ValueError) as error:
        raise FinalMorphPlanError("point contains an invalid canonical numeric value") from error
    return FinalMorphPoint(
        point_id=obj["point_id"],
        record_id=obj["record_id"],
        frame_no=obj["frame_no"],
        semantic_morph=obj["semantic_morph"],
        value=numeric,
        source_ids=_string_tuple(obj["source_ids"], "source_ids"),
        required_reasons=_string_tuple(obj["required_reasons"], "required_reasons"),
    )


def _record_from_dict(value: object) -> MorphPointRecord:
    fields = {"record_id", "stage", "ordinal", "frame_no", "semantic_morph", "value_hex", "source_ids", "required_reasons"}
    obj = _object(value, "point_record", fields)
    return MorphPointRecord(
        record_id=obj["record_id"],
        stage=obj["stage"],
        ordinal=obj["ordinal"],
        frame_no=obj["frame_no"],
        semantic_morph=obj["semantic_morph"],
        value_hex=obj["value_hex"],
        source_ids=_string_tuple(obj["source_ids"], "source_ids"),
        required_reasons=_string_tuple(obj["required_reasons"], "required_reasons"),
    )


def _source_from_dict(value: object) -> MorphPointSource:
    fields = {"source_id", "issuer_kind", "issuer_id", "shape_ordinal", "point_ordinal", "base_event_indices", "point_kind", "intent_origin"}
    obj = _object(value, "source", fields)
    indices = _list(obj["base_event_indices"], "base_event_indices")
    return MorphPointSource(
        source_id=obj["source_id"],
        issuer_kind=obj["issuer_kind"],
        issuer_id=obj["issuer_id"],
        shape_ordinal=obj["shape_ordinal"],
        point_ordinal=obj["point_ordinal"],
        base_event_indices=tuple(indices),
        point_kind=obj["point_kind"],
        intent_origin=obj["intent_origin"],
    )


def _requirement_from_dict(value: object) -> MorphRequirement:
    fields = {"requirement_id", "kind", "semantic_morph", "start_frame", "end_frame", "source_ids", "reason"}
    obj = _object(value, "requirement", fields)
    return MorphRequirement(
        requirement_id=obj["requirement_id"],
        kind=obj["kind"],
        semantic_morph=obj["semantic_morph"],
        start_frame=obj["start_frame"],
        end_frame=obj["end_frame"],
        source_ids=_string_tuple(obj["source_ids"], "source_ids"),
        reason=obj["reason"],
    )


def _transformation_from_dict(value: object) -> MorphTransformation:
    fields = {"transformation_id", "stage", "ordinal", "reason", "input_record_ids", "output_record_ids", "protection_status"}
    obj = _object(value, "transformation", fields)
    return MorphTransformation(
        transformation_id=obj["transformation_id"],
        stage=obj["stage"],
        ordinal=obj["ordinal"],
        reason=obj["reason"],
        input_record_ids=_string_tuple(obj["input_record_ids"], "input_record_ids"),
        output_record_ids=_string_tuple(obj["output_record_ids"], "output_record_ids"),
        protection_status=obj["protection_status"],
    )


def issue(
    reason: str,
    stage: str,
    *,
    point_ids: tuple[str, ...] = (),
    requirement_ids: tuple[str, ...] = (),
    semantic_morph: str | None = None,
    frame_range: tuple[int, int] | None = None,
) -> FinalMorphIssue:
    return FinalMorphIssue(
        reason=reason,
        stage=stage,
        point_ids=tuple(sorted(set(point_ids))),
        requirement_ids=tuple(sorted(set(requirement_ids))),
        semantic_morph=semantic_morph,
        frame_range=frame_range,
    )


__all__ = [
    "CURVE_POLICY_ID",
    "FinalMorphBuildResult",
    "FinalMorphIdentityContext",
    "FinalMorphIssue",
    "FinalMorphPlan",
    "FinalMorphPlanError",
    "FinalMorphPoint",
    "MorphPointRecord",
    "MorphPointSource",
    "MorphRequirement",
    "MorphTransformation",
    "SCHEMA_ID",
    "STAGES",
    "create_plan",
    "issue",
    "validate_final_morph_plan",
    "validate_plan_integrity",
    "wire_digest_for_points",
]
