from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core.model_profiles import (
    MAX_USER_PROFILES,
    ModelProfile,
    ModelProfileStore,
    ProfileContractError,
    ProfileGenerationOverrides,
)
from src.core.morph_name_sets import JAPANESE_MORPH_NAME_SET_ID, LATIN_MORPH_NAME_SET_ID
from src.core.settings_store import SettingsStore
from tests.helpers import workspace_tempdir


PROFILE_ID = "11111111-1111-4111-8111-111111111111"
PROFILE_ID_2 = "22222222-2222-4222-8222-222222222222"
USER_PRESET_ID = "33333333-3333-4333-8333-333333333333"


class ProfileGenerationOverridesContractTests(unittest.TestCase):
    def test_nullable_values_and_boundaries_are_accepted(self) -> None:
        self.assertEqual(ProfileGenerationOverrides(), ProfileGenerationOverrides(None, None, None))
        self.assertEqual(
            ProfileGenerationOverrides(100, 0, "decay"),
            ProfileGenerationOverrides(
                closing_hold_frames=100,
                closing_softness_frames=0,
                long_vowel_mode="decay",
            ),
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
            values = ProfileGenerationOverrides().to_dict()
            values.update(overrides)
            with self.subTest(overrides=overrides):
                with self.assertRaises(ProfileContractError):
                    ProfileGenerationOverrides.from_dict(values)

    def test_dataclass_is_immutable(self) -> None:
        overrides = ProfileGenerationOverrides()
        with self.assertRaises(AttributeError):
            overrides.long_vowel_mode = "decay"  # type: ignore[misc]


class ModelProfileContractTests(unittest.TestCase):
    @staticmethod
    def _profile(**overrides: object) -> ModelProfile:
        values: dict[str, object] = {
            "id": PROFILE_ID,
            "display_name": "標準モデル",
            "morph_name_set_id": JAPANESE_MORPH_NAME_SET_ID,
            "morph_upper_limit": 0.5,
            "generation_overrides": ProfileGenerationOverrides(),
            "default_preset_id": "builtin:standard-hold",
        }
        values.update(overrides)
        return ModelProfile(**values)  # type: ignore[arg-type]

    def test_valid_profile_is_immutable_and_serializes_exactly(self) -> None:
        profile = self._profile()
        self.assertEqual(
            set(profile.to_json_dict()),
            {
                "id",
                "display_name",
                "morph_name_set_id",
                "morph_upper_limit",
                "generation_overrides",
                "default_preset_id",
            },
        )
        with self.assertRaises(AttributeError):
            profile.display_name = "別名"  # type: ignore[misc]

    def test_strict_upper_limit_and_morph_reference_contract(self) -> None:
        invalid_values = (True, 0, "0.5", float("nan"), float("inf"), -0.1, 10.1)
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ProfileContractError):
                    self._profile(morph_upper_limit=value)

        with self.assertRaises(ProfileContractError):
            self._profile(morph_name_set_id="builtin:unknown")
        self.assertEqual(
            self._profile(morph_name_set_id=LATIN_MORPH_NAME_SET_ID).morph_name_set_id,
            LATIN_MORPH_NAME_SET_ID,
        )

    def test_profile_reference_and_name_validation_is_strict(self) -> None:
        for value in ("", " preset", "preset ", "builtin:", "not-a-uuid"):
            with self.subTest(value=value):
                with self.assertRaises(ProfileContractError):
                    self._profile(default_preset_id=value)
        self.assertEqual(
            self._profile(default_preset_id=USER_PRESET_ID).default_preset_id,
            USER_PRESET_ID,
        )
        with self.assertRaises(ProfileContractError):
            self._profile(display_name="\n")

    def test_json_entry_key_set_is_strict(self) -> None:
        payload = self._profile().to_json_dict()
        with self.assertRaises(ProfileContractError):
            ModelProfile.from_dict(payload | {"unexpected": 1})
        overrides = dict(payload["generation_overrides"])
        with self.assertRaises(ProfileContractError):
            ModelProfile.from_dict(payload | {"generation_overrides": overrides | {"unexpected": 1}})


class ModelProfileStoreTests(unittest.TestCase):
    @staticmethod
    def _overrides(
        closing_hold_frames: int | None = 2,
        closing_softness_frames: int | None = 3,
        long_vowel_mode: str | None = "hold",
    ) -> ProfileGenerationOverrides:
        return ProfileGenerationOverrides(
            closing_hold_frames,
            closing_softness_frames,
            long_vowel_mode,
        )

    @classmethod
    def _valid_entry(
        cls,
        profile_id: str = PROFILE_ID,
        display_name: str = "標準モデル",
        morph_name_set_id: str = JAPANESE_MORPH_NAME_SET_ID,
        morph_upper_limit: float | None = 0.5,
        default_preset_id: str = "builtin:standard-hold",
    ) -> dict[str, object]:
        return {
            "id": profile_id,
            "display_name": display_name,
            "morph_name_set_id": morph_name_set_id,
            "morph_upper_limit": morph_upper_limit,
            "generation_overrides": cls._overrides().to_dict(),
            "default_preset_id": default_preset_id,
        }

    @staticmethod
    def _write_payload(path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _store(tmp_dir: Path, *, profiles_path: Path | None = None) -> ModelProfileStore:
        return ModelProfileStore(
            settings_path=tmp_dir / "MMD_AutoLipTool.ini",
            profiles_path=profiles_path,
        )

    def test_missing_file_is_writable_but_constructor_is_unloaded(self) -> None:
        with workspace_tempdir("ms23_b3_unloaded") as tmp_dir:
            store = self._store(tmp_dir)
            self.assertFalse(store.load_completed)
            self.assertFalse(store.mutation_available)
            self.assertEqual(store.create("未ロード", JAPANESE_MORPH_NAME_SET_ID, 0.5, self._overrides(), "builtin:standard-hold").error_code, "store_not_loaded")
            self.assertFalse(store.profiles_path.exists())
            with self.assertRaises(ProfileContractError):
                store.get_profile(PROFILE_ID)

            result = store.load()
            self.assertFalse(result.file_exists)
            self.assertTrue(result.mutation_available)
            self.assertEqual(result.user_profiles, ())

    def test_constructor_path_seams_and_mutual_exclusion(self) -> None:
        with workspace_tempdir("ms23_b3_paths") as tmp_dir:
            settings_path = tmp_dir / "config" / "MMD_AutoLipTool.ini"
            settings_store = SettingsStore(settings_path)
            injected = ModelProfileStore(settings_store=settings_store)
            self.assertEqual(injected.profiles_path, settings_path.parent / "profiles.json")

            explicit_path = tmp_dir / "custom" / "profiles.json"
            explicit = ModelProfileStore(settings_path=settings_path, profiles_path=explicit_path)
            self.assertEqual(explicit.profiles_path, explicit_path)

            with self.assertRaises(ValueError):
                ModelProfileStore(
                    settings_path=settings_path,
                    settings_store=settings_store,
                )

    def test_create_round_trip_and_json_keeps_only_stable_references(self) -> None:
        with workspace_tempdir("ms23_b3_roundtrip") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            result = store.create(
                "  標準モデル  ",
                JAPANESE_MORPH_NAME_SET_ID,
                0.5,
                self._overrides(),
                "builtin:standard-hold",
                profile_id=PROFILE_ID,
            )
            self.assertTrue(result.succeeded)
            self.assertEqual(result.user_profiles[0].display_name, "標準モデル")
            payload = json.loads(store.profiles_path.read_text(encoding="utf-8"))
            self.assertEqual(set(payload), {"schema_version", "user_profiles"})
            self.assertEqual(set(payload["user_profiles"][0]), set(self._valid_entry()))
            self.assertNotIn("generation_settings", payload["user_profiles"][0])

            reloaded = self._store(tmp_dir)
            self.assertEqual(reloaded.load().user_profiles, result.user_profiles)
            self.assertEqual(reloaded.get_profile(PROFILE_ID), result.user_profiles[0])

    def test_valid_missing_preset_reference_is_retained_for_b4(self) -> None:
        with workspace_tempdir("ms23_b3_dangling_reference") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            result = store.create(
                "未解決参照",
                JAPANESE_MORPH_NAME_SET_ID,
                None,
                self._overrides(None, None, None),
                USER_PRESET_ID,
            )
            self.assertTrue(result.succeeded)
            self.assertEqual(result.user_profiles[0].default_preset_id, USER_PRESET_ID)

    def test_invalid_files_fail_closed_without_partial_import(self) -> None:
        invalid_payloads: tuple[tuple[object, str], ...] = (
            ({"schema_version": True, "user_profiles": []}, "unsupported_schema"),
            ({"schema_version": 2, "user_profiles": []}, "unsupported_schema"),
            ({"schema_version": 1}, "invalid_schema"),
            ({"schema_version": 1, "user_profiles": [], "extra": 1}, "invalid_schema"),
            ({"schema_version": 1, "user_profiles": [{}]}, "invalid_schema"),
            ({"schema_version": 1, "user_profiles": [self._valid_entry() | {"extra": 1}]}, "invalid_schema"),
            ({"schema_version": 1, "user_profiles": [self._valid_entry(morph_upper_limit=0)]}, "invalid_schema"),
            ({"schema_version": 1, "user_profiles": [self._valid_entry(morph_name_set_id="builtin:unknown")]}, "invalid_schema"),
            ({"schema_version": 1, "user_profiles": [self._valid_entry(), self._valid_entry()]}, "duplicate_id"),
            ({"schema_version": 1, "user_profiles": [self._valid_entry(), self._valid_entry(profile_id=PROFILE_ID_2, display_name=" 標準モデル ")]}, "duplicate_display_name"),
        )
        with workspace_tempdir("ms23_b3_invalid") as tmp_dir:
            store = self._store(tmp_dir)
            for payload, error_code in invalid_payloads:
                self._write_payload(store.profiles_path, payload)
                result = store.load()
                with self.subTest(error_code=error_code, payload=payload):
                    self.assertFalse(result.mutation_available)
                    self.assertEqual(result.error_code, error_code)
                    self.assertEqual(result.user_profiles, ())

    def test_limit_and_reload_recovery_are_strict(self) -> None:
        with workspace_tempdir("ms23_b3_limit_recovery") as tmp_dir:
            store = self._store(tmp_dir)
            entries = [
                self._valid_entry(
                    profile_id=f"00000000-0000-4000-8000-{index:012d}",
                    display_name=f"モデル{index}",
                )
                for index in range(MAX_USER_PROFILES + 1)
            ]
            self._write_payload(store.profiles_path, {"schema_version": 1, "user_profiles": entries})
            failed = store.load()
            self.assertEqual(failed.error_code, "limit_exceeded")
            self.assertFalse(failed.mutation_available)

            self._write_payload(
                store.profiles_path,
                {"schema_version": 1, "user_profiles": [self._valid_entry()]},
            )
            recovered = store.load()
            self.assertTrue(recovered.mutation_available)
            self.assertIsNone(recovered.error_code)
            self.assertEqual(len(recovered.user_profiles), 1)

            store.profiles_path.unlink()
            missing = store.load()
            self.assertFalse(missing.file_exists)
            self.assertTrue(missing.mutation_available)
            self.assertEqual(missing.user_profiles, ())

    def test_invalid_json_and_unreadable_mutation_preserve_file(self) -> None:
        with workspace_tempdir("ms23_b3_invalid_json") as tmp_dir:
            store = self._store(tmp_dir)
            store.profiles_path.write_text("{broken", encoding="utf-8")
            self.assertEqual(store.load().error_code, "invalid_json")
            before = store.profiles_path.read_bytes()
            failed = store.create(
                "停止中",
                JAPANESE_MORPH_NAME_SET_ID,
                0.5,
                self._overrides(),
                "builtin:standard-hold",
            )
            self.assertEqual(failed.error_code, "store_unavailable")
            self.assertEqual(store.profiles_path.read_bytes(), before)

    def test_create_update_delete_preserve_id_and_order(self) -> None:
        with workspace_tempdir("ms23_b3_mutation") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            first = store.create(
                "一件目",
                JAPANESE_MORPH_NAME_SET_ID,
                0.5,
                self._overrides(),
                "builtin:standard-hold",
                profile_id=PROFILE_ID,
            )
            second = store.create(
                "二件目",
                LATIN_MORPH_NAME_SET_ID,
                1.0,
                self._overrides(9, 8, "decay"),
                USER_PRESET_ID,
                profile_id=PROFILE_ID_2,
            )
            self.assertTrue(first.succeeded)
            self.assertTrue(second.succeeded)
            updated = store.update(
                PROFILE_ID,
                "一件目",
                LATIN_MORPH_NAME_SET_ID,
                10.0,
                self._overrides(9, 8, "decay"),
                USER_PRESET_ID,
            )
            self.assertTrue(updated.succeeded)
            self.assertEqual([profile.id for profile in updated.user_profiles], [PROFILE_ID, PROFILE_ID_2])
            self.assertEqual(updated.user_profiles[0].morph_name_set_id, LATIN_MORPH_NAME_SET_ID)
            self.assertEqual(store.update(PROFILE_ID, "二件目", LATIN_MORPH_NAME_SET_ID, 1.0, self._overrides(), USER_PRESET_ID).error_code, "duplicate_display_name")
            self.assertEqual(store.delete("unknown").error_code, "invalid_input")
            self.assertEqual(store.delete(PROFILE_ID).user_profiles, (second.user_profiles[1],))

    def test_invalid_mutation_does_not_change_file_or_collection(self) -> None:
        with workspace_tempdir("ms23_b3_invalid_mutation") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            self.assertEqual(
                store.create("不正", JAPANESE_MORPH_NAME_SET_ID, 0, self._overrides(), "builtin:standard-hold").error_code,
                "invalid_input",
            )
            self.assertFalse(store.profiles_path.exists())
            self.assertEqual(store.user_profiles, ())

    def test_write_and_replace_failure_keep_old_state_and_cleanup_temp(self) -> None:
        with workspace_tempdir("ms23_b3_write_failure") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            self.assertTrue(
                store.create(
                    "既存",
                    JAPANESE_MORPH_NAME_SET_ID,
                    0.5,
                    self._overrides(),
                    "builtin:standard-hold",
                    profile_id=PROFILE_ID,
                ).succeeded
            )
            before = store.profiles_path.read_bytes()
            with patch("src.core.model_profiles.os.replace", side_effect=OSError("replace failed")):
                failed = store.create(
                    "新規",
                    JAPANESE_MORPH_NAME_SET_ID,
                    0.5,
                    self._overrides(),
                    "builtin:standard-hold",
                )
            self.assertEqual(failed.error_code, "replace_failed")
            self.assertEqual(failed.user_profiles[0].display_name, "既存")
            self.assertEqual(store.profiles_path.read_bytes(), before)
            self.assertEqual(list(store.profiles_path.parent.glob("mmd_autoliptool_profiles_*.tmp")), [])
            self.assertEqual(
                store.create("再試行", JAPANESE_MORPH_NAME_SET_ID, 0.5, self._overrides(), "builtin:standard-hold").error_code,
                "store_unavailable",
            )

        with workspace_tempdir("ms23_b3_write_failure_missing") as tmp_dir:
            store = self._store(tmp_dir)
            store.load()
            with patch("src.core.model_profiles.json.dump", side_effect=OSError("write failed")):
                failed = store.create(
                    "設定",
                    JAPANESE_MORPH_NAME_SET_ID,
                    0.5,
                    self._overrides(),
                    "builtin:standard-hold",
                )
            self.assertEqual(failed.error_code, "write_failed")
            self.assertFalse(store.profiles_path.exists())
            self.assertEqual(list(store.profiles_path.parent.glob("mmd_autoliptool_profiles_*.tmp")), [])

    def test_atomic_replace_uses_closed_same_directory_temp_file(self) -> None:
        with workspace_tempdir("ms23_b3_atomic") as tmp_dir:
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

            with patch("src.core.model_profiles.os.replace", side_effect=replace_and_probe):
                result = store.create(
                    "設定",
                    JAPANESE_MORPH_NAME_SET_ID,
                    0.5,
                    self._overrides(),
                    "builtin:standard-hold",
                )
            self.assertTrue(result.succeeded)
            self.assertEqual(captured["destination"], store.profiles_path)


class ModelProfileSettingsBoundaryTests(unittest.TestCase):
    def test_defaults_and_invalid_profile_ids(self) -> None:
        defaults = SettingsStore.default_settings()
        self.assertIsNone(defaults["active_model_profile_id"])
        self.assertIsNone(defaults["active_profile_baseline_preset_id"])
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {
                "active_model_profile_id": 123,
                "active_profile_baseline_preset_id": False,
            }
        )
        self.assertIsNone(normalized["active_model_profile_id"])
        self.assertIsNone(normalized["active_profile_baseline_preset_id"])
        for key in ("active_model_profile_id", "active_profile_baseline_preset_id"):
            self.assertIn(key, invalid_keys)
            self.assertIn(key, used_default_keys)

    def test_profile_ids_round_trip_and_explicit_clear(self) -> None:
        with workspace_tempdir("ms23_b3_settings") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            initial = SettingsStore.default_settings()
            initial.update(
                {
                    "active_model_profile_id": PROFILE_ID,
                    "active_profile_baseline_preset_id": USER_PRESET_ID,
                }
            )
            self.assertTrue(store.save(initial).succeeded)
            loaded = store.load().settings
            self.assertEqual(loaded["active_model_profile_id"], PROFILE_ID)
            self.assertEqual(loaded["active_profile_baseline_preset_id"], USER_PRESET_ID)

            self.assertTrue(
                store.save(
                    {
                        "active_model_profile_id": None,
                        "active_profile_baseline_preset_id": None,
                    }
                ).succeeded
            )
            cleared = store.load().settings
            self.assertIsNone(cleared["active_model_profile_id"])
            self.assertIsNone(cleared["active_profile_baseline_preset_id"])
            ini_text = (tmp_dir / "MMD_AutoLipTool.ini").read_text(encoding="utf-8")
            self.assertIn("active_model_profile_id =", ini_text)
            self.assertIn("active_profile_baseline_preset_id =", ini_text)

    def test_legacy_save_omitting_profile_ids_preserves_existing_values(self) -> None:
        with workspace_tempdir("ms23_b3_legacy_settings") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            initial = SettingsStore.default_settings()
            initial.update(
                {
                    "active_model_profile_id": PROFILE_ID,
                    "active_profile_baseline_preset_id": USER_PRESET_ID,
                }
            )
            self.assertTrue(store.save(initial).succeeded)
            self.assertTrue(store.save({"theme": "light"}).succeeded)
            loaded = store.load().settings
            self.assertEqual(loaded["theme"], "light")
            self.assertEqual(loaded["active_model_profile_id"], PROFILE_ID)
            self.assertEqual(loaded["active_profile_baseline_preset_id"], USER_PRESET_ID)
            self.assertTrue(store.save(None).succeeded)
            loaded_after_none = store.load().settings
            self.assertEqual(loaded_after_none["active_model_profile_id"], PROFILE_ID)
            self.assertEqual(loaded_after_none["active_profile_baseline_preset_id"], USER_PRESET_ID)


if __name__ == "__main__":
    unittest.main()
