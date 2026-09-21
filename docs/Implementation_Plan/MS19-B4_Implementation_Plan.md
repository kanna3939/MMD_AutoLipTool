# MS19-B4 Implementation Plan

## 1. 文書情報

- 文書名: MS19-B4 Implementation Plan
- 対象マイルストーン: MS19
- 対象Block: MS19-B4 GUI Entry Point and State Handling
- 対象ブランチ: `feature/MS19`
- 作成日: 2026-07-06
- 文書ステータス: Completed
- 前提:
  - MS19-B1 Voice-only Input Requirements / State Contract は完了済み。
  - MS19-B2 Transcription Pipeline Pre-check は完了済み。
  - MS19-B3 Textless Pipeline Integration Foundation は実装済み。
  - B3では `extract_transcription_text()`、`TranscriptionTextResult`、`build_vowel_timing_plan(..., whisper_timing_result=...)` が追加された。
  - B3実装差分とB4実装プランは `d9fc248 Implement MS19 B3 and plan B4` でコミット済み。
  - B4実装は2026-07-07に実施し、ユーザー側の音声のみ入力スモークテスト通過・問題なしを確認済み。

## 2. 背景

MS19-B3により、core層ではWhisper raw resultから本文を抽出し、同じ `WhisperTimingResult` を使って `build_vowel_timing_plan()` へ接続できるようになった。

一方、wxPython GUI側の現行実装は、まだTEXTファイルあり入力を前提にしている。

- `src/gui_wx/main_frame.py`
  - `解析実行` ボタンは `selected_text_path` と音声入力が揃った場合のみ有効になる。
  - `_run_analysis()` は `selected_text_content` が空の場合にエラーを表示して停止する。
  - `AnalysisWorker` には `selected_text_content` だけを渡している。
- `src/gui_wx/analysis_worker.py`
  - `text_content` を受け取り、`build_vowel_timing_plan()` を実行する。
  - 音声のみ入力時にWhisper結果から本文を抽出する分岐はまだない。
- `src/gui_wx/ui_state.py`
  - `selected_text_path` / `selected_text_content` はあるが、音声のみ入力を表す `input_mode` や `transcription_text` はまだない。
- `src/gui_wx/app_controller.py`
  - VMD保存は `selected_text_path` を `generate_vmd_from_text_wav()` へ渡す。

B4では、VMD保存や編集UIまでは扱わず、TEXTなしで音声のみ入力モードへ入れる最小GUI導線と状態契約を追加する。

## 3. 目的

MS19-B4の目的は、wxPython GUIでTEXTファイルなしの音声入力状態を認識し、既存の解析実行ボタンから音声のみ解析を開始できるようにすることである。

このBlockでは、既存TEXTあり導線を壊さず、B3で追加したcore契約をGUI workerへ接続する。

## 4. In Scope

- `UiState` への音声のみ入力状態の追加
- TEXTあり / TEXTなしの解析可否判定の分岐
- `AnalysisWorker` のTEXTあり / 音声のみ入力分岐
- 音声のみ入力時の `recognize_audio_timing()`、`extract_transcription_text()`、`build_vowel_timing_plan(..., whisper_timing_result=...)` 接続
- 音声のみ入力で得た `transcription_text` / source のセッション内保持
- InfoPanelへの最小反映方針
- Busy / cancel / late callback の既存動作維持
- 既存TEXTあり導線の回帰テスト
- B4用GUI状態テスト追加

## 5. Out of Scope

- 書き起こし結果の編集UI
- 書き起こし結果の永続保存
- VMD保存導線のTEXTなし対応
- `generate_vmd_from_text_wav()` の `text_path` optional化
- VMD writer変更
- Preview / VMD保存の完全統合
- Whisper model管理UI
- 自動モデルダウンロード
- 英語音声対応、多言語対応
- 高度なエラー分類・ユーザー通知文言の全面整理
- package / release作業
- Qt / PySide6 GUI復活

## 6. 前提条件

- 作業ブランチは `feature/MS19` とする。
- `docs/MS17_and_Beyond_Index.md` を最初に確認する。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- B3のproduction codeとテストが存在すること。
- B4実装開始時点では、B3差分は `d9fc248 Implement MS19 B3 and plan B4` でコミット済みであること。
- 既存TEXTあり入力は `TextAudioInput` として維持する。
- 音声のみ入力は `VoiceOnlyInput` として扱う。
- wxPython主系を維持し、Qt / PySide6 GUIは復活させない。

## 7. 対象ファイル

### 7.1 production code

- `src/gui_wx/ui_state.py`
  - 音声のみ入力状態を表す最小フィールドを追加する。
  - 解析可能判定をhelper化する候補。
- `src/gui_wx/analysis_worker.py`
  - TEXTあり / 音声のみ入力の解析分岐を追加する。
  - 音声のみ入力時はB3のcore helperを利用する。
- `src/gui_wx/main_frame.py`
  - 解析ボタン有効条件をTEXTあり / TEXTなしに分岐する。
  - `_run_analysis()` の事前検証をTEXTなし入力に対応させる。
  - 解析成功時に音声のみ入力の書き起こし結果を状態とInfoPanelへ最小反映する。
- `src/gui_wx/app_controller.py`
  - 音声読み込み完了時の `mark_ready_for_analysis()` 条件をTEXTあり / TEXTなしに分岐する。
  - VMD保存はB4では変更しない。

### 7.2 tests

- `tests/test_ms19_b4_voice_only_gui_state.py`
  - TEXTなし音声入力状態で解析可能になることを検証する。
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
  - 音声のみ入力時にB3 core契約を使い、Whisperを二重実行しないことを検証する。
- 既存回帰:
  - `tests/test_wx_ms14_b2_state.py`
  - `tests/test_wx_ms14_b3_input.py`
  - `tests/test_wx_ms14_b4_analysis.py`
  - `tests/test_ms19_b3_transcription_contract.py`
  - `tests/test_ms19_b3_textless_pipeline.py`

### 7.3 docs

- `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

## 8. 実装方針

### 8.1 入力モード

B4では、以下の2モードをGUI状態上で区別する。

```text
text_audio:
  TEXTファイル + 音声ファイルの既存モード。
  selected_text_path / selected_text_content を正本にする。

voice_only:
  音声ファイルのみのMS19追加モード。
  selected_text_path は None のまま。
  transcription_text を解析用テキスト相当データとして扱う。
```

実装名は、既存コードの単純さを優先し、まずは `input_mode: str` または軽量Enum相当のどちらかにする。大規模な状態管理クラスは追加しない。

### 8.2 `UiState` 追加候補

最小候補:

```python
input_mode: str = "text_audio"
transcription_text: str = ""
transcription_source: str = ""
transcription_timing_source: str = ""
analysis_text_content: str = ""
analysis_text_source: str = ""
```

実装時の推奨:

- `selected_text_content` はTEXTあり入力の正本として維持する。
- 音声のみ入力では `selected_text_path` を設定しない。
- 音声のみ入力で得た本文は `transcription_text` に保持する。
- `analysis_text_content` は、解析に実際に使った本文を表示・後続Blockへ渡すためのセッション内値として扱う。
- B4では永続保存しない。

### 8.3 解析可能条件

現行:

```python
can_analyze = bool(state.selected_text_path and (state.selected_audio_input or state.selected_wav_path))
```

B4後:

```text
TEXTあり:
  selected_text_path and selected_text_content and audio input がある

音声のみ:
  selected_text_path is None and audio input がある
```

ただし、現行コードと既存テストではTEXTあり条件が完全には揃っていない。

- `main_frame.update_action_states()` は `selected_text_path + audio` で解析ボタンを有効化している。
- `main_frame._run_analysis()` は `selected_text_content + wav_analysis` を実行前提にしており、`selected_text_path` は要求していない。
- `tests/test_wx_ms14_b2_state.py` には `selected_text_path + selected_wav_path` だけで解析ボタン有効を期待するテストがある。
- `tests/test_wx_ms14_b4_analysis.py` には `selected_text_content + selected_wav_analysis` だけで解析実行を期待するテストがある。

B4実装では、TEXTあり解析の正式条件を `selected_text_path + selected_text_content + audio input` に寄せる。そのため、既存テストは単なる回帰実行だけでなく、B4後の状態契約に合わせて期待値を更新する対象に含める。

音声のみ入力では、音声読み込み完了後に解析ボタンを有効化する。ただし、解析実行時にWhisperが本文抽出できなければエラーで停止する。

### 8.4 `AnalysisWorker` 契約

B4では `AnalysisWorker` がTEXTあり / 音声のみの両方を扱う。

TEXTあり:

```text
text_content -> build_vowel_timing_plan()
```

音声のみ:

```text
recognize_audio_timing()
  -> extract_transcription_text(raw_result)
  -> build_vowel_timing_plan(text_content=transcription_text, whisper_timing_result=...)
```

Whisperは1回だけ実行し、B3で追加した `whisper_timing_result` 再利用契約を使う。

### 8.5 解析結果の返却

現行の成功callbackは `plan` だけを返す。

B4では、音声のみ入力の `transcription_text` をGUI状態へ反映する必要があるため、以下の小さな結果データ構造を追加する方針とする。

```python
@dataclass(frozen=True)
class AnalysisWorkerResult:
    timing_plan: VowelTimingPlan
    input_mode: str
    analysis_text_content: str
    analysis_text_source: str
    transcription_text: str = ""
    transcription_source: str = ""
```

`MainFrame._on_analysis_success()` は、当面この結果型を正本として扱う。既存テストはB4で更新する。

### 8.6 InfoPanel反映

B4では編集UIは作らない。

音声のみ入力の解析成功時に、既存InfoPanelへ以下を最小表示する。

- text preview: `transcription_text`
- hiragana preview: `text_to_hiragana(transcription_text)` の結果
- vowel preview: 5母音列

B5でreview / edit flowを実装するまでは、表示は確認用に留める。

### 8.7 VMD保存

B4ではVMD保存をTEXTなし対応しない。

- `app_controller.request_save_vmd()` の `generate_vmd_from_text_wav(text_path=...)` 契約は変更しない。
- 音声のみ解析後にVMD保存ボタンを有効化するかどうかはB6で扱う。B4では有効化しない。
- B4では、TEXTなし解析結果ができても保存導線は既存TEXTあり契約を優先し、誤って `selected_text_path=None` で保存処理へ進まないようにする。
- 現行 `main_frame.update_action_states()` は `state.analysis_ready` だけでVMD保存ボタンを有効化するため、B4実装では保存ボタン条件を `analysis_ready and input_mode == "text_audio" and selected_text_path` 相当に絞る。
- `app_controller.request_save_vmd()` 側にも、`selected_text_path` がない場合は保存へ進まないガードを維持または追加する。

## 9. 詳細ステップ

1. repo状態を確認する。
   - `git status --short --branch`
   - `git log --oneline -n 5`
2. `docs/MS17_and_Beyond_Index.md` を確認する。
3. B3実装差分が存在することを確認する。
4. GUI対象ファイルを確認する。
   - `src/gui_wx/ui_state.py`
   - `src/gui_wx/main_frame.py`
   - `src/gui_wx/analysis_worker.py`
   - `src/gui_wx/app_controller.py`
5. `UiState` に音声のみ入力状態を追加する。
6. 解析可能条件をTEXTあり / 音声のみで分岐する。
   - TEXTありは `selected_text_path + selected_text_content + audio input` を正式条件にする。
   - 既存テストの `selected_text_path` のみ / `selected_text_content` のみの前提は、B4後の契約に合わせて更新する。
7. `AnalysisWorker` に音声のみ入力分岐を追加する。
8. `AnalysisWorkerResult` 相当の返却契約を追加する。
9. 解析成功時に `transcription_text` と生成結果をUI状態へ反映する。
10. VMD保存導線がTEXTなしで誤作動しないことを確認する。
    - voice_only解析成功後も、B4ではVMD保存ボタンが無効のままであることを確認する。
    - `selected_text_path=None` の状態で `request_save_vmd()` が `generate_vmd_from_text_wav()` へ進まないことを確認する。
11. B4用テストと既存回帰テストを実行する。
12. 関連ドキュメントへB4実施結果を反映する。

## 10. 状態遷移 / データ契約

### 10.1 TEXTあり

```text
TEXT選択
  -> selected_text_path / selected_text_content 更新
音声選択
  -> selected_audio_input / selected_wav_path / selected_analysis_wav 更新
解析実行
  -> AnalysisWorker(input_mode=text_audio)
  -> build_vowel_timing_plan(text_content=selected_text_content)
  -> current_timing_plan
```

### 10.2 音声のみ

```text
音声選択
  -> selected_audio_input / selected_wav_path / selected_analysis_wav 更新
  -> input_mode=voice_only
解析実行
  -> AnalysisWorker(input_mode=voice_only)
  -> recognize_audio_timing()
  -> extract_transcription_text(raw_result)
  -> build_vowel_timing_plan(text_content=transcription_text, whisper_timing_result=...)
  -> transcription_text / analysis_text_content / current_timing_plan
```

### 10.3 失敗条件

- 音声入力がない: 既存どおりエラー。
- TEXTあり入力でTEXT内容が空: 既存どおりエラー。
- 音声のみ入力でWhisper本文抽出が空: `WhisperTimingError` 相当として解析失敗。
- 音声のみ入力で母音列が空: 解析失敗。
- timing anchorがspeech interval内にない: B3と同様にwarning付きeven fallbackを許容。

## 11. テスト方針

B4ではGUI状態とworker分岐のテストを追加する。

B4で既存TEXTあり条件を明確化するため、以下の既存テストは必要に応じて期待値を更新する。

- `tests/test_wx_ms14_b2_state.py`
  - TEXTあり解析ボタン有効条件は `selected_text_path` だけでなく `selected_text_content` も揃う前提へ更新する。
  - voice_only解析成功後も、B4ではVMD保存ボタンが無効のままであることを追加検証する。
- `tests/test_wx_ms14_b4_analysis.py`
  - TEXTあり `_run_analysis()` の正常系は `selected_text_path` と `selected_text_content` の両方を持つ状態で検証する。
- `tests/test_ms19_b4_voice_only_gui_state.py`
  - TEXTなし音声入力で解析ボタンが有効になることを検証する。
  - voice_only解析結果ができても、B4ではVMD保存ボタンが有効化されないことを検証する。
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
  - voice_only workerがWhisper timing結果を再利用し、Whisperを二重実行しないことを検証する。

実行候補:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py tests\test_ms19_b3_textless_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b4_analysis.py
```

必要に応じて軽量スモーク:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_app_version.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms13_integration.py
```

`tests/test_wx_startup_splash.py` は表示上passでも pytest process の exit code が 1 になる既存挙動があるため、実行した場合は表示上のpass数とexit codeを分けて記録する。

## 12. 受け入れ条件

- TEXTなし音声入力後に、解析実行ボタンが有効化される。
- TEXTあり入力の解析実行条件が `selected_text_path + selected_text_content + audio input` として明確化され、既存TEXTあり導線が壊れていない。
- 音声のみ入力で `recognize_audio_timing()`、`extract_transcription_text()`、`build_vowel_timing_plan(..., whisper_timing_result=...)` が接続されている。
- 音声のみ入力でWhisperを二重実行しない。
- 音声のみ入力の `transcription_text` がセッション内状態へ保持される。
- InfoPanelに書き起こし本文・ひらがな・母音列が最小表示される。
- Busy / cancel / late callbackの既存動作を壊していない。
- B4ではVMD保存導線をTEXTなし対応していない。
- voice_only解析成功後も、B4ではVMD保存ボタンが有効化されない。
- `selected_text_path=None` の状態で `request_save_vmd()` が `generate_vmd_from_text_wav()` へ進まない。
- B4ではVMD writerを変更していない。
- 既存TEXTあり導線の回帰テストが通過している。

## 13. リスクと対策

### 13.1 TEXTあり導線の回帰

- リスク: 解析可能条件を広げることで、TEXTあり入力の既存挙動が壊れる。
- 対策: `text_audio` と `voice_only` を明示的に分け、TEXTあり条件を `selected_text_path + selected_text_content + audio input` として固定する。既存TEXTありテストはB4後の契約に合わせて期待値を更新し、そのうえで必ず実行する。

### 13.2 VMD保存の誤有効化

- リスク: 音声のみ解析後に `selected_text_path=None` のまま既存保存処理へ進む。
- 対策: B4ではTEXTなし保存をOut of Scopeとし、保存ボタンの有効条件をTEXTあり解析結果に限定する。`request_save_vmd()` 側でも `selected_text_path` なしでは保存へ進まないガードを確認する。TEXTなし保存はB6で扱う。

### 13.3 Whisper二重実行

- リスク: 本文抽出とtiming plan生成でWhisperを2回実行すると待ち時間が増える。
- 対策: B3の `whisper_timing_result` 再利用契約を `AnalysisWorker` で使う。

### 13.4 B5/B6範囲の先取り

- リスク: B4で編集UIや保存入口まで実装するとBlock境界が崩れる。
- 対策: B4は状態・解析開始・最小表示までに限定する。

### 13.5 wxテスト終了コード

- リスク: wx系テストで表示上passだがexit code 1になる既存挙動を、B4回帰と誤認する。
- 対策: 表示上のpass数とexit codeを分けて記録する。

## 14. Codex 実装時の注意

- 実装前に必ず `git status --short --branch` と `git log --oneline -n 5` を確認する。
- `docs/MS17_and_Beyond_Index.md` を最初に読む。
- コマンドを並列実行しない。
- shell pipeline / chained command を避ける。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- B4ではVMD保存導線を実装しない。
- B4ではVMD writerを変更しない。
- B4では `generate_vmd_from_text_wav()` の `text_path` 契約を変更しない。
- B4では書き起こし編集UIを作らない。
- 既存TEXTあり導線の回帰テストを必ず含める。
- テスト未実行の場合は理由を明記する。

## 15. 実装結果 / Closeoutメモ

### 15.1 実装日

2026-07-07

### 15.2 実装内容

- `UiState` に `text_audio` / `voice_only` の入力モード、解析開始可否、TEXTありVMD保存可否、transcription保持フィールドを追加した。
- `AnalysisWorker` に `AnalysisWorkerResult` とTEXTあり / voice_only分岐を追加した。
- voice_only分岐では `recognize_audio_timing()` を1回だけ実行し、同じ `WhisperTimingResult` を `build_vowel_timing_plan(..., whisper_timing_result=...)` へ渡すことでWhisper二重実行を避ける。
- `MainFrame` はTEXTなし音声入力で解析ボタンを有効化し、voice_only解析成功時に書き起こし本文・ひらがな・母音列をInfoPanelへ最小反映する。
- `AppController.request_save_vmd()` は、B4ではTEXTあり解析結果のみ保存可能とし、`selected_text_path=None` では保存ダイアログや `generate_vmd_from_text_wav()` へ進まない。
- 音声のみ解析で発生した `WinError 2` に対して、Whisper実行中だけ検出済み `FFmpeg\bin` を `PATH` 先頭へ一時追加し、実行後に元へ戻す補正を `src/core/whisper_timing.py` に追加した。

### 15.3 変更ファイル

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

### 15.4 テスト / 確認

- `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py` -> 1 passed / exit code 0
- `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py` -> 表示上 5 passed。pytest process の exit code は 1。
- `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 3 passed / exit code 0
- `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py` -> 5 passed / exit code 0
- `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py` -> 2 passed / exit code 0
- `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b4_analysis.py` -> 3 passed / exit code 0
- `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py tests\test_ms19_b3_textless_pipeline.py tests\test_whisper_timing.py tests\test_pipeline_and_vmd.py` -> 17 passed / exit code 0
- `.\.venv\Scripts\python.exe -m pytest tests\test_app_version.py tests\test_wx_ms13_integration.py` -> 10 passed / exit code 0
- `git diff --check` -> エラーなし。CRLF警告のみ。
- ユーザー側スモークテスト: 2026-07-07 に音声のみ解析で通過・問題なし。

### 15.5 Closeout判定

MS19-B4 closeoutはOK。

B4では、音声のみ入力から解析実行までのGUI導線、voice_only状態、InfoPanel最小反映、TEXTなしVMD保存無効化を実装した。書き起こし編集UI、TEXTなしVMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` 契約変更はB4では扱っていない。
