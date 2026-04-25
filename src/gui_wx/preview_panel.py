import wx
from dataclasses import dataclass
from gui.preview_transform import PreviewData, PREVIEW_ROW_VOWELS, empty_preview_data

@dataclass
class PreviewModel:
    """[MS15-B2] Previewの表示用状態を保持するデータモデル"""
    data: PreviewData = empty_preview_data()
    duration_sec: float = 0.0
    playback_position_sec: float | None = None
    is_valid: bool = False
    viewport_start_sec: float = 0.0
    viewport_end_sec: float = 0.0

    def set_data(self, data: PreviewData, duration_sec: float):
        self.data = data
        self.duration_sec = duration_sec
        self.is_valid = True
        if self.viewport_start_sec == 0.0 and self.viewport_end_sec == 0.0:
            self.viewport_end_sec = duration_sec

    def clear(self):
        self.data = empty_preview_data()
        self.duration_sec = 0.0
        self.playback_position_sec = None
        self.is_valid = False
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = 0.0

    def set_playback_position(self, position_sec: float | None):
        self.playback_position_sec = position_sec

    def set_viewport_sec(self, start_sec: float, end_sec: float):
        self.viewport_start_sec = start_sec
        self.viewport_end_sec = end_sec
        
    def clear_viewport_sec(self):
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = self.duration_sec


class PreviewRenderer:
    """[MS15-B2] Previewの描画を担当するレンダラー"""
    def __init__(self, model: PreviewModel):
        self.model = model
        # 各母音の色定義 (既存のQt実装等に合わせる、あるいは適当な区別できる色)
        self.vowel_colors = {
            "あ": wx.Colour(239, 83, 80, 180),  # Red
            "い": wx.Colour(66, 165, 245, 180), # Blue
            "う": wx.Colour(102, 187, 106, 180),# Green
            "え": wx.Colour(255, 167, 38, 180), # Orange
            "お": wx.Colour(171, 71, 188, 180), # Purple
        }

    def render(self, gc: wx.GraphicsContext, rect: wx.Rect, font: wx.Font):
        # 背景
        brush = wx.Brush(wx.Colour(32, 38, 47))
        gc.SetBrush(brush)
        gc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

        if not self.model.is_valid or self.model.duration_sec <= 0.0:
            return

        self._draw_grid_and_labels(gc, rect, font)
        self._draw_lanes(gc, rect)
        self._draw_cursor(gc, rect)

    def _draw_grid_and_labels(self, gc: wx.GraphicsContext, rect: wx.Rect, font: wx.Font):
        # 5段レーンの枠線と母音ラベル
        lane_height = rect.height / 5.0
        
        pen = wx.Pen(wx.Colour(81, 96, 114), 1, wx.PENSTYLE_SOLID)
        gc.SetPen(pen)
        
        gc.SetFont(font, wx.Colour(216, 222, 233))
        
        for i, vowel in enumerate(PREVIEW_ROW_VOWELS):
            y = int(i * lane_height)
            # 水平線
            if i > 0:
                path = gc.CreatePath()
                path.MoveToPoint(0, y)
                path.AddLineToPoint(rect.width, y)
                gc.StrokePath(path)
            
            # 母音ラベル
            gc.DrawText(vowel, 5, y + 2)

    def _time_to_x(self, time_sec: float, rect_width: float) -> float:
        span = self.model.viewport_end_sec - self.model.viewport_start_sec
        if span <= 0.0:
            return 0.0
        return ((time_sec - self.model.viewport_start_sec) / span) * rect_width

    def _draw_lanes(self, gc: wx.GraphicsContext, rect: wx.Rect):
        lane_height = rect.height / 5.0

        for i, vowel in enumerate(PREVIEW_ROW_VOWELS):
            row_data = next((r for r in self.model.data.rows if r.vowel == vowel), None)
            if not row_data:
                continue
            
            y_base = i * lane_height
            color = self.vowel_colors.get(vowel, wx.Colour(200, 200, 200, 180))
            brush = wx.Brush(color)
            pen = wx.Pen(wx.Colour(color.Red(), color.Green(), color.Blue(), 255), 1, wx.PENSTYLE_SOLID)
            
            gc.SetBrush(brush)
            gc.SetPen(pen)
            
            for segment in row_data.segments:
                # duration_secの範囲外なら描画しない（clampの結果、可視幅が0になるものを省く）
                if segment.end_sec < self.model.viewport_start_sec or segment.start_sec > self.model.viewport_end_sec:
                    continue
                    
                x_start = self._time_to_x(segment.start_sec, rect.width)
                x_end = self._time_to_x(segment.end_sec, rect.width)
                w = x_end - x_start
                if w <= 0:
                    continue
                
                # intensityを使って高さを表現 (最大でlane_height - 4)
                h = max(2.0, (lane_height - 4) * segment.intensity)
                y = y_base + (lane_height - h) / 2.0
                
                # 角丸矩形で描画（shape_kindの詳細によらず区間として描く最小実装）
                gc.DrawRoundedRectangle(x_start, y, w, h, 2.0)

    def _draw_cursor(self, gc: wx.GraphicsContext, rect: wx.Rect):
        if self.model.playback_position_sec is None:
            return
            
        span = self.model.viewport_end_sec - self.model.viewport_start_sec
        if span <= 0:
            return
            
        if self.model.viewport_start_sec <= self.model.playback_position_sec <= self.model.viewport_end_sec:
            x = self._time_to_x(self.model.playback_position_sec, rect.width)
            
            path = gc.CreatePath()
            path.MoveToPoint(x, 0)
            path.AddLineToPoint(x, rect.height)
            
            pen = wx.Pen(wx.Colour(248, 113, 113), 2, wx.PENSTYLE_SOLID)
            gc.SetPen(pen)
            gc.StrokePath(path)

class PreviewPanel(wx.Panel):
    """
    [MS15-B2] プレビュー表示用パネル。
    5母音固定5段レーンの確認用可視化を行う。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self.SetMinSize((-1, 150))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.model = PreviewModel()
        self.renderer = PreviewRenderer(self.model)
        self.placeholder_msg: str = "[Placeholder] Preview エリア"
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)

    def set_preview_data(self, data: PreviewData, duration_sec: float):
        """[MS15-B2] 解析成功時にプレビューデータをセットする"""
        self.model.set_data(data, duration_sec)
        self.Refresh()

    def set_placeholder(self, msg: str):
        """[MS15-B2] 解析失敗時などにプレースホルダへ戻す"""
        self.model.clear()
        self.placeholder_msg = msg
        self.Refresh()

    def set_playback_position_sec(self, position_sec: float | None):
        """[MS15-B2] 再生位置カーソルの受け口 API"""
        self.model.set_playback_position(position_sec)
        self.Refresh()

    def set_viewport_sec(self, start_sec: float, end_sec: float):
        """[MS15-B4] 表示範囲の更新"""
        self.model.set_viewport_sec(start_sec, end_sec)
        self.Refresh()

    def clear_viewport_sec(self):
        """[MS15-B4] 表示範囲のクリア"""
        self.model.clear_viewport_sec()
        self.Refresh()

    def clear_playback_cursor(self):
        """[MS15-B2] 再生位置カーソルクリアの受け口 API"""
        self.model.set_playback_position(None)
        self.Refresh()

    def _on_size(self, event):
        self.Refresh()
        event.Skip()

    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        rect = self.GetClientRect()
        
        if not self.model.is_valid:
            # Placeholder描画
            dc.SetBackground(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)))
            dc.Clear()
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
            font = self.GetFont()
            dc.SetFont(font)
            # Center text
            text_lines = self.placeholder_msg.split('\n')
            total_h = sum(dc.GetTextExtent(line)[1] for line in text_lines)
            y = max(0, (rect.height - total_h) // 2)
            for line in text_lines:
                tw, th = dc.GetTextExtent(line)
                x = max(0, (rect.width - tw) // 2)
                dc.DrawText(line, x, y)
                y += th
            return

        self.renderer.render(gc, rect, self.GetFont())
