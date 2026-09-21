# MS17-B6 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B6
- Block name: wav / mp3 / m4a 入力導線統合
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B6_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Google Antigravity
- Coding AI: Gemini 3.1 Pro
- Shell: Windows PowerShell
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作業種別: 実装
- 実装変更: あり
- GUI文言変更: あり
- GUI大規模再設計: 禁止
- 処理方式: 既存構造に合わせた同期処理を基本とする
- worker / Busy / cancel / late callback統合: MS17-B8へ送る
- MMD用WAV出力: MS17-B7へ送る
- 300秒確認ダイアログ: MS17-B8へ送る

---

## 2. 背景

MS17-B3では、FFmpeg / ffprobe locator と入力音声種別判定基盤を追加した。

B3で追加済みの主なファイルは以下。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
````

B3で確定した主な仕様は以下。

```text
- ffmpeg / ffprobe の探索順:
  1. repo直下 FFmpeg\bin
  2. PyInstaller onefile 展開先 sys._MEIPASS\FFmpeg
  3. PATH fallback

- .wav / .mp3 / .m4a を入力音声種別として判定する
- PATH上のFFmpeg / ffprobeはfallback扱い
- B3ではffmpeg / ffprobeを実行しない
```

MS17-B4では、ffprobe検査、入力制限、エラー分類基盤を追加した。

B4で追加済みの想定ファイルは以下。

```text
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b4_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py
```

B4で確定した主な仕様は以下。

```text
- 入力ファイルサイズ上限:
  500 MiB = 500 * 1024 * 1024 bytes

- 音声長上限:
  15分 = 900.0 sec

- ffprobe検査結果として AudioProbeResult を扱う
- 実 ffprobe 必須テストは行わない
- 標準テストは mock / fake runner で行う
```

MS17-B5では、ffmpegによる解析用WAV生成基盤を追加した。

B5で追加済みの想定ファイルは以下。

```text
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_analysis_wav_generation.py
tests/test_ms17_b5_analysis_wav_cache.py
tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

B5で確定した主な仕様は以下。

```text
- 解析用WAV仕様:
  PCM signed 16-bit little-endian / 44100 Hz / mono

- 解析用WAV保存先:
  cache/analysis_wav/

- 既存 .wav 入力も必ず解析用WAVへ変換する

- 解析用WAVファイル名:
  <safe_stem>_<hash8>_analysis.wav

- cache自動削除はB5では行わない
- 変換失敗時の不完全ファイルのみ削除する
- 実 ffmpeg 必須テストは行わない
```

MS17-B6では、B3〜B5で作成した core 層の基盤を、wxPython GUI の音声読み込み導線へ接続する。

B6の中心は、ユーザーが GUI から `.wav` / `.mp3` / `.m4a` を選択し、その入力音声を ffprobe検査・解析用WAV生成へ通したうえで、既存の波形表示・解析処理へ渡せるようにすることである。

---

## 3. 目的

MS17-B6の目的は、既存の「WAV読み込み」導線を「音声読み込み」導線へ拡張し、`.wav` / `.mp3` / `.m4a` を同一フローで扱えるようにすることである。

具体的には、以下を達成する。

1. GUI上の「WAV読み込み」を「音声読み込み」へ変更する。
2. ファイル選択ダイアログで `.wav` / `.mp3` / `.m4a` を選択できるようにする。
3. 既存WAV履歴を「音声ファイル履歴」として扱い、`.wav` / `.mp3` / `.m4a` を保存対象にする。
4. ファイル選択後、次の順序で処理する。

```text
ファイル選択
→ 拡張子判定
→ ffprobe検査
→ 解析用WAV生成
→ 波形表示
→ 解析可能状態へ更新
```

5. 波形表示・解析処理へ渡す音声パスを、常に `AnalysisWavResult.analysis_wav_path` に統一する。
6. 既存 `.wav` 入力も、元ファイルではなく解析用WAV経由で処理する。
7. 入力音声と解析用WAVを内部状態として区別する。
8. 音声変更時に、古い timing plan / Preview / VMD保存可能状態 / 選択状態を無効化する。
9. ffprobe検査失敗、入力制限違反、解析用WAV生成失敗時に、古い解析結果を有効扱いしない。
10. B8での worker / Busy / cancel / late callback破棄に備え、B6では同期処理を基本にしつつ責務境界を明確にする。

---

## 4. In Scope

MS17-B6で行う作業は以下に限定する。

### 4.1 GUI文言の変更

GUI上の音声入力導線の文言を変更する。

```text
旧: WAV読み込み
新: 音声読み込み
```

関連する表示・メニュー・ボタン・ステータス文言も、必要最小限で更新する。

例。

```text
旧: WAVファイルを読み込みました
新: 音声ファイルを読み込みました

旧: WAVを選択してください
新: 音声ファイルを選択してください
```

ただし、GUI全体の大規模な文言再設計は行わない。

### 4.2 ファイル選択ダイアログの拡張

音声読み込みダイアログで、以下の拡張子を選択可能にする。

```text
.wav
.mp3
.m4a
```

推奨フィルタ。

```text
音声ファイル (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|WAVファイル (*.wav)|*.wav|MP3ファイル (*.mp3)|*.mp3|M4Aファイル (*.m4a)|*.m4a|すべてのファイル (*.*)|*.*
```

注意。

```text
- ダイアログで選べても、未対応拡張子は audio_input 側で拒否する
- 拡張子だけで完全な音声妥当性を保証しない
- ffprobe検査で音声streamやdurationを確認する
```

### 4.3 音声読み込みフロー統合

B6では、音声読み込み時の処理順を以下に統一する。

```text
1. ファイル選択
2. 拡張子判定
3. ffprobe検査
4. 解析用WAV生成
5. 解析用WAVを波形表示へ渡す
6. 解析用WAVを解析対象として保持する
7. 解析可能状態へ更新する
```

`.wav` / `.mp3` / `.m4a` のいずれも同じフローで扱う。

既存 `.wav` 入力も、元ファイルを直接波形表示・解析へ渡さず、B5で生成される解析用WAVを渡す。

### 4.4 解析用WAVを正本にする接続

B6以降、波形表示・解析処理へ渡す音声パスは以下に統一する。

```text
AnalysisWavResult.analysis_wav_path
```

これにより、GUI上でユーザーが選択した元音声と、内部処理用の解析用WAVを分離する。

```text
入力音声:
ユーザーが選択した .wav / .mp3 / .m4a

解析用WAV:
cache/analysis_wav/ に生成された PCM signed 16-bit little-endian / 44100 Hz / mono のWAV
```

B6では、MMD用WAVは扱わない。

### 4.5 UiState / Controller 状態の拡張

B6では、必要に応じてGUI状態に以下の概念を追加する。

```text
selected_audio_input
selected_audio_probe
selected_analysis_wav
```

ただし、既存の `selected_wav_path` / `selected_wav_analysis` がある場合、いきなり削除しない。

方針。

```text
- 既存テストや既存コードへの影響を抑える
- 既存 selected_wav_path が必要な箇所は段階的に維持する
- 新しい正本として selected_analysis_wav を導入する
- 命名変更の大規模リファクタはB6では避ける
```

必要なら以下のような過渡状態を許容する。

```text
selected_wav_path:
既存互換のために解析用WAVパスを保持する、または既存処理向けに残す

selected_audio_input:
元音声ファイル情報

selected_analysis_wav:
解析用WAV生成結果
```

ただし、どの値が正本かをコメント・テストで明確にする。

### 4.6 最近使ったファイル履歴の拡張

既存のWAV履歴を「音声ファイル履歴」として拡張する。

方針。

```text
- 既存WAV履歴を破棄しない
- .wav / .mp3 / .m4a を履歴保存対象にする
- 表示名や内部名は、可能な範囲で audio / 音声 へ寄せる
- 既存設定ファイル互換を壊さない
```

互換方針。

```text
- 既存の recent_wav_files がある場合、B6で急に削除しない
- 新しい recent_audio_files へ移行する場合は、旧値を読み込めるようにする
- 大規模な設定移行処理が必要ならB9またはMS18へ送る
```

B6では、最低限として「最近使った音声ファイル」に `.wav` / `.mp3` / `.m4a` が残る状態を目標とする。

### 4.7 エラー時の状態復旧

B6では、以下のいずれかで失敗した場合、古い解析結果を有効扱いしてはならない。

```text
- 拡張子判定失敗
- ffprobe検査失敗
- 入力ファイルサイズ上限超過
- 音声長上限超過
- 音声streamなし
- 解析用WAV生成失敗
- cache保存先作成失敗
```

失敗時に無効化するもの。

```text
- current_timing_plan
- analysis_result_valid
- Preview
- VMD保存可能状態
- selected_source_event_index
- playback_ready
- analysis_ready
```

実際の変数名はrepo状態に従う。

### 4.8 同期処理としての実装

B6では、既存構造に合わせて同期処理を基本にする。

B6で行わないこと。

```text
- worker化
- Busy状態の完全統合
- cancel UI
- late callback破棄
- 300秒確認ダイアログ
```

これらはMS17-B8で扱う。

ただし、B6時点でも最低限として以下を守る。

```text
- 処理中に例外でGUIが落ちない
- 失敗時に状態が復旧する
- 古い解析結果を有効扱いしない
- status文言で失敗が分かる
```

### 4.9 テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b6_audio_file_selection.py
tests/test_ms17_b6_analysis_wav_pipeline.py
tests/test_ms17_b6_recent_audio_files.py
tests/test_ms17_b6_audio_state_invalidation.py
```

必要に応じて、既存のGUIテスト構成に合わせてファイル名を調整する。

---

## 5. Out of Scope

MS17-B6では以下を行わない。

```text
- MMD用WAV生成
- MMD用WAV保存導線
- MMD互換WAV検証
- VMD保存処理との連動MMD用WAV出力
- worker化
- Busy状態の完全統合
- cancel UI
- late callback破棄
- 300秒確認ダイアログ
- ffmpeg / ffprobe のプロセス終了UI統合
- cache/analysis_wav/ の自動削除
- cache容量管理
- 変換キャッシュ再利用
- 音量正規化
- 無音トリム
- 自動フェード
- 自動ノイズ除去
- ピッチ補正
- テンポ補正
- 複数音声ファイルの同時入力
- 複数トラック合成
- 母音イベント本格編集
- Preview shape contract の再設計
- Qt / PySide6 系GUIの再導入
- 旧 src/gui 系の復活
- FFmpeg / ffprobe の自動ダウンロード
- FFmpegバイナリのrepo追加
- build.ps1変更
- MMD_AutoLipTool.spec変更
- .gitignore作成・変更
```

README本文更新は原則B9へ送る。
ただし、B6完了時点でREADMEの記載と実装が大きく矛盾する場合は、B6完了報告に「B9で要更新」として明記する。B6ではREADME本文の大規模更新は行わない。

---

## 6. 前提条件

MS17-B6は、以下を前提とする。

```text
- 作業branchは feature/MS17 である
- MS17-B1 が完了済みである
- MS17-B2 が完了済みである
- MS17-B3 が完了済みである
- MS17-B4 が完了済みである
- MS17-B5 が完了済みである
```

B3から引き継ぐ仕様。

```text
- .wav / .mp3 / .m4a は AudioInputInfo として判定できる
- ffmpeg / ffprobe locator が存在する
- PATH fallback はfallback扱い
```

B4から引き継ぐ仕様。

```text
- ffprobe検査ができる
- 入力ファイルサイズ上限は 500 MiB
- 音声長上限は 15分
- AudioProbeResult が存在する
- 音声入力エラー分類が存在する
```

B5から引き継ぐ仕様。

```text
- AnalysisWavResult が存在する
- 解析用WAV仕様は PCM signed 16-bit little-endian / 44100 Hz / mono
- 解析用WAV保存先は cache/analysis_wav/
- 既存 .wav 入力も必ず解析用WAVへ変換する
- 変換失敗時に不完全ファイルを削除する
```

B6で固定する仕様。

```text
- GUI文言は「WAV読み込み」から「音声読み込み」へ変更する
- 最近使ったファイル履歴は音声ファイル履歴として wav / mp3 / m4a を扱う
- 波形表示・解析処理へ渡す音声パスは常に AnalysisWavResult.analysis_wav_path にする
- 処理順は ファイル選択 → 拡張子判定 → ffprobe検査 → 解析用WAV生成 → 波形表示 → 解析可能状態へ更新
- B6では同期処理を基本にし、worker化はB8へ送る
```

---

## 7. 対象ファイル

MS17-B6で変更する候補。

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
[NEW] src/gui_wx/recent_files.py
```

MS17-B6で参照・接続する core ファイル。

```text
src/core/audio_input.py
src/core/ffmpeg_locator.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_errors.py
```

MS17-B6で追加するテスト候補。

```text
tests/test_ms17_b6_audio_file_selection.py
tests/test_ms17_b6_analysis_wav_pipeline.py
tests/test_ms17_b6_recent_audio_files.py
tests/test_ms17_b6_audio_state_invalidation.py
```

必要に応じて変更する docs。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

確認するが原則変更しないファイル。

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
.gitignore
```

B6で `src/gui_wx/recent_files.py` が存在しない場合は、repo実装に合わせて以下のいずれかを確認する。

```text
src/gui_wx/app_controller.py
src/gui_wx/main_frame.py
src/gui_wx/settings.py
src/gui_wx/ui_state.py
```

存在しないファイルを無理に前提化しない。

---

## 8. 実装方針

### 8.1 全体方針

MS17-B6では、B3〜B5で追加した core 層を GUI の音声読み込み導線に接続する。

基本方針。

```text
- 既存WAV読み込み導線を音声読み込み導線へ拡張する
- .wav / .mp3 / .m4a を同一フローで扱う
- 解析用WAVを波形表示・解析の正本にする
- 既存の無効化規則を維持する
- エラー時に古い解析結果を残さない
- B8範囲のworker化・Busy・cancelは行わない
```

### 8.2 音声読み込みフロー

B6の標準フローは以下。

```text
1. ユーザーが「音声読み込み」を押す
2. ファイルダイアログで .wav / .mp3 / .m4a を選択する
3. AudioInputInfo を作成する
4. ffmpeg / ffprobe の locator を実行する
5. ffprobe path を使って probe_audio_file を実行する
6. ffmpeg path を使って generate_analysis_wav を実行する
7. AnalysisWavResult.analysis_wav_path を波形表示へ渡す
8. AnalysisWavResult.analysis_wav_path を解析対象として保持する
9. recent audio files に元音声パスを追加する
10. UI状態を playback_ready / analysis_ready 相当へ更新する
```

注意。

```text
- 履歴に保存するのは、原則としてユーザーが選択した元音声パス
- 波形表示・解析に使うのは解析用WAVパス
- ステータス表示では元音声名と解析用WAV生成成功が分かるようにする
```

### 8.3 MainFrame の変更方針

`src/gui_wx/main_frame.py` では、以下を変更する候補とする。

```text
- ボタン / メニュー / ラベルの「WAV読み込み」を「音声読み込み」へ変更
- ファイルダイアログのフィルタを wav / mp3 / m4a 対応へ変更
- controllerへ渡すメソッド名またはイベント名を音声読み込み向けに整理
- 既存WAV読み込みAPIとの互換を維持
```

メソッド名の扱い。

```text
- 既存の on_open_wav / request_open_wav などがある場合、即削除しない
- 新しく on_open_audio / request_open_audio を追加し、旧メソッドから委譲してもよい
- 大規模リネームはB6では避ける
```

### 8.4 AppController の変更方針

`src/gui_wx/app_controller.py` では、音声読み込みの統合処理を担当する。

想定する高レベル処理。

```python
def request_open_audio_file(path: str | Path) -> None:
    ...
```

または既存構造に合わせて、以下を拡張する。

```python
def request_open_wav_file(path: str | Path) -> None:
    ...
```

推奨は、新メソッドを追加し、旧メソッドを互換のために残す形である。

処理内容。

```text
1. 入力直後に既存解析結果を無効化する
2. AudioInputInfo を作成する
3. locate_ffmpeg_tools を実行する
4. ffprobe path がない場合はエラー
5. probe_audio_file を実行する
6. ffmpeg path がない場合はエラー
7. generate_analysis_wav を実行する
8. analysis_wav_path を load_waveform_preview / analyze_wav_file へ渡す
9. selected_audio_input / selected_analysis_wav / selected_wav_analysis 等を更新する
10. recent audio files を更新する
11. UI状態を更新する
```

失敗時。

```text
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア
- playback_ready / analysis_ready を False 相当にする
- ステータスへユーザー向けmessageを表示する
```

### 8.5 UiState の変更方針

`src/gui_wx/ui_state.py` では、必要に応じて以下を追加する。

```text
selected_audio_input
selected_audio_probe
selected_analysis_wav
recent_audio_files
last_audio_dialog_dir
```

ただし、既存の `selected_wav_path` / `recent_wav_files` がある場合は、急に削除しない。

移行方針。

```text
- B6では後方互換を優先する
- selected_wav_path を既存コード向けに残す (内部で selected_analysis_wav.analysis_wav_path を指すように委譲するなどの構成を検討)
- selected_analysis_wav を新しい内部正本として扱う
- recent_wav_files は recent_audio_files へ段階移行する
```

実装上の安全策。

```text
- 既存テストが参照するプロパティを削除しない
- 名前変更よりも追加を優先する
- B9またはMS18で整理リファクタ候補として記録する
```

### 8.6 最近使ったファイル履歴

履歴に保存する対象は、ユーザーが選択した元音声ファイルとする。

```text
保存対象:
- input.wav
- input.mp3
- input.m4a

保存しない対象:
- cache/analysis_wav/..._analysis.wav
```

理由。

```text
- ユーザーが再度開きたいのは元音声ファイルである
- 解析用WAVは内部生成物である
- cache/analysis_wav/ をユーザー向け履歴に出すと混乱する
```

既存WAV履歴からの移行。

```text
- 既存の recent_wav_files がある場合、それを recent_audio_files として読み替えてよい
- 設定ファイルのキー名を変える場合は後方互換を用意する
- 設定互換が重い場合、B6では内部名を維持し、表示だけ「最近使った音声」にする
```

推奨。

```text
- B6では保存対象拡張子を wav / mp3 / m4a に広げる
- 内部キー名の大規模変更は避ける
- UI表示上は「最近使った音声ファイル」に寄せる
```

### 8.7 波形表示・解析処理への接続

B6では、以下を常に解析用WAVパスに統一する。

```text
AnalysisWavResult.analysis_wav_path
```

接続候補。

```text
load_waveform_preview(analysis_wav_path)
analyze_wav_file(analysis_wav_path)
```

既存関数名に `wav` が含まれていても、B6時点では関数名変更を必須にしない。

理由。

```text
- 解析用WAVは実際にWAVである
- 関数名変更による大規模差分を避ける
- B6では入力導線統合を優先する
```

ただし、コメントやdocsでは以下を明確にする。

```text
- 元音声ファイルではなく解析用WAVを渡している
- 解析用WAVが波形表示・解析の正本である
```

### 8.8 エラー表示

B6では、B4/B5の `AudioErrorInfo` / `AudioProbeError` 相当を受け取り、GUIのstatusやmessageに反映する。

方針。

```text
- ユーザー向けmessageを表示する
- detailやstderr全文をGUIへ直接表示しない
- 技術詳細はログまたは完了報告で扱う
```

B6でのエラー表示は最小限でよい。

B8で、Warning / Info / Busy / 長時間処理と合わせて整理する。

### 8.9 同期処理の範囲

B6では同期処理を基本とする。

理由。

```text
- 既存WAV読み込み構造に合わせるため
- B6の責務を入力導線統合に絞るため
- worker化、Busy、cancel、late callback破棄はB8でまとめて扱うため
```

ただし、実装時には以下を避ける。

```text
- 例外でGUIが落ちる
- 失敗後に古いPreviewが残る
- 失敗後にVMD保存可能状態が残る
- 失敗後に古い選択イベントが残る
```

---

## 9. 詳細ステップ

### Step 1: branch / 作業ツリー確認

最初に以下を実行する。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text
- 現在branchが feature/MS17 であるか
- 作業ツリーがcleanか
- staged差分がないか
- MS17-B5完了commitまたは記録があるか
- B6開始前に意図しない差分がないか
```

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。

### Step 2: B3〜B5成果確認

以下を確認する。

```text
src/core/audio_input.py
src/core/ffmpeg_locator.py
src/core/audio_errors.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_cache.py
docs/repo_milestone.md
docs/Version_Control.md
```

確認観点。

```text
- AudioInputInfo が存在するか
- locate_ffmpeg_tools が存在するか
- probe_audio_file が存在するか
- generate_analysis_wav が存在するか
- AnalysisWavResult が存在するか
- 解析用WAV保存先が cache/analysis_wav/ であるか
- B6へ進む記録があるか
```

### Step 3: 既存GUI入力導線確認

以下を確認する。

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/recent_files.py
```

`recent_files.py` が存在しない場合は、履歴処理がどこにあるか確認する。

確認観点。

```text
- WAV読み込みボタン / メニュー / イベント
- ファイルダイアログのfilter
- selected_wav_path の更新箇所
- selected_wav_analysis の更新箇所
- load_waveform_preview の呼び出し箇所
- analyze_wav_file の呼び出し箇所
- invalidate_analysis の呼び出し箇所
- Preview clear の呼び出し箇所
- VMD保存可能状態の更新箇所
- 最近使ったWAVファイル履歴
- **app_controller.py のインポートパス不整合 (from core -> from src.core)**
```

### Step 4: GUI文言変更

GUI上の「WAV読み込み」を「音声読み込み」へ変更する。

対象候補。

```text
- ボタンラベル
- メニュー項目
- ツールチップ
- ステータス文言
- ファイルダイアログタイトル
```

変更方針。

```text
- 既存レイアウトを大きく崩さない
- 長すぎる文言は避ける
- 詳細な対応形式はファイルダイアログfilterやstatusで補足する
```

### Step 5: ファイルダイアログ拡張

ファイル選択ダイアログを `.wav` / `.mp3` / `.m4a` 対応にする。

推奨filter。

```text
音声ファイル (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|WAVファイル (*.wav)|*.wav|MP3ファイル (*.mp3)|*.mp3|M4Aファイル (*.m4a)|*.m4a|すべてのファイル (*.*)|*.*
```

last dialog dir の扱い。

```text
- 既存 last_wav_dialog_dir がある場合、互換のため残す
- 新規 last_audio_dialog_dir を追加する場合は、旧値を初期値として使えるようにする
```

### Step 6: AppControllerに音声読み込み統合処理を追加

`app_controller.py` に、音声読み込み統合処理を追加する。

推奨メソッド名。

```python
request_open_audio_file(path)
```

または、既存構造に合わせる。

処理順。

```text
1. 既存解析結果を無効化する
2. AudioInputInfo を作成する
3. locate_ffmpeg_tools を実行する
4. ffprobe path を確認する
5. probe_audio_file を実行する
6. ffmpeg path を確認する
7. generate_analysis_wav を実行する
8. analysis_wav_path を load_waveform_preview へ渡す
9. analysis_wav_path を analyze_wav_file へ渡す
10. 状態を更新する
11. recent audio files を更新する
12. UIを再描画 / action state更新する

**注意: app_controller.py の `from core import ...` を `from src.core import ...` へ修正する。**
```

注意。

```text
- 元音声パスと解析用WAVパスを混同しない
- recent filesには元音声パスを保存する
- 波形表示・解析には解析用WAVパスを渡す
```

### Step 7: UiStateを必要最小限で拡張

必要に応じて `ui_state.py` を拡張する。

追加候補。

```text
selected_audio_input
selected_audio_probe
selected_analysis_wav
recent_audio_files
last_audio_dialog_dir
```

注意。

```text
- 既存プロパティを削除しない
- 既存テストを壊さない
- 大規模な命名整理はB9またはMS18へ送る
```

### Step 8: 最近使った音声ファイル履歴の拡張 (recent_files.py の新設)

既存の `MainFrame` 等に分散している履歴処理を `src/gui_wx/recent_files.py` を新設して集約・拡張する。

対象拡張子。

```text
.wav
.mp3
.m4a
```

保存するパス。

```text
ユーザーが選択した元音声ファイルのパス
```

保存しないパス。

```text
cache/analysis_wav/..._analysis.wav
```

テストで確認すること。

```text
- wav が履歴に入る
- mp3 が履歴に入る
- m4a が履歴に入る
- 解析用WAVパスは履歴に入らない
- 既存WAV履歴が読める
```

### Step 9: 解析用WAVを波形表示・解析へ接続

B6では、波形表示と解析処理へ渡すパスを `AnalysisWavResult.analysis_wav_path` に統一する。

対象候補。

```text
load_waveform_preview(analysis_wav_path)
analyze_wav_file(analysis_wav_path)
```

成功時に保持する情報。

```text
- selected_audio_input:
  元音声ファイル情報

- selected_audio_probe:
  ffprobe検査結果

- selected_analysis_wav:
  解析用WAV生成結果

- selected_wav_analysis:
  解析用WAVを analyze_wav_file した結果
```

実際の変数名はrepo状態に従う。

### Step 10: エラー時無効化処理

以下の失敗時に、古い状態が残らないようにする。

```text
- AudioInputInfo作成失敗
- locator失敗
- ffprobe pathなし
- probe_audio_file失敗
- ffmpeg pathなし
- generate_analysis_wav失敗
- load_waveform_preview失敗
- analyze_wav_file失敗
```

失敗時に行うこと。

```text
- current_timing_plan 無効化
- analysis_result_valid False
- Preview clear
- VMD保存不可
- selected_source_event_index clear
- playback_ready False
- analysis_ready False
- 必要に応じて selected_analysis_wav clear
```

### Step 11: テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b6_audio_file_selection.py
tests/test_ms17_b6_analysis_wav_pipeline.py
tests/test_ms17_b6_recent_audio_files.py
tests/test_ms17_b6_audio_state_invalidation.py
```

テスト内容。

```text
- ファイルダイアログfilterが wav / mp3 / m4a を含む
- GUI文言が音声読み込みになっている
- wav / mp3 / m4a が同一フローに乗る
- AnalysisWavResult.analysis_wav_path が波形表示へ渡る
- AnalysisWavResult.analysis_wav_path が解析処理へ渡る
- recent filesには元音声パスが保存される
- cache/analysis_wav のパスはrecent filesに入らない
- 失敗時に古い解析結果が無効化される
- 失敗時にVMD保存可能状態にならない
- 失敗時に選択イベントが残らない
```

### Step 12: B3〜B5回帰テスト

必要に応じて、B3〜B5の限定テストを再実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

### Step 13: B6限定テスト実行

以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_file_selection.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_analysis_wav_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_recent_audio_files.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_state_invalidation.py
```

既存GUI関連の回帰確認として、必要に応じて以下を限定実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

全体pytestは、既知のハング可能性がある場合は実行しない。

### Step 14: docs更新

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録内容。

```text
- MS17-B6を実施したこと
- GUI文言を「音声読み込み」へ変更したこと
- ファイル選択で wav / mp3 / m4a を扱うようにしたこと
- 処理順を 拡張子判定 → ffprobe検査 → 解析用WAV生成 → 波形表示・解析 としたこと
- 波形表示・解析へ AnalysisWavResult.analysis_wav_path を渡すようにしたこと
- 最近使ったファイル履歴を音声ファイル向けに拡張したこと
- B6では同期処理を基本とし、Busy / worker / cancel / late callback破棄はB8へ送ったこと
- MMD用WAV出力はB7へ送ったこと
```

READMEはB9でMS17全体closeout時に更新する方針とする。
ただし、B6完了報告にREADME更新必要性を明記する。

### Step 15: 完了前diff確認

以下を実行する。

```powershell
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
git diff -- .gitignore
```

想定される追加・変更ファイル。

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/recent_files.py
tests/test_ms17_b6_audio_file_selection.py
tests/test_ms17_b6_analysis_wav_pipeline.py
tests/test_ms17_b6_recent_audio_files.py
tests/test_ms17_b6_audio_state_invalidation.py
docs/repo_milestone.md
docs/Version_Control.md
```

ただし、実際の対象ファイル名はrepo構成に従う。

以下に差分がないことを確認する。

```text
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
.gitignore
```

READMEに差分が出ている場合は、B6で必要最小限の更新か、B9へ送るべき更新かを報告で明確にする。

---

## 10. 状態遷移 / データ契約

### 10.1 B6で接続するデータ契約

B6では、以下を接続する。

```text
AudioInputInfo
→ AudioProbeResult
→ AnalysisWavResult
→ load_waveform_preview
→ analyze_wav_file
```

各データの役割。

```text
AudioInputInfo:
ユーザーが選択した元音声ファイル

AudioProbeResult:
ffprobeで検査した入力音声情報

AnalysisWavResult:
ffmpegで生成した解析用WAV情報

selected_wav_analysis:
解析用WAVを既存WAV解析処理へ渡した結果
```

### 10.2 正本の扱い

B6以降の正本は以下。

```text
入力音声の正本:
AudioInputInfo.source_path

波形表示・解析・timing plan生成の音声正本:
AnalysisWavResult.analysis_wav_path
```

以下を混同しない。

```text
- 入力音声
- 解析用WAV
- MMD用WAV
- VMD出力
```

MMD用WAVはB7で扱う。

### 10.3 B6で変更するGUI状態

B6で追加・更新する候補。

```text
selected_audio_input
selected_audio_probe
selected_analysis_wav
recent_audio_files
last_audio_dialog_dir
```

既存互換のために残す候補。

```text
selected_wav_path
selected_wav_analysis
recent_wav_files
last_wav_dialog_dir
```

方針。

```text
- 削除より追加・委譲を優先する
- B6では既存WAV系命名の全面リネームをしない
- 正本がどれかをテストとコメントで明確にする
```

### 10.4 無効化規則

B6でも以下を維持する。

```text
TEXT変更時:
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア

音声変更時:
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア
- selected_analysis_wav を更新またはクリア
- playback_ready / analysis_ready を更新

パラメータ変更時:
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア
```

エラー時は、読み込み開始前の古い解析結果を再利用してはならない。

### 10.5 B6でまだ追加しない契約

以下はB6では追加しない。

```text
mmd_wav_output_path
mmd_wav_validation_result
conversion_worker_id
cancel_token
late_callback_generation_id
long_processing_confirmation_state
```

これらはB7またはB8で扱う。

---

## 11. テスト方針

### 11.1 B6で実行する標準テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_file_selection.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_analysis_wav_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_recent_audio_files.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_state_invalidation.py
```

### 11.2 B3〜B5回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

### 11.3 既存GUI回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

### 11.4 実 ffmpeg / ffprobe テスト方針

B6では、実 `ffmpeg.exe` / `ffprobe.exe` を必須テストにしない。

理由。

```text
- B6の標準テストを環境依存にしないため
- B3〜B5と同様に mock / fake runner 中心で検証するため
- 実体確認はB9統合確認または手動確認へ送るため
```

必要に応じて任意手動確認として、ローカル環境で実ファイルを読み込む確認を行ってよい。
ただし、B6の自動テスト完了条件には含めない。

### 11.5 全体pytest

全体pytestは、既知のハング可能性がある場合は実行しない。

実行しない場合は、完了報告に理由を書く。

---

## 12. 受け入れ条件

MS17-B6は、以下を満たしたら完了とする。

### 12.1 実装条件

* GUI上の「WAV読み込み」が「音声読み込み」へ変更されている。
* ファイルダイアログで `.wav` / `.mp3` / `.m4a` を選択できる。
* `.wav` / `.mp3` / `.m4a` が同一の音声読み込みフローへ入る。
* 音声読み込み処理順が以下になっている。

```text
ファイル選択
→ 拡張子判定
→ ffprobe検査
→ 解析用WAV生成
→ 波形表示
→ 解析可能状態へ更新
```

* 波形表示へ渡す音声パスが `AnalysisWavResult.analysis_wav_path` になっている。
* 解析処理へ渡す音声パスが `AnalysisWavResult.analysis_wav_path` になっている。
* 既存 `.wav` 入力も解析用WAV経由で処理される。
* 最近使ったファイル履歴が `.wav` / `.mp3` / `.m4a` を扱う。
* 最近使ったファイル履歴に保存されるのは元音声パスであり、解析用WAVパスではない。
* 音声変更時に古い timing plan / Preview / VMD保存可能状態 / 選択状態が無効化される。
* 失敗時に古い解析結果が有効扱いされない。
* B7 / B8 の範囲へ踏み込んでいない。

### 12.2 禁止事項遵守

以下が守られている。

```text
- MMD用WAV出力をしていない
- VMD保存処理との連動MMD用WAV出力をしていない
- worker化をしていない
- Busy状態の完全統合をしていない
- cancel UIを実装していない
- late callback破棄を実装していない
- 300秒確認ダイアログを実装していない
- cache自動削除を実装していない
- 音量正規化をしていない
- 無音トリムをしていない
- 自動フェードをしていない
- 自動ノイズ除去をしていない
- build.ps1を変更していない
- MMD_AutoLipTool.specを変更していない
- .gitignoreを変更していない
- Qt / PySide6を再導入していない
```

### 12.3 テスト条件

以下が成功している。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_file_selection.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_analysis_wav_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_recent_audio_files.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_state_invalidation.py
```

必要に応じて実行したB3〜B5回帰テスト、既存GUI回帰テストの結果が報告されている。

全体pytestを実行しなかった場合は、その理由が報告されている。

### 12.4 docs条件

以下が必要最小限で更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録上、B6の範囲が以下として明確である。

```text
- wav / mp3 / m4a 入力導線統合
- GUI文言を「音声読み込み」へ変更
- 解析用WAVを波形表示・解析の正本として接続
- 最近使った音声ファイル履歴の拡張
- 同期処理を基本とし、worker化はB8へ送る
- MMD用WAV出力はB7へ送る
```

---

## 13. リスクと対策

### Risk 1: 入力音声と解析用WAVを混同する

対策。

```text
- recent filesには元音声パスを保存する
- 波形表示・解析には analysis_wav_path を渡す
- selected_audio_input と selected_analysis_wav を分ける
- コメントとテストで正本を固定する
```

### Risk 2: 既存WAV入力経路を壊す

対策。

```text
- 既存 selected_wav_path / selected_wav_analysis を急に削除しない
- 関数名に wav が残っていても、B6では互換を優先する
- 既存GUI回帰テストを必要に応じて実行する
```

### Risk 3: mp3 / m4a を元ファイルのまま波形表示へ渡してしまう

対策。

```text
- 波形表示・解析へ渡すパスを AnalysisWavResult.analysis_wav_path に統一する
- テストで load_waveform_preview / analyze_wav_file に渡るパスを確認する
```

### Risk 4: エラー時に古いPreviewやVMD保存可能状態が残る

対策。

```text
- 読み込み開始時点で既存解析結果を無効化する
- 失敗時に再度無効化を保証する
- selected_source_event_index をクリアする
- VMD保存可能状態がFalseになることをテストする
```

### Risk 5: B6でworker化まで進んでしまう

対策。

```text
- B6は同期処理を基本とする
- Busy / cancel / late callback破棄はB8へ送る
- B6完了報告にB8引き継ぎとして明記する
```

### Risk 6: 最近使ったファイル履歴に解析用WAVが混入する

対策。

```text
- 履歴保存対象は元音声パスに限定する
- cache/analysis_wav/ 配下のパスが履歴に入らないことをテストする
```

### Risk 7: READMEとGUIの記述が一時的にずれる

対策。

```text
- B6ではREADME大規模更新を行わない
- B9 closeoutでREADMEをMS17完了状態へ更新する
- B6完了報告にREADME更新必要性を記録する
```

### Risk 8: 同期処理で長時間フリーズが発生する

対策。

```text
- B6では既存構造に合わせて同期処理とする
- 300秒確認、Busy、worker化はB8で統合する
- B6完了報告にB8引き継ぎとして明記する
```

---

## 14. Antigravity 実装時の注意

以下のプロンプトを Antigravity に渡して実施する。

```text
今回は MS17-B6 です。

目的:
wav / mp3 / m4a 入力導線をGUIへ統合してください。

重要:
- 対象branchは feature/MS17 です。
- MS17-B3 / B4 / B5 の成果を前提にしてください。
- GUI上の「WAV読み込み」を「音声読み込み」へ変更してください。
- ファイル選択dialogで .wav / .mp3 / .m4a を選べるようにしてください。
- 読み込み処理順は以下にしてください。
  ファイル選択
  → 拡張子判定
  → ffprobe検査
  → 解析用WAV生成
  → 波形表示
  → 解析可能状態へ更新
- 波形表示・解析処理へ渡す音声パスは常に AnalysisWavResult.analysis_wav_path にしてください。
- 最近使ったファイル履歴は、既存WAV履歴を音声ファイル履歴として拡張し、wav / mp3 / m4a を保存対象にしてください。
- 履歴に保存するのは元音声ファイルのパスであり、cache/analysis_wav/ の解析用WAVパスではありません。
- B6では既存構造に合わせて同期処理を基本にしてください。
- worker化、Busy状態の完全統合、cancel、late callback破棄はB8へ送ってください。
- MMD用WAV出力はB7へ送ってください。
- 300秒確認ダイアログは実装しないでください。
- cache自動削除は実装しないでください。
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わないでください。
- build.ps1 / MMD_AutoLipTool.spec は変更しないでください。
- .gitignore は作成・変更しないでください。
- Qt / PySide6 は再導入しないでください。

最初に以下を実行してください。

git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only

現在branchが feature/MS17 ではない場合は、checkoutせず、その時点で報告してください。

確認対象:

src/core/audio_input.py
src/core/ffmpeg_locator.py
src/core/audio_errors.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_cache.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/recent_files.py
docs/repo_milestone.md
docs/Version_Control.md

src/gui_wx/recent_files.py が存在しないことを確認済みです。B6で新設してください。
また、app_controller.py の `from core import ...` を `from src.core import ...` へ修正してください。

実装候補:

src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/recent_files.py
tests/test_ms17_b6_audio_file_selection.py
tests/test_ms17_b6_analysis_wav_pipeline.py
tests/test_ms17_b6_recent_audio_files.py
tests/test_ms17_b6_audio_state_invalidation.py

実装内容:

1. GUI文言を変更してください。
   - 「WAV読み込み」を「音声読み込み」へ変更してください。
   - ファイルダイアログタイトルやstatus文言も必要最小限で更新してください。
   - GUI全体の大規模再設計は行わないでください。

2. ファイル選択dialogを拡張してください。
   - .wav / .mp3 / .m4a を選択可能にしてください。
   - 推奨filter:
     音声ファイル (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|WAVファイル (*.wav)|*.wav|MP3ファイル (*.mp3)|*.mp3|M4Aファイル (*.m4a)|*.m4a|すべてのファイル (*.*)|*.*
   - 未対応拡張子は core/audio_input.py 側で拒否してください。

3. AppControllerに音声読み込み統合処理を追加してください。
   - 既存構造に合わせて request_open_audio_file などを追加してください。
   - 既存 request_open_wav_file がある場合は、互換のため残し、新処理へ委譲してもよいです。
   - 処理順は以下にしてください。
     1. 既存解析結果を無効化
     2. AudioInputInfo作成
     3. locate_ffmpeg_tools
     4. probe_audio_file
     5. generate_analysis_wav
     6. load_waveform_preview(analysis_wav_path)
     7. analyze_wav_file(analysis_wav_path)
     8. 状態更新
     9. recent audio files更新

4. 波形表示・解析へ渡すパスを AnalysisWavResult.analysis_wav_path に統一してください。
   - 元音声ファイルを直接 load_waveform_preview / analyze_wav_file へ渡さないでください。
   - .wav 入力でも解析用WAVを使ってください。

5. UiStateを必要最小限で拡張してください。
   - selected_audio_input
   - selected_audio_probe
   - selected_analysis_wav
   - recent_audio_files
   - last_audio_dialog_dir
   などが必要であれば追加してください。
   - 既存 selected_wav_path / selected_wav_analysis / recent_wav_files を急に削除しないでください。

6. 最近使ったファイル履歴を拡張してください。
   - wav / mp3 / m4a を履歴対象にしてください。
   - 履歴に保存するのは元音声ファイルのパスにしてください。
   - cache/analysis_wav/ の解析用WAVパスは履歴に入れないでください。
   - 既存WAV履歴との互換を壊さないでください。

7. エラー時の状態無効化を保証してください。
   - 拡張子判定失敗
   - ffprobe検査失敗
   - ffmpeg pathなし
   - 解析用WAV生成失敗
   - 波形表示失敗
   - 解析失敗
   のいずれでも、古い timing plan / Preview / VMD保存可能状態 / 選択状態が残らないようにしてください。

8. テストを追加してください。
   - tests/test_ms17_b6_audio_file_selection.py
   - tests/test_ms17_b6_analysis_wav_pipeline.py
   - tests/test_ms17_b6_recent_audio_files.py
   - tests/test_ms17_b6_audio_state_invalidation.py
   実際のrepoのテスト構成に合わせてファイル名は調整してよいです。

実行するテスト:

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_file_selection.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_analysis_wav_pipeline.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_recent_audio_files.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_state_invalidation.py

必要に応じてB3〜B5回帰テストも実行してください。

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py

必要に応じて既存GUI回帰テストも限定実行してください。

.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py

全体pytestは、ハング可能性がある場合は実行しないでください。

実装後、必要最小限で以下を更新してください。

docs/repo_milestone.md
docs/Version_Control.md

記録内容:
- MS17-B6を実施したこと
- GUI文言を「音声読み込み」へ変更したこと
- ファイル選択で wav / mp3 / m4a を扱うようにしたこと
- 処理順を 拡張子判定 → ffprobe検査 → 解析用WAV生成 → 波形表示・解析 としたこと
- 波形表示・解析へ AnalysisWavResult.analysis_wav_path を渡すようにしたこと
- 最近使ったファイル履歴を音声ファイル向けに拡張したこと
- B6では同期処理を基本とし、Busy / worker / cancel / late callback破棄はB8へ送ったこと
- MMD用WAV出力はB7へ送ったこと
- README更新はB9 closeoutで行う必要があること

完了前に以下を確認してください。

git diff --stat
git diff --name-only
git diff -- .gitignore

.gitignoreに差分が出ている場合は、ユーザー側管理対象なので元に戻して報告してください。

完了報告では、以下を必ず分けてください。

1. 確認したbranch / commit
2. 作業前の状態
3. 変更したファイル
4. 追加したファイル
5. GUI文言変更
6. ファイル選択dialog拡張
7. 音声読み込み統合フロー
8. 解析用WAV接続
9. 最近使った音声ファイル履歴
10. エラー時無効化
11. 実行したテスト
12. 実行していないテスト
13. 変更していないファイル
14. .gitignoreを変更していないこと
15. 禁止事項の遵守
16. B7への引き継ぎ
17. B8への引き継ぎ
18. 未解決・要確認事項
```

---

## 15. 完了報告テンプレート

Antigravityは、完了時に以下の形式で報告する。

```text
MS17-B6 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 変更したファイル
- src/gui_wx/main_frame.py:
- src/gui_wx/app_controller.py:
- src/gui_wx/ui_state.py:
- src/gui_wx/recent_files.py:
- docs/repo_milestone.md:
- docs/Version_Control.md:

4. 追加したファイル
- tests/test_ms17_b6_audio_file_selection.py:
- tests/test_ms17_b6_analysis_wav_pipeline.py:
- tests/test_ms17_b6_recent_audio_files.py:
- tests/test_ms17_b6_audio_state_invalidation.py:

5. GUI文言変更
- WAV読み込み → 音声読み込み:
- ファイルダイアログタイトル:
- status文言:
- その他:

6. ファイル選択dialog拡張
- 対応拡張子:
- filter:
- 未対応拡張子拒否:
- last dialog dir:

7. 音声読み込み統合フロー
- 拡張子判定:
- ffprobe検査:
- 解析用WAV生成:
- 波形表示:
- 解析可能状態:
- 同期処理:

8. 解析用WAV接続
- AnalysisWavResult.analysis_wav_path:
- load_waveform_preview:
- analyze_wav_file:
- 元音声パスとの分離:
- 既存wav入力:

9. 最近使った音声ファイル履歴
- wav:
- mp3:
- m4a:
- 元音声パス保存:
- 解析用WAVパス除外:
- 既存WAV履歴互換:

10. エラー時無効化
- 拡張子判定失敗:
- ffprobe検査失敗:
- 解析用WAV生成失敗:
- 波形表示失敗:
- 解析失敗:
- timing plan:
- Preview:
- VMD保存可能状態:
- 選択イベント:

11. 実行したテスト
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_file_selection.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_analysis_wav_pipeline.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_recent_audio_files.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b6_audio_state_invalidation.py:
- B3〜B5回帰テスト:
- 既存GUI回帰テスト:

12. 実行していないテスト
- 実ffmpeg / ffprobeテスト:
- 全体pytest:
- 理由:

13. 変更していないファイル
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:

14. 禁止事項の確認
- MMD用WAV出力:
- VMD保存処理との連動MMD用WAV出力:
- worker化:
- Busy完全統合:
- cancel UI:
- late callback破棄:
- 300秒確認ダイアログ:
- cache自動削除:
- 音量正規化:
- 無音トリム:
- 自動フェード:
- 自動ノイズ除去:
- Qt / PySide6再導入:

15. B7への引き継ぎ
- MMD用WAV出力:
- VMD保存導線:
- MMD互換WAV検証:
- 解析用WAVとの分離:

16. B8への引き継ぎ
- 同期処理:
- Busy状態:
- worker化:
- cancel:
- late callback破棄:
- 300秒確認:

17. 未解決・要確認事項
- README更新:
- recent files内部名整理:
- selected_wav_path命名整理:
- その他:
```

---

## 16. MS17-B7への引き継ぎ条件

MS17-B7へ進む場合、B6から以下を引き継ぐ。

```text
- GUIから wav / mp3 / m4a を選択できること
- 入力音声は AudioInputInfo として保持されること
- ffprobe検査が音声読み込みフローに接続されていること
- 解析用WAV生成が音声読み込みフローに接続されていること
- 波形表示・解析へ AnalysisWavResult.analysis_wav_path が渡されていること
- 最近使った音声ファイル履歴には元音声パスが保存されること
- 解析用WAVパスはrecent filesに入らないこと
```

MS17-B7では、以下へ進む。

```text
MS17-B7: MMD用WAV出力基盤
```

B7で扱う候補。

```text
- MMD用WAV出力仕様の確定
- MMD互換WAV検証
- VMD保存時の同時出力導線
- 出力ファイル名規則
- 上書き確認
- 不完全ファイル削除
- 保存成功 / 失敗メッセージ
- VMD出力との整合
```

B7で守ること。

```text
- MMD用WAVと解析用WAVを混同しない
- 解析用WAVは内部正本
- MMD用WAVはMMDに読み込ませるための出力物
- VMD出力は引き続きリップモーフキーフレームのみ
```

---

## 17. MS17-B8への引き継ぎ条件

MS17-B8へ進む場合、B6から以下を引き継ぐ。

```text
- B6では同期処理を基本にしていること
- 音声読み込み・ffprobe検査・解析用WAV生成は長時間化する可能性があること
- B6ではworker化していないこと
- B6ではBusy状態の完全統合をしていないこと
- B6ではcancel UIを実装していないこと
- B6ではlate callback破棄を実装していないこと
- B6では300秒確認ダイアログを実装していないこと
```

MS17-B8では、以下へ進む。

```text
MS17-B8: GUI状態・Busy・長時間処理確認・worker結果破棄統合
```

B8で扱う候補。

```text
- 変換中Busy状態
- ffprobe中Busy状態
- 解析用WAV生成中Busy状態
- 300秒確認ダイアログ
- cancel要求
- ffmpeg / ffprobe terminate / kill
- Whisperなど即時停止できない処理の late callback 破棄
- 古いworker結果を現在結果として扱わない
- TEXT / 音声 / パラメータ変更時の無効化
```
