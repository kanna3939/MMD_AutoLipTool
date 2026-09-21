from __future__ import annotations

from dataclasses import dataclass, replace

import wx

from gui_wx.main_frame import MainFrame
from gui_wx.selected_event_editor import SelectedEventEditRequest
from gui_wx.theme import ThemeManager
from src.core.audio_processing import WavAnalysisResult
from src.core.pipeline import VowelTimingPlan
from src.core.generation_presets import GenerationSettings
from src.core.output_edit_state import GenerationState
from src.core.preview_hit_test import PreviewSelectionRequest
from src.vmd_writer import VowelTimelinePoint
from tests.helpers import destroy_wx_app, get_or_create_wx_app


@dataclass
class FakeEvent:
    def Skip(self) -> None:
        pass


def make_ready_frame(
    *,
    timeline: list[VowelTimelinePoint] | None = None,
    hold_frames: int | None = None,
    softness_frames: int | None = None,
) -> MainFrame:
    frame = MainFrame(None)
    if hold_frames is not None:
        frame.set_closing_hold_frames(hold_frames)
    if softness_frames is not None:
        frame.set_closing_softness_frames(softness_frames)
    if hold_frames is not None or softness_frames is not None:
        frame.apply_generation_state(
            GenerationState(
                GenerationSettings(
                    closing_hold_frames=hold_frames or 0,
                    closing_softness_frames=softness_frames or 0,
                )
            )
        )
    frame.ui_state.selected_text_path = "input.txt"
    frame.ui_state.selected_text_content = "あ"
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
            vowels=["あ", "あ"],
            timeline=(
                timeline
                if timeline is not None
                else [
                    VowelTimelinePoint(
                        1.0,
                        "あ",
                        value=0.6,
                        start_sec=0.8,
                        end_sec=1.1,
                    ),
                    VowelTimelinePoint(
                        1.2,
                        "あ",
                        value=0.4,
                        start_sec=1.1,
                        end_sec=1.4,
                    ),
                ]
            ),
            anchors=[],
            source="test",
            observations=None,
        ),
        analysis_text_content="あ",
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


def test_editor_controls_process_enter_and_emit_one_typed_request() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 1)
    pane = frame.right_pane
    requests = []
    original_callback = pane.on_selected_event_edit_callback
    pane.on_selected_event_edit_callback = (
        lambda request: (
            requests.append(request),
            original_callback(request),
        )
    )

    for control in pane._selected_editor_controls.values():
        assert control.GetWindowStyleFlag() & wx.TE_PROCESS_ENTER

    pane._selected_editor_controls["peak_value"].ChangeValue("0.8")
    pane._commit_selected_editor_control(FakeEvent(), "peak_value")
    pane._commit_selected_editor_control(FakeEvent(), "peak_value")

    assert len(requests) == 1
    assert requests[0].field == "peak_value"
    assert requests[0].value == 0.8

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_mainframe_edit_updates_preview_and_blocks_vmd_save_from_one_snapshot() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 1)
    editor_state = frame.right_pane._selected_editor_state
    assert editor_state is not None
    old_revision = frame.placeholder_container.pnl_preview.model.render_revision

    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=1,
            base_identity_digest=editor_state.base_identity_digest,
            editor_revision=editor_state.editor_revision,
            field="peak_value",
            value=0.8,
        )
    )

    snapshot = frame.ui_state.current_adjustment_snapshot
    diagnostics = frame.ui_state.current_output_diagnostics_snapshot
    assert snapshot is not None
    assert snapshot.adjustments[0].peak_value == 0.8
    assert frame.ui_state.selected_source_event_index == 1
    assert frame.placeholder_container.pnl_preview.model.render_revision == old_revision + 1
    assert "Peak: 0.80" in (
        frame.placeholder_container.get_selected_shape_summary() or ""
    )
    assert diagnostics is not None
    assert diagnostics.saveability.blocking_codes == ()
    assert diagnostics.adjustment_summary.adjusted_event_count == 1
    assert frame.btn_save_vmd.IsEnabled() is True
    assert frame.mi_vmd_save.IsEnabled() is True
    assert "VMD出力可能" in frame.get_status_text()

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_reset_restores_base_and_cancel_keeps_adjustment_state_contract() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 1)
    editor_state = frame.right_pane._selected_editor_state
    assert editor_state is not None
    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=1,
            base_identity_digest=editor_state.base_identity_digest,
            editor_revision=editor_state.editor_revision,
            field="peak_value",
            value=0.8,
        )
    )
    adjusted_state = frame.right_pane._selected_editor_state
    assert adjusted_state is not None

    frame.ui_state.set_busy(True)
    frame._finish_analysis_cancelled()

    assert frame.ui_state.has_event_adjustments is True
    assert frame.ui_state.selected_source_event_index == 1
    assert frame.get_status_text() == "解析をキャンセルしました"
    diagnostics = frame.ui_state.current_output_diagnostics_snapshot
    assert diagnostics is not None
    assert [item.code for item in diagnostics.items] == [
        "analysis_cancelled",
        "analysis_ready",
        "vmd_save_ready",
    ]

    current_state = frame.right_pane._selected_editor_state
    assert current_state is not None
    frame._on_selected_event_reset_request(
        current_state.base_event_index,
        current_state.base_identity_digest,
        current_state.editor_revision,
    )
    assert frame.ui_state.has_event_adjustments is False
    assert frame.btn_save_vmd.IsEnabled() is True

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_busy_and_stale_requests_do_not_change_snapshot_or_preview() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    select_event(frame, 1)
    editor_state = frame.right_pane._selected_editor_state
    assert editor_state is not None
    before = frame.ui_state.current_adjustment_snapshot
    revision = frame.placeholder_container.pnl_preview.model.render_revision
    frame.ui_state.set_busy(True)

    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=1,
            base_identity_digest=editor_state.base_identity_digest,
            editor_revision=editor_state.editor_revision,
            field="peak_value",
            value=0.9,
        )
    )
    frame.ui_state.set_busy(False)
    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=1,
            base_identity_digest=editor_state.base_identity_digest,
            editor_revision=editor_state.editor_revision + 1,
            field="peak_value",
            value=0.9,
        )
    )

    assert frame.ui_state.current_adjustment_snapshot == before
    assert frame.placeholder_container.pnl_preview.model.render_revision == revision

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_limited_effect_notice_coexists_with_operation_notice() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame(
        timeline=[
            VowelTimelinePoint(
                1.0,
                "あ",
                value=0.6,
                start_sec=0.9,
                end_sec=1.0,
            ),
            VowelTimelinePoint(
                1.1,
                "い",
                value=0.4,
                start_sec=1.1,
                end_sec=1.2,
            ),
        ],
        hold_frames=5,
        softness_frames=5,
    )
    select_event(frame, 0)
    pane = frame.right_pane
    state = pane._selected_editor_state
    assert state is not None

    assert "設定値を一部だけ反映" in (
        pane.st_selected_event_effect_notice_header.GetLabel()
    )
    assert "開口保持: 設定 5 → 反映 2 フレーム" in (
        pane.st_selected_event_effect_notice_details.GetLabel()
    )
    assert pane.st_selected_event_notice.GetLabel() == ""

    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=state.base_event_index,
            base_identity_digest=state.base_identity_digest,
            editor_revision=state.editor_revision,
            field="peak_value",
            value=0.8,
        )
    )
    assert "VMD" in pane.st_selected_event_notice.GetLabel()
    assert pane.st_selected_event_effect_notice_header.IsShown()
    assert pane.st_selected_event_effect_notice_details.IsShown()

    state = pane._selected_editor_state
    assert state is not None
    pane.set_selected_event_editor_state(
        state,
        operation_notice="閉口スムーズの変化により閉口傾斜比を解除しました。",
    )
    assert "閉口傾斜比を解除" in pane.st_selected_event_notice.GetLabel()
    assert pane.st_selected_event_effect_notice_header.IsShown()

    without_effect = replace(
        state,
        effect_notice_header="",
        effect_notice_lines=(),
    )
    pane.set_selected_event_editor_state(
        without_effect,
        operation_notice="操作結果は保持されます。",
    )
    assert pane.st_selected_event_notice.GetLabel() == "操作結果は保持されます。"
    assert not pane.st_selected_event_effect_notice_header.IsShown()
    assert not pane.st_selected_event_effect_notice_details.IsShown()

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_effect_notice_theme_and_slope_helper_styles_are_distinct() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame(
        timeline=[
            VowelTimelinePoint(
                1.0,
                "あ",
                value=0.6,
                start_sec=0.9,
                end_sec=1.0,
            ),
            VowelTimelinePoint(
                1.1,
                "い",
                value=0.4,
                start_sec=1.1,
                end_sec=1.2,
            ),
        ],
        hold_frames=5,
        softness_frames=5,
    )
    select_event(frame, 0)
    pane = frame.right_pane
    palette = ThemeManager.get_palette()

    assert (
        pane.st_selected_event_effect_notice_header.GetFont().GetWeight()
        == wx.FONTWEIGHT_BOLD
    )
    assert (
        pane.st_selected_event_effect_notice_details.GetFont().GetWeight()
        == wx.FONTWEIGHT_NORMAL
    )
    assert (
        pane.st_selected_event_effect_notice_header.GetForegroundColour()
        == palette.attention_text
    )
    assert (
        pane.st_selected_event_effect_notice_details.GetForegroundColour()
        == palette.attention_text
    )
    assert (
        pane._selected_editor_effective_labels[
            "hold_frames"
        ].GetForegroundColour()
        == palette.attention_text
    )
    assert (
        pane._selected_editor_effective_labels[
            "softness_frames"
        ].GetForegroundColour()
        == palette.attention_text
    )

    helper_state = replace(
        pane._selected_editor_state,
        effect_notice_header="",
        effect_notice_lines=(),
        slope_helper_text=(
            "傾斜比を調整するには、閉口スムーズを1フレーム以上にしてください。"
        ),
    )
    pane.set_selected_event_editor_state(helper_state)
    assert pane.st_selected_event_slope_helper.IsShown()
    assert not pane.st_selected_event_effect_notice_header.IsShown()
    assert (
        pane.st_selected_event_slope_helper.GetFont().GetWeight()
        == wx.FONTWEIGHT_NORMAL
    )
    assert (
        pane.st_selected_event_slope_helper.GetForegroundColour()
        == palette.muted_text
    )

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_manual_crossfade_notice_is_separate_and_uses_attention_style() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame(
        timeline=[
            VowelTimelinePoint(
                0.3,
                "あ",
                value=0.5,
                start_sec=0.2,
                end_sec=0.4,
            ),
            VowelTimelinePoint(
                0.7,
                "い",
                value=1.0,
                start_sec=0.5,
                end_sec=0.9,
            ),
        ],
    )
    select_event(frame, 0)
    state = frame.right_pane._selected_editor_state
    assert state is not None
    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=state.base_event_index,
            base_identity_digest=state.base_identity_digest,
            editor_revision=state.editor_revision,
            field="hold_frames",
            value=6,
        )
    )
    state = frame.right_pane._selected_editor_state
    assert state is not None
    frame._on_selected_event_edit_request(
        SelectedEventEditRequest(
            base_event_index=state.base_event_index,
            base_identity_digest=state.base_identity_digest,
            editor_revision=state.editor_revision,
            field="softness_frames",
            value=2,
        )
    )

    pane = frame.right_pane
    palette = ThemeManager.get_palette()
    assert pane.st_selected_event_crossfade_notice_header.IsShown()
    assert pane.st_selected_event_crossfade_notice_details.IsShown()
    assert pane.st_selected_event_crossfade_notice_header.GetLabel() == (
        "次の口形とクロスフェードしています。"
    )
    assert "「い」の開口量が0.95以上" in (
        pane.st_selected_event_crossfade_notice_details.GetLabel()
    )
    assert not pane.st_selected_event_effect_notice_header.IsShown()
    assert (
        pane.st_selected_event_crossfade_notice_header.GetFont().GetWeight()
        == wx.FONTWEIGHT_BOLD
    )
    assert (
        pane.st_selected_event_crossfade_notice_details.GetFont().GetWeight()
        == wx.FONTWEIGHT_NORMAL
    )
    assert (
        pane.st_selected_event_crossfade_notice_header.GetForegroundColour()
        == palette.attention_text
    )
    assert (
        pane.st_selected_event_crossfade_notice_details.GetForegroundColour()
        == palette.attention_text
    )

    destroy_wx_app(app, frame, owns_app=owns_app)
