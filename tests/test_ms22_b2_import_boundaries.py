from __future__ import annotations

import importlib


def test_public_modules_import_without_cycle() -> None:
    for name in (
        "src.core.text_processing",
        "src.core.event_adjustment",
        "src.core.effective_shape_plan",
        "src.core.pipeline",
        "src.core.preview_transform",
        "src.vmd_writer",
        "src.vmd_writer.effective_shape_adapter",
    ):
        module = importlib.import_module(name)
        assert module is not None


def test_mode_contract_uses_primitive_strings() -> None:
    from src.core.event_adjustment import AdjustmentContractError, validate_long_vowel_mode

    assert validate_long_vowel_mode("hold") == "hold"
    assert validate_long_vowel_mode("decay") == "decay"
    for value in ("Hold", " hold", "decay ", "", True, 1):
        try:
            validate_long_vowel_mode(value)
        except AdjustmentContractError:
            continue
        raise AssertionError(f"accepted invalid mode: {value!r}")


def test_writer_accepts_structurally_equivalent_timeline_point() -> None:
    from src.vmd_writer.writer import _normalize_timeline

    try:
        legacy_module = importlib.import_module("vmd_writer.writer")
    except ModuleNotFoundError:
        return
    point = legacy_module.VowelTimelinePoint(
        0.2,
        "あ",
        value=0.4,
        duration_sec=0.2,
        start_sec=0.1,
        end_sec=0.3,
        vowel_token_index=0,
    )
    normalized = _normalize_timeline([point])
    assert normalized[0].vowel_token_index == 0
