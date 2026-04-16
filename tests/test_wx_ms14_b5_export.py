import pytest
import wx
import os
from unittest.mock import MagicMock, patch
from gui_wx.app_controller import AppController
from gui_wx.ui_state import UiState
from gui.settings_store import SettingsStore, SettingsSaveResult

class MockView:
    def __init__(self):
        self.ui_state = UiState()
        self.status = ""
        self.save_path = None
        self.destroyed = False

    def update_status(self, msg):
        self.status = msg

    def show_vmd_save_dialog_and_get_path(self, default_dir):
        return self.save_path

    def get_morph_upper_limit(self): return 1.0
    def get_closing_hold_frames(self): return 1
    def get_closing_softness_frames(self): return 1

    def Destroy(self):
        self.destroyed = True

def test_vmd_export_success():
    view = MockView()
    view.ui_state.analysis_result_valid = True
    view.ui_state.current_timing_plan = MagicMock()
    view.ui_state.selected_text_path = "dummy_text.txt"
    view.ui_state.selected_wav_path = "dummy_wav.wav"
    view.save_path = "out.vmd"
    
    controller = AppController(view)
    controller.settings_store.save = MagicMock(return_value=SettingsSaveResult(True, True, None, False, False, None))
    
    with patch("gui_wx.app_controller.generate_vmd_from_text_wav", autospec=True) as mock_gen, \
         patch("wx.MessageBox"):
        controller.request_save_vmd()
        
        mock_gen.assert_called_once_with(
            text_path="dummy_text.txt",
            wav_path="dummy_wav.wav",
            output_path="out.vmd",
            timing_plan=view.ui_state.current_timing_plan,
            closing_hold_frames=1,
            closing_softness_frames=1,
            upper_limit=1.0
        )
        assert view.status == "VMD保存成功"
        assert controller._pending_save is True

def test_settings_save_coalescing_and_busy():
    view = MockView()
    controller = AppController(view)
    controller.settings_store.save = MagicMock(return_value=SettingsSaveResult(True, True, None, False, False, None))
    
    controller.request_settings_save()
    assert controller._pending_save is True
    
    # Simulate busy, save should not flush
    view.ui_state.is_busy = True
    controller.flush_pending_save()
    assert controller._pending_save is True
    
    # Simulate not busy, save should flush
    view.ui_state.is_busy = False
    controller.flush_pending_save()
    assert controller._pending_save is False
    assert controller.settings_store.save.called

def test_settings_save_closing():
    view = MockView()
    controller = AppController(view)
    controller.settings_store.save = MagicMock(return_value=SettingsSaveResult(True, True, None, False, False, None))
    
    controller.request_settings_save()
    view.ui_state.is_busy = True
    controller.request_exit()
    
    assert view.destroyed
    assert controller.settings_store.save.called

def test_merge_save_settings_store(tmp_path):
    store = SettingsStore(tmp_path / "test.ini")
    
    # Build initial arbitrary ini
    store.settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store.settings_path, "w", encoding="utf-8") as f:
        f.write("[unknown_section]\nmy_key = 123\n")
        
    settings = store.default_settings()
    store.save(settings)
    
    with open(store.settings_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "[unknown_section]" in content
        assert "my_key = 123" in content
        assert "[ui]" in content

def test_closeEvent_save_failure_is_non_blocking():
    view = MockView()
    controller = AppController(view)
    controller.settings_store.save = MagicMock(return_value=SettingsSaveResult(False, False, "error", False, False, None))
    
    with patch("wx.MessageBox") as mock_box:
        controller._pending_save = True
        controller.request_exit()
        
        mock_box.assert_not_called()
        assert view.destroyed

def test_dialog_dir_updated_on_load():
    with patch("gui_wx.main_frame.wx.MessageBox"), \
         patch("gui_wx.main_frame.os.path.exists", return_value=True), \
         patch("gui_wx.main_frame.os.path.isdir", return_value=False), \
         patch("builtins.open", unittest.mock.mock_open(read_data="dummy")), \
         patch("gui_wx.main_frame.analyze_wav_file"), \
         patch("gui_wx.main_frame._validate_and_clean_text", return_value="dummy"), \
         patch("gui_wx.main_frame.text_to_hiragana", return_value="dummy"), \
         patch("gui_wx.main_frame.hiragana_to_vowel_string", return_value="dummy"):
         
        from gui_wx.main_frame import MainFrame
        try:
            app = wx.App()
        except Exception:
            pass # App may already exist in tests
            
        frame = MainFrame(None, default_settings={})
        
        # Test Text load
        frame._open_text_file(quiet_path="C:/dummy/path/text.txt")
        assert frame.ui_state.last_text_dialog_dir == "C:/dummy/path".replace("/", os.sep)
        
        # Test Wav load
        frame._open_wav_file(quiet_path="C:/dummy/path/audio.wav")
        assert frame.ui_state.last_wav_dialog_dir == "C:/dummy/path".replace("/", os.sep)
        
        frame.Destroy()
