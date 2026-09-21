from __future__ import annotations

from typing import Protocol, Sequence

from . import writer as _writer


class ControlPointLike(Protocol):
    frame_no: int
    value: float


class ShapeLike(Protocol):
    vowel: str
    control_points: Sequence[ControlPointLike]


class NormalizationContractLike(Protocol):
    allowed_non_zero_ranges: Sequence[tuple[str, int, int]]
    required_zero_frames: Sequence[tuple[str, int]]
    protected_event_ranges: Sequence[tuple[str, int, int]]


class EffectiveShapePlanLike(Protocol):
    shapes: Sequence[ShapeLike]
    normalization_contract: NormalizationContractLike


def _range_mapping(
    values: Sequence[tuple[str, int, int]],
) -> dict[str, list[tuple[int, int]]]:
    result: dict[str, list[tuple[int, int]]] = {}
    for vowel, start_frame, end_frame in values:
        result.setdefault(str(vowel), []).append((int(start_frame), int(end_frame)))
    return result


def _required_zero_mapping(
    values: Sequence[tuple[str, int]],
) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    for vowel, frame_no in values:
        result.setdefault(str(vowel), set()).add(int(frame_no))
    return result


def build_morph_frames_from_effective_shape_plan(
    effective_plan: EffectiveShapePlanLike,
    apply_final_normalization: bool = True,
    *,
    output_morph_names: Sequence[str] = _writer.SUPPORTED_MORPHS,
) -> tuple[tuple[int, str, float], ...]:
    """Convert a resolved plan without repeating candidate/group/tail logic."""
    normalized_output_morph_names = _writer._validate_output_morph_names(
        output_morph_names
    )
    frames = [
        (int(point.frame_no), str(shape.vowel), float(point.value))
        for shape in effective_plan.shapes
        for point in shape.control_points
    ]
    contract = getattr(effective_plan, "normalization_contract", None)
    required_zero_frames = _required_zero_mapping(
        getattr(contract, "required_zero_frames", ())
    )
    silence_core_ranges = tuple(
        getattr(effective_plan, "silence_core_frame_ranges", ()) or ()
    )
    for vowel, frame_numbers in required_zero_frames.items():
        frames.extend(
            (int(frame_no), vowel, 0.0)
            for frame_no in frame_numbers
            if any(start <= frame_no <= end for start, end in silence_core_ranges)
        )
    frames.sort(key=lambda item: (item[0], item[1]))
    if not apply_final_normalization:
        return _writer._map_morph_frames_to_output_names(
            frames,
            normalized_output_morph_names,
        )

    contract = effective_plan.normalization_contract
    normalized = _writer._apply_final_morph_frame_normalization(
        frames,
        protected_event_ranges=_range_mapping(contract.protected_event_ranges),
        allowed_non_zero_ranges=_range_mapping(contract.allowed_non_zero_ranges),
        required_zero_frames=_required_zero_mapping(contract.required_zero_frames),
    )
    return _writer._map_morph_frames_to_output_names(
        normalized,
        normalized_output_morph_names,
    )
