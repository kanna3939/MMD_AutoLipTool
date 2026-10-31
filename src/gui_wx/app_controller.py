import wx
import os
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from src.core import (
    DiagnosticReportError,
    build_diagnostic_report_default_filename,
    write_diagnostic_report,
)
from src.core.debug_operation_log import (
    DebugOperationRecorder,
    OperationHandle,
)
from src.core.settings_store import SettingsStore
from src.core.whisper_model_store import (
    WhisperModelStore,
    resolve_whisper_models_dir,
)
from src.core.whisper_model_runtime import (
    VerifiedAnalysisModelRequest,
    WhisperModelRuntime,
    WhisperModelRuntimeError,
    build_verified_analysis_model_request,
)
from src.core.whisper_models import load_whisper_model_catalog
from src.core.generation_presets import (
    GenerationPreset,
    GenerationPresetStore,
    GenerationSettings,
    PresetMutationResult,
)
from src.core.model_profiles import (
    ModelProfile,
    ProfileGenerationOverrides,
    ModelProfileStore,
    ProfileMutationResult,
)
from src.core.model_profile_state import (
    ModelProfileResolutionResult,
    resolve_active_profile_preset_apply,
    resolve_model_profile_apply,
    resolve_no_profile,
    resolve_startup_model_profile,
    validate_generation_preset_mutation,
    validate_model_profile_mutation,
)
from src.core.output_edit_state import GenerationState, OutputEditState
from src.core.final_output_gate import (
    SaveCommitLease,
    VerifiedVmdSaveRequest,
    evaluate_shared_save_gate,
)
from src.core.verified_vmd_save import (
    VerifiedVmdSaveError,
    VerifiedVmdSaveTerminalResult,
    capture_vmd_file_identity,
    validate_vmd_save_target,
)
from src.core.event_adjustment_history import (
    normalize_profile_aware_output_edit_history_state,
)
from src.core.startup_diagnostics import SCAN_SLOW_THRESHOLD_MS
from src.core.audio_input import AudioInputInfo, build_audio_input_info
from src.core.ffmpeg_locator import (
    format_locator_status,
    format_tool_status,
    locate_ffmpeg_tools,
)
from src.core.audio_probe import probe_audio_file
from src.core.audio_convert import convert_to_analysis_wav
from src.core.mmd_wav_export import export_mmd_wav
from src.core.ffmpeg_runner import run_ffmpeg_analysis_wav_cancellable, run_ffmpeg_mmd_wav_cancellable
from src.core.ffprobe_runner import run_ffprobe_json_cancellable
from src.core.audio_processing import analyze_wav_file, load_waveform_preview
from src.core.delivery_artifacts import build_delivery_artifact_operations
from src.core.delivery_package import (
    DeliveryCommitAuthorization,
    DeliveryCommitGuardRequest,
    DeliveryStartContext,
    DeliveryStartGateResult,
    DeliveryTerminalResult,
    build_delivery_start_context,
    evaluate_delivery_commit_fingerprint,
    orchestrate_delivery_package,
    validate_delivery_destination,
)
from gui_wx.audio_worker import AudioWorker, DeliveryPackageWorker
from gui_wx.verified_vmd_worker import (
    VerifiedVmdSaveGateInputs,
    VerifiedVmdSaveWorker,
)
from gui_wx.ui_state import (
    StatusKey,
    WhisperModelSelectionState,
    WHISPER_MANAGEMENT_OPERATION_APPLY,
    WHISPER_AVAILABILITY_SCAN_FAILED,
    WHISPER_AVAILABILITY_SCAN_PENDING,
    WHISPER_AVAILABILITY_SCAN_SUCCEEDED,
    format_whisper_failure_notice,
)
from gui_wx.theme import ThemeMode
from gui_wx.whisper_availability_worker import (
    WhisperAvailabilityScanResult,
    WhisperAvailabilityWorker,
)
from gui_wx.model_download_worker import (
    MODEL_MANAGEMENT_OPERATION_DELETE,
    MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
    MODEL_MANAGEMENT_STATUS_BLOCKED,
    MODEL_MANAGEMENT_STATUS_CANCELLED,
    MODEL_MANAGEMENT_STATUS_SUCCEEDED,
    ModelManagementProgress,
    ModelManagementResult,
    WhisperModelManagementWorker,
)
from gui_wx.model_apply_worker import (
    MODEL_APPLY_STATUS_CANCELLED,
    MODEL_APPLY_STATUS_FAILED,
    MODEL_APPLY_STATUS_READY,
    WhisperModelApplyResult,
    WhisperModelApplyWorker,
)
from gui_wx.worker_state import (
    AudioWorkerKind,
    AudioWorkerState,
    AudioWorkerStatus,
    LONG_AUDIO_CONFIRMATION_THRESHOLD_SEC,
)
from gui_wx.playback_controller import PlaybackController
from gui_wx.output_diagnostics_adapter import (
    resolve_source_audio_path_from_ui_state,
)
from gui_wx.viewport_controller import ViewportController


DELIVERY_COMMIT_GUARD_UI_TIMEOUT_SEC = 30.0

_DELIVERY_ERROR_MESSAGES = {
    "output_destination_collision": "同名の出力先があるため、別のfolder名で再実行してください。",
    "output_path_invalid": "親directoryまたはfolder名を確認してください。",
    "output_path_too_long": "親directoryまたはfolder名が長すぎます。",
    "output_parent_invalid": "保存先directoryが見つからないか、利用できません。",
    "source_audio_changed": "音声が処理中に変更されたため、読み込み直して再実行してください。",
    "delivery_state_stale": "作業状態が変わったため確定できませんでした。現在の状態を確認して再実行してください。",
    "delivery_commit_guard_failed": "出力を安全に確定できませんでした。もう一度お試しください。",
    "delivery_commit_failed": "出力を安全に確定できませんでした。保存先を確認してください。",
    "output_permission_denied": "出力先または一時出力へのアクセスが拒否されました。権限と使用中のファイルを確認してください。",
    "output_file_locked": "出力先または一時出力が別の処理で使用中です。ファイルを閉じて再実行してください。",
    "output_path_inspection_failed": "出力先を確認できませんでした。権限と保存先を確認してください。",
    "partial_output_cleanup_failed": "一時出力を削除できませんでした。残存ファイルを確認してください。",
    "delivery_current_state_invalid": "現在の解析状態を確認できないため、一括出力を開始できません。",
    "delivery_artifact_operations_invalid": "一括出力の準備に失敗しました。もう一度お試しください。",
    "delivery_busy": "別の処理が実行中のため、一括出力を開始できません。",
    "delivery_worker_reference_missing": "一括出力の処理状態を確認できないため、終了を待っています。再試行してください。",
    "delivery_ffmpeg_unavailable": "FFmpegを確認できないため、一括出力を開始できません。",
    "delivery_worker_failed": "一括出力の実行に失敗しました。もう一度お試しください。",
    "vmd_write_failed": "VMDを生成・検証できませんでした。",
    "vmd_validation_failed": "VMDを生成・検証できませんでした。",
    "mmd_wav_write_failed": "MMD用WAVを生成・検証できませんでした。",
    "mmd_wav_validation_failed": "MMD用WAVを生成・検証できませんでした。",
    "report_write_failed": "診断レポートを生成・検証できませんでした。",
    "report_validation_failed": "診断レポートを生成・検証できませんでした。",
    "shared_final_output_unavailable": "共有最終出力を検証できません。Previewと診断を確認してください。",
    "shared_final_output_stale": "作業状態が変わったため保存できません。Previewを再確認してください。",
}


class _DeliveryGuardReply:
    def __init__(self) -> None:
        self.event = threading.Event()
        self._lock = threading.Lock()
        self._completed = False
        self.authorization: DeliveryCommitAuthorization | None = None
        self.error: Exception | None = None

    def complete(
        self,
        authorization: DeliveryCommitAuthorization | None = None,
        error: Exception | None = None,
    ) -> bool:
        with self._lock:
            if self._completed:
                return False
            self._completed = True
            self.authorization = authorization
            self.error = error
            self.event.set()
            return True


class _VerifiedSaveGuardReply:
    def __init__(self) -> None:
        self.event = threading.Event()
        self._lock = threading.Lock()
        self._completed = False
        self.decision: str | None = None
        self.error: Exception | None = None

    def complete(self, decision: str | None = None, error: Exception | None = None) -> bool:
        with self._lock:
            if self._completed:
                return False
            self._completed = True
            self.decision = decision
            self.error = error
            self.event.set()
            return True


@dataclass(slots=True)
class _VerifiedVmdSaveOperation:
    operation_id: int
    job_id: int
    previous_status_key: StatusKey
    gate_inputs: VerifiedVmdSaveGateInputs
    cancel_requested: bool = False
    worker_started: bool = False


def _summarize_technical_error(error: BaseException) -> str:
    message = str(error).strip()
    if message:
        return f"{error.__class__.__name__}: {message}"
    return error.__class__.__name__


def _storage_display_metadata(resolution) -> tuple[str, str]:
    if not resolution.succeeded or resolution.resolved_path is None:
        return "unresolved", "保存先を確認できません"
    if resolution.used_default:
        return "default", "既定保存先 (models)"
    tail = resolution.resolved_path.name
    return (
        "user_specified",
        f"ユーザー指定 ({tail})" if tail else "ユーザー指定",
    )


class WorkerHooks:
    """
    [MS13-B5] 将来の非同期処理 (Worker/Thread) との接続スタブ。
    実処理は含めず、将来 thread 等からコールバックされる口として用意する。
    """
    def __init__(self, controller):
        self.controller = controller

    def start_analysis_worker(self):
        self.controller.update_status("Worker: 解析開始要求を受理しました (Stub)")

    def on_analysis_progress(self, current: int, total: int):
        self.controller.update_status(f"Worker: 進捗 {current}/{total} (Stub)")

    def on_analysis_success(self, result):
        self.controller.update_status("Worker: 解析完了 (Stub)")

    def on_analysis_error(self, error: Exception):
        self.controller.update_status(f"Worker: エラー発生 {error} (Stub)")


class AppController:
    def __init__(
        self,
        view,
        *,
        settings_store: SettingsStore | None = None,
        preset_store: GenerationPresetStore | None = None,
        profile_store: ModelProfileStore | None = None,
        whisper_ownership_provider=None,
        startup_diagnostics=None,
        operation_recorder: DebugOperationRecorder | None = None,
    ):
        self.view = view
        self._startup_diagnostics = startup_diagnostics
        self._operation_recorder = operation_recorder or DebugOperationRecorder(
            on_state_change=self._on_debug_operation_log_state_changed
        )
        self._operation_handles_by_job: dict[tuple[str, int], OperationHandle] = {}
        self._debug_audio_operations: dict[int, OperationHandle] = {}
        self._whisper_debug_operations: dict[tuple[str, int], OperationHandle] = {}
        self._pending_exit_operation_handle: OperationHandle | None = None
        self.worker_hooks = WorkerHooks(self)
        if settings_store is None and preset_store is not None:
            settings_store = SettingsStore(preset_store.settings_path)
        self.settings_store = settings_store or SettingsStore()
        if preset_store is None:
            self.preset_store = GenerationPresetStore(
                settings_store=self.settings_store
            )
        else:
            if preset_store.settings_path != self.settings_store.settings_path:
                raise ValueError(
                    "settings_store and preset_store must use the same settings path"
                )
            self.preset_store = preset_store
        if profile_store is None:
            self.profile_store = ModelProfileStore(settings_store=self.settings_store)
        else:
            if profile_store.settings_path != self.settings_store.settings_path:
                raise ValueError(
                    "settings_store and profile_store must use the same settings path"
                )
            self.profile_store = profile_store
        self.startup_settings_result = None
        self.startup_preset_result = None
        self.startup_profile_result = None
        self.active_preset_resolution = None
        self.model_profile_resolution = None
        self._startup_state: dict[str, object] | None = None
        
        self.playback_controller = PlaybackController(
            update_callback=self._on_playback_update,
            finished_callback=self._on_playback_finished
        )
        self._playback_scrub_operation_handle = None
        
        # [MS15-B4] Viewport Controller
        self.viewport_controller = ViewportController(
            on_viewport_changed=self._on_viewport_changed
        )
        
        self._coalesced_save_timer = wx.Timer()
        self.view.Bind(wx.EVT_TIMER, self._on_save_timer, self._coalesced_save_timer)
        self._pending_save = False
        self._pending_settings_save_kind = "none"
        self._first_save_failure = False
        self._audio_worker = None
        self._delivery_worker: DeliveryPackageWorker | None = None
        self._delivery_parent_directory_session: Path | None = None
        self._active_delivery_binding: tuple[int, AudioWorkerKind, int] | None = None
        self._active_delivery_save_lease: SaveCommitLease | None = None
        self._delivery_close_pending = False
        self._delivery_terminal_received = False
        self._verified_vmd_worker: VerifiedVmdSaveWorker | None = None
        self._verified_vmd_save_operation: _VerifiedVmdSaveOperation | None = None
        self._verified_vmd_save_operation_sequence = 0
        self._active_verified_vmd_binding: tuple[int, AudioWorkerKind, int] | None = None
        self._active_verified_vmd_request: VerifiedVmdSaveRequest | None = None
        self._active_save_commit_lease: SaveCommitLease | None = None
        self._verified_vmd_close_pending = False
        self._verified_vmd_terminal_received = False
        self._audio_worker_previous_status_key = None
        self._is_shutting_down = False
        self.whisper_model_catalog = None
        self.whisper_model_store: WhisperModelStore | None = None
        self._whisper_availability_worker: WhisperAvailabilityWorker | None = None
        self._whisper_scan_job_id = 0
        self._whisper_scan_generation = 0
        self._whisper_scan_started = False
        self._whisper_scan_slow_timer = None
        self._whisper_scan_slow_key: tuple[int, int] | None = None
        self._whisper_management_worker: WhisperModelManagementWorker | None = None
        self._whisper_management_job_id = 0
        self._whisper_ownership_provider = whisper_ownership_provider
        self.whisper_model_runtime: WhisperModelRuntime | None = None
        self._whisper_apply_worker: WhisperModelApplyWorker | None = None
        self._whisper_apply_job_id = 0

    def _build_whisper_startup_state(
        self,
        settings: dict[str, object],
    ) -> tuple[WhisperModelSelectionState, WhisperModelStore | None, bool]:
        selected_key = settings.get("selected_whisper_model_key", "small")
        active_key = settings.get("active_whisper_model_key", "small")
        active_identity = settings.get("active_whisper_manifest_identity", "")
        if not isinstance(selected_key, str) or not selected_key:
            selected_key = "small"
        if not isinstance(active_key, str) or not active_key:
            active_key = "small"
        if not isinstance(active_identity, str):
            active_identity = ""

        try:
            catalog = load_whisper_model_catalog()
        except Exception as error:
            detail = _summarize_technical_error(error)
            state = WhisperModelSelectionState(
                selected_model_key=selected_key,
                active_model_key=active_key,
                active_manifest_identity=active_identity,
                availability_scan_status=WHISPER_AVAILABILITY_SCAN_FAILED,
                availability_scan_failure_code="manifest_invalid",
                availability_scan_failure_detail=detail,
                active_config_status="invalid",
                active_config_reason="manifest_invalid",
                notice=format_whisper_failure_notice("manifest_invalid"),
            )
            return state, None, False

        self.whisper_model_catalog = catalog
        self.whisper_model_runtime = WhisperModelRuntime(catalog=catalog)
        allowed_keys = {spec.model_key for spec in catalog.models}
        correction_required = False
        if selected_key not in allowed_keys:
            selected_key = catalog.default_model_key
            correction_required = True

        active_config_status = "valid"
        active_config_reason = None
        expected_identity = None
        if active_key in allowed_keys:
            expected_identity = catalog.manifest_identity(active_key)
            if not active_identity:
                active_identity = expected_identity
                correction_required = True
            elif active_identity != expected_identity:
                active_config_status = "invalid"
                active_config_reason = "active_manifest_identity_mismatch"
        else:
            active_config_status = "invalid"
            active_config_reason = "active_model_key_unsupported"

        settings["selected_whisper_model_key"] = selected_key
        settings["active_whisper_model_key"] = active_key
        settings["active_whisper_manifest_identity"] = active_identity

        root_resolution = resolve_whisper_models_dir(
            settings.get("whisper_models_dir", "")
        )
        if root_resolution.succeeded and root_resolution.resolved_path is not None:
            store = WhisperModelStore(
                root_resolution.resolved_path,
                catalog=catalog,
            )
            storage_location_kind, storage_location_display = (
                _storage_display_metadata(root_resolution)
            )
            state = WhisperModelSelectionState(
                model_specs=catalog.models,
                selected_model_key=selected_key,
                active_model_key=active_key,
                active_manifest_identity=active_identity,
                availability_scan_status=WHISPER_AVAILABILITY_SCAN_PENDING,
                storage_root_display=str(root_resolution.resolved_path),
                storage_location_kind=storage_location_kind,
                storage_location_display=storage_location_display,
                active_config_status=active_config_status,
                active_config_reason=active_config_reason,
                notice=(
                    "現在のWhisperモデル設定を確認してください。"
                    if active_config_status != "valid"
                    else ""
                ),
            )
            return state, store, correction_required

        failure_code = root_resolution.failure_code or "storage_path_invalid"
        state = WhisperModelSelectionState(
            model_specs=catalog.models,
            selected_model_key=selected_key,
            active_model_key=active_key,
            active_manifest_identity=active_identity,
            availability_scan_status=WHISPER_AVAILABILITY_SCAN_FAILED,
            availability_scan_failure_code=failure_code,
            availability_scan_failure_detail=root_resolution.message,
            active_config_status=active_config_status,
            active_config_reason=active_config_reason,
            notice=format_whisper_failure_notice(failure_code),
        )
        return state, None, correction_required

    def build_active_whisper_model_request(self) -> VerifiedAnalysisModelRequest:
        """Return the active verified checkpoint for one analysis job."""
        if self.view is None or self.whisper_model_store is None:
            raise WhisperModelRuntimeError(
                "model_unavailable",
                "Whisper model storage is not available.",
                failure_class="model_unavailable",
            )
        if self.whisper_model_runtime is None:
            raise WhisperModelRuntimeError(
                "model_unavailable",
                "Whisper model runtime is not available.",
                failure_class="model_unavailable",
            )
        state = self.view.ui_state.whisper_model_selection
        if state.availability_scan_status != WHISPER_AVAILABILITY_SCAN_SUCCEEDED:
            raise WhisperModelRuntimeError(
                "availability_scan_pending",
                "Whisper model availability has not been verified.",
                failure_class="model_unavailable",
            )
        availability = next(
            (item for item in state.availability if item.model_key == state.active_model_key),
            None,
        )
        request = build_verified_analysis_model_request(availability)
        if request.identity.manifest_identity != state.active_manifest_identity:
            raise WhisperModelRuntimeError(
                "active_manifest_identity_mismatch",
                "Active Whisper model identity does not match availability.",
                failure_class="integrity_mismatch",
            )
        return request

    def _ownership_permit_for_delete(self, model_key: str):
        """Release the runtime owner before issuing the one-shot B5 permit."""
        if self.whisper_model_runtime is None or self.whisper_model_store is None:
            return None
        if self.view is None:
            return None
        availability = next(
            (
                item
                for item in self.view.ui_state.whisper_model_selection.availability
                if item.model_key == model_key
            ),
            None,
        )
        if availability is None or not availability.is_verified or availability.file_path is None:
            return None
        if not self.whisper_model_runtime.unload():
            return None
        return self.whisper_model_runtime.issue_ownership_release_permit(
            model_key=model_key,
            manifest_identity=availability.manifest_identity or "",
            artifact_id=str(availability.file_path.resolve(strict=False)),
        )

    def load_startup_state(self) -> dict[str, object]:
        """Load settings and presets once, without doing so in the constructor."""
        if self._startup_state is not None:
            return self._startup_state
        settings_result = self.settings_store.load()
        preset_result = self.preset_store.load()
        profile_result = self.profile_store.load()
        settings = dict(settings_result.settings)
        whisper_state, whisper_store, whisper_correction_required = (
            self._build_whisper_startup_state(settings)
        )
        self.whisper_model_store = whisper_store
        generation_settings = GenerationSettings(
            closing_hold_frames=settings.get("closing_hold_frames", 0),
            closing_softness_frames=settings.get("closing_softness_frames", 0),
            long_vowel_mode=settings.get("long_vowel_mode", "hold"),
        )
        raw_active_id = settings.get("active_preset_id")
        profile_resolution = resolve_startup_model_profile(
            application_generation_settings=generation_settings,
            application_morph_upper_limit=settings.get("morph_upper_limit", 0.9),
            raw_active_preset_id=raw_active_id,
            raw_active_model_profile_id=settings.get("active_model_profile_id"),
            raw_active_profile_baseline_preset_id=(
                settings.get("active_profile_baseline_preset_id")
            ),
            profile_load_result=profile_result,
            preset_load_result=preset_result,
        )
        self.startup_settings_result = settings_result
        self.startup_preset_result = preset_result
        self.startup_profile_result = profile_result
        self.model_profile_resolution = profile_resolution
        resolution = self.preset_store.resolve_active(
            profile_resolution.resolution.generation_settings,
            profile_resolution.resolution.active_preset_id,
        )
        self.active_preset_resolution = resolution
        resolved = profile_resolution.resolution
        settings["morph_upper_limit"] = resolved.morph_upper_limit
        settings["active_preset_id"] = resolved.active_preset_id
        settings["active_model_profile_id"] = (
            resolved.model_profile_state.active_model_profile_id
        )
        settings["active_profile_baseline_preset_id"] = (
            resolved.model_profile_state.active_profile_baseline_preset_id
        )
        if profile_resolution.identity_correction_required or whisper_correction_required:
            self.request_startup_identity_correction_save()
        self._startup_state = {
            "settings": settings,
            "generation_state": GenerationState(
                generation_settings=resolved.generation_settings,
                active_preset_id=resolved.active_preset_id,
                resolved_morph_name_set_id=resolved.morph_name_set.set_id,
            ),
            "active_preset_display_name": resolved.active_preset_display_name,
            "model_profile_state": resolved.model_profile_state,
            "active_model_profile_display_name": resolved.active_profile_display_name,
            "baseline_preset_display_name": resolved.baseline_preset_display_name,
            "resolved_morph_upper_limit": resolved.morph_upper_limit,
            "settings_result": settings_result,
            "preset_result": preset_result,
            "profile_result": profile_result,
            "active_preset_resolution": resolution,
            "model_profile_resolution": profile_resolution,
            "whisper_model_selection_state": whisper_state,
        }
        return self._startup_state

    def update_status(self, message: str):
        if self.view:
            self.view.update_status(message)

    @property
    def operation_recorder(self) -> DebugOperationRecorder:
        recorder = getattr(self, "_operation_recorder", None)
        if recorder is None:
            recorder = DebugOperationRecorder(
                on_state_change=self._on_debug_operation_log_state_changed
            )
            self._operation_recorder = recorder
        return recorder

    def _audio_debug_operation_handles(self) -> dict[int, OperationHandle]:
        handles = getattr(self, "_debug_audio_operations", None)
        if handles is None:
            handles = {}
            self._debug_audio_operations = handles
        return handles

    def set_debug_operation_recording(
        self,
        enabled: bool,
        *,
        state_snapshot: dict | None = None,
    ) -> str:
        return self.operation_recorder.set_enabled(
            enabled,
            state_snapshot=state_snapshot,
        )

    def begin_debug_operation(
        self,
        action: str,
        *,
        payload: dict | None = None,
        source: str = "user",
        entry: str | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
        capture_current_origin: bool = True,
    ) -> OperationHandle | None:
        if capture_current_origin and self.view is not None and (
            analysis_run_id is None or analysis_result_id is None
        ):
            state = getattr(self.view, "ui_state", None)
            final_output_state = getattr(state, "final_output_state", None)
            origin = getattr(final_output_state, "accepted_origin", None)
            if analysis_run_id is None and origin is not None:
                analysis_run_id = getattr(origin, "source_run_id", None)
            if analysis_result_id is None and origin is not None:
                analysis_result_id = getattr(origin, "analysis_result_id", None)
        return self.operation_recorder.begin_operation(
            action,
            payload=payload,
            source=source,
            entry=entry,
            analysis_run_id=analysis_run_id,
            analysis_result_id=analysis_result_id,
        )

    def mark_debug_operation_started(
        self,
        handle: OperationHandle | None,
        *,
        job_kind: str | None = None,
        job_id: int | None = None,
        payload: dict | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
    ) -> OperationHandle | None:
        return self.operation_recorder.mark_started(
            handle,
            job_kind=job_kind,
            job_id=job_id,
            payload=payload,
            analysis_run_id=analysis_run_id,
            analysis_result_id=analysis_result_id,
        )

    def finish_debug_operation(
        self,
        handle: OperationHandle | None,
        status: str,
        *,
        reason_code: str | None = None,
        payload: dict | None = None,
        accepted_origin: object | None = None,
    ) -> bool:
        return self.operation_recorder.finish_operation(
            handle,
            status,
            reason_code=reason_code,
            payload=payload,
            accepted_origin=accepted_origin,
        )

    def record_debug_operation_phase(
        self,
        handle: OperationHandle | None,
        phase: str,
        status: str,
        *,
        job_kind: str | None = None,
        job_id: int | None = None,
        payload: dict | None = None,
        reason_code: str | None = None,
    ) -> bool:
        return self.operation_recorder.record_operation_phase(
            handle,
            phase,
            status,
            job_kind=job_kind,
            job_id=job_id,
            payload=payload,
            reason_code=reason_code,
        )

    def record_debug_operation_event(
        self,
        action: str,
        status: str,
        *,
        payload: dict | None = None,
        source: str = "system",
        entry: str | None = None,
        job_kind: str | None = None,
        job_id: int | None = None,
        analysis_run_id: str | None = None,
        analysis_result_id: str | None = None,
        reason_code: str | None = None,
    ) -> bool:
        return self.operation_recorder.record_event(
            action,
            status,
            payload=payload,
            source=source,
            entry=entry,
            job_kind=job_kind,
            job_id=job_id,
            analysis_run_id=analysis_run_id,
            analysis_result_id=analysis_result_id,
            reason_code=reason_code,
        )

    def bind_debug_operation_to_job(
        self,
        handle: OperationHandle | None,
        *,
        job_kind: str,
        job_id: int,
        payload: dict | None = None,
    ) -> OperationHandle | None:
        bound = self.mark_debug_operation_started(
            handle,
            job_kind=job_kind,
            job_id=job_id,
            payload=payload,
        )
        if bound is not None:
            self._operation_handles_by_job[(job_kind, job_id)] = bound
        return bound

    def finish_debug_operation_job(
        self,
        *,
        job_kind: str,
        job_id: int,
        status: str,
        reason_code: str | None = None,
        payload: dict | None = None,
        accepted_origin: object | None = None,
    ) -> bool:
        handle = self._operation_handles_by_job.pop((job_kind, job_id), None)
        if handle is None:
            return self.record_debug_operation_event(
                "unbound_worker_result",
                "ignored" if status == "ignored" else status,
                payload=payload,
                source="worker",
                job_kind=job_kind,
                job_id=job_id,
                analysis_run_id=(
                    getattr(accepted_origin, "source_run_id", None)
                    if accepted_origin is not None
                    else None
                ),
                analysis_result_id=(
                    getattr(accepted_origin, "analysis_result_id", None)
                    if accepted_origin is not None
                    else None
                ),
                reason_code=reason_code or "start_not_recorded",
            )
        return self.finish_debug_operation(
            handle,
            status,
            reason_code=reason_code,
            payload=payload,
            accepted_origin=accepted_origin,
        )

    def shutdown_debug_operation_log(self, *, timeout: float = 1.0) -> bool:
        return self.operation_recorder.shutdown(timeout=timeout)

    def set_pending_exit_operation(
        self,
        handle: OperationHandle | None,
    ) -> None:
        self._pending_exit_operation_handle = handle

    def _on_debug_operation_log_state_changed(
        self,
        state: str,
        error_code: str | None,
        path: Path | None,
    ) -> None:
        try:
            wx.CallAfter(
                self._apply_debug_operation_log_state,
                state,
                error_code,
                path,
            )
        except Exception:
            pass

    def _apply_debug_operation_log_state(
        self,
        state: str,
        error_code: str | None,
        path: Path | None,
    ) -> None:
        view = self.view
        if view is None:
            return
        updater = getattr(view, "update_debug_operation_log_state", None)
        if callable(updater):
            updater(state, error_code, path)

    def _update_audio_worker_action_states(self) -> None:
        updater = getattr(self.view, "update_audio_worker_action_states", None)
        if callable(updater):
            updater()

    def _set_audio_worker_state(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        status: AudioWorkerStatus,
        message: str = "",
    ):
        if not self.view:
            return
        self.view.ui_state.audio_worker_state = AudioWorkerState(
            audio_job_id=audio_job_id,
            kind=kind,
            status=status,
            message=message,
        )

    def _start_audio_worker(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        task,
        message: str,
        *,
        operation_handle: OperationHandle | None = None,
    ):
        if not self.view or getattr(self, "_is_shutting_down", False):
            return
        operation_handles = self._audio_debug_operation_handles()
        operation_handle = operation_handle or operation_handles.get(
            audio_job_id
        )
        if operation_handle is not None:
            operation_handle = self.bind_debug_operation_to_job(
                operation_handle,
                job_kind=kind.name.lower(),
                job_id=audio_job_id,
                payload={"worker_kind": kind.name.lower()},
            )
            if operation_handle is not None:
                operation_handles[audio_job_id] = operation_handle
        st = self.view.ui_state
        if not st.is_busy:
            self._audio_worker_previous_status_key = st.status_key
        st.set_busy(
            True,
            preserve_final_output_context=(kind == AudioWorkerKind.MMD_WAV),
        )
        self._set_audio_worker_state(audio_job_id, kind, AudioWorkerStatus.RUNNING, message)
        self.update_status(message)
        if kind == AudioWorkerKind.MMD_WAV:
            self._update_audio_worker_action_states()
        else:
            self.view.sync_ui_state()
        self.update_status(message)

        if kind == AudioWorkerKind.MMD_WAV:
            try:
                worker = AudioWorker(
                    audio_job_id=audio_job_id,
                    kind=kind,
                    task=task,
                    success_callback=self._on_audio_worker_success,
                    error_callback=self._on_audio_worker_error,
                    cancelled_callback=self._on_audio_worker_cancelled,
                )
                self._audio_worker = worker
                worker.start()
            except Exception as error:
                self._finish_audio_worker(
                    audio_job_id,
                    kind,
                    AudioWorkerStatus.FAILED,
                    "MMD用WAV出力失敗",
                )
                wx.MessageBox(
                    f"MMD用WAVの出力に失敗しました。\n{error}",
                    "MMD用WAV出力エラー",
                    wx.OK | wx.ICON_ERROR,
                )
            return

        worker = AudioWorker(
            audio_job_id=audio_job_id,
            kind=kind,
            task=task,
            success_callback=self._on_audio_worker_success,
            error_callback=self._on_audio_worker_error,
            cancelled_callback=self._on_audio_worker_cancelled,
        )
        self._audio_worker = worker
        try:
            worker.start()
        except Exception:
            self._finish_debug_audio_operation(
                audio_job_id,
                "failed",
                kind=kind,
                reason_code="worker_start_failed",
            )
            raise

    def _is_current_audio_worker_result(
        self,
        audio_job_id: int,
        expected_kind: AudioWorkerKind,
    ) -> bool:
        if getattr(self, "_is_shutting_down", False) or not self.view:
            return False
        st = self.view.ui_state
        if not st.is_current_audio_job(audio_job_id):
            return False
        worker_state = st.audio_worker_state
        if (
            worker_state is None
            or worker_state.audio_job_id != audio_job_id
            or worker_state.kind != expected_kind
            or worker_state.status != AudioWorkerStatus.RUNNING
        ):
            return False
        return True

    def _clear_selected_audio_state(self):
        if not self.view:
            return
        st = self.view.ui_state
        st.selected_audio_input = None
        st.selected_audio_probe = None
        st.selected_analysis_wav = None
        st.selected_wav_path = None
        st.selected_wav_analysis = None

    def _finish_audio_worker(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        status: AudioWorkerStatus,
        message: str,
        *,
        busy: bool = False,
    ):
        self._release_audio_worker_reference(audio_job_id, kind)
        operation_status = {
            AudioWorkerStatus.COMPLETED: "completed",
            AudioWorkerStatus.FAILED: "failed",
            AudioWorkerStatus.CANCELLED: "cancelled",
        }.get(status)
        if operation_status is not None:
            self._finish_debug_audio_operation(
                audio_job_id,
                operation_status,
                kind=kind,
                reason_code=f"{kind.name.lower()}_{operation_status}",
            )
        if not self.view:
            return
        st = self.view.ui_state
        if st.is_current_audio_job(audio_job_id):
            st.set_busy(busy)
            if not busy and self._audio_worker_previous_status_key is not None:
                st.status_key = self._audio_worker_previous_status_key
                self._audio_worker_previous_status_key = None
            self._set_audio_worker_state(audio_job_id, kind, status, message)
            self.update_status(message)
            if kind == AudioWorkerKind.MMD_WAV:
                self._update_audio_worker_action_states()
            else:
                self.view.sync_ui_state()
            self.update_status(message)

    def _finish_debug_audio_operation(
        self,
        audio_job_id: int,
        status: str,
        *,
        kind: AudioWorkerKind,
        reason_code: str,
        payload: dict | None = None,
    ) -> None:
        handle = self._audio_debug_operation_handles().pop(audio_job_id, None)
        if handle is not None:
            terminal_payload = {"worker_kind": kind.name.lower()}
            if payload:
                terminal_payload.update(payload)
            self.finish_debug_operation(
                handle,
                status,
                reason_code=reason_code,
                payload=terminal_payload,
            )

    def _bind_whisper_debug_operation(
        self,
        operation: str,
        job_id: int,
        handle: OperationHandle | None,
        *,
        model_key: str,
    ) -> None:
        if handle is None:
            return
        bound = self.bind_debug_operation_to_job(
            handle,
            job_kind=f"whisper_{operation}",
            job_id=job_id,
            payload={"model_key": model_key, "worker_kind": f"whisper_{operation}"},
        )
        if bound is not None:
            self._whisper_debug_operations[(operation, job_id)] = bound

    def _finish_whisper_debug_operation(
        self,
        operation: str,
        job_id: int,
        status: str,
        *,
        reason_code: str,
        model_key: str | None = None,
    ) -> None:
        handle = self._whisper_debug_operations.pop((operation, job_id), None)
        self.finish_debug_operation(
            handle,
            status,
            reason_code=reason_code,
            payload={
                "model_key": model_key,
                "worker_kind": f"whisper_{operation}",
            },
        )

    def _release_audio_worker_reference(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
    ) -> None:
        worker = getattr(self, "_audio_worker", None)
        if worker is None:
            return
        if (
            getattr(worker, "audio_job_id", None) == audio_job_id
            and getattr(worker, "kind", None) == kind
        ):
            self._audio_worker = None

    def _confirm_long_audio_if_needed(self, duration_sec: float | None) -> bool:
        if duration_sec is None or duration_sec <= LONG_AUDIO_CONFIRMATION_THRESHOLD_SEC:
            return True
        if self.view and hasattr(self.view, "confirm_long_audio_processing"):
            return self.view.confirm_long_audio_processing(duration_sec)
        result = wx.MessageBox(
            f"音声の長さが {duration_sec:.1f} 秒あります。\n処理に時間がかかる可能性があります。続行しますか？",
            "長時間処理の確認",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        return result == wx.YES

    def invalidate_audio_job_for_input_change(self):
        if not self.view:
            return
        st = self.view.ui_state
        if self.is_delivery_active():
            self.request_cancel_audio_worker()
            return
        if st.audio_worker_active:
            self.request_cancel_audio_worker()
            return
        st.invalidate_audio_job()

    def request_cancel_audio_worker(self):
        if not self.view:
            return
        st = self.view.ui_state
        operation_handle = self._audio_debug_operation_handles().get(
            st.current_audio_job_id
        )
        worker_state = st.audio_worker_state
        worker_kind = (
            worker_state.kind.name.lower() if worker_state is not None else None
        )
        job_id = st.current_audio_job_id
        if self.is_delivery_active():
            worker = self._delivery_worker
            if worker is None:
                self._show_delivery_error("delivery_worker_reference_missing")
                self.record_debug_operation_phase(
                    operation_handle,
                    "cancel_request",
                    "rejected",
                    job_kind="delivery_package",
                    job_id=job_id,
                    reason_code="worker_reference_missing",
                )
                return False
            if not st.audio_worker_cancel_available:
                self.record_debug_operation_phase(
                    operation_handle,
                    "cancel_request",
                    "rejected",
                    job_kind="delivery_package",
                    job_id=job_id,
                    reason_code="finalizing",
                )
                return False
            accepted = worker.cancel()
            self._set_audio_worker_state(
                st.current_audio_job_id,
                AudioWorkerKind.DELIVERY_PACKAGE,
                (
                    AudioWorkerStatus.CANCELLING
                    if accepted
                    else AudioWorkerStatus.FINALIZING
                ),
                (
                    "MMD一括出力をキャンセル中..."
                    if accepted
                    else "出力先を確定中です。完了を待っています。"
                ),
            )
            self.update_status(
                "MMD一括出力をキャンセル中..."
                if accepted
                else "出力先を確定中です。完了を待っています。"
            )
            self.view.sync_ui_state()
            self.update_status(
                "MMD一括出力をキャンセル中..."
                if accepted
                else "出力先を確定中です。完了を待っています。"
            )
            self.record_debug_operation_phase(
                operation_handle,
                "cancel_request",
                "requested" if accepted else "rejected",
                job_kind="delivery_package",
                job_id=job_id,
                reason_code="cancel_accepted" if accepted else "finalizing",
            )
            return accepted
        save_operation = getattr(self, "_verified_vmd_save_operation", None)
        if save_operation is not None and not save_operation.worker_started:
            save_operation.cancel_requested = True
            self._set_audio_worker_state(
                save_operation.job_id,
                AudioWorkerKind.VERIFIED_VMD_SAVE,
                AudioWorkerStatus.CANCELLING,
                "VMD保存準備をキャンセル中...",
            )
            self.update_status("VMD保存準備をキャンセル中...")
            self.view.update_vmd_save_action_states()
            self.record_debug_operation_phase(
                self._audio_debug_operation_handles().get(save_operation.job_id),
                "cancel_request",
                "requested",
                job_kind="verified_vmd_save",
                job_id=save_operation.job_id,
                reason_code="cancel_accepted",
            )
            return True
        worker_state = st.audio_worker_state
        if (
            worker_state is not None
            and worker_state.kind == AudioWorkerKind.VERIFIED_VMD_SAVE
        ):
            worker = self._verified_vmd_worker
            if worker is None:
                self.update_status("VMD保存の終了を確認できないため、完了を待っています。")
                return False
            accepted = worker.cancel()
            self._set_audio_worker_state(
                worker_state.audio_job_id,
                AudioWorkerKind.VERIFIED_VMD_SAVE,
                AudioWorkerStatus.CANCELLING if accepted else AudioWorkerStatus.FINALIZING,
                "VMD保存をキャンセル中..." if accepted else "VMD確定処理の終了を待っています。",
            )
            self.update_status(
                "VMD保存をキャンセル中..." if accepted else "VMD確定処理の終了を待っています。"
            )
            self.view.update_vmd_save_action_states()
            self.update_status(
                "VMD保存をキャンセル中..." if accepted else "VMD確定処理の終了を待っています。"
            )
            self.record_debug_operation_phase(
                self._audio_debug_operation_handles().get(worker_state.audio_job_id),
                "cancel_request",
                "requested" if accepted else "rejected",
                job_kind="verified_vmd_save",
                job_id=worker_state.audio_job_id,
                reason_code="cancel_accepted" if accepted else "finalizing",
            )
            return accepted
        if not st.audio_worker_active:
            self.record_debug_operation_phase(
                operation_handle,
                "cancel_request",
                "rejected",
                job_kind=worker_kind,
                job_id=job_id,
                reason_code="worker_not_active",
            )
            return False
        worker = getattr(self, "_audio_worker", None)
        if worker is None:
            self.update_status(
                "音声処理の状態を確認できないため、キャンセルを実行できません。"
            )
            self.record_debug_operation_phase(
                operation_handle,
                "cancel_request",
                "rejected",
                job_kind=worker_kind,
                job_id=job_id,
                reason_code="worker_reference_missing",
            )
            return False
        self._set_audio_worker_state(
            worker_state.audio_job_id,
            worker_state.kind,
            AudioWorkerStatus.CANCELLING,
            "キャンセル中...",
        )
        worker.cancel()
        self.update_status("キャンセル中...")
        if worker_state.kind == AudioWorkerKind.MMD_WAV:
            self._update_audio_worker_action_states()
        else:
            self.view.sync_ui_state()
        self.update_status("キャンセル中...")
        self.record_debug_operation_phase(
            operation_handle,
            "cancel_request",
            "requested",
            job_kind=worker_kind,
            job_id=job_id,
            reason_code="cancel_accepted",
        )
        return True

    @property
    def delivery_close_pending(self) -> bool:
        return self._delivery_close_pending

    @property
    def delivery_may_be_active(self) -> bool:
        """Return whether delivery state still needs terminal reconciliation."""
        state = self.view.ui_state.audio_worker_state if self.view is not None else None
        return bool(
            self._delivery_worker is not None
            or self._active_delivery_binding is not None
            or self._delivery_close_pending
            or (
                state is not None
                and state.kind == AudioWorkerKind.DELIVERY_PACKAGE
                and state.is_active
            )
        )

    def is_delivery_active(self) -> bool:
        binding = self._active_delivery_binding
        if binding is None or self.view is None:
            return False
        state = self.view.ui_state.audio_worker_state
        return bool(
            self.view.ui_state.is_current_audio_job(binding[0])
            and state is not None
            and state.audio_job_id == binding[0]
            and state.kind == AudioWorkerKind.DELIVERY_PACKAGE
            and state.is_active
        )

    def _show_delivery_error(self, error_code: str) -> None:
        message = _DELIVERY_ERROR_MESSAGES.get(
            error_code,
            "一括出力を完了できませんでした。現在の状態を確認して再実行してください。",
        )
        self.update_status("MMD一括出力失敗")
        if self.view is not None:
            wx.MessageBox(
                message,
                "MMD一括出力エラー",
                wx.OK | wx.ICON_ERROR,
                self.view,
            )

    def _resolve_delivery_ffmpeg_path(self) -> Path | None:
        try:
            tools = locate_ffmpeg_tools()
            path = getattr(getattr(tools, "ffmpeg", None), "path", None)
            if not path:
                self._show_delivery_error("delivery_ffmpeg_unavailable")
                return None
            resolved = Path(path)
            if not resolved.is_file():
                self._show_delivery_error("delivery_ffmpeg_unavailable")
                return None
            return resolved
        except (OSError, RuntimeError, TypeError, ValueError):
            self._show_delivery_error("delivery_ffmpeg_unavailable")
            return None

    def _delivery_default_parent(self) -> Path:
        if self._delivery_parent_directory_session is not None:
            return self._delivery_parent_directory_session
        st = self.view.ui_state
        for value in (st.last_mmd_wav_export_dir, st.last_vmd_output_dir):
            if value:
                return Path(value)
        source_path = resolve_source_audio_path_from_ui_state(st)
        if source_path is not None:
            return Path(source_path).parent
        return Path.cwd()

    def _capture_delivery_ready_candidate(
        self,
        ffmpeg_path: Path,
    ):
        st = self.view.ui_state
        confirmed = st.confirmed_shared_warning_fingerprint
        while True:
            try:
                gate = self.view.capture_current_delivery_state(
                    ffmpeg_path=ffmpeg_path,
                    confirmed_warning_save_state_fingerprint=confirmed,
                )
            except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
                self._show_delivery_error("delivery_current_state_invalid")
                return None
            if not isinstance(gate, DeliveryStartGateResult):
                self._show_delivery_error("delivery_current_state_invalid")
                return None
            if gate.status == "blocked":
                self._show_delivery_error(gate.blocking_codes[0])
                return None
            if gate.status != "warning_confirmation_required":
                return gate
            candidate = gate.candidate_state
            if candidate is None or not self.view.confirm_vmd_save_warnings(
                candidate.diagnostics_snapshot
            ):
                self.update_status("MMD一括出力をキャンセルしました")
                return None
            confirmed = gate.fingerprint
            st.confirmed_shared_warning_fingerprint = confirmed

    def _build_delivery_context(
        self,
        candidate_gate,
        parent_directory: Path,
        folder_name: str,
    ) -> DeliveryStartContext | None:
        candidate = candidate_gate.candidate_state
        if candidate is None:
            return None
        try:
            return build_delivery_start_context(
                candidate,
                parent_directory,
                folder_name,
                datetime.now().astimezone(),
            )
        except Exception:
            self._show_delivery_error("output_path_invalid")
            return None

    def request_export_delivery_package(self) -> bool:
        """Start a transactional VMD/WAV/report delivery package export."""
        operation_handle = self.begin_debug_operation(
            "delivery_package_export",
            payload={"analysis_result_valid": bool(
                self.view is not None and self.view.ui_state.analysis_result_valid
            )},
            entry="menu",
        )
        if (
            self.view is None
            or self._is_shutting_down
            or self.is_delivery_active()
            or self.view.ui_state.is_busy
        ):
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("busy" if self.view is not None and self.view.ui_state.is_busy
                             else "delivery_unavailable"),
            )
            return False

        ffmpeg_path = self._resolve_delivery_ffmpeg_path()
        if ffmpeg_path is None:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="ffmpeg_unavailable",
            )
            return False
        candidate_gate = self._capture_delivery_ready_candidate(ffmpeg_path)
        if candidate_gate is None:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="delivery_candidate_unavailable",
            )
            return False
        candidate = candidate_gate.candidate_state
        if candidate is None:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="delivery_candidate_unavailable",
            )
            return False

        parent_directory = self._delivery_default_parent()
        folder_name = candidate.artifact_names.default_directory_name
        dialog_error: str | None = None

        while True:
            selection = self.view.show_delivery_destination_dialog(
                str(parent_directory),
                folder_name,
                error_message=dialog_error,
            )
            dialog_error = None
            if selection is None:
                self.update_status("MMD一括出力をキャンセルしました")
                self.finish_debug_operation(
                    operation_handle,
                    "cancelled",
                    reason_code="destination_dialog_cancelled",
                )
                return False
            try:
                parent_directory, folder_name = selection
                parent_directory = Path(parent_directory)
                folder_name = str(folder_name)
            except (TypeError, ValueError):
                dialog_error = _DELIVERY_ERROR_MESSAGES["output_path_invalid"]
                continue

            self._delivery_parent_directory_session = parent_directory
            post_dialog_gate = self._capture_delivery_ready_candidate(ffmpeg_path)
            if post_dialog_gate is None:
                self.finish_debug_operation(
                    operation_handle,
                    "rejected",
                    reason_code="delivery_candidate_changed",
                )
                return False
            post_candidate = post_dialog_gate.candidate_state
            if post_candidate is None:
                self.finish_debug_operation(
                    operation_handle,
                    "rejected",
                    reason_code="delivery_candidate_unavailable",
                )
                return False
            if (
                post_candidate.source_identity != candidate.source_identity
                or post_candidate.artifact_names != candidate.artifact_names
            ):
                candidate = post_candidate
                parent_directory = self._delivery_default_parent()
                folder_name = candidate.artifact_names.default_directory_name
                continue

            start_context = self._build_delivery_context(
                post_dialog_gate,
                parent_directory,
                folder_name,
            )
            if start_context is None:
                self.finish_debug_operation(
                    operation_handle,
                    "rejected",
                    reason_code="delivery_context_unavailable",
                )
                return False
            try:
                validate_delivery_destination(start_context)
            except Exception as error:
                error_code = getattr(error, "code", "output_path_invalid")
                if error_code not in {
                    "output_destination_collision",
                    "output_path_invalid",
                    "output_path_too_long",
                    "output_parent_invalid",
                }:
                    error_code = "output_path_invalid"
                dialog_error = _DELIVERY_ERROR_MESSAGES.get(error_code)
                continue

            duration_sec = post_candidate.audio_probe.duration_sec
            if not self._confirm_long_audio_if_needed(duration_sec):
                self.update_status("MMD一括出力をキャンセルしました")
                self.finish_debug_operation(
                    operation_handle,
                    "cancelled",
                    reason_code="long_audio_confirmation_declined",
                )
                return False
            try:
                artifact_operations = build_delivery_artifact_operations()
            except Exception:
                self._show_delivery_error("delivery_artifact_operations_invalid")
                self.finish_debug_operation(
                    operation_handle,
                    "failed",
                    reason_code="delivery_artifact_operations_invalid",
                )
                return False
            audio_job_id = self.view.ui_state.next_audio_job_id()
            projection_generation = post_candidate.projection_generation
            return self._start_delivery_worker(
                audio_job_id=audio_job_id,
                projection_generation=projection_generation,
                start_context=start_context,
                artifact_operations=artifact_operations,
                operation_handle=operation_handle,
            )

    def _start_delivery_worker(
        self,
        *,
        audio_job_id: int,
        projection_generation: int,
        start_context: DeliveryStartContext,
        artifact_operations,
        operation_handle: OperationHandle | None = None,
    ) -> bool:
        if self.view is None:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="controller_unavailable",
            )
            return False
        st = self.view.ui_state
        if st.audio_worker_active or self.is_delivery_active():
            self._show_delivery_error("delivery_busy")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="delivery_busy",
            )
            return False
        previous_status_key = st.status_key
        pre_commit_guard = self._build_delivery_pre_commit_guard(
            start_context,
            projection_generation,
        )
        shared_context = start_context.current_state.shared_final_output_context
        if shared_context is not None:
            self._active_delivery_save_lease = SaveCommitLease(
                job_id=audio_job_id,
                ticket=shared_context.ticket,
                lifecycle_epoch=shared_context.lifecycle_epoch,
                binding_digest=shared_context.identity.binding_digest,
                fingerprint=start_context.current_state.start_fingerprint,
                lifecycle_signature=self._save_lifecycle_signature(
                    shared_context.lifecycle_signature
                ),
                lease_id=uuid.uuid4().hex,
            )
        else:
            self._active_delivery_save_lease = None

        def task(cancel_token):
            return orchestrate_delivery_package(
                job_id=audio_job_id,
                start_context=start_context,
                artifact_operations=artifact_operations,
                pre_commit_guard=pre_commit_guard,
                cancel_token=cancel_token,
            )

        worker = DeliveryPackageWorker(
            audio_job_id=audio_job_id,
            projection_generation=projection_generation,
            task=task,
            terminal_callback=self._on_delivery_worker_terminal,
            error_callback=self._on_delivery_worker_error,
        )
        self._delivery_worker = worker
        self._active_delivery_binding = (
            audio_job_id,
            AudioWorkerKind.DELIVERY_PACKAGE,
            projection_generation,
        )
        self._delivery_close_pending = False
        self._delivery_terminal_received = False
        self._audio_worker_previous_status_key = previous_status_key
        st.set_busy(True, preserve_final_output_context=True)
        self._set_audio_worker_state(
            audio_job_id,
            AudioWorkerKind.DELIVERY_PACKAGE,
            AudioWorkerStatus.RUNNING,
            "MMD一括出力中...",
        )
        self.update_status("MMD一括出力中...")
        try:
            # Keep the accepted shared-output context leased to this transaction.
            # Full sync observes the transient busy flag as a lifecycle change and
            # invalidates the very context whose artifacts this worker is writing.
            update_action_states = getattr(self.view, "update_action_states", None)
            if callable(update_action_states):
                update_action_states()
            self.update_status("MMD一括出力中...")
            worker.start()
        except Exception:
            self._delivery_worker = None
            self._active_delivery_binding = None
            self._active_delivery_save_lease = None
            self._delivery_terminal_received = True
            st.set_busy(False)
            self._set_audio_worker_state(
                audio_job_id,
                AudioWorkerKind.DELIVERY_PACKAGE,
                AudioWorkerStatus.FAILED,
                "MMD一括出力失敗",
            )
            self._audio_worker_previous_status_key = None
            self._show_delivery_error("delivery_worker_failed")
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="delivery_worker_start_failed",
                payload={"worker_kind": "delivery_package"},
            )
            try:
                self.view.sync_ui_state()
            except Exception:
                pass
            return False
        bound_handle = self.bind_debug_operation_to_job(
            operation_handle,
            job_kind="delivery_package",
            job_id=audio_job_id,
            payload={"worker_kind": "delivery_package"},
        )
        if bound_handle is not None:
            self._audio_debug_operation_handles()[audio_job_id] = bound_handle
        return True

    def _build_delivery_pre_commit_guard(
        self,
        start_context: DeliveryStartContext,
        projection_generation: int,
    ):
        def guard(request: DeliveryCommitGuardRequest, cancel_token):
            reply = _DeliveryGuardReply()
            if cancel_token.cancel_requested:
                return DeliveryCommitAuthorization(
                    job_id=request.job_id,
                    start_fingerprint=request.start_fingerprint,
                    decision="cancelled",
                )
            try:
                wx.CallAfter(
                    self._resolve_delivery_commit_guard,
                    request,
                    cancel_token,
                    start_context,
                    projection_generation,
                    reply,
                )
            except Exception as error:
                reply.complete(error=error)

            deadline = time.monotonic() + DELIVERY_COMMIT_GUARD_UI_TIMEOUT_SEC
            while not reply.event.wait(0.05):
                if cancel_token.cancel_requested:
                    reply.complete(
                        authorization=DeliveryCommitAuthorization(
                            job_id=request.job_id,
                            start_fingerprint=request.start_fingerprint,
                            decision="cancelled",
                        )
                    )
                    break
                if time.monotonic() >= deadline:
                    reply.complete(error=TimeoutError("delivery commit guard timed out"))
                    break
            if reply.error is not None:
                raise reply.error
            if reply.authorization is None:
                raise RuntimeError("delivery commit guard returned no decision")
            return reply.authorization

        return guard

    def _resolve_delivery_commit_guard(
        self,
        request: DeliveryCommitGuardRequest,
        cancel_token,
        start_context: DeliveryStartContext,
        projection_generation: int,
        reply: _DeliveryGuardReply,
    ) -> None:
        binding = self._active_delivery_binding
        state = self.view.ui_state.audio_worker_state if self.view else None
        if (
            binding is None
            or binding != (
                request.job_id,
                AudioWorkerKind.DELIVERY_PACKAGE,
                projection_generation,
            )
            or self.view is None
            or not self.view.ui_state.is_current_audio_job(request.job_id)
            or state is None
            or state.kind != AudioWorkerKind.DELIVERY_PACKAGE
            or not state.is_active
        ):
            decision = "invalid_job"
        elif self._delivery_close_pending:
            decision = "closing"
        elif cancel_token.cancel_requested:
            decision = "cancelled"
        elif start_context.current_state.projection_kind == "shared_final_output":
            shared = start_context.current_state.shared_final_output_context
            lease = self._active_delivery_save_lease
            if (
                shared is None
                or self.view.ui_state.final_output_state.current_context is not shared
                or lease is None
                or lease.job_id != request.job_id
                or lease.fingerprint != request.start_fingerprint
                or lease.binding_digest != shared.identity.binding_digest
                or lease.ticket != shared.ticket
                or lease.lifecycle_epoch != shared.lifecycle_epoch
                or not self.view.ui_state.is_busy
                or self.view.ui_state.analysis_pending_rebuild
                or self.view._analysis_info_in_progress
                or self.view.ui_state.final_output_state.expected_transition_input_digest
                != start_context.current_state.expected_transition_input_digest
                or self.view.ui_state.final_output_state.expected_application_binding_digest
                != start_context.current_state.expected_application_binding_digest
                or self._save_lifecycle_signature(
                    self.view._capture_final_output_lifecycle_signature()
                )
                != lease.lifecycle_signature
                or (
                    start_context.current_state.diagnostics_snapshot.saveability.warning_codes
                    and self.view.ui_state.confirmed_shared_warning_fingerprint
                    != lease.fingerprint
                )
            ):
                decision = "stale"
            else:
                fingerprint_result = evaluate_delivery_commit_fingerprint(
                    start_context,
                    start_context.current_state.diagnostics_snapshot,
                )
                decision = (
                    "authorized" if fingerprint_result.allowed else "stale"
                )
        else:
            try:
                snapshot = self.view.build_current_delivery_commit_snapshot()
                fingerprint_result = evaluate_delivery_commit_fingerprint(
                    start_context,
                    snapshot,
                )
                decision = "authorized" if fingerprint_result.allowed else "stale"
            except Exception as error:
                reply.complete(error=error)
                return
        reply.complete(
            authorization=DeliveryCommitAuthorization(
                job_id=request.job_id,
                start_fingerprint=request.start_fingerprint,
                decision=decision,
            )
        )

    def request_close_delivery(self) -> bool:
        if not self.is_delivery_active():
            return False
        if self._delivery_close_pending:
            return True
        self._delivery_close_pending = True
        self.request_cancel_audio_worker()
        return True

    def _reconcile_delivery_close_state(self) -> bool:
        """Hold close until a worker terminal event, or settle an orphaned UI state."""
        if not self.delivery_may_be_active:
            return True
        if self._delivery_worker is not None:
            self._delivery_close_pending = True
            try:
                self._delivery_worker.cancel()
            except Exception:
                pass
            self.update_status("MMD一括出力の終了を待っています。")
            return False

        view = self.view
        state = view.ui_state.audio_worker_state if view is not None else None
        binding = self._active_delivery_binding
        job_id = (
            state.audio_job_id
            if state is not None and state.kind == AudioWorkerKind.DELIVERY_PACKAGE
            else binding[0]
            if binding is not None
            else None
        )
        self._delivery_terminal_received = True
        self._delivery_worker = None
        self._active_delivery_binding = None
        self._active_delivery_save_lease = None
        self._delivery_close_pending = False
        self._audio_worker_previous_status_key = None
        if view is not None:
            view.ui_state.set_busy(False)
            if job_id is not None:
                self._set_audio_worker_state(
                    job_id,
                    AudioWorkerKind.DELIVERY_PACKAGE,
                    AudioWorkerStatus.FAILED,
                    "MMD一括出力失敗",
                )
            self.update_status("MMD一括出力失敗")
            try:
                view.sync_ui_state()
            except Exception:
                pass
        return True

    def _delivery_terminal_is_current(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        projection_generation: int,
        result: DeliveryTerminalResult,
    ) -> bool:
        if self.view is None or self._delivery_terminal_received:
            return False
        if not isinstance(result, DeliveryTerminalResult) or result.job_id != audio_job_id:
            return False
        if self._active_delivery_binding != (
            audio_job_id,
            kind,
            projection_generation,
        ):
            return False
        st = self.view.ui_state
        state = st.audio_worker_state
        return bool(
            kind == AudioWorkerKind.DELIVERY_PACKAGE
            and st.is_current_audio_job(audio_job_id)
            and state is not None
            and state.audio_job_id == audio_job_id
            and state.kind == kind
            and state.is_active
        )

    def _on_delivery_worker_error(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        projection_generation: int,
        error: Exception,
    ) -> None:
        if self.view is None or self._delivery_terminal_received:
            return
        result = DeliveryTerminalResult(
            job_id=audio_job_id,
            primary_status="failed",
            primary_error_code="delivery_worker_failed",
            committed=False,
            final_path=None,
            staging_path=None,
            cleanup_status="not_required",
            commit_phase="before_commit",
            artifact_phase=None,
        )
        self._on_delivery_worker_terminal(
            audio_job_id,
            kind,
            projection_generation,
            result,
        )

    def _on_delivery_worker_terminal(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        projection_generation: int,
        result: DeliveryTerminalResult,
    ) -> None:
        if not self._delivery_terminal_is_current(
            audio_job_id,
            kind,
            projection_generation,
            result,
        ):
            self.record_debug_operation_event(
                "delivery_package_export",
                "ignored",
                source="worker",
                job_kind="delivery_package",
                job_id=audio_job_id,
                reason_code="stale_delivery_result",
            )
            return
        self._delivery_terminal_received = True
        worker = self._delivery_worker
        self._delivery_worker = None
        self._active_delivery_binding = None
        self._active_delivery_save_lease = None
        st = self.view.ui_state
        if result.committed:
            status = AudioWorkerStatus.COMPLETED
            message = "MMD一括出力成功"
        elif result.primary_status == "cancelled":
            status = AudioWorkerStatus.CANCELLED
            message = "MMD一括出力をキャンセルしました"
        else:
            status = AudioWorkerStatus.FAILED
            message = "MMD一括出力失敗"
        st.set_busy(False)
        if self._audio_worker_previous_status_key is not None:
            st.status_key = self._audio_worker_previous_status_key
        self._audio_worker_previous_status_key = None
        self._set_audio_worker_state(audio_job_id, kind, status, message)
        operation_status = (
            "cancelled"
            if result.primary_status == "cancelled"
            else "completed"
            if result.primary_status == "success" and result.committed
            else "failed"
        )
        self._finish_debug_audio_operation(
            audio_job_id,
            operation_status,
            kind=kind,
            reason_code=(
                result.primary_error_code
                or ("delivery_committed" if result.committed else "delivery_terminal")
            ),
            payload={
                "committed": result.committed,
                "file_basename": (
                    result.final_path.name if result.final_path is not None else None
                ),
            },
        )
        close_pending = self._delivery_close_pending
        self._delivery_close_pending = False
        try:
            self.view.sync_ui_state()
        except Exception:
            pass
        cleanup_failed = result.cleanup_status == "partial_output_cleanup_failed"
        if close_pending:
            if cleanup_failed:
                cleanup_prefix = (
                    "MMD一括出力は完了しました。"
                    if result.committed
                    else "MMD一括出力は終了しました。"
                )
                wx.MessageBox(
                    cleanup_prefix
                    + "一時出力の自動cleanupに失敗しました。"
                    "残存ファイルを確認してください。",
                    "一時出力cleanup警告",
                    wx.OK | wx.ICON_WARNING,
                    self.view,
                )
            self.request_exit()
            return
        if result.committed or result.primary_status == "cancelled":
            self.update_status(message)
            return
        error_code = result.primary_error_code or "delivery_worker_failed"
        safe_message = _DELIVERY_ERROR_MESSAGES.get(
            error_code,
            "一括出力を完了できませんでした。現在の状態を確認して再実行してください。",
        )
        if cleanup_failed:
            safe_message += "\n一時出力の自動cleanupにも失敗しました。"
        self.update_status(message)
        wx.MessageBox(
            safe_message,
            "MMD一括出力エラー",
            wx.OK | wx.ICON_ERROR,
            self.view,
        )

    def start_whisper_availability_scan(self) -> bool:
        """Start the one-shot B3 local-only availability scan after startup projection."""
        if self._startup_diagnostics is not None:
            self._startup_diagnostics.record_scan_requested()
        if (
            self.view is None
            or self._is_shutting_down
            or self.whisper_model_store is None
            or self._whisper_scan_started
        ):
            if self._startup_diagnostics is not None:
                reason_code, failure_code = self._scan_not_started_reason()
                self._startup_diagnostics.record_scan_not_started(
                    reason_code,
                    failure_code=failure_code,
                )
            return False
        self._whisper_scan_started = True
        return self.start_whisper_availability_rescan(_request_logged=True)

    def _scan_not_started_reason(self) -> tuple[str, str | None]:
        if self.view is None:
            return "controller_unavailable", None
        if self._is_shutting_down:
            return "shutdown", None
        if self.whisper_model_store is None:
            state = self.view.ui_state.whisper_model_selection
            failure_code = state.availability_scan_failure_code
            if failure_code in {
                "manifest_invalid",
                "storage_path_invalid",
                "storage_path_remote",
            }:
                return failure_code, failure_code
            return "store_unavailable", None
        if self._whisper_scan_started:
            return "already_started", None
        return "start_rejected", "scan_start_rejected"

    def start_whisper_availability_rescan(self, *, _request_logged: bool = False) -> bool:
        """Start a reusable local-only availability projection scan."""
        if self._startup_diagnostics is not None and not _request_logged:
            self._startup_diagnostics.record_scan_requested()
        if (
            self.view is None
            or self._is_shutting_down
            or self.whisper_model_store is None
        ):
            if self._startup_diagnostics is not None:
                reason_code, failure_code = self._scan_not_started_reason()
                self._startup_diagnostics.record_scan_not_started(
                    reason_code,
                    failure_code=failure_code,
                )
            return False
        state = self.view.ui_state.whisper_model_selection
        self._whisper_scan_job_id += 1
        self._whisper_scan_generation += 1
        job_id = self._whisper_scan_job_id
        scan_generation = self._whisper_scan_generation
        self.view.ui_state.whisper_model_selection = replace(
            state,
            availability=(),
            availability_scan_status=WHISPER_AVAILABILITY_SCAN_PENDING,
            availability_scan_job_id=job_id,
            availability_scan_generation=scan_generation,
            availability_scan_failure_code=None,
            availability_scan_failure_detail=None,
            notice=(
                state.notice
                if state.active_config_status != "valid"
                else ""
            ),
        )
        self.view.sync_ui_state(adjustment_only=True)
        worker = WhisperAvailabilityWorker(
            job_id=job_id,
            scan_generation=scan_generation,
            store=self.whisper_model_store,
            result_callback=self._on_whisper_availability_scan_result,
        )
        self._whisper_availability_worker = worker
        try:
            worker.start()
        except Exception:
            self._whisper_availability_worker = None
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.record_scan_not_started(
                    "start_rejected",
                    failure_code="scan_start_rejected",
                )
            raise
        if self._startup_diagnostics is not None:
            self._startup_diagnostics.record_scan_started(job_id, scan_generation)
            self._schedule_whisper_scan_slow_check(job_id, scan_generation)
        return True

    def _schedule_whisper_scan_slow_check(
        self,
        job_id: int,
        scan_generation: int,
    ) -> None:
        if self._startup_diagnostics is None:
            return
        self._stop_whisper_scan_slow_check()
        try:
            self._whisper_scan_slow_key = (job_id, scan_generation)
            self._whisper_scan_slow_timer = wx.CallLater(
                SCAN_SLOW_THRESHOLD_MS,
                self._on_whisper_scan_slow_timeout,
                job_id,
                scan_generation,
            )
        except Exception as error:
            self._whisper_scan_slow_key = None
            self._whisper_scan_slow_timer = None
            self._startup_diagnostics.log_event(
                "diagnostics",
                "diagnostic_check_failed",
                "warning",
                failure_code="unknown_failure",
                exception=error,
            )

    def _stop_whisper_scan_slow_check(
        self,
        job_id: int | None = None,
        scan_generation: int | None = None,
    ) -> None:
        key = self._whisper_scan_slow_key
        if key is None or (
            job_id is not None
            and scan_generation is not None
            and key != (job_id, scan_generation)
        ):
            return
        timer = self._whisper_scan_slow_timer
        self._whisper_scan_slow_key = None
        self._whisper_scan_slow_timer = None
        if timer is not None:
            try:
                timer.Stop()
            except Exception:
                pass

    def _on_whisper_scan_slow_timeout(
        self,
        job_id: int,
        scan_generation: int,
    ) -> None:
        self._whisper_scan_slow_timer = None
        self._whisper_scan_slow_key = None
        if (
            self.view is None
            or self._is_shutting_down
            or self._startup_diagnostics is None
        ):
            return
        state = self.view.ui_state.whisper_model_selection
        if (
            state.availability_scan_job_id != job_id
            or state.availability_scan_generation != scan_generation
            or state.availability_scan_status != WHISPER_AVAILABILITY_SCAN_PENDING
        ):
            return
        self._startup_diagnostics.record_scan_slow(job_id, scan_generation)

    def _on_whisper_availability_scan_result(
        self,
        result: WhisperAvailabilityScanResult,
    ) -> None:
        if not isinstance(result, WhisperAvailabilityScanResult):
            return
        if self.view is None or self._is_shutting_down:
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.record_callback_ignored_after_shutdown(
                    result.job_id,
                    result.scan_generation,
                )
            return
        state = self.view.ui_state.whisper_model_selection
        if (
            result.job_id != self._whisper_scan_job_id
            or result.scan_generation != self._whisper_scan_generation
            or result.job_id != state.availability_scan_job_id
            or result.scan_generation != state.availability_scan_generation
        ):
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.record_scan_stale(
                    result.job_id,
                    result.scan_generation,
                )
            return
        self._stop_whisper_scan_slow_check(
            result.job_id,
            result.scan_generation,
        )
        self._whisper_availability_worker = None
        if result.succeeded:
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.record_scan_result(
                    result.job_id,
                    result.scan_generation,
                    succeeded=True,
                )
            notice = (
                state.notice
                if state.active_config_status != "valid"
                else ""
            )
            self.view.ui_state.whisper_model_selection = replace(
                state,
                availability=result.availability,
                availability_scan_status=WHISPER_AVAILABILITY_SCAN_SUCCEEDED,
                availability_scan_failure_code=None,
                availability_scan_failure_detail=None,
                notice=notice,
            )
        else:
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.record_scan_result(
                    result.job_id,
                    result.scan_generation,
                    succeeded=False,
                    failure_code="availability_scan_failed",
                )
            self.view.ui_state.whisper_model_selection = replace(
                state,
                availability=(),
                availability_scan_status=WHISPER_AVAILABILITY_SCAN_FAILED,
                availability_scan_failure_code=result.failure_code,
                availability_scan_failure_detail=result.failure_detail,
                notice=format_whisper_failure_notice(result.failure_code),
            )
        self.view.sync_ui_state(adjustment_only=True)

    def start_whisper_model_download(
        self,
        model_key: str,
        expected_panel_revision: int,
        *,
        confirmed: bool = False,
        operation_handle: OperationHandle | None = None,
    ) -> bool:
        if not confirmed or not self._whisper_management_request_is_allowed(
            model_key,
            expected_panel_revision,
        ):
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("confirmation_required" if not confirmed else "management_request_rejected"),
            )
            return False
        if self.whisper_model_catalog is None or self.whisper_model_store is None:
            blocked = self._finish_whisper_management_blocked(
                model_key,
                "storage_path_invalid",
            )
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="storage_path_invalid",
            )
            return blocked
        try:
            spec = self.whisper_model_catalog.get(model_key)
        except Exception:
            blocked = self._finish_whisper_management_blocked(model_key, "model_key_unsupported")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_key_unsupported",
            )
            return blocked

        self._whisper_management_job_id += 1
        job_id = self._whisper_management_job_id
        state = self.view.ui_state.whisper_model_selection
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=True,
            management_operation=MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
            management_phase="preflight",
            management_job_id=job_id,
            management_model_key=model_key,
            management_received_bytes=0,
            management_expected_bytes=spec.size_bytes,
            management_failure_code=None,
            management_failure_detail=None,
            management_cleanup_status=None,
            notice="保存先を確認しています。",
        )
        self.view.sync_ui_state(adjustment_only=True)
        try:
            preflight = self.whisper_model_store.preflight_download(model_key)
        except Exception as error:
            self._project_whisper_management_failure(
                job_id,
                MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
                model_key,
                "storage_preflight_failed",
                _summarize_technical_error(error),
                phase="blocked",
            )
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="storage_preflight_failed",
            )
            return False
        if not preflight.succeeded:
            self._project_whisper_management_failure(
                job_id,
                MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
                model_key,
                preflight.failure_code or "storage_preflight_failed",
                preflight.message,
                phase="blocked",
            )
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code=preflight.failure_code or "storage_preflight_failed",
            )
            return False

        state = self.view.ui_state.whisper_model_selection
        if (
            self._is_shutting_down
            or not state.management_busy
            or state.management_job_id != job_id
        ):
            self.finish_debug_operation(
                operation_handle,
                "ignored",
                reason_code="management_request_stale",
            )
            return False
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_phase="downloading",
            notice="Whisperモデルを取得しています。",
        )
        self.view.sync_ui_state(adjustment_only=True)
        worker = WhisperModelManagementWorker(
            job_id=job_id,
            operation=MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
            model_key=model_key,
            catalog=self.whisper_model_catalog,
            store=self.whisper_model_store,
            preflight=preflight,
            result_callback=self._on_whisper_management_result,
            progress_callback=self._on_whisper_management_progress,
        )
        self._whisper_management_worker = worker
        try:
            worker.start()
        except Exception:
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="worker_start_failed",
                payload={"model_key": model_key},
            )
            raise
        self._bind_whisper_debug_operation(
            MODEL_MANAGEMENT_OPERATION_DOWNLOAD,
            job_id,
            operation_handle,
            model_key=model_key,
        )
        return True

    def start_whisper_model_delete(
        self,
        model_key: str,
        expected_panel_revision: int,
        *,
        confirmed: bool = False,
        operation_handle: OperationHandle | None = None,
    ) -> bool:
        if not confirmed or not self._whisper_management_request_is_allowed(
            model_key,
            expected_panel_revision,
        ):
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=("confirmation_required" if not confirmed else "management_request_rejected"),
            )
            return False
        if self.whisper_model_store is None or self.whisper_model_catalog is None:
            blocked = self._finish_whisper_management_blocked(
                model_key,
                "storage_path_invalid",
            )
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="storage_path_invalid",
            )
            return blocked
        state = self.view.ui_state.whisper_model_selection
        availability = next(
            (item for item in state.availability if item.model_key == model_key),
            None,
        )
        if availability is None or not availability.is_verified:
            blocked = self._finish_whisper_management_blocked(model_key, "delete_failed")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="delete_model_unavailable",
            )
            return blocked
        self._whisper_management_job_id += 1
        job_id = self._whisper_management_job_id
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=True,
            management_operation=MODEL_MANAGEMENT_OPERATION_DELETE,
            management_phase="verifying",
            management_job_id=job_id,
            management_model_key=model_key,
            management_received_bytes=0,
            management_expected_bytes=0,
            management_failure_code=None,
            management_failure_detail=None,
            management_cleanup_status=None,
            notice="Whisperモデルの削除条件を確認しています。",
        )
        self.view.sync_ui_state(adjustment_only=True)
        worker = WhisperModelManagementWorker(
            job_id=job_id,
            operation=MODEL_MANAGEMENT_OPERATION_DELETE,
            model_key=model_key,
            catalog=self.whisper_model_catalog,
            store=self.whisper_model_store,
            result_callback=self._on_whisper_management_result,
            progress_callback=self._on_whisper_management_progress,
            ownership_provider=(
                self._whisper_ownership_provider
                or self._ownership_permit_for_delete
            ),
        )
        self._whisper_management_worker = worker
        try:
            worker.start()
        except Exception:
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="worker_start_failed",
                payload={"model_key": model_key},
            )
            raise
        self._bind_whisper_debug_operation(
            MODEL_MANAGEMENT_OPERATION_DELETE,
            job_id,
            operation_handle,
            model_key=model_key,
        )
        return True

    def start_whisper_model_apply(
        self,
        model_key: str,
        expected_panel_revision: int,
        *,
        operation_handle: OperationHandle | None = None,
    ) -> bool:
        if (
            self.view is None
            or self._is_shutting_down
            or self.view.ui_state.is_busy
            or self.view.ui_state.output_edit_draft_dirty
            or self.view.ui_state.whisper_model_selection.management_busy
            or expected_panel_revision
            != self.view.ui_state.whisper_model_selection.panel_revision
            or model_key
            != self.view.ui_state.whisper_model_selection.selected_model_key
            or self.whisper_model_store is None
            or self.whisper_model_runtime is None
        ):
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_apply_request_rejected",
            )
            return False
        state = self.view.ui_state.whisper_model_selection
        availability = next(
            (item for item in state.availability if item.model_key == model_key),
            None,
        )
        if availability is None or not availability.is_verified:
            self._finish_whisper_apply_failure(model_key, "model_unavailable", "選択モデルは未検証です。")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="model_unavailable",
            )
            return False
        if (
            model_key == state.active_model_key
            and availability.manifest_identity == state.active_manifest_identity
        ):
            self.finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="model_already_active",
                payload={"model_key": model_key},
            )
            return False
        try:
            request = build_verified_analysis_model_request(availability)
        except WhisperModelRuntimeError as error:
            self._finish_whisper_apply_failure(model_key, error.code, str(error))
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code=error.code,
            )
            return False

        self._whisper_apply_job_id += 1
        job_id = self._whisper_apply_job_id
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=True,
            management_operation=WHISPER_MANAGEMENT_OPERATION_APPLY,
            management_phase="verifying",
            management_job_id=job_id,
            management_model_key=model_key,
            management_failure_code=None,
            management_failure_detail=None,
            notice="選択したWhisperモデルを準備しています。",
        )
        self.view.sync_ui_state(adjustment_only=True)
        worker = WhisperModelApplyWorker(
            job_id=job_id,
            request=request,
            runtime=self.whisper_model_runtime,
            result_callback=self._on_whisper_model_apply_result,
        )
        self._whisper_apply_worker = worker
        try:
            worker.start()
        except Exception:
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="worker_start_failed",
                payload={"model_key": model_key},
            )
            raise
        self._bind_whisper_debug_operation(
            WHISPER_MANAGEMENT_OPERATION_APPLY,
            job_id,
            operation_handle,
            model_key=model_key,
        )
        return True

    def _finish_whisper_apply_failure(
        self,
        model_key: str,
        failure_code: str,
        failure_detail: str,
    ) -> None:
        if self.view is None:
            return
        state = self.view.ui_state.whisper_model_selection
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=False,
            management_operation="idle",
            management_phase="blocked",
            management_model_key=model_key,
            management_failure_code=failure_code,
            management_failure_detail=failure_detail,
            loaded_whisper_model_key=None,
            loaded_whisper_manifest_identity=None,
            notice=format_whisper_failure_notice(failure_code),
        )
        self.view.sync_ui_state(adjustment_only=True)

    def _reject_whisper_apply_candidate(self, candidate) -> None:
        if self.whisper_model_runtime is None:
            return
        try:
            self.whisper_model_runtime.reject_candidate(candidate)
        except Exception:
            pass

    def _on_whisper_model_apply_result(
        self,
        result: WhisperModelApplyResult,
    ) -> None:
        if not isinstance(result, WhisperModelApplyResult):
            return
        if self.view is None or self._is_shutting_down:
            if result.candidate is not None:
                self._reject_whisper_apply_candidate(result.candidate)
            return
        state = self.view.ui_state.whisper_model_selection
        if (
            result.job_id != state.management_job_id
            or result.model_key != state.management_model_key
            or state.management_operation != WHISPER_MANAGEMENT_OPERATION_APPLY
        ):
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "ignored",
                reason_code="stale_model_apply_result",
                model_key=result.model_key,
            )
            if result.candidate is not None:
                self._reject_whisper_apply_candidate(result.candidate)
            return
        self._whisper_apply_worker = None
        if result.status == MODEL_APPLY_STATUS_CANCELLED:
            self._finish_whisper_apply_failure(
                result.model_key,
                "model_apply_cancelled",
                "Whisperモデルの適用をキャンセルしました。",
            )
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "cancelled",
                reason_code="model_apply_cancelled",
                model_key=result.model_key,
            )
            return
        if result.status != MODEL_APPLY_STATUS_READY or result.candidate is None:
            self._finish_whisper_apply_failure(
                result.model_key,
                result.failure_code or "model_apply_failed",
                result.failure_detail,
            )
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "failed",
                reason_code=result.failure_code or "model_apply_failed",
                model_key=result.model_key,
            )
            return

        if self.whisper_model_runtime is None:
            self._finish_whisper_apply_failure(result.model_key, "model_apply_failed", "Whisper runtime is unavailable.")
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "failed",
                reason_code="model_apply_failed",
                model_key=result.model_key,
            )
            return
        if self._pending_save:
            self.flush_pending_save()
        settings_result = self.settings_store.load()
        if settings_result.had_error:
            self._reject_whisper_apply_candidate(result.candidate)
            self._finish_whisper_apply_failure(result.model_key, "settings_load_failed", settings_result.load_error or "")
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "failed",
                reason_code="settings_load_failed",
                model_key=result.model_key,
            )
            return
        settings = dict(settings_result.settings)
        settings["selected_whisper_model_key"] = result.model_key
        settings["active_whisper_model_key"] = result.model_key
        settings["active_whisper_manifest_identity"] = (
            result.candidate.session.identity.manifest_identity
        )
        save_result = self.settings_store.save(settings)
        if not save_result.succeeded:
            self._reject_whisper_apply_candidate(result.candidate)
            self._finish_whisper_apply_failure(
                result.model_key,
                "settings_save_failed",
                save_result.error_message or "",
            )
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "failed",
                reason_code="settings_save_failed",
                model_key=result.model_key,
            )
            return
        self._pending_save = False
        self._pending_settings_save_kind = "none"
        self._coalesced_save_timer.Stop()
        try:
            session = self.whisper_model_runtime.commit_candidate(result.candidate)
        except Exception as error:
            try:
                self.whisper_model_runtime.reject_candidate(result.candidate)
            except Exception:
                pass
            self._finish_whisper_apply_failure(result.model_key, "model_apply_failed", str(error))
            self._finish_whisper_debug_operation(
                WHISPER_MANAGEMENT_OPERATION_APPLY,
                result.job_id,
                "failed",
                reason_code="model_apply_failed",
                model_key=result.model_key,
            )
            return

        self.view.ui_state.invalidate_analysis()
        self.view.ui_state.whisper_model_selection = replace(
            state,
            active_model_key=session.identity.model_key,
            active_manifest_identity=session.identity.manifest_identity,
            loaded_whisper_model_key=session.identity.model_key,
            loaded_whisper_manifest_identity=session.identity.manifest_identity,
            analysis_whisper_model_key=None,
            analysis_whisper_manifest_identity=None,
            retained_whisper_model_key=None,
            retained_whisper_timing_model_identity=None,
            analysis_rebuild_reason="model_changed",
            whisper_failure_class="none",
            whisper_failure_detail_code=None,
            whisper_failure_detail=None,
            management_busy=False,
            management_operation="idle",
            management_phase="finished",
            management_failure_code=None,
            management_failure_detail=None,
            notice="Whisperモデルを適用しました。再解析を開始します。",
            panel_revision=state.panel_revision + 1,
        )
        if self._startup_state is not None:
            startup_settings = self._startup_state.get("settings")
            if isinstance(startup_settings, dict):
                startup_settings.update(
                    {
                        "selected_whisper_model_key": result.model_key,
                        "active_whisper_model_key": result.model_key,
                        "active_whisper_manifest_identity": session.identity.manifest_identity,
                    }
                )
        self.view.sync_ui_state()
        self._finish_whisper_debug_operation(
            WHISPER_MANAGEMENT_OPERATION_APPLY,
            result.job_id,
            "completed",
            reason_code="whisper_model_applied",
            model_key=result.model_key,
        )
        if self.view.ui_state.analysis_start_ready:
            wx.CallAfter(self.view._run_analysis)

    def request_cancel_whisper_management(
        self,
        job_id: int | None = None,
        expected_panel_revision: int | None = None,
    ) -> bool:
        if self.view is None or self._is_shutting_down:
            return False
        state = self.view.ui_state.whisper_model_selection
        worker = self._whisper_management_worker
        if state.management_operation == WHISPER_MANAGEMENT_OPERATION_APPLY:
            worker = self._whisper_apply_worker
        if not state.management_busy or worker is None:
            return False
        if job_id is not None and job_id != state.management_job_id:
            return False
        if (
            expected_panel_revision is not None
            and expected_panel_revision != state.panel_revision
        ):
            return False
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_phase="cancelling",
            notice="キャンセル中です。取得済みの一時ファイルを整理しています。",
        )
        self.view.sync_ui_state(adjustment_only=True)
        handle = self._whisper_debug_operations.get(
            (state.management_operation, state.management_job_id)
        )
        cancel_accepted = worker.cancel()
        self.record_debug_operation_phase(
            handle,
            "cancel_request",
            "requested" if cancel_accepted else "rejected",
            job_kind=f"whisper_{state.management_operation}",
            job_id=state.management_job_id,
            payload={"model_key": state.management_model_key},
            reason_code="cancel_accepted" if cancel_accepted else "worker_finishing",
        )
        return True

    def change_whisper_storage_root(
        self,
        configured_path: str,
        expected_panel_revision: int,
        *,
        confirmed: bool = False,
    ) -> bool:
        if (
            not confirmed
            or self.view is None
            or self._is_shutting_down
            or self.view.ui_state.is_busy
            or self.view.ui_state.whisper_model_selection.management_busy
            or expected_panel_revision
            != self.view.ui_state.whisper_model_selection.panel_revision
        ):
            return False
        root_resolution = resolve_whisper_models_dir(configured_path)
        if not root_resolution.succeeded or root_resolution.resolved_path is None:
            return self._finish_whisper_storage_change_failure(
                root_resolution.failure_code or "storage_path_invalid",
            )
        if self.whisper_model_runtime is not None and not self.whisper_model_runtime.unload():
            return self._finish_whisper_storage_change_failure("delete_blocked_ownership")
        current_state = self.view.ui_state.whisper_model_selection
        self.view.ui_state.whisper_model_selection = replace(
            current_state,
            loaded_whisper_model_key=None,
            loaded_whisper_manifest_identity=None,
        )
        self.view.sync_ui_state(adjustment_only=True)
        settings_result = self.settings_store.load()
        if settings_result.had_error:
            return self._finish_whisper_storage_change_failure("settings_load_failed")
        snapshot = dict(settings_result.settings)
        snapshot["whisper_models_dir"] = str(root_resolution.resolved_path)
        try:
            new_store = WhisperModelStore(
                root_resolution.resolved_path,
                catalog=self.whisper_model_catalog,
            )
            new_runtime = WhisperModelRuntime(catalog=self.whisper_model_catalog)
        except Exception:
            return self._finish_whisper_storage_change_failure("storage_path_invalid")
        save_result = self.settings_store.save(snapshot)
        if not save_result.succeeded:
            return self._finish_whisper_storage_change_failure("settings_save_failed")
        self.whisper_model_store = new_store
        self.whisper_model_runtime = new_runtime
        if self._startup_state is not None:
            startup_settings = self._startup_state.get("settings")
            if isinstance(startup_settings, dict):
                startup_settings["whisper_models_dir"] = str(
                    root_resolution.resolved_path
                )
        state = self.view.ui_state.whisper_model_selection
        self.view.ui_state.whisper_model_selection = replace(
            state,
            storage_root_display=str(root_resolution.resolved_path),
            storage_location_kind=_storage_display_metadata(root_resolution)[0],
            storage_location_display=_storage_display_metadata(root_resolution)[1],
            availability=(),
            availability_scan_status=WHISPER_AVAILABILITY_SCAN_PENDING,
            availability_scan_failure_code=None,
            availability_scan_failure_detail=None,
            notice="新しい保存先を確認しています。",
        )
        self.view.sync_ui_state(adjustment_only=True)
        return self.start_whisper_availability_rescan()

    def _finish_whisper_storage_change_failure(self, failure_code: str) -> bool:
        if self.view is None:
            return False
        state = self.view.ui_state.whisper_model_selection
        self.view.ui_state.whisper_model_selection = replace(
            state,
            notice=format_whisper_failure_notice(failure_code),
        )
        self.view.sync_ui_state(adjustment_only=True)
        return False

    def _whisper_management_request_is_allowed(
        self,
        model_key: str,
        expected_panel_revision: int,
    ) -> bool:
        if (
            self.view is None
            or self._is_shutting_down
            or self.view.ui_state.is_busy
            or self.view.ui_state.whisper_model_selection.management_busy
            or expected_panel_revision
            != self.view.ui_state.whisper_model_selection.panel_revision
            or model_key
            != self.view.ui_state.whisper_model_selection.selected_model_key
            or self.whisper_model_catalog is None
        ):
            return False
        try:
            self.whisper_model_catalog.get(model_key)
        except Exception:
            return False
        return True

    def _finish_whisper_management_blocked(
        self,
        model_key: str,
        failure_code: str,
    ) -> bool:
        if self.view is None:
            return False
        state = self.view.ui_state.whisper_model_selection
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=False,
            management_operation="idle",
            management_phase="blocked",
            management_model_key=model_key,
            management_failure_code=failure_code,
            management_failure_detail=None,
            management_cleanup_status=None,
            notice=format_whisper_failure_notice(failure_code),
        )
        self.view.sync_ui_state(adjustment_only=True)
        return False

    def _on_whisper_management_progress(
        self,
        progress: ModelManagementProgress,
    ) -> None:
        if not isinstance(progress, ModelManagementProgress):
            return
        if self.view is None or self._is_shutting_down:
            return
        state = self.view.ui_state.whisper_model_selection
        if (
            not state.management_busy
            or progress.job_id != state.management_job_id
            or progress.model_key != state.management_model_key
            or progress.operation != state.management_operation
        ):
            return
        received = progress.received_bytes
        expected = progress.expected_bytes or state.management_expected_bytes
        if expected and received > expected:
            return
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_phase=progress.phase,
            management_received_bytes=received,
            management_expected_bytes=expected,
        )
        self.view.sync_ui_state(adjustment_only=True)

    def _on_whisper_management_result(
        self,
        result: ModelManagementResult,
    ) -> None:
        if not isinstance(result, ModelManagementResult):
            return
        if self.view is None or self._is_shutting_down:
            return
        state = self.view.ui_state.whisper_model_selection
        if (
            result.job_id != state.management_job_id
            or result.model_key != state.management_model_key
            or result.operation != state.management_operation
        ):
            self._finish_whisper_debug_operation(
                result.operation,
                result.job_id,
                "ignored",
                reason_code="stale_management_result",
                model_key=result.model_key,
            )
            return
        self._whisper_management_worker = None
        if result.status == MODEL_MANAGEMENT_STATUS_SUCCEEDED:
            if result.operation == MODEL_MANAGEMENT_OPERATION_DELETE and self.view is not None:
                current_state = self.view.ui_state.whisper_model_selection
                if result.model_key in {
                    current_state.active_model_key,
                    current_state.analysis_whisper_model_key,
                }:
                    self.view.ui_state.invalidate_analysis()
                    self.view.ui_state.whisper_model_selection = replace(
                        current_state,
                        loaded_whisper_model_key=None,
                        retained_whisper_model_key=None,
                        analysis_whisper_model_key=None,
                        analysis_whisper_manifest_identity=None,
                        retained_whisper_timing_model_identity=None,
                        whisper_failure_class="model_unavailable",
                    )
                state = self.view.ui_state.whisper_model_selection
            notice = "管理操作が完了しました。保存状態を再確認しています。"
            self.view.ui_state.whisper_model_selection = replace(
                state,
                management_busy=False,
                management_operation="idle",
                management_phase="finished",
                management_failure_code=None,
                management_failure_detail=None,
                management_cleanup_status=result.cleanup_status,
                notice=notice,
            )
            self.view.sync_ui_state(adjustment_only=True)
            self.start_whisper_availability_rescan()
            self._finish_whisper_debug_operation(
                result.operation,
                result.job_id,
                "completed",
                reason_code="whisper_management_completed",
                model_key=result.model_key,
            )
            return
        if result.status == MODEL_MANAGEMENT_STATUS_CANCELLED:
            notice = "Whisperモデルの取得をキャンセルしました。再取得は最初から開始します。"
            phase = "finished"
        elif result.status == MODEL_MANAGEMENT_STATUS_BLOCKED:
            notice = format_whisper_failure_notice(
                result.failure_code or "delete_blocked_ownership"
            )
            phase = "blocked"
        else:
            notice = format_whisper_failure_notice(
                result.failure_code or "download_connection_failed"
            )
            phase = "finished"
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=False,
            management_operation="idle",
            management_phase=phase,
            management_failure_code=result.failure_code,
            management_failure_detail=result.failure_detail,
            management_cleanup_status=result.cleanup_status,
            notice=notice,
        )
        self.view.sync_ui_state(adjustment_only=True)
        terminal_status = (
            "cancelled"
            if result.status == MODEL_MANAGEMENT_STATUS_CANCELLED
            else "rejected"
            if result.status == MODEL_MANAGEMENT_STATUS_BLOCKED
            else "failed"
        )
        self._finish_whisper_debug_operation(
            result.operation,
            result.job_id,
            terminal_status,
            reason_code=result.failure_code or f"whisper_management_{result.status}",
            model_key=result.model_key,
        )

    def _project_whisper_management_failure(
        self,
        job_id: int,
        operation: str,
        model_key: str,
        failure_code: str,
        failure_detail: str,
        *,
        phase: str,
    ) -> None:
        if self.view is None:
            return
        state = self.view.ui_state.whisper_model_selection
        if (
            state.management_job_id != job_id
            or state.management_operation != operation
            or state.management_model_key != model_key
        ):
            return
        self._whisper_management_worker = None
        self.view.ui_state.whisper_model_selection = replace(
            state,
            management_busy=False,
            management_operation="idle",
            management_phase=phase,
            management_failure_code=failure_code,
            management_failure_detail=failure_detail,
            notice=format_whisper_failure_notice(failure_code),
        )
        self.view.sync_ui_state(adjustment_only=True)

    def _on_save_timer(self, event):
        self.flush_pending_save()

    def flush_pending_save(self, is_closing=False):
        if not self._pending_save or not self.view:
            return
            
        if self.view.ui_state.is_busy:
            return
            
        save_kind = self._pending_settings_save_kind
        self._pending_save = False
        self._pending_settings_save_kind = "none"
        st = self.view.ui_state
        if save_kind == "identity_only":
            settings_dict = {
                "active_preset_id": st.generation_state.active_preset_id,
                "active_model_profile_id": (
                    st.model_profile_state.active_model_profile_id
                ),
                "active_profile_baseline_preset_id": (
                    st.model_profile_state.active_profile_baseline_preset_id
                ),
                "selected_whisper_model_key": (
                    st.whisper_model_selection.selected_model_key
                ),
                "active_whisper_model_key": (
                    st.whisper_model_selection.active_model_key
                ),
                "active_whisper_manifest_identity": (
                    st.whisper_model_selection.active_manifest_identity
                ),
            }
        else:
            generation_settings = st.generation_state.generation_settings
            settings_dict = {
                "theme": st.theme_mode,
                "recent_text_files": st.recent_text_files,
                "recent_wav_files": st.recent_wav_files,
                "recent_audio_files": st.recent_audio_files,
                "last_vmd_output_dir": st.last_vmd_output_dir or "",
                "last_mmd_wav_export_dir": st.last_mmd_wav_export_dir or "",
                "last_text_dialog_dir": st.last_text_dialog_dir or "",
                "last_wav_dialog_dir": st.last_wav_dialog_dir or "",
                "last_audio_dialog_dir": st.last_audio_dialog_dir or "",
                "morph_upper_limit": st.resolved_morph_upper_limit,
                "closing_hold_frames": generation_settings.closing_hold_frames,
                "closing_softness_frames": generation_settings.closing_softness_frames,
                "long_vowel_mode": generation_settings.long_vowel_mode,
                "active_preset_id": st.generation_state.active_preset_id,
                "active_model_profile_id": (
                    st.model_profile_state.active_model_profile_id
                ),
                "active_profile_baseline_preset_id": (
                    st.model_profile_state.active_profile_baseline_preset_id
                ),
                "selected_whisper_model_key": (
                    st.whisper_model_selection.selected_model_key
                ),
                "active_whisper_model_key": (
                    st.whisper_model_selection.active_model_key
                ),
                "active_whisper_manifest_identity": (
                    st.whisper_model_selection.active_manifest_identity
                ),
            }
        
        result = self.settings_store.save(settings_dict)
        if not result.succeeded:
            if not is_closing and not self._first_save_failure:
                self._first_save_failure = True
                wx.MessageBox(f"設定の保存に失敗しました。\n{result.error_message}", "保存エラー", wx.OK | wx.ICON_WARNING)
        else:
            self._first_save_failure = False

    def request_select_text(self):
        self.update_status("TEXTファイル選択要求 (Stub)")

    def request_select_audio(self):
        """[MS17-B6] 音声ファイル選択要求"""
        if not self.view:
            return
        operation_handle = self.begin_debug_operation(
            "audio_input_open",
            entry="file_dialog",
        )
        path = self.view.show_audio_open_dialog()
        if path:
            self.request_open_audio_file(
                path,
                _operation_handle=operation_handle,
            )
        else:
            self.finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="file_dialog_cancelled",
            )

    def request_select_wav(self):
        """[Legacy] request_select_audio へ委譲"""
        self.request_select_audio()

    def request_open_audio_file(
        self,
        path: str,
        *,
        _operation_handle: OperationHandle | None = None,
        _source: str = "user",
        _entry: str = "audio_input",
    ):
        """[MS17-B6] 音声ファイル読み込み統合フロー"""
        operation_handle = _operation_handle or self.begin_debug_operation(
            "audio_input_open",
            payload={"file_basename": os.path.basename(path)},
            source=_source,
            entry=_entry,
        )
        if not self.view:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="view_unavailable",
            )
            return
        st = self.view.ui_state
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="busy",
            )
            return

        # 1. 既存状態の無効化
        if st.playback_active:
            self.request_playback_stop(
                _source="system",
                _reason_code="audio_reloaded",
            )
        audio_job_id = st.next_audio_job_id()
        st.invalidate_analysis()
        st.clear_transcription_state()
        self._clear_selected_audio_state()
        self.view.clear_playback_cursor()
        self.view.sync_ui_state()
        self.update_status(f"読み込み中: {os.path.basename(path)}")

        try:
            # 2. AudioInputInfo 作成 (拡張子チェック)
            input_info = build_audio_input_info(path)
            
            # 3. locate_ffmpeg_tools
            ffmpeg_tools = locate_ffmpeg_tools()
            if not ffmpeg_tools.is_complete:
                raise Exception(
                    "FFmpeg または ffprobe の実行ファイルが見つかりません。\n"
                    f"{format_locator_status(ffmpeg_tools)}\n"
                    "FFmpeg/bin フォルダ内に配置するか、PATH から実行できる状態にしてください。"
                )

            def task(cancel_token):
                runner = lambda **kwargs: run_ffprobe_json_cancellable(
                    cancel_token=cancel_token,
                    **kwargs,
                )
                probe_result = probe_audio_file(
                    input_info.source_path,
                    ffmpeg_tools.ffprobe.path,
                    runner=runner,
                )
                return {
                    "path": path,
                    "input_info": input_info,
                    "ffmpeg_tools": ffmpeg_tools,
                    "probe_result": probe_result,
                }

            self._start_audio_worker(
                audio_job_id,
                AudioWorkerKind.PROBE,
                task,
                "音声情報を確認中...",
                operation_handle=operation_handle,
            )
            
        except Exception as e:
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="audio_input_open_failed",
            )
            traceback.print_exc()
            # エラー時は状態をクリアしたままにする (invalidate_analysis済み)
            self._clear_selected_audio_state()
            
            wx.MessageBox(f"音声ファイルの読み込みに失敗しました。\n{e}", "読み込みエラー", wx.OK | wx.ICON_ERROR)
            self.update_status("音声読み込み失敗")
            self.view.placeholder_container.set_waveform_placeholder_text("読み込みエラー")
            self.view.sync_ui_state()

    def _on_audio_worker_success(self, audio_job_id: int, kind: AudioWorkerKind, result):
        if not self.view or not self._is_current_audio_worker_result(audio_job_id, kind):
            self._finish_debug_audio_operation(
                audio_job_id,
                "ignored",
                kind=kind,
                reason_code="stale_worker_result",
            )
            return
        if kind == AudioWorkerKind.PROBE:
            operation_handle = self._audio_debug_operation_handles().get(audio_job_id)
            self.operation_recorder.record_operation_phase(
                operation_handle,
                "audio_probe",
                "completed",
                job_kind=kind.name.lower(),
                job_id=audio_job_id,
                payload={"worker_kind": kind.name.lower()},
            )
        if kind == AudioWorkerKind.PROBE:
            self._on_audio_probe_success(audio_job_id, result)
        elif kind == AudioWorkerKind.ANALYSIS_WAV:
            self._on_analysis_wav_success(audio_job_id, result)
        elif kind == AudioWorkerKind.MMD_WAV:
            self._on_mmd_wav_success(audio_job_id, result)

    def _on_audio_worker_error(self, audio_job_id: int, kind: AudioWorkerKind, error: Exception):
        if not self.view:
            return
        if not self._is_current_audio_worker_result(audio_job_id, kind):
            self._finish_debug_audio_operation(
                audio_job_id,
                "ignored",
                kind=kind,
                reason_code="stale_worker_error",
            )
            return

        if kind in {AudioWorkerKind.PROBE, AudioWorkerKind.ANALYSIS_WAV}:
            self._clear_selected_audio_state()
            self.view.placeholder_container.set_waveform_placeholder_text("読み込みエラー")
            title = "読み込みエラー"
            message = f"音声ファイルの読み込みに失敗しました。\n{error}"
            status = "音声読み込み失敗"
        else:
            title = "MMD用WAV出力エラー"
            message = f"MMD用WAVの出力に失敗しました。\n{error}"
            status = "MMD用WAV出力失敗"

        self._finish_audio_worker(audio_job_id, kind, AudioWorkerStatus.FAILED, status)
        wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)

    def _on_audio_worker_cancelled(self, audio_job_id: int, kind: AudioWorkerKind):
        if not self.view:
            return
        if getattr(self, "_is_shutting_down", False):
            return
        st = self.view.ui_state
        if not st.is_current_audio_job(audio_job_id):
            self._finish_debug_audio_operation(
                audio_job_id,
                "ignored",
                kind=kind,
                reason_code="stale_worker_cancelled",
            )
            return
        worker_state = st.audio_worker_state
        if (
            worker_state is None
            or worker_state.audio_job_id != audio_job_id
            or worker_state.kind != kind
            or worker_state.status != AudioWorkerStatus.CANCELLING
        ):
            return
        message = "処理をキャンセルしました"
        self._finish_audio_worker(audio_job_id, kind, AudioWorkerStatus.CANCELLED, message)

    def _on_audio_probe_success(self, audio_job_id: int, result: dict):
        if not self.view or not self._is_current_audio_worker_result(
            audio_job_id,
            AudioWorkerKind.PROBE,
        ):
            return
        probe_result = result["probe_result"]
        if not self._confirm_long_audio_if_needed(probe_result.duration_sec):
            self._clear_selected_audio_state()
            self._finish_audio_worker(
                audio_job_id,
                AudioWorkerKind.PROBE,
                AudioWorkerStatus.CANCELLED,
                "音声読み込みをキャンセルしました",
            )
            return

        input_info = result["input_info"]
        ffmpeg_tools = result["ffmpeg_tools"]
        path = result["path"]

        def task(cancel_token):
            runner = lambda **kwargs: run_ffmpeg_analysis_wav_cancellable(
                cancel_token=cancel_token,
                **kwargs,
            )
            analysis_wav_result = convert_to_analysis_wav(
                probe_result,
                ffmpeg_tools.ffmpeg.path,
                runner=runner,
            )
            waveform_data = load_waveform_preview(analysis_wav_result.analysis_wav_path)
            analysis = analyze_wav_file(analysis_wav_result.analysis_wav_path)
            return {
                "path": path,
                "input_info": input_info,
                "probe_result": probe_result,
                "analysis_wav_result": analysis_wav_result,
                "waveform_data": waveform_data,
                "analysis": analysis,
            }

        self._start_audio_worker(
            audio_job_id,
            AudioWorkerKind.ANALYSIS_WAV,
            task,
            "解析用WAVを生成中...",
        )

    def _on_analysis_wav_success(self, audio_job_id: int, result: dict):
        if not self.view or not self._is_current_audio_worker_result(
            audio_job_id,
            AudioWorkerKind.ANALYSIS_WAV,
        ):
            return

        st = self.view.ui_state
        path = result["path"]
        input_info = result["input_info"]
        probe_result = result["probe_result"]
        analysis_wav_result = result["analysis_wav_result"]
        waveform_data = result["waveform_data"]
        analysis = result["analysis"]

        st.selected_audio_input = input_info
        st.selected_audio_probe = probe_result
        st.selected_analysis_wav = analysis_wav_result
        st.selected_wav_path = str(input_info.source_path)
        st.selected_wav_analysis = analysis
        st.last_audio_dialog_dir = os.path.dirname(path)
        st.last_wav_dialog_dir = os.path.dirname(path)

        if path in st.recent_audio_files:
            st.recent_audio_files.remove(path)
        st.recent_audio_files.insert(0, path)

        self.notify_duration_changed(analysis.duration_sec)
        self.view.set_wav_path(os.path.basename(path))
        info_text = f"Format: {probe_result.format_name}\nSample Rate: {analysis.sample_rate_hz}Hz\nChannels: {analysis.channel_count}\nDuration: {analysis.duration_sec:.2f}s"
        self.view.set_wav_info(info_text)
        self.view.placeholder_container.set_waveform_data(
            waveform_data.samples,
            waveform_data.duration_sec,
        )

        st.refresh_input_mode()
        if st.analysis_start_ready:
            st.mark_ready_for_analysis()
        else:
            st.status_key = StatusKey.INPUT_MISSING
        st.set_busy(False)
        self._audio_worker_previous_status_key = None
        self._set_audio_worker_state(
            audio_job_id,
            AudioWorkerKind.ANALYSIS_WAV,
            AudioWorkerStatus.COMPLETED,
            "音声読み込み完了",
        )
        self.update_status("音声読み込み完了")
        self.request_settings_save()
        self.view.sync_ui_state()
        self.update_status("音声読み込み完了")
        self.view._build_recent_menus()
        self._finish_debug_audio_operation(
            audio_job_id,
            "completed",
            kind=AudioWorkerKind.ANALYSIS_WAV,
            reason_code="audio_input_ready",
        )

    def _on_mmd_wav_success(self, audio_job_id: int, result):
        if not self.view or not self._is_current_audio_worker_result(
            audio_job_id,
            AudioWorkerKind.MMD_WAV,
        ):
            return
        st = self.view.ui_state
        st.last_mmd_wav_export_dir = os.path.dirname(str(result.mmd_wav_path))
        st.last_mmd_wav_output_path = str(result.mmd_wav_path)
        self._finish_audio_worker(
            audio_job_id,
            AudioWorkerKind.MMD_WAV,
            AudioWorkerStatus.COMPLETED,
            "MMD用WAV出力成功",
        )
        self.request_settings_save()
        self.view.show_mmd_wav_export_completed(result.mmd_wav_path)

    def _record_view_debug_action(self, action: str, *, payload=None, status: str = "completed"):
        callback = getattr(self.view, "record_debug_action", None) if self.view else None
        if callable(callback):
            callback(action, payload=payload, status=status)

    def request_save_vmd(self):
        if self.view is None or self._is_shutting_down:
            return False
        st = self.view.ui_state
        if st.is_busy or st.output_edit_draft_dirty:
            if st.output_edit_draft_dirty:
                self.update_status("変更未適用のため、先に変更を適用してください")
            return False
        self._record_view_debug_action(
            "vmd_save_request",
            payload={"input_mode": st.input_mode},
            status="requested",
        )

        gate = self._capture_shared_vmd_save_gate()
        if gate is None:
            self.update_status("共有最終出力を準備中です。完了後にVMD保存を再実行してください。")
            return False
        if gate.status == "blocked":
            reason = gate.blocking_codes[0]
            self._record_view_debug_action(
                "vmd_save_blocked",
                payload={"reason": reason},
                status="blocked",
            )
            self.update_status("VMD保存不可")
            return False
        if gate.status == "warning_confirmation_required":
            snapshot = gate.diagnostics_snapshot
            if snapshot is None or not self.view.confirm_vmd_save_warnings(snapshot):
                self._record_view_debug_action(
                    "vmd_save_cancelled",
                    payload={"reason": "warning_confirmation_declined"},
                    status="cancelled",
                )
                self.update_status("VMD保存をキャンセルしました")
                return False
            st.confirmed_shared_warning_fingerprint = gate.fingerprint
            gate = self._capture_shared_vmd_save_gate()
            if gate is None or gate.status != "ready":
                self.update_status("作業状態が変わったため、VMD保存を開始できませんでした")
                return False

        context = gate.context
        snapshot = gate.diagnostics_snapshot
        if context is None or snapshot is None or gate.fingerprint is None:
            self.update_status("VMD保存不可")
            return False
        path_value = self.view.show_vmd_save_dialog_and_get_path(
            st.last_vmd_output_dir or ""
        )
        if not path_value:
            self._record_view_debug_action(
                "vmd_save_cancelled",
                payload={"reason": "save_dialog_cancelled"},
                status="cancelled",
            )
            return False

        captured = self._capture_verified_vmd_save_gate_inputs()
        if captured is None:
            self._show_verified_vmd_save_error("shared_final_output_stale")
            return False
        current_context, current_snapshot, current_fingerprint, gate_inputs = captured
        if (
            current_context.identity != context.identity
            or current_context.ticket != context.ticket
            or current_context.lifecycle_epoch != context.lifecycle_epoch
            or current_context.lifecycle_signature != context.lifecycle_signature
            or current_fingerprint != gate.fingerprint
        ):
            self._show_verified_vmd_save_error("shared_final_output_stale")
            return False

        operation = self._begin_verified_vmd_save_operation(gate_inputs)
        if operation is None:
            self.update_status("VMD保存を開始できませんでした")
            return False

        try:
            final_path = Path(os.path.abspath(path_value))
            existing_identity = capture_vmd_file_identity(final_path)
        except Exception as error:
            return self._abort_verified_vmd_save_operation(
                operation,
                error_code=getattr(error, "code", "output_path_invalid"),
                detail=error,
            )
        if existing_identity is not None:
            self.view.suspend_vmd_save_progress(operation.operation_id)
            try:
                try:
                    overwrite_confirmed = self.view.confirm_vmd_overwrite(
                        str(final_path)
                    )
                except Exception as error:
                    return self._abort_verified_vmd_save_operation(
                        operation,
                        error_code="output_path_inspection_failed",
                        detail=error,
                    )
            finally:
                if (
                    self._verified_vmd_save_operation is operation
                    and not operation.cancel_requested
                    and not self._verified_vmd_close_pending
                ):
                    self.view.resume_vmd_save_progress(operation.operation_id)
            if not overwrite_confirmed:
                return self._abort_verified_vmd_save_operation(
                    operation,
                    cancelled=True,
                    message="VMD保存をキャンセルしました",
                )
            if operation.cancel_requested or self._verified_vmd_close_pending:
                return self._abort_verified_vmd_save_operation(
                    operation,
                    cancelled=True,
                    message="VMD保存をキャンセルしました",
                )
            try:
                if capture_vmd_file_identity(final_path) != existing_identity:
                    return self._abort_verified_vmd_save_operation(
                        operation,
                        error_code="output_destination_collision",
                    )
            except Exception as error:
                return self._abort_verified_vmd_save_operation(
                    operation,
                    error_code=getattr(error, "code", "output_path_inspection_failed"),
                    detail=error,
                )

        if operation.cancel_requested or self._verified_vmd_close_pending:
            return self._abort_verified_vmd_save_operation(
                operation,
                cancelled=True,
                message="VMD保存をキャンセルしました",
            )
        if not self._verified_vmd_save_snapshot_is_current(
            operation,
            current_context,
            current_snapshot,
            current_fingerprint,
        ):
            return self._abort_verified_vmd_save_operation(
                operation,
                error_code="shared_final_output_stale",
            )

        job_id = operation.job_id
        try:
            request = VerifiedVmdSaveRequest(
                job_id=job_id,
                context=current_context,
                diagnostics_snapshot=current_snapshot,
                fingerprint=current_fingerprint,
                ticket=current_context.ticket,
                lifecycle_epoch=current_context.lifecycle_epoch,
                lifecycle_signature=current_context.lifecycle_signature,
                model_name="AutoLipTool",
                output_mapping=current_context.input_identity.output_mapping,
                final_path=final_path,
                overwrite_authorized=existing_identity is not None,
                expected_existing_file_identity=existing_identity,
                protected_paths=(),
            )
            validate_vmd_save_target(request)
            lease = SaveCommitLease(
                job_id=job_id,
                ticket=request.ticket,
                lifecycle_epoch=request.lifecycle_epoch,
                binding_digest=request.context.identity.binding_digest,
                fingerprint=request.fingerprint,
                lifecycle_signature=self._save_lifecycle_signature(
                    request.lifecycle_signature
                ),
                lease_id=uuid.uuid4().hex,
            )
        except (TypeError, ValueError, VerifiedVmdSaveError) as error:
            return self._abort_verified_vmd_save_operation(
                operation,
                error_code=getattr(error, "code", "shared_final_output_stale"),
                detail=error,
            )
        if operation.cancel_requested or self._verified_vmd_close_pending:
            return self._abort_verified_vmd_save_operation(
                operation,
                cancelled=True,
                message="VMD保存をキャンセルしました",
            )
        if not self._start_verified_vmd_worker(
            request,
            lease,
            operation=operation,
            gate_inputs=gate_inputs,
        ):
            if self._verified_vmd_save_operation is operation:
                self._abort_verified_vmd_save_operation(
                    operation,
                    error_code="delivery_worker_failed",
                )
            return False
        return True

    def _capture_verified_vmd_save_gate_inputs(self):
        if self.view is None:
            return None
        state = self.view.ui_state
        if state.is_busy:
            return None
        context = state.final_output_state.current_context
        snapshot = getattr(self.view, "_shared_final_output_diagnostics", None)
        if (
            context is None
            or snapshot is None
            or snapshot.shared_final_output_identity != context.identity
            or type(snapshot.save_state_fingerprint) is not str
            or not snapshot.save_state_fingerprint
        ):
            return None
        inputs = VerifiedVmdSaveGateInputs(
            current_lifecycle_signature=(
                self.view._capture_final_output_lifecycle_signature()
            ),
            confirmed_warning_fingerprint=state.confirmed_shared_warning_fingerprint,
            application_busy=state.is_busy,
            analysis_pending=(
                state.analysis_pending_rebuild
                or bool(getattr(self.view, "_analysis_info_in_progress", False))
            ),
            expected_transition_input_digest=(
                state.final_output_state.expected_transition_input_digest
            ),
            expected_application_binding_digest=(
                state.final_output_state.expected_application_binding_digest
            ),
            expected_cleanup_input_digest=(
                getattr(context.input_identity, "cleanup_input_digest", None)
            ),
            expected_cleanup_application_binding_digest=(
                state.final_output_state.expected_cleanup_application_binding_digest
            ),
        )
        if inputs.current_lifecycle_signature != context.lifecycle_signature:
            return None
        return context, snapshot, snapshot.save_state_fingerprint, inputs

    def _begin_verified_vmd_save_operation(
        self,
        gate_inputs: VerifiedVmdSaveGateInputs,
    ) -> _VerifiedVmdSaveOperation | None:
        if self.view is None or self._is_shutting_down:
            return None
        state = self.view.ui_state
        if (
            state.is_busy
            or state.audio_worker_active
            or self._verified_vmd_worker is not None
            or self._active_verified_vmd_binding is not None
            or self._verified_vmd_save_operation is not None
        ):
            return None
        self._verified_vmd_save_operation_sequence += 1
        operation = _VerifiedVmdSaveOperation(
            operation_id=self._verified_vmd_save_operation_sequence,
            job_id=state.next_audio_job_id(),
            previous_status_key=state.status_key,
            gate_inputs=gate_inputs,
        )
        self._verified_vmd_save_operation = operation
        self._verified_vmd_close_pending = False
        self._audio_worker_previous_status_key = operation.previous_status_key
        state.set_busy(True, preserve_final_output_context=True)
        self._set_audio_worker_state(
            operation.job_id,
            AudioWorkerKind.VERIFIED_VMD_SAVE,
            AudioWorkerStatus.RUNNING,
            "VMD保存準備中...",
        )
        self.update_status("VMD保存準備中...")
        try:
            shown = self.view.show_vmd_save_progress(
                operation.operation_id,
                on_cancel=self.request_cancel_audio_worker,
                get_progress_state=lambda: self._get_vmd_save_progress_state(
                    operation.operation_id
                ),
            )
        except Exception:
            shown = False
        if not shown:
            self._finish_verified_vmd_save_operation(
                operation,
                status=AudioWorkerStatus.FAILED,
                message="VMD保存ダイアログを開始できませんでした",
            )
            return None
        self.view.update_vmd_save_action_states()
        return operation

    def _get_vmd_save_progress_state(self, operation_id: int):
        operation = self._verified_vmd_save_operation
        if operation is None or operation.operation_id != operation_id:
            return None
        worker = self._verified_vmd_worker
        if worker is None or not operation.worker_started:
            if operation.cancel_requested:
                return "キャンセル中です。処理終了を待っています…", False
            return "保存準備中…", not operation.cancel_requested
        token = worker.cancel_token
        if token.commit_result == "committed":
            return "保存したファイルを確認しています…", False
        if token.commit_started:
            return "保存を確定しています…", False
        if operation.cancel_requested or token.cancel_requested:
            return "キャンセル中です。処理終了を待っています…", False
        phases = {
            "created": "保存準備中…",
            "validating": "保存状態を確認しています…",
            "creating_temporary": "保存準備中…",
            "writing": "VMDを書き出しています…",
            "readback": "保存内容を確認しています…",
            "awaiting_commit_guard": "保存前の状態を確認しています…",
        }
        return phases.get(token.phase, "VMDを保存しています…"), True

    def _verified_vmd_save_snapshot_is_current(
        self,
        operation: _VerifiedVmdSaveOperation,
        context,
        snapshot,
        fingerprint: str,
    ) -> bool:
        if self.view is None or self._verified_vmd_save_operation is not operation:
            return False
        state = self.view.ui_state
        current_context = state.final_output_state.current_context
        current_snapshot = getattr(self.view, "_shared_final_output_diagnostics", None)
        inputs = operation.gate_inputs
        return bool(
            not self._is_shutting_down
            and not operation.cancel_requested
            and not self._verified_vmd_close_pending
            and state.is_current_audio_job(operation.job_id)
            and state.is_busy
            and current_context is not None
            and current_context.identity == context.identity
            and current_context.ticket == context.ticket
            and current_context.lifecycle_epoch == context.lifecycle_epoch
            and current_context.lifecycle_signature == inputs.current_lifecycle_signature
            and current_snapshot is not None
            and current_snapshot.shared_final_output_identity == context.identity
            and current_snapshot.save_state_fingerprint == fingerprint
            and fingerprint == snapshot.save_state_fingerprint
            and self._save_lifecycle_signature(
                self.view._capture_final_output_lifecycle_signature()
            )
            == self._save_lifecycle_signature(inputs.current_lifecycle_signature)
            and state.confirmed_shared_warning_fingerprint
            == inputs.confirmed_warning_fingerprint
            and state.final_output_state.expected_transition_input_digest
            == inputs.expected_transition_input_digest
            and state.final_output_state.expected_application_binding_digest
            == inputs.expected_application_binding_digest
            and state.final_output_state.expected_cleanup_application_binding_digest
            == inputs.expected_cleanup_application_binding_digest
            and not state.analysis_pending_rebuild
            and not bool(getattr(self.view, "_analysis_info_in_progress", False))
        )

    def _abort_verified_vmd_save_operation(
        self,
        operation: _VerifiedVmdSaveOperation,
        *,
        cancelled: bool = False,
        message: str | None = None,
        error_code: str | None = None,
        detail: BaseException | None = None,
    ) -> bool:
        self._finish_verified_vmd_save_operation(
            operation,
            status=(AudioWorkerStatus.CANCELLED if cancelled else AudioWorkerStatus.FAILED),
            message=message or ("VMD保存をキャンセルしました" if cancelled else "VMD保存失敗"),
        )
        if error_code is not None:
            self._show_verified_vmd_save_error(error_code, detail=detail)
        elif message:
            self.update_status(message)
        return False

    def _finish_verified_vmd_save_operation(
        self,
        operation: _VerifiedVmdSaveOperation,
        *,
        status: AudioWorkerStatus,
        message: str,
    ) -> None:
        if self._verified_vmd_save_operation is not operation:
            return
        close_pending = self._verified_vmd_close_pending
        self._verified_vmd_save_operation = None
        self._verified_vmd_close_pending = False
        view = self.view
        if view is not None:
            view.close_vmd_save_progress(operation.operation_id)
            state = view.ui_state
            if state.is_current_audio_job(operation.job_id):
                state.set_busy(False)
                if state.status_key == StatusKey.BUSY:
                    state.status_key = operation.previous_status_key
                self._set_audio_worker_state(
                    operation.job_id,
                    AudioWorkerKind.VERIFIED_VMD_SAVE,
                    status,
                    message,
                )
                self.update_status(message)
                view.update_vmd_save_action_states()
        self._audio_worker_previous_status_key = None
        if close_pending:
            self.request_exit()

    def _capture_shared_vmd_save_gate(self):
        if self.view is None:
            return None
        state = self.view.ui_state
        context = state.final_output_state.current_context
        snapshot = getattr(self.view, "_shared_final_output_diagnostics", None)
        if context is None or snapshot is None:
            if not state.is_busy:
                request_shared = getattr(
                    self.view, "request_shared_final_output_context", None
                )
                if callable(request_shared):
                    request_shared()
            return None
        return evaluate_shared_save_gate(
            context=context,
            diagnostics_snapshot=snapshot,
            current_lifecycle_signature=self.view._capture_final_output_lifecycle_signature(),
            confirmed_warning_fingerprint=state.confirmed_shared_warning_fingerprint,
            application_busy=state.is_busy,
            analysis_pending=(
                state.analysis_pending_rebuild
                or bool(getattr(self.view, "_analysis_info_in_progress", False))
            ),
            expected_transition_input_digest=(
                state.final_output_state.expected_transition_input_digest
            ),
            expected_application_binding_digest=(
                state.final_output_state.expected_application_binding_digest
            ),
            expected_cleanup_input_digest=(
                getattr(context.input_identity, "cleanup_input_digest", None)
            ),
            expected_cleanup_application_binding_digest=(
                state.final_output_state.expected_cleanup_application_binding_digest
            ),
        )

    @staticmethod
    def _save_lifecycle_signature(
        signature: tuple[object, ...],
    ) -> tuple[object, ...]:
        if len(signature) < 12:
            return signature
        return signature[:9] + signature[12:]

    def _start_verified_vmd_worker(
        self,
        request: VerifiedVmdSaveRequest,
        lease: SaveCommitLease,
        *,
        operation: _VerifiedVmdSaveOperation | None = None,
        gate_inputs: VerifiedVmdSaveGateInputs | None = None,
    ) -> bool:
        if self.view is None or self._is_shutting_down:
            return False
        st = self.view.ui_state
        if operation is None:
            if (
                st.is_busy
                or st.audio_worker_active
                or self._verified_vmd_worker is not None
                or self._verified_vmd_save_operation is not None
            ):
                return False
            previous_status_key = st.status_key
        else:
            if (
                self._verified_vmd_save_operation is not operation
                or operation.worker_started
                or operation.job_id != request.job_id
                or self._verified_vmd_worker is not None
                or self._active_verified_vmd_binding is not None
                or not st.is_busy
                or not st.audio_worker_active
                or operation.cancel_requested
                or self._verified_vmd_close_pending
            ):
                return False
            previous_status_key = operation.previous_status_key

        try:
            worker = VerifiedVmdSaveWorker(
                request=request,
                pre_commit_guard=self._build_verified_vmd_pre_commit_guard(request, lease),
                terminal_callback=self._on_verified_vmd_worker_terminal,
                error_callback=self._on_verified_vmd_worker_error,
                gate_inputs=gate_inputs,
            )
            self._verified_vmd_worker = worker
            self._active_verified_vmd_binding = (
                request.job_id,
                AudioWorkerKind.VERIFIED_VMD_SAVE,
                request.ticket,
            )
            self._active_verified_vmd_request = request
            self._active_save_commit_lease = lease
            self._verified_vmd_close_pending = False
            self._verified_vmd_terminal_received = False
            self._audio_worker_previous_status_key = previous_status_key
            if operation is None:
                st.set_busy(True, preserve_final_output_context=True)
                self._set_audio_worker_state(
                    request.job_id,
                    AudioWorkerKind.VERIFIED_VMD_SAVE,
                    AudioWorkerStatus.RUNNING,
                    "検証済みVMDを保存中...",
                )
            else:
                operation.worker_started = True
                self._set_audio_worker_state(
                    request.job_id,
                    AudioWorkerKind.VERIFIED_VMD_SAVE,
                    AudioWorkerStatus.RUNNING,
                    "検証済みVMDを保存中...",
                )
            self.update_status("検証済みVMDを保存中...")
            self.view.update_vmd_save_action_states()
            worker.start()
        except Exception:
            self._verified_vmd_worker = None
            self._active_verified_vmd_binding = None
            self._active_verified_vmd_request = None
            self._active_save_commit_lease = None
            self._verified_vmd_terminal_received = True
            if operation is not None:
                operation.worker_started = False
                self._finish_verified_vmd_save_operation(
                    operation,
                    status=AudioWorkerStatus.FAILED,
                    message="VMD保存失敗",
                )
            else:
                st.set_busy(False)
                if st.status_key == StatusKey.BUSY:
                    st.status_key = previous_status_key
                self._set_audio_worker_state(
                    request.job_id,
                    AudioWorkerKind.VERIFIED_VMD_SAVE,
                    AudioWorkerStatus.FAILED,
                    "VMD保存失敗",
                )
                self._audio_worker_previous_status_key = None
                self.view.update_vmd_save_action_states()
            self._show_verified_vmd_save_error("delivery_worker_failed")
            return False
        self._record_view_debug_action(
            "vmd_save_writing",
            payload={
                "save_state_fingerprint": request.fingerprint,
                "job_id": request.job_id,
                "worker_kind": "verified_vmd_save",
            },
            status="writing",
        )
        return True

    def _build_verified_vmd_pre_commit_guard(
        self,
        request: VerifiedVmdSaveRequest,
        lease: SaveCommitLease,
    ):
        def guard(_request, cancel_token):
            reply = _VerifiedSaveGuardReply()
            if cancel_token.cancel_requested:
                return "cancelled"
            try:
                wx.CallAfter(
                    self._resolve_verified_vmd_commit_guard,
                    request,
                    lease,
                    cancel_token,
                    reply,
                )
            except Exception as error:
                reply.complete(error=error)
            deadline = time.monotonic() + DELIVERY_COMMIT_GUARD_UI_TIMEOUT_SEC
            while not reply.event.wait(0.05):
                if cancel_token.cancel_requested:
                    reply.complete(decision="cancelled")
                    break
                if time.monotonic() >= deadline:
                    reply.complete(error=TimeoutError("verified VMD save guard timed out"))
                    break
            if reply.error is not None:
                raise reply.error
            if reply.decision is None:
                raise RuntimeError("verified VMD save guard returned no decision")
            return reply.decision

        return guard

    def _resolve_verified_vmd_commit_guard(
        self,
        request: VerifiedVmdSaveRequest,
        lease: SaveCommitLease,
        cancel_token,
        reply: _VerifiedSaveGuardReply,
    ) -> None:
        view = self.view
        state = view.ui_state if view is not None else None
        worker_state = state.audio_worker_state if state is not None else None
        binding = self._active_verified_vmd_binding
        if (
            view is None
            or state is None
            or self._verified_vmd_terminal_received
            or binding != (
                request.job_id,
                AudioWorkerKind.VERIFIED_VMD_SAVE,
                request.ticket,
            )
            or self._active_save_commit_lease != lease
            or not state.is_current_audio_job(request.job_id)
            or worker_state is None
            or worker_state.audio_job_id != request.job_id
            or worker_state.kind != AudioWorkerKind.VERIFIED_VMD_SAVE
            or not worker_state.is_active
        ):
            decision = "invalid_job"
        elif self._verified_vmd_close_pending:
            decision = "closing"
        elif cancel_token.cancel_requested:
            decision = "cancelled"
        elif (
            not state.is_busy
            or state.analysis_pending_rebuild
            or view._analysis_info_in_progress
            or self._save_lifecycle_signature(
                view._capture_final_output_lifecycle_signature()
            )
            != lease.lifecycle_signature
            or request.context.identity.binding_digest != lease.binding_digest
            or request.fingerprint != lease.fingerprint
            or request.context.ticket != lease.ticket
            or request.context.lifecycle_epoch != lease.lifecycle_epoch
            or state.final_output_state.expected_transition_input_digest
            != request.context.input_identity.transition_input_digest
            or state.final_output_state.expected_application_binding_digest
            != request.context.input_identity.application_binding_digest
        ):
            decision = "stale"
        elif (
            request.diagnostics_snapshot.shared_final_output_identity
            != request.context.identity
            or request.diagnostics_snapshot.save_state_fingerprint != request.fingerprint
            or not request.diagnostics_snapshot.saveability.vmd_save_allowed
            or request.diagnostics_snapshot.saveability.blocking_codes
            or any(item.severity.value == "ERROR" for item in request.diagnostics_snapshot.items)
        ):
            decision = "stale"
        elif request.diagnostics_snapshot.saveability.warning_codes and (
            state.confirmed_shared_warning_fingerprint != request.fingerprint
        ):
            decision = "stale"
        else:
            decision = "authorized"
        reply.complete(decision=decision)

    def _show_verified_vmd_save_error(
        self,
        error_code: str,
        *,
        detail: BaseException | None = None,
    ) -> None:
        message = _DELIVERY_ERROR_MESSAGES.get(
            error_code,
            "VMD保存を完了できませんでした。現在の状態と保存先を確認してください。",
        )
        if detail is not None:
            message = f"{message}\n\n詳細: {detail}"
        self.update_status("VMD保存失敗")
        if self.view is not None:
            wx.MessageBox(message, "VMD保存エラー", wx.OK | wx.ICON_ERROR, self.view)

    def _on_verified_vmd_worker_error(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        ticket: int,
        error: Exception,
    ) -> None:
        result = VerifiedVmdSaveTerminalResult(
            job_id=audio_job_id,
            status="failed",
            error_code="vmd_write_failed",
            committed=False,
            final_path=None,
            temporary_path=None,
            commit_phase="worker_failed",
            evidence=None,
            cleanup_error=f"{type(error).__name__}: {error}",
        )
        self._on_verified_vmd_worker_terminal(audio_job_id, kind, ticket, result)

    def _on_verified_vmd_worker_terminal(
        self,
        audio_job_id: int,
        kind: AudioWorkerKind,
        ticket: int,
        result: VerifiedVmdSaveTerminalResult,
    ) -> None:
        if self._verified_vmd_terminal_received:
            return
        binding = self._active_verified_vmd_binding
        request = self._active_verified_vmd_request
        if (
            binding != (audio_job_id, kind, ticket)
            or kind != AudioWorkerKind.VERIFIED_VMD_SAVE
            or request is None
            or result.job_id != audio_job_id
        ):
            return
        self._verified_vmd_terminal_received = True
        self._verified_vmd_worker = None
        self._active_verified_vmd_binding = None
        self._active_verified_vmd_request = None
        self._active_save_commit_lease = None
        close_pending = self._verified_vmd_close_pending
        self._verified_vmd_close_pending = False
        operation = self._verified_vmd_save_operation
        if operation is not None and operation.job_id == audio_job_id:
            self._verified_vmd_save_operation = None
            if self.view is not None:
                self.view.close_vmd_save_progress(operation.operation_id)
        if self.view is None:
            return
        state = self.view.ui_state
        is_current = state.is_current_audio_job(audio_job_id)
        if is_current:
            state.set_busy(False)
            if result.committed and result.final_path is not None:
                state.last_vmd_output_dir = str(result.final_path.parent)
            previous_status_key = (
                operation.previous_status_key
                if operation is not None
                else self._audio_worker_previous_status_key
            )
            if state.status_key == StatusKey.BUSY and previous_status_key is not None:
                state.status_key = previous_status_key
            self._audio_worker_previous_status_key = None
            if result.status == "committed":
                status = AudioWorkerStatus.COMPLETED
                message = "VMD保存成功"
            elif result.status == "cancelled":
                status = AudioWorkerStatus.CANCELLED
                message = "VMD保存をキャンセルしました"
            else:
                status = AudioWorkerStatus.FAILED
                message = "VMD保存失敗"
            self._set_audio_worker_state(audio_job_id, kind, status, message)
            self.update_status(message)
            self.view.update_vmd_save_action_states()
            self.update_status(message)
            if result.status == "committed":
                self._record_view_debug_action(
                    "vmd_save_completed",
                    payload={
                        "path": str(result.final_path),
                        "save_state_fingerprint": request.fingerprint,
                        "wire_digest": request.context.identity.wire_digest,
                    },
                    status="succeeded",
                )
            if result.committed:
                self.request_settings_save()
            if result.status == "failed":
                self._record_view_debug_action(
                    "vmd_save_failed",
                    payload={
                        "error_code": result.error_code,
                        "committed": result.committed,
                        "file_basename": (
                            result.final_path.name
                            if result.final_path is not None
                            else None
                        ),
                    },
                    status="failed",
                )
                detail = result.cleanup_error
                if result.temporary_path is not None:
                    detail = f"{detail or ''}\n残留一時ファイル: {result.temporary_path}"
                self._show_verified_vmd_save_error(
                    result.error_code or "vmd_write_failed",
                    detail=RuntimeError(detail) if detail else None,
                )
            elif result.status == "cancelled":
                self._record_view_debug_action(
                    "vmd_save_cancelled",
                    payload={"committed": result.committed},
                    status="cancelled",
                )
        elif operation is not None:
            if self._audio_worker_previous_status_key == operation.previous_status_key:
                self._audio_worker_previous_status_key = None
        if close_pending:
            self.request_exit()

    @property
    def verified_vmd_save_may_be_active(self) -> bool:
        state = self.view.ui_state if self.view is not None else None
        return bool(
            getattr(self, "_verified_vmd_save_operation", None) is not None
            or getattr(self, "_verified_vmd_worker", None) is not None
            or getattr(self, "_active_verified_vmd_binding", None) is not None
            or getattr(self, "_verified_vmd_close_pending", False)
            or (
                state is not None
                and state.audio_worker_state is not None
                and state.audio_worker_state.kind == AudioWorkerKind.VERIFIED_VMD_SAVE
                and state.audio_worker_state.is_active
            )
        )

    def request_close_verified_vmd_save(self) -> bool:
        operation = self._verified_vmd_save_operation
        if operation is not None and not operation.worker_started:
            self._verified_vmd_close_pending = True
            operation.cancel_requested = True
            if self.view is not None:
                self._set_audio_worker_state(
                    operation.job_id,
                    AudioWorkerKind.VERIFIED_VMD_SAVE,
                    AudioWorkerStatus.CANCELLING,
                    "VMD保存準備をキャンセル中...",
                )
                self.update_status("VMD保存準備をキャンセル中...")
                self.view.update_vmd_save_action_states()
            return True
        if self._verified_vmd_worker is None:
            return False
        self._verified_vmd_close_pending = True
        accepted = self._verified_vmd_worker.cancel()
        if self.view is not None:
            state = self.view.ui_state
            self._set_audio_worker_state(
                state.current_audio_job_id,
                AudioWorkerKind.VERIFIED_VMD_SAVE,
                AudioWorkerStatus.CANCELLING if accepted else AudioWorkerStatus.FINALIZING,
                "VMD保存をキャンセル中..." if accepted else "VMD確定処理の終了を待っています。",
            )
            self.update_status(
                "VMD保存をキャンセル中..." if accepted else "VMD確定処理の終了を待っています。"
            )
            try:
                self.view.sync_ui_state()
            except Exception:
                pass
            self.update_status(
                "VMD保存をキャンセル中..." if accepted else "VMD確定処理の終了を待っています。"
            )
        return True

    def apply_generation_preset(self, preset_id: str) -> bool:
        if not self.view or self.view.ui_state.is_busy:
            return False
        preset = next(
            (
                item
                for item in self.preset_store.built_in_presets + self.preset_store.user_presets
                if item.id == preset_id
            ),
            None,
        )
        if preset is None:
            return False
        return self.view.apply_preset_generation(
            preset.generation_settings,
            preset.id,
            preset.display_name,
        )

    def lookup_generation_preset(self, preset_id: str) -> GenerationPreset | None:
        if type(preset_id) is not str or not preset_id:
            return None
        return next(
            (
                item
                for item in self.preset_store.built_in_presets + self.preset_store.user_presets
                if item.id == preset_id
            ),
            None,
        )

    def lookup_model_profile(self, profile_id: str) -> ModelProfile | None:
        if type(profile_id) is not str or not profile_id:
            return None
        return next(
            (item for item in self.profile_store.user_profiles if item.id == profile_id),
            None,
        )

    def _loaded_profile_and_preset_tuples(self):
        profile_result = self.profile_store.last_load_result
        if profile_result is None:
            profile_result = self.profile_store.load()
        preset_result = self.preset_store.last_load_result
        if preset_result is None:
            preset_result = self.preset_store.load()
        profiles = tuple(self.profile_store.user_profiles)
        presets = tuple(preset_result.built_in_presets) + tuple(self.preset_store.user_presets)
        return profiles, presets

    def resolve_model_profile_apply(self, profile_id: str) -> ModelProfileResolutionResult:
        profiles, presets = self._loaded_profile_and_preset_tuples()
        return resolve_model_profile_apply(
            requested_profile_id=profile_id,
            application_morph_upper_limit=self.view.ui_state.resolved_morph_upper_limit,
            profiles=profiles,
            presets=presets,
        )

    def resolve_active_profile_preset_apply(
        self,
        preset_id: str,
    ) -> ModelProfileResolutionResult:
        profiles, presets = self._loaded_profile_and_preset_tuples()
        return resolve_active_profile_preset_apply(
            requested_preset_id=preset_id,
            current_model_profile_state=self.view.ui_state.model_profile_state,
            application_morph_upper_limit=self.view.ui_state.resolved_morph_upper_limit,
            profiles=profiles,
            presets=presets,
        )

    def resolve_no_profile(self) -> ModelProfileResolutionResult:
        profiles, presets = self._loaded_profile_and_preset_tuples()
        return resolve_no_profile(
            current_generation_settings=self.view.ui_state.generation_state.generation_settings,
            current_morph_upper_limit=self.view.ui_state.resolved_morph_upper_limit,
            presets=presets,
        )

    def _profile_mutation_guard(self, operation, target_profile_id, candidate_profile):
        profile_result = self.profile_store.last_load_result
        if profile_result is None:
            profile_result = self.profile_store.load()
        profile_result = replace(
            profile_result,
            user_profiles=self.profile_store.user_profiles,
        )
        preset_result = self.preset_store.last_load_result
        if preset_result is None:
            preset_result = self.preset_store.load()
        preset_result = replace(
            preset_result,
            user_presets=self.preset_store.user_presets,
        )
        guard = validate_model_profile_mutation(
            operation=operation,
            target_profile_id=target_profile_id,
            candidate_profile=candidate_profile,
            current_model_profile_state=self.view.ui_state.model_profile_state,
            profile_load_result=profile_result,
            preset_load_result=preset_result,
        )
        return profile_result, guard

    def _preset_mutation_guard(self, operation, target_preset_id, candidate_preset):
        profile_result = self.profile_store.last_load_result
        if profile_result is None:
            profile_result = self.profile_store.load()
        profile_result = replace(
            profile_result,
            user_profiles=self.profile_store.user_profiles,
        )
        preset_result = self.preset_store.last_load_result
        if preset_result is None:
            preset_result = self.preset_store.load()
        preset_result = replace(
            preset_result,
            user_presets=self.preset_store.user_presets,
        )
        guard = validate_generation_preset_mutation(
            operation=operation,
            target_preset_id=target_preset_id,
            candidate_preset=candidate_preset,
            current_model_profile_state=self.view.ui_state.model_profile_state,
            profile_load_result=profile_result,
            preset_load_result=preset_result,
        )
        return preset_result, guard

    @staticmethod
    def _profile_guard_failure(operation, profile_result, guard) -> ProfileMutationResult:
        return ProfileMutationResult(
            operation=operation,
            succeeded=False,
            user_profiles=profile_result.user_profiles,
            mutation_available=profile_result.mutation_available,
            error_code=guard.error_code,
            error_message=guard.error_message,
        )

    @staticmethod
    def _preset_guard_failure(operation, preset_result, guard) -> PresetMutationResult:
        return PresetMutationResult(
            operation=operation,
            succeeded=False,
            user_presets=preset_result.user_presets,
            mutation_available=preset_result.mutation_available,
            error_code=guard.error_code,
            error_message=guard.error_message,
        )

    def _build_history_candidate_for_collections(
        self,
        profiles: tuple[ModelProfile, ...],
        presets: tuple[GenerationPreset, ...],
    ):
        if not self.view or self.view.ui_state.output_edit_history_state is None:
            return None
        upper = self.view.ui_state.resolved_morph_upper_limit

        def resolve_endpoint(output_state, profile_state):
            if profile_state is None:
                return output_state, None
            profile_id = profile_state.active_model_profile_id
            if profile_id is None:
                active_id = output_state.generation_state.active_preset_id
                active = next((item for item in presets if item.id == active_id), None)
                if (
                    active_id is None
                    or active is None
                    or active.generation_settings
                    != output_state.generation_state.generation_settings
                ):
                    generation_state = GenerationState(
                        generation_settings=output_state.generation_state.generation_settings,
                        active_preset_id=None,
                        resolved_morph_name_set_id="builtin:japanese-vowels",
                    )
                    return (
                        OutputEditState(
                            base_plan_identity=output_state.base_plan_identity,
                            adjustment_snapshot=output_state.adjustment_snapshot,
                            generation_state=generation_state,
                            morph_upper_limit=output_state.morph_upper_limit,
                        ),
                        profile_state,
                    )
                return output_state, profile_state

            profile = next((item for item in profiles if item.id == profile_id), None)
            baseline = next(
                (
                    item
                    for item in presets
                    if item.id == profile_state.active_profile_baseline_preset_id
                ),
                None,
            )
            if profile is None or baseline is None:
                return None
            profile_for_baseline = replace(profile, default_preset_id=baseline.id)
            resolution = resolve_model_profile_apply(
                requested_profile_id=profile_for_baseline.id,
                application_morph_upper_limit=upper,
                profiles=(profile_for_baseline,),
                presets=presets,
            )
            if resolution.resolution is None:
                return None
            resolved = resolution.resolution
            generation_state = output_state.generation_state
            if (
                generation_state.generation_settings != resolved.generation_settings
                or generation_state.active_preset_id is not None
                or generation_state.resolved_morph_name_set_id
                != resolved.morph_name_set.set_id
            ):
                return None
            return output_state, profile_state

        return normalize_profile_aware_output_edit_history_state(
            self.view.ui_state.output_edit_history_state,
            resolve_endpoint,
        )

    def _adopt_history_candidate(self, candidate) -> None:
        if candidate is None or not self.view:
            return
        state = self.view.ui_state
        if candidate == state.output_edit_history_state:
            return
        previous_generation_state = state.generation_state
        previous_profile_state = state.model_profile_state
        state.output_edit_history_state = candidate
        state.generation_state = candidate.current_state.generation_state
        if candidate.current_model_profile_state is not None:
            state.model_profile_state = candidate.current_model_profile_state
        state._sync_legacy_adjustment_history()
        if (
            state.generation_state != previous_generation_state
            or state.model_profile_state != previous_profile_state
        ):
            state.final_output_state.invalidate_context()
        state._observe_final_output_manual_snapshot()

    def _profile_invalid_input_result(self, operation: str) -> ProfileMutationResult:
        return ProfileMutationResult(
            operation=operation,
            succeeded=False,
            user_profiles=self.profile_store.user_profiles,
            mutation_available=self.profile_store.mutation_available,
            error_code="invalid_input",
            error_message="model profile input is invalid",
        )

    @staticmethod
    def _coerce_profile_overrides(value) -> ProfileGenerationOverrides:
        if isinstance(value, ProfileGenerationOverrides):
            return value
        return ProfileGenerationOverrides.from_dict(value)

    def create_model_profile_from_values(
        self,
        display_name: str,
        morph_name_set_id: str,
        morph_upper_limit: float | None,
        generation_overrides,
        default_preset_id: str,
    ) -> ProfileMutationResult:
        try:
            candidate = ModelProfile(
                id=str(uuid.uuid4()),
                display_name=display_name,
                morph_name_set_id=morph_name_set_id,
                morph_upper_limit=morph_upper_limit,
                generation_overrides=self._coerce_profile_overrides(
                    generation_overrides
                ),
                default_preset_id=default_preset_id,
            )
        except (TypeError, ValueError):
            return self._profile_invalid_input_result("create")
        return self.create_model_profile(candidate)

    def update_model_profile_from_values(
        self,
        profile_id: str,
        display_name: str,
        morph_name_set_id: str,
        morph_upper_limit: float | None,
        generation_overrides,
        default_preset_id: str,
    ) -> ProfileMutationResult:
        try:
            candidate = ModelProfile(
                id=profile_id,
                display_name=display_name,
                morph_name_set_id=morph_name_set_id,
                morph_upper_limit=morph_upper_limit,
                generation_overrides=self._coerce_profile_overrides(
                    generation_overrides
                ),
                default_preset_id=default_preset_id,
            )
        except (TypeError, ValueError):
            return self._profile_invalid_input_result("update")
        return self.update_model_profile(candidate)

    def create_model_profile(self, candidate_profile: ModelProfile) -> ProfileMutationResult:
        profile_result, guard = self._profile_mutation_guard(
            "create",
            None,
            candidate_profile,
        )
        if not guard.allowed:
            return self._profile_guard_failure("create", profile_result, guard)
        candidate_history = self._build_history_candidate_for_collections(
            tuple(self.profile_store.user_profiles) + (candidate_profile,),
            tuple(self.preset_store.built_in_presets) + tuple(self.preset_store.user_presets),
        )
        result = self.profile_store.create(
            candidate_profile.display_name,
            candidate_profile.morph_name_set_id,
            candidate_profile.morph_upper_limit,
            candidate_profile.generation_overrides,
            candidate_profile.default_preset_id,
            profile_id=candidate_profile.id,
        )
        if result.succeeded:
            self._adopt_history_candidate(candidate_history)
        return result

    def update_model_profile(self, candidate_profile: ModelProfile) -> ProfileMutationResult:
        profile_result, guard = self._profile_mutation_guard(
            "update",
            candidate_profile.id,
            candidate_profile,
        )
        if not guard.allowed:
            return self._profile_guard_failure("update", profile_result, guard)
        candidate_profiles = tuple(
            candidate_profile if item.id == candidate_profile.id else item
            for item in self.profile_store.user_profiles
        )
        candidate_history = self._build_history_candidate_for_collections(
            candidate_profiles,
            tuple(self.preset_store.built_in_presets) + tuple(self.preset_store.user_presets),
        )
        result = self.profile_store.update(
            candidate_profile.id,
            candidate_profile.display_name,
            candidate_profile.morph_name_set_id,
            candidate_profile.morph_upper_limit,
            candidate_profile.generation_overrides,
            candidate_profile.default_preset_id,
        )
        if result.succeeded:
            self._adopt_history_candidate(candidate_history)
        return result

    def delete_model_profile(self, profile_id: str) -> ProfileMutationResult:
        profile_result, guard = self._profile_mutation_guard(
            "delete",
            profile_id,
            None,
        )
        if not guard.allowed:
            return self._profile_guard_failure("delete", profile_result, guard)
        candidate_profiles = tuple(
            item for item in self.profile_store.user_profiles if item.id != profile_id
        )
        candidate_history = self._build_history_candidate_for_collections(
            candidate_profiles,
            tuple(self.preset_store.built_in_presets) + tuple(self.preset_store.user_presets),
        )
        result = self.profile_store.delete(profile_id)
        if result.succeeded:
            self._adopt_history_candidate(candidate_history)
        return result

    def create_generation_preset(
        self,
        display_name: str,
        generation_settings: GenerationSettings,
    ) -> PresetMutationResult:
        return self.preset_store.create(display_name, generation_settings)

    def update_generation_preset(
        self,
        preset_id: str,
        display_name: str,
        generation_settings: GenerationSettings,
    ) -> PresetMutationResult:
        candidate = GenerationPreset(
            id=preset_id,
            display_name=display_name,
            generation_settings=generation_settings,
            source="user",
        )
        preset_result, guard = self._preset_mutation_guard(
            "update",
            preset_id,
            candidate,
        )
        if not guard.allowed:
            return self._preset_guard_failure("update", preset_result, guard)
        candidate_presets = tuple(
            candidate if item.id == preset_id else item
            for item in self.preset_store.user_presets
        )
        candidate_history = self._build_history_candidate_for_collections(
            tuple(self.profile_store.user_profiles),
            tuple(self.preset_store.built_in_presets) + candidate_presets,
        )
        result = self.preset_store.update(preset_id, display_name, generation_settings)
        if result.succeeded:
            self._adopt_history_candidate(candidate_history)
        return result

    def delete_generation_preset(self, preset_id: str) -> PresetMutationResult:
        preset_result, guard = self._preset_mutation_guard(
            "delete",
            preset_id,
            None,
        )
        if not guard.allowed:
            return self._preset_guard_failure("delete", preset_result, guard)
        candidate_history = self._build_history_candidate_for_collections(
            tuple(self.profile_store.user_profiles),
            tuple(self.preset_store.built_in_presets)
            + tuple(item for item in self.preset_store.user_presets if item.id != preset_id),
        )
        result = self.preset_store.delete(preset_id)
        if result.succeeded:
            self._adopt_history_candidate(candidate_history)
        return result

    def request_save_diagnostic_report(self):
        if not self.view or self._is_shutting_down:
            return
        state = self.view.ui_state
        operation_handle = self.begin_debug_operation(
            "diagnostic_report_save",
            payload={"analysis_result_valid": state.analysis_result_valid},
            entry="menu",
        )
        if state.is_busy or state.output_edit_draft_dirty:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code=(
                    "unapplied_output_edits"
                    if state.output_edit_draft_dirty
                    else "busy"
                ),
            )
            if state.output_edit_draft_dirty:
                self.update_status("変更未適用のため、診断レポートを保存できません")
            return
        context = state.final_output_state.current_context
        snapshot = self.view._shared_final_output_diagnostics
        if (
            context is None
            or snapshot is None
            or snapshot.shared_final_output_identity != context.identity
            or context.lifecycle_signature
            != self.view._capture_final_output_lifecycle_signature()
        ):
            self.view.request_shared_final_output_context()
            self.update_status("共有最終出力の診断を準備中です")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="diagnostic_context_unavailable",
            )
            return
        source_audio_path = resolve_source_audio_path_from_ui_state(state)
        default_name = build_diagnostic_report_default_filename(source_audio_path)
        if source_audio_path is None or default_name is None:
            self.update_status("診断レポート保存不可")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="diagnostic_source_unavailable",
            )
            return

        output_path = self.view.show_diagnostic_report_save_dialog_and_get_path(
            str(source_audio_path.parent),
            default_name,
        )
        if not output_path:
            self.update_status("診断レポート保存をキャンセルしました")
            self.finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="save_dialog_cancelled",
            )
            return

        current_context = state.final_output_state.current_context
        current_snapshot = self.view._shared_final_output_diagnostics
        if (
            state.is_busy
            or current_context is None
            or current_snapshot is None
            or current_context.identity != context.identity
            or current_snapshot.shared_final_output_identity != context.identity
            or current_snapshot.save_state_fingerprint
            != snapshot.save_state_fingerprint
            or current_context.lifecycle_signature
            != self.view._capture_final_output_lifecycle_signature()
        ):
            self.update_status("作業状態が変わったため、診断レポートを保存できません")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="diagnostic_context_changed",
            )
            return

        generated_at = datetime.now().astimezone()
        operation_handle = self.mark_debug_operation_started(
            operation_handle,
            payload={"file_basename": Path(output_path).name},
        )
        try:
            write_diagnostic_report(
                snapshot,
                output_path,
                generated_at=generated_at,
            )
        except DiagnosticReportError as error:
            wx.MessageBox(
                "診断レポートの保存に失敗しました。\n"
                "保存先の権限、空き容量、ファイルの使用状態を確認し、"
                "別の保存先でもう一度お試しください。\n\n"
                f"詳細: {error}",
                "診断レポート保存エラー",
                wx.OK | wx.ICON_ERROR,
            )
            self.update_status("診断レポート保存失敗")
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="diagnostic_report_write_failed",
            )
            return

        self.update_status("診断レポート保存成功")
        self.finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="diagnostic_report_saved",
            payload={"file_basename": Path(output_path).name},
        )

    def request_export_mmd_wav(self):
        if not self.view:
            return
        st = self.view.ui_state
        operation_handle = self.begin_debug_operation(
            "mmd_wav_export",
            payload={
                "has_audio_input": bool(st.selected_audio_input),
                "available": bool(st.selected_analysis_wav),
            },
            entry="menu_or_button",
        )
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle, "rejected", reason_code="busy"
            )
            return
        if not st.selected_analysis_wav:
            self.update_status("MMD用WAV出力不可")
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="analysis_wav_unavailable",
            )
            return
        if not st.selected_audio_input or not st.selected_audio_probe:
            self.update_status("MMD用WAV出力不可")
            wx.MessageBox(
                "MMD用WAVを出力するための音声情報が不足しています。\n音声ファイルを読み込み直してください。",
                "MMD用WAV出力エラー",
                wx.OK | wx.ICON_ERROR,
            )
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="audio_probe_unavailable",
            )
            return

        source_path = Path(st.selected_audio_input.source_path)
        default_dir = st.last_mmd_wav_export_dir or st.last_vmd_output_dir or str(source_path.parent)
        default_name = f"{source_path.stem}_mmd.wav"
        output_path = self.view.show_mmd_wav_save_dialog_and_get_path(default_dir, default_name)
        if not output_path:
            self.update_status("MMD用WAV出力をキャンセルしました")
            self.finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="save_dialog_cancelled",
            )
            return

        try:
            ffmpeg_tools = locate_ffmpeg_tools()
            if not ffmpeg_tools.ffmpeg.path:
                raise Exception(
                    "ffmpeg.exe が見つかりません。\n"
                    f"{format_tool_status('ffmpeg.exe', ffmpeg_tools.ffmpeg)}\n"
                    "FFmpeg/bin フォルダ内に配置するか、PATH から実行できる状態にしてください。"
                )
        except Exception as e:
            wx.MessageBox(f"MMD用WAVの出力に失敗しました。\n{e}", "MMD用WAV出力エラー", wx.OK | wx.ICON_ERROR)
            self.update_status("MMD用WAV出力失敗")
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="ffmpeg_unavailable",
            )
            return

        if not self._confirm_long_audio_if_needed(st.selected_audio_probe.duration_sec):
            self.update_status("MMD用WAV出力をキャンセルしました")
            self.finish_debug_operation(
                operation_handle,
                "cancelled",
                reason_code="long_audio_confirmation_declined",
            )
            return

        audio_job_id = st.next_audio_job_id()
        probe_result = st.selected_audio_probe

        def task(cancel_token):
            runner = lambda **kwargs: run_ffmpeg_mmd_wav_cancellable(
                cancel_token=cancel_token,
                **kwargs,
            )
            return export_mmd_wav(
                probe_result=probe_result,
                ffmpeg_path=ffmpeg_tools.ffmpeg.path,
                output_path=output_path,
                runner=runner,
            )

        self._start_audio_worker(
            audio_job_id,
            AudioWorkerKind.MMD_WAV,
            task,
            "MMD用WAVを出力中...",
            operation_handle=operation_handle,
        )

    def request_run_analysis(self):
        self.update_status("解析実行要求 (Stub)")

    def _on_playback_update(self, pos_sec: float):
        if not self.view:
            return
        st = self.view.ui_state
        if not st.is_playing:
            return
        st.playback_position_sec = pos_sec
        self.view.set_playback_position_sec(pos_sec)
        self.view.sync_playback_context()
        viewport_before = (
            self.viewport_controller.viewport_start_sec,
            self.viewport_controller.viewport_end_sec,
        )
        # [MS15-B4] Auto-follow check
        self.viewport_controller.update_playback_position(pos_sec)
        viewport_after = (
            self.viewport_controller.viewport_start_sec,
            self.viewport_controller.viewport_end_sec,
        )
        if viewport_after != viewport_before:
            self.record_debug_operation_event(
                "viewport_auto_follow",
                "completed",
                source="system",
                reason_code="viewport_followed",
                payload={
                    "operation_kind": "playback_auto_follow",
                    "before": viewport_before[0],
                    "after": viewport_after[0],
                    "zoom_factor": self.viewport_controller.zoom_factor,
                    "viewport_start_sec": viewport_after[0],
                    "viewport_end_sec": viewport_after[1],
                    "playback_position_sec": pos_sec,
                },
            )

    def _on_playback_finished(self):
        if self.view:
            self.record_debug_operation_event(
                "playback",
                "completed",
                source="system",
                reason_code="playback_finished",
            )
        self.request_playback_stop(
            _source="system",
            _reason_code="playback_finished",
        )

    @staticmethod
    def _playback_state_name(state) -> str:
        if state.is_playing:
            return "playing"
        if state.is_paused:
            return "paused"
        return "stopped"

    @staticmethod
    def _selected_playback_path(state) -> str | None:
        if state.selected_analysis_wav:
            return state.selected_analysis_wav.analysis_wav_path
        return state.selected_wav_path

    def request_playback_play(self, *, _source: str = "user"):
        if not self.view:
            return
        st = self.view.ui_state
        before = self._playback_state_name(st)
        operation_handle = self.begin_debug_operation(
            "playback_play",
            source=_source,
            payload={
                "has_audio_input": bool(st.selected_wav_path),
                "before": before,
                "playback_position_sec": st.playback_position_sec,
            },
            entry="button",
        )
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="busy",
                payload={"before": before, "after": before},
            )
            return
        if st.is_playing:
            self.finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="already_playing",
                payload={"before": before, "after": before},
            )
            return

        was_paused = st.is_paused
        play_path = st.loaded_playback_path if was_paused else self._selected_playback_path(st)
        if not play_path:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="audio_path_unavailable",
                payload={"before": before, "after": before},
            )
            return

        start_position = st.playback_position_sec if was_paused else 0.0
        success = (
            self.playback_controller.resume(start_position)
            if was_paused
            else self.playback_controller.play(play_path)
        )
        if not success:
            self.playback_controller.stop()
            st.is_playing = False
            st.is_paused = False
            st.playback_position_sec = 0.0
            st.loaded_playback_path = None
            self.view.set_playback_position_sec(0.0)
            self.update_status("音声の再生に失敗しました")
            wx.MessageBox(
                "音声の再生に失敗しました。\n(再生バックエンドがファイルを開けませんでした)",
                "再生エラー",
                wx.OK | wx.ICON_WARNING,
            )
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="playback_start_failed",
                payload={
                    "before": before,
                    "after": "stopped",
                    "playback_position_sec": 0.0,
                },
            )
        else:
            st.is_playing = True
            st.is_paused = False
            st.playback_position_sec = start_position
            st.loaded_playback_path = play_path
            self.view.set_playback_position_sec(start_position)
            self.update_status("再生中...")
            self.finish_debug_operation(
                operation_handle,
                "completed",
                reason_code="playback_resumed" if was_paused else "playback_started",
                payload={
                    "file_basename": Path(play_path).name,
                    "before": before,
                    "after": "playing",
                    "playback_position_sec": start_position,
                },
            )
        self.view.sync_playback_controls()
        self.view.sync_playback_context()

    def request_playback_seek(self, position_sec: float) -> bool:
        if not self.view:
            return False
        st = self.view.ui_state
        before = self._playback_state_name(st)
        operation_handle = self.begin_debug_operation(
            "playback_seek",
            payload={
                "before": before,
                "playback_position_sec": position_sec,
                "operation_kind": "waveform_click",
            },
            entry="waveform",
        )
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="busy",
                payload={"before": before, "after": before},
            )
            return False
        play_path = self._selected_playback_path(st)
        if not play_path:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="audio_path_unavailable",
                payload={"before": before, "after": before},
            )
            return False

        position = max(0.0, min(self.viewport_controller.duration_sec, float(position_sec)))
        if not self.playback_controller.seek(play_path, position):
            self.playback_controller.stop()
            st.is_playing = False
            st.is_paused = False
            st.playback_position_sec = 0.0
            st.loaded_playback_path = None
            self.view.clear_playback_cursor()
            self.view.set_playback_position_sec(0.0)
            self.update_status("音声の位置を設定できませんでした")
            self.view.sync_playback_controls()
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="playback_seek_failed",
                payload={"before": before, "after": "stopped"},
            )
            return False

        st.is_playing = False
        st.is_paused = True
        st.playback_position_sec = position
        st.loaded_playback_path = play_path
        self.view.set_playback_position_sec(position)
        self.update_status("一時停止中")
        self.view.sync_playback_controls()
        self.finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="playback_seek_completed",
            payload={
                "before": before,
                "after": "paused",
                "playback_position_sec": position,
                "operation_kind": "waveform_click",
            },
        )
        return True

    def request_playback_pause(self, *, _source: str = "user"):
        if not self.view:
            return
        st = self.view.ui_state
        before = self._playback_state_name(st)
        operation_handle = self.begin_debug_operation(
            "playback_pause",
            source=_source,
            payload={
                "before": before,
                "playback_position_sec": st.playback_position_sec,
            },
            entry="button" if _source == "user" else None,
        )
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="busy",
                payload={"before": before, "after": before},
            )
            return
        if not st.is_playing:
            self.finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="playback_not_active",
                payload={"before": before, "after": before},
            )
            return
        if not self.playback_controller.pause():
            self.request_playback_stop(
                _source="system",
                _reason_code="playback_pause_failed",
            )
            self.update_status("一時停止に失敗しました")
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="playback_pause_failed",
                payload={"before": before, "after": "stopped"},
            )
            return

        position = self.playback_controller.get_position_sec()
        if position is not None:
            st.playback_position_sec = position
        st.is_playing = False
        st.is_paused = True
        self.view.set_playback_position_sec(st.playback_position_sec)
        self.update_status("一時停止中")
        self.view.sync_playback_controls()
        self.view.sync_playback_context()
        self.finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="playback_paused",
            payload={
                "before": before,
                "after": "paused",
                "playback_position_sec": st.playback_position_sec,
            },
        )

    def request_playback_stop(
        self,
        *,
        _source: str = "user",
        _reason_code: str | None = None,
    ):
        if not self.view:
            return
        st = self.view.ui_state
        before = self._playback_state_name(st)
        was_active = st.playback_active
        operation_handle = self.begin_debug_operation(
            "playback_stop",
            source=_source,
            payload={
                "is_playing": st.is_playing,
                "before": before,
                "playback_position_sec": st.playback_position_sec,
            },
            entry="button" if _source == "user" else None,
        )
        self.playback_controller.stop()
        st.is_playing = False
        st.is_paused = False
        st.playback_position_sec = 0.0
        st.loaded_playback_path = None
        self.view.set_playback_position_sec(0.0)
        self.viewport_controller.ensure_position_visible(0.0)
        worker_state = st.audio_worker_state
        if (
            st.is_busy
            and worker_state is not None
            and worker_state.kind == AudioWorkerKind.MMD_WAV
        ):
            self._update_audio_worker_action_states()
        elif _source == "user" or _reason_code == "playback_pause_failed":
            self.view.sync_playback_controls()
            self.view.sync_playback_context()
            self.view.update_status_display()
        else:
            self.view.sync_ui_state()
        self.finish_debug_operation(
            operation_handle,
            "completed" if was_active else "noop",
            reason_code=(
                _reason_code
                or ("playback_stopped" if was_active else "playback_not_active")
            ),
            payload={
                "changed": was_active,
                "before": before,
                "after": "stopped",
                "playback_position_sec": 0.0,
            },
        )

    def request_playback_scrub_start(self, position_sec: float) -> bool:
        if not self.view:
            return False
        st = self.view.ui_state
        before = self._playback_state_name(st)
        operation_handle = self.begin_debug_operation(
            "playback_scrub",
            payload={
                "before": before,
                "playback_position_sec": position_sec,
                "operation_kind": "waveform_drag",
            },
            entry="waveform",
        )
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="busy",
                payload={"before": before, "after": before},
            )
            return False
        play_path = self._selected_playback_path(st)
        if not play_path:
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="audio_path_unavailable",
                payload={"before": before, "after": before},
            )
            return False

        position = max(0.0, min(self.viewport_controller.duration_sec, float(position_sec)))
        if not self.playback_controller.begin_scrub(play_path, position):
            st.is_playing = False
            st.is_paused = False
            st.playback_position_sec = 0.0
            st.loaded_playback_path = None
            self.view.clear_playback_cursor()
            self.view.set_playback_position_sec(0.0)
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="playback_scrub_start_failed",
                payload={"before": before, "after": "stopped"},
            )
            self.view.sync_playback_controls()
            return False

        self._playback_scrub_operation_handle = operation_handle
        st.is_playing = True
        st.is_paused = False
        st.playback_position_sec = position
        st.loaded_playback_path = play_path
        self.view.set_playback_position_sec(position)
        self.viewport_controller.update_playback_position(
            position,
            allow_backward=True,
        )
        self.update_status("再生中...")
        self.view.sync_playback_controls()
        return True

    def request_playback_scrub_update(self, position_sec: float):
        if not self.view or not self.view.ui_state.is_playing:
            return
        st = self.view.ui_state
        position = max(0.0, min(self.viewport_controller.duration_sec, float(position_sec)))
        self.playback_controller.scrub_to(position)
        st.playback_position_sec = position
        self.view.set_playback_position_sec(position)
        self.viewport_controller.update_playback_position(
            position,
            allow_backward=True,
        )

    def request_playback_scrub_end(self, position_sec: float):
        if not self.view:
            return
        st = self.view.ui_state
        operation_handle = self._playback_scrub_operation_handle
        self._playback_scrub_operation_handle = None
        position = max(0.0, min(self.viewport_controller.duration_sec, float(position_sec)))
        succeeded = self.playback_controller.finish_scrub(position)
        if succeeded:
            st.is_playing = False
            st.is_paused = True
            st.playback_position_sec = position
            self.view.set_playback_position_sec(position)
            self.update_status("一時停止中")
            self.finish_debug_operation(
                operation_handle,
                "completed",
                reason_code="playback_scrub_completed",
                payload={
                    "before": "playing",
                    "after": "paused",
                    "playback_position_sec": position,
                    "operation_kind": "waveform_drag",
                },
            )
        else:
            self.playback_controller.stop()
            st.is_playing = False
            st.is_paused = False
            st.playback_position_sec = 0.0
            st.loaded_playback_path = None
            self.view.clear_playback_cursor()
            self.view.set_playback_position_sec(0.0)
            self.update_status("波形スクラブ中の再生に失敗しました")
            self.finish_debug_operation(
                operation_handle,
                "failed",
                reason_code="playback_scrub_failed",
                payload={
                    "before": "playing",
                    "after": "stopped",
                    "playback_position_sec": 0.0,
                    "operation_kind": "waveform_drag",
                },
            )
        self.view.sync_playback_controls()

    def request_reset_workspace(
        self,
        operation_handle: OperationHandle | None = None,
    ) -> bool:
        """Reset the active workspace without clearing settings or file history."""
        if not self.view:
            return False

        st = self.view.ui_state
        operation_handle = operation_handle or self.begin_debug_operation(
            "workspace_reset",
            payload={
                "has_text_input": bool(st.selected_text_path),
                "has_audio_input": bool(st.selected_audio_input or st.selected_wav_path),
            },
            entry="menu",
        )
        if st.is_busy:
            self.finish_debug_operation(
                operation_handle, "rejected", reason_code="busy"
            )
            return False

        st.invalidate_audio_job()
        self.view.invalidate_analysis_job()
        self.request_playback_stop(
            _source="system",
            _reason_code="workspace_reset",
        )
        self.viewport_controller.set_duration(0.0)

        st.reset_workspace()
        self._audio_worker_previous_status_key = None
        self.view.reset_workspace_display()
        self.view.sync_ui_state()
        self.finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="workspace_reset",
            payload={"changed": True},
        )
        return True

    # --- [MS15-B4] Zoom Control ---
    def notify_duration_changed(self, duration_sec: float):
        self.viewport_controller.set_duration(duration_sec)

    def _on_viewport_changed(self, start_sec: float, end_sec: float):
        if self.view:
            self.view.placeholder_container.set_viewport_sec(start_sec, end_sec)

    def request_zoom_in(self):
        if not self.view: return
        st = self.view.ui_state
        before = self.viewport_controller.zoom_factor
        operation_handle = self.begin_debug_operation(
            "viewport_zoom_in",
            payload={"before": before},
            entry="button",
        )
        self.viewport_controller.zoom_in(
            playback_position_sec=st.playback_position_sec
        )
        after = self.viewport_controller.zoom_factor
        if after != before:
            self.view.sync_zoom_controls()
        self.finish_debug_operation(
            operation_handle,
            "completed" if after != before else "noop",
            reason_code="zoom_changed" if after != before else "zoom_unchanged",
            payload={"before": before, "after": after, "changed": after != before},
        )

    def request_zoom_out(self):
        if not self.view: return
        st = self.view.ui_state
        before = self.viewport_controller.zoom_factor
        operation_handle = self.begin_debug_operation(
            "viewport_zoom_out",
            payload={"before": before},
            entry="button",
        )
        self.viewport_controller.zoom_out(
            playback_position_sec=st.playback_position_sec
        )
        after = self.viewport_controller.zoom_factor
        if after != before:
            self.view.sync_zoom_controls()
        self.finish_debug_operation(
            operation_handle,
            "completed" if after != before else "noop",
            reason_code="zoom_changed" if after != before else "zoom_unchanged",
            payload={"before": before, "after": after, "changed": after != before},
        )

    def request_zoom_reset(self):
        before = self.viewport_controller.zoom_factor
        operation_handle = self.begin_debug_operation(
            "viewport_zoom_reset",
            payload={"before": before},
            entry="button",
        )
        self.viewport_controller.reset_zoom()
        after = self.viewport_controller.zoom_factor
        if after != before and self.view:
            self.view.sync_zoom_controls()
        self.finish_debug_operation(
            operation_handle,
            "completed" if after != before else "noop",
            reason_code="zoom_reset" if after != before else "zoom_unchanged",
            payload={"before": before, "after": after, "changed": after != before},
        )

    def request_pan(self, delta_sec: float):
        if not self.view: return
        before = self.viewport_controller.viewport_start_sec
        operation_handle = self.begin_debug_operation(
            "viewport_pan",
            payload={"before": before, "delta_sec": delta_sec},
            entry="waveform_drag",
        )
        self.viewport_controller.pan(delta_sec)
        after = self.viewport_controller.viewport_start_sec
        self.finish_debug_operation(
            operation_handle,
            "completed" if after != before else "noop",
            reason_code="viewport_panned" if after != before else "viewport_unchanged",
            payload={"before": before, "after": after, "changed": after != before},
        )

    def get_zoom_action_state(self) -> dict[str, bool]:
        """[MS15-B5] Helper for Zoom UI action states"""
        state = {
            "zoom_in": False,
            "zoom_out": False,
            "zoom_reset": False
        }
        
        if not self.view: return state
        ui_st = self.view.ui_state
        
        can_zoom_common = (
            ui_st.selected_wav_analysis is not None and 
            ui_st.selected_wav_analysis.duration_sec > 0 and
            self.viewport_controller is not None and
            self.viewport_controller.duration_sec > 0 and
            not ui_st.is_busy
        )
        
        if can_zoom_common:
            zf = self.viewport_controller.zoom_factor
            state["zoom_in"] = (zf < 8)
            state["zoom_out"] = (zf > 1)
            state["zoom_reset"] = True
            
        return state

    def request_open_settings_dialog(self):
        self.update_status("設定画面表示要求 (Stub)")
        
    def request_open_help(self):
        if not self.view or getattr(self, "_is_shutting_down", False):
            return
        self.view.show_help_dialog()

    def request_show_about(self):
        if not self.view or getattr(self, "_is_shutting_down", False):
            return
        self.view.show_about_dialog()

    def request_change_theme(self, mode: str):
        if not self.view: return
        previous = self.view.ui_state.theme_mode
        operation_handle = self.begin_debug_operation(
            "theme_change",
            payload={"before": previous, "after": mode},
            entry="menu",
        )
        if mode not in {ThemeMode.SYSTEM, ThemeMode.LIGHT, ThemeMode.DARK}:
            self.finish_debug_operation(
                operation_handle, "rejected", reason_code="theme_mode_invalid"
            )
            return
        if mode == previous:
            self.finish_debug_operation(
                operation_handle,
                "noop",
                reason_code="theme_unchanged",
                payload={"theme_mode": mode},
            )
            return
        self.view.ui_state.theme_mode = mode
        self.view.apply_theme(mode)
        self.request_settings_save()
        self.finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="theme_changed",
            payload={"before": previous, "after": mode, "theme_mode": mode},
        )
        
    def request_exit(self, operation_handle: OperationHandle | None = None):
        if operation_handle is not None:
            self._pending_exit_operation_handle = operation_handle
        operation_handle = operation_handle or getattr(
            self, "_pending_exit_operation_handle", None
        )
        if self.verified_vmd_save_may_be_active:
            if not self._verified_vmd_close_pending:
                self.request_close_verified_vmd_save()
            return False
        if self.delivery_may_be_active:
            if self.is_delivery_active():
                self.request_close_delivery()
                return False
            if not self._reconcile_delivery_close_state():
                self.finish_debug_operation(
                    operation_handle,
                    "rejected",
                    reason_code="delivery_close_not_reconciled",
                )
                self._pending_exit_operation_handle = None
                return False
        view = self.view
        if (
            view is not None
            and view.ui_state.audio_worker_active
            and getattr(self, "_audio_worker", None) is None
        ):
            self.update_status(
                "音声処理の状態を確認できないため、終了を実行できません。"
            )
            self.finish_debug_operation(
                operation_handle,
                "rejected",
                reason_code="audio_worker_state_unavailable",
            )
            self._pending_exit_operation_handle = None
            return False
        if view is not None:
            prepare_exit = getattr(view, "prepare_for_confirmed_exit", None)
            if callable(prepare_exit):
                prepare_exit()
        self.finish_debug_operation(
            operation_handle,
            "completed",
            reason_code="exit_confirmed",
        )
        self._pending_exit_operation_handle = None
        if self._coalesced_save_timer.IsRunning():
            self._coalesced_save_timer.Stop()
        if (
            self._startup_diagnostics is not None
            and self._whisper_availability_worker is not None
            and view is not None
        ):
            scan_state = view.ui_state.whisper_model_selection
            if (
                scan_state.availability_scan_status
                == WHISPER_AVAILABILITY_SCAN_PENDING
                and type(scan_state.availability_scan_job_id) is int
                and type(scan_state.availability_scan_generation) is int
            ):
                self._startup_diagnostics.record_scan_pending_at_shutdown(
                    scan_state.availability_scan_job_id,
                    scan_state.availability_scan_generation,
                )
        self._stop_whisper_scan_slow_check()
        self._is_shutting_down = True
        if self.whisper_model_runtime is not None:
            self.whisper_model_runtime.begin_shutdown()
        self._whisper_scan_job_id += 1
        self._whisper_scan_generation += 1
        self._whisper_availability_worker = None
        self._whisper_management_job_id += 1
        if self._whisper_management_worker is not None:
            self._whisper_management_worker.cancel()
        self._whisper_management_worker = None
        self._whisper_apply_job_id += 1
        if self._whisper_apply_worker is not None:
            self._whisper_apply_worker.cancel()
        self._whisper_apply_worker = None
        if view:
            view.ui_state.invalidate_audio_job()
            if view.ui_state.audio_worker_active and self._audio_worker:
                self._audio_worker.cancel()
        if self._pending_save:
            if view:
                view.ui_state.set_busy(False)
            self.flush_pending_save(is_closing=True)

        self.shutdown_debug_operation_log(timeout=1.0)
        if view:
            self.view = None
            view.Destroy()
        return True

    def on_settings_changed(self):
        self.request_settings_save()

    def request_startup_identity_correction_save(self):
        if self._pending_settings_save_kind == "none":
            self._pending_settings_save_kind = "identity_only"
        self._pending_save = True
        self._coalesced_save_timer.Start(500, wx.TIMER_ONE_SHOT)

    def request_settings_save(self):
        self._pending_settings_save_kind = "full"
        self._pending_save = True
        self._coalesced_save_timer.Start(500, wx.TIMER_ONE_SHOT)

    def reapply_settings_to_view(self):
        pass
