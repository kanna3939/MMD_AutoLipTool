# MS22-B4 Implementation Plan

## 1. 文書情報

- 対象Block: `MS22-B4`
- 名称: Generation State / History / Diagnostics Integration
- 作成日: 2026-08-08
- 基準branch: `feature/MS21-implementation`
- 基準HEAD: `53308a1 Sync MS22-B3 documentation status`
- 文書状態: **Implemented / Code Check Passed / User Manual Test Passed / P2-P3 Resolved (2026-08-09)**
- 直接依存: MS22-B1 Completed / Contract Fixed、MS22-B2 Implemented / Code Check Passed、
  MS22-B3 Implemented / Code Check Passed、MS21 Closeout A
- 次工程: MS22-B5 Implementation Plan策定

本書は、B2の長音shared resolverとB3のgeneration preset / settings contractを、MS21のadjustment history、
wx `UiState`、Preview / VMD、diagnostics、analysis lifecycleへ統合する実装計画である。本書作成段階では
production code、test code、GUI、INI / JSON本体、dependency、build設定を変更しない。

## 2. 背景

MS22-B2は、`ShapeParameters`のclosing hold / softness / long-vowel modeを入力として、長音runを含む
`EffectiveShapePlan`を一回のshared resolverで構築できる。MS22-B3は、同じ3値をimmutable
`GenerationSettings`として保存し、built-in / user preset、INI active settings / active preset id、
`presets.json`、Custom fallbackを実装した。

一方、現行wx統合はB3以前の状態である。

- `UiState`が保持する履歴は`AdjustmentLayerSnapshot`だけで、generation settingsとactive preset idを
  Undo / Redoしない。
- closing hold / softnessを変更すると`_on_param_changed()`がanalysis結果、base、adjustment、selectionを
  無効化し、再解析を要求する。
- `AnalysisParameterSnapshot`とrollback DTOはclosing hold / softnessをanalysis-affecting parameterとして扱う。
- startupは`app.py`と`AppController`が別々の`SettingsStore` instanceを作り、B3のpreset store / active
  resolutionをwx stateへ接続していない。
- INI保存値はParameterPanelから再取得され、`long_vowel_mode`と`active_preset_id`をcurrent stateから明示的に
  渡していない。
- diagnostics generation summaryはmodel name、hold / softness、fingerprint schemaだけで、active mode / preset、
  effective hold / decay run数、mode override数を持たない。

B4ではこれらを一つのbase-bound output edit stateへ統合する。ただしpreset selector、preset管理dialog、
long-vowel event mode editorの見た目はB5の責務として残す。

## 3. 目的

- baseなしでも有効な`GenerationState`と、base確定中だけ有効な`OutputEditState`を実装する。
- adjustment、generation settings、active preset idを一つの最大50件history transactionとして復元する。
- preset適用、direct output setting変更、Undo / Redoを、base再解析なしでshared resolverへ接続する。
- candidateを一回だけresolveし、同じimmutable contextをPreview、editor、diagnostics、saveability、VMD保存へ渡す。
- generation commit後にINI保存をcoalesceし、保存失敗でin-memory state / historyをrollbackしない。
- analysis success / failure / cancel / mismatch、input変更、workspace reset、late callbackでB1 lifecycle matrixを守る。
- MS21 fingerprint canonical payloadを維持したまま、generation / adjustment summaryをadditiveに拡張する。
- B5がGUIを追加するときに、preset適用とmode editを既存historyへ接続できる非表示のstate APIを固定する。

## 4. In Scope

- immutable `GenerationState`
  - `generation_settings: GenerationSettings`
  - `active_preset_id: str | None`
- immutable `OutputEditState`
  - `base_plan_identity: BasePlanIdentity`
  - `adjustment_snapshot: AdjustmentLayerSnapshot`
  - `generation_state: GenerationState`
- output edit全体を保持するhistory transaction / current state / pending gesture
- 最大50 transaction、redo破棄、event edit gesture coalescing、preset apply / direct settingのdiscrete commit
- active presetのapply、Custom generation settings commit、deleted / mismatched presetのCustom正規化API
- current adjustment commit / reset / Undo / Redoのatomic output historyへの移行
- startup時のINI settings + preset store resolutionと、baseなし`GenerationState`初期化
- closing hold / softness / long-vowel modeのoutput-only化
- morph upper limitだけをanalysis-affecting parameterとして残すhandler / rollback guard分離
- generation stateを正本にした`BaseTimingPlanInput.shape_parameters`構築
- resolver resultがcandidate generation settingsと一致することを保証するprovenance / context guard
- non-no-op preset apply / direct edit / Undo / Redo後のresolver 1回、UI同期、INI保存要求
- generation stateを含むanalysis rollback capture / restore / mismatch判定
- generation / adjustment diagnostics summaryとInfo / text reportのadditive拡張
- fingerprint payloadとschema `ms21-effective-output-v1`の維持、WARNING確認再利用契約
- B4専用core / wx testとMS20 / MS21 / MS22-B2 / B3回帰

## 5. Out of Scope

- RightPane `プリセット`tabのselector、Custom表示control、preset管理dialog
- user presetの作成・更新・名前変更・削除UIとerror notice UI
- selected long-vowel terminal eventのmode override control、disabled reason、reset UI
- generic history framework、persistent history、session restore、historyのINI / JSON保存
- morph upper limitのpreset化、model profile、morph名切替
- B2 resolver semantics、decay exact zero、long run ownership、same-vowel / cross-vowel algorithmの変更
- fixed morph `あ / い / う / え / お`、30fps、VMD形式、既存音声3役契約の変更
- Qt / PySide6、network、external ASR、background通信、Whisper自動download
- dependency、package、release、tag、merge、push、branch操作
- B5のpreset selector / mode controlを含む総合manual GUI受け入れ（B5 / B6）
- 実MMDでのVMD / WAV・リップ同期確認（MS26）

## 6. 前提条件

- MS21 Closeout A、MS22-B1契約、B2 / B3実装済み状態を未完了へ戻さない。
- `GenerationSettings`はB3実装のimmutable `0..100 / 0..100 / hold|decay`を再利用し、別DTOへ複製しない。
- `GenerationPresetStore.resolve_active()`はINI settingsを正本にし、missing / unknown / mismatch idをCustomへ
  正規化するB3契約を維持する。
- `BasePlanIdentity`はtimeline、observation、source durationを正本とし、generation settingsを含まない。
  B4はidentity schemaを変更せず、output stateでgeneration settingsを別に所有する。
- 明示hold / softness / long mode overrideはactive generation settingsと同値でもsnapshotに残す。
- decay中のtail overrideはlatentのまま保持し、holdへ戻したとき再び有効にする。
- adjustment historyの最大50件、redo破棄、gesture coalescing、Edit menu shortcut / dirty input guardを維持する。
- settings / preset editはBusy中に拒否する。late / duplicate analysis callbackの現行job guardを迂回しない。
- 計画作成baseline（2026-08-08）は関連180件＋19 subtestsがpass表示、failure / error表示なし、
  各process exit code 0である。production code、test code、GUIは変更していない。

## 7. 対象ファイル

### 7.1 production code変更対象

| ファイル | B4で担当する責務 |
| --- | --- |
| `src/core/output_edit_state.py`（新規） | `GenerationState`、`OutputEditState`のimmutable契約とidentity整合validation |
| `src/core/event_adjustment_history.py` | atomic output edit history、50件、redo、gesture coalescing。既存adjustment-only public APIは回帰用に維持 |
| `src/core/effective_shape_plan.py` | resolver入力`ShapeParameters`を保持する唯一のadditive provenanceとhint整合検証 |
| `src/core/output_diagnostics.py` | generation / adjustment summary additive field。fingerprint payloadは維持 |
| `src/core/diagnostic_report.py` | active mode / preset、hold / decay run数、mode override数のstructured report表示 |
| `src/core/__init__.py` | 新state / history DTO・helperの必要最小限export。fresh import cycleを追加しない |
| `src/gui_wx/ui_state.py` | always-valid generation state、base-bound output history、compatibility property、lifecycle clear / retain |
| `src/gui_wx/ui_sync_context.py` | output state / generation settingsとeffective plan hintの整合guard |
| `src/gui_wx/analysis_rollback.py` | morph upperだけのanalysis parameter guard、generation + output history rollback |
| `src/gui_wx/output_diagnostics_adapter.py` | UiState / effective plan / active preset resolutionからsummary inputを構築 |
| `src/gui_wx/main_frame.py` | candidate resolve-before-commit、output-only parameter handler、canonical control投影、single sync context、Undo / Redo統合と出力編集文言 |
| `src/gui_wx/app_controller.py` | injectableなsingle settings / preset store ownership、明示startup load、preset apply entry、generation stateのINI保存 |
| `src/gui_wx/app.py` | controller所有storeを使うstartup initializationへ統一 |

### 7.2 条件付き変更対象

| ファイル | 条件 |
| --- | --- |
| `src/core/generation_presets.py` | controllerがprivate collection走査をせずpreset idを解決するpure lookup helperが必要な場合だけadditive変更する |
| `src/gui_wx/parameter_panel.py` | morph upper handlerとoutput-only handlerをMainFrame側bindingだけで分離できない場合だけ、既存control / labelを変えずevent routingを最小変更する |
| `tests/test_ms21_b7_import_boundaries.py` | 新core / wx module順序のfresh-process cycle回帰を追加する場合に変更する |

### 7.3 B4で必須作成する新規test

- `tests/test_ms22_b4_generation_history.py`
- `tests/test_wx_ms22_b4_generation_state.py`

### 7.4 既存testの変更・回帰対象

- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_wx_ms21_b7_state_integration.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms21_b7_ui_sync_context.py`
- `tests/test_wx_ms21_b7_sync_efficiency.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_settings_store.py`
- `tests/test_wx_ms13_integration.py`
- `tests/test_wx_startup_splash.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms22_b2_import_boundaries.py`

### 7.5 B4で変更しないファイル

- `src/gui_wx/right_pane.py`、`src/gui_wx/selected_event_editor.py`のpreset / mode UI
- `src/core/text_processing.py`、`src/core/pipeline.py`、`src/vmd_writer/writer.py`のlong metadata生成
- `src/core/generation_presets.py`のschema version 1、built-in definition、atomic JSON contract
- `src/core/preview_transform.py`、`src/vmd_writer/effective_shape_adapter.py`のmapping semantics
- README、end-user仕様文書（B6 documentation closeoutで同期）
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、license / package文書

## 8. 実装方針

### 8.1 state ownership

- `GenerationState`はbaseなしでも`UiState`に常在し、startup、input変更、workspace reset後も保持する。
- `OutputEditState`はbase plan確定中だけ存在し、adjustment snapshotとbase identityの完全一致を必須とする。
- base確定中は`OutputEditHistoryState.current_state.generation_state`と`UiState.generation_state`を常に同一にする。
- generation stateとadjustment historyを独立したlive正本にしない。UiStateのlegacy adjustment propertyは
  current output stateから派生させる。

### 8.2 atomic output history

- existing adjustment-only DTO / pure helperはcore回帰と外部import互換のため残す。
- 同moduleへoutput edit全体を扱うDTO / helperをadditiveに追加し、wx canonical pathだけを新historyへ移す。
- 50件切り詰め、redo破棄、pending gestureなど共通transitionはprivate generic helperまたは同じ検証関数を
  再利用し、adjustment-only系とoutput-edit系へ独立したcopy-and-paste algorithmを作らない。
- transaction before / afterは同じbase identityを要求し、adjustment、settings、active idを部分復元しない。
- event editor gestureだけは既存`AdjustmentCoalescingKey`でまとめる。preset apply、direct generation edit、
  reset all、Undo / Redoはgestureと結合しないdiscrete boundaryとする。
- no-op candidateはtransactionを作らず、new commitはredoを破棄し、確定transactionを最大50件に切り詰める。

### 8.3 resolve-before-commit

- generation変更、preset適用、Undo / Redoは、immutable candidate history / stateを先に構築する。
- candidate generation settingsから`ShapeParameters`を作り、current base + candidate adjustmentをB2 resolverへ
  一回だけ渡す。
- resolve成功後だけcandidate historyとgeneration stateをUiStateへinstallする。失敗時はcurrent state、history、
  Preview、diagnostics、INI保存要求を変更しない。
- success時は同じ`EffectiveShapePlan`を含む`UiSyncContext`を`sync_ui_state()`へ渡し、Preview、editor、
  diagnostics、saveability、VMD準備でresolverを再実行しない。
- successful sync contextはcurrent `OutputEditState`と対応付けてMainFrame内に保持し、後続のVMD保存と
  diagnostic report準備でも同じimmutable planを再利用する。cacheはbase identityだけで判定せず、
  adjustmentとgeneration stateの一致を必須とする。
- input / base / output state変更、invalid rollback、workspace resetではcacheをclearする。contextがない場合だけ
  current stateから一回構築し、構築後に同じ同期処理内で共有する。

### 8.4 effective plan provenance guard

- 現行`BasePlanIdentity`はgeneration settingsを含まないため、identity + adjustmentだけではhintのgeneration一致を
  証明できない。
- `EffectiveShapePlan`をresolver入力`ShapeParameters` provenanceの唯一の所有先とし、末尾にimmutable
  `shape_parameters: ShapeParameters`をadditiveに持たせる。既存の直接constructorとの互換用defaultを許すが、
  `resolve_effective_shape_plan()`は常に`base_input.shape_parameters`を明示設定する。
- `UiSyncContext`は独立したprovenanceを持たず、hint受理時に`effective_plan_hint.shape_parameters`とcandidate
  `base_input.shape_parameters`を比較する。context側のcandidate値を複製してhint由来情報の代用にしない。
- base identity、adjustment snapshot、shape parametersのいずれかが不一致ならstale hintを拒否する。
- hint比較前にcandidate adjustmentが`None`なら、そのbase identityに対する`empty_adjustment_snapshot(identity)`へ
  canonicalizeする。`None`をwildcardとして扱わず、candidateがemptyでhintがnon-emptyの場合もstale hintとして拒否する。
- provenance fieldはdiagnostic display / history / fingerprintの新正本にせず、resolver resultの整合guardだけに使う。
- このadditive fieldをsave-state fingerprint payloadへ含めず、既存effective frame / tail canonicalizationを維持する。

### 8.5 generation commitとpreset normalization

- direct hold / softness / long-mode入口は、requested `GenerationSettings`をcurrent settingsと先に比較する。
  settingsが同値ならactive preset idを保持した完全no-opとし、resolver、history、INI保存要求を発生させない。
- direct変更でsettingsが実際に変わった場合だけ`GenerationState(new_settings, None)`としてCustomへ移る。
- preset applyは選択presetのsettingsとidを一回のcandidateへ入れ、current adjustment / selection / baseを保持する。
  settingsが同値でもvalid idが異なるpreset applyはid-only discrete transactionとし、requested settingsとidの
  両方がcurrent generation stateと同じ場合だけfull-state no-opとする。base確定中のid-only transactionも
  preset apply契約どおりresolver 1回を通す。
- apply入口はB4でcontroller / frame APIとして実装し、B5はそのAPIを呼ぶだけにする。
- Undo / Redoで復元するactive idは、その時点のpreset storeで`resolve_active()`する。deleted / unknown / definition
  mismatchならsettingsを保持してidをNoneへ正規化し、追加transactionは作らない。
- deleted / unknown / definition mismatchの正規化はUndo / Redoと同じatomic transitionで行う。移動対象transactionの
  `before_state` / `after_state`をcurrent storeで正規化し、正規化後に両endpointが同値ならeffective no-opとして履歴から
  除去する。同値でない場合は正規化済みendpointへ置換し、追加のuser transactionを作らず、次の反対方向navigationでも
  `before` / `after`とcurrentのinvariantを満たす。
- preset表示名はstore resolutionから派生し、history / INI / fingerprintへ重複保存しない。

### 8.6 output-only parameter handler

- ParameterPanelのmorph upper eventとclosing hold / softness eventを別handlerへ分離する。
- morph upper変更は現行どおりaudio job invalidation、analysis invalidation、再解析要求、settings saveを行う。
- closing hold / softness変更はgeneration candidateをcommitし、baseがある場合だけresolver 1回とoutput history
  transactionを作る。baseなしではgeneration stateだけを更新し、Undo対象にしない。
- long-vowel modeはB4 state APIで同じ処理を実装するが、B5まで新controlを追加しない。
- programmatic startup applyはhistoryを作らず、user event binding後の同値eventもno-opとして扱う。
- ParameterPanelは表示・入力adapterとし、resolver、diagnostics、VMD writer引数、INI保存はすべて
  `UiState.generation_state.generation_settings`を正本にする。未確定control文字列をoutputへ直接渡さない。
- startup、successful direct edit、preset apply、Undo / Redo、rollback後は、専用の投影処理でcanonical
  generation stateのhold / softnessを既存controlへ設定する。long-vowel modeはB5までcontrolを追加しない。
- control投影中は専用guardでEVT_TEXT / EVT_SPINCTRLをcommit入口から除外する。candidate resolve拒否時は
  commit前のcanonical値をcontrolへ再投影し、追加resolver、history、INI保存要求を発生させない。

### 8.7 startup / persistence

- `AppController`が単一`SettingsStore`と、それを基準pathにした`GenerationPresetStore`を所有する。
- `AppController` constructorはoptional `SettingsStore` / `GenerationPresetStore`を受け取れるようにし、
  未指定時だけproduction default pathのstoreを構築する。constructor内ではload / saveを実行しない。
- `AutoLipToolApp`のconstructorはoptionalな`settings_store` / `preset_store` keyword引数を受け取り、`OnInit`で
  同じinstanceを`AppController`へ渡す経路を明示する。既存の`AutoLipToolApp(False)`を含むwx.Appの位置引数意味は
  維持し、既定pathはstore引数省略時だけ使用する。
  startup testはこのseam経由でtemporary storeを注入してrepository既定INI / `presets.json`が不変であることを確認する。
- startup load / active resolution / normalizationは明示startup methodで一回だけ実行し、`app.py`はFrameと
  controllerの接続後にそのresultを適用する。
- `app.py`は別`SettingsStore`を作らず、controllerのstartup load resultをMainFrameへ適用する。
- normalized INI 3値から`GenerationSettings`を作り、preset load後にactive idをresolveし、baseなし
  `GenerationState`を初期化する。
- raw active idがmissing / mismatchでCustomへ正規化された場合、current outputはINI settingsを保持し、
  安全なstartup完了後に正規化済みidのcoalesced INI保存を一回要求する。
- `flush_pending_save()`とVMD保存時のgeneration引数はParameterPanelではなく`UiState.generation_state`から
  hold / softness / mode / active idを読む。morph upperは既存control値を維持する。
- INI保存失敗ではcurrent state / historyをrollbackせず、既存save-disabled / first notificationを維持する。
  同一sessionの後続保存要求とclose flushは再保存を試みず、`attempted=False` / state非変更として扱う。

### 8.8 lifecycle / rollback

- `AnalysisParameterSnapshot`は`morph_upper_limit`だけを保持する。
- `AnalysisRollbackSnapshot`はtiming plan、base identity、output edit history、generation state、selection、prior
  diagnostic failure、morph upper parameterを保持する。
- analysis start時はpending event gestureをfinishし、generation stateとoutput historyが一致する場合だけcaptureする。
- current successはcurrent generationを保持し、新base + empty adjustmentでhistoryを初期化する。初期化自体はUndo
  transactionを作らず、resolverを一回だけ実行する。
- failure / cancel rollbackはcurrent generationがcapture時と一致し、job / morph upper / base comparisonが有効な場合だけ
  old base / output history / generation / selectionを復元する。
- morph upper mismatchではresultもrollbackもcommitせず、current generationを保持してbase / history / selectionを
  clearし、再解析待ちへ移る。
- input変更とworkspace resetはbase / output history / adjustment / selectionをclearし、generation stateを保持する。
- app-level generation state単独はworkspace作業データではないため、`has_workspace_user_data`の判定へ含めず、
  startupまたはbaseなしgeneration変更だけで新規作業確認を表示しない。
- late / duplicate callbackはgeneration、history、diagnostics、INI pending stateを変更しない。

### 8.9 diagnostics / report

- `GenerationDiagnosticsSummary`へ次をadditiveに追加する。

```text
active_long_vowel_mode: hold | decay
active_preset_id: str | None
active_preset_display_name: str | None
effective_long_vowel_hold_run_count: int | None
effective_long_vowel_decay_run_count: int | None
```

- `AdjustmentDiagnosticsSummary`へ`long_vowel_mode_override_count: int`をadditiveに追加する。
- DTO constructor / validationで、modeは`hold`または`decay`だけ、hold / decay run countは`None`または非負整数、
  active preset idとdisplay nameは両方`None`または両方present、mode override countは非負整数と固定する。
  `None`（未確定）と`0`（確定済みzero run）を混同しない。
- effective run countはwriter input未確定／未解析時`None`、有効planで該当runなしなら`0`、存在時は
  `EffectiveShapePlan.long_vowel_runs[].resolved_mode`から数える。
- override countはcanonical adjustment snapshotのnon-`None` `long_vowel_mode`件数から数える。
- active display nameはpreset store resolutionから受け取り、Noneはadapter / reportで`Custom`と表示する。
- Info formatterとdiagnostic reportは同じstructured summaryだけを使用し、表示文字列からstateを復元しない。

### 8.10 fingerprint / WARNING

- `build_save_state_fingerprint_payload()`の既存field、順序、schema `ms21-effective-output-v1`を変更しない。
- active preset id / display name、Custom、history、notice、generation summary fieldをpayloadへ追加しない。
- generation変更でeffective morph frames / tailsが変われば既存payloadが自然に変わり、WARNING確認を再利用しない。
- preset idだけが変わる、またはmode変更が該当long runのないoutputへ影響しない場合、effective payloadが同じなら
  WARNING確認を再利用する。
- Preview、VMD保存、diagnostics、fingerprintはcommit時に得た同一contextを使い、別々にresolveしない。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- branch、HEAD、worktree、B1 / B2 / B3の実装済み状態、本planを再確認する。
- P1 / P2 / P3の残存とユーザー所有変更の有無を確認し、実装前チェック判定を出す。
- production変更前に§7の現行path、import、test名を再照合する。

### Step 2: output state DTO

- `output_edit_state.py`へ`GenerationState`と`OutputEditState`をfrozen dataclassとして実装する。
- GenerationSettings型、active id型、base identity、adjustment identityをconstructorでfail closedにする。
- serialization APIを作らず、timing plan / path / selection / historyをDTOへ混入させない。

### Step 3: atomic history core

- output edit transaction、pending edit、history state、initialize / commit / finish / undo / redo pure helperを追加する。
- base identity invariant、50件、redo破棄、no-op、gesture key一致をテストする。
- adjustment-only public APIと既存testを維持し、wx側に二つのlive historyを作らない。

### Step 4: UiState migration

- always-valid generation stateとbase-bound output historyを追加する。
- current adjustment、can undo / redo、pending gesture、has adjustmentの既存propertyをcurrent output stateから派生させる。
- legacy UiState method / Edit menu callerを最小wrapperで維持しつつ、commit単位をOutputEditStateへ統一する。
- reset / invalidate / successでgeneration retain、history clear / initializeを§10 matrixどおり実装する。
- generation state単独を`has_workspace_user_data`へ含めず、startup / baseなし設定変更の新規作業確認を抑止する。

### Step 5: startup store integration

- controller constructorへoptional settings / preset storeを追加し、constructorからload / saveを分離する。
- `AutoLipToolApp(settings_store=..., preset_store=...)`をstartup seamとし、既存のwx.App callerを壊さず`OnInit`でその
  同一instanceをcontrollerへ渡す。
- explicit startup methodでINI load、preset load、active resolutionを一つのstartup flowへまとめる。
- app.pyの重複SettingsStoreを撤去し、MainFrameへnormalized settingsとGenerationStateを一回適用する。
- invalid user JSONでもbuilt-in resolutionを維持し、B5表示用load resultをcontrollerに保持する。
- startup testはtemporary INI / `presets.json`を注入し、repository既定pathを読み書きしない。

### Step 6: output-only direct edit / preset API

- morph upperとgeneration control eventを分離する。
- settings同値direct no-opをCustom transitionより先に判定し、baseなしcommit、baseありresolve-before-commit、
  actual settings変更時のCustom transition、id-onlyを含むpreset applyを実装する。
- stale / invalid / Busy requestをstate非変更で拒否し、successful commitだけINI保存要求へ進める。
- B5から呼べるpreset apply / custom settings APIをwx control非依存で固定する。
- canonical generation stateからhold / softness controlへのguard付き投影と、candidate拒否時の再投影を実装する。

### Step 7: Undo / Redo / editor integration

- existing adjustment edit / resetをoutput state transactionへ移す。
- Undo / Redo候補をpreset storeで正規化し、一回resolve後にinstallする。
- dirty editor、selection identity、gesture boundary、shortcut、redo discard、50件を維持する。
- valid selectionは保持し、base identity不一致・new baseではclearする。
- Edit menu、tooltip、完了noticeをhistory全体に合う「出力編集を元に戻す／やり直す」へ更新する。

### Step 8: analysis lifecycle integration

- rollback DTOとcapture / restore / can-restoreをgeneration + output history契約へ更新する。
- hold / softnessをanalysis parameter comparisonから外し、morph upper mismatch回帰へ期待値を移す。
- success / failure / cancel / prior ERROR / input change / workspace reset / late callbackを§10 matrixで検証する。

### Step 9: diagnostics / report / fingerprint

- generation / adjustment summary fieldをadditiveに追加し、adapterでcurrent stateとeffective planから構築する。
- Info / reportへmode、preset、run count、override countを追加する。
- fingerprint payloadのsnapshot testを維持し、id-only変更、effective変更、save-disabled後の後続要求を検証する。

### Step 10: import / regression / closeout

- fresh-process import、B4専用test、指定回帰、full suite、compileall、diff checkを一つずつ実行する。
- diffを§7へ照合し、B5 UI、B6 docs、dependency / packageの先行変更を除外する。
- 実装結果だけをplan、Block Breakdown、Index、Roadmapへ同期し、Codexが実施していないmanual GUIと
  実MMDを独自判断で完了扱いにしない。

## 10. 状態遷移 / データ契約

### 10.1 DTO

```text
GenerationState (immutable, base-less valid)
  generation_settings: GenerationSettings
  active_preset_id: str | None

OutputEditState (immutable, base-bound)
  base_plan_identity: BasePlanIdentity
  adjustment_snapshot: AdjustmentLayerSnapshot
  generation_state: GenerationState

OutputEditHistoryTransaction (immutable)
  before_state: OutputEditState
  after_state: OutputEditState

OutputEditHistoryState (immutable)
  current_state: OutputEditState
  undo_transactions: tuple[OutputEditHistoryTransaction, ...]
  redo_transactions: tuple[OutputEditHistoryTransaction, ...]
  pending_edit: PendingOutputEditHistoryEdit | None
```

- transaction before / after / currentは同じbase identityを持つ。
- `adjustment_snapshot.base_plan_identity == OutputEditState.base_plan_identity`を必須とする。
- `UiState.generation_state == current_state.generation_state`をbase確定中の必須invariantとする。

### 10.2 commit flow

```text
request
  ↓ Busy / stale / dirty / type guard
direct requestはsettings同値をid=None candidate生成より先に判定
  ├─同値: preserve current settings / id / history / INI pending state、resolverなし
  └─変更あり、またはpreset / Undo / Redo: 続行
finish pending event gesture when boundary changes
  ↓
immutable candidate OutputEditHistoryState
  ↓ preset id normalize
candidate ShapeParameters + current base + candidate adjustment
  ↓ base確定中だけshared resolver exactly once。baseなしcommitはresolverをskip
effective plan / provenance validation
  ├─ failure: preserve current state / history / INI pending state、canonical controlをguard付き再投影
  └─ success: install candidate atomically
                 ↓
             sync same UiSyncContext
                 ↓
             coalesced INI save request
```

### 10.3 lifecycle matrix

| transition | generation state | base / output history / selection | resolver / persistence |
| --- | --- | --- | --- |
| app startup | INI settingsを正本にactive idをresolve | baseなし、historyなし | mismatch idはCustomへ正規化しINI保存要求 |
| baseなしdirect edit | settings commit、id=None | historyなし | resolverなし、INI保存要求 |
| analysis start | 保持、Busy edit拒否 | rollback候補capture、pending gesture完了 | resolverなし |
| current success | current generationを保持 | new base + empty adjustmentでhistory初期化、selection clear | resolver 1回、Undo entryなし |
| failure / cancel rollback可 | capture stateを復元 | old output history / selection復元 | current diagnostics規則を維持 |
| morph upper mismatch | current generationを保持 | result / rollback非commit、base / history / selection clear | 再解析待ち、保存禁止 |
| input変更 | 保持 | base / history / selection clear | old callback拒否 |
| workspace reset | 保持 | workspace / base / history / selection clear | settings / preset file非削除 |
| preset apply（full-state変更） | preset settings + id | full stateを1 transaction | resolver 1回、INI保存要求 |
| preset same-state再適用 | current generation保持 | history変更なし | resolver / INI保存要求なし |
| direct output edit（settings変更） | settings + id=None | full stateを1 transaction | resolver 1回、INI保存要求 |
| direct settings同値event | settings / id保持 | history変更なし | resolver / INI保存要求なし |
| event edit gesture | generation保持 | adjustmentをcoalesced transaction | gesture中もcandidate resolver 1回ずつ |
| Undo / Redo | full stateをrestore、missing idはCustom | valid selection保持 | resolver 1回、INI保存要求 |
| INI save failure | current state保持 | history保持 | first notification / save-disabled維持 |
| late callback | 変更なし | 変更なし | sync / save要求なし |
| app close | current generationをflush可能なら保存 | history破棄 | 次回はlast successful INIのみ |

Undo / Redoでactive presetがdeleted / mismatchedになった場合は、移動中transactionのbefore / after endpointを
current storeで同時に正規化する。正規化後にbeforeとafterが同値ならそのtransactionをeffective no-opとして除去し、
追加のuser historyを作らない。反対方向のnavigationは正規化済みendpointをcurrentとして検証する。

### 10.4 diagnostics contract

| state | active mode / preset | run count | override count |
| --- | --- | --- | --- |
| baseなし / 未解析 | current generation / resolved nameまたはCustom | hold=None、decay=None | 0 |
| invalid / rebuild待ち | current generation / resolved nameまたはCustom | hold=None、decay=None | 0 |
| valid base、long runなし | current generation / resolved nameまたはCustom | hold=0、decay=0 | snapshot実数 |
| valid base、long runあり | current generation / resolved nameまたはCustom | resolved mode別実数 | snapshot実数 |

### 10.5 fingerprint contract

```text
MS21 canonical payload (unchanged)
  input mode / normalized paths
  effective writer input state
  VMD model name
  effective morph frames
  effective tails
  diagnostic identities

Excluded
  active preset id / display name / Custom label
  raw generation state / raw adjustment / base identity
  history / selection / notice / playback
```

## 11. テスト方針

### 11.1 B4専用core test

`tests/test_ms22_b4_generation_history.py`で次を検証する。

- GenerationState / OutputEditStateのimmutability、type、identity mismatch拒否
- history initialize、no-op、commit、Undo / Redo、new commit時redo破棄、50 / 51件境界
- before / after base mismatch拒否
- event gesture同key coalescing、key変更 / preset / direct editのdiscrete boundary
- adjustmentだけ、generationだけ、両方が変わるtransactionのfull-state復元
- active settingsと同値の明示tail / mode override保持、decay中latent tail保持
- missing preset normalization時にsettings保持・id None、extra historyを作らないこと
- deleted / mismatched presetをUndo / Redoした後、history endpointをatomicに正規化し、同値transactionの除去と
  反対方向navigationのinvariant維持を行うこと
- settings同値・id異値のpreset applyは1 transaction、同じsettings / idの再適用はno-opであること

### 11.2 B4専用wx test

`tests/test_wx_ms22_b4_generation_state.py`で次を検証する。

- temporary storeを注入したstartup INI + valid built-in / user / Custom resolution、invalid user JSON時built-in維持
- controller constructorはload / saveせず、startup testがrepository既定INI / `presets.json`を変更しないこと
- `AutoLipToolApp`から同じtemporary settings / preset storeがcontrollerへ渡るstartup seamと、default path未使用を検証すること
- baseなしdirect editはhistoryなし、baseありdirect editは1 transaction
- active preset中のsettings同値direct eventはid保持、resolver / history / INI保存要求なし
- preset applyはadjustment / base / selectionを保持し、Undo / Redoでsettings + idを復元
- startup / direct edit / preset / Undo / Redo後にhold / softness controlがcanonical stateと一致すること
- candidate resolve拒否時にcontrolをcurrent canonical値へ戻し、projection eventが再commitされないこと
- closing hold / softness変更が再解析を要求せず、Preview / diagnostics / VMD準備を更新
- morph upper変更だけがanalysis invalidationを行う
- non-no-op generation / preset / Undo / Redoごとのresolver call count 1と同一context共有
- stale shape-parameter hint拒否（candidate `None` adjustmentをempty snapshotへcanonicalizeし、non-empty hintを拒否する場合を含む）、
  resolve failure時state非変更
- commit後INI保存要求、save失敗時state / history非rollback、後続要求 / close flushの`attempted=False`
- success new base、failure / cancel rollback、morph mismatch、input、reset、late callback
- generation state単独では`has_workspace_user_data`がfalseで、新規作業確認対象にならないこと
- deleted / mismatched active presetをUndo / RedoでCustomへ正規化
- selected event editorのcore / wx回帰と、B3 pipeline-preview integration回帰を維持すること
- Busy / dirty editor / stale identity requestがstateを変更しないこと
- Edit menu、tooltip、完了noticeがgeneration変更を含む「出力編集」表現であること

### 11.3 diagnostics / fingerprint回帰

- summaryのactive mode、id、display name、hold / decay run count、override countを検証する。
- summary DTOのmode、run count、id / display name pair、override countのvalidation invariantを検証する。
- 未確定Noneと確定0を区別する。
- Infoとreportが同じstructured値を表示する。
- id / display nameだけの変更ではfingerprintが同一でWARNING確認を再利用する。
- effective frames / tailsが変わるgeneration変更ではfingerprintが変わり、WARNING確認を再利用しない。
- fingerprint payload field / order / schemaがMS21の既存期待値から変わらない。

### 11.4 実装時の指定command

各commandは一つずつ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b4_generation_history.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms22_b4_generation_state.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b6_adjustment_history.py tests\test_wx_ms21_b6_undo_redo.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms21_b7_state_integration.py tests\test_ms21_b7_analysis_rollback.py tests\test_ms21_b7_ui_sync_context.py tests\test_wx_ms21_b7_sync_efficiency.py tests\test_ms21_b7_audio_worker_terminal.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms20_b2_output_diagnostics.py tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b3_right_pane_info.py tests\test_ms20_b6_diagnostic_report.py tests\test_ms20_b7_diagnostics_state_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms20_b5_warning_save_policy.py tests\test_ms20_b6_report_save_flow.py tests\test_ms21_b5_effective_output_identity.py tests\test_ms21_b5_adjusted_vmd_save.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b5_export.py tests\test_ms22_b3_generation_presets.py tests\test_settings_store.py tests\test_ms22_b2_long_vowel_resolver.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms13_integration.py tests\test_wx_startup_splash.py tests\test_ms19_b8_workspace_reset.py tests\test_ms22_b2_import_boundaries.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b7_import_boundaries.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b4_selected_event_editor.py tests\test_wx_ms21_b4_selected_event_editor.py tests\test_ms21_b3_pipeline_preview_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

pytestはpass件数、failure / error表示、process exit codeを分けて記録する。wx processがpass表示後に
nonzero終了した場合も自動的にpass扱いせず、既知終了処理問題か新規回帰かを分離する。

### 11.5 計画作成baseline

2026-08-08にproduction / test非変更で次を実行した。

- B3 settings / preset、MS21 history、B2 resolver: 53 passed、19 subtests passed、process exit code 0
- wx history / state / rollback / sync / terminal: 22 passed、process exit code 0
- diagnostics / report / effective output / VMD save: 62 passed、process exit code 0
- RightPane parameter / warning / report save / INI caller: 43 passed、process exit code 0
- 合計: 180 passed、19 subtests passed。failure / error表示なし、全process exit code 0
- 自己回帰チェック追加対象（startup / workspace reset / B2・B7 import boundary）: 19 passed、
  process exit code 0。追加対象を含む合計は199 passed、19 subtests passed

### 11.6 実装・修正・自動検証結果

- 2026-08-09にB4 production code / test codeを実装し、state / history / startup / lifecycle / diagnostics統合と
  P2 / P3修正後のcode checkを完了した。
- 手動確認で解析成功後に母音Previewが表示されない問題が判明した。分析開始からworker、terminal callback、
  `UiState`、同期context、Previewまでを再確認し、RMS補正後に別母音を挟んだ同一モーフが1フレーム重複して
  shared resolverのrequired-zero conflictとなる原因を特定した。
- post-B4 repairとして`src/core/pipeline.py`の自動生成timelineだけを限定補正した。raw conflictを拒否する
  B2 fail-closed resolver契約は維持し、同一モーフ境界とwx Previewの回帰testを追加した。
- 修正後の関連testは33 passed、full suiteは686 passed、26 subtests passed、failure / error表示なし、
  各process exit code 0だった。`compileall src tests`と`git diff --check`もprocess exit code 0だった。
- 実入力・実Whisperでは272 timing eventから205 shapeを解決し、programmatic wx flowで
  `analysis_valid=True`、sync contextあり、Preview valid、205 segments、failureなしを確認した。

### 11.7 diff / scope監査

- B4本体のproduction diffは§7のstate / history / startup / lifecycle / diagnostics integrationに限定した。
- §11.6のpost-B4 repairだけは、手動確認で判明したPreview表示不能を解消するため、B2所有の
  `src/core/pipeline.py`と同一モーフ境界回帰testを限定変更した。
- B5のRightPane preset / mode UI、B6のend-user docsを先行実装しない。
- B2 resolver semantics、B3 JSON schema / built-in definition、MS21 fingerprint payloadを変更しない。
- existing testを削除・skip・期待値弱化していない。output-only化に伴う期待値変更は、morph upper回帰と
  base保持回帰を追加して意味を移す。
- dependency、package、license、fixed morph、30fps、VMD、audio、network契約に変更がない。

### 11.8 手動確認・MMD確認

- 2026-08-09にユーザーから、母音Preview問題の解消とMS22-B4手動テスト通過が報告された。
- 上記はユーザー実施の手動GUI確認を証拠として記録し、Codex自身のGUI手動実行とは扱わない。
- B5 preset UI / mode controlは未実装なので、B4完了時にpreset UIのユーザー確認済みとは記録しない。
- 実MMDでのVMD / WAV読み込み・リップ同期はMS26へ維持する。

## 12. 受け入れ条件

- `GenerationState`がbaseなしでも有効で、startup、input変更、workspace resetで保持される。
- `OutputEditState`がbase確定時だけ存在し、base / adjustment identityとgeneration stateのinvariantを守る。
- adjustment、generation settings、active preset idが最大50件の一つのhistoryでatomicにUndo / Redoされる。
- event gesture coalescing、redo discard、dirty editor、selection、Edit menu shortcutのMS21契約を維持し、
  menu / tooltip / noticeはgeneration変更も含む「出力編集」表現を使用する。
- non-no-op preset applyはbase / adjustment / selectionを保持し、1回のdiscrete transactionとresolver 1回で
  反映される。同じsettings / idの再適用はhistory / resolver / INI保存要求なしのno-opである。
- active preset中のsettings同値direct eventはpreset idを保持する完全no-opであり、settingsが変わった場合だけ
  Customへ移る。settings同値・id異値のpreset applyはid-only transactionとして扱う。
- direct closing hold / softness / long mode変更はbaseを破棄せず、current effective outputだけを再構築する。
- startup / direct edit / preset / Undo / Redo / rollback後のhold / softness controlはcanonical generation stateと
  一致し、投影eventは再commitを発生させない。candidate拒否時も旧canonical値へ戻る。
- morph upper変更だけがanalysis invalidation / parameter mismatch guardを発生させる。
- candidate resolve失敗、Busy、stale request、late callbackでcurrent output / history / INI pending stateを変更しない。
- resolver hintは`EffectiveShapePlan.shape_parameters`を唯一のprovenanceとしてbase identity、adjustment、
  shape parametersの一致を検証し、stale generation hintを受理しない。
- candidate adjustment `None`はempty snapshotへ正規化して比較し、non-empty hintをwildcardとして受理しない。
- Preview、editor、diagnostics、saveability、VMD保存がcommit時の同じimmutable contextを使用する。
- current context cacheはOutputEditState全体へ照合し、base identityだけが同じstale generation contextを再利用しない。
- non-no-op direct edit / preset / Undo / Redo後にINI保存要求を出し、保存失敗でもlast-valid in-memory state /
  historyを維持する。save-disabled後の後続要求 / close flushは`attempted=False`で再保存しない。
- controller constructorは永続化I/Oを行わず、startup testはtemporary storeを注入してrepository既定INI / preset
  fileを変更しない。
- `AutoLipToolApp`からcontrollerへのstore注入経路が一意で、startup testが同じtemporary instanceを使う。
- startup active id missing / mismatchはINI settingsを保持してCustomへ正規化し、matching built-in / userだけを保持する。
- Undo / Redo時にpresetがdeleted / mismatchedならsettingsを保持してCustomへ正規化し、移動対象transactionの両endpointを
  atomicに整合させる。正規化後同値なら追加transactionなしで除去する。
- active generation settingsと同値の明示override、decay中latent tailをpreset変更前後で失わない。
- analysis success、failure、cancel、morph mismatch、input、reset、late callbackが§10.3 lifecycle matrixどおりである。
- app-level generation state単独はworkspace user dataに数えず、新規作業確認を発生させない。
- generation summaryにactive mode / preset / hold・decay run数、adjustment summaryにmode override数を持つ。
- diagnostics DTOはmode、run count、active id / display name pair、override countの不変条件をconstructorで拒否・保証する。
- 未確定run数`None`と確定済み0件を区別し、Info / reportが同じstructured summaryを使う。
- active preset identityだけではfingerprintを変えず、effective output変更時は既存WARNING確認を再利用しない。
- fingerprint payload / field順 / schema `ms21-effective-output-v1`を維持する。
- B4専用test、指定回帰、full suite、compileall、diff checkの表示結果とexit codeを記録する。
- B5 UI、B6 documentation closeout、dependency / package、実MMD確認を先行完了扱いにしない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| adjustmentとgenerationを別historyへcommitして部分Undoになる | OutputEditState全体だけをwx canonical historyにし、live二重historyを禁止する |
| generation stateをUiStateとhistoryで二重正本化する | base確定中の同値invariantとatomic installをconstructor / testで固定する |
| old generationで解決したhintがidentity一致だけで通る | EffectiveShapePlanをShapeParameters provenanceの唯一の所有先にし、hintの3点一致を検証する |
| resolver後にstate commitが失敗しUIが不一致になる | immutable candidateを検証し、resolve成功後だけ一括install、同じcontextでsyncする |
| hold / softness変更でbase / adjustmentを失う | handlerをmorph upperから分離し、output-only base保持回帰を追加する |
| EVT_TEXT / spinの同値eventでactive preset idが消える | settings比較をCustom化より先に行い、id保持の完全no-opとして処理する |
| stateをcontrolへ投影したeventが再commitされる | projection guardを設け、拒否時もcanonical値をguard付きで再投影する |
| deleted preset idをUndoで復活表示する | restore時にcurrent storeでresolveし、settings保持・id Noneへ正規化する |
| preset削除後のUndo / Redoでhistory endpointがcurrentと不一致になる | navigation中にbefore / afterをatomicに正規化し、同値transactionを追加履歴なしで除去する |
| appとcontrollerのstore instanceが分かれて状態がずれる | controllerをsingle ownerとし、app.pyの重複loadを撤去する |
| AutoLipToolAppのstartupがcontrollerと別storeを使いrepository fileへ書き込む | App→controllerの注入seamを固定し、startup testは同一temporary instanceとdefault path不変を検証する |
| startup testがrepository既定INI / preset fileを変更する | injectable storeとI/Oなしconstructorを固定し、temporary pathだけでtestする |
| INI保存失敗でUndo済みstateを戻してしまう | in-memory commit先行、coalesced save失敗非rollbackを固定する |
| generation変更のUndoを「個別補正」と誤表示する | Edit menu、tooltip、noticeを「出力編集」へ統一する |
| summary field追加でfingerprint schemaが変わる | payload builderを非変更対象にし、canonical payload snapshot回帰を維持する |
| diagnostics summaryの不正なmode / count / id表示が混入する | DTO constructorでmode、非負count、id / display name pairの不変条件を検証する |
| B4でpreset UIまで膨らむ | controller / frame APIだけを実装し、RightPane / selected editorの新controlはB5へ残す |
| rollback guardからhold / softnessを外してmorph upperまで漏れる | AnalysisParameterSnapshotをmorph upper単独で明示し、mismatch回帰をmorph upperへ移す |

## 14. Codex 実装時の注意

- 実装前に本planを現行HEADへ再照合し、P1 / P2 / P3を解消してからproduction codeへ進む。
- commandは一つずつ実行し、既存変更・未追跡fileをユーザー所有として保護する。
- `GenerationSettings`、`AdjustmentLayerSnapshot`、`EffectiveShapePlan`を表示controlやmutable dictへ置き換えない。
- candidate resolve失敗を例外握り潰しで成功扱いにせず、state非変更のfail-closedとしてtestする。
- test期待値をoutput-only仕様へ更新するとき、旧再解析期待を単に削除せず、base / adjustment保持と
  morph upper invalidationの両方を検証する。
- B5のGUIを追加せず、B5が利用するstate / controller APIのみに留める。
- Qt / PySide6、network、external ASR、自動download、新dependencyを追加しない。
- fixed morph、30fps、VMD形式、audio contract、B3 JSON schemaを変更しない。
- 完了時は確認ファイル、変更ファイル、実装、test、仕様逸脱、残課題、B5への引き継ぎを報告する。
