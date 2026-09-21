from __future__ import annotations

import pytest

from src.core.text_processing import (
    VowelToken,
    hiragana_to_vowel_sequence,
    hiragana_to_vowel_tokens,
    text_to_vowel_tokens,
)


def test_long_markers_create_explicit_continuations() -> None:
    tokens = hiragana_to_vowel_tokens("あーあーー")
    assert [(item.vowel, item.token_index, item.is_long_vowel_continuation, item.long_vowel_source_token_index) for item in tokens] == [
        ("あ", 0, False, None),
        ("あ", 1, True, 0),
        ("あ", 2, False, None),
        ("あ", 3, True, 2),
        ("あ", 4, True, 2),
    ]


def test_leading_marker_is_ignored_and_same_vowel_without_marker_is_not_long() -> None:
    assert hiragana_to_vowel_tokens("ーあ")[0] == VowelToken("あ", 0)
    assert all(not token.is_long_vowel_continuation for token in hiragana_to_vowel_tokens("ああ"))


def test_legacy_sequence_is_derived_without_output_change() -> None:
    assert hiragana_to_vowel_sequence("あーい") == ["あ", "あ", "い"]
    assert [token.vowel for token in text_to_vowel_tokens("アイー")] == ["あ", "い", "い"]


def test_token_is_immutable_and_validates_source_contract() -> None:
    token = VowelToken("あ", 0)
    with pytest.raises((AttributeError, TypeError)):
        token.vowel = "い"  # type: ignore[misc]
    with pytest.raises(ValueError):
        VowelToken("あ", 1, is_long_vowel_continuation=True, long_vowel_source_token_index=1)
    with pytest.raises(ValueError):
        VowelToken("あ", 0, long_vowel_source_token_index=0)
