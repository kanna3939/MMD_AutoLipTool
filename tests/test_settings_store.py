from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui.settings_store import SettingsStore
from tests.helpers import workspace_tempdir


class SettingsStoreClosingSoftnessTests(unittest.TestCase):
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
