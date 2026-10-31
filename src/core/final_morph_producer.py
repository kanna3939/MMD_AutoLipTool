"""Build and validate immutable MS30 candidate morph plans."""

from __future__ import annotations

import sys

_module_alias = __name__[4:] if __name__.startswith("src.") else "src." + __name__
sys.modules.setdefault(_module_alias, sys.modules[__name__])

import hashlib
import json
import math
from collections import defaultdict
from typing import Iterable

try:
    from src.core.canonical_morph_value import (
        POLICY_ID,
        CanonicalMorphValueError,
        canonicalize_morph_value,
    )
    from src.core.final_morph_plan import (
        CURVE_POLICY_ID,
        FinalMorphBuildResult,
        FinalMorphFullSnapshotIssuerContext,
        FinalMorphIdentityContext,
        FinalMorphIssue,
        FinalMorphPlan,
        FinalMorphPlanError,
        FinalMorphPoint,
        FinalMorphReplayEvidence,
        MorphPointRecord,
        MorphPointSource,
        MorphRequirement,
        MorphTransformation,
        STAGES,
        canonical_snapshot_value,
        create_plan,
        effective_plan_snapshot_digest,
        issue,
        is_global_silence_zero,
        required_zero_event_indices,
        resolved_shape_terminal,
        validate_plan_integrity,
        wire_digest_for_points,
    )
    from src.core.morph_name_sets import (
        SEMANTIC_VOWEL_ORDER,
        get_builtin_morph_name_set,
        validate_output_morph_names,
    )
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.canonical_morph_value", "src.core.final_morph_plan", "src.core.morph_name_sets"}:
        raise
    from core.canonical_morph_value import (
        POLICY_ID,
        CanonicalMorphValueError,
        canonicalize_morph_value,
    )
    from core.final_morph_plan import (
        CURVE_POLICY_ID,
        FinalMorphBuildResult,
        FinalMorphFullSnapshotIssuerContext,
        FinalMorphIdentityContext,
        FinalMorphIssue,
        FinalMorphPlan,
        FinalMorphPlanError,
        FinalMorphPoint,
        FinalMorphReplayEvidence,
        MorphPointRecord,
        MorphPointSource,
        MorphRequirement,
        MorphTransformation,
        STAGES,
        canonical_snapshot_value,
        create_plan,
        effective_plan_snapshot_digest,
        issue,
        is_global_silence_zero,
        required_zero_event_indices,
        resolved_shape_terminal,
        validate_plan_integrity,
        wire_digest_for_points,
    )
    from core.morph_name_sets import (
        SEMANTIC_VOWEL_ORDER,
        get_builtin_morph_name_set,
        validate_output_morph_names,
    )


def _base_plan_digest(base_input: object) -> str:
    try:
        from src.core.effective_shape_plan import build_base_plan_identity
    except ModuleNotFoundError as error:
        if error.name not in {"src", "src.core", "src.core.effective_shape_plan"}:
            raise
        from core.effective_shape_plan import build_base_plan_identity
    return build_base_plan_identity(base_input).digest


_UNAVAILABLE_REASONS = frozenset({"capture_unavailable", "terminal_evidence_missing"})


def make_identity_context(
    *,
    source_run_id: str,
    analysis_generation: int,
    manual_revision: int,
    base_input: object,
    effective_plan_snapshot: object,
    resolved_profile_id: str | None,
    morph_name_set_id: str,
    numeric_policy_id: str,
    curve_policy_id: str,
    silence_policy_id: str,
    crossfade_policy_id: str,
) -> FinalMorphIdentityContext:
    """Issue identity only from explicit metadata and complete digest inputs."""
    base_digest = _base_plan_digest(base_input)
    effective_digest = effective_plan_snapshot_digest(effective_plan_snapshot)
    mapping_set = get_builtin_morph_name_set(morph_name_set_id)
    mapping = tuple(zip(SEMANTIC_VOWEL_ORDER, mapping_set.output_names))
    return FinalMorphIdentityContext(
        source_run_id=source_run_id,
        analysis_generation=analysis_generation,
        base_plan_digest=base_digest,
        effective_plan_digest=effective_digest,
        manual_revision=manual_revision,
        resolved_profile_id=resolved_profile_id,
        output_mapping=mapping,
        numeric_policy_id=numeric_policy_id,
        curve_policy_id=curve_policy_id,
        silence_policy_id=silence_policy_id,
        crossfade_policy_id=crossfade_policy_id,
    )


def _unavailable_result(
    reason: str,
    *,
    baseline: tuple[tuple[int, str, float], ...] = (),
    evidence: object | None = None,
) -> FinalMorphBuildResult:
    return FinalMorphBuildResult(
        state="unavailable",
        plan=None,
        baseline_points=baseline,
        issues=(issue(reason, "capture"),),
        issuer_evidence=evidence,
    )


_ISSUER_EVIDENCE_FIELDS = (
    "source_run_id",
    "analysis_generation",
    "base_plan_digest",
    "effective_plan_digest",
    "manual_revision",
    "base_events",
    "effective_events",
    "shapes",
    "admissions",
    "required_zero_frames",
    "allowed_non_zero_ranges",
    "protected_event_ranges",
    "silence_core_frame_ranges",
    "manual_event_indices",
    "silence_policy_id",
    "effective_plan_snapshot_json",
)


def _issuer_event_signature(event: object) -> tuple[object, ...]:
    peak = float(getattr(event, "peak_value"))
    return (
        getattr(event, "base_event_index"),
        getattr(event, "vowel"),
        getattr(event, "start_frame"),
        getattr(event, "peak_frame"),
        getattr(event, "end_frame"),
        peak.hex(),
    )


def _derived_issuer_evidence_fields(effective_plan: object) -> dict[str, object]:
    base_events = tuple(
        _issuer_event_signature(item)
        for item in getattr(effective_plan, "base_events")
    )
    effective_events = tuple(
        _issuer_event_signature(item)
        for item in getattr(effective_plan, "effective_events")
    )
    shapes: list[tuple[object, ...]] = []
    for shape_ordinal, shape in enumerate(tuple(getattr(effective_plan, "shapes"))):
        semantic = getattr(shape, "vowel")
        base_indices = tuple(sorted(set(getattr(shape, "real_base_event_indices", ()))))
        points = tuple(
            (
                point_ordinal,
                getattr(point, "frame_no"),
                float(getattr(point, "value")).hex(),
                getattr(point, "point_kind"),
            )
            for point_ordinal, point in enumerate(tuple(getattr(shape, "control_points", ())))
        )
        terminal = points[-1] if points else None
        _, terminal_base_index, resolved = resolved_shape_terminal(
            shape, tuple(effective_plan.effective_events)
        )
        shapes.append(
            (
                shape_ordinal,
                semantic,
                base_indices,
                points,
                None if terminal is None else terminal[1],
                None if terminal is None else terminal[2],
                terminal_base_index,
                resolved,
            )
        )
    admissions = tuple(
        (
            getattr(item, "event_index"),
            getattr(item, "vowel"),
            tuple(getattr(item, "source_event_indices")),
            getattr(item, "enabled"),
            getattr(item, "boundary_only"),
            getattr(item, "boundary_frame"),
            tuple(getattr(item, "required_zero_frame_ranges")),
            getattr(item, "base_event_silence_core_overlap"),
        )
        for item in getattr(effective_plan, "event_silence_admissions")
    )
    contract = getattr(effective_plan, "normalization_contract")
    manual_indices = {
        getattr(item, "base_event_index")
        for item in getattr(
            getattr(effective_plan, "canonical_adjustment_snapshot"),
            "adjustments",
        )
        if not getattr(item, "is_empty", False)
    }
    for item in getattr(effective_plan, "manual_crossfades"):
        manual_indices.update(
            (
                getattr(item, "source_base_event_index"),
                getattr(item, "target_base_event_index"),
            )
        )
    payload = {
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
    snapshot_json = json.dumps(
        canonical_snapshot_value(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return {
        "base_events": base_events,
        "effective_events": effective_events,
        "shapes": tuple(shapes),
        "admissions": admissions,
        "required_zero_frames": tuple(contract.required_zero_frames),
        "allowed_non_zero_ranges": tuple(contract.allowed_non_zero_ranges),
        "protected_event_ranges": tuple(contract.protected_event_ranges),
        "silence_core_frame_ranges": tuple(
            getattr(effective_plan, "silence_core_frame_ranges") or ()
        ),
        "manual_event_indices": tuple(sorted(manual_indices)),
        "silence_policy_id": getattr(effective_plan, "silence_policy"),
        "effective_plan_snapshot_json": snapshot_json,
    }


def _issuer_evidence_matches_snapshot(evidence: object, effective_plan: object) -> bool:
    try:
        expected = _derived_issuer_evidence_fields(effective_plan)
        actual_events = {
            "base_events": tuple(
                (
                    getattr(item, "event_index"),
                    getattr(item, "semantic_morph"),
                    getattr(item, "start_frame"),
                    getattr(item, "peak_frame"),
                    getattr(item, "end_frame"),
                    getattr(item, "peak_value_hex"),
                )
                for item in getattr(evidence, "base_events")
            ),
            "effective_events": tuple(
                (
                    getattr(item, "event_index"),
                    getattr(item, "semantic_morph"),
                    getattr(item, "start_frame"),
                    getattr(item, "peak_frame"),
                    getattr(item, "end_frame"),
                    getattr(item, "peak_value_hex"),
                )
                for item in getattr(evidence, "effective_events")
            ),
            "shapes": tuple(
                (
                    getattr(item, "shape_ordinal"),
                    getattr(item, "semantic_morph"),
                    tuple(getattr(item, "base_event_indices")),
                    tuple(
                        (
                            getattr(point, "point_ordinal"),
                            getattr(point, "frame_no"),
                            getattr(point, "value_hex"),
                            getattr(point, "point_kind"),
                        )
                        for point in getattr(item, "points")
                    ),
                    getattr(item, "terminal_frame"),
                    getattr(item, "terminal_value_hex"),
                    getattr(item, "terminal_base_event_index"),
                    getattr(item, "terminal_resolved"),
                )
                for item in getattr(evidence, "shapes")
            ),
            "admissions": tuple(
                (
                    getattr(item, "event_index"),
                    getattr(item, "semantic_morph"),
                    tuple(getattr(item, "source_event_indices")),
                    getattr(item, "enabled"),
                    getattr(item, "boundary_only"),
                    getattr(item, "boundary_frame"),
                    tuple(getattr(item, "required_zero_frame_ranges")),
                    getattr(item, "core_overlap"),
                )
                for item in getattr(evidence, "admissions")
            ),
        }
        for name in ("base_events", "effective_events", "shapes", "admissions"):
            if actual_events[name] != expected[name]:
                return False
        for name in (
            "required_zero_frames",
            "allowed_non_zero_ranges",
            "protected_event_ranges",
            "silence_core_frame_ranges",
            "manual_event_indices",
            "silence_policy_id",
            "effective_plan_snapshot_json",
        ):
            if getattr(evidence, name) != expected[name]:
                return False
        return True
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError, FinalMorphPlanError):
        return False


def _full_snapshot_context_issues(
    expected_identity: FinalMorphIdentityContext | None,
    issuer_context: FinalMorphFullSnapshotIssuerContext | None,
) -> tuple[FinalMorphIssue, ...]:
    if issuer_context is None or not isinstance(issuer_context, FinalMorphFullSnapshotIssuerContext):
        return (issue("capture_unavailable", "issuer_context"),)
    required_context = (
        "input_kind",
        "identity_context",
        "base_input",
        "adjustment_snapshot",
        "effective_plan_snapshot",
        "issuer_evidence",
        "replay_evidence",
    )
    if any(getattr(issuer_context, field, None) is None for field in required_context):
        return (issue("capture_unavailable", "issuer_context"),)
    if issuer_context.input_kind not in {"synthetic_snapshot", "captured_snapshot"}:
        return (issue("capture_unavailable", "issuer_context"),)
    identity = issuer_context.identity_context
    evidence = issuer_context.issuer_evidence
    replay_evidence = issuer_context.replay_evidence
    if not isinstance(identity, FinalMorphIdentityContext):
        return (issue("capture_unavailable", "identity"),)
    if not isinstance(replay_evidence, FinalMorphReplayEvidence):
        return (issue("capture_unavailable", "replay_evidence"),)
    if any(not hasattr(evidence, field) for field in _ISSUER_EVIDENCE_FIELDS):
        return (issue("capture_unavailable", "issuer_evidence"),)

    issues: list[FinalMorphIssue] = []
    if expected_identity is not None and identity != expected_identity:
        issues.append(issue("identity_mismatch", "identity"))
    try:
        computed_base_digest = _base_plan_digest(issuer_context.base_input)
        computed_effective_digest = effective_plan_snapshot_digest(
            issuer_context.effective_plan_snapshot
        )
        effective_plan_base_digest = issuer_context.effective_plan_snapshot.base_plan_identity.digest
        adjustment_snapshot = issuer_context.adjustment_snapshot
        recorded_adjustment_snapshot = (
            issuer_context.effective_plan_snapshot.canonical_adjustment_snapshot
        )
        encoded_evidence_snapshot = evidence.effective_plan_snapshot_json.encode("utf-8")
        evidence_snapshot_digest = hashlib.sha256(encoded_evidence_snapshot).hexdigest()
        evidence_snapshot = json.loads(evidence.effective_plan_snapshot_json)
        evidence_snapshot_base_digest = evidence_snapshot["base_plan_identity"]["digest"]
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
        return (issue("identity_mismatch", "issuer_snapshot"),)

    if (
        computed_base_digest != identity.base_plan_digest
        or computed_base_digest != evidence.base_plan_digest
        or computed_base_digest != effective_plan_base_digest
        or computed_base_digest != evidence_snapshot_base_digest
        or computed_effective_digest != identity.effective_plan_digest
        or computed_effective_digest != evidence.effective_plan_digest
        or computed_effective_digest != evidence_snapshot_digest
        or adjustment_snapshot != recorded_adjustment_snapshot
        or getattr(adjustment_snapshot, "base_plan_identity", None)
        != issuer_context.effective_plan_snapshot.base_plan_identity
        or identity.silence_policy_id != issuer_context.effective_plan_snapshot.silence_policy
    ):
        issues.append(issue("identity_mismatch", "issuer_snapshot"))

    if not _issuer_evidence_matches_snapshot(
        evidence,
        issuer_context.effective_plan_snapshot,
    ):
        issues.append(issue("provenance_missing", "issuer_evidence"))

    if (
        identity.source_run_id != evidence.source_run_id
        or identity.analysis_generation != evidence.analysis_generation
        or identity.base_plan_digest != evidence.base_plan_digest
        or identity.effective_plan_digest != evidence.effective_plan_digest
        or identity.manual_revision != evidence.manual_revision
        or identity.silence_policy_id != evidence.silence_policy_id
    ):
        issues.append(issue("identity_mismatch", "identity"))
    return tuple(_deduplicate_issues(issues))


def _create_candidate_plan(
    replay: object,
    issuer_context: FinalMorphFullSnapshotIssuerContext,
) -> tuple[FinalMorphPlan | None, tuple[FinalMorphIssue, ...]]:
    evidence = issuer_context.issuer_evidence
    identity = issuer_context.identity_context
    issues: list[FinalMorphIssue] = []
    context_issues = _full_snapshot_context_issues(identity, issuer_context)
    if any(item.reason == "capture_unavailable" for item in context_issues):
        return None, context_issues
    issues.extend(context_issues)
    issues.extend(
        issue(reason, "capture" if reason == "capture_unavailable" else "issuer_snapshot")
        for reason in replay.capture_issues
    )
    unresolved_shapes = tuple(shape for shape in evidence.shapes if not shape.terminal_resolved)
    for shape in unresolved_shapes:
        issues.append(
            issue(
                "terminal_evidence_missing",
                "requirements",
                semantic_morph=shape.semantic_morph,
                frame_range=(
                    shape.terminal_frame if shape.terminal_frame is not None else 0,
                    shape.terminal_frame if shape.terminal_frame is not None else 0,
                ),
            )
        )

    normalized_records = replay.records_for("legacy_merge_final")
    order = {semantic: index for index, semantic in enumerate(SEMANTIC_VOWEL_ORDER)}
    sorted_records = tuple(
        sorted(normalized_records, key=lambda record: (record.frame_no, order[record.semantic_morph]))
    )
    canonical_records: list[MorphPointRecord] = []
    points: list[FinalMorphPoint] = []
    transformations: list[MorphTransformation] = [
        item for item in replay.transformations if item.stage != "canonical"
    ]
    for ordinal, record in enumerate(sorted_records):
        try:
            raw_value = float.fromhex(record.value_hex)
            if not math.isfinite(raw_value) or raw_value < 0.0:
                raise CanonicalMorphValueError("legacy output is not finite and non-negative")
            canonical_value = canonicalize_morph_value(raw_value)
        except (CanonicalMorphValueError, ValueError, OverflowError) as error:
            issues.append(
                issue(
                    "numeric_invalid",
                    "legacy_merge_final",
                    semantic_morph=record.semantic_morph,
                    frame_range=(record.frame_no, record.frame_no),
                )
            )
            return None, tuple(issues)
        canonical_record = MorphPointRecord(
            record_id=f"record:canonical:{ordinal}",
            stage="canonical",
            ordinal=ordinal,
            frame_no=record.frame_no,
            semantic_morph=record.semantic_morph,
            value_hex=canonical_value.scalar.hex(),
            source_ids=record.source_ids,
            required_reasons=record.required_reasons,
        )
        canonical_records.append(canonical_record)
        points.append(
            FinalMorphPoint(
                point_id=f"key:{record.semantic_morph}:{record.frame_no}",
                record_id=canonical_record.record_id,
                frame_no=record.frame_no,
                semantic_morph=record.semantic_morph,
                value=canonical_value,
                source_ids=record.source_ids,
                required_reasons=record.required_reasons,
            )
        )
        changed = canonical_value.scalar != raw_value
        transformations.append(
            MorphTransformation(
                transformation_id=f"transform:canonical:{ordinal}",
                stage="canonical",
                ordinal=ordinal,
                reason="b1_canonical_numeric_policy",
                input_record_ids=(record.record_id,),
                output_record_ids=(canonical_record.record_id,),
                protection_status="canonicalized" if changed else "preserved",
            )
        )

    baseline_by_key = {
        (frame_no, semantic): value_hex
        for frame_no, semantic, value_hex in replay.baseline_wire_values
    }
    for point in points:
        expected_hex = baseline_by_key.get((point.frame_no, point.semantic_morph))
        if expected_hex is None or point.value.binary32_hex != expected_hex:
            issues.append(
                issue(
                    "baseline_mismatch",
                    "canonical",
                    point_ids=(point.point_id,),
                    semantic_morph=point.semantic_morph,
                    frame_range=(point.frame_no, point.frame_no),
                )
            )

    records = tuple(
        record
        for stage in replay.stages
        if stage.stage != "canonical"
        for record in stage.records
    ) + tuple(canonical_records)
    records = tuple(
        sorted(records, key=lambda item: (STAGES.index(item.stage), item.ordinal))
    )
    try:
        plan = create_plan(
            identity_context=identity,
            points=tuple(points),
            point_records=records,
            source_records=replay.sources,
            requirements=replay.requirements,
            transformations=tuple(
                sorted(transformations, key=lambda item: (STAGES.index(item.stage), item.ordinal))
            ),
        )
    except (FinalMorphPlanError, ValueError, TypeError) as error:
        issues.append(issue("input_invalid", "plan"))
        return None, tuple(issues)
    issues.extend(validate_final_morph_plan(plan, issuer_context))
    return plan, tuple(_deduplicate_issues(issues))


def build_from_replay(
    replay: object,
    issuer_context: FinalMorphFullSnapshotIssuerContext,
) -> FinalMorphBuildResult:
    """Build from a replay and its separately supplied complete issuer context."""
    baseline = tuple(getattr(replay, "baseline_points", ()))
    context_issues = _full_snapshot_context_issues(
        getattr(issuer_context, "identity_context", None),
        issuer_context,
    )
    if any(item.reason == "capture_unavailable" for item in context_issues):
        return _unavailable_result(
            "capture_unavailable",
            baseline=baseline,
            evidence=issuer_context,
        )
    if context_issues:
        return FinalMorphBuildResult(
            state="invalid",
            plan=None,
            baseline_points=baseline,
            issues=context_issues,
            issuer_evidence=issuer_context,
        )
    if getattr(replay, "issuer_context", None) != issuer_context:
        context_issues = (*context_issues, issue("identity_mismatch", "replay_context"))
    plan, issues = _create_candidate_plan(replay, issuer_context)
    issues = tuple(_deduplicate_issues((*context_issues, *issues)))
    return FinalMorphBuildResult(
        state=_state_for_issues(issues),
        plan=plan,
        baseline_points=baseline,
        issues=issues,
        issuer_evidence=issuer_context,
    )


def build_final_morph_candidate(
    replay: object,
    issuer_context: FinalMorphFullSnapshotIssuerContext,
) -> FinalMorphBuildResult:
    """Pure producer entry point requiring a complete, explicit issuer context."""
    return build_from_replay(replay, issuer_context)


def _deduplicate_issues(issues: Iterable[FinalMorphIssue]) -> tuple[FinalMorphIssue, ...]:
    by_key: dict[tuple[object, ...], FinalMorphIssue] = {}
    for item in issues:
        key = (
            item.reason,
            item.stage,
            item.point_ids,
            item.requirement_ids,
            item.semantic_morph,
            item.frame_range,
        )
        by_key[key] = item
    return tuple(
        by_key[key]
        for key in sorted(by_key, key=lambda item: tuple("" if part is None else str(part) for part in item))
    )


def _state_for_issues(issues: Iterable[FinalMorphIssue]) -> str:
    items = tuple(issues)
    if any(item.reason in _UNAVAILABLE_REASONS for item in items):
        return "unavailable"
    return "invalid" if items else "valid"


def _replay_binding_issues(
    plan: FinalMorphPlan,
    replay: FinalMorphReplayEvidence,
) -> tuple[FinalMorphIssue, ...]:
    issues: list[FinalMorphIssue] = []
    if replay.capture_issues:
        issues.append(issue("provenance_missing", "replay_capture"))
    expected_by_stage = {item.stage: item.records for item in replay.stages}
    actual_by_stage = {
        stage: tuple(item for item in plan.point_records if item.stage == stage)
        for stage in STAGES
    }
    for stage in STAGES[:-1]:
        if actual_by_stage[stage] != expected_by_stage[stage]:
            issues.append(issue("provenance_missing", stage))
    if plan.source_records != replay.sources:
        issues.append(issue("provenance_missing", "source_registry"))
    if plan.requirements != replay.requirements:
        issues.append(issue("provenance_missing", "requirements"))

    final_records = tuple(
        sorted(
            expected_by_stage["legacy_merge_final"],
            key=lambda item: (
                item.frame_no,
                SEMANTIC_VOWEL_ORDER.index(item.semantic_morph),
            ),
        )
    )
    expected_baseline = tuple(
        (record.frame_no, record.semantic_morph, float.fromhex(record.value_hex))
        for record in final_records
    )
    if expected_baseline != replay.baseline_points:
        issues.append(issue("baseline_mismatch", "legacy_merge_final"))

    canonical_records: list[MorphPointRecord] = []
    expected_points: list[FinalMorphPoint] = []
    canonical_transforms: list[MorphTransformation] = []
    for ordinal, record in enumerate(final_records):
        try:
            canonical_value = canonicalize_morph_value(float.fromhex(record.value_hex))
        except (CanonicalMorphValueError, ValueError, OverflowError):
            issues.append(
                issue(
                    "numeric_invalid",
                    "legacy_merge_final",
                    semantic_morph=record.semantic_morph,
                    frame_range=(record.frame_no, record.frame_no),
                )
            )
            continue
        canonical_record = MorphPointRecord(
            record_id=f"record:canonical:{ordinal}",
            stage="canonical",
            ordinal=ordinal,
            frame_no=record.frame_no,
            semantic_morph=record.semantic_morph,
            value_hex=canonical_value.scalar.hex(),
            source_ids=record.source_ids,
            required_reasons=record.required_reasons,
        )
        canonical_records.append(canonical_record)
        expected_points.append(
            FinalMorphPoint(
                point_id=f"key:{record.semantic_morph}:{record.frame_no}",
                record_id=canonical_record.record_id,
                frame_no=record.frame_no,
                semantic_morph=record.semantic_morph,
                value=canonical_value,
                source_ids=record.source_ids,
                required_reasons=record.required_reasons,
            )
        )
        changed = canonical_value.scalar != float.fromhex(record.value_hex)
        canonical_transforms.append(
            MorphTransformation(
                transformation_id=f"transform:canonical:{ordinal}",
                stage="canonical",
                ordinal=ordinal,
                reason="b1_canonical_numeric_policy",
                input_record_ids=(record.record_id,),
                output_record_ids=(canonical_record.record_id,),
                protection_status="canonicalized" if changed else "preserved",
            )
        )
    if actual_by_stage["canonical"] != tuple(canonical_records):
        issues.append(issue("provenance_missing", "canonical"))
    if plan.points != tuple(expected_points):
        issues.append(issue("provenance_missing", "canonical"))

    expected_transformations = tuple(
        sorted(
            (
                *(item for item in replay.transformations if item.stage != "canonical"),
                *canonical_transforms,
            ),
            key=lambda item: (STAGES.index(item.stage), item.ordinal),
        )
    )
    if plan.transformations != expected_transformations:
        issues.append(issue("provenance_missing", "transformations"))

    expected_wire = tuple(
        (
            point.frame_no,
            point.semantic_morph,
            point.value.binary32_hex,
        )
        for point in expected_points
    )
    if expected_wire != replay.baseline_wire_values:
        issues.append(issue("baseline_mismatch", "canonical"))
    return tuple(_deduplicate_issues(issues))


def validate_final_morph_plan(
    plan: FinalMorphPlan,
    issuer_context: FinalMorphFullSnapshotIssuerContext | None,
) -> tuple[FinalMorphIssue, ...]:
    """Validate against complete inputs and separately supplied issuer evidence."""
    issues: list[FinalMorphIssue] = []
    try:
        validate_plan_integrity(plan)
    except (FinalMorphPlanError, TypeError, ValueError):
        return (issue("identity_mismatch", "serializer"),)
    context_issues = _full_snapshot_context_issues(plan.identity_context, issuer_context)
    if context_issues:
        return context_issues
    if issuer_context is None or issuer_context.issuer_evidence is None:
        return (issue("capture_unavailable", "issuer_evidence"),)
    replay_evidence = issuer_context.replay_evidence
    if not isinstance(replay_evidence, FinalMorphReplayEvidence):
        return (issue("capture_unavailable", "replay_evidence"),)
    issues.extend(_replay_binding_issues(plan, replay_evidence))
    issuer_evidence = issuer_context.issuer_evidence
    identity = plan.identity_context

    source_by_id = {item.source_id: item for item in plan.source_records}
    record_by_id = {item.record_id: item for item in plan.point_records}
    requirement_by_id = {item.requirement_id: item for item in plan.requirements}
    shape_by_ordinal = {item.shape_ordinal: item for item in issuer_evidence.shapes}
    base_event_by_index = {item.event_index: item for item in issuer_evidence.base_events}
    if len(source_by_id) != len(plan.source_records) or len(record_by_id) != len(plan.point_records):
        issues.append(issue("input_invalid", "registry"))
    if len(requirement_by_id) != len(plan.requirements):
        issues.append(issue("input_invalid", "requirements"))

    # Snapshot-evidence check: source coordinates, raw values, and event
    # ownership must match the separately supplied frozen issuer snapshot.
    expected_shape_sources = {
        f"{identity.source_run_id}:shape:{shape.shape_ordinal}:point:{point.point_ordinal}"
        for shape in issuer_evidence.shapes
        for point in shape.points
    }
    actual_shape_sources = {
        source.source_id
        for source in plan.source_records
        if source.issuer_kind == "shape_point"
    }
    if actual_shape_sources != expected_shape_sources:
        issues.append(issue("provenance_missing", "source_registry"))
    for shape in issuer_evidence.shapes:
        terminal = shape.points[-1] if shape.points else None
        snapshot_shape = issuer_context.effective_plan_snapshot.shapes[shape.shape_ordinal]
        _, _, expected_terminal_resolved = resolved_shape_terminal(
            snapshot_shape, tuple(issuer_context.effective_plan_snapshot.effective_events)
        )
        if not expected_terminal_resolved:
            issues.append(issue("terminal_evidence_missing", "requirements"))
        if (
            shape.terminal_resolved != expected_terminal_resolved
            or shape.terminal_frame != (None if terminal is None else terminal.frame_no)
            or shape.terminal_value_hex != (None if terminal is None else terminal.value_hex)
        ):
            issues.append(issue("provenance_missing", "terminal_evidence"))
        if shape.terminal_base_event_index is not None:
            terminal_event = base_event_by_index.get(shape.terminal_base_event_index)
            if terminal_event is None or terminal_event.semantic_morph != shape.semantic_morph:
                issues.append(issue("provenance_missing", "terminal_evidence"))
    raw_records_by_source: dict[str, list[MorphPointRecord]] = defaultdict(list)
    for record in plan.point_records:
        if record.stage == "raw_shape":
            for source_id in record.source_ids:
                raw_records_by_source[source_id].append(record)
    for source in plan.source_records:
        if source.issuer_kind == "shape_point":
            shape = shape_by_ordinal.get(source.shape_ordinal)
            if shape is None or source.point_ordinal is None or source.point_ordinal >= len(shape.points):
                issues.append(issue("provenance_missing", "source_registry"))
                continue
            point_evidence = shape.points[source.point_ordinal]
            expected_id = (
                f"{identity.source_run_id}:shape:{source.shape_ordinal}:point:{source.point_ordinal}"
            )
            expected_origin = (
                "manual"
                if set(shape.base_event_indices).intersection(issuer_evidence.manual_event_indices)
                else "automatic"
                if shape.base_event_indices
                else "unknown"
            )
            raw_rows = raw_records_by_source.get(source.source_id, [])
            if (
                source.source_id != expected_id
                or source.issuer_id != expected_id
                or shape.semantic_morph not in SEMANTIC_VOWEL_ORDER
                or source.base_event_indices != shape.base_event_indices
                or source.point_kind != point_evidence.point_kind
                or source.intent_origin != expected_origin
                or len(raw_rows) != 1
                or raw_rows[0].frame_no != point_evidence.frame_no
                or raw_rows[0].semantic_morph != shape.semantic_morph
                or raw_rows[0].value_hex != point_evidence.value_hex
                or raw_rows[0].source_ids != (source.source_id,)
            ):
                issues.append(issue("provenance_missing", "source_registry"))
            for event_index in source.base_event_indices:
                event = base_event_by_index.get(event_index)
                if event is None or event.semantic_morph != shape.semantic_morph:
                    issues.append(issue("provenance_missing", "source_registry"))
                    break
        else:
            requirement = requirement_by_id.get(source.issuer_id)
            expected_source_id = f"{identity.source_run_id}:requirement:{source.issuer_id}"
            if (
                requirement is None
                or source.source_id not in requirement.source_ids
                or source.source_id != expected_source_id
                or source.intent_origin != "automatic"
                or source.point_kind != requirement.kind
            ):
                issues.append(issue("provenance_missing", "source_registry"))
            if any(event_index not in base_event_by_index for event_index in source.base_event_indices):
                issues.append(issue("provenance_missing", "source_registry"))

    expected_requirements: dict[
        str, tuple[str, str, int, int, tuple[str, ...], tuple[int, ...], str]
    ] = {}
    shape_sources_at_key: dict[tuple[str, int], set[str]] = defaultdict(set)
    for shape in issuer_evidence.shapes:
        for point in shape.points:
            shape_sources_at_key[(shape.semantic_morph, point.frame_no)].add(
                f"{identity.source_run_id}:shape:{shape.shape_ordinal}:point:{point.point_ordinal}"
            )
    for semantic, frame_no in set(issuer_evidence.required_zero_frames):
        requirement_id = f"requirement:required_zero:{semantic}:{frame_no}"
        source_id = f"{identity.source_run_id}:requirement:{requirement_id}"
        event_indices = required_zero_event_indices(
            issuer_context.effective_plan_snapshot, semantic, frame_no
        )
        if not event_indices and not is_global_silence_zero(
            issuer_context.effective_plan_snapshot, frame_no
        ):
            issues.append(issue("capture_unavailable", "requirements"))
        source_ids = tuple(
            sorted({source_id, *shape_sources_at_key.get((semantic, frame_no), set())})
        )
        expected_requirements[requirement_id] = (
            "required_zero",
            semantic,
            frame_no,
            frame_no,
            source_ids,
            event_indices,
            "effective_plan_required_zero",
        )
    for start_frame, end_frame in issuer_evidence.silence_core_frame_ranges:
        for semantic in SEMANTIC_VOWEL_ORDER:
            requirement_id = (
                f"requirement:silence_core:{semantic}:{start_frame}:{end_frame}"
            )
            source_id = f"{identity.source_run_id}:requirement:{requirement_id}"
            expected_requirements[requirement_id] = (
                "silence_core",
                semantic,
                start_frame,
                end_frame,
                (source_id,),
                (),
                "effective_plan_silence_core",
            )
    for shape in issuer_evidence.shapes:
        if not shape.terminal_resolved or shape.terminal_frame is None:
            continue
        requirement_id = (
            f"requirement:per_morph_terminal:{shape.semantic_morph}:"
            f"{shape.shape_ordinal}:{shape.terminal_frame}"
        )
        source_id = f"{identity.source_run_id}:requirement:{requirement_id}"
        point_source_id = (
            f"{identity.source_run_id}:shape:{shape.shape_ordinal}:"
            f"point:{len(shape.points) - 1}"
        )
        expected_requirements[requirement_id] = (
            "per_morph_terminal",
            shape.semantic_morph,
            shape.terminal_frame,
            shape.terminal_frame,
            tuple(sorted({source_id, point_source_id})),
            (
                (shape.terminal_base_event_index,)
                if shape.terminal_base_event_index is not None
                else shape.base_event_indices
            ),
            "resolved_shape_group_terminal",
        )
    if set(requirement_by_id) != set(expected_requirements):
        issues.append(issue("provenance_missing", "requirements"))
    for requirement_id, expected in expected_requirements.items():
        requirement = requirement_by_id.get(requirement_id)
        kind, semantic, start, end, source_ids, event_indices, reason = expected
        if (
            requirement is None
            or requirement.kind != kind
            or requirement.semantic_morph != semantic
            or requirement.start_frame != start
            or requirement.end_frame != end
            or requirement.source_ids != source_ids
            or requirement.reason != reason
        ):
            issues.append(
                issue(
                    "provenance_missing",
                    "requirements",
                    requirement_ids=(requirement_id,),
                )
            )
        requirement_source_id = f"{identity.source_run_id}:requirement:{requirement_id}"
        requirement_source = source_by_id.get(requirement_source_id)
        if (
            requirement_source is None
            or requirement_source.issuer_id != requirement_id
            or requirement_source.base_event_indices != event_indices
        ):
            issues.append(
                issue(
                    "provenance_missing",
                    "source_registry",
                    requirement_ids=(requirement_id,),
                )
            )

    # Every record and requirement reference resolves, including points deleted
    # by an earlier normalization stage.
    for record in plan.point_records:
        if any(source_id not in source_by_id for source_id in record.source_ids):
            issues.append(issue("provenance_missing", record.stage))
    for requirement in plan.requirements:
        if any(source_id not in source_by_id for source_id in requirement.source_ids):
            issues.append(
                issue(
                    "provenance_missing",
                    "requirements",
                    requirement_ids=(requirement.requirement_id,),
                )
            )

    # Stage ordering, unique IDs and complete input/output explanation.
    stage_ordinals: dict[str, list[int]] = defaultdict(list)
    for record in plan.point_records:
        stage_ordinals[record.stage].append(record.ordinal)
        if record.record_id != f"record:{record.stage}:{record.ordinal}":
            issues.append(issue("input_invalid", "registry"))
    for stage, ordinals in stage_ordinals.items():
        if ordinals != list(range(len(ordinals))):
            issues.append(issue("input_invalid", "registry"))
    expected_record_order = tuple(
        sorted(plan.point_records, key=lambda item: (STAGES.index(item.stage), item.ordinal))
    )
    if expected_record_order != plan.point_records:
        issues.append(issue("input_invalid", "registry"))
    transformation_ids = [item.transformation_id for item in plan.transformations]
    if len(set(transformation_ids)) != len(transformation_ids):
        issues.append(issue("input_invalid", "transformations"))
    expected_transform_order = tuple(
        sorted(plan.transformations, key=lambda item: (STAGES.index(item.stage), item.ordinal))
    )
    if expected_transform_order != plan.transformations:
        issues.append(issue("input_invalid", "transformations"))

    previous_stage = {STAGES[index]: STAGES[index - 1] for index in range(1, len(STAGES))}
    for stage, predecessor in previous_stage.items():
        before = {item.record_id: item for item in plan.point_records if item.stage == predecessor}
        after = {item.record_id: item for item in plan.point_records if item.stage == stage}
        transitions = tuple(item for item in plan.transformations if item.stage == stage)
        input_coverage: list[str] = []
        output_coverage: list[str] = []
        for transition in transitions:
            if any(record_id not in before for record_id in transition.input_record_ids):
                issues.append(issue("input_invalid", "transformations"))
            if any(record_id not in after for record_id in transition.output_record_ids):
                issues.append(issue("input_invalid", "transformations"))
            input_coverage.extend(transition.input_record_ids)
            output_coverage.extend(transition.output_record_ids)
            if not transition.input_record_ids:
                if stage != "legacy_input" or not transition.output_record_ids:
                    issues.append(issue("provenance_missing", "transformations"))
                else:
                    out_record = after[transition.output_record_ids[0]]
                    requirement_source_ids = {
                        source_id
                        for source_id in out_record.source_ids
                        if source_id in source_by_id
                        and source_by_id[source_id].issuer_kind == "requirement"
                    }
                    referenced_requirements = [
                        requirement
                        for requirement in plan.requirements
                        if any(
                            source_id in requirement.source_ids
                            and source_id in requirement_source_ids
                            for source_id in out_record.source_ids
                        )
                    ]
                    if (
                        not requirement_source_ids
                        or not any(requirement.kind == "required_zero" for requirement in referenced_requirements)
                        or any(
                            # The core boundary zero can also be an existing
                            # group terminal. Keep both co-located obligations.
                            requirement.kind not in {"required_zero", "per_morph_terminal"}
                            or requirement.semantic_morph != out_record.semantic_morph
                            or requirement.start_frame != out_record.frame_no
                            or requirement.end_frame != out_record.frame_no
                            or float.fromhex(out_record.value_hex) != 0.0
                            for requirement in referenced_requirements
                        )
                    ):
                        issues.append(issue("provenance_missing", "transformations"))
            elif len(transition.output_record_ids) > 1:
                issues.append(issue("input_invalid", "transformations"))
            if transition.input_record_ids and transition.output_record_ids:
                in_records = [before[item] for item in transition.input_record_ids]
                out_record = after[transition.output_record_ids[0]]
                combined_sources = tuple(sorted({source for item in in_records for source in item.source_ids}))
                requirement_sources = {
                    source_id
                    for source_id in out_record.source_ids
                    if source_id in source_by_id
                    and source_by_id[source_id].issuer_kind == "requirement"
                    and any(
                        source_id in requirement.source_ids
                        for requirement in plan.requirements
                    )
                    and stage == "legacy_input"
                }
                combined_sources = tuple(sorted(set(combined_sources) | requirement_sources))
                combined_reasons = tuple(sorted({reason for item in in_records for reason in item.required_reasons}))
                if out_record.source_ids != combined_sources or out_record.required_reasons != combined_reasons:
                    issues.append(issue("provenance_missing", stage))
        if sorted(input_coverage) != sorted(before):
            issues.append(issue("input_invalid", "transformations"))
        if sorted(output_coverage) != sorted(after):
            issues.append(issue("input_invalid", "transformations"))

    # Candidate points use the final canonical registry exactly once and in
    # fixed semantic order. Duplicate keys are never resolved by last/max here.
    point_records_by_id = record_by_id
    key_order = {semantic: index for index, semantic in enumerate(SEMANTIC_VOWEL_ORDER)}
    keys: list[tuple[int, int]] = []
    point_ids: set[str] = set()
    for point in plan.points:
        expected_point_id = f"key:{point.semantic_morph}:{point.frame_no}"
        record = point_records_by_id.get(point.record_id)
        if (
            point.point_id != expected_point_id
            or point.point_id in point_ids
            or record is None
            or record.stage != "canonical"
            or record.frame_no != point.frame_no
            or record.semantic_morph != point.semantic_morph
            or record.value_hex != point.value.scalar.hex()
            or record.source_ids != point.source_ids
            or record.required_reasons != point.required_reasons
        ):
            issues.append(issue("input_invalid", "canonical"))
        point_ids.add(point.point_id)
        keys.append((point.frame_no, key_order[point.semantic_morph]))
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        issues.append(issue("collision_unresolved", "canonical"))
    canonical_records = tuple(item for item in plan.point_records if item.stage == "canonical")
    if {item.record_id for item in canonical_records} != {item.record_id for item in plan.points}:
        issues.append(issue("input_invalid", "canonical"))

    # Unequal values at one same-morph/frame key are semantic ambiguity even if
    # legacy max happened to reproduce the saved result.
    for transition in plan.transformations:
        if transition.stage not in {"legacy_merge_initial", "legacy_merge_final"}:
            continue
        if len(transition.input_record_ids) < 2 or len(transition.output_record_ids) != 1:
            continue
        inputs = [record_by_id[item] for item in transition.input_record_ids if item in record_by_id]
        values = {item.value_hex for item in inputs}
        if len(values) > 1:
            has_required = any(item.required_reasons for item in inputs)
            output = record_by_id.get(transition.output_record_ids[0])
            issues.append(
                issue(
                    "collision_unresolved",
                    transition.stage,
                    semantic_morph=None if output is None else output.semantic_morph,
                    frame_range=None if output is None else (output.frame_no, output.frame_no),
                )
            )
        elif any(item.value_hex == 0.0.hex() for item in inputs) and any(
            float.fromhex(item.value_hex) > 0.0 for item in inputs
        ):
            issues.append(issue("collision_unresolved", transition.stage))

    # Manual/unknown intent and every positive raw point are protected from
    # unproven legacy changes. No value-only epsilon classifies intent.
    raw_records = tuple(item for item in plan.point_records if item.stage == "raw_shape")
    protected_source_ids = {
        source.source_id
        for source in plan.source_records
        if source.intent_origin in {"manual", "unknown"}
    }
    protected_source_ids.update(
        source_id
        for record in raw_records
        if float.fromhex(record.value_hex) > 0.0
        for source_id in record.source_ids
    )
    for source_id in protected_source_ids:
        source_raw = next((r for r in raw_records if source_id in r.source_ids), None)
        if source_raw is None:
            issues.append(issue("provenance_missing", "raw_shape"))
            continue
        for stage in STAGES[1:-1]:
            descendants = [
                item
                for item in plan.point_records
                if item.stage == stage and source_id in item.source_ids
            ]
            if not descendants:
                issues.append(issue("protected_change_unexplained", stage))
                break
            if any(item.value_hex != source_raw.value_hex for item in descendants):
                issues.append(
                    issue(
                        "protected_change_unexplained",
                        stage,
                        semantic_morph=source_raw.semantic_morph,
                        frame_range=(source_raw.frame_no, source_raw.frame_no),
                    )
                )
                break

    # Requirements bind to captured issuer fields. Missing terminal evidence is
    # unavailable; a captured mismatch is an invalid candidate.
    for requirement in plan.requirements:
        if requirement.kind == "required_zero":
            if (requirement.semantic_morph, requirement.start_frame) not in set(
                issuer_evidence.required_zero_frames
            ):
                issues.append(issue("identity_mismatch", "requirements", requirement_ids=(requirement.requirement_id,)))
        elif requirement.kind == "silence_core":
            if (requirement.start_frame, requirement.end_frame) not in set(
                issuer_evidence.silence_core_frame_ranges
            ):
                issues.append(issue("identity_mismatch", "requirements", requirement_ids=(requirement.requirement_id,)))
        elif requirement.kind == "per_morph_terminal":
            matched = any(
                shape.terminal_resolved
                and shape.semantic_morph == requirement.semantic_morph
                and shape.terminal_frame == requirement.start_frame
                for shape in issuer_evidence.shapes
            )
            if not matched:
                issues.append(
                    issue(
                        "terminal_evidence_missing",
                        "requirements",
                        requirement_ids=(requirement.requirement_id,),
                        semantic_morph=requirement.semantic_morph,
                        frame_range=(requirement.start_frame, requirement.end_frame),
                    )
                )

    final_key_values = {
        (point.semantic_morph, point.frame_no): point.value.scalar
        for point in plan.points
    }
    for requirement in plan.requirements:
        if requirement.kind in {"required_zero", "per_morph_terminal"}:
            value = final_key_values.get((requirement.semantic_morph, requirement.start_frame))
            if value is None or value != 0.0:
                reason = "required_zero_missing"
                if requirement.kind == "per_morph_terminal":
                    reason = "required_zero_missing"
                issues.append(
                    issue(
                        reason,
                        "canonical",
                        requirement_ids=(requirement.requirement_id,),
                        semantic_morph=requirement.semantic_morph,
                        frame_range=(requirement.start_frame, requirement.end_frame),
                    )
                )
        elif requirement.kind == "silence_core":
            core_issues = _validate_silence_core(plan, requirement)
            issues.extend(core_issues)

    # Identity/policy and mapping invariants are repeated at the pure-validator
    # boundary so a caller cannot rely only on a serialized digest.
    try:
        validated_names = validate_output_morph_names(tuple(name for _, name in plan.output_mapping))
    except ValueError:
        validated_names = ()
    if (
        plan.identity_context.numeric_policy_id != POLICY_ID
        or plan.identity_context.curve_policy_id != CURVE_POLICY_ID
        or validated_names != tuple(name for _, name in plan.output_mapping)
        or plan.output_mapping != plan.identity_context.output_mapping
    ):
        issues.append(issue("mapping_invalid", "mapping"))
    try:
        if wire_digest_for_points(plan.points, plan.output_mapping) != plan.wire_digest:
            issues.append(issue("wire_unrepresentable", "wire"))
    except (FinalMorphPlanError, UnicodeError, ValueError, OverflowError):
        issues.append(issue("wire_unrepresentable", "wire"))
    return _deduplicate_issues(issues)


def _validate_silence_core(
    plan: FinalMorphPlan,
    requirement: MorphRequirement,
) -> tuple[FinalMorphIssue, ...]:
    semantic = requirement.semantic_morph
    start = requirement.start_frame
    end = requirement.end_frame
    keys = sorted(
        (point.frame_no, point.value.scalar)
        for point in plan.points
        if point.semantic_morph == semantic
    )
    if not keys:
        return (
            issue(
                "capture_unavailable",
                "canonical",
                requirement_ids=(requirement.requirement_id,),
                semantic_morph=semantic,
                frame_range=(start, end),
            ),
        )
    first_frame, _ = keys[0]
    last_frame, _ = keys[-1]
    if start < first_frame or end > last_frame or (start < end and len(keys) < 2):
        return (
            issue(
                "capture_unavailable",
                "canonical",
                requirement_ids=(requirement.requirement_id,),
                semantic_morph=semantic,
                frame_range=(start, end),
            ),
        )
    violations: list[FinalMorphIssue] = []
    for frame_no, value in keys:
        if start <= frame_no <= end and value != 0.0:
            violations.append(
                issue(
                    "silence_core_violation",
                    "canonical",
                    requirement_ids=(requirement.requirement_id,),
                    semantic_morph=semantic,
                    frame_range=(frame_no, frame_no),
                )
            )
    for (left_frame, left_value), (right_frame, right_value) in zip(keys, keys[1:]):
        if right_frame <= left_frame or right_frame < start or left_frame > end:
            continue
        overlap_start = max(start, left_frame)
        overlap_end = min(end, right_frame)
        span = right_frame - left_frame
        at_start = left_value + (right_value - left_value) * ((overlap_start - left_frame) / span)
        at_end = left_value + (right_value - left_value) * ((overlap_end - left_frame) / span)
        if at_start != 0.0 or at_end != 0.0:
            violations.append(
                issue(
                    "silence_core_violation",
                    "canonical",
                    requirement_ids=(requirement.requirement_id,),
                    semantic_morph=semantic,
                    frame_range=(overlap_start, overlap_end),
                )
            )
    return tuple(violations)


__all__ = [
    "build_final_morph_candidate",
    "build_from_replay",
    "make_identity_context",
    "validate_final_morph_plan",
]
