from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import tomllib

_APP_PACKAGE_NAMES: tuple[str, ...] = ("mmd-autolip-tool",)


def resolve_installed_version(package_names: Sequence[str]) -> str | None:
    for package_name in package_names:
        try:
            return package_version(package_name)
        except PackageNotFoundError:
            continue
    return None


def resolve_pyproject_version(pyproject_path: Path | None = None) -> str | None:
    target_path = pyproject_path or Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        with target_path.open("rb") as fh:
            parsed = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return None

    project = parsed.get("project")
    if not isinstance(project, dict):
        return None

    version = project.get("version")
    if not isinstance(version, str):
        return None

    stripped = version.strip()
    if not stripped:
        return None
    return stripped


def resolve_app_version() -> str | None:
    installed_version = resolve_installed_version(_APP_PACKAGE_NAMES)
    if installed_version:
        return installed_version
    return resolve_pyproject_version()


def format_app_version_display(
    version: str | None,
    *,
    fallback: str = "Ver. ?",
) -> str:
    if version:
        return f"Ver. {version}"
    return fallback
