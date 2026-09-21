import wx
from dataclasses import dataclass, field
import math
from typing import Sequence

from src.core.preview_hit_test import (
    PreviewEventHitRegion,
    PreviewHitTestInput,
    PreviewSelectionRequest,
    collect_preview_hit_regions,
    hit_test_preview_event,
)
from src.core.preview_transform import PreviewData, PREVIEW_ROW_VOWELS, empty_preview_data, PreviewSegment
from gui_wx.theme import ThemeManager

@dataclass
class PreviewModel:
    """[MS15-B2] Previewの表示用状態を保持するデータモデル"""
    data: PreviewData = field(default_factory=empty_preview_data)
    duration_sec: float = 0.0
    playback_position_sec: float | None = None
    is_valid: bool = False
    viewport_start_sec: float = 0.0
    viewport_end_sec: float = 0.0
    selected_source_event_index: int | None = None
    base_plan_identity_digest: str | None = None
    render_revision: int = 0

    def set_data(self, data: PreviewData, duration_sec: float):
        self.data = data
        self.duration_sec = duration_sec
        self.is_valid = True
        self.selected_source_event_index = None
        self.base_plan_identity_digest = None
        self.render_revision += 1
        if self.viewport_start_sec == 0.0 and self.viewport_end_sec == 0.0:
            self.viewport_end_sec = duration_sec

    def set_identity_aware_data(
        self,
        data: PreviewData,
        duration_sec: float,
        base_plan_identity_digest: str,
    ) -> bool:
        """Replace canonical Preview data and preserve selection only for the same base."""
        if not isinstance(base_plan_identity_digest, str) or not base_plan_identity_digest:
            raise ValueError("base_plan_identity_digest must be a non-empty string")
        data_changed = (
            not self.is_valid
            or self.data != data
            or self.duration_sec != duration_sec
            or self.base_plan_identity_digest != base_plan_identity_digest
        )
        if not data_changed:
            return False
        same_identity = self.base_plan_identity_digest == base_plan_identity_digest
        self.data = data
        self.duration_sec = duration_sec
        self.is_valid = True
        self.base_plan_identity_digest = base_plan_identity_digest
        self.render_revision += 1
        if not same_identity:
            self.selected_source_event_index = None
        elif (
            self.selected_source_event_index is not None
            and self.find_shape_by_source_event_index(self.selected_source_event_index) is None
        ):
            self.selected_source_event_index = None
        if self.viewport_start_sec == 0.0 and self.viewport_end_sec == 0.0:
            self.viewport_end_sec = duration_sec
        return True

    def clear(
        self,
        *,
        output_morph_names: Sequence[str] = PREVIEW_ROW_VOWELS,
    ):
        self.data = empty_preview_data(output_morph_names=output_morph_names)
        self.duration_sec = 0.0
        self.playback_position_sec = None
        self.is_valid = False
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = 0.0
        self.selected_source_event_index = None
        self.base_plan_identity_digest = None
        self.render_revision += 1

    def set_playback_position(self, position_sec: float | None):
        self.playback_position_sec = position_sec

    def set_viewport_sec(self, start_sec: float, end_sec: float):
        self.viewport_start_sec = start_sec
        self.viewport_end_sec = end_sec
        
    def clear_viewport_sec(self):
        self.viewport_start_sec = 0.0
        self.viewport_end_sec = self.duration_sec

    def find_shape_by_source_event_index(self, index: int) -> PreviewSegment | None:
        if not self.is_valid or index is None:
            return None
        for row in self.data.rows:
            for segment in row.segments:
                if segment.source_event_index == index:
                    return segment
                if index in segment.source_event_indices:
                    return segment
        return None

    def find_event_hit_region(self, index: int) -> PreviewEventHitRegion | None:
        for region in collect_preview_hit_regions(self.data.rows):
            if region.base_event_index == index:
                return region
        return None

    def get_event_hit_regions(self) -> tuple[PreviewEventHitRegion, ...]:
        if not self.is_valid:
            return ()
        return collect_preview_hit_regions(self.data.rows)


@dataclass
class _GestureState:
    origin_x: int
    origin_y: int
    last_x: int
    base_plan_identity_digest: str | None
    render_revision: int
    dragging: bool = False


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
        palette = ThemeManager.get_palette()
        # 背景
        brush = wx.Brush(palette.preview_lane_bg)
        gc.SetBrush(brush)
        gc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

        if not self.model.is_valid or self.model.duration_sec <= 0.0:
            return

        self._draw_grid_and_labels(gc, rect, font)
        self._draw_lanes(gc, rect)
        self._draw_cursor(gc, rect)

    def _draw_grid_and_labels(self, gc: wx.GraphicsContext, rect: wx.Rect, font: wx.Font):
        palette = ThemeManager.get_palette()
        # 5段レーンの枠線と母音ラベル
        lane_height = rect.height / 5.0
        
        pen = wx.Pen(palette.waveform_grid, 1, wx.PENSTYLE_SOLID)
        gc.SetPen(pen)
        
        gc.SetFont(font, palette.text_fg)
        
        for i, vowel in enumerate(PREVIEW_ROW_VOWELS):
            row_data = next(
                (row for row in self.model.data.rows if row.vowel == vowel),
                None,
            )
            y = int(i * lane_height)
            # 水平線
            if i > 0:
                path = gc.CreatePath()
                path.MoveToPoint(0, y)
                path.AddLineToPoint(rect.width, y)
                gc.StrokePath(path)
            
            # 母音ラベル
            gc.DrawText(
                (row_data.display_name if row_data and row_data.display_name else vowel),
                5,
                y + 2,
            )

    def _time_to_x(self, time_sec: float, rect_width: float) -> float:
        span = self.model.viewport_end_sec - self.model.viewport_start_sec
        if span <= 0.0:
            return 0.0
        return ((time_sec - self.model.viewport_start_sec) / span) * rect_width

    def _draw_lanes(self, gc: wx.GraphicsContext, rect: wx.Rect):
        palette = ThemeManager.get_palette()
        lane_height = rect.height / 5.0

        for i, vowel in enumerate(PREVIEW_ROW_VOWELS):
            row_data = next((r for r in self.model.data.rows if r.vowel == vowel), None)
            if not row_data:
                continue
            
            y_base = i * lane_height
            color = self.vowel_colors.get(vowel, wx.Colour(200, 200, 200, 180))
            
            for segment in row_data.segments:
                # duration_secの範囲外なら描画しない（clampの結果、可視幅が0になるものを省く）
                if segment.end_sec < self.model.viewport_start_sec or segment.start_sec > self.model.viewport_end_sec:
                    continue
                    
                x_start = self._time_to_x(segment.start_sec, rect.width)
                x_end = self._time_to_x(segment.end_sec, rect.width)
                w = x_end - x_start
                if w <= 0:
                    continue
                
                selected_index = self.model.selected_source_event_index
                is_selected = selected_index is not None and (
                    segment.source_event_index == selected_index
                    or selected_index in segment.source_event_indices
                )
                
                if is_selected:
                    brush = wx.Brush(wx.Colour(color.Red(), color.Green(), color.Blue(), 255))
                    # Highlight border with slightly thicker / distinct color
                    pen = wx.Pen(palette.text_fg, 2, wx.PENSTYLE_SOLID)
                else:
                    brush = wx.Brush(color)
                    pen = wx.Pen(wx.Colour(color.Red(), color.Green(), color.Blue(), 255), 1, wx.PENSTYLE_SOLID)
                
                gc.SetBrush(brush)
                gc.SetPen(pen)
                
                if not segment.control_points:
                    # Fallback to rectangle
                    h = max(2.0, (lane_height - 4) * segment.intensity)
                    y = y_base + lane_height - 2 - h
                    gc.DrawRoundedRectangle(x_start, y, w, h, 2.0)
                else:
                    max_h_lane = lane_height - 4
                    base_y = y_base + lane_height - 2
                    path = gc.CreatePath()
                    
                    first = True
                    for cp in segment.control_points:
                        cp_x = self._time_to_x(cp.time_sec, rect.width)
                        cp_h = max_h_lane * cp.value
                        cp_y_top = base_y - cp_h
                        if first:
                            path.MoveToPoint(cp_x, cp_y_top)
                            first = False
                        else:
                            path.AddLineToPoint(cp_x, cp_y_top)
                            
                    for cp in reversed(segment.control_points):
                        cp_x = self._time_to_x(cp.time_sec, rect.width)
                        path.AddLineToPoint(cp_x, base_y)
                        
                    path.CloseSubpath()
                    gc.FillPath(path, wx.WINDING_RULE)
                    gc.StrokePath(path)

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
            
            palette = ThemeManager.get_palette()
            pen = wx.Pen(palette.playback_cursor, 2, wx.PENSTYLE_SOLID)
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
        self.SetDoubleBuffered(True)
        
        self.model = PreviewModel()
        self.renderer = PreviewRenderer(self.model)
        self.placeholder_msg: str = "[Placeholder] Preview エリア"
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        
        self.on_pan_callback = None
        self.on_selection_request_callback = None
        self._gesture: _GestureState | None = None
        self.Bind(wx.EVT_LEFT_DOWN, self._on_mouse_down)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        self.Bind(wx.EVT_LEFT_UP, self._on_mouse_up)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_leave)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self._on_mouse_capture_lost)

    def set_preview_data(self, data: PreviewData, duration_sec: float):
        """[MS15-B2] 解析成功時にプレビューデータをセットする"""
        self._cancel_gesture()
        self.model.set_data(data, duration_sec)
        self.Refresh()

    def set_identity_aware_preview_data(
        self,
        data: PreviewData,
        duration_sec: float,
        base_plan_identity_digest: str,
    ):
        """Set canonical Preview data while retaining same-base selection."""
        changed = self.model.set_identity_aware_data(
            data,
            duration_sec,
            base_plan_identity_digest,
        )
        if changed:
            self._cancel_gesture()
        self.Refresh()

    def set_placeholder(
        self,
        msg: str,
        *,
        output_morph_names: Sequence[str] = PREVIEW_ROW_VOWELS,
    ):
        """[MS15-B2] 解析失敗時などにプレースホルダへ戻す"""
        self._cancel_gesture()
        self.model.clear(output_morph_names=output_morph_names)
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

    def set_selected_source_event_index(self, index: int | None):
        """[MS16-B6] 選択されたイベントインデックスをセットする"""
        self.model.selected_source_event_index = index
        self.Refresh()

    def clear_selection(self):
        """[MS16-B6] 選択状態をクリアする"""
        self.model.selected_source_event_index = None
        self.Refresh()

    def get_selected_shape_summary(self) -> str | None:
        """[MS16-B6] 選択中のshape情報からsummary文字列を生成する"""
        if self.model.selected_source_event_index is None:
            return None
        segment = self.model.find_shape_by_source_event_index(self.model.selected_source_event_index)
        if not segment:
            return None
            
        lines = []
        lines.append(f"Morph: {segment.display_name or segment.vowel}")
        selected_index = self.model.selected_source_event_index
        lines.append(f"Event Index: {selected_index}")
        lines.append(f"Shape: {segment.shape_kind}")
        region = self.model.find_event_hit_region(selected_index)
        if region is not None:
            lines.append(
                f"Time: {region.start_frame / 30.0:.2f}s - {region.end_frame / 30.0:.2f}s"
            )
            lines.append(f"Peak: {region.peak_value:.2f}")
            lines.append(f"Peak Frame: {region.base_peak_frame}")
            lines.append(f"Frame: {region.start_frame} - {region.end_frame}")
        else:
            lines.append(f"Time: {segment.start_sec:.2f}s - {segment.end_sec:.2f}s")
            lines.append(f"Peak: {segment.intensity:.2f}")
        if region is None and segment.frame_range:
            lines.append(f"Frame: {segment.frame_range[0]} - {segment.frame_range[1]}")
            
        return "\n".join(lines)

    def _on_size(self, event):
        self.Refresh()
        event.Skip()

    def _on_mouse_down(self, event):
        if not self.model.is_valid:
            event.Skip()
            return
        position = event.GetPosition()
        self._gesture = _GestureState(
            origin_x=position.x,
            origin_y=position.y,
            last_x=position.x,
            base_plan_identity_digest=self.model.base_plan_identity_digest,
            render_revision=self.model.render_revision,
        )
        if not self.HasCapture():
            self.CaptureMouse()
        event.Skip()
        
    def _on_mouse_motion(self, event):
        gesture = self._gesture
        if event.Dragging() and event.LeftIsDown() and gesture is not None:
            position = event.GetPosition()
            threshold = max(float(self.FromDIP(4)), 1.0)
            if not gesture.dragging and math.hypot(
                position.x - gesture.origin_x,
                position.y - gesture.origin_y,
            ) >= threshold:
                gesture.dragging = True
            dx = gesture.last_x - position.x
            if gesture.dragging:
                gesture.last_x = position.x
            if gesture.dragging and dx != 0 and self.on_pan_callback:
                span = self.model.viewport_end_sec - self.model.viewport_start_sec
                rect_width = self.GetClientRect().width
                if rect_width > 0:
                    delta_sec = (dx / rect_width) * span
                    self.on_pan_callback(delta_sec)
        event.Skip()

    def _on_mouse_up(self, event):
        gesture = self._gesture
        if gesture is not None and not gesture.dragging:
            self._commit_click(event.GetPosition(), gesture)
        self._cancel_gesture()
        event.Skip()

    def _commit_click(self, position: wx.Point, gesture: _GestureState):
        if (
            gesture.base_plan_identity_digest is None
            or gesture.base_plan_identity_digest != self.model.base_plan_identity_digest
            or gesture.render_revision != self.model.render_revision
        ):
            return
        rect = self.GetClientRect()
        selected_index = hit_test_preview_event(
            PreviewHitTestInput(
                x=position.x,
                y=position.y,
                width=rect.width,
                height=rect.height,
                viewport_start_sec=self.model.viewport_start_sec,
                viewport_end_sec=self.model.viewport_end_sec,
                event_hit_regions=self.model.get_event_hit_regions(),
            )
        )
        if selected_index is None or self.on_selection_request_callback is None:
            return
        self.on_selection_request_callback(
            PreviewSelectionRequest(
                base_event_index=selected_index,
                base_plan_identity_digest=gesture.base_plan_identity_digest,
                render_revision=gesture.render_revision,
            )
        )

    def _cancel_gesture(self):
        self._gesture = None
        if self.HasCapture():
            self.ReleaseMouse()

    def _on_mouse_leave(self, event):
        self._cancel_gesture()
        event.Skip()

    def _on_mouse_capture_lost(self, event):
        self._gesture = None
        event.Skip()

    def _on_paint(self, event):
        rect = self.GetClientRect()
        if rect.width <= 0 or rect.height <= 0:
            wx.PaintDC(self)  # Consume the paint event
            return
            
        dc = wx.PaintDC(self)
        
        if not self.model.is_valid:
            palette = ThemeManager.get_palette()
            # Placeholder描画
            dc.SetBrush(wx.Brush(palette.preview_lane_bg))
            dc.SetPen(wx.Pen(palette.preview_lane_bg, 1, wx.PENSTYLE_TRANSPARENT))
            dc.DrawRectangle(rect)
            dc.SetTextForeground(palette.muted_text)
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
            
        gc = wx.GraphicsContext.Create(dc)
        if gc is None:
            return

        self.renderer.render(gc, rect, self.GetFont())
