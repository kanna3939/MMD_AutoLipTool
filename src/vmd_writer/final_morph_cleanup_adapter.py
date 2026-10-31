"""Verified wire projection for an independently validated MS33-B2 plan."""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

from src.core.event_cleanup import EventCleanupInput, validate_event_cleanup_plan
from src.core.final_morph_cleanup_plan import FinalMorphCleanupPlan, validate_final_morph_cleanup_plan_integrity
from src.core.final_morph_shadow import read_morph_vmd
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names
from src.vmd_writer.final_morph_closure_adapter import ClosureProjection, ClosureWirePoint
from src.vmd_writer.verified_morph_output import VerifiedMorphOutputError, write_verified_morph_vmd


class FinalMorphCleanupAdapterError(ValueError):
    """Raised when a cleanup plan cannot be safely projected or read back."""


@dataclass(frozen=True, slots=True)
class CleanupProjection:
    closure_projection: ClosureProjection
    projection_digest: str
    wire_digest: str


@dataclass(frozen=True, slots=True)
class CleanupReadback:
    status: str
    model_name: str
    record_count: int
    wire_digest: str
    sha256: str
    file_size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, "model_name": self.model_name, "record_count": self.record_count, "wire_digest": self.wire_digest, "sha256": self.sha256, "file_size_bytes": self.file_size_bytes}


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def project_validated_cleanup_plan(plan: FinalMorphCleanupPlan, issuer: EventCleanupInput) -> CleanupProjection:
    if not isinstance(plan, FinalMorphCleanupPlan) or not isinstance(issuer, EventCleanupInput):
        raise FinalMorphCleanupAdapterError("cleanup plan and source issuer are required")
    validation = validate_event_cleanup_plan(plan, issuer)
    if validation.state != "valid" or validation.issues:
        raise FinalMorphCleanupAdapterError("only an independently valid cleanup plan can be projected")
    validate_final_morph_cleanup_plan_integrity(plan)
    mapping_value = plan.identity.get("output_mapping")
    if type(mapping_value) not in (list, tuple):
        raise FinalMorphCleanupAdapterError("cleanup plan output mapping is missing")
    mapping_rows: list[tuple[str, str]] = []
    for row in mapping_value:
        if type(row) not in (list, tuple) or len(row) != 2 or row[0] not in SEMANTIC_VOWEL_ORDER or type(row[1]) is not str or not row[1]:
            raise FinalMorphCleanupAdapterError("cleanup output mapping is invalid")
        mapping_rows.append((row[0], row[1]))
    mapping_names = validate_output_morph_names(tuple(name for _semantic, name in mapping_rows))
    if tuple(name for _semantic, name in mapping_rows) != mapping_names or set(semantic for semantic, _name in mapping_rows) != set(SEMANTIC_VOWEL_ORDER):
        raise FinalMorphCleanupAdapterError("cleanup output mapping does not cover the five vowel morphs")
    output_by_semantic = dict(mapping_rows)
    semantic_points = tuple((item.frame_no, item.semantic_morph, item.canonical_value) for item in plan.points)
    wire_points = tuple(
        ClosureWirePoint(
            frame_no=item.frame_no,
            semantic_morph=item.semantic_morph,
            output_morph_name=output_by_semantic[item.semantic_morph],
            binary32_hex=item.binary32_hex,
            binary32_value=item.wire_value,
        )
        for item in plan.points
    )
    deltas = tuple((item.frame_no, item.semantic_morph, item.wire_value - item.canonical_value) for item in plan.points if item.wire_value != item.canonical_value)
    closure_projection = ClosureProjection(semantic_points, wire_points, plan.wire_digest, deltas)
    projection_digest = _digest({"semantic_digest": plan.semantic_digest, "wire_digest": plan.wire_digest, "points": [item.to_dict() for item in plan.points]})
    return CleanupProjection(closure_projection, projection_digest, plan.wire_digest)


def write_validated_cleanup_vmd(output_path: str | Path, plan: FinalMorphCleanupPlan, issuer: EventCleanupInput, *, model_name: str = "AutoLipTool") -> tuple[Path, CleanupProjection]:
    projection = project_validated_cleanup_plan(plan, issuer)
    path = Path(output_path)
    if path.exists():
        raise FinalMorphCleanupAdapterError("cleanup VMD output already exists")
    try:
        write_verified_morph_vmd(path, projection.closure_projection, model_name=model_name)
    except (OSError, VerifiedMorphOutputError) as error:
        raise FinalMorphCleanupAdapterError("verified cleanup VMD write failed") from error
    return path, projection


def validate_cleanup_vmd_readback(path: str | Path, plan: FinalMorphCleanupPlan, projection: CleanupProjection, *, model_name: str = "AutoLipTool") -> CleanupReadback:
    output = Path(path)
    try:
        payload = output.read_bytes()
    except OSError as error:
        raise FinalMorphCleanupAdapterError("cleanup VMD could not be read back") from error
    try:
        read_model, rows = read_morph_vmd(payload)
    except ValueError as error:
        raise FinalMorphCleanupAdapterError("cleanup VMD readback is invalid") from error
    if read_model != model_name or len(rows) != len(plan.points):
        raise FinalMorphCleanupAdapterError("cleanup VMD model name or record count differs")
    mapping_value = plan.identity.get("output_mapping")
    mapping = {row[0]: row[1] for row in mapping_value}
    expected = tuple((point.frame_no, mapping[point.semantic_morph], point.binary32_hex) for point in plan.points)
    actual = tuple((point.frame_no, point.morph_name, point.value_hex) for point in rows)
    if actual != expected:
        raise FinalMorphCleanupAdapterError("cleanup VMD wire points differ from the validated plan")
    actual_wire_digest = hashlib.sha256(json.dumps({"output_mapping": mapping_value, "points": [{"frame_no": point.frame_no, "semantic_morph": point.semantic_morph, "binary32_hex": point.binary32_hex} for point in plan.points]}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if actual_wire_digest != plan.wire_digest or projection.wire_digest != plan.wire_digest:
        raise FinalMorphCleanupAdapterError("cleanup VMD wire digest differs from the validated plan")
    return CleanupReadback("passed", read_model, len(rows), actual_wire_digest, hashlib.sha256(payload).hexdigest(), len(payload))


__all__ = ["CleanupProjection", "CleanupReadback", "FinalMorphCleanupAdapterError", "project_validated_cleanup_plan", "validate_cleanup_vmd_readback", "write_validated_cleanup_vmd"]
