"""UI-independent numeric and wire comparisons for the MS30 shadow tool."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence


class ShadowComparisonError(ValueError):
    """Raised when shadow evidence cannot be compared without guessing."""


@dataclass(frozen=True, slots=True)
class CurveComparison:
    status: str
    sample_count: int
    compared_count: int
    not_evaluable_count: int
    max_abs_diff: float | None
    differences: tuple[tuple[float, float, float, float], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "sample_count": self.sample_count,
            "compared_count": self.compared_count,
            "not_evaluable_count": self.not_evaluable_count,
            "max_abs_diff": self.max_abs_diff,
            "differences": [
                {
                    "frame": frame,
                    "left": left,
                    "right": right,
                    "abs_diff": delta,
                }
                for frame, left, right, delta in self.differences
            ],
        }


@dataclass(frozen=True, slots=True)
class WireReadbackPoint:
    frame_no: int
    morph_name: str
    value: float
    value_bytes: bytes

    @property
    def value_hex(self) -> str:
        return self.value_bytes.hex()


@dataclass(frozen=True, slots=True)
class ShadowCaseResult:
    case_id: str
    input_mode: str
    evidence_id: str
    snapshot_identity: Mapping[str, object] | None
    input_hashes: Mapping[str, Mapping[str, object]]
    validation_scope: str
    scope_results: Mapping[str, str]
    candidate_state: str | None
    expected_candidate_state: str | None
    expected_issue_reasons: tuple[str, ...]
    case_verdict: str
    raw_to_baseline: Mapping[str, object]
    baseline_to_canonical: Mapping[str, object]
    canonical_to_wire: Mapping[str, object]
    preview_difference: Mapping[str, object]
    issues: tuple[str, ...]
    execution_state: str

    def __post_init__(self) -> None:
        for field_name in (
            "snapshot_identity",
            "input_hashes",
            "scope_results",
            "raw_to_baseline",
            "baseline_to_canonical",
            "canonical_to_wire",
            "preview_difference",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _freeze_json(value))
        object.__setattr__(self, "expected_issue_reasons", tuple(self.expected_issue_reasons))
        object.__setattr__(self, "issues", tuple(self.issues))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_id": "final-morph-shadow/v1",
            "case_id": self.case_id,
            "input_mode": self.input_mode,
            "evidence_id": self.evidence_id,
            "snapshot_identity": _thaw_json(self.snapshot_identity),
            "input_hashes": _thaw_json(self.input_hashes),
            "validation_scope": self.validation_scope,
            "scope_results": _thaw_json(self.scope_results),
            "candidate_state": self.candidate_state,
            "expected_candidate_state": self.expected_candidate_state,
            "expected_issue_reasons": list(self.expected_issue_reasons),
            "case_verdict": self.case_verdict,
            "raw_to_baseline": _thaw_json(self.raw_to_baseline),
            "baseline_to_canonical": _thaw_json(self.baseline_to_canonical),
            "canonical_to_wire": _thaw_json(self.canonical_to_wire),
            "preview_difference": _thaw_json(self.preview_difference),
            "issues": list(self.issues),
            "execution_state": self.execution_state,
        }


def _freeze_json(value: object) -> object:
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise TypeError("shadow result object keys must be strings")
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise TypeError(f"shadow result contains a non-JSON value: {type(value).__name__}")


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def compare_curves(
    left_points: Iterable[tuple[int | float, int | float]],
    right_points: Iterable[tuple[int | float, int | float]],
    *,
    tolerance: float = 0.0,
) -> CurveComparison:
    """Compare piecewise-linear curves on their key union and sampled intervals.

    Values are evaluated only inside each curve's own key domain. No implicit
    zero curve or endpoint extension is introduced.
    """
    left = _validated_curve(left_points, field_name="left_points")
    right = _validated_curve(right_points, field_name="right_points")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ShadowComparisonError("tolerance must be finite and non-negative")
    if not left or not right:
        return CurveComparison(
            status="not_evaluated",
            sample_count=0,
            compared_count=0,
            not_evaluable_count=0,
            max_abs_diff=None,
            differences=(),
        )

    union_keys = sorted({frame for frame, _ in (*left, *right)})
    sample_frames: set[float] = {float(frame) for frame in union_keys}
    for curve in (left, right):
        for (start, _), (end, _) in zip(curve, curve[1:]):
            sample_frames.update(float(frame) for frame in range(start + 1, end))
    sample_frames.update(
        (float(start) + float(end)) / 2.0
        for start, end in zip(union_keys, union_keys[1:])
    )

    compared = 0
    not_evaluable = 0
    differences: list[tuple[float, float, float, float]] = []
    max_abs_diff = 0.0
    for frame in sorted(sample_frames):
        left_value = _curve_value_at(left, frame)
        right_value = _curve_value_at(right, frame)
        if left_value is None or right_value is None:
            not_evaluable += 1
            continue
        compared += 1
        delta = abs(left_value - right_value)
        if not math.isfinite(delta):
            raise ShadowComparisonError("curve difference is not finite")
        max_abs_diff = max(max_abs_diff, delta)
        if delta > tolerance:
            differences.append((frame, left_value, right_value, delta))

    return CurveComparison(
        status=("fail" if differences else "not_evaluated" if compared == 0 else "pass"),
        sample_count=len(sample_frames),
        compared_count=compared,
        not_evaluable_count=not_evaluable,
        max_abs_diff=max_abs_diff if compared else None,
        differences=tuple(differences),
    )


def compare_keyed_values(
    left_points: Iterable[tuple[int, str, int | float]],
    right_points: Iterable[tuple[int, str, int | float]],
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    """Compare key sets and values without restricting to common keys."""
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ShadowComparisonError("tolerance must be finite and non-negative")
    left = _validated_keyed_points(left_points, field_name="left_points")
    right = _validated_keyed_points(right_points, field_name="right_points")
    left_by_key = {(frame, morph): value for frame, morph, value in left}
    right_by_key = {(frame, morph): value for frame, morph, value in right}
    keys = sorted(set(left_by_key) | set(right_by_key), key=lambda item: (item[0], item[1]))
    missing_left = [key for key in keys if key not in left_by_key]
    missing_right = [key for key in keys if key not in right_by_key]
    changed: list[dict[str, object]] = []
    for frame, morph in keys:
        if (frame, morph) not in left_by_key or (frame, morph) not in right_by_key:
            continue
        delta = abs(left_by_key[(frame, morph)] - right_by_key[(frame, morph)])
        if not math.isfinite(delta):
            raise ShadowComparisonError("keyed value difference is not finite")
        if delta > tolerance:
            changed.append(
                {
                    "frame_no": frame,
                    "semantic_morph": morph,
                    "left": left_by_key[(frame, morph)],
                    "right": right_by_key[(frame, morph)],
                    "abs_diff": delta,
                }
            )
    return {
        "key_union_count": len(keys),
        "missing_from_left": [
            {"frame_no": frame, "semantic_morph": morph} for frame, morph in missing_left
        ],
        "missing_from_right": [
            {"frame_no": frame, "semantic_morph": morph} for frame, morph in missing_right
        ],
        "changed_values": changed,
        "equal": not missing_left and not missing_right and not changed,
    }


def read_morph_vmd(data: bytes) -> tuple[str, tuple[WireReadbackPoint, ...]]:
    """Read a minimal morph-only VMD independently of the production writer."""
    if type(data) is not bytes:
        raise ShadowComparisonError("VMD payload must be bytes")
    header = b"Vocaloid Motion Data 0002".ljust(30, b"\0")
    if len(data) < 74 or data[:30] != header:
        raise ShadowComparisonError("VMD header is invalid or truncated")
    model_field = data[30:50]
    model_bytes = model_field.split(b"\0", 1)[0]
    if b"\0" in model_field and any(model_field[model_field.index(b"\0") :]):
        raise ShadowComparisonError("VMD model field has non-zero padding after its terminator")
    try:
        model_name = model_bytes.decode("shift_jis")
    except UnicodeDecodeError as error:
        raise ShadowComparisonError("VMD model field is invalid Shift-JIS") from error
    if len(data) < 58:
        raise ShadowComparisonError("VMD prefix is truncated")
    bone_count = struct.unpack_from("<I", data, 50)[0]
    morph_count = struct.unpack_from("<I", data, 54)[0]
    if bone_count != 0:
        raise ShadowComparisonError("VMD contains bone frames outside the shadow contract")
    if morph_count > 1_000_000:
        raise ShadowComparisonError("VMD morph frame count exceeds the shadow limit")
    expected_size = 58 + (23 * morph_count) + 16
    if len(data) != expected_size:
        raise ShadowComparisonError("VMD size does not match its morph frame count")
    points: list[WireReadbackPoint] = []
    cursor = 58
    for index in range(morph_count):
        name_bytes = data[cursor : cursor + 15]
        frame_no = struct.unpack_from("<I", data, cursor + 15)[0]
        value_bytes = data[cursor + 19 : cursor + 23]
        name_payload = name_bytes.split(b"\0", 1)[0]
        if b"\0" in name_bytes and any(name_bytes[name_bytes.index(b"\0") :]):
            raise ShadowComparisonError(f"VMD morph name {index} has non-zero padding after its terminator")
        try:
            morph_name = name_payload.decode("shift_jis")
        except UnicodeDecodeError as error:
            raise ShadowComparisonError(f"VMD morph name {index} is invalid Shift-JIS") from error
        value = struct.unpack("<f", value_bytes)[0]
        if not morph_name or not math.isfinite(value) or value < 0.0:
            raise ShadowComparisonError(f"VMD morph record {index} is invalid")
        points.append(WireReadbackPoint(frame_no, morph_name, value, value_bytes))
        cursor += 23
    if any(struct.unpack_from("<I", data, cursor + offset)[0] != 0 for offset in (0, 4, 8, 12)):
        raise ShadowComparisonError("VMD contains non-morph frames outside the shadow contract")
    return model_name, tuple(points)


def compare_wire_readback(
    expected: Sequence[tuple[int, str, bytes]],
    actual: Sequence[WireReadbackPoint],
) -> dict[str, object]:
    """Compare VMD frame/name/value bytes in their serialized order."""
    expected_rows = tuple(expected)
    actual_rows = tuple(actual)
    mismatches: list[dict[str, object]] = []
    limit = max(len(expected_rows), len(actual_rows))
    for index in range(limit):
        expected_row = expected_rows[index] if index < len(expected_rows) else None
        actual_row = actual_rows[index] if index < len(actual_rows) else None
        if expected_row is not None and actual_row is not None:
            frame, name, value_bytes = expected_row
            if (frame, name, value_bytes) == (actual_row.frame_no, actual_row.morph_name, actual_row.value_bytes):
                continue
        mismatches.append(
            {
                "index": index,
                "expected": None
                if expected_row is None
                else {
                    "frame_no": expected_row[0],
                    "morph_name": expected_row[1],
                    "value_hex": expected_row[2].hex(),
                },
                "actual": None
                if actual_row is None
                else {
                    "frame_no": actual_row.frame_no,
                    "morph_name": actual_row.morph_name,
                    "value_hex": actual_row.value_hex,
                },
            }
        )
    return {
        "expected_count": len(expected_rows),
        "actual_count": len(actual_rows),
        "mismatches": mismatches,
        "equal": not mismatches,
    }


def _validated_curve(
    points: Iterable[tuple[int | float, int | float]], *, field_name: str
) -> tuple[tuple[int, float], ...]:
    try:
        rows = tuple(points)
    except TypeError as error:
        raise ShadowComparisonError(f"{field_name} must be iterable") from error
    parsed: list[tuple[int, float]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, (tuple, list)) or len(row) != 2:
            raise ShadowComparisonError(f"{field_name}[{index}] is malformed")
        frame, value = row
        if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
            raise ShadowComparisonError(f"{field_name}[{index}] has an invalid frame")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ShadowComparisonError(f"{field_name}[{index}] has an invalid value")
        scalar = float(value)
        if not math.isfinite(scalar):
            raise ShadowComparisonError(f"{field_name}[{index}] has a non-finite value")
        parsed.append((frame, scalar))
    if any(left[0] >= right[0] for left, right in zip(parsed, parsed[1:])):
        raise ShadowComparisonError(f"{field_name} frames must be unique and strictly increasing")
    return tuple(parsed)


def _validated_keyed_points(
    points: Iterable[tuple[int, str, int | float]], *, field_name: str
) -> tuple[tuple[int, str, float], ...]:
    try:
        rows = tuple(points)
    except TypeError as error:
        raise ShadowComparisonError(f"{field_name} must be iterable") from error
    parsed: list[tuple[int, str, float]] = []
    seen: set[tuple[int, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            raise ShadowComparisonError(f"{field_name}[{index}] is malformed")
        frame, morph, value = row
        if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
            raise ShadowComparisonError(f"{field_name}[{index}] has an invalid frame")
        if type(morph) is not str or not morph:
            raise ShadowComparisonError(f"{field_name}[{index}] has an invalid morph")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ShadowComparisonError(f"{field_name}[{index}] has an invalid value")
        scalar = float(value)
        if not math.isfinite(scalar):
            raise ShadowComparisonError(f"{field_name}[{index}] has a non-finite value")
        key = frame, morph
        if key in seen:
            raise ShadowComparisonError(f"{field_name} contains a duplicate key: {key!r}")
        seen.add(key)
        parsed.append((frame, morph, scalar))
    return tuple(parsed)


def _curve_value_at(curve: Sequence[tuple[int, float]], frame: float) -> float | None:
    if not curve or frame < curve[0][0] or frame > curve[-1][0]:
        return None
    for (left_frame, left_value), (right_frame, right_value) in zip(curve, curve[1:]):
        if left_frame <= frame <= right_frame:
            if left_frame == right_frame:
                return left_value
            ratio = (frame - left_frame) / (right_frame - left_frame)
            value = left_value + (right_value - left_value) * ratio
            if not math.isfinite(value):
                raise ShadowComparisonError("curve interpolation is not finite")
            return value
    if frame == curve[-1][0]:
        return curve[-1][1]
    if frame == curve[0][0]:
        return curve[0][1]
    return None


__all__ = [
    "CurveComparison",
    "ShadowCaseResult",
    "ShadowComparisonError",
    "WireReadbackPoint",
    "compare_curves",
    "compare_keyed_values",
    "compare_wire_readback",
    "read_morph_vmd",
]
