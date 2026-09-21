# MS17-B5 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B5
- Block name: 解析用WAV生成基盤
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B5_Implementation_Plan.md`
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
- 実 ffmpeg 必須テスト: なし
- 標準テスト方式: mock / fake runner
- 解析用WAV仕様:
  - container: WAV
  - codec: PCM signed 16-bit little-endian
  - sample rate: 44100 Hz
  - channels: mono
- 解析用WAV保存先:
  - `cache/analysis_wav/`
- cache削除方針:
  - B5では自動削除しない
  - 変換失敗時の不完全ファイルのみ削除する
- 既存 `.wav` 入力:
  - 必ず解析用WAVへ変換する
- 解析用WAVファイル名規則:
  - 元ファイル名stem + 短いハッシュ + `_analysis.wav`
  - 例: `song_ab12cd34_analysis.wav`

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

- 実 ffprobe 必須テストは行わない
- 標準テストは mock / fake runner で行う
- ffprobe検査結果として AudioProbeResult を扱う
- ffmpeg変換、解析用WAV生成、MMD用WAV出力はまだ行わない
```

MS17-B5では、B3の locator と B4の probe / error分類を前提に、ffmpegを用いて入力音声から解析用WAVを生成する。

解析用WAVは、MS17以降の波形表示・解析・timing plan生成に使う内部正本である。
MMD用WAVとは役割を分ける。

---

## 3. 目的

MS17-B5の目的は、入力音声 `.wav` / `.mp3` / `.m4a` から、内部処理用の解析用WAVを生成する基盤を作ることである。

具体的には、以下を達成する。

1. B3で追加した `ffmpeg_locator.py` を利用し、`ffmpeg.exe` の実体パスを取得する。
2. B4で追加した `AudioProbeResult` を前提に、入力音声が検査済みであることを扱えるようにする。
3. `ffmpeg.exe` を実行する最小ラッパーを追加する。
4. 入力音声から解析用WAVを生成する。
5. 解析用WAV仕様を以下に固定する。

```text
container: WAV
codec: PCM signed 16-bit little-endian
sample rate: 44100 Hz
channels: mono
```

6. 解析用WAVを `cache/analysis_wav/` に保存する。
7. 既存 `.wav` 入力も必ず解析用WAVへ変換する。
8. 解析用WAVのファイル名を、元ファイル名stem + 短いハッシュ + `_analysis.wav` にする。
9. 変換失敗時に不完全ファイルを削除する。
10. ffmpeg未検出、permission error、timeout、実行失敗、不完全出力などを分類できるようにする。
11. B6以降で、解析用WAVを波形表示・解析・timing plan生成の正本として接続できる状態にする。
12. B5ではGUI本格統合を行わず、core層の変換基盤を固定する。

---

## 4. In Scope

MS17-B5で行う作業は以下に限定する。

### 4.1 ffmpeg runner の追加

`src/core/ffmpeg_runner.py` を追加する。

責務は以下。

```text
- ffmpeg.exe を subprocess で実行する
- 入力音声パスを受け取る
- 出力WAVパスを受け取る
- 解析用WAV仕様に変換する
- timeoutを扱う
- returncode失敗を扱う
- stderrを安全に扱う
- permission errorを分類する
- 変換失敗時に不完全ファイル削除のための情報を返す
```

想定コマンド。

```powershell
ffmpeg.exe -y -i <input_path> -vn -acodec pcm_s16le -ar 44100 -ac 1 <output_path>
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
    "-ac", "1",
    str(output_path),
]
```

実装上の注意。

```text
- shell=True を使わない
- コマンドは list[str] で渡す
- stderr は長すぎる場合に備えて切り詰める
- ユーザー向けmessageに生stderrをそのまま出さない
- timeout秒数を引数で指定できるようにする
- B5では長時間処理確認ダイアログを実装しない
- B5ではキャンセルUIを実装しない
- ffmpeg / ffprobe の自動ダウンロードは行わない
```

標準timeout候補。

```text
DEFAULT_FFMPEG_TIMEOUT_SEC = 300.0
```

これはB8の「300秒確認ダイアログ」とは異なる。
B5では内部timeout値として扱うだけで、確認ダイアログは実装しない。

### 4.2 解析用WAV生成基盤

`src/core/audio_convert.py` を追加する。

責務は以下。

```text
- 入力音声パスを受け取る
- AudioProbeResult を受け取る、または検査済み入力として扱う
- ffmpeg path を受け取る
- 解析用WAVの出力先を決める
- 解析用WAVファイル名を生成する
- ffmpeg_runner を呼び出す
- 変換成功時に AnalysisWavResult を返す
- 変換失敗時に不完全ファイルを削除する
```

想定する結果構造。

```python
@dataclass(frozen=True)
class AnalysisWavSpec:
    codec: str
    sample_rate_hz: int
    channel_count: int

@dataclass(frozen=True)
class AnalysisWavResult:
    source_path: Path
    analysis_wav_path: Path
    spec: AnalysisWavSpec
    duration_sec: float | None
    file_size_bytes: int | None
```

B5では、`duration_sec` は B4の `AudioProbeResult` から受け継いでもよい。
変換後WAVの再probeはB5必須にしない。
変換後WAVのMMD互換検証はB7へ送る。

### 4.3 解析用WAV保存先管理

`src/core/audio_cache.py` または `src/core/audio_temp_files.py` を追加する。

推奨ファイル名は以下。

```text
src/core/audio_cache.py
```

責務は以下。

```text
- cache/analysis_wav/ のパス解決
- 必要に応じたディレクトリ作成
- 解析用WAVファイル名生成
- 元ファイル名stemの安全化
- 短いハッシュ生成
- 不完全ファイル削除
```

保存先は以下。

```text
cache/analysis_wav/
```

基準ディレクトリは、原則としてアプリ実行基準または project root 基準とする。

B5での方針。

```text
- 開発時は repo直下 cache/analysis_wav/ を想定する
- 配布時はアプリ実行フォルダ配下 cache/analysis_wav/ を想定する
- B5ではOS一時ディレクトリを使わない
- B5ではcacheの自動削除を行わない
- 変換失敗時の不完全ファイルだけ削除する
```

注意。

```text
- cache/analysis_wav/ が作れない場合は明確なエラーにする
- 書き込み権限がない場合は明確なエラーにする
- .gitignore はユーザー側管理のため変更しない
```

### 4.4 ファイル名規則

解析用WAVのファイル名は以下にする。

```text
<safe_stem>_<hash8>_analysis.wav
```

例。

```text
song_ab12cd34_analysis.wav
```

方針。

```text
- safe_stem は元ファイル名stemをベースにする
- Windowsファイル名として危険な文字を置換する
- hash8 は元ファイルの絶対パス、サイズ、mtime等から作る
- hash8 は8文字程度の短い識別子にする
- 別フォルダの同名ファイルが衝突しないようにする
```

hash材料候補。

```text
- source path の絶対パス文字列
- file size
- mtime_ns
```

B5では、再利用キャッシュとしての厳密なキャッシュキー設計は行わない。
ただし、同名衝突を避けるための短いハッシュは生成する。

### 4.5 既存WAV入力の扱い

既存 `.wav` 入力も、B5では必ず解析用WAVへ変換する。

理由。

```text
- wav / mp3 / m4a の入力差をB5以降で吸収する
- 波形表示・解析・timing plan生成の正本を解析用WAVに統一しやすくする
- 既存WAVがPCM条件を満たすかどうかに依存しない
- MS17全体で「入力音声」と「解析用WAV」を明確に分離できる
```

ただし、B5ではGUIの既存WAV入力経路へ本格接続しない。
B6で、GUIから選ばれた `.wav` / `.mp3` / `.m4a` を解析用WAV生成へ接続する。

### 4.6 エラー分類の拡張

B4で追加した `audio_errors.py` を必要に応じて拡張する。

追加候補。

```text
ffmpeg_not_found
ffmpeg_permission_error
ffmpeg_timeout
ffmpeg_execution_failed
analysis_wav_output_failed
analysis_wav_cleanup_failed
analysis_wav_cache_dir_failed
analysis_wav_generation_failed
```

既存の ffprobe 系 error code と混同しない。

エラー設計方針。

```text
- ffprobe系とffmpeg系を区別する
- 変換失敗と出力先作成失敗を区別する
- ユーザー向けmessageと開発者向けdetailを分ける
- stderr全文をユーザー向けmessageへ直接入れない
```

### 4.7 テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_analysis_wav_generation.py
tests/test_ms17_b5_analysis_wav_cache.py
tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

標準テストでは、実 `ffmpeg.exe` を必須にしない。

テスト方針。

```text
- ffmpeg_runner は subprocess.run を mock する
- audio_convert は fake runner を注入する
- 巨大ファイルや実変換を必要としない
- cache/analysis_wav/ は tmp_path 上で再現する
- 不完全ファイル削除を確認する
```

---

## 5. Out of Scope

MS17-B5では以下を行わない。

```text
- GUIファイル選択dialogの本格拡張
- GUI文言の大規模変更
- mp3 / m4a をGUIから完全解析導線へ接続すること
- 解析用WAVを波形表示へ接続する完成実装
- 解析用WAVをWhisper / 解析処理へ接続する完成実装
- VMD保存処理の変更
- MMD用WAV生成
- MMD用WAV保存導線
- MMD互換WAV検証
- 変換キャッシュ再利用機能
- cache/analysis_wav/ の起動時自動削除
- cache/analysis_wav/ のアプリ終了時自動削除
- cache容量管理
- 音量正規化
- 無音トリム
- 自動フェード
- 自動ノイズ除去
- ピッチ補正
- テンポ補正
- 300秒確認ダイアログ
- 完全なキャンセルUI
- ffmpeg / ffprobe の自動ダウンロード
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

MS17-B5は、以下を前提とする。

```text
- 作業branchは feature/MS17 である
- MS17-B1 が完了済みである
- MS17-B2 が完了済みである
- MS17-B3 が完了済みである
- MS17-B4 が完了済みである
- src/core/ffmpeg_locator.py が存在する
- src/core/audio_input.py が存在する
- src/core/audio_errors.py が存在する
- src/core/ffprobe_runner.py が存在する
- src/core/audio_probe.py が存在する
```

B3から引き継ぐ仕様。

```text
- ffmpeg / ffprobe の探索順は repo直下 FFmpeg\bin → bundled sys._MEIPASS\FFmpeg → PATH fallback
- PATHはfallback扱い
- .wav / .mp3 / .m4a は入力音声種別として認識済み
```

B4から引き継ぐ仕様。

```text
- 入力ファイルサイズ上限は 500 MiB
- 音声長上限は 15分
- AudioProbeResult が存在する
- ffprobe検査とエラー分類基盤が存在する
```

B5で固定する仕様。

```text
- 解析用WAVは PCM signed 16-bit little-endian / 44100 Hz / mono
- 解析用WAVは cache/analysis_wav/ に保存する
- B5ではcacheの自動削除を行わない
- 変換失敗時の不完全ファイルのみ削除する
- 既存 .wav 入力も必ず解析用WAVへ変換する
- 解析用WAVファイル名は <safe_stem>_<hash8>_analysis.wav
- 実 ffmpeg.exe を使うテストは必須にしない
- 標準テストは mock / fake runner で行う
```

---

## 7. 対象ファイル

MS17-B5で追加する候補。

```text
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_analysis_wav_generation.py
tests/test_ms17_b5_analysis_wav_cache.py
tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

MS17-B5で必要に応じて最小変更する候補。

```text
src/core/audio_errors.py
docs/repo_milestone.md
docs/Version_Control.md
```

MS17-B5で確認するファイル。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
src/core/audio_probe.py
src/core/audio_errors.py
docs/repo_milestone.md
docs/Version_Control.md
docs/Implementation_Plan/MS17-B5_Implementation_Plan.md
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

ただし、`src/gui_wx/` 側はB5では原則変更しない。
GUI接続はB6以降へ送る。

---

## 8. 実装方針

### 8.1 全体方針

MS17-B5では、core層に解析用WAV生成基盤を追加する。

基本方針。

```text
- B5の中心は core 層
- GUI統合は行わない
- 実 ffmpeg 必須テストは行わない
- mock / fake runner で動作を固定する
- 既存WAV経路を壊さない
- 解析用WAVを内部正本として扱う準備をする
- MMD用WAVとは分離する
```

### 8.2 `ffmpeg_runner.py` 設計

`ffmpeg_runner.py` では、ffmpeg実行だけを担当する。

想定構造。

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class FfmpegRunResult:
    stdout: str
    stderr: str
    returncode: int
    output_path: Path
```

関数候補。

```python
def run_ffmpeg_analysis_wav(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> FfmpegRunResult:
    ...
```

責務。

```text
- subprocess.run を呼ぶ
- stdout / stderr を capture する
- timeout を指定する
- returncode != 0 を分類する
- FileNotFoundError / PermissionError / TimeoutExpired を分類する
- 出力先ディレクトリがない場合は呼び出し側で作成済みとする
```

コマンド。

```python
[
    str(ffmpeg_path),
    "-y",
    "-i", str(input_path),
    "-vn",
    "-acodec", "pcm_s16le",
    "-ar", "44100",
    "-ac", "1",
    str(output_path),
]
```

禁止。

```text
- shell=True
- GUI表示
- MMD用WAV生成
- 音量正規化
- 無音トリム
- 自動フェード
- 自動ノイズ除去
```

### 8.3 `audio_cache.py` 設計

`audio_cache.py` では、解析用WAVの保存先とファイル名生成を担当する。

想定定数。

```python
ANALYSIS_WAV_CACHE_DIR = Path("cache") / "analysis_wav"
ANALYSIS_WAV_SUFFIX = "_analysis.wav"
```

関数候補。

```python
def get_analysis_wav_cache_dir(base_dir: Path) -> Path:
    ...

def ensure_analysis_wav_cache_dir(base_dir: Path) -> Path:
    ...

def build_analysis_wav_filename(source_path: Path) -> str:
    ...

def build_analysis_wav_path(source_path: Path, cache_dir: Path) -> Path:
    ...

def cleanup_partial_file(path: Path) -> None:
    ...
```

safe stem方針。

```text
- 元ファイル名stemを使う
- Windowsで問題になりやすい文字を `_` に置換する
- 空になった場合は `audio` などのfallbackを使う
```

hash方針。

```text
- source path の絶対パス文字列
- file size
- mtime_ns
```

上記からSHA-256などでhashを作り、先頭8文字を使う。

例。

```text
song_ab12cd34_analysis.wav
```

### 8.4 `audio_convert.py` 設計

`audio_convert.py` では、解析用WAV生成の高レベル処理を担当する。

想定構造。

```python
@dataclass(frozen=True)
class AnalysisWavSpec:
    codec: str
    sample_rate_hz: int
    channel_count: int

@dataclass(frozen=True)
class AnalysisWavResult:
    source_path: Path
    analysis_wav_path: Path
    spec: AnalysisWavSpec
    duration_sec: float | None
    file_size_bytes: int | None
```

想定定数。

```python
ANALYSIS_WAV_SPEC = AnalysisWavSpec(
    codec="pcm_s16le",
    sample_rate_hz=44100,
    channel_count=1,
)
```

関数候補。

```python
def generate_analysis_wav(
    source_path: str | Path,
    ffmpeg_path: str | Path,
    *,
    probe_result: AudioProbeResult | None = None,
    base_dir: Path | None = None,
    runner: Callable[..., FfmpegRunResult] | None = None,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> AnalysisWavResult:
    ...
```

責務。

```text
1. source_pathをPathへ変換
2. ffmpeg_pathをPathへ変換
3. cache/analysis_wav/ を作成
4. 出力ファイル名を生成
5. 既存の同名出力がある場合は上書きまたは削除してから生成
6. ffmpeg runnerを呼ぶ
7. 成功時に出力ファイル存在を確認
8. 成功時にAnalysisWavResultを返す
9. 失敗時に不完全ファイルを削除する
10. 削除失敗時も情報を失わない
```

出力ファイルが作られなかった場合。

```text
analysis_wav_output_failed
```

変換失敗時の削除方針。

```text
- output_path が存在する場合は削除を試みる
- 削除に失敗した場合は analysis_wav_cleanup_failed として記録または例外化する
- 元のffmpeg失敗原因を失わないようにする
```

### 8.5 既存WAV入力の扱い

`.wav` 入力でも、B5では必ず解析用WAVを生成する。

想定。

```text
input.wav
→ cache/analysis_wav/input_ab12cd34_analysis.wav
```

理由。

```text
- 入力音声と解析用WAVを分離する
- 既存WAVの形式差を吸収する
- mp3 / m4a と同じ後続処理経路へ乗せやすくする
```

B5では既存GUI経路を置き換えないため、既存の `selected_wav_path` はそのまま維持される。
B6で、GUI上の入力音声から解析用WAV生成・波形表示・解析へ接続する。

### 8.6 エラー設計

`audio_errors.py` に必要な error code を追加する。

追加候補。

```text
ffmpeg_not_found
ffmpeg_permission_error
ffmpeg_timeout
ffmpeg_execution_failed
analysis_wav_cache_dir_failed
analysis_wav_output_failed
analysis_wav_cleanup_failed
analysis_wav_generation_failed
```

分類方針。

```text
- ffmpeg未検出とffprobe未検出を分ける
- ffmpeg実行失敗と解析用WAV出力失敗を分ける
- cacheディレクトリ作成失敗を分ける
- 不完全ファイル削除失敗を分ける
```

ユーザー向けmessage例。

```text
ffmpeg_not_found:
FFmpegが見つかりません。アプリに同梱されたFFmpeg、またはPATH上のFFmpegを確認してください。

ffmpeg_execution_failed:
音声ファイルの変換に失敗しました。入力音声が壊れているか、対応していない形式の可能性があります。

analysis_wav_cache_dir_failed:
解析用WAVの保存先フォルダを作成できませんでした。アプリの保存先権限を確認してください。
```

stderr全文は `detail` に保持してよいが、GUIのmessageに直接出さない。

### 8.7 docs更新方針

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録する内容。

```text
- MS17-B5を実施したこと
- ffmpeg_runnerを追加したこと
- audio_convertを追加したこと
- audio_cacheを追加したこと
- 解析用WAV仕様を PCM signed 16-bit little-endian / 44100 Hz / mono に固定したこと
- 解析用WAV保存先を cache/analysis_wav/ にしたこと
- cache自動削除はB5では行わないこと
- 変換失敗時の不完全ファイル削除を実装したこと
- 既存wavも解析用WAVへ変換する方針にしたこと
- 実ffmpeg必須テストではなく mock / fake runner で検証したこと
- B6ではGUI入力導線統合へ進むこと
```

README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは変更しない。

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
- MS17-B4完了commitまたは記録があるか
- B5開始前に意図しない差分がないか
```

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。

### Step 2: B3 / B4成果確認

以下を確認する。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
docs/repo_milestone.md
docs/Version_Control.md
```

確認観点。

```text
- ffmpeg path の探索結果を利用できるか
- AudioProbeResult が存在するか
- AudioErrorCode / AudioProbeError が存在するか
- B4で入力制限・ffprobe検査が完了しているか
- B5へ進む記録があるか
```

### Step 3: `src/core/audio_errors.py` 拡張

必要に応じて、B5用の error code を追加する。

追加候補。

```text
ffmpeg_not_found
ffmpeg_permission_error
ffmpeg_timeout
ffmpeg_execution_failed
analysis_wav_cache_dir_failed
analysis_wav_output_failed
analysis_wav_cleanup_failed
analysis_wav_generation_failed
```

既存の `AudioErrorInfo` / `AudioProbeError` が汎用利用可能なら、それを再利用する。

クラス名が probe 専用に見える場合は、B5で無理に大規模改名しない。
必要なら将来 `AudioProcessingError` などへの整理をB9またはMS18へ送る。

### Step 4: `src/core/ffmpeg_runner.py` 追加

`src/core/ffmpeg_runner.py` を追加する。

最低限含めるもの。

```text
DEFAULT_FFMPEG_TIMEOUT_SEC
FfmpegRunResult
run_ffmpeg_analysis_wav
```

実装内容。

```text
- subprocess.runを使用
- shell=True禁止
- stdout/stderr capture
- timeout指定
- returncode失敗時に AudioProbeError または既存エラー基盤で例外化
- FileNotFoundError を ffmpeg_not_found
- PermissionError を ffmpeg_permission_error
- subprocess.TimeoutExpired を ffmpeg_timeout
```

### Step 5: `src/core/audio_cache.py` 追加

`src/core/audio_cache.py` を追加する。

最低限含めるもの。

```text
ANALYSIS_WAV_CACHE_DIR
get_analysis_wav_cache_dir
ensure_analysis_wav_cache_dir
build_analysis_wav_filename
build_analysis_wav_path
cleanup_partial_file
```

実装内容。

```text
- cache/analysis_wav/ のパス生成
- ディレクトリ作成
- 元ファイル名stemのsafe化
- hash8生成
- _analysis.wav suffix付与
- 不完全ファイル削除
```

注意。

```text
- .gitignore は変更しない
- cache自動削除は実装しない
- 失敗時の対象ファイル削除だけ実装する
```

### Step 6: `src/core/audio_convert.py` 追加

`src/core/audio_convert.py` を追加する。

最低限含めるもの。

```text
AnalysisWavSpec
AnalysisWavResult
ANALYSIS_WAV_SPEC
generate_analysis_wav
```

実装内容。

```text
- source_pathを受け取る
- ffmpeg_pathを受け取る
- probe_resultを任意で受け取る
- base_dirを任意で受け取る
- runnerを任意で注入できる
- cache/analysis_wav/ を作成する
- 解析用WAV出力パスを作る
- ffmpeg_runnerを呼び出す
- 成功時に出力ファイル存在を確認する
- 失敗時に不完全ファイルを削除する
- AnalysisWavResultを返す
```

### Step 7: `tests/test_ms17_b5_ffmpeg_runner.py` 追加

`ffmpeg_runner` のテストを追加する。

標準テストは `subprocess.run` の mock を使う。

テスト観点。

```text
- 正常時にstdout/stderr/returncode/output_pathが返る
- 実行コマンドが shell=True ではない
- ffmpeg引数が期待通り
- -acodec pcm_s16le が含まれる
- -ar 44100 が含まれる
- -ac 1 が含まれる
- returncode != 0 で ffmpeg_execution_failed
- FileNotFoundError で ffmpeg_not_found
- PermissionError で ffmpeg_permission_error
- TimeoutExpired で ffmpeg_timeout
```

### Step 8: `tests/test_ms17_b5_analysis_wav_cache.py` 追加

`audio_cache` のテストを追加する。

テスト観点。

```text
- cache/analysis_wav/ パスが生成される
- cache/analysis_wav/ が作成される
- 元ファイルstemがファイル名に含まれる
- hash8が含まれる
- _analysis.wav で終わる
- 危険文字がsafe化される
- 同名stemでもpath/size/mtimeが違えばhashが変わる
- cleanup_partial_file が存在ファイルを削除する
- cleanup_partial_file が存在しないファイルで失敗しない
```

### Step 9: `tests/test_ms17_b5_analysis_wav_generation.py` 追加

`audio_convert` の正常系テストを追加する。

実 ffmpeg は使わず、fake runnerを注入する。

テスト観点。

```text
- generate_analysis_wav が AnalysisWavResult を返す
- 出力先が cache/analysis_wav/ 配下になる
- 仕様が pcm_s16le / 44100 / mono になる
- runnerに正しい input_path / output_path が渡る
- 既存wav入力でも変換対象になる
- mp3入力でも変換対象になる
- m4a入力でも変換対象になる
- probe_result の duration を結果へ引き継げる
```

### Step 10: `tests/test_ms17_b5_ffmpeg_failure_cleanup.py` 追加

変換失敗時の不完全ファイル削除テストを追加する。

テスト観点。

```text
- runner失敗時に不完全出力ファイルが削除される
- output_pathが存在しない場合でもcleanupで落ちない
- cleanup失敗時に analysis_wav_cleanup_failed などで分類される
- ffmpeg失敗の元エラー情報を失わない
```

### Step 11: B3 / B4回帰テスト

必要に応じてB3 / B4テストを再実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
```

### Step 12: B5限定テスト実行

以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py
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
- MS17-B5を実施したこと
- ffmpeg_runner / audio_convert / audio_cache を追加したこと
- 解析用WAV仕様を PCM signed 16-bit little-endian / 44100 Hz / mono に固定したこと
- 解析用WAV保存先を cache/analysis_wav/ にしたこと
- cache自動削除はB5では行わないこと
- 変換失敗時の不完全ファイル削除を実装したこと
- 既存wavも解析用WAVへ変換する方針であること
- 実ffmpeg必須テストではなく mock / fake runner で検証したこと
- B6では wav / mp3 / m4a 入力導線統合へ進むこと
```

README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは変更しない。

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
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/audio_errors.py
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_analysis_wav_generation.py
tests/test_ms17_b5_analysis_wav_cache.py
tests/test_ms17_b5_ffmpeg_failure_cleanup.py
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
src/gui_wx/
```

---

## 10. 状態遷移 / データ契約

### 10.1 B5で追加するデータ契約

B5では、解析用WAV生成結果として `AnalysisWavResult` を追加する。

役割。

```text
AnalysisWavResult:
- 入力音声から生成された解析用WAVの結果
- B6以降で波形表示・解析・timing plan生成へ渡す候補
- MMD用WAVではない
- VMD出力ではない
```

想定構造。

```text
source_path
analysis_wav_path
spec
duration_sec
file_size_bytes
```

`spec` の固定値。

```text
codec: pcm_s16le
sample_rate_hz: 44100
channel_count: 1
```

### 10.2 B5で追加する保存先契約

解析用WAVは以下に生成する。

```text
cache/analysis_wav/
```

ファイル名。

```text
<safe_stem>_<hash8>_analysis.wav
```

B5では以下を行わない。

```text
- cacheの自動削除
- cacheの再利用判定
- cache容量管理
```

### 10.3 B5で追加するエラー契約

B5では、ffmpeg変換と解析用WAV出力に関する失敗を分類可能にする。

最低限の分類。

```text
ffmpeg_not_found
ffmpeg_permission_error
ffmpeg_timeout
ffmpeg_execution_failed
analysis_wav_cache_dir_failed
analysis_wav_output_failed
analysis_wav_cleanup_failed
analysis_wav_generation_failed
```

### 10.4 B5で変更しない契約

以下はB5では変更しない。

```text
- selected_wav_path
- selected_wav_analysis
- current_timing_plan
- analysis_result_valid
- Preview shape contract
- VMD writer input
- MMD用WAV path
- GUI上のWAV読み込み導線
```

B5では、既存WAV読み込み経路を解析用WAVへ置き換えない。
B6で、GUI入力導線と解析用WAV生成を接続する。

### 10.5 B6以降へ送る契約

以下はB6で扱う。

```text
- GUIから wav / mp3 / m4a を選択する導線
- 入力音声と解析用WAVの内部状態保持
- 解析用WAVを波形表示へ渡す
- 解析用WAVを既存解析処理へ渡す
- 最近使ったファイル履歴の音声拡張対応
```

以下はB7で扱う。

```text
- MMD用WAV生成
- MMD用WAV保存
- MMD互換WAV検証
```

---

## 11. テスト方針

### 11.1 B5で実行する標準テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

### 11.2 B3 / B4回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
```

### 11.3 実 ffmpeg テスト方針

実 `ffmpeg.exe` を使うテストは必須にしない。

理由。

```text
- 開発環境にFFmpegが存在しない場合でもB5のテストを成立させるため
- GitHub Actionsや別Windows環境での環境差を避けるため
- B5の主目的はrunner / cache / conversion orchestrationの基盤固定であるため
```

任意テストを追加する場合は、以下の条件を満たすこと。

```text
- FFmpeg\bin\ffmpeg.exe が存在する場合のみ実行
- 存在しない場合は skip
- B5完了条件には含めない
```

ただし、初期B5では任意実ffmpegテストも追加しない方針を推奨する。

### 11.4 全体pytest

全体pytestは、既知のハング可能性がある場合は実行しない。

実行しない場合は、完了報告に理由を書く。

---

## 12. 受け入れ条件

MS17-B5は、以下を満たしたら完了とする。

### 12.1 実装条件

* `src/core/ffmpeg_runner.py` が追加されている。
* `src/core/audio_convert.py` が追加されている。
* `src/core/audio_cache.py` が追加されている。
* 必要に応じて `src/core/audio_errors.py` が拡張されている。
* 解析用WAV生成コマンドが実装されている。
* 解析用WAV仕様が `pcm_s16le / 44100 Hz / mono` として固定されている。
* 解析用WAV保存先が `cache/analysis_wav/` として実装されている。
* 解析用WAVファイル名が `<safe_stem>_<hash8>_analysis.wav` として生成される。
* `.wav` / `.mp3` / `.m4a` のいずれも解析用WAV生成対象として扱える。
* 既存 `.wav` 入力も解析用WAVへ変換する方針になっている。
* 変換失敗時に不完全ファイルが削除される。
* ffmpeg未検出、permission error、timeout、実行失敗、出力失敗、cleanup失敗が分類できる。
* B3 / B4の `ffmpeg_locator.py` / `audio_probe.py` と矛盾していない。

### 12.2 禁止事項遵守

以下が守られている。

```text
- GUI導線統合を完成扱いしていない
- mp3 / m4a 完全対応扱いしていない
- 解析用WAVを波形表示へ接続していない
- MMD用WAV出力をしていない
- 300秒確認ダイアログを実装していない
- cache自動削除を実装していない
- 音量正規化をしていない
- 無音トリムをしていない
- 自動フェードをしていない
- 自動ノイズ除去をしていない
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
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py
```

実 ffmpeg.exe がなくてもテストが成功する。

全体pytestを実行しなかった場合は、その理由が報告されている。

### 12.4 docs条件

以下が必要最小限で更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録上、B5の範囲が以下として明確である。

```text
- 解析用WAV生成基盤
- ffmpeg runner
- cache/analysis_wav/ 保存
- pcm_s16le / 44100 Hz / mono
- mock / fake runner中心の検証
- GUI統合なし
- MMD用WAV出力なし
- cache自動削除なし
```

---

## 13. リスクと対策

### Risk 1: 実 ffmpeg 依存でテストが不安定になる

対策。

```text
- 標準テストは mock / fake runner にする
- 実 ffmpeg 必須テストを入れない
- 実体確認はB9統合確認または任意手動確認へ送る
```

### Risk 2: B5でGUI統合まで進んでしまう

対策。

```text
- B5はcore層の解析用WAV生成基盤まで
- GUI入力導線統合はB6へ送る
- 波形表示・解析への接続もB6へ送る
```

### Risk 3: 解析用WAVとMMD用WAVを混同する

対策。

```text
- B5は解析用WAVのみ
- MMD用WAVはB7へ送る
- AnalysisWavResult にMMD用WAV情報を持たせない
- docsにも解析用WAVとMMD用WAVの役割差を記録する
```

### Risk 4: cache/analysis_wav/ がユーザー環境で作れない

対策。

```text
- cache dir作成失敗を analysis_wav_cache_dir_failed として分類する
- 書き込み権限エラーを明確に扱う
- 将来OS一時ディレクトリ方式へ移行可能なように audio_cache.py に責務を隔離する
```

### Risk 5: cacheが残り続ける

対策。

```text
- B5では自動削除しない方針を明記する
- 変換失敗時の不完全ファイルだけ削除する
- 起動時削除・終了時削除・容量管理はB8またはMS18へ送る
```

### Risk 6: 既存WAV経路を壊す

対策。

```text
- selected_wav_path / selected_wav_analysis をB5で変更しない
- audio_processing.py の既存WAV解析をB5で置き換えない
- B6で接続するときに段階的に切り替える
```

### Risk 7: 既存WAVも変換する方針により処理時間が増える

対策。

```text
- B5では仕様統一を優先する
- キャッシュ再利用はB5では行わない
- 処理時間や長時間確認はB8へ送る
```

### Risk 8: 不完全ファイル削除で元音声を誤削除する

対策。

```text
- cleanup対象は必ず生成予定の output_path のみに限定する
- source_path は削除対象にしない
- output_path が cache/analysis_wav/ 配下であることを確認する
```

---

## 14. Antigravity 実装時の注意

以下のプロンプトを Antigravity に渡して実施する。

```text
今回は MS17-B5 です。

目的:
解析用WAV生成基盤を実装してください。

重要:
- 対象branchは feature/MS17 です。
- MS17-B3 / B4 の成果を前提にしてください。
- 解析用WAV仕様は PCM signed 16-bit little-endian / 44100 Hz / mono です。
- 解析用WAV保存先は cache/analysis_wav/ です。
- B5では cache の自動削除は行わないでください。
- 変換失敗時の不完全ファイルだけ削除してください。
- 既存 .wav 入力も必ず解析用WAVへ変換する方針で実装してください。
- 解析用WAVファイル名は 元ファイル名stem + 短いハッシュ + _analysis.wav にしてください。
- 実 ffmpeg.exe を使うテストは必須にしないでください。
- 標準テストは mock / fake runner で行ってください。
- GUIファイル選択dialogの本格拡張は行わないでください。
- 解析用WAVを波形表示・解析へ接続する完成実装は行わないでください。
- MMD用WAV出力は行わないでください。
- 300秒確認ダイアログは実装しないでください。
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わないでください。
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
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
docs/repo_milestone.md
docs/Version_Control.md

実装対象:

src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_analysis_wav_generation.py
tests/test_ms17_b5_analysis_wav_cache.py
tests/test_ms17_b5_ffmpeg_failure_cleanup.py

必要に応じて最小変更:

src/core/audio_errors.py
docs/repo_milestone.md
docs/Version_Control.md

実装内容:

1. src/core/ffmpeg_runner.py を追加してください。
   - ffmpeg.exe を subprocess.run で実行するラッパーを実装してください。
   - shell=True は使わないでください。
   - コマンドは list[str] で渡してください。
   - stdout / stderr をcaptureしてください。
   - timeoutを扱ってください。
   - returncode失敗を分類してください。
   - FileNotFoundError / PermissionError / TimeoutExpired を分類してください。
   - コマンドは以下の仕様にしてください。
     ffmpeg.exe -y -i <input_path> -vn -acodec pcm_s16le -ar 44100 -ac 1 <output_path>

2. src/core/audio_cache.py を追加してください。
   - cache/analysis_wav/ のパス生成を実装してください。
   - cache/analysis_wav/ の作成を実装してください。
   - 元ファイル名stemをsafe化してください。
   - 元ファイルの絶対パス、サイズ、mtime_ns などから短いhash8を作ってください。
   - ファイル名は <safe_stem>_<hash8>_analysis.wav にしてください。
   - 不完全ファイル削除 helper を実装してください。
   - cacheの自動削除は実装しないでください。

3. src/core/audio_convert.py を追加してください。
   - AnalysisWavSpec を定義してください。
   - AnalysisWavResult を定義してください。
   - ANALYSIS_WAV_SPEC は pcm_s16le / 44100 Hz / mono にしてください。
   - generate_analysis_wav を実装してください。
   - source_path / ffmpeg_path / probe_result / base_dir / runner / timeout_sec を扱えるようにしてください。
   - cache/analysis_wav/ に解析用WAVを生成してください。
   - 既存 .wav 入力も変換対象にしてください。
   - .mp3 / .m4a も変換対象にしてください。
   - 成功時は AnalysisWavResult を返してください。
   - 失敗時は不完全ファイルを削除してください。

4. src/core/audio_errors.py を必要最小限で拡張してください。
   - ffmpeg_not_found
   - ffmpeg_permission_error
   - ffmpeg_timeout
   - ffmpeg_execution_failed
   - analysis_wav_cache_dir_failed
   - analysis_wav_output_failed
   - analysis_wav_cleanup_failed
   - analysis_wav_generation_failed
   を扱えるようにしてください。
   - 既存のffprobe系エラーと混同しないでください。

5. tests/test_ms17_b5_ffmpeg_runner.py を追加してください。
   - subprocess.run を mock してください。
   - 正常系、returncode失敗、FileNotFoundError、PermissionError、TimeoutExpired を確認してください。
   - shell=True を使っていないことを確認してください。
   - -acodec pcm_s16le / -ar 44100 / -ac 1 が含まれることを確認してください。

6. tests/test_ms17_b5_analysis_wav_cache.py を追加してください。
   - cache/analysis_wav/ パス生成
   - ディレクトリ作成
   - safe stem
   - hash8
   - _analysis.wav suffix
   - cleanup_partial_file
   を確認してください。

7. tests/test_ms17_b5_analysis_wav_generation.py を追加してください。
   - 実 ffmpeg.exe は使わず fake runner を注入してください。
   - generate_analysis_wav が AnalysisWavResult を返すことを確認してください。
   - 出力先が cache/analysis_wav/ 配下になることを確認してください。
   - 仕様が pcm_s16le / 44100 / mono になることを確認してください。
   - wav / mp3 / m4a がいずれも変換対象になることを確認してください。

8. tests/test_ms17_b5_ffmpeg_failure_cleanup.py を追加してください。
   - runner失敗時に不完全出力ファイルが削除されることを確認してください。
   - output_pathが存在しない場合でもcleanupで落ちないことを確認してください。
   - cleanup失敗時に分類可能であることを確認してください。
   - source_pathを誤削除しないことを確認してください。

実行するテスト:

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py

必要に応じてB3/B4回帰テストも実行してください。

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py

全体pytestは、ハング可能性がある場合は実行しないでください。

実装後、必要最小限で以下を更新してください。

docs/repo_milestone.md
docs/Version_Control.md

記録内容:
- MS17-B5を実施したこと
- ffmpeg_runner / audio_convert / audio_cache を追加したこと
- 解析用WAV仕様を PCM signed 16-bit little-endian / 44100 Hz / mono に固定したこと
- 解析用WAV保存先を cache/analysis_wav/ にしたこと
- cache自動削除はB5では行わないこと
- 変換失敗時の不完全ファイル削除を実装したこと
- 既存wavも解析用WAVへ変換する方針であること
- 実ffmpeg必須テストではなく mock / fake runner で検証したこと
- B6では wav / mp3 / m4a 入力導線統合へ進むこと

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
5. 実装したffmpeg runner仕様
6. 実装したaudio_cache仕様
7. 実装したaudio_convert仕様
8. 解析用WAV仕様
9. cache/analysis_wav/ の扱い
10. 失敗時cleanup
11. 実行したテスト
12. 実行していないテスト
13. 変更していないファイル
14. .gitignoreを変更していないこと
15. 禁止事項の遵守
16. B6への引き継ぎ
17. 未解決・要確認事項
```

---

## 15. 完了報告テンプレート

Antigravityは、完了時に以下の形式で報告する。

```text
MS17-B5 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 追加したファイル
- src/core/ffmpeg_runner.py:
- src/core/audio_convert.py:
- src/core/audio_cache.py:
- tests/test_ms17_b5_ffmpeg_runner.py:
- tests/test_ms17_b5_analysis_wav_generation.py:
- tests/test_ms17_b5_analysis_wav_cache.py:
- tests/test_ms17_b5_ffmpeg_failure_cleanup.py:

4. 変更したファイル
- src/core/audio_errors.py:
- docs/repo_milestone.md:
- docs/Version_Control.md:

5. 実装したffmpeg runner仕様
- コマンド:
- shell=True不使用:
- stdout/stderr capture:
- timeout:
- returncode失敗:
- permission error:
- timeout error:
- stderrの扱い:

6. 実装したaudio_cache仕様
- cache dir:
- safe stem:
- hash8:
- filename:
- cleanup_partial_file:
- cache自動削除:

7. 実装したaudio_convert仕様
- generate_analysis_wav:
- AnalysisWavSpec:
- AnalysisWavResult:
- wav入力:
- mp3入力:
- m4a入力:
- probe_result連携:
- runner注入:

8. 解析用WAV仕様
- codec:
- sample rate:
- channels:
- container:

9. cache/analysis_wav/ の扱い
- 保存先:
- 自動削除:
- 失敗時削除:
- 権限エラー:

10. 失敗時cleanup
- 不完全ファイル削除:
- cleanup失敗時:
- source_path誤削除防止:

11. 実行したテスト
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_generation.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_analysis_wav_cache.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_failure_cleanup.py:
- B3/B4回帰テスト:

12. 実行していないテスト
- 実ffmpegテスト:
- 全体pytest:
- 理由:

13. 変更していないファイル
- README.md:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:
- src/gui_wx/:

14. 禁止事項の確認
- GUI本格統合:
- 解析用WAVの波形表示接続:
- MMD用WAV出力:
- 300秒確認ダイアログ:
- cache自動削除:
- 音量正規化:
- 無音トリム:
- 自動フェード:
- 自動ノイズ除去:
- Qt / PySide6再導入:

15. B6への引き継ぎ
- AnalysisWavResult:
- analysis_wav_path:
- cache/analysis_wav/:
- GUI入力導線:
- 既存WAV経路からの切替:
- 未解決事項:

16. 未解決・要確認事項
- ...
```

---

## 16. MS17-B6への引き継ぎ条件

MS17-B6へ進む場合、B5から以下を引き継ぐ。

```text
- AnalysisWavSpec の構造
- AnalysisWavResult の構造
- 解析用WAV仕様:
  - PCM signed 16-bit little-endian
  - 44100 Hz
  - mono
- 解析用WAV保存先:
  - cache/analysis_wav/
- 解析用WAVファイル名規則:
  - <safe_stem>_<hash8>_analysis.wav
- 既存wavも解析用WAVへ変換する方針
- 変換失敗時の不完全ファイル削除方針
- cache自動削除は未実装であること
- 実ffmpeg必須テストではなく mock / fake runner で検証していること
```

MS17-B6では、以下へ進む。

```text
MS17-B6: wav / mp3 / m4a 入力導線統合
```

B6で扱う候補。

```text
- GUIファイル選択dialogの拡張
- 「WAV読み込み」から「音声読み込み」への文言見直し
- 入力音声パス表示
- 入力形式表示
- ffprobe検査との接続
- 解析用WAV生成との接続
- 解析用WAVを波形表示へ渡す
- 解析用WAVを既存解析処理へ渡す
- TEXT / 音声 / パラメータ変更時の無効化規則確認
- 最近使ったファイル履歴の音声拡張対応
```

B6でも引き続き、以下を守る。

```text
- MMD用WAV出力はB7へ送る
- 300秒確認ダイアログはB8へ送る
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わない
- Qt / PySide6 は再導入しない
```
