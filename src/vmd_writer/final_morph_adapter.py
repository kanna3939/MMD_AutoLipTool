"""Validated FinalMorphPlan projections for Preview-like and VMD wire use."""

from __future__ import annotations

import sys

_module_alias = __name__[4:] if __name__.startswith("src.") else "src." + __name__
sys.modules.setdefault(_module_alias, sys.modules[__name__])

import struct
from bisect import bisect_left
from dataclasses import dataclass

try:
    from src.core.final_morph_plan import (
        FinalMorphBuildResult,
        FinalMorphFullSnapshotIssuerContext,
        FinalMorphPlan,
        FinalMorphPlanError,
        validate_plan_integrity,
        validate_final_morph_plan,
        wire_digest_for_points,
    )
    from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names
except ModuleNotFoundError as error:
    if error.name not in {"src", "src.core", "src.core.final_morph_plan", "src.core.morph_name_sets"}:
        raise
    from core.final_morph_plan import (
        FinalMorphBuildResult,
        FinalMorphFullSnapshotIssuerContext,
        FinalMorphPlan,
        FinalMorphPlanError,
        validate_plan_integrity,
        validate_final_morph_plan,
        wire_digest_for_points,
    )
    from core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names


@dataclass(frozen=True, slots=True)
class WireMorphPoint:
    frame_no: int
    semantic_morph: str
    output_morph_name: str
    binary32_hex: str
    binary32_value: float


@dataclass(frozen=True, slots=True)
class FinalMorphProjection:
    semantic_points: tuple[tuple[int, str, float], ...]
    wire_points: tuple[WireMorphPoint, ...]
    wire_digest: str
    binary32_deltas: tuple[tuple[int, str, float], ...]


def project_validated_candidate(
    result: FinalMorphBuildResult,
    issuer_context: FinalMorphFullSnapshotIssuerContext,
) -> FinalMorphProjection:
    """Map once and expose scalar and precomputed binary32 projections."""
    if not isinstance(result, FinalMorphBuildResult) or result.state != "valid" or result.plan is None:
        raise FinalMorphPlanError("only a valid candidate can be projected")
    plan = result.plan
    issues = validate_final_morph_plan(plan, issuer_context)
    if issues:
        raise FinalMorphPlanError("candidate no longer validates against its issuer snapshot")
    validate_plan_integrity(plan)
    names = validate_output_morph_names(tuple(name for _, name in plan.output_mapping))
    mapping = dict(zip(SEMANTIC_VOWEL_ORDER, names))
    semantic_points = tuple(
        (point.frame_no, point.semantic_morph, point.value.scalar)
        for point in plan.points
    )
    wire_points: list[WireMorphPoint] = []
    deltas: list[tuple[int, str, float]] = []
    for point in plan.points:
        raw = point.value.binary32_bytes
        value = struct.unpack("<f", raw)[0]
        wire_points.append(
            WireMorphPoint(
                frame_no=point.frame_no,
                semantic_morph=point.semantic_morph,
                output_morph_name=mapping[point.semantic_morph],
                binary32_hex=raw.hex(),
                binary32_value=value,
            )
        )
        delta = value - point.value.scalar
        if delta:
            deltas.append((point.frame_no, point.semantic_morph, delta))
    projection = FinalMorphProjection(
        semantic_points=semantic_points,
        wire_points=tuple(wire_points),
        wire_digest=wire_digest_for_points(plan.points, plan.output_mapping),
        binary32_deltas=tuple(deltas),
    )
    if projection.wire_digest != plan.wire_digest:
        raise FinalMorphPlanError("projected wire digest differs from the validated plan")
    return projection


def candidate_preview_value(
    plan: FinalMorphPlan,
    issuer_context: FinalMorphFullSnapshotIssuerContext,
    semantic_morph: str,
    frame_no: int,
) -> float | None:
    """Linearly interpolate inside the candidate key domain; return None outside."""
    if validate_final_morph_plan(plan, issuer_context):
        raise FinalMorphPlanError("candidate is not valid against its issuer snapshot")
    validate_plan_integrity(plan)
    if semantic_morph not in SEMANTIC_VOWEL_ORDER:
        raise FinalMorphPlanError("semantic_morph is unsupported")
    if isinstance(frame_no, bool) or not isinstance(frame_no, int) or frame_no < 0:
        raise FinalMorphPlanError("frame_no must be a non-negative integer")
    curve = tuple(
        (point.frame_no, point.value.scalar)
        for point in plan.points
        if point.semantic_morph == semantic_morph
    )
    frames = [item[0] for item in curve]
    if not frames or frame_no < frames[0] or frame_no > frames[-1]:
        return None
    index = bisect_left(frames, frame_no)
    if index < len(curve) and curve[index][0] == frame_no:
        return curve[index][1]
    if index == 0 or index >= len(curve):
        return None
    left_frame, left_value = curve[index - 1]
    right_frame, right_value = curve[index]
    if right_frame <= left_frame:
        raise FinalMorphPlanError("candidate curve frames are not strictly increasing")
    ratio = (frame_no - left_frame) / (right_frame - left_frame)
    return left_value + (right_value - left_value) * ratio


__all__ = [
    "FinalMorphProjection",
    "WireMorphPoint",
    "candidate_preview_value",
    "project_validated_candidate",
]
