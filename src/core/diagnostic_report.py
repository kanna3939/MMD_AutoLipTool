"""Deterministic plain-text export for MS20 output diagnostics."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .morph_name_sets import get_builtin_morph_name_set
from .output_diagnostics import OutputDiagnosticsSnapshot


_NOT_AVAILABLE = "(not available)"
_ADJUSTMENT_NOT_AVAILABLE = "N/A"
_UTF8_BOM = b"\xef\xbb\xbf"
_SAFE_REPORT_WRITE_ERROR = "診断レポートを安全に保存できませんでした。"


class DiagnosticReportError(Exception):
    """Raised when a diagnostic report cannot be written safely."""


def build_diagnostic_report_default_filename(
    source_audio_path: str | Path | None,
) -> str | None:
    """Return a case-preserving report filename for the original audio input."""
    if source_audio_path is None:
        return None
    raw_path = os.fspath(source_audio_path)
    if not raw_path:
        return None
    stem = Path(raw_path).stem
    if not stem:
        return None
    return f"{stem}_report.txt"


def _single_line(value: Any) -> str:
    if value is None or value == "":
        return _NOT_AVAILABLE
    text = str(value)
    escaped: list[str] = []
    for character in text:
        if character == "\\":
            escaped.append("\\\\")
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\t":
            escaped.append("\\t")
        elif ord(character) < 0x20 or ord(character) == 0x7F:
            escaped.append(f"\\u{ord(character):04x}")
        else:
            escaped.append(character)
    return "".join(escaped)


def _display_bool(value: bool) -> str:
    return "true" if value else "false"


def _display_yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _adjustment_value(value: Any) -> str:
    if value is None or value == "":
        return _ADJUSTMENT_NOT_AVAILABLE
    return _single_line(value)


def _display_codes(codes: tuple[str, ...]) -> str:
    if not codes:
        return _NOT_AVAILABLE
    return ", ".join(_single_line(code) for code in codes)


def _display_ordered_morph_names(values: tuple[str, ...]) -> str:
    return " / ".join(_single_line(value) for value in values)


def _json_compatible(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    return value


def _identity_context_json(context: tuple[tuple[str, Any], ...]) -> str:
    payload = {
        key: _json_compatible(value)
        for key, value in context
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _detail_lines(detail: str) -> list[str]:
    if not detail:
        return [f"    {_NOT_AVAILABLE}"]
    normalized = detail.replace("\r\n", "\n").replace("\r", "\n")
    return [f"    {_single_line(line)}" for line in normalized.split("\n")]


def _shared_final_output_lines(snapshot: OutputDiagnosticsSnapshot) -> list[str]:
    identity = snapshot.shared_final_output_identity
    if identity is None:
        failure = next(
            (
                item
                for item in snapshot.items
                if item.code == "effective_writer_input_unavailable"
                and item.detail.startswith("MS31 final output ")
            ),
            None,
        )
        if failure is not None:
            return [
                "Shared Final Output: failed",
                f"Failure: {_single_line(failure.detail)}",
            ]
        return ["Shared Final Output: (not applicable)"]
    input_identity = getattr(identity, "input_identity", None)
    lines = [
        f"Source Run ID: {_single_line(getattr(input_identity, 'source_run_id', None))}",
        f"Job ID: {_single_line(getattr(input_identity, 'job_id', None))}",
        f"Analysis Generation: {_single_line(getattr(input_identity, 'analysis_generation', None))}",
        f"Manual Revision: {_single_line(getattr(input_identity, 'manual_revision', None))}",
        f"Base Plan Digest: {_single_line(getattr(input_identity, 'base_plan_digest', None))}",
        f"Effective Plan Digest: {_single_line(getattr(input_identity, 'effective_plan_digest', None))}",
        f"Plan Schema ID: {_single_line(getattr(identity, 'plan_schema_id', None))}",
        f"Curve Policy ID: {_single_line(getattr(identity, 'curve_policy_id', None))}",
        f"Legacy Curve Policy ID: {_single_line(getattr(input_identity, 'curve_policy_id', None))}",
        f"Final Semantic Digest: {_single_line(getattr(identity, 'semantic_digest', None))}",
        f"Final Wire Digest: {_single_line(getattr(identity, 'wire_digest', None))}",
        f"Binding Digest: {_single_line(getattr(identity, 'binding_digest', None))}",
        "Restrictions:",
    ]
    restrictions = tuple(snapshot.shared_final_output_restrictions)
    event_targets = tuple(
        snapshot.shared_final_output_restriction_event_targets
    )
    if not restrictions:
        lines.append(f"  {_NOT_AVAILABLE}")
    for restriction in restrictions:
        lines.append(
            "  "
            + " / ".join(
                (
                    _single_line(getattr(restriction, "semantic_morph", None)),
                    f"frame {_single_line(getattr(restriction, 'frame_no', None))}",
                    f"{_single_line(getattr(restriction, 'requested_value_hex', None))}"
                    f" → {_single_line(getattr(restriction, 'effective_value_hex', None))}",
                    _single_line(getattr(restriction, "reason", None)),
                )
            )
        )
        source_ids = tuple(getattr(restriction, "source_ids", ()))
        lines.append(
            "    Sources: "
            + (
                ", ".join(_single_line(source_id) for source_id in source_ids)
                if source_ids
                else _NOT_AVAILABLE
            )
        )
        for target in event_targets:
            if getattr(getattr(target, "restriction", None), "restriction_id", None) != getattr(
                restriction, "restriction_id", None
            ):
                continue
            event = target.event
            lines.append(
                "    Event: "
                f"{_single_line(getattr(event, 'base_event_index', None))} / "
                f"group {_single_line(getattr(event, 'group_event_indices', None))} / "
                f"long {_single_line(getattr(event, 'long_vowel_role', None))} / "
                f"frames {_single_line(getattr(event, 'start_frame', None))}–"
                f"{_single_line(getattr(event, 'end_frame', None))}"
            )
    transition_summary = snapshot.transition_summary
    if transition_summary is not None:
        lines.extend(
            (
                "Transition Candidate Summary:",
                f"  Schema: {_single_line(transition_summary.schema_id)}",
                f"  Summary Digest: {_single_line(transition_summary.summary_digest)}",
                f"  Input Digest: {_single_line(transition_summary.input_digest)}",
                f"  Policy Digest: {_single_line(transition_summary.policy_digest)}",
                f"  Acoustic Digest: {_single_line(transition_summary.acoustic_digest)}",
                f"  Outer Plan: {_single_line(transition_summary.outer_plan_schema_id)} / "
                f"{_single_line(transition_summary.outer_semantic_digest)} / "
                f"{_single_line(transition_summary.outer_wire_digest)}",
                "  Pairs:",
            )
        )
        if not transition_summary.pairs:
            lines.append(f"    {_NOT_AVAILABLE}")
        for pair in transition_summary.pairs:
            owner = (
                pair.next_event_index
                if pair.state == "applied"
                else None
            )
            lines.append(
                "    Pair "
                f"{pair.previous_event_index}→{pair.next_event_index} / "
                f"{_single_line(pair.previous_morph)}→{_single_line(pair.next_morph)} / "
                f"{_single_line(pair.state)} / reason {_single_line(pair.reason)}"
            )
            lines.append(
                "      Owner event: "
                f"{_single_line(owner)} / "
                f"start {pair.baseline_start_frame}→{pair.candidate_start_frame} "
                f"(advance {pair.start_advance_frames}) / "
                f"overlap {pair.baseline_overlap_width_frames:.6f}→"
                f"{pair.candidate_overlap_width_frames:.6f} "
                f"(delta {pair.overlap_width_delta_frames:.6f}) / "
                f"positive frames {pair.baseline_positive_integer_frame_count}→"
                f"{pair.candidate_positive_integer_frame_count} "
                f"(delta {pair.positive_integer_frame_count_delta}) / "
                f"local peak ratio {_single_line(pair.local_peak_ratio)}"
            )
    cleanup_summary = snapshot.cleanup_summary
    if cleanup_summary is not None:
        cleanup_heading = (
            "Cleanup Default Summary:"
            if cleanup_summary.application_origin == "adopted_default"
            else "Cleanup Candidate Summary:"
        )
        lines.extend(
            (
                cleanup_heading,
                f"  Schema: {_single_line(cleanup_summary.schema_id)}",
                f"  Variant: {_single_line(cleanup_summary.variant)}",
                f"  Summary Digest: {_single_line(cleanup_summary.summary_digest)}",
                f"  Final Binding: {_single_line(cleanup_summary.final_binding)}",
                f"  Event Policy Digest: {_single_line(cleanup_summary.policy_digests[0])}",
                f"  Key Policy Digest: {_single_line(cleanup_summary.policy_digests[1])}",
                f"  Source Events: {cleanup_summary.source_event_count}",
                f"  Suppressed Events: {len(cleanup_summary.suppressed_event_ids)}",
                f"  Final Keys: {cleanup_summary.input_key_count} → {cleanup_summary.final_key_count}",
                f"  Reduced Keys: {len(cleanup_summary.removed_keys)}",
                "  Event Decisions:",
            )
        )
        if cleanup_summary.application_origin == "adopted_default":
            lines.extend((
                f"  Application Origin: {_single_line(cleanup_summary.application_origin)}",
                f"  Event Component: {_single_line(cleanup_summary.event_component_state)}",
                f"  Key Component: {_single_line(cleanup_summary.key_component_state)}",
                f"  Selection Kind: {_single_line(cleanup_summary.selection_kind)}",
                f"  Selection Reason: {_single_line(cleanup_summary.selection_reason)}",
            ))
        if not cleanup_summary.event_reasons:
            lines.append(f"    {_NOT_AVAILABLE}")
        for event_id, action, reasons in cleanup_summary.event_reasons:
            lines.append(
                f"    {_single_line(event_id)} / {_single_line(action)} / "
                + (", ".join(_single_line(reason) for reason in reasons) if reasons else _NOT_AVAILABLE)
            )
        if cleanup_summary.removed_keys:
            lines.append(
                "  Removed Keys: "
                + ", ".join(f"{morph}@{frame}" for frame, morph in cleanup_summary.removed_keys)
            )
    return lines


def format_diagnostic_report(
    snapshot: OutputDiagnosticsSnapshot,
    *,
    generated_at: datetime,
) -> str:
    """Format one immutable diagnostics snapshot as deterministic plain text."""
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("generated_at must be timezone-aware")

    input_summary = snapshot.input_summary
    analysis_summary = snapshot.analysis_summary
    generation_summary = snapshot.generation_summary
    whisper_summary = snapshot.whisper_summary
    adjustment_summary = snapshot.adjustment_summary
    saveability = snapshot.saveability
    morph_name_set = get_builtin_morph_name_set(
        generation_summary.resolved_morph_name_set_id
    )
    profile_lines = [
        f"Active Model Profile ID: {_adjustment_value(generation_summary.active_model_profile_id)}",
        "Active Model Profile Display Name: "
        f"{_single_line(generation_summary.active_model_profile_display_name)}",
        "Active Profile Baseline Preset ID: "
        f"{_adjustment_value(generation_summary.active_profile_baseline_preset_id)}",
        "Baseline Preset Display Name: "
        f"{_single_line(generation_summary.baseline_preset_display_name)}",
        "Model Profile Resolution Status: "
        f"{_single_line(generation_summary.model_profile_resolution_status)}",
        "Model Profile Resolution Reason: "
        f"{_single_line(generation_summary.model_profile_resolution_reason_code)}",
        "Resolved Morph Name Set ID: "
        f"{_single_line(generation_summary.resolved_morph_name_set_id)}",
        "Resolved Morph Name Set Display Name: "
        f"{_single_line(generation_summary.resolved_morph_name_set_display_name)}",
        "Resolved Morph Names (Ordered): "
        f"{_display_ordered_morph_names(morph_name_set.output_names)}",
    ]

    lines = [
        "MMD AutoLipTool Diagnostic Report",
        f"Generated At: {generated_at.isoformat(timespec='seconds')}",
        "",
        "[Input]",
        f"Input Mode: {_single_line(input_summary.input_mode)}",
        f"Text Path: {_single_line(input_summary.normalized_text_path)}",
        f"Source Audio Path: {_single_line(input_summary.normalized_source_audio_path)}",
        f"Effective WAV Path: {_single_line(input_summary.normalized_effective_wav_path)}",
        f"Text Content Present: {_display_bool(input_summary.text_content_present)}",
        f"Analysis Text Present: {_display_bool(input_summary.analysis_text_present)}",
        "",
        "[Analysis]",
        f"Analysis Result Valid: {_display_bool(analysis_summary.analysis_result_valid)}",
        f"Analysis Pending Rebuild: {_display_bool(analysis_summary.analysis_pending_rebuild)}",
        f"Timing Source: {_single_line(analysis_summary.timing_source)}",
        f"Anchor Count: {analysis_summary.anchor_count}",
        f"Event Count: {analysis_summary.event_count}",
        f"Max Frame: {_single_line(analysis_summary.max_frame)}",
        f"Timing Warning Present: {_display_bool(analysis_summary.timing_warning_present)}",
        f"Observation Fallback Count: {analysis_summary.observation_fallback_count}",
        "",
        "[Whisper]",
        f"Selected Model Key: {_single_line(whisper_summary.selected_model_key)}",
        f"Selected Model Display Name: {_single_line(whisper_summary.selected_model_display_name)}",
        f"Selected Manifest Identity: {_single_line(whisper_summary.selected_manifest_identity)}",
        f"Active Model Key: {_single_line(whisper_summary.active_model_key)}",
        f"Active Model Display Name: {_single_line(whisper_summary.active_model_display_name)}",
        f"Active Manifest Identity: {_single_line(whisper_summary.active_manifest_identity)}",
        f"Loaded Model Key: {_single_line(whisper_summary.loaded_model_key)}",
        "Loaded Model Display Name: "
        f"{_single_line(whisper_summary.loaded_model_display_name)}",
        f"Loaded Manifest Identity: {_single_line(whisper_summary.loaded_manifest_identity)}",
        f"Analysis Model Key: {_single_line(whisper_summary.analysis_model_key)}",
        "Analysis Model Display Name: "
        f"{_single_line(whisper_summary.analysis_model_display_name)}",
        f"Analysis Manifest Identity: {_single_line(whisper_summary.analysis_manifest_identity)}",
        f"Analysis Identity Status: {_single_line(whisper_summary.analysis_identity_status)}",
        f"Runtime Identity Status: {_single_line(whisper_summary.runtime_identity_status)}",
        f"Manifest Schema Version: {_single_line(whisper_summary.manifest_schema_version)}",
        f"Package: {_single_line(whisper_summary.package_name)}=={_single_line(whisper_summary.package_version)}",
        f"Package Gate Status: {_single_line(whisper_summary.package_gate_status)}",
        f"Availability Scan Status: {_single_line(whisper_summary.availability_scan_status)}",
        f"Availability Scan Failure Code: {_single_line(whisper_summary.availability_scan_failure_code)}",
        f"Management Operation: {_single_line(whisper_summary.management_operation)}",
        f"Management Phase: {_single_line(whisper_summary.management_phase)}",
        f"Management Model Key: {_single_line(whisper_summary.management_model_key)}",
        f"Management Failure Code: {_single_line(whisper_summary.management_failure_code)}",
        f"Management Cleanup Status: {_single_line(whisper_summary.management_cleanup_status)}",
        f"Active Config Status: {_single_line(whisper_summary.active_config_status)}",
        f"Active Config Reason: {_single_line(whisper_summary.active_config_reason)}",
        f"Analysis Rebuild Reason: {_single_line(whisper_summary.analysis_rebuild_reason)}",
        f"Failure Class: {_single_line(whisper_summary.failure_class)}",
        f"Failure Detail Code: {_single_line(whisper_summary.failure_detail_code)}",
        f"Safe Failure Notice: {_single_line(whisper_summary.safe_failure_notice)}",
        f"Recoverability: {_single_line(whisper_summary.recoverability)}",
        f"Storage Location: {_single_line(whisper_summary.storage_location_display)}",
        f"Projection Generation: {snapshot.projection_generation}",
        "",
        "[Generation]",
        f"VMD Model Name: {_single_line(generation_summary.vmd_model_name)}",
        f"Closing Hold Frames: {generation_summary.closing_hold_frames}",
        f"Closing Softness Frames: {generation_summary.closing_softness_frames}",
        f"Fingerprint Schema Version: {_single_line(generation_summary.fingerprint_schema_version)}",
        f"Active Long Vowel Mode: {_single_line(generation_summary.active_long_vowel_mode)}",
        f"Active Preset ID: {_adjustment_value(generation_summary.active_preset_id)}",
        "Active Preset Display Name: "
        f"{_single_line(generation_summary.active_preset_display_name or 'Custom')}",
        "Effective Long Vowel Hold Run Count: "
        f"{_adjustment_value(generation_summary.effective_long_vowel_hold_run_count)}",
        "Effective Long Vowel Decay Run Count: "
        f"{_adjustment_value(generation_summary.effective_long_vowel_decay_run_count)}",
        *profile_lines,
        "",
        "[Adjustment]",
        f"Base Plan Identity: {_adjustment_value(adjustment_summary.base_plan_identity_digest)}",
        f"Adjustment Present: {_display_yes_no(adjustment_summary.adjustment_present)}",
        f"Adjusted Event Count: {adjustment_summary.adjusted_event_count}",
        f"Effective Shape Count: {_adjustment_value(adjustment_summary.effective_shape_count)}",
        f"Effective Morph Frame Count: {_adjustment_value(adjustment_summary.effective_morph_frame_count)}",
        f"Long Vowel Mode Override Count: {adjustment_summary.long_vowel_mode_override_count}",
        "",
        "[Saveability]",
        f"VMD Save Allowed: {_display_bool(saveability.vmd_save_allowed)}",
        f"Blocking Codes: {_display_codes(saveability.blocking_codes)}",
        f"Warning Codes: {_display_codes(saveability.warning_codes)}",
        f"Save State Fingerprint: {_single_line(snapshot.save_state_fingerprint)}",
    ]

    has_shared_final_output_context = (
        snapshot.shared_final_output_identity is not None
        or any(
            item.code == "effective_writer_input_unavailable"
            and item.detail.startswith("MS31 final output ")
            for item in snapshot.items
        )
    )
    if has_shared_final_output_context:
        lines.extend(
            [
                "",
                "[Shared Final Output]",
                *_shared_final_output_lines(snapshot),
            ]
        )

    lines.extend(["", "[Diagnostics]"])

    if not snapshot.items:
        lines.append(_NOT_AVAILABLE)
    else:
        for index, item in enumerate(snapshot.items, start=1):
            if index > 1:
                lines.append("")
            lines.extend(
                [
                    f"Diagnostic {index}:",
                    f"  Severity: {item.severity.value}",
                    f"  Code: {_single_line(item.code)}",
                    f"  Phase: {_single_line(item.phase)}",
                    f"  Summary: {_single_line(item.summary)}",
                    "  Detail:",
                    *_detail_lines(item.detail),
                    f"  Identity Context: {_identity_context_json(item.identity_context)}",
                ]
            )

    return "\n".join(lines) + "\n"


def write_diagnostic_report(
    snapshot: OutputDiagnosticsSnapshot,
    output_path: str | Path,
    *,
    generated_at: datetime,
) -> Path:
    """Write and verify a report before atomically replacing the target."""
    target_path = Path(output_path)
    temp_path: Path | None = None

    try:
        if not target_path.parent.is_dir():
            raise OSError(f"output directory does not exist: {target_path.parent}")

        expected_bytes = format_diagnostic_report(
            snapshot,
            generated_at=generated_at,
        ).encode("utf-8")

        with NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=str(target_path.parent),
            prefix=f".{target_path.name}.",
            suffix=".tmp",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(expected_bytes)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        actual_bytes = temp_path.read_bytes()
        if actual_bytes != expected_bytes:
            raise OSError("temporary report verification failed: byte mismatch")
        actual_bytes.decode("utf-8", errors="strict")
        if actual_bytes.startswith(_UTF8_BOM):
            raise OSError("temporary report verification failed: UTF-8 BOM detected")

        os.replace(temp_path, target_path)
        temp_path = None
        return target_path
    except Exception as error:
        raise DiagnosticReportError(_SAFE_REPORT_WRITE_ERROR) from error
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
