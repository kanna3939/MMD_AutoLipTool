from __future__ import annotations

from dataclasses import dataclass

import pytest

from gui_wx.analysis_rollback import (
    AnalysisParameterSnapshot,
    AnalysisRollbackSnapshot,
    can_restore_analysis_rollback,
)
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    build_base_plan_identity,
)
from src.core.event_adjustment import empty_adjustment_snapshot
from src.core.event_adjustment_history import initialize_adjustment_history
from src.core.output_diagnostics import DiagnosticFailureInput


@dataclass(frozen=True)
class Point:
    time_sec: float
    vowel: str = "あ"
    value: float = 0.5
    duration_sec: float = 0.2


def make_base_input(*, hold: int = 2, softness: int = 1):
    return BaseTimingPlanInput(
        timeline=(Point(0.5),),
        observations=None,
        source_duration_frames=90,
        shape_parameters=ShapeParameters(hold, softness),
    )


def make_parameters(*, upper_limit: float = 0.75):
    return AnalysisParameterSnapshot(morph_upper_limit=upper_limit)


def make_snapshot():
    base_input = make_base_input()
    identity = build_base_plan_identity(base_input)
    adjustment = empty_adjustment_snapshot(identity)
    failure = DiagnosticFailureInput(
        code="analysis_failed",
        source_severity="error",
        phase="analysis",
        recoverability="retry_possible",
    )
    return AnalysisRollbackSnapshot(
        job_id=7,
        timing_plan=object(),
        base_plan_identity=identity,
        adjustment_history_state=initialize_adjustment_history(adjustment),
        selected_source_event_index=0,
        selected_base_plan_identity_digest=identity.digest,
        prior_diagnostic_failure=failure,
        parameters=make_parameters(),
    )


def test_valid_snapshot_restores_only_for_current_job_and_parameters():
    snapshot = make_snapshot()

    assert can_restore_analysis_rollback(
        snapshot,
        job_id=7,
        comparison_base_input=make_base_input(),
        current_parameters=make_parameters(),
    )
    assert snapshot.prior_diagnostic_failure is not None
    assert not can_restore_analysis_rollback(
        snapshot,
        job_id=8,
        comparison_base_input=make_base_input(),
        current_parameters=make_parameters(),
    )
    assert not can_restore_analysis_rollback(
        snapshot,
        job_id=7,
        comparison_base_input=make_base_input(),
        current_parameters=make_parameters(upper_limit=0.8),
    )


def test_parameter_snapshot_rejects_nonfinite_and_out_of_range_values():
    with pytest.raises(ValueError, match="morph_upper_limit"):
        make_parameters(upper_limit=float("nan"))
    with pytest.raises(ValueError, match="morph_upper_limit"):
        AnalysisParameterSnapshot(-0.1)


def test_snapshot_rejects_pending_history_and_stale_selection():
    base_input = make_base_input()
    identity = build_base_plan_identity(base_input)
    history = initialize_adjustment_history(empty_adjustment_snapshot(identity))

    with pytest.raises(ValueError, match="selection base identity"):
        AnalysisRollbackSnapshot(
            job_id=7,
            timing_plan=object(),
            base_plan_identity=identity,
            adjustment_history_state=history,
            selected_source_event_index=0,
            selected_base_plan_identity_digest="stale",
            prior_diagnostic_failure=None,
            parameters=make_parameters(),
        )
