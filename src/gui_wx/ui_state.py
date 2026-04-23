from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any

class StatusKey(Enum):
    """
    [MS14-B2] Status meanings to avoid hardcoded strings spread throughout the app.
    """
    IDLE = "idle"
    INPUT_MISSING = "input_missing"
    READY_FOR_ANALYSIS = "ready_for_analysis"
    ANALYSIS_INVALIDATED = "analysis_invalidated"
    BUSY = "busy"
    ANALYSIS_READY = "analysis_ready"

@dataclass
class UiState:
    """
    [MS14-B2] Lightweight state holder for MS14 core workflow.
    """
    # Input Related
    selected_text_path: Optional[str] = None
    selected_wav_path: Optional[str] = None
    selected_text_content: str = ""
    selected_hiragana_content: str = ""
    selected_vowel_content: str = ""
    selected_wav_analysis: Any = None
    
    # MS14-B3 Session/Dialog History (Memory Only)
    recent_text_files: list[str] = field(default_factory=list)
    recent_wav_files: list[str] = field(default_factory=list)
    last_text_dialog_dir: Optional[str] = None
    last_wav_dialog_dir: Optional[str] = None
    last_vmd_output_dir: Optional[str] = None
    
    # Analysis Related
    current_timing_plan: Any = None
    analysis_result_valid: bool = False
    analysis_pending_rebuild: bool = False
    
    # UI / Application Related
    is_busy: bool = False
    status_key: StatusKey = StatusKey.IDLE
    
    # [MS15-B3] Playback State
    is_playing: bool = False
    playback_position_sec: float = 0.0
    loaded_playback_path: Optional[str] = None

    def invalidate_analysis(self):
        """
        [MS14-B2] Invalidate the current analysis results.
        Call this when inputs (paths or parameters) change.
        """
        self.analysis_result_valid = False
        self.analysis_pending_rebuild = True
        self.status_key = StatusKey.ANALYSIS_INVALIDATED

    def mark_ready_for_analysis(self):
        """
        [MS14-B2] Mark that inputs are sufficient for analysis.
        """
        self.status_key = StatusKey.READY_FOR_ANALYSIS

    def set_busy(self, is_busy: bool):
        """
        [MS14-B2] Toggle busy state.
        """
        self.is_busy = is_busy
        if is_busy:
            self.status_key = StatusKey.BUSY

    def mark_analysis_success(self, timing_plan: Any):
        """
        [MS14-B2] Mark that analysis has completed successfully.
        """
        self.current_timing_plan = timing_plan
        self.analysis_result_valid = True
        self.analysis_pending_rebuild = False
        self.status_key = StatusKey.ANALYSIS_READY
