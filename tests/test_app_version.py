from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app_version import (
    format_app_version_display,
    resolve_app_version,
    resolve_pyproject_version,
)


class AppVersionTests(unittest.TestCase):
    def test_resolve_app_version_uses_installed_package_lookup(self) -> None:
        with patch("app_version.resolve_installed_version", return_value="0.3.8.0") as mocked:
            version = resolve_app_version()

        self.assertEqual(version, "0.3.8.0")
        mocked.assert_called_once()

    def test_resolve_app_version_falls_back_to_pyproject_version(self) -> None:
        with (
            patch("app_version.resolve_installed_version", return_value=None),
            patch("app_version.resolve_pyproject_version", return_value="0.3.8.0") as mocked,
        ):
            version = resolve_app_version()

        self.assertEqual(version, "0.3.8.0")
        mocked.assert_called_once()

    def test_resolve_pyproject_version_reads_project_version(self) -> None:
        version = resolve_pyproject_version(Path(__file__).resolve().parents[1] / "pyproject.toml")
        self.assertEqual(version, "0.3.8.0")

    def test_format_app_version_display_uses_ver_prefix(self) -> None:
        self.assertEqual(
            format_app_version_display("0.3.8.0"),
            "Ver. 0.3.8.0",
        )

    def test_format_app_version_display_uses_fallback_when_missing(self) -> None:
        self.assertEqual(
            format_app_version_display(None, fallback="Ver. ?"),
            "Ver. ?",
        )


if __name__ == "__main__":
    unittest.main()
