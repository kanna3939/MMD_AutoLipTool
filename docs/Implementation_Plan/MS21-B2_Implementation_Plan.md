# MS21-B2 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B2 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
- 対象Block: MS21-B2
- Block名: Adjustment Core / Shared Shape Resolver
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `b44f3f8 Complete MS21-B1 adjustment contract`
- 作成日: 2026-07-21
- 文書ステータス: Implemented / Automated Verification Completed / User GUI Regression Check Passed / B3 Planning Ready
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- 関連正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS21-B2は、B1で固定したevent adjustment、base plan identity、shape provenance、group-aware shared resolverをUI非依存coreとして実装するBlockである。B2では既存GUIの編集導線、VMD保存導線、Undo / Redoを有効化しない。

## 2. 背景

現行実装には次の責務境界がある。

- `src/core/pipeline.py` の `VowelTimingPlan.timeline` と `observations` が解析結果を保持する。
- `VowelTimelinePoint` は `src/vmd_writer/writer.py` にあり、生成時にstart / peak / endを秒単位で正規化する。
- `write_morph_vmd()` はtimelineを正規化・sortした後、observation candidate変換、same-vowel grouping、single / multi-point shape生成、tail処理、final normalization、binary出力を行う。
- `src/core/preview_transform.py` はwriterと同じshapeを表示するため、writer moduleから多数のprivate helperを直接importしている。
- writerのsame-vowel candidate変換では、real base eventをskipし、負数のsynthetic source indexを持つpointへ置換する場合がある。
- `PreviewSegment.source_event_index` はmulti-source shapeの先頭indexだけを公開し、完全なprovenanceを保持しない。
- `VmdWriterParameters` とMS20 save-state fingerprintは存在するが、adjustment snapshotやeffective shape payloadはまだ存在しない。
- `selected_wav_analysis.duration_sec` はGUI stateに存在するが、現行 `VowelTimingPlan` 自体にはsource durationが含まれない。

B1は次を契約として固定した。

- canonical `base_event_index` はnormalization / filter / sortより前のbase timeline ordinalである。
- observationsなしを許可し、present時はtimelineとのlength / event index / vowel対応をfail closedで検証する。
- canonical編集単位は30fps整数frameであり、real eventのstart / peak / endはsource duration frameを上限にする。
- base plan identity、adjustment snapshot、effective resultを分離する。
- automatic candidateよりユーザー補正を優先し、影響spanを再評価する。
- hold / softness / slopeは再grouping後のgroup末尾real eventだけに適用する。
- Previewとwriterはwriter非依存coreの同じ `EffectiveShapePlan` を消費する。
- base identityのcanonical payloadをB2 coreで所有し、MS20 diagnosticsのprivate canonicalizationをimportしない。

B2では、この契約を既存writerのprivate implementationへ単純に追加してはならない。coreからwriterをimportすると、現在の `pipeline -> vmd_writer` 依存と将来の `vmd_writer -> core resolver` 依存が循環するためである。

## 3. 目的

- immutableなevent adjustment modelとcanonical snapshotを追加する。
- base timing planのcanonical identityを決定的に生成する。
- base input、observations、source duration、adjustmentをfail closedで検証する。
- source duration秒値からcanonical frameへの変換を単一pure helperへ集約する。
- user adjustmentを反映したeffective event列をbaseとは別に生成する。
- automatic candidate、synthetic token、real base provenanceを分離する。
- nearby grouping、group末尾tail、shape control point生成をUI・writer非依存coreへ集約する。
- Previewとwriterが同じ `EffectiveShapePlan` を変換できるadapter境界を追加する。
- adjustmentなしの既存Preview / VMD出力意味を維持する。
- B3からB6が再発明せず使用できるpure APIとtest fixtureを確立する。

## 4. In Scope

- `EventAdjustment` immutable DTO
- `AdjustmentLayerSnapshot` immutable canonical DTO
- `BasePlanIdentity` と明示的canonical payload
- base event、observation、source duration、writer shape parameter validation
- peak / start / end adjustment
- hold / softness / slope adjustment
- canonical no-op除去
- base identity mismatch、stale index、不正値のreject
- base event frame化とreal base provenance
- observationsなしのresolver経路
- observations present時の対応検証
- observation candidate handoffの有効 / 無効範囲
- automatic cross-vowel / same-vowel candidate準備
- adjustmentが交差するcandidate spanのdeterministicな再評価
- negative synthetic `shape_source_token`
- nearby same-vowel grouping
- group末尾tail validation / canonical removal
- single / multi-point / fallback shape control point生成
- shape normalization metadataのcore DTO化
- writer / Preview向けpure adapter
- 現行public APIと既存private-helper test入口の互換維持
- B2専用core testと既存Preview / writer回帰

## 5. Out of Scope

- Preview mouse hit-test、click選択、drag threshold
- canonical selection commit
- RightPane編集control、入力dialog、即時GUI反映
- UiStateへのadjustment / rollback snapshot追加
- Undo / Redo stack、history上限、coalescing実装
- 現行GUI Preview導線をadjustment付きresolverへ切り替えること
- 現行VMD保存導線をadjustment付きresolverへ切り替えること
- save-state fingerprint schema更新
- diagnostic reportへのadjustment summary追加
- analysis failure / cancel rollbackのGUI state実装
- README、配布用readme、Pipeline / GUI / Error正本仕様のimplemented更新
- VMD file format、model name、Shift_JIS encoding変更
- final morph normalization policyの機能変更
- 固定モーフ `あ / い / う / え / お` の変更
- dependency追加、package、release、version bump、tag、merge、push
- Qt / PySide6、network、cloud ASR、他ASR backend、外部送信、background通信、Whisper自動download

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- B1完了commit `b44f3f8` を契約baselineとする。
- 作業開始時に未コミット変更を再確認し、既存変更をユーザー所有として保護する。
- Python 3.11以上、wxPython主系、30fps writer契約を維持する。
- production実装前に本planを現行code / testへ再照合する。
- B2でsource durationを推測してadjustmentを許可しない。full resolverのcallerは `source_duration_frames` を明示する。
- 現行GUI / pipelineはB4 / B5までadjustment snapshotを持たないため、B2のfull resolverを既存保存導線へ接続しない。

### 6.1 現行依存関係

```text
pipeline -> vmd_writer
output_diagnostics -> pipeline + vmd_writer
preview_transform -> vmd_writer public type + private shape helpers
```

B2後の目標:

```text
event_adjustment <- effective_shape_plan
                         ^       |
                         |       v
              preview_transform  vmd_writer/effective_shape_adapter -> writer

pipeline / output_diagnostics はB2では既存入口を維持
```

- `event_adjustment.py` と `effective_shape_plan.py` は `src.vmd_writer`、wxPython、`output_diagnostics` をimportしない。
- `effective_shape_plan.py` はmodule内で `TimelinePointLike` / `ObservationLike` Protocolとown input DTOを定義し、pipeline concrete dataclassをimportしない。
- writer / Previewがcore resultをconsumeする一方向依存にする。
- `writer.py` はmodule初期化中に `src.core` をimportしない。legacy wrapperからの委譲は、`src.vmd_writer` packageと `writer.py` の初期化完了後にfunction-local importする `src/vmd_writer/effective_shape_adapter.py` を経由する。
- 新規B2 public APIの正本は `src.core.*` とする。一方、現行testが使用するtop-level `vmd_writer.writer` private helper互換はB2中も維持する。wrapperは自身のpackageに対するrelative importでsibling adapterを解決し、`src.*` とtop-level namespaceで別々にloadされたclassのobject identityへ依存しない。

### 6.2 計画作成baseline

2026-07-21、HEAD `b44f3f8` で次を実行した。

- Preview / grouping / multi-point: 52件pass表示、process exit code 0
- writer interval / peak / pipeline: 49件pass表示、process exit code 0
- MS20 output diagnostics: 12件pass表示、process exit code 0
- writer final normalization / zero guard: 39件pass表示、process exit code 0
- 合計152件、failure / error / fatal表示なし

B1完了後のcommit差分は文書4件だけであり、B1検証時からproduction codeとtest codeは変更されていない。

### 6.3 Pre-implementation review修正記録

2026-07-21の現行code / test照合ではP1なし、P2 4件、P3 1件を検出し、本planと関連routing文書で解消した。

- P2: `writer.py` からcoreをmodule-level direct importすると、`src/core/__init__.py -> pipeline -> src.vmd_writer -> writer` と循環する。writer初期化後にだけcoreへ委譲する専用adapterとfresh-process import smokeへ変更した。
- P2: legacy writerのhold / softnessは0から100へnormalizeしておらず、非負整数として100超も受理する。MS21 adjustment / `ShapeParameters` の0から100 reject契約と、legacy入口の100超互換を分離した。
- P2: 現行tail control pointは最終shapeでsource durationを超過でき、次shapeがある場合だけclampされる。source duration上限をreal event intervalへ限定し、tailは現行writer semanticsを維持する契約へ修正した。
- P2: shape定数の移動・互換所有権が未定義だった。shape内部定数はcoreへ移し、外部共有名はwriter互換mirrorとして値を維持し、drift-guard testで固定する。
- P3: 読み取り専用の `src/core/__init__.py` を主変更対象から読み取り確認対象へ移した。

動的確認ではlegacy normalizerが101 / 250をそのまま受理し、最終eventのtail計算例はreal end 10に対してhold 3、softness 2で `(12, 14, 15)` となった。いずれもprocess exit code 0だった。production code、GUI、test codeは変更していない。

### 6.4 2026-07-22 pre-implementation check修正記録

2026-07-22の再照合ではP1なし、P2 2件、P3 1件を検出し、本planと関連routing文書で解消した。

- P2: repositoryでは `src.vmd_writer.writer` とtop-level `vmd_writer.writer` が別module / classとしてloadされ、既存testは両namespaceを同一processで混在使用する。新規public APIを `src.core.*` に維持しつつ、legacy top-level writer helperはpackage-relative adapterとstructural inputで互換を保ち、mixed importをfresh-process testへ追加した。
- P2: candidate observationの `previous_non_zero_event_index`、`next_non_zero_event_index`、`span_start_index`、`span_end_index` が範囲外でもlookup前に検証されず、現行helperでは `IndexError` になり得る。B2 resolverは全参照を型・範囲・span順序・bracketing順序まで先に検証し、`AdjustmentContractError` へ統一する。
- P3: 回帰対象一覧にある `tests/test_wx_ms16_b6_event_selection_foundation.py` を実行コマンドへ追加した。

修正前診断では両writer moduleと `VowelTimelinePoint` のidentity比較がそれぞれ `False`、process exit code 0だった。範囲外observation参照は `IndexError`、process exit code 1を再現した。production code、GUI、test code、dependency、build設定は変更していない。

補正後の再チェックでは残存P1 / P2 / P3なしと判定した。関連回帰は52件、76件、24件、4件の計156件がすべてpassし、4コマンドともprocess exit code 0だった。fresh processの `src.*` importとtop-level importも各process exit code 0であり、両writer moduleと `VowelTimelinePoint` が別objectとなる現行事実を再確認した。`git diff --check` もprocess exit code 0である。B2 production実装は未着手だが、本planは実装着手可能である。

### 6.5 2026-07-22 implementation結果

- `event_adjustment.py` にimmutable adjustment DTO、base identity、snapshot schema、strict validation、canonical no-op除去を実装した。
- `effective_shape_plan.py` にsource duration変換、base / observation validation、canonical identity、adjustment適用、candidate handoff、real / synthetic provenance、group-aware shape、tail override、update transactionを実装した。
- Preview / writerへ同じ `EffectiveShapePlan` を渡すpure adapterを追加した。既存 `build_preview_data()` の出力互換は `legacy_shape_compat.py` に隔離し、writer private helperの直接importを `preview_transform.py` から除去した。互換facadeはB4 / B5接続前のlegacy caller保護のため残す。
- `src.*` とtop-level writerの別class identityへ依存しないstructural adapter、およびwriterからのfunction-local package-relative delegationを追加した。
- B2専用35件と指定回帰156件はすべてpass表示、各process exit code 0だった。全体は511件と7 subtestsがpass表示、failure / error表示なしだが、既知wx終了処理系と同じprocess exit code 1だった。`compileall` はprocess exit code 0である。
- 2026-07-22にユーザーから、既存GUIの起動、解析、Preview、再生・viewport操作、VMD保存等を対象としたB2回帰確認は通過し、問題なしと報告された。B2で未接続のevent選択・個別補正・RightPane編集・Undo / Redoを確認済みとは扱わない。
- GUI adjustment導線、VMD保存導線、UiState、history、fingerprintは計画どおり未接続である。次はMS21-B3 Implementation Plan策定である。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/core/event_adjustment.py` | adjustment DTO、base identity、snapshot canonicalization、static validation |
| 新規 `src/core/effective_shape_plan.py` | base input DTO、effective event / provenance / shape DTO、candidate・grouping・tail・shape resolver |
| `src/core/preview_transform.py` | writer private importを除去し、core shape planから `PreviewData` を作るadapterを追加 |
| `src/vmd_writer/writer.py` | shape preparationをcoreへ委譲し、effective planからmorph frameを作るadapterを追加 |
| 新規 `src/vmd_writer/effective_shape_adapter.py` | writer package初期化後にcore effective planとwriter morph変換を接続する遅延委譲境界 |

### 7.2 新規test

- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_shape_adapters.py`

### 7.3 回帰確認対象

- `tests/test_preview_transform.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_peak_value.py`
- `tests/test_vmd_writer_zero_guard.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_wx_ms16_b6_event_selection_foundation.py`

### 7.4 読み取り確認対象

- `src/core/pipeline.py`
- `src/core/__init__.py`
- `src/core/output_diagnostics.py`
- `src/vmd_writer/__init__.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`

### 7.5 文書更新

- 本planへ実装結果、変更file、test結果、findingsを追記する。
- Block Breakdown、Index、RoadmapはB2完了状態と次工程B3 plan策定へ同期する。
- README、配布用readme、3正本仕様はB7までimplemented状態へ更新しない。

## 8. 実装方針

### 8.1 二層構造

shape coreを次の二層に分ける。

1. `resolve_effective_shape_plan()`
   - B1契約どおりsource duration、base identity、adjustmentを厳密検証する。
   - B3以降が使用するMS21正規入口である。
2. legacy-compatible shape preparation
   - adjustmentなしの既存Preview / writerから使用する。
   - 既存callerのsignatureと出力意味を維持しつつ、candidate / grouping / shape生成の重複をcoreへ集約する。
   - full resolverのsource duration必須契約を緩和する入口として使用してはならない。

これにより、B2時点で既存GUI / VMD保存をMS21 stateへ接続せず、shape semanticsだけをshared coreへ移せる。

### 8.2 互換性

- `write_morph_vmd()`、`build_preview_data()`、`VowelTimelinePoint` の既存signatureと意味を維持する。
- 現行testが参照するwriter private helperは、B2中に一度で削除しない。core functionへの薄いdelegation wrapperまたはaliasとして残し、既存回帰を維持する。
- 新しいMS21 codeとtestはwriter private helperをimportせず、core public APIだけを使用する。
- `PreviewSegment.source_event_index` は互換fieldとして残すが、canonical identityには使用しない。
- full provenance用に `source_event_indices` と `event_ranges` を追加する場合、immutable tuple、既定空tupleとし、既存constructionを壊さない。

### 8.3 fail closed

- 不正base input、identity mismatch、stale index、不正field、non-finite、bool-as-int、範囲外値はclampや無視をせず例外にする。
- 例外はUI文言を持たないcore exceptionとし、B4 / B5 adapterがユーザー表示へ変換する。
- MS21 adjustment modelと `ShapeParameters` はhold / softnessの0から100以外を拒否する。
- 既存legacy `write_morph_vmd()` / `build_preview_data()` とwriter private normalizerは、現行どおり非負値を受理し、100超、`int()` coercion、boolの扱いをB2で変更しない。legacy互換pathへMS21の上限を遡及適用しない。

### 8.4 immutable / deterministic

- input list、observation、adjustmentを変更しない。
- public collectionはtupleへcopyする。
- orderingは明示keyで固定し、set / dict iteration順を出力identityへ使用しない。
- hash前canonical payloadは単体test可能にする。
- raw `repr()`、object identity、path、UI文字列をidentityへ含めない。

## 9. 詳細ステップ

### Step 1: adjustment error / schema / DTO追加

`src/core/event_adjustment.py` に少なくとも次を追加する。

```text
AdjustmentContractError(ValueError)

BasePlanIdentity
  - schema_version
  - canonical_payload
  - digest

EventAdjustment
  - base_event_index
  - peak_value: float | None
  - start_offset_frames: int
  - end_offset_frames: int
  - hold_frames: int | None
  - softness_frames: int | None
  - slope_ratio: float | None

AdjustmentLayerSnapshot
  - schema_version
  - base_plan_identity
  - adjustments: tuple[EventAdjustment, ...]
```

- schema versionはB2内で固定文字列とし、B5 fingerprint schemaとは分離する。
- `base_event_index` は0以上のintとし、boolを拒否する。
- offsetsはint、peak / slopeはfinite float、hold / softnessはintとして検証する。
- hold / softnessは `0 <= value <= 100`、slopeは `0.0 <= value <= 1.0` とする。
- dataclass frozenだけに依存せず、nested collectionをtuple copyする。

### Step 2: base inputとidentity canonicalization

`src/core/effective_shape_plan.py` に `TimelinePointLike` / `ObservationLike` Protocol、`ShapeParameters`、次のboundaryを定義する。

```text
BaseTimingPlanInput
  - timeline
  - observations: none / present
  - source_duration_frames
  - ShapeParameters

ShapeParameters
  - closing_hold_frames
  - closing_softness_frames
```

source duration変換は次の単一helperを使用する。

```text
source_duration_frames_from_seconds(duration_sec)
  -> int(round(duration_sec * 30))
```

- `None`、bool、non-numeric、NaN / infinity、負値を拒否する。
- callerが独自に秒からframeへ変換しないよう、B3以降のpublic入口としてtestで固定する。
- `BaseTimingPlanInput` はこのhelperで得た0以上のintだけを受ける。

canonical payloadは固定順で次を含む。

- identity schema version
- base timeline ordinalごとのvowel、time / start / end / duration / peak value
- observations state `none` または `present`
- present時のobservation fieldsとRMS tuple
- `source_duration_frames`

global hold / softnessはeffective resultとcanonical no-op判定へ影響するresolver inputだが、B1で固定した `BasePlanIdentity` の構成要素には含めない。parameter変更時のbase / adjustment破棄はB7 lifecycle責務、effective output identityとの統合はB5責務とする。

規則:

- floatはfinite確認後、`float.hex()`相当の決定的文字列表現へ変換する。
- `output_diagnostics._canonicalize()` はprivateなのでimportしない。
- payloadからSHA-256 digestを生成するが、testはdigestだけでなくpayloadも比較する。
- observations present時は `len(observations) == len(timeline)`、各 `event_index == base_event_index`、vowel一致を必須とする。
- observationの `previous_non_zero_event_index`、`next_non_zero_event_index`、`span_start_index`、`span_end_index` は、`None` またはboolではないintとし、値がある場合は `0 <= value < len(timeline)` を必須とする。
- candidate判定でspan端が `None` の場合は現行意味どおり当該 `event_index` へ正規化する。正規化後は `span_start_index <= event_index <= span_end_index` を必須とし、bracketing eventを必要とするcandidateでは `previous_non_zero_event_index < span_start_index <= span_end_index < next_non_zero_event_index` を必須とする。
- candidate参照の型・範囲・順序を、point / observationの配列lookupより前に検証する。不正参照をPythonのnegative index、`IndexError`、silent skipへ委ねない。
- timeline非空でpresent empty observationsは拒否する。timeline空 / present emptyは許可する。
- observationsなしは許可し、candidate処理を無効化する。
- source durationはboolではない0以上のintを必須とする。

### Step 3: base event frame化

base timeline順にcanonical `base_event_index` を付与し、次を生成する。

```text
BaseShapeEvent
  - base_event_index
  - vowel
  - original seconds
  - start_frame
  - peak_frame
  - end_frame
  - peak_value
```

- frameは各秒値から `int(round(seconds * 30))` で一度だけ求める。
- `0 <= start <= peak <= end <= source_duration_frames` を必須とする。
- unsupported vowel、non-finite秒、non-finite peak、負peakを拒否する。
- ordinal付与後にshape処理用orderingを `(peak_frame, base_event_index)` で決定する。
- base identityとadjustment keyはsort後indexへ置換しない。
- adjustmentなしのlegacy互換では元秒値を保持し、既存sub-frame入力のwriter結果を不要に変えない。

### Step 4: adjustment snapshot canonicalization

pure functionでrequested adjustment列をcanonical snapshotへ変換する。

- index昇順へsortする。
- duplicate indexを拒否する。
- base identity mismatchを拒否する。
- 存在しないindexを拒否する。
- peakがbase peakと同値なら `None` にする。
- start / end offset 0は保持しない。
- hold / softnessがcurrent global値と同値なら `None` にする。
- active slope 0.7はdefaultと同値なので保持しない。
- 全fieldがdefault / `None` になったentryは削除する。
- canonical no-opはempty snapshotと等価にする。

canonicalizationで不正値をclampしない。

### Step 5: event adjustment適用

各real base eventへ次の順で適用する。

1. peak absolute override
2. start frame offset
3. end frame offset
4. frame ordering validation

- vowelは変更しない。
- peak overrideはanalysis `morph_upper_limit`でclampしない。
- output eventは新しいimmutable DTOとし、base eventを変更しない。
- `0 <= start <= peak <= end <= source duration` を崩すadjustmentは拒否する。
- 隣接eventとのoverlapはこの段階でclampせず、deterministic grouping / tail処理へ渡す。

### Step 6: observation handoffとcandidate再評価

observationをcandidate判定とRMS shape補助へ分離して扱う。

- observationsなしではautomatic candidate変換を実施しない。
- adjustmentのないspanは現行candidate意味を維持する。
- peak / start / end adjustment対象がsynthetic置換されるspan memberなら、そのspanのsynthetic置換を無効化し、adjusted real eventを残してgroupingを再評価する。
- start / end adjustmentがcross-vowel boundary shift対象eventと交差する場合は、そのcandidate shiftを無効化してadjusted real boundaryを正本にする。
- candidate span外のbracketing eventにpeak adjustmentだけがある場合は、adjusted peakをcontinuity計算へ使用できるが、explicit peak自体を置換しない。
- start / end変更eventでは旧interval由来のobservation shape補助を使用しない。
- peakだけの変更ではRMS decay補助を維持するが、explicit peakを起点にpeak-end値を計算し、observationが明示peakを上書きしない。
- tail fieldだけの変更はcandidate判定を無効化しない。

candidateから作る内部pointには、real event indexとは別に負数tokenを決定的に付与する。

```text
ShapeSourceProvenance
  - real_base_event_indices
  - shape_source_token: negative int | None
  - event_ranges
```

- negative tokenは-1からshape preparation順に減少させる。
- tokenはselection、adjustment key、history keyへ公開しない。
- synthetic shapeにも対応するreal event rangeを保持する。

### Step 7: groupingとtail canonicalization

- nearby same-vowel groupingをcoreへ移す。
- group memberはreal provenanceを失わない。
- group末尾real eventを決定した後、hold / softness / slopeを適用する。
- middle eventへ新規tail overrideを要求した場合は拒否する。
- start / end更新で以前のtail eventがmiddleになった場合は、同じupdate transactionでそのeventのhold / softness / slopeをcanonical snapshotから削除する。
- tail removal結果をcallerへ返し、B4表示とB6 historyが同じafter snapshotを使用できるようにする。
- effective softnessがmidpointを作れない状態への新規slope overrideは拒否する。以前有効だった既存slopeがgroup / clamp変更で作用不能になった場合だけcanonical removalする。
- hold、softness、slopeの作用順は現行shape生成順を維持し、slope defaultは0.7とする。

このため、単なるresolverと編集updateを分ける。

```text
resolve_effective_shape_plan(base_input, canonical_snapshot)
  -> invalid snapshotはreject

apply_adjustment_update(base_input, current_snapshot, requested_change)
  -> canonical after snapshot
  -> removed tail override metadata
  -> EffectiveShapePlan
```

### Step 8: EffectiveShapePlan DTO

少なくとも次の意味を保持する。

```text
EffectiveShapePlan
  - base_plan_identity
  - canonical_adjustment_snapshot
  - effective_events
  - shapes
  - observation_handoffs
  - normalization_contract

EffectiveShape
  - vowel
  - shape_kind
  - ordered control_points
  - real_base_event_indices
  - internal shape_source_tokens
  - event_ranges
  - fallback_reason
  - protection metadata
```

- control pointはframe、value、kindを持つimmutable DTOとする。
- single-point fallback、asymmetric trapezoid、multi-point envelopeを同じtop-level collectionで表現する。
- Previewが再groupingやtail計算を行わず表示へ変換できる情報を含める。
- writerがcandidate / grouping / tailを再実行せずmorph framesへ変換できる情報を含める。
- binary encoding、model name、output pathは含めない。
- selection、GUI tab、viewport、history positionは含めない。

### Step 9: existing shape helperのcore抽出

現行writerから次の責務をcoreへ抽出する。

- event bounds / frame conversionのshape用途
- cross-vowel candidate boundary処理
- same-vowel candidate spanとsynthetic point処理
- nearby same-vowel grouping
- single / multi-point shape specification
- group末尾hold / softness / slope
- Previewとwriterが共有すべきcontrol point / provenance生成

writerに残す責務:

- legacy timeline tupleのpublic入力normalize
- core `EffectiveShapePlan` からMorphFrameへの変換
- final morph frame normalization
- maximum frame count検査
- VMD binary encoding / file I/O
- 既存public `VMD_FPS`、`SUPPORTED_MORPHS` と互換参照される `MORPH_FRAME_OPEN_EPSILON` の名前・値

Previewに残す責務:

- core control pointを秒表示へ変換
- fixed five rowsへの配置
- `PreviewSegment` / `PreviewData` construction
- 表示用intensity range

private compatibility wrapperには新しいbusiness ruleを追加しない。

shape内部のcandidate / grouping / continuity / bridge比率など、抽出algorithmだけが使用する定数は `effective_shape_plan.py` へ移す。`VMD_FPS=30`、固定 `SUPPORTED_MORPHS`、`MORPH_FRAME_OPEN_EPSILON` は既存caller互換のためwriter側の公開名を維持する。writer初期化中のcore importを避けるため、この3値だけはcore側にも明示的なcompatibility mirrorを置き、値の一致をdrift-guard testで固定する。抽出済みbusiness rule定数をwriter側のactive logicとして二重所有しない。

### Step 10: Preview adapter

pure adapterを追加する。

```text
build_preview_data_from_effective_shape_plan(effective_plan)
  -> PreviewData
```

- full provenanceを `PreviewSegment.source_event_indices` と `event_ranges` へ渡す。
- legacy `source_event_index` は最初のreal base indexまたは `None` とするが、canonical identityにしない。
- synthetic tokenをlegacy source_event_indexへ設定しない。
- existing `build_preview_data()` は互換pathとしてshared core shape preparationを使用し、signatureを維持する。
- viewport、selection、wx objectをimportしない。

### Step 11: writer adapter

`src/vmd_writer/effective_shape_adapter.py` に、file I/Oと分離したpure adapterを追加する。

```text
build_morph_frames_from_effective_shape_plan(
    effective_plan,
    apply_final_normalization=True,
) -> tuple[MorphFrame, ...]
```

- writerはeffective planを受けた後にcandidate / grouping / tailを再計算しない。
- final normalizationは現行policyを維持する。
- `write_morph_vmd()` のlegacy signatureと結果を維持する。
- writerのlegacy compatibility wrapperはfunction-localかつpackage-relative importでsibling adapterへ委譲し、`writer.py` のmodule-levelでは `src.core` をimportしない。
- adapter / compatibility wrapperはProtocol、属性、primitive tupleで境界を構成し、`src.vmd_writer.writer` とtop-level `vmd_writer.writer` のclass identity一致を前提にしない。
- B5が保存導線を接続するまで、現在のpipeline callへadjustment引数を追加しない。
- 新adapterはfileを作成せず、B2 core testから直接比較可能にする。

### Step 12: public exportとfresh-process import cycle検査

- B2 public APIは `src.core.event_adjustment` / `src.core.effective_shape_plan` の明示module pathを正本とし、`src/core/__init__.py` へexportを追加しない。top-level `core.*` をB2の新規public APIとして追加しない。ただしPythonがsubmodule import前にpackage `__init__.py` を実行する事実を、循環回避策として扱わない。
- `src/vmd_writer` と `writer.py` の初期化完了後に `src/vmd_writer/effective_shape_adapter.py` がcore submoduleをimportする順序を固定する。
- `src/vmd_writer/__init__.py` の既存exportを壊さず、初期化時にcoreを読むadapter exportを追加しない。adapterは初期化完了後に明示module pathからimportする。
- `preview_transform.py` からwriter private helper importを除去する。
- fresh processごとに、`src.vmd_writer`、adapter、`src.core.effective_shape_plan`、legacy writer callの順序を個別に変えたimport smokeをtestで固定する。
- top-level `vmd_writer.writer` helper単独、`src.vmd_writer` DTOとのmixed import、両writer moduleが同一processで別objectとなる場合のlegacy callもfresh-process testへ含める。互換判定ではclass identity一致を要求せず、出力tupleと例外契約を比較する。

### Step 13: documentation closeout

実装後に次を記録する。

- 実際に追加・変更したfile
- coreへ移した責務とwriterに残した責務
- compatibility wrapperの残存理由
- 実行testとpass表示 / process exit code
- P1 / P2 / P3
- B3 Implementation Plan策定可否

## 10. 状態遷移 / データ契約

### 10.1 resolver flow

```text
base timeline + observations + source duration + global shape parameters
  -> validate / canonical BasePlanIdentity
  -> assign base_event_index before sorting
  -> canonical AdjustmentLayerSnapshot
  -> apply peak / start / end to real base events
  -> candidate handoff validation
  -> disable / re-evaluate affected candidate spans
  -> effective event + provenance sequence
  -> deterministic nearby grouping
  -> validate / canonicalize tail overrides
  -> shared control point / normalization contract generation
  -> EffectiveShapePlan
       -> Preview adapter
       -> writer MorphFrame adapter
```

### 10.2 canonical equality

- same base payload + same canonical adjustment + same global parametersからsame effective planを得る。
- input collection objectが違ってもcanonical payloadが同じならbase identityは同じである。
- `None` observationsとpresent empty observationsは異なる。
- defaultと同値のoverrideはcanonical snapshotへ残さない。
- selection、Undo位置、Preview cache、path、model nameはbase adjustment identityへ含めない。
- output-equivalent adjustmentとfingerprintの統合はB5で行う。B2はcanonical effective payloadを提供するだけである。

### 10.3 invalid input

次は `AdjustmentContractError` とする。legacy writer / Preview compatibility入口は既存 `ValueError` 契約を維持する。

- non-finite timeline / peak / adjustment
- unsupported vowel
- invalid frame ordering
- source duration欠落 / bool / 負値 / base end未満
- observation length / event index / vowel不一致
- observation candidate参照indexのbool / 負値 / 範囲外 / span逆転 / bracketing順序不正
- duplicate / negative / out-of-range adjustment key
- base identity mismatch
- hold / softness範囲外
- slope範囲外
- group middleへのtail override
- midpointを持てないshapeへのslope override

### 10.4 base不変条件

- resolver前後でbase timeline / observationsの要素と順序が変わらない。
- `VowelTimingPlan` をeffective outputとして再利用しない。
- real base event identityは負数にならない。
- synthetic tokenはreal identity collectionへ混入しない。
- real / effective event intervalは `0 <= start_frame <= peak_frame <= end_frame <= source_duration_frames` を満たす。
- tail control pointは現行writer semanticsどおり最終shapeでsource durationを超過できる。次shapeがある場合だけ、その開始frameに対する既存clampを維持する。event別tail overrideも同じ規則に従う。

## 11. テスト方針

### 11.1 B2 adjustment model test

`tests/test_ms21_b2_event_adjustment.py` で少なくとも次を固定する。

- DTO collectionのtuple copy / immutable性
- base identity payload / digest安定性
- object identity、path、selectionをidentityへ含めない
- float canonicalizationとnon-finite拒否
- index昇順canonicalization
- duplicate / negative / stale index拒否
- peak / offset / hold / softness / slope境界
- bool-as-int拒否
- default同値overrideとempty entry除去
- base identity mismatch拒否
- base input非変更

### 11.2 B2 effective resolver test

`tests/test_ms21_b2_effective_shape_plan.py` で少なくとも次を固定する。

- observations `None` の解決
- empty timeline + present empty observations
- non-empty timeline + present empty observations拒否
- observation length / event index / vowel不一致拒否
- candidate参照indexのbool / 負値 / `len(timeline)` 以上拒否
- `span_start <= event_index <= span_end` と `previous < span_start <= span_end < next` の検証
- 不正candidate参照がlookup前に `AdjustmentContractError` となり、negative index / `IndexError` / silent skipへ流れないこと
- source duration欠落 / 非整数 / 負値 / base end未満拒否
- source duration秒値のNone / bool / NaN / infinity / 負値拒否と30fps round結果
- frame境界 `0 <= start <= peak <= end <= duration`
- empty adjustmentとbase-only shapeの同値性
- same inputからsame output
- peak / start / endの適用
- analysis upper limitをpeak adjustmentへ適用しない
- unaffected candidate spanの既存意味維持
- adjusted candidate spanがreal event identityへfallbackする
- negative synthetic tokenとreal provenance分離
- multi-source groupのfull provenance
- group middle tail override拒否
- tailでなくなったeventのoverride removal
- midpointなしslope拒否 / removal
- hold / softness 0、100とslope 0.0、1.0
- MS21 adjustment / `ShapeParameters` のhold / softness 101拒否
- legacy writer / Previewのhold / softness 101、250受理互換
- 最終shape tailのsource duration超過許容と、次shapeがある場合の既存clamp
- base collection非変更

### 11.3 adapter test

- same `EffectiveShapePlan` からPreviewとwriterが同じshape kind、control point frame、provenanceを得る。
- Preview legacy `source_event_index` がnegative tokenにならない。
- writer adapterはcandidate / groupingを再実行しない。
- final normalization on / offの既存意味を維持する。
- import時にwxPythonを要求しない。
- fresh processで `src.vmd_writer`、adapter、core moduleを異なる順序でimportし、legacy writer callまで循環を起こさない。
- fresh processでtop-level `vmd_writer.writer` helperと `src.vmd_writer` DTOのmixed importを実行し、class identity一致に依存せずlegacy出力を維持する。
- writer / coreの `VMD_FPS`、`SUPPORTED_MORPHS`、`MORPH_FRAME_OPEN_EPSILON` compatibility mirrorが一致する。

### 11.4 既存回帰

最小順に実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_event_adjustment.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_effective_shape_plan.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_shape_adapters.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_preview_transform.py tests/test_vmd_writer_grouping.py tests/test_vmd_writer_multipoint_shape.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_vmd_writer_intervals.py tests/test_vmd_writer_peak_value.py tests/test_vmd_writer_zero_guard.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py tests/test_ms20_b2_output_diagnostics.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py -q
```

3件の新規test fileを作成し、各fileを単独実行してから関連回帰へ進む。実行コマンドを実装結果へ記録する。

### 11.5 広範囲回帰

B2限定・関連回帰が成功した後、次を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

- pass表示とprocess exit codeを分けて報告する。
- 既知wx終了処理を理由に、新しいfailure / errorを無視しない。

### 11.6 手動 / build確認

- 手動GUI確認: B2では必須条件にしない。GUI導線を変更しないため。ただし2026-07-22に既存GUI回帰確認を実施し、ユーザーから通過・問題なしと報告された
- 実MMD確認: B2では実施しない
- build / SmokeLaunch: dependency / package変更がない限り実施しない
- B4 / B5統合前にadjustment付きGUI出力を実装済みと扱わない

## 12. 受け入れ条件

- B1で固定したadjustment field、単位、default、validationがcore DTOへ実装されている。
- base plan identityのcanonical payloadとdigestが決定的である。
- observationsなしを許可し、present不整合をfail closedで拒否する。
- source durationに対するreal / effective event interval上限が検証される一方、最終tailのduration超過と次shape clampは既存意味を維持する。
- base timeline / observationsを変更しない。
- canonical no-opがempty adjustmentと同値である。
- real base event indexとnegative synthetic tokenが分離されている。
- adjusted candidate spanでユーザー補正がautomatic変換に失われない。
- multi-source groupの全real provenanceとevent rangeを保持する。
- middle eventのtail overrideを拒否し、group変更でstale tail overrideをcanonical removalできる。
- default 0.7を含むslope契約がshapeへ反映される。
- Preview / writer adapterが同じeffective planを消費する。
- `preview_transform.py` がwriter private shape helperへ依存しない。
- core resolverがwriter、wxPython、diagnostics private helperをimportしない。
- writer module-level importがcoreを参照せず、fresh-process import順序とlegacy callで循環がない。
- top-level writer helperと `src.vmd_writer` DTOのmixed import互換を維持し、別namespaceのclass identityへ依存しない。
- observation candidate参照indexをlookup前に検証し、不正参照を `AdjustmentContractError` で拒否する。
- MS21 adjustment / `ShapeParameters` はhold / softnessを0から100へ制限し、legacy writer / Previewの100超受理を維持する。
- shared固定定数のwriter互換名・値とcore mirrorがdrift-guard testで一致する。
- existing `write_morph_vmd()`、`build_preview_data()`、pipeline / diagnostics回帰を壊さない。
- 新規B2 testと指定回帰がpassし、結果とprocess exit codeが記録される。
- dependency、package、network、Qt、固定モーフに変更がない。
- B3 Implementation Plan策定へ進めるか明示される。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| coreとwriterの循環import | writer module-levelではcoreをimportせず、writer初期化後の専用adapterとfunction-local delegationを使う。fresh-processでimport順序とlegacy callを検証する |
| `src.*` とtop-level packageの二重loadでclass identityが分岐する | 新規public APIは `src.core.*` に固定し、legacy writer wrapperはpackage-relative adapterとstructural boundaryを使う。src / top-level / mixed importをfresh-processで検証する |
| candidate observationの不正参照がnegative indexまたは `IndexError` になる | 全参照indexの型・範囲・span / bracketing順序をlookup前に検証し、`AdjustmentContractError` へ統一する |
| private helper移動で既存testが大量破損 | writer側に薄いcompatibility wrapperを残し、core testへ段階移行する |
| empty adjustmentでもVMD shapeが変わる | 152件baselineとexact frame / control point比較を先に固定する |
| Previewとwriterで再びshape順序が分岐 | candidate / grouping / tail / control point生成をEffectiveShapePlan作成時に一度だけ行う |
| source durationをtimeline末尾から誤推測 | full resolverでは明示値必須。legacy compatibility pathと分離する |
| source durationで既存tailを切り詰める | duration上限はreal event intervalだけに適用し、最終tail超過と次shape clampの現行semanticsを回帰testで固定する |
| MS21 rangeをlegacy writerへ遡及適用する | adjustment / `ShapeParameters` の0から100 rejectと、legacy非負整数・100超受理を別testで固定する |
| shape定数がcore / writerでdriftする | algorithm内部定数はcoreだけで所有し、互換上mirrorが必要な3定数は一致testを追加する |
| sort後indexをcanonical keyにする | ordinalを先に付与し、shape orderingではprovenanceを保持する |
| observation変更が明示peakを上書きする | candidate flagとRMS補助を分離し、explicit fieldを正本にする |
| stale tail overrideがlatentに残る | update APIでgroup再計算後にsame transaction canonical removalする |
| raw float hashが環境差を持つ | finite確認後のhex canonicalizationを固定する |
| VmdWriterParametersを直接importしてdiagnosticsと結合する | B2専用 `ShapeParameters` DTOを使い、B5でadapterする |
| B2でGUI stateまで広げる | UiState、MainFrame、RightPane、selection、historyをOut of Scopeに維持する |
| final normalizationまでcoreへ移し過ぎる | shared shape semanticsだけcoreへ移し、binary / final morph normalizationはwriterに残す |

## 14. Codex 実装時の注意

- 最初にGit状態、B1 plan、Block Breakdown、本planを再確認する。
- implementation前にplanと現行code / testの齟齬をP1 / P2 / P3で分類する。
- shell commandは一つずつ実行し、parallel、pipeline、chained commandを使用しない。
- production変更前に既存private helperのcallerを `rg` で全確認する。
- user-owned差分をrestore、上書き、無断stageしない。
- broad renameや一括移動を避け、compatibility wrapperを使って小さく抽出する。
- base inputやtest expectationを弱めて移行を成功扱いにしない。
- non-finite、不正index、不正frameをsilent skip / clampしない。
- `VowelTimingPlan` へadjustment fieldを追加しない。
- Preview cacheやGUI文字列をwriter inputにしない。
- B2完了時点でGUI編集またはadjusted VMD保存を実装済みと記載しない。
- dependency、package、release、merge、push、tagは明示依頼なしに行わない。
- wxPython主系、固定モーフ、local-only/no-network契約を維持する。

実装完了報告は次を含める。

1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
