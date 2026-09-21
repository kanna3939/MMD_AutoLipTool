# MS19 Block Breakdown

## 1. 文書情報

- 文書名: MS19 Block Breakdown
- 想定配置先: `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 対象マイルストーン: MS19
- 基準ブランチ: `feature/MS19`
- 正本:
  - `feature/MS19`
  - 分岐元: `main` / `d876397 Close out MS18`
- 関連ロードマップ:
  - `docs/MS18_and_Beyond_Roadmap.md`
- 作成日: 2026-07-03
- 文書ステータス: Draft
- 現在ステータス:
  - MS18 CloseOut 完了
  - MS18 closeout 判定: A. MS18 closeout OK。package 化へ進める。
  - MS18-B6由来のpackage化前P2はユーザー判断によりクリア扱い
  - MS18-B7の実MMD確認はユーザー確認通過・問題なし
  - MS19-B1 Voice-only Input Requirements / State Contract 完了
  - MS19-B2 Transcription Pipeline Pre-check 完了
  - MS19-B3 Textless Pipeline Integration Foundation 完了
  - MS19-B4 GUI Entry Point and State Handling 完了
  - MS19-B5 Review / Edit Transcription Result Flow 完了。ユーザー側B5確認通過・問題なし
  - MS19-B6 VMD / Preview / Save Integration 完了。ユーザー側B6確認通過・問題なし
  - MS19-B7 Error Handling / Tests / Docs 完了。自動テスト完走、ユーザー確認通過・問題なし
  - MS19-B8 Workspace Reset / New Session Flow 完了。ユーザースモークテスト通過・問題なし
  - MS19 CloseoutはB9で完了
  - MS19-B9 MS19 Closeout 完了。判定A
  - ユーザーチェック通過・問題なし

## 2. 背景

MS17では、wxPython 主系上で wav / mp3 / m4a 音声入力、解析用WAV生成、MMD用WAV出力、音声処理 worker 化、Busy制御、キャンセル導線、Preview / waveform 連携、MS17-B9 closeout まで完了した。

MS18では、Release Readiness / Refactor / Security Hardening として、FFmpeg / ffprobe探索元説明性改善、解析用WAV再生時のMCI向け短い一時ファイル名対応、SmokeLaunch停止待機、Release / Packaging / License Preflight、実MMD確認を完了した。

MS19では、MS18の安定化作業とは切り離し、TEXT 必須前提を外して、音声ファイルのみから最低限の VMD 生成を成立させる。

## 3. MS19の位置づけ

MS19は、Voice-only Input のマイルストーンである。

現行実装では、解析実行とVMD保存の中心契約は TEXT あり入力を前提としている。

- `src/core/pipeline.py`
  - `generate_vmd_from_text_wav()` は `text_path` の存在とUTF-8読み込みを必須にしている。
  - `build_vowel_timing_plan()` は `text_content` から母音列を生成する。
- `src/gui_wx/main_frame.py`
  - `解析実行` は `selected_text_path` と音声入力の両方が揃った場合のみ有効になる。
  - `_run_analysis()` は `selected_text_content` が空の場合にエラーとする。
- `src/gui_wx/analysis_worker.py`
  - `AnalysisWorker` は `text_content` を受け取り、`build_vowel_timing_plan()` へ渡す。
- `src/gui_wx/app_controller.py`
  - VMD保存時に `generate_vmd_from_text_wav()` へ `selected_text_path` を渡す。

MS19では、上記の TEXT あり導線を壊さず、TEXTなしの場合だけ音声認識結果を入力テキスト相当の正本として扱うための状態契約を追加する。

## 4. MS19で扱うもの

MS19で扱うものは以下とする。

- 音声のみ入力モードの仕様定義
- TEXT あり / TEXT なしの状態分岐
- 日本語音声の書き起こし導線
- 書き起こし結果の確認・編集方針
- 書き起こし結果からの日本語読み生成
- 日本語読みからの5母音列変換
- 既存 timing pipeline への接続
- Preview / waveform / VMD保存との整合
- 音声のみ入力時のエラー処理
- wxPython GUI導線
- 既存TEXTあり入力の回帰テスト
- README / docs 同期

## 5. MS19で扱わないもの

MS19では、以下を扱わない。

- 英語対応
- 多言語対応
- クラウドAPI依存
- 自動ダウンロード
- Whisper model 管理の大規模UI
- 任意モーフ対応
- モーフ編集機能
- VMD writer の全面再設計
- pipeline の品質アルゴリズム全面変更
- GUI レイアウト刷新
- Qt / PySide6 GUI の復活
- package / release 公開作業

## 6. MS19全体の受け入れ条件

MS19全体の完了条件は以下とする。

- TEXTなしで音声ファイルのみを読み込める
- 音声のみ入力から書き起こし結果を得られる
- 書き起こし結果から日本語読み・母音列を生成できる
- 既存 timing pipeline へ接続できる
- Preview / waveform 上で結果を確認できる
- VMD 保存できる
- TEXTあり入力の既存導線が壊れていない
- 音声のみ入力時の制約とエラーがユーザーに分かる形で通知される
- README / docs に TEXTあり / TEXTなしの違いが説明されている

## 7. MS19 Block 一覧

```text
MS19-B1: Voice-only Input Requirements / State Contract
MS19-B2: Transcription Pipeline Pre-check
MS19-B3: Textless Pipeline Integration Foundation
MS19-B4: GUI Entry Point and State Handling
MS19-B5: Review / Edit Transcription Result Flow
MS19-B6: VMD / Preview / Save Integration
MS19-B7: Error Handling / Tests / Docs
MS19-B8: Workspace Reset / New Session Flow
MS19-B9: MS19 Closeout
```

## 8. Block依存関係

```text
MS19-B1
  ↓
MS19-B2
  ↓
MS19-B3
  ↓
MS19-B4
  ↓
MS19-B5
  ↓
MS19-B6
  ↓
MS19-B7
  ↓
MS19-B8
  ↓
MS19-B9
```

原則として、上記順に進める。

B1で TEXTあり / TEXTなしの状態契約を固定するまで、実装には入らない。

B2で既存 `whisper_timing` と書き起こし本文の扱いを確認したうえで、B3以降の実装単位を確定する。

B5の review / edit flow は、B3 / B4で最低限の音声のみ導線が成立した後に扱う。

B6の VMD / Preview / Save Integration は、B3からB5までの状態契約が安定した後に実施済みである。

## 9. MS19-B1: Voice-only Input Requirements / State Contract

### 9.0 ステータス

完了。

2026-07-04 に `feature/MS19` 上で、現行TEXT必須導線、Whisper / text_processing 既存契約、TEXTあり / TEXTなし状態契約、VMD保存時の `text_path` 依存、MS19-B2以降への引き継ぎを確認した。

コード変更、GUI変更、テスト追加は行っていない。

### 9.1 目的

MS19-B1では、音声のみ入力対応の実装に入る前に、TEXTあり / TEXTなしの状態契約、入力正本、生成物、エラー分類、次Blockの作業範囲を固定する。

このBlockでは、実装変更を行わない。

### 9.2 In Scope

- 現行TEXT必須導線の確認
- 音声のみ入力時の入力正本定義
- TEXTあり / TEXTなしの状態遷移定義
- 書き起こし結果、ひらがな、母音列の保持方針定義
- 既存 `text_processing` との接続方針定義
- 既存 `whisper_timing` との接続方針定義
- Preview / VMD保存までの後続Block境界整理
- MS19-B2以降への引き継ぎ整理

### 9.3 Out of Scope

- コード変更
- GUI変更
- Whisper実行経路の変更
- 新しい依存関係追加
- VMD writer変更
- Preview / waveform仕様変更
- package / release作業

### 9.4 成果物

- `docs/Implementation_Plan/MS19-B1_Implementation_Plan.md`
- TEXTあり / TEXTなし状態契約
- MS19-B2以降の作業境界
- 実装前に確認すべき対象ファイル一覧

### 9.5 受け入れ条件

- TEXTあり既存導線を壊さない方針が明記されている
- 音声のみ入力時の入力正本が定義されている
- `selected_text_path` が存在しない場合の代替契約が定義されている
- 書き起こし結果、ひらがな、母音列の保持方針が定義されている
- 実装変更が行われていない

## 10. MS19-B2: Transcription Pipeline Pre-check

### 10.0 ステータス

完了。

2026-07-04 に `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md` を作成し、B2の対象を `whisper_timing.py` のraw result保持、transcription本文抽出候補、timing anchor契約、エラー分類、既存テスト不足確認に限定した。

2026-07-05 に `feature/MS19` 上で、既存 `whisper_timing.py` / `pipeline.py` / `text_processing.py` / Error Handling仕様 / 既存テストを確認し、transcription本文抽出の第一候補を `segments[].text`、fallback候補を `raw_result["text"]` としてB3へ引き継ぐ方針を整理した。

production code変更、GUI変更、テスト追加は行っていない。対象テスト21件は通過した。

### 10.1 目的

既存 `whisper_timing.py` を、音声のみ入力の書き起こし本文取得に使えるか確認し、必要な最小追加契約を定義する。

### 10.2 In Scope

- `recognize_audio()` のraw result確認
- `recognize_audio_timing()` のtiming anchor契約確認
- segment / word text の扱い確認
- Whisper失敗時のエラー分類確認
- 既存テスト `tests/test_whisper_timing.py` の不足確認

### 10.3 Out of Scope

- Whisper model管理UI
- 自動モデルダウンロード導線
- クラウド文字起こし
- 英語音声対応

### 10.4 成果物

- `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md`
- transcription本文抽出候補の比較結果
- Whisper raw result / timing anchor の契約確認結果
- B3で追加するproduction code候補
- B3で追加するテスト候補

### 10.5 受け入れ条件

- `recognize_audio()` のraw result契約が確認されている
- `recognize_audio_timing()` の `raw_result` 保持契約が確認されている
- segment text / word text / raw text の本文抽出候補が比較されている
- 音声のみ入力の `transcription_text` 初期値候補が定義されている
- Whisper失敗、空本文、空anchorの扱いが分類されている
- 既存テストの不足が整理されている
- B3へ渡すproduction code変更候補が明記されている
- production code変更を行っていない、または行った場合はユーザー承認と理由が記録されている

## 11. MS19-B3: Textless Pipeline Integration Foundation

### 11.0 ステータス

完了。

2026-07-05 に `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md` を作成し、B3の対象をWhisper raw resultからの本文抽出helper、既存 `WhisperTimingResult` を再利用できる `build_vowel_timing_plan()` 契約、core単体テストに限定した。

2026-07-06 に `src/core/whisper_timing.py`、`src/core/pipeline.py`、`src/core/__init__.py`、B3用テストを更新し、Whisper raw resultからの本文抽出と既存 `WhisperTimingResult` 再利用契約を実装した。対象テスト27件は通過した。

同日に、Codex軽量スモークではB3 core smoke / version smoke / wx MS13 integration smokeが通過した。`tests/test_wx_startup_splash.py` は表示上 2 passed だが pytest process の exit code は 1。ユーザースモークテストは通過した。

B3ではGUI導線、VMD保存導線、VMD writer変更は扱っていない。

### 11.1 目的

TEXTファイルなしでも、書き起こし本文からひらがな・母音列・timing planを生成できるcore契約を追加する。

### 11.2 In Scope

- textless用の入力データ構造
- 書き起こし本文から `text_processing` への接続
- `build_vowel_timing_plan()` の再利用方針
- `generate_vmd_from_text_wav()` とは別の保存入口、またはTEXT path optional化の設計判断
- core単体テスト

### 11.3 Out of Scope

- GUI導線
- VMD writer再設計
- 音声解析品質の大幅変更

### 11.4 成果物

- `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md`
- `extract_transcription_text()` 追加方針
- `TranscriptionTextResult` 追加方針
- 既存 `WhisperTimingResult` 再利用方針
- B3用core単体テスト方針
- `src/core/whisper_timing.py`
- `src/core/pipeline.py`
- `src/core/__init__.py`
- `tests/test_ms19_b3_transcription_contract.py`
- `tests/test_ms19_b3_textless_pipeline.py`

### 11.5 受け入れ条件

- `segments[].text` 優先、`raw_result["text"]` fallback、`words[].word` 非採用の本文抽出契約が実装・テストされている
- 空本文を成功扱いにしない
- `build_vowel_timing_plan()` の既存TEXTあり呼び出しが壊れていない
- 既存 `WhisperTimingResult` を渡した場合にWhisperを再実行しない
- B3でGUI導線、VMD保存導線、VMD writerを変更していない

## 12. MS19-B4: GUI Entry Point and State Handling

### 12.0 ステータス

完了。

2026-07-06 に `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md` を作成し、B4の対象をwxPython GUI上の音声のみ入力状態、解析ボタン有効条件、`AnalysisWorker` のvoice_only分岐、InfoPanelへの最小反映に限定した。

2026-07-07 に、`UiState` の `text_audio` / `voice_only` 状態、TEXTなし音声入力時の解析ボタン有効化、`AnalysisWorker` のvoice_only分岐、`AnalysisWorkerResult`、InfoPanelへの書き起こし本文・ひらがな・母音列の最小反映を実装した。

同日に、voice_only解析で発生した `WinError 2` を受け、Whisper実行中だけ検出済み `FFmpeg\bin` を `PATH` 先頭へ一時追加する補正を `src/core/whisper_timing.py` へ追加した。音声読み込みで使うrepo-local FFmpeg探索方針とWhisper内部のffmpeg探索を接続するためのB4実装補正であり、自動ダウンロードや新規依存追加は行っていない。

ユーザー側の音声のみ解析スモークテストは2026-07-07に通過・問題なし。

B4では書き起こし編集UI、TEXTなしVMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` 契約変更は扱っていない。voice_only解析結果ができてもB4ではVMD保存ボタンを有効化しない。

### 12.1 目的

wxPython GUI上で、TEXTなしでも音声のみ入力モードへ入れる最小導線と状態表示を追加する。

### 12.2 In Scope

- `解析実行` 有効条件の分岐
- `UiState` の音声のみ入力状態
- Busy / cancel / late callback との整合
- InfoPanel表示方針
- 既存TEXTあり導線の回帰確認

### 12.3 Out of Scope

- 大規模レイアウト刷新
- Qt / PySide6復活
- 詳細編集UI

### 12.4 成果物

- `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/core/whisper_timing.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_whisper_timing.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b4_analysis.py`

### 12.5 受け入れ条件

- TEXTなし音声入力後に解析実行ボタンが有効化される
- TEXTあり入力の解析実行条件が壊れていない
- 音声のみ入力でB3の本文抽出・timing plan再利用契約を使う
- 音声のみ入力でWhisperを二重実行しない
- 音声のみ入力の `transcription_text` がセッション内状態へ保持される
- InfoPanelに書き起こし本文・ひらがな・母音列が最小反映される
- voice_only解析成功後も、B4ではVMD保存ボタンが有効化されない
- B4でVMD保存導線、VMD writer、書き起こし編集UIを変更していない
- ユーザー側音声のみ解析スモークテストが通過している

## 13. MS19-B5: Review / Edit Transcription Result Flow

### 13.0 ステータス

完了。

2026-07-07 に `docs/Implementation_Plan/MS19-B5_Implementation_Plan.md` を作成し、B5の対象を音声のみ解析で得た書き起こし結果の確認・編集、編集後のひらがな / 母音列 preview 更新、編集前 timing plan の誤用防止、保持済み `WhisperTimingResult` を使った編集済みテキスト再解析の最小導線に限定した。編集済みテキスト再解析で `current_timing_plan` を更新した場合、既存Previewが追従して再描画されることはB5の許容範囲とする。

2026-07-08 に、InfoPanel上の書き起こし編集UI、`UiState` の編集済みtranscription保持、`AnalysisWorker` の編集済み再解析契約、MainFrameの適用 / 元に戻す / 未適用編集ガード、B5用テストを実装した。

同日に、ユーザー側のB5確認は通過・問題なしと報告された。

B5では、音声のみ入力のVMD保存有効化、Preview操作、再生タイムライン操作、VMD保存まで含む最終連携、永続的な書き起こし履歴管理、外部字幕形式出力、Qt / PySide6 GUI復活は扱っていない。

### 13.1 目的

音声のみ入力で得た書き起こし結果を、ユーザーが確認・必要に応じて修正できる方針を固め、最小実装する。

### 13.2 In Scope

- 音声のみ解析成功後の書き起こし結果編集
- 編集適用 / 元に戻すの最小UI
- 編集後テキストからのひらがな / 母音列プレビュー再生成
- 編集前 timing plan を編集後テキスト由来として扱わない状態遷移
- 保持済み `WhisperTimingResult` を使った編集済みテキスト再解析
- 編集済み再解析時の worker 入力契約
- TEXTあり入力の読み取り専用プレビュー維持
- セッション内状態としての編集結果保持

### 13.4 成果物

- `src/gui_wx/info_panel.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/main_frame.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `docs/Implementation_Plan/MS19-B5_Implementation_Plan.md`

### 13.3 Out of Scope

- 音声のみ入力のVMD保存有効化
- Preview操作、再生タイムライン操作、VMD保存まで含む最終連携
- 高度なテキストエディタ
- 永続的な書き起こし履歴管理
- 外部字幕形式出力
- Qt / PySide6 GUI復活

## 14. MS19-B6: VMD / Preview / Save Integration

### 14.0 ステータス

完了。

2026-07-08 に `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md` を作成し、B6の対象を音声のみ入力のVMD保存有効化、TEXT pathなし保存入口、Preview追従確認、既存TEXTあり保存導線維持に限定した。

B6計画では、既存 `generate_vmd_from_text_wav()` の破壊的な契約変更は行わず、音声のみ入力向けに `current_timing_plan` からVMDを書き出す別入口を追加する方針とした。

2026-07-09 に、`src/core/pipeline.py` へTEXTなし保存入口 `generate_vmd_from_timing_plan()` と戻り値 `VmdGenerationResult` を追加し、`src/gui_wx/ui_state.py` / `src/gui_wx/app_controller.py` / `src/gui_wx/main_frame.py` でvoice_only保存可否、保存分岐、ステータス文言をB6仕様へ更新した。

同日に、B4/B5由来の保存不可期待値テストをB6後の仕様へ更新し、B6対象自動スモーク36件が通過した。全体pytestは通常実行では既存のimport path不足で収集停止し、`src` / `tests` を `sys.path` に追加した全体確認では `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件が失敗した。B6保存導線の対象テストでは問題を検出していない。

ユーザー側のB6確認は通過・問題なし。音声のみ解析後のTEXTなしVMD保存、編集適用直後の保存不可、編集済み再解析後の保存可、既存TEXTあり導線について、B6内で追加修正が必要な問題は報告されていない。

### 14.1 目的

音声のみ入力で生成した timing plan を、Preview表示とVMD保存へ接続する。

### 14.2 In Scope

- Preview表示
- VMD保存
- `selected_text_path` がない場合の `PipelineResult` / 保存契約
- 既存TEXTあり保存導線の維持
- MMD用WAV出力導線との整合

### 14.3 Out of Scope

- VMD writer全面再設計
- モーフ編集
- MMD用WAV仕様変更

### 14.4 成果物

- `src/core/pipeline.py`
- `src/core/__init__.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md`

### 14.5 受け入れ条件

- 音声のみ解析成功後、VMD保存ボタンとメニューが有効化される
- TEXT pathなしで `current_timing_plan` からVMD保存できる
- 編集適用直後の未再解析状態ではVMD保存できない
- 編集済み再解析成功後はVMD保存できる
- TEXTあり入力の既存VMD保存導線が維持されている
- Previewは既存の `current_timing_plan` 追従を維持している
- MMD用WAV出力仕様を変更していない
- ユーザー側B6確認が通過している

## 15. MS19-B7: Error Handling / Tests / Docs

### 15.0 ステータス

完了。自動テスト完走、ユーザー確認通過・問題なし。

2026-07-09 に `docs/Implementation_Plan/MS19-B7_Implementation_Plan.md` を作成し、B7の対象を音声のみ入力に固有の失敗条件分類、状態復帰、テスト実行状態整理、README / 配布用readme / 関連docs同期に限定した。

B7計画では、新機能追加ではなく、Whisper失敗、書き起こし空、読み変換失敗、母音列なし、編集済みテキスト空、VMD保存失敗の表示・状態復帰・テストを整理する方針とした。

2026-07-10 に、voice_only解析エラー分類helper、解析失敗時の安全な状態復帰、VMD保存失敗時の解析結果保持、B7回帰テスト、通常pytestのimport path安定化、旧MS14 fixtureの現行入力契約追従を実装した。README / 配布用readme / 関連仕様docsも音声のみ入力へ同期した。

通常の `pytest tests` は360件すべてpass表示まで完走した。既存wxテスト終了処理由来のprocess exit code 1は残るため、表示結果と終了コードを分けて記録する。2026-07-10 にユーザー確認通過・問題なしと報告された。

### 15.1 目的

音声のみ入力に固有の失敗条件、回帰テスト、ユーザー向け説明を整理する。

### 15.2 In Scope

- 書き起こし失敗
- 書き起こし結果が空
- 日本語読み変換失敗
- 母音列が空
- 既存TEXTあり導線の回帰テスト
- README / docs同期

### 15.3 Out of Scope

- 法的ライセンス再監査
- package公開
- MS20向けモーフ編集

## 16. MS19-B8: Workspace Reset / New Session Flow

### 16.0 ステータス

完了。

2026-07-11 にファイルメニューの `新規作業... Ctrl+N` を実装した。TEXT・音声・書き起こし・解析結果・表示・再生状態を初期化し、設定・履歴を保持したまま次素材へ移れる。確認キャンセル時は状態を変更せず、Busy中は実行不可とし、audio / analysis job ID無効化でlate callbackを破棄する。

`tests/test_ms19_b8_workspace_reset.py` は8件pass、対象・関連回帰は60件すべてpass表示、通常 `pytest tests` は368件すべてpass表示まで完走した。後者2件は既存wx終了処理由来のprocess exit code 1を記録した。2026-07-11 にユーザースモークテスト通過・問題なしを確認した。

MS19 CloseoutはB9で完了した。

### 16.1 目的

現在の作業データを安全に破棄し、設定・履歴を保持したまま次のTEXTあり / voice_only作業を開始できるようにする。

### 16.2 In Scope

- ファイルメニューの `新規作業... Ctrl+N`
- 作業データ存在時の確認とキャンセル
- Busy中の実行禁止
- TEXT / 音声 / 書き起こし / timing planの初期化
- Preview / Waveform / InfoPanel / playback / viewportの初期表示復帰
- audio / analysis job IDの無効化
- recent files / theme / parameter / last directoryの保持
- TEXTあり / voice_onlyの次作業再開テスト

### 16.3 Out of Scope

- 設定初期化
- recent files削除
- source / output / cacheファイル削除
- Busy中workerの自動キャンセルとresetの複合処理
- dedicated toolbarリセットボタン
- project / tab / Undo機能
- MS19 Closeout判定

### 16.4 成果物

- `docs/Implementation_Plan/MS19-B8_Implementation_Plan.md`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/info_panel.py`
- 新規 `tests/test_ms19_b8_workspace_reset.py`
- README / 配布用readme / 関連仕様・進捗docs

### 16.5 受け入れ条件

- 新規作業確認Yesで作業データと表示が初期状態へ戻る
- 確認Noで状態が変わらない
- Busy中は実行できない
- reset後に再解析待ちが残らず、VMD保存・再生・Zoomが不可になる
- recent files、theme、parameter、last directoryが保持される
- source / output / cacheファイルを削除しない
- reset後にTEXTあり / voice_onlyのどちらも開始できる
- late callbackがreset後状態へ反映されない

## 17. MS19-B9: MS19 Closeout

### 17.0 ステータス

完了・Closeout A。

2026-07-12 に `docs/Implementation_Plan/MS19-B9_Implementation_Plan.md` を作成し、2026-07-13 にB9の自動テスト・差分・文書・既存ユーザー確認記録を再照合した。MS19固有テストは33件、計画指定回帰は62件、全体テストは368件がpass表示となった。`test_wx_ms14_b6_closeout.py` の終了処理には、フレーム破棄前に `_cleanup_analysis_job()` を呼ぶ補修を行い、access violationが再発しないことを確認した。ユーザーチェックも通過・問題なしである。

Production code、build/package設定は変更していない。次工程はpackage / release作業またはMS20計画である。

### 17.1 目的

MS19全体の実装・テスト・docs同期結果を確認し、MS20へ進めるか判定する。

### 17.2 In Scope

- MS19受け入れ条件確認
- TEXTあり / TEXTなし導線の確認
- 実音声での手動確認
- VMD出力確認
- README / docs同期確認
- closeout判定

### 17.3 Out of Scope

- MS20実装
- release公開
- 英語対応

## 18. MS19全体のテスト方針

MS19では、変更範囲に応じて以下のテストを追加・実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests/test_text_processing.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
```

core契約を追加するBlockでは、新規 `tests/test_ms19_*.py` を追加する。

GUI導線を変更するBlockでは、既存 wx テストの終了コード不安定性を、表示上のpass数と終了コードに分けて報告する。

## 19. AI agent 作業時の共通指示

AI agent に MS19 作業を依頼する場合は、以下を共通指示とする。

```text
- feature/MS19 を作業ブランチとして扱うこと。
- MS18の安定化作業とMS19の音声のみ入力対応を混同しないこと。
- 実装前に MS19-B1 で TEXTあり / TEXTなしの状態契約を固定すること。
- 既存TEXTあり導線を壊さないこと。
- 最初は日本語音声のみを対象とすること。
- 英語対応、多言語対応、クラウドAPI、自動ダウンロードはMS19から除外すること。
- wxPython主系を維持し、Qt / PySide6 GUIを復活させないこと。
- VMD writerの全面再設計を行わないこと。
- 変更したファイル、確認したファイル、実行したテスト、未実行テスト、残課題を報告すること。
```
