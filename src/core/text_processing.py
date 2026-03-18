import unicodedata

VOWELS = ("あ", "い", "う", "え", "お")

_A_KANA = set("あぁかがさざただなはばぱまゃやらわゎ")
_I_KANA = set("いぃきぎしじちぢにひびぴみりゐ")
_U_KANA = set("うぅくぐすずつづぬふぶぷむゅゆるゔ")
_E_KANA = set("えぇけげせぜてでねへべぺめれゑ")
_O_KANA = set("おぉこごそぞとどのほぼぽもょよろを")

_SMALL_COMBINERS = set("ゃゅょぁぃぅぇぉゎ")
_SKIP_CHARS = set("っん、。 \t\r\n")


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


def text_to_vowel_sequence(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = _katakana_to_hiragana(normalized)

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


def text_to_vowel_string(text: str) -> str:
    return "".join(text_to_vowel_sequence(text))
