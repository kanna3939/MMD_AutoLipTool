# MS19-B2 Implementation Plan

## 1. 文書情報

- 文書名: MS19-B2 Implementation Plan
- 想定配置先: `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 対象マイルストーン: MS19
- 対象Block: MS19-B2
- Block名: Transcription Pipeline Pre-check
- 基準ブランチ: `feature/MS19`
- 分岐元:
  - `main` / `d876397 Close out MS18`
- 関連文書:
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS19-B1_Implementation_Plan.md`
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/Error_Handling_Specification.md`
- 作成日: 2026-07-04
- 文書ステータス: Completed
- 作業種別:
  - 実装前調査
  - transcription契約確認
  - B3実装境界定義
- 実装変更:
  - 原則なし

## 2. 背景

MS19-B1では、TEXTあり / TEXTなしの状態契約を固定し、音声のみ入力では `transcription_text` を解析用テキスト相当データとして扱う方針を定義した。

現行実装には、Whisperを使ったタイミング抽出の部品が存在する。

- `src/core/whisper_timing.py`
  - `recognize_audio()` は Whisper raw result を返す。
  - `recognize_audio_timing()` は `WhisperTimingResult` として `anchors`、`raw_result`、`source` を返す。
  - timing anchor は word timestamps を優先し、不足時は segment timestamps にfallbackする。
- `src/core/pipeline.py`
  - `build_vowel_timing_plan()` は `text_content` から母音列を生成し、同じ音声から `recognize_audio_timing()` でtiming anchorを取得する。
  - `generate_vmd_from_text_wav()` はTEXT pathを必須とするため、TEXTなし保存契約はB3 / B6で扱う。
- `src/core/text_processing.py`
  - 書き起こし本文を文字列として渡せれば、ひらがな化・5母音列変換を既存部品で再利用できる。

一方で、現時点では Whisper raw result から音声のみ入力用の本文を取り出し、UI状態またはpipeline契約上の正本として扱う実装契約は未固定である。

## 3. 目的

MS19-B2の目的は、既存 `whisper_timing.py` を音声のみ入力の書き起こし本文取得に使えるか確認し、B3以降で追加すべき最小契約を定義することである。

具体的には、以下を確認する。

- Whisper raw result から `transcription_text` を抽出する候補
- segment text と word text のどちらを初期本文の正本にするか
- `recognize_audio_timing()` の `raw_result` と timing anchor を同一実行結果として扱えるか
- Whisper失敗、空本文、anchor欠落、本文とanchor不整合のエラー分類
- 既存 `tests/test_whisper_timing.py` の不足
- B3でproduction codeへ入れるべき最小変更点

## 4. In Scope

MS19-B2では、以下を対象とする。

### 4.1 Repo / document 状態確認

- `git status --short --branch`
- `git log --oneline -n 5`
- `docs/MS17_and_Beyond_Index.md`
- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/Implementation_Plan/MS19-B1_Implementation_Plan.md`

### 4.2 Whisper transcription契約確認

- `src/core/whisper_timing.py`
- `tests/test_whisper_timing.py`

確認すること。

- `recognize_audio()` の戻り値が raw result dict であること
- `recognize_audio_timing()` が `raw_result` を保持していること
- word timestamps使用時とsegment fallback時で、本文抽出に使うraw resultが失われないこと
- `segments[].text` と `segments[].words[].word` のどちらが本文正本として安定するか
- 空白、空文字、非dict、segments欠落などの扱い

### 4.3 既存pipelineとの接続点確認

- `src/core/pipeline.py`
- `src/core/text_processing.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_text_processing.py`

確認すること。

- `build_vowel_timing_plan()` が `text_content` を受け取る既存契約
- `text_to_hiragana()` / `text_to_vowel_sequence()` に書き起こし本文を渡す場合の前提
- Whisper timing失敗時に既存pipelineがeven fallbackへ進む挙動
- 音声のみ入力で本文が空の場合、B3でどの層が止めるべきか

### 4.4 エラー分類確認

- `src/core/whisper_timing.py`
- `src/core/audio_errors.py`
- `docs/Error_Handling_Specification.md`

確認すること。

- 現行実装ではWhisper系失敗が `src/core/whisper_timing.py` の `WhisperTimingError` に閉じていること
- `src/core/audio_errors.py` は音声入力 / ffprobe / ffmpeg / MMD用WAV出力系の分類を持つが、Whisper専用の `AudioErrorCode` はまだ持たないこと
- `docs/Error_Handling_Specification.md` のL4 Whisper分類と、現行 `WhisperTimingError` の対応関係
- Whisper import失敗
- model load失敗
- transcription実行失敗
- raw result型不正
- raw resultに本文候補がない
- `recognize_audio_timing()` が `WhisperTimingError` を投げる「usable timing anchorなし」
- `build_vowel_timing_plan()` がwarningを持ってeven fallbackへ進む「speech interval内にclip後anchorなし」
- 本文はあるが母音列が空

### 4.5 B3への引き継ぎ定義

- `transcription_text` 抽出規則
- `TranscriptionResult` 相当のデータ契約候補
- B3で追加するproduction code候補
- B3で追加するテスト候補

## 5. Out of Scope

MS19-B2では、以下を行わない。

- production codeの挙動変更
- GUI変更
- `UiState` 変更
- `AnalysisWorker` 変更
- `generate_vmd_from_text_wav()` 変更
- VMD writer変更
- Whisper model管理UI
- 自動モデルダウンロード導線
- クラウド文字起こし
- 英語対応
- 多言語対応
- 書き起こし結果の編集UI
- package / release公開作業

ただし、B2実施時に明らかな契約テスト不足があり、かつproduction code変更なしで固定できる場合は、ユーザー確認後にテスト追加を別作業として扱う。

## 6. 前提条件

MS19-B2を開始する前提は以下とする。

- MS18 CloseOut が完了している
- MS19-B1 が完了している
- TEXTあり / TEXTなし状態契約が定義済みである
- `feature/MS19` 上で作業する
- wxPython が主系である
- Qt / PySide6 GUIを復活させない
- 最初は日本語音声のみを対象とする
- 英語対応、多言語対応、クラウドAPI、自動ダウンロードはMS19から除外する
- B2はB3実装前のpre-checkであり、production code変更はB3へ送る

## 7. 対象ファイル

MS19-B2で確認する主な対象は以下。

```text
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS19_Block_Breakdown.md
docs/Implementation_Plan/MS19-B1_Implementation_Plan.md
docs/Implementation_Plan/MS19-B2_Implementation_Plan.md
src/core/whisper_timing.py
src/core/pipeline.py
src/core/text_processing.py
tests/test_whisper_timing.py
tests/test_pipeline_and_vmd.py
tests/test_text_processing.py
```

必要に応じて、以下もピンポイントで参照する。

```text
docs/Pipeline_Data_Contract_Specification.md
docs/Error_Handling_Specification.md
src/core/audio_errors.py
```

`docs/repo_milestone.md` と `docs/Version_Control.md` は巨大なため、MS19-B2では原則として全文読込しない。

## 8. 実装方針

MS19-B2では、実装前確認を主目的とし、production code変更を行わない。

作業方針は以下とする。

1. repo状態を確認する
2. MS17以降インデックスを確認する
3. MS19-B1の状態契約を確認する
4. `whisper_timing.py` のraw result保持とanchor抽出契約を確認する
5. Whisper raw resultから本文を抽出する候補を比較する
6. 既存pipelineが必要とする `text_content` 契約と照合する
7. エラー分類とユーザー通知の不足を整理する
8. 既存テストの不足を整理する
9. B3へ渡すproduction code変更候補を明文化する

## 9. 詳細ステップ

### 9.1 Step 1: 作業開始前のGit状態確認

以下を順に実行する。

```powershell
git status --short --branch
git log --oneline -n 5
```

確認すること。

- 現在ブランチが `feature/MS19` であること
- 未コミット変更の有無
- 現在の最新コミット
- MS19-B1関連の未コミット差分がある場合、その範囲

### 9.2 Step 2: MS19状態確認

確認対象。

```text
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS19_Block_Breakdown.md
docs/Implementation_Plan/MS19-B1_Implementation_Plan.md
```

確認すること。

- MS19-B1が完了扱いであること
- 次作業がMS19-B2であること
- B2がB3実装前のpre-checkとして定義されていること

### 9.3 Step 3: Whisper raw result確認

確認対象。

```text
src/core/whisper_timing.py
```

確認すること。

- `recognize_audio()` が返すraw resultの型確認
- `recognize_audio_timing()` が `raw_result` を保持する条件
- word timestamps実行でsegment textも保持されるか
- segment fallback実行時に `raw_result` が失われないか
- `source` が `words` / `segments` のどちらになるか
- `extract_timing_anchors()` と内部 `_extract_*_anchors()` の責務境界

### 9.4 Step 4: transcription_text抽出候補の比較

raw resultからの本文抽出候補を比較する。

```text
候補A:
  raw_result["text"] を優先する。

候補B:
  segments[].text を連結する。

候補C:
  words[].word を連結する。
```

B2時点の推奨は候補Bである。

理由:

- timing anchor fallbackと同じ `segments` を基準にしやすい。
- word timestampsが不足しても本文を得られる可能性が高い。
- wordsは分割粒度や空白の扱いが不安定になりやすい。
- raw_result全体の `text` は存在すれば有用だが、segmentsとの対応検証が必要である。

ただし、B2実施時に実コード・テストで `raw_result["text"]` の安定性が確認できる場合は、候補Aを優先する判断も許容する。

### 9.5 Step 5: pipeline接続前提確認

確認対象。

```text
src/core/pipeline.py
src/core/text_processing.py
```

確認すること。

- `build_vowel_timing_plan(text_content=...)` に渡す文字列の条件
- `text_to_vowel_sequence()` が空母音列を返す条件
- pyopenjtalk失敗時の例外
- Whisper timing失敗時のeven fallbackと、本文抽出失敗時の扱いを混同しないこと
- `PipelineResult.text_path` は現行実装では必須 `Path` であり、TEXTなし保存契約はB3 / B6で扱うこと

### 9.6 Step 6: テスト不足確認

確認対象。

```text
tests/test_whisper_timing.py
tests/test_pipeline_and_vmd.py
tests/test_text_processing.py
```

確認すること。

- `WhisperTimingResult.raw_result` が保持されることを直接検証しているか
- segment fallback時のraw result保持を検証しているか
- 本文抽出ヘルパーを追加する場合の正常系・空本文・不正型テスト候補
- TEXTあり既存pipelineを壊さない回帰テスト候補

### 9.7 Step 7: B3引き継ぎ作成

B2実施結果として、B3へ以下を引き継ぐ。

```text
- transcription_text抽出規則
- raw_result / anchors / source をまとめるデータ契約候補
- 空本文の停止位置
- Whisper timing失敗と本文抽出失敗のエラー分類
- B3で変更するproduction code候補
- B3で追加するテスト候補
```

## 10. 状態遷移 / データ契約

MS19-B2で確認・固定する契約候補は以下。

### 10.1 Whisper raw result契約

```text
WhisperRawResult:
  Whisper model.transcribe() が返すdict。
  少なくとも segments を持つ可能性がある。
  text は存在する場合があるが、B2で安定性を確認する。
```

### 10.2 Transcription候補契約

B3で追加するデータ構造候補。

```text
TranscriptionResult:
  text: str
  raw_result: dict[str, Any]
  anchors: list[SpeechTimingAnchor]
  timing_source: str
  text_source: str
```

`text_source` の候補。

```text
raw_text:
  raw_result["text"] 由来。

segments:
  segments[].text 連結由来。

words:
  segments[].words[].word 連結由来。

user_edited:
  B5以降でユーザー編集済み本文を扱う場合。
```

### 10.3 空本文契約

音声のみ入力では、本文抽出に失敗した状態とtiming anchor取得に失敗した状態を分ける。

```text
本文抽出失敗:
  transcription_text が空。
  B3以降では音声のみ入力の解析を止める候補。

timing anchor取得失敗:
  transcription_text はあるがanchorsが空。
  既存pipelineのeven fallbackを使える可能性がある。
```

現行実装では、anchor欠落には少なくとも以下の2種類がある。

```text
usable timing anchorなし:
  recognize_audio_timing() が WhisperTimingError を送出する。
  build_vowel_timing_plan() は例外を捕捉し、warningを保持してeven fallbackへ進む。

speech interval内にclip後anchorなし:
  recognize_audio_timing() 自体は成功している。
  build_vowel_timing_plan() は "Whisper returned no anchors inside the detected speech interval." をwarningとして保持し、even fallbackへ進む。
```

### 10.4 既存TEXTあり導線との関係

TEXTあり入力では、引き続きTEXTファイル内容を `text_content` の正本とする。

音声のみ入力では、`transcription_text` を `text_content` 相当として扱うが、TEXTファイルpathは生成しない。

B2ではこの契約を確認するだけで、GUI状態やVMD保存入口は変更しない。

## 11. テスト方針

MS19-B2のpre-checkでは、まず既存テストを確認対象とする。

想定コマンド。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests/test_text_processing.py
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py
```

B2でproduction code変更を行わない場合、自動テスト実行は必須ではないが、実行した場合は結果を記録する。

B3以降で追加するテスト候補。

```text
tests/test_ms19_b3_transcription_contract.py
tests/test_ms19_b3_textless_pipeline.py
```

B2で記録すべきテスト不足。

- raw resultから本文抽出する正常系
- `segments[].text` 連結時の空白整理
- `raw_result["text"]` 欠落時のfallback
- segments欠落時の空本文エラー
- timing anchorsが空でも本文があるケース
- TEXTあり既存pipelineの回帰

## 12. 受け入れ条件

MS19-B2の完了条件は以下。

- `feature/MS19` 上で作業していることが確認されている
- MS19-B1完了状態が確認されている
- `recognize_audio()` のraw result契約が確認されている
- `recognize_audio_timing()` の `raw_result` 保持契約が確認されている
- segment text / word text / raw text の本文抽出候補が比較されている
- 音声のみ入力の `transcription_text` 初期値候補が定義されている
- Whisper失敗、空本文、anchor欠落の扱いが分類されている
- 既存テストの不足が整理されている
- B3へ渡すproduction code変更候補が明記されている
- production code変更を行っていない、または行った場合はユーザー承認と理由が記録されている

## 13. リスクと対策

### 13.1 本文抽出とtiming anchorが別結果になる

#### リスク

本文抽出のためにWhisperを再実行すると、timing anchor取得時と結果がずれる可能性がある。

#### 対策

- `recognize_audio_timing()` が返す `raw_result` から本文を抽出する方針を優先する。
- B2で同一raw resultから本文候補とanchorsを得られるか確認する。
- 再実行が必要な設計はB3の既定方針にしない。

### 13.2 raw_result["text"] と segments[].text が不一致になる

#### リスク

Whisper raw resultのtop-level textとsegments textが、空白・句読点・分割単位の違いで一致しない可能性がある。

#### 対策

- B2で候補A/B/Cを比較する。
- 初期本文は、timing anchorとの対応を説明しやすいものを優先する。
- 表記差はB5のreview / edit flowでユーザー確認可能にする。

### 13.3 timing anchor失敗と本文失敗を混同する

#### リスク

本文は取得できているのにanchorがないケースと、本文自体が空のケースを同じエラーにすると、既存even fallbackを使える場面まで止める可能性がある。

#### 対策

- B2で空本文とanchor欠落を別分類にする。
- B3では本文が空の場合は停止、anchorが欠落した場合は既存pipeline fallback候補として扱う。

### 13.4 B2で実装範囲が広がる

#### リスク

B2で本文抽出ヘルパー、pipeline接続、GUI状態、保存導線まで同時に実装すると、B3以降の境界が崩れる。

#### 対策

- B2はpre-checkに限定する。
- production code変更はB3へ送る。
- テスト追加が必要な場合も、ユーザー確認後に別作業として扱う。

## 14. MS19-B2 実施結果

実施日: 2026-07-05

MS19-B2 は、production code変更を行わず、既存 `whisper_timing.py` のraw result保持、書き起こし本文抽出候補、timing anchor契約、エラー分類、既存テスト不足、B3への引き継ぎを確認した。

### 14.1 Git状態

- Current branch: `feature/MS19`
- Latest commit at start: `b7be4d9 Document MS19 B1 closeout and B2 plan`
- Working tree at start: clean

### 14.2 確認したファイル

```text
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS19-B2_Implementation_Plan.md
src/core/whisper_timing.py
src/core/pipeline.py
src/core/text_processing.py
src/core/audio_errors.py
docs/Error_Handling_Specification.md
tests/test_whisper_timing.py
tests/test_text_processing.py
tests/test_pipeline_and_vmd.py
```

### 14.3 transcription_text 抽出候補の比較結果

Whisper raw result からの本文抽出候補は以下のように整理した。

```text
候補A: raw_result["text"]
  全体書き起こし本文として存在する場合がある。
  ただし現行テストでは存在・型・segmentsとの整合を保証していない。
  B3ではfallback候補として扱う。

候補B: segments[].text
  現行 anchor fallback と同じ segments 構造を基準にできる。
  word timestamps が不足しても本文を得られる可能性が高い。
  B3の初期 transcription_text の第一候補とする。

候補C: segments[].words[].word
  word timestamps が得られる場合は細粒度だが、分割粒度・空白・欠落の影響を受けやすい。
  B3では本文正本の第一候補にしない。
```

B3への推奨契約:

```text
1. segments[].text の非空文字列を正規化して連結する。
2. segments から本文を得られない場合のみ raw_result["text"] をfallbackとして使う。
3. words[].word は timing anchor 由来情報として扱い、初期 transcription_text の正本にはしない。
4. どちらからも非空本文を得られない場合、音声のみ入力の解析は停止する。
```

### 14.4 raw_result / anchors / source 契約

`recognize_audio_timing()` は、成功時に `WhisperTimingResult` として以下を返す。

```text
anchors:
  word anchors または segment anchors。

raw_result:
  anchors 抽出に使われた Whisper raw result。

source:
  "words" または "segments"。
```

word timestamps 実行で word anchors が複数得られる場合は `source="words"` となり、同じ `result_with_words` が `raw_result` として保持される。

word anchors が不足し、同じ実行結果内の segment anchors にfallbackする場合も、`result_with_words` が `raw_result` として保持される。

word timestamps 実行で usable anchors が得られず、segment-only再実行で成功する場合は、`result_with_segments` が `raw_result` として保持される。

### 14.5 エラー分類

現行実装では、Whisper系失敗は `src/core/whisper_timing.py` の `WhisperTimingError` に閉じている。`src/core/audio_errors.py` には、Whisper専用の `AudioErrorCode` はまだ存在しない。

B2時点の分類は以下とする。

```text
Whisper import / model load / transcribe / raw result型不正:
  recognize_audio() または _load_whisper_model() が WhisperTimingError を送出する。
  既存TEXTありpipelineでは build_vowel_timing_plan() が捕捉し、warning付きeven fallbackへ進む。

usable timing anchorなし:
  recognize_audio_timing() が WhisperTimingError を送出する。
  既存TEXTありpipelineでは warning付きeven fallbackへ進む。

speech interval内にclip後anchorなし:
  recognize_audio_timing() 自体は成功している。
  build_vowel_timing_plan() が warning を保持し、even fallbackへ進む。

transcription_text 空:
  音声のみ入力では解析を停止する。
  timing anchor欠落とは別扱いにする。

本文はあるが母音列が空、または text_processing 変換失敗:
  音声のみ入力では解析を停止する。
  B3では text_processing 側の TextProcessingError / ValueError をユーザー向け失敗として扱う候補。
```

`docs/Error_Handling_Specification.md` には L4 Whisper分類として `whisper_model_load_failed`、`whisper_transcribe_failed`、`whisper_result_invalid`、`whisper_no_segments`、`whisper_no_words` などが定義されている。B3では実装を増やしすぎず、B7でユーザー通知・分類名・GUI表示との整合をまとめて扱う。

### 14.6 既存テスト不足

既存 `tests/test_whisper_timing.py` は以下を確認している。

```text
- word anchors が疎な場合に segment anchors を優先すること
- 複数word anchorsがある場合に words を優先すること
```

一方で、以下は未検証である。

```text
- WhisperTimingResult.raw_result が保持されること
- word run内segment fallback時の raw_result 保持
- segment-only再実行成功時の raw_result 保持
- raw_result["text"] / segments[].text / words[].word からの本文抽出
- segments欠落、非dict、空text、不正型の扱い
- transcription_text が空の場合に音声のみ入力を停止する契約
```

### 14.7 B3への引き継ぎ

B3では、production codeの最小追加として以下を検討する。

```text
- src/core/whisper_timing.py に transcription_text 抽出ヘルパーを追加する。
- 例: extract_transcription_text(raw_result: dict[str, Any]) -> TranscriptionTextResult または str
- primary source は segments[].text とする。
- raw_result["text"] はfallback候補とする。
- words[].word は初期本文正本にしない。
- 空本文は音声のみ入力の停止条件にする。
- raw_result / anchors / timing_source / text_source をまとめる TranscriptionResult 相当のデータ契約を定義する。
- GUI、UiState、VMD保存入口はB3では必要最小限に留め、B4 / B6へ分離する。
```

B3で追加するテスト候補:

```text
tests/test_ms19_b3_transcription_contract.py
tests/test_ms19_b3_textless_pipeline.py
```

重点テスト:

```text
- segments[].text から transcription_text を抽出する
- raw_result["text"] fallback
- words[].word を本文正本にしない
- 空segments / 空text / 不正型で空本文扱いにする
- raw_result と anchors を同一契約で保持する
- TEXTあり既存pipelineを壊さない
```

### 14.8 実行したテスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py
```

### 14.9 テスト結果

```text
tests/test_whisper_timing.py: 2 passed
tests/test_text_processing.py: 10 passed
tests/test_pipeline_and_vmd.py: 9 passed
```

合計21件通過。

### 14.10 判定

```text
MS19-B2 closeout: OK
次に進むBlock: MS19-B3 Textless Pipeline Integration Foundation
```

### 14.11 変更有無

- Code changes: なし
- GUI changes: なし
- Test changes: なし
- Docs changes: あり。本実施結果と関連進行状況文書へMS19-B2完了を反映する。

## 15. Codex 実装時の注意

MS19-B2をCodexに依頼する場合は、以下を明示する。

```text
今回は MS19-B2: Transcription Pipeline Pre-check の作業です。

このBlockでは、production code変更を原則行わないでください。
GUI変更、UiState変更、VMD保存入口変更、Whisper model管理UI、自動ダウンロード、クラウドAPI、英語対応は禁止です。

feature/MS19 を作業ブランチとして扱ってください。

まず以下を順に確認してください。

git status --short --branch
git log --oneline -n 5
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS19_Block_Breakdown.md
docs/Implementation_Plan/MS19-B1_Implementation_Plan.md

確認対象は以下です。

src/core/whisper_timing.py
src/core/pipeline.py
src/core/text_processing.py
tests/test_whisper_timing.py
tests/test_pipeline_and_vmd.py
tests/test_text_processing.py

確認してください。

- recognize_audio() のraw result契約
- recognize_audio_timing() のraw_result保持契約
- segment text / word text / raw text の本文抽出候補
- transcription_text 初期値候補
- Whisper失敗、空本文、anchor欠落の分類
- 既存テスト不足
- B3へ渡すproduction code変更候補

完了報告では、以下を必ず記載してください。

1. 現在ブランチ
2. 最新コミット
3. working tree状態
4. 確認したファイル
5. transcription_text抽出候補の比較結果
6. エラー分類
7. テスト不足
8. B3への引き継ぎ
9. production code変更を行っていないこと、または行った場合の承認・理由
```
