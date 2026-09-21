from __future__ import annotations

from dataclasses import dataclass

import wx

from gui_wx.main_frame import MainFrame
from gui_wx.selected_event_editor import (
    SelectedEventEditBoundaryRequest,
    SelectedEventEditRequest,
)
from src.core.audio_processing import WavAnalysisResult
from src.core.pipeline import VowelTimingPlan
from src.core.preview_hit_test import PreviewSelectionRequest
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


@dataclass
class FakeKeyEvent:
    key_code: int
    control_down: bool = True
    alt_down: bool = False
    shift_down: bool = False
    skipped: bool = False

    def ControlDown(self) -> bool:
        return self.control_down

    def AltDown(self) -> bool:
        return self.alt_down

    def ShiftDown(self) -> bool:
        return self.shift_down

    def GetKeyCode(self) -> int:
        return self.key_code

    def Skip(self) -> None:
        self.skipped = True


@dataclass
class FakeEditorEvent:
    key_code: int = 0
    skipped: bool = False

    def GetKeyCode(self) -> int:
        return self.key_code

    def Skip(self) -> None:
        self.skipped = True


def make_ready_frame() -> MainFrame:
    frame = MainFrame(None)
    frame.ui_state.selected_text_path = "input.txt"
    frame.ui_state.selected_text_content = "あい"
    frame.ui_state.selected_wav_path = "input.wav"
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
            vowels=["あ", "い"],
            timeline=[
                VowelTimelinePoint(
                    1.0,
                    "あ",
                    value=0.6,
                    start_sec=0.8,
                    end_sec=1.1,
                ),
                VowelTimelinePoint(
                    1.4,
                    "い",
                    value=0.4,
                    start_sec=1.2,
                    end_sec=1.6,
                ),
            ],
            anchors=[],
            source="test",
            observations=None,
        ),
        analysis_text_content="あい",
        analysis_text_source="text_file",
    )
    frame.sync_ui_state()
    return frame


def select_event(frame: MainFrame, index: int) -> None:
    model = frame.placeholder_container.pnl_preview.model
    frame._on_preview_selection_request(
        PreviewSelectionRequest(
            index,
            model.base_plan_identity_digest,
            model.render_revision,
        )
    )


def edit_selected(
    frame: MainFrame,
    field: str,
    value: float | int,
    *,
    coalescing_token: int | None = None,
) -> None:
    editor_state = frame.right_pane._selected_editor_state
    assert editor_state is not None
    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=editor_state.base_event_index,
            base_identity_digest=editor_state.base_identity_digest,
            editor_revision=editor_state.editor_revision,
            field=field,
            value=value,
            coalescing_token=coalescing_token,
        )
    )


def test_discrete_edit_undo_redo_updates_snapshot_and_action_state() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)

    edit_selected(frame, "peak_value", 0.8)
    assert frame.ui_state.current_adjustment_snapshot.adjustments[0].peak_value == 0.8
    assert frame.mi_adjustment_undo.IsEnabled() is True
    assert frame.mi_adjustment_redo.IsEnabled() is False

    assert frame._perform_adjustment_history_navigation(redo=False) is True
    assert frame.ui_state.has_event_adjustments is False
    assert frame.mi_adjustment_redo.IsEnabled() is True
    assert frame.right_pane.st_selected_event_notice.GetLabel() == (
        "出力編集を元に戻しました。"
    )

    assert frame._perform_adjustment_history_navigation(redo=True) is True
    assert frame.ui_state.current_adjustment_snapshot.adjustments[0].peak_value == 0.8
    assert frame.right_pane.st_selected_event_notice.GetLabel() == (
        "出力編集をやり直しました。"
    )

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_coalesced_edits_are_one_transaction_and_selection_finishes_pending() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    editor_state = frame.right_pane._selected_editor_state
    assert editor_state is not None

    edit_selected(frame, "peak_value", 0.7, coalescing_token=4)
    edit_selected(frame, "peak_value", 0.8, coalescing_token=4)
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is True
    assert history.undo_transactions == ()

    select_event(frame, 1)
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is False
    assert len(history.undo_transactions) == 1

    assert frame._perform_adjustment_history_navigation(redo=False) is True
    assert frame.ui_state.has_event_adjustments is False

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_matching_boundary_finishes_pending_and_stale_boundary_is_noop() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    editor_state = frame.right_pane._selected_editor_state
    assert editor_state is not None
    edit_selected(frame, "peak_value", 0.8, coalescing_token=7)
    before = frame.ui_state.adjustment_history_state
    assert before is not None

    frame._on_selected_event_edit_boundary_request(
        SelectedEventEditBoundaryRequest(
            base_event_index=0,
            base_identity_digest=editor_state.base_identity_digest,
            field="peak_value",
            coalescing_token=8,
        )
    )
    assert frame.ui_state.adjustment_history_state == before

    frame._on_selected_event_edit_boundary_request(
        SelectedEventEditBoundaryRequest(
            base_event_index=0,
            base_identity_digest=editor_state.base_identity_digest,
            field="peak_value",
            coalescing_token=7,
        )
    )
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is False
    assert len(history.undo_transactions) == 1

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_right_pane_arrow_gesture_survives_refresh_and_coalesces_spin_events() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    pane = frame.right_pane
    control = pane._selected_editor_controls["hold_frames"]

    pane._on_selected_editor_key_down(
        FakeEditorEvent(wx.WXK_UP),
        "hold_frames",
    )
    active = pane._selected_editor_active_gesture
    assert active is not None
    control.SetValue(control.GetValue() + 1)
    pane._on_selected_editor_spin(FakeEditorEvent(), "hold_frames")
    assert pane._selected_editor_active_gesture == active

    control.SetValue(control.GetValue() + 1)
    pane._on_selected_editor_spin(FakeEditorEvent(), "hold_frames")
    assert pane._selected_editor_active_gesture == active
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is True

    pane._on_selected_editor_key_up(
        FakeEditorEvent(wx.WXK_UP),
        "hold_frames",
    )
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is False
    assert len(history.undo_transactions) == 1
    assert pane._selected_editor_active_gesture is None

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_reset_selected_and_reset_all_are_independent_undoable_transactions() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    edit_selected(frame, "peak_value", 0.8)
    select_event(frame, 1)
    edit_selected(frame, "peak_value", 0.9)
    assert len(frame.ui_state.current_adjustment_snapshot.adjustments) == 2

    current = frame.right_pane._selected_editor_state
    assert current is not None
    frame._on_adjustment_reset_selected(None)
    assert [
        item.base_event_index
        for item in frame.ui_state.current_adjustment_snapshot.adjustments
    ] == [0]
    assert frame._perform_adjustment_history_navigation(redo=False) is True
    assert len(frame.ui_state.current_adjustment_snapshot.adjustments) == 2

    frame._on_adjustment_reset_all(None)
    assert frame.ui_state.has_event_adjustments is False
    assert frame._perform_adjustment_history_navigation(redo=False) is True
    assert len(frame.ui_state.current_adjustment_snapshot.adjustments) == 2

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_invalid_direct_input_blocks_history_navigation_without_mutation() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    edit_selected(frame, "peak_value", 0.8)
    before = frame.ui_state.adjustment_history_state

    frame.right_pane._selected_editor_controls["peak_value"].ChangeValue("invalid")
    assert frame._perform_adjustment_history_navigation(redo=False) is False
    assert frame.ui_state.adjustment_history_state == before
    assert frame.right_pane.st_selected_event_validation.GetLabel() == (
        "Enterで値を確定するか、入力内容を修正してください。"
    )

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_shortcut_preserves_native_text_undo_outside_selected_editor(
    monkeypatch,
) -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    event = FakeKeyEvent(ord("Z"))
    monkeypatch.setattr(
        wx.Window,
        "FindFocus",
        staticmethod(lambda: frame.info_panel.tc_text_preview),
    )

    frame._on_history_shortcut(event)

    assert event.skipped is True
    assert frame.ui_state.can_undo_adjustment is False

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_new_edit_after_undo_discards_redo() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    edit_selected(frame, "peak_value", 0.8)
    assert frame._perform_adjustment_history_navigation(redo=False) is True
    assert frame.ui_state.can_redo_adjustment is True

    edit_selected(frame, "peak_value", 0.7)

    assert frame.ui_state.can_redo_adjustment is False

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_busy_finalizes_pending_and_workspace_reset_discards_history() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 0)
    edit_selected(frame, "peak_value", 0.8, coalescing_token=3)
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is True

    frame.ui_state.set_busy(True)
    frame.sync_ui_state()
    history = frame.ui_state.adjustment_history_state
    assert history is not None
    assert history.has_pending_change is False
    assert len(history.undo_transactions) == 1
    assert frame.mi_adjustment_undo.IsEnabled() is False

    frame.ui_state.set_busy(False)
    frame.ui_state.reset_workspace()
    frame.sync_ui_state()
    assert frame.ui_state.adjustment_history_state is None
    assert frame.mi_adjustment_undo.IsEnabled() is False
    assert frame.mi_adjustment_redo.IsEnabled() is False

    destroy_wx_app(app, frame, owns_app=owns_app)
