from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app_version import (
    _candidate_pyproject_paths,
    format_app_version_display,
    resolve_app_version,
    resolve_pyproject_version,
)


class AppVersionTests(unittest.TestCase):
    def test_resolve_app_version_prefers_project_over_stale_installed_metadata(self) -> None:
        with patch("app_version.resolve_installed_version", return_value="0.4.0.0") as mocked:
            version = resolve_app_version()

        self.assertEqual(version, "1.0.0")
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
        self.assertEqual(version, "1.0.0")

    def test_resolve_app_version_uses_frozen_project_resource(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_root = Path(temp_dir)
            (bundle_root / "pyproject.toml").write_text(
                '[project]\nname = "mmd-autolip-tool"\nversion = "1.0.0"\n',
                encoding="utf-8",
            )
            with (
                patch.object(sys, "_MEIPASS", str(bundle_root), create=True),
                patch("app_version.resolve_installed_version", return_value="0.4.0.0"),
            ):
                version = resolve_app_version()

        self.assertEqual(version, "1.0.0")

    def test_implicit_project_resource_rejects_other_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_root = Path(temp_dir)
            (bundle_root / "pyproject.toml").write_text(
                '[project]\nname = "another-project"\nversion = "9.9.9"\n',
                encoding="utf-8",
            )
            with (
                patch.object(sys, "_MEIPASS", str(bundle_root), create=True),
                patch("app_version.resolve_installed_version", return_value="0.3.8.0"),
            ):
                version = resolve_app_version()

        self.assertEqual(version, "0.3.8.0")

    def test_explicit_project_path_keeps_generic_version_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "pyproject.toml"
            project_path.write_text('[project]\nversion = "0.3.8.0"\n', encoding="utf-8")
            version = resolve_pyproject_version(project_path)

        self.assertEqual(version, "0.3.8.0")

    def test_invalid_utf8_project_path_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "pyproject.toml"
            project_path.write_bytes(b"[project]\nversion = \"1.0.0\"\n\xff")
            version = resolve_pyproject_version(project_path)

        self.assertIsNone(version)

    def test_candidate_pyproject_paths_prioritize_explicit_path(self) -> None:
        explicit = Path("custom_pyproject.toml")
        self.assertEqual(_candidate_pyproject_paths(explicit), (explicit,))

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
