"""UI-independent diagnostics and save-state fingerprinting for MS20-B2.

The module deliberately contains no GUI, filesystem I/O, or persistence logic.
It turns an explicit snapshot input into deterministic summaries, diagnostic
identities, and a canonical SHA-256 payload for the VMD writer boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Literal, TypeAlias

from src.core.pipeline import (
    PeakValueEvaluation,
    PeakValueObservation,
    VowelTimingPlan,
)
from src.core.event_adjustment import validate_long_vowel_mode
from src.core.morph_name_sets import (
    JAPANESE_MORPH_NAME_SET_ID,
    validate_builtin_output_morph_name,
    validate_output_morph_names,
    get_builtin_morph_name_set,
)
from src.core.whisper_timing import SpeechTimingAnchor
from src.core.transition_diagnostics import TransitionDiagnosticSummary
from src.vmd_writer import SUPPORTED_MORPHS, VMD_FPS, VowelTimelinePoint


SourceDiagnosticSeverity: TypeAlias = Literal[
    "info", "warning", "error", "fatal", "cancelled"
]
DiagnosticRecoverability: TypeAlias = Literal[
    "retry_possible",
    "select_file_again",
    "fallback_used",
    "restart_recommended",
    "cannot_continue",
    "cancelled_by_user",
]
CanonicalScalar: TypeAlias = None | bool | int | str
CanonicalValue: TypeAlias = CanonicalScalar | tuple["CanonicalValue", ...]
DiagnosticIdentityContext: TypeAlias = tuple[tuple[str, CanonicalValue], ...]
FingerprintPayload: TypeAlias = tuple[tuple[str, CanonicalValue], ...]
EffectiveWriterInputState: TypeAlias = Literal[
    "not_applicable", "ready", "invalid"
]

_SOURCE_SEVERITIES = {"info", "warning", "error", "fatal", "cancelled"}
_RECOVERABILITIES = {
    "retry_possible",
    "select_file_again",
    "fallback_used",
    "restart_recommended",
    "cannot_continue",
    "cancelled_by_user",
}
_INPUT_MODES = {"text_audio", "voice_only"}
_EFFECTIVE_WRITER_INPUT_STATES = {"not_applicable", "ready", "invalid"}
_FINGERPRINT_SCHEMA_VERSION = "ms21-effective-output-v1"
_SHARED_FINAL_OUTPUT_FINGERPRINT_SCHEMA_VERSION = "ms31-final-output-v1"
_PROFILE_RESOLUTION_REASONS = {
    "profile_store_unavailable",
    "orphan_profile_baseline",
    "active_profile_not_found",
    "profile_default_preset_not_found",
    "runtime_baseline_preset_not_found",
}

_WHISPER_IDENTITY_STATUSES = {
    "not_applicable",
    "consistent",
    "incomplete",
    "mismatch",
}
_WHISPER_RUNTIME_IDENTITY_STATUSES = _WHISPER_IDENTITY_STATUSES | {"unloaded"}
_WHISPER_PACKAGE_GATE_STATUSES = {"not_checked", "passed", "failed"}
_WHISPER_PREVIEW_PROJECTION_STATUSES = {
    "ready",
    "analysis_required",
    "unavailable",
}
_WHISPER_STORAGE_LOCATION_KINDS = {
    "default",
    "user_specified",
    "unresolved",
    "not_applicable",
}


@dataclass(frozen=True)
class WhisperModelDiagnosticsItem:
    """Safe, manifest-backed display data for one Whisper model candidate."""

    model_key: str
    display_name: str
    size_bytes: int
    vram_hint: str
    speed_hint: str
    recommended_use: str
    expected_manifest_identity: str
    availability_status: str = "unknown"
    availability_failure_code: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "model_key",
            "display_name",
            "vram_hint",
            "speed_hint",
            "recommended_use",
            "expected_manifest_identity",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be a non-empty string")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise ValueError("size_bytes must be an integer")
        if self.size_bytes <= 0:
            raise ValueError("size_bytes must be positive")
        if not isinstance(self.availability_status, str) or not self.availability_status:
            raise ValueError("availability_status must be a non-empty string")
        if self.availability_failure_code is not None and (
            not isinstance(self.availability_failure_code, str)
            or not self.availability_failure_code
        ):
            raise ValueError("availability_failure_code must be None or non-empty string")


@dataclass(frozen=True)
class WhisperDiagnosticsSummary:
    """Immutable Whisper projection shared by all diagnostics consumers."""

    models: tuple[WhisperModelDiagnosticsItem, ...] = ()
    selected_model_key: str | None = None
    selected_model_display_name: str | None = None
    selected_manifest_identity: str | None = None
    selected_availability_status: str | None = None
    active_model_key: str | None = None
    active_model_display_name: str | None = None
    active_manifest_identity: str | None = None
    active_availability_status: str | None = None
    loaded_model_key: str | None = None
    loaded_model_display_name: str | None = None
    loaded_manifest_identity: str | None = None
    analysis_model_key: str | None = None
    analysis_model_display_name: str | None = None
    analysis_manifest_identity: str | None = None
    manifest_schema_version: int | None = None
    package_name: str = "openai-whisper"
    package_version: str = "20250625"
    package_gate_status: str = "not_checked"
    availability_scan_status: str = "not_applicable"
    availability_scan_failure_code: str | None = None
    management_operation: str = "idle"
    management_phase: str = "idle"
    management_busy: bool = False
    management_job_id: int = 0
    management_model_key: str | None = None
    management_received_bytes: int = 0
    management_expected_bytes: int = 0
    management_failure_code: str | None = None
    management_cleanup_status: str | None = None
    active_config_status: str = "not_applicable"
    active_config_reason: str | None = None
    panel_revision: int = 0
    analysis_rebuild_reason: str = "none"
    failure_class: str = "none"
    failure_detail_code: str | None = None
    safe_failure_notice: str = ""
    recoverability: str = "not_applicable"
    analysis_identity_status: str = "not_applicable"
    runtime_identity_status: str = "not_applicable"
    storage_location_kind: str = "not_applicable"
    storage_location_display: str = "保存先を確認できません"
    application_busy: bool = False
    transcription_text_present: bool = False
    transcription_edit_available: bool = False
    preview_projection_status: str = "unavailable"

    def __post_init__(self) -> None:
        object.__setattr__(self, "models", tuple(self.models))
        if any(not isinstance(item, WhisperModelDiagnosticsItem) for item in self.models):
            raise ValueError("models must contain WhisperModelDiagnosticsItem values")
        for field_name in (
            "selected_model_key",
            "selected_model_display_name",
            "selected_manifest_identity",
            "selected_availability_status",
            "active_model_key",
            "active_model_display_name",
            "active_manifest_identity",
            "active_availability_status",
            "loaded_model_key",
            "loaded_model_display_name",
            "loaded_manifest_identity",
            "analysis_model_key",
            "analysis_model_display_name",
            "analysis_manifest_identity",
            "active_config_reason",
            "failure_detail_code",
            "management_failure_code",
            "management_cleanup_status",
        ):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{field_name} must be None or non-empty string")
        if not isinstance(self.package_name, str) or not self.package_name:
            raise ValueError("package_name must be a non-empty string")
        if not isinstance(self.package_version, str) or not self.package_version:
            raise ValueError("package_version must be a non-empty string")
        if self.package_gate_status not in _WHISPER_PACKAGE_GATE_STATUSES:
            raise ValueError("unsupported package_gate_status")
        if self.analysis_identity_status not in _WHISPER_IDENTITY_STATUSES:
            raise ValueError("unsupported analysis_identity_status")
        if self.runtime_identity_status not in _WHISPER_RUNTIME_IDENTITY_STATUSES:
            raise ValueError("unsupported runtime_identity_status")
        if self.storage_location_kind not in _WHISPER_STORAGE_LOCATION_KINDS:
            raise ValueError("unsupported storage_location_kind")
        if self.preview_projection_status not in _WHISPER_PREVIEW_PROJECTION_STATUSES:
            raise ValueError("unsupported preview_projection_status")
        for field_name in (
            "management_job_id",
            "management_received_bytes",
            "management_expected_bytes",
            "panel_revision",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.management_received_bytes > self.management_expected_bytes and self.management_expected_bytes:
            raise ValueError("management progress cannot exceed expected bytes")
        for field_name in (
            "management_busy",
            "application_busy",
            "transcription_text_present",
            "transcription_edit_available",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be bool")
        if not isinstance(self.storage_location_display, str) or not self.storage_location_display:
            raise ValueError("storage_location_display must be a non-empty string")

    @property
    def selected_model_manifest_identity(self) -> str | None:
        return self.selected_manifest_identity

    @property
    def active_model_manifest_identity(self) -> str | None:
        return self.active_manifest_identity

    @property
    def loaded_whisper_model_key(self) -> str | None:
        return self.loaded_model_key

    @property
    def loaded_whisper_manifest_identity(self) -> str | None:
        return self.loaded_manifest_identity

    @property
    def analysis_whisper_model_key(self) -> str | None:
        return self.analysis_model_key

    @property
    def analysis_whisper_manifest_identity(self) -> str | None:
        return self.analysis_manifest_identity


def _validate_optional_non_negative_int(value: object, field_name: str) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value < 0
    ):
        raise ValueError(f"{field_name} must be None or a non-negative integer")


def _validate_generation_summary_fields(
    *,
    active_long_vowel_mode: object,
    active_preset_id: object,
    active_preset_display_name: object,
    effective_long_vowel_hold_run_count: object,
    effective_long_vowel_decay_run_count: object,
    long_vowel_mode_override_count: object,
) -> None:
    try:
        validate_long_vowel_mode(active_long_vowel_mode)
    except ValueError as error:
        raise ValueError("active_long_vowel_mode must be 'hold' or 'decay'") from error
    if active_preset_id is None:
        if active_preset_display_name is not None:
            raise ValueError(
                "active_preset_id and active_preset_display_name must both be None or present"
            )
    elif (
        type(active_preset_id) is not str
        or not active_preset_id
        or type(active_preset_display_name) is not str
        or not active_preset_display_name
    ):
        raise ValueError(
            "active_preset_id and active_preset_display_name must both be None or present"
        )
    _validate_optional_non_negative_int(
        effective_long_vowel_hold_run_count,
        "effective_long_vowel_hold_run_count",
    )
    _validate_optional_non_negative_int(
        effective_long_vowel_decay_run_count,
        "effective_long_vowel_decay_run_count",
    )
    if (
        isinstance(long_vowel_mode_override_count, bool)
        or not isinstance(long_vowel_mode_override_count, int)
        or long_vowel_mode_override_count < 0
    ):
        raise ValueError("long_vowel_mode_override_count must be a non-negative integer")


def _validate_profile_summary_fields(
    *,
    active_model_profile_id: object,
    active_model_profile_display_name: object,
    active_profile_baseline_preset_id: object,
    baseline_preset_display_name: object,
    resolution_status: object,
    resolution_reason_code: object,
    resolved_morph_name_set_id: object,
    resolved_morph_name_set_display_name: object,
) -> None:
    statuses = {
        "no_profile",
        "resolved",
        "fallback_profile_default",
        "fallback_no_profile",
    }
    if resolution_status not in statuses:
        raise ValueError("unsupported model profile resolution status")
    for name, value in (
        ("active_model_profile_id", active_model_profile_id),
        ("active_profile_baseline_preset_id", active_profile_baseline_preset_id),
    ):
        if value is not None and (type(value) is not str or not value):
            raise ValueError(f"{name} must be None or a non-empty string")
    for name, value in (
        ("active_model_profile_display_name", active_model_profile_display_name),
        ("baseline_preset_display_name", baseline_preset_display_name),
    ):
        if value is not None and (type(value) is not str or not value):
            raise ValueError(f"{name} must be None or a non-empty string")
    if (active_model_profile_id is None) != (active_model_profile_display_name is None):
        raise ValueError("profile ID and display name must be a pair")
    if (active_profile_baseline_preset_id is None) != (baseline_preset_display_name is None):
        raise ValueError("baseline ID and display name must be a pair")
    if resolution_status in {"resolved", "fallback_profile_default"}:
        if active_model_profile_id is None or active_profile_baseline_preset_id is None:
            raise ValueError("resolved profile status requires profile and baseline IDs")
        if resolution_reason_code is not None and resolution_status == "resolved":
            raise ValueError("resolved profile status must not have a fallback reason")
    elif resolution_status in {"no_profile", "fallback_no_profile"}:
        if active_model_profile_id is not None or active_profile_baseline_preset_id is not None:
            raise ValueError("no-profile status must not have profile IDs")
    if resolution_status == "no_profile" and resolution_reason_code is not None:
        raise ValueError("no_profile status must not have a reason")
    if resolution_status != "no_profile":
        if resolution_reason_code is not None and (
            type(resolution_reason_code) is not str
            or resolution_reason_code not in _PROFILE_RESOLUTION_REASONS
        ):
            raise ValueError("resolution_reason_code is not a supported profile reason")
        if resolution_status == "fallback_profile_default" and (
            resolution_reason_code != "runtime_baseline_preset_not_found"
        ):
            raise ValueError("fallback_profile_default reason is invalid")
        if resolution_status == "fallback_no_profile" and (
            resolution_reason_code
            not in {
                "profile_store_unavailable",
                "orphan_profile_baseline",
                "active_profile_not_found",
                "profile_default_preset_not_found",
            }
        ):
            raise ValueError("fallback_no_profile reason is invalid")
    if type(resolved_morph_name_set_id) is not str or not resolved_morph_name_set_id:
        raise ValueError("resolved_morph_name_set_id must be a non-empty string")
    try:
        morph_name_set = get_builtin_morph_name_set(resolved_morph_name_set_id)
    except ValueError as error:
        raise ValueError("resolved_morph_name_set_id must identify a built-in set") from error
    if resolved_morph_name_set_display_name != morph_name_set.display_name:
        raise ValueError("resolved morph name set display name does not match its ID")


class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class _NonFiniteWriterInput(ValueError):
    """Internal marker for fail-closed canonicalization."""

    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(f"Non-finite writer input: {field}")


def _canonicalize(value: object, *, field: str = "value") -> CanonicalValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _NonFiniteWriterInput(field)
        return ("float_hex", value.hex())
    if isinstance(value, (tuple, list)):
        return tuple(
            _canonicalize(item, field=f"{field}[{index}]")
            for index, item in enumerate(value)
        )
    raise ValueError(f"Unsupported canonical value at {field}: {type(value).__name__}")


def _normalize_identity_context(
    context: DiagnosticIdentityContext,
) -> DiagnosticIdentityContext:
    if not isinstance(context, (tuple, list)):
        raise ValueError("identity_context must be a tuple of key/value pairs")
    normalized: list[tuple[str, CanonicalValue]] = []
    seen: set[str] = set()
    for entry in context:
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            raise ValueError("identity_context entries must be (key, value) pairs")
        key, value = entry
        if not isinstance(key, str) or not key:
            raise ValueError("identity_context keys must be non-empty strings")
        if key in seen:
            raise ValueError(f"duplicate identity_context key: {key}")
        seen.add(key)
        normalized.append((key, _canonicalize(value, field=f"identity_context.{key}")))
    return tuple(sorted(normalized, key=lambda entry: entry[0]))


def _normalized_path(path: Path | None) -> str | None:
    if path is None:
        return None
    raw_path = os.fspath(path)
    normalized = os.path.normcase(os.path.normpath(os.path.abspath(raw_path)))
    return normalized.replace("\\", "/")


@dataclass(frozen=True)
class DiagnosticFailureInput:
    code: str
    source_severity: SourceDiagnosticSeverity
    phase: str
    recoverability: DiagnosticRecoverability
    identity_context: DiagnosticIdentityContext = ()
    summary: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("failure code must be a non-empty string")
        if self.source_severity not in _SOURCE_SEVERITIES:
            raise ValueError(f"unsupported source severity: {self.source_severity}")
        if not isinstance(self.phase, str) or not self.phase:
            raise ValueError("failure phase must be a non-empty string")
        if self.recoverability not in _RECOVERABILITIES:
            raise ValueError(f"unsupported recoverability: {self.recoverability}")
        object.__setattr__(
            self,
            "identity_context",
            _normalize_identity_context(self.identity_context),
        )


@dataclass(frozen=True)
class VmdWriterParameters:
    vmd_model_name: str = "AutoLipTool"
    closing_hold_frames: int = 0
    closing_softness_frames: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.vmd_model_name, str) or not self.vmd_model_name.strip():
            raise ValueError("vmd_model_name must be a non-empty string")
        for name, value in (
            ("closing_hold_frames", self.closing_hold_frames),
            ("closing_softness_frames", self.closing_softness_frames),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class EffectiveMorphFrameInput:
    frame_no: int
    morph_name: str
    value: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.frame_no, bool)
            or not isinstance(self.frame_no, int)
            or self.frame_no < 0
        ):
            raise ValueError("frame_no must be a non-negative integer")
        validate_builtin_output_morph_name(self.morph_name)
        _validate_finite_float(self.value, "effective_morph_frame.value")
        object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
class EffectiveTailInput:
    shape_ordinal: int
    vowel: str
    effective_hold_frames: int
    effective_softness_frames: int
    effective_slope_ratio: float
    has_slope_midpoint: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("shape_ordinal", self.shape_ordinal),
            ("effective_hold_frames", self.effective_hold_frames),
            ("effective_softness_frames", self.effective_softness_frames),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.vowel not in SUPPORTED_MORPHS:
            raise ValueError(f"unsupported vowel: {self.vowel!r}")
        _validate_finite_float(
            self.effective_slope_ratio,
            "effective_tail.effective_slope_ratio",
        )
        object.__setattr__(
            self,
            "effective_slope_ratio",
            float(self.effective_slope_ratio),
        )
        if not isinstance(self.has_slope_midpoint, bool):
            raise ValueError("has_slope_midpoint must be bool")


@dataclass(frozen=True)
class EffectiveWriterInput:
    shape_count: int
    morph_frames: tuple[EffectiveMorphFrameInput, ...]
    tails: tuple[EffectiveTailInput, ...]
    allowed_morph_names: tuple[str, ...] = SUPPORTED_MORPHS

    def __post_init__(self) -> None:
        if (
            isinstance(self.shape_count, bool)
            or not isinstance(self.shape_count, int)
            or self.shape_count < 0
        ):
            raise ValueError("shape_count must be a non-negative integer")
        object.__setattr__(self, "morph_frames", tuple(self.morph_frames))
        object.__setattr__(self, "tails", tuple(self.tails))
        normalized_allowed_morph_names = validate_output_morph_names(
            self.allowed_morph_names
        )
        object.__setattr__(
            self,
            "allowed_morph_names",
            normalized_allowed_morph_names,
        )
        if not all(
            isinstance(item, EffectiveMorphFrameInput)
            for item in self.morph_frames
        ):
            raise ValueError("morph_frames must contain EffectiveMorphFrameInput")
        if any(
            item.morph_name not in normalized_allowed_morph_names
            for item in self.morph_frames
        ):
            raise ValueError("morph_frames contain a name outside allowed_morph_names")
        if not all(isinstance(item, EffectiveTailInput) for item in self.tails):
            raise ValueError("tails must contain EffectiveTailInput")
        if any(item.shape_ordinal >= self.shape_count for item in self.tails):
            raise ValueError("tail shape_ordinal must be smaller than shape_count")
        tail_ordinals = tuple(item.shape_ordinal for item in self.tails)
        if len(set(tail_ordinals)) != len(tail_ordinals):
            raise ValueError("tails must not contain duplicate shape_ordinal values")


def _copy_observation(observation: PeakValueObservation) -> PeakValueObservation:
    return replace(
        observation,
        rms_window_times_sec=tuple(observation.rms_window_times_sec),
        rms_window_values=tuple(observation.rms_window_values),
    )


@dataclass(frozen=True)
class DiagnosticTimingPlanInput:
    vowels: tuple[str, ...]
    timeline: tuple[VowelTimelinePoint, ...]
    anchors: tuple[SpeechTimingAnchor, ...]
    source: str
    warning: str | None = None
    observations: tuple[PeakValueObservation, ...] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "vowels", tuple(self.vowels))
        object.__setattr__(self, "timeline", tuple(self.timeline))
        object.__setattr__(self, "anchors", tuple(self.anchors))
        if self.observations is not None:
            object.__setattr__(
                self,
                "observations",
                tuple(_copy_observation(item) for item in self.observations),
            )

    @classmethod
    def from_timing_plan(cls, timing_plan: VowelTimingPlan) -> "DiagnosticTimingPlanInput":
        return cls(
            vowels=tuple(timing_plan.vowels),
            timeline=tuple(timing_plan.timeline),
            anchors=tuple(timing_plan.anchors),
            source=timing_plan.source,
            warning=timing_plan.warning,
            observations=(
                None
                if timing_plan.observations is None
                else tuple(timing_plan.observations)
            ),
        )


@dataclass(frozen=True)
class DiagnosticSnapshotInput:
    input_mode: str
    text_path: Path | None
    text_content_present: bool
    source_audio_path: Path | None
    effective_wav_path: Path | None
    analysis_text_present: bool
    analysis_result_valid: bool
    analysis_pending_rebuild: bool
    timing_plan: DiagnosticTimingPlanInput | None
    existing_vmd_save_ready: bool
    writer_parameters: VmdWriterParameters
    failure: DiagnosticFailureInput | None = None
    analysis_cancelled: bool = False
    effective_writer_input_state: EffectiveWriterInputState = "not_applicable"
    effective_writer_input: EffectiveWriterInput | None = None
    effective_writer_input_failure_reason: str | None = None
    base_plan_identity_digest: str | None = None
    adjustment_present: bool = False
    adjusted_event_count: int = 0
    active_long_vowel_mode: str = "hold"
    active_preset_id: str | None = None
    active_preset_display_name: str | None = None
    effective_long_vowel_hold_run_count: int | None = None
    effective_long_vowel_decay_run_count: int | None = None
    long_vowel_mode_override_count: int = 0
    active_model_profile_id: str | None = None
    active_model_profile_display_name: str | None = None
    active_profile_baseline_preset_id: str | None = None
    baseline_preset_display_name: str | None = None
    model_profile_resolution_status: str = "no_profile"
    model_profile_resolution_reason_code: str | None = None
    resolved_morph_name_set_id: str = JAPANESE_MORPH_NAME_SET_ID
    resolved_morph_name_set_display_name: str = "日本語5母音"
    whisper_summary: WhisperDiagnosticsSummary = WhisperDiagnosticsSummary()
    projection_generation: int = 0
    shared_final_output_identity: object | None = None
    shared_final_output_restrictions: tuple[object, ...] = ()
    shared_final_output_restriction_event_targets: tuple[object, ...] = ()
    transition_summary: TransitionDiagnosticSummary | None = None
    cleanup_summary: object | None = None

    def __post_init__(self) -> None:
        if self.effective_writer_input_state not in _EFFECTIVE_WRITER_INPUT_STATES:
            raise ValueError(
                "effective_writer_input_state must be not_applicable, ready, or invalid"
            )
        if (
            isinstance(self.adjusted_event_count, bool)
            or not isinstance(self.adjusted_event_count, int)
            or self.adjusted_event_count < 0
        ):
            raise ValueError("adjusted_event_count must be a non-negative integer")
        if not isinstance(self.adjustment_present, bool):
            raise ValueError("adjustment_present must be bool")
        _validate_generation_summary_fields(
            active_long_vowel_mode=self.active_long_vowel_mode,
            active_preset_id=self.active_preset_id,
            active_preset_display_name=self.active_preset_display_name,
            effective_long_vowel_hold_run_count=(
                self.effective_long_vowel_hold_run_count
            ),
            effective_long_vowel_decay_run_count=(
                self.effective_long_vowel_decay_run_count
            ),
            long_vowel_mode_override_count=self.long_vowel_mode_override_count,
        )
        _validate_profile_summary_fields(
            active_model_profile_id=self.active_model_profile_id,
            active_model_profile_display_name=self.active_model_profile_display_name,
            active_profile_baseline_preset_id=self.active_profile_baseline_preset_id,
            baseline_preset_display_name=self.baseline_preset_display_name,
            resolution_status=self.model_profile_resolution_status,
            resolution_reason_code=self.model_profile_resolution_reason_code,
            resolved_morph_name_set_id=self.resolved_morph_name_set_id,
            resolved_morph_name_set_display_name=self.resolved_morph_name_set_display_name,
        )
        if self.effective_writer_input is not None and not isinstance(
            self.effective_writer_input,
            EffectiveWriterInput,
        ):
            raise ValueError("effective_writer_input must be EffectiveWriterInput")
        if self.base_plan_identity_digest is not None and (
            not isinstance(self.base_plan_identity_digest, str)
            or not self.base_plan_identity_digest
        ):
            raise ValueError("base_plan_identity_digest must be a non-empty string")
        if self.effective_writer_input_failure_reason is not None and (
            not isinstance(self.effective_writer_input_failure_reason, str)
            or not self.effective_writer_input_failure_reason
        ):
            raise ValueError(
                "effective_writer_input_failure_reason must be a non-empty string"
            )
        if self.shared_final_output_identity is not None and not hasattr(
            self.shared_final_output_identity, "input_identity"
        ):
            raise ValueError("shared_final_output_identity is invalid")
        if self.transition_summary is not None and not isinstance(
            self.transition_summary, TransitionDiagnosticSummary
        ):
            raise ValueError("transition_summary is invalid")
        if self.cleanup_summary is not None and not hasattr(self.cleanup_summary, "summary_digest"):
            raise ValueError("cleanup_summary is invalid")
        object.__setattr__(
            self,
            "shared_final_output_restrictions",
            tuple(self.shared_final_output_restrictions),
        )
        object.__setattr__(
            self,
            "shared_final_output_restriction_event_targets",
            tuple(self.shared_final_output_restriction_event_targets),
        )
        if not isinstance(self.whisper_summary, WhisperDiagnosticsSummary):
            raise ValueError("whisper_summary must be WhisperDiagnosticsSummary")
        if (
            isinstance(self.projection_generation, bool)
            or not isinstance(self.projection_generation, int)
            or self.projection_generation < 0
        ):
            raise ValueError("projection_generation must be a non-negative integer")


@dataclass(frozen=True)
class InputDiagnosticsSummary:
    input_mode: str
    normalized_text_path: str | None
    normalized_source_audio_path: str | None
    normalized_effective_wav_path: str | None
    text_content_present: bool
    analysis_text_present: bool


@dataclass(frozen=True)
class AnalysisDiagnosticsSummary:
    analysis_result_valid: bool
    analysis_pending_rebuild: bool
    timing_source: str | None
    anchor_count: int
    event_count: int
    max_frame: int | None
    timing_warning_present: bool
    observation_fallback_count: int


@dataclass(frozen=True)
class GenerationDiagnosticsSummary:
    vmd_model_name: str
    closing_hold_frames: int
    closing_softness_frames: int
    fingerprint_schema_version: str
    active_long_vowel_mode: str = "hold"
    active_preset_id: str | None = None
    active_preset_display_name: str | None = None
    effective_long_vowel_hold_run_count: int | None = None
    effective_long_vowel_decay_run_count: int | None = None
    active_model_profile_id: str | None = None
    active_model_profile_display_name: str | None = None
    active_profile_baseline_preset_id: str | None = None
    baseline_preset_display_name: str | None = None
    model_profile_resolution_status: str = "no_profile"
    model_profile_resolution_reason_code: str | None = None
    resolved_morph_name_set_id: str = JAPANESE_MORPH_NAME_SET_ID
    resolved_morph_name_set_display_name: str = "日本語5母音"

    def __post_init__(self) -> None:
        if not isinstance(self.vmd_model_name, str) or not self.vmd_model_name:
            raise ValueError("vmd_model_name must be a non-empty string")
        for name, value in (
            ("closing_hold_frames", self.closing_hold_frames),
            ("closing_softness_frames", self.closing_softness_frames),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.fingerprint_schema_version, str) or not self.fingerprint_schema_version:
            raise ValueError("fingerprint_schema_version must be a non-empty string")
        _validate_generation_summary_fields(
            active_long_vowel_mode=self.active_long_vowel_mode,
            active_preset_id=self.active_preset_id,
            active_preset_display_name=self.active_preset_display_name,
            effective_long_vowel_hold_run_count=(
                self.effective_long_vowel_hold_run_count
            ),
            effective_long_vowel_decay_run_count=(
                self.effective_long_vowel_decay_run_count
            ),
            long_vowel_mode_override_count=0,
        )
        _validate_profile_summary_fields(
            active_model_profile_id=self.active_model_profile_id,
            active_model_profile_display_name=self.active_model_profile_display_name,
            active_profile_baseline_preset_id=self.active_profile_baseline_preset_id,
            baseline_preset_display_name=self.baseline_preset_display_name,
            resolution_status=self.model_profile_resolution_status,
            resolution_reason_code=self.model_profile_resolution_reason_code,
            resolved_morph_name_set_id=self.resolved_morph_name_set_id,
            resolved_morph_name_set_display_name=self.resolved_morph_name_set_display_name,
        )


@dataclass(frozen=True)
class AdjustmentDiagnosticsSummary:
    base_plan_identity_digest: str | None = None
    adjustment_present: bool = False
    adjusted_event_count: int = 0
    effective_shape_count: int | None = None
    effective_morph_frame_count: int | None = None
    long_vowel_mode_override_count: int = 0

    def __post_init__(self) -> None:
        if self.base_plan_identity_digest is not None and (
            type(self.base_plan_identity_digest) is not str
            or not self.base_plan_identity_digest
        ):
            raise ValueError("base_plan_identity_digest must be None or non-empty string")
        if not isinstance(self.adjustment_present, bool):
            raise ValueError("adjustment_present must be bool")
        for name, value in (
            ("adjusted_event_count", self.adjusted_event_count),
            ("long_vowel_mode_override_count", self.long_vowel_mode_override_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name, value in (
            ("effective_shape_count", self.effective_shape_count),
            ("effective_morph_frame_count", self.effective_morph_frame_count),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{name} must be None or a non-negative integer")


@dataclass(frozen=True)
class SaveabilitySummary:
    vmd_save_allowed: bool
    blocking_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocking_codes", tuple(self.blocking_codes))
        object.__setattr__(self, "warning_codes", tuple(self.warning_codes))


@dataclass(frozen=True)
class DiagnosticItem:
    code: str
    severity: DiagnosticSeverity
    phase: str
    identity_context: DiagnosticIdentityContext = ()
    summary: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("diagnostic code must be a non-empty string")
        if not isinstance(self.severity, DiagnosticSeverity):
            raise ValueError("severity must be DiagnosticSeverity")
        if not isinstance(self.phase, str) or not self.phase:
            raise ValueError("diagnostic phase must be a non-empty string")
        object.__setattr__(
            self,
            "identity_context",
            _normalize_identity_context(self.identity_context),
        )


@dataclass(frozen=True)
class OutputDiagnosticsSnapshot:
    input_summary: InputDiagnosticsSummary
    analysis_summary: AnalysisDiagnosticsSummary
    generation_summary: GenerationDiagnosticsSummary
    saveability: SaveabilitySummary
    items: tuple[DiagnosticItem, ...]
    fingerprint_payload: FingerprintPayload | None
    save_state_fingerprint: str | None
    adjustment_summary: AdjustmentDiagnosticsSummary = AdjustmentDiagnosticsSummary()
    whisper_summary: WhisperDiagnosticsSummary = WhisperDiagnosticsSummary()
    projection_generation: int = 0
    shared_final_output_identity: object | None = None
    shared_final_output_restrictions: tuple[object, ...] = ()
    shared_final_output_restriction_event_targets: tuple[object, ...] = ()
    transition_summary: TransitionDiagnosticSummary | None = None
    cleanup_summary: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        if self.fingerprint_payload is not None:
            object.__setattr__(self, "fingerprint_payload", tuple(self.fingerprint_payload))
        if not isinstance(self.whisper_summary, WhisperDiagnosticsSummary):
            raise ValueError("whisper_summary must be WhisperDiagnosticsSummary")
        if self.transition_summary is not None and not isinstance(
            self.transition_summary, TransitionDiagnosticSummary
        ):
            raise ValueError("transition_summary is invalid")
        if self.cleanup_summary is not None and not hasattr(self.cleanup_summary, "summary_digest"):
            raise ValueError("cleanup_summary is invalid")
        object.__setattr__(
            self,
            "shared_final_output_restrictions",
            tuple(self.shared_final_output_restrictions),
        )
        object.__setattr__(
            self,
            "shared_final_output_restriction_event_targets",
            tuple(self.shared_final_output_restriction_event_targets),
        )
        if (
            isinstance(self.projection_generation, bool)
            or not isinstance(self.projection_generation, int)
            or self.projection_generation < 0
        ):
            raise ValueError("projection_generation must be a non-negative integer")


_CODE_ORDER = (
    "analysis_rebuild_required",
    "analysis_not_ready",
    "timing_plan_empty",
    "text_input_missing",
    "voice_only_text_missing",
    "audio_input_missing",
    "analysis_failure",
    "effective_writer_input_unavailable",
    "timing_fallback_used",
    "observation_fallback_used",
    "analysis_cancelled",
    "analysis_ready",
    "vmd_save_ready",
)
_CODE_RANK = {code: index for index, code in enumerate(_CODE_ORDER)}

_SUMMARY = {
    "analysis_not_ready": "解析結果がありません。",
    "analysis_rebuild_required": "入力または設定の変更後に再解析が必要です。",
    "timing_plan_empty": "有効な母音イベントがありません。",
    "text_input_missing": "TEXT入力を確認してください。",
    "voice_only_text_missing": "音声のみ解析の書き起こしがありません。",
    "audio_input_missing": "解析用音声を確認してください。",
    "analysis_failure": "解析結果をVMD保存に使用できません。",
    "effective_writer_input_unavailable": "補正後のVMD生成データを準備できません。",
    "timing_fallback_used": "タイミング解析でfallbackを使用しました。",
    "observation_fallback_used": "一部イベントの音量評価でfallbackを使用しました。",
    "analysis_cancelled": "解析はキャンセルされました。",
    "analysis_ready": "解析結果を利用できます。",
    "vmd_save_ready": "VMDを保存できます。",
}


def _validate_timing_plan(plan: DiagnosticTimingPlanInput) -> None:
    if not isinstance(plan.source, str) or not plan.source:
        raise ValueError("timing source must be a non-empty string")
    if plan.warning is not None and not isinstance(plan.warning, str):
        raise ValueError("timing warning must be a string or None")
    if len(plan.vowels) != len(plan.timeline):
        raise ValueError("vowels and timeline must have the same length")
    for index, vowel in enumerate(plan.vowels):
        if not isinstance(vowel, str) or vowel not in SUPPORTED_MORPHS:
            raise ValueError(f"unsupported vowel morph at index {index}: {vowel!r}")
    for index, point in enumerate(plan.timeline):
        if not isinstance(point, VowelTimelinePoint):
            raise ValueError(f"timeline[{index}] must be VowelTimelinePoint")
        _validate_finite_float(point.time_sec, f"timeline[{index}].time_sec")
        _validate_finite_float(point.value, f"timeline[{index}].value")
        _validate_finite_float(point.peak_value, f"timeline[{index}].peak_value")
        _validate_finite_float(point.duration_sec, f"timeline[{index}].duration_sec")
        _validate_finite_float(point.start_sec, f"timeline[{index}].start_sec")
        _validate_finite_float(point.end_sec, f"timeline[{index}].end_sec")
        if point.time_sec < 0 or point.value < 0 or point.peak_value < 0:
            raise ValueError(f"timeline[{index}] contains a negative writer value")
        if point.duration_sec < 0 or point.start_sec > point.end_sec:
            raise ValueError(f"timeline[{index}] has an invalid interval")
        if not point.start_sec <= point.time_sec <= point.end_sec:
            raise ValueError(f"timeline[{index}].time_sec is outside its interval")
    for index, anchor in enumerate(plan.anchors):
        if not isinstance(anchor, SpeechTimingAnchor):
            raise ValueError(f"anchors[{index}] must be SpeechTimingAnchor")
        _validate_finite_float(anchor.start_sec, f"anchors[{index}].start_sec")
        _validate_finite_float(anchor.end_sec, f"anchors[{index}].end_sec")
        if anchor.start_sec > anchor.end_sec:
            raise ValueError(f"anchors[{index}] has an invalid interval")
    if plan.observations is not None:
        for index, observation in enumerate(plan.observations):
            _validate_observation(observation, index)


def _validate_finite_float(value: object, field: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    if isinstance(value, float) and not math.isfinite(value):
        raise _NonFiniteWriterInput(field)


def _validate_observation(observation: PeakValueObservation, index: int) -> None:
    if not isinstance(observation, PeakValueObservation):
        raise ValueError(f"observations[{index}] must be PeakValueObservation")
    if isinstance(observation.event_index, bool) or not isinstance(observation.event_index, int):
        raise ValueError(f"observations[{index}].event_index must be an integer")
    if observation.event_index < 0:
        raise ValueError(f"observations[{index}].event_index must be non-negative")
    if observation.vowel not in SUPPORTED_MORPHS:
        raise ValueError(f"observations[{index}] has an unsupported vowel morph")
    if isinstance(observation.window_sample_count, bool) or not isinstance(
        observation.window_sample_count,
        int,
    ) or observation.window_sample_count < 0:
        raise ValueError(f"observations[{index}].window_sample_count must be non-negative")
    float_fields = (
        "time_sec",
        "initial_interval_start_sec",
        "initial_interval_end_sec",
        "refined_interval_start_sec",
        "refined_interval_end_sec",
        "peak_window_start_sec",
        "peak_window_end_sec",
        "peak_value",
    )
    for name in float_fields:
        _validate_finite_float(getattr(observation, name), f"observations[{index}].{name}")
    for name, values in (
        ("rms_window_times_sec", observation.rms_window_times_sec),
        ("rms_window_values", observation.rms_window_values),
    ):
        for value_index, value in enumerate(values):
            _validate_finite_float(
                value,
                f"observations[{index}].{name}[{value_index}]",
            )
    evaluation = observation.evaluation
    if not isinstance(evaluation, PeakValueEvaluation):
        raise ValueError(f"observations[{index}].evaluation must be PeakValueEvaluation")
    for name in (
        "interval_start_sec",
        "interval_end_sec",
        "peak_window_start_sec",
        "peak_window_end_sec",
        "peak_value",
    ):
        _validate_finite_float(
            getattr(evaluation, name),
            f"observations[{index}].evaluation.{name}",
        )
    if evaluation.local_peak is not None:
        _validate_finite_float(
            evaluation.local_peak,
            f"observations[{index}].evaluation.local_peak",
        )
    if observation.local_peak is not None:
        _validate_finite_float(observation.local_peak, f"observations[{index}].local_peak")
    if observation.global_peak is not None:
        _validate_finite_float(observation.global_peak, f"observations[{index}].global_peak")
    for name in (
        "is_bridgeable_same_vowel_micro_gap_candidate",
        "is_same_vowel_burst_candidate",
        "is_bridgeable_cross_vowel_transition_candidate",
        "is_cross_vowel_zero_run_continuity_floor_candidate",
        "is_bridgeable_micro_gap_candidate",
    ):
        if not isinstance(getattr(observation, name), bool):
            raise ValueError(f"observations[{index}].{name} must be bool")
    for name in (
        "previous_non_zero_event_index",
        "next_non_zero_event_index",
        "span_start_index",
        "span_end_index",
    ):
        value = getattr(observation, name)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"observations[{index}].{name} must be a non-negative integer or None")


def _failure_identity(failure: DiagnosticFailureInput) -> tuple[CanonicalValue, ...]:
    return (
        failure.code,
        failure.source_severity,
        failure.phase,
        failure.recoverability,
        failure.identity_context,
    )


def _failure_sort_key(failure: DiagnosticFailureInput) -> tuple[object, ...]:
    return (
        failure.code,
        failure.phase,
        failure.recoverability,
        failure.source_severity,
        failure.identity_context,
    )


def _make_item(
    code: str,
    severity: DiagnosticSeverity,
    phase: str,
    context: DiagnosticIdentityContext = (),
    detail: str = "",
) -> DiagnosticItem:
    return DiagnosticItem(
        code=code,
        severity=severity,
        phase=phase,
        identity_context=context,
        summary=_SUMMARY[code],
        detail=detail,
    )


def _build_failure_items(
    failures: list[DiagnosticFailureInput],
) -> DiagnosticItem | None:
    if not failures:
        return None
    ordered = tuple(sorted(failures, key=_failure_sort_key))
    context = (("failures", tuple(_failure_identity(failure) for failure in ordered)),)
    summaries = tuple(failure.summary or failure.code for failure in ordered)
    details = tuple(
        failure.detail or failure.code
        for failure in ordered
    )
    return DiagnosticItem(
        code="analysis_failure",
        severity=DiagnosticSeverity.ERROR,
        phase="pipeline_build",
        identity_context=context,
        summary=" / ".join(summaries),
        detail="\n".join(details),
    )


def _timeline_canonical(plan: DiagnosticTimingPlanInput) -> CanonicalValue:
    return tuple(
        (
            ("event_index", index),
            ("time_sec", _canonicalize(point.time_sec, field=f"timeline[{index}].time_sec")),
            ("vowel", point.vowel),
            ("value", _canonicalize(point.value, field=f"timeline[{index}].value")),
            (
                "duration_sec",
                _canonicalize(point.duration_sec, field=f"timeline[{index}].duration_sec"),
            ),
            ("start_sec", _canonicalize(point.start_sec, field=f"timeline[{index}].start_sec")),
            ("end_sec", _canonicalize(point.end_sec, field=f"timeline[{index}].end_sec")),
            (
                "peak_value",
                _canonicalize(point.peak_value, field=f"timeline[{index}].peak_value"),
            ),
        )
        for index, point in enumerate(plan.timeline)
    )


def _evaluation_canonical(
    evaluation: PeakValueEvaluation,
    *,
    field: str,
) -> CanonicalValue:
    return (
        ("interval_start_sec", _canonicalize(evaluation.interval_start_sec, field=f"{field}.interval_start_sec")),
        ("interval_end_sec", _canonicalize(evaluation.interval_end_sec, field=f"{field}.interval_end_sec")),
        ("peak_window_start_sec", _canonicalize(evaluation.peak_window_start_sec, field=f"{field}.peak_window_start_sec")),
        ("peak_window_end_sec", _canonicalize(evaluation.peak_window_end_sec, field=f"{field}.peak_window_end_sec")),
        ("local_peak", _canonicalize(evaluation.local_peak, field=f"{field}.local_peak")),
        ("peak_value", _canonicalize(evaluation.peak_value, field=f"{field}.peak_value")),
        ("reason", evaluation.reason),
    )


def _observations_canonical(
    observations: tuple[PeakValueObservation, ...] | None,
) -> tuple[CanonicalValue, CanonicalValue]:
    if observations is None:
        return "none", None
    result: list[CanonicalValue] = []
    for index, observation in enumerate(observations):
        field = f"observations[{index}]"
        result.append(
            (
                ("event_index", observation.event_index),
                ("vowel", observation.vowel),
                ("time_sec", _canonicalize(observation.time_sec, field=f"{field}.time_sec")),
                ("initial_interval_start_sec", _canonicalize(observation.initial_interval_start_sec, field=f"{field}.initial_interval_start_sec")),
                ("initial_interval_end_sec", _canonicalize(observation.initial_interval_end_sec, field=f"{field}.initial_interval_end_sec")),
                ("refined_interval_start_sec", _canonicalize(observation.refined_interval_start_sec, field=f"{field}.refined_interval_start_sec")),
                ("refined_interval_end_sec", _canonicalize(observation.refined_interval_end_sec, field=f"{field}.refined_interval_end_sec")),
                ("peak_window_start_sec", _canonicalize(observation.peak_window_start_sec, field=f"{field}.peak_window_start_sec")),
                ("peak_window_end_sec", _canonicalize(observation.peak_window_end_sec, field=f"{field}.peak_window_end_sec")),
                ("local_peak", _canonicalize(observation.local_peak, field=f"{field}.local_peak")),
                ("global_peak", _canonicalize(observation.global_peak, field=f"{field}.global_peak")),
                ("peak_value", _canonicalize(observation.peak_value, field=f"{field}.peak_value")),
                ("reason", observation.reason),
                ("fallback_reason", observation.fallback_reason),
                ("window_sample_count", observation.window_sample_count),
                ("evaluation", _evaluation_canonical(observation.evaluation, field=f"{field}.evaluation")),
                ("rms_window_times_sec", _canonicalize(observation.rms_window_times_sec, field=f"{field}.rms_window_times_sec")),
                ("rms_window_values", _canonicalize(observation.rms_window_values, field=f"{field}.rms_window_values")),
                ("is_bridgeable_same_vowel_micro_gap_candidate", observation.is_bridgeable_same_vowel_micro_gap_candidate),
                ("is_same_vowel_burst_candidate", observation.is_same_vowel_burst_candidate),
                ("is_bridgeable_cross_vowel_transition_candidate", observation.is_bridgeable_cross_vowel_transition_candidate),
                ("is_cross_vowel_zero_run_continuity_floor_candidate", observation.is_cross_vowel_zero_run_continuity_floor_candidate),
                ("is_bridgeable_micro_gap_candidate", observation.is_bridgeable_micro_gap_candidate),
                ("bridge_candidate_reason", observation.bridge_candidate_reason),
                ("previous_non_zero_event_index", observation.previous_non_zero_event_index),
                ("next_non_zero_event_index", observation.next_non_zero_event_index),
                ("span_start_index", observation.span_start_index),
                ("span_end_index", observation.span_end_index),
                ("full_span_start_frame", observation.full_span_start_frame),
                ("full_span_end_frame", observation.full_span_end_frame),
                (
                    "silence_core_frame_ranges",
                    _canonicalize(
                        observation.silence_core_frame_ranges,
                        field=f"{field}.silence_core_frame_ranges",
                    ),
                ),
                (
                    "boundary_fringe_frame_ranges",
                    _canonicalize(
                        observation.boundary_fringe_frame_ranges,
                        field=f"{field}.boundary_fringe_frame_ranges",
                    ),
                ),
                ("silence_core_overlap", observation.silence_core_overlap),
                ("coverage_status", observation.coverage_status),
                ("provenance_status", observation.provenance_status),
                ("bridge_rejection_reason_code", observation.bridge_rejection_reason_code),
                (
                    "base_event_silence_core_overlap",
                    observation.base_event_silence_core_overlap,
                ),
                (
                    "positive_core_frame_ranges",
                    _canonicalize(
                        observation.positive_core_frame_ranges,
                        field=f"{field}.positive_core_frame_ranges",
                    ),
                ),
                ("long_vowel_role", observation.long_vowel_role),
                ("manual_adjustment_applied", observation.manual_adjustment_applied),
                (
                    "base_event_rejection_reason_code",
                    observation.base_event_rejection_reason_code,
                ),
                ("boundary_only", observation.boundary_only),
                ("boundary_frame", observation.boundary_frame),
                ("boundary_point_kind", observation.boundary_point_kind),
            )
        )
    return "present", tuple(result)


def build_save_state_fingerprint_payload(
    snapshot_input: DiagnosticSnapshotInput,
    items: tuple[DiagnosticItem, ...],
) -> FingerprintPayload:
    """Build the canonical identity of the effective VMD writer input."""
    if snapshot_input.input_mode not in _INPUT_MODES:
        raise ValueError(f"unsupported input_mode: {snapshot_input.input_mode}")
    effective_state = snapshot_input.effective_writer_input_state
    effective_input = snapshot_input.effective_writer_input
    if effective_state == "invalid":
        raise ValueError("invalid effective writer input cannot be fingerprinted")
    if effective_state == "ready" and effective_input is None:
        raise ValueError("ready effective writer input is missing")

    morph_frames: CanonicalValue = ()
    effective_tails: CanonicalValue = ()
    if effective_state == "ready" and effective_input is not None:
        morph_frames = tuple(
            (
                ("frame_no", frame.frame_no),
                ("morph_name", frame.morph_name),
                (
                    "value",
                    _canonicalize(
                        frame.value,
                        field=f"effective_morph_frames[{index}].value",
                    ),
                ),
            )
            for index, frame in enumerate(effective_input.morph_frames)
        )
        effective_tails = tuple(
            (
                ("shape_ordinal", tail.shape_ordinal),
                ("vowel", tail.vowel),
                ("effective_hold_frames", tail.effective_hold_frames),
                ("effective_softness_frames", tail.effective_softness_frames),
                (
                    "effective_slope_ratio",
                    _canonicalize(
                        tail.effective_slope_ratio,
                        field=f"effective_tails[{index}].effective_slope_ratio",
                    ),
                ),
                ("has_slope_midpoint", tail.has_slope_midpoint),
            )
            for index, tail in enumerate(effective_input.tails)
        )

    writer_parameters = snapshot_input.writer_parameters
    diagnostic_identities = tuple(
        (
            item.severity.value,
            item.code,
            item.phase,
            item.identity_context,
        )
        for item in sorted(items, key=lambda item: (_severity_rank(item.severity), _CODE_RANK.get(item.code, len(_CODE_ORDER))))
    )
    return (
        ("schema_version", _FINGERPRINT_SCHEMA_VERSION),
        ("input_mode", snapshot_input.input_mode),
        ("normalized_text_path", _normalized_path(snapshot_input.text_path)),
        ("normalized_effective_wav_path", _normalized_path(snapshot_input.effective_wav_path)),
        ("effective_writer_input_state", effective_state),
        ("vmd_model_name", writer_parameters.vmd_model_name),
        ("effective_morph_frames", morph_frames),
        ("effective_tails", effective_tails),
        ("diagnostic_identities", diagnostic_identities),
    )


def build_shared_final_output_fingerprint_payload(
    snapshot_input: DiagnosticSnapshotInput,
    items: tuple[DiagnosticItem, ...],
) -> FingerprintPayload:
    """Build the B3 fingerprint without changing the legacy payload schema."""
    identity = snapshot_input.shared_final_output_identity
    if identity is None:
        raise ValueError("shared final-output identity is required")
    input_identity = getattr(identity, "input_identity", None)
    if input_identity is None:
        raise ValueError("shared final-output input identity is missing")
    if snapshot_input.input_mode != getattr(input_identity, "input_mode", None):
        raise ValueError("diagnostics input mode differs from final-output identity")
    normalized_text_path = _normalized_path(snapshot_input.text_path)
    identity_text_path = getattr(input_identity, "normalized_text_path", None)
    normalized_identity_text_path = (
        None
        if identity_text_path is None
        else _normalized_path(Path(identity_text_path))
    )
    if normalized_text_path != normalized_identity_text_path:
        raise ValueError("diagnostics text path differs from final-output identity")
    diagnostic_identities = tuple(
        (
            item.severity.value,
            item.code,
            item.phase,
            item.identity_context,
        )
        for item in sorted(
            items,
            key=lambda item: (
                _severity_rank(item.severity),
                _CODE_RANK.get(item.code, len(_CODE_ORDER)),
            ),
        )
    )
    output_mapping = tuple(getattr(input_identity, "output_mapping", ()))
    plan_schema_id = getattr(identity, "plan_schema_id", None)
    semantic_digest = getattr(identity, "semantic_digest", None)
    wire_digest = getattr(identity, "wire_digest", None)
    curve_policy_id = getattr(identity, "curve_policy_id", None)
    for field_name, value in (
        ("plan_schema_id", plan_schema_id),
        ("final_curve_policy_id", curve_policy_id),
        ("final_semantic_digest", semantic_digest),
        ("final_wire_digest", wire_digest),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is missing")
    if not output_mapping:
        raise ValueError("final output mapping is missing")
    payload = (
        ("schema_version", _SHARED_FINAL_OUTPUT_FINGERPRINT_SCHEMA_VERSION),
        ("input_mode", snapshot_input.input_mode),
        ("normalized_text_path", normalized_text_path),
        (
            "normalized_effective_wav_path",
            _normalized_path(snapshot_input.effective_wav_path),
        ),
        ("vmd_model_name", snapshot_input.writer_parameters.vmd_model_name),
        ("final_plan_schema_id", plan_schema_id),
        ("final_curve_policy_id", curve_policy_id),
        ("final_semantic_digest", semantic_digest),
        ("final_wire_digest", wire_digest),
        ("output_mapping", output_mapping),
        ("diagnostic_identities", diagnostic_identities),
    )
    if snapshot_input.transition_summary is not None:
        payload += (("transition_summary_digest", snapshot_input.transition_summary.summary_digest),)
    cleanup_summary = snapshot_input.cleanup_summary
    if getattr(input_identity, "cleanup_input_digest", None) is None:
        if cleanup_summary is not None:
            raise ValueError("cleanup summary has no cleanup identity")
    else:
        if (
            cleanup_summary is None
            or getattr(cleanup_summary, "final_binding", None) != identity.binding_digest
        ):
            raise ValueError("cleanup summary differs from final-output identity")
        payload += (("cleanup_summary_digest", cleanup_summary.summary_digest),)
    return payload


def compute_save_state_fingerprint(payload: FingerprintPayload) -> str:
    _assert_canonical_value(payload, field="payload")
    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical_json).hexdigest()}"


def shared_warning_confirmation_matches(
    snapshot: OutputDiagnosticsSnapshot,
    confirmed_fingerprint: str | None,
) -> bool:
    """Compare B3 warning confirmation without reading or mutating legacy state."""
    if (
        not isinstance(snapshot, OutputDiagnosticsSnapshot)
        or snapshot.shared_final_output_identity is None
        or snapshot.save_state_fingerprint is None
        or snapshot.saveability.blocking_codes
        or not snapshot.analysis_summary.analysis_result_valid
        or snapshot.analysis_summary.analysis_pending_rebuild
    ):
        return False
    if not snapshot.saveability.warning_codes:
        return True
    return confirmed_fingerprint == snapshot.save_state_fingerprint


def _assert_canonical_value(value: object, *, field: str) -> None:
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        raise ValueError(f"raw float is not allowed in canonical payload: {field}")
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _assert_canonical_value(item, field=f"{field}[{index}]")
        return
    raise ValueError(f"unsupported canonical payload value at {field}")


def _severity_rank(severity: DiagnosticSeverity) -> int:
    return {
        DiagnosticSeverity.ERROR: 0,
        DiagnosticSeverity.WARNING: 1,
        DiagnosticSeverity.INFO: 2,
    }[severity]


def evaluate_whisper_identity_status(
    left_model_key: str | None,
    left_manifest_identity: str | None,
    right_model_key: str | None,
    right_manifest_identity: str | None,
    *,
    unloaded_is_distinct: bool = False,
) -> str:
    """Compare two model identities without treating a missing value as success."""
    left_empty = left_model_key is None and left_manifest_identity is None
    right_empty = right_model_key is None and right_manifest_identity is None
    if unloaded_is_distinct and right_empty:
        return "unloaded"
    if left_empty and right_empty:
        return "not_applicable"
    if (
        left_model_key is None
        or left_manifest_identity is None
        or right_model_key is None
        or right_manifest_identity is None
    ):
        return "incomplete"
    if (
        left_model_key == right_model_key
        and left_manifest_identity == right_manifest_identity
    ):
        return "consistent"
    return "mismatch"


def _whisper_failure_from_summary(
    summary: WhisperDiagnosticsSummary,
) -> DiagnosticFailureInput | None:
    if summary.failure_class == "none":
        return None
    code = summary.failure_detail_code or summary.failure_class
    safe_notice = summary.safe_failure_notice or "Whisper解析を完了できませんでした。"
    recoverability = summary.recoverability
    if recoverability not in _RECOVERABILITIES:
        recoverability = "retry_possible"
    source_severity: SourceDiagnosticSeverity = (
        "cancelled" if summary.failure_class == "cancelled" else "error"
    )
    return DiagnosticFailureInput(
        code=code,
        source_severity=source_severity,
        phase="whisper_model_runtime",
        recoverability=recoverability,  # type: ignore[arg-type]
        identity_context=(
            ("failure_class", summary.failure_class),
            ("detail_code", code),
        ),
        summary=safe_notice,
        detail=safe_notice,
    )


def build_output_diagnostics_snapshot(
    snapshot_input: DiagnosticSnapshotInput,
) -> OutputDiagnosticsSnapshot:
    if snapshot_input.input_mode not in _INPUT_MODES:
        raise ValueError(f"unsupported input_mode: {snapshot_input.input_mode}")
    if not isinstance(snapshot_input.writer_parameters, VmdWriterParameters):
        raise ValueError("writer_parameters must be VmdWriterParameters")
    plan = snapshot_input.timing_plan
    nonfinite_failure: DiagnosticFailureInput | None = None
    if plan is not None:
        try:
            _validate_timing_plan(plan)
        except _NonFiniteWriterInput as error:
            nonfinite_failure = DiagnosticFailureInput(
                code="writer_input_non_finite",
                source_severity="error",
                phase="vmd_write",
                recoverability="cannot_continue",
                identity_context=(("field", error.field),),
                summary="VMD writer入力に非有限値があります。",
            )

    failures: list[DiagnosticFailureInput] = []
    if snapshot_input.failure is not None:
        failures.append(snapshot_input.failure)
    summary_failure = _whisper_failure_from_summary(snapshot_input.whisper_summary)
    if summary_failure is not None and snapshot_input.failure is None:
        failures.append(summary_failure)
    if nonfinite_failure is not None:
        failures.append(nonfinite_failure)

    plan_is_valid = (
        snapshot_input.analysis_result_valid
        and plan is not None
        and nonfinite_failure is None
    )
    has_derived_error = snapshot_input.analysis_pending_rebuild or (
        not snapshot_input.analysis_pending_rebuild and not plan_is_valid
    )
    if not has_derived_error and plan_is_valid and not plan.timeline:
        has_derived_error = True
    if not failures and not snapshot_input.existing_vmd_save_ready and not has_derived_error:
        failures.append(
            DiagnosticFailureInput(
                code="legacy_save_contract_unsatisfied",
                source_severity="error",
                phase="vmd_write",
                recoverability="cannot_continue",
                identity_context=(("existing_vmd_save_ready", False),),
                summary="既存のVMD保存契約が成立していません。",
            )
        )

    items: list[DiagnosticItem] = []
    if snapshot_input.analysis_pending_rebuild:
        items.append(
            _make_item(
                "analysis_rebuild_required",
                DiagnosticSeverity.ERROR,
                "pipeline_build",
                (("pending_rebuild", True),),
            )
        )
    elif snapshot_input.whisper_summary.analysis_identity_status in {
        "incomplete",
        "mismatch",
    }:
        items.append(
            _make_item(
                "analysis_rebuild_required",
                DiagnosticSeverity.ERROR,
                "whisper_identity",
                (
                    (
                        "analysis_identity_status",
                        snapshot_input.whisper_summary.analysis_identity_status,
                    ),
                ),
            )
        )
    elif not plan_is_valid and nonfinite_failure is None:
        items.append(
            _make_item(
                "analysis_not_ready",
                DiagnosticSeverity.ERROR,
                "pipeline_build",
                (
                    ("analysis_result_valid", snapshot_input.analysis_result_valid),
                    ("plan_present", plan is not None),
                ),
            )
        )
    elif plan is not None and not plan.timeline:
        items.append(
            _make_item(
                "timing_plan_empty",
                DiagnosticSeverity.ERROR,
                "pipeline_build",
                (("event_count", 0),),
            )
        )

    if snapshot_input.input_mode == "text_audio" and snapshot_input.text_path is None:
        items.append(
            _make_item(
                "text_input_missing",
                DiagnosticSeverity.ERROR,
                "text_validate",
                (("path_present", False),),
            )
        )
    if snapshot_input.input_mode == "voice_only" and not snapshot_input.analysis_text_present:
        items.append(
            _make_item(
                "voice_only_text_missing",
                DiagnosticSeverity.ERROR,
                "pipeline_build",
                (("analysis_text_present", False),),
            )
        )
    if snapshot_input.effective_wav_path is None:
        items.append(
            _make_item(
                "audio_input_missing",
                DiagnosticSeverity.ERROR,
                "analysis_wav_validate",
                (("path_present", False),),
            )
        )

    failure_item = _build_failure_items(failures)
    if failure_item is not None:
        items.append(failure_item)
    effective_writer_input_invalid = (
        snapshot_input.effective_writer_input_state == "invalid"
        or (
            snapshot_input.effective_writer_input_state == "ready"
            and snapshot_input.effective_writer_input is None
        )
    )
    if effective_writer_input_invalid:
        reason = (
            snapshot_input.effective_writer_input_failure_reason
            or "ready_input_missing"
        )
        items.append(
            _make_item(
                "effective_writer_input_unavailable",
                DiagnosticSeverity.ERROR,
                "vmd_write",
                (("reason", reason),),
            )
        )

    if plan is not None and plan_is_valid:
        if plan.source == "even_fallback" or plan.warning is not None:
            reason = "even_fallback" if plan.source == "even_fallback" else "timing_warning"
            items.append(
                _make_item(
                    "timing_fallback_used",
                    DiagnosticSeverity.WARNING,
                    "pipeline_build",
                    (("reason", reason), ("source", plan.source)),
                )
            )
        fallback_entries = tuple(
            sorted(
                (
                    (observation.event_index, observation.fallback_reason)
                    for observation in (plan.observations or ())
                    if observation.fallback_reason
                ),
                key=lambda entry: (entry[0], entry[1]),
            )
        )
        if fallback_entries:
            items.append(
                _make_item(
                    "observation_fallback_used",
                    DiagnosticSeverity.WARNING,
                    "pipeline_build",
                    (("fallbacks", fallback_entries),),
                )
            )

    has_error = any(item.severity is DiagnosticSeverity.ERROR for item in items)
    if not has_error and snapshot_input.analysis_cancelled:
        items.append(
            _make_item(
                "analysis_cancelled",
                DiagnosticSeverity.INFO,
                "pipeline_build",
                (("reason", "cancelled_by_user"),),
            )
        )
    if not has_error and plan_is_valid and plan is not None and plan.timeline:
        items.append(
            _make_item(
                "analysis_ready",
                DiagnosticSeverity.INFO,
                "pipeline_build",
                (("ready", True),),
            )
        )
    if not has_error and snapshot_input.existing_vmd_save_ready:
        items.append(
            _make_item(
                "vmd_save_ready",
                DiagnosticSeverity.INFO,
                "vmd_write",
                (("ready", True),),
            )
        )

    items.sort(key=lambda item: (_severity_rank(item.severity), _CODE_RANK.get(item.code, len(_CODE_ORDER))))
    items_tuple = tuple(items)
    input_summary = InputDiagnosticsSummary(
        input_mode=snapshot_input.input_mode,
        normalized_text_path=_normalized_path(snapshot_input.text_path),
        normalized_source_audio_path=_normalized_path(snapshot_input.source_audio_path),
        normalized_effective_wav_path=_normalized_path(snapshot_input.effective_wav_path),
        text_content_present=snapshot_input.text_content_present,
        analysis_text_present=snapshot_input.analysis_text_present,
    )
    analysis_summary = AnalysisDiagnosticsSummary(
        analysis_result_valid=snapshot_input.analysis_result_valid,
        analysis_pending_rebuild=snapshot_input.analysis_pending_rebuild,
        timing_source=None if plan is None else plan.source,
        anchor_count=0 if plan is None else len(plan.anchors),
        event_count=0 if plan is None else len(plan.timeline),
        max_frame=(
            None
            if plan is None or not plan.timeline or nonfinite_failure is not None
            else max(round(point.end_sec * VMD_FPS) for point in plan.timeline)
        ),
        timing_warning_present=plan is not None and plan.warning is not None,
        observation_fallback_count=(
            0
            if plan is None
            else sum(1 for observation in plan.observations or () if observation.fallback_reason)
        ),
    )
    writer_parameters = snapshot_input.writer_parameters
    generation_summary = GenerationDiagnosticsSummary(
        vmd_model_name=writer_parameters.vmd_model_name,
        closing_hold_frames=writer_parameters.closing_hold_frames,
        closing_softness_frames=writer_parameters.closing_softness_frames,
        fingerprint_schema_version=(
            _SHARED_FINAL_OUTPUT_FINGERPRINT_SCHEMA_VERSION
            if snapshot_input.shared_final_output_identity is not None
            else _FINGERPRINT_SCHEMA_VERSION
        ),
        active_long_vowel_mode=snapshot_input.active_long_vowel_mode,
        active_preset_id=snapshot_input.active_preset_id,
        active_preset_display_name=snapshot_input.active_preset_display_name,
        effective_long_vowel_hold_run_count=(
            snapshot_input.effective_long_vowel_hold_run_count
        ),
        effective_long_vowel_decay_run_count=(
            snapshot_input.effective_long_vowel_decay_run_count
        ),
        active_model_profile_id=snapshot_input.active_model_profile_id,
        active_model_profile_display_name=(
            snapshot_input.active_model_profile_display_name
        ),
        active_profile_baseline_preset_id=(
            snapshot_input.active_profile_baseline_preset_id
        ),
        baseline_preset_display_name=snapshot_input.baseline_preset_display_name,
        model_profile_resolution_status=(
            snapshot_input.model_profile_resolution_status
        ),
        model_profile_resolution_reason_code=(
            snapshot_input.model_profile_resolution_reason_code
        ),
        resolved_morph_name_set_id=snapshot_input.resolved_morph_name_set_id,
        resolved_morph_name_set_display_name=(
            snapshot_input.resolved_morph_name_set_display_name
        ),
    )
    effective_writer_input = snapshot_input.effective_writer_input
    adjustment_summary = AdjustmentDiagnosticsSummary(
        base_plan_identity_digest=snapshot_input.base_plan_identity_digest,
        adjustment_present=snapshot_input.adjustment_present,
        adjusted_event_count=snapshot_input.adjusted_event_count,
        effective_shape_count=(
            effective_writer_input.shape_count
            if (
                snapshot_input.effective_writer_input_state == "ready"
                and effective_writer_input is not None
            )
            else None
        ),
        effective_morph_frame_count=(
            len(effective_writer_input.morph_frames)
            if (
                snapshot_input.effective_writer_input_state == "ready"
                and effective_writer_input is not None
            )
            else None
        ),
        long_vowel_mode_override_count=snapshot_input.long_vowel_mode_override_count,
    )
    error_codes = tuple(item.code for item in items_tuple if item.severity is DiagnosticSeverity.ERROR)
    warning_codes = tuple(item.code for item in items_tuple if item.severity is DiagnosticSeverity.WARNING)
    saveability = SaveabilitySummary(
        vmd_save_allowed=bool(snapshot_input.existing_vmd_save_ready and not error_codes),
        blocking_codes=error_codes,
        warning_codes=warning_codes,
    )

    payload: FingerprintPayload | None = None
    fingerprint: str | None = None
    if nonfinite_failure is None and not effective_writer_input_invalid:
        if snapshot_input.shared_final_output_identity is not None:
            payload = build_shared_final_output_fingerprint_payload(
                snapshot_input, items_tuple
            )
        else:
            payload = build_save_state_fingerprint_payload(snapshot_input, items_tuple)
        fingerprint = compute_save_state_fingerprint(payload)
    return OutputDiagnosticsSnapshot(
        input_summary=input_summary,
        analysis_summary=analysis_summary,
        generation_summary=generation_summary,
        saveability=saveability,
        items=items_tuple,
        fingerprint_payload=payload,
        save_state_fingerprint=fingerprint,
        adjustment_summary=adjustment_summary,
        whisper_summary=snapshot_input.whisper_summary,
        projection_generation=snapshot_input.projection_generation,
        shared_final_output_identity=snapshot_input.shared_final_output_identity,
        shared_final_output_restrictions=(
            snapshot_input.shared_final_output_restrictions
        ),
        shared_final_output_restriction_event_targets=(
            snapshot_input.shared_final_output_restriction_event_targets
        ),
        transition_summary=snapshot_input.transition_summary,
        cleanup_summary=snapshot_input.cleanup_summary,
    )


__all__ = [
    "AnalysisDiagnosticsSummary",
    "AdjustmentDiagnosticsSummary",
    "CanonicalScalar",
    "CanonicalValue",
    "DiagnosticFailureInput",
    "DiagnosticIdentityContext",
    "DiagnosticItem",
    "DiagnosticRecoverability",
    "DiagnosticSeverity",
    "DiagnosticSnapshotInput",
    "DiagnosticTimingPlanInput",
    "EffectiveMorphFrameInput",
    "EffectiveTailInput",
    "EffectiveWriterInput",
    "EffectiveWriterInputState",
    "FingerprintPayload",
    "GenerationDiagnosticsSummary",
    "InputDiagnosticsSummary",
    "OutputDiagnosticsSnapshot",
    "SaveabilitySummary",
    "SourceDiagnosticSeverity",
    "VmdWriterParameters",
    "WhisperDiagnosticsSummary",
    "WhisperModelDiagnosticsItem",
    "build_output_diagnostics_snapshot",
    "build_save_state_fingerprint_payload",
    "build_shared_final_output_fingerprint_payload",
    "compute_save_state_fingerprint",
    "shared_warning_confirmation_matches",
    "evaluate_whisper_identity_status",
]
