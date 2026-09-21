from __future__ import annotations

import json
import math
import os
import unicodedata
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .event_adjustment import validate_long_vowel_mode
from .morph_name_sets import get_builtin_morph_name_set
from .settings_store import SettingsStore


PROFILES_FILE_NAME = "profiles.json"
PROFILES_SCHEMA_VERSION = 1
MAX_USER_PROFILES = 100

_PROFILE_ENTRY_KEYS = frozenset(
    {
        "id",
        "display_name",
        "morph_name_set_id",
        "morph_upper_limit",
        "generation_overrides",
        "default_preset_id",
    }
)
_PROFILE_ROOT_KEYS = frozenset({"schema_version", "user_profiles"})
_OVERRIDE_KEYS = frozenset(
    {
        "closing_hold_frames",
        "closing_softness_frames",
        "long_vowel_mode",
    }
)


class ProfileContractError(ValueError):
    """Raised when an MS23 model profile contract is invalid."""


ModelProfileError = ProfileContractError


class _ProfileFileError(ProfileContractError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def _require_bounded_optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProfileContractError(f"{field_name} must be an int or null")
    if not 0 <= value <= 100:
        raise ProfileContractError(f"{field_name} must be between 0 and 100")
    return value


def _normalize_display_name(value: object) -> str:
    if type(value) is not str:
        raise ProfileContractError("display_name must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > 100:
        raise ProfileContractError("display_name must contain 1 to 100 characters")
    if any(unicodedata.category(character) == "Cc" for character in normalized):
        raise ProfileContractError("display_name must not contain control characters")
    if "\r" in normalized or "\n" in normalized:
        raise ProfileContractError("display_name must be single-line")
    return normalized


def _validate_profile_id(value: object) -> str:
    if type(value) is not str or not value:
        raise ProfileContractError("model profile id must be a canonical UUID")
    if value.startswith("builtin:"):
        raise ProfileContractError("model profile id must not use the built-in prefix")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, ValueError) as error:
        raise ProfileContractError("model profile id must be a canonical UUID") from error
    if str(parsed) != value:
        raise ProfileContractError("model profile id must be a canonical lowercase UUID")
    return value


def _validate_morph_upper_limit(value: object) -> float | None:
    if value is None:
        return None
    if type(value) is not float:
        raise ProfileContractError("morph_upper_limit must be a finite float or null")
    if not math.isfinite(value) or not 0.0 <= value <= 10.0:
        raise ProfileContractError("morph_upper_limit must be between 0.0 and 10.0")
    return value


def _validate_default_preset_id(value: object) -> str:
    if type(value) is not str or not value:
        raise ProfileContractError("default_preset_id must be a stable string")
    if value != value.strip() or any(character.isspace() for character in value):
        raise ProfileContractError("default_preset_id must not contain whitespace")
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise ProfileContractError("default_preset_id must not contain control characters")
    if value.startswith("builtin:"):
        if not value.removeprefix("builtin:"):
            raise ProfileContractError("built-in default_preset_id must have a suffix")
        return value
    return _validate_profile_reference_uuid(value)


def _validate_profile_reference_uuid(value: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, ValueError) as error:
        raise ProfileContractError(
            "default_preset_id must be a canonical UUID or a built-in reference"
        ) from error
    if str(parsed) != value:
        raise ProfileContractError("default_preset_id must use a canonical lowercase UUID")
    return value


@dataclass(frozen=True)
class ProfileGenerationOverrides:
    closing_hold_frames: int | None = None
    closing_softness_frames: int | None = None
    long_vowel_mode: str | None = None

    def __post_init__(self) -> None:
        _require_bounded_optional_int(self.closing_hold_frames, "closing_hold_frames")
        _require_bounded_optional_int(self.closing_softness_frames, "closing_softness_frames")
        if self.long_vowel_mode is not None:
            try:
                validate_long_vowel_mode(self.long_vowel_mode)
            except ValueError as error:
                raise ProfileContractError(str(error)) from error

    def to_dict(self) -> dict[str, object]:
        return {
            "closing_hold_frames": self.closing_hold_frames,
            "closing_softness_frames": self.closing_softness_frames,
            "long_vowel_mode": self.long_vowel_mode,
        }

    @classmethod
    def from_dict(cls, value: object) -> "ProfileGenerationOverrides":
        if type(value) is not dict or frozenset(value) != _OVERRIDE_KEYS:
            raise ProfileContractError("generation_overrides has an invalid key set")
        return cls(
            closing_hold_frames=value["closing_hold_frames"],
            closing_softness_frames=value["closing_softness_frames"],
            long_vowel_mode=value["long_vowel_mode"],
        )


@dataclass(frozen=True)
class ModelProfile:
    id: str
    display_name: str
    morph_name_set_id: str
    morph_upper_limit: float | None
    generation_overrides: ProfileGenerationOverrides
    default_preset_id: str

    def __post_init__(self) -> None:
        _validate_profile_id(self.id)
        object.__setattr__(self, "display_name", _normalize_display_name(self.display_name))
        try:
            get_builtin_morph_name_set(self.morph_name_set_id)
        except ValueError as error:
            raise ProfileContractError(str(error)) from error
        _validate_morph_upper_limit(self.morph_upper_limit)
        if not isinstance(self.generation_overrides, ProfileGenerationOverrides):
            raise ProfileContractError(
                "generation_overrides must be ProfileGenerationOverrides"
            )
        _validate_default_preset_id(self.default_preset_id)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "morph_name_set_id": self.morph_name_set_id,
            "morph_upper_limit": self.morph_upper_limit,
            "generation_overrides": self.generation_overrides.to_dict(),
            "default_preset_id": self.default_preset_id,
        }

    @classmethod
    def from_dict(cls, value: object) -> "ModelProfile":
        if type(value) is not dict or frozenset(value) != _PROFILE_ENTRY_KEYS:
            raise ProfileContractError("model profile entry has an invalid key set")
        return cls(
            id=value["id"],
            display_name=value["display_name"],
            morph_name_set_id=value["morph_name_set_id"],
            morph_upper_limit=value["morph_upper_limit"],
            generation_overrides=ProfileGenerationOverrides.from_dict(
                value["generation_overrides"]
            ),
            default_preset_id=value["default_preset_id"],
        )


@dataclass(frozen=True)
class ProfileLoadResult:
    user_profiles: tuple[ModelProfile, ...]
    profiles_path: Path
    file_exists: bool
    mutation_available: bool
    error_code: str | None
    error_message: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_profiles", tuple(self.user_profiles))
        object.__setattr__(self, "profiles_path", Path(self.profiles_path))


@dataclass(frozen=True)
class ProfileMutationResult:
    operation: str
    succeeded: bool
    user_profiles: tuple[ModelProfile, ...]
    mutation_available: bool
    error_code: str | None
    error_message: str | None

    def __post_init__(self) -> None:
        if self.operation not in {"create", "update", "delete"}:
            raise ProfileContractError("mutation operation is invalid")
        if self.succeeded:
            if self.error_code is not None or self.error_message is not None:
                raise ProfileContractError("successful mutation must not have an error")
        elif not self.error_code:
            raise ProfileContractError("failed mutation must have an error code")
        object.__setattr__(self, "user_profiles", tuple(self.user_profiles))


def _coerce_overrides(value: ProfileGenerationOverrides | Mapping[str, Any]) -> ProfileGenerationOverrides:
    if isinstance(value, ProfileGenerationOverrides):
        return value
    if isinstance(value, Mapping):
        return ProfileGenerationOverrides.from_dict(dict(value))
    raise ProfileContractError(
        "generation_overrides must be ProfileGenerationOverrides or a mapping"
    )


def _decode_user_profiles(payload: object) -> tuple[ModelProfile, ...]:
    if type(payload) is not dict or frozenset(payload) != _PROFILE_ROOT_KEYS:
        raise _ProfileFileError("invalid_schema", "profiles.json root has an invalid key set")
    schema_version = payload["schema_version"]
    if type(schema_version) is not int or schema_version != PROFILES_SCHEMA_VERSION:
        raise _ProfileFileError("unsupported_schema", "profiles.json schema_version is unsupported")
    entries = payload["user_profiles"]
    if type(entries) is not list:
        raise _ProfileFileError("invalid_schema", "user_profiles must be a list")
    if len(entries) > MAX_USER_PROFILES:
        raise _ProfileFileError("limit_exceeded", "user_profiles exceeds the 100 profile limit")

    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    decoded: list[ModelProfile] = []
    for entry in entries:
        try:
            profile = ModelProfile.from_dict(entry)
        except ProfileContractError as error:
            raise _ProfileFileError("invalid_schema", str(error)) from error
        if profile.id in seen_ids:
            raise _ProfileFileError("duplicate_id", "model profile id is duplicated")
        if profile.display_name in seen_names:
            raise _ProfileFileError("duplicate_display_name", "display name is duplicated")
        seen_ids.add(profile.id)
        seen_names.add(profile.display_name)
        decoded.append(profile)
    return tuple(decoded)


def _build_document(user_profiles: tuple[ModelProfile, ...]) -> dict[str, object]:
    return {
        "schema_version": PROFILES_SCHEMA_VERSION,
        "user_profiles": [profile.to_json_dict() for profile in user_profiles],
    }


class ModelProfileStore:
    def __init__(
        self,
        settings_path: Path | SettingsStore | None = None,
        *,
        settings_store: SettingsStore | None = None,
        profiles_path: Path | None = None,
    ) -> None:
        if settings_store is not None and settings_path is not None:
            raise ValueError("settings_path and settings_store are mutually exclusive")
        if isinstance(settings_path, SettingsStore):
            settings_store = settings_path
            settings_path = None
        if settings_store is not None:
            resolved_settings_path = settings_store.settings_path
        elif settings_path is not None:
            resolved_settings_path = Path(settings_path)
        else:
            resolved_settings_path = SettingsStore().settings_path

        self._settings_path = Path(resolved_settings_path)
        self._profiles_path = Path(profiles_path) if profiles_path is not None else (
            self._settings_path.parent / PROFILES_FILE_NAME
        )
        self._user_profiles: tuple[ModelProfile, ...] = ()
        self._load_completed = False
        self._mutation_available = False
        self._last_error_code: str | None = None
        self._last_error_message: str | None = None
        self._last_load_result: ProfileLoadResult | None = None

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    @property
    def profiles_path(self) -> Path:
        return self._profiles_path

    @property
    def user_profiles(self) -> tuple[ModelProfile, ...]:
        return self._user_profiles

    @property
    def profiles(self) -> tuple[ModelProfile, ...]:
        return self._user_profiles

    @property
    def load_completed(self) -> bool:
        return self._load_completed

    @property
    def mutation_available(self) -> bool:
        return self._mutation_available

    @property
    def last_error_code(self) -> str | None:
        return self._last_error_code

    @property
    def last_error_message(self) -> str | None:
        return self._last_error_message

    @property
    def last_load_result(self) -> ProfileLoadResult | None:
        return self._last_load_result

    def load(self) -> ProfileLoadResult:
        self._user_profiles = ()
        self._load_completed = True
        self._mutation_available = True
        self._last_error_code = None
        self._last_error_message = None
        file_exists = self._profiles_path.exists()

        if not file_exists:
            return self._set_load_result(
                ProfileLoadResult(
                    user_profiles=(),
                    profiles_path=self._profiles_path,
                    file_exists=False,
                    mutation_available=True,
                    error_code=None,
                    error_message=None,
                )
            )

        if not self._profiles_path.is_file():
            return self._load_failure(
                file_exists=True,
                error_code="read_failed",
                error_message="profiles.json is not a regular file",
            )

        try:
            with self._profiles_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            user_profiles = _decode_user_profiles(payload)
        except json.JSONDecodeError as error:
            return self._load_failure(
                file_exists=True,
                error_code="invalid_json",
                error_message=str(error),
            )
        except UnicodeError as error:
            return self._load_failure(
                file_exists=True,
                error_code="read_failed",
                error_message=str(error),
            )
        except OSError as error:
            return self._load_failure(
                file_exists=True,
                error_code="read_failed",
                error_message=str(error),
            )
        except _ProfileFileError as error:
            return self._load_failure(
                file_exists=True,
                error_code=error.error_code,
                error_message=str(error),
            )

        self._user_profiles = user_profiles
        return self._set_load_result(
            ProfileLoadResult(
                user_profiles=user_profiles,
                profiles_path=self._profiles_path,
                file_exists=True,
                mutation_available=True,
                error_code=None,
                error_message=None,
            )
        )

    def get_profile(self, profile_id: object) -> ModelProfile | None:
        if not self._load_completed:
            raise ProfileContractError("model profile store has not been loaded")
        if type(profile_id) is not str:
            return None
        return next(
            (profile for profile in self._user_profiles if profile.id == profile_id),
            None,
        )

    def create(
        self,
        display_name: str,
        morph_name_set_id: str,
        morph_upper_limit: float | None,
        generation_overrides: ProfileGenerationOverrides | Mapping[str, Any],
        default_preset_id: str,
        *,
        profile_id: str | None = None,
    ) -> ProfileMutationResult:
        if not self._load_completed:
            return self._mutation_failure("create", "store_not_loaded", "profile store has not been loaded")
        if not self._mutation_available:
            return self._mutation_failure("create", "store_unavailable", self._last_error_message)
        if len(self._user_profiles) >= MAX_USER_PROFILES:
            return self._mutation_failure("create", "limit_exceeded", "user profile limit exceeded")

        candidate_id = str(uuid.uuid4()) if profile_id is None else profile_id
        try:
            profile = ModelProfile(
                id=candidate_id,
                display_name=display_name,
                morph_name_set_id=morph_name_set_id,
                morph_upper_limit=morph_upper_limit,
                generation_overrides=_coerce_overrides(generation_overrides),
                default_preset_id=default_preset_id,
            )
        except ProfileContractError as error:
            return self._mutation_failure("create", "invalid_input", str(error))
        if profile.id in {item.id for item in self._user_profiles}:
            return self._mutation_failure("create", "duplicate_id", "model profile id is duplicated")
        if profile.display_name in {item.display_name for item in self._user_profiles}:
            return self._mutation_failure(
                "create", "duplicate_display_name", "display name is duplicated"
            )
        return self._commit_mutation("create", self._user_profiles + (profile,))

    def update(
        self,
        profile_id: str,
        display_name: str,
        morph_name_set_id: str,
        morph_upper_limit: float | None,
        generation_overrides: ProfileGenerationOverrides | Mapping[str, Any],
        default_preset_id: str,
    ) -> ProfileMutationResult:
        if not self._load_completed:
            return self._mutation_failure("update", "store_not_loaded", "profile store has not been loaded")
        if not self._mutation_available:
            return self._mutation_failure("update", "store_unavailable", self._last_error_message)
        try:
            target_id = _validate_profile_id(profile_id)
        except ProfileContractError as error:
            return self._mutation_failure("update", "invalid_input", str(error))
        index = next(
            (index for index, profile in enumerate(self._user_profiles) if profile.id == target_id),
            None,
        )
        if index is None:
            return self._mutation_failure("update", "profile_not_found", "model profile was not found")
        try:
            updated = ModelProfile(
                id=target_id,
                display_name=display_name,
                morph_name_set_id=morph_name_set_id,
                morph_upper_limit=morph_upper_limit,
                generation_overrides=_coerce_overrides(generation_overrides),
                default_preset_id=default_preset_id,
            )
        except ProfileContractError as error:
            return self._mutation_failure("update", "invalid_input", str(error))
        conflicting_names = {
            profile.display_name for profile in self._user_profiles if profile.id != target_id
        }
        if updated.display_name in conflicting_names:
            return self._mutation_failure(
                "update", "duplicate_display_name", "display name is duplicated"
            )
        candidate = list(self._user_profiles)
        candidate[index] = updated
        return self._commit_mutation("update", tuple(candidate))

    def delete(self, profile_id: str) -> ProfileMutationResult:
        if not self._load_completed:
            return self._mutation_failure("delete", "store_not_loaded", "profile store has not been loaded")
        if not self._mutation_available:
            return self._mutation_failure("delete", "store_unavailable", self._last_error_message)
        try:
            target_id = _validate_profile_id(profile_id)
        except ProfileContractError as error:
            return self._mutation_failure("delete", "invalid_input", str(error))
        candidate = tuple(profile for profile in self._user_profiles if profile.id != target_id)
        if len(candidate) == len(self._user_profiles):
            return self._mutation_failure("delete", "profile_not_found", "model profile was not found")
        return self._commit_mutation("delete", candidate)

    def create_profile(self, *args: Any, **kwargs: Any) -> ProfileMutationResult:
        return self.create(*args, **kwargs)

    def update_profile(self, *args: Any, **kwargs: Any) -> ProfileMutationResult:
        return self.update(*args, **kwargs)

    def delete_profile(self, *args: Any, **kwargs: Any) -> ProfileMutationResult:
        return self.delete(*args, **kwargs)

    def _set_load_result(self, result: ProfileLoadResult) -> ProfileLoadResult:
        self._last_load_result = result
        return result

    def _load_failure(
        self,
        *,
        file_exists: bool,
        error_code: str,
        error_message: str,
    ) -> ProfileLoadResult:
        self._user_profiles = ()
        self._load_completed = True
        self._mutation_available = False
        self._last_error_code = error_code
        self._last_error_message = error_message
        return self._set_load_result(
            ProfileLoadResult(
                user_profiles=(),
                profiles_path=self._profiles_path,
                file_exists=file_exists,
                mutation_available=False,
                error_code=error_code,
                error_message=error_message,
            )
        )

    def _mutation_failure(
        self,
        operation: str,
        error_code: str,
        error_message: str | None,
    ) -> ProfileMutationResult:
        return ProfileMutationResult(
            operation=operation,
            succeeded=False,
            user_profiles=self._user_profiles,
            mutation_available=self._mutation_available,
            error_code=error_code,
            error_message=error_message or error_code,
        )

    def _commit_mutation(
        self,
        operation: str,
        candidate: tuple[ModelProfile, ...],
    ) -> ProfileMutationResult:
        error = self._write_candidate(candidate)
        if error is not None:
            error_code, error_message = error
            return self._mutation_failure(operation, error_code, error_message)
        self._user_profiles = candidate
        return ProfileMutationResult(
            operation=operation,
            succeeded=True,
            user_profiles=candidate,
            mutation_available=True,
            error_code=None,
            error_message=None,
        )

    def _write_candidate(
        self,
        candidate: tuple[ModelProfile, ...],
    ) -> tuple[str, str] | None:
        temp_path: Path | None = None
        try:
            self._profiles_path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=str(self._profiles_path.parent),
                prefix="mmd_autoliptool_profiles_",
                suffix=".tmp",
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(_build_document(candidate), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        except (OSError, TypeError, ValueError) as error:
            self._cleanup_temp(temp_path)
            return self._mark_unavailable("write_failed", str(error))

        try:
            os.replace(temp_path, self._profiles_path)
        except OSError as error:
            self._cleanup_temp(temp_path)
            return self._mark_unavailable("replace_failed", str(error))

        self._last_error_code = None
        self._last_error_message = None
        return None

    def _mark_unavailable(self, error_code: str, error_message: str) -> tuple[str, str]:
        self._mutation_available = False
        self._last_error_code = error_code
        self._last_error_message = error_message or error_code
        return (error_code, self._last_error_message)

    @staticmethod
    def _cleanup_temp(temp_path: Path | None) -> None:
        if temp_path is None:
            return
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


ModelProfileStoreError = ProfileContractError
ProfileStore = ModelProfileStore


__all__ = [
    "MAX_USER_PROFILES",
    "ModelProfile",
    "ModelProfileError",
    "ModelProfileStore",
    "ModelProfileStoreError",
    "PROFILES_FILE_NAME",
    "PROFILES_SCHEMA_VERSION",
    "ProfileContractError",
    "ProfileGenerationOverrides",
    "ProfileLoadResult",
    "ProfileMutationResult",
    "ProfileStore",
]
