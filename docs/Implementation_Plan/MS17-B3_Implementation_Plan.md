# MS17-B3 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B3
- Block name: FFmpeg / ffprobe locator + 音声入力拡張の前提基盤
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B3_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Google Antigravity
- Coding AI: Gemini 3.1 Pro
- Shell: Windows PowerShell
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作業種別: 最小実装
- 実装変更: あり
- GUI大規模変更: 禁止
- FFmpeg実行確認: 禁止
- ffprobe実行確認: 禁止
- テスト実行: 限定テストのみ

---

## 2. 背景

MS17は、MS16 closeout 後に開始する音声入力・音声変換拡張マイルストーンである。

MS17全体では、以下を扱う。

- wav / mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 入力音声の検査
- 解析用WAV生成
- 解析用WAVを波形表示・解析の正本にする
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換系エラー分類
- 長時間処理確認ダイアログ
- FFmpeg / ffprobe プロセス終了方針
- 失敗時の不完全ファイル削除
- FFmpeg同梱有無、ライセンス、NOTICE、THIRD_PARTY_LICENSES 方針整理

MS17 Block Breakdown では、MS17-B3 は当初以下として定義されている。

```text
MS17-B3: 音声入力拡張の前提基盤
````

ただし、MS17-B2 では FFmpeg / ffprobe の接続方式・配布方針・探索優先順が整理され、後続Blockで locator 実装へ進む前提が成立している。

そのため、MS17-B3ではB案を採用し、Block名を次のように扱う。

```text
MS17-B3: FFmpeg / ffprobe locator + 音声入力拡張の前提基盤
```

ただし、MS17-B3では範囲を広げすぎない。

MS17-B3で行うのは、以下に限定する。

* FFmpeg / ffprobe の実体パス探索基盤
* 入力音声ファイル情報の最小データ構造
* `.wav` / `.mp3` / `.m4a` の種別判定
* 未対応拡張子の拒否
* 既存WAV入力経路の互換維持
* 音声変更時の既存無効化規則の維持確認

MS17-B3では、ffmpeg変換、ffprobe検査、解析用WAV生成、MMD用WAV出力はまだ行わない。

---

## 3. 目的

MS17-B3の目的は、MS17-B4以降で ffprobe検査、MS17-B5以降で解析用WAV生成、MS17-B6以降で wav / mp3 / m4a 入力導線統合を行うための前提基盤を整えることである。

具体的には、以下を達成する。

1. FFmpeg / ffprobe の探索優先順を実装可能な形で固定する。
2. repo直下、PyInstaller onefile展開先、PATH fallback の探索を扱える locator を追加する。
3. locator は実体パスを返すだけに留め、ffmpeg / ffprobe の実行は行わない。
4. 入力音声ファイルを表す最小データ構造を追加する。
5. `.wav` / `.mp3` / `.m4a` の種別判定を行う。
6. `.mp3` / `.m4a` は受け入れ準備段階として扱い、変換済み・解析可能扱いしない。
7. 既存の PCM WAV 入力経路を壊さない。
8. TEXT / 音声 / パラメータ変更時に、古い timing plan / Preview / VMD保存可能状態 / 選択状態が無効化される既存規則を維持する。
9. Qt / PySide6 系を再導入しない。
10. 解析用WAVとMMD用WAVを混同しない。

---

## 4. In Scope

MS17-B3で行う作業は以下に限定する。

### 4.1 FFmpeg / ffprobe locator の追加

`src/core/ffmpeg_locator.py` を新規追加する。

責務は以下。

* `ffmpeg.exe` の候補パス探索
* `ffprobe.exe` の候補パス探索
* 探索元の分類
* 見つかった実体パスの保持
* 見つからなかった場合の分類可能な結果返却
* `ffmpeg.exe` / `ffprobe.exe` の片方だけ見つかった場合の状態表現

探索優先順は以下。

```text
1. repo直下 FFmpeg\bin\ffmpeg.exe / FFmpeg\bin\ffprobe.exe
2. PyInstaller onefile 展開先 sys._MEIPASS 配下の FFmpeg\ffmpeg.exe / FFmpeg\ffprobe.exe
3. PATH 上の ffmpeg.exe / ffprobe.exe
```

補足:

* repo直下の開発時配置は `FFmpeg\bin\` を正とする。
* PyInstaller onefile 展開先は `sys._MEIPASS` を確認する。
* 現行 spec では onefile 内部に `FFmpeg` 配下としてバイナリが展開される可能性があるため、B3では `sys._MEIPASS\FFmpeg\ffmpeg.exe` / `sys._MEIPASS\FFmpeg\ffprobe.exe` を探索対象に含める。
* `PATH` は fallback として扱う。
* `PATH` fallback 使用時は、将来 GUI またはログで実体パスとversion情報を表示・記録できる設計にする。
* B3では version 取得は行わない。
* B3では `ffmpeg.exe` / `ffprobe.exe` を実行しない。

### 4.2 音声入力データ構造の追加

`src/core/audio_input.py` を新規追加する。

責務は以下。

* 入力音声ファイル情報を表す dataclass の追加
* 入力元ファイルパスの保持
* 入力音声種別の保持
* 拡張子判定
* `.wav` / `.mp3` / `.m4a` の受け入れ準備
* 未対応拡張子の拒否
* 入力音声と解析用WAVを混同しない命名

想定する最小構造例:

```python
class AudioInputKind(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"

@dataclass(frozen=True)
class AudioInputInfo:
    source_path: str
    kind: AudioInputKind
    suffix: str
```

この構造は、ユーザーが選択した元ファイルを表す。

以下は含めない。

* 解析用WAVパス
* MMD用WAVパス
* ffprobe結果
* ffmpeg変換結果
* duration
* codec
* sample rate
* channel count

これらはB4以降、B5以降、B7以降で扱う。

### 4.3 既存WAV入力経路の互換維持

既存のWAV入力経路を壊さない。

現時点で既存経路として扱うもの。

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/core/audio_processing.py
```

維持対象。

* `selected_wav_path`
* `selected_wav_analysis`
* `analyze_wav_file`
* `load_waveform_preview`
* Playback
* Waveform表示
* Preview表示
* VMD保存可能状態
* TEXT / WAV / パラメータ変更時の無効化規則
* 選択イベント状態のクリア

MS17-B3では、内部に新しい `AudioInputInfo` を追加しても、既存の `selected_wav_path` を即座に置き換えない。

既存WAV経路を壊さないことを優先する。

### 4.4 GUI側の接続候補整理

MS17-B3では、GUI上の大規模変更は行わない。

ただし、後続Blockのために以下を整理する。

* 「WAV読み込み」を将来「音声読み込み」に変更する候補
* ファイルダイアログで `.wav` / `.mp3` / `.m4a` を受け入れる導線
* 最近使ったファイル履歴の扱い
* `selected_wav_path` という既存名称をいつ置き換えるか
* 既存のWAV解析処理と mp3 / m4a 変換導線の接続境界

MS17-B3でGUI文言を変更する場合は、最小限に留める。

推奨は以下。

* B3では内部構造とテストを優先する。
* GUI文言変更とファイルダイアログ拡張はB6で本格対応する。
* ただし、B3で入力種別判定のテスト可能なヘルパーは追加する。

### 4.5 テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
```

テスト観点。

* repo直下配置の探索
* onefile展開先配置の探索
* PATH fallback の探索
* `ffmpeg.exe` / `ffprobe.exe` 両方あり
* `ffmpeg.exe` のみあり
* `ffprobe.exe` のみあり
* 両方なし
* `.wav` 判定
* `.mp3` 判定
* `.m4a` 判定
* 拡張子大文字小文字の扱い
* 未対応拡張子拒否
* パスが空の場合の拒否
* ディレクトリが渡された場合の扱い
* 既存WAV経路に影響しないこと

---

## 5. Out of Scope

MS17-B3では以下を行わない。

```text
- ffmpeg.exe の実行
- ffprobe.exe の実行
- ffmpeg / ffprobe の version 取得
- ffprobe による音声長取得
- ffprobe による codec 取得
- ffprobe による stream 検査
- 入力ファイルサイズ上限 500MB の実装
- 音声長上限 15分の実装
- ffmpeg による解析用WAV生成
- mp3 / m4a の完全動作保証
- mp3 / m4a を波形表示へ直接接続すること
- 解析用WAVを波形表示・解析へ接続する完成実装
- MMD用WAV出力
- VMD保存導線の変更
- Whisper入力の変更
- 音量正規化
- 無音トリム
- 自動フェード
- 自動ノイズ除去
- ピッチ補正
- テンポ補正
- 300秒確認ダイアログ
- FFmpeg / ffprobe の terminate / kill 実装
- FFmpeg / ffprobe の自動ダウンロード
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

MS17-B3は、以下を前提とする。

* 作業branchは `feature/MS17` である。
* MS17-B1 が完了済みである。
* MS17-B2 が完了済みである。
* FFmpeg / ffprobe は配布物に同梱する方向を推奨する。
* 基準配置は `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe` である。
* PyInstaller onefile では、バイナリが `sys._MEIPASS` 配下に展開される可能性がある。
* PATH上の FFmpeg / ffprobe は fallback として扱う。
* MS17では FFmpeg / ffprobe の自動ダウンロードを行わない。
* `.gitignore` はユーザー側で管理するため、Antigravityは作成・変更しない。
* 既存WAV入力は、現時点では PCM WAV を前提に動作している。
* 既存の `analyze_wav_file` / `load_waveform_preview` は WAV ファイルを対象とする。
* mp3 / m4a はB3時点では受け入れ準備・種別判定までとする。
* 解析用WAVはB5以降の正本として扱う。
* MMD用WAVはB7以降の出力物として扱う。
* VMD出力は引き続きリップモーフキーフレームのみである。
* Qt / PySide6 / shiboken6 は再導入しない。

---

## 7. 対象ファイル

MS17-B3で変更・追加する候補は以下。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
```

必要に応じて確認するファイル。

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/core/audio_processing.py
MMD_AutoLipTool.spec
build.ps1
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Implementation_Plan/MS17-B1_Implementation_Plan.md
docs/Implementation_Plan/MS17-B2_Implementation_Plan.md
```

原則として、MS17-B3で変更してよいのは以下。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
docs/Version_Control.md
docs/repo_milestone.md
```

ただし、`docs/Version_Control.md` と `docs/repo_milestone.md` の更新は、実装完了後の記録として必要最小限に留める。

MS17-B3で変更しないもの。

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

## 8. 実装方針

### 8.1 実装の基本方針

MS17-B3では、後続Blockのための前提基盤を追加する。

ただし、既存WAV処理の主経路は壊さない。

実装方針は以下。

```text
- 既存WAV入力経路を正として維持する
- 新しい音声入力抽象は追加するが、既存UI経路へ無理に全面統合しない
- ffmpeg / ffprobe locator は実行ファイルの有無とパス解決だけを扱う
- ffmpeg / ffprobe の実行・version取得はB4以降に送る
- mp3 / m4a は入力種別として認識するが、解析可能扱いしない
- 解析用WAVとMMD用WAVをデータ構造上も命名上も混同しない
- テストでB3の責務境界を固定する
```

### 8.2 `ffmpeg_locator.py` の方針

`ffmpeg_locator.py` には、最小限の純粋関数・dataclassを置く。

想定構造。

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

class FfmpegToolSource(str, Enum):
    REPO_LOCAL = "repo_local"
    BUNDLED = "bundled"
    PATH = "path"
    NOT_FOUND = "not_found"

@dataclass(frozen=True)
class FfmpegToolPath:
    path: Optional[Path]
    source: FfmpegToolSource

@dataclass(frozen=True)
class FfmpegLocatorResult:
    ffmpeg: FfmpegToolPath
    ffprobe: FfmpegToolPath

    @property
    def is_complete(self) -> bool:
        return self.ffmpeg.path is not None and self.ffprobe.path is not None
```

関数候補。

```python
def locate_ffmpeg_tools(
    project_root: Path | None = None,
    meipass_root: Path | None = None,
    path_env: str | None = None,
) -> FfmpegLocatorResult:
    ...
```

設計上の注意。

* テストしやすいように、`project_root` / `meipass_root` / `path_env` を注入可能にする。
* 実環境依存を減らす。
* `sys._MEIPASS` 参照は関数内で直接固定せず、ヘルパーで扱う。
* `shutil.which` を使う場合も、`path_env` をテストで差し替えられるようにする。
* Windows前提の `.exe` 名を扱う。
* B3ではUnix系バイナリ名 `ffmpeg` / `ffprobe` の本格対応は不要。
* 見つかったパスは `Path` として返す。
* 存在確認は `Path.is_file()` を基本とする。
* 実行権限確認や `subprocess` 実行はB4以降に送る。

### 8.3 onefile展開先の扱い

PyInstaller onefileでは、バンドルされたファイルが実行時に `sys._MEIPASS` 配下へ展開される。

MS17-B3では、以下の候補を探索対象に含める。

```text
sys._MEIPASS\FFmpeg\ffmpeg.exe
sys._MEIPASS\FFmpeg\ffprobe.exe
```

補足:

* repo開発時配置は `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe`。
* onefile展開時配置は spec の `binaries` 設定により `FFmpeg\ffmpeg.exe` / `FFmpeg\ffprobe.exe` になる可能性がある。
* B3では `build.ps1` や spec を変更しない。
* 配置不整合が見つかった場合は、B4以降または packaging補正で扱う。

### 8.4 `audio_input.py` の方針

`audio_input.py` には、入力音声ファイルの最小情報を置く。

想定構造。

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class AudioInputKind(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"

@dataclass(frozen=True)
class AudioInputInfo:
    source_path: Path
    kind: AudioInputKind
    suffix: str
```

関数候補。

```python
def detect_audio_input_kind(path: str | Path) -> AudioInputKind:
    ...

def build_audio_input_info(path: str | Path) -> AudioInputInfo:
    ...
```

判定方針。

```text
.wav  -> AudioInputKind.WAV
.mp3  -> AudioInputKind.MP3
.m4a  -> AudioInputKind.M4A
その他 -> ValueError など明確な例外
```

注意。

* 拡張子は小文字正規化して判定する。
* `.WAV` / `.MP3` / `.M4A` など大文字小文字混在を許容する。
* B3ではファイルの中身検査は行わない。
* B3では ffprobe による形式検査は行わない。
* B3ではファイルサイズ上限や音声長上限は行わない。
* B3では `AudioInputInfo` に解析用WAVパスを持たせない。
* B3では `AudioInputInfo` にMMD用WAVパスを持たせない。

### 8.5 既存UiStateとの関係

現時点の `UiState` には、既存WAV入力向けの状態がある。

代表例。

```text
selected_wav_path
selected_wav_analysis
recent_wav_files
last_wav_dialog_dir
loaded_playback_path
```

MS17-B3では、これらを大きく置き換えない。

B3で `AudioInputInfo` を `UiState` に追加するかどうかは、repo実装状態を確認して最小判断する。

推奨方針。

```text
- B3では core 側の audio_input.py とテストを優先する
- UiStateへの統合は必要最小限に留める
- GUI導線の本格統合はB6へ送る
```

もし `UiState` に追加する場合の候補。

```python
selected_audio_input: Optional[Any] = None
```

ただし、型の安定性や既存テストへの影響を確認したうえで判断する。

### 8.6 無効化規則の維持

MS17-B3では、既存の無効化規則を壊さないことを確認する。

維持すべき規則。

```text
TEXT変更時:
- timing plan 無効化
- Preview 無効化
- VMD保存不可
- 選択イベントクリア

音声変更時:
- timing plan 無効化
- Preview 無効化
- VMD保存不可
- 選択イベントクリア
- 再生状態の不整合を残さない

パラメータ変更時:
- timing plan 無効化
- Preview 無効化
- VMD保存不可
- 選択イベントクリア
```

B3では、mp3 / m4aを選択しただけで解析成功扱いにしない。

### 8.7 docs更新方針

MS17-B3完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録する内容。

* MS17-B3で追加したファイル
* locator追加の範囲
* audio_input追加の範囲
* ffmpeg / ffprobeは実行していないこと
* mp3 / m4aは種別判定までであり、完全対応ではないこと
* B4への引き継ぎ

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

* 現在branchが `feature/MS17` であるか
* 作業ツリーに意図しない差分がないか
* staged差分がないか
* docs配下のMS17関連文書が読めるか
* B1/B2実装プランが存在するか
* MS17 Block Breakdown が存在するか

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。

### Step 2: 既存ファイル確認

以下を確認する。

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/core/audio_processing.py
MMD_AutoLipTool.spec
build.ps1
docs/repo_milestone.md
docs/Version_Control.md
```

確認観点。

* 既存WAV入力経路
* `selected_wav_path` の使われ方
* `selected_wav_analysis` の使われ方
* `analyze_wav_file` の呼び出し箇所
* `load_waveform_preview` の呼び出し箇所
* 音声変更時の `invalidate_analysis()` 呼び出し
* 選択状態クリアの経路
* onefile時のFFmpegバンドル配置
* build時の `FFmpeg\bin` 前提

### Step 3: `src/core/ffmpeg_locator.py` 追加

`src/core/ffmpeg_locator.py` を追加する。

最低限含めるもの。

```text
FfmpegToolSource
FfmpegToolPath
FfmpegLocatorResult
locate_ffmpeg_tools
```

探索順。

```text
1. repo直下 FFmpeg\bin
2. PyInstaller onefile 展開先 sys._MEIPASS\FFmpeg
3. PATH
```

実装時の注意。

* `subprocess` は使用しない。
* `ffmpeg.exe` / `ffprobe.exe` は実行しない。
* version取得は行わない。
* テストしやすいように root を注入できる設計にする。
* PATH探索もテスト可能にする。
* Windows前提の `.exe` を扱う。

### Step 4: `tests/test_ms17_b3_ffmpeg_locator.py` 追加

locatorのテストを追加する。

テスト観点。

```text
- repo直下 FFmpeg\bin に両方ある場合、repo_local として検出される
- repo直下に片方しかない場合、片方だけ検出される
- repo直下になく、meipass配下に両方ある場合、bundled として検出される
- repo直下にもmeipassにもなく、PATH上にある場合、path として検出される
- どこにもない場合、not_found として返る
- repo配置がPATHより優先される
- bundled配置がPATHより優先される
- ffmpeg / ffprobe の実行は行われない
```

テストでは一時ディレクトリを使い、空ファイルとして `ffmpeg.exe` / `ffprobe.exe` を作成してよい。

### Step 5: `src/core/audio_input.py` 追加

`src/core/audio_input.py` を追加する。

最低限含めるもの。

```text
AudioInputKind
AudioInputInfo
detect_audio_input_kind
build_audio_input_info
```

実装時の注意。

* 拡張子判定は小文字正規化する。
* `.wav` / `.mp3` / `.m4a` のみ許可する。
* それ以外は明確な例外にする。
* B3ではファイル内容検査は行わない。
* B3では音声長検査は行わない。
* B3ではファイルサイズ検査は行わない。
* B3では解析用WAVパスを扱わない。
* B3ではMMD用WAVパスを扱わない。

### Step 6: `tests/test_ms17_b3_audio_input_foundation.py` 追加

音声入力基盤のテストを追加する。

テスト観点。

```text
- .wav が WAV と判定される
- .mp3 が MP3 と判定される
- .m4a が M4A と判定される
- .WAV / .MP3 / .M4A など大文字小文字混在を許容する
- 未対応拡張子は拒否される
- 拡張子なしは拒否される
- build_audio_input_info が source_path / kind / suffix を保持する
- AudioInputInfo が入力音声のみを表し、解析用WAVやMMD用WAVを持たない
```

### Step 7: 既存WAV経路への影響確認

B3実装で既存WAV入力経路が壊れていないことを確認する。

最低限、以下を確認する。

```text
- src/gui_wx/main_frame.py の既存WAV読み込み経路を壊していない
- src/core/audio_processing.py の analyze_wav_file / load_waveform_preview を変更していない
- selected_wav_path / selected_wav_analysis の既存意味を変更していない
- VMD保存可能状態の条件を変更していない
- Preview表示の正本を変更していない
```

B3では既存GUI経路への統合は最小限に留める。

### Step 8: 限定テスト実行

以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
```

必要に応じて、既存WAV経路に近いテストを限定実行する。

候補。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

ただし、全体pytestにハング可能性がある場合、全体pytestは実行しない。

### Step 9: docs更新

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録内容。

```text
- MS17-B3を実施したこと
- ffmpeg_locator を追加したこと
- audio_input を追加したこと
- ffmpeg / ffprobe は実行していないこと
- mp3 / m4a は種別判定までであり、完全対応ではないこと
- B4では ffprobe検査・入力制限・エラー分類へ進むこと
```

README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは変更しない。

### Step 10: 完了前diff確認

以下を実行する。

```powershell
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

想定される変更ファイル。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py
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

### 10.1 MS17-B3で追加する契約

MS17-B3では、入力音声と FFmpeg / ffprobe 探索結果の最小契約を追加する。

#### 入力音声

入力音声は、ユーザーが選択した元ファイルである。

```text
AudioInputInfo.source_path
AudioInputInfo.kind
AudioInputInfo.suffix
```

入力音声は、解析可能なWAVであるとは限らない。

`.mp3` / `.m4a` は、B3時点では入力種別として認識するだけであり、解析可能扱いしない。

#### FFmpeg / ffprobe 探索結果

FFmpeg / ffprobe 探索結果は、実体パスと探索元を表す。

```text
FfmpegLocatorResult.ffmpeg.path
FfmpegLocatorResult.ffmpeg.source
FfmpegLocatorResult.ffprobe.path
FfmpegLocatorResult.ffprobe.source
FfmpegLocatorResult.is_complete
```

B3では、探索結果は実行可能性を保証しない。

実行可能性、version、codec対応、権限エラー、timeoutはB4以降で扱う。

### 10.2 MS17-B3で変更しない契約

以下はB3では変更しない。

```text
- selected_wav_path は既存WAV入力経路のために維持する
- selected_wav_analysis は既存WAV解析結果として維持する
- current_timing_plan は解析結果の正本として維持する
- Preview shape は timing plan から派生する表示・選択用データである
- Preview shape を timing plan の正本にしない
- RightPane表示は正本ではない
- VMD writer input は既存 timing plan を正とする
```

### 10.3 MS17-B3でまだ追加しない契約

以下はB3では追加しない。

```text
- analysis_wav_path
- mmd_wav_output_path
- ffprobe_result
- audio_duration_sec
- audio_codec
- audio_sample_rate
- audio_channel_count
- audio_file_size_bytes
- conversion_job_id
- conversion_cancel_token
```

これらはB4以降、B5以降、B7以降、B8以降で扱う。

### 10.4 無効化規則

B3実装後も、以下の既存規則を維持する。

```text
TEXT変更:
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア

音声変更:
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア

パラメータ変更:
- current_timing_plan を無効化
- analysis_result_valid を False
- Previewをクリア
- VMD保存不可
- selected_source_event_index をクリア
```

B3では mp3 / m4a を選択しただけで `analysis_result_valid=True` にしてはならない。

---

## 11. テスト方針

MS17-B3では、追加した基盤に対する限定テストを実行する。

### 11.1 実行するテスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
```

必要に応じて、既存WAV経路への影響確認として以下を限定実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

### 11.2 実行しないテスト

全体pytestは、既知のハング可能性がある場合は実行しない。

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

上記を実行する場合は、ハング可能性と実行時間を考慮し、必要性を判断してから行う。

### 11.3 テストで確認する境界

テストでは、以下の境界を固定する。

```text
- locator は探索のみ行う
- locator は ffmpeg / ffprobe を実行しない
- audio_input は拡張子判定のみ行う
- audio_input は ffprobe検査を行わない
- mp3 / m4a は変換済み扱いしない
- 解析用WAVパスをB3のAudioInputInfoに含めない
- MMD用WAVパスをB3のAudioInputInfoに含めない
```

---

## 12. 受け入れ条件

MS17-B3は、以下を満たしたら完了とする。

### 12.1 実装条件

* `src/core/ffmpeg_locator.py` が追加されている。
* `src/core/audio_input.py` が追加されている。
* `tests/test_ms17_b3_ffmpeg_locator.py` が追加されている。
* `tests/test_ms17_b3_audio_input_foundation.py` が追加されている。
* repo直下 `FFmpeg\bin` 探索が実装されている。
* PyInstaller onefile 展開先 `sys._MEIPASS\FFmpeg` 探索が実装されている。
* PATH fallback 探索が実装されている。
* `.wav` / `.mp3` / `.m4a` の種別判定ができる。
* 未対応拡張子を拒否できる。
* 既存WAV入力経路が壊れていない。
* mp3 / m4a が変換済み扱いされていない。
* 解析用WAVとMMD用WAVが混同されていない。

### 12.2 禁止事項遵守

以下が守られている。

* ffmpeg / ffprobe を実行していない。
* ffmpeg / ffprobe の version 取得をしていない。
* ffprobe検査を実装していない。
* ffmpeg変換を実装していない。
* 解析用WAV生成を実装していない。
* MMD用WAV出力を実装していない。
* READMEを変更していない。
* NOTICEを変更していない。
* THIRD_PARTY_LICENSES.mdを変更していない。
* Release Package Manifestを変更していない。
* build.ps1を変更していない。
* MMD_AutoLipTool.specを変更していない。
* `.gitignore` を変更していない。
* Qt / PySide6 を再導入していない。

### 12.3 テスト条件

以下が成功している。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
```

必要に応じて実行した既存WAV経路関連テストの結果も報告されている。

全体pytestを実行しなかった場合は、その理由が報告されている。

### 12.4 docs条件

以下が必要最小限で更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

記録上、B3の範囲が以下として明確である。

```text
- locator追加
- 音声入力種別判定追加
- ffmpeg / ffprobe実行なし
- mp3 / m4a完全対応なし
- 解析用WAV生成なし
- MMD用WAV出力なし
```

---

## 13. リスクと対策

### Risk 1: B3でffmpeg / ffprobe実行まで進んでしまう

対策:

* `ffmpeg_locator.py` は探索のみとする。
* `subprocess` を使わない。
* version取得をしない。
* ffprobe検査はB4へ送る。
* ffmpeg変換はB5へ送る。
* テストで「実行しない」境界を固定する。

### Risk 2: mp3 / m4a を解析可能扱いしてしまう

対策:

* `AudioInputInfo` は入力音声の種別判定だけを担う。
* mp3 / m4a を `selected_wav_analysis` に接続しない。
* mp3 / m4a を `load_waveform_preview` に直接渡さない。
* mp3 / m4a の解析用WAV生成はB5以降に送る。
* GUI統合はB6で扱う。

### Risk 3: 既存WAV入力経路を壊す

対策:

* `audio_processing.py` は原則変更しない。
* `selected_wav_path` の意味をB3で変更しない。
* 既存GUI経路の変更は最小限にする。
* 既存WAV関連テストを必要に応じて限定実行する。

### Risk 4: 解析用WAVとMMD用WAVを混同する

対策:

* B3の `AudioInputInfo` には解析用WAVパスもMMD用WAVパスも持たせない。
* 解析用WAVはB5以降、MMD用WAVはB7以降で扱う。
* docs更新時にも、B3では入力音声の識別までと明記する。

### Risk 5: onefile展開先とrepo配置を混同する

対策:

* repo開発時配置は `FFmpeg\bin`。
* onefile展開先は `sys._MEIPASS\FFmpeg`。
* `build.ps1` / spec はB3で変更しない。
* 配置不整合があればB4以降またはpackaging補正へ送る。

### Risk 6: PATH fallbackが主経路になってしまう

対策:

* 探索優先順を repo配置 → bundled → PATH に固定する。
* PATHはfallback扱いとする。
* PATH使用時の実体パスとversion情報記録はB4以降に送る。

### Risk 7: `.gitignore` を変更してしまう

対策:

* `.gitignore` はユーザー側管理とする。
* Antigravityは `.gitignore` を作成・変更しない。
* 完了前に `git diff -- .gitignore` を確認する。

### Risk 8: docs更新が広がりすぎる

対策:

* B3で更新するdocsは原則 `docs/repo_milestone.md` と `docs/Version_Control.md` のみ。
* README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは変更しない。
* エンドユーザー向け説明更新はB6またはB9へ送る。

---

## 14. Antigravity 実装時の注意

以下のプロンプトを Antigravity に渡して実施する。

```text
今回は MS17-B3 です。

目的:
FFmpeg / ffprobe locator と音声入力拡張の前提基盤を最小実装してください。

重要:
- 対象branchは feature/MS17 です。
- B3では ffmpeg / ffprobe の探索と入力音声種別判定までを扱います。
- ffmpeg / ffprobe の実行は行わないでください。
- ffmpeg.exe -version / ffprobe.exe -version は実行しないでください。
- ffprobe検査は実装しないでください。
- ffmpeg変換は実装しないでください。
- 解析用WAV生成は実装しないでください。
- MMD用WAV出力は実装しないでください。
- mp3 / m4a を完全対応扱いしないでください。
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

src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/core/audio_processing.py
MMD_AutoLipTool.spec
build.ps1
docs/repo_milestone.md
docs/Version_Control.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Implementation_Plan/MS17-B1_Implementation_Plan.md
docs/Implementation_Plan/MS17-B2_Implementation_Plan.md

実装対象:

src/core/ffmpeg_locator.py
src/core/audio_input.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py

実装内容:

1. src/core/ffmpeg_locator.py を追加してください。
   - ffmpeg.exe / ffprobe.exe の探索を実装してください。
   - 探索順は以下です。
     1. repo直下 FFmpeg\bin
     2. PyInstaller onefile 展開先 sys._MEIPASS\FFmpeg
     3. PATH
   - PATHはfallback扱いにしてください。
   - 見つかった実体パスと探索元を返せる構造にしてください。
   - ffmpeg / ffprobe の片方だけ見つかった場合も表現できるようにしてください。
   - subprocessは使わないでください。
   - ffmpeg / ffprobe は実行しないでください。
   - version取得は行わないでください。

2. src/core/audio_input.py を追加してください。
   - 入力音声ファイル情報を表す dataclass を追加してください。
   - .wav / .mp3 / .m4a の拡張子判定を実装してください。
   - 大文字小文字混在の拡張子を許容してください。
   - 未対応拡張子を拒否してください。
   - 入力音声と解析用WAV、MMD用WAVを混同しない命名にしてください。
   - B3では解析用WAVパスやMMD用WAVパスを持たせないでください。

3. tests/test_ms17_b3_ffmpeg_locator.py を追加してください。
   - repo直下探索
   - bundled探索
   - PATH fallback
   - 片方のみ存在
   - 両方なし
   - 探索優先順
   を確認してください。

4. tests/test_ms17_b3_audio_input_foundation.py を追加してください。
   - .wav / .mp3 / .m4a 判定
   - 大文字小文字混在
   - 未対応拡張子拒否
   - AudioInputInfo の保持内容
   - 解析用WAVやMMD用WAVを持たないこと
   を確認してください。

5. 既存WAV経路を壊さないでください。
   - selected_wav_path
   - selected_wav_analysis
   - analyze_wav_file
   - load_waveform_preview
   - Playback
   - Preview
   - VMD保存可能状態
   の既存意味を変更しないでください。

実行するテスト:

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py

必要に応じて、既存WAV経路確認として以下を限定実行してもよいです。

.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py

全体pytestは、ハング可能性がある場合は実行しないでください。

実装後、必要最小限で以下を更新してください。

docs/repo_milestone.md
docs/Version_Control.md

記録内容:
- MS17-B3を実施したこと
- ffmpeg_locatorを追加したこと
- audio_inputを追加したこと
- ffmpeg / ffprobeは実行していないこと
- mp3 / m4aは種別判定までであり完全対応ではないこと
- B4では ffprobe検査・入力制限・エラー分類へ進むこと

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
5. 実装したlocator仕様
6. 実装した音声入力種別判定仕様
7. 既存WAV経路への影響
8. 実行したテスト
9. 実行していないテスト
10. 変更していないファイル
11. .gitignoreを変更していないこと
12. B4への引き継ぎ
13. 未解決・要確認事項
```

---

## 15. 完了報告テンプレート

Antigravityは、完了時に以下の形式で報告する。

```text
MS17-B3 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 追加したファイル
- src/core/ffmpeg_locator.py:
- src/core/audio_input.py:
- tests/test_ms17_b3_ffmpeg_locator.py:
- tests/test_ms17_b3_audio_input_foundation.py:

4. 変更したファイル
- docs/repo_milestone.md:
- docs/Version_Control.md:

5. 実装したlocator仕様
- repo直下探索:
- bundled探索:
- PATH fallback:
- 片方のみ検出:
- 両方未検出:
- ffmpeg / ffprobe実行有無:
- version取得有無:

6. 実装した音声入力種別判定仕様
- .wav:
- .mp3:
- .m4a:
- 大文字小文字:
- 未対応拡張子:
- AudioInputInfoの保持内容:
- 解析用WAV / MMD用WAVとの分離:

7. 既存WAV経路への影響
- selected_wav_path:
- selected_wav_analysis:
- analyze_wav_file:
- load_waveform_preview:
- Playback:
- Preview:
- VMD保存可能状態:

8. 実行したテスト
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py:
- その他:

9. 実行していないテスト
- 全体pytest:
- 理由:

10. 変更していないファイル
- README.md:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:

11. 禁止事項の確認
- ffmpeg.exe 実行:
- ffprobe.exe 実行:
- version取得:
- ffprobe検査:
- ffmpeg変換:
- 解析用WAV生成:
- MMD用WAV出力:
- Qt / PySide6再導入:

12. B4への引き継ぎ
- ffprobe検査:
- 入力ファイルサイズ上限 500MB:
- 音声長上限 15分:
- エラー分類:
- version取得:
- GUIエラー表示:

13. 未解決・要確認事項
- ...
```

---

## 16. MS17-B4への引き継ぎ条件

MS17-B4へ進む場合、B3から以下を引き継ぐ。

```text
- ffmpeg / ffprobe locator の探索結果構造
- repo直下 / bundled / PATH fallback の source分類
- ffmpeg / ffprobe の片方だけ見つかった場合の扱い
- PATH fallback 使用時の実体パス記録方針
- AudioInputInfo の構造
- .wav / .mp3 / .m4a の種別判定
- 未対応拡張子拒否の仕様
- mp3 / m4a はまだ完全対応ではないこと
- ffmpeg / ffprobe はB3では実行していないこと
```

MS17-B4では、以下へ進む。

```text
MS17-B4: ffprobe検査 + 入力制限 + エラー分類基盤
```

B4で扱う候補。

```text
- ffprobe実行ラッパー
- ffprobe version取得
- ffprobe timeout
- ffprobe失敗時エラー分類
- ffprobe未検出エラー
- 音声streamなしエラー
- 非対応形式エラー
- 壊れた音声ファイルエラー
- 入力ファイルサイズ上限 500MB
- 音声長上限 15分
- GUI表示用エラーメッセージ
```

B4でも引き続き、以下を守る。

```text
- 解析用WAV生成はB5へ送る
- MMD用WAV出力はB7へ送る
- 300秒確認ダイアログはB8へ送る
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わない
- Qt / PySide6 は再導入しない
```
