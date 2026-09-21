from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from gui_wx.output_diagnostics_adapter import (
    build_output_diagnostics_snapshot_from_ui_state,
    format_output_diagnostics_info,
)
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, INPUT_MODE_VOICE_ONLY, UiState
from src.core import (
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    SpeechTimingAnchor,
    VmdWriterParameters,
    VowelTimingPlan,
    build_output_diagnostics_snapshot,
    resolve_vmd_writer_timing_plan,
)
from src.core.audio_processing import WavAnalysisResult
from src.core.effective_shape_plan import BaseTimingPlanInput, resolve_effective_shape_plan
from src.core.morph_name_sets import LATIN_OUTPUT_NAMES
from src.vmd_writer import VowelTimelinePoint


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


def _timing_plan(*, duration_sec: float = 0.2, warning: str | None = None) -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.3,
                vowel="あ",
                duration_sec=duration_sec,
                start_sec=0.2 if duration_sec > 0.0 else None,
                end_sec=0.4 if duration_sec > 0.0 else None,
            )
        ],
        anchors=[SpeechTimingAnchor(start_sec=0.2, end_sec=0.4, text="あ")],
        source="even_fallback" if warning else "whisper_segments",
        warning=warning,
        observations=[],
    )


def _ready_text_audio_state(
    *,
    timing_plan: VowelTimingPlan | None = None,
) -> UiState:
    state = UiState(
        selected_text_path="input.txt",
        selected_text_content="あ",
        selected_wav_path="source.wav",
        selected_wav_analysis=_wav_analysis(),
        input_mode=INPUT_MODE_TEXT_AUDIO,
    )
    state.mark_analysis_success(
        timing_plan or _timing_plan(),
        input_mode=INPUT_MODE_TEXT_AUDIO,
        analysis_text_content="あ",
        analysis_text_source="text_file",
    )
    return state


def test_adapter_module_does_not_import_wx_widgets():
    import gui_wx.output_diagnostics_adapter as adapter

    assert "wx" not in adapter.__dict__
    assert "RightPane" not in adapter.__dict__
    assert "MainFrame" not in adapter.__dict__


def test_initial_state_builds_not_ready_non_saveable_snapshot():
    snapshot = build_output_diagnostics_snapshot_from_ui_state(UiState())

    assert snapshot.analysis_summary.analysis_result_valid is False
    assert snapshot.analysis_summary.event_count == 0
    assert snapshot.saveability.vmd_save_allowed is False
    assert snapshot.input_summary.input_mode == INPUT_MODE_TEXT_AUDIO


def test_adapter_maps_paths_and_writer_parameters_with_expected_priority():
    state = _ready_text_audio_state()
    state.selected_audio_input = SimpleNamespace(source_path=Path("original.mp3"))
    state.selected_analysis_wav = SimpleNamespace(
        analysis_wav_path=Path("cache/analysis.wav")
    )

    snapshot = build_output_diagnostics_snapshot_from_ui_state(
        state,
        closing_hold_frames=3,
        closing_softness_frames=4,
    )

    assert snapshot.input_summary.normalized_source_audio_path.endswith(
        "/original.mp3"
    )
    assert snapshot.input_summary.normalized_effective_wav_path.endswith(
        "/cache/analysis.wav"
    )
    assert snapshot.generation_summary.vmd_model_name == "AutoLipTool"
    assert snapshot.generation_summary.closing_hold_frames == 3
    assert snapshot.generation_summary.closing_softness_frames == 4


def test_adapter_falls_back_to_selected_wav_path():
    state = _ready_text_audio_state()

    snapshot = build_output_diagnostics_snapshot_from_ui_state(state)

    assert snapshot.input_summary.normalized_source_audio_path.endswith("/source.wav")
    assert snapshot.input_summary.normalized_effective_wav_path.endswith("/source.wav")


def test_voice_only_state_maps_analysis_text_and_saveability():
    state = UiState(
        selected_wav_path="voice.wav",
        selected_wav_analysis=_wav_analysis(),
        input_mode=INPUT_MODE_VOICE_ONLY,
    )
    state.mark_analysis_success(
        _timing_plan(),
        input_mode=INPUT_MODE_VOICE_ONLY,
        analysis_text_content="あ",
        analysis_text_source="whisper_transcription",
        transcription_text="あ",
        transcription_source="segments",
        transcription_timing_source="segments",
    )

    snapshot = build_output_diagnostics_snapshot_from_ui_state(state)

    assert snapshot.input_summary.input_mode == INPUT_MODE_VOICE_ONLY
    assert snapshot.input_summary.text_content_present is False
    assert snapshot.input_summary.analysis_text_present is True
    assert snapshot.saveability.vmd_save_allowed is True


def test_non_positive_duration_uses_writer_resolution_and_matching_fingerprint():
    state = _ready_text_audio_state(timing_plan=_timing_plan(duration_sec=0.0))

    snapshot = build_output_diagnostics_snapshot_from_ui_state(state)
    resolved = resolve_vmd_writer_timing_plan(
        state.current_timing_plan,
        speech_start_sec=state.selected_wav_analysis.speech_start_sec,
        speech_end_sec=state.selected_wav_analysis.speech_end_sec,
    )
    expected = build_output_diagnostics_snapshot(
        DiagnosticSnapshotInput(
            input_mode=state.input_mode,
            text_path=Path(state.selected_text_path),
            text_content_present=True,
            source_audio_path=Path(state.selected_wav_path),
            effective_wav_path=Path(state.selected_wav_path),
            analysis_text_present=True,
            analysis_result_valid=True,
            analysis_pending_rebuild=False,
            timing_plan=DiagnosticTimingPlanInput.from_timing_plan(resolved),
            existing_vmd_save_ready=True,
            writer_parameters=VmdWriterParameters(),
        )
    )

    assert snapshot.analysis_summary.event_count == 1
    assert snapshot.save_state_fingerprint == expected.save_state_fingerprint
    assert snapshot.fingerprint_payload == expected.fingerprint_payload


def test_non_positive_duration_requires_speech_interval():
    state = _ready_text_audio_state(timing_plan=_timing_plan(duration_sec=0.0))
    state.selected_wav_analysis = None

    with pytest.raises(ValueError, match="selected_wav_analysis"):
        build_output_diagnostics_snapshot_from_ui_state(state)


def test_adapter_passes_explicit_latin_names_to_effective_diagnostics():
    state = _ready_text_audio_state()
    effective_plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(
                VowelTimelinePoint(
                    time_sec=0.3,
                    vowel="あ",
                    duration_sec=0.2,
                    start_sec=0.2,
                    end_sec=0.4,
                ),
            ),
            observations=None,
            source_duration_frames=60,
        )
    )

    snapshot = build_output_diagnostics_snapshot_from_ui_state(
        state,
        effective_shape_plan=effective_plan,
        effective_writer_input_state="ready",
        output_morph_names=LATIN_OUTPUT_NAMES,
    )

    assert snapshot.saveability.vmd_save_allowed is True
    morph_frames = dict(snapshot.fingerprint_payload)["effective_morph_frames"]
    assert any(("morph_name", "A") in frame for frame in morph_frames)


def test_adapter_rejects_non_production_timing_plan():
    state = _ready_text_audio_state()
    state.current_timing_plan = SimpleNamespace(timeline=[])

    with pytest.raises(ValueError, match="VowelTimingPlan"):
        build_output_diagnostics_snapshot_from_ui_state(state)


def test_analysis_in_progress_masks_old_plan_without_mutating_state():
    state = _ready_text_audio_state()
    original_plan = state.current_timing_plan

    snapshot = build_output_diagnostics_snapshot_from_ui_state(
        state,
        analysis_in_progress=True,
    )

    assert snapshot.analysis_summary.analysis_result_valid is False
    assert snapshot.analysis_summary.analysis_pending_rebuild is True
    assert snapshot.analysis_summary.event_count == 0
    assert snapshot.analysis_summary.max_frame is None
    assert snapshot.saveability.vmd_save_allowed is False
    assert state.current_timing_plan is original_plan
    assert state.analysis_result_valid is True


def test_adapter_copies_plan_collections_without_mutating_source():
    state = _ready_text_audio_state()
    before = deepcopy(state.current_timing_plan)

    snapshot = build_output_diagnostics_snapshot_from_ui_state(state)

    assert state.current_timing_plan == before
    assert snapshot.analysis_summary.event_count == 1
    state.current_timing_plan.timeline.append(
        VowelTimelinePoint(time_sec=0.7, vowel="い", duration_sec=0.1)
    )
    assert snapshot.analysis_summary.event_count == 1


def test_formatter_has_fixed_sections_and_omits_diagnostic_details():
    state = _ready_text_audio_state(timing_plan=_timing_plan(warning="raw warning"))
    snapshot = build_output_diagnostics_snapshot_from_ui_state(state)

    text = format_output_diagnostics_info(snapshot)

    assert text.index("[入力]") < text.index("[解析]") < text.index("[生成]")
    assert text.index("[生成]") < text.index("[保存可否]")
    assert "入力モード: TEXT + 音声" in text
    assert "状態: 解析済み" in text
    assert "要確認警告数: 1 件" in text
    assert "raw warning" not in text
    assert "sha256:" not in text


def test_formatter_distinguishes_progress_pending_and_empty_values():
    state = _ready_text_audio_state()
    progress_snapshot = build_output_diagnostics_snapshot_from_ui_state(
        state,
        analysis_in_progress=True,
    )
    progress_text = format_output_diagnostics_info(
        progress_snapshot,
        analysis_in_progress=True,
    )
    state.invalidate_analysis()
    pending_text = format_output_diagnostics_info(
        build_output_diagnostics_snapshot_from_ui_state(state)
    )

    assert "状態: 解析中" in progress_text
    assert "母音イベント数: 0 件" in progress_text
    assert "最大フレーム: (未算出)" in progress_text
    assert "状態: 再解析が必要" in pending_text
    assert "VMD保存: 不可" in pending_text
