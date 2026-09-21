from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from .generation_presets import (
    GenerationPreset,
    GenerationSettings,
    PresetLoadResult,
)
from .model_profiles import ModelProfile, ProfileLoadResult
from .morph_name_sets import (
    DEFAULT_MORPH_NAME_SET,
    MorphNameSet,
    get_builtin_morph_name_set,
)


_PROFILE_FALLBACK_REASONS = frozenset(
    {
        "profile_store_unavailable",
        "orphan_profile_baseline",
        "active_profile_not_found",
        "profile_default_preset_not_found",
    }
)
_PROFILE_ERROR_CODES = frozenset(
    {
        "store_not_loaded",
        "store_unavailable",
        "invalid_input",
        "duplicate_id",
        "duplicate_display_name",
        "limit_exceeded",
        "write_failed",
        "replace_failed",
        "builtin_read_only",
        "profile_store_unavailable",
        "profile_not_found",
        "profile_default_preset_not_found",
        "preset_not_found",
        "preset_reference_not_found",
        "active_profile_locked",
        "active_profile_baseline_locked",
        "profile_reference_check_unavailable",
        "preset_referenced_by_profile",
        "active_profile_direct_edit_locked",
    }
)


class ModelProfileResolutionStatus(str, Enum):
    NO_PROFILE = "no_profile"
    RESOLVED = "resolved"
    FALLBACK_PROFILE_DEFAULT = "fallback_profile_default"
    FALLBACK_NO_PROFILE = "fallback_no_profile"


def _require_optional_id(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be None or a non-empty string")
    return value


def _require_required_id(value: object, field_name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_strict_upper(value: object, field_name: str) -> float:
    if type(value) is not float:
        raise ValueError(f"{field_name} must be a finite float")
    if not math.isfinite(value) or not 0.0 <= value <= 10.0:
        raise ValueError(f"{field_name} must be between 0.0 and 10.0")
    return value


def _require_display_name(value: object, field_name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class ModelProfileState:
    active_model_profile_id: str | None
    active_profile_baseline_preset_id: str | None
    resolution_status: ModelProfileResolutionStatus
    resolution_reason_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.resolution_status, ModelProfileResolutionStatus):
            raise ValueError("resolution_status must be ModelProfileResolutionStatus")
        profile_id = _require_optional_id(
            self.active_model_profile_id,
            "active_model_profile_id",
        )
        baseline_id = _require_optional_id(
            self.active_profile_baseline_preset_id,
            "active_profile_baseline_preset_id",
        )
        reason = self.resolution_reason_code
        if reason is not None and (type(reason) is not str or not reason):
            raise ValueError("resolution_reason_code must be None or a non-empty string")

        status = self.resolution_status
        if status is ModelProfileResolutionStatus.NO_PROFILE:
            if profile_id is not None or baseline_id is not None or reason is not None:
                raise ValueError("NO_PROFILE must not have profile IDs or a reason")
        elif status is ModelProfileResolutionStatus.RESOLVED:
            if profile_id is None or baseline_id is None or reason is not None:
                raise ValueError("RESOLVED requires both profile IDs and no reason")
        elif status is ModelProfileResolutionStatus.FALLBACK_PROFILE_DEFAULT:
            if profile_id is None or baseline_id is None:
                raise ValueError("FALLBACK_PROFILE_DEFAULT requires both profile IDs")
            if reason != "runtime_baseline_preset_not_found":
                raise ValueError("FALLBACK_PROFILE_DEFAULT reason is invalid")
        elif status is ModelProfileResolutionStatus.FALLBACK_NO_PROFILE:
            if profile_id is not None or baseline_id is not None:
                raise ValueError("FALLBACK_NO_PROFILE must not have profile IDs")
            if reason not in _PROFILE_FALLBACK_REASONS:
                raise ValueError("FALLBACK_NO_PROFILE reason is invalid")


@dataclass(frozen=True)
class ResolvedModelProfile:
    model_profile_state: ModelProfileState
    generation_settings: GenerationSettings
    morph_upper_limit: float
    morph_name_set: MorphNameSet
    active_preset_id: str | None
    active_preset_display_name: str | None
    active_profile_display_name: str | None
    baseline_preset_display_name: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.model_profile_state, ModelProfileState):
            raise ValueError("model_profile_state must be ModelProfileState")
        if not isinstance(self.generation_settings, GenerationSettings):
            raise ValueError("generation_settings must be GenerationSettings")
        _require_strict_upper(self.morph_upper_limit, "morph_upper_limit")
        if not isinstance(self.morph_name_set, MorphNameSet):
            raise ValueError("morph_name_set must be MorphNameSet")

        preset_id = _require_optional_id(self.active_preset_id, "active_preset_id")
        preset_name = self.active_preset_display_name
        if (preset_id is None) != (preset_name is None):
            raise ValueError("active preset ID and display name must be a pair")
        if preset_name is not None:
            _require_display_name(preset_name, "active_preset_display_name")

        profile_id = self.model_profile_state.active_model_profile_id
        if profile_id is None:
            if self.active_profile_display_name is not None:
                raise ValueError("no-profile resolution must not have a profile display name")
            if self.baseline_preset_display_name is not None:
                raise ValueError("no-profile resolution must not have a baseline display name")
            if self.morph_name_set is not DEFAULT_MORPH_NAME_SET:
                raise ValueError("no-profile resolution must use the Japanese morph name set")
        else:
            _require_display_name(self.active_profile_display_name, "active_profile_display_name")
            _require_display_name(
                self.baseline_preset_display_name,
                "baseline_preset_display_name",
            )
            if preset_id is not None or preset_name is not None:
                raise ValueError("active profile resolution must not have active preset identity")


@dataclass(frozen=True)
class ModelProfileResolutionResult:
    resolution: ResolvedModelProfile | None
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.resolution is not None:
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful resolution must not have an error")
        elif not self.error_code or not self.error_message:
            raise ValueError("failed resolution must have a non-empty error pair")


@dataclass(frozen=True)
class StartupModelProfileResolution:
    resolution: ResolvedModelProfile
    identity_correction_required: bool
    active_preset_id: str | None
    active_model_profile_id: str | None
    active_profile_baseline_preset_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.resolution, ResolvedModelProfile):
            raise ValueError("resolution must be ResolvedModelProfile")
        if type(self.identity_correction_required) is not bool:
            raise ValueError("identity_correction_required must be bool")
        state = self.resolution.model_profile_state
        if self.active_model_profile_id != state.active_model_profile_id:
            raise ValueError("startup profile ID does not match resolution")
        if self.active_profile_baseline_preset_id != state.active_profile_baseline_preset_id:
            raise ValueError("startup baseline ID does not match resolution")
        if self.active_preset_id != self.resolution.active_preset_id:
            raise ValueError("startup preset ID does not match resolution")


@dataclass(frozen=True)
class RuntimeMutationGuardResult:
    allowed: bool
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if type(self.allowed) is not bool:
            raise ValueError("allowed must be bool")
        if self.allowed:
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("allowed guard result must not have an error")
        elif not self.error_code or not self.error_message:
            raise ValueError("rejected guard result must have a non-empty error pair")


def _success(resolution: ResolvedModelProfile) -> ModelProfileResolutionResult:
    return ModelProfileResolutionResult(resolution=resolution)


def _failure(error_code: str, error_message: str) -> ModelProfileResolutionResult:
    if error_code not in _PROFILE_ERROR_CODES:
        raise ValueError(f"unsupported profile resolution error code: {error_code}")
    return ModelProfileResolutionResult(
        resolution=None,
        error_code=error_code,
        error_message=error_message,
    )


def _guard_allowed() -> RuntimeMutationGuardResult:
    return RuntimeMutationGuardResult(allowed=True)


def _guard_rejected(error_code: str, error_message: str) -> RuntimeMutationGuardResult:
    if error_code not in _PROFILE_ERROR_CODES:
        raise ValueError(f"unsupported profile guard error code: {error_code}")
    return RuntimeMutationGuardResult(
        allowed=False,
        error_code=error_code,
        error_message=error_message,
    )


def _all_presets(presets: Iterable[GenerationPreset]) -> tuple[GenerationPreset, ...]:
    resolved = tuple(presets)
    if any(not isinstance(item, GenerationPreset) for item in resolved):
        raise ValueError("presets must contain GenerationPreset values")
    return resolved


def _presets_from_load_result(result: PresetLoadResult) -> tuple[GenerationPreset, ...]:
    if not isinstance(result, PresetLoadResult):
        raise ValueError("preset_load_result must be PresetLoadResult")
    return _all_presets((*result.built_in_presets, *result.user_presets))


def _profiles_from_load_result(result: ProfileLoadResult) -> tuple[ModelProfile, ...]:
    if not isinstance(result, ProfileLoadResult):
        raise ValueError("profile_load_result must be ProfileLoadResult")
    return tuple(result.user_profiles)


def _find_by_id(items: Iterable[Any], item_id: str | None) -> Any | None:
    if item_id is None:
        return None
    return next((item for item in items if item.id == item_id), None)


def _find_preset(
    presets: tuple[GenerationPreset, ...],
    preset_id: str | None,
) -> GenerationPreset | None:
    return _find_by_id(presets, preset_id)


def _resolve_active_preset(
    generation_settings: GenerationSettings,
    active_preset_id: str | None,
    presets: tuple[GenerationPreset, ...],
) -> tuple[str | None, str | None]:
    preset = _find_preset(presets, active_preset_id)
    if preset is None or preset.generation_settings != generation_settings:
        return None, None
    return preset.id, preset.display_name


def _resolve_exact_preset(
    generation_settings: GenerationSettings,
    presets: tuple[GenerationPreset, ...],
) -> tuple[str | None, str | None]:
    preset = next(
        (
            item
            for item in presets
            if item.generation_settings == generation_settings
        ),
        None,
    )
    if preset is None:
        return None, None
    return preset.id, preset.display_name


def _merge_profile_settings(
    preset_settings: GenerationSettings,
    profile: ModelProfile,
) -> GenerationSettings:
    overrides = profile.generation_overrides
    return GenerationSettings(
        closing_hold_frames=(
            preset_settings.closing_hold_frames
            if overrides.closing_hold_frames is None
            else overrides.closing_hold_frames
        ),
        closing_softness_frames=(
            preset_settings.closing_softness_frames
            if overrides.closing_softness_frames is None
            else overrides.closing_softness_frames
        ),
        long_vowel_mode=(
            preset_settings.long_vowel_mode
            if overrides.long_vowel_mode is None
            else overrides.long_vowel_mode
        ),
    )


def _resolved_profile(
    *,
    profile: ModelProfile,
    baseline: GenerationPreset,
    application_morph_upper_limit: float,
    status: ModelProfileResolutionStatus,
    reason: str | None,
) -> ResolvedModelProfile:
    upper = (
        application_morph_upper_limit
        if profile.morph_upper_limit is None
        else profile.morph_upper_limit
    )
    return ResolvedModelProfile(
        model_profile_state=ModelProfileState(
            active_model_profile_id=profile.id,
            active_profile_baseline_preset_id=baseline.id,
            resolution_status=status,
            resolution_reason_code=reason,
        ),
        generation_settings=_merge_profile_settings(
            baseline.generation_settings,
            profile,
        ),
        morph_upper_limit=_require_strict_upper(upper, "resolved morph_upper_limit"),
        morph_name_set=get_builtin_morph_name_set(profile.morph_name_set_id),
        active_preset_id=None,
        active_preset_display_name=None,
        active_profile_display_name=profile.display_name,
        baseline_preset_display_name=baseline.display_name,
    )


def _resolved_no_profile(
    *,
    generation_settings: GenerationSettings,
    morph_upper_limit: float,
    active_preset_id: str | None,
    active_preset_display_name: str | None,
    status: ModelProfileResolutionStatus = ModelProfileResolutionStatus.NO_PROFILE,
    reason: str | None = None,
) -> ResolvedModelProfile:
    return ResolvedModelProfile(
        model_profile_state=ModelProfileState(
            active_model_profile_id=None,
            active_profile_baseline_preset_id=None,
            resolution_status=status,
            resolution_reason_code=reason,
        ),
        generation_settings=generation_settings,
        morph_upper_limit=_require_strict_upper(
            morph_upper_limit,
            "resolved morph_upper_limit",
        ),
        morph_name_set=DEFAULT_MORPH_NAME_SET,
        active_preset_id=active_preset_id,
        active_preset_display_name=active_preset_display_name,
        active_profile_display_name=None,
        baseline_preset_display_name=None,
    )


def resolve_startup_model_profile(
    *,
    application_generation_settings: GenerationSettings,
    application_morph_upper_limit: float,
    raw_active_preset_id: str | None,
    raw_active_model_profile_id: str | None,
    raw_active_profile_baseline_preset_id: str | None,
    profile_load_result: ProfileLoadResult,
    preset_load_result: PresetLoadResult,
) -> StartupModelProfileResolution:
    if not isinstance(application_generation_settings, GenerationSettings):
        raise ValueError("application_generation_settings must be GenerationSettings")
    application_upper = _require_strict_upper(
        application_morph_upper_limit,
        "application_morph_upper_limit",
    )
    raw_active_preset_id = _require_optional_id(raw_active_preset_id, "raw_active_preset_id")
    raw_active_model_profile_id = _require_optional_id(
        raw_active_model_profile_id,
        "raw_active_model_profile_id",
    )
    raw_active_profile_baseline_preset_id = _require_optional_id(
        raw_active_profile_baseline_preset_id,
        "raw_active_profile_baseline_preset_id",
    )
    profiles = _profiles_from_load_result(profile_load_result)
    presets = _presets_from_load_result(preset_load_result)

    def no_profile(status: ModelProfileResolutionStatus, reason: str | None) -> StartupModelProfileResolution:
        active_id, active_name = _resolve_active_preset(
            application_generation_settings,
            raw_active_preset_id,
            presets,
        )
        resolution = _resolved_no_profile(
            generation_settings=application_generation_settings,
            morph_upper_limit=application_upper,
            active_preset_id=active_id,
            active_preset_display_name=active_name,
            status=status,
            reason=reason,
        )
        corrected = (
            active_id != raw_active_preset_id
            or raw_active_model_profile_id is not None
            or raw_active_profile_baseline_preset_id is not None
        )
        return StartupModelProfileResolution(
            resolution=resolution,
            identity_correction_required=corrected,
            active_preset_id=active_id,
            active_model_profile_id=None,
            active_profile_baseline_preset_id=None,
        )

    if not profile_load_result.mutation_available:
        return no_profile(
            ModelProfileResolutionStatus.FALLBACK_NO_PROFILE,
            "profile_store_unavailable",
        )
    if raw_active_model_profile_id is None:
        if raw_active_profile_baseline_preset_id is not None:
            return no_profile(
                ModelProfileResolutionStatus.FALLBACK_NO_PROFILE,
                "orphan_profile_baseline",
            )
        return no_profile(ModelProfileResolutionStatus.NO_PROFILE, None)

    profile = _find_by_id(profiles, raw_active_model_profile_id)
    if profile is None:
        return no_profile(
            ModelProfileResolutionStatus.FALLBACK_NO_PROFILE,
            "active_profile_not_found",
        )
    default_preset = _find_preset(presets, profile.default_preset_id)
    if default_preset is None:
        return no_profile(
            ModelProfileResolutionStatus.FALLBACK_NO_PROFILE,
            "profile_default_preset_not_found",
        )

    baseline = _find_preset(presets, raw_active_profile_baseline_preset_id)
    fallback = baseline is None
    if baseline is None:
        baseline = default_preset
    status = (
        ModelProfileResolutionStatus.FALLBACK_PROFILE_DEFAULT
        if fallback
        else ModelProfileResolutionStatus.RESOLVED
    )
    reason = "runtime_baseline_preset_not_found" if fallback else None
    resolution = _resolved_profile(
        profile=profile,
        baseline=baseline,
        application_morph_upper_limit=application_upper,
        status=status,
        reason=reason,
    )
    return StartupModelProfileResolution(
        resolution=resolution,
        identity_correction_required=(
            raw_active_preset_id is not None
            or raw_active_model_profile_id != profile.id
            or raw_active_profile_baseline_preset_id != baseline.id
        ),
        active_preset_id=None,
        active_model_profile_id=profile.id,
        active_profile_baseline_preset_id=baseline.id,
    )


def resolve_model_profile_apply(
    *,
    requested_profile_id: str,
    application_morph_upper_limit: float,
    profiles: tuple[ModelProfile, ...],
    presets: tuple[GenerationPreset, ...],
) -> ModelProfileResolutionResult:
    if type(requested_profile_id) is not str or not requested_profile_id:
        return _failure("profile_not_found", "model profile ID is invalid")
    application_upper = _require_strict_upper(
        application_morph_upper_limit,
        "application_morph_upper_limit",
    )
    profile = _find_by_id(tuple(profiles), requested_profile_id)
    if profile is None:
        return _failure("profile_not_found", "model profile was not found")
    preset = _find_preset(_all_presets(presets), profile.default_preset_id)
    if preset is None:
        return _failure(
            "profile_default_preset_not_found",
            "profile default preset was not found",
        )
    return _success(
        _resolved_profile(
            profile=profile,
            baseline=preset,
            application_morph_upper_limit=application_upper,
            status=ModelProfileResolutionStatus.RESOLVED,
            reason=None,
        )
    )


def resolve_active_profile_preset_apply(
    *,
    requested_preset_id: str,
    current_model_profile_state: ModelProfileState,
    application_morph_upper_limit: float,
    profiles: tuple[ModelProfile, ...],
    presets: tuple[GenerationPreset, ...],
) -> ModelProfileResolutionResult:
    if not isinstance(current_model_profile_state, ModelProfileState):
        raise ValueError("current_model_profile_state must be ModelProfileState")
    if current_model_profile_state.active_model_profile_id is None:
        return _failure("profile_not_found", "no active model profile exists")
    application_upper = _require_strict_upper(
        application_morph_upper_limit,
        "application_morph_upper_limit",
    )
    profile = _find_by_id(
        tuple(profiles),
        current_model_profile_state.active_model_profile_id,
    )
    if profile is None:
        return _failure("profile_not_found", "active model profile was not found")
    preset = _find_preset(_all_presets(presets), requested_preset_id)
    if preset is None:
        return _failure("preset_not_found", "preset was not found")
    return _success(
        _resolved_profile(
            profile=profile,
            baseline=preset,
            application_morph_upper_limit=application_upper,
            status=ModelProfileResolutionStatus.RESOLVED,
            reason=None,
        )
    )


def resolve_no_profile(
    *,
    current_generation_settings: GenerationSettings,
    current_morph_upper_limit: float,
    presets: tuple[GenerationPreset, ...],
) -> ModelProfileResolutionResult:
    if not isinstance(current_generation_settings, GenerationSettings):
        raise ValueError("current_generation_settings must be GenerationSettings")
    upper = _require_strict_upper(current_morph_upper_limit, "current_morph_upper_limit")
    active_id, active_name = _resolve_exact_preset(
        current_generation_settings,
        _all_presets(presets),
    )
    return _success(
        _resolved_no_profile(
            generation_settings=current_generation_settings,
            morph_upper_limit=upper,
            active_preset_id=active_id,
            active_preset_display_name=active_name,
        )
    )


def validate_model_profile_mutation(
    *,
    operation: Literal["create", "update", "delete"],
    target_profile_id: str | None,
    candidate_profile: ModelProfile | None,
    current_model_profile_state: ModelProfileState,
    profile_load_result: ProfileLoadResult,
    preset_load_result: PresetLoadResult,
) -> RuntimeMutationGuardResult:
    if operation not in {"create", "update", "delete"}:
        raise ValueError("unsupported model profile mutation operation")
    if not isinstance(current_model_profile_state, ModelProfileState):
        raise ValueError("current_model_profile_state must be ModelProfileState")
    if not profile_load_result.mutation_available:
        return _guard_rejected("store_unavailable", "profile store is unavailable")
    profiles = _profiles_from_load_result(profile_load_result)
    presets = _presets_from_load_result(preset_load_result)

    if operation == "create":
        if candidate_profile is None:
            raise ValueError("candidate_profile is required for create")
        if candidate_profile.id in {profile.id for profile in profiles}:
            return _guard_rejected("duplicate_id", "model profile id is duplicated")
        if candidate_profile.display_name in {
            profile.display_name for profile in profiles
        }:
            return _guard_rejected(
                "duplicate_display_name",
                "display name is duplicated",
            )
        target = None
    else:
        target = _find_by_id(profiles, target_profile_id)
        if target is None:
            return _guard_rejected("profile_not_found", "model profile was not found")
        if operation == "update" and candidate_profile is None:
            raise ValueError("candidate_profile is required for update")
        if operation == "update" and candidate_profile is not None:
            if candidate_profile.id != target.id:
                return _guard_rejected("invalid_input", "profile ID does not match target")

    if operation == "update" and target is not None:
        assert candidate_profile is not None
        same_except_name = (
            target.id == candidate_profile.id
            and target.morph_name_set_id == candidate_profile.morph_name_set_id
            and target.morph_upper_limit == candidate_profile.morph_upper_limit
            and target.generation_overrides == candidate_profile.generation_overrides
            and target.default_preset_id == candidate_profile.default_preset_id
        )
        active = current_model_profile_state.active_model_profile_id == target.id
        if active and not same_except_name:
            return _guard_rejected(
                "active_profile_locked",
                "active model profile is locked until it is inactive",
            )
        if any(
            profile.id != target.id
            and profile.display_name == candidate_profile.display_name
            for profile in profiles
        ):
            return _guard_rejected(
                "duplicate_display_name",
                "display name is duplicated",
            )

    if operation == "delete" and target is not None:
        if current_model_profile_state.active_model_profile_id == target.id:
            return _guard_rejected(
                "active_profile_locked",
                "active model profile is locked until it is inactive",
            )
        return _guard_allowed()

    if candidate_profile is not None and _find_preset(presets, candidate_profile.default_preset_id) is None:
        return _guard_rejected(
            "preset_reference_not_found",
            "profile default preset reference was not found",
        )
    return _guard_allowed()


def validate_generation_preset_mutation(
    *,
    operation: Literal["update", "delete"],
    target_preset_id: str,
    candidate_preset: GenerationPreset | None,
    current_model_profile_state: ModelProfileState,
    profile_load_result: ProfileLoadResult,
    preset_load_result: PresetLoadResult,
) -> RuntimeMutationGuardResult:
    if operation not in {"update", "delete"}:
        raise ValueError("unsupported generation preset mutation operation")
    if not isinstance(current_model_profile_state, ModelProfileState):
        raise ValueError("current_model_profile_state must be ModelProfileState")
    if not preset_load_result.mutation_available:
        return _guard_rejected("store_unavailable", "preset store is unavailable")
    presets = _presets_from_load_result(preset_load_result)
    target = _find_preset(presets, target_preset_id)
    if target is None:
        return _guard_rejected("preset_not_found", "preset was not found")
    if target.source == "built_in":
        return _guard_rejected("builtin_read_only", "built-in preset is not mutable")

    active_baseline = (
        current_model_profile_state.active_model_profile_id is not None
        and current_model_profile_state.active_profile_baseline_preset_id == target.id
    )
    if active_baseline:
        if operation == "delete":
            return _guard_rejected(
                "active_profile_baseline_locked",
                "active profile baseline preset is locked",
            )
        if candidate_preset is None:
            raise ValueError("candidate_preset is required for update")
        if candidate_preset.id != target.id:
            return _guard_rejected("invalid_input", "preset ID does not match target")
        if candidate_preset.generation_settings != target.generation_settings:
            return _guard_rejected(
                "active_profile_baseline_locked",
                "active profile baseline preset values are locked",
            )
        return _guard_allowed()

    if not profile_load_result.mutation_available:
        return _guard_rejected(
            "profile_reference_check_unavailable",
            "profile references cannot be checked",
        )
    profiles = _profiles_from_load_result(profile_load_result)
    if any(profile.default_preset_id == target.id for profile in profiles):
        return _guard_rejected(
            "preset_referenced_by_profile",
            "preset is referenced by a model profile",
        )
    return _guard_allowed()


def validate_active_profile_direct_edit(
    *,
    current_model_profile_state: ModelProfileState,
    current_generation_settings: GenerationSettings,
    candidate_generation_settings: GenerationSettings,
    current_morph_upper_limit: float,
    candidate_morph_upper_limit: float,
) -> RuntimeMutationGuardResult:
    if not isinstance(current_model_profile_state, ModelProfileState):
        raise ValueError("current_model_profile_state must be ModelProfileState")
    if not isinstance(current_generation_settings, GenerationSettings):
        raise ValueError("current_generation_settings must be GenerationSettings")
    if not isinstance(candidate_generation_settings, GenerationSettings):
        raise ValueError("candidate_generation_settings must be GenerationSettings")
    current_upper = _require_strict_upper(current_morph_upper_limit, "current_morph_upper_limit")
    candidate_upper = _require_strict_upper(candidate_morph_upper_limit, "candidate_morph_upper_limit")
    if current_model_profile_state.active_model_profile_id is None:
        return _guard_allowed()
    if current_generation_settings != candidate_generation_settings or current_upper != candidate_upper:
        return _guard_rejected(
            "active_profile_direct_edit_locked",
            "global generation settings are locked while a model profile is active",
        )
    return _guard_allowed()


__all__ = [
    "ModelProfileResolutionStatus",
    "ModelProfileState",
    "ResolvedModelProfile",
    "ModelProfileResolutionResult",
    "StartupModelProfileResolution",
    "RuntimeMutationGuardResult",
    "resolve_startup_model_profile",
    "resolve_model_profile_apply",
    "resolve_active_profile_preset_apply",
    "resolve_no_profile",
    "validate_model_profile_mutation",
    "validate_generation_preset_mutation",
    "validate_active_profile_direct_edit",
]
