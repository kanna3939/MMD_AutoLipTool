from __future__ import annotations

from types import SimpleNamespace

from src.core.effective_shape_diagnostics import ResolverDiagnosticsCollector
from src.core.analysis_debug_trace import build_debug_trace
from src.gui_wx.main_frame import MainFrame


def _frame(*, resolver: dict | None = None) -> MainFrame:
    frame = MainFrame.__new__(MainFrame)
    frame._current_ui_sync_diagnostic = {
        "resolver_diagnostics": resolver or {},
        "base_input": {"status": "available", "failure_code": None},
        "sync_context": {"status": "available"},
    }
    frame.ui_state = SimpleNamespace(
        debug_mode_enabled=True,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
        current_timing_plan=None,
        is_busy=False,
        vmd_save_ready=False,
        current_output_diagnostics_snapshot=None,
    )
    frame._analysis_info_in_progress = False
    return frame


def _resolver_snapshot(*, status: str, plan_origin: str = "resolved") -> dict:
    return {
        "diagnostic_revision": "ms28-b3c-resolver-v1",
        "capture_state": "complete",
        "attempts": [
            {
                "attempt_index": 1,
                "caller": "resolver",
                "plan_origin": plan_origin,
                "status": status,
                "phase_records": [],
                "failure": None,
                "summary": {},
            }
        ],
        "truncation": {"limited": False},
    }


def test_resolver_failure_is_attempted_and_failed_in_new_object() -> None:
    frame = _frame(resolver=_resolver_snapshot(status="failed"))
    payload = frame._debug_execution_diagnostics(
        sync_context=None,
        diagnostics_snapshot=None,
        effective_writer_input_state="invalid",
        snapshot_point="projection_complete",
    )
    assert payload["operations"]["effective_shape"] == {
        "state": "attempted",
        "outcome": "failed",
        "reason_code": "resolver_failed",
        "plan_origin": "resolved",
    }
    assert payload["operations"]["vmd_save"]["state"] == "not_attempted"
    assert payload["diagnostic_snapshot_scope"] == "post_stage"
    assert payload["authoritative_for_stage"] is True


def test_cache_and_hint_are_resolver_skips() -> None:
    for origin, reason in (("cache", "resolver_skipped_cache"), ("hint", "resolver_skipped_hint")):
        frame = _frame(resolver=_resolver_snapshot(status="completed", plan_origin=origin))
        payload = frame._debug_execution_diagnostics(
            sync_context=None,
            diagnostics_snapshot=object(),
            effective_writer_input_state="ready",
            snapshot_point="projection_input",
        )
        assert payload["operations"]["effective_shape"]["state"] == "skipped"
        assert payload["operations"]["effective_shape"]["reason_code"] == reason
        assert payload["operations"]["effective_shape"]["plan_origin"] == origin
        assert payload["diagnostic_snapshot_scope"] == "pre_stage"
        assert payload["authoritative_for_stage"] is False


def test_projection_input_keeps_legacy_downstream_and_adds_optional_objects() -> None:
    frame = _frame(resolver=_resolver_snapshot(status="failed"))
    payload = frame._debug_projection_input_payload(
        projection_revision=4,
        sync_context=None,
        diagnostics_snapshot=None,
        effective_writer_input_state="invalid",
        effective_writer_input_failure_reason="private path C:/secret.txt",
    )
    assert payload["contract_version"] == "ms28-b3b-projection-input-v1"
    assert set(payload["downstream"]) == {
        "diagnostics_snapshot",
        "effective_shape",
        "preview_projection",
        "writer_projection",
        "vmd_save",
    }
    assert "resolver_diagnostics" in payload
    assert "execution_diagnostics" in payload
    assert "C:/secret" not in str(payload)


def test_save_action_is_bound_to_action_status_not_saveability_bool() -> None:
    frame = _frame()
    trace = build_debug_trace(
        input_mode="voice_only",
        job_id=1,
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
    frame._accepted_debug_trace = trace
    frame._debug_save_operation_id = None

    frame.record_debug_action("vmd_save_request", status="requested")
    frame.record_debug_action("vmd_save_cancelled", status="cancelled")
    actions = [
        record
        for record in trace.snapshot()["records"]
        if record["stage"] == "vmd_file_save"
    ]
    assert actions[-2]["save_operation_id"] == actions[-1]["save_operation_id"]
    assert actions[-2]["payload"]["execution_diagnostics"]["operations"]["vmd_save"]["outcome"] == "pending"
    assert actions[-1]["payload"]["execution_diagnostics"]["operations"]["vmd_save"]["outcome"] == "cancelled"
