from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
from typing import Any, Callable, Protocol, Sequence

from src.core.event_adjustment import (
    ADJUSTMENT_SNAPSHOT_SCHEMA,
    BASE_PLAN_IDENTITY_SCHEMA,
    DEFAULT_SLOPE_RATIO,
    AdjustmentContractError,
    AdjustmentLayerSnapshot,
    BasePlanIdentity,
    EventAdjustment,
    canonicalize_adjustment_snapshot,
    empty_adjustment_snapshot,
    LONG_VOWEL_MODE_DECAY,
    LONG_VOWEL_MODE_HOLD,
    validate_long_vowel_mode,
)
from src.core.effective_shape_diagnostics import (
    ResolverDiagnosticsCollector,
    ensure_safe_failure_metadata,
)
from src.peak_value_resolver import (
    MORPH_FRAME_OPEN_EPSILON,
    resolve_close_peak_value,
)


VMD_FPS = 30
SUPPORTED_MORPHS = ("あ", "い", "う", "え", "お")
SILENCE_POLICY_ACOUSTIC_CORE_PRECEDENCE = "acoustic_core_precedence"
NEARBY_GROUP_GAP_FRAMES = 4
BOUNDARY_RELATIONS = frozenset(
    {
        "same_vowel_same_frame",
        "silence_gap",
        "different_vowel_boundary",
        "not_applicable",
    }
)
BOUNDARY_ACTIONS = frozenset({"preserved_zero_keyframe", "not_applicable"})


class TimelinePointLike(Protocol):
    vowel: str
    time_sec: float
    duration_sec: float
    start_sec: float | None
    end_sec: float | None
    peak_value: float | None
    value: float
    vowel_token_index: int | None
    is_long_vowel_continuation: bool
    long_vowel_source_token_index: int | None


class ObservationLike(Protocol):
    event_index: int
    vowel: str
    local_peak: float | None
    previous_non_zero_event_index: int | None
    next_non_zero_event_index: int | None
    span_start_index: int | None
    span_end_index: int | None
    rms_window_times_sec: Sequence[float]
    rms_window_values: Sequence[float]
    boundary_only: bool
    boundary_frame: int | None
    boundary_point_kind: str | None


@dataclass(frozen=True)
class ShapeParameters:
    closing_hold_frames: int = 0
    closing_softness_frames: int = 0
    long_vowel_mode: str = LONG_VOWEL_MODE_HOLD

    def __post_init__(self) -> None:
        for field_name in ("closing_hold_frames", "closing_softness_frames"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
                raise AdjustmentContractError(
                    f"{field_name} must be an int between 0 and 100",
                    safe_code="shape_parameter_invalid",
                    safe_field_code=field_name,
                    safe_phase="shape_parameters",
                )
        validate_long_vowel_mode(self.long_vowel_mode)


@dataclass(frozen=True)
class BaseTimingPlanInput:
    timeline: tuple[TimelinePointLike, ...]
    observations: tuple[ObservationLike, ...] | None
    source_duration_frames: int
    shape_parameters: ShapeParameters = ShapeParameters()

    def __post_init__(self) -> None:
        object.__setattr__(self, "timeline", tuple(self.timeline))
        if self.observations is not None:
            object.__setattr__(self, "observations", tuple(self.observations))
        if (
            isinstance(self.source_duration_frames, bool)
            or not isinstance(self.source_duration_frames, int)
            or self.source_duration_frames < 0
        ):
            raise AdjustmentContractError(
                "source_duration_frames must be a non-negative int",
                safe_code="source_duration_invalid",
                safe_field_code="source_duration_frames",
                safe_phase="resolver_input",
            )
        if not isinstance(self.shape_parameters, ShapeParameters):
            raise AdjustmentContractError(
                "shape_parameters must be ShapeParameters",
                safe_code="shape_parameters_type_invalid",
                safe_field_code="shape_parameters",
                safe_phase="resolver_input",
            )


@dataclass(frozen=True)
class BaseShapeEvent:
    base_event_index: int
    vowel: str
    time_sec: float
    start_sec: float
    end_sec: float
    duration_sec: float
    start_frame: int
    peak_frame: int
    end_frame: int
    peak_value: float
    vowel_token_index: int | None = None
    is_long_vowel_continuation: bool = False
    long_vowel_source_token_index: int | None = None
    long_vowel_role: str | None = None


@dataclass(frozen=True)
class EffectiveShapeEvent:
    base_event_index: int
    vowel: str
    start_frame: int
    peak_frame: int
    end_frame: int
    peak_value: float
    vowel_token_index: int | None = None
    is_long_vowel_continuation: bool = False
    long_vowel_source_token_index: int | None = None
    long_vowel_role: str | None = None
    closing_peak_value: float | None = None
    closing_peak_used_observation: bool | None = None
    closing_peak_fallback_reason: str | None = None


@dataclass(frozen=True)
class ShapeControlPoint:
    frame_no: int
    value: float
    point_kind: str
    source_event_index: int | None = None


@dataclass(frozen=True)
class ObservationHandoff:
    span_start_index: int
    span_end_index: int
    previous_non_zero_event_index: int | None
    next_non_zero_event_index: int | None
    candidate_kind: str
    enabled: bool
    full_span_start_frame: int | None = None
    full_span_end_frame: int | None = None
    silence_core_frame_ranges: tuple[tuple[int, int], ...] = ()
    boundary_fringe_frame_ranges: tuple[tuple[int, int], ...] = ()
    silence_core_overlap: bool = False
    coverage_status: str = "unobserved"
    provenance_status: str = "unavailable"
    rejection_reason_code: str | None = None


@dataclass(frozen=True)
class EventSilenceAdmission:
    """Base-event silence decision and final projection provenance."""

    event_index: int
    vowel: str
    origin_shape_id: int | None = None
    positive_point_kinds: tuple[str, ...] = ()
    source_event_indices: tuple[int, ...] = ()
    effective_frame_range: tuple[int, int] | None = None
    boundary_only: bool = False
    boundary_frame: int | None = None
    boundary_point_kind: str | None = None
    boundary_relation: str = "not_applicable"
    boundary_action: str = "not_applicable"
    base_event_silence_core_overlap: bool = False
    positive_core_frame_ranges: tuple[tuple[int, int], ...] = ()
    long_vowel_role: str | None = None
    manual_adjustment_applied: bool = False
    enabled: bool = True
    rejection_reason_code: str | None = None
    required_zero_frame_ranges: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        if (
            isinstance(self.event_index, bool)
            or not isinstance(self.event_index, int)
            or self.event_index < 0
        ):
            raise AdjustmentContractError(
                "event_index must be a non-negative int",
                safe_code="admission_index_invalid",
                safe_field_code="event_index",
                safe_phase="silence_admission",
                event_index=self.event_index if isinstance(self.event_index, int) else None,
            )
        if self.vowel not in SUPPORTED_MORPHS:
            raise AdjustmentContractError(
                "event silence admission vowel is unsupported",
                safe_code="admission_vowel_invalid",
                safe_field_code="vowel",
                safe_phase="silence_admission",
                event_index=self.event_index if isinstance(self.event_index, int) else None,
            )
        if (
            self.origin_shape_id is not None
            and (
                isinstance(self.origin_shape_id, bool)
                or not isinstance(self.origin_shape_id, int)
                or self.origin_shape_id < 0
            )
        ):
            raise AdjustmentContractError(
                "origin_shape_id must be a non-negative int or None",
                safe_code="admission_shape_id_invalid",
                safe_field_code="origin_shape_id",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if not isinstance(self.positive_point_kinds, tuple):
            raise AdjustmentContractError(
                "positive_point_kinds must be a tuple",
                safe_code="admission_point_kind_invalid",
                safe_field_code="positive_point_kinds",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if not all(isinstance(item, str) and item for item in self.positive_point_kinds):
            raise AdjustmentContractError(
                "positive_point_kinds must contain non-empty strings",
                safe_code="admission_point_kind_invalid",
                safe_field_code="positive_point_kinds",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if not isinstance(self.source_event_indices, tuple):
            raise AdjustmentContractError(
                "source_event_indices must be a tuple",
                safe_code="admission_source_indices_invalid",
                safe_field_code="source_event_indices",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in self.source_event_indices
        ):
            raise AdjustmentContractError(
                "source_event_indices must contain non-negative ints",
                safe_code="admission_source_indices_invalid",
                safe_field_code="source_event_indices",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        for field_name, ranges in (
            ("positive_core_frame_ranges", self.positive_core_frame_ranges),
            ("required_zero_frame_ranges", self.required_zero_frame_ranges),
        ):
            if not isinstance(ranges, tuple):
                raise AdjustmentContractError(
                    f"{field_name} must be a tuple",
                    safe_code="admission_range_invalid",
                    safe_field_code=field_name,
                    safe_phase="silence_admission",
                    event_index=self.event_index,
                )
            for frame_range in ranges:
                if (
                    not isinstance(frame_range, tuple)
                    or len(frame_range) != 2
                    or any(
                        isinstance(frame_no, bool) or not isinstance(frame_no, int)
                        for frame_no in frame_range
                    )
                    or frame_range[1] <= frame_range[0]
                ):
                    raise AdjustmentContractError(
                        f"{field_name} must contain half-open integer ranges",
                        safe_code="admission_range_invalid",
                        safe_field_code=field_name,
                        safe_phase="silence_admission",
                        event_index=self.event_index,
                    )
        if self.effective_frame_range is not None:
            if (
                not isinstance(self.effective_frame_range, tuple)
                or len(self.effective_frame_range) != 2
                or any(
                    isinstance(frame_no, bool) or not isinstance(frame_no, int)
                    for frame_no in self.effective_frame_range
                )
                or self.effective_frame_range[1] <= self.effective_frame_range[0]
            ):
                raise AdjustmentContractError(
                    "effective_frame_range must be a half-open integer range or None",
                    safe_code="admission_range_invalid",
                    safe_field_code="effective_frame_range",
                    safe_phase="silence_admission",
                    event_index=self.event_index,
                )
        if not isinstance(self.boundary_only, bool):
            raise AdjustmentContractError(
                "boundary_only must be bool",
                safe_code="admission_flag_invalid",
                safe_field_code="boundary_only",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.boundary_frame is not None and (
            isinstance(self.boundary_frame, bool)
            or not isinstance(self.boundary_frame, int)
            or self.boundary_frame < 0
        ):
            raise AdjustmentContractError(
                "boundary_frame must be a non-negative int or None",
                safe_code="admission_boundary_invalid",
                safe_field_code="boundary_frame",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.boundary_point_kind not in {None, "end_zero"}:
            raise AdjustmentContractError(
                "unsupported boundary point kind",
                safe_code="admission_boundary_invalid",
                safe_field_code="boundary_point_kind",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.boundary_relation not in BOUNDARY_RELATIONS:
            raise AdjustmentContractError(
                "unsupported boundary relation",
                safe_code="admission_boundary_invalid",
                safe_field_code="boundary_relation",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.boundary_action not in BOUNDARY_ACTIONS:
            raise AdjustmentContractError(
                "unsupported boundary action",
                safe_code="admission_boundary_invalid",
                safe_field_code="boundary_action",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.boundary_only:
            if (
                self.effective_frame_range is not None
                or self.boundary_frame is None
                or self.boundary_point_kind != "end_zero"
                or self.positive_point_kinds
                or self.positive_core_frame_ranges
                or self.boundary_relation == "not_applicable"
                or self.boundary_action != "preserved_zero_keyframe"
            ):
                raise AdjustmentContractError(
                    "boundary-only admission fields are inconsistent",
                    safe_code="admission_boundary_invalid",
                    safe_field_code="boundary_only",
                    safe_phase="silence_admission",
                    event_index=self.event_index,
                )
        elif any(
            value is not None
            for value in (self.boundary_frame, self.boundary_point_kind)
        ) or self.boundary_relation != "not_applicable" or self.boundary_action != "not_applicable":
            raise AdjustmentContractError(
                "non-boundary admission contains boundary fields",
                safe_code="admission_boundary_invalid",
                safe_field_code="boundary_only",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.long_vowel_role not in {
            None,
            "long_source",
            "intermediate_continuation",
            "terminal_continuation",
        }:
            raise AdjustmentContractError(
                "unsupported long_vowel_role",
                safe_code="admission_role_invalid",
                safe_field_code="long_vowel_role",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        for field_name in (
            "base_event_silence_core_overlap",
            "manual_adjustment_applied",
            "enabled",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise AdjustmentContractError(
                    f"{field_name} must be bool",
                    safe_code="admission_flag_invalid",
                    safe_field_code=field_name,
                    safe_phase="silence_admission",
                    event_index=self.event_index,
                )
        if self.rejection_reason_code not in {
            None,
            "base_event_overlaps_silence_core",
            "required_zero_missing",
            "admission_boundary_invalid",
        }:
            raise AdjustmentContractError(
                "unsupported event silence rejection reason",
                safe_code="admission_rejection_invalid",
                safe_field_code="rejection_reason_code",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if not self.enabled and self.rejection_reason_code is None:
            raise AdjustmentContractError(
                "disabled event silence admission must have a rejection reason",
                safe_code="admission_enabled_reason_conflict",
                safe_field_code="rejection_reason_code",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )
        if self.enabled and self.rejection_reason_code is not None:
            raise AdjustmentContractError(
                "enabled event silence admission cannot have a rejection reason",
                safe_code="admission_enabled_reason_conflict",
                safe_field_code="rejection_reason_code",
                safe_phase="silence_admission",
                event_index=self.event_index,
            )


@dataclass(frozen=True)
class ResolvedTailParameters:
    tail_base_event_index: int
    requested_hold_frames: int
    requested_softness_frames: int
    effective_hold_frames: int
    effective_softness_frames: int
    available_extension_frames: int | None
    slope_ratio: float
    has_slope_midpoint: bool


@dataclass(frozen=True)
class EffectiveLongVowelRun:
    source_base_event_index: int
    continuation_base_event_indices: tuple[int, ...]
    terminal_base_event_index: int
    vowel: str
    resolved_mode: str
    source_peak_frame: int
    terminal_end_frame: int
    source_peak_value: float


@dataclass(frozen=True)
class EffectiveShape:
    vowel: str
    shape_kind: str
    control_points: tuple[ShapeControlPoint, ...]
    real_base_event_indices: tuple[int, ...]
    internal_shape_source_tokens: tuple[int, ...] = ()
    event_ranges: tuple[tuple[int, int], ...] = ()
    fallback_reason: str | None = None
    protection_mode: str | None = None
    resolved_tail: ResolvedTailParameters | None = None
    silence_core_frame_ranges: tuple[tuple[int, int], ...] = ()

    @property
    def start_frame(self) -> int:
        return self.control_points[0].frame_no

    @property
    def end_frame(self) -> int:
        return self.control_points[-1].frame_no


@dataclass(frozen=True)
class NormalizationContract:
    allowed_non_zero_ranges: tuple[tuple[str, int, int], ...] = ()
    required_zero_frames: tuple[tuple[str, int], ...] = ()
    protected_event_ranges: tuple[tuple[str, int, int], ...] = ()


@dataclass(frozen=True)
class ManualCrossfadeKeyframeNotice:
    frame_no: int
    vowel: str
    value: float


@dataclass(frozen=True)
class ManualCrossfadeMetadata:
    source_base_event_index: int
    target_base_event_index: int
    source_vowel: str
    target_vowel: str
    overlap_start_frame: int
    overlap_end_frame: int
    high_target_keyframes: tuple[ManualCrossfadeKeyframeNotice, ...] = ()


@dataclass(frozen=True)
class EffectiveShapePlan:
    base_plan_identity: BasePlanIdentity
    canonical_adjustment_snapshot: AdjustmentLayerSnapshot
    base_events: tuple[BaseShapeEvent, ...]
    effective_events: tuple[EffectiveShapeEvent, ...]
    shapes: tuple[EffectiveShape, ...]
    observation_handoffs: tuple[ObservationHandoff, ...]
    normalization_contract: NormalizationContract
    event_silence_admissions: tuple[EventSilenceAdmission, ...] = ()
    manual_crossfades: tuple[ManualCrossfadeMetadata, ...] = ()
    long_vowel_runs: tuple[EffectiveLongVowelRun, ...] = ()
    # Resolver provenance.  This is intentionally additive and is not part of
    # the MS21 save-state fingerprint payload.
    shape_parameters: ShapeParameters = ShapeParameters()
    silence_policy: str = SILENCE_POLICY_ACOUSTIC_CORE_PRECEDENCE
    silence_core_frame_ranges: tuple[tuple[int, int], ...] = ()
    silence_clip_records: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class _ManualCrossfadeContext:
    source_shape_index: int
    target_shape_index: int
    source_base_event_index: int
    target_base_event_index: int
    target_open_start_frame: int
    target_open_end_frame: int
    crossfade_limit_frame: int


@dataclass(frozen=True)
class AdjustmentUpdateResult:
    canonical_snapshot: AdjustmentLayerSnapshot
    removed_tail_override_event_indices: tuple[int, ...]
    removed_slope_override_event_indices: tuple[int, ...]
    effective_plan: EffectiveShapePlan


def source_duration_frames_from_seconds(duration_sec: object) -> int:
    if isinstance(duration_sec, bool) or not isinstance(duration_sec, (int, float)):
        raise AdjustmentContractError(
            "duration_sec must be a finite number",
            safe_code="numeric_type_invalid",
            safe_field_code="duration_sec",
            safe_phase="base_events",
        )
    normalized = float(duration_sec)
    if not math.isfinite(normalized) or normalized < 0.0:
        raise AdjustmentContractError(
            "duration_sec must be finite and >= 0",
            safe_code="numeric_negative" if normalized < 0.0 else "numeric_non_finite",
            safe_field_code="duration_sec",
            safe_phase="base_events",
        )
    return int(round(normalized * VMD_FPS))


def _finite_number(
    value: object,
    field_name: str,
    *,
    non_negative: bool = False,
    safe_phase: str = "base_events",
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdjustmentContractError(
            f"{field_name} must be a finite number",
            safe_code="numeric_type_invalid",
            safe_field_code=field_name,
            safe_phase=safe_phase,
        )
    normalized = float(value)
    if not math.isfinite(normalized) or (non_negative and normalized < 0.0):
        suffix = " and >= 0" if non_negative else ""
        raise AdjustmentContractError(
            f"{field_name} must be finite{suffix}",
            safe_code="numeric_negative" if non_negative and normalized < 0.0 else "numeric_non_finite",
            safe_field_code=field_name,
            safe_phase=safe_phase,
        )
    return normalized


def _canonical_float(
    value: object,
    field_name: str,
    *,
    non_negative: bool = False,
    safe_phase: str = "base_events",
) -> str:
    return _finite_number(
        value,
        field_name,
        non_negative=non_negative,
        safe_phase=safe_phase,
    ).hex()


def _point_bounds(point: TimelinePointLike) -> tuple[float, float, float, float, float]:
    time_sec = _finite_number(getattr(point, "time_sec", None), "time_sec", non_negative=True)
    duration_sec = _finite_number(
        getattr(point, "duration_sec", 0.0), "duration_sec", non_negative=True
    )
    raw_start = getattr(point, "start_sec", None)
    raw_end = getattr(point, "end_sec", None)
    if raw_start is None and raw_end is None:
        half = duration_sec * 0.5
        start_sec = time_sec - half if duration_sec > 0.0 else time_sec
        end_sec = time_sec + half if duration_sec > 0.0 else time_sec
    elif raw_start is None:
        end_sec = _finite_number(raw_end, "end_sec", non_negative=True)
        start_sec = end_sec - duration_sec if duration_sec > 0.0 else min(time_sec, end_sec)
    elif raw_end is None:
        start_sec = _finite_number(raw_start, "start_sec", non_negative=True)
        end_sec = start_sec + duration_sec if duration_sec > 0.0 else max(time_sec, start_sec)
    else:
        start_sec = _finite_number(raw_start, "start_sec", non_negative=True)
        end_sec = _finite_number(raw_end, "end_sec", non_negative=True)
    if start_sec < 0.0 or not start_sec <= time_sec <= end_sec:
        raise AdjustmentContractError(
            "timeline point must satisfy 0 <= start <= time <= end",
            safe_code="timeline_bounds_invalid",
            safe_field_code="timeline_bounds",
            safe_phase="base_events",
        )
    peak_raw = getattr(point, "peak_value", None)
    if peak_raw is None:
        peak_raw = getattr(point, "value", None)
    peak_value = _finite_number(peak_raw, "peak_value", non_negative=True)
    return time_sec, start_sec, end_sec, end_sec - start_sec, peak_value


def _timeline_long_metadata(
    timeline: Sequence[TimelinePointLike],
) -> tuple[tuple[int | None, bool, int | None], ...]:
    metadata: list[tuple[int | None, bool, int | None]] = []
    explicit_count = 0
    for point in timeline:
        token_index = getattr(point, "vowel_token_index", None)
        continuation = getattr(point, "is_long_vowel_continuation", False)
        source = getattr(point, "long_vowel_source_token_index", None)
        if token_index is not None:
            explicit_count += 1
        if token_index is not None and (
            isinstance(token_index, bool) or not isinstance(token_index, int) or token_index < 0
        ):
            raise AdjustmentContractError(
                "vowel_token_index must be a non-negative int",
                safe_code="long_metadata_type_invalid",
                safe_field_code="vowel_token_index",
                safe_phase="timeline_metadata",
            )
        if not isinstance(continuation, bool):
            raise AdjustmentContractError(
                "is_long_vowel_continuation must be bool",
                safe_code="long_metadata_type_invalid",
                safe_field_code="is_long_vowel_continuation",
                safe_phase="timeline_metadata",
            )
        if source is not None and (
            isinstance(source, bool) or not isinstance(source, int) or source < 0
        ):
            raise AdjustmentContractError(
                "long_vowel_source_token_index must be a non-negative int",
                safe_code="long_metadata_type_invalid",
                safe_field_code="long_vowel_source_token_index",
                safe_phase="timeline_metadata",
            )
        if continuation and (token_index is None or source is None or source >= token_index):
            raise AdjustmentContractError(
                "long-vowel continuation source must point backwards",
                safe_code="long_source_order_invalid",
                safe_field_code="long_vowel_source_token_index",
                safe_phase="timeline_metadata",
            )
        if not continuation and source is not None:
            raise AdjustmentContractError(
                "non-continuation timeline point cannot carry a source",
                safe_code="long_source_unexpected",
                safe_field_code="long_vowel_source_token_index",
                safe_phase="timeline_metadata",
            )
        metadata.append((token_index, continuation, source))
    if explicit_count not in (0, len(timeline)):
        raise AdjustmentContractError(
            "timeline long-vowel metadata must be all explicit or all legacy",
            safe_code="long_metadata_mixed",
            safe_field_code="long_metadata",
            safe_phase="timeline_metadata",
        )
    if explicit_count == 0:
        return tuple((None, False, None) for _ in timeline)
    indexes = tuple(item[0] for item in metadata)
    if indexes != tuple(range(len(timeline))):
        raise AdjustmentContractError(
            "timeline vowel token indexes must be contiguous",
            safe_code="long_token_order_invalid",
            safe_field_code="vowel_token_index",
            safe_phase="timeline_metadata",
        )
    active_source: int | None = None
    for index, (_, continuation, source) in enumerate(metadata):
        if continuation:
            if source != active_source:
                raise AdjustmentContractError(
                    "long-vowel continuation must reference the active source",
                    safe_code="long_active_source_mismatch",
                    safe_field_code="long_vowel_source_token_index",
                    safe_phase="timeline_metadata",
                )
            source_vowel = getattr(timeline[source], "vowel", None)
            if source_vowel != getattr(timeline[index], "vowel", None):
                raise AdjustmentContractError(
                    "long-vowel continuation vowel must match its source",
                    safe_code="long_source_vowel_mismatch",
                    safe_field_code="vowel",
                    safe_phase="timeline_metadata",
                )
        else:
            active_source = index
    return tuple(metadata)


def _base_events(base_input: BaseTimingPlanInput) -> tuple[BaseShapeEvent, ...]:
    events: list[BaseShapeEvent] = []
    metadata = _timeline_long_metadata(base_input.timeline)
    for index, point in enumerate(base_input.timeline):
        vowel = getattr(point, "vowel", None)
        if vowel not in SUPPORTED_MORPHS:
            raise AdjustmentContractError(
                f"unsupported vowel: {vowel}",
                safe_code="vowel_unsupported",
                safe_field_code="vowel",
                safe_phase="base_events",
                event_index=index,
                event_role="subject",
            )
        time_sec, start_sec, end_sec, duration_sec, peak_value = _point_bounds(point)
        start_frame = int(round(start_sec * VMD_FPS))
        peak_frame = int(round(time_sec * VMD_FPS))
        end_frame = int(round(end_sec * VMD_FPS))
        if not 0 <= start_frame <= peak_frame <= end_frame <= base_input.source_duration_frames:
            raise AdjustmentContractError(
                f"event {index} must satisfy 0 <= start <= peak <= end <= source duration",
                safe_code="base_frame_order_invalid",
                safe_field_code="frame_order",
                safe_phase="base_events",
                event_index=index,
                event_role="subject",
                safe_details={
                    "start_frame": start_frame,
                    "peak_frame": peak_frame,
                    "end_frame": end_frame,
                },
            )
        events.append(
            BaseShapeEvent(
                base_event_index=index,
                vowel=vowel,
                time_sec=time_sec,
                start_sec=start_sec,
                end_sec=end_sec,
                duration_sec=duration_sec,
                start_frame=start_frame,
                peak_frame=peak_frame,
                end_frame=end_frame,
                peak_value=peak_value,
                vowel_token_index=metadata[index][0],
                is_long_vowel_continuation=metadata[index][1],
                long_vowel_source_token_index=metadata[index][2],
            )
        )
    by_source: dict[int, list[int]] = {}
    for event in events:
        if event.is_long_vowel_continuation and event.long_vowel_source_token_index is not None:
            by_source.setdefault(event.long_vowel_source_token_index, []).append(event.base_event_index)
    return tuple(
        replace(
            event,
            long_vowel_role=(
                "terminal_continuation"
                if event.is_long_vowel_continuation
                and event.base_event_index == by_source.get(event.long_vowel_source_token_index, [None])[-1]
                else "intermediate_continuation"
                if event.is_long_vowel_continuation
                else "long_source"
                if event.base_event_index in by_source
                else None
            ),
        )
        for event in events
    )


def _long_vowel_runs(events: tuple[BaseShapeEvent, ...], shape_parameters: ShapeParameters) -> tuple[EffectiveLongVowelRun, ...]:
    by_source: dict[int, list[BaseShapeEvent]] = {}
    for event in events:
        if event.is_long_vowel_continuation and event.long_vowel_source_token_index is not None:
            by_source.setdefault(event.long_vowel_source_token_index, []).append(event)
    runs: list[EffectiveLongVowelRun] = []
    for source_index, continuations in sorted(by_source.items()):
        source = next((event for event in events if event.base_event_index == source_index), None)
        if source is None or not continuations:
            raise AdjustmentContractError(
                "long-vowel source is missing",
                safe_code="long_source_missing",
                safe_field_code="long_vowel_source_token_index",
                safe_phase="long_runs",
                source_event_index=source_index,
                source_event_role="source",
            )
        terminal = continuations[-1]
        runs.append(
            EffectiveLongVowelRun(
                source_base_event_index=source.base_event_index,
                continuation_base_event_indices=tuple(event.base_event_index for event in continuations),
                terminal_base_event_index=terminal.base_event_index,
                vowel=source.vowel,
                resolved_mode=shape_parameters.long_vowel_mode,
                source_peak_frame=source.peak_frame,
                terminal_end_frame=terminal.end_frame,
                source_peak_value=source.peak_value,
            )
        )
    return tuple(runs)


_OBSERVATION_FLAGS = (
    "is_bridgeable_micro_gap_candidate",
    "is_bridgeable_same_vowel_micro_gap_candidate",
    "is_same_vowel_burst_candidate",
    "is_bridgeable_cross_vowel_transition_candidate",
    "is_cross_vowel_zero_run_continuity_floor_candidate",
)
_OBSERVATION_INDEX_FIELDS = (
    "previous_non_zero_event_index",
    "next_non_zero_event_index",
    "span_start_index",
    "span_end_index",
)


def _observation_contract_payload(observation: object, *, index: int) -> tuple[object, ...]:
    frame_values: list[int | None] = []
    for field_name in ("full_span_start_frame", "full_span_end_frame"):
        value = getattr(observation, field_name, None)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise AdjustmentContractError(
                f"invalid observation {field_name}",
                safe_code="observation_frame_invalid",
                safe_field_code=field_name,
                safe_phase="observation_contract",
                event_index=index,
            )
        frame_values.append(value)

    range_values: list[tuple[tuple[int, int], ...]] = []
    for field_name in ("silence_core_frame_ranges", "boundary_fringe_frame_ranges"):
        raw_ranges = getattr(observation, field_name, ()) or ()
        normalized_ranges: list[tuple[int, int]] = []
        for raw_range in raw_ranges:
            if (
                not isinstance(raw_range, (tuple, list))
                or len(raw_range) != 2
                or any(isinstance(value, bool) or not isinstance(value, int) for value in raw_range)
                or raw_range[0] < 0
                or raw_range[1] <= raw_range[0]
            ):
                raise AdjustmentContractError(
                    f"invalid observation {field_name}[{index}]",
                    safe_code="observation_range_invalid",
                    safe_field_code=field_name,
                    safe_phase="observation_contract",
                    event_index=index,
                )
            normalized_ranges.append((raw_range[0], raw_range[1]))
        range_values.append(tuple(normalized_ranges))

    overlap = getattr(observation, "silence_core_overlap", False)
    if not isinstance(overlap, bool):
        raise AdjustmentContractError(
            "observation silence_core_overlap must be bool",
            safe_code="observation_overlap_invalid",
            safe_field_code="silence_core_overlap",
            safe_phase="observation_contract",
            event_index=index,
        )

    coverage_status = getattr(observation, "coverage_status", "unobserved")
    if coverage_status not in {"complete", "partial", "unobserved"}:
        raise AdjustmentContractError(
            "invalid observation coverage_status",
            safe_code="observation_coverage_invalid",
            safe_field_code="coverage_status",
            safe_phase="observation_contract",
            event_index=index,
        )
    provenance_status = getattr(observation, "provenance_status", "unavailable")
    if provenance_status not in {"complete", "partial", "unavailable"}:
        raise AdjustmentContractError(
            "invalid observation provenance_status",
            safe_code="observation_provenance_invalid",
            safe_field_code="provenance_status",
            safe_phase="observation_contract",
            event_index=index,
        )
    rejection_reason = getattr(observation, "bridge_rejection_reason_code", None)
    if rejection_reason is not None and not isinstance(rejection_reason, str):
        raise AdjustmentContractError(
            "observation bridge_rejection_reason_code must be str or None",
            safe_code="observation_rejection_invalid",
            safe_field_code="bridge_rejection_reason_code",
            safe_phase="observation_contract",
            event_index=index,
        )

    return (
        frame_values[0],
        frame_values[1],
        range_values[0],
        range_values[1],
        overlap,
        coverage_status,
        provenance_status,
        rejection_reason,
    )


def _validate_observations(
    base_input: BaseTimingPlanInput,
) -> tuple[tuple[object, ...], ...] | None:
    observations = base_input.observations
    if observations is None:
        return None
    if len(observations) != len(base_input.timeline):
        raise AdjustmentContractError(
            "observations must match timeline length",
            safe_code="observation_count_mismatch",
            safe_field_code="observations",
            safe_phase="observations",
            safe_details={
                "expected_count": len(base_input.timeline),
                "observed_count": len(observations),
            },
        )
    payload: list[tuple[object, ...]] = []
    count = len(base_input.timeline)
    for index, observation in enumerate(observations):
        event_index = getattr(observation, "event_index", None)
        if isinstance(event_index, bool) or not isinstance(event_index, int) or event_index != index:
            raise AdjustmentContractError(
                "observation event_index must match base_event_index",
                safe_code="observation_index_mismatch",
                safe_field_code="event_index",
                safe_phase="observations",
                event_index=index,
            )
        point_vowel = getattr(base_input.timeline[index], "vowel", None)
        observation_vowel = getattr(observation, "vowel", point_vowel)
        if observation_vowel != point_vowel:
            raise AdjustmentContractError(
                "observation vowel must match timeline vowel",
                safe_code="observation_vowel_mismatch",
                safe_field_code="vowel",
                safe_phase="observations",
                event_index=index,
            )

        refs: dict[str, int | None] = {}
        for field_name in _OBSERVATION_INDEX_FIELDS:
            value = getattr(observation, field_name, None)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value < count
            ):
                raise AdjustmentContractError(
                    f"invalid observation {field_name}",
                    safe_code="observation_reference_invalid",
                    safe_field_code=field_name,
                    safe_phase="observations",
                    event_index=index,
                )
            refs[field_name] = value

        span_start = refs["span_start_index"] if refs["span_start_index"] is not None else index
        span_end = refs["span_end_index"] if refs["span_end_index"] is not None else index
        if not span_start <= index <= span_end:
            raise AdjustmentContractError(
                "observation span must contain event_index",
                safe_code="observation_span_invalid",
                safe_field_code="span_indices",
                safe_phase="observations",
                event_index=index,
            )
        flags: list[bool] = []
        for field_name in _OBSERVATION_FLAGS:
            value = getattr(observation, field_name, False)
            if not isinstance(value, bool):
                raise AdjustmentContractError(
                    f"observation {field_name} must be bool",
                    safe_code="observation_flag_invalid",
                    safe_field_code=field_name,
                    safe_phase="observations",
                    event_index=index,
                )
            flags.append(value)
        if any(flags) and (
            refs["previous_non_zero_event_index"] is not None
            or refs["next_non_zero_event_index"] is not None
        ):
            previous_index = refs["previous_non_zero_event_index"]
            next_index = refs["next_non_zero_event_index"]
            if (
                previous_index is None
                or next_index is None
                or not previous_index < span_start <= span_end < next_index
            ):
                raise AdjustmentContractError(
                    "candidate observation bracketing order is invalid",
                    safe_code="observation_bracketing_invalid",
                    safe_field_code="bracketing",
                    safe_phase="observations",
                    event_index=index,
                )

        times = tuple(
            _canonical_float(
                value,
                "rms_window_times_sec",
                non_negative=True,
                safe_phase="observations",
            )
            for value in getattr(observation, "rms_window_times_sec", ())
        )
        values = tuple(
            _canonical_float(
                value,
                "rms_window_values",
                non_negative=True,
                safe_phase="observations",
            )
            for value in getattr(observation, "rms_window_values", ())
        )
        if len(times) != len(values):
            raise AdjustmentContractError(
                "observation RMS arrays must have equal length",
                safe_code="observation_rms_length_mismatch",
                safe_field_code="rms_window_values",
                safe_phase="observations",
                event_index=index,
            )
        local_peak = getattr(observation, "local_peak", None)
        local_peak_payload = (
            None
            if local_peak is None
            else _canonical_float(
                local_peak,
                "local_peak",
                non_negative=True,
                safe_phase="observations",
            )
        )
        payload.append(
            (
                event_index,
                observation_vowel,
                tuple(flags),
                refs["previous_non_zero_event_index"],
                refs["next_non_zero_event_index"],
                refs["span_start_index"],
                refs["span_end_index"],
                local_peak_payload,
                times,
                values,
                *_observation_contract_payload(observation, index=index),
            )
        )
    return tuple(payload)


def build_base_plan_identity(base_input: BaseTimingPlanInput) -> BasePlanIdentity:
    events = _base_events(base_input)
    observation_payload = _validate_observations(base_input)
    timeline_payload = tuple(
        (
            event.base_event_index,
            event.vowel,
            event.time_sec.hex(),
            event.start_sec.hex(),
            event.end_sec.hex(),
            event.duration_sec.hex(),
            event.peak_value.hex(),
            event.vowel_token_index,
            event.is_long_vowel_continuation,
            event.long_vowel_source_token_index,
        )
        for event in events
    )
    payload: tuple[object, ...] = (
        BASE_PLAN_IDENTITY_SCHEMA,
        timeline_payload,
        "none" if observation_payload is None else "present",
        () if observation_payload is None else observation_payload,
        base_input.source_duration_frames,
    )
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return BasePlanIdentity(
        schema_version=BASE_PLAN_IDENTITY_SCHEMA,
        canonical_payload=payload,
        digest=hashlib.sha256(encoded).hexdigest(),
    )


def _canonical_snapshot(
    base_input: BaseTimingPlanInput,
    identity: BasePlanIdentity,
    requested: AdjustmentLayerSnapshot | Sequence[EventAdjustment] | None,
    events: tuple[BaseShapeEvent, ...],
) -> AdjustmentLayerSnapshot:
    if requested is None:
        return empty_adjustment_snapshot(identity)
    if isinstance(requested, AdjustmentLayerSnapshot):
        if requested.base_plan_identity != identity:
            raise AdjustmentContractError(
                "adjustment snapshot base identity mismatch",
                safe_code="snapshot_identity_mismatch",
                safe_field_code="base_plan_identity",
                safe_phase="snapshot_canonicalize",
            )
        values: Sequence[EventAdjustment] = requested.adjustments
    else:
        values = requested
    return canonicalize_adjustment_snapshot(
        identity,
        values,
        base_peak_values=tuple(event.peak_value for event in events),
        closing_hold_frames=base_input.shape_parameters.closing_hold_frames,
        closing_softness_frames=base_input.shape_parameters.closing_softness_frames,
    )


def _validate_long_adjustment_ownership(
    events: tuple[BaseShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
) -> None:
    by_index = {event.base_event_index: event for event in events}
    for item in snapshot.adjustments:
        event = by_index.get(item.base_event_index)
        if event is None:
            raise AdjustmentContractError(
                "stale adjustment index",
                safe_code="adjustment_index_out_of_range",
                safe_field_code="base_event_index",
                safe_phase="adjustment_ownership",
                event_index=item.base_event_index,
            )
        if event.long_vowel_role is not None and item.manual_overlap_limit_override:
            raise AdjustmentContractError(
                "manual overlap override is not supported for long-vowel runs",
                safe_code="long_adjustment_ownership_invalid",
                safe_field_code="manual_overlap_limit_override",
                safe_phase="adjustment_ownership",
                event_index=event.base_event_index,
            )
        if event.long_vowel_role is None:
            if item.long_vowel_mode is not None:
                raise AdjustmentContractError(
                    "long_vowel_mode is valid only on a terminal continuation",
                    safe_code="long_role_invalid",
                    safe_field_code="long_vowel_role",
                    safe_phase="adjustment_ownership",
                    event_index=event.base_event_index,
                )
            continue
        if event.long_vowel_role == "long_source":
            if item.end_offset_frames != 0 or item.hold_frames is not None or item.softness_frames is not None or item.slope_ratio is not None or item.long_vowel_mode is not None:
                raise AdjustmentContractError(
                    "long source adjustment owns only peak and start",
                    safe_code="long_adjustment_ownership_invalid",
                    safe_field_code="adjustment_ownership",
                    safe_phase="adjustment_ownership",
                    event_index=event.base_event_index,
                )
        elif event.long_vowel_role == "intermediate_continuation":
            if not item.is_empty:
                raise AdjustmentContractError(
                    "intermediate long-vowel continuation is not adjustable",
                    safe_code="long_adjustment_ownership_invalid",
                    safe_field_code="adjustment_ownership",
                    safe_phase="adjustment_ownership",
                    event_index=event.base_event_index,
                )
        elif event.long_vowel_role == "terminal_continuation":
            if item.peak_value is not None or item.start_offset_frames != 0:
                raise AdjustmentContractError(
                    "terminal continuation adjustment owns only end and tail",
                    safe_code="long_adjustment_ownership_invalid",
                    safe_field_code="adjustment_ownership",
                    safe_phase="adjustment_ownership",
                    event_index=event.base_event_index,
                )
        else:
            raise AdjustmentContractError(
                "unknown long-vowel role",
                safe_code="long_role_invalid",
                safe_field_code="long_vowel_role",
                safe_phase="adjustment_ownership",
                event_index=event.base_event_index,
            )


def _resolved_long_mode(
    run: EffectiveLongVowelRun,
    snapshot: AdjustmentLayerSnapshot,
    shape_parameters: ShapeParameters,
) -> str:
    terminal = next(
        (item for item in snapshot.adjustments if item.base_event_index == run.terminal_base_event_index),
        None,
    )
    if terminal is not None and terminal.long_vowel_mode is not None:
        return validate_long_vowel_mode(terminal.long_vowel_mode)
    return validate_long_vowel_mode(shape_parameters.long_vowel_mode)


def _apply_event_adjustments(
    base_input: BaseTimingPlanInput,
    events: tuple[BaseShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
) -> tuple[EffectiveShapeEvent, ...]:
    by_index = {item.base_event_index: item for item in snapshot.adjustments}
    effective: list[EffectiveShapeEvent] = []
    for event in events:
        adjustment = by_index.get(event.base_event_index)
        start_frame = event.start_frame
        end_frame = event.end_frame
        peak_value = event.peak_value
        if adjustment is not None:
            start_frame += adjustment.start_offset_frames
            end_frame += adjustment.end_offset_frames
            if adjustment.peak_value is not None:
                peak_value = adjustment.peak_value
        if not 0 <= start_frame <= event.peak_frame <= end_frame <= base_input.source_duration_frames:
            raise AdjustmentContractError(
                f"adjustment for event {event.base_event_index} creates invalid frame ordering"
            )
        effective.append(
            EffectiveShapeEvent(
                base_event_index=event.base_event_index,
                vowel=event.vowel,
                start_frame=start_frame,
                peak_frame=event.peak_frame,
                end_frame=end_frame,
                peak_value=peak_value,
                vowel_token_index=event.vowel_token_index,
                is_long_vowel_continuation=event.is_long_vowel_continuation,
                long_vowel_source_token_index=event.long_vowel_source_token_index,
                long_vowel_role=event.long_vowel_role,
            )
        )
    return tuple(sorted(effective, key=lambda item: (item.peak_frame, item.base_event_index)))


def _resolve_close_peak_values(
    base_input: BaseTimingPlanInput,
    events: tuple[EffectiveShapeEvent, ...],
) -> tuple[EffectiveShapeEvent, ...]:
    observations = base_input.observations
    resolved: list[EffectiveShapeEvent] = []
    for event in events:
        peak_start_frame, peak_end_frame = _single_event_peak_frames(
            event.start_frame,
            event.peak_frame,
            event.end_frame,
        )
        closing_peak_value = None
        closing_peak_used_observation = None
        closing_peak_fallback_reason = None
        if peak_end_frame > peak_start_frame and peak_end_frame < event.end_frame:
            observation = (
                None
                if observations is None
                else observations[event.base_event_index]
            )
            resolution = resolve_close_peak_value(
                observation,
                peak_end_frame=peak_end_frame,
                opening_peak=event.peak_value,
                frame_rate=VMD_FPS,
            )
            closing_peak_value = resolution.value
            closing_peak_used_observation = resolution.used_observation
            closing_peak_fallback_reason = resolution.fallback_reason
        resolved.append(
            replace(
                event,
                closing_peak_value=closing_peak_value,
                closing_peak_used_observation=closing_peak_used_observation,
                closing_peak_fallback_reason=closing_peak_fallback_reason,
            )
        )
    return tuple(resolved)


def _candidate_handoffs(
    base_input: BaseTimingPlanInput,
    adjusted_indices: set[int],
    *,
    excluded_indices: set[int] | None = None,
) -> tuple[ObservationHandoff, ...]:
    if base_input.observations is None:
        return ()
    seen: set[tuple[int, int, str]] = set()
    result: list[ObservationHandoff] = []
    for index, observation in enumerate(base_input.observations):
        span_start = getattr(observation, "span_start_index", None)
        span_end = getattr(observation, "span_end_index", None)
        span_start = index if span_start is None else span_start
        span_end = index if span_end is None else span_end
        if getattr(observation, "is_same_vowel_burst_candidate", False) or getattr(
            observation, "is_bridgeable_same_vowel_micro_gap_candidate", False
        ):
            kind = "same_vowel_span"
        elif getattr(observation, "is_bridgeable_cross_vowel_transition_candidate", False) or getattr(
            observation, "is_cross_vowel_zero_run_continuity_floor_candidate", False
        ) or getattr(observation, "bridge_rejection_reason_code", None) in {
            "cross_vowel_handoff_crosses_silence_core",
            "cross_vowel_handoff_exceeds_full_span_limit",
            "provenance_unavailable",
        }:
            kind = "cross_vowel_transition"
        elif getattr(observation, "is_bridgeable_micro_gap_candidate", False):
            kind = "micro_gap"
        else:
            continue
        key = (span_start, span_end, kind)
        if key in seen:
            continue
        seen.add(key)
        excluded = excluded_indices or set()
        touched = set(range(span_start, span_end + 1))
        previous_index = getattr(observation, "previous_non_zero_event_index", None)
        next_index = getattr(observation, "next_non_zero_event_index", None)
        touches_long = bool(touched & excluded) or previous_index in excluded or next_index in excluded
        has_contract_metadata = any(
            hasattr(observation, field_name)
            for field_name in (
                "silence_core_overlap",
                "coverage_status",
                "provenance_status",
            )
        )
        silence_core_overlap = bool(getattr(observation, "silence_core_overlap", False))
        coverage_status = str(getattr(observation, "coverage_status", "unobserved"))
        provenance_status = str(getattr(observation, "provenance_status", "unavailable"))
        rejection_reason_code = getattr(observation, "bridge_rejection_reason_code", None)
        contract_rejected = (
            kind == "cross_vowel_transition"
            and (
                silence_core_overlap
                or rejection_reason_code is not None
                or (
                    has_contract_metadata
                    and (coverage_status != "complete" or provenance_status != "complete")
                )
            )
        )
        if contract_rejected and rejection_reason_code is None:
            rejection_reason_code = (
                "cross_vowel_handoff_crosses_silence_core"
                if silence_core_overlap
                else "provenance_unavailable"
            )
        result.append(
            ObservationHandoff(
                span_start_index=span_start,
                span_end_index=span_end,
                previous_non_zero_event_index=previous_index,
                next_non_zero_event_index=next_index,
                candidate_kind=kind,
                enabled=(
                    not touches_long
                    and not any(value in adjusted_indices for value in touched)
                    and not contract_rejected
                ),
                full_span_start_frame=getattr(observation, "full_span_start_frame", None),
                full_span_end_frame=getattr(observation, "full_span_end_frame", None),
                silence_core_frame_ranges=tuple(
                    getattr(observation, "silence_core_frame_ranges", ()) or ()
                ),
                boundary_fringe_frame_ranges=tuple(
                    getattr(observation, "boundary_fringe_frame_ranges", ()) or ()
                ),
                silence_core_overlap=silence_core_overlap,
                coverage_status=coverage_status,
                provenance_status=provenance_status,
                rejection_reason_code=rejection_reason_code,
            )
        )
    return tuple(result)


def _apply_cross_vowel_handoffs(
    events: tuple[EffectiveShapeEvent, ...],
    handoffs: tuple[ObservationHandoff, ...],
) -> tuple[EffectiveShapeEvent, ...]:
    by_index = {event.base_event_index: event for event in events}
    for handoff in handoffs:
        if not handoff.enabled or handoff.candidate_kind != "cross_vowel_transition":
            continue
        previous_index = handoff.previous_non_zero_event_index
        next_index = handoff.next_non_zero_event_index
        if previous_index is None or next_index is None:
            continue
        previous = by_index[previous_index]
        next_event = by_index[next_index]
        span_start = by_index[handoff.span_start_index]
        span_end = by_index[handoff.span_end_index]
        if previous.vowel == next_event.vowel:
            continue
        by_index[previous_index] = replace(
            previous,
            end_frame=max(previous.end_frame, span_end.end_frame),
        )
        by_index[next_index] = replace(
            next_event,
            start_frame=min(next_event.start_frame, span_start.start_frame),
        )
    return tuple(
        sorted(by_index.values(), key=lambda item: (item.peak_frame, item.base_event_index))
    )


def _merge_frame_ranges(frames: Sequence[int]) -> tuple[tuple[int, int], ...]:
    ordered = sorted(set(int(frame_no) for frame_no in frames))
    if not ordered:
        return ()
    ranges: list[tuple[int, int]] = []
    start = ordered[0]
    end = start + 1
    for frame_no in ordered[1:]:
        if frame_no == end:
            end += 1
            continue
        ranges.append((start, end))
        start = frame_no
        end = frame_no + 1
    ranges.append((start, end))
    return tuple(ranges)


def _shape_value_at_frame(shape: EffectiveShape, frame_no: int) -> float:
    points = tuple(shape.control_points)
    if not points or frame_no < points[0].frame_no or frame_no > points[-1].frame_no:
        return 0.0
    for point in points:
        if point.frame_no == frame_no:
            return float(point.value)
    for left, right in zip(points, points[1:]):
        if not left.frame_no <= frame_no <= right.frame_no:
            continue
        span = right.frame_no - left.frame_no
        if span <= 0:
            return max(float(left.value), float(right.value))
        ratio = (frame_no - left.frame_no) / span
        return float(left.value) + ((float(right.value) - float(left.value)) * ratio)
    return 0.0


def _silence_core_ranges_from_observations(
    observations: Sequence[ObservationLike] | None,
) -> tuple[tuple[int, int], ...]:
    if observations is None:
        return ()
    frames: list[int] = []
    for observation in observations:
        for frame_range in getattr(observation, "silence_core_frame_ranges", ()) or ():
            if (
                not isinstance(frame_range, (tuple, list))
                or len(frame_range) != 2
                or any(
                    isinstance(frame_no, bool) or not isinstance(frame_no, int)
                    for frame_no in frame_range
                )
                or frame_range[1] <= frame_range[0]
            ):
                continue
            frames.extend(range(frame_range[0], frame_range[1]))
    return _merge_frame_ranges(frames)


def _frame_in_ranges(
    frame_no: int,
    frame_ranges: Sequence[tuple[int, int]],
) -> bool:
    return any(start <= frame_no < end for start, end in frame_ranges)


def _clip_shape_to_silence_cores(
    shape: EffectiveShape,
    silence_core_frame_ranges: Sequence[tuple[int, int]],
) -> tuple[EffectiveShape, tuple[tuple[int, int], ...]]:
    applicable_ranges: list[tuple[int, int]] = []
    boundary_frames: set[int] = set()
    for start_frame, end_frame in silence_core_frame_ranges:
        clipped_start = max(shape.start_frame, start_frame)
        clipped_end = min(shape.end_frame + 1, end_frame)
        if clipped_end > clipped_start:
            applicable_ranges.append((clipped_start, clipped_end))
        for boundary in (start_frame, end_frame):
            if shape.start_frame <= boundary <= shape.end_frame:
                boundary_frames.add(boundary)
    if not applicable_ranges and not boundary_frames:
        return shape, ()

    clipped_frames = _merge_frame_ranges(
        [frame_no for start, end in applicable_ranges for frame_no in range(start, end)]
    )
    forced_zero_frames = {
        boundary
        for start, end in clipped_frames
        for boundary in (start, end)
    }
    forced_zero_frames.update(boundary_frames)
    by_frame: dict[int, ShapeControlPoint] = {}
    for point in shape.control_points:
        if _frame_in_ranges(point.frame_no, clipped_frames):
            by_frame[point.frame_no] = ShapeControlPoint(
                point.frame_no,
                0.0,
                "silence_core_zero",
            )
        else:
            by_frame[point.frame_no] = point
    for frame_no in forced_zero_frames:
        if shape.start_frame <= frame_no <= shape.end_frame:
            by_frame[frame_no] = ShapeControlPoint(
                frame_no,
                0.0,
                "silence_core_zero",
            )

    clipped_points = tuple(by_frame[frame_no] for frame_no in sorted(by_frame))
    if clipped_points == shape.control_points:
        return shape, clipped_frames
    return (
        replace(
            shape,
            control_points=clipped_points,
            silence_core_frame_ranges=clipped_frames,
        ),
        clipped_frames,
    )


def _clip_shapes_to_silence_cores(
    shapes: Sequence[EffectiveShape],
    silence_core_frame_ranges: Sequence[tuple[int, int]],
    *,
    record_sink: list[dict[str, Any]] | None = None,
) -> tuple[EffectiveShape, ...]:
    clipped_shapes: list[EffectiveShape] = []
    for shape_index, shape in enumerate(shapes):
        clipped_shape, clipped_ranges = _clip_shape_to_silence_cores(
            shape,
            silence_core_frame_ranges,
        )
        if record_sink is not None and clipped_shape is not shape:
            record_sink.append(
                {
                    "shape_id": shape_index,
                    "vowel": shape.vowel,
                    "source_event_indices": list(shape.real_base_event_indices),
                    "reason_code": (
                        "shape_split_by_silence_core"
                        if clipped_ranges
                        else "silence_core_boundary_zero"
                    ),
                    "silence_core_frame_ranges": [list(item) for item in clipped_ranges],
                    "before_control_points": [
                        {
                            "frame_no": point.frame_no,
                            "value": point.value,
                            "point_kind": point.point_kind,
                        }
                        for point in shape.control_points
                    ],
                    "after_control_points": [
                        {
                            "frame_no": point.frame_no,
                            "value": point.value,
                            "point_kind": point.point_kind,
                        }
                        for point in clipped_shape.control_points
                    ],
                }
            )
        clipped_shapes.append(clipped_shape)
    return tuple(clipped_shapes)


def _matching_shapes_for_event(
    shapes: Sequence[EffectiveShape],
    event: EffectiveShapeEvent,
) -> list[tuple[int, EffectiveShape]]:
    return [
        (shape_index, shape)
        for shape_index, shape in enumerate(shapes)
        if event.base_event_index in shape.real_base_event_indices
    ]


def _candidate_shape_details_for_event(
    shapes: Sequence[EffectiveShape],
    event: EffectiveShapeEvent,
    core_frames: set[int],
    *,
    matching: Sequence[tuple[int, EffectiveShape]] | None = None,
) -> tuple[
    int | None,
    tuple[str, ...],
    tuple[int, ...],
    tuple[int, int],
    tuple[tuple[int, int], ...],
]:
    if matching is None:
        matching = _matching_shapes_for_event(shapes, event)
    if not matching:
        return None, (), (), (event.start_frame, event.end_frame), ()

    positive_frames: set[int] = set()
    positive_point_kinds: set[str] = set()
    source_event_indices: set[int] = set()
    effective_start = event.start_frame
    effective_end = event.end_frame
    origin_shape_id = matching[0][0]
    for _, shape in matching:
        source_event_indices.update(shape.real_base_event_indices)
        event_position = shape.real_base_event_indices.index(event.base_event_index)
        if event_position < len(shape.event_ranges):
            event_start, event_end = shape.event_ranges[event_position]
        else:
            event_start, event_end = event.start_frame, event.end_frame
        if event.long_vowel_role is not None:
            event_start = min(event_start, shape.start_frame)
            event_end = max(event_end, shape.end_frame)
        elif event_position == len(shape.real_base_event_indices) - 1:
            event_end = max(event_end, shape.end_frame)
        effective_start = min(effective_start, event_start)
        effective_end = max(effective_end, event_end)
        for frame_no in core_frames:
            if not event_start <= frame_no < event_end:
                continue
            if _shape_value_at_frame(shape, frame_no) > MORPH_FRAME_OPEN_EPSILON:
                positive_frames.add(frame_no)
        for point in shape.control_points:
            if (
                point.frame_no in core_frames
                and event_start <= point.frame_no < event_end
                and point.value > MORPH_FRAME_OPEN_EPSILON
            ):
                positive_point_kinds.add(point.point_kind)

    return (
        origin_shape_id,
        tuple(sorted(positive_point_kinds)),
        tuple(sorted(source_event_indices)),
        (effective_start, effective_end),
        _merge_frame_ranges(sorted(positive_frames)),
    )


def _boundary_relation_for_event(
    effective_events: Sequence[EffectiveShapeEvent],
    event: EffectiveShapeEvent,
    boundary_frame: int,
) -> str | None:
    position = next(
        (
            index
            for index, candidate in enumerate(effective_events)
            if candidate.base_event_index == event.base_event_index
        ),
        None,
    )
    if position is None:
        return None
    previous = effective_events[position - 1] if position > 0 else None
    following = (
        effective_events[position + 1]
        if position + 1 < len(effective_events)
        else None
    )
    same_vowel_boundary = any(
        candidate is not None
        and candidate.vowel == event.vowel
        and (
            candidate.end_frame == boundary_frame
            if candidate is previous
            else candidate.start_frame == boundary_frame
        )
        for candidate in (previous, following)
    )
    if same_vowel_boundary:
        return "same_vowel_same_frame"
    different_vowel_boundary = any(
        candidate is not None
        and candidate.vowel != event.vowel
        and (
            candidate.end_frame == boundary_frame
            if candidate is previous
            else candidate.start_frame == boundary_frame
        )
        for candidate in (previous, following)
    )
    if different_vowel_boundary:
        return "different_vowel_boundary"
    if (
        previous is not None
        and previous.end_frame < boundary_frame
        or following is not None
        and following.start_frame > boundary_frame
    ):
        return "silence_gap"
    return None


def _boundary_point_kinds_at_frame(
    matching: Sequence[tuple[int, EffectiveShape]],
    frame_no: int,
) -> tuple[tuple[str, ...], bool]:
    positive_point_kinds: set[str] = set()
    matching_end_zero = False
    for _, shape in matching:
        for point in shape.control_points:
            if point.frame_no != frame_no:
                continue
            if point.point_kind == "end_zero" and point.value <= MORPH_FRAME_OPEN_EPSILON:
                matching_end_zero = True
            if point.value > MORPH_FRAME_OPEN_EPSILON:
                positive_point_kinds.add(point.point_kind)
    return tuple(sorted(positive_point_kinds)), matching_end_zero


def _admission_range_status(value: object) -> str:
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        return "unavailable"
    if value[1] == value[0]:
        return "zero_width"
    if value[1] < value[0]:
        return "reversed"
    return "valid"


def _admission_shape_provenance(
    matching: Sequence[tuple[int, EffectiveShape]],
    event: EffectiveShapeEvent,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for shape_index, shape in matching:
        event_position = shape.real_base_event_indices.index(event.base_event_index)
        event_range = (
            shape.event_ranges[event_position]
            if event_position < len(shape.event_ranges)
            else (event.start_frame, event.end_frame)
        )
        shape_range = (
            (shape.start_frame, shape.end_frame)
            if shape.control_points
            else None
        )
        result.append(
            {
                "shape_ordinal": shape_index,
                "shape_kind": shape.shape_kind,
                "real_base_event_indices": tuple(shape.real_base_event_indices),
                "event_range": event_range,
                "shape_range": shape_range,
                "control_points": tuple(
                    {
                        "frame_no": point.frame_no,
                        "value": point.value,
                        "point_kind": point.point_kind,
                    }
                    for point in shape.control_points
                ),
            }
        )
    return result


def _build_admission_failure_detail(
    *,
    base_events: Sequence[BaseShapeEvent] | None,
    effective_events: Sequence[EffectiveShapeEvent],
    event: EffectiveShapeEvent,
    matching: Sequence[tuple[int, EffectiveShape]],
    origin_shape_id: int | None,
    positive_point_kinds: tuple[str, ...],
    source_event_indices: tuple[int, ...],
    effective_frame_range: tuple[int, int],
    positive_core_frame_ranges: tuple[tuple[int, int], ...],
    observed_positive_ranges: tuple[tuple[int, int], ...],
    required_zero_frame_ranges: tuple[tuple[int, int], ...],
    base_overlap: bool,
    manual_adjustment_applied: bool,
    enabled: bool,
    rejection_reason_code: str | None,
    boundary_only: bool,
    boundary_frame: int | None,
    boundary_point_kind: str | None,
    boundary_point_kinds: tuple[str, ...],
    matching_end_zero: bool,
    boundary_relation: str,
    boundary_action: str,
    long_runs: Sequence[EffectiveLongVowelRun],
) -> dict[str, object]:
    base_event = next(
        (
            item
            for item in (base_events or ())
            if item.base_event_index == event.base_event_index
        ),
        None,
    )
    raw_range: dict[str, object] = {}
    if base_event is not None:
        raw_range = {
            "start_sec": base_event.start_sec,
            "end_sec": base_event.end_sec,
            "start_frame": base_event.start_frame,
            "peak_frame": base_event.peak_frame,
            "end_frame": base_event.end_frame,
        }

    event_position = next(
        (
            index
            for index, candidate in enumerate(effective_events)
            if candidate.base_event_index == event.base_event_index
        ),
        None,
    )
    adjacent_ranges: list[dict[str, object]] = []
    previous_event_index: int | None = None
    next_event_index: int | None = None
    if event_position is not None:
        if event_position > 0:
            previous = effective_events[event_position - 1]
            previous_event_index = previous.base_event_index
            adjacent_ranges.append(
                {
                    "event_index": previous.base_event_index,
                    "vowel": previous.vowel,
                    "range": (previous.start_frame, previous.end_frame),
                }
            )
        if event_position + 1 < len(effective_events):
            following = effective_events[event_position + 1]
            next_event_index = following.base_event_index
            adjacent_ranges.append(
                {
                    "event_index": following.base_event_index,
                    "vowel": following.vowel,
                    "range": (following.start_frame, following.end_frame),
                }
            )

    long_source_event_index: int | None = None
    for run in long_runs:
        if event.base_event_index in {
            run.source_base_event_index,
            *run.continuation_base_event_indices,
        }:
            long_source_event_index = run.source_base_event_index
            break

    event_context_available = (
        isinstance(event.base_event_index, int)
        and isinstance(event.vowel, str)
        and isinstance(effective_frame_range, tuple)
        and len(effective_frame_range) == 2
    )
    candidate_available = bool(matching)
    range_available = base_event is not None and event_context_available
    section_status = {
        "event_context": {
            "state": "available" if event_context_available else "not_available",
            "reason": "not_applicable" if event_context_available else "not_available",
        },
        "admission_candidate": {
            "state": "available" if candidate_available else "partial",
            "reason": "not_applicable" if candidate_available else "value_not_observed",
        },
        "range_derivation": {
            "state": "available" if range_available else "partial",
            "reason": "not_applicable" if range_available else "value_not_observed",
        },
    }
    capture_state = (
        "available"
        if all(item["state"] == "available" for item in section_status.values())
        else "partial"
    )
    shape_provenance = _admission_shape_provenance(matching, event)
    candidate_range_status = _admission_range_status(effective_frame_range)
    boundary_admission_checks: dict[str, object] = {
        "candidate_range": candidate_range_status,
        "positive_point_kinds_empty": not positive_point_kinds,
        "boundary_positive_point_kinds_empty": not boundary_point_kinds,
        "positive_core_frame_ranges_empty": not positive_core_frame_ranges,
        "matching_end_zero": (
            matching_end_zero if candidate_range_status == "zero_width" else "not_available"
        ),
        "shape_provenance_available": bool(shape_provenance),
        "boundary_relation_verified": (
            boundary_relation != "not_applicable"
            if boundary_frame is not None
            else "not_available"
        ),
        "event_peak_value": event.peak_value,
        "decision": (
            "accepted_boundary_only"
            if boundary_only
            else (
                "rejected_boundary_invalid"
                if rejection_reason_code == "admission_boundary_invalid"
                else "not_applicable"
            )
        ),
    }
    return {
        "detail_capture_state": capture_state,
        "unavailable_reason": "not_applicable" if capture_state == "available" else "value_not_observed",
        "section_status": section_status,
        "event_context": {
            "event_index": event.base_event_index,
            "vowel": event.vowel,
            "raw_range": raw_range,
            "effective_event_range": effective_frame_range,
            "event_range_status": _admission_range_status(effective_frame_range),
            "adjacent": {
                "previous_event_index": previous_event_index,
                "next_event_index": next_event_index,
            },
            "adjacent_ranges": adjacent_ranges,
            "long_vowel_role": event.long_vowel_role,
            "long_vowel_source_event_index": long_source_event_index,
        },
        "admission_candidate": {
            "origin_shape_id": origin_shape_id,
            "source_event_indices": source_event_indices,
            "shape_match_count": len(matching),
            "shape_provenance": shape_provenance,
            "positive_point_kinds": positive_point_kinds,
            "positive_core_frame_ranges": positive_core_frame_ranges,
            "observed_positive_core_frame_ranges": observed_positive_ranges,
            "required_zero_frame_ranges": required_zero_frame_ranges,
            "boundary_only": boundary_only,
            "boundary_frame": boundary_frame,
            "boundary_point_kind": boundary_point_kind,
            "boundary_relation": boundary_relation,
            "boundary_action": boundary_action,
            "boundary_admission_checks": boundary_admission_checks,
            "base_event_silence_core_overlap": base_overlap,
            "manual_adjustment_applied": manual_adjustment_applied,
            "enabled": enabled,
            "rejection_reason_code": rejection_reason_code,
        },
        "range_derivation": {
            "raw_event_range": (
                (base_event.start_frame, base_event.end_frame)
                if base_event is not None
                else None
            ),
            "shape_event_ranges": [item["event_range"] for item in shape_provenance],
            "effective_range_before_validation": effective_frame_range,
            "range_inputs_status": (
                "invalid"
                if _admission_range_status(effective_frame_range) in {"zero_width", "reversed"}
                else "observed"
            ),
        },
    }


def _build_event_silence_admissions(
    base_input: BaseTimingPlanInput,
    effective_events: tuple[EffectiveShapeEvent, ...],
    candidate_shapes: Sequence[EffectiveShape],
    snapshot: AdjustmentLayerSnapshot,
    *,
    base_events: Sequence[BaseShapeEvent] | None = None,
    long_runs: Sequence[EffectiveLongVowelRun] = (),
    failure_detail_sink: dict[str, object] | None = None,
    _defer_boundary_validation: bool = False,
) -> tuple[tuple[EventSilenceAdmission, ...], set[int]]:
    observations = base_input.observations or ()
    adjustment_by_index = {item.base_event_index: item for item in snapshot.adjustments}
    admissions: list[EventSilenceAdmission] = []
    rejected_indices: set[int] = set()
    for event in effective_events:
        observation = observations[event.base_event_index] if event.base_event_index < len(observations) else None
        core_ranges = tuple(getattr(observation, "silence_core_frame_ranges", ()) or ())
        core_frames = {
            frame_no
            for start, end in core_ranges
            for frame_no in range(start, end)
        }
        matching = _matching_shapes_for_event(candidate_shapes, event)
        (
            origin_shape_id,
            positive_point_kinds,
            source_event_indices,
            effective_frame_range,
            positive_core_frame_ranges,
        ) = _candidate_shape_details_for_event(
            candidate_shapes,
            event,
            core_frames,
            matching=matching,
        )
        observed_positive_ranges = tuple(
            getattr(observation, "positive_core_frame_ranges", ()) or ()
        )
        candidate_effective_frame_range = effective_frame_range
        if (
            observed_positive_ranges
            and _admission_range_status(candidate_effective_frame_range) == "zero_width"
        ):
            positive_core_frame_ranges = _merge_frame_ranges(
                [
                    frame_no
                    for start, end in observed_positive_ranges
                    for frame_no in range(start, end)
                ]
            )
        base_overlap = bool(
            getattr(observation, "base_event_silence_core_overlap", False)
            or any(
                start < candidate_effective_frame_range[1]
                and candidate_effective_frame_range[0] < end
                for start, end in core_ranges
            )
        )
        adjustment = adjustment_by_index.get(event.base_event_index)
        manual_adjustment_applied = (
            adjustment is not None and adjustment.has_shape_adjustment
        )
        has_positive_core = bool(positive_core_frame_ranges)
        explicitly_allowed = event.long_vowel_role is not None or manual_adjustment_applied
        enabled = not has_positive_core or explicitly_allowed
        rejection_reason_code = None
        required_zero_frame_ranges: tuple[tuple[int, int], ...] = ()
        boundary_only = False
        boundary_frame: int | None = None
        boundary_point_kind: str | None = None
        boundary_point_kinds: tuple[str, ...] = ()
        matching_end_zero = False
        boundary_relation = "not_applicable"
        boundary_action = "not_applicable"
        if _admission_range_status(candidate_effective_frame_range) == "zero_width":
            boundary_frame = candidate_effective_frame_range[0]
            boundary_point_kinds, matching_end_zero = _boundary_point_kinds_at_frame(
                matching,
                boundary_frame,
            )
            if boundary_point_kinds:
                positive_point_kinds = tuple(
                    sorted(set(positive_point_kinds).union(boundary_point_kinds))
                )
            boundary_relation = _boundary_relation_for_event(
                effective_events,
                event,
                boundary_frame,
            ) or "not_applicable"
            if (
                not has_positive_core
                and not positive_point_kinds
                and not boundary_point_kinds
                and matching_end_zero
                and boundary_relation != "not_applicable"
            ):
                boundary_only = True
                effective_frame_range = None
                boundary_point_kind = "end_zero"
                boundary_action = "preserved_zero_keyframe"
                enabled = True
            else:
                enabled = False
                rejection_reason_code = "admission_boundary_invalid"
                effective_frame_range = None
                rejected_indices.add(event.base_event_index)
        if has_positive_core and not explicitly_allowed and not boundary_only and rejection_reason_code is None:
            enabled = False
            rejection_reason_code = "base_event_overlaps_silence_core"
            required_zero_frame_ranges = positive_core_frame_ranges
            rejected_indices.add(event.base_event_index)
        if failure_detail_sink is not None:
            failure_detail_sink["value"] = _build_admission_failure_detail(
                base_events=base_events,
                effective_events=effective_events,
                event=event,
                matching=matching,
                origin_shape_id=origin_shape_id,
                positive_point_kinds=positive_point_kinds,
                source_event_indices=source_event_indices,
                effective_frame_range=candidate_effective_frame_range,
                positive_core_frame_ranges=positive_core_frame_ranges,
                observed_positive_ranges=observed_positive_ranges,
                required_zero_frame_ranges=required_zero_frame_ranges,
                base_overlap=base_overlap,
                manual_adjustment_applied=manual_adjustment_applied,
                enabled=enabled,
                rejection_reason_code=rejection_reason_code,
                boundary_only=boundary_only,
                boundary_frame=boundary_frame,
                boundary_point_kind=boundary_point_kind,
                boundary_point_kinds=boundary_point_kinds,
                matching_end_zero=matching_end_zero,
                boundary_relation=boundary_relation,
                boundary_action=boundary_action,
                long_runs=long_runs,
            )
        if (_defer_boundary_validation and event.peak_value > 0
                and _admission_range_status(candidate_effective_frame_range) == "zero_width"
                and not core_ranges and not manual_adjustment_applied and not event.long_vowel_role):
            boundary_only = False
            boundary_frame = None
            boundary_point_kind = None
            boundary_relation = "not_applicable"
            boundary_action = "not_applicable"
            effective_frame_range = None
            enabled = True
            rejection_reason_code = None
            rejected_indices.discard(event.base_event_index)
        if (rejection_reason_code == "admission_boundary_invalid" and _defer_boundary_validation
                and not core_ranges and not manual_adjustment_applied and not event.long_vowel_role):
            # Held only inside the B4B preparation DTO. The scheduler must
            # supply the positive support before any final issuer is accepted.
            enabled = True
            rejection_reason_code = None
            rejected_indices.discard(event.base_event_index)
        if rejection_reason_code == "admission_boundary_invalid":
            raise AdjustmentContractError(
                "zero-width admission is not a verified boundary",
                safe_code="admission_boundary_invalid",
                safe_field_code="boundary_frame",
                safe_phase="silence_admission",
                event_index=event.base_event_index,
            )
        admissions.append(
            EventSilenceAdmission(
                event_index=event.base_event_index,
                vowel=event.vowel,
                origin_shape_id=origin_shape_id,
                positive_point_kinds=positive_point_kinds,
                source_event_indices=source_event_indices,
                effective_frame_range=effective_frame_range,
                boundary_only=boundary_only,
                boundary_frame=boundary_frame if boundary_only else None,
                boundary_point_kind=boundary_point_kind if boundary_only else None,
                boundary_relation=boundary_relation if boundary_only else "not_applicable",
                boundary_action=boundary_action if boundary_only else "not_applicable",
                base_event_silence_core_overlap=base_overlap,
                positive_core_frame_ranges=positive_core_frame_ranges,
                long_vowel_role=event.long_vowel_role,
                manual_adjustment_applied=manual_adjustment_applied,
                enabled=enabled,
                rejection_reason_code=rejection_reason_code,
                required_zero_frame_ranges=required_zero_frame_ranges,
            )
        )
    return tuple(admissions), rejected_indices


def _rebind_event_silence_admissions(
    admissions: tuple[EventSilenceAdmission, ...],
    final_shapes: Sequence[EffectiveShape],
) -> tuple[EventSilenceAdmission, ...]:
    shape_by_event: dict[int, tuple[int, EffectiveShape]] = {}
    for shape_index, shape in enumerate(final_shapes):
        for event_index in shape.real_base_event_indices:
            shape_by_event[event_index] = (shape_index, shape)
    rebound: list[EventSilenceAdmission] = []
    for admission in admissions:
        match = shape_by_event.get(admission.event_index)
        if match is None:
            rebound.append(replace(admission, origin_shape_id=None))
            continue
        shape_index, shape = match
        rebound.append(
            replace(
                admission,
                origin_shape_id=shape_index,
                source_event_indices=tuple(shape.real_base_event_indices),
            )
        )
    return tuple(rebound)


def _required_zero_frames_from_admissions(
    admissions: Sequence[EventSilenceAdmission],
) -> tuple[tuple[str, int], ...]:
    pairs = {
        (admission.vowel, frame_no)
        for admission in admissions
        for start, end in admission.required_zero_frame_ranges
        for frame_no in range(start, end)
    }
    pairs.update(
        (admission.vowel, admission.boundary_frame)
        for admission in admissions
        if admission.boundary_only and admission.boundary_frame is not None
    )
    return tuple(sorted(pairs, key=lambda item: (item[1], item[0])))


def _group_events(events: tuple[EffectiveShapeEvent, ...]) -> list[list[EffectiveShapeEvent]]:
    groups: list[list[EffectiveShapeEvent]] = []
    for event in events:
        if (
            groups
            and groups[-1][-1].vowel == event.vowel
            and event.base_event_index == groups[-1][-1].base_event_index + 1
            and event.start_frame - groups[-1][-1].end_frame <= NEARBY_GROUP_GAP_FRAMES
        ):
            groups[-1].append(event)
        else:
            groups.append([event])
    return groups


def _validate_manual_overlap_override_ownership(
    events: tuple[EffectiveShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
    long_indices: set[int],
) -> None:
    regular_events = tuple(
        event for event in events if event.base_event_index not in long_indices
    )
    tail_indices = {
        group[-1].base_event_index for group in _group_events(regular_events)
    }
    for item in snapshot.adjustments:
        if item.manual_overlap_limit_override and item.base_event_index not in tail_indices:
            raise AdjustmentContractError(
                "manual overlap override belongs to the regular group tail owner",
                safe_code="manual_overlap_override_owner_invalid",
                safe_field_code="manual_overlap_limit_override",
                safe_phase="adjustment_ownership",
                event_index=item.base_event_index,
            )


def _next_shape_boundary_event(
    effective_events: tuple[EffectiveShapeEvent, ...],
    after_base_event_index: int,
) -> EffectiveShapeEvent | None:
    return next(
        (
            event
            for event in effective_events
            if event.base_event_index > after_base_event_index
            and event.long_vowel_role in (None, "long_source")
        ),
        None,
    )


def _next_same_vowel_boundary_event(
    effective_events: tuple[EffectiveShapeEvent, ...],
    after_base_event_index: int,
    vowel: str,
) -> EffectiveShapeEvent | None:
    return next(
        (
            event
            for event in effective_events
            if event.base_event_index > after_base_event_index
            and event.vowel == vowel
            and event.long_vowel_role in (None, "long_source")
        ),
        None,
    )


def _single_event_peak_frames(
    start_frame: int,
    peak_frame: int,
    end_frame: int,
) -> tuple[int, int]:
    total_span = end_frame - start_frame
    left_available = peak_frame - start_frame
    right_available = end_frame - peak_frame
    max_centered_half_width = min(left_available - 1, right_available - 1)
    if peak_frame == start_frame:
        return peak_frame, peak_frame
    if total_span >= 4 and max_centered_half_width >= 1:
        relative_half_width = min(left_available, right_available) // 2
        top_half_width = max(1, min(relative_half_width, max_centered_half_width))
        return peak_frame - top_half_width, peak_frame + top_half_width

    peak_start = min(peak_frame, start_frame + 2)
    peak_end = max(peak_frame, end_frame - 2)
    if peak_end <= peak_start:
        return peak_frame, peak_frame
    return peak_start, peak_end


def _shape_for_group(
    group: Sequence[EffectiveShapeEvent],
    *,
    adjustment_by_index: dict[int, EventAdjustment],
    shape_parameters: ShapeParameters,
    next_shape_start_frame: int | None,
    synthetic_token: int | None = None,
    manual_extension_limit_frame: int | None = None,
    allow_inactive_slope: bool = False,
) -> EffectiveShape:
    first = group[0]
    last = group[-1]
    tail_adjustment = adjustment_by_index.get(last.base_event_index)
    hold_frames = (
        tail_adjustment.hold_frames
        if tail_adjustment is not None and tail_adjustment.hold_frames is not None
        else shape_parameters.closing_hold_frames
    )
    softness_frames = (
        tail_adjustment.softness_frames
        if tail_adjustment is not None and tail_adjustment.softness_frames is not None
        else shape_parameters.closing_softness_frames
    )
    slope_ratio = (
        tail_adjustment.slope_ratio
        if tail_adjustment is not None and tail_adjustment.slope_ratio is not None
        else DEFAULT_SLOPE_RATIO
    )
    points: list[ShapeControlPoint] = [ShapeControlPoint(first.start_frame, 0.0, "start_zero")]
    if len(group) == 1:
        peak_start, peak_end = _single_event_peak_frames(
            first.start_frame,
            first.peak_frame,
            first.end_frame,
        )
        if first.peak_frame == first.start_frame:
            # A source event can begin on its acoustic peak. In that case the
            # start-zero and peak occupy the same VMD frame; preserve the peak
            # so normalization does not erase the entire opening.
            points[0] = ShapeControlPoint(
                first.peak_frame,
                first.peak_value,
                "top",
            )
        if first.start_frame < peak_start < first.end_frame:
            points.append(ShapeControlPoint(peak_start, first.peak_value, "top"))
        if peak_end > peak_start and peak_end < first.end_frame:
            points.append(
                ShapeControlPoint(
                    peak_end,
                    (
                        first.peak_value
                        if first.closing_peak_value is None
                        else first.closing_peak_value
                    ),
                    "top",
                    source_event_index=first.base_event_index,
                )
            )
    else:
        for index, event in enumerate(group):
            if index > 0:
                previous = group[index - 1]
                valley_frame = (previous.peak_frame + event.peak_frame) // 2
                lower_peak = min(previous.peak_value, event.peak_value)
                valley_value = min(lower_peak - 0.01, max(0.05, lower_peak * 0.35))
                if points[-1].frame_no < valley_frame < event.peak_frame:
                    points.append(ShapeControlPoint(valley_frame, valley_value, "valley"))
            if points[-1].frame_no == event.peak_frame:
                points[-1] = ShapeControlPoint(
                    event.peak_frame,
                    max(points[-1].value, event.peak_value),
                    "top",
                )
            elif points[-1].frame_no < event.peak_frame:
                points.append(ShapeControlPoint(event.peak_frame, event.peak_value, "top"))

    tail_anchor_frame = last.end_frame
    tail_anchor_value = last.peak_value
    if len(group) == 1 and first.closing_peak_value is not None:
        tail_anchor_value = first.closing_peak_value
    available_extension = None
    if manual_extension_limit_frame is not None:
        available_extension = max(0, manual_extension_limit_frame - last.end_frame)
    elif next_shape_start_frame is not None:
        available_extension = max(0, (next_shape_start_frame - 1) - last.end_frame)
    effective_hold = hold_frames
    effective_softness = softness_frames
    if available_extension is not None:
        effective_hold = min(effective_hold, available_extension)
        effective_softness = min(effective_softness, available_extension - effective_hold)
    end_frame = last.end_frame + effective_hold + effective_softness
    hold_frame = None
    if effective_hold > 0 and end_frame > last.end_frame:
        hold_frame = max(last.end_frame, end_frame - effective_softness - 1)
        if hold_frame < end_frame:
            points.append(ShapeControlPoint(hold_frame, tail_anchor_value, "hold"))
    if effective_softness > 0 and end_frame > last.end_frame:
        mid_frame = end_frame - 1
        minimum_mid = last.end_frame if hold_frame is None else hold_frame + 1
        mid_frame = max(mid_frame, minimum_mid)
        if mid_frame < end_frame:
            points.append(ShapeControlPoint(mid_frame, tail_anchor_value * slope_ratio, "slope_mid"))
    has_slope_midpoint = any(point.point_kind == "slope_mid" for point in points)
    if (
        tail_adjustment is not None
        and tail_adjustment.slope_ratio is not None
        and not has_slope_midpoint
        and not allow_inactive_slope
    ):
        raise AdjustmentContractError(
            "slope override requires an effective softness midpoint",
            safe_code="slope_midpoint_missing",
            safe_field_code="slope_ratio",
            safe_phase="regular_shapes",
            event_index=last.base_event_index,
        )
    if points[-1].frame_no == end_frame:
        points[-1] = ShapeControlPoint(end_frame, 0.0, "end_zero")
    else:
        points.append(ShapeControlPoint(end_frame, 0.0, "end_zero"))

    indices = tuple(event.base_event_index for event in group)
    return EffectiveShape(
        vowel=first.vowel,
        shape_kind=("multi_point_envelope" if len(group) > 1 else "asymmetric_trapezoid"),
        control_points=tuple(points),
        real_base_event_indices=indices,
        internal_shape_source_tokens=(() if synthetic_token is None else (synthetic_token,)),
        event_ranges=tuple((event.start_frame, event.end_frame) for event in group),
        protection_mode="preserve_shape",
        resolved_tail=ResolvedTailParameters(
            tail_base_event_index=last.base_event_index,
            requested_hold_frames=hold_frames,
            requested_softness_frames=softness_frames,
            effective_hold_frames=effective_hold,
            effective_softness_frames=effective_softness,
            available_extension_frames=available_extension,
            slope_ratio=slope_ratio,
            has_slope_midpoint=has_slope_midpoint,
        ),
    )


def _shape_for_long_run(
    run: EffectiveLongVowelRun,
    *,
    effective_events: tuple[EffectiveShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
    shape_parameters: ShapeParameters,
    next_shape_start_frame: int | None,
    next_shape_vowel: str | None = None,
    next_same_vowel_start_frame: int | None = None,
    next_same_vowel_starts_positive: bool = False,
) -> EffectiveShape:
    by_index = {event.base_event_index: event for event in effective_events}
    members = tuple(
        by_index[index]
        for index in (run.source_base_event_index, *run.continuation_base_event_indices)
    )
    source = members[0]
    terminal = members[-1]
    if terminal.end_frame <= source.peak_frame:
        raise AdjustmentContractError(
            "long-vowel terminal end must be after source peak",
            safe_code="long_terminal_order_invalid",
            safe_field_code="terminal_end_frame",
            safe_phase="long_shapes",
            event_index=terminal.base_event_index,
            source_event_index=source.base_event_index,
            event_role="terminal",
            source_event_role="source",
            safe_details={
                "peak_frame": source.peak_frame,
                "end_frame": terminal.end_frame,
            },
        )
    adjustment_by_index = {item.base_event_index: item for item in snapshot.adjustments}
    terminal_adjustment = adjustment_by_index.get(terminal.base_event_index)
    hold_frames = (
        terminal_adjustment.hold_frames
        if terminal_adjustment is not None and terminal_adjustment.hold_frames is not None
        else shape_parameters.closing_hold_frames
    )
    softness_frames = (
        terminal_adjustment.softness_frames
        if terminal_adjustment is not None and terminal_adjustment.softness_frames is not None
        else shape_parameters.closing_softness_frames
    )
    slope_ratio = (
        terminal_adjustment.slope_ratio
        if terminal_adjustment is not None and terminal_adjustment.slope_ratio is not None
        else DEFAULT_SLOPE_RATIO
    )
    mode = _resolved_long_mode(run, snapshot, shape_parameters)
    same_frame_same_vowel_handoff = (
        next_shape_start_frame is not None
        and next_shape_vowel == source.vowel
        and next_shape_start_frame == terminal.end_frame
    )
    points: list[ShapeControlPoint] = []
    if source.start_frame < source.peak_frame:
        points.append(ShapeControlPoint(source.start_frame, 0.0, "start_zero"))
    points.append(ShapeControlPoint(source.peak_frame, source.peak_value, "top"))
    available_extension = None
    if next_shape_start_frame is not None:
        available_extension = max(0, next_shape_start_frame - 1 - terminal.end_frame)

    if mode == LONG_VOWEL_MODE_DECAY:
        points.append(ShapeControlPoint(terminal.end_frame, 0.0, "end_zero"))
        resolved_tail = ResolvedTailParameters(
            tail_base_event_index=terminal.base_event_index,
            requested_hold_frames=hold_frames,
            requested_softness_frames=softness_frames,
            effective_hold_frames=0,
            effective_softness_frames=0,
            available_extension_frames=available_extension,
            slope_ratio=slope_ratio,
            has_slope_midpoint=False,
        )
        shape_kind = "long_vowel_decay"
    else:
        # A different vowel may be interleaved before the next same-vowel
        # event, so the immediate next shape does not protect this boundary.
        adjacent_same_vowel_handoff = (
            next_same_vowel_starts_positive
            and next_same_vowel_start_frame == terminal.end_frame + 1
        )
        if terminal.end_frame > source.peak_frame and not same_frame_same_vowel_handoff:
            terminal_hold_frame = (
                terminal.end_frame - 1
                if adjacent_same_vowel_handoff
                else terminal.end_frame
            )
            if terminal_hold_frame > points[-1].frame_no:
                points.append(ShapeControlPoint(terminal_hold_frame, source.peak_value, "top"))
        effective_hold = hold_frames
        effective_softness = softness_frames
        if available_extension is not None:
            effective_hold = min(effective_hold, available_extension)
            effective_softness = min(effective_softness, max(0, available_extension - effective_hold))
        closing_frame = terminal.end_frame + effective_hold + effective_softness
        if closing_frame <= terminal.end_frame:
            closing_frame = (
                terminal.end_frame
                if same_frame_same_vowel_handoff or adjacent_same_vowel_handoff
                else terminal.end_frame + 1
            )
        if (
            adjacent_same_vowel_handoff
            and closing_frame >= next_same_vowel_start_frame
        ):
            closing_frame = terminal.end_frame
        # Equality is safe: the repaired next same-morph event starts with the
        # same explicit zero.  A later closing zero would overlap its shape.
        if (
            next_shape_start_frame is not None
            and next_shape_vowel == source.vowel
            and closing_frame > next_shape_start_frame
        ):
            raise AdjustmentContractError(
                "long-vowel hold cannot close before the next shape",
                safe_code="long_hold_close_conflict",
                safe_field_code="closing_frame",
                safe_phase="long_shapes",
                event_index=terminal.base_event_index,
                source_event_index=run.source_base_event_index,
                event_role="terminal",
                source_event_role="source",
                safe_details={
                    "end_frame": terminal.end_frame,
                    "frame_end": closing_frame,
                    "neighbor_event_index": run.terminal_base_event_index,
                },
            )
        hold_frame = None
        if effective_hold > 0:
            hold_frame = max(terminal.end_frame, closing_frame - effective_softness - 1)
            if hold_frame > terminal.end_frame and hold_frame < closing_frame:
                points.append(ShapeControlPoint(hold_frame, source.peak_value, "hold"))
        if effective_softness > 0:
            midpoint = closing_frame - 1
            minimum_midpoint = terminal.end_frame if hold_frame is None else hold_frame + 1
            midpoint = max(midpoint, minimum_midpoint)
            if midpoint < closing_frame:
                points.append(ShapeControlPoint(midpoint, source.peak_value * slope_ratio, "slope_mid"))
        points.append(ShapeControlPoint(closing_frame, 0.0, "end_zero"))
        resolved_tail = ResolvedTailParameters(
            tail_base_event_index=terminal.base_event_index,
            requested_hold_frames=hold_frames,
            requested_softness_frames=softness_frames,
            effective_hold_frames=max(0, closing_frame - terminal.end_frame - effective_softness),
            effective_softness_frames=max(0, min(effective_softness, closing_frame - terminal.end_frame)),
            available_extension_frames=available_extension,
            slope_ratio=slope_ratio,
            has_slope_midpoint=any(point.point_kind == "slope_mid" for point in points),
        )
        shape_kind = "long_vowel_hold"

    return EffectiveShape(
        vowel=source.vowel,
        shape_kind=shape_kind,
        control_points=tuple(points),
        real_base_event_indices=tuple(event.base_event_index for event in members),
        event_ranges=tuple((event.start_frame, event.end_frame) for event in members),
        protection_mode="preserve_shape",
        resolved_tail=resolved_tail,
    )


def _build_shapes(
    effective_events: tuple[EffectiveShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
    handoffs: tuple[ObservationHandoff, ...],
    shape_parameters: ShapeParameters,
    *,
    allow_inactive_slope: bool = False,
    excluded_indices: set[int] | None = None,
) -> tuple[EffectiveShape, ...]:
    adjustment_by_index = {item.base_event_index: item for item in snapshot.adjustments}
    excluded = excluded_indices or set()
    filtered_events = tuple(event for event in effective_events if event.base_event_index not in excluded)
    groups = _group_events(filtered_events)
    tail_indices = {group[-1].base_event_index for group in groups}
    tail_indices.update(
        event.base_event_index
        for event in effective_events
        if event.long_vowel_role == "terminal_continuation"
    )
    for item in snapshot.adjustments:
        if (
            item.base_event_index not in tail_indices
            and (item.hold_frames is not None or item.softness_frames is not None or item.slope_ratio is not None)
        ):
            raise AdjustmentContractError(
                "tail overrides are valid only on a group tail event",
                safe_code="tail_override_non_tail",
                safe_field_code="tail_override",
                safe_phase="regular_shapes",
                event_index=item.base_event_index,
            )

    shapes: list[EffectiveShape] = []
    for group in groups:
        next_event = _next_shape_boundary_event(effective_events, group[-1].base_event_index)
        next_start = None if next_event is None else next_event.start_frame
        shapes.append(
            _shape_for_group(
                group,
                adjustment_by_index=adjustment_by_index,
                shape_parameters=shape_parameters,
                next_shape_start_frame=next_start,
                allow_inactive_slope=allow_inactive_slope,
            )
        )

    token = -1
    for handoff in handoffs:
        if not handoff.enabled or handoff.candidate_kind != "same_vowel_span":
            continue
        members = [
            event
            for event in effective_events
            if handoff.span_start_index <= event.base_event_index <= handoff.span_end_index
        ]
        if not members or any(event.vowel != members[0].vowel for event in members):
            continue
        member_indices = {event.base_event_index for event in members}
        shapes = [
            shape
            for shape in shapes
            if not member_indices.intersection(shape.real_base_event_indices)
        ]
        shapes.append(
            _shape_for_group(
                members,
                adjustment_by_index=adjustment_by_index,
                shape_parameters=shape_parameters,
                next_shape_start_frame=None,
                synthetic_token=token,
                allow_inactive_slope=allow_inactive_slope,
            )
        )
        token -= 1
    return tuple(sorted(shapes, key=lambda shape: (shape.start_frame, shape.real_base_event_indices)))


def _shape_is_non_zero(shape: EffectiveShape) -> bool:
    return any(point.value > MORPH_FRAME_OPEN_EPSILON for point in shape.control_points)


def _first_event_for_shape(
    shape: EffectiveShape,
    events_by_index: dict[int, EffectiveShapeEvent],
) -> EffectiveShapeEvent:
    events = tuple(
        events_by_index[index]
        for index in shape.real_base_event_indices
        if index in events_by_index
    )
    if not events:
        raise AdjustmentContractError(
            "shape is missing real effective events",
            safe_code="shape_event_missing",
            safe_field_code="real_base_event_indices",
            safe_phase="manual_crossfade",
        )
    return min(events, key=lambda event: (event.peak_frame, event.base_event_index))


def _manual_crossfade_context_for_shape(
    shapes: Sequence[EffectiveShape],
    source_shape_index: int,
    effective_events: tuple[EffectiveShapeEvent, ...],
) -> _ManualCrossfadeContext | None:
    if not 0 <= source_shape_index < len(shapes):
        return None
    source_shape = shapes[source_shape_index]
    if source_shape.shape_kind.startswith("long_vowel_"):
        return None
    if source_shape.resolved_tail is None or not _shape_is_non_zero(source_shape):
        return None

    target_shape_index = None
    for index in range(source_shape_index + 1, len(shapes)):
        if _shape_is_non_zero(shapes[index]):
            target_shape_index = index
            break
    if target_shape_index is None:
        return None

    target_shape = shapes[target_shape_index]
    if target_shape.shape_kind.startswith("long_vowel_"):
        return None
    if target_shape.vowel == source_shape.vowel:
        return None

    events_by_index = {event.base_event_index: event for event in effective_events}
    target_event = _first_event_for_shape(target_shape, events_by_index)
    limit = target_event.peak_frame

    for index in range(target_shape_index + 1, len(shapes)):
        third_shape = shapes[index]
        if third_shape.shape_kind.startswith("long_vowel_"):
            continue
        if not _shape_is_non_zero(third_shape):
            continue
        third_event = _first_event_for_shape(third_shape, events_by_index)
        limit = min(limit, third_event.start_frame - 1)
        break

    return _ManualCrossfadeContext(
        source_shape_index=source_shape_index,
        target_shape_index=target_shape_index,
        source_base_event_index=source_shape.resolved_tail.tail_base_event_index,
        target_base_event_index=target_event.base_event_index,
        target_open_start_frame=target_event.start_frame,
        target_open_end_frame=target_event.peak_frame,
        crossfade_limit_frame=limit,
    )


def _has_manual_crossfade_intent(adjustment: EventAdjustment | None) -> bool:
    return adjustment is not None and (
        adjustment.end_offset_frames > 0
        or adjustment.hold_frames is not None
        or adjustment.softness_frames is not None
    )


def _apply_manual_crossfade_extensions(
    shapes: tuple[EffectiveShape, ...],
    *,
    raw_adjusted_events: tuple[EffectiveShapeEvent, ...],
    effective_events: tuple[EffectiveShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
    shape_parameters: ShapeParameters,
) -> tuple[EffectiveShape, ...]:
    result = list(shapes)
    adjustments = {item.base_event_index: item for item in snapshot.adjustments}
    raw_by_index = {event.base_event_index: event for event in raw_adjusted_events}
    effective_by_index = {event.base_event_index: event for event in effective_events}

    for source_shape_index, source_shape in enumerate(shapes):
        context = _manual_crossfade_context_for_shape(
            shapes,
            source_shape_index,
            effective_events,
        )
        if context is None:
            continue
        adjustment = adjustments.get(context.source_base_event_index)
        if not _has_manual_crossfade_intent(adjustment):
            continue
        if (
            adjustment is not None
            and adjustment.end_offset_frames > 0
            and raw_by_index[context.source_base_event_index].end_frame
            > context.crossfade_limit_frame
            and not adjustment.manual_overlap_limit_override
        ):
            raise AdjustmentContractError(
                "positive end offset exceeds the manual crossfade range",
                safe_code="manual_crossfade_limit_exceeded",
                safe_field_code="end_offset_frames",
                safe_phase="manual_crossfade",
                event_index=context.source_base_event_index,
                source_event_index=context.target_base_event_index,
                event_role="source",
                source_event_role="neighbor",
            )
        if adjustment is None or (
            adjustment.hold_frames is None
            and adjustment.softness_frames is None
        ):
            continue

        group = tuple(
            effective_by_index[index]
            for index in source_shape.real_base_event_indices
        )
        synthetic_token = (
            source_shape.internal_shape_source_tokens[0]
            if source_shape.internal_shape_source_tokens
            else None
        )
        result[source_shape_index] = _shape_for_group(
            group,
            adjustment_by_index=adjustments,
            shape_parameters=shape_parameters,
            next_shape_start_frame=None,
            synthetic_token=synthetic_token,
            manual_extension_limit_frame=context.crossfade_limit_frame,
        )
    return tuple(result)


def _manual_comparison_snapshot(
    snapshot: AdjustmentLayerSnapshot,
) -> AdjustmentLayerSnapshot:
    adjustments: list[EventAdjustment] = []
    for item in snapshot.adjustments:
        comparison = replace(
            item,
            end_offset_frames=(
                0 if item.end_offset_frames > 0 else item.end_offset_frames
            ),
            hold_frames=None,
            softness_frames=None,
        )
        if not comparison.is_empty:
            adjustments.append(comparison)
    return AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=snapshot.base_plan_identity,
        adjustments=tuple(adjustments),
    )


def _shape_output_identity(shape: EffectiveShape) -> tuple[object, ...]:
    return (
        shape.vowel,
        shape.real_base_event_indices,
        shape.internal_shape_source_tokens,
        tuple(
            (point.frame_no, point.value, point.point_kind)
            for point in shape.control_points
        ),
    )


def _shape_for_source_event(
    shapes: Sequence[EffectiveShape],
    source_base_event_index: int,
) -> EffectiveShape | None:
    matches = tuple(
        shape
        for shape in shapes
        if source_base_event_index in shape.real_base_event_indices
    )
    return matches[0] if len(matches) == 1 else None


def _source_closing_start_point(
    shape: EffectiveShape,
) -> ShapeControlPoint | None:
    for point in reversed(shape.control_points[:-1]):
        if (
            point.value > MORPH_FRAME_OPEN_EPSILON
            and point.point_kind != "slope_mid"
        ):
            return point
    return None


def _build_manual_crossfade_metadata(
    final_shapes: tuple[EffectiveShape, ...],
    comparison_shapes: tuple[EffectiveShape, ...],
    *,
    effective_events: tuple[EffectiveShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
) -> tuple[ManualCrossfadeMetadata, ...]:
    adjustments = {item.base_event_index: item for item in snapshot.adjustments}
    metadata: list[ManualCrossfadeMetadata] = []

    for source_shape_index, source_shape in enumerate(final_shapes):
        context = _manual_crossfade_context_for_shape(
            final_shapes,
            source_shape_index,
            effective_events,
        )
        if context is None:
            continue
        adjustment = adjustments.get(context.source_base_event_index)
        if not _has_manual_crossfade_intent(adjustment):
            continue
        comparison_shape = _shape_for_source_event(
            comparison_shapes,
            context.source_base_event_index,
        )
        if (
            comparison_shape is not None
            and _shape_output_identity(comparison_shape)
            == _shape_output_identity(source_shape)
        ):
            continue

        source_end = source_shape.control_points[-1]
        source_closing_start = _source_closing_start_point(source_shape)
        if (
            source_end.value > MORPH_FRAME_OPEN_EPSILON
            or source_closing_start is None
        ):
            continue
        overlap_start = max(
            source_closing_start.frame_no,
            context.target_open_start_frame + 1,
        )
        overlap_end = min(
            source_end.frame_no - 1,
            context.crossfade_limit_frame,
        )
        if overlap_start > overlap_end:
            continue

        target_shape = final_shapes[context.target_shape_index]
        high_by_key: dict[tuple[int, str], float] = {}
        for point in target_shape.control_points:
            if (
                overlap_start <= point.frame_no <= overlap_end
                and point.value >= 0.95
            ):
                key = (point.frame_no, target_shape.vowel)
                high_by_key[key] = max(high_by_key.get(key, 0.0), point.value)
        high_target_keyframes = tuple(
            ManualCrossfadeKeyframeNotice(frame_no, vowel, value)
            for (frame_no, vowel), value in sorted(high_by_key.items())
        )
        metadata.append(
            ManualCrossfadeMetadata(
                source_base_event_index=context.source_base_event_index,
                target_base_event_index=context.target_base_event_index,
                source_vowel=source_shape.vowel,
                target_vowel=target_shape.vowel,
                overlap_start_frame=overlap_start,
                overlap_end_frame=overlap_end,
                high_target_keyframes=high_target_keyframes,
            )
        )
    return tuple(
        sorted(
            metadata,
            key=lambda item: (
                item.source_base_event_index,
                item.target_base_event_index,
            ),
        )
    )


def _validate_active_slope_overrides(
    shapes: tuple[EffectiveShape, ...],
    snapshot: AdjustmentLayerSnapshot,
) -> None:
    midpoint_by_tail = {
        shape.resolved_tail.tail_base_event_index: (
            shape.resolved_tail.has_slope_midpoint,
            shape.shape_kind,
        )
        for shape in shapes
        if shape.resolved_tail is not None
    }
    for item in snapshot.adjustments:
        if (
            item.slope_ratio is not None
            and not midpoint_by_tail.get(item.base_event_index, (False, ""))[0]
            and midpoint_by_tail.get(item.base_event_index, (False, ""))[1] != "long_vowel_decay"
        ):
            raise AdjustmentContractError(
                "slope override requires an effective softness midpoint",
                safe_code="slope_midpoint_missing",
                safe_field_code="slope_ratio",
                safe_phase="slope_validation",
                event_index=item.base_event_index,
            )


def resolve_manual_crossfade_end_offset_max(
    effective_plan: EffectiveShapePlan,
    base_event_index: int,
    *,
    source_duration_frames: int,
    adjustment_snapshot: AdjustmentLayerSnapshot | None = None,
) -> int:
    if not isinstance(effective_plan, EffectiveShapePlan):
        raise AdjustmentContractError("effective_plan must be EffectiveShapePlan")
    if (
        isinstance(base_event_index, bool)
        or not isinstance(base_event_index, int)
        or base_event_index < 0
    ):
        raise AdjustmentContractError("base_event_index must be a non-negative int")
    if (
        isinstance(source_duration_frames, bool)
        or not isinstance(source_duration_frames, int)
        or source_duration_frames < 0
    ):
        raise AdjustmentContractError("source_duration_frames must be a non-negative int")
    base_matches = tuple(
        event
        for event in effective_plan.base_events
        if event.base_event_index == base_event_index
    )
    if len(base_matches) != 1:
        raise AdjustmentContractError("base event is missing from effective plan")
    base = base_matches[0]
    fallback = source_duration_frames - base.end_frame
    snapshot = (
        effective_plan.canonical_adjustment_snapshot
        if adjustment_snapshot is None
        else adjustment_snapshot
    )
    if (
        not isinstance(snapshot, AdjustmentLayerSnapshot)
        or snapshot.base_plan_identity != effective_plan.base_plan_identity
    ):
        raise AdjustmentContractError("adjustment_snapshot differs from effective plan base")
    source_matches = tuple(
        (index, shape)
        for index, shape in enumerate(effective_plan.shapes)
        if base_event_index in shape.real_base_event_indices
    )
    if len(source_matches) != 1:
        return fallback
    source_shape_index, source_shape = source_matches[0]
    if (
        source_shape.resolved_tail is None
        or source_shape.resolved_tail.tail_base_event_index != base_event_index
    ):
        return fallback
    owner_adjustment = next(
        (
            item
            for item in snapshot.adjustments
            if item.base_event_index == base_event_index
        ),
        None,
    )
    if (
        owner_adjustment is not None
        and owner_adjustment.manual_overlap_limit_override
        and not source_shape.shape_kind.startswith("long_vowel_")
    ):
        same_vowel_limit = fallback
        for index, shape in enumerate(effective_plan.shapes):
            if index == source_shape_index or shape.vowel != source_shape.vowel:
                continue
            later_event_indices = tuple(
                event_index
                for event_index in shape.real_base_event_indices
                if event_index > base_event_index
            )
            if not later_event_indices:
                continue
            same_vowel_limit = min(
                same_vowel_limit,
                shape.start_frame - base.end_frame,
            )
        return max(0, same_vowel_limit)
    context = _manual_crossfade_context_for_shape(
        effective_plan.shapes,
        source_shape_index,
        effective_plan.effective_events,
    )
    if context is None:
        return fallback
    return max(0, min(fallback, context.crossfade_limit_frame - base.end_frame))


def _normalization_contract(
    shapes: tuple[EffectiveShape, ...],
    *,
    additional_required_zero_frames: Sequence[tuple[str, int]] = (),
) -> NormalizationContract:
    allowed = tuple((shape.vowel, shape.start_frame, shape.end_frame) for shape in shapes)
    required = {
        pair
        for shape in shapes
        for point in shape.control_points
        if point.value <= MORPH_FRAME_OPEN_EPSILON and point.point_kind in ("start_zero", "end_zero")
        for pair in ((shape.vowel, point.frame_no),)
    }
    required.update(additional_required_zero_frames)
    protected = tuple(
        (shape.vowel, start, end)
        for shape in shapes
        for start, end in shape.event_ranges
    )
    return NormalizationContract(
        allowed_non_zero_ranges=allowed,
        required_zero_frames=tuple(sorted(required, key=lambda item: (item[1], item[0]))),
        protected_event_ranges=protected,
    )


def _silence_core_boundary_zero_frames(
    shapes: Sequence[EffectiveShape],
    silence_core_frame_ranges: Sequence[tuple[int, int]],
) -> tuple[tuple[str, int], ...]:
    """Return zero keys that stop same-vowel interpolation through each core.

    Add the start boundary when a positive point precedes the core and the end
    boundary when a positive point follows it. Either side alone can otherwise
    interpolate through part of the silent interval.
    """

    result: set[tuple[str, int]] = set()
    vowels = {shape.vowel for shape in shapes}
    for start_frame, end_frame in silence_core_frame_ranges:
        if end_frame <= start_frame:
            continue
        for vowel in vowels:
            has_positive_before = any(
                shape.vowel == vowel
                and any(
                    point.frame_no < start_frame
                    and point.value > MORPH_FRAME_OPEN_EPSILON
                    for point in shape.control_points
                )
                for shape in shapes
            )
            has_positive_after = any(
                shape.vowel == vowel
                and any(
                    point.frame_no >= end_frame
                    and point.value > MORPH_FRAME_OPEN_EPSILON
                    for point in shape.control_points
                )
                for shape in shapes
            )
            if has_positive_before:
                result.add((vowel, start_frame))
            if has_positive_after:
                result.add((vowel, end_frame))
    return tuple(sorted(result, key=lambda item: (item[1], item[0])))


def _validate_required_zero_conflicts(
    shapes: tuple[EffectiveShape, ...],
    effective_events: tuple[EffectiveShapeEvent, ...] = (),
) -> None:
    required: dict[tuple[str, int], set[int]] = {}
    positive: dict[tuple[str, int], set[int]] = {}
    for shape_index, shape in enumerate(shapes):
        for point in shape.control_points:
            key = (shape.vowel, point.frame_no)
            if point.value <= MORPH_FRAME_OPEN_EPSILON and point.point_kind in ("start_zero", "end_zero"):
                required.setdefault(key, set()).add(shape_index)
            elif point.value > MORPH_FRAME_OPEN_EPSILON:
                positive.setdefault(key, set()).add(shape_index)
    shape_by_event = {
        event_index: shape_index
        for shape_index, shape in enumerate(shapes)
        for event_index in shape.real_base_event_indices
    }
    for event in effective_events:
        if event.peak_value <= MORPH_FRAME_OPEN_EPSILON:
            continue
        shape_index = shape_by_event.get(event.base_event_index)
        if shape_index is not None:
            positive.setdefault((event.vowel, event.peak_frame), set()).add(shape_index)
    for key, zero_shapes in required.items():
        positive_shapes = positive.get(key, set())
        if any(zero_shape != positive_shape for zero_shape in zero_shapes for positive_shape in positive_shapes):
            raise AdjustmentContractError(
                "required zero conflicts with a positive control point",
                safe_code="required_zero_positive_conflict",
                safe_field_code="required_zero_frames",
                safe_phase="required_zero_conflicts",
                safe_details={
                    "frame_start": key[1],
                    "reason_code": "required_zero_positive_conflict",
                },
            )


def _diagnostic_resolver_call(
    diagnostics: ResolverDiagnosticsCollector | None,
    phase: str,
    callback,
    *,
    pass_kind: str = "primary",
    fallback_code: str = "unknown_contract_failure",
    field_code: str = "unknown",
    failure_detail_provider: Callable[[], object | None] | None = None,
):
    """Run one existing resolver step while optionally observing its outcome."""

    if diagnostics is not None:
        diagnostics.phase_started(phase, pass_kind=pass_kind)
    try:
        result = callback()
    except Exception as error:
        ensure_safe_failure_metadata(
            error,
            phase=phase,
            pass_kind=pass_kind,
            fallback_code=fallback_code,
            field_code=field_code,
        )
        if diagnostics is not None:
            failure_detail = None
            if failure_detail_provider is not None:
                try:
                    failure_detail = failure_detail_provider()
                except Exception:
                    failure_detail = None
            diagnostics.phase_failed(
                phase,
                error,
                pass_kind=pass_kind,
                fallback_code=fallback_code,
                failure_detail=failure_detail,
            )
        raise
    if diagnostics is not None:
        event_count = len(result) if isinstance(result, (tuple, list, dict, set)) else None
        diagnostics.phase_completed(phase, pass_kind=pass_kind, event_count=event_count)
    return result


def _build_shapes_with_long_runs(
    *,
    raw_adjusted_events: tuple[EffectiveShapeEvent, ...],
    effective_events: tuple[EffectiveShapeEvent, ...],
    snapshot: AdjustmentLayerSnapshot,
    handoffs: tuple[ObservationHandoff, ...],
    shape_parameters: ShapeParameters,
    base_long_runs: tuple[EffectiveLongVowelRun, ...],
    excluded_indices: set[int] | None = None,
    silence_core_frame_ranges: Sequence[tuple[int, int]] = (),
    silence_clip_record_sink: list[dict[str, Any]] | None = None,
) -> tuple[tuple[EffectiveShape, ...], tuple[EffectiveLongVowelRun, ...]]:
    excluded = set(excluded_indices or ())
    long_indices = {
        index
        for run in base_long_runs
        for index in (run.source_base_event_index, *run.continuation_base_event_indices)
    }
    regular_shapes = _build_shapes(
        effective_events,
        snapshot,
        handoffs,
        shape_parameters,
        allow_inactive_slope=True,
        excluded_indices=long_indices | excluded,
    )
    effective_by_index = {event.base_event_index: event for event in effective_events}
    long_shapes: list[EffectiveShape] = []
    resolved_runs: list[EffectiveLongVowelRun] = []
    for base_run in base_long_runs:
        mode = _resolved_long_mode(base_run, snapshot, shape_parameters)
        run = replace(
            base_run,
            resolved_mode=mode,
            source_peak_frame=effective_by_index[base_run.source_base_event_index].peak_frame,
            terminal_end_frame=effective_by_index[base_run.terminal_base_event_index].end_frame,
            source_peak_value=effective_by_index[base_run.source_base_event_index].peak_value,
        )
        next_event = _next_shape_boundary_event(
            effective_events,
            run.terminal_base_event_index,
        )
        next_same_vowel_event = _next_same_vowel_boundary_event(
            effective_events,
            run.terminal_base_event_index,
            run.vowel,
        )
        next_start = None if next_event is None else next_event.start_frame
        next_same_vowel_start = (
            None if next_same_vowel_event is None else next_same_vowel_event.start_frame
        )
        next_same_vowel_starts_positive = (
            next_same_vowel_event is not None
            and next_same_vowel_event.peak_frame == next_same_vowel_event.start_frame
            and next_same_vowel_event.peak_value > MORPH_FRAME_OPEN_EPSILON
        )
        long_shapes.append(
            _shape_for_long_run(
                run,
                effective_events=effective_events,
                snapshot=snapshot,
                shape_parameters=shape_parameters,
                next_shape_start_frame=next_start,
                next_shape_vowel=None if next_event is None else next_event.vowel,
                next_same_vowel_start_frame=next_same_vowel_start,
                next_same_vowel_starts_positive=next_same_vowel_starts_positive,
            )
        )
        resolved_runs.append(run)
    baseline_shapes = tuple(
        sorted(
            (*regular_shapes, *long_shapes),
            key=lambda shape: (shape.start_frame, shape.real_base_event_indices),
        )
    )
    shapes = _apply_manual_crossfade_extensions(
        baseline_shapes,
        raw_adjusted_events=raw_adjusted_events,
        effective_events=effective_events,
        snapshot=snapshot,
        shape_parameters=shape_parameters,
    )
    shapes = _clip_shapes_to_silence_cores(
        shapes,
        silence_core_frame_ranges,
        record_sink=silence_clip_record_sink,
    )
    _validate_active_slope_overrides(shapes, snapshot)
    return shapes, tuple(resolved_runs)


def resolve_effective_shape_plan(
    base_input: BaseTimingPlanInput,
    adjustment_snapshot: AdjustmentLayerSnapshot | Sequence[EventAdjustment] | None = None,
    *,
    diagnostics: ResolverDiagnosticsCollector | None = None,
    resolver_diagnostics: ResolverDiagnosticsCollector | None = None,
) -> EffectiveShapePlan:
    return _build_effective_shape_plan(base_input, adjustment_snapshot,
        diagnostics=diagnostics, resolver_diagnostics=resolver_diagnostics)


def _build_effective_shape_plan(
    base_input: BaseTimingPlanInput,
    adjustment_snapshot: AdjustmentLayerSnapshot | Sequence[EventAdjustment] | None = None,
    *,
    diagnostics: ResolverDiagnosticsCollector | None = None,
    resolver_diagnostics: ResolverDiagnosticsCollector | None = None,
    _defer_zero_conflicts: bool = False,
) -> EffectiveShapePlan:
    if diagnostics is None:
        diagnostics = resolver_diagnostics
    if diagnostics is not None:
        diagnostics.start_attempt(caller="resolver", plan_origin="resolved")
    if not isinstance(base_input, BaseTimingPlanInput):
        error = AdjustmentContractError(
            "base_input must be BaseTimingPlanInput",
            safe_code="base_input_type_invalid",
            safe_field_code="base_input",
            safe_phase="resolver_input",
            safe_pass_kind="primary",
        )
        if diagnostics is not None:
            diagnostics.phase_started("resolver_input")
            diagnostics.phase_failed("resolver_input", error, fallback_code="base_input_type_invalid")
        raise error
    if diagnostics is not None:
        diagnostics.set_input_summary(
            timeline_count=len(base_input.timeline),
            observation_count=(
                None if base_input.observations is None else len(base_input.observations)
            ),
            source_duration_frames=base_input.source_duration_frames,
            observations_present=base_input.observations is not None,
            timeline_present=True,
        )
        diagnostics.phase_started("resolver_input")
        diagnostics.phase_completed("resolver_input")
        diagnostics.phase_started("shape_parameters")
        diagnostics.phase_completed("shape_parameters")
    events = _diagnostic_resolver_call(
        diagnostics,
        "base_events",
        lambda: _base_events(base_input),
        fallback_code="base_input_contract_error",
        field_code="timeline_point",
    )
    base_long_runs = _diagnostic_resolver_call(
        diagnostics,
        "long_runs",
        lambda: _long_vowel_runs(events, base_input.shape_parameters),
        fallback_code="long_source_missing",
        field_code="long_vowel_source",
    )
    silence_core_frame_ranges = _silence_core_ranges_from_observations(
        base_input.observations
    )
    long_indices = {
        index
        for run in base_long_runs
        for index in (run.source_base_event_index, *run.continuation_base_event_indices)
    }
    identity = _diagnostic_resolver_call(
        diagnostics,
        "base_identity",
        lambda: build_base_plan_identity(base_input),
        pass_kind="identity_validation",
        fallback_code="identity_contract_invalid",
        field_code="base_plan_identity",
    )
    snapshot = _diagnostic_resolver_call(
        diagnostics,
        "snapshot_canonicalize",
        lambda: _canonical_snapshot(base_input, identity, adjustment_snapshot, events),
        fallback_code="snapshot_schema_invalid",
        field_code="adjustment_snapshot",
    )
    _diagnostic_resolver_call(
        diagnostics,
        "adjustment_ownership",
        lambda: _validate_long_adjustment_ownership(events, snapshot),
        fallback_code="long_adjustment_ownership_invalid",
        field_code="adjustment_ownership",
    )
    raw_adjusted_events = _diagnostic_resolver_call(
        diagnostics,
        "adjustment_apply",
        lambda: _apply_event_adjustments(base_input, events, snapshot),
        fallback_code="adjusted_frame_order_invalid",
        field_code="frame_order",
    )
    adjusted_interval_indices = {
        item.base_event_index
        for item in snapshot.adjustments
        if item.peak_value is not None
        or item.start_offset_frames != 0
        or item.end_offset_frames != 0
    }
    handoffs = _diagnostic_resolver_call(
        diagnostics,
        "handoff_candidates",
        lambda: _candidate_handoffs(
            base_input,
            adjusted_interval_indices,
            excluded_indices=long_indices,
        ),
        fallback_code="unknown_contract_failure",
        field_code="observation",
    )
    effective_events = _diagnostic_resolver_call(
        diagnostics,
        "handoff_apply",
        lambda: _resolve_close_peak_values(
            base_input,
            _apply_cross_vowel_handoffs(raw_adjusted_events, handoffs),
        ),
        fallback_code="unknown_contract_failure",
        field_code="observation",
    )
    _diagnostic_resolver_call(
        diagnostics,
        "manual_overlap_ownership",
        lambda: _validate_manual_overlap_override_ownership(
            effective_events, snapshot, long_indices
        ),
        fallback_code="manual_overlap_override_owner_invalid",
        field_code="manual_overlap_limit_override",
    )
    silence_clip_records: list[dict[str, Any]] = []
    shapes, resolved_runs = _diagnostic_resolver_call(
        diagnostics,
        "long_shapes",
        lambda: _build_shapes_with_long_runs(
            raw_adjusted_events=raw_adjusted_events,
            effective_events=effective_events,
            snapshot=snapshot,
            handoffs=handoffs,
            shape_parameters=base_input.shape_parameters,
            base_long_runs=base_long_runs,
            excluded_indices=set(),
            silence_core_frame_ranges=silence_core_frame_ranges,
            silence_clip_record_sink=silence_clip_records,
        ),
        fallback_code="long_terminal_order_invalid",
        field_code="terminal_end_frame",
    )
    admission_detail_holder: dict[str, object] = {}
    admissions, rejected_event_indices = _diagnostic_resolver_call(
        diagnostics,
        "silence_admission",
        lambda: _build_event_silence_admissions(
            base_input,
            effective_events,
            shapes,
            snapshot,
            base_events=events,
            long_runs=base_long_runs,
            failure_detail_sink=(admission_detail_holder if diagnostics is not None else None),
            _defer_boundary_validation=_defer_zero_conflicts,
        ),
        fallback_code="admission_range_invalid",
        field_code="effective_frame_range",
        failure_detail_provider=(
            lambda: admission_detail_holder.get("value")
            if diagnostics is not None
            else None
        ),
    )
    if rejected_event_indices:
        shapes, _ = _diagnostic_resolver_call(
            diagnostics,
            "silence_admission",
            lambda: _build_shapes_with_long_runs(
                raw_adjusted_events=raw_adjusted_events,
                effective_events=effective_events,
                snapshot=snapshot,
                handoffs=handoffs,
                shape_parameters=base_input.shape_parameters,
                base_long_runs=base_long_runs,
                excluded_indices=rejected_event_indices,
                silence_core_frame_ranges=silence_core_frame_ranges,
            ),
            pass_kind="silence_rebuild",
            fallback_code="admission_range_invalid",
            field_code="effective_frame_range",
        )
    admissions = _diagnostic_resolver_call(
        diagnostics,
        "silence_rebind",
        lambda: _rebind_event_silence_admissions(admissions, shapes),
        fallback_code="admission_shape_id_invalid",
        field_code="origin_shape_id",
    )

    comparison_snapshot = _manual_comparison_snapshot(snapshot)
    comparison_raw_events = _diagnostic_resolver_call(
        diagnostics,
        "adjustment_apply",
        lambda: _apply_event_adjustments(
            base_input,
            events,
            comparison_snapshot,
        ),
        pass_kind="manual_comparison",
        fallback_code="adjusted_frame_order_invalid",
        field_code="frame_order",
    )
    comparison_adjusted_indices = {
        item.base_event_index
        for item in comparison_snapshot.adjustments
        if item.peak_value is not None
        or item.start_offset_frames != 0
        or item.end_offset_frames != 0
    }
    comparison_handoffs = _diagnostic_resolver_call(
        diagnostics,
        "handoff_candidates",
        lambda: _candidate_handoffs(
            base_input,
            comparison_adjusted_indices,
            excluded_indices=long_indices,
        ),
        pass_kind="manual_comparison",
        fallback_code="unknown_contract_failure",
        field_code="observation",
    )
    comparison_effective_events = _diagnostic_resolver_call(
        diagnostics,
        "handoff_apply",
        lambda: _resolve_close_peak_values(
            base_input,
            _apply_cross_vowel_handoffs(
                comparison_raw_events,
                comparison_handoffs,
            ),
        ),
        pass_kind="manual_comparison",
        fallback_code="unknown_contract_failure",
        field_code="observation",
    )
    comparison_shapes, _ = _diagnostic_resolver_call(
        diagnostics,
        "long_shapes",
        lambda: _build_shapes_with_long_runs(
            raw_adjusted_events=comparison_raw_events,
            effective_events=comparison_effective_events,
            snapshot=comparison_snapshot,
            handoffs=comparison_handoffs,
            shape_parameters=base_input.shape_parameters,
            base_long_runs=base_long_runs,
            excluded_indices=rejected_event_indices,
            silence_core_frame_ranges=silence_core_frame_ranges,
        ),
        pass_kind="manual_comparison",
        fallback_code="long_terminal_order_invalid",
        field_code="terminal_end_frame",
    )
    manual_crossfades = _diagnostic_resolver_call(
        diagnostics,
        "manual_crossfade",
        lambda: _build_manual_crossfade_metadata(
            shapes,
            comparison_shapes,
            effective_events=effective_events,
            snapshot=snapshot,
        ),
        fallback_code="manual_crossfade_limit_exceeded",
        field_code="end_offset_frames",
    )
    if not _defer_zero_conflicts:
        _diagnostic_resolver_call(
            diagnostics,
            "required_zero_conflicts",
            lambda: _validate_required_zero_conflicts(shapes, effective_events),
            fallback_code="required_zero_positive_conflict",
            field_code="required_zero_frames",
        )
    additional_required_zero_frames = _diagnostic_resolver_call(
        diagnostics,
        "normalization_contract",
        lambda: _required_zero_frames_from_admissions(admissions),
        fallback_code="unknown_contract_failure",
        field_code="normalization_contract",
    )
    silence_core_boundary_zero_frames = _silence_core_boundary_zero_frames(
        shapes,
        silence_core_frame_ranges,
    )
    additional_required_zero_frames = tuple(
        sorted(
            set(additional_required_zero_frames).union(
                silence_core_boundary_zero_frames,
                {
                    (shape.vowel, frame_no)
                    for shape in shapes
                    for start_frame, end_frame in silence_core_frame_ranges
                    for frame_no in (start_frame, end_frame)
                    if shape.start_frame <= frame_no <= shape.end_frame
                }
            ),
            key=lambda item: (item[1], item[0]),
        )
    )
    plan = EffectiveShapePlan(
        base_plan_identity=identity,
        canonical_adjustment_snapshot=snapshot,
        base_events=events,
        effective_events=effective_events,
        shapes=shapes,
        observation_handoffs=handoffs,
        normalization_contract=_normalization_contract(
            shapes,
            additional_required_zero_frames=additional_required_zero_frames,
        ),
        event_silence_admissions=admissions,
        manual_crossfades=manual_crossfades,
        long_vowel_runs=tuple(resolved_runs),
        shape_parameters=base_input.shape_parameters,
        silence_policy=SILENCE_POLICY_ACOUSTIC_CORE_PRECEDENCE,
        silence_core_frame_ranges=silence_core_frame_ranges,
        silence_clip_records=tuple(silence_clip_records),
    )
    if diagnostics is not None:
        diagnostics.phase_started("plan_assemble")
        diagnostics.phase_completed("plan_assemble")
        diagnostics.complete_attempt()
    return plan


def apply_adjustment_update(
    base_input: BaseTimingPlanInput,
    current_snapshot: AdjustmentLayerSnapshot,
    requested_change: EventAdjustment,
    *,
    defer_automatic_zero_conflicts: bool = False,
) -> AdjustmentUpdateResult:
    if current_snapshot.base_plan_identity != build_base_plan_identity(base_input):
        raise AdjustmentContractError("adjustment snapshot base identity mismatch")
    requested = {
        item.base_event_index: item for item in current_snapshot.adjustments
    }
    requested[requested_change.base_event_index] = requested_change
    events = _base_events(base_input)
    canonical = canonicalize_adjustment_snapshot(
        current_snapshot.base_plan_identity,
        requested.values(),
        base_peak_values=tuple(event.peak_value for event in events),
        closing_hold_frames=base_input.shape_parameters.closing_hold_frames,
        closing_softness_frames=base_input.shape_parameters.closing_softness_frames,
    )
    _validate_long_adjustment_ownership(events, canonical)

    trial = _apply_event_adjustments(base_input, events, canonical)
    long_runs = _long_vowel_runs(events, base_input.shape_parameters)
    long_indices = {
        index
        for run in long_runs
        for index in (run.source_base_event_index, *run.continuation_base_event_indices)
    }
    tail_indices = {
        group[-1].base_event_index
        for group in _group_events(tuple(event for event in trial if event.base_event_index not in long_indices))
    }
    tail_indices.update(run.terminal_base_event_index for run in long_runs)
    removed_tail: list[int] = []
    cleaned: list[EventAdjustment] = []
    for item in canonical.adjustments:
        if item.base_event_index not in tail_indices and (
            item.hold_frames is not None
            or item.softness_frames is not None
            or item.slope_ratio is not None
            or item.manual_overlap_limit_override
        ):
            removed_tail.append(item.base_event_index)
            item = replace(
                item,
                hold_frames=None,
                softness_frames=None,
                slope_ratio=None,
                manual_overlap_limit_override=False,
            )
        if not item.is_empty:
            cleaned.append(item)
    canonical = AdjustmentLayerSnapshot(
        schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
        base_plan_identity=canonical.base_plan_identity,
        adjustments=tuple(cleaned),
    )

    slope_indices = {
        item.base_event_index
        for item in canonical.adjustments
        if item.slope_ratio is not None
    }
    removed_slope: list[int] = []
    if slope_indices:
        adjustments_without_slopes: list[EventAdjustment] = []
        for item in canonical.adjustments:
            item_without_slope = replace(item, slope_ratio=None)
            if not item_without_slope.is_empty:
                adjustments_without_slopes.append(item_without_slope)
        without_slopes = AdjustmentLayerSnapshot(
            schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
            base_plan_identity=canonical.base_plan_identity,
            adjustments=tuple(adjustments_without_slopes),
        )
        probe_plan = _build_effective_shape_plan(base_input, without_slopes,
            _defer_zero_conflicts=defer_automatic_zero_conflicts)
        midpoint_by_tail = {
            shape.resolved_tail.tail_base_event_index: (
                shape.resolved_tail.has_slope_midpoint,
                shape.shape_kind,
            )
            for shape in probe_plan.shapes
            if shape.resolved_tail is not None
        }
        final_adjustments: list[EventAdjustment] = []
        for item in canonical.adjustments:
            if (
                item.base_event_index in slope_indices
                and not midpoint_by_tail.get(item.base_event_index, (False, ""))[0]
                and midpoint_by_tail.get(item.base_event_index, (False, ""))[1] != "long_vowel_decay"
            ):
                removed_slope.append(item.base_event_index)
                item = replace(item, slope_ratio=None)
            if not item.is_empty:
                final_adjustments.append(item)
        canonical = AdjustmentLayerSnapshot(
            schema_version=ADJUSTMENT_SNAPSHOT_SCHEMA,
            base_plan_identity=canonical.base_plan_identity,
            adjustments=tuple(final_adjustments),
        )

    plan = _build_effective_shape_plan(base_input, canonical,
        _defer_zero_conflicts=defer_automatic_zero_conflicts)
    return AdjustmentUpdateResult(
        canonical_snapshot=canonical,
        removed_tail_override_event_indices=tuple(sorted(removed_tail)),
        removed_slope_override_event_indices=tuple(sorted(removed_slope)),
        effective_plan=plan,
    )
