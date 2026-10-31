"""Read-only replay bridge for the existing Writer normalization pipeline."""

from __future__ import annotations

import sys

_module_alias = __name__[4:] if __name__.startswith("src.") else "src." + __name__
sys.modules.setdefault(_module_alias, sys.modules[__name__])

import copy
import hashlib
import json
import math
import struct
from dataclasses import dataclass, fields, replace
from typing import Any, Iterable

try:
    from src.core.final_morph_plan import (
        FinalMorphFullSnapshotIssuerContext,
        FinalMorphIdentityContext,
        FinalMorphReplayEvidence,
        FinalMorphReplayStage,
        MorphPointRecord,
        MorphPointSource,
        MorphRequirement,
        MorphTransformation,
        canonical_snapshot_value,
        effective_plan_snapshot_digest as _core_effective_plan_snapshot_digest,
        is_global_silence_zero,
        required_zero_event_indices,
        resolved_shape_terminal,
    )
    from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.final_morph_plan", "src.core.morph_name_sets"}:
        raise
    from core.final_morph_plan import (
        FinalMorphFullSnapshotIssuerContext,
        FinalMorphIdentityContext,
        FinalMorphReplayEvidence,
        FinalMorphReplayStage,
        MorphPointRecord,
        MorphPointSource,
        MorphRequirement,
        MorphTransformation,
        canonical_snapshot_value,
        effective_plan_snapshot_digest as _core_effective_plan_snapshot_digest,
        is_global_silence_zero,
        required_zero_event_indices,
        resolved_shape_terminal,
    )
    from core.morph_name_sets import SEMANTIC_VOWEL_ORDER


class LegacyReplayUnavailable(RuntimeError):
    """Raised when a frozen effective plan cannot be replayed faithfully."""


@dataclass(frozen=True, slots=True)
class FrozenPoint:
    frame_no: int
    value: float
    point_kind: str
    value_hex: str


@dataclass(frozen=True, slots=True)
class FrozenShape:
    vowel: str
    shape_kind: str
    control_points: tuple[FrozenPoint, ...]
    real_base_event_indices: tuple[int, ...]
    internal_shape_source_tokens: tuple[int, ...]
    event_ranges: tuple[tuple[int, int], ...]
    fallback_reason: str | None
    protection_mode: str | None
    resolved_tail: tuple[tuple[str, object], ...] | None
    silence_core_frame_ranges: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class FrozenContract:
    allowed_non_zero_ranges: tuple[tuple[str, int, int], ...]
    required_zero_frames: tuple[tuple[str, int], ...]
    protected_event_ranges: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True, slots=True)
class FrozenReplayPlan:
    shapes: tuple[FrozenShape, ...]
    normalization_contract: FrozenContract
    silence_core_frame_ranges: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class IssuerShapePoint:
    point_ordinal: int
    frame_no: int
    value_hex: str
    point_kind: str


@dataclass(frozen=True, slots=True)
class IssuerShapeEvidence:
    shape_ordinal: int
    semantic_morph: str
    base_event_indices: tuple[int, ...]
    points: tuple[IssuerShapePoint, ...]
    terminal_frame: int | None
    terminal_value_hex: str | None
    terminal_base_event_index: int | None
    terminal_resolved: bool


@dataclass(frozen=True, slots=True)
class IssuerEventEvidence:
    event_index: int
    semantic_morph: str
    start_frame: int
    peak_frame: int
    end_frame: int
    peak_value_hex: str


@dataclass(frozen=True, slots=True)
class IssuerAdmissionEvidence:
    event_index: int
    semantic_morph: str
    source_event_indices: tuple[int, ...]
    enabled: bool
    boundary_only: bool
    boundary_frame: int | None
    required_zero_frame_ranges: tuple[tuple[int, int], ...]
    core_overlap: bool


@dataclass(frozen=True, slots=True)
class FinalMorphIssuerEvidence:
    """Captured issuer data passed separately to the pure validator."""

    source_run_id: str
    analysis_generation: int
    base_plan_digest: str
    effective_plan_digest: str
    manual_revision: int
    base_events: tuple[IssuerEventEvidence, ...]
    effective_events: tuple[IssuerEventEvidence, ...]
    shapes: tuple[IssuerShapeEvidence, ...]
    admissions: tuple[IssuerAdmissionEvidence, ...]
    required_zero_frames: tuple[tuple[str, int], ...]
    allowed_non_zero_ranges: tuple[tuple[str, int, int], ...]
    protected_event_ranges: tuple[tuple[str, int, int], ...]
    silence_core_frame_ranges: tuple[tuple[int, int], ...]
    manual_event_indices: tuple[int, ...]
    silence_policy_id: str
    effective_plan_snapshot_json: str


@dataclass(frozen=True, slots=True)
class _ReplayRow:
    frame_no: int
    semantic_morph: str
    value: float
    source_ids: tuple[str, ...]
    required_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReplayStage:
    stage: str
    records: tuple[MorphPointRecord, ...]


@dataclass(frozen=True, slots=True)
class LegacyReplayResult:
    stages: tuple[ReplayStage, ...]
    sources: tuple[MorphPointSource, ...]
    requirements: tuple[MorphRequirement, ...]
    transformations: tuple[MorphTransformation, ...]
    baseline_points: tuple[tuple[int, str, float], ...]
    baseline_wire_values: tuple[tuple[int, str, str], ...]
    issuer_evidence: FinalMorphIssuerEvidence
    issuer_context: FinalMorphFullSnapshotIssuerContext
    capture_issues: tuple[str, ...] = ()

    def records_for(self, stage: str) -> tuple[MorphPointRecord, ...]:
        for item in self.stages:
            if item.stage == stage:
                return item.records
        return ()


def _canonical_snapshot_value(value: object) -> Any:
    try:
        return canonical_snapshot_value(value)
    except (TypeError, ValueError) as error:
        raise LegacyReplayUnavailable("effective snapshot is not canonicalizable") from error


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _effective_plan_payload(effective_plan: object) -> dict[str, Any]:
    return {
        "base_plan_identity": getattr(effective_plan, "base_plan_identity"),
        "canonical_adjustment_snapshot": getattr(effective_plan, "canonical_adjustment_snapshot"),
        "base_events": getattr(effective_plan, "base_events"),
        "effective_events": getattr(effective_plan, "effective_events"),
        "shapes": getattr(effective_plan, "shapes"),
        "observation_handoffs": getattr(effective_plan, "observation_handoffs"),
        "normalization_contract": getattr(effective_plan, "normalization_contract"),
        "event_silence_admissions": getattr(effective_plan, "event_silence_admissions"),
        "manual_crossfades": getattr(effective_plan, "manual_crossfades"),
        "long_vowel_runs": getattr(effective_plan, "long_vowel_runs"),
        "shape_parameters": getattr(effective_plan, "shape_parameters"),
        "silence_policy": getattr(effective_plan, "silence_policy"),
        "silence_core_frame_ranges": getattr(effective_plan, "silence_core_frame_ranges"),
        "silence_clip_records": getattr(effective_plan, "silence_clip_records"),
    }


def effective_plan_snapshot_digest(effective_plan: object) -> str:
    """Hash all B2 identity inputs using named fields and canonical float hex."""
    return _core_effective_plan_snapshot_digest(copy.deepcopy(effective_plan))


def _freeze_replay_plan(effective_plan: object) -> tuple[FrozenReplayPlan, str, tuple[IssuerShapeEvidence, ...]]:
    frozen = copy.deepcopy(effective_plan)
    contract = getattr(frozen, "normalization_contract", None)
    shapes_raw = tuple(getattr(frozen, "shapes", ()))
    if contract is None or not hasattr(contract, "required_zero_frames"):
        raise LegacyReplayUnavailable("effective plan has no normalization contract")
    shapes: list[FrozenShape] = []
    evidence: list[IssuerShapeEvidence] = []
    for shape_ordinal, shape in enumerate(shapes_raw):
        vowel = getattr(shape, "vowel", None)
        if vowel not in SEMANTIC_VOWEL_ORDER:
            raise LegacyReplayUnavailable("effective plan has an unsupported semantic vowel")
        base_indices = tuple(sorted(set(getattr(shape, "real_base_event_indices", ()))))
        point_rows: list[FrozenPoint] = []
        evidence_points: list[IssuerShapePoint] = []
        for point_ordinal, point in enumerate(tuple(getattr(shape, "control_points", ()))):
            frame_no = getattr(point, "frame_no", None)
            value = getattr(point, "value", None)
            point_kind = getattr(point, "point_kind", None)
            if isinstance(frame_no, bool) or not isinstance(frame_no, int) or not 0 <= frame_no <= 0xFFFFFFFF:
                raise LegacyReplayUnavailable("shape point frame is outside uint32")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise LegacyReplayUnavailable("shape point value is not numeric")
            value = float(value)
            if not math.isfinite(value):
                raise LegacyReplayUnavailable("shape point value is not finite")
            if type(point_kind) is not str or not point_kind:
                raise LegacyReplayUnavailable("shape point kind is missing")
            point_rows.append(FrozenPoint(frame_no, value, point_kind, value.hex()))
            evidence_points.append(IssuerShapePoint(point_ordinal, frame_no, value.hex(), point_kind))
        resolved_tail = getattr(shape, "resolved_tail", None)
        frozen_tail = None
        tail_event_index = None
        if resolved_tail is not None:
            frozen_tail = tuple(
                (item.name, _canonical_snapshot_value(getattr(resolved_tail, item.name)))
                for item in fields(resolved_tail)
            )
            tail_event_index = getattr(resolved_tail, "tail_base_event_index", None)
        terminal = point_rows[-1] if point_rows else None
        _, tail_event_index, terminal_resolved = resolved_shape_terminal(
            shape, tuple(getattr(frozen, "effective_events", ()))
        )
        shapes.append(
            FrozenShape(
                vowel=vowel,
                shape_kind=str(getattr(shape, "shape_kind", "unknown")),
                control_points=tuple(point_rows),
                real_base_event_indices=base_indices,
                internal_shape_source_tokens=tuple(getattr(shape, "internal_shape_source_tokens", ())),
                event_ranges=tuple(getattr(shape, "event_ranges", ())),
                fallback_reason=getattr(shape, "fallback_reason", None),
                protection_mode=getattr(shape, "protection_mode", None),
                resolved_tail=frozen_tail,
                silence_core_frame_ranges=tuple(getattr(shape, "silence_core_frame_ranges", ())),
            )
        )
        evidence.append(
            IssuerShapeEvidence(
                shape_ordinal=shape_ordinal,
                semantic_morph=vowel,
                base_event_indices=base_indices,
                points=tuple(evidence_points),
                terminal_frame=None if terminal is None else terminal.frame_no,
                terminal_value_hex=None if terminal is None else terminal.value_hex,
                terminal_base_event_index=tail_event_index,
                terminal_resolved=terminal_resolved,
            )
        )

    frozen_contract = FrozenContract(
        allowed_non_zero_ranges=tuple(getattr(contract, "allowed_non_zero_ranges", ())),
        required_zero_frames=tuple(getattr(contract, "required_zero_frames", ())),
        protected_event_ranges=tuple(getattr(contract, "protected_event_ranges", ())),
    )
    frozen_plan = FrozenReplayPlan(
        shapes=tuple(shapes),
        normalization_contract=frozen_contract,
        silence_core_frame_ranges=tuple(getattr(frozen, "silence_core_frame_ranges", ()) or ()),
    )
    digest = effective_plan_snapshot_digest(frozen)
    full_json = _canonical_json(_canonical_snapshot_value(frozen))
    return frozen_plan, digest, tuple(evidence)


def _event_evidence(event: object) -> IssuerEventEvidence:
    value = float(getattr(event, "peak_value"))
    return IssuerEventEvidence(
        event_index=getattr(event, "base_event_index"),
        semantic_morph=getattr(event, "vowel"),
        start_frame=getattr(event, "start_frame"),
        peak_frame=getattr(event, "peak_frame"),
        end_frame=getattr(event, "end_frame"),
        peak_value_hex=value.hex(),
    )


def capture_issuer_evidence(
    effective_plan: object,
    *,
    source_run_id: str,
    analysis_generation: int,
    manual_revision: int,
) -> FinalMorphIssuerEvidence:
    """Deep-copy then freeze issuer evidence before a candidate is built."""
    frozen = copy.deepcopy(effective_plan)
    _, effective_digest, shapes = _freeze_replay_plan(frozen)
    base_identity = getattr(frozen, "base_plan_identity", None)
    base_digest = getattr(base_identity, "digest", None)
    if type(base_digest) is not str or len(base_digest) != 64:
        raise LegacyReplayUnavailable("base plan identity digest is unavailable")
    base_events = tuple(_event_evidence(item) for item in getattr(frozen, "base_events", ()))
    effective_events = tuple(_event_evidence(item) for item in getattr(frozen, "effective_events", ()))
    admissions = tuple(
        IssuerAdmissionEvidence(
            event_index=item.event_index,
            semantic_morph=item.vowel,
            source_event_indices=tuple(item.source_event_indices),
            enabled=item.enabled,
            boundary_only=item.boundary_only,
            boundary_frame=item.boundary_frame,
            required_zero_frame_ranges=tuple(item.required_zero_frame_ranges),
            core_overlap=item.base_event_silence_core_overlap,
        )
        for item in getattr(frozen, "event_silence_admissions", ())
    )
    snapshot = _canonical_json(_canonical_snapshot_value(_effective_plan_payload(frozen)))
    manual_indices = {
        item.base_event_index
        for item in getattr(getattr(frozen, "canonical_adjustment_snapshot", None), "adjustments", ())
        if not getattr(item, "is_empty", False)
    }
    for item in getattr(frozen, "manual_crossfades", ()):
        manual_indices.update((item.source_base_event_index, item.target_base_event_index))
    contract = getattr(frozen, "normalization_contract")
    return FinalMorphIssuerEvidence(
        source_run_id=source_run_id,
        analysis_generation=analysis_generation,
        base_plan_digest=base_digest,
        effective_plan_digest=effective_digest,
        manual_revision=manual_revision,
        base_events=base_events,
        effective_events=effective_events,
        shapes=shapes,
        admissions=admissions,
        required_zero_frames=tuple(contract.required_zero_frames),
        allowed_non_zero_ranges=tuple(contract.allowed_non_zero_ranges),
        protected_event_ranges=tuple(contract.protected_event_ranges),
        silence_core_frame_ranges=tuple(getattr(frozen, "silence_core_frame_ranges", ()) or ()),
        manual_event_indices=tuple(sorted(manual_indices)),
        silence_policy_id=getattr(frozen, "silence_policy"),
        effective_plan_snapshot_json=snapshot,
    )


def _range_mapping(values: Iterable[tuple[str, int, int]]) -> dict[str, list[tuple[int, int]]]:
    result: dict[str, list[tuple[int, int]]] = {}
    for vowel, start_frame, end_frame in values:
        result.setdefault(vowel, []).append((start_frame, end_frame))
    return result


def _required_mapping(values: Iterable[tuple[str, int]]) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    for vowel, frame_no in values:
        result.setdefault(vowel, set()).add(frame_no)
    return result


def _record_rows(stage: str, rows: tuple[_ReplayRow, ...]) -> tuple[MorphPointRecord, ...]:
    return tuple(
        MorphPointRecord(
            record_id=f"record:{stage}:{ordinal}",
            stage=stage,
            ordinal=ordinal,
            frame_no=row.frame_no,
            semantic_morph=row.semantic_morph,
            value_hex=row.value.hex(),
            source_ids=tuple(sorted(set(row.source_ids))),
            required_reasons=tuple(sorted(set(row.required_reasons))),
        )
        for ordinal, row in enumerate(rows)
    )


def _frames(rows: tuple[_ReplayRow, ...]) -> list[tuple[int, str, float]]:
    return [(row.frame_no, row.semantic_morph, row.value) for row in rows]


def _make_transition(
    stage: str,
    previous: tuple[_ReplayRow, ...],
    previous_records: tuple[MorphPointRecord, ...],
    output_frames: list[tuple[int, str, float]],
    *,
    operation: str,
    merge: bool = False,
) -> tuple[tuple[_ReplayRow, ...], tuple[MorphTransformation, ...]]:
    previous_by_key: dict[tuple[int, str], list[tuple[int, _ReplayRow, MorphPointRecord]]] = {}
    for index, (row, record) in enumerate(zip(previous, previous_records)):
        previous_by_key.setdefault((row.frame_no, row.semantic_morph), []).append((index, row, record))
    used: set[int] = set()
    rows: list[_ReplayRow] = []
    transformations: list[MorphTransformation] = []
    for ordinal, (frame_no, semantic, value) in enumerate(output_frames):
        key = (frame_no, semantic)
        candidates = previous_by_key.get(key, [])
        if not candidates:
            raise LegacyReplayUnavailable(f"{stage} created an untraceable point at {key!r}")
        if merge:
            selected = candidates
        else:
            selected = [item for item in candidates if item[0] not in used]
            if not selected:
                raise LegacyReplayUnavailable(f"{stage} duplicated an untraceable point at {key!r}")
            selected = selected[:1]
        for index, _, _ in selected:
            used.add(index)
        source_ids = tuple(sorted({source for _, row, _ in selected for source in row.source_ids}))
        reasons = tuple(sorted({reason for _, row, _ in selected for reason in row.required_reasons}))
        output_row = _ReplayRow(frame_no, semantic, float(value), source_ids, reasons)
        rows.append(output_row)
        input_ids = tuple(sorted(record.record_id for _, _, record in selected))
        output_id = f"record:{stage}:{ordinal}"
        if not input_ids:
            status = "requirement_synthesized"
        elif merge and len(selected) > 1:
            status = "legacy_merge"
        elif all(old.value == output_row.value for _, old, _ in selected):
            status = "preserved"
        else:
            status = "legacy_transformed"
        transformations.append(
            MorphTransformation(
                transformation_id=f"transform:{stage}:{len(transformations)}",
                stage=stage,
                ordinal=len(transformations),
                reason=operation,
                input_record_ids=input_ids,
                output_record_ids=(output_id,),
                protection_status=status,
            )
        )
    for index, row in enumerate(previous):
        if index in used:
            continue
        record = previous_records[index]
        transformations.append(
            MorphTransformation(
                transformation_id=f"transform:{stage}:{len(transformations)}",
                stage=stage,
                ordinal=len(transformations),
                reason=operation,
                input_record_ids=(record.record_id,),
                output_record_ids=(),
                protection_status="legacy_removed",
            )
        )
    return tuple(rows), tuple(transformations)


def _make_raw_records(
    replay_plan: FrozenReplayPlan,
    *,
    source_run_id: str,
    manual_event_indices: set[int],
    required_ids: dict[tuple[str, int], tuple[str, ...]],
) -> tuple[tuple[_ReplayRow, ...], tuple[MorphPointSource, ...]]:
    rows: list[_ReplayRow] = []
    sources: list[MorphPointSource] = []
    for shape_ordinal, shape in enumerate(replay_plan.shapes):
        base_indices = tuple(sorted(set(shape.real_base_event_indices)))
        if manual_event_indices.intersection(base_indices):
            origin = "manual"
        elif base_indices:
            origin = "automatic"
        else:
            origin = "unknown"
        for point_ordinal, point in enumerate(shape.control_points):
            source_id = f"{source_run_id}:shape:{shape_ordinal}:point:{point_ordinal}"
            point_sources = (source_id,)
            key_requirements = required_ids.get((shape.vowel, point.frame_no), ())
            reasons = list(key_requirements)
            if origin == "manual":
                reasons.append("manual_intent")
            elif origin == "unknown":
                reasons.append("unknown_origin")
            sources.append(
                MorphPointSource(
                    source_id=source_id,
                    issuer_kind="shape_point",
                    issuer_id=source_id,
                    shape_ordinal=shape_ordinal,
                    point_ordinal=point_ordinal,
                    base_event_indices=base_indices,
                    point_kind=point.point_kind,
                    intent_origin=origin,
                )
            )
            rows.append(
                _ReplayRow(
                    point.frame_no,
                    shape.vowel,
                    point.value,
                    point_sources,
                    tuple(sorted(set(reasons))),
                )
            )
    return tuple(rows), tuple(sources)


def _requirements_and_synthetic_sources(
    replay_plan: FrozenReplayPlan,
    *,
    source_run_id: str,
    evidence: FinalMorphIssuerEvidence,
    effective_plan_snapshot: object,
) -> tuple[tuple[MorphRequirement, ...], tuple[MorphPointSource, ...], dict[tuple[str, int], tuple[str, ...]]]:
    requirements: list[MorphRequirement] = []
    sources: list[MorphPointSource] = []
    by_key_sources: dict[tuple[str, int], set[str]] = {}
    points_by_key: dict[tuple[str, int], set[str]] = {}
    for shape_ordinal, shape in enumerate(replay_plan.shapes):
        for point_ordinal, point in enumerate(shape.control_points):
            points_by_key.setdefault((shape.vowel, point.frame_no), set()).add(
                f"{source_run_id}:shape:{shape_ordinal}:point:{point_ordinal}"
            )
    required_pairs = tuple(sorted(set(evidence.required_zero_frames), key=lambda item: (item[1], item[0])))
    for semantic, frame_no in required_pairs:
        requirement_id = f"requirement:required_zero:{semantic}:{frame_no}"
        source_id = f"{source_run_id}:requirement:{requirement_id}"
        event_indices = required_zero_event_indices(effective_plan_snapshot, semantic, frame_no)
        matched = set(points_by_key.get((semantic, frame_no), ()))
        matched.add(source_id)
        requirements.append(
            MorphRequirement(
                requirement_id=requirement_id,
                kind="required_zero",
                semantic_morph=semantic,
                start_frame=frame_no,
                end_frame=frame_no,
                source_ids=tuple(sorted(matched)),
                reason="effective_plan_required_zero",
            )
        )
        sources.append(
            MorphPointSource(
                source_id=source_id,
                issuer_kind="requirement",
                issuer_id=requirement_id,
                shape_ordinal=None,
                point_ordinal=None,
                base_event_indices=event_indices,
                point_kind="required_zero",
                intent_origin="automatic",
            )
        )
        by_key_sources.setdefault((semantic, frame_no), set()).add(requirement_id)

    for start_frame, end_frame in evidence.silence_core_frame_ranges:
        for semantic in SEMANTIC_VOWEL_ORDER:
            requirement_id = f"requirement:silence_core:{semantic}:{start_frame}:{end_frame}"
            source_id = f"{source_run_id}:requirement:{requirement_id}"
            requirements.append(
                MorphRequirement(
                    requirement_id=requirement_id,
                    kind="silence_core",
                    semantic_morph=semantic,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    source_ids=(source_id,),
                    reason="effective_plan_silence_core",
                )
            )
            sources.append(
                MorphPointSource(
                    source_id=source_id,
                    issuer_kind="requirement",
                    issuer_id=requirement_id,
                    shape_ordinal=None,
                    point_ordinal=None,
                    base_event_indices=(),
                    point_kind="silence_core",
                    intent_origin="automatic",
                )
            )

    shape_evidence = {item.shape_ordinal: item for item in evidence.shapes}
    for shape_ordinal, shape in enumerate(replay_plan.shapes):
        shape_info = shape_evidence.get(shape_ordinal)
        if shape_info is None or not shape_info.terminal_resolved or shape_info.terminal_frame is None:
            continue
        requirement_id = f"requirement:per_morph_terminal:{shape.vowel}:{shape_ordinal}:{shape_info.terminal_frame}"
        source_id = f"{source_run_id}:requirement:{requirement_id}"
        terminal_source_id = (
            f"{source_run_id}:shape:{shape_ordinal}:point:{len(shape.control_points) - 1}"
        )
        requirements.append(
            MorphRequirement(
                requirement_id=requirement_id,
                kind="per_morph_terminal",
                semantic_morph=shape.vowel,
                start_frame=shape_info.terminal_frame,
                end_frame=shape_info.terminal_frame,
                source_ids=tuple(sorted({source_id, terminal_source_id})),
                reason="resolved_shape_group_terminal",
            )
        )
        sources.append(
            MorphPointSource(
                source_id=source_id,
                issuer_kind="requirement",
                issuer_id=requirement_id,
                shape_ordinal=None,
                point_ordinal=None,
                base_event_indices=(
                    (shape_info.terminal_base_event_index,)
                    if shape_info.terminal_base_event_index is not None
                    else shape_info.base_event_indices
                ),
                point_kind="per_morph_terminal",
                intent_origin="automatic",
            )
        )
        by_key_sources.setdefault((shape.vowel, shape_info.terminal_frame), set()).add(requirement_id)

    return (
        tuple(sorted(requirements, key=lambda item: item.requirement_id)),
        tuple(sorted(sources, key=lambda item: item.source_id)),
        {key: tuple(sorted(value)) for key, value in by_key_sources.items()},
    )


def _legacy_input_rows(
    replay_plan: FrozenReplayPlan,
    raw_rows: tuple[_ReplayRow, ...],
    sources: tuple[MorphPointSource, ...],
    requirements: tuple[MorphRequirement, ...],
    required_ids: dict[tuple[str, int], tuple[str, ...]],
) -> tuple[_ReplayRow, ...]:
    rows = list(raw_rows)
    source_by_id = {item.source_id: item for item in sources}
    requirement_by_id = {item.requirement_id: item for item in requirements}
    silence_ranges = replay_plan.silence_core_frame_ranges
    for semantic, frame_no in replay_plan.normalization_contract.required_zero_frames:
        if not any(start <= frame_no <= end for start, end in silence_ranges):
            continue
        related = required_ids.get((semantic, frame_no), ())
        req_sources = tuple(
            source_id
            for requirement_id in related
            for source_id in requirement_by_id[requirement_id].source_ids
            if source_by_id[source_id].issuer_kind == "requirement"
        )
        if not req_sources:
            raise LegacyReplayUnavailable("silence-core zero lacks requirement issuer source")
        rows.append(
            _ReplayRow(
                frame_no,
                semantic,
                0.0,
                tuple(sorted(set(req_sources))),
                related,
            )
        )
    rows.sort(key=lambda item: (item.frame_no, item.semantic_morph))
    return tuple(rows)


def replay_effective_shape_plan(
    issuer_context: FinalMorphFullSnapshotIssuerContext,
) -> LegacyReplayResult:
    """Freeze, replay and trace a complete, explicitly issued B2 snapshot."""
    try:
        from src.core.effective_shape_plan import build_base_plan_identity
        from src.vmd_writer import effective_shape_adapter, writer
    except ModuleNotFoundError as error:
        if error.name not in {"src", "src.core", "src.core.effective_shape_plan", "src.vmd_writer"}:
            raise
        from core.effective_shape_plan import build_base_plan_identity
        from vmd_writer import effective_shape_adapter, writer
    if not isinstance(issuer_context, FinalMorphFullSnapshotIssuerContext):
        raise LegacyReplayUnavailable("full-snapshot issuer context is missing")
    if issuer_context.input_kind not in {"synthetic_snapshot", "captured_snapshot"}:
        raise LegacyReplayUnavailable("full-snapshot input kind is unavailable")
    identity = issuer_context.identity_context
    base_input = issuer_context.base_input
    adjustment_snapshot = issuer_context.adjustment_snapshot
    effective_plan = issuer_context.effective_plan_snapshot
    supplied_evidence = issuer_context.issuer_evidence
    if (
        not isinstance(identity, FinalMorphIdentityContext)
        or base_input is None
        or adjustment_snapshot is None
        or effective_plan is None
        or supplied_evidence is None
    ):
        raise LegacyReplayUnavailable("full-snapshot issuer context is incomplete")

    source_run_id = identity.source_run_id
    analysis_generation = identity.analysis_generation
    manual_revision = identity.manual_revision
    frozen_copy = copy.deepcopy(effective_plan)
    replay_plan, _, _ = _freeze_replay_plan(frozen_copy)
    captured_evidence = capture_issuer_evidence(
        frozen_copy,
        source_run_id=source_run_id,
        analysis_generation=analysis_generation,
        manual_revision=manual_revision,
    )
    capture_issues: list[str] = []
    try:
        computed_base = build_base_plan_identity(base_input).digest
        computed_effective = _core_effective_plan_snapshot_digest(frozen_copy)
    except (AttributeError, TypeError, ValueError, RuntimeError):
        computed_base = ""
        computed_effective = ""
        capture_issues.append("identity_mismatch")
    if (
        computed_base != identity.base_plan_digest
        or computed_effective != identity.effective_plan_digest
        or getattr(getattr(frozen_copy, "base_plan_identity", None), "digest", None)
        != computed_base
        or getattr(frozen_copy, "canonical_adjustment_snapshot", None) != adjustment_snapshot
        or getattr(getattr(adjustment_snapshot, "base_plan_identity", None), "digest", None)
        != computed_base
        or getattr(frozen_copy, "silence_policy", None) != identity.silence_policy_id
    ):
        capture_issues.append("identity_mismatch")
    if supplied_evidence != captured_evidence:
        capture_issues.append("provenance_missing")
    evidence = captured_evidence
    manual_indices = set(evidence.manual_event_indices)
    if any(
        not required_zero_event_indices(frozen_copy, semantic, frame_no)
        and not is_global_silence_zero(frozen_copy, frame_no)
        for semantic, frame_no in evidence.required_zero_frames
    ):
        capture_issues.append("capture_unavailable")
    requirements, req_sources, required_ids = _requirements_and_synthetic_sources(
        replay_plan,
        source_run_id=source_run_id,
        evidence=evidence,
        effective_plan_snapshot=frozen_copy,
    )
    raw_rows, shape_sources = _make_raw_records(
        replay_plan,
        source_run_id=source_run_id,
        manual_event_indices=manual_indices,
        required_ids=required_ids,
    )
    sources = tuple(sorted((*shape_sources, *req_sources), key=lambda item: item.source_id))
    raw_records = _record_rows("raw_shape", raw_rows)
    stages: list[ReplayStage] = [ReplayStage("raw_shape", raw_records)]
    transformations: list[MorphTransformation] = []

    legacy_input_rows = _legacy_input_rows(
        replay_plan,
        raw_rows,
        sources,
        requirements,
        required_ids,
    )
    legacy_input_records = _record_rows("legacy_input", legacy_input_rows)
    raw_by_source = {source_id: raw_records[index] for index, row in enumerate(raw_rows) for source_id in row.source_ids}
    input_transforms: list[MorphTransformation] = []
    for ordinal, (row, record) in enumerate(zip(legacy_input_rows, legacy_input_records)):
        input_records = tuple(
            sorted(
                {
                    raw_by_source[source_id].record_id
                    for source_id in row.source_ids
                    if source_id in raw_by_source
                }
            )
        )
        source_items = [item for item in sources if item.source_id in row.source_ids]
        synthesized = any(item.issuer_kind == "requirement" for item in source_items)
        input_transforms.append(
            MorphTransformation(
                transformation_id=f"transform:legacy_input:{ordinal}",
                stage="legacy_input",
                ordinal=ordinal,
                reason="shape_point_to_legacy_input" if input_records else "required_zero_synthesis",
                input_record_ids=input_records,
                output_record_ids=(record.record_id,),
                protection_status="requirement_synthesized" if synthesized and not input_records else "preserved",
            )
        )
    transformations.extend(input_transforms)
    stages.append(ReplayStage("legacy_input", legacy_input_records))

    contract = replay_plan.normalization_contract
    required_map = _required_mapping(contract.required_zero_frames)
    allowed_map = _range_mapping(contract.allowed_non_zero_ranges)
    protected_map = _range_mapping(contract.protected_event_ranges)

    merged_initial_frames = writer._merge_duplicate_morph_frames(_frames(legacy_input_rows))
    merged_initial_rows, trans = _make_transition(
        "legacy_merge_initial",
        legacy_input_rows,
        legacy_input_records,
        merged_initial_frames,
        operation="legacy_duplicate_merge",
        merge=True,
    )
    transformations.extend(trans)
    merged_initial_records = _record_rows("legacy_merge_initial", merged_initial_rows)
    stages.append(ReplayStage("legacy_merge_initial", merged_initial_records))

    active_specs = writer._filter_active_ms11_2_protected_specs(_frames(merged_initial_rows), None)
    open_state = writer._build_morph_frame_open_state(_frames(merged_initial_rows))
    short_global_frames = writer._normalize_isolated_short_open_segments(
        _frames(merged_initial_rows),
        open_state,
        active_protected_specs=active_specs,
        protected_event_ranges=protected_map,
    )
    short_global_rows, trans = _make_transition(
        "legacy_short_global",
        merged_initial_rows,
        merged_initial_records,
        short_global_frames,
        operation="legacy_isolated_short_open_normalization",
    )
    transformations.extend(trans)
    short_global_records = _record_rows("legacy_short_global", short_global_rows)
    stages.append(ReplayStage("legacy_short_global", short_global_records))

    active_specs = writer._filter_active_ms11_2_protected_specs(_frames(short_global_rows), None)
    open_state = writer._build_morph_frame_open_state(_frames(short_global_rows))
    short_morph_frames = writer._normalize_short_morph_pulses(
        _frames(short_global_rows),
        open_state,
        active_protected_specs=active_specs,
        protected_event_ranges=protected_map,
    )
    short_morph_rows, trans = _make_transition(
        "legacy_short_morph",
        short_global_rows,
        short_global_records,
        short_morph_frames,
        operation="legacy_short_morph_pulse_normalization",
    )
    transformations.extend(trans)
    short_morph_records = _record_rows("legacy_short_morph", short_morph_rows)
    stages.append(ReplayStage("legacy_short_morph", short_morph_records))

    allowed_frames = writer._remove_non_zero_outside_allowed_ranges(
        _frames(short_morph_rows),
        allowed_non_zero_ranges=allowed_map,
    )
    allowed_rows, trans = _make_transition(
        "legacy_allowed_range",
        short_morph_rows,
        short_morph_records,
        allowed_frames,
        operation="legacy_allowed_non_zero_range_filter",
    )
    transformations.extend(trans)
    allowed_records = _record_rows("legacy_allowed_range", allowed_rows)
    stages.append(ReplayStage("legacy_allowed_range", allowed_records))

    pruned_frames = writer._prune_redundant_zero_morph_frames(
        _frames(allowed_rows),
        required_zero_frames=required_map,
    )
    pruned_rows, trans = _make_transition(
        "legacy_zero_prune",
        allowed_rows,
        allowed_records,
        pruned_frames,
        operation="legacy_redundant_zero_prune",
    )
    transformations.extend(trans)
    pruned_records = _record_rows("legacy_zero_prune", pruned_rows)
    stages.append(ReplayStage("legacy_zero_prune", pruned_records))

    merged_final_frames = writer._merge_duplicate_morph_frames(_frames(pruned_rows))
    merged_final_rows, trans = _make_transition(
        "legacy_merge_final",
        pruned_rows,
        pruned_records,
        merged_final_frames,
        operation="legacy_final_duplicate_merge",
        merge=True,
    )
    transformations.extend(trans)
    merged_final_records = _record_rows("legacy_merge_final", merged_final_rows)
    stages.append(ReplayStage("legacy_merge_final", merged_final_records))

    canonical_frames = writer._sort_morph_frames(_frames(merged_final_rows))
    canonical_rows, trans = _make_transition(
        "canonical",
        merged_final_rows,
        merged_final_records,
        canonical_frames,
        operation="legacy_final_sort",
    )
    transformations.extend(trans)
    canonical_records = _record_rows("canonical", canonical_rows)
    stages.append(ReplayStage("canonical", canonical_records))

    # Run the established public adapter as an independent parity oracle.
    expected = effective_shape_adapter.build_morph_frames_from_effective_shape_plan(
        replay_plan,
        apply_final_normalization=True,
        output_morph_names=SEMANTIC_VOWEL_ORDER,
    )
    actual = tuple((row.frame_no, row.semantic_morph, row.value) for row in canonical_rows)
    if actual != expected:
        raise LegacyReplayUnavailable("stage replay differs from effective_shape_adapter baseline")

    try:
        baseline_wire = tuple(
            (frame_no, semantic, struct.pack("<f", writer._finalize_morph_value(value)).hex())
            for frame_no, semantic, value in actual
        )
    except (OverflowError, struct.error) as error:
        raise LegacyReplayUnavailable("legacy baseline cannot be represented as binary32") from error
    replay_evidence = FinalMorphReplayEvidence(
        stages=tuple(
            FinalMorphReplayStage(stage.stage, stage.records)
            for stage in stages
        ),
        sources=sources,
        requirements=requirements,
        transformations=tuple(transformations),
        baseline_points=actual,
        baseline_wire_values=baseline_wire,
        capture_issues=tuple(sorted(set(capture_issues))),
    )
    completed_context = replace(
        issuer_context,
        replay_evidence=replay_evidence,
    )
    return LegacyReplayResult(
        stages=tuple(stages),
        sources=sources,
        requirements=requirements,
        transformations=tuple(transformations),
        baseline_points=actual,
        baseline_wire_values=baseline_wire,
        issuer_evidence=evidence,
        issuer_context=completed_context,
        capture_issues=tuple(sorted(set(capture_issues))),
    )


__all__ = [
    "FinalMorphIssuerEvidence",
    "IssuerAdmissionEvidence",
    "IssuerEventEvidence",
    "IssuerShapeEvidence",
    "IssuerShapePoint",
    "LegacyReplayResult",
    "LegacyReplayUnavailable",
    "ReplayStage",
    "capture_issuer_evidence",
    "effective_plan_snapshot_digest",
    "replay_effective_shape_plan",
]
