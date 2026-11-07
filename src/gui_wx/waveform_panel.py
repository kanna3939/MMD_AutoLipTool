import wx
from gui_wx.frame_grid import FrameGridTick, calculate_frame_grid_ticks
from gui_wx.theme import ThemeManager


_SCRUB_DRAG_SCALE = 1.0


class WaveformPanel(wx.Panel):
    """
    [MS15-B1] 波形表示用の wx.Panel.
    WAV 読込後に取得されたダウンサンプル済みデータを元に、
    可視幅に合わせた簡易描画 (結線) を行う。
    再生(B3)の受け口として playback_position_sec をサポートする。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._ms33c_theme_border = True
        self.SetMinSize((-1, 140))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)
        
        self._samples: list[float] = []
        self._duration_sec: float = 0.0
        self._playback_position_sec: float | None = None
        self._viewport_start_sec: float = 0.0
        self._viewport_end_sec: float = 0.0
        self._frame_grid_enabled = True
        self._placeholder_msg: str = "WAVファイルが読み込まれていません"
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        
        self.on_scrub_start_callback = None
        self.on_scrub_update_callback = None
        self.on_scrub_end_callback = None
        self.on_seek_callback = None
        self._drag_start_x = None
        self._drag_start_y = None
        self._drag_start_position_sec = None
        self._last_pointer_x = None
        self._scrub_active = False
        self._scrub_rejected = False
        self._last_scrub_position_sec = None
        self.Bind(wx.EVT_LEFT_DOWN, self._on_mouse_down)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        self.Bind(wx.EVT_LEFT_UP, self._on_mouse_up)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self._on_mouse_capture_lost)

    def set_waveform_data(self, samples: list[float], duration_sec: float):
        self._samples = samples
        self._duration_sec = duration_sec
        if self._viewport_end_sec == 0.0 and self._viewport_start_sec == 0.0:
            self._viewport_end_sec = duration_sec
        self._placeholder_msg = ""
        self.Refresh()

    def show_placeholder(self, msg: str):
        self._samples = []
        self._duration_sec = 0.0
        self._playback_position_sec = None
        self._placeholder_msg = msg
        self.Refresh()

    def set_playback_position_sec(self, position_sec: float | None):
        """[MS15-B1] 再生位置(B3で本格更新予定)の受け口"""
        self._playback_position_sec = position_sec
        self.Refresh()

    def set_viewport_sec(self, start_sec: float, end_sec: float) -> None:
        """[MS15-B4] 表示範囲の更新"""
        self._viewport_start_sec = start_sec
        self._viewport_end_sec = end_sec
        self.Refresh()

    def clear_viewport_sec(self) -> None:
        """[MS15-B4] 表示範囲のクリア (full-rangeへ戻す)"""
        self._viewport_start_sec = 0.0
        self._viewport_end_sec = self._duration_sec
        self.Refresh()

    def set_frame_grid_enabled(self, enabled: bool) -> None:
        value = bool(enabled)
        if self._frame_grid_enabled == value:
            return
        self._frame_grid_enabled = value
        self.Refresh()

    def _frame_grid_ticks(self, rect: wx.Rect) -> tuple[FrameGridTick, ...]:
        return calculate_frame_grid_ticks(
            self._viewport_start_sec,
            self._viewport_end_sec,
            self._duration_sec,
            rect.width,
            enabled=self._frame_grid_enabled,
        )

    def _on_size(self, event):
        self.Refresh()
        event.Skip()

    def _on_mouse_down(self, event):
        self._reset_drag()
        if self._duration_sec > 0 and self._viewport_end_sec > self._viewport_start_sec:
            position = event.GetPosition()
            self._drag_start_x = position.x
            self._drag_start_y = position.y
            self._drag_start_position_sec = self._position_for_x(position.x)
            self._last_pointer_x = position.x
            self._scrub_active = False
            self._scrub_rejected = False
            self._last_scrub_position_sec = None
        if self._drag_start_x is not None and not self.HasCapture():
            self.CaptureMouse()
        event.Skip()

    def _on_mouse_motion(self, event):
        if event.Dragging() and event.LeftIsDown() and self._drag_start_x is not None:
            position = event.GetPosition()
            threshold = max(1, int(self.FromDIP(4)))
            dx = position.x - self._drag_start_x
            dy = position.y - self._drag_start_y
            if not self._scrub_active and not self._scrub_rejected:
                if dx * dx + dy * dy < threshold * threshold:
                    event.Skip()
                    return
                scrub_position = self._scrub_position_for_pointer_x(position.x)
                if self.on_scrub_start_callback is None:
                    self._scrub_rejected = True
                else:
                    callback_result = self.on_scrub_start_callback(scrub_position)
                    if callback_result is False:
                        self._scrub_rejected = True
                    else:
                        self._scrub_active = True
                        self._last_scrub_position_sec = scrub_position
            elif self._scrub_active:
                scrub_position = self._scrub_position_for_pointer_x(position.x)
                self._last_scrub_position_sec = scrub_position
                if self.on_scrub_update_callback:
                    self.on_scrub_update_callback(scrub_position)
        event.Skip()

    def _on_mouse_up(self, event):
        if self._scrub_active:
            final_position = self._scrub_position_for_pointer_x(
                event.GetPosition().x
            )
            if (
                final_position != self._last_scrub_position_sec
                and self.on_scrub_update_callback
            ):
                self.on_scrub_update_callback(final_position)
            self._finish_scrub(final_position)
        elif self._drag_start_x is not None and not self._scrub_rejected:
            if self.on_seek_callback:
                self.on_seek_callback(
                    self._position_for_x(event.GetPosition().x)
                )
            self._reset_drag()
        else:
            self._reset_drag()
        if self.HasCapture():
            self.ReleaseMouse()
        event.Skip()

    def _on_mouse_capture_lost(self, event):
        if self._scrub_active:
            self._finish_scrub(self._last_scrub_position_sec)
        else:
            self._reset_drag()
        event.Skip()

    def _position_for_x(self, x: int) -> float:
        rect_width = self.GetClientRect().width
        if rect_width <= 0:
            return max(0.0, min(self._duration_sec, self._viewport_start_sec))
        bounded_x = max(0, min(rect_width, int(x)))
        ratio = bounded_x / rect_width
        position = self._viewport_start_sec + (
            (self._viewport_end_sec - self._viewport_start_sec) * ratio
        )
        return max(0.0, min(self._duration_sec, position))

    def _scrub_position_for_pointer_x(self, x: int) -> float:
        rect_width = self.GetClientRect().width
        if rect_width <= 0:
            position = self._last_scrub_position_sec
            if position is None:
                position = self._drag_start_position_sec
            return 0.0 if position is None else position

        if self._last_scrub_position_sec is None:
            base_position = self._drag_start_position_sec
            base_x = self._drag_start_x
        else:
            base_position = self._last_scrub_position_sec
            base_x = self._last_pointer_x
        if base_position is None or base_x is None:
            return self._position_for_x(x)

        span = self._viewport_end_sec - self._viewport_start_sec
        delta_sec = ((int(x) - int(base_x)) / rect_width) * span
        self._last_pointer_x = int(x)
        position = base_position + delta_sec * _SCRUB_DRAG_SCALE
        return max(0.0, min(self._duration_sec, position))

    def _finish_scrub(self, position_sec: float | None):
        final_position = (
            self._last_scrub_position_sec if position_sec is None else position_sec
        )
        if self.on_scrub_end_callback and final_position is not None:
            self.on_scrub_end_callback(final_position)
        self._reset_drag()

    def _reset_drag(self):
        self._drag_start_x = None
        self._drag_start_y = None
        self._drag_start_position_sec = None
        self._last_pointer_x = None
        self._scrub_active = False
        self._scrub_rejected = False
        self._last_scrub_position_sec = None

    def _on_paint(self, event):
        rect = self.GetClientRect()
        if rect.width <= 0 or rect.height <= 0:
            wx.PaintDC(self)  # Consume the paint event
            return
            
        dc = wx.PaintDC(self)
        palette = ThemeManager.get_palette()
        
        # Background
        dc.SetBrush(wx.Brush(palette.preview_lane_bg))
        dc.SetPen(wx.Pen(palette.preview_lane_bg, 1, wx.PENSTYLE_TRANSPARENT))
        dc.DrawRectangle(rect)
        
        if not self._samples or self._duration_sec <= 0.0:
            self._draw_placeholder(dc, rect)
            ThemeManager.draw_border(dc, rect, self)
            return
            
        gc = wx.GraphicsContext.Create(dc)
        if gc is None:
            ThemeManager.draw_border(dc, rect, self)
            return
            
        frame_ticks = self._frame_grid_ticks(rect)
        self._draw_grid(gc, rect, frame_ticks)
        self._draw_waveform(gc, rect)
        self._draw_labels(gc, rect, frame_ticks)
        self._draw_cursor(gc, rect)
        ThemeManager.draw_border(gc, rect, self)
        
    def _draw_placeholder(self, dc: wx.DC, rect: wx.Rect):
        palette = ThemeManager.get_palette()
        dc.SetTextForeground(palette.muted_text)
        font = self.GetFont()
        dc.SetFont(font)
        text_w, text_h = dc.GetTextExtent(self._placeholder_msg)
        x = max(0, (rect.width - text_w) // 2)
        y = max(0, (rect.height - text_h) // 2)
        dc.DrawText(self._placeholder_msg, x, y)

    def _draw_grid(
        self,
        gc: wx.GraphicsContext,
        rect: wx.Rect,
        frame_ticks: tuple[FrameGridTick, ...],
    ):
        minor_path = gc.CreatePath()
        major_path = gc.CreatePath()
        for tick in frame_ticks:
            path = major_path if tick.is_major else minor_path
            path.MoveToPoint(tick.x, 0)
            path.AddLineToPoint(tick.x, rect.height)

        palette = ThemeManager.get_palette()
        if any(tick.is_minor for tick in frame_ticks):
            gc.SetPen(wx.Pen(palette.waveform_grid, 1, wx.PENSTYLE_DOT))
            gc.StrokePath(minor_path)
        if any(tick.is_major for tick in frame_ticks):
            gc.SetPen(wx.Pen(palette.waveform_grid, 1, wx.PENSTYLE_SOLID))
            gc.StrokePath(major_path)

        center_path = gc.CreatePath()
        center_path.MoveToPoint(0, rect.height / 2.0)
        center_path.AddLineToPoint(rect.width, rect.height / 2.0)
        gc.SetPen(wx.Pen(palette.waveform_grid, 1, wx.PENSTYLE_SOLID))
        gc.StrokePath(center_path)

    def _draw_waveform(self, gc: wx.GraphicsContext, rect: wx.Rect):
        if not self._samples:
            return
            
        path = gc.CreatePath()
        width = rect.width
        height = rect.height
        half_h = height / 2.0
        
        num_samples = len(self._samples)
        if width <= 0 or num_samples == 0:
            return
            
        span = self._viewport_end_sec - self._viewport_start_sec
        if span <= 0 or self._duration_sec <= 0:
            return
            
        start_sample_idx = int((self._viewport_start_sec / self._duration_sec) * num_samples)
        end_sample_idx = int((self._viewport_end_sec / self._duration_sec) * num_samples)
        
        start_sample_idx = max(0, start_sample_idx)
        end_sample_idx = min(num_samples, end_sample_idx)
        
        visible_samples = end_sample_idx - start_sample_idx
        if visible_samples <= 0:
            return
            
        samples_per_pixel = visible_samples / width
        
        if samples_per_pixel < 1.0:
            # 高倍率ズーム時: サンプル単位で正確なX座標を計算し、折れ線で結ぶ
            is_first = True
            for i in range(visible_samples):
                sample_idx = start_sample_idx + i
                if sample_idx >= num_samples:
                    break
                    
                x = (i / visible_samples) * width
                val = self._samples[sample_idx]
                y = half_h - (val * half_h)
                
                if is_first:
                    path.MoveToPoint(x, y)
                    is_first = False
                else:
                    path.AddLineToPoint(x, y)
        else:
            # 低倍率時: ピクセルごとに min/max のエンベロープを連続パスで描画する
            is_first = True
            for x in range(width):
                start_idx = start_sample_idx + int(x * samples_per_pixel)
                end_idx = start_sample_idx + int((x + 1) * samples_per_pixel)
                if start_idx >= num_samples:
                    break
                if end_idx > num_samples:
                    end_idx = num_samples
                if start_idx == end_idx:
                    end_idx = start_idx + 1
                    
                chunk = self._samples[start_idx:end_idx]
                min_val = min(chunk)
                max_val = max(chunk)
                
                y_min = half_h - (max_val * half_h)
                y_max = half_h - (min_val * half_h)
                
                if abs(y_max - y_min) < 1.0:
                    y_max = y_min + 1.0
                
                if is_first:
                    path.MoveToPoint(x, y_min)
                    path.AddLineToPoint(x, y_max)
                    is_first = False
                else:
                    path.AddLineToPoint(x, y_min)
                    path.AddLineToPoint(x, y_max)
            
        palette = ThemeManager.get_palette()
        pen = wx.Pen(palette.waveform_line, 1, wx.PENSTYLE_SOLID)
        gc.SetPen(pen)
        gc.StrokePath(path)

    def _draw_labels(
        self,
        gc: wx.GraphicsContext,
        rect: wx.Rect,
        frame_ticks: tuple[FrameGridTick, ...],
    ):
        palette = ThemeManager.get_palette()
        font = self.GetFont()
        gc.SetFont(font, palette.text_fg)

        left_text = f"{self._viewport_start_sec:.2f} sec"
        left_x = 5
        left_width, _ = gc.GetTextExtent(left_text)
        gc.DrawText(left_text, left_x, rect.height - 20)

        right_text = f"{self._viewport_end_sec:.2f} sec"
        right_width, _ = gc.GetTextExtent(right_text)
        right_x = rect.width - right_width - 5
        gc.DrawText(right_text, right_x, rect.height - 20)

        gc.SetFont(font, palette.muted_text)
        previous_label_right = left_x + left_width + 4
        for tick in frame_ticks:
            if not tick.label_allowed:
                continue
            label = str(tick.frame_no)
            label_width, _ = gc.GetTextExtent(label)
            label_x = int(round(tick.x - label_width / 2.0))
            label_right = label_x + label_width
            if label_x < previous_label_right:
                continue
            if label_right + 4 > right_x:
                continue
            gc.DrawText(label, label_x, rect.height - 20)
            previous_label_right = label_right + 4

    def _draw_cursor(self, gc: wx.GraphicsContext, rect: wx.Rect):
        if self._playback_position_sec is None:
            return
            
        span = self._viewport_end_sec - self._viewport_start_sec
        if span <= 0:
            return
            
        if self._viewport_start_sec <= self._playback_position_sec <= self._viewport_end_sec:
            x = ((self._playback_position_sec - self._viewport_start_sec) / span) * rect.width
            
            path = gc.CreatePath()
            path.MoveToPoint(x, 0)
            path.AddLineToPoint(x, rect.height)
            
            palette = ThemeManager.get_palette()
            pen = wx.Pen(palette.playback_cursor, 2, wx.PENSTYLE_SOLID)
            gc.SetPen(pen)
            gc.StrokePath(path)
