from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, UiState
from src.core.audio_processing import WavAnalysisResult
from src.core.audio_probe import AudioProbeResult, AudioStreamInfo
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    resolve_effective_shape_plan,
)
from src.core.pipeline import VowelTimingPlan
from src.core.whisper_timing import SpeechTimingAnchor
from src.vmd_writer import VowelTimelinePoint


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


def _fixture(tmp_path: Path):
    source_path = tmp_path / "source.wav"
    source_path.write_bytes(b"source")
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
    return state, probe, source_path, ffmpeg_path, effective_plan


def _frame(state: UiState, effective_plan):
    frame = MainFrame.__new__(MainFrame)
    frame.ui_state = state
    frame._analysis_info_in_progress = False
    frame._diagnostics_projection_generation = 0
    frame._active_preset_display_name = None
    frame._current_ui_sync_failure_reason = None
    frame._build_current_ui_sync_context = Mock(
        return_value=SimpleNamespace(effective_plan=effective_plan)
    )
    frame.prepare_current_effective_output = Mock(
        return_value=("ready", effective_plan, None)
    )
    frame._resolved_output_morph_names = Mock(
        return_value=("あ", "い", "う", "え", "お")
    )
    frame.get_closing_hold_frames = Mock(return_value=0)
    frame.get_closing_softness_frames = Mock(return_value=0)
    return frame


def test_capture_uses_one_sync_context_prepare_and_morph_resolution(tmp_path):
    state, probe, source_path, ffmpeg_path, effective_plan = _fixture(tmp_path)
    frame = _frame(state, effective_plan)

    result = MainFrame.capture_current_delivery_state(
        frame,
        ffmpeg_path=ffmpeg_path,
    )

    assert result.status == "ready"
    assert result.candidate_state is not None
    assert result.candidate_state.effective_shape_plan is effective_plan
    assert result.candidate_state.audio_probe is probe
    assert frame._build_current_ui_sync_context.call_count == 1
    assert frame.prepare_current_effective_output.call_count == 1
    assert frame._resolved_output_morph_names.call_count == 1
    assert (
        result.candidate_state.diagnostics_snapshot.adjustment_summary.base_plan_identity_digest
        == effective_plan.base_plan_identity.digest
    )
    assert source_path == result.candidate_state.source_identity.resolved_path


def test_capture_does_not_reprepare_when_sync_context_is_unavailable(tmp_path):
    state, _, _, ffmpeg_path, effective_plan = _fixture(tmp_path)
    frame = _frame(state, effective_plan)
    frame._build_current_ui_sync_context = Mock(return_value=None)
    frame._current_ui_sync_failure_reason = "base_input_unavailable"
    frame.prepare_current_effective_output = Mock(
        side_effect=AssertionError("prepare must not rebuild a failed context")
    )

    result = MainFrame.capture_current_delivery_state(
        frame,
        ffmpeg_path=ffmpeg_path,
    )

    assert result.status == "blocked"
    assert result.candidate_state is None
    assert frame._build_current_ui_sync_context.call_count == 1
    assert frame.prepare_current_effective_output.call_count == 0


def test_capture_candidate_is_independent_of_later_ui_state_mutation(tmp_path):
    state, _, _, ffmpeg_path, effective_plan = _fixture(tmp_path)
    frame = _frame(state, effective_plan)

    result = MainFrame.capture_current_delivery_state(
        frame,
        ffmpeg_path=ffmpeg_path,
    )
    current = result.candidate_state
    assert current is not None
    original_fingerprint = current.start_fingerprint

    state.selected_text_content = "い"
    state.current_timing_plan = None
    state.analysis_result_valid = False

    assert current.start_fingerprint == original_fingerprint
    assert current.effective_shape_plan is effective_plan
    assert current.diagnostics_snapshot.save_state_fingerprint == original_fingerprint


def test_capture_busy_state_does_not_start_current_state_resolution(tmp_path):
    state, _, _, ffmpeg_path, effective_plan = _fixture(tmp_path)
    state.is_busy = True
    frame = _frame(state, effective_plan)

    result = MainFrame.capture_current_delivery_state(
        frame,
        ffmpeg_path=ffmpeg_path,
    )

    assert result.status == "blocked"
    assert "delivery_busy" in result.blocking_codes
    assert frame._build_current_ui_sync_context.call_count == 0
    assert frame.prepare_current_effective_output.call_count == 0
