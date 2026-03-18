import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import text_to_vowel_sequence, text_to_vowel_string


class TextProcessingTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
