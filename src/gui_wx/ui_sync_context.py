from __future__ import annotations

from dataclasses import dataclass

from src.core.effective_shape_plan import (
    BasePlanIdentity,
    BaseTimingPlanInput,
    EffectiveShapePlan,
    build_base_plan_identity,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import (
    AdjustmentLayerSnapshot,
    AdjustmentContractError,
    empty_adjustment_snapshot,
)
from src.core.effective_shape_diagnostics import ResolverDiagnosticsCollector


@dataclass(frozen=True)
class UiSyncContext:
    base_input: BaseTimingPlanInput
    base_plan_identity: BasePlanIdentity
    effective_plan: EffectiveShapePlan


def build_ui_sync_context(
    base_input: BaseTimingPlanInput,
    adjustment_snapshot: AdjustmentLayerSnapshot | None,
    *,
    effective_plan_hint: EffectiveShapePlan | None = None,
    diagnostics: ResolverDiagnosticsCollector | None = None,
    resolver_diagnostics: ResolverDiagnosticsCollector | None = None,
) -> UiSyncContext:
    if diagnostics is None:
        diagnostics = resolver_diagnostics
    if not isinstance(base_input, BaseTimingPlanInput):
        raise TypeError("base_input must be BaseTimingPlanInput")

    if effective_plan_hint is None:
        try:
            effective_plan = resolve_effective_shape_plan(
                base_input,
                adjustment_snapshot,
                diagnostics=diagnostics,
            )
        except AdjustmentContractError as error:
            if error.safe_code is None:
                error.safe_code = "adjustment_contract_invalid"
            if error.safe_field_code is None:
                error.safe_field_code = "unknown"
            raise
        return UiSyncContext(
            base_input=base_input,
            base_plan_identity=effective_plan.base_plan_identity,
            effective_plan=effective_plan,
        )

    identity = build_base_plan_identity(base_input)
    if effective_plan_hint.base_plan_identity != identity:
        raise AdjustmentContractError(
            "effective plan hint base identity mismatch",
            safe_code="identity_mismatch",
            safe_field_code="base_plan_identity",
            safe_phase="base_identity",
            safe_pass_kind="identity_validation",
        )
    candidate_adjustment = (
        empty_adjustment_snapshot(identity)
        if adjustment_snapshot is None
        else adjustment_snapshot
    )
    if effective_plan_hint.canonical_adjustment_snapshot != candidate_adjustment:
        raise AdjustmentContractError(
            "effective plan hint adjustment snapshot mismatch",
            safe_code="adjustment_snapshot_mismatch",
            safe_field_code="adjustment_snapshot_identity",
            safe_phase="snapshot_canonicalize",
            safe_pass_kind="identity_validation",
        )
    if effective_plan_hint.shape_parameters != base_input.shape_parameters:
        raise AdjustmentContractError(
            "effective plan hint shape parameters mismatch",
            safe_code="shape_parameters_mismatch",
            safe_field_code="shape_parameters",
            safe_phase="shape_parameters",
            safe_pass_kind="identity_validation",
        )
    return UiSyncContext(
        base_input=base_input,
        base_plan_identity=identity,
        effective_plan=effective_plan_hint,
    )
