# MS18-B4 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B4 Implementation Plan
- 対象ブロック: MS18-B4 Safe Refactor Implementation
- 想定配置先: `docs/Implementation_Plan/MS18-B4_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 基準ブランチ: `feature/MS18`
- 作成日: 2026-06-29
- 文書ステータス: Completed
- 作成目的:
  - MS18-B3で確定したB4許可範囲を、実装時に迷わない粒度へ分解する。
  - B4で扱う変更と、B5/B6/B7へ送る変更を混同しないようにする。

## 2. 背景

MS18-B1では、MS17 closeout後のリリース前状態、`cache/` 追跡対象外化、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の同期状態、release readiness risk inventory を確認した。

MS18-B2では、外部ファイル入力、ffprobe / ffmpeg、subprocess、temp / cache、GUI worker、PyInstaller onefile、release package、FFmpeg license notice をSecurity Preflightとして確認した。P1は検出されず、P2/P3が後続Blockへ分類された。

MS18-B3では、B2で残ったP2/P3をB4で扱う項目と扱わない項目へ分類した。B4で扱ってよい候補は、以下の小規模な挙動非変更改善に限定された。

- PATH fallback時の探索元説明性改善
- `error.log` / 開発コンソールの診断情報扱いの小規模整理

B4は新機能追加ではない。実装は、MS17で完成した音声入力、解析用WAV、MMD用WAV出力、worker状態管理、Preview / waveform、VMD出力仕様を維持したまま行う。

## 3. 目的

MS18-B4の目的は、MS18-B3で許可された範囲に限定して、挙動非変更の安全なリファクタリングを実施することである。

具体的には、FFmpeg / ffprobe 探索結果の説明性と、ローカル診断情報の扱いを最小限整理し、実装とテストで退行を防ぐ。

このBlockでは、release packaging、SmokeLaunch調査、実MMD確認、cache命名変更、pipeline意味論変更は扱わない。

## 4. In Scope

B4で扱う範囲は以下に限定する。

- `src/core/ffmpeg_locator.py` の小規模整理
  - 探索順を変えずに、探索元を説明しやすくする補助関数またはデータ整形を追加する。
  - `FfmpegToolSource` / `FfmpegToolPath` / `FfmpegLocatorResult` の既存契約を壊さない。
  - 自動ダウンロード、環境変数変更、探索対象ディレクトリ追加は行わない。
- `tests/test_ms17_b3_ffmpeg_locator.py` の限定テスト追加
  - repo local / bundled / PATH / not found / partial found の既存探索挙動が維持されることを確認する。
  - 追加した説明用補助関数が、ローカルパスを不用意に露出せず、探索元を判別できることを確認する。
- `src/gui_wx/app_controller.py` の条件付き小修正
  - FFmpeg / ffprobe 未検出時の表示文言または内部メッセージに、探索元説明を安全に反映できる場合のみ変更する。
  - GUI状態遷移、worker起動順、Busy制御、late callback破棄、キャンセル導線は変更しない。
- `src/main.py` / `src/gui_wx/app_controller.py` の条件付き小修正
  - `error.log` と開発コンソール出力の扱いを、ユーザー向け挙動を変えない範囲で整理する。
  - 既存の `error.log` 記録方針を削除しない。
- `docs/Error_Handling_Specification.md` の条件付き更新
  - 診断ログまたはユーザー通知文言を変更した場合のみ、実装状態に合わせて更新する。
- `docs/repo_milestone.md` / `docs/Version_Control.md` のB4完了記録
  - 実装後に、実施内容、テスト、残課題を記録する。

## 5. Out of Scope

B4では以下を扱わない。

- `build.ps1` / `MMD_AutoLipTool.spec` の変更
- `build.ps1 -SmokeLaunch` の残留プロセス調査または修正
- `build.ps1 -Clean` の旧onefile成果物削除仕様変更
- Release package同梱物、除外物、license texts、NOTICE、THIRD_PARTY_LICENSES.md の確定
- FFmpeg build configuration の変更
- FFmpeg / ffprobe の自動ダウンロード
- FFmpeg / ffprobe 探索順の変更
- PATH fallbackの無効化
- cacheファイル名、cache削除ポリシー、配布除外ポリシーの変更
- pipeline の意味論変更
- VMD writer の再設計
- MMD用WAV出力仕様の変更
- Preview / waveform の仕様変更
- GUIレイアウト刷新
- 音声解析品質の変更
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- 英語対応

## 6. 前提条件

B4実装前に、以下を確認する。

- 作業ブランチが `feature/MS18` である。
- `git status --short --branch` で、作業開始時の差分を把握している。
- `docs/MS17_and_Beyond_Index.md` を読んで、現在地がMS18-B4であることを確認している。
- `docs/Implementation_Plan/MS18-B3_Implementation_Plan.md` のB3 Scope Tableを確認している。
- MS18-B1 / B2 / B3は完了済みである。
- B2 / B3でSecurity P1は検出されていない。
- B4へ必須投入すべきP2はない。
- B4は挙動非変更の安全な小規模整理である。

## 7. 対象ファイル

### 7.1 実装対象候補

```text
src/core/ffmpeg_locator.py
src/main.py
src/gui_wx/app_controller.py
```

### 7.2 テスト対象候補

```text
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_wx_ms14_b3_input.py
```

### 7.3 文書更新候補

```text
docs/Error_Handling_Specification.md
docs/repo_milestone.md
docs/Version_Control.md
```

### 7.4 参照専用候補

```text
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-B3_Implementation_Plan.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
```

## 8. 実装方針

### 8.1 基本方針

- 変更はB3で許可されたファイルと論点に限定する。
- 既存の探索順、PATH fallback、未検出時の扱いを変更しない。
- 追加する関数は、探索結果を「説明する」ための補助に留める。
- ユーザー向け表示にローカル絶対パスを不用意に出さない。
- 既存テストを弱めない。
- GUI workerや状態遷移に触れる場合は、対象テストを追加または実行する。

### 8.2 推奨実装単位

#### B4-001: FFmpeg / ffprobe 探索元説明補助

`src/core/ffmpeg_locator.py` に、探索結果のソースを表示・診断向けに整形する純粋関数を追加する。

想定例:

```text
format_tool_source(...)
format_locator_status(...)
```

名称は実装時に既存コードへ合わせてよい。ただし、以下を満たすこと。

- 入力は既存の `FfmpegToolPath` / `FfmpegLocatorResult` を中心にする。
- 出力はテストしやすい文字列または小さな構造化値にする。
- repo local / bundled / PATH / not found を区別できる。
- 既存の `_find_tool` の探索順を変更しない。
- `shutil.which` の呼び出し条件を変更しない。

#### B4-002: 未検出時メッセージの限定改善

`src/gui_wx/app_controller.py` のFFmpeg / ffprobe未検出メッセージに、B4-001の補助情報を反映できるか確認する。

反映する場合も、以下を守る。

- ユーザー向け文言は簡潔にする。
- ローカル絶対パスを過剰に表示しない。
- 既存の例外発生箇所、状態クリア、MessageBox表示、worker起動可否を変更しない。
- GUIテストが重くなる場合は、core側の補助関数を優先し、GUI反映は保留してよい。

#### B4-003: 診断情報扱いの小規模整理

`src/main.py` と `src/gui_wx/app_controller.py` の `error.log` / 開発コンソール出力を確認し、明らかに重複または過剰な箇所だけ整理する。

実装する場合も、以下を守る。

- `error.log` への記録方針を削除しない。
- ユーザー向けダイアログにtraceback全文を出さない。
- 予期しない例外の開発者向け診断性を完全に失わせない。
- 起動失敗時のstderr出力と `error.log` 書き込みを破壊しない。

この項目はB4-001より優先度が低い。安全に確認できない場合は、B4では実装しない判断をしてよい。

## 9. 詳細ステップ

### Step 1: 事前確認

```powershell
git status --short --branch
git branch
git log --oneline -n 10
```

続いて、以下を確認する。

```text
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS18-B3_Implementation_Plan.md
src/core/ffmpeg_locator.py
tests/test_ms17_b3_ffmpeg_locator.py
src/gui_wx/app_controller.py
src/main.py
```

### Step 2: B4-001を実装

- `ffmpeg_locator.py` に探索元説明用の小さな補助関数を追加する。
- 既存データ構造を破壊しない。
- `_find_tool` と `locate_ffmpeg_tools` の探索挙動を変更しない。

### Step 3: B4-001のテストを追加

- `tests/test_ms17_b3_ffmpeg_locator.py` に、追加した補助関数のテストを加える。
- repo local / bundled / PATH / not found の既存テストを維持する。
- partial found / partial missing の説明が破綻しないことを確認する。

### Step 4: B4-002を実装するか判定

以下を満たせる場合のみ、`app_controller.py` へ反映する。

- 差分が未検出時の文言または内部メッセージに限定される。
- GUI状態遷移を変えない。
- テスト可能である。

満たせない場合は、B4ではcore側の説明補助までに留める。

### Step 5: B4-003を実装するか判定

以下を満たせる場合のみ、診断情報扱いを整理する。

- `error.log` の存在意義を維持できる。
- ユーザー向け表示の情報量を増やしすぎない。
- 開発者向け診断性を損なわない。

満たせない場合は、B4では保留として記録する。

### Step 6: 文書同期

実装内容に応じて、以下を更新する。

- `docs/Error_Handling_Specification.md`
  - ユーザー通知または診断ログ扱いを変更した場合のみ更新する。
- `docs/repo_milestone.md`
  - B4完了時に、実施内容、テスト、残課題を記録する。
- `docs/Version_Control.md`
  - B4実施ログを追加する。

### Step 7: 検証

最低限、以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py
git diff --check
```

`app_controller.py` に触れた場合は、以下も実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py
```

必要に応じて、変更ファイルを確認する。

```powershell
git status --short --branch
git diff --stat
git diff --name-only
```

## 10. 状態遷移 / データ契約

B4では、以下の契約を変更しない。

- 音声入力ファイルの選択後、既存タイミングやPreviewが無効化される規則
- ffprobe worker の起動条件
- 解析用WAV生成 worker の起動条件
- MMD用WAV出力 worker の起動条件
- Busy状態中の操作制限
- キャンセル導線
- late callback破棄
- 入力音声、解析用WAV、MMD用WAVの正本分離
- VMD出力仕様

B4で追加してよい契約は、FFmpeg / ffprobe 探索結果の説明用補助だけである。

追加する補助関数は、以下の性質を持つこと。

- 副作用を持たない。
- ファイルシステム探索を追加で行わない。
- 既存の探索結果を解釈するだけである。
- テストで完全に確認できる。

## 11. テスト方針

### 11.1 必須テスト

`ffmpeg_locator.py` を変更した場合は、以下を必須とする。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py
```

### 11.2 条件付きテスト

`app_controller.py` の通知文言、例外文言、音声入力導線に触れた場合は、以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py
```

`src/main.py` の起動例外処理に触れた場合は、単体テストが不足している可能性があるため、差分レビューで以下を確認する。

- `error.log` 書き込みが維持されている
- 起動失敗時のstderr出力が維持されている
- `sys.excepthook` の役割が維持されている

### 11.3 全体テスト

B4は小規模変更であるため、全体pytestは必須ではない。

ただし、GUI状態遷移やworker経路へ触れた場合は、関連テストを追加で検討する。全体pytestを実行する場合は、既知のwx teardown由来の終了コード不安定性があるため、表示上のpass数とプロセス終了コードを分けて記録する。

## 12. 受け入れ条件

B4完了条件は以下。

- 差分がMS18-B3で許可された範囲内に収まっている。
- `ffmpeg_locator.py` の探索順が変わっていない。
- repo local、bundled、PATH、not found の判定が維持されている。
- FFmpeg / ffprobe の自動ダウンロードを追加していない。
- ユーザー向け表示にローカル絶対パスやtraceback全文を不用意に表示していない。
- GUI状態遷移、worker起動順、Busy制御、キャンセル導線を変更していない。
- 変更範囲に応じた限定テストが通過している。
- `git diff --check` が通過している。
- 実施内容、実行テスト、未実行テスト、残課題が文書に記録されている。
- B5 / B6 / B7へ送る項目をB4で先行実装していない。

## 13. リスクと対策

### 13.1 探索順の意図しない変更

リスク:
`ffmpeg_locator.py` の整理中に、repo local / bundled / PATH の優先順が変わる可能性がある。

対策:
既存テストを維持し、探索順を確認するテストを削除または弱体化しない。

### 13.2 ユーザー向け表示の情報過多

リスク:
説明性改善のつもりで、ローカル絶対パスや内部情報をMessageBoxに出しすぎる可能性がある。

対策:
ユーザー向け表示は「アプリ内FFmpegまたはPATHを確認してください」程度に留める。詳細なパス情報は必要な場合でも開発者向け診断へ限定する。

### 13.3 GUI状態遷移の退行

リスク:
未検出時メッセージの修正で、音声入力時の状態クリア、worker起動条件、MessageBox表示順に副作用が出る可能性がある。

対策:
`app_controller.py` へ触れる場合は差分を文言に限定し、`tests/test_wx_ms14_b3_input.py` を実行する。

### 13.4 診断ログの消しすぎ

リスク:
開発コンソール出力の整理で、起動失敗や予期しない例外の調査に必要な情報まで失われる可能性がある。

対策:
`error.log` の記録方針を維持する。診断情報扱いの整理は、安全に確認できる場合だけ実施する。

### 13.5 B5/B6/B7項目の混入

リスク:
B4作業中に、SmokeLaunch、license、package、実MMD確認、cache命名変更へ作業範囲が広がる可能性がある。

対策:
B4では実装しない。必要が見つかった場合は、B5/B6/B7の残課題として記録する。

## 14. Codex 実装時の注意

- 作業開始時に `docs/MS17_and_Beyond_Index.md` を読む。
- コマンドは1つずつ実行し、並列実行しない。
- shell pipelineやコマンド連結を避ける。
- 実装前に `git status --short --branch` を確認する。
- MS18-B3のB3 Scope Tableを再確認してから編集する。
- 変更前に対象ファイルを読む。
- 変更は小さく保つ。
- 新規依存関係を追加しない。
- wxPython主系を維持する。
- Qt / PySide6を復活させない。
- READMEへ内部計画の詳細を追加しない。
- 実装後は、変更したファイル、実装内容、実行したテスト、未実行テスト、残課題を報告する。
- テストを実行していない場合は、実行していない理由を明記する。
- B4完了後の次作業は、MS18-B5 SmokeLaunch / Process Residual Investigation である。

## 15. Completion Report

- 完了日: 2026-06-30
- ブランチ: `feature/MS18`
- 実装結果:
  - `src/core/ffmpeg_locator.py` に、探索結果をユーザー向け診断文へ整形する `format_tool_status` / `format_locator_status` を追加した。
  - 整形結果は探索元を `アプリ内 FFmpeg フォルダ` / `同梱 FFmpeg` / `PATH` / `未検出` として示し、ローカル絶対パスは表示しない。
  - `src/gui_wx/app_controller.py` のFFmpeg / ffprobe未検出メッセージへ、上記の探索元説明を反映した。
  - ユーザーチェックで発生した解析用WAV再生エラーを調査し、Windows MCIが長い解析用WAVファイル名を拒否する問題として修正した。
  - `src/gui_wx/playback_controller.py` で、MCI再生時のみ短い一時ファイル名 `p.wav` のコピーを使い、停止時に削除するようにした。
  - `src/main.py` の `error.log` / 起動例外処理は変更していない。
- 実行テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py` -> `8 passed`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py` -> `2 passed`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py` -> `10 passed`
  - 生成済み解析用WAVを短い一時ファイル名経由でMCI openできることを直接確認した。
  - ユーザーチェックで、解析後のWAVファイル再生エラーが解消し、ユーザーテスト通過が報告された。
- closeout判定:
  - MS18-B4 closeoutはOK。
  - 次作業は MS18-B5 SmokeLaunch / Process Residual Investigation。
