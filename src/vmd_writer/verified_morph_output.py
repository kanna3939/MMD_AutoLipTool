from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from src.core.final_morph_closure_plan import (
    ClosurePlan,
    ClosureRequirement,
    closure_wire_digest,
    validate_closure_plan_integrity,
)
from src.core.final_morph_shadow import (
    ShadowComparisonError,
    WireReadbackPoint,
    compare_wire_readback,
    read_morph_vmd,
)
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names
from src.vmd_writer.final_morph_closure_adapter import ClosureProjection, ClosureWirePoint
from src.vmd_writer.writer import MAX_MORPH_FRAMES


_VMD_HEADER = b"Vocaloid Motion Data 0002".ljust(30, b"\0")


class VerifiedMorphOutputError(ValueError):
    """Raised when verified wire output cannot be written or proven."""


@dataclass(frozen=True, slots=True)
class VerifiedVmdEvidence:
    path: Path
    file_size_bytes: int
    file_sha256: str
    file_identity: tuple[int | None, int | None, int | None, int]
    model_name: str
    output_mapping: tuple[tuple[str, str], ...]
    semantic_digest: str
    wire_digest: str
    record_count: int
    requirement_ids: tuple[str, ...]
    closure_verified: bool


def _fixed_shift_jis(value: str, width: int, field_name: str) -> bytes:
    if type(value) is not str or not value or any(
        ord(character) < 0x20 or ord(character) == 0x7F for character in value
    ):
        raise VerifiedMorphOutputError(f"{field_name} is invalid")
    try:
        encoded = value.encode("shift_jis", errors="strict")
    except UnicodeEncodeError as error:
        raise VerifiedMorphOutputError(f"{field_name} cannot be encoded as Shift-JIS") from error
    if len(encoded) > width or b"\0" in encoded:
        raise VerifiedMorphOutputError(f"{field_name} exceeds its fixed VMD field")
    return encoded.ljust(width, b"\0")


def _validated_rows(
    projection: ClosureProjection,
) -> tuple[tuple[ClosureWirePoint, bytes], ...]:
    if not isinstance(projection, ClosureProjection):
        raise VerifiedMorphOutputError("projection is invalid")
    rows: list[tuple[ClosureWirePoint, bytes]] = []
    seen: set[tuple[int, str]] = set()
    output_by_semantic: dict[str, str] = {}
    semantic_by_output: dict[str, str] = {}
    previous: tuple[int, int] | None = None
    for index, point in enumerate(projection.wire_points):
        if not isinstance(point, ClosureWirePoint):
            raise VerifiedMorphOutputError(f"wire point {index} is invalid")
        if (
            isinstance(point.frame_no, bool)
            or not isinstance(point.frame_no, int)
            or point.frame_no < 0
            or point.frame_no > 0xFFFFFFFF
        ):
            raise VerifiedMorphOutputError(f"wire point {index} has an invalid frame")
        if point.semantic_morph not in SEMANTIC_VOWEL_ORDER:
            raise VerifiedMorphOutputError(f"wire point {index} has an invalid semantic morph")
        if type(point.output_morph_name) is not str or not point.output_morph_name:
            raise VerifiedMorphOutputError(f"wire point {index} has an invalid output name")
        if (
            point.semantic_morph in output_by_semantic
            and output_by_semantic[point.semantic_morph] != point.output_morph_name
        ):
            raise VerifiedMorphOutputError("one semantic morph maps to multiple output names")
        if (
            point.output_morph_name in semantic_by_output
            and semantic_by_output[point.output_morph_name] != point.semantic_morph
        ):
            raise VerifiedMorphOutputError("output mapping is ambiguous")
        output_by_semantic[point.semantic_morph] = point.output_morph_name
        semantic_by_output[point.output_morph_name] = point.semantic_morph
        try:
            raw = bytes.fromhex(point.binary32_hex)
        except (TypeError, ValueError) as error:
            raise VerifiedMorphOutputError(f"wire point {index} has invalid binary32 bytes") from error
        if len(raw) != 4 or raw.hex() != point.binary32_hex.lower():
            raise VerifiedMorphOutputError(f"wire point {index} has non-canonical binary32 bytes")
        value = struct.unpack("<f", raw)[0]
        if not math.isfinite(value) or value < 0.0 or value != point.binary32_value:
            raise VerifiedMorphOutputError(f"wire point {index} has an invalid binary32 value")
        if value == 0.0 and raw != b"\0\0\0\0":
            raise VerifiedMorphOutputError(f"wire point {index} uses non-canonical signed zero")
        key = (point.frame_no, point.semantic_morph)
        if key in seen:
            raise VerifiedMorphOutputError("wire points contain duplicate semantic keys")
        seen.add(key)
        order_key = (point.frame_no, SEMANTIC_VOWEL_ORDER.index(point.semantic_morph))
        if previous is not None and order_key < previous:
            raise VerifiedMorphOutputError("wire points are not in canonical order")
        previous = order_key
        rows.append((point, raw))
    if len(rows) > MAX_MORPH_FRAMES:
        raise VerifiedMorphOutputError("wire point count exceeds the VMD frame limit")
    if len(semantic_by_output) > len(SEMANTIC_VOWEL_ORDER):
        raise VerifiedMorphOutputError("wire points contain unsupported output names")
    return tuple(rows)


def write_verified_morph_vmd(
    output_path: str | Path,
    projection: ClosureProjection,
    *,
    model_name: str,
) -> Path:
    """Write the already-validated binary32 wire records without re-quantizing them."""
    rows = _validated_rows(projection)
    model_field = _fixed_shift_jis(model_name, 20, "model name")
    name_fields = tuple(
        _fixed_shift_jis(point.output_morph_name, 15, "morph name")
        for point, _value_bytes in rows
    )
    output = Path(output_path)
    with output.open("wb") as stream:
        stream.write(_VMD_HEADER)
        stream.write(model_field)
        stream.write(struct.pack("<I", 0))
        stream.write(struct.pack("<I", len(rows)))
        for (point, value_bytes), name_field in zip(rows, name_fields, strict=True):
            stream.write(name_field)
            stream.write(struct.pack("<I", point.frame_no))
            stream.write(value_bytes)
        stream.write(struct.pack("<IIII", 0, 0, 0, 0))
    return output


def _fraction_at(curve: tuple[WireReadbackPoint, ...], frame: int) -> Fraction:
    if not curve or frame < curve[0].frame_no or frame > curve[-1].frame_no:
        raise VerifiedMorphOutputError("closure requirement exceeds the wire curve domain")
    for point in curve:
        if point.frame_no == frame:
            return Fraction.from_float(point.value)
    for left, right in zip(curve, curve[1:]):
        if left.frame_no < frame < right.frame_no:
            left_value = Fraction.from_float(left.value)
            right_value = Fraction.from_float(right.value)
            ratio = Fraction(frame - left.frame_no, right.frame_no - left.frame_no)
            return left_value + (right_value - left_value) * ratio
    raise VerifiedMorphOutputError("closure boundary cannot be evaluated")


def _verify_requirement(
    requirement: ClosureRequirement,
    curve: tuple[WireReadbackPoint, ...],
) -> None:
    if requirement.kind == "required_zero":
        if requirement.start_frame != requirement.end_frame:
            raise VerifiedMorphOutputError("required_zero must identify exactly one frame")
        value = _fraction_at(curve, requirement.start_frame)
        if value != 0:
            raise VerifiedMorphOutputError("required_zero is non-zero on the wire curve")
        if requirement.endpoint_policy == "explicit_key_exact_zero" and not any(
            point.frame_no == requirement.start_frame and point.value_bytes == b"\0\0\0\0"
            for point in curve
        ):
            raise VerifiedMorphOutputError("required_zero has no explicit zero key")
        return

    start = requirement.start_frame
    end = requirement.end_frame
    start_value = _fraction_at(curve, start)
    end_value = _fraction_at(curve, end)
    if start_value != 0 or end_value != 0:
        raise VerifiedMorphOutputError("closure interval boundary is non-zero")
    if any(start <= point.frame_no <= end and point.value_bytes != b"\0\0\0\0" for point in curve):
        raise VerifiedMorphOutputError("closure interval contains a non-zero key")

    if requirement.endpoint_policy == "explicit_key_exact_zero":
        for frame in {start, end}:
            if not any(
                point.frame_no == frame and point.value_bytes == b"\0\0\0\0"
                for point in curve
            ):
                raise VerifiedMorphOutputError("closure endpoint has no explicit zero key")

    if start == end:
        return
    for left, right in zip(curve, curve[1:]):
        overlap_start = max(start, left.frame_no)
        overlap_end = min(end, right.frame_no)
        if overlap_start > overlap_end:
            continue
        left_value = _fraction_at(curve, overlap_start)
        right_value = _fraction_at(curve, overlap_end)
        if overlap_start < overlap_end and (left_value != 0 or right_value != 0):
            raise VerifiedMorphOutputError("closure interval crosses a non-zero wire segment")
        if overlap_start == overlap_end and left_value != 0:
            raise VerifiedMorphOutputError("closure interval touches a non-zero wire value")


def validate_verified_morph_readback(
    output_path: str | Path,
    projection: ClosureProjection,
    plan: ClosurePlan,
    *,
    model_name: str,
) -> VerifiedVmdEvidence:
    """Independently decode, compare every wire record, and prove closure requirements."""
    if not isinstance(plan, ClosurePlan) or plan.state != "valid":
        raise VerifiedMorphOutputError("closure plan is not valid")
    try:
        validate_closure_plan_integrity(plan)
    except (TypeError, ValueError) as error:
        raise VerifiedMorphOutputError("closure plan integrity check failed") from error
    rows = _validated_rows(projection)
    mapping = tuple(plan.identity_context.output_mapping)
    if projection.wire_digest != plan.wire_digest or closure_wire_digest(
        plan.points,
        mapping,
    ) != plan.wire_digest:
        raise VerifiedMorphOutputError("projection digest differs from closure plan")
    output_by_semantic = dict(mapping)
    expected_projection = tuple(
        (
            point.frame_no,
            point.semantic_morph,
            output_by_semantic[point.semantic_morph],
            point.value.binary32_hex,
        )
        for point in plan.points
    )
    actual_projection = tuple(
        (point.frame_no, point.semantic_morph, point.output_morph_name, point.binary32_hex)
        for point, _raw in rows
    )
    if actual_projection != expected_projection:
        raise VerifiedMorphOutputError("projection records differ from the validated closure plan")
    try:
        output = Path(output_path).resolve(strict=True)
        before_stat = output.stat()
        data = output.read_bytes()
        decoded_model, points = read_morph_vmd(data)
        file_stat = output.stat()
    except (OSError, RuntimeError, TypeError, ValueError, ShadowComparisonError) as error:
        raise VerifiedMorphOutputError("generated VMD could not be independently read") from error
    before_identity = (
        getattr(before_stat, "st_dev", None),
        getattr(before_stat, "st_ino", None),
        getattr(before_stat, "st_mtime_ns", None),
        int(before_stat.st_size),
    )
    read_identity = (
        getattr(file_stat, "st_dev", None),
        getattr(file_stat, "st_ino", None),
        getattr(file_stat, "st_mtime_ns", None),
        int(file_stat.st_size),
    )
    if before_identity != read_identity or len(data) != file_stat.st_size:
        raise VerifiedMorphOutputError("generated VMD changed during independent readback")
    if decoded_model != model_name:
        raise VerifiedMorphOutputError("readback model name differs from the request")
    expected = tuple(
        (point.frame_no, point.output_morph_name, raw) for point, raw in rows
    )
    comparison = compare_wire_readback(expected, points)
    if comparison["equal"] is not True:
        raise VerifiedMorphOutputError("readback records differ from the validated wire projection")

    validate_output_morph_names(tuple(name for _, name in mapping))
    output_to_semantic = {name: semantic for semantic, name in mapping}
    if len(output_to_semantic) != len(mapping):
        raise VerifiedMorphOutputError("output mapping is ambiguous")
    curves: dict[str, tuple[WireReadbackPoint, ...]] = {}
    mutable_curves: dict[str, list[WireReadbackPoint]] = {
        semantic: [] for semantic in SEMANTIC_VOWEL_ORDER
    }
    for point in points:
        semantic = output_to_semantic.get(point.morph_name)
        if semantic is None:
            raise VerifiedMorphOutputError("readback morph name is outside the committed mapping")
        mutable_curves[semantic].append(point)
    for semantic, curve_points in mutable_curves.items():
        curve = tuple(curve_points)
        if any(left.frame_no >= right.frame_no for left, right in zip(curve, curve[1:])):
            raise VerifiedMorphOutputError("readback curve contains duplicate or unordered frames")
        curves[semantic] = curve
    for requirement in plan.requirements:
        _verify_requirement(requirement, curves[requirement.semantic_morph])

    return VerifiedVmdEvidence(
        path=output,
        file_size_bytes=len(data),
        file_sha256=hashlib.sha256(data).hexdigest(),
        file_identity=(
            getattr(file_stat, "st_dev", None),
            getattr(file_stat, "st_ino", None),
            getattr(file_stat, "st_mtime_ns", None),
            int(file_stat.st_size),
        ),
        model_name=model_name,
        output_mapping=mapping,
        semantic_digest=plan.semantic_digest,
        wire_digest=plan.wire_digest,
        record_count=len(points),
        requirement_ids=tuple(requirement.requirement_id for requirement in plan.requirements),
        closure_verified=True,
    )


def verify_evidence_unchanged(evidence: VerifiedVmdEvidence) -> bool:
    if not isinstance(evidence, VerifiedVmdEvidence):
        return False
    try:
        path = evidence.path.resolve(strict=True)
        before_stat = path.stat()
        data = path.read_bytes()
        file_stat = path.stat()
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    identity_before = (
        getattr(before_stat, "st_dev", None),
        getattr(before_stat, "st_ino", None),
        getattr(before_stat, "st_mtime_ns", None),
        int(before_stat.st_size),
    )
    identity = (
        getattr(file_stat, "st_dev", None),
        getattr(file_stat, "st_ino", None),
        getattr(file_stat, "st_mtime_ns", None),
        int(file_stat.st_size),
    )
    return (
        identity_before == identity
        and identity == evidence.file_identity
        and len(data) == evidence.file_size_bytes
        and hashlib.sha256(data).hexdigest() == evidence.file_sha256
    )


__all__ = [
    "VerifiedMorphOutputError",
    "VerifiedVmdEvidence",
    "validate_verified_morph_readback",
    "verify_evidence_unchanged",
    "write_verified_morph_vmd",
]
