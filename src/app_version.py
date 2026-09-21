from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import tomllib

from resource_utils import get_resource_path

_APP_PACKAGE_NAMES: tuple[str, ...] = ("mmd-autolip-tool",)
_APP_PROJECT_NAME = "mmd-autolip-tool"


def resolve_installed_version(package_names: Sequence[str]) -> str | None:
    for package_name in package_names:
        try:
            return package_version(package_name)
        except PackageNotFoundError:
            continue
    return None


def _candidate_pyproject_paths(pyproject_path: Path | None = None) -> tuple[Path, ...]:
    if pyproject_path is not None:
        return (pyproject_path,)

    return (get_resource_path("pyproject.toml"),)


def resolve_pyproject_version(pyproject_path: Path | None = None) -> str | None:
    require_app_identity = pyproject_path is None
    for target_path in _candidate_pyproject_paths(pyproject_path):
        try:
            with target_path.open("rb") as fh:
                parsed = tomllib.load(fh)
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue

        project = parsed.get("project")
        if not isinstance(project, dict):
            continue
        if require_app_identity and project.get("name") != _APP_PROJECT_NAME:
            continue

        version = project.get("version")
        if not isinstance(version, str):
            continue

        stripped = version.strip()
        if stripped:
            return stripped
    return None


def resolve_app_version() -> str | None:
    installed_version = resolve_installed_version(_APP_PACKAGE_NAMES)
    project_version = resolve_pyproject_version()
    if project_version:
        return project_version
    return installed_version


def format_app_version_display(
    version: str | None,
    *,
    fallback: str = "Ver. ?",
) -> str:
    if version:
        return f"Ver. {version}"
    return fallback
