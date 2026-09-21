from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core.generation_presets import (
    BUILTIN_LONG_VOWEL_DECAY_ID,
    BUILTIN_LONG_VOWEL_DECAY_NAME,
    BUILTIN_STANDARD_HOLD_ID,
    BUILTIN_STANDARD_HOLD_NAME,
    MAX_USER_PRESETS,
    GenerationPresetStore,
    GenerationSettings,
    PresetContractError,
    get_builtin_presets,
)
from src.core.settings_store import SettingsStore
from tests.helpers import workspace_tempdir


class GenerationSettingsContractTests(unittest.TestCase):
    def test_default_and_boundary_values_are_accepted(self) -> None:
        self.assertEqual(GenerationSettings(), GenerationSettings(0, 0, "hold"))
        self.assertEqual(
            GenerationSettings(100, 100, "decay"),
            GenerationSettings(closing_hold_frames=100, closing_softness_frames=100, long_vowel_mode="decay"),
        )

    def test_invalid_types_ranges_and_mode_are_rejected(self) -> None:
        invalid_values = (
            {"closing_hold_frames": -1},
            {"closing_hold_frames": 101},
            {"closing_hold_frames": True},
            {"closing_hold_frames": 1.0},
            {"closing_softness_frames": -1},
            {"closing_softness_frames": 101},
            {"closing_softness_frames": False},
            {"closing_softness_frames": "1"},
            {"long_vowel_mode": "invalid"},
        )
        for overrides in invalid_values:
            values = GenerationSettings().to_dict()
            values.update(overrides)
            with self.subTest(overrides=overrides):
                with self.assertRaises(PresetContractError):
                    GenerationSettings.from_dict(values)

    def test_json_contract_is_strict(self) -> None:
        values = GenerationSettings().to_dict()
        values["unexpected"] = 1
        with self.assertRaises(PresetContractError):
            GenerationSettings.from_dict(values)

    def test_dataclass_is_immutable(self) -> None:
        settings = GenerationSettings()
        with self.assertRaises(AttributeError):
            settings.long_vowel_mode = "decay"  # type: ignore[misc]


class GenerationPresetStoreTests(unittest.TestCase):
    @staticmethod
    def _settings(
        closing_hold_frames: int = 2,
        closing_softness_frames: int = 3,
        long_vowel_mode: str = "hold",
    ) -> GenerationSettings:
        return GenerationSettings(closing_hold_frames, closing_softness_frames, long_vowel_mode)

    @staticmethod
    def _valid_entry(
        preset_id: str = "11111111-1111-4111-8111-111111111111",
        display_name: str = "ユーザー設定",
        settings: GenerationSettings | None = None,
    ) -> dict[str, object]:
        return {
            "id": preset_id,
            "display_name": display_name,
            "generation_settings": (settings or GenerationSettings()).to_dict(),
        }

    @staticmethod
    def _write_payload(path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _store(self, tmp_dir: Path) -> GenerationPresetStore:
        return GenerationPresetStore(settings_path=tmp_dir / "MMD_AutoLipTool.ini")

    def test_builtins_are_fixed_and_not_serialized(self) -> None:
        builtins = get_builtin_presets()
        self.assertEqual(
            [(preset.id, preset.display_name) for preset in builtins],
            [
                (BUILTIN_STANDARD_HOLD_ID, BUILTIN_STANDARD_HOLD_NAME),
                (BUILTIN_LONG_VOWEL_DECAY_ID, BUILTIN_LONG_VOWEL_DECAY_NAME),
            ],
        )
        self.assertEqual(builtins[0].generation_settings, GenerationSettings())
        self.assertEqual(builtins[1].generation_settings, GenerationSettings(long_vowel_mode="decay"))
        with self.assertRaises(PresetContractError):
            builtins[0].to_json_dict()
        with self.assertRaises(TypeError):
            builtins[0] = builtins[1]  # type: ignore[index]

    def test_missing_file_loads_builtins_and_allows_mutation(self) -> None:
        with workspace_tempdir("ms22_b3_missing") as tmp_dir:
            store = self._store(tmp_dir)
            result = store.load()
            self.assertFalse(result.file_exists)
            self.assertTrue(result.mutation_available)
            self.assertEqual(result.user_presets, ())
            self.assertEqual(len(result.built_in_presets), 2)

    def test_create_round_trip_and_json_excludes_source(self) -> None:
        with workspace_tempdir("ms22_b3_roundtrip") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            result = store.create("  ユーザー設定  ", self._settings())
            self.assertTrue(result.succeeded)
            self.assertEqual(result.user_presets[0].display_name, "ユーザー設定")
            UUID(result.user_presets[0].id)
            self.assertEqual(result.user_presets[0].source, "user")

            payload = json.loads(store.presets_path.read_text(encoding="utf-8"))
            self.assertEqual(set(payload), {"schema_version", "user_presets"})
            self.assertEqual(set(payload["user_presets"][0]), {"id", "display_name", "generation_settings"})
            self.assertNotIn("source", payload["user_presets"][0])

            reloaded = self._store(tmp_dir)
            load_result = reloaded.load()
            self.assertTrue(load_result.mutation_available)
            self.assertEqual(load_result.user_presets, result.user_presets)

    def test_strict_invalid_files_fail_closed_without_partial_import(self) -> None:
        invalid_payloads: tuple[tuple[object, str], ...] = (
            ({"schema_version": 0, "user_presets": []}, "unsupported_schema"),
            ({"schema_version": 2, "user_presets": []}, "unsupported_schema"),
            ({"schema_version": 1}, "invalid_schema"),
            ({"schema_version": 1, "user_presets": [], "extra": 1}, "invalid_schema"),
            ({"schema_version": 1, "user_presets": [{}]}, "invalid_schema"),
            ({"schema_version": 1, "user_presets": [self._valid_entry() | {"extra": 1}]}, "invalid_schema"),
            ({"schema_version": 1, "user_presets": [self._valid_entry() | {"id": "not-a-uuid"}]}, "invalid_schema"),
            ({"schema_version": 1, "user_presets": [self._valid_entry() | {"display_name": "\n"}]}, "invalid_schema"),
            ({"schema_version": 1, "user_presets": [self._valid_entry(), self._valid_entry()]}, "duplicate_id"),
            (
                {"schema_version": 1, "user_presets": [self._valid_entry(display_name=BUILTIN_STANDARD_HOLD_NAME)]},
                "duplicate_display_name",
            ),
        )
        with workspace_tempdir("ms22_b3_invalid") as tmp_dir:
            store = self._store(tmp_dir)
            for payload, error_code in invalid_payloads:
                self._write_payload(store.presets_path, payload)
                result = store.load()
                with self.subTest(error_code=error_code, payload=payload):
                    self.assertFalse(result.mutation_available)
                    self.assertEqual(result.error_code, error_code)
                    self.assertEqual(result.user_presets, ())
                    self.assertEqual(len(result.built_in_presets), 2)

    def test_json_preset_limit_is_strict(self) -> None:
        with workspace_tempdir("ms22_b3_json_limit") as tmp_dir:
            store = self._store(tmp_dir)
            entries = [
                self._valid_entry(
                    preset_id=f"00000000-0000-4000-8000-{index:012d}",
                    display_name=f"設定{index}",
                )
                for index in range(MAX_USER_PRESETS + 1)
            ]
            self._write_payload(store.presets_path, {"schema_version": 1, "user_presets": entries})
            result = store.load()
            self.assertFalse(result.mutation_available)
            self.assertEqual(result.error_code, "limit_exceeded")
            self.assertEqual(result.user_presets, ())

    def test_malformed_json_and_unavailable_mutations_preserve_file(self) -> None:
        with workspace_tempdir("ms22_b3_malformed") as tmp_dir:
            store = self._store(tmp_dir)
            store.presets_path.parent.mkdir(parents=True, exist_ok=True)
            store.presets_path.write_text("{broken", encoding="utf-8")
            load_result = store.load()
            self.assertEqual(load_result.error_code, "invalid_json")
            before = store.presets_path.read_bytes()

            mutation = store.create("設定", self._settings())
            self.assertFalse(mutation.succeeded)
            self.assertEqual(mutation.error_code, "store_unavailable")
            self.assertEqual(store.presets_path.read_bytes(), before)

    def test_external_repair_recovers_on_next_load(self) -> None:
        with workspace_tempdir("ms22_b3_repair") as tmp_dir:
            store = self._store(tmp_dir)
            store.presets_path.parent.mkdir(parents=True, exist_ok=True)
            store.presets_path.write_text("{broken", encoding="utf-8")
            self.assertFalse(store.load().mutation_available)

            entry = self._valid_entry(settings=self._settings(4, 5, "decay"))
            self._write_payload(store.presets_path, {"schema_version": 1, "user_presets": [entry]})
            result = store.load()
            self.assertTrue(result.mutation_available)
            self.assertEqual(len(result.user_presets), 1)
            self.assertEqual(result.user_presets[0].generation_settings.long_vowel_mode, "decay")

    def test_create_update_delete_and_boundaries(self) -> None:
        with workspace_tempdir("ms22_b3_mutation") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            first = store.create("一件目", self._settings(), preset_id="11111111-1111-4111-8111-111111111111")
            self.assertTrue(first.succeeded)
            stable_id = first.user_presets[0].id
            same_name = store.update(stable_id, "一件目", self._settings(9, 8, "decay"))
            self.assertTrue(same_name.succeeded)
            self.assertEqual(same_name.user_presets[0].id, stable_id)
            self.assertEqual(same_name.user_presets[0].generation_settings.long_vowel_mode, "decay")
            duplicate = store.create("一件目", self._settings())
            self.assertFalse(duplicate.succeeded)
            self.assertEqual(duplicate.error_code, "duplicate_display_name")
            self.assertEqual(store.update(BUILTIN_STANDARD_HOLD_ID, "別名", self._settings()).error_code, "builtin_read_only")
            self.assertEqual(store.delete(BUILTIN_STANDARD_HOLD_ID).error_code, "builtin_read_only")
            self.assertTrue(store.delete(stable_id).succeeded)
            self.assertEqual(store.user_presets, ())

            for index in range(MAX_USER_PRESETS):
                result = store.create(f"設定{index}", self._settings())
                self.assertTrue(result.succeeded, msg=f"failed at index {index}: {result.error_code}")
            before = store.presets_path.read_bytes()
            over_limit = store.create("設定101", self._settings())
            self.assertFalse(over_limit.succeeded)
            self.assertEqual(over_limit.error_code, "limit_exceeded")
            self.assertEqual(store.presets_path.read_bytes(), before)

    def test_invalid_user_input_does_not_mutate_collection(self) -> None:
        with workspace_tempdir("ms22_b3_invalid_input") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            before = store.user_presets
            self.assertEqual(store.create("", self._settings()).error_code, "invalid_input")
            self.assertEqual(store.create("設定", self._settings(), preset_id="ABC").error_code, "invalid_input")
            self.assertEqual(store.create("空ID", self._settings(), preset_id="").error_code, "invalid_input")
            self.assertEqual(store.user_presets, before)

    def test_display_name_length_boundaries_are_enforced(self) -> None:
        with workspace_tempdir("ms22_b3_display_name_bounds") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            one_character = store.create("a", self._settings())
            self.assertTrue(one_character.succeeded)
            hundred_characters = store.create("b" * 100, self._settings())
            self.assertTrue(hundred_characters.succeeded)
            over_limit = store.create("c" * 101, self._settings())
            self.assertFalse(over_limit.succeeded)
            self.assertEqual(over_limit.error_code, "invalid_input")
            self.assertEqual(len(store.user_presets), 2)

    def test_write_failure_preserves_old_file_and_enters_unavailable(self) -> None:
        with workspace_tempdir("ms22_b3_write_failure") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            self.assertTrue(store.create("既存", self._settings()).succeeded)
            before = store.presets_path.read_bytes()
            with patch("src.core.generation_presets.os.replace", side_effect=OSError("replace failed")):
                failed = store.create("新規", self._settings())
            self.assertFalse(failed.succeeded)
            self.assertEqual(failed.error_code, "replace_failed")
            self.assertEqual(failed.user_presets[0].display_name, "既存")
            self.assertEqual(store.presets_path.read_bytes(), before)
            self.assertEqual(list(store.presets_path.parent.glob("mmd_autoliptool_presets_*.tmp")), [])
            self.assertEqual(store.create("再試行", self._settings()).error_code, "store_unavailable")

    def test_write_failure_cleans_temp_and_preserves_missing_file(self) -> None:
        with workspace_tempdir("ms22_b3_write_failure_missing") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            with patch(
                "src.core.generation_presets.json.dump",
                side_effect=OSError("write failed"),
            ):
                failed = store.create("設定", self._settings())
            self.assertFalse(failed.succeeded)
            self.assertEqual(failed.error_code, "write_failed")
            self.assertFalse(store.presets_path.exists())
            self.assertEqual(store.user_presets, ())
            self.assertEqual(list(store.presets_path.parent.glob("mmd_autoliptool_presets_*.tmp")), [])

    def test_atomic_replace_uses_closed_same_directory_temp_file(self) -> None:
        with workspace_tempdir("ms22_b3_atomic_contract") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            captured: dict[str, Path] = {}
            real_replace = os.replace

            def replace_and_probe(source: str | Path, destination: str | Path) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                captured["source"] = source_path
                captured["destination"] = destination_path
                self.assertEqual(source_path.resolve().parent, destination_path.resolve().parent)
                with source_path.open("r", encoding="utf-8") as handle:
                    self.assertIn('"schema_version": 1', handle.read())
                real_replace(source_path, destination_path)

            with patch(
                "src.core.generation_presets.os.replace",
                side_effect=replace_and_probe,
            ):
                result = store.create("設定", self._settings())

            self.assertTrue(result.succeeded)
            self.assertEqual(
                captured["source"].resolve().parent,
                store.presets_path.resolve().parent,
            )
            self.assertEqual(captured["destination"], store.presets_path)

    def test_active_resolution_keeps_ini_settings_for_custom(self) -> None:
        with workspace_tempdir("ms22_b3_resolution") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            builtin_settings = GenerationSettings(long_vowel_mode="decay")
            builtin = store.resolve_active(builtin_settings, BUILTIN_LONG_VOWEL_DECAY_ID)
            self.assertEqual(builtin.generation_settings, builtin_settings)
            self.assertEqual(builtin.active_preset_id, BUILTIN_LONG_VOWEL_DECAY_ID)
            self.assertEqual(builtin.active_preset_display_name, BUILTIN_LONG_VOWEL_DECAY_NAME)
            self.assertEqual(builtin.source, "built_in")

            settings = self._settings(6, 7, "decay")
            mismatch = store.resolve_active(settings, BUILTIN_STANDARD_HOLD_ID)
            self.assertEqual(mismatch.generation_settings, settings)
            self.assertIsNone(mismatch.active_preset_id)
            self.assertEqual(mismatch.source, "custom")
            unknown = store.resolve_active(settings, "unknown")
            self.assertEqual(unknown.source, "custom")
            missing = store.resolve_active(settings, None)
            self.assertEqual(missing.source, "custom")

            user_result = store.create("ユーザー", settings)
            user = store.resolve_active(settings, user_result.user_presets[0].id)
            self.assertEqual(user.source, "user")
            self.assertEqual(user.active_preset_display_name, "ユーザー")

    def test_builtin_resolution_survives_invalid_user_json(self) -> None:
        with workspace_tempdir("ms22_b3_builtin_resolution") as tmp_dir:
            store = self._store(tmp_dir)
            store.presets_path.parent.mkdir(parents=True, exist_ok=True)
            store.presets_path.write_text("{broken", encoding="utf-8")
            store.load()
            result = store.resolve_active(GenerationSettings(), BUILTIN_STANDARD_HOLD_ID)
            self.assertEqual(result.source, "built_in")
            self.assertEqual(result.active_preset_id, BUILTIN_STANDARD_HOLD_ID)


class SettingsStoreGenerationBoundaryTests(unittest.TestCase):
    def test_defaults_and_invalid_generation_values(self) -> None:
        defaults = SettingsStore.default_settings()
        self.assertEqual(defaults["long_vowel_mode"], "hold")
        self.assertIsNone(defaults["active_preset_id"])
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {
                "closing_hold_frames": 101,
                "closing_softness_frames": True,
                "long_vowel_mode": "invalid",
                "active_preset_id": 123,
            }
        )
        self.assertEqual(normalized["closing_hold_frames"], 0)
        self.assertEqual(normalized["closing_softness_frames"], 0)
        self.assertEqual(normalized["long_vowel_mode"], "hold")
        self.assertIsNone(normalized["active_preset_id"])
        for key in ("closing_hold_frames", "closing_softness_frames", "long_vowel_mode", "active_preset_id"):
            self.assertIn(key, invalid_keys)
            self.assertIn(key, used_default_keys)

    def test_generation_settings_and_active_id_round_trip(self) -> None:
        with workspace_tempdir("ms22_b3_settings") as tmp_dir:
            settings_path = tmp_dir / "MMD_AutoLipTool.ini"
            store = SettingsStore(settings_path)
            settings = SettingsStore.default_settings()
            settings.update(
                {
                    "closing_hold_frames": 100,
                    "closing_softness_frames": 99,
                    "long_vowel_mode": "decay",
                    "active_preset_id": "11111111-1111-4111-8111-111111111111",
                }
            )
            self.assertTrue(store.save(settings).succeeded)
            loaded = store.load().settings
            self.assertEqual(loaded["closing_hold_frames"], 100)
            self.assertEqual(loaded["closing_softness_frames"], 99)
            self.assertEqual(loaded["long_vowel_mode"], "decay")
            self.assertEqual(loaded["active_preset_id"], "11111111-1111-4111-8111-111111111111")

            settings["active_preset_id"] = None
            self.assertTrue(store.save(settings).succeeded)
            self.assertIsNone(store.load().settings["active_preset_id"])
            ini_text = settings_path.read_text(encoding="utf-8")
            self.assertIn("active_preset_id =", ini_text)

    def test_legacy_caller_omitting_generation_keys_preserves_existing_values(self) -> None:
        with workspace_tempdir("ms22_b3_legacy_settings") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            initial = SettingsStore.default_settings()
            initial.update(
                {
                    "closing_hold_frames": 8,
                    "closing_softness_frames": 9,
                    "long_vowel_mode": "decay",
                    "active_preset_id": "11111111-1111-4111-8111-111111111111",
                }
            )
            self.assertTrue(store.save(initial).succeeded)
            self.assertTrue(store.save({"theme": "light"}).succeeded)
            loaded = store.load().settings
            self.assertEqual(loaded["theme"], "light")
            self.assertEqual(loaded["closing_hold_frames"], 8)
            self.assertEqual(loaded["closing_softness_frames"], 9)
            self.assertEqual(loaded["long_vowel_mode"], "decay")
            self.assertEqual(loaded["active_preset_id"], "11111111-1111-4111-8111-111111111111")

    def test_none_save_also_preserves_existing_generation_values(self) -> None:
        with workspace_tempdir("ms22_b3_none_settings") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            initial = SettingsStore.default_settings()
            initial.update({"long_vowel_mode": "decay", "active_preset_id": "preset"})
            self.assertTrue(store.save(initial).succeeded)
            self.assertTrue(store.save(None).succeeded)
            loaded = store.load().settings
            self.assertEqual(loaded["long_vowel_mode"], "decay")
            self.assertEqual(loaded["active_preset_id"], "preset")


if __name__ == "__main__":
    unittest.main()
