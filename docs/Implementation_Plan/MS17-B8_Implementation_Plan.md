# MS17-B8 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B8
- Block name: GUI状態・Busy・長時間処理確認・worker結果破棄統合
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B8_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE / agent environment: Codex
- Coding AI: Codex
- Shell: Windows PowerShell
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作業種別: 実装
- 実装変更: あり
- GUI変更: あり
- GUI大規模再設計: 禁止
- worker化対象:
  - ffprobe検査
  - 解析用WAV生成
  - MMD用WAV出力
- キャンセル方針:
  - ffmpeg / ffprobe プロセスはキャンセル要求時に `terminate`
  - 一定時間後に残っていれば `kill`
  - キャンセル後に返ってきた結果は破棄する
- 300秒確認ダイアログ:
  - ffprobe完了後、`AudioProbeResult.duration_sec > 300.0` の場合に表示
  - ffmpeg変換開始前に確認する
- Busy中に無効化する操作:
  - 音声読み込み
  - MMD用WAV出力
  - VMD保存
  - 解析実行
  - TEXT / 音声 / パラメータ変更系の主要操作
- 古いworker結果破棄:
  - 音声入力ジョブごとに `audio_job_id` を発行
  - callback時に現在の `audio_job_id` と一致しない結果を破棄する
- Busy表示とキャンセル導線:
  - ステータス表示
  - 既存操作ボタン無効化
  - 「キャンセル」ボタン追加

---

## 2. 背景

MS17では、wav / mp3 / m4a 入力対応、FFmpeg / ffprobe 接続、解析用WAV生成、MMD用WAV出力を段階的に追加している。

MS17-B3では、FFmpeg / ffprobe locator と入力音声種別判定基盤を追加した。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
````

MS17-B4では、ffprobe検査、入力制限、音声エラー分類基盤を追加した。

```text
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
```

MS17-B5では、ffmpegによる解析用WAV生成基盤を追加した。

```text
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
```

MS17-B6では、wav / mp3 / m4a 入力導線をGUIへ統合した。

```text
ファイル選択
→ 拡張子判定
→ ffprobe検査
→ 解析用WAV生成
→ 波形表示
→ 解析可能状態へ更新
```

MS17-B7では、MMD用WAV出力基盤を追加した。

```text
- 専用の「MMD用WAV出力」ボタン
- MMD用WAV仕様: PCM signed 16-bit little-endian / 44100 Hz / stereo
- 入力元: ユーザーが選択した元音声ファイル
- ffprobe再検査なし
- B6で保持済みの AudioProbeResult を利用
```

ただし、B6/B7までは、音声読み込み、ffprobe検査、解析用WAV生成、MMD用WAV出力を基本的に同期処理として扱っている。

そのため、長い音声や大きいファイル、FFmpeg / ffprobe の遅延、ユーザー操作による状態変更が重なると、以下の問題が起こり得る。

```text
- GUIが固まる
- 処理中に別操作が行われ、状態が不整合になる
- 古いworker結果が現在の入力結果として反映される
- キャンセルできない
- ffmpeg / ffprobe プロセスが残る
- 長時間処理前のユーザー確認がない
```

MS17-B8では、これらをまとめて扱い、GUI状態・Busy・長時間処理確認・worker結果破棄を統合する。

---

## 3. 目的

MS17-B8の目的は、MS17で追加した音声変換系処理を、wxPython GUI上で安全に実行できる状態へ整えることである。

具体的には、以下を達成する。

1. ffprobe検査をworker化する。
2. 解析用WAV生成をworker化する。
3. MMD用WAV出力をworker化する。
4. worker実行中はBusy状態として扱う。
5. Busy中は、状態不整合を起こし得る主要操作を無効化する。
6. 「キャンセル」ボタンを追加する。
7. キャンセル要求時、ffmpeg / ffprobe プロセスに `terminate` を送る。
8. 一定時間後に残っていれば `kill` する。
9. キャンセル後に返ってきたworker結果は破棄する。
10. 音声入力ジョブごとに `audio_job_id` を発行し、古いworker結果を現在状態へ反映しない。
11. ffprobe完了後、音声長が300秒を超える場合、ffmpeg変換開始前に確認ダイアログを表示する。
12. TEXT / 音声 / パラメータ変更時に、現在jobを無効化し、古い結果が混入しないようにする。
13. B9 closeoutに向けて、音声拡張全体の状態管理を安定させる。

---

## 4. In Scope

MS17-B8で行う作業は以下に限定する。

### 4.1 worker化対象

B8でworker化する対象は以下。

```text
- ffprobe検査
- 解析用WAV生成
- MMD用WAV出力
```

具体的には、B4〜B7で追加された次の処理をGUIスレッドから直接実行しないようにする。

```text
probe_audio_file
convert_to_analysis_wav
export_mmd_wav
```

ただし、B8では Whisper解析そのものやVMD生成処理のworker化は行わない。

Whisper解析やVMD生成のworker化が必要な場合は、B9またはMS18以降で検討する。

### 4.2 Busy状態管理

GUIにBusy状態を追加・統合する。

Busy中は、以下を無効化する。

```text
- 音声読み込み
- MMD用WAV出力
- VMD保存
- 解析実行
- TEXT変更系操作
- 音声変更系操作
- 解析パラメータ変更系操作
```

ただし、以下は可能な限り残す。

```text
- キャンセル操作
- ウィンドウの基本操作
- 必要最低限の表示更新
```

Busy中の表示は、ステータス表示とボタン状態で表す。

### 4.3 キャンセル導線

GUIに「キャンセル」ボタンを追加する。

方針。

```text
- worker実行中のみ有効化する
- worker実行中でない場合は無効化する
- キャンセル要求後は「キャンセル中」相当の状態にする
- 連打しても状態が壊れないようにする
```

B8では、モーダル進捗ダイアログではなく、既存GUI上のステータス表示 + ボタン制御で実装する。

### 4.4 ffmpeg / ffprobe プロセス停止

キャンセル要求時、ffmpeg / ffprobe プロセスに対して以下を行う。

```text
1. terminate を試みる
2. 一定時間待つ
3. まだ終了していなければ kill を試みる
4. 結果callbackが返ってきても、キャンセル済みまたは古いjobなら破棄する
```

terminate後の待機時間候補。

```text
PROCESS_TERMINATE_GRACE_SEC = 2.0
```

この値はB8で定数化する。

Windows環境では、プロセス終了の挙動に差が出る可能性があるため、テストでは実プロセスに依存せず fake process / mock process を使う。

### 4.5 300秒確認ダイアログ

B8では、300秒を超える音声に対して、ffmpeg変換開始前に確認ダイアログを出す。

条件。

```text
AudioProbeResult.duration_sec > 300.0
```

表示タイミング。

```text
ffprobe完了後
解析用WAV生成またはMMD用WAV出力のffmpeg変換開始前
```

ユーザーが続行を選んだ場合。

```text
- ffmpeg変換を開始する
```

ユーザーがキャンセルを選んだ場合。

```text
- ffmpeg変換を開始しない
- 現在jobをキャンセル扱いにする
- 古い解析結果を有効扱いしない
- statusにキャンセルを表示する
```

注意。

```text
- 300秒確認は「強制停止」ではない
- 15分上限とは別仕様である
- 15分上限はB4の入力制限
- 300秒確認はB8の長時間処理確認
- `DEFAULT_FFMPEG_TIMEOUT_SEC = 300.0` はffmpeg実行timeoutであり、
  音声長300秒確認とは別概念である
```

### 4.6 audio_job_id による世代管理

B8では、音声入力ジョブごとに `audio_job_id` を発行する。

目的。

```text
- 古いworker結果を現在状態へ反映しない
- キャンセル済みjobの結果を破棄する
- TEXT / 音声 / パラメータ変更時に現在jobを無効化する
```

基本方針。

```text
- 音声読み込み開始時に新しい audio_job_id を発行する
- ffprobe worker / 解析用WAV生成 worker は同じ audio_job_id を持つ
- callback時に callback側の audio_job_id と現在の audio_job_id を比較する
- 一致しない場合は結果を破棄する
- キャンセル済みの場合も結果を破棄する
```

MMD用WAV出力については、B6で読み込まれた音声状態に紐づくため、同じ `audio_job_id` または `mmd_wav_job_id` を使う選択肢がある。

B8では初期実装として、`audio_job_id` を主軸に扱う。
必要に応じて、内部的に `current_worker_job_id` を併用してもよい。

### 4.7 TEXT / 音声 / パラメータ変更時のjob無効化

以下の操作が行われた場合、現在の `audio_job_id` を無効化する。

```text
- TEXT変更
- 音声変更
- 解析パラメータ変更
```

無効化時に行うこと。

```text
- 現在jobをcancelledまたはinvalid扱いにする
- 実行中プロセスがあればキャンセル要求を出す
- current_timing_planを無効化する
- Previewをクリアする
- VMD保存不可にする
- selected_source_event_indexをクリアする
```

ただし、具体的な既存メソッド名はrepo状態に従う。

### 4.8 worker結果破棄

worker callback時に、以下の条件なら結果を破棄する。

```text
- callback側の audio_job_id が現在の audio_job_id と一致しない
- jobがcancelled状態である
- jobがinvalidated状態である
- アプリ側がすでに別の音声入力状態になっている
```

破棄時の方針。

```text
- GUI状態を成功扱いにしない
- 波形表示を更新しない
- 解析結果を有効扱いしない
- VMD保存可能状態を有効にしない
- statusには必要最小限の情報だけ表示する
```

破棄はエラーではなく、状態整合のための正常動作として扱う。

### 4.9 テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_long_audio_confirmation.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py
```

必要に応じて、既存のGUIテスト構成に合わせてファイル名を調整する。

---

## 5. Out of Scope

MS17-B8では以下を行わない。

```text
- Whisper解析本体のworker化
- VMD生成処理のworker化
- VMD writer仕様変更
- VMD出力対象の変更
- MMD用WAV仕様変更
- 解析用WAV仕様変更
- wav / mp3 / m4a 入力仕様変更
- MMD用WAVのVMD保存時同時出力への変更
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
ただし、B8完了時点でREADMEの記載と実装が大きく矛盾する場合は、B8完了報告に「B9で要更新」として明記する。

---

## 6. 前提条件

MS17-B8は、以下を前提とする。

```text
- 作業branchは feature/MS17 である
- MS17-B1 が完了済みである
- MS17-B2 が完了済みである
- MS17-B3 が完了済みである
- MS17-B4 が完了済みである
- MS17-B5 が完了済みである
- MS17-B6 が完了済みである
- MS17-B7 が完了済みである
```

B3から引き継ぐ仕様。

```text
- ffmpeg / ffprobe locator が存在する
- .wav / .mp3 / .m4a の入力種別判定が存在する
```

B4から引き継ぐ仕様。

```text
- ffprobe runner が存在する
- AudioProbeResult が存在する
- 音声長上限15分が存在する
- 音声エラー分類が存在する
```

B5から引き継ぐ仕様。

```text
- 解析用WAV生成基盤が存在する
- AnalysisWavResult が存在する
- ffmpeg runner が存在する
```

B6から引き継ぐ仕様。

```text
- wav / mp3 / m4a 入力導線がGUIへ統合されている
- 解析用WAVが波形表示・解析へ接続されている
- 音声読み込み処理は同期処理を基本としている
```

B7から引き継ぐ仕様。

```text
- MMD用WAV出力ボタンが存在する
- MMD用WAV出力は同期処理を基本としている
- MMD用WAV出力はffmpeg実行を伴う
```

B8で固定する仕様。

```text
- ffprobe検査・解析用WAV生成・MMD用WAV出力をworker化する
- キャンセル時は terminate → kill を行う
- 300秒確認は ffprobe完了後・ffmpeg変換開始前に行う
- Busy中は主要操作を無効化する
- audio_job_id により古いworker結果を破棄する
- Busy表示 + 操作無効化 + キャンセルボタンを導入する
```

---

## 7. 対象ファイル

MS17-B8で追加する候補。

```text
src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_long_audio_confirmation.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py
```

MS17-B8で変更する候補。

```text
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
src/gui_wx/analysis_worker.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

MS17-B8で参照するファイル。

```text
src/core/audio_input.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/mmd_wav_export.py
src/core/audio_errors.py
src/core/ffmpeg_locator.py
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

B8では、`build.ps1` / `MMD_AutoLipTool.spec` / `.gitignore` は変更しない。

---

## 8. 実装方針

### 8.1 全体方針

MS17-B8では、音声変換系処理をGUIから安全に扱うためのworker / Busy / cancel / late callback破棄を統合する。

基本方針。

```text
- B8の中心はGUI状態管理とworker管理
- coreの変換仕様は変更しない
- ffprobe / ffmpeg の実行をworkerへ移す
- GUIスレッドで長時間処理を直接実行しない
- 古いworker結果を現在状態へ反映しない
- キャンセル時はプロセス停止と結果破棄を両方行う
```

### 8.2 worker構造

`src/gui_wx/audio_worker.py` を追加する。

責務は以下。

```text
- worker thread の生成
- ffprobe検査worker
- 解析用WAV生成worker
- MMD用WAV出力worker
- worker結果のcallback通知
- worker失敗のcallback通知
- workerキャンセル通知
```

実装方式候補。

```text
- threading.Thread を使う
- wx.CallAfter でGUIスレッドへcallbackする
```

B8では、標準ライブラリ中心の最小実装を推奨する。

`concurrent.futures.ThreadPoolExecutor` を使ってもよいが、キャンセルやプロセス停止の扱いが見えにくくなる場合は、明示的な `threading.Thread` を優先する。

既存実装との関係。

```text
- 現repoには既に `src/gui_wx/analysis_worker.py` が存在する。
- `analysis_worker.py` はリップシンク解析実行用であり、B8の ffprobe / ffmpeg 変換workerとは責務が異なる。
- B8で `audio_worker.py` を新設する場合でも、既存 `AnalysisWorker` の job_id / cancel / Busy 制御と衝突させない。
- 共通化する場合は小さく限定し、Whisper解析本体やVMD生成処理のworker化へ範囲を広げない。
- `MainFrame._current_job_id` / `_cancel_requested` は既存解析workerで使われているため、B8の `audio_job_id` と混同しない。
- 既存解析workerの `_current_job_id` はリップシンク解析専用として残し、B8の音声変換worker世代管理は `current_audio_job_id` などの別名で保持する。
```

### 8.3 worker state構造

`src/gui_wx/worker_state.py` または `ui_state.py` に worker状態を追加する。

推奨は `worker_state.py` を新設すること。

想定構造。

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class AudioWorkerKind(str, Enum):
    PROBE = "probe"
    ANALYSIS_WAV = "analysis_wav"
    MMD_WAV = "mmd_wav"

class AudioWorkerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCARDED = "discarded"

@dataclass
class AudioWorkerState:
    audio_job_id: int
    kind: AudioWorkerKind
    status: AudioWorkerStatus
    message: str = ""
```

ただし、実際の型・配置はrepo状態に従う。

### 8.4 audio_job_id設計

B8では、音声入力ジョブごとに `audio_job_id` を発行する。

推奨実装。

```text
- UiState または AppController に current_audio_job_id を持たせる
- 音声読み込み開始時に increment する
- TEXT / 音声 / パラメータ変更時にも increment または invalidate する
- worker起動時に audio_job_id を渡す
- callback時に一致確認する
- 現repoでは TEXT変更は `MainFrame._open_text_file`、パラメータ変更は `MainFrame._on_param_changed`、音声変更は `AppController.request_open_audio_file` が主な入口であるため、これらの入口から現在の音声worker jobを無効化する。
- `MainFrame._current_job_id` は既存 `AnalysisWorker` 用のIDであり、音声workerの `audio_job_id` として再利用しない。
```

callback時の判定。

```python
if result.audio_job_id != self.ui_state.current_audio_job_id:
    discard_result()
    return
```

キャンセル済み判定。

```python
if self.ui_state.audio_worker_status in ("cancelling", "cancelled"):
    discard_result()
    return
```

この判定により、遅れて返ってきたworker結果を現在状態へ反映しない。

### 8.5 ffprobe worker

ffprobe workerは、B4の `probe_audio_file` をworker内で実行する。

入力。

```text
- audio_job_id
- input_path
- ffprobe_path
```

出力。

```text
- AudioProbeResult
```

失敗時。

```text
- AudioProbeError または AudioErrorInfo
```

GUI callback。

```text
- 成功時: audio_job_id確認後、解析用WAV生成へ進む
- 失敗時: audio_job_id確認後、エラー表示・Busy解除
- 古いjob: 破棄
```

### 8.6 解析用WAV生成worker

解析用WAV生成workerは、B5の `convert_to_analysis_wav` をworker内で実行する。

入力。

```text
- audio_job_id
- source_path
- ffmpeg_path
- probe_result
```

出力。

```text
- AnalysisWavResult
```

失敗時。

```text
- AudioProbeError または AudioErrorInfo
```

GUI callback。

```text
- 成功時: audio_job_id確認後、波形表示・解析へ接続
- 失敗時: audio_job_id確認後、エラー表示・Busy解除
- 古いjob: 破棄
```

### 8.7 MMD用WAV出力worker

MMD用WAV出力workerは、B7の `export_mmd_wav` をworker内で実行する。

入力。

```text
- audio_job_id
- source_path
- output_path
- ffmpeg_path
- selected_audio_probe
```

出力。

```text
- MmdWavExportResult
```

失敗時。

```text
- AudioProbeError または AudioErrorInfo
```

GUI callback。

```text
- 成功時: audio_job_id確認後、status更新
- 失敗時: audio_job_id確認後、エラー表示・Busy解除
- 古いjob: 破棄
```

MMD用WAV出力失敗時は、既存の解析結果・Preview・VMD保存可能状態を過剰に無効化しない。

### 8.8 プロセス停止対応

B8では、ffmpeg / ffprobe プロセスをキャンセルできるようにする。

現repoの `ffmpeg_runner.py` / `ffprobe_runner.py` は `subprocess.run` を使っているため、プロセスハンドルを外部からterminateしづらい。

そのため、B8では必要に応じて以下へ変更する。

```text
- subprocess.run から subprocess.Popen ベースへ移行する
- Popen オブジェクトを worker が保持する
- cancel要求時に worker が process.terminate() を呼ぶ
- 一定時間後に process.kill() を呼ぶ
```

ただし、大規模なrunner再設計は避ける。

推奨方針。

```text
- 既存run関数は後方互換のため残す
- worker用に cancellable runner を追加する
```

関数候補。

```python
def run_ffprobe_json_cancellable(..., cancel_token: CancelToken) -> FfprobeRunResult:
    ...

def run_ffmpeg_analysis_wav_cancellable(..., cancel_token: CancelToken) -> FfmpegRunResult:
    ...

def run_ffmpeg_mmd_wav_cancellable(..., cancel_token: CancelToken) -> FfmpegRunResult:
    ...
```

または、worker側でPopenを直接扱ってもよい。
ただし、責務が散らばりすぎないようにする。

### 8.9 CancelToken

B8では、最小限のキャンセル制御として `CancelToken` を追加する。

配置候補。

```text
src/gui_wx/audio_worker.py
または
src/gui_wx/worker_state.py
```

想定構造。

```python
class CancelToken:
    def __init__(self):
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    @property
    def cancel_requested(self) -> bool:
        return self._cancel_requested
```

必要なら `threading.Event` を使う。

```python
class CancelToken:
    def __init__(self):
        self._event = threading.Event()

    def request_cancel(self) -> None:
        self._event.set()

    @property
    def cancel_requested(self) -> bool:
        return self._event.is_set()
```

B8では、複雑なキャンセル階層や複数ジョブ同時キャンセルは扱わない。

### 8.10 Busy中の操作無効化

`main_frame.py` / `app_controller.py` / `ui_state.py` の既存 `update_action_states` 相当を拡張する。

Busy中に無効化する候補。

```text
- 音声読み込みボタン
- MMD用WAV出力ボタン
- VMD保存ボタン
- 解析実行ボタン
- TEXT読み込みボタン
- 解析パラメータ変更UI
- 最近使った音声ファイル選択
```

Busy中に有効化する候補。

```text
- キャンセルボタン
```

必要に応じて、キャンセルボタンは以下の状態にする。

```text
- worker実行中: 有効
- キャンセル要求後: 無効、または「キャンセル中」と表示
- idle: 無効
```

実装時の注意。

```text
- ボタンやメニューの無効化だけに依存しない。
- `MainFrame._open_text_file` はTEXT読み込み処理を直接持つため、busy中はメソッド冒頭でも明示的にreturnする。
- `MainFrame._open_audio_file` / recent file handlers / parameter changed handler も、busy中に状態を変更しないようにガードする。
- Controller側の `request_open_audio_file` / `request_export_mmd_wav` の `is_busy` ガードは維持する。
```

### 8.11 300秒確認ダイアログ

B8では、ffprobe完了後に `duration_sec > 300.0` の場合、確認ダイアログを出す。

実装候補。

```python
def confirm_long_audio_processing(duration_sec: float) -> bool:
    ...
```

表示文言候補。

```text
この音声は300秒を超えています。
変換に時間がかかる可能性があります。
処理を続行しますか？
```

ボタン。

```text
続行
キャンセル
```

キャンセル時。

```text
- ffmpeg変換を開始しない
- Busyを解除する
- 現在jobをキャンセル扱いにする
- 古い解析結果を有効扱いしない
```

注意。

```text
- 15分上限超過はB4で拒否済み
- 300秒確認は300秒超過でも続行可能
- ffmpeg実行timeoutの300秒とは別概念である
```

### 8.12 エラー表示

B8では、worker失敗時のエラー表示を統一する。

方針。

```text
- AudioErrorInfo.message をstatusまたはmessageに表示する
- detailやstderr全文をGUIへ直接表示しない
- キャンセルはエラー扱いにしない
- 古いworker結果破棄はエラー扱いにしない
```

### 8.13 docs更新方針

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

記録する内容。

```text
- MS17-B8を実施したこと
- ffprobe検査・解析用WAV生成・MMD用WAV出力をworker化したこと
- Busy状態を導入したこと
- キャンセルボタンを追加したこと
- キャンセル時に terminate → kill を行う方針にしたこと
- audio_job_id による古いworker結果破棄を実装したこと
- 300秒超過時の確認ダイアログをffmpeg変換前に出すこと
- B9では統合テスト・docs補正・MS17 closeoutへ進むこと
```

README、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは原則変更しない。
B9でMS17全体closeout時に更新する。

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
- MS17-B7完了commitまたは記録があるか
- B8開始前に意図しない差分がないか
```

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。

### Step 2: B3〜B7成果確認

以下を確認する。

```text
src/core/audio_input.py
src/core/ffmpeg_locator.py
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/mmd_wav_export.py
src/gui_wx/analysis_worker.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

確認観点。

```text
- probe_audio_file が存在するか
- convert_to_analysis_wav が存在するか
- export_mmd_wav が存在するか
- ffmpeg / ffprobe runner が存在するか
- B6の音声読み込み導線が存在するか
- B7のMMD用WAV出力導線が存在するか
- B8へ進む記録があるか
```

### Step 3: worker状態構造を追加

`src/gui_wx/worker_state.py` を追加する、または `ui_state.py` に最小追加する。

推奨追加。

```text
AudioWorkerKind
AudioWorkerStatus
AudioWorkerState
```

必要に応じて `CancelToken` も追加する。

### Step 4: audio_job_id管理を追加

`ui_state.py` または `app_controller.py` に `current_audio_job_id` を追加する。

実装方針。

```text
- 新規音声読み込み開始時にincrement
- TEXT変更時にinvalidate
- 音声変更時にinvalidate
- パラメータ変更時にinvalidate
- worker callback時に一致確認
```

テストで確認すること。

```text
- 新規jobでidが進む
- 古いidのcallbackが破棄される
- cancel後のcallbackが破棄される
```

### Step 5: `src/gui_wx/audio_worker.py` 追加

`audio_worker.py` を追加する。

最低限含める候補。

```text
AudioWorkerResult
AudioWorkerError
start_probe_worker
start_analysis_wav_worker
start_mmd_wav_worker
CancelToken
```

または、クラスベースで以下を実装する。

```text
AudioWorkerController
```

実装方針。

```text
- threading.Thread を使う
- GUI更新は wx.CallAfter で行う
- worker内ではGUIオブジェクトを直接触らない
- callbackには audio_job_id を必ず含める
```

### Step 6: ffprobe workerへ接続

B6の音声読み込み処理で、同期 `probe_audio_file` 呼び出しをworker呼び出しへ置き換える。

処理順。

```text
1. 音声読み込み開始
2. audio_job_id発行
3. 既存解析結果無効化
4. AudioInputInfo作成
5. ffprobe worker開始
6. Busy状態へ移行
7. ffprobe成功callback
8. audio_job_id一致確認
9. 300秒確認
10. 解析用WAV生成worker開始
```

### Step 7: 解析用WAV生成workerへ接続

B6の解析用WAV生成処理をworker化する。

処理順。

```text
1. ffprobe成功後、必要に応じて300秒確認
2. ffmpeg path確認
3. 解析用WAV生成worker開始
4. 成功callback
5. audio_job_id一致確認
6. AnalysisWavResult保存
7. analysis_wav_pathを波形表示・解析へ接続
8. Busy解除
```

失敗時。

```text
- audio_job_id一致確認
- エラー表示
- 古い解析結果を有効扱いしない
- Busy解除
```

### Step 8: MMD用WAV出力workerへ接続

B7のMMD用WAV出力処理をworker化する。

処理順。

```text
1. MMD用WAV出力ボタン押下
2. selected_analysis_wav / selected_audio_input / selected_audio_probe確認
3. 保存ダイアログ
4. 上書き確認
5. 必要に応じて300秒確認
6. MMD用WAV出力worker開始
7. Busy状態へ移行
8. 成功callback
9. audio_job_id一致確認
10. status更新
11. Busy解除
```

MMD用WAV出力失敗時は、既存の解析結果やPreviewを過剰に無効化しない。

### Step 9: cancellable runner 対応

`ffprobe_runner.py` / `ffmpeg_runner.py` を必要最小限で拡張する。

方針。

```text
- 既存関数を壊さない
- worker用にcancellable関数を追加する
- subprocess.Popen を使う
- CancelToken を監視する
- cancel要求時に terminate → kill
```

テストでは、実プロセスではなく fake process / mock Popen を使う。

### Step 10: キャンセルボタン追加

`main_frame.py` に「キャンセル」ボタンを追加する。

表示候補。

```text
キャンセル
```

有効化条件。

```text
- worker実行中: 有効
- キャンセル要求中: 無効、または「キャンセル中」
- idle: 無効
```

ボタン押下時。

```text
- AppController.request_cancel_current_audio_job() を呼ぶ
```

### Step 11: Busy中のaction state更新

`update_action_states` 相当の処理を拡張する。

Busy中に無効化するもの。

```text
- 音声読み込み
- MMD用WAV出力
- VMD保存
- 解析実行
- TEXT読み込み
- 解析パラメータ変更
- 最近使った音声ファイル読み込み
```

Busy中に有効化するもの。

```text
- キャンセルボタン
```

テストで、Busy中の各ボタン状態を確認する。

### Step 12: 300秒確認ダイアログ追加

`app_controller.py` または `main_frame.py` に確認処理を追加する。

推奨。

```text
- ダイアログ表示はMainFrame側
- 判定はAppController側
```

処理。

```text
if probe_result.duration_sec > 300.0:
    if not confirm_long_audio_processing(duration_sec):
        cancel job
        return
```

テストでは、confirm callback を注入して、GUIダイアログを実表示せずに判定する。

### Step 13: late callback破棄

全worker callbackに `audio_job_id` 一致確認を入れる。

対象。

```text
- ffprobe成功callback
- ffprobe失敗callback
- 解析用WAV生成成功callback
- 解析用WAV生成失敗callback
- MMD用WAV出力成功callback
- MMD用WAV出力失敗callback
```

破棄時。

```text
- GUI状態を更新しない
- 成功扱いしない
- 必要に応じてdebug logまたはstatusに最小表示
```

### Step 14: テスト追加

以下のテストを追加する。

```text
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_long_audio_confirmation.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py
```

テスト内容。

```text
- worker開始でBusyになる
- worker完了でBusy解除される
- キャンセル要求でstatusがcancellingになる
- ffmpeg / ffprobe cancel時に terminate → kill が呼ばれる
- 300秒超過で確認が呼ばれる
- 300秒以下では確認が呼ばれない
- 確認キャンセル時にffmpeg変換が開始されない
- Busy中に主要操作が無効化される
- キャンセルボタンはBusy中のみ有効
- 古いaudio_job_idの結果が破棄される
- cancel済みjobの結果が破棄される
```

### Step 15: B3〜B7回帰テスト

必要に応じて、B3〜B7の限定テストを再実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

現repoには `tests/test_ms17_b6_*` 形式の専用テストは存在しない。
B6導線の回帰確認は、既存の wx 系入力・保存統合テストを実在ファイル名で指定する。

### Step 16: B8限定テスト実行

以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

既存GUI関連の回帰確認として、必要に応じて以下を限定実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

全体pytestは、既知のハング可能性がある場合は実行しない。

### Step 17: docs更新

実装完了後、必要最小限で以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

記録内容。

```text
- MS17-B8を実施したこと
- ffprobe検査・解析用WAV生成・MMD用WAV出力をworker化したこと
- Busy状態を導入したこと
- キャンセルボタンを追加したこと
- キャンセル時に terminate → kill を行う方針にしたこと
- audio_job_id による古いworker結果破棄を実装したこと
- 300秒超過時の確認ダイアログをffmpeg変換前に出すこと
- B9では統合テスト・docs補正・MS17 closeoutへ進むこと
```

READMEはB9でMS17全体closeout時に更新する方針とする。

### Step 18: 完了前diff確認

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
src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py
src/core/ffprobe_runner.py
src/core/ffmpeg_runner.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_long_audio_confirmation.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
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

READMEに差分が出ている場合は、B8で必要最小限の更新か、B9へ送るべき更新かを報告で明確にする。

---

## 10. 状態遷移 / データ契約

### 10.1 B8で追加する状態契約

B8では、音声変換系workerの状態を追加する。

最低限の状態。

```text
idle
running
cancelling
cancelled
completed
failed
discarded
```

対象worker種別。

```text
probe
analysis_wav
mmd_wav
```

### 10.2 audio_job_id契約

B8では、音声入力ジョブの世代管理として `audio_job_id` を追加する。

契約。

```text
- audio_job_id は音声入力ジョブごとに発行する
- worker開始時に audio_job_id を渡す
- worker完了callback時に current_audio_job_id と一致確認する
- 一致しない場合は結果を破棄する
- cancel済みjobの結果も破棄する
```

### 10.3 Busy契約

Busy中は、主要操作を無効化する。

Busy開始。

```text
- ffprobe worker開始時
- 解析用WAV生成worker開始時
- MMD用WAV出力worker開始時
```

Busy終了。

```text
- worker成功後、現在jobとして反映完了
- worker失敗後、現在jobとしてエラー処理完了
- cancel完了
- 結果破棄後、現在実行中jobがない
```

### 10.4 Cancel契約

キャンセル要求時の契約。

```text
- CancelToken に cancel_requested を立てる
- 実行中のffmpeg / ffprobeプロセスに terminate を試みる
- PROCESS_TERMINATE_GRACE_SEC 経過後に残っていれば kill を試みる
- worker callback結果は破棄する
- キャンセルは通常のエラーとは区別する
```

### 10.5 300秒確認契約

300秒確認の契約。

```text
- AudioProbeResult.duration_sec > 300.0 の場合に表示する
- 表示タイミングは ffprobe完了後、ffmpeg変換開始前
- ユーザーが続行した場合のみffmpeg変換へ進む
- ユーザーがキャンセルした場合はffmpeg変換を開始しない
```

### 10.6 B8で変更しない契約

以下はB8では変更しない。

```text
- 解析用WAV仕様
- MMD用WAV仕様
- AudioInputInfo
- AudioProbeResult
- AnalysisWavResult
- MmdWavExportResult
- VMD writer input
- Preview shape contract
- VMD出力対象
```

---

## 11. テスト方針

### 11.1 B8で実行する標準テスト

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

### 11.2 B3〜B7回帰テスト

必要に応じてB3〜B7の限定テストを実行する。

実行候補。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

現repoには `tests/test_ms17_b6_*` 形式の専用テストは存在しない。
B6導線の回帰確認は、既存の wx 系入力・保存統合テストを実在ファイル名で指定する。

### 11.3 既存GUI回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

### 11.4 実 ffmpeg / ffprobe テスト方針

B8では、実 `ffmpeg.exe` / `ffprobe.exe` を必須テストにしない。

理由。

```text
- worker / cancel / late callback破棄のテストを環境依存にしないため
- Windows環境差でプロセス終了挙動が揺れる可能性があるため
- fake process / mock Popen で terminate → kill を検証するため
```

実プロセスでの確認は、B9統合確認または手動確認へ送る。

### 11.5 全体pytest

全体pytestは、既知のハング可能性がある場合は実行しない。

実行しない場合は、完了報告に理由を書く。

---

## 12. 受け入れ条件

MS17-B8は、以下を満たしたら完了とする。

### 12.1 実装条件

* ffprobe検査がworker化されている。
* 解析用WAV生成がworker化されている。
* MMD用WAV出力がworker化されている。
* Busy状態が導入されている。
* Busy中に主要操作が無効化されている。
* 「キャンセル」ボタンが追加されている。
* キャンセル要求時に ffmpeg / ffprobe プロセスへ `terminate` を試みる。
* 一定時間後に残っていれば `kill` を試みる。
* `audio_job_id` により古いworker結果が破棄される。
* キャンセル済みworker結果が破棄される。
* 300秒を超える音声では、ffmpeg変換開始前に確認ダイアログが出る。
* 300秒以下の音声では確認ダイアログが出ない。
* 確認キャンセル時にffmpeg変換が開始されない。
* TEXT / 音声 / パラメータ変更時に現在jobが無効化される。
* B3〜B7で確定したデータ契約を壊していない。

### 12.2 禁止事項遵守

以下が守られている。

```text
- Whisper解析本体のworker化をしていない
- VMD生成処理のworker化をしていない
- VMD保存処理を変更していない
- VMD出力対象を変更していない
- MMD用WAV仕様を変更していない
- 解析用WAV仕様を変更していない
- 音量正規化をしていない
- 無音トリムをしていない
- 自動フェードをしていない
- 自動ノイズ除去をしていない
- cache自動削除をしていない
- FFmpeg / ffprobe 自動ダウンロードをしていない
- build.ps1を変更していない
- MMD_AutoLipTool.specを変更していない
- .gitignoreを変更していない
- Qt / PySide6を再導入していない
```

### 12.3 テスト条件

以下が成功している。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

必要に応じて実行したB3〜B7回帰テスト、既存GUI回帰テストの結果が報告されている。

全体pytestを実行しなかった場合は、その理由が報告されている。

実施後確認:

```text
- B8追加pytest: 11 passed
- B7関連回帰pytest: 14 passed
- B4/B5 runner関連回帰pytest: 13 passed
- 既存入力導線pytest: 2 passed
- ユーザー手動テスト: 通過
```

### 12.4 docs条件

以下が必要最小限で更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

記録上、B8の範囲が以下として明確である。

```text
- ffprobe検査・解析用WAV生成・MMD用WAV出力のworker化
- Busy状態
- キャンセルボタン
- terminate → kill
- audio_job_idによる古いworker結果破棄
- 300秒確認ダイアログ
- B9で統合テスト・docs補正・MS17 closeoutへ進む
```

---

## 13. リスクと対策

### Risk 1: worker結果が古い状態へ反映される

対策。

```text
- audio_job_id を必ずcallbackへ含める
- callback時に current_audio_job_id と一致確認する
- 一致しなければ破棄する
- cancel済みjobも破棄する
```

### Risk 2: キャンセル後にffmpeg / ffprobeプロセスが残る

対策。

```text
- terminate を試みる
- PROCESS_TERMINATE_GRACE_SEC 待つ
- 残っていれば kill を試みる
- テストでは fake process で terminate / kill 呼び出しを確認する
```

### Risk 3: Busy中にユーザー操作で状態が変わる

対策。

```text
- Busy中は主要操作を無効化する
- TEXT / 音声 / パラメータ変更系操作も無効化する
- キャンセルボタンだけ有効化する
```

### Risk 4: 300秒確認と15分上限を混同する

対策。

```text
- 15分上限はB4の入力制限
- 300秒確認はB8の長時間処理確認
- 300秒超過は続行可能
- 900秒超過はB4で拒否
```

### Risk 5: worker化によりGUI更新が別スレッドから行われる

対策。

```text
- workerからGUIを直接触らない
- GUI更新は wx.CallAfter で行う
- テストでcallback経路を分離する
```

### Risk 6: B8で範囲が広がりすぎる

対策。

```text
- worker化対象を ffprobe検査・解析用WAV生成・MMD用WAV出力に限定する
- Whisper解析やVMD生成はB8では扱わない
- cache管理やREADME更新はB9以降へ送る
```

### Risk 7: キャンセル時に状態を壊す

対策。

```text
- キャンセルはエラーとは区別する
- キャンセル後の結果は破棄する
- 既存の成功状態へ反映しない
- 必要に応じて状態を安全側へ戻す
```

### Risk 8: READMEと実装が一時的にずれる

対策。

```text
- B8ではREADME大規模更新を行わない
- B9 closeoutでREADMEをMS17完了状態へ更新する
- B8完了報告にREADME更新必要性を記録する
```

---

## 14. Codex 実装時の注意

以下のプロンプトを Codex に渡して実施する。

```text
今回は MS17-B8 です。

目的:
GUI状態・Busy・長時間処理確認・worker結果破棄を統合してください。

重要:
- 対象branchは feature/MS17 です。
- MS17-B3〜B7 の成果を前提にしてください。
- worker化対象は ffprobe検査・解析用WAV生成・MMD用WAV出力です。
- Whisper解析本体やVMD生成処理のworker化は行わないでください。
- キャンセル要求時、ffmpeg / ffprobe プロセスは terminate し、一定時間後に残っていれば kill してください。
- キャンセル後に返ってきた結果は破棄してください。
- 300秒確認ダイアログは、ffprobe完了後、AudioProbeResult.duration_sec が300秒を超える場合に表示してください。
- 300秒確認はffmpeg変換開始前に出してください。
- Busy中は、音声読み込み、MMD用WAV出力、VMD保存、解析実行、TEXT/音声/パラメータ変更系の主要操作を無効化してください。
- Busy表示はstatus表示とボタン状態で行ってください。
- 「キャンセル」ボタンを追加してください。
- 古いworker結果破棄は audio_job_id で行ってください。
- callback時に現在の audio_job_id と一致しない結果は破棄してください。
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わないでください。
- 解析用WAV仕様、MMD用WAV仕様は変更しないでください。
- VMD保存処理は変更しないでください。
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
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/mmd_wav_export.py
src/gui_wx/analysis_worker.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md

実装候補:

src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py
src/gui_wx/analysis_worker.py
src/core/ffprobe_runner.py
src/core/ffmpeg_runner.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_long_audio_confirmation.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py

実装内容:

1. worker状態構造を追加してください。
   - AudioWorkerKind
   - AudioWorkerStatus
   - AudioWorkerState
   - CancelToken
   などを必要に応じて追加してください。

2. audio_job_id を追加してください。
   - 音声入力ジョブごとに発行してください。
   - 音声読み込み開始時に更新してください。
   - TEXT / 音声 / パラメータ変更時に無効化してください。
   - worker callback時に current_audio_job_id と一致しない結果を破棄してください。

3. ffprobe検査をworker化してください。
   - probe_audio_file をworker内で実行してください。
   - workerからGUIを直接触らず、wx.CallAfter 等でGUI threadに戻してください。
   - 成功/失敗callbackに audio_job_id を含めてください。

4. 解析用WAV生成をworker化してください。
   - convert_to_analysis_wav をworker内で実行してください。
   - ffprobe成功後、必要に応じて300秒確認を行ってから開始してください。
   - callback時に audio_job_id を確認してください。

5. MMD用WAV出力をworker化してください。
   - export_mmd_wav をworker内で実行してください。
   - callback時に audio_job_id を確認してください。
   - 失敗時に既存の解析結果やPreviewを過剰に無効化しないでください。

6. ffmpeg / ffprobe プロセスをキャンセル可能にしてください。
   - 必要に応じて subprocess.run とは別に Popen ベースの cancellable runner を追加してください。
   - キャンセル要求時は terminate を呼んでください。
   - 一定時間後に残っていれば kill を呼んでください。
   - 既存のB4/B5/B7テストを壊さないでください。

7. Busy状態を追加してください。
   - worker実行中はBusyにしてください。
   - Busy中は主要操作を無効化してください。
   - キャンセルボタンだけ有効にしてください。

8. キャンセルボタンを追加してください。
   - worker実行中のみ有効にしてください。
   - キャンセル要求後はキャンセル中状態にしてください。
   - 連打で状態が壊れないようにしてください。

9. 300秒確認ダイアログを追加してください。
   - AudioProbeResult.duration_sec > 300.0 の場合に表示してください。
   - 表示タイミングはffprobe完了後、ffmpeg変換開始前です。
   - ユーザーがキャンセルした場合はffmpeg変換を開始しないでください。
   - 300秒確認は15分上限とは別仕様です。

10. テストを追加してください。
   - tests/test_ms17_b8_audio_worker_state.py
   - tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
   - tests/test_ms17_b8_long_audio_confirmation.py
   - tests/test_ms17_b8_busy_action_states.py
   - tests/test_ms17_b8_late_worker_result_discard.py
   実際のrepoのテスト構成に合わせてファイル名は調整してよいです。

実行するテスト:

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py

必要に応じてB3〜B7回帰テストも実行してください。

全体pytestは、ハング可能性がある場合は実行しないでください。

実装後、必要最小限で以下を更新してください。

docs/repo_milestone.md
docs/Version_Control.md
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS17_Block_Breakdown.md

記録内容:
- MS17-B8を実施したこと
- ffprobe検査・解析用WAV生成・MMD用WAV出力をworker化したこと
- Busy状態を導入したこと
- キャンセルボタンを追加したこと
- キャンセル時に terminate → kill を行う方針にしたこと
- audio_job_id による古いworker結果破棄を実装したこと
- 300秒超過時の確認ダイアログをffmpeg変換前に出すこと
- B9では統合テスト・docs補正・MS17 closeoutへ進むこと

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
5. worker化対象
6. Busy状態
7. キャンセル導線
8. terminate / kill 方針
9. 300秒確認
10. audio_job_id による結果破棄
11. Busy中の操作無効化
12. 実行したテスト
13. 実行していないテスト
14. 変更していないファイル
15. .gitignoreを変更していないこと
16. 禁止事項の遵守
17. B9への引き継ぎ
18. 未解決・要確認事項
```

---

## 15. 完了報告テンプレート

Codexは、完了時に以下の形式で報告する。

```text
MS17-B8 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 変更したファイル
- src/core/ffprobe_runner.py:
- src/core/ffmpeg_runner.py:
- src/gui_wx/main_frame.py:
- src/gui_wx/app_controller.py:
- src/gui_wx/ui_state.py:
- docs/repo_milestone.md:
- docs/Version_Control.md:
- docs/MS17_and_Beyond_Index.md:
- docs/Implementation_Plan/MS17_Block_Breakdown.md:

4. 追加したファイル
- src/gui_wx/audio_worker.py:
- src/gui_wx/worker_state.py:
- tests/test_ms17_b8_audio_worker_state.py:
- tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py:
- tests/test_ms17_b8_long_audio_confirmation.py:
- tests/test_ms17_b8_busy_action_states.py:
- tests/test_ms17_b8_late_worker_result_discard.py:

5. worker化対象
- ffprobe検査:
- 解析用WAV生成:
- MMD用WAV出力:
- Whisper解析:
- VMD生成:

6. Busy状態
- Busy開始条件:
- Busy終了条件:
- status表示:
- action state更新:

7. キャンセル導線
- キャンセルボタン:
- 有効化条件:
- キャンセル中状態:
- 連打対策:

8. terminate / kill 方針
- ffprobe:
- ffmpeg:
- terminate:
- grace秒数:
- kill:
- fake process / mock test:

9. 300秒確認
- 判定条件:
- 表示タイミング:
- 続行時:
- キャンセル時:
- 15分上限との分離:

10. audio_job_id による結果破棄
- 発行タイミング:
- callback比較:
- cancel済み結果:
- TEXT変更時:
- 音声変更時:
- パラメータ変更時:

11. Busy中の操作無効化
- 音声読み込み:
- MMD用WAV出力:
- VMD保存:
- 解析実行:
- TEXT変更:
- 音声変更:
- パラメータ変更:
- キャンセル:

12. 実行したテスト
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py:
- .\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py:
- B3〜B7回帰テスト:
- 既存GUI回帰テスト:

13. 実行していないテスト
- 実ffmpeg / ffprobeテスト:
- 全体pytest:
- 理由:

14. 変更していないファイル
- README.md:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:

15. 禁止事項の確認
- Whisper解析worker化:
- VMD生成worker化:
- VMD保存処理変更:
- 解析用WAV仕様変更:
- MMD用WAV仕様変更:
- 音量正規化:
- 無音トリム:
- 自動フェード:
- 自動ノイズ除去:
- cache自動削除:
- Qt / PySide6再導入:

16. B9への引き継ぎ
- 統合テスト:
- README更新:
- docs closeout:
- 実ffmpeg / ffprobe手動確認:
- 実MMD確認:
- MS17 closeout:

17. 未解決・要確認事項
- ...
```

---

## 16. MS17-B9への引き継ぎ条件

MS17-B9へ進む場合、B8から以下を引き継ぐ。

```text
- ffprobe検査がworker化されていること
- 解析用WAV生成がworker化されていること
- MMD用WAV出力がworker化されていること
- Busy状態が導入されていること
- キャンセルボタンが導入されていること
- キャンセル時に terminate → kill を行う方針であること
- audio_job_id により古いworker結果を破棄すること
- 300秒超過時にffmpeg変換前確認を行うこと
- B8ではREADME大規模更新を行っていないこと
```

MS17-B9では、以下へ進む。

```text
MS17-B9: 統合テスト・docs補正・MS17 closeout
```

B9で扱う候補。

```text
- wav / mp3 / m4a 入力から解析用WAV生成までの統合確認
- 解析用WAVから波形表示・解析・VMD生成までの統合確認
- MMD用WAV出力の統合確認
- Busy / cancel / 300秒確認 / late callback破棄の統合確認
- 実ffmpeg / ffprobe が配置されている環境での手動確認
- 実MMDでのMMD用WAV読み込み確認
- README更新
- repo_milestone更新
- Version_Control更新
- MS17 Block Breakdown更新
- Release Package Manifest更新
- Error Handling Specification更新
- MMD Audio WAV Compatibility Specification更新
- MS17 closeout
```
