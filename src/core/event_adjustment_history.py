from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from .event_adjustment import (
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
)
from .output_edit_state import OutputEditState
from .model_profile_state import ModelProfileState


MAX_ADJUSTMENT_HISTORY_TRANSACTIONS = 50


def _require_snapshot(
    value: object,
    field_name: str,
) -> AdjustmentLayerSnapshot:
    if not isinstance(value, AdjustmentLayerSnapshot):
        raise AdjustmentContractError(
            f"{field_name} must be an AdjustmentLayerSnapshot"
        )
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise AdjustmentContractError(f"{field_name} must be a non-empty string")
    return value


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AdjustmentContractError(f"{field_name} must be a non-negative int")
    return value


def _require_optional_model_profile_state(
    value: object,
    field_name: str,
) -> ModelProfileState | None:
    if value is None:
        return None
    if not isinstance(value, ModelProfileState):
        raise AdjustmentContractError(
            f"{field_name} must be a ModelProfileState or None"
        )
    return value


@dataclass(frozen=True)
class AdjustmentCoalescingKey:
    base_plan_identity_digest: str
    base_event_index: int
    field: str
    gesture_token: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "base_plan_identity_digest",
            _require_non_empty_string(
                self.base_plan_identity_digest,
                "base_plan_identity_digest",
            ),
        )
        object.__setattr__(
            self,
            "base_event_index",
            _require_non_negative_int(self.base_event_index, "base_event_index"),
        )
        object.__setattr__(
            self,
            "field",
            _require_non_empty_string(self.field, "field"),
        )
        object.__setattr__(
            self,
            "gesture_token",
            _require_non_negative_int(self.gesture_token, "gesture_token"),
        )


@dataclass(frozen=True)
class AdjustmentHistoryTransaction:
    before_snapshot: AdjustmentLayerSnapshot
    after_snapshot: AdjustmentLayerSnapshot

    def __post_init__(self) -> None:
        before = _require_snapshot(self.before_snapshot, "before_snapshot")
        after = _require_snapshot(self.after_snapshot, "after_snapshot")
        if before.base_plan_identity != after.base_plan_identity:
            raise AdjustmentContractError(
                "history transaction base identity mismatch"
            )
        if before == after:
            raise AdjustmentContractError(
                "history transaction must change the adjustment snapshot"
            )


@dataclass(frozen=True)
class PendingAdjustmentHistoryEdit:
    key: AdjustmentCoalescingKey
    before_snapshot: AdjustmentLayerSnapshot
    after_snapshot: AdjustmentLayerSnapshot

    def __post_init__(self) -> None:
        if not isinstance(self.key, AdjustmentCoalescingKey):
            raise AdjustmentContractError(
                "pending edit key must be an AdjustmentCoalescingKey"
            )
        before = _require_snapshot(self.before_snapshot, "before_snapshot")
        after = _require_snapshot(self.after_snapshot, "after_snapshot")
        if before.base_plan_identity != after.base_plan_identity:
            raise AdjustmentContractError("pending edit base identity mismatch")
        if self.key.base_plan_identity_digest != before.base_plan_identity.digest:
            raise AdjustmentContractError(
                "pending edit key base identity mismatch"
            )


# Output-edit gestures intentionally reuse the established adjustment key.  The
# alias keeps B5 callers independent of the internal history representation.
OutputEditCoalescingKey = AdjustmentCoalescingKey


@dataclass(frozen=True)
class OutputEditHistoryTransaction:
    before_state: OutputEditState
    after_state: OutputEditState
    before_model_profile_state: ModelProfileState | None = None
    after_model_profile_state: ModelProfileState | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.before_state, OutputEditState):
            raise AdjustmentContractError(
                "before_state must be an OutputEditState"
            )
        if not isinstance(self.after_state, OutputEditState):
            raise AdjustmentContractError(
                "after_state must be an OutputEditState"
            )
        if self.before_state.base_plan_identity != self.after_state.base_plan_identity:
            raise AdjustmentContractError(
                "output history transaction base identity mismatch"
            )
        if (
            self.before_state == self.after_state
            and self.before_model_profile_state == self.after_model_profile_state
        ):
            raise AdjustmentContractError(
                "output history transaction must change the output state"
            )
        before_profile = _require_optional_model_profile_state(
            self.before_model_profile_state,
            "before_model_profile_state",
        )
        after_profile = _require_optional_model_profile_state(
            self.after_model_profile_state,
            "after_model_profile_state",
        )
        if (before_profile is None) != (after_profile is None):
            raise AdjustmentContractError(
                "output history transaction profile context must be a pair"
            )
        object.__setattr__(self, "before_model_profile_state", before_profile)
        object.__setattr__(self, "after_model_profile_state", after_profile)


@dataclass(frozen=True)
class PendingOutputEditHistoryEdit:
    key: AdjustmentCoalescingKey
    before_state: OutputEditState
    after_state: OutputEditState
    before_model_profile_state: ModelProfileState | None = None
    after_model_profile_state: ModelProfileState | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, AdjustmentCoalescingKey):
            raise AdjustmentContractError(
                "pending output edit key must be an AdjustmentCoalescingKey"
            )
        if not isinstance(self.before_state, OutputEditState):
            raise AdjustmentContractError(
                "pending output before_state must be an OutputEditState"
            )
        if not isinstance(self.after_state, OutputEditState):
            raise AdjustmentContractError(
                "pending output after_state must be an OutputEditState"
            )
        if self.before_state.base_plan_identity != self.after_state.base_plan_identity:
            raise AdjustmentContractError("pending output edit base identity mismatch")
        if self.key.base_plan_identity_digest != self.before_state.base_plan_identity.digest:
            raise AdjustmentContractError(
                "pending output edit key base identity mismatch"
            )
        before_profile = _require_optional_model_profile_state(
            self.before_model_profile_state,
            "before_model_profile_state",
        )
        after_profile = _require_optional_model_profile_state(
            self.after_model_profile_state,
            "after_model_profile_state",
        )
        if (before_profile is None) != (after_profile is None):
            raise AdjustmentContractError(
                "pending output edit profile context must be a pair"
            )
        object.__setattr__(self, "before_model_profile_state", before_profile)
        object.__setattr__(self, "after_model_profile_state", after_profile)


@dataclass(frozen=True)
class OutputEditHistoryState:
    current_state: OutputEditState
    undo_transactions: tuple[OutputEditHistoryTransaction, ...] = ()
    redo_transactions: tuple[OutputEditHistoryTransaction, ...] = ()
    pending_edit: PendingOutputEditHistoryEdit | None = None
    current_model_profile_state: ModelProfileState | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.current_state, OutputEditState):
            raise AdjustmentContractError("current_state must be an OutputEditState")
        current_profile = _require_optional_model_profile_state(
            self.current_model_profile_state,
            "current_model_profile_state",
        )
        object.__setattr__(self, "current_model_profile_state", current_profile)
        undo = tuple(self.undo_transactions)
        redo = tuple(self.redo_transactions)
        if any(not isinstance(item, OutputEditHistoryTransaction) for item in undo):
            raise AdjustmentContractError(
                "undo_transactions must contain output history transactions"
            )
        if any(not isinstance(item, OutputEditHistoryTransaction) for item in redo):
            raise AdjustmentContractError(
                "redo_transactions must contain output history transactions"
            )
        identity = self.current_state.base_plan_identity
        for transaction in (*undo, *redo):
            if (
                transaction.before_state.base_plan_identity != identity
                or transaction.after_state.base_plan_identity != identity
            ):
                raise AdjustmentContractError(
                    "output history contains a different base identity"
                )
            if (current_profile is None) != (
                transaction.before_model_profile_state is None
            ) or (current_profile is None) != (
                transaction.after_model_profile_state is None
            ):
                raise AdjustmentContractError(
                    "output history profile context is inconsistent"
                )
        object.__setattr__(self, "undo_transactions", undo)
        object.__setattr__(self, "redo_transactions", redo)

        pending = self.pending_edit
        anchor = self.current_state
        if pending is not None:
            if not isinstance(pending, PendingOutputEditHistoryEdit):
                raise AdjustmentContractError(
                    "pending_edit must be a PendingOutputEditHistoryEdit"
                )
            if pending.after_state != self.current_state:
                raise AdjustmentContractError(
                    "pending output edit after state must be current"
                )
            if (current_profile is None) != (
                pending.before_model_profile_state is None
            ) or (current_profile is None) != (
                pending.after_model_profile_state is None
            ):
                raise AdjustmentContractError(
                    "pending output profile context is inconsistent"
                )
            anchor = pending.before_state
        if undo and undo[-1].after_state != anchor:
            raise AdjustmentContractError("output undo history is stale")
        if redo and redo[-1].before_state != anchor:
            raise AdjustmentContractError("output redo history is stale")

    @property
    def has_pending_change(self) -> bool:
        return bool(
            self.pending_edit is not None
            and self.pending_edit.before_state != self.pending_edit.after_state
        )

    @property
    def can_undo(self) -> bool:
        return self.has_pending_change or bool(self.undo_transactions)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_transactions) and not self.has_pending_change


@dataclass(frozen=True)
class AdjustmentHistoryState:
    current_snapshot: AdjustmentLayerSnapshot
    undo_transactions: tuple[AdjustmentHistoryTransaction, ...] = ()
    redo_transactions: tuple[AdjustmentHistoryTransaction, ...] = ()
    pending_edit: PendingAdjustmentHistoryEdit | None = None

    def __post_init__(self) -> None:
        current = _require_snapshot(self.current_snapshot, "current_snapshot")
        undo = tuple(self.undo_transactions)
        redo = tuple(self.redo_transactions)
        if any(not isinstance(item, AdjustmentHistoryTransaction) for item in undo):
            raise AdjustmentContractError(
                "undo_transactions must contain history transactions"
            )
        if any(not isinstance(item, AdjustmentHistoryTransaction) for item in redo):
            raise AdjustmentContractError(
                "redo_transactions must contain history transactions"
            )
        object.__setattr__(self, "undo_transactions", undo)
        object.__setattr__(self, "redo_transactions", redo)

        identity = current.base_plan_identity
        for transaction in (*undo, *redo):
            if (
                transaction.before_snapshot.base_plan_identity != identity
                or transaction.after_snapshot.base_plan_identity != identity
            ):
                raise AdjustmentContractError(
                    "history state contains a different base identity"
                )

        pending = self.pending_edit
        anchor = current
        if pending is not None:
            if not isinstance(pending, PendingAdjustmentHistoryEdit):
                raise AdjustmentContractError(
                    "pending_edit must be a PendingAdjustmentHistoryEdit"
                )
            if pending.after_snapshot != current:
                raise AdjustmentContractError(
                    "pending edit after snapshot must be current"
                )
            anchor = pending.before_snapshot

        if undo and undo[-1].after_snapshot != anchor:
            raise AdjustmentContractError("undo history is stale")
        if redo and redo[-1].before_snapshot != anchor:
            raise AdjustmentContractError("redo history is stale")

    @property
    def has_pending_change(self) -> bool:
        return bool(
            self.pending_edit is not None
            and self.pending_edit.before_snapshot
            != self.pending_edit.after_snapshot
        )

    @property
    def can_undo(self) -> bool:
        return self.has_pending_change or bool(self.undo_transactions)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_transactions) and not self.has_pending_change


def initialize_adjustment_history(
    snapshot: AdjustmentLayerSnapshot,
) -> AdjustmentHistoryState:
    return AdjustmentHistoryState(
        current_snapshot=_require_snapshot(snapshot, "snapshot")
    )


def _append_undo_transaction(
    undo_transactions: tuple[AdjustmentHistoryTransaction, ...],
    transaction: AdjustmentHistoryTransaction,
) -> tuple[AdjustmentHistoryTransaction, ...]:
    updated = (*undo_transactions, transaction)
    return tuple(updated[-MAX_ADJUSTMENT_HISTORY_TRANSACTIONS:])


def finish_current_adjustment_coalescing(
    state: AdjustmentHistoryState,
) -> AdjustmentHistoryState:
    if not isinstance(state, AdjustmentHistoryState):
        raise AdjustmentContractError("state must be an AdjustmentHistoryState")
    pending = state.pending_edit
    if pending is None:
        return state
    if pending.before_snapshot == pending.after_snapshot:
        return AdjustmentHistoryState(
            current_snapshot=pending.before_snapshot,
            undo_transactions=state.undo_transactions,
            redo_transactions=state.redo_transactions,
        )
    transaction = AdjustmentHistoryTransaction(
        before_snapshot=pending.before_snapshot,
        after_snapshot=pending.after_snapshot,
    )
    return AdjustmentHistoryState(
        current_snapshot=pending.after_snapshot,
        undo_transactions=_append_undo_transaction(
            state.undo_transactions,
            transaction,
        ),
        redo_transactions=(),
    )


def finish_adjustment_coalescing(
    state: AdjustmentHistoryState,
    expected_key: AdjustmentCoalescingKey,
) -> AdjustmentHistoryState:
    if not isinstance(state, AdjustmentHistoryState):
        raise AdjustmentContractError("state must be an AdjustmentHistoryState")
    if not isinstance(expected_key, AdjustmentCoalescingKey):
        raise AdjustmentContractError(
            "expected_key must be an AdjustmentCoalescingKey"
        )
    pending = state.pending_edit
    if pending is None or pending.key != expected_key:
        return state
    return finish_current_adjustment_coalescing(state)


def commit_adjustment_snapshot(
    state: AdjustmentHistoryState,
    snapshot: AdjustmentLayerSnapshot,
    *,
    coalesce_key: AdjustmentCoalescingKey | None = None,
) -> AdjustmentHistoryState:
    if not isinstance(state, AdjustmentHistoryState):
        raise AdjustmentContractError("state must be an AdjustmentHistoryState")
    requested = _require_snapshot(snapshot, "snapshot")
    if requested.base_plan_identity != state.current_snapshot.base_plan_identity:
        raise AdjustmentContractError("adjustment history base identity mismatch")
    if coalesce_key is not None:
        if not isinstance(coalesce_key, AdjustmentCoalescingKey):
            raise AdjustmentContractError(
                "coalesce_key must be an AdjustmentCoalescingKey"
            )
        if (
            coalesce_key.base_plan_identity_digest
            != requested.base_plan_identity.digest
        ):
            raise AdjustmentContractError(
                "coalescing key base identity mismatch"
            )

    if coalesce_key is None:
        settled = finish_current_adjustment_coalescing(state)
        if requested == settled.current_snapshot:
            return settled
        transaction = AdjustmentHistoryTransaction(
            before_snapshot=settled.current_snapshot,
            after_snapshot=requested,
        )
        return AdjustmentHistoryState(
            current_snapshot=requested,
            undo_transactions=_append_undo_transaction(
                settled.undo_transactions,
                transaction,
            ),
            redo_transactions=(),
        )

    pending = state.pending_edit
    if pending is not None and pending.key != coalesce_key:
        state = finish_current_adjustment_coalescing(state)
        pending = None

    if pending is None:
        if requested == state.current_snapshot:
            return state
        return AdjustmentHistoryState(
            current_snapshot=requested,
            undo_transactions=state.undo_transactions,
            redo_transactions=state.redo_transactions,
            pending_edit=PendingAdjustmentHistoryEdit(
                key=coalesce_key,
                before_snapshot=state.current_snapshot,
                after_snapshot=requested,
            ),
        )

    if requested == state.current_snapshot:
        return state
    return AdjustmentHistoryState(
        current_snapshot=requested,
        undo_transactions=state.undo_transactions,
        redo_transactions=state.redo_transactions,
        pending_edit=PendingAdjustmentHistoryEdit(
            key=pending.key,
            before_snapshot=pending.before_snapshot,
            after_snapshot=requested,
        ),
    )


def undo_adjustment_snapshot(
    state: AdjustmentHistoryState,
) -> AdjustmentHistoryState:
    settled = finish_current_adjustment_coalescing(state)
    if not settled.undo_transactions:
        return settled
    transaction = settled.undo_transactions[-1]
    if transaction.after_snapshot != settled.current_snapshot:
        raise AdjustmentContractError("undo current snapshot is stale")
    return AdjustmentHistoryState(
        current_snapshot=transaction.before_snapshot,
        undo_transactions=settled.undo_transactions[:-1],
        redo_transactions=(*settled.redo_transactions, transaction),
    )


def redo_adjustment_snapshot(
    state: AdjustmentHistoryState,
) -> AdjustmentHistoryState:
    settled = finish_current_adjustment_coalescing(state)
    if not settled.redo_transactions:
        return settled
    transaction = settled.redo_transactions[-1]
    if transaction.before_snapshot != settled.current_snapshot:
        raise AdjustmentContractError("redo current snapshot is stale")
    return AdjustmentHistoryState(
        current_snapshot=transaction.after_snapshot,
        undo_transactions=_append_undo_transaction(
            settled.undo_transactions,
            transaction,
        ),
        redo_transactions=settled.redo_transactions[:-1],
    )


def _append_output_undo_transaction(
    undo_transactions: tuple[OutputEditHistoryTransaction, ...],
    transaction: OutputEditHistoryTransaction,
) -> tuple[OutputEditHistoryTransaction, ...]:
    updated = (*undo_transactions, transaction)
    return tuple(updated[-MAX_ADJUSTMENT_HISTORY_TRANSACTIONS:])


def initialize_output_edit_history(
    state: OutputEditState,
    *,
    model_profile_state: ModelProfileState | None = None,
) -> OutputEditHistoryState:
    if not isinstance(state, OutputEditState):
        raise AdjustmentContractError("state must be an OutputEditState")
    return OutputEditHistoryState(
        current_state=state,
        current_model_profile_state=_require_optional_model_profile_state(
            model_profile_state,
            "model_profile_state",
        ),
    )


def finish_current_output_edit_coalescing(
    state: OutputEditHistoryState,
) -> OutputEditHistoryState:
    if not isinstance(state, OutputEditHistoryState):
        raise AdjustmentContractError("state must be an OutputEditHistoryState")
    pending = state.pending_edit
    if pending is None:
        return state
    if (
        pending.before_state == pending.after_state
        and pending.before_model_profile_state == pending.after_model_profile_state
    ):
        return OutputEditHistoryState(
            current_state=pending.before_state,
            undo_transactions=state.undo_transactions,
            redo_transactions=state.redo_transactions,
            current_model_profile_state=pending.after_model_profile_state,
        )
    transaction = OutputEditHistoryTransaction(
        before_state=pending.before_state,
        after_state=pending.after_state,
        before_model_profile_state=pending.before_model_profile_state,
        after_model_profile_state=pending.after_model_profile_state,
    )
    return OutputEditHistoryState(
        current_state=pending.after_state,
        undo_transactions=_append_output_undo_transaction(
            state.undo_transactions,
            transaction,
        ),
        redo_transactions=(),
        current_model_profile_state=pending.after_model_profile_state,
    )


def finish_output_edit_coalescing(
    state: OutputEditHistoryState,
    expected_key: AdjustmentCoalescingKey,
) -> OutputEditHistoryState:
    if not isinstance(state, OutputEditHistoryState):
        raise AdjustmentContractError("state must be an OutputEditHistoryState")
    if not isinstance(expected_key, AdjustmentCoalescingKey):
        raise AdjustmentContractError(
            "expected_key must be an AdjustmentCoalescingKey"
        )
    pending = state.pending_edit
    if pending is None or pending.key != expected_key:
        return state
    return finish_current_output_edit_coalescing(state)


def commit_output_edit_state(
    state: OutputEditHistoryState,
    output_state: OutputEditState,
    *,
    coalesce_key: AdjustmentCoalescingKey | None = None,
    model_profile_state: ModelProfileState | None = None,
) -> OutputEditHistoryState:
    if not isinstance(state, OutputEditHistoryState):
        raise AdjustmentContractError("state must be an OutputEditHistoryState")
    if not isinstance(output_state, OutputEditState):
        raise AdjustmentContractError("output_state must be an OutputEditState")
    model_profile_state = _require_optional_model_profile_state(
        model_profile_state,
        "model_profile_state",
    )
    if output_state.base_plan_identity != state.current_state.base_plan_identity:
        raise AdjustmentContractError("output edit history base identity mismatch")
    if coalesce_key is not None:
        if not isinstance(coalesce_key, AdjustmentCoalescingKey):
            raise AdjustmentContractError(
                "coalesce_key must be an AdjustmentCoalescingKey"
            )
        if coalesce_key.base_plan_identity_digest != output_state.base_plan_identity.digest:
            raise AdjustmentContractError(
                "output coalescing key base identity mismatch"
            )

    if coalesce_key is None:
        settled = finish_current_output_edit_coalescing(state)
        if (
            output_state == settled.current_state
            and model_profile_state == settled.current_model_profile_state
        ):
            return settled
        transaction = OutputEditHistoryTransaction(
            before_state=settled.current_state,
            after_state=output_state,
            before_model_profile_state=settled.current_model_profile_state,
            after_model_profile_state=model_profile_state,
        )
        return OutputEditHistoryState(
            current_state=output_state,
            undo_transactions=_append_output_undo_transaction(
                settled.undo_transactions,
                transaction,
            ),
            redo_transactions=(),
            current_model_profile_state=model_profile_state,
        )

    pending = state.pending_edit
    if pending is not None and pending.key != coalesce_key:
        state = finish_current_output_edit_coalescing(state)
        pending = None
    if pending is None:
        if (
            output_state == state.current_state
            and model_profile_state == state.current_model_profile_state
        ):
            return state
        return OutputEditHistoryState(
            current_state=output_state,
            undo_transactions=state.undo_transactions,
            redo_transactions=state.redo_transactions,
            pending_edit=PendingOutputEditHistoryEdit(
                key=coalesce_key,
                before_state=state.current_state,
                after_state=output_state,
                before_model_profile_state=state.current_model_profile_state,
                after_model_profile_state=model_profile_state,
            ),
            current_model_profile_state=model_profile_state,
        )
    if (
        output_state == state.current_state
        and model_profile_state == state.current_model_profile_state
    ):
        return state
    return OutputEditHistoryState(
        current_state=output_state,
        undo_transactions=state.undo_transactions,
        redo_transactions=state.redo_transactions,
        pending_edit=PendingOutputEditHistoryEdit(
            key=pending.key,
            before_state=pending.before_state,
            after_state=output_state,
            before_model_profile_state=pending.before_model_profile_state,
            after_model_profile_state=model_profile_state,
        ),
        current_model_profile_state=model_profile_state,
    )


def undo_output_edit_state(
    state: OutputEditHistoryState,
) -> OutputEditHistoryState:
    settled = finish_current_output_edit_coalescing(state)
    if not settled.undo_transactions:
        return settled
    transaction = settled.undo_transactions[-1]
    if transaction.after_state != settled.current_state:
        raise AdjustmentContractError("output undo current state is stale")
    return OutputEditHistoryState(
        current_state=transaction.before_state,
        undo_transactions=settled.undo_transactions[:-1],
        redo_transactions=(*settled.redo_transactions, transaction),
        current_model_profile_state=transaction.before_model_profile_state,
    )


def redo_output_edit_state(
    state: OutputEditHistoryState,
) -> OutputEditHistoryState:
    settled = finish_current_output_edit_coalescing(state)
    if not settled.redo_transactions:
        return settled
    transaction = settled.redo_transactions[-1]
    if transaction.before_state != settled.current_state:
        raise AdjustmentContractError("output redo current state is stale")
    return OutputEditHistoryState(
        current_state=transaction.after_state,
        undo_transactions=_append_output_undo_transaction(
            settled.undo_transactions,
            transaction,
        ),
        redo_transactions=settled.redo_transactions[:-1],
        current_model_profile_state=transaction.after_model_profile_state,
    )


def normalize_output_edit_history_state(
    state: OutputEditHistoryState,
    normalize_generation_state: Callable[[object], object],
) -> OutputEditHistoryState:
    """Normalize preset identities across current and navigation endpoints atomically."""
    if not isinstance(state, OutputEditHistoryState):
        raise AdjustmentContractError("state must be an OutputEditHistoryState")

    def normalize_output_state(output_state: OutputEditState) -> OutputEditState:
        normalized = normalize_generation_state(output_state.generation_state)
        if not isinstance(normalized, type(output_state.generation_state)):
            raise AdjustmentContractError(
                "normalized generation state must be a GenerationState"
            )
        if normalized == output_state.generation_state:
            return output_state
        return OutputEditState(
            base_plan_identity=output_state.base_plan_identity,
            adjustment_snapshot=output_state.adjustment_snapshot,
            generation_state=normalized,
            morph_upper_limit=output_state.morph_upper_limit,
        )

    settled = finish_current_output_edit_coalescing(state)
    current = normalize_output_state(settled.current_state)
    normalized_undo: list[OutputEditHistoryTransaction] = []
    for item in settled.undo_transactions:
        before_state = normalize_output_state(item.before_state)
        after_state = normalize_output_state(item.after_state)
        if (
            before_state == after_state
            and item.before_model_profile_state == item.after_model_profile_state
        ):
            continue
        normalized_undo.append(
            OutputEditHistoryTransaction(
                before_state=before_state,
                after_state=after_state,
                before_model_profile_state=item.before_model_profile_state,
                after_model_profile_state=item.after_model_profile_state,
            )
        )
    normalized_redo: list[OutputEditHistoryTransaction] = []
    for item in settled.redo_transactions:
        before_state = normalize_output_state(item.before_state)
        after_state = normalize_output_state(item.after_state)
        if (
            before_state == after_state
            and item.before_model_profile_state == item.after_model_profile_state
        ):
            continue
        normalized_redo.append(
            OutputEditHistoryTransaction(
                before_state=before_state,
                after_state=after_state,
                before_model_profile_state=item.before_model_profile_state,
                after_model_profile_state=item.after_model_profile_state,
            )
        )
    return OutputEditHistoryState(
        current_state=current,
        undo_transactions=tuple(normalized_undo),
        redo_transactions=tuple(normalized_redo),
        current_model_profile_state=settled.current_model_profile_state,
    )


def normalize_profile_aware_output_edit_history_state(
    state: OutputEditHistoryState,
    resolve_endpoint: Callable[
        [OutputEditState, ModelProfileState | None],
        tuple[OutputEditState, ModelProfileState | None] | None,
    ],
) -> OutputEditHistoryState:
    """Normalize profile-aware endpoints against a candidate store collection.

    The callback is pure and returns ``None`` for an endpoint that cannot be
    resolved after a store mutation.  The current endpoint must remain
    resolvable; disconnected historical transactions are compacted while the
    live state is left untouched until the caller adopts this return value.
    """
    if not isinstance(state, OutputEditHistoryState):
        raise AdjustmentContractError("state must be an OutputEditHistoryState")
    if not callable(resolve_endpoint):
        raise AdjustmentContractError("resolve_endpoint must be callable")

    settled = finish_current_output_edit_coalescing(state)

    def resolve(
        output_state: OutputEditState,
        profile_state: ModelProfileState | None,
    ) -> tuple[OutputEditState, ModelProfileState | None] | None:
        result = resolve_endpoint(output_state, profile_state)
        if result is None:
            return None
        if (
            not isinstance(result, tuple)
            or len(result) != 2
            or not isinstance(result[0], OutputEditState)
        ):
            raise AdjustmentContractError(
                "resolve_endpoint must return an output/profile state pair or None"
            )
        _require_optional_model_profile_state(result[1], "resolved profile state")
        return result

    current_result = resolve(
        settled.current_state,
        settled.current_model_profile_state,
    )
    if current_result is None:
        raise AdjustmentContractError("current output endpoint cannot be resolved")
    current, current_profile = current_result

    def compact_undo() -> tuple[OutputEditHistoryTransaction, ...]:
        cursor = (current, current_profile)
        selected: list[OutputEditHistoryTransaction] = []
        for transaction in reversed(settled.undo_transactions):
            before = resolve(
                transaction.before_state,
                transaction.before_model_profile_state,
            )
            after = resolve(
                transaction.after_state,
                transaction.after_model_profile_state,
            )
            if before is None or after is None or after != cursor:
                continue
            if before == after:
                continue
            selected.append(
                OutputEditHistoryTransaction(
                    before_state=before[0],
                    after_state=after[0],
                    before_model_profile_state=before[1],
                    after_model_profile_state=after[1],
                )
            )
            cursor = before
        return tuple(reversed(selected))

    def compact_redo() -> tuple[OutputEditHistoryTransaction, ...]:
        cursor = (current, current_profile)
        selected: list[OutputEditHistoryTransaction] = []
        for transaction in reversed(settled.redo_transactions):
            before = resolve(
                transaction.before_state,
                transaction.before_model_profile_state,
            )
            after = resolve(
                transaction.after_state,
                transaction.after_model_profile_state,
            )
            if before is None or after is None or before != cursor:
                continue
            if before == after:
                continue
            selected.append(
                OutputEditHistoryTransaction(
                    before_state=before[0],
                    after_state=after[0],
                    before_model_profile_state=before[1],
                    after_model_profile_state=after[1],
                )
            )
            cursor = after
        return tuple(reversed(selected))

    return OutputEditHistoryState(
        current_state=current,
        undo_transactions=compact_undo(),
        redo_transactions=compact_redo(),
        current_model_profile_state=current_profile,
    )


__all__ = [
    "MAX_ADJUSTMENT_HISTORY_TRANSACTIONS",
    "AdjustmentCoalescingKey",
    "AdjustmentHistoryState",
    "AdjustmentHistoryTransaction",
    "PendingAdjustmentHistoryEdit",
    "OutputEditCoalescingKey",
    "OutputEditHistoryState",
    "OutputEditHistoryTransaction",
    "PendingOutputEditHistoryEdit",
    "commit_adjustment_snapshot",
    "finish_adjustment_coalescing",
    "finish_current_adjustment_coalescing",
    "initialize_adjustment_history",
    "redo_adjustment_snapshot",
    "undo_adjustment_snapshot",
    "commit_output_edit_state",
    "finish_output_edit_coalescing",
    "finish_current_output_edit_coalescing",
    "initialize_output_edit_history",
    "normalize_output_edit_history_state",
    "normalize_profile_aware_output_edit_history_state",
    "redo_output_edit_state",
    "undo_output_edit_state",
]
