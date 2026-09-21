# MS20-B7 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B7 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B7_Implementation_Plan.md`
- 対象Block: MS20-B7
- Block名: State Integration / Regression / Docs
- 実施予定ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `b54933a Implement MS20-B6 diagnostic report export`
- 作成日: 2026-07-18
- 文書ステータス: Implementation / Automated Verification / User Manual GUI Check Completed
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 直接の前提契約:
  - `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B6_Implementation_Plan.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B7は、B2からB6で導入したdiagnostics snapshot、failure保持、WARNING確認済みfingerprint、RightPane Info / Warning、VMD保存policy、diagnostic reportを、既存の入力変更、parameter変更、解析lifecycle、workspace reset、job ID / late callback契約へ横断統合するBlockである。新しい診断機能を追加するのではなく、古い作業状態を次の入力や失敗後の状態へ持ち越さないことと、保存失敗だけでは有効な解析状態を破棄しないことを回帰テストと正本文書へ固定する。

### 1.1 計画作成時の確認結果

- 2026-07-18にbranch、HEAD、worktree、MS20 routing、B1のB7引き継ぎ、B5 / B6実装、UiState、MainFrame、AppController、analysis / audio workerのjob ID guard、既存回帰テスト、README、配布用readme、3正本仕様を照合した。
- branchは `feature/MS20-implementation`、HEADは `b54933a`、worktreeは計画作成前にcleanだった。
- `UiState.clear_output_diagnostics_state()` は `current_diagnostic_failure`、`current_output_diagnostics_snapshot`、`confirmed_warning_save_state_fingerprint` を一括clearする。
- `UiState.invalidate_analysis()`、`mark_analysis_success()`、`reset_workspace()` は上記clearへ到達する。
- TEXT読込成功、音声読込開始、書き起こし編集適用／復元は `invalidate_analysis()` へ到達する。
- 解析開始時は旧diagnostics stateをclearし、解析成功時は現行入力から新snapshotを生成し、解析失敗時は旧planを無効化して分類済みfailureを保持する。
- VMD保存失敗は有効なtiming plan、snapshot、WARNING確認済みfingerprintを保持する。diagnostic report保存失敗もsnapshot、failure、timing plan、fingerprintを保持する。
- analysis callbackは `_current_job_id`、audio callbackは `current_audio_job_id` とworker statusでlate resultを破棄する。
- workspace resetはaudio / analysis job IDを進め、workspace stateをclearし、`sync_ui_state()` で未入力snapshot、RightPane、action stateを再構築する。
- 現行parameter変更は `analysis_result_valid` がtrueのときだけ `invalidate_analysis()` を呼ぶ。解析失敗snapshotや未解析snapshotだけが保持されている状態では、旧failure／snapshot／確認済みfingerprintを明示clearしない経路が残る。
- core builderは `analysis_cancelled` diagnostic codeを実装済みだが、GUI adapterは `analysis_cancelled=False` を固定し、UiStateとanalysis cancel callbackから接続していない。
- `README.md` と `readme_mmdautolip.txt` はMS19までの基本操作を説明するが、MS20のRightPane Info / Warning、severity連動VMD保存、diagnostic report保存を説明していない。
- 3正本仕様はMS19のreset / failure / late callback契約を持つが、MS20 diagnostics state、WARNING確認済みfingerprint、report保存可否／失敗保持をまだ記載していない。
- Block Breakdown記載の配布用readme候補 `MMD_AutoLipTool_readme.txt` は存在せず、現行ファイルは `readme_mmdautolip.txt` である。
- B7計画作成baselineとして、state / analysis / late callback / failure / reset / B5 / B6関連48件＋subtest 7件はpass表示・process exit code 0だった。
- 本計画作成ではproduction code、test code、README、仕様本文、dependency、build設定を変更しない。

### 1.2 計画作成時に固定する判断

- B7はB1からB6の契約を横断監査し、実証された欠落だけを最小補修する。diagnostic item、severity、fingerprint schema、report formatは変更しない。
- diagnostics lifecycleの一括clear対象はfailure、snapshot、WARNING確認済みfingerprint、analysis cancel表示状態とする。
- `sync_ui_state()` 後は `current_output_diagnostics_snapshot` が `None` のままとは限らない。旧snapshotを破棄した後、現在状態から新snapshotを再構築することを正常契約とする。
- parameter変更は、有効な解析結果がある場合は従来どおりtiming planを無効化する。有効な解析結果がなくても、旧failure、旧snapshot、確認済みfingerprint、cancel表示状態はclearする。
- cancel自体はfailure DTOにしない。入力契約不成立のERRORがなければ `analysis_cancelled` INFOを現在snapshotへ反映し、ERRORが残る場合はcore builderの既存規則どおりcancel INFOを抑制する。
- 入力変更、parameter変更、解析開始、解析成功、解析失敗、workspace resetはcancel表示状態をclearする。`_on_analysis_cancel()` は中止要求だけを記録し、current jobのterminal success / error callbackが `_cancel_requested` を確認した時点でだけcancel表示状態を設定する。
- 解析cancel時に、入力とparameterが変わっておらず直前の有効planを保持している場合は、そのplanを破棄しない。既に再解析待ち／入力不成立なら、cancelだけを理由に保存可能へ戻さない。
- analysis / audio job ID不一致のlate callbackはfailure、snapshot、confirmation、cancel状態、RightPane、Preview、保存action、statusを一切更新しない。
- VMD保存失敗とdiagnostic report保存失敗は、現在の有効な解析／diagnostics stateを保持する。保存dialog cancelや上書き拒否もstate非変更とする。
- workspace resetは保存済みVMD、MMD用WAV、diagnostic report、source file、analysis WAV cacheを削除しない。
- B7文書同期ではREADME、`readme_mmdautolip.txt`、3正本仕様を現行MS20到達状態へ更新する。`repo_milestone.md`、`Version_Control.md`、package / release文書はB8 closeoutへ残す。
- 新規dependency、package、license、固定モーフ、ASR、network、Qt / PySide6は変更しない。

### 1.3 実装前チェック結果

- 2026-07-18の初回チェックではP1なし、P2 2件、P3 1件を検出した。
- P2として、入力commit前失敗を一律にworkspace不変と読める記述を、dialog cancel、TEXT commit前失敗、音声選択確定後失敗の非対称な現行契約へ分離した。
- P2として、analysis cancel状態の確定を `_on_analysis_cancel()` の要求時点ではなく、current jobのterminal success / error callbackへ限定した。
- P3として、`tests/test_ms17_b8_audio_worker_state.py` と `tests/test_ms17_b8_busy_action_states.py` を関連回帰一覧と指定testコマンドへ追加した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。
- P3で指定回帰へ追加したaudio worker state / Busy action 3件はpass表示・process exit code 0だった。補正後のstate / analysis / late / failure / reset指定回帰は48件＋subtest 7件がpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- production code、test code、dependency、build設定は変更していない。MS20-B7は実装着手可能である。
- 2026-07-19の再チェックでP1なし、P2 2件、P3 1件を検出した。audio workerの正常cancel完了callbackとlate / duplicate callbackの条件分離、analysis cancel terminal後の非Busy status確定をP2として補正した。P3として前回の「残存なし／Ready」記録を再チェック結果で更新した。
- audio success / error callbackは `CANCELLING / CANCELLED / DISCARDED` で破棄する一方、current jobかつcurrent kindのcancelled callbackは `CANCELLING` から `CANCELLED` へ遷移する正常terminalとして一度だけ許可する。job不一致、shutdown、status不一致、既にterminalのduplicate callbackは完全不変とする。
- analysis cancel terminalでは `analysis_cancelled=True`、Busy解除に加え、Statusをcancelledへ確定する。Busy解除後に `StatusKey.BUSY`／「処理中...」を残さない。
- 上記補正後、P1 / P2 / P3の残存なしと判定し、MS20-B7の実装を開始する。

## 2. 背景

MS20-B5 / B6完了後のworkspace diagnostics stateは次の4要素を持つ。

```text
current_diagnostic_failure
current_output_diagnostics_snapshot
confirmed_warning_save_state_fingerprint
analysis cancellation presentation state (B7 connection candidate)
```

表示と保存は次の経路へ収束している。

```text
UiState + timing plan + writer parameters
  -> OutputDiagnosticsSnapshot
       -> RightPane Info
       -> RightPane Warning
       -> VMD save button / menu / controller guard
       -> diagnostic report formatter / writer
```

この構造では、旧snapshotを保持したまま表示文字列だけをclearしても不十分である。反対に、VMDやreportの保存失敗だけで有効なsnapshotを破棄すると、同一解析状態での再試行とWARNING確認済み状態が失われる。B7は「破棄すべき状態」と「保持すべき状態」を入口ごとに固定し、UiState、RightPane、保存導線、late callbackの一貫性を保証する。

## 3. 目的

- B2からB6のdiagnostics stateを既存workspace lifecycleへ完全統合する。
- input / parameter / analysis / resetごとのclear、rebuild、retain規則を固定する。
- analysis cancelを既存core diagnostic contractへ接続する。
- late callbackが現在diagnostics stateとGUIを上書きしないことを固定する。
- TEXTあり／voice_onlyの既存解析・Preview・VMD保存・report保存を維持する。
- README、配布用readme、3正本仕様をMS20-B6完了後の実到達状態へ同期する。

## 4. In Scope

- `UiState` diagnostics lifecycleの横断監査と限定補修
- analysis cancel stateのUiState／adapter／callback接続
- parameter変更時のfailure／snapshot／confirmation／cancel clear
- TEXT読込、音声読込、書き起こし編集／復元時のclear回帰
- analysis start / success / failure / cancelのclear／retain回帰
- analysis / audio late callbackの完全不変回帰
- workspace reset後のUiState、RightPane、Preview、report menu、VMD save、confirmation整合
- VMD保存失敗／cancelとreport保存失敗／cancelの保持回帰
- TEXTあり／voice_onlyの回帰
- B7専用state integration test
- README、配布用readme、Pipeline / GUI / Error仕様の実到達状態同期
- MS20関連限定回帰、全体test、compileall、文書差分検証

## 5. Out of Scope

- diagnostic code、severity、identity contextの追加・再設計
- fingerprint schema version変更
- report section、encoding、filename、atomic writer変更
- RightPane layout、色、theme、playback contextの再設計
- VMD writer、morph補間、固定モーフ `あ / い / う / え / お` の変更
- 新規の入力形式、ASR backend、Whisper model選択
- report自動保存、VMD／WAV／report一括出力
- MS20-B8 closeout判定
- `repo_milestone.md`、`Version_Control.md` のcloseout更新
- package build、SmokeLaunch、実MMD受け入れ、release、tag、push
- 新規dependency
- Qt / PySide6復活
- cloud ASR、音声外部送信、background通信、Whisper自動download
- MS21以降の先行実装

## 6. 前提条件

- branchが `feature/MS20-implementation` である。
- B6実装コミット `b54933a` 以降を基準とする。
- worktreeの既存変更を確認し、ユーザー所有変更を保護する。
- B1のstate discard / failure / cancel / late callback所有権を変更しない。
- B5のERROR禁止、WARNING同一fingerprint一回確認を変更しない。
- B6のERROR report保存許可と保存失敗時state保持を変更しない。
- 現行 `UiState.clear_output_diagnostics_state()` を一括clearの責務境界として維持する。
- 実装前チェックでcancel state追加の必要性、parameter変更の欠落、既存test fixture影響を再照合する。

## 7. 対象ファイル

### 7.1 主変更候補

| ファイル | 変更内容 |
| --- | --- |
| `src/gui_wx/ui_state.py` | analysis cancel状態の保持、diagnostics一括clear、reset / invalidate / success lifecycle |
| `src/gui_wx/output_diagnostics_adapter.py` | UiStateのcancel状態を `DiagnosticSnapshotInput.analysis_cancelled` へ接続 |
| `src/gui_wx/main_frame.py` | parameter変更clear、analysis start / success / failure / cancel接続、late callback不変 |

`src/gui_wx/app_controller.py` はinput audio、audio job ID、workspace reset、VMD／report保存失敗保持の関連確認対象とする。現行guardで契約を満たす場合は変更しない。欠落がtestで実証された場合だけ限定補修する。

`src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、`src/gui_wx/right_pane.py` は原則変更しない。B7に必要なcore code、report、RightPane表示APIは既に存在する。

### 7.2 関連確認

- `src/gui_wx/app_controller.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/parameter_panel.py`
- `src/gui_wx/voice_only_errors.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/core/pipeline.py`
- `pyproject.toml`
- `MMD_AutoLipTool.spec`
- `build.ps1`

### 7.3 テスト

主追加:

- 新規 `tests/test_ms20_b7_diagnostics_state_integration.py`

既存testは原則として回帰対象とする。fixtureが新しいUiState fieldやmenu contractを明示的に構築している場合だけ、production契約を弱めず最小更新する。

関連回帰:

- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b4_playback_context.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms17_b8_audio_worker_state.py`
- `tests/test_ms17_b8_busy_action_states.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`

### 7.4 文書

- 新規 `docs/Implementation_Plan/MS20-B7_Implementation_Plan.md`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

`repo_milestone.md` と `Version_Control.md` はB8 closeoutまで更新しない。

## 8. 実装方針

### 8.1 diagnostics lifecycle正本

UiStateの一括clear APIを次の正本とする。

```text
clear_output_diagnostics_state()
  -> current_diagnostic_failure = None
  -> current_output_diagnostics_snapshot = None
  -> confirmed_warning_save_state_fingerprint = None
  -> analysis_cancelled = False
```

個別入口が4 fieldを直接重複clearしない。`invalidate_analysis()`、`mark_analysis_success()`、`reset_workspace()`、analysis startは一括clear APIを使用する。

### 8.2 snapshot破棄と再構築

`sync_ui_state()` は現在状態からsnapshotを再構築してUiStateへ保存する。したがってtestは次を区別する。

1. 旧snapshot object / fingerprint / failure / confirmationが破棄された。
2. sync後の新snapshotが現在入力、analysis validity、parameter、cancel状態を反映する。
3. RightPane Info / Warning、VMD save、report menuが新snapshot／現在source audio状態と一致する。

`current_output_diagnostics_snapshot is None` だけをGUI同期後の受け入れ条件にしない。

### 8.3 input変更

成功したTEXT変更、音声変更、書き起こし編集適用／復元では次を行う。

- 旧timing planを無効化する。
- 旧failure、snapshot、confirmation、cancel状態をclearする。
- Previewと選択eventをclearする。
- 現在入力から再解析待ち／未解析snapshotを再構築する。
- source audioが残る場合、report menuは有効でよい。ただし保存内容は新snapshotであり旧snapshotを使用しない。

入力失敗時は入口ごとに次を正本とする。

- TEXT / 音声のfile dialog cancelは、job ID、input、analysis、diagnostics、Preview、action、statusを変更しない。
- TEXT読込、検証、変換がState更新前に失敗した場合は、現行実装どおり既存workspaceを変更しない。
- 音声file pathを受理して `request_open_audio_file()` を開始した後は、probe / FFmpeg探索 / 解析用WAV生成より前に旧音声、transcription、analysis、diagnosticsを無効化する。その後のprobe / 変換失敗や長時間音声確認cancelでは旧workspaceを復元せず、音声・解析・diagnosticsが無効な状態を維持する。
- 音声失敗後のsnapshotは現在の無効状態から再構築し、旧failure、旧snapshot、confirmation、analysis cancel表示状態を再利用しない。

### 8.4 parameter変更

parameter変更時:

- 有効な解析結果がある場合は `invalidate_analysis()` を呼び、timing plan、Preview、VMD保存を無効化する。
- 有効な解析結果がない場合も `clear_output_diagnostics_state()` を呼び、旧failure、snapshot、confirmation、cancel状態を破棄する。
- 変更後parameterを含むgeneration summaryで新snapshotを生成する。
- parameter変更でinput path、transcription、audio analysis、job IDを変更しない。
- settings保存失敗はdiagnostics lifecycleを巻き戻さない。

### 8.5 analysis lifecycle

| 入口 | plan | failure | snapshot / confirmation | cancel状態 |
| --- | --- | --- | --- | --- |
| start | 現行規則を維持。表示は解析中mask | clear | clear後、解析中snapshotを再構築 | clear |
| success | 新planへ置換 | clear | clear後、成功snapshotを再構築 | clear |
| failure | 旧plan破棄、再解析待ち | 分類済みfailureを保持 | failure ERROR snapshotを再構築、confirmationなし | clear |
| cancel、旧plan有効 | 旧plan保持 | 追加しない | cancel INFOを含むsnapshot、saveability再評価 | true |
| cancel、plan無効 | 無効のまま | 追加しない | 現在ERROR snapshot。cancel INFOは抑制 | true |
| late result | 更新しない | 更新しない | 更新しない | 更新しない |

cancel状態はユーザー中止の表示情報であり、exception detailやfailure identityへ変換しない。次のinput / parameter / analysis lifecycleでclearする。

`_on_analysis_cancel()` はprogress dialogからの中止要求を記録するだけで、cancel表示状態、Busy、snapshotを確定しない。current jobの `_on_analysis_success()` または `_on_analysis_error()` が `_cancel_requested` を検出したterminal経路で、cancel表示状態を設定してからBusyを解除し、`sync_ui_state()` でsnapshotとactionを再構築する。`job_id != _current_job_id` のcallbackはterminal経路として扱わない。

### 8.6 late callback

analysis callback:

- `job_id != _current_job_id` ならcleanup、Busy、status、UiState、RightPane、Previewを更新しない。

audio callback:

- success / error callbackは `audio_job_id != current_audio_job_id`、shutdown中、またはworker statusが `CANCELLING / CANCELLED / DISCARDED` なら、UiStateとGUIを更新しない。
- cancelled callbackはshutdown中、job ID不一致、kind不一致、worker stateなし、またはworker statusが `CANCELLING` 以外なら更新しない。
- current jobかつcurrent kindでworker statusが `CANCELLING` のcancelled callbackだけを正常terminalとして受理し、Busy解除、`CANCELLED` 遷移、status更新、GUI同期を一度だけ行う。
- 既に `CANCELLED / DISCARDED / COMPLETED / FAILED` のcurrent jobへ届くduplicate cancelled callbackは完全不変とする。

late callback testはtiming planだけでなく、failure、snapshot object、fingerprint、confirmation、cancel状態、Info / Warning label、report menu、VMD action、statusの前後同一性を確認する。

### 8.7 reset

workspace reset成功時:

- audio / analysis job IDを進める。
- input、transcription、timing plan、failure、snapshot、confirmation、cancel状態、selection、playback、workspace output参照をclearする。
- `analysis_pending_rebuild=False`、`input_mode=text_audio`、`status=IDLE` とする。
- `sync_ui_state()` 後は未入力ERROR snapshotを現在snapshotとしてよい。
- RightPaneは前作業のInfo / Warningを表示せず、report menu、VMD保存、Playを無効にする。
- source file、保存済みVMD / MMD用WAV / report、analysis WAV cacheを削除しない。

reset確認No／dialog close、Busy中拒否は完全不変とする。

### 8.8 保存失敗とcancel

VMD保存:

- dialog cancel / WARNING確認Noではwriterを呼ばない。
- writer失敗ではtiming plan、failure、snapshot、confirmationを保持する。

diagnostic report保存:

- dialog cancel / 上書きNoではwriterを呼ばない。
- writer失敗ではtiming plan、failure、snapshot、confirmation、cancel状態を保持する。
- report保存可否はVMD saveabilityと分離したままにする。

MMD用WAV出力失敗はMS17のaudio worker契約を維持し、diagnostics snapshotを変更しない。

### 8.9 文書同期

`README.md` と `readme_mmdautolip.txt`:

- RightPane Info / Warningの役割
- `INFO / WARNING / ERROR`
- ERROR時のVMD保存不可
- WARNING時の保存前確認
- `ファイル > 診断レポート保存...`
- `<base>_report.txt`
- resetで保存済みreportを削除しないこと

Pipeline仕様:

- `OutputDiagnosticsSnapshot` の正本と4つのlifecycle state
- input / parameter / analysis / cancel / late / resetのclear／retain matrix
- reportとVMD saveabilityの分離

GUI仕様:

- RightPane Info / Warning
- VMD／report action state
- cancel／reset／Busy／themeの表示契約

Error仕様:

- MS20 severity正規化
- failure DTO保持
- cancel INFOとERROR優先
- VMD／report保存失敗時のstate保持

## 9. 詳細ステップ

### Step 1: 実装前基準線確認

- branch、HEAD、worktree、Python / pytest環境を確認する。
- B1、B5、B6、Block Breakdown、3正本仕様を再読する。
- UiState、MainFrame、AppController、adapter、worker、関連testを再照合する。
- P1 / P2 / P3を確定し、production変更前にplanを補正する。

### Step 2: B7専用testを先に追加

- lifecycle stateを持つfixtureを作る。
- input、parameter、analysis、cancel、late、reset、save failureの期待状態をtestへ固定する。
- 既存実装で通る項目と欠落項目を分離する。

### Step 3: UiState lifecycle補修

- cancel状態を必要最小限で追加する。
- diagnostics一括clearへcancel状態を含める。
- reset / invalidate / successの既存呼出しを維持する。
- 新しいsettings keyや永続化fieldを追加しない。

### Step 4: adapter / MainFrame接続

- adapterからcancel状態をcore snapshot inputへ渡す。
- `_on_analysis_cancel()` は中止要求だけを設定し、current jobのterminal success / error callbackだけがcancel状態を設定してBusy解除、cancelled Status確定、`sync_ui_state()` を行う。
- analysis cancel terminal後は `StatusKey.BUSY` を残さず、Status表示を「解析をキャンセルしました」とする。
- parameter変更時、analysis validityにかかわらず旧diagnostics stateをclearする。
- late callback guardより前にstate変更やcleanupを追加しない。

### Step 5: controller / reset / save回帰

- audio input、audio late callback、workspace resetを新diagnostics field込みで確認する。
- audio正常cancel terminalとlate / duplicate cancelled callbackを分離して確認する。
- VMD / report保存失敗とcancelの保持を確認する。
- 欠落がなければAppControllerを変更しない。

### Step 6: TEXTあり／voice_only回帰

- TEXT変更と通常解析を確認する。
- voice_only transcription edit、再解析、failure、cancelを確認する。
- Preview、VMD保存、report保存の既存契約を維持する。

### Step 7: README / 仕様同期

- READMEと配布用readmeへMS20ユーザー導線を追加する。
- Pipeline / GUI / Error仕様へMS20 diagnostics lifecycleを追加する。
- legacy履歴を現行仕様として書き換えず、現行節を追加・補正する。

### Step 8: 回帰・差分監査

- B7専用testからMS20関連、state / worker / reset、pipeline / VMDへ広げる。
- 全体test、compileall、`git diff --check` を実行する。
- dependency、package、license、Qt、network、固定モーフ変更がないことを確認する。
- 実装結果とユーザーGUI確認結果をB7 plan、Index、Roadmap、Block Breakdownへ同期する。

## 10. 状態遷移 / データ契約

### 10.1 clear / retain matrix

| 操作 | failure | snapshot | confirmation | cancel | timing plan |
| --- | --- | --- | --- | --- | --- |
| TEXT / 音声dialog cancel | unchanged | unchanged | unchanged | unchanged | unchanged |
| TEXT読込／変換のcommit前失敗 | unchanged | unchanged | unchanged | unchanged | unchanged |
| TEXT変更成功 | clear | discard / rebuild | clear | clear | invalidate |
| 音声変更開始 | clear | discard / rebuild | clear | clear | invalidate |
| 音声変更開始後のprobe／変換失敗・長時間確認cancel | clear | invalid-state rebuild | clear | clear | invalidate |
| transcription edit / revert | clear | discard / rebuild | clear | clear | invalidate |
| parameter変更 | clear | discard / rebuild | clear | clear | validならinvalidate |
| analysis start | clear | discard / in-progress rebuild | clear | clear | 現行規則を維持 |
| analysis success | clear | success rebuild | clear | clear | new plan |
| analysis failure | replace | failure rebuild | clear | clear | invalidate |
| analysis cancel | clearのまま | current-state rebuild | clearのまま | set | current validityに従う |
| analysis / audio late result | unchanged | unchanged | unchanged | unchanged | unchanged |
| VMD save failure | unchanged | unchanged | unchanged | unchanged | unchanged |
| report save failure | unchanged | unchanged | unchanged | unchanged | unchanged |
| reset Yes | clear | discard / initial rebuild | clear | clear | clear |
| reset No / Busy reject | unchanged | unchanged | unchanged | unchanged | unchanged |

analysis cancel terminalのStatus契約:

- cancel要求直後はBusyと `StatusKey.BUSY` を維持する。
- current jobのterminal success / error callbackで `analysis_cancelled=True`、Busy解除、cancelled Status確定を同一経路で行う。
- Status表示は「解析をキャンセルしました」とし、Busy解除後に「処理中...」を残さない。
- 次のinput / parameter / analysis start / success / failure / resetでcancel状態をclearするとき、各既存lifecycleのStatusへ遷移する。

### 10.2 report state

- report fileはworkspace stateではない。
- 保存済みreport pathをUiStateへ保持しない。
- resetはreport fileを削除しない。
- report menuはsource audio pathあり／非Busyで有効であり、ERROR snapshotでも有効でよい。
- input変更後のreportは必ず保存操作時の最新snapshotから生成する。

### 10.3 fingerprint

- input、timing plan、writer parameter、diagnostic identityが変われば新fingerprintを生成する。
- old confirmationは旧fingerprintとともにclearする。
- playback、tab、scroll、status、save pathはfingerprintへ含めない。
- B7ではschema versionを変更しない。

## 11. テスト方針

### 11.1 B7専用state integration

- `clear_output_diagnostics_state()` が全diagnostics lifecycle fieldをclearする。
- `sync_ui_state()` が旧snapshotではなく現在状態のsnapshotを保持する。
- TEXT / 音声dialog cancelではworkspace diagnostics stateを変更しない。
- TEXT読込／変換のcommit前失敗では既存workspaceを保持する。
- successful TEXT / audio changeで旧failure／snapshot／confirmation／cancelをclearする。
- 音声変更開始後のprobe／変換失敗と長時間確認cancelでは旧workspaceを復元せず、無効状態の新snapshotを保持する。
- transcription edit / revertで同じclearを行う。
- failure snapshot中のparameter変更で旧failureをclearする。
- valid snapshot中のparameter変更でplanを無効化し、再解析待ちERRORへ移る。
- analysis startで旧failure／confirmation／cancelをclearする。
- successで新snapshot／fingerprintになる。
- failureで旧planを破棄し、failure ERRORと保存禁止になる。
- `_on_analysis_cancel()` の要求時点ではcancel表示状態とBusyを確定しない。
- current jobのterminal success / error callbackだけがcancel表示状態を設定し、Busy解除とcancelled Status確定を行う。
- analysis cancel terminal後に `StatusKey.BUSY` と「処理中...」が残らない。
- cancel、旧plan有効時はcancel INFOを持ち、current saveabilityを維持する。
- cancel、plan無効時はERRORを維持し、cancel INFOを抑制する。
- cancelでfailure DTOを生成しない。
- analysis late success / errorが全stateとGUIを変更しない。
- audio success / errorはcancelling以降に破棄し、正常cancelled callbackだけが `CANCELLING -> CANCELLED` を一度実行する。
- audio late / duplicate cancelled callbackが全stateとGUIを変更しない。
- reset Yesで全workspace diagnostics stateとactionを初期化する。
- reset No / Busy拒否で完全不変になる。
- VMD / report save failureとdialog cancelでstateを保持する。

### 11.2 TEXTあり／voice_only

- TEXTありinput change、success、failure、cancel
- voice_only initial analysis、transcription edit、reanalysis、failure、cancel
- voice_only failure時の編集済みtext保持
- 両modeのVMD saveability、RightPane、report menu

### 11.3 文書

- `README.md` と `readme_mmdautolip.txt` の操作説明が一致する。
- 3正本仕様のclear / retain規則がplanと一致する。
- `MMD_AutoLipTool_readme.txt` という不存在pathが現行成果物候補に残らない。
- B7をimplementedと記載するのは実装後だけとする。

### 11.4 対象testコマンド

各コマンドは一つずつ実行する。

B7専用:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b7_diagnostics_state_integration.py -q
```

MS20 diagnostics:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b3_output_diagnostics_adapter.py tests/test_ms20_b3_right_pane_info.py tests/test_ms20_b4_playback_context.py tests/test_ms20_b5_warning_save_policy.py tests/test_ms20_b6_diagnostic_report.py tests/test_ms20_b6_report_save_flow.py -q
```

state / analysis / late / failure / reset:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py tests/test_wx_ms14_b4_analysis.py tests/test_wx_ms14_b5_export.py tests/test_ms17_b8_audio_worker_state.py tests/test_ms17_b8_busy_action_states.py tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms19_b4_voice_only_gui_state.py tests/test_ms19_b5_transcription_edit_state.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py -q
```

pipeline / VMD:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py -q
```

全体:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

compile:

```powershell
.\.venv\Scripts\python.exe -m compileall src tests
```

文書・差分:

```powershell
git diff --check
```

GUI runnerがpass表示後に既知wx終了処理でnonzeroとなる場合も、pass数とprocess exit codeを分けて記録する。

### 11.5 手動GUI確認

1. TEXTあり解析成功後、RightPane Info / Warning、VMD保存、report保存が現在解析と一致する。
2. TEXT / 音声dialog cancelとTEXT読込／変換のcommit前失敗では既存workspaceが変わらない。
3. TEXTを変更すると旧Info / Warning／確認済みWARNING状態が消え、再解析待ちになる。
4. 音声を変更すると旧解析、Preview、Info / Warningが残らない。
5. 音声選択確定後のprobe／変換失敗では旧workspaceへ戻らず、音声・解析・diagnosticsが無効な状態になる。
6. parameter変更で旧解析が無効化され、旧failure表示も残らない。
7. 解析開始時に旧failureとWARNING確認済み状態が残らない。
8. 解析成功後、新しいInfo / Warningと保存状態になる。
9. 分析中止button押下直後はBusyを維持し、current jobのterminal callback後にcancel情報と「解析をキャンセルしました」を表示してBusyを解除する。「処理中...」は残らない。
10. 有効planからの再解析cancelでは旧planを保持する。
11. 再解析待ち状態でのcancelではVMD保存不可のままである。
12. voice_onlyの編集、再解析、failure、cancelで編集済み書き起こしが契約どおり保持される。
13. VMD保存失敗とreport保存失敗後も、解析結果、RightPane、WARNING確認済み状態が保持される。
14. `新規作業...` のNo／closeで状態が変わらず、YesでInfo / Warning、Preview、VMD保存、report保存が初期化される。
15. reset後に保存済みVMD、MMD用WAV、report、source fileが削除されない。
16. Light / Dark / Systemで、初期、再解析待ち、failure、cancelのInfo / Warningが判読できる。

手動GUI確認を実施していない場合は未実施と報告する。実MMD、build、SmokeLaunch、package確認はB7範囲外とする。

## 12. 受け入れ条件

- input / parameter / analysis / resetの全入口で旧diagnostics stateが契約どおりclearされる。
- dialog cancel、TEXT commit前失敗、音声変更開始後失敗の非対称な状態復帰が現行実装とError仕様の補正後記載に一致する。
- sync後のsnapshotが旧objectではなく現在状態から再構築される。
- parameter変更時、analysis validityにかかわらず旧failure／snapshot／confirmation／cancelが残らない。
- analysis cancelが既存 `analysis_cancelled` INFOへ接続され、failure DTOへ変換されない。
- cancel要求時点ではBusyとsnapshotを確定せず、current jobのterminal callbackだけがcancel状態を確定する。
- analysis cancel terminal後にStatusがcancelledへ遷移し、`StatusKey.BUSY`／「処理中...」が残らない。
- cancelだけを理由にERROR状態が保存可能へ変わらない。
- analysis / audio late callbackがUiState、RightPane、Preview、保存action、statusを変更しない。
- audio正常cancelled callbackはcurrent job / kindの `CANCELLING -> CANCELLED` だけを一度実行し、late / duplicate callbackは完全不変である。
- reset後に旧Info / Warning、report、WARNING確認済み状態を使用できない。
- reset No / Busy拒否は完全不変である。
- 解析失敗後に旧解析結果をVMD保存できない。
- VMD / report保存失敗とcancelで有効な解析snapshotを破棄しない。
- TEXTあり／voice_onlyの既存導線が維持される。
- README、配布用readme、3正本仕様がMS20-B6完了状態と一致する。
- B7専用test、指定回帰、全体testがpass表示まで完走する。
- pass表示とprocess exit codeが分けて報告される。
- ユーザーGUI確認の実施／未実施と結果が記録される。
- 新規dependency、package、license、Qt、network、固定モーフ変更がない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| `sync_ui_state()` が新snapshotを生成するため、clear失敗を見逃す | old object / fingerprintとcurrent field内容の両方をtestする |
| 「input commit前」をTEXTと音声へ一律適用し、音声失敗時に旧workspaceを誤復元する | dialog cancel、TEXT commit前失敗、音声選択確定後失敗を別契約・別testにする |
| parameter変更でfailure snapshotだけが残る | analysis validityと無関係にdiagnostics一括clearへ到達させる |
| cancelをfailure扱いしてERRORを増やす | failure DTOと分離したbool stateから既存INFO codeへ接続する |
| cancel INFOで既存ERRORが隠れる | core builderのERROR優先・cancel抑制規則を維持する |
| cancelで有効な旧planを不要に破棄する | input / parameter不変ならcurrent plan validityを維持する |
| cancel button押下時点でcancel表示やBusy解除を早期確定する | request callbackとcurrent job terminal callbackを分離してtestする |
| analysis cancelでBusyだけ解除し、Statusが「処理中...」のまま残る | terminal cancel専用Statusへ遷移し、StatusKeyと表示文字列をtestする |
| late callback testがtiming planだけを見てdiagnostics上書きを見逃す | failure / snapshot / confirmation / cancel / GUI / statusの完全不変を検証する |
| audioの `CANCELLING` を全callbackで破棄して正常cancel完了できない | success / error破棄条件とcancelled terminal受理条件を分離する |
| resetで保存済みreportまで削除する | workspace参照clearとfilesystem file削除を分離する |
| VMD / report保存失敗で再試行可能状態を失う | state前後同一性をfailure injection testへ固定する |
| report menuをVMD saveabilityへ誤接続する | source audio path／BusyだけのB6 guardを回帰する |
| READMEだけ更新して仕様が古いままになる | README、配布用readme、Pipeline / GUI / Error仕様を同一実装証拠で同期する |
| Block Breakdownの不存在readme pathを転記する | 現行 `readme_mmdautolip.txt` を成果物正本として使用する |
| B7をMS20 closeoutと誤認する | B8 closeout判定、repo milestone、Version ControlをB7から除外する |
| wx全体testの既知nonzeroをpassと誤報する | pass表示とprocess exit codeを分けて記録する |

## 14. Codex 実装時の注意

- 最初に `docs/MS17_and_Beyond_Index.md` を読む。
- コマンドは並列・連結実行せず、一つずつ実行する。
- `feature/MS20-implementation` 上で作業する。
- 未コミット変更があればユーザー所有変更として保護する。
- pre-implementation checkでP1 / P2 / P3を確定するまでproduction codeを変更しない。
- B7はstate integrationとdocs同期だけを所有し、B8 closeoutを先行しない。
- clearとsync後のrebuildを混同しない。
- late callback guardより前にstateを変更しない。
- cancelをexception failureへ変換しない。
- ERROR状態をcancelだけで保存可能へ倒さない。
- VMD / report保存失敗で有効な解析状態を破棄しない。
- report menuをVMD saveabilityから導出しない。
- source file、保存済み出力、analysis WAV cacheをresetで削除しない。
- `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、fingerprint schema、report formatを根拠なく変更しない。
- READMEと配布用readmeの操作説明を一致させる。
- 実行していないtestや手動GUI確認を通過と報告しない。
- 固定モーフ `あ / い / う / え / お` を変更しない。
- Qt / PySide6を復活させない。
- network、cloud ASR、音声外部送信、background通信、Whisper自動downloadを追加しない。
- package、release、tag、pushを行わない。

B7実装完了報告は次の形式とする。

1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題

## 15. 実装結果

- 2026-07-19に再チェックで検出したP2 2件、P3 1件を本計画へ補正し、残存なしを確認して実装した。
- `UiState` に `analysis_cancelled` と `StatusKey.ANALYSIS_CANCELLED` を追加し、diagnostics一括clear、reset、invalidate、successへ既存lifecycle経由で接続した。
- adapterからcore `DiagnosticSnapshotInput.analysis_cancelled` へ状態を渡した。
- analysis cancelはrequest時にBusyを維持し、current jobのterminal callbackでcancel状態、Busy解除、「解析をキャンセルしました」を確定する。
- parameter変更時はanalysis validityにかかわらず旧diagnostics stateをclearし、cancelled Statusを現行input準備状態へ戻す。
- audio cancelled callbackはcurrent job / kindの `CANCELLING -> CANCELLED` のみ一度受理し、kind不一致とduplicate terminal callbackを破棄する。
- B7専用11件、MS20 diagnostics 97件、pipeline / VMD 12件はpass表示・終了コード0だった。
- state / analysis / late / failure / reset 48件＋subtest 7件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- 全体476件は全件pass表示、failure / error表示なし、同じ既知wx終了処理由来のprocess exit code 1だった。compileallは終了コード0だった。
- dependency、package、license、Qt、network、固定モーフ、fingerprint schema、report formatは変更していない。
- README、配布用readme、Pipeline / GUI / Error仕様、MS20 routing文書を実装済み・自動検証済みへ同期した。
- 2026-07-19にユーザーから、手動GUI確認は通過し問題なしと報告された。
- B7はproduction実装、自動検証、ユーザー手動GUI確認まで完了した。B8 closeoutは未着手である。
