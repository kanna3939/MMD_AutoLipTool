from __future__ import annotations

from src.core.settings_store import SettingsStore


def test_identity_only_save_preserves_numeric_generation_settings(tmp_path) -> None:
    store = SettingsStore(tmp_path / "MMD_AutoLipTool.ini")
    initial = SettingsStore.default_settings()
    initial.update(
        {
            "morph_upper_limit": 0.9,
            "closing_hold_frames": 8,
            "closing_softness_frames": 9,
            "long_vowel_mode": "decay",
            "active_preset_id": "old-preset",
        }
    )
    assert store.save(initial).succeeded

    assert store.save(
        {
            "active_preset_id": "new-preset",
            "active_model_profile_id": "profile",
            "active_profile_baseline_preset_id": "baseline",
        }
    ).succeeded

    loaded = store.load().settings
    assert loaded["morph_upper_limit"] == 0.9
    assert loaded["closing_hold_frames"] == 8
    assert loaded["closing_softness_frames"] == 9
    assert loaded["long_vowel_mode"] == "decay"
    assert loaded["active_preset_id"] == "new-preset"
    assert loaded["active_model_profile_id"] == "profile"
    assert loaded["active_profile_baseline_preset_id"] == "baseline"
