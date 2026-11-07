import wx
from dataclasses import dataclass, field
import math
from typing import Sequence

from src.core.preview_hit_test import (
    PreviewCurveHitRegion,
    PreviewEventHitRegion,
    PreviewHitTestInput,
    PreviewSelectionRequest,
    collect_preview_curve_hit_regions,
    collect_preview_hit_regions,
    hit_test_preview_event,
)
from src.core.preview_transform import PreviewData, PREVIEW_ROW_VOWELS, empty_preview_data, PreviewSegment
from gui_wx.theme import ThemeManager
from gui_wx.frame_grid import FrameGridTick, calculate_frame_grid_ticks


_PAN_DRAG_SCALE = 0.5


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
    final_output_binding: str | None = None
    render_revision: int = 0

    def set_data(self, data: PreviewData, duration_sec: float):
        self.data = data
        self.duration_sec = duration_sec
        self.is_valid = True
        self.selected_source_event_index = None
        self.base_plan_identity_digest = None
        self.final_output_binding = None
        self.render_revision += 1
        if self.viewport_start_sec == 0.0 and self.viewport_end_sec == 0.0:
            self.viewport_end_sec = duration_sec

    def set_identity_aware_data(
        self,
        data: PreviewData,
        duration_sec: float,
        base_plan_identity_digest: str,
        final_output_binding: str | None = None,
    ) -> bool:
        """Replace canonical Preview data and preserve selection only for the same base."""
        if not isinstance(base_plan_identity_digest, str) or not base_plan_identity_digest:
            raise ValueError("base_plan_identity_digest must be a non-empty string")
        if final_output_binding is not None and (
            not isinstance(final_output_binding, str)
            or not final_output_binding
        ):
            raise ValueError("final_output_binding must be non-empty text or None")
        if (
            data.final_output_binding is not None
            and data.final_output_binding != final_output_binding
        ):
            raise ValueError("Preview data binding differs from the requested identity")
        data_changed = (
            not self.is_valid
            or self.data != data
            or self.duration_sec != duration_sec
            or self.base_plan_identity_digest != base_plan_identity_digest
            or self.final_output_binding != final_output_binding
        )
        if not data_changed:
            return False
        same_identity = self.base_plan_identity_digest == base_plan_identity_digest
        self.data = data
        self.duration_sec = duration_sec
        self.is_valid = True
        self.base_plan_identity_digest = base_plan_identity_digest
        self.final_output_binding = final_output_binding
        self.render_revision += 1
        if not same_identity:
            self.selected_source_event_index = None
        elif (
            self.selected_source_event_index is not None
            and (
                self.find_event_hit_region(self.selected_source_event_index) is None
                if final_output_binding is not None
                else self.find_shape_by_source_event_index(self.selected_source_event_index)
                is None
            )
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
        self.final_output_binding = None
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
        region = next(
            (
                item
                for item in self.get_event_hit_regions()
                if item.base_event_index == index
            ),
            None,
        )
        if region is not None:
            row = next((item for item in self.data.rows if item.vowel == region.vowel), None)
            if row is not None:
                for segment in row.segments:
                    if (
                        segment.frame_range is None
                        or segment.frame_range[0] <= region.end_frame
                        and region.start_frame <= segment.frame_range[1]
                    ):
                        return segment
        return None

    def find_event_hit_region(self, index: int) -> PreviewEventHitRegion | None:
        for region in self.get_event_hit_regions():
            if region.base_event_index == index:
                return region
        return None

    def get_event_hit_regions(self) -> tuple[PreviewEventHitRegion, ...]:
        if not self.is_valid:
            return ()
        if self.data.selection_regions:
            return tuple(self.data.selection_regions)
        return collect_preview_hit_regions(self.data.rows)

    def get_curve_hit_regions(self):
        if not self.is_valid:
            return ()
        return collect_preview_curve_hit_regions(self.data.rows)


@dataclass
class _GestureState:
    origin_x: int
    origin_y: int
    last_x: int
    base_plan_identity_digest: str | None
    render_revision: int
    final_output_binding: str | None = None
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

    def render(
        self,
        gc: wx.GraphicsContext,
        rect: wx.Rect,
        font: wx.Font,
        *,
        frame_grid_enabled: bool = True,
    ):
        palette = ThemeManager.get_palette()
        # 背景
        brush = wx.Brush(palette.preview_lane_bg)
        gc.SetBrush(brush)
        gc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

        if not self.model.is_valid or self.model.duration_sec <= 0.0:
            return

        self._draw_frame_grid(gc, rect, frame_grid_enabled)
        self._draw_grid_and_labels(gc, rect, font)
        self._draw_lanes(gc, rect)
        self._draw_cursor(gc, rect)

    def _draw_frame_grid(
        self,
        gc: wx.GraphicsContext,
        rect: wx.Rect,
        enabled: bool,
    ) -> None:
        frame_ticks: tuple[FrameGridTick, ...] = calculate_frame_grid_ticks(
            self.model.viewport_start_sec,
            self.model.viewport_end_sec,
            self.model.duration_sec,
            rect.width,
            enabled=enabled,
        )
        if not frame_ticks:
            return

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
        selected_index = self.model.selected_source_event_index
        selected_region = (
            None
            if selected_index is None
            else self.model.find_event_hit_region(selected_index)
        )

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
                    if selected_index is not None and segment.shape_kind == "shared_final_output":
                        curve = PreviewCurveHitRegion(
                            vowel,
                            tuple((point.frame_no, point.value) for point in segment.control_points),
                            tuple(point.source_event_indices for point in segment.control_points),
                            requires_source_ownership=True,
                        )
                        gc.SetPen(wx.Pen(palette.text_fg, 2, wx.PENSTYLE_SOLID))
                        for left, right in zip(segment.control_points, segment.control_points[1:]):
                            if left.frame_no == right.frame_no or max(left.value, right.value) <= 0.0:
                                continue
                            midpoint = (left.frame_no + right.frame_no) / 2
                            if curve.source_event_indices_at(midpoint) != (selected_index,):
                                continue
                            outline = gc.CreatePath()
                            outline.MoveToPoint(
                                self._time_to_x(left.time_sec, rect.width),
                                base_y - max_h_lane * left.value,
                            )
                            outline.AddLineToPoint(
                                self._time_to_x(right.time_sec, rect.width),
                                base_y - max_h_lane * right.value,
                            )
                            gc.StrokePath(outline)

            if selected_region is not None and selected_region.vowel == vowel:
                selected_points = (
                    point
                    for segment in row_data.segments
                    if segment.shape_kind == "shared_final_output"
                    for point in segment.control_points
                    if selected_index in point.source_event_indices
                    and point.value > 0.0
                    and self.model.viewport_start_sec <= point.time_sec <= self.model.viewport_end_sec
                )
                anchor = min(
                    selected_points,
                    key=lambda point: (
                        -point.value,
                        abs((point.frame_no or 0) - selected_region.base_peak_frame),
                    ),
                    default=None,
                )
                if anchor is not None:
                    anchor_x = self._time_to_x(anchor.time_sec, rect.width)
                    anchor_y = y_base + lane_height - 2 - (lane_height - 4) * anchor.value
                    gc.SetBrush(wx.Brush(wx.Colour(color.Red(), color.Green(), color.Blue(), 255)))
                    gc.SetPen(wx.Pen(palette.text_fg, 2, wx.PENSTYLE_SOLID))
                    gc.DrawEllipse(anchor_x - 4, anchor_y - 4, 8, 8)

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
        super().__init__(parent, style=wx.BORDER_NONE | wx.CLIP_CHILDREN)
        self._ms33c_theme_border = True
        self.SetMinSize((-1, 150))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)
        
        self.model = PreviewModel()
        self.renderer = PreviewRenderer(self.model)
        self._frame_grid_enabled = True
        self.placeholder_msg: str = "[Placeholder] Preview エリア"
        self._loading_label = wx.StaticText(self, label="")
        self._loading_label.Hide()
        self._loading_step = 0
        self._loading_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_loading_timer, self._loading_timer)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)
        
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
        self._set_loading(False)
        self.Refresh()

    def set_identity_aware_preview_data(
        self,
        data: PreviewData,
        duration_sec: float,
        base_plan_identity_digest: str,
        final_output_binding: str | None = None,
    ):
        """Set canonical Preview data while retaining same-base selection."""
        changed = self.model.set_identity_aware_data(
            data,
            duration_sec,
            base_plan_identity_digest,
            final_output_binding,
        )
        if changed:
            self._cancel_gesture()
        was_loading = self._loading_label.IsShown()
        self._set_loading(False)
        if changed or was_loading:
            self.Refresh()

    def set_placeholder(
        self,
        msg: str,
        *,
        output_morph_names: Sequence[str] = PREVIEW_ROW_VOWELS,
        loading: bool = False,
    ):
        """[MS15-B2] 解析失敗時などにプレースホルダへ戻す"""
        self._cancel_gesture()
        self.model.clear(output_morph_names=output_morph_names)
        self.placeholder_msg = msg
        self._set_loading(loading)
        self.Refresh()

    def _set_loading(self, loading: bool):
        self._loading_timer.Stop()
        self._loading_step = 0
        self._loading_label.Hide()
        if loading:
            self._loading_label.SetLabel(self.placeholder_msg)
            self._loading_label.SetFont(self.GetFont())
            self._layout_loading_label()
            self._loading_label.Show()
            self._loading_timer.Start(100)

    def _layout_loading_label(self):
        palette = ThemeManager.get_palette()
        if self._loading_label.GetForegroundColour() != palette.muted_text:
            self._loading_label.SetForegroundColour(palette.muted_text)
        if self._loading_label.GetBackgroundColour() != palette.preview_lane_bg:
            self._loading_label.SetBackgroundColour(palette.preview_lane_bg)
        size = self._loading_label.GetBestSize()
        rect = self.GetClientRect()
        if self._loading_label.GetSize() != size:
            self._loading_label.SetSize(size)
        position = wx.Point(
            max(0, (rect.width - size.width) // 2),
            max(0, (rect.height - size.height) // 2),
        )
        if self._loading_label.GetPosition() != position:
            self._loading_label.SetPosition(position)

    def _on_loading_timer(self, event):
        if self._loading_timer.IsRunning():
            self._loading_step = (self._loading_step + 1) % 8
            self.Refresh(False)

    def _on_destroy(self, event):
        if event.GetEventObject() is self:
            self._loading_timer.Stop()
        event.Skip()

    def set_playback_position_sec(self, position_sec: float | None):
        """[MS15-B2] 再生位置カーソルの受け口 API"""
        self.model.set_playback_position(position_sec)
        self.Refresh()

    def set_viewport_sec(self, start_sec: float, end_sec: float):
        """[MS15-B4] 表示範囲の更新"""
        self.model.set_viewport_sec(start_sec, end_sec)
        self.Refresh()

    def set_frame_grid_enabled(self, enabled: bool) -> None:
        value = bool(enabled)
        if self._frame_grid_enabled == value:
            return
        self._frame_grid_enabled = value
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
        if self.model.selected_source_event_index == index:
            return
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
        if self._loading_timer.IsRunning():
            self._layout_loading_label()
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
            final_output_binding=self.model.final_output_binding,
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
                    delta_sec = (dx / rect_width) * span * _PAN_DRAG_SCALE
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
            or gesture.final_output_binding != self.model.final_output_binding
            or gesture.render_revision != self.model.render_revision
        ):
            return
        rect = self.GetClientRect()
        try:
            curve_regions = self.model.get_curve_hit_regions()
        except ValueError:
            return
        selected_index = hit_test_preview_event(
            PreviewHitTestInput(
                x=position.x,
                y=position.y,
                width=rect.width,
                height=rect.height,
                viewport_start_sec=self.model.viewport_start_sec,
                viewport_end_sec=self.model.viewport_end_sec,
                event_hit_regions=self.model.get_event_hit_regions(),
                curve_hit_regions=curve_regions,
            )
        )
        if selected_index is None or self.on_selection_request_callback is None:
            return
        self.on_selection_request_callback(
            PreviewSelectionRequest(
                base_event_index=selected_index,
                base_plan_identity_digest=gesture.base_plan_identity_digest,
                render_revision=gesture.render_revision,
                final_output_binding=gesture.final_output_binding,
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
            if self._loading_timer.IsRunning():
                # Use the same native text control as the rest of the GUI.
                self._layout_loading_label()
                y = self._loading_label.GetRect().GetBottom()
                # Draw beneath the message using the current theme and DPI.
                radius = self.FromDIP(8)
                center_x = rect.width // 2
                center_y = y + self.FromDIP(8) + radius
                background = palette.preview_lane_bg
                foreground = palette.muted_text
                dc.SetPen(wx.TRANSPARENT_PEN)
                for index in range(8):
                    strength = 0.25 + 0.75 * ((index - self._loading_step) % 8) / 7
                    colour = wx.Colour(*(
                        round(bg + (fg - bg) * strength)
                        for bg, fg in zip(background.Get(), foreground.Get())
                    ))
                    dc.SetBrush(wx.Brush(colour))
                    angle = index * math.tau / 8
                    dc.DrawCircle(
                        round(center_x + radius * math.cos(angle)),
                        round(center_y + radius * math.sin(angle)),
                        max(1, self.FromDIP(2)),
                    )
            else:
                # Center non-loading placeholder text.
                text_lines = self.placeholder_msg.split('\n')
                total_h = sum(dc.GetTextExtent(line)[1] for line in text_lines)
                y = max(0, (rect.height - total_h) // 2)
                for line in text_lines:
                    tw, th = dc.GetTextExtent(line)
                    x = max(0, (rect.width - tw) // 2)
                    dc.DrawText(line, x, y)
                    y += th
            ThemeManager.draw_border(dc, rect, self)
            return
            
        gc = wx.GraphicsContext.Create(dc)
        if gc is None:
            ThemeManager.draw_border(dc, rect, self)
            return

        self.renderer.render(
            gc,
            rect,
            self.GetFont(),
            frame_grid_enabled=self._frame_grid_enabled,
        )
        ThemeManager.draw_border(gc, rect, self)
