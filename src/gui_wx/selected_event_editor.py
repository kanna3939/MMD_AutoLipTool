from __future__ import annotations

from dataclasses import dataclass, replace
import math

from src.core.effective_shape_plan import (
    EffectiveShapePlan,
    resolve_manual_crossfade_end_offset_max,
)
from src.core.event_adjustment import (
    DEFAULT_SLOPE_RATIO,
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
    EventAdjustment,
    LONG_VOWEL_MODE_DECAY,
    validate_long_vowel_mode,
)


EDITABLE_FIELDS = (
    "peak_value",
    "start_offset_frames",
    "end_offset_frames",
    "hold_frames",
    "softness_frames",
    "slope_ratio",
    "long_vowel_mode",
    "manual_overlap_limit_override",
)
GESTURE_EDITABLE_FIELDS = tuple(
    field
    for field in EDITABLE_FIELDS
    if field not in {"long_vowel_mode", "manual_overlap_limit_override"}
)
TAIL_FIELDS = ("hold_frames", "softness_frames", "slope_ratio")
GROUP_SHARED_FIELDS = (*TAIL_FIELDS, "manual_overlap_limit_override")


@dataclass(frozen=True)
class SelectedEventEditorState:
    base_event_index: int
    vowel: str
    base_identity_digest: str
    editor_revision: int
    group_member_count: int
    is_group_tail: bool
    group_tail_base_event_index: int
    long_vowel_mode_enabled: bool
    requested_long_vowel_mode: str | None
    effective_long_vowel_mode: str | None
    long_vowel_mode_overridden: bool
    long_vowel_mode_notice: str
    tail_controls_enabled: bool
    manual_overlap_override_enabled: bool
    requested_manual_overlap_limit_override: bool
    base_start_frame: int
    base_peak_frame: int
    base_end_frame: int
    base_peak_value: float
    requested_peak_value: float
    requested_start_offset_frames: int
    requested_end_offset_frames: int
    requested_hold_frames: int
    requested_softness_frames: int
    requested_slope_ratio: float
    effective_start_frame: int
    effective_peak_frame: int
    effective_end_frame: int
    effective_peak_value: float
    effective_hold_frames: int
    effective_softness_frames: int
    available_extension_frames: int | None
    hold_is_limited: bool
    softness_is_limited: bool
    effect_notice_header: str
    effect_notice_lines: tuple[str, ...]
    crossfade_notice_header: str
    crossfade_notice_lines: tuple[str, ...]
    slope_helper_text: str
    peak_overridden: bool
    start_overridden: bool
    end_overridden: bool
    hold_overridden: bool
    softness_overridden: bool
    slope_overridden: bool
    slope_enabled: bool
    reset_enabled: bool
    start_offset_min: int
    start_offset_max: int
    end_offset_min: int
    end_offset_max: int
    end_offset_range_error: str
    final_output_binding: str | None = None


@dataclass(frozen=True)
class SelectedEventEditRequest:
    base_event_index: int
    base_identity_digest: str
    editor_revision: int
    field: str
    value: float | int | str | None
    coalescing_token: int | None = None
    final_output_binding: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.base_event_index, bool)
            or not isinstance(self.base_event_index, int)
            or self.base_event_index < 0
        ):
            raise AdjustmentContractError("base_event_index must be a non-negative int")
        if not isinstance(self.base_identity_digest, str) or not self.base_identity_digest:
            raise AdjustmentContractError("base_identity_digest must be a non-empty string")
        if (
            isinstance(self.editor_revision, bool)
            or not isinstance(self.editor_revision, int)
            or self.editor_revision < 0
        ):
            raise AdjustmentContractError("editor_revision must be a non-negative int")
        if self.field not in EDITABLE_FIELDS:
            raise AdjustmentContractError(f"unsupported editor field: {self.field}")
        if self.coalescing_token is not None and (
            isinstance(self.coalescing_token, bool)
            or not isinstance(self.coalescing_token, int)
            or self.coalescing_token < 0
        ):
            raise AdjustmentContractError(
                "coalescing_token must be a non-negative int or None"
            )
        if self.final_output_binding is not None and (
            not isinstance(self.final_output_binding, str)
            or not self.final_output_binding
        ):
            raise AdjustmentContractError(
                "final_output_binding must be non-empty text or None"
            )


@dataclass(frozen=True)
class SelectedEventEditBoundaryRequest:
    base_event_index: int
    base_identity_digest: str
    field: str
    coalescing_token: int
    final_output_binding: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.base_event_index, bool)
            or not isinstance(self.base_event_index, int)
            or self.base_event_index < 0
        ):
            raise AdjustmentContractError(
                "base_event_index must be a non-negative int"
            )
        if (
            not isinstance(self.base_identity_digest, str)
            or not self.base_identity_digest
        ):
            raise AdjustmentContractError(
                "base_identity_digest must be a non-empty string"
            )
        if self.field not in GESTURE_EDITABLE_FIELDS:
            raise AdjustmentContractError(
                f"unsupported editor field: {self.field}"
            )
        if (
            isinstance(self.coalescing_token, bool)
            or not isinstance(self.coalescing_token, int)
            or self.coalescing_token < 0
        ):
            raise AdjustmentContractError(
                "coalescing_token must be a non-negative int"
            )
        if self.final_output_binding is not None and (
            not isinstance(self.final_output_binding, str)
            or not self.final_output_binding
        ):
            raise AdjustmentContractError(
                "final_output_binding must be non-empty text or None"
            )


def _one_by_index(values, index: int, *, field_name: str):
    matches = tuple(
        value for value in values if getattr(value, "base_event_index", None) == index
    )
    if len(matches) != 1:
        raise AdjustmentContractError(
            f"{field_name} must contain exactly one entry for base_event_index"
        )
    return matches[0]


def _build_tail_effect_notice(
    *,
    is_group_tail: bool,
    requested_hold_frames: int,
    requested_softness_frames: int,
    effective_hold_frames: int,
    effective_softness_frames: int,
    slope_enabled: bool,
) -> tuple[str, tuple[str, ...], str]:
    if not is_group_tail:
        return "", (), ""

    hold_is_limited = requested_hold_frames != effective_hold_frames
    softness_is_limited = requested_softness_frames != effective_softness_frames
    lines = []
    if hold_is_limited:
        lines.append(
            "開口保持: "
            f"設定 {requested_hold_frames} → 反映 {effective_hold_frames} フレーム"
        )
    if softness_is_limited:
        lines.append(
            "閉口スムーズ: "
            f"設定 {requested_softness_frames} → "
            f"反映 {effective_softness_frames} フレーム"
        )
    if (
        requested_softness_frames > 0
        and effective_softness_frames == 0
        and not slope_enabled
    ):
        lines.append(
            "閉口スムーズが反映されないため、"
            "傾斜比は現在のプレビューには反映されません。"
        )

    header = (
        "次の口形までの間隔が短いため、設定値を一部だけ反映しています。"
        if hold_is_limited or softness_is_limited
        else ""
    )
    helper = (
        "傾斜比を調整するには、閉口スムーズを1フレーム以上にしてください。"
        if requested_softness_frames == 0 and not slope_enabled
        else ""
    )
    return header, tuple(lines), helper


def _build_crossfade_notice(
    effective_plan: EffectiveShapePlan,
    selected_base_event_index: int,
) -> tuple[str, tuple[str, ...]]:
    matches = tuple(
        item
        for item in effective_plan.manual_crossfades
        if item.source_base_event_index == selected_base_event_index
        and item.high_target_keyframes
    )
    if not matches:
        return "", ()
    target_vowels = tuple(
        dict.fromkeys(
            item.target_vowel
            for item in matches
        )
    )
    target_text = "・".join(f"「{vowel}」" for vowel in target_vowels)
    return (
        "次の口形とクロスフェードしています。",
        (
            f"重複区間内で{target_text}の開口量が0.95以上に設定されています。",
            "意図した動きかプレビューとMMD上で確認してください。",
        ),
    )


def build_selected_event_editor_state(
    effective_plan: EffectiveShapePlan,
    selected_base_event_index: int,
    *,
    expected_base_identity_digest: str,
    editor_revision: int,
    source_duration_frames: int,
    adjustment_snapshot: AdjustmentLayerSnapshot | None = None,
    final_output_binding: str | None = None,
) -> SelectedEventEditorState:
    if not isinstance(effective_plan, EffectiveShapePlan):
        raise AdjustmentContractError("effective_plan must be EffectiveShapePlan")
    digest = effective_plan.base_plan_identity.digest
    if digest != expected_base_identity_digest:
        raise AdjustmentContractError("selected event base identity mismatch")
    if (
        isinstance(selected_base_event_index, bool)
        or not isinstance(selected_base_event_index, int)
        or selected_base_event_index < 0
    ):
        raise AdjustmentContractError("selected_base_event_index must be a non-negative int")
    if (
        isinstance(source_duration_frames, bool)
        or not isinstance(source_duration_frames, int)
        or source_duration_frames < 0
    ):
        raise AdjustmentContractError("source_duration_frames must be a non-negative int")
    if final_output_binding is not None and (
        not isinstance(final_output_binding, str) or not final_output_binding
    ):
        raise AdjustmentContractError(
            "final_output_binding must be non-empty text or None"
        )
    requested_snapshot = (
        effective_plan.canonical_adjustment_snapshot
        if adjustment_snapshot is None
        else adjustment_snapshot
    )
    if (
        not isinstance(requested_snapshot, AdjustmentLayerSnapshot)
        or requested_snapshot.base_plan_identity != effective_plan.base_plan_identity
    ):
        raise AdjustmentContractError(
            "selected event draft snapshot identity mismatch"
        )

    base = _one_by_index(
        effective_plan.base_events,
        selected_base_event_index,
        field_name="base_events",
    )
    effective = _one_by_index(
        effective_plan.effective_events,
        selected_base_event_index,
        field_name="effective_events",
    )
    matching_shapes = tuple(
        shape
        for shape in effective_plan.shapes
        if selected_base_event_index in shape.real_base_event_indices
    )
    if len(matching_shapes) != 1:
        raise AdjustmentContractError(
            "shapes must contain exactly one selected real base event"
        )
    shape = matching_shapes[0]
    if shape.resolved_tail is None:
        raise AdjustmentContractError("selected shape is missing resolved tail metadata")

    adjustments_by_index = {
        item.base_event_index: item for item in requested_snapshot.adjustments
    }
    adjustment = adjustments_by_index.get(selected_base_event_index)
    tail = shape.resolved_tail
    is_tail = tail.tail_base_event_index == selected_base_event_index
    tail_adjustment = adjustments_by_index.get(tail.tail_base_event_index)
    long_run = next(
        (
            item
            for item in effective_plan.long_vowel_runs
            if selected_base_event_index
            in (item.source_base_event_index, *item.continuation_base_event_indices)
        ),
        None,
    )
    is_long_vowel_terminal = bool(
        long_run is not None
        and long_run.terminal_base_event_index == selected_base_event_index
    )
    requested_long_vowel_mode = (
        adjustment.long_vowel_mode
        if is_long_vowel_terminal and adjustment is not None
        else None
    )
    effective_long_vowel_mode = (
        long_run.resolved_mode if is_long_vowel_terminal and long_run is not None else None
    )
    if is_long_vowel_terminal:
        long_vowel_mode_notice = (
            "decayでは長音終端を0へ減衰させるため、閉口設定は一時的に反映されません。"
            "holdへ戻すと保持済みの設定を再利用します。"
            if effective_long_vowel_mode == LONG_VOWEL_MODE_DECAY
            else "継承は現在の生成設定の長音モードを使用します。"
        )
    elif long_run is not None:
        long_vowel_mode_notice = "長音モードは長音終端イベントでのみ編集できます。"
    else:
        long_vowel_mode_notice = "長音モードは長音終端イベントでのみ編集できます。"
    peak_override = adjustment is not None and adjustment.peak_value is not None
    start_override = adjustment is not None and adjustment.start_offset_frames != 0
    end_override = adjustment is not None and adjustment.end_offset_frames != 0
    hold_override = tail_adjustment is not None and tail_adjustment.hold_frames is not None
    softness_override = (
        tail_adjustment is not None and tail_adjustment.softness_frames is not None
    )
    slope_override = tail_adjustment is not None and tail_adjustment.slope_ratio is not None
    slope_enabled = tail.has_slope_midpoint
    requested_hold_frames = (
        tail_adjustment.hold_frames
        if tail_adjustment is not None and tail_adjustment.hold_frames is not None
        else effective_plan.shape_parameters.closing_hold_frames
    )
    requested_softness_frames = (
        tail_adjustment.softness_frames
        if tail_adjustment is not None and tail_adjustment.softness_frames is not None
        else effective_plan.shape_parameters.closing_softness_frames
    )
    requested_slope_ratio = (
        tail_adjustment.slope_ratio
        if tail_adjustment is not None and tail_adjustment.slope_ratio is not None
        else DEFAULT_SLOPE_RATIO
    )
    hold_is_limited = requested_hold_frames != tail.effective_hold_frames
    softness_is_limited = (
        requested_softness_frames != tail.effective_softness_frames
    )
    effect_notice_header, effect_notice_lines, slope_helper_text = (
        _build_tail_effect_notice(
            is_group_tail=long_run is None or is_long_vowel_terminal,
            requested_hold_frames=requested_hold_frames,
            requested_softness_frames=requested_softness_frames,
            effective_hold_frames=tail.effective_hold_frames,
            effective_softness_frames=tail.effective_softness_frames,
            slope_enabled=slope_enabled,
        )
    )
    crossfade_notice_header, crossfade_notice_lines = _build_crossfade_notice(
        effective_plan,
        selected_base_event_index,
    )

    return SelectedEventEditorState(
        base_event_index=selected_base_event_index,
        vowel=base.vowel,
        base_identity_digest=digest,
        editor_revision=editor_revision,
        final_output_binding=final_output_binding,
        group_member_count=len(shape.real_base_event_indices),
        is_group_tail=is_tail,
        long_vowel_mode_enabled=is_long_vowel_terminal,
        requested_long_vowel_mode=requested_long_vowel_mode,
        effective_long_vowel_mode=effective_long_vowel_mode,
        long_vowel_mode_overridden=(requested_long_vowel_mode is not None),
        long_vowel_mode_notice=long_vowel_mode_notice,
        tail_controls_enabled=(
            (long_run is None or is_long_vowel_terminal)
            and effective_long_vowel_mode != LONG_VOWEL_MODE_DECAY
        ),
        manual_overlap_override_enabled=long_run is None,
        requested_manual_overlap_limit_override=bool(
            tail_adjustment is not None
            and tail_adjustment.manual_overlap_limit_override
        ),
        group_tail_base_event_index=tail.tail_base_event_index,
        base_start_frame=base.start_frame,
        base_peak_frame=base.peak_frame,
        base_end_frame=base.end_frame,
        base_peak_value=base.peak_value,
        requested_peak_value=(
            adjustment.peak_value if peak_override else base.peak_value
        ),
        requested_start_offset_frames=(
            adjustment.start_offset_frames if adjustment is not None else 0
        ),
        requested_end_offset_frames=(
            adjustment.end_offset_frames if adjustment is not None else 0
        ),
        requested_hold_frames=requested_hold_frames,
        requested_softness_frames=requested_softness_frames,
        requested_slope_ratio=requested_slope_ratio,
        effective_start_frame=effective.start_frame,
        effective_peak_frame=effective.peak_frame,
        effective_end_frame=effective.end_frame,
        effective_peak_value=effective.peak_value,
        effective_hold_frames=tail.effective_hold_frames,
        effective_softness_frames=tail.effective_softness_frames,
        available_extension_frames=tail.available_extension_frames,
        hold_is_limited=hold_is_limited,
        softness_is_limited=softness_is_limited,
        effect_notice_header=effect_notice_header,
        effect_notice_lines=effect_notice_lines,
        crossfade_notice_header=crossfade_notice_header,
        crossfade_notice_lines=crossfade_notice_lines,
        slope_helper_text=slope_helper_text,
        peak_overridden=peak_override,
        start_overridden=start_override,
        end_overridden=end_override,
        hold_overridden=hold_override,
        softness_overridden=softness_override,
        slope_overridden=slope_override,
        slope_enabled=slope_enabled,
        reset_enabled=adjustment is not None,
        start_offset_min=-base.start_frame,
        start_offset_max=base.peak_frame - base.start_frame,
        end_offset_min=base.peak_frame - base.end_frame,
        end_offset_max=resolve_manual_crossfade_end_offset_max(
            effective_plan,
            selected_base_event_index,
            source_duration_frames=source_duration_frames,
            adjustment_snapshot=requested_snapshot,
        ),
        end_offset_range_error=(
            "終了offsetが許容範囲外です。範囲内へ戻すか、制限を再解除してください。"
            if adjustment is not None
            and (
                adjustment.end_offset_frames
                < base.peak_frame - base.end_frame
                or adjustment.end_offset_frames
                > resolve_manual_crossfade_end_offset_max(
                    effective_plan,
                    selected_base_event_index,
                    source_duration_frames=source_duration_frames,
                    adjustment_snapshot=requested_snapshot,
                )
            )
            else ""
        ),
    )


def _validate_typed_value(field: str, value: object) -> float | int | str | None:
    if field == "manual_overlap_limit_override":
        if type(value) is not bool:
            raise AdjustmentContractError(
                "manual_overlap_limit_override must be bool"
            )
        return value
    if field == "long_vowel_mode":
        if value is None:
            return None
        return validate_long_vowel_mode(value)
    if value is None:
        return None
    if field in {
        "start_offset_frames",
        "end_offset_frames",
        "hold_frames",
        "softness_frames",
    }:
        if isinstance(value, bool) or not isinstance(value, int):
            raise AdjustmentContractError(f"{field} must be an int")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdjustmentContractError(f"{field} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise AdjustmentContractError(f"{field} must be finite")
    return normalized


def merge_selected_event_edit(
    snapshot: AdjustmentLayerSnapshot,
    request: SelectedEventEditRequest,
    *,
    adjustment_target_base_event_index: int | None = None,
) -> EventAdjustment:
    if snapshot.base_plan_identity.digest != request.base_identity_digest:
        raise AdjustmentContractError("edit request base identity mismatch")
    target_index = (
        request.base_event_index
        if adjustment_target_base_event_index is None
        else adjustment_target_base_event_index
    )
    if (
        isinstance(target_index, bool)
        or not isinstance(target_index, int)
        or target_index < 0
    ):
        raise AdjustmentContractError(
            "adjustment_target_base_event_index must be a non-negative int"
        )
    current = next(
        (
            item
            for item in snapshot.adjustments
            if item.base_event_index == target_index
        ),
        EventAdjustment(target_index),
    )
    value = _validate_typed_value(request.field, request.value)
    return replace(current, **{request.field: value})


def reset_selected_event_adjustment(
    snapshot: AdjustmentLayerSnapshot,
    base_event_index: int,
) -> EventAdjustment:
    if (
        isinstance(base_event_index, bool)
        or not isinstance(base_event_index, int)
        or base_event_index < 0
    ):
        raise AdjustmentContractError("base_event_index must be a non-negative int")
    return EventAdjustment(base_event_index)


def display_slope_default() -> float:
    return DEFAULT_SLOPE_RATIO


__all__ = [
    "EDITABLE_FIELDS",
    "GROUP_SHARED_FIELDS",
    "TAIL_FIELDS",
    "SelectedEventEditRequest",
    "SelectedEventEditBoundaryRequest",
    "SelectedEventEditorState",
    "build_selected_event_editor_state",
    "display_slope_default",
    "merge_selected_event_edit",
    "reset_selected_event_adjustment",
]
