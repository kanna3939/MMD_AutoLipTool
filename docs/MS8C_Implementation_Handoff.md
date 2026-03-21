# MS8C Implementation Handoff

## 1. Scope
MS8C introduced playback control and shared-position synchronization on top of MS8B static preview/waveform rendering.

Implemented scope:
- Phase 1: playback core files added (`playback_controller.py`, `view_sync.py`)
- Phase 2: minimum wiring in `main_window.py`
- Phase 3: Play/Stop action-state integration
- Phase 4: playback cursor path in `WaveformView`
- Phase 5: playback cursor path in `PreviewArea`
- Phase 6: status playback-frame display
- Phase 7: shared sync route unified (`controller -> view_sync -> views/status`)
- Phase 8: integrated with timing-plan invalidation route
- Phase 9: consistency across existing entry points (reload/failure/input-invalid/reanalysis-wait/silent restore)
- Phase 10: completion-condition check

## 2. Core Decisions
- Source of truth for current position: actual audio playback position
- Shared unit: seconds (absolute); frame number is derived display-only value (30fps)
- Playback start position: always `0.0` seconds
- Playback end state: stop + shared position reset to `0.0` seconds (no tail hold)
- Status responsibility: final status-priority judgment stays in `main_window.py`

## 3. Main File Responsibilities
- `src/gui/playback_controller.py`
  - Real WAV playback control (`QMediaPlayer` + `QAudioOutput`)
  - Start/stop/end handling
  - Second-based position notifications
  - Reset-to-zero behavior on start/stop/end
- `src/gui/view_sync.py`
  - Shared second-based position hub
  - Position update signal
  - Reset signal
- `src/gui/main_window.py`
  - Orchestration and wiring
  - Play/Stop action-state conditions
  - Status text generation/priority handling
  - Invalidation-route integration for playback stop/reset
- `src/gui/waveform_view.py`
  - Draw-only playback cursor receive/render/clear
- `src/gui/preview_area.py`
  - Draw-only playback cursor receive/render/clear

## 4. Completion Conditions (MS8C)
- Play enabled only after valid processing state
- Stop enabled only while playback is active
- Playback starts at `0.0` sec (frame 0 equivalent)
- Waveform / Preview / status are synchronized from the same second-based position
- On stop/end/invalidation/recovery routes, playback state is not left behind
- Existing core routes remain intact:
  - TEXT load
  - WAV load
  - Process run
  - VMD export

## 5. Explicitly Out of Scope (MS8D+)
- Zoom
- Scrub/manual seek/click seek
- Detailed frame-axis redesign
- `pipeline.py` behavior changes
- `writer.py` behavior changes
- `preview_transform.py` behavior changes
- `whisper_timing.py` behavior changes

