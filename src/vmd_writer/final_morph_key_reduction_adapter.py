"""Projection and readback for an independently validated B3 reduction plan."""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

from src.core.final_morph_key_reduction_plan import FinalMorphKeyReductionPlan, KeyReductionInput, KeyReductionPlanError
from src.core.final_morph_shadow import compare_wire_readback, read_morph_vmd
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names
from src.core.redundant_key_reduction import validate_key_reduction_plan
from src.vmd_writer.final_morph_closure_adapter import ClosureProjection, ClosureWirePoint
from src.vmd_writer.verified_morph_output import write_verified_morph_vmd


class FinalMorphKeyReductionAdapterError(ValueError):
    """Raised when a B3 candidate cannot be safely projected or read back."""


@dataclass(frozen=True, slots=True)
class KeyReductionProjection:
    output_mapping: tuple[tuple[str, str], ...]
    wire_points: tuple[ClosureWirePoint, ...]
    wire_digest: str


@dataclass(frozen=True, slots=True)
class KeyReductionReadback:
    status: str
    model_name: str
    record_count: int
    wire_digest: str
    records_equal: bool
    mismatches: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_id": "ms33-b3-readback/v1",
            "status": self.status,
            "model_name": self.model_name,
            "record_count": self.record_count,
            "wire_digest": self.wire_digest,
            "records_equal": self.records_equal,
            "mismatches": list(self.mismatches),
        }


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def project_validated_key_reduction_plan(
    plan: FinalMorphKeyReductionPlan, issuer: KeyReductionInput,
) -> KeyReductionProjection:
    validation = validate_key_reduction_plan(plan, issuer)
    if validation.state != "valid":
        raise FinalMorphKeyReductionAdapterError("only an independently valid key reduction plan can be projected")
    raw_mapping = issuer.source_binding.get("output_mapping")
    if type(raw_mapping) not in (list, tuple) or len(raw_mapping) != len(SEMANTIC_VOWEL_ORDER):
        raise FinalMorphKeyReductionAdapterError("source output mapping is missing or incomplete")
    mapping_rows: list[tuple[str, str]] = []
    for row in raw_mapping:
        if type(row) not in (list, tuple) or len(row) != 2 or any(type(item) is not str for item in row):
            raise FinalMorphKeyReductionAdapterError("source output mapping is malformed")
        mapping_rows.append((row[0], row[1]))
    mapping = tuple(mapping_rows)
    if tuple(item[0] for item in mapping) != SEMANTIC_VOWEL_ORDER:
        raise FinalMorphKeyReductionAdapterError("source output mapping order is invalid")
    validate_output_morph_names(tuple(item[1] for item in mapping))
    names = dict(mapping)
    wire_points = tuple(
        ClosureWirePoint(
            frame_no=point.frame_no,
            semantic_morph=point.semantic_morph,
            output_morph_name=names[point.semantic_morph],
            binary32_hex=point.canonical_value.binary32_hex,
            binary32_value=struct.unpack("<f", point.canonical_value.binary32_bytes)[0],
        )
        for point in plan.points
    )
    digest = _digest([
        {"frame_no": row.frame_no, "semantic_morph": row.semantic_morph, "output_morph_name": row.output_morph_name, "binary32_hex": row.binary32_hex}
        for row in wire_points
    ])
    if digest != plan.wire_digest:
        raise FinalMorphKeyReductionAdapterError("plan wire digest does not match the projected mapping")
    return KeyReductionProjection(mapping, wire_points, digest)


def write_validated_key_reduction_vmd(
    output_path: str | Path,
    plan: FinalMorphKeyReductionPlan,
    issuer: KeyReductionInput,
    *,
    model_name: str,
) -> tuple[Path, KeyReductionProjection]:
    output = Path(output_path)
    if output.exists():
        raise FinalMorphKeyReductionAdapterError("refusing to overwrite an existing B3 VMD candidate")
    projection = project_validated_key_reduction_plan(plan, issuer)
    closure_projection = ClosureProjection(
        semantic_points=tuple((item.frame_no, item.semantic_morph, item.canonical_value.scalar) for item in plan.points),
        wire_points=projection.wire_points,
        wire_digest=projection.wire_digest,
        binary32_deltas=tuple(
            (wire.frame_no, wire.semantic_morph, wire.binary32_value - item.canonical_value.scalar)
            for item, wire in zip(plan.points, projection.wire_points, strict=True)
            if wire.binary32_value != item.canonical_value.scalar
        ),
    )
    try:
        write_verified_morph_vmd(output, closure_projection, model_name=model_name)
    except (OSError, ValueError, TypeError) as error:
        raise FinalMorphKeyReductionAdapterError("verified VMD writer rejected the B3 projection") from error
    return output, projection


def validate_key_reduction_vmd_readback(
    path: str | Path,
    projection: KeyReductionProjection,
    *,
    model_name: str,
) -> KeyReductionReadback:
    candidate = Path(path)
    try:
        saved_model_name, actual = read_morph_vmd(candidate.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise FinalMorphKeyReductionAdapterError("B3 candidate VMD could not be read independently") from error
    expected = tuple((point.frame_no, point.output_morph_name, bytes.fromhex(point.binary32_hex)) for point in projection.wire_points)
    comparison = compare_wire_readback(expected, actual)
    issues: list[str] = []
    if saved_model_name != model_name:
        issues.append("model_name_mismatch")
    if not comparison["equal"]:
        issues.append("wire_records_mismatch")
    semantic_by_name = {name: semantic for semantic, name in projection.output_mapping}
    digest = _digest([
        {
            "frame_no": point.frame_no,
            "semantic_morph": semantic_by_name.get(point.morph_name),
            "output_morph_name": point.morph_name,
            "binary32_hex": point.value_hex,
        }
        for point in actual
    ])
    if digest != projection.wire_digest:
        issues.append("wire_digest_mismatch")
    return KeyReductionReadback(
        status="passed" if not issues else "failed",
        model_name=saved_model_name,
        record_count=len(actual),
        wire_digest=digest,
        records_equal=bool(comparison["equal"]),
        mismatches=tuple([*issues, *comparison["mismatches"]]),
    )


__all__ = [
    "FinalMorphKeyReductionAdapterError", "KeyReductionProjection", "KeyReductionReadback",
    "project_validated_key_reduction_plan", "validate_key_reduction_vmd_readback",
    "write_validated_key_reduction_vmd",
]
