import pytest
from gui_wx.ui_state import UiState, StatusKey
from gui_wx.theme import ThemeMode, ResolvedTheme, ThemeManager
from unittest.mock import MagicMock

def test_uistate_theme_defaults():
    state = UiState()
    assert state.theme_mode == "system"
    assert state.resolved_theme == "dark"

def test_uistate_playback_ready():
    state = UiState()
    assert state.playback_ready == False
    
    state.selected_wav_path = "dummy.wav"
    assert state.playback_ready == True

def test_uistate_analysis_ready():
    state = UiState()
    assert state.analysis_ready == False
    
    state.analysis_result_valid = True
    assert state.analysis_ready == False
    
    state.current_timing_plan = object()
    assert state.analysis_ready == True

def test_theme_manager_resolve():
    assert ThemeManager.resolve_theme(ThemeMode.LIGHT) == ResolvedTheme.LIGHT
    assert ThemeManager.resolve_theme(ThemeMode.DARK) == ResolvedTheme.DARK
    # System resolution relies on wx.App, difficult to test in pure unit tests without an active app

def test_app_controller_zoom_action_state():
    from gui_wx.app_controller import AppController
    from unittest.mock import Mock
    
    view_mock = Mock()
    st = UiState()
    view_mock.ui_state = st
    
    ctrl = AppController(view_mock)
    
    # 1. duration 未設定では Zoom In / Out / Reset が false
    state = ctrl.get_zoom_action_state()
    assert state == {"zoom_in": False, "zoom_out": False, "zoom_reset": False}
    
    # Setup dummy analysis and viewport
    class DummyAnalysis:
        duration_sec = 10.0
    st.selected_wav_analysis = DummyAnalysis()
    ctrl.viewport_controller.set_duration(10.0)
    
    # 2. duration 有効、zoom_factor 1 では In: True, Out: False, Reset: True
    state = ctrl.get_zoom_action_state()
    assert state == {"zoom_in": True, "zoom_out": False, "zoom_reset": True}
    
    # 3. zoom_factor 8 では In: False, Out: True, Reset: True
    ctrl.viewport_controller.zoom_in() # 2x
    ctrl.viewport_controller.zoom_in() # 4x
    ctrl.viewport_controller.zoom_in() # 8x
    state = ctrl.get_zoom_action_state()
    assert state == {"zoom_in": False, "zoom_out": True, "zoom_reset": True}
    
    # 4. busy 中は全 Zoom false
    st.is_busy = True
    state = ctrl.get_zoom_action_state()
    assert state == {"zoom_in": False, "zoom_out": False, "zoom_reset": False}
    st.is_busy = False
    
    # 5. analysis_result_valid == False でも duration が有効なら Zoom は有効になり得る
    st.analysis_result_valid = False
    state = ctrl.get_zoom_action_state()
    assert state["zoom_reset"] == True
