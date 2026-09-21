from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


SEMANTIC_VOWEL_ORDER = ("あ", "い", "う", "え", "お")
JAPANESE_OUTPUT_NAMES = SEMANTIC_VOWEL_ORDER
LATIN_OUTPUT_NAMES = ("A", "I", "U", "E", "O")

JAPANESE_MORPH_NAME_SET_ID = "builtin:japanese-vowels"
LATIN_MORPH_NAME_SET_ID = "builtin:latin-vowels"

_EXPECTED_BUILTIN_SET_FIELDS = {
    JAPANESE_MORPH_NAME_SET_ID: ("日本語5母音", JAPANESE_OUTPUT_NAMES),
    LATIN_MORPH_NAME_SET_ID: ("英字5母音", LATIN_OUTPUT_NAMES),
}
_BUILTIN_OUTPUT_NAMES = frozenset(JAPANESE_OUTPUT_NAMES + LATIN_OUTPUT_NAMES)
_UNSET = object()


def _validate_name_text(name: object, field_name: str) -> str:
    if type(name) is not str or not name:
        raise ValueError(f"{field_name} must be a non-empty string")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in name):
        raise ValueError(f"{field_name} must not contain control characters")
    return name


def _normalize_output_names(output_names: object) -> tuple[str, ...]:
    if output_names is None or isinstance(output_names, (str, bytes, bytearray)):
        raise ValueError("output_morph_names must be a sequence of five names")
    try:
        normalized = tuple(output_names)  # type: ignore[arg-type]
    except TypeError as error:
        raise ValueError("output_morph_names must be a sequence of five names") from error
    if len(normalized) != len(SEMANTIC_VOWEL_ORDER):
        raise ValueError("output_morph_names must contain exactly five names")
    normalized = tuple(
        _validate_name_text(name, f"output_morph_names[{index}]")
        for index, name in enumerate(normalized)
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError("output_morph_names must not contain duplicates")
    return normalized


@dataclass(frozen=True)
class MorphNameSet:
    set_id: str
    display_name: str
    output_names: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_name_text(self.set_id, "set_id")
        expected = _EXPECTED_BUILTIN_SET_FIELDS.get(self.set_id)
        if expected is None:
            raise ValueError(f"unsupported built-in morph name set: {self.set_id!r}")
        _validate_name_text(self.display_name, "display_name")
        if self.display_name != expected[0]:
            raise ValueError("display_name does not match the built-in morph name set")
        normalized_output_names = _normalize_output_names(self.output_names)
        if normalized_output_names != expected[1]:
            raise ValueError("output_names do not match the built-in morph name set")
        object.__setattr__(self, "output_names", normalized_output_names)


JAPANESE_MORPH_NAME_SET = MorphNameSet(
    set_id=JAPANESE_MORPH_NAME_SET_ID,
    display_name="日本語5母音",
    output_names=JAPANESE_OUTPUT_NAMES,
)
LATIN_MORPH_NAME_SET = MorphNameSet(
    set_id=LATIN_MORPH_NAME_SET_ID,
    display_name="英字5母音",
    output_names=LATIN_OUTPUT_NAMES,
)
BUILTIN_MORPH_NAME_SETS = (JAPANESE_MORPH_NAME_SET, LATIN_MORPH_NAME_SET)
DEFAULT_MORPH_NAME_SET = JAPANESE_MORPH_NAME_SET


def get_builtin_morph_name_set(set_id: str | object = _UNSET) -> MorphNameSet:
    if set_id is _UNSET:
        return DEFAULT_MORPH_NAME_SET
    if type(set_id) is not str:
        raise ValueError("set_id must be a built-in morph name set ID")
    for morph_name_set in BUILTIN_MORPH_NAME_SETS:
        if morph_name_set.set_id == set_id:
            return morph_name_set
    raise ValueError(f"unsupported built-in morph name set: {set_id!r}")


def validate_output_morph_names(
    output_morph_names: Sequence[str] | None,
) -> tuple[str, ...]:
    normalized = _normalize_output_names(output_morph_names)
    if normalized not in (JAPANESE_OUTPUT_NAMES, LATIN_OUTPUT_NAMES):
        raise ValueError("output_morph_names must match a built-in morph name set")
    return normalized


def validate_builtin_output_morph_name(name: object) -> str:
    normalized = _validate_name_text(name, "morph_name")
    if normalized not in _BUILTIN_OUTPUT_NAMES:
        raise ValueError(f"unsupported built-in morph name: {normalized!r}")
    return normalized


def map_semantic_morph_name(
    semantic_vowel: str,
    morph_name_set: MorphNameSet,
) -> str:
    if semantic_vowel not in SEMANTIC_VOWEL_ORDER:
        raise ValueError(f"unsupported semantic vowel: {semantic_vowel!r}")
    return morph_name_set.output_names[SEMANTIC_VOWEL_ORDER.index(semantic_vowel)]


__all__ = [
    "BUILTIN_MORPH_NAME_SETS",
    "DEFAULT_MORPH_NAME_SET",
    "JAPANESE_MORPH_NAME_SET",
    "JAPANESE_MORPH_NAME_SET_ID",
    "JAPANESE_OUTPUT_NAMES",
    "LATIN_MORPH_NAME_SET",
    "LATIN_MORPH_NAME_SET_ID",
    "LATIN_OUTPUT_NAMES",
    "MorphNameSet",
    "SEMANTIC_VOWEL_ORDER",
    "get_builtin_morph_name_set",
    "map_semantic_morph_name",
    "validate_builtin_output_morph_name",
    "validate_output_morph_names",
]
