# MS17-B4 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B4
- Block name: ffprobe検査 + 入力制限 + エラー分類基盤
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B4_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Google Antigravity
- Coding AI: Gemini 3.1 Pro
- Shell: Windows PowerShell
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作業種別: 実装
- 実装変更: あり
- GUI大規模変更: 禁止
- 実 ffprobe 必須テスト: なし
- 標準テスト方式: mock / fake runner
- 入力ファイルサイズ上限: 500 MiB = `500 * 1024 * 1024` bytes
- 音声長上限: 15分 = `900.0` sec

---

## 2. 背景

MS17-B3では、FFmpeg / ffprobe locator と入力音声種別判定基盤を追加した。

B3で追加済みの主な前提は以下。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
````

B3の責務は、以下に限定されていた。

```text
- ffmpeg.exe / ffprobe.exe の探索
- repo直下 FFmpeg\bin → bundled sys._MEIPASS\FFmpeg → PATH fallback の探索順
- 入力音声 .wav / .mp3 / .m4a の拡張子判定
- 未対応拡張子拒否
- 既存WAV経路の互換維持
```

B3では、以下は意図的に未実装である。

```text
- ffprobe実行
- ffprobe version取得
- 入力音声のduration / codec / stream検査
- 入力ファイルサイズ上限 500 MiB
- 音声長上限 15分
- ffmpeg変換
- 解析用WAV生成
- MMD用WAV出力
- GUI導線統合
```

MS17-B4では、B3の locator と audio_input を前提に、ffprobeを用いた入力音声検査と、MS17全体で必要になる音声変換系エラー分類の基盤を追加する。

ただし、B4でも ffmpeg変換、解析用WAV生成、MMD用WAV出力は行わない。

---

## 3. 目的

MS17-B4の目的は、入力音声ファイルを解析・変換へ進めてよいかを判定するための検査基盤を作ることである。

具体的には、以下を達成する。

1. B3で追加した `ffmpeg_locator.py` の結果を利用し、`ffprobe.exe` の実体パスを取得する。
2. `ffprobe.exe` を実行する最小ラッパーを追加する。
3. `ffprobe` のJSON出力を安全にparseする。
4. 入力音声に音声streamが存在するか確認する。
5. 入力音声のdurationを取得する。
6. codec / sample rate / channel count などの基本情報を保持する。
7. 入力ファイルサイズ上限 500 MiB を実装する。
8. 音声長上限 15分を実装する。
9. ffprobe未検出、ffprobe失敗、timeout、JSON parse失敗、音声streamなし、非対応形式、壊れたファイル等を分類できるようにする。
10. GUIで表示しやすいユーザー向けエラーメッセージを用意する。
11. B5以降の解析用WAV生成へ渡せる `AudioProbeResult` を定義する。
12. 実 ffprobe に依存しない mock / fake runner ベースのテストで検証できるようにする。

---

## 4. In Scope

MS17-B4で行う作業は以下に限定する。

### 4.1 音声エラー分類基盤

`src/core/audio_errors.py` を追加する。

責務は以下。

```text
- 音声入力・ffprobe検査・入力制限に関するエラー種別を定義する
- 内部向け error code を持つ
- ユーザー向け message を持つ
- GUI表示に使える短い説明を持つ
- 例外または結果型から参照できる構造にする
```

想定するエラー分類。

```text
audio_file_not_found
audio_path_is_directory
audio_file_too_large
unsupported_audio_extension
ffprobe_not_found
ffprobe_permission_error
ffprobe_timeout
ffprobe_execution_failed
ffprobe_invalid_json
audio_stream_not_found
audio_duration_missing
audio_duration_too_long
audio_probe_failed
```

必要に応じて、将来拡張用に以下を残してよい。

```text
audio_codec_unsupported
audio_sample_rate_unsupported
audio_channel_unsupported
```

ただし、B4で codec / sample rate / channel を強く拒否するかどうかは慎重に扱う。
B4の中心は、まず「読める音声か」「長すぎないか」「音声streamがあるか」を判定することである。

### 4.2 ffprobe runner

`src/core/ffprobe_runner.py` を追加する。

責務は以下。

```text
- ffprobe.exe を subprocess で実行する
- JSON出力を取得する
- timeoutを扱う
- returncode失敗を扱う
- stderrを安全に扱う
- permission errorを分類する
- 実行結果を dataclass で返す
```

想定コマンド。

```powershell
ffprobe.exe -v error -print_format json -show_format -show_streams <input_path>
```

Python上の想定引数。

```python
[
    str(ffprobe_path),
    "-v", "error",
    "-print_format", "json",
    "-show_format",
    "-show_streams",
    str(input_path),
]
```

実装上の注意。

```text
- shell=True を使わない
- コマンドは list[str] で渡す
- stderr は長すぎる場合に備えて切り詰める
- ユーザー向けmessageに生stderrをそのまま出さない
- timeout秒数を引数で指定できるようにする
- B4では terminate / kill の詳細統合は最小限に留める
- 長時間処理確認ダイアログはB8へ送る
```

標準timeout候補。

```text
timeout_sec = 30.0
```

B4では30秒を初期値とする。
ただし、これは300秒確認ダイアログとは別物である。

### 4.3 audio probe

`src/core/audio_probe.py` を追加する。

責務は以下。

```text
- 入力音声ファイルの存在確認
- ディレクトリ誤指定の拒否
- ファイルサイズ上限 500 MiB の検査
- ffprobe runner の呼び出し
- ffprobe JSON のparse
- 音声stream抽出
- duration取得
- 音声長上限 15分の検査
- AudioProbeResult の返却
```

想定する定数。

```python
MAX_AUDIO_FILE_SIZE_BYTES = 500 * 1024 * 1024
MAX_AUDIO_DURATION_SEC = 15 * 60.0
DEFAULT_FFPROBE_TIMEOUT_SEC = 30.0
```

想定する結果構造。

```python
@dataclass(frozen=True)
class AudioStreamInfo:
    codec_name: str | None
    sample_rate_hz: int | None
    channel_count: int | None
    duration_sec: float | None

@dataclass(frozen=True)
class AudioProbeResult:
    source_path: Path
    file_size_bytes: int
    duration_sec: float
    format_name: str | None
    audio_stream: AudioStreamInfo
```

B4では、`AudioProbeResult` は入力音声の検査結果であり、解析用WAVではない。

### 4.4 B3成果との接続

B4では、B3で追加した以下を利用する。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
```

利用方針。

```text
- audio_input.py の .wav / .mp3 / .m4a 種別判定を前提にする
- ffmpeg_locator.py の ffprobe path 探索結果を前提にする
- ffprobe path が not_found の場合は ffprobe_not_found として分類する
```

ただし、B4では GUI導線へ本格統合しない。
既存WAV経路の `selected_wav_path` / `selected_wav_analysis` は変更しない。

### 4.5 mock / fake runner テスト

B4の標準テストは、実 `ffprobe.exe` に依存させない。

標準テスト方針。

```text
- ffprobe runner 単体は subprocess.run を mock する
- audio_probe は fake runner / injected runner で検証する
- 実 ffprobe.exe がなくてもテストが通る
- 実 ffprobe.exe を使う統合確認はB9または任意手動確認へ送る
```

---

## 5. Out of Scope

MS17-B4では以下を行わない。

```text
- ffmpeg変換
- 解析用WAV生成
- MMD用WAV生成
- MMD用WAV保存導線
- GUIファイル選択dialogの本格拡張
- GUI文言の大規模変更
- mp3 / m4a の波形表示接続
- 解析用WAVを既存解析処理へ接続すること
- VMD保存処理の変更
- Whisper入力の変更
- 音量正規化
- 無音トリム
- 自動フェード
- 自動ノイズ除去
- ピッチ補正
- テンポ補正
- 300秒確認ダイアログ
- ffmpeg / ffprobe の長時間処理確認UI
- 完全なキャンセルUI
- FFmpeg / ffprobe 自動ダウンロード
- FFmpegバイナリのrepo追加
- README本文更新
- NOTICE本文更新
- THIRD_PARTY_LICENSES本文更新
- Release Package Manifest本文更新
- build.ps1変更
- MMD_AutoLipTool.spec変更
- .gitignore作成・変更
- Qt / PySide6 系の再導入
- 旧 src/gui 系の復活
```

---

## 6. 前提条件

MS17-B4は、以下を前提とする。

```text
- 作業branchは feature/MS17 である
- MS17-B1 が完了済みである
- MS17-B2 が完了済みである
- MS17-B3 が完了済みである
- src/core/ffmpeg_locator.py が存在する
- src/core/audio_input.py が存在する
- tests/test_ms17_b3_ffmpeg_locator.py が存在する
- tests/test_ms17_b3_audio_input_foundation.py が存在する
```

B3から引き継ぐ仕様。

```text
- ffmpeg / ffprobe の探索順は repo直下 FFmpeg\bin → bundled sys._MEIPASS\FFmpeg → PATH fallback
- PATHはfallback扱い
- .wav / .mp3 / .m4a は入力音声種別として認識済み
- mp3 / m4a はまだ完全対応ではない
- ffmpeg / ffprobe はB3では実行していない
```

B4で固定する仕様。

```text
- 入力ファイルサイズ上限は 500 MiB = 500 * 1024 * 1024 bytes
- 音声長上限は 15分 = 900.0 sec
- 実 ffprobe.exe を使うテストは必須にしない
- 標準テストは mock / fake runner で行う
```

---

## 7. 対象ファイル

MS17-B4で追加する候補。

```text
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b4_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py
```

MS17-B4で必要に応じて確認・最小変更する候補。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
docs/repo_milestone.md
docs/Version_Control.md
```

原則として変更しないファイル。

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
.gitignore
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
```

ただし、`src/gui_wx/` 側は、B4でエラー表示の接続が必要と判断した場合でも大規模変更は避ける。
B4では core 層の検査・分類基盤を優先し、GUI本格統合はB6またはB8へ送る。

---

## 8. 実装方針

### 8.1 全体方針

MS17-B4では、入力音声を後続処理へ進められるか検査する core 層を作る。

基本方針。

```text
- 実装中心は core 層
- GUI統合は最小限または未実施
- 実 ffprobe 必須テストは行わない
- mock / fake runner で動作を固定する
- 既存WAV経路を壊さない
- B4では解析用WAVを生成しない
- B4ではMMD用WAVを扱わない
```

### 8.2 エラー設計

`audio_errors.py` では、ユーザー向け表示と内部分類を分ける。

想定構造。

```python
from dataclasses import dataclass
from enum import Enum

class AudioErrorCode(str, Enum):
    AUDIO_FILE_NOT_FOUND = "audio_file_not_found"
    AUDIO_PATH_IS_DIRECTORY = "audio_path_is_directory"
    AUDIO_FILE_TOO_LARGE = "audio_file_too_large"
    UNSUPPORTED_AUDIO_EXTENSION = "unsupported_audio_extension"
    FFPROBE_NOT_FOUND = "ffprobe_not_found"
    FFPROBE_PERMISSION_ERROR = "ffprobe_permission_error"
    FFPROBE_TIMEOUT = "ffprobe_timeout"
    FFPROBE_EXECUTION_FAILED = "ffprobe_execution_failed"
    FFPROBE_INVALID_JSON = "ffprobe_invalid_json"
    AUDIO_STREAM_NOT_FOUND = "audio_stream_not_found"
    AUDIO_DURATION_MISSING = "audio_duration_missing"
    AUDIO_DURATION_TOO_LONG = "audio_duration_too_long"
    AUDIO_PROBE_FAILED = "audio_probe_failed"

@dataclass(frozen=True)
class AudioErrorInfo:
    code: AudioErrorCode
    message: str
    detail: str | None = None
```

例外を使う場合。

```python
class AudioProbeError(Exception):
    def __init__(self, info: AudioErrorInfo):
        self.info = info
        super().__init__(info.message)
```

注意。

```text
- message はユーザー向けに短くする
- detail はログ・開発者向けにする
- stderr全文をmessageへ入れない
- 技術詳細をGUIへ過剰表示しない
```

### 8.3 ffprobe runner 設計

`ffprobe_runner.py` では、ffprobe実行だけを担当する。

想定構造。

```python
@dataclass(frozen=True)
class FfprobeRunResult:
    stdout: str
    stderr: str
    returncode: int
```

関数候補。

```python
def run_ffprobe_json(
    ffprobe_path: Path,
    input_path: Path,
    timeout_sec: float = DEFAULT_FFPROBE_TIMEOUT_SEC,
) -> FfprobeRunResult:
    ...
```

責務。

```text
- subprocess.run を呼ぶ
- stdout / stderr を capture する
- timeout を指定する
- returncode != 0 を分類する
- FileNotFoundError / PermissionError / TimeoutExpired を分類する
```

コマンド。

```python
[
    str(ffprobe_path),
    "-v", "error",
    "-print_format", "json",
    "-show_format",
    "-show_streams",
    str(input_path),
]
```

禁止。

```text
- shell=True
- ffmpeg.exe の実行
- 解析用WAV生成
- GUI表示
```

### 8.4 audio probe 設計

`audio_probe.py` では、入力音声の検査とJSON parseを担当する。

関数候補。

```python
def probe_audio_file(
    input_path: str | Path,
    ffprobe_path: str | Path,
    *,
    runner: Callable[..., FfprobeRunResult] | None = None,
    timeout_sec: float = DEFAULT_FFPROBE_TIMEOUT_SEC,
) -> AudioProbeResult:
    ...
```

責務。

```text
1. pathをPathへ変換
2. 存在確認
3. ディレクトリ拒否
4. ファイルサイズ取得
5. 500 MiB超過拒否
6. 拡張子判定
7. ffprobe runner実行
8. JSON parse
9. streamsから audio stream を抽出
10. duration取得
11. 15分超過拒否
12. AudioProbeResultを返す
```

duration取得方針。

```text
優先1: format.duration
優先2: audio stream duration
```

durationが取得できない場合。

```text
audio_duration_missing
```

音声streamがない場合。

```text
audio_stream_not_found
```

sample rate / channel count の扱い。

```text
- 取得できる場合は保持する
- B4では原則として拒否条件にしない
- 互換WAV仕様への変換はB5/B7で扱う
```

codec の扱い。

```text
- 取得できる場合は保持する
- B4では codec だけで強い拒否はしない
- ffprobeで音声streamとして読めることを優先する
```

### 8.5 ファイルサイズ上限

B4では、入力ファイルサイズ上限を以下に固定する。

```python
MAX_AUDIO_FILE_SIZE_BYTES = 500 * 1024 * 1024
```

ユーザー向け表示では「約500MB」または「500 MiB相当」としてよい。

判定。

```text
file_size_bytes > MAX_AUDIO_FILE_SIZE_BYTES なら拒否
file_size_bytes == MAX_AUDIO_FILE_SIZE_BYTES は許可
```

### 8.6 音声長上限

B4では、音声長上限を以下に固定する。

```python
MAX_AUDIO_DURATION_SEC = 15 * 60.0
```

判定。

```text
duration_sec > 900.0 なら拒否
duration_sec == 900.0 は許可
```

300秒確認ダイアログとは別仕様である。

```text
- 900秒上限: B4の入力制限
- 300秒確認: B8の長時間処理確認UI
```

B4で300秒確認ダイアログを実装してはならない。

### 8.7 locatorとの接続

B4では、`ffmpeg_locator.py` の `locate_ffmpeg_tools()` を利用できる。

ただし、B4の core テストでは実環境に依存しないよう、`ffprobe_path` を直接注入できる設計を優先する。

方針。

```text
- audio_probe本体は ffprobe_path を受け取れるようにする
- locatorを呼ぶ高レベルhelperを追加する場合もよい
- ただしテストは fake path / fake runner で成立させる
```

高レベルhelper候補。

```python
def probe_audio_file_with_locator(
    input_path: str | Path,
    *,
    project_root: Path | None = None,
    meipass_root: Path | None = None,
    path_env: str | None = None,
) -> AudioProbeResult:
    ...
```

この helper を追加する場合も、実 ffprobe 必須テストにはしない。

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
- MS17-B3完了commitまたは記録があるか
- B4開始前に意図しない差分がないか
```

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。

### Step 2: B3成果確認

以下を確認する。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
docs/repo_milestone.md
docs/Version_Control.md
```

確認観点。

```text
- ffmpeg / ffprobe locator が存在するか
- ffprobe path の探索結果を利用できるか
- audio_input の .wav / .mp3 / .m4a 判定が存在するか
- B3で ffmpeg / ffprobe を実行していないことが記録されているか
- B4へ進む記録があるか
```

### Step 3: `src/core/audio_errors.py` 追加

`src/core/audio_errors.py` を追加する。

最低限含めるもの。

```text
AudioErrorCode
AudioErrorInfo
AudioProbeError
```

必要に応じて、以下のhelperを追加してよい。

```python
def make_audio_error(
    code: AudioErrorCode,
    message: str,
    detail: str | None = None,
) -> AudioProbeError:
    ...
```

### Step 4: `src/core/ffprobe_runner.py` 追加

`src/core/ffprobe_runner.py` を追加する。

最低限含めるもの。

```text
FfprobeRunResult
run_ffprobe_json
```

実装内容。

```text
- subprocess.runを使用
- shell=True禁止
- stdout/stderr capture
- timeout指定
- returncode失敗時に AudioProbeError
- FileNotFoundError を ffprobe_not_found
- PermissionError を ffprobe_permission_error
- subprocess.TimeoutExpired を ffprobe_timeout
```

### Step 5: `src/core/audio_probe.py` 追加

`src/core/audio_probe.py` を追加する。

最低限含めるもの。

```text
MAX_AUDIO_FILE_SIZE_BYTES
MAX_AUDIO_DURATION_SEC
DEFAULT_FFPROBE_TIMEOUT_SEC
AudioStreamInfo
AudioProbeResult
probe_audio_file
```

実装内容。

```text
- path存在確認
- directory拒否
- file size確認
- 500 MiB超過拒否
- audio_inputによる拡張子判定
- ffprobe runner 実行
- JSON parse
- audio stream抽出
- duration抽出
- 15分超過拒否
- AudioProbeResult返却
```

### Step 6: `tests/test_ms17_b4_ffprobe_runner.py` 追加

`ffprobe_runner` のテストを追加する。

標準テストは `subprocess.run` の mock を使う。

テスト観点。

```text
- 正常時にstdout/stderr/returncodeが返る
- 実行コマンドが shell=True ではない
- ffprobe引数が期待通り
- returncode != 0 で ffprobe_execution_failed
- FileNotFoundError で ffprobe_not_found
- PermissionError で ffprobe_permission_error
- TimeoutExpired で ffprobe_timeout
```

### Step 7: `tests/test_ms17_b4_audio_probe.py` 追加

`audio_probe` のテストを追加する。

実 ffprobe は使わず、fake runner を注入する。

テスト観点。

```text
- 正常なffprobe JSONから AudioProbeResult が作られる
- format.duration が使われる
- format.duration がない場合 audio stream duration が使われる
- audio stream がない場合 audio_stream_not_found
- duration が取れない場合 audio_duration_missing
- duration > 900.0 で audio_duration_too_long
- duration == 900.0 は許可
- invalid JSON で ffprobe_invalid_json
- codec_name / sample_rate / channels が保持される
```

### Step 8: `tests/test_ms17_b4_audio_input_limits.py` 追加

入力制限のテストを追加する。

テスト観点。

```text
- 存在しないファイルは audio_file_not_found
- ディレクトリは audio_path_is_directory
- 500 MiB超過は audio_file_too_large
- 500 MiBちょうどは許可
- 未対応拡張子は unsupported_audio_extension
```

大容量ファイルテストは、実際に巨大ファイルを作らない。

方針。

```text
- Path.stat を mock する
- または file size取得関数を切り出してmockする
```

### Step 9: B3テストの回帰確認

必要に応じてB3テストを再実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
```

### Step 10: B4限定テスト実行

以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
```

全体pytestは、既知のハング可能性がある場合は実行しない。

### Step 11: docs更新

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録内容。

```text
- MS17-B4を実施したこと
- audio_errors を追加したこと
- ffprobe_runner を追加したこと
- audio_probe を追加したこと
- 入力ファイルサイズ上限を 500 MiB としたこと
- 音声長上限を 15分としたこと
- 実 ffprobe 必須テストではなく mock / fake runner で検証したこと
- ffmpeg変換、解析用WAV生成、MMD用WAV出力は未実装であること
- B5では解析用WAV生成へ進むこと
```

README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは変更しない。

### Step 12: 完了前diff確認

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
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b4_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py
docs/repo_milestone.md
docs/Version_Control.md
```

以下に差分がないことを確認する。

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
.gitignore
```

---

## 10. 状態遷移 / データ契約

### 10.1 B4で追加するデータ契約

B4では、入力音声の検査結果として `AudioProbeResult` を追加する。

役割。

```text
AudioProbeResult:
- 入力音声ファイルのffprobe検査結果
- B5の解析用WAV生成判断に使う
- 波形表示・解析の正本ではない
- MMD用WAVではない
```

想定構造。

```text
source_path
file_size_bytes
duration_sec
format_name
audio_stream
```

`audio_stream` の想定内容。

```text
codec_name
sample_rate_hz
channel_count
duration_sec
```

### 10.2 B4で追加するエラー契約

B4では、入力音声検査の失敗を分類可能にする。

最低限の分類。

```text
audio_file_not_found
audio_path_is_directory
audio_file_too_large
unsupported_audio_extension
ffprobe_not_found
ffprobe_permission_error
ffprobe_timeout
ffprobe_execution_failed
ffprobe_invalid_json
audio_stream_not_found
audio_duration_missing
audio_duration_too_long
audio_probe_failed
```

### 10.3 B4で変更しない契約

以下はB4では変更しない。

```text
- selected_wav_path
- selected_wav_analysis
- current_timing_plan
- analysis_result_valid
- Preview shape contract
- VMD writer input
- 解析用WAV path
- MMD用WAV path
```

B4では、既存WAV読み込み経路を新しい `AudioProbeResult` に置き換えない。

### 10.4 B5以降へ送る契約

以下はB5以降で扱う。

```text
analysis_wav_path
analysis_wav_format
ffmpeg_conversion_result
temporary_file_path
conversion_cleanup_result
```

以下はB7以降で扱う。

```text
mmd_wav_output_path
mmd_wav_format
mmd_wav_validation_result
```

---

## 11. テスト方針

### 11.1 B4で実行する標準テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
```

### 11.2 B3回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
```

### 11.3 実 ffprobe テスト方針

実 `ffprobe.exe` を使うテストは必須にしない。

理由。

```text
- 開発環境にFFmpegが存在しない場合でもB4のテストを成立させるため
- GitHub Actionsや別Windows環境での環境差を避けるため
- B4の主目的はrunner / parser / classifierの基盤固定であるため
```

任意テストを追加する場合は、以下の条件を満たすこと。

```text
- FFmpeg\bin\ffprobe.exe が存在する場合のみ実行
- 存在しない場合は skip
- B4完了条件には含めない
```

ただし、初期B4では任意実ffprobeテストも追加しない方針を推奨する。

### 11.4 全体pytest

全体pytestは、既知のハング可能性がある場合は実行しない。

実行しない場合は、完了報告に理由を書く。

---

## 12. 受け入れ条件

MS17-B4は、以下を満たしたら完了とする。

### 12.1 実装条件

* `src/core/audio_errors.py` が追加されている。
* `src/core/ffprobe_runner.py` が追加されている。
* `src/core/audio_probe.py` が追加されている。
* ffprobe実行ラッパーが実装されている。
* ffprobe JSON parseが実装されている。
* 音声stream抽出が実装されている。
* duration取得が実装されている。
* 入力ファイルサイズ上限 500 MiB が実装されている。
* 音声長上限 15分が実装されている。
* ffprobe未検出、permission error、timeout、実行失敗、JSON不正、音声streamなし、duration欠落、duration超過が分類できる。
* GUI表示に使えるユーザー向けエラーメッセージが用意されている。
* B3の `ffmpeg_locator.py` / `audio_input.py` と矛盾していない。

### 12.2 禁止事項遵守

以下が守られている。

```text
- ffmpeg変換をしていない
- 解析用WAV生成をしていない
- MMD用WAV出力をしていない
- GUI導線統合を完成扱いしていない
- mp3 / m4a 完全対応扱いしていない
- 300秒確認ダイアログを実装していない
- READMEを変更していない
- NOTICEを変更していない
- THIRD_PARTY_LICENSES.mdを変更していない
- Release Package Manifestを変更していない
- build.ps1を変更していない
- MMD_AutoLipTool.specを変更していない
- .gitignoreを変更していない
- Qt / PySide6を再導入していない
```

### 12.3 テスト条件

以下が成功している。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
```

実 ffprobe.exe がなくてもテストが成功する。

全体pytestを実行しなかった場合は、その理由が報告されている。

### 12.4 docs条件

以下が必要最小限で更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録上、B4の範囲が以下として明確である。

```text
- ffprobe検査基盤
- 入力ファイルサイズ上限 500 MiB
- 音声長上限 15分
- エラー分類基盤
- mock / fake runner中心の検証
- ffmpeg変換なし
- 解析用WAV生成なし
- MMD用WAV出力なし
```

---

## 13. リスクと対策

### Risk 1: 実 ffprobe 依存でテストが不安定になる

対策。

```text
- 標準テストは mock / fake runner にする
- 実 ffprobe 必須テストを入れない
- 実体確認はB9統合確認または任意手動確認へ送る
```

### Risk 2: B4でffmpeg変換まで進んでしまう

対策。

```text
- B4はffprobe検査まで
- ffmpeg_runner / audio_convert はB5へ送る
- 解析用WAV生成をB4に含めない
```

### Risk 3: codec / sample rate を早期に拒否しすぎる

対策。

```text
- B4ではffprobeで読める音声streamを検出することを優先
- codec / sample rate / channels は保持する
- 変換仕様やMMD互換WAV仕様はB5/B7で判断する
```

### Risk 4: 500MB表記とbytes実装が曖昧になる

対策。

```text
- 実装は 500 MiB = 500 * 1024 * 1024 bytes と明記
- ユーザー向け表示では約500MBと表現してもよい
- テストでは境界値を確認する
```

### Risk 5: 15分上限と300秒確認を混同する

対策。

```text
- 15分上限はB4の入力制限
- 300秒確認はB8の長時間処理確認
- B4で300秒確認ダイアログを実装しない
```

### Risk 6: GUI統合が先行しすぎる

対策。

```text
- B4ではcore層の検査・分類を優先
- GUI表示はユーザー向けmessageを用意するまで
- ファイル選択dialog拡張やエラー表示統合はB6/B8で扱う
```

### Risk 7: 既存WAV経路を壊す

対策。

```text
- selected_wav_path / selected_wav_analysis を変更しない
- audio_processing.py の既存WAV解析を置き換えない
- B4は新規probe基盤として追加する
```

---

## 14. Antigravity 実装時の注意

以下のプロンプトを Antigravity に渡して実施する。

```text
今回は MS17-B4 です。

目的:
ffprobe検査 + 入力制限 + エラー分類基盤を実装してください。

重要:
- 対象branchは feature/MS17 です。
- MS17-B3の成果を前提にしてください。
- 実 ffprobe.exe を使うテストは必須にしないでください。
- 標準テストは mock / fake runner で行ってください。
- 入力ファイルサイズ上限は 500 MiB = 500 * 1024 * 1024 bytes としてください。
- 音声長上限は 15分 = 900.0 sec としてください。
- ffmpeg変換は行わないでください。
- 解析用WAV生成は行わないでください。
- MMD用WAV出力は行わないでください。
- 300秒確認ダイアログは実装しないでください。
- GUIファイル選択dialogの本格拡張は行わないでください。
- README / NOTICE / THIRD_PARTY_LICENSES.md / Release Package Manifest は変更しないでください。
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

src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
docs/repo_milestone.md
docs/Version_Control.md

実装対象:

src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b4_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py

実装内容:

1. src/core/audio_errors.py を追加してください。
   - AudioErrorCode を定義してください。
   - AudioErrorInfo を定義してください。
   - AudioProbeError を定義してください。
   - ffprobe未検出、permission error、timeout、実行失敗、JSON不正、音声streamなし、duration欠落、duration超過、ファイルサイズ超過などを分類できるようにしてください。
   - ユーザー向けmessageと開発者向けdetailを分けてください。

2. src/core/ffprobe_runner.py を追加してください。
   - ffprobe.exe を subprocess.run で実行するラッパーを実装してください。
   - shell=True は使わないでください。
   - コマンドは list[str] で渡してください。
   - stdout / stderr をcaptureしてください。
   - timeoutを扱ってください。
   - returncode失敗を分類してください。
   - FileNotFoundError / PermissionError / TimeoutExpired を分類してください。
   - ffmpeg.exe は実行しないでください。
   - 解析用WAV生成はしないでください。

3. src/core/audio_probe.py を追加してください。
   - MAX_AUDIO_FILE_SIZE_BYTES = 500 * 1024 * 1024
   - MAX_AUDIO_DURATION_SEC = 15 * 60.0
   - DEFAULT_FFPROBE_TIMEOUT_SEC = 30.0
   を定義してください。
   - AudioStreamInfo を定義してください。
   - AudioProbeResult を定義してください。
   - probe_audio_file を実装してください。
   - 入力パス存在確認、ディレクトリ拒否、500 MiB超過拒否、拡張子判定、ffprobe JSON parse、音声stream抽出、duration取得、15分超過拒否を行ってください。
   - durationは format.duration を優先し、なければ audio stream duration を使ってください。
   - durationが取れない場合は audio_duration_missing にしてください。
   - 音声streamがない場合は audio_stream_not_found にしてください。

4. tests/test_ms17_b4_ffprobe_runner.py を追加してください。
   - subprocess.run を mock してください。
   - 正常系、returncode失敗、FileNotFoundError、PermissionError、TimeoutExpired を確認してください。
   - shell=True を使っていないことを確認してください。

5. tests/test_ms17_b4_audio_probe.py を追加してください。
   - 実 ffprobe.exe は使わず fake runner を注入してください。
   - 正常なJSON、音声streamなし、duration欠落、duration超過、invalid JSON を確認してください。
   - codec_name / sample_rate / channels が保持されることを確認してください。

6. tests/test_ms17_b4_audio_input_limits.py を追加してください。
   - 存在しないファイル
   - ディレクトリ
   - 500 MiB超過
   - 500 MiBちょうど
   - 未対応拡張子
   を確認してください。
   - 巨大ファイルは実作成せず、statのmockなどで対応してください。

実行するテスト:

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py

必要に応じてB3回帰テストも実行してください。

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py

全体pytestは、ハング可能性がある場合は実行しないでください。

実装後、必要最小限で以下を更新してください。

docs/repo_milestone.md
docs/Version_Control.md

記録内容:
- MS17-B4を実施したこと
- audio_errors / ffprobe_runner / audio_probe を追加したこと
- 入力ファイルサイズ上限を 500 MiB としたこと
- 音声長上限を 15分としたこと
- 実 ffprobe必須テストではなく mock / fake runner で検証したこと
- ffmpeg変換、解析用WAV生成、MMD用WAV出力は未実装であること
- B5では解析用WAV生成へ進むこと

完了前に以下を確認してください。

git diff --stat
git diff --name-only
git diff -- .gitignore

.gitignoreに差分が出ている場合は、ユーザー側管理対象なので元に戻して報告してください。

完了報告では、以下を必ず分けてください。

1. 確認したbranch / commit
2. 作業前の状態
3. 追加したファイル
4. 変更したファイル
5. 実装したエラー分類
6. 実装したffprobe runner仕様
7. 実装したaudio probe仕様
8. 入力制限
9. 実行したテスト
10. 実行していないテスト
11. 変更していないファイル
12. .gitignoreを変更していないこと
13. 禁止事項の遵守
14. B5への引き継ぎ
15. 未解決・要確認事項
```

---

## 15. 完了報告テンプレート

Antigravityは、完了時に以下の形式で報告する。

```text
MS17-B4 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 追加したファイル
- src/core/audio_errors.py:
- src/core/ffprobe_runner.py:
- src/core/audio_probe.py:
- tests/test_ms17_b4_ffprobe_runner.py:
- tests/test_ms17_b4_audio_probe.py:
- tests/test_ms17_b4_audio_input_limits.py:

4. 変更したファイル
- docs/repo_milestone.md:
- docs/Version_Control.md:

5. 実装したエラー分類
- audio_file_not_found:
- audio_path_is_directory:
- audio_file_too_large:
- unsupported_audio_extension:
- ffprobe_not_found:
- ffprobe_permission_error:
- ffprobe_timeout:
- ffprobe_execution_failed:
- ffprobe_invalid_json:
- audio_stream_not_found:
- audio_duration_missing:
- audio_duration_too_long:
- audio_probe_failed:

6. 実装したffprobe runner仕様
- コマンド:
- shell=True不使用:
- stdout/stderr capture:
- timeout:
- returncode失敗:
- permission error:
- timeout error:
- stderrの扱い:

7. 実装したaudio probe仕様
- file存在確認:
- directory拒否:
- file size確認:
- extension判定:
- ffprobe JSON parse:
- audio stream抽出:
- duration取得:
- codec/sample rate/channels保持:

8. 入力制限
- file size上限:
- duration上限:
- 500 MiB境界:
- 900秒境界:

9. 実行したテスト
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py:
- B3回帰テスト:

10. 実行していないテスト
- 実ffprobeテスト:
- 全体pytest:
- 理由:

11. 変更していないファイル
- README.md:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:
- src/gui_wx/:

12. 禁止事項の確認
- ffmpeg変換:
- 解析用WAV生成:
- MMD用WAV出力:
- 300秒確認ダイアログ:
- GUI本格統合:
- Qt / PySide6再導入:

13. B5への引き継ぎ
- ffprobe検査結果:
- AudioProbeResult:
- codec/sample rate/channel情報:
- ffmpeg変換へ渡す前提:
- 未解決事項:

14. 未解決・要確認事項
- ...
```

---

## 16. MS17-B5への引き継ぎ条件

MS17-B5へ進む場合、B4から以下を引き継ぐ。

```text
- AudioProbeResult の構造
- AudioStreamInfo の構造
- 入力ファイルサイズ上限 500 MiB
- 音声長上限 15分
- ffprobe runner のtimeout方針
- ffprobe JSON parse方針
- audio stream抽出方針
- duration取得方針
- エラー分類
- 実 ffprobe必須テストを避けたmock / fake runner方針
```

MS17-B5では、以下へ進む。

```text
MS17-B5: 解析用WAV生成基盤
```

B5で扱う候補。

```text
- ffmpeg runner
- ffmpeg path解決
- 解析用WAV出力先管理
- 一時ファイル命名
- 失敗時の不完全ファイル削除
- ffmpeg stderrの安全な扱い
- 既存WAV入力でも必要に応じた解析用WAV生成
- 解析用WAV仕様の確定
```

B5でも引き続き、以下を守る。

```text
- MMD用WAV出力はB7へ送る
- 300秒確認ダイアログはB8へ送る
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わない
- Qt / PySide6 は再導入しない
```
