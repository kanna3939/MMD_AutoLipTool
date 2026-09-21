from gui_wx.ui_state import UiState


def test_mmd_wav_export_not_ready_without_analysis_wav():
    state = UiState()

    assert state.mmd_wav_export_ready is False


def test_mmd_wav_export_ready_with_analysis_wav_result():
    state = UiState()
    state.selected_analysis_wav = object()

    assert state.mmd_wav_export_ready is True
