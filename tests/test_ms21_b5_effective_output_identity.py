from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.core import (
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    EffectiveMorphFrameInput,
    EffectiveTailInput,
    EffectiveWriterInput,
    VmdWriterParameters,
    build_output_diagnostics_snapshot,
)
from src.vmd_writer import VowelTimelinePoint


def _effective_input(
    *,
    value: float = 0.5,
    slope_ratio: float = 0.5,
) -> EffectiveWriterInput:
    return EffectiveWriterInput(
        shape_count=1,
        morph_frames=(
            EffectiveMorphFrameInput(6, "あ", 0.0),
            EffectiveMorphFrameInput(9, "あ", value),
            EffectiveMorphFrameInput(12, "あ", 0.0),
        ),
        tails=(
            EffectiveTailInput(
                shape_ordinal=0,
                vowel="あ",
                effective_hold_frames=2,
                effective_softness_frames=1,
                effective_slope_ratio=slope_ratio,
                has_slope_midpoint=True,
            ),
        ),
    )


def _snapshot_input(
    *,
    effective_input: EffectiveWriterInput | None = None,
    state: str = "ready",
    base_digest: str | None = "sha256:base-a",
) -> DiagnosticSnapshotInput:
    plan = DiagnosticTimingPlanInput(
        vowels=("あ",),
        timeline=(
            VowelTimelinePoint(
                time_sec=0.3,
                vowel="あ",
                value=0.5,
                duration_sec=0.2,
                start_sec=0.2,
                end_sec=0.4,
            ),
        ),
        anchors=(),
        source="whisper_words",
        observations=None,
    )
    return DiagnosticSnapshotInput(
        input_mode="text_audio",
        text_path=Path("input.txt"),
        text_content_present=True,
        source_audio_path=Path("source.wav"),
        effective_wav_path=Path("analysis.wav"),
        analysis_text_present=True,
        analysis_result_valid=True,
        analysis_pending_rebuild=False,
        timing_plan=plan,
        existing_vmd_save_ready=True,
        writer_parameters=VmdWriterParameters(),
        effective_writer_input_state=state,
        effective_writer_input=effective_input,
        base_plan_identity_digest=base_digest,
        adjustment_present=True,
        adjusted_event_count=1,
    )


def test_base_identity_is_report_metadata_not_save_identity() -> None:
    first = build_output_diagnostics_snapshot(
        _snapshot_input(effective_input=_effective_input())
    )
    second = build_output_diagnostics_snapshot(
        _snapshot_input(
            effective_input=_effective_input(),
            base_digest="sha256:base-b",
        )
    )

    assert first.save_state_fingerprint == second.save_state_fingerprint
    assert first.adjustment_summary.base_plan_identity_digest != (
        second.adjustment_summary.base_plan_identity_digest
    )
    assert first.generation_summary.fingerprint_schema_version == (
        "ms21-effective-output-v1"
    )


def test_effective_frame_or_tail_change_changes_save_identity() -> None:
    original = build_output_diagnostics_snapshot(
        _snapshot_input(effective_input=_effective_input())
    )
    frame_changed = build_output_diagnostics_snapshot(
        _snapshot_input(effective_input=_effective_input(value=0.4))
    )
    tail_changed = build_output_diagnostics_snapshot(
        _snapshot_input(effective_input=_effective_input(slope_ratio=0.75))
    )

    assert original.save_state_fingerprint != frame_changed.save_state_fingerprint
    assert original.save_state_fingerprint != tail_changed.save_state_fingerprint


def test_raw_writer_parameters_do_not_change_identical_effective_output() -> None:
    original_input = _snapshot_input(effective_input=_effective_input())
    changed_input = replace(
        original_input,
        writer_parameters=VmdWriterParameters(
            closing_hold_frames=9,
            closing_softness_frames=8,
        ),
    )

    original = build_output_diagnostics_snapshot(original_input)
    changed = build_output_diagnostics_snapshot(changed_input)

    assert original.save_state_fingerprint == changed.save_state_fingerprint


def test_not_applicable_is_deterministic_and_invalid_fails_closed() -> None:
    not_applicable_input = _snapshot_input(
        effective_input=None,
        state="not_applicable",
        base_digest=None,
    )
    first = build_output_diagnostics_snapshot(not_applicable_input)
    second = build_output_diagnostics_snapshot(not_applicable_input)
    invalid = build_output_diagnostics_snapshot(
        replace(
            not_applicable_input,
            effective_writer_input_state="invalid",
            effective_writer_input_failure_reason="adapter_failed",
        )
    )

    assert first.save_state_fingerprint == second.save_state_fingerprint
    assert "effective_writer_input_unavailable" not in first.saveability.blocking_codes
    assert invalid.save_state_fingerprint is None
    assert invalid.saveability.blocking_codes == (
        "effective_writer_input_unavailable",
    )
