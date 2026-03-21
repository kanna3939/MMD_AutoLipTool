from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from gui.preview_transform import PREVIEW_ROW_VOWELS, PreviewData, PreviewRow, empty_preview_data

_ROW_COLORS: dict[str, QColor] = {
    "あ": QColor("#d1495b"),
    "い": QColor("#edae49"),
    "う": QColor("#66a182"),
    "え": QColor("#2e86ab"),
    "お": QColor("#5a4e7c"),
}


class PreviewArea(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._preview_data: PreviewData = empty_preview_data()
        self.setMinimumHeight(140)

    def set_preview_data(self, preview_data: PreviewData) -> None:
        self._preview_data = preview_data
        self.update()

    def clear_preview(self) -> None:
        self._preview_data = empty_preview_data()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        canvas = self.rect()
        painter.fillRect(canvas, QColor("#ffffff"))

        if canvas.width() <= 4 or canvas.height() <= 4:
            return

        margin = 8
        label_width = 18
        inner = canvas.adjusted(margin, margin, -margin, -margin)
        timeline_rect = inner.adjusted(label_width + 6, 0, 0, 0)
        rows = self._rows_with_fallback()
        row_count = len(rows)
        row_height = timeline_rect.height() / max(row_count, 1)

        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawRect(timeline_rect)

        for row_index, row in enumerate(rows):
            top = timeline_rect.top() + (row_height * row_index)
            row_rect = QRectF(timeline_rect.left(), top, timeline_rect.width(), row_height)
            self._draw_row_label(painter, inner, top, row_height, row.vowel)
            self._draw_row_grid(painter, row_rect, row_index, row_count)
            self._draw_row_segments(painter, row_rect, row, rows)

    def _rows_with_fallback(self) -> list[PreviewRow]:
        if self._preview_data.rows:
            return self._preview_data.rows
        return empty_preview_data().rows

    def _draw_row_label(
        self,
        painter: QPainter,
        inner: QRectF,
        top: float,
        row_height: float,
        vowel: str,
    ) -> None:
        label_rect = QRectF(inner.left(), top, 18, row_height)
        painter.setPen(QColor("#333333"))
        painter.drawText(label_rect, int(Qt.AlignVCenter | Qt.AlignCenter), vowel)

    def _draw_row_grid(self, painter: QPainter, row_rect: QRectF, row_index: int, row_count: int) -> None:
        if row_index + 1 >= row_count:
            return
        painter.setPen(QPen(QColor("#e6e6e6"), 1))
        painter.drawLine(
            int(row_rect.left()),
            int(row_rect.bottom()),
            int(row_rect.right()),
            int(row_rect.bottom()),
        )

    def _draw_row_segments(
        self,
        painter: QPainter,
        row_rect: QRectF,
        row: PreviewRow,
        all_rows: list[PreviewRow],
    ) -> None:
        max_end_sec = self._max_end_sec(all_rows)
        if max_end_sec <= 0.0:
            return

        base_color = _ROW_COLORS.get(row.vowel, QColor("#2e86ab"))
        for segment in row.segments:
            start_ratio = max(0.0, min(segment.start_sec / max_end_sec, 1.0))
            end_ratio = max(0.0, min(segment.end_sec / max_end_sec, 1.0))
            if end_ratio < start_ratio:
                end_ratio = start_ratio

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
