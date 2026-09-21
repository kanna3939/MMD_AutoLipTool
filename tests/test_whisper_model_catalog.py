from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core import whisper_models
from src.core.whisper_models import (
    EXPECTED_WHISPER_VERSION,
    SUPPORTED_MODEL_KEYS,
    WhisperManifestError,
    load_whisper_model_catalog,
    parse_whisper_model_manifest,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "src" / "core" / "whisper_models.json"


class _FakeManifestResource:
    def __init__(self, manifest_bytes: bytes) -> None:
        self.manifest_bytes = manifest_bytes
        self.requested_name: str | None = None

    def joinpath(self, name: str) -> _FakeManifestResource:
        self.requested_name = name
        return self

    def read_bytes(self) -> bytes:
        return self.manifest_bytes


class WhisperModelCatalogTests(unittest.TestCase):
    def test_source_package_relative_resource_loads_exact_catalog(self) -> None:
        catalog = load_whisper_model_catalog()

        self.assertEqual(catalog.schema_version, 1)
        self.assertEqual(catalog.openai_whisper_version, EXPECTED_WHISPER_VERSION)
        self.assertEqual(catalog.default_model_key, "small")
        self.assertEqual(tuple(spec.model_key for spec in catalog.models), SUPPORTED_MODEL_KEYS)
        self.assertEqual(catalog.get("turbo").filename, "large-v3-turbo.pt")

    def test_resource_loader_uses_package_relative_frozen_boundary(self) -> None:
        manifest_bytes = MANIFEST_PATH.read_bytes()
        fake_resource = _FakeManifestResource(manifest_bytes)

        with patch.object(whisper_models.resources, "files", return_value=fake_resource) as files:
            catalog = load_whisper_model_catalog()

        files.assert_called_once_with("src.core")
        self.assertEqual(fake_resource.requested_name, "whisper_models.json")
        self.assertEqual(catalog.default_model_key, "small")

    def test_exact_metadata_and_manifest_identity(self) -> None:
        catalog = load_whisper_model_catalog()
        expected = {
            "small": (
                "small.pt",
                483617219,
                "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794",
            ),
            "medium": (
                "medium.pt",
                1528008539,
                "345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1",
            ),
            "turbo": (
                "large-v3-turbo.pt",
                1617941637,
                "aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a",
            ),
        }

        for model_key, (filename, size_bytes, sha256) in expected.items():
            with self.subTest(model_key=model_key):
                spec = catalog.get(model_key)
                self.assertEqual(spec.filename, filename)
                self.assertEqual(spec.size_bytes, size_bytes)
                self.assertEqual(spec.sha256, sha256)
                self.assertEqual(
                    catalog.manifest_identity(model_key),
                    f"whisper-manifest-v1:20250625:{model_key}:{sha256}",
                )

    def test_installed_package_data_and_pyinstaller_mapping_are_static_contracts(self) -> None:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        spec = (REPOSITORY_ROOT / "MMD_AutoLipTool.spec").read_text(encoding="utf-8")

        self.assertIn("[tool.setuptools.package-data]", pyproject)
        self.assertIn('core = ["whisper_models.json"]', pyproject)
        self.assertIn('("src/core/whisper_models.json", "src/core")', spec)
        self.assertNotIn(".pt", spec)

    def test_pyinstaller_excludes_retired_gui_bindings_and_broad_backend_collection(self) -> None:
        spec = (REPOSITORY_ROOT / "MMD_AutoLipTool.spec").read_text(encoding="utf-8")
        torch_hook = (REPOSITORY_ROOT / "build_hooks" / "hook-torch.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn('collect_submodules("matplotlib.backends")', spec)
        self.assertNotIn('collect_data_files("tiktoken")', spec)
        self.assertNotIn('collect_data_files("tiktoken_ext")', spec)
        self.assertIn('path.name not in {".gitkeep", "ffplay.exe"}', spec)
        self.assertIn("excludes=excluded_modules", spec)
        self.assertIn('hookspath=["build_hooks"]', spec)
        self.assertNotIn('collect_submodules("torch")', torch_hook)
        for module_name in (
            "matplotlib",
            "PySide6",
            "PySide6_Addons",
            "PySide6_Essentials",
            "shiboken6",
            "PySide2",
            "PyQt5",
            "PyQt6",
            "torch.fx.passes.tests",
            "torch.utils.tensorboard",
            "numba.np.ufunc.tbbpool",
        ):
            with self.subTest(module_name=module_name):
                self.assertIn(f'    "{module_name}",', spec)

    def test_manifest_rejects_unknown_keys_and_invalid_metadata(self) -> None:
        cases = []

        def add_root_key(document: dict) -> None:
            document["unexpected"] = True

        def add_entry_key(document: dict) -> None:
            document["models"][0]["unexpected"] = True

        def set_unsupported_model_key(document: dict) -> None:
            document["models"][0]["model_key"] = "small.en"

        def set_external_url(document: dict) -> None:
            document["models"][0]["official_url"] = "https://example.com/small.pt"

        def set_hash_mismatch(document: dict) -> None:
            document["models"][0]["sha256"] = "0" * 64

        def set_invalid_size(document: dict) -> None:
            document["models"][0]["size_bytes"] = True

        def duplicate_model_key(document: dict) -> None:
            document["models"][1]["model_key"] = "small"

        cases.extend(
            [
                ("unknown root key", add_root_key),
                ("unknown entry key", add_entry_key),
                ("unsupported model key", set_unsupported_model_key),
                ("external URL", set_external_url),
                ("hash mismatch", set_hash_mismatch),
                ("invalid size", set_invalid_size),
                ("duplicate model key", duplicate_model_key),
            ]
        )
        source_document = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        for label, mutate in cases:
            with self.subTest(label=label):
                document = copy.deepcopy(source_document)
                mutate(document)
                with self.assertRaises(WhisperManifestError):
                    parse_whisper_model_manifest(document)

    def test_manifest_rejects_wrong_schema_version_and_model_order(self) -> None:
        document = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        document["schema_version"] = 2
        with self.assertRaises(WhisperManifestError):
            parse_whisper_model_manifest(document)

        document = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        document["models"].reverse()
        with self.assertRaises(WhisperManifestError):
            parse_whisper_model_manifest(document)


if __name__ == "__main__":
    unittest.main()
