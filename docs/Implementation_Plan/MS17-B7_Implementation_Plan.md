# MS17-B7 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B7
- Block name: MMD用WAV出力基盤
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B7_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Codex
- Coding AI: Codex
- Shell: Windows PowerShell
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作業種別: 実装
- 実装変更: あり
- GUI変更: あり
- GUI大規模再設計: 禁止
- 出力対象: MMD用WAV
- MMD用WAV仕様:
  - container: WAV
  - codec: PCM signed 16-bit little-endian
  - sample rate: 44100 Hz
  - channels: stereo
- 出力導線:
  - 専用の「MMD用WAV出力」ボタン
- VMD保存処理との連動出力:
  - B7では行わない
- ボタン有効化条件:
  - 解析用WAV生成済み
- 保存先:
  - ユーザーが保存ダイアログで指定する
- 初期ファイル名:
  - 元音声stem + `_mmd.wav`
- 同名ファイル存在時:
  - 上書き確認ダイアログを出し、ユーザーが承認した場合のみ上書きする
- MMD用WAVの入力元:
  - ユーザーが選択した元音声ファイル
- B7でのffprobe再検査:
  - 行わない
  - B6で保持済みの `AudioProbeResult` を利用する
- worker / Busy / cancel / late callback統合:
  - MS17-B8へ送る
- 300秒確認ダイアログ:
  - MS17-B8へ送る

---

## 2. 背景

MS17では、既存の TEXT + WAV 入力からVMDを生成する機能を壊さずに、音声入力・音声変換・MMD用WAV出力の基盤を追加する。

MS17-B3では、FFmpeg / ffprobe locator と入力音声種別判定基盤を追加した。

B3で追加済みの主なファイルは以下。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
```

B3で確定した主な仕様は以下。

```text
- ffmpeg / ffprobe の探索順:
  1. repo直下 FFmpeg\bin
  2. PyInstaller onefile 展開先 sys._MEIPASS\FFmpeg
  3. PATH fallback

- .wav / .mp3 / .m4a を入力音声種別として判定する
- PATH上のFFmpeg / ffprobeはfallback扱い
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
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b5_audio_cache.py
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

- 解析用WAVは内部正本であり、MMD用WAVではない
```

MS17-B6では、wav / mp3 / m4a 入力導線をGUIへ統合した。

B6で確定した主な仕様は以下。

```text
- GUI文言を「WAV読み込み」から「音声読み込み」へ変更する
- ファイル選択dialogで .wav / .mp3 / .m4a を扱う
- 処理順:
  ファイル選択
  → 拡張子判定
  → ffprobe検査
  → 解析用WAV生成
  → 波形表示
  → 解析可能状態へ更新

- 波形表示・解析処理へ渡す音声パスは AnalysisWavResult.analysis_wav_path
- 最近使ったファイル履歴には元音声パスを保存する
- 解析用WAVパスはrecent filesに入れない
- B6では同期処理を基本とし、worker化はB8へ送る
```

MS17-B7では、MMDに読み込ませるためのユーザー向けWAV出力を追加する。

ただし、今回の方針では、VMD保存処理との連動出力ではなく、専用の「MMD用WAV出力」ボタンによる明示的な出力とする。

---

## 3. 目的

MS17-B7の目的は、ユーザーがMMDで読み込ませるためのWAVファイルを、GUIから明示的に出力できるようにすることである。

具体的には、以下を達成する。

1. MMD用WAVの仕様を以下に固定する。

```text
container: WAV
codec: PCM signed 16-bit little-endian
sample rate: 44100 Hz
channels: stereo
```

2. GUIに専用の「MMD用WAV出力」ボタンまたは同等の導線を追加する。
3. 「MMD用WAV出力」ボタンは、解析用WAV生成済みの場合に有効化する。
4. 保存先はユーザーが保存ダイアログで指定する。
5. 初期ファイル名は、元音声stem + `_mmd.wav` とする。
6. 保存先に同名ファイルがある場合は、上書き確認ダイアログを出し、ユーザーが承認した場合のみ上書きする。
7. MMD用WAVの入力元は、ユーザーが選択した元音声ファイルとする。
8. B7ではffprobe再検査を行わず、B6で保持済みの `AudioProbeResult` を利用する。
9. MMD用WAVと解析用WAVを明確に分離する。
10. VMD出力対象は引き続きリップモーフキーフレームのみとし、B7ではVMD保存処理を変更しない。
11. B8での worker / Busy / cancel / late callback破棄に備え、B7では同期処理を基本にしつつ責務境界を明確にする。

---

## 4. In Scope

MS17-B7で行う作業は以下に限定する。

### 4.1 MMD用WAV出力 core の追加

`src/core/mmd_wav_export.py` を追加する。

責務は以下。

```text
- MMD用WAV仕様を定義する
- 元音声ファイルからMMD用WAVを生成する
- ffmpeg runner または専用runnerを利用する
- 出力先WAVパスを受け取る
- 失敗時に不完全ファイルを削除する
- 成功時にMMD用WAV出力結果を返す
```

想定する結果構造。

```python
@dataclass(frozen=True)
class MmdWavSpec:
    codec: str
    sample_rate_hz: int
    channel_count: int

@dataclass(frozen=True)
class MmdWavExportResult:
    source_path: Path
    mmd_wav_path: Path
    spec: MmdWavSpec
    duration_sec: float | None
    file_size_bytes: int | None
```

仕様固定値。

```python
MMD_WAV_SPEC = MmdWavSpec(
    codec="pcm_s16le",
    sample_rate_hz=44100,
    channel_count=2,
)
```

B5の `AnalysisWavSpec` とは別定義にしてよい。
共通化する場合でも、解析用WAVとMMD用WAVの責務が混同されない命名にする。

### 4.2 ffmpeg runner の拡張またはMMD用WAV専用runner追加

B5で追加済みの `ffmpeg_runner.py` を利用できる場合は、MMD用WAV出力用の関数を追加する。

候補。

```python
def run_ffmpeg_mmd_wav(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> FfmpegRunResult:
    ...
```

想定コマンド。

```powershell
ffmpeg.exe -y -i <input_path> -vn -acodec pcm_s16le -ar 44100 -ac 2 -bitexact <output_path>
```

Python上の想定引数。

```python
[
    str(ffmpeg_path),
    "-y",
    "-i", str(input_path),
    "-vn",
    "-acodec", "pcm_s16le",
    "-ar", "44100",
    "-ac", "2",
    "-bitexact",
    str(output_path),
]
```

B5の解析用WAV生成コマンドとの差分。

```text
解析用WAV:
-ac 1

MMD用WAV:
-ac 2
```

注意。

```text
- shell=True を使わない
- コマンドは list[str] で渡す
- stderr は長すぎる場合に備えて切り詰める
- ユーザー向けmessageに生stderrをそのまま出さない
- timeout秒数を引数で指定できるようにする
- B7では長時間処理確認ダイアログを実装しない
- B7ではキャンセルUIを実装しない
```

### 4.3 MMD用WAV保存ダイアログ

GUIに「MMD用WAV出力」導線を追加する。

導線候補。

```text
- 上部ボタン
- ファイルメニュー
- 既存保存系ボタン付近
```

推奨は、既存のVMD保存導線と近い位置に「MMD用WAV出力」ボタンを追加すること。
ただし、B7ではGUIレイアウトの大規模再設計は行わない。

保存ダイアログ仕様。

```text
- 保存対象: WAVファイル
- 拡張子: .wav
- 初期ファイル名: 元音声stem + _mmd.wav
- 保存先: ユーザーが指定
- 同名ファイルがある場合: 上書き確認
```

推奨filter。

```text
WAVファイル (*.wav)|*.wav|すべてのファイル (*.*)|*.*
```

拡張子が省略された場合。

```text
- .wav を付与する
```

### 4.4 ボタン有効化条件

「MMD用WAV出力」ボタンは、解析用WAV生成済みなら有効化する。

具体的な条件候補。

```text
selected_analysis_wav が存在する
または
AnalysisWavResult がUiState / AppController上で保持されている
```

ただし、実際にMMD用WAVの入力元として使うのは元音声ファイルである。

そのため、有効化時には以下も確認する。

```text
- selected_audio_input が存在する
- selected_audio_probe が存在する
- selected_analysis_wav が存在する
```

ボタン有効化の考え方。

```text
selected_analysis_wav:
B6の音声読み込みフローが成功済みであることを示す

selected_audio_input:
MMD用WAV生成の入力元となる元音声ファイル

selected_audio_probe:
B6でffprobe検査済みであることを示す
```

B7では、ffprobe再検査は行わない。

### 4.5 MMD用WAVの入力元

MMD用WAVの入力元は、ユーザーが選択した元音声ファイルとする。

```text
入力元:
AudioInputInfo.source_path

出力先:
ユーザーが保存ダイアログで指定した .wav
```

理由。

```text
- ユーザー向け出力物は元音声から生成する
- 解析用WAVは内部正本であり、MMD用出力物とは責務を分ける
- B5の解析用WAVは mono であり、B7のMMD用WAVは stereo である
```

B7では、元音声ファイルに対してffprobe再検査は行わない。
B6で保持済みの `AudioProbeResult` を前提とする。

ただし、出力時点で元音声ファイルが存在しない場合は、ffmpeg実行前または実行失敗として明確に扱う。

### 4.6 上書き確認

保存先に同名ファイルが存在する場合は、上書き確認ダイアログを出す。

方針。

```text
- ユーザーが承認した場合のみ上書きする
- キャンセルした場合は出力しない
- キャンセルはエラーではなくユーザー中断として扱う
```

B7では、上書き確認はGUI側で行う。

core側は、指定された出力パスへ書き込む責務に留める。

### 4.7 失敗時の不完全ファイル削除

MMD用WAV生成に失敗した場合、出力途中の不完全ファイルを削除する。

対象。

```text
ユーザーが指定した output_path
```

注意。

```text
- source_path は絶対に削除しない
- analysis_wav_path は削除しない
- 既存ファイルを上書き中に失敗した場合の扱いは慎重に記録する
```

上書き時の注意。

```text
- ffmpeg -y で既存ファイルを上書きする場合、失敗時に既存ファイルが破損・削除される可能性がある
- B7では、上書き時の安全性を高めるため、一時出力ファイルに生成してから置換する方式を検討する
```

推奨実装。

```text
- 直接 output_path に出力せず、同じフォルダに一時ファイルを生成する
- 成功後に一時ファイルを output_path へ置換する
- 失敗時は一時ファイルを削除する
```

一時ファイル名候補。

```text
<target_stem>.tmp_mmd.wav
```

または衝突回避のために短いUUIDを付与する。

```text
<target_stem>_<uuid8>.tmp_mmd.wav
```

この方式により、既存の同名ファイルを直接壊すリスクを下げる。

### 4.8 エラー分類の拡張

B4/B5で追加した `audio_errors.py` を必要に応じて拡張する。

追加候補。

```text
mmd_wav_source_missing
mmd_wav_output_cancelled
mmd_wav_output_path_invalid
mmd_wav_permission_error
mmd_wav_export_failed
mmd_wav_output_failed
mmd_wav_cleanup_failed
mmd_wav_replace_failed
```

既存の `ffmpeg_not_found` / `ffmpeg_permission_error` / `ffmpeg_timeout` / `ffmpeg_execution_failed` は再利用できる。

エラー設計方針。

```text
- ffmpeg実行失敗とMMD用WAV出力失敗を区別する
- ユーザーキャンセルは失敗扱いにしない
- ユーザー向けmessageと開発者向けdetailを分ける
- stderr全文をユーザー向けmessageへ直接出さない
```

### 4.9 テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

標準テストでは、実 `ffmpeg.exe` を必須にしない。

テスト方針。

```text
- ffmpeg runner は subprocess.run を mock する
- mmd_wav_export は fake runner を注入する
- 保存ダイアログはGUI部品を直接表示せず、メソッド・状態・戻り値をテストする
- 上書き確認は confirm callback などを注入してテストする
- 実ファイル生成は tmp_path 上で行う
- 不完全ファイル削除を確認する
```

---

## 5. Out of Scope

MS17-B7では以下を行わない。

```text
- VMD保存処理との連動MMD用WAV出力
- VMD保存処理の変更
- VMD出力対象の変更
- VMDにボーン / カメラ / 照明 / IK / 表示制御を追加すること
- MMD用WAVの複数プリセット
- MMD用WAVの音量正規化
- MMD用WAVの無音トリム
- MMD用WAVの自動フェード
- MMD用WAVの自動ノイズ除去
- ピッチ補正
- テンポ補正
- GUIの大規模再設計
- worker化
- Busy状態の完全統合
- cancel UI
- late callback破棄
- 300秒確認ダイアログ
- cache/analysis_wav/ の自動削除
- 変換キャッシュ再利用
- FFmpeg / ffprobe の自動ダウンロード
- FFmpegバイナリのrepo追加
- build.ps1変更
- MMD_AutoLipTool.spec変更
- .gitignore作成・変更
- Qt / PySide6 系GUIの再導入
- 旧 src/gui 系の復活
```

README本文更新は原則B9へ送る。
ただし、B7完了時点でREADMEの記載と実装が大きく矛盾する場合は、B7完了報告に「B9で要更新」として明記する。

---

## 6. 前提条件

MS17-B7は、以下を前提とする。

```text
- 作業branchは feature/MS17 である
- MS17-B1 が完了済みである
- MS17-B2 が完了済みである
- MS17-B3 が完了済みである
- MS17-B4 が完了済みである
- MS17-B5 が完了済みである
- MS17-B6 が完了済みである
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
- 解析用WAVは内部正本である
```

B6から引き継ぐ仕様。

```text
- GUIから wav / mp3 / m4a を選択できる
- AudioInputInfo が保持されている
- AudioProbeResult が保持されている
- AnalysisWavResult が保持されている
- 波形表示・解析処理には AnalysisWavResult.analysis_wav_path が渡されている
- 最近使ったファイル履歴には元音声パスが保存されている
```

B7で固定する仕様。

```text
- MMD用WAVは PCM signed 16-bit little-endian / 44100 Hz / stereo
- MMD用WAVは専用の「MMD用WAV出力」ボタンで出力する
- VMD保存処理との連動出力はB7では行わない
- ボタンは解析用WAV生成済みなら有効化する
- 保存先はユーザーが保存ダイアログで指定する
- 初期ファイル名は元音声stem + _mmd.wav
- 同名ファイルがある場合は上書き確認を行う
- MMD用WAVの入力元は元音声ファイル
- B7ではffprobe再検査を行わない
- B6で保持済みの AudioProbeResult を利用する
```

### 6.1 実装前チェック反映

2026-06-01 の MS17-B7 実装前チェックで、実装を止める P1 問題は確認されていない。

ただし、以下の P2 注意点を実装時に解消または明示的に扱う。

```text
1. MMD用WAV仕様は stereo 固定で扱う。
   docs/MMD_Audio_WAV_Compatibility_Specification.md の検証条件には
   「channel count が 1 または 2」という表現が残っているが、
   B7実装・B7テストでは channel count = 2 を正とする。
   必要な仕様書表現の補正は、B7実装時またはB9 closeoutで記録対象にする。

2. UiState には B6時点で selected_audio_input / selected_audio_probe /
   selected_analysis_wav は存在するが、B7で使用する
   last_mmd_wav_export_dir / last_mmd_wav_output_path /
   mmd_wav_export_ready は未実装である。
   B7実装時に追加し、成功時のみ last_mmd_wav_output_path を更新する。

3. src/core/mmd_wav_export.py と B7用テスト群は現時点では存在しない。
   これは B7 未着手状態として整合しており、B7の追加対象とする。

4. src/core/ffmpeg_runner.py は現時点では解析用WAV用の
   run_ffmpeg_analysis_wav のみを持つ。
   B7では MMD用WAV専用に -ac 2 を指定する runner を追加し、
   解析用WAV生成の -ac 1 経路を壊さない。

5. src/core/audio_errors.py には MMD用WAV固有のエラーコードが未追加である。
   B7では MMD用WAV出力固有の失敗を、解析用WAV生成失敗と混同しない
   最小限のエラー分類として追加する。
```

この節の内容は、ユーザー判断が必要な仕様分岐ではなく、既存のB7方針
（MMD用WAVは `pcm_s16le / 44100 Hz / stereo` 固定）を実装時に徹底するための注意事項である。

---

## 7. 対象ファイル

MS17-B7で追加する候補。

```text
src/core/mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

MS17-B7で必要に応じて変更する候補。

```text
src/core/ffmpeg_runner.py
src/core/audio_errors.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
docs/repo_milestone.md
docs/Version_Control.md
```

MS17-B7で参照するファイル。

```text
src/core/audio_input.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/ffmpeg_locator.py
src/core/audio_cache.py
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

B7では、`build.ps1` / `MMD_AutoLipTool.spec` / `.gitignore` は変更しない。

---

## 8. 実装方針

### 8.1 全体方針

MS17-B7では、MMD用WAV出力を core 層と GUI 導線に追加する。

基本方針。

```text
- MMD用WAVはユーザー向け出力物である
- 解析用WAVは内部正本である
- MMD用WAVと解析用WAVを混同しない
- MMD用WAVは元音声ファイルから生成する
- B7ではffprobe再検査を行わない
- B6で保持済みの AudioProbeResult を利用する
- VMD保存処理は変更しない
- VMD保存処理との連動出力はB7では行わない
```

### 8.2 MMD用WAV生成コマンド

MMD用WAV生成コマンドは以下に固定する。

```powershell
ffmpeg.exe -y -i <source_audio_path> -vn -acodec pcm_s16le -ar 44100 -ac 2 -bitexact <output_path>
```

出力仕様。

```text
container: WAV
codec: PCM signed 16-bit little-endian
sample rate: 44100 Hz
channels: stereo
chunk: RIFF/WAVE -> fmt(size 16) -> data
```

`-bitexact` は、FFmpegのWAV出力に `LIST` chunk などのmetadata chunkが混入してMMD用WAV検証に失敗するケースを避けるために指定する。

B5の解析用WAVとの差分。

```text
解析用WAV:
- mono
- cache/analysis_wav/
- 内部正本

MMD用WAV:
- stereo
- ユーザー指定保存先
- MMDに読み込ませるための出力物
```

### 8.3 `mmd_wav_export.py` 設計

`mmd_wav_export.py` は、MMD用WAV生成の高レベル処理を担当する。

想定構造。

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class MmdWavSpec:
    codec: str
    sample_rate_hz: int
    channel_count: int

@dataclass(frozen=True)
class MmdWavExportResult:
    source_path: Path
    mmd_wav_path: Path
    spec: MmdWavSpec
    duration_sec: float | None
    file_size_bytes: int | None
```

想定定数。

```python
MMD_WAV_SPEC = MmdWavSpec(
    codec="pcm_s16le",
    sample_rate_hz=44100,
    channel_count=2,
)
```

関数候補。

```python
def export_mmd_wav(
    source_path: str | Path,
    output_path: str | Path,
    ffmpeg_path: str | Path,
    *,
    probe_result: AudioProbeResult | None = None,
    runner: Callable[..., FfmpegRunResult] | None = None,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> MmdWavExportResult:
    ...
```

責務。

```text
1. source_pathをPathへ変換
2. output_pathをPathへ変換
3. ffmpeg_pathをPathへ変換
4. source_pathの存在を確認する
5. output_pathの親ディレクトリを確認する
6. 一時出力ファイルを作る
7. ffmpeg runnerを呼び出す
8. 成功時に一時出力ファイルをoutput_pathへ置換する
9. 成功時にMmdWavExportResultを返す
10. 失敗時に一時出力ファイルを削除する
```

B7ではffprobe再検査を行わない。
`probe_result` はB6で保持済みの結果を参照するために受け取る。

### 8.4 上書き安全性

MMD用WAVはユーザー指定保存先へ出力するため、上書き時の安全性を重視する。

推奨方式。

```text
1. GUI側で上書き確認を行う
2. ユーザーが承認した場合のみ処理を進める
3. core側では直接 output_path に書かず、一時ファイルへ出力する
4. ffmpeg成功後に一時ファイルを output_path へ置換する
5. 失敗時は一時ファイルのみ削除する
```

一時ファイル名候補。

```text
<output_stem>_<uuid8>.tmp_mmd.wav
```

例。

```text
song_12ab34cd.tmp_mmd.wav
```

注意。

```text
- source_path は削除しない
- analysis_wav_path は削除しない
- 既存 output_path は、置換直前まで直接触らない
```

置換失敗時。

```text
mmd_wav_replace_failed
```

cleanup失敗時。

```text
mmd_wav_cleanup_failed
```

### 8.5 GUI導線

GUIに「MMD用WAV出力」ボタンまたは同等のメニュー項目を追加する。

候補。

```text
- 既存のVMD保存ボタン付近
- ファイルメニュー内
- 右ペインの出力関連領域
```

推奨は、既存のVMD保存導線の近くに配置すること。
ただし、B7ではGUI全体の大規模再設計は行わない。

表示文言。

```text
MMD用WAV出力
```

ツールチップ候補。

```text
MMDで読み込ませるためのWAVファイルを出力します。
```

### 8.6 ボタン有効化

「MMD用WAV出力」ボタンは、解析用WAV生成済みなら有効化する。

最低条件。

```text
selected_analysis_wav が存在する
```

実用上の確認候補。

```text
selected_audio_input が存在する
selected_audio_probe が存在する
selected_analysis_wav が存在する
ffmpeg path が解決できる
```

ただし、ffmpeg path 解決をボタン有効化条件に含めるかどうかは、実装状態に応じて判断する。

推奨。

```text
- ボタン有効化は selected_analysis_wav の存在を主条件にする
- 実際の出力処理時に ffmpeg path を解決し、見つからなければエラー表示する
```

理由。

```text
- 有効化条件を複雑にしすぎない
- B6の音声読み込み成功をMMD用WAV出力可能状態として扱える
- ffmpeg path の詳細エラーは押下時にユーザーへ示せる
```

### 8.7 保存ダイアログ

保存ダイアログは、MMD用WAV出力ボタン押下時に表示する。

初期ファイル名。

```text
<source_stem>_mmd.wav
```

例。

```text
song_mmd.wav
```

保存filter。

```text
WAVファイル (*.wav)|*.wav|すべてのファイル (*.*)|*.*
```

拡張子補完。

```text
ユーザーが拡張子を省略した場合は .wav を付与する
```

保存先に同名ファイルが存在する場合。

```text
上書き確認ダイアログを出す
ユーザーが承認した場合のみ出力する
キャンセル時は何も出力しない
```

キャンセル時の扱い。

```text
- エラー扱いにしない
- statusに「MMD用WAV出力をキャンセルしました」程度を表示してよい
- 内部状態を破壊しない
```

### 8.8 AppController の変更方針

`src/gui_wx/app_controller.py` では、MMD用WAV出力の高レベル処理を担当する。

想定メソッド。

```python
def request_export_mmd_wav(self) -> None:
    ...
```

既存の `request_save_vmd(self)` と同様に、Controllerがview側の保存ダイアログを呼び出して `output_path` を取得する構造に合わせる。

処理順。

```text
1. selected_analysis_wav が存在するか確認する
2. selected_audio_input が存在するか確認する
3. selected_audio_probe が存在するか確認する
4. 保存ダイアログで output_path を取得する
5. 同名ファイルがある場合は上書き確認する
6. locate_ffmpeg_tools で ffmpeg path を取得する
7. export_mmd_wav を実行する
8. 成功時にstatusを更新する
9. 失敗時にユーザー向けmessageを表示する
```

B7ではffprobe再検査は行わない。

### 8.9 UiState の変更方針

`src/gui_wx/ui_state.py` では、必要に応じて以下を追加する。

```text
mmd_wav_export_ready
last_mmd_wav_export_dir
last_mmd_wav_output_path
```

ただし、既存構造に `playback_ready` / `analysis_ready` / `vmd_save_ready` などがある場合は、それらと矛盾しないようにする。

有効化条件の候補。

```python
@property
def mmd_wav_export_ready(self) -> bool:
    return self.selected_analysis_wav is not None
```

実際のプロパティ名・型はrepo状態に従う。

### 8.10 エラー時の状態

MMD用WAV出力失敗時、既存の解析結果やPreviewを無効化する必要は原則ない。

理由。

```text
- MMD用WAV出力はユーザー向け保存処理であり、既存の解析結果自体は壊れていない
- 出力失敗で timing plan / Preview / VMD保存可能状態 を無効化すると過剰
```

ただし、以下は行う。

```text
- statusに失敗messageを表示する
- 不完全な一時ファイルを削除する
- 出力成功扱いにしない
- last_mmd_wav_output_path を成功時のみ更新する
```

元音声ファイルが見つからない場合。

```text
- MMD用WAV出力は失敗扱い
- selected_audio_input は必要に応じて保持したままでもよい
- 再読み込みを促すmessageを表示する
```

### 8.11 docs更新方針

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録する内容。

```text
- MS17-B7を実施したこと
- MMD用WAV仕様を PCM signed 16-bit little-endian / 44100 Hz / stereo に固定したこと
- 専用の「MMD用WAV出力」導線を追加したこと
- VMD保存処理との連動出力ではなく専用ボタン出力にしたこと
- ボタン有効化条件を解析用WAV生成済みにしたこと
- 保存先はユーザー指定にしたこと
- 初期ファイル名を 元音声stem + _mmd.wav にしたこと
- 同名ファイルは上書き確認後のみ上書きすること
- MMD用WAVの入力元は元音声ファイルであること
- B7ではffprobe再検査を行わず、B6で保持済みの AudioProbeResult を利用すること
- B8ではBusy / worker / cancel / 300秒確認へ進むこと
```

README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは原則変更しない。

ただし、B7完了によりREADMEの使用説明との差分が大きくなる場合は、B9で更新する必要性を完了報告に記録する。

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
- MS17-B6完了commitまたは記録があるか
- B7開始前に意図しない差分がないか
```

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。

### Step 2: B3〜B6成果確認

以下を確認する。

```text
src/core/audio_input.py
src/core/ffmpeg_locator.py
src/core/audio_errors.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/ffmpeg_runner.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
docs/repo_milestone.md
docs/Version_Control.md
```

確認観点。

```text
- AudioInputInfo が存在するか
- AudioProbeResult が存在するか
- AnalysisWavResult が存在するか
- selected_audio_input が保持されているか
- selected_audio_probe が保持されているか
- selected_analysis_wav が保持されているか
- ffmpeg path を locator で解決できるか
- B6で音声読み込み導線が統合されているか
- B7へ進む記録があるか
```

### Step 3: `src/core/audio_errors.py` 拡張

必要に応じて、B7用の error code を追加する。

追加候補。

```text
mmd_wav_source_missing
mmd_wav_output_cancelled
mmd_wav_output_path_invalid
mmd_wav_permission_error
mmd_wav_export_failed
mmd_wav_output_failed
mmd_wav_cleanup_failed
mmd_wav_replace_failed
```

既存の以下は再利用してよい。

```text
ffmpeg_not_found
ffmpeg_permission_error
ffmpeg_timeout
ffmpeg_execution_failed
analysis_wav_cleanup_failed
```

ただし、MMD用WAV出力固有の失敗と解析用WAV生成失敗を混同しない。

### Step 4: `src/core/ffmpeg_runner.py` 拡張

`ffmpeg_runner.py` に MMD用WAV出力用の関数を追加する。

追加候補。

```text
run_ffmpeg_mmd_wav
```

コマンド仕様。

```text
ffmpeg.exe -y -i <input_path> -vn -acodec pcm_s16le -ar 44100 -ac 2 -bitexact <output_path>
```

注意。

```text
- shell=True は使わない
- stdout / stderr をcaptureする
- timeoutを扱う
- returncode失敗を分類する
- FileNotFoundError / PermissionError / TimeoutExpired を分類する
```

B5の `run_ffmpeg_analysis_wav` と共通化できる場合は、内部helperを追加してよい。
ただし、大規模リファクタは避ける。

### Step 5: `src/core/mmd_wav_export.py` 追加

`src/core/mmd_wav_export.py` を追加する。

最低限含めるもの。

```text
MmdWavSpec
MmdWavExportResult
MMD_WAV_SPEC
export_mmd_wav
```

実装内容。

```text
- source_pathを受け取る
- output_pathを受け取る
- ffmpeg_pathを受け取る
- probe_resultを任意で受け取る
- runnerを任意で注入できる
- timeout_secを受け取れる
- 一時出力ファイルへ変換する
- 成功時に一時ファイルをoutput_pathへ置換する
- 成功時にMmdWavExportResultを返す
- 失敗時に一時ファイルを削除する
```

B7では、ffprobe再検査は行わない。

### Step 6: MainFrameにMMD用WAV出力導線を追加

`main_frame.py` に「MMD用WAV出力」ボタンまたはメニュー項目を追加する。

推奨。

```text
- VMD保存ボタン付近に配置
- 文言は「MMD用WAV出力」
- tooltipに「MMDで読み込ませるためのWAVファイルを出力します。」を設定
```

有効化条件。

```text
解析用WAV生成済み
```

実装上は `update_action_states` 相当の処理で制御する。

### Step 7: 保存ダイアログ実装

MMD用WAV出力時に保存ダイアログを表示する。

仕様。

```text
- 初期ファイル名: 元音声stem + _mmd.wav
- filter: WAVファイル (*.wav)|*.wav|すべてのファイル (*.*)|*.*
- 拡張子省略時は .wav を付与
- 保存先はユーザー指定
```

同名ファイルがある場合。

```text
- 上書き確認ダイアログを出す
- 承認時のみ出力する
- キャンセル時は何も出力しない
```

キャンセル時。

```text
- エラー扱いにしない
- statusにキャンセルを表示してよい
- 既存解析状態は変更しない
```

### Step 8: AppControllerにMMD用WAV出力処理を追加

`app_controller.py` に、MMD用WAV出力処理を追加する。

想定メソッド。

```python
def request_export_mmd_wav(self) -> None:
    ...
```

既存の `request_save_vmd(self)` と同様に、Controllerがview側の保存ダイアログを呼び出して `output_path` を取得する構造に合わせる。

処理順。

```text
1. selected_analysis_wav が存在するか確認
2. selected_audio_input が存在するか確認
3. selected_audio_probe が存在するか確認
4. source_path = selected_audio_input.source_path を取得
5. output_path を保存ダイアログから取得
6. 同名ファイルがある場合は上書き確認
7. locate_ffmpeg_tools で ffmpeg path を取得
8. export_mmd_wav を実行
9. 成功時にstatus更新
10. 失敗時にユーザー向けmessage表示
```

B7では、ffprobe再検査は行わない。
B6で保持済みの `selected_audio_probe` を利用する。

### Step 9: UiStateを必要最小限で拡張

必要に応じて `ui_state.py` を拡張する。

追加候補。

```text
mmd_wav_export_ready
last_mmd_wav_export_dir
last_mmd_wav_output_path
```

有効化条件候補。

```python
@property
def mmd_wav_export_ready(self) -> bool:
    return self.selected_analysis_wav is not None
```

実際のプロパティ名・型はrepo状態に従う。

### Step 10: テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

テスト内容。

```text
- MMD_WAV_SPEC が pcm_s16le / 44100 / stereo である
- run_ffmpeg_mmd_wav が -ac 2 を指定する
- shell=True を使っていない
- export_mmd_wav が元音声ファイルを入力元にする
- export_mmd_wav が一時ファイル経由で出力する
- 失敗時に一時ファイルが削除される
- source_path が削除されない
- analysis_wav_path が削除されない
- ボタンは解析用WAV生成済みで有効になる
- 保存ダイアログの初期ファイル名が 元音声stem + _mmd.wav になる
- 拡張子省略時に .wav が付与される
- 同名ファイルがある場合に上書き確認が呼ばれる
- 上書きキャンセル時に出力されない
```

### Step 11: B3〜B6回帰テスト

必要に応じて、B3〜B6の限定テストを再実行する。
現repoには `test_ms17_b6_*` 形式の専用テストは存在しないため、B6のGUI統合確認は既存の wx 入力統合テストで確認する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
```

### Step 12: B7限定テスト実行

以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

既存GUI関連の回帰確認として、必要に応じて以下を限定実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

全体pytestは、既知のハング可能性がある場合は実行しない。

### Step 13: docs更新

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録内容。

```text
- MS17-B7を実施したこと
- MMD用WAV仕様を PCM signed 16-bit little-endian / 44100 Hz / stereo に固定したこと
- 専用の「MMD用WAV出力」導線を追加したこと
- VMD保存処理との連動出力ではなく専用ボタン出力にしたこと
- ボタン有効化条件を解析用WAV生成済みにしたこと
- 保存先はユーザー指定にしたこと
- 初期ファイル名を 元音声stem + _mmd.wav にしたこと
- 同名ファイルは上書き確認後のみ上書きすること
- MMD用WAVの入力元は元音声ファイルであること
- B7ではffprobe再検査を行わず、B6で保持済みの AudioProbeResult を利用すること
- B8ではBusy / worker / cancel / 300秒確認へ進むこと
```

READMEはB9でMS17全体closeout時に更新する方針とする。
ただし、B7完了報告にREADME更新必要性を明記する。

### Step 14: 完了前diff確認

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
src/core/mmd_wav_export.py
src/core/ffmpeg_runner.py
src/core/audio_errors.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
docs/repo_milestone.md
docs/Version_Control.md
```

以下に差分がないことを確認する。

```text
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
.gitignore
```

READMEに差分が出ている場合は、B7で必要最小限の更新か、B9へ送るべき更新かを報告で明確にする。

---

## 10. 状態遷移 / データ契約

### 10.1 B7で追加するデータ契約

B7では、MMD用WAV出力結果として `MmdWavExportResult` を追加する。

役割。

```text
MmdWavExportResult:
- MMDに読み込ませるためのWAV出力結果
- ユーザー指定保存先のWAVファイル
- 解析用WAVではない
- VMD出力ではない
```

想定構造。

```text
source_path
mmd_wav_path
spec
duration_sec
file_size_bytes
```

`spec` の固定値。

```text
codec: pcm_s16le
sample_rate_hz: 44100
channel_count: 2
```

### 10.2 正本の扱い

B7でも、以下の分離を維持する。

```text
入力音声:
ユーザーが選択した元音声ファイル
AudioInputInfo.source_path

解析用WAV:
波形表示・解析・timing plan生成の内部正本
AnalysisWavResult.analysis_wav_path

MMD用WAV:
MMDに読み込ませるためのユーザー向け出力物
MmdWavExportResult.mmd_wav_path

VMD出力:
リップモーフキーフレームのみ
```

B7では、MMD用WAVを解析用WAVの代替正本にしない。

### 10.3 B7で変更するGUI状態

B7で追加・更新する候補。

```text
mmd_wav_export_ready
last_mmd_wav_export_dir
last_mmd_wav_output_path
```

有効化条件。

```text
selected_analysis_wav が存在する
```

補助的に確認する状態。

```text
selected_audio_input
selected_audio_probe
selected_analysis_wav
```

### 10.4 B7で変更しない契約

以下はB7では変更しない。

```text
- selected_wav_path
- selected_wav_analysis
- current_timing_plan
- analysis_result_valid
- Preview shape contract
- VMD writer input
- VMD保存処理
- AnalysisWavResult.analysis_wav_path
- recent audio files
```

B7では、MMD用WAV出力失敗時に `current_timing_plan` や `Preview` を無効化しない。
MMD用WAV出力は保存処理であり、解析結果そのものを壊すものではないためである。

### 10.5 B8以降へ送る契約

以下はB8で扱う。

```text
worker_job_id
cancel_token
busy_state
ffmpeg_process_handle
ffprobe_process_handle
late_callback_generation_id
long_processing_confirmation_state
```

B7では、同期処理を基本とし、worker化しない。

---

## 11. テスト方針

### 11.1 B7で実行する標準テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

### 11.2 B3〜B6回帰テスト

必要に応じて以下を実行する。
現repoには `test_ms17_b6_*` 形式の専用テストは存在しないため、B6のGUI統合確認は既存の wx 入力統合テストで確認する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
```

### 11.3 既存GUI回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

### 11.4 実 ffmpeg テスト方針

B7では、実 `ffmpeg.exe` を必須テストにしない。

理由。

```text
- B7の標準テストを環境依存にしないため
- B5/B6と同様に mock / fake runner 中心で検証するため
- 実体確認はB9統合確認または手動確認へ送るため
```

必要に応じて任意手動確認として、ローカル環境で実ファイルをMMD用WAVとして出力する確認を行ってよい。
ただし、B7の自動テスト完了条件には含めない。

### 11.5 全体pytest

全体pytestは、既知のハング可能性がある場合は実行しない。

実行しない場合は、完了報告に理由を書く。

---

## 12. 受け入れ条件

MS17-B7は、以下を満たしたら完了とする。

### 12.1 実装条件

* `src/core/mmd_wav_export.py` が追加されている。
* 必要に応じて `src/core/ffmpeg_runner.py` に MMD用WAV出力関数が追加されている。
* MMD用WAV仕様が `pcm_s16le / 44100 Hz / stereo` として固定されている。
* GUIに「MMD用WAV出力」導線が追加されている。
* 「MMD用WAV出力」ボタンは解析用WAV生成済みで有効化される。
* 保存ダイアログで保存先をユーザーが指定できる。
* 初期ファイル名が元音声stem + `_mmd.wav` になっている。
* 拡張子省略時に `.wav` が付与される。
* 同名ファイルが存在する場合、上書き確認が出る。
* ユーザーが上書きを承認した場合のみ上書きされる。
* ユーザーがキャンセルした場合は出力されない。
* MMD用WAVの入力元が元音声ファイルになっている。
* B7ではffprobe再検査を行わず、B6で保持済みの `AudioProbeResult` を利用している。
* MMD用WAVと解析用WAVが混同されていない。
* 失敗時に不完全な一時ファイルが削除される。
* 既存の解析結果・Preview・VMD保存可能状態を過剰に無効化しない。

### 12.2 禁止事項遵守

以下が守られている。

```text
- VMD保存処理との連動出力をしていない
- VMD保存処理を変更していない
- VMD出力対象を変更していない
- ボーン / カメラ / 照明 / IK / 表示制御をVMDへ追加していない
- MMD用WAVの複数プリセットを実装していない
- 音量正規化をしていない
- 無音トリムをしていない
- 自動フェードをしていない
- 自動ノイズ除去をしていない
- worker化をしていない
- Busy状態の完全統合をしていない
- cancel UIを実装していない
- late callback破棄を実装していない
- 300秒確認ダイアログを実装していない
- build.ps1を変更していない
- MMD_AutoLipTool.specを変更していない
- .gitignoreを変更していない
- Qt / PySide6を再導入していない
```

### 12.3 テスト条件

以下が成功している。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

必要に応じて実行したB3〜B6回帰テスト、既存GUI回帰テストの結果が報告されている。

全体pytestを実行しなかった場合は、その理由が報告されている。

### 12.4 docs条件

以下が必要最小限で更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録上、B7の範囲が以下として明確である。

```text
- MMD用WAV出力基盤
- MMD用WAV仕様は pcm_s16le / 44100 Hz / stereo
- 専用の「MMD用WAV出力」導線
- VMD保存処理との連動出力ではない
- 保存先はユーザー指定
- 上書き確認あり
- 入力元は元音声ファイル
- ffprobe再検査なし
- B6保持済みの AudioProbeResult を利用
- B8でBusy / worker / cancel / 300秒確認へ進む
```

---

## 13. リスクと対策

### Risk 1: MMD用WAVと解析用WAVを混同する

対策。

```text
- MMD用WAVは MmdWavExportResult として別構造にする
- 解析用WAVは AnalysisWavResult として維持する
- MMD用WAVはユーザー指定保存先へ出力する
- 解析用WAVは cache/analysis_wav/ の内部正本として維持する
- テストで MMD用WAVが analysis_wav_path を上書きしないことを確認する
```

### Risk 2: VMD保存処理との連動出力に踏み込んでしまう

対策。

```text
- B7では専用ボタン出力に限定する
- VMD保存処理を変更しない
- VMD保存処理との連動出力はB9以降または別Blockで検討する
```

### Risk 3: 元音声ファイルが読み込み後に削除・移動される

対策。

```text
- 出力時に source_path の存在確認を行う
- 見つからない場合は mmd_wav_source_missing として扱う
- ffprobe再検査は行わない
- 再読み込みを促すユーザー向けmessageを出す
```

### Risk 4: 上書き時に既存ファイルを壊す

対策。

```text
- GUI側で上書き確認を行う
- core側では一時ファイルへ出力してから置換する
- 失敗時は一時ファイルだけ削除する
- source_path / analysis_wav_path を削除しない
```

### Risk 5: 実 ffmpeg 依存でテストが不安定になる

対策。

```text
- 標準テストは mock / fake runner にする
- 実 ffmpeg 必須テストを入れない
- 実体確認はB9統合確認または任意手動確認へ送る
```

### Risk 6: MMD用WAV出力失敗時に解析状態を壊す

対策。

```text
- MMD用WAV出力失敗では current_timing_plan / Preview / VMD保存可能状態を無効化しない
- 保存処理の失敗としてstatus表示に留める
- 成功時のみ last_mmd_wav_output_path を更新する
```

### Risk 7: B7でworker化まで進んでしまう

対策。

```text
- B7は同期処理を基本とする
- Busy / cancel / late callback破棄はB8へ送る
- B7完了報告にB8引き継ぎとして明記する
```

### Risk 8: READMEとGUIの記述が一時的にずれる

対策。

```text
- B7ではREADME大規模更新を行わない
- B9 closeoutでREADMEをMS17完了状態へ更新する
- B7完了報告にREADME更新必要性を記録する
```

---

## 14. Codex 実装時の注意

以下のプロンプトを Codex に渡して実施する。

```text
今回は MS17-B7 です。

目的:
MMD用WAV出力基盤を実装してください。

重要:
- 対象branchは feature/MS17 です。
- MS17-B3 / B4 / B5 / B6 の成果を前提にしてください。
- MMD用WAV仕様は PCM signed 16-bit little-endian / 44100 Hz / stereo です。
- 出力導線は専用の「MMD用WAV出力」ボタンにしてください。
- B7ではVMD保存処理との連動出力は行わないでください。
- 「MMD用WAV出力」ボタンは、解析用WAV生成済みなら有効化してください。
- 保存先はユーザーが保存ダイアログで指定するようにしてください。
- 初期ファイル名は 元音声stem + _mmd.wav にしてください。
- 同名ファイルが存在する場合は、上書き確認ダイアログを出し、ユーザーが承認した場合のみ上書きしてください。
- MMD用WAVの入力元は、ユーザーが選択した元音声ファイルにしてください。
- B7ではffprobe再検査を行わないでください。
- B6で保持済みの AudioProbeResult を利用してください。
- MMD用WAVと解析用WAVを混同しないでください。
- worker化、Busy状態の完全統合、cancel、late callback破棄はB8へ送ってください。
- 300秒確認ダイアログは実装しないでください。
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わないでください。
- VMD保存処理は変更しないでください。
- VMD出力対象は引き続きリップモーフキーフレームのみです。
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
src/core/ffmpeg_runner.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
docs/repo_milestone.md
docs/Version_Control.md

実装候補:

src/core/mmd_wav_export.py
src/core/ffmpeg_runner.py
src/core/audio_errors.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py

実装内容:

1. src/core/mmd_wav_export.py を追加してください。
   - MmdWavSpec を定義してください。
   - MmdWavExportResult を定義してください。
   - MMD_WAV_SPEC は pcm_s16le / 44100 Hz / stereo にしてください。
   - export_mmd_wav を実装してください。
   - 入力元は元音声ファイルにしてください。
   - 出力先はユーザー指定の output_path にしてください。
   - ffprobe再検査は行わないでください。
   - B6で保持済みの AudioProbeResult を受け取れるようにしてください。
   - 一時ファイルへ出力し、成功後にoutput_pathへ置換してください。
   - 失敗時は一時ファイルを削除してください。
   - source_path や analysis_wav_path を削除しないでください。

2. src/core/ffmpeg_runner.py を必要最小限で拡張してください。
   - run_ffmpeg_mmd_wav などを追加してください。
   - コマンドは以下の仕様にしてください。
     ffmpeg.exe -y -i <input_path> -vn -acodec pcm_s16le -ar 44100 -ac 2 -bitexact <output_path>
   - shell=True は使わないでください。
   - stdout / stderr をcaptureしてください。
   - timeoutを扱ってください。
   - returncode失敗、FileNotFoundError、PermissionError、TimeoutExpired を分類してください。
   - B5の解析用WAV生成関数を壊さないでください。

3. src/core/audio_errors.py を必要最小限で拡張してください。
   - mmd_wav_source_missing
   - mmd_wav_output_cancelled
   - mmd_wav_output_path_invalid
   - mmd_wav_permission_error
   - mmd_wav_export_failed
   - mmd_wav_output_failed
   - mmd_wav_cleanup_failed
   - mmd_wav_replace_failed
   などを必要に応じて扱えるようにしてください。
   - 既存のffmpeg系エラーを再利用できる場合は再利用してください。
   - 解析用WAV生成失敗とMMD用WAV出力失敗を混同しないでください。

4. GUIに「MMD用WAV出力」導線を追加してください。
   - 既存のVMD保存導線の近くに配置することを推奨します。
   - 大規模レイアウト変更は行わないでください。
   - ボタン文言は「MMD用WAV出力」にしてください。
   - tooltipに「MMDで読み込ませるためのWAVファイルを出力します。」のような説明を追加してよいです。

5. ボタン有効化条件を追加してください。
   - 解析用WAV生成済みなら有効化してください。
   - 実装上は selected_analysis_wav の存在を主条件にしてください。
   - selected_audio_input / selected_audio_probe も出力時に確認してください。

6. 保存ダイアログを実装してください。
   - 初期ファイル名は 元音声stem + _mmd.wav にしてください。
   - filterは WAVファイル (*.wav)|*.wav|すべてのファイル (*.*)|*.* を推奨します。
   - ユーザーが拡張子を省略した場合は .wav を付与してください。
   - 同名ファイルがある場合は上書き確認を出してください。
   - ユーザーがキャンセルした場合は出力せず、エラー扱いにしないでください。

7. AppControllerにMMD用WAV出力処理を追加してください。
   - selected_analysis_wav が存在するか確認してください。
   - selected_audio_input が存在するか確認してください。
   - selected_audio_probe が存在するか確認してください。
   - source_path は selected_audio_input.source_path を使ってください。
   - ffmpeg path は locate_ffmpeg_tools で取得してください。
   - export_mmd_wav を呼び出してください。
   - 成功時のみ last_mmd_wav_output_path などを更新してください。
   - 失敗時に current_timing_plan / Preview / VMD保存可能状態を過剰に無効化しないでください。

8. テストを追加してください。
   - tests/test_ms17_b7_mmd_wav_export.py
   - tests/test_ms17_b7_mmd_wav_save_dialog.py
   - tests/test_ms17_b7_mmd_wav_button_state.py
   - tests/test_ms17_b7_mmd_wav_failure_cleanup.py
   - tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
   実際のrepoのテスト構成に合わせてファイル名は調整してよいです。

実行するテスト:

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py

必要に応じてB3〜B6回帰テストも実行してください。

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py

必要に応じて既存GUI回帰テストも限定実行してください。

.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py

全体pytestは、ハング可能性がある場合は実行しないでください。

実装後、必要最小限で以下を更新してください。

docs/repo_milestone.md
docs/Version_Control.md

記録内容:
- MS17-B7を実施したこと
- MMD用WAV仕様を PCM signed 16-bit little-endian / 44100 Hz / stereo に固定したこと
- 専用の「MMD用WAV出力」導線を追加したこと
- VMD保存処理との連動出力ではなく専用ボタン出力にしたこと
- ボタン有効化条件を解析用WAV生成済みにしたこと
- 保存先はユーザー指定にしたこと
- 初期ファイル名を 元音声stem + _mmd.wav にしたこと
- 同名ファイルは上書き確認後のみ上書きすること
- MMD用WAVの入力元は元音声ファイルであること
- B7ではffprobe再検査を行わず、B6で保持済みの AudioProbeResult を利用すること
- B8ではBusy / worker / cancel / 300秒確認へ進むこと
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
5. MMD用WAV仕様
6. MMD用WAV出力core
7. ffmpeg runner拡張
8. GUI導線
9. 保存ダイアログ
10. 上書き確認
11. 入力元とffprobe再検査の扱い
12. 失敗時cleanup
13. 実行したテスト
14. 実行していないテスト
15. 変更していないファイル
16. .gitignoreを変更していないこと
17. 禁止事項の遵守
18. B8への引き継ぎ
19. B9への引き継ぎ
20. 未解決・要確認事項
```

---

## 15. 完了報告テンプレート

Codexは、完了時に以下の形式で報告する。

```text
MS17-B7 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 変更したファイル
- src/core/ffmpeg_runner.py:
- src/core/audio_errors.py:
- src/gui_wx/main_frame.py:
- src/gui_wx/app_controller.py:
- src/gui_wx/ui_state.py:
- docs/repo_milestone.md:
- docs/Version_Control.md:

4. 追加したファイル
- src/core/mmd_wav_export.py:
- tests/test_ms17_b7_mmd_wav_export.py:
- tests/test_ms17_b7_mmd_wav_save_dialog.py:
- tests/test_ms17_b7_mmd_wav_button_state.py:
- tests/test_ms17_b7_mmd_wav_failure_cleanup.py:
- tests/test_ms17_b7_mmd_wav_overwrite_confirm.py:

5. MMD用WAV仕様
- codec:
- sample rate:
- channels:
- container:
- 解析用WAVとの差分:

6. MMD用WAV出力core
- MmdWavSpec:
- MmdWavExportResult:
- export_mmd_wav:
- 一時ファイル経由:
- source_path:
- output_path:

7. ffmpeg runner拡張
- run_ffmpeg_mmd_wav:
- コマンド:
- -acodec pcm_s16le:
- -ar 44100:
- -ac 2:
- shell=True不使用:
- timeout:
- stderrの扱い:

8. GUI導線
- MMD用WAV出力ボタン:
- 配置:
- tooltip:
- 有効化条件:

9. 保存ダイアログ
- 初期ファイル名:
- filter:
- .wav補完:
- 保存先:

10. 上書き確認
- 同名ファイル検出:
- 確認ダイアログ:
- 承認時:
- キャンセル時:

11. 入力元とffprobe再検査の扱い
- 入力元:
- selected_audio_input:
- selected_audio_probe:
- ffprobe再検査:
- 元音声ファイル不存在時:

12. 失敗時cleanup
- 一時ファイル削除:
- source_path削除防止:
- analysis_wav_path削除防止:
- replace失敗:
- cleanup失敗:

13. 実行したテスト
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py:
- B3〜B6回帰テスト:
- 既存GUI回帰テスト:

14. 実行していないテスト
- 実ffmpegテスト:
- 全体pytest:
- 理由:

15. 変更していないファイル
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:

16. 禁止事項の確認
- VMD保存処理との連動出力:
- VMD保存処理変更:
- VMD出力対象変更:
- MMD用WAV複数プリセット:
- 音量正規化:
- 無音トリム:
- 自動フェード:
- 自動ノイズ除去:
- worker化:
- Busy完全統合:
- cancel UI:
- late callback破棄:
- 300秒確認ダイアログ:
- Qt / PySide6再導入:

17. B8への引き継ぎ
- 同期処理:
- Busy状態:
- worker化:
- cancel:
- late callback破棄:
- 300秒確認:
- ffmpeg process terminate / kill:

18. B9への引き継ぎ
- README更新:
- docs closeout:
- Release Package Manifest:
- MMD用WAV説明:
- 実MMD確認:

19. 未解決・要確認事項
- ...
```

## 15.1 実装後確認結果

2026-06-01時点のMS17-B7実装後確認結果。

```text
- B7関連pytest: 14 passed
- 関連回帰pytest: 25 passed
- 実FFmpeg出力確認: -bitexact 追加後にMMD用WAV検証通過
- 実FFmpeg出力chunk: RIFF/WAVE -> fmt(size 16) -> data
- ユーザー手動テスト: 問題なし
- git diff --check: 空白エラーなし（CRLF警告のみ）
```

実装後に確認した注意点。

```text
- FFmpeg標準のWAV出力では LIST chunk が混入する場合がある。
- MMD用WAVでは余分なchunkを含めない方針のため、run_ffmpeg_mmd_wav では -bitexact を指定する。
- 3ch以上の入力は ch1/ch2 のみを pan filter で stereo 出力する。
- mono入力は ch1 を L/R に複製する。
- MMD用WAV出力失敗時も、既存の解析結果・Preview・VMD保存可能状態は無効化しない。
```

---

## 16. MS17-B8への引き継ぎ条件

MS17-B8へ進む場合、B7から以下を引き継ぐ。

```text
- B7ではMMD用WAV出力を同期処理で実装していること
- B7ではworker化していないこと
- B7ではBusy状態の完全統合をしていないこと
- B7ではcancel UIを実装していないこと
- B7ではlate callback破棄を実装していないこと
- B7では300秒確認ダイアログを実装していないこと
- MMD用WAV出力もffmpeg実行を伴うため、長時間化する可能性があること
- ffmpeg process の terminate / kill 方針はB8で扱うこと
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
- MMD用WAV出力中Busy状態
- 300秒確認ダイアログ
- cancel要求
- ffmpeg / ffprobe terminate / kill
- Whisperなど即時停止できない処理の late callback 破棄
- 古いworker結果を現在結果として扱わない
- TEXT / 音声 / パラメータ変更時の無効化
```

---

## 17. MS17-B9への引き継ぎ条件

MS17-B9へ進む場合、B7から以下を引き継ぐ。

```text
- MMD用WAV出力が専用ボタン導線で実装されていること
- VMD保存処理との連動出力ではないこと
- READMEでは、実装済み導線を正確に説明する必要があること
- docsでは、解析用WAVとMMD用WAVの違いを明確に記録する必要があること
- Release Package Manifestでは、MMD用WAVはユーザー生成出力物であり、配布物ではないことを整理する必要があること
- B9で、実MMD環境でのWAV読み込み手動確認を検討すること
```

B9で扱う候補。

```text
- README更新
- repo_milestone更新
- Version_Control更新
- MS17 Block Breakdown更新
- MMD_Audio_WAV_Compatibility_Specification更新
- Error_Handling_Specification更新
- Release Package Manifest更新
- 実MMDでのMMD用WAV読み込み確認
- wav / mp3 / m4a 入力からVMD生成までの統合確認
- MS17 closeout
```
