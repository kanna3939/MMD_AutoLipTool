from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


BASE_PLAN_IDENTITY_SCHEMA = "ms22-base-plan-v1"
ADJUSTMENT_SNAPSHOT_SCHEMA = "ms22-adjustment-snapshot-v2"
DEFAULT_SLOPE_RATIO = 0.7
LONG_VOWEL_MODE_HOLD = "hold"
LONG_VOWEL_MODE_DECAY = "decay"
SUPPORTED_LONG_VOWEL_MODES = (LONG_VOWEL_MODE_HOLD, LONG_VOWEL_MODE_DECAY)


class AdjustmentContractError(ValueError):
    """Raised when an MS21 adjustment contract is invalid or stale."""

    def __init__(
        self,
        message: str = "",
        *,
        safe_code: str | None = None,
        safe_field_code: str | None = None,
        event_index: int | None = None,
        source_event_index: int | None = None,
        safe_phase: str | None = None,
        safe_pass_kind: str | None = None,
        safe_details: dict[str, object] | None = None,
        event_role: str | None = None,
        source_event_role: str | None = None,
    ) -> None:
        super().__init__(message)
        self.safe_code = safe_code
        self.safe_field_code = safe_field_code
        self.event_index = event_index
        self.source_event_index = source_event_index
        self.safe_phase = safe_phase
        self.safe_pass_kind = safe_pass_kind
        self.safe_details = safe_details
        self.event_role = event_role
        self.source_event_role = source_event_role


def validate_long_vowel_mode(value: object) -> str:
    if type(value) is not str or value not in SUPPORTED_LONG_VOWEL_MODES:
        raise AdjustmentContractError(
            "long_vowel_mode must be exactly 'hold' or 'decay'",
            safe_code="long_vowel_mode_invalid",
            safe_field_code="long_vowel_mode",
            safe_phase="shape_parameters",
        )
    return value


def _freeze_payload(value: object) -> object:
    if isinstance(value, dict):
        return tuple(
            (str(key), _freeze_payload(item))
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_payload(item) for item in value)
    return value


def _require_index(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AdjustmentContractError(
            f"{field_name} must be a non-negative int",
            safe_code="adjustment_field_invalid",
            safe_field_code=field_name,
            safe_phase="snapshot_canonicalize",
        )
    return value


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdjustmentContractError(
            f"{field_name} must be an int",
            safe_code="adjustment_field_invalid",
            safe_field_code=field_name,
            safe_phase="snapshot_canonicalize",
        )
    return value


def _require_bounded_int(value: object, field_name: str) -> int:
    normalized = _require_int(value, field_name)
    if not 0 <= normalized <= 100:
        raise AdjustmentContractError(
            f"{field_name} must be between 0 and 100",
            safe_code="adjustment_field_invalid",
            safe_field_code=field_name,
            safe_phase="snapshot_canonicalize",
        )
    return normalized


def _require_finite_non_negative(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdjustmentContractError(
            f"{field_name} must be a finite number",
            safe_code="adjustment_field_invalid",
            safe_field_code=field_name,
            safe_phase="snapshot_canonicalize",
        )
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0.0:
        raise AdjustmentContractError(
            f"{field_name} must be finite and >= 0",
            safe_code="adjustment_field_invalid",
            safe_field_code=field_name,
            safe_phase="snapshot_canonicalize",
        )
    return normalized


@dataclass(frozen=True)
class BasePlanIdentity:
    schema_version: str
    canonical_payload: tuple[object, ...]
    digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str) or not self.schema_version:
            raise AdjustmentContractError("schema_version must be a non-empty string")
        if not isinstance(self.digest, str) or not self.digest:
            raise AdjustmentContractError("digest must be a non-empty string")
        object.__setattr__(
            self,
            "canonical_payload",
            tuple(_freeze_payload(item) for item in self.canonical_payload),
        )


@dataclass(frozen=True)
class EventAdjustment:
    base_event_index: int
    peak_value: float | None = None
    start_offset_frames: int = 0
    end_offset_frames: int = 0
    hold_frames: int | None = None
    softness_frames: int | None = None
    slope_ratio: float | None = None
    long_vowel_mode: str | None = None
    manual_overlap_limit_override: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "base_event_index",
            _require_index(self.base_event_index, "base_event_index"),
        )
        object.__setattr__(
            self,
            "start_offset_frames",
            _require_int(self.start_offset_frames, "start_offset_frames"),
        )
        object.__setattr__(
            self,
            "end_offset_frames",
            _require_int(self.end_offset_frames, "end_offset_frames"),
        )
        if self.peak_value is not None:
            object.__setattr__(
                self,
                "peak_value",
                _require_finite_non_negative(self.peak_value, "peak_value"),
            )
        if self.hold_frames is not None:
            object.__setattr__(
                self,
                "hold_frames",
                _require_bounded_int(self.hold_frames, "hold_frames"),
            )
        if self.softness_frames is not None:
            object.__setattr__(
                self,
                "softness_frames",
                _require_bounded_int(self.softness_frames, "softness_frames"),
            )
        if self.slope_ratio is not None:
            slope_ratio = _require_finite_non_negative(self.slope_ratio, "slope_ratio")
            if slope_ratio > 1.0:
                raise AdjustmentContractError(
                    "slope_ratio must be between 0.0 and 1.0",
                    safe_code="adjustment_field_invalid",
                    safe_field_code="slope_ratio",
                    safe_phase="snapshot_canonicalize",
                )
            object.__setattr__(self, "slope_ratio", slope_ratio)
        if self.long_vowel_mode is not None:
            object.__setattr__(self, "long_vowel_mode", validate_long_vowel_mode(self.long_vowel_mode))
        if type(self.manual_overlap_limit_override) is not bool:
            raise AdjustmentContractError(
                "manual_overlap_limit_override must be bool",
                safe_code="adjustment_field_invalid",
                safe_field_code="manual_overlap_limit_override",
                safe_phase="snapshot_canonicalize",
            )

    @property
    def is_empty(self) -> bool:
        return (
            self.peak_value is None
            and self.start_offset_frames == 0
            and self.end_offset_frames == 0
            and self.hold_frames is None
            and self.softness_frames is None
            and self.slope_ratio is None
            and self.long_vowel_mode is None
            and not self.manual_overlap_limit_override
        )

    @property
    def has_shape_adjustment(self) -> bool:
        """Whether this entry changes a requested shape value."""
        return (
            self.peak_value is not None
            or self.start_offset_frames != 0
            or self.end_offset_frames != 0
            or self.hold_frames is not None
            or self.softness_frames is not None
            or self.slope_ratio is not None
            or self.long_vowel_mode is not None
        )


@dataclass(frozen=True)
class AdjustmentLayerSnapshot:
    schema_version: str
    base_plan_identity: BasePlanIdentity
    adjustments: tuple[EventAdjustment, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != ADJUSTMENT_SNAPSHOT_SCHEMA:
            raise AdjustmentContractError(
                f"unsupported adjustment snapshot schema: {self.schema_version}",
                safe_code="snapshot_schema_invalid",
                safe_field_code="adjustment_schema",
                safe_phase="snapshot_canonicalize",
            )
        if not isinstance(self.base_plan_identity, BasePlanIdentity):
            raise AdjustmentContractError(
                "base_plan_identity is invalid",
                safe_code="identity_contract_invalid",
                safe_field_code="base_plan_identity",
                safe_phase="base_identity",
            )
        adjustments = tuple(self.adjustments)
        if any(not isinstance(item, EventAdjustment) for item in adjustments):
            raise AdjustmentContractError(
                "adjustments must contain EventAdjustment values",
                safe_code="adjustment_entry_type_invalid",
                safe_field_code="adjustments",
                safe_phase="snapshot_canonicalize",
            )
        object.__setattr__(self, "adjustments", adjustments)


def canonicalize_adjustment_snapshot(
    base_plan_identity: BasePlanIdentity,
    adjustments: Iterable[EventAdjustment],
    *,
    base_peak_values: tuple[float, ...],
    closing_hold_frames: int,
    closing_softness_frames: int,
) -> AdjustmentLayerSnapshot:
    """Validate, order and remove canonical no-op adjustment entries."""
    hold = _require_bounded_int(closing_hold_frames, "closing_hold_frames")
    softness = _require_bounded_int(closing_softness_frames, "closing_softness_frames")
    peak_values = tuple(
        _require_finite_non_negative(value, "base_peak_values")
        for value in base_peak_values
    )

    requested = tuple(adjustments)
    if any(not isinstance(item, EventAdjustment) for item in requested):
        raise AdjustmentContractError(
            "adjustments must contain EventAdjustment values",
            safe_code="adjustment_entry_type_invalid",
            safe_field_code="adjustments",
            safe_phase="snapshot_canonicalize",
        )

    seen: set[int] = set()
    canonical: list[EventAdjustment] = []
    for item in sorted(requested, key=lambda value: value.base_event_index):
        index = item.base_event_index
        if index in seen:
            raise AdjustmentContractError(
                f"duplicate adjustment index: {index}",
                safe_code="adjustment_duplicate_index",
                safe_field_code="base_event_index",
                safe_phase="snapshot_canonicalize",
                event_index=index,
            )
        seen.add(index)
        if index >= len(peak_values):
            raise AdjustmentContractError(
                f"stale adjustment index: {index}",
                safe_code="adjustment_index_out_of_range",
                safe_field_code="base_event_index",
                safe_phase="snapshot_canonicalize",
                event_index=index,
            )

        peak_value = item.peak_value
        if peak_value is not None and peak_value == peak_values[index]:
            peak_value = None
        hold_frames = item.hold_frames
        softness_frames = item.softness_frames
        slope_ratio = item.slope_ratio
        if slope_ratio == DEFAULT_SLOPE_RATIO:
            slope_ratio = None

        normalized = EventAdjustment(
            base_event_index=index,
            peak_value=peak_value,
            start_offset_frames=item.start_offset_frames,
            end_offset_frames=item.end_offset_frames,
            hold_frames=hold_frames,
            softness_frames=softness_frames,
            slope_ratio=slope_ratio,
            long_vowel_mode=item.long_vowel_mode,
            manual_overlap_limit_override=item.manual_overlap_limit_override,
        )
        if not normalized.is_empty:
            canonical.append(normalized)

    return AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=base_plan_identity,
        adjustments=tuple(canonical),
    )


def empty_adjustment_snapshot(
    base_plan_identity: BasePlanIdentity,
) -> AdjustmentLayerSnapshot:
    return AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=base_plan_identity,
        adjustments=(),
    )
