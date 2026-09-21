import pytest
from src.core.preview_transform import build_preview_data, PREVIEW_ROW_VOWELS
from src.vmd_writer import VowelTimelinePoint

def test_ms16_b4_preview_shape_normal_event_generates_control_points():
    # 通常のイベントが変形台形の control_points を持つか確認する
    timeline = [
        VowelTimelinePoint(
            vowel="あ",
            time_sec=1.0,
            duration_sec=0.5,
            start_sec=0.75,
            end_sec=1.25,
            peak_value=1.0,
            value=1.0
        )
    ]
    preview_data = build_preview_data(timeline=timeline)
    
    a_row = next((r for r in preview_data.rows if r.vowel == "あ"), None)
    assert a_row is not None
    assert len(a_row.segments) > 0
    
    segment = a_row.segments[0]
    # control_points が3点以上あること
    assert len(segment.control_points) >= 3
    
    # 時刻が start_sec 〜 end_sec の範囲内であること
    for cp in segment.control_points:
        assert 0.75 - 0.05 <= cp.time_sec <= 1.25 + 0.05
        # 値が 0.0 〜 1.0 に収まること
        assert 0.0 <= cp.value <= 1.0

def test_ms16_b4_preview_shape_short_event_generates_control_points():
    # 短区間イベントが三角形または fallback の control_points を持つか確認する
    timeline = [
        VowelTimelinePoint(
            vowel="い",
            time_sec=2.0,
            duration_sec=0.01,
            start_sec=1.995,
            end_sec=2.005,
            peak_value=0.5,
            value=0.5
        )
    ]
    preview_data = build_preview_data(timeline=timeline)
    
    i_row = next((r for r in preview_data.rows if r.vowel == "い"), None)
    assert i_row is not None
    assert len(i_row.segments) > 0
    
    segment = i_row.segments[0]
    # control_points が生成されること
    assert len(segment.control_points) > 0
    
def test_ms16_b4_preview_shape_zero_peak_is_not_emphasized():
    # peak_value == 0.0 のイベント
    timeline = [
        VowelTimelinePoint(
            vowel="う",
            time_sec=3.0,
            duration_sec=0.5,
            start_sec=2.75,
            end_sec=3.25,
            peak_value=0.0,
            value=0.0
        )
    ]
    preview_data = build_preview_data(timeline=timeline)
    
    u_row = next((r for r in preview_data.rows if r.vowel == "う"), None)
    assert u_row is not None
    
    if len(u_row.segments) > 0:
        segment = u_row.segments[0]
        for cp in segment.control_points:
            # peak_value が 0 なので値も 0 になるはず
            assert cp.value == 0.0
