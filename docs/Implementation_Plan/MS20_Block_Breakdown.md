# MS20 Block Breakdown

## 1. 文書情報

- 文書名: MS20 Block Breakdown
- 配置: `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 対象マイルストーン: MS20
- 基準ブランチ: `feature/MS20-implementation`
- B8実施基準コミット: `41af559 Plan MS20-B8 closeout`
- 作成日: 2026-07-13
- 最終更新日: 2026-07-20
- 文書ステータス: MS20 CloseOut Completed / A
- 上位正本:
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
- 関連仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

本書はMS20内の責務と実装順を定める。各Blockの実装前には個別の `MS20-Bx_Implementation_Plan.md` を作成し、本書だけを直接の実装指示としない。

MS20-B1は2026-07-14に、production code・GUI・テストを変更せず、診断参照元、severity、diagnostic code、canonical fingerprint、report、failure保持の責務境界を固定した。MS20-B2は2026-07-15にコミット `b6f4254` で実装済みである。MS20-B3は2026-07-16にコミット `c40162d` でRightPane Info表示を実装し、自動テストとユーザー手動GUI確認を完了した。同日、B4 Implementation Plan、pre-implementation check、production実装、自動検証、ユーザーGUI確認まで完了した。MS20-B5は2026-07-17にproduction実装、自動検証、ユーザーGUI確認13項目まで完了した。MS20-B6は2026-07-18にproduction実装、自動検証、ユーザーGUI確認14項目まで完了した。MS20-B7は2026-07-19にproduction実装、自動検証、ユーザー手動GUI確認まで完了した。2026-07-20にB8 Closeout監査を実施し、P1 / P2 / P3なし、A判定とした。同日にB8ユーザーチェックも通過・問題なしと報告され、MS20をCloseOutした。次はMS21 Implementation Plan策定である。

## 2. 背景

MS19 closeout時点で、TEXTあり／voice_onlyの解析、Preview、再生、VMD保存、MMD用WAV出力、新規作業resetは成立していた。MS20-B2 / B3により構造化diagnostics coreとRightPane Infoの静的4セクション表示、MS20-B4によりlive playback context、MS20-B5によりWarning全severity表示とseverity連動保存policy、MS20-B6によりdiagnostic report保存を実装済みである。

現行実装の主な基盤は次のとおりである。

- `src/core/pipeline.py`
  - `VowelTimingPlan`、`PipelineResult`、`VmdGenerationResult` がtimeline、anchor、timing source、warningを保持する。
- `src/gui_wx/ui_state.py`
  - `current_timing_plan`、解析有効性、VMD保存可否、再生位置を保持する。
- `src/gui_wx/right_pane.py`
  - InfoはB2 snapshotによる入力・解析・生成・保存可否、縦scroll、再解析attention表示を実装済みである。WarningはB5で全severity表示を実装済みであり、後続タブは未実装の受け口である。
- `src/gui_wx/app_controller.py`
  - VMD保存と再生位置更新の入口を持つ。
- `src/gui_wx/main_frame.py`
  - RightPane、VMD保存導線、workspace reset時の表示初期化を統合する。

MS20では、表示文字列を正本にせず、coreの構造化診断snapshotをInfo、Warning、保存判定、reportの共通入力とする。

## 3. 目的

MS20の目的は、後続のイベント編集、preset、model profile、Whisper model選択、一括出力が共通利用できる情報・警告・出力診断基盤を完成させることである。

- Infoに入力・解析・生成概要を表示する。
- 再生中の位置、現在frame、現在母音をInfoへ反映する。
- Warningに `INFO / WARNING / ERROR` の構造化診断を表示する。
- `ERROR` 時はVMD保存不可、`WARNING` 時は同一保存状態につき一度だけ確認する。
- 専用操作からUTF-8の `<base>_report.txt` を安全に出力する。

## 4. In Scope

- 構造化診断モデルとsnapshot builder
- `INFO / WARNING / ERROR` のseverity契約
- input / analysis / generation / saveabilityの要約
- timing source、anchor数、fallback / warning、イベント数、最大frame
- RightPane Info / Warningの本実装とスクロール表示
- 再生位置、現在frame、現在母音の反映
- VMD保存前のseverity判定
- WARNING確認の同一状態判定と確認済み管理
- `<base>_report.txt` の専用保存導線
- 新規作業、入力変更、再解析、解析失敗、late result破棄の状態契約
- TEXTあり／voice_onlyの回帰テスト
- 関連仕様・ユーザー文書の同期

## 5. Out of Scope

- 発音イベントの選択・補正・母音変更
- Undo / Redoとadjustment layer
- 長音 `hold / decay`、生成preset、model profile
- Whisper model選択・download・削除
- VMD / MMD用WAV / reportの一括出力
- session保存・再読込
- VMD読み戻し、任意keyframe編集
- VMD writerの形状生成アルゴリズム変更
- 新規外部依存関係
- package / release / tag / push
- Qt / PySide6 GUIの復活

## 6. MS20共通設計契約

### 6.1 診断の正本

診断の正本は、MS20-B2で実装したUI非依存coreモデル `src/core/output_diagnostics.py` とする。公開APIと契約はMS20-B1 / B2 Implementation Planおよび現行実装に従う。

実装済み構造の概要:

```text
DiagnosticSeverity
  INFO
  WARNING
  ERROR

DiagnosticItem
  code
  severity
  summary
  detail
  phase

OutputDiagnosticsSnapshot
  input_summary
  analysis_summary
  generation_summary
  saveability
  items
  save_state_fingerprint
```

- UI文字列、ダイアログ、reportテキストを正本にしない。
- snapshotは現在の `UiState`、timing plan、解析結果から生成し、RightPaneが独自に解析結果を推測しない。
- 既存 `Error_Handling_Specification` の `fatal` は出力診断上 `ERROR`、`cancelled` は保存を禁止する失敗が残らない限り `INFO` へ正規化する。既存エラーモデル自体の値は削除しない。
- 不明な状態を安易に `INFO` へ降格させず、保存入力契約を満たさない場合は `ERROR` とする。

### 6.2 Info表示

Infoは少なくとも次を表示する。

- input mode: `text_audio` / `voice_only`
- TEXT・入力音声・解析用WAVの有無と表示用名
- 解析有効性とtiming source
- anchor数、発音イベント数、最大frame
- fallbackの有無
- VMD保存可否と禁止理由
- 再生位置（秒）、現在frame、現在母音

再生位置は表示用情報であり、解析snapshotの同一性判定に使用しない。frameは現行VMD契約の30fpsと同じ変換を使い、独自の丸め規則を追加しない。現在母音は `current_timing_plan.timeline` の有効区間から求め、区間外は「なし」とする。

### 6.3 Warning表示と保存ポリシー

- 表示順は `ERROR`、`WARNING`、`INFO` の順とし、同一severity内はbuilderの安定順を保つ。
- 各項目は安定した `code` を持ち、表示文言を同一性判定に使わない。
- `ERROR` が1件以上ある場合はVMD保存ボタン／メニューを無効とし、controller入口でも拒否する。
- `WARNING` だけでは保存ボタンを無効にしない。保存直前にYes / No確認する。
- Yes時だけ現在fingerprintを確認済みとする。Noまたはダイアログclose時は保存せず、確認済みにしない。
- 確認済みfingerprintで再度保存する場合は再確認しない。

`save_state_fingerprint` には、少なくとも次を含める。

- 入力identityまたは解析job / result generation
- timing planの内容同一性
- VMD出力に影響する現行parameter
- severityとdiagnostic codeの安定リスト

次はfingerprintから除外する。

- 再生位置、現在frame、現在母音
- RightPaneの選択タブ、scroll位置
- status barの一時文言
- report保存先

### 6.4 report出力

- 専用導線は `ファイル > 診断レポート保存...` を第一候補とする。現行ツールバーに新規ボタンを追加しない。
- `<base>` は現在の入力音声stemとする。有効な入力音声がない状態ではreport保存を有効にしない。
- 既定名は `<base>_report.txt` とする。
- 文字コードはUTF-8（BOMなし）とする。
- reportは構造化snapshotから決定的に生成し、RightPaneの表示文字列を読み戻さない。
- 一時ファイルへの書き込みと検証後の確定を基本とし、失敗時に不完全な出力を残さない。
- reportは `ERROR` を含むsnapshotでも保存可能とする。VMD保存可否とreport保存可否を混同しない。

### 6.5 状態破棄

- 入力変更、再解析開始、パラメータ変更、新規作業で、旧snapshotとWARNING確認済みfingerprintを無効化する。
- 解析失敗は失敗内容を持つ新snapshotへ更新し、旧解析結果を保存可能として残さない。
- cancelはBusyを解除し、旧結果を再利用できない契約であれば現在snapshotを更新する。
- job id不一致のlate resultは `UiState`、snapshot、RightPane、確認済みfingerprintのいずれも更新しない。
- workspace reset後はInfo / Warningを初期表示へ戻し、report保存を無効にする。

## 7. Block一覧

```text
MS20-B1: Diagnostics Contract / Current-State Pre-check
MS20-B2: Structured Diagnostics Core Foundation
MS20-B3: RightPane Analysis Information
MS20-B4: Live Playback Context
MS20-B5: Warning Panel / VMD Save Policy
MS20-B6: Diagnostic Report Export
MS20-B7: State Integration / Regression / Docs
MS20-B8: MS20 Closeout
```

## 8. Block依存関係

```text
MS20-B1
  ↓
MS20-B2
  ↓
MS20-B3
  ↓
MS20-B4
  ↓
MS20-B5
  ↓
MS20-B6
  ↓
MS20-B7
  ↓
MS20-B8
```

B1で既存仕様と現行実装の衝突、severity正規化、fingerprint、report契約を確定するまでproduction codeを変更しない。B2でUI非依存の診断snapshotを成立させ、B3以降がそれを共通利用する。

B4の再生位置更新はB3のInfo表示基盤に依存する。B5の保存ポリシーはB2のseverity / fingerprintとB3の表示反映を前提とする。B6はB2の同一snapshotを文字列化し、B7でreset・失敗・late resultを含む横断回帰を固定する。

## 9. MS20-B1: Diagnostics Contract / Current-State Pre-check

### 9.1 目的

production code変更前に、診断項目、severity変換、VMD保存可否、WARNING同一状態、report出力の契約を現行コードと照合して固定する。

### 9.2 In Scope

- `PipelineResult`、`VowelTimingPlan`、`UiState`、`AnalysisWorkerResult`の利用可能データ監査
- 既存error severityとMS20出力診断severityの対応表
- 全diagnostic codeと発生条件の初期一覧
- save-state fingerprintの構成要素と無効化トリガー
- reportのセクション、表示順、未設定値の表現
- B2からB7の対象ファイルとテスト分割

### 9.3 Out of Scope

- production code変更
- GUI変更
- 新規テスト追加
- 仕様にないseverityや保存導線の追加

### 9.4 主な成果物

- `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
- 診断項目／severity対応表
- fingerprint・report・状態破棄契約
- B2の実装対象と受け入れ条件

### 9.5 受け入れ条件

- 診断の参照元が現行コード上で特定されている。
- `ERROR`、`WARNING`、`INFO` の判定が表示文字列に依存しない。
- 再生位置をfingerprintから除外する理由が明記されている。
- production codeとテストを変更していない。

## 10. MS20-B2: Structured Diagnostics Core Foundation

### 10.1 目的

Info、Warning、保存policy、reportが共通利用するUI非依存の構造化診断snapshotを実装する。

### 10.2 In Scope

- severity、diagnostic item、summary、snapshotの不変データモデル
- writer保存実体と共用するtiming plan正規化境界
- 正規化済みtiming plan / pipeline result / input stateからのsnapshot builder
- event数、anchor数、timing source、fallback、最大frameの決定的導出
- VMD保存可否と理由
- save-state fingerprint生成
- core単体テスト

### 10.3 Out of Scope

- wxPython表示
- VMD保存ダイアログ
- reportファイル書き込み
- pipeline品質アルゴリズム変更

### 10.4 実装済み成果物

- `src/core/output_diagnostics.py`
- `src/core/pipeline.py` の既存保存前正規化helper抽出
- `src/core/__init__.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`

### 10.5 受け入れ条件

- wx importなしでsnapshotを生成できる。
- 同一入力と設定から同一diagnostic code順・同一fingerprintが得られる。
- 非正durationを含むplanでも、writer実入力とfingerprint対象が一致する。
- 再生位置だけの変更でfingerprintが変わらない。
- 保存契約不成立時は `ERROR`、fallback継続時は `WARNING` になる。
- 既存pipelineとVMD writerの出力を変更しない。

### 10.6 実施結果

- 2026-07-15にコミット `b6f4254` でUI非依存diagnostics core、canonical fingerprint、writer timing plan共有helper、core testを実装した。
- B2単体12件、非正duration回帰1件、限定回帰24件はpass表示・process exit code 0だった。
- 全体380件はpass表示まで完走し、既知wx終了処理由来のprocess exit code 1を別記録した。
- GUI、UiState、Warning、save policy、report、依存関係、packageは変更していない。

## 11. MS20-B3: RightPane Analysis Information

### 11.1 目的

RightPane Infoのプレースホルダーを、B2のsnapshotから生成する入力・解析・生成・保存概要表示へ置き換える。

### 11.2 In Scope

- Infoタブのスクロール可能表示
- snapshotからのセクション表示
- TEXTあり／voice_only、未解析／解析済み、保存可／不可の表示
- analysis成功、入力変更、再解析開始時の表示更新
- RightPane表示テスト

### 11.3 Out of Scope

- 再生中の秒・frame・母音更新
- Warningのseverity別表示
- 選択イベント、preset、model profileタブの本実装

### 11.4 実装済み成果物

- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/theme.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- production `VowelTimingPlan` 契約へ補正した既存GUI fixture
- `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`

### 11.5 受け入れ条件

- Infoにinput / analysis / generation / saveabilityの概要が表示される。
- 長い値を表示してもRightPane全体のレイアウトを押し広げない。
- 未解析と解析済みを同じ表示にしない。
- 表示文字列からsnapshotやtiming planを復元しない。

### 11.6 実施結果

- B3 adapter単体12件、B3 RightPaneとMS16 RightPane回帰16件、workspace reset回帰8件はpass表示・終了コード0だった。
- 指定限定回帰56件と全体406件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- ユーザー手動GUI確認10項目はすべて通過し、問題なしと報告された。確認後の微修正で「再解析が必要」の文字列だけをボールド＋theme別オレンジ系文字色にし、微修正後のユーザーチェックも通過・問題なしと報告された。
- Warning、failure保持、save policy、live playback、reportは後続Blockへ残した。

## 12. MS20-B4: Live Playback Context

### 12.1 目的

既存再生timerの更新に合わせ、Infoへ再生位置、現在frame、現在母音を即時反映する。

### 12.2 In Scope

- `playback_position_sec` からの表示用frame計算
- timing planからの現在母音解決
- RightPane単体構築／`clear_info()` 後のB3空表示契約と、MainFrame初回同期後のdefault `[再生]` 表示の両立
- play / timer update / stop / finish / playback failure / resetの表示更新
- 再生timerごとのsnapshot再構築を避ける軽量更新
- 境界時刻、timeline区間外、非有限位置、停止後遅延callbackのテスト

### 12.3 Out of Scope

- 再生engineとMCI制御の変更
- Pause UI / pause state / seek / loopの追加
- Previewのカーソル動作変更
- イベント選択・編集

### 12.4 主な成果物

- 新規 `src/gui_wx/playback_context.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- 新規 `tests/test_ms20_b4_playback_context.py`
- `docs/Implementation_Plan/MS20-B4_Implementation_Plan.md`

### 12.5 受け入れ条件

- 再生位置の変化がInfoの秒・frame・母音へ反映される。
- stop / finish / workspace reset後は初期表示へ戻る。
- timelineのギャップや区間外で直前の母音を誤表示しない。
- 非有限位置で0秒eventを現在母音として誤表示しない。
- RightPane単体構築／`clear_info()` 直後は空表示で、MainFrame初回同期後はdefault `[再生]` を表示する。
- 再生更新でWARNING確認済みfingerprintが変化しない。
- timer更新でB2 snapshot builderとB3 formatterを呼ばない。

### 12.6 実装前チェック結果

- 2026-07-16に現行callback順序、RightPane widget / helper契約、UiState、timing plan、既存playback / reset / B3 Info testを照合した。
- P1なし、P2 1件、P3 2件を検出し、MS20-B4 Implementation Plan内で解消した。
- 現行前提の限定回帰は34件と21件の2段階で全件pass表示、process exit code 0だった。
- この実装前チェック時点ではproduction codeとtestは未変更・未実装だった。実装結果は12.7へ記録する。

### 12.7 実装・自動検証結果

- 2026-07-16にwx非依存playback context、RightPaneの独立 `[再生]` label、MainFrame軽量同期を実装した。
- static Info / fingerprint分離、半開区間、gap、overlap、0長event、invalid値、playback lifecycle、停止後遅延callback、theme追従を自動testへ固定した。
- B4新規24件、関連回帰28件・29件・8件は全件pass表示、process exit code 0だった。
- 全体430件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- MCI、Pause、Preview cursor、Warning、save policy、report、依存関係、packageは変更していない。
- 2026-07-16にユーザーからGUI確認完了・問題なしと報告され、B4は完了した。

## 13. MS20-B5: Warning Panel / VMD Save Policy

### 13.1 目的

B2の構造化診断をWarningタブとVMD保存前policyへ接続する。

### 13.2 In Scope

- Warningタブのスクロール可能表示
- severity別のラベル、順序、視認性
- snapshot生成前のinput mode再判定と、同一snapshotによるInfo / Warning / action state同期
- `ERROR` 存在時の保存UI無効化とcontrollerガード
- `WARNING` 存在時のYes / No確認
- 確認済みfingerprintの保持と無効化
- B5で追加するfailure、current snapshot、確認済みfingerprintの既存invalidation / reset経路における最小clear
- VMD保存失敗時の現行解析結果保持

### 13.3 Out of Scope

- 診断項目の手動非表示設定
- 警告をユーザー設定で恒久的に無視する機能
- MMD用WAV保存policyの変更
- reportファイル出力

### 13.4 主な成果物候補

- `src/core/output_diagnostics.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/theme.py`
- 新規 `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_pipeline_and_vmd.py`
- `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md`

### 13.5 受け入れ条件

- `ERROR` がある間はボタン／メニューとcontrollerのどちらからもVMD保存できない。
- `WARNING` のYes確認後は同一fingerprintで再確認しない。
- No / close時は保存せず、次回試行時に再確認する。
- 解析や出力parameterが変わった場合は確認済み状態を引き継がない。
- フォールバック警告が表示だけで失われずreport用snapshotに残る。

### 13.6 計画・実装前チェック結果

- 2026-07-16に `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md` を作成した。
- Warningタブは `INFO / WARNING / ERROR` の全diagnostic itemを表示し、severity別label、theme追従、縦scrollを実装対象とする。
- VMD保存policyは最新snapshotをbutton / menuとcontroller guardへ接続し、ERROR禁止とWARNINGの同一fingerprint一回確認を行う。
- analysis failureはUI非依存DTOとしてworkspace内に保持し、exception messageをfingerprint identityへ含めない。
- 初回実装前チェックでP1なし、P2 2件、P3 1件を検出し、input mode再判定順序、B5基本clearとB7横断監査の責務境界、成果物候補一覧を補正した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。限定回帰は24件、47件、28件＋subtest 7件がpass表示・終了コード0だった。
- 実装前チェック完了時点ではproduction codeとtest codeは未変更・未実装だった。
- 2026-07-17にP2 / P3再補正後、workspace diagnostics state、failure adapter、snapshot共有、Warning全severity表示、severity連動VMD保存policyを実装した。
- B5 / theme限定17件、diagnostics / RightPane限定64件、state / save / failure限定35件＋subtest 7件、pipeline / VMD 12件はpass表示・終了コード0だった。全体442件＋subtest 7件はpass表示、failure / error表示なし、既知wx終了処理由来の終了コード1だった。
- 2026-07-17にユーザーGUI確認13項目がすべて通過し、問題なしと報告された。B5はproduction実装、自動検証、ユーザーGUI確認まで完了した。

## 14. MS20-B6: Diagnostic Report Export

### 14.1 目的

B2の構造化snapshotを、専用保存操作からUTF-8の `<base>_report.txt` として出力する。

### 14.2 In Scope

- reportの決定的フォーマッタ
- input / analysis / generation / saveability / diagnosticsセクション
- `ファイル > 診断レポート保存...` 導線
- `<base>_report.txt` の既定名
- UTF-8 BOMなし出力
- 上書き確認、キャンセル、一時ファイル、失敗時cleanup
- `ERROR` を含むsnapshotのreport保存

### 14.3 Out of Scope

- JSON / CSV / HTML report
- reportの自動出力
- VMD保存操作へのreport自動同梱
- MMD用一括出力directory

### 14.4 主な成果物候補

- `src/core/output_diagnostics.py`
- 新規 `src/core/diagnostic_report.py`（分離が必要な場合）
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- 新規 `tests/test_ms20_b6_diagnostic_report.py`
- 新規 `tests/test_ms20_b6_report_save_flow.py`
- `docs/Implementation_Plan/MS20-B6_Implementation_Plan.md`

### 14.5 受け入れ条件

- 現在snapshotから `<base>_report.txt` をUTF-8 BOMなしで出力できる。
- RightPaneの表示文字列をreport入力に使わない。
- 上書き拒否とキャンセル時に既存ファイルを変更しない。
- 書き込み失敗時に不完全な確定出力を残さない。
- VMD保存不可の `ERROR` があってもreportを保存できる。

### 14.6 計画作成結果

- 2026-07-17に `docs/Implementation_Plan/MS20-B6_Implementation_Plan.md` を作成した。
- UI非依存formatter、timezone付きGenerated At、固定section / field順、LF、UTF-8 BOMなし、diagnostic item形式を固定した。
- source audio stem由来の既定名、File menu専用導線、ERROR時も許可するreport固有save guardを固定した。
- same-directory temporary file、byte検証、`os.replace()`、failure cleanup、既存target保持を固定した。
- report保存先履歴、toolbar button、VMD自動同梱、B7横断closeoutはB6対象外とした。
- production code、GUI、test code、dependency、build設定は変更していない。

### 14.7 実装前チェック結果

- 2026-07-17の初回チェックでP1なし、P2 2件、P3なしを検出した。
- normalized snapshot path由来の既定名で元音声stemの大小文字を失う問題は、元source audio pathとsnapshot正規化pathの責務を分離し、adapter resolverをsnapshot builder、menu、controllerで共有する契約へ補正した。
- Windowsでtemporary handleを開いたままreadback / replaceし得る問題は、write handle close、別handle readback、readback handle close、`os.replace()` の順序へ補正した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。
- MS20 diagnostics回帰50件、state / export / reset回帰28件＋subtest 7件、既存output dialog回帰6件、pipeline / VMD回帰12件はpass表示・終了コード0だった。
- 実装前チェック時点で、MS20-B6は実装着手可能と判定した。

### 14.8 実装・自動検証結果

- 2026-07-18に `src/core/diagnostic_report.py`、共有source audio path resolver、File menu、dialog、AppController report保存flowを実装した。
- reportは固定5 section、timezone付きGenerated At、LF、UTF-8 BOMなし、全diagnostic item、source audio stem由来の既定名を持つ。
- report保存はVMD保存policyと独立し、ERROR snapshotでも許可する。Busy／入力なし／reset後はUIとcontrollerでfail closedとする。
- same-directory temporary write、byte検証、全handle close後の `os.replace()`、failure cleanupにより既存targetを保護する。
- B6 core 13件、B6 GUI flow 10件、指定回帰96件＋subtest 7件はpass表示・終了コード0だった。
- 全体465件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。compileallと `git diff --check` は終了コード0だった。
- dependency、package、license、Qt、network、固定モーフは変更していない。
- 2026-07-18にユーザーから、手動GUI確認14項目はすべて通過し、問題なしと報告された。
- B6はproduction実装、自動検証、ユーザーGUI確認まで完了した。B7 Implementation Planは15.6のとおり作成済みである。

## 15. MS20-B7: State Integration / Regression / Docs

### 15.1 目的

B2からB6の成果について、B5で追加した基本clearを含む既存の入力・解析・reset・worker状態への統合を横断監査し、古い診断や確認済み状態が次作業へ残らないことを回帰テストと文書で固定する。

### 15.2 In Scope

- 新規作業、TEXT／音声変更、再解析、parameter変更のsnapshot無効化
- 解析失敗・cancel・VMD保存失敗の復帰
- analysis job id不一致時のlate result破棄
- B5の基本clearが全input / parameter / reset入口から到達することの確認と、欠落時の限定補修
- TEXTあり／voice_onlyの回帰
- Info / Warning / Preview / VMD保存状態の整合
- README、配布用readme、関連仕様の実到達状態同期
- MS20対象テストと比例した回帰テスト

### 15.3 Out of Scope

- package build / SmokeLaunch
- 実MMD受け入れ（MS26）
- release readiness（MS27）
- MS21以降の機能先行実装

### 15.4 主な成果物候補

- `src/gui_wx/ui_state.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- 新規 `tests/test_ms20_b7_diagnostics_state_integration.py`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS20-B7_Implementation_Plan.md`

### 15.5 受け入れ条件

- reset後に前作業のInfo、Warning、report、WARNING確認済み状態を使用できない。
- late resultが現在snapshotとRightPaneを上書きしない。
- 解析失敗後に旧解析結果をVMD保存できない。
- VMD保存失敗だけで有効な解析snapshotを破棄しない。
- TEXTあり／voice_onlyの既存導線が維持される。
- 文書が実装済みと計画中を混同しない。

### 15.6 計画作成結果

- 2026-07-18に `docs/Implementation_Plan/MS20-B7_Implementation_Plan.md` を作成した。
- B1のB7所有権、B5 / B6 diagnostics state、UiState、MainFrame、AppController、analysis / audio job ID、既存test、README、配布用readme、3正本仕様を照合した。
- parameter変更時の旧failure／snapshot／confirmation clearと、core `analysis_cancelled` INFOのUiState / adapter接続を限定補修候補として固定した。
- input / parameter / analysis / cancel / late callback / reset / VMD・report保存失敗のclear・rebuild・retain matrixを固定した。
- README、`readme_mmdautolip.txt`、Pipeline / GUI / Error仕様をMS20-B6完了状態へ同期し、B8 closeoutは先行しない。
- 計画作成baselineの関連48件＋subtest 7件はpass表示・終了コード0だった。
- 計画作成時点ではproduction code、test code、README、仕様本文、dependency、build設定を変更しておらず、次工程をB7実装前チェックとしていた。

### 15.7 実装前チェック結果

- 2026-07-18の初回チェックではP1なし、P2 2件、P3 1件を検出した。
- input failure契約をdialog cancel、TEXT commit前失敗、音声選択確定後失敗へ分離し、音声probe／変換失敗では旧workspaceを復元しない現行契約を固定した。
- analysis cancelは要求callbackで確定せず、current jobのterminal success / error callbackだけがcancel状態設定、Busy解除、snapshot再構築を行う契約へ補正した。
- audio worker state / Busy actionの既存2 test fileを指定回帰へ追加した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。
- P3で指定回帰へ追加したaudio worker state / Busy action 3件はpass表示・process exit code 0だった。補正後のstate / analysis / late / failure / reset指定回帰は48件＋subtest 7件がpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- production codeとtest codeは未変更であり、MS20-B7は実装着手可能である。

### 15.8 実装結果

- 2026-07-19の再チェックでP1なし、P2 2件、P3 1件を検出し、audio正常cancel terminalとlate / duplicate callbackの分離、analysis cancel後の非Busy Statusを計画へ補正した。補正後はP1 / P2 / P3の残存なしと判定した。
- `UiState.analysis_cancelled`、adapter接続、analysis cancel terminal Status、parameter変更時のdiagnostics clear、audio cancelled callbackのcurrent job / kind / status guardを実装した。
- 新規 `tests/test_ms20_b7_diagnostics_state_integration.py` 11件でclear、adapter、analysis cancel、parameter、reset、audio normal / duplicate / kind mismatch、analysis / audio late callbackを固定した。
- B7専用11件、MS20 diagnostics 97件、pipeline / VMD 12件はpass表示・終了コード0だった。
- state / analysis / late / failure / reset 48件＋subtest 7件と全体476件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。compileallは終了コード0だった。
- README、配布用readme、Pipeline / GUI / Error仕様を現行MS20 diagnostics lifecycleへ同期した。
- dependency、package、license、Qt、network、固定モーフ、fingerprint schema、report formatは変更していない。
- 2026-07-19にユーザーから、手動GUI確認は通過し問題なしと報告された。
- B7はproduction実装、自動検証、ユーザー手動GUI確認まで完了した。B8 closeoutは未実施である。

## 16. MS20-B8: MS20 Closeout

### 16.1 目的

MS20の要求、実装、テスト、ユーザー確認、文書を総合照合し、MS21へ進めるか判定する。

### 16.2 In Scope

- B1からB7の受け入れ条件監査
- MS20固有テスト、計画指定回帰、全体テスト
- RightPane Info / Warning、VMD保存policy、report出力のユーザー確認
- TEXTあり／voice_onlyの回帰確認
- 実装済み・未実装・保留・非採用の文書同期
- P1 / P2 / P3分類とcloseout判定

### 16.3 Out of Scope

- MS21のイベント編集実装
- package / release / tag / push
- MS26の実MMD全機能受け入れ

### 16.4 主な成果物

- `docs/Implementation_Plan/MS20-B8_Implementation_Plan.md`
- テスト・ユーザー確認記録
- MS20 closeout判定
- MS21への引き継ぎ

### 16.5 受け入れ条件

- MS20全体の要求に未評価の穴がない。
- P1 / P2が解消済み、またはユーザー判断で明示処理されている。
- 実行したテストの表示結果とexit codeが分けて記録されている。
- ユーザー確認の実施範囲と結果が記録されている。
- MS21開始可否を根拠付きで判定できる。

### 16.6 計画作成結果

- 2026-07-19に `docs/Implementation_Plan/MS20-B8_Implementation_Plan.md` を作成した。
- B1からB7の成果、test、ユーザー確認、README、配布用readme、3正本仕様、現行code、MS20差分を照合した。
- B8をreview / verification / documentation closeout専用Blockとし、production codeとtest codeの変更を原則禁止した。
- MS20固有、state / GUI / worker / voice_only、pipeline / VMD、全体testの段階実行と、pass表示・fatal・process exit codeの分離記録を固定した。
- P1 / P2 / P3分類とA / B / C判定、Aまたは承認済みBの場合だけ行う正本文書同期を固定した。
- `repo_milestone.md` と `Version_Control.md` はCloseout判定後の同期対象とし、plan作成時には更新しない。
- package、release、merge、push、tag、MS21実装はB8対象外とした。
- 計画作成時点ではproduction code、test code、dependency、build設定を変更していない。次工程はB8 pre-implementation checkである。

### 16.7 実装前チェック・Closeout結果

- 2026-07-20にHEAD `41af559`、clean worktreeからB8を実施した。
- 実装前チェックではP1 / P2なし、P3 1件を検出した。現行成果物一覧の `diagnostic_report.py` とImplementation Plan群の古い候補表記を本同期で解消した。
- MS20固有108件とpipeline / VMD 12件はpass表示・process exit code 0だった。
- state / GUI / worker / voice_only回帰は65件＋subtest 7件、全体回帰は476件がpass表示まで完走した。failure / error / fatal stack traceはなく、process exit codeは既知baselineと同じ1だった。
- `compileall src tests` と `git diff --check` はprocess exit code 0だった。
- B3からB7の通過済みユーザーGUI確認を再利用した。Closeout監査後、2026-07-20にユーザーからB8チェック通過・問題なしと報告された。
- dependency、package、build、license、固定モーフ、network、Qtに変更はない。
- 残存findingはP1 / P2 / P3なし。自動検証とユーザー確認が揃ったためMS20 CloseoutをA判定で確定し、MS21 Implementation Plan策定へ進行可能である。
- merge、push、tag、release、branch削除は実施していない。

## 17. 対象ファイル整理

### 17.1 主変更対象

- 実装済み `src/core/output_diagnostics.py`
- 実装済み `src/core/diagnostic_report.py`
- `src/core/__init__.py`
- 実装済み `src/gui_wx/playback_context.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`

### 17.2 関連確認

- `src/core/pipeline.py`
- `src/core/preview_transform.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/playback_controller.py`
- `src/gui_wx/preview_panel.py`
- `src/vmd_writer/writer.py`

### 17.3 テスト候補

- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b4_playback_context.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_pipeline_and_vmd.py`

### 17.4 文書候補

- `README.md`
- `readme_mmdautolip.txt`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
- 作成済み `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md` から `MS20-B8_Implementation_Plan.md`

## 18. テスト方針

### 18.1 実行順

1. 各Blockの新規core / GUI単体テスト
2. RightPane、UiState、VMD保存、resetの関連回帰
3. TEXTあり／voice_onlyの計画指定回帰
4. MS20 closeout時の全体テスト

### 18.2 主な実行候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b3_right_pane.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms19_b8_workspace_reset.py
.\.venv\Scripts\python.exe -m pytest tests
```

実在しないMS20テストファイルは各Blockの実装時に追加する候補である。Blockごとに実在パスを再確認し、未作成ファイルを実行済みとして報告しない。

GUIテストは表示上のpass数とprocess exit codeを分けて報告する。手動GUI確認と実MMD確認を実行していない場合は、未実施と明記する。

## 19. MS20全体の受け入れ条件

- RightPane Infoが現行状態から生成したinput / analysis / generation / saveabilityを表示する。
- 再生中の位置、frame、母音がInfoへ反映される。
- Warningが `INFO / WARNING / ERROR` を構造化データから表示する。
- `ERROR` がある状態でVMD保存できない。
- `WARNING` は同一保存状態につき一度確認され、再生位置の変化で再確認されない。
- `<base>_report.txt` が専用操作からUTF-8で出力される。
- Info、Warning、保存policy、reportが同じ構造化snapshotを使用する。
- reset、入力変更、再解析、失敗、late result破棄で古い診断を残さない。
- TEXTあり／voice_only、Preview、VMD保存、MMD用WAV出力の既存導線を壊さない。
- MS21以降の機能を先行実装しない。

## 20. リスクと対策

| リスク | 対策 |
| --- | --- |
| UIが独自に診断を再計算し、reportと不一致になる | core snapshotを共通入力とし、表示文字列の読み戻しを禁止する |
| 再生timerがfingerprintを変更し、WARNING確認が繰り返される | transientな再生情報をfingerprintから除外する |
| `ERROR`時にUI無効化だけを迂回して保存できる | controller入口でも同じpolicyを検証する |
| WARNING確認のNoを確認済みとし、次回保存が無確認になる | Yesの場合だけfingerprintを記録する |
| 古いworker結果が現在診断を上書きする | 既存job id契約にsnapshot反映を合流させる |
| report出力失敗で不完全ファイルが残る | 一時ファイルで生成・検証し、成功時だけ確定する |
| RightPaneの長文でレイアウトが拡張される | scrollable childとwrap幅更新を組み合わせ、既存サイズ回帰を維持する |
| MS21以降の拡張性を理由に過剰な汎用化を行う | MS20で必要な診断項目と入力だけを実装する |

## 21. AI agent実装時の共通指示

```text
- feature/MS20-implementation を作業ブランチとする。
- 各Block開始前に対応するImplementation Planを作成する。
- Info / Warning / reportの表示文字列を診断の正本にしない。
- ERROR時の保存禁止をUIだけに依存させない。
- WARNING確認の同一性判定に再生位置を含めない。
- TEXTあり / voice_onlyの既存導線を壊さない。
- workspace reset、cancel、late callback破棄の契約を維持する。
- MMD用WAV、VMD writer形状、Whisper model選択をMS20で変更しない。
- wxPython主系を維持し、Qt / PySide6を復活させない。
- テストの表示結果とexit codeを分けて報告する。
- 実施していない手動GUI確認を通過と報告しない。
```
