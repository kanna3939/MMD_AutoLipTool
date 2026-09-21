from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import wx

from gui_wx.app import AutoLipToolApp
from gui_wx.app_controller import AppController
from gui_wx.main_frame import MainFrame
from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    ShapeParameters,
    build_base_plan_identity,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import EventAdjustment, empty_adjustment_snapshot
from src.core.generation_presets import GenerationPresetStore, GenerationSettings
from src.core.generation_presets import (
    BUILTIN_LONG_VOWEL_DECAY_ID,
    BUILTIN_STANDARD_HOLD_ID,
)
from src.core.output_diagnostics import AdjustmentDiagnosticsSummary, GenerationDiagnosticsSummary
from src.core.settings_store import SettingsStore
from gui_wx.ui_sync_context import build_ui_sync_context
from src.vmd_writer import VowelTimelinePoint
from tests.test_wx_ms21_b6_undo_redo import make_ready_frame
from tests.helpers import destroy_wx_app, get_or_create_wx_app, workspace_tempdir


def test_controller_constructor_has_no_persistence_io() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    with workspace_tempdir("ms22_b4_constructor") as tmp_dir:
        settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
        preset_store = GenerationPresetStore(settings_store=settings_store)
        frame = MainFrame(None)
        controller = AppController(
            frame,
            settings_store=settings_store,
            preset_store=preset_store,
        )
        assert controller.startup_settings_result is None
        assert controller.startup_preset_result is None
        assert not settings_store.settings_path.exists()
        assert not preset_store.presets_path.exists()
        destroy_wx_app(app, frame, owns_app=owns_app)


def test_app_passes_same_temporary_stores_through_startup_seam() -> None:
    with patch("gui_wx.app.get_resource_path", return_value=Path("missing_splash.png")), \
         workspace_tempdir("ms22_b4_app_seam") as tmp_dir:
        settings_store = SettingsStore(tmp_dir / "MMD_AutoLipTool.ini")
        preset_store = GenerationPresetStore(settings_store=settings_store)
        app, owns_app = get_or_create_wx_app(
            AutoLipToolApp,
            False,
            settings_store=settings_store,
            preset_store=preset_store,
        )
        assert app.controller.settings_store is settings_store
        assert app.controller.preset_store is preset_store
        assert app.frame.ui_state.generation_state.generation_settings == GenerationSettings()
        destroy_wx_app(app, app.frame, owns_app=owns_app)


def test_output_only_generation_edit_preserves_analysis_and_is_undoable() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    old_plan = frame.ui_state.current_timing_plan
    changed = GenerationSettings(3, 4, "decay")

    assert frame.commit_generation_settings(changed, request_save=False)
    assert frame.ui_state.analysis_result_valid is True
    assert frame.ui_state.current_timing_plan is old_plan
    assert frame.ui_state.generation_state.generation_settings == changed
    assert frame.ui_state.can_undo_adjustment is True

    assert frame._perform_adjustment_history_navigation(redo=False)
    assert frame.ui_state.generation_state.generation_settings == GenerationSettings()
    assert frame.ui_state.analysis_result_valid is True
    assert frame.ui_state.current_timing_plan is old_plan
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_builtin_preset_apply_is_one_atomic_output_transaction() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    settings_before = frame.ui_state.generation_state.generation_settings
    controller = AppController(frame)
    frame.set_controller(controller)

    assert controller.apply_generation_preset(BUILTIN_LONG_VOWEL_DECAY_ID)
    assert frame.ui_state.generation_state.active_preset_id == BUILTIN_LONG_VOWEL_DECAY_ID
    assert frame.ui_state.generation_state.generation_settings.long_vowel_mode == "decay"
    assert frame.ui_state.analysis_result_valid is True
    assert frame.ui_state.current_adjustment_snapshot is not None
    assert frame.ui_state.can_undo_adjustment is True

    assert frame._perform_adjustment_history_navigation(redo=False)
    assert frame.ui_state.generation_state.generation_settings == settings_before
    assert frame.ui_state.generation_state.active_preset_id is None
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_direct_generation_change_moves_active_preset_to_custom() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    controller = AppController(frame)
    frame.set_controller(controller)

    assert controller.apply_generation_preset(BUILTIN_LONG_VOWEL_DECAY_ID)
    current = frame.ui_state.generation_state.generation_settings
    changed = GenerationSettings(
        closing_hold_frames=current.closing_hold_frames + 1,
        closing_softness_frames=current.closing_softness_frames,
        long_vowel_mode=current.long_vowel_mode,
    )
    assert frame.commit_generation_settings(changed, request_save=False)
    assert frame.ui_state.generation_state.active_preset_id is None
    assert frame._active_preset_display_name is None
    destroy_wx_app(app, frame, owns_app=owns_app)


def test_id_only_preset_undo_resolves_against_current_output_state() -> None:
    app, owns_app = get_or_create_wx_app(wx.App, False)
    frame = make_ready_frame()
    controller = AppController(frame)
    frame.set_controller(controller)

    with patch(
        "gui_wx.main_frame.resolve_effective_shape_plan",
        wraps=resolve_effective_shape_plan,
    ) as commit_resolver, patch(
        "gui_wx.ui_sync_context.resolve_effective_shape_plan",
        wraps=resolve_effective_shape_plan,
    ) as sync_resolver:
        assert controller.apply_generation_preset(BUILTIN_STANDARD_HOLD_ID)
        assert commit_resolver.call_count == 1
        sync_resolver.reset_mock()

        assert frame._perform_adjustment_history_navigation(redo=False)
        assert sync_resolver.call_count == 1

    destroy_wx_app(app, frame, owns_app=owns_app)


def test_none_adjustment_is_not_a_wildcard_for_non_empty_hint() -> None:
    base = BaseTimingPlanInput(
        timeline=(VowelTimelinePoint(0.5, "あ", value=0.5, start_sec=0.4, end_sec=0.6),),
        observations=None,
        source_duration_frames=30,
        shape_parameters=ShapeParameters(),
    )
    identity = build_base_plan_identity(base)
    non_empty = empty_adjustment_snapshot(identity)
    # The empty snapshot is replaced below with a non-empty adjustment while
    # keeping the same base identity.
    non_empty = non_empty.__class__(
        non_empty.schema_version,
        identity,
        (EventAdjustment(base_event_index=0, peak_value=0.8),),
    )
    hint = resolve_effective_shape_plan(base, non_empty)
    with pytest.raises(ValueError, match="adjustment snapshot mismatch"):
        build_ui_sync_context(base, None, effective_plan_hint=hint)


def test_diagnostics_dto_invariants_reject_invalid_generation_values() -> None:
    with pytest.raises(ValueError):
        GenerationDiagnosticsSummary(
            "AutoLipTool", 0, 0, "schema", active_long_vowel_mode="invalid"
        )
    with pytest.raises(ValueError):
        GenerationDiagnosticsSummary(
            "AutoLipTool", 0, 0, "schema", active_preset_id="id"
        )
    with pytest.raises(ValueError):
        AdjustmentDiagnosticsSummary(long_vowel_mode_override_count=-1)
