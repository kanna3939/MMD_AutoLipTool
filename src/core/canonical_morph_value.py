"""Canonical, UI-independent morph values for the MS30 numeric contract."""

from __future__ import annotations

import sys

# Both supported package spellings must share the numeric DTO's class identity.
_module_alias = __name__[4:] if __name__.startswith("src.") else "src." + __name__
sys.modules.setdefault(_module_alias, sys.modules[__name__])

import json
import math
import re
import struct
from dataclasses import dataclass


POLICY_ID = "legacy-compatible-q10000/v1"
QUANTUM = 10_000
LEGACY_TOLERANCE = 1e-12

_DTO_FIELDS = frozenset(
    {
        "policy_id",
        "quantum",
        "units",
        "value_kind",
        "legacy_value_hex",
        "binary32_hex",
        "wire_underflow",
    }
)
_CANONICAL_UNITS_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_BINARY32_HEX_PATTERN = re.compile(r"[0-9a-f]{8}\Z")


class CanonicalMorphValueError(ValueError):
    """Raised when a morph value or its serialized representation is invalid."""


def _round_units_ties_to_even(value: float) -> int:
    numerator, denominator = value.as_integer_ratio()
    quotient, remainder = divmod(numerator * QUANTUM, denominator)
    doubled_remainder = remainder * 2
    if doubled_remainder > denominator or (
        doubled_remainder == denominator and quotient % 2 == 1
    ):
        quotient += 1
    return quotient


def _grid_scalar(units: int) -> float:
    try:
        scalar = units / QUANTUM
    except OverflowError as error:
        raise CanonicalMorphValueError("units do not produce a finite scalar") from error
    if not math.isfinite(scalar) or scalar < 0.0:
        raise CanonicalMorphValueError("units do not produce a finite non-negative scalar")
    if _round_units_ties_to_even(scalar) != units:
        raise CanonicalMorphValueError("units are inconsistent with their grid scalar")
    return scalar


def _binary32_projection(scalar: float) -> tuple[str, bool]:
    try:
        packed = struct.pack("<f", scalar)
    except (OverflowError, struct.error) as error:
        raise CanonicalMorphValueError("scalar is not representable as finite binary32") from error
    readback = struct.unpack("<f", packed)[0]
    if not math.isfinite(readback):
        raise CanonicalMorphValueError("scalar is not representable as finite binary32")
    return packed.hex(), scalar > 0.0 and readback == 0.0


def _parse_legacy_value_hex(value: object) -> float:
    if type(value) is not str:
        raise CanonicalMorphValueError("legacy_value_hex must be a canonical float.hex string")
    try:
        scalar = float.fromhex(value)
    except (OverflowError, ValueError) as error:
        raise CanonicalMorphValueError("legacy_value_hex must be a canonical float.hex string") from error
    if (
        not math.isfinite(scalar)
        or scalar < 0.0
        or (scalar == 0.0 and value.startswith("-"))
        or scalar.hex() != value
    ):
        raise CanonicalMorphValueError("legacy_value_hex must be a canonical non-negative float.hex string")
    return scalar


@dataclass(frozen=True, slots=True)
class CanonicalMorphValue:
    """Immutable numeric DTO with a recoverable scalar and binary32 projection."""

    policy_id: str
    quantum: int
    units: int
    value_kind: str
    legacy_value_hex: str | None
    binary32_hex: str
    wire_underflow: bool

    def __post_init__(self) -> None:
        if type(self.policy_id) is not str or self.policy_id != POLICY_ID:
            raise CanonicalMorphValueError("policy_id is unsupported")
        if isinstance(self.quantum, bool) or not isinstance(self.quantum, int):
            raise CanonicalMorphValueError("quantum must be an integer")
        if self.quantum != QUANTUM:
            raise CanonicalMorphValueError("quantum does not match the policy")
        if isinstance(self.units, bool) or not isinstance(self.units, int):
            raise CanonicalMorphValueError("units must be an integer")
        if self.units < 0:
            raise CanonicalMorphValueError("units must be non-negative")
        if type(self.value_kind) is not str or self.value_kind not in {
            "quantized",
            "legacy_preserved",
        }:
            raise CanonicalMorphValueError("value_kind is unsupported")
        if type(self.wire_underflow) is not bool:
            raise CanonicalMorphValueError("wire_underflow must be a bool")

        grid = _grid_scalar(self.units)
        if self.value_kind == "quantized":
            if self.legacy_value_hex is not None:
                raise CanonicalMorphValueError(
                    "quantized values must not include legacy_value_hex"
                )
            scalar = grid
        else:
            scalar = _parse_legacy_value_hex(self.legacy_value_hex)
            if _round_units_ties_to_even(scalar) != self.units:
                raise CanonicalMorphValueError(
                    "legacy_value_hex does not match units"
                )
            difference = abs(scalar - grid)
            if scalar == grid or difference > LEGACY_TOLERANCE:
                raise CanonicalMorphValueError(
                    "legacy_value_hex does not satisfy the compatibility exception"
                )

        expected_binary32_hex, expected_underflow = _binary32_projection(scalar)
        if (
            type(self.binary32_hex) is not str
            or _BINARY32_HEX_PATTERN.fullmatch(self.binary32_hex) is None
            or self.binary32_hex != expected_binary32_hex
        ):
            raise CanonicalMorphValueError("binary32_hex does not match the scalar")
        if self.wire_underflow is not expected_underflow:
            raise CanonicalMorphValueError("wire_underflow does not match the scalar")

    @property
    def scalar(self) -> float:
        """Return the canonical scalar, preserving its original binary64 when required."""
        if self.value_kind == "legacy_preserved":
            return float.fromhex(self.legacy_value_hex)  # type: ignore[arg-type]
        return _grid_scalar(self.units)

    @property
    def binary32_bytes(self) -> bytes:
        """Return the validated little-endian binary32 bytes."""
        return bytes.fromhex(self.binary32_hex)

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "quantum": self.quantum,
            "units": str(self.units),
            "value_kind": self.value_kind,
            "legacy_value_hex": self.legacy_value_hex,
            "binary32_hex": self.binary32_hex,
            "wire_underflow": self.wire_underflow,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_dict(cls, value: object) -> "CanonicalMorphValue":
        if type(value) is not dict or frozenset(value) != _DTO_FIELDS:
            raise CanonicalMorphValueError("canonical morph value has an invalid field set")
        raw_units = value["units"]
        if (
            type(raw_units) is not str
            or _CANONICAL_UNITS_PATTERN.fullmatch(raw_units) is None
        ):
            raise CanonicalMorphValueError("units must be a canonical decimal string")
        try:
            units = int(raw_units)
        except ValueError as error:
            raise CanonicalMorphValueError("units are outside the supported integer range") from error
        return cls(
            policy_id=value["policy_id"],
            quantum=value["quantum"],
            units=units,
            value_kind=value["value_kind"],
            legacy_value_hex=value["legacy_value_hex"],
            binary32_hex=value["binary32_hex"],
            wire_underflow=value["wire_underflow"],
        )

    @classmethod
    def from_json(cls, value: object) -> "CanonicalMorphValue":
        if type(value) is not str:
            raise CanonicalMorphValueError("serialized canonical morph value must be text")

        def reject_constant(constant: str) -> None:
            raise CanonicalMorphValueError(f"invalid JSON numeric constant: {constant}")

        try:
            data = json.loads(value, parse_constant=reject_constant)
        except (TypeError, ValueError) as error:
            raise CanonicalMorphValueError("serialized canonical morph value is invalid JSON") from error
        dto = cls.from_dict(data)
        if dto.to_json() != value:
            raise CanonicalMorphValueError("serialized canonical morph value is not canonical JSON")
        return dto


def canonicalize_morph_value(value: object) -> CanonicalMorphValue:
    """Validate, quantize, and project one finite non-negative numeric input."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CanonicalMorphValueError("value must be a non-bool int or float")
    try:
        scalar = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise CanonicalMorphValueError("value cannot be converted to binary64") from error
    if not math.isfinite(scalar):
        raise CanonicalMorphValueError("value must be finite")
    if scalar < 0.0:
        raise CanonicalMorphValueError("value must be non-negative")
    if scalar == 0.0:
        scalar = 0.0

    units = _round_units_ties_to_even(scalar)
    grid = _grid_scalar(units)
    if scalar != grid and abs(scalar - grid) <= LEGACY_TOLERANCE:
        value_kind = "legacy_preserved"
        legacy_value_hex = scalar.hex()
        effective_scalar = scalar
    else:
        value_kind = "quantized"
        legacy_value_hex = None
        effective_scalar = grid

    binary32_hex, wire_underflow = _binary32_projection(effective_scalar)
    return CanonicalMorphValue(
        policy_id=POLICY_ID,
        quantum=QUANTUM,
        units=units,
        value_kind=value_kind,
        legacy_value_hex=legacy_value_hex,
        binary32_hex=binary32_hex,
        wire_underflow=wire_underflow,
    )
