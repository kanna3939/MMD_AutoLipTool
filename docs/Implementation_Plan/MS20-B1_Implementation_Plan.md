# MS20-B1 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B1 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
- 対象Block: MS20-B1
- Block名: Diagnostics Contract / Current-State Pre-check
- 基準ブランチ: `feature/MS20`
- 基準コミット: `0d5ceb3 Establish MS20 and beyond roadmap`
- 作成日: 2026-07-13
- 最終更新日: 2026-07-14
- 実施ブランチ: `feature/MS20-implementation`
- 実施開始HEAD: `6df0fab Refine MS20-B1 diagnostic contracts`
- 文書ステータス: B1 Contract Fixed / Ready for B2 Implementation Plan
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B1は調査・契約固定Blockである。production code、GUI、テスト、build設定を変更しない。

## 2. 背景

MS20では、RightPane Info / Warning、VMD保存policy、診断reportが共通利用する構造化診断snapshotを導入する。ただし、現行データは複数レイヤーに分散している。

- `VowelTimingPlan`
  - vowels、timeline、anchors、source、warning、observationsを保持する。
- `UiState`
  - input mode、入力パス・音声情報、current timing plan、解析有効性、再生位置、VMD保存可否を保持する。
- `AnalysisWorkerResult`
  - timing plan、input mode、解析テキスト由来、voice_only書き起こし由来を保持する。
- `MainFrame`
  - 解析成功を `UiState` へ反映するが、解析失敗はダイアログ表示後に構造化状態として保持しない。
- `RightPane`
  - Info / Warning表示helperは文字列入力であり、診断の正本ではない。
- `Error_Handling_Specification`
  - `info / warning / error / fatal / cancelled` を定義するが、MS20の出力診断は `INFO / WARNING / ERROR` の3段階である。

これらを実装中に都度判断すると、Info、Warning、保存可否、report間で意味が分岐する。B1では現行実装を再監査し、B2以降が実装判断を再発明しない粒度まで契約を固定する。

## 3. 目的

- MS20の各診断項目に対し、現行コード上の参照元を特定する。
- 既存error severityをMS20の `INFO / WARNING / ERROR` へ正規化する規則を固定する。
- diagnostic codeの初期一覧と発生条件を固定する。
- WARNING確認の `save_state_fingerprint` 構成要素と無効化トリガーを固定する。
- fingerprintを、VMD writerへ渡る正規化済み入力と診断の構造値から決定的に生成する契約へ固定する。
- 解析失敗をUI非依存DTOとして表す責務と、UiState保持・callback接続・横断破棄のBlock所有権を固定する。
- reportのセクション、順序、空値表現、文字コードを固定する。
- B2からB7の実装・テスト境界を確定する。

## 4. In Scope

- 現行リポジトリの読み取り監査
- データ参照元マトリクスの確定
- severity正規化表の確定
- diagnostic code初期レジストリの確定
- 表示文言とは独立したdiagnostic identity contextの確定
- snapshot / fingerprint入力と除外項目の確定
- snapshot生成タイミングと破棄タイミングの確定
- reportフォーマット契約の確定
- B2の主変更ファイル候補、API、単体テスト境界の確定
- B3からB7への引き継ぎ事項整理
- B1実施結果の本文更新または別紙記録

## 5. Out of Scope

- production code変更
- wxPython GUI変更
- テストコードの追加・変更
- 自動テストを通すための補修
- `UiState`、`PipelineResult`、`VowelTimingPlan`、`AnalysisWorkerResult` のAPI変更
- RightPane Info / Warningの本実装
- VMD保存policyの変更
- report保存導線とファイル出力の実装
- MS21以降の機能設計
- 新規依存関係
- build / package / release / tag / push
- Qt / PySide6 GUIの復活

## 6. 前提条件

- `feature/MS20` を作業ブランチとする。
- MS19 closeoutのA判定を未完了に戻さない。
- `docs/MS20_and_Beyond_Roadmap.md` と `docs/Implementation_Plan/MS20_Block_Breakdown.md` を上位計画とする。
- 現行の `UiState.vmd_save_ready` は解析有効性と入力契約の判定であり、MS20構造化診断は未接続である。
- 現行 `VowelTimingPlan.warning` は単一文字列または `None` であり、diagnostic codeを持たない。
- 現行の解析失敗情報はダイアログ表示後に診断snapshotとして保持されない。
- 表示文字列をデータ正本としない。
- 作業開始時に現行HEADと未コミット差分を再確認する。

## 7. 対象ファイル

### 7.1 主要確認対象

| ファイル | 確認する責務 |
| --- | --- |
| `src/core/pipeline.py` | timing plan、pipeline result、warning、anchor、observation、timeline |
| `src/gui_wx/ui_state.py` | input identity、analysis validity、VMD保存可否、reset / invalidate、再生位置 |
| `src/gui_wx/analysis_worker.py` | worker結果、input mode、テキスト由来、Whisper timing由来 |
| `src/gui_wx/main_frame.py` | analysis success / error / cancel / late result、RightPane反映、表示更新 |
| `src/gui_wx/app_controller.py` | VMD保存入口、再生更新、input変更、workspace reset統合 |
| `src/gui_wx/right_pane.py` | 現行Info / Warning表示APIとプレースホルダー |
| `src/gui_wx/parameter_panel.py` | VMD出力へ影響するparameterと変更通知 |
| `src/gui_wx/voice_only_errors.py` | voice_only失敗の現行分類と表示文言 |
| `src/vmd_writer/writer.py` | 秒からframeへの現行変換契約（範囲検索のみ） |

### 7.2 正本文書

- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`

### 7.3 テスト参照対象

B1ではテストを変更しない。次の既存テストから現行期待値とB2以降の回帰境界を読み取る。

- `tests/test_pipeline_and_vmd.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`

### 7.4 B1で変更する文書

- `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
- B1実施結果を反映する場合の `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- B1完了時のrouting更新に限定した `docs/MS20_and_Beyond_Index.md`
- B1完了後の次作業表示だけを同期する `docs/MS20_and_Beyond_Roadmap.md`

`README.md`、配布用readme、`repo_milestone.md`、`Version_Control.md` はB1で変更しない。

## 8. 実装方針

B1にproduction code実装はない。以下の方針で読み取り監査と契約固定を行う。

1. ロードマップ要求を診断項目、severity、保存policy、report、状態破棄に分解する。
2. 各要求を現行データ・状態・callbackへ対応付ける。
3. 「直接取得可能」「決定的に導出可能」「現行は保持していない」を区別する。
4. 既存error severityを削除・置換せず、出力診断用の3段階へ正規化する。
5. 表示文言ではなく、安定codeと出力影響にfingerprintを構成する。
6. B2のUI非依存snapshot builderが受け取る入力と返す出力を固定する。
7. B3からB7の実装所有権を分離する。

## 9. 詳細ステップ

### Step 1: リポジトリ基準線の固定

- `git status`、現在ブランチ、最近履歴を一つずつ確認する。
- 未コミット差分をユーザー所有として識別する。
- MS20 roadmap / Index / Block Breakdownの現在内容を基準とする。

### Step 2: 診断データ参照元監査

以下のマトリクスを現行コードで検証し、フィールド名、型、空値、生存期間を記録する。

| 診断項目 | 現行参照元候補 | 現時点の判定 |
| --- | --- | --- |
| input mode | `UiState.input_mode` | 直接取得可能 |
| TEXT | `selected_text_path`, `selected_text_content` | 直接取得可能 |
| 入力音声 | `selected_audio_input`, `selected_wav_path` | 表示名とidentityの優先順を要確定 |
| 解析用WAV | `selected_analysis_wav` | 直接取得可能 |
| 解析有効性 | `analysis_result_valid`, `analysis_pending_rebuild` | 直接取得可能 |
| timing source | `current_timing_plan.source` | 解析成功後に取得可能 |
| anchor数 | `len(current_timing_plan.anchors)` | 決定的に導出可能 |
| event数 | `len(current_timing_plan.timeline)` | 決定的に導出可能 |
| 最大frame | timelineの最大終了時刻と現行30fps変換 | 丸め契約の再確認が必要 |
| timing warning | `current_timing_plan.warning` | 取得可能だがcodeなし |
| observation fallback | `current_timing_plan.observations[].fallback_reason / reason` | 複数項目の安定コード化が必要 |
| writer入力 | timeline、observations、closing parameter | fingerprint用の正規化対象。timelineだけでは不足 |
| VMD保存可否 | `UiState.vmd_save_ready` | 現行入力契約は取得可能、severity未接続 |
| 解析失敗 | `_on_analysis_error()` の `error` | callback中だけ存在し、現行は保持なし |
| 再生位置 | `playback_position_sec` | 直接取得可能、fingerprint対象外 |

### Step 3: severity正規化契約の確定

初期契約は次とし、現行仕様の例外を監査する。

| 既存severity / 状態 | MS20診断 | 理由 |
| --- | --- | --- |
| `info` | `INFO` | 処理結果の説明 |
| `warning` | `WARNING` | fallback等で処理継続可能 |
| `error` | `ERROR` | 現在の保存入力契約が不成立 |
| `fatal` | `ERROR` | MS20表示は3段階。より強い失敗を降格しない |
| `cancelled` | `INFO` | ユーザー中止自体は出力異常ではない |
| 保存入力契約不成立 | `ERROR` | 不明状態を保存可能側へ倒さない |

`cancelled` 後に別の保存禁止理由が残る場合は、その理由を別の `ERROR` として生成する。`cancelled -> INFO` だけを根拠にVMD保存を許可しない。

### Step 4: diagnostic code初期レジストリの確定

B1実施時に、少なくとも次のcode候補を発生条件、severity、表示先、保存影響とともに固定する。

| code候補 | severity候補 | 発生条件 |
| --- | --- | --- |
| `analysis_not_ready` | `ERROR` | 有効なtiming planがない |
| `analysis_rebuild_required` | `ERROR` | `analysis_pending_rebuild` がtrue |
| `timing_plan_empty` | `ERROR` | timelineが空 |
| `text_input_missing` | `ERROR` | text_audioの保存契約でTEXTがない |
| `voice_only_text_missing` | `ERROR` | voice_onlyの解析テキストがない |
| `audio_input_missing` | `ERROR` | 保存対象の音声／解析WAV契約が不成立 |
| `timing_fallback_used` | `WARNING` | timing sourceが均等配分fallback、またはtiming warningあり |
| `observation_fallback_used` | `WARNING` | observationに `fallback_reason` あり |
| `analysis_ready` | `INFO` | 有効な解析結果あり |
| `vmd_save_ready` | `INFO` | 保存禁止理由なし |

同一原因から重複する `ERROR` と `INFO`、または複数 `WARNING` を生成する場合の抑制・集約規則も固定する。

各 `DiagnosticItem` は、表示用の `summary` / `detail` とは別に、同一診断状態を決定する `identity_context` を持つ。

```text
DiagnosticItem
  - code
  - severity
  - phase
  - identity_context: 安定key順の不変な構造値
  - summary: 表示用。fingerprint対象外
  - detail: 表示用。fingerprint対象外
```

- `identity_context` には、同じcodeでも結果・保存判断・ユーザー確認の意味が変わる値を入れる。例はfallback対象event index、fallback reason、対象件数、失敗category、recoverabilityである。
- exception message、翻訳済み文言、UI表示文言を `identity_context` に入れない。
- 同じcodeの複数項目を集約する場合も、対象indexやreasonの安定順tupleを保持し、件数だけで異なる内容を同一扱いにしない。
- fingerprint上のdiagnostic identityは、安定順に並べた `(severity, code, phase, identity_context)` とする。

### Step 5: fingerprint契約の確定

fingerprintは「同じVMD writer入力と同じ診断状態を持つか」を判定する。Python object identity、非決定的な `repr()`、表示文言に依存しない。B2では次のcanonical payloadを明示的なtupleへ正規化し、version識別子を付けてhashする。

含める:

- fingerprint schema version
- input mode
- 入力identity
  - TEXTあり: 正規化TEXT path
  - 共通: writerへ実際に渡す解析用WAV pathを優先した正規化effective WAV path
  - file size / mtimeは外部変更検知に使用する場合だけ両方を採用し、片方だけを任意採用しない
- analysis generationを導入する場合はその単調増加値。導入しない場合は下記canonical writer input自体を正本とする
- canonical timeline。元list順を維持し、各eventについて次を含める
  - event index
  - `vowel`
  - `time_sec`
  - `duration_sec`
  - `start_sec`
  - `end_sec`
  - `value`
  - `peak_value`
- canonical observations。`None` と空listを区別し、各 `PeakValueObservation` を元list順でdataclass宣言順に正規化する
  - `evaluation` はその各fieldを宣言順に展開する
  - `rms_window_times_sec` / `rms_window_values`、candidate flag、前後index、span indexも含める
  - これはwriterがbridge、smoothing、peak再評価でobservationsを参照するためであり、timelineだけをfingerprint正本にしない
- VMD writerへ渡す現行parameter
  - `closing_hold_frames`
  - `closing_softness_frames`
  - model name。現行固定値でもschema上は明示する
  - `morph_upper_limit` は解析済みtiming planのevent値へ反映済みであり、現行parameter変更時はplan自体が無効化される。重複入力にはせず、canonical timelineと無効化契約で扱う
- 安定順に並べたdiagnostic identity `(severity, code, phase, identity_context)`

正規化規則:

- pathはabsolute化・区切り統一・Windowsの大文字小文字規則を考慮した単一表現をB2で選び、同一処理を全pathへ適用する。
- floatは表示用丸めを行わず、有限値だけを受理して一つの決定的なシリアライズ規則を使う。NaN / infinityは保存入力不成立の `ERROR` とする。
- dictやsetの反復順、object identity、dataclassの既定 `repr()` をhash入力に使わない。
- hash algorithmはB2 Implementation Planで固定するが、canonical payload自体を単体テスト可能なpure valueとして先に生成する。

除外する:

- 再生位置、現在frame、現在母音
- RightPaneタブ・scroll位置
- status barの一時文言
- report保存先、VMD保存先
- ダイアログ開閉状態

無効化トリガー:

- TEXT／音声入力変更
- 解析開始・成功・失敗
- 解析結果へ影響するparameter変更
- voice_only書き起こし編集の適用／復元
- workspace reset

### Step 6: snapshot生成・破棄契約の確定

| event | snapshot | WARNING確認済みfingerprint |
| --- | --- | --- |
| 初期状態 | 未入力の説明用snapshotまたは `None` をB1で確定 | なし |
| 入力選択成功 | 入力済み／未解析状態へ更新 | 破棄 |
| 解析開始 | 旧解析snapshotを保存可能として残さない | 破棄 |
| 解析成功 | 新timing planから再生成 | 破棄 |
| 解析失敗 | B5以降は保持済みfailure DTOを含む保存不可snapshot。B2単体では明示入力されたfailure DTOから生成 | 破棄 |
| cancel | cancel自体はINFO。現行入力契約から保存可否を再評価 | 解析状態が変わる場合は破棄 |
| late result | 一切更新しない | 更新しない |
| 再生位置更新 | live表示部分だけ更新 | 更新しない |
| workspace reset | 初期状態へ戻す | 破棄 |

### Step 7: report契約の確定

初期セクションと順序:

```text
MMD AutoLipTool Diagnostic Report
Generated At

[Input]
[Analysis]
[Generation]
[Saveability]
[Diagnostics]
```

- `<base>`: 入力音声stem
- filename: `<base>_report.txt`
- encoding: UTF-8、BOMなし
- 改行: フォーマッタ内で統一し、プラットフォーム依存の混在を避ける
- 空値: 項目を削除せず `(not available)` または合意した単一表現を使う
- diagnostics: severity順と安定code順を保つ
- `Generated At`: 人間向け情報であり、snapshot fingerprintへ含めない
- `ERROR` があってもreport保存は可能
- RightPane表示文字列をreport元データにしない

### Step 8: B2からB7への引き継ぎ確定

| Block | B1から渡す契約 |
| --- | --- |
| B2 | coreモデル、UI非依存input DTO、failure DTO、builder入出力、diagnostic code、severity、identity context、canonical fingerprint payload |
| B3 | Infoセクションと初期／入力済み／解析済み表示 |
| B4 | 30fps変換、timeline区間判定、live情報のfingerprint除外 |
| B5 | `UiState.current_diagnostic_failure` と現在snapshotのworkspace内保持、analysis callback接続、Warning表示、ERROR禁止、WARNING確認、Yes / No契約、確認済み無効化 |
| B6 | reportセクション、文字コード、空値、安定順、既定名 |
| B7 | B5の保持状態に対するreset、input change、analysis start / success / failure / cancel、parameter change、late resultの横断破棄・回帰、TEXTあり／voice_only回帰 |

### Step 9: B1実施結果の記録

- 確認したファイルと根拠行を記録する。
- 現時点の初期契約から修正した判断がある場合は、理由と反証を記録する。
- 不明点がB2のAPIまたは出力仕様を変える場合は、B1 closeout前にユーザー判断を求める。
- B1で確定できない実装詳細は「B2 Implementation Planで確定」と所有者を明記し、無記名の未確定事項を残さない。

### Step 9.1: B1実施結果（2026-07-14）

#### 9.1.1 実施範囲と変更境界

- 実施ブランチは `feature/MS20-implementation`、開始HEADは `6df0fab`。
- 現行コード、正本文書、指定された既存テストを読み取り照合した。
- production code、GUI、テスト、依存関係、build設定は変更していない。
- B1で変更した成果物は本Implementation Planと、B1完了状態・次作業を伝えるstatus/routing文書だけである。

#### 9.1.2 診断データ参照元の確定

| 診断項目 | 現行コード上の正本 | B2へ渡す契約 |
| --- | --- | --- |
| input mode | `UiState.input_mode`。値は `text_audio` / `voice_only` | snapshot inputへそのまま渡す |
| TEXT | `selected_text_path`、`selected_text_content` | pathは表示名と保存入力identity、contentはvoice_onlyでなくtext_audioの入力状態に使用 |
| 入力音声 | `selected_audio_input`、`selected_wav_path` | source identityは入力音声、writer effective pathは解析用WAVを優先 |
| 解析用WAV | `selected_analysis_wav.analysis_wav_path` | effective WAV pathと表示用解析WAV名を分離して渡す |
| 解析有効性 | `analysis_result_valid`、`analysis_pending_rebuild`、`current_timing_plan` | `analysis_pending_rebuild` は保存禁止ERROR。未解析と再解析待ちを別codeにする |
| timing source | `current_timing_plan.source` | 文字列をそのまま表示正本にせず、安定codeへの変換入力にする |
| anchors | `len(current_timing_plan.anchors)` | timelineと独立した決定的な件数としてanalysis summaryへ渡す |
| events | `len(current_timing_plan.timeline)` | 空timelineは保存禁止ERROR |
| 最大frame | `VowelTimelinePoint` の正規化済み `end_sec` を `round(end_sec * 30)` | `writer.py` の `VMD_FPS = 30` と同じ丸めを使用する |
| timing warning | `current_timing_plan.warning` | 文言をcodeにせず、fallback分類とidentity contextへ変換する |
| observation | `current_timing_plan.observations` | `None` と空listを区別。fallback reasonとwriter参照フィールドを保持する |
| saveability | `UiState.vmd_save_ready` と診断ERRORの両方 | 既存入力契約を満たし、かつ診断ERRORがない場合だけ保存可 |
| failure | `MainFrame._on_analysis_error()` のerrorと `voice_only_errors` のcategory | B2のfailure DTOへ正規化。B5でUiStateへ保持し、B7で破棄回帰を接続する |
| live playback | `UiState.playback_position_sec` | 表示専用。fingerprintとsnapshot同一性から除外する |

#### 9.1.3 severityとdiagnostic codeの確定

既存 `Error_Handling_Specification` の `info / warning / error / fatal / cancelled` は削除せず、MS20表示用の3段階へ次のように正規化する。

| code | 発生条件 | MS20 severity | 保存影響 |
| --- | --- | --- | --- |
| `analysis_not_ready` | 有効なtiming planがなく、再解析待ちでもない初期／未解析状態 | `ERROR` | VMD保存不可 |
| `analysis_rebuild_required` | `analysis_pending_rebuild` がtrue、または入力／parameter変更後 | `ERROR` | VMD保存不可 |
| `timing_plan_empty` | 有効扱いのplanのtimelineが空 | `ERROR` | VMD保存不可 |
| `text_input_missing` | `text_audio` でTEXT pathがない、または保存時に読取可能なTEXT入力契約を満たさない | `ERROR` | VMD保存不可 |
| `voice_only_text_missing` | `voice_only` で解析テキストが空 | `ERROR` | VMD保存不可 |
| `audio_input_missing` | writerへ渡すeffective WAV pathがない、または解析用WAV入力契約を満たさない | `ERROR` | VMD保存不可 |
| `analysis_failure` | retained `DiagnosticFailureInput` がある | `ERROR` | VMD保存不可 |
| `timing_fallback_used` | `source == even_fallback` またはfallback継続を示すtiming warningがある | `WARNING` | VMD保存可。保存前にfingerprint確認 |
| `observation_fallback_used` | observationに `fallback_reason` が1件以上ある | `WARNING` | VMD保存可。保存前にfingerprint確認 |
| `analysis_cancelled` | ユーザーcancelが発生し、cancel以外の保存禁止理由が残っていない | `INFO` | cancelだけを理由に保存可へ倒さない |
| `analysis_ready` | 有効な非空timelineがあり、保存禁止ERRORがない | `INFO` | 現行入力契約を満たせば保存可 |
| `vmd_save_ready` | `UiState.vmd_save_ready` と診断保存条件がともに成立 | `INFO` | 保存可 |

抑制規則:

- `analysis_not_ready` と `analysis_rebuild_required` は同時に出さず、再解析待ちを後者へ優先する。
- 保存禁止ERRORが1件でもある場合、`analysis_ready` と `vmd_save_ready` は生成しない。
- fallback warningは複数の原因を同一codeへ潰さず、`identity_context` 内に対象event indexとreasonの安定順tupleを残す。
- `cancelled` は常に現在入力状態とplanを再評価し、保存禁止理由がある場合は別ERRORを残す。

#### 9.1.4 fingerprintとreportの確定

- fingerprintのcanonical payloadは、schema version、input mode、正規化path、正規化済みtimeline全field、`None`／空listを区別したobservations全field、writer parameter、diagnostic identityを含む。
- timelineは `time_sec / vowel / value / duration_sec / start_sec / end_sec / peak_value` をevent順に含む。
- observationsは `PeakValueObservation` とnested `PeakValueEvaluation` の全field、RMS系列、candidate flag、前後index、span indexを含む。writerがbridge／peak-end shapeで参照するため、timelineだけを正本にしない。
- diagnostic identityは `(severity, code, phase, identity_context)` の安定順であり、`summary`、`detail`、exception message、UI文言を含めない。
- 再生秒、frame、現在母音、RightPane tab／scroll、status bar、report保存先、VMD保存先、dialog開閉はfingerprintから除外する。
- reportは `MMD AutoLipTool Diagnostic Report`、`Generated At`、`[Input]`、`[Analysis]`、`[Generation]`、`[Saveability]`、`[Diagnostics]` の順、UTF-8 BOMなし、改行LF、空値 `(not available)` とする。`Generated At` はreport表示だけに使用し、fingerprintには入れない。

#### 9.1.5 failure保持とBlock所有権の確定

| Block | 確定責務 |
| --- | --- |
| B2 | UI非依存 `DiagnosticFailureInput` とsnapshot builder。UiState／wxPython／callbackを参照しない |
| B3 / B4 | failureを独自保持せず、snapshotのInfo／live表示だけを接続 |
| B5 | `UiState.current_diagnostic_failure` のworkspace内保持、analysis error callbackからの設定、解析開始／成功時clear、Warning／save policy接続 |
| B6 | 同一snapshotからのreport formatting／保存 |
| B7 | input変更、parameter変更、cancel、workspace reset、analysis／audio job ID不一致late callbackのfailure・snapshot・確認済みfingerprint破棄回帰 |

#### 9.1.6 B2開始条件

- B1の参照元、severity、diagnostic code、fingerprint、report、failure所有権は確定した。
- B2では `src/core/output_diagnostics.py` と対応coreテストを新規作成する。正式APIはB2 Implementation Planで固定する。
- B2は既存pipelineのtiming／VMD形状アルゴリズム、固定モーフ `あ / い / う / え / お`、GUI表示、外部通信を変更しない。
- B2開始前に残るのは実装API・hash algorithm・テストfixtureの具体化だけであり、B1の契約不明点ではない。

## 10. 状態遷移 / データ契約

### 10.1 B2用snapshot境界

B1では実装しないが、B2の入出力契約を次の粒度で固定する。

```text
DiagnosticSnapshotInput (core / immutable)
  - input identity / mode
  - analysis validity / pending rebuild
  - current timing plan
  - output-affecting parameters
  - DiagnosticFailureInput, optional

          ↓ deterministic builder

OutputDiagnosticsSnapshot
  - input summary
  - analysis summary
  - generation summary
  - saveability
  - ordered diagnostic items
  - save-state fingerprint
```

- builderはwxPythonに依存しない。
- builderとcore DTOは `UiState`、`MainFrame`、`AppController` をimportしない。GUI層が現在状態から `DiagnosticSnapshotInput` を組み立てる。
- builderはダイアログを開かない。
- builderはファイルを書き込まない。
- builderはtiming planや `UiState` を変更しない。
- 同じ入力内容から同じ診断順とfingerprintを返す。

failure責務は次のように分離する。

| Block | 責務 |
| --- | --- |
| B2 | UI非依存の `DiagnosticFailureInput` と、それを受け取るbuilderを実装・単体テストする。UiStateやcallbackは変更しない |
| B3 / B4 | failureなしを含むsnapshotのInfo / live表示を接続する。failure保持の責務は持たない |
| B5 | `UiState.current_diagnostic_failure` をworkspace内状態として追加し、現在analysis jobのerror callbackだけが分類済みfailure DTOを設定する。解析開始・成功時のclearとWarning / save policyへの接続もここで行う |
| B7 | input変更、parameter変更、cancel、workspace reset、audio / analysis job ID不一致のlate callbackを含む全破棄規則を回帰テストする |

- `DiagnosticFailureInput` は最低限 `code`、正規化前severity、`phase`、`recoverability`、安定した構造値を持つ。exception instanceや表示済みmessageそのものを保持しない。
- B5より前のB2単体テストはfailure DTOを明示引数で渡してfailure snapshotを検証する。現行GUIが解析失敗を保持していると仮定しない。
- late callbackはfailure、snapshot、確認済みfingerprintのいずれも更新しない。

### 10.2 保存判定

```text
diagnostic itemsにERRORあり
  → VMD保存不可

ERRORなし、WARNINGあり
  → VMD保存可
  → 未確認fingerprintならYes / No確認
  → Yesのみ確認済みとして保存継続

ERROR / WARNINGなし
  → 現行VMD保存契約が成立すれば保存可
```

MS20のseverityは現行 `vmd_save_ready` の代替ではない。現行契約と診断policyの両方を満たす場合だけ保存可能とする。

### 10.3 データ保持期間

- 解析snapshotと確認済みfingerprintはworkspace内だけで保持する。
- アプリ終了後へ永続化しない。
- reportは明示的に保存された出力ファイルであり、workspace内snapshotとは別である。

## 11. テスト方針

B1は読み取り監査Blockであり、テストコードを追加・変更しない。

### 11.1 読み取り検証

- `rg`でdata class、property、callback、reset、save入口を特定する。
- 必要範囲だけを `Get-Content` で読む。
- 既存テストの期待値を読み、計画が既存契約を破壊しないか確認する。
- ドキュメント内のフィールド名・パスが現行リポジトリと一致するか確認する。

### 11.2 自動テスト

原則として実行しない。B1実施中に現行期待値の確認が必要になった場合は、次の最小テストを読み取り確認または非変更実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b3_right_pane.py
```

実行した場合は、表示上のpass数とprocess exit codeを分けて記録する。

### 11.3 手動・build確認

- 手動GUI確認: 実施しない
- 実MMD確認: 実施しない
- build / SmokeLaunch: 実施しない

### 11.4 B2へ渡すfingerprint / failure単体テスト境界

B1では追加しないが、B2 Implementation Planは少なくとも次をcore単体テストとして具体化する。

- 同一の `DiagnosticSnapshotInput` から同一canonical payloadと同一fingerprintが得られる。
- timelineの `start_sec`、`end_sec`、`peak_value` のいずれかが変わるとfingerprintが変わる。
- observationのRMS系列、candidate flag、前後index、span indexのいずれかが変わるとfingerprintが変わる。
- `closing_hold_frames`、`closing_softness_frames`、model nameのいずれかが変わるとfingerprintが変わる。
- diagnosticの `identity_context` が変わるとfingerprintが変わる。
- `summary` / `detail` の翻訳・表現だけが変わってもfingerprintは変わらない。
- 再生位置、現在frame、現在母音だけが変わってもfingerprintは変わらない。
- `DiagnosticFailureInput` を明示入力すると対応する保存不可snapshotを生成でき、coreテストにwxPython、`UiState`、`MainFrame`を必要としない。
- `None` observationsと空observationsは別canonical payloadになる。
- NaN / infinityを含むwriter入力を通常fingerprintとして受理せず、保存入力不成立として扱う。

## 12. 受け入れ条件

- 全診断項目の現行参照元、型、空値、生存期間が記録されている。
- 直接取得可能、決定的導出可能、現行未保持が区別されている。
- 既存severityからMS20診断severityへの対応が固定されている。
- diagnostic codeと発生条件、severity、保存影響が固定されている。
- fingerprintの入力、除外、無効化トリガーが固定されている。
- canonical timeline、canonical observations、closing parameter、diagnostic identity contextがfingerprint入力として固定されている。
- `summary` / `detail`、exception message、object reprがfingerprintから除外されている。
- failure DTO定義、B2のUI非依存builder、B5のUiState保持・callback接続、B7の横断破棄責務が分離されている。
- 再生位置がfingerprintに含まれない。
- reportのセクション、順序、空値、UTF-8、既定名が固定されている。
- B2からB7の所有権と引き継ぎ契約が明記されている。
- production code、GUI、テスト、build設定が変更されていない。
- B2開始前に解消が必要な不明点が無記名で残っていない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| Block Breakdownの初期仮定を現行実装より優先する | 各契約を実フィールド・callback・テストへ再対応付けする |
| `VowelTimingPlan.warning` の文言をdiagnostic codeとして使う | 文言と安定codeを分離する契約をB2へ渡す |
| 未解析と解析失敗を同じERRORに集約し、復帰方法を失う | diagnostic codeを分け、表示文言とrecoverabilityを別属性とする |
| `cancelled -> INFO` で保存禁止理由まで消える | cancel以外の現行状態を再評価し、必要なERRORを別途生成する |
| object identityやメッセージ文言がfingerprintを不安定にする | 決定的な値と安定codeのみを使う |
| timelineだけをfingerprint化し、observationsやclosing parameterが変化してもWARNING確認を再利用する | canonical writer inputとしてtimeline、observations、closing parameterを明示的に正規化する |
| 同じdiagnostic codeで対象eventやfallback理由が変化しても同一診断扱いになる | 表示文言と分離した `identity_context` をdiagnostic identityへ含める |
| B2が現行UiStateに存在しないfailure保持を前提にGUI層へ依存する | B2はfailure DTOとpure builder、B5はUiState保持とcallback接続、B7は横断破棄回帰を所有する |
| 再生timer更新のたびにWARNING確認が復活する | 再生位置・frame・母音をfingerprintから除外する |
| B1でB2の実装まで開始する | 差分監査でproduction code・テスト変更がないことを受け入れ条件にする |
| 将来MS用の汎用拡張を先行設計する | MS20で必要な項目と後続Blockの具体的な入力に限定する |

## 14. Codex 実装時の注意

```text
- 本Blockは調査・契約固定のみとし、production codeとテストを変更しない。
- コマンドは一つずつ実行し、並列・パイプ・連結実行をしない。
- MS20 roadmap、Block Breakdown、過去履歴を無条件に正しいと仮定せず、現行コードとテストへ再対応付けする。
- 確認できた事実、推論、未確定を区別する。
- UI表示文字列、exception message、object reprを安定codeやfingerprintの正本にしない。
- timelineだけをfingerprintの正本にせず、observationsとclosing parameterを含むcanonical writer inputを使う。
- diagnostic identityは `severity / code / phase / identity_context` で構成し、summary / detailは含めない。
- B2 coreからUiStateを参照せず、GUI層がUI非依存input DTOを組み立てる。
- 再生位置・frame・母音をsave-state fingerprintに含めない。
- `ERROR`時のVMD保存禁止をUIボタンだけではなくcontroller入口でも後続実装する契約とする。
- MS19のTEXTあり / voice_only、reset、late callback破棄契約を壊さない。
- Qt / PySide6 GUIを復活させない。
- コードとテストの差分が発生した場合はB1の範囲逸脱として停止する。
- 実行していないテストや手動確認を通過と報告しない。
```

B1完了報告は、次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 調査・契約固定内容
4. 実行したテスト
5. テスト結果
6. 仕様からの逸脱
7. 残課題
```
