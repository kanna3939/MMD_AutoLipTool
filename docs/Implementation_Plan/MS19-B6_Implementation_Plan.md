# MS19-B6 Implementation Plan

## 1. 文書情報

- Milestone: MS19
- Block: B6
- Title: VMD / Preview / Save Integration
- Status: Implemented
- 作成日: 2026-07-08
- 実装状態照合日: 2026-07-09
- 実装日: 2026-07-09
- ユーザーチェック: 2026-07-09 通過・問題なし
- 前提:
  - MS19-B1 / B2 / B3 / B4 / B5 は完了済み。
  - MS19-B5 のユーザー側確認は通過・問題なし。
  - B5実装およびB6計画は `979b536 Implement MS19 B5 and plan B6` でコミット済み。
  - B6実装開始時点の作業ツリーは clean。
- 実装結果:
  - `generate_vmd_from_timing_plan()` により、TEXT pathなしで `current_timing_plan` からVMD保存できる入口を追加した。
  - voice_only解析成功後はVMD保存を有効化し、編集適用直後の未再解析状態では保存不可にする状態契約を実装した。
  - B4/B5由来の保存不可期待値テストをB6後の仕様へ更新し、対象テスト36件の通過を確認した。
  - ユーザー側のB6確認は通過・問題なし。
- 実装方針サマリ:
  - 既存TEXTあり保存経路 `generate_vmd_from_text_wav()` は維持する。
  - 音声のみ入力では `selected_text_path` を要求せず、B5までに確定した `current_timing_plan` からVMDを書き出す別入口を追加する。
  - Preview表示は既存の `current_timing_plan` 追従を活かし、B6では保存可否・ステータス文言・保存実行契約を主対象にする。

## 2. 背景

MS19-B4 では、wxPython GUI上でTEXTなし音声のみ入力から解析を開始し、Whisper書き起こし結果とtiming planを得られるようにした。ただしB4時点では、音声のみ解析後もVMD保存は無効のままとした。

MS19-B5 では、音声のみ解析結果の書き起こし編集、編集後のひらがな / 母音列preview更新、保持済み `WhisperTimingResult` による編集済みテキスト再解析を実装した。編集済み再解析成功後は `current_timing_plan` が編集済みテキスト由来へ更新され、既存Previewはその `current_timing_plan` に追従できる状態になっている。

一方、B6実装前のVMD保存経路はTEXTあり入力を前提としていた。`UiState.vmd_save_ready` は `input_mode == text_audio` と `selected_text_path` を要求し、`AppController.request_save_vmd()` は `generate_vmd_from_text_wav(text_path=...)` を呼んでいた。`src/core/pipeline.py` の `PipelineResult` も `text_path: Path` を必須としており、TEXTなし音声のみ入力の保存契約には合っていなかった。

B6では、B5までに得た音声のみ用 `current_timing_plan` をVMD保存へ接続し、MS19全体の「TEXTなしでもVMD保存できる」条件を満たす最小実装を行う。

2026-07-09 に、TEXTなし保存入口、voice_only保存可否判定、`AppController.request_save_vmd()` の保存分岐、ステータス文言更新、関連テスト更新を実装した。B6実装後は、音声のみ解析成功後に `current_timing_plan` からVMD保存できる。編集適用直後は `analysis_pending_rebuild == True` かつ `current_timing_plan is None` のため、引き続きVMD保存不可である。

同日に、ユーザー側のB6確認は通過・問題なしと報告された。音声のみ解析後のTEXTなしVMD保存、編集適用直後の保存不可、編集済み再解析後の保存可、既存TEXTあり導線について、B6内で追加の仕様修正が必要な問題は報告されていない。

## 3. 目的

- 音声のみ入力の解析成功後、VMD保存ボタンとメニューを有効化できるようにする。
- 音声のみ入力で `selected_text_path` がない場合でも、現在の `current_timing_plan` からVMDを書き出せるようにする。
- 編集適用後の未再解析状態では、古いtiming planをVMD保存へ流さない。
- 既存TEXTあり入力の保存導線、Preview表示、MMD用WAV出力導線を壊さない。
- B6後の状態を、B7のエラー処理 / README / docs同期へ渡せるようにする。

## 4. In Scope

- `UiState.vmd_save_ready` を、TEXTあり保存と音声のみ保存の両方に対応する状態契約へ拡張する。
- 音声のみ入力では、以下を満たす場合だけVMD保存可能にする。
  - `analysis_result_valid == True`
  - `current_timing_plan is not None`
  - `input_mode == voice_only`
  - `analysis_pending_rebuild == False`
  - `analysis_text_content` または `transcription_text` が存在する
  - `selected_wav_path` または `selected_analysis_wav` が存在する
- voice_only保存時の音声パスは、既存TEXTあり保存と同じく `selected_analysis_wav.analysis_wav_path` を優先し、存在しない場合は `selected_wav_path` を使う。
- `src/core/pipeline.py` に、TEXT pathを要求しないVMD保存入口を追加する。
- `AppController.request_save_vmd()` で、TEXTあり / voice_only の保存経路を分岐する。
- voice_only保存成功後も、既存の `last_vmd_output_dir` 更新、ステータス更新、設定保存要求を維持する。
- 音声のみ解析成功後のステータス文言を、B4/B5の「TEXTなしVMD保存は未対応」からB6後の状態に合わせて更新する。
- Preview表示が `current_timing_plan` に基づいて表示されることを、既存経路またはテストで確認する。
- B4/B5で追加した「未適用編集ガード」「編集適用後は再解析待ち」の契約を保存可否にも反映する。
- 既存TEXTあり保存テスト、B4/B5 voice_onlyテストをB6後の期待値へ更新する。

## 5. Out of Scope

- VMD writer の全面再設計。
- 既存 `generate_vmd_from_text_wav()` の破壊的な契約変更。
- 音声のみ入力時の高度な保存オプション追加。
- MMD用WAV出力仕様の変更。
- Preview UI の大規模刷新。
- 再生タイムライン操作の再設計。
- 書き起こし履歴の永続化。
- Whisper model / language 設定UI。
- Qt / PySide6 GUI の復活。
- package / release 公開作業。

## 6. 前提条件

- MS19-B5により、音声のみ解析結果の書き起こし編集と編集済み再解析が実装済みである。
- 音声のみ解析成功後、`UiState.current_timing_plan` には voice_only 由来の `VowelTimingPlan` が保持される。
- 編集適用直後は `UiState.invalidate_analysis()` により `current_timing_plan` が `None` になり、`analysis_pending_rebuild == True` になる。
- 編集済み再解析成功後は、`analysis_pending_rebuild == False` になり、`current_timing_plan` が編集済みテキスト由来として扱える。
- 既存Previewは `MainFrame._update_preview_display()` で `current_timing_plan` から描画データを生成する。
- 既存TEXTあり保存は、`generate_vmd_from_text_wav()` と `selected_text_path` 契約を維持する。

## 7. 対象ファイル

主対象:

- `src/core/pipeline.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`

必要に応じて確認:

- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/preview_panel.py`
- `src/vmd_writer/writer.py`

テスト候補:

- `tests\test_ms19_b4_voice_only_gui_state.py`
- `tests\test_ms19_b5_transcription_edit_state.py`
- `tests\test_wx_ms14_b2_state.py`
- `tests\test_wx_ms14_b5_export.py`
- `tests\test_pipeline_and_vmd.py`
- 新規 `tests\test_ms19_b6_voice_only_vmd_save.py`

関連ドキュメント:

- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

## 8. 実装方針

### 8.1 保存入口方針

B6では、既存の `generate_vmd_from_text_wav()` をTEXTあり入力専用の安定した入口として維持する。

音声のみ入力向けには、`current_timing_plan` から直接VMDを書き出す新規関数を `src/core/pipeline.py` に追加する方針とする。

候補名:

- `generate_vmd_from_timing_plan()`

想定入力:

- `wav_path`
- `output_path`
- `timing_plan`
- `model_name`
- `silence_threshold`
- `closing_hold_frames`
- `closing_softness_frames`

この入口はTEXTファイルを読まない。`upper_limit` はtiming plan構築時に反映済みの値であり、確定済み `timing_plan` を書き出すだけの保存入口では追加入力にしない。`timing_plan` の空timeline、非正duration、出力失敗を `PipelineError` として扱う。

非正durationのtimelineを受け取った場合は、既存 `generate_vmd_from_text_wav(..., timing_plan=...)` と同様に、`wav_path` からWAV解析を行い、speech intervalを使ってdurationを補完する。通常のB5/B6 voice_only経路では `build_vowel_timing_plan()` 済みのpositive duration timelineが渡る想定である。

`PipelineResult.text_path` を optional に変える案は、既存TEXTありテストと利用側への影響が大きいためB6では採用しない。必要な場合は、TEXTなし保存用の軽量な戻り値データ構造を別に追加する。

### 8.2 `UiState.vmd_save_ready` 方針

TEXTあり入力:

- 既存と同じく、解析成功済み、`current_timing_plan` あり、`input_mode == text_audio`、`selected_text_path` ありの場合に保存可能。

音声のみ入力:

- `input_mode == voice_only`
- `analysis_ready == True`
- `analysis_pending_rebuild == False`
- `analysis_text_content` または `transcription_text` あり
- `selected_wav_path` または `selected_analysis_wav` あり

編集適用直後は `analysis_pending_rebuild == True` かつ `current_timing_plan is None` になるため保存不可にする。

### 8.3 `AppController.request_save_vmd()` 方針

`request_save_vmd()` は、保存ダイアログ表示前に `st.vmd_save_ready` を確認する。

保存ダイアログ後:

- TEXTあり入力: 既存どおり `generate_vmd_from_text_wav()` を呼ぶ。
- voice_only入力: 新規 `generate_vmd_from_timing_plan()` を呼ぶ。

voice_only保存時の `wav_path` は、`selected_analysis_wav.analysis_wav_path` を優先し、存在しない場合のみ `selected_wav_path` を使う。これは既存TEXTあり保存時の音声パス選択と揃える。

voice_only保存時も、出力先ディレクトリ更新、ステータス `"VMD保存成功"`、設定保存要求は既存TEXTありと同じにする。

### 8.4 Preview方針

B5時点で、解析成功後の `sync_ui_state()` は `_update_preview_display()` を呼び、`current_timing_plan` から `build_preview_data()` を実行する。

B6ではPreview描画ロジックを大きく変更しない。確認すべき点は以下に限定する。

- voice_only解析成功後に `current_timing_plan` がある場合、Preview placeholderではなくpreview dataが設定される。
- 編集適用直後はPreviewが未解析 / 再解析待ち扱いになる。
- 編集済み再解析成功後は、編集済み `current_timing_plan` に基づくPreviewへ戻る。

### 8.5 ステータス文言方針

B4/B5では voice_only解析成功時に `"解析完了 (TEXTなしVMD保存は未対応)"` と表示していた。

B6後は、保存可能な状態では `"解析完了 (VMD出力可能)"` または同等の文言へ戻す。未再解析状態では既存の `"入力が変更されました (再解析が必要)"` 系の表示を維持する。

### 8.6 MMD用WAV出力との整合

MMD用WAV出力はMS17-B7の既存導線を維持する。B6では、音声のみVMD保存が可能になっても、MMD用WAV出力仕様や保存先決定、stereo固定方針は変更しない。

## 9. 詳細ステップ

1. B5実装後のリポジトリ状態を確認する。
   - `git status --short --branch`
   - B5対象コードが `979b536` でコミット済みであることを前提にする

2. `src/core/pipeline.py` にTEXTなし保存入口を追加する。
   - `generate_vmd_from_timing_plan()` を追加する
   - 空timelineを拒否する
   - non-positive durationがある場合の扱いを既存 `generate_vmd_from_text_wav()` と揃える
   - `upper_limit` は保存入口の入力にしない
   - `write_morph_vmd()` の呼び出し方は既存関数と揃える

3. `src/gui_wx/ui_state.py` の `vmd_save_ready` を拡張する。
   - TEXTあり条件を維持する
   - voice_only条件を追加する
   - `analysis_pending_rebuild` 中は保存不可にする

4. `src/gui_wx/app_controller.py` の保存分岐を実装する。
   - TEXTありは既存関数
   - voice_onlyは新規関数
   - 保存失敗時のMessageBoxとステータスは既存と揃える

5. `src/gui_wx/main_frame.py` のステータス文言とボタン状態を確認・更新する。
   - voice_only保存可能時に保存ボタン / メニューが有効になる
   - 未再解析状態では無効になる
   - `"TEXTなしVMD保存は未対応"` の文言をB6後の状態へ更新する

6. Preview追従を確認する。
   - 既存 `_update_preview_display()` が voice_only `current_timing_plan` で動くことを確認する
   - 必要最小限のテストを追加する

7. 既存テストをB6後の期待値へ更新する。
   - B4の「voice_only保存不可」テストを、B6では保存可能テストへ更新またはB4歴史テストとして整理する
   - B5の編集適用後保存不可 / 再解析後保存可を追加する

8. 関連ドキュメントを同期する。
   - B6実装結果は、実装後にMS19 Block Breakdown / Index / Roadmap / history docsへ反映する
   - README / 配布用readmeへのユーザー向け説明はB7でまとめる

## 10. 状態遷移 / データ契約

### 10.1 TEXTあり解析成功後

保存可否:

- `input_mode = text_audio`
- `selected_text_path` あり
- `current_timing_plan` あり
- `analysis_result_valid = True`
- VMD保存可

保存入口:

- `generate_vmd_from_text_wav(text_path=selected_text_path, timing_plan=current_timing_plan, ...)`

### 10.2 音声のみ初回解析成功後

保存可否:

- `input_mode = voice_only`
- `analysis_text_source = whisper_transcription`
- `transcription_text` あり
- `current_timing_plan` あり
- `analysis_result_valid = True`
- `analysis_pending_rebuild = False`
- VMD保存可

保存入口:

- `generate_vmd_from_timing_plan(timing_plan=current_timing_plan, ...)`

### 10.3 音声のみ編集適用直後

保存可否:

- `input_mode = voice_only`
- `analysis_text_source = user_edited_transcription`
- `analysis_pending_rebuild = True`
- `current_timing_plan = None`
- VMD保存不可

理由:

- 編集前timing planを編集後テキスト由来として扱わないため。

### 10.4 音声のみ編集済み再解析成功後

保存可否:

- `input_mode = voice_only`
- `analysis_text_source = user_edited_transcription`
- `transcription_is_edited = True`
- `current_timing_plan` あり
- `analysis_result_valid = True`
- `analysis_pending_rebuild = False`
- VMD保存可

保存入口:

- `generate_vmd_from_timing_plan(timing_plan=current_timing_plan, ...)`

## 11. テスト方針

### 11.1 Core tests

- `generate_vmd_from_timing_plan()` がTEXT pathなしで `write_morph_vmd()` を呼べること。
- 空timelineを `PipelineError` として拒否すること。
- non-positive durationのtimelineについて、既存関数と同等に扱うこと。
- 既存 `generate_vmd_from_text_wav()` の挙動が変わらないこと。

### 11.2 GUI state tests

- TEXTあり解析成功後、VMD保存が有効であること。
- voice_only初回解析成功後、VMD保存が有効であること。
- voice_only編集適用直後、VMD保存が無効であること。
- voice_only編集済み再解析成功後、VMD保存が有効であること。
- busy中は保存ボタン / メニューが無効であること。

### 11.3 Controller tests

- TEXTあり保存では既存 `generate_vmd_from_text_wav()` が呼ばれること。
- voice_only保存では新規 `generate_vmd_from_timing_plan()` が呼ばれること。
- voice_only保存で保存ダイアログが表示され、キャンセル時は出力関数を呼ばないこと。
- 保存成功時に `last_vmd_output_dir` とステータスが更新されること。
- 保存失敗時に既存と同じエラー表示方針を使うこと。

### 11.4 Preview tests

- voice_only解析成功後、`current_timing_plan` に基づいてPreview dataが設定されること。
- `current_timing_plan is None` のときは未解析placeholderへ戻ること。

### 11.5 実行候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b6_voice_only_vmd_save.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b5_transcription_edit_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py
```

## 12. 受け入れ条件

- 音声のみ解析成功後、VMD保存ボタンとメニューが有効になる。
- 音声のみ入力で `selected_text_path` がなくてもVMDを書き出せる。
- voice_only保存時にTEXTファイル読み込みを要求しない。
- 編集適用直後の未再解析状態ではVMD保存できない。
- 編集済み再解析成功後は、編集済みテキスト由来の `current_timing_plan` でVMD保存できる。
- TEXTあり入力の既存VMD保存導線が壊れていない。
- Previewがvoice_onlyの `current_timing_plan` に追従する。
- MMD用WAV出力仕様を変更していない。
- Qt / PySide6 依存を追加しない。
- 新規依存を追加しない。

## 13. リスクと対策

### R1. TEXTなし保存のために既存 `PipelineResult` を壊す

リスク:

- `PipelineResult.text_path` をoptional化すると、既存TEXTあり保存テストや利用側に影響が広がる。

対策:

- B6ではTEXTなし保存用の別入口と必要なら別戻り値を追加する。
- 既存 `generate_vmd_from_text_wav()` のシグネチャは維持する。

### R2. 編集前timing planを誤って保存する

リスク:

- B5で編集適用した直後に、古いtiming planをVMD保存すると、表示テキストと出力内容が不一致になる。

対策:

- `analysis_pending_rebuild` と `current_timing_plan` の両方で保存可否を判定する。
- 編集適用直後の保存不可テストを追加する。

### R3. B4/B5のvoice_onlyテストと期待値が衝突する

リスク:

- B4時点の「voice_only保存不可」テストがB6仕様と矛盾する。

対策:

- B6実装時に該当テストをB6後の期待値へ更新する。
- B4の歴史的事実はドキュメントで保持し、現行回帰テストは最新仕様を正とする。

### R4. Preview範囲が広がりすぎる

リスク:

- B6でPreview操作や再生タイムラインまで広げると、MS19-B7/B8前に範囲が膨らむ。

対策:

- B6では `current_timing_plan` 表示追従の確認に留める。
- Preview操作や高度な編集導線は扱わない。

### R5. MMD用WAV出力とVMD保存の責務混同

リスク:

- 音声のみVMD保存対応と同時にMMD用WAV出力仕様まで変更すると、配布・互換性リスクが増える。

対策:

- B6ではMMD用WAV出力仕様を変更しない。
- 既存ボタン状態・出力導線が壊れていないことだけ確認する。

## 14. Codex 実装時の注意

- 実装前に `git status --short --branch` を確認する。
- B6実装開始時点ではB5実装差分は `979b536` でコミット済み。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- wxPython main line のみ変更する。
- Qt / PySide6 関連ファイルには触れない。
- shell command は並列実行しない。
- shell pipeline / chained command は避ける。
- 既存TEXTあり保存導線を壊さない。
- B6実装後レポートでは、音声のみVMD保存が有効化された条件と、編集適用直後は保存不可であることを明示する。
