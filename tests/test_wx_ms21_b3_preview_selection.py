from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import Mock

import wx

from gui_wx.main_frame import MainFrame
from gui_wx.preview_panel import PreviewPanel, PreviewRenderer, _GestureState
from src.core.audio_processing import WavAnalysisResult
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    resolve_effective_shape_plan,
)
from src.core.pipeline import VowelTimingPlan
from src.core.preview_hit_test import PreviewSelectionRequest
from src.core.preview_transform import build_preview_data_from_effective_shape_plan
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


@dataclass
class FakeMouseEvent:
    x: int
    y: int
    dragging: bool = False
    left_down: bool = False

    def GetPosition(self) -> wx.Point:
        return wx.Point(self.x, self.y)

    def Dragging(self) -> bool:
        return self.dragging

    def LeftIsDown(self) -> bool:
        return self.left_down

    def Skip(self) -> None:
        pass


def grouped_preview(shape_parameters: ShapeParameters = ShapeParameters()):
    plan = resolve_effective_shape_plan(
        BaseTimingPlanInput(
            timeline=(
                VowelTimelinePoint(
                    1.0, "あ", value=0.6, start_sec=0.8, end_sec=1.1
                ),
                VowelTimelinePoint(
                    1.2, "あ", value=0.4, start_sec=1.1, end_sec=1.4
                ),
            ),
            observations=None,
            source_duration_frames=300,
            shape_parameters=shape_parameters,
        )
    )
    return plan, build_preview_data_from_effective_shape_plan(plan)


def test_grouped_non_first_event_highlight_and_summary_are_event_specific() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = wx.Frame(None)
    panel = PreviewPanel(frame)
    plan, preview = grouped_preview()
    panel.set_identity_aware_preview_data(preview, 10.0, plan.base_plan_identity.digest)
    panel.set_selected_source_event_index(1)

    segment = panel.model.find_shape_by_source_event_index(1)
    summary = panel.get_selected_shape_summary()
    assert segment is not None
    assert segment.source_event_indices == (0, 1)
    assert summary is not None
    assert "Event Index: 1" in summary
    assert "Peak: 0.40" in summary
    assert "Frame: 33 - 42" in summary

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_click_emits_canonical_request_and_empty_click_is_noop() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = wx.Frame(None)
    panel = PreviewPanel(frame)
    panel.SetSize((300, 500))
    plan, preview = grouped_preview()
    panel.set_identity_aware_preview_data(preview, 10.0, plan.base_plan_identity.digest)
    requests: list[PreviewSelectionRequest] = []
    panel.on_selection_request_callback = requests.append
    gesture = _GestureState(
        origin_x=30,
        origin_y=20,
        last_x=30,
        base_plan_identity_digest=plan.base_plan_identity.digest,
        render_revision=panel.model.render_revision,
    )

    panel._commit_click(wx.Point(30, 20), gesture)
    panel._commit_click(wx.Point(250, 450), gesture)

    assert len(requests) == 1
    assert requests[0].base_event_index == 0
    assert requests[0].base_plan_identity_digest == plan.base_plan_identity.digest
    assert requests[0].render_revision == panel.model.render_revision

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_drag_threshold_pans_only_after_cumulative_four_dip() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = wx.Frame(None)
    panel = PreviewPanel(frame)
    panel.SetSize((300, 500))
    plan, preview = grouped_preview()
    panel.set_identity_aware_preview_data(preview, 10.0, plan.base_plan_identity.digest)
    pans: list[float] = []
    panel.on_pan_callback = pans.append
    panel._gesture = _GestureState(
        origin_x=100,
        origin_y=20,
        last_x=100,
        base_plan_identity_digest=plan.base_plan_identity.digest,
        render_revision=panel.model.render_revision,
    )

    panel._on_mouse_motion(FakeMouseEvent(98, 20, dragging=True, left_down=True))
    assert pans == []
    panel._on_mouse_motion(FakeMouseEvent(95, 20, dragging=True, left_down=True))
    assert len(pans) == 1
    assert panel._gesture is not None and panel._gesture.dragging is True

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_same_identity_preserves_selection_and_changed_render_rejects_stale_request() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = wx.Frame(None)
    panel = PreviewPanel(frame)
    panel.SetSize((300, 500))
    plan, preview = grouped_preview()
    panel.set_identity_aware_preview_data(preview, 10.0, plan.base_plan_identity.digest)
    panel.set_selected_source_event_index(1)
    old_revision = panel.model.render_revision
    stale_gesture = _GestureState(
        origin_x=36,
        origin_y=20,
        last_x=36,
        base_plan_identity_digest=plan.base_plan_identity.digest,
        render_revision=old_revision,
    )
    requests: list[PreviewSelectionRequest] = []
    panel.on_selection_request_callback = requests.append

    changed_plan, changed_preview = grouped_preview(ShapeParameters(closing_hold_frames=2))
    assert changed_plan.base_plan_identity.digest == plan.base_plan_identity.digest
    panel.set_identity_aware_preview_data(
        changed_preview, 10.0, changed_plan.base_plan_identity.digest
    )
    panel._commit_click(wx.Point(36, 20), stale_gesture)

    assert panel.model.selected_source_event_index == 1
    assert panel.model.render_revision == old_revision + 1
    assert requests == []

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_mainframe_commits_current_request_and_rejects_stale_revision() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = MainFrame(None)
    plan, _ = grouped_preview()
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
                VowelTimelinePoint(1.0, "あ", value=0.6, start_sec=0.8, end_sec=1.1),
                VowelTimelinePoint(1.2, "あ", value=0.4, start_sec=1.1, end_sec=1.4),
            ],
            anchors=[],
            source="test",
            observations=None,
        )
    )
    frame.sync_ui_state()
    model = frame.placeholder_container.pnl_preview.model
    request = PreviewSelectionRequest(
        1,
        model.base_plan_identity_digest,
        model.render_revision,
    )

    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_info
    )
    frame._on_preview_selection_request(request)
    assert frame.ui_state.selected_source_event_index == 1
    assert (
        frame.ui_state.selected_base_plan_identity_digest
        == model.base_plan_identity_digest
    )
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_selected_event
    )

    frame.right_pane.notebook.ChangeSelection(
        frame.right_pane.notebook.FindPage(frame.right_pane.panel_info)
    )
    frame._on_preview_selection_request(request)
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_selected_event
    )

    frame.right_pane.notebook.ChangeSelection(
        frame.right_pane.notebook.FindPage(frame.right_pane.panel_warning)
    )
    frame.sync_ui_state()
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_warning
    )
    model = frame.placeholder_container.pnl_preview.model
    stale_request = PreviewSelectionRequest(
        0,
        model.base_plan_identity_digest,
        model.render_revision - 1,
    )
    frame._on_preview_selection_request(stale_request)
    assert frame.ui_state.selected_source_event_index == 1
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_warning
    )

    current_request = PreviewSelectionRequest(
        0,
        model.base_plan_identity_digest,
        model.render_revision,
    )
    frame.ui_state.set_busy(True)
    frame._on_preview_selection_request(current_request)
    assert frame.ui_state.selected_source_event_index == 1
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_warning
    )
    frame.ui_state.set_busy(False)

    invalid_request = PreviewSelectionRequest(
        999,
        model.base_plan_identity_digest,
        model.render_revision,
    )
    frame._on_preview_selection_request(invalid_request)
    assert frame.ui_state.selected_source_event_index == 1
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_warning
    )

    identity_mismatch_request = PreviewSelectionRequest(
        0,
        "stale-base-identity",
        model.render_revision,
    )
    frame._on_preview_selection_request(identity_mismatch_request)
    assert frame.ui_state.selected_source_event_index == 1
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_warning
    )

    frame.clear_selected_event()
    assert frame.ui_state.selected_source_event_index is None
    assert (
        frame.right_pane.notebook.GetCurrentPage()
        is frame.right_pane.panel_warning
    )
    assert plan.base_plan_identity.digest == model.base_plan_identity_digest

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_selected_renderer_resolves_theme_palette_in_lane_draw() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = wx.Frame(None)
    panel = PreviewPanel(frame)
    plan, preview = grouped_preview()
    panel.set_identity_aware_preview_data(preview, 10.0, plan.base_plan_identity.digest)
    panel.set_selected_source_event_index(0)
    gc = Mock()
    gc.CreatePath.return_value = Mock()

    PreviewRenderer(panel.model)._draw_lanes(gc, wx.Rect(0, 0, 300, 500))

    assert gc.SetPen.called
    destroy_wx_app(app, frame, owns_app=owns_app)
