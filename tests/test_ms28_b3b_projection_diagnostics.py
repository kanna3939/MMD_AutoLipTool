from __future__ import annotations

import json
from types import SimpleNamespace

from src.core.analysis_debug_store import AnalysisDebugStore
from src.core.analysis_debug_trace import build_debug_trace
from src.gui_wx.main_frame import (
    MainFrame,
    _debug_failure_context_from_error,
    _debug_safe_failure_code,
)
from src.core.event_adjustment import AdjustmentContractError


def _frame_for_projection_trace(*, diagnostic: dict) -> MainFrame:
    frame = MainFrame.__new__(MainFrame)
    frame.ui_state = SimpleNamespace(
        debug_mode_enabled=True,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
    )
    frame._analysis_info_in_progress = False
    frame._accepted_debug_trace = build_debug_trace(
        input_mode="text_audio",
        job_id=21,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="text_file",
        selected_model_key="small",
        selected_wav_analysis=None,
    )
    frame._accepted_debug_trace.adopt()
    frame._current_ui_sync_diagnostic = diagnostic
    frame._current_ui_sync_failure_reason = None
    return frame


def _base_diagnostic(*, status: str = "available", failure_code: str | None = None) -> dict:
    return {
        "analysis_state": {
            "analysis_result_valid": True,
            "analysis_pending_rebuild": False,
            "current_timing_plan_present": True,
            "current_timing_plan_type": "VowelTimingPlan",
            "analysis_info_in_progress": False,
            "is_busy": False,
            "vmd_save_ready": True,
        },
        "base_input": {
            "status": status,
            "failure_code": failure_code,
            "timeline_count": 4,
            "observations_present": True,
            "duration_candidates": [
                {
                    "source": "selected_wav_analysis",
                    "status": "candidate",
                    "duration_sec": 2.0,
                }
            ],
            "duration_status": "selected",
            "duration_sec": 2.0,
        },
        "sync_context": {
            "status": "available" if status == "available" else "unavailable",
            "failure_code": None if status == "available" else "base_input_unavailable",
            "exception_type": None,
        },
    }


def test_failure_projection_records_input_diagnostics_before_legacy_skip() -> None:
    frame = _frame_for_projection_trace(
        diagnostic=_base_diagnostic(
            status="unavailable",
            failure_code="duration_unavailable",
        )
    )

    frame._record_debug_projection_impl(
        sync_context=None,
        diagnostics_snapshot=None,
        effective_writer_input_state="invalid",
        effective_writer_input_failure_reason=(
            "AdjustmentContractError: private path C:/secret/input.txt"
        ),
    )

    records = frame._accepted_debug_trace.snapshot()["records"]
    stages = [record["stage"] for record in records]
    assert stages[-3:] == [
        "projection_input",
        "effective_shape",
        "projection_comparison",
    ]
    projection_input = records[-3]
    assert projection_input["reason_code"] == "base_input_unavailable"
    assert projection_input["payload"]["status"] == "unavailable"
    assert projection_input["payload"]["base_input"]["failure_code"] == (
        "duration_unavailable"
    )
    assert projection_input["payload"]["effective_writer_input"]["failure_code"] == (
        "unknown_contract_failure"
    )
    assert "C:/secret" not in json.dumps(projection_input, ensure_ascii=False)
    assert records[-2]["payload"]["projection_input_reason"] == (
        "base_input_unavailable"
    )
    assert records[-1]["payload"]["projection_input_reason"] == (
        "base_input_unavailable"
    )


def test_projection_input_reason_separates_sync_and_diagnostics_failures() -> None:
    frame = _frame_for_projection_trace(diagnostic=_base_diagnostic())

    frame._record_debug_projection_impl(
        sync_context=None,
        diagnostics_snapshot=None,
    )
    sync_record = frame._accepted_debug_trace.snapshot()["records"][-3]
    assert sync_record["reason_code"] == "sync_context_build_failed"

    frame._current_ui_sync_diagnostic = _base_diagnostic()
    frame._record_debug_projection_impl(
        sync_context=object(),
        diagnostics_snapshot=None,
    )
    diagnostics_record = frame._accepted_debug_trace.snapshot()["records"][-3]
    assert diagnostics_record["reason_code"] == "diagnostics_snapshot_unavailable"


def test_projection_input_payload_marks_ready_when_all_inputs_are_available() -> None:
    frame = _frame_for_projection_trace(diagnostic=_base_diagnostic())

    payload = frame._debug_projection_input_payload(
        projection_revision=3,
        sync_context=object(),
        diagnostics_snapshot=object(),
        effective_writer_input_state="ready",
        effective_writer_input_failure_reason=None,
    )

    assert payload["status"] == "ready"
    assert payload["reason_code"] == "projection_input_ready"
    assert payload["projection_revision"] == 3
    assert payload["sync_context"]["status"] == "available"
    assert payload["diagnostics_snapshot"]["present"] is True
    assert payload["effective_writer_input"] == {
        "state": "ready",
        "failure_code": "not_applicable",
    }
    assert payload["failure_context"] == {
        "phase": "none",
        "domain": "none",
        "code": "none",
        "exception_type": "not_applicable",
        "field_code": "not_applicable",
        "event_index": "not_applicable",
        "source_event_index": "not_applicable",
        "index_status": "not_applicable",
        "observed_stage": "ui_sync_context",
    }
    assert payload["sync_inputs"]["effective_plan_hint"] == "not_evaluated"
    assert payload["downstream"]["diagnostics_snapshot"] == "completed"
    assert payload["downstream"]["effective_shape"] == "completed"
    assert payload["contract_summary"]["event_index_range"] == [0, 4]


def test_projection_gate_does_not_reuse_old_trace_for_excluded_states() -> None:
    frame = MainFrame.__new__(MainFrame)
    frame._accepted_debug_trace = object()
    frame._analysis_info_in_progress = False
    frame.ui_state = SimpleNamespace(
        debug_mode_enabled=True,
        analysis_result_valid=False,
        analysis_pending_rebuild=False,
    )
    assert frame._debug_trace_for_current_projection() is None

    frame.ui_state.analysis_result_valid = True
    frame.ui_state.analysis_pending_rebuild = True
    assert frame._debug_trace_for_current_projection() is None

    frame.ui_state.analysis_pending_rebuild = False
    frame.ui_state.debug_mode_enabled = False
    assert frame._debug_trace_for_current_projection() is None


def test_safe_failure_code_never_keeps_exception_message() -> None:
    raw = "ValueError: private path C:/secret/input.txt"
    assert _debug_safe_failure_code(raw) == "unknown_contract_failure"


def test_adjustment_contract_error_carries_safe_metadata_without_message_parsing() -> None:
    error = AdjustmentContractError(
        "private path C:/secret/input.txt",
        safe_code="observation_metadata_invalid",
        safe_field_code="observation",
        event_index=7,
        source_event_index=6,
    )

    context = _debug_failure_context_from_error(
        error,
        phase="effective_plan_resolve",
    )

    assert context == {
        "phase": "effective_plan_resolve",
        "domain": "observation_metadata",
        "code": "observation_metadata_invalid",
        "exception_type": "AdjustmentContractError",
        "field_code": "observation",
        "event_index": 7,
        "source_event_index": 6,
        "index_status": "available",
        "observed_stage": "ui_sync_context",
    }
    assert "private path" not in json.dumps(context, ensure_ascii=False)


def test_projection_input_artifact_is_persisted_per_revision(tmp_path) -> None:
    trace = build_debug_trace(
        input_mode="voice_only",
        job_id=22,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="whisper_words",
        selected_model_key="small",
        selected_wav_analysis=None,
    )
    trace.adopt()
    revision = trace.start_projection_revision()
    trace.record_stage(
        "projection_input",
        reason_code="projection_input_ready",
        payload={
            "contract_version": "ms28-b3b-projection-input-v1",
            "status": "ready",
            "projection_revision": revision,
        },
    )
    trace.record_terminal("completed", reason_code="test")

    store = AnalysisDebugStore(tmp_path / "debug")
    assert store.submit(trace) is True
    assert store.flush(timeout=2.0) is True
    store.shutdown(timeout=1.0)

    run_dir = next(path for path in (tmp_path / "debug").iterdir() if path.is_dir())
    artifact = run_dir / "projections" / str(revision) / "projection_input.json"
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "ms28-b3b-projection-input-v1"
    assert payload["status"] == "ready"
    assert payload["projection_revision"] == revision
