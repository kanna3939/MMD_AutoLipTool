from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.theme import ThemeManager, ThemeMode
from gui_wx.ui_state import INPUT_MODE_TEXT_AUDIO, INPUT_MODE_VOICE_ONLY, UiState
from src.core import SpeechTimingAnchor, VowelTimingPlan
from src.core.audio_processing import WavAnalysisResult
from src.core.pipeline import (
    _refine_timeline_intervals_with_observations,
    build_even_vowel_timeline,
)
from src.core.text_processing import hiragana_to_vowel_tokens
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _wav_analysis(duration_sec: float = 1.0) -> WavAnalysisResult:
    return WavAnalysisResult(
        sample_rate_hz=44100,
        frame_count=int(44100 * duration_sec),
        channel_count=1,
        duration_sec=duration_sec,
        leading_silence_end_sec=0.1,
        trailing_silence_start_sec=max(0.1, duration_sec - 0.1),
        speech_start_sec=0.1,
        speech_end_sec=max(0.1, duration_sec - 0.1),
        has_speech=True,
    )


def _timing_plan(
    *,
    vowel: str = "あ",
    time_sec: float = 0.3,
    warning: str | None = None,
) -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=[vowel],
        timeline=[
            VowelTimelinePoint(
                time_sec=time_sec,
                vowel=vowel,
                duration_sec=0.2,
                start_sec=time_sec - 0.1,
                end_sec=time_sec + 0.1,
            )
        ],
        anchors=[
            SpeechTimingAnchor(
                start_sec=time_sec - 0.1,
                end_sec=time_sec + 0.1,
                text=vowel,
            )
        ],
        source="even_fallback" if warning else "whisper_segments",
        warning=warning,
        observations=None,
    )


class TestMS20B3RightPaneInfo:
    @classmethod
    def setup_class(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)

    @classmethod
    def teardown_class(cls):
        destroy_wx_app(cls.app, owns_app=cls.owns_app)

    def setup_method(self):
        self.frame = MainFrame(None)
        self.controller = AppController(self.frame)
        self.controller.build_active_whisper_model_request = MagicMock(
            return_value=MagicMock()
        )
        self.frame.set_controller(self.controller)

    def teardown_method(self):
        destroy_wx_app(self.app, self.frame, owns_app=False)

    def _mark_text_audio_success(self, plan: VowelTimingPlan | None = None):
        state = self.frame.ui_state
        state.selected_text_path = "input.txt"
        state.selected_text_content = "あ"
        state.selected_wav_path = "source.wav"
        state.selected_wav_analysis = _wav_analysis()
        state.mark_analysis_success(
            plan or _timing_plan(),
            input_mode=INPUT_MODE_TEXT_AUDIO,
            analysis_text_content="あ",
            analysis_text_source="text_file",
        )
        self.frame.sync_ui_state()

    def test_preview_uses_retained_audio_metadata_when_analysis_duration_is_missing(self):
        state = self.frame.ui_state
        state.selected_text_path = "input.txt"
        state.selected_text_content = "あ"
        state.selected_wav_path = "source.wav"
        state.selected_wav_analysis = None
        state.selected_analysis_wav = SimpleNamespace(duration_sec=1.0)
        state.mark_analysis_success(
            _timing_plan(),
            input_mode=INPUT_MODE_TEXT_AUDIO,
            analysis_text_content="あ",
            analysis_text_source="text_file",
        )

        self.frame.sync_ui_state()

        assert self.frame._current_ui_sync_context is not None
        assert self.frame.placeholder_container.pnl_preview.model.is_valid
        assert self.frame.placeholder_container.pnl_preview.model.duration_sec == 1.0

    def test_preview_displays_pipeline_repaired_long_vowel_same_morph_plan(self):
        tokens = hiragana_to_vowel_tokens("あーあ")
        raw_timeline = build_even_vowel_timeline(
            [token.vowel for token in tokens],
            0.0,
            1.5,
            tokens=tokens,
        )
        with patch(
            "src.core.pipeline.load_rms_series",
            side_effect=OSError("mocked RMS failure"),
        ):
            observed = _refine_timeline_intervals_with_observations(
                timeline=raw_timeline,
                wav_path="dummy.wav",
                speech_start_sec=0.0,
                speech_end_sec=1.5,
                upper_limit=0.5,
            )
        plan = VowelTimingPlan(
            vowels=[token.vowel for token in tokens],
            timeline=observed.timeline,
            anchors=[],
            source="even_fallback",
            observations=observed.observations,
        )
        state = self.frame.ui_state
        state.selected_text_path = "input.txt"
        state.selected_text_content = "あーあ"
        state.selected_wav_path = "source.wav"
        state.selected_wav_analysis = _wav_analysis(1.5)
        state.mark_analysis_success(
            plan,
            input_mode=INPUT_MODE_TEXT_AUDIO,
            analysis_text_content="あーあ",
            analysis_text_source="text_file",
        )

        self.frame.sync_ui_state()

        preview_model = self.frame.placeholder_container.pnl_preview.model
        assert self.frame._current_ui_sync_context is not None
        assert preview_model.is_valid
        assert sum(len(row.segments) for row in preview_model.data.rows) == 2

    def test_preview_displays_pipeline_repaired_interleaved_same_morph_plan(self):
        raw_timeline = [
            VowelTimelinePoint(
                0.2,
                "あ",
                value=0.6,
                duration_sec=0.4,
                start_sec=0.1,
                end_sec=0.5,
                vowel_token_index=0,
            ),
            VowelTimelinePoint(
                0.5,
                "い",
                value=0.4,
                duration_sec=0.1,
                start_sec=0.45,
                end_sec=0.55,
                vowel_token_index=1,
            ),
            VowelTimelinePoint(
                16 / 30,
                "あ",
                value=0.5,
                duration_sec=6 / 30,
                start_sec=14 / 30,
                end_sec=20 / 30,
                vowel_token_index=2,
            ),
        ]
        with patch(
            "src.core.pipeline.load_rms_series",
            side_effect=OSError("mocked RMS failure"),
        ):
            observed = _refine_timeline_intervals_with_observations(
                timeline=raw_timeline,
                wav_path="dummy.wav",
                speech_start_sec=0.0,
                speech_end_sec=1.0,
                upper_limit=0.5,
            )
        plan = VowelTimingPlan(
            vowels=[point.vowel for point in observed.timeline],
            timeline=observed.timeline,
            anchors=[],
            source="whisper_words",
            observations=observed.observations,
        )
        state = self.frame.ui_state
        state.selected_text_path = "input.txt"
        state.selected_text_content = "あいあ"
        state.selected_wav_path = "source.wav"
        state.selected_wav_analysis = _wav_analysis()
        state.mark_analysis_success(
            plan,
            input_mode=INPUT_MODE_TEXT_AUDIO,
            analysis_text_content="あいあ",
            analysis_text_source="text_file",
        )

        self.frame.sync_ui_state()

        preview_model = self.frame.placeholder_container.pnl_preview.model
        assert self.frame._current_ui_sync_context is not None
        assert self.frame._current_ui_sync_failure_reason is None
        assert preview_model.is_valid
        assert sum(len(row.segments) for row in preview_model.data.rows) == 3

    def test_preview_shape_failure_is_not_reported_as_missing_audio(self):
        with patch(
            "gui_wx.main_frame.build_ui_sync_context",
            side_effect=ValueError("synthetic shape failure"),
        ):
            self._mark_text_audio_success()

        preview_panel = self.frame.placeholder_container.pnl_preview
        assert not preview_panel.model.is_valid
        assert "Preview形状を生成できませんでした" in preview_panel.placeholder_msg
        assert "音声情報" not in preview_panel.placeholder_msg
        assert self.frame._current_ui_sync_failure_reason == (
            "ValueError: synthetic shape failure"
        )

    def test_right_pane_uses_scrolled_info_and_clear_is_empty(self):
        pane = self.frame.right_pane

        assert isinstance(pane.panel_info, wx.ScrolledWindow)
        assert pane.notebook.GetPageCount() == 6
        pane.clear_info()
        assert pane.st_info.GetLabel() == ""
        assert pane.get_playback_context_text() == ""

    def test_main_frame_initial_sync_shows_four_sections(self):
        text = self.frame.right_pane.st_info.GetLabel()

        assert "[入力]" in text
        assert "[解析]" in text
        assert "[生成]" in text
        assert "[保存可否]" in text
        assert "将来ここに" not in text
        assert "状態: 未解析" in text
        assert "VMD保存: 不可" in text
        assert "[再生]" in self.frame.right_pane.get_playback_context_text()

    def test_text_input_pending_and_voice_only_success_are_distinct(self):
        state = self.frame.ui_state
        state.selected_text_path = "input.txt"
        state.selected_text_content = "あ"
        state.selected_wav_path = "source.wav"
        state.selected_wav_analysis = _wav_analysis()
        state.invalidate_analysis()
        self.frame.sync_ui_state()
        pending_text = self.frame.right_pane.get_info_text()

        self.frame.ui_state = UiState(
            selected_wav_path="voice.wav",
            selected_wav_analysis=_wav_analysis(),
            input_mode=INPUT_MODE_VOICE_ONLY,
        )
        self.frame.ui_state.mark_analysis_success(
            _timing_plan(),
            input_mode=INPUT_MODE_VOICE_ONLY,
            analysis_text_content="あ",
            analysis_text_source="whisper_transcription",
            transcription_text="あ",
            transcription_source="segments",
            transcription_timing_source="segments",
        )
        self.frame.sync_ui_state()
        success_text = self.frame.right_pane.st_info.GetLabel()

        assert "状態: 再解析が必要" in pending_text
        assert "入力モード: 音声のみ" in success_text
        assert "状態: 解析済み" in success_text
        assert "タイミング元: whisper_segments" in success_text
        assert "アンカー数: 1 件" in success_text
        assert "母音イベント数: 1 件" in success_text
        assert "最大フレーム: 12" in success_text
        assert "VMD保存: 可能" in success_text

    def test_fallback_updates_warning_count_and_warning_tab(self):
        self._mark_text_audio_success(_timing_plan(warning="fallback warning"))
        info_text = self.frame.right_pane.st_info.GetLabel()
        warning_text = self.frame.right_pane.get_warning_text()

        assert "タイミング警告: あり" in info_text
        assert "要確認警告数: 1 件" in info_text
        assert "[WARNING]" in warning_text
        assert "fallback" in warning_text

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_analysis_start_masks_old_result_and_success_replaces_it(
        self,
        mock_worker_class,
        mock_dialog_class,
    ):
        mock_worker_class.return_value = MagicMock()
        self._mark_text_audio_success(_timing_plan(vowel="あ", time_sec=0.3))

        self.frame._run_analysis()
        progress_text = self.frame.right_pane.st_info.GetLabel()
        assert "状態: 解析中" in progress_text
        assert "母音イベント数: 0 件" in progress_text
        assert "最大フレーム: (未算出)" in progress_text
        assert "VMD保存: 不可" in progress_text

        self.frame._on_analysis_success(
            self.frame._current_job_id,
            _timing_plan(vowel="い", time_sec=0.6),
        )
        success_text = self.frame.right_pane.st_info.GetLabel()
        assert "状態: 解析済み" in success_text
        assert "最大フレーム: 21" in success_text
        assert "VMD保存: 可能" in success_text

    @patch("gui_wx.main_frame.wx.MessageBox")
    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_analysis_error_restores_old_info_but_blocks_save(
        self,
        mock_worker_class,
        mock_dialog_class,
        mock_message_box,
    ):
        mock_worker_class.return_value = MagicMock()
        self._mark_text_audio_success()
        self.frame._run_analysis()

        self.frame._on_analysis_error(
            self.frame._current_job_id,
            ValueError("analysis failed"),
        )
        text = self.frame.right_pane.get_info_text()

        assert "状態: 解析済み" in text
        assert "母音イベント数: 1 件" in text
        assert "最大フレーム: (未算出)" not in text
        assert "VMD保存: 不可" in text

    @patch("gui_wx.main_frame.AnalysisProgressDialog")
    @patch("gui_wx.main_frame.AnalysisWorker")
    def test_analysis_cancel_restores_reusable_old_result(
        self,
        mock_worker_class,
        mock_dialog_class,
    ):
        mock_worker_class.return_value = MagicMock()
        old_plan = _timing_plan()
        self._mark_text_audio_success(old_plan)
        self.frame._run_analysis()
        self.frame._on_analysis_cancel()

        self.frame._on_analysis_success(
            self.frame._current_job_id,
            MagicMock(),
        )
        text = self.frame.right_pane.get_info_text()

        assert self.frame.ui_state.current_timing_plan is old_plan
        assert "状態: 解析済み" in text
        assert "VMD保存: 可能" in text
        assert "状態: 解析中" not in text

    def test_output_parameter_change_uses_full_sync_once_without_reanalysis(self):
        self._mark_text_audio_success()
        self.frame.set_closing_hold_frames(3)
        self.frame.set_closing_softness_frames(4)
        event = MagicMock()

        with patch.object(
            self.frame,
            "_update_preview_display",
            wraps=self.frame._update_preview_display,
        ) as update_preview:
            self.frame._on_output_setting_changed(event)

        text = self.frame.right_pane.get_info_text()
        assert update_preview.call_count == 1
        assert "状態: 解析済み" in text
        assert "開口保持: 3 フレーム" in text
        assert "閉口スムース: 4 フレーム" in text

    def test_reanalysis_state_only_uses_bold_orange_attention_style(self):
        pane = self.frame.right_pane

        assert pane.pnl_info_reanalysis.IsShown() is False
        self.frame.ui_state.invalidate_analysis()
        self.frame.sync_ui_state()

        assert pane.pnl_info_reanalysis.IsShown() is True
        assert pane.st_info_state_prefix.GetFont().GetWeight() != wx.FONTWEIGHT_BOLD
        assert pane.st_info_reanalysis.GetFont().GetWeight() == wx.FONTWEIGHT_BOLD
        assert (
            pane.st_info_reanalysis.GetForegroundColour()
            == ThemeManager.get_palette().attention_text
        )

        self.frame.apply_theme(ThemeMode.LIGHT)
        assert (
            pane.st_info_reanalysis.GetForegroundColour()
            == ThemeManager.get_palette().attention_text
        )

        self._mark_text_audio_success()
        assert pane.pnl_info_reanalysis.IsShown() is False

    def test_apply_settings_syncs_generation_values(self):
        self.frame.apply_settings(
            {
                "closing_hold_frames": 5,
                "closing_softness_frames": 6,
            }
        )
        text = self.frame.right_pane.st_info.GetLabel()

        assert "開口保持: 5 フレーム" in text
        assert "閉口スムース: 6 フレーム" in text

    def test_workspace_reset_restores_initial_info(self):
        self._mark_text_audio_success()
        with patch.object(self.controller.playback_controller, "stop"):
            assert self.controller.request_reset_workspace() is True
        text = self.frame.right_pane.st_info.GetLabel()

        assert "状態: 未解析" in text
        assert "母音イベント数: 0 件" in text
        assert "VMD保存: 不可" in text
        assert "input.txt" not in text

    def test_late_analysis_callback_does_not_change_info(self):
        self._mark_text_audio_success()
        self.frame._current_job_id = 10
        before = self.frame.right_pane.st_info.GetLabel()

        self.frame._on_analysis_success(9, _timing_plan(time_sec=0.7))

        assert self.frame.right_pane.st_info.GetLabel() == before

    def test_playback_position_does_not_change_snapshot_info(self):
        self._mark_text_audio_success()
        before = self.frame.right_pane.st_info.GetLabel()

        self.frame.ui_state.playback_position_sec = 0.5
        self.frame.sync_ui_state()

        assert self.frame.right_pane.st_info.GetLabel() == before

    def test_long_path_uses_vertical_scrolling_without_horizontal_style(self):
        self.frame.SetSize((420, 240))
        self.frame.ui_state.selected_text_path = "C:/" + "very_long_directory/" * 20 + "input.txt"
        self.frame.ui_state.selected_text_content = "あ"
        self.frame.sync_ui_state()
        self.frame.Layout()
        self.app.ProcessPendingEvents()

        pane = self.frame.right_pane.panel_info
        assert pane.GetVirtualSize().height > 0
        assert pane.GetWindowStyleFlag() & wx.HSCROLL == 0
        assert self.frame.right_pane.GetMinSize().width <= 0
