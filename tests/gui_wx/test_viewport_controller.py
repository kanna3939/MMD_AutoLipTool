import pytest
from gui_wx.viewport_controller import ViewportController

def test_viewport_controller_initial_state():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    
    assert ctrl.duration_sec == 0.0
    assert ctrl.zoom_factor == 1
    assert ctrl.viewport_start_sec == 0.0
    assert ctrl.viewport_end_sec == 0.0

def test_set_duration():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    
    ctrl.set_duration(10.0)
    assert ctrl.duration_sec == 10.0
    assert ctrl.viewport_start_sec == 0.0
    assert ctrl.viewport_end_sec == 10.0
    assert ctrl.zoom_factor == 1
    assert updates[-1] == (0.0, 10.0)

def test_zoom_in_and_out():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    ctrl.set_duration(10.0)
    
    # 1x -> 2x
    ctrl.zoom_in()
    assert ctrl.zoom_factor == 2
    # Center was 5.0, new span is 5.0. start = 5.0 - 2.5 = 2.5
    assert ctrl.viewport_start_sec == 2.5
    assert ctrl.viewport_end_sec == 7.5
    
    # 2x -> 4x
    ctrl.zoom_in()
    assert ctrl.zoom_factor == 4
    # Center is 5.0, new span is 2.5. start = 5.0 - 1.25 = 3.75
    assert ctrl.viewport_start_sec == 3.75
    assert ctrl.viewport_end_sec == 6.25
    
    # 4x -> 2x
    ctrl.zoom_out()
    assert ctrl.zoom_factor == 2
    assert ctrl.viewport_start_sec == 2.5
    assert ctrl.viewport_end_sec == 7.5
    
    # 2x -> 1x
    ctrl.zoom_out()
    assert ctrl.zoom_factor == 1
    assert ctrl.viewport_start_sec == 0.0
    assert ctrl.viewport_end_sec == 10.0

def test_zoom_clamp():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    ctrl.set_duration(1.0)
    
    # At 8x, requested span is 0.125, but min span is 0.25
    ctrl.zoom_in() # 2x (0.5)
    ctrl.zoom_in() # 4x (0.25)
    ctrl.zoom_in() # 8x (requested 0.125 -> clamped 0.25)
    
    assert ctrl.zoom_factor == 8
    span = ctrl.viewport_end_sec - ctrl.viewport_start_sec
    assert abs(span - 0.25) < 1e-5

def test_auto_follow():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    ctrl.set_duration(10.0)
    
    # 1x shouldn't follow
    ctrl.update_playback_position(9.0)
    assert ctrl.viewport_start_sec == 0.0
    
    ctrl.zoom_in() # 2x, span 5.0, start 2.5, end 7.5
    assert ctrl.viewport_start_sec == 2.5
    assert ctrl.viewport_end_sec == 7.5
    
    # 80% threshold = 2.5 + 5.0 * 0.8 = 6.5
    ctrl.update_playback_position(6.4)
    # no change
    assert ctrl.viewport_start_sec == 2.5
    
    ctrl.update_playback_position(6.6) # crossed 80%
    # should re-center at 60%. anchor=6.6, span=5.0. 
    # new_start = 6.6 - 5.0 * 0.6 = 3.6
    # new_end = 3.6 + 5.0 = 8.6
    assert abs(ctrl.viewport_start_sec - 3.6) < 1e-5
    assert abs(ctrl.viewport_end_sec - 8.6) < 1e-5

def test_auto_follow_clamp():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    ctrl.set_duration(10.0)
    
    ctrl.zoom_in() # 2x, span 5.0, start 2.5, end 7.5
    
    # Play near the end
    ctrl.update_playback_position(9.5) 
    # 60% of 5.0 is 3.0. start = 9.5 - 3.0 = 6.5. end = 11.5
    # Since end > duration, clamp to end = 10.0, start = 5.0
    assert abs(ctrl.viewport_end_sec - 10.0) < 1e-5
    assert abs(ctrl.viewport_start_sec - 5.0) < 1e-5

def test_playback_zoom_anchor():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    ctrl.set_duration(10.0)
    
    # 1x full range から 2x に zoom in
    # is_playing=True, playback_position_sec=6.0
    # 2x の span は 5.0 sec
    # anchor ratio 0.6 なので、期待 start は 6.0 - 5.0 * 0.6 = 3.0
    # 期待 end は 8.0
    ctrl.zoom_in(is_playing=True, playback_position_sec=6.0)
    
    assert ctrl.zoom_factor == 2
    assert abs(ctrl.viewport_start_sec - 3.0) < 1e-5
    assert abs(ctrl.viewport_end_sec - 8.0) < 1e-5

def test_playback_zoom_anchor_clamp():
    updates = []
    ctrl = ViewportController(lambda s, e: updates.append((s, e)))
    ctrl.set_duration(10.0)
    
    # 1x full range から 2x に zoom in
    # is_playing=True, playback_position_sec=9.5
    # 期待 start は 9.5 - 5.0 * 0.6 = 6.5
    # 期待 end は 11.5 -> clamped to 10.0, start to 5.0
    ctrl.zoom_in(is_playing=True, playback_position_sec=9.5)
    
    assert ctrl.zoom_factor == 2
    assert abs(ctrl.viewport_start_sec - 5.0) < 1e-5
    assert abs(ctrl.viewport_end_sec - 10.0) < 1e-5
