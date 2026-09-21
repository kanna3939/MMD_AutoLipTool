from __future__ import annotations

import pytest

from src.core.effective_shape_plan import BasePlanIdentity
from src.core.event_adjustment import (
    ADJUSTMENT_SNAPSHOT_SCHEMA,
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
    EventAdjustment,
)
from src.core.event_adjustment_history import (
    MAX_ADJUSTMENT_HISTORY_TRANSACTIONS,
    AdjustmentCoalescingKey,
    commit_output_edit_state,
    finish_current_output_edit_coalescing,
    initialize_output_edit_history,
    normalize_output_edit_history_state,
    redo_output_edit_state,
    undo_output_edit_state,
)
from src.core.generation_presets import GenerationSettings
from src.core.output_edit_state import GenerationState, OutputEditState


def identity(value: str = "base") -> BasePlanIdentity:
    return BasePlanIdentity("test-v1", (value,), value)


def snapshot(base: BasePlanIdentity, value: float | None = None) -> AdjustmentLayerSnapshot:
    adjustments = () if value is None else (EventAdjustment(0, peak_value=value),)
    return AdjustmentLayerSnapshot(ADJUSTMENT_SNAPSHOT_SCHEMA, base, adjustments)


def output(
    base: BasePlanIdentity,
    *,
    value: float | None = None,
    settings: GenerationSettings | None = None,
    preset_id: str | None = None,
) -> OutputEditState:
    return OutputEditState(
        base,
        snapshot(base, value),
        GenerationState(settings or GenerationSettings(), preset_id),
    )


def key(base: BasePlanIdentity, token: int = 1) -> AdjustmentCoalescingKey:
    return AdjustmentCoalescingKey(base.digest, 0, "peak_value", token)


def test_output_history_is_atomic_and_supports_redo_discard_and_limit() -> None:
    base = identity()
    initial = output(base)
    edited = output(base, value=0.6, settings=GenerationSettings(2, 3, "decay"), preset_id="preset")
    replacement = output(base, value=0.8)
    state = initialize_output_edit_history(initial)
    state = commit_output_edit_state(state, edited)
    state = undo_output_edit_state(state)
    assert state.current_state == initial
    assert state.can_redo
    state = commit_output_edit_state(state, replacement)
    assert state.redo_transactions == ()
    assert undo_output_edit_state(state).current_state == initial

    for index in range(MAX_ADJUSTMENT_HISTORY_TRANSACTIONS + 1):
        state = commit_output_edit_state(
            state,
            output(base, value=(index + 1) / 100.0),
        )
    assert len(state.undo_transactions) == MAX_ADJUSTMENT_HISTORY_TRANSACTIONS


def test_output_gesture_coalescing_keeps_generation_and_adjustment_atomic() -> None:
    base = identity()
    initial = output(base)
    first = output(base, settings=GenerationSettings(1, 0, "hold"))
    second = output(base, settings=GenerationSettings(2, 0, "hold"))
    state = initialize_output_edit_history(initial)
    state = commit_output_edit_state(state, first, coalesce_key=key(base))
    state = commit_output_edit_state(state, second, coalesce_key=key(base))
    assert state.pending_edit is not None
    state = finish_current_output_edit_coalescing(state)
    assert len(state.undo_transactions) == 1
    assert undo_output_edit_state(state).current_state == initial


def test_output_state_rejects_identity_mismatch_and_preserves_immutable_contract() -> None:
    base = identity()
    with pytest.raises(AdjustmentContractError):
        OutputEditState(identity("a"), snapshot(identity("b")), GenerationState(GenerationSettings()))
    state = GenerationState(GenerationSettings())
    with pytest.raises(AttributeError):
        state.active_preset_id = "changed"  # type: ignore[misc]


def test_deleted_preset_normalization_is_atomic_and_removes_effective_noop() -> None:
    base = identity()
    settings = GenerationSettings(2, 0, "decay")
    initial = output(base, settings=settings)
    preset = output(base, settings=settings, preset_id="deleted")
    state = commit_output_edit_state(initialize_output_edit_history(initial), preset)

    def normalize(generation_state: GenerationState) -> GenerationState:
        if generation_state.active_preset_id == "deleted":
            return GenerationState(generation_state.generation_settings, None)
        return generation_state

    normalized = normalize_output_edit_history_state(state, normalize)
    assert normalized.current_state == initial
    assert normalized.undo_transactions == ()
    assert normalized.redo_transactions == ()
