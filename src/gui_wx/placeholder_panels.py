from collections.abc import Sequence

import wx
from gui_wx.waveform_panel import WaveformPanel
from gui_wx.preview_panel import PreviewPanel
from gui_wx.theme import ThemeManager
from src.core.preview_hit_test import PreviewSelectionRequest
from src.core.preview_transform import PreviewData

class PlaceholderContainer(wx.Panel):
    """
    [MS14-B1] 右側表示プレースホルダコンテナ。
    上下2段で波形とPreviewの置き場を確保する。
    [MS15-B2] PreviewPanelを実体化し組み込み。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._ms33c_theme_border = True
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self._init_ui()

    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        ThemeManager.draw_border(dc, self.GetClientRect(), self)

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.pnl_waveform = WaveformPanel(self)
        self.pnl_preview = PreviewPanel(self)

        sizer.Add(self.pnl_waveform, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.pnl_preview, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

        self.on_pan_callback = None
        self.on_scrub_start_callback = None
        self.on_scrub_update_callback = None
        self.on_scrub_end_callback = None
        self.on_seek_callback = None
        self.on_selection_request_callback = None
        self.pnl_waveform.on_scrub_start_callback = self._on_scrub_start
        self.pnl_waveform.on_scrub_update_callback = self._on_scrub_update
        self.pnl_waveform.on_scrub_end_callback = self._on_scrub_end
        self.pnl_waveform.on_seek_callback = self._on_seek
        self.pnl_preview.on_pan_callback = self._on_pan
        self.pnl_preview.on_selection_request_callback = self._on_selection_request

    def _on_pan(self, delta_sec: float):
        if self.on_pan_callback:
            self.on_pan_callback(delta_sec)

    def _on_scrub_start(self, position_sec: float):
        if self.on_scrub_start_callback:
            return self.on_scrub_start_callback(position_sec)
        return False

    def _on_scrub_update(self, position_sec: float):
        if self.on_scrub_update_callback:
            self.on_scrub_update_callback(position_sec)

    def _on_scrub_end(self, position_sec: float):
        if self.on_scrub_end_callback:
            self.on_scrub_end_callback(position_sec)

    def _on_seek(self, position_sec: float):
        if self.on_seek_callback:
            return self.on_seek_callback(position_sec)
        return False

    def _on_selection_request(self, request: PreviewSelectionRequest):
        if self.on_selection_request_callback:
            self.on_selection_request_callback(request)

    # --- View Helpers ---
    def set_waveform_data(self, samples: list[float], duration_sec: float):
        self.pnl_waveform.set_waveform_data(samples, duration_sec)

    def set_waveform_placeholder_text(self, text: str):
        self.pnl_waveform.show_placeholder(text)

    def set_preview_data(self, data: PreviewData, duration_sec: float):
        self.pnl_preview.set_preview_data(data, duration_sec)

    def set_identity_aware_preview_data(
        self,
        data: PreviewData,
        duration_sec: float,
        base_plan_identity_digest: str,
        final_output_binding: str | None = None,
    ):
        self.pnl_preview.set_identity_aware_preview_data(
            data,
            duration_sec,
            base_plan_identity_digest,
            final_output_binding,
        )

    def set_preview_placeholder_text(
        self,
        text: str,
        *,
        output_morph_names: Sequence[str] | None = None,
        loading: bool = False,
    ):
        if output_morph_names is None:
            self.pnl_preview.set_placeholder(text, loading=loading)
        else:
            self.pnl_preview.set_placeholder(
                text,
                output_morph_names=output_morph_names,
                loading=loading,
            )

    def set_playback_position_sec(self, position_sec: float | None):
        self.pnl_waveform.set_playback_position_sec(position_sec)
        self.pnl_preview.set_playback_position_sec(position_sec)

    def set_viewport_sec(self, start_sec: float, end_sec: float):
        self.pnl_waveform.set_viewport_sec(start_sec, end_sec)
        self.pnl_preview.set_viewport_sec(start_sec, end_sec)

    def set_frame_grid_enabled(self, enabled: bool) -> None:
        value = bool(enabled)
        self.pnl_waveform.set_frame_grid_enabled(value)
        self.pnl_preview.set_frame_grid_enabled(value)

    def clear_viewport_sec(self):
        self.pnl_waveform.clear_viewport_sec()
        self.pnl_preview.clear_viewport_sec()

    def clear_playback_cursor(self):
        self.pnl_waveform.set_playback_position_sec(None)
        self.pnl_preview.clear_playback_cursor()

    def set_selected_source_event_index(self, index: int | None):
        """[MS16-B6] プレビューへの選択状態の伝搬"""
        self.pnl_preview.set_selected_source_event_index(index)

    def clear_selection(self):
        """[MS16-B6] プレビューの選択状態のクリア"""
        self.pnl_preview.clear_selection()

    def get_selected_shape_summary(self) -> str | None:
        """[MS16-B6] プレビューの選択中summaryの取得"""
        return self.pnl_preview.get_selected_shape_summary()

