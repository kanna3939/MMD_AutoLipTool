from __future__ import annotations

from gui_wx.ui_state import UiState


def commit(state: UiState, index: object = 1, requested: str = "base-a", current: str = "base-a") -> bool:
    return state.commit_selected_source_event_index(
        index,
        requested_base_plan_identity_digest=requested,
        current_base_plan_identity_digest=current,
        valid_base_event_indices=(0, 1, 2),
    )


def test_canonical_commit_updates_index_and_identity_together() -> None:
    state = UiState()
    assert commit(state) is True
    assert state.selected_source_event_index == 1
    assert state.selected_base_plan_identity_digest == "base-a"


def test_invalid_or_stale_commit_is_noop() -> None:
    state = UiState()
    assert commit(state) is True
    assert commit(state, 9) is False
    assert commit(state, 2, requested="base-old") is False
    assert commit(state, True) is False
    assert state.selected_source_event_index == 1
    assert state.selected_base_plan_identity_digest == "base-a"


def test_busy_commit_is_noop() -> None:
    state = UiState(is_busy=True)
    assert commit(state) is False
    assert state.selected_source_event_index is None
    assert state.selected_base_plan_identity_digest is None


def test_legacy_setter_remains_permissive_and_clears_canonical_identity() -> None:
    state = UiState()
    assert commit(state) is True
    state.set_selected_source_event_index(999)
    assert state.selected_source_event_index == 999
    assert state.selected_base_plan_identity_digest is None
    state.clear_selection()
    assert state.selected_source_event_index is None
    assert state.selected_base_plan_identity_digest is None
