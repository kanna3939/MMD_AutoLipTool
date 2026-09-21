from __future__ import annotations

from pathlib import Path

import pytest

from src.core.generation_presets import (
    BUILTIN_PRESETS,
    GenerationPreset,
    GenerationSettings,
    GenerationPresetStore,
)
from src.core.model_profile_state import (
    ModelProfileResolutionStatus,
    resolve_model_profile_apply,
    resolve_no_profile,
    resolve_startup_model_profile,
    validate_generation_preset_mutation,
)
from src.core.model_profiles import (
    ModelProfile,
    ModelProfileStore,
    ProfileGenerationOverrides,
)
from src.core.settings_store import SettingsStore


PROFILE_ID = "11111111-1111-4111-8111-111111111111"
PROFILE_ID_2 = "22222222-2222-4222-8222-222222222222"


def _profile(
    *,
    profile_id: str = PROFILE_ID,
    default_preset_id: str = "builtin:standard-hold",
    morph_upper_limit: float | None = 0.8,
    morph_name_set_id: str = "builtin:latin-vowels",
    overrides: ProfileGenerationOverrides | None = None,
) -> ModelProfile:
    return ModelProfile(
        id=profile_id,
        display_name=f"Profile {profile_id[:4]}",
        morph_name_set_id=morph_name_set_id,
        morph_upper_limit=morph_upper_limit,
        generation_overrides=(
            ProfileGenerationOverrides()
            if overrides is None
            else overrides
        ),
        default_preset_id=default_preset_id,
    )


def _loaded_results(tmp_path: Path):
    settings_store = SettingsStore(tmp_path / "MMD_AutoLipTool.ini")
    preset_store = GenerationPresetStore(settings_store=settings_store)
    preset_result = preset_store.load()
    profile_store = ModelProfileStore(settings_store=settings_store)
    profile_result = profile_store.load()
    return profile_result, preset_result


def test_profile_apply_resolves_precedence_and_builtin_morph_set(tmp_path: Path) -> None:
    profile_result, preset_result = _loaded_results(tmp_path)
    profile = _profile(
        overrides=ProfileGenerationOverrides(
            closing_hold_frames=7,
            long_vowel_mode="decay",
        )
    )
    result = resolve_model_profile_apply(
        requested_profile_id=profile.id,
        application_morph_upper_limit=0.6,
        profiles=(profile,),
        presets=(*preset_result.built_in_presets, *preset_result.user_presets),
    )

    assert result.error_code is None
    assert result.resolution is not None
    resolved = result.resolution
    assert resolved.model_profile_state.resolution_status is ModelProfileResolutionStatus.RESOLVED
    assert resolved.model_profile_state.active_model_profile_id == PROFILE_ID
    assert resolved.model_profile_state.active_profile_baseline_preset_id == "builtin:standard-hold"
    assert resolved.generation_settings == GenerationSettings(7, 0, "decay")
    assert resolved.morph_upper_limit == 0.8
    assert resolved.morph_name_set.output_names == ("A", "I", "U", "E", "O")
    assert resolved.active_preset_id is None
    assert resolved.active_preset_display_name is None


@pytest.mark.parametrize("value", [True, 1, "0.5"])
def test_profile_resolution_rejects_non_strict_upper(value: object) -> None:
    profile = _profile()
    with pytest.raises(ValueError, match="application_morph_upper_limit"):
        resolve_model_profile_apply(
            requested_profile_id=profile.id,
            application_morph_upper_limit=value,
            profiles=(profile,),
            presets=BUILTIN_PRESETS,
        )


def test_no_profile_recomputes_exact_preset_identity(tmp_path: Path) -> None:
    _, preset_result = _loaded_results(tmp_path)
    result = resolve_no_profile(
        current_generation_settings=BUILTIN_PRESETS[0].generation_settings,
        current_morph_upper_limit=0.5,
        presets=(*preset_result.built_in_presets, *preset_result.user_presets),
    )

    assert result.resolution is not None
    assert result.resolution.model_profile_state.resolution_status is ModelProfileResolutionStatus.NO_PROFILE
    assert result.resolution.active_preset_id == BUILTIN_PRESETS[0].id
    assert result.resolution.active_preset_display_name == BUILTIN_PRESETS[0].display_name
    assert result.resolution.morph_name_set.output_names == ("あ", "い", "う", "え", "お")


def test_startup_missing_runtime_baseline_falls_back_to_profile_default(tmp_path: Path) -> None:
    profile_result, preset_result = _loaded_results(tmp_path)
    profile = _profile()
    profile_result = profile_result.__class__(
        user_profiles=(profile,),
        profiles_path=profile_result.profiles_path,
        file_exists=True,
        mutation_available=True,
        error_code=None,
        error_message=None,
    )
    startup = resolve_startup_model_profile(
        application_generation_settings=GenerationSettings(4, 5, "hold"),
        application_morph_upper_limit=0.6,
        raw_active_preset_id=None,
        raw_active_model_profile_id=profile.id,
        raw_active_profile_baseline_preset_id="missing-baseline",
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )

    assert startup.resolution.model_profile_state.resolution_status is ModelProfileResolutionStatus.FALLBACK_PROFILE_DEFAULT
    assert startup.resolution.model_profile_state.resolution_reason_code == "runtime_baseline_preset_not_found"
    assert startup.active_profile_baseline_preset_id == profile.default_preset_id
    assert startup.active_preset_id is None
    assert startup.identity_correction_required is True
    assert startup.resolution.morph_upper_limit == 0.8


def test_active_baseline_guard_precedes_profile_reference_checks(tmp_path: Path) -> None:
    profile_result, preset_result = _loaded_results(tmp_path)
    baseline_id = "44444444-4444-4444-8444-444444444444"
    baseline = GenerationPreset(
        id=baseline_id,
        display_name="User baseline",
        generation_settings=GenerationSettings(),
        source="user",
    )
    preset_result = preset_result.__class__(
        built_in_presets=preset_result.built_in_presets,
        user_presets=(baseline,),
        presets_path=preset_result.presets_path,
        file_exists=True,
        mutation_available=True,
        error_code=None,
        error_message=None,
    )
    profile = _profile(default_preset_id=baseline_id)
    profile_result = profile_result.__class__(
        user_profiles=(profile,),
        profiles_path=profile_result.profiles_path,
        file_exists=True,
        mutation_available=True,
        error_code=None,
        error_message=None,
    )
    current = resolve_model_profile_apply(
        requested_profile_id=profile.id,
        application_morph_upper_limit=0.5,
        profiles=(profile,),
        presets=(*preset_result.built_in_presets, *preset_result.user_presets),
    ).resolution.model_profile_state
    target = baseline

    guard = validate_generation_preset_mutation(
        operation="delete",
        target_preset_id=target.id,
        candidate_preset=None,
        current_model_profile_state=current,
        profile_load_result=profile_result,
        preset_load_result=preset_result,
    )

    assert guard.allowed is False
    assert guard.error_code == "active_profile_baseline_locked"
