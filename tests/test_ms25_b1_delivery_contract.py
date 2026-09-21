from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from gui_wx.output_diagnostics_adapter import (
    build_output_diagnostics_snapshot_from_ui_state,
)
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, UiState
from src.core.audio_probe import AudioProbeResult, AudioStreamInfo
from src.core.delivery_package import (
    DeliveryContractError,
    DeliveryCurrentState,
    DeliveryStartContext,
    SourceAudioIdentity,
    build_delivery_artifact_names,
    build_delivery_start_context,
    capture_source_audio_identity,
    evaluate_delivery_commit_fingerprint,
    evaluate_delivery_start_gate,
)
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    resolve_effective_shape_plan,
)
from src.core.mmd_wav_export import MMD_WAV_SPEC
from src.core.output_diagnostics import SaveabilitySummary, VmdWriterParameters
from src.core.pipeline import VowelTimingPlan
from src.core.whisper_timing import SpeechTimingAnchor
from src.vmd_writer import VowelTimelinePoint
from src.core.audio_processing import WavAnalysisResult


def _timing_plan() -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.3,
                vowel="あ",
                duration_sec=0.2,
                start_sec=0.2,
                end_sec=0.4,
            )
        ],
        anchors=[SpeechTimingAnchor(start_sec=0.2, end_sec=0.4, text="あ")],
        source="whisper_segments",
        observations=[],
    )


def _wav_analysis() -> WavAnalysisResult:
    return WavAnalysisResult(
        sample_rate_hz=44100,
        frame_count=44100,
        channel_count=1,
        duration_sec=1.0,
        leading_silence_end_sec=0.1,
        trailing_silence_start_sec=0.9,
        speech_start_sec=0.1,
        speech_end_sec=0.9,
        has_speech=True,
    )


def _inputs(tmp_path: Path):
    source_path = tmp_path / "音声 sample.WAV"
    source_path.write_bytes(b"source audio")
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffmpeg_path.write_bytes(b"ffmpeg")
    probe = AudioProbeResult(
        source_path=source_path,
        file_size_bytes=source_path.stat().st_size,
        duration_sec=1.0,
        format_name="wav",
        audio_stream=AudioStreamInfo(
            codec_name="pcm_s16le",
            sample_rate_hz=44100,
            channel_count=1,
            duration_sec=1.0,
        ),
    )
    timing_plan = _timing_plan()
    state = UiState(
        selected_text_path=str(tmp_path / "input.txt"),
        selected_text_content="あ",
        selected_wav_path=str(source_path),
        selected_audio_input=SimpleNamespace(source_path=source_path),
        selected_audio_probe=probe,
        selected_wav_analysis=_wav_analysis(),
        input_mode=INPUT_MODE_TEXT_AUDIO,
    )
    state.mark_analysis_success(
        timing_plan,
        input_mode=INPUT_MODE_TEXT_AUDIO,
        analysis_text_content="あ",
        analysis_text_source="text_file",
    )
    effective_plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=tuple(timing_plan.timeline),
            observations=None,
            source_duration_frames=30,
        ),
        None,
    )
    snapshot = build_output_diagnostics_snapshot_from_ui_state(
        state,
        effective_shape_plan=effective_plan,
        effective_writer_input_state="ready",
        output_morph_names=("あ", "い", "う", "え", "お"),
        projection_generation=4,
    )
    return source_path, ffmpeg_path, probe, effective_plan, snapshot


def _evaluate_ready(tmp_path: Path, **overrides):
    source_path, ffmpeg_path, probe, effective_plan, snapshot = _inputs(tmp_path)
    values = {
        "effective_shape_plan": effective_plan,
        "diagnostics_snapshot": snapshot,
        "audio_probe": probe,
        "source_audio_path": source_path,
        "mmd_wav_spec": MMD_WAV_SPEC,
        "ffmpeg_path": ffmpeg_path,
        "writer_parameters": VmdWriterParameters(),
        "output_morph_names": ("あ", "い", "う", "え", "お"),
        "effective_writer_input_state": "ready",
    }
    values.update(overrides)
    return evaluate_delivery_start_gate(**values), values


def test_build_delivery_artifact_names_preserves_unicode_case_and_spaces():
    names = build_delivery_artifact_names(Path("音声 sample.WAV"))

    assert names.audio_stem == "音声 sample"
    assert names.default_directory_name == "音声 sample_MMD"
    assert names.vmd_file_name == "音声 sample_lip.vmd"
    assert names.mmd_wav_file_name == "音声 sample_mmd.wav"
    assert names.report_file_name == "音声 sample_report.txt"


def test_empty_stem_is_fail_closed():
    with pytest.raises(DeliveryContractError) as error:
        build_delivery_artifact_names(Path(""))

    assert error.value.code == "delivery_source_audio_invalid"


def test_capture_source_audio_identity_records_resolved_file_metadata(tmp_path):
    source_path = tmp_path / "source.wav"
    source_path.write_bytes(b"audio")

    identity = capture_source_audio_identity(source_path)

    assert identity.resolved_path == source_path.resolve()
    assert identity.size_bytes == source_path.stat().st_size
    assert identity.mtime_ns == source_path.stat().st_mtime_ns
    assert isinstance(identity, SourceAudioIdentity)


@pytest.mark.parametrize("path_kind", ["missing", "directory"])
def test_capture_source_audio_identity_rejects_missing_or_directory(tmp_path, path_kind):
    path = tmp_path / "source"
    if path_kind == "directory":
        path.mkdir()

    with pytest.raises(DeliveryContractError) as error:
        capture_source_audio_identity(path)

    assert error.value.code == "delivery_source_audio_invalid"


def test_ready_gate_contains_one_immutable_current_state(tmp_path):
    result, values = _evaluate_ready(tmp_path)

    assert result.status == "ready"
    assert result.blocking_codes == ()
    assert result.candidate_state is not None
    current = result.candidate_state
    assert current.effective_shape_plan is values["effective_shape_plan"]
    assert current.diagnostics_snapshot is values["diagnostics_snapshot"]
    assert current.output_morph_names == ("あ", "い", "う", "え", "お")
    assert current.artifact_order == ("vmd", "mmd_wav", "report")
    assert current.start_fingerprint == current.diagnostics_snapshot.save_state_fingerprint
    with pytest.raises(FrozenInstanceError):
        current.output_morph_names = ("A", "I", "U", "E", "O")


def test_current_state_rejects_morph_names_mismatching_snapshot_identity(tmp_path):
    _, values = _evaluate_ready(tmp_path)
    snapshot = values["diagnostics_snapshot"]
    values["diagnostics_snapshot"] = replace(
        snapshot,
        generation_summary=replace(
            snapshot.generation_summary,
            resolved_morph_name_set_id="builtin:latin-vowels",
            resolved_morph_name_set_display_name="英字5母音",
        ),
    )

    result = evaluate_delivery_start_gate(**values)

    assert result.status == "blocked"
    assert result.candidate_state is None
    assert "delivery_current_state_invalid" in result.blocking_codes


def test_warning_gate_requires_same_fingerprint_confirmation(tmp_path):
    _, values = _evaluate_ready(tmp_path)
    snapshot = values["diagnostics_snapshot"]
    values["diagnostics_snapshot"] = replace(
        snapshot,
        saveability=SaveabilitySummary(
            vmd_save_allowed=True,
            blocking_codes=(),
            warning_codes=("timing_warning",),
        ),
    )

    unconfirmed = evaluate_delivery_start_gate(**values)
    confirmed = evaluate_delivery_start_gate(
        **values,
        confirmed_warning_save_state_fingerprint=unconfirmed.fingerprint,
    )
    changed = evaluate_delivery_start_gate(
        **values,
        confirmed_warning_save_state_fingerprint="sha256:other",
    )

    assert unconfirmed.status == "warning_confirmation_required"
    assert confirmed.status == "ready"
    assert changed.status == "warning_confirmation_required"


def test_warning_candidate_cannot_be_promoted_to_start_context(tmp_path):
    _, values = _evaluate_ready(tmp_path)
    values["diagnostics_snapshot"] = replace(
        values["diagnostics_snapshot"],
        saveability=SaveabilitySummary(
            vmd_save_allowed=True,
            blocking_codes=(),
            warning_codes=("timing_warning",),
        ),
    )

    result = evaluate_delivery_start_gate(**values)
    current = result.candidate_state
    assert result.status == "warning_confirmation_required"
    assert current is not None
    assert current.gate_status == "warning_confirmation_required"

    with pytest.raises(DeliveryContractError) as error:
        build_delivery_start_context(
            current,
            tmp_path,
            "delivery",
            datetime.now(timezone.utc),
        )
    assert error.value.code == "delivery_start_context_invalid"


def test_error_gate_does_not_create_candidate_state(tmp_path):
    _, values = _evaluate_ready(tmp_path)
    values["diagnostics_snapshot"] = replace(
        values["diagnostics_snapshot"],
        saveability=SaveabilitySummary(
            vmd_save_allowed=False,
            blocking_codes=("analysis_failure",),
            warning_codes=(),
        ),
    )

    result = evaluate_delivery_start_gate(**values)

    assert result.status == "blocked"
    assert result.candidate_state is None
    assert "delivery_diagnostics_blocked" in result.blocking_codes


@pytest.mark.parametrize("mismatch_kind", ["path", "size"])
def test_source_probe_path_or_size_mismatch_is_blocked(tmp_path, mismatch_kind):
    _, values = _evaluate_ready(tmp_path)
    if mismatch_kind == "path":
        other_path = tmp_path / "other.wav"
        other_path.write_bytes(b"other")
        values["audio_probe"] = replace(values["audio_probe"], source_path=other_path)
    else:
        values["audio_probe"] = replace(
            values["audio_probe"],
            file_size_bytes=values["audio_probe"].file_size_bytes + 1,
        )

    result = evaluate_delivery_start_gate(**values)

    assert result.status == "blocked"
    assert "delivery_source_audio_invalid" in result.blocking_codes


def test_start_context_requires_timezone_aware_timestamp(tmp_path):
    result, _ = _evaluate_ready(tmp_path)
    current = result.candidate_state
    assert current is not None

    context = build_delivery_start_context(
        current,
        tmp_path,
        "delivery",
        datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc),
    )
    assert isinstance(context, DeliveryStartContext)
    assert context.parent_directory == tmp_path

    with pytest.raises(DeliveryContractError) as error:
        build_delivery_start_context(
            current,
            tmp_path,
            "delivery",
            datetime(2026, 8, 30, 12, 0),
        )
    assert error.value.code == "delivery_start_context_invalid"


def test_commit_fingerprint_ignores_projection_generation_but_rejects_stale_state(tmp_path):
    result, _ = _evaluate_ready(tmp_path)
    current = result.candidate_state
    assert current is not None
    context = build_delivery_start_context(
        current,
        tmp_path,
        "delivery",
        datetime.now(timezone.utc),
    )

    projected = replace(
        current.diagnostics_snapshot,
        projection_generation=current.diagnostics_snapshot.projection_generation + 1,
    )
    changed = replace(
        current.diagnostics_snapshot,
        save_state_fingerprint="sha256:changed",
    )

    allowed = evaluate_delivery_commit_fingerprint(context, projected)
    stale = evaluate_delivery_commit_fingerprint(context, changed)
    missing = evaluate_delivery_commit_fingerprint(context, None)

    assert allowed.allowed is True
    assert allowed.reason_code is None
    assert stale.allowed is False
    assert stale.reason_code == "delivery_state_stale"
    assert missing.reason_code == "delivery_commit_snapshot_unavailable"
