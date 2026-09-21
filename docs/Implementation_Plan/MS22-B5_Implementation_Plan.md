# MS22-B5 Implementation Plan

## 1. 文書情報

- 文書名: `MS22-B5 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS22-B5_Implementation_Plan.md`
- 対象Block: `MS22-B5 Preset UI / Event Override Flow`
- 基準ブランチ: `feature/MS21-implementation`
- 計画作成基準HEAD: `624a9a8 Implement MS22-B4 output state and preview repair`
- 作成日: 2026-08-09
- 文書ステータス: **Implemented / B5 Code Check Passed / User Manual Test Passed / B6でsplash P3解消済み (2026-08-11)**
- 直接依存:
  - MS21 Closeout A
  - MS22-B1 Contract Fixed
  - MS22-B2 Implemented / Code Check Passed
  - MS22-B3 Implemented / Code Check Passed
  - MS22-B4 Implemented / Code Check Passed / User Manual Test Passed
- 次工程: MS22-B6 Lifecycle Regression / Documentation
- 上位正本:
  - `docs/Implementation_Plan/MS22_Block_Breakdown.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/Pipeline_Data_Contract_Specification.md`

本書は、MS22-B3で実装済みのpreset storeとMS22-B4で実装済みのoutput state / history APIを、
既存wxPython GUIから安全に操作するための実装計画である。本書の作成段階ではproduction code、
test code、GUI、INI本体、`presets.json`本体、依存関係、build設定を変更しない。

2026-08-09の実装状態整合レビューではP1なし、P2 3件、P3 2件を検出した。active preset mutation後の
Custom正規化、load / mutation別error matrix、preset request DTO、B4 history直接回帰、selector fallbackを
本書へ反映して解消した。修正確認ではB3 / B4 state・history関連35件、B2 resolver / selected editor関連32件が
pass表示・各process exit code 0だった。これは計画レビューの証拠であり、B5実装済みの証拠ではない。

2026-08-10にB5 production codeとB5専用testを実装した。B5専用test 10件、スプラッシュテストを除く
既存全体回帰694件はpass表示・process exit code 0、`compileall src tests`と`git diff --check`もexit code 0だった。
全体実行では既存の`tests/test_wx_startup_splash.py`が起動時間条件により1件失敗したが、同テスト単独は2件passであり、
B5変更対象外の既存テストである。ユーザーによるB5手動GUI確認は通過した。
実MMDでのVMD / WAV読み込み・リップ同期確認はMS26へ、横断lifecycle回帰と文書正本同期はMS22-B6へ引き継ぐ。

2026-08-11のB7計画レビューで、上記splash P3のcurrent statusが未同期であることを確認した。
B6ではsplash 3件、B4 / B5 / splash既知組合せ18件、full suite 713件をすべてpass表示・process exit code 0で
確認しているため、B5時点の失敗記録は履歴として保持し、現在状態を「B6で解消済み」へ更新した。

## 2. 背景

MS22-B3では、次のUI非依存契約が確定している。

- immutable `GenerationSettings`（`closing_hold_frames`、`closing_softness_frames`、
  `long_vowel_mode`）
- 組み込みpreset `標準（長音維持）` と `長音減衰`
- user presetのschema version 1、stable UUID、表示名、最大100件
- `GenerationPresetStore`のcreate / update / delete、strict validation、atomic write
- invalid JSON、unsupported schema、write / replace failure時のbuilt-in維持とuser mutation停止
- `SettingsStore`のINI active settings / active preset id保存、およびCustom fallback

MS22-B4では、これらを次のwx側stateへ接続済みである。

- baseなしでも有効な`GenerationState`
- base確定中の`OutputEditState`
- adjustment、generation settings、active preset idを一体で扱う最大50件history
- preset apply、direct generation setting変更、Undo / Redo後のresolve-before-commitとPreview / writer / diagnostics同期
- `AppController`へのsingle settings / preset store注入とstartup load
- `MainFrame.apply_preset_generation()` と `commit_generation_settings()`
- active mode / preset、effective hold / decay run数、mode override数を含むdiagnostics summary

一方、現行GUIには次の未実装境界が残っている。

- `RightPane`の`プリセット`タブは後続対応予定のStaticTextだけを表示する。
- preset一覧のbuilt-in / user / Custom区別、選択、適用、作成、更新、名前変更、削除UIがない。
- `SelectedEventEditorState`と`RightPane`は`long_vowel_mode`のterminal event overrideを表示・編集しない。
- `EventAdjustment`、shared resolver、B4 historyはmode overrideを既に受け取れるが、GUIからの入力入口がない。
- B4のpreset apply APIは存在するが、user store mutationの結果、失敗通知、再描画、active preset消失時のUI正規化が未接続である。

B5はこのGUI導線だけを実装し、B2のlong-vowel semantics、B3のJSON schema、B4のstate/history契約を再実装しない。

## 3. 目的

1. RightPaneの`プリセット`タブからbuilt-in / user / Customの状態を混同せず表示する。
2. presetの明示適用を、再解析なしのB4 output edit transactionとしてPreview、VMD準備、diagnosticsへ反映する。
3. user presetの作成・更新・名前変更・削除を、`GenerationPresetStore`のvalidationとatomic persistenceへ接続する。
4. invalid JSON、保存失敗、上限超過、built-in read-only、missing presetを回復可能なUI通知として表示する。
5. 長音terminal continuation eventだけに`hold / decay / 継承`のmode overrideを追加し、B2の優先順位とdecay終端zeroを守る。
6. active preset更新・削除、Undo / Redo、selection、dirty input、Busy、stale callback、theme、tab behaviorを既存契約のまま維持する。

## 4. In Scope

### 4.1 Preset tab

- `RightPane`の`プリセット`タブ本実装
- 現在のgeneration settings、active preset id / display name、source（built-in / user / Custom）の表示
- `Custom`を現在値の表示状態として扱う選択肢または同等の明示表示
- stable idを内部値とするpreset selector。表示名をidentityとして使用しない
- built-inとuserの表示区別
- presetの明示選択と明示Applyの分離
- user presetの作成、更新、名前変更、削除ダイアログ
- 作成・更新時の表示名、hold、softness、long-vowel modeの入力
- built-inの編集・削除不可表示
- user preset上限100件、重複名、空名、範囲外、invalid modeの表示
- JSON load / write / replace failure、store unavailableの非モーダル通知
- Busy中のselector、Apply、管理操作のロック
- theme、tab order、scroll、既存RightPaneレイアウトの維持

### 4.2 Preset適用とstate接続

- B4 `AppController.apply_generation_preset()`の利用または最小のlookup helper追加
- preset apply前のBusy、stale、selected event dirty input検証
- B4 `commit_generation_settings()`によるresolve-before-commit、history transaction、同期
- apply後のactive preset display、ParameterPanel、Preview、selected event、Info / Warning、saveabilityの同時更新
- 同一settings / 同一idの再適用no-op
- 同一settings / id異値のid-only transaction
- preset applyで入力、timing plan、個別adjustment、selection、viewport、playbackを消去しない
- apply失敗時のstate、history、Preview、現在のpreset一覧の不変

### 4.3 User preset mutation

- `GenerationPresetStore.create()`、`update()`、`delete()`へのcontroller経由接続
- mutation成功後の一覧再構築とpanel selection復元
- mutation失敗時の旧一覧・旧JSON・現在のoutput state保持
- createはcurrent outputを変更せず、作成したpresetを選択可能な一覧へ追加する
- updateはcurrent outputへ自動適用せず、明示Applyを要求する
- active user presetのupdateでsettingsが変わる場合、現在のoutput settingsを保持し、active idをCustomへ正規化する
- active user presetのupdateでsettingsが同じ場合、active idを保持し、表示名だけ更新する
- active user presetのdeleteでは現在のoutput settingsを保持し、active idをCustomへ正規化する
- deleted / mismatched presetをUndo / Redoで再表示・再適用しない。B4のendpoint normalizationを利用する
- mutation後に`presets.json`の再loadを要求せず、成功resultのimmutable user preset tupleをpanelへ反映する

### 4.4 Long-vowel terminal event override

- `SelectedEventEditorState`へのmode override表示情報追加
- `SelectedEventEditRequest` / merge / resetへの`long_vowel_mode`対応
- UI選択値 `継承`（`None`）、`hold`、`decay`のprimitive mapping
- 長音runのterminal continuation eventだけを操作可能とする
- source event、intermediate continuation event、非長音event、synthetic eventでは操作不可
- active generation settingsと明示overrideの優先順位表示
- `hold`では既存hold / softness / slope controlを有効化
- `decay`ではtail controlを無効化し、終端zeroを守る理由を表示
- decay中も既存のhold / softness / slopeのlatent overrideをsnapshotへ保持し、holdへ戻したとき再利用する
- resetでmode overrideを`None`へ戻し、既存event adjustment全体をB4 history transactionとして復元する
- mode変更後にPreview、VMD準備、diagnostics、fingerprintを同じeffective contextで更新する

### 4.5 最小manual GUI確認

- preset tabの表示・選択・Apply
- built-in / user / Custom区別
- user preset create / update / rename / delete
- invalid / failure noticeとbuilt-in継続利用
- 長音terminal eventの継承・hold・decay、decay tail無効化、reset
- non-terminal / non-long eventでmode controlが無効であること
- Undo / Redo、Busy、dirty input、theme、tab / scroll維持

## 5. Out of Scope

- B2 shared resolver、hold / decay shape semantics、decay終端exact `0.0`の変更
- `ー`のない同音母音列からの長音推論、音響的長音推定、歌唱専用algorithm
- `GenerationSettings`、`presets.json` schema version 1、user preset上限100件の変更
- presetのimport / export、drag reorder、cloud sharing、generic preset editor framework
- preset値への`morph_upper_limit`、model profile、morph name mappingの追加
- non-long eventへのmode control表示、terminal zero規則の緩和
- 任意キーフレーム編集、VMD読み戻し、複数event一括編集、adjustmentのdisk保存
- MS22-B6の横断lifecycle回帰、README / 配布用readme / 3正本仕様の実装後同期
- MS22-B7 Closeout、package / release / tag / merge / push
- 実MMDでのVMD / WAV読み込み・リップ同期確認（MS26）
- Qt / PySide6、外部ASR、外部音声送信、background通信、Whisper自動download、新規依存
- 固定モーフ`あ / い / う / え / お`、30fps、VMD形式、音声三役契約の変更

## 6. 前提条件

- MS21 Closeout A、MS22-B1〜B4の完了状態を未完了へ戻さない。
- `GenerationSettings`はB3のimmutable DTOを再利用し、GUI側で別のsettings schemaを作らない。
- `GenerationPresetStore`の公開mutation resultを使用し、private collection、JSON payload、temporary fileをGUIから直接操作しない。
- built-inは読み取り専用で、`presets.json`へ複製・編集しない。
- active preset idのidentityはstable idであり、表示名変更で別presetにならない。
- active presetのsettings不一致・missing・deletedは、INI settingsまたは現在のoutput settingsを失わずCustomへ正規化する。
- preset update / delete失敗では現在のoutput stateを変更しない。
- preset applyは明示操作であり、selector変更だけではoutput stateを変更しない。
- output state変更前にselected eventの未確定入力を検査し、入力を黙って破棄しない。
- Busy中のpreset操作とmode override操作は拒否し、Busy解除後に自動再送しない。
- `EventAdjustment.long_vowel_mode`の`None`はinherit、`hold | decay`は明示overrideである。
- event別mode overrideはterminal continuation eventだけに許可する。
- decayではtail controlをUIで無効化するが、latent overrideを消去しない。
- Preview、selected editor、diagnostics、VMD保存は同一`EffectiveShapePlan` / `UiSyncContext`を使用する。
- commandは一つずつ実行し、既存変更、未追跡ファイル、ユーザー手動確認の境界を保護する。
- 実装開始前に本planと現行HEADを再照合し、P1 / P2 / P3を解消する。

## 7. 対象ファイル

### 7.1 production code主変更対象

| ファイル | B5で担当する責務 |
| --- | --- |
| `src/gui_wx/right_pane.py` | preset tab controls、preset panel state / request DTO、mutation notice、mode choice、decay tail notice、theme / layout / Busy反映 |
| `src/gui_wx/main_frame.py` | RightPane callback接続、canonical stateからpanelを同期、preset apply / mutationのguard、selected event mode commit、active preset normalization |
| `src/gui_wx/selected_event_editor.py` | terminal long-vowel modeのeditor state、request validation、mode merge / reset、hold / decay表示用derived state |
| `src/gui_wx/app_controller.py` | preset lookup、create / update / delete request、load / mutation resultのcontroller経由通知、store ownership維持 |

### 7.2 条件付きproduction code

| ファイル | 条件 |
| --- | --- |
| `src/core/generation_presets.py` | controllerの公開APIだけでstable-id lookupを表現できない場合に限り、pureなlookup helperをadditiveに追加する。JSON schema、mutation semantics、built-in定義は変更しない。 |
| `src/gui_wx/ui_state.py` | panel revisionをMainFrame / RightPaneだけで安全に保持できない場合に限り、canonical generation stateを二重化しないUI revisionまたはnotice保持を最小追加する。history DTOは変更しない。 |
| `src/gui_wx/theme.py` | 既存paletteの利用だけでpreset controlのtheme追従が満たせない場合に限り、既存色の再利用を前提に最小補助を追加する。 |

### 7.3 読み取り確認対象

- `src/core/generation_presets.py`
- `src/core/event_adjustment.py`
- `src/core/effective_shape_plan.py`
- `src/core/output_edit_state.py`
- `src/core/event_adjustment_history.py`
- `src/gui_wx/ui_sync_context.py`
- `src/gui_wx/parameter_panel.py`
- `src/gui_wx/app.py`
- `src/gui_wx/output_diagnostics_adapter.py`

### 7.4 B5で新規作成するtest

- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_wx_ms22_b5_long_vowel_override.py`

### 7.5 変更・回帰対象test

- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_wx_ms21_b7_state_integration.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_wx_ms22_b4_generation_state.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms21_b7_import_boundaries.py`

### 7.6 B5では変更しない文書・成果物

- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `MMD_AutoLipTool.spec`
- `build.ps1`
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`

B5の計画・進捗記録は、本plan、`MS22_Block_Breakdown.md`、`MS20_and_Beyond_Index.md`、
`MS20_and_Beyond_Roadmap.md`へ反映する。end-user docsと正本仕様のimplemented同期はB6で行う。

## 8. 実装方針

### 8.1 UIとcoreの責務分離

- RightPaneはpreset storeのJSONやprivate collectionを読まず、MainFrame / AppControllerから渡されたimmutableな表示stateだけを描画する。
- `GenerationPreset`のid、display name、source、GenerationSettingsをpanel itemへ投影する。表示名を選択identityにしない。
- UIの選択状態とactive output stateを分離する。selector変更は一覧上の選択だけを変更し、Applyで初めてB4 stateを変更する。
- controllerはstoreのload / mutation / lookupを所有し、MainFrameはcanonical output stateと表示同期を所有する。
- resolver、fingerprint、diagnostics、VMD writerをUIから直接呼び出さず、既存B4の`commit_generation_settings()`と`sync_ui_state()`を経由する。

### 8.2 Preset panel表示契約

panelへ渡す表示stateは、少なくとも次を含む。

```text
PresetPanelItem (immutable)
  id: str
  display_name: str
  source: built_in | user
  generation_settings: GenerationSettings

PresetPanelState (immutable)
  items: tuple[PresetPanelItem, ...]
  selected_preset_id: str | None
  active_preset_id: str | None
  active_preset_display_name: str | None
  active_generation_settings: GenerationSettings
  mutation_available: bool
  load_error_code: str | None
  load_error_message: str | None
  busy: bool
  panel_revision: int
```

RightPaneからMainFrameへ渡すrequestは、表示stateとは別のimmutable DTOとする。

```text
PresetSelectRequest
  selected_preset_id: str | None
  expected_panel_revision: int

PresetApplyRequest
  preset_id: str
  expected_panel_revision: int
  expected_editor_revision: int

PresetCreateRequest
  display_name: str
  generation_settings: GenerationSettings
  expected_panel_revision: int

PresetUpdateRequest
  preset_id: str
  display_name: str
  generation_settings: GenerationSettings
  expected_panel_revision: int
  expected_editor_revision: int

PresetDeleteRequest
  preset_id: str
  expected_panel_revision: int
  expected_editor_revision: int
```

- `active_preset_id is None`かつdisplay nameもNoneの場合はCustomと表示する。
- `selected_preset_id`はselectorの選択だけを表し、active idと自動同期しない場合がある。
- built-in / userのsourceは表示ラベルと編集可否へ投影するが、idのprefix判定をUIの唯一の正本にしない。
- mutation unavailableでもbuilt-in itemとApplyは使用できる。user create / update / deleteだけを無効化する。
- load errorはpanel内noticeへ表示し、既存built-inと現在のsettingsを消去しない。
- panel revisionはUIイベントのstale guardに使うが、GenerationStateやhistoryの代替にしない。
- MainFrameはrequest受理時にexpected revision、Busy、current selection、selected editor dirty inputを再確認する。
  Createはoutput stateを変更しないためeditor revisionを持たず、Apply / Update / Deleteはactive identityを
  変更し得るためeditor revision不一致を拒否する。

### 8.3 Preset操作契約

#### Select

- selector変更は`selected_preset_id`だけを更新する。
- `Custom`を選択した場合は現在settingsを保持し、既存outputへresetやdefault再適用を行わない。
- 選択内容のsettings previewはpanel内へ表示するが、Preview、diagnostics、INI、historyは変更しない。
- 一覧再構築後もselected idが存在すれば選択を保持する。selected idが消失した場合は、存在するactive preset、
  Customの順でfallbackする。表示名や先頭行を暗黙のidentity fallbackにしない。

#### Apply

- Applyはselectorのstable idをcontrollerへ渡す。stale / missing idはstore current collectionで再検証する。
- Busy中、selected editor dirty input中、panel revision不一致、preset missingではstateを変更しない。
- built-in / userのsettingsとidを`MainFrame.apply_preset_generation()`へ渡し、B4のresolve-before-commitを一回だけ実行する。
- settingsが同じでidも同じならno-opとし、resolver、history、INI save要求を発生させない。
- settingsが同じでidだけ異なる場合はid-only transactionとし、effective outputが同じならfingerprint / WARNING確認を再利用する。
- settingsが変わる場合はbase、timing plan、adjustment、selectionを保持したoutput transactionを1件作り、Preview / writer / diagnosticsを同じcontextで更新する。
- apply成功後だけactive display、ParameterPanel、selector、noticeをcanonical stateへ投影する。
- apply失敗時は旧state、旧history、旧selection、旧panel selectionを維持し、原因をpanel noticeへ表示する。

#### Create

- Create dialogの初期値はcurrent active generation settingsとする。
- display nameはB3 storeの1〜100文字、single-line、control character禁止、重複禁止を利用する。
- modeはprimitive `hold / decay`から選ぶ。GUIで独自enumや別schemaを作らない。
- create成功は一覧へ追加したpresetをselector上で選択するがApplyは行わず、active output、history、Previewを変更しない。
- create失敗は旧一覧と旧JSONを維持し、`PresetMutationResult.error_code`に対応する日本語noticeを表示する。

#### Update / rename

- user presetだけを対象とし、built-inはdialogをread-only表示する。
- update dialogは対象idをstableに保持し、表示名だけの変更とsettings変更を区別しない一つのstore updateとして送る。
- active user presetを同じsettingsでrenameした場合はeffective resolver、history、INI保存要求を発生させず、
  preset panel、Info / diagnostics、report用active display nameだけをstore resolutionから再同期する。
- active user presetのsettingsが変わった場合は現在のoutput settingsを自動変更せず、active idをCustomへ正規化してから再描画する。新settingsを使う場合は明示Applyする。
- inactive user presetのupdateはoutput stateを変更しない。
- update成功後はstable idが残るため、対象がselectedなら同じidの選択を保持する。
- update失敗ではstore一覧、active output、history、Previewを変更しない。

#### Delete

- built-in deleteはdisabled表示とし、stale requestもstoreで拒否する。
- user preset delete成功後、削除対象がactive idなら現在settingsを保持してactive idをCustomへ正規化する。
- active idのCustom正規化はB4 output history全endpointまたはbaseなしGenerationStateのatomic normalizationとして
  行い、追加transactionを作らずdeleted idをhistory endpointへ残さない。
- delete後のUndo / Redoは削除済みpresetを復活表示・再適用せず、B4 normalizationによりCustomへ収束する。
- delete対象がselectedなら、削除後も存在するactive preset、Customの順でselectorをfallbackする。非選択presetの
  deleteではcurrent selectionを保持する。
- delete失敗では一覧、active output、history、Previewを変更しない。

### 8.4 User preset mutationとoutput stateの境界

`presets.json`のatomic mutationとB4 in-memory output stateは別の失敗境界である。B5では次の順序を固定する。

1. UI入力、expected panel revision、必要なexpected editor revision、Busy、dirty inputをstore mutation前に検証する。
2. create / update / deleteはstoreへ送り、成功resultを得るまでoutput stateを変更しない。
3. mutation failureでは旧user preset tuple、旧JSON、output state、history、Preview、INIを変更しない。resultの
   `mutation_available`だけをpanel action stateへ反映する。
4. mutation成功後はsuccess resultのtupleを新しいstore正本としてpanel itemsを再構築し、current
   `GenerationState`のsettingsとactive idを`resolve_active()`で再解決する。
5. active idが同じsettingsで有効な場合はoutput stateを変更しない。rename時はstore由来display name、panel、
   Info / diagnostics / report表示だけを同期し、effective resolver、history、INI保存要求を発生させない。
6. active idがmissingまたはsettings mismatchになった場合は、effective resolverを呼ばず、settingsを保持したまま
   active idだけをNoneへ正規化する。
   - base-bound `OutputEditHistoryState`がある場合は`UiState.normalize_output_edit_history()`を使用し、pending editを
     先にsettleしたうえでcurrent、undo / redo transactionのbefore / after endpointを同じcurrent store resolutionで
     一括正規化する。
     id消失だけで同値になったtransactionはB4契約どおり追加履歴なしで除去する。
   - historyがない場合は、同じ`GenerationSettings`とactive id Noneの`GenerationState`を直接installする。
   - どちらも`_active_preset_display_name=None`、Custom表示、panel / Info / diagnostics同期、INI保存要求1回を行う。
7. preset Applyだけがstore lookup成功後にB4 `commit_generation_settings()`を使用し、settings変更時の
   effective resolver / output transactionを実行する。

mutation後のidentity正規化はeffective outputを変えないため、resolver failureを後段の通常分岐にしない。これにより、
JSON更新済みなのにdeleted idがcurrent stateやhistory endpointへ残る状態と、JSON書き換え失敗によるPreview消失を防ぐ。

### 8.5 Long-vowel mode editor

`SelectedEventEditorState`へ次のderived informationを追加する。

```text
long_vowel_mode_enabled: bool
requested_long_vowel_mode: str | None
effective_long_vowel_mode: str | None
long_vowel_mode_overridden: bool
long_vowel_mode_notice: str
tail_controls_enabled: bool
```

- `SelectedEventEditRequest.value`はB5で`float | int | str | None`へadditiveに拡張し、
  `long_vowel_mode`だけ`None | "hold" | "decay"`を許可する。numeric fieldへstr、mode fieldへ数値や
  空文字を渡したrequestはcontract errorとして拒否する。
- mode choiceは一回のdiscrete history transactionとし、`coalescing_token`を常にNoneにする。
  `SelectedEventEditBoundaryRequest`とgesture coalescing対象へ`long_vowel_mode`を追加しない。

- `effective_plan.long_vowel_runs`でselected eventがterminal continuationかを判定する。
- terminal eventでは`requested_long_vowel_mode`がNoneなら`継承`、非Noneなら明示modeとして表示する。
- effective modeはrunの`resolved_mode`から表示し、UIで再計算しない。
- terminal以外ではmode controlを無効化し、理由を表示する。requestを作成してもMainFrameとresolverの両方で拒否する。
- `hold`では既存tail controlを有効化する。
- `decay`ではhold / softness / slopeを無効化し、次のnoticeを表示する。
  `decayでは長音終端を0へ減衰させるため、閉口設定は一時的に反映されません。holdへ戻すと保持済みの設定を再利用します。`
- decay中のlatent hold / softness / slopeは`EventAdjustment`へ残し、modeをholdへ変更した時に消さない。
- resetはmode overrideをNoneへ戻し、既存のevent adjustment resetと同一transactionへまとめる。
- UIの`継承`は`None`を意味し、active generation settingsのmodeを再利用する。空文字や表示名をcoreへ渡さない。

### 8.6 Canonical sync / lifecycle

- preset apply、mode override、Undo / Redoの完了後は、既存`sync_ui_state()`へ一つのeffective plan hintを渡す。
  identity-only Custom normalizationとsame-settings renameはcurrent effective contextを再利用し、resolverを追加実行せず
  preset表示、Info / diagnostics、action state、INI保存要否だけを同期する。
- selected event displayは同じsync contextを読み、selector / mode controlをcanonical stateへprojectionする。
- projection中のwx eventはguardで抑止し、projection eventを新しいhistory transactionにしない。
- Preview clickによる「選択イベント」tab自動切替は維持する。preset操作や通常syncではcurrent tabを変更しない。
- preset操作でselected eventが無効になる場合は、selectionだけをclearし、入力やanalysis resultを不要に破棄しない。
- analysis success / failure / cancel、workspace reset、input change、late callbackではB4 lifecycle clear / retain規則を優先する。
- app終了・新規作業・input変更でsession historyは破棄され、preset JSON / INIはhistoryを保存しない。

### 8.7 Error / notice

- error codeだけでload failureとmutation failureを判定せず、`PresetLoadResult` / `PresetMutationResult`の型と
  `mutation_available`を正本にする。

| 結果 | error code | UI動作 |
| --- | --- | --- |
| `PresetLoadResult` | `invalid_json`、`unsupported_schema`、`invalid_schema`、`read_failed`、`duplicate_id`、`duplicate_display_name`、`limit_exceeded` | built-inとcurrent settingsを維持し、user一覧を空、user mutationを無効化して継続noticeを表示する |
| `PresetMutationResult`（入力・対象拒否） | `invalid_input`、`duplicate_id`、`duplicate_display_name`、`limit_exceeded`、`preset_not_found`、`builtin_read_only` | 旧一覧・旧JSON・output stateを維持し、操作単位noticeを表示する。resultがmutation availableなら再入力を許可する |
| `PresetMutationResult`（永続化不可） | `write_failed`、`replace_failed`、`store_unavailable` | 旧一覧・旧JSON・output stateを維持し、user mutationを無効化する。built-in Applyは継続利用できる |

- store error codeをユーザー向け表示へ直接露出せず、diagnostic detailが必要な場合だけ補足表示する。
- noticeはpanel内で再操作可能な形にし、失敗時にmodal dialogを連続表示しない。
- B4のINI保存失敗通知とpresets.json mutation failureを同じ成功扱いにしない。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- branch、HEAD、worktree、B1〜B4の完了記録、本plan、Block Breakdown、Roadmap、Indexを再確認する。
- B5 target pathの実在、current placeholder、B4 public API、selected editor request / state、既存testを再確認する。
- P1 / P2 / P3、ユーザー所有変更、依存・package差分を確認する。
- `GenerationPresetStore`、`EventAdjustment`、`EffectiveShapePlan`のpublic contractを再確認し、private collection走査とcore duplicateを避ける。

### Step 2: Preset panelの表示stateとRightPane controls

- placeholderをselector、active state、settings preview、Apply、管理ボタン、noticeへ置き換える。
- built-in / user / Customの表示とstable id mappingを実装する。
- panel revision、projection guard、selected idとactive idの分離、およびSelect / Apply / Create / Update /
  Delete request DTOを固定する。
- `set_preset_panel_state()`、`set_preset_panel_notice()`、`set_preset_panel_busy()`などのUI非依存入口を追加する。
- `_on_size()`、`_update_wrap()`、theme refreshへ新controlを追加する。

### Step 3: MainFrame / AppController callback seam

- RightPaneのpreset select / apply / create / update / delete callbackをMainFrameへ接続する。
- AppControllerはstore load / lookup / mutationを所有し、結果DTOをMainFrameへ返す。
- Applyとactive normalizationはMainFrameのB4 output state APIへ接続する。
- mutation後はsuccess resultのuser preset tupleをpanelへ渡し、storeをUIから再読込しない。
- stale id、expected panel / editor revision不一致、Busy、dirty input、missing store resultを各入口で拒否する。
- active update / delete後のidentity正規化はbase-bound history全endpointとbaseなしGenerationStateを分け、
  effective resolverを呼ばずsettingsを保持する。same-settings renameはdisplay / diagnosticsだけを同期する。
- create後は新規idを選択し、updateではstable selectionを保持する。deleteでselected idが消えた場合は
  existing active preset、Customの順でfallbackする。

### Step 4: Preset management dialog

- create / update dialogを既存wxPythonのmodal dialog規約へ合わせて実装する。
- 100件上限、表示名境界、hold / softness範囲、hold / decay選択を入力時に表示する。
- built-in選択時は編集・削除を無効化し、stale requestでもstoreのread-only契約を守る。
- dialog cancelは一覧、output state、history、selectionを変更しない。
- mutation success / failureを一回のpanel rerenderへまとめ、temporary objectやJSON direct writeを行わない。

### Step 5: Selected event mode override

- selected event editorのmode rowとnoticeを追加する。
- request validator、merge、reset、MainFrame commitを`long_vowel_mode`へ拡張する。
- edit request value型をstrへadditiveに広げ、mode choiceをcoalescingなしのdiscrete transactionとする。
- terminal continuation判定、active mode / requested override / effective mode表示を実装する。
- decay時tail disable、latent保持、hold復帰、non-terminal disableを実装する。
- existing gesture coalescing、editor revision、base identity guard、Undo / Redo文言を維持する。

### Step 6: Canonical synchronization and action states

- `MainFrame.update_action_states()`からpreset panelとselected event mode controlへBusy / saveability / selectionを反映する。
- canonical generation stateをParameterPanelとpreset panelへguard付き投影する。
- active preset update / deleteのCustom normalization後にselector、display name、settings previewを同じstateから再描画する。
- preset Apply後のPreview表示がB4 manual repairを壊さないことを確認する。
- Preview clickのselected-event tab auto-switch、通常syncのtab維持を回帰させる。

### Step 7: Test実装

- preset panelの表示・identity・callback・busy・failure noticeを新規wx testへ固定する。
- mode rowのterminal / non-terminal / inherit / hold / decay / latent tail / reset / staleを新規wx testへ固定する。
- B4 history、B3 store、MS21 selected editor / Undo / Redo / state integrationへ必要最小限の回帰を追加する。
- testでrepository既定INI / `presets.json`を使わず、temporary settings / preset storeを注入する。

### Step 8: 検証と実装後同期

- B5専用test、関連回帰、MS17 / MS19 / MS20 / MS21回帰、full suite、`compileall`、`git diff --check`を一つずつ実行する。
- diffを§7へ照合し、B6 docs、MS23、dependency、package、release、実MMD確認を除外する。
- ユーザーが実施したmanual GUI確認だけを証拠として記録し、CodexがGUI確認を実施したとは記載しない。
- 実装結果を本plan、Block Breakdown、Index、Roadmapへ反映する。B6対象のREADME / 正本仕様は先行同期しない。

## 10. 状態遷移 / データ契約

### 10.1 Preset panel

```text
Startup loaded
  -> built-in + valid user listを表示
  -> invalid user fileならbuilt-inのみ + mutation unavailable notice

Select item
  -> selected_preset_idだけ変更
  -> output state / history / Preview / INIは不変

Apply item
  -> Busy / dirty / stale / missing guard
  -> store lookup
  -> B4 resolve-before-commit
  -> OutputEditState + shared contextをinstall
  -> selector / controls / Preview / diagnostics / saveability同期

Create / update / delete
  -> request revision / Busy / dirty / dialog validation
  -> GenerationPresetStore mutation
  -> success resultで一覧更新
  -> createは新規id選択、updateはstable selection保持
  -> delete selectedはexisting active preset、Customの順でfallback
  -> active idが無効化された場合だけresolverなしでcurrent / history endpointをCustom normalization
  -> Custom normalization時だけINI保存要求1回
```

### 10.2 Preset identity

| 状態 | `active_preset_id` | 表示 | Apply |
| --- | --- | --- | --- |
| built-in active | `builtin:*` | built-in名 | 使用可 |
| user active | UUID | user名 | 使用可 |
| Custom | `None` | `カスタム（現在の設定）` | current値を再適用しない |
| missing / mismatch | `None`へ正規化 | Custom + notice | store修復後に明示再選択 |
| invalid user JSON | built-in idまたはNone | built-in / Custom | built-inのみ可 |

### 10.3 Mutation境界

| 操作 | presets.json | output state | history |
| --- | --- | --- | --- |
| Create | 成功時のみ追加 | 不変 | 不変 |
| Update inactive | 成功時のみ更新 | 不変 | 不変 |
| Update active, same settings | 成功時のみ更新 | id保持・display / diagnostics更新 | resolver / INI / 新規transactionなし |
| Update active, settings changed | 成功時のみ更新 | settings保持・Custom化 | 全endpoint正規化・新規transactionなし |
| Delete inactive | 成功時のみ削除 | 不変 | 不変 |
| Delete active | 成功時のみ削除 | settings保持・Custom化 | 全endpoint正規化・新規transactionなし |
| Apply | JSON変更なし | B4 transaction | 1 transaction / no-op |

### 10.4 Selected event mode

| selected event | mode control | tail control | commit |
| --- | --- | --- | --- |
| terminal continuation | `継承 / hold / decay` | holdなら有効、decayなら無効 | `long_vowel_mode`を許可 |
| source event | 無効 | source所有権どおり | mode request拒否 |
| intermediate continuation | 無効 | 無効 | adjustment request拒否 |
| non-long group tail | 無効 | 既存どおり | mode request拒否 |
| synthetic / stale | 表示対象外 | 表示対象外 | state変更なし |

### 10.5 Mode resolution

```text
terminal event explicit override
  > active GenerationSettings.long_vowel_mode
  > application default hold
```

- `requested_long_vowel_mode=None`はinheritであり、空文字ではない。
- `effective_long_vowel_mode`は`EffectiveLongVowelRun.resolved_mode`を表示する。
- decayのterminal zeroはUI設定で後ろへ移動できない。
- decay中のlatent tailはsnapshotから削除しない。

## 11. テスト方針

### 11.1 計画作成baseline

2026-08-09に、B3 store、B4 state、RightPane、selected event editor、Undo / Redo、state integrationの
関連53件を実行し、53 passed、process exit code 0を確認した。これはB5実装前の現行baselineであり、B5機能の実装済み証拠ではない。

同日のplan実装状態整合レビューでは、B4 history / B3 preset / B4 generation stateの35件、B2 long-vowel
resolver / selected event editor core・wxの32件がpass表示・各process exit code 0だった。P2 / P3修正は文書だけであり、
production code、test code、GUIは変更していない。

### 11.2 `tests/test_wx_ms22_b5_preset_ui.py`

- built-in / user / Customの表示名、source、stable id mapping
- selector変更がoutput state、history、Preview、INIを変更しないこと
- Select / Apply / Create / Update / Delete requestのexpected panel / editor revisionとstale拒否
- built-in / user Applyのcallback、active state、settings control、Preview同期
- 同一settings / idのno-op、同一settings / id異値のid-only transaction
- create成功が新規idを選択し、Applyせずoutputを変更しないこと
- update / renameのactive・inactive分岐、same-settings renameのdisplay / diagnostics限定同期
- deleteのactive・inactive分岐、baseあり / なしCustom normalization、全history endpoint、deleted id非復活
- selected preset削除後のexisting active preset / Custom fallbackと非選択delete時のselection保持
- load resultのduplicate id / name、100件超過、invalid JSON / schema / read failureとuser mutation lock
- mutation resultのinvalid input、duplicate id / name、100件上限、missing、built-in read-only
- write / replace failure時の旧一覧、旧JSON、output state保持
- Busy、stale panel revision、missing id、selected editor dirty input拒否
- dialog cancelの完全不変
- theme、scroll、tab order、既存Info / Warning / selected eventの回帰
- temporary settings / preset store注入とrepository default path不変

### 11.3 `tests/test_wx_ms22_b5_long_vowel_override.py`

- terminal continuationだけmode controlが有効になること
- source / intermediate / non-long / stale eventでmode requestが拒否されること
- inherit（None）、hold、decayのprimitive mappingとeffective表示
- active generation modeと明示overrideの優先順位
- decayでhold / softness / slopeがdisabled、noticeが表示されること
- decay中のlatent tailが保持され、hold復帰で再表示・再反映されること
- mode resetが既存adjustmentを壊さずNoneへ戻すこと
- editor revision、base identity、Busy、dirty input、projection guard
- mode change後のPreview / writer / diagnostics同一context
- Preview selected-event tab auto-switchと通常syncのtab維持

### 11.4 既存回帰

- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_wx_ms22_b4_generation_state.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_wx_ms21_b7_state_integration.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- MS17 / MS19 / MS20のinput、pipeline、VMD、diagnostics、lifecycle回帰

### 11.5 実装後の検証コマンド

実装後に、以下を一つずつ実行する。実数と終了コードは実行結果へ置き換え、未実行の結果を先に記載しない。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms22_b5_preset_ui.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms22_b5_long_vowel_override.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b3_generation_presets.py tests/test_ms22_b4_generation_history.py tests/test_wx_ms22_b4_generation_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b2_long_vowel_resolver.py tests/test_ms22_b2_long_vowel_adapters.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b3_right_pane.py tests/test_wx_ms21_b4_selected_event_editor.py tests/test_wx_ms21_b6_undo_redo.py tests/test_wx_ms21_b7_state_integration.py
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

### 11.6 Manual GUI境界

ユーザー確認では、実際に次を操作して記録する。

1. 起動時のbuilt-in / Custom表示とプリセット一覧。
2. `標準（長音維持）`、`長音減衰`、user presetのApplyと再解析不要のPreview反映。
3. create / update / rename / delete、active preset削除後のCustom化。
4. 長音terminal eventの継承・hold・decay、decay tail disable、hold復帰、reset。
5. non-long / source / intermediate eventでmode controlが操作できないこと。
6. Busy中、dirty selected editor、Undo / Redo、theme、tab / scrollの維持。
7. invalid JSONまたは保存失敗時にbuilt-inが利用でき、user mutationだけが停止すること。

CodexがGUIを起動していない場合、手動確認は「未実施」と記録する。実MMDのVMD / WAV読み込み・リップ同期はMS26へ残す。

## 12. 受け入れ条件

- RightPane `プリセット`タブがplaceholderではなく、built-in / user / Customをstable idで区別して表示する。
- Select / Apply / Create / Update / Deleteがimmutable request DTOとexpected revisionを使用し、stale requestを
  store mutation前に拒否する。
- selector変更だけではoutput state、history、Preview、diagnostics、INIが変更されない。
- built-in / userのApplyはBusy・stale・dirty guardを通過した場合だけ1回のB4 transactionで反映される。
- 同一settings / idの再Applyはno-op、同一settings / id異値はid-only transactionとなる。
- Apply後に再解析を要求せず、Preview、VMD準備、diagnostics、saveabilityが同じeffective contextへ同期する。
- create / update / deleteはB3 storeのvalidation、上限、read-only、atomic failureを利用し、GUIからJSONを直接編集しない。
- create / inactive update / inactive deleteはcurrent outputを変更しない。
- create後の新規id選択、update後のstable selection保持、delete後のexisting active / Custom fallbackが
  output Applyとは分離される。
- active update / deleteで旧settingsを失わず、settings不一致・deleted idをresolverなしでCustomへ正規化する。
  base-bound current / undo / redo endpointまたはbaseなしGenerationStateを一括更新し、INI保存要求を1回だけ出す。
- active presetのsame-settings renameはhistory、resolver、INIを変更せず、panel、Info / diagnostics、report表示名を更新する。
- deleted / mismatched presetがUndo / Redoで復活表示・再適用されない。
- load resultとmutation resultを区別し、invalid JSON、schema不正、duplicate id / name、上限超過、
  invalid input、missing、read / write / replace failureが正しいmutation availabilityと回復可能なnoticeへ反映される。
- 長音terminal continuation eventだけで`継承 / hold / decay`を選択できる。
- mode overrideは`None | hold | decay`へ厳密に対応し、non-terminal / non-long / stale eventではstateを変更しない。
- mode request valueは`str | None`としてfield別検証し、gesture coalescingなしのdiscrete transactionになる。
- decayではtail controlを無効化し、終端zeroの理由を表示する。latent tailはhold復帰で再利用できる。
- source / intermediate ownership、B2 resolver semantics、fixed morph、30fps、VMD、audio contractを変更しない。
- selected event editorのstale / dirty / gesture、Preview tab auto-switch、Busy、theme、lifecycleの既存挙動を維持する。
- B5専用test、指定回帰、full suite、compileall、diff checkの表示結果と終了コードを記録する。
- B5実装済み、B6 docs、実MMD確認、MS23以降を混同しない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| selector変更が暗黙Applyになり、意図しないhistoryを作る | selectorとApplyを分離し、選択は表示stateだけを変更する |
| 表示名をidentityとしてrename後に別presetへ適用する | stable idをrequest payloadとstore lookupの正本にする |
| preset store mutationとoutput transactionの片方だけが成功する | mutation failureではoutput不変とし、mutation成功後のidentity-only正規化はresolverを使わない。Applyだけをstore lookup後のB4 commitへ送る |
| active preset update / deleteで旧idがUndo / Redoから復活する | current store resolutionでbase-bound history全endpointまたはbaseなしstateを正規化し、missing idを追加履歴なしでCustomへ収束させる |
| 同じerror codeをloadとmutationで同一処理する | result型とmutation availabilityを先に判定し、error matrixどおりbuilt-in継続・再入力・mutation lockを分ける |
| invalid JSONでbuilt-inまで使用不能になる | `PresetLoadResult`のbuilt-inを維持し、user mutationだけをlockする |
| selected preset削除後にstale idや表示名fallbackが残る | existing active preset、Customの順でstable id selectionを復元する |
| decay中のtail disable時にlatent overrideを消す | UI disableとsnapshot cleanupを分離し、mode変更時にlatent値を保持する |
| non-terminal eventへmode overrideが混入する | editor state、MainFrame、shared resolverの三段階でownershipを検証する |
| canonical control projectionが再commitを起こす | B4 projection guardとpanel suppress guardを共用し、projection eventをhistory対象外にする |
| selected editorのdirty inputをpreset Applyで消す | Apply / destructive mutation前に既存dirty guardを実行し、拒否時は入力を保持する |
| Busy解除前のwx callbackがstateを変更する | Busy / panel revision / editor revisionをrequestへ含め、stale requestをno-opにする |
| store内部やJSONをRightPaneが直接参照する | controllerがresult DTOを所有し、RightPaneはimmutable panel stateのみ描画する |
| B5でB2 resolverやB6 docsまで膨らむ | target file表とOut of Scopeを実装前チェックで照合する |
| wx modal dialogのcancelで一覧やstateが変わる | dialog resultをcommit境界まで保持し、OK確定後だけmutationを実行する |
| 新規controlがtheme / scrollで表示崩れする | 既存palette、Wrap、ScrolledWindow、RightPane testを再利用する |

## 14. Codex 実装時の注意

- 実装前に本plan、Block Breakdown、Index、Roadmap、B4 current codeをHEADへ再照合する。
- P1 / P2 / P3を解消してからproduction codeへ進み、レビューを実装へすり替えない。
- commandは一つずつ実行し、未追跡fileと既存変更をユーザー所有として保護する。
- `GenerationSettings`、`GenerationPresetStore`、`EventAdjustment`、`OutputEditState`、`EffectiveShapePlan`をUI用mutable dictへ置き換えない。
- `presets.json`をRightPaneやtestから直接編集しない。temporary storeを注入する。
- display name、preset id、active resolution、Customを混同しない。
- preset update / deleteの失敗時に、output state・history・Previewを成功扱いで進めない。
- mode requestで`hold` / `decay`を表示名から推測せず、primitive stringを明示する。
- decayの終端zero、tail disable、latent override保持を、UI都合でresolverへ追加修正しない。
- 既存のselected editor gesture、Preview tab auto-switch、Busy、late callback、rollback、saveabilityを回帰させない。
- Qt / PySide6、network、external ASR、自動download、新dependencyを追加しない。
- fixed morph、30fps、VMD形式、audio三役、B3 JSON schema、MS21 fingerprint payloadを変更しない。
- 実MMD確認、B6 docs同期、MS23以降、package / release / pushは先行完了扱いにしない。
- 完了時は確認ファイル、変更ファイル、実装内容、テスト結果、仕様逸脱、残課題、B6への引き継ぎを報告する。
