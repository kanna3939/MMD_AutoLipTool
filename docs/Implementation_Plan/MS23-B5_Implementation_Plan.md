# MS23-B5 Model Profile UI Implementation Plan

## 1. 文書情報

- 文書名: MS23-B5 Model Profile UI Implementation Plan
- 作成日: 2026-08-18
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時branch: `feature/MS23-implementation`
- 計画作成時HEAD: `cc23666 Implement MS23-B4B wx teardown repair`
- 実装・検証時HEAD: `38f8eb5 Finalize MS23-B5 implementation plan`（実装変更は未コミット）
- 依存: MS22-B7 Closeout A、MS23-B1 Completed / Contract Fixed、MS23-B2〜B4 Implemented、MS23-B4B Implemented / Automated Verification Passed
- 文書ステータス: Reviewed / P2-P3 Corrections Applied / Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) / MS26 Actual-MMD Verification Deferred
- 計画策定時の権限: planning documentとrouting documentだけを変更し、production code、test code、GUI、runtime user dataを変更しない
- 実装開始条件: 本planの内容レビューとfresh read-only実装前チェックでP1 / P2 / P3なし、または検出事項の解消を確認する

本planは、MS23-B4で実装済みのmodel profile resolver、state、history、diagnostics、mutation guardを、既存wxPython GUIへ接続するB5の実装境界を固定する。B5はprofileのSelect / Apply / Create / Update / Deleteと表示を所有するが、profile resolution、precedence、schema、store failure、historyの規則を再実装しない。

## 2. 背景

MS23-B2はbuilt-in morph-name setとwriter / Preview / diagnosticsのmapping境界、B3は`profiles.json`と`ModelProfileStore`、B4はcross-store resolutionとruntime state / history / diagnostics、B4Bはwx test teardownを実装した。

現行GUIには次の状態がある。

- `src/gui_wx/right_pane.py`の「モデルプロファイル」tabはplaceholderだけである。
- `src/gui_wx/main_frame.py`には`apply_model_profile()`、`apply_no_model_profile()`、`apply_active_model_profile_preset()`と、resolved stateをatomic commitする`_commit_resolved_model_profile()`がある。
- `src/gui_wx/app_controller.py`にはprofile lookup、Apply resolution、Create / Update / Delete guardとstore mutationがある。
- `UiState`はactive profile ID / runtime baseline ID、resolved morph-name set、resolved generation settings、resolved upper limitを既に保持する。
- MS22-B5 preset UIにはstable ID、Select / Apply分離、panel revision、Busy / dirty input / stale request guard、modal CRUD dialog、panel noticeの実装例がある。

B5でUIがstoreやresolverを直接扱うと、B1の`event adjustment > model profile > preset > application default`、active profile mutation lock、runtime baseline、upper-limit差分のanalysis invalidationがconsumerごとに分岐する。したがってRightPaneはimmutableな表示stateとrequestだけを扱い、MainFrameとAppControllerの既存B4入口へ接続する。

## 3. 目的

1. RightPaneのmodel profile placeholderを、stable IDによる選択・明示Apply・管理UIへ置き換える。
2. selector上の候補選択とactive runtime stateを分離し、選択だけでoutput、analysis、history、INIを変更しない。
3. profileのrequired fieldとnullable overrideを、schema v1へそのまま対応するdialogで編集できるようにする。
4. B4のprofile Apply / no-profile Apply / mutation guard / history normalizationを唯一のruntime入口として再利用する。
5. Busy、selected-event dirty input、panel / editor revision、missing ID、store failureでpartial mutationを起こさない。
6. active profile、runtime baseline、morph-name set、resolved値、継承／override、fallback理由をユーザーが区別できる表示にする。
7. no-profile時の日本語5母音default、既存preset UI、VMD / Preview / diagnostics / 30fps / audio契約を回帰させない。

## 4. In Scope

- RightPane「モデルプロファイル」tabのselector、active summary、selected preview、Apply、Create / Update / Delete、notice
- `ModelProfilePanelItem`、`ModelProfilePresetOption`、`ModelProfilePanelState`等のimmutable表示DTO
- Select / Apply / Create / Update / Delete用immutable request DTOとexpected revision
- no-profile候補と日本語default表示
- profile create / update dialog
- built-in morph-name set 2種だけのchoice
- required default preset referenceのchoice
- nullable `morph_upper_limit`、hold、softness、long-vowel modeのoverride / inherit入力
- current active profile、runtime baseline、resolved output name、resolved numeric setting、fallback reasonの表示
- active profile中のglobal upper / hold / softness controlのlock表示と、no-profile復帰時の再有効化
- MainFrameでのpanel projection、selection保持、stale guard、notice、callback接続
- AppControllerでのGUI-facing candidate生成と既存B4 guarded mutationへの接続
- active profile Renameだけの許可表示、value / set / reference updateとdeleteのlock表示
- missing preset referenceを持つinactive profileの可視化と修復可能なUpdate導線
- dedicated wx UI test、controller plumbing test、B2〜B4B / MS22 preset UI回帰
- B5実装後のユーザー手動GUI確認項目

## 5. Out of Scope

- `ModelProfile` schema、`profiles.json` schema version、100件上限、atomic save仕様の変更
- `GenerationPreset` schema、`presets.json`仕様の変更
- B4 resolver、precedence、mutation guard code、history semantics、fingerprint schemaの再設計
- built-in以外のmorph-name set、任意morph名入力、ユーザー定義set
- PMX / PMD読込、model file解析、model名自動取得
- writer、Preview、diagnostics、reportの新しいmapping実装
- B6が所有するREADME、配布用readme、Pipeline / VMD / GUI / Error仕様の横断同期
- MS24 Whisper model選択、MS25一括出力、MS26実MMD確認、MS27 packaging / release
- dependency、license、build、package、network、FFmpeg、VMD format、30fps、WAV契約の変更
- Qt / PySide6の復活
- root `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`のtest fixture化、内容変更、stage
- branch、commit、merge、tag、push、branch削除

## 6. 前提条件

### 6.1 完了済み契約

- MS22 Closeout Aを維持する。
- D1 / D1A / D2〜D7、S1〜S7はAdoptedであり、未確定へ戻さない。
- profile Applyは`default_preset_id`をruntime baselineへ初期化する。
- active profile中の別preset Applyはprofile IDを維持し、runtime baseline IDだけを更新してprofileのnon-null overrideを再適用する。
- active profile中は`GenerationState.active_preset_id=None`である。
- active profileのvalue / set / default reference updateとdeleteはinactive化まで拒否し、同値内容のRenameだけを許可する。
- active runtime baseline presetのvalue update / deleteを拒否し、同値Renameだけを許可する。
- active profile中のglobal generation / upper direct editはnon-no-opを拒否する。
- upper limit差分はanalysis invalidationとbase-bound history clear、output-only差分はbase plan再利用とprofile-aware historyへ接続する。
- no-profileはJapanese morph-name setへ戻し、current generation settingsのexact preset identityを再照合する。
- validation / resolution / commit前failureは完全不変、commit後INI save failureはcommitted in-memory state / historyをrollbackしない。

### 6.2 B4B wx lifecycle

- wx testは`tests/helpers.py`の`get_or_create_wx_app()`と`destroy_wx_app()`を使用する。
- activeな`wx.App`を同時に複数生成しない。
- reused Appを無条件に破棄しない。
- Controller / timer / pending callbackを明示teardownし、root runtime user dataへのpending saveをtemporary storeへ隔離する。
- pass表示とprocess exit codeを別々に記録し、access violationをpassへ読み替えない。

### 6.3 計画作成baseline

2026-08-18に次を実行し、`41 passed, 31 subtests passed`、process exit code 0を確認した。

```powershell
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms23_b3_model_profiles.py tests\test_ms23_b4_model_profile_state.py tests\test_ms23_b4_profile_history.py tests\test_wx_ms23_b4_profile_runtime.py tests\test_wx_ms22_b5_preset_ui.py tests\test_ms23_b4b_wx_teardown.py
```

このbaselineはB3 persistence、B4 resolution / history / runtime、MS22 preset UI、B4B teardownの開始前状態であり、B5実装後の合格を意味しない。

### 6.4 実装後の到達状態（2026-08-19）

- B5のRightPane、MainFrame、AppController接続、profile CRUD、Select / Apply分離、Busy / stale guard、profile / preset cross-syncを実装した。
- 削除確認結果を`wx.ID_YES`へ修正し、削除成功後に`wx.Choice`の候補と選択状態を再投影する回帰を追加した。
- 連続する同一母音の長音境界を補正し、`long_vowel_mode=decay`で前区間の終端ゼロと次区間のピークが同一フレームへ重なることでPreview形状計画が失敗する経路を解消した。既存の衝突検出契約は維持した。
- 関連回帰は31件、全体は785件＋57 subtestsがpass表示・process exit code 0、`compileall src tests`と`git diff --check`もprocess exit code 0である。
- ユーザーによる手動GUI確認は問題なしと報告された。確認主体はユーザーであり、Codex自身のGUI実行結果とは扱わない。
- ユーザー確認後、旧ユーザーモデルプロファイルをruntime `profiles.json`から削除し、`MMD_AutoLipTool.ini`のactive profile参照をクリアした。標準の「プロファイルなし（日本語5母音）」を保持し、`presets.json`は変更していない。これらのruntime dataはstage対象外である。
- 実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままである。次工程はMS23-B6 Cross Regression / Documentationである。

## 7. 対象ファイル

### 7.1 主変更候補

| ファイル | 変更責務 |
|---|---|
| `src/gui_wx/right_pane.py` | profile panel表示DTO / request DTO、selector、summary、dialog、buttons、notice、theme / wrap / Busy projection |
| `src/gui_wx/main_frame.py` | panel selection / revision、canonical projection、request guard、Apply / CRUD callback、notice、preset panelとのcross-sync |
| `src/gui_wx/app_controller.py` | GUI入力からcanonical profile candidateを一度だけ生成し、既存B4 guard / store mutationへ渡すadditive facade |

### 7.2 原則変更しない関連確認対象

| ファイル | 確認内容 |
|---|---|
| `src/core/model_profiles.py` | schema v1、DTO、store、100件上限、atomic mutationをそのまま利用する |
| `src/core/model_profile_state.py` | resolver / guard / error codeをそのまま利用する |
| `src/core/morph_name_sets.py` | built-in 2セットのID、display name、output namesを表示へ投影する |
| `src/core/generation_presets.py` | built-in / user presetのstable IDとsettingsをdefault baseline候補にする |
| `src/gui_wx/ui_state.py` | canonical runtime state。panel selectionやrevisionを追加しない |
| `src/gui_wx/ui_sync_context.py` | semantic base identityへprofile UI stateを混入させない |
| `src/gui_wx/parameter_panel.py` | current resolved control。profile editor stateを追加しない |
| `src/gui_wx/app.py` | startup store ownershipとB4 startup projectionを変更しない |

`ui_state.py`、`ui_sync_context.py`、`parameter_panel.py`に変更が必要になった場合は、panel-local stateで不足する理由とB4 ownershipへの影響を実装前に再確認する。単なるselector stateやdialog stateのためには変更しない。

### 7.3 テスト候補

- 新規 `tests/test_wx_ms23_b5_model_profile_ui.py`
- 新規 `tests/test_ms23_b5_model_profile_controller.py`
- 既存 `tests/test_wx_ms23_b4_profile_runtime.py`
- 既存 `tests/test_wx_ms22_b5_preset_ui.py`
- 既存B2 / B3 / B4 / B4B、settings / startup / reset / diagnostics / Preview / writer回帰

### 7.4 文書変更

B5計画策定時は次だけを変更する。

- `docs/Implementation_Plan/MS23-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

README、配布用readme、正本仕様のimplemented同期はB6へ残す。B5実装時は本planのstatusとrouting上のB5状態・検証結果だけを同期できる。

## 8. 実装方針

### 8.1 UIとruntime責務の分離

- RightPaneは`ModelProfileStore`、JSON、resolver、historyへ直接アクセスしない。
- RightPaneはMainFrameから渡されたimmutable `ModelProfilePanelState`だけを描画する。
- selectorはstable profile IDを保持し、display nameをidentityに使用しない。
- selector変更は`selected_model_profile_id`だけを変更する。Apply前はcurrent output、analysis、history、Preview、diagnostics、INIを完全不変にする。
- MainFrameはpanel-local selection / revision、UiStateからのcanonical projection、request validationを所有する。
- AppControllerはstore lookup、candidate construction、B4 guard、atomic mutationを所有する。
- Applyは既存`apply_model_profile()`または`apply_no_model_profile()`だけを呼ぶ。UIでprecedenceを再計算しない。

### 8.2 immutable panel DTO

`src/gui_wx/right_pane.py`へ、少なくとも次のfrozen dataclassを追加する。field名は実装前チェックで現行命名と衝突しないことを再確認する。

```text
ModelProfilePresetOption
  id: str
  display_name: str
  source: built_in | user
  generation_settings: GenerationSettings

ModelProfilePanelItem
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

ModelProfilePanelState
  items: tuple[ModelProfilePanelItem, ...]
  preset_options: tuple[ModelProfilePresetOption, ...]
  selected_profile_id: str | None
  active_profile_id: str | None
  active_profile_display_name: str | None
  active_preset_id: str | None
  active_preset_display_name: str | None
  active_baseline_preset_id: str | None
  active_baseline_preset_display_name: str | None
  active_morph_name_set_id: str
  active_morph_name_set_display_name: str
  active_output_names: tuple[str, str, str, str, str]
  active_generation_settings: GenerationSettings
  active_morph_upper_limit: float
  resolution_status: str
  resolution_reason: str | None
  mutation_available: bool
  load_error_code: str | None
  load_error_message: str | None
  busy: bool
  panel_revision: int
```

pair fieldとstatus / reasonはB4 DTOの不変条件を維持する。no-profile時はactive profile / baseline pairを`None`、morph-name setをJapaneseとし、active preset pairは既存preset resolverのexact-matchまたはCustomを表す。active profile時はprofile ID / display name、baseline ID / display nameをpairで持ち、active preset pairは`None`とする。fallback reasonをUIで別codeへ変換しない。

### 8.3 immutable request DTO

```text
ModelProfileEditorValues
  display_name: str
  morph_name_set_id: str
  morph_upper_limit: float | None
  generation_overrides: ProfileGenerationOverrides
  default_preset_id: str

ModelProfileSelectRequest
  selected_profile_id: str | None
  expected_panel_revision: int

ModelProfileApplyRequest
  profile_id: str | None
  expected_panel_revision: int
  expected_editor_revision: int

ModelProfileCreateRequest
  values: ModelProfileEditorValues
  expected_panel_revision: int

ModelProfileUpdateRequest
  profile_id: str
  values: ModelProfileEditorValues
  expected_panel_revision: int
  expected_editor_revision: int

ModelProfileDeleteRequest
  profile_id: str
  expected_panel_revision: int
  expected_editor_revision: int
```

- `profile_id=None`のApplyは「プロファイルなし」を意味する。空文字や表示名を特殊値にしない。
- expected revisionはnon-negative intだけを受理し、boolを拒否する。
- Createはcurrent output identityを変更しないためeditor revisionを持たないが、受理時に既存dirty-input guardを確認する。
- Apply / Update / Deleteはoutput identityまたはhistory normalizationへ影響し得るため、panel revisionとselected editor revisionの両方を確認する。
- DTO validation failureはcallback前に拒否し、stateを変更しない。

### 8.4 model profile panel表示

panelは`wx.ScrolledWindow`とし、既存RightPaneのtheme、wrap、scroll、tab selectionを維持する。上から次を表示する。

1. active profile: profile名、または「プロファイルなし」
2. active runtime baseline: preset名、または「なし / Custom」
3. active morph-name setとresolved output names
4. resolved upper / hold / softness / long-vowel mode
5. resolution fallback notice（存在する場合だけ）
6. profile selector
7. selected profileのstored default preset、morph set、nullable override summary
8. 「選択したモデルプロファイルを適用」button
9. Create / Update / Delete buttons
10. operation / load error notice

selector先頭は`プロファイルなし（日本語5母音）`とし、IDは`None`で表す。user profileはstore orderを維持し、表示名順に暗黙sortしない。

selected previewはstored値を表示する。nullable fieldは`継承`、non-null fieldは`上書き: <value>`と表示する。active summaryはresolved値を表示し、stored値と混同しない。

active profileがselected itemと異なる場合でも、active profile IDからstore itemをlookupし、active側のdefault baselineと各override / inheritをresolved summaryの隣へ表示する。active profile / baselineのdisplay nameは既存`_sync_profile_display_names_from_state()`でstable IDから再取得し、Undo / RedoやRename後に古いmetadataを表示しない。

missing `default_preset_id`を持つstructurally valid profileは一覧から消さない。`参照先プリセットが見つかりません`と表示し、Applyをdisabledにする。inactive profileのUpdate / Deleteは許可し、Update dialogでvalid presetへ修復できる。requestを直接生成した場合もB4 resolver / guardがfail closedにする。

### 8.5 Create / Update dialog

dialogは次の入力を持つ。

- profile表示名: single-line text
- default preset: built-in / userをstable IDで選ぶchoice
- morph-name set: `日本語5母音` / `英字5母音`だけのchoice
- morph upper limit: override checkbox + `wx.SpinCtrlDouble(min=0.0, max=10.0, inc=0.05)`
- closing hold: override checkbox + `wx.SpinCtrl(min=0, max=100)`
- closing softness: override checkbox + `wx.SpinCtrl(min=0, max=100)`
- long-vowel mode: override checkbox + `hold / decay` choice
- baselineとoverrideから得られる設定のpreview

override checkboxがoffならDTO値を`None`にし、対応controlをdisabledにする。onならcontrolのprimitive値を渡す。表示用の`継承`や日本語labelをcoreへ渡さない。

Create dialogの初期値は次とする。

- nameは空。
- default presetは、active profileのvalid runtime baseline、no-profileのvalid active preset、`builtin:standard-hold`の順で選ぶ。
- morph-name setはcurrent resolved setを選ぶ。
- upper、hold、softness、long-vowel modeのoverride checkboxはoffとし、DTOでは`None`としてapplication / selected presetから継承する。
- disabledな各controlにはcurrent resolved値を明示overrideへ切り替える場合の候補値として保持する。checkboxをonにしたfieldだけ、そのprimitive値をDTOへ入れる。

この初期値はD1のstable preset referenceとnullable inheritを既定にするinherit-first契約であり、preset値や既存active profileのoverride metadataを新規profileへ暗黙複製しない。current effective snapshotとして固定したいfieldだけ、ユーザーがcheckboxを明示的にonにする。B5では別のClone機能を追加しない。

Update dialogはselected profileのstored値をexactに表示する。nullable fieldはcheckbox off、non-null fieldはonとする。missing default referenceの場合はwarningを表示し、choiceをvalid fallbackへ選び直すまでOKを無効化する。

selected profileがactiveの場合、display name以外のcontrolをdisabledにし、`適用中のプロファイルは名前だけ変更できます。設定変更や削除は「プロファイルなし」または別profileをApplyした後に行ってください。`と表示する。stale requestではUI disableを信用せずB4 guardを再実行する。

dialog Cancelはpanel selection、active state、store、history、Preview、INIを完全不変にする。

### 8.6 Select / Apply契約

#### Select

- selector変更はpanel-local selected IDだけを更新する。
- selected previewだけを更新し、Apply resolverを呼ばない。
- 一覧再構築後にselected IDが存在すれば保持する。
- selected IDが消失した場合、valid active profile、no-profileの順でfallbackする。
- profile Create成功後は、mutation前後のstable ID集合差から一意に得たcreated IDをselectするがApplyしない。display nameからIDを逆引きしない。

#### Apply profile

- requestのprofile IDがcurrent selector selectionと一致することを確認する。
- Busy、panel revision、editor revision、dirty selected-event input、missing profile、missing default presetをcommit前に拒否する。
- `MainFrame.apply_model_profile(profile_id)`からB4 resolver / commitを一回だけ呼ぶ。
- success後だけactive summary、preset panel、ParameterPanel、Preview、diagnostics、action stateを`sync_ui_state()`で再投影する。
- exact no-opはB4どおりhistory transactionとsettings saveを作らない。
- upper差分は既存B4経路でanalysis invalidation / history clearを行い、panel独自のconfirmやinvalidatorを追加しない。
- output-only差分はbase planを保持し、B4 profile-aware historyへ一transactionとしてcommitする。
- failureは旧active state、history、selection、panel selectionを保持し、noticeだけを更新する。

#### Apply no-profile

- selected IDが`None`であることを確認し、`MainFrame.apply_no_model_profile()`を呼ぶ。
- profile / baseline IDをclearし、Japanese setとcurrent generation settingsのexact preset reconciliationはB4 resolverに委譲する。
- already no-profileかつ同一projectionならno-opとする。
- no-profile Apply成功後もselectorは`None`を保持する。

### 8.7 Create / Update / Delete契約

#### Controller candidate facade

現行`AppController.create_model_profile(candidate_profile)`はprebuilt candidateを受ける。RightPane / MainFrameがUUID生成を所有しないよう、B5ではadditiveなGUI-facing facadeを追加する。

```text
create_model_profile_from_values(...fields...) -> ProfileMutationResult
update_model_profile_from_values(profile_id, ...fields...) -> ProfileMutationResult
```

- Create facadeはcanonical lowercase UUIDを一度だけ生成し、そのIDで`ModelProfile`を構築する。
- 同じcandidateを既存`create_model_profile()`のpreflightと`ModelProfileStore.create(profile_id=...)`へ渡す。
- Update facadeはtarget stable IDをcandidate IDに再利用する。
- DTO construction failureは`invalid_input`の`ProfileMutationResult`へ変換し、storeを呼ばない。
- 既存candidate-based method、B4 guard、store APIは削除・弱化しない。
- MainFrameはCreate facade呼出し前のprofile ID集合を保持し、success時の`ProfileMutationResult.user_profiles`との差がexact 1件であることを確認してcreated stable IDを取得する。0件または複数件ならdisplay nameで補完せず、旧selectionを保持してcanonical collectionを再同期し、自動選択できなかった旨をnoticeへ表示する。

#### Create

- Busy、panel revision、dirty input、mutation availabilityを確認してからdialog resultを送る。
- successまではoutput、history、active profile、INIを変更しない。
- success後、stable ID集合差がexact 1件ならそのcreated IDをselectし、`Applyで出力へ反映できます`とnoticeを表示する。
- 100件上限、duplicate display name、invalid input、write / replace failureはresult codeを日本語noticeへ投影する。

#### Update / Rename

- inactive profileは全fieldを更新できるが、current outputへ暗黙Applyしない。
- active profileは同じID・同じvalue / set / referenceでdisplay nameだけが変わるRenameだけ成功する。
- active Rename成功時は既存`_sync_profile_display_names_from_state()`を使い、UiStateのactive display name、panel、Info / diagnostics / report表示をstoreから再同期する。profile ID、baseline ID、effective output、history、fingerprint、INI save要求は変えない。
- inactive mutation後のhistorical endpoint normalizationは既存Controllerに委譲する。
- success後もselected stable IDを保持する。

#### Delete

- inactive profileだけを削除できる。
- active profileのDelete buttonはdisabledにし、direct / stale requestは`active_profile_locked`で拒否する。
- Yes / No確認を行い、Noは完全不変とする。
- success後、削除対象がselectedならvalid active profile、no-profileの順でselectionをfallbackする。
- Controllerがnormalized history candidateをcommitするまでstore mutationを行わない既存B4順序を維持する。

### 8.8 preset UIとのcross-sync

- `sync_ui_state()`はpreset panelとmodel profile panelを同じcanonical UiStateから順に再投影する。
- active profile中にpreset tabから別presetをApplyした場合、profile panelはactive profileを維持し、runtime baseline名とresolved override結果を更新する。
- profile Apply / no-profile Apply後はpreset panelも更新する。active profile中のpreset panelはexisting `active_preset_id=None`契約をCustomと誤解してprofileを解除しない。
- preset Create / Update / Deleteでprofile panelのdefault preset optionやselected previewが変わる場合、profile panel revisionを更新する。
- profileから参照中preset Delete、active runtime baseline preset mutationは既存B4 guardのerror codeをpreset panel noticeへ表示する。
- profile UIがpreset store private collectionを変更しない。

### 8.9 Busy / stale / dirty / lifecycle

- Busy中はselector、Apply、Create / Update / Deleteをdisabledにし、callbackを受けてもno-opにする。
- `active_model_profile_id`がnon-nullの間は、既存`ParameterPanel.enable_inputs()`をMainFrameの`update_action_states()`からfalseにし、global upper / hold / softness direct editを視覚的にもlockする。no-profile復帰時はBusyでなければ再有効化する。
- このcontrol lockはD7のcommit前guardを置換しない。stale wx eventやdirect method callは既存`validate_active_profile_direct_edit()`でも拒否する。
- active profile中もevent adjustment editorとpreset tabの明示Applyは既存契約どおり利用できる。
- Busy解除後に拒否操作を自動再送しない。
- panel signatureが変わるたびrevisionを単調増加させる。signatureはprofile tuple、preset option tuple、selected / active ID、runtime baseline、resolved settings / set / upper、mutation / load state、Busyを含む。Busy開始前に作られたrequestをBusy解除後に受理しない。
- revisionはUI stale guardだけに使い、UiState、history、fingerprint、INIへ保存しない。
- selected-event dirty inputをApply / CRUDで暗黙破棄しない。
- profile操作でcurrent tabを自動変更しない。Preview clickによる「選択イベント」tab自動切替を維持する。
- workspace reset、analysis failure / cancel / rollback、playback、diagnostic clearはactive profileを保持し、profile panelをcanonical stateへ再投影する。
- startup fallbackはB4 stateをそのまま表示し、B5で再resolutionしない。

### 8.10 error / notice

load errorとmutation / Apply errorを同じ成功扱いにしない。error codeは内部契約として保持し、panelには次の分類で日本語noticeを表示する。

| 分類 | code例 | UI動作 |
|---|---|---|
| profile load failure | `invalid_json`、`unsupported_schema`、`invalid_schema`、`read_failed`、`duplicate_id`、`duplicate_display_name`、`limit_exceeded` | user profile一覧を空、mutation無効、no-profile/current fallback stateを表示 |
| input / target failure | `invalid_input`、`profile_not_found`、`duplicate_display_name`、`duplicate_id`、`limit_exceeded` | state / store不変、再入力可能なnotice |
| reference / active lock | `preset_reference_not_found`、`active_profile_locked` | state / store不変、inactive化またはreference修復方法をnotice |
| persistence failure | `write_failed`、`replace_failed`、`store_unavailable`、`store_not_loaded` | old JSON / tuple / runtime stateを保持し、mutationを無効化 |
| Apply resolution failure | `profile_not_found`、`profile_default_preset_not_found`等 | active state / history / selection不変、panelをcurrent collectionへ再同期 |

連続modal errorは使用せず、通常の操作失敗はpanel noticeへ表示する。Delete確認だけをmodalとする。INI save failureは既存AppControllerの一回通知 / session save停止を維持する。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- branch、HEAD、worktree、B1〜B4B status、本plan、Block Breakdown、Index、Roadmapを確認する。
- production / test / docsのpre-existing差分を確認し、ユーザー所有変更を保持する。
- root runtime user dataがignore対象であり、stage対象外であることを確認する。
- fresh read-only pre-checkで本planのexact DTO / method名と現行codeを再照合する。

### Step 2: RightPane DTOとpanel skeleton

- immutable panel / request DTOを追加する。
- placeholderをScrolledWindow、summary、selector、buttons、noticeへ置き換える。
- projection guard、stable ID mapping、wrap / theme / scrollを追加する。
- selectorイベントではSelect requestだけを送る。

### Step 3: profile editor dialog

- required baseline / morph set、nullable override controlを実装する。
- Create inherit-first初期値と明示override用current value候補、Update stored値、active Rename-only状態を投影する。
- invalid / missing selection、Cancel、checkbox enable / disableを固定する。

### Step 4: MainFrame projectionとrequest guard

- panel-local selection、initialized flag、signature、revisionを追加する。
- `_sync_model_profile_panel()`をcanonical `sync_ui_state()`へ接続する。
- Select / Apply / Create / Update / Delete callbackをbindする。
- Busy、revision、dirty input、current selection、missing IDをstore / resolver前に確認する。

### Step 5: AppController GUI facade

- UUIDを一度だけ生成するCreate facadeを追加する。
- Update facadeでtarget IDを保持したcandidateを作る。
- DTO validation failureをnon-mutating failure resultへ変換する。
- MainFrameでmutation前後のstable ID集合差をexact 1件として検証し、created IDを取得する。
- 既存B4 guard、candidate history normalization、store mutation順序を変更しない。

### Step 6: Apply / mutation後のcross-sync

- Apply success後にprofile / preset / Parameter / Preview / diagnosticsを一回同期する。
- active Renameはdisplay metadataだけを同期する。
- inactive CRUDはoutputへApplyしない。
- selected ID消失時のfallbackとpanel noticeを確定する。

### Step 7: dedicated tests

- controller facadeのUUID / validation / guard / atomic failureをtemp storesで検証する。
- wx panelのSelect / Apply / CRUD / inherit / Busy / stale / broken file / cross-syncを検証する。
- B4B helperを使い、root runtime fileを作成・変更しない。

### Step 8: regression / manual handoff / status同期

- dedicatedからfull suiteまで一コマンドずつ実行する。
- pass表示とprocess exit codeを別記録する。
- manual GUI項目を提示し、ユーザー報告とCodex実施を区別する。
- B5の実装・自動検証状態だけをrouting文書へ同期する。正本仕様の横断closeoutはB6へ残す。

## 10. 状態遷移 / データ契約

### 10.1 panel state

```text
sync canonical state
  -> project profile tuple + preset options + active runtime state
  -> preserve selected stable ID if still present
  -> otherwise active profile -> no-profile fallback
  -> update panel signature / revision if projection changed

Select
  -> panel-local selected ID / preview only

Apply
  -> Busy / dirty / panel revision / editor revision / current ID guard
  -> B4 resolve
  -> B4 atomic commit
  -> canonical sync

CRUD
  -> Busy / dirty / revision / dialog validation
  -> B4 mutation guard + candidate history
  -> profile store atomic mutation
  -> selection / metadata sync only
```

### 10.2 Apply matrix

| 操作 | upper差分 | output / profile差分 | 結果 |
|---|---:|---:|---|
| 未適用profile Select | - | - | panel previewだけ変更 |
| active profileと同一profile Apply | no | no | no-op、save / historyなし |
| profile Apply | no | yes | B4 output/profile transaction、base再利用 |
| profile Apply | yes | any | analysis invalidation、base-bound history clear |
| no-profile Apply | no | yes | Japanese + exact preset reconciliationをcommit |
| no-profile再Apply | no | no | no-op |
| active profile中preset Apply | no | yes | active profile維持、runtime baseline更新、override再適用 |
| invalid / stale / Busy / dirty | - | - | 完全不変、noticeまたはsilent stale no-op |

### 10.3 CRUD matrix

| 操作 | store変更 | current output / identity |
|---|---:|---|
| Create valid | yes | 不変。created IDをselectするだけ |
| inactive Update / Rename | yes | current不変。必要なhistorical endpointだけnormalize |
| active Rename | yes | profile ID / output / history / INI不変、displayだけ同期 |
| active value / set / reference Update | no | 全不変、`active_profile_locked` |
| inactive Delete | yes | current不変、selection fallback |
| active Delete | no | 全不変、`active_profile_locked` |
| missing default preset repair Update | yes | current不変。以後Apply可能 |
| write / replace failure | no | old file / tuple / state / historyを保持 |

### 10.4 nullable field mapping

| UI | DTO | resolution |
|---|---|---|
| upper override off | `morph_upper_limit=None` | application / INIを継承 |
| upper override on | strict `float` | profileがapplicationより優先 |
| hold / softness override off | field `None` | runtime baseline presetを継承 |
| hold / softness override on | strict `int` | profileがpresetより優先 |
| mode override off | `None` | runtime baseline presetを継承 |
| mode override on | `hold` / `decay` | profileがpresetより優先 |
| morph set choice | required built-in ID | active profileがrequired setを所有 |

## 11. テスト方針

### 11.1 dedicated controller test

`tests/test_ms23_b5_model_profile_controller.py`で次を検証する。

- Create facadeがcanonical UUIDを一度生成し、guard candidateとstore resultで同じIDを使う。
- Create successの前後stable ID集合差がexact 1件となり、そのcreated IDが`ProfileMutationResult.user_profiles`から取得できることをController側で検証する。0件／複数件の防御経路ではdisplay nameをidentityに使わない。MainFrame／wx側の選択反映は専用UI testで検証する。
- invalid fieldは`invalid_input`でstore / file / stateを変更しない。
- valid Create / inactive Update / Deleteの外部永続化対象はtemporary `profiles.json`だけとし、current output、analysis、INIは変更しない。B4契約に基づくhistorical endpoint normalizationは成功後のin-memory history candidateとして許可し、別テストで検証する。
- missing preset referenceをCreate / Updateで拒否する。
- active Renameだけ成功し、active value / set / reference UpdateとDeleteを拒否する。
- write / replace failureでold tuple / file / historyを保持する。
- Create / CRUDだけでactive output、analysis、INIを変更しない。

### 11.2 dedicated wx test

`tests/test_wx_ms23_b5_model_profile_ui.py`で次を検証する。

- stable ID selectorとno-profile item。
- SelectだけではUiState、history、analysis、Preview、INIが変わらない。
- Japanese / Latin profile Applyとno-profile復帰。
- upper差分Applyのanalysis invalidation、output-only Applyのbase再利用。
- active profile中preset Apply後のruntime baseline / override summary。
- Create inherit-first初期値、明示overrideへ切り替えたfieldだけのprimitive mapping、Cancel不変。
- Create success後にMainFrameがstable ID集合差から取得したcreated IDを選択し、Applyしない。
- inactive Update / Delete、active Rename-only、active Delete disabled。
- missing default referenceの表示、Apply disabled、Update修復。
- profile load failure時のno-profile継続とmutation lock。
- Busy、panel revision、editor revision、dirty input、missing / stale IDの拒否。
- profile / preset panel cross-sync、theme、wrap、scroll、current tab維持。
- active profile中のglobal upper / hold / softness disabledと、no-profile復帰後の再有効化。
- B4B helperによるowned / reused App teardownとprocess exit code 0。

### 11.3 必須回帰

- MS23-B2 morph mapping / Preview / writer / diagnostics
- MS23-B3 profile store / settings / ignore
- MS23-B4 resolution / history / startup / save / rollback / reset
- MS23-B4B wx teardown
- MS22-B3〜B5 generation preset / history / preset UI
- MS21 event adjustment / Undo / Redo / Preview selection
- MS17 / MS19 / MS20 lifecycle、voice-only、diagnostics、saveability
- existing Japanese default writer / VMD / 30fps / audio tests

### 11.4 実装後command順

実装時に実在するtest pathへ再確認したうえで、次を一つずつ実行する。

1. B5 dedicated controller
2. B5 dedicated wx
3. B2〜B4B + MS22 preset UI related regression
4. lifecycle / startup / reset / rollback / diagnostics / Preview / writer regression
5. `-k "wx"` aggregateを2回連続
6. full suiteを2回連続
7. `compileall src tests`
8. `git diff --check`
9. runtime user data / package境界確認

代表command:

```powershell
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms23_b5_model_profile_controller.py tests\test_wx_ms23_b5_model_profile_ui.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q -k "wx"
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
git status --short -- profiles.json presets.json MMD_AutoLipTool.ini
```

test削除、skip / xfail追加、assertion弱化でpassさせない。pass表示後にprocess exit codeがnon-zeroなら未解消として切り分ける。

### 11.5 manual GUI確認項目

B5実装後、ユーザーへ少なくとも次を提示する。

1. profileなしで既存日本語5母音と既存preset UIが変わらない。
2. Create dialogでname、baseline、Japanese / Latin、各override / inheritを設定できる。
3. Create直後は候補が選択されるだけで、Apply前のPreview / analysis / outputが変わらない。
4. Latin profile Apply後にPreview label、Info / diagnostics、profile summaryが`A / I / U / E / O`へ揃う。
5. upper同値のoutput-only Applyで再解析不要、upper差分Applyで再解析必要になる。
6. active profile中にpreset tabから別presetをApplyし、runtime baselineだけが変わりprofile overrideが維持される。
7. no-profile ApplyでJapaneseへ戻り、current generation settingsが保持される。
8. inactive profileのUpdate / Delete、active profileのRename、active value update / Delete lockが説明どおり動く。
9. active profile中は上部のモーフ最大値 / 開口保持 / 閉口スムーズが無効になり、no-profile復帰後に再び編集可能になる。
10. dialog Cancel、Busy、selected-event dirty inputで意図しない変更が起きない。
11. app再起動と「新規作業」でactive profile / baseline / resolved settingが契約どおり復元・保持される。
12. light / dark theme、RightPane scroll、tab選択が維持される。

ユーザー報告はユーザー実施のmanual GUI evidenceとして記録し、Codex自身の実施結果と混同しない。実MMDによるVMD / WAV読込・リップ同期はMS26へ残す。

## 12. 受け入れ条件

- RightPane placeholderがmodel profile selector / summary / CRUD UIへ置き換わる。
- selectionとApplyが分離され、Selectだけではruntime stateを変更しない。
- profileなしがstable `None` identityで表され、Japanese defaultを維持する。
- editorがrequired baseline / built-in setと全nullable fieldをschemaどおり入出力する。
- Createは全nullable fieldをinheritとして開始し、明示的にonへ切り替えたfieldだけcurrent value候補をoverrideとして保存する。
- RightPaneがJSON、store mutation、resolver、historyを直接扱わない。
- Create candidate IDをControllerが一度だけ生成し、preflight / store commitで同じIDを使う。MainFrameはmutation前後のstable ID集合差がexact 1件であることを確認してcreated IDを選択する。
- ApplyはB4 resolver / commitを一回だけ使い、upper差分とoutput-only差分を正しく分ける。
- active profile中の別preset Applyでprofile overrideとruntime baseline契約を維持する。
- active profileのRenameだけを許可し、value / set / reference UpdateとDeleteをcommit前に拒否する。
- inactive CRUDはcurrent outputを暗黙変更しない。
- Busy、dirty input、panel / editor revision、missing ID、broken JSON、write / replace failureでpartial stateを作らない。
- missing preset reference profileを消さず、inactive Updateで修復できる。
- profile / preset panels、ParameterPanel、Preview、diagnostics、action stateが同じcanonical stateへ同期する。
- active profile中はglobal upper / hold / softness controlがdisabledとなり、no-profile復帰時に再有効化される。D7 guardも維持する。
- no-profile Japanese default、existing preset Custom、event adjustment、Undo / Redo、workspace reset、startup、rollbackを回帰させない。
- B5 dedicated、related regression、wx aggregate 2回、full suite 2回、compileall、diff checkがpass表示・process exit code 0である。
- root runtime filesを作成・変更・stageせず、temporary storesだけで自動testする。
- dependency、package、license、network、Qt / PySide6、VMD / audio format変更がない。
- manual GUI確認の主体と範囲、MS26 actual-MMD未確認を正確に記録する。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| selector変更が暗黙Applyになる | selected IDをpanel-localにし、Apply requestだけがB4 resolverを呼ぶ |
| display nameをidentityに使う | selector / request / lookupはstable profile IDだけを使う |
| UIがprecedenceを再計算する | stored previewとresolved summaryを分け、ApplyはB4 resolverへ委譲する |
| nullable `None`を0や表示文字列に変換する | checkbox offをexact `None`、onをstrict primitiveへmappingする |
| Create既定値がpreset値をoverrideへ複製する | 全nullable checkboxをoffで開始し、ユーザーがonにしたfieldだけを明示overrideにする |
| Create UUIDをUIとstoreで別生成する | Controller facadeが一度生成したcandidate IDをguard / storeで共有する |
| Create成功後にdisplay nameからIDを逆引きする | mutation前後のstable ID集合差をexact 1件として検証し、そのIDだけを選択する |
| active profile updateでoutputが暗黙変更される | active dialogをRename-onlyにし、B4 guardでも再拒否する |
| active profile中もglobal controlが編集可能に見える | MainFrame action stateでParameterPanelをlockし、既存D7 guardを防御層として残す |
| missing preset profileが一覧から消えて修復不能になる | itemを保持し、Apply disabled + inactive Update repairを提供する |
| profile Apply後にpreset panelがCustom表示だけになりprofile identityを失う | profile stateとpreset stateを別summaryで表示し、同じsyncで再投影する |
| upper差分をoutput-onlyとして扱う | invalidationをUIで再実装せずB4 `_commit_resolved_model_profile()`だけを使う |
| stale dialog resultが新しいstateへ適用される | panel / editor expected revisionとcurrent stable IDをcommit前に確認する |
| CRUD success後にhistory endpointだけ壊れる | Controllerのcandidate collection normalizationをstore commit前に維持する |
| broken JSON時にcurrent stateを消す | B4 startup fallbackを表示し、mutationをfail closedにする |
| wx App teardownが再発する | B4B helperを全新規wx testで使い、wx / full aggregateを2回実行する |
| runtime user dataをtest / commitへ混入する | temp stores、root限定ignore、status path checkをacceptance gateにする |
| B5でB6 docs closeoutへ拡大する | plan / routing statusだけを同期し、README / specsはB6へ残す |

## 14. Codex 実装時の注意

- commandは一つずつ実行し、parallel、pipeline、chained commandを使わない。
- 実装前にlive Git、current code、test、planを再照合し、古い履歴記述をcurrent factにしない。
- B1のD1〜D7 / S1〜S7、B4のresolver / guard / history、B4Bのteardownを弱化しない。
- `src/core/model_profiles.py`や`src/core/model_profile_state.py`の変更が必要に見えた場合は、B5 UI plumbingで解決できない理由を確認する。material contract変更はB5内で暗黙に行わない。
- RightPaneからraw store、JSON、writer、Preview resolver、diagnostics builderを直接呼ばない。
- UI表示名、`継承`label、choice indexをcore identityとして保存しない。
- profile editorのinput validationをtest回避のため緩めない。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`をroot test fixtureにせず、stageしない。
- dependency、package、release、tag、merge、push、branch削除を行わない。
- GUIを実行していない場合、manual GUI verifiedと記録しない。
- 実MMD未確認をMS23-B5完了へ混入させず、MS26へ維持する。
- 実装完了報告では、確認ファイル、変更ファイル、実装内容、test command / result / exit code、仕様逸脱、manual GUI境界、残課題、B6 handoffを分ける。
