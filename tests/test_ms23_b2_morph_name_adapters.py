from dataclasses import dataclass
import struct

import pytest

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    resolve_effective_shape_plan,
)
from src.core.morph_name_sets import (
    JAPANESE_OUTPUT_NAMES,
    LATIN_OUTPUT_NAMES,
)
from src.core.output_diagnostics import (
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    EffectiveMorphFrameInput,
    EffectiveTailInput,
    EffectiveWriterInput,
    VmdWriterParameters,
    build_output_diagnostics_snapshot,
)
from src.core.preview_transform import (
    build_preview_data,
    build_preview_data_from_effective_shape_plan,
    empty_preview_data,
)
from src.core.whisper_timing import SpeechTimingAnchor
from src.gui_wx.preview_panel import PreviewModel
from src.vmd_writer import VowelTimelinePoint, write_morph_frames_vmd, write_morph_vmd
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)


@dataclass(frozen=True)
class Point:
    time_sec: float
    vowel: str = "あ"
    value: float = 0.5
    peak_value: float | None = None
    duration_sec: float = 0.2
    start_sec: float | None = None
    end_sec: float | None = None


def _effective_plan():
    return resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(Point(0.3, start_sec=0.2, end_sec=0.4),),
            observations=None,
            source_duration_frames=60,
        )
    )


def _read_morph_frames(path):
    data = path.read_bytes()
    morph_count = struct.unpack_from("<I", data, 54)[0]
    frames = []
    offset = 58
    for _ in range(morph_count):
        name = data[offset : offset + 15].split(b"\0", 1)[0].decode("shift_jis")
        frame_no = struct.unpack_from("<I", data, offset + 15)[0]
        value = struct.unpack_from("<f", data, offset + 19)[0]
        frames.append((frame_no, name, value))
        offset += 23
    return tuple(frames)


def test_effective_shape_adapter_maps_names_without_changing_frame_data() -> None:
    plan = _effective_plan()
    japanese = build_morph_frames_from_effective_shape_plan(
        plan,
        apply_final_normalization=False,
    )
    latin = build_morph_frames_from_effective_shape_plan(
        plan,
        apply_final_normalization=False,
        output_morph_names=LATIN_OUTPUT_NAMES,
    )

    assert tuple((frame_no, value) for frame_no, _, value in japanese) == tuple(
        (frame_no, value) for frame_no, _, value in latin
    )
    assert {name for _, name, _ in japanese} == {"あ"}
    assert {name for _, name, _ in latin} == {"A"}


def test_write_morph_vmd_maps_after_normalization_and_preserves_frame_data(tmp_path) -> None:
    timeline = (
        VowelTimelinePoint(
            time_sec=0.3,
            vowel="あ",
            value=0.4,
            duration_sec=0.2,
            start_sec=0.2,
            end_sec=0.4,
        ),
    )
    japanese_path = tmp_path / "japanese.vmd"
    latin_path = tmp_path / "latin.vmd"
    write_morph_vmd(japanese_path, timeline)
    write_morph_vmd(latin_path, timeline, output_morph_names=LATIN_OUTPUT_NAMES)

    japanese = _read_morph_frames(japanese_path)
    latin = _read_morph_frames(latin_path)
    assert tuple(frame_no for frame_no, _, _ in japanese) == tuple(
        frame_no for frame_no, _, _ in latin
    )
    assert tuple(value for _, _, value in japanese) == pytest.approx(
        tuple(value for _, _, value in latin)
    )
    assert {name for _, name, _ in japanese} == {"あ"}
    assert {name for _, name, _ in latin} == {"A"}
    assert len(japanese) == len(latin)


def test_resolved_frame_writer_accepts_latin_and_rejects_unresolved_name(tmp_path) -> None:
    output_path = tmp_path / "latin-frames.vmd"
    write_morph_frames_vmd(
        output_path,
        ((3, "A", 0.25),),
        output_morph_names=LATIN_OUTPUT_NAMES,
    )
    assert _read_morph_frames(output_path)[0][1] == "A"

    with pytest.raises(ValueError):
        write_morph_frames_vmd(
            tmp_path / "invalid.vmd",
            ((3, "あ", 0.25),),
            output_morph_names=LATIN_OUTPUT_NAMES,
        )


def test_preview_empty_effective_and_timeline_paths_keep_latin_display_names() -> None:
    empty = empty_preview_data(output_morph_names=LATIN_OUTPUT_NAMES)
    empty_timeline = build_preview_data(None, output_morph_names=LATIN_OUTPUT_NAMES)
    effective = build_preview_data_from_effective_shape_plan(
        _effective_plan(),
        output_morph_names=LATIN_OUTPUT_NAMES,
    )
    timeline = build_preview_data(
        [
            VowelTimelinePoint(
                time_sec=0.3,
                vowel="あ",
                value=0.4,
                duration_sec=0.2,
                start_sec=0.2,
                end_sec=0.4,
            )
        ],
        output_morph_names=LATIN_OUTPUT_NAMES,
    )

    for preview in (empty, empty_timeline, effective, timeline):
        assert [row.display_name for row in preview.rows] == list(LATIN_OUTPUT_NAMES)
        assert [row.vowel for row in preview.rows] == list(JAPANESE_OUTPUT_NAMES)
    assert effective.rows[0].segments[0].display_name == "A"
    assert effective.rows[0].segments[0].vowel == "あ"
    assert timeline.rows[0].segments[0].display_name == "A"


def test_preview_model_clear_preserves_explicit_names_and_default_compatibility() -> None:
    model = PreviewModel()
    model.clear(output_morph_names=LATIN_OUTPUT_NAMES)
    assert [row.display_name for row in model.data.rows] == list(LATIN_OUTPUT_NAMES)
    model.clear()
    assert [row.display_name for row in model.data.rows] == list(JAPANESE_OUTPUT_NAMES)


def _diagnostic_input(effective_writer_input: EffectiveWriterInput) -> DiagnosticSnapshotInput:
    timing_plan = DiagnosticTimingPlanInput(
        vowels=("あ",),
        timeline=(
            VowelTimelinePoint(
                time_sec=0.2,
                vowel="あ",
                value=0.4,
                duration_sec=0.2,
                start_sec=0.1,
                end_sec=0.3,
            ),
        ),
        anchors=(SpeechTimingAnchor(start_sec=0.1, end_sec=0.3, text="あ"),),
        source="test",
        warning=None,
        observations=(),
    )
    return DiagnosticSnapshotInput(
        input_mode="text_audio",
        text_path=None,
        text_content_present=False,
        source_audio_path=None,
        effective_wav_path=None,
        analysis_text_present=True,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
        timing_plan=timing_plan,
        existing_vmd_save_ready=True,
        writer_parameters=VmdWriterParameters(),
        effective_writer_input_state="ready",
        effective_writer_input=effective_writer_input,
    )


def test_diagnostics_allowed_names_and_fingerprint_follow_resolved_frames() -> None:
    japanese_input = EffectiveWriterInput(
        shape_count=1,
        morph_frames=(EffectiveMorphFrameInput(3, "あ", 0.25),),
        tails=(EffectiveTailInput(0, "あ", 0, 0, 0.0, False),),
        allowed_morph_names=JAPANESE_OUTPUT_NAMES,
    )
    latin_input = EffectiveWriterInput(
        shape_count=1,
        morph_frames=(EffectiveMorphFrameInput(3, "A", 0.25),),
        tails=(EffectiveTailInput(0, "あ", 0, 0, 0.0, False),),
        allowed_morph_names=LATIN_OUTPUT_NAMES,
    )
    japanese = build_output_diagnostics_snapshot(_diagnostic_input(japanese_input))
    latin = build_output_diagnostics_snapshot(_diagnostic_input(latin_input))

    assert japanese.fingerprint_payload != latin.fingerprint_payload

    with pytest.raises(ValueError):
        EffectiveWriterInput(
            shape_count=1,
            morph_frames=(EffectiveMorphFrameInput(3, "A", 0.25),),
            tails=(),
        )
