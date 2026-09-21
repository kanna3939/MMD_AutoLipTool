from __future__ import annotations

from src.core.effective_shape_plan import BasePlanIdentity
from src.core.event_adjustment import ADJUSTMENT_SNAPSHOT_SCHEMA, AdjustmentLayerSnapshot
from src.core.event_adjustment_history import (
    commit_output_edit_state,
    initialize_output_edit_history,
    normalize_profile_aware_output_edit_history_state,
    redo_output_edit_state,
    undo_output_edit_state,
)
from src.core.generation_presets import GenerationSettings
from src.core.model_profile_state import ModelProfileResolutionStatus, ModelProfileState
from src.core.output_edit_state import GenerationState, OutputEditState


def _output(
    *,
    adjustment_value: float | None = None,
    preset_id: str | None = None,
) -> OutputEditState:
    identity = BasePlanIdentity("test-v1", ("base",), "base")
    adjustments = ()
    if adjustment_value is not None:
        from src.core.event_adjustment import EventAdjustment

        adjustments = (EventAdjustment(0, peak_value=adjustment_value),)
    return OutputEditState(
        identity,
        AdjustmentLayerSnapshot(ADJUSTMENT_SNAPSHOT_SCHEMA, identity, adjustments),
        GenerationState(GenerationSettings(), preset_id),
    )


def _profile_state(profile_id: str | None, baseline_id: str | None):
    return ModelProfileState(
        active_model_profile_id=profile_id,
        active_profile_baseline_preset_id=baseline_id,
        resolution_status=(
            ModelProfileResolutionStatus.RESOLVED
            if profile_id is not None
            else ModelProfileResolutionStatus.NO_PROFILE
        ),
    )


def test_profile_identity_only_transaction_is_atomic_through_undo_redo() -> None:
    output = _output()
    no_profile = _profile_state(None, None)
    active_profile = _profile_state("profile", "baseline")
    state = initialize_output_edit_history(output, model_profile_state=no_profile)

    state = commit_output_edit_state(
        state,
        output,
        model_profile_state=active_profile,
    )
    assert len(state.undo_transactions) == 1
    assert state.current_state == output
    assert state.current_model_profile_state == active_profile

    undone = undo_output_edit_state(state)
    assert undone.current_state == output
    assert undone.current_model_profile_state == no_profile
    redone = redo_output_edit_state(undone)
    assert redone.current_model_profile_state == active_profile


def test_event_only_transaction_keeps_active_profile_context() -> None:
    initial = _output()
    edited = _output(adjustment_value=0.6)
    active_profile = _profile_state("profile", "baseline")
    state = initialize_output_edit_history(
        initial,
        model_profile_state=active_profile,
    )
    state = commit_output_edit_state(
        state,
        edited,
        model_profile_state=active_profile,
    )

    undone = undo_output_edit_state(state)
    assert undone.current_model_profile_state == active_profile
    assert redo_output_edit_state(undone).current_model_profile_state == active_profile


def test_profile_aware_normalization_compacts_unresolvable_history() -> None:
    initial = _output()
    deleted_endpoint = _output(preset_id="deleted")
    current_endpoint = _output(adjustment_value=0.8)
    state = initialize_output_edit_history(initial, model_profile_state=_profile_state(None, None))
    state = commit_output_edit_state(
        state,
        deleted_endpoint,
        model_profile_state=_profile_state(None, None),
    )
    state = commit_output_edit_state(
        state,
        current_endpoint,
        model_profile_state=_profile_state(None, None),
    )

    normalized = normalize_profile_aware_output_edit_history_state(
        state,
        lambda output_state, profile_state: (
            None
            if output_state.generation_state.active_preset_id == "deleted"
            else (output_state, profile_state)
        ),
    )

    assert normalized.current_state == current_endpoint
    assert normalized.undo_transactions == ()
    assert normalized.redo_transactions == ()
