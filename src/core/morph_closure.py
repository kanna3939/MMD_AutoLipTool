from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from typing import Any

try:
    from src.core.canonical_morph_value import CanonicalMorphValueError, canonicalize_morph_value
    from src.core.final_morph_capture import snapshot_digest
    from src.core.final_morph_plan import FinalMorphFullSnapshotIssuerContext
    from src.core.final_morph_closure_plan import (
        CLOSURE_POLICY_ID,
        NUMERIC_POLICY_ID,
        STAGES,
        ClosureBuildResult,
        ClosureContract,
        ClosureIdentityContext,
        ClosureIssue,
        ClosurePlan,
        ClosurePlanError,
        ClosurePoint,
        ClosureRequirement,
        ClosureRestriction,
        ClosureTransformation,
        create_closure_plan,
        validate_closure_plan_integrity,
    )
    from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.canonical_morph_value", "src.core.final_morph_capture", "src.core.final_morph_plan", "src.core.final_morph_closure_plan", "src.core.morph_name_sets"}:
        raise
    from core.canonical_morph_value import CanonicalMorphValueError, canonicalize_morph_value
    from core.final_morph_capture import snapshot_digest
    from core.final_morph_plan import FinalMorphFullSnapshotIssuerContext
    from core.final_morph_closure_plan import (
        CLOSURE_POLICY_ID,
        NUMERIC_POLICY_ID,
        STAGES,
        ClosureBuildResult,
        ClosureContract,
        ClosureIdentityContext,
        ClosureIssue,
        ClosurePlan,
        ClosurePlanError,
        ClosurePoint,
        ClosureRequirement,
        ClosureRestriction,
        ClosureTransformation,
        create_closure_plan,
        validate_closure_plan_integrity,
    )
    from core.morph_name_sets import SEMANTIC_VOWEL_ORDER


class ClosureIssuerError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ClosureProtectedPoint:
    frame_no: int
    semantic_morph: str
    value: float
    source_id: str
    origin: str
    reason: str

    def __post_init__(self) -> None:
        if isinstance(self.frame_no, bool) or not isinstance(self.frame_no, int) or not 0 <= self.frame_no <= 0xFFFFFFFF:
            raise ClosureIssuerError("protected point frame is invalid")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosureIssuerError("protected point morph is invalid")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not math.isfinite(float(self.value)) or self.value < 0:
            raise ClosureIssuerError("protected point value is invalid")
        if type(self.source_id) is not str or not self.source_id:
            raise ClosureIssuerError("protected point source is invalid")
        if self.origin not in {"manual", "unknown"}:
            raise ClosureIssuerError("protected point origin is invalid")
        if type(self.reason) is not str or not self.reason:
            raise ClosureIssuerError("protected point reason is invalid")


@dataclass(frozen=True, slots=True)
class ClosureExplicitBoundary:
    frame_no: int
    semantic_morph: str
    source_id: str
    reason: str

    def __post_init__(self) -> None:
        if isinstance(self.frame_no, bool) or not isinstance(self.frame_no, int) or not 0 <= self.frame_no <= 0xFFFFFFFF:
            raise ClosureIssuerError("explicit boundary frame is invalid")
        if self.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise ClosureIssuerError("explicit boundary morph is invalid")
        if type(self.source_id) is not str or not self.source_id or type(self.reason) is not str or not self.reason:
            raise ClosureIssuerError("explicit boundary provenance is invalid")


def _baseline_digest(
    points: tuple[tuple[int, str, float], ...],
    protected: tuple[ClosureProtectedPoint, ...],
    boundaries: tuple[ClosureExplicitBoundary, ...],
) -> str:
    payload = {
        "baseline": [[frame, morph, float(value).hex()] for frame, morph, value in points],
        "protected": [
            [item.frame_no, item.semantic_morph, float(item.value).hex(), item.source_id, item.origin, item.reason]
            for item in protected
        ],
        "explicit_requirement_boundaries": [
            [item.frame_no, item.semantic_morph, item.source_id, item.reason]
            for item in boundaries
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ClosureIssuerContext:
    """Complete immutable source issuer plus the independently read legacy baseline."""

    legacy_context: FinalMorphFullSnapshotIssuerContext
    baseline_points: tuple[tuple[int, str, float], ...]
    protected_points: tuple[ClosureProtectedPoint, ...] = ()
    explicit_requirement_boundaries: tuple[ClosureExplicitBoundary, ...] = ()
    transition_admission: TransitionClosureAdmission | None = None
    schedule_admission: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.legacy_context, FinalMorphFullSnapshotIssuerContext):
            raise ClosureIssuerError("legacy full-snapshot context is required")
        if not isinstance(self.baseline_points, tuple):
            raise ClosureIssuerError("baseline_points must be a tuple")
        normalized: list[tuple[int, str, float]] = []
        for item in self.baseline_points:
            if not isinstance(item, tuple) or len(item) != 3:
                raise ClosureIssuerError("baseline point must be a frame, morph, value triple")
            frame, semantic, value = item
            if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame <= 0xFFFFFFFF:
                raise ClosureIssuerError("baseline frame is invalid")
            if semantic not in SEMANTIC_VOWEL_ORDER:
                raise ClosureIssuerError("baseline semantic morph is invalid")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
                raise ClosureIssuerError("baseline value must be finite and non-negative")
            normalized.append((frame, semantic, float(value)))
        order_key = lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1]))
        if normalized != sorted(normalized, key=order_key):
            raise ClosureIssuerError("baseline points must be canonically ordered")
        keys = [(frame, semantic) for frame, semantic, _ in normalized]
        if len(keys) != len(set(keys)):
            raise ClosureIssuerError("baseline points contain duplicate semantic keys")
        object.__setattr__(self, "baseline_points", tuple(normalized))
        for name in ("protected_points", "explicit_requirement_boundaries"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise ClosureIssuerError(f"{name} must be a tuple")
        if any(not isinstance(item, ClosureProtectedPoint) for item in self.protected_points):
            raise ClosureIssuerError("protected_points contains an invalid value")
        if any(not isinstance(item, ClosureExplicitBoundary) for item in self.explicit_requirement_boundaries):
            raise ClosureIssuerError("explicit_requirement_boundaries contains an invalid value")
        if self.transition_admission is not None and not isinstance(self.transition_admission, TransitionClosureAdmission):
            raise ClosureIssuerError("transition_admission contains an invalid value")
        protected = tuple(sorted(self.protected_points, key=lambda item: (item.frame_no, SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.source_id)))
        boundaries = tuple(sorted(self.explicit_requirement_boundaries, key=lambda item: (item.frame_no, SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.source_id)))
        if len({(item.frame_no, item.semantic_morph, item.source_id) for item in protected}) != len(protected):
            raise ClosureIssuerError("protected points contain duplicate source keys")
        if len({(item.frame_no, item.semantic_morph, item.source_id) for item in boundaries}) != len(boundaries):
            raise ClosureIssuerError("explicit requirement boundaries contain duplicate source keys")
        object.__setattr__(self, "protected_points", protected)
        object.__setattr__(self, "explicit_requirement_boundaries", boundaries)

    @property
    def baseline_digest(self) -> str:
        return _baseline_digest(self.baseline_points, self.protected_points, self.explicit_requirement_boundaries)


@dataclass(frozen=True, slots=True)
class TransitionClosureAdmission:
    """B2-only proof that a changed shape plan derives from an admitted MS31 source."""

    original_issuer_context: ClosureIssuerContext
    policy: Any
    acoustic_snapshot: Any
    pairs: tuple[Any, ...]
    resolution: Any

    def __post_init__(self) -> None:
        if (
            not isinstance(self.original_issuer_context, ClosureIssuerContext)
            or self.original_issuer_context.transition_admission is not None
        ):
            raise ClosureIssuerError("transition admission requires an original MS31 issuer context")
        try:
            from src.core.cross_vowel_transition import (
                TransitionPairInput,
                TransitionPolicySnapshot,
                TransitionResolution,
            )
            from src.core.transition_acoustic import TransitionAcousticSnapshot
        except ModuleNotFoundError as error:
            if error.name not in {"src", "src.core", "src.core.cross_vowel_transition", "src.core.transition_acoustic"}:
                raise
            from core.cross_vowel_transition import (
                TransitionPairInput,
                TransitionPolicySnapshot,
                TransitionResolution,
            )
            from core.transition_acoustic import TransitionAcousticSnapshot
        if not isinstance(self.policy, TransitionPolicySnapshot):
            raise ClosureIssuerError("transition admission policy is invalid")
        if not isinstance(self.acoustic_snapshot, TransitionAcousticSnapshot):
            raise ClosureIssuerError("transition admission acoustic snapshot is invalid")
        if not isinstance(self.pairs, tuple) or any(not isinstance(item, TransitionPairInput) for item in self.pairs):
            raise ClosureIssuerError("transition admission pairs are invalid")
        if not isinstance(self.resolution, TransitionResolution):
            raise ClosureIssuerError("transition admission resolution is invalid")


@dataclass(frozen=True, slots=True)
class ClosureValidationResult:
    state: str
    issues: tuple[ClosureIssue, ...]

    def __post_init__(self) -> None:
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise ClosurePlanError("validation state is unsupported")
        if not isinstance(self.issues, tuple) or any(not isinstance(item, ClosureIssue) for item in self.issues):
            raise ClosurePlanError("validation issues are invalid")


@dataclass(frozen=True, slots=True)
class _SourcePoint:
    frame_no: int
    semantic_morph: str
    value: float
    source_id: str
    origin: str
    point_kind: str


@dataclass(frozen=True, slots=True)
class _ShapeInfo:
    ordinal: int
    semantic_morph: str
    start_frame: int
    terminal_frame: int
    owner_event_indices: tuple[int, ...]
    source_ids: tuple[str, ...]
    origin: str


def _failure(state: str, reason: str, stage: str, detail: str) -> ClosureBuildResult:
    issue = ClosureIssue(reason, stage, detail)
    return ClosureBuildResult(state, None, (issue,))


def _verify_source_context(
    issuer: ClosureIssuerContext,
) -> tuple[object, object, object, ClosureIdentityContext, tuple[_SourcePoint, ...], tuple[_ShapeInfo, ...]]:
    legacy = issuer.legacy_context
    if legacy.input_kind not in {"synthetic_snapshot", "captured_snapshot"}:
        raise ClosureIssuerError("full-snapshot input kind is unavailable")
    if legacy.identity_context is None or legacy.base_input is None or legacy.adjustment_snapshot is None or legacy.effective_plan_snapshot is None or legacy.issuer_evidence is None:
        raise ClosureIssuerError("full-snapshot issuer fields are incomplete")
    try:
        from src.core.effective_shape_plan import build_base_plan_identity, resolve_effective_shape_plan
        from src.core.final_morph_plan import effective_plan_snapshot_digest
        from src.vmd_writer.final_morph_legacy_bridge import capture_issuer_evidence
    except ModuleNotFoundError as error:
        if error.name not in {"src", "src.core", "src.core.effective_shape_plan", "src.core.final_morph_plan", "src.vmd_writer", "src.vmd_writer.final_morph_legacy_bridge"}:
            raise
        from core.effective_shape_plan import build_base_plan_identity, resolve_effective_shape_plan
        from core.final_morph_plan import effective_plan_snapshot_digest
        from vmd_writer.final_morph_legacy_bridge import capture_issuer_evidence

    identity = legacy.identity_context
    try:
        base_identity = build_base_plan_identity(legacy.base_input)
        admission = issuer.transition_admission
        if issuer.schedule_admission is not None:
            from src.core.bounded_transition import verify_schedule_admission, bounded_baseline_points
            resolved = verify_schedule_admission(issuer.schedule_admission)
            effective_digest = effective_plan_snapshot_digest(resolved)
            if (admission is not None
                    or effective_digest != effective_plan_snapshot_digest(legacy.effective_plan_snapshot)
                    or snapshot_digest(issuer.schedule_admission.preparation.base_input) != snapshot_digest(legacy.base_input)
                    or snapshot_digest(issuer.schedule_admission.preparation.adjustment_snapshot) != snapshot_digest(legacy.adjustment_snapshot)):
                raise ClosureIssuerError("bounded schedule source mismatch")
            expected_baseline = bounded_baseline_points(resolved, identity.output_mapping,
                issuer.schedule_admission.schedule.closure_guards)
            if issuer.baseline_points != expected_baseline:
                raise ClosureIssuerError("bounded baseline differs from source-derived points and closure guards")
        elif admission is None:
            resolved = resolve_effective_shape_plan(legacy.base_input, legacy.adjustment_snapshot)
            effective_digest = effective_plan_snapshot_digest(resolved)
        else:
            try:
                from src.core.cross_vowel_transition import (
                    apply_transition_resolution_to_effective_plan,
                    build_transition_pairs_from_effective_plan,
                    validate_transition_resolution,
                )
            except ModuleNotFoundError as error:
                if error.name not in {"src", "src.core", "src.core.cross_vowel_transition"}:
                    raise
                from core.cross_vowel_transition import (
                    apply_transition_resolution_to_effective_plan,
                    build_transition_pairs_from_effective_plan,
                    validate_transition_resolution,
                )

            original_context = admission.original_issuer_context
            original_resolved = _verify_source_context(original_context)[0]
            expected_pairs = build_transition_pairs_from_effective_plan(
                original_resolved,
                fps=admission.policy.fps,
            )
            if expected_pairs != admission.pairs:
                raise ClosureIssuerError("transition pairs differ from re-resolved source")
            transition_validation = validate_transition_resolution(
                policy=admission.policy,
                acoustic_snapshot=admission.acoustic_snapshot,
                pairs=expected_pairs,
                baseline_shapes=tuple(getattr(original_resolved, "shapes", ())),
                resolution=admission.resolution,
            )
            if transition_validation.state != "valid":
                raise ClosureIssuerError("transition resolution is invalid")
            resolved = apply_transition_resolution_to_effective_plan(
                original_resolved,
                admission.resolution,
            )
            effective_digest = effective_plan_snapshot_digest(resolved)
            expected_identity = replace(
                original_context.legacy_context.identity_context,
                effective_plan_digest=effective_digest,
            )
            if (
                legacy.input_kind != original_context.legacy_context.input_kind
                or legacy.base_input != original_context.legacy_context.base_input
                or legacy.adjustment_snapshot != original_context.legacy_context.adjustment_snapshot
                or legacy.identity_context != expected_identity
                or effective_plan_snapshot_digest(legacy.effective_plan_snapshot) != effective_digest
                or tuple(getattr(resolved, "shapes", ()))
                != tuple(getattr(legacy.effective_plan_snapshot, "shapes", ()))
                or getattr(resolved, "normalization_contract", None)
                != getattr(legacy.effective_plan_snapshot, "normalization_contract", None)
            ):
                raise ClosureIssuerError("transition source differs from its admitted resolution")
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        raise ClosureIssuerError("complete source could not be resolved") from error
    if (
        base_identity.digest != identity.base_plan_digest
        or effective_digest != identity.effective_plan_digest
        or getattr(resolved, "canonical_adjustment_snapshot", None) != legacy.adjustment_snapshot
    ):
        raise ClosureIssuerError("source resolution differs from the captured identity or adjustment snapshot")
    expected_evidence = capture_issuer_evidence(
        resolved,
        source_run_id=identity.source_run_id,
        analysis_generation=identity.analysis_generation,
        manual_revision=identity.manual_revision,
    )
    if expected_evidence != legacy.issuer_evidence:
        raise ClosureIssuerError("issuer evidence differs from re-resolved source")
    adjustment_digest = snapshot_digest(legacy.adjustment_snapshot)
    contract = ClosureContract()
    closure_identity = ClosureIdentityContext(
        source_run_id=identity.source_run_id,
        analysis_generation=identity.analysis_generation,
        manual_revision=identity.manual_revision,
        base_plan_digest=identity.base_plan_digest,
        adjustment_snapshot_digest=adjustment_digest,
        effective_plan_digest=identity.effective_plan_digest,
        baseline_digest=issuer.baseline_digest,
        resolved_profile_id=identity.resolved_profile_id,
        output_mapping=tuple(identity.output_mapping),
        numeric_policy_id=NUMERIC_POLICY_ID,
        silence_policy_id=identity.silence_policy_id,
        crossfade_policy_id=identity.crossfade_policy_id,
        closure_policy_id=CLOSURE_POLICY_ID,
        contract_digest=contract.digest,
    )

    source_points: list[_SourcePoint] = []
    manual_indices = set(expected_evidence.manual_event_indices)
    effective_shapes = tuple(getattr(resolved, "shapes", ()))
    for shape_ordinal, shape in enumerate(effective_shapes):
        owners = tuple(sorted(set(getattr(shape, "real_base_event_indices", ()))))
        origin = "manual" if manual_indices.intersection(owners) else "automatic" if owners else "unknown"
        for point_ordinal, point in enumerate(tuple(getattr(shape, "control_points", ()))):
            source_points.append(
                _SourcePoint(
                    frame_no=getattr(point, "frame_no"),
                    semantic_morph=getattr(shape, "vowel"),
                    value=float(getattr(point, "value")),
                    source_id=f"source:shape:{shape_ordinal}:point:{point_ordinal}",
                    origin=origin,
                    point_kind=getattr(point, "point_kind"),
                )
            )

    effective_events = {getattr(item, "base_event_index"): item for item in tuple(getattr(resolved, "effective_events", ()))}
    shapes: list[_ShapeInfo] = []
    for ordinal, shape in enumerate(effective_shapes):
        points = tuple(getattr(shape, "control_points", ()))
        owners = tuple(sorted(set(getattr(shape, "real_base_event_indices", ()))))
        tail = getattr(shape, "resolved_tail", None)
        tail_event_index = getattr(tail, "tail_base_event_index", None)
        if not points or not owners or tail_event_index not in effective_events:
            continue
        tail_event = effective_events[tail_event_index]
        hold = getattr(tail, "effective_hold_frames", None)
        softness = getattr(tail, "effective_softness_frames", None)
        end_frame = getattr(tail_event, "end_frame", None)
        if (
            getattr(tail_event, "vowel", None) != getattr(shape, "vowel", None)
            or tail_event_index not in owners
            or any(index not in effective_events or getattr(effective_events[index], "vowel", None) != getattr(shape, "vowel", None) for index in owners)
            or any(type(value) is not int or value < 0 for value in (hold, softness, end_frame))
        ):
            continue
        terminal = end_frame + hold + softness
        if terminal > 0xFFFFFFFF:
            continue
        source_ids = tuple(sorted(item.source_id for item in source_points if item.semantic_morph == getattr(shape, "vowel", None) and item.frame_no in {point.frame_no for point in points}))
        shapes.append(
            _ShapeInfo(
                ordinal=ordinal,
                semantic_morph=getattr(shape, "vowel"),
                start_frame=getattr(points[0], "frame_no"),
                terminal_frame=terminal,
                owner_event_indices=owners,
                source_ids=source_ids,
                origin="manual" if manual_indices.intersection(owners) else "automatic",
            )
        )
    if len(shapes) != len(effective_shapes):
        raise ClosureIssuerError("one or more effective shapes lack resolvable source ownership or terminal")
    return resolved, legacy.base_input, legacy.issuer_evidence, closure_identity, tuple(source_points), tuple(shapes)


def _origin_for_baseline_point(
    frame_no: int,
    semantic_morph: str,
    source_points: tuple[_SourcePoint, ...],
    issuer_evidence: object,
) -> tuple[str, tuple[str, ...]]:
    matching = tuple(item for item in source_points if item.frame_no == frame_no and item.semantic_morph == semantic_morph)
    if matching:
        origins = {item.origin for item in matching}
        origin = next(iter(origins)) if len(origins) == 1 else "mixed"
        return origin, tuple(sorted(item.source_id for item in matching))
    required = set(getattr(issuer_evidence, "required_zero_frames", ()))
    if (semantic_morph, frame_no) in required or any(
        start <= frame_no <= end for start, end in tuple(getattr(issuer_evidence, "silence_core_frame_ranges", ()))
    ):
        return "automatic", (f"source:legacy-zero:{semantic_morph}:{frame_no}",)
    return "unknown", (f"source:unattributed:{semantic_morph}:{frame_no}",)


def _point_kinds_for_baseline_point(
    frame_no: int,
    semantic_morph: str,
    source_points: tuple[_SourcePoint, ...],
    issuer_evidence: object,
) -> tuple[str, ...]:
    matching = tuple(item.point_kind for item in source_points if item.frame_no == frame_no and item.semantic_morph == semantic_morph)
    if matching:
        return tuple(sorted(set(matching)))
    if (semantic_morph, frame_no) in set(getattr(issuer_evidence, "required_zero_frames", ())):
        return ("required_zero",)
    if any(start <= frame_no <= end for start, end in tuple(getattr(issuer_evidence, "silence_core_frame_ranges", ()))):
        return ("silence_core_zero",)
    return ("unknown",)


def _source_positive_at(
    source_points: tuple[_SourcePoint, ...],
    semantic_morph: str,
    frame_no: int,
) -> tuple[_SourcePoint, ...]:
    return tuple(item for item in source_points if item.semantic_morph == semantic_morph and item.frame_no == frame_no and item.value > 0.0)


def _source_zero_at(
    source_points: tuple[_SourcePoint, ...],
    semantic_morph: str,
    frame_no: int,
) -> tuple[_SourcePoint, ...]:
    return tuple(item for item in source_points if item.semantic_morph == semantic_morph and item.frame_no == frame_no and item.value == 0.0)


def _curve_value_and_source_refs(
    points: tuple[tuple[int, float], ...],
    *,
    frame_no: int,
    shape_id: int,
) -> tuple[float | None, tuple[str, ...]]:
    ordered = tuple(sorted(points))
    for ordinal, (frame, value) in enumerate(ordered):
        if frame == frame_no:
            return value, (f"source:shape:{shape_id}:point:{ordinal}",)
    for ordinal, ((left_frame, left_value), (right_frame, right_value)) in enumerate(zip(ordered, ordered[1:])):
        if left_frame < frame_no < right_frame:
            ratio = (frame_no - left_frame) / (right_frame - left_frame)
            return left_value + (right_value - left_value) * ratio, (
                f"source:shape:{shape_id}:point:{ordinal}",
                f"source:shape:{shape_id}:point:{ordinal + 1}",
            )
    return None, ()


def _source_core_restrictions(resolved: object) -> tuple[ClosureRestriction, ...]:
    restrictions: list[ClosureRestriction] = []
    for record_ordinal, record in enumerate(tuple(getattr(resolved, "silence_clip_records", ()) or ())):
        if not isinstance(record, dict):
            raise ClosureIssuerError("silence-core restriction record has an unsupported type")
        shape_id = record.get("shape_id")
        semantic = record.get("vowel")
        reason_code = record.get("reason_code")
        try:
            event_indices = tuple(record.get("source_event_indices", ()))
            before_payload = tuple(record.get("before_control_points", ()))
            after_payload = tuple(record.get("after_control_points", ()))
        except TypeError as error:
            raise ClosureIssuerError("silence-core restriction record is incomplete") from error
        if (
            type(shape_id) is not int
            or semantic not in SEMANTIC_VOWEL_ORDER
            or not event_indices
            or any(type(index) is not int or index < 0 for index in event_indices)
            or type(reason_code) is not str
            or not reason_code
        ):
            raise ClosureIssuerError("silence-core restriction record lacks event, morph, or reason provenance")
        try:
            before = tuple((item["frame_no"], float(item["value"])) for item in before_payload)
            after = tuple((item["frame_no"], float(item["value"])) for item in after_payload)
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ClosureIssuerError("silence-core restriction control points are incomplete") from None
        if any(type(frame) is not int or not math.isfinite(value) for frame, value in (*before, *after)):
            raise ClosureIssuerError("silence-core restriction control points are invalid")
        source_ids = {
            f"source:event:{index}" for index in event_indices
        }
        source_ids.add(f"source:shape:{shape_id}")
        source_ids.add(f"source:core-clip:{shape_id}:{reason_code}")
        for start, end in tuple(record.get("silence_core_frame_ranges", ())):
            if type(start) is int and type(end) is int:
                source_ids.add(f"source:silence-core:{start}:{end}")
        for frame, _effective in after:
            requested, point_refs = _curve_value_and_source_refs(before, frame_no=frame, shape_id=shape_id)
            effective, _effective_refs = _curve_value_and_source_refs(after, frame_no=frame, shape_id=shape_id)
            if requested is None or effective is None or requested <= effective:
                continue
            restrictions.append(
                ClosureRestriction(
                    restriction_id=f"restriction:core:{shape_id}:{semantic}:{frame}:{record_ordinal}",
                    semantic_morph=semantic,
                    frame_no=frame,
                    requested_value_hex=float(requested).hex(),
                    effective_value_hex=float(effective).hex(),
                    reason="silence_core_precedence",
                    source_ids=tuple(sorted(source_ids.union(point_refs))),
                )
            )
    return tuple(sorted(
        restrictions,
        key=lambda item: (SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.frame_no, item.restriction_id),
    ))


def _shape_start_source_point(shape: _ShapeInfo, source_points: tuple[_SourcePoint, ...]) -> _SourcePoint:
    source_id = f"source:shape:{shape.ordinal}:point:0"
    matches = tuple(item for item in source_points if item.source_id == source_id)
    if (
        len(matches) != 1
        or matches[0].frame_no != shape.start_frame
        or matches[0].semantic_morph != shape.semantic_morph
        or not math.isfinite(matches[0].value)
        or matches[0].value < 0.0
    ):
        raise ClosureIssuerError("next same-morph shape start lacks a unique source-resolved control point")
    return matches[0]


def _make_requirement(
    *,
    requirement_id: str,
    kind: str,
    semantic_morph: str,
    start_frame: int,
    end_frame: int,
    endpoint_policy: str,
    source_ids: tuple[str, ...],
    reason: str,
) -> ClosureRequirement:
    return ClosureRequirement(
        requirement_id=requirement_id,
        kind=kind,
        semantic_morph=semantic_morph,
        start_frame=start_frame,
        end_frame=end_frame,
        endpoint_policy=endpoint_policy,
        source_ids=tuple(sorted(set(source_ids))),
        reason=reason,
    )


def _ordered_requirements(requirements: list[ClosureRequirement]) -> tuple[ClosureRequirement, ...]:
    kind_order = {"per_morph_closure": 0, "silence_core": 1, "required_zero": 2}
    return tuple(sorted(requirements, key=lambda item: (kind_order[item.kind], SEMANTIC_VOWEL_ORDER.index(item.semantic_morph), item.start_frame, item.end_frame, item.requirement_id)))


def _requirement_set(
    resolved: object,
    base_input: object,
    issuer: ClosureIssuerContext,
    shapes: tuple[_ShapeInfo, ...],
    source_points: tuple[_SourcePoint, ...],
    issuer_evidence: object,
) -> tuple[tuple[ClosureRequirement, ...], int]:
    duration_end = getattr(base_input, "source_duration_frames", None)
    if isinstance(duration_end, bool) or not isinstance(duration_end, int) or not 0 <= duration_end <= 0xFFFFFFFF:
        raise ClosureIssuerError("source audio duration frame is unavailable or out of range")
    protected_frames = [item.frame_no for item in issuer.protected_points]
    for frame, semantic, _value in issuer.baseline_points:
        origin, _ = _origin_for_baseline_point(frame, semantic, source_points, issuer_evidence)
        if origin in {"manual", "unknown", "mixed"}:
            protected_frames.append(frame)
    shape_terminal_frames = [item.terminal_frame for item in shapes]
    explicit_frames = [item.frame_no for item in issuer.explicit_requirement_boundaries]
    output_end = max([duration_end, *shape_terminal_frames, *protected_frames, *explicit_frames])
    if output_end > 0xFFFFFFFF:
        raise ClosureIssuerError("source-derived output end exceeds VMD frame range")

    requirements: list[ClosureRequirement] = []
    by_morph: dict[str, list[_ShapeInfo]] = {item: [] for item in SEMANTIC_VOWEL_ORDER}
    for shape in shapes:
        by_morph[shape.semantic_morph].append(shape)
    for semantic in SEMANTIC_VOWEL_ORDER:
        ordered_shapes = sorted(by_morph[semantic], key=lambda item: (item.start_frame, item.terminal_frame, item.ordinal))
        for index, shape in enumerate(ordered_shapes):
            next_shape = ordered_shapes[index + 1] if index + 1 < len(ordered_shapes) else None
            if next_shape is None:
                end = output_end
                reason = "source_resolved_terminal_until_output_end"
            else:
                if next_shape.start_frame < shape.terminal_frame:
                    raise ClosureIssuerError("next same-morph shape begins before the source-resolved terminal")
                next_start = _shape_start_source_point(next_shape, source_points)
                if next_start.value == 0.0:
                    end = next_shape.start_frame
                    reason = "source_terminal_until_zero_next_same_morph_shape"
                elif next_start.value > 0.0:
                    end = shape.terminal_frame
                    reason = "source_terminal_before_positive_next_same_morph_shape"
                else:
                    raise ClosureIssuerError("next same-morph shape start value is invalid")
            refs = list(shape.source_ids)
            refs.extend(f"source:event:{event_index}" for event_index in shape.owner_event_indices)
            if next_shape is not None:
                refs.extend(next_shape.source_ids)
            else:
                refs.extend(f"source:output-end:{item.source_id}" for item in issuer.explicit_requirement_boundaries)
                refs.append(f"source:audio-duration-end:{duration_end}")
                refs.extend(f"source:protected-key:{item.frame_no}:{item.semantic_morph}:{item.source_id}" for item in issuer.protected_points)
            requirements.append(
                _make_requirement(
                    requirement_id=f"closure:{semantic}:{shape.ordinal}:{shape.terminal_frame}:{end}",
                    kind="per_morph_closure",
                    semantic_morph=semantic,
                    start_frame=shape.terminal_frame,
                    end_frame=end,
                    endpoint_policy="closed_exact_zero",
                    source_ids=tuple(refs),
                    reason=reason,
                )
            )

    for index, (start, end) in enumerate(tuple(getattr(resolved, "silence_core_frame_ranges", ()) or ())):
        for semantic in SEMANTIC_VOWEL_ORDER:
            requirements.append(
                _make_requirement(
                    requirement_id=f"silence-core:{semantic}:{start}:{end}:{index}",
                    kind="silence_core",
                    semantic_morph=semantic,
                    start_frame=start,
                    end_frame=end,
                    endpoint_policy="closed_exact_zero",
                    source_ids=(f"source:silence-core:{start}:{end}",),
                    reason="existing_effective_plan_silence_core",
                )
            )
    for semantic, frame in tuple(getattr(getattr(resolved, "normalization_contract", None), "required_zero_frames", ())):
        requirements.append(
            _make_requirement(
                requirement_id=f"required-zero:{semantic}:{frame}",
                kind="required_zero",
                semantic_morph=semantic,
                start_frame=frame,
                end_frame=frame,
                endpoint_policy="explicit_key_exact_zero",
                source_ids=(f"source:required-zero:{semantic}:{frame}",),
                reason="existing_effective_plan_required_zero",
            )
        )
    return _ordered_requirements(requirements), output_end


def _exact_zero_interval(
    points: tuple[ClosurePoint, ...], semantic_morph: str, start_frame: int, end_frame: int
) -> bool:
    curve = tuple((item.frame_no, item.value.scalar) for item in points if item.semantic_morph == semantic_morph)
    if not curve or start_frame < curve[0][0] or end_frame > curve[-1][0]:
        return False
    if start_frame == end_frame:
        exact = next((value for frame, value in curve if frame == start_frame), None)
        if exact is not None:
            return exact == 0.0
        for (left_frame, left_value), (right_frame, right_value) in zip(curve, curve[1:]):
            if left_frame < start_frame < right_frame:
                ratio = (start_frame - left_frame) / (right_frame - left_frame)
                return left_value + (right_value - left_value) * ratio == 0.0
        return False
    for frame, value in curve:
        if start_frame <= frame <= end_frame and value != 0.0:
            return False
    for (left_frame, left_value), (right_frame, right_value) in zip(curve, curve[1:]):
        overlap_start = max(start_frame, left_frame)
        overlap_end = min(end_frame, right_frame)
        if overlap_end < overlap_start:
            continue
        if overlap_end == overlap_start:
            if overlap_start not in {left_frame, right_frame}:
                ratio = (overlap_start - left_frame) / (right_frame - left_frame)
                value = left_value + (right_value - left_value) * ratio
                if value != 0.0:
                    return False
        elif left_value != 0.0 or right_value != 0.0:
            return False
    return True


def _closure_endpoint_specs(
    requirement: ClosureRequirement,
    shapes: tuple[_ShapeInfo, ...],
    output_end: int,
) -> tuple[tuple[int, str, bool], ...]:
    terminal_shapes = tuple(
        item for item in shapes
        if item.semantic_morph == requirement.semantic_morph and item.terminal_frame == requirement.start_frame
    )
    endpoints: list[tuple[int, str, bool]] = [
        (requirement.start_frame, "terminal", len(terminal_shapes) == 1)
    ]
    if requirement.reason == "source_terminal_until_zero_next_same_morph_shape":
        next_shapes = tuple(
            item for item in shapes
            if item.semantic_morph == requirement.semantic_morph
            and item.start_frame == requirement.end_frame
            and item.start_frame > requirement.start_frame
        )
        endpoints.append((requirement.end_frame, "next_shape_start", len(next_shapes) == 1))
    elif requirement.reason == "source_resolved_terminal_until_output_end" and requirement.end_frame > requirement.start_frame:
        endpoints.append((requirement.end_frame, "output_end", requirement.end_frame == output_end))
    unique: dict[int, tuple[int, str, bool]] = {}
    for frame, kind, repairable in endpoints:
        prior = unique.get(frame)
        if prior is None or (not prior[2] and repairable):
            unique[frame] = (frame, kind, repairable)
    return tuple(unique.values())


def _silence_core_boundary_targets(
    requirement: ClosureRequirement,
    curve: tuple[tuple[int, float], ...],
    source_points: tuple[_SourcePoint, ...],
) -> tuple[tuple[int, str], ...]:
    if any(
        item.semantic_morph == requirement.semantic_morph
        and requirement.start_frame <= item.frame_no <= requirement.end_frame
        and item.value > 0.0
        for item in source_points
    ) or any(
        requirement.start_frame <= frame <= requirement.end_frame and value > 0.0
        for frame, value in curve
    ):
        return ()
    targets: list[tuple[int, str]] = []
    if not curve or requirement.start_frame < curve[0][0]:
        targets.append((requirement.start_frame, "materialize_source_silence_core_start_zero"))
    if requirement.end_frame != requirement.start_frame and (not curve or requirement.end_frame > curve[-1][0]):
        targets.append((requirement.end_frame, "materialize_source_silence_core_end_zero"))
    return tuple(dict.fromkeys(targets))


def _repair_record_covers(
    plan: ClosurePlan,
    *,
    frame_no: int,
    semantic_morph: str,
    requirement: ClosureRequirement,
    operation: str,
) -> bool:
    return any(
        item.stage == "closure_zero_materialization"
        and item.operation == operation
        and item.frame_no == frame_no
        and item.semantic_morph == semantic_morph
        and requirement.requirement_id in item.requirement_ids
        and bool(set(requirement.source_ids).intersection(item.source_ids))
        for item in plan.transformations
    )


def build_closure_candidate(
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract | None = None,
) -> ClosureBuildResult:
    """Build a source-bound closure candidate under the current closure policy."""
    if not isinstance(issuer_context, ClosureIssuerContext):
        return _failure("unavailable", "capture_unavailable", "issuer_admission", "typed closure issuer context is missing")
    contract = closure_contract or ClosureContract()
    if not isinstance(contract, ClosureContract):
        return _failure("invalid", "input_invalid", "issuer_admission", "closure contract has an unsupported type")
    try:
        resolved, base_input, issuer_evidence, identity, source_points, shapes = _verify_source_context(issuer_context)
        requirements, output_end = _requirement_set(resolved, base_input, issuer_context, shapes, source_points, issuer_evidence)
        source_core_restrictions = _source_core_restrictions(resolved)
    except ClosureIssuerError as error:
        reason = "identity_mismatch" if "identity" in str(error) or "resolution differs" in str(error) else "provenance_missing" if "evidence" in str(error) else "capture_unavailable"
        state = "invalid" if reason in {"identity_mismatch", "provenance_missing"} else "unavailable"
        return _failure(state, reason, "issuer_admission", str(error))
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError, ClosurePlanError) as error:
        return _failure("invalid", "input_invalid", "issuer_admission", str(error))

    transformations: list[ClosureTransformation] = []
    issues: list[ClosureIssue] = []
    restrictions: list[ClosureRestriction] = list(source_core_restrictions)
    work: dict[tuple[int, str], dict[str, Any]] = {}
    source_by_key: dict[tuple[int, str], tuple[_SourcePoint, ...]] = {}
    for point in source_points:
        source_by_key.setdefault((point.frame_no, point.semantic_morph), ())
        source_by_key[(point.frame_no, point.semantic_morph)] += (point,)
    for frame, semantic, value in issuer_context.baseline_points:
        origin, source_ids = _origin_for_baseline_point(frame, semantic, source_points, issuer_evidence)
        point_kinds = _point_kinds_for_baseline_point(frame, semantic, source_points, issuer_evidence)
        work[(frame, semantic)] = {"value": value, "source_ids": set(source_ids), "requirement_ids": set(), "origin": origin, "point_kinds": set(point_kinds)}
    for item in issuer_context.protected_points:
        key = (item.frame_no, item.semantic_morph)
        existing = work.get(key)
        if existing is not None and existing["value"] != float(item.value):
            issues.append(ClosureIssue("protected_change_unexplained", "legacy_candidate_binding", "protected key differs from baseline", item.semantic_morph, (item.frame_no, item.frame_no), (item.source_id,)))
            continue
        if existing is None:
            work[key] = {"value": float(item.value), "source_ids": {item.source_id}, "requirement_ids": set(), "origin": item.origin, "point_kinds": {item.origin}}
        else:
            existing["source_ids"].add(item.source_id)
            existing["point_kinds"].add(item.origin)
            existing["origin"] = item.origin if existing["origin"] == item.origin else "mixed"

    stage_ordinal: dict[str, int] = {stage: 0 for stage in STAGES[1:]}

    def record(
        stage: str,
        operation: str,
        *,
        semantic: str | None = None,
        frame: int | None = None,
        before: float | None = None,
        after: float | None = None,
        source_ids: tuple[str, ...] = (),
        requirement_ids: tuple[str, ...] = (),
        protection: str = "preserved",
    ) -> None:
        ordinal = stage_ordinal[stage]
        stage_ordinal[stage] += 1
        transformations.append(
            ClosureTransformation(
                transformation_id=f"transform:{stage}:{ordinal}",
                stage=stage,
                ordinal=ordinal,
                operation=operation,
                semantic_morph=semantic,
                frame_no=frame,
                before_value_hex=None if before is None else float(before).hex(),
                after_value_hex=None if after is None else float(after).hex(),
                source_ids=tuple(sorted(set(source_ids))),
                requirement_ids=tuple(sorted(set(requirement_ids))),
                protection_status=protection,
            )
        )

    record("requirement_derivation", "derive_source_requirements", source_ids=tuple(sorted({source_id for item in requirements for source_id in item.source_ids})))
    record("legacy_candidate_binding", "bind_verified_legacy_baseline", source_ids=tuple(sorted({source_id for item in work.values() for source_id in item["source_ids"]})))
    record("automatic_shape_reresolution", "resolve_complete_source_owner_shapes", source_ids=tuple(sorted({source_id for item in source_points for source_id in (item.source_id,)})))
    for restriction in source_core_restrictions:
        linked_requirements = tuple(
            item.requirement_id
            for item in requirements
            if item.kind == "silence_core"
            and item.semantic_morph == restriction.semantic_morph
            and item.start_frame <= restriction.frame_no <= item.end_frame
        )
        record(
            "automatic_shape_reresolution",
            "retain_source_silence_core_restriction",
            semantic=restriction.semantic_morph,
            frame=restriction.frame_no,
            before=float.fromhex(restriction.requested_value_hex),
            after=float.fromhex(restriction.effective_value_hex),
            source_ids=restriction.source_ids,
            requirement_ids=linked_requirements,
            protection="silence_core_precedence",
        )

    closure_requirements = tuple(item for item in requirements if item.kind == "per_morph_closure")
    for requirement in closure_requirements:
        terminal_shapes = tuple(
            item for item in shapes
            if item.semantic_morph == requirement.semantic_morph and item.terminal_frame == requirement.start_frame
        )
        terminal_shape = terminal_shapes[0] if len(terminal_shapes) == 1 else None
        for frame, endpoint_kind, repairable in _closure_endpoint_specs(requirement, shapes, output_end):
            key = (frame, requirement.semantic_morph)
            existing = work.get(key)
            source_matches = source_by_key.get(key, ())
            source_positive = tuple(item for item in source_matches if item.value > 0.0)
            source_zero = tuple(item for item in source_matches if item.value == 0.0)
            if existing is not None and existing["value"] == 0.0:
                existing["requirement_ids"].add(requirement.requirement_id)
                existing["source_ids"].add(f"source:requirement:{requirement.requirement_id}")
                existing["point_kinds"].add("closure_zero")
                record("closure_zero_materialization", "retain_existing_zero", semantic=requirement.semantic_morph, frame=frame, before=0.0, after=0.0, source_ids=tuple(existing["source_ids"]), requirement_ids=(requirement.requirement_id,))
                continue
            if existing is not None and existing["value"] > 0.0:
                origin = existing["origin"]
                if origin in {"manual", "unknown", "mixed"}:
                    reason = "protected_change_unexplained"
                    detail = "protected positive key conflicts with a source-required closure zero"
                    restrictions.append(
                        ClosureRestriction(
                            restriction_id=f"restriction:{requirement.requirement_id}:{frame}",
                            semantic_morph=requirement.semantic_morph,
                            frame_no=frame,
                            requested_value_hex=float(existing["value"]).hex(),
                            effective_value_hex=float(existing["value"]).hex(),
                            reason="manual_or_unknown_key_preserved",
                            source_ids=tuple(sorted(
                                set(existing["source_ids"]).union(
                                    item for item in requirement.source_ids if item.startswith("source:event:")
                                )
                            )),
                        )
                    )
                    issues.append(ClosureIssue(reason, "collision_resolution", detail, requirement.semantic_morph, (frame, frame), tuple(sorted(existing["source_ids"])), (requirement.requirement_id,)))
                    continue
                if source_positive:
                    issues.append(ClosureIssue("collision_unresolved", "collision_resolution", "re-resolved automatic owner still has a positive value at the required-zero frame", requirement.semantic_morph, (frame, frame), tuple(sorted(item.source_id for item in source_positive)), (requirement.requirement_id,)))
                    continue
                if not repairable or terminal_shape is None:
                    if endpoint_kind == "output_end":
                        authorized = repairable
                    elif endpoint_kind == "next_shape_start":
                        next_shape = next((item for item in shapes if item.semantic_morph == requirement.semantic_morph and item.start_frame == frame and item.start_frame > requirement.start_frame), None)
                        authorized = repairable and next_shape is not None and bool(source_zero)
                    else:
                        authorized = repairable and terminal_shape is not None
                    if not authorized:
                        issues.append(ClosureIssue("required_zero_missing", "collision_resolution", "automatic positive is outside the source-resolved endpoint repair authority", requirement.semantic_morph, (frame, frame), tuple(sorted(existing["source_ids"])), (requirement.requirement_id,)))
                        continue
                if source_positive:
                    issues.append(ClosureIssue("collision_unresolved", "collision_resolution", "re-resolved automatic owner still has a positive value at the required-zero frame", requirement.semantic_morph, (frame, frame), tuple(sorted(item.source_id for item in source_positive)), (requirement.requirement_id,)))
                    continue
                record("collision_resolution", "remove_re_resolved_automatic_positive", semantic=requirement.semantic_morph, frame=frame, before=float(existing["value"]), after=0.0, source_ids=tuple(existing["source_ids"]), requirement_ids=(requirement.requirement_id,), protection="automatic_source_re_resolved")
                del work[key]
            elif existing is None:
                if endpoint_kind == "next_shape_start" and not source_zero:
                    issues.append(ClosureIssue("required_zero_missing", "closure_zero_materialization", "next same-morph shape start is not source-resolved zero", requirement.semantic_morph, (frame, frame), tuple(sorted(item.source_id for item in source_matches)), (requirement.requirement_id,)))
                    continue
                if not repairable:
                    issues.append(ClosureIssue("required_zero_missing", "closure_zero_materialization", "source-required endpoint is outside the selected repair authority", requirement.semantic_morph, (frame, frame), tuple(sorted(item.source_id for item in source_matches)), (requirement.requirement_id,)))
                    continue
            if source_positive:
                issues.append(ClosureIssue("collision_unresolved", "collision_resolution", "re-resolved automatic owner remains positive at the required-zero frame", requirement.semantic_morph, (frame, frame), tuple(sorted(item.source_id for item in source_positive)), (requirement.requirement_id,)))
                continue
            if endpoint_kind == "terminal" and terminal_shape is None:
                issues.append(ClosureIssue("terminal_evidence_missing", "automatic_shape_reresolution", "terminal owner cannot be uniquely identified from complete source", requirement.semantic_morph, (frame, frame), requirement.source_ids, (requirement.requirement_id,)))
                continue
            if endpoint_kind == "next_shape_start" and not source_zero:
                issues.append(ClosureIssue("required_zero_missing", "closure_zero_materialization", "next same-morph shape start has no source-resolved zero point", requirement.semantic_morph, (frame, frame), tuple(sorted(item.source_id for item in source_matches)), (requirement.requirement_id,)))
                continue
            zero = canonicalize_morph_value(0.0)
            source_ids = set(requirement.source_ids)
            source_ids.update(item.source_id for item in source_zero)
            source_ids.add(f"source:requirement:{requirement.requirement_id}")
            point_kinds = {"closure_zero"}
            point_kinds.update(item.point_kind for item in source_zero)
            work[key] = {"value": zero.scalar, "source_ids": source_ids, "requirement_ids": {requirement.requirement_id}, "origin": "automatic", "point_kinds": point_kinds}
            record("closure_zero_materialization", f"materialize_source_{endpoint_kind}_zero", semantic=requirement.semantic_morph, frame=frame, before=None, after=0.0, source_ids=tuple(source_ids), requirement_ids=(requirement.requirement_id,), protection="source_required")

    for requirement in requirements:
        if requirement.kind != "silence_core":
            continue
        curve = tuple(sorted(
            (frame, item["value"])
            for (frame, semantic), item in work.items()
            if semantic == requirement.semantic_morph
        ))
        for frame, operation in _silence_core_boundary_targets(requirement, curve, source_points):
            key = (frame, requirement.semantic_morph)
            if key in work:
                continue
            source_ids = set(requirement.source_ids)
            source_ids.add(f"source:requirement:{requirement.requirement_id}")
            work[key] = {
                "value": 0.0,
                "source_ids": source_ids,
                "requirement_ids": {requirement.requirement_id},
                "origin": "automatic",
                "point_kinds": {"closure_zero", "silence_core_zero"},
            }
            record("closure_zero_materialization", operation, semantic=requirement.semantic_morph, frame=frame, before=None, after=0.0, source_ids=tuple(source_ids), requirement_ids=(requirement.requirement_id,), protection="source_required")

    # Existing source-required single-frame zeros remain validation-only.
    for requirement in requirements:
        if requirement.kind == "required_zero":
            key = (requirement.start_frame, requirement.semantic_morph)
            existing = work.get(key)
            if existing is None or existing["value"] != 0.0:
                issues.append(ClosureIssue("required_zero_missing", "independent_validation", "existing source-required zero is missing or nonzero", requirement.semantic_morph, (requirement.start_frame, requirement.end_frame), requirement.source_ids, (requirement.requirement_id,)))
            else:
                existing["requirement_ids"].add(requirement.requirement_id)

    provisional_points: list[ClosurePoint] = []
    for (frame, semantic), item in sorted(work.items(), key=lambda pair: (pair[0][0], SEMANTIC_VOWEL_ORDER.index(pair[0][1]))):
        try:
            canonical = canonicalize_morph_value(item["value"])
        except (CanonicalMorphValueError, OverflowError, ValueError) as error:
            issues.append(ClosureIssue("numeric_invalid", "numeric_canonicalization", str(error), semantic, (frame, frame), tuple(sorted(item["source_ids"])), tuple(sorted(item["requirement_ids"]))))
            continue
        record("numeric_canonicalization", "canonicalize_scalar", semantic=semantic, frame=frame, before=float(item["value"]), after=canonical.scalar, source_ids=tuple(item["source_ids"]), requirement_ids=tuple(item["requirement_ids"]), protection="preserved")
        provisional_points.append(
            ClosurePoint(
                point_id=f"point:{semantic}:{frame}",
                record_id=f"record:canonical:{semantic}:{frame}",
                frame_no=frame,
                semantic_morph=semantic,
                value=canonical,
                source_ids=tuple(sorted(item["source_ids"])),
                requirement_ids=tuple(sorted(item["requirement_ids"])),
                origin=item["origin"],
                point_kinds=tuple(sorted(item["point_kinds"])),
            )
        )

    points = tuple(provisional_points)
    for requirement in requirements:
        if requirement.kind in {"per_morph_closure", "silence_core"}:
            if not _exact_zero_interval(points, requirement.semantic_morph, requirement.start_frame, requirement.end_frame):
                positive = tuple(item for item in points if item.semantic_morph == requirement.semantic_morph and requirement.start_frame <= item.frame_no <= requirement.end_frame and item.value.scalar > 0.0)
                protected = next((item for item in positive if item.origin in {"manual", "unknown", "mixed"}), None)
                if protected is None:
                    protected = next((item for item in positive if set(item.point_kinds).intersection({"valid_low", "valley", "boundary", "long", "manual_crossfade"})), None)
                reason = "protected_change_unexplained" if protected is not None else "silence_core_violation"
                detail = "protected positive key prevents the required zero interval" if protected is not None else "piecewise-linear curve is nonzero or undefined inside a required closed interval"
                if protected is not None:
                    restriction_id = f"restriction:{requirement.requirement_id}:{protected.frame_no}"
                    if not any(item.restriction_id == restriction_id for item in restrictions):
                        restrictions.append(
                            ClosureRestriction(
                                restriction_id=restriction_id,
                                semantic_morph=protected.semantic_morph,
                                frame_no=protected.frame_no,
                                requested_value_hex=protected.value.scalar.hex(),
                                effective_value_hex=protected.value.scalar.hex(),
                                reason="preserved_protected_shape_value",
                                source_ids=tuple(sorted(
                                    set(protected.source_ids).union(
                                        item for item in requirement.source_ids if item.startswith("source:event:")
                                    )
                                )),
                            )
                        )
                issues.append(ClosureIssue(reason, "independent_validation", detail, requirement.semantic_morph, (requirement.start_frame, requirement.end_frame), requirement.source_ids, (requirement.requirement_id,)))

    # Every stage is explicit, including unchanged stages, for audit and stable serialization.
    for stage in STAGES[1:]:
        if stage_ordinal[stage] == 0:
            operation = "independent_validator_pending" if stage == "independent_validation" and not issues else "candidate_rejected_before_validator" if stage == "independent_validation" else "no_op_verified"
            record(stage, operation, protection="preserved")
    issues = _dedupe_issues(issues)
    state = "valid" if not issues else "invalid"
    ordered_transformations = tuple(sorted(transformations, key=lambda item: (STAGES.index(item.stage), item.ordinal)))
    try:
        plan = create_closure_plan(
            contract=contract,
            identity_context=identity,
            state=state,
            requirements=requirements,
            transformations=ordered_transformations,
            restrictions=tuple(restrictions),
            points=points,
            issues=tuple(issues),
        )
    except (ClosurePlanError, TypeError, ValueError) as error:
        return _failure("invalid", "input_invalid", "independent_validation", str(error))
    if state == "valid":
        validation = validate_closure_plan(plan, issuer_context, contract)
        final_issues = _dedupe_issues(list(validation.issues))
        if validation.state != "valid":
            state = validation.state
            issues = final_issues
            validation_operation = "independent_validator_rejected_candidate"
        else:
            validation_operation = "independent_validator_pass"
        updated_transformations = tuple(
            replace(item, operation=validation_operation)
            if item.stage == "independent_validation" and item.operation == "independent_validator_pending"
            else item
            for item in plan.transformations
        )
        try:
            plan = create_closure_plan(
                contract=contract,
                identity_context=identity,
                state=state,
                requirements=requirements,
                transformations=updated_transformations,
                restrictions=tuple(restrictions),
                points=points,
                issues=tuple(issues),
            )
        except (ClosurePlanError, TypeError, ValueError) as error:
            return _failure("invalid", "input_invalid", "independent_validation", str(error))
    return ClosureBuildResult(state, plan, tuple(issues))


def _dedupe_issues(issues: list[ClosureIssue]) -> list[ClosureIssue]:
    unique: dict[tuple[object, ...], ClosureIssue] = {}
    for item in issues:
        key = (item.reason_code, item.stage, item.detail, item.semantic_morph, item.frame_range, item.source_ids, item.requirement_ids)
        unique[key] = item
    return sorted(unique.values(), key=lambda item: (STAGES.index(item.stage) if item.stage in STAGES else len(STAGES), item.reason_code, item.semantic_morph or "", item.frame_range or (-1, -1), item.detail))


def validate_closure_plan(
    plan: ClosurePlan,
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract | None = None,
) -> ClosureValidationResult:
    """Independently validate identity, allowed deltas, provenance and curve intervals."""
    contract = closure_contract or ClosureContract()
    if not isinstance(plan, ClosurePlan) or not isinstance(issuer_context, ClosureIssuerContext):
        return ClosureValidationResult("unavailable", (ClosureIssue("capture_unavailable", "issuer_admission", "typed plan or issuer is missing"),))
    if plan.state != "valid":
        return ClosureValidationResult(plan.state, plan.issues or (ClosureIssue("input_invalid", "independent_validation", "candidate is not valid"),))
    issues: list[ClosureIssue] = []
    try:
        validate_closure_plan_integrity(plan)
        resolved, base_input, issuer_evidence, identity, source_points, shapes = _verify_source_context(issuer_context)
        expected_requirements, output_end = _requirement_set(resolved, base_input, issuer_context, shapes, source_points, issuer_evidence)
        expected_restrictions = _source_core_restrictions(resolved)
    except (ClosureIssuerError, ClosurePlanError, AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        return ClosureValidationResult("unavailable", (ClosureIssue("capture_unavailable", "issuer_admission", str(error)),))
    if plan.contract != contract or plan.identity_context != identity:
        issues.append(ClosureIssue("identity_mismatch", "independent_validation", "plan contract or issuer identity differs from complete input"))
    if plan.requirements != expected_requirements:
        issues.append(ClosureIssue("provenance_missing", "independent_validation", "requirement set or source references differ from re-resolved source"))
    if plan.restrictions != expected_restrictions:
        issues.append(ClosureIssue("provenance_missing", "independent_validation", "restriction values or source references differ from re-resolved silence-core clipping"))
    restriction_transformations = tuple(
        item for item in plan.transformations
        if item.operation == "retain_source_silence_core_restriction"
    )
    if len(restriction_transformations) != len(expected_restrictions):
        issues.append(ClosureIssue("provenance_missing", "independent_validation", "source silence-core restriction transformation coverage is incomplete"))
    for restriction in expected_restrictions:
        linked_requirements = tuple(
            item.requirement_id
            for item in expected_requirements
            if item.kind == "silence_core"
            and item.semantic_morph == restriction.semantic_morph
            and item.start_frame <= restriction.frame_no <= item.end_frame
        )
        if not any(
            item.stage == "automatic_shape_reresolution"
            and item.semantic_morph == restriction.semantic_morph
            and item.frame_no == restriction.frame_no
            and item.before_value_hex == restriction.requested_value_hex
            and item.after_value_hex == restriction.effective_value_hex
            and item.source_ids == restriction.source_ids
            and item.requirement_ids == linked_requirements
            and item.protection_status == "silence_core_precedence"
            for item in restriction_transformations
        ):
            issues.append(ClosureIssue("provenance_missing", "independent_validation", "source silence-core restriction lacks a matching transformation record", restriction.semantic_morph, (restriction.frame_no, restriction.frame_no), restriction.source_ids, linked_requirements))

    expected_baseline: dict[tuple[int, str], tuple[float, str, tuple[str, ...]]] = {}
    for frame, semantic, value in issuer_context.baseline_points:
        origin, source_ids = _origin_for_baseline_point(frame, semantic, source_points, issuer_evidence)
        expected_baseline[(frame, semantic)] = (value, origin, source_ids)
    for item in issuer_context.protected_points:
        expected_baseline[(item.frame_no, item.semantic_morph)] = (float(item.value), item.origin, (item.source_id,))
    actual = {(item.frame_no, item.semantic_morph): item for item in plan.points}
    if len(actual) != len(plan.points):
        issues.append(ClosureIssue("baseline_mismatch", "independent_validation", "candidate contains duplicate semantic keys"))

    repairable: set[tuple[int, str]] = set()
    closure_endpoint_requirements: dict[tuple[int, str], list[tuple[ClosureRequirement, str]]] = {}
    for requirement in expected_requirements:
        if requirement.kind != "per_morph_closure":
            continue
        for frame, endpoint_kind, endpoint_repairable in _closure_endpoint_specs(requirement, shapes, output_end):
            if endpoint_repairable:
                key = (frame, requirement.semantic_morph)
                repairable.add(key)
                closure_endpoint_requirements.setdefault(key, []).append((requirement, endpoint_kind))

    allowed_repair_keys = repairable
    for key, (baseline_value, origin, source_ids) in expected_baseline.items():
        point = actual.get(key)
        if point is None:
            issues.append(ClosureIssue("baseline_mismatch", "independent_validation", "baseline key was removed", key[1], (key[0], key[0]), source_ids))
            continue
        expected_kinds = set(_point_kinds_for_baseline_point(key[0], key[1], source_points, issuer_evidence))
        if point.value.scalar.hex() == float(baseline_value).hex():
            if not set(source_ids).issubset(point.source_ids) or not expected_kinds.issubset(point.point_kinds):
                issues.append(ClosureIssue("provenance_missing", "independent_validation", "unchanged baseline point lost source or point-kind provenance", key[1], (key[0], key[0]), source_ids, point.requirement_ids))
            if origin in {"manual", "unknown", "mixed"} and point.origin not in {origin, "mixed"}:
                issues.append(ClosureIssue("protected_change_unexplained", "independent_validation", "protected baseline key changed provenance or scalar", key[1], (key[0], key[0]), source_ids))
            continue
        matching_requirements = tuple(
            item for item in expected_requirements
            if item.kind == "per_morph_closure" and item.semantic_morph == key[1]
            and any(frame == key[0] and repairable_endpoint for frame, _kind, repairable_endpoint in _closure_endpoint_specs(item, shapes, output_end))
            and key in allowed_repair_keys
        )
        operation = None
        for requirement in matching_requirements:
            endpoint_kind = next((kind for frame, kind, can_repair in _closure_endpoint_specs(requirement, shapes, output_end) if frame == key[0] and can_repair), None)
            endpoint_operation = None if endpoint_kind is None else f"materialize_source_{endpoint_kind}_zero"
            if endpoint_operation and _repair_record_covers(plan, frame_no=key[0], semantic_morph=key[1], requirement=requirement, operation=endpoint_operation):
                operation = endpoint_operation
                break
        re_resolved_positive = _source_positive_at(source_points, key[1], key[0])
        source_zero = _source_zero_at(source_points, key[1], key[0])
        next_shape_zero_authority = any(
            endpoint_kind == "next_shape_start" and bool(source_zero)
            for requirement, endpoint_kind in closure_endpoint_requirements.get(key, ())
        )
        terminal_authority = any(
            endpoint_kind == "terminal"
            and any(shape.semantic_morph == key[1] and shape.terminal_frame == key[0] for shape in shapes)
            for _requirement, endpoint_kind in closure_endpoint_requirements.get(key, ())
        )
        output_end_authority = any(
            endpoint_kind == "output_end" and key[0] == output_end
            for _requirement, endpoint_kind in closure_endpoint_requirements.get(key, ())
        )
        positive_removal_record = any(
            item.stage == "collision_resolution"
            and item.operation == "remove_re_resolved_automatic_positive"
            and item.frame_no == key[0]
            and item.semantic_morph == key[1]
            and item.before_value_hex == float(baseline_value).hex()
            and item.after_value_hex == "0x0.0p+0"
            and any(req.requirement_id in item.requirement_ids for req in matching_requirements)
            for item in plan.transformations
        )
        if not (
            origin == "automatic"
            and baseline_value > 0.0
            and point.value.scalar == 0.0
            and operation is not None
            and (terminal_authority or next_shape_zero_authority or output_end_authority)
            and not re_resolved_positive
            and positive_removal_record
            and point.point_kinds.count("closure_zero") == 1
        ):
            reason = "protected_change_unexplained" if origin in {"manual", "unknown", "mixed"} else "baseline_mismatch"
            issues.append(ClosureIssue(reason, "independent_validation", "candidate changed a key outside the source-resolved terminal/zero-next-shape/output-end repair", key[1], (key[0], key[0]), source_ids))
    for key, point in actual.items():
        if key in expected_baseline:
            continue
        closure_addition_valid = any(
            point.value.scalar == 0.0
            and point.origin == "automatic"
            and "closure_zero" in point.point_kinds
            and _repair_record_covers(
                plan,
                frame_no=key[0],
                semantic_morph=key[1],
                requirement=requirement,
                operation=f"materialize_source_{endpoint_kind}_zero",
            )
            and (endpoint_kind != "next_shape_start" or bool(_source_zero_at(source_points, key[1], key[0])))
            for requirement, endpoint_kind in closure_endpoint_requirements.get(key, ())
        )
        baseline_curve = tuple(sorted(
            (frame, value)
            for (frame, semantic), (value, _origin, _source_ids) in expected_baseline.items()
            if semantic == key[1]
        ))
        silence_addition_valid = any(
            point.value.scalar == 0.0
            and point.origin == "automatic"
            and {"closure_zero", "silence_core_zero"}.issubset(point.point_kinds)
            and _repair_record_covers(plan, frame_no=key[0], semantic_morph=key[1], requirement=requirement, operation=operation)
            for requirement in expected_requirements
            if requirement.kind == "silence_core"
            for frame, operation in _silence_core_boundary_targets(requirement, baseline_curve, source_points)
            if frame == key[0]
        )
        if not (closure_addition_valid or silence_addition_valid):
            issues.append(ClosureIssue("baseline_mismatch", "independent_validation", "candidate added a key outside a source-required closure or silence-core boundary zero", key[1], (key[0], key[0]), point.source_ids, point.requirement_ids))

    for requirement in expected_requirements:
        if requirement.kind in {"per_morph_closure", "silence_core"}:
            if not _exact_zero_interval(plan.points, requirement.semantic_morph, requirement.start_frame, requirement.end_frame):
                issues.append(ClosureIssue("silence_core_violation", "independent_validation", "analytic piecewise-linear interval check found a nonzero or undefined value", requirement.semantic_morph, (requirement.start_frame, requirement.end_frame), requirement.source_ids, (requirement.requirement_id,)))
        elif requirement.kind == "required_zero":
            point = actual.get((requirement.start_frame, requirement.semantic_morph))
            if point is None or point.value.scalar != 0.0:
                issues.append(ClosureIssue("required_zero_missing", "independent_validation", "source-required zero point is missing or nonzero", requirement.semantic_morph, (requirement.start_frame, requirement.end_frame), requirement.source_ids, (requirement.requirement_id,)))
    if plan.state != "valid":
        issues.append(ClosureIssue("input_invalid", "independent_validation", "candidate plan is not marked valid"))
    issues = _dedupe_issues(issues)
    return ClosureValidationResult("valid" if not issues else "invalid", tuple(issues))


def project_validated_closure_candidate(
    result: ClosureBuildResult,
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract | None = None,
) -> tuple[tuple[int, str, float], ...]:
    if not isinstance(result, ClosureBuildResult) or result.state != "valid" or result.plan is None:
        raise ClosurePlanError("only a valid closure candidate can be projected")
    validation = validate_closure_plan(result.plan, issuer_context, closure_contract)
    if validation.state != "valid":
        raise ClosurePlanError("closure candidate no longer validates against its issuer")
    return tuple((item.frame_no, item.semantic_morph, item.value.scalar) for item in result.plan.points)


__all__ = [
    "ClosureExplicitBoundary", "ClosureIssuerContext", "ClosureIssuerError", "ClosureProtectedPoint", "ClosureValidationResult",
    "build_closure_candidate", "project_validated_closure_candidate", "validate_closure_plan",
]
