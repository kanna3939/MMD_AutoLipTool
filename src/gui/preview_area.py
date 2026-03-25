from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from gui.i18n_strings import ThemeStrings, localized_vowel_label, normalize_language
from gui.preview_transform import PREVIEW_ROW_VOWELS, PreviewData, PreviewRow, empty_preview_data

_FRAME_RATE = 30.0
_OUTER_MARGIN = 8
_LABEL_WIDTH = 18
_LABEL_TIMELINE_GAP = 6
_ROW_COLORS: dict[str, QColor] = {
    vowel: QColor(color)
    for vowel, color in zip(
        PREVIEW_ROW_VOWELS,
        ("#d1495b", "#edae49", "#66a182", "#2e86ab", "#5a4e7c"),
    )
}
_THEME_COLORS = {
    ThemeStrings.DARK: {
        "background": "#20262f",
        "timeline_border": "#556072",
        "axis_separator": "#4b5563",
        "row_grid": "#3b4552",
        "major_grid": "#556072",
        "minor_grid": "#394150",
        "axis_text": "#aeb6c2",
        "row_label": "#e5e7eb",
        "cursor": "#f87171",
    },
    ThemeStrings.LIGHT: {
        "background": "#ffffff",
        "timeline_border": "#cbd5e1",
        "axis_separator": "#d9d9d9",
        "row_grid": "#e6e6e6",
        "major_grid": "#d5d5d5",
        "minor_grid": "#ececec",
        "axis_text": "#667085",
        "row_label": "#333333",
        "cursor": "#d62728",
    },
}


class PreviewArea(QWidget):
    pan_requested = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self._preview_data: PreviewData = empty_preview_data()
        self._timeline_duration_sec: float = 0.0
        self._viewport_start_sec: float | None = None
        self._viewport_end_sec: float | None = None
        self._playback_position_sec: float | None = None
        self._pan_drag_active = False
        self._pan_drag_last_x: float | None = None
        self._waveform_plot_area_rect: tuple[float, float, float, float] | None = None
        self._theme_name = ThemeStrings.DARK
        self._language = "ja"
        self.setMinimumHeight(140)

    def set_theme(self, theme_name: str) -> None:
        resolved_theme = self._normalize_theme_name(theme_name)
        if self._theme_name == resolved_theme:
            return
        self._theme_name = resolved_theme
        self.update()

    def set_language(self, language: str) -> None:
        resolved_language = normalize_language(language)
        if self._language == resolved_language:
            return
        self._language = resolved_language
        self.update()

    def retranslate_ui(self, language: str) -> None:
        self.set_language(language)

    def set_preview_data(self, preview_data: PreviewData) -> None:
        self._preview_data = preview_data
        self.update()

    def set_timeline_duration_sec(self, duration_sec: float) -> None:
        normalized_duration_sec = self._normalize_non_negative_sec(duration_sec)
        if abs(self._timeline_duration_sec - normalized_duration_sec) <= 1e-6:
            return
        self._timeline_duration_sec = normalized_duration_sec
        self.update()

    def set_waveform_plot_area_rect(self, rect: tuple[float, float, float, float] | None) -> None:
        if self._waveform_plot_area_rect == rect:
            return
        self._waveform_plot_area_rect = rect
        self.update()

    @property
    def waveform_plot_area_rect(self) -> tuple[float, float, float, float] | None:
        return self._waveform_plot_area_rect

    def clear_preview(self) -> None:
        self._preview_data = empty_preview_data()
        self.update()

    def set_viewport_sec(self, start_sec: float, end_sec: float) -> None:
        normalized_start, normalized_end = self._normalize_viewport_sec(start_sec, end_sec)
        if self._is_same_viewport(normalized_start, normalized_end):
            return
        self._viewport_start_sec = normalized_start
        self._viewport_end_sec = normalized_end
        self.update()

    def clear_viewport_sec(self) -> None:
        if self._viewport_start_sec is None and self._viewport_end_sec is None:
            return
        self._viewport_start_sec = None
        self._viewport_end_sec = None
        self.update()

    def viewport_sec(self) -> tuple[float | None, float | None]:
        return (self._viewport_start_sec, self._viewport_end_sec)

    def set_playback_position_sec(self, position_sec: float) -> None:
        resolved = max(float(position_sec), 0.0)
        if self._playback_position_sec is not None and abs(self._playback_position_sec - resolved) <= 1e-6:
            return
        self._playback_position_sec = resolved
        self.update()

    def clear_playback_cursor(self) -> None:
        if self._playback_position_sec is None:
            return
        self._playback_position_sec = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self._pan_interaction_rect().contains(self._event_position(event)):
            self._pan_drag_active = True
            self._pan_drag_last_x = float(event.position().x())
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self._pan_drag_active or self._pan_drag_last_x is None:
            super().mouseMoveEvent(event)
            return

        current_x = float(event.position().x())
        delta_x = current_x - self._pan_drag_last_x
        self._pan_drag_last_x = current_x

        timeline_rect = self._pan_interaction_rect()
        if timeline_rect.width() <= 0.0:
            event.accept()
            return

        rows = self._rows_with_fallback()
        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec(rows)
        visible_span_sec = visible_end_sec - visible_start_sec
        if visible_span_sec <= 0.0:
            event.accept()
            return

        pan_delta_sec = -(delta_x / timeline_rect.width()) * visible_span_sec
        if abs(pan_delta_sec) > 1e-9:
            self.pan_requested.emit(pan_delta_sec)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton or not self._pan_drag_active:
            super().mouseReleaseEvent(event)
            return
        self._pan_drag_active = False
        self._pan_drag_last_x = None
        self.unsetCursor()
        event.accept()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        colors = self._theme_colors()

        canvas = self.rect()
        painter.fillRect(canvas, QColor(colors["background"]))

        if canvas.width() <= 4 or canvas.height() <= 4:
            return

        margin = _OUTER_MARGIN
        inner = canvas.adjusted(margin, margin, -margin, -margin)
        timeline_rect = self._resolve_timeline_rect(inner)
        if timeline_rect.width() <= 2.0 or timeline_rect.height() <= 2.0:
            return

        rows = self._rows_with_fallback()
        visible_start_sec, visible_end_sec = self._resolved_visible_range_sec(rows)
        frame_axis_height = self._resolve_frame_axis_height(timeline_rect.height())
        if frame_axis_height >= timeline_rect.height() - 4.0:
            frame_axis_height = 0.0
        frame_axis_rect = QRectF(
            timeline_rect.left(),
            timeline_rect.top(),
            timeline_rect.width(),
            frame_axis_height,
        )
        row_timeline_rect = QRectF(
            timeline_rect.left(),
            timeline_rect.top() + frame_axis_height,
            timeline_rect.width(),
            max(0.0, timeline_rect.height() - frame_axis_height),
        )
        row_count = len(rows)
        row_height = row_timeline_rect.height() / max(row_count, 1)

        painter.setPen(QPen(QColor(colors["timeline_border"]), 1))
        painter.drawRect(timeline_rect)
        if frame_axis_rect.height() > 0.0:
            painter.setPen(QPen(QColor(colors["axis_separator"]), 1))
            painter.drawLine(
                int(timeline_rect.left()),
                int(frame_axis_rect.bottom()),
                int(timeline_rect.right()),
                int(frame_axis_rect.bottom()),
            )
        self._draw_frame_axis_ticks(
            painter,
            frame_axis_rect,
            row_timeline_rect,
            visible_start_sec,
            visible_end_sec,
        )

        for row_index, row in enumerate(rows):
            top = row_timeline_rect.top() + (row_height * row_index)
            row_rect = QRectF(row_timeline_rect.left(), top, row_timeline_rect.width(), row_height)
            self._draw_row_label(painter, inner, timeline_rect, top, row_height, row.vowel)
            self._draw_row_grid(painter, row_rect, row_index, row_count)
            self._draw_row_segments(
                painter,
                row_rect,
                row,
                visible_start_sec,
                visible_end_sec,
            )
        self._draw_playback_cursor(
            painter,
            row_timeline_rect,
            visible_start_sec,
            visible_end_sec,
        )

    def _rows_with_fallback(self) -> list[PreviewRow]:
        if self._preview_data.rows:
            return self._preview_data.rows
        return empty_preview_data().rows

    def _pan_interaction_rect(self) -> QRectF:
        canvas = QRectF(self.rect())
        inner = canvas.adjusted(_OUTER_MARGIN, _OUTER_MARGIN, -_OUTER_MARGIN, -_OUTER_MARGIN)
        return self._resolve_timeline_rect(inner)

    def _resolve_timeline_rect(self, inner: QRectF) -> QRectF:
        if self._waveform_plot_area_rect is not None:
            plot_x, _, plot_width, _ = self._waveform_plot_area_rect
            return QRectF(plot_x, inner.top(), plot_width, inner.height())
        return inner.adjusted(_LABEL_WIDTH + _LABEL_TIMELINE_GAP, 0, 0, 0)

    def _event_position(self, event: QMouseEvent) -> QPointF:
        return QPointF(event.position())

    def _draw_row_label(
        self,
        painter: QPainter,
        inner: QRectF,
        timeline_rect: QRectF,
        top: float,
        row_height: float,
        vowel: str,
    ) -> None:
        label_right = timeline_rect.left() - _LABEL_TIMELINE_GAP
        label_width = label_right - inner.left()
        label_rect = QRectF(inner.left(), top, label_width, row_height)
        painter.setPen(QColor(self._theme_colors()["row_label"]))
        painter.drawText(
            label_rect,
            int(Qt.AlignVCenter | Qt.AlignRight),
            localized_vowel_label(vowel, self._language),
        )

    def _draw_row_grid(self, painter: QPainter, row_rect: QRectF, row_index: int, row_count: int) -> None:
        if row_index + 1 >= row_count:
            return
        painter.setPen(QPen(QColor(self._theme_colors()["row_grid"]), 1))
        painter.drawLine(
            int(row_rect.left()),
            int(row_rect.bottom()),
            int(row_rect.right()),
            int(row_rect.bottom()),
        )

    def _draw_frame_axis_ticks(
        self,
        painter: QPainter,
        frame_axis_rect: QRectF,
        timeline_rect: QRectF,
        visible_start_sec: float,
        visible_end_sec: float,
    ) -> None:
        if frame_axis_rect.height() <= 0.0 or timeline_rect.width() <= 0.0:
            return

        visible_span_sec = visible_end_sec - visible_start_sec
        if visible_span_sec <= 0.0:
            painter.setPen(QPen(QColor(self._theme_colors()["axis_text"]), 1))
            painter.drawText(
                QRectF(frame_axis_rect.left() + 2.0, frame_axis_rect.top(), 32.0, frame_axis_rect.height()),
                int(Qt.AlignLeft | Qt.AlignVCenter),
                "0",
            )
            return

        major_frames = self._build_major_frame_ticks(visible_start_sec, visible_end_sec)
        if not major_frames:
            major_frames = [self._seconds_to_frame_floor(visible_start_sec)]
        major_step = self._major_step_from_ticks(major_frames)
        minor_frames = self._build_minor_frame_ticks(
            visible_start_sec,
            visible_end_sec,
            major_step,
            major_frames,
        )

        painter.setPen(QPen(QColor(self._theme_colors()["minor_grid"]), 1))
        for frame_no in minor_frames:
            sec = self._frame_to_seconds(frame_no)
            x = self._seconds_to_x(sec, timeline_rect, visible_start_sec, visible_end_sec)
            painter.drawLine(
                int(x),
                int(timeline_rect.top()),
                int(x),
                int(timeline_rect.bottom()),
            )
            painter.drawLine(
                int(x),
                int(frame_axis_rect.bottom() - 4.0),
                int(x),
                int(frame_axis_rect.bottom()),
            )

        painter.setPen(QPen(QColor(self._theme_colors()["major_grid"]), 1))
        for frame_no in major_frames:
            sec = self._frame_to_seconds(frame_no)
            x = self._seconds_to_x(sec, timeline_rect, visible_start_sec, visible_end_sec)
            painter.drawLine(
                int(x),
                int(timeline_rect.top()),
                int(x),
                int(timeline_rect.bottom()),
            )

        painter.setPen(QPen(QColor(self._theme_colors()["axis_text"]), 1))
        metrics = painter.fontMetrics()
        min_spacing = 4.0
        last_label_right = -1e9
        for frame_no in major_frames:
            sec = self._frame_to_seconds(frame_no)
            x = self._seconds_to_x(sec, timeline_rect, visible_start_sec, visible_end_sec)
            text = str(frame_no)
            text_width = float(metrics.horizontalAdvance(text))
            left = x - (text_width * 0.5)
            right = left + text_width
            if left <= last_label_right + min_spacing:
                continue
            painter.drawText(
                QRectF(left - 1.0, frame_axis_rect.top(), text_width + 2.0, frame_axis_rect.height() - 5.0),
                int(Qt.AlignHCenter | Qt.AlignTop),
                text,
            )
            painter.drawLine(
                int(x),
                int(frame_axis_rect.bottom() - 6.0),
                int(x),
                int(frame_axis_rect.bottom()),
            )
            last_label_right = right

    def _draw_row_segments(
        self,
        painter: QPainter,
        row_rect: QRectF,
        row: PreviewRow,
        visible_start_sec: float,
        visible_end_sec: float,
    ) -> None:
        visible_span_sec = visible_end_sec - visible_start_sec
        if visible_span_sec <= 0.0:
            return

        base_color = _ROW_COLORS.get(row.vowel, QColor("#2e86ab"))
        for segment in row.segments:
            clipped_start = min(max(segment.start_sec, visible_start_sec), visible_end_sec)
            clipped_end = min(max(segment.end_sec, visible_start_sec), visible_end_sec)
            if clipped_end <= clipped_start:
                continue

            start_ratio = (clipped_start - visible_start_sec) / visible_span_sec
            end_ratio = (clipped_end - visible_start_sec) / visible_span_sec

            left = row_rect.left() + (row_rect.width() * start_ratio)
            right = row_rect.left() + (row_rect.width() * end_ratio)
            width = max(1.0, right - left)
            height = max(2.0, row_rect.height() - 6.0)
            top = row_rect.top() + 3.0

            fill = QColor(base_color)
            alpha = 60 + int(max(0.0, min(segment.intensity, 1.0)) * 160)
            fill.setAlpha(alpha)
            painter.fillRect(QRectF(left, top, width, height), fill)

    def _max_end_sec(self, rows: list[PreviewRow]) -> float:
        max_end_sec = 0.0
        for row in rows:
            for segment in row.segments:
                if segment.end_sec > max_end_sec:
                    max_end_sec = segment.end_sec
        return max_end_sec

    def _resolved_visible_range_sec(self, rows: list[PreviewRow]) -> tuple[float, float]:
        full_start_sec = 0.0
        full_end_sec = max(self._timeline_duration_sec, self._max_end_sec(rows), 0.0)
        if full_end_sec <= full_start_sec:
            return (full_start_sec, full_start_sec)
        if self._viewport_start_sec is None or self._viewport_end_sec is None:
            return (full_start_sec, full_end_sec)
        clipped_start_sec = min(max(self._viewport_start_sec, full_start_sec), full_end_sec)
        clipped_end_sec = min(max(self._viewport_end_sec, full_start_sec), full_end_sec)
        if clipped_end_sec <= clipped_start_sec:
            return (full_start_sec, full_end_sec)
        return (clipped_start_sec, clipped_end_sec)

    def _resolve_frame_axis_height(self, timeline_height: float) -> float:
        if timeline_height <= 0.0:
            return 0.0
        if timeline_height <= 64.0:
            return 14.0
        return min(24.0, max(16.0, timeline_height * 0.14))

    def _build_major_frame_ticks(self, start_sec: float, end_sec: float) -> list[int]:
        start_frame = max(0, self._seconds_to_frame_ceil(start_sec))
        end_frame = max(start_frame, self._seconds_to_frame_floor(end_sec))
        frame_span = max(end_frame - start_frame, 1)
        max_label_count = 9
        min_step = max(1, int(math.ceil(frame_span / max_label_count)))
        step_frame = self._normalized_tick_step(min_step)

        first_frame = ((start_frame + step_frame - 1) // step_frame) * step_frame
        frames: list[int] = []
        frame_no = first_frame
        while frame_no <= end_frame:
            frames.append(frame_no)
            frame_no += step_frame

        if not frames:
            return [start_frame, end_frame]
        if frames[0] != start_frame:
            frames.insert(0, start_frame)
        if frames[-1] != end_frame:
            frames.append(end_frame)
        return frames

    def _build_minor_frame_ticks(
        self,
        start_sec: float,
        end_sec: float,
        major_step: int,
        major_frames: list[int],
    ) -> list[int]:
        if major_step <= 1:
            return []
        minor_step = max(1, major_step // 5)
        if minor_step >= major_step:
            return []

        start_frame = max(0, self._seconds_to_frame_ceil(start_sec))
        end_frame = max(start_frame, self._seconds_to_frame_floor(end_sec))
        first_minor = ((start_frame + minor_step - 1) // minor_step) * minor_step
        major_set = set(major_frames)
        minor_frames: list[int] = []
        frame_no = first_minor
        while frame_no <= end_frame:
            if frame_no not in major_set:
                minor_frames.append(frame_no)
            frame_no += minor_step
        return minor_frames

    def _major_step_from_ticks(self, major_frames: list[int]) -> int:
        if len(major_frames) < 2:
            return 1
        smallest_step = major_frames[1] - major_frames[0]
        for index in range(2, len(major_frames)):
            delta = major_frames[index] - major_frames[index - 1]
            if delta < smallest_step:
                smallest_step = delta
        return max(smallest_step, 1)

    def _normalized_tick_step(self, minimum_step: int) -> int:
        if minimum_step <= 1:
            return 1
        magnitude = 1
        while magnitude * 10 < minimum_step:
            magnitude *= 10
        for candidate in (1, 2, 5, 10):
            step = candidate * magnitude
            if step >= minimum_step:
                return step
        return 10 * magnitude

    def _seconds_to_frame_floor(self, seconds: float) -> int:
        return int(math.floor(max(seconds, 0.0) * _FRAME_RATE + 1e-9))

    def _seconds_to_frame_ceil(self, seconds: float) -> int:
        return int(math.ceil(max(seconds, 0.0) * _FRAME_RATE - 1e-9))

    def _frame_to_seconds(self, frame_no: int) -> float:
        return max(float(frame_no), 0.0) / _FRAME_RATE

    def _seconds_to_x(
        self,
        seconds: float,
        timeline_rect: QRectF,
        visible_start_sec: float,
        visible_end_sec: float,
    ) -> float:
        span_sec = visible_end_sec - visible_start_sec
        if span_sec <= 0.0 or timeline_rect.width() <= 0.0:
            return timeline_rect.left()
        ratio = (seconds - visible_start_sec) / span_sec
        clamped_ratio = min(max(ratio, 0.0), 1.0)
        return timeline_rect.left() + (timeline_rect.width() * clamped_ratio)

    def _theme_colors(self) -> dict[str, str]:
        return _THEME_COLORS[self._theme_name]

    def _normalize_theme_name(self, theme_name: str) -> str:
        resolved_theme = str(theme_name).strip().lower()
        if resolved_theme not in ThemeStrings.SUPPORTED:
            return ThemeStrings.DARK
        return resolved_theme

    def _normalize_viewport_sec(self, start_sec: float, end_sec: float) -> tuple[float, float]:
        normalized_start = self._normalize_non_negative_sec(start_sec)
        normalized_end = self._normalize_non_negative_sec(end_sec)
        if normalized_end < normalized_start:
            normalized_start, normalized_end = normalized_end, normalized_start
        return (normalized_start, normalized_end)

    def _normalize_non_negative_sec(self, value: float) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(resolved):
            return 0.0
        return max(resolved, 0.0)

    def _is_same_viewport(self, start_sec: float, end_sec: float) -> bool:
        if self._viewport_start_sec is None or self._viewport_end_sec is None:
            return False
        return (
            abs(start_sec - self._viewport_start_sec) <= 1e-6
            and abs(end_sec - self._viewport_end_sec) <= 1e-6
        )

    def _draw_playback_cursor(
        self,
        painter: QPainter,
        timeline_rect: QRectF,
        visible_start_sec: float,
        visible_end_sec: float,
    ) -> None:
        if self._playback_position_sec is None:
            return

        visible_span_sec = visible_end_sec - visible_start_sec
        if visible_span_sec <= 0.0:
            return

        if self._playback_position_sec < visible_start_sec or self._playback_position_sec > visible_end_sec:
            return

        ratio = (self._playback_position_sec - visible_start_sec) / visible_span_sec
        x = timeline_rect.left() + (timeline_rect.width() * min(max(ratio, 0.0), 1.0))

        painter.setPen(QPen(QColor(self._theme_colors()["cursor"]), 1))
        painter.drawLine(
            int(x),
            int(timeline_rect.top()),
            int(x),
            int(timeline_rect.bottom()),
        )
