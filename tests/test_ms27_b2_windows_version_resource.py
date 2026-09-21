from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app_version import resolve_pyproject_version
from PyInstaller.utils.win32.versioninfo import (
    VarFileInfo,
    VSVersionInfo,
    load_version_info_from_text_file,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERSION_RESOURCE = REPOSITORY_ROOT / "MMD_AutoLipTool.version.txt"
SPEC_FILE = REPOSITORY_ROOT / "MMD_AutoLipTool.spec"


def _version_parts(most_significant: int, least_significant: int) -> tuple[int, int, int, int]:
    return (
        most_significant >> 16,
        most_significant & 0xFFFF,
        least_significant >> 16,
        least_significant & 0xFFFF,
    )


def _string_values(info: VSVersionInfo) -> tuple[str, dict[str, str]]:
    string_file_infos = [kid for kid in info.kids if getattr(kid, "name", None) == "StringFileInfo"]
    if len(string_file_infos) != 1:
        raise AssertionError(f"expected one StringFileInfo, got {len(string_file_infos)}")
    tables = string_file_infos[0].kids
    if len(tables) != 1:
        raise AssertionError(f"expected one StringTable, got {len(tables)}")
    return tables[0].name, {item.name: item.val for item in tables[0].kids}


def _translation_values(info: VSVersionInfo) -> list[int]:
    var_file_infos = [kid for kid in info.kids if isinstance(kid, VarFileInfo)]
    if len(var_file_infos) != 1:
        raise AssertionError(f"expected one VarFileInfo, got {len(var_file_infos)}")
    translations = [item for item in var_file_infos[0].kids if item.name == "Translation"]
    if len(translations) != 1:
        raise AssertionError(f"expected one Translation, got {len(translations)}")
    return translations[0].kids


class WindowsVersionResourceTests(unittest.TestCase):
    def test_resource_matches_project_version_and_round_trips(self) -> None:
        info = load_version_info_from_text_file(str(VERSION_RESOURCE))
        table_name, values = _string_values(info)

        self.assertEqual(resolve_pyproject_version(REPOSITORY_ROOT / "pyproject.toml"), "1.0.0")
        self.assertEqual(table_name, "040904B0")
        self.assertEqual(values["FileVersion"], "1.0.0")
        self.assertEqual(values["ProductVersion"], "1.0.0")
        self.assertEqual(values["OriginalFilename"], "MMD_AutoLipTool.exe")
        self.assertEqual(values["InternalName"], "MMD_AutoLipTool")
        self.assertEqual(values["ProductName"], "MMD_AutoLipTool")
        self.assertEqual(_version_parts(info.ffi.fileVersionMS, info.ffi.fileVersionLS), (1, 0, 0, 0))
        self.assertEqual(_version_parts(info.ffi.productVersionMS, info.ffi.productVersionLS), (1, 0, 0, 0))
        self.assertEqual(_translation_values(info), [1033, 1200])

        round_tripped = VSVersionInfo()
        round_tripped.fromRaw(info.toRaw())
        _, round_tripped_values = _string_values(round_tripped)
        self.assertEqual(round_tripped_values["FileVersion"], "1.0.0")
        self.assertEqual(round_tripped_values["ProductVersion"], "1.0.0")
        self.assertEqual(_version_parts(round_tripped.ffi.fileVersionMS, round_tripped.ffi.fileVersionLS), (1, 0, 0, 0))
        self.assertEqual(_version_parts(round_tripped.ffi.productVersionMS, round_tripped.ffi.productVersionLS), (1, 0, 0, 0))
        self.assertEqual(_translation_values(round_tripped), [1033, 1200])

    def test_spec_connects_fixed_resource_and_exe_name(self) -> None:
        spec_text = SPEC_FILE.read_text(encoding="utf-8")

        self.assertIn('version_file_path = project_root / "MMD_AutoLipTool.version.txt"', spec_text)
        self.assertIn("version=str(version_file_path)", spec_text)
        self.assertIn('name="MMD_AutoLipTool"', spec_text)
        self.assertIn('datas += [("pyproject.toml", ".")]', spec_text)


if __name__ == "__main__":
    unittest.main()
