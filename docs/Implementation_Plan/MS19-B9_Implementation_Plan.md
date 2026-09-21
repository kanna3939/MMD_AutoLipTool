# MS19-B9 Implementation Plan

## 1. 文書情報

- Milestone: MS19
- Block: B9
- Title: MS19 Closeout
- Status: Completed - Closeout A
- 作成日: 2026-07-12
- 基準ブランチ: `feature/MS19`
- 計画作成時HEAD: `b1dff14 Complete MS19 B7 and plan B8`
- 実行前提:
  - MS19-B1からMS19-B8までは完了済み。
  - B3からB8のユーザー確認対象は通過・問題なし。
  - B8実装・テスト・文書同期と本計画書は、B9実施前にコミットし、作業ツリーをcleanにする。
  - MS19-B9は新機能Blockではなく、検証・文書同期・Closeout判定を行うBlockである。

## 2. 背景

MS19では、既存のTEXTあり入力を維持しながら、TEXTなしの音声のみ入力、Whisper書き起こし、書き起こし編集・再解析、Preview、VMD保存、音声のみ入力固有のエラー処理を追加した。

MS19-B8では、ファイルメニューの `新規作業... Ctrl+N` から現在の入力・書き起こし・解析結果・表示・再生状態を初期化し、設定・履歴を保持したまま次素材へ移る導線を追加した。B8専用テスト8件はexit code 0でpassし、通常 `pytest tests` は368件すべてpass表示まで完走した。対象・関連回帰と全体テストでは、既存wx終了処理由来のprocess exit code 1が継続している。B8のユーザースモークテストは通過・問題なしである。

B9では、B1からB8の成果を追加実装せずに再照合し、MS19をCloseOutしてよいかを判定する。

## 3. 目的

- MS19の受け入れ条件がコード、テスト、ユーザー確認、文書のすべてで成立しているか確認する。
- TEXTあり / voice_onlyの両導線と、B8の連続作業導線に回帰がないことを確認する。
- 自動テストの表示結果とprocess exit codeを分けて記録する。
- README、配布用readme、仕様書、進捗文書を実際の到達状態へ同期する。
- P1 / P2 / P3を分類し、MS19 Closeout可否を明示する。

## 4. In Scope

- `feature/MS19` のbranch、HEAD、作業ツリー、MS19差分範囲の確認。
- MS19-B1からB8の成果物・受け入れ条件・ユーザー確認結果の一覧化。
- voice_only core / GUI / VMD保存 / エラー処理 / workspace resetの対象テスト実行。
- 既存TEXTあり、Preview、Waveform、playback、RightPane、VMD保存の回帰テスト実行。
- 通常 `pytest tests` の再実行と、pass表示数・process exit code・wx終了挙動の分離記録。
- B3からB8までのユーザー確認結果の証拠確認。
- README、配布用readme、GUI状態仕様、pipeline契約、エラー仕様の最終整合確認。
- milestone Index、Block Breakdown、Roadmap、B9計画書、repo milestone、Version ControlのCloseout同期。
- dependency、packaging、license関連ファイルにMS19由来の意図しない変更がないことの確認。
- MS19 Closeout判定と、次工程への引き継ぎ整理。

## 5. Out of Scope

- 新機能追加、UI redesign、広範なrefactor。
- MS19で未発見だった不具合の無制限な修正。
- MS20のモーフ編集・タイミング編集機能。
- package / installer / release成果物の生成。
- version bump、tag作成、GitHub Release公開。
- `main`へのmerge、remote push、branch削除。
- PyInstaller、FFmpeg、Whisper、wxPython等のdependency変更。
- Qt / PySide6 GUIの復活。

Closeout確認でコード修正が必要なP1 / P2を検出した場合は、B9を完了扱いにせず、修正範囲を提示してユーザー承認後のrepair作業へ分離する。

## 6. 前提条件

- Active GUIはwxPythonであり、Qt / PySide6系は凍結済みである。
- MS19の入力モードは `text_audio` と `voice_only` である。
- voice_onlyのVMD writer inputは有効な `current_timing_plan` であり、TEXT pathを必須としない。
- 書き起こし編集適用後は再解析成功までVMD保存不可である。
- `新規作業...` は設定・履歴と物理ファイルを保持し、作業データと表示だけを初期化する。
- B3からB8のユーザー確認結果は、該当Block完了の手動確認証拠として再利用してよい。
- B9で機能変更を行わない限り、同じ手動シナリオの再実施を必須としない。
- baselineの全体テストは368件pass表示、process exit code 1である。exit code 1だけをテスト失敗と断定しない一方、新しい失敗・例外・未完走を既知問題として処理しない。
- MS19ではdependency、packaging設定、license方針を変更していない。

## 7. 対象ファイル

### 7.1 主対象

- 新規 `docs/Implementation_Plan/MS19-B9_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

### 7.2 Closeout整合確認対象

- `README.md`
- `readme_mmdautolip.txt`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS19-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B7_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19-B8_Implementation_Plan.md`

### 7.3 実装・設定確認対象

- `src/core/whisper_timing.py`
- `src/core/pipeline.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/info_panel.py`
- `src/gui_wx/voice_only_errors.py`
- `pyproject.toml`
- `MMD_AutoLipTool.spec`
- `build.ps1`
- `LICENSE`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`

### 7.4 テスト対象

- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b3_transcription_contract.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_whisper_timing.py`
- `tests/test_text_processing.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b3_input.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_wx_ms14_b6_closeout.py`
- `tests/test_wx_ms15_b1_waveform.py`
- `tests/test_wx_ms15_b2_preview.py`
- `tests/test_wx_ms15_b3_playback.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms16_b6_event_selection_foundation.py`

## 8. 実装方針

### 8.1 Closeout専用Blockとする

B9では、実装済み挙動を変更しない。コード・テストの追加が必要になった場合は、Closeout判定を保留し、問題をP1 / P2 / P3へ分類する。

P3の文書表現修正だけで到達状態が変わらない場合は、B9文書同期として修正してよい。P1 / P2のコード・状態契約・回帰問題はB9内で黙って修正しない。

### 8.2 証拠を四系統に分ける

Closeout判断は以下を混同せずに行う。

1. 現行コードとGit差分
2. 自動テストの表示結果とprocess exit code
3. ユーザーが実施した手動確認
4. README / 仕様 / milestone文書の状態

### 8.3 package / releaseとの境界

MS19 Closeoutはsource tree上の機能・テスト・文書の完了判定である。package生成、release version決定、実行用ZIP作成、tag / pushは別作業とし、B9の合否へ混在させない。

### 8.4 Closeout判定

- A: P1 / P2なし。MS19 Closeout OK。package / release作業またはMS20計画へ進める。
- B: P1なし。P2をユーザー判断で持ち越す場合のみ条件付きCloseout。
- C: P1、未承認P2、主要テスト失敗、必須手動確認不足のいずれかがあり、Closeout不可。

## 9. 詳細ステップ

1. `git status --short --branch`、branch、HEAD、直近履歴を確認する。
2. B8実装・文書同期とB9計画がコミット済みで、作業ツリーがcleanであることを確認する。
3. `d876397`以降のMS19差分と、B1からB8の成果物一覧を確認する。
4. MS19の受け入れ条件を、コード・テスト・ユーザー確認・文書へ対応付けたmatrixにする。
5. MS19固有テストを実行する。
6. core / VMD / wxPython関連回帰テストを実行する。
7. 通常 `pytest tests` を実行し、収集数、pass表示、失敗、警告、process exit codeを記録する。
8. B3からB8のユーザー確認記録を確認する。機能変更や証拠不足がある場合だけ追加手動確認を提示する。
9. README、配布用readme、GUI状態仕様、pipeline契約、エラー仕様を現行挙動と照合する。
10. `pyproject.toml`、spec、build、license文書にMS19由来の意図しない変更がないことを確認する。
11. findingsをP1 / P2 / P3へ分類する。
12. P1 / P2がなければ、B9計画書、Block Breakdown、Index、Roadmap、repo milestone、Version ControlをMS19 CloseOut済みへ同期する。
13. `git diff --check` と変更範囲監査を行い、MS20、package、release、Qtへ範囲が広がっていないことを確認する。
14. A / B / CのCloseout判定、実行テスト、手動確認証拠、未検証事項、次工程を報告する。

## 10. 状態遷移 / データ契約

### 10.1 milestone状態

```text
MS19-B1〜B8 完了
  └─ B9 repo / test / docs audit
       ├─ P1 / 未承認P2 / 必須証拠不足あり -> C: Closeout不可
       ├─ ユーザー承認済みP2持ち越しのみ -> B: 条件付きCloseout
       └─ P1 / P2なし -> A: MS19 Closeout OK
```

### 10.2 機能データ契約

B9は以下の実装済み契約を変更しない。

- `text_audio` と `voice_only` の入力モード分離。
- Whisper書き起こし・編集・再解析・timing planの有効性契約。
- TEXT pathなしのvoice_only VMD保存契約。
- 解析失敗時とVMD保存失敗時の状態復帰差分。
- workspace reset後の `text_audio` / `IDLE`、設定履歴保持、late callback破棄契約。

### 10.3 Git / release状態

MS19 Closeout文書更新と、commit / merge / push / releaseは別操作である。B9実施依頼だけではremoteへ書き込まない。

## 11. テスト方針

### 11.1 MS19固有テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_textless_pipeline.py tests\test_ms19_b3_transcription_contract.py tests\test_ms19_b4_analysis_worker_voice_only.py tests\test_ms19_b4_voice_only_gui_state.py tests\test_ms19_b5_transcription_edit_state.py tests\test_ms19_b7_voice_only_error_handling.py tests\test_ms19_b8_workspace_reset.py
```

### 11.2 core / GUI回帰

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py tests\test_text_processing.py tests\test_pipeline_and_vmd.py tests\test_wx_ms14_b2_state.py tests\test_wx_ms14_b3_input.py tests\test_wx_ms14_b5_export.py tests\test_wx_ms14_b6_closeout.py tests\test_wx_ms15_b1_waveform.py tests\test_wx_ms15_b2_preview.py tests\test_wx_ms15_b3_playback.py tests\test_wx_ms16_b3_right_pane.py tests\test_wx_ms16_b6_event_selection_foundation.py
```

### 11.3 全体テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

baselineは368件pass表示 / process exit code 1である。B9では次を別々に記録する。

- collected件数
- pass / fail / error / skip表示
- stack traceまたはfatal exceptionの有無
- process exit code
- baselineとの差分

### 11.4 手動確認

B3からB8でユーザー確認済みの以下を証拠として再確認する。

- TEXTあり入力の解析・Preview・VMD保存。
- TEXTなし音声のみ入力の書き起こし・解析・VMD保存。
- 書き起こし編集適用、再解析、保存可否。
- voice_only失敗時の案内と状態復帰。
- `新規作業...` の確認Yes / No、次素材開始、物理ファイル非削除。

B9で機能コードを変更しない場合は再実施を必須としない。証拠不足、機能変更、回帰疑いがある場合だけ追加確認を提示する。

### 11.5 build / package

B9ではbuild・packageを必須にしない。spec、build script、dependency、licenseに変更がないことをdiffで確認し、実際のpackage生成は別工程へ送る。

## 12. 受け入れ条件

- B1からB8の状態が完了として整合し、B9開始時の作業ツリーがcleanである。
- MS19固有テストと関連回帰テストで新規fail / errorがない。
- 全体テストがbaseline同等以上まで完走し、表示結果とprocess exit codeが分離記録されている。
- 既知のwx終了コード以外の新規例外・未完走を既知問題扱いしていない。
- B3からB8のユーザー確認結果が追跡でき、未確認の必須導線がない。
- TEXTあり / voice_only / 編集再解析 / VMD保存 / エラー復帰 / workspace reset契約が文書とコードで一致する。
- READMEと配布用readmeが現在のユーザー操作を説明している。
- package、version、dependency、licenseに未承認変更がない。
- P1 / P2 / P3が分類され、P1 / 未承認P2が残る場合はCloseoutしない。
- Closeout判定がA / B / Cで明示される。
- Aまたは承認済みBの場合だけ、MS19の正本進捗文書をCloseOut済みへ同期する。
- merge / push / tag / releaseを明示依頼なしに実行していない。

## 13. リスクと対策

### R1. wx終了コード1を回帰と誤認する

- pass表示、stack trace、process exit code、baselineを分けて記録する。
- exit codeだけで成功・失敗を断定しない。

### R2. 既知扱いで新しい失敗を見逃す

- collected数、失敗位置、例外内容をbaselineと比較する。
- 新規fail / error /未完走はP1またはP2として扱う。

### R3. Closeout中に修正範囲が拡大する

- P3文書修正以外のコード変更はrepairへ分離する。
- MS20候補やUI改善をB9へ混ぜない。

### R4. ユーザー確認を未実施または再実施済みと誤記する

- 各Blockのユーザー報告を証拠として記録する。
- B9で実行していない操作を新規の手動passとして記載しない。

### R5. MS19 Closeoutとrelease完了を混同する

- version bump、package、tag、GitHub ReleaseをOut of Scopeとして維持する。
- MS19 Closeout後の次工程をpackage / releaseまたはMS20計画として分ける。

### R6. B8未コミット変更を取りこぼす

- B9実施前にB8実装・テスト・文書とB9計画を含むコミットを作成し、clean treeを確認する。
- B9差分監査では基準コミットと現在HEADの両方を記録する。

## 14. Codex 実装時の注意

- 最初に `docs/MS17_and_Beyond_Index.md`、Git状態、B9計画、MS19 Block Breakdownを確認する。
- shell commandを並列実行せず、pipeline / chained commandを避ける。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- review / closeoutをコード実装へ広げない。
- P1 / P2を検出した場合はMS19完了を記録せず、ユーザーへ判断材料を提示する。
- 自動テストのpass表示とprocess exit codeを必ず分離する。
- ユーザー確認済み事項とB9で新たに実行した事項を分けて報告する。
- package / release / version bump / merge / push / tagを実行しない。
- wxPython主系を維持し、Qt / PySide6へ触れない。
- 最終報告には、確認ファイル、変更ファイル、テスト結果、ユーザー確認証拠、P1 / P2 / P3、Closeout判定、未検証事項、次工程を含める。

## 15. B9実施結果

### 15.1 実施日と環境

- 実施日: 2026-07-13
- ブランチ: `feature/MS19`
- HEAD: `63c57d3 Implement MS19 B8 and plan B9`
- Python: 3.14.3
- wxPython: 4.2.5 / wxWidgets 3.2.9
- pytest: 9.0.3
- `AGENTS.md` の未コミット変更は、ユーザー指示により保留し、B9変更へ混在させていない。

### 15.2 自動テスト結果

- MS19固有テスト: 33 passed / exit code 0
- `test_wx_ms14_b6_closeout.py`: 修正前は3件pass表示後にaccess violationが発生。`tearDownClass` で `_cleanup_analysis_job()` を呼ぶ補修後は3 passed / exit code 0。
- 計画指定回帰: 62 passed / exit code 1。pass表示後のaccess violationやテスト失敗はなし。
- 全体テスト: 368 passed / exit code 1。access violationやfatal stack traceは発生しなかった。
- `git diff --check d876397..HEAD`: 問題なし。
- dependency、packaging、license関連ファイルのMS19差分: なし。

### 15.3 Findings

- P1: なし。
- P2: 解消。`tests/test_wx_ms14_b6_closeout.py` の終了処理で、フレーム破棄前に `_cleanup_analysis_job()` を実行するよう補修し、access violationの再発がないことを確認した。
- P3: なし。

### 15.4 Closeout判定

判定は **A: MS19 Closeout OK** とする。P1 / P2はなく、主要回帰テストと全体テストでaccess violationや新規テスト失敗は確認されなかった。exit code 1は従来から記録されているwx終了コード不安定性として、pass表示と分離して記録する。

B3からB8のユーザー確認結果を再利用し、B9のユーザーチェック通過・問題なしも反映した。Production code、build/package設定は変更していない。変更は対象テストの終了処理補修とCloseout文書同期に限定した。
