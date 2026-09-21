import math
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core import (  # noqa: E402
    DiagnosticFailureInput,
    DiagnosticSeverity,
    DiagnosticSnapshotInput,
    DiagnosticTimingPlanInput,
    EffectiveMorphFrameInput,
    EffectiveTailInput,
    EffectiveWriterInput,
    VmdWriterParameters,
    VowelTimingPlan,
    build_output_diagnostics_snapshot,
    build_save_state_fingerprint_payload,
    compute_save_state_fingerprint,
    resolve_vmd_writer_timing_plan,
)
from src.core.pipeline import PeakValueEvaluation, PeakValueObservation  # noqa: E402
from src.core.whisper_timing import SpeechTimingAnchor  # noqa: E402
from src.vmd_writer import VowelTimelinePoint  # noqa: E402


def _make_observation(*, fallback_reason: str | None = None) -> PeakValueObservation:
    evaluation = PeakValueEvaluation(
        interval_start_sec=0.0,
        interval_end_sec=0.25,
        peak_window_start_sec=0.0,
        peak_window_end_sec=0.25,
        local_peak=0.3,
        peak_value=0.3,
        reason="local_peak",
    )
    return PeakValueObservation(
        event_index=0,
        vowel="あ",
        time_sec=0.1,
        initial_interval_start_sec=0.0,
        initial_interval_end_sec=0.25,
        refined_interval_start_sec=0.0,
        refined_interval_end_sec=0.25,
        peak_window_start_sec=0.0,
        peak_window_end_sec=0.25,
        local_peak=0.3,
        global_peak=0.4,
        peak_value=0.3,
        reason="local_peak",
        fallback_reason=fallback_reason,
        window_sample_count=3,
        evaluation=evaluation,
        rms_window_times_sec=(0.0, 0.1, 0.2),
        rms_window_values=(0.1, 0.3, 0.2),
        is_bridgeable_micro_gap_candidate=True,
        bridge_candidate_reason="test",
        previous_non_zero_event_index=None,
        next_non_zero_event_index=1,
        span_start_index=0,
        span_end_index=1,
    )


def _make_plan(
    *,
    observations: tuple[PeakValueObservation, ...] | None = (),
    source: str = "whisper_words",
    warning: str | None = None,
) -> DiagnosticTimingPlanInput:
    return DiagnosticTimingPlanInput(
        vowels=("あ", "い"),
        timeline=(
            VowelTimelinePoint(
                time_sec=0.1,
                vowel="あ",
                value=0.3,
                duration_sec=0.2,
                start_sec=0.0,
                end_sec=0.2,
            ),
            VowelTimelinePoint(
                time_sec=0.3,
                vowel="い",
                value=0.4,
                duration_sec=0.2,
                start_sec=0.2,
                end_sec=0.4,
            ),
        ),
        anchors=(SpeechTimingAnchor(start_sec=0.0, end_sec=0.4, text="test"),),
        source=source,
        warning=warning,
        observations=observations,
    )


def _make_input(
    *,
    plan: DiagnosticTimingPlanInput | None = None,
    input_mode: str = "text_audio",
    existing_vmd_save_ready: bool = True,
    analysis_result_valid: bool = True,
    analysis_pending_rebuild: bool = False,
    text_path: Path | None = Path("Input.TXT"),
    effective_wav_path: Path | None = Path("VOICE.WAV"),
    analysis_text_present: bool = True,
    failure: DiagnosticFailureInput | None = None,
    analysis_cancelled: bool = False,
    effective_writer_input_state: str = "not_applicable",
    effective_writer_input: EffectiveWriterInput | None = None,
    writer_parameters: VmdWriterParameters | None = None,
) -> DiagnosticSnapshotInput:
    return DiagnosticSnapshotInput(
        input_mode=input_mode,
        text_path=text_path,
        text_content_present=text_path is not None,
        source_audio_path=Path("Source.WAV"),
        effective_wav_path=effective_wav_path,
        analysis_text_present=analysis_text_present,
        analysis_result_valid=analysis_result_valid,
        analysis_pending_rebuild=analysis_pending_rebuild,
        timing_plan=plan,
        existing_vmd_save_ready=existing_vmd_save_ready,
        writer_parameters=writer_parameters or VmdWriterParameters(),
        failure=failure,
        analysis_cancelled=analysis_cancelled,
        effective_writer_input_state=effective_writer_input_state,
        effective_writer_input=effective_writer_input,
    )


class OutputDiagnosticsTests(unittest.TestCase):
    def test_invalid_effective_writer_input_blocks_save(self) -> None:
        snapshot = build_output_diagnostics_snapshot(
            _make_input(
                plan=_make_plan(),
                analysis_cancelled=True,
                effective_writer_input_state="invalid",
            )
        )

        self.assertEqual(
            [item.code for item in snapshot.items],
            ["effective_writer_input_unavailable"],
        )
        self.assertEqual(
            snapshot.saveability.blocking_codes,
            ("effective_writer_input_unavailable",),
        )
        self.assertFalse(snapshot.saveability.vmd_save_allowed)
        self.assertIsNone(snapshot.save_state_fingerprint)

    def test_valid_snapshot_is_ready_and_fingerprint_is_stable(self) -> None:
        snapshot_input = _make_input(plan=_make_plan(observations=(_make_observation(),)))

        first = build_output_diagnostics_snapshot(snapshot_input)
        second = build_output_diagnostics_snapshot(snapshot_input)

        self.assertEqual(
            [item.code for item in first.items],
            ["analysis_ready", "vmd_save_ready"],
        )
        self.assertTrue(first.saveability.vmd_save_allowed)
        self.assertEqual(first.save_state_fingerprint, second.save_state_fingerprint)
        self.assertEqual(first.fingerprint_payload, second.fingerprint_payload)
        self.assertRegex(first.save_state_fingerprint or "", r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(first.analysis_summary.max_frame, 12)

    def test_fallbacks_are_warnings_and_do_not_block_save(self) -> None:
        snapshot = build_output_diagnostics_snapshot(
            _make_input(
                plan=_make_plan(
                    observations=(_make_observation(fallback_reason="rms_unavailable"),),
                    source="even_fallback",
                    warning="ignored display text",
                )
            )
        )

        self.assertEqual(
            [item.code for item in snapshot.items],
            [
                "timing_fallback_used",
                "observation_fallback_used",
                "analysis_ready",
                "vmd_save_ready",
            ],
        )
        self.assertEqual(snapshot.saveability.warning_codes, ("timing_fallback_used", "observation_fallback_used"))
        self.assertTrue(snapshot.saveability.vmd_save_allowed)

    def test_error_conditions_are_ordered_and_ready_info_is_suppressed(self) -> None:
        snapshot = build_output_diagnostics_snapshot(
            _make_input(
                plan=None,
                text_path=None,
                effective_wav_path=None,
                analysis_result_valid=False,
                existing_vmd_save_ready=False,
            )
        )

        self.assertEqual(
            [item.code for item in snapshot.items],
            ["analysis_not_ready", "text_input_missing", "audio_input_missing"],
        )
        self.assertFalse(snapshot.saveability.vmd_save_allowed)
        self.assertEqual(snapshot.saveability.blocking_codes, tuple(item.code for item in snapshot.items))

    def test_rebuild_suppresses_not_ready_and_voice_only_requires_transcription(self) -> None:
        rebuild = build_output_diagnostics_snapshot(
            _make_input(
                plan=None,
                input_mode="voice_only",
                analysis_result_valid=False,
                analysis_pending_rebuild=True,
                text_path=None,
                analysis_text_present=False,
            )
        )
        self.assertIn("analysis_rebuild_required", [item.code for item in rebuild.items])
        self.assertNotIn("analysis_not_ready", [item.code for item in rebuild.items])
        self.assertIn("voice_only_text_missing", [item.code for item in rebuild.items])

    def test_empty_plan_and_explicit_failure_are_distinct(self) -> None:
        empty_plan = DiagnosticTimingPlanInput(
            vowels=(),
            timeline=(),
            anchors=(),
            source="whisper_words",
            observations=(),
        )
        empty = build_output_diagnostics_snapshot(_make_input(plan=empty_plan))
        self.assertIn("timing_plan_empty", [item.code for item in empty.items])
        self.assertNotIn("analysis_not_ready", [item.code for item in empty.items])

        failure = DiagnosticFailureInput(
            code="whisper_failed",
            source_severity="fatal",
            phase="whisper_transcribe",
            recoverability="retry_possible",
            identity_context=(("provider", "local"),),
            summary="raw message must not be hashed",
            detail="another raw message",
        )
        failed = build_output_diagnostics_snapshot(_make_input(plan=_make_plan(), failure=failure))
        failure_item = next(item for item in failed.items if item.code == "analysis_failure")
        self.assertEqual(failure_item.severity, DiagnosticSeverity.ERROR)
        self.assertIn("whisper_failed", repr(failure_item.identity_context))
        self.assertFalse(failed.saveability.vmd_save_allowed)

    def test_nonfinite_input_fails_closed_without_hash(self) -> None:
        nonfinite_plan = DiagnosticTimingPlanInput(
            vowels=("あ",),
            timeline=(
                VowelTimelinePoint(
                    time_sec=math.nan,
                    vowel="あ",
                    value=0.3,
                    duration_sec=0.2,
                    start_sec=0.0,
                    end_sec=0.2,
                ),
            ),
            anchors=(),
            source="whisper_words",
            observations=None,
        )
        snapshot = build_output_diagnostics_snapshot(_make_input(plan=nonfinite_plan))

        self.assertIn("analysis_failure", [item.code for item in snapshot.items])
        self.assertFalse(snapshot.saveability.vmd_save_allowed)
        self.assertIsNone(snapshot.fingerprint_payload)
        self.assertIsNone(snapshot.save_state_fingerprint)
        failure_item = next(item for item in snapshot.items if item.code == "analysis_failure")
        self.assertIn("writer_input_non_finite", repr(failure_item.identity_context))

    def test_structural_writer_contract_raises_value_error(self) -> None:
        bad_plan = DiagnosticTimingPlanInput(
            vowels=("か",),
            timeline=(VowelTimelinePoint(time_sec=0.1, vowel="か"),),
            anchors=(),
            source="whisper_words",
        )
        with self.assertRaises(ValueError):
            build_output_diagnostics_snapshot(_make_input(plan=bad_plan))
        with self.assertRaises(ValueError):
            VmdWriterParameters(closing_hold_frames=-1)

    def test_raw_observations_do_not_change_effective_output_identity(self) -> None:
        none_snapshot = build_output_diagnostics_snapshot(_make_input(plan=_make_plan(observations=None)))
        empty_snapshot = build_output_diagnostics_snapshot(_make_input(plan=_make_plan(observations=())))
        self.assertEqual(none_snapshot.fingerprint_payload, empty_snapshot.fingerprint_payload)
        self.assertEqual(none_snapshot.save_state_fingerprint, empty_snapshot.save_state_fingerprint)

    def test_effective_frames_and_tails_change_output_identity(self) -> None:
        first_input = EffectiveWriterInput(
            shape_count=1,
            morph_frames=(EffectiveMorphFrameInput(0, "あ", 0.0),),
            tails=(EffectiveTailInput(0, "あ", 2, 1, 0.5, True),),
        )
        second_input = EffectiveWriterInput(
            shape_count=1,
            morph_frames=(EffectiveMorphFrameInput(0, "あ", 0.1),),
            tails=(EffectiveTailInput(0, "あ", 2, 1, 0.5, True),),
        )
        first = build_output_diagnostics_snapshot(
            _make_input(
                plan=_make_plan(),
                effective_writer_input_state="ready",
                effective_writer_input=first_input,
            )
        )
        second = build_output_diagnostics_snapshot(
            _make_input(
                plan=_make_plan(),
                effective_writer_input_state="ready",
                effective_writer_input=second_input,
            )
        )
        self.assertNotEqual(first.save_state_fingerprint, second.save_state_fingerprint)
        self.assertEqual(first.adjustment_summary.effective_shape_count, 1)
        self.assertEqual(first.adjustment_summary.effective_morph_frame_count, 1)

    def test_paths_and_summary_text_do_not_change_identity(self) -> None:
        first_input = _make_input(plan=_make_plan())
        first = build_output_diagnostics_snapshot(first_input)
        failure = DiagnosticFailureInput(
            code="diagnostic_notice",
            source_severity="info",
            phase="pipeline_build",
            recoverability="fallback_used",
            summary="one",
            detail="two",
        )
        second_input = _make_input(plan=_make_plan(), failure=failure)
        second = build_output_diagnostics_snapshot(second_input)
        self.assertNotEqual(first.save_state_fingerprint, second.save_state_fingerprint)

        changed_text = DiagnosticFailureInput(
            code="diagnostic_notice",
            source_severity="info",
            phase="pipeline_build",
            recoverability="fallback_used",
            summary="changed",
            detail="changed detail",
        )
        third = build_output_diagnostics_snapshot(_make_input(plan=_make_plan(), failure=changed_text))
        self.assertEqual(second.save_state_fingerprint, third.save_state_fingerprint)

        path_input = _make_input(plan=_make_plan())
        path_variant = _make_input(plan=_make_plan())
        object.__setattr__(path_variant, "text_path", Path("input.txt"))
        object.__setattr__(path_variant, "effective_wav_path", Path("voice.wav"))
        self.assertEqual(
            build_output_diagnostics_snapshot(path_input).input_summary.normalized_text_path,
            build_output_diagnostics_snapshot(path_variant).input_summary.normalized_text_path,
        )

    def test_dto_collections_are_copied_and_frozen(self) -> None:
        vowels = ["あ"]
        timeline = [VowelTimelinePoint(time_sec=0.1, vowel="あ", duration_sec=0.2)]
        anchors = [SpeechTimingAnchor(start_sec=0.0, end_sec=0.2, text="a")]
        observations = [_make_observation()]
        dto = DiagnosticTimingPlanInput(vowels, timeline, anchors, "whisper_words", observations=observations)
        vowels.append("い")
        timeline.clear()
        anchors.clear()
        observations.clear()
        self.assertIsInstance(dto.vowels, tuple)
        self.assertIsInstance(dto.timeline, tuple)
        self.assertIsInstance(dto.anchors, tuple)
        self.assertIsInstance(dto.observations, tuple)
        with self.assertRaises(FrozenInstanceError):
            dto.source = "changed"  # type: ignore[misc]

    def test_shared_helper_repairs_nonpositive_duration_and_drops_observations(self) -> None:
        plan = VowelTimingPlan(
            vowels=["あ", "い"],
            timeline=[
                VowelTimelinePoint(time_sec=0.1, vowel="あ"),
                VowelTimelinePoint(time_sec=0.3, vowel="い"),
            ],
            anchors=[],
            source="whisper_words",
            observations=[_make_observation()],
        )
        resolved = resolve_vmd_writer_timing_plan(
            plan,
            speech_start_sec=0.0,
            speech_end_sec=0.4,
        )
        self.assertTrue(all(point.duration_sec > 0 for point in resolved.timeline))
        self.assertIsNone(resolved.observations)
        diagnostic_input = DiagnosticTimingPlanInput.from_timing_plan(resolved)
        self.assertIsNone(diagnostic_input.observations)

    def test_public_payload_function_and_hash_function(self) -> None:
        snapshot_input = _make_input(plan=_make_plan())
        snapshot = build_output_diagnostics_snapshot(snapshot_input)
        payload = build_save_state_fingerprint_payload(snapshot_input, snapshot.items)
        self.assertEqual(compute_save_state_fingerprint(payload), snapshot.save_state_fingerprint)


if __name__ == "__main__":
    unittest.main()
