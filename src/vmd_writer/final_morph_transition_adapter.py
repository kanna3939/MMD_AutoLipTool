"""Verified wire projection for the MS32 outer transition contract."""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.core.cross_vowel_transition import TransitionResolution
from src.core.final_morph_closure_plan import closure_plan_from_json
from src.core.final_morph_transition_plan import (
    FinalMorphTransitionPlan,
    TransitionPlanIssuerContext,
    validate_transition_plan,
)
from src.core.morph_closure import build_closure_candidate
from src.core.final_morph_shadow import read_morph_vmd
from src.vmd_writer.final_morph_closure_adapter import (
    ClosureProjection,
    ClosureWirePoint,
    _project_closure_plan,
)
from src.vmd_writer.verified_morph_output import (
    VerifiedMorphOutputError,
    VerifiedVmdEvidence,
    validate_verified_morph_readback,
    write_verified_morph_vmd,
)
from src.core.effective_shape_plan import ShapeControlPoint


class TransitionProjectionError(ValueError):
    """The outer transition plan cannot be projected to a verified wire view."""


@dataclass(frozen=True, slots=True)
class TransitionProjection:
    transition_plan_digest: str
    source_lineage_digest: str
    policy_digest: str
    closure_projection: ClosureProjection
    projection_digest: str

    @property
    def semantic_points(self) -> tuple[tuple[int, str, float], ...]:
        return self.closure_projection.semantic_points

    @property
    def wire_points(self) -> tuple[ClosureWirePoint, ...]:
        return self.closure_projection.wire_points

    @property
    def wire_digest(self) -> str:
        return self.closure_projection.wire_digest


@dataclass(frozen=True, slots=True)
class TransitionReadbackMeasurement:
    previous_event_index: int
    next_event_index: int
    previous_morph: str
    next_morph: str
    baseline_overlap_width_frames: float
    candidate_overlap_width_frames: float
    overlap_width_delta_frames: float
    baseline_positive_integer_frames: tuple[int, ...]
    candidate_positive_integer_frames: tuple[int, ...]
    positive_integer_frame_delta: int
    candidate_start_frame: int
    baseline_start_frame: int
    value_at_baseline_start: float


@dataclass(frozen=True, slots=True)
class TransitionVmdEvidence:
    transition_plan_digest: str
    projection_digest: str
    wire_digest: str
    verified_vmd: VerifiedVmdEvidence
    applied_transition_count: int
    readback_transition_count: int
    readback_measurements: tuple[TransitionReadbackMeasurement, ...] = ()


def _projection_digest(
    plan: FinalMorphTransitionPlan,
    closure_projection: ClosureProjection,
) -> str:
    payload = {
        "transition_plan_digest": plan.semantic_digest,
        "source_lineage_digest": plan.identity_context.source_lineage.lineage_digest,
        "policy_digest": plan.identity_context.policy_digest,
        "closure_wire_digest": closure_projection.wire_digest,
        "wire_records": [
            [item.output_morph_name, item.frame_no, item.binary32_hex]
            for item in closure_projection.wire_points
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def project_validated_transition_plan(
    plan: FinalMorphTransitionPlan,
    *,
    issuer_context: TransitionPlanIssuerContext,
    resolution: TransitionResolution,
) -> TransitionProjection:
    validation = validate_transition_plan(
        plan,
        issuer_context=issuer_context,
        resolution=resolution,
    )
    if validation.state != "valid":
        raise TransitionProjectionError("transition plan no longer validates against its full issuer")
    closure_plan = closure_plan_from_json(plan.closure_plan_json)
    try:
        closure_projection = _project_closure_plan(closure_plan)
    except (TypeError, ValueError, RuntimeError) as error:
        raise TransitionProjectionError("closure subproof could not be projected") from error
    if closure_projection.wire_digest != plan.identity_context.closure_wire_digest:
        raise TransitionProjectionError("wire digest differs from outer transition identity")
    return TransitionProjection(
        transition_plan_digest=plan.semantic_digest,
        source_lineage_digest=plan.identity_context.source_lineage.lineage_digest,
        policy_digest=plan.identity_context.policy_digest,
        closure_projection=closure_projection,
        projection_digest=_projection_digest(plan, closure_projection),
    )


def _curve_value(points: Sequence[ShapeControlPoint], frame: float) -> float | None:
    if not points or frame < points[0].frame_no or frame > points[-1].frame_no:
        return None
    for point in points:
        if frame == point.frame_no:
            return point.value
    for left, right in zip(points, points[1:]):
        if left.frame_no < frame < right.frame_no:
            ratio = (frame - left.frame_no) / (right.frame_no - left.frame_no)
            return left.value + (right.value - left.value) * ratio
    return None


def _positive_intersection_width(
    left: Sequence[ShapeControlPoint],
    right: Sequence[ShapeControlPoint],
    *,
    start_frame: int,
    end_frame: int,
) -> float:
    low = max(float(start_frame), float(left[0].frame_no), float(right[0].frame_no))
    high = min(float(end_frame), float(left[-1].frame_no), float(right[-1].frame_no))
    if high <= low:
        return 0.0
    breaks = {low, high}
    for curve in (left, right):
        for point in curve:
            if low < point.frame_no < high:
                breaks.add(float(point.frame_no))
        for first, second in zip(curve, curve[1:]):
            if second.value == first.value:
                continue
            fraction = -first.value / (second.value - first.value)
            if 0.0 < fraction < 1.0:
                root = first.frame_no + (second.frame_no - first.frame_no) * fraction
                if low < root < high:
                    breaks.add(root)
    ordered = sorted(breaks)
    width = 0.0
    for first, second in zip(ordered, ordered[1:]):
        middle = (first + second) / 2.0
        a = _curve_value(left, middle)
        b = _curve_value(right, middle)
        if a is not None and b is not None and a > 0.0 and b > 0.0:
            width += second - first
    return width


def _verify_transition_readback(
    points: tuple[Any, ...],
    issuer_context: TransitionPlanIssuerContext,
    resolution: TransitionResolution,
) -> tuple[TransitionReadbackMeasurement, ...]:
    if resolution.schedule is not None:
        from src.core.bounded_transition import verify_bounded_issuer
        from src.core.short_vowel_schedule import curve_value
        resolved = verify_bounded_issuer(issuer_context, resolution)
        mapping = dict(issuer_context.closure_issuer_context.legacy_context.identity_context.output_mapping)
        by_morph = {v: [] for v in mapping}
        for point in points:
            for semantic, name in mapping.items():
                if name == point.morph_name:
                    by_morph[semantic].append(ShapeControlPoint(point.frame_no, point.value, "wire_readback"))
        for curve in by_morph.values():
            curve.sort(key=lambda p: p.frame_no)
        breaks=sorted({p.frame_no for curve in by_morph.values() for p in curve})
        for x in breaks+[(a+b)/2 for a,b in zip(breaks,breaks[1:])]:
            if sum(curve_value(curve,x)>0 for curve in by_morph.values())>2:
                exceptions=[resolved.shapes[i] for i,_reason in resolution.schedule.unresolved]
                if not any(s.start_frame<=x<=s.end_frame for s in exceptions):
                    raise TransitionProjectionError("wire readback contains unissued triple-vowel overlap")
        # Required closures are checked by the exact verified projection above.
        # Also check every protected short peak against actual binary32 output.
        for change in resolution.schedule.changes:
            if change.action == "short_pulse":
                shape = resolved.shapes[change.shape_index]
                peak = max(shape.control_points, key=lambda p: p.value)
                if curve_value(by_morph[shape.vowel], peak.frame_no) <= 0:
                    raise TransitionProjectionError("wire readback lost a rescued short vowel")
        return tuple(TransitionReadbackMeasurement(
            d.previous_event_index,d.next_event_index,d.previous_morph,d.next_morph,
            d.baseline_overlap_width_frames,d.candidate_overlap_width_frames,d.overlap_width_delta_frames,
            d.baseline_positive_integer_frames,d.candidate_positive_integer_frames,
            len(d.candidate_positive_integer_frames)-len(d.baseline_positive_integer_frames),
            d.candidate_start_frame,d.baseline_start_frame,
            curve_value(by_morph[d.next_morph],d.baseline_start_frame))
            for d in resolution.decisions if d.state == "applied")
    if not any(item.state == "applied" for item in resolution.decisions):
        return ()
    output_by_semantic = dict(
        issuer_context.closure_issuer_context.legacy_context.identity_context.output_mapping
    )
    semantic_by_output = {name: semantic for semantic, name in output_by_semantic.items()}
    by_morph: dict[str, list[ShapeControlPoint]] = {}
    for point in points:
        semantic = next((key for key, value in output_by_semantic.items() if value == point.morph_name), None)
        if semantic is None:
            continue
        by_morph.setdefault(semantic, []).append(
            ShapeControlPoint(point.frame_no, point.value, "wire_readback")
        )
    for semantic in by_morph:
        by_morph[semantic].sort(key=lambda item: item.frame_no)
        frames = [item.frame_no for item in by_morph[semantic]]
        if len(frames) != len(set(frames)):
            raise TransitionProjectionError("wire readback contains duplicate semantic morph frames")
    baseline_closure = build_closure_candidate(issuer_context.closure_issuer_context)
    if baseline_closure.state != "valid" or baseline_closure.plan is None:
        raise TransitionProjectionError("original closure baseline cannot be reissued for readback comparison")
    baseline_projection = _project_closure_plan(baseline_closure.plan)
    baseline_by_morph: dict[str, list[ShapeControlPoint]] = {}
    for item in baseline_projection.wire_points:
        semantic = semantic_by_output.get(item.output_morph_name)
        if semantic is None:
            raise TransitionProjectionError("baseline closure wire contains an unmapped morph")
        value = struct.unpack("<f", bytes.fromhex(item.binary32_hex))[0]
        baseline_by_morph.setdefault(semantic, []).append(
            ShapeControlPoint(item.frame_no, value, "wire_readback")
        )
    for semantic in baseline_by_morph:
        baseline_by_morph[semantic].sort(key=lambda item: item.frame_no)
    measurements: list[TransitionReadbackMeasurement] = []
    for decision, pair in zip(resolution.decisions, issuer_context.pairs, strict=True):
        if decision.state != "applied":
            continue
        target = by_morph.get(pair.next_morph, [])
        previous = by_morph.get(pair.previous_morph, [])
        baseline_target = baseline_by_morph.get(pair.next_morph, [])
        baseline_previous = baseline_by_morph.get(pair.previous_morph, [])
        if not target or not previous or not baseline_target or not baseline_previous:
            raise TransitionProjectionError("wire readback is missing a transition or baseline morph curve")
        if not any(
            item.frame_no == decision.candidate_start_frame and item.value == 0.0
            for item in target
        ):
            raise TransitionProjectionError("wire readback lost the issued structural start zero")
        candidate_width = _positive_intersection_width(
            previous,
            target,
            start_frame=pair.previous_event_peak_frame,
            end_frame=pair.next_event_peak_frame,
        )
        baseline_width = _positive_intersection_width(
            baseline_previous,
            baseline_target,
            start_frame=pair.previous_event_peak_frame,
            end_frame=pair.next_event_peak_frame,
        )
        width_delta = candidate_width - baseline_width
        if width_delta <= 1e-9:
            raise TransitionProjectionError("wire readback did not add positive overlap to the current closure baseline")
        if width_delta > issuer_context.input_snapshot.policy.maximum_continuous_overlap_width_delta_frames + 1e-4:
            raise TransitionProjectionError("wire readback exceeds the continuous overlap width cap")
        baseline_integer_frames = tuple(
            frame
            for frame in range(pair.previous_event_peak_frame, pair.next_event_peak_frame + 1)
            if (_curve_value(baseline_previous, frame) or 0.0) > 0.0
            and (_curve_value(baseline_target, frame) or 0.0) > 0.0
        )
        candidate_integer_frames = tuple(
            frame
            for frame in range(pair.previous_event_peak_frame, pair.next_event_peak_frame + 1)
            if (_curve_value(previous, frame) or 0.0) > 0.0 and (_curve_value(target, frame) or 0.0) > 0.0
        )
        integer_delta = len(candidate_integer_frames) - len(baseline_integer_frames)
        if (
            integer_delta < 0
            or integer_delta > issuer_context.input_snapshot.policy.maximum_positive_integer_overlap_frame_count_delta
            or not set(baseline_integer_frames).issubset(candidate_integer_frames)
        ):
            raise TransitionProjectionError("wire readback integer overlap differs from the current closure baseline")
        value_at_baseline_start = _curve_value(target, decision.baseline_start_frame)
        if value_at_baseline_start is None or value_at_baseline_start <= 0.0:
            raise TransitionProjectionError("wire readback did not materialize the advanced onset")
        measurements.append(TransitionReadbackMeasurement(
            previous_event_index=decision.previous_event_index,
            next_event_index=decision.next_event_index,
            previous_morph=decision.previous_morph,
            next_morph=decision.next_morph,
            baseline_overlap_width_frames=baseline_width,
            candidate_overlap_width_frames=candidate_width,
            overlap_width_delta_frames=width_delta,
            baseline_positive_integer_frames=baseline_integer_frames,
            candidate_positive_integer_frames=candidate_integer_frames,
            positive_integer_frame_delta=integer_delta,
            candidate_start_frame=decision.candidate_start_frame,
            baseline_start_frame=decision.baseline_start_frame,
            value_at_baseline_start=value_at_baseline_start,
        ))
    return tuple(measurements)


def write_validated_transition_vmd(
    output_path: str | Path,
    plan: FinalMorphTransitionPlan,
    *,
    issuer_context: TransitionPlanIssuerContext,
    resolution: TransitionResolution,
    model_name: str,
) -> TransitionVmdEvidence:
    projection = project_validated_transition_plan(
        plan,
        issuer_context=issuer_context,
        resolution=resolution,
    )
    try:
        output = write_verified_morph_vmd(
            output_path,
            projection.closure_projection,
            model_name=model_name,
        )
        closure_plan = closure_plan_from_json(plan.closure_plan_json)
        verified = validate_verified_morph_readback(
            output,
            projection.closure_projection,
            closure_plan,
            model_name=model_name,
        )
        readback_measurements = validate_transition_vmd_readback(
            output,
            plan,
            issuer_context=issuer_context,
            resolution=resolution,
            model_name=model_name,
            projection=projection,
        )
    except (OSError, RuntimeError, TypeError, ValueError, VerifiedMorphOutputError) as error:
        raise TransitionProjectionError("verified transition VMD write/readback failed") from error
    applied_count = sum(item.state == "applied" for item in resolution.decisions)
    return TransitionVmdEvidence(
        transition_plan_digest=plan.semantic_digest,
        projection_digest=projection.projection_digest,
        wire_digest=projection.wire_digest,
        verified_vmd=verified,
        applied_transition_count=applied_count,
        readback_transition_count=len(readback_measurements),
        readback_measurements=readback_measurements,
    )


def validate_transition_vmd_readback(
    output_path: str | Path,
    plan: FinalMorphTransitionPlan,
    *,
    issuer_context: TransitionPlanIssuerContext,
    resolution: TransitionResolution,
    model_name: str,
    projection: TransitionProjection | None = None,
) -> tuple[TransitionReadbackMeasurement, ...]:
    """Recheck both closure wire and applied-transition readback for an existing VMD."""
    verified_projection = project_validated_transition_plan(
        plan,
        issuer_context=issuer_context,
        resolution=resolution,
    )
    if projection is not None and projection != verified_projection:
        raise TransitionProjectionError("transition projection differs from the full issuer")
    closure_plan = closure_plan_from_json(plan.closure_plan_json)
    try:
        validate_verified_morph_readback(
            output_path,
            verified_projection.closure_projection,
            closure_plan,
            model_name=model_name,
        )
        decoded_model, readback_points = read_morph_vmd(Path(output_path).read_bytes())
    except (OSError, RuntimeError, TypeError, ValueError, VerifiedMorphOutputError) as error:
        raise TransitionProjectionError("transition VMD wire readback is invalid") from error
    if decoded_model != model_name:
        raise TransitionProjectionError("transition VMD model identity changed during readback")
    measurements = _verify_transition_readback(
        readback_points,
        issuer_context,
        resolution,
    )
    applied_count = sum(item.state == "applied" for item in resolution.decisions)
    if len(measurements) != applied_count:
        raise TransitionProjectionError("readback did not verify every applied transition")
    return measurements


__all__ = [
    "TransitionProjection",
    "TransitionProjectionError",
    "TransitionReadbackMeasurement",
    "TransitionVmdEvidence",
    "project_validated_transition_plan",
    "validate_transition_vmd_readback",
    "write_validated_transition_vmd",
]
