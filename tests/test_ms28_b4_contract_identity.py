from __future__ import annotations

from dataclasses import dataclass, replace
import json

from src.core.analysis_debug_store import AnalysisDebugStore
from src.core.analysis_debug_trace import build_debug_trace
from src.core.effective_shape_plan import BaseTimingPlanInput, resolve_effective_shape_plan
from src.core.output_diagnostics import _observations_canonical
from src.core.pipeline import PeakValueEvaluation, PeakValueObservation
from src.gui_wx.main_frame import _build_debug_silence_observations
from src.vmd_writer import VowelTimelinePoint


@dataclass(frozen=True)
class _HandoffObservation:
    event_index: int
    vowel: str
    is_bridgeable_cross_vowel_transition_candidate: bool = False
    previous_non_zero_event_index: int | None = None
    next_non_zero_event_index: int | None = None
    span_start_index: int | None = None
    span_end_index: int | None = None
    full_span_start_frame: int | None = None
    full_span_end_frame: int | None = None
    silence_core_frame_ranges: tuple[tuple[int, int], ...] = ()
    boundary_fringe_frame_ranges: tuple[tuple[int, int], ...] = ()
    silence_core_overlap: bool = False
    coverage_status: str = "unobserved"
    provenance_status: str = "unavailable"
    bridge_rejection_reason_code: str | None = None


def _make_peak_observation() -> PeakValueObservation:
    evaluation = PeakValueEvaluation(
        interval_start_sec=0.0,
        interval_end_sec=0.25,
        peak_window_start_sec=0.0,
        peak_window_end_sec=0.25,
        local_peak=0.3,
        peak_value=0.3,
        reason="local_peak",
    )
    return PeakValueObservation(
        event_index=0,
        vowel="あ",
        time_sec=0.1,
        initial_interval_start_sec=0.0,
        initial_interval_end_sec=0.25,
        refined_interval_start_sec=0.0,
        refined_interval_end_sec=0.25,
        peak_window_start_sec=0.0,
        peak_window_end_sec=0.25,
        local_peak=0.3,
        global_peak=0.4,
        peak_value=0.3,
        reason="local_peak",
        fallback_reason=None,
        window_sample_count=3,
        evaluation=evaluation,
        rms_window_times_sec=(0.0, 0.1, 0.2),
        rms_window_values=(0.1, 0.3, 0.2),
        full_span_start_frame=18,
        full_span_end_frame=42,
        silence_core_frame_ranges=((18, 42),),
        boundary_fringe_frame_ranges=(),
        silence_core_overlap=True,
        coverage_status="complete",
        provenance_status="complete",
        bridge_rejection_reason_code="cross_vowel_handoff_crosses_silence_core",
    )


def test_long_cross_vowel_handoff_is_rejected_and_keeps_previous_end() -> None:
    timeline = (
        VowelTimelinePoint(time_sec=0.5, vowel="あ", start_sec=0.4, end_sec=0.6),
        VowelTimelinePoint(time_sec=1.0, vowel="い", start_sec=0.9, end_sec=1.1),
        VowelTimelinePoint(time_sec=1.5, vowel="う", start_sec=1.4, end_sec=1.6),
    )
    observations = (
        _HandoffObservation(0, "あ"),
        _HandoffObservation(
            1,
            "い",
            is_bridgeable_cross_vowel_transition_candidate=True,
            previous_non_zero_event_index=0,
            next_non_zero_event_index=2,
            span_start_index=1,
            span_end_index=1,
            full_span_start_frame=18,
            full_span_end_frame=42,
            silence_core_frame_ranges=((18, 42),),
            silence_core_overlap=True,
            coverage_status="complete",
            provenance_status="complete",
            bridge_rejection_reason_code="cross_vowel_handoff_crosses_silence_core",
        ),
        _HandoffObservation(2, "う"),
    )

    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=timeline,
            observations=observations,
            source_duration_frames=90,
        )
    )

    assert len(plan.observation_handoffs) == 1
    handoff = plan.observation_handoffs[0]
    assert handoff.enabled is False
    assert handoff.silence_core_overlap is True
    assert handoff.rejection_reason_code == "cross_vowel_handoff_crosses_silence_core"
    assert plan.effective_events[0].end_frame == 18
    assert plan.effective_events[2].start_frame == 42


def test_runtime_contract_fields_are_in_canonical_observation_identity() -> None:
    observation = _make_peak_observation()
    _, payload = _observations_canonical((observation,))
    fields = [name for name, _ in payload[0]]

    assert fields[-16:] == [
        "full_span_start_frame",
        "full_span_end_frame",
        "silence_core_frame_ranges",
        "boundary_fringe_frame_ranges",
        "silence_core_overlap",
        "coverage_status",
        "provenance_status",
        "bridge_rejection_reason_code",
        "base_event_silence_core_overlap",
        "positive_core_frame_ranges",
        "long_vowel_role",
        "manual_adjustment_applied",
        "base_event_rejection_reason_code",
        "boundary_only",
        "boundary_frame",
        "boundary_point_kind",
    ]
    assert "contract_version" not in fields
    changed = replace(observation, full_span_end_frame=43)
    assert _observations_canonical((observation,)) != _observations_canonical((changed,))
    boundary_changed = replace(
        observation,
        boundary_only=True,
        boundary_frame=30,
        boundary_point_kind="end_zero",
    )
    assert _observations_canonical((observation,)) != _observations_canonical(
        (boundary_changed,)
    )


def test_b4_silence_artifact_has_payload_schema_and_contract_version(tmp_path) -> None:
    trace = build_debug_trace(
        input_mode="voice_only",
        job_id=28,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="whisper_words",
        selected_model_key="small",
        selected_wav_analysis=None,
    )
    trace.start_projection_revision()
    trace.record_stage(
        "silence_observations",
        payload={
            "schema_version": 1,
            "contract_version": "ms28-b4-silence-v1",
            "observations": [{"result": "clear", "reason_code": "clear_no_positive_opening"}],
        },
    )
    trace.record_terminal("completed")

    store = AnalysisDebugStore(tmp_path / "debug")
    assert store.submit(trace) is True
    assert store.flush(timeout=2.0) is True
    store.shutdown(timeout=1.0)

    run_dir = next(path for path in (tmp_path / "debug").iterdir() if path.is_dir())
    canonical = json.loads((run_dir / "silence_observations.json").read_text(encoding="utf-8"))
    projection = json.loads(
        (run_dir / "projections" / "1" / "silence_observations.json").read_text(encoding="utf-8")
    )
    stage_path = next((run_dir / "stages").glob("*_silence_observations.json"))
    stage = json.loads(stage_path.read_text(encoding="utf-8"))

    for payload in (canonical, projection):
        assert payload["schema_version"] == 1
        assert payload["contract_version"] == "ms28-b4-silence-v1"
        assert payload["observations"][0]["result"] == "clear"
    assert stage["schema_version"] == 1
    assert stage["payload"]["schema_version"] == 1
    assert stage["payload"]["contract_version"] == "ms28-b4-silence-v1"


def test_b4_debug_classification_fails_closed_on_missing_coverage_or_provenance() -> None:
    intervals = [
        {
            "start_sec": 1.0,
            "end_sec": 1.4,
            "coverage_status": "partial",
            "provenance_status": "complete",
        },
        {
            "start_sec": 2.0,
            "end_sec": 2.4,
            "coverage_status": "complete",
            "provenance_status": "unavailable",
        },
    ]
    writer_points = [(30, "あ", 0.4), (60, "あ", 0.0)]

    rows = _build_debug_silence_observations(intervals, writer_points)

    assert [row["result"] for row in rows] == ["not_evaluable", "not_evaluable"]
    assert rows[0]["reason_code"] == "silence_coverage_insufficient"
    assert rows[1]["reason_code"] == "provenance_unavailable"
