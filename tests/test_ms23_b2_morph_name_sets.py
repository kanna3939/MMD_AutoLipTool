from dataclasses import FrozenInstanceError

import pytest

from src.core.morph_name_sets import (
    BUILTIN_MORPH_NAME_SETS,
    DEFAULT_MORPH_NAME_SET,
    JAPANESE_MORPH_NAME_SET,
    JAPANESE_MORPH_NAME_SET_ID,
    JAPANESE_OUTPUT_NAMES,
    LATIN_MORPH_NAME_SET,
    LATIN_MORPH_NAME_SET_ID,
    LATIN_OUTPUT_NAMES,
    MorphNameSet,
    get_builtin_morph_name_set,
    map_semantic_morph_name,
    validate_builtin_output_morph_name,
    validate_output_morph_names,
)


def test_built_in_sets_have_stable_ids_display_names_and_order() -> None:
    assert tuple(item.set_id for item in BUILTIN_MORPH_NAME_SETS) == (
        JAPANESE_MORPH_NAME_SET_ID,
        LATIN_MORPH_NAME_SET_ID,
    )
    assert JAPANESE_MORPH_NAME_SET.display_name == "日本語5母音"
    assert LATIN_MORPH_NAME_SET.display_name == "英字5母音"
    assert JAPANESE_MORPH_NAME_SET.output_names == JAPANESE_OUTPUT_NAMES
    assert LATIN_MORPH_NAME_SET.output_names == LATIN_OUTPUT_NAMES
    assert all(isinstance(item.output_names, tuple) for item in BUILTIN_MORPH_NAME_SETS)


def test_default_and_explicit_builtin_resolution() -> None:
    assert get_builtin_morph_name_set() is DEFAULT_MORPH_NAME_SET
    assert get_builtin_morph_name_set(JAPANESE_MORPH_NAME_SET_ID) is JAPANESE_MORPH_NAME_SET
    assert get_builtin_morph_name_set(LATIN_MORPH_NAME_SET_ID) is LATIN_MORPH_NAME_SET


@pytest.mark.parametrize(
    "set_id",
    (None, "builtin:unknown", 1, [], ""),
)
def test_unknown_or_invalid_set_id_fails_closed(set_id: object) -> None:
    with pytest.raises(ValueError):
        get_builtin_morph_name_set(set_id)


@pytest.mark.parametrize(
    "output_names",
    (
        None,
        ("あ", "い"),
        ("あ", "い", "う", "え", "え"),
        ("", "い", "う", "え", "お"),
        ("あ", "い", "う", "え", "\n"),
        ("x", "y", "z", "u", "v"),
    ),
)
def test_output_name_validation_rejects_invalid_or_non_builtin_sets(
    output_names: object,
) -> None:
    with pytest.raises(ValueError):
        validate_output_morph_names(output_names)  # type: ignore[arg-type]


def test_output_name_validation_returns_immutable_tuple() -> None:
    assert validate_output_morph_names(list(LATIN_OUTPUT_NAMES)) == LATIN_OUTPUT_NAMES
    assert validate_builtin_output_morph_name("A") == "A"
    with pytest.raises(ValueError):
        validate_builtin_output_morph_name("あいう")


def test_morph_name_set_is_frozen_and_maps_by_semantic_order() -> None:
    with pytest.raises(FrozenInstanceError):
        JAPANESE_MORPH_NAME_SET.display_name = "changed"  # type: ignore[misc]
    assert map_semantic_morph_name("あ", LATIN_MORPH_NAME_SET) == "A"
    assert map_semantic_morph_name("お", LATIN_MORPH_NAME_SET) == "O"
    with pytest.raises(ValueError):
        map_semantic_morph_name("A", LATIN_MORPH_NAME_SET)


@pytest.mark.parametrize(
    "set_id,display_name,output_names",
    (
        (JAPANESE_MORPH_NAME_SET_ID, "英字5母音", JAPANESE_OUTPUT_NAMES),
        (LATIN_MORPH_NAME_SET_ID, "英字5母音", JAPANESE_OUTPUT_NAMES),
    ),
)
def test_morph_name_set_rejects_mismatched_builtin_fields(
    set_id: str,
    display_name: str,
    output_names: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        MorphNameSet(
            set_id=set_id,
            display_name=display_name,
            output_names=output_names,
        )
