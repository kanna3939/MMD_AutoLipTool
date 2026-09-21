# MS23-B4 Implementation Plan

## 1. 文書情報

- 対象: MS23-B4 Resolution / State / Diagnostics
- 作成日: 2026-08-17
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時branch: `feature/MS23-implementation`
- 計画作成時HEAD: `3d9f936 Implement MS23-B3 model profile persistence`
- 実装開始時HEAD: `005c57b Document MS23-B4 implementation plan`
- 依存: MS22-B7 Closeout A、MS23-B1 Completed / Contract Fixed、MS23-B2 Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report)、MS23-B3 Implemented / Automated Verification Passed / Manual GUI Not Required
- 文書ステータス: Implemented / Automated Verification Complete / Manual GUI Deferred to B5 / Actual-MMD Verification Deferred to MS26
- 計画策定時の権限: planning documentだけを変更し、production code、test code、GUI、runtime user dataを変更しない

B1で採用済みのD1〜D7、S1〜S7を本planの正本契約とする。B4で新たなmaterial decisionは追加しない。B1で実装詳細へ委譲されたexact class名、resolution status、error code、history projection、startup ID補正保存の接続方法を本planで固定する。

2026-08-17のplan reviewではP1なし、P2 5件、P3 1件を確認した。P2は、profile-aware Undo / Redo後のINI保存要求、active profile下のhistory初期endpoint、startup identity-only saveとfull saveのpending優先順位、mutation guard codeの競合優先順位、resolution DTO / APIのexact field・型・不変条件である。P3は、store mutation preflight時のpending coalescingをlive historyではなくlocal immutable candidate上でsettleすることの明文化である。本改訂で推奨案を反映した。その後のfresh read-only再チェックでは、B1 / B3のstrict float・0.0〜10.0契約に対して`ResolvedModelProfile.morph_upper_limit`の型・上限記載が不足しているP2を1件確認した。ユーザー採用の推奨修正として、strict float、有限、0.0〜10.0、bool / int / string拒否を本planへ反映した。2026-08-18にB4を実装し、専用state / resolver、startup、history、guard、pipeline / Preview / diagnostics / report接続の自動検証を完了した。profile UIの手動確認はB5、実MMD確認はMS26へdeferredとする。

## 2. 背景

MS23-B2は、日本語・英字のbuilt-in morph-name setと、writer / Preview / diagnosticsが明示的なordered output namesを受けるprimitive境界を実装した。MS23-B3は、strict schema v1の`profiles.json`、`ModelProfileStore`、INIの`active_model_profile_id` / `active_profile_baseline_preset_id`を実装した。

現行runtimeは、`GenerationState`がgeneration settingsとactive preset IDだけを保持し、`AppController.load_startup_state()`がSettingsStoreとPresetStoreだけを解決している。VMD保存は`AppController`から`src/core/pipeline.py`を経由し、PreviewとdiagnosticsはMainFrameから別々にadapterを呼ぶ。ここへprofile precedenceをconsumerごとに追加すると、profile override、runtime baseline、morph-name set、fingerprintが分岐する。

B4では、cross-store resolutionをUI非依存coreで一度だけ行い、base-independent profile state、analysis parameter、output projection、base-bound historyを分離したままruntimeへ統合する。RightPaneのprofile selector / editorはB5に残すが、B5が独自resolverやmutation guardを実装しなくて済むcontroller APIまでをB4で用意する。

## 3. 目的

1. profile、runtime baseline preset、application settingをimmutableに解決し、D1のprecedenceを一箇所へ固定する。
2. active profile ID、runtime baseline ID、resolution statusを専用stateへ置き、resolved morph-name set IDを`GenerationState`へ追加する。
3. profile Apply、no-profile Apply、active profile中の別preset Applyを、upper-limit差分とoutput差分に応じて既存analysis / history契約へ接続する。
4. D2 / D3 / D6 / D7のmutation・direct-edit guardをstore commit前へ置き、拒否時の完全不変を保証する。
5. startup fallback、IDだけの補正保存、workspace reset、analysis rollback、Undo / Redoをprofile-awareにする。
6. writer、Preview、Info、diagnostic reportへ同じresolved morph-name setを渡し、fingerprint schemaを変えず実出力名だけをidentityへ反映する。
7. 既存日本語default、preset単独Custom、VMD形式、30fps、audio、wx lifecycle、save-disabled契約を維持する。

## 4. In Scope

- UI非依存のprofile resolution DTO、status、reason、structured result
- startup / explicit profile Apply / no-profile Apply / active-profile preset Apply resolver
- `GenerationState.resolved_morph_name_set_id`
- `UiState.model_profile_state`と`UiState.resolved_morph_upper_limit`
- profile-aware output history endpointとatomic Undo / Redo
- historical endpointがstore mutation後に解決不能となる場合のatomic compaction
- output-only Apply、identity-only reconciliation、upper-limit変更時のanalysis invalidation
- profile / preset cross-store mutation guard
- active profile中のglobal generation / upper-limit direct-edit guard
- SettingsStore / PresetStore / ProfileStoreのstartup一括解決と同一path注入
- startup identity補正だけを行うpartial INI save
- writer pipeline、Preview empty / clear、diagnostics / reportへのresolved output-name伝播
- fallback reasonを含むstructured diagnostics
- workspace reset、analysis failure / cancel / rollback、stale worker、save failure回帰
- B4専用test、既存MS20〜MS23回帰、full suite、compileall、diff check
- 実装後のBlock Breakdown、Index、Roadmapへの状態同期

## 5. Out of Scope

- RightPane「モデルプロファイル」tabのselector、Apply button、Create / Update / Delete dialog
- profile候補選択state、expected revision、Busy表示、panel noticeのB5 UI実装
- PMX / PMD読込、モデルファイル解析、任意morph mapping、user-defined morph-name set、追加表情morph
- profile schema、上限、atomic persistenceの変更
- built-in morph-name setの追加、mapping変更、英語音声認識・英語音素処理
- event adjustment field / precedenceの変更
- fingerprint payload構造または`ms21-effective-output-v1`の変更
- MS24 Whisperモデル選択、MS25一括出力、MS26実MMD確認、MS27 packaging / release readiness
- Qt / PySide6、外部クラウドASR、外部音声送信、background通信、Whisper自動download
- dependency、license、build、PyInstaller、VMD形式、30fps、audio role / limitの変更
- repository rootの`profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`の作成・変更・stage
- commit、push、merge、tag、release、branch削除

## 6. 前提条件

- 計画開始時のbranchは`feature/MS23-implementation`、HEADは`3d9f936`、worktreeはcleanであった。実装開始時HEADは文書情報の`005c57b`である。
- MS22 Closeout Aを未完了へ戻さず、実MMD未確認はMS26へdeferredのままとする。
- `ModelProfileStore`は明示`load()`後のimmutable tuple、lookup、structured mutation resultを提供し、cross-store lookupとguardはB4 Controller / core resolverが所有する。
- `GenerationPresetStore`はbuilt-in / user presetとexact-settingsのactive preset resolverを提供する。
- `MorphNameSet`の正本は`src/core/morph_name_sets.py`であり、B4でID別display-name表を複製しない。
- writer / Preview / diagnosticsのB2 APIは明示ordered output-name tupleを受け、省略時は日本語defaultを維持する。
- output historyは最大50件、analysis base-bound、commit-before failureは完全不変、commit後INI save failureはin-memory commitをrollbackしない。
- B4実装開始前に本planのレビューとfresh read-only pre-implementation checkを通過済みである。

## 7. 対象ファイル

### 7.1 production code変更対象

| ファイル | B4で担当する責務 |
|---|---|
| 新規 `src/core/model_profile_state.py` | immutable profile state、resolved DTO、startup / Apply resolver、mutation guard result |
| `src/core/output_edit_state.py` | `GenerationState`へのresolved morph-name set ID追加とvalidation |
| `src/core/event_adjustment_history.py` | profile-aware endpoint、identity-only transaction、Undo / Redo、store mutation後のatomic normalization / compaction |
| `src/gui_wx/ui_state.py` | profile state、resolved upper limit、historyとのatomic同期、reset保持 |
| `src/gui_wx/app_controller.py` | 3 store注入、startup resolution、partial identity save、Apply API、mutation guard、writer入力 |
| `src/gui_wx/app.py` | `ModelProfileStore`注入seamとstartup resolved stateのMainFrame投影 |
| `src/gui_wx/main_frame.py` | unified resolved-state commit、direct-edit guard、Preview / diagnosticsへのresolved names投影 |
| `src/gui_wx/analysis_rollback.py` | profile state consistency tokenを持つrollback guard |
| `src/core/pipeline.py` | TEXTあり / voice-onlyの両VMD経路へexplicit output namesを追加 |
| `src/gui_wx/preview_panel.py` | placeholder / clearでもexplicit output namesを保持 |
| `src/gui_wx/placeholder_panels.py` | MainFrameからPreview clearへのoutput-name伝播 |
| `src/core/output_diagnostics.py` | profile / baseline / morph set / fallbackのstructured summary |
| `src/gui_wx/output_diagnostics_adapter.py` | resolved stateからdiagnostics DTOを構築 |
| `src/core/diagnostic_report.py` | 同じsummaryからprofile情報をreportへ出力 |

### 7.2 変更せず直接回帰する境界

- `src/core/model_profiles.py`: B3 persistence正本。B4都合でschemaやraw storeを変更しない。
- `src/core/generation_presets.py`: preset単独resolverとJSON contractを変更しない。
- `src/core/morph_name_sets.py`: B2 registry / display name / mappingを再実装しない。
- `src/vmd_writer/effective_shape_adapter.py`: 既存explicit mapping APIを利用する。
- `src/vmd_writer/writer.py`: B2のprimitive allow-list、日本語default、final normalize-before-mapを維持する。
- `src/core/preview_transform.py`: 既存explicit output namesをMainFrameから渡す。
- `src/gui_wx/ui_sync_context.py`: semantic effective planはmorph-name setに依存しないためidentityへset IDを混ぜない。
- `src/core/settings_store.py`: B3で追加済みのINI keyとpartial mergeを利用し、schemaを追加しない。
- `src/core/__init__.py`: consumerはleaf moduleをimportし、B4でもpackage root exportを必須にしない。
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、license文書: 変更しない。

### 7.3 test対象

- 新規 `tests/test_ms23_b4_model_profile_state.py`
- 新規 `tests/test_ms23_b4_profile_history.py`
- 新規 `tests/test_wx_ms23_b4_profile_runtime.py`
- 既存B2 / B3、generation history / state、preset UI、rollback、workspace reset、pipeline / writer、diagnostics / report、lifecycle test

### 7.4 文書変更対象

- `docs/Implementation_Plan/MS23-B4_Implementation_Plan.md`
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

## 8. 実装方針

### 8.1 core stateとexact status

`src/core/model_profile_state.py`へ次を定義する。

- `ModelProfileResolutionStatus(str, Enum)`
  - `NO_PROFILE = "no_profile"`
  - `RESOLVED = "resolved"`
  - `FALLBACK_PROFILE_DEFAULT = "fallback_profile_default"`
  - `FALLBACK_NO_PROFILE = "fallback_no_profile"`
- `ModelProfileState`
  - `active_model_profile_id: str | None`
  - `active_profile_baseline_preset_id: str | None`
  - `resolution_status: ModelProfileResolutionStatus`
  - `resolution_reason_code: str | None`
- `ResolvedModelProfile`
  - `model_profile_state: ModelProfileState`
  - `generation_settings: GenerationSettings`
  - `morph_upper_limit: float`
  - `morph_name_set: MorphNameSet`
  - `active_preset_id: str | None`
  - `active_preset_display_name: str | None`
  - `active_profile_display_name: str | None`
  - `baseline_preset_display_name: str | None`
- `ModelProfileResolutionResult`
  - `resolution: ResolvedModelProfile | None`
  - `error_code: str | None`
  - `error_message: str | None`
- `StartupModelProfileResolution`
  - `resolution: ResolvedModelProfile`
  - `identity_correction_required: bool`
  - `active_preset_id: str | None`
  - `active_model_profile_id: str | None`
  - `active_profile_baseline_preset_id: str | None`
- `RuntimeMutationGuardResult`
  - `allowed: bool`
  - `error_code: str | None`
  - `error_message: str | None`

`NO_PROFILE`はprofile / baseline IDとreasonをすべて`None`、`RESOLVED`は両ID必須かつreasonを`None`とする。`FALLBACK_PROFILE_DEFAULT`は両IDと`runtime_baseline_preset_not_found` reasonを必須とする。`FALLBACK_NO_PROFILE`は両IDとも`None`とし、reasonを`profile_store_unavailable / orphan_profile_baseline / active_profile_not_found / profile_default_preset_not_found`のいずれかに限定する。status / reasonはruntime diagnostics用で、INIや`profiles.json`へ保存しない。

`ResolvedModelProfile`は、no-profile時だけprofile / baseline display nameを`None`とし、active profile時は両display nameを必須とする。`active_preset_id`と`active_preset_display_name`は常にpairであり、active profile時は両方`None`とする。`morph_upper_limit`は`type(value) is float`を満たす有限値で、`0.0 <= value <= 10.0`だけを受理し、bool / int / stringを拒否する。resolverへ渡すapplication / current upperも同じ正規化済みstrict float契約を満たすことを検証する。`morph_name_set`はB2 registryのbuilt-in objectだけを受理する。

`ModelProfileResolutionResult`は、成功時に`resolution`だけを持ちerror pairを`None`、失敗時に`resolution=None`とnon-empty error pairを持つ。`StartupModelProfileResolution`は常にresolutionを持ち、補正後profile / baseline IDは`resolution.model_profile_state`と一致し、補正後active preset IDは`resolution.active_preset_id`と一致する。`RuntimeMutationGuardResult`は、`allowed=True`ならerror pairを`None`、`allowed=False`ならnon-empty error pairを必須とする。

### 8.2 fixed reason / error code

startup resolution reasonを次に固定する。

- `profile_store_unavailable`
- `orphan_profile_baseline`
- `active_profile_not_found`
- `profile_default_preset_not_found`
- `runtime_baseline_preset_not_found`

explicit resolution / guard errorを次に固定する。

- `profile_store_unavailable`
- `profile_not_found`
- `profile_default_preset_not_found`
- `preset_not_found`
- `preset_reference_not_found`
- `active_profile_locked`
- `active_profile_baseline_locked`
- `preset_referenced_by_profile`
- `profile_reference_check_unavailable`
- `active_profile_direct_edit_locked`

同じ原因をUI側で別文字列codeへ変換しない。B5はこのcodeを日本語noticeへ投影する。

### 8.3 resolver APIとprecedence

public pure function名、keyword-only引数、戻り値を次に固定する。`profiles`はload済み`ModelProfile` tuple、`presets`はbuilt-inとuserを結合したload済み`GenerationPreset` tupleであり、resolver内でstore I/Oを行わない。

```python
def resolve_startup_model_profile(
    *,
    application_generation_settings: GenerationSettings,
    application_morph_upper_limit: float,
    raw_active_preset_id: str | None,
    raw_active_model_profile_id: str | None,
    raw_active_profile_baseline_preset_id: str | None,
    profile_load_result: ProfileLoadResult,
    preset_load_result: PresetLoadResult,
) -> StartupModelProfileResolution: ...

def resolve_model_profile_apply(
    *,
    requested_profile_id: str,
    application_morph_upper_limit: float,
    profiles: tuple[ModelProfile, ...],
    presets: tuple[GenerationPreset, ...],
) -> ModelProfileResolutionResult: ...

def resolve_active_profile_preset_apply(
    *,
    requested_preset_id: str,
    current_model_profile_state: ModelProfileState,
    application_morph_upper_limit: float,
    profiles: tuple[ModelProfile, ...],
    presets: tuple[GenerationPreset, ...],
) -> ModelProfileResolutionResult: ...

def resolve_no_profile(
    *,
    current_generation_settings: GenerationSettings,
    current_morph_upper_limit: float,
    presets: tuple[GenerationPreset, ...],
) -> ModelProfileResolutionResult: ...

def validate_model_profile_mutation(
    *,
    operation: Literal["create", "update", "delete"],
    target_profile_id: str | None,
    candidate_profile: ModelProfile | None,
    current_model_profile_state: ModelProfileState,
    profile_load_result: ProfileLoadResult,
    preset_load_result: PresetLoadResult,
) -> RuntimeMutationGuardResult: ...

def validate_generation_preset_mutation(
    *,
    operation: Literal["update", "delete"],
    target_preset_id: str,
    candidate_preset: GenerationPreset | None,
    current_model_profile_state: ModelProfileState,
    profile_load_result: ProfileLoadResult,
    preset_load_result: PresetLoadResult,
) -> RuntimeMutationGuardResult: ...
```

startup resolverはnormalized INI numeric / ID値、`ProfileLoadResult`、`PresetLoadResult`を一回の入力として受け、profile store unavailableとvalid empty collectionを区別する。explicit Apply resolverはcurrent application upper、requested stable ID、load済みimmutable tupleを受ける。mutation validatorはcandidate DTOとload resultだけを受け、storeを変更せず、history moduleをimportしない。model profile Createでは`target_profile_id=None`かつcandidate必須、Updateではcandidate IDとtarget IDの一致必須、Deleteではcandidateを`None`とする。preset Updateではcandidate IDとtarget IDの一致必須、Deleteではcandidateを`None`とする。上記以外の組合せはB4 guard codeへ変換せず`TypeError`またはcontract errorとして拒否する。

resolution順序はfield単位に次で固定する。

```text
generation settings:
  referenced/runtime preset
    -> profile non-null override
      -> event adjustment（effective shape resolver側）

morph_upper_limit:
  current application / INI value
    -> profile non-null override

morph-name set:
  Japanese application default
    -> active profile required set
```

profile Applyは`default_preset_id`をbaselineへ設定する。active profile中の別preset Applyはactive profile IDを維持し、baseline IDだけを置換する。active profile中は`GenerationState.active_preset_id=None`とし、profile override付きeffective settingsを既存preset resolverへ渡してCustom化しない。

no-profile Applyはgeneration settingsとupper limitを現在値のまま保持し、morph-name setをJapaneseへ戻し、baseline IDをclearする。active preset IDは既存`resolve_active()`のexact-settings規則で再計算する。

### 8.4 startup matrixとidentity-only save

- profile store unavailable、active profile不明、default preset不明では、INI numeric settingsをin-memoryでも保持したno-profile + Japaneseへfallbackする。
- active profileがvalidでruntime baselineだけがmissing / unknownなら、profile default presetをbaselineとしてprofile overrideを再解決する。
- active profileなしでbaseline IDだけがある場合はorphanとしてbaselineをclearする。
- active profileが解決された場合は`active_preset_id=None`へ正規化する。
- raw IDと補正後IDに差がある場合だけ`identity_correction_required=True`とする。

startup補正保存は通常のfull settings saveと分離する。`AppController`は`_pending_settings_save_kind: Literal["none", "identity_only", "full"]`を持ち、優先順位を`full > identity_only > none`に固定する。

- startup補正は`request_startup_identity_correction_save()`で`none -> identity_only`だけを行い、既に`full`ならdowngradeしない。
- 通常の`request_settings_save()`はpending kindを必ず`full`へ昇格する。
- identity correctionだけがpendingのflushでは、補正後`active_preset_id`、`active_model_profile_id`、`active_profile_baseline_preset_id`の3 ID keyだけを`SettingsStore.save()`へ渡し、morph upper / generation numeric keyを送らない。
- timer発火前にfull saveが要求された場合はidentity-only payloadを別送せず、flush時点のcurrent UiStateからfull payloadを一回だけ保存する。
- full pending後にstartup identity-only要求が来てもfullを維持する。同種要求の反復は一回へcoalesceする。
- close flushも同じpriorityとpayload規則を使う。保存失敗時は既存の初回通知と`save_disabled`を維持し、partial / fullのどちらもin-memory state / historyをrollbackしない。

これにより、fallback時の「補正後IDだけ保存しnumeric settingsを保持する」S7と、後続の実ユーザー操作時にcurrent stateをfull saveする契約を両立する。

### 8.5 runtime ownership

- `GenerationState`へ`resolved_morph_name_set_id`を末尾default付きで追加し、既存2引数constructorを壊さない。defaultは`builtin:japanese-vowels`とする。
- `UiState.model_profile_state`のdefaultは`NO_PROFILE`、ID / reasonなしとする。
- `UiState.resolved_morph_upper_limit`をcurrent analysis parameterの正本とし、controlはprojectionとする。
- `AnalysisParameterSnapshot`は引き続きupper limitだけを保持する。
- `OutputEditState`はprofile IDを直接持たず、GenerationStateを通じてresolved generation settings / set IDだけを持つ。
- workspace resetは上記3 stateをclearしない。

### 8.6 unified commit classification

MainFrameへresolved resultを受ける一つのcommit経路を置き、commit前に次を比較する。

| 差分 | commit |
|---|---|
| 全resolved値・identityとも同一 | exact no-op、saveなし |
| upper不変、output / profile identity差分、valid baseあり | profile-aware output history transaction |
| upper不変、baseなし | base-independent stateを一括置換、historyなし |
| upper差分あり | state / control投影後にaudio job無効化、analysis invalidation、base-bound history clear |

output differenceにはgeneration settingsとmorph-name set IDを含む。profile ID / baseline IDだけが変わるidentity reconciliationも、valid baseがある場合はprofile-aware transactionとしてUndo / Redo対象にする。analysisを無効化するupper差分transactionはoutput historyへ入れない。

candidate resolution、effective plan構築、history validationまでに失敗した場合はstate、control、history、store、INI save requestを完全不変にする。commit成功後のINI save failureはstate / historyをrollbackしない。

### 8.7 profile-aware history

既存`OutputEditState`へprofile IDを追加せず、history endpointへoptional contextを追加する。

- `OutputEditHistoryState.current_model_profile_state`
- `OutputEditHistoryTransaction.before_model_profile_state / after_model_profile_state`
- `PendingOutputEditHistoryEdit.before_model_profile_state / after_model_profile_state`

既存callerのdefaultは`None`とし、MS22のprofile非対応testとconstructor互換を維持する。`initialize_output_edit_history(...)`とUiState側の`initialize_output_edit_history_state(...)` / `initialize_adjustment_history(...)`へkeyword-only `model_profile_state: ModelProfileState | None = None`を追加する。analysis開始前からactive profileがあるB4 runtimeでは、history初期化時に必ずcurrent `UiState.model_profile_state`を渡し、最初のevent adjustment Undoでprofileが`None`へ落ちないようにする。

profileを一度も利用していない既存no-profile callerは`None`のままとする。active profileまたはprofile transitionを一度含んだchainでは、no-profile endpointもprofile / baseline IDとreasonが`None`、statusが`NO_PROFILE`のexplicit `ModelProfileState`としてcarryし、通常のevent adjustment / generation transactionもcurrent profile contextを維持する。transactionはoutput stateまたはprofile stateの少なくとも一方が変われば成立する。

Undo / RedoはOutputEditState、GenerationState、ModelProfileStateを一括置換する。上限50件、coalescing、redo discard、base identity、legacy adjustment-history projectionを変更しない。

履歴移動前後で、`ModelProfileState.active_model_profile_id`、`ModelProfileState.active_profile_baseline_preset_id`、`GenerationState.generation_settings`、`GenerationState.active_preset_id`から成るpersistent projectionを比較する。runtimeだけのresolution status / reasonはINI projectionへ含めない。profile / baseline / generation / active preset identityが変わったUndo / Redoだけ、移動成功後に通常のfull settings saveを一回要求する。event adjustmentだけが変わりpersistent projectionが同一ならsaveを要求しない。save failureはcommit後failureであり、復元済みstate / historyをrollbackしない。この規則はMS22-B4の非no-op Undo / Redo後INI保存契約を継承するもので、MS22 Closeout判定を変更しない。

### 8.8 store mutation後のhistory normalization

inactive profileや非current presetのUpdate / Deleteはcurrent outputを変更しない一方、過去endpointを解決不能にし得る。raw store mutation前にcandidate profile / preset tupleを構築し、current / undo / redo endpointをcandidate collectionへ再照合したnormalized-history candidateを完成させる。

history側のpublic function名を`normalize_profile_aware_output_edit_history_state(...)`に固定する。`src/core/event_adjustment_history.py`が`ModelProfileState`をimportし、このfunctionはcontrollerから渡されたcandidate-collection resolver callbackでendpointを評価する。`src/core/model_profile_state.py`からhistory moduleをimportせず、循環依存を作らない。

- no-profile endpointのactive preset mismatchは既存どおりCustomへ正規化する。
- active profile endpointはprofile ID、baseline preset ID、stored GenerationState / set IDが現在のresolutionと一致する場合だけ維持する。
- historical endpointだけがmissing / mismatchの場合、別baselineへ黙って置換せず、そのendpointを除外して残る隣接endpointからtransaction chainを再構築する。
- current endpointが解決不能なcandidate mutationはD3 / D6 guardでraw store commit前に拒否する。
- exact no-op transactionを除去し、current state、最大50件、redo順序を維持する。

preflight前に、pure `finish_current_output_edit_coalescing()`をlive `UiState`ではなくlocal immutable history candidateへ適用し、確定済みcurrent endpointを基準にする。UiStateのmutating wrapperはraw store成功前に呼ばない。preflight成功後にだけraw store mutationを実行し、store成功時だけsettled / normalized済みhistory candidateをUiStateへ一括反映する。guard拒否、preflight failure、store write / replace failureではcandidateを破棄し、live historyはpending editを含め完全不変とする。store result tupleがpreflight candidateと一致しない場合もhistoryを変更せずcontract failureとして扱い、silent reconciliationを行わない。

### 8.9 mutation guard

- profile Create / inactive Updateではcandidate `default_preset_id`の参照先をcommit前に確認する。missingなら`preset_reference_not_found`で拒否する。
- active profile Updateは、display name以外の全fieldがexact一致するRenameだけ許可する。value、set、default reference変更は`active_profile_locked`とする。
- active profile Deleteは`active_profile_locked`とする。
- active runtime baseline user preset Updateはgeneration settings exact一致のRenameだけ許可し、value変更は`active_profile_baseline_locked`とする。
- active runtime baseline preset Deleteは`active_profile_baseline_locked`とする。
- 1件でもprofileの`default_preset_id`から参照されるuser preset Deleteは`preset_referenced_by_profile`とする。
- profile store unavailable時は参照不在を証明できないため、user preset Deleteを`profile_reference_check_unavailable`でfail closedにする。preset Applyとbuilt-in利用は停止しない。
- active profile中のglobal generation / upper direct editはexact no-opだけを受理し、non-no-opは`active_profile_direct_edit_locked`としてcontrolをcurrent projectionへ戻す。
- guard拒否ではJSON、INI、state、history、fingerprint、save requestを変更しない。

同一要求で複数のfailure候補が成立する場合のcode決定順を次に固定する。

1. B3 / MS22のcandidate DTO構造、mutation対象storeのload / mutation availability、target ID形式・存在、built-in read-onlyなど、raw storeを変更せず判定可能な既存precondition errorを先に返す。preset mutation時のprofile store unavailableは対象store preconditionではなく、active baseline lock判定後のreference check failureとして第3項で扱う。既存codeをB4 codeへ置換しない。
2. valid targetに対する`active_profile_locked`または`active_profile_baseline_locked`を返す。
3. active lockがなく、user preset Deleteでprofile reference collectionを信頼できない場合は`profile_reference_check_unavailable`を返す。
4. reference check可能で1件以上から参照中なら`preset_referenced_by_profile`を返す。
5. profile Create / inactive Updateのvalid candidateでdefault referenceだけがmissingなら`preset_reference_not_found`を返す。
6. guard通過後にraw storeが返すduplicate、limit、write / replace failureは既存B3 / MS22 codeをそのまま返す。

したがって、active runtime baselineかつprofile参照中のpreset Deleteは`active_profile_baseline_locked`、active runtime baselineかつprofile store unavailableでも`active_profile_baseline_locked`、非active presetかつprofile store unavailableは`profile_reference_check_unavailable`、非activeかつ参照中は`preset_referenced_by_profile`となる。active profile Updateのnon-Renameはcandidate default referenceもmissingであっても`active_profile_locked`とする。settings exact一致Renameがduplicate display nameになる場合はguardを通過後、storeの`duplicate_display_name`を返す。

profile CreateはController側でcanonical candidate IDを一度生成し、同じIDを`validate_model_profile_mutation()`のcandidateと`ModelProfileStore.create(profile_id=...)`へ渡す。Updateもcandidate IDとtarget IDを一致させる。これにより、preflight candidateとstore resultのidentityを偶然の再生成へ依存させない。

Controllerはguard failureを既存`ProfileMutationResult` / `PresetMutationResult`へ同じerror codeのまま投影し、current immutable tupleとmutation availabilityを返す。DTO構造validation、duplicate、limit、write / replace failureはB3 / MS22 storeの既存error codeを維持し、B4 guard codeへ置換しない。

### 8.10 Preview / writer / diagnosticsの同一set

MainFrameは`GenerationState.resolved_morph_name_set_id`をB2 registryで一度解決し、その`output_names`を次へ明示的に渡す。

- `build_preview_data_from_effective_shape_plan()`
- Preview placeholder / clear
- `build_output_diagnostics_snapshot_from_ui_state()`
- `generate_vmd_from_text_wav()` / `generate_vmd_from_timing_plan()`

`src/core/pipeline.py`は両public APIへdefault付き`output_morph_names`を追加し、legacy timeline writerとeffective-shape writerの双方で`write_morph_vmd()` / adapter / `write_morph_frames_vmd()`へ同じtupleを渡す。既存引数省略時は日本語defaultとする。

Preview placeholder、analysis invalidation、workspace reset、error表示で`PreviewModel.clear()`を呼ぶ場合もcurrent resolved namesを渡し、Latin profile中に空状態だけ日本語rowへ戻さない。

### 8.11 diagnostics / report / fingerprint

`DiagnosticSnapshotInput`と`GenerationDiagnosticsSummary`へdefault付きで次をadditiveに追加する。

- active profile ID / display name
- runtime baseline preset ID / display name
- morph-name set ID / display name
- profile resolution status / reason code

既存caller用defaultは、profile / baseline ID・display name・reasonを`None`、morph-name setを`builtin:japanese-vowels` / `日本語5母音`、statusを`no_profile`とする。

ID / display-name pair、profile / baseline組、status / reason、morph set registry一致をDTOで検証する。display nameはprofile / preset store、set名は`MorphNameSet.display_name`から取得する。

Infoとdiagnostic reportは同じsummaryから表示する。fallback reasonは構造化codeを保持し、format時だけ日本語または英語labelへ変換する。これらの説明identityをcanonical fingerprint payloadへ追加しない。Japanese / Latin差分は`EffectiveWriterInput.morph_frames`のmapped nameだけでfingerprintへ反映し、schemaは`ms21-effective-output-v1`のままとする。

### 8.12 lifecycle / rollback

- `AutoLipToolApp`はSettingsStore、PresetStore、ProfileStoreを同じsettings pathでControllerへ渡す。constructorではI/Oしない。
- startupは3 storeを一回ずつloadし、resolved stateをMainFrameへ一括投影する。
- profile Apply / no-profile Apply / preset ApplyはBusy中に拒否する。
- upper差分Applyはcurrent audio / analysis jobを無効化し、late resultをdiscardする。
- output-only Applyはsemantic base / analysisを再利用する。
- `AnalysisRollbackSnapshot`へModelProfileState consistency tokenを追加し、capture時とrestore時のprofile stateが一致する場合だけrollbackする。通常経路ではprofile stateをrollback対象として変更しない。
- analysis failure / cancel、workspace reset、playback、diagnostic clearはactive profile / baseline / resolved settings / set / upperを保持する。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- live Git、B1 / B3 plan、Block Breakdown、Index、Roadmap、関連code / testをfresh read-onlyで再確認する。
- P1 / P2 / P3なし、または指摘解消済みを着手条件とする。
- root runtime user dataとpre-existing diffを記録し、scope外変更を取り込まない。

### Step 2: core resolution DTO

- exact status / reason / error codeとfrozen DTOを追加する。
- preset / profile / morph setのimmutable collectionを入力にし、file I/OやGUI参照を持たないresolverを実装する。
- startup、profile Apply、profile中preset Apply、no-profileを個別public functionで固定する。

### Step 3: GenerationState / UiState ownership

- GenerationStateへset ID defaultをadditiveに追加する。
- UiStateへprofile stateとresolved upper limitを追加し、control / save / analysis snapshotの参照元を正規化する。
- resetが新stateを保持する回帰を追加する。

### Step 4: profile-aware history

- history state / transaction / pending editへoptional profile contextを追加する。
- active profile下でanalysisを開始した場合はhistory初期endpointへcurrent profile stateを渡し、以後のevent adjustmentを含む全endpointでcontextをcarryする。
- output-only、identity-only、coalescing、Undo / Redo、redo discard、50件上限を検証する。
- profile / baseline / generation identityが変わるUndo / Redo後だけfull settings saveを要求し、event-only navigationでは要求しない。
- store mutation後のendpoint normalize / compactを追加する。

### Step 5: startup integration

- App / ControllerへProfileStore injection seamとsame-path validationを追加する。
- startup matrixをresolverへ接続し、MainFrameへresolved stateを一括適用する。
- ID補正だけのpartial saveと通常full saveを`full > identity_only > none`のpending priorityで分離する。

### Step 6: runtime Apply / direct edit

- Controllerへ`apply_model_profile()`、`apply_no_model_profile()`とprofile-aware `apply_generation_preset()`を追加する。
- MainFrameへunified resolved-state commitを追加する。
- upper差分、output差分、identity-only、exact no-opを分類する。
- active profile中direct editをcontrol projection前後で拒否する。

### Step 7: mutation guard API

- Controllerのprofile Create / Update / Deleteをraw store前guardへ接続する。
- 既存preset Update / Deleteへreference / active baseline guardを追加する。
- candidate collectionに対するhistory normalizationをstore commit前にpreflightし、store成功後だけ事前検証済みcandidateを反映する。current outputを暗黙変更しない。

### Step 8: output-name propagation

- pipelineのTEXTあり / voice-only、legacy / effective branchへexplicit output namesを渡す。
- MainFrameのPreview / diagnostics / save pathを同じresolved setへ統一する。
- placeholder / clearでもLatin display namesを保持する。

### Step 9: diagnostics / report

- summary DTO、adapter、Info formatter、report formatterへprofile / baseline / set / fallbackを追加する。
- existing default caller互換とDTO invariantを更新する。
- mapped frame名以外をfingerprint payloadへ入れない回帰を追加する。

### Step 10: lifecycleとfailure回帰

- startup normalization、partial save failure、save-disabled、rollback consistency、reset、stale workerを検証する。
- B5 preset UIの既存動作がguard追加後もno-profile時に維持されることを確認する。

### Step 11: validation / scope audit

- B4専用から関連回帰、full suite、compileall、diff checkの順に実行する。
- diffでB5 UI、schema、dependency、package、runtime file、networkへのscope creepがないことを確認する。

### Step 12: docs同期

- implementation / verification結果をBlock Breakdown、Index、Roadmap、本planへ同期する。
- manual GUI未実施とactual-MMD未確認を明記し、B5 / MS26へ正しく引き継ぐ。

## 10. 状態遷移 / データ契約

### 10.1 startup matrix

| raw state | resolved state | generation / upper | set | ID save |
|---|---|---|---|---|
| active profileなし、baselineなし | `NO_PROFILE` | INI current、preset exact-match | Japanese | active preset補正時だけ |
| active profileなし、baselineあり | `FALLBACK_NO_PROFILE / orphan_profile_baseline` | INI current | Japanese | baseline clear |
| profile store unavailable | `FALLBACK_NO_PROFILE / profile_store_unavailable` | INI current | Japanese | active / baseline clearが必要な場合だけ |
| active profile unknown | `FALLBACK_NO_PROFILE / active_profile_not_found` | INI current | Japanese | active / baseline clear |
| profile default missing | `FALLBACK_NO_PROFILE / profile_default_preset_not_found` | INI current | Japanese | active / baseline clear |
| valid profile + valid runtime baseline | `RESOLVED` | baseline + profile override / profile-or-INI upper | profile set | raw IDs差分時だけ |
| valid profile + runtime baseline missing | `FALLBACK_PROFILE_DEFAULT / runtime_baseline_preset_not_found` | default baseline + profile override / profile-or-INI upper | profile set | default baseline ID |

ID correction saveはID keyだけを送る。startup resolutionだけを理由にnumeric keyを同時保存しない。

### 10.2 Apply matrix

| operation | upper diff | output / identity diff | result |
|---|---:|---:|---|
| profile candidate Select | - | - | B5 ownership、B4 state不変 |
| valid profile Apply | no | no | exact no-op |
| valid profile Apply | no | yes | output/profile history transactionまたはbase-independent commit |
| valid profile Apply | yes | any | analysis invalidation、base history clear |
| no-profile Apply | no | yes | Japanese / exact preset reconciliationをcommit |
| profile中preset Apply | no | yes | active profile維持、baselineだけ更新、override再適用 |
| invalid reference Apply | any | any | `ModelProfileResolutionResult` failure、完全不変 |
| active profile中direct edit | - | exact no-op | 完全不変 |
| active profile中direct edit | - | non-no-op | guard拒否、control再投影、完全不変 |

### 10.3 mutation matrix

| operation | allowed | current state / history |
|---|---|---|
| profile Create + valid preset ref | yes | 不変 |
| inactive profile Rename / value update / delete | yes | current不変、historical endpointのみ再照合 |
| active profile Rename | yes | output / fingerprint / INI不変 |
| active profile value / set / ref update | no | 全不変 |
| active profile delete | no | 全不変 |
| active baseline preset Rename、settings同一 | yes | profile / baseline / output / history / INI不変 |
| active baseline preset value update / delete | no | 全不変 |
| profileから参照中preset delete | no | 全不変 |
| profile store unavailable中のuser preset delete | no | fail closed、全不変 |

### 10.4 history endpoint

```text
OutputEditHistoryState
  current_state: OutputEditState
  current_model_profile_state: ModelProfileState | None
  undo / redo: OutputEditHistoryTransaction

OutputEditHistoryTransaction
  before_state / after_state
  before_model_profile_state / after_model_profile_state
```

profile contextなしの既存MS22 callerと、profileを一度も利用していないno-profile historyは`None`のまま動作できる。active profileまたはprofile identity transitionを含むB4 transactionではcurrent profile stateをpairとしてcommitし、以後そのchain内でoutputとprofile endpointを分割Undoしない。

active profile適用済みでanalysisからhistoryを初期化する場合は、初期`current_model_profile_state`をactive stateとする。profile transition後にno-profileへ戻ったendpointは`None`へ戻さずexplicit `NO_PROFILE` stateを持つ。これにより、active profile下の最初のevent-only transactionをUndoしてもprofile / baselineを維持し、profile transitionのUndo / Redoだけがprofile identityを変更する。

### 10.5 diagnostics identity

| active state | active preset | profile | baseline | set | fallback |
|---|---|---|---|---|---|
| no-profile exact preset | preset ID / name | none | none | Japanese | none |
| no-profile Custom | Custom | none | none | Japanese | none |
| resolved profile | none / Custom表示禁止 | profile ID / name | baseline ID / name | profile set | none |
| fallback profile default | none | profile ID / name | default ID / name | profile set | reason code |
| fallback no-profile | existing exact presetまたはCustom | none | none | Japanese | reason code |

## 11. テスト方針

### 11.1 core resolver

- 全nullable / non-null overrideとfield precedenceを検証する。
- profile Apply直後のdefault baseline、profile中別preset Apply、no-profile exact-matchを検証する。
- active profile中`active_preset_id=None`を検証する。
- startupの7 matrix行、status / reason、ID correction flag、numeric preservationを検証する。
- profile default missingとinactive explicit Apply failureをpartial applyしない。
- frozen DTOとinvalid invariantを検証する。

### 11.2 history

- set ID差分、profile identity-only、generation settings差分を一transactionとしてUndo / Redoする。
- upper差分をhistoryへ入れず、base-bound historyをclearする。
- profile中の別preset ApplyをUndo / Redoし、baseline IDとprofile non-null overrideを復元する。
- active profile適用済みでanalysisを開始し、最初のevent adjustmentをUndo / Redoしてもprofile / baselineを維持する。
- no-profileへUndo / Redoした際のactive preset exact-match / Customを検証する。
- profile / baseline / generation identityが変わるUndo / Redoはfull saveを一回要求し、event-only Undo / Redoはsaveを要求しない。
- inactive profile / noncurrent preset mutation後にinvalid historical endpointだけをcompactする。
- pending editありのlocal history candidateをsettle / normalizeしても、guard / preflight / store failure時はlive pending editとhistory全体が不変であることを検証する。
- store成功時だけsettled / normalized candidateが一括反映されることを検証する。
- current endpointがmutationでinvalidにならないguardを検証する。
- existing coalescing、redo discard、max 50、legacy adjustment projectionを回帰する。

### 11.3 startup / settings / failure

- 3 storeがsame settings pathで一回ずつloadされ、constructor I/Oがない。
- injected mismatched pathを拒否する。
- ID補正だけのstartup saveがnumeric keyを送らず、補正なしではsaveしない。
- identity-only pending後にfull要求が来た場合はfull payload一回だけ、full pending後のidentity-only要求ではfullをdowngradeしないことを検証する。
- identity-only / fullの反復coalescing、close flush、partial save failure時の初回通知 / save-disabledを検証する。
- profile Apply後のfull saveがprofile IDs、baseline ID、active preset、upper、generation settingsを一致して保存する。
- profile-aware Undo / Redo後のfull saveが復元後のcurrent identity / settingsを保存し、save failureでもstate / historyを保持する。
- commit前failureでsave requestが発生しない。
- commit後save failureでin-memory state / historyを保持し、初回通知とsave-disabledを維持する。

### 11.4 guard

- active profile update / delete、active baseline value update / delete、referenced preset deleteを固定codeで拒否する。
- active baselineかつreferenced、active baselineかつprofile store unavailable、非activeかつstore unavailable、非activeかつreferencedのoverlap matrixでSection 8.9の優先codeを検証する。
- malformed / unknown / built-in targetとduplicate RenameがB3 / MS22 codeを維持することを検証する。
- exact-settings Renameだけを許可し、fingerprint / history / INIを変えない。
- profile store unavailable時のpreset deleteをfail closedにする。
- active profile中のglobal generation / upper non-no-opを拒否し、event adjustmentと別preset Applyを許可する。
- no-profile時のMS22 direct edit、Custom正規化、preset UI mutation回帰を維持する。

### 11.5 writer / Preview / diagnostics

- Japanese / Latinでsemantic plan、frame number、value、count、sort orderが同一でnameだけが変わる。
- TEXTあり / voice-only、legacy / effective shapeの4 writer経路で同じsetを使う。
- Preview analyzed / empty / placeholder / clear / resetでLatin display nameがJapaneseへ戻らない。
- Preview hit-test / semantic selected vowelは日本語semantic keyのまま維持する。
- diagnostics effective allowed names、Info、reportがwriterと同じsetを示す。
- profile / preset / set display name、status / reasonだけではfingerprintが変わらない。
- Japanese / Latin mapped frame名ではfingerprintが変わり、schemaは不変である。

### 11.6 lifecycle

- workspace resetがprofile / baseline / generation / set / upperを保持し、workspace / historyをclearする。
- output-only Applyはanalysis / baseを再利用する。
- upper差分Applyはanalysis / Preview / saveability / historyを無効化し、late worker resultをdiscardする。
- analysis failure / cancel / rollbackでprofile stateが変わらない。
- rollback consistency token不一致ではrestoreしない。

### 11.7 実行順

一つのcommandごとにpass表示とprocess exit codeを確認する。

1. B4 core resolver / history専用test
2. B4 wx runtime専用test
3. B2 morph-name、B3 profile / preset / settings回帰
4. MS22 generation state / history / preset UI回帰
5. pipeline / writer / Preview / diagnostics / report回帰
6. rollback / workspace reset / lifecycle / save failure回帰
7. full suite
8. `compileall src tests`
9. `git diff --check`

計画作成時のread-only baselineは次のとおりである。

- B2 / B3 / preset / output history / rollback: `74 passed, 50 subtests passed`、process exit code 0
- wx generation / preset、reset / lifecycle、diagnostics / report、pipeline / VMD: `99 passed`、process exit code 0

両commandは別集合として実行した。production code、test code、GUI、runtime user dataは変更していない。

### 11.8 manual / actual-MMD

- B4はprofile選択UIを追加しないため、manual GUIを必須acceptance gateにしない。
- B5で実ユーザー導線のSelect / Apply / Create / Update / Deleteと表示を手動確認する。
- 実MMDでのVMD / WAV読み込み・リップ同期はMS26へdeferredのままとする。

### 11.9 実装後検証記録

- 2026-08-18にB4専用test 12件を実行し、process exit code 0で確認した。
- 同日にMS21 / MS22 / MS20関連回帰52件を実行し、process exit code 0で確認した。
- full suiteは`771 passed, 57 subtests passed`まで完走したがprocess exit codeは1だった。B4追加wxテストを除外しても`770 passed, 1 deselected, 57 subtests passed`・exit code 1を再現し、B4追加テスト固有ではない既存wx終了処理系のknown baselineとして、pass表示と終了コードを分離して記録する。`compileall src tests`と`git diff --check`はprocess exit code 0だった。
- manual GUIはB4の必須gateではなく、profile UIの確認をB5へ委譲する。実MMDによるVMD / WAV読み込み・リップ同期はMS26へdeferredである。

## 12. 受け入れ条件

- D1〜D7、S1〜S7のprecedence、guard、startup、state ownershipが再判断なしで実装される。
- exact class、field名・型・不変条件、public resolver / guard signature、status、reason / error codeがSection 8.1〜8.3と一致する。
- profile resolutionをUI、writer、Preview、diagnosticsで再実装しない。
- active profile、runtime baseline、resolved set、upper、generation settingsが責務別stateに保持される。
- profile Apply / no-profile / profile中preset ApplyがApply matrixどおりatomicに動く。
- upper差分で古いanalysis / Preview / output / base historyを再利用しない。
- output-only / identity-only Applyが不要な再解析なしでUndo / Redoできる。
- active profile下で初期化したhistoryの最初のevent-only Undo / Redoがprofile / baselineを変更しない。
- runtime baseline IDとprofile non-null overrideがrestart、Undo / Redoで維持・復元される。
- profile / baseline / generation / active preset identityが変わるUndo / Redoだけfull saveを要求し、event-only navigationでは要求しない。保存失敗でも復元済みstate / historyを維持する。
- historical dangling endpointをfallbackで別outputへ変えず、安全にcompactする。
- pending coalescingをlocal candidateでsettleし、guard / preflight / store failureではlive pending historyを完全不変にする。
- D2 / D3 / D6 / D7拒否でstore、state、history、fingerprint、INI、save requestが不変である。
- mutation failureが重なる場合はSection 8.9の優先順位で一意のcodeを返し、B3 / MS22 codeをB4 codeへ置換しない。
- settings同値Renameがmetadata-onlyで成功する。
- startup fallback status / reasonがdiagnosticsへ残り、補正後IDだけが必要時にINIへ保存される。
- startup identity-onlyと通常full saveが`full > identity_only > none`でcoalesceされ、full要求をpartial要求でdowngradeしない。
- 補正なしstartupではsaveを要求しない。
- workspace reset、analysis failure / cancel / rollback、stale resultでactive profileを失わない。
- writer、Preview、diagnostics、reportが同じresolved output namesを使う。
- Latinでもsemantic planとframe dataを変えず、empty / clear PreviewがJapaneseへ戻らない。
- no-profileと既存引数省略経路は日本語5母音defaultを維持する。
- fingerprint payload構造と`ms21-effective-output-v1`を維持し、mapped frame名だけがset差分を反映する。
- commit後INI save failureでcommitted in-memory state / historyをrollbackしない。
- B4専用、関連回帰、`compileall`、`git diff --check`はprocess exit code 0である。full suiteはsummary完走・failure / error表示なしを確認するが、既存wx終了処理系のknown baselineによりprocess exit code 1となる場合は、B4追加テストを除外した再実行とpass表示を分離記録し、新規failureと混同しない。
- profile UI、schema、dependency、package、network、runtime root fileへscope外変更がない。
- B4完了をmanual GUI確認済みまたはactual-MMD確認済みと表現しない。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| profile override付きsettingsをpreset resolverがCustom化する | baseline identityを専用profile stateへ置き、active profile時はpreset単独resolverを使わない |
| profile IDをOutputEditStateへ混ぜる | historyのoptional endpoint contextでだけprofile identityをpair commitする |
| identity-only ApplyがUndo不能になる | outputまたはprofile context差分でtransactionを成立させる |
| active profile下のhistory初期endpointが`None`になり最初のUndoでprofileを失う | analysis時のhistory初期化へcurrent profile stateを必ず渡す |
| profile-aware Undo / RedoがINIへ保存されずrestartで別baselineへ戻る | persistent projection差分がある履歴移動後だけfull saveを要求する |
| inactive store mutationで過去endpointがdanglingになる | currentはguard、historical endpointはatomic再照合 / compactionする |
| preflight前のcoalescing finishがstore失敗時にもlive historyを変更する | pure finishをlocal immutable candidateだけへ適用し、store成功後に一括反映する |
| missing historical baselineをdefaultへ置換してUndo outputが変わる | invalid endpointを除外し、stored outputを別resolutionへ黙って変えない |
| startup correctionがnumeric settingsまで上書きする、または後続full saveをpartialで失う | identity-only partial saveとfull saveを分離し`full > identity_only > none`でcoalesceする |
| 複数guard条件でUI notice codeが実装順に揺れる | B3 / MS22 precondition、active lock、reference unavailable、referencedの優先順位を固定する |
| upper limitの正本がcontrolだけでdirect-edit拒否できない | UiStateのresolved upperを正本、controlをprojectionにする |
| Latin profileのPreview clearだけJapaneseへ戻る | placeholder / clearにもexplicit current namesを渡す |
| diagnostics表示identityでfingerprintが変わる | summary fieldsをpayloadへ追加せず、effective mapped framesだけをhashする |
| pipelineの一方だけ日本語固定になる | TEXT / voice-only、legacy / effectiveの4経路を直接testする |
| broken profile JSON中にpresetを削除してdangling refを作る | reference不在を証明できないdeleteをfail closedにする |
| active profile中direct editでidentityと値が乖離する | event handlerのcommit前guardとcontrol再投影を必須化する |
| analysis rollbackが別profile stateを復元する | profile consistency token一致時だけ既存rollbackを許可する |
| B4がB5 profile UIへ拡大する | controller APIまでに止め、RightPane selector / editorを変更しない |
| B2 adapter / writerを再設計して回帰する | explicit primitive tupleを渡し、既存normalization / mapping実装を変更しない |

## 14. Codex実装時の注意

- 実装前に本planをfresh read-onlyで再チェックし、P1 / P2 / P3 gateを通す。
- shell commandは必ず一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`を使わない。
- 編集前後にlive contentを確認し、小さなpatchで既存worktree変更を保持する。
- D1〜D7、S1〜S7を未確定へ戻さない。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`をrepo root test fixtureにせず、stageしない。
- raw ProfileStore / PresetStore mutationをB5 GUIから直接呼ばせず、B4 controller guardを唯一のruntime入口にする。
- no-profileのJapanese default、preset単独Custom、event adjustment、VMD 30fps、audio contractを変更しない。
- writer module-levelからcoreへ逆importせず、primitive output-name tupleを渡す。
- UI sync contextやBasePlanIdentityへmorph-name set IDを追加しない。set変更はsemantic planを再解析しない。
- validation / resolution / history commit前にUI controlやstateを部分変更しない。
- startup identity correctionと通常full saveを混同しない。
- testを削除・弱化してfailureを回避しない。pass表示とprocess exit codeを分けて記録する。
- diffをvalidation前と最終報告前に自己監査し、scope creep、過去判断へのanchoring、例外経路を再確認する。
- commit、push、merge、tag、release、branch削除は別途明示承認まで行わない。
- 完了報告では、確認ファイル、変更ファイル、実装内容、test command / result / exit code、仕様逸脱、残課題、B5 handoffを分ける。
