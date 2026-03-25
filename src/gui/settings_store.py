from __future__ import annotations

import configparser
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from gui.i18n_strings import ThemeStrings

SETTINGS_FILE_NAME = "MMD_AutoLipTool.ini"

_SECTION_UI = "ui"
_SECTION_RECENT = "recent"

_KEY_THEME = "theme"
_KEY_CENTER_SPLITTER_RATIO = "center_splitter_ratio"
_KEY_WINDOW_WIDTH = "window_width"
_KEY_WINDOW_HEIGHT = "window_height"
_KEY_LANGUAGE = "language"
_KEY_MORPH_UPPER_LIMIT = "morph_upper_limit"
_KEY_RECENT_TEXT_FILES = "recent_text_files"
_KEY_RECENT_WAV_FILES = "recent_wav_files"

_ALLOWED_LANGUAGES = ("ja", "en")
_DEFAULT_THEME = ThemeStrings.DARK
_DEFAULT_CENTER_SPLITTER_RATIO = 0.3
_DEFAULT_WINDOW_WIDTH = 1280
_DEFAULT_WINDOW_HEIGHT = 740
_DEFAULT_LANGUAGE = "ja"
_DEFAULT_MORPH_UPPER_LIMIT = 0.5
_MIN_MORPH_UPPER_LIMIT = 0.0
_MAX_MORPH_UPPER_LIMIT = 10.0
_RECENT_FILE_LIMIT = 10


@dataclass(frozen=True)
class SettingsLoadResult:
    settings: dict[str, Any]
    settings_path: Path
    file_exists: bool
    load_error: str | None
    invalid_keys: tuple[str, ...]
    used_default_keys: tuple[str, ...]

    @property
    def had_error(self) -> bool:
        return self.load_error is not None


@dataclass(frozen=True)
class SettingsSaveResult:
    attempted: bool
    succeeded: bool
    settings_path: Path
    save_disabled: bool
    first_failure_in_session: bool
    error_message: str | None

    @property
    def should_notify_user(self) -> bool:
        return self.first_failure_in_session and self.error_message is not None


class SettingsStore:
    def __init__(self, settings_path: Path | None = None) -> None:
        self._settings_path = settings_path or self.default_settings_path()
        self._save_disabled = False
        self._save_failure_reported = False
        self._last_save_error: str | None = None

    @property
    def settings_path(self) -> Path:
        return self._settings_path

    @property
    def last_save_error(self) -> str | None:
        return self._last_save_error

    @property
    def save_disabled(self) -> bool:
        return self._save_disabled

    @classmethod
    def default_settings_path(cls) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / SETTINGS_FILE_NAME
        return Path(__file__).resolve().parents[2] / SETTINGS_FILE_NAME

    @classmethod
    def default_settings(cls) -> dict[str, Any]:
        return {
            _KEY_THEME: _DEFAULT_THEME,
            _KEY_CENTER_SPLITTER_RATIO: _DEFAULT_CENTER_SPLITTER_RATIO,
            _KEY_WINDOW_WIDTH: _DEFAULT_WINDOW_WIDTH,
            _KEY_WINDOW_HEIGHT: _DEFAULT_WINDOW_HEIGHT,
            _KEY_LANGUAGE: _DEFAULT_LANGUAGE,
            _KEY_MORPH_UPPER_LIMIT: _DEFAULT_MORPH_UPPER_LIMIT,
            _KEY_RECENT_TEXT_FILES: [],
            _KEY_RECENT_WAV_FILES: [],
        }

    @classmethod
    def normalize_settings(
        cls,
        settings: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
        base = cls.default_settings()
        raw_settings = dict(settings or {})
        normalized: dict[str, Any] = {}
        invalid_keys: list[str] = []
        used_default_keys: list[str] = []

        for key, default_value in base.items():
            raw_value = raw_settings.get(key, default_value)
            normalized_value, used_default = cls._normalize_value(key, raw_value)
            normalized[key] = normalized_value
            if used_default:
                used_default_keys.append(key)
                if key in raw_settings:
                    invalid_keys.append(key)

        return (normalized, tuple(invalid_keys), tuple(used_default_keys))

    def load(self) -> SettingsLoadResult:
        file_exists = self.settings_path.is_file()
        defaults = self.default_settings()
        if not file_exists:
            return SettingsLoadResult(
                settings=defaults,
                settings_path=self.settings_path,
                file_exists=False,
                load_error=None,
                invalid_keys=(),
                used_default_keys=tuple(defaults.keys()),
            )

        parser = configparser.ConfigParser()
        try:
            with self.settings_path.open("r", encoding="utf-8") as fh:
                parser.read_file(fh)
        except (OSError, configparser.Error, UnicodeError, ValueError) as error:
            return SettingsLoadResult(
                settings=defaults,
                settings_path=self.settings_path,
                file_exists=True,
                load_error=self._summarize_exception(error),
                invalid_keys=(),
                used_default_keys=tuple(defaults.keys()),
            )

        raw_settings = self._settings_from_parser(parser)
        normalized, invalid_keys, used_default_keys = self.normalize_settings(raw_settings)
        return SettingsLoadResult(
            settings=normalized,
            settings_path=self.settings_path,
            file_exists=True,
            load_error=None,
            invalid_keys=invalid_keys,
            used_default_keys=used_default_keys,
        )

    def can_save(self) -> bool:
        return not self._save_disabled

    def save(self, settings: dict[str, Any] | None) -> SettingsSaveResult:
        if self._save_disabled:
            return SettingsSaveResult(
                attempted=False,
                succeeded=False,
                settings_path=self.settings_path,
                save_disabled=True,
                first_failure_in_session=False,
                error_message=self._last_save_error,
            )

        normalized_settings, _, _ = self.normalize_settings(settings)
        parser = self._build_parser(normalized_settings)

        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._write_temp_file(parser)
            os.replace(temp_path, self.settings_path)
        except OSError as error:
            temp_path_ref = locals().get("temp_path")
            if isinstance(temp_path_ref, Path):
                try:
                    temp_path_ref.unlink(missing_ok=True)
                except OSError:
                    pass
            self._last_save_error = self._summarize_exception(error)
            first_failure = not self._save_failure_reported
            self._save_failure_reported = True
            self._save_disabled = True
            return SettingsSaveResult(
                attempted=True,
                succeeded=False,
                settings_path=self.settings_path,
                save_disabled=True,
                first_failure_in_session=first_failure,
                error_message=self._last_save_error,
            )

        self._last_save_error = None
        return SettingsSaveResult(
            attempted=True,
            succeeded=True,
            settings_path=self.settings_path,
            save_disabled=False,
            first_failure_in_session=False,
            error_message=None,
        )

    def _write_temp_file(self, parser: configparser.ConfigParser) -> Path:
        temp_path: Path | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=str(self.settings_path.parent),
                prefix="mmd_autoliptool_",
                suffix=".tmp",
            ) as fh:
                temp_path = Path(fh.name)
                parser.write(fh)
            return temp_path
        except Exception:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    @classmethod
    def _build_parser(cls, settings: dict[str, Any]) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser[_SECTION_UI] = {
            _KEY_THEME: str(settings[_KEY_THEME]),
            _KEY_CENTER_SPLITTER_RATIO: cls._format_ratio(
                settings[_KEY_CENTER_SPLITTER_RATIO]
            ),
            _KEY_WINDOW_WIDTH: str(int(settings[_KEY_WINDOW_WIDTH])),
            _KEY_WINDOW_HEIGHT: str(int(settings[_KEY_WINDOW_HEIGHT])),
            _KEY_LANGUAGE: str(settings[_KEY_LANGUAGE]),
            _KEY_MORPH_UPPER_LIMIT: cls._format_morph_upper_limit(
                settings[_KEY_MORPH_UPPER_LIMIT]
            ),
        }
        parser[_SECTION_RECENT] = {
            _KEY_RECENT_TEXT_FILES: json.dumps(
                settings[_KEY_RECENT_TEXT_FILES],
                ensure_ascii=False,
            ),
            _KEY_RECENT_WAV_FILES: json.dumps(
                settings[_KEY_RECENT_WAV_FILES],
                ensure_ascii=False,
            ),
        }
        return parser

    @classmethod
    def _settings_from_parser(cls, parser: configparser.ConfigParser) -> dict[str, Any]:
        raw: dict[str, Any] = {}
        if parser.has_section(_SECTION_UI):
            section = parser[_SECTION_UI]
            for key in (
                _KEY_THEME,
                _KEY_CENTER_SPLITTER_RATIO,
                _KEY_WINDOW_WIDTH,
                _KEY_WINDOW_HEIGHT,
                _KEY_LANGUAGE,
                _KEY_MORPH_UPPER_LIMIT,
            ):
                if key in section:
                    raw[key] = section.get(key)

        if parser.has_section(_SECTION_RECENT):
            section = parser[_SECTION_RECENT]
            for key in (_KEY_RECENT_TEXT_FILES, _KEY_RECENT_WAV_FILES):
                if key in section:
                    raw[key] = cls._parse_recent_files_value(section.get(key))

        return raw

    @classmethod
    def _parse_recent_files_value(cls, value: str | None) -> list[Any]:
        if value is None:
            return []
        stripped = str(value).strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return parsed
        return []

    @classmethod
    def _normalize_value(cls, key: str, value: Any) -> tuple[Any, bool]:
        if key == _KEY_THEME:
            return cls._normalize_theme(value)
        if key == _KEY_CENTER_SPLITTER_RATIO:
            return cls._normalize_center_splitter_ratio(value)
        if key == _KEY_WINDOW_WIDTH:
            return cls._normalize_positive_int(value, _DEFAULT_WINDOW_WIDTH)
        if key == _KEY_WINDOW_HEIGHT:
            return cls._normalize_positive_int(value, _DEFAULT_WINDOW_HEIGHT)
        if key == _KEY_LANGUAGE:
            return cls._normalize_language(value)
        if key == _KEY_MORPH_UPPER_LIMIT:
            return cls._normalize_morph_upper_limit(value)
        if key == _KEY_RECENT_TEXT_FILES:
            return cls._normalize_recent_files(value)
        if key == _KEY_RECENT_WAV_FILES:
            return cls._normalize_recent_files(value)
        raise KeyError(f"Unsupported settings key: {key}")

    @classmethod
    def _normalize_theme(cls, value: Any) -> tuple[str, bool]:
        resolved = str(value).strip().lower()
        if resolved in ThemeStrings.SUPPORTED:
            return (resolved, False)
        return (_DEFAULT_THEME, True)

    @classmethod
    def _normalize_center_splitter_ratio(cls, value: Any) -> tuple[float, bool]:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            try:
                left = float(value[0])
                right = float(value[1])
            except (TypeError, ValueError):
                return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
            if not all(math.isfinite(part) for part in (left, right)):
                return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
            if left <= 0.0 or right <= 0.0:
                return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
            total = left + right
            if total <= 0.0:
                return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
            ratio = left / total
            if 0.0 < ratio < 1.0:
                return (round(ratio, 6), False)
            return (_DEFAULT_CENTER_SPLITTER_RATIO, True)

        try:
            ratio = float(value)
        except (TypeError, ValueError):
            return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
        if not math.isfinite(ratio):
            return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
        if not (0.0 < ratio < 1.0):
            return (_DEFAULT_CENTER_SPLITTER_RATIO, True)
        return (round(ratio, 6), False)

    @classmethod
    def _normalize_positive_int(cls, value: Any, default: int) -> tuple[int, bool]:
        try:
            resolved = int(value)
        except (TypeError, ValueError):
            return (default, True)
        if resolved <= 0:
            return (default, True)
        return (resolved, False)

    @classmethod
    def _normalize_language(cls, value: Any) -> tuple[str, bool]:
        resolved = str(value).strip().lower()
        if resolved in _ALLOWED_LANGUAGES:
            return (resolved, False)
        return (_DEFAULT_LANGUAGE, True)

    @classmethod
    def _normalize_morph_upper_limit(cls, value: Any) -> tuple[float, bool]:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return (_DEFAULT_MORPH_UPPER_LIMIT, True)
        if not math.isfinite(resolved):
            return (_DEFAULT_MORPH_UPPER_LIMIT, True)
        clamped = min(max(resolved, _MIN_MORPH_UPPER_LIMIT), _MAX_MORPH_UPPER_LIMIT)
        return (round(clamped, 4), clamped != resolved)

    @classmethod
    def _normalize_recent_files(cls, value: Any) -> tuple[list[str], bool]:
        if value is None:
            return ([], False)

        raw_items: list[Any]
        if isinstance(value, str):
            raw_items = [value]
        elif isinstance(value, (list, tuple)):
            raw_items = list(value)
        else:
            return ([], True)

        normalized_items: list[str] = []
        seen: set[str] = set()
        had_invalid = False

        for item in raw_items:
            if not isinstance(item, str):
                had_invalid = True
                continue
            stripped = item.strip()
            if not stripped:
                had_invalid = True
                continue
            dedupe_key = os.path.normcase(os.path.normpath(stripped))
            if dedupe_key in seen:
                had_invalid = True
                continue
            seen.add(dedupe_key)
            normalized_items.append(stripped)
            if len(normalized_items) >= _RECENT_FILE_LIMIT:
                break

        if len(raw_items) > len(normalized_items):
            had_invalid = True
        return (normalized_items, had_invalid)

    @classmethod
    def _format_ratio(cls, value: Any) -> str:
        normalized, _ = cls._normalize_center_splitter_ratio(value)
        return f"{normalized:.6f}"

    @classmethod
    def _format_morph_upper_limit(cls, value: Any) -> str:
        normalized, _ = cls._normalize_morph_upper_limit(value)
        return f"{normalized:.4f}"

    @staticmethod
    def _summarize_exception(error: BaseException) -> str:
        message = str(error).strip()
        if message:
            return message
        return error.__class__.__name__


def default_settings_path() -> Path:
    return SettingsStore.default_settings_path()


def default_settings() -> dict[str, Any]:
    return SettingsStore.default_settings()
