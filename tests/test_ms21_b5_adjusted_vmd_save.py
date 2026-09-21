from __future__ import annotations

import struct
from unittest.mock import patch

import pytest

from src.core.audio_processing import WavAnalysisResult
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    resolve_effective_shape_plan,
)
from src.core.pipeline import (
    VowelTimingPlan,
    generate_vmd_from_text_wav,
    generate_vmd_from_timing_plan,
)
from src.vmd_writer import write_morph_frames_vmd, write_morph_vmd
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)
from src.vmd_writer.writer import VowelTimelinePoint


def _analysis() -> WavAnalysisResult:
    return WavAnalysisResult(
        sample_rate_hz=44100,
        frame_count=44100,
        channel_count=1,
        duration_sec=1.0,
        leading_silence_end_sec=0.0,
        trailing_silence_start_sec=1.0,
        speech_start_sec=0.0,
        speech_end_sec=1.0,
        has_speech=True,
    )


def _timing_plan() -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.3,
                vowel="あ",
                value=0.5,
                duration_sec=0.2,
                start_sec=0.2,
                end_sec=0.4,
            )
        ],
        anchors=[],
        source="whisper_words",
        observations=None,
    )


def _effective_plan():
    return resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=tuple(_timing_plan().timeline),
            observations=None,
            source_duration_frames=30,
            shape_parameters=ShapeParameters(
                closing_hold_frames=2,
                closing_softness_frames=1,
            ),
        )
    )


def test_prepared_writer_preserves_legacy_binary_for_base_only_plan(tmp_path) -> None:
    plan = _effective_plan()
    legacy_path = tmp_path / "legacy.vmd"
    prepared_path = tmp_path / "prepared.vmd"

    write_morph_vmd(
        legacy_path,
        _timing_plan().timeline,
        closing_hold_frames=2,
        closing_softness_frames=1,
    )
    prepared_frames = build_morph_frames_from_effective_shape_plan(plan)
    write_morph_frames_vmd(prepared_path, prepared_frames)

    assert prepared_path.read_bytes() == legacy_path.read_bytes()
    data = prepared_path.read_bytes()
    assert data[:30].rstrip(b"\0") == b"Vocaloid Motion Data 0002"
    assert struct.unpack("<I", data[50:54])[0] == 0
    assert struct.unpack("<I", data[54:58])[0] == len(prepared_frames)
    assert data[-16:] == b"\0" * 16


@pytest.mark.parametrize("mode", ["text_audio", "voice_only"])
def test_pipeline_uses_only_prepared_writer_for_effective_plan(
    tmp_path,
    mode: str,
) -> None:
    text_path = tmp_path / "input.txt"
    text_path.write_text("あ", encoding="utf-8")
    wav_path = tmp_path / "input.wav"
    wav_path.write_bytes(b"placeholder")
    output_path = tmp_path / "output.vmd"
    timing_plan = _timing_plan()
    effective_plan = _effective_plan()
    prepared_frames = ((0, "あ", 0.0), (9, "あ", 0.5), (12, "あ", 0.0))

    with (
        patch("src.core.pipeline.analyze_wav_file", return_value=_analysis()),
        patch(
            "src.core.pipeline.build_morph_frames_from_effective_shape_plan",
            return_value=prepared_frames,
        ) as adapter,
        patch("src.core.pipeline.write_morph_frames_vmd") as prepared_writer,
        patch("src.core.pipeline.write_morph_vmd") as legacy_writer,
    ):
        if mode == "text_audio":
            generate_vmd_from_text_wav(
                text_path,
                wav_path,
                output_path,
                timing_plan=timing_plan,
                effective_shape_plan=effective_plan,
            )
        else:
            generate_vmd_from_timing_plan(
                wav_path,
                output_path,
                timing_plan=timing_plan,
                effective_shape_plan=effective_plan,
            )

    adapter.assert_called_once_with(effective_plan)
    prepared_writer.assert_called_once_with(
        output_path=output_path,
        morph_frames=prepared_frames,
        model_name="AutoLipTool",
    )
    legacy_writer.assert_not_called()


@pytest.mark.parametrize(
    "frame",
    [
        (-1, "あ", 0.0),
        (0, "か", 0.0),
        (0, "あ", -0.1),
        (0, "あ", float("nan")),
    ],
)
def test_prepared_writer_rejects_invalid_frames(tmp_path, frame) -> None:
    with pytest.raises(ValueError):
        write_morph_frames_vmd(tmp_path / "invalid.vmd", (frame,))
