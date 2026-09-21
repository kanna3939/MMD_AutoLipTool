import json

from src.core.analysis_debug_store import AnalysisDebugStore
from src.core.analysis_debug_trace import build_debug_trace


def _trace_with_boundary_payload():
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
            "contract_version": "ms28-b4-silence-v2",
            "projection_revision": 1,
            "observations": [
                {
                    "result": "clear",
                    "reason_code": "clear_no_positive_opening",
                    "base_event_admissions": [
                        {
                            "event_index": 1,
                            "vowel": "あ",
                            "boundary_only": True,
                            "boundary_frame": 30,
                            "boundary_point_kind": "end_zero",
                            "boundary_relation": "different_vowel_boundary",
                            "boundary_action": "preserved_zero_keyframe",
                            "admission_key": "event:1|vowel:あ|frame:30|shape:2",
                            "assignment_status": "assigned_interval",
                            "boundary_admission_checks": {
                                "candidate_range": "zero_width",
                                "positive_point_kinds_empty": True,
                                "boundary_positive_point_kinds_empty": True,
                                "positive_core_frame_ranges_empty": True,
                                "matching_end_zero": True,
                                "shape_provenance_available": True,
                                "boundary_relation_verified": True,
                                "event_peak_value": 0.0,
                                "decision": "accepted_boundary_only",
                            },
                            "required_zero_frame_ranges": [],
                        }
                    ],
                }
            ],
            "unassigned_boundary_admissions": [
                {
                    "event_index": 3,
                    "vowel": "い",
                    "boundary_only": True,
                    "boundary_frame": 90,
                    "boundary_point_kind": "end_zero",
                    "boundary_relation": "different_vowel_boundary",
                    "boundary_action": "not_applicable",
                    "admission_key": "event:3|vowel:い|frame:90|shape:4",
                    "assignment_status": "unassigned",
                    "boundary_admission_checks": {
                        "candidate_range": "zero_width",
                        "positive_point_kinds_empty": True,
                        "boundary_positive_point_kinds_empty": True,
                        "positive_core_frame_ranges_empty": True,
                        "matching_end_zero": True,
                        "shape_provenance_available": True,
                        "boundary_relation_verified": True,
                        "event_peak_value": 0.0,
                        "decision": "accepted_boundary_only",
                    },
                    "reason_code": "boundary_interval_unassigned",
                    "required_zero_frame_ranges": [],
                }
            ],
        },
    )
    trace.record_terminal("completed")
    return trace


def test_b4b_artifact_keeps_boundary_fields_across_all_storage_paths(tmp_path) -> None:
    store = AnalysisDebugStore(tmp_path / "debug")
    assert store.submit(_trace_with_boundary_payload()) is True
    assert store.flush(timeout=2.0) is True
    store.shutdown(timeout=1.0)

    run_dir = next(path for path in (tmp_path / "debug").iterdir() if path.is_dir())
    canonical = json.loads((run_dir / "silence_observations.json").read_text(encoding="utf-8"))
    projection = json.loads(
        (run_dir / "projections" / "1" / "silence_observations.json").read_text(
            encoding="utf-8"
        )
    )
    stage_path = next((run_dir / "stages").glob("*_silence_observations.json"))
    stage_record = json.loads(stage_path.read_text(encoding="utf-8"))
    stage = stage_record["payload"]

    payloads = (stage, canonical, projection)
    for payload in payloads:
        assert payload["schema_version"] == 1
        assert payload["contract_version"] == "ms28-b4-silence-v2"
        assert payload["observations"][0]["base_event_admissions"][0]["boundary_frame"] == 30
        assert (
            payload["observations"][0]["base_event_admissions"][0]["assignment_status"]
            == "assigned_interval"
        )
        assert (
            payload["observations"][0]["base_event_admissions"][0][
                "boundary_admission_checks"
            ]["decision"]
            == "accepted_boundary_only"
        )
        assert payload["unassigned_boundary_admissions"][0]["boundary_frame"] == 90
        assert (
            payload["unassigned_boundary_admissions"][0]["assignment_status"]
            == "unassigned"
        )
        assert (
            payload["unassigned_boundary_admissions"][0]["boundary_relation"]
            == "different_vowel_boundary"
        )
        assert (
            payload["unassigned_boundary_admissions"][0]["boundary_admission_checks"][
                "event_peak_value"
            ]
            == 0.0
        )
        assert (
            payload["unassigned_boundary_admissions"][0]["reason_code"]
            == "boundary_interval_unassigned"
        )

    assert stage == canonical == projection
