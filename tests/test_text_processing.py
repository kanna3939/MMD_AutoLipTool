import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import (
    TextProcessingError,
    text_to_hiragana,
    text_to_vowel_sequence,
    text_to_vowel_string,
)


class TextProcessingTests(unittest.TestCase):
    def test_text_to_hiragana_normalizes_katakana_and_halfwidth(self) -> None:
        text = "\u30a2\u30a4\u30a6\u30a8\u30aa \uff71\uff72\uff73\uff74\uff75"
        expected = "\u3042\u3044\u3046\u3048\u304a\u3042\u3044\u3046\u3048\u304a"
        self.assertEqual(text_to_hiragana(text), expected)

    def test_text_to_hiragana_removes_punctuation_and_symbols(self) -> None:
        text = "あ、い。う! え? お@#$%"
        expected = "あいうえお"
        self.assertEqual(text_to_hiragana(text), expected)

    def test_text_to_hiragana_ignores_emojis_and_zwj(self) -> None:
        # Two family emojis contain 6 ZWJ (\u200D) characters.
        # Validates that ZWJ doesn't trigger the control char limit.
        text = "あ👨‍👩‍👧‍👦い👨‍👩‍👧‍👦う"
        expected = "あいう"
        self.assertEqual(text_to_hiragana(text), expected)

    @patch("core.text_processing._pyopenjtalk_g2p", return_value="\u30ad\u30e7\u30fc\u30ef\u30ab\u30ca\u30b8")
    def test_text_to_hiragana_uses_pyopenjtalk_for_kanji(self, _: object) -> None:
        text = "\u4eca\u65e5\u306f\u304b\u306a\u5b57"
        expected = "\u304d\u3087\u30fc\u308f\u304b\u306a\u3058"
        self.assertEqual(text_to_hiragana(text), expected)

    def test_text_to_hiragana_raises_when_only_symbols(self) -> None:
        with self.assertRaises(TextProcessingError):
            text_to_hiragana("\u3001\u3002!?[]{}  ")

    @patch("core.text_processing._pyopenjtalk_g2p", side_effect=TextProcessingError("mock conversion error"))
    def test_text_to_hiragana_raises_on_pyopenjtalk_error(self, _: object) -> None:
        with self.assertRaises(TextProcessingError):
            text_to_hiragana("\u4eca\u65e5\u306f\u826f\u3044\u5929\u6c17")

    def test_short_kana_to_vowels(self) -> None:
        text = "\u3042\u3044\u3046\u3048\u304a"  # あいうえお
        expected = ["\u3042", "\u3044", "\u3046", "\u3048", "\u304a"]

        self.assertEqual(text_to_vowel_sequence(text), expected)
        self.assertEqual(text_to_vowel_string(text), "".join(expected))

    def test_special_cases_yoon_choon_sokuon_hatsuon_punctuation(self) -> None:
        text = (
            "\u304d\u3083"  # きゃ
            "\u3057\u3085"  # しゅ
            "\u3061\u3087"  # ちょ
            "\u30fc"        # ー
            "\u3063"        # っ
            "\u3093"        # ん
            "\u3001\u3002"  # 、。
        )
        expected = ["\u3042", "\u3046", "\u304a", "\u304a"]

        self.assertEqual(text_to_vowel_sequence(text), expected)

    def test_katakana_is_supported(self) -> None:
        text = "\u30a2\u30a4\u30a6\u30a8\u30aa"  # アイウエオ
        expected = ["\u3042", "\u3044", "\u3046", "\u3048", "\u304a"]
        self.assertEqual(text_to_vowel_sequence(text), expected)

    def test_text_to_vowel_sequence_ignores_punctuation_and_symbols(self) -> None:
        text = "\u3042\u3001\u3044\u3002\u3046! \u3048? \u304a@#$%"
        expected = ["\u3042", "\u3044", "\u3046", "\u3048", "\u304a"]
        self.assertEqual(text_to_vowel_sequence(text), expected)


if __name__ == "__main__":
    unittest.main()
