from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    _shape_value_at_frame,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import EventAdjustment
from src.gui_wx.main_frame import _build_debug_silence_observations
from src.vmd_writer import VowelTimelinePoint
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)


def _observation(
    event_index: int,
    *,
    core_ranges: tuple[tuple[int, int], ...] = (),
    positive_ranges: tuple[tuple[int, int], ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        event_index=event_index,
        vowel="あ",
        silence_core_frame_ranges=core_ranges,
        positive_core_frame_ranges=positive_ranges,
        base_event_silence_core_overlap=bool(core_ranges),
        is_bridgeable_micro_gap_candidate=False,
        is_bridgeable_same_vowel_micro_gap_candidate=False,
        is_same_vowel_burst_candidate=False,
        is_bridgeable_cross_vowel_transition_candidate=False,
        is_cross_vowel_zero_run_continuity_floor_candidate=False,
        previous_non_zero_event_index=None,
        next_non_zero_event_index=None,
        span_start_index=None,
        span_end_index=None,
        rms_window_times_sec=(),
        rms_window_values=(),
    )


def test_regular_event_in_silence_core_is_clipped_and_required_zero_is_propagated() -> None:
    base_input = BaseTimingPlanInput(
        timeline=(
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                value=0.5,
                start_sec=0.9,
                end_sec=1.1,
            ),
        ),
        observations=(_observation(0, core_ranges=((29, 32),), positive_ranges=((30, 31),)),),
        source_duration_frames=90,
    )

    plan = resolve_effective_shape_plan(base_input)

    admission = plan.event_silence_admissions[0]
    assert admission.enabled is True
    assert admission.origin_shape_id == 0
    assert admission.rejection_reason_code is None
    assert admission.positive_core_frame_ranges == ()
    assert admission.required_zero_frame_ranges == ()
    assert plan.shapes
    assert all(
        _shape_value_at_frame(plan.shapes[0], frame_no) == 0.0
        for frame_no in range(29, 32)
    )
    assert ("あ", 29) in plan.normalization_contract.required_zero_frames
    assert ("あ", 32) in plan.normalization_contract.required_zero_frames
    assert plan.silence_clip_records[0]["reason_code"] == "shape_split_by_silence_core"


def test_long_vowel_role_is_clipped_by_acoustic_silence() -> None:
    timeline = (
        VowelTimelinePoint(
            time_sec=0.9,
            vowel="あ",
            value=0.5,
            start_sec=0.8,
            end_sec=1.0,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            time_sec=1.1,
            vowel="あ",
            value=0.5,
            start_sec=1.0,
            end_sec=1.2,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
    )
    observations = (
        _observation(0, core_ranges=((27, 29),), positive_ranges=((27, 28),)),
        _observation(1),
    )

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(timeline=timeline, observations=observations, source_duration_frames=90)
    )

    source_admission = plan.event_silence_admissions[0]
    assert source_admission.long_vowel_role == "long_source"
    assert source_admission.enabled is True
    assert source_admission.rejection_reason_code is None
    assert plan.shapes
    assert all(
        _shape_value_at_frame(plan.shapes[0], frame_no) == 0.0
        for frame_no in range(27, 29)
    )


@pytest.mark.parametrize("mode", ("hold", "decay"))
def test_long_vowel_modes_cannot_reopen_an_acoustic_silence_core(mode: str) -> None:
    timeline = (
        VowelTimelinePoint(
            time_sec=0.9,
            vowel="あ",
            value=0.6,
            start_sec=0.8,
            end_sec=1.0,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            time_sec=1.1,
            vowel="あ",
            value=0.4,
            start_sec=1.0,
            end_sec=1.3,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=timeline,
            observations=(
                _observation(0, core_ranges=((29, 34),), positive_ranges=((30, 33),)),
                _observation(1),
            ),
            source_duration_frames=90,
            shape_parameters=ShapeParameters(0, 0, mode),
        )
    )

    assert plan.silence_policy == "acoustic_core_precedence"
    assert plan.silence_clip_records
    for shape in plan.shapes:
        assert all(
            _shape_value_at_frame(shape, frame_no) == 0.0
            for frame_no in range(29, 34)
        )


def test_writer_gets_explicit_zero_keys_between_separate_same_vowel_shapes() -> None:
    timeline = (
        VowelTimelinePoint(
            time_sec=1.0,
            vowel="あ",
            value=0.5,
            start_sec=0.9,
            end_sec=1.1,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            time_sec=1.5,
            vowel="あ",
            value=0.4,
            start_sec=1.4,
            end_sec=1.6,
            vowel_token_index=1,
        ),
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=timeline,
            observations=(
                _observation(0),
                _observation(1, core_ranges=((34, 42),)),
            ),
            source_duration_frames=90,
        )
    )

    writer_points = build_morph_frames_from_effective_shape_plan(plan, False)
    writer_values = {
        frame_no: value
        for frame_no, vowel, value in writer_points
        if vowel == "あ"
    }
    assert writer_values[34] == 0.0
    assert writer_values[42] == 0.0
    assert all(writer_values.get(frame_no, 0.0) <= 1e-9 for frame_no in range(34, 43))


def test_non_empty_manual_adjustment_is_an_explicit_admission_allowance() -> None:
    base_input = BaseTimingPlanInput(
        timeline=(
            VowelTimelinePoint(
                time_sec=1.0,
                vowel="あ",
                value=0.5,
                start_sec=0.9,
                end_sec=1.1,
            ),
        ),
        observations=(_observation(0, core_ranges=((29, 32),), positive_ranges=((30, 31),)),),
        source_duration_frames=90,
    )

    plan = resolve_effective_shape_plan(
        base_input,
        (EventAdjustment(base_event_index=0, peak_value=0.7),),
    )

    admission = plan.event_silence_admissions[0]
    assert admission.manual_adjustment_applied is True
    assert admission.enabled is True
    assert admission.rejection_reason_code is None
    assert plan.shapes

    rows = _build_debug_silence_observations(
        [
            {
                "start_sec": 29 / 30,
                "end_sec": 32 / 30,
                "coverage_status": "complete",
                "provenance_status": "complete",
            }
        ],
        [(29, "あ", 0.0), (30, "あ", 0.0), (31, "あ", 0.0)],
        effective_plan=plan,
    )
    assert rows[0]["result"] == "clear"
    assert rows[0]["reason_code"] == "clear_no_positive_opening"


def test_long_vowel_admission_is_explained_in_debug_classification() -> None:
    timeline = (
        VowelTimelinePoint(
            time_sec=0.9,
            vowel="あ",
            value=0.5,
            start_sec=0.8,
            end_sec=1.0,
            vowel_token_index=0,
        ),
        VowelTimelinePoint(
            time_sec=1.1,
            vowel="あ",
            value=0.5,
            start_sec=1.0,
            end_sec=1.2,
            vowel_token_index=1,
            is_long_vowel_continuation=True,
            long_vowel_source_token_index=0,
        ),
    )
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=timeline,
            observations=(
                _observation(0, core_ranges=((27, 29),), positive_ranges=((27, 28),)),
                _observation(1),
            ),
            source_duration_frames=90,
        )
    )

    rows = _build_debug_silence_observations(
        [
            {
                "start_sec": 27 / 30,
                "end_sec": 29 / 30,
                "coverage_status": "complete",
                "provenance_status": "complete",
            }
        ],
        [(27, "あ", 0.0), (28, "あ", 0.0)],
        effective_plan=plan,
    )

    assert rows[0]["result"] == "clear"
    assert rows[0]["reason_code"] == "clear_no_positive_opening"


def test_debug_admission_violation_is_reported_separately_from_handoff() -> None:
    admission = SimpleNamespace(
        event_index=65,
        vowel="あ",
        origin_shape_id=None,
        positive_point_kinds=("peak",),
        source_event_indices=(65,),
        effective_frame_range=(30, 31),
        base_event_silence_core_overlap=True,
        positive_core_frame_ranges=((30, 31),),
        long_vowel_role=None,
        manual_adjustment_applied=False,
        enabled=False,
        rejection_reason_code="base_event_overlaps_silence_core",
        required_zero_frame_ranges=((30, 31),),
    )
    plan = SimpleNamespace(event_silence_admissions=(admission,), observation_handoffs=())

    rows = _build_debug_silence_observations(
        [
            {
                "start_sec": 1.0,
                "end_sec": 1.2,
                "coverage_status": "complete",
                "provenance_status": "complete",
            }
        ],
        [(30, "あ", 0.0)],
        effective_plan=plan,
    )

    assert rows[0]["result"] == "contract_violation"
    assert rows[0]["reason_code"] == "base_event_overlaps_silence_core"
    assert rows[0]["handoffs"] == []
    assert rows[0]["base_event_admissions"][0]["event_index"] == 65


def test_debug_provenance_is_checked_against_projection_keys() -> None:
    interval = [
        {
            "start_sec": 1.0,
            "end_sec": 1.4,
            "coverage_status": "complete",
            "provenance_status": "unavailable",
        }
    ]
    writer_points = [(30, "あ", 0.4), (42, "あ", 0.0)]
    provenance = [
        {
            "origin_shape_id": 0,
            "source_event_indices": (0,),
            "raw_point_id": "0:0",
            "point_kind": "peak",
            "required_zero": False,
            "raw_key": [30, "あ"],
            "normalized_key": [30, "あ"],
            "normalization_action": "none",
            "origin_kind": "shape_control_point",
        },
        {
            "origin_shape_id": 0,
            "source_event_indices": (0,),
            "raw_point_id": "0:1",
            "point_kind": "end_zero",
            "required_zero": True,
            "raw_key": [42, "あ"],
            "normalized_key": [42, "あ"],
            "normalization_action": "none",
            "origin_kind": "shape_control_point",
        },
    ]

    complete = _build_debug_silence_observations(
        interval,
        writer_points,
        provenance_rows=provenance,
    )[0]
    incomplete = _build_debug_silence_observations(
        interval,
        writer_points,
        provenance_rows=provenance[:1],
    )[0]

    assert complete["provenance_status"] == "complete"
    assert complete["result"] == "suspicious"
    assert incomplete["provenance_status"] == "unavailable"
    assert incomplete["result"] == "not_evaluable"
    assert incomplete["reason_code"] == "provenance_unavailable"
