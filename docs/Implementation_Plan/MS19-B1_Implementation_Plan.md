# MS19-B1 Implementation Plan

## 1. 文書情報

- 文書名: MS19-B1 Implementation Plan
- 想定配置先: `docs/Implementation_Plan/MS19-B1_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 対象マイルストーン: MS19
- 対象Block: MS19-B1
- Block名: Voice-only Input Requirements / State Contract
- 基準ブランチ: `feature/MS19`
- 分岐元:
  - `main` / `d876397 Close out MS18`
- 関連文書:
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md`
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`
- 作成日: 2026-07-03
- 文書ステータス: Completed
- 作業種別:
  - 実装前要件整理
  - 状態契約定義
  - Block境界定義
- 実装変更:
  - なし

## 2. 背景

MS18はCloseOut済みであり、closeout判定は「A. MS18 closeout OK。package 化へ進める。」である。

MS19では、TEXT 必須前提を外し、音声ファイルのみから最低限の VMD 生成を成立させる。

現行実装では、TEXTあり入力が前提である。

- `src/core/pipeline.py`
  - `generate_vmd_from_text_wav()` は `text_path` を必須とする。
  - `build_vowel_timing_plan()` は `text_content` から母音列を生成する。
- `src/gui_wx/main_frame.py`
  - `解析実行` はTEXTと音声の両方が揃った場合のみ有効である。
  - `_run_analysis()` は `selected_text_content` が空の場合にエラーを出す。
- `src/gui_wx/analysis_worker.py`
  - `AnalysisWorker` は `text_content` を受け取り、`build_vowel_timing_plan()` へ渡す。
- `src/gui_wx/app_controller.py`
  - VMD保存時に `selected_text_path` を `generate_vmd_from_text_wav()` へ渡す。
- `src/core/text_processing.py`
  - TEXTからひらがな、ひらがなから5母音列への変換は既に存在する。
- `src/core/whisper_timing.py`
  - Whisperによる音声認識とtiming anchor抽出は存在するが、音声のみ入力の書き起こし本文をUI状態へ正本化する契約はまだない。

## 3. 目的

MS19-B1の目的は、音声のみ入力対応の実装に入る前に、TEXTあり / TEXTなしの状態契約と作業境界を固定することである。

具体的には、以下を定義する。

- TEXTあり既存導線を維持する条件
- TEXTなし音声のみ入力時の入力正本
- 書き起こし結果、ひらがな、母音列の保持方針
- timing plan生成に渡すテキスト相当データ
- VMD保存時に `text_path` がない場合の後続検討事項
- MS19-B2以降へ渡す確認項目

## 4. In Scope

MS19-B1では、以下を対象とする。

### 4.1 Repo / branch 状態確認

- `git status --short --branch`
- `git log --oneline -n 5`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md` のMS19節

### 4.2 現行TEXT必須導線の確認

- `src/core/pipeline.py`
- `src/core/text_processing.py`
- `src/core/whisper_timing.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/app_controller.py`

### 4.3 状態契約定義

- TEXTあり入力
- TEXTなし音声のみ入力
- 書き起こし未実行
- 書き起こし成功
- 書き起こし結果編集済み
- ひらがな生成済み
- 母音列生成済み
- timing plan生成済み
- VMD保存可能
- 入力変更による解析結果無効化

### 4.4 後続Block境界定義

- B2: transcription pipeline pre-check
- B3: textless core pipeline foundation
- B4: GUI entry point and state handling
- B5: transcription result review / edit
- B6: VMD / Preview / Save integration
- B7: error handling / tests / docs
- B8: closeout

## 5. Out of Scope

MS19-B1では、以下を行わない。

- コード変更
- GUI変更
- テスト追加
- Whisper実行処理の変更
- `UiState` の実装変更
- `generate_vmd_from_text_wav()` の変更
- VMD writer変更
- Preview / waveform仕様変更
- 新しい依存関係追加
- Whisper model管理UI
- 自動ダウンロード
- クラウドAPI連携
- 英語対応
- 多言語対応
- package / release 公開作業

## 6. 前提条件

MS19-B1を開始する前提は以下とする。

- MS18 CloseOut が完了している
- MS18 closeout 判定は A
- `feature/MS19` は `main` の `d876397 Close out MS18` から作成済み
- 作業ツリーは clean
- wxPython が主系である
- Qt / PySide6 GUIを復活させない
- MS19は音声のみ入力対応が主題であり、MS18の安定化作業とは混同しない
- 最初は日本語音声のみを対象とする
- 英語対応はMS19から除外する

## 7. 対象ファイル

MS19-B1で確認する主な対象は以下。

```text
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS19_Block_Breakdown.md
src/core/pipeline.py
src/core/text_processing.py
src/core/whisper_timing.py
src/gui_wx/ui_state.py
src/gui_wx/main_frame.py
src/gui_wx/analysis_worker.py
src/gui_wx/app_controller.py
tests/test_text_processing.py
tests/test_whisper_timing.py
tests/test_wx_ms14_b2_state.py
tests/test_wx_ms14_b3_input.py
```

必要に応じて、以下の仕様書もピンポイントで参照する。

```text
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Error_Handling_Specification.md
```

`docs/repo_milestone.md` と `docs/Version_Control.md` は巨大なため、MS19-B1では原則として全文読込しない。

## 8. 実装方針

MS19-B1では、実装変更を行わない。

作業方針は以下とする。

1. repo状態を確認する
2. MS17以降インデックスを確認する
3. ロードマップのMS19節を確認する
4. 現行TEXT必須導線を確認する
5. TEXTあり / TEXTなしの状態契約を定義する
6. 音声のみ入力時の入力正本を定義する
7. 書き起こし結果、ひらがな、母音列の保持方針を定義する
8. MS19-B2以降のBlock境界を固定する
9. 実装変更を行っていないことを確認する

## 9. 詳細ステップ

### 9.1 Step 1: 作業開始前のGit状態確認

以下を順に実行する。

```powershell
git status --short --branch
git log --oneline -n 5
```

確認すること。

- 現在ブランチが `feature/MS19` であること
- working tree が clean であること
- 現在の最新コミットを記録すること
- 履歴に分岐元 `d876397 Close out MS18` が含まれること

### 9.2 Step 2: インデックス確認

確認対象。

```text
docs/MS17_and_Beyond_Index.md
```

確認すること。

- MS18 CloseOut 完了状態
- MS19へ進める前提
- 音声処理、GUI状態、テストファイルの現在の入口

### 9.3 Step 3: MS19ロードマップ確認

確認対象。

```text
docs/MS18_and_Beyond_Roadmap.md
```

確認すること。

- MS19の目的
- In Scope
- Out of Scope
- 想定Block構成
- MS19の受け入れ条件
- MS19のリスクと対策

### 9.4 Step 4: 現行TEXT必須導線確認

確認対象。

```text
src/core/pipeline.py
src/gui_wx/main_frame.py
src/gui_wx/analysis_worker.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
```

確認すること。

- TEXT pathが必須になっている箇所
- TEXT contentが必須になっている箇所
- 解析実行ボタンの有効条件
- VMD保存時の `text_path` 依存
- timing plan と Preview / VMD保存の関係

### 9.5 Step 5: 既存変換部品確認

確認対象。

```text
src/core/text_processing.py
src/core/whisper_timing.py
```

確認すること。

- 書き起こし結果を `text_to_hiragana()` / `text_to_vowel_sequence()` に渡せるか
- pyopenjtalk変換失敗時の扱い
- Whisper raw resultから本文を取り出せるか
- timing anchor抽出と本文抽出を同一実行結果から扱えるか

## 10. 状態遷移 / データ契約

MS19-B1時点の設計契約は以下とする。

### 10.1 入力モード

```text
TextAudioInput:
  TEXTファイル + 音声ファイルを入力する既存モード。
  MS18以前の既存導線を維持する。

VoiceOnlyInput:
  音声ファイルのみを入力するMS19追加モード。
  TEXTファイルpathは存在しない。
  書き起こし結果を、解析用のテキスト相当データとして扱う。
```

### 10.2 TEXTあり入力の契約

TEXTあり入力では、既存契約を維持する。

```text
selected_text_path:
  実ファイルpath。

selected_text_content:
  UTF-8 TEXTを検証・整形した内容。

selected_hiragana_content:
  selected_text_content から生成したひらがな。

selected_vowel_content:
  selected_hiragana_content から生成した5母音列。
```

解析実行条件は、従来どおりTEXTと音声の両方が揃うことを基本とする。MS19で条件を拡張する場合も、TEXTあり導線の条件を弱めて壊さない。

### 10.3 音声のみ入力の契約

音声のみ入力では、TEXTファイルpathは存在しない。

代替として、以下の論理データを導入する方針とする。

```text
transcription_text:
  Whisper等で得た書き起こし本文。
  ユーザー編集前または編集後の解析用正本。

transcription_source:
  書き起こし本文の由来。
  例: whisper_segments, whisper_words, user_edited

generated_hiragana_content:
  transcription_text から生成したひらがな。

generated_vowel_content:
  generated_hiragana_content から生成した5母音列。

input_mode:
  text_audio または voice_only。
```

B1時点では名称は契約候補であり、実装名はB3 / B4で確定する。

### 10.4 timing plan生成の契約

`build_vowel_timing_plan()` は現時点で `text_content` を受け取る。

MS19では、TEXTあり / 音声のみのどちらでも、最終的に以下を満たす文字列を `text_content` 相当として渡す。

```text
- 空でない
- 日本語読み生成またはひらがな化が可能
- 5母音列へ変換可能
- 解析対象音声と対応しているとユーザーが判断できる
```

B3では、既存関数へ文字列を渡す最小拡張を優先する。pipeline全体の意味論変更やVMD writer再設計は行わない。

### 10.5 VMD保存の契約

現行 `generate_vmd_from_text_wav()` は `text_path` を必須とする。

MS19では、以下のいずれかをB3 / B6で判断する。

```text
案A:
  text_path を持たない保存用入口を追加する。
  timing_plan と wav_path からVMD保存する責務を分離する。

案B:
  generate_vmd_from_text_wav() の text_path を optional にする。
  TEXTあり既存動作を壊さないよう分岐する。
```

B1時点の推奨は案Aである。

理由:
- 現行関数名と責務が TEXT + WAV を明示している。
- TEXTなし入力では実ファイルpathが存在しない。
- 既存TEXTあり保存導線への影響範囲を小さくできる。

ただし、最終判断はB3でコード構造を確認して行う。

### 10.6 状態無効化契約

以下の場合、既存と同様に解析結果を無効化する。

```text
- 音声ファイルが変更された
- TEXTファイルが変更された
- 音声のみ入力の書き起こし結果が変更された
- 書き起こし結果のユーザー編集が確定した
- 解析パラメータが変更された
```

## 11. テスト方針

MS19-B1では、実装変更を行わないため、自動テストは必須ではない。

B2以降で想定するテスト候補は以下。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_whisper_timing.py
.\.venv\Scripts\python.exe -m pytest tests/test_text_processing.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
```

MS19実装中に追加するテスト候補。

```text
tests/test_ms19_b2_transcription_contract.py
tests/test_ms19_b3_textless_pipeline.py
tests/test_ms19_b4_voice_only_gui_state.py
tests/test_ms19_b6_voice_only_vmd_save.py
```

テスト設計では、必ず以下を分けて確認する。

- TEXTあり既存導線
- TEXTなし音声のみ導線
- 書き起こし失敗
- 書き起こし結果が空
- ひらがな生成失敗
- 母音列が空
- VMD保存
- Preview表示

## 12. 受け入れ条件

MS19-B1の完了条件は以下。

- `feature/MS19` 上で作業していることが確認されている
- MS18 CloseOut 完了状態が確認されている
- MS19の目的、In Scope、Out of Scopeが確認されている
- 現行TEXT必須導線が確認されている
- TEXTあり入力の既存契約を維持する方針が明記されている
- 音声のみ入力時の入力正本が定義されている
- `selected_text_path` が存在しない場合の代替契約が定義されている
- 書き起こし結果、ひらがな、母音列の保持方針が定義されている
- VMD保存時の `text_path` 依存が後続Blockの検討対象として明記されている
- MS19-B2以降の作業境界が定義されている
- 実装変更が行われていない

## 13. リスクと対策

### 13.1 TEXTあり既存導線を壊す

#### リスク

音声のみ入力のために解析実行条件やpipeline入口を変更すると、既存のTEXT + 音声入力が壊れる可能性がある。

#### 対策

- TEXTあり入力を `TextAudioInput` として明示的に維持する。
- 既存テスト `tests/test_wx_ms14_b2_state.py` / `tests/test_wx_ms14_b3_input.py` を回帰確認に含める。
- B3以降では既存関数の置換ではなく、分岐または新規入口を優先する。

### 13.2 書き起こし本文とtiming anchorが不整合になる

#### リスク

Whisperの本文とtiming anchorを別実行で取得すると、結果がずれて母音列とタイミングの対応が不安定になる可能性がある。

#### 対策

- B2で、同一raw resultから本文とanchorを抽出できるか確認する。
- 可能であれば transcription result と timing anchors を1つの契約として扱う。
- 別実行が必要な場合は、差異が起きることを明示し、最小リスクの実装に限定する。

### 13.3 音声のみ入力の範囲が広がる

#### リスク

書き起こし、読み生成、母音変換、GUI状態、Preview、VMD保存が連鎖し、MS19の範囲が英語対応や高度編集まで広がる可能性がある。

#### 対策

- 最初は日本語音声のみを対象とする。
- 英語対応、多言語対応、任意モーフ対応、モーフ編集はOut of Scopeに固定する。
- Review / Edit flow はB5に分離し、B3 / B4で過剰に作り込まない。

### 13.4 VMD保存時のTEXT path依存

#### リスク

`generate_vmd_from_text_wav()` がTEXT path必須であるため、音声のみ入力では保存時に不要な仮TEXTファイルを作る誘惑がある。

#### 対策

- B1では、仮TEXTファイル生成を既定方針にしない。
- B3 / B6で、timing_plan と wav_path から保存できる入口を検討する。
- TEXTあり保存導線は既存関数で維持する。

## 14. MS19-B1 実施結果

実施日: 2026-07-04

MS19-B1 は、コード変更を行わず、Voice-only Input 実装前の状態契約固定、現行TEXT必須導線の確認、後続Block境界の整理を実施した。

### 14.1 Git状態

- Current branch: `feature/MS19`
- Latest commit at start: `d2580de Add MS19 planning docs`
- Branch base included in history: `d876397 Close out MS18`
- Working tree at start: clean

### 14.2 確認したファイル

```text
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS19_Block_Breakdown.md
docs/Implementation_Plan/MS19-B1_Implementation_Plan.md
src/core/pipeline.py
src/core/text_processing.py
src/core/whisper_timing.py
src/gui_wx/ui_state.py
src/gui_wx/main_frame.py
src/gui_wx/analysis_worker.py
src/gui_wx/app_controller.py
tests/
README.md
readme_mmdautolip.txt
pyproject.toml
requirements.txt
```

### 14.3 確認結果

- MS18 CloseOut は完了済みで、MS19へ進む前提は満たされている。
- MS19のBlock構成は、`docs/MS18_and_Beyond_Roadmap.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、本B1計画で一致している。
- 現行実装では、解析実行とVMD保存はTEXTあり入力を前提としている。
- `src/core/pipeline.py` の `generate_vmd_from_text_wav()` は `text_path` を必須とし、`PipelineResult` も `text_path` を持つ。
- `src/core/pipeline.py` の `build_vowel_timing_plan()` は `text_content` から母音列を生成する。
- `src/gui_wx/main_frame.py` の `解析実行` は、TEXTと音声の両方が揃った場合のみ有効である。
- `src/gui_wx/analysis_worker.py` は `text_content` を `build_vowel_timing_plan()` へ渡す。
- `src/gui_wx/app_controller.py` のVMD保存は `selected_text_path` を `generate_vmd_from_text_wav()` へ渡す。
- `src/core/text_processing.py` には、TEXTからひらがな、ひらがなから5母音列への変換部品が存在する。
- `src/core/whisper_timing.py` には、Whisper raw result、timing anchor抽出、`raw_result`保持の契約が存在する。ただし、音声のみ入力の書き起こし本文をUI状態へ正本化する契約は未実装である。
- README / readme は現行のTEXT + 音声入力仕様を説明しており、音声のみ入力を実装済みとは記載していない。

### 14.4 固定した状態契約

```text
TextAudioInput:
  既存の TEXTファイル + 音声ファイル入力モード。
  selected_text_path / selected_text_content / selected_hiragana_content / selected_vowel_content を維持する。

VoiceOnlyInput:
  MS19で追加する音声ファイルのみ入力モード。
  TEXTファイルpathは存在しない。
  transcription_text を解析用テキスト相当データとして扱う。
  transcription_text から generated_hiragana_content と generated_vowel_content を生成する。
```

VMD保存については、B3 / B6で以下の判断を行う。

```text
推奨:
  text_path を持たない保存用入口を追加し、timing_plan と wav_path からVMD保存する責務を分離する。

代替:
  generate_vmd_from_text_wav() の text_path を optional にする。
```

### 14.5 Risk Inventory

```text
P1:
  なし。

P2:
  なし。

P3:
  なし。
```

### 14.6 MS19-B2以降への引き継ぎ

MS19-B2では、既存 `src/core/whisper_timing.py` を、音声のみ入力の書き起こし本文取得に使えるか確認する。

重点確認項目:

```text
- recognize_audio() の raw result から本文を抽出できるか
- recognize_audio_timing() の raw_result と timing anchors を同一契約で扱えるか
- segment text / word text のどちらを transcription_text の初期値にするか
- Whisper失敗、空本文、非日本語らしい結果をどうエラー分類するか
- tests/test_whisper_timing.py に不足する契約テストは何か
```

### 14.7 判定

```text
MS19-B1 closeout: OK
次に進むBlock: MS19-B2 Transcription Pipeline Pre-check
```

### 14.8 変更有無

- Code changes: なし
- GUI changes: なし
- Test changes: なし
- Docs changes: あり。本実施結果と関連進行状況文書へMS19-B1完了を反映する。

## 15. Codex 実装時の注意

MS19-B1をCodexに依頼する場合は、以下を明示する。

```text
今回は MS19-B1: Voice-only Input Requirements / State Contract の作業です。

このBlockでは、実装変更を行わないでください。
コード変更、GUI変更、テスト追加、依存関係追加は禁止です。

feature/MS19 を作業ブランチとして扱ってください。

まず以下を順に確認してください。

git status --short --branch
git log --oneline -n 5
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md の MS19 節

確認対象は以下です。

src/core/pipeline.py
src/core/text_processing.py
src/core/whisper_timing.py
src/gui_wx/ui_state.py
src/gui_wx/main_frame.py
src/gui_wx/analysis_worker.py
src/gui_wx/app_controller.py

確認してください。

- 現行TEXT必須導線
- TEXTあり入力で維持すべき状態契約
- TEXTなし入力で追加すべき状態契約
- 書き起こし結果、ひらがな、母音列の保持方針
- VMD保存時の text_path 依存
- MS19-B2以降への引き継ぎ

完了報告では、以下を必ず記載してください。

1. 現在ブランチ
2. 最新コミット
3. working tree状態
4. 確認したファイル
5. MS19-B1で定義した状態契約
6. MS19-B2以降への引き継ぎ
7. 実装変更を行っていないこと
```
