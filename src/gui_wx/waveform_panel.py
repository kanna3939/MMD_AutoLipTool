import wx

class WaveformPanel(wx.Panel):
    """
    [MS15-B1] 波形表示用の wx.Panel.
    WAV 読込後に取得されたダウンサンプル済みデータを元に、
    可視幅に合わせた簡易描画 (結線) を行う。
    再生(B3)の受け口として playback_position_sec をサポートする。
    """
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self.SetMinSize((-1, 140))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self._samples: list[float] = []
        self._duration_sec: float = 0.0
        self._playback_position_sec: float | None = None
        self._viewport_start_sec: float = 0.0
        self._viewport_end_sec: float = 0.0
        self._placeholder_msg: str = "WAVファイルが読み込まれていません"
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)

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

    def _on_size(self, event):
        self.Refresh()
        event.Skip()

    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        rect = self.GetClientRect()
        
        # Background
        dc.SetBackground(wx.Brush(wx.Colour(32, 38, 47)))
        dc.Clear()
        
        if not self._samples or self._duration_sec <= 0.0:
            self._draw_placeholder(dc, rect)
            return
            
        self._draw_grid(gc, rect)
        self._draw_waveform(gc, rect)
        self._draw_labels(gc, rect)
        self._draw_cursor(gc, rect)
        
    def _draw_placeholder(self, dc: wx.DC, rect: wx.Rect):
        dc.SetTextForeground(wx.Colour(174, 182, 194))
        font = self.GetFont()
        dc.SetFont(font)
        text_w, text_h = dc.GetTextExtent(self._placeholder_msg)
        x = max(0, (rect.width - text_w) // 2)
        y = max(0, (rect.height - text_h) // 2)
        dc.DrawText(self._placeholder_msg, x, y)

    def _draw_grid(self, gc: wx.GraphicsContext, rect: wx.Rect):
        path = gc.CreatePath()
        path.MoveToPoint(0, rect.height / 2.0)
        path.AddLineToPoint(rect.width, rect.height / 2.0)
        pen = wx.Pen(wx.Colour(81, 96, 114), 1, wx.PENSTYLE_SOLID)
        gc.SetPen(pen)
        gc.StrokePath(path)

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
            
        pen = wx.Pen(wx.Colour(124, 198, 254), 1, wx.PENSTYLE_SOLID)
        gc.SetPen(pen)
        gc.StrokePath(path)

    def _draw_labels(self, gc: wx.GraphicsContext, rect: wx.Rect):
        font = self.GetFont()
        gc.SetFont(font, wx.Colour(216, 222, 233))
        
        left_text = f"{self._viewport_start_sec:.2f} sec"
        gc.DrawText(left_text, 5, rect.height - 20)
        
        right_text = f"{self._viewport_end_sec:.2f} sec"
        tw, th = gc.GetTextExtent(right_text)
        gc.DrawText(right_text, rect.width - tw - 5, rect.height - 20)

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
            
            pen = wx.Pen(wx.Colour(248, 113, 113), 2, wx.PENSTYLE_SOLID)
            gc.SetPen(pen)
            gc.StrokePath(path)
