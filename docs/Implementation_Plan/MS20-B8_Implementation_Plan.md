# MS20-B8 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B8 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B8_Implementation_Plan.md`
- 対象Milestone / Block: MS20-B8
- Title: MS20 Closeout
- 基準ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `58d6ded Implement MS20-B7 diagnostics state integration`
- 作成日: 2026-07-19
- 最終更新日: 2026-07-20
- 文書ステータス: Completed / MS20 Closeout A / User Check Passed
- 上位正本:
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 関連仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

### 1.1 計画作成時のリポジトリ状態

- branch: `feature/MS20-implementation`
- HEAD: `58d6ded Implement MS20-B7 diagnostics state integration`
- worktree: clean
- `main / origin/main`: `050ad2d Plan MS20 diagnostics foundation`
- 実装branchのupstream: 未設定
- Python: 3.14.3
- pytest: 9.0.3
- wxPython: 4.2.5 / wxWidgets 3.2.9

### 1.2 計画作成時の確認結果

- MS20-B1からB7の計画、実装記録、自動検証、ユーザー確認を現行Index、Roadmap、Block Breakdownから照合した。
- B2からB7のproduction実装はコミット済みである。
- B3からB7のユーザーGUI確認は通過・問題なしとして記録済みである。B2はUI非依存core foundationであり、Block固有GUI確認を前提にしない。
- B7完了時点の自動検証記録は、B7専用11件、MS20 diagnostics 97件、pipeline / VMD 12件がpass表示・終了コード0、state関連48件＋subtest 7件と全体476件がpass表示・既知wx終了処理由来のprocess exit code 1、compileallが終了コード0である。
- `050ad2d..58d6ded` のMS20差分には、diagnostics core、adapter、RightPane、playback context、save policy、report、state integration、テスト、README、仕様、進捗文書が含まれる。
- 同差分に `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` の変更はない。
- `docs/repo_milestone.md` と `docs/Version_Control.md` はMS19 Closeoutが最新記録であり、MS20 Closeout時の同期対象である。
- MS20-B8は新機能実装Blockではなく、現行成果の総合監査、回帰検証、文書同期、Closeout判定を行うBlockとして実施可能である。
- 計画作成時点で、結果を変える未確定のユーザー選択はない。

### 1.3 実装前チェック・Closeout実施結果

- 2026-07-20に、HEAD `41af559 Plan MS20-B8 closeout`、clean worktreeからB8を実施した。
- 実装前チェックではP1 / P2なし、P3 1件を検出した。P3はBlock Breakdownの現行成果物一覧に、実装済み `src/core/diagnostic_report.py` が「新規候補」、作成済みImplementation Plan群が「後続」と残っていた記録上の不整合である。
- MS20固有108件はpass表示・process exit code 0だった。
- state / GUI / worker / voice_only回帰は65件＋subtest 7件がpass表示、failure / error / fatal stack traceなし、process exit code 1だった。
- pipeline / VMD回帰12件はpass表示・process exit code 0だった。
- 全体476件はpass表示まで完走し、failure / error / fatal stack traceなし、process exit code 1だった。B7完了baselineと件数・終了状態が一致した。
- `compileall src tests` はprocess exit code 0だった。
- B3からB7のユーザーGUI確認は各Blockの通過・問題なし記録を再利用した。Closeout監査後、2026-07-20にユーザーからB8チェック通過・問題なしと報告された。
- `050ad2d..41af559` にdependency、package、build、license関連ファイルの変更はなく、固定モーフ、network禁止、wxPython主系を維持している。
- P3をBlock Breakdownの文書同期で解消した。Closeout時点の残存findingはP1 / P2 / P3なしである。
- MS20 Closeout判定はAとする。MS21 Implementation Plan策定へ進行可能である。
- 自動検証、既存BlockのGUI確認証拠、B8ユーザーチェックが揃い、MS20のCloseout状態を確定した。
- package、release、main merge、remote push、tag、branch削除は実施していない。

## 2. 背景

MS20は、後続Milestoneが共通利用できるRightPane Information / Warning / Output Diagnostics基盤を整備するMilestoneである。

B1で診断参照元、severity、diagnostic code、save-state fingerprint、report、failure保持の契約を固定した。B2からB7では次を実装した。

- B2: UI非依存 `OutputDiagnosticsSnapshot`、diagnostic item、severity、canonical fingerprint
- B3: wx adapterとRightPane Infoの入力・解析・生成・保存可否表示
- B4: snapshotから分離した軽量live playback context
- B5: Warning全severity表示、ERROR保存禁止、WARNING同一fingerprint一回確認、failure保持
- B6: 同一snapshotを使用するUTF-8 plain-text diagnostic reportとatomic保存
- B7: input / parameter / analysis / cancel / late callback / reset / save failureへのstate統合

B3からB7のユーザーGUI確認は通過し、B7完了時点でREADME、配布用readme、Pipeline / GUI / Error仕様も現行実装へ同期済みである。

B8では新しい診断機能を追加せず、B1からB7の要求、コード、テスト、ユーザー確認、文書を再照合する。MS20固有回帰と全体回帰を実行し、findingsをP1 / P2 / P3に分類したうえで、MS20をCloseoutしてMS21計画へ進めるかをA / B / Cで判定する。

## 3. 目的

- MS20の完了条件を、現行コード、テスト、ユーザー確認、文書の4系統で再検証する。
- Info、Warning、VMD保存policy、diagnostic reportが同じ構造化snapshot契約へ接続されていることを確認する。
- input、parameter、analysis、cancel、late callback、reset、save failureで古いdiagnostics stateが持ち越されないことを確認する。
- TEXTあり / voice_only、Preview、playback、VMD保存、MMD用WAV出力の既存導線に回帰がないことを確認する。
- 自動テストのpass表示とprocess exit codeを分離して記録する。
- P1 / P2 / P3を分類し、MS20 CloseoutをA / B / Cで明示する。
- Closeout可能な場合だけ、正本進捗文書をMS20完了・MS21計画待ちへ同期する。

## 4. In Scope

- branch、HEAD、worktree、MS20基準コミット、MS20差分範囲の確認
- B1からB7の目的、受け入れ条件、実装結果、テスト結果、ユーザー確認結果の監査
- MS20固有testの再実行
- UiState、RightPane、analysis、audio worker、save、reset、voice_onlyの関連回帰
- pipeline / VMD回帰と全体test
- `compileall`、`git diff --check`、変更範囲監査
- READMEと配布用readmeの操作説明整合
- Pipeline / GUI / Error仕様と現行実装の整合
- dependency、package、license関連ファイルがMS20で変更されていないことの確認
- findingsのP1 / P2 / P3分類
- A / B / CのCloseout判定
- Closeout可能な場合の以下の文書同期:
  - 本計画
  - MS20 Block Breakdown
  - MS20 Index
  - MS20 Roadmap
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- MS21 Implementation Plan策定への引き継ぎ

## 5. Out of Scope

- 新しいproduction機能、GUI部品、diagnostic code、severityの追加
- fingerprint schema、report format、VMD formatの変更
- MS21のイベント選択・編集・履歴機能
- MS22以降のpreset、profile、Whisper model、一括出力機能
- broad refactor、repository再構成
- dependency追加・更新
- package build、SmokeLaunch、installer、実行用ZIP作成
- version bump、release readiness、tag、GitHub Release
- `main`へのmerge、remote push、branch削除
- 実MMDでの全機能受け入れ。これはMS26で扱う
- Qt / PySide6の復活
- network、cloud ASR、他ASR backend、音声外部送信、background通信、Whisper自動download

Closeout監査でP1 / P2のコード・状態契約・回帰問題を検出した場合、B8を完了扱いにせず、修正をrepair作業へ分離する。P3の文書表現修正だけはB8文書同期として実施してよい。

## 6. 前提条件

- Active GUIはwxPythonである。
- 固定モーフは `あ / い / う / え / お` である。
- input modeは `text_audio` と `voice_only` である。
- diagnosticsの正本は `OutputDiagnosticsSnapshot` であり、RightPane表示文字列を保存policyやreport入力へ読み戻さない。
- live playback contextはdiagnostics snapshot / fingerprintから分離する。
- ERRORはVMD保存を禁止する。
- WARNING確認済み状態は同一save-state fingerprintにつき一度だけ保持し、再生位置をidentityへ含めない。
- diagnostic reportは元source audio pathをuser-facing既定pathに使用し、本文ではsnapshotの正規化pathを使用する。
- workspace diagnostics stateはfailure、snapshot、WARNING確認済みfingerprint、analysis cancel状態を含む。
- analysis / audio workerのlate resultはcurrent job / kind / status契約で破棄する。
- VMD / report保存失敗だけでは有効な解析・diagnostics stateを破棄しない。
- workspace resetはsource、保存済みVMD、MMD用WAV、diagnostic report、analysis WAV cacheを削除しない。
- B3からB7のユーザー確認結果は各Blockの手動確認証拠として再利用できる。
- B8でproduction codeを変更しない場合、同一手動シナリオの再実施を必須にしない。
- B7完了コミット `58d6ded` と本計画をコミットし、B8実行前にclean worktreeを確認する。
- 全体476件pass表示 / process exit code 1はB7完了時の比較baselineである。exit code 1だけで成功扱いにも失敗扱いにもせず、fail / error / fatal exception /未完走の有無を確認する。

## 7. 対象ファイル

### 7.1 B8主変更対象

- 新規 `docs/Implementation_Plan/MS20-B8_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

### 7.2 Closeout整合確認対象

- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20-B4_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20-B6_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20-B7_Implementation_Plan.md`

過去Blockの履歴記述は、現在状態と誤認されない限り保持する。現行status、次工程、実装済み／未実装の分類が矛盾する箇所だけを同期する。

### 7.3 実装確認対象

- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/core/pipeline.py`
- `src/core/__init__.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/playback_context.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/playback_controller.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/theme.py`
- `src/gui_wx/voice_only_errors.py`
- `src/vmd_writer/writer.py`

### 7.4 dependency / package / license確認対象

- `pyproject.toml`
- `requirements.txt`
- `MMD_AutoLipTool.spec`
- `build.ps1`
- `LICENSE`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`
- `FFmpeg/bin/`

B8では内容変更を予定しない。MS20基準コミットとの差分有無と、意図しない変更がないことだけを確認する。

### 7.5 test対象

MS20固有:

- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b4_playback_context.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`

state / GUI / worker / voice_only:

- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_wx_ms15_b3_playback.py`
- `tests/test_wx_ms15_b5_state_theme.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_ms17_b8_audio_worker_state.py`
- `tests/test_ms17_b8_busy_action_states.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`

pipeline / VMD:

- `tests/test_pipeline_and_vmd.py`

全体:

- `tests/`

## 8. 実装方針

### 8.1 Closeout専用Blockとする

B8はreview、verification、documentation closeoutを行う。production code、test code、build設定、dependencyを変更しない。

P1 / P2を検出した場合はCloseout判定を保留し、問題、成立条件、影響、最小修正範囲、必要回帰を提示する。B8実行依頼だけをrepair権限と解釈しない。

### 8.2 証拠を四系統に分ける

Closeout判定は次を混同せずに行う。

1. 現行コードとGit差分
2. 自動テストのpass / fail / error表示とprocess exit code
3. ユーザーが各Blockで実施した手動GUI確認
4. README、仕様、進捗文書の記載

生成したcloseout記録を、それ自身の実装・検証証拠として循環参照しない。

### 8.3 MS20受け入れmatrix

各要求を少なくとも次へ対応付ける。

| 要求 | code正本 | test証拠 | user / docs証拠 |
| --- | --- | --- | --- |
| structured diagnostics / fingerprint | `output_diagnostics.py` | B2 test | Pipeline仕様 |
| RightPane Info | adapter / `right_pane.py` | B3 test | B3 user確認 / README |
| live playback context | `playback_context.py` | B4 test | B4 user確認 / GUI仕様 |
| Warning / VMD save policy | snapshot / controller | B5 test | B5 user確認 / Error仕様 |
| diagnostic report | `diagnostic_report.py` / controller | B6 test | B6 user確認 / README |
| state lifecycle / late result | UiState / callbacks | B7 test | B7 user確認 / 3正本仕様 |
| TEXTあり / voice_only互換 | pipeline / worker / controller | MS19 + MS20回帰 | README / user確認 |

test名や文書記載だけで成立を断定せず、実装入口とguardを確認する。

### 8.4 findings分類

- P1: データ破損、誤ったVMD保存許可、現行workspaceへのlate result反映、MS20主要機能不成立など、直ちにCloseoutを止める問題
- P2: 主要契約・回帰・必須文書・検証証拠の欠落など、次Milestone前に解消すべき問題
- P3: 現行挙動を変えない記録・表現・routing上の軽微な不整合

P3はB8文書同期で解消してよい。P1 / P2は未解消のままA判定にしない。

### 8.5 Closeout判定

- A: P1 / P2なし。MS20 Closeout OK。MS21 Implementation Plan策定へ進める
- B: P1なし。P2をユーザーが明示承認して持ち越す場合だけ条件付きCloseout
- C: P1、未承認P2、主要test失敗、必須ユーザー確認不足、文書証拠不足のいずれかがありCloseout不可

判定時は根拠、findings、未検証事項、持ち越し先を明記する。

### 8.6 文書同期

Aまたはユーザー承認済みBの場合だけ、次をMS20 CloseOut済みへ同期する。

- B8 planの実施結果と判定
- Block BreakdownのB8結果とMS20全体status
- IndexのActive MS / 現在フェーズ / B8記録
- RoadmapのMS20完了記録と次工程
- `repo_milestone.md` の先頭へMS20 Closeout記録
- `Version_Control.md` の先頭へMS20 Closeout変更記録

README、配布用readme、3正本仕様は現行実装との不一致がある場合だけ更新する。

### 8.7 Git / release境界

MS20 Closeout文書更新、commit、main merge、remote push、次branch作成、releaseは別操作である。

B8実施依頼だけでは、stage、commit、merge、push、tag、branch削除を行わない。ユーザーの明示依頼ごとに実行する。

## 9. 詳細ステップ

1. `git status --short --branch`、branch、HEAD、直近履歴、branch trackingを確認する。
2. B7実装・テスト・ユーザー確認・文書とB8計画がコミット済みで、B8実行前のworktreeがcleanであることを確認する。
3. MS20基準 `050ad2d` から現在HEADまでの変更ファイルとcommit列を確認する。
4. B1からB7の目的、受け入れ条件、実装結果、テスト結果、ユーザー確認を一覧化する。
5. MS20受け入れmatrixを、code、test、user、docsの4系統で照合する。
6. diagnostics core、adapter、RightPane、playback、save policy、report、state lifecycleの実装入口とguardを確認する。
7. MS20固有testを実行する。
8. state / GUI / worker / voice_only回帰を実行する。
9. pipeline / VMD回帰を実行する。
10. 全体testを実行し、collected、pass / fail / error / skip、fatal exception、process exit codeを記録する。
11. `compileall src tests` を実行する。
12. B3からB7のユーザー確認記録を再確認する。B8で機能変更がなく証拠が十分なら再実施を要求しない。
13. README、配布用readme、Pipeline / GUI / Error仕様を現行コードと照合する。
14. `pyproject.toml`、requirements、spec、build、license文書、FFmpeg同梱物にMS20由来の意図しない変更がないことを確認する。
15. findingsをP1 / P2 / P3へ分類する。
16. P1 / P2がある場合はCloseoutを保留し、repairまたはユーザー判断へ送る。
17. P1 / P2がなく、test・user・docs証拠が揃う場合はA判定を行う。
18. Aまたは承認済みBの場合だけ、B8 plan、Block Breakdown、Index、Roadmap、repo milestone、Version Controlを同期する。
19. `git diff --check`、変更範囲、古いstatus、未実装機能の完了誤記を監査する。
20. 確認ファイル、変更ファイル、test結果、user証拠、findings、判定、未検証事項、次工程を報告する。

## 10. 状態遷移 / データ契約

### 10.1 milestone状態

```text
MS20-B1〜B7 完了
  └─ B8 repo / code / test / user / docs audit
       ├─ P1 / 未承認P2 / 必須証拠不足あり
       │    └─ C: Closeout不可 / repairまたは追加確認へ
       ├─ ユーザー承認済みP2持ち越しのみ
       │    └─ B: 条件付きCloseout / 持ち越し先を明記
       └─ P1 / P2なし
            └─ A: MS20 Closeout OK / MS21計画へ
```

### 10.2 B8で変更しない機能契約

- `OutputDiagnosticsSnapshot` がInfo、Warning、VMD保存policy、reportの共通構造化正本である。
- diagnostic itemは安定したcode、normalized severity、phase、identity contextを持つ。
- canonical fingerprintはwriter出力と診断identityに影響する状態だけを含む。
- live playback positionはfingerprintと静的snapshotを変更しない。
- ERRORはVMD保存不可、WARNINGは同一fingerprintにつき一回確認である。
- diagnostic reportはsnapshotをplain text化し、RightPane表示文字列を入力にしない。
- input / parameter / analysis / resetで旧diagnostics stateをclearし、現在状態からrebuildする。
- analysis cancelはcurrent terminal callbackで確定し、有効な旧planが再利用可能ならsaveabilityを維持する。
- late / duplicate callbackは現行stateとGUIを変更しない。
- VMD / report保存失敗とdialog cancelでは有効な解析・diagnostics stateを保持する。
- TEXTあり / voice_onlyの既存VMD保存契約を維持する。
- 固定モーフは `あ / い / う / え / お` である。

### 10.3 文書状態

```text
B8 plan作成
  -> Pre-implementation Check Pending
  -> Closeout Audit In Progress
  -> A / B: MS20 CloseOut済み
  -> C: MS20 Open / blocker記録
```

歴史記録の「計画時点では未実装」は履歴として保持できる。現行status、現在フェーズ、次工程だけはCloseout結果と一致させる。

### 10.4 Git状態

- plan作成commit、B8 closeout文書commit、main merge、remote pushは別commit / 別操作でよい。
- B8判定はbranch上のsource tree完成度を対象とし、remote未pushだけをC判定理由にしない。
- merge / pushが未実施であることはCloseout報告へ明記する。

## 11. テスト方針

各コマンドは一つずつ実行し、pass表示とprocess exit codeを分けて記録する。

### 11.1 MS20固有

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms20_b2_output_diagnostics.py tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b3_right_pane_info.py tests\test_ms20_b4_playback_context.py tests\test_ms20_b5_warning_save_policy.py tests\test_ms20_b6_diagnostic_report.py tests\test_ms20_b6_report_save_flow.py tests\test_ms20_b7_diagnostics_state_integration.py -q
```

B7完了時の各test件数合計は108件である。B8では収集・pass表示を再確認し、件数差がある場合は原因を記録する。

### 11.2 state / GUI / worker / voice_only

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py tests\test_wx_ms14_b4_analysis.py tests\test_wx_ms14_b5_export.py tests\test_wx_ms15_b3_playback.py tests\test_wx_ms15_b5_state_theme.py tests\test_wx_ms16_b3_right_pane.py tests\test_ms17_b8_audio_worker_state.py tests\test_ms17_b8_busy_action_states.py tests\test_ms17_b8_late_worker_result_discard.py tests\test_ms19_b4_voice_only_gui_state.py tests\test_ms19_b5_transcription_edit_state.py tests\test_ms19_b7_voice_only_error_handling.py tests\test_ms19_b8_workspace_reset.py -q
```

### 11.3 pipeline / VMD

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py -q
```

B7完了時は12件pass表示・終了コード0である。

### 11.4 全体

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

B7完了baseline:

- collected: 476
- pass表示: 476
- fail / error表示: なし
- process exit code: 1
- pytest summary後のfatal stack trace: なし

B8では次を別々に記録する。

- collected件数
- pass / fail / error / skip表示
- pytest summary到達有無
- fatal exception / access violation / stack traceの有無
- process exit code
- baselineとの差分

process exit code 1を自動的にpass扱いしない。一方、pass表示、summary完走、fatal有無を確認せずexit codeだけで新規回帰と断定しない。

### 11.5 compile

```powershell
.\.venv\Scripts\python.exe -m compileall src tests
```

### 11.6 文書・差分

```powershell
git diff --check
```

追加で次を確認する。

- `050ad2d..HEAD` のMS20変更ファイル
- dependency / package / license対象の差分有無
- B8 closeout対象外のproduction code変更有無
- `MS20-B7完了 / 次はB8` などの古いcurrent-status記載
- MS21以降の計画機能を実装済みと誤記していないこと

### 11.7 手動GUI確認

各Blockの既存証拠:

- B3: RightPane Info、縦scroll、解析中mask、「再解析が必要」attention表示
- B4: live playback contextとtheme追従
- B5: Warning全severity、ERROR保存禁止、WARNING確認policy
- B6: diagnostic reportの専用保存導線、内容、失敗・cancel
- B7: state lifecycle、cancel、late callback、reset、保存失敗回帰

B8でproduction code / GUIを変更せず、各記録が追跡可能なら再実施を必須にしない。

次の場合だけ追加手動確認を提示する。

- GUI挙動へ影響するrepairを実施した
- 既存ユーザー確認記録と現行実装が対応しない
- 自動testで代替できない必須導線の証拠が欠落している
- closeout auditで表示・操作回帰の疑いを検出した

### 11.8 build / package

B8ではbuild、SmokeLaunch、packageを実行しない。spec、build script、dependency、licenseにMS20差分がないことを確認し、実際のrelease readinessはMS27へ送る。

## 12. 受け入れ条件

- B1からB7の成果、受け入れ条件、実装結果、test、user確認が追跡可能である。
- MS20受け入れmatrixに未評価の主要要求がない。
- MS20固有testで新規fail / errorがない。
- state / GUI / worker / voice_only回帰で新規fail / errorがない。
- pipeline / VMD回帰で新規fail / errorがない。
- 全体testがbaseline同等以上まで完走し、pass表示とprocess exit codeが分離記録される。
- 既知exit codeだけを理由に新規fail / error / fatal exceptionを見逃していない。
- Info / Warning / VMD保存policy / reportが同じsnapshot契約を使用する。
- playback positionがsnapshot / fingerprintを変更しない。
- input / parameter / analysis / cancel / late callback / reset / save failureのstate契約がコード・test・仕様で一致する。
- TEXTあり / voice_only、Preview、VMD保存、MMD用WAV出力の既存導線を壊していない。
- B3からB7のユーザー確認結果が追跡でき、未確認の必須GUI導線がない。
- READMEと配布用readmeが現行操作を一致して説明する。
- Pipeline / GUI / Error仕様が現行実装と一致する。
- dependency、package、license、固定モーフ、network方針に未承認変更がない。
- P1 / P2 / P3が分類される。
- P1または未承認P2がある場合はCloseoutしない。
- Closeout判定をA / B / Cで明示する。
- Aまたは承認済みBの場合だけ、MS20正本文書をCloseOut済みへ同期する。
- B8だけを根拠にMS21以降、package、releaseを実装済みと記載しない。
- stage、commit、merge、push、tag、releaseを明示依頼なしに実行しない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| B1からB7のplan記載を実装証拠と誤認する | current code、test、user記録、docsの4系統で再照合する |
| 古いBlockの「未実装」履歴を現行statusと誤認する | 履歴記述とcurrent status / next actionを分離する |
| wxのprocess exit code 1を無条件に成功または失敗扱いする | pass / fail / error、summary完走、fatal、exit code、baselineを分離する |
| 既知扱いで新しいfail / fatalを見逃す | failure位置、stack trace、collected件数、完走状態をbaseline比較する |
| test件数だけで主要導線の成立を断定する | 受け入れmatrixで実装入口とguardを確認する |
| B7ユーザー確認をB8で新規実施したと誤記する | 各Blockの既存証拠として再利用し、B8新規確認と分離する |
| closeout中にP1 / P2を黙って修正する | Cまたは保留とし、repair権限を別途得る |
| P3文書修正からproduction変更へscopeが広がる | B8主変更対象をcloseout文書へ限定する |
| `repo_milestone.md` / `Version_Control.md` を先に完了更新する | A / 承認済みB判定後だけ先頭へCloseout記録を追加する |
| MS20完了とmain merge / push完了を混同する | Git外部操作を別依頼とし、未実施状態を明記する |
| MS20完了とrelease readinessを混同する | build / package / releaseはMS27へ送る |
| MS21以降の将来機能を実装済みと誤記する | Roadmapのplanned状態を維持する |
| 固定モーフやnetwork方針をcloseoutで変更する | `あ / い / う / え / お` とlocal-only制約を不変条件にする |

## 14. Codex 実装時の注意

- 最初に `docs/MS17_and_Beyond_Index.md`、Git状態、本計画、MS20 Index、Block Breakdownを確認する。
- shell commandは一つずつ実行し、pipeline / chained command / parallel実行を行わない。
- B8はCloseout監査であり、新機能実装へ広げない。
- `docs/repo_milestone.md` と `docs/Version_Control.md` はtargeted searchと先頭のbounded readを使用し、全体を読み込まない。
- P1 / P2を検出した場合はMS20完了を記録せず、成立条件、影響、最小repair範囲を報告する。
- P3だけをB8文書同期で修正してよい。
- testのpass表示とprocess exit codeを必ず分離する。
- 既存ユーザー確認とB8で新たに実施した確認を分けて記録する。
- 手動GUI確認を再実施していない場合は、既存Block証拠の再利用と明記する。
- B8でproduction code、test code、dependency、build設定を変更しない。
- package、release、version bump、merge、push、tag、branch削除を行わない。
- wxPython主系を維持し、Qt / PySide6へ触れない。
- 固定モーフ `あ / い / う / え / お` を変更しない。
- network、cloud ASR、他ASR backend、音声外部送信、background通信、Whisper自動downloadを追加しない。

B8完了報告は次を含める。

1. 確認したファイル
2. 変更したファイル
3. 実行したtest
4. testの表示結果とprocess exit code
5. ユーザー確認証拠
6. P1 / P2 / P3
7. Closeout判定
8. 仕様からの逸脱
9. 未検証事項
10. 次工程
