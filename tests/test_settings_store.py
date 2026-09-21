from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.core.settings_store import SettingsStore
from tests.helpers import workspace_tempdir


class SettingsStoreClosingSoftnessTests(unittest.TestCase):
    def test_whisper_models_dir_defaults_to_empty_string(self) -> None:
        settings = SettingsStore.default_settings()

        self.assertIn("whisper_models_dir", settings)
        self.assertEqual(settings["whisper_models_dir"], "")

    def test_whisper_models_dir_round_trips_and_survives_partial_save(self) -> None:
        with workspace_tempdir("settings_store_whisper_models_dir") as tmp_dir:
            settings_path = tmp_dir / "MMD_AutoLipTool.ini"
            configured_path = tmp_dir / "models"
            store = SettingsStore(settings_path)

            settings = SettingsStore.default_settings()
            settings["whisper_models_dir"] = str(configured_path)
            first_save = store.save(settings)
            partial_save = store.save({"theme": "light"})
            loaded = store.load()

        self.assertTrue(first_save.succeeded)
        self.assertTrue(partial_save.succeeded)
        self.assertEqual(loaded.settings["whisper_models_dir"], str(configured_path))

    def test_system_theme_round_trips_without_implicit_conversion(self) -> None:
        with workspace_tempdir("settings_store_system_theme") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            save_result = store.save({"theme": "system"})
            loaded = store.load()

        self.assertTrue(save_result.succeeded)
        self.assertEqual(loaded.settings["theme"], "system")

    def test_partial_storage_update_preserves_supported_settings_snapshot(self) -> None:
        with workspace_tempdir("settings_store_managed_merge") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            original = SettingsStore.default_settings()
            original.update(
                {
                    "theme": "system",
                    "window_width": 1400,
                    "window_height": 900,
                    "recent_text_files": [r"C:\work\sample.txt"],
                    "recent_wav_files": [r"C:\work\sample.wav"],
                    "last_vmd_output_dir": r"C:\work\vmd",
                    "last_mmd_wav_export_dir": r"C:\work\wav",
                    "selected_whisper_model_key": "turbo",
                    "active_whisper_model_key": "medium",
                    "active_whisper_manifest_identity": "identity",
                }
            )
            first_save = store.save(original)
            partial_save = store.save({"whisper_models_dir": str(tmp_dir / "models")})
            loaded = store.load()

        self.assertTrue(first_save.succeeded)
        self.assertTrue(partial_save.succeeded)
        for key, value in original.items():
            if key == "whisper_models_dir":
                continue
            self.assertEqual(loaded.settings[key], value, key)

    def test_whisper_models_dir_non_string_falls_back_to_empty_string(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {"whisper_models_dir": 123}
        )

        self.assertEqual(normalized["whisper_models_dir"], "")
        self.assertIn("whisper_models_dir", invalid_keys)
        self.assertIn("whisper_models_dir", used_default_keys)

    def test_whisper_models_dir_whitespace_is_safe_empty_value(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {"whisper_models_dir": "   "}
        )

        self.assertEqual(normalized["whisper_models_dir"], "")
        self.assertNotIn("whisper_models_dir", invalid_keys)
        self.assertNotIn("whisper_models_dir", used_default_keys)

    def test_whisper_model_identity_defaults_are_small_and_empty_manifest(self) -> None:
        settings = SettingsStore.default_settings()

        self.assertEqual(settings["selected_whisper_model_key"], "small")
        self.assertEqual(settings["active_whisper_model_key"], "small")
        self.assertEqual(settings["active_whisper_manifest_identity"], "")

    def test_whisper_model_identity_round_trips_and_survives_partial_save(self) -> None:
        with workspace_tempdir("settings_store_whisper_identity") as tmp_dir:
            store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
            identity = "whisper-manifest-v1:20250625:turbo:" + ("a" * 64)
            first_save = store.save(
                {
                    "selected_whisper_model_key": "turbo",
                    "active_whisper_model_key": "medium",
                    "active_whisper_manifest_identity": identity,
                }
            )
            partial_save = store.save({"theme": "light"})
            loaded = store.load()

        self.assertTrue(first_save.succeeded)
        self.assertTrue(partial_save.succeeded)
        self.assertEqual(loaded.settings["selected_whisper_model_key"], "turbo")
        self.assertEqual(loaded.settings["active_whisper_model_key"], "medium")
        self.assertEqual(loaded.settings["active_whisper_manifest_identity"], identity)

    def test_whisper_model_unknown_string_is_preserved_for_startup_resolver(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {
                "selected_whisper_model_key": "large",
                "active_whisper_model_key": "legacy",
            }
        )

        self.assertEqual(normalized["selected_whisper_model_key"], "large")
        self.assertEqual(normalized["active_whisper_model_key"], "legacy")
        self.assertNotIn("selected_whisper_model_key", invalid_keys)
        self.assertNotIn("active_whisper_model_key", used_default_keys)

    def test_whisper_model_non_string_values_fall_back_safely(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {
                "selected_whisper_model_key": 1,
                "active_whisper_model_key": False,
                "active_whisper_manifest_identity": 2,
            }
        )

        self.assertEqual(normalized["selected_whisper_model_key"], "small")
        self.assertEqual(normalized["active_whisper_model_key"], "small")
        self.assertEqual(normalized["active_whisper_manifest_identity"], "")
        self.assertIn("selected_whisper_model_key", invalid_keys)
        self.assertIn("active_whisper_model_key", invalid_keys)
        self.assertIn("active_whisper_manifest_identity", invalid_keys)
        self.assertIn("selected_whisper_model_key", used_default_keys)

    def test_last_vmd_output_dir_round_trips_through_save_and_load(self) -> None:
        with workspace_tempdir("settings_store_vmd_output_dir") as tmp_dir:
            settings_path = tmp_dir / "MMD_AutoLipTool.ini"
            store = SettingsStore(settings_path)

            settings = SettingsStore.default_settings()
            settings["last_vmd_output_dir"] = str(tmp_dir)

            save_result = store.save(settings)
            self.assertTrue(save_result.succeeded)

            load_result = store.load()
            self.assertEqual(load_result.settings["last_vmd_output_dir"], str(tmp_dir))

    def test_non_string_last_vmd_output_dir_falls_back_to_default(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {"last_vmd_output_dir": 123}
        )

        self.assertEqual(normalized["last_vmd_output_dir"], "")
        self.assertIn("last_vmd_output_dir", invalid_keys)
        self.assertIn("last_vmd_output_dir", used_default_keys)

    def test_closing_hold_frames_round_trips_through_save_and_load(self) -> None:
        with workspace_tempdir("settings_store_closing_hold") as tmp_dir:
            settings_path = tmp_dir / "MMD_AutoLipTool.ini"
            store = SettingsStore(settings_path)

            settings = SettingsStore.default_settings()
            settings["closing_hold_frames"] = 5

            save_result = store.save(settings)
            self.assertTrue(save_result.succeeded)

            load_result = store.load()
            self.assertEqual(load_result.settings["closing_hold_frames"], 5)

    def test_negative_closing_hold_frames_falls_back_to_default(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {"closing_hold_frames": -2}
        )

        self.assertEqual(normalized["closing_hold_frames"], 0)
        self.assertIn("closing_hold_frames", invalid_keys)
        self.assertIn("closing_hold_frames", used_default_keys)

    def test_closing_softness_frames_round_trips_through_save_and_load(self) -> None:
        with workspace_tempdir("settings_store_closing_softness") as tmp_dir:
            settings_path = tmp_dir / "MMD_AutoLipTool.ini"
            store = SettingsStore(settings_path)

            settings = SettingsStore.default_settings()
            settings["closing_softness_frames"] = 7

            save_result = store.save(settings)
            self.assertTrue(save_result.succeeded)

            load_result = store.load()
            self.assertEqual(load_result.settings["closing_softness_frames"], 7)

    def test_negative_closing_softness_frames_falls_back_to_default(self) -> None:
        normalized, invalid_keys, used_default_keys = SettingsStore.normalize_settings(
            {"closing_softness_frames": -3}
        )

        self.assertEqual(normalized["closing_softness_frames"], 0)
        self.assertIn("closing_softness_frames", invalid_keys)
        self.assertIn("closing_softness_frames", used_default_keys)


if __name__ == "__main__":
    unittest.main()
