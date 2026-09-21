# MS20-B2 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B2 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
- 対象Block: MS20-B2
- Block名: Structured Diagnostics Core Foundation
- 実施予定ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `2d06750 Complete MS20-B1 contract review`
- 作成日: 2026-07-14
- 文書ステータス: Implemented / Consumed by B3
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 直接の前提契約:
  - `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B2は、B1で固定した診断契約をUI非依存のcoreモデルとpure builderへ実装するBlockである。RightPane表示、GUI状態保持、VMD保存policy、reportファイル出力は接続しない。

### 1.1 実施結果

- 実装コミット: `b6f4254 Implement MS20-B2 diagnostics core foundation`
- `src/core/output_diagnostics.py`、pipeline共有helper、`src.core` export、B2 core testを実装した。
- B2単体: 12件pass表示、終了コード0。
- 非正duration回帰: 1件pass表示、終了コード0。
- pipeline / wx限定回帰: 24件pass表示、終了コード0。
- 全体: 380件pass表示。既知wx終了処理由来のprocess exit code 1を別記録した。
- GUI、UiState、Warning、save policy、report、依存関係、packageは変更していない。
- B3は2026-07-16に本Blockの公開APIを利用してRightPane Infoへ接続済みである。本Block自体の追加変更はない。

## 2. 背景

MS20-B1では、Info、Warning、VMD保存policy、diagnostic reportが共通利用する診断snapshotについて、次を固定した。

- 診断参照元と `INFO / WARNING / ERROR` のseverity正規化
- diagnostic codeと抑制規則
- `DiagnosticFailureInput` をGUI状態から分離する責務
- timelineだけでなくobservationsとclosing parameterを含むcanonical writer input
- 表示文言から独立したdiagnostic identity
- 再生位置等を除外するsave-state fingerprint
- B2をUI非依存core、B5をUiState保持、B7を横断破棄回帰とするBlock所有権

現行実装では、`VowelTimingPlan` がtimeline、anchors、source、warning、observationsを保持し、`UiState.vmd_save_ready` が既存の解析有効性と入力契約を判定している。しかし、これらを構造化診断へ変換する共通モデルとbuilderは存在しない。

B2では、後続Blockが表示文字列やGUI状態から診断を再推測しないように、B1契約を `src/core/output_diagnostics.py` の公開APIとして固定する。

2026-07-14のpre-implementation checkで検出したP2 / P3は、次のとおり本計画へ反映済みである。

| finding | 解消内容 |
| --- | --- |
| P2: fingerprint対象と保存直前の非正duration補完が不一致 | 現行補完処理をpure helperへ抽出し、writer保存と診断入力で共有する |
| P2: frozen DTO内へ可変な `VowelTimingPlan` listを保持 | 診断専用 `DiagnosticTimingPlanInput` を追加し、全collectionをtupleへcopyする |
| P2: 実装に存在しないreadable flagへ依存 | path有無だけを状態診断とし、実在・読取・解析可否は現行保存時I/Oへ残す |
| P2: `analysis_failure` の条件がB1より拡大 | failure DTO経由へ限定し、構造的契約違反は `ValueError` とする |
| P3: canonical value / failure domainの型が未確定 | recursive canonical型aliasとseverity / recoverabilityの許容値を固定する |

実装開始時に残っていた契約境界は、次の実装規則で固定する。

- `build_save_state_fingerprint_payload()` は非有限値を受けた場合に `ValueError`（内部の非有限入力マーカーを含む）を送出する。`build_output_diagnostics_snapshot()` だけがそれを捕捉し、`writer_input_non_finite` failure、`analysis_failure` ERROR、`fingerprint_payload=None`、`save_state_fingerprint=None`へ正規化する。
- diagnostic identityのphaseは、状態診断を `pipeline_build`、TEXT不足を `text_validate`、解析WAV不足を `analysis_wav_validate`、VMD writer入力を `vmd_write` とする。明示failureの元phaseとidentity contextは `analysis_failure` の `failures` contextへ安定tupleとして保持し、表示用detailや例外文はidentityへ含めない。
- `legacy_save_contract_unsatisfied` は `source_severity="error"`、`phase="vmd_write"`、`recoverability="cannot_continue"`、`(("existing_vmd_save_ready", False),)` を固定し、明示または合成のfailureをcode等でsortして1項目へ集約する。
- timelineの負値・未対応morph・不正interval、observationの構造不正、writer parameter不正は `ValueError` とし、診断failureへ暗黙変換しない。有限性だけを非有限入力failureへ変換する。

## 3. 目的

- UI非依存の不変DTOと診断snapshotを実装する。
- 同じ入力値から同じdiagnostic item順、canonical payload、fingerprintを生成する。
- B1で固定した保存禁止ERROR、fallback WARNING、準備完了INFOを決定的に生成する。
- VMD writerが参照するtimeline、observations、closing parameterをfingerprintへ漏れなく含める。
- exception message、UI文言、object identity、再生位置をfingerprintから除外する。
- B3からB7が同一snapshotを利用できる公開APIとcore単体テストを成立させる。

## 4. In Scope

- `DiagnosticSeverity`
- `SourceDiagnosticSeverity` / `DiagnosticRecoverability`
- `CanonicalValue` / `DiagnosticIdentityContext` / `FingerprintPayload`
- `DiagnosticFailureInput`
- `DiagnosticTimingPlanInput`
- `VmdWriterParameters`
- `DiagnosticSnapshotInput`
- input / analysis / generation / saveability summary
- `DiagnosticItem`
- `OutputDiagnosticsSnapshot`
- diagnostic itemの生成、severity順・code順・抑制
- event数、anchor数、timing source、fallback、最大frameの導出
- canonical timeline / observations / writer parameter / diagnostic identity payload
- Windows前提のpath正規化
- SHA-256 save-state fingerprint
- 非有限writer入力のfail-closed診断
- writer保存直前とfingerprintで共用するtiming plan正規化境界
- `src/core/__init__.py` からの公開export
- 新規core単体テスト
- B2実施結果に限定した計画・routing文書の更新

## 5. Out of Scope

- `UiState` から `DiagnosticSnapshotInput` を組み立てるGUI adapter
- `UiState` へのsnapshot、failure、確認済みfingerprint保持
- analysis callback、audio callback、late result、resetへの接続
- RightPane Info / Warningの表示変更
- 再生位置、現在frame、現在母音のlive表示
- VMD保存ボタン／メニューの有効条件変更
- WARNING保存確認ダイアログ
- report文字列化、保存ダイアログ、ファイル書き込み
- `VowelTimingPlan`、`PipelineResult`、`AnalysisWorkerResult` のデータ契約変更
- pipeline timing、peak評価、VMD形状生成アルゴリズムの動作変更
- 固定モーフ `あ / い / う / え / お` の変更
- 新規依存関係
- README、配布文書、package、release、tag、push
- 外部通信、外部クラウドASR、他ASR backend、Whisper自動download
- Qt / PySide6の復活

## 6. 前提条件

- 作業開始時に `feature/MS20-implementation`、HEAD、未コミット差分を再確認する。
- 未コミット差分がある場合はユーザー所有変更として保護する。
- MS20-B1の契約固定を未完了へ戻さない。
- B2 coreは `wx`、`gui_wx`、`UiState`、`MainFrame`、`AppController` をimportしない。
- builderはファイル存在確認、ダイアログ表示、ファイル書き込み、状態変更を行わない。
- B2はpathの有無だけを状態契約として診断する。実ファイルの存在、読取可能性、UTF-8 decode、WAV解析可否は保存時I/Oで再検証する現行契約を維持する。
- 現行 `UiState.vmd_save_ready` 相当の値は `existing_vmd_save_ready` として明示入力し、診断ERRORと論理積を取る。
- `morph_upper_limit` は解析済みtimeline値へ反映済みであり、変更時にplanを無効化する現行契約を維持する。B2 fingerprintへ重複格納しない。
- model nameはWhisper modelではなく、VMD writerへ渡す `vmd_model_name` を意味する。

## 7. 対象ファイル

### 7.1 主変更

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/core/output_diagnostics.py` | DTO、diagnostic builder、canonical payload、SHA-256 fingerprint |
| `src/core/pipeline.py` | 既存の非正duration補完を保存処理とB2入力で共有するpure helperへ抽出。保存結果は変更しない |
| `src/core/__init__.py` | B2公開型・公開関数のexport |

### 7.2 テスト

| ファイル | 変更内容 |
| --- | --- |
| 新規 `tests/test_ms20_b2_output_diagnostics.py` | DTO、diagnostic、canonicalization、fingerprintのcore単体テスト |

新規テスト内に `_make_timing_plan()`、`_make_observation()` 等の局所fixture helperを置く。既存の共通test helperは変更しない。

### 7.3 関連確認のみ

- `src/gui_wx/ui_state.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/voice_only_errors.py`
- `src/vmd_writer/writer.py`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`

### 7.4 計画・実施結果の文書

- 新規 `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
- routing同期に限定した `docs/MS20_and_Beyond_Index.md`
- 次作業同期に限定した `docs/MS20_and_Beyond_Roadmap.md`
- B2状態同期に限定した `docs/Implementation_Plan/MS20_Block_Breakdown.md`

B2実装中にREADME、配布用readme、`docs/repo_milestone.md`、`docs/Version_Control.md`、正本仕様を変更しない。MS20全体のユーザー文書・仕様同期はB7が所有する。

## 8. 実装方針

### 8.1 モジュール境界

`src/core/output_diagnostics.py` は次の依存だけを許可する。

- Python標準ライブラリ: `dataclasses`、`enum`、`hashlib`、`json`、`math`、`os`、`pathlib`、`typing`
- `src.core.pipeline` の `VowelTimingPlan`、`PeakValueObservation`、`PeakValueEvaluation`、`resolve_vmd_writer_timing_plan`
- `src.core.whisper_timing` の `SpeechTimingAnchor`
- `src.vmd_writer` の `VMD_FPS`、`SUPPORTED_MORPHS`、`VowelTimelinePoint`

GUI、worker、settings、filesystem I/Oを直接参照しない。B2で新規依存関係は追加しない。

### 8.2 公開データモデル

全DTOは `@dataclass(frozen=True)` とし、可変collectionをoutputへ保持せずtupleへ変換する。

```text
DiagnosticSeverity(str, Enum)
  INFO = "INFO"
  WARNING = "WARNING"
  ERROR = "ERROR"

SourceDiagnosticSeverity = Literal[
  "info", "warning", "error", "fatal", "cancelled"
]

DiagnosticRecoverability = Literal[
  "retry_possible", "select_file_again", "fallback_used",
  "restart_recommended", "cannot_continue", "cancelled_by_user"
]

CanonicalScalar: TypeAlias = None | bool | int | str
CanonicalValue: TypeAlias = CanonicalScalar | tuple["CanonicalValue", ...]
DiagnosticIdentityContext: TypeAlias = tuple[tuple[str, CanonicalValue], ...]
FingerprintPayload: TypeAlias = tuple[tuple[str, CanonicalValue], ...]

DiagnosticFailureInput
  code: str
  source_severity: SourceDiagnosticSeverity
  phase: str
  recoverability: DiagnosticRecoverability
  identity_context: DiagnosticIdentityContext = ()
  summary: str = ""
  detail: str = ""

VmdWriterParameters
  vmd_model_name: str = "AutoLipTool"
  closing_hold_frames: int = 0
  closing_softness_frames: int = 0

DiagnosticTimingPlanInput
  vowels: tuple[str, ...]
  timeline: tuple[VowelTimelinePoint, ...]
  anchors: tuple[SpeechTimingAnchor, ...]
  source: str
  warning: str | None
  observations: tuple[PeakValueObservation, ...] | None

DiagnosticSnapshotInput
  input_mode: str
  text_path: Path | None
  text_content_present: bool
  source_audio_path: Path | None
  effective_wav_path: Path | None
  analysis_text_present: bool
  analysis_result_valid: bool
  analysis_pending_rebuild: bool
  timing_plan: DiagnosticTimingPlanInput | None
  existing_vmd_save_ready: bool
  writer_parameters: VmdWriterParameters
  failure: DiagnosticFailureInput | None = None
  analysis_cancelled: bool = False
```

`CanonicalValue` はraw floatを許さない。finite floatはcanonicalization時に `("float_hex", value.hex())` というtupleへ変換する。`DiagnosticFailureInput.summary` / `detail` は表示用の正規化済み情報であり、fingerprintへ含めない。exception instance、traceback、`str(error)` を連結したダイアログ文面は保持しない。`identity_context` はkey昇順へ正規化し、重複keyを拒否する。

`DiagnosticTimingPlanInput` は、保存処理と共有する `resolve_vmd_writer_timing_plan()` の結果を境界でcopyして構築する。元の `VowelTimingPlan` が持つlistをそのまま保持せず、全collectionをtupleへ変換する。これによりfrozen dataclass内へ可変listを残さず、DTO構築後にcaller側listが変更されてもsnapshotとfingerprintは変化しない。

`DiagnosticSnapshotInput` は現行 `UiState` をimportせずに必要値を表現する。B3以降のGUI adapterは次の対応で組み立てるが、そのadapter自体はB2で実装しない。

| DTO | 後続GUI adapterの参照元 |
| --- | --- |
| `input_mode` | `UiState.input_mode` |
| `text_path` | `selected_text_path` |
| `text_content_present` | `bool(selected_text_content)` |
| `source_audio_path` | `selected_audio_input` または `selected_wav_path` のsource path |
| `effective_wav_path` | `selected_analysis_wav.analysis_wav_path` 優先、fallbackとして `selected_wav_path` |
| `analysis_text_present` | `bool(analysis_text_content or transcription_text)` |
| analysis状態 | `analysis_result_valid`、`analysis_pending_rebuild`、`current_timing_plan` |
| writer入力正規化 | `current_timing_plan` と `selected_wav_analysis.speech_start_sec / speech_end_sec` から共有helperを呼び、正規化済み `DiagnosticTimingPlanInput` へcopy |
| `existing_vmd_save_ready` | `UiState.vmd_save_ready` |
| writer parameter | `ParameterPanel` のclosing値と現行固定VMD model name |

### 8.3 公開snapshot

```text
InputDiagnosticsSummary
  input_mode
  normalized_text_path
  normalized_source_audio_path
  normalized_effective_wav_path
  text_content_present
  analysis_text_present

AnalysisDiagnosticsSummary
  analysis_result_valid
  analysis_pending_rebuild
  timing_source
  anchor_count
  event_count
  max_frame
  timing_warning_present
  observation_fallback_count

GenerationDiagnosticsSummary
  vmd_model_name
  closing_hold_frames
  closing_softness_frames
  fingerprint_schema_version

SaveabilitySummary
  vmd_save_allowed
  blocking_codes
  warning_codes

DiagnosticItem
  code
  severity
  phase
  identity_context
  summary
  detail

OutputDiagnosticsSnapshot
  input_summary
  analysis_summary
  generation_summary
  saveability
  items
  fingerprint_payload
  save_state_fingerprint
```

`items`、`blocking_codes`、`warning_codes`、`identity_context`、`fingerprint_payload` はtupleとする。`fingerprint_payload` と `save_state_fingerprint` は通常 `None` ではないが、NaN / infinity等によりcanonical writer inputを安全に構築できない場合だけ `None` を許可する。この場合は、まず安定した `DiagnosticFailureInput` へ正規化し、そのDTOから保存禁止 `analysis_failure` を生成する。

### 8.4 公開関数

```text
build_output_diagnostics_snapshot(
    snapshot_input: DiagnosticSnapshotInput,
) -> OutputDiagnosticsSnapshot

build_save_state_fingerprint_payload(
    snapshot_input: DiagnosticSnapshotInput,
    items: tuple[DiagnosticItem, ...],
) -> FingerprintPayload

compute_save_state_fingerprint(
    payload: FingerprintPayload,
) -> str
```

`src/core/__init__.py` から上記の公開DTO、型alias、summary、snapshot、3関数、およびpipelineの `resolve_vmd_writer_timing_plan()` をexportする。private canonicalization helperやcode registryはexportしない。

## 9. 詳細ステップ

### Step 1: coreモデルを定義する

- `DiagnosticSeverity` を文字列Enumとして定義する。
- `SourceDiagnosticSeverity` と `DiagnosticRecoverability` は `docs/Error_Handling_Specification.md` 6.5 / 6.6の値だけを許す `Literal` とする。
- `CanonicalValue`、`DiagnosticIdentityContext`、`FingerprintPayload` をrecursive tuple型として定義し、raw float、dict、list、set、任意objectを公開payload型から除外する。
- 入力DTO、failure DTO、writer parameter、summary、item、snapshotをfrozen dataclassで定義する。
- inputとoutputのcollectionをtupleへ固定する。
- `input_mode`、failure severity、recoverability、parameter、identity contextの構造検証をbuilder入口へ集約し、不正値は `ValueError` とする。
- inputの `VowelTimingPlan` を変更せず、保存用正規化後の必要値を `DiagnosticTimingPlanInput` のtupleへcopyする。

### Step 2: writer入力の共有正規化境界を抽出する

- `src/core/pipeline.py` にpureな公開helper `resolve_vmd_writer_timing_plan()` を追加する。
- 入力は `timing_plan`、解析済みWAVから得た `speech_start_sec`、`speech_end_sec` とする。
- signatureは `resolve_vmd_writer_timing_plan(timing_plan: VowelTimingPlan, *, speech_start_sec: float, speech_end_sec: float) -> VowelTimingPlan` とする。
- timelineがすべて正durationなら、内容を変更せず返す。
- 非正durationを含む場合は、現行 `_infer_durations_from_midpoints()` を使ってdurationを補完し、現行どおりobservationsを `None` にしたplanを返す。
- `generate_vmd_from_text_wav()` は既存どおりcaller supplied planの分岐だけで、`generate_vmd_from_timing_plan()` は非空planの保存前に、このhelperを使用する。内部で新規構築したplanへ適用範囲を広げない。
- B2のcaller/test fixtureも同じhelperの結果から `DiagnosticTimingPlanInput` を構築し、実際にwriterへ渡るtimeline / observationsとfingerprint対象を一致させる。
- `_infer_durations_from_midpoints()` の計算式、例外条件、既存保存関数の引数・戻り値・出力を変更しない。

### Step 3: summaryを決定的に導出する

- `input_mode` は `text_audio` / `voice_only` だけを通常値として扱う。
- anchor数は `len(timing_plan.anchors)`、event数は `len(timing_plan.timeline)` とする。
- 最大frameは各eventの正規化済み `end_sec` に `round(end_sec * VMD_FPS)` を適用した最大値とする。timelineなしは `None` とする。
- timing sourceは `timing_plan.source`、warning有無は `timing_plan.warning is not None` とする。
- observation fallback件数は `fallback_reason` が空でないobservation数とする。
- pathは表示用summaryでも同一のpath正規化helperを通す。

### Step 4: diagnostic itemを生成する

severity順は `ERROR -> WARNING -> INFO`、同一severity内は次の固定code registry順とする。

| 順 | code | severity | 発生条件 | identity context |
| ---: | --- | --- | --- | --- |
| 1 | `analysis_rebuild_required` | ERROR | `analysis_pending_rebuild` | reason=`pending_rebuild` |
| 2 | `analysis_not_ready` | ERROR | rebuild待ちでなく、有効planがない | validityとplan有無 |
| 3 | `timing_plan_empty` | ERROR | 有効扱いplanのtimelineが空 | event_count=0 |
| 4 | `text_input_missing` | ERROR | `text_audio` で現在のTEXT pathがない | path_present=false |
| 5 | `voice_only_text_missing` | ERROR | `voice_only` で解析テキストなし | analysis_text_present=false |
| 6 | `audio_input_missing` | ERROR | 現在のeffective WAV pathがない | path_present=false |
| 7 | `analysis_failure` | ERROR | `DiagnosticFailureInput` あり | failure code / source severity / phase / recoverability / 安定context |
| 8 | `timing_fallback_used` | WARNING | `source == "even_fallback"` またはtiming warningあり | sourceと安定reason |
| 9 | `observation_fallback_used` | WARNING | `fallback_reason` が1件以上 | `(event_index, fallback_reason)` の安定tuple |
| 10 | `analysis_cancelled` | INFO | cancelあり、かつ他の保存禁止ERRORなし | reason=`cancelled_by_user` |
| 11 | `analysis_ready` | INFO | 有効な非空timelineがありERRORなし | ready=true |
| 12 | `vmd_save_ready` | INFO | 既存保存契約trueかつERRORなし | ready=true |

抑制・集約規則:

- `analysis_rebuild_required` がある場合は `analysis_not_ready` を生成しない。
- `timing_plan_empty` は「planはあるがtimelineが空」の場合だけ生成し、同じ原因の `analysis_not_ready` を重ねない。
- ERRORが1件でもある場合は `analysis_ready`、`vmd_save_ready`、`analysis_cancelled` を生成しない。
- `existing_vmd_save_ready == False` なのに上記の明示ERRORを一つも導出できない場合、安定code `legacy_save_contract_unsatisfied` の `DiagnosticFailureInput` を構築し、通常のfailure経路からfail-closedの `analysis_failure` を生成する。
- failure DTOは1つの `analysis_failure` へ正規化し、source code、source severity、phase、recoverability、安定contextをidentityへ含める。
- 非有限writer値はcanonicalization前に安定code `writer_input_non_finite`、`source_severity="error"`、`phase="vmd_write"`、`recoverability="cannot_continue"`、field / indexを示す安定contextを持つ `DiagnosticFailureInput` へ正規化する。そのDTOを通常のfailure経路へ渡し、`analysis_failure` の生成条件を一つに保つ。
- 未知input mode、負のclosing parameter、空VMD model name、不正identity context、未対応morph等の構造的な契約違反はprogramming errorとして `ValueError` を送出する。diagnostic itemへ暗黙変換しない。
- B2がpathから実在性・読取可能性を予測しないため、snapshot作成後に外部ファイルが消失・破損した場合は現行保存処理の `exists()`、TEXT読取、WAV解析と既存例外処理が責任を持つ。B5以降はその失敗を `DiagnosticFailureInput` として保持できるが、B2ではI/Oを行わない。
- timing warning文字列はsummary / detailに使用してよいがidentityへ含めない。`even_fallback` は `even_fallback`、それ以外のwarningは `timing_warning_present` を安定reasonとする。
- observation fallbackは1項目へ集約し、件数だけでなく `(event_index, fallback_reason)` をevent index、reasonの順で安定sortする。
- anchor数、event数、通常timing sourceはInfo summaryであり、それだけでは保存結果・警告確認の意味を変えないため `analysis_ready` のidentityへ入れない。event内容はcanonical timeline、fallback sourceはWARNING identityで別途追跡する。

初期summary文言は次を正本とする。detailは構造値から決定的に組み立て、raw exception messageを含めない。

| code | summary |
| --- | --- |
| `analysis_not_ready` | 解析結果がありません。 |
| `analysis_rebuild_required` | 入力または設定の変更後に再解析が必要です。 |
| `timing_plan_empty` | 有効な母音イベントがありません。 |
| `text_input_missing` | TEXT入力を確認してください。 |
| `voice_only_text_missing` | 音声のみ解析の書き起こしがありません。 |
| `audio_input_missing` | 解析用音声を確認してください。 |
| `analysis_failure` | 解析結果をVMD保存に使用できません。 |
| `timing_fallback_used` | タイミング解析でfallbackを使用しました。 |
| `observation_fallback_used` | 一部イベントの音量評価でfallbackを使用しました。 |
| `analysis_cancelled` | 解析はキャンセルされました。 |
| `analysis_ready` | 解析結果を利用できます。 |
| `vmd_save_ready` | VMDを保存できます。 |

### Step 5: canonical pathを実装する

Windows 11を対象に、全pathへ次を同じ順で適用する。

1. `os.fspath()` で文字列化する。
2. `os.path.abspath()` と `os.path.normpath()` を適用する。
3. `os.path.normcase()` でWindowsの大文字小文字規則へ正規化する。
4. 区切り文字を `/` へ統一する。

builderは `resolve()`、`exists()`、`stat()` を呼ばない。file size / mtimeはB1で採用していないためpayloadへ含めない。relative pathの基準はbuilder実行時のcurrent working directoryとなるため、GUI adapterと単体テストはabsolute pathを渡す。

### Step 6: canonical writer inputを実装する

fingerprint schema versionは `ms20-output-diagnostics-v1` とする。

canonical payloadはdictではなく、key名を持つ明示tupleを次の固定順で構築する。

```text
schema_version
input_mode
normalized_text_path
normalized_effective_wav_path
timeline
observations_state
observations
writer_parameters
diagnostic_identities
```

timelineは元list順を保ち、各eventを次の順で格納する。

```text
event_index
time_sec
vowel
value
duration_sec
start_sec
end_sec
peak_value
```

observationsは `None` と空tupleを別表現にする。各observationは元list順、各fieldは現行 `PeakValueObservation` の宣言順で格納する。

```text
event_index
vowel
time_sec
initial_interval_start_sec
initial_interval_end_sec
refined_interval_start_sec
refined_interval_end_sec
peak_window_start_sec
peak_window_end_sec
local_peak
global_peak
peak_value
reason
fallback_reason
window_sample_count
evaluation
rms_window_times_sec
rms_window_values
is_bridgeable_same_vowel_micro_gap_candidate
is_same_vowel_burst_candidate
is_bridgeable_cross_vowel_transition_candidate
is_cross_vowel_zero_run_continuity_floor_candidate
is_bridgeable_micro_gap_candidate
bridge_candidate_reason
previous_non_zero_event_index
next_non_zero_event_index
span_start_index
span_end_index
```

nested `PeakValueEvaluation` は次の宣言順とする。

```text
interval_start_sec
interval_end_sec
peak_window_start_sec
peak_window_end_sec
local_peak
peak_value
reason
```

writer parameterは次の順とする。

```text
vmd_model_name
closing_hold_frames
closing_softness_frames
```

diagnostic identityはseverity順・固定code順に並べた次のtupleとする。

```text
(severity, code, phase, identity_context)
```

`summary`、`detail`、timing warningのraw文字列、exception messageは含めない。

### Step 7: scalar正規化とhashを実装する

- finite floatは `("float_hex", value.hex())` へ変換し、表示丸めをしない。
- NaN / positive infinity / negative infinityはcanonical payloadへ入れず、`writer_input_non_finite` の `DiagnosticFailureInput` を経由して保存禁止 `analysis_failure` とfingerprint `None` にする。
- boolはintへ暗黙変換せずboolのまま保持する。
- tuple、`None`、str、int、boolだけで最終payloadを構成する。
- dict、set、object `repr()`、object identityをpayloadへ入れない。
- canonical tupleを `json.dumps(..., ensure_ascii=False, separators=(",", ":"), allow_nan=False)` でUTF-8 bytesへ変換する。
- `hashlib.sha256()` を使い、fingerprint表現は `sha256:<64文字lowercase hex>` とする。
- `Generated At`、再生位置、frame、現在母音、RightPane状態、status bar、保存先、dialog状態を入力DTOとpayloadの両方へ追加しない。

### Step 8: saveabilityを構築する

```text
has_error = itemsにERRORが1件以上
vmd_save_allowed = existing_vmd_save_ready and not has_error
blocking_codes = ERROR codeの表示順tuple
warning_codes = WARNING codeの表示順tuple
```

WARNINGは保存可否をfalseにしない。WARNING確認済みfingerprintの保持とダイアログ制御はB5で実装する。

### Step 9: core exportを追加する

- `src/core/__init__.py` ではpipeline import後にB2公開APIをimportする。
- `__all__` へ公開型・公開関数を追加する。
- private helper、schema定数、code order定数は公開しない。
- import時にwxPythonやGUI moduleが読み込まれないことを単体テストで確認する。

### Step 10: 単体テストと回帰を実行する

- 最初に新規B2 testだけを実行する。
- 次にpipeline / VMD保存状態の限定回帰を実行する。
- 最後に全testsを実行する。
- pass表示とprocess exit codeを分けて記録する。
- test failureを回避するために既存テストを弱めない。

### Step 11: B2実施結果を記録する

- 実際に追加した公開APIとschema versionを本書へ記録する。
- 計画との差分があれば理由を記録する。
- B3開始条件、未検証事項、test結果を明記する。
- B3のGUI adapter、RightPane表示、B5のfailure保持をB2へ先行実装しない。

## 10. 状態遷移 / データ契約

### 10.1 B2の処理境界

```text
GUI / test fixture
  ├─ VowelTimingPlan + speech interval
  │    ↓ resolve_vmd_writer_timing_plan()
  │  writer実入力と同じ正規化済みplan
  └─ 明示的にtupleへcopy
DiagnosticSnapshotInput
  ↓ pure / deterministic
build_output_diagnostics_snapshot()
  ├─ summary
  ├─ ordered DiagnosticItem tuple
  ├─ canonical fingerprint payload
  └─ OutputDiagnosticsSnapshot
```

- B2 builderはsnapshotをcache・永続化しない。
- B2 builderは `UiState`、timing plan、failure inputを変更しない。
- `resolve_vmd_writer_timing_plan()` は入力planを変更せず、非正durationがある場合だけ新しいplanを返す。
- B2 builderはWARNING確認済み状態を保持しない。
- callerが入力値を変更した場合は、新しいDTOからsnapshotを再生成する。

### 10.2 状態別期待値

| 入力状態 | 主diagnostic | 保存可否 |
| --- | --- | --- |
| 初期・未解析 | `analysis_not_ready` と不足input ERROR | 不可 |
| 入力変更後 | `analysis_rebuild_required` | 不可 |
| 有効plan・入力契約成立 | `analysis_ready`、`vmd_save_ready` | 可 |
| timing fallback | `timing_fallback_used` とready INFO | 可。B5で確認対象 |
| observation fallback | `observation_fallback_used` とready INFO | 可。B5で確認対象 |
| empty timeline | `timing_plan_empty` | 不可 |
| 明示failure | `analysis_failure` | 不可 |
| cancelのみ | 現在状態を再評価し、ERRORなしの場合だけ `analysis_cancelled` | 現行契約による |
| 非有限writer入力 | `DiagnosticFailureInput(writer_input_non_finite)` 経由の `analysis_failure`、fingerprint `None` | 不可 |
| 構造的な契約違反 | diagnosticを生成せず `ValueError` | snapshot構築失敗 |

### 10.3 failure ownership

- B2は `DiagnosticFailureInput` とbuilderだけを所有する。
- B2 testはfailure DTOを直接生成して渡す。
- B2は現在GUIがfailureを保持していると仮定しない。
- B5が現在analysis jobのerror callbackからfailure DTOを設定・clearする。
- B7がinput変更、parameter変更、cancel、reset、late callbackの破棄を回帰固定する。

### 10.4 compatibility

- 既存 `VowelTimingPlan`、`PipelineResult`、`VmdGenerationResult`、`VowelTimelinePoint` のfield・意味を変更しない。
- 既存VMD生成関数の引数・戻り値・writer出力を変更しない。
- `resolve_vmd_writer_timing_plan()` は重複している現行の保存前処理を公開名へ抽出するだけであり、新しいtimingアルゴリズムを追加しない。
- `UiState.vmd_save_ready` を置換しない。
- B2 moduleを利用しない既存経路の動作は変えない。

## 11. テスト方針

### 11.1 新規core単体テスト

`tests/test_ms20_b2_output_diagnostics.py` で少なくとも次を検証する。

#### DTO / import境界

- 公開DTOがfrozenである。
- input / output collectionがtupleである。
- `DiagnosticTimingPlanInput` 構築後に元planのlistを変更してもDTOとfingerprintが変化しない。
- `SourceDiagnosticSeverity`、`DiagnosticRecoverability`、`CanonicalValue`、`DiagnosticIdentityContext`、`FingerprintPayload` の公開型契約が定義どおりである。
- `src.core.output_diagnostics` importにwxPython、`gui_wx`、`UiState`が不要である。
- `src.core` から公開APIをimportできる。

#### diagnostic生成

- 初期状態で保存禁止ERRORを生成する。
- rebuild待ちは `analysis_not_ready` を抑制し、`analysis_rebuild_required` を生成する。
- empty timeline、TEXT不足、voice_only解析テキスト不足、WAV不足を別codeにする。
- valid text_audio / voice_onlyで `analysis_ready` と `vmd_save_ready` を生成する。
- timing fallbackとobservation fallbackをWARNINGにし、保存可能性を維持する。
- failure DTOを `analysis_failure` へ変換し、raw severity / phase / recoverabilityをidentityへ保持する。
- 非有限writer値が `writer_input_non_finite` のfailure DTO経由で `analysis_failure` になる。
- 未知input mode、負のclosing parameter、空VMD model name、不正identity context、未対応morphは `ValueError` となり、`analysis_failure` に暗黙変換されない。
- cancelだけを保存可能へ倒さず、現在のERRORを再評価する。
- severity順と固定code順が入力collection順に依存しない。
- ERROR時にready INFOを生成しない。
- `existing_vmd_save_ready` とderived診断が矛盾した場合にfail-closedとなる。

#### summary導出

- anchor数、event数、timing source、fallback件数を導出する。
- 最大frameが現行 `round(end_sec * 30)` と一致する。
- timelineなしの最大frameは `None` になる。

#### fingerprint決定性

- 非正durationを含むplanで、既存保存関数と共有helperが同じtimeline補完・observations `None` を使用する。
- 補完後のeffective writer inputがfingerprintへ入り、補完前planの無効durationをそのままhashしない。
- 同一inputから同一payloadと同一fingerprintを得る。
- pathの区切り・case差がWindows同一pathとして正規化される。
- timelineの `time_sec / vowel / value / duration_sec / start_sec / end_sec / peak_value` の各変更でfingerprintが変わる。
- observationとnested evaluationの各field変更でfingerprintが変わる。
- RMS系列、candidate flag、前後index、span indexの変更でfingerprintが変わる。
- `None` observationsと空observationsでpayloadとfingerprintが異なる。
- `vmd_model_name`、`closing_hold_frames`、`closing_softness_frames` の各変更でfingerprintが変わる。
- diagnosticのseverity / code / phase / identity_context変更でfingerprintが変わる。
- `summary` / `detail` だけの変更でfingerprintが変わらない。
- input DTOに再生位置、現在frame、現在母音、保存先、UI状態のfieldがない。
- finite floatがhex表現で決定的にpayload化される。
- NaN / infinityで通常fingerprintを生成せず、ERRORと `None` を返す。
- fingerprintが `sha256:` と64文字lowercase hexの形式になる。

### 11.2 実行順

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py::PipelineAndVmdTests::test_generate_vmd_from_timing_plan_infers_non_positive_durations
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py tests/test_wx_ms14_b2_state.py tests/test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests
```

各コマンドは一つずつ実行し、完了を待ってから次へ進む。pass表示とprocess exit codeを別々に報告する。

### 11.3 手動・build確認

- 手動GUI確認: 実施しない。GUI変更なし。
- 実MMD確認: 実施しない。writer出力変更なし。
- build / SmokeLaunch: 実施しない。依存関係・package設定変更なし。

### 11.4 文書検証

```powershell
git diff --check
```

実装後はstaged / unstagedの対象ファイルを確認し、B2範囲外のGUI・仕様・設定変更がないことを監査する。

## 12. 受け入れ条件

- `src/core/output_diagnostics.py` が追加されている。
- `src/core/__init__.py` からB2公開APIをimportできる。
- core moduleがwxPython、GUI、UiState、callback、filesystem I/Oに依存しない。
- B1で固定した12 diagnostic codeを安定順で生成できる。
- `analysis_not_ready` / `analysis_rebuild_required` / `timing_plan_empty` の重複抑制が成立する。
- path未設定による保存入力契約不成立と、failure DTOへ正規化した非有限writer入力が `ERROR` になる。
- 実ファイルの存在・読取可否をB2 builderが判定せず、現行保存時I/Oの再検証契約が保持される。
- fallbackが `WARNING` となり、それだけでは保存不可にならない。
- 同一inputから同一canonical payloadとSHA-256 fingerprintを得る。
- timeline、observations、nested evaluation、closing parameter、VMD model name、diagnostic identityがfingerprintへ含まれる。
- `None` observationsと空observationsが区別される。
- summary / detail、raw exception message、object repr、再生位置、UI状態、保存先がfingerprintから除外される。
- path正規化、finite float hex化、JSON serialization、fingerprint表現が計画どおりである。
- ERROR時に `vmd_save_allowed` がfalseとなる。
- WARNINGだけの場合は既存保存契約がtrueなら `vmd_save_allowed` がtrueとなる。
- 既存pipelineの保存入力正規化は共有helperへ抽出されるが、VMD保存結果、VMD writer、UiState、GUI、固定モーフの挙動は変更されていない。
- 新規B2 test、限定回帰、全testsについて表示上の結果とprocess exit codeが記録されている。
- 新規依存関係、network、build、package変更がない。
- B3開始前に解消が必要な未記名の判断事項が残っていない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| frozen dataclass内にmutable listを保持し、不変snapshotと誤認する | 正規化済みplanを `DiagnosticTimingPlanInput` のtupleへcopyし、input / outputのどちらにもpipeline listを保持しない |
| `dataclasses.asdict()` や `repr()` でfield追加・文言変更がfingerprintを暗黙変更する | schema version付きの明示field tupleを使う |
| JSON float表現やNaN処理が環境依存になる | finite floatを `float.hex()` へ変換し、`allow_nan=False` とする |
| pathのcase・separator差で同一状態が別fingerprintになる | 全pathへ単一のWindows正規化helperを適用する |
| `resolve()` / `exists()` でbuilderがfilesystem状態に依存する | absolute pathの有無だけを明示入力し、存在・読取・解析可否は保存時I/Oが再検証する |
| 補完前timelineをhashし、実際のwriter入力とfingerprintがずれる | 現行の非正duration補完を `resolve_vmd_writer_timing_plan()` に抽出し、保存関数とB2入力で共用する |
| timelineだけをhashし、writerが参照するobservation差を見落とす | observation全fieldとnested evaluationをschemaへ列挙する |
| `None` observationと空listを同一扱いする | `observations_state` をpayloadへ明示する |
| timing warning本文やexception messageでfingerprintが変わる | 安定reasonとidentity contextだけをhashする |
| 同一codeでもfallback対象が変わったのに確認済みfingerprintを再利用する | event indexとfallback reasonのtupleをidentityへ含める |
| `morph_upper_limit` をparameterとtimelineの両方へ入れ、意味が重複する | timeline値と現行無効化契約を正本とし、重複格納しない |
| VMD model nameとWhisper model nameを混同する | field名を `vmd_model_name` に固定する |
| `existing_vmd_save_ready` falseの理由が診断に出ない | 明示ERRORがない矛盾状態を `analysis_failure` でfail-closedにする |
| B2がGUI adapterやfailure保持まで先行実装する | B2はDTO・pure builder・core testだけに限定する |
| `src/core/__init__.py` export追加でimport cycleが発生する | pipeline import後にoutput diagnosticsをimportし、対象回帰と全testsで確認する |
| 将来MS向けの汎用診断frameworkへ拡張する | MS20-B1の入力・12 code・B3からB7の直接利用だけを対象にする |

## 14. Codex 実装時の注意

```text
- コマンドは必ず一つずつ実行し、並列・パイプ・連結実行をしない。
- 解消済みpre-implementation checkのP2 / P3契約を実装開始時に再確認し、計画と現行コードのfield名を再照合する。
- B1の12 diagnostic codeを無断で追加・改名・削除しない。
- coreからwxPython、UiState、MainFrame、AppControllerをimportしない。
- builder内でpath.exists / stat / resolveやfile writeを行わない。
- 入力のVowelTimingPlan、timeline、observationsを変更しない。
- fingerprintにdict、set、repr、object identity、raw message、再生位置を使わない。
- VMD model nameとWhisper model nameを混同しない。
- 固定モーフ あ / い / う / え / お と30fps契約を変更しない。
- ERROR時はfail-closed、WARNINGだけでは保存可能性を失わせない。
- B3のRightPane、B5のUiState保持・保存確認、B6のreport出力、B7の破棄回帰を先行実装しない。
- 新規依存関係、外部通信、Whisper download、Qt / PySide6を追加しない。
- 既存テストを削除・skip・期待値緩和してpassさせない。
- 実行していないテスト、GUI、MMD、build確認を通過と報告しない。
```

B2完了報告は次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様からの逸脱
7. 残課題
```
