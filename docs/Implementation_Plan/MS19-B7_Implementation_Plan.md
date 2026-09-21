# MS19-B7 Implementation Plan

## 1. 文書情報

- Milestone: MS19
- Block: B7
- Title: Error Handling / Tests / Docs
- Status: Completed
- 作成日: 2026-07-09
- 実装状態照合日: 2026-07-10
- 実装日: 2026-07-10
- ユーザーチェック: 2026-07-10 通過・問題なし
- 前提:
  - MS19-B1 / B2 / B3 / B4 / B5 / B6 は完了済み。
  - MS19-B6 のユーザー側確認は通過・問題なし。
  - B6実装およびB7計画は `f4991d0 Implement MS19 B6 and plan B7` でコミット済み。
  - B7実装開始時点の作業ツリーは clean。
- 実装結果:
  - voice_only解析例外を7分類へ整理し、原因要約、再試行方法、例外詳細を表示するhelperを追加した。
  - 解析失敗時は編集済み書き起こしを保持しつつtiming planを無効化し、VMD保存不可へ戻ることをテストした。
  - voice_only VMD保存失敗時は解析結果と保存可否を保持し、成功時以外は出力先履歴を更新しないことをテストした。
  - `tests/conftest.py` で通常pytestのimport pathを安定化し、MS14 closeoutテストの古いTEXT入力fixtureを現行契約へ更新した。
  - 通常の `pytest tests` は360件すべてpass表示まで完走した。既存wxテスト終了処理由来のprocess exit code 1は継続して記録する。
  - README / 配布用readme / Error Handling / Pipeline Data Contract / GUI State仕様を音声のみ入力の実装状態へ同期した。
  - ユーザー側で音声のみ入力のエラー表示と復帰動作を確認し、通過・問題なしと報告された。
- 実装方針サマリ:
  - B7では新機能追加ではなく、音声のみ入力で発生しうる失敗条件、テスト実行状態、ユーザー向け説明を整理する。
  - 既存TEXTあり導線、B6のTEXTなしVMD保存導線、MMD用WAV出力仕様は維持する。
  - README / 配布用readmeには、TEXTあり入力と音声のみ入力の違い、書き起こし編集、VMD保存条件、エラー時の復帰を最小限反映する。

## 2. 背景

MS19-B3からB6により、TEXTファイルなしでも、音声のみ入力からWhisper書き起こし、ひらがな / 母音列生成、timing plan生成、書き起こし編集、編集済み再解析、`current_timing_plan` からのVMD保存まで成立するようになった。

一方で、音声のみ入力は、TEXTあり入力よりも失敗条件が多い。特に、Whisper実行失敗、書き起こし本文なし、timing anchorなし、読み変換失敗、母音列なし、編集済みテキスト空、保存時のtiming plan不整合などは、ユーザーにとって原因が分かりにくい。

現行実装では、これらの多くは `AnalysisWorker` から例外としてGUIへ戻り、`MainFrame._on_analysis_error()` の汎用メッセージ `"解析中にエラーが発生しました。"` で表示される。B7では、音声のみ入力固有の失敗条件を分類し、ユーザーが次に何をすればよいか分かる最小限の文言と状態復帰を整える。

また、B6自動スモークではB6対象テスト36件は通過したが、通常の `pytest tests` は既存のimport path不足で収集停止し、`src` / `tests` を `sys.path` に追加した全体確認では `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件が失敗した。B7では、MS19の完了前にテスト実行方針と既知失敗の扱いを整理する。

README / `readme_mmdautolip.txt` は、まだTEXT 1件 + 音声1件を前提にした説明が中心である。B7では、MS19の音声のみ入力対応をユーザー向け文書へ反映する。

## 3. 目的

- 音声のみ入力に固有のエラー条件を、ユーザー向けに分かる形へ分類する。
- 解析失敗後に古いtiming planやVMD保存可状態が残らないことを確認・必要なら補強する。
- 書き起こし失敗、空本文、読み変換失敗、母音列なし、編集済みテキスト空、VMD保存失敗のテストを整理する。
- B6後の自動テスト実行状態を、限定テスト / 全体テスト / 既知失敗に分けて記録する。
- README / 配布用readme / 関連docsへ、音声のみ入力の使い方と制約を反映する。
- MS19-B9 closeoutへ進めるため、残課題をP1 / P2 / P3で整理する。

## 4. In Scope

- voice_only解析時のユーザー向けエラー文言整理。
- voice_only解析失敗時の状態復帰確認。
- `WhisperTimingError`、`TextProcessingError`、`PipelineError`、編集済みテキスト空の扱い整理。
- 必要最小限のエラー分類helperまたはGUI表示helper追加。
- `AnalysisWorker` / `MainFrame` / `UiState` 周辺の限定的な状態復帰テスト追加。
- `generate_vmd_from_timing_plan()` の保存失敗・空timeline・WAVなしの回帰テスト確認。
- README / `readme_mmdautolip.txt` の音声のみ入力説明追加。
- `docs/Error_Handling_Specification.md` / `docs/Pipeline_Data_Contract_Specification.md` / `docs/GUI_State_Theme_Specification.md` のMS19差分同期。ただし全文改稿はしない。
- `docs/MS17_and_Beyond_Index.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/repo_milestone.md`、`docs/Version_Control.md` のB7実装結果同期。
- 通常の `pytest tests` が収集失敗する件と、`tests/test_wx_ms14_b6_closeout.py` の既存失敗2件の扱い整理。

## 5. Out of Scope

- Whisper model / language 設定UI。
- Whisperの自動ダウンロード導線。
- クラウドAPIまたはネットワーク依存の文字起こし。
- 英語対応・多言語対応。
- VMD writerの全面再設計。
- 音声解析品質アルゴリズムの大幅変更。
- MMD用WAV出力仕様変更。
- 書き起こし履歴の永続化。
- 発音イベント単位の手動編集。
- Qt / PySide6 GUIの復活。
- package / release公開作業。

## 6. 前提条件

- B6により、voice_only解析成功後にTEXT pathなしでVMD保存できる。
- B6により、編集適用直後の未再解析状態ではVMD保存不可である。
- B6対象自動スモーク36件は通過済み。
- 通常の `pytest tests` には、B7開始時点で既存のimport path収集問題がある。
- `src` / `tests` を `sys.path` に追加した全体確認では、B7開始時点で `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件が失敗している。
- README / 配布用readmeは、B7開始時点ではTEXTあり入力中心の説明であり、音声のみ入力のユーザー向け説明が不足している。

## 7. 対象ファイル

主対象:

- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/core/whisper_timing.py`
- `src/core/pipeline.py`
- `src/core/audio_errors.py`

テスト候補:

- `tests/test_ms19_b3_transcription_contract.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_whisper_timing.py`
- `tests/test_text_processing.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- 新規 `tests/test_ms19_b7_voice_only_error_handling.py`
- 必要なら `tests/conftest.py` またはpytest設定。ただし既存テストへの影響を確認してから扱う。

ユーザー向けdocs:

- `README.md`
- `readme_mmdautolip.txt`

関連仕様docs:

- `docs/Error_Handling_Specification.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`

履歴・進行管理docs:

- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

## 8. 実装方針

### 8.1 エラー分類方針

B7では、既存例外をすべて大きく置き換えない。まず、GUI表示前に解析エラーを音声のみ入力向けに分類する最小のhelperを追加する方針とする。

候補分類:

- `voice_only_whisper_failed`
- `voice_only_transcription_empty`
- `voice_only_timing_anchor_failed`
- `voice_only_text_conversion_failed`
- `voice_only_vowel_empty`
- `voice_only_edited_text_empty`
- `voice_only_timing_plan_invalid`
- `voice_only_vmd_save_failed`

この分類は、ユーザー向け表示文言とテスト用の判定に使う。`audio_errors.py` に統合するか、GUI側の小さな分類helperに留めるかは、実装前チェックで既存例外との結合度を見て決める。

### 8.2 GUI表示方針

音声のみ入力で解析に失敗した場合は、単に例外文字列を表示するだけでなく、以下のどれに近いか分かる文言にする。

- 音声から書き起こしを取得できなかった
- 書き起こし結果が空だった
- 書き起こしの読み変換に失敗した
- 母音列を作れなかった
- 編集済みテキストが空で再解析できなかった
- VMD保存に必要な解析結果が不足している

ただし、ユーザーに内部実装名を押し付けない。詳細には例外メッセージを残してよいが、主文は次に取れる行動を示す。

### 8.3 状態復帰方針

解析失敗時:

- 入力音声は保持する。
- TEXTあり入力ではTEXTを保持する。
- voice_onlyでは書き起こし編集状態を不用意に消さない。
- `current_timing_plan` は無効化する。
- `analysis_result_valid` は `False` にする。
- `analysis_pending_rebuild` は、再解析が必要な状態として扱う。
- VMD保存は不可にする。
- Busy状態、進捗ダイアログ、worker参照は必ず解除する。

保存失敗時:

- 解析結果は保持する。
- VMD保存可否は解析結果の有効性に基づいて維持してよい。
- 保存失敗を解析失敗として扱わない。

### 8.4 テスト整理方針

B7では、MS19に必要な対象テストを優先する。

最小対象:

- voice_only Whisper失敗時に解析成功扱いにならない
- voice_only 空書き起こしで解析成功扱いにならない
- voice_only 編集済みテキスト空で再解析へ進まない
- voice_only 解析失敗後はVMD保存不可
- voice_only VMD保存失敗後も解析結果は保持される
- TEXTあり保存導線が壊れていない
- README / readmeにTEXTあり / 音声のみの使い分けが記載されている

通常の `pytest tests` の収集問題は、B7で以下のどちらかを選ぶ。

1. テスト設定を修正し、通常の `pytest tests` を収集可能にする。
2. 収集問題が古いテスト構造由来でB7範囲を超える場合、MS19-B9 closeoutの既知残課題として記録し、B7では限定テストコマンドを正とする。

推奨は、影響が小さい場合に限り `tests/conftest.py` などで `src` / `tests` のimport pathを安定化すること。ただし、既存テストに広く影響する場合は無理に直さない。

`tests/test_wx_ms14_b6_closeout.py` の既存失敗2件は、B7実装前チェックで現行GUI仕様との齟齬かテスト側の古い前提かを分類する。B7の保存・エラー処理と無関係な場合は、MS19-B9のcloseout判断材料として記録する。

### 8.5 Documentation方針

README / `readme_mmdautolip.txt` には以下を反映する。

- TEXTあり入力と音声のみ入力の両方に対応していること。
- 音声のみ入力では書き起こし結果を確認・編集できること。
- 編集適用後は再解析が必要であること。
- 解析成功後にVMD保存できること。
- MMD用WAV出力はVMD保存と自動連動しないことを維持すること。
- 書き起こし精度やタイミングは自動処理であり、最終確認はMMD側で必要であること。
- Whisper / FFmpeg / 音声状態によって解析に失敗する場合があること。

仕様docsは、実装状態との差分を最小同期する。過去の仕様全体を書き換えない。

## 9. 詳細ステップ

1. B6差分と作業ツリーを確認する。
   - `git status --short --branch`
   - B7開始時点ではB6実装とB7計画がコミット済みであることを確認する

2. B7対象の失敗条件を実装状態から棚卸しする。
   - `AnalysisWorker` のvoice_only分岐
   - `extract_transcription_text()`
   - `build_vowel_timing_plan()`
   - `generate_vmd_from_timing_plan()`
   - `MainFrame._on_analysis_error()`
   - `AppController.request_save_vmd()`

3. エラー分類helperの追加要否を決める。
   - GUI側helperで足りるか確認する
   - `audio_errors.py` へ拡張する場合は、既存音声変換エラーとの責務境界を崩さない

4. voice_only解析失敗時の表示と状態復帰を実装する。
   - 汎用例外表示から、原因カテゴリが分かる表示へ寄せる
   - 解析失敗後はVMD保存不可にする
   - 入力と編集状態は必要以上に消さない

5. voice_only保存失敗時の表示と状態維持を確認する。
   - VMD保存失敗を解析失敗として扱わない
   - 保存先エラー・WAVなし・空timelineをテストする

6. テストを追加・更新する。
   - 新規B7テストを追加する
   - B6対象テストを維持する
   - 通常 `pytest tests` の収集問題と既存closeout失敗を分類する

7. README / `readme_mmdautolip.txt` を更新する。
   - 使い方をTEXTあり / 音声のみの2系統に分ける
   - 音声のみ入力の注意事項とエラー時の行動を追加する

8. 関連仕様docsを同期する。
   - Error Handling
   - Pipeline Data Contract
   - GUI State / Theme

9. 履歴・進行管理docsを同期する。
   - MS19 Block Breakdown
   - MS17 and Beyond Index
   - Roadmap
   - repo_milestone
   - Version_Control

10. 対象テストを実行し、結果を記録する。

## 10. 状態遷移 / データ契約

### 10.1 voice_only 初回解析失敗

期待状態:

- `input_mode = voice_only`
- 入力音声は保持
- `analysis_result_valid = False`
- `current_timing_plan = None`
- `analysis_pending_rebuild = True`
- VMD保存不可
- 書き起こし結果は、成功していない限り保存用正本として扱わない

### 10.2 voice_only 書き起こし編集適用後の再解析失敗

期待状態:

- 編集済みテキストは保持
- `analysis_text_source = user_edited_transcription`
- `analysis_result_valid = False`
- `current_timing_plan = None`
- `analysis_pending_rebuild = True`
- VMD保存不可
- ユーザーが再編集または再解析できる

### 10.3 voice_only VMD保存失敗

期待状態:

- `analysis_result_valid = True` は維持してよい
- `current_timing_plan` は維持してよい
- VMD保存可否は入力と解析結果に基づいて維持してよい
- `last_vmd_output_dir` は成功時のみ更新する
- ステータスはVMD保存失敗

### 10.4 TEXTあり入力

期待状態:

- 既存TEXTあり解析・保存導線を維持する
- B7のエラー表示改善でTEXTあり導線の成功条件を変えない

## 11. テスト方針

### 11.1 Targeted tests

実装後は最低限以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b7_voice_only_error_handling.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b5_transcription_edit_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py
```

### 11.2 Full test handling

通常の全体テスト:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

B7開始時点では収集時import path不足が確認されているため、B7では以下を明示的に判断する。

- 通常全体テストを通せるようにテスト設定を直す
- または、B7内では限定テストを正とし、全体テストの既知問題をB8へ渡す

### 11.3 Documentation checks

以下を検索し、古いTEXT必須記述が残っていないか確認する。

```powershell
rg -n "TEXT 1 件|TEXT 1件|テキストファイルと音声ファイル|音声のみ|書き起こし|VMD保存" README.md readme_mmdautolip.txt docs
```

## 12. 受け入れ条件

- 音声のみ入力の代表的な失敗条件がユーザー向けに分類されている。
- 解析失敗後に古いtiming planを保存可能状態として扱わない。
- 編集済みテキスト空や変換失敗が、成功状態として扱われない。
- VMD保存失敗時に解析結果まで失わない。
- B6で実装したTEXTなしVMD保存が壊れていない。
- TEXTあり入力の既存導線が壊れていない。
- README / `readme_mmdautolip.txt` に音声のみ入力の使い方と注意点が反映されている。
- Error Handling / Pipeline Data Contract / GUI State docs がMS19実装状態と矛盾していない。
- B7対象テストが通過している。
- 通常 `pytest tests` の結果または既知問題の扱いが明記されている。
- 新規依存を追加していない。
- Qt / PySide6を復活させていない。

## 13. リスクと対策

### R1. エラー分類追加が大規模化する

リスク:

- エラー情報モデル全体を作り直すと、B7の範囲を超える。

対策:

- B7ではvoice_only解析・保存に必要な最小分類に留める。
- 既存 `audio_errors.py` の責務を崩さない。

### R2. Whisper不足結果の扱いを品質改善へ広げすぎる

リスク:

- anchorなしfallbackや解析品質改善に広げると、MS19-B7のエラー整理から外れる。

対策:

- B7では失敗を分かりやすく通知し、状態を安全に戻すことを優先する。
- fallback方針変更が必要な場合はP2/P3として記録し、実装はユーザー判断を挟む。

### R3. README更新で未実装機能を完了扱いする

リスク:

- 音声のみ入力の説明が過剰になり、英語対応、多言語対応、精密な音素解析までできるように読める。

対策:

- 日本語音声中心、5母音モーフ固定、自動生成補助、MMD側確認必須を明記する。

### R4. 全体pytestの既存問題をB7で無理に直す

リスク:

- 古いテスト前提や広範囲のテスト環境をB7で変更すると、MS19範囲を超える。

対策:

- import path安定化のような小規模修正に限定する。
- `test_wx_ms14_b6_closeout.py` の失敗は、B7との関連性を確認してから扱う。
- 無関係ならB9 closeoutの既知残課題として記録する。

### R5. 既存TEXTあり導線の回帰

リスク:

- voice_only向けエラー表示を追加する過程で、TEXTあり解析・保存の挙動が変わる。

対策:

- `input_mode` で処理を分ける。
- TEXTありの保存・解析テストをB7対象テストに含める。

## 14. Codex 実装時の注意

- 実装前に `git status --short --branch` を確認する。
- B6実装とB7計画がコミット済みの状態を前提にする。
- B7はエラー処理・テスト・docs同期のBlockであり、新しいユーザー機能を追加しない。
- README / readme更新では、実装済みの範囲だけを書く。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- wxPython main lineのみ変更する。
- Qt / PySide6関連ファイルには触れない。
- shell commandは並列実行しない。
- shell pipeline / chained commandは避ける。
- B6のTEXTなしVMD保存導線を壊さない。
- B7実装後レポートでは、代表エラー条件、状態復帰、実行テスト、全体pytestの扱い、docs更新範囲を明示する。
