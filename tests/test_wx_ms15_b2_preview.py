import wx
import pytest
from gui_wx.preview_panel import PreviewPanel, PreviewModel, PreviewRenderer
from gui_wx.placeholder_panels import PlaceholderContainer
from src.core.preview_transform import empty_preview_data
from tests.helpers import destroy_wx_app, get_or_create_wx_app

def test_preview_panel_instantiation():
    app, owns_app = get_or_create_wx_app(wx.App)
    frame = wx.Frame(None)
    panel = PreviewPanel(frame)
    
    assert panel is not None
    assert isinstance(panel, wx.Panel)
    
    # Check default state
    assert panel.model.is_valid is False
    assert panel.model.duration_sec == 0.0
    assert "Preview エリア" in panel.placeholder_msg

    # Check set_preview_data
    panel.set_preview_data(empty_preview_data(), 2.5)
    assert panel.model.is_valid is True
    assert panel.model.duration_sec == 2.5

    # Check placeholder fallback
    panel.set_placeholder("エラー")
    assert panel.model.is_valid is False
    assert panel.model.duration_sec == 0.0
    assert panel.placeholder_msg == "エラー"

    # Check cursor API
    panel.set_playback_position_sec(1.0)
    assert panel.model.playback_position_sec == 1.0
    panel.clear_playback_cursor()
    assert panel.model.playback_position_sec is None
    
    destroy_wx_app(app, frame, owns_app=owns_app)

def test_placeholder_container_b2():
    app, owns_app = get_or_create_wx_app(wx.App)
    frame = wx.Frame(None)
    container = PlaceholderContainer(frame)
    
    # pnl_preview should be PreviewPanel
    assert isinstance(container.pnl_preview, PreviewPanel)
    
    # set_preview_data route check
    container.set_preview_data(empty_preview_data(), 3.0)
    assert container.pnl_preview.model.duration_sec == 3.0
    assert container.pnl_preview.model.is_valid is True
    
    # placeholder route check
    container.set_preview_placeholder_text("TEST_MSG")
    assert container.pnl_preview.placeholder_msg == "TEST_MSG"
    assert container.pnl_preview.model.is_valid is False
    
    destroy_wx_app(app, frame, owns_app=owns_app)
