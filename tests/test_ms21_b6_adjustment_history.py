from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.event_adjustment import (
    ADJUSTMENT_SNAPSHOT_SCHEMA,
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
    BasePlanIdentity,
    EventAdjustment,
    empty_adjustment_snapshot,
)
from src.core.event_adjustment_history import (
    MAX_ADJUSTMENT_HISTORY_TRANSACTIONS,
    AdjustmentCoalescingKey,
    AdjustmentHistoryState,
    commit_adjustment_snapshot,
    finish_adjustment_coalescing,
    finish_current_adjustment_coalescing,
    initialize_adjustment_history,
    redo_adjustment_snapshot,
    undo_adjustment_snapshot,
)


def make_identity(digest: str = "base-a") -> BasePlanIdentity:
    return BasePlanIdentity(
        schema_version="test-base-v1",
        canonical_payload=(digest,),
        digest=digest,
    )


def make_snapshot(
    identity: BasePlanIdentity,
    value: float | None = None,
    *,
    event_index: int = 0,
) -> AdjustmentLayerSnapshot:
    adjustments = (
        ()
        if value is None
        else (
            EventAdjustment(
                base_event_index=event_index,
                peak_value=value,
            ),
        )
    )
    return AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=identity,
        adjustments=adjustments,
    )


def make_key(
    identity: BasePlanIdentity,
    *,
    event_index: int = 0,
    field: str = "peak_value",
    token: int = 1,
) -> AdjustmentCoalescingKey:
    return AdjustmentCoalescingKey(
        base_plan_identity_digest=identity.digest,
        base_event_index=event_index,
        field=field,
        gesture_token=token,
    )


def test_initialize_has_no_history() -> None:
    snapshot = empty_adjustment_snapshot(make_identity())
    state = initialize_adjustment_history(snapshot)

    assert state.current_snapshot == snapshot
    assert state.undo_transactions == ()
    assert state.redo_transactions == ()
    assert state.pending_edit is None
    assert state.can_undo is False
    assert state.can_redo is False


def test_discrete_commit_undo_redo_restores_full_snapshot() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    first = make_snapshot(identity, 0.5)
    second = AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=identity,
        adjustments=(
            EventAdjustment(base_event_index=0, peak_value=0.5),
            EventAdjustment(base_event_index=1, peak_value=0.8),
        ),
    )
    state = initialize_adjustment_history(initial)
    state = commit_adjustment_snapshot(state, first)
    state = commit_adjustment_snapshot(state, second)

    assert state.current_snapshot == second
    assert len(state.undo_transactions) == 2
    state = undo_adjustment_snapshot(state)
    assert state.current_snapshot == first
    assert state.can_redo is True
    state = undo_adjustment_snapshot(state)
    assert state.current_snapshot == initial
    state = redo_adjustment_snapshot(state)
    assert state.current_snapshot == first
    state = redo_adjustment_snapshot(state)
    assert state.current_snapshot == second


def test_new_discrete_commit_after_undo_clears_redo() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    first = make_snapshot(identity, 0.5)
    replacement = make_snapshot(identity, 0.7)
    state = commit_adjustment_snapshot(
        initialize_adjustment_history(initial),
        first,
    )
    state = undo_adjustment_snapshot(state)
    assert state.can_redo is True

    state = commit_adjustment_snapshot(state, replacement)

    assert state.current_snapshot == replacement
    assert state.redo_transactions == ()


def test_discrete_noop_preserves_redo() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    changed = make_snapshot(identity, 0.5)
    state = commit_adjustment_snapshot(
        initialize_adjustment_history(initial),
        changed,
    )
    state = undo_adjustment_snapshot(state)

    result = commit_adjustment_snapshot(state, initial)

    assert result == state
    assert result.can_redo is True


def test_same_gesture_coalesces_and_clears_redo_only_when_finished() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    first = make_snapshot(identity, 0.5)
    second = make_snapshot(identity, 0.7)
    key = make_key(identity)
    state = initialize_adjustment_history(initial)
    state = commit_adjustment_snapshot(state, first, coalesce_key=key)
    state = commit_adjustment_snapshot(state, second, coalesce_key=key)

    assert state.current_snapshot == second
    assert state.undo_transactions == ()
    assert state.pending_edit is not None

    state = finish_adjustment_coalescing(state, key)

    assert state.pending_edit is None
    assert len(state.undo_transactions) == 1
    assert undo_adjustment_snapshot(state).current_snapshot == initial


def test_gesture_returning_to_before_is_noop_and_preserves_redo() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    prior = make_snapshot(identity, 0.4)
    changed = make_snapshot(identity, 0.8)
    key = make_key(identity)
    state = commit_adjustment_snapshot(
        initialize_adjustment_history(initial),
        prior,
    )
    state = undo_adjustment_snapshot(state)
    assert state.can_redo is True
    state = commit_adjustment_snapshot(state, changed, coalesce_key=key)
    state = commit_adjustment_snapshot(state, initial, coalesce_key=key)

    state = finish_current_adjustment_coalescing(state)

    assert state.current_snapshot == initial
    assert state.undo_transactions == ()
    assert state.can_redo is True


def test_mismatched_boundary_does_not_change_any_state() -> None:
    identity = make_identity()
    key = make_key(identity)
    state = commit_adjustment_snapshot(
        initialize_adjustment_history(make_snapshot(identity)),
        make_snapshot(identity, 0.6),
        coalesce_key=key,
    )

    result = finish_adjustment_coalescing(
        state,
        replace(key, gesture_token=key.gesture_token + 1),
    )

    assert result == state


def test_different_gesture_key_finishes_previous_transaction() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    first = make_snapshot(identity, 0.5)
    second = make_snapshot(identity, 0.7)
    state = initialize_adjustment_history(initial)
    state = commit_adjustment_snapshot(
        state,
        first,
        coalesce_key=make_key(identity, token=1),
    )
    state = commit_adjustment_snapshot(
        state,
        second,
        coalesce_key=make_key(identity, token=2),
    )

    assert len(state.undo_transactions) == 1
    assert state.pending_edit is not None
    state = undo_adjustment_snapshot(state)
    assert state.current_snapshot == first


def test_history_discards_only_oldest_transaction_after_limit() -> None:
    identity = make_identity()
    state = initialize_adjustment_history(make_snapshot(identity))
    snapshots = []
    for index in range(MAX_ADJUSTMENT_HISTORY_TRANSACTIONS + 1):
        snapshot = make_snapshot(identity, float(index + 1))
        snapshots.append(snapshot)
        state = commit_adjustment_snapshot(state, snapshot)

    assert len(state.undo_transactions) == MAX_ADJUSTMENT_HISTORY_TRANSACTIONS
    for _ in range(MAX_ADJUSTMENT_HISTORY_TRANSACTIONS):
        state = undo_adjustment_snapshot(state)

    assert state.current_snapshot == snapshots[0]
    assert state.can_undo is False


def test_output_equivalent_requested_snapshot_is_still_a_transaction() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    requested = AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=identity,
        adjustments=(
            EventAdjustment(
                base_event_index=0,
                hold_frames=5,
            ),
        ),
    )

    state = commit_adjustment_snapshot(
        initialize_adjustment_history(initial),
        requested,
    )

    assert len(state.undo_transactions) == 1
    assert undo_adjustment_snapshot(state).current_snapshot == initial


def test_invalid_types_and_identity_mismatch_fail_closed() -> None:
    identity = make_identity()
    state = initialize_adjustment_history(make_snapshot(identity))
    other = make_snapshot(make_identity("base-b"), 0.5)

    with pytest.raises(AdjustmentContractError):
        initialize_adjustment_history(object())  # type: ignore[arg-type]
    with pytest.raises(AdjustmentContractError):
        commit_adjustment_snapshot(state, other)
    with pytest.raises(AdjustmentContractError):
        commit_adjustment_snapshot(
            state,
            make_snapshot(identity, 0.5),
            coalesce_key=make_key(make_identity("base-b")),
        )


def test_malformed_stale_history_state_is_rejected() -> None:
    identity = make_identity()
    initial = make_snapshot(identity)
    first = make_snapshot(identity, 0.5)
    valid = commit_adjustment_snapshot(
        initialize_adjustment_history(initial),
        first,
    )

    with pytest.raises(AdjustmentContractError, match="undo history is stale"):
        AdjustmentHistoryState(
            current_snapshot=initial,
            undo_transactions=valid.undo_transactions,
        )
