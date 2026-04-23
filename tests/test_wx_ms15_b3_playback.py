import pytest
from unittest.mock import MagicMock
from gui_wx.app_controller import AppController
from gui_wx.ui_state import UiState
from gui_wx.playback_controller import PlaybackController
import wx

@pytest.fixture(scope="session", autouse=True)
def wx_app():
    app = wx.App()
    yield app
    app.Destroy()

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.ui_state = UiState()
    return view

@pytest.fixture
def app_controller(mock_view):
    controller = AppController(mock_view)
    controller.playback_controller = MagicMock(spec=PlaybackController)
    return controller

def test_playback_play_success(app_controller, mock_view):
    st = mock_view.ui_state
    st.selected_wav_path = "dummy.wav"
    
    app_controller.playback_controller.play.return_value = True
    app_controller.request_playback_play()
    
    assert st.is_playing is True
    assert st.playback_position_sec == 0.0
    assert st.loaded_playback_path == "dummy.wav"
    mock_view.set_playback_position_sec.assert_called_with(0.0)
    app_controller.playback_controller.play.assert_called_once_with("dummy.wav")

def test_playback_play_failure(app_controller, mock_view):
    st = mock_view.ui_state
    st.selected_wav_path = "dummy.wav"
    
    app_controller.playback_controller.play.return_value = False
    
    # We patch wx.MessageBox so the test doesn't block
    import wx
    original_messagebox = wx.MessageBox
    wx.MessageBox = MagicMock()
    try:
        app_controller.request_playback_play()
        
        assert st.is_playing is False
        mock_view.clear_playback_cursor.assert_called_once()
    finally:
        wx.MessageBox = original_messagebox

def test_playback_stop(app_controller, mock_view):
    st = mock_view.ui_state
    st.is_playing = True
    st.playback_position_sec = 1.5
    
    app_controller.request_playback_stop()
    
    app_controller.playback_controller.stop.assert_called_once()
    assert st.is_playing is False
    assert st.playback_position_sec == 0.0
    mock_view.clear_playback_cursor.assert_called_once()
    mock_view.set_playback_position_sec.assert_called_with(0.0)

def test_playback_repress_ignored(app_controller, mock_view):
    st = mock_view.ui_state
    st.selected_wav_path = "dummy.wav"
    st.is_playing = True
    
    app_controller.request_playback_play()
    
    app_controller.playback_controller.play.assert_not_called()

def test_playback_busy_ignored(app_controller, mock_view):
    st = mock_view.ui_state
    st.selected_wav_path = "dummy.wav"
    st.is_busy = True
    
    app_controller.request_playback_play()
    
    app_controller.playback_controller.play.assert_not_called()

def test_playback_update(app_controller, mock_view):
    st = mock_view.ui_state
    
    app_controller._on_playback_update(1.23)
    
    assert st.playback_position_sec == 1.23
    mock_view.set_playback_position_sec.assert_called_with(1.23)

def test_playback_finished(app_controller, mock_view):
    st = mock_view.ui_state
    st.is_playing = True
    
    app_controller._on_playback_finished()
    
    assert st.is_playing is False
    app_controller.playback_controller.stop.assert_called_once()
