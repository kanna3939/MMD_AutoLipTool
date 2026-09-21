import wx
import pytest
from gui_wx.waveform_panel import WaveformPanel
from gui_wx.placeholder_panels import PlaceholderContainer
from tests.helpers import destroy_wx_app, get_or_create_wx_app

def test_waveform_panel_instantiation():
    app, owns_app = get_or_create_wx_app(wx.App)
    frame = wx.Frame(None)
    panel = WaveformPanel(frame)
    
    assert panel is not None
    assert isinstance(panel, wx.Panel)
    
    # Check default state
    assert panel._duration_sec == 0.0
    assert len(panel._samples) == 0
    assert "読み込まれていません" in panel._placeholder_msg

    # Check set_waveform_data
    panel.set_waveform_data([0.1, -0.1, 0.5], 1.5)
    assert panel._duration_sec == 1.5
    assert len(panel._samples) == 3
    assert panel._placeholder_msg == ""

    # Check placeholder fallback
    panel.show_placeholder("エラー")
    assert panel._duration_sec == 0.0
    assert panel._placeholder_msg == "エラー"
    
    destroy_wx_app(app, frame, owns_app=owns_app)

def test_placeholder_container_b1():
    app, owns_app = get_or_create_wx_app(wx.App)
    frame = wx.Frame(None)
    container = PlaceholderContainer(frame)
    
    # pnl_waveform should be WaveformPanel
    assert isinstance(container.pnl_waveform, WaveformPanel)
    
    # set_waveform_data route check
    container.set_waveform_data([0.0], 1.0)
    assert container.pnl_waveform._duration_sec == 1.0
    
    # placeholder route check
    container.set_waveform_placeholder_text("TEST_MSG")
    assert container.pnl_waveform._placeholder_msg == "TEST_MSG"
    
    destroy_wx_app(app, frame, owns_app=owns_app)

