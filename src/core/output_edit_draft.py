from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Sequence

from .effective_shape_plan import BaseTimingPlanInput, build_base_plan_identity
from .event_adjustment import (
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
    EventAdjustment,
    canonicalize_adjustment_snapshot,
)
from .event_adjustment_history import (
    OutputEditHistoryState,
    OutputEditHistoryTransaction,
    finish_current_output_edit_coalescing,
)
from .model_profile_state import ModelProfileState
from .output_edit_state import OutputEditState


SourceEventKey = tuple[str, int | None, bool, int | None, str]


@dataclass(frozen=True, slots=True)
class OutputEditDraftBaseline:
    source_revision: int
    source_event_keys: tuple[SourceEventKey, ...]
    output_state: OutputEditState
    model_profile_state: ModelProfileState

    def __post_init__(self) -> None:
        if (
            isinstance(self.source_revision, bool)
            or not isinstance(self.source_revision, int)
            or self.source_revision < 0
        ):
            raise AdjustmentContractError(
                "source_revision must be a non-negative integer"
            )
        keys = tuple(self.source_event_keys)
        if len(set(keys)) != len(keys):
            raise AdjustmentContractError(
                "source event identities are ambiguous",
                safe_code="source_event_identity_ambiguous",
                safe_field_code="source_event_keys",
                safe_phase="draft_source_identity",
            )
        if not isinstance(self.output_state, OutputEditState):
            raise AdjustmentContractError("output_state must be an OutputEditState")
        if not isinstance(self.model_profile_state, ModelProfileState):
            raise AdjustmentContractError(
                "model_profile_state must be a ModelProfileState"
            )
        object.__setattr__(self, "source_event_keys", keys)


def source_event_keys(timeline: Sequence[object]) -> tuple[SourceEventKey, ...]:
    """Build stable keys for events whose peak value may change with the upper limit."""
    keys: list[SourceEventKey] = []
    for index, point in enumerate(timeline):
        vowel = getattr(point, "vowel", None)
        time_sec = getattr(point, "time_sec", None)
        token_index = getattr(point, "vowel_token_index", None)
        is_continuation = getattr(point, "is_long_vowel_continuation", False)
        long_source = getattr(point, "long_vowel_source_token_index", None)
        if (
            not isinstance(vowel, str)
            or not vowel
            or isinstance(time_sec, bool)
            or not isinstance(time_sec, (int, float))
            or not math.isfinite(float(time_sec))
            or not isinstance(is_continuation, bool)
        ):
            raise AdjustmentContractError(
                f"source event {index} has invalid identity data",
                safe_code="source_event_identity_invalid",
                safe_field_code="timeline",
                event_index=index,
                safe_phase="draft_source_identity",
            )
        if token_index is not None and (
            isinstance(token_index, bool)
            or not isinstance(token_index, int)
            or token_index < 0
        ):
            raise AdjustmentContractError(
                f"source event {index} has invalid token identity",
                safe_code="source_event_identity_invalid",
                safe_field_code="vowel_token_index",
                event_index=index,
                safe_phase="draft_source_identity",
            )
        if long_source is not None and (
            isinstance(long_source, bool)
            or not isinstance(long_source, int)
            or long_source < 0
        ):
            raise AdjustmentContractError(
                f"source event {index} has invalid long-vowel identity",
                safe_code="source_event_identity_invalid",
                safe_field_code="long_vowel_source_token_index",
                event_index=index,
                safe_phase="draft_source_identity",
            )
        keys.append(
            (
                vowel,
                token_index,
                is_continuation,
                long_source,
                float(time_sec).hex(),
            )
        )
    if len(set(keys)) != len(keys):
        raise AdjustmentContractError(
            "source event identities are ambiguous",
            safe_code="source_event_identity_ambiguous",
            safe_field_code="timeline",
            safe_phase="draft_source_identity",
        )
    return tuple(keys)


def rebase_adjustment_snapshot(
    snapshot: AdjustmentLayerSnapshot,
    source_keys: Sequence[SourceEventKey],
    target_base_input: BaseTimingPlanInput,
) -> tuple[AdjustmentLayerSnapshot, tuple[SourceEventKey, ...]]:
    """Map event adjustments by source identity and validate them on a new base."""
    if not isinstance(snapshot, AdjustmentLayerSnapshot):
        raise AdjustmentContractError("snapshot must be an AdjustmentLayerSnapshot")
    old_keys = tuple(source_keys)
    new_keys = source_event_keys(target_base_input.timeline)
    if len(set(old_keys)) != len(old_keys) or len(set(new_keys)) != len(new_keys):
        raise AdjustmentContractError(
            "source event mapping is ambiguous",
            safe_code="source_event_mapping_ambiguous",
            safe_field_code="source_event_keys",
            safe_phase="draft_rebase",
        )
    new_index_by_key = {key: index for index, key in enumerate(new_keys)}
    rebased: list[EventAdjustment] = []
    for item in snapshot.adjustments:
        if item.base_event_index >= len(old_keys):
            raise AdjustmentContractError(
                "adjustment points outside its source event mapping",
                safe_code="source_event_mapping_unavailable",
                safe_field_code="base_event_index",
                event_index=item.base_event_index,
                safe_phase="draft_rebase",
            )
        target_index = new_index_by_key.get(old_keys[item.base_event_index])
        if target_index is None:
            raise AdjustmentContractError(
                "edited source event is missing from the new base",
                safe_code="source_event_mapping_missing",
                safe_field_code="base_event_index",
                event_index=item.base_event_index,
                safe_phase="draft_rebase",
            )
        rebased.append(replace(item, base_event_index=target_index))
    identity = build_base_plan_identity(target_base_input)
    peaks = tuple(float(getattr(point, "peak_value", getattr(point, "value", 0.0))) for point in target_base_input.timeline)
    result = canonicalize_adjustment_snapshot(
        identity,
        rebased,
        base_peak_values=peaks,
        closing_hold_frames=target_base_input.shape_parameters.closing_hold_frames,
        closing_softness_frames=target_base_input.shape_parameters.closing_softness_frames,
    )
    return result, new_keys


def semantic_output_edit_key(
    output_state: OutputEditState,
    model_profile_state: ModelProfileState | None,
    event_keys: Sequence[SourceEventKey],
) -> tuple[object, ...]:
    """Compare draft and applied values without treating a rederived base digest as an edit."""
    if not isinstance(output_state, OutputEditState):
        raise AdjustmentContractError("output_state must be an OutputEditState")
    keys = tuple(event_keys)
    adjustments: list[tuple[SourceEventKey, tuple[object, ...]]] = []
    for item in output_state.adjustment_snapshot.adjustments:
        if item.base_event_index >= len(keys):
            raise AdjustmentContractError(
                "adjustment is outside its source event mapping",
                safe_code="source_event_mapping_unavailable",
                safe_field_code="base_event_index",
                event_index=item.base_event_index,
                safe_phase="draft_compare",
            )
        adjustments.append(
            (
                keys[item.base_event_index],
                (
                    item.peak_value,
                    item.start_offset_frames,
                    item.end_offset_frames,
                    item.hold_frames,
                    item.softness_frames,
                    item.slope_ratio,
                    item.long_vowel_mode,
                    item.manual_overlap_limit_override,
                ),
            )
        )
    return (
        output_state.morph_upper_limit,
        output_state.generation_state,
        model_profile_state,
        tuple(adjustments),
    )


def rebase_output_edit_history(
    history: OutputEditHistoryState,
    source_keys: Sequence[SourceEventKey],
    target_base_input: BaseTimingPlanInput,
) -> tuple[OutputEditHistoryState, tuple[SourceEventKey, ...]]:
    """Rebase every endpoint atomically while retaining profile and undo/redo order."""
    if not isinstance(history, OutputEditHistoryState):
        raise AdjustmentContractError("history must be an OutputEditHistoryState")

    def state_and_profile(output: OutputEditState, profile: ModelProfileState | None):
        adjustment, keys = rebase_adjustment_snapshot(
            output.adjustment_snapshot,
            source_keys,
            target_base_input,
        )
        return (
            OutputEditState(
                base_plan_identity=adjustment.base_plan_identity,
                adjustment_snapshot=adjustment,
                generation_state=output.generation_state,
                morph_upper_limit=output.morph_upper_limit,
            ),
            profile,
            keys,
        )

    settled = finish_current_output_edit_coalescing(history)
    current, current_profile, keys = state_and_profile(
        settled.current_state,
        settled.current_model_profile_state,
    )
    undo: list[OutputEditHistoryTransaction] = []
    for item in settled.undo_transactions:
        before, before_profile, _ = state_and_profile(
            item.before_state,
            item.before_model_profile_state,
        )
        after, after_profile, _ = state_and_profile(
            item.after_state,
            item.after_model_profile_state,
        )
        if before != after or before_profile != after_profile:
            undo.append(
                OutputEditHistoryTransaction(
                    before_state=before,
                    after_state=after,
                    before_model_profile_state=before_profile,
                    after_model_profile_state=after_profile,
                )
            )
    redo: list[OutputEditHistoryTransaction] = []
    for item in settled.redo_transactions:
        before, before_profile, _ = state_and_profile(
            item.before_state,
            item.before_model_profile_state,
        )
        after, after_profile, _ = state_and_profile(
            item.after_state,
            item.after_model_profile_state,
        )
        if before != after or before_profile != after_profile:
            redo.append(
                OutputEditHistoryTransaction(
                    before_state=before,
                    after_state=after,
                    before_model_profile_state=before_profile,
                    after_model_profile_state=after_profile,
                )
            )
    return (
        OutputEditHistoryState(
            current_state=current,
            undo_transactions=tuple(undo),
            redo_transactions=tuple(redo),
            current_model_profile_state=current_profile,
        ),
        keys,
    )


__all__ = [
    "OutputEditDraftBaseline",
    "SourceEventKey",
    "rebase_adjustment_snapshot",
    "rebase_output_edit_history",
    "semantic_output_edit_key",
    "source_event_keys",
]
