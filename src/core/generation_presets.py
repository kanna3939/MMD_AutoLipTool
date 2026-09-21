from __future__ import annotations

import json
import os
import unicodedata
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .event_adjustment import validate_long_vowel_mode
from .settings_store import SettingsStore


PRESETS_FILE_NAME = "presets.json"
PRESETS_SCHEMA_VERSION = 1
MAX_USER_PRESETS = 100

BUILTIN_STANDARD_HOLD_ID = "builtin:standard-hold"
BUILTIN_LONG_VOWEL_DECAY_ID = "builtin:long-vowel-decay"
BUILTIN_STANDARD_HOLD_NAME = "標準（長音維持）"
BUILTIN_LONG_VOWEL_DECAY_NAME = "長音減衰"

_GENERATION_SETTINGS_KEYS = frozenset(
    {
        "closing_hold_frames",
        "closing_softness_frames",
        "long_vowel_mode",
    }
)
_PRESET_ENTRY_KEYS = frozenset({"id", "display_name", "generation_settings"})
_PRESETS_ROOT_KEYS = frozenset({"schema_version", "user_presets"})
_BUILTIN_SOURCE = "built_in"
_USER_SOURCE = "user"


class PresetContractError(ValueError):
    """Raised when a generation preset contract is invalid."""


GenerationPresetError = PresetContractError


class _PresetFileError(PresetContractError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def _require_bounded_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PresetContractError(f"{field_name} must be an int")
    if not 0 <= value <= 100:
        raise PresetContractError(f"{field_name} must be between 0 and 100")
    return value


def _normalize_display_name(value: object) -> str:
    if type(value) is not str:
        raise PresetContractError("display_name must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > 100:
        raise PresetContractError("display_name must contain 1 to 100 characters")
    if any(unicodedata.category(char) == "Cc" for char in normalized):
        raise PresetContractError("display_name must not contain control characters")
    if "\r" in normalized or "\n" in normalized:
        raise PresetContractError("display_name must be single-line")
    return normalized


def _validate_user_id(value: object) -> str:
    if type(value) is not str or not value:
        raise PresetContractError("user preset id must be a canonical UUID")
    if value.startswith("builtin:"):
        raise PresetContractError("user preset id must not use the built-in prefix")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as error:
        raise PresetContractError("user preset id must be a canonical UUID") from error
    if str(parsed) != value:
        raise PresetContractError("user preset id must be a canonical lowercase UUID")
    return value


def _validate_builtin_id(value: object) -> str:
    if type(value) is not str or not value.startswith("builtin:"):
        raise PresetContractError("built-in preset id must use the built-in prefix")
    return value


@dataclass(frozen=True)
class GenerationSettings:
    closing_hold_frames: int = 0
    closing_softness_frames: int = 0
    long_vowel_mode: str = "hold"

    def __post_init__(self) -> None:
        _require_bounded_int(self.closing_hold_frames, "closing_hold_frames")
        _require_bounded_int(self.closing_softness_frames, "closing_softness_frames")
        try:
            validate_long_vowel_mode(self.long_vowel_mode)
        except ValueError as error:
            raise PresetContractError(str(error)) from error

    def to_dict(self) -> dict[str, object]:
        return {
            "closing_hold_frames": self.closing_hold_frames,
            "closing_softness_frames": self.closing_softness_frames,
            "long_vowel_mode": self.long_vowel_mode,
        }

    @classmethod
    def from_dict(cls, value: object) -> "GenerationSettings":
        if type(value) is not dict or frozenset(value) != _GENERATION_SETTINGS_KEYS:
            raise PresetContractError("generation_settings has an invalid key set")
        return cls(
            closing_hold_frames=value["closing_hold_frames"],
            closing_softness_frames=value["closing_softness_frames"],
            long_vowel_mode=value["long_vowel_mode"],
        )


@dataclass(frozen=True)
class GenerationPreset:
    id: str
    display_name: str
    generation_settings: GenerationSettings
    source: str

    def __post_init__(self) -> None:
        if self.source == _BUILTIN_SOURCE:
            _validate_builtin_id(self.id)
        elif self.source == _USER_SOURCE:
            _validate_user_id(self.id)
        else:
            raise PresetContractError("preset source must be built_in or user")
        object.__setattr__(self, "display_name", _normalize_display_name(self.display_name))
        if not isinstance(self.generation_settings, GenerationSettings):
            raise PresetContractError("generation_settings must be GenerationSettings")

    def to_json_dict(self) -> dict[str, object]:
        if self.source != _USER_SOURCE:
            raise PresetContractError("built-in presets are not serialized to JSON")
        return {
            "id": self.id,
            "display_name": self.display_name,
            "generation_settings": self.generation_settings.to_dict(),
        }


BUILTIN_PRESETS: tuple[GenerationPreset, ...] = (
    GenerationPreset(
        id=BUILTIN_STANDARD_HOLD_ID,
        display_name=BUILTIN_STANDARD_HOLD_NAME,
        generation_settings=GenerationSettings(),
        source=_BUILTIN_SOURCE,
    ),
    GenerationPreset(
        id=BUILTIN_LONG_VOWEL_DECAY_ID,
        display_name=BUILTIN_LONG_VOWEL_DECAY_NAME,
        generation_settings=GenerationSettings(long_vowel_mode="decay"),
        source=_BUILTIN_SOURCE,
    ),
)


def get_builtin_presets() -> tuple[GenerationPreset, ...]:
    return BUILTIN_PRESETS


@dataclass(frozen=True)
class PresetLoadResult:
    built_in_presets: tuple[GenerationPreset, ...]
    user_presets: tuple[GenerationPreset, ...]
    presets_path: Path
    file_exists: bool
    mutation_available: bool
    error_code: str | None
    error_message: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "built_in_presets", tuple(self.built_in_presets))
        object.__setattr__(self, "user_presets", tuple(self.user_presets))
        object.__setattr__(self, "presets_path", Path(self.presets_path))


@dataclass(frozen=True)
class PresetMutationResult:
    operation: str
    succeeded: bool
    user_presets: tuple[GenerationPreset, ...]
    mutation_available: bool
    error_code: str | None
    error_message: str | None

    def __post_init__(self) -> None:
        if self.operation not in {"create", "update", "delete"}:
            raise PresetContractError("mutation operation is invalid")
        if self.succeeded:
            if self.error_code is not None or self.error_message is not None:
                raise PresetContractError("successful mutation must not have an error")
        elif not self.error_code:
            raise PresetContractError("failed mutation must have an error code")
        object.__setattr__(self, "user_presets", tuple(self.user_presets))


@dataclass(frozen=True)
class ActivePresetResolution:
    generation_settings: GenerationSettings
    active_preset_id: str | None
    active_preset_display_name: str | None
    source: str

    def __post_init__(self) -> None:
        if self.source not in {_BUILTIN_SOURCE, _USER_SOURCE, "custom"}:
            raise PresetContractError("resolution source is invalid")
        if not isinstance(self.generation_settings, GenerationSettings):
            raise PresetContractError("generation_settings must be GenerationSettings")
        if self.source == "custom":
            if self.active_preset_id is not None or self.active_preset_display_name is not None:
                raise PresetContractError("custom resolution must not have preset identity")
        elif not self.active_preset_id or not self.active_preset_display_name:
            raise PresetContractError("active resolution must have preset identity")


def _coerce_generation_settings(value: object) -> GenerationSettings:
    if isinstance(value, GenerationSettings):
        return value
    if isinstance(value, Mapping):
        return GenerationSettings.from_dict(dict(value))
    raise PresetContractError("generation_settings must be a GenerationSettings or mapping")


def _decode_user_presets(payload: object) -> tuple[GenerationPreset, ...]:
    if type(payload) is not dict or frozenset(payload) != _PRESETS_ROOT_KEYS:
        raise _PresetFileError("invalid_schema", "presets.json root has an invalid key set")
    schema_version = payload["schema_version"]
    if type(schema_version) is not int or schema_version != PRESETS_SCHEMA_VERSION:
        raise _PresetFileError("unsupported_schema", "presets.json schema_version is unsupported")
    entries = payload["user_presets"]
    if type(entries) is not list:
        raise _PresetFileError("invalid_schema", "user_presets must be a list")
    if len(entries) > MAX_USER_PRESETS:
        raise _PresetFileError("limit_exceeded", "user_presets exceeds the 100 preset limit")

    builtin_names = {preset.display_name for preset in BUILTIN_PRESETS}
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    decoded: list[GenerationPreset] = []
    for entry in entries:
        if type(entry) is not dict or frozenset(entry) != _PRESET_ENTRY_KEYS:
            raise _PresetFileError("invalid_schema", "preset entry has an invalid key set")
        try:
            preset = GenerationPreset(
                id=_validate_user_id(entry["id"]),
                display_name=entry["display_name"],
                generation_settings=GenerationSettings.from_dict(entry["generation_settings"]),
                source=_USER_SOURCE,
            )
        except PresetContractError as error:
            raise _PresetFileError("invalid_schema", str(error)) from error
        if preset.id in seen_ids:
            raise _PresetFileError("duplicate_id", "user preset id is duplicated")
        if preset.display_name in seen_names or preset.display_name in builtin_names:
            raise _PresetFileError("duplicate_display_name", "preset display name is duplicated")
        seen_ids.add(preset.id)
        seen_names.add(preset.display_name)
        decoded.append(preset)
    return tuple(decoded)


def _build_document(user_presets: tuple[GenerationPreset, ...]) -> dict[str, object]:
    return {
        "schema_version": PRESETS_SCHEMA_VERSION,
        "user_presets": [preset.to_json_dict() for preset in user_presets],
    }


class GenerationPresetStore:
    def __init__(
        self,
        settings_path: Path | SettingsStore | None = None,
        *,
        settings_store: SettingsStore | None = None,
        presets_path: Path | None = None,
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
        self._presets_path = Path(presets_path) if presets_path is not None else (
            self._settings_path.parent / PRESETS_FILE_NAME
        )
        self._user_presets: tuple[GenerationPreset, ...] = ()
        self._mutation_available = True
        self._last_error_code: str | None = None
        self._last_error_message: str | None = None
        self._last_load_result: PresetLoadResult | None = None

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    @property
    def presets_path(self) -> Path:
        return self._presets_path

    @property
    def built_in_presets(self) -> tuple[GenerationPreset, ...]:
        return BUILTIN_PRESETS

    @property
    def user_presets(self) -> tuple[GenerationPreset, ...]:
        return self._user_presets

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
    def last_load_result(self) -> PresetLoadResult | None:
        return self._last_load_result

    def load(self) -> PresetLoadResult:
        self._user_presets = ()
        self._mutation_available = True
        self._last_error_code = None
        self._last_error_message = None
        file_exists = self._presets_path.exists()

        if not file_exists:
            return self._set_load_result(
                PresetLoadResult(
                    built_in_presets=BUILTIN_PRESETS,
                    user_presets=(),
                    presets_path=self._presets_path,
                    file_exists=False,
                    mutation_available=True,
                    error_code=None,
                    error_message=None,
                )
            )

        if not self._presets_path.is_file():
            return self._load_failure(
                file_exists=True,
                error_code="read_failed",
                error_message="presets.json is not a regular file",
            )

        try:
            with self._presets_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            user_presets = _decode_user_presets(payload)
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
        except _PresetFileError as error:
            return self._load_failure(
                file_exists=True,
                error_code=error.error_code,
                error_message=str(error),
            )

        self._user_presets = user_presets
        return self._set_load_result(
            PresetLoadResult(
                built_in_presets=BUILTIN_PRESETS,
                user_presets=user_presets,
                presets_path=self._presets_path,
                file_exists=True,
                mutation_available=True,
                error_code=None,
                error_message=None,
            )
        )

    def create(
        self,
        display_name: str,
        generation_settings: GenerationSettings | Mapping[str, Any],
        *,
        preset_id: str | None = None,
    ) -> PresetMutationResult:
        if not self._mutation_available:
            return self._mutation_failure("create", "store_unavailable", self._last_error_message)
        try:
            normalized_name = _normalize_display_name(display_name)
            settings = _coerce_generation_settings(generation_settings)
        except PresetContractError as error:
            return self._mutation_failure("create", "invalid_input", str(error))
        if len(self._user_presets) >= MAX_USER_PRESETS:
            return self._mutation_failure("create", "limit_exceeded", "user preset limit exceeded")
        if normalized_name in {preset.display_name for preset in BUILTIN_PRESETS}:
            return self._mutation_failure(
                "create", "duplicate_display_name", "display name conflicts with a built-in preset"
            )
        if normalized_name in {preset.display_name for preset in self._user_presets}:
            return self._mutation_failure("create", "duplicate_display_name", "display name is duplicated")

        candidate_id = str(uuid.uuid4()) if preset_id is None else preset_id
        try:
            candidate_id = _validate_user_id(candidate_id)
        except PresetContractError as error:
            return self._mutation_failure("create", "invalid_input", str(error))
        if candidate_id in {preset.id for preset in self._user_presets}:
            return self._mutation_failure("create", "duplicate_id", "user preset id is duplicated")

        preset = GenerationPreset(candidate_id, normalized_name, settings, _USER_SOURCE)
        return self._commit_mutation("create", self._user_presets + (preset,))

    def update(
        self,
        preset_id: str,
        display_name: str,
        generation_settings: GenerationSettings | Mapping[str, Any],
    ) -> PresetMutationResult:
        if not self._mutation_available:
            return self._mutation_failure("update", "store_unavailable", self._last_error_message)
        if isinstance(preset_id, str) and preset_id.startswith("builtin:"):
            return self._mutation_failure("update", "builtin_read_only", "built-in presets are read-only")
        try:
            target_id = _validate_user_id(preset_id)
        except PresetContractError as error:
            return self._mutation_failure("update", "invalid_input", str(error))
        index = next((index for index, preset in enumerate(self._user_presets) if preset.id == target_id), None)
        if index is None:
            return self._mutation_failure("update", "preset_not_found", "user preset was not found")
        try:
            normalized_name = _normalize_display_name(display_name)
            settings = _coerce_generation_settings(generation_settings)
        except PresetContractError as error:
            return self._mutation_failure("update", "invalid_input", str(error))
        conflicting_names = {
            preset.display_name for preset in self._user_presets if preset.id != target_id
        }
        if normalized_name in conflicting_names or normalized_name in {
            preset.display_name for preset in BUILTIN_PRESETS
        }:
            return self._mutation_failure(
                "update", "duplicate_display_name", "display name is duplicated"
            )
        updated = GenerationPreset(target_id, normalized_name, settings, _USER_SOURCE)
        candidate = list(self._user_presets)
        candidate[index] = updated
        return self._commit_mutation("update", tuple(candidate))

    def delete(self, preset_id: str) -> PresetMutationResult:
        if not self._mutation_available:
            return self._mutation_failure("delete", "store_unavailable", self._last_error_message)
        if isinstance(preset_id, str) and preset_id.startswith("builtin:"):
            return self._mutation_failure("delete", "builtin_read_only", "built-in presets are read-only")
        try:
            target_id = _validate_user_id(preset_id)
        except PresetContractError as error:
            return self._mutation_failure("delete", "invalid_input", str(error))
        candidate = tuple(preset for preset in self._user_presets if preset.id != target_id)
        if len(candidate) == len(self._user_presets):
            return self._mutation_failure("delete", "preset_not_found", "user preset was not found")
        return self._commit_mutation("delete", candidate)

    def create_preset(
        self,
        display_name: str,
        generation_settings: GenerationSettings | Mapping[str, Any],
        *,
        preset_id: str | None = None,
    ) -> PresetMutationResult:
        return self.create(display_name, generation_settings, preset_id=preset_id)

    def update_preset(
        self,
        preset_id: str,
        display_name: str,
        generation_settings: GenerationSettings | Mapping[str, Any],
    ) -> PresetMutationResult:
        return self.update(preset_id, display_name, generation_settings)

    def delete_preset(self, preset_id: str) -> PresetMutationResult:
        return self.delete(preset_id)

    def resolve_active(
        self,
        generation_settings: GenerationSettings | Mapping[str, Any],
        active_preset_id: str | None,
    ) -> ActivePresetResolution:
        settings = _coerce_generation_settings(generation_settings)
        if not isinstance(active_preset_id, str) or not active_preset_id.strip():
            return ActivePresetResolution(settings, None, None, "custom")
        for preset in BUILTIN_PRESETS + self._user_presets:
            if preset.id == active_preset_id:
                if preset.generation_settings == settings:
                    return ActivePresetResolution(
                        settings,
                        preset.id,
                        preset.display_name,
                        preset.source,
                    )
                break
        return ActivePresetResolution(settings, None, None, "custom")

    def resolve_active_preset(
        self,
        generation_settings: GenerationSettings | Mapping[str, Any],
        active_preset_id: str | None,
    ) -> ActivePresetResolution:
        return self.resolve_active(generation_settings, active_preset_id)

    def _set_load_result(self, result: PresetLoadResult) -> PresetLoadResult:
        self._last_load_result = result
        return result

    def _load_failure(
        self,
        *,
        file_exists: bool,
        error_code: str,
        error_message: str,
    ) -> PresetLoadResult:
        self._mutation_available = False
        self._last_error_code = error_code
        self._last_error_message = error_message
        return self._set_load_result(
            PresetLoadResult(
                built_in_presets=BUILTIN_PRESETS,
                user_presets=(),
                presets_path=self._presets_path,
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
    ) -> PresetMutationResult:
        return PresetMutationResult(
            operation=operation,
            succeeded=False,
            user_presets=self._user_presets,
            mutation_available=self._mutation_available,
            error_code=error_code,
            error_message=error_message or error_code,
        )

    def _commit_mutation(
        self,
        operation: str,
        candidate: tuple[GenerationPreset, ...],
    ) -> PresetMutationResult:
        error = self._write_candidate(candidate)
        if error is not None:
            error_code, error_message = error
            return self._mutation_failure(operation, error_code, error_message)
        self._user_presets = candidate
        return PresetMutationResult(
            operation=operation,
            succeeded=True,
            user_presets=candidate,
            mutation_available=True,
            error_code=None,
            error_message=None,
        )

    def _write_candidate(
        self,
        candidate: tuple[GenerationPreset, ...],
    ) -> tuple[str, str] | None:
        temp_path: Path | None = None
        try:
            self._presets_path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=str(self._presets_path.parent),
                prefix="mmd_autoliptool_presets_",
                suffix=".tmp",
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(_build_document(candidate), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        except (OSError, TypeError, ValueError) as error:
            self._cleanup_temp(temp_path)
            return self._mark_unavailable("write_failed", str(error))

        try:
            os.replace(temp_path, self._presets_path)
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


PresetStore = GenerationPresetStore


__all__ = [
    "ActivePresetResolution",
    "BUILTIN_LONG_VOWEL_DECAY_ID",
    "BUILTIN_LONG_VOWEL_DECAY_NAME",
    "BUILTIN_PRESETS",
    "BUILTIN_STANDARD_HOLD_ID",
    "BUILTIN_STANDARD_HOLD_NAME",
    "GenerationPreset",
    "GenerationPresetError",
    "GenerationPresetStore",
    "GenerationSettings",
    "MAX_USER_PRESETS",
    "PRESETS_FILE_NAME",
    "PRESETS_SCHEMA_VERSION",
    "PresetContractError",
    "PresetLoadResult",
    "PresetMutationResult",
    "PresetStore",
    "get_builtin_presets",
]
