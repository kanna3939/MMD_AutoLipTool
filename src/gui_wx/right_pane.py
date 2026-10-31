import math
from dataclasses import dataclass

import wx

from gui_wx.output_diagnostics_adapter import format_output_diagnostics_info
from gui_wx.playback_context import (
    PlaybackInfoContext,
    format_playback_info_context,
)
from gui_wx.theme import ThemeButton, ThemeManager
from gui_wx.selected_event_editor import (
    SelectedEventEditBoundaryRequest,
    SelectedEventEditRequest,
    SelectedEventEditorState,
)
from src.core import OutputDiagnosticsSnapshot
from src.core.generation_presets import GenerationSettings
from src.core.model_profiles import ProfileGenerationOverrides
from src.core.morph_name_sets import (
    JAPANESE_MORPH_NAME_SET_ID,
    JAPANESE_OUTPUT_NAMES,
)


def _require_revision(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative int")
    return value


def _format_size(size_bytes: int) -> str:
    return f"{size_bytes / (1024 ** 3):.2f} GiB ({size_bytes:,} bytes)"


def _format_whisper_artifact_status(status: str) -> str:
    return {
        "unknown": "未確認",
        "missing": "未配置（Download & Verifyが必要）",
        "partial": "未完了（Download & Verifyが必要）",
        "verified": "確認済み",
        "invalid_size": "サイズ不一致",
        "invalid_sha256": "SHA256不一致",
        "read_failed": "読み取り失敗",
        "invalid_path": "パス不正",
    }.get(status, "確認失敗")


def _format_closure_restriction_reason(reason: str) -> str:
    return {
        "silence_core_precedence": "無音区間の閉口要件を適用",
        "manual_or_unknown_key_preserved": "手動または由来不明の値を保護",
        "preserved_protected_shape_value": "保護対象の既存形状値を維持",
    }.get(reason, "閉口要件に基づく値の制限")


@dataclass(frozen=True)
class CleanupEventSelectionRequest:
    binding_digest: str
    ticket: int
    lifecycle_epoch: int
    base_event_index: int

    def __post_init__(self) -> None:
        if type(self.binding_digest) is not str or len(self.binding_digest) != 64:
            raise ValueError("binding_digest must be a SHA-256 digest")
        for name in ("ticket", "lifecycle_epoch", "base_event_index"):
            _require_revision(getattr(self, name), name)


@dataclass(frozen=True)
class PresetPanelItem:
    id: str
    display_name: str
    source: str
    generation_settings: GenerationSettings

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("preset id must be a non-empty string")
        if self.source not in {"built_in", "user"}:
            raise ValueError("preset source must be built_in or user")
        if not isinstance(self.generation_settings, GenerationSettings):
            raise ValueError("generation_settings must be GenerationSettings")


@dataclass(frozen=True)
class PresetPanelState:
    items: tuple[PresetPanelItem, ...] = ()
    selected_preset_id: str | None = None
    active_preset_id: str | None = None
    active_preset_display_name: str | None = None
    active_generation_settings: GenerationSettings = GenerationSettings()
    mutation_available: bool = True
    load_error_code: str | None = None
    load_error_message: str | None = None
    busy: bool = False
    panel_revision: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        if not isinstance(self.active_generation_settings, GenerationSettings):
            raise ValueError("active_generation_settings must be GenerationSettings")
        _require_revision(self.panel_revision, "panel_revision")
        if self.active_preset_id is None and self.active_preset_display_name is not None:
            raise ValueError("Custom state must not have an active display name")


@dataclass(frozen=True)
class PresetSelectRequest:
    selected_preset_id: str | None
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if self.selected_preset_id is not None and (
            not isinstance(self.selected_preset_id, str) or not self.selected_preset_id
        ):
            raise ValueError("selected_preset_id must be None or a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class PresetApplyRequest:
    preset_id: str
    expected_panel_revision: int
    expected_editor_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.preset_id, str) or not self.preset_id:
            raise ValueError("preset_id must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        _require_revision(self.expected_editor_revision, "expected_editor_revision")


@dataclass(frozen=True)
class PresetCreateRequest:
    display_name: str
    generation_settings: GenerationSettings
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.display_name, str):
            raise ValueError("display_name must be a string")
        if not isinstance(self.generation_settings, GenerationSettings):
            raise ValueError("generation_settings must be GenerationSettings")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class PresetUpdateRequest:
    preset_id: str
    display_name: str
    generation_settings: GenerationSettings
    expected_panel_revision: int
    expected_editor_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.preset_id, str) or not self.preset_id:
            raise ValueError("preset_id must be a non-empty string")
        if not isinstance(self.display_name, str):
            raise ValueError("display_name must be a string")
        if not isinstance(self.generation_settings, GenerationSettings):
            raise ValueError("generation_settings must be GenerationSettings")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        _require_revision(self.expected_editor_revision, "expected_editor_revision")


@dataclass(frozen=True)
class PresetDeleteRequest:
    preset_id: str
    expected_panel_revision: int
    expected_editor_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.preset_id, str) or not self.preset_id:
            raise ValueError("preset_id must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        _require_revision(self.expected_editor_revision, "expected_editor_revision")


@dataclass(frozen=True)
class ModelProfilePresetOption:
    id: str
    display_name: str
    source: str
    generation_settings: GenerationSettings

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("profile preset id must be a non-empty string")
        if self.source not in {"built_in", "user"}:
            raise ValueError("profile preset source must be built_in or user")
        if not isinstance(self.generation_settings, GenerationSettings):
            raise ValueError("generation_settings must be GenerationSettings")


@dataclass(frozen=True)
class ModelProfilePanelItem:
    id: str
    display_name: str
    morph_name_set_id: str
    morph_name_set_display_name: str
    output_names: tuple[str, str, str, str, str]
    morph_upper_limit: float | None
    generation_overrides: ProfileGenerationOverrides
    default_preset_id: str
    default_preset_display_name: str | None
    default_preset_available: bool

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("model profile id must be a non-empty string")
        if not isinstance(self.display_name, str) or not self.display_name:
            raise ValueError("model profile display_name must be a non-empty string")
        output_names = tuple(self.output_names)
        if len(output_names) != 5 or any(
            not isinstance(name, str) or not name for name in output_names
        ):
            raise ValueError("output_names must contain five non-empty strings")
        object.__setattr__(self, "output_names", output_names)
        if not isinstance(self.generation_overrides, ProfileGenerationOverrides):
            raise ValueError("generation_overrides must be ProfileGenerationOverrides")
        if type(self.default_preset_available) is not bool:
            raise ValueError("default_preset_available must be bool")
        if self.default_preset_available and self.default_preset_display_name is None:
            raise ValueError("available default preset must have a display name")


@dataclass(frozen=True)
class ModelProfilePanelState:
    items: tuple[ModelProfilePanelItem, ...] = ()
    preset_options: tuple[ModelProfilePresetOption, ...] = ()
    selected_profile_id: str | None = None
    active_profile_id: str | None = None
    active_profile_display_name: str | None = None
    active_preset_id: str | None = None
    active_preset_display_name: str | None = None
    active_baseline_preset_id: str | None = None
    active_baseline_preset_display_name: str | None = None
    active_morph_name_set_id: str = JAPANESE_MORPH_NAME_SET_ID
    active_morph_name_set_display_name: str = "日本語5母音"
    active_output_names: tuple[str, str, str, str, str] = JAPANESE_OUTPUT_NAMES
    active_generation_settings: GenerationSettings = GenerationSettings()
    active_morph_upper_limit: float = 0.9
    resolution_status: str = "no_profile"
    resolution_reason: str | None = None
    mutation_available: bool = True
    load_error_code: str | None = None
    load_error_message: str | None = None
    busy: bool = False
    panel_revision: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "preset_options", tuple(self.preset_options))
        if self.active_profile_id is None:
            if self.active_profile_display_name is not None:
                raise ValueError("no-profile state must not have an active profile name")
            if self.active_baseline_preset_id is not None:
                raise ValueError("no-profile state must not have an active baseline")
            if self.active_baseline_preset_display_name is not None:
                raise ValueError("no-profile state must not have a baseline name")
        else:
            if not self.active_profile_display_name:
                raise ValueError("active profile state requires a profile name")
            if not self.active_baseline_preset_id:
                raise ValueError("active profile state requires a baseline ID")
            if not self.active_baseline_preset_display_name:
                raise ValueError("active profile state requires a baseline name")
            if self.active_preset_id is not None or self.active_preset_display_name is not None:
                raise ValueError("active profile state must not have an active preset pair")
        if self.active_preset_id is None and self.active_preset_display_name is not None:
            raise ValueError("active preset ID and display name must be a pair")
        if self.active_preset_id is not None and not self.active_preset_display_name:
            raise ValueError("active preset ID and display name must be a pair")
        if not isinstance(self.active_generation_settings, GenerationSettings):
            raise ValueError("active_generation_settings must be GenerationSettings")
        output_names = tuple(self.active_output_names)
        if len(output_names) != 5:
            raise ValueError("active_output_names must contain five names")
        object.__setattr__(self, "active_output_names", output_names)
        if not isinstance(self.active_morph_upper_limit, float):
            raise ValueError("active_morph_upper_limit must be a float")
        if not isinstance(self.resolution_status, str) or not self.resolution_status:
            raise ValueError("resolution_status must be a non-empty string")
        _require_revision(self.panel_revision, "panel_revision")


@dataclass(frozen=True)
class ModelProfileEditorValues:
    display_name: str
    morph_name_set_id: str
    morph_upper_limit: float | None
    generation_overrides: ProfileGenerationOverrides
    default_preset_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.display_name, str):
            raise ValueError("display_name must be a string")
        if not isinstance(self.morph_name_set_id, str) or not self.morph_name_set_id:
            raise ValueError("morph_name_set_id must be a non-empty string")
        if not isinstance(self.generation_overrides, ProfileGenerationOverrides):
            raise ValueError("generation_overrides must be ProfileGenerationOverrides")
        if not isinstance(self.default_preset_id, str) or not self.default_preset_id:
            raise ValueError("default_preset_id must be a non-empty string")


@dataclass(frozen=True)
class ModelProfileSelectRequest:
    selected_profile_id: str | None
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if self.selected_profile_id is not None and (
            not isinstance(self.selected_profile_id, str) or not self.selected_profile_id
        ):
            raise ValueError("selected_profile_id must be None or a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class ModelProfileApplyRequest:
    profile_id: str | None
    expected_panel_revision: int
    expected_editor_revision: int

    def __post_init__(self) -> None:
        if self.profile_id is not None and (
            not isinstance(self.profile_id, str) or not self.profile_id
        ):
            raise ValueError("profile_id must be None or a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        _require_revision(self.expected_editor_revision, "expected_editor_revision")


@dataclass(frozen=True)
class ModelProfileCreateRequest:
    values: ModelProfileEditorValues
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.values, ModelProfileEditorValues):
            raise ValueError("values must be ModelProfileEditorValues")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class ModelProfileUpdateRequest:
    profile_id: str
    values: ModelProfileEditorValues
    expected_panel_revision: int
    expected_editor_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not self.profile_id:
            raise ValueError("profile_id must be a non-empty string")
        if not isinstance(self.values, ModelProfileEditorValues):
            raise ValueError("values must be ModelProfileEditorValues")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        _require_revision(self.expected_editor_revision, "expected_editor_revision")


@dataclass(frozen=True)
class ModelProfileDeleteRequest:
    profile_id: str
    expected_panel_revision: int
    expected_editor_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not self.profile_id:
            raise ValueError("profile_id must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        _require_revision(self.expected_editor_revision, "expected_editor_revision")


@dataclass(frozen=True)
class WhisperModelPanelItem:
    model_key: str
    display_name: str
    size_bytes: int
    vram_hint: str
    speed_hint: str
    recommended_use: str
    artifact_status: str = "unknown"
    failure_code: str | None = None
    manifest_identity: str | None = None
    expected_manifest_identity: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.model_key, str) or not self.model_key:
            raise ValueError("model_key must be a non-empty string")
        if not isinstance(self.display_name, str) or not self.display_name:
            raise ValueError("display_name must be a non-empty string")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise ValueError("size_bytes must be an integer")
        if self.size_bytes <= 0:
            raise ValueError("size_bytes must be positive")
        if self.expected_manifest_identity is None:
            object.__setattr__(self, "expected_manifest_identity", self.manifest_identity)


@dataclass(frozen=True)
class WhisperModelPanelState:
    items: tuple[WhisperModelPanelItem, ...] = ()
    selected_model_key: str = "small"
    active_model_key: str = "small"
    active_manifest_identity: str = ""
    storage_root_display: str = ""
    availability_scan_status: str = "idle"
    availability_scan_failure_code: str | None = None
    notice: str = ""
    busy: bool = False
    management_busy: bool = False
    management_operation: str = "idle"
    management_phase: str = "idle"
    management_job_id: int = 0
    management_model_key: str | None = None
    management_received_bytes: int = 0
    management_expected_bytes: int = 0
    management_failure_code: str | None = None
    management_failure_detail: str | None = None
    management_cleanup_status: str | None = None
    active_config_status: str = "valid"
    panel_revision: int = 0
    loaded_model_key: str | None = None
    loaded_manifest_identity: str | None = None
    analysis_model_key: str | None = None
    analysis_manifest_identity: str | None = None
    analysis_identity_status: str = "not_applicable"
    runtime_identity_status: str = "not_applicable"
    package_version: str = "20250625"
    package_gate_status: str = "not_checked"
    active_config_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        _require_revision(self.panel_revision, "panel_revision")
        if not isinstance(self.selected_model_key, str) or not self.selected_model_key:
            raise ValueError("selected_model_key must be a non-empty string")
        if not isinstance(self.active_model_key, str) or not self.active_model_key:
            raise ValueError("active_model_key must be a non-empty string")


@dataclass(frozen=True)
class WhisperModelSelectRequest:
    selected_model_key: str
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.selected_model_key, str) or not self.selected_model_key:
            raise ValueError("selected_model_key must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class WhisperModelDownloadRequest:
    model_key: str
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.model_key, str) or not self.model_key:
            raise ValueError("model_key must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class WhisperModelApplyRequest:
    model_key: str
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.model_key, str) or not self.model_key:
            raise ValueError("model_key must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class WhisperModelDeleteRequest:
    model_key: str
    expected_panel_revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.model_key, str) or not self.model_key:
            raise ValueError("model_key must be a non-empty string")
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class WhisperStorageRootRequest:
    expected_panel_revision: int

    def __post_init__(self) -> None:
        _require_revision(self.expected_panel_revision, "expected_panel_revision")


@dataclass(frozen=True)
class WhisperModelCancelRequest:
    job_id: int
    expected_panel_revision: int

    def __post_init__(self) -> None:
        _require_revision(self.expected_panel_revision, "expected_panel_revision")
        if isinstance(self.job_id, bool) or not isinstance(self.job_id, int) or self.job_id < 0:
            raise ValueError("job_id must be a non-negative int")


_REANALYSIS_STATE_LINE = "状態: 再解析が必要"
PENDING_OUTPUT_EDIT_INFO_PREFIX = "変更未適用（編集表示）。"
PENDING_OUTPUT_EDIT_DIAGNOSTICS_NOTE = "以下は最後に適用した結果の診断です"


class RightPane(wx.Panel):
    """
    [MS16-B3] 右ペイン型GUI基盤
    Info / Warning / 選択イベント / プリセット / モデルプロファイル のタブを持つ。
    InfoはMS20-B3 diagnostics表示とMS20-B4 playback context、
    他タブは後続Block用の受け口。
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._is_shutting_down = False
        self._pending_output_edit_info = False
        self._pending_output_edit_diagnostics_note = False
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # タブコンテナ
        self.notebook = wx.Notebook(self)
        
        self._init_info_tab()
        self._init_warning_tab()
        self._init_selected_event_tab()
        self._init_preset_tab()
        self._init_model_profile_tab()
        self._init_whisper_model_tab()
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(main_sizer)
        
        # サイズ変更時にテキストのWrapを更新するためのイベントバインド
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.on_closure_restriction_selection = None

    def _init_info_tab(self):
        self.panel_info = wx.ScrolledWindow(self.notebook, style=wx.VSCROLL)
        self.panel_info.SetScrollRate(0, 10)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_pending_output_edit = wx.StaticText(
            self.panel_info,
            label=PENDING_OUTPUT_EDIT_INFO_PREFIX,
        )
        self.st_pending_output_edit.SetMinSize((1, -1))
        self.st_pending_output_edit.Wrap(200)
        self.st_pending_output_edit.Hide()
        sizer.Add(
            self.st_pending_output_edit,
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )
        self.st_pending_output_edit_note = wx.StaticText(
            self.panel_info,
            label=PENDING_OUTPUT_EDIT_DIAGNOSTICS_NOTE,
        )
        self.st_pending_output_edit_note.SetMinSize((1, -1))
        self.st_pending_output_edit_note.Wrap(200)
        self.st_pending_output_edit_note.Hide()
        sizer.Add(
            self.st_pending_output_edit_note,
            0,
            wx.LEFT | wx.RIGHT | wx.EXPAND,
            5,
        )
        self.st_info = wx.StaticText(
            self.panel_info,
            label="",
        )
        self.st_info.SetMinSize((1, -1))
        self.st_info.Wrap(200)
        sizer.Add(self.st_info, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)

        self.st_transition_candidate_status = wx.StaticText(
            self.panel_info,
            label="",
        )
        self.st_transition_candidate_status.SetMinSize((1, -1))
        self.st_transition_candidate_status.Wrap(200)
        sizer.Add(
            self.st_transition_candidate_status,
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )
        self.st_transition_summary = wx.StaticText(self.panel_info, label="")
        self.st_transition_summary.SetMinSize((1, -1))
        self.st_transition_summary.Wrap(200)
        sizer.Add(
            self.st_transition_summary,
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )

        self.pnl_info_reanalysis = wx.Panel(self.panel_info)
        reanalysis_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.st_info_state_prefix = wx.StaticText(
            self.pnl_info_reanalysis,
            label="状態: ",
        )
        self.st_info_reanalysis = wx.StaticText(
            self.pnl_info_reanalysis,
            label="再解析が必要",
        )
        reanalysis_sizer.Add(self.st_info_state_prefix, 0)
        reanalysis_sizer.Add(self.st_info_reanalysis, 0)
        self.pnl_info_reanalysis.SetSizer(reanalysis_sizer)
        sizer.Add(
            self.pnl_info_reanalysis,
            0,
            wx.LEFT | wx.RIGHT | wx.EXPAND,
            5,
        )

        self.st_info_suffix = wx.StaticText(self.panel_info, label="")
        self.st_info_suffix.SetMinSize((1, -1))
        self.st_info_suffix.Wrap(200)
        sizer.Add(
            self.st_info_suffix,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )

        self.st_playback_context = wx.StaticText(self.panel_info, label="")
        self.st_playback_context.SetMinSize((1, -1))
        self.st_playback_context.Wrap(200)
        sizer.Add(
            self.st_playback_context,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.st_shared_restrictions_title = wx.StaticText(
            self.panel_info,
            label="閉口要件による出力制限",
        )
        self.tree_shared_restrictions = wx.TreeCtrl(
            self.panel_info,
            style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT,
            size=(-1, 130),
        )
        self._shared_restrictions_binding = None
        self._shared_restrictions_render_signature = None
        self.tree_shared_restrictions.Bind(
            wx.EVT_TREE_SEL_CHANGED,
            self._on_shared_restriction_selection,
        )
        sizer.Add(
            self.st_shared_restrictions_title,
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )
        sizer.Add(
            self.tree_shared_restrictions,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.pnl_info_reanalysis.Hide()
        self.st_transition_candidate_status.Hide()
        self.st_transition_summary.Hide()
        self.st_info_suffix.Hide()
        self.st_playback_context.Hide()
        self.st_shared_restrictions_title.Hide()
        self.tree_shared_restrictions.Hide()
        self.refresh_info_attention_style()
        self.panel_info.SetSizer(sizer)
        self.notebook.AddPage(self.panel_info, "Info")

    def _init_warning_tab(self):
        self.panel_warning = wx.ScrolledWindow(self.notebook, style=wx.VSCROLL)
        self.panel_warning.SetScrollRate(0, 10)
        self.warning_sizer = wx.BoxSizer(wx.VERTICAL)
        self._warning_signature = None
        self._warning_rows = []
        self._warning_text = "現在の診断はありません。"
        self.panel_warning.SetSizer(self.warning_sizer)
        self._rebuild_warning_rows(())
        self.notebook.AddPage(self.panel_warning, "Warning")

    def _init_selected_event_tab(self):
        self.panel_selected_event = wx.ScrolledWindow(
            self.notebook,
            style=wx.VSCROLL,
        )
        self.panel_selected_event.SetScrollRate(0, 10)
        self.on_selected_event_edit_callback = None
        self.on_selected_event_edit_boundary_callback = None
        self.on_selected_event_reset_callback = None
        self.on_selected_event_mode_callback = None
        self.on_cleanup_event_select_callback = None
        self._cleanup_event_selection_binding = None
        self._cleanup_event_selection_rows = ()
        self._selected_editor_state = None
        self._selected_editor_pending_request = None
        self._suppress_selected_editor_events = False
        self._selected_event_editor_revision = 0
        self._selected_editor_gesture_serial = 0
        self._selected_editor_active_gesture = None
        self._selected_editor_wheel_field = None
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_selected_event = wx.StaticText(
            self.panel_selected_event,
            label="選択中のイベントはありません。"
        )
        self.st_selected_event.Wrap(200)
        sizer.Add(self.st_selected_event, 0, wx.ALL | wx.EXPAND, 5)
        self.st_cleanup_event_label = wx.StaticText(
            self.panel_selected_event, label="出力を整理したイベント"
        )
        self.choice_cleanup_events = wx.Choice(self.panel_selected_event, choices=())
        self.choice_cleanup_events.Enable(False)
        self.st_cleanup_event_label.Hide()
        self.choice_cleanup_events.Hide()
        sizer.Add(self.st_cleanup_event_label, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        sizer.Add(self.choice_cleanup_events, 0, wx.ALL | wx.EXPAND, 5)

        self.pnl_selected_editor = wx.Panel(self.panel_selected_event)
        editor_sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_selected_event_header = wx.StaticText(self.pnl_selected_editor)
        editor_sizer.Add(
            self.st_selected_event_header,
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )

        grid = wx.FlexGridSizer(cols=4, hgap=4, vgap=4)
        grid.AddGrowableCol(3, 1)
        for label in ("項目", "Base", "補正", "Effective"):
            header = wx.StaticText(self.pnl_selected_editor, label=label)
            font = header.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            header.SetFont(font)
            grid.Add(header, 0, wx.ALIGN_CENTER_VERTICAL)

        self._selected_editor_controls = {}
        self._selected_editor_markers = {}
        self._selected_editor_effective_labels = {}
        self._add_selected_editor_row(
            grid,
            "peak_value",
            "開口量",
            wx.TextCtrl(
                self.pnl_selected_editor,
                style=wx.TE_PROCESS_ENTER,
            ),
        )
        for field, label in (
            ("start_offset_frames", "開始offset"),
            ("end_offset_frames", "終了offset"),
            ("hold_frames", "開口保持"),
            ("softness_frames", "閉口スムーズ"),
        ):
            minimum = 0 if field in {"hold_frames", "softness_frames"} else -100000
            maximum = 100 if field in {"hold_frames", "softness_frames"} else 100000
            self._add_selected_editor_row(
                grid,
                field,
                label,
                wx.SpinCtrl(
                    self.pnl_selected_editor,
                    min=minimum,
                    max=maximum,
                    style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER,
                ),
            )
        slope = wx.SpinCtrlDouble(
            self.pnl_selected_editor,
            min=0.0,
            max=1.0,
            inc=0.05,
            style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER,
        )
        slope.SetDigits(2)
        self._add_selected_editor_row(grid, "slope_ratio", "閉口傾斜比", slope)
        editor_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 5)

        self.chk_manual_overlap_limit_override = wx.CheckBox(
            self.pnl_selected_editor,
            label="制限を解除（後続の異母音へ延長）",
        )
        editor_sizer.Add(
            self.chk_manual_overlap_limit_override,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM,
            5,
        )

        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_sizer.Add(
            wx.StaticText(self.pnl_selected_editor, label="長音モード:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
            5,
        )
        self.choice_selected_event_mode = wx.Choice(
            self.pnl_selected_editor,
            choices=("継承", "hold", "decay"),
        )
        self.choice_selected_event_mode.SetSelection(0)
        mode_sizer.Add(
            self.choice_selected_event_mode,
            0,
            wx.LEFT | wx.RIGHT,
            5,
        )
        self.st_selected_event_mode_effective = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_mode_effective.SetMinSize((1, -1))
        mode_sizer.Add(
            self.st_selected_event_mode_effective,
            1,
            wx.RIGHT | wx.EXPAND,
            5,
        )
        editor_sizer.Add(mode_sizer, 0, wx.EXPAND)
        self.st_selected_event_mode_notice = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_mode_notice.SetMinSize((1, -1))
        editor_sizer.Add(
            self.st_selected_event_mode_notice,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )

        self.st_selected_event_validation = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_notice = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_effect_notice_header = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_effect_notice_details = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_crossfade_notice_header = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_crossfade_notice_details = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        self.st_selected_event_slope_helper = wx.StaticText(
            self.pnl_selected_editor,
            label="",
        )
        for label in (
            self.st_selected_event_notice,
            self.st_selected_event_mode_notice,
            self.st_selected_event_effect_notice_header,
            self.st_selected_event_effect_notice_details,
            self.st_selected_event_crossfade_notice_header,
            self.st_selected_event_crossfade_notice_details,
            self.st_selected_event_slope_helper,
        ):
            label.SetMinSize((1, -1))
        editor_sizer.Add(
            self.st_selected_event_validation,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        editor_sizer.Add(
            self.st_selected_event_effect_notice_header,
            0,
            wx.LEFT | wx.RIGHT | wx.EXPAND,
            5,
        )
        editor_sizer.Add(
            self.st_selected_event_effect_notice_details,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        editor_sizer.Add(
            self.st_selected_event_crossfade_notice_header,
            0,
            wx.LEFT | wx.RIGHT | wx.EXPAND,
            5,
        )
        editor_sizer.Add(
            self.st_selected_event_crossfade_notice_details,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        editor_sizer.Add(
            self.st_selected_event_slope_helper,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        editor_sizer.Add(
            self.st_selected_event_notice,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.btn_reset_selected_event = ThemeButton(
            self.pnl_selected_editor,
            label="選択イベントの補正をリセット",
        )
        editor_sizer.Add(
            self.btn_reset_selected_event,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.pnl_selected_editor.SetSizer(editor_sizer)
        self.pnl_selected_editor.Hide()
        sizer.Add(self.pnl_selected_editor, 0, wx.EXPAND)
        self.panel_selected_event.SetSizer(sizer)
        self.notebook.AddPage(self.panel_selected_event, "選択イベント")
        self._bind_selected_editor_events()

    def _add_selected_editor_row(self, grid, field, label, control):
        grid.Add(
            wx.StaticText(self.pnl_selected_editor, label=label),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        marker = wx.StaticText(self.pnl_selected_editor, label="-")
        grid.Add(marker, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(control, 0, wx.EXPAND)
        effective = wx.StaticText(self.pnl_selected_editor, label="-")
        grid.Add(effective, 0, wx.ALIGN_CENTER_VERTICAL)
        self._selected_editor_controls[field] = control
        self._selected_editor_markers[field] = marker
        self._selected_editor_effective_labels[field] = effective

    def _bind_selected_editor_events(self):
        for field, control in self._selected_editor_controls.items():
            control.Bind(
                wx.EVT_TEXT,
                lambda event, name=field: self._on_selected_editor_text(event, name),
            )
            control.Bind(
                wx.EVT_TEXT_ENTER,
                lambda event, name=field: self._on_selected_editor_commit_boundary(
                    event,
                    name,
                ),
            )
            control.Bind(
                wx.EVT_KILL_FOCUS,
                lambda event, name=field: self._on_selected_editor_commit_boundary(
                    event,
                    name,
                ),
            )
            if isinstance(control, wx.SpinCtrlDouble):
                control.Bind(
                    wx.EVT_SPINCTRLDOUBLE,
                    lambda event, name=field: self._on_selected_editor_spin(
                        event,
                        name,
                    ),
                )
            elif isinstance(control, wx.SpinCtrl):
                control.Bind(
                    wx.EVT_SPINCTRL,
                    lambda event, name=field: self._on_selected_editor_spin(
                        event,
                        name,
                    ),
                )
            if isinstance(control, (wx.SpinCtrl, wx.SpinCtrlDouble)):
                control.Bind(
                    wx.EVT_LEFT_DOWN,
                    lambda event, name=field: self._on_selected_editor_mouse_down(
                        event,
                        name,
                    ),
                )
                control.Bind(
                    wx.EVT_LEFT_UP,
                    lambda event, name=field: self._on_selected_editor_mouse_up(
                        event,
                        name,
                    ),
                )
                control.Bind(
                    wx.EVT_KEY_DOWN,
                    lambda event, name=field: self._on_selected_editor_key_down(
                        event,
                        name,
                    ),
                )
                control.Bind(
                    wx.EVT_KEY_UP,
                    lambda event, name=field: self._on_selected_editor_key_up(
                        event,
                        name,
                    ),
                )
                control.Bind(
                    wx.EVT_MOUSEWHEEL,
                    lambda event, name=field: self._on_selected_editor_mouse_wheel(
                        event,
                        name,
                    ),
                )
        self.btn_reset_selected_event.Bind(
            wx.EVT_BUTTON,
            self._on_reset_selected_event,
        )
        self.choice_selected_event_mode.Bind(
            wx.EVT_CHOICE,
            self._on_selected_event_mode_choice,
        )
        self.chk_manual_overlap_limit_override.Bind(
            wx.EVT_CHECKBOX,
            self._on_manual_overlap_limit_override,
        )
        self.choice_cleanup_events.Bind(wx.EVT_CHOICE, self._on_cleanup_event_choice)

    def _init_preset_tab(self):
        self.panel_preset = wx.ScrolledWindow(self.notebook, style=wx.VSCROLL)
        self.panel_preset.SetScrollRate(0, 10)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._preset_panel_state = PresetPanelState()
        self._preset_selector_ids: tuple[str | None, ...] = (None,)
        self._suppress_preset_events = False
        self._preset_notice = ""
        self.on_preset_select_callback = None
        self.on_preset_apply_callback = None
        self.on_preset_create_callback = None
        self.on_preset_update_callback = None
        self.on_preset_delete_callback = None
        self.st_preset_active = wx.StaticText(
            self.panel_preset,
            label="現在: カスタム（現在の設定）",
        )
        self.st_preset_active.SetMinSize((1, -1))
        sizer.Add(self.st_preset_active, 0, wx.ALL | wx.EXPAND, 5)
        self.st_preset_source = wx.StaticText(self.panel_preset, label="")
        self.st_preset_source.SetMinSize((1, -1))
        sizer.Add(self.st_preset_source, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(
            wx.StaticText(self.panel_preset, label="選択:"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )
        self.choice_preset = wx.Choice(self.panel_preset, choices=("カスタム（現在の設定）",))
        sizer.Add(self.choice_preset, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_preset_settings = wx.StaticText(self.panel_preset, label="")
        self.st_preset_settings.SetMinSize((1, -1))
        sizer.Add(self.st_preset_settings, 0, wx.ALL | wx.EXPAND, 5)
        self.btn_apply_preset = ThemeButton(self.panel_preset, label="選択したプリセットを適用")
        sizer.Add(self.btn_apply_preset, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        management_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_create_preset = ThemeButton(self.panel_preset, label="作成")
        self.btn_update_preset = ThemeButton(self.panel_preset, label="更新 / 名前変更")
        self.btn_delete_preset = ThemeButton(self.panel_preset, label="削除")
        management_sizer.Add(self.btn_create_preset, 1, wx.RIGHT, 3)
        management_sizer.Add(self.btn_update_preset, 1, wx.LEFT | wx.RIGHT, 3)
        management_sizer.Add(self.btn_delete_preset, 1, wx.LEFT, 3)
        sizer.Add(management_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        self.st_preset_notice = wx.StaticText(self.panel_preset, label="")
        self.st_preset_notice.SetMinSize((1, -1))
        sizer.Add(self.st_preset_notice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        self.st_preset = wx.StaticText(
            self.panel_preset,
            label="",
        )
        self.st_preset.Hide()
        sizer.Add(self.st_preset, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_preset.SetSizer(sizer)
        self.notebook.AddPage(self.panel_preset, "プリセット")
        self.refresh_preset_styles()
        self.btn_apply_preset.Bind(wx.EVT_BUTTON, self._on_apply_preset)
        self.btn_create_preset.Bind(wx.EVT_BUTTON, self._on_create_preset)
        self.btn_update_preset.Bind(wx.EVT_BUTTON, self._on_update_preset)
        self.btn_delete_preset.Bind(wx.EVT_BUTTON, self._on_delete_preset)
        self.choice_preset.Bind(wx.EVT_CHOICE, self._on_select_preset)

    def _init_model_profile_tab(self):
        self.panel_model_profile = wx.ScrolledWindow(
            self.notebook,
            style=wx.VSCROLL,
        )
        self.panel_model_profile.SetScrollRate(0, 10)
        self._model_profile_panel_state = ModelProfilePanelState()
        self._model_profile_selector_ids: tuple[str | None, ...] = (None,)
        self._suppress_model_profile_events = False
        self._model_profile_notice = ""
        self.on_model_profile_select_callback = None
        self.on_model_profile_apply_callback = None
        self.on_model_profile_create_callback = None
        self.on_model_profile_update_callback = None
        self.on_model_profile_delete_callback = None
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_model_profile_active = wx.StaticText(
            self.panel_model_profile,
            label="現在: プロファイルなし（日本語5母音）",
        )
        self.st_model_profile_active.SetMinSize((1, -1))
        sizer.Add(self.st_model_profile_active, 0, wx.ALL | wx.EXPAND, 5)
        self.st_model_profile_baseline = wx.StaticText(
            self.panel_model_profile,
            label="基準プリセット: なし / Custom",
        )
        self.st_model_profile_baseline.SetMinSize((1, -1))
        sizer.Add(self.st_model_profile_baseline, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_model_profile_morph = wx.StaticText(
            self.panel_model_profile,
            label="モーフ名セット: 日本語5母音（あ / い / う / え / お）",
        )
        self.st_model_profile_morph.SetMinSize((1, -1))
        sizer.Add(self.st_model_profile_morph, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_model_profile_values = wx.StaticText(
            self.panel_model_profile,
            label="解決値: モーフ最大値 0.90 / 開口保持 0f / 閉口スムース 0f / 長音 hold",
        )
        self.st_model_profile_values.SetMinSize((1, -1))
        sizer.Add(self.st_model_profile_values, 0, wx.ALL | wx.EXPAND, 5)
        self.st_model_profile_resolution = wx.StaticText(
            self.panel_model_profile,
            label="",
        )
        self.st_model_profile_resolution.SetMinSize((1, -1))
        sizer.Add(self.st_model_profile_resolution, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(
            wx.StaticText(self.panel_model_profile, label="選択:"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )
        self.choice_model_profile = wx.Choice(
            self.panel_model_profile,
            choices=("プロファイルなし（日本語5母音）",),
        )
        sizer.Add(self.choice_model_profile, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_model_profile_selected = wx.StaticText(
            self.panel_model_profile,
            label="選択値: プロファイルなし",
        )
        self.st_model_profile_selected.SetMinSize((1, -1))
        sizer.Add(self.st_model_profile_selected, 0, wx.ALL | wx.EXPAND, 5)
        self.btn_apply_model_profile = ThemeButton(
            self.panel_model_profile,
            label="選択したモデルプロファイルを適用",
        )
        sizer.Add(
            self.btn_apply_model_profile,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        management_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_create_model_profile = ThemeButton(self.panel_model_profile, label="作成")
        self.btn_update_model_profile = ThemeButton(
            self.panel_model_profile,
            label="更新 / 名前変更",
        )
        self.btn_delete_model_profile = ThemeButton(self.panel_model_profile, label="削除")
        management_sizer.Add(self.btn_create_model_profile, 1, wx.RIGHT, 3)
        management_sizer.Add(self.btn_update_model_profile, 1, wx.LEFT | wx.RIGHT, 3)
        management_sizer.Add(self.btn_delete_model_profile, 1, wx.LEFT, 3)
        sizer.Add(
            management_sizer,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.st_model_profile_notice = wx.StaticText(
            self.panel_model_profile,
            label="",
        )
        self.st_model_profile_notice.SetMinSize((1, -1))
        sizer.Add(
            self.st_model_profile_notice,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.st_model_profile = wx.StaticText(self.panel_model_profile, label="")
        self.st_model_profile.Hide()
        sizer.Add(self.st_model_profile, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_model_profile.SetSizer(sizer)
        self.notebook.AddPage(self.panel_model_profile, "モデルプロファイル")
        self.refresh_model_profile_styles()
        self.btn_apply_model_profile.Bind(wx.EVT_BUTTON, self._on_apply_model_profile)
        self.btn_create_model_profile.Bind(wx.EVT_BUTTON, self._on_create_model_profile)
        self.btn_update_model_profile.Bind(wx.EVT_BUTTON, self._on_update_model_profile)
        self.btn_delete_model_profile.Bind(wx.EVT_BUTTON, self._on_delete_model_profile)
        self.choice_model_profile.Bind(wx.EVT_CHOICE, self._on_select_model_profile)

    def _init_whisper_model_tab(self):
        self.panel_whisper_model = wx.ScrolledWindow(
            self.notebook,
            style=wx.VSCROLL,
        )
        self.panel_whisper_model.SetScrollRate(0, 10)
        self._whisper_model_panel_state = WhisperModelPanelState()
        self._whisper_model_selector_keys: tuple[str, ...] = ("small",)
        self._suppress_whisper_model_events = False
        self.on_whisper_model_select_callback = None
        self.on_whisper_model_download_callback = None
        self.on_whisper_model_apply_callback = None
        self.on_whisper_model_cancel_callback = None
        self.on_whisper_model_delete_callback = None
        self.on_whisper_storage_root_callback = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.st_whisper_model_active = wx.StaticText(
            self.panel_whisper_model,
            label="現在: Whisper small",
        )
        self.st_whisper_model_active.SetMinSize((1, -1))
        sizer.Add(self.st_whisper_model_active, 0, wx.ALL | wx.EXPAND, 5)
        self.st_whisper_model_selected = wx.StaticText(
            self.panel_whisper_model,
            label="選択: Whisper small",
        )
        self.st_whisper_model_selected.SetMinSize((1, -1))
        sizer.Add(self.st_whisper_model_selected, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_whisper_model_storage = wx.StaticText(
            self.panel_whisper_model,
            label="保存先: 未確認",
        )
        self.st_whisper_model_storage.SetMinSize((1, -1))
        sizer.Add(self.st_whisper_model_storage, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_whisper_model_scan = wx.StaticText(
            self.panel_whisper_model,
            label="保存状態: 未確認",
        )
        self.st_whisper_model_scan.SetMinSize((1, -1))
        sizer.Add(self.st_whisper_model_scan, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        self.st_whisper_model_explanation = wx.StaticText(
            self.panel_whisper_model,
            label=(
                "候補を選択しただけでは、downloadや解析は開始されません。\n"
                "適用と再解析は後続の操作で行います。"
            ),
        )
        self.st_whisper_model_explanation.SetMinSize((1, -1))
        sizer.Add(
            self.st_whisper_model_explanation,
            0,
            wx.ALL | wx.EXPAND,
            5,
        )
        sizer.Add(
            wx.StaticText(self.panel_whisper_model, label="候補:"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
            5,
        )
        self.choice_whisper_model = wx.Choice(
            self.panel_whisper_model,
            choices=("Whisper small",),
        )
        sizer.Add(self.choice_whisper_model, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_whisper_download = ThemeButton(
            self.panel_whisper_model,
            label="Download & Verify",
        )
        self.btn_whisper_apply = ThemeButton(
            self.panel_whisper_model,
            label="選択モデルを適用",
        )
        self.btn_whisper_cancel = ThemeButton(
            self.panel_whisper_model,
            label="キャンセル",
        )
        self.btn_whisper_delete = ThemeButton(
            self.panel_whisper_model,
            label="削除",
        )
        action_sizer.Add(self.btn_whisper_download, 1, wx.RIGHT, 5)
        action_sizer.Add(self.btn_whisper_apply, 1, wx.RIGHT, 5)
        action_sizer.Add(self.btn_whisper_cancel, 0, wx.RIGHT, 5)
        action_sizer.Add(self.btn_whisper_delete, 0)
        sizer.Add(action_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.btn_whisper_change_storage = ThemeButton(
            self.panel_whisper_model,
            label="保存先を変更",
        )
        sizer.Add(
            self.btn_whisper_change_storage,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.gauge_whisper_model_progress = wx.Gauge(
            self.panel_whisper_model,
            range=1000,
        )
        self.gauge_whisper_model_progress.SetValue(0)
        sizer.Add(
            self.gauge_whisper_model_progress,
            0,
            wx.LEFT | wx.RIGHT | wx.EXPAND,
            5,
        )
        self.st_whisper_model_management = wx.StaticText(
            self.panel_whisper_model,
            label="管理状態: 待機中",
        )
        self.st_whisper_model_management.SetMinSize((1, -1))
        sizer.Add(
            self.st_whisper_model_management,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.st_whisper_model_details = wx.StaticText(
            self.panel_whisper_model,
            label="",
        )
        self.st_whisper_model_details.SetMinSize((1, -1))
        sizer.Add(self.st_whisper_model_details, 0, wx.ALL | wx.EXPAND, 5)
        self.st_whisper_model_notice = wx.StaticText(
            self.panel_whisper_model,
            label="",
        )
        self.st_whisper_model_notice.SetMinSize((1, -1))
        sizer.Add(
            self.st_whisper_model_notice,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            5,
        )
        self.panel_whisper_model.SetSizer(sizer)
        self.notebook.AddPage(self.panel_whisper_model, "Whisperモデル")
        self.refresh_whisper_model_styles()
        self.choice_whisper_model.Bind(wx.EVT_CHOICE, self._on_select_whisper_model)
        self.btn_whisper_download.Bind(wx.EVT_BUTTON, self._on_download_whisper_model)
        self.btn_whisper_apply.Bind(wx.EVT_BUTTON, self._on_apply_whisper_model)
        self.btn_whisper_cancel.Bind(wx.EVT_BUTTON, self._on_cancel_whisper_model)
        self.btn_whisper_delete.Bind(wx.EVT_BUTTON, self._on_delete_whisper_model)
        self.btn_whisper_change_storage.Bind(
            wx.EVT_BUTTON,
            self._on_change_whisper_storage,
        )

    def _on_select_whisper_model(self, event) -> None:
        if self._suppress_whisper_model_events:
            return
        index = self.choice_whisper_model.GetSelection()
        if index < 0 or index >= len(self._whisper_model_selector_keys):
            return
        callback = self.on_whisper_model_select_callback
        if callback is not None:
            callback(
                WhisperModelSelectRequest(
                    self._whisper_model_selector_keys[index],
                    self._whisper_model_panel_state.panel_revision,
                )
            )

    def _on_download_whisper_model(self, event) -> None:
        state = self._whisper_model_panel_state
        callback = self.on_whisper_model_download_callback
        if callback is None or not state.selected_model_key:
            return
        callback(
            WhisperModelDownloadRequest(
                state.selected_model_key,
                state.panel_revision,
            )
        )

    def _on_apply_whisper_model(self, event) -> None:
        state = self._whisper_model_panel_state
        callback = self.on_whisper_model_apply_callback
        if callback is None or not state.selected_model_key:
            return
        callback(
            WhisperModelApplyRequest(
                state.selected_model_key,
                state.panel_revision,
            )
        )

    def _on_cancel_whisper_model(self, event) -> None:
        state = self._whisper_model_panel_state
        callback = self.on_whisper_model_cancel_callback
        if callback is None:
            return
        callback(
            WhisperModelCancelRequest(
                state.management_job_id,
                state.panel_revision,
            )
        )

    def _on_delete_whisper_model(self, event) -> None:
        state = self._whisper_model_panel_state
        callback = self.on_whisper_model_delete_callback
        if callback is None or not state.selected_model_key:
            return
        callback(
            WhisperModelDeleteRequest(
                state.selected_model_key,
                state.panel_revision,
            )
        )

    def _on_change_whisper_storage(self, event) -> None:
        callback = self.on_whisper_storage_root_callback
        if callback is not None:
            callback(
                WhisperStorageRootRequest(
                    self._whisper_model_panel_state.panel_revision,
                )
            )

    def get_whisper_model_panel_state(self) -> WhisperModelPanelState:
        return self._whisper_model_panel_state

    def set_whisper_model_panel_state(self, state: WhisperModelPanelState) -> None:
        if not isinstance(state, WhisperModelPanelState):
            raise ValueError("state must be WhisperModelPanelState")
        self._whisper_model_panel_state = state
        self._suppress_whisper_model_events = True
        try:
            self._whisper_model_selector_keys = tuple(
                item.model_key for item in state.items
            )
            labels = tuple(item.display_name for item in state.items)
            self.choice_whisper_model.SetItems(labels or ("候補なし",))
            selected_index = (
                self._whisper_model_selector_keys.index(state.selected_model_key)
                if state.selected_model_key in self._whisper_model_selector_keys
                else wx.NOT_FOUND
            )
            self.choice_whisper_model.SetSelection(selected_index)

            active_item = next(
                (item for item in state.items if item.model_key == state.active_model_key),
                None,
            )
            selected_item = next(
                (item for item in state.items if item.model_key == state.selected_model_key),
                None,
            )
            active_name = (
                active_item.display_name
                if active_item is not None and state.active_config_status == "valid"
                else "設定不整合（明示的な再選択が必要）"
            )
            selected_name = (
                selected_item.display_name
                if selected_item is not None
                else "設定不整合"
            )
            self.st_whisper_model_active.SetLabel(f"現在: {active_name}")
            self.st_whisper_model_selected.SetLabel(f"選択: {selected_name}")
            self.st_whisper_model_storage.SetLabel(
                f"保存先: {state.storage_root_display or '未確認'}"
            )
            scan_labels = {
                "idle": "未確認",
                "pending": "確認中",
                "succeeded": "確認済み",
                "failed": "確認失敗",
            }
            self.st_whisper_model_scan.SetLabel(
                f"保存状態: {scan_labels.get(state.availability_scan_status, '未確認')}"
            )
            if selected_item is None:
                details = "選択候補の設定を確認できません。"
            else:
                details = (
                    f"{selected_item.display_name}\n"
                    f"サイズ: {_format_size(selected_item.size_bytes)}\n"
                    f"VRAM目安: {selected_item.vram_hint} / 速度目安: {selected_item.speed_hint}\n"
                    f"推奨用途: {selected_item.recommended_use}\n"
                    f"保存状態: {_format_whisper_artifact_status(selected_item.artifact_status)}\n"
                    f"読み込み済み: {state.loaded_model_key or 'なし'}\n"
                    f"解析結果モデル: {state.analysis_model_key or 'なし'}\n"
                    f"identity: {state.analysis_identity_status} / runtime: {state.runtime_identity_status}\n"
                    f"package gate: {state.package_gate_status}"
                )
            self.st_whisper_model_details.SetLabel(details)
            self.st_whisper_model_notice.SetLabel(state.notice)
            operation_labels = {
                "idle": "待機中",
                "download": "Download",
                "delete": "削除",
                "apply": "適用",
            }
            phase_labels = {
                "idle": "待機中",
                "preflight": "保存先を準備中",
                "downloading": "取得中",
                "verifying": "検証中",
                "cancelling": "キャンセル中",
                "blocked": "保護のため停止",
                "finished": "完了処理済み",
            }
            self.st_whisper_model_management.SetLabel(
                "管理状態: "
                f"{operation_labels.get(state.management_operation, '管理')} / "
                f"{phase_labels.get(state.management_phase, '確認中')}"
            )
            expected = state.management_expected_bytes
            received = state.management_received_bytes
            if expected > 0:
                self.gauge_whisper_model_progress.SetValue(
                    min(1000, max(0, int(received * 1000 / expected)))
                )
            else:
                self.gauge_whisper_model_progress.SetValue(0)
            enabled = not state.busy and not state.management_busy and bool(state.items)
            self.choice_whisper_model.Enable(enabled)
            selected_available = selected_item is not None
            selected_verified = (
                selected_item is not None
                and selected_item.artifact_status == "verified"
            )
            self.btn_whisper_download.Enable(
                enabled and selected_available and not selected_verified
            )
            self.btn_whisper_apply.Enable(
                enabled
                and selected_verified
                and state.selected_model_key != state.active_model_key
            )
            self.btn_whisper_delete.Enable(
                enabled and selected_verified
            )
            self.btn_whisper_change_storage.Enable(
                not state.busy and not state.management_busy
            )
            self.btn_whisper_cancel.Enable(state.management_busy)
        finally:
            self._suppress_whisper_model_events = False
        self._update_wrap()

    def set_whisper_model_panel_busy(self, busy: bool) -> None:
        state = self._whisper_model_panel_state
        self.set_whisper_model_panel_state(
            WhisperModelPanelState(
                items=state.items,
                selected_model_key=state.selected_model_key,
                active_model_key=state.active_model_key,
                active_manifest_identity=state.active_manifest_identity,
                storage_root_display=state.storage_root_display,
                availability_scan_status=state.availability_scan_status,
                availability_scan_failure_code=state.availability_scan_failure_code,
                notice=state.notice,
                busy=busy,
                management_busy=state.management_busy,
                management_operation=state.management_operation,
                management_phase=state.management_phase,
                management_job_id=state.management_job_id,
                management_model_key=state.management_model_key,
                management_received_bytes=state.management_received_bytes,
                management_expected_bytes=state.management_expected_bytes,
                management_failure_code=state.management_failure_code,
                management_failure_detail=state.management_failure_detail,
                management_cleanup_status=state.management_cleanup_status,
                active_config_status=state.active_config_status,
                panel_revision=state.panel_revision,
                loaded_model_key=state.loaded_model_key,
                loaded_manifest_identity=state.loaded_manifest_identity,
                analysis_model_key=state.analysis_model_key,
                analysis_manifest_identity=state.analysis_manifest_identity,
                analysis_identity_status=state.analysis_identity_status,
                runtime_identity_status=state.runtime_identity_status,
                package_version=state.package_version,
                package_gate_status=state.package_gate_status,
                active_config_reason=state.active_config_reason,
            )
        )

    def refresh_whisper_model_styles(self) -> None:
        palette = ThemeManager.get_palette()
        self.st_whisper_model_active.SetForegroundColour(palette.text_fg)
        self.st_whisper_model_selected.SetForegroundColour(palette.text_fg)
        self.st_whisper_model_storage.SetForegroundColour(palette.muted_text)
        self.st_whisper_model_scan.SetForegroundColour(palette.muted_text)
        self.st_whisper_model_explanation.SetForegroundColour(palette.muted_text)
        self.st_whisper_model_management.SetForegroundColour(palette.muted_text)
        self.st_whisper_model_details.SetForegroundColour(palette.text_fg)
        self.st_whisper_model_notice.SetForegroundColour(palette.attention_text)

    def _on_size(self, event):
        # リサイズ時にWrap幅を再計算して表示崩れを防ぐ
        width = self.GetClientSize().width - 20
        info_width = self.panel_info.GetClientSize().width - 10
        if info_width > 0:
            self.st_pending_output_edit.Wrap(info_width)
            self.st_pending_output_edit_note.Wrap(info_width)
            self.st_info.Wrap(info_width)
            self.st_info_suffix.Wrap(info_width)
            self.st_playback_context.Wrap(info_width)
            self.panel_info.Layout()
            self.panel_info.FitInside()
        if width > 0:
            for _, summary_label, detail_label in self._warning_rows:
                summary_label.Wrap(width)
                if detail_label is not None:
                    detail_label.Wrap(width)
            self.st_selected_event.Wrap(width)
            self.st_selected_event_header.Wrap(width)
            self.st_selected_event_validation.Wrap(width)
            self.st_selected_event_notice.Wrap(width)
            self.st_selected_event_mode_notice.Wrap(width)
            self.st_selected_event_effect_notice_header.Wrap(width)
            self.st_selected_event_effect_notice_details.Wrap(width)
            self.st_selected_event_crossfade_notice_header.Wrap(width)
            self.st_selected_event_crossfade_notice_details.Wrap(width)
            self.st_selected_event_slope_helper.Wrap(width)
            self.st_preset_active.Wrap(width)
            self.st_preset_source.Wrap(width)
            self.st_preset_settings.Wrap(width)
            self.st_preset_notice.Wrap(width)
            self.st_preset.Wrap(width)
            self.st_model_profile_active.Wrap(width)
            self.st_model_profile_baseline.Wrap(width)
            self.st_model_profile_morph.Wrap(width)
            self.st_model_profile_values.Wrap(width)
            self.st_model_profile_resolution.Wrap(width)
            self.st_model_profile_selected.Wrap(width)
            self.st_model_profile_notice.Wrap(width)
            self.st_model_profile.Wrap(width)
            self.st_whisper_model_active.Wrap(width)
            self.st_whisper_model_selected.Wrap(width)
            self.st_whisper_model_storage.Wrap(width)
            self.st_whisper_model_scan.Wrap(width)
            self.st_whisper_model_explanation.Wrap(width)
            self.st_whisper_model_management.Wrap(width)
            self.st_whisper_model_details.Wrap(width)
            self.st_whisper_model_notice.Wrap(width)
            
            # 各パネルのレイアウト更新
            self.panel_warning.Layout()
            self.panel_selected_event.Layout()
            self.panel_selected_event.FitInside()
            self.panel_preset.Layout()
            self.panel_preset.FitInside()
            self.panel_model_profile.Layout()
            self.panel_model_profile.FitInside()
            self.panel_whisper_model.Layout()
            self.panel_whisper_model.FitInside()
            
        event.Skip()

    # --- View Helpers ---
    def show_selected_event_tab(self):
        """Show the existing selected-event page without emitting a page event."""
        page_index = self.notebook.FindPage(self.panel_selected_event)
        if (
            page_index == wx.NOT_FOUND
            or self.notebook.GetSelection() == page_index
        ):
            return
        self.notebook.ChangeSelection(page_index)

    def set_info_text(
        self,
        text: str,
        *,
        pending_edits: bool = False,
        pending_diagnostics: bool = True,
    ):
        self._set_pending_output_edit_info(
            pending_edits,
            show_diagnostics_note=pending_diagnostics,
        )
        if (
            self.st_info.GetLabel() == text
            and not self.pnl_info_reanalysis.IsShown()
            and not self.st_info_suffix.IsShown()
            and not self.st_info_suffix.GetLabel()
        ):
            return
        self.st_info.SetLabel(text)
        self.pnl_info_reanalysis.Hide()
        self.st_info_suffix.SetLabel("")
        self.st_info_suffix.Hide()
        self._update_wrap()

    def get_info_text(self) -> str:
        if not self.pnl_info_reanalysis.IsShown():
            body = self.st_info.GetLabel()
        else:
            body = "\n".join(
                (
                    self.st_info.GetLabel(),
                    _REANALYSIS_STATE_LINE,
                    self.st_info_suffix.GetLabel(),
                )
            )
        if not self._pending_output_edit_info:
            return body
        lines = [PENDING_OUTPUT_EDIT_INFO_PREFIX]
        if self._pending_output_edit_diagnostics_note:
            lines.append(PENDING_OUTPUT_EDIT_DIAGNOSTICS_NOTE)
        lines.extend(("", body))
        return "\n".join(lines)

    def set_transition_candidate_status(self, text: str) -> None:
        if type(text) is not str or not text:
            raise ValueError("transition candidate status must be non-empty text")
        if self.st_transition_candidate_status.GetLabel() == text and self.st_transition_candidate_status.IsShown():
            return
        self.st_transition_candidate_status.SetLabel(text)
        self.st_transition_candidate_status.Show()
        self._update_wrap()

    def clear_transition_candidate_status(self) -> None:
        if not self.st_transition_candidate_status.IsShown() and not self.st_transition_candidate_status.GetLabel():
            return
        self.st_transition_candidate_status.SetLabel("")
        self.st_transition_candidate_status.Hide()
        self._update_wrap()

    def set_transition_summary(
        self,
        summary,
        *,
        label: str = "候補遷移",
    ) -> None:
        if summary is None:
            self.clear_transition_summary()
            return
        if label not in {"候補遷移", "自動母音遷移", "自動整理：比較候補"}:
            raise ValueError("transition summary label is unsupported")
        pairs = tuple(getattr(summary, "pairs", ()))
        applied = sum(getattr(item, "state", None) == "applied" for item in pairs)
        not_applicable = sum(
            getattr(item, "state", None) == "not_applicable" for item in pairs
        )
        text = f"{label}: 適用 {applied}件 / 非適用 {not_applicable}件"
        if self.st_transition_summary.GetLabel() == text and self.st_transition_summary.IsShown():
            return
        self.st_transition_summary.SetLabel(text)
        self.st_transition_summary.Show()
        self._update_wrap()

    def clear_transition_summary(self) -> None:
        if not self.st_transition_summary.IsShown() and not self.st_transition_summary.GetLabel():
            return
        self.st_transition_summary.SetLabel("")
        self.st_transition_summary.Hide()
        self._update_wrap()

    def refresh_info_attention_style(self):
        font = self.st_info_reanalysis.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.st_info_reanalysis.SetFont(font)
        self.st_info_reanalysis.SetForegroundColour(
            ThemeManager.get_palette().attention_text
        )
        pending_font = self.st_pending_output_edit.GetFont()
        pending_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.st_pending_output_edit.SetFont(pending_font)
        self.st_pending_output_edit.SetForegroundColour(
            ThemeManager.get_palette().pending_edit_text
        )

    def _set_pending_output_edit_info(
        self,
        pending: bool,
        *,
        show_diagnostics_note: bool = True,
    ) -> bool:
        pending = bool(pending)
        show_diagnostics_note = bool(pending and show_diagnostics_note)
        if (
            self._pending_output_edit_info == pending
            and self._pending_output_edit_diagnostics_note == show_diagnostics_note
        ):
            return False
        self._pending_output_edit_info = pending
        self._pending_output_edit_diagnostics_note = show_diagnostics_note
        if pending:
            self.st_pending_output_edit.Show()
            self.st_pending_output_edit_note.Show(show_diagnostics_note)
            self.refresh_info_attention_style()
        else:
            self.st_pending_output_edit.Hide()
            self.st_pending_output_edit_note.Hide()
        self._update_wrap()
        return True

    def clear_info(self):
        self.set_info_text("")
        self.clear_transition_candidate_status()
        self.clear_transition_summary()
        self.clear_playback_context()

    def set_playback_context(self, context: PlaybackInfoContext):
        text = format_playback_info_context(context)
        was_shown = self.st_playback_context.IsShown()
        if was_shown and self.st_playback_context.GetLabel() == text:
            return

        self.st_playback_context.SetLabel(text)
        if not was_shown:
            self.st_playback_context.Show()
            self._update_wrap()
            return
        self.st_playback_context.Refresh()

    def clear_playback_context(self):
        if not self.st_playback_context.IsShown() and not self.st_playback_context.GetLabel():
            return
        self.st_playback_context.SetLabel("")
        self.st_playback_context.Hide()
        self._update_wrap()

    def get_playback_context_text(self) -> str:
        if not self.st_playback_context.IsShown():
            return ""
        return self.st_playback_context.GetLabel()

    def set_info_snapshot(
        self,
        snapshot: OutputDiagnosticsSnapshot,
        *,
        analysis_in_progress: bool = False,
        transition_label: str | None = None,
        pending_edits: bool = False,
    ):
        if transition_label is None:
            identity = snapshot.shared_final_output_identity
            input_identity = getattr(identity, "input_identity", None)
            transition_label = (
                "自動母音遷移"
                if getattr(input_identity, "application_binding_digest", None)
                is not None
                else "候補遷移"
            )
        self.set_transition_summary(
            snapshot.transition_summary,
            label=transition_label,
        )
        text = format_output_diagnostics_info(
            snapshot,
            analysis_in_progress=analysis_in_progress,
        )
        self._set_pending_output_edit_info(pending_edits)
        self._set_shared_final_output_restrictions(snapshot)
        if _REANALYSIS_STATE_LINE not in text:
            self.set_info_text(text, pending_edits=pending_edits)
            return

        prefix, suffix = text.split(_REANALYSIS_STATE_LINE, maxsplit=1)
        prefix = prefix.rstrip("\n")
        suffix = suffix.lstrip("\n")
        if (
            self.st_info.GetLabel() == prefix
            and self.st_info_suffix.GetLabel() == suffix
            and self.pnl_info_reanalysis.IsShown()
            and self.st_info_suffix.IsShown()
        ):
            return
        self.st_info.SetLabel(prefix)
        self.st_info_suffix.SetLabel(suffix)
        self.pnl_info_reanalysis.Show()
        self.st_info_suffix.Show()
        self.refresh_info_attention_style()
        self._update_wrap()

    def _set_shared_final_output_restrictions(
        self,
        snapshot: OutputDiagnosticsSnapshot,
    ) -> None:
        identity = snapshot.shared_final_output_identity
        restrictions = tuple(snapshot.shared_final_output_restrictions)
        binding = getattr(identity, "binding_digest", None)
        if not isinstance(binding, str) or not binding:
            binding = None
        targets = tuple(snapshot.shared_final_output_restriction_event_targets)
        render_signature = (binding, restrictions, targets)
        if render_signature == self._shared_restrictions_render_signature:
            return
        self._shared_restrictions_render_signature = render_signature
        if binding is None or not restrictions:
            self._shared_restrictions_binding = None
            self.tree_shared_restrictions.DeleteAllItems()
            self.tree_shared_restrictions.Hide()
            self.st_shared_restrictions_title.Hide()
            self.panel_info.Layout()
            return
        self._shared_restrictions_binding = binding
        self.tree_shared_restrictions.DeleteAllItems()
        root = self.tree_shared_restrictions.AddRoot("制限一覧")
        targets_by_id = {}
        for target in targets:
            restriction_id = getattr(target.restriction, "restriction_id", None)
            if isinstance(restriction_id, str):
                targets_by_id.setdefault(restriction_id, []).append(target)
        for restriction in restrictions:
            try:
                requested = float.fromhex(restriction.requested_value_hex)
                effective = float.fromhex(restriction.effective_value_hex)
            except (AttributeError, TypeError, ValueError, OverflowError):
                continue
            label = (
                f"{restriction.semantic_morph} / frame {restriction.frame_no} / "
                f"{requested:.4f} → {effective:.4f} / "
                f"{_format_closure_restriction_reason(restriction.reason)}"
            )
            parent = self.tree_shared_restrictions.AppendItem(root, label)
            for target in targets_by_id.get(restriction.restriction_id, ()):
                event = target.event
                group_label = ",".join(
                    str(index) for index in event.group_event_indices
                )
                long_label = (
                    ""
                    if event.long_vowel_role is None
                    else (
                        f" / long {event.long_vowel_role}"
                        f" ({event.long_vowel_mode}, source {event.long_vowel_source_event_index})"
                    )
                )
                child = self.tree_shared_restrictions.AppendItem(
                    parent,
                    (
                        f"event {event.base_event_index}: frame "
                        f"{event.start_frame}–{event.end_frame} "
                        f"(peak {event.peak_frame}) / group [{group_label}]"
                        f"{long_label}"
                    ),
                )
                self.tree_shared_restrictions.SetItemData(child, target)
            if targets_by_id.get(restriction.restriction_id):
                self.tree_shared_restrictions.Expand(parent)
        self.st_shared_restrictions_title.Show()
        self.tree_shared_restrictions.Show()
        self.panel_info.Layout()

    def clear_shared_final_output_restrictions(self) -> None:
        empty_signature = (None, (), ())
        if (
            self._shared_restrictions_render_signature == empty_signature
            and not self.tree_shared_restrictions.IsShown()
            and not self.st_shared_restrictions_title.IsShown()
        ):
            return
        self._shared_restrictions_render_signature = empty_signature
        self._shared_restrictions_binding = None
        self.tree_shared_restrictions.DeleteAllItems()
        self.tree_shared_restrictions.Hide()
        self.st_shared_restrictions_title.Hide()
        self.panel_info.Layout()

    def prepare_for_shutdown(self) -> None:
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        self.on_closure_restriction_selection = None
        try:
            self.tree_shared_restrictions.Unbind(
                wx.EVT_TREE_SEL_CHANGED,
                handler=self._on_shared_restriction_selection,
            )
        except RuntimeError:
            pass

    def _on_shared_restriction_selection(self, event):
        if self._is_shutting_down:
            event.Skip()
            return
        item = event.GetItem()
        try:
            target = self.tree_shared_restrictions.GetItemData(item)
        except RuntimeError:
            event.Skip()
            return
        if target is not None and callable(self.on_closure_restriction_selection):
            self.on_closure_restriction_selection(
                self._shared_restrictions_binding,
                target,
            )
        event.Skip()

    def set_warnings(self, items: list[str]):
        if not items:
            self.clear_warnings()
            return
        text = "\n".join(f"- {msg}" for msg in items)
        self._warning_text = text
        rows = tuple(("WARNING", msg, "") for msg in items)
        self._rebuild_warning_rows(rows)

    def clear_warnings(self):
        self._warning_text = "現在の診断はありません。"
        self._rebuild_warning_rows(())

    def set_warning_snapshot(self, snapshot: OutputDiagnosticsSnapshot):
        rows = tuple(
            (item.severity.value, item.summary, item.detail)
            for item in snapshot.items
        )
        self._warning_text = (
            "現在の診断はありません。"
            if not rows
            else "\n\n".join(
                f"[{severity}] {summary}" + (f"\n{detail}" if detail else "")
                for severity, summary, detail in rows
            )
        )
        self._rebuild_warning_rows(rows)

    def get_warning_text(self) -> str:
        return self._warning_text

    def get_warning_row_labels(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (
                summary_label.GetLabel(),
                "" if detail_label is None else detail_label.GetLabel(),
            )
            for _, summary_label, detail_label in self._warning_rows
        )

    def refresh_warning_styles(self):
        palette = ThemeManager.get_palette()
        colours = {
            "ERROR": palette.error_text,
            "WARNING": palette.attention_text,
            "INFO": palette.text_fg,
        }
        for severity, summary_label, detail_label in self._warning_rows:
            font = summary_label.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            summary_label.SetFont(font)
            summary_label.SetForegroundColour(colours.get(severity, palette.text_fg))
            if detail_label is not None:
                detail_label.SetForegroundColour(palette.text_fg)

    def _rebuild_warning_rows(self, rows):
        signature = tuple(rows)
        if signature == self._warning_signature:
            return
        self._warning_signature = signature
        self.warning_sizer.Clear(delete_windows=True)
        self._warning_rows = []

        if not rows:
            empty_label = wx.StaticText(
                self.panel_warning,
                label="現在の診断はありません。",
            )
            self.warning_sizer.Add(
                empty_label,
                0,
                wx.ALL | wx.EXPAND,
                5,
            )
        else:
            for index, (severity, summary, detail) in enumerate(rows):
                summary_label = wx.StaticText(
                    self.panel_warning,
                    label=f"[{severity}] {summary}",
                )
                summary_label.SetMinSize((1, -1))
                self.warning_sizer.Add(
                    summary_label,
                    0,
                    wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND,
                    5,
                )
                detail_label = None
                if detail:
                    detail_label = wx.StaticText(self.panel_warning, label=detail)
                    detail_label.SetMinSize((1, -1))
                    self.warning_sizer.Add(
                        detail_label,
                        0,
                        wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
                        5,
                    )
                elif index < len(rows) - 1:
                    self.warning_sizer.AddSpacer(5)
                self._warning_rows.append((severity, summary_label, detail_label))

        self.refresh_warning_styles()
        self._update_wrap()

    def set_selected_event_summary(self, text: str):
        self.clear_selected_event_gesture_state()
        self._selected_editor_state = None
        self.pnl_selected_editor.Hide()
        self.st_selected_event.Show()
        self.st_selected_event.SetLabel(text)
        self._update_wrap()

    def clear_selected_event(self):
        self.set_selected_event_summary("選択中のイベントはありません。")

    def set_cleanup_event_choices(
        self,
        *,
        binding_digest: str,
        ticket: int,
        lifecycle_epoch: int,
        items: tuple[tuple[str, int], ...],
        busy: bool = False,
    ) -> None:
        rows = tuple(items)
        if any(
            type(label) is not str or not label
            or isinstance(index, bool) or not isinstance(index, int) or index < 0
            for label, index in rows
        ):
            raise ValueError("cleanup event choices are invalid")
        self._cleanup_event_selection_binding = (binding_digest, ticket, lifecycle_epoch)
        self._cleanup_event_selection_rows = rows
        self.choice_cleanup_events.Set(tuple(label for label, _index in rows))
        self.choice_cleanup_events.SetSelection(wx.NOT_FOUND)
        available = bool(rows) and not busy
        self.st_cleanup_event_label.Show(bool(rows))
        self.choice_cleanup_events.Show(bool(rows))
        self.choice_cleanup_events.Enable(available)
        self.panel_selected_event.Layout()
        self.panel_selected_event.FitInside()

    def clear_cleanup_event_choices(self) -> None:
        self._cleanup_event_selection_binding = None
        self._cleanup_event_selection_rows = ()
        self.choice_cleanup_events.Set(())
        self.choice_cleanup_events.SetSelection(wx.NOT_FOUND)
        self.choice_cleanup_events.Enable(False)
        self.choice_cleanup_events.Hide()
        self.st_cleanup_event_label.Hide()
        self.panel_selected_event.Layout()
        self.panel_selected_event.FitInside()

    def _on_cleanup_event_choice(self, _event) -> None:
        selection = self.choice_cleanup_events.GetSelection()
        binding = self._cleanup_event_selection_binding
        callback = self.on_cleanup_event_select_callback
        if (
            selection < 0
            or selection >= len(self._cleanup_event_selection_rows)
            or binding is None
            or not callable(callback)
        ):
            return
        callback(CleanupEventSelectionRequest(
            binding_digest=binding[0],
            ticket=binding[1],
            lifecycle_epoch=binding[2],
            base_event_index=self._cleanup_event_selection_rows[selection][1],
        ))

    def set_selected_event_editor_revision(self, revision: int) -> None:
        self._selected_event_editor_revision = _require_revision(
            revision,
            "selected_event_editor_revision",
        )

    def set_selected_event_editor_state(
        self,
        state: SelectedEventEditorState,
        *,
        busy: bool = False,
        operation_notice: str = "",
    ):
        active = self._selected_editor_active_gesture
        self._suppress_selected_editor_events = True
        try:
            previous_state = self._selected_editor_state
            if (
                previous_state is None
                or previous_state.editor_revision != state.editor_revision
            ):
                self._selected_editor_pending_request = None
            self._selected_editor_state = state
            self._selected_event_editor_revision = state.editor_revision
            self.st_selected_event.Hide()
            self.pnl_selected_editor.Show()
            tail_text = "group末尾" if state.is_group_tail else "group途中"
            self.st_selected_event_header.SetLabel(
                f"Event {state.base_event_index} / 母音 {state.vowel} / "
                f"{state.group_member_count} event / {tail_text}"
            )
            values = {
                "peak_value": state.requested_peak_value,
                "start_offset_frames": state.requested_start_offset_frames,
                "end_offset_frames": state.requested_end_offset_frames,
                "hold_frames": state.requested_hold_frames,
                "softness_frames": state.requested_softness_frames,
                "slope_ratio": state.requested_slope_ratio,
            }
            controls = self._selected_editor_controls
            controls["start_offset_frames"].SetRange(
                state.start_offset_min,
                state.start_offset_max,
            )
            controls["end_offset_frames"].SetRange(
                min(state.end_offset_min, state.requested_end_offset_frames),
                max(state.end_offset_max, state.requested_end_offset_frames),
            )
            controls["peak_value"].ChangeValue(f"{state.requested_peak_value:.4g}")
            for field in (
                "start_offset_frames",
                "end_offset_frames",
                "hold_frames",
                "softness_frames",
            ):
                controls[field].SetValue(int(values[field]))
            controls["slope_ratio"].SetValue(state.requested_slope_ratio)
            self.chk_manual_overlap_limit_override.SetValue(
                state.requested_manual_overlap_limit_override
            )
            mode_selection = {
                None: 0,
                "hold": 1,
                "decay": 2,
            }[state.requested_long_vowel_mode]
            self.choice_selected_event_mode.SetSelection(mode_selection)
            effective_mode_text = (
                "実効: 継承"
                if state.effective_long_vowel_mode is None
                else f"実効: {state.effective_long_vowel_mode}"
            )
            self.st_selected_event_mode_effective.SetLabel(effective_mode_text)
            self.st_selected_event_mode_notice.SetLabel(
                state.long_vowel_mode_notice
            )

            overridden = {
                "peak_value": state.peak_overridden,
                "start_offset_frames": state.start_overridden,
                "end_offset_frames": state.end_overridden,
                "hold_frames": state.hold_overridden,
                "softness_frames": state.softness_overridden,
                "slope_ratio": state.slope_overridden,
            }
            base_labels = {
                "peak_value": f"{state.base_peak_value:.4g}",
                "start_offset_frames": f"{state.base_start_frame}f",
                "end_offset_frames": f"{state.base_end_frame}f",
                "hold_frames": "-",
                "softness_frames": "-",
                "slope_ratio": "-",
            }
            effective_labels = {
                "peak_value": f"{state.effective_peak_value:.4g}",
                "start_offset_frames": f"{state.effective_start_frame}f",
                "end_offset_frames": f"{state.effective_end_frame}f",
                "hold_frames": f"{state.effective_hold_frames}f",
                "softness_frames": f"{state.effective_softness_frames}f",
                "slope_ratio": f"{state.requested_slope_ratio:.2f}",
            }
            for field in controls:
                self._selected_editor_markers[field].SetLabel(
                    f"{base_labels[field]}\n"
                    f"{'補正あり' if overridden[field] else '補正なし'}"
                )
                self._selected_editor_effective_labels[field].SetLabel(
                    effective_labels[field]
                )

            tail_enabled = state.tail_controls_enabled and not busy
            controls["peak_value"].Enable(not busy)
            controls["start_offset_frames"].Enable(not busy)
            controls["end_offset_frames"].Enable(not busy)
            controls["hold_frames"].Enable(tail_enabled)
            controls["softness_frames"].Enable(tail_enabled)
            controls["slope_ratio"].Enable(
                state.slope_enabled and tail_enabled
            )
            self.chk_manual_overlap_limit_override.Enable(
                state.manual_overlap_override_enabled and not busy
            )
            self.choice_selected_event_mode.Enable(
                state.long_vowel_mode_enabled and not busy
            )
            self.btn_reset_selected_event.Enable(state.reset_enabled and not busy)
            self.st_selected_event_validation.SetLabel(
                state.end_offset_range_error
            )
            self.st_selected_event_notice.SetLabel(operation_notice)
            self.st_selected_event_effect_notice_header.SetLabel(
                state.effect_notice_header
            )
            self.st_selected_event_effect_notice_details.SetLabel(
                "\n".join(state.effect_notice_lines)
            )
            self.st_selected_event_crossfade_notice_header.SetLabel(
                state.crossfade_notice_header
            )
            self.st_selected_event_crossfade_notice_details.SetLabel(
                "\n".join(state.crossfade_notice_lines)
            )
            self.st_selected_event_slope_helper.SetLabel(state.slope_helper_text)
            self.st_selected_event_effect_notice_header.Show(
                bool(state.effect_notice_header)
            )
            self.st_selected_event_effect_notice_details.Show(
                bool(state.effect_notice_lines)
            )
            self.st_selected_event_crossfade_notice_header.Show(
                bool(state.crossfade_notice_header)
            )
            self.st_selected_event_crossfade_notice_details.Show(
                bool(state.crossfade_notice_lines)
            )
            self.st_selected_event_slope_helper.Show(bool(state.slope_helper_text))
            self.st_selected_event_mode_notice.Show(bool(state.long_vowel_mode_notice))
            self.refresh_selected_event_editor_styles()
        finally:
            self._suppress_selected_editor_events = False
        if active is not None:
            control = self._selected_editor_controls.get(active.field)
            if (
                active.base_event_index != state.base_event_index
                or active.base_identity_digest != state.base_identity_digest
                or busy
                or control is None
                or not control.IsEnabled()
            ):
                self.clear_selected_event_gesture_state()
        self._update_wrap()

    def set_selected_event_editor_error(self, message: str):
        self.st_selected_event_validation.SetLabel(message)
        self.refresh_selected_event_editor_styles()
        self._update_wrap()

    def set_selected_event_editor_notice(self, message: str):
        self.st_selected_event_notice.SetLabel(message)
        self.refresh_selected_event_editor_styles()
        self._update_wrap()

    def refresh_selected_event_editor_styles(self):
        palette = ThemeManager.get_palette()
        self.chk_manual_overlap_limit_override.SetForegroundColour(palette.text_fg)
        self.st_selected_event_validation.SetForegroundColour(palette.error_text)
        self.st_selected_event_notice.SetForegroundColour(palette.attention_text)
        self.st_selected_event_mode_notice.SetForegroundColour(palette.attention_text)
        self.st_selected_event_effect_notice_header.SetForegroundColour(
            palette.attention_text
        )
        self.st_selected_event_effect_notice_details.SetForegroundColour(
            palette.attention_text
        )
        self.st_selected_event_crossfade_notice_header.SetForegroundColour(
            palette.attention_text
        )
        self.st_selected_event_crossfade_notice_details.SetForegroundColour(
            palette.attention_text
        )
        self.st_selected_event_slope_helper.SetForegroundColour(palette.muted_text)
        header_font = self.st_selected_event_effect_notice_header.GetFont()
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.st_selected_event_effect_notice_header.SetFont(header_font)
        crossfade_header_font = (
            self.st_selected_event_crossfade_notice_header.GetFont()
        )
        crossfade_header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.st_selected_event_crossfade_notice_header.SetFont(
            crossfade_header_font
        )
        for label in (
            self.st_selected_event_mode_effective,
            self.st_selected_event_effect_notice_details,
            self.st_selected_event_crossfade_notice_details,
            self.st_selected_event_slope_helper,
        ):
            font = label.GetFont()
            font.SetWeight(wx.FONTWEIGHT_NORMAL)
            label.SetFont(font)
        for label in self._selected_editor_effective_labels.values():
            label.SetForegroundColour(palette.text_fg)
        state = self._selected_editor_state
        if state is not None:
            if state.hold_is_limited:
                self._selected_editor_effective_labels[
                    "hold_frames"
                ].SetForegroundColour(palette.attention_text)
            if state.softness_is_limited:
                self._selected_editor_effective_labels[
                    "softness_frames"
                ].SetForegroundColour(palette.attention_text)

    def _parse_selected_editor_value(self, field: str):
        control = self._selected_editor_controls[field]
        if field == "peak_value":
            try:
                value = float(control.GetValue())
            except (TypeError, ValueError):
                raise ValueError("開口量は0以上の数値で入力してください。")
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("開口量は0以上の有限値で入力してください。")
            return value
        if field == "slope_ratio":
            return float(control.GetValue())
        return int(control.GetValue())

    def _current_requested_value(self, state, field):
        return {
            "peak_value": state.requested_peak_value,
            "start_offset_frames": state.requested_start_offset_frames,
            "end_offset_frames": state.requested_end_offset_frames,
            "hold_frames": state.requested_hold_frames,
            "softness_frames": state.requested_softness_frames,
            "slope_ratio": state.requested_slope_ratio,
        }[field]

    def _on_selected_editor_text(self, event, field):
        event.Skip()
        if self._suppress_selected_editor_events or field != "peak_value":
            return
        try:
            self._parse_selected_editor_value(field)
        except ValueError as error:
            self.set_selected_event_editor_error(str(error))
        else:
            self.set_selected_event_editor_error("")

    def _selected_editor_arrow_key_codes(self):
        return {
            wx.WXK_UP,
            wx.WXK_DOWN,
            getattr(wx, "WXK_NUMPAD_UP", wx.WXK_UP),
            getattr(wx, "WXK_NUMPAD_DOWN", wx.WXK_DOWN),
        }

    def _begin_selected_editor_gesture(self, field: str):
        state = self._selected_editor_state
        if state is None:
            return None
        active = self._selected_editor_active_gesture
        if (
            active is not None
            and active.base_event_index == state.base_event_index
            and active.base_identity_digest == state.base_identity_digest
            and active.final_output_binding == state.final_output_binding
            and active.field == field
        ):
            return active
        if active is not None:
            self._finish_active_selected_editor_gesture()
        self._selected_editor_gesture_serial += 1
        active = SelectedEventEditBoundaryRequest(
            base_event_index=state.base_event_index,
            base_identity_digest=state.base_identity_digest,
            field=field,
            coalescing_token=self._selected_editor_gesture_serial,
            final_output_binding=state.final_output_binding,
        )
        self._selected_editor_active_gesture = active
        return active

    def _finish_active_selected_editor_gesture(self):
        active = self._selected_editor_active_gesture
        self._selected_editor_active_gesture = None
        if active is None:
            return
        callback = self.on_selected_event_edit_boundary_callback
        if callback is not None:
            callback(active)

    def clear_selected_event_gesture_state(self):
        self._selected_editor_active_gesture = None
        self._selected_editor_wheel_field = None

    def is_selected_event_editor_window(self, window) -> bool:
        current = window
        while current is not None:
            if current is self.pnl_selected_editor:
                return True
            current = current.GetParent()
        return False

    def selected_event_editor_has_dirty_input(self) -> bool:
        state = self._selected_editor_state
        if state is None:
            return False
        for field in self._selected_editor_controls:
            try:
                value = self._parse_selected_editor_value(field)
            except ValueError:
                return True
            if value != self._current_requested_value(state, field):
                return True
        if state.long_vowel_mode_enabled and self.choice_selected_event_mode.IsEnabled():
            selected = self.choice_selected_event_mode.GetSelection()
            requested = (None, "hold", "decay")[selected] if selected in {0, 1, 2} else None
            if requested != state.requested_long_vowel_mode:
                return True
        if (
            state.manual_overlap_override_enabled
            and self.chk_manual_overlap_limit_override.IsEnabled()
            and self.chk_manual_overlap_limit_override.GetValue()
            != state.requested_manual_overlap_limit_override
        ):
            return True
        return False

    def _on_selected_event_mode_choice(self, event):
        event.Skip()
        state = self._selected_editor_state
        if (
            self._suppress_selected_editor_events
            or state is None
            or not state.long_vowel_mode_enabled
            or not self.choice_selected_event_mode.IsEnabled()
        ):
            return
        selection = self.choice_selected_event_mode.GetSelection()
        if selection not in {0, 1, 2}:
            return
        value = (None, "hold", "decay")[selection]
        if value == state.requested_long_vowel_mode:
            return
        callback = self.on_selected_event_mode_callback or self.on_selected_event_edit_callback
        if callback is not None:
            callback(
                SelectedEventEditRequest(
                    base_event_index=state.base_event_index,
                    base_identity_digest=state.base_identity_digest,
                    editor_revision=state.editor_revision,
                    field="long_vowel_mode",
                    value=value,
                    coalescing_token=None,
                    final_output_binding=state.final_output_binding,
                )
            )

    def _on_manual_overlap_limit_override(self, event):
        event.Skip()
        state = self._selected_editor_state
        if (
            self._suppress_selected_editor_events
            or state is None
            or not state.manual_overlap_override_enabled
            or not self.chk_manual_overlap_limit_override.IsEnabled()
        ):
            return
        value = self.chk_manual_overlap_limit_override.GetValue()
        if value == state.requested_manual_overlap_limit_override:
            return
        callback = self.on_selected_event_edit_callback
        if callback is not None:
            self._selected_editor_pending_request = (
                state.editor_revision,
                "manual_overlap_limit_override",
                value,
            )
            callback(
                SelectedEventEditRequest(
                    base_event_index=state.base_event_index,
                    base_identity_digest=state.base_identity_digest,
                    editor_revision=state.editor_revision,
                    field="manual_overlap_limit_override",
                    value=value,
                    final_output_binding=state.final_output_binding,
                )
            )

    def _on_selected_editor_mouse_down(self, event, field):
        event.Skip()
        self._begin_selected_editor_gesture(field)

    def _on_selected_editor_mouse_up(self, event, field):
        event.Skip()
        active = self._selected_editor_active_gesture
        if active is not None and active.field == field:
            self._finish_active_selected_editor_gesture()

    def _on_selected_editor_key_down(self, event, field):
        event.Skip()
        if event.GetKeyCode() in self._selected_editor_arrow_key_codes():
            self._begin_selected_editor_gesture(field)

    def _on_selected_editor_key_up(self, event, field):
        event.Skip()
        if event.GetKeyCode() not in self._selected_editor_arrow_key_codes():
            return
        active = self._selected_editor_active_gesture
        if active is not None and active.field == field:
            self._finish_active_selected_editor_gesture()

    def _on_selected_editor_mouse_wheel(self, event, field):
        event.Skip()
        self._finish_active_selected_editor_gesture()
        self._selected_editor_wheel_field = field

    def _on_selected_editor_spin(self, event, field):
        token = None
        if self._selected_editor_wheel_field == field:
            self._selected_editor_wheel_field = None
        else:
            active = self._selected_editor_active_gesture
            if active is not None and active.field == field:
                token = active.coalescing_token
        self._commit_selected_editor_control(
            event,
            field,
            coalescing_token=token,
        )

    def _on_selected_editor_commit_boundary(self, event, field):
        active = self._selected_editor_active_gesture
        if active is not None and active.field == field:
            self._finish_active_selected_editor_gesture()
        self._commit_selected_editor_control(event, field)

    def _commit_selected_editor_control(
        self,
        event,
        field,
        *,
        coalescing_token=None,
    ):
        event.Skip()
        state = self._selected_editor_state
        if self._suppress_selected_editor_events or state is None:
            return
        try:
            value = self._parse_selected_editor_value(field)
        except ValueError as error:
            self.set_selected_event_editor_error(str(error))
            return
        current = self._current_requested_value(state, field)
        if value == current:
            return
        if self._selected_editor_pending_request == (
            state.editor_revision,
            field,
            value,
        ):
            return
        callback = self.on_selected_event_edit_callback
        if callback is not None:
            self._selected_editor_pending_request = (
                state.editor_revision,
                field,
                value,
            )
            active = self._selected_editor_active_gesture
            request_binding = state.final_output_binding
            if (
                coalescing_token is not None
                and active is not None
                and active.coalescing_token == coalescing_token
            ):
                request_binding = active.final_output_binding
            callback(
                SelectedEventEditRequest(
                    base_event_index=state.base_event_index,
                    base_identity_digest=state.base_identity_digest,
                    editor_revision=state.editor_revision,
                    field=field,
                    value=value,
                    coalescing_token=coalescing_token,
                    final_output_binding=request_binding,
                )
            )

    def clear_selected_event_edit_pending(self) -> None:
        self._selected_editor_pending_request = None

    def _on_reset_selected_event(self, event):
        state = self._selected_editor_state
        if state is None or not state.reset_enabled:
            return
        callback = self.on_selected_event_reset_callback
        if callback is not None:
            callback(
                state.base_event_index,
                state.base_identity_digest,
                state.editor_revision,
                state.final_output_binding,
            )

    def get_preset_panel_state(self) -> PresetPanelState:
        return self._preset_panel_state

    def set_preset_panel_notice(self, message: str):
        self._preset_notice = message or ""
        self.st_preset_notice.SetLabel(self._preset_notice)
        self._update_wrap()

    def set_preset_panel_state(self, state: PresetPanelState):
        if not isinstance(state, PresetPanelState):
            raise ValueError("state must be a PresetPanelState")
        self._preset_panel_state = state
        labels = ["カスタム（現在の設定）"]
        ids: list[str | None] = [None]
        for item in state.items:
            source = "組み込み" if item.source == "built_in" else "ユーザー"
            labels.append(f"[{source}] {item.display_name}")
            ids.append(item.id)
        self._suppress_preset_events = True
        try:
            self._preset_selector_ids = tuple(ids)
            self.choice_preset.SetItems(labels)
            selected_index = (
                ids.index(state.selected_preset_id)
                if state.selected_preset_id in ids
                else 0
            )
            self.choice_preset.SetSelection(selected_index)
            active_text = state.active_preset_display_name or "カスタム（現在の設定）"
            self.st_preset_active.SetLabel(f"現在: {active_text}")
            active_item = next(
                (item for item in state.items if item.id == state.active_preset_id),
                None,
            )
            if active_item is None:
                source_text = "種類: Custom"
            else:
                source_text = "種類: 組み込み" if active_item.source == "built_in" else "種類: ユーザー"
            self.st_preset_source.SetLabel(source_text)
            selected_item = next(
                (item for item in state.items if item.id == state.selected_preset_id),
                None,
            )
            preview_settings = (
                selected_item.generation_settings
                if selected_item is not None
                else state.active_generation_settings
            )
            self.st_preset_settings.SetLabel(
                "設定: "
                f"開口保持 {preview_settings.closing_hold_frames}f / "
                f"閉口スムーズ {preview_settings.closing_softness_frames}f / "
                f"長音 {preview_settings.long_vowel_mode}"
            )
            if state.load_error_code:
                self._preset_notice = (
                    state.load_error_message
                    or f"ユーザープリセットを読み込めませんでした ({state.load_error_code})。"
                )
            self.st_preset_notice.SetLabel(self._preset_notice)
            busy = state.busy
            selected_is_user = selected_item is not None and selected_item.source == "user"
            self.choice_preset.Enable(not busy)
            self.btn_apply_preset.Enable(
                not busy and state.selected_preset_id is not None and selected_item is not None
            )
            self.btn_create_preset.Enable(not busy and state.mutation_available)
            self.btn_update_preset.Enable(
                not busy and state.mutation_available and selected_is_user
            )
            self.btn_delete_preset.Enable(
                not busy and state.mutation_available and selected_is_user
            )
        finally:
            self._suppress_preset_events = False
        self._update_wrap()

    def set_preset_panel_busy(self, busy: bool):
        state = self._preset_panel_state
        self.set_preset_panel_state(
            PresetPanelState(
                items=state.items,
                selected_preset_id=state.selected_preset_id,
                active_preset_id=state.active_preset_id,
                active_preset_display_name=state.active_preset_display_name,
                active_generation_settings=state.active_generation_settings,
                mutation_available=state.mutation_available,
                load_error_code=state.load_error_code,
                load_error_message=state.load_error_message,
                busy=busy,
                panel_revision=state.panel_revision,
            )
        )

    def get_model_profile_panel_state(self) -> ModelProfilePanelState:
        return self._model_profile_panel_state

    def set_model_profile_panel_notice(self, message: str) -> None:
        self._model_profile_notice = message or ""
        self.st_model_profile_notice.SetLabel(self._model_profile_notice)
        self._update_wrap()

    def set_model_profile_panel_state(self, state: ModelProfilePanelState) -> None:
        if not isinstance(state, ModelProfilePanelState):
            raise ValueError("state must be ModelProfilePanelState")
        self._model_profile_panel_state = state
        labels = ["プロファイルなし（日本語5母音）"]
        ids: list[str | None] = [None]
        for item in state.items:
            labels.append(item.display_name)
            ids.append(item.id)
        self._suppress_model_profile_events = True
        try:
            self._model_profile_selector_ids = tuple(ids)
            self.choice_model_profile.SetItems(labels)
            selected_index = (
                ids.index(state.selected_profile_id)
                if state.selected_profile_id in ids
                else 0
            )
            self.choice_model_profile.SetSelection(selected_index)

            active_name = state.active_profile_display_name or "プロファイルなし（日本語5母音）"
            self.st_model_profile_active.SetLabel(f"現在: {active_name}")
            baseline_name = state.active_baseline_preset_display_name or "なし / Custom"
            self.st_model_profile_baseline.SetLabel(f"基準プリセット: {baseline_name}")
            self.st_model_profile_morph.SetLabel(
                "モーフ名セット: "
                f"{state.active_morph_name_set_display_name}（"
                f"{' / '.join(state.active_output_names)}）"
            )
            settings = state.active_generation_settings
            self.st_model_profile_values.SetLabel(
                "解決値: "
                f"モーフ最大値 {state.active_morph_upper_limit:.2f} / "
                f"開口保持 {settings.closing_hold_frames}f / "
                f"閉口スムース {settings.closing_softness_frames}f / "
                f"長音 {settings.long_vowel_mode}"
            )
            if state.resolution_reason:
                self.st_model_profile_resolution.SetLabel(
                    f"解決状態: {state.resolution_status}（{state.resolution_reason}）"
                )
            else:
                self.st_model_profile_resolution.SetLabel(
                    f"解決状態: {state.resolution_status}"
                )

            selected_item = next(
                (item for item in state.items if item.id == state.selected_profile_id),
                None,
            )
            if selected_item is None:
                self.st_model_profile_selected.SetLabel(
                    "選択値: プロファイルなし（日本語5母音）"
                )
            else:
                preset_text = selected_item.default_preset_display_name
                if not selected_item.default_preset_available:
                    preset_text = "参照先プリセットが見つかりません"
                overrides = selected_item.generation_overrides
                override_text = (
                    f"上限 {'継承' if selected_item.morph_upper_limit is None else f'上書き: {selected_item.morph_upper_limit:.2f}'} / "
                    f"保持 {'継承' if overrides.closing_hold_frames is None else f'上書き: {overrides.closing_hold_frames}f'} / "
                    f"スムース {'継承' if overrides.closing_softness_frames is None else f'上書き: {overrides.closing_softness_frames}f'} / "
                    f"長音 {'継承' if overrides.long_vowel_mode is None else f'上書き: {overrides.long_vowel_mode}'}"
                )
                self.st_model_profile_selected.SetLabel(
                    "選択値: "
                    f"{selected_item.display_name} / 基準 {preset_text} / "
                    f"{selected_item.morph_name_set_display_name} / {override_text}"
                )

            if state.load_error_code:
                self._model_profile_notice = (
                    state.load_error_message
                    or f"ユーザーモデルプロファイルを読み込めませんでした ({state.load_error_code})。"
                )
            self.st_model_profile_notice.SetLabel(self._model_profile_notice)
            busy = state.busy
            selected_valid = selected_item is None or selected_item.default_preset_available
            selected_is_user = selected_item is not None
            selected_is_active = (
                selected_item is not None
                and selected_item.id == state.active_profile_id
            )
            self.choice_model_profile.Enable(not busy)
            self.btn_apply_model_profile.Enable(
                not busy
                and selected_valid
                and (
                    selected_item is not None
                    or state.active_profile_id is not None
                )
            )
            self.btn_create_model_profile.Enable(not busy and state.mutation_available)
            self.btn_update_model_profile.Enable(
                not busy and state.mutation_available and selected_is_user
            )
            self.btn_delete_model_profile.Enable(
                not busy
                and state.mutation_available
                and selected_is_user
                and not selected_is_active
            )
        finally:
            self._suppress_model_profile_events = False
        self._update_wrap()

    def set_model_profile_panel_busy(self, busy: bool) -> None:
        state = self._model_profile_panel_state
        self.set_model_profile_panel_state(
            ModelProfilePanelState(
                items=state.items,
                preset_options=state.preset_options,
                selected_profile_id=state.selected_profile_id,
                active_profile_id=state.active_profile_id,
                active_profile_display_name=state.active_profile_display_name,
                active_preset_id=state.active_preset_id,
                active_preset_display_name=state.active_preset_display_name,
                active_baseline_preset_id=state.active_baseline_preset_id,
                active_baseline_preset_display_name=state.active_baseline_preset_display_name,
                active_morph_name_set_id=state.active_morph_name_set_id,
                active_morph_name_set_display_name=state.active_morph_name_set_display_name,
                active_output_names=state.active_output_names,
                active_generation_settings=state.active_generation_settings,
                active_morph_upper_limit=state.active_morph_upper_limit,
                resolution_status=state.resolution_status,
                resolution_reason=state.resolution_reason,
                mutation_available=state.mutation_available,
                load_error_code=state.load_error_code,
                load_error_message=state.load_error_message,
                busy=busy,
                panel_revision=state.panel_revision,
            )
        )

    def refresh_model_profile_styles(self) -> None:
        palette = ThemeManager.get_palette()
        self.st_model_profile_notice.SetForegroundColour(palette.attention_text)
        self.st_model_profile_resolution.SetForegroundColour(palette.attention_text)
        self.st_model_profile_baseline.SetForegroundColour(palette.muted_text)
        self.st_model_profile_morph.SetForegroundColour(palette.muted_text)
        self.st_model_profile_values.SetForegroundColour(palette.text_fg)
        self.st_model_profile_selected.SetForegroundColour(palette.text_fg)

    def _on_select_model_profile(self, event) -> None:
        event.Skip()
        if self._suppress_model_profile_events:
            return
        index = self.choice_model_profile.GetSelection()
        if index < 0 or index >= len(self._model_profile_selector_ids):
            return
        callback = self.on_model_profile_select_callback
        if callback is not None:
            callback(
                ModelProfileSelectRequest(
                    self._model_profile_selector_ids[index],
                    self._model_profile_panel_state.panel_revision,
                )
            )

    def _on_apply_model_profile(self, event) -> None:
        event.Skip()
        state = self._model_profile_panel_state
        callback = self.on_model_profile_apply_callback
        if callback is not None:
            callback(
                ModelProfileApplyRequest(
                    state.selected_profile_id,
                    state.panel_revision,
                    self._selected_event_editor_revision,
                )
            )

    def _selected_model_profile_item(self) -> ModelProfilePanelItem | None:
        selected_id = self._model_profile_panel_state.selected_profile_id
        return next(
            (
                item
                for item in self._model_profile_panel_state.items
                if item.id == selected_id
            ),
            None,
        )

    def _show_model_profile_dialog(
        self,
        *,
        title: str,
        initial_values: ModelProfileEditorValues,
        current_upper: float,
        current_settings: GenerationSettings,
        active_locked: bool,
        missing_default_reference: bool = False,
    ) -> ModelProfileEditorValues | None:
        state = self._model_profile_panel_state
        dialog = wx.Dialog(self, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        form = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        form.AddGrowableCol(1, 1)

        form.Add(wx.StaticText(dialog, label="表示名"), 0, wx.ALIGN_CENTER_VERTICAL)
        name_ctrl = wx.TextCtrl(dialog, value=initial_values.display_name)
        form.Add(name_ctrl, 1, wx.EXPAND)

        form.Add(wx.StaticText(dialog, label="基準プリセット"), 0, wx.ALIGN_CENTER_VERTICAL)
        preset_labels = [
            f"[{'組み込み' if item.source == 'built_in' else 'ユーザー'}] {item.display_name}"
            for item in state.preset_options
        ]
        preset_ctrl = wx.Choice(dialog, choices=preset_labels)
        preset_ids = tuple(item.id for item in state.preset_options)
        if initial_values.default_preset_id in preset_ids:
            preset_ctrl.SetSelection(preset_ids.index(initial_values.default_preset_id))
        else:
            preset_ctrl.SetSelection(wx.NOT_FOUND)
        form.Add(preset_ctrl, 1, wx.EXPAND)

        form.Add(wx.StaticText(dialog, label="モーフ名セット"), 0, wx.ALIGN_CENTER_VERTICAL)
        morph_ctrl = wx.Choice(dialog, choices=("日本語5母音", "英字5母音"))
        morph_ctrl.SetSelection(
            1 if initial_values.morph_name_set_id == "builtin:latin-vowels" else 0
        )
        form.Add(morph_ctrl, 1, wx.EXPAND)

        upper_override = wx.CheckBox(dialog, label="モーフ最大値を上書き")
        upper_override.SetValue(initial_values.morph_upper_limit is not None)
        upper_ctrl = wx.SpinCtrlDouble(
            dialog,
            min=0.0,
            max=10.0,
            inc=0.05,
        )
        upper_ctrl.SetDigits(2)
        upper_ctrl.SetValue(
            float(
                initial_values.morph_upper_limit
                if initial_values.morph_upper_limit is not None
                else current_upper
            )
        )
        form.Add(upper_override, 0, wx.ALIGN_CENTER_VERTICAL)
        form.Add(upper_ctrl, 1, wx.EXPAND)

        overrides = initial_values.generation_overrides
        hold_override = wx.CheckBox(dialog, label="開口保持を上書き")
        hold_override.SetValue(overrides.closing_hold_frames is not None)
        hold_ctrl = wx.SpinCtrl(
            dialog,
            min=0,
            max=100,
            initial=(
                overrides.closing_hold_frames
                if overrides.closing_hold_frames is not None
                else current_settings.closing_hold_frames
            ),
        )
        form.Add(hold_override, 0, wx.ALIGN_CENTER_VERTICAL)
        form.Add(hold_ctrl, 1, wx.EXPAND)

        softness_override = wx.CheckBox(dialog, label="閉口スムースを上書き")
        softness_override.SetValue(overrides.closing_softness_frames is not None)
        softness_ctrl = wx.SpinCtrl(
            dialog,
            min=0,
            max=100,
            initial=(
                overrides.closing_softness_frames
                if overrides.closing_softness_frames is not None
                else current_settings.closing_softness_frames
            ),
        )
        form.Add(softness_override, 0, wx.ALIGN_CENTER_VERTICAL)
        form.Add(softness_ctrl, 1, wx.EXPAND)

        mode_override = wx.CheckBox(dialog, label="長音モードを上書き")
        mode_override.SetValue(overrides.long_vowel_mode is not None)
        mode_ctrl = wx.Choice(dialog, choices=("hold", "decay"))
        selected_mode = overrides.long_vowel_mode or current_settings.long_vowel_mode
        mode_ctrl.SetSelection(1 if selected_mode == "decay" else 0)
        form.Add(mode_override, 0, wx.ALIGN_CENTER_VERTICAL)
        form.Add(mode_ctrl, 1, wx.EXPAND)

        sizer.Add(form, 1, wx.ALL | wx.EXPAND, 10)
        warning = wx.StaticText(dialog, label="")
        if active_locked:
            warning.SetLabel(
                "適用中のプロファイルは名前だけ変更できます。"
                "設定変更や削除はプロファイルなし、または別profileを適用後に行ってください。"
            )
        elif missing_default_reference:
            warning.SetLabel("参照先プリセットが見つかりません。基準プリセットを選び直してください。")
        warning.Wrap(420)
        sizer.Add(warning, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        dialog.SetSizerAndFit(sizer)
        ok_button = dialog.FindWindowById(wx.ID_OK)

        def update_enabled(event=None):
            enabled = not active_locked
            upper_ctrl.Enable(enabled and upper_override.GetValue())
            hold_ctrl.Enable(enabled and hold_override.GetValue())
            softness_ctrl.Enable(enabled and softness_override.GetValue())
            mode_ctrl.Enable(enabled and mode_override.GetValue())
            preset_ctrl.Enable(enabled)
            morph_ctrl.Enable(enabled)
            if ok_button is not None:
                ok_button.Enable(
                    preset_ctrl.GetSelection() >= 0
                    and morph_ctrl.GetSelection() >= 0
                    and bool(name_ctrl.GetValue().strip())
                )
            if event is not None:
                event.Skip()

        for checkbox in (upper_override, hold_override, softness_override, mode_override):
            checkbox.Bind(wx.EVT_CHECKBOX, update_enabled)
        name_ctrl.Bind(wx.EVT_TEXT, update_enabled)
        preset_ctrl.Bind(wx.EVT_CHOICE, update_enabled)
        morph_ctrl.Bind(wx.EVT_CHOICE, update_enabled)
        update_enabled()
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return None
            preset_index = preset_ctrl.GetSelection()
            morph_index = morph_ctrl.GetSelection()
            if preset_index < 0 or morph_index < 0:
                return None
            return ModelProfileEditorValues(
                display_name=name_ctrl.GetValue(),
                morph_name_set_id=(
                    "builtin:latin-vowels"
                    if morph_index == 1
                    else "builtin:japanese-vowels"
                ),
                morph_upper_limit=(
                    float(upper_ctrl.GetValue())
                    if upper_override.GetValue()
                    else None
                ),
                generation_overrides=ProfileGenerationOverrides(
                    closing_hold_frames=(
                        hold_ctrl.GetValue() if hold_override.GetValue() else None
                    ),
                    closing_softness_frames=(
                        softness_ctrl.GetValue()
                        if softness_override.GetValue()
                        else None
                    ),
                    long_vowel_mode=(
                        "decay" if mode_ctrl.GetSelection() == 1 else "hold"
                    )
                    if mode_override.GetValue()
                    else None,
                ),
                default_preset_id=preset_ids[preset_index],
            )
        finally:
            dialog.Destroy()

    def _on_create_model_profile(self, event) -> None:
        event.Skip()
        state = self._model_profile_panel_state
        if state.busy or not state.mutation_available:
            return
        valid_preset_ids = {item.id for item in state.preset_options}
        preferred_ids = (
            state.active_baseline_preset_id,
            state.active_preset_id,
            "builtin:standard-hold",
        )
        default_preset_id = next(
            (item for item in preferred_ids if item in valid_preset_ids),
            state.preset_options[0].id if state.preset_options else "",
        )
        values = self._show_model_profile_dialog(
            title="モデルプロファイルを作成",
            initial_values=ModelProfileEditorValues(
                display_name="",
                morph_name_set_id=state.active_morph_name_set_id,
                morph_upper_limit=None,
                generation_overrides=ProfileGenerationOverrides(),
                default_preset_id=default_preset_id,
            ),
            current_upper=state.active_morph_upper_limit,
            current_settings=state.active_generation_settings,
            active_locked=False,
        )
        if values is not None and self.on_model_profile_create_callback is not None:
            self.on_model_profile_create_callback(
                ModelProfileCreateRequest(values, state.panel_revision)
            )

    def _on_update_model_profile(self, event) -> None:
        event.Skip()
        state = self._model_profile_panel_state
        item = self._selected_model_profile_item()
        if state.busy or not state.mutation_available or item is None:
            return
        values = self._show_model_profile_dialog(
            title="モデルプロファイルを更新",
            initial_values=ModelProfileEditorValues(
                display_name=item.display_name,
                morph_name_set_id=item.morph_name_set_id,
                morph_upper_limit=item.morph_upper_limit,
                generation_overrides=item.generation_overrides,
                default_preset_id=item.default_preset_id,
            ),
            current_upper=state.active_morph_upper_limit,
            current_settings=state.active_generation_settings,
            active_locked=item.id == state.active_profile_id,
            missing_default_reference=not item.default_preset_available,
        )
        if values is not None and self.on_model_profile_update_callback is not None:
            self.on_model_profile_update_callback(
                ModelProfileUpdateRequest(
                    item.id,
                    values,
                    state.panel_revision,
                    self._selected_event_editor_revision,
                )
            )

    def _on_delete_model_profile(self, event) -> None:
        event.Skip()
        state = self._model_profile_panel_state
        item = self._selected_model_profile_item()
        if (
            state.busy
            or not state.mutation_available
            or item is None
            or item.id == state.active_profile_id
        ):
            return
        if wx.MessageBox(
            f"モデルプロファイル「{item.display_name}」を削除しますか？",
            "モデルプロファイル削除",
            wx.YES_NO | wx.ICON_WARNING,
            self,
        ) != wx.ID_YES:
            return
        callback = self.on_model_profile_delete_callback
        if callback is not None:
            callback(
                ModelProfileDeleteRequest(
                    item.id,
                    state.panel_revision,
                    self._selected_event_editor_revision,
                )
            )

    def refresh_preset_styles(self):
        palette = ThemeManager.get_palette()
        self.st_preset_notice.SetForegroundColour(palette.attention_text)
        self.st_preset_source.SetForegroundColour(palette.muted_text)
        self.st_preset_settings.SetForegroundColour(palette.text_fg)
        self.st_selected_event_mode_notice.SetForegroundColour(palette.attention_text)
        if hasattr(self, "st_model_profile_notice"):
            self.refresh_model_profile_styles()

    def _on_select_preset(self, event):
        event.Skip()
        if self._suppress_preset_events:
            return
        index = self.choice_preset.GetSelection()
        if index < 0 or index >= len(self._preset_selector_ids):
            return
        callback = self.on_preset_select_callback
        if callback is not None:
            callback(
                PresetSelectRequest(
                    self._preset_selector_ids[index],
                    self._preset_panel_state.panel_revision,
                )
            )

    def _on_apply_preset(self, event):
        event.Skip()
        state = self._preset_panel_state
        if state.selected_preset_id is None:
            return
        callback = self.on_preset_apply_callback
        if callback is not None:
            callback(
                PresetApplyRequest(
                    state.selected_preset_id,
                    state.panel_revision,
                    self._selected_event_editor_revision,
                )
            )

    def _show_preset_dialog(
        self,
        *,
        title: str,
        initial_name: str,
        initial_settings: GenerationSettings,
    ):
        dialog = wx.Dialog(self, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        form = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        form.AddGrowableCol(1, 1)
        form.Add(wx.StaticText(dialog, label="表示名"), 0, wx.ALIGN_CENTER_VERTICAL)
        name_ctrl = wx.TextCtrl(dialog, value=initial_name)
        form.Add(name_ctrl, 1, wx.EXPAND)
        form.Add(wx.StaticText(dialog, label="開口保持"), 0, wx.ALIGN_CENTER_VERTICAL)
        hold_ctrl = wx.SpinCtrl(dialog, min=0, max=100, initial=initial_settings.closing_hold_frames)
        form.Add(hold_ctrl, 1, wx.EXPAND)
        form.Add(wx.StaticText(dialog, label="閉口スムーズ"), 0, wx.ALIGN_CENTER_VERTICAL)
        softness_ctrl = wx.SpinCtrl(
            dialog,
            min=0,
            max=100,
            initial=initial_settings.closing_softness_frames,
        )
        form.Add(softness_ctrl, 1, wx.EXPAND)
        form.Add(wx.StaticText(dialog, label="長音モード"), 0, wx.ALIGN_CENTER_VERTICAL)
        mode_ctrl = wx.Choice(dialog, choices=("hold", "decay"))
        mode_ctrl.SetSelection(1 if initial_settings.long_vowel_mode == "decay" else 0)
        form.Add(mode_ctrl, 1, wx.EXPAND)
        sizer.Add(form, 1, wx.ALL | wx.EXPAND, 10)
        buttons = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        dialog.SetSizerAndFit(sizer)
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return None
            try:
                settings = GenerationSettings(
                    closing_hold_frames=hold_ctrl.GetValue(),
                    closing_softness_frames=softness_ctrl.GetValue(),
                    long_vowel_mode=("decay" if mode_ctrl.GetSelection() == 1 else "hold"),
                )
            except (TypeError, ValueError) as error:
                self.set_preset_panel_notice(str(error))
                return None
            return name_ctrl.GetValue(), settings
        finally:
            dialog.Destroy()

    def _on_create_preset(self, event):
        event.Skip()
        state = self._preset_panel_state
        if state.busy or not state.mutation_available:
            return
        values = self._show_preset_dialog(
            title="ユーザープリセットを作成",
            initial_name="",
            initial_settings=state.active_generation_settings,
        )
        if values is None:
            return
        callback = self.on_preset_create_callback
        if callback is not None:
            callback(PresetCreateRequest(values[0], values[1], state.panel_revision))

    def _selected_preset_item(self):
        selected_id = self._preset_panel_state.selected_preset_id
        return next(
            (item for item in self._preset_panel_state.items if item.id == selected_id),
            None,
        )

    def _on_update_preset(self, event):
        event.Skip()
        state = self._preset_panel_state
        item = self._selected_preset_item()
        if state.busy or not state.mutation_available or item is None or item.source != "user":
            return
        values = self._show_preset_dialog(
            title="ユーザープリセットを更新",
            initial_name=item.display_name,
            initial_settings=item.generation_settings,
        )
        if values is None:
            return
        callback = self.on_preset_update_callback
        if callback is not None:
            callback(
                PresetUpdateRequest(
                    item.id,
                    values[0],
                    values[1],
                    state.panel_revision,
                    self._selected_event_editor_revision,
                )
            )

    def _on_delete_preset(self, event):
        event.Skip()
        state = self._preset_panel_state
        item = self._selected_preset_item()
        if state.busy or not state.mutation_available or item is None or item.source != "user":
            return
        if wx.MessageBox(
            f"ユーザープリセット「{item.display_name}」を削除しますか？",
            "プリセット削除",
            wx.YES_NO | wx.ICON_WARNING,
            self,
        ) != wx.YES:
            return
        callback = self.on_preset_delete_callback
        if callback is not None:
            callback(
                PresetDeleteRequest(
                    item.id,
                    state.panel_revision,
                    self._selected_event_editor_revision,
                )
            )

    def set_preset_summary(self, text: str):
        self.st_preset.SetLabel(text)
        self._update_wrap()

    def clear_preset_summary(self):
        self.set_preset_summary("プリセット機能は後続マイルストーンで対応予定です。")

    def set_model_profile_summary(self, text: str):
        self.st_model_profile.SetLabel(text)
        self._update_wrap()

    def clear_model_profile_summary(self):
        self.set_model_profile_summary("モデルプロファイル機能は後続マイルストーンで対応予定です。")

    def _update_wrap(self):
        # View Helperから呼ばれた際の再描画
        width = self.GetClientSize().width - 20
        info_width = self.panel_info.GetClientSize().width - 10
        if info_width > 0:
            self.st_info.Wrap(info_width)
            self.st_info_suffix.Wrap(info_width)
            self.st_playback_context.Wrap(info_width)
            self.panel_info.Layout()
            self.panel_info.FitInside()
            self.panel_info.Refresh()
        if width > 0:
            for _, summary_label, detail_label in self._warning_rows:
                summary_label.Wrap(width)
                if detail_label is not None:
                    detail_label.Wrap(width)
            self.st_selected_event.Wrap(width)
            self.st_selected_event_header.Wrap(width)
            self.st_selected_event_validation.Wrap(width)
            self.st_selected_event_notice.Wrap(width)
            self.st_selected_event_mode_notice.Wrap(width)
            self.st_selected_event_effect_notice_header.Wrap(width)
            self.st_selected_event_effect_notice_details.Wrap(width)
            self.st_selected_event_crossfade_notice_header.Wrap(width)
            self.st_selected_event_crossfade_notice_details.Wrap(width)
            self.st_selected_event_slope_helper.Wrap(width)
            self.st_preset_active.Wrap(width)
            self.st_preset_source.Wrap(width)
            self.st_preset_settings.Wrap(width)
            self.st_preset_notice.Wrap(width)
            self.st_preset.Wrap(width)
            self.st_model_profile.Wrap(width)
            self.st_whisper_model_active.Wrap(width)
            self.st_whisper_model_selected.Wrap(width)
            self.st_whisper_model_storage.Wrap(width)
            self.st_whisper_model_scan.Wrap(width)
            self.st_whisper_model_explanation.Wrap(width)
            self.st_whisper_model_management.Wrap(width)
            self.st_whisper_model_details.Wrap(width)
            self.st_whisper_model_notice.Wrap(width)
            self.panel_warning.Layout()
            self.panel_warning.FitInside()
            self.panel_selected_event.Layout()
            self.panel_selected_event.FitInside()
            self.panel_preset.Layout()
            self.panel_preset.FitInside()
            self.panel_model_profile.Layout()
            self.panel_whisper_model.Layout()
