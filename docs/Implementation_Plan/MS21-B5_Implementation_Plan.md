# MS21-B5 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B5 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
- 対象Block: MS21-B5
- Block名: VMD Save / Diagnostics Integration
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `0aa7fbf Implement MS21-B4 event editor`
- 作成日: 2026-07-25
- 文書ステータス: Implemented / Automated Verification Passed / User GUI Check Passed
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
- 関連正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS21-B5は、B2のshared resolverが生成し、B4のPreviewで確認できる
`EffectiveShapePlan` をVMD保存とMS20 diagnosticsへ接続するBlockである。
Preview、VMD writer、save-state fingerprint、WARNING確認、diagnostic reportが
同じeffective outputを参照する状態を完成させ、B4の一時保存禁止を撤去する。

## 2. 背景

B4完了時点の実装状態は次のとおりである。

- `UiState.current_adjustment_snapshot` がworkspace内のcanonical補正状態である。
- `MainFrame._resolve_current_effective_plan()` はcurrent base inputとcanonical
  adjustment snapshotをB2 `resolve_effective_shape_plan()` へ渡す。
- PreviewとRightPane editorは同じ `EffectiveShapePlan` を参照し、補正を即時反映する。
- `build_morph_frames_from_effective_shape_plan()` はresolved shapeを再解釈せず、
  final normalizationを含むwriter frame列へ変換できる。
- `AppController.request_save_vmd()` はTEXTありとvoice-onlyの両方でbase
  `VowelTimingPlan` とglobal hold / softnessを既存pipelineへ渡しており、
  canonical adjustment snapshotを参照しない。
- `write_morph_vmd()` はtimelineからshape生成とbinary書き込みを一つの関数で行い、
  prepared morph frame列だけを書き込むpublic境界を持たない。
- `OutputDiagnosticsSnapshot` のfingerprint schemaは
  `ms20-output-diagnostics-v1` であり、base timeline、observations、global writer
  parameterをidentityに含めるが、effective shapeとper-group tailを含めない。
- non-empty adjustmentは一時ERROR
  `adjustment_vmd_integration_pending` でVMD保存を禁止する。
- diagnostic reportはInput、Analysis、Generation、Saveability、Diagnosticsを出力するが、
  adjustment summaryを持たない。

この状態で一時ERRORだけを外すと、Previewと保存VMDが異なる。逆にraw adjustment
snapshotをfingerprintへ直接追加すると、requested値が変わってもclamp後のwriter
outputが同じであるoutput-equivalent editでfingerprintが不必要に変わる。
B5ではB2のeffective resultを保存正本にし、requested adjustmentではなくeffective
writer inputをidentityへ接続する必要がある。

## 3. 目的

- PreviewとVMD保存に同じB2 `EffectiveShapePlan` を使用する。
- TEXTありとvoice-onlyの両保存経路をeffective writer inputへ接続する。
- writerのshape生成を再実行せず、prepared morph frame列をVMD binaryへ書く境界を追加する。
- save-state fingerprint schemaをMS21へ更新し、effective morph frameとeffective
  per-shape tailをcanonical payloadにする。
- output-equivalent editではfingerprintを維持し、writer outputが変わるeditでは変更する。
- output変更後に古いWARNING確認済みfingerprintを再利用しない。
- ERROR保存禁止、WARNING同一fingerprint一回確認、ERROR時もreport保存可能という
  MS20 policyを維持する。
- diagnostics snapshotとdiagnostic reportへadjustment summaryを追加する。
- B4の一時保存禁止diagnosticと「B5対応待ち」表示を撤去する。
- 保存dialog cancelまたはwriter failureでbase、adjustment、selectionを変更しない。

## 4. In Scope

- current base inputとcanonical adjustment snapshotからのeffective output準備
- `EffectiveShapePlan` からfinal normalized morph frame列への既存B2 adapter接続
- prepared morph frame列をVMD binaryへ書くpublic writer境界
- existing TEXTあり / voice-only pipeline保存入口へのoptional effective plan接続
- save要求内でdiagnosticsとwriterへ同じeffective plan instanceを渡す統合境界
- MS21 save-state fingerprint schema
- canonical effective morph frame payload
- canonical effective per-shape tail payload
- base plan identityとeffective save-state fingerprintの分離
- adjustment diagnostics summary
- diagnostic reportの固定 `[Adjustment]` section
- WARNING確認のsame / changed fingerprint回帰
- B4一時diagnostic、専用Status、B5待ちnoticeの撤去
- save dialog cancel、writer failure、ERROR guardのstate保持回帰
- TEXTあり / voice-only両方のadjusted VMD保存test
- MS20 diagnostics / report / save policy回帰
- 実装完了時のB5 plan、Block Breakdown、routing文書への進捗記録

## 5. Out of Scope

- adjustment model、validation、resolver semantics、grouping順序の再定義
- Preview shape生成の別実装
- base `VowelTimingPlan` やobservationsへの補正値書き戻し
- Undo / Redo stack、50操作上限、coalescing
- analysis failure / cancel時の旧base rollback完成
- input変更、再解析、workspace resetを含むMS21 lifecycle全体の完成
- adjustment、selection、historyのsession外永続化
- 新しいVMD形式、VMD読み戻し、VMDとreportの自動同梱
- VMD model name、Shift_JIS、30fps、固定モーフ `あ / い / う / え / お` の変更
- MMD用WAV生成内容、保存先policy、audio三役の変更
- editor control、layout、themeの再設計
- README、配布用readme、Pipeline / GUI / Error仕様のimplemented同期（B7）
- dependency、package、release、version bump、tag、merge、push
- Qt / PySide6、network、cloud ASR、他ASR backend、外部送信、
  background通信、Whisper自動download

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- B4完了commit `0aa7fbf` を実装baselineとする。
- 作業開始時に未コミット変更と未追跡fileを確認し、ユーザー所有変更を保護する。
- Python 3.11以上、Windows 11、wxPython主系を維持する。
- base identity、adjustment snapshot、effective resolverの正本はB2実装を使用する。
- writer frameへの変換は
  `src.vmd_writer.effective_shape_adapter.build_morph_frames_from_effective_shape_plan()`
  を使用し、GUI、pipeline、diagnosticsでcontrol point生成を再実装しない。
- existing `write_morph_vmd()` と既存pipeline APIはlegacy / non-GUI caller向け互換入口として残す。
- B5実装前に本planをcurrent code / testへ再照合し、findingをP1 / P2 / P3で分類する。

### 6.1 計画作成baseline

2026-07-25、HEAD `0aa7fbf` で次の134件を実行した。

- B2 adjustment / effective resolver / adapter
- B4 editor core / wx integration
- pipeline / VMD
- MS20 output diagnostics / adapter
- MS20 WARNING save policy
- MS20 diagnostic report / report save flow
- MS20 diagnostics state integration

結果は134件pass表示、process exit code 0だった。計画作成開始時のworktreeはcleanであり、
production code、test code、dependency、build設定は変更していない。

### 6.2 現行実装から確定した接続点

- `MainFrame._build_current_base_timing_plan_input()` がPreview用base inputを構築する。
- `MainFrame._resolve_current_effective_plan()` がcanonical adjustmentとのidentity一致を
  fail closedで検証する。
- `AppController.request_save_vmd()` はdiagnostics snapshotを確認した後、save dialogを開き、
  input mode別pipelineへ移る。
- `build_output_diagnostics_snapshot_from_ui_state()` はbase timing planだけをdiagnostics
  coreへ渡すため、B5ではresolved effective outputを追加で受け取る必要がある。
- `write_morph_vmd()` のbinary書き込み部分はprepared frame writerへ分離できる。
- B4のedit / reset完了後は `sync_ui_state()` が呼ばれるため、effective outputを使う
  snapshotとfingerprintを直ちに再構築できる。

### 6.3 2026-07-26 実装状態整合レビューとP2 / P3解消

現行code、test、B1 / B2 / B4契約、Block Breakdownへ再照合し、P1なし、
P2 2件、P3 2件を検出した。本planとrouting文書へ次のように反映した。

- P2: B5完了時にREADMEと3正本仕様を同期する記載が、B7の
  State Integration / Regression / Docs所有権と重複していた。B5ではplan、
  Block Breakdown、Index、Roadmapの進捗記録だけを更新し、README、配布用readme、
  Pipeline / GUI / Error仕様はB7へ戻した。
- P2: effective writer inputが存在しない通常状態とresolver / adapter失敗が区別されて
  いなかった。`not_applicable / ready / invalid` の3状態を固定し、通常の未解析・
  再解析待ちを追加ERRORにせず、保存可能な解析結果からeffective inputを構築できない
  場合だけ `effective_writer_input_unavailable` ERRORとfingerprintなしにする。
- P3: AppControllerとmode別pipelineの直接mockを持つMS14 / MS19保存testを回帰対象へ
  追加した。
- P3: adjustment summaryのcount意味とempty / invalid時表現を固定し、effective countの
  未算出と正常な0件を区別する。

レビュー時のB2 / B4 / pipeline / VMD / MS20 diagnostics / report関連134件は
pass表示、process exit code 0だった。`git diff --check` もprocess exit code 0だった。
production code、test code、dependency、build設定は変更していない。

### 6.4 2026-07-26 実装・確認結果

- B2 `EffectiveShapePlan` からprepared morph frameを生成し、TEXTあり / voice-onlyの
  VMD保存とdiagnosticsへ同じeffective planを接続した。
- save-state fingerprintを `ms21-effective-output-v1` へ更新し、final normalized
  morph frameとeffective tailをidentityへ含めた。
- diagnostic reportへ固定Adjustment sectionを追加し、B4の一時
  `adjustment_vmd_integration_pending` ERRORとB5待ち表示を撤去した。
- B5実装の自動検証はpass表示・process exit code 0となり、ユーザーGUI確認も
  通過・問題なしと報告された。
- その後に合意された単イベントcrossfade仕様は、
  `MS21-B5_Explicit_Event_Crossfade_Additional_Fix_Plan.md` で追加補正として管理する。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| `src/vmd_writer/writer.py` | final normalized済み `MorphFrame` 列を検証しVMD binaryへ書くpublic境界を追加し、legacy `write_morph_vmd()` のbinary出力を共通化 |
| `src/vmd_writer/effective_shape_adapter.py` | B2 effective planからwriter frame列を作る既存責務を維持し、新binary writerへ渡せる型境界を明確化 |
| `src/vmd_writer/__init__.py` | 新public writer入口のexport |
| `src/core/pipeline.py` | TEXTあり / voice-onlyの既存validationとresult契約を維持したまま、optional effective planがある場合はB2 adapter経由で保存 |
| `src/core/output_diagnostics.py` | effective output DTO、adjustment summary、MS21 fingerprint schema、fail-closed診断、一時diagnostic撤去 |
| `src/core/diagnostic_report.py` | 固定 `[Adjustment]` sectionの追加 |
| `src/core/__init__.py` | additive diagnostics DTO / summary export |
| `src/gui_wx/output_diagnostics_adapter.py` | resolved effective planからdiagnostics inputとsummaryを構築 |
| `src/gui_wx/main_frame.py` | diagnostics/saveへ同じeffective planを渡す入口、一時Status・B5待ちnotice撤去 |
| `src/gui_wx/app_controller.py` | save要求単位のeffective plan取得、同じplanをsnapshotとmode別pipelineへ渡す |

### 7.2 新規test候補

- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`

既存testへ追加する方が責務を明確に保てる場合は、無理に新規fileへ分割しない。

### 7.3 回帰対象

- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- VMD writer grouping / interval / multipoint / zero guard関連test

### 7.4 実装完了時の文書同期対象

- `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

`docs/MS17_and_Beyond_Index.md` はrouting先またはactive milestone記載に変更が必要な場合だけ更新する。
`README.md`、`readme_mmdautolip.txt`、Pipeline / GUI / Error仕様はB7の
State Integration / Regression / DocsでMS21全体のimplemented lifecycleと同時に同期する。

## 8. 実装方針

### 8.1 effective resultを唯一の保存shape正本にする

保存要求では、次の順に処理する。

1. MainFrameがcurrent base inputを構築する。
2. current canonical adjustment snapshotとのidentity一致を検証する。
3. B2 `resolve_effective_shape_plan()` で `EffectiveShapePlan` を得る。
4. 同じplan instanceをdiagnostics snapshot構築とpipeline保存へ渡す。
5. writer adapterがfinal normalized morph frame列へ変換する。
6. prepared frame writerがVMD binaryを書き込む。

pipeline、diagnostics、controllerはcandidate、group、tail、slope、normalizationを再計算しない。
resolverを複数箇所へ再実装せず、MainFrameのcurrent effective plan入口を共有する。

### 8.2 writerのshape生成とbinary出力を分離する

`write_morph_vmd()` からbinary出力部分を、prepared `MorphFrame` 列を受け取る
public関数へ抽出する。関数名は実装前checkで既存命名と衝突しないことを確認し、
例として `write_morph_frames_vmd()` を使用する。

新入口は少なくとも次を検証する。

- frame countが `MAX_MORPH_FRAMES` 以下
- `frame_no` がboolでない0以上のint
- morph名が固定5モーフのいずれか
- valueがfinite
- output pathとmodel nameは既存writerと同じ処理
- `_finalize_morph_value()`、Shift_JIS固定長、VMD section countは既存と同じ

`write_morph_vmd()` はlegacy timelineからframeを生成した後、この新入口を呼ぶ。
これにより既存callerの結果を変えず、B5はB2 frame列を再shapeせず保存できる。

### 8.3 pipeline互換を維持する

`generate_vmd_from_text_wav()` と `generate_vmd_from_timing_plan()` にoptional
effective plan引数をadditiveに追加する。

- effective planなし: 現行legacy writer経路を維持する。
- effective planあり: current TEXT / WAV / timing planの既存validationを維持し、
  B2 adapterからprepared frame writerへ接続する。
- TEXTあり / voice-onlyのreturn DTOとerror wrappingを変えない。
- effective planを受け取った後にbase timelineからshapeを再生成しない。

AppControllerはinput mode分岐を維持するが、両分岐へ同じeffective planを渡す。

### 8.4 save要求内のsnapshotとwriterを同じplanへ固定する

`MainFrame.build_and_store_output_diagnostics_snapshot()` に、既に解決済みの
effective planを任意で受け取れる内部引数を追加する。

- 通常の `sync_ui_state()` / report保存: current stateからplanを解決する。
- VMD保存: controllerがplanを一度解決し、そのinstanceをsnapshot構築とpipelineへ渡す。
- diagnostics inputはeffective writer inputの状態を次の3値で明示する。
  - `not_applicable`: 有効な保存対象planがない通常状態
  - `ready`: effective plan、final frame、tail payloadを構築済み
  - `invalid`: 保存対象planはあるがresolver / adapterを完了できない
- `not_applicable` は未解析、再解析待ち、解析結果なしの通常状態であり、
  `effective_writer_input_unavailable` を追加しない。
- `ready` はeffective output DTOを必須とする。DTO欠落はcontract violationとして
  `invalid` と同じfail-closed結果にする。
- `invalid` は例外をGUIへ漏らさず、structured ERROR
  `effective_writer_input_unavailable` とfingerprintなしでVMD保存を禁止する。
- MainFrame / GUI adapterはresolver失敗を `current_diagnostic_failure` へ上書きせず、
  専用stateとしてdiagnostics coreへ渡す。
- identity contextは `base_input_unavailable / base_identity_mismatch /
  resolver_failed / adapter_failed` のstable reasonだけを使用し、raw exception textを
  fingerprintへ含めない。
- saveability確認からwriter呼び出しまでにUI thread上で補正stateを変更しない。

derived effective planを長期cacheまたは新しいworkspace正本にはしない。
正本はbase planとcanonical adjustment snapshotの組であり、effective planは要求単位の派生値とする。

### 8.5 fingerprint schemaをeffective outputへ移行する

schema versionは `ms21-effective-output-v1` とする。

fingerprint payloadは次を含む。

- schema version
- input mode
- normalized TEXT path
- normalized effective WAV path
- VMD model name
- effective writer input state
- final normalized effective morph frame列
- effective per-shape tail列
- stable diagnostic identity列

effective morph frameは `(frame_no, morph_name, canonical value)` の順序付きtupleとする。
valueは現行finite checkとfloat canonicalizationを使用し、raw floatをJSON payloadへ残さない。

effective per-shape tailはshape順に、次をcanonical化する。

- shape ordinal
- vowel
- effective hold frames
- effective softness frames
- effective slope ratio
- slope midpointの有無

requested hold / softness / slope、adjustment snapshot自体、base event index、
base plan identity digestはfingerprintへ含めない。base plan identityはstale補正拒否用であり、
effective save-state fingerprintとは別の値として保持する。

MS20 payloadのbase timeline、observations、raw global hold / softnessは、
effective outputと重複しoutput-equivalent identityを壊すためMS21 payloadから外す。
ただしglobal値がeffective frameまたはeffective tailを変えればfingerprintは結果として変わる。

`not_applicable` のpayloadはeffective writer input stateとempty frame / tail markerを
canonical化し、通常の未解析状態でも現行どおりdeterministic fingerprintを構築する。
`invalid` はunsafe inputのhashを作らず、fingerprintを `None` とする。

selection、selected event、editor revision、history position、Undo / Redo可否、
RightPane表示、playback、pan、zoomは含めない。

### 8.6 output-equivalent editとWARNING確認

- canonical snapshotが変わらないno-opではfingerprintを変えない。
- requested overrideが変わってもclamp後のeffective frameとeffective tailが同じなら
  fingerprintを変えない。
- effective frameまたはeffective tailが変わればfingerprintを変える。
- `confirmed_warning_save_state_fingerprint` をedit時に無条件clearしない。
- 保存時の現行比較を維持し、current fingerprintと一致する場合だけ確認を再利用する。
- output変更後は不一致になるため再確認する。
- output-equivalent editでは一致を維持し、不要な再確認を出さない。
- save dialog cancelまたはwriter failure後は、確認済みcurrent fingerprintを保持する
  MS20契約を維持する。

### 8.7 adjustment diagnostics summaryとreport

`OutputDiagnosticsSnapshot` にimmutableなadjustment summaryを追加する。
表示用summaryはfingerprint sourceと分離し、次のfieldを固定する。

- `base_plan_identity_digest: str | None`
- `adjustment_present`
- `adjusted_event_count`
- `effective_shape_count: int | None`
- `effective_morph_frame_count: int | None`

fieldの意味とempty / failure表現は次で固定する。

- `adjustment_present` はcurrent canonical snapshotにnon-empty adjustmentが1件以上あれば
  `True` とする。
- `adjusted_event_count` はcurrent canonical snapshotのnon-empty adjustment entry数とする。
  effective outputとの差分event数ではない。
- base identityを取得できない場合は `base_plan_identity_digest=None` とする。
- `ready` ではeffective shape / morph frameの実数を0以上のintで記録する。
- `not_applicable / invalid` ではeffective countを `None` とし、正常に算出した0件と
  区別する。
- report formatterは `None` を既存empty表現 `N/A` で出力する。

diagnostic reportは `[Generation]` の後、`[Saveability]` の前に次を出力する。

```text
[Adjustment]
Base Plan Identity: <digest または N/A>
Adjustment Present: yes / no
Adjusted Event Count: <int>
Effective Shape Count: <int>
Effective Morph Frame Count: <int>
```

未算出の場合、`<digest>`、`<int>` は `N/A` とする。

reportはrequested補正値やsource text/audio内容を新たに出力しない。
base identity digestはreportのtraceability用であり、save-state fingerprintへ混入させない。
ERROR時も元音声pathがあればreport保存可能という現行policyを維持する。

### 8.8 B4一時guardを完全に撤去する

adjusted writerとfingerprint統合後、次を同一変更で撤去する。

- `DiagnosticSnapshotInput.adjustment_vmd_integration_pending`
- diagnostic code / message / ordering
  `adjustment_vmd_integration_pending`
- MainFrameの専用bottom Status
  `解析完了（個別補正あり・VMD保存はB5対応待ち）`
- editor noticeの `VMD保存連携はMS21-B5で対応します`
- reset noticeの `VMD保存はB5対応待ちです`
- 一時guard専用test期待値

non-empty adjustmentだけを理由にERRORにしない。別のERRORが存在する場合は従来どおり保存禁止とする。

### 8.9 failure / cancel時のstate保持

- save dialog cancel: writerを呼ばず、adjustment、selection、base、diagnostics、
  WARNING確認済みfingerprintを保持する。
- writer failure: output errorを表示し、adjustment、selection、base、diagnostics、
  WARNING確認済みfingerprintを保持する。
- save success: `last_vmd_output_dir` とStatusだけを現行どおり更新し、adjustmentを保持する。
- ERROR guard: save dialogとwriterを呼ばない。
- B6 historyはまだ存在しないためB5で履歴操作を追加しない。将来history fieldが追加されても
  save requestがそれを変更しない境界を維持する。

## 9. 詳細ステップ

### Step 1: B5 pre-implementation check

1. branch、worktree、HEADを確認する。
2. B1、B2、B4、Block Breakdownとcurrent code / testを再照合する。
3. writer import順、`src.*` / top-level mixed namespace回帰を確認する。
4. fingerprint schema、report fixture、manual snapshot constructorの変更影響を列挙する。
5. findingをP1 / P2 / P3で分類し、P2 / P3をplanへ反映して再チェックする。

### Step 2: prepared morph frame writer

1. binary出力をpublic prepared-frame関数へ抽出する。
2. frame / morph / value / count validationを追加する。
3. legacy `write_morph_vmd()` を新入口へ委譲する。
4. existing VMD binaryとframe列が変わらないことをtestする。
5. effective adapter frameを直接保存し、binary recordが一致することをtestする。

### Step 3: effective pipeline接続

1. mode別pipelineへoptional effective planを追加する。
2. legacy呼び出しの結果を維持する。
3. effective plan指定時はB2 adapterとprepared writerだけを使用する。
4. OSErrorを既存 `PipelineError` に変換する。
5. TEXTあり / voice-only両方の保存testを追加する。

### Step 4: diagnostics effective output DTO

1. diagnostics coreにimmutable morph frame / tail inputを追加する。
2. adjustment summaryを追加する。
3. adapterがB2 planからDTOを構築する。
4. `not_applicable / ready / invalid` をdiagnostics inputへ追加する。
5. non-finite、unsupported morph、invalid frame、`ready` 時のDTO欠落を
   `invalid` としてfail closedにする。
6. base identity digestはsummaryにだけ渡す。
7. 未解析 / 再解析待ちの `not_applicable` が追加ERRORにならないことをtestする。

### Step 5: MS21 fingerprint

1. schemaを `ms21-effective-output-v1` へ更新する。
2. effective frameとeffective tailのcanonicalizationを実装する。
3. 旧base writer payloadをMS21 payloadから外す。
4. stable diagnostics identityとpath policyを維持する。
5. same output / changed output / selection-only / requested-only editをtestする。

### Step 6: MainFrame / controller統合

1. current effective planを要求単位で解決する入口を整理する。
2. save requestでは同じplanをsnapshotとpipelineへ渡す。
3. resolver / adapter failureをstructured ERRORへ変換する。
4. existing ERROR / WARNING / save dialog順序を維持する。
5. TEXTあり / voice-only両分岐をeffective planへ接続する。

### Step 7: temporary guard撤去

1. 一時diagnostic field / code / message / orderを削除する。
2. bottom StatusのB5待ち特例を削除する。
3. editor / reset noticeのB5待ち表現を現在形へ更新する。
4. non-empty adjustmentで保存button / menu / controllerが有効になることをtestする。
5. 別ERRORがある場合は引き続き無効であることをtestする。

### Step 8: report統合

1. snapshotへadjustment summaryを追加する。
2. 固定 `[Adjustment]` sectionを追加する。
3. adjustmentなし / あり / ERROR時のreportをtestする。
4. UTF-8、LF、BOMなし、atomic replace、既存file保持回帰を維持する。

### Step 9: state保持と回帰

1. warning confirm same / changed fingerprintをtestする。
2. save dialog cancelでstateを保持する。
3. writer failureでstateを保持する。
4. save successでもadjustment / selectionを保持する。
5. report save failureがcurrent snapshotとfingerprintを変更しないことを維持する。

### Step 10: verificationと文書同期

1. B5専用testを実行する。
2. B2 / B4 / MS20 diagnostics / report / writer関連回帰を実行する。
3. 全体test、`compileall src tests`、`git diff --check` を実行する。
4. user manual GUI確認項目を提示する。
5. ユーザー確認後に本plan、Block Breakdown、Index、RoadmapをB5実装済み状態へ同期する。
6. README、配布用readme、Pipeline / GUI / Error仕様はB7へ引き継ぐ。

## 10. 状態遷移 / データ契約

### 10.1 保存データフロー

```text
current VowelTimingPlan + source duration + global shape parameters
  + current canonical AdjustmentLayerSnapshot
    -> B2 resolve_effective_shape_plan()
      -> EffectiveShapePlan
        -> Preview adapter
        -> writer adapter -> final normalized MorphFrame tuple
        -> diagnostics effective frame / effective tail DTO
```

Preview、writer、diagnosticsは同じresolver結果から分岐する。
adjustment snapshotを各consumerが独自解釈してはならない。

### 10.2 fingerprint identity

| 値 | 用途 | fingerprintへ含める |
| --- | --- | --- |
| base plan identity digest | stale selection / adjustment拒否、report traceability | いいえ |
| canonical adjustment snapshot | editor正本、将来history | いいえ |
| final normalized morph frames | 実際のwriter frame入力 | はい |
| effective per-shape tail | group後に採用されたhold / softness / slope意味 | はい |
| requested override | editor表示、history | いいえ |
| VMD model name | binary writer input | はい |
| selection / history / playback | UI状態 | いいえ |

### 10.3 save policy

| current snapshot | 保存操作 |
| --- | --- |
| ERRORあり | dialogを開かず保存禁止 |
| WARNINGあり・fingerprint未確認 | 確認後にdialog |
| WARNINGあり・同じfingerprint確認済み | 再確認せずdialog |
| WARNINGあり・fingerprint変更 | 再確認後にdialog |
| INFOのみ / 診断なし | dialog |
| fingerprintなし | fail closed |

### 10.4 effective writer input state

| state | 条件 | diagnostic | fingerprint |
| --- | --- | --- | --- |
| `not_applicable` | 未解析、再解析待ち、有効な保存対象planなし | 既存状態診断だけ | unavailable markerから構築 |
| `ready` | effective frame / tail DTO構築済み | 通常policy | effective outputから構築 |
| `invalid` | 保存対象planあり、resolver / adapter失敗、またはready DTO欠落 | `effective_writer_input_unavailable` ERROR | `None` |

### 10.5 save terminal result

| result | base / adjustment / selection | confirmed WARNING fingerprint | 保存先履歴 |
| --- | --- | --- | --- |
| dialog cancel | 保持 | 保持 | 変更しない |
| writer failure | 保持 | 保持 | 変更しない |
| writer success | 保持 | 保持 | 成功先directoryへ更新 |
| ERROR guard | 保持 | 保持 | 変更しない |

## 11. テスト方針

### 11.1 writer単体

- prepared framesから既存VMD header / model / morph record / zero section countを出力する。
- legacy writer refactor前後のbinaryが一致する。
- frame count超過、negative / bool frame、unsupported morph、non-finite valueを拒否する。
- B2 adapterのfinal normalized frame列と保存recordが一致する。
- fixed morph、Shift_JIS、30fpsの既存契約を維持する。

### 11.2 fingerprint / diagnostics単体

- empty adjustmentとbase-only effective outputがstable fingerprintを作る。
- peak、start、end、hold、softness、slopeでeffective outputが変わるとfingerprintが変わる。
- requested値だけが変わりeffective frame / tailが同じ場合は変わらない。
- selection、editor revision、playbackは変えない。
- base identity digestはreport summaryへ出るがfingerprintに含まれない。
- `not_applicable` は追加ERRORを生成せずdeterministic fingerprintを持つ。
- `invalid` effective inputはfingerprintなしのERRORとなる。
- `adjustment_vmd_integration_pending` が生成されない。

### 11.3 GUI / controller統合

- TEXTありのadjusted saveがeffective frame列をpipelineへ渡す。
- voice-onlyのadjusted saveも同じ経路を使う。
- non-empty adjustmentだけでは保存button / menuを無効化しない。
- ERRORはbutton / menu / controllerの全入口で保存を止める。
- WARNING同一fingerprintは一度だけ確認する。
- output変更後は再確認し、output-equivalent editでは再確認しない。
- cancel / failure / successでadjustmentとselectionを保持する。

### 11.4 report

- `[Adjustment]` sectionと5 fieldの順序を固定する。
- adjustmentなし / ありを区別する。
- `adjusted_event_count` はcanonical adjustment entry数である。
- effective countの未算出は `N/A` とし、正常な0件と区別する。
- ERROR時もreport生成できる。
- path、UTF-8、LF、BOMなし、temp close-before-replaceを維持する。

### 11.5 回帰

- B2 resolver / adapter
- B4 editor / Preview
- pipeline / VMD writer
- MS20 diagnostics / WARNING / report / state integration
- workspace reset、analysis lifecycle、late worker result discard
- wx RightPane / status / action state

テスト結果はpass表示とprocess exit codeを分けて報告する。
ユーザーGUI確認を自動testで代替したとは記載しない。

### 11.6 ユーザー手動GUI確認候補

- TEXTあり解析後、選択eventのpeak / start / endを変更し、Previewと保存VMDの口形が一致する。
- voice-onlyでも補正後VMDを保存できる。
- group tailのhold / softness / slope変更が保存VMDへ反映される。
- non-empty adjustment時もVMD保存button / menuが使用できる。
- WARNINGがある場合、同じ補正状態では一度だけ確認される。
- writer outputが変わる補正後は再確認される。
- save dialog cancelと保存失敗後も補正と選択が残る。
- diagnostic reportのAdjustment sectionが現在状態を示す。

## 12. 受け入れ条件

- Previewと保存VMDが同じB2 `EffectiveShapePlan` を使用する。
- B5でresolver、candidate、grouping、tail semanticsを再定義していない。
- TEXTあり / voice-only両方でadjusted VMDを保存できる。
- adjustmentなしの既存VMD出力互換を維持する。
- final normalized morph frame列がwriterへ一度だけshape済み入力として渡る。
- fingerprint schemaが `ms21-effective-output-v1` である。
- effective output変更でfingerprintが変わる。
- output-equivalent edit、selection、playbackではfingerprintが変わらない。
- effective per-shape tailがfingerprint payloadに含まれる。
- base plan identityとsave-state fingerprintが分離されている。
- 古いWARNING確認済みfingerprintをoutput変更後に再利用しない。
- ERROR保存禁止とERROR時report保存可能を維持する。
- effective writer inputの `not_applicable / ready / invalid` が区別され、
  未解析状態を追加ERRORにしない。
- `invalid` は `effective_writer_input_unavailable` ERRORとfingerprintなしでfail closedになる。
- `adjustment_vmd_integration_pending` とB5待ち表示が残っていない。
- reportに固定Adjustment sectionがある。
- save cancel / failureでadjustment、selection、baseを失わない。
- dependency、VMD形式、MMD用WAV、固定モーフ、wxPython主系を変更していない。
- 関連自動testがpassし、process exit code 0である。
- ユーザーGUI確認結果を実施後に記録する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| Previewとsaveで別planを解決する | save要求内で同じeffective plan instanceをsnapshotとpipelineへ渡す |
| pipelineがbase timelineからshapeを再生成する | effective plan指定時はB2 adapterとprepared writerだけを使う |
| raw adjustmentをhashしoutput-equivalent editで再確認が出る | final effective frameとeffective tailだけをadjustment由来identityにする |
| base identityをhashし責務が循環する | base identityはstale guard / report専用としfingerprintから除外する |
| global parameterを外してoutput変更を見逃す | global値そのものではなく変化後のeffective frame / tailをhashする |
| prepared writerでlegacy binaryが変わる | `write_morph_vmd()` も同じbinary関数へ委譲しbyte比較回帰を置く |
| invalid effective planでGUI同期が例外終了する | structured ERROR、fingerprintなしでfail closedにする |
| 未解析のinput欠落をresolver失敗と誤認する | `not_applicable / ready / invalid` の3状態で区別する |
| effective未算出を正常な0件とreportする | optional countと `N/A` 表示を使用する |
| 一時guardの一部だけが残る | field、code、message、Status、notice、testを同じStepで検索・撤去する |
| warning confirmationをeditごとにclearする | current fingerprint比較を正本にし、無条件clearを追加しない |
| save cancel / failureでeditor stateをclearする | save terminal pathではworkspace stateを変更しない回帰を置く |
| reportへ過剰な補正値を出す | aggregate summaryだけを固定し、requested値や本文を追加しない |
| mixed import namespaceでclass identityが分裂する | B2 import-order / mixed namespace regressionを維持する |

## 14. Codex 実装時の注意

- 実装開始前に `git status`、`git branch`、`git log --oneline -n 10` を
  一つずつ実行する。
- `docs/MS17_and_Beyond_Index.md` を最初に読み、active routingを再確認する。
- pre-implementation check中はproduction codeとtest codeを変更しない。
- user-owned未コミット変更をrestore、上書き、無断stageしない。
- B2 resolverとeffective adapterを使用し、GUIやpipelineへshape計算を複製しない。
- base `VowelTimingPlan` とcanonical adjustment snapshotを混同しない。
- requested値、effective値、final normalized writer frameを区別する。
- private writer helperへの新規GUI依存を作らず、public境界を追加する。
- existing legacy pipeline callerを破壊しないadditive signatureにする。
- `ERROR` / `WARNING` policyを弱めない。
- `not_applicable` と `invalid` を同じmissing inputとして処理しない。
- report failure、VMD failure、dialog cancelでworkspace stateをclearしない。
- dependencyを追加しない。
- MMD用WAV、audio入力、解析用WAVの役割を混同しない。
- Qt / PySide6、network、cloud、telemetry、auto-downloadを追加しない。
- testは小さい対象から実行し、pass表示とprocess exit codeを別々に記録する。
- implementation diffを検証前に自己監査し、scope外変更と一時文言の残存を確認する。
- user manual GUI確認前に「確認済み」と記載しない。
- merge、push、tag、releaseは明示依頼があるまで行わない。
