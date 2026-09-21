from __future__ import annotations

import wx

from gui_wx.main_frame import MainFrame
from src.core.audio_processing import WavAnalysisResult
from src.core.pipeline import VowelTimingPlan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app
from tests.test_wx_ms21_b6_undo_redo import select_event


def _make_long_frame():
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    frame.ui_state.selected_text_path = "long.txt"
    frame.ui_state.selected_text_content = "ああ"
    frame.ui_state.selected_wav_path = "long.wav"
    frame.ui_state.selected_wav_analysis = WavAnalysisResult(
        sample_rate_hz=44100,
        frame_count=441000,
        channel_count=1,
        duration_sec=10.0,
        leading_silence_end_sec=0.0,
        trailing_silence_start_sec=10.0,
        speech_start_sec=0.0,
        speech_end_sec=10.0,
        has_speech=True,
    )
    frame.ui_state.mark_analysis_success(
        VowelTimingPlan(
            vowels=["あ", "あ"],
            timeline=[
                VowelTimelinePoint(
                    0.2,
                    "あ",
                    value=0.6,
                    duration_sec=0.2,
                    start_sec=0.1,
                    end_sec=0.3,
                    vowel_token_index=0,
                ),
                VowelTimelinePoint(
                    0.5,
                    "あ",
                    value=0.4,
                    duration_sec=0.2,
                    start_sec=0.4,
                    end_sec=0.6,
                    vowel_token_index=1,
                    is_long_vowel_continuation=True,
                    long_vowel_source_token_index=0,
                ),
            ],
            anchors=[],
            source="test",
            observations=None,
        )
    )
    frame.sync_ui_state()
    return app, frame, owns_app


def _mode_request(frame: MainFrame, value):
    state = frame.right_pane._selected_editor_state
    assert state is not None
    from gui_wx.selected_event_editor import SelectedEventEditRequest

    return SelectedEventEditRequest(
        base_event_index=state.base_event_index,
        base_identity_digest=state.base_identity_digest,
        editor_revision=state.editor_revision,
        field="long_vowel_mode",
        value=value,
    )


def test_only_terminal_long_vowel_event_enables_mode_override() -> None:
    app, frame, owns_app = _make_long_frame()
    select_event(frame, 0)
    assert frame.right_pane.choice_selected_event_mode.IsEnabled() is False
    before = frame.ui_state.current_adjustment_snapshot
    frame._on_selected_event_edit_request(_mode_request(frame, "decay"))
    assert frame.ui_state.current_adjustment_snapshot == before

    select_event(frame, 1)
    state = frame.right_pane._selected_editor_state
    assert state is not None
    assert state.long_vowel_mode_enabled is True
    assert state.requested_long_vowel_mode is None
    assert state.effective_long_vowel_mode == "hold"
    assert frame.right_pane.choice_selected_event_mode.IsEnabled() is True
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_decay_disables_tail_but_preserves_latent_values_on_hold_restore() -> None:
    app, frame, owns_app = _make_long_frame()
    select_event(frame, 1)
    state = frame.right_pane._selected_editor_state
    assert state is not None

    from gui_wx.selected_event_editor import SelectedEventEditRequest

    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            state.base_event_index,
            state.base_identity_digest,
            state.editor_revision,
            "hold_frames",
            5,
        )
    )
    state = frame.right_pane._selected_editor_state
    assert state is not None
    frame._on_selected_event_edit_request(_mode_request(frame, "decay"))
    state = frame.right_pane._selected_editor_state
    assert state is not None
    assert state.effective_long_vowel_mode == "decay"
    assert state.tail_controls_enabled is False
    assert frame.right_pane.st_selected_event_mode_notice.GetLabel().startswith("decayでは長音終端を0へ")
    adjustment = frame.ui_state.current_adjustment_snapshot.adjustments[0]
    assert adjustment.hold_frames == 5
    assert adjustment.long_vowel_mode == "decay"

    frame._on_selected_event_edit_request(_mode_request(frame, "hold"))
    state = frame.right_pane._selected_editor_state
    assert state is not None
    assert state.tail_controls_enabled is True
    adjustment = frame.ui_state.current_adjustment_snapshot.adjustments[0]
    assert adjustment.hold_frames == 5
    assert adjustment.long_vowel_mode == "hold"
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_mode_reset_restores_inherit_and_stale_mode_is_ignored() -> None:
    app, frame, owns_app = _make_long_frame()
    select_event(frame, 1)
    state = frame.right_pane._selected_editor_state
    assert state is not None
    request = _mode_request(frame, "decay")
    frame._on_selected_event_edit_request(request)
    state_after = frame.right_pane._selected_editor_state
    assert state_after is not None
    frame._on_selected_event_edit_request(request)
    assert frame.ui_state.current_adjustment_snapshot.adjustments[0].long_vowel_mode == "decay"

    frame._on_selected_event_reset_request(
        state_after.base_event_index,
        state_after.base_identity_digest,
        state_after.editor_revision,
    )
    assert frame.ui_state.current_adjustment_snapshot.adjustments == ()
    state_reset = frame.right_pane._selected_editor_state
    assert state_reset is not None
    assert state_reset.requested_long_vowel_mode is None
    assert state_reset.effective_long_vowel_mode == "hold"
    destroy_wx_app(app, frame, owns_app=owns_app)
