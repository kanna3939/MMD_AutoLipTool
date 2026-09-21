# MS18-B6 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B6 Implementation Plan
- 対象ブロック: MS18-B6 Release / Packaging / License Preflight
- 想定配置先: `docs/Implementation_Plan/MS18-B6_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 基準ブランチ: `feature/MS18`
- 作成日: 2026-07-01
- 文書ステータス: Completed
- 作成目的:
  - GitHub Releases 向け実行用ZIPを作成する前に、同梱物・除外物・ライセンス通知・FFmpeg配布条件の確認手順を固定する。
  - MS18-B5で安定化した `build.ps1` / `SmokeLaunch` 結果を前提に、package化へ進めるかどうかを判断する。
  - 実MMD確認を行うMS18-B7と、配布前preflightで行う確認を混同しないようにする。
- ユーザーへの追加質問:
  - 不要。B6の対象は既存MS18定義、`docs/Release_Package_Manifest.md`、ライセンス関連文書、現行 `build.ps1` / `MMD_AutoLipTool.spec` から確定できる。
- 実施日:
  - 2026-07-02
- CloseOut更新日:
  - 2026-07-03

## 2. 背景

MS18-B1では、release readiness risk inventoryとして、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifestの同期状態と、リリース前に残る確認項目を棚卸しした。

MS18-B2では、Security Preflightとして外部入力、ffprobe / ffmpeg、subprocess、temp / cache、GUI worker、PyInstaller onefile、release package、FFmpeg license noticeを確認した。P1は検出されず、FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定を後続Blockへ送った。

MS18-B3では、`build.ps1 -SmokeLaunch` と `build.ps1 -Clean` はMS18-B5、FFmpeg license / package確認とcache配布除外確認はMS18-B6、実MMD確認はMS18-B7へ分離した。

MS18-B5では、`build.ps1 -Clean -SmokeLaunch` の停止待機・残留確認が改善され、ユーザーテスト通過が報告された。一方、PyInstallerログ上でMatplotlib backend収集時に `PySide6` hook が選択されていることが観測されたため、B6で配布内容・依存関係確認として扱う。

## 3. 目的

MS18-B6の目的は、実行用ZIPまたはGitHub Release向け配布物を作成する前に、配布物として含めるべきもの、含めてはいけないもの、ライセンス通知、FFmpeg同梱条件、依存関係の注意事項を確認し、package化へ進めるかどうかを判定することである。

B6は、実公開やGitHub Release作成そのものを行うBlockではない。

## 4. In Scope

B6で扱う範囲は以下に限定する。

- `README.md` の配布前同期確認
- `readme_mmdautolip.txt` の配布前同期確認
- `LICENSE` の存在確認
- `NOTICE` の内容確認
- `THIRD_PARTY_LICENSES.md` の内容確認
- `docs/Release_Package_Manifest.md` の内容確認・必要最小限の更新
- `MMD_AutoLipTool.spec` の同梱対象確認
- `build.ps1` のB5修正後前提確認
- PyInstaller onefile成果物の存在確認
- PyInstaller buildログ / warnファイル / xref等による依存関係の注意確認
- B5で観測した `PySide6` hook 選択の扱い確認
- FFmpeg / ffprobe のversion確認
- FFmpeg / ffprobe のbuild configuration確認
- `--enable-gpl --enable-version3` を含むFFmpeg buildへの第三者ライセンス通知確認
- 実行用ZIPに含めるもの / 含めないものの確認
- `cache/`, `build/`, `src/`, `tests/`, `.venv/` などが配布物に混入しないことの確認
- `sample/` を実行用ZIPに含めるかどうかのpreflight判断
- GitHub Release本文に必要な注意事項の整理
- package化へ進めるかどうかの判定
- 必要な履歴文書更新

## 5. Out of Scope

B6では以下を扱わない。

- 実行用ZIPの正式作成
- GitHub Releaseの作成・公開
- installer導入
- CI/CD workflowの大規模追加
- PyInstaller以外の配布方式への移行
- FFmpeg buildの変更
- FFmpeg自動ダウンロード導入
- ライセンス解釈の法的断定
- 有償コード署名導入
- 配布方式の全面変更
- 実MMDでのVMD / MMD用WAV読み込み確認
- 音声入力・解析・VMD生成の機能変更
- GUI起動設計の変更
- PySide6 / Qt系GUIの復活
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応

## 6. 前提条件

B6実装前に、以下を確認する。

- 作業ブランチが `feature/MS18` である。
- `docs/MS17_and_Beyond_Index.md` を読んで、現在地がMS18-B6であることを確認している。
- MS18-B5の実装差分とユーザーテスト通過記録が保持されている。
- B6作業前に、B5差分をコミット済みにするか、未コミット差分として明示的に扱う。
- `FFmpeg\bin\ffmpeg.exe` と `FFmpeg\bin\ffprobe.exe` が存在する。
- `.venv\Scripts\python.exe` が存在する。
- PyInstallerが `.venv` から実行可能である。
- `build.ps1 -Clean -SmokeLaunch` がB5修正後の手順で通る、または直近の通過結果が記録されている。

## 7. 対象ファイル

### 7.1 主対象

```text
README.md
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
MMD_AutoLipTool.spec
build.ps1
pyproject.toml
.gitignore
```

### 7.2 条件付き変更候補

```text
docs/Release_Package_Manifest.md
NOTICE
THIRD_PARTY_LICENSES.md
README.md
readme_mmdautolip.txt
docs/Implementation_Plan/MS18-B6_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/repo_milestone.md
docs/Version_Control.md
```

### 7.3 参照専用候補

```text
docs/Implementation_Plan/MS18-B5_Implementation_Plan.md
build/MMD_AutoLipTool/warn-MMD_AutoLipTool.txt
build/MMD_AutoLipTool/xref-MMD_AutoLipTool.html
dist/MMD_AutoLipTool.exe
FFmpeg/bin/
sample/
```

## 8. 実装方針

### 8.1 基本方針

- package化へ進めるかどうかを判定するためのpreflightに限定する。
- 確認結果は、実装済み、確認済み、未確定、B7送り、B6内修正対象に分けて記録する。
- 実行用ZIPを作成する場合でも、正式配布物として公開しない。
- FFmpegのライセンスについては、実際に確認できるversion / configuration / 同梱方針を記録する。法的断定はしない。
- `sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する方針を優先する。
- PyInstallerログで `PySide6` hook が選択された件は、Qt / PySide GUI復活ではなく、依存関係収集上の配布確認項目として扱う。
- B6でコード変更は原則行わない。必要になった場合は、配布文書・manifest・noticeの小修正に限定する。

### 8.2 判定区分

B6の結果は以下のいずれかに分類する。

```text
A. package化へ進んでよい。
B. package化へ進めるが、Release本文または同梱文書に注意事項が必要。
C. B6内で文書修正が必要。修正後に再判定する。
D. package化へ進む前に、依存関係またはライセンス通知の追加調査が必要。
```

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

### Step 2: MS18-B5結果確認

以下を確認する。

```text
docs/Implementation_Plan/MS18-B5_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/MS17_and_Beyond_Index.md
docs/repo_milestone.md
docs/Version_Control.md
```

確認観点:

- B5が完了扱いか
- `build.ps1 -Clean -SmokeLaunch` 通過が記録されているか
- ユーザーテスト通過が記録されているか
- B5からB6へ送られた事項があるか
- `PySide6` hook選択の扱いがB6送りになっているか

### Step 3: 配布関連文書確認

以下を確認する。

```text
README.md
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
```

確認観点:

- 実行用ZIPの想定内容が矛盾していないか
- Source code ZIPと実行用ZIPの違いが説明されているか
- FFmpeg同梱時の注意が一致しているか
- `--enable-gpl --enable-version3` を含むFFmpeg buildへの注意が記録されているか
- NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の記述が古くないか

### Step 4: spec / build script確認

以下を確認する。

```text
MMD_AutoLipTool.spec
build.ps1
pyproject.toml
.gitignore
```

確認観点:

- `MMD_AutoLipTool.spec` が `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md` を同梱対象にしているか
- `FFmpeg\bin\` の実体が onefile に取り込まれる前提か
- `.gitignore` が `dist/`, `build/`, `cache/`, `FFmpeg/bin/*` の扱いを正しく定義しているか
- B5で修正した `build.ps1` の `-Clean` / `-SmokeLaunch` が維持されているか

### Step 5: build / SmokeLaunch確認

必要に応じて以下を実行する。

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

確認する結果:

- buildが成功するか
- `dist\MMD_AutoLipTool.exe` が存在するか
- SmokeLaunchが成功するか
- SmokeLaunch後に `MMD_AutoLipTool` / `pyinstaller` / `python` が残留しないか

### Step 6: PyInstaller成果物・ログ確認

以下を確認する。

```text
dist/MMD_AutoLipTool.exe
build/MMD_AutoLipTool/warn-MMD_AutoLipTool.txt
build/MMD_AutoLipTool/xref-MMD_AutoLipTool.html
```

確認観点:

- `dist\MMD_AutoLipTool.exe` が存在するか
- warnに配布前に説明すべき問題がないか
- `PySide6` hook選択が実際の配布内容にどの程度影響するか
- PyInstaller onefileとして、外部同梱ファイルがZIP側に別途必要か

### Step 7: FFmpeg / ffprobe確認

以下を確認する。

```powershell
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

確認観点:

- versionが `N-123549-g70537ec8e6-20260318` か
- configurationに `--enable-gpl --enable-version3` が含まれるか
- NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifestに、この前提が反映されているか
- FFmpeg関連license textsを実行用ZIPにどう扱うかが明確か

### Step 8: 実行用ZIP内容方針確認

候補:

```text
MMD_AutoLipTool.exe
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
FFmpeg関連license texts
```

除外候補:

```text
src/
tests/
docs/
.agent/
AGENTS.md
.git/
.venv/
build/
cache/
__pycache__/
.pytest_cache/
*.pyc
*.log
*.tmp
*.bak
sample/  # 出典・ライセンス・用途説明が確定できない場合
```

### Step 9: `sample/` の扱い判断

現状の `sample/` には音声・テキスト・pipeline生成用ディレクトリが存在する。

B6では以下のいずれかに分類する。

```text
A. sample/ は実行用ZIPから除外する。
B. sample/ を含めるが、出典・ライセンス・用途説明を確認し、readmeへ明記する。
C. sample/ の扱いはB6では未確定として、package化前の残課題にする。
```

推奨は A。理由は、配布前preflightでは不明な素材の同梱を避ける方が安全であり、実行用ZIPの必須動作に sample/ は不要なため。

### Step 10: Release本文メモ整理

GitHub Release本文に記載すべき候補を整理する。

- 通常利用者は実行用ZIPを使うこと
- Source code ZIP / tar.gz は開発者向けであること
- Windows向け onefile 実行ファイルであること
- FFmpegを同梱している場合、その概要とlicense notice参照先
- 初回起動時にWindows Defender等の確認が出る可能性
- 実MMD確認はB7で行うため、B6ではまだcloseoutではないこと

### Step 11: 文書同期

B6完了時に、必要に応じて以下を更新する。

```text
docs/Implementation_Plan/MS18-B6_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Release_Package_Manifest.md
NOTICE
THIRD_PARTY_LICENSES.md
README.md
readme_mmdautolip.txt
```

## 10. 状態遷移 / データ契約

B6では、アプリの通常利用時の状態遷移やデータ契約を変更しない。

変更禁止:

- 音声入力状態
- 解析用WAV生成
- MMD用WAV出力
- VMD出力
- Preview / waveform
- GUI操作仕様
- 設定schema
- FFmpeg / ffprobe探索順
- PyInstaller以外の配布方式

B6で扱ってよい契約は、配布前preflight、同梱物、除外物、license notice、release本文メモだけである。

## 11. テスト方針

### 11.1 必須確認

B6で必須とする確認は以下。

```powershell
git diff --check
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

### 11.2 build / SmokeLaunch確認

B5の実装差分が未コミット、またはB6中に配布関連文書以外へ触れた場合は、以下を再実行する。

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

B6で `build.ps1` / `MMD_AutoLipTool.spec` に触れた場合は必須とする。

### 11.3 unit test

B6が配布関連文書・manifest確認だけで完結する場合、pytestは必須ではない。

ただし、`src/` や通常アプリ動作に影響するファイルに触れた場合は、関連テストを実行する。

候補:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py
```

## 12. 受け入れ条件

B6完了条件は以下。

- `README.md` / `readme_mmdautolip.txt` / `NOTICE` / `THIRD_PARTY_LICENSES.md` / `Release_Package_Manifest.md` の整合状態が確認されている。
- 実行用ZIPに含めるものが明確である。
- 実行用ZIPから除外するものが明確である。
- FFmpeg / ffprobe のversionとconfigurationが確認されている。
- `--enable-gpl --enable-version3` を含むFFmpeg buildのlicense notice扱いが記録されている。
- `sample/` を含めるか除外するかのpreflight判断が記録されている。
- B5で観測した `PySide6` hook選択の扱いが記録されている。
- package化へ進めるか、追加調査が必要かが判定されている。
- 実公開は行っていない。
- B7で扱う実MMD確認と、B6で扱う配布前確認が分離されている。

## 13. リスクと対策

### 13.1 FFmpeg license notice不足

リスク:
FFmpeg同梱時に必要なlicense noticeやbuild configurationの説明が不足すると、配布前提が不明確になる。

対策:
実際の `ffmpeg.exe -version` / `ffprobe.exe -version` を根拠に、NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifestの整合を確認する。法的断定は避け、未確定ならB6内で保留判断を明記する。

### 13.2 不要ファイル混入

リスク:
`src/`, `tests/`, `docs/`, `.venv/`, `build/`, `cache/` 等が実行用ZIPに混入すると、利用者向け配布物として不要・過大・誤解を招く。

対策:
Release_Package_Manifestの除外リストを確認し、実行用ZIP作成手順へ反映する。

### 13.3 sample素材の出典不明

リスク:
`sample/` の音声やテキストの出典・ライセンスが明確でないまま配布物に含まれる。

対策:
B6では原則除外を推奨する。含める場合は、出典・ライセンス・用途説明を明記できることを条件にする。

### 13.4 PySide6 hook選択

リスク:
wxPython主系にもかかわらず、PyInstallerログ上で `PySide6` hook が選択されている場合、配布物サイズ・依存物・ライセンス通知の確認漏れにつながる可能性がある。

対策:
B6ではGUIフレームワークを変更せず、PyInstaller成果物・warn/xref・依存関係上の扱いを確認する。必要ならB6判定を追加調査扱いにする。

### 13.5 実MMD確認との混同

リスク:
B6の配布前preflightで、実MMDでのVMD / MMD用WAV読み込み確認まで広がる。

対策:
実MMD確認はMS18-B7へ残す。B6ではpackage化前提の配布内容・ライセンス・同梱物確認に限定する。

## 14. Codex 実装時の注意

- 作業開始時に `docs/MS17_and_Beyond_Index.md` を読む。
- コマンドは1つずつ実行し、並列実行しない。
- shell pipelineやコマンド連結を避ける。
- `docs/repo_milestone.md` や `docs/Version_Control.md` は必要箇所だけ読む。
- B5未コミット差分がある場合は、B5差分を上書きしない。
- B6は原則として確認と文書同期であり、package化そのものやGitHub Release公開は行わない。
- FFmpeg licenseについて法的断定をしない。
- `sample/` を同梱可と断定しない。出典・ライセンスが不明なら除外または保留にする。
- `PySide6` hook選択を、Qt / PySide GUI復活と混同しない。
- `src/` への変更が必要になった場合は、B6範囲外の可能性を報告してから進める。
- B6完了後の次作業は、MS18-B7 Actual MMD Manual Verification Closeoutである。

## 15. 実施結果

### 15.1 判定

MS18-B6は完了。

package化可否判定は、CloseOut時点で **A: package化へ進んでよい** とする。

理由:

- 2026-07-02時点では、`FFmpeg\bin\` のGit追跡、GitHub Source code ZIP / tar.gzへのFFmpeg実体混入、FFmpeg license texts / COPYING類未確認、PyInstaller xref上の `PySide6` 参照をpackage化前P2として記録した。
- 2026-07-03のMS18 CloseOut時点で、ユーザー判断により上記P2はクリア扱いとする指示を受けた。
- `sample/` は引き続き出典・ライセンス・用途説明が確定するまで実行用ZIPから除外する。これはpackage化阻害要因ではない。
- B6の配布前preflightとして、package化を止める未解決P1 / P2は残っていない。

### 15.2 実施内容

以下の文書を更新した。

- `docs/Release_Package_Manifest.md`
- `THIRD_PARTY_LICENSES.md`
- `NOTICE`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/MS18_and_Beyond_Roadmap.md`

反映内容:

- 実行用ZIPだけでなく、GitHub自動生成 Source code ZIP / tar.gz もFFmpegバイナリを含む前提でlicense notice確認が必要であることを明記した。
- FFmpeg buildが `--enable-gpl --enable-version3` を含むため、package化前にFFmpeg license texts / noticeを確定する必要があることを明記した。
- `sample/` は、出典・ライセンス・用途説明が確定できるまで実行用ZIPから除外する方針とした。
- PyInstaller xref上の `PySide6` 関連参照は、Qt / PySide GUI復活ではなく、配布内容・依存関係・license notice確認項目として扱うことを明記した。

### 15.3 確認結果

確認した事実:

- `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe` は実行可能。
- FFmpeg / ffprobe のversionは `N-123549-g70537ec8e6-20260318`。
- configurationに `--enable-gpl --enable-version3` を含む。
- `git ls-files FFmpeg/bin` で、FFmpeg実体ファイルがGit追跡対象であることを確認した。
- `dist\MMD_AutoLipTool.exe` は存在する。
- `build\MMD_AutoLipTool\warn-MMD_AutoLipTool.txt` / `xref-MMD_AutoLipTool.html` は存在する。
- `xref-MMD_AutoLipTool.html` に `PySide6` 関連参照が存在する。
- `sample/` には音声・テキスト・pipeline生成用ディレクトリが存在する。

実行した確認:

```powershell
git status --short --branch
git log --oneline -n 5
.\.venv\Scripts\python.exe -m PyInstaller --version
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
git ls-files FFmpeg/bin
```

### 15.4 CloseOut時点の扱い

2026-07-03 のMS18 CloseOut時点で、以下はユーザー判断によりクリア済みとして扱う。

- FFmpeg関連license texts / noticeを、実行用ZIPおよびGitHub Source code ZIP / tar.gzの両方の前提で確定する件。
- `FFmpeg\bin\` の実体をGit追跡に残すか、配布用ビルド入力として別管理にするかの判断。
- PyInstaller xref上の `PySide6` 関連モジュールが最終成果物へ入るか、license noticeが必要か、除外できるかの確認。

`sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する方針を維持する。
