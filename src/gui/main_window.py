import os
import math
from collections.abc import Mapping, Sequence
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

try:
    import winsound
except ImportError:  # pragma: no cover - non-Windows fallback
    winsound = None

from PySide6.QtCore import QTimer, Qt
from core import (
    PipelineError,
    TextProcessingError,
    VowelTimingPlan,
    WavAnalysisResult,
    analyze_wav_file,
    build_vowel_timing_plan,
    generate_vmd_from_text_wav,
    hiragana_to_vowel_string,
    load_waveform_preview,
    text_to_hiragana,
)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMenuBar,
    QMessageBox,
    QProgressDialog,
    QVBoxLayout,
    QWidget,
)
from gui.central_panels import (
    CenterContentContainer,
    LeftInfoPanel,
    MorphUpperLimitRow,
    RightDisplayContainer,
)
from gui.i18n_strings import MainWindowStrings, StatusTexts, ThemeStrings
from gui.operation_panel import OperationPanel
from gui.playback_controller import PlaybackController
from gui.preview_transform import build_preview_data
from gui.status_panel import StatusPanel
from gui.view_sync import ViewSync

_PLAYBACK_STATUS_PREFIX = StatusTexts.PLAYBACK
_DEFAULT_ZOOM_LEVELS: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)
_PATH_DISPLAY_MAX_FULL_LENGTH = 48
_DEFAULT_THEME = ThemeStrings.DARK
_DEFAULT_WINDOW_WIDTH = 1270
_DEFAULT_WINDOW_HEIGHT = 714
_MIN_WINDOW_WIDTH = 720
_MIN_WINDOW_HEIGHT = 405
_DEFAULT_CENTER_SPLITTER_RATIO = (30, 70)
_DEFAULT_UI_FONT_FAMILY = '"Yu Gothic UI", "Meiryo", sans-serif'
_DEFAULT_UI_FONT_SIZE_PT = 11
_MAIN_LAYOUT_MARGIN = 6
_MAIN_LAYOUT_SPACING = 6
_VIEWPORT_SCROLLBAR_UNITS_PER_SEC = 1000
_UI_SETTING_KEY_THEME = "theme"
_UI_SETTING_KEY_CENTER_SPLITTER_RATIO = "center_splitter_ratio"


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MainWindowRoot")
        self.setWindowTitle(MainWindowStrings.WINDOW_TITLE)
        self.resize(_DEFAULT_WINDOW_WIDTH, _DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(_MIN_WINDOW_WIDTH, _MIN_WINDOW_HEIGHT)

        self.selected_text_path: str | None = None
        self.selected_wav_path: str | None = None
        self.selected_text_content: str = ""
        self.selected_hiragana_content: str = ""
        self.selected_vowel_content: str = ""
        self.selected_wav_analysis: WavAnalysisResult | None = None
        self.current_timing_plan: VowelTimingPlan | None = None
        self.last_text_dialog_dir: str | None = None
        self.last_wav_dialog_dir: str | None = None
        self._is_processing = False
        self._processing_dialog: QProgressDialog | None = None
        self._recent_file_limit = 10
        self.recent_text_files: list[str] = []
        self.recent_wav_files: list[str] = []
        self._zoom_levels: tuple[float, ...] = _DEFAULT_ZOOM_LEVELS
        self._zoom_level_index = 0
        self._current_theme = _DEFAULT_THEME
        self._current_center_splitter_ratio = _DEFAULT_CENTER_SPLITTER_RATIO

        layout = QVBoxLayout()
        layout.setContentsMargins(
            _MAIN_LAYOUT_MARGIN,
            _MAIN_LAYOUT_MARGIN,
            _MAIN_LAYOUT_MARGIN,
            _MAIN_LAYOUT_MARGIN,
        )
        layout.setSpacing(_MAIN_LAYOUT_SPACING)
        self.menu_bar = self._build_menu_bar()
        self.menu_bar.setObjectName("MainMenuBar")
        layout.setMenuBar(self.menu_bar)

        self.operation_panel = OperationPanel()
        # Keep existing attribute names to minimize impact on state-update paths.
        self.text_button = self.operation_panel.text_button
        self.wav_button = self.operation_panel.wav_button
        self.process_button = self.operation_panel.process_button
        self.output_button = self.operation_panel.output_button
        self.play_button = self.operation_panel.play_button
        self.stop_button = self.operation_panel.stop_button
        self.zoom_in_button = self.operation_panel.zoom_in_button
        self.zoom_out_button = self.operation_panel.zoom_out_button
        self.morph_upper_limit_row = MorphUpperLimitRow(self)
        self.morph_upper_limit_label = self.morph_upper_limit_row.label
        self.morph_upper_limit_input = self.morph_upper_limit_row.input

        self.left_info_panel = LeftInfoPanel(self)
        self.text_path_label = self.left_info_panel.text_path_label
        self.wav_path_label = self.left_info_panel.wav_path_label
        self._set_file_path_label(self.text_path_label, "TEXT", None)
        self._set_file_path_label(self.wav_path_label, "WAV", None)
        self.text_preview_label = self.left_info_panel.text_preview_label
        self.text_preview = self.left_info_panel.text_preview
        self.hiragana_preview_label = self.left_info_panel.hiragana_preview_label
        self.hiragana_preview = self.left_info_panel.hiragana_preview
        self.vowel_preview_label = self.left_info_panel.vowel_preview_label
        self.vowel_preview = self.left_info_panel.vowel_preview
        self.wav_info_label = self.left_info_panel.wav_info_label

        self.right_display_container = RightDisplayContainer(self)
        self.wav_waveform_view = self.right_display_container.wav_waveform_view
        self.preview_area = self.right_display_container.preview_area
        self.viewport_scrollbar = self.right_display_container.viewport_scrollbar
        self.status_panel = StatusPanel("\u51fa\u529b\u72b6\u614b: \u672a\u5b9f\u884c")
        self.playback_controller = PlaybackController(self)
        self.view_sync = ViewSync(self)
        self._syncing_viewport_scrollbar = False
        self._sync_view_action_checks()

        self.morph_upper_limit_input.valueChanged.connect(self._on_morph_upper_limit_changed)

        self._connect_operation_panel()
        self._connect_playback_layer()
        self._connect_viewport_layer()
        self.center_content_container = CenterContentContainer(
            self.left_info_panel,
            self.right_display_container,
            self,
        )
        self.center_splitter = self.center_content_container.splitter
        self.center_splitter.splitterMoved.connect(self._on_center_splitter_moved)
        self.apply_ui_settings(self.default_ui_settings())

        layout.addWidget(self.operation_panel)
        layout.addWidget(self.morph_upper_limit_row)
        layout.addWidget(self.center_content_container, 1)
        layout.addWidget(self.status_panel)

        self.setLayout(layout)
        QTimer.singleShot(0, self._apply_initial_center_splitter_ratio)
        self._update_action_states()

    def _connect_playback_layer(self) -> None:
        self.playback_controller.playback_active_changed.connect(
            self._on_playback_active_changed
        )
        self.playback_controller.position_sec_changed.connect(
            self._on_playback_position_sec_changed
        )
        self.playback_controller.playback_finished.connect(self._on_playback_finished)
        self.view_sync.shared_position_sec_changed.connect(
            self.wav_waveform_view.set_playback_position_sec
        )
        self.view_sync.shared_position_sec_changed.connect(
            self.preview_area.set_playback_position_sec
        )
        self.view_sync.shared_position_sec_changed.connect(
            self._on_shared_position_sec_changed
        )
        self.view_sync.shared_position_reset.connect(
            self.wav_waveform_view.clear_playback_cursor
        )
        self.view_sync.shared_position_reset.connect(
            self.preview_area.clear_playback_cursor
        )
        self.view_sync.shared_position_reset.connect(self._on_shared_position_reset)

    def _connect_viewport_layer(self) -> None:
        self.wav_waveform_view.pan_requested.connect(self._on_pan_requested)
        self.preview_area.pan_requested.connect(self._on_pan_requested)
        self.viewport_scrollbar.valueChanged.connect(
            self._on_viewport_scrollbar_value_changed
        )
        self.view_sync.shared_viewport_sec_changed.connect(
            self.wav_waveform_view.set_viewport_sec
        )
        self.view_sync.shared_viewport_sec_changed.connect(
            self.preview_area.set_viewport_sec
        )
        self.view_sync.shared_viewport_sec_changed.connect(
            self._sync_viewport_scrollbar_to_shared_viewport
        )
        self.view_sync.shared_viewport_reset.connect(
            self.wav_waveform_view.clear_viewport_sec
        )
        self.view_sync.shared_viewport_reset.connect(
            self.preview_area.clear_viewport_sec
        )
        self.view_sync.shared_viewport_reset.connect(
            self._reset_viewport_scrollbar_position
        )
        self._sync_viewport_scrollbar_to_shared_viewport(
            *self.view_sync.shared_viewport_sec()
        )

    def _connect_operation_panel(self) -> None:
        self.operation_panel.open_text_requested.connect(self._open_text_file)
        self.operation_panel.open_wav_requested.connect(self._open_wav_file)
        self.operation_panel.run_processing_requested.connect(self._run_processing_requested)
        self.operation_panel.save_requested.connect(self._save_vmd_file)
        self.operation_panel.play_requested.connect(self._on_play_requested)
        self.operation_panel.stop_requested.connect(self._on_stop_requested)
        self.operation_panel.zoom_in_requested.connect(self._on_zoom_in_requested)
        self.operation_panel.zoom_out_requested.connect(self._on_zoom_out_requested)

    # Common GUI entry points (buttons and menu actions should share these).
    def _open_text_file(self) -> None:
        self._select_text_file()

    def _open_wav_file(self) -> None:
        self._select_wav_file()

    def _run_processing_requested(self) -> None:
        if self._is_processing:
            return
        self._run_processing()

    def _run_reanalysis_requested(self) -> None:
        if self._is_processing:
            return
        self._run_processing()

    def _save_vmd_file(self) -> None:
        self._export_vmd()

    def _close_application(self) -> None:
        self.close()

    def _on_play_requested(self) -> None:
        if not self._sync_playback_source_from_selected_wav():
            return
        self.playback_controller.start_playback()

    def _on_stop_requested(self) -> None:
        self.playback_controller.stop_playback()
        self._reset_shared_playback_position()

    def _on_playback_position_sec_changed(self, position_sec: float) -> None:
        self.view_sync.update_shared_position_sec(position_sec)

    def _on_playback_finished(self) -> None:
        self._reset_shared_playback_position()
        self._update_action_states()

    def _on_playback_active_changed(self, _: bool) -> None:
        if self.playback_controller.is_playing():
            self._on_shared_position_sec_changed(self.view_sync.shared_position_sec())
        self._update_action_states()

    def _on_shared_position_sec_changed(self, position_sec: float) -> None:
        self._refresh_playback_frame_status(position_sec)

    def _on_shared_position_reset(self) -> None:
        self._restore_status_after_playback_stop()

    def _reset_shared_playback_position(self) -> None:
        self.view_sync.reset_shared_position()

    def _has_loaded_wav_for_viewport(self) -> bool:
        return bool(self.selected_wav_path and self.selected_wav_analysis is not None)

    def _current_wav_duration_sec(self) -> float:
        if self.selected_wav_analysis is None:
            return 0.0
        return max(float(self.selected_wav_analysis.duration_sec), 0.0)

    def _reset_zoom_level_state(self) -> None:
        self._zoom_level_index = self._clamp_zoom_level_index(0)

    def _on_zoom_in_requested(self) -> None:
        self._step_zoom_level(1)

    def _on_zoom_out_requested(self) -> None:
        self._step_zoom_level(-1)

    def _on_pan_requested(self, delta_sec: float) -> None:
        self._apply_pan_delta_to_shared_viewport(delta_sec)

    def _on_viewport_scrollbar_value_changed(self, raw_value: int) -> None:
        if self._syncing_viewport_scrollbar:
            return
        if not self._has_loaded_wav_for_viewport():
            return

        duration_sec = self._current_wav_duration_sec()
        if duration_sec <= 0.0:
            return

        current_start_sec, current_end_sec = self._resolved_current_viewport_for_pan(
            duration_sec
        )
        current_span_sec = current_end_sec - current_start_sec
        if current_span_sec <= 0.0:
            return

        max_start_sec = max(duration_sec - current_span_sec, 0.0)
        resolved_start_sec = min(
            max(self._scrollbar_value_to_sec(raw_value), 0.0),
            max_start_sec,
        )
        resolved_end_sec = min(resolved_start_sec + current_span_sec, duration_sec)
        self.view_sync.update_shared_viewport_sec(resolved_start_sec, resolved_end_sec)

    def _step_zoom_level(self, step: int) -> None:
        if step == 0:
            return
        if not self._has_loaded_wav_for_viewport():
            self._update_action_states()
            return
        next_index = self._clamp_zoom_level_index(self._zoom_level_index + int(step))
        if next_index == self._zoom_level_index:
            self._update_action_states()
            return
        self._zoom_level_index = next_index
        self._apply_zoom_level_to_shared_viewport()
        self._update_action_states()

    def _apply_zoom_level_to_shared_viewport(self) -> None:
        if not self._has_loaded_wav_for_viewport():
            self.view_sync.reset_shared_viewport()
            return
        duration_sec = self._current_wav_duration_sec()
        if duration_sec <= 0.0:
            self.view_sync.update_shared_viewport_sec(0.0, 0.0)
            return
        zoom_factor = self._current_zoom_factor()
        new_span_sec = duration_sec / zoom_factor
        new_span_sec = min(max(new_span_sec, 0.0), duration_sec)
        if new_span_sec >= duration_sec - 1e-9:
            self.view_sync.update_shared_viewport_sec(0.0, duration_sec)
            return

        current_start_sec, current_end_sec = self._resolved_current_viewport_for_pan(
            duration_sec
        )
        current_center_sec = self._clamp_sec_within_duration(
            (current_start_sec + current_end_sec) * 0.5,
            duration_sec,
        )
        new_start_sec, new_end_sec = self._build_center_preserving_viewport(
            duration_sec,
            current_center_sec,
            new_span_sec,
        )
        if new_end_sec <= new_start_sec:
            self.view_sync.update_shared_viewport_sec(0.0, duration_sec)
            return
        self.view_sync.update_shared_viewport_sec(new_start_sec, new_end_sec)

    def _apply_pan_delta_to_shared_viewport(self, delta_sec: float) -> None:
        if not self._has_loaded_wav_for_viewport():
            return
        duration_sec = self._current_wav_duration_sec()
        if duration_sec <= 0.0:
            self.view_sync.update_shared_viewport_sec(0.0, 0.0)
            return

        current_start_sec, current_end_sec = self._resolved_current_viewport_for_pan(
            duration_sec
        )
        current_span_sec = current_end_sec - current_start_sec
        if current_span_sec <= 0.0:
            return
        if current_span_sec >= duration_sec - 1e-9:
            self.view_sync.update_shared_viewport_sec(0.0, duration_sec)
            return

        resolved_delta_sec = self._normalize_finite_sec_delta(delta_sec)
        if abs(resolved_delta_sec) <= 1e-9:
            return

        max_start_sec = max(duration_sec - current_span_sec, 0.0)
        next_start_sec = min(
            max(current_start_sec + resolved_delta_sec, 0.0),
            max_start_sec,
        )
        next_end_sec = next_start_sec + current_span_sec
        self.view_sync.update_shared_viewport_sec(next_start_sec, next_end_sec)

    def _sync_viewport_scrollbar_to_shared_viewport(
        self,
        start_sec: float,
        end_sec: float,
    ) -> None:
        scrollbar_state = self._build_viewport_scrollbar_state(start_sec, end_sec)

        self._syncing_viewport_scrollbar = True
        try:
            self.viewport_scrollbar.setEnabled(scrollbar_state["enabled"])
            self.viewport_scrollbar.setRange(
                scrollbar_state["minimum"],
                scrollbar_state["maximum"],
            )
            self.viewport_scrollbar.setPageStep(scrollbar_state["page_step"])
            self.viewport_scrollbar.setSingleStep(scrollbar_state["single_step"])
            self.viewport_scrollbar.setValue(scrollbar_state["value"])
        finally:
            self._syncing_viewport_scrollbar = False

    def _reset_viewport_scrollbar_position(self) -> None:
        self._sync_viewport_scrollbar_to_shared_viewport(0.0, 0.0)

    def _build_viewport_scrollbar_state(
        self,
        start_sec: float,
        end_sec: float,
    ) -> dict[str, int | bool]:
        default_state: dict[str, int | bool] = {
            "enabled": False,
            "minimum": 0,
            "maximum": 0,
            "page_step": 1,
            "single_step": 1,
            "value": 0,
        }
        if not self._has_loaded_wav_for_viewport():
            return default_state

        duration_sec = self._current_wav_duration_sec()
        if duration_sec <= 0.0:
            return default_state

        normalized_start_sec = min(
            max(self._normalize_non_negative_sec(start_sec), 0.0),
            duration_sec,
        )
        normalized_end_sec = min(
            max(self._normalize_non_negative_sec(end_sec), 0.0),
            duration_sec,
        )
        if normalized_end_sec < normalized_start_sec:
            normalized_start_sec, normalized_end_sec = (
                normalized_end_sec,
                normalized_start_sec,
            )
        if normalized_end_sec <= normalized_start_sec:
            normalized_start_sec, normalized_end_sec = (0.0, duration_sec)

        viewport_span_sec = max(normalized_end_sec - normalized_start_sec, 0.0)
        total_value = self._sec_to_scrollbar_value(duration_sec)
        page_step_value = min(
            max(self._sec_to_scrollbar_value(viewport_span_sec), 1),
            max(total_value, 1),
        )
        maximum_value = max(total_value - page_step_value, 0)
        single_step_value = max(page_step_value // 16, 1)
        current_value = min(max(self._sec_to_scrollbar_value(normalized_start_sec), 0), maximum_value)

        # Snap the scrollbar to the exact edges when the viewport is effectively clamped.
        # This reduces the "pulled away from the edge" feel caused by sec->int rounding.
        if normalized_start_sec <= 1e-6:
            current_value = 0
        elif normalized_end_sec >= duration_sec - 1e-6:
            current_value = maximum_value

        can_scroll = maximum_value > 0 and page_step_value < total_value

        return {
            "enabled": can_scroll,
            "minimum": 0,
            "maximum": maximum_value,
            "page_step": page_step_value,
            "single_step": single_step_value,
            "value": current_value,
        }

    def _resolved_current_viewport_for_pan(self, duration_sec: float) -> tuple[float, float]:
        shared_start_sec, shared_end_sec = self.view_sync.shared_viewport_sec()
        start_sec = self._normalize_non_negative_sec(shared_start_sec)
        end_sec = self._normalize_non_negative_sec(shared_end_sec)

        if end_sec < start_sec:
            start_sec, end_sec = end_sec, start_sec
        start_sec = min(start_sec, duration_sec)
        end_sec = min(end_sec, duration_sec)
        if end_sec <= start_sec:
            return (0.0, duration_sec)
        return (start_sec, end_sec)

    def _build_center_preserving_viewport(
        self,
        duration_sec: float,
        center_sec: float,
        span_sec: float,
    ) -> tuple[float, float]:
        resolved_duration_sec = self._normalize_non_negative_sec(duration_sec)
        if resolved_duration_sec <= 0.0:
            return (0.0, 0.0)

        resolved_span_sec = min(
            max(self._normalize_non_negative_sec(span_sec), 0.0),
            resolved_duration_sec,
        )
        if resolved_span_sec >= resolved_duration_sec - 1e-9:
            return (0.0, resolved_duration_sec)
        if resolved_span_sec <= 0.0:
            return (0.0, resolved_duration_sec)

        resolved_center_sec = self._clamp_sec_within_duration(
            center_sec,
            resolved_duration_sec,
        )
        half_span_sec = resolved_span_sec * 0.5
        start_sec = resolved_center_sec - half_span_sec
        end_sec = resolved_center_sec + half_span_sec

        if start_sec < 0.0:
            end_sec -= start_sec
            start_sec = 0.0
        if end_sec > resolved_duration_sec:
            overshoot_sec = end_sec - resolved_duration_sec
            start_sec -= overshoot_sec
            end_sec = resolved_duration_sec

        max_start_sec = max(resolved_duration_sec - resolved_span_sec, 0.0)
        start_sec = min(max(start_sec, 0.0), max_start_sec)
        end_sec = min(start_sec + resolved_span_sec, resolved_duration_sec)
        return (start_sec, end_sec)

    def _current_zoom_factor(self) -> float:
        if not self._zoom_levels:
            return 1.0
        current_index = self._clamp_zoom_level_index(self._zoom_level_index)
        raw_factor = self._zoom_levels[current_index]
        try:
            resolved_factor = float(raw_factor)
        except (TypeError, ValueError):
            return 1.0
        if resolved_factor <= 0.0:
            return 1.0
        return resolved_factor

    def _clamp_zoom_level_index(self, level_index: int) -> int:
        if not self._zoom_levels:
            return 0
        return min(max(int(level_index), 0), len(self._zoom_levels) - 1)

    def _normalize_non_negative_sec(self, value: float) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(resolved):
            return 0.0
        return max(resolved, 0.0)

    def _clamp_sec_within_duration(self, value_sec: float, duration_sec: float) -> float:
        resolved_duration_sec = self._normalize_non_negative_sec(duration_sec)
        if resolved_duration_sec <= 0.0:
            return 0.0
        return min(
            max(self._normalize_non_negative_sec(value_sec), 0.0),
            resolved_duration_sec,
        )

    def _normalize_finite_sec_delta(self, value: float) -> float:
        try:
            resolved = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(resolved):
            return 0.0
        return resolved

    def _sec_to_scrollbar_value(self, value_sec: float) -> int:
        normalized_sec = self._normalize_non_negative_sec(value_sec)
        return max(int(round(normalized_sec * _VIEWPORT_SCROLLBAR_UNITS_PER_SEC)), 0)

    def _scrollbar_value_to_sec(self, scrollbar_value: int) -> float:
        try:
            resolved_value = int(scrollbar_value)
        except (TypeError, ValueError):
            return 0.0
        return max(resolved_value, 0) / _VIEWPORT_SCROLLBAR_UNITS_PER_SEC

    def _snapshot_zoom_and_viewport_state(self) -> tuple[int, float, float]:
        viewport_start_sec, viewport_end_sec = self.view_sync.shared_viewport_sec()
        return (self._zoom_level_index, viewport_start_sec, viewport_end_sec)

    def _restore_zoom_and_viewport_state_from_snapshot(
        self,
        snapshot: tuple[int, float, float] | None,
    ) -> None:
        if snapshot is None:
            self._reset_zoom_and_viewport_state()
            return

        zoom_level_index, viewport_start_sec, viewport_end_sec = snapshot
        self._zoom_level_index = self._clamp_zoom_level_index(zoom_level_index)
        if not self._has_loaded_wav_for_viewport():
            self.view_sync.reset_shared_viewport()
            return

        duration_sec = self._current_wav_duration_sec()
        if duration_sec <= 0.0:
            self.view_sync.update_shared_viewport_sec(0.0, 0.0)
            return

        resolved_start_sec = min(
            max(self._normalize_non_negative_sec(viewport_start_sec), 0.0),
            duration_sec,
        )
        resolved_end_sec = min(
            max(self._normalize_non_negative_sec(viewport_end_sec), 0.0),
            duration_sec,
        )
        if resolved_end_sec <= resolved_start_sec:
            self._apply_zoom_level_to_shared_viewport()
            return
        self.view_sync.update_shared_viewport_sec(resolved_start_sec, resolved_end_sec)

    def _reset_shared_viewport_for_current_wav(self) -> None:
        if not self._has_loaded_wav_for_viewport():
            self.view_sync.reset_shared_viewport()
            return
        self.view_sync.update_shared_viewport_sec(0.0, self._current_wav_duration_sec())

    def _reset_zoom_and_viewport_state(self) -> None:
        self._reset_zoom_level_state()
        self._reset_shared_viewport_for_current_wav()

    def _stop_playback_for_timing_invalidation(self) -> None:
        self.playback_controller.stop_playback()
        self._reset_shared_playback_position()

    def _sync_playback_source_from_selected_wav(self) -> bool:
        selected_wav_path = self.selected_wav_path
        if not selected_wav_path:
            return False
        current_source_path = self.playback_controller.source_path()
        if current_source_path is not None and str(current_source_path) == selected_wav_path:
            return True
        return self.playback_controller.set_wav_path(selected_wav_path)

    def _refresh_playback_frame_status(self, position_sec: float | None = None) -> None:
        if not self.playback_controller.is_playing():
            return

        current_status_text = self.status_panel.status_text()
        if not self._status_allows_playback_frame_override(current_status_text):
            return

        resolved_position_sec = (
            self.playback_controller.current_position_sec()
            if position_sec is None
            else max(float(position_sec), 0.0)
        )
        self._set_output_status(self._format_playback_status(resolved_position_sec))

    def _restore_status_after_playback_stop(self) -> None:
        if not self._is_playback_status_text(self.status_panel.status_text()):
            return
        self._set_ready_status()

    def _format_playback_status(self, position_sec: float) -> str:
        del position_sec
        return _PLAYBACK_STATUS_PREFIX

    def _status_allows_playback_frame_override(self, status_text: str) -> bool:
        if self._is_playback_status_text(status_text):
            return True
        return self._is_ready_status_text(status_text)

    def _is_playback_status_text(self, status_text: str) -> bool:
        return status_text.startswith(_PLAYBACK_STATUS_PREFIX)

    def _is_ready_status_text(self, status_text: str) -> bool:
        return any(status_text.startswith(prefix) for prefix in StatusTexts.READY_PREFIXES)

    def _ensure_processing_dialog(self) -> QProgressDialog:
        if self._processing_dialog is None:
            dialog = QProgressDialog(MainWindowStrings.PROCESSING_DIALOG_LABEL, "", 0, 0, self)
            dialog.setWindowTitle(MainWindowStrings.PROCESSING_DIALOG_TITLE)
            dialog.setCancelButton(None)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.setAutoClose(False)
            dialog.setAutoReset(False)
            dialog.setMinimumDuration(0)
            dialog.setValue(0)
            dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
            dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            self._processing_dialog = dialog
        return self._processing_dialog

    def _show_processing_dialog(self) -> None:
        dialog = self._ensure_processing_dialog()
        dialog.setRange(0, 0)
        dialog.setValue(0)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _hide_processing_dialog(self) -> None:
        if self._processing_dialog is None:
            return
        self._processing_dialog.hide()

    def _begin_processing_session(self) -> None:
        self._is_processing = True
        self._update_action_states()
        self._set_output_status(StatusTexts.PROCESSING)
        self._show_processing_dialog()
        QApplication.processEvents()

    def _end_processing_session(self) -> None:
        self._hide_processing_dialog()
        self._is_processing = False
        if self.status_panel.status_text() == StatusTexts.PROCESSING:
            self._set_output_status(StatusTexts.FAILURE)
        self._play_analysis_completion_sound()
        self._update_action_states()

    def _play_analysis_completion_sound(self) -> None:
        if winsound is None:
            return
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except RuntimeError:
            return

    def _show_version_info(self) -> None:
        pyopenjtalk_version = self._resolve_installed_version(["pyopenjtalk"])
        whisper_version = self._resolve_installed_version(["openai-whisper", "whisper"])
        QMessageBox.information(
            self,
            MainWindowStrings.VERSION_INFO_TITLE,
            "\n".join(
                [
                    MainWindowStrings.VERSION_INFO_APP_VERSION,
                    f"pyopenjtalk: {pyopenjtalk_version}",
                    f"whisper: {whisper_version}",
                ]
            ),
        )

    def _resolve_installed_version(self, package_names: list[str]) -> str:
        for package_name in package_names:
            try:
                return package_version(package_name)
            except PackageNotFoundError:
                continue
        return "not installed"

    def _set_file_path_label(
        self,
        label: QLabel,
        prefix: str,
        full_path: str | None,
    ) -> None:
        normalized_path = ""
        if full_path is not None:
            normalized_path = str(full_path).strip()

        if not normalized_path:
            label.setText(f"{prefix}: \u672a\u9078\u629e")
            label.setToolTip("")
            return

        display_path = self._build_elided_file_path_display(normalized_path)
        label.setText(f"{prefix}: {display_path}")
        label.setToolTip(normalized_path)

    def _build_elided_file_path_display(self, full_path: str) -> str:
        normalized_path = str(Path(full_path))
        if len(normalized_path) <= _PATH_DISPLAY_MAX_FULL_LENGTH:
            return normalized_path

        path_obj = Path(normalized_path)
        file_name = path_obj.name or normalized_path
        parent_name = path_obj.parent.name
        anchor = path_obj.drive or path_obj.anchor.rstrip("\\/")

        if anchor:
            if parent_name and parent_name != anchor:
                return f"{anchor}\\...\\{parent_name}\\{file_name}"
            return f"{anchor}\\...\\{file_name}"
        if parent_name:
            return f"...\\{parent_name}\\{file_name}"
        return file_name

    def _build_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar(self)

        file_menu = menu_bar.addMenu(MainWindowStrings.MENU_FILE)
        self.action_open_text = QAction("TEXT\u3092\u958b\u304f", self)
        self.action_open_wav = QAction("WAV\u3092\u958b\u304f", self)
        self.action_save_vmd = QAction("VMD\u3092\u4fdd\u5b58", self)
        self.action_exit = QAction("\u7d42\u4e86", self)
        file_menu.addAction(self.action_open_text)
        file_menu.addAction(self.action_open_wav)
        self.menu_recent_text = file_menu.addMenu("\u6700\u8fd1\u4f7f\u3063\u305fTEXT")
        self.menu_recent_wav = file_menu.addMenu("\u6700\u8fd1\u4f7f\u3063\u305fWAV")
        file_menu.addSeparator()
        file_menu.addAction(self.action_save_vmd)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        run_menu = menu_bar.addMenu(MainWindowStrings.MENU_RUN)
        self.action_run_processing = QAction("\u51e6\u7406\u5b9f\u884c", self)
        self.action_reanalyze = QAction("\u518d\u89e3\u6790", self)
        run_menu.addAction(self.action_run_processing)
        run_menu.addAction(self.action_reanalyze)

        view_menu = menu_bar.addMenu(MainWindowStrings.MENU_VIEW)
        self.action_show_30fps_lines = QAction("30fps\u7e26\u7dda\u3092\u8868\u793a", self)
        self.action_show_vowel_labels = QAction("\u6bcd\u97f3\u30e9\u30d9\u30eb\u3092\u8868\u793a", self)
        self.action_show_event_ranges = QAction("\u30a4\u30d9\u30f3\u30c8\u533a\u9593\u3092\u8868\u793a", self)
        self.action_zoom_in = QAction("Zoom In", self)
        self.action_zoom_out = QAction("Zoom Out", self)
        self.action_reset_waveform_view = QAction("\u6ce2\u5f62\u8868\u793a\u3092\u521d\u671f\u5316", self)
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)
        self.action_theme_dark = QAction(MainWindowStrings.ACTION_THEME_DARK, self)
        self.action_theme_light = QAction(MainWindowStrings.ACTION_THEME_LIGHT, self)
        self.action_theme_dark.setCheckable(True)
        self.action_theme_light.setCheckable(True)
        self.theme_action_group.addAction(self.action_theme_dark)
        self.theme_action_group.addAction(self.action_theme_light)
        self.action_show_30fps_lines.setCheckable(True)
        self.action_show_vowel_labels.setCheckable(True)
        self.action_show_event_ranges.setCheckable(True)
        view_menu.addAction(self.action_show_30fps_lines)
        view_menu.addAction(self.action_show_vowel_labels)
        view_menu.addAction(self.action_show_event_ranges)
        view_menu.addSeparator()
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addSeparator()
        view_menu.addAction(self.action_reset_waveform_view)
        view_menu.addSeparator()
        self.menu_theme = view_menu.addMenu(MainWindowStrings.MENU_VIEW_THEME)
        self.menu_theme.addAction(self.action_theme_dark)
        self.menu_theme.addAction(self.action_theme_light)

        help_menu = menu_bar.addMenu(MainWindowStrings.MENU_HELP)
        self.action_show_version = QAction("\u30d0\u30fc\u30b8\u30e7\u30f3\u60c5\u5831", self)
        help_menu.addAction(self.action_show_version)

        self._connect_menu_actions()
        self._refresh_recent_file_menus()

        return menu_bar

    def _connect_menu_actions(self) -> None:
        self.action_open_text.triggered.connect(self._open_text_file)
        self.action_open_wav.triggered.connect(self._open_wav_file)
        self.action_save_vmd.triggered.connect(self._save_vmd_file)
        self.action_exit.triggered.connect(self._close_application)
        self.action_run_processing.triggered.connect(self._run_processing_requested)
        self.action_reanalyze.triggered.connect(self._run_reanalysis_requested)
        self.action_show_30fps_lines.toggled.connect(self._on_show_30fps_lines_toggled)
        self.action_show_vowel_labels.toggled.connect(self._on_show_vowel_labels_toggled)
        self.action_show_event_ranges.toggled.connect(self._on_show_event_ranges_toggled)
        self.action_zoom_in.triggered.connect(self._on_zoom_in_requested)
        self.action_zoom_out.triggered.connect(self._on_zoom_out_requested)
        self.action_reset_waveform_view.triggered.connect(self._reset_waveform_view_options)
        self.action_theme_dark.triggered.connect(
            lambda _checked=False: self.apply_theme(ThemeStrings.DARK)
        )
        self.action_theme_light.triggered.connect(
            lambda _checked=False: self.apply_theme(ThemeStrings.LIGHT)
        )
        self.action_show_version.triggered.connect(self._show_version_info)

    def _sync_view_action_checks(self) -> None:
        show_frame_grid, show_vowel_labels, show_event_regions = (
            self.wav_waveform_view.overlay_visibility()
        )
        for action, checked in (
            (self.action_show_30fps_lines, show_frame_grid),
            (self.action_show_vowel_labels, show_vowel_labels),
            (self.action_show_event_ranges, show_event_regions),
        ):
            previous_blocked = action.blockSignals(True)
            action.setChecked(checked)
            action.blockSignals(previous_blocked)

    def current_theme(self) -> str:
        return self._current_theme

    def default_theme(self) -> str:
        return _DEFAULT_THEME

    def default_center_splitter_ratio(self) -> tuple[int, int]:
        return _DEFAULT_CENTER_SPLITTER_RATIO

    def current_center_splitter_ratio(self) -> tuple[int, int]:
        sizes = self.center_splitter.sizes()
        resolved_ratio = self._normalize_center_splitter_ratio(sizes)
        self._current_center_splitter_ratio = resolved_ratio
        return resolved_ratio

    def apply_center_splitter_ratio(self, ratio: Sequence[int] | None) -> tuple[int, int]:
        resolved_ratio = self._normalize_center_splitter_ratio(ratio)
        self._current_center_splitter_ratio = resolved_ratio
        self.center_splitter.setStretchFactor(0, resolved_ratio[0])
        self.center_splitter.setStretchFactor(1, resolved_ratio[1])
        self.center_splitter.setSizes(
            self._build_center_splitter_sizes_from_ratio(resolved_ratio)
        )
        return resolved_ratio

    def default_ui_settings(self) -> dict[str, object]:
        return {
            _UI_SETTING_KEY_THEME: self.default_theme(),
            _UI_SETTING_KEY_CENTER_SPLITTER_RATIO: list(self.default_center_splitter_ratio()),
        }

    def current_ui_settings(self) -> dict[str, object]:
        return {
            _UI_SETTING_KEY_THEME: self.current_theme(),
            _UI_SETTING_KEY_CENTER_SPLITTER_RATIO: list(self.current_center_splitter_ratio()),
        }

    def apply_ui_settings(self, settings: Mapping[str, object] | None) -> None:
        resolved_settings = dict(settings or {})
        self.apply_theme(resolved_settings.get(_UI_SETTING_KEY_THEME, self.default_theme()))
        self.apply_center_splitter_ratio(
            resolved_settings.get(
                _UI_SETTING_KEY_CENTER_SPLITTER_RATIO,
                self.default_center_splitter_ratio(),
            )
        )

    def apply_theme(self, theme_name: str) -> None:
        resolved_theme = str(theme_name).strip().lower()
        if resolved_theme not in ThemeStrings.SUPPORTED:
            resolved_theme = self.default_theme()
        self._current_theme = resolved_theme

        QApplication.instance().setProperty("appTheme", resolved_theme)
        for widget in (
            self,
            self.menu_bar,
            self.operation_panel,
            self.morph_upper_limit_row,
            self.left_info_panel,
            self.right_display_container,
            self.center_content_container,
            self.status_panel,
        ):
            widget.setProperty("appTheme", resolved_theme)

        self.wav_waveform_view.set_theme(resolved_theme)
        self.preview_area.set_theme(resolved_theme)
        QApplication.instance().setStyleSheet(
            self._build_qt_theme_stylesheet(resolved_theme)
        )
        self._sync_theme_action_checks()

    def _on_center_splitter_moved(self, _pos: int, _index: int) -> None:
        self._current_center_splitter_ratio = self.current_center_splitter_ratio()

    def _apply_initial_center_splitter_ratio(self) -> None:
        self.apply_center_splitter_ratio(self._current_center_splitter_ratio)

    def _normalize_center_splitter_ratio(
        self,
        ratio: Sequence[int] | None,
    ) -> tuple[int, int]:
        if ratio is None or len(ratio) < 2:
            return self.default_center_splitter_ratio()

        try:
            left_value = int(ratio[0])
            right_value = int(ratio[1])
        except (TypeError, ValueError, IndexError):
            return self.default_center_splitter_ratio()

        if left_value <= 0 or right_value <= 0:
            return self.default_center_splitter_ratio()
        return (left_value, right_value)

    def _build_center_splitter_sizes_from_ratio(
        self,
        ratio: Sequence[int],
    ) -> list[int]:
        resolved_ratio = self._normalize_center_splitter_ratio(ratio)
        total_ratio = resolved_ratio[0] + resolved_ratio[1]
        if total_ratio <= 0:
            return list(self.default_center_splitter_ratio())

        available_width = max(
            self.center_splitter.width(),
            sum(self.center_splitter.sizes()),
            total_ratio,
        )
        left_width = max((available_width * resolved_ratio[0]) // total_ratio, 1)
        right_width = max(available_width - left_width, 1)
        return [left_width, right_width]

    def _build_qt_theme_stylesheet(self, theme_name: str) -> str:
        if theme_name == ThemeStrings.LIGHT:
            colors = {
                "window_bg": "#f4f6f8",
                "panel_bg": "#ffffff",
                "panel_alt_bg": "#f8fafc",
                "surface_bg": "#ffffff",
                "input_bg": "#ffffff",
                "border": "#c9d2dc",
                "border_strong": "#94a3b8",
                "text": "#17212b",
                "text_muted": "#5b6775",
                "accent": "#2563eb",
                "accent_hover": "#1d4ed8",
                "accent_pressed": "#1e40af",
                "menu_hover": "#dbeafe",
                "menu_border": "#cbd5e1",
                "selection_bg": "#bfdbfe",
                "selection_text": "#0f172a",
                "splitter": "#d7dee7",
                "button_disabled_bg": "#e5e7eb",
                "button_disabled_text": "#94a3b8",
                "morph_step_bg": "#eef2f7",
                "morph_step_hover": "#dbeafe",
                "morph_step_pressed": "#bfdbfe",
                "morph_step_border": "#94a3b8",
                "morph_step_text": "#17212b",
                "morph_step_disabled_bg": "#e5e7eb",
                "morph_step_disabled_text": "#94a3b8",
                "ui_font_family": _DEFAULT_UI_FONT_FAMILY,
                "ui_font_size": _DEFAULT_UI_FONT_SIZE_PT,
            }
        else:
            colors = {
                "window_bg": "#1e232a",
                "panel_bg": "#252b34",
                "panel_alt_bg": "#2c3440",
                "surface_bg": "#20262f",
                "input_bg": "#1b2129",
                "border": "#394150",
                "border_strong": "#596274",
                "text": "#e5e7eb",
                "text_muted": "#aeb6c2",
                "accent": "#3b82f6",
                "accent_hover": "#60a5fa",
                "accent_pressed": "#2563eb",
                "menu_hover": "#334155",
                "menu_border": "#475569",
                "selection_bg": "#1d4ed8",
                "selection_text": "#f8fafc",
                "splitter": "#334155",
                "button_disabled_bg": "#303744",
                "button_disabled_text": "#7b8594",
                "morph_step_bg": "#475569",
                "morph_step_hover": "#64748b",
                "morph_step_pressed": "#94a3b8",
                "morph_step_border": "#94a3b8",
                "morph_step_text": "#f8fafc",
                "morph_step_disabled_bg": "#303744",
                "morph_step_disabled_text": "#7b8594",
                "ui_font_family": _DEFAULT_UI_FONT_FAMILY,
                "ui_font_size": _DEFAULT_UI_FONT_SIZE_PT,
            }

        return """
QWidget#MainWindowRoot {{
    background-color: {window_bg};
    color: {text};
    font-family: {ui_font_family};
    font-size: {ui_font_size}pt;
}}
QMenuBar#MainMenuBar {{
    background-color: {panel_bg};
    color: {text};
    border: 1px solid {border};
    font-family: {ui_font_family};
    font-size: {ui_font_size}pt;
}}
QMenuBar#MainMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
}}
QMenuBar#MainMenuBar::item:selected {{
    background-color: {menu_hover};
}}
QMenu {{
    background-color: {panel_bg};
    color: {text};
    border: 1px solid {menu_border};
}}
QMenu::item {{
    padding: 6px 22px 6px 22px;
}}
QMenu::item:selected {{
    background-color: {menu_hover};
}}
QWidget#OperationPanel,
QWidget#OperationGroup,
QWidget#LeftInfoPanel,
QWidget#RightDisplayContainer,
QWidget#MorphUpperLimitRow,
QWidget#CenterContentContainer,
QWidget#InfoSection,
QWidget#DisplaySection,
QWidget#SectionHeader {{
    background-color: {panel_bg};
    color: {text};
}}
QFrame#StatusPanel {{
    background-color: {panel_alt_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
}}
QLabel {{
    color: {text};
    background: transparent;
    font-family: {ui_font_family};
    font-size: {ui_font_size}pt;
}}
QLabel#SectionTitle {{
    color: {text};
    font-weight: 600;
}}
QLabel#StatusStateLabel {{
    color: {text};
    font-weight: 600;
}}
QLabel#StatusMessageLabel {{
    color: {text_muted};
}}
QFrame#SectionDivider {{
    color: {border_strong};
    background-color: {border_strong};
    max-height: 1px;
}}
QScrollBar#RightViewportScrollBar:horizontal {{
    background-color: {surface_bg};
    border: 1px solid {border};
    border-radius: 6px;
    min-height: 18px;
    margin-top: 2px;
}}
QScrollBar#RightViewportScrollBar::handle:horizontal {{
    background-color: {border_strong};
    border-radius: 5px;
    min-width: 28px;
}}
QScrollBar#RightViewportScrollBar::handle:horizontal:hover {{
    background-color: {accent_hover};
}}
QScrollBar#RightViewportScrollBar::handle:horizontal:pressed {{
    background-color: {accent};
}}
QScrollBar#RightViewportScrollBar::add-line:horizontal,
QScrollBar#RightViewportScrollBar::sub-line:horizontal {{
    width: 0px;
    background: transparent;
    border: none;
}}
QScrollBar#RightViewportScrollBar::add-page:horizontal,
QScrollBar#RightViewportScrollBar::sub-page:horizontal {{
    background-color: transparent;
}}
QScrollBar#RightViewportScrollBar:disabled {{
    background-color: {button_disabled_bg};
    border-color: {border};
}}
QScrollBar#RightViewportScrollBar::handle:horizontal:disabled {{
    background-color: {button_disabled_text};
}}
QToolButton#OperationButton {{
    background-color: {surface_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 4px 6px;
    font-family: {ui_font_family};
    font-size: {ui_font_size}pt;
}}
QToolButton#OperationButton:hover {{
    border-color: {accent_hover};
    background-color: {panel_alt_bg};
}}
QToolButton#OperationButton:pressed {{
    border-color: {accent_pressed};
    background-color: {menu_hover};
}}
QToolButton#OperationButton:checked {{
    border-color: {accent};
}}
QToolButton#OperationButton:disabled {{
    background-color: {button_disabled_bg};
    color: {button_disabled_text};
    border-color: {border};
}}
QPlainTextEdit,
QDoubleSpinBox {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    selection-background-color: {selection_bg};
    selection-color: {selection_text};
    font-family: {ui_font_family};
    font-size: {ui_font_size}pt;
}}
QDoubleSpinBox {{
    padding: 4px 6px;
}}
QToolButton#MorphStepButton {{
    background-color: {morph_step_bg};
    color: {morph_step_text};
    border: 1px solid {morph_step_border};
    border-radius: 4px;
    padding: 0px;
    font-family: {ui_font_family};
    font-size: {ui_font_size}pt;
}}
QToolButton#MorphStepButton:hover {{
    background-color: {morph_step_hover};
}}
QToolButton#MorphStepButton:pressed {{
    background-color: {morph_step_pressed};
}}
QToolButton#MorphStepButton:disabled {{
    background-color: {morph_step_disabled_bg};
    color: {morph_step_disabled_text};
    border-color: {border};
}}
QSplitter#CenterSplitter::handle {{
    background-color: {splitter};
    width: 6px;
}}
""".format(**colors)

    def _sync_theme_action_checks(self) -> None:
        current_theme = self.current_theme()
        for action, theme_name in (
            (self.action_theme_dark, ThemeStrings.DARK),
            (self.action_theme_light, ThemeStrings.LIGHT),
        ):
            previous_blocked = action.blockSignals(True)
            action.setChecked(current_theme == theme_name)
            action.blockSignals(previous_blocked)

    def _on_show_30fps_lines_toggled(self, checked: bool) -> None:
        self.wav_waveform_view.set_show_frame_grid(checked)

    def _on_show_vowel_labels_toggled(self, checked: bool) -> None:
        self.wav_waveform_view.set_show_vowel_labels(checked)

    def _on_show_event_ranges_toggled(self, checked: bool) -> None:
        self.wav_waveform_view.set_show_event_regions(checked)

    def _reset_waveform_view_options(self) -> None:
        self.wav_waveform_view.reset_overlay_visibility()
        self._sync_view_action_checks()

    def _resolve_text_dialog_initial_dir(self) -> str:
        return self._resolve_dialog_initial_dir(self.last_text_dialog_dir)

    def _resolve_wav_dialog_initial_dir(self) -> str:
        return self._resolve_dialog_initial_dir(self.last_wav_dialog_dir)

    def _resolve_dialog_initial_dir(self, remembered_dir: str | None) -> str:
        fallback_dir = ""
        if remembered_dir is None:
            return fallback_dir

        normalized_dir = remembered_dir.strip()
        if not normalized_dir:
            return fallback_dir

        try:
            if not os.path.exists(normalized_dir):
                return fallback_dir
            if not os.path.isdir(normalized_dir):
                return fallback_dir
        except OSError:
            return fallback_dir

        return normalized_dir

    def _resolve_counterpart_path(self, primary_path: str | Path) -> Path | None:
        if isinstance(primary_path, str):
            normalized_path = primary_path.strip()
            if not normalized_path:
                return None
            base_path = Path(normalized_path)
        else:
            base_path = Path(primary_path)

        suffix = base_path.suffix.lower()
        if suffix == ".txt":
            return base_path.with_suffix(".wav")
        if suffix == ".wav":
            return base_path.with_suffix(".txt")
        return None

    def _try_autocomplete_counterpart_load(self, primary_path: str | Path) -> None:
        """Try one counterpart load after the primary load has already succeeded."""
        counterpart_path = self._resolve_counterpart_path(primary_path)
        if counterpart_path is None:
            return

        counterpart_suffix = counterpart_path.suffix.lower()
        if counterpart_suffix == ".txt":
            if self.selected_text_path:
                return
        elif counterpart_suffix == ".wav":
            if self.selected_wav_path:
                return
        else:
            return

        try:
            if not counterpart_path.exists() or counterpart_path.is_dir():
                return
        except OSError:
            return

        if counterpart_suffix == ".txt":
            if self._load_text_file(str(counterpart_path), suppress_warning=True):
                self.last_text_dialog_dir = str(counterpart_path.parent)
            return
        if counterpart_suffix == ".wav":
            if self._load_wav_file(str(counterpart_path), suppress_warning=True):
                self.last_wav_dialog_dir = str(counterpart_path.parent)

    def _select_text_file(self) -> None:
        initial_dir = self._resolve_text_dialog_initial_dir()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e",
            initial_dir,
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return
        if self._load_text_file(file_path):
            self.last_text_dialog_dir = str(Path(file_path).parent)
            self._try_autocomplete_counterpart_load(file_path)

    def _reset_text_analysis_state(self) -> None:
        self._invalidate_current_timing_plan()
        self.wav_waveform_view.clear_morph_labels()

    def _show_text_conversion_failed_previews(self) -> None:
        self.selected_hiragana_content = ""
        self.selected_vowel_content = ""
        self.hiragana_preview.setPlainText("(\u3072\u3089\u304c\u306a\u5909\u63db\u306b\u5931\u6557\u3057\u307e\u3057\u305f)")
        self.vowel_preview.setPlainText("(\u6bcd\u97f3\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")

    def _load_text_file(self, file_path: str, *, suppress_warning: bool = False) -> bool:
        def _fail_text_load(*, title: str, message: str, status: str) -> bool:
            if suppress_warning:
                self._stop_playback_for_timing_invalidation()
                self._update_preview_from_current_timing_plan()
                self._update_action_states()
                return False
            self._reset_text_analysis_state()
            self._show_warning(
                title=title,
                message=message,
                status=status,
            )
            return False

        normalized_path = file_path.strip()
        if not normalized_path:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="TEXT\u30d5\u30a1\u30a4\u30eb\u306e\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )

        text_path = Path(normalized_path)
        try:
            if not text_path.exists():
                return _fail_text_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="TEXT\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
                    status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
                )
            if text_path.is_dir():
                return _fail_text_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="TEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u304f\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
                    status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
                )
        except OSError as error:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"TEXT\u30d5\u30a1\u30a4\u30eb\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )

        try:
            text_content = text_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="UTF-8\u306eTEXT\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u3044\u53ef\u80fd\u6027\u304c\u3042\u308a\u307e\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )
        except OSError as error:
            return _fail_text_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"TEXT\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )

        previous_text_state = None
        previous_zoom_and_viewport_state = None
        if suppress_warning:
            previous_text_state = {
                "selected_text_path": self.selected_text_path,
                "selected_text_content": self.selected_text_content,
                "selected_hiragana_content": self.selected_hiragana_content,
                "selected_vowel_content": self.selected_vowel_content,
                "current_timing_plan": self.current_timing_plan,
                "text_preview": self.text_preview.toPlainText(),
                "hiragana_preview": self.hiragana_preview.toPlainText(),
                "vowel_preview": self.vowel_preview.toPlainText(),
            }
            previous_zoom_and_viewport_state = self._snapshot_zoom_and_viewport_state()

        def _restore_text_state_on_silent_failure() -> bool:
            if previous_text_state is None:
                self._invalidate_current_timing_plan()
                return False
            self.selected_text_path = previous_text_state["selected_text_path"]
            self.selected_text_content = previous_text_state["selected_text_content"]
            self.selected_hiragana_content = previous_text_state["selected_hiragana_content"]
            self.selected_vowel_content = previous_text_state["selected_vowel_content"]
            self.current_timing_plan = previous_text_state["current_timing_plan"]
            self._set_file_path_label(self.text_path_label, "TEXT", self.selected_text_path)
            self.text_preview.setPlainText(previous_text_state["text_preview"])
            self.hiragana_preview.setPlainText(previous_text_state["hiragana_preview"])
            self.vowel_preview.setPlainText(previous_text_state["vowel_preview"])
            self._restore_zoom_and_viewport_state_from_snapshot(previous_zoom_and_viewport_state)
            self._update_preview_from_current_timing_plan()
            self._set_ready_status()
            return True

        if not text_content:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self.selected_hiragana_content = ""
            self.selected_vowel_content = ""
            self.hiragana_preview.setPlainText("(\u3072\u3089\u304c\u306a\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")
            self.vowel_preview.setPlainText("(\u6bcd\u97f3\u5909\u63db\u306f\u672a\u5b9f\u884c\u3067\u3059)")
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message="TEXT\u30d5\u30a1\u30a4\u30eb\u304c\u7a7a\u3067\u3059\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return False

        self.selected_text_path = normalized_path
        self.selected_text_content = text_content
        self._invalidate_current_timing_plan()
        self._set_file_path_label(self.text_path_label, "TEXT", self.selected_text_path)
        try:
            self._refresh_text_processing_views()
        except TextProcessingError as error:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self._show_text_conversion_failed_previews()
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message=f"TEXT\u3092\u304b\u306a/\u3072\u3089\u304c\u306a\u306b\u5909\u63db\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return False
        except Exception as error:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self._show_text_conversion_failed_previews()
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"TEXT\u8aad\u307f\u8fbc\u307f\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u8aad\u8fbc\u5931\u6557",
            )
            return False

        if not self.selected_vowel_content:
            if suppress_warning:
                _restore_text_state_on_silent_failure()
                return False
            self._reset_text_analysis_state()
            self._show_warning(
                title="TEXT\u5909\u63db\u30a8\u30e9\u30fc",
                message="\u6bcd\u97f3\u3092\u62bd\u51fa\u3067\u304d\u308b\u6587\u5b57\u304c\u3042\u308a\u307e\u305b\u3093\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return False

        self.wav_waveform_view.clear_morph_labels()
        self._set_ready_status()
        self._add_recent_text_file(normalized_path)
        return True

    def _select_wav_file(self) -> None:
        initial_dir = self._resolve_wav_dialog_initial_dir()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "WAV\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e",
            initial_dir,
            "WAV Files (*.wav);;All Files (*)",
        )
        if not file_path:
            return
        if self._load_wav_file(file_path):
            self.last_wav_dialog_dir = str(Path(file_path).parent)
            self._try_autocomplete_counterpart_load(file_path)

    def _reset_wav_load_state(self, placeholder_message: str = "Waveform preview (load failed)") -> None:
        self.selected_wav_path = None
        self.selected_wav_analysis = None
        self._invalidate_current_timing_plan()
        self._set_file_path_label(self.wav_path_label, "WAV", None)
        self.wav_info_label.setText(MainWindowStrings.WAV_INFO_NOT_LOADED)
        self.wav_waveform_view.clear_morph_labels()
        self.wav_waveform_view.show_placeholder(placeholder_message)
        self.preview_area.set_timeline_duration_sec(0.0)

    def _validate_wav_load_result(self, wav_info: WavAnalysisResult, waveform_preview) -> str | None:
        if wav_info.sample_rate_hz <= 0:
            return "WAV\u306e\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u5468\u6ce2\u6570\u304c\u7121\u52b9\u3067\u3059\u3002"
        if wav_info.frame_count < 0:
            return "WAV\u306e\u30d5\u30ec\u30fc\u30e0\u6570\u304c\u7121\u52b9\u3067\u3059\u3002"
        if wav_info.duration_sec < 0.0:
            return "WAV\u306e\u518d\u751f\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
        if wav_info.has_speech:
            if wav_info.speech_start_sec < 0.0:
                return "WAV\u306e\u767a\u8a71\u958b\u59cb\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
            if wav_info.speech_end_sec <= wav_info.speech_start_sec:
                return "WAV\u306e\u767a\u8a71\u533a\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
            if wav_info.speech_end_sec > (wav_info.duration_sec + 1e-9):
                return "WAV\u306e\u767a\u8a71\u7d42\u4e86\u6642\u9593\u304c\u518d\u751f\u6642\u9593\u3092\u8d85\u3048\u3066\u3044\u307e\u3059\u3002"
        if waveform_preview.duration_sec < 0.0:
            return "WAV\u6ce2\u5f62\u306e\u518d\u751f\u6642\u9593\u304c\u7121\u52b9\u3067\u3059\u3002"
        if waveform_preview.duration_sec > 0.0 and not waveform_preview.samples:
            return "WAV\u6ce2\u5f62\u306e\u8868\u793a\u30c7\u30fc\u30bf\u304c\u53d6\u5f97\u3067\u304d\u307e\u305b\u3093\u3002"
        return None

    def _load_wav_file(self, file_path: str, *, suppress_warning: bool = False) -> bool:
        def _fail_wav_load(*, title: str, message: str, status: str) -> bool:
            if suppress_warning:
                self._stop_playback_for_timing_invalidation()
                self._update_preview_from_current_timing_plan()
                self._update_action_states()
                return False
            self._reset_wav_load_state()
            self._show_warning(
                title=title,
                message=message,
                status=status,
            )
            return False

        normalized_path = file_path.strip()
        if not normalized_path:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message="WAV\u30d5\u30a1\u30a4\u30eb\u306e\u30d1\u30b9\u304c\u7a7a\u3067\u3059\u3002",
                status=StatusTexts.WAV_LOAD_FAILURE,
            )

        wav_path = Path(normalized_path)
        try:
            if not wav_path.exists():
                return _fail_wav_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="WAV\u30d5\u30a1\u30a4\u30eb\u304c\u5b58\u5728\u3057\u307e\u305b\u3093\u3002",
                    status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
                )
            if wav_path.is_dir():
                return _fail_wav_load(
                    title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                    message="WAV\u30d5\u30a1\u30a4\u30eb\u3067\u306f\u306a\u304f\u30d5\u30a9\u30eb\u30c0\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u3059\u3002",
                    status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
                )
        except OSError as error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u30d5\u30a1\u30a4\u30eb\u306e\u78ba\u8a8d\u4e2d\u306b\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        try:
            wav_info = analyze_wav_file(normalized_path)
        except (ValueError, OSError, EOFError) as error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u30d5\u30a1\u30a4\u30eb\u3092\u89e3\u6790\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )
        except Exception as error:
            return _fail_wav_load(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"WAV\u89e3\u6790\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        try:
            waveform_preview = load_waveform_preview(
                normalized_path,
                max_points=3000,
                stereo_mode="average",
            )
        except (ValueError, OSError, EOFError) as error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u6ce2\u5f62\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )
        except Exception as error:
            return _fail_wav_load(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"WAV\u6ce2\u5f62\u53d6\u5f97\u4e2d\u306b\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        wav_load_error = self._validate_wav_load_result(wav_info, waveform_preview)
        if wav_load_error:
            return _fail_wav_load(
                title="\u8aad\u307f\u8fbc\u307f\u30a8\u30e9\u30fc",
                message=f"WAV\u60c5\u5831\u304c\u7121\u52b9\u3067\u3059: {wav_load_error}",
                status="\u51fa\u529b\u72b6\u614b: WAV\u8aad\u8fbc\u5931\u6557",
            )

        self.selected_wav_path = normalized_path
        self.selected_wav_analysis = wav_info
        self.playback_controller.set_wav_path(normalized_path)
        self._invalidate_current_timing_plan()
        self.preview_area.set_timeline_duration_sec(wav_info.duration_sec)
        self._set_file_path_label(self.wav_path_label, "WAV", self.selected_wav_path)
        self.wav_info_label.setText(
            MainWindowStrings.WAV_INFO_TEMPLATE.format(
                file_name=wav_path.name,
                duration_sec=wav_info.duration_sec,
                sample_rate_hz=wav_info.sample_rate_hz,
                speech_start_sec=wav_info.speech_start_sec,
                speech_end_sec=wav_info.speech_end_sec,
            )
        )
        self.wav_waveform_view.plot_waveform(
            waveform_preview.samples,
            waveform_preview.duration_sec,
        )
        self.wav_waveform_view.clear_morph_labels()
        self._set_ready_status()
        self._add_recent_wav_file(normalized_path)
        return True

    def _open_recent_text_file(self, file_path: str) -> None:
        try:
            recent_path_error = self._validate_recent_file_path(
                file_path=file_path,
                expected_suffix=".txt",
            )
            if recent_path_error:
                self._remove_recent_text_file(file_path)
                self._show_warning(
                    title="読み込みエラー",
                    message=f"最近使ったTEXTを開けません: {recent_path_error}",
                    status=StatusTexts.TEXT_LOAD_FAILURE,
                )
                return
            if self._load_text_file(file_path):
                self.last_text_dialog_dir = str(Path(file_path).parent)
                self._try_autocomplete_counterpart_load(file_path)
                return
            self._remove_recent_text_file(file_path)
            return
        except Exception as error:
            self._remove_recent_text_file(file_path)
            self._reset_text_analysis_state()
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"最近使ったTEXTの読み込み中に予期しないエラーが発生しました: {error}",
                status=StatusTexts.TEXT_LOAD_FAILURE,
            )

    def _open_recent_wav_file(self, file_path: str) -> None:
        try:
            recent_path_error = self._validate_recent_file_path(
                file_path=file_path,
                expected_suffix=".wav",
            )
            if recent_path_error:
                self._remove_recent_wav_file(file_path)
                self._show_warning(
                    title="読み込みエラー",
                    message=f"最近使ったWAVを開けません: {recent_path_error}",
                    status=StatusTexts.WAV_LOAD_FAILURE,
                )
                return
            if self._load_wav_file(file_path):
                self.last_wav_dialog_dir = str(Path(file_path).parent)
                self._try_autocomplete_counterpart_load(file_path)
                return
            self._remove_recent_wav_file(file_path)
            return
        except Exception as error:
            self._remove_recent_wav_file(file_path)
            self._reset_wav_load_state()
            self._show_warning(
                title="\u4e88\u671f\u3057\u306a\u3044\u30a8\u30e9\u30fc",
                message=f"最近使ったWAVの読み込み中に予期しないエラーが発生しました: {error}",
                status=StatusTexts.WAV_LOAD_FAILURE,
            )

    def _add_recent_text_file(self, file_path: str) -> None:
        self._remember_recent_file(self.recent_text_files, file_path)
        self._refresh_recent_text_menu()

    def _add_recent_wav_file(self, file_path: str) -> None:
        self._remember_recent_file(self.recent_wav_files, file_path)
        self._refresh_recent_wav_menu()

    def _remove_recent_text_file(self, file_path: str) -> None:
        if self._remove_recent_file(self.recent_text_files, file_path):
            self._refresh_recent_text_menu()

    def _remove_recent_wav_file(self, file_path: str) -> None:
        if self._remove_recent_file(self.recent_wav_files, file_path):
            self._refresh_recent_wav_menu()

    def _remember_recent_file(self, recent_files: list[str], file_path: str) -> None:
        normalized_target = self._normalize_recent_path(file_path)
        recent_files[:] = [
            existing_path
            for existing_path in recent_files
            if self._normalize_recent_path(existing_path) != normalized_target
        ]
        recent_files.insert(0, file_path)
        if len(recent_files) > self._recent_file_limit:
            del recent_files[self._recent_file_limit :]

    def _remove_recent_file(self, recent_files: list[str], file_path: str) -> bool:
        normalized_target = self._normalize_recent_path(file_path)
        original_size = len(recent_files)
        recent_files[:] = [
            existing_path
            for existing_path in recent_files
            if self._normalize_recent_path(existing_path) != normalized_target
        ]
        return len(recent_files) != original_size

    def _normalize_recent_path(self, file_path: str) -> str:
        return os.path.normcase(os.path.normpath(file_path))

    def _validate_recent_file_path(
        self,
        *,
        file_path: str,
        expected_suffix: str,
    ) -> str | None:
        normalized_path = file_path.strip()
        if not normalized_path:
            return "履歴パスが空です。"

        path = Path(normalized_path)
        try:
            if not path.exists():
                return "ファイルが存在しません。"
            if path.is_dir():
                return "フォルダが指定されています。"
        except OSError as error:
            return f"ファイル確認中にエラーが発生しました: {error}"

        if path.suffix.lower() != expected_suffix:
            return f"{expected_suffix} ファイルではありません。"

        return None

    def _refresh_recent_file_menus(self) -> None:
        self._refresh_recent_text_menu()
        self._refresh_recent_wav_menu()

    def _refresh_recent_text_menu(self) -> None:
        self._refresh_recent_menu(
            menu=self.menu_recent_text,
            recent_files=self.recent_text_files,
            on_selected=self._open_recent_text_file,
        )

    def _refresh_recent_wav_menu(self) -> None:
        self._refresh_recent_menu(
            menu=self.menu_recent_wav,
            recent_files=self.recent_wav_files,
            on_selected=self._open_recent_wav_file,
        )

    def _refresh_recent_menu(
        self,
        menu,
        recent_files: list[str],
        on_selected,
    ) -> None:
        menu.clear()
        if not recent_files:
            empty_action = QAction("(\u5c65\u6b74\u306a\u3057)", self)
            empty_action.setEnabled(False)
            menu.addAction(empty_action)
            menu.setEnabled(False)
            return
        menu.setEnabled(True)
        for recent_path in recent_files:
            action = QAction(recent_path, self)
            action.triggered.connect(
                lambda _checked=False, selected_path=recent_path: on_selected(selected_path)
            )
            menu.addAction(action)

    def _resolve_vmd_output_path(self, raw_output_path: str) -> Path | None:
        normalized_output_path = raw_output_path.strip()
        if not normalized_output_path:
            self._show_warning(
                title="出力エラー",
                message="VMDの保存先パスが空です。",
                status=StatusTexts.FAILURE,
            )
            return None

        out_path = Path(normalized_output_path)
        try:
            if out_path.suffix.lower() != ".vmd":
                out_path = out_path.with_suffix(".vmd")
        except ValueError:
            self._show_warning(
                title="出力エラー",
                message="VMDの保存先パスが不正です。",
                status=StatusTexts.FAILURE,
            )
            return None

        final_output_path = str(out_path).strip()
        if not final_output_path:
            self._show_warning(
                title="出力エラー",
                message="VMDの保存先パスが不正です。",
                status=StatusTexts.FAILURE,
            )
            return None

        out_path = Path(final_output_path)
        try:
            if out_path.exists() and out_path.is_dir():
                self._show_warning(
                    title="出力エラー",
                    message="保存先にフォルダが指定されています。ファイル名を指定してください。",
                    status=StatusTexts.FAILURE,
                )
                return None

            parent_dir = out_path.parent
            if not str(parent_dir).strip():
                self._show_warning(
                    title="出力エラー",
                    message="保存先フォルダが不正です。",
                    status=StatusTexts.FAILURE,
                )
                return None
            if parent_dir.exists() and not parent_dir.is_dir():
                self._show_warning(
                    title="出力エラー",
                    message="保存先フォルダが不正です。",
                    status=StatusTexts.FAILURE,
                )
                return None
        except OSError as error:
            self._show_warning(
                title="出力エラー",
                message=f"保存先の確認中にエラーが発生しました: {error}",
                status=StatusTexts.FAILURE,
            )
            return None

        return out_path

    def _export_vmd(self) -> None:
        if self.selected_text_path and self.selected_wav_path and not self.selected_vowel_content:
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u304b\u3089\u6709\u52b9\u306a\u3072\u3089\u304c\u306a/\u6bcd\u97f3\u5217\u3092\u751f\u6210\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002TEXT\u3092\u898b\u76f4\u3057\u3066\u518d\u8aad\u307f\u8fbc\u307f\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return

        if not self._has_required_inputs():
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u3068WAV\u306e\u4e21\u65b9\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u5165\u529b\u4e0d\u8db3",
            )
            return

        if self.current_timing_plan is None:
            self._show_warning(
                title="\u672a\u89e3\u6790",
                message="\u51e6\u7406\u5b9f\u884c\u30dc\u30bf\u30f3\u3067\u89e3\u6790\u3057\u3066\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u89e3\u6790\u672a\u5b9f\u884c",
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "VMD\u30d5\u30a1\u30a4\u30eb\u306e\u4fdd\u5b58\u5148\u3092\u9078\u629e",
            "",
            "VMD Files (*.vmd);;All Files (*)",
        )
        if not output_path:
            self._set_output_status("\u51fa\u529b\u72b6\u614b: \u30ad\u30e3\u30f3\u30bb\u30eb")
            return

        out_path = self._resolve_vmd_output_path(output_path)
        if out_path is None:
            return

        try:
            timing_plan = self._ensure_timing_plan()
            result = generate_vmd_from_text_wav(
                text_path=self.selected_text_path,
                wav_path=self.selected_wav_path,
                output_path=out_path,
                timing_plan=timing_plan,
                upper_limit=self._current_upper_limit(),
            )
            self.current_timing_plan = timing_plan
        except ValueError as error:
            self._show_warning(
                title="\u51fa\u529b\u30a8\u30e9\u30fc",
                message=f"\u6bcd\u97f3\u30bf\u30a4\u30df\u30f3\u30b0\u3092\u6c7a\u5b9a\u3067\u304d\u307e\u305b\u3093: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return
        except PipelineError as error:
            self._show_warning(
                title="\u51fa\u529b\u30a8\u30e9\u30fc",
                message=f"VMD\u306e\u51fa\u529b\u306b\u5931\u6557\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return
        except OSError as error:
            self._show_warning(
                title="\u51fa\u529b\u30a8\u30e9\u30fc",
                message=f"VMD\u4fdd\u5b58\u6642\u306b\u30d5\u30a1\u30a4\u30eb\u30a8\u30e9\u30fc\u304c\u767a\u751f\u3057\u307e\u3057\u305f: {error}",
                status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
            )
            return
        except Exception as error:
            self._show_warning(
                title=MainWindowStrings.UNEXPECTED_ERROR_TITLE,
                message=MainWindowStrings.UNEXPECTED_ERROR_MESSAGE.format(error=error),
                status=StatusTexts.FAILURE,
            )
            return

        QMessageBox.information(
            self,
            MainWindowStrings.OUTPUT_COMPLETE_TITLE,
            MainWindowStrings.OUTPUT_COMPLETE_MESSAGE.format(output_path=result.output_path),
        )
        timing_label = MainWindowStrings.TIMING_LABEL_OUTPUT_WHISPER
        if not result.timing_source.startswith("whisper_"):
            timing_label = MainWindowStrings.TIMING_LABEL_FALLBACK

        self._set_output_status(
            StatusTexts.SUCCESS_TEMPLATE.format(
                output_name=result.output_path.name,
                timing_label=timing_label,
            )
        )

    def _run_processing(self) -> None:
        if self._is_processing:
            return
        if not self.selected_text_content:
            self._invalidate_current_timing_plan()
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51e6\u7406\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u5165\u529b\u4e0d\u8db3",
            )
            return
        if not self.selected_wav_analysis or not self.selected_wav_path:
            self._invalidate_current_timing_plan()
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="WAV\u3092\u8aad\u307f\u8fbc\u3093\u3067\u304b\u3089\u51e6\u7406\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                status="\u51fa\u529b\u72b6\u614b: \u5165\u529b\u4e0d\u8db3",
            )
            return
        if not self.selected_vowel_content:
            self._invalidate_current_timing_plan()
            self._show_warning(
                title="\u5165\u529b\u4e0d\u8db3",
                message="TEXT\u304b\u3089\u6709\u52b9\u306a\u3072\u3089\u304c\u306a/\u6bcd\u97f3\u5217\u3092\u751f\u6210\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002",
                status="\u51fa\u529b\u72b6\u614b: TEXT\u5909\u63db\u5931\u6557",
            )
            return

        self._begin_processing_session()
        try:
            self._refresh_waveform_morph_labels()
            if self.current_timing_plan is None:
                self._show_warning(
                    title="\u51e6\u7406\u30a8\u30e9\u30fc",
                    message="\u97f3\u58f0\u51e6\u7406\u306b\u5931\u6557\u3057\u307e\u3057\u305f\u3002",
                    status="\u51fa\u529b\u72b6\u614b: \u5931\u6557",
                )
                return
            self._set_ready_status()
        finally:
            self._end_processing_session()

    def _has_required_inputs(self) -> bool:
        return bool(self.selected_text_path and self.selected_wav_path)

    def _set_output_status(self, text: str) -> None:
        if self.status_panel.status_text() == text:
            return
        self.status_panel.set_status_text(text)

    def _clear_preview_display(self) -> None:
        preview_area = getattr(self, "preview_area", None)
        if preview_area is None:
            return
        preview_area.clear_preview()

    def _invalidate_current_timing_plan(self) -> None:
        self.current_timing_plan = None
        self._stop_playback_for_timing_invalidation()
        self._reset_zoom_and_viewport_state()
        self._update_preview_from_current_timing_plan()
        self._update_action_states()

    def _update_preview_from_current_timing_plan(self) -> None:
        preview_area = getattr(self, "preview_area", None)
        if preview_area is None:
            return
        if self.current_timing_plan is None:
            self._clear_preview_display()
            return
        preview_data = build_preview_data(self.current_timing_plan.timeline)
        preview_area.set_preview_data(preview_data)

    def _refresh_text_processing_views(self) -> None:
        self.text_preview.setPlainText(self.selected_text_content)

        self.selected_hiragana_content = text_to_hiragana(self.selected_text_content)
        self.hiragana_preview.setPlainText(self.selected_hiragana_content)

        self.selected_vowel_content = hiragana_to_vowel_string(self.selected_hiragana_content)
        if self.selected_vowel_content:
            self.vowel_preview.setPlainText(self.selected_vowel_content)
        else:
            self.vowel_preview.setPlainText("(\u6bcd\u97f3\u306e\u62bd\u51fa\u7d50\u679c\u306f\u3042\u308a\u307e\u305b\u3093)")

    def _refresh_waveform_morph_labels(self) -> None:
        if (
            not self.selected_wav_analysis
            or not self.selected_text_content
            or not self.selected_wav_path
        ):
            self._invalidate_current_timing_plan()
            self.wav_waveform_view.clear_morph_labels()
            return

        if not self.selected_wav_analysis.has_speech:
            self._invalidate_current_timing_plan()
            self.wav_waveform_view.clear_morph_labels()
            return

        try:
            timing_plan = build_vowel_timing_plan(
                text_content=self.selected_text_content,
                wav_path=self.selected_wav_path,
                wav_analysis=self.selected_wav_analysis,
                whisper_model_name="small",
                upper_limit=self._current_upper_limit(),
            )
        except ValueError:
            self._invalidate_current_timing_plan()
            self.wav_waveform_view.clear_morph_labels()
            return

        self.current_timing_plan = timing_plan
        self.wav_waveform_view.set_morph_events(timing_plan.timeline)
        self._update_preview_from_current_timing_plan()

    def _show_warning(self, title: str, message: str, status: str | None = None) -> None:
        QMessageBox.warning(self, title, message)
        if status:
            self._set_output_status(status)
        self._update_action_states()

    def _ensure_timing_plan(self) -> VowelTimingPlan:
        if self.current_timing_plan is not None:
            return self.current_timing_plan
        if not self.selected_text_content:
            raise ValueError("TEXT \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002")
        if not self.selected_wav_analysis or not self.selected_wav_path:
            raise ValueError("WAV \u304c\u307e\u3060\u6e96\u5099\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002")
        raise ValueError(
            "\u89e3\u6790\u304c\u307e\u3060\u5b9f\u884c\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002"
            "\u300c\u51e6\u7406\u5b9f\u884c\u300d\u3092\u62bc\u3057\u3066\u304b\u3089\u51fa\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002"
        )

    def _on_morph_upper_limit_changed(self, _: float) -> None:
        self._invalidate_current_timing_plan()
        self.wav_waveform_view.clear_morph_labels()
        self._set_ready_status()

    def _current_upper_limit(self) -> float:
        return float(self.morph_upper_limit_input.value())

    def _set_ready_status(self) -> None:
        text_loaded = bool(self.selected_text_path)
        wav_loaded = bool(self.selected_wav_path and self.selected_wav_analysis is not None)
        self._update_action_states()

        if text_loaded and wav_loaded and not self.current_timing_plan:
            self._set_output_status(StatusTexts.READY_ANALYSIS_PENDING)
            return
        if text_loaded and not wav_loaded:
            self._set_output_status(StatusTexts.READY_TEXT_ONLY)
            return
        if wav_loaded and not text_loaded:
            self._set_output_status(StatusTexts.READY_WAV_ONLY)
            return
        if not self.current_timing_plan:
            self._set_output_status(StatusTexts.READY_NOT_LOADED)
            return

        timing_source = self.current_timing_plan.source
        if timing_source.startswith("whisper_"):
            timing_label = MainWindowStrings.TIMING_LABEL_READY_WHISPER
        else:
            timing_label = MainWindowStrings.TIMING_LABEL_FALLBACK
        self._set_output_status(
            f"\u51fa\u529b\u72b6\u614b: \u89e3\u6790\u5b9f\u884c\u6e08\u307f ({timing_label} / \u533a\u9593={len(self.current_timing_plan.anchors)} / \u6bcd\u97f3={len(self.current_timing_plan.timeline)})"
        )

    def _update_action_states(self) -> None:
        action_states = self._build_normal_action_states()
        action_states = self._apply_processing_lock_overrides(action_states)
        self._apply_action_states(action_states)

    def _build_normal_action_states(self) -> dict[str, bool]:
        has_text = bool(self.selected_text_content and self.selected_vowel_content)
        has_wav = bool(self.selected_wav_path and self.selected_wav_analysis is not None)
        has_valid_analysis = self.current_timing_plan is not None
        has_recent_text = bool(self.recent_text_files)
        has_recent_wav = bool(self.recent_wav_files)
        is_playing = self.playback_controller.is_playing()
        playback_source_path = self.playback_controller.source_path()
        has_playback_source = (
            playback_source_path is not None
            and self.selected_wav_path is not None
            and str(playback_source_path) == self.selected_wav_path
        )
        can_run = has_text and has_wav
        can_save = can_run and self.current_timing_plan is not None
        zoom_level_count = len(self._zoom_levels)
        can_zoom_in = (
            has_wav
            and zoom_level_count > 0
            and self._zoom_level_index < (zoom_level_count - 1)
        )
        can_zoom_out = has_wav and self._zoom_level_index > 0
        can_play = (
            (not self._is_processing)
            and has_valid_analysis
            and has_wav
            and has_playback_source
            and self.playback_controller.is_ready()
            and (not is_playing)
        )
        can_stop = (not self._is_processing) and is_playing

        return {
            "can_open_text": True,
            "can_open_wav": True,
            "can_open_recent_text": has_recent_text,
            "can_open_recent_wav": has_recent_wav,
            "can_adjust_morph_upper_limit": True,
            "can_run": can_run,
            "can_save": can_save,
            "can_play": can_play,
            "can_stop": can_stop,
            "can_zoom_in": can_zoom_in,
            "can_zoom_out": can_zoom_out,
        }

    def _apply_processing_lock_overrides(self, action_states: dict[str, bool]) -> dict[str, bool]:
        if not self._is_processing:
            return action_states
        locked_states = action_states.copy()
        locked_states["can_open_text"] = False
        locked_states["can_open_wav"] = False
        locked_states["can_open_recent_text"] = False
        locked_states["can_open_recent_wav"] = False
        locked_states["can_adjust_morph_upper_limit"] = False
        locked_states["can_run"] = False
        locked_states["can_save"] = False
        locked_states["can_play"] = False
        locked_states["can_stop"] = False
        locked_states["can_zoom_in"] = False
        locked_states["can_zoom_out"] = False
        return locked_states

    def _apply_action_states(self, action_states: dict[str, bool]) -> None:
        can_open_text = action_states["can_open_text"]
        can_open_wav = action_states["can_open_wav"]
        can_open_recent_text = action_states["can_open_recent_text"]
        can_open_recent_wav = action_states["can_open_recent_wav"]
        can_adjust_morph_upper_limit = action_states["can_adjust_morph_upper_limit"]
        can_run = action_states["can_run"]
        can_save = action_states["can_save"]
        can_play = action_states["can_play"]
        can_stop = action_states["can_stop"]
        can_zoom_in = action_states["can_zoom_in"]
        can_zoom_out = action_states["can_zoom_out"]

        self.operation_panel.set_button_enabled_states(
            {
                "text": can_open_text,
                "wav": can_open_wav,
                "run": can_run,
                "save": can_save,
                "play": can_play,
                "stop": can_stop,
                "zoom_in": can_zoom_in,
                "zoom_out": can_zoom_out,
            }
        )

        self.action_open_text.setEnabled(can_open_text)
        self.action_open_wav.setEnabled(can_open_wav)
        self.menu_recent_text.setEnabled(can_open_recent_text)
        self.menu_recent_wav.setEnabled(can_open_recent_wav)
        for action in self.menu_recent_text.actions():
            action.setEnabled(can_open_recent_text)
        for action in self.menu_recent_wav.actions():
            action.setEnabled(can_open_recent_wav)
        self.morph_upper_limit_input.setEnabled(can_adjust_morph_upper_limit)

        self.action_zoom_in.setEnabled(can_zoom_in)
        self.action_zoom_out.setEnabled(can_zoom_out)
        self.action_run_processing.setEnabled(can_run)
        self.action_reanalyze.setEnabled(can_run)
        self.action_save_vmd.setEnabled(can_save)
