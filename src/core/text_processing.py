import unicodedata

VOWELS = ("あ", "い", "う", "え", "お")

_A_KANA = set("あぁかがさざただなはばぱまゃやらわゎ")
_I_KANA = set("いぃきぎしじちぢにひびぴみりゐ")
_U_KANA = set("うぅくぐすずつづぬふぶぷむゅゆるゔ")
_E_KANA = set("えぇけげせぜてでねへべぺめれゑ")
_O_KANA = set("おぉこごそぞとどのほぼぽもょよろを")

_SMALL_COMBINERS = set("ゃゅょぁぃぅぇぉゎ")
_SKIP_CHARS = set("っん、。 \t\r\n")
_KANJI_EXTRA_CHARS = {"々", "〆", "〇", "ヶ"}


class TextProcessingError(ValueError):
    """Recoverable text-processing error for GUI and pipeline handling."""


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _strip_ignored_symbols(text: str) -> str:
    filtered: list[str] = []
    for char in text:
        if char == "ー":
            filtered.append(char)
            continue

        category = unicodedata.category(char)
        if category.startswith("P") or category.startswith("S"):
            continue
        if category.startswith("Z"):
            continue
        if category in ("Cc", "Cf"):
            continue

        filtered.append(char)
    return "".join(filtered)


def _contains_kanji(text: str) -> bool:
    for char in text:
        code = ord(char)
        if 0x3400 <= code <= 0x4DBF:
            return True
        if 0x4E00 <= code <= 0x9FFF:
            return True
        if 0xF900 <= code <= 0xFAFF:
            return True
        if char in _KANJI_EXTRA_CHARS:
            return True
    return False


def _pyopenjtalk_g2p(text: str) -> str:
    try:
        import pyopenjtalk
    except Exception as error:
        raise TextProcessingError(f"Failed to import pyopenjtalk: {error}") from error

    try:
        kana = pyopenjtalk.g2p(text, kana=True)
    except Exception as error:
        raise TextProcessingError(f"pyopenjtalk conversion failed: {error}") from error

    if not isinstance(kana, str):
        raise TextProcessingError("pyopenjtalk returned an unexpected type.")

    kana = kana.strip()
    if not kana:
        raise TextProcessingError("pyopenjtalk returned an empty reading.")
    return kana


def _katakana_to_hiragana(text: str) -> str:
    converted: list[str] = []
    for char in text:
        code = ord(char)
        # Convert full-width katakana to hiragana.
        if 0x30A1 <= code <= 0x30F6:
            converted.append(chr(code - 0x60))
        else:
            converted.append(char)
    return "".join(converted)


def text_to_hiragana(text: str) -> str:
    normalized = _normalize_text(text)
    conversion_input = _strip_ignored_symbols(normalized)
    if not conversion_input:
        raise TextProcessingError(
            "No convertible text remains after removing punctuation/symbols."
        )

    kana_text = conversion_input
    if _contains_kanji(conversion_input):
        kana_text = _pyopenjtalk_g2p(conversion_input)

    return _katakana_to_hiragana(_normalize_text(kana_text))


def _kana_to_vowel(kana: str) -> str | None:
    if kana in _A_KANA:
        return "あ"
    if kana in _I_KANA:
        return "い"
    if kana in _U_KANA:
        return "う"
    if kana in _E_KANA:
        return "え"
    if kana in _O_KANA:
        return "お"
    return None


def hiragana_to_vowel_sequence(text: str) -> list[str]:
    normalized = _katakana_to_hiragana(_strip_ignored_symbols(_normalize_text(text)))
    vowels: list[str] = []
    index = 0
    while index < len(normalized):
        char = normalized[index]

        if char in _SKIP_CHARS:
            index += 1
            continue

        if char == "ー":
            if vowels:
                vowels.append(vowels[-1])
            index += 1
            continue

        if (
            index + 1 < len(normalized)
            and normalized[index + 1] in _SMALL_COMBINERS
            and _kana_to_vowel(char) is not None
        ):
            combined_vowel = _kana_to_vowel(normalized[index + 1])
            if combined_vowel is not None:
                vowels.append(combined_vowel)
                index += 2
                continue

        vowel = _kana_to_vowel(char)
        if vowel is not None:
            vowels.append(vowel)
        index += 1

    return vowels


def hiragana_to_vowel_string(text: str) -> str:
    return "".join(hiragana_to_vowel_sequence(text))


def text_to_vowel_sequence(text: str) -> list[str]:
    normalized = text_to_hiragana(text)
    return hiragana_to_vowel_sequence(normalized)


def text_to_vowel_string(text: str) -> str:
    return "".join(text_to_vowel_sequence(text))
