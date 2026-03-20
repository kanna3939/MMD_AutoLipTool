# MS8A Phase1 UI Partition

## Scope
- Phase1 performs only UI partitioning and responsibility clarification for `src/gui/main_window.py`.
- No runtime behavior changes, no signal destination changes, no layout reimplementation.
- No new GUI component files in this phase (`operation_panel.py`, `status_panel.py` are future work).
- `WaveformView` is treated as an existing reusable display component and is not modified.

## Current UI Inventory
- Root layout in `MainWindow.__init__`: `QVBoxLayout` with menu bar.
- Current widget creation (main targets):
  - Buttons: `text_button`, `wav_button`, `process_button`, `output_button`
  - Morph UI: `morph_upper_limit_label`, `morph_upper_limit_input`
  - Status label: `output_status_label`
  - Text/display widgets: `text_path_label`, `wav_path_label`, `text_preview_label`, `text_preview`, `hiragana_preview_label`, `hiragana_preview`, `vowel_preview_label`, `vowel_preview`, `wav_info_label`, `wav_waveform_view`
- Current vertical placement order (top to bottom, excluding menu):
  1. `text_button`
  2. `text_path_label`
  3. `text_preview_label`
  4. `text_preview`
  5. `hiragana_preview_label`
  6. `hiragana_preview`
  7. `vowel_preview_label`
  8. `vowel_preview`
  9. `wav_button`
  10. `wav_path_label`
  11. `wav_info_label`
  12. `wav_waveform_view`
  13. `process_button`
  14. `morph_upper_limit_layout` (`label + input`)
  15. `output_button`
  16. `output_status_label`

## Mapping to v3 Layout
- `mockup_sample_v3.png` and `Specification_Prompt_v3.md` indicate a top operation row, morph row, left/right center area, and bottom status area.

| v3 layout region | Current elements to map |
| --- | --- |
| Top operation row | `text_button`, `wav_button`, `process_button`, `output_button` (plus future placeholders: Play/Stop/Zoom in Phase2+) |
| Row below operation (morph) | `morph_upper_limit_label`, `morph_upper_limit_input` |
| Center left column | `text_path_label`, `wav_path_label`, `text_preview_label`, `text_preview`, `hiragana_preview_label`, `hiragana_preview`, `vowel_preview_label`, `vowel_preview`, `wav_info_label` |
| Center right upper | `wav_waveform_view` (`WaveformView`) |
| Center right lower (future area) | No current dedicated widget; reserve placeholder container in later phase |
| Bottom status bar | `output_status_label` (replacement target for future `StatusPanel`) |

## Existing Connections to Preserve
- Button signal connections:
  - `text_button.clicked -> _open_text_file`
  - `wav_button.clicked -> _open_wav_file`
  - `process_button.clicked -> _run_processing_requested`
  - `output_button.clicked -> _save_vmd_file`
  - `morph_upper_limit_input.valueChanged -> _on_morph_upper_limit_changed`
- Shared entry design that must remain:
  - `_open_text_file` -> `_select_text_file`
  - `_open_wav_file` -> `_select_wav_file`
  - `_run_processing_requested` and `_run_reanalysis_requested` -> `_run_processing`
  - `_save_vmd_file` -> `_export_vmd`
- Menu linkage to keep consistent with button entry points:
  - Open TEXT/WAV, Run/Reanalyze, Save VMD are routed to same entry methods.

## State/Status Update Paths to Preserve
- Action enable/disable control root:
  - `_update_action_states()` -> `_build_normal_action_states()` -> `_apply_processing_lock_overrides()` -> `_apply_action_states()`
- `_apply_action_states()` currently controls:
  - Buttons: `text_button`, `wav_button`, `process_button`, `output_button`
  - Menu actions: `action_open_text`, `action_open_wav`, `action_run_processing`, `action_reanalyze`, `action_save_vmd`
  - Recent menus and each recent action
  - `morph_upper_limit_input`
- Processing session lock/status flow:
  - `_run_processing()` -> `_begin_processing_session()` -> `_refresh_waveform_morph_labels()` -> `_set_ready_status()` -> `finally _end_processing_session()`
  - `_begin_processing_session()` sets busy flag, updates actions, sets processing status, shows progress dialog.
  - `_end_processing_session()` hides dialog, clears busy flag, restores status when needed, updates actions.
- Status text update entry points to preserve:
  - `_set_ready_status()`
  - `_show_warning(..., status=...)`
  - `_begin_processing_session()` / `_end_processing_session()`
  - `_export_vmd()` completion/cancel/failure paths
  - TEXT/WAV load success and failure paths via `_set_ready_status()` and `_show_warning()`

## Morph Upper Limit Handling
- Current UI and value source:
  - UI: `morph_upper_limit_input` (`QDoubleSpinBox`)
  - Value accessor: `_current_upper_limit()`
- Preserve current value-change behavior (no auto re-run):
  - `_on_morph_upper_limit_changed()`:
    - `current_timing_plan = None`
    - `wav_waveform_view.clear_morph_labels()`
    - `_set_ready_status()` to return to reanalysis-waiting state
- Preserve current usage points:
  - Processing path: `build_vowel_timing_plan(..., upper_limit=self._current_upper_limit())`
  - Export path: `generate_vmd_from_text_wav(..., upper_limit=self._current_upper_limit())`

## Candidates for Future Extraction
- Candidate extraction to `OperationPanel` (display-focused only):
  - `text_button`, `wav_button`, `process_button`, `output_button`
  - Future placeholder buttons: Play/Stop/Zoom In/Zoom Out
  - Minimal API needed in later phase: button state reflection + signal exposure
- Candidate extraction to `StatusPanel` (display-focused only):
  - `output_status_label` display sink (replace `_set_output_status` target)
- Responsibilities that must stay in `main_window.py`:
  - State judgment (`can_run`, `can_save`, processing lock)
  - Processing/input/output orchestration and guard checks
  - Status transition decisions
  - Morph upper limit invalidation and reanalysis-wait transition
  - Menu and recent-file integration
- Phase2+ planned changes (not now):
  - Physical swap of top row to `OperationPanel`
  - Physical swap of status sink to `StatusPanel`
  - Two-column center layout and right-lower placeholder container introduction

## Out of Scope in This Phase
- Adding `operation_panel.py`, `status_panel.py`, `preview_area.py`, or any other new GUI module.
- Rewriting `main_window.py` layout implementation.
- Any signal reconnection that changes destinations.
- Any runtime behavior change in text/wav/process/export flow.
- Any change in `waveform_view.py` drawing responsibility.
- Preview rendering, playback control, zoom logic, i18n, persistence, or `core/*` responsibility changes.

## Phase10 Sync Note (Post-Implementation)
- MS8A phases 1-9 are now applied in code:
  - Top operation row is handled by `OperationPanel`.
  - Morph upper-limit UI is directly below the operation row.
  - Center area is split into two columns (left info/text, right waveform + lower placeholder).
  - Bottom status area uses `StatusPanel` as the single display sink.
- Existing orchestration remains in `main_window.py`:
  - State judgment (`_update_action_states`) and status decision paths stay in `main_window.py`.
  - `OperationPanel` and `StatusPanel` remain display-focused components.
- Preserved behavior confirmed for MS8A scope:
  - Main flow: TEXT load -> WAV load -> processing -> VMD export.
  - Safety flow: processing lock, re-entry prevention, save guard before analysis, morph upper-limit change returning to reanalysis-wait state.
- Deferred to later milestones (kept out of MS8A):
  - Preview area implementation, playback controls, zoom behavior, i18n, settings persistence, and output-quality expansion.
