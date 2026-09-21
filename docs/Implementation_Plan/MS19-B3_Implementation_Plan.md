# MS19-B3 Implementation Plan

## 1. 文書情報

- 文書名: MS19-B3 Implementation Plan
- 対象マイルストーン: MS19
- 対象Block: MS19-B3 Textless Pipeline Integration Foundation
- 対象ブランチ: `feature/MS19`
- 作成日: 2026-07-05
- 文書ステータス: Completed
- 前提:
  - MS19-B1 Voice-only Input Requirements / State Contract は完了済み。
  - MS19-B2 Transcription Pipeline Pre-check は完了済み。
  - B2で、書き起こし本文の第一候補を `segments[].text`、fallback候補を `raw_result["text"]` とする方針を確認済み。
  - B2で、`words[].word` は初期本文正本にしない方針を確認済み。

## 2. 背景

現行実装は、TEXTファイルと音声ファイルの両方があることを前提にしている。

- `src/core/pipeline.py`
  - `build_vowel_timing_plan()` は `text_content` から母音列を生成し、内部で `recognize_audio_timing()` を実行してタイミングanchorを得る。
  - `generate_vmd_from_text_wav()` は `text_path` を必須にしている。
- `src/core/whisper_timing.py`
  - `recognize_audio()` はWhisper raw result dictを返す。
  - `recognize_audio_timing()` は `WhisperTimingResult.raw_result` と `WhisperTimingResult.source` を保持する。
- `src/gui_wx/`
  - 解析実行とVMD保存は `selected_text_path` / `selected_text_content` を前提にしている。

B3ではGUI導線には入らず、TEXTファイルなしでもcore層で「Whisper raw resultから本文を取り出し、その本文を既存のひらがな・母音列・timing plan生成へ接続できる」契約を追加する。

## 3. 目的

MS19-B3の目的は、音声のみ入力で得た書き起こし本文を、TEXTファイル相当の解析入力として扱えるcore契約を追加することである。

このBlockでは、既存TEXTあり導線を壊さず、後続のB4 GUI導線およびB6 VMD保存統合が利用できる最小のproduction codeと単体テストを追加する。

## 4. In Scope

- Whisper raw resultから初期 `transcription_text` を抽出するhelper追加
- 抽出結果のsourceを示す小さなデータ構造追加
- 空本文を成功扱いにしないエラー契約追加
- `build_vowel_timing_plan()` が既存Whisper timing結果を再利用できる契約の追加
- 既存TEXTあり呼び出しの後方互換維持
- core単体テスト追加
- MS19関連ドキュメントのB3計画作成状態への同期

## 5. Out of Scope

- wxPython GUI導線の変更
- `UiState` への音声のみ入力状態追加
- `AnalysisWorker` のTEXTなし実行対応
- VMD保存導線の実装
- `generate_vmd_from_text_wav()` のoptional `text_path` 化
- VMD writerの再設計
- Whisper model管理UI
- 自動モデルダウンロード
- 英語音声対応、多言語対応
- 音声解析品質アルゴリズムの大幅変更
- package / release作業

## 6. 前提条件

- 作業ブランチは `feature/MS19` とする。
- `docs/MS17_and_Beyond_Index.md` を最初に確認する。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- 既存TEXTあり入力の動作を正本として維持する。
- 音声のみ入力の初期対象は日本語音声のみとする。
- wxPython主系を維持し、Qt / PySide6 GUIは復活させない。

## 7. 対象ファイル

### 7.1 production code

- `src/core/whisper_timing.py`
  - `TranscriptionTextResult` などの抽出結果dataclassを追加する。
  - `extract_transcription_text(raw_result: dict[str, Any])` を追加する。
- `src/core/pipeline.py`
  - `build_vowel_timing_plan()` に、既存 `WhisperTimingResult` を再利用できるoptional引数を追加する。
  - optional引数が未指定の場合の既存動作を維持する。
- `src/core/__init__.py`
  - 追加した公開APIを必要に応じてexportする。

### 7.2 tests

- `tests/test_ms19_b3_transcription_contract.py`
  - Whisper raw resultからの本文抽出契約を検証する。
- `tests/test_ms19_b3_textless_pipeline.py`
  - 既存Whisper timing結果を再利用してtiming planを生成できることを検証する。

### 7.3 docs

- `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md`
- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

## 8. 実装方針

### 8.1 transcription text抽出

`src/core/whisper_timing.py` に、Whisper raw resultから本文を抽出するhelperを追加する。

想定API:

```python
@dataclass(frozen=True)
class TranscriptionTextResult:
    text: str
    source: str


def extract_transcription_text(raw_result: dict[str, Any]) -> TranscriptionTextResult:
    ...
```

抽出優先順位:

1. `raw_result["segments"]` がlistで、各segmentの `text` に非空文字列がある場合は、それらをstripして連結する。
2. segment textが得られない場合のみ、`raw_result["text"]` の非空文字列をfallbackとして使う。
3. `segments[].words[].word` は初期本文正本には使わない。
4. どちらからも非空本文が得られない場合は `WhisperTimingError` を送出する。

`source` は、少なくとも `"segments"` / `"raw_text"` を区別できる値にする。

### 8.2 timing plan生成への接続

`build_vowel_timing_plan()` は、既存のTEXTあり呼び出しを維持したまま、既に取得済みの `WhisperTimingResult` を任意で受け取れるようにする。

想定方針:

```python
def build_vowel_timing_plan(
    *,
    text_content: str,
    wav_path: str | Path,
    wav_analysis: WavAnalysisResult,
    whisper_model_name: str = "small",
    upper_limit: float = _DEFAULT_MORPH_UPPER_LIMIT,
    phase_callback: Callable[[str], None] | None = None,
    whisper_timing_result: WhisperTimingResult | None = None,
) -> VowelTimingPlan:
    ...
```

- `whisper_timing_result` が未指定の場合:
  - 現行どおり `recognize_audio_timing()` を実行する。
- `whisper_timing_result` が指定された場合:
  - `recognize_audio_timing()` を再実行しない。
  - 渡されたanchorを既存処理と同じくspeech intervalへclipする。
  - `VowelTimingPlan.source` は `whisper_{whisper_timing_result.source}` を使う。
  - anchorがspeech interval内に残らない場合は、既存fallbackと同様にeven fallbackへ落とす。

この方針により、後続B4では音声認識を1回実行し、同じraw resultから本文とtiming anchorの両方を利用できる。

### 8.3 VMD保存入口の判断

B3では `generate_vmd_from_text_wav()` を変更しない。

現時点の推奨は、B6でTEXTなし保存用の別入口を追加することとする。理由は、既存 `PipelineResult.text_path` とTEXTファイル読み込み契約をB3で崩すと、保存・履歴・GUI状態の影響範囲が広がるためである。

`text_path` optional化はB6で再評価してよいが、B3ではproduction code対象外とする。

## 9. 詳細ステップ

1. repo状態を確認する。
   - `git status --short --branch`
   - `git log --oneline -n 5`
2. `docs/MS17_and_Beyond_Index.md` を確認する。
3. B3対象ファイルを確認する。
   - `src/core/whisper_timing.py`
   - `src/core/pipeline.py`
   - `src/core/__init__.py`
   - `tests/test_whisper_timing.py`
   - `tests/test_pipeline_and_vmd.py`
4. `TranscriptionTextResult` と `extract_transcription_text()` を追加する。
5. `build_vowel_timing_plan()` に `whisper_timing_result` optional引数を追加する。
6. 既存呼び出しが壊れていないことをテストで確認する。
7. B3用テストを追加する。
8. 対象テストを実行する。
9. MS19関連ドキュメントへB3実施結果を反映する。

## 10. 状態遷移 / データ契約

### 10.1 B3後のcore契約

```text
Whisper raw result
  -> extract_transcription_text()
  -> TranscriptionTextResult(text, source)
  -> build_vowel_timing_plan(text_content=TranscriptionTextResult.text, ...)
  -> VowelTimingPlan
```

`WhisperTimingResult` は、同じraw result由来のtiming anchorを保持する。

```text
WhisperTimingResult(raw_result, anchors, source)
  -> extract_transcription_text(raw_result)
  -> build_vowel_timing_plan(..., whisper_timing_result=WhisperTimingResult)
```

### 10.2 空本文の扱い

以下の場合は、音声のみ入力として続行しない。

- `segments[].text` が存在しない、またはすべて空
- fallback `raw_result["text"]` も存在しない、または空

この場合は `WhisperTimingError` を送出し、GUIでのユーザー通知はB4/B7で扱う。

### 10.3 既存TEXTあり導線

既存TEXTあり導線では、`build_vowel_timing_plan()` の新optional引数を指定しない。したがって、現行どおり関数内部で `recognize_audio_timing()` を実行する。

## 11. テスト方針

B3ではcore単体テストを追加し、GUIテストは原則追加しない。

実行対象:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_textless_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py
```

主な検証観点:

- `segments[].text` から本文を抽出できる
- segment textが空の場合に `raw_result["text"]` へfallbackできる
- `words[].word` だけでは本文抽出成功にしない
- 空本文では `WhisperTimingError` を送出する
- `whisper_timing_result` 指定時に `recognize_audio_timing()` を再実行しない
- optional引数未指定時の既存TEXTあり挙動が壊れない

## 12. 受け入れ条件

- `extract_transcription_text()` が追加され、本文抽出sourceを区別できる。
- `segments[].text` 優先、`raw_result["text"]` fallback、`words[].word` 非採用の契約がテストされている。
- 空本文が成功扱いにならない。
- `build_vowel_timing_plan()` が既存TEXTあり呼び出しを壊さない。
- 既存 `WhisperTimingResult` を渡した場合にWhisperを再実行しない。
- B3でGUI導線、VMD保存導線、VMD writerを変更していない。
- 対象テスト結果が記録されている。
- 関連ドキュメントがB3実施状態へ同期されている。

## 13. リスクと対策

### 13.1 Whisper再実行による遅延

- リスク: 本文抽出とtiming anchor取得でWhisperを2回実行すると、音声のみ入力の待ち時間が増える。
- 対策: B3で `WhisperTimingResult` 再利用契約を追加し、後続B4で1回の認識結果から本文とanchorを使えるようにする。

### 13.2 `generate_vmd_from_text_wav()` の影響範囲拡大

- リスク: B3で `text_path` optional化まで行うと、保存導線、`PipelineResult`、GUI状態、既存TEXTあり回帰の確認範囲が広がる。
- 対策: B3では保存入口を変更せず、B6で別入口追加を第一候補として扱う。

### 13.3 空本文の誤成功

- リスク: Whisperがanchorを返しても本文が空の場合、母音列生成が空になり、後段で分かりにくく失敗する。
- 対策: `extract_transcription_text()` で空本文を明示的に拒否する。

### 13.4 日本語以外の空白連結

- リスク: segment textの連結ルールが英語などの空白区切り言語に適さない可能性がある。
- 対策: MS19は日本語音声のみ対象とし、多言語対応はOut of Scopeとして維持する。

## 14. Codex 実装時の注意

- 実装前に必ず `git status --short --branch` と `git log --oneline -n 5` を確認する。
- `docs/MS17_and_Beyond_Index.md` を最初に読む。
- コマンドを並列実行しない。
- shell pipeline / chained command を避ける。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- B3ではGUIを変更しない。
- B3ではVMD writerを変更しない。
- B3では `generate_vmd_from_text_wav()` の `text_path` 契約を変更しない。
- 既存TEXTあり導線のテストを必ず含める。
- テスト未実行の場合は、理由を明記する。

## 15. MS19-B3 実施結果

実施日: 2026-07-06

MS19-B3 は、Whisper raw resultからの本文抽出helper、既存 `WhisperTimingResult` を再利用できる `build_vowel_timing_plan()` 契約、core単体テストを追加して完了した。

GUI導線、VMD保存導線、VMD writer、`generate_vmd_from_text_wav()` の `text_path` 契約は変更していない。

### 15.1 Git状態

- Current branch: `feature/MS19`
- Latest commit at start: `820a13a Document MS19 B3 implementation plan`
- Working tree at start: clean

### 15.2 変更したファイル

- `src/core/whisper_timing.py`
  - `TranscriptionTextResult` を追加した。
  - `extract_transcription_text()` を追加した。
  - `segments[].text` 優先、`raw_result["text"]` fallback、`words[].word` 非採用の本文抽出契約を実装した。
- `src/core/pipeline.py`
  - `build_vowel_timing_plan()` に `whisper_timing_result` optional引数を追加した。
  - optional引数指定時は `recognize_audio_timing()` を再実行せず、既存 `WhisperTimingResult` のanchorを再利用するようにした。
- `src/core/__init__.py`
  - `TranscriptionTextResult`、`WhisperTimingResult`、`extract_transcription_text()` を公開APIに追加した。
- `tests/test_ms19_b3_transcription_contract.py`
  - 書き起こし本文抽出契約の単体テストを追加した。
- `tests/test_ms19_b3_textless_pipeline.py`
  - 既存 `WhisperTimingResult` 再利用によるtiming plan生成の単体テストを追加した。

### 15.3 実装内容

- Whisper raw resultの `segments[].text` から初期 `transcription_text` を抽出できるようにした。
- segment textが使えない場合のみ `raw_result["text"]` をfallbackとして使う。
- `segments[].words[].word` だけでは初期本文抽出成功にしない。
- 空本文では `WhisperTimingError` を送出する。
- `build_vowel_timing_plan()` の既存TEXTあり呼び出しは維持した。
- 後続B4で、1回のWhisper結果から本文とtiming anchorを使えるcore契約を用意した。

### 15.4 実行したテスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_textless_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py
```

### 15.5 テスト結果

```text
tests/test_ms19_b3_transcription_contract.py: 4 passed
tests/test_ms19_b3_textless_pipeline.py: 2 passed
tests/test_whisper_timing.py: 2 passed
tests/test_text_processing.py: 10 passed
tests/test_pipeline_and_vmd.py: 9 passed
```

### 15.6 スモーク確認

- Codex軽量スモーク:
  - `tests/test_ms19_b3_transcription_contract.py tests/test_ms19_b3_textless_pipeline.py`: 6 passed / exit code 0
  - `tests/test_app_version.py`: 6 passed / exit code 0
  - `tests/test_wx_ms13_integration.py`: 4 passed / exit code 0
  - `tests/test_wx_startup_splash.py`: 表示上 2 passed。ただし pytest process の exit code は 1。
- ユーザースモークテスト:
  - 2026-07-06 にユーザー確認通過。
- `build.ps1 -Clean -SmokeLaunch`:
  - B3はpackaging変更ではないため未実行。

### 15.7 判定

```text
MS19-B3 closeout: OK
次に進むBlock: MS19-B4 GUI Entry Point and State Handling
```

### 15.8 変更有無

- Code changes: あり
- GUI changes: なし
- Test changes: あり
- Docs changes: あり。本実施結果と関連進行状況文書へMS19-B3完了を反映する。
