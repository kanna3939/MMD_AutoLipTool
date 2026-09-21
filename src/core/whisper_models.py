from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import PurePosixPath
from typing import Any, Mapping
from urllib.parse import urlsplit


EXPECTED_WHISPER_VERSION = "20250625"
MANIFEST_SCHEMA_VERSION = 1
MANIFEST_RESOURCE_NAME = "whisper_models.json"
SUPPORTED_MODEL_KEYS = ("small", "medium", "turbo")
_SUPPORTED_MODEL_KEY_SET = frozenset(SUPPORTED_MODEL_KEYS)
_OFFICIAL_MODEL_HOST = "openaipublic.azureedge.net"
_OFFICIAL_MODEL_PATH_PREFIX = "/main/whisper/models/"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class WhisperManifestError(ValueError):
    """Raised when the versioned Whisper manifest is invalid or unavailable."""

    def __init__(self, message: str, *, code: str = "manifest_invalid") -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class WhisperModelSpec:
    model_key: str
    display_name: str
    multilingual: bool
    japanese_supported: bool
    official_url: str
    filename: str
    sha256: str
    size_bytes: int
    vram_hint: str
    speed_hint: str
    recommended_use: str


@dataclass(frozen=True)
class WhisperModelCatalog:
    schema_version: int
    openai_whisper_version: str
    default_model_key: str
    models: tuple[WhisperModelSpec, ...]

    def get(self, model_key: str) -> WhisperModelSpec:
        for spec in self.models:
            if spec.model_key == model_key:
                return spec
        raise WhisperManifestError(f"Unsupported Whisper model key: {model_key!r}", code="model_key_unsupported")

    def manifest_identity(self, model_key: str) -> str:
        spec = self.get(model_key)
        return build_manifest_identity(self.openai_whisper_version, spec.model_key, spec.sha256)


def build_manifest_identity(openai_whisper_version: str, model_key: str, sha256: str) -> str:
    return f"whisper-manifest-v1:{openai_whisper_version}:{model_key}:{sha256}"


def load_whisper_model_catalog() -> WhisperModelCatalog:
    """Load and strictly validate the package-relative versioned manifest."""
    try:
        manifest_resource = resources.files(__package__).joinpath(MANIFEST_RESOURCE_NAME)
        manifest_bytes = manifest_resource.read_bytes()
    except Exception as error:
        raise WhisperManifestError(f"Failed to read Whisper manifest resource: {error}") from error
    return parse_whisper_model_manifest(manifest_bytes)


def parse_whisper_model_manifest(payload: bytes | str | Mapping[str, Any]) -> WhisperModelCatalog:
    """Parse a manifest payload without accepting caller-controlled metadata overrides."""
    try:
        if isinstance(payload, bytes):
            document = json.loads(payload.decode("utf-8"))
        elif isinstance(payload, str):
            document = json.loads(payload)
        else:
            document = payload
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        raise WhisperManifestError(f"Invalid Whisper manifest JSON: {error}") from error

    if not isinstance(document, Mapping):
        raise WhisperManifestError("Whisper manifest root must be an object.")

    _require_exact_keys(
        document,
        {
            "schema_version",
            "openai_whisper_version",
            "default_model_key",
            "models",
        },
        "manifest root",
    )
    if document["schema_version"] != MANIFEST_SCHEMA_VERSION or type(document["schema_version"]) is not int:
        raise WhisperManifestError("Whisper manifest schema_version must be integer 1.")
    if document["openai_whisper_version"] != EXPECTED_WHISPER_VERSION:
        raise WhisperManifestError("Whisper manifest package version is not 20250625.")
    if document["default_model_key"] != "small":
        raise WhisperManifestError("Whisper manifest default_model_key must be small.")

    raw_models = document["models"]
    if not isinstance(raw_models, list):
        raise WhisperManifestError("Whisper manifest models must be an array.")
    if len(raw_models) != len(SUPPORTED_MODEL_KEYS):
        raise WhisperManifestError("Whisper manifest must contain exactly three models.")

    models: list[WhisperModelSpec] = []
    seen_keys: set[str] = set()
    seen_filenames: set[str] = set()
    seen_urls: set[str] = set()
    for raw_model in raw_models:
        spec = _parse_model_spec(raw_model)
        if spec.model_key in seen_keys:
            raise WhisperManifestError(f"Duplicate Whisper model key: {spec.model_key!r}.")
        if spec.filename in seen_filenames:
            raise WhisperManifestError(f"Duplicate Whisper model filename: {spec.filename!r}.")
        if spec.official_url in seen_urls:
            raise WhisperManifestError("Duplicate Whisper model official_url.")
        seen_keys.add(spec.model_key)
        seen_filenames.add(spec.filename)
        seen_urls.add(spec.official_url)
        models.append(spec)

    if tuple(model.model_key for model in models) != SUPPORTED_MODEL_KEYS:
        raise WhisperManifestError("Whisper manifest model order must be small, medium, turbo.")

    return WhisperModelCatalog(
        schema_version=MANIFEST_SCHEMA_VERSION,
        openai_whisper_version=EXPECTED_WHISPER_VERSION,
        default_model_key="small",
        models=tuple(models),
    )


def _parse_model_spec(raw_model: Any) -> WhisperModelSpec:
    if not isinstance(raw_model, Mapping):
        raise WhisperManifestError("Each Whisper model entry must be an object.")
    expected_keys = {
        "model_key",
        "display_name",
        "multilingual",
        "japanese_supported",
        "official_url",
        "filename",
        "sha256",
        "size_bytes",
        "vram_hint",
        "speed_hint",
        "recommended_use",
    }
    _require_exact_keys(raw_model, expected_keys, "Whisper model entry")

    string_fields = (
        "model_key",
        "display_name",
        "official_url",
        "filename",
        "sha256",
        "vram_hint",
        "speed_hint",
        "recommended_use",
    )
    for field_name in string_fields:
        value = raw_model[field_name]
        if not isinstance(value, str) or not value.strip():
            raise WhisperManifestError(f"Whisper model {field_name} must be a non-empty string.")

    model_key = raw_model["model_key"]
    if model_key not in _SUPPORTED_MODEL_KEY_SET:
        raise WhisperManifestError(f"Unsupported Whisper model key: {model_key!r}", code="model_key_unsupported")

    if type(raw_model["multilingual"]) is not bool or not raw_model["multilingual"]:
        raise WhisperManifestError(f"Whisper model {model_key!r} must be multilingual.")
    if type(raw_model["japanese_supported"]) is not bool or not raw_model["japanese_supported"]:
        raise WhisperManifestError(f"Whisper model {model_key!r} must support Japanese.")

    sha256 = raw_model["sha256"]
    if _SHA256_PATTERN.fullmatch(sha256) is None:
        raise WhisperManifestError(f"Whisper model {model_key!r} has an invalid SHA256.")

    size_bytes = raw_model["size_bytes"]
    if type(size_bytes) is not int or size_bytes <= 0:
        raise WhisperManifestError(f"Whisper model {model_key!r} has an invalid size_bytes.")

    official_url = raw_model["official_url"]
    filename = raw_model["filename"]
    _validate_official_url(official_url, filename, sha256, model_key)

    return WhisperModelSpec(
        model_key=model_key,
        display_name=raw_model["display_name"],
        multilingual=raw_model["multilingual"],
        japanese_supported=raw_model["japanese_supported"],
        official_url=official_url,
        filename=filename,
        sha256=sha256,
        size_bytes=size_bytes,
        vram_hint=raw_model["vram_hint"],
        speed_hint=raw_model["speed_hint"],
        recommended_use=raw_model["recommended_use"],
    )


def _validate_official_url(url: str, filename: str, sha256: str, model_key: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != _OFFICIAL_MODEL_HOST
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise WhisperManifestError(f"Whisper model {model_key!r} URL is not an official HTTPS URL.")
    if not parsed.path.startswith(_OFFICIAL_MODEL_PATH_PREFIX):
        raise WhisperManifestError(f"Whisper model {model_key!r} URL path is not official.")
    path_parts = parsed.path.split("/")
    if len(path_parts) != 6 or path_parts[:4] != ["", "main", "whisper", "models"]:
        raise WhisperManifestError(f"Whisper model {model_key!r} URL path is invalid.")
    if path_parts[4] != sha256:
        raise WhisperManifestError(f"Whisper model {model_key!r} URL hash does not match SHA256.")
    if PurePosixPath(parsed.path).name != filename:
        raise WhisperManifestError(f"Whisper model {model_key!r} URL filename does not match filename.")


def _require_exact_keys(document: Mapping[str, Any], expected_keys: set[str], label: str) -> None:
    actual_keys = set(document)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unknown = sorted(actual_keys - expected_keys)
        detail = []
        if missing:
            detail.append(f"missing={missing}")
        if unknown:
            detail.append(f"unknown={unknown}")
        raise WhisperManifestError(f"Invalid {label} keys ({', '.join(detail)}).")
