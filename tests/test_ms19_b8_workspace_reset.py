import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import wx

from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from gui_wx.ui_state import INPUT_MODE_VOICE_ONLY, StatusKey, UiState
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus
from src.core import SpeechTimingAnchor, VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


def _timing_plan() -> VowelTimingPlan:
    return VowelTimingPlan(
        vowels=["あ"],
        timeline=[
            VowelTimelinePoint(
                time_sec=0.2,
                vowel="あ",
                duration_sec=0.2,
                start_sec=0.1,
                end_sec=0.3,
            )
        ],
        anchors=[SpeechTimingAnchor(start_sec=0.1, end_sec=0.3, text="あ")],
        source="whisper_segments",
        observations=[],
    )


class UiStateWorkspaceResetTests(unittest.TestCase):
    def _workspace_state(self) -> UiState:
        state = UiState(
            selected_text_path="source.txt",
            selected_wav_path="source.wav",
            selected_audio_input=SimpleNamespace(source_path="source.wav"),
            selected_audio_probe=SimpleNamespace(format_name="wav"),
            selected_analysis_wav=SimpleNamespace(analysis_wav_path="cache.wav"),
            selected_text_content="あいうえお",
            selected_hiragana_content="あいうえお",
            selected_vowel_content="aiueo",
            selected_wav_analysis=SimpleNamespace(duration_sec=1.0),
            input_mode=INPUT_MODE_VOICE_ONLY,
            transcription_text="あいうえお",
            transcription_source="segments",
            transcription_timing_source="segments",
            transcription_original_text="あいうえお",
            transcription_is_edited=True,
            transcription_edit_dirty=True,
            transcription_timing_result=object(),
            analysis_text_content="あいうえお",
            analysis_text_source="user_edited_transcription",
            current_timing_plan=SimpleNamespace(timeline=[object()]),
            analysis_result_valid=True,
            analysis_pending_rebuild=True,
            selected_source_event_index=2,
            current_audio_job_id=7,
            audio_worker_state=AudioWorkerState(
                audio_job_id=7,
                kind=AudioWorkerKind.MMD_WAV,
                status=AudioWorkerStatus.FAILED,
                message="出力失敗",
            ),
            is_playing=True,
            playback_position_sec=0.5,
            loaded_playback_path="cache.wav",
            last_mmd_wav_output_path="result.wav",
            status_key=StatusKey.ANALYSIS_READY,
        )
        state.recent_text_files = ["recent.txt"]
        state.recent_wav_files = ["recent.wav"]
        state.recent_audio_files = ["recent.mp3"]
        state.last_text_dialog_dir = "text-dir"
        state.last_wav_dialog_dir = "wav-dir"
        state.last_audio_dialog_dir = "audio-dir"
        state.last_vmd_output_dir = "vmd-dir"
        state.last_mmd_wav_export_dir = "mmd-wav-dir"
        state.theme_mode = "light"
        state.resolved_theme = "light"
        return state

    def test_workspace_user_data_excludes_worker_failure_only(self):
        state = UiState(
            audio_worker_state=AudioWorkerState(
                audio_job_id=1,
                kind=AudioWorkerKind.PROBE,
                status=AudioWorkerStatus.FAILED,
                message="読み込み失敗",
            )
        )

        self.assertFalse(state.has_workspace_user_data)

    def test_reset_workspace_clears_work_data_and_preserves_history(self):
        state = self._workspace_state()

        state.reset_workspace()

        self.assertFalse(state.has_workspace_user_data)
        self.assertIsNone(state.selected_text_path)
        self.assertIsNone(state.selected_wav_path)
        self.assertIsNone(state.selected_audio_input)
        self.assertIsNone(state.selected_audio_probe)
        self.assertIsNone(state.selected_analysis_wav)
        self.assertEqual(state.selected_text_content, "")
        self.assertEqual(state.selected_hiragana_content, "")
        self.assertEqual(state.selected_vowel_content, "")
        self.assertIsNone(state.selected_wav_analysis)
        self.assertEqual(state.transcription_text, "")
        self.assertIsNone(state.transcription_timing_result)
        self.assertEqual(state.analysis_text_content, "")
        self.assertIsNone(state.current_timing_plan)
        self.assertFalse(state.analysis_result_valid)
        self.assertFalse(state.analysis_pending_rebuild)
        self.assertIsNone(state.selected_source_event_index)
        self.assertIsNone(state.audio_worker_state)
        self.assertFalse(state.is_playing)
        self.assertEqual(state.playback_position_sec, 0.0)
        self.assertIsNone(state.loaded_playback_path)
        self.assertIsNone(state.last_mmd_wav_output_path)
        self.assertEqual(state.status_key, StatusKey.IDLE)
        self.assertEqual(state.current_audio_job_id, 7)
        self.assertEqual(state.recent_text_files, ["recent.txt"])
        self.assertEqual(state.recent_wav_files, ["recent.wav"])
        self.assertEqual(state.recent_audio_files, ["recent.mp3"])
        self.assertEqual(state.last_text_dialog_dir, "text-dir")
        self.assertEqual(state.last_mmd_wav_export_dir, "mmd-wav-dir")
        self.assertEqual(state.theme_mode, "light")
        self.assertEqual(state.resolved_theme, "light")

        state.reset_workspace()
        self.assertFalse(state.has_workspace_user_data)
        self.assertEqual(state.current_audio_job_id, 7)


class WorkspaceResetControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.owns_app = get_or_create_wx_app(wx.App, False)
        cls.frame = MainFrame(None)
        cls.controller = AppController(cls.frame)
        cls.frame.set_controller(cls.controller)

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, cls.frame, owns_app=cls.owns_app)

    def setUp(self):
        self.frame.ui_state = UiState()
        self.frame._current_job_id = 31
        self.frame._cancel_requested = False
        self.frame._progress_dialog = None
        self.frame._timeout_timer = None
        self.frame._worker = None
        self.controller._audio_worker_previous_status_key = None
        self.controller.viewport_controller.set_duration(0.0)
        self.frame.reset_workspace_display()
        self.frame.sync_ui_state()

    def _populate_frame_workspace(self):
        state = self.frame.ui_state
        state.selected_text_path = "source.txt"
        state.selected_text_content = "あいうえお"
        state.selected_hiragana_content = "あいうえお"
        state.selected_vowel_content = "aiueo"
        state.selected_wav_path = "source.wav"
        state.selected_audio_input = SimpleNamespace(source_path="source.wav")
        state.selected_audio_probe = SimpleNamespace(format_name="wav")
        state.selected_analysis_wav = SimpleNamespace(analysis_wav_path="cache.wav")
        state.selected_wav_analysis = SimpleNamespace(duration_sec=2.0)
        state.input_mode = INPUT_MODE_VOICE_ONLY
        state.transcription_text = "あいうえお"
        state.transcription_original_text = "あいうえお"
        state.transcription_timing_result = object()
        state.analysis_text_content = "あいうえお"
        state.current_timing_plan = _timing_plan()
        state.analysis_result_valid = True
        state.selected_source_event_index = 3
        state.is_playing = True
        state.playback_position_sec = 0.75
        state.loaded_playback_path = "cache.wav"
        state.last_mmd_wav_output_path = "result.wav"
        state.status_key = StatusKey.ANALYSIS_READY
        self.frame.set_text_path("source.txt")
        self.frame.set_wav_path("source.wav")
        self.frame.set_text_preview("あいうえお")
        self.frame.set_hiragana_preview("あいうえお")
        self.frame.set_vowel_preview("aiueo")
        self.frame.set_wav_info("Duration: 2.00s")
        self.frame.placeholder_container.set_waveform_data([0.1, 0.2], 2.0)
        self.frame.right_pane.set_selected_event_summary("選択中のイベント")
        self.controller.viewport_controller.set_duration(2.0)

    def test_confirmed_reset_invalidates_jobs_and_restores_widgets(self):
        self._populate_frame_workspace()
        old_audio_job_id = self.frame.ui_state.current_audio_job_id
        old_analysis_job_id = self.frame._current_job_id

        with patch.object(self.controller.playback_controller, "stop") as mock_stop:
            self.assertTrue(self.controller.request_reset_workspace())

        state = self.frame.ui_state
        mock_stop.assert_called_once()
        self.assertEqual(state.current_audio_job_id, old_audio_job_id + 1)
        self.assertEqual(self.frame._current_job_id, old_analysis_job_id + 1)
        self.assertFalse(state.has_workspace_user_data)
        self.assertFalse(state.analysis_result_valid)
        self.assertFalse(state.analysis_pending_rebuild)
        self.assertEqual(state.status_key, StatusKey.IDLE)
        self.assertFalse(state.vmd_save_ready)
        self.assertFalse(state.playback_ready)
        self.assertIsNone(state.loaded_playback_path)
        self.assertEqual(self.controller.viewport_controller.duration_sec, 0.0)
        self.assertEqual(self.controller.viewport_controller.zoom_factor, 1)
        self.assertEqual(self.frame.info_panel.st_text_path.GetLabel(), "TEXT: (未選択)")
        self.assertEqual(self.frame.info_panel.st_wav_path.GetLabel(), "WAV: (未選択)")
        self.assertEqual(self.frame.info_panel.get_text_preview(), "")
        self.assertEqual(self.frame.info_panel.tc_hiragana_preview.GetValue(), "")
        self.assertEqual(self.frame.info_panel.tc_vowel_preview.GetValue(), "")
        self.assertEqual(self.frame.info_panel.tc_wav_info.GetValue(), "")
        self.assertFalse(self.frame.info_panel.is_text_preview_editable())
        self.assertFalse(self.frame.info_panel.btn_apply_transcription_edit.IsEnabled())
        self.assertEqual(self.frame.placeholder_container.pnl_waveform._samples, [])
        self.assertEqual(self.frame.placeholder_container.pnl_waveform._duration_sec, 0.0)
        self.assertEqual(self.frame.placeholder_container.pnl_preview.model.duration_sec, 0.0)
        self.assertEqual(
            self.frame.right_pane.st_selected_event.GetLabel(),
            "選択中のイベントはありません。",
        )
        self.assertEqual(self.frame.get_status_text(), "待機中")

    def test_menu_confirmation_no_keeps_everything_unchanged(self):
        self._populate_frame_workspace()
        state = self.frame.ui_state
        old_audio_job_id = state.current_audio_job_id
        old_analysis_job_id = self.frame._current_job_id

        with patch.object(self.frame, "confirm_workspace_reset", return_value=False):
            self.frame._on_mi_workspace_reset(None)

        self.assertEqual(state.selected_text_path, "source.txt")
        self.assertEqual(state.selected_wav_path, "source.wav")
        self.assertTrue(state.analysis_result_valid)
        self.assertEqual(state.current_audio_job_id, old_audio_job_id)
        self.assertEqual(self.frame._current_job_id, old_analysis_job_id)
        self.assertEqual(self.frame.info_panel.get_text_preview(), "あいうえお")

    def test_menu_confirmation_yes_starts_reset(self):
        self._populate_frame_workspace()

        with patch.object(self.frame, "confirm_workspace_reset", return_value=True):
            with patch.object(self.controller, "request_reset_workspace", return_value=True) as mock_reset:
                self.frame._on_mi_workspace_reset(None)

        mock_reset.assert_called_once_with()

    def test_pristine_menu_reset_skips_confirmation_and_clears_failure_state(self):
        state = self.frame.ui_state
        state.audio_worker_state = AudioWorkerState(
            audio_job_id=0,
            kind=AudioWorkerKind.PROBE,
            status=AudioWorkerStatus.FAILED,
            message="読み込み失敗",
        )
        old_audio_job_id = state.current_audio_job_id
        old_analysis_job_id = self.frame._current_job_id

        with patch.object(self.frame, "confirm_workspace_reset") as mock_confirm:
            with patch.object(self.controller.playback_controller, "stop"):
                self.frame._on_mi_workspace_reset(None)

        mock_confirm.assert_not_called()
        self.assertIsNone(state.audio_worker_state)
        self.assertEqual(state.current_audio_job_id, old_audio_job_id + 1)
        self.assertEqual(self.frame._current_job_id, old_analysis_job_id + 1)
        self.assertEqual(self.frame.get_status_text(), "待機中")

    def test_busy_workspace_reset_is_rejected(self):
        self.frame.ui_state.set_busy(True)
        self.frame.sync_ui_state()
        old_audio_job_id = self.frame.ui_state.current_audio_job_id
        old_analysis_job_id = self.frame._current_job_id

        self.assertFalse(self.frame.mi_workspace_reset.IsEnabled())
        self.assertFalse(self.controller.request_reset_workspace())
        self.frame._on_mi_workspace_reset(None)

        self.assertEqual(self.frame.ui_state.current_audio_job_id, old_audio_job_id)
        self.assertEqual(self.frame._current_job_id, old_analysis_job_id)

    def test_reset_drops_late_callbacks_without_deleting_files(self):
        self._populate_frame_workspace()
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "source.txt"
            output_path = Path(temp_dir) / "result.vmd"
            cache_path = Path(temp_dir) / "analysis.wav"
            for path in (source_path, output_path, cache_path):
                path.write_text("keep", encoding="utf-8")

            old_audio_job_id = self.frame.ui_state.current_audio_job_id
            old_analysis_job_id = self.frame._current_job_id
            with patch.object(self.controller.playback_controller, "stop"):
                self.controller.request_reset_workspace()

            self.frame._on_analysis_success(old_analysis_job_id, MagicMock())
            with patch("gui_wx.app_controller.wx.MessageBox") as mock_message_box:
                self.controller._on_audio_worker_error(
                    old_audio_job_id,
                    AudioWorkerKind.PROBE,
                    RuntimeError("late callback"),
                )

            self.assertIsNone(self.frame.ui_state.current_timing_plan)
            self.assertFalse(self.frame.ui_state.analysis_result_valid)
            mock_message_box.assert_not_called()
            for path in (source_path, output_path, cache_path):
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
