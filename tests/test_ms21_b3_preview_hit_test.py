from __future__ import annotations

import pytest

from src.core.preview_hit_test import (
    PreviewEventHitRegion,
    PreviewHitTestInput,
    hit_test_preview_event,
)


def region(
    index: int,
    vowel: str,
    start: int,
    peak: int,
    end: int,
) -> PreviewEventHitRegion:
    return PreviewEventHitRegion(index, vowel, start, peak, end, 0.5)


def hit(
    *,
    x: float,
    y: float,
    regions: tuple[PreviewEventHitRegion, ...],
) -> int | None:
    return hit_test_preview_event(
        PreviewHitTestInput(
            x=x,
            y=y,
            width=300.0,
            height=500.0,
            viewport_start_sec=0.0,
            viewport_end_sec=10.0,
            event_hit_regions=regions,
        )
    )


def test_maps_each_lane_and_rejects_panel_boundaries() -> None:
    regions = tuple(
        region(index, vowel, 29, 30, 31)
        for index, vowel in enumerate(("あ", "い", "う", "え", "お"))
    )
    assert tuple(hit(x=30.0, y=lane * 100.0, regions=regions) for lane in range(5)) == (
        0,
        1,
        2,
        3,
        4,
    )
    assert hit(x=-1.0, y=0.0, regions=regions) is None
    assert hit(x=300.0, y=0.0, regions=regions) is None
    assert hit(x=30.0, y=500.0, regions=regions) is None


def test_selects_only_event_range_in_clicked_lane() -> None:
    regions = (region(3, "あ", 29, 30, 31), region(4, "い", 29, 30, 31))
    assert hit(x=30.0, y=20.0, regions=regions) == 3
    assert hit(x=30.0, y=120.0, regions=regions) == 4
    assert hit(x=60.0, y=20.0, regions=regions) is None


def test_overlap_prefers_nearest_base_peak_then_lower_index() -> None:
    regions = (
        region(7, "あ", 20, 35, 50),
        region(3, "あ", 20, 25, 50),
        region(2, "あ", 20, 35, 50),
    )
    assert hit(x=35.0, y=20.0, regions=regions) == 2
    assert hit(x=25.0, y=20.0, regions=regions) == 3
    assert hit(x=30.0, y=20.0, regions=regions) == 2


def test_zero_span_event_is_selectable() -> None:
    assert hit(x=30.0, y=20.0, regions=(region(1, "あ", 30, 30, 30),)) == 1


@pytest.mark.parametrize(
    "kwargs",
    (
        {"base_event_index": -1},
        {"base_event_index": True},
        {"vowel": "ん"},
        {"start_frame": 31},
        {"base_peak_frame": 32},
        {"peak_value": float("nan")},
    ),
)
def test_hit_region_rejects_malformed_provenance(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "base_event_index": 0,
        "vowel": "あ",
        "start_frame": 29,
        "base_peak_frame": 30,
        "end_frame": 31,
        "peak_value": 0.5,
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        PreviewEventHitRegion(**values)
