# MS22-B1 Implementation Plan

## 1. 文書情報

- 文書名: `MS22-B1 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS22-B1_Implementation_Plan.md`
- 対象Block: MS22-B1
- Block名: Long-Vowel / Generation-Preset Contract Pre-check
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `a18de64 Record MS21 closeout`
- 作成日: 2026-08-01
- 文書ステータス: Completed / Contract Fixed / 2026-08-01実施済み
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- 継承する完了基準:
  - MS21-B8 Closeout A
  - MS21のbase / adjustment / effective分離
  - Preview / writer共通`EffectiveShapePlan`
  - session内Undo / Redo、diagnostics、fingerprint、lifecycle guard

MS22-B1は、現行repositoryを読み取り監査し、MS22-B2からB6へ渡す長音・preset・history契約を
固定するBlockである。production code、test code、GUI、INI、JSON、dependency、build設定を
変更しない。

ユーザーが選択した長音`decay`契約は、長音runの先頭peakからterminal endまで線形減衰し、
**長音区間の終端で値`0.0`へ到達する**ものとする。

## 2. 背景

現行実装にはMS22の基盤となる次の事実がある。

- `text_to_hiragana()`はNFKC、記号除去、必要時のpyopenjtalk G2P、カタカナからひらがなへの
  変換を行い、`ー`を保持する。
- `hiragana_to_vowel_sequence()`は`ー`を直前母音の複製へ変換するが、その由来を返さない。
- TEXTありとvoice-onlyは、どちらも`AnalysisWorker`から同じ`build_vowel_timing_plan()`へ
  `text_content`を渡す。voice-onlyはWhisper書き起こしまたは編集済み書き起こしを入力にする。
- `build_vowel_timing_plan()`は`text_to_vowel_sequence()`から`list[str]`を作り、even / anchor配分、
  RMS refine、peak反映、interval conflict解消を通して`VowelTimelinePoint`を複数回再構築する。
- `VowelTimelinePoint`は`src/vmd_writer/writer.py`のfrozen dataclassで、現在は長音metadataを持たない。
- `VowelTimingPlan.vowels`と`timeline`はlistであり、frozen dataclassでもdeep immutableではない。
- `ShapeParameters`はglobal closing hold / softnessだけを持ち、`BaseShapeEvent`、
  `EffectiveShape`、`EffectiveShapePlan`は長音run provenanceを持たない。
- `BasePlanIdentity`のschemaは`ms21-base-plan-v1`であり、timeline identityに長音metadataを
  含めていない。
- `EventAdjustment`はpeak、start / end offset、hold、softness、slopeだけを持ち、長音mode
  overrideは存在しない。
- `canonicalize_adjustment_snapshot()`はhold / softnessが現在のglobal値と同じ場合に
  明示overrideを削除する。preset変更後も明示意図を保持するMS22契約とは一致しない。
- `AdjustmentHistoryState`はadjustment snapshotだけをcurrent stateとして持ち、generation settingsと
  active preset idを履歴化しない。
- `closing_hold_frames`と`closing_softness_frames`は現在、`morph_upper_limit`と同じ
  `_on_param_changed()`へ接続され、解析job invalidationとtiming plan無効化を行う。
- `SettingsStore`はINIを同一directory temporary fileから`os.replace()`し、最初の保存失敗後は
  session内saveをdisableする。
- RightPaneの`プリセット`tabはplaceholderであり、preset store、`presets.json`、長音mode、
  generation stateは未実装である。
- same-vowel micro-gap / burst candidate、same-vowel grouping、cross-vowel transitionは既存機能であり、
  `ー`由来長音の正本ではない。

B1でデータ正本、schema、run member別の編集所有権、preset境界、atomic history、lifecycle、
failure、test ownershipを固定しない場合、B2からB5が異なる前提で実装されるおそれがある。

## 3. 目的

- 長音を検出する正規化段階とimmutable token metadataを固定する。
- tokenからtimeline、base event、effective shapeへmetadataを運ぶ一方向データ経路を固定する。
- `BasePlanIdentity`とadjustment snapshotのMS22 schema更新を固定する。
- 長音runのsource、intermediate continuation、terminal continuationの意味を固定する。
- `hold`と`decay`のcontrol point、終端zero、次shape保護を固定する。
- run member別のpeak / start / end / hold / softness / slope / mode編集所有権を固定する。
- 長音、same-vowel candidate、grouping、manual crossfadeの処理優先順位を固定する。
- `GenerationSettings`、built-in preset、user preset、INI、`presets.json`の責務を固定する。
- 明示overrideを失わないcanonicalizationとatomic output edit historyを固定する。
- Preview、writer、diagnostics、fingerprint、report、WARNING確認の共通派生元を固定する。
- startup、input変更、解析、rollback、reset、Undo / Redo、保存失敗のstate matrixを固定する。
- B2からB6の入力、出力、failure、test ownershipを分離する。
- B1実施後のP1 / P2 / P3とB2 / B3計画策定可否を判定する。

## 4. In Scope

- 現行branch、HEAD、worktree、上位計画、正本文書の読み取り確認
- TEXTあり／voice-onlyの共通text-to-vowel経路確認
- 長音token DTOとtimeline metadataの初期契約
- legacy `list[str]`、legacy timeline tuple、fixed morph互換契約
- 全`VowelTimelinePoint`再構築経路のcopy ownership
- long run identity、source / terminal参照、invalid metadata拒否
- `ms22-base-plan-v1`とMS22 adjustment snapshot schema
- `hold / decay`、decay terminal zero、30fps整数frame契約
- run member別adjustment ownershipとUI disabled / reject handoff
- automatic candidate、same-vowel grouping、manual crossfadeとの優先順位
- `GenerationSettings`と`LongVowelMode`の初期契約
- built-in / user / Custom状態、versioned JSON、INI責務
- explicit override canonicalizationとlatent tail保持
- output edit history、最大50件、coalescing、Undo / Redo、redo破棄
- generation settingsをanalysis-affecting parameterから分離する将来変更境界
- diagnostics、effective output identity、save-state fingerprint、reportの引き継ぎ
- lifecycle / failure matrixとB2からB6の所有権表
- 既存testの読み取り監査と非変更baseline実行
- B1実施結果と残存findingの文書記録

## 5. Out of Scope

- production code変更
- test code追加・変更
- wxPython GUI変更
- `VowelToken`、timeline metadata、long resolverの実装
- `GenerationSettings`、preset store、`presets.json`の実装
- `EventAdjustment`、history、UiState、diagnosticsのMS22実装
- RightPane preset tab、event mode controlの実装
- README、配布用readme、正本仕様のimplemented状態への更新
- user preset実file、INI key、migration fileの生成
- `ー`を含まない同音母音列または音響からの長音推定
- singing専用algorithm、VMD読み戻し、任意keyframe編集、複数event一括編集
- model profile、英字morph、Whisper model選択、一括出力、MS23以降の先行実装
- fixed morph、30fps、VMD形式、音声三権分立の変更
- dependency、package、license、version、release、tag、merge、push、branch削除
- Qt / PySide6、network、cloud ASR、音声外部送信、background通信、Whisper自動download
- manual GUI確認、実MMD確認、build / SmokeLaunch

## 6. 前提条件

- 作業branchは`feature/MS21-implementation`、計画基準HEADは`a18de64`とする。
- MS21 Closeout Aを未完了へ戻さない。
- 未追跡の`MS22_Block_Breakdown.md`と本計画を文書変更として保護する。
- Roadmapを計画正本、Indexを現在地正本として扱う。
- `src.*`とtop-level packageが別module objectとしてloadされ得る現行import境界を維持する。
- writer module初期化中にcoreへの新しいmodule-level逆importを追加しない。
- `LongVowelMode`のruntime境界はclass identityに依存しないcanonical primitive string
  `hold | decay`とする。B2がvalidation正本を実装し、B3はその契約を使用する。
- 新規metadataはprimitive / structural fieldでwriter DTOへ追加し、writerからcore `VowelToken`
  class identityを要求しない。
- existing `VowelTimelinePoint` positional constructorとlegacy tuple inputは長音metadataなしの
  non-long inputとして互換維持する。
- application defaultはhold / softness `0`、`long_vowel_mode=hold`とする。
- hold / softnessの範囲は現行MS21契約どおり0から100の整数とする。
- slopeはMS21契約どおりevent別0.0から1.0、default 0.7を維持し、generation presetへ含めない。
- B1開始時にworktreeへ未知の変更があればユーザー所有変更として保護する。

### 6.1 計画作成baseline

2026-08-01に次の非変更testを実行した。

- text processing / pipeline / VMD entry: 51件pass、process exit code 0
- MS21 effective core / Preview / writer: 102件pass、process exit code 0
- settings / history / RightPane / lifecycle: 40件pass、process exit code 0
- voice-only / effective identity / workspace reset / import境界: 17件pass、process exit code 0
- diagnostics core / rollback / callback / sync efficiency: 24件pass、process exit code 0
- diagnostics adapter / report / state integration: 37件pass、process exit code 0
- writer zero guard / multipoint / pipeline Preview / prepared VMD: 65件pass、process exit code 0
- 合計336件pass、failure / error表示なし、全process exit code 0

計画作成時点でproduction code、test code、GUI、dependency、build設定は変更していない。

## 7. 対象ファイル

### 7.1 主要確認対象

| ファイル | B1で確認・固定する責務 |
| --- | --- |
| `src/core/text_processing.py` | normalized reading、`ー`保持、legacy vowel API、新token API候補 |
| `src/core/__init__.py` | package初期化順、public export、pipeline経由の循環import境界 |
| `src/core/pipeline.py` | token配分、timeline生成、refine、peak反映、duration / conflict repair、`VowelTimingPlan` |
| `src/gui_wx/analysis_worker.py` | TEXTあり／voice-onlyが同じbuilderへ入る境界 |
| `src/vmd_writer/writer.py` | `VowelTimelinePoint`、legacy tuple、normalization、copy helper、fixed morph / 30fps |
| `src/vmd_writer/__init__.py` | writer package初期化順、legacy public export境界 |
| `src/core/preview_transform.py` | Preview timeline再構築とmetadata copy境界 |
| `src/core/effective_shape_plan.py` | base identity、base event、shape parameters、candidate / grouping、effective provenance |
| `src/core/event_adjustment.py` | event field、snapshot schema、canonicalization、stale identity拒否 |
| `src/core/event_adjustment_history.py` | current snapshot、transaction、coalescing、50件、Undo / Redo |
| `src/vmd_writer/effective_shape_adapter.py` | core resultからwriter morph frameへの一方向adapter |
| `src/core/settings_store.py` | INI default / validation、same-directory atomic save、save-disabled failure |
| `src/gui_wx/ui_state.py` | current adjustment history、selection、workspace clear / retain |
| `src/gui_wx/analysis_rollback.py` | parameter snapshot、base identity、history rollback payload |
| `src/gui_wx/main_frame.py` | parameter handler、base input、single resolver sync、analysis lifecycle、settings restore |
| `src/gui_wx/app_controller.py` | coalesced INI保存、flush failure、workspace reset |
| `src/gui_wx/parameter_panel.py` | morph upper、hold、softnessの現行control / range |
| `src/gui_wx/right_pane.py` | preset placeholder、selected editor、tab / theme / disabled説明境界 |
| `src/gui_wx/selected_event_editor.py` | field state、validation、gesture、effect notice DTO |
| `src/gui_wx/output_diagnostics_adapter.py` | generation / adjustment summaryのGUI adapter |
| `src/core/output_diagnostics.py` | effective output fingerprint、generation summary、saveability |
| `src/core/diagnostic_report.py` | Generation / Adjustment sectionの固定出力 |

### 7.2 正本文書

- `docs/MS17_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B8_Implementation_Plan.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `AGENTS.md`
- `pyproject.toml`

### 7.3 test参照対象

B1ではtestを変更しない。少なくとも次を現行回帰正本として確認する。

- `tests/test_text_processing.py`
- `tests/test_pipeline_peak_values.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_preview_transform.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_zero_guard.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_settings_store.py`
- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_wx_ms21_b7_state_integration.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms21_b7_import_boundaries.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms21_b7_ui_sync_context.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_wx_ms21_b7_sync_efficiency.py`

### 7.4 B1で変更可能な文書

- `docs/Implementation_Plan/MS22-B1_Implementation_Plan.md`
- 必要な責務補正に限定した`docs/Implementation_Plan/MS22_Block_Breakdown.md`
- B1実施記録とrouting更新に限定した`docs/MS20_and_Beyond_Index.md`
- 次作業表示の更新に限定した`docs/MS20_and_Beyond_Roadmap.md`

`README.md`、`readme_mmdautolip.txt`、`docs/repo_milestone.md`、`docs/Version_Control.md`は
B1で変更しない。実装済み仕様への同期はB6の責務とする。

## 8. 実装方針

B1にproduction実装はない。確認済みの現行事実とMS22のplanned contractを区別し、次の順序で
読み取り監査と契約固定を行う。

1. repository基準線とMS21完了契約を固定する。
2. normalized readingからlong-vowel tokenまでの正本を固定する。
3. tokenをtimelineへ投影し、全copy経路とbase identityへ保持する契約を固定する。
4. explicit long runをsame-vowel candidate / groupingから分離する。
5. hold / decay control pointとrun member別編集所有権を固定する。
6. `GenerationSettings`、preset DTO、JSON、INI、Customの責務を固定する。
7. EventAdjustmentのmode field、schema、explicit override canonicalizationを固定する。
8. adjustmentとgeneration stateを一体化するhistory / lifecycleを固定する。
9. Preview、writer、diagnostics、fingerprint、reportの一方向派生を固定する。
10. B2からB6の変更・failure・test ownershipを分離する。
11. 非変更testとdiff監査を実行し、P1 / P2 / P3を判定する。

B1で契約上の矛盾が見つかった場合は、文書だけを補正して再チェックする。production codeまたは
test codeを先行修正して問題を隠してはならない。

## 9. 詳細ステップ

### Step 1: repository基準線の固定

- `git status --short --branch`、branch、直近logを一つずつ確認する。
- `a18de64`とMS21 Closeout A、MS22 Block BreakdownのP2修正済み状態を確認する。
- 未追跡・未commit文書以外の変更があれば、作成者とscopeを確定するまで変更しない。
- RoadmapのMS22範囲とMS23からMS26の除外境界を再確認する。

### Step 2: normalized reading / token契約の固定

- 長音検出正本を`text_to_hiragana()`または同等の共通変換が返すnormalized readingとする。
- raw入力由来とG2P生成の`ー`は区別せず、normalized reading上に実在する`ー`を長音markerとする。
- voice-onlyのWhisper書き起こしと編集済み書き起こしも同じ変換を通す。
- `ー`を含まない同音母音、observation、RMS、groupingから長音を推定しない。
- leading `ー`はeventを生成しない。連続`ーー`は同じ最初のsource tokenを参照する。
- continuationのsourceは、同一long runを開始した**直前のnon-continuation token**とする。
  同じvowelが過去に存在してもrun境界を越えて参照しない。
- 新規token APIはadditiveとし、既存`text_to_vowel_sequence()`、
  `hiragana_to_vowel_sequence()`、string helperを維持する。
- B2の新規public API候補を`src.core.text_processing`へ置き、top-level / `src.*`のclass
  identity一致を互換条件にしない。

### Step 3: timeline metadata / identity契約の固定

- `VowelToken`候補と`VowelTimelinePoint`へ渡すprimitive metadataを§10.1どおり固定する。
- `build_even_vowel_timeline()`と`build_anchor_based_vowel_timeline()`でtoken順とtimeline順を
  1対1に維持する。
- fallbackでeven timelineへ戻る場合も同じtoken metadataを渡す。
- 次の再構築経路でmetadataをcopyする責務を列挙する。
  - RMS interval refine
  - observation付きrefine
  - peak value反映
  - adjacent interval conflict解消
  - midpoint duration補修
  - writer直前duration repair
  - writer timeline normalization / interval copy / resolved peak copy
  - Preview timeline normalization
- automatic candidate用synthetic pointへlong markerを継承しない。
- legacy tuple timelineは長音metadataなしとして扱い、tuple arityをMS22で拡張しない。
- `BasePlanIdentity`へmetadataを含め、schemaを`ms22-base-plan-v1`へ更新する。
- metadataだけが異なるplanを別identityとし、MS21 schema snapshotをfail closedで拒否する。

### Step 4: explicit long run / shape契約の固定

- source tokenと1個以上のcontinuation tokenを有効long runとする。
- source / continuationのvowel一致、token index順、source参照、base event存在を検証する。
- long runをatomic shape boundaryとし、automatic same-vowel candidateまたは通常groupingへ
  吸収しない。
- `あーあ`の末尾通常`あ`をlong runへ自動追加せず、long run境界を越えたgroupingを禁止する。
- source peak valueとterminal end frameをshape正本にする。
- hold / decayのcontrol pointとinvalid intervalを§10.3どおり固定する。
- source duration、次shape、normalization、manual crossfadeとの競合をB2 resolverで一度だけ解決する。

### Step 5: run member別adjustment所有権の固定

- §10.4の所有権表をB2 model validationとB5 UI stateの共通正本にする。
- 非所有fieldをsnapshotへcommitせず、model側でfail closedにする。
- UIはmodel validationを再実装せず、structured editor stateからdisabled理由を表示する。
- continuation peakをdecay途中のcontrol pointへ変換しない。
- invalid adjustmentではlast-valid output、snapshot、history、selectionを維持する。
- decay中のterminal tail fieldは編集disabledとするが、既存明示値はlatent保持する。

### Step 6: same-vowel / candidate監査境界の固定

- `test_pipeline_peak_values.py`のmicro-gap / burst / representative spanを監査baselineにする。
- `test_vmd_writer_grouping.py`の通常same-vowel groupingを非長音baselineにする。
- `test_vmd_writer_intervals.py`と`test_preview_transform.py`のsame-vowel / cross-vowel
  candidate出力が長音metadataなしで不変であることをB2回帰条件にする。
- 改善はlong runと衝突する再現済み問題だけに限定し、既存閾値の一般調整を行わない。

### Step 7: GenerationSettings / preset契約の固定

- B2が`LongVowelMode`をprimitive string `hold | decay`の閉じた値集合としてvalidationし、
  class / Enum identityをpackage境界の互換条件にしない。
- B3はB2のmode validation契約を入力とし、immutable `GenerationSettings`をclosing hold、
  closing softness、long-vowel modeの3 fieldに限定する。
- `morph_upper_limit`、slope、morph name、model profileをpresetへ含めない。
- built-in presetはcode内read-onlyとし、stable idと表示名を持つ。
- user presetはstable UUID、single-line display name、`GenerationSettings`を持つ。
- JSON schema、保存場所、UTF-8 encoding、上限、load / save failure、temporary cleanup、Custom fallbackを
  §10.6どおり固定する。
- INIはactive settingsとactive preset idだけを保存し、preset本体を保存しない。

### Step 8: EventAdjustment / canonicalization契約の固定

- `EventAdjustment`へterminal long event専用のoptional `long_vowel_mode`を追加するB2契約を固定する。
- adjustment snapshot schemaを`ms22-adjustment-snapshot-v1`へ更新する。
- `None`だけをinheritとし、hold / softness / modeの非`None`値を明示overrideとして保持する。
- active generation settingsと同値でもhold / softnessをcanonical no-opとして削除しない。
- peakがbase peakと同値、offset 0、slope default等のMS21 no-op規則は、preset変更で意味が
  変化しないfieldに限って維持する。
- B2がmodel、schema、canonicalizationを所有し、B4は完成済みcanonical snapshotをatomic
  historyへ組み込む。Block Breakdownに異なる所有表現が残る場合はB1実施時に同期する。

### Step 9: output edit history / persistence契約の固定

- base有無にかかわらず§10.7の`GenerationState`をapp-levelで保持する。
- base確定時だけ、current adjustment snapshotとその時点の`GenerationState`を含む
  `OutputEditState`をhistoryのcurrent stateとして持つ。
- before / after stateを1 transactionとして持ち、部分復元を禁止する。
- preset applyとlong-vowel mode変更はdiscrete transactionとする。
- direct hold / softness変更は既存gesture境界を維持し、timer-based coalescingを追加しない。
- history上限50件、redo破棄、no-op、pending finish、dirty editor guardを維持する。
- in-memory commit、resolver / UI同期、coalesced INI保存要求の順序を固定する。
- INI保存失敗ではin-memory output stateとhistoryをrollbackしない。
- JSON user preset collectionのcreate / update / deleteはatomic file保存成功後だけstoreへcommitする。

### Step 10: lifecycle / rollback契約の固定

- §10.8のstate matrixを現行`UiState`、`AnalysisRollbackSnapshot`、workspace resetへ対応付けする。
- generation settingsはapp-level persistent stateとしてinput変更やworkspace resetで保持する。
- adjustment、selection、output edit historyはbase planに従いclear / restoreする。
- hold / softness / long modeをanalysis-affecting parameterから外し、B4でoutput-only再解決へ移す。
- `morph_upper_limit`だけをanalysis resultのpeak生成に関与するparameterとして維持する。
- Busy中のgeneration edit、late / duplicate callback、stale identityはstateを変更しない。

### Step 11: diagnostics / fingerprint / report契約の固定

- Preview、writer、diagnosticsは同じ`EffectiveShapePlan` instanceまたは同じimmutable contextを使う。
- effective long shapeのkind、run member、terminal frame、resolved modeをcore planへ保持する。
- diagnostics / reportはstructured summaryを使い、preset表示文字列から状態を復元しない。
- generation summaryへactive long-vowel mode、active preset id / display name、effective hold / decay
  run countをadditiveに追加する。adjustment summaryへmode override件数をadditiveに追加する。
- effective run countは未解析／writer input未確定を`None`、解析済みで該当runなしを`0`として区別する。

```text
GenerationDiagnosticsSummary additive fields
  active_long_vowel_mode: hold | decay
  active_preset_id: str | None
  active_preset_display_name: str | None
  effective_long_vowel_hold_run_count: int | None
  effective_long_vowel_decay_run_count: int | None

AdjustmentDiagnosticsSummary additive field
  long_vowel_mode_override_count: int
```

- `active_preset_id=None`はCustom、`active_preset_display_name=None`はCustom表示名をadapterで生成する。
- preset display nameとidはreport表示用structured dataであり、fingerprint入力にはしない。
- active preset id / display nameだけでsave-state fingerprintを変えない。
- MS21 fingerprintの既存canonical入力であるinput mode、normalized TEXT / WAV path、effective writer
  input state、VMD model name、effective morph frame / tail、diagnostic identityを維持する。
- MS22 generation操作は、effective morph frame / tailまたはdiagnostic identityを含む既存canonical入力が
  変化した場合だけ既存WARNING確認を無効化する。preset id / display name、notice、history順序だけでは
  無効化しない。
- current fingerprint payload構造が変わらない場合は`ms21-effective-output-v1`を維持し、
  milestone名だけを理由にschemaをbumpしない。payload構造変更が必要ならB4 planで明示する。

### Step 12: B2からB6へのhandoffとB1判定

- §10.9のownership表を各Block planの入力正本とする。
- 新規候補path、既存API、回帰testが存在することを確認する。
- 非変更baselineを実行し、pass表示、failure / error、process exit codeを分けて記録する。
- findingsをP1 / P2 / P3へ分類する。
- P1 / P2があればB2 / B3計画策定可とせず、文書補正後に再チェックする。
- P1 / P2 / P3なしの場合だけB1をCompleted / Contract Fixedとし、B2 / B3計画策定可と記録する。
  B3 planは策定可能だが、production実装はB2 primitive mode契約の実装・検証後とする。

## 10. 状態遷移 / データ契約

### 10.1 long-vowel token / timeline metadata

B2で追加するimmutable tokenの意味を次で固定する。名前は実装時に同等名へ調整できるが、意味を
削減または推測へ置換しない。

```text
VowelToken
  vowel: あ / い / う / え / お
  token_index: normalized vowel-token列内の0以上のindex
  is_long_vowel_continuation: bool
  long_vowel_source_token_index: int | None
```

- non-continuationは`long_vowel_source_token_index=None`とする。
- continuationは`True`かつsource index必須とする。
- source indexは自身より小さく、同一long runを開始した直前のnon-continuation tokenを指す。
- `あーあー`では前半continuationは最初の`あ`、後半continuationは2個目の`あ`をsourceとし、
  同じvowelでもrun境界を越えて最初のtokenへ戻さない。
- 連続`ーー`は全continuationが同じsource indexを指す。
- leading `ー`はtokenを作らない。

`VowelTimelinePoint`へはwriter / core間の循環を避けるため、primitive fieldとして次をadditiveに
追加する候補を固定する。

```text
vowel_token_index: int | None = None
is_long_vowel_continuation: bool = False
long_vowel_source_token_index: int | None = None
```

- pipeline生成pointではtoken indexを必須とする。
- legacy callerの`None / False / None`はlong-vowel metadataなしとして受理する。
- metadataなしpointからsame-vowel関係を使ってsource indexを推測しない。
- `VowelTimingPlan.vowels`は既存表示互換の`list[str]`として維持し、timeline fieldをmetadata正本とする。
  parallel token listをplanへ重複保持してdriftさせない。

### 10.2 データフロー

```text
TEXT file content / voice-only transcription
  ↓ text_to_hiragana or equivalent common normalization
normalized reading with explicit ー
  ↓ additive tokenization
VowelToken sequence
  ├──→ legacy list[str] vowels
  ↓ even / anchor allocation
VowelTimelinePoint + primitive long metadata
  ↓ RMS refine / peak / interval repair (metadata copy)
VowelTimingPlan.timeline
  ↓ BaseTimingPlanInput
BaseShapeEvent + long provenance
  ↓ validate adjustment / resolve long run / existing candidate / grouping
EffectiveShapePlan
  ├──→ Preview adapter
  ├──→ writer adapter / VMD
  └──→ diagnostics / fingerprint / report
```

observation、Preview cache、RightPane文字列、preset表示名をこの経路の代替正本にしない。

### 10.3 long run / hold / decay

- long runは1件のsource eventと1件以上のcontinuation eventから成る。
- source peak frameとeffective peak valueをrun開始振幅とする。
- terminal continuationのeffective end frameを長音区間終端とする。
- `terminal_end_frame <= source_peak_frame`はinvalidであり、edit commitまたはplan解決をfail closedにする。
- `hold`はsource peakからterminal endまで同じpeak valueを維持する。
- `hold`のterminal end後だけ、terminal eventのexplicit tailまたはglobal tailを適用する。
- `decay`はsource peak valueからterminal endの`0.0`まで単一の線形segmentとする。
- continuation peakから中間control pointを生成しない。
- decayではhold / softness / slope tail controlをshapeへ適用せず、terminal endを後方へ移動しない。
- terminal `0.0`を`MORPH_FRAME_OPEN_EPSILON`へclampしない。
- next shape競合とsource durationは30fps整数frameでresolverが決定的に解決する。

### 10.4 run member別adjustment所有権

| event role | peak | start | end | hold / softness / slope | long mode |
| --- | --- | --- | --- | --- | --- |
| long source | 有効。run振幅を所有 | 有効。opening edgeを所有 | 無効。terminalが終端を所有 | 無効 | 無効 |
| intermediate continuation | 無効 | 無効 | 無効 | 無効 | 無効 |
| terminal continuation | 無効 | 無効 | 有効。run終端を所有 | hold時有効、decay時disabledかつlatent保持 | 有効 |
| non-long real event | MS21契約を維持 | MS21契約を維持 | MS21契約を維持 | current group tailだけMS21契約を維持 | 非表示／拒否 |
| synthetic token | 拒否 | 拒否 | 拒否 | 拒否 | 拒否 |

- real eventはroleにかかわらずselection / provenance対象として保持する。
- 無効fieldはeditor DTOでdisabled理由を返し、requestをmodel側でも拒否する。
- long metadata変更で旧snapshotのroleが変わる場合はbase identity mismatchで拒否する。

### 10.5 mode / adjustment優先順位

```text
terminal continuation event の明示 long_vowel_mode
  > active GenerationSettings.long_vowel_mode
  > application default hold
```

- preset適用はevent adjustment、selection、viewport、playbackを削除しない。
- explicit hold / softness / modeはactive settingsと同値でも保持する。
- decay中のtail overrideは出力へ作用しないがsnapshotに残し、holdへ戻すと再び有効になる。
- long run memberはautomatic same-vowel candidate / groupingの入力から隔離する。
- remaining non-long eventだけを既存candidate / grouping / manual crossfadeへ渡す。

### 10.6 GenerationSettings / preset / persistence

```text
LongVowelMode = hold | decay

GenerationSettings
  closing_hold_frames: int 0..100
  closing_softness_frames: int 0..100
  long_vowel_mode: LongVowelMode
```

組み込みpreset:

| stable id | 表示名 | settings |
| --- | --- | --- |
| `builtin:standard-hold` | `標準（長音維持）` | hold 0 / softness 0 / mode hold |
| `builtin:long-vowel-decay` | `長音減衰` | hold 0 / softness 0 / mode decay |

user preset JSONの初期schema:

```json
{
  "schema_version": 1,
  "user_presets": [
    {
      "id": "canonical-lowercase-uuid",
      "display_name": "ユーザー表示名",
      "generation_settings": {
        "closing_hold_frames": 0,
        "closing_softness_frames": 0,
        "long_vowel_mode": "hold"
      }
    }
  ]
}
```

- user idはUUIDとして生成し、built-in prefixを使用しない。
- display nameはtrim後1から100文字のsingle-line Unicodeとし、control characterを拒否する。
- trim後の同名、built-in表示名との同名、duplicate idを拒否する。
- user presetは0から100件を受理し、101件目を既存file非変更で拒否する。
- unsupported version、root / entry / field不正、duplicateはfile全体をfail closedにし、partial importしない。
- invalid fileを自動上書きせず、built-inだけを利用可能にする。
- invalid / unsupported user preset fileを読み込んだsessionではuser storeをread-only unavailableとし、
  create / update / deleteを拒否して原因をstructured resultで返す。外部修復後の次回loadまで既存fileを
  上書きしない。
- user preset fileは`SettingsStore.settings_path`のparent directoryに単一`presets.json`として置き、
  INIと保存場所を一致させる。
- JSONはUTF-8で読み書きする。
- create / update / deleteはtargetとsame-directoryのtemporary fileへ書き、明示closeしてから
  `os.replace()`する。replaceを含む保存失敗ではtemporary fileをcleanupし、旧`presets.json`と
  in-memory preset collectionを維持する。成功後だけcollectionへcommitする。
- active preset idが見つからない場合、INIのactive settingsを保持して`Custom`へ戻す。
- startupではINIのactive settingsを出力正本とする。active preset idが存在してもpreset definitionの
  settingsとINI settingsが一致しない場合はINI settingsを保持し、idを`None`へ正規化して`Custom`へ戻す。
- invalid user preset fileでもbuilt-in idは独立に解決し、INI settingsと一致する場合だけactive idを保持する。
- direct setting変更はactive preset idを`None`へし、`Custom`とする。
- INIへactive settingsとactive preset idだけを保存する。
- timing plan、input path、adjustment、history、selectionをINI / JSONへ保存しない。

### 10.7 adjustment / output edit history

```text
EventAdjustment
  existing MS21 fields
  long_vowel_mode: hold | decay | None

AdjustmentLayerSnapshot
  schema: ms22-adjustment-snapshot-v1
  base_plan_identity: ms22-base-plan-v1
  ordered EventAdjustment entries

GenerationState
  generation_settings: GenerationSettings
  active_preset_id: str | None

OutputEditState
  base_plan_identity: BasePlanIdentity
  adjustment_snapshot: AdjustmentLayerSnapshot
  generation_state: GenerationState

OutputEditHistoryTransaction
  before_state
  after_state
```

- `None`だけをinheritとし、非`None`のhold / softness / modeを明示overrideとする。
- `GenerationState`はbaseなしでも常に有効であり、input変更／new workspaceで保持する。
- `OutputEditState`はbase確定時だけ存在し、`adjustment_snapshot.base_plan_identity`と
  `base_plan_identity`の一致を必須とする。
- transaction before / afterでbase identity一致を必須とする。
- adjustment、settings、active idを部分的にUndo / Redoしない。
- active presetが削除済みならsettingsを復元し、idを`None`へ正規化してCustom表示する。
- historyは最大50 transaction、session内だけ、disk保存なしとする。
- legacy UiState property / Edit menuはB4で最小互換wrapperを維持してよい。base確定中のhistoryは
  adjustmentとgeneration stateを別transactionへ分裂させず、常に`OutputEditState`全体を復元する。

### 10.8 lifecycle matrix

| transition | generation settings / active id | base / adjustment / history | persistence / guard |
| --- | --- | --- | --- |
| app startup | INI settingsを正本として復元。missing idまたはdefinition不一致はCustom | baseなし、historyなし | invalid値はdefault。invalid user JSONはread-only unavailable |
| baseなしでsetting変更 | commitして保持 | historyを作らない | INI保存要求、Undo対象外 |
| analysis start | 保持。Busy中edit禁止 | rollback候補をcapture | morph upperだけanalysis parameter guard |
| current analysis success | 保持 | new base、empty adjustmentでhistory初期化。Undo entryなし | resolver 1回 |
| failure rollback可 | capture時stateと同一であることを検証 | old base / output history / selection復元 | current ERROR、VMD保存禁止 |
| cancel rollback可 | capture時stateと同一であることを検証 | old base / output history / selection復元 | prior ERROR優先、その他cancel INFO |
| parameter / identity mismatch | current settingsを保持 | resultとrollbackをcommitしない | rebuild待ち、保存禁止 |
| input変更 | 保持 | base / adjustment / history / selection clear | old callback拒否 |
| new workspace | 保持 | workspace stateとhistory clear | settings / preset file非削除 |
| preset apply、direct edit | atomic stateへcommit | baseありならhistory transaction | resolver / UI後にINI保存要求 |
| Undo / Redo | state全体をrestore | selectionが有効なら保持 | resolver / UI後にINI保存要求 |
| INI保存失敗 | current in-memory state保持 | history保持 | existing save-disabled / first notification |
| preset JSON保存失敗 | active output保持 | history保持 | old JSONとpreset collection保持 |
| app close | current settingsを保存可能ならflush | history破棄 | next startupはlast successful INIのみ |

closing hold / softness / long modeはB4でoutput-only settingへ移し、analysis resultを無効化しない。
`AnalysisParameterSnapshot`からhold / softnessを外す時期とrollback DTO更新はB4が所有する。

### 10.9 Block ownership

| Block | 入力 | 出力 | failure ownership | test ownership |
| --- | --- | --- | --- | --- |
| B2 | normalized reading、token contract、MS21 base / adjustment core | primitive LongVowelMode validation、token API、timeline metadata、MS22 identity / adjustment schema、long resolver | invalid metadata、invalid mode、non-owner edit、frame / identity mismatch | text、pipeline、effective core、same-vowel、Preview / writer adapter |
| B3 | B2 primitive mode contract、preset schema | GenerationSettings、built-in definitions、user store、JSON、INI keys | invalid / future JSON、IO、100件、missing / mismatched id | preset DTO、settings、atomic file、read-only recovery |
| B4 | B2 core＋B3 store | OutputEditState / history、UiState、diagnostics、fingerprint、lifecycle | stale state、INI failure、late callback、rollback | history、state、diagnostics、saveability、lifecycle |
| B5 | B4 state API | RightPane preset UI、terminal mode editor、disabled reason | Busy、dirty、stale、dialog cancel、user save error | wx preset、selected editor、theme、tab、Undo / Redo |
| B6 | B2からB5 implemented state | cross-regression、正本文書、manual GUI記録 | regression finding、docs drift | TEXTあり／voice-only、reset、failure、save、full regression |

## 11. テスト方針

B1は読み取り監査Blockであり、test codeを変更しない。

### 11.1 読み取り検証

- `rg`でDTO、constructor、copy helper、schema、canonicalizer、history、callback、settings keyを特定する。
- `VowelTimelinePoint`再構築箇所を漏れなく一覧化する。
- current same-vowel / cross-vowel test名と期待値を監査baselineへ対応付ける。
- plan記載のpath、class、function、testが現行repositoryに存在することを確認する。
- pyprojectのpackage includeと`src.*` / top-level import境界を確認する。

### 11.2 B1非変更baseline

各commandを一つずつ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py tests\test_pipeline_peak_values.py tests\test_pipeline_and_vmd.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b2_event_adjustment.py tests\test_ms21_b2_effective_shape_plan.py tests\test_ms21_b2_shape_adapters.py tests\test_preview_transform.py tests\test_vmd_writer_grouping.py tests\test_vmd_writer_intervals.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_settings_store.py tests\test_ms21_b6_adjustment_history.py tests\test_wx_ms16_b3_right_pane.py tests\test_wx_ms21_b4_selected_event_editor.py tests\test_wx_ms21_b6_undo_redo.py tests\test_wx_ms21_b7_state_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_textless_pipeline.py tests\test_ms19_b4_analysis_worker_voice_only.py tests\test_ms21_b5_effective_output_identity.py tests\test_ms19_b8_workspace_reset.py tests\test_ms21_b7_import_boundaries.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms20_b2_output_diagnostics.py tests\test_ms21_b7_analysis_rollback.py tests\test_ms21_b7_ui_sync_context.py tests\test_ms21_b7_audio_worker_terminal.py tests\test_wx_ms21_b7_sync_efficiency.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b6_diagnostic_report.py tests\test_ms20_b7_diagnostics_state_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_vmd_writer_zero_guard.py tests\test_vmd_writer_multipoint_shape.py tests\test_ms21_b3_pipeline_preview_integration.py tests\test_ms21_b5_adjusted_vmd_save.py -q
git diff --check
rg -n "[ \t]+$" docs\Implementation_Plan\MS22-B1_Implementation_Plan.md docs\Implementation_Plan\MS22_Block_Breakdown.md docs\MS20_and_Beyond_Index.md
```

pytestはpass表示、failure / error、fatal、process exit codeを分けて記録する。末尾空白`rg`は
matchなしのexit code 1を正常とし、matchが出た場合だけ文書を補正する。`git diff --check`が未追跡文書を
検査しないため、両方を必須とする。

### 11.3 B2以降へ渡す必須test境界

- raw入力`ー`、G2P生成`ー`、voice-only `ー`が同じtoken contractになる。
- leading `ー`を無視し、連続`ーー`が同じsourceを参照する。
- legacy vowel list / string helper出力が不変である。
- legacy `VowelTimelinePoint` positional / keyword constructorとtuple inputがnon-longとして動く。
- every pipeline / Preview / writer copy pathがmetadataを保持する。
- frame / vowelが同じでもlong metadataが異なるbase identityは異なる。
- MS21 identity / adjustment schema、invalid source index、cycle / forward source、vowel mismatchを拒否する。
- long runをsame-vowel candidate / groupingへ吸収しない。
- `あーあ`、`あーあー`、`あーーい`、source duration端、次shape隣接、zero-lengthを決定的に扱う。
- holdはterminalまでpeak維持、decayはterminalでexact `0.0`となる。
- continuation peakを中間control pointにしない。
- ownership表のenabled fieldだけを受理し、非所有fieldを拒否する。
- decay中にtail値をlatent保持し、holdへ戻すと復元する。
- active settingsと同値の明示hold / softnessをcanonicalizerが削除しない。
- built-in presetがJSONなしで利用でき、編集・削除・JSON保存できない。
- user preset 0 / 100 / 101件、UUID、name、duplicate、broken / future JSONを検証する。
- JSON保存失敗で旧file / collection / output stateを維持する。
- missing active idでINI settingsを保持してCustomへ戻る。
- active idが存在してもdefinitionとINI settingsが不一致ならINIを保持してCustomへ戻る。
- invalid user JSON後はbuilt-inを維持し、user mutationを拒否して旧fileを上書きしない。
- `presets.json`をINIと同じdirectoryへUTF-8で保存し、保存失敗時はtemporary fileをcleanupして
  旧fileとin-memory collectionを維持する。
- preset apply、direct edit、Undo / RedoがOutputEditState全体を原子的に復元する。
- baseなしsetting変更はhistoryを作らず、new baseでcurrent settingsを初期stateにする。
- INI保存失敗でin-memory state / historyをrollbackしない。
- effective frame同一ならpreset id / name変更だけでfingerprintを変えない。
- Preview / writer / diagnostics / reportが同じeffective planを使用する。
- writer zero guard / same-vowel multipoint、pipeline Preview identity、prepared VMD saveの既存回帰を
  B2の直接test ownershipとして維持する。
- current sync 1回につきresolver最大1回を維持する。
- failure / cancel rollback、input変更、workspace reset、late / duplicate callbackを維持する。
- fresh processで`src.core`、`core`、`src.vmd_writer`、top-level `vmd_writer`のimport順を変えても
  cycleを起こさず、class identity一致へ依存しない。

### 11.4 手動・build確認

- 手動GUI確認: B1では実施しない
- 実MMD確認: B1では実施しない。MS26へ維持
- build / SmokeLaunch: 実施しない
- package / release確認: 実施しない

## 12. 受け入れ条件

- normalized readingを長音検出正本とする段階が固定されている。
- raw / G2P / voice-onlyの`ー`と、same-vowel非長音の境界が固定されている。
- token / timeline metadata field、validation、legacy defaultが固定されている。
- 全timeline再構築経路のcopy ownershipが列挙されている。
- `ms22-base-plan-v1`と`ms22-adjustment-snapshot-v1`の入力と拒否境界が固定されている。
- long runのsource / continuation / terminal、atomic shape boundaryが固定されている。
- holdとdecay、terminal exact zero、source duration / next shape境界が固定されている。
- run member別adjustment所有権とdisabled / fail-closed契約が固定されている。
- same-vowel candidate / grouping / manual crossfadeとの処理順が固定されている。
- GenerationSettingsの3 field、default、validationが固定されている。
- B2のprimitive mode validationとB3のGenerationSettings所有、B3のB2依存が固定されている。
- built-in id / settings、user preset JSON schema、100件、failure recoveryが固定されている。
- `presets.json`のINI同一directory、UTF-8、close-before-replace、失敗時temporary cleanupが固定されている。
- INI、JSON、session state、historyの保存責務が分離されている。
- explicit override、latent tail、canonicalizationのB2所有が固定されている。
- OutputEditState、atomic transaction、50件、coalescing、Undo / Redoが固定されている。
- generation settingsのoutput-only化とmorph upperのanalysis-affecting維持が固定されている。
- lifecycle matrixとINI / JSON failure時の非rollbackが固定されている。
- baseなし`GenerationState`、base確定時`OutputEditState`、startup reconciliationが固定されている。
- effective plan、fingerprint、WARNING、diagnostics、reportの関係が固定されている。
- B2からB6の入力、出力、failure、test ownershipが固定されている。
- B1でproduction code、test code、GUI、dependency、build設定を変更していない。
- 実行testのpass表示とprocess exit codeが記録されている。
- B1実施後の残存P1 / P2がなく、未記名の設計判断が残っていない。
- B2 / B3 Implementation Plan策定可否が明記されている。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| raw文字列とnormalized readingで長音判定が分岐する | 共通変換後のnormalized readingだけを正本にする |
| 同じvowelの別long runが最初のsourceへ誤結合する | continuationは同一run直前のnon-continuationだけを参照し、`あーあー`を検証する |
| legacy vowel APIを破壊する | token APIをadditiveにし、existing list / string helperを維持する |
| writerからcore DTOをimportして循環する | timelineにはprimitive metadataを持たせ、fresh-process importを検証する |
| copy helperでmetadataを失う | constructor再構築箇所を列挙し、全経路にcopy testを割り当てる |
| metadataだけ違うplanへ旧adjustmentを適用する | base identity payloadとschemaをMS22へ更新する |
| adjustment mode追加をMS21 schemaのまま扱う | adjustment snapshotもMS22 schemaへ更新し旧snapshotを拒否する |
| long runを既存same-vowel groupingが吸収する | long runをatomic boundaryとしてcandidate / grouping前に隔離する |
| continuation peakでdecayが非線形になる | source peakだけを振幅正本にし、continuation peak editを拒否する |
| 非所有fieldをUIだけで無効化する | model validationでもrejectし、structured disabled reasonを返す |
| preset変更で明示tail overrideが消える | `None=inherit`とし、active settingsとの同値比較で削除しない |
| B2とB4でcanonicalization責務が重複する | model / schemaはB2、atomic history / state統合はB4に分離する |
| setting変更が解析結果を不要に破棄する | hold / softness / modeをoutput-onlyへ分離し、morph upperだけ解析parameterに残す |
| preset idだけでWARNING確認が失効する、またはMS21 fingerprint入力を失う | preset表示identityを除外しつつ、既存path / model / diagnostic identity / effective output入力を維持する |
| baseなしgeneration settingをOutputEditStateで表現できない | always-valid GenerationStateとbase-bound OutputEditStateを分離し、historyは後者全体を扱う |
| INI settingsとpreset definitionが不一致になる | INI settingsを出力正本とし、不一致idをCustomへ正規化する |
| invalid user JSONをmutationで上書きする | session内user storeをread-only unavailableにし、built-inだけを維持する |
| JSON失敗でuser presetを失う、またはtemporary fileが残る | INI同一directory・UTF-8・close-before-replaceを固定し、失敗時temporary cleanupとold file保持を行い、成功後だけcollectionへcommitする |
| INI失敗でcurrent outputを巻き戻す | in-memory commitを維持し、last successful INIだけを次回復元する |
| history拡張でMS21 shortcut / coalescingが壊れる | current behaviorを互換wrapperと既存回帰で保護する |
| B1でproduction実装を始める | Git diffを監査し、code / test / GUI変更をscope逸脱とする |
| MS23以降へscopeが膨らむ | presetを3 fieldに限定し、profile / morph / model / packageを除外する |

## 14. Codex 実装時の注意

```text
- B1は読み取り監査と文書上の契約固定だけを行う。
- production code、test code、GUI、INI、JSONを変更しない。
- commandは一つずつ実行し、parallel、pipeline、chained commandを使わない。
- Roadmap、Block Breakdown、過去planを仮説としてcurrent code / testsへ再照合する。
- 確認済み事実、planned contract、ユーザー決定、未確定を区別する。
- decayはterminal endでexact 0.0とし、tailやepsilonで後方・正値へ変えない。
- long markerをsame-vowel proximity、observation、RMSから推測しない。
- metadataなしlegacy callerをlong扱いしない。
- BasePlanIdentityとAdjustmentLayerSnapshotの両schema更新を漏らさない。
- EventAdjustment model / canonicalizationはB2、history / UiState統合はB4に分離する。
- Preview、writer、diagnosticsでlong runを再推定しない。
- generation setting変更でbase timing planを破棄しない将来契約を維持する。
- user adjustment、history、timing planをINI / presets.jsonへ保存しない。
- fixed morph、30fps、VMD形式、audio三権分立を変更しない。
- Qt、network、cloud ASR、Whisper自動downloadを追加しない。
- 実行していないtest、GUI、実MMD確認を通過と報告しない。
```

B1完了報告は次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 調査・契約固定内容
4. ユーザー判断・採用案
5. 実行した検証
6. 検証結果
7. P1 / P2 / P3
8. 仕様からの逸脱
9. 残課題
10. B2 / B3計画策定可否
```

## 15. B1実施結果 (2026-08-01)

- `feature/MS21-implementation` のclean worktree、`335178d Plan MS22 long-vowel and presets`、
  MS21 Closeout A (`a18de64`)を確認し、MS21完了契約を基準線として保護した。
- 正規化済み読み列を長音検出の正本とし、TEXTあり／voice-only共通経路、leading `ー`、連続`ーー`、
  run境界、legacy母音列互換、timeline metadata、base identity、same-vowel分離を固定した。
- ユーザー選択の`decay`は長音runのsource peakからterminal endまで線形減衰し、長音区間終端で
  exact `0.0`へ到達する契約として採用した。hold、run member別所有権、mode優先順位、tail latent保持、
  fail-closed境界も固定した。
- `GenerationSettings`、built-in / user preset、`presets.json`のschema・保存場所・UTF-8・atomic保存・
  失敗時保護、INIのactive settings責務、Custom復帰、OutputEditState / history、diagnostics / fingerprint /
  report、lifecycleのB2〜B6引き継ぎ境界を固定した。
- 現行コード、既存test、package設定との対応を確認した。B1の範囲ではproduction code、test code、GUI、
  INI、JSON、dependency、build設定を変更していない。
- 非変更baselineは7グループ合計336件がpass、各process exit code 0。`compileall src tests`と
  `git diff --check`もexit code 0で、文書末尾空白は検出されなかった。
- P1 / P2 / P3は残存なし。B1を`Completed / Contract Fixed`と判定し、B2 / B3 Implementation Planの
  策定を可能とする。ただしB3のproduction実装はB2のprimitive `LongVowelMode`実装・検証後とする。
- 実MMDでのVMD / WAV読み込み・リップ同期、MS23以降の機能は本Blockの残課題として変更せず、MS26以降へ維持する。
