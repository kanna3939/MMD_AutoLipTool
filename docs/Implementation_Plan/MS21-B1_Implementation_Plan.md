# MS21-B1 Implementation Plan

## 1. 文書情報

- 文書名: MS21-B1 Implementation Plan
- 配置: `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- 対象Block: MS21-B1
- Block名: Adjustment Contract / Current-State Pre-check
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `6cd8233 Close out MS20 diagnostics milestone`
- 作成日: 2026-07-20
- 文書ステータス: Completed / Contract Fixed / Ready for MS21-B2 Planning
- B1実施日: 2026-07-21
- B1実施基準HEAD: `c7f2c20 Plan MS21 adjustment foundation`
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/MS16_GUI_Layout_Spec_for_Antigravity.md`

MS21-B1は読み取り調査と契約固定だけを行うBlockである。production code、GUI、test code、dependency、build設定を変更しない。

## 2. 背景

MS21では、自動解析結果を直接書き換えず、発音イベント単位のユーザー補正をPreviewとVMDへ同じ意味で反映する。

現行実装には次の下地がある。

- `VowelTimingPlan.timeline` は解析済みのevent列を保持する。
- `PeakValueObservation.event_index` は生成時のtimeline indexに対応する。
- writerとPreviewは同じgrouping / shape helper familyを使用する。
- `MultiPointEnvelopeSpec.source_event_indices` はgroup内の複数source eventを保持する。
- `PreviewSegment` は現在 `source_event_index` を1件だけ保持し、multi-point shapeでは先頭indexだけを公開する。
- writerのsame-vowel candidate変換は、元eventをskipして負数のsynthetic source tokenを持つshape pointへ置換する場合がある。この内部tokenはbase event identityではない。
- `UiState.selected_source_event_index`、Preview highlight、RightPane summaryは存在する。
- Previewのmouse操作はdrag panだけで、click hit-testは存在しない。
- `closing_hold_frames` と `closing_softness_frames` は全体parameterであり、grouped shapeではgroup末尾tailへ作用する。
- `slope_mid` はsoftness適用時に生成され、値はtail anchorの70%に固定されている。
- MS20のsave-state fingerprintはbase timing plan、observations、writer parameter、diagnostics identityを正本にする。

一方、MS21に必要なadjustment layer、base plan identity、per-event validation、effective resolver、history transactionは存在しない。B1でこれらの意味と所有権を固定しなければ、B2以降でPreview、writer、UiState、Undo / Redoが別々の解釈を持つ。

## 3. 目的

- canonical event identityとbase plan identityを固定する。
- base、adjustment、effective resultの責務を固定する。
- 開口量、開始、終了、hold、softness、slopeの意味・単位・default・validation境界を固定する。
- groupingより前後のadjustment適用順を固定する。
- multi-source grouped shapeの選択・編集可能範囲を固定する。
- adjustment snapshotとUndo / Redo transaction境界を固定する。
- reanalysis、failure、cancel、input変更、reset、late callbackの保持・破棄規則を固定する。
- MS20 fingerprint、WARNING確認、diagnostic reportへの引き継ぎを固定する。
- B2からB7の実装・test所有権を分離する。

## 4. In Scope

- 現行repositoryの読み取り監査
- `VowelTimingPlan.timeline` と `PeakValueObservation.event_index` の対応確認
- writer / Previewのnormalization、sorting、grouping、shape生成順序確認
- canonical `base_event_index`、内部 `shape_source_token`、複数source provenance、`event_ranges` の対応確認
- base plan identityとplan-local event keyの契約
- adjustment fieldの初期契約
- per-event tail編集とgroup末尾制約
- hit-test候補とoverlap優先規則
- immutable adjustment snapshot境界
- Undo / Redo最大50操作とcoalescing境界
- lifecycle matrixとrollback契約
- fingerprint schema更新方針
- B2からB7へのhandoff
- B1実施結果、P1 / P2 / P3、B2着手可否の記録

## 5. Out of Scope

- production code変更
- wxPython GUI変更
- test code追加・変更
- B2 adjustment model / resolverの先行実装
- Preview click選択の実装
- RightPane編集controlの実装
- VMD writer変更
- Undo / Redo実装
- README、配布用readme、正本仕様のMS21実装済み更新
- VMD読み戻し
- adjustment / selection / historyのsession外永続化
- 任意keyframe編集
- 複数event一括編集
- 母音種別変更
- MS22以降のpreset / profile / model選択 / 一括出力
- dependency追加
- package、release、version bump、tag、merge、push
- Qt / PySide6復活
- network、cloud ASR、他ASR backend、音声外部送信、background通信、Whisper自動download

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- MS20 Closeout Aと `main / origin/main = 6cd8233` の完了状態を戻さない。
- `c7f2c20` でcommit済みのMS21 Block Breakdown、B1 plan、Index、Roadmapを今回の上位計画として保護する。
- wxPythonを主系GUIとする。
- 固定モーフ `あ / い / う / え / お` を変更しない。
- `VowelTimingPlan` はfrozen dataclassだが、内部collectionはlistであり、構造上のdeep immutableではない。B2はbase collectionを変更しない契約をtestで固定する。
- 現行writerはpeak valueを一般的な上限へclampしない。B1では解析時 `morph_upper_limit`、writerの非負・有限値条件、Previewの表示clampを混同しない。
- B1開始時に現行HEAD、branch、未コミット差分を再確認する。

### 6.1 計画作成baseline

- selection foundation: 4件pass表示、process exit code 0
- Preview / grouping / multi-point shape: 52件pass表示、process exit code 0
- output diagnostics / WARNING save policy: 24件pass表示、process exit code 0
- workspace reset / late callback / analysis: 15件pass表示、process exit code 0
- failure / error / fatal表示はない。
- 計画作成時点でproduction code、GUI、test code、dependency、build設定は変更していない。

### 6.2 初回pre-implementation review修正

- P1: なし。
- P2: 4件を修正した。
  - negative synthetic source tokenをcanonical base event identityから分離した。
  - automatic candidate shapeよりユーザー補正を優先し、影響spanを再評価する順序へ固定した。
  - shape provenanceとgroup-aware shared resolverの所有をB2へ集約した。
  - midpointを生成できないslopeはdisabled / reject / canonical removalとし、latent overrideを禁止した。
- P3: 2件を修正した。
  - 既存render-only selection setterの未知index許容と、B3 canonical selection commitのvalidationを分離した。
  - hold / softnessを0から100の整数範囲へ固定し、model側は範囲外をclampせず拒否する。
- 修正は本計画、Block Breakdown、Index、Roadmapに限定し、production code、GUI、test code、dependency、build設定は変更していない。
- 修正後再チェックではP1 / P2 / P3の残存なしと判定した。
- selection 4件、Preview / grouping / multi-point 52件、diagnostics / save policy 24件、reset / late callback / analysis 15件はすべてpass表示、各process exit code 0だった。
- `git diff --check` はprocess exit code 0、MS21 plan 2文書の末尾空白検索は該当なしだった。

### 6.3 2026-07-21 pre-implementation check修正

- P1: なし。
- P2: 2件を修正した。
  - observations省略時のcanonical event identityと、observations present時の対応検証を分離した。
  - analysis failure時rollbackを現行正本仕様からの意図的なMS21変更とし、再利用条件、diagnostics、保存可否、B7文書同期を固定した。
- P3: 1件を修正した。
  - 未コミット文書保護の古い前提を、`c7f2c20` のcommit済み計画基準へ更新した。
- 修正後の再チェックでは、P1 / P2 / P3の残存なしと判定した。
- 修正後に指定95件と補完72件、合計167件を再実行し、すべてpass表示、各process exit code 0だった。`git diff --check` もprocess exit code 0だった。

## 7. 対象ファイル

### 7.1 主要確認対象

| ファイル | 確認する責務 |
| --- | --- |
| `src/core/pipeline.py` | `VowelTimingPlan`、timeline、observation index、interval / peak生成 |
| `src/core/preview_transform.py` | timeline normalization、sorting、grouping、PreviewSegment metadata |
| 新規候補 `src/core/effective_shape_plan.py` | Preview / writer共通のshape準備、candidate再評価、base event provenance契約 |
| `src/vmd_writer/writer.py` | frame変換、grouping、multi-point shape、tail、normalization |
| `src/core/output_diagnostics.py` | canonical writer payload、fingerprint schema、finite value validation |
| `src/core/diagnostic_report.py` | report sectionとgeneration summary |
| `src/gui_wx/ui_state.py` | base plan、selection、diagnostics、reset / invalidate / success |
| `src/gui_wx/preview_panel.py` | viewport座標、pan gesture、selection highlight、summary |
| `src/gui_wx/placeholder_panels.py` | Preview callback forwarding |
| `src/gui_wx/right_pane.py` | 選択イベントtabの現行placeholder / summary |
| `src/gui_wx/main_frame.py` | Preview生成、selection同期、analysis lifecycle、Busy action |
| `src/gui_wx/app_controller.py` | input commit、workspace reset、VMD保存入口 |
| `src/gui_wx/analysis_worker.py` | current job resultとbase plan確定境界 |
| `src/gui_wx/parameter_panel.py` | `morph_upper_limit`、global hold / softnessの現行範囲 |

### 7.2 正本文書

- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/MS16_GUI_Layout_Spec_for_Antigravity.md`

### 7.3 test参照対象

B1ではtestを変更しない。次の既存testから現在の挙動とB2以降の回帰境界を読み取る。

- `tests/test_wx_ms16_b6_event_selection_foundation.py`
- `tests/test_preview_transform.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_peak_value.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_wx_ms15_b3_playback.py`

### 7.4 B1で変更する文書

- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- 必要な契約補正に限定した `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- routing / phase表示に限定した `docs/MS20_and_Beyond_Index.md`
- 次作業表示に限定した `docs/MS20_and_Beyond_Roadmap.md`

`README.md`、`readme_mmdautolip.txt`、`docs/repo_milestone.md`、`docs/Version_Control.md` はB1で変更しない。

## 8. 実装方針

B1にproduction実装はない。次の順序で事実を監査し、初期契約を確定または根拠付きで補正する。

1. base eventとobservationのindex対応を確認する。
2. writer / Previewがsource indexを付与する前後のsortingを確認する。
3. plan-local event keyとbase plan identityを分離する。
4. adjustmentをoptional absolute overrideまたはframe offsetとして正規化する。
5. 自動candidate shapeへbase provenanceを付与し、ユーザー補正を優先してからgrouping / shape生成する順序を固定する。
6. grouped shapeの末尾tail制約をPreview / writer双方へ適用する。
7. adjustment layer全体をimmutable snapshotとしてhistoryへ渡す。
8. MS20 fingerprintはeffective writer inputを参照し、base identityと循環させない。
9. lifecycleはcurrent job成功時のcommitと失敗 / cancel時のrollbackを分ける。

## 9. 詳細ステップ

### Step 1: repository基準線の固定

- `git status`、branch、最近履歴を一つずつ確認する。
- 未コミット変更と未追跡fileを記録する。
- MS21 Roadmap、Block Breakdown、本計画の役割を確認する。
- B1中にproduction code / test code差分が発生していないことを継続監査する。

### Step 2: canonical event identity監査

canonicalな編集identityは次とする。

```text
base_event_index
  = current base VowelTimingPlan.timeline の0-based ordinal
  = observations present時は対応する PeakValueObservation.event_index
```

- `base_event_index` は0以上であり、selection、adjustment key、history keyへ使用する唯一のevent identityとする。
- `base_event_index` はwriter / Previewのnormalization・filter・sortingより前のbase timeline順で付与し、全shape変換でprovenanceとして保持する。
- `observations is None` のplanを許可する。この場合はobservation対応を検証せず、observation依存のautomatic candidate shapingを無効化するが、base eventの選択・補正は許可する。
- observations present時は `len(observations) == len(timeline)`、`observations[index].event_index == index`、`observations[index].vowel == timeline[index].vowel` をすべて必須とし、不一致をfail closedで拒否する。
- presentの空observationsはbase timelineも空の場合だけ許可する。非空timelineに対する空list / tupleは `None` と同一視せず不整合として拒否する。
- writer内部で生成される負数のsynthetic source indexは `shape_source_token` として分離する。synthetic tokenは選択・編集・adjustment keyへ使用しない。
- writer / Previewのgroup後segment ordinalはevent identityにしない。
- `PreviewSegment.source_event_index` の先頭indexだけをmulti-source groupの完全なidentityとみなさない。
- B2でPreviewとwriterが共有するshape provenanceを構築し、B3へ実base eventだけの `source_event_indices` とevent別hit regionを渡す。
- same-vowel candidateによりbase eventがskip / synthetic置換されても、対応するbase eventのrangeとindexをprovenanceから失わない。
- timeline sorting後にindexが付け直される経路とobservation順がずれる可能性を監査する。
- `vowels[index]`、`timeline[index].vowel`、`observations[index].event_index / vowel` の不一致は通常解決せずfail closedとする。

共通provenanceの初期構造:

```text
ShapeEventProvenance
  - shape_source_token: int
  - contributing_base_event_indices: tuple[int, ...]
  - event_frame_ranges: tuple[(base_event_index, start_frame, end_frame), ...]
  - is_synthetic: bool
```

- `contributing_base_event_indices` と `event_frame_ranges` に負数tokenを混入させない。
- visible segment metadataとは別に、effective base event rangeからevent別hit regionを構築する。zero-spanまたはcandidateで置換されたbase eventも、決定的なrange規則により選択可能とする。

### Step 3: base plan identity監査

plan-local indexを別baseへ誤適用しないため、adjustment snapshotはbase plan identityへ結び付ける。

初期構造:

```text
BasePlanIdentity
  - schema_version
  - canonical base timeline
  - observations_state: none / present
  - canonical observations
  - source_duration_frames
```

- identityはpath、UI文言、object identity、`repr()`、selection、playback位置を含めない。
- base identityは未補正planから生成し、effective output fingerprintと分離する。
- `source_duration_frames` は解析正本音声のdurationを30fpsの `int(round(seconds * 30))` で一度だけ変換した0以上の整数とする。調整可否に影響するためbase identityへ含める。
- source durationが欠落、非有限、負値、またはbase eventのend frameより小さい場合はbase input自体をfail closedで拒否する。
- adjustment snapshotとresolverへ渡したbase identityが一致しない場合はfail closedとする。
- base plan identityのcanonical payloadはB2のwriter非依存coreで所有し、MS20 `output_diagnostics` のprivate canonicalizationを直接importしない。diagnostics側は後続B5でeffective resultを受け取り、save-state fingerprint用payloadを構築する。
- B2ではhashだけでなくcanonical payload自体を単体test可能にする。

### Step 4: adjustment field契約の確定

初期contract:

| field | canonical意味 | 単位 / default | validation初期方針 |
| --- | --- | --- | --- |
| `peak_value` | effective最大開口量のabsolute override | float / `None` はbase | finiteかつ0以上、analysis upper limitとは独立 |
| `start_offset_frames` | base start frameからの差分 | int frame / 0 | `0 <= effective start <= peak` |
| `end_offset_frames` | base end frameからの差分 | int frame / 0 | `peak <= effective end <= source duration` |
| `hold_frames` | event / group tailのabsolute override | int frame / `None` はglobal値 | `0 <= value <= 100`、group末尾だけ有効 |
| `softness_frames` | event / group tailのabsolute override | int frame / `None` はglobal値 | `0 <= value <= 100`、group末尾だけ有効 |
| `slope_ratio` | closing `slope_mid` のtail anchor比 | float / default `0.7` | finite、`0.0 <= value <= 1.0`、group末尾だけ有効 |

ユーザー採用済み判断:

- `slope_ratio` は独立補正値である。
- `slope_mid_value = tail_anchor_value * slope_ratio` とする。
- adjustment未指定時は現行writerの `0.7` を維持する。
- `slope_ratio` はeffective softnessが `slope_mid` を生成できる場合だけ編集可能とする。
- midpointを生成できない場合、UIはdefault `0.7` を表示してcontrolを無効化し、新しいslope overrideを拒否する。
- groupingまたはclamp変更でmidpointが消えた場合、同じtransaction内のcanonicalizationで既存slope overrideを削除し、作用しないlatent overrideを保持しない。
- `hold_frames` / `softness_frames` は現行global controlと同じ0から100の整数範囲を採用する。GUI controlは入力を制限し、model / resolverは範囲外値をclampせず拒否する。

B1固定規則:

- `peak_value` はpost-analysis補正であり、analysis時の `morph_upper_limit` でreject / clampしない。writerの現行契約に合わせ、finiteかつ0以上を許可し、Previewの描画clampとwriter出力値を混同しない。
- base start / peak / endはそれぞれ `int(round(seconds * 30))` でframe化し、`0 <= start <= peak <= end <= source_duration_frames` を必須とする。隣接shapeとの競合は入力値をclampせず、後段のdeterministic grouping / tail clampで解決する。
- `peak_value == base peak`、start / end offset `0`、hold / softnessがcurrent global値と同値、active slopeがdefault `0.7` のoverrideはcanonical snapshotから削除する。空entryも保持しない。
- canonical編集単位は整数frameとする。秒表示は `frame / 30`から毎回導出し、秒入力を提供する場合もcommit時に一度だけ `int(round(seconds * 30))` へ量子化したあとcanonical frameからUIを再表示する。

### Step 5: effective resolver順序の確定

固定順序:

```text
base VowelTimingPlan
  -> base identity / adjustment key validation
  -> observation整合性を解決
  -> cross-vowel / same-vowel automatic candidate shapeをprovenance付きで準備
  -> peak / start / endを対応するreal base eventへ適用
  -> 影響candidate spanを補正後eventで再評価
  -> immutable effective event / provenance列を生成
  -> nearby same-vowel grouping
  -> group末尾のreal base eventへhold / softness / active slopeを適用
  -> shape生成 / final normalization
  -> PreviewまたはVMD
```

- ユーザー補正はautomatic candidate変換より優先し、candidate変換が明示補正fieldを上書きしてはならない。
- skip / synthetic置換されたbase eventが補正された場合、該当spanのautomatic synthetic replacementを無効化して補正後eventを含めて再評価する。candidate前提を満たさなければreal base event列を使用する。
- shared resolverはautomatic shaping、provenance、補正優先、groupingまでをPreviewとwriterの共通契約として提供する。B4 / B5で別々の順序を再実装しない。
- B2は専用 `EffectiveShapePlan` DTOを返す。既存 `VowelTimingPlan` はbase解析正本のままとし、tail override、provenance、synthetic tokenを追加して再利用しない。
- `src/core/effective_shape_plan.py` はwriter非依存のDTO・validation・resolverを所有し、`src.vmd_writer.writer` とwxPythonをimportしない。writerとPreviewがcore resultを消費する一方向依存とし、既存writer private helperの必要ロジックはB2でcoreへ抽出する。
- Preview cacheやRightPane control値からwriter inputを復元しない。
- base `VowelTimingPlan.timeline` とobservationを変更しない。
- start / end変更後に旧observation intervalをそのまま使用できる範囲を監査する。
- observationを保持できない場合は全observationsを無条件破棄するのではなく、影響範囲とwriter candidate依存を根拠に規則化する。

### Step 6: grouped shapeの選択・編集契約

ユーザー採用済み判断:

- multi-source grouped shapeを単一base eventと扱わない。
- click位置をgroup内event rangeへ対応付け、canonical source eventを1件選ぶ。
- 開口量、開始、終了は各source eventで編集可能とする。
- `hold / softness / slope` は再grouping後のgroup末尾real base eventだけ編集可能とする。
- 中間eventではtail fieldを無効化し、理由を表示する。
- start / end編集でgroup構成が変わった場合、tail fieldの有効状態を再評価する。
- start / end編集で以前のtail eventが中間eventになった場合、そのeventのhold / softness / slope overrideを同一transaction内でcanonical removalする。latent tail overrideは保持せず、Undoでのみ編集前snapshotへ戻せる。
- synthetic shape pointはhit-test候補にせず、対応するreal base event rangeを選択対象とする。

hit-test初期優先順位:

1. cursorが属するvowel laneだけを対象にする。
2. event別frame range内の候補を抽出する。
3. 複数候補ではcursor frameからbase peak frameまでの距離が短いeventを優先する。
4. 同距離では小さい `base_event_index` を優先する。
5. event range外、空lane、viewport外ではselectionを変更しない。

click / drag thresholdのpixel値はB3 Implementation Planでwxのmouse eventとDPIを確認して固定する。B1ではgesture状態がhit-test結果をcommitする条件だけを固定する。

### Step 7: adjustment snapshot / history契約

初期構造:

```text
EventAdjustment
  - base_event_index
  - optional field overrides

AdjustmentLayerSnapshot
  - schema_version
  - base_plan_identity
  - event adjustments: base_event_index昇順
```

- snapshotはUI controlやwx objectを保持しない。
- 同値overrideを削除し、空entryを保持しないcanonicalization規則を固定する。
- history要素はadjustment layer全体のbefore / after snapshotとする。
- selection、tab、pan、zoom、playback位置はhistoryへ含めない。
- reset selected / reset allは1 transactionとする。
- canonical snapshotが変わらないstate no-opはhistoryを増やさずredoを破棄しない。
- hold / softnessのrequested overrideが変わってもcurrent shape clampによりoutputが同値となる場合、UIへrequested値を表示するためsnapshot変更としてhistoryへ記録する。ただしeffective writer payloadが同じならfingerprintは変えない。
- 新規commit後はredo stackを破棄する。
- 最大50操作を超えた場合は最古のundo可能transactionだけを破棄する。

coalescing初期契約:

```text
begin_edit(event, field)
  -> 0回以上のpreview update
  -> commit_edit(event, field)
```

- 同一event・同一field・同一gesture内だけを1操作へ集約する。
- selection変更、focus loss、Enter、mouse release、別field編集、reset、Undo / Redoをtransaction境界とする。
- controlが発生させる重複 `EVT_TEXT` / `EVT_SPINCTRL` を別操作にしない。

### Step 8: lifecycle / rollback契約

ユーザー採用済み判断:

- 解析開始時に旧base、adjustment、historyをrollback候補として一時保持し、編集操作を無効化する。
- 解析開始中は旧selectionとPreviewを表示のみ維持し、RightPane編集、reset、Undo / Redoをlockする。表示をclearしてrollback候補と不一致にしない。
- current job成功時に新baseをcommitし、旧selection、adjustment、Undo / Redoを破棄する。
- current job失敗 / cancel時に旧baseが再利用可能なら、旧adjustmentとhistoryを復元する。
- input変更、output-affecting parameter変更、workspace resetにより旧baseが無効なら破棄する。
- late / duplicate callbackはbase、selection、adjustment、history、Previewを変更しない。

旧base再利用可能条件:

- analysis開始時に `analysis_result_valid=True`のbase plan、base identity、adjustment snapshot、history、selectionをrollback snapshotへ保存できた。
- job開始後にinput commit、TEXT / transcription適用・復元、output-affecting parameter変更、workspace reset、別analysis job開始が発生していない。
- terminal callbackのjob IDがcurrent jobと一致し、rollback snapshotのbase identityが開始時identityと一致する。
- 上記を1つでも満たさなければ復元せず、現行invalidate契約どおりbase、selection、adjustment、historyを破棄する。

現行正本仕様との関係:

- 現行Pipeline / Error仕様のanalysis failure時 `current_timing_plan` 破棄はMS20実装済み契約である。旧base再利用可能時のrollbackは、MS21での意図的な将来契約変更として扱う。
- B1は計画契約だけを固定し、現行codeと正本仕様のimplemented表示は変更しない。B7がPipeline / GUI / Error仕様を実装結果へ同期する。

状態matrix:

| event | base / adjustment / history | selection | 備考 |
| --- | --- | --- | --- |
| input dialog cancel | 保持 | 保持 | workspace不変 |
| input commit | 破棄 | clear | old base無効 |
| global parameter変更 | 破棄 | clear | 現行 `invalidate_analysis()` と整合 |
| analysis開始 | rollback候補として保持、編集lock | 表示のみ保持、編集lock | irreversible clearしない |
| current job成功 | 新baseへ置換、旧編集破棄 | clear | 新base identity |
| current job失敗 | 再利用条件を満たす場合だけ復元、不可なら破棄 | 同じsnapshotから復元 | failure ERRORを保持しVMD保存禁止 |
| current job cancel | 再利用条件を満たす場合だけ復元 | 同じsnapshotから復元 | cancel INFOを追加し、他ERRORがなければ保存可 |
| late / duplicate callback | 変更なし | 変更なし | current job guardより後だけ更新 |
| workspace reset Yes | 破棄 | clear | session外保存なし |
| workspace reset No | 保持 | 保持 | 完全不変 |
| VMD / report dialog cancel | 保持 | 保持 | 出力操作だけ |
| VMD / report保存失敗 | 保持 | 保持 | 再試行可能 |

### Step 9: diagnostics / fingerprint / report引き継ぎ

- effective VMD outputが変わるadjustmentをMS20 save-state fingerprintへ含める。
- base plan identityとeffective save fingerprintを同じ値にしない。
- fingerprint schema versionをMS21で更新する。
- fingerprintはcanonical effective writer inputとeffective per-group tail parameterを含む。
- canonical snapshotが変わらないstate no-opはeffective payloadとfingerprintを変えない。
- snapshotが変わってもeffective writer payloadが同値のoutput-equivalent editはfingerprintを変えない。
- outputが変わるedit後は確認済みWARNING fingerprintを再利用しない。
- analysis failure後に旧baseを復元しても `current_diagnostic_failure` のERRORを保持し、VMD保存を禁止する。Preview・編集再開は許可するが、次のanalysis成功までfailureをclearしない。
- analysis cancel後はcancel INFOを含むcurrent snapshotとfingerprintを再構築する。旧WARNING確認済みfingerprintは復元せず、新fingerprintにWARNINGがあれば再確認する。
- selection、history position、Undo可否、RightPane表示、playback位置はfingerprintへ含めない。
- reportへadjustment summaryを追加する場合のsection / fieldはB5 Implementation Planで固定し、B1では元データをsnapshotから得る責務だけを渡す。
- `ERROR`保存禁止、`WARNING`同一fingerprint一回確認、reportはERROR時も保存可能というMS20契約を維持する。

### Step 10: B2からB7へのhandoff

| Block | B1から渡す契約 |
| --- | --- |
| B2 | base identity、base event key、adjustment DTO、validation、canonical snapshot、automatic shape準備、synthetic token分離、provenance、group-aware shared resolver |
| B3 | B2 provenanceからのevent別hit region、canonical selection commit、overlap優先、click / drag commit条件 |
| B4 | B2 shared resolverを使うfield単位表示、base / override / effective表示、tail / slope有効条件、live Preview |
| B5 | B2 shared resolverを使うeffective writer input、fingerprint schema更新、WARNING確認、report元データ |
| B6 | immutable snapshot、transaction、50操作、coalescing、reset selected / all |
| B7 | reanalysis rollback、input / parameter / reset破棄、Busy lock、late callback、TEXT / voice_only回帰 |

### Step 11: B1実施結果の記録

- 2026-07-21に現行code、test、Pipeline / GUI / Error仕様、Block Breakdown、Index、Roadmapを読み取り照合した。
- `VowelTimingPlan.observations` のoptional契約、writer / Previewのsorting後source index、same-vowel synthetic token、Previewのmulti-point先頭index、analysis failure / cancel、fingerprint、global parameter範囲を確認した。
- pre-implementation checkのP2 2件、P3 1件を本文へ反映し、補正後の残存P1 / P2 / P3はなしと判定した。
- 文書補正後に限定回帰167件を再実行し、すべてpass表示、各process exit code 0を確認した。
- B2のAPIやユーザー挙動を変える未解決選択は残っていない。B2は専用Implementation Plan作成・実装状態照合の段階へ進行可能である。

## 10. 状態遷移 / データ契約

### 10.1 base / adjustment / effectiveの境界

```text
BaseTimingPlanInput
  - canonical base plan identity
  - timeline
  - observations
  - source_duration_frames
  - global writer parameters

AdjustmentLayerSnapshot
  - same base plan identity
  - ordered EventAdjustment entries

          ↓ pure resolver

EffectiveShapePlan
  - effective events
  - observation handoff
  - event / group tail overrides
  - real base event provenance
  - internal shape source tokens
```

- resolverはwxPython、UiState、MainFrameをimportしない。
- resolver moduleは `src.vmd_writer.writer` をimportせず、writer / Preview adapterがcoreの `EffectiveShapePlan` をimportする。
- resolverはdialogを開かず、fileを書かず、baseを変更しない。
- identity mismatch、不正index、非有限値、不正frame順序はfail closedとする。
- empty adjustmentはbaseと同じwriter意味を返す。

### 10.2 field適用の不変条件

- `base_event_index` はbase plan内で一意かつ0以上である。
- observationsなしでもbase event identityは成立する。observations present時は長さ、event index、vowel対応がbase timelineと一致する。
- synthetic `shape_source_token` はcanonical selection / adjustment keyにならない。
- vowelは変更しない。
- effective start frameは0以上である。
- `0 <= start_frame <= peak_frame <= end_frame <= source_duration_frames` を維持する。
- peak valueはfiniteかつ0以上である。
- hold / softness frameは0から100の整数である。
- slope ratioは0.0から1.0である。
- effective softnessがmidpointを生成できない場合、slope overrideは存在しない。
- group末尾でないeventのtail overrideは通常入力として受理しない。
- effective shapeがwriter normalization後も決定的である。

### 10.3 selectionとhistory

- selectionはplan-local event参照でありadjustment内容ではない。
- 既存 `PreviewPanel.set_selected_source_event_index()` はrender-only互換性のため未知indexを一時保持でき、summary `None` を許容する。
- B3のcanonical selection commitはcurrent base identityとindex範囲を検証し、範囲外index、stale index、負数synthetic tokenをUiState / editor selectionへ書き込まない。
- invalid / empty / Busy入力では既存selectionを変更しない。
- selection変更はUndo対象外である。
- adjustment snapshot更新時はcurrent selectionが同じbase identityに属することを検証する。
- Undo / Redo後もselectionが有効なら保持し、eventが存在しない場合だけclearする。

## 11. テスト方針

B1は読み取り監査Blockであり、test codeを変更しない。

### 11.1 読み取り検証

- dataclass、normalization、sorting、grouping、callback、reset、fingerprint入口を `rg` で特定する。
- 必要範囲だけを読む。
- current test fixtureでsource index、group末尾、softness midpoint、cancel / resetの期待値を確認する。
- plan記載のpath、class、methodが現行repositoryに存在するか確認する。

### 11.2 必要時の非変更test実行

最小順:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_preview_transform.py tests/test_vmd_writer_grouping.py tests/test_vmd_writer_multipoint_shape.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b5_warning_save_policy.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms19_b8_workspace_reset.py tests/test_ms17_b8_late_worker_result_discard.py tests/test_wx_ms14_b4_analysis.py -q
```

実行した場合はpass表示、failure / error、fatal、process exit codeを分離して記録する。

### 11.3 B2以降へ渡すtest境界

B1では追加しないが、少なくとも次を後続testへ渡す。

- base collectionをresolverが変更しない。
- same base / same adjustmentからsame effective resultを得る。
- base identity mismatchを拒否する。
- observation event index不一致を拒否する。
- observations `None` を許可しautomatic candidateなしで解決できる。
- observations present時の長さ、event index、vowel不一致と、非空timeline + present empty observationsを拒否する。
- source durationの欠落、NaN / infinity、負値、base endより小さいdurationを拒否する。
- adjustmentなしとcanonical no-op adjustmentが同じwriter意味になる。
- 各fieldの境界、NaN / infinity、範囲外indexを拒否する。
- slope default 0.7が現行shapeと同値である。
- midpointなしではslope編集を拒否し、latent slope overrideを残さない。
- hold / softnessの0、100を受理し、負数と101以上を拒否する。
- automatic candidate変換後も明示したpeak / start / end補正が保持される。
- synthetic置換対象のbase eventを補正すると該当candidate spanを再評価し、real base event identityで編集できる。
- PreviewとVMDが同じprovenance / grouping resultを使用する。
- 既存render-only selection setterの範囲外許容を維持し、canonical commitだけがinvalid / synthetic selectionを拒否する。
- grouped中間eventのtail overrideを拒否する。
- group構成変更後にtail編集可否を再評価する。
- tailでなくなったeventのhold / softness / slope overrideを同一transactionで除去する。
- output変更でfingerprintが変わり、selection / history位置だけでは変わらない。
- analysis failure / cancelのrollbackとsuccess時の旧編集破棄。
- failure rollback後はERRORでVMD保存禁止、cancel rollback後はcancel INFO付きfingerprint再構築とWARNING再確認を行う。
- late callbackがadjustment / historyを変更しない。
- 51操作目で最古historyだけを破棄する。
- no-opとcoalesced editが履歴件数を増やさない。

### 11.4 手動・build確認

- 手動GUI確認: 実施しない
- 実MMD確認: 実施しない
- build / SmokeLaunch: 実施しない
- package / release確認: 実施しない

## 12. 受け入れ条件

- timeline index、observation event index、Preview / writer source indexの対応が記録されている。
- canonical event keyとbase plan identityが分離定義されている。
- base plan identityの入力と除外項目が固定されている。
- observations省略時とpresent時のevent identity / validation契約が分離定義されている。
- 全adjustment fieldの意味、単位、default、validationが固定されている。
- slope ratio 0.0から1.0、default 0.7が記録されている。
- slope midpointがない場合のdisabled / reject / canonical removalが記録されている。
- hold / softnessの0から100、model側reject境界が記録されている。
- opening / start / endとtail fieldのgrouped shape上の編集可能範囲が固定されている。
- automatic candidate、明示補正、candidate再評価、grouping、tailの順序と補正優先が固定されている。
- real base event identityとsynthetic shape tokenが分離され、zero / skipped eventの選択規則が固定されている。
- adjustment snapshotとhistory transaction / coalescing境界が固定されている。
- current job success commit、failure / cancel rollback、late callback無変更が固定されている。
- failure rollbackが現行正本仕様からのMS21将来変更であることと、B7の仕様同期責務が固定されている。
- effective outputとMS20 fingerprint / WARNING / reportの関係が固定されている。
- B2からB7の所有権が明記されている。
- P1 / P2 / P3とB2着手可否が記録されている。
- production code、GUI、test code、dependency、build設定が変更されていない。
- B2開始前に解消すべき未記名の仕様判断が残っていない。
- B1実施後の残存P1 / P2 / P3がなく、B2計画策定へ進行可能である。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| frozen dataclassをdeep immutableと誤認する | base collection非変更をresolver testで固定する |
| sorted shape ordinalをevent keyにする | plan-local timeline indexとbase identityを使用する |
| multi-point先頭indexだけをgroup全体とみなす | real base source indicesとevent別hit regionをprovenanceとして保持する |
| synthetic source tokenを編集identityにする | internal tokenと0以上のbase event indexを分離する |
| 旧base用adjustmentを新baseへ適用する | base identity mismatchをfail closedにする |
| Previewとwriterでadjustment適用順が異なる | B2のgroup-aware shared resolverを唯一のshape準備入口にする |
| automatic candidateがユーザー補正を上書きする | 補正を優先し、影響candidate spanを補正後eventで再評価する |
| grouped中間eventへ存在しないtailを追加する | tail fieldはgroup末尾だけ許可する |
| slopeをsoftnessと同一視する | 位置をsoftness、強度比をslopeとして分離する |
| peak値を存在しないwriter clampへ依存させる | analysis upper limitとwriter validationを別契約にする |
| analysis開始時clearでcancel後に編集を失う | rollback候補を保持しcurrent job結果でcommit / restoreする |
| state no-opとoutput-equivalent editを混同する | snapshot同値性とeffective writer payload同値性を分離する |
| UI event連打で履歴が50件埋まる | begin / update / commitでcoalesceする |
| B1で実装を開始する | diff監査でcode / test変更をscope逸脱とする |

## 14. Codex 実装時の注意

```text
- B1は調査・契約固定だけを行い、production codeとtest codeを変更しない。
- shell commandは一つずつ実行し、parallel、pipeline、chained commandを使わない。
- RoadmapとBlock Breakdownを仮説として現行code / testへ再対応付けする。
- 確認済み事実、初期提案、ユーザー採用判断、未確定を区別する。
- base_event_indexをgroup後segment番号またはsynthetic tokenとして扱わない。
- base VowelTimingPlanとobservationを変更しない。
- Preview cache、RightPane文字列、wx control値をwriter正本にしない。
- slope ratioは0.0から1.0、default 0.7とする。
- midpointなしのslope overrideを保持しない。
- hold / softnessは0から100の整数とし、範囲外をclampせず拒否する。
- grouped shapeのtail fieldは再grouping後の末尾eventだけに許可する。
- analysis開始時に旧編集を不可逆clearせず、current job成功 / failure / cancelを分ける。
- effective outputが変わるadjustmentをsave-state fingerprintから漏らさない。
- MS20のERROR / WARNING / report契約を弱めない。
- TEXTあり / voice_only、Busy、reset、late callback契約を維持する。
- 固定モーフ、Qt禁止、network禁止を維持する。
- 実行していないtestや手動確認を通過と報告しない。
```

B1完了報告は次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 調査・契約固定内容
4. 実行したテスト
5. テスト結果
6. P1 / P2 / P3
7. 仕様からの逸脱
8. 残課題
9. B2着手可否
```
