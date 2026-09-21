# MS18-B5 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B5 Implementation Plan
- 対象ブロック: MS18-B5 SmokeLaunch / Process Residual Investigation
- 想定配置先: `docs/Implementation_Plan/MS18-B5_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 基準ブランチ: `feature/MS18`
- 作成日: 2026-06-30
- 文書ステータス: Completed
- 作成目的:
  - `build.ps1 -SmokeLaunch` におけるプロセス残留・タイムアウト原因の調査手順を固定する。
  - 修正する場合と手順化に留める場合の判断基準を明確にする。
  - MS18-B6 / B7 のrelease preflightや実MMD確認と作業範囲を混同しないようにする。
- ユーザーへの追加質問:
  - 不要。B5の対象は既存MS18定義と現行 `build.ps1` から確定できる。
- 実施日:
  - 2026-07-01

## 2. 背景

MS18-B1では、release readiness risk inventoryとして、`build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因が未確定であることをP2として記録した。

MS18-B2では、Security Preflightとして外部入力、subprocess、temp / cache、GUI worker、PyInstaller onefile、release package等を確認し、`build.ps1 -SmokeLaunch` のプロセス残留原因未確定をMS18-B5へ送った。

MS18-B3では、B4で扱う安全なリファクタリング範囲と、B5/B6/B7へ送る項目を分類した。`build.ps1 -SmokeLaunch` と `build.ps1 -Clean` の旧onefile成果物扱いはB5へ送られた。

MS18-B4では、FFmpeg / ffprobe探索元説明性改善、未検出時メッセージ整理、解析用WAV再生エラー修正が完了した。B5は、B4の差分が反映された状態で、release / package化前の起動スモーク確認手順を安定させる。

## 3. 目的

MS18-B5の目的は、`build.ps1 -SmokeLaunch` のプロセス残留・タイムアウト原因を調査し、release / package化前に使う起動確認手順を確定することである。

最終的には、以下のいずれかを判断する。

```text
A. build.ps1 を最小修正し、SmokeLaunch後に残留プロセスが出ない状態にする。
B. build.ps1 は変更せず、SmokeLaunchの既知制約と手動確認手順をrelease preflightへ記録する。
C. 原因を切り分けた上で、B6前に追加調査が必要な残課題として明示する。
```

B5は、新機能追加や配布物確定のBlockではない。

## 4. In Scope

B5で扱う範囲は以下に限定する。

- `build.ps1` の現行処理確認
- `-Clean` と `-SmokeLaunch` の処理順確認
- PyInstaller onefile build後の `dist\MMD_AutoLipTool.exe` 存在確認
- `Start-Process -PassThru` が返すPIDと、実際に残るプロセスの対応確認
- `Stop-Process -Id $proc.Id -Force` 後の残留確認
- `MMD_AutoLipTool.exe` / `pyinstaller.exe` / `python.exe` の残留有無確認
- 残留がPyInstaller由来か、onefile bootloader由来か、アプリ本体由来か、wx event loop由来かの切り分け
- 修正する場合の `build.ps1` 最小修正
- 修正しない場合のrelease preflight手順化
- 必要な履歴文書更新

## 5. Out of Scope

B5では以下を扱わない。

- installer導入
- CI/CD workflowの大規模追加
- PyInstaller以外の配布方式への移行
- PyInstaller specの全面再設計
- GUI起動設計の大規模変更
- wxPython event loopの全面再設計
- アプリ終了処理の全面再設計
- FFmpeg license texts / NOTICE / THIRD_PARTY_LICENSES.md の最終確定
- Release package同梱物・除外物の最終確定
- 実MMDでのVMD / MMD用WAV読み込み確認
- cache命名規則変更
- 音声入力・解析・VMD生成の機能変更
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応

## 6. 前提条件

B5実装前に、以下を確認する。

- 作業ブランチが `feature/MS18` である。
- `docs/MS17_and_Beyond_Index.md` を読んで、現在地がMS18-B5であることを確認している。
- MS18-B4の実装差分とユーザーテスト通過記録が保持されている。
- B5作業前に、B4差分をコミット済みにするか、未コミット差分として明示的に扱う。
- `FFmpeg\bin\ffmpeg.exe` と `FFmpeg\bin\ffprobe.exe` が存在する。
- `.venv\Scripts\python.exe` が存在する。
- PyInstallerが `.venv` から実行可能である。
- GUI起動を伴うSmokeLaunchは、Codex環境で承認または適切な実行権限が必要になる可能性がある。

## 7. 対象ファイル

### 7.1 主対象

```text
build.ps1
MMD_AutoLipTool.spec
src/main.py
src/gui_wx/app.py
src/gui_wx/main_frame.py
```

### 7.2 条件付き変更候補

```text
build.ps1
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
```

### 7.3 参照専用候補

```text
docs/MS17_and_Beyond_Index.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-B5_Implementation_Plan.md
docs/Implementation_Plan/MS18-B4_Implementation_Plan.md
MMD_AutoLipTool.spec
```

## 8. 実装方針

### 8.1 基本方針

- 調査を先に行い、原因が見えない状態で `build.ps1` を変更しない。
- プロセス停止は、B5で起動した対象PIDに限定する。
- `python.exe` などの汎用プロセスを広く停止しない。
- GUI起動確認のためだけにアプリ本体の終了設計を大きく変えない。
- build scriptを修正する場合は、SmokeLaunch後の待機・停止・検証に限定する。
- release packaging / license確認はB6へ残す。
- 実MMD確認はB7へ残す。

### 8.2 想定される原因候補

B5では、以下の候補を切り分ける。

```text
1. Start-Process -PassThru が onefile bootloaderの親プロセスだけを返し、子プロセスが残る。
2. Stop-Process -Force 後に Wait-Process 相当の待機がなく、終了確認前に成功扱いしている。
3. SmokeLaunchの5秒確認が短すぎる、またはスプラッシュ表示中の状態を誤判定している。
4. wx MainLoop / SplashScreen / Frame破棄のタイミングにより、外部停止後の終了確認が遅れる。
5. PyInstaller build側の一時プロセスと、生成exe起動側のプロセスを混同している。
6. 既存 `dist\MMD_AutoLipTool.exe` がCleanで削除されず、古い成果物の影響を受ける。
```

### 8.3 修正判断

以下を満たす場合は、`build.ps1` の最小修正を行ってよい。

- 修正対象がSmokeLaunch後の停止・待機・確認に限定される。
- 起動確認の意味が変わらない。
- 不要に広いプロセス停止を行わない。
- 既存の `build.ps1 -Clean` / 通常build導線を壊さない。

以下の場合は、修正せず手順化を優先する。

- 残留原因が環境依存で再現しない。
- Codex sandbox / GUI起動制約により正確な確認ができない。
- 修正にアプリ本体の終了設計の大改造が必要になる。
- release preflightで手動確認した方が安全な場合。

## 9. 詳細ステップ

### Step 1: 事前確認

```powershell
git status --short --branch
git branch
git log --oneline -n 10
```

以下を確認する。

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --version
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

### Step 2: build inputs確認

以下を確認する。

```text
build.ps1
MMD_AutoLipTool.spec
src/main.py
src/gui_wx/app.py
src/gui_wx/main_frame.py
```

確認観点:

- `build.ps1 -Clean` が削除する対象
- `dist\MMD_AutoLipTool.exe` の生成確認方法
- `Start-Process -PassThru` のPID扱い
- `Stop-Process -Force` 後の終了確認有無
- PyInstaller onefileで同梱されるFFmpeg / assets / license files

### Step 3: build前プロセス状態確認

実行前に、既存の対象プロセスを確認する。

```powershell
Get-Process -Name MMD_AutoLipTool -ErrorAction SilentlyContinue
Get-Process -Name pyinstaller -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue
```

注意:
`python.exe` は他用途でも存在しうるため、停止対象にしない。記録用途に留める。

### Step 4: SmokeLaunch再現確認

GUI起動を伴うため、必要に応じて承認を得て以下を実行する。

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

確認する結果:

- build自体が成功するか
- `dist\MMD_AutoLipTool.exe` が存在するか
- SmokeLaunchが早期終了扱いになるか
- SmokeLaunchが成功表示するか
- 成功/失敗後にプロセスが残るか

### Step 5: build後プロセス状態確認

SmokeLaunch直後に以下を確認する。

```powershell
Get-Process -Name MMD_AutoLipTool -ErrorAction SilentlyContinue
Get-Process -Name pyinstaller -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue
```

必要に応じて、対象exeの実行パスとPIDを確認する。

```powershell
Get-CimInstance Win32_Process -Filter "Name='MMD_AutoLipTool.exe'"
```

### Step 6: 原因分類

観測結果を以下へ分類する。

```text
P1:
  SmokeLaunch後にユーザー環境へ明確な残留プロセスを残し、release前に必ず修正すべき状態。

P2:
  SmokeLaunch手順として不安定、またはbuild scriptの終了確認不足があり、B5内で修正または手順化すべき状態。

P3:
  表現・記録・環境依存の軽微な問題。B6のrelease preflightへ注意事項として送ってよい状態。
```

### Step 7: 最小修正案の検討

原因が `build.ps1` の停止確認不足に限定できる場合、以下を検討する。

- `Stop-Process` 後に対象PIDの終了を待つ。
- 起動したPIDが残っていないことを確認する。
- 必要な場合のみ、同じ実行ファイルパスを持つ `MMD_AutoLipTool.exe` の残留を検出する。
- 残留がある場合は、エラーとして明示するか、B5で起動した対象に限定して停止する。

修正例の方向性:

```text
Start-Processで取得したPIDを記録
5秒後に未終了ならStop-Process
終了待機
同じexeパスの残留確認
結果を明示表示
```

### Step 8: 修正後確認または手順化

修正した場合は、以下を再実行する。

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

修正しない場合は、以下を記録する。

- 原因
- 再現条件
- release preflightで必要な手順
- B6へ送る注意事項

### Step 9: 文書同期

B5完了時に、以下を更新する。

```text
docs/Implementation_Plan/MS18-B5_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/MS17_and_Beyond_Index.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Release_Package_Manifest.md  # release preflight手順へ送る場合のみ
```

## 10. 状態遷移 / データ契約

B5では、アプリの通常利用時の状態遷移やデータ契約を変更しない。

変更禁止:

- 音声入力状態
- 解析用WAV生成
- MMD用WAV出力
- VMD出力
- Preview / waveform
- GUI操作仕様
- 設定schema
- FFmpeg / ffprobe探索順

B5で扱ってよい契約は、build script上のSmokeLaunch確認手順だけである。

## 11. テスト方針

### 11.1 必須確認

B5で必須とする確認は以下。

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

ただし、GUI起動を伴うため、Codex環境で実行できない場合は、実行不能理由を明記する。

### 11.2 build script変更時の確認

`build.ps1` を変更した場合は、以下を確認する。

- `-Clean` なしのbuildが壊れていないこと
- `-Clean` ありのbuildが壊れていないこと
- `-SmokeLaunch` が成功または明確な失敗理由を返すこと
- SmokeLaunch後に `MMD_AutoLipTool.exe` が残留しないこと

### 11.3 unit test

B5が `build.ps1` のみを変更する場合、pytestは必須ではない。

ただし、`src/main.py` / `src/gui_wx/app.py` / `src/gui_wx/main_frame.py` に触れた場合は、関連GUIテストを実行する。

候補:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py
```

### 11.4 終了コード不安定性の扱い

wx系テストを複数まとめて実行した場合、表示上はpassでも終了コードが不安定になることがある。B5でも、表示上のpass数とプロセス終了コードを分けて記録する。

## 12. 受け入れ条件

B5完了条件は以下。

- `build.ps1 -SmokeLaunch` の残留原因が説明されている。
- 残留が再現するか、再現しないかが記録されている。
- 修正する場合、差分は最小限である。
- 修正しない場合、release preflightで使う手順または注意事項が記録されている。
- SmokeLaunch後に残る可能性があるプロセス名・PID・条件が整理されている。
- `build.ps1 -Clean` の旧onefile成果物扱いについて、修正または保留判断が記録されている。
- package化へ進める前に使う起動確認手順が明確である。
- B6/B7へ送る項目が分離されている。

## 13. リスクと対策

### 13.1 無関係プロセスの停止

リスク:
`python.exe` や同名プロセスを広く停止すると、ユーザーの別作業を壊す可能性がある。

対策:
B5で起動したPID、または同じ `dist\MMD_AutoLipTool.exe` 実行パスに限定して扱う。

### 13.2 GUI起動の環境依存

リスク:
Codex環境やsandbox上ではGUI起動・プロセス確認が通常環境と異なる可能性がある。

対策:
実行可否、承認有無、確認できた範囲を明記する。必要ならユーザー側実行結果を別途記録する。

### 13.3 build時間と副作用

リスク:
`build.ps1 -Clean -SmokeLaunch` はbuild成果物を作り直し、時間がかかる。

対策:
事前にFFmpeg、PyInstaller、dist状態を確認し、実行結果を明確に記録する。

### 13.4 アプリ本体修正への拡大

リスク:
SmokeLaunch調査が、GUI終了設計の大規模変更へ広がる可能性がある。

対策:
B5ではbuild script側の確認・最小修正を優先する。アプリ本体の大改造が必要なら、B5では保留判断として記録する。

### 13.5 release / license作業との混同

リスク:
SmokeLaunch調査中に、FFmpeg license noticeやrelease package同梱物確認へ作業が広がる可能性がある。

対策:
license / packageはMS18-B6へ送る。B5では起動スモークとプロセス残留だけを扱う。

## 14. Codex 実装時の注意

- 作業開始時に `docs/MS17_and_Beyond_Index.md` を読む。
- コマンドは1つずつ実行し、並列実行しない。
- shell pipelineやコマンド連結を避ける。
- `Get-Process | Where-Object` のようなpipeline形式は避け、`Get-Process -Name ...` や `Get-CimInstance -Filter ...` を優先する。
- GUI起動を伴うコマンドは、必要に応じて承認を得る。
- 実行前に既存プロセスを記録する。
- 停止対象はB5で起動したプロセスに限定する。
- `build.ps1` を変更する場合は、SmokeLaunchの停止・待機・確認に限定する。
- `src/main.py` / GUI起動設計へ触れる場合は、理由とリスクを明示する。
- B5完了後の次作業は、MS18-B6 Release / Packaging / License Preflight である。

## 15. 実施結果

### 15.1 判定

MS18-B5は完了。

`build.ps1 -SmokeLaunch` の残留・タイムアウト扱いは、アプリ本体の終了設計ではなく、build script側の停止後確認不足として扱うのが妥当と判断した。

### 15.2 確認した原因

初回観測では、既存 `build.ps1 -Clean -SmokeLaunch` は成功表示し、直後の `MMD_AutoLipTool` / `pyinstaller` / `python` 残留は確認されなかった。

修正途中で停止待機を追加したところ、`Stop-Process` 後10秒以内に `MMD_AutoLipTool.exe` が終了せず、SmokeLaunch cleanup failureとして検出された。その後の確認時点ではプロセスは消えていたため、恒久残留ではなく、PyInstaller onefile起動後の外部停止が短時間で完了しないケースと分類した。

### 15.3 実装内容

`build.ps1` に以下を追加した。

- `-Clean` 実行時に旧 `dist\MMD_AutoLipTool.exe` を明示削除する。
- SmokeLaunchで起動前の同一exeパスの既存プロセスIDを記録する。
- SmokeLaunchで起動したPIDを停止後、最大30秒まで終了をポーリングする。
- 同一 `dist\MMD_AutoLipTool.exe` パスに限定して、B5で起動した対象から派生した残留PIDを検出・停止する。
- 既存プロセスIDは停止対象から除外し、広い `python.exe` 停止は行わない。

### 15.4 検証結果

実行した確認:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
powershell -ExecutionPolicy Bypass -File .\build.ps1
Get-Process -Name MMD_AutoLipTool -ErrorAction SilentlyContinue
Get-Process -Name pyinstaller -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue
```

結果:

- `git diff --check`: 通過。
- `build.ps1 -Clean -SmokeLaunch`: 通過。
- `build.ps1`: 通常build導線として通過。
- SmokeLaunch後の `MMD_AutoLipTool` / `pyinstaller` / `python` 残留: 確認時点でなし。
- ユーザーテスト: 通過報告あり。

### 15.5 残課題

PyInstallerログ上、Matplotlib backend収集の過程で `PySide6` hook が選択されている。これはB5のプロセス残留修正範囲外であり、MS18-B6 Release / Packaging / License Preflightで配布内容・依存関係確認として扱う。
