from __future__ import annotations

import math
import struct
from bisect import bisect_left
from dataclasses import dataclass

try:
    from src.core.final_morph_closure_plan import (
        ClosureBuildResult,
        ClosureContract,
        ClosurePlan,
        ClosurePlanError,
        closure_wire_digest,
        validate_closure_plan_integrity,
    )
    from src.core.morph_closure import ClosureIssuerContext, validate_closure_plan
    from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.final_morph_closure_plan", "src.core.morph_closure", "src.core.morph_name_sets"}:
        raise
    from core.final_morph_closure_plan import (
        ClosureBuildResult,
        ClosureContract,
        ClosurePlan,
        ClosurePlanError,
        closure_wire_digest,
        validate_closure_plan_integrity,
    )
    from core.morph_closure import ClosureIssuerContext, validate_closure_plan
    from core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names


@dataclass(frozen=True, slots=True)
class ClosureWirePoint:
    frame_no: int
    semantic_morph: str
    output_morph_name: str
    binary32_hex: str
    binary32_value: float


@dataclass(frozen=True, slots=True)
class ClosureProjection:
    semantic_points: tuple[tuple[int, str, float], ...]
    wire_points: tuple[ClosureWirePoint, ...]
    wire_digest: str
    binary32_deltas: tuple[tuple[int, str, float], ...]


def project_validated_closure_candidate(
    result: ClosureBuildResult,
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract | None = None,
) -> ClosureProjection:
    if not isinstance(result, ClosureBuildResult) or result.state != "valid" or result.plan is None:
        raise ClosurePlanError("only a valid closure candidate can be projected")
    validation = validate_closure_plan(result.plan, issuer_context, closure_contract)
    if validation.state != "valid":
        raise ClosurePlanError("closure candidate no longer validates against its issuer")
    return _project_closure_plan(result.plan)


def _project_closure_plan(plan: ClosurePlan) -> ClosureProjection:
    """Project a closure plan after its owning outer contract has validated it."""
    if not isinstance(plan, ClosurePlan) or plan.state != "valid":
        raise ClosurePlanError("only a valid closure plan can be projected")
    validate_closure_plan_integrity(plan)
    names = validate_output_morph_names(tuple(name for _, name in plan.identity_context.output_mapping))
    mapping = dict(zip(SEMANTIC_VOWEL_ORDER, names))
    semantic_points = tuple((point.frame_no, point.semantic_morph, point.value.scalar) for point in plan.points)
    wire_points: list[ClosureWirePoint] = []
    deltas: list[tuple[int, str, float]] = []
    for point in plan.points:
        scalar = point.value.scalar
        wire_value = struct.unpack("<f", point.value.binary32_bytes)[0]
        wire_points.append(
            ClosureWirePoint(
                frame_no=point.frame_no,
                semantic_morph=point.semantic_morph,
                output_morph_name=mapping[point.semantic_morph],
                binary32_hex=point.value.binary32_hex,
                binary32_value=wire_value,
            )
        )
        if wire_value != scalar:
            deltas.append((point.frame_no, point.semantic_morph, wire_value - scalar))
    digest = closure_wire_digest(plan.points, plan.identity_context.output_mapping)
    if digest != plan.wire_digest:
        raise ClosurePlanError("projected wire digest differs from validated closure plan")
    return ClosureProjection(semantic_points, tuple(wire_points), digest, tuple(deltas))


def candidate_closure_value(plan: ClosurePlan, semantic_morph: str, frame_no: float) -> float | None:
    """Evaluate only inside the candidate's closed key domain; never extrapolate."""
    if not isinstance(plan, ClosurePlan):
        raise ClosurePlanError("closure plan is invalid")
    if plan.state != "valid":
        raise ClosurePlanError("only a valid closure candidate can be evaluated")
    validate_closure_plan_integrity(plan)
    if semantic_morph not in SEMANTIC_VOWEL_ORDER:
        raise ClosurePlanError("semantic morph is unsupported")
    if isinstance(frame_no, bool) or not isinstance(frame_no, (int, float)):
        raise ClosurePlanError("frame position is invalid")
    try:
        position = float(frame_no)
    except (OverflowError, ValueError) as error:
        raise ClosurePlanError("frame position is invalid") from error
    if not math.isfinite(position) or position < 0.0:
        raise ClosurePlanError("frame position is invalid")
    curve = tuple((item.frame_no, item.value.scalar) for item in plan.points if item.semantic_morph == semantic_morph)
    if not curve or position < curve[0][0] or position > curve[-1][0]:
        return None
    frames = [item[0] for item in curve]
    index = bisect_left(frames, position)
    if index < len(curve) and curve[index][0] == position:
        return curve[index][1]
    if index == 0 or index >= len(curve):
        return None
    left_frame, left_value = curve[index - 1]
    right_frame, right_value = curve[index]
    ratio = (position - left_frame) / (right_frame - left_frame)
    return left_value + (right_value - left_value) * ratio


__all__ = ["ClosureProjection", "ClosureWirePoint", "candidate_closure_value", "project_validated_closure_candidate"]
