from __future__ import annotations

import json
import hashlib
from types import SimpleNamespace

from src.core.analysis_debug_store import AnalysisDebugStore
from src.core.analysis_debug_trace import (
    build_debug_trace,
    build_settings_provenance,
)
from src.core.audio_processing import RmsSeriesData
from src.core.pipeline import (
    _refine_timeline_intervals_with_observations,
    _repair_resolver_same_morph_boundaries,
)
from src.gui_wx.ui_state import UiState
from src.gui_wx.main_frame import (
    _build_debug_silence_curve_comparison,
    _build_debug_silence_observations,
)
from src.vmd_writer import VowelTimelinePoint


def _timeline() -> tuple[VowelTimelinePoint, ...]:
    return (
        VowelTimelinePoint(
            time_sec=1 / 30,
            vowel="あ",
            value=0.5,
            duration_sec=2 / 30,
            start_sec=0.0,
            end_sec=2 / 30,
        ),
        VowelTimelinePoint(
            time_sec=3 / 30,
            vowel="い",
            value=0.4,
            duration_sec=2 / 30,
            start_sec=2 / 30,
            end_sec=4 / 30,
        ),
    )


def test_debug_mode_is_session_only_and_defaults_off() -> None:
    state = UiState()

    assert state.debug_mode_enabled is False
    state.debug_mode_enabled = True
    state.reset_workspace()

    assert state.debug_mode_enabled is True


def test_trace_records_pipeline_and_projection_ownership() -> None:
    trace = build_debug_trace(
        input_mode="text_audio",
        job_id=7,
        source_audio_path="C:/private/input.wav",
        analysis_wav_path="C:/private/cache.wav",
        text_path="C:/private/input.txt",
        analysis_text="機密本文",
        model_identity=None,
        timing_source="pending",
        selected_model_key="small",
        selected_wav_analysis=None,
    )

    repaired = _repair_resolver_same_morph_boundaries(
        _timeline(),
        debug_trace=trace,
        debug_call_site="test",
    )
    trace.record_timeline("timeline_initial", repaired)
    trace.adopt()
    revision = trace.start_projection_revision()
    trace.record_action("vmd_save_request", payload={"input_mode": "text_audio"})

    snapshot = trace.snapshot()
    stages = [record["stage"] for record in snapshot["records"]]

    assert revision == 1
    assert "test.long_boundary" in stages
    assert "analysis_acceptance" in stages
    assert "projection_revision" in stages
    assert "vmd_file_save" in stages
    assert "C:/private" not in json.dumps(snapshot, ensure_ascii=False)
    assert "機密本文" not in json.dumps(snapshot, ensure_ascii=False)


def test_trace_keeps_final_metadata_over_initial_or_generic_values() -> None:
    trace = build_debug_trace(
        input_mode="voice_only",
        job_id=8,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="pending",
        selected_model_key="small",
        selected_wav_analysis=None,
    )

    trace.set_analysis_text("音声から得た本文", source="whisper_transcription")
    trace.set_analysis_text("音声から得た本文", source="provided")
    trace.set_model_identity(
        SimpleNamespace(
            model_key="small",
            manifest_identity="manifest-v1",
            package_version="20250625",
        )
    )
    trace.set_timing_source("whisper_words")

    identity = trace.snapshot()["input_identity"]
    assert identity["analysis_text"]["source"] == "whisper_transcription"
    assert identity["timing"]["source"] == "whisper_words"
    assert identity["model"] == {
        "model_key": "small",
        "manifest_identity": "manifest-v1",
        "package_version": "20250625",
    }


def test_settings_provenance_records_effective_values_without_absolute_path(tmp_path) -> None:
    settings_path = tmp_path / "MMD_AutoLipTool.ini"
    settings_path.write_text("long_vowel_mode=decay\n", encoding="utf-8")
    provenance = build_settings_provenance(
        settings_store=SimpleNamespace(settings_path=settings_path),
        generation_settings=SimpleNamespace(
            closing_hold_frames=2,
            closing_softness_frames=3,
            long_vowel_mode="decay",
        ),
        active_preset_id="default",
        active_model_profile_id="small",
    )

    assert provenance["settings_file"]["status"] == "observed"
    assert provenance["settings_file"]["basename"] == "MMD_AutoLipTool.ini"
    assert provenance["settings_file"]["scope"] == "source_repo_root"
    assert provenance["effective_generation_settings"]["long_vowel_mode"] == "decay"
    assert str(tmp_path) not in json.dumps(provenance, ensure_ascii=False)

    trace = build_debug_trace(
        input_mode="text_audio",
        job_id=9,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="whisper_words",
        selected_model_key="small",
        selected_wav_analysis=None,
        settings_provenance=provenance,
    )
    assert trace.snapshot()["settings_provenance"] == provenance


def test_debug_store_writes_safe_intermediate_artifacts(tmp_path) -> None:
    input_path = tmp_path / "private_input.wav"
    input_path.write_bytes(b"private-audio-content")
    trace = build_debug_trace(
        input_mode="voice_only",
        job_id=3,
        source_audio_path=input_path,
        analysis_wav_path=input_path,
        text_path=None,
        analysis_text="private transcription",
        model_identity=None,
        timing_source="whisper_segments",
        selected_model_key="small",
        selected_wav_analysis=SimpleNamespace(
            duration_sec=1.0,
            sample_rate_hz=44100,
            channel_count=1,
            has_speech=True,
            speech_start_sec=0.0,
            speech_end_sec=1.0,
        ),
    )
    trace.record_stage("audio_analysis", payload={"duration_sec": 1.0})
    trace.record_timeline("timeline_initial", _timeline())
    trace.record_terminal("completed", reason_code="test")

    store = AnalysisDebugStore(tmp_path / "debug")
    assert store.submit(trace) is True
    assert store.flush(timeout=2.0) is True
    store.shutdown(timeout=1.0)

    run_dirs = [path for path in (tmp_path / "debug").iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "events.csv").is_file()
    assert (run_dir / "diagnostics.txt").is_file()
    assert (run_dir / "stages").is_dir()

    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in run_dir.rglob("*")
        if path.is_file()
    )
    assert str(input_path) not in serialized
    assert "private transcription" not in serialized
    assert "private-audio-content" not in serialized
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_identity"]["source_audio"]["file_basename"] == input_path.name
    assert manifest["capture_status"] == "completed"
    assert manifest["runtime_identity"]["execution_mode"] in {"source", "frozen"}
    assert manifest["runtime_identity"]["executable_basename"]
    assert manifest["runtime_identity"]["app_version"]
    assert manifest["runtime_identity"]["build_identifier"]
    assert not any(item["relative_name"] == "manifest.json" for item in manifest["artifact_files"])
    for item in manifest["artifact_files"]:
        artifact_path = run_dir / item["relative_name"]
        assert artifact_path.stat().st_size == item["bytes"]
        assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == item["sha256"]


def test_debug_store_persists_final_identity_metadata(tmp_path) -> None:
    trace = build_debug_trace(
        input_mode="voice_only",
        job_id=12,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="pending",
        selected_model_key="small",
        selected_wav_analysis=None,
    )
    store = AnalysisDebugStore(tmp_path / "debug")
    assert store.submit(trace) is True
    trace.set_analysis_text("音声から得た本文", source="whisper_transcription")
    trace.set_model_identity(
        SimpleNamespace(
            model_key="small",
            manifest_identity="manifest-v1",
            package_version="20250625",
        )
    )
    trace.set_timing_source("whisper_words")
    trace.record_terminal("completed", reason_code="test")
    assert store.submit(trace) is True
    assert store.flush(timeout=2.0) is True
    store.shutdown(timeout=1.0)

    run_dir = next(path for path in (tmp_path / "debug").iterdir() if path.is_dir())
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    identity = manifest["input_identity"]
    assert identity["analysis_text"]["source"] == "whisper_transcription"
    assert identity["timing"]["source"] == "whisper_words"
    assert identity["model"]["manifest_identity"] == "manifest-v1"


def test_debug_store_coalesces_late_records_into_terminal_manifest(tmp_path) -> None:
    trace = build_debug_trace(
        input_mode="text_audio",
        job_id=4,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="pending",
        selected_model_key="small",
        selected_wav_analysis=None,
    )
    trace.record_stage("input_snapshot", payload={"input_mode": "text_audio"})
    trace.record_terminal("completed", reason_code="test")
    store = AnalysisDebugStore(tmp_path / "debug")
    assert store.submit(trace) is True
    trace.record_stage("late_projection", payload={"projection_revision": 1})
    assert store.submit(trace) is True
    assert store.flush(timeout=2.0) is True
    store.shutdown(timeout=1.0)

    run_dir = next(path for path in (tmp_path / "debug").iterdir() if path.is_dir())
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["capture_status"] == "completed"
    assert any(item["stage"] == "late_projection" for item in manifest["stage_status"])


def test_debug_silence_observation_measures_linear_interpolation() -> None:
    rows = _build_debug_silence_observations(
        [
            {
                "start_sec": 9.827,
                "end_sec": 10.217,
                "duration_sec": 0.39,
                "classification": "silence_candidate",
                "coverage_status": "complete",
                "provenance_status": "complete",
            }
        ],
        [
            (303, "あ", 0.0),
            (304, "あ", 0.2402),
            (306, "あ", 0.2402),
            (309, "あ", 0.0),
        ],
    )

    assert rows[0]["result"] == "suspicious"
    assert rows[0]["evaluation_status"] == "evaluable"
    assert rows[0]["reason_code"] == "positive_writer_control_point_and_interpolation_in_silence_core"
    assert rows[0]["positive_frames"] == [304]
    assert rows[0]["positive_fringe_frames"] == [306]
    assert rows[0]["positive_interpolated_intervals"]


def test_debug_silence_curve_comparison_samples_preview_and_writer() -> None:
    rows = _build_debug_silence_curve_comparison(
        [
            {
                "start_sec": 1.0,
                "end_sec": 1.1,
            }
        ],
        {"あ": [[(29, 0.0), (30, 0.0), (33, 0.0)]]},
        [(29, "あ", 0.0), (30, "あ", 0.0), (32, "あ", 0.0), (33, "あ", 0.0)],
    )

    assert rows
    assert rows[0]["sample_count"] == 4
    assert rows[0]["preview_positive_frame_count"] == 0
    assert rows[0]["writer_positive_frame_count"] == 0
    assert rows[0]["max_abs_diff"] == 0.0
    assert rows[0]["within_tolerance"] is True


def test_pipeline_trace_contains_pre_post_rms_and_fallback_reason(monkeypatch) -> None:
    trace = build_debug_trace(
        input_mode="text_audio",
        job_id=11,
        source_audio_path=None,
        analysis_wav_path=None,
        text_path=None,
        analysis_text="",
        model_identity=None,
        timing_source="whisper_segments",
        selected_model_key="small",
        selected_wav_analysis=None,
    )
    monkeypatch.setattr(
        "src.core.pipeline.load_rms_series",
        lambda *_args, **_kwargs: RmsSeriesData(
            sample_rate_hz=1000,
            channel_count=1,
            duration_sec=1.0,
            window_size_samples=20,
            hop_size_samples=10,
            times_sec=[0.01, 0.02, 0.03],
            values=[0.2, 0.0, 0.2],
        ),
    )

    _refine_timeline_intervals_with_observations(
        timeline=_timeline(),
        wav_path="ignored.wav",
        speech_start_sec=0.0,
        speech_end_sec=1.0,
        upper_limit=0.5,
        debug_trace=trace,
    )

    records = trace.snapshot()["records"]
    rms_record = next(record for record in records if record["stage"] == "rms_load")
    assert rms_record["payload"]["diagnostic_threshold_rms"] == 0.01
    assert rms_record["payload"]["silence_intervals"]
    assert any(record["stage"] == "timeline_pre_rms" for record in records)
    assert any(record["stage"] == "timeline_post_rms_raw" for record in records)
