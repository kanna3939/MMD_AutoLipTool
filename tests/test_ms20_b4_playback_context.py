from unittest.mock import patch

import pytest
import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.playback_context import (
    PlaybackInfoContext,
    build_playback_info_context,
    format_playback_info_context,
)
from gui_wx.right_pane import RightPane
from gui_wx.theme import ThemeManager, ThemeMode
from src.core import VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _point(
    vowel: str,
    *,
    time_sec: float,
    start_sec: float,
    end_sec: float,
) -> VowelTimelinePoint:
    return VowelTimelinePoint(
        time_sec=time_sec,
        vowel=vowel,
        start_sec=start_sec,
        end_sec=end_sec,
    )


def _context(
    position_sec: object,
    timeline=(),
    *,
    is_playing: bool = True,
    analysis_result_valid: bool = True,
    analysis_pending_rebuild: bool = False,
) -> PlaybackInfoContext:
    return build_playback_info_context(
        is_playing=is_playing,
        position_sec=position_sec,
        timeline=timeline,
        analysis_result_valid=analysis_result_valid,
        analysis_pending_rebuild=analysis_pending_rebuild,
    )


def test_stopped_context_forces_default_values():
    context = _context(
        1.23,
        [_point("あ", time_sec=1.2, start_sec=1.0, end_sec=1.4)],
        is_playing=False,
    )

    assert context == PlaybackInfoContext(False, 0.0, 0, None)


def test_playing_context_uses_vmd_rounding_and_fixed_format():
    context = _context(1.23, analysis_result_valid=False)

    assert context.position_sec == 1.23
    assert context.frame_no == 37
    assert context.current_vowel is None
    assert format_playback_info_context(context) == (
        "[再生]\n"
        "再生位置: 1.23 秒\n"
        "現在フレーム: 37\n"
        "現在母音: (なし)"
    )


@pytest.mark.parametrize("position", [float("nan"), float("inf"), float("-inf"), "bad"])
def test_invalid_position_does_not_reuse_zero_second_event(position):
    context = _context(
        position,
        [_point("あ", time_sec=0.0, start_sec=0.0, end_sec=0.0)],
    )

    assert context.position_sec == 0.0
    assert context.frame_no == 0
    assert context.current_vowel is None


def test_negative_position_is_clamped_without_failing():
    context = _context(-0.5, analysis_result_valid=False)

    assert context.position_sec == 0.0
    assert context.frame_no == 0


@pytest.mark.parametrize(
    ("position_sec", "expected_frame"),
    [(0.0, 0), (1.0 / 30.0, 1), (0.5 / 30.0, 0), (1.5 / 30.0, 2)],
)
def test_frame_conversion_uses_python_round(position_sec, expected_frame):
    assert _context(position_sec, analysis_result_valid=False).frame_no == expected_frame


def test_half_open_intervals_choose_next_event_at_shared_boundary():
    timeline = [
        _point("あ", time_sec=0.25, start_sec=0.0, end_sec=0.5),
        _point("い", time_sec=0.75, start_sec=0.5, end_sec=1.0),
    ]

    assert _context(0.0, timeline).current_vowel == "あ"
    assert _context(0.5, timeline).current_vowel == "い"
    assert _context(1.0, timeline).current_vowel is None


def test_gap_and_timeline_outside_have_no_current_vowel():
    timeline = [
        _point("あ", time_sec=0.2, start_sec=0.1, end_sec=0.3),
        _point("い", time_sec=0.8, start_sec=0.7, end_sec=0.9),
    ]

    assert _context(0.0, timeline).current_vowel is None
    assert _context(0.5, timeline).current_vowel is None
    assert _context(1.0, timeline).current_vowel is None


def test_overlap_uses_nearest_peak_then_later_peak_and_index():
    overlap = [
        _point("あ", time_sec=0.25, start_sec=0.0, end_sec=1.0),
        _point("い", time_sec=0.75, start_sec=0.0, end_sec=1.0),
    ]
    same_peak = [
        _point("う", time_sec=0.5, start_sec=0.0, end_sec=1.0),
        _point("え", time_sec=0.5, start_sec=0.0, end_sec=1.0),
    ]

    assert _context(0.3, overlap).current_vowel == "あ"
    assert _context(0.5, overlap).current_vowel == "い"
    assert _context(0.5, same_peak).current_vowel == "え"


def test_zero_duration_event_is_active_only_in_same_vmd_frame():
    timeline = [_point("お", time_sec=0.5, start_sec=0.5, end_sec=0.5)]

    assert _context(0.49, timeline).current_vowel == "お"
    assert _context(0.55, timeline).current_vowel is None


def test_invalid_plan_state_and_invalid_events_are_ignored():
    timeline = [
        object(),
        _point("ん", time_sec=0.5, start_sec=0.4, end_sec=0.6),
        _point("あ", time_sec=float("nan"), start_sec=0.4, end_sec=0.6),
    ]

    assert _context(0.5, timeline).current_vowel is None
    assert _context(0.5, timeline, analysis_result_valid=False).current_vowel is None
    assert _context(0.5, timeline, analysis_pending_rebuild=True).current_vowel is None


class TestMS20B4PlaybackContextGui:
    @classmethod
    def setup_class(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)

    @classmethod
    def teardown_class(cls):
        destroy_wx_app(cls.app, owns_app=cls.owns_app)

    def setup_method(self):
        self.frame = MainFrame(None)
        self.controller = AppController(self.frame)
        self.frame.set_controller(self.controller)

    def teardown_method(self):
        destroy_wx_app(self.app, self.frame, owns_app=False)

    def _set_playing_plan(self):
        self.frame.ui_state.current_timing_plan = VowelTimingPlan(
            vowels=["あ"],
            timeline=[
                _point("あ", time_sec=0.5, start_sec=0.4, end_sec=0.6),
            ],
            anchors=[],
            source="whisper_segments",
            warning=None,
            observations=[],
        )
        self.frame.ui_state.analysis_result_valid = True
        self.frame.ui_state.analysis_pending_rebuild = False
        self.frame.ui_state.is_playing = True

    def test_initial_sync_and_raw_right_pane_clear_contract(self):
        assert self.frame.right_pane.get_playback_context_text() == (
            "[再生]\n"
            "再生位置: 0.00 秒\n"
            "現在フレーム: 0\n"
            "現在母音: (なし)"
        )

        host = wx.Frame(None)
        pane = RightPane(host)
        try:
            assert pane.get_info_text() == ""
            assert pane.get_playback_context_text() == ""
            pane.set_playback_context(_context(0.0, analysis_result_valid=False))
            pane.clear_info()
            assert pane.get_info_text() == ""
            assert pane.get_playback_context_text() == ""
        finally:
            host.Destroy()

    def test_live_update_changes_only_playback_context(self):
        self._set_playing_plan()
        static_before = self.frame.right_pane.get_info_text()

        with (
            patch("gui_wx.main_frame.build_output_diagnostics_snapshot_from_ui_state") as snapshot_builder,
            patch("gui_wx.right_pane.format_output_diagnostics_info") as static_formatter,
            patch.object(self.frame, "_update_preview_display") as preview_builder,
            patch.object(self.frame.right_pane.panel_info, "Layout") as layout,
            patch.object(self.frame.right_pane.panel_info, "FitInside") as fit_inside,
        ):
            self.frame.ui_state.playback_position_sec = 0.5
            self.frame.set_playback_position_sec(0.5)

        playback_text = self.frame.right_pane.get_playback_context_text()
        assert "再生位置: 0.50 秒" in playback_text
        assert "現在フレーム: 15" in playback_text
        assert "現在母音: あ" in playback_text
        assert self.frame.right_pane.get_info_text() == static_before
        snapshot_builder.assert_not_called()
        static_formatter.assert_not_called()
        preview_builder.assert_not_called()
        layout.assert_not_called()
        fit_inside.assert_not_called()

    def test_stopped_late_position_callback_keeps_default_context(self):
        self._set_playing_plan()
        self.frame.ui_state.is_playing = False

        self.controller._on_playback_update(0.5)

        assert self.frame.ui_state.playback_position_sec == 0.5
        playback_text = self.frame.right_pane.get_playback_context_text()
        assert "再生位置: 0.00 秒" in playback_text
        assert "現在母音: (なし)" in playback_text

    def test_stop_finish_and_reset_restore_default_context(self):
        self._set_playing_plan()
        self.frame.ui_state.playback_position_sec = 0.5
        self.frame.set_playback_position_sec(0.5)

        with patch.object(self.controller.playback_controller, "stop"):
            self.controller.request_playback_stop()
        assert "再生位置: 0.00 秒" in self.frame.right_pane.get_playback_context_text()

        self._set_playing_plan()
        self.frame.ui_state.playback_position_sec = 0.5
        self.frame.set_playback_position_sec(0.5)
        with patch.object(self.controller.playback_controller, "stop"):
            self.controller._on_playback_finished()
        assert "再生位置: 0.00 秒" in self.frame.right_pane.get_playback_context_text()

        self.frame.ui_state.selected_wav_path = "source.wav"
        self._set_playing_plan()
        with patch.object(self.controller.playback_controller, "stop"):
            assert self.controller.request_reset_workspace() is True
        assert "再生位置: 0.00 秒" in self.frame.right_pane.get_playback_context_text()
        assert "現在母音: (なし)" in self.frame.right_pane.get_playback_context_text()

    def test_playback_failure_restores_default_context(self, tmp_path):
        wav_path = tmp_path / "input.wav"
        wav_path.touch()
        self.frame.ui_state.selected_wav_path = str(wav_path)
        self._set_playing_plan()

        with (
            patch.object(self.controller.playback_controller, "play", return_value=False),
            patch("gui_wx.app_controller.wx.MessageBox"),
        ):
            self.frame.ui_state.is_playing = False
            self.controller.request_playback_play()

        assert "再生位置: 0.00 秒" in self.frame.right_pane.get_playback_context_text()
        assert "現在母音: (なし)" in self.frame.right_pane.get_playback_context_text()

    @pytest.mark.parametrize("mode", [ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SYSTEM])
    def test_playback_label_follows_normal_theme_text(self, mode):
        self.frame.apply_theme(mode)
        label = self.frame.right_pane.st_playback_context

        assert label.GetForegroundColour() == ThemeManager.get_palette().text_fg
        assert label.GetFont().GetWeight() != wx.FONTWEIGHT_BOLD
