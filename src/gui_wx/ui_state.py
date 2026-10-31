from enum import Enum
from dataclasses import dataclass, field, replace
from typing import Optional, Any

from gui_wx.worker_state import AudioWorkerStatus
from src.core import (
    DiagnosticFailureInput,
    OutputDiagnosticsSnapshot,
    GenerationState,
    OutputEditState,
    OutputEditHistoryState,
    build_output_edit_state,
    commit_output_edit_state as commit_output_history_state,
    finish_output_edit_coalescing as finish_output_history_coalescing,
    finish_current_output_edit_coalescing as finish_current_output_history_coalescing,
    initialize_output_edit_history,
    normalize_output_edit_history_state,
    redo_output_edit_state as redo_output_history_state,
    undo_output_edit_state as undo_output_history_state,
)
from src.core.generation_presets import GenerationSettings
from src.core.event_adjustment import AdjustmentContractError, AdjustmentLayerSnapshot
from src.core.final_output_state import FinalOutputState
from src.core.output_edit_draft import (
    OutputEditDraftBaseline,
    semantic_output_edit_key,
    source_event_keys,
)
from src.core.model_profile_state import (
    ModelProfileResolutionStatus,
    ModelProfileState,
)
from src.core.whisper_model_store import ModelAvailability
from src.core.whisper_models import WhisperModelSpec
from src.core.event_adjustment_history import (
    AdjustmentCoalescingKey,
    AdjustmentHistoryState,
    commit_adjustment_snapshot as commit_history_snapshot,
    finish_adjustment_coalescing as finish_history_coalescing,
    finish_current_adjustment_coalescing as finish_current_history_coalescing,
    initialize_adjustment_history as initialize_history,
    redo_adjustment_snapshot as redo_history_snapshot,
    undo_adjustment_snapshot as undo_history_snapshot,
    AdjustmentHistoryTransaction,
    PendingAdjustmentHistoryEdit,
    normalize_profile_aware_output_edit_history_state,
)

INPUT_MODE_TEXT_AUDIO = "text_audio"
INPUT_MODE_VOICE_ONLY = "voice_only"

WHISPER_AVAILABILITY_SCAN_IDLE = "idle"
WHISPER_AVAILABILITY_SCAN_PENDING = "pending"
WHISPER_AVAILABILITY_SCAN_SUCCEEDED = "succeeded"
WHISPER_AVAILABILITY_SCAN_FAILED = "failed"

WHISPER_MANAGEMENT_OPERATION_IDLE = "idle"
WHISPER_MANAGEMENT_OPERATION_DOWNLOAD = "download"
WHISPER_MANAGEMENT_OPERATION_DELETE = "delete"
WHISPER_MANAGEMENT_OPERATION_APPLY = "apply"
WHISPER_MANAGEMENT_PHASE_IDLE = "idle"
WHISPER_MANAGEMENT_PHASE_PREFLIGHT = "preflight"
WHISPER_MANAGEMENT_PHASE_DOWNLOADING = "downloading"
WHISPER_MANAGEMENT_PHASE_VERIFYING = "verifying"
WHISPER_MANAGEMENT_PHASE_CANCELLING = "cancelling"
WHISPER_MANAGEMENT_PHASE_BLOCKED = "blocked"
WHISPER_MANAGEMENT_PHASE_FINISHED = "finished"
WHISPER_FAILURE_CLASSES = frozenset(
    {
        "none",
        "model_unavailable",
        "integrity_mismatch",
        "load_failure",
        "memory_failure",
        "transcribe_failure",
        "cancelled",
    }
)


def format_whisper_failure_notice(failure_code: str | None) -> str:
    """Return a safe user-facing notice without exposing technical detail."""
    messages = {
        "storage_path_invalid": (
            "Whisperモデルの保存先を確認できません。保存先の設定を見直してください。"
        ),
        "storage_path_remote": (
            "Whisperモデルの保存先にネットワーク上の場所は指定できません。"
        ),
        "manifest_invalid": (
            "Whisperモデルの定義を確認できません。アプリケーションを確認してください。"
        ),
        "manifest_version_mismatch": (
            "Whisperモデルの定義とアプリケーションの対応バージョンが一致しません。"
        ),
        "availability_scan_failed": (
            "Whisperモデルの保存状態を確認できませんでした。保存先を確認してください。"
        ),
        "download_redirect_rejected": (
            "Whisperモデルの接続先が公式URLと一致しないため、取得を中止しました。"
        ),
        "download_content_length_invalid": (
            "Whisperモデルのサイズ情報を確認できないため、取得を中止しました。"
        ),
        "download_content_length_mismatch": (
            "Whisperモデルのサイズが定義と一致しないため、取得を中止しました。"
        ),
        "download_short_read": (
            "Whisperモデルの取得が途中で終わったため、取得を完了できませんでした。"
        ),
        "download_overrun": (
            "Whisperモデルの受信サイズが定義を超えたため、取得を中止しました。"
        ),
        "download_connection_failed": (
            "Whisperモデルに接続できませんでした。ネットワーク状態を確認してください。"
        ),
        "download_read_failed": (
            "Whisperモデルの受信に失敗しました。もう一度お試しください。"
        ),
        "download_worker_failed": (
            "Whisperモデルの取得処理が予期せず終了しました。もう一度お試しください。"
        ),
        "storage_preflight_failed": (
            "Whisperモデルの保存先を準備できないため、取得を開始できませんでした。"
        ),
        "storage_not_writable": (
            "Whisperモデルの保存先へ書き込めません。別の保存先を選択してください。"
        ),
        "storage_free_space_insufficient": (
            "Whisperモデルの保存に必要な空き容量がありません。"
        ),
        "storage_free_space_unknown": (
            "Whisperモデル保存先の空き容量を確認できません。"
        ),
        "storage_write_failed": (
            "Whisperモデルを保存できませんでした。保存先を確認してください。"
        ),
        "model_promote_failed": (
            "Whisperモデルの検証済み保存に失敗しました。もう一度お試しください。"
        ),
        "cleanup_failed": (
            "取得を中止しましたが、一時ファイルの削除を完了できませんでした。"
        ),
        "delete_blocked_ownership": (
            "現在の解析状態を保護するため、Whisperモデルを削除できません。"
        ),
        "delete_ownership_provider_failed": (
            "Whisperモデルの削除条件を確認できないため、削除を中止しました。"
        ),
        "delete_failed": (
            "Whisperモデルを削除できませんでした。ファイルを確認してください。"
        ),
        "settings_load_failed": (
            "現在の設定を確認できないため、保存先を変更できませんでした。"
        ),
        "settings_save_failed": (
            "保存先の設定を保存できませんでした。元の保存先を維持しています。"
        ),
        "model_unavailable": (
            "確認済みのWhisperモデルがないため、解析を開始できません。"
        ),
        "availability_scan_pending": (
            "Whisperモデルの保存状態の確認が終わっていません。"
        ),
        "model_apply_failed": (
            "Whisperモデルを適用できませんでした。現在の設定を維持します。"
        ),
        "model_apply_cancelled": (
            "Whisperモデルの適用をキャンセルしました。現在の設定を維持します。"
        ),
        "load_failed": (
            "Whisperモデルの読み込みに失敗しました。モデルを確認してください。"
        ),
        "checkpoint_bytes_load_failed": (
            "Whisperモデルの読み込みに失敗しました。モデルを確認してください。"
        ),
        "whisper_version_mismatch": (
            "Whisperの対応バージョンが一致しないため、解析を中止しました。"
        ),
        "integrity_mismatch": (
            "Whisperモデルの検証に失敗しました。モデルを確認してください。"
        ),
        "memory_failure": (
            "Whisperモデルを読み込むメモリが不足しました。別のモデルを選択してください。"
        ),
        "transcribe_failure": (
            "Whisperの書き起こしに失敗しました。音声とモデルを確認してください。"
        ),
        "cancelled": "解析をキャンセルしました。必要に応じて再解析してください。",
    }
    return messages.get(
        failure_code,
        "Whisperモデルの保存状態を確認できませんでした。詳細は診断情報を確認してください。",
    )


@dataclass(frozen=True)
class WhisperModelSelectionState:
    """B3 projection state for local Whisper model selection and availability."""

    model_specs: tuple[WhisperModelSpec, ...] = ()
    selected_model_key: str = "small"
    active_model_key: str = "small"
    active_manifest_identity: str = ""
    availability: tuple[ModelAvailability, ...] = ()
    availability_scan_status: str = WHISPER_AVAILABILITY_SCAN_IDLE
    availability_scan_job_id: int = 0
    availability_scan_generation: int = 0
    availability_scan_failure_code: str | None = None
    availability_scan_failure_detail: str | None = None
    storage_root_display: str = ""
    storage_location_kind: str = "unresolved"
    storage_location_display: str = "保存先を確認できません"
    active_config_status: str = "valid"
    active_config_reason: str | None = None
    loaded_whisper_model_key: str | None = None
    loaded_whisper_manifest_identity: str | None = None
    analysis_whisper_model_key: str | None = None
    analysis_whisper_manifest_identity: str | None = None
    retained_whisper_model_key: str | None = None
    retained_whisper_timing_model_identity: str | None = None
    analysis_rebuild_reason: str = "none"
    whisper_failure_class: str = "none"
    whisper_failure_detail_code: str | None = None
    whisper_failure_detail: str | None = None
    management_busy: bool = False
    management_operation: str = WHISPER_MANAGEMENT_OPERATION_IDLE
    management_phase: str = WHISPER_MANAGEMENT_PHASE_IDLE
    management_job_id: int = 0
    management_model_key: str | None = None
    management_received_bytes: int = 0
    management_expected_bytes: int = 0
    management_failure_code: str | None = None
    management_failure_detail: str | None = None
    management_cleanup_status: str | None = None
    notice: str = ""
    panel_revision: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_specs", tuple(self.model_specs))
        object.__setattr__(self, "availability", tuple(self.availability))
        if self.availability_scan_status not in {
            WHISPER_AVAILABILITY_SCAN_IDLE,
            WHISPER_AVAILABILITY_SCAN_PENDING,
            WHISPER_AVAILABILITY_SCAN_SUCCEEDED,
            WHISPER_AVAILABILITY_SCAN_FAILED,
        }:
            raise ValueError("unsupported Whisper availability scan status")
        if self.management_operation not in {
            WHISPER_MANAGEMENT_OPERATION_IDLE,
            WHISPER_MANAGEMENT_OPERATION_DOWNLOAD,
            WHISPER_MANAGEMENT_OPERATION_DELETE,
            WHISPER_MANAGEMENT_OPERATION_APPLY,
        }:
            raise ValueError("unsupported Whisper management operation")
        if self.management_phase not in {
            WHISPER_MANAGEMENT_PHASE_IDLE,
            WHISPER_MANAGEMENT_PHASE_PREFLIGHT,
            WHISPER_MANAGEMENT_PHASE_DOWNLOADING,
            WHISPER_MANAGEMENT_PHASE_VERIFYING,
            WHISPER_MANAGEMENT_PHASE_CANCELLING,
            WHISPER_MANAGEMENT_PHASE_BLOCKED,
            WHISPER_MANAGEMENT_PHASE_FINISHED,
        }:
            raise ValueError("unsupported Whisper management phase")
        for field_name in (
            "availability_scan_job_id",
            "availability_scan_generation",
            "management_job_id",
            "panel_revision",
            "management_received_bytes",
            "management_expected_bytes",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative int")
        if self.management_received_bytes > self.management_expected_bytes and self.management_expected_bytes:
            raise ValueError("management progress cannot exceed expected bytes")
        if not isinstance(self.selected_model_key, str) or not self.selected_model_key:
            raise ValueError("selected_model_key must be a non-empty string")
        if not isinstance(self.active_model_key, str) or not self.active_model_key:
            raise ValueError("active_model_key must be a non-empty string")
        if self.whisper_failure_class not in WHISPER_FAILURE_CLASSES:
            raise ValueError("unsupported Whisper failure class")
        if self.storage_location_kind not in {
            "default",
            "user_specified",
            "unresolved",
            "not_applicable",
        }:
            raise ValueError("unsupported storage location kind")
        if not isinstance(self.storage_location_display, str) or not self.storage_location_display:
            raise ValueError("storage_location_display must be a non-empty string")

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
    ANALYSIS_CANCELLED = "analysis_cancelled"
    ANALYSIS_FAILED_WITH_ROLLBACK = "analysis_failed_with_rollback"

@dataclass
class UiState:
    """
    [MS14-B2] Lightweight state holder for MS14 core workflow.
    """
    # Input Related
    selected_text_path: Optional[str] = None
    selected_wav_path: Optional[str] = None  # Legacy / Forwarding
    selected_audio_input: Any = None         # MS17-B6
    selected_audio_probe: Any = None         # MS17-B6
    selected_analysis_wav: Any = None        # MS17-B6

    selected_text_content: str = ""
    selected_hiragana_content: str = ""
    selected_vowel_content: str = ""
    selected_wav_analysis: Any = None

    # MS19-B4 Voice-only Input
    input_mode: str = INPUT_MODE_TEXT_AUDIO
    transcription_text: str = ""
    transcription_source: str = ""
    transcription_timing_source: str = ""
    transcription_original_text: str = ""
    transcription_is_edited: bool = False
    transcription_edit_dirty: bool = False
    transcription_timing_result: Any = None
    analysis_text_content: str = ""
    analysis_text_source: str = ""
    
    # MS14-B3 Session/Dialog History (Memory Only)
    recent_text_files: list[str] = field(default_factory=list)
    recent_wav_files: list[str] = field(default_factory=list)
    recent_audio_files: list[str] = field(default_factory=list) # MS17-B6
    last_text_dialog_dir: Optional[str] = None
    last_wav_dialog_dir: Optional[str] = None
    last_audio_dialog_dir: Optional[str] = None # MS17-B6
    last_vmd_output_dir: Optional[str] = None
    last_mmd_wav_export_dir: Optional[str] = None # MS17-B7
    last_mmd_wav_output_path: Optional[str] = None # MS17-B7
    
    # Analysis Related
    current_timing_plan: Any = None
    analysis_result_valid: bool = False
    analysis_pending_rebuild: bool = False
    # MS28-B3: session-only diagnostic capture.  This is intentionally not
    # part of settings/preset/profile persistence.
    debug_mode_enabled: bool = False

    # MS20-B5 workspace-local diagnostics state
    current_diagnostic_failure: Optional[DiagnosticFailureInput] = None
    current_output_diagnostics_snapshot: Optional[OutputDiagnosticsSnapshot] = None
    confirmed_warning_save_state_fingerprint: Optional[str] = None
    confirmed_shared_warning_fingerprint: Optional[str] = None
    analysis_cancelled: bool = False
    
    # UI / Application Related
    is_busy: bool = False
    status_key: StatusKey = StatusKey.IDLE
    selected_source_event_index: Optional[int] = None
    selected_base_plan_identity_digest: Optional[str] = None
    generation_state: GenerationState = field(
        default_factory=lambda: GenerationState(GenerationSettings())
    )
    model_profile_state: ModelProfileState = field(
        default_factory=lambda: ModelProfileState(
            active_model_profile_id=None,
            active_profile_baseline_preset_id=None,
            resolution_status=ModelProfileResolutionStatus.NO_PROFILE,
        )
    )
    whisper_model_selection: WhisperModelSelectionState = field(
        default_factory=WhisperModelSelectionState
    )
    active_model_profile_display_name: Optional[str] = None
    baseline_preset_display_name: Optional[str] = None
    resolved_morph_upper_limit: float = 0.9
    output_edit_history_state: Optional[OutputEditHistoryState] = None
    adjustment_history_state: Optional[AdjustmentHistoryState] = None
    output_edit_draft_baseline: OutputEditDraftBaseline | None = None
    output_edit_draft_force_apply_states: tuple[OutputEditState, ...] = ()
    output_edit_draft_timing_plan: Any = None
    output_edit_draft_timing_upper_limit: float | None = None
    output_edit_source_revision: int = 0
    output_edit_draft_revision: int = 0
    output_edit_draft_error: str | None = None
    output_edit_apply_status: str | None = None
    final_output_state: FinalOutputState = field(default_factory=FinalOutputState)
    selected_event_editor_revision: int = 0
    current_audio_job_id: int = 0
    audio_worker_state: Any = None
    
    # [MS15-B5] Theme State
    theme_mode: str = "system"
    resolved_theme: str = "dark"
    
    # [MS15-B3] Playback State
    is_playing: bool = False
    is_paused: bool = False
    playback_position_sec: float = 0.0
    loaded_playback_path: Optional[str] = None

    @property
    def playback_active(self) -> bool:
        return bool(self.is_playing or self.is_paused)

    @property
    def playback_ready(self) -> bool:
        """
        [MS15-B5] Indicates if an audio file is loaded and can be played.
        B6: check selected_analysis_wav or selected_wav_path.
        """
        return bool(self.selected_analysis_wav or self.selected_wav_path)

    @property
    def analysis_ready(self) -> bool:
        """
        [MS15-B5] Indicates if the analysis result is valid and a timing plan exists.
        """
        return self.analysis_result_valid and self.current_timing_plan is not None

    @property
    def mmd_wav_export_ready(self) -> bool:
        """
        [MS17-B7] Indicates if MMD-use WAV can be exported.
        """
        return self.selected_analysis_wav is not None

    @property
    def audio_for_analysis_ready(self) -> bool:
        """
        [MS19-B4] Indicates if the analysis worker has both an audio path and WAV analysis.
        """
        return bool(self.selected_wav_path and self.selected_wav_analysis)

    @property
    def text_audio_input_ready(self) -> bool:
        """
        [MS19-B4] TEXT + audio input contract for existing analysis.
        """
        return bool(
            self.selected_text_path
            and self.selected_text_content
            and self.audio_for_analysis_ready
        )

    @property
    def voice_only_input_ready(self) -> bool:
        """
        [MS19-B4] Audio-only input contract. TEXT remains unset.
        """
        return bool(
            self.selected_text_path is None
            and not self.selected_text_content
            and self.audio_for_analysis_ready
        )

    @property
    def analysis_start_ready(self) -> bool:
        return self.text_audio_input_ready or self.voice_only_input_ready

    @property
    def vmd_save_ready(self) -> bool:
        """
        [MS19-B6] Indicates if the current analysis result can be saved as VMD.
        """
        if not self.analysis_ready or self.analysis_pending_rebuild:
            return False
        timeline = getattr(self.current_timing_plan, "timeline", None)
        if timeline is not None and not timeline:
            return False
        if self.input_mode == INPUT_MODE_TEXT_AUDIO:
            return bool(self.selected_text_path)
        if self.input_mode == INPUT_MODE_VOICE_ONLY:
            return bool(
                self.current_timing_plan
                and (self.analysis_text_content or self.transcription_text)
                and (self.selected_wav_path or self.selected_analysis_wav)
            )
        return False

    def refresh_input_mode(self):
        """
        [MS19-B4] Resolve current input mode from loaded inputs.
        """
        if self.selected_text_path or self.selected_text_content:
            self.input_mode = INPUT_MODE_TEXT_AUDIO
        elif self.audio_for_analysis_ready:
            self.input_mode = INPUT_MODE_VOICE_ONLY
        else:
            self.input_mode = INPUT_MODE_TEXT_AUDIO

    def clear_transcription_state(self):
        self.transcription_text = ""
        self.transcription_source = ""
        self.transcription_timing_source = ""
        self.transcription_original_text = ""
        self.transcription_is_edited = False
        self.transcription_edit_dirty = False
        self.transcription_timing_result = None
        self.analysis_text_content = ""
        self.analysis_text_source = ""

    def clear_output_diagnostics_state(self):
        """Discard diagnostics derived from the previous analysis state."""
        self.current_diagnostic_failure = None
        self.current_output_diagnostics_snapshot = None
        self.confirmed_warning_save_state_fingerprint = None
        self.confirmed_shared_warning_fingerprint = None
        self.analysis_cancelled = False

    @property
    def has_event_adjustments(self) -> bool:
        return bool(
            self.current_adjustment_snapshot is not None
            and self.current_adjustment_snapshot.adjustments
        )

    @property
    def current_adjustment_snapshot(self) -> Optional[AdjustmentLayerSnapshot]:
        output_history = self.output_edit_history_state
        if output_history is not None:
            return output_history.current_state.adjustment_snapshot
        history = self.adjustment_history_state
        return None if history is None else history.current_snapshot

    @property
    def current_output_edit_state(self) -> OutputEditState | None:
        history = self.output_edit_history_state
        return None if history is None else history.current_state

    @property
    def applied_output_edit_state(self) -> OutputEditState | None:
        baseline = self.output_edit_draft_baseline
        if baseline is not None:
            return baseline.output_state
        return self.current_output_edit_state

    @property
    def draft_model_profile_state(self) -> ModelProfileState:
        history = self.output_edit_history_state
        if history is not None and history.current_model_profile_state is not None:
            return history.current_model_profile_state
        return self.model_profile_state

    @property
    def output_edit_draft_dirty(self) -> bool:
        baseline = self.output_edit_draft_baseline
        current = self.current_output_edit_state
        if baseline is None or current is None:
            return False
        if any(
            current == forced_state
            for forced_state in self.output_edit_draft_force_apply_states
        ):
            return True
        try:
            current_keys = source_event_keys(
                getattr(self.current_timing_plan, "timeline", ()) or ()
            )
            if (
                baseline.source_revision != self.output_edit_source_revision
                or current_keys != baseline.source_event_keys
                or self.output_edit_draft_error is not None
            ):
                return True
            return semantic_output_edit_key(
                baseline.output_state,
                baseline.model_profile_state,
                baseline.source_event_keys,
            ) != semantic_output_edit_key(
                current,
                self.draft_model_profile_state,
                current_keys,
            )
        except (AdjustmentContractError, TypeError, ValueError):
            return True

    def initialize_output_edit_draft_baseline(self) -> bool:
        output_state = self.current_output_edit_state
        if output_state is None or not self.analysis_result_valid:
            return False
        try:
            keys = source_event_keys(
                getattr(self.current_timing_plan, "timeline", ()) or ()
            )
            baseline = OutputEditDraftBaseline(
                source_revision=self.output_edit_source_revision,
                source_event_keys=keys,
                output_state=output_state,
                model_profile_state=self.model_profile_state,
            )
        except (AdjustmentContractError, TypeError, ValueError):
            return False
        self.output_edit_draft_baseline = baseline
        self.output_edit_draft_error = None
        return True

    def mark_output_edit_draft_changed(self) -> None:
        self.output_edit_draft_revision += 1
        self.output_edit_draft_error = None
        self.output_edit_apply_status = None

    def require_output_edit_apply_for_current_state(self) -> bool:
        current = self.current_output_edit_state
        if current is None or not self.analysis_result_valid:
            return False
        if not any(
            current == forced_state
            for forced_state in self.output_edit_draft_force_apply_states
        ):
            self.output_edit_draft_force_apply_states = (
                *self.output_edit_draft_force_apply_states,
                current,
            )
        self.output_edit_draft_error = None
        self.output_edit_apply_status = None
        return True

    def clear_output_edit_draft(self, *, source_changed: bool = False) -> None:
        self.output_edit_draft_baseline = None
        self.output_edit_draft_force_apply_states = ()
        self.output_edit_draft_timing_plan = None
        self.output_edit_draft_timing_upper_limit = None
        self.output_edit_draft_error = None
        self.output_edit_apply_status = None
        self.output_edit_draft_revision += 1
        if source_changed:
            self.output_edit_source_revision += 1

    @property
    def can_undo_adjustment(self) -> bool:
        if self.output_edit_history_state is not None:
            return self.output_edit_history_state.can_undo
        history = self.adjustment_history_state
        return bool(history is not None and history.can_undo)

    @property
    def can_redo_adjustment(self) -> bool:
        if self.output_edit_history_state is not None:
            return self.output_edit_history_state.can_redo
        history = self.adjustment_history_state
        return bool(history is not None and history.can_redo)

    @property
    def has_pending_adjustment_change(self) -> bool:
        if self.output_edit_history_state is not None:
            return self.output_edit_history_state.has_pending_change
        history = self.adjustment_history_state
        return bool(history is not None and history.has_pending_change)

    def _sync_legacy_adjustment_history(self) -> None:
        """Expose the output history through the MS21 adjustment compatibility API."""
        output_history = self.output_edit_history_state
        if output_history is None:
            self.adjustment_history_state = None
            return
        undo = tuple(
            AdjustmentHistoryTransaction(
                before_snapshot=item.before_state.adjustment_snapshot,
                after_snapshot=item.after_state.adjustment_snapshot,
            )
            for item in output_history.undo_transactions
            if item.before_state.adjustment_snapshot
            != item.after_state.adjustment_snapshot
        )
        redo = tuple(
            AdjustmentHistoryTransaction(
                before_snapshot=item.before_state.adjustment_snapshot,
                after_snapshot=item.after_state.adjustment_snapshot,
            )
            for item in output_history.redo_transactions
            if item.before_state.adjustment_snapshot
            != item.after_state.adjustment_snapshot
        )
        pending = output_history.pending_edit
        legacy_pending = None
        if pending is not None:
            legacy_pending = PendingAdjustmentHistoryEdit(
                key=pending.key,
                before_snapshot=pending.before_state.adjustment_snapshot,
                after_snapshot=pending.after_state.adjustment_snapshot,
            )
        self.adjustment_history_state = AdjustmentHistoryState(
            current_snapshot=output_history.current_state.adjustment_snapshot,
            undo_transactions=undo,
            redo_transactions=redo,
            pending_edit=legacy_pending,
        )

    def _observe_final_output_manual_snapshot(self) -> None:
        if not self.output_edit_draft_dirty:
            self.final_output_state.observe_manual_snapshot(
                self.current_adjustment_snapshot
            )

    def initialize_output_edit_history_state(self, output_state: OutputEditState) -> bool:
        try:
            self.output_edit_history_state = initialize_output_edit_history(
                output_state,
                model_profile_state=self.model_profile_state,
            )
        except (TypeError, ValueError):
            return False
        self._sync_legacy_adjustment_history()
        self._observe_final_output_manual_snapshot()
        if self.analysis_result_valid and self.output_edit_draft_baseline is None:
            self.initialize_output_edit_draft_baseline()
        return True

    def commit_output_edit_state(
        self,
        output_state: OutputEditState,
        *,
        coalesce_key: AdjustmentCoalescingKey | None = None,
        model_profile_state: ModelProfileState | None = None,
    ) -> bool:
        history = self.output_edit_history_state
        target_profile_state = (
            self.draft_model_profile_state
            if model_profile_state is None
            else model_profile_state
        )
        if history is None:
            try:
                self.output_edit_history_state = initialize_output_edit_history(
                    output_state,
                    model_profile_state=target_profile_state,
                )
            except (TypeError, ValueError):
                return False
            self._sync_legacy_adjustment_history()
            self._observe_final_output_manual_snapshot()
            if self.analysis_result_valid and self.output_edit_draft_baseline is None:
                self.initialize_output_edit_draft_baseline()
            return True
        try:
            updated = commit_output_history_state(
                history,
                output_state,
                coalesce_key=coalesce_key,
                model_profile_state=target_profile_state,
            )
        except (TypeError, ValueError):
            return False
        changed = (
            updated.current_state != history.current_state
            or updated.current_model_profile_state
            != history.current_model_profile_state
        )
        self.output_edit_history_state = updated
        if not self.output_edit_draft_dirty:
            self.generation_state = updated.current_state.generation_state
            if updated.current_model_profile_state is not None:
                self.model_profile_state = updated.current_model_profile_state
        elif changed:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        self._observe_final_output_manual_snapshot()
        if changed:
            self.selected_event_editor_revision += 1
        return True

    def finish_output_edit_coalescing(
        self,
        expected_coalesce_key: AdjustmentCoalescingKey,
    ) -> bool:
        history = self.output_edit_history_state
        if history is None:
            return False
        try:
            updated = finish_output_history_coalescing(history, expected_coalesce_key)
        except (TypeError, ValueError):
            return False
        changed = updated != history
        self.output_edit_history_state = updated
        if not self.output_edit_draft_dirty:
            self.generation_state = updated.current_state.generation_state
            if updated.current_model_profile_state is not None:
                self.model_profile_state = updated.current_model_profile_state
        elif changed:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        return changed

    def finish_current_output_edit_coalescing(self) -> bool:
        history = self.output_edit_history_state
        if history is None:
            return False
        try:
            updated = finish_current_output_history_coalescing(history)
        except (TypeError, ValueError):
            return False
        changed = updated != history
        self.output_edit_history_state = updated
        if not self.output_edit_draft_dirty:
            self.generation_state = updated.current_state.generation_state
            if updated.current_model_profile_state is not None:
                self.model_profile_state = updated.current_model_profile_state
        elif changed:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        return changed

    def undo_output_edit_state(self) -> bool:
        history = self.output_edit_history_state
        if history is None:
            return False
        before = (
            history.current_state,
            history.current_model_profile_state,
        )
        try:
            updated = undo_output_history_state(history)
        except (TypeError, ValueError):
            return False
        self.output_edit_history_state = updated
        if not self.output_edit_draft_dirty:
            self.generation_state = updated.current_state.generation_state
            if updated.current_model_profile_state is not None:
                self.model_profile_state = updated.current_model_profile_state
        elif (
            updated.current_state,
            updated.current_model_profile_state,
        ) != before:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        self._observe_final_output_manual_snapshot()
        if (
            updated.current_state,
            updated.current_model_profile_state,
        ) == before:
            return False
        self.selected_event_editor_revision += 1
        return True

    def redo_output_edit_state(self) -> bool:
        history = self.output_edit_history_state
        if history is None:
            return False
        before = (
            history.current_state,
            history.current_model_profile_state,
        )
        try:
            updated = redo_output_history_state(history)
        except (TypeError, ValueError):
            return False
        self.output_edit_history_state = updated
        if not self.output_edit_draft_dirty:
            self.generation_state = updated.current_state.generation_state
            if updated.current_model_profile_state is not None:
                self.model_profile_state = updated.current_model_profile_state
        elif (
            updated.current_state,
            updated.current_model_profile_state,
        ) != before:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        self._observe_final_output_manual_snapshot()
        if (
            updated.current_state,
            updated.current_model_profile_state,
        ) == before:
            return False
        self.selected_event_editor_revision += 1
        return True

    def normalize_output_edit_history(self, normalize_generation_state) -> bool:
        history = self.output_edit_history_state
        if history is None:
            return False
        try:
            normalized = normalize_output_edit_history_state(
                history,
                normalize_generation_state,
            )
        except (TypeError, ValueError):
            return False
        changed = normalized != history
        self.output_edit_history_state = normalized
        if not self.output_edit_draft_dirty:
            self.generation_state = normalized.current_state.generation_state
            if normalized.current_model_profile_state is not None:
                self.model_profile_state = normalized.current_model_profile_state
        elif changed:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        self._observe_final_output_manual_snapshot()
        return changed

    def normalize_profile_aware_output_edit_history(self, resolve_endpoint) -> bool:
        history = self.output_edit_history_state
        if history is None:
            return False
        try:
            normalized = normalize_profile_aware_output_edit_history_state(
                history,
                resolve_endpoint,
            )
        except (TypeError, ValueError):
            return False
        changed = normalized != history
        self.output_edit_history_state = normalized
        if not self.output_edit_draft_dirty:
            self.generation_state = normalized.current_state.generation_state
            if normalized.current_model_profile_state is not None:
                self.model_profile_state = normalized.current_model_profile_state
        elif changed:
            self.mark_output_edit_draft_changed()
        self._sync_legacy_adjustment_history()
        self._observe_final_output_manual_snapshot()
        if self.analysis_result_valid and self.output_edit_draft_baseline is None:
            self.initialize_output_edit_draft_baseline()
        return changed

    def initialize_adjustment_history(
        self,
        snapshot: AdjustmentLayerSnapshot,
        *,
        expected_base_plan_identity_digest: str,
        model_profile_state: ModelProfileState | None = None,
    ) -> bool:
        if not isinstance(snapshot, AdjustmentLayerSnapshot):
            return False
        if (
            not expected_base_plan_identity_digest
            or snapshot.base_plan_identity.digest
            != expected_base_plan_identity_digest
        ):
            return False
        try:
            history = initialize_history(snapshot)
        except (TypeError, ValueError):
            return False
        previous = self.current_adjustment_snapshot
        target_profile_state = (
            self.model_profile_state
            if model_profile_state is None
            else model_profile_state
        )
        try:
            output_state = build_output_edit_state(
                base_plan_identity=snapshot.base_plan_identity,
                adjustment_snapshot=snapshot,
                generation_state=self.generation_state,
                morph_upper_limit=self.resolved_morph_upper_limit,
            )
            self.output_edit_history_state = initialize_output_edit_history(
                output_state,
                model_profile_state=target_profile_state,
            )
            self._sync_legacy_adjustment_history()
        except (TypeError, ValueError):
            self.output_edit_history_state = None
            self.adjustment_history_state = history
        self._observe_final_output_manual_snapshot()
        if self.analysis_result_valid and self.output_edit_draft_baseline is None:
            self.initialize_output_edit_draft_baseline()
        if previous != snapshot:
            self.selected_event_editor_revision += 1
        return True

    def commit_adjustment_snapshot(
        self,
        snapshot: AdjustmentLayerSnapshot,
        *,
        expected_base_plan_identity_digest: str,
        coalesce_key: AdjustmentCoalescingKey | None = None,
    ) -> bool:
        if not isinstance(snapshot, AdjustmentLayerSnapshot):
            return False
        if (
            not expected_base_plan_identity_digest
            or snapshot.base_plan_identity.digest
            != expected_base_plan_identity_digest
        ):
            return False
        history = self.adjustment_history_state
        output_history = self.output_edit_history_state
        if output_history is not None:
            try:
                output_state = build_output_edit_state(
                    base_plan_identity=snapshot.base_plan_identity,
                    adjustment_snapshot=snapshot,
                    generation_state=output_history.current_state.generation_state,
                    morph_upper_limit=output_history.current_state.morph_upper_limit,
                )
            except (TypeError, ValueError):
                return False
            before = output_history.current_state
            try:
                updated = commit_output_history_state(
                    output_history,
                    output_state,
                    coalesce_key=coalesce_key,
                    model_profile_state=self.draft_model_profile_state,
                )
            except (TypeError, ValueError):
                return False
            self.output_edit_history_state = updated
            if self.output_edit_draft_baseline is not None:
                if updated.current_state != before:
                    self.mark_output_edit_draft_changed()
            elif updated.current_model_profile_state is not None:
                self.model_profile_state = updated.current_model_profile_state
            self._sync_legacy_adjustment_history()
            self._observe_final_output_manual_snapshot()
            if updated.current_state != before:
                self.selected_event_editor_revision += 1
            return True
        if history is None:
            return self.initialize_adjustment_history(
                snapshot,
                expected_base_plan_identity_digest=(
                    expected_base_plan_identity_digest
                ),
            )
        before = history.current_snapshot
        try:
            updated = commit_history_snapshot(
                history,
                snapshot,
                coalesce_key=coalesce_key,
            )
        except (TypeError, ValueError):
            return False
        self.adjustment_history_state = updated
        self._observe_final_output_manual_snapshot()
        if updated.current_snapshot != before:
            self.selected_event_editor_revision += 1
        return True

    def set_current_adjustment_snapshot(
        self,
        snapshot: AdjustmentLayerSnapshot,
        *,
        expected_base_plan_identity_digest: str,
    ) -> bool:
        return self.commit_adjustment_snapshot(
            snapshot,
            expected_base_plan_identity_digest=(
                expected_base_plan_identity_digest
            ),
        )

    def finish_adjustment_coalescing(
        self,
        expected_coalesce_key: AdjustmentCoalescingKey,
    ) -> bool:
        history = self.adjustment_history_state
        if self.output_edit_history_state is not None:
            return self.finish_output_edit_coalescing(expected_coalesce_key)
        if history is None:
            return False
        try:
            updated = finish_history_coalescing(
                history,
                expected_coalesce_key,
            )
        except (TypeError, ValueError):
            return False
        changed = updated != history
        self.adjustment_history_state = updated
        return changed

    def finish_current_adjustment_coalescing(self) -> bool:
        if self.output_edit_history_state is not None:
            return self.finish_current_output_edit_coalescing()
        history = self.adjustment_history_state
        if history is None:
            return False
        try:
            updated = finish_current_history_coalescing(history)
        except (TypeError, ValueError):
            return False
        changed = updated != history
        self.adjustment_history_state = updated
        return changed

    def undo_adjustment_snapshot(self) -> bool:
        if self.output_edit_history_state is not None:
            return self.undo_output_edit_state()
        history = self.adjustment_history_state
        if history is None:
            return False
        before = history.current_snapshot
        try:
            updated = undo_history_snapshot(history)
        except (TypeError, ValueError):
            return False
        self.adjustment_history_state = updated
        self._observe_final_output_manual_snapshot()
        if updated.current_snapshot == before:
            return False
        self.selected_event_editor_revision += 1
        return True

    def redo_adjustment_snapshot(self) -> bool:
        if self.output_edit_history_state is not None:
            return self.redo_output_edit_state()
        history = self.adjustment_history_state
        if history is None:
            return False
        before = history.current_snapshot
        try:
            updated = redo_history_snapshot(history)
        except (TypeError, ValueError):
            return False
        self.adjustment_history_state = updated
        self._observe_final_output_manual_snapshot()
        if updated.current_snapshot == before:
            return False
        self.selected_event_editor_revision += 1
        return True

    def clear_adjustment_history(self):
        self.output_edit_history_state = None
        self.adjustment_history_state = None
        self.clear_output_edit_draft(source_changed=True)
        self._observe_final_output_manual_snapshot()
        self.selected_event_editor_revision += 1

    def clear_adjustment_snapshot(self):
        self.clear_adjustment_history()

    @property
    def has_workspace_user_data(self) -> bool:
        """Return whether the current workspace warrants reset confirmation."""
        return bool(
            self.selected_text_path
            or self.selected_text_content
            or self.selected_hiragana_content
            or self.selected_vowel_content
            or self.selected_audio_input
            or self.selected_audio_probe
            or self.selected_analysis_wav
            or self.selected_wav_path
            or self.selected_wav_analysis
            or self.transcription_text
            or self.transcription_original_text
            or self.transcription_timing_result
            or self.analysis_text_content
            or self.current_timing_plan
            or self.analysis_result_valid
            or self.analysis_pending_rebuild
            or self.analysis_cancelled
            or self.has_event_adjustments
            or self.playback_active
            or self.playback_position_sec
            or self.loaded_playback_path
            or self.last_mmd_wav_output_path
        )

    def reset_workspace(self):
        """Clear current-workspace data while preserving settings and history."""
        self.final_output_state.reset()
        self.selected_text_path = None
        self.selected_wav_path = None
        self.selected_audio_input = None
        self.selected_audio_probe = None
        self.selected_analysis_wav = None
        self.selected_text_content = ""
        self.selected_hiragana_content = ""
        self.selected_vowel_content = ""
        self.selected_wav_analysis = None
        self.clear_transcription_state()

        self.current_timing_plan = None
        self.analysis_result_valid = False
        self.analysis_pending_rebuild = False
        self.clear_output_diagnostics_state()
        self.clear_adjustment_snapshot()
        self.clear_selection()
        self.audio_worker_state = None

        self.is_playing = False
        self.is_paused = False
        self.playback_position_sec = 0.0
        self.loaded_playback_path = None
        self.last_mmd_wav_output_path = None

        self.input_mode = INPUT_MODE_TEXT_AUDIO
        self.status_key = StatusKey.IDLE

    def invalidate_analysis(self):
        """
        [MS14-B2] Invalidate the current analysis results.
        Call this when inputs (paths or parameters) change.
        """
        self.final_output_state.invalidate(reason="analysis_invalidated")
        self.analysis_result_valid = False
        self.current_timing_plan = None
        self.analysis_pending_rebuild = True
        self.clear_output_diagnostics_state()
        self.clear_adjustment_snapshot()
        self.clear_output_edit_draft(source_changed=True)
        self.status_key = StatusKey.ANALYSIS_INVALIDATED
        self.clear_selection()

    def mark_ready_for_analysis(self):
        """
        [MS14-B2] Mark that inputs are sufficient for analysis.
        """
        self.status_key = StatusKey.READY_FOR_ANALYSIS

    def set_busy(
        self,
        is_busy: bool,
        *,
        preserve_final_output_context: bool = False,
    ):
        """
        [MS14-B2] Toggle busy state.
        """
        if is_busy:
            self.finish_current_adjustment_coalescing()
            if not self.is_busy and not preserve_final_output_context:
                self.final_output_state.invalidate_context()
        self.is_busy = is_busy
        if is_busy:
            self.status_key = StatusKey.BUSY

    def next_audio_job_id(self) -> int:
        self.current_audio_job_id += 1
        return self.current_audio_job_id

    def invalidate_audio_job(self) -> int:
        return self.next_audio_job_id()

    def is_current_audio_job(self, audio_job_id: int) -> bool:
        return self.current_audio_job_id == audio_job_id

    @property
    def audio_worker_active(self) -> bool:
        worker_state = self.audio_worker_state
        return bool(worker_state and worker_state.is_active)

    @property
    def audio_worker_cancel_available(self) -> bool:
        worker_state = self.audio_worker_state
        return bool(
            worker_state
            and worker_state.is_active
            and worker_state.status != AudioWorkerStatus.FINALIZING
        )

    def mark_analysis_success(
        self,
        timing_plan: Any,
        *,
        input_mode: str | None = None,
        analysis_text_content: str = "",
        analysis_text_source: str = "",
        transcription_text: str = "",
        transcription_source: str = "",
        transcription_timing_source: str = "",
        transcription_original_text: str | None = None,
        transcription_is_edited: bool = False,
        transcription_timing_result: Any = None,
    ):
        """
        [MS14-B2] Mark that analysis has completed successfully.
        """
        if input_mode is not None:
            self.input_mode = input_mode
        self.analysis_text_content = analysis_text_content
        self.analysis_text_source = analysis_text_source
        self.transcription_text = transcription_text
        self.transcription_source = transcription_source
        self.transcription_timing_source = transcription_timing_source
        if transcription_original_text is not None:
            self.transcription_original_text = transcription_original_text
        elif transcription_text and not self.transcription_original_text:
            self.transcription_original_text = transcription_text
        self.transcription_is_edited = transcription_is_edited
        self.transcription_edit_dirty = False
        if transcription_timing_result is not None:
            self.transcription_timing_result = transcription_timing_result
        self.current_timing_plan = timing_plan
        self.clear_output_edit_draft(source_changed=True)
        self.analysis_result_valid = True
        self.analysis_pending_rebuild = False
        self.clear_output_diagnostics_state()
        self.clear_adjustment_snapshot()
        self.status_key = StatusKey.ANALYSIS_READY
        self.clear_selection()

    def apply_transcription_edit(self, edited_text: str):
        """
        [MS19-B5] Apply a manually edited voice-only transcription to session state.
        The existing timing plan is invalid until rebuilt from the retained anchors.
        """
        self.transcription_text = edited_text
        self.analysis_text_content = edited_text
        self.analysis_text_source = "user_edited_transcription"
        self.transcription_source = "user_edited_transcription"
        self.transcription_is_edited = edited_text != self.transcription_original_text
        self.transcription_edit_dirty = False
        self.invalidate_analysis()
        self.whisper_model_selection = replace(
            self.whisper_model_selection,
            analysis_rebuild_reason="transcription_edit",
        )

    def revert_transcription_edit(self):
        """
        [MS19-B5] Restore the transcription text captured from Whisper.
        """
        self.transcription_text = self.transcription_original_text
        self.analysis_text_content = self.transcription_original_text
        self.analysis_text_source = "whisper_transcription" if self.transcription_original_text else ""
        self.transcription_source = "whisper_transcription" if self.transcription_original_text else ""
        self.transcription_is_edited = False
        self.transcription_edit_dirty = False
        self.invalidate_analysis()
        self.whisper_model_selection = replace(
            self.whisper_model_selection,
            analysis_rebuild_reason="transcription_edit",
        )

    def set_selected_source_event_index(self, index: int | None):
        """
        [MS16-B6] Set the selected source event index.

        This compatibility setter intentionally remains permissive. Canonical
        Preview selection must use commit_selected_source_event_index().
        """
        self.selected_source_event_index = index
        self.selected_base_plan_identity_digest = None
        self.selected_event_editor_revision += 1

    def commit_selected_source_event_index(
        self,
        index: int,
        *,
        requested_base_plan_identity_digest: str,
        current_base_plan_identity_digest: str,
        valid_base_event_indices: tuple[int, ...],
    ) -> bool:
        """Commit a current canonical Preview selection, failing closed."""
        if self.is_busy or isinstance(index, bool) or not isinstance(index, int) or index < 0:
            return False
        if (
            not isinstance(requested_base_plan_identity_digest, str)
            or not requested_base_plan_identity_digest
            or requested_base_plan_identity_digest != current_base_plan_identity_digest
        ):
            return False
        valid_indices = tuple(valid_base_event_indices)
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in valid_indices
        ):
            return False
        if index not in valid_indices:
            return False
        self.selected_source_event_index = index
        self.selected_base_plan_identity_digest = requested_base_plan_identity_digest
        self.selected_event_editor_revision += 1
        return True

    def clear_selection(self):
        """
        [MS16-B6] Clear the selected source event index.
        """
        self.selected_source_event_index = None
        self.selected_base_plan_identity_digest = None
        self.selected_event_editor_revision += 1

