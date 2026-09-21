from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from src.core.effective_shape_plan import (
    BasePlanIdentity,
    BaseTimingPlanInput,
    build_base_plan_identity,
)
from src.core.event_adjustment_history import AdjustmentHistoryState
from src.core.output_diagnostics import DiagnosticFailureInput
from src.core.output_edit_state import GenerationState
from src.core.model_profile_state import ModelProfileState
from src.core.event_adjustment_history import OutputEditHistoryState


ROLLBACK_FORBIDDEN_FAILURE_CLASSES = frozenset(
    {
        "model_unavailable",
        "integrity_mismatch",
        "load_failure",
        "memory_failure",
        "transcribe_failure",
    }
)


def is_rollback_forbidden_failure_class(failure_class: str | None) -> bool:
    return failure_class in ROLLBACK_FORBIDDEN_FAILURE_CLASSES


@dataclass(frozen=True)
class AnalysisParameterSnapshot:
    morph_upper_limit: float

    def __post_init__(self) -> None:
        upper_limit = self.morph_upper_limit
        if (
            isinstance(upper_limit, bool)
            or not isinstance(upper_limit, (int, float))
            or not math.isfinite(float(upper_limit))
            or float(upper_limit) < 0.0
        ):
            raise ValueError("morph_upper_limit must be finite and >= 0")
        object.__setattr__(self, "morph_upper_limit", float(upper_limit))


@dataclass(frozen=True)
class AnalysisRollbackSnapshot:
    job_id: int
    timing_plan: Any
    base_plan_identity: BasePlanIdentity
    adjustment_history_state: AdjustmentHistoryState | None
    selected_source_event_index: int | None
    selected_base_plan_identity_digest: str | None
    prior_diagnostic_failure: DiagnosticFailureInput | None
    parameters: AnalysisParameterSnapshot
    output_edit_history_state: OutputEditHistoryState | None = None
    generation_state: GenerationState | None = None
    model_profile_state: ModelProfileState | None = None
    model_key: str | None = None
    manifest_identity: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.job_id, bool) or not isinstance(self.job_id, int):
            raise ValueError("job_id must be an integer")
        if self.job_id < 0:
            raise ValueError("job_id must be >= 0")
        if self.timing_plan is None:
            raise ValueError("timing_plan is required")
        if not isinstance(self.base_plan_identity, BasePlanIdentity):
            raise ValueError("base_plan_identity is invalid")
        if self.adjustment_history_state is not None:
            if (
                self.adjustment_history_state.current_snapshot.base_plan_identity
                != self.base_plan_identity
            ):
                raise ValueError("adjustment history base identity mismatch")
            if self.adjustment_history_state.has_pending_change:
                raise ValueError("pending adjustment history cannot be captured")
        if self.output_edit_history_state is not None:
            if (
                self.output_edit_history_state.current_state.base_plan_identity
                != self.base_plan_identity
            ):
                raise ValueError("output edit history base identity mismatch")
            if self.output_edit_history_state.has_pending_change:
                raise ValueError("pending output history cannot be captured")
        if self.generation_state is not None and not isinstance(
            self.generation_state,
            GenerationState,
        ):
            raise ValueError("generation state is invalid")
        if self.model_profile_state is not None and not isinstance(
            self.model_profile_state,
            ModelProfileState,
        ):
            raise ValueError("model profile state is invalid")
        index = self.selected_source_event_index
        digest = self.selected_base_plan_identity_digest
        if index is None:
            if digest is not None:
                raise ValueError("selection digest requires an event index")
        else:
            if isinstance(index, bool) or not isinstance(index, int) or index < 0:
                raise ValueError("selected event index is invalid")
            if digest != self.base_plan_identity.digest:
                raise ValueError("selection base identity mismatch")
        if (
            self.prior_diagnostic_failure is not None
            and not isinstance(
                self.prior_diagnostic_failure,
                DiagnosticFailureInput,
            )
        ):
            raise ValueError("prior diagnostic failure is invalid")
        if not isinstance(self.parameters, AnalysisParameterSnapshot):
            raise ValueError("parameters are invalid")
        if (self.model_key is None) != (self.manifest_identity is None):
            raise ValueError("model identity must be complete")
        if self.model_key is not None and (
            not isinstance(self.model_key, str)
            or not self.model_key
            or not isinstance(self.manifest_identity, str)
            or not self.manifest_identity
        ):
            raise ValueError("model identity is invalid")


def can_restore_analysis_rollback(
    snapshot: AnalysisRollbackSnapshot | None,
    *,
    job_id: int,
    comparison_base_input: BaseTimingPlanInput | None,
    current_parameters: AnalysisParameterSnapshot | None,
    current_model_profile_state: ModelProfileState | None = None,
    current_model_key: str | None = None,
    current_manifest_identity: str | None = None,
) -> bool:
    if (
        snapshot is None
        or isinstance(job_id, bool)
        or not isinstance(job_id, int)
        or job_id != snapshot.job_id
        or comparison_base_input is None
        or current_parameters is None
        or current_parameters != snapshot.parameters
    ):
        return False
    if snapshot.model_profile_state != current_model_profile_state:
        return False
    if (
        snapshot.model_key != current_model_key
        or snapshot.manifest_identity != current_manifest_identity
    ):
        return False
    try:
        return (
            build_base_plan_identity(comparison_base_input)
            == snapshot.base_plan_identity
        )
    except (TypeError, ValueError):
        return False
