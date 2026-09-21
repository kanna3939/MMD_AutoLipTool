"""Public compatibility facade for the pre-MS21 Preview shape path.

The active MS21 resolver lives in ``src.core.effective_shape_plan``.  These
aliases keep the existing Preview contract stable while writer internals are
retained for legacy callers during the staged MS21 migration.
"""

from .writer import (
    AsymmetricTrapezoidSpec,
    GroupedNearbyVowelEvents,
    MORPH_FRAME_OPEN_EPSILON,
    MultiPointEnvelopeSpec,
    SUPPORTED_MORPHS,
    VMD_FPS,
    _apply_closing_hold_to_trapezoid_spec as apply_closing_hold_to_trapezoid_spec,
    _apply_closing_softness_to_trapezoid_spec as apply_closing_softness_to_trapezoid_spec,
    _apply_cross_vowel_transition_candidates_to_points as apply_cross_vowel_transition_candidates_to_points,
    _build_adjusted_trapezoid_spec as build_adjusted_trapezoid_spec,
    _build_existing_point_morph_frames_with_metadata as build_existing_point_morph_frames_with_metadata,
    _build_ms11_3_group_morph_frames_with_spec as build_ms11_3_group_morph_frames_with_spec,
    _build_same_vowel_span_adjusted_points as build_same_vowel_span_adjusted_points,
    _first_non_zero_shape_start_frame_in_group as first_non_zero_shape_start_frame_in_group,
    _group_nearby_same_vowel_events_with_source_indices as group_nearby_same_vowel_events_with_source_indices,
    _is_ms11_3_attemptable_group as is_ms11_3_attemptable_group,
    _normalize_closing_hold_frames as normalize_closing_hold_frames,
    _normalize_closing_softness_frames as normalize_closing_softness_frames,
    _resolve_effective_final_closing_hold_frames as resolve_effective_final_closing_hold_frames,
    _resolve_effective_final_closing_softness_frames as resolve_effective_final_closing_softness_frames,
)

__all__ = [
    "AsymmetricTrapezoidSpec",
    "GroupedNearbyVowelEvents",
    "MORPH_FRAME_OPEN_EPSILON",
    "MultiPointEnvelopeSpec",
    "SUPPORTED_MORPHS",
    "VMD_FPS",
    "apply_closing_hold_to_trapezoid_spec",
    "apply_closing_softness_to_trapezoid_spec",
    "apply_cross_vowel_transition_candidates_to_points",
    "build_adjusted_trapezoid_spec",
    "build_existing_point_morph_frames_with_metadata",
    "build_ms11_3_group_morph_frames_with_spec",
    "build_same_vowel_span_adjusted_points",
    "first_non_zero_shape_start_frame_in_group",
    "group_nearby_same_vowel_events_with_source_indices",
    "is_ms11_3_attemptable_group",
    "normalize_closing_hold_frames",
    "normalize_closing_softness_frames",
    "resolve_effective_final_closing_hold_frames",
    "resolve_effective_final_closing_softness_frames",
]
