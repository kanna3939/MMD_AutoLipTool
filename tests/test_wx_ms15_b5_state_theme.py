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
