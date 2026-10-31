from __future__ import annotations

from dataclasses import dataclass
import math

from .effective_shape_plan import BasePlanIdentity
from .event_adjustment import AdjustmentContractError, AdjustmentLayerSnapshot
from .generation_presets import GenerationSettings
from .morph_name_sets import (
    JAPANESE_MORPH_NAME_SET_ID,
    get_builtin_morph_name_set,
)


def _require_generation_state(value: object, field_name: str) -> "GenerationState":
    if not isinstance(value, GenerationState):
        raise AdjustmentContractError(f"{field_name} must be a GenerationState")
    return value


def _require_identity(value: object, field_name: str) -> BasePlanIdentity:
    if not isinstance(value, BasePlanIdentity):
        raise AdjustmentContractError(f"{field_name} must be a BasePlanIdentity")
    return value


def _require_snapshot(value: object, field_name: str) -> AdjustmentLayerSnapshot:
    if not isinstance(value, AdjustmentLayerSnapshot):
        raise AdjustmentContractError(
            f"{field_name} must be an AdjustmentLayerSnapshot"
        )
    return value


def _validate_active_preset_id(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value:
        raise AdjustmentContractError(
            "active_preset_id must be None or a non-empty string"
        )
    return value


def _validate_morph_name_set_id(value: object) -> str:
    if type(value) is not str or not value:
        raise AdjustmentContractError(
            "resolved_morph_name_set_id must be a non-empty string"
        )
    try:
        get_builtin_morph_name_set(value)
    except (KeyError, ValueError) as exc:
        raise AdjustmentContractError(
            "resolved_morph_name_set_id must identify a built-in morph name set"
        ) from exc
    return value


@dataclass(frozen=True)
class GenerationState:
    """Immutable generation settings that remain valid without an analysis base."""

    generation_settings: GenerationSettings
    active_preset_id: str | None = None
    resolved_morph_name_set_id: str = JAPANESE_MORPH_NAME_SET_ID

    def __post_init__(self) -> None:
        if not isinstance(self.generation_settings, GenerationSettings):
            raise AdjustmentContractError(
                "generation_settings must be GenerationSettings"
            )
        object.__setattr__(
            self,
            "active_preset_id",
            _validate_active_preset_id(self.active_preset_id),
        )
        object.__setattr__(
            self,
            "resolved_morph_name_set_id",
            _validate_morph_name_set_id(self.resolved_morph_name_set_id),
        )


@dataclass(frozen=True)
class OutputEditState:
    """Atomic base-bound output state used by the output edit history."""

    base_plan_identity: BasePlanIdentity
    adjustment_snapshot: AdjustmentLayerSnapshot
    generation_state: GenerationState
    morph_upper_limit: float = 0.9

    def __post_init__(self) -> None:
        identity = _require_identity(self.base_plan_identity, "base_plan_identity")
        snapshot = _require_snapshot(
            self.adjustment_snapshot,
            "adjustment_snapshot",
        )
        if snapshot.base_plan_identity != identity:
            raise AdjustmentContractError(
                "output edit adjustment snapshot base identity mismatch"
            )
        _require_generation_state(self.generation_state, "generation_state")
        value = self.morph_upper_limit
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AdjustmentContractError(
                "morph_upper_limit must be a finite number between 0 and 10"
            )
        normalized = float(value)
        if not math.isfinite(normalized) or not 0.0 <= normalized <= 10.0:
            raise AdjustmentContractError(
                "morph_upper_limit must be a finite number between 0 and 10"
            )
        object.__setattr__(self, "morph_upper_limit", normalized)


def build_output_edit_state(
    base_plan_identity: BasePlanIdentity,
    adjustment_snapshot: AdjustmentLayerSnapshot,
    generation_state: GenerationState,
    morph_upper_limit: float = 0.9,
) -> OutputEditState:
    return OutputEditState(
        base_plan_identity=base_plan_identity,
        adjustment_snapshot=adjustment_snapshot,
        generation_state=generation_state,
        morph_upper_limit=morph_upper_limit,
    )


__all__ = [
    "GenerationState",
    "OutputEditState",
    "build_output_edit_state",
]
