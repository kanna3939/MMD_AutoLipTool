from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.effective_shape_plan import BaseTimingPlanInput, build_base_plan_identity
from src.core.pipeline import build_anchor_based_vowel_timeline, build_even_vowel_timeline
from src.core.preview_transform import _normalize_preview_timeline_points
from src.core.text_processing import hiragana_to_vowel_tokens
from src.vmd_writer import VowelTimelinePoint
from src.vmd_writer.writer import _normalize_timeline


def test_even_and_legacy_timeline_metadata_modes() -> None:
    tokens = hiragana_to_vowel_tokens("あーい")
    explicit = build_even_vowel_timeline([token.vowel for token in tokens], 0.0, 1.0, tokens=tokens)
    assert [(point.vowel_token_index, point.is_long_vowel_continuation, point.long_vowel_source_token_index) for point in explicit] == [
        (0, False, None),
        (1, True, 0),
        (2, False, None),
    ]
    legacy = build_even_vowel_timeline(["あ", "い"], 0.0, 1.0)
    assert all(point.vowel_token_index is None and not point.is_long_vowel_continuation for point in legacy)


def test_anchor_fallback_preserves_tokens() -> None:
    tokens = hiragana_to_vowel_tokens("あー")
    timeline = build_anchor_based_vowel_timeline(
        [token.vowel for token in tokens],
        [],
        0.0,
        1.0,
        tokens=tokens,
    )
    assert timeline[1].long_vowel_source_token_index == 0


def test_writer_and_preview_copy_metadata() -> None:
    point = VowelTimelinePoint(
        0.2,
        "あ",
        value=0.4,
        duration_sec=0.2,
        start_sec=0.1,
        end_sec=0.3,
        vowel_token_index=1,
        is_long_vowel_continuation=True,
        long_vowel_source_token_index=0,
    )
    writer_point = _normalize_timeline([point])[0]
    preview_point = _normalize_preview_timeline_points([point])[0]
    assert (writer_point.vowel_token_index, writer_point.long_vowel_source_token_index) == (1, 0)
    assert (preview_point.vowel_token_index, preview_point.long_vowel_source_token_index) == (1, 0)


def test_partial_and_invalid_timeline_metadata_fail_closed() -> None:
    points = (
        VowelTimelinePoint(0.2, "あ", duration_sec=0.2, start_sec=0.1, end_sec=0.3, vowel_token_index=0),
        VowelTimelinePoint(0.5, "あ", duration_sec=0.2, start_sec=0.4, end_sec=0.6),
    )
    with pytest.raises(ValueError, match="metadata"):
        build_base_plan_identity(BaseTimingPlanInput(points, None, 30))

    invalid = (
        replace(points[0], vowel_token_index=0),
        replace(points[1], vowel="い", vowel_token_index=1, is_long_vowel_continuation=True, long_vowel_source_token_index=0),
    )
    with pytest.raises(ValueError):
        build_base_plan_identity(BaseTimingPlanInput(invalid, None, 30))


def test_long_metadata_changes_base_identity() -> None:
    legacy = (VowelTimelinePoint(0.2, "あ", duration_sec=0.2, start_sec=0.1, end_sec=0.3),)
    explicit = (replace(legacy[0], vowel_token_index=0),)
    assert build_base_plan_identity(BaseTimingPlanInput(legacy, None, 30)) != build_base_plan_identity(
        BaseTimingPlanInput(explicit, None, 30)
    )
