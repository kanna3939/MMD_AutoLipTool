from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import errno
import hashlib
import os
import shutil
import stat
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Literal, Sequence

from src.core.audio_probe import AudioProbeResult
from src.core.effective_shape_plan import EffectiveShapePlan
from src.core.final_output_projection import SharedFinalOutputContext
from src.core.mmd_wav_export import MMD_WAV_SPEC, MmdWavSpec
from src.core.morph_name_sets import (
    JAPANESE_OUTPUT_NAMES,
    LATIN_OUTPUT_NAMES,
    get_builtin_morph_name_set,
    validate_output_morph_names,
)
from src.core.output_diagnostics import (
    DiagnosticSeverity,
    OutputDiagnosticsSnapshot,
    VmdWriterParameters,
)
from src.vmd_writer.effective_shape_adapter import (
    build_morph_frames_from_effective_shape_plan,
)


DeliveryArtifactKind = Literal["vmd", "mmd_wav", "report"]
DELIVERY_ARTIFACT_ORDER: tuple[DeliveryArtifactKind, ...] = (
    "vmd",
    "mmd_wav",
    "report",
)
_BUILTIN_OUTPUT_NAME_SETS = (JAPANESE_OUTPUT_NAMES, LATIN_OUTPUT_NAMES)
_GATE_STATUSES = {"ready", "warning_confirmation_required", "blocked"}


class DeliveryContractError(ValueError):
    """Safe, structured contract failure for the delivery boundary."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _require_non_empty_string(value: object, field_name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _coerce_path(value: object, field_name: str) -> Path:
    if value is None:
        raise DeliveryContractError(
            "delivery_source_audio_unavailable",
            f"{field_name} is unavailable.",
        )
    try:
        raw_value = os.fspath(value)
    except TypeError as error:
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            f"{field_name} is invalid.",
        ) from error
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            f"{field_name} is invalid.",
        )
    return Path(raw_value)


def _normalize_codes(values: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value:
            raise ValueError("diagnostic codes must be non-empty strings")
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _is_timezone_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _normalize_builtin_output_morph_names(
    output_morph_names: Sequence[str],
) -> tuple[str, ...]:
    normalized = validate_output_morph_names(output_morph_names)
    if normalized not in _BUILTIN_OUTPUT_NAME_SETS:
        raise ValueError("output_morph_names must be a built-in morph name set")
    return normalized


@dataclass(frozen=True)
class DeliveryArtifactNames:
    audio_stem: str
    default_directory_name: str
    vmd_file_name: str
    mmd_wav_file_name: str
    report_file_name: str

    def __post_init__(self) -> None:
        audio_stem = _require_non_empty_string(self.audio_stem, "audio_stem")
        expected = (
            f"{audio_stem}_MMD",
            f"{audio_stem}_lip.vmd",
            f"{audio_stem}_mmd.wav",
            f"{audio_stem}_report.txt",
        )
        actual = (
            self.default_directory_name,
            self.vmd_file_name,
            self.mmd_wav_file_name,
            self.report_file_name,
        )
        for field_name, value in zip(
            (
                "default_directory_name",
                "vmd_file_name",
                "mmd_wav_file_name",
                "report_file_name",
            ),
            actual,
        ):
            _require_non_empty_string(value, field_name)
        if actual != expected:
            raise ValueError("delivery artifact names do not match audio_stem")


def build_delivery_artifact_names(source_path: str | Path) -> DeliveryArtifactNames:
    """Build the fixed delivery names from the case-preserving source stem."""
    path = _coerce_path(source_path, "source_path")
    audio_stem = path.stem
    if not audio_stem:
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            "source audio stem is empty.",
        )
    return DeliveryArtifactNames(
        audio_stem=audio_stem,
        default_directory_name=f"{audio_stem}_MMD",
        vmd_file_name=f"{audio_stem}_lip.vmd",
        mmd_wav_file_name=f"{audio_stem}_mmd.wav",
        report_file_name=f"{audio_stem}_report.txt",
    )


def _optional_stat_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            f"source identity {field_name} is invalid.",
        )
    return value


@dataclass(frozen=True)
class SourceAudioIdentity:
    resolved_path: Path
    size_bytes: int
    mtime_ns: int
    device_id: int | None
    file_id: int | None
    file_attributes: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.resolved_path, Path):
            raise ValueError("resolved_path must be Path")
        for field_name in ("size_bytes", "mtime_ns"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        for field_name in ("device_id", "file_id", "file_attributes"):
            _optional_stat_int(getattr(self, field_name), field_name)


def capture_source_audio_identity(source_path: str | Path) -> SourceAudioIdentity:
    """Capture the resolved regular-file identity used by delivery gating."""
    path = _coerce_path(source_path, "source_path")
    try:
        resolved_path = path.resolve(strict=True)
        file_stat = os.stat(resolved_path)
    except (OSError, RuntimeError, ValueError) as error:
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            "source audio identity could not be captured.",
        ) from error
    if not stat.S_ISREG(file_stat.st_mode):
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            "source audio is not a regular file.",
        )
    mtime_ns = getattr(file_stat, "st_mtime_ns", None)
    if isinstance(mtime_ns, bool) or not isinstance(mtime_ns, int) or mtime_ns < 0:
        raise DeliveryContractError(
            "delivery_source_audio_invalid",
            "source audio modification time is unavailable.",
        )
    return SourceAudioIdentity(
        resolved_path=resolved_path,
        size_bytes=int(file_stat.st_size),
        mtime_ns=mtime_ns,
        device_id=_optional_stat_int(getattr(file_stat, "st_dev", None), "device_id"),
        file_id=_optional_stat_int(getattr(file_stat, "st_ino", None), "file_id"),
        file_attributes=_optional_stat_int(
            getattr(file_stat, "st_file_attributes", None),
            "file_attributes",
        ),
    )


@dataclass(frozen=True)
class DeliveryCurrentState:
    effective_shape_plan: EffectiveShapePlan
    diagnostics_snapshot: OutputDiagnosticsSnapshot
    audio_probe: AudioProbeResult
    source_identity: SourceAudioIdentity
    mmd_wav_spec: MmdWavSpec
    ffmpeg_path: Path
    writer_parameters: VmdWriterParameters
    output_morph_names: tuple[str, ...]
    artifact_names: DeliveryArtifactNames
    start_fingerprint: str
    projection_generation: int
    artifact_order: tuple[DeliveryArtifactKind, ...] = DELIVERY_ARTIFACT_ORDER
    gate_status: Literal["ready", "warning_confirmation_required"] = "ready"
    projection_kind: Literal["legacy_effective", "shared_final_output"] = "legacy_effective"
    shared_final_output_context: SharedFinalOutputContext | None = None
    expected_transition_input_digest: str | None = None
    expected_application_binding_digest: str | None = None
    expected_cleanup_input_digest: str | None = None
    expected_cleanup_application_binding_digest: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.effective_shape_plan, EffectiveShapePlan):
            raise ValueError("effective_shape_plan must be EffectiveShapePlan")
        if self.projection_kind not in {"legacy_effective", "shared_final_output"}:
            raise ValueError("projection_kind is unsupported")
        if self.projection_kind == "legacy_effective":
            if self.shared_final_output_context is not None:
                raise ValueError("legacy projection cannot carry a shared context")
        elif not isinstance(self.shared_final_output_context, SharedFinalOutputContext):
            raise ValueError("shared projection requires a shared final output context")
        if self.projection_kind == "legacy_effective":
            if (
                self.expected_transition_input_digest is not None
                or self.expected_application_binding_digest is not None
                or self.expected_cleanup_input_digest is not None
                or self.expected_cleanup_application_binding_digest is not None
            ):
                raise ValueError("legacy delivery cannot carry shared binding digests")
        elif self.shared_final_output_context.transition_binding is None:
            if (
                self.expected_transition_input_digest is not None
                or self.shared_final_output_context.input_identity.transition_input_digest is not None
            ):
                raise ValueError("legacy shared delivery has an unexpected transition digest")
        elif (
            self.expected_transition_input_digest is None
            or self.shared_final_output_context.input_identity.transition_input_digest
            != self.expected_transition_input_digest
            or self.shared_final_output_context.transition_binding.input_snapshot.input_digest
            != self.expected_transition_input_digest
        ):
            raise ValueError("shared delivery transition identity is stale")
        if self.projection_kind == "shared_final_output" and (
            self.shared_final_output_context.input_identity.application_binding_digest
            != self.expected_application_binding_digest
        ):
            raise ValueError("shared delivery application binding is stale")
        if self.projection_kind == "shared_final_output":
            cleanup_binding = self.shared_final_output_context.cleanup_binding
            if cleanup_binding is None:
                if (
                    self.expected_cleanup_input_digest is not None
                    or self.expected_cleanup_application_binding_digest is not None
                    or self.shared_final_output_context.input_identity.cleanup_input_digest is not None
                    or self.shared_final_output_context.input_identity.cleanup_application_binding_digest is not None
                    or self.diagnostics_snapshot.cleanup_summary is not None
                ):
                    raise ValueError("shared delivery cleanup binding is unexpected")
            elif (
                self.expected_cleanup_input_digest != cleanup_binding.input_digest
                or self.shared_final_output_context.input_identity.cleanup_input_digest
                != cleanup_binding.input_digest
                or self.shared_final_output_context.input_identity.cleanup_application_binding_digest
                != (
                    None
                    if cleanup_binding.default_selection is None
                    else cleanup_binding.default_selection.selection_digest
                )
                or self.expected_cleanup_application_binding_digest
                != self.shared_final_output_context.input_identity.cleanup_application_binding_digest
                or self.diagnostics_snapshot.cleanup_summary != cleanup_binding.summary
            ):
                raise ValueError("shared delivery cleanup binding is stale")
        if not isinstance(self.diagnostics_snapshot, OutputDiagnosticsSnapshot):
            raise ValueError(
                "diagnostics_snapshot must be OutputDiagnosticsSnapshot"
            )
        if not isinstance(self.audio_probe, AudioProbeResult):
            raise ValueError("audio_probe must be AudioProbeResult")
        if not isinstance(self.source_identity, SourceAudioIdentity):
            raise ValueError("source_identity must be SourceAudioIdentity")
        if self.mmd_wav_spec != MMD_WAV_SPEC:
            raise ValueError("mmd_wav_spec must be MMD_WAV_SPEC")
        if not isinstance(self.ffmpeg_path, Path):
            raise ValueError("ffmpeg_path must be Path")
        if not isinstance(self.writer_parameters, VmdWriterParameters):
            raise ValueError("writer_parameters must be VmdWriterParameters")
        normalized_names = _normalize_builtin_output_morph_names(
            self.output_morph_names
        )
        object.__setattr__(self, "output_morph_names", normalized_names)
        resolved_morph_name_set = get_builtin_morph_name_set(
            self.diagnostics_snapshot.generation_summary.resolved_morph_name_set_id
        )
        if normalized_names != resolved_morph_name_set.output_names:
            raise ValueError(
                "output_morph_names do not match diagnostics snapshot morph name set"
            )
        if not isinstance(self.artifact_names, DeliveryArtifactNames):
            raise ValueError("artifact_names must be DeliveryArtifactNames")
        if type(self.start_fingerprint) is not str or not self.start_fingerprint:
            raise ValueError("start_fingerprint must be a non-empty string")
        if self.diagnostics_snapshot.save_state_fingerprint != self.start_fingerprint:
            raise ValueError("start_fingerprint must match diagnostics snapshot")
        if (
            isinstance(self.projection_generation, bool)
            or not isinstance(self.projection_generation, int)
            or self.projection_generation < 0
        ):
            raise ValueError("projection_generation must be a non-negative integer")
        if self.diagnostics_snapshot.projection_generation != self.projection_generation:
            raise ValueError("projection_generation must match diagnostics snapshot")
        if self.artifact_order != DELIVERY_ARTIFACT_ORDER:
            raise ValueError("artifact_order must be VMD, MMD WAV, report")
        if self.gate_status not in {"ready", "warning_confirmation_required"}:
            raise ValueError("unsupported current state gate status")
        if (
            self.effective_shape_plan.base_plan_identity.digest
            != self.diagnostics_snapshot.adjustment_summary.base_plan_identity_digest
        ):
            raise ValueError("effective plan and snapshot base identity mismatch")
        if self.projection_kind == "shared_final_output":
            shared = self.shared_final_output_context
            assert shared is not None
            if self.diagnostics_snapshot.shared_final_output_identity != shared.identity:
                raise ValueError("shared diagnostics and output context differ")
            if shared.identity.wire_digest != shared.projection.wire_digest:
                raise ValueError("shared projection digest differs from its identity")
            if shared.transition_binding is not None:
                transition_context = shared
                if shared.cleanup_binding is not None:
                    transition_context = shared.cleanup_binding.upstream_context
                if (
                    transition_context.transition_binding != shared.transition_binding
                    or transition_context.identity.semantic_digest
                    != shared.transition_binding.plan.semantic_digest
                    or transition_context.identity.plan_schema_id
                    != shared.transition_binding.plan.schema_id
                ):
                    raise ValueError("shared upstream transition identity differs from its plan")
            if shared.input_identity.output_mapping != shared.candidate.plan.identity_context.output_mapping:
                raise ValueError("shared projection mapping differs from its closure plan")
            try:
                shared_source_path = (
                    None
                    if shared.input_identity.source_audio_path is None
                    else Path(shared.input_identity.source_audio_path).resolve(strict=False)
                )
            except (OSError, RuntimeError, TypeError, ValueError) as error:
                raise ValueError("shared source audio path is invalid") from error
            if shared_source_path != self.source_identity.resolved_path:
                raise ValueError("shared source audio identity differs from delivery source")
            if self.start_fingerprint != self.diagnostics_snapshot.save_state_fingerprint:
                raise ValueError("shared save fingerprint differs from diagnostics")
        adjustment_summary = self.diagnostics_snapshot.adjustment_summary
        if (
            adjustment_summary.effective_shape_count is not None
            and adjustment_summary.effective_shape_count
            != len(self.effective_shape_plan.shapes)
        ):
            raise ValueError("effective shape count mismatch")
        if self.projection_kind == "legacy_effective":
            expected_morph_frames = build_morph_frames_from_effective_shape_plan(
                self.effective_shape_plan,
                output_morph_names=normalized_names,
            )
            if (
                adjustment_summary.effective_morph_frame_count is not None
                and adjustment_summary.effective_morph_frame_count
                != len(expected_morph_frames)
            ):
                raise ValueError("effective morph frame count mismatch")
        if (
            self.diagnostics_snapshot.generation_summary.vmd_model_name
            != self.writer_parameters.vmd_model_name
        ):
            raise ValueError("writer model name mismatch")
        try:
            probe_path = Path(self.audio_probe.source_path).resolve(strict=False)
        except (TypeError, ValueError, OSError, RuntimeError) as error:
            raise ValueError("audio probe source path is invalid") from error
        if probe_path != self.source_identity.resolved_path:
            raise ValueError("source identity and probe path mismatch")
        if self.audio_probe.file_size_bytes != self.source_identity.size_bytes:
            raise ValueError("source identity and probe size mismatch")


@dataclass(frozen=True)
class DeliveryStartGateResult:
    status: Literal["ready", "warning_confirmation_required", "blocked"]
    blocking_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    fingerprint: str | None
    candidate_state: DeliveryCurrentState | None

    def __post_init__(self) -> None:
        if self.status not in _GATE_STATUSES:
            raise ValueError("unsupported delivery gate status")
        object.__setattr__(self, "blocking_codes", _normalize_codes(self.blocking_codes))
        object.__setattr__(self, "warning_codes", _normalize_codes(self.warning_codes))
        if self.fingerprint is not None and (
            type(self.fingerprint) is not str or not self.fingerprint
        ):
            raise ValueError("fingerprint must be None or a non-empty string")
        if self.status == "blocked":
            if self.candidate_state is not None:
                raise ValueError("blocked gate cannot expose candidate state")
            if self.fingerprint is not None:
                raise ValueError("blocked gate cannot expose a fingerprint")
            if not self.blocking_codes:
                raise ValueError("blocked gate requires blocking codes")
        else:
            if self.candidate_state is None:
                raise ValueError("non-blocked gate requires candidate state")
            if self.fingerprint != self.candidate_state.start_fingerprint:
                raise ValueError("gate fingerprint must match candidate state")
            expected_candidate_status = (
                "warning_confirmation_required"
                if self.status == "warning_confirmation_required"
                else "ready"
            )
            if self.candidate_state.gate_status != expected_candidate_status:
                raise ValueError("gate status must match candidate state")
            if self.status == "warning_confirmation_required" and not self.warning_codes:
                raise ValueError("warning gate requires warning codes")
            if self.blocking_codes:
                raise ValueError("non-blocked gate cannot contain blocking codes")
        if self.status == "ready" and self.warning_codes and self.fingerprint is None:
            raise ValueError("ready gate with warnings requires fingerprint")


@dataclass(frozen=True)
class DeliveryStartContext:
    current_state: DeliveryCurrentState
    parent_directory: Path
    folder_name: str
    report_generated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.current_state, DeliveryCurrentState):
            raise ValueError("current_state must be DeliveryCurrentState")
        if not isinstance(self.parent_directory, Path):
            raise ValueError("parent_directory must be Path")
        _require_non_empty_string(self.folder_name, "folder_name")
        if not isinstance(self.report_generated_at, datetime):
            raise ValueError("report_generated_at must be datetime")
        if not _is_timezone_aware(self.report_generated_at):
            raise ValueError("report_generated_at must be timezone-aware")


def build_delivery_start_context(
    current_state: DeliveryCurrentState,
    parent_directory: str | Path,
    folder_name: str,
    report_generated_at: datetime,
) -> DeliveryStartContext:
    """Bundle a ready current state with B2-approved destination inputs."""
    if not isinstance(current_state, DeliveryCurrentState):
        raise DeliveryContractError(
            "delivery_start_context_invalid",
            "delivery current state is invalid.",
        )
    if current_state.gate_status != "ready":
        raise DeliveryContractError(
            "delivery_start_context_invalid",
            "delivery warning confirmation is required.",
        )
    try:
        parent = _coerce_path(parent_directory, "parent_directory")
    except DeliveryContractError as error:
        raise DeliveryContractError(
            "delivery_start_context_invalid",
            "parent directory is invalid.",
        ) from error
    try:
        return DeliveryStartContext(
            current_state=current_state,
            parent_directory=parent,
            folder_name=folder_name,
            report_generated_at=report_generated_at,
        )
    except (TypeError, ValueError) as error:
        raise DeliveryContractError(
            "delivery_start_context_invalid",
            "delivery start context is invalid.",
        ) from error


@dataclass(frozen=True)
class DeliveryCommitFingerprintResult:
    allowed: bool
    reason_code: str | None
    current_fingerprint: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be bool")
        if self.reason_code is not None and (
            type(self.reason_code) is not str or not self.reason_code
        ):
            raise ValueError("reason_code must be None or a non-empty string")
        if self.current_fingerprint is not None and (
            type(self.current_fingerprint) is not str or not self.current_fingerprint
        ):
            raise ValueError(
                "current_fingerprint must be None or a non-empty string"
            )
        if self.allowed and self.reason_code is not None:
            raise ValueError("allowed result cannot contain a reason code")
        if not self.allowed and self.reason_code is None:
            raise ValueError("blocked result requires a reason code")


def _snapshot_has_error(snapshot: OutputDiagnosticsSnapshot) -> bool:
    return any(item.severity is DiagnosticSeverity.ERROR for item in snapshot.items)


def _blocked_result(
    blocking_codes: Sequence[str],
    warning_codes: Sequence[str] = (),
) -> DeliveryStartGateResult:
    return DeliveryStartGateResult(
        status="blocked",
        blocking_codes=_normalize_codes(blocking_codes),
        warning_codes=_normalize_codes(warning_codes),
        fingerprint=None,
        candidate_state=None,
    )


def evaluate_delivery_start_gate(
    *,
    effective_shape_plan: EffectiveShapePlan | None,
    diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
    audio_probe: AudioProbeResult | None,
    source_audio_path: str | Path | None,
    mmd_wav_spec: MmdWavSpec | None,
    ffmpeg_path: str | Path | None,
    writer_parameters: VmdWriterParameters | None,
    output_morph_names: Sequence[str] | None,
    effective_writer_input_state: str | None = None,
    confirmed_warning_save_state_fingerprint: str | None = None,
    application_busy: bool = False,
    analysis_in_progress: bool = False,
    projection_kind: Literal["legacy_effective", "shared_final_output"] = "legacy_effective",
    shared_final_output_context: SharedFinalOutputContext | None = None,
    shared_lifecycle_signature: tuple[object, ...] | None = None,
    expected_transition_input_digest: str | None = None,
    expected_application_binding_digest: str | None = None,
    expected_cleanup_input_digest: str | None = None,
    expected_cleanup_application_binding_digest: str | None = None,
) -> DeliveryStartGateResult:
    """Evaluate the pure, fail-closed B1 start contract."""
    blocking_codes: list[str] = []
    snapshot_is_valid = isinstance(diagnostics_snapshot, OutputDiagnosticsSnapshot)

    if projection_kind not in {"legacy_effective", "shared_final_output"}:
        blocking_codes.append("delivery_projection_kind_invalid")
    elif projection_kind == "legacy_effective":
        if shared_final_output_context is not None:
            blocking_codes.append("delivery_projection_context_mismatch")
        if (
            expected_transition_input_digest is not None
            or expected_application_binding_digest is not None
            or expected_cleanup_input_digest is not None
            or expected_cleanup_application_binding_digest is not None
        ):
            blocking_codes.append("delivery_projection_context_mismatch")
    elif (
        not isinstance(shared_final_output_context, SharedFinalOutputContext)
        or not snapshot_is_valid
        or diagnostics_snapshot.shared_final_output_identity
        != shared_final_output_context.identity
        or shared_final_output_context.identity.wire_digest
        != shared_final_output_context.projection.wire_digest
        or shared_final_output_context.lifecycle_signature
        != shared_lifecycle_signature
        or shared_final_output_context.input_identity.application_binding_digest
        != expected_application_binding_digest
        or (
            shared_final_output_context.cleanup_binding is None
            and (
                expected_cleanup_input_digest is not None
                or expected_cleanup_application_binding_digest is not None
                or shared_final_output_context.input_identity.cleanup_input_digest is not None
                or shared_final_output_context.input_identity.cleanup_application_binding_digest is not None
                or diagnostics_snapshot.cleanup_summary is not None
            )
        )
        or (
            shared_final_output_context.cleanup_binding is not None
            and (
                expected_cleanup_input_digest is None
                or expected_cleanup_input_digest
                != shared_final_output_context.cleanup_binding.input_digest
                or expected_cleanup_input_digest
                != shared_final_output_context.input_identity.cleanup_input_digest
                or shared_final_output_context.input_identity.cleanup_application_binding_digest
                != (
                    None
                    if shared_final_output_context.cleanup_binding.default_selection is None
                    else shared_final_output_context.cleanup_binding.default_selection.selection_digest
                )
                or expected_cleanup_application_binding_digest
                != shared_final_output_context.input_identity.cleanup_application_binding_digest
                or diagnostics_snapshot.cleanup_summary
                != shared_final_output_context.cleanup_binding.summary
            )
        )
        or (
            shared_final_output_context.transition_binding is None
            and (
                expected_transition_input_digest is not None
                or shared_final_output_context.input_identity.transition_input_digest is not None
            )
        )
        or (
            shared_final_output_context.transition_binding is not None
            and (
                expected_transition_input_digest is None
                or expected_transition_input_digest
                != shared_final_output_context.transition_binding.input_snapshot.input_digest
                or expected_transition_input_digest
                != shared_final_output_context.input_identity.transition_input_digest
            )
        )
    ):
        blocking_codes.append("delivery_shared_output_unavailable")

    if application_busy or (
        snapshot_is_valid
        and diagnostics_snapshot.whisper_summary.application_busy
    ):
        blocking_codes.append("delivery_busy")

    if (
        not snapshot_is_valid
        or analysis_in_progress
        or not diagnostics_snapshot.analysis_summary.analysis_result_valid
        or diagnostics_snapshot.analysis_summary.analysis_pending_rebuild
        or diagnostics_snapshot.analysis_summary.event_count <= 0
    ):
        blocking_codes.append("delivery_analysis_unavailable")

    if (
        not isinstance(effective_shape_plan, EffectiveShapePlan)
        or not effective_shape_plan.shapes
        or effective_writer_input_state != "ready"
    ):
        blocking_codes.append("delivery_effective_output_unavailable")

    source_identity: SourceAudioIdentity | None = None
    artifact_names: DeliveryArtifactNames | None = None
    if source_audio_path is None or audio_probe is None:
        blocking_codes.append("delivery_source_audio_unavailable")
    elif not isinstance(audio_probe, AudioProbeResult):
        blocking_codes.append("delivery_source_audio_invalid")
    else:
        try:
            source_identity = capture_source_audio_identity(source_audio_path)
            probe_path = Path(audio_probe.source_path).resolve(strict=True)
            if probe_path != source_identity.resolved_path:
                raise DeliveryContractError(
                    "delivery_source_audio_invalid",
                    "source audio and probe refer to different files.",
                )
            if audio_probe.file_size_bytes != source_identity.size_bytes:
                raise DeliveryContractError(
                    "delivery_source_audio_invalid",
                    "source audio and probe sizes differ.",
                )
            artifact_names = build_delivery_artifact_names(source_audio_path)
        except (DeliveryContractError, OSError, RuntimeError, TypeError, ValueError):
            source_identity = None
            artifact_names = None
            blocking_codes.append("delivery_source_audio_invalid")

    if mmd_wav_spec != MMD_WAV_SPEC:
        blocking_codes.append("delivery_mmd_wav_spec_invalid")

    resolved_ffmpeg_path: Path | None = None
    if ffmpeg_path is None:
        blocking_codes.append("delivery_ffmpeg_unavailable")
    else:
        try:
            resolved_ffmpeg_path = _coerce_path(ffmpeg_path, "ffmpeg_path")
            if not resolved_ffmpeg_path.is_file():
                resolved_ffmpeg_path = None
                blocking_codes.append("delivery_ffmpeg_unavailable")
        except (DeliveryContractError, OSError, RuntimeError, TypeError, ValueError):
            resolved_ffmpeg_path = None
            blocking_codes.append("delivery_ffmpeg_unavailable")

    if not isinstance(writer_parameters, VmdWriterParameters):
        blocking_codes.append("delivery_writer_parameters_unavailable")

    normalized_morph_names: tuple[str, ...] | None = None
    if output_morph_names is None:
        blocking_codes.append("delivery_morph_names_invalid")
    else:
        try:
            normalized_morph_names = _normalize_builtin_output_morph_names(
                output_morph_names
            )
        except (TypeError, ValueError):
            blocking_codes.append("delivery_morph_names_invalid")

    warning_codes: tuple[str, ...] = ()
    if snapshot_is_valid:
        warning_codes = _normalize_codes(
            diagnostics_snapshot.saveability.warning_codes
        )
        if (
            not diagnostics_snapshot.saveability.vmd_save_allowed
            or diagnostics_snapshot.saveability.blocking_codes
            or _snapshot_has_error(diagnostics_snapshot)
        ):
            blocking_codes.append("delivery_diagnostics_blocked")
        if (
            type(diagnostics_snapshot.save_state_fingerprint) is not str
            or not diagnostics_snapshot.save_state_fingerprint
        ):
            blocking_codes.append("delivery_fingerprint_unavailable")
    else:
        blocking_codes.append("delivery_diagnostics_blocked")
        blocking_codes.append("delivery_fingerprint_unavailable")

    blocking_codes = list(_normalize_codes(blocking_codes))
    if blocking_codes:
        return _blocked_result(blocking_codes, warning_codes)

    assert effective_shape_plan is not None
    assert diagnostics_snapshot is not None
    assert source_identity is not None
    assert artifact_names is not None
    assert resolved_ffmpeg_path is not None
    assert writer_parameters is not None
    assert normalized_morph_names is not None
    fingerprint = diagnostics_snapshot.save_state_fingerprint
    warning_confirmation_required = bool(
        warning_codes
        and confirmed_warning_save_state_fingerprint != fingerprint
    )
    try:
        candidate_state = DeliveryCurrentState(
            effective_shape_plan=effective_shape_plan,
            diagnostics_snapshot=diagnostics_snapshot,
            audio_probe=audio_probe,
            source_identity=source_identity,
            mmd_wav_spec=MMD_WAV_SPEC,
            ffmpeg_path=resolved_ffmpeg_path,
            writer_parameters=writer_parameters,
            output_morph_names=normalized_morph_names,
            artifact_names=artifact_names,
            start_fingerprint=diagnostics_snapshot.save_state_fingerprint,
            projection_generation=diagnostics_snapshot.projection_generation,
            gate_status=(
                "warning_confirmation_required"
                if warning_confirmation_required
                else "ready"
            ),
            projection_kind=projection_kind,
            shared_final_output_context=shared_final_output_context,
            expected_transition_input_digest=expected_transition_input_digest,
            expected_application_binding_digest=expected_application_binding_digest,
            expected_cleanup_input_digest=expected_cleanup_input_digest,
            expected_cleanup_application_binding_digest=expected_cleanup_application_binding_digest,
        )
    except (TypeError, ValueError, DeliveryContractError):
        return _blocked_result(
            (*blocking_codes, "delivery_current_state_invalid"),
            warning_codes,
        )

    fingerprint = candidate_state.start_fingerprint
    if warning_confirmation_required:
        return DeliveryStartGateResult(
            status="warning_confirmation_required",
            blocking_codes=(),
            warning_codes=warning_codes,
            fingerprint=fingerprint,
            candidate_state=candidate_state,
        )
    return DeliveryStartGateResult(
        status="ready",
        blocking_codes=(),
        warning_codes=warning_codes,
        fingerprint=fingerprint,
        candidate_state=candidate_state,
    )


def evaluate_delivery_commit_fingerprint(
    start_context: DeliveryStartContext,
    current_snapshot: OutputDiagnosticsSnapshot | None,
) -> DeliveryCommitFingerprintResult:
    """Compare semantic save-state identity without using projection generation."""
    if not isinstance(start_context, DeliveryStartContext):
        return DeliveryCommitFingerprintResult(
            allowed=False,
            reason_code="delivery_commit_context_unavailable",
            current_fingerprint=None,
        )
    if not isinstance(current_snapshot, OutputDiagnosticsSnapshot):
        return DeliveryCommitFingerprintResult(
            allowed=False,
            reason_code="delivery_commit_snapshot_unavailable",
            current_fingerprint=None,
        )
    current_fingerprint = current_snapshot.save_state_fingerprint
    if (
        not current_snapshot.saveability.vmd_save_allowed
        or current_snapshot.saveability.blocking_codes
        or _snapshot_has_error(current_snapshot)
    ):
        return DeliveryCommitFingerprintResult(
            allowed=False,
            reason_code="delivery_commit_state_blocked",
            current_fingerprint=current_fingerprint,
        )
    if type(current_fingerprint) is not str or not current_fingerprint:
        return DeliveryCommitFingerprintResult(
            allowed=False,
            reason_code="delivery_fingerprint_unavailable",
            current_fingerprint=None,
        )
    if current_fingerprint != start_context.current_state.start_fingerprint:
        return DeliveryCommitFingerprintResult(
            allowed=False,
            reason_code="delivery_state_stale",
            current_fingerprint=current_fingerprint,
        )
    return DeliveryCommitFingerprintResult(
        allowed=True,
        reason_code=None,
        current_fingerprint=current_fingerprint,
    )


DELIVERY_COMPONENT_UTF16_BUDGET = 255
DELIVERY_ABSOLUTE_PATH_UTF16_BUDGET = 240
STAGING_COMPONENT_UTF16_BUDGET = 64
_STAGING_PREFIX = ".MMD_AutoLipTool.delivery-"
_STAGING_SUFFIX = ".staging"
_WINDOWS_INVALID_COMPONENT_CHARS = frozenset('<>:"/\\|?*')
_WINDOWS_RESERVED_DEVICE_NAMES = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
        "com¹",
        "com²",
        "com³",
        "lpt¹",
        "lpt²",
        "lpt³",
        "conin$",
        "conout$",
        "clock$",
    }
)
_DELIVERY_AUTHORIZATION_DECISIONS = frozenset(
    {"authorized", "stale", "cancelled", "invalid_job", "closing"}
)
_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _utf16_code_units(value: str) -> int:
    return len(value.encode("utf-16-le", errors="strict")) // 2


def _validate_delivery_component(value: object, field_name: str) -> str:
    if type(value) is not str or not value:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} must be a non-empty path component.",
        )
    try:
        code_units = _utf16_code_units(value)
    except UnicodeEncodeError as error:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} contains an invalid Unicode surrogate.",
        ) from error
    if code_units > DELIVERY_COMPONENT_UTF16_BUDGET:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} exceeds the Windows component length limit.",
        )
    if value in {".", ".."}:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} cannot be a dot path component.",
        )
    if value[-1] in {" ", "."}:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} cannot end with a space or dot.",
        )
    if any(char in _WINDOWS_INVALID_COMPONENT_CHARS for char in value) or any(
        ord(char) < 0x20 for char in value
    ):
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} contains a Windows-invalid character.",
        )
    base_name = value.split(".", 1)[0].rstrip(" .").casefold()
    if base_name in _WINDOWS_RESERVED_DEVICE_NAMES:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} is a reserved Windows device name.",
        )
    return value


def _validate_delivery_absolute_path(path: Path, field_name: str) -> Path:
    if not isinstance(path, Path) or not path.is_absolute():
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} must be absolute.",
        )
    try:
        code_units = _utf16_code_units(os.fspath(path))
    except UnicodeEncodeError as error:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} contains invalid Unicode.",
        ) from error
    if code_units > DELIVERY_ABSOLUTE_PATH_UTF16_BUDGET:
        raise DeliveryContractError(
            "output_path_invalid",
            f"{field_name} exceeds the delivery path length limit.",
        )
    return path


def _is_reparse_or_link(file_stat: os.stat_result) -> bool:
    if stat.S_ISLNK(file_stat.st_mode):
        return True
    attributes = getattr(file_stat, "st_file_attributes", 0)
    return bool(attributes & _REPARSE_POINT_ATTRIBUTE)


_DELIVERY_OS_REMAP_CODES = frozenset(
    {
        "vmd_write_failed",
        "mmd_wav_write_failed",
        "report_write_failed",
        "output_path_inspection_failed",
        "output_staging_create_failed",
        "output_staging_invalid",
        "delivery_commit_failed",
    }
)


def _iter_delivery_exception_chain(error: BaseException):
    current: BaseException | None = error
    seen: set[int] = set()
    while isinstance(current, BaseException) and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _delivery_os_error_code(error: BaseException, default_code: str) -> str:
    chain = tuple(_iter_delivery_exception_chain(error))
    for cause in chain:
        winerror = getattr(cause, "winerror", None)
        cause_errno = getattr(cause, "errno", None)
        if winerror in {32, 33} or cause_errno == errno.EBUSY:
            return "output_file_locked"
    for cause in chain:
        winerror = getattr(cause, "winerror", None)
        cause_errno = getattr(cause, "errno", None)
        if (
            isinstance(cause, PermissionError)
            or winerror == 5
            or cause_errno in {errno.EACCES, errno.EPERM}
        ):
            return "output_permission_denied"
    for cause in chain:
        winerror = getattr(cause, "winerror", None)
        cause_errno = getattr(cause, "errno", None)
        if winerror in {123, 206, 267} or cause_errno in {
            errno.ENAMETOOLONG,
            errno.ENOTDIR,
        }:
            return "output_path_invalid"
    return default_code


def _capture_delivery_staging_identity(
    destination: ValidatedDeliveryDestination,
    staging: DeliveryStagingPaths,
) -> _DeliveryStagingIdentity:
    root_directory = staging.root_directory
    try:
        root_lstat = os.lstat(root_directory)
        parent_stat = os.stat(destination.parent_directory)
        root_stat = os.stat(root_directory)
    except (OSError, TypeError, ValueError) as error:
        raise DeliveryContractError(
            _delivery_os_error_code(error, "output_staging_invalid"),
            "The staging directory could not be inspected.",
        ) from error

    is_reparse = _is_reparse_or_link(root_lstat)
    if not stat.S_ISDIR(root_lstat.st_mode) or is_reparse:
        raise DeliveryContractError(
            "output_staging_invalid",
            "The staging path is not a normal directory.",
        )
    if root_stat.st_dev != parent_stat.st_dev:
        raise DeliveryContractError(
            "output_staging_invalid",
            "The staging directory is not on the output parent volume.",
        )
    return _DeliveryStagingIdentity(
        path=root_directory,
        device_id=getattr(root_lstat, "st_dev", None),
        file_id=getattr(root_lstat, "st_ino", None),
        file_attributes=getattr(root_lstat, "st_file_attributes", None),
        mode_type=stat.S_IFMT(root_lstat.st_mode),
        is_reparse=is_reparse,
    )


def _assert_delivery_staging_identity(
    destination: ValidatedDeliveryDestination,
    staging: DeliveryStagingPaths,
    expected: _DeliveryStagingIdentity,
) -> None:
    actual = _capture_delivery_staging_identity(destination, staging)
    if actual != expected:
        raise DeliveryContractError(
            "output_staging_invalid",
            "The staging directory identity changed during delivery.",
        )


def _inspect_delivery_absence(path: Path) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    except (OSError, ValueError, TypeError) as error:
        default_code = (
            "output_path_invalid"
            if isinstance(error, (ValueError, TypeError))
            else "output_path_inspection_failed"
        )
        raise DeliveryContractError(
            _delivery_os_error_code(error, default_code),
            "The output destination could not be inspected.",
        ) from error
    raise DeliveryContractError(
        "output_destination_collision",
        "The output destination already exists.",
    )


def _validate_delivery_parent(parent_path: Path) -> Path:
    try:
        raw_parent = os.fspath(parent_path)
    except TypeError as error:
        raise DeliveryContractError(
            "output_parent_invalid",
            "The output parent directory is invalid.",
        ) from error
    if type(raw_parent) is not str or not raw_parent.strip():
        raise DeliveryContractError(
            "output_parent_invalid",
            "The output parent directory is invalid.",
        )
    namespace_path = raw_parent.replace("/", "\\")
    if namespace_path.startswith(("\\\\?\\", "\\\\.\\")):
        raise DeliveryContractError(
            "output_parent_invalid",
            "Device and extended namespace paths are not supported.",
        )
    if not parent_path.is_absolute():
        raise DeliveryContractError(
            "output_parent_invalid",
            "The output parent directory must be absolute.",
        )
    try:
        resolved_parent = parent_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise DeliveryContractError(
            "output_parent_invalid",
            "The output parent directory does not exist or cannot be resolved.",
        ) from error
    if not resolved_parent.is_dir():
        raise DeliveryContractError(
            "output_parent_invalid",
            "The output parent path is not a directory.",
        )
    try:
        _validate_delivery_absolute_path(resolved_parent, "parent_directory")
        for component in resolved_parent.parts:
            if component == resolved_parent.anchor:
                continue
            _validate_delivery_component(component, "parent_directory component")
    except DeliveryContractError as error:
        raise DeliveryContractError(
            "output_parent_invalid",
            "The output parent directory is not Windows-compatible.",
        ) from error
    return resolved_parent


def _validate_delivery_artifact_names(
    artifact_names: DeliveryArtifactNames,
) -> DeliveryArtifactNames:
    if not isinstance(artifact_names, DeliveryArtifactNames):
        raise DeliveryContractError(
            "output_path_invalid",
            "Delivery artifact names are invalid.",
        )
    _validate_delivery_component(artifact_names.audio_stem, "audio_stem")
    for field_name in (
        "default_directory_name",
        "vmd_file_name",
        "mmd_wav_file_name",
        "report_file_name",
    ):
        _validate_delivery_component(
            getattr(artifact_names, field_name),
            field_name,
        )
    expected_names = DeliveryArtifactNames(
        audio_stem=artifact_names.audio_stem,
        default_directory_name=f"{artifact_names.audio_stem}_MMD",
        vmd_file_name=f"{artifact_names.audio_stem}_lip.vmd",
        mmd_wav_file_name=f"{artifact_names.audio_stem}_mmd.wav",
        report_file_name=f"{artifact_names.audio_stem}_report.txt",
    )
    if artifact_names != expected_names:
        raise DeliveryContractError(
            "output_path_invalid",
            "Delivery artifact names do not match the source audio stem.",
        )
    return artifact_names


@dataclass(frozen=True)
class ValidatedDeliveryDestination:
    parent_directory: Path
    folder_name: str
    final_directory: Path
    final_artifact_paths: tuple[tuple[DeliveryArtifactKind, Path], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.parent_directory, Path):
            raise ValueError("parent_directory must be Path")
        if type(self.folder_name) is not str or not self.folder_name:
            raise ValueError("folder_name must be a non-empty string")
        if not isinstance(self.final_directory, Path):
            raise ValueError("final_directory must be Path")
        if self.final_directory.parent != self.parent_directory:
            raise ValueError("final_directory must be a direct child of parent_directory")
        if self.final_artifact_paths != tuple(self.final_artifact_paths):
            raise ValueError("final_artifact_paths must be a tuple")
        if tuple(kind for kind, _ in self.final_artifact_paths) != DELIVERY_ARTIFACT_ORDER:
            raise ValueError("final artifact order is invalid")
        for kind, path in self.final_artifact_paths:
            if kind not in DELIVERY_ARTIFACT_ORDER or not isinstance(path, Path):
                raise ValueError("final artifact path is invalid")
            if path.parent != self.final_directory:
                raise ValueError("final artifact must be inside final_directory")


@dataclass(frozen=True)
class DeliveryStagingPaths:
    root_directory: Path
    artifact_paths: tuple[tuple[DeliveryArtifactKind, Path], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.root_directory, Path):
            raise ValueError("root_directory must be Path")
        if self.artifact_paths != tuple(self.artifact_paths):
            raise ValueError("artifact_paths must be a tuple")
        if tuple(kind for kind, _ in self.artifact_paths) != DELIVERY_ARTIFACT_ORDER:
            raise ValueError("staging artifact order is invalid")
        for kind, path in self.artifact_paths:
            if kind not in DELIVERY_ARTIFACT_ORDER or not isinstance(path, Path):
                raise ValueError("staging artifact path is invalid")
            if path.parent != self.root_directory:
                raise ValueError("staging artifact must be inside root_directory")


@dataclass(frozen=True)
class _DeliveryStagingIdentity:
    path: Path
    device_id: int | None
    file_id: int | None
    file_attributes: int | None
    mode_type: int
    is_reparse: bool


@dataclass
class _DeliveryOwnershipTracker:
    staging_path: Path | None = None
    staging_identity: _DeliveryStagingIdentity | None = None
    parent_directory: Path | None = None
    final_directory: Path | None = None
    artifact_phase: DeliveryArtifactKind | None = None
    commit_phase: Literal[
        "before_commit",
        "awaiting_commit_guard",
        "commit_started",
        "committed",
        "commit_failed",
    ] = "before_commit"
    commit_succeeded: bool = False


@dataclass(frozen=True)
class DeliveryCommitGuardRequest:
    job_id: int
    start_fingerprint: str
    final_directory: Path

    def __post_init__(self) -> None:
        if (
            isinstance(self.job_id, bool)
            or not isinstance(self.job_id, int)
            or self.job_id <= 0
        ):
            raise ValueError("job_id must be a positive integer")
        if type(self.start_fingerprint) is not str or not self.start_fingerprint:
            raise ValueError("start_fingerprint must be a non-empty string")
        if not isinstance(self.final_directory, Path) or not self.final_directory.is_absolute():
            raise ValueError("final_directory must be an absolute Path")


@dataclass(frozen=True)
class DeliveryCommitAuthorization:
    job_id: int
    start_fingerprint: str
    decision: Literal[
        "authorized",
        "stale",
        "cancelled",
        "invalid_job",
        "closing",
    ]

    def __post_init__(self) -> None:
        if (
            isinstance(self.job_id, bool)
            or not isinstance(self.job_id, int)
            or self.job_id <= 0
        ):
            raise ValueError("job_id must be a positive integer")
        if type(self.start_fingerprint) is not str or not self.start_fingerprint:
            raise ValueError("start_fingerprint must be a non-empty string")
        if self.decision not in _DELIVERY_AUTHORIZATION_DECISIONS:
            raise ValueError("unsupported authorization decision")


@dataclass(frozen=True)
class DeliveryArtifactOperations:
    generate_and_validate_vmd: Callable[[DeliveryStartContext, Path, "DeliveryCancelToken"], None]
    generate_and_validate_mmd_wav: Callable[[DeliveryStartContext, Path, "DeliveryCancelToken"], None]
    generate_and_validate_report: Callable[[DeliveryStartContext, Path, "DeliveryCancelToken"], None]
    validate_before_commit: Callable[
        [DeliveryStartContext, tuple[tuple[DeliveryArtifactKind, Path], ...], "DeliveryCancelToken"],
        None,
    ] | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "generate_and_validate_vmd",
            "generate_and_validate_mmd_wav",
            "generate_and_validate_report",
        ):
            if not callable(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be callable")
        if self.validate_before_commit is not None and not callable(self.validate_before_commit):
            raise ValueError("validate_before_commit must be callable or None")


class DeliveryCancelToken:
    """Thread-safe cancellation and process bridge for delivery orchestration."""

    def __init__(self, grace_sec: float = 2.0) -> None:
        if isinstance(grace_sec, bool) or not isinstance(grace_sec, (int, float)):
            raise ValueError("grace_sec must be numeric")
        if grace_sec < 0:
            raise ValueError("grace_sec must be non-negative")
        self._grace_sec = float(grace_sec)
        self._cancel_requested = False
        self._process: Any = None
        self._phase = "created"
        self._commit_started = False
        self._lock = threading.Lock()
        self._commit_lock = threading.Lock()
        self._artifact_seals: dict[
            str,
            tuple[str, tuple[int | None, int | None, int | None, int], str],
        ] = {}

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    @property
    def phase(self) -> str:
        with self._lock:
            return self._phase

    def register_process(self, process: Any) -> None:
        should_cancel = False
        with self._lock:
            self._process = process
            should_cancel = self._cancel_requested
        if should_cancel:
            self._terminate_process_async(process)

    def clear_process(self, process: Any) -> None:
        with self._lock:
            if self._process is process:
                self._process = None

    def request_cancel(self) -> bool:
        process = None
        with self._commit_lock:
            with self._lock:
                if self._commit_started:
                    return False
                self._cancel_requested = True
                process = self._process
        if process is not None:
            self._terminate_process_async(process)
        return True

    def _set_phase(self, phase: str) -> None:
        with self._lock:
            self._phase = phase

    def _begin_commit_locked(self) -> bool:
        with self._lock:
            if self._cancel_requested or self._commit_started:
                return False
            self._commit_started = True
            self._phase = "commit_started"
            return True

    def _set_commit_result(self, phase: Literal["committed", "commit_failed"]) -> None:
        with self._lock:
            self._phase = phase

    @staticmethod
    def _read_artifact_seal(
        path: str | Path,
    ) -> tuple[str, tuple[int | None, int | None, int | None, int], str]:
        artifact = Path(path).resolve(strict=True)
        before = artifact.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
            raise DeliveryContractError(
                "delivery_staging_artifact_invalid",
                "delivery artifact is not a non-empty regular file.",
            )
        digest = hashlib.sha256()
        bytes_read = 0
        with artifact.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                bytes_read += len(chunk)
        after = artifact.stat()
        identity_before = (
            getattr(before, "st_dev", None),
            getattr(before, "st_ino", None),
            getattr(before, "st_mtime_ns", None),
            int(before.st_size),
        )
        identity_after = (
            getattr(after, "st_dev", None),
            getattr(after, "st_ino", None),
            getattr(after, "st_mtime_ns", None),
            int(after.st_size),
        )
        if identity_before != identity_after or bytes_read != after.st_size:
            raise DeliveryContractError(
                "delivery_staging_artifact_invalid",
                "delivery artifact changed while its identity was captured.",
            )
        return str(artifact), identity_after, digest.hexdigest()

    def capture_artifact_seal(self, kind: DeliveryArtifactKind, path: str | Path) -> None:
        if kind not in DELIVERY_ARTIFACT_ORDER:
            raise DeliveryContractError(
                "delivery_artifact_kind_invalid", "delivery artifact kind is invalid."
            )
        seal = self._read_artifact_seal(path)
        with self._lock:
            if kind in self._artifact_seals:
                raise DeliveryContractError(
                    "delivery_artifact_seal_duplicate",
                    "delivery artifact identity was captured more than once.",
                )
            self._artifact_seals[kind] = seal

    def verify_artifact_seal(self, kind: DeliveryArtifactKind, path: str | Path) -> bool:
        with self._lock:
            expected = self._artifact_seals.get(kind)
        if expected is None:
            return False
        try:
            actual = self._read_artifact_seal(path)
        except (DeliveryContractError, OSError, RuntimeError, TypeError, ValueError):
            return False
        return actual == expected

    def has_complete_artifact_seals(self) -> bool:
        with self._lock:
            return tuple(
                kind for kind in DELIVERY_ARTIFACT_ORDER if kind in self._artifact_seals
            ) == DELIVERY_ARTIFACT_ORDER

    def _terminate_process_async(self, process: Any) -> None:
        thread = threading.Thread(
            target=_terminate_delivery_process_then_kill,
            args=(process, self._grace_sec),
            daemon=True,
        )
        thread.start()


def _terminate_delivery_process_then_kill(process: Any, grace_sec: float) -> None:
    try:
        if process.poll() is None:
            process.terminate()
    except Exception:
        return
    try:
        process.wait(timeout=grace_sec)
        return
    except Exception:
        pass
    try:
        if process.poll() is None:
            process.kill()
    except Exception:
        pass


@dataclass(frozen=True)
class DeliveryTerminalResult:
    job_id: int
    primary_status: Literal["success", "cancelled", "failed"]
    primary_error_code: str | None
    committed: bool
    final_path: Path | None
    staging_path: Path | None
    cleanup_status: Literal[
        "not_required",
        "completed",
        "partial_output_cleanup_failed",
    ]
    commit_phase: Literal[
        "before_commit",
        "awaiting_commit_guard",
        "commit_started",
        "committed",
        "commit_failed",
    ]
    artifact_phase: DeliveryArtifactKind | None

    def __post_init__(self) -> None:
        if (
            isinstance(self.job_id, bool)
            or not isinstance(self.job_id, int)
            or self.job_id <= 0
        ):
            raise ValueError("job_id must be a positive integer")
        if self.primary_status not in {"success", "cancelled", "failed"}:
            raise ValueError("unsupported terminal status")
        if self.primary_error_code is not None and (
            type(self.primary_error_code) is not str or not self.primary_error_code
        ):
            raise ValueError("primary_error_code must be None or non-empty")
        if not isinstance(self.committed, bool):
            raise ValueError("committed must be bool")
        for field_name in ("final_path", "staging_path"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, Path):
                raise ValueError(f"{field_name} must be Path or None")
        if self.cleanup_status not in {
            "not_required",
            "completed",
            "partial_output_cleanup_failed",
        }:
            raise ValueError("unsupported cleanup status")
        if self.commit_phase not in {
            "before_commit",
            "awaiting_commit_guard",
            "commit_started",
            "committed",
            "commit_failed",
        }:
            raise ValueError("unsupported commit phase")
        if self.artifact_phase is not None and self.artifact_phase not in DELIVERY_ARTIFACT_ORDER:
            raise ValueError("unsupported artifact phase")
        if self.cleanup_status == "partial_output_cleanup_failed":
            if self.staging_path is None:
                raise ValueError("cleanup failure requires staging_path")
        elif self.staging_path is not None:
            raise ValueError("staging_path requires cleanup failure")
        if self.primary_status == "success":
            if (
                not self.committed
                or self.primary_error_code is not None
                or self.final_path is None
                or self.staging_path is not None
                or self.cleanup_status != "not_required"
                or self.commit_phase != "committed"
            ):
                raise ValueError("invalid success terminal result")
        else:
            if self.committed or self.final_path is not None:
                raise ValueError("non-success terminal cannot be committed")
            if self.primary_status == "cancelled":
                if self.primary_error_code != "output_cancelled":
                    raise ValueError("cancelled terminal requires output_cancelled")
            elif self.primary_error_code is None:
                raise ValueError("failed terminal requires an error code")
            if self.commit_phase == "committed":
                raise ValueError("non-success terminal cannot be committed phase")


def _build_delivery_final_paths(
    parent_directory: Path,
    folder_name: str,
    artifact_names: DeliveryArtifactNames,
) -> tuple[Path, tuple[tuple[DeliveryArtifactKind, Path], ...]]:
    final_directory = parent_directory / folder_name
    file_names = {
        "vmd": artifact_names.vmd_file_name,
        "mmd_wav": artifact_names.mmd_wav_file_name,
        "report": artifact_names.report_file_name,
    }
    artifact_paths = tuple(
        (kind, final_directory / file_names[kind])
        for kind in DELIVERY_ARTIFACT_ORDER
    )
    return final_directory, artifact_paths


def validate_delivery_destination(
    start_context: DeliveryStartContext,
) -> ValidatedDeliveryDestination:
    """Validate destination inputs and inspect the final path without side effects."""
    if not isinstance(start_context, DeliveryStartContext):
        raise DeliveryContractError(
            "output_parent_invalid",
            "The delivery start context is invalid.",
        )
    if start_context.current_state.gate_status != "ready":
        raise DeliveryContractError(
            "output_path_invalid",
            "The delivery start context is not ready.",
        )
    parent_directory = _validate_delivery_parent(start_context.parent_directory)
    _validate_delivery_component(start_context.folder_name, "folder_name")
    artifact_names = _validate_delivery_artifact_names(
        start_context.current_state.artifact_names
    )
    final_directory, final_artifact_paths = _build_delivery_final_paths(
        parent_directory,
        start_context.folder_name,
        artifact_names,
    )
    _validate_delivery_absolute_path(final_directory, "final_directory")
    for _, path in final_artifact_paths:
        _validate_delivery_absolute_path(path, "final artifact path")
    staging_probe = parent_directory / ("x" * STAGING_COMPONENT_UTF16_BUDGET)
    _validate_delivery_absolute_path(staging_probe, "staging directory path")
    for _, path in final_artifact_paths:
        _validate_delivery_absolute_path(
            staging_probe / path.name,
            "staging artifact path",
        )
    _inspect_delivery_absence(final_directory)
    return ValidatedDeliveryDestination(
        parent_directory=parent_directory,
        folder_name=start_context.folder_name,
        final_directory=final_directory,
        final_artifact_paths=final_artifact_paths,
    )


def _build_staging_paths(
    destination: ValidatedDeliveryDestination,
    root_directory: Path,
) -> DeliveryStagingPaths:
    file_name_by_kind = {
        kind: path.name for kind, path in destination.final_artifact_paths
    }
    artifact_paths = tuple(
        (kind, root_directory / file_name_by_kind[kind])
        for kind in DELIVERY_ARTIFACT_ORDER
    )
    return DeliveryStagingPaths(
        root_directory=root_directory,
        artifact_paths=artifact_paths,
    )


def _validate_staging_directory(
    destination: ValidatedDeliveryDestination,
    staging: DeliveryStagingPaths,
) -> _DeliveryStagingIdentity:
    root_directory = staging.root_directory
    if not root_directory.is_absolute() or root_directory.parent != destination.parent_directory:
        raise DeliveryContractError(
            "output_staging_invalid",
            "The staging directory is outside the validated parent directory.",
        )
    _validate_delivery_component(root_directory.name, "staging directory name")
    if _utf16_code_units(root_directory.name) > STAGING_COMPONENT_UTF16_BUDGET:
        raise DeliveryContractError(
            "output_staging_invalid",
            "The staging directory name exceeds its safety budget.",
        )
    _validate_delivery_absolute_path(root_directory, "staging directory path")
    for _, path in staging.artifact_paths:
        _validate_delivery_absolute_path(path, "staging artifact path")
    return _capture_delivery_staging_identity(destination, staging)


def _validate_staging_artifact_file(path: Path) -> None:
    try:
        file_stat = os.lstat(path)
    except (OSError, ValueError) as error:
        raise DeliveryContractError(
            _delivery_os_error_code(error, "delivery_staging_artifact_invalid"),
            "A staging artifact is missing or cannot be inspected.",
        ) from error
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or _is_reparse_or_link(file_stat)
        or file_stat.st_size <= 0
    ):
        raise DeliveryContractError(
            "delivery_staging_artifact_invalid",
            "A staging artifact is not a non-empty regular file.",
        )


def _validate_staging_contents(staging: DeliveryStagingPaths) -> None:
    expected_names = {path.name for _, path in staging.artifact_paths}
    discovered_names: list[str] = []
    try:
        with os.scandir(staging.root_directory) as entries:
            for entry in entries:
                if entry.name not in expected_names:
                    raise DeliveryContractError(
                        "delivery_staging_contents_invalid",
                        "The staging directory contains an unexpected entry.",
                    )
                if entry.name in discovered_names:
                    raise DeliveryContractError(
                        "delivery_staging_contents_invalid",
                        "The staging directory contains duplicate artifact names.",
                    )
                discovered_names.append(entry.name)
                _validate_staging_artifact_file(Path(entry.path))
    except DeliveryContractError:
        raise
    except (OSError, ValueError) as error:
        raise DeliveryContractError(
            _delivery_os_error_code(error, "delivery_staging_contents_invalid"),
            "The staging directory contents could not be inspected.",
        ) from error
    if set(discovered_names) != expected_names:
        raise DeliveryContractError(
            "delivery_staging_contents_invalid",
            "The staging directory does not contain exactly the three artifacts.",
        )
    for _, path in staging.artifact_paths:
        _validate_staging_artifact_file(path)


def _delivery_staging_identity_matches(
    path: Path,
    expected_identity: _DeliveryStagingIdentity,
    file_stat: Any | None = None,
) -> bool:
    try:
        if file_stat is None:
            file_stat = os.lstat(path)
        actual_identity = _DeliveryStagingIdentity(
            path=path,
            device_id=getattr(file_stat, "st_dev", None),
            file_id=getattr(file_stat, "st_ino", None),
            file_attributes=getattr(file_stat, "st_file_attributes", None),
            mode_type=stat.S_IFMT(file_stat.st_mode),
            is_reparse=_is_reparse_or_link(file_stat),
        )
    except Exception:
        return False
    return actual_identity == expected_identity


def _cleanup_owned_staging(
    staging_path: Path | None,
    parent_directory: Path | None,
    expected_identity: _DeliveryStagingIdentity | None = None,
) -> bool:
    if staging_path is None:
        return True
    if (
        parent_directory is None
        or not isinstance(staging_path, Path)
        or not staging_path.is_absolute()
        or staging_path.parent != parent_directory
    ):
        return False
    try:
        file_stat = os.lstat(staging_path)
    except FileNotFoundError:
        return True
    except Exception:
        return False
    if expected_identity is not None:
        if not _delivery_staging_identity_matches(
            staging_path,
            expected_identity,
            file_stat,
        ):
            return False
    try:
        if _is_reparse_or_link(file_stat):
            if stat.S_ISDIR(file_stat.st_mode):
                os.rmdir(staging_path)
            else:
                os.unlink(staging_path)
        elif stat.S_ISDIR(file_stat.st_mode):
            shutil.rmtree(staging_path)
        else:
            os.unlink(staging_path)
    except Exception:
        pass
    try:
        os.lstat(staging_path)
    except FileNotFoundError:
        return True
    except Exception:
        return False
    return False


_ORIGINAL_CLEANUP_OWNED_STAGING = _cleanup_owned_staging


def _cleanup_status(
    staging_path: Path | None,
    parent_directory: Path | None,
    expected_identity: _DeliveryStagingIdentity | None = None,
) -> tuple[Literal["not_required", "completed", "partial_output_cleanup_failed"], Path | None]:
    if staging_path is None:
        return "not_required", None
    try:
        if expected_identity is None:
            cleanup_succeeded = _cleanup_owned_staging(staging_path, parent_directory)
        else:
            try:
                current_stat = os.lstat(staging_path)
            except FileNotFoundError:
                cleanup_succeeded = True
            except Exception:
                cleanup_succeeded = False
            else:
                identity_matches = _delivery_staging_identity_matches(
                    staging_path,
                    expected_identity,
                    current_stat,
                )
                if not identity_matches:
                    cleanup_succeeded = False
                elif _cleanup_owned_staging is _ORIGINAL_CLEANUP_OWNED_STAGING:
                    cleanup_succeeded = _cleanup_owned_staging(
                        staging_path,
                        parent_directory,
                        expected_identity,
                    )
                else:
                    cleanup_succeeded = _cleanup_owned_staging(
                        staging_path,
                        parent_directory,
                    )
    except Exception:
        cleanup_succeeded = False
    if cleanup_succeeded:
        return "completed", None
    return "partial_output_cleanup_failed", staging_path


def _build_delivery_terminal_result(
    *,
    job_id: int,
    primary_status: Literal["success", "cancelled", "failed"],
    primary_error_code: str | None,
    committed: bool,
    final_path: Path | None,
    staging_path: Path | None,
    parent_directory: Path | None,
    commit_phase: Literal[
        "before_commit",
        "awaiting_commit_guard",
        "commit_started",
        "committed",
        "commit_failed",
    ],
    artifact_phase: DeliveryArtifactKind | None,
    staging_identity: _DeliveryStagingIdentity | None = None,
) -> DeliveryTerminalResult:
    if committed:
        return DeliveryTerminalResult(
            job_id=job_id,
            primary_status="success",
            primary_error_code=None,
            committed=True,
            final_path=final_path,
            staging_path=None,
            cleanup_status="not_required",
            commit_phase="committed",
            artifact_phase=artifact_phase,
        )
    cleanup_status, residual_staging = _cleanup_status(
        staging_path,
        parent_directory,
        staging_identity,
    )
    return DeliveryTerminalResult(
        job_id=job_id,
        primary_status=primary_status,
        primary_error_code=primary_error_code,
        committed=False,
        final_path=None,
        staging_path=residual_staging,
        cleanup_status=cleanup_status,
        commit_phase=commit_phase,
        artifact_phase=artifact_phase,
    )


def _delivery_exception_code(error: Exception, default_code: str) -> str:
    code = getattr(error, "code", None)
    if type(code) is str and code:
        if code not in _DELIVERY_OS_REMAP_CODES:
            return code
        default_code = code
    return _delivery_os_error_code(error, default_code)


def _artifact_callable_for_kind(
    operations: DeliveryArtifactOperations,
    kind: DeliveryArtifactKind,
) -> Callable[[DeliveryStartContext, Path, DeliveryCancelToken], None]:
    return {
        "vmd": operations.generate_and_validate_vmd,
        "mmd_wav": operations.generate_and_validate_mmd_wav,
        "report": operations.generate_and_validate_report,
    }[kind]


def _orchestrate_delivery_package_impl(
    *,
    job_id: int,
    start_context: DeliveryStartContext,
    artifact_operations: DeliveryArtifactOperations,
    pre_commit_guard: Callable[
        [DeliveryCommitGuardRequest, DeliveryCancelToken],
        DeliveryCommitAuthorization,
    ],
    cancel_token: DeliveryCancelToken,
    _ownership_tracker: _DeliveryOwnershipTracker | None = None,
) -> DeliveryTerminalResult:
    """Generate a delivery package transactionally into a dedicated directory."""
    ownership_tracker = _ownership_tracker or _DeliveryOwnershipTracker()
    terminal_builder = globals()["_build_delivery_terminal_result"]

    def _build_delivery_terminal_result(**kwargs: Any) -> DeliveryTerminalResult:
        if kwargs.get("staging_path") is not None:
            kwargs.setdefault("staging_identity", ownership_tracker.staging_identity)
        return terminal_builder(**kwargs)
    if (
        isinstance(job_id, bool)
        or not isinstance(job_id, int)
        or job_id <= 0
    ):
        raise DeliveryContractError(
            "delivery_job_invalid",
            "The delivery job ID is invalid.",
        )
    if not isinstance(cancel_token, DeliveryCancelToken):
        raise DeliveryContractError(
            "delivery_cancel_token_invalid",
            "The delivery cancel token is invalid.",
        )
    if not isinstance(artifact_operations, DeliveryArtifactOperations):
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="delivery_artifact_operations_invalid",
            committed=False,
            final_path=None,
            staging_path=None,
            parent_directory=None,
            commit_phase="before_commit",
            artifact_phase=None,
        )
    if not callable(pre_commit_guard):
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="delivery_commit_guard_failed",
            committed=False,
            final_path=None,
            staging_path=None,
            parent_directory=None,
            commit_phase="before_commit",
            artifact_phase=None,
        )
    if cancel_token.cancel_requested:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="cancelled",
            primary_error_code="output_cancelled",
            committed=False,
            final_path=None,
            staging_path=None,
            parent_directory=None,
            commit_phase="before_commit",
            artifact_phase=None,
        )

    cancel_token._set_phase("validating_destination")
    try:
        destination = validate_delivery_destination(start_context)
    except DeliveryContractError as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=error.code,
            committed=False,
            final_path=None,
            staging_path=None,
            parent_directory=None,
            commit_phase="before_commit",
            artifact_phase=None,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="output_path_invalid",
            committed=False,
            final_path=None,
            staging_path=None,
            parent_directory=None,
            commit_phase="before_commit",
            artifact_phase=None,
        )
    ownership_tracker.parent_directory = destination.parent_directory
    ownership_tracker.final_directory = destination.final_directory
    if cancel_token.cancel_requested:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="cancelled",
            primary_error_code="output_cancelled",
            committed=False,
            final_path=None,
            staging_path=None,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase=None,
        )

    owned_staging: Path | None = None
    staging: DeliveryStagingPaths | None = None
    try:
        owned_staging = Path(
            tempfile.mkdtemp(
                dir=str(destination.parent_directory),
                prefix=_STAGING_PREFIX,
                suffix=_STAGING_SUFFIX,
            )
        )
        ownership_tracker.staging_path = owned_staging
        staging = _build_staging_paths(destination, owned_staging)
        staging_identity = _validate_staging_directory(destination, staging)
        ownership_tracker.staging_identity = staging_identity
    except DeliveryContractError as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=error.code,
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase=None,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=_delivery_exception_code(
                error,
                "output_staging_create_failed",
            ),
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase=None,
        )
    assert staging is not None
    assert staging_identity is not None

    try:
        _assert_delivery_staging_identity(
            destination,
            staging,
            staging_identity,
        )
        _inspect_delivery_absence(destination.final_directory)
    except DeliveryContractError as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=error.code,
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase=None,
        )

    artifact_phase: DeliveryArtifactKind | None = None
    for kind in DELIVERY_ARTIFACT_ORDER:
        artifact_phase = kind
        ownership_tracker.artifact_phase = kind
        if cancel_token.cancel_requested:
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="cancelled",
                primary_error_code="output_cancelled",
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase=kind,
            )
        cancel_token._set_phase(f"generating_{kind}")
        artifact_path = dict(staging.artifact_paths)[kind]
        operation = _artifact_callable_for_kind(artifact_operations, kind)
        try:
            _assert_delivery_staging_identity(
                destination,
                staging,
                staging_identity,
            )
            operation(start_context, artifact_path, cancel_token)
            _assert_delivery_staging_identity(
                destination,
                staging,
                staging_identity,
            )
        except Exception as error:
            if cancel_token.cancel_requested:
                return _build_delivery_terminal_result(
                    job_id=job_id,
                    primary_status="cancelled",
                    primary_error_code="output_cancelled",
                    committed=False,
                    final_path=None,
                    staging_path=owned_staging,
                    parent_directory=destination.parent_directory,
                    commit_phase="before_commit",
                    artifact_phase=kind,
                )
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="failed",
                primary_error_code=_delivery_exception_code(
                    error,
                    f"{kind}_write_failed",
                ),
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase=kind,
            )
        if cancel_token.cancel_requested:
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="cancelled",
                primary_error_code="output_cancelled",
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase=kind,
            )
        try:
            _assert_delivery_staging_identity(
                destination,
                staging,
                staging_identity,
            )
            _validate_staging_artifact_file(artifact_path)
            _inspect_delivery_absence(destination.final_directory)
            _assert_delivery_staging_identity(
                destination,
                staging,
                staging_identity,
            )
        except DeliveryContractError as error:
            default_code = (
                "output_destination_collision"
                if error.code
                in {"output_destination_collision", "output_path_inspection_failed"}
                else f"{kind}_validation_failed"
            )
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="failed",
                primary_error_code=(
                    error.code if error.code != "delivery_staging_artifact_invalid" else default_code
                ),
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase=kind,
            )
    try:
        _assert_delivery_staging_identity(
            destination,
            staging,
            staging_identity,
        )
        _validate_staging_contents(staging)
        _inspect_delivery_absence(destination.final_directory)
        _assert_delivery_staging_identity(
            destination,
            staging,
            staging_identity,
        )
    except DeliveryContractError as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=error.code,
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase="report",
        )

    validate_before_commit = artifact_operations.validate_before_commit
    if (
        start_context.current_state.projection_kind == "shared_final_output"
        and validate_before_commit is None
    ):
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="delivery_artifact_operations_invalid",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase="report",
        )
    if validate_before_commit is not None:
        if cancel_token.cancel_requested:
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="cancelled",
                primary_error_code="output_cancelled",
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase="report",
            )
        try:
            validate_before_commit(
                start_context,
                staging.artifact_paths,
                cancel_token,
            )
        except Exception as error:
            if cancel_token.cancel_requested:
                return _build_delivery_terminal_result(
                    job_id=job_id,
                    primary_status="cancelled",
                    primary_error_code="output_cancelled",
                    committed=False,
                    final_path=None,
                    staging_path=owned_staging,
                    parent_directory=destination.parent_directory,
                    commit_phase="before_commit",
                    artifact_phase="report",
                )
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="failed",
                primary_error_code=_delivery_exception_code(
                    error,
                    "vmd_validation_failed",
                ),
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase="report",
            )
        if start_context.current_state.projection_kind == "shared_final_output":
            if not cancel_token.has_complete_artifact_seals() or not all(
                cancel_token.verify_artifact_seal(kind, path)
                for kind, path in staging.artifact_paths
            ):
                return _build_delivery_terminal_result(
                    job_id=job_id,
                    primary_status="failed",
                    primary_error_code="vmd_validation_failed",
                    committed=False,
                    final_path=None,
                    staging_path=owned_staging,
                    parent_directory=destination.parent_directory,
                    commit_phase="before_commit",
                    artifact_phase="report",
                )

    if cancel_token.cancel_requested:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="cancelled",
            primary_error_code="output_cancelled",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="before_commit",
            artifact_phase="report",
        )

    cancel_token._set_phase("awaiting_commit_guard")
    ownership_tracker.commit_phase = "awaiting_commit_guard"
    request = DeliveryCommitGuardRequest(
        job_id=job_id,
        start_fingerprint=start_context.current_state.start_fingerprint,
        final_directory=destination.final_directory,
    )
    try:
        authorization = pre_commit_guard(request, cancel_token)
    except Exception:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="delivery_commit_guard_failed",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )
    if not isinstance(authorization, DeliveryCommitAuthorization):
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="delivery_commit_authorization_invalid",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )
    if (
        authorization.job_id != request.job_id
        or authorization.start_fingerprint != request.start_fingerprint
    ):
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="delivery_commit_authorization_invalid",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )
    if start_context.current_state.projection_kind == "shared_final_output" and not all(
        cancel_token.verify_artifact_seal(kind, path)
        for kind, path in staging.artifact_paths
    ):
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code="vmd_validation_failed",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )
    if authorization.decision in {"cancelled", "closing"} or cancel_token.cancel_requested:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="cancelled",
            primary_error_code="output_cancelled",
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )
    if authorization.decision != "authorized":
        code = (
            "delivery_state_stale"
            if authorization.decision == "stale"
            else "delivery_job_invalid"
            if authorization.decision == "invalid_job"
            else "delivery_commit_guard_failed"
        )
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=code,
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )
    try:
        _inspect_delivery_absence(destination.final_directory)
    except DeliveryContractError as error:
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=error.code,
            committed=False,
            final_path=None,
            staging_path=owned_staging,
            parent_directory=destination.parent_directory,
            commit_phase="awaiting_commit_guard",
            artifact_phase="report",
        )

    with cancel_token._commit_lock:
        try:
            _assert_delivery_staging_identity(
                destination,
                staging,
                staging_identity,
            )
            _inspect_delivery_absence(destination.final_directory)
        except DeliveryContractError as error:
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="failed",
                primary_error_code=error.code,
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="awaiting_commit_guard",
                artifact_phase="report",
            )
        if not cancel_token._begin_commit_locked():
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="cancelled",
                primary_error_code="output_cancelled",
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="before_commit",
                artifact_phase="report",
            )
        ownership_tracker.commit_phase = "commit_started"
        try:
            os.rename(owned_staging, destination.final_directory)
        except Exception as error:
            ownership_tracker.commit_phase = "commit_failed"
            cancel_token._set_commit_result("commit_failed")
            try:
                _inspect_delivery_absence(destination.final_directory)
            except DeliveryContractError as collision_error:
                error_code = collision_error.code
            else:
                error_code = _delivery_exception_code(error, "delivery_commit_failed")
            return _build_delivery_terminal_result(
                job_id=job_id,
                primary_status="failed",
                primary_error_code=error_code,
                committed=False,
                final_path=None,
                staging_path=owned_staging,
                parent_directory=destination.parent_directory,
                commit_phase="commit_failed",
                artifact_phase="report",
            )
        ownership_tracker.commit_succeeded = True
        ownership_tracker.commit_phase = "committed"
        cancel_token._set_commit_result("committed")
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="success",
            primary_error_code=None,
            committed=True,
            final_path=destination.final_directory,
            staging_path=None,
            parent_directory=destination.parent_directory,
            commit_phase="committed",
            artifact_phase="report",
        )


def orchestrate_delivery_package(
    *,
    job_id: int,
    start_context: DeliveryStartContext,
    artifact_operations: DeliveryArtifactOperations,
    pre_commit_guard: Callable[
        [DeliveryCommitGuardRequest, DeliveryCancelToken],
        DeliveryCommitAuthorization,
    ],
    cancel_token: DeliveryCancelToken,
) -> DeliveryTerminalResult:
    """Converge post-staging failures into one recoverable terminal result."""
    ownership_tracker = _DeliveryOwnershipTracker()
    try:
        return _orchestrate_delivery_package_impl(
            job_id=job_id,
            start_context=start_context,
            artifact_operations=artifact_operations,
            pre_commit_guard=pre_commit_guard,
            cancel_token=cancel_token,
            _ownership_tracker=ownership_tracker,
        )
    except Exception as error:
        if ownership_tracker.commit_succeeded:
            return DeliveryTerminalResult(
                job_id=job_id,
                primary_status="success",
                primary_error_code=None,
                committed=True,
                final_path=ownership_tracker.final_directory,
                staging_path=None,
                cleanup_status="not_required",
                commit_phase="committed",
                artifact_phase=ownership_tracker.artifact_phase,
            )
        if ownership_tracker.staging_path is None:
            raise
        return _build_delivery_terminal_result(
            job_id=job_id,
            primary_status="failed",
            primary_error_code=_delivery_exception_code(
                error,
                "delivery_worker_failed",
            ),
            committed=False,
            final_path=None,
            staging_path=ownership_tracker.staging_path,
            parent_directory=ownership_tracker.parent_directory,
            commit_phase=(
                ownership_tracker.commit_phase
                if ownership_tracker.commit_phase != "committed"
                else "commit_failed"
            ),
            artifact_phase=ownership_tracker.artifact_phase,
            staging_identity=ownership_tracker.staging_identity,
        )
