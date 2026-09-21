# MS18-B1 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B1 Implementation Plan
- 想定配置先: `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 対象マイルストーン: MS18
- 対象Block: MS18-B1
- Block名: Repo / Release Readiness / Risk Inventory
- 基準ブランチ: `main`
- 正本:
  - `main / origin/main`
- 非正本:
  - `feature/MS17`
- 関連文書:
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
  - `README.md`
  - `NOTICE`
  - `THIRD_PARTY_LICENSES.md`
  - `docs/Release_Package_Manifest.md`
- 作成日: 2026-06-03
- 文書ステータス: Completed
- 作業種別:
  - repo状態確認
  - release readiness 棚卸し
  - risk inventory
  - 実装前チェック
- 実装変更:
  - なし

## 2. 背景

MS17では、wxPython 主系上での音声入力拡張、解析用WAV生成、MMD用WAV出力、音声処理 worker 化、Busy制御、キャンセル導線、MS17-B9 closeout まで完了した。

MS17 closeout 後の追補として、`cache/` は Git 追跡対象外となり、`cache/analysis_wav/` 配下の解析用WAVは Git 管理から外された。

MS18では、リリース / package 化へ進む前に、リリース前安定化、セキュリティ確認、処理効率化、重複コード整理、SmokeLaunch残留調査、FFmpeg同梱配布時のライセンス通知確認、実MMD確認を行う。

MS18-B1は、MS18全体の最初のBlockである。  
このBlockでは、実装変更を行わず、現在の repo 状態、MS17 closeout 反映状態、リリース前残課題、MS18で扱うリスクを棚卸しする。

## 3. 目的

MS18-B1の目的は、`main / origin/main` を正本として、MS18開始時点の状態を確認し、MS18-B2以降に進むための前提を確定することである。

具体的には、以下を確認する。

- `main / origin/main` が最新正本であること
- `feature/MS17` など古いブランチを見ていないこと
- MS17-B9 closeout が `main` に反映済みであること
- MS17 closeout 後追補として、`cache/` の Git 追跡対象外化が反映済みであること
- README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest が MS17 状態に同期されていること
- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留が残課題として記録されていること
- 実MMD確認がリリース前確認へ引き継がれていること
- FFmpeg build の `--enable-gpl --enable-version3` に関する第三者ライセンス通知確認が残課題として記録されていること
- MS18で扱うリスクを P1 / P2 / P3 に分類できること

## 4. In Scope

MS18-B1では、以下を対象とする。

### 4.1 Git / branch 状態確認

- `git status`
- `git branch`
- `git log --oneline -n 10`
- `git remote -v`
- `git fetch origin`
- `origin/main` の最新ログ確認
- local main と origin/main の同期確認
- working tree の未コミット差分確認
- staged 差分確認
- `cache/` の Git 追跡状態確認

### 4.2 正本確認

- `main / origin/main` を正本として扱う
- `feature/MS17` は main より古い状態として扱う
- MS18作業開始前に古いブランチ上で作業していないことを確認する

### 4.3 MS17 closeout 反映確認

- MS17-B9 closeout が main に反映済みであること
- MS17-B9 closeout 後追補として `cache/` が `.gitignore` 管理になっていること
- `cache/analysis_wav/` 配下の解析用WAVが Git 追跡対象外になっていること
- README が MS17 closeout 状態になっていること
- NOTICE が FFmpeg 同梱前提の MS17 状態になっていること
- THIRD_PARTY_LICENSES.md が FFmpeg / wxPython / PyInstaller 等の配布前確認事項を記録していること
- Release_Package_Manifest が MS17 状態に同期されていること

### 4.4 リリース前残課題確認

- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留
- 実MMDでの VMD / MMD用WAV 読み込み・再生確認
- FFmpeg 同梱配布時の第三者ライセンス通知確定
- Release package の同梱物・除外物確認
- package 化へ進める前に必要な確認事項

### 4.5 MS18リスク分類

MS18-B1では、確認した残課題を以下に分類する。

```text
P1:
  リリース前に必ず解消すべき重大問題。

P2:
  MS18内で解消または扱いを確定すべき問題。

P3:
  記録・表現・将来改善として扱える軽微な問題。
```

### 4.6 MS18-B2以降への引き継ぎ

MS18-B1の確認結果を、以下へ引き継ぐ。

- MS18-B2: Security Preflight Review
- MS18-B3: Refactor Scope Definition
- MS18-B5: SmokeLaunch / Process Residual Investigation
- MS18-B6: Release / Packaging / License Preflight
- MS18-B7: Actual MMD Manual Verification Closeout

## 5. Out of Scope

MS18-B1では、以下を行わない。

- コード変更
- ドキュメント変更
- リファクタリング
- セキュリティ修正
- packaging 実作業
- GitHub Release 作成
- 実MMD確認
- `build.ps1` 修正
- FFmpeg build の変更
- 依存関係更新
- 新機能追加
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- 英語対応
- VMD writer 再設計
- pipeline の意味論変更
- Preview / waveform の仕様変更
- GUI レイアウト刷新

## 6. 前提条件

MS18-B1を開始する前提は以下とする。

- MS17-B9 closeout が完了済みである
- MS17 closeout 後追補として `cache/` の Git 追跡対象外化が完了済みである
- 現在の最新正本は `main` である
- `feature/MS17` は古い状態として扱う
- MS18以降のロードマップとして、`docs/MS18_and_Beyond_Roadmap.md` を新規正本候補とする
- 旧 `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md` は、MS18以降の正本ロードマップとして扱わない
- MS18は新機能追加ではなく、リリース前安定化・処理効率化・セキュリティ確認のマイルストーンである

## 7. 対象ファイル

MS18-B1では、以下のファイルを確認対象とする。

```text
README.md
readme_mmdautolip.txt
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
.gitignore
build.ps1
MMD_AutoLipTool.spec
pyproject.toml
```

必要に応じて、以下も確認対象に含める。

```text
src/main.py
src/core/ffmpeg_locator.py
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/mmd_wav_export.py
src/gui_wx/app_controller.py
src/gui_wx/audio_worker.py
```

ただし、MS18-B1ではコード内容の詳細レビューは行わない。  
コード確認は、リスク棚卸しに必要な最小限に留める。

## 8. 実装方針

MS18-B1では、実装変更を行わない。

作業方針は以下とする。

1. Git 状態を確認する
2. `main / origin/main` を正本として確認する
3. `feature/MS17` を参照していないことを確認する
4. MS17-B9 closeout 反映状態を確認する
5. `cache/` の Git 追跡対象外化を確認する
6. README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の同期状態を確認する
7. MS17 closeout 後に残っている課題を確認する
8. MS18で扱うリスクを分類する
9. MS18-B2以降へ引き継ぐ内容を整理する
10. 実装変更を行っていないことを確認する

## 9. 詳細ステップ

### 9.1 Step 1: 作業開始前の Git 状態確認

以下を実行する。

```powershell
git status
git branch
git log --oneline -n 10
git remote -v
```

確認すること。

- 現在の作業ブランチ
- working tree の状態
- staged / unstaged 差分の有無
- 最新コミット
- remote URL

### 9.2 Step 2: origin/main の取得と確認

以下を実行する。

```powershell
git fetch origin
git status
git log --oneline -n 10 origin/main
```

確認すること。

- local main と origin/main が同期しているか
- origin/main の直近ログに MS17-B9 closeout と cache追跡対象外化が含まれているか
- MS18作業開始前に取り込むべき remote 差分がないか

### 9.3 Step 3: working tree / staged 差分確認

以下を実行する。

```powershell
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

- 未コミット差分がないか
- staged 差分がないか
- MS18-B1開始前に既存の作業差分が混入していないか

### 9.4 Step 4: cache 追跡状態確認

以下を実行する。

```powershell
git ls-files cache
```

確認すること。

- 出力が空であること
- `cache/analysis_wav/` 配下の解析用WAVが Git 追跡対象外であること

`.gitignore` も確認する。

```text
.gitignore
```

確認すること。

- `cache/` が除外対象になっていること
- `FFmpeg/bin/*` と `!FFmpeg/bin/.gitkeep` の扱いが維持されていること

### 9.5 Step 5: README の MS17 状態確認

確認対象。

```text
README.md
```

確認すること。

- 現在バージョンが MS17 closeout 状態を反映していること
- wav / mp3 / m4a 入力が記載されていること
- 解析用WAVを使うことが記載されていること
- 専用の `MMD用WAV出力` 導線が記載されていること
- `あ / い / う / え / お` 固定が記載されていること
- 最終確認は MMD 側で行うべきことが記載されていること
- 配布時に LICENSE / NOTICE / THIRD_PARTY_LICENSES.md を同梱することが記載されていること

### 9.6 Step 6: NOTICE / THIRD_PARTY_LICENSES.md の確認

確認対象。

```text
NOTICE
THIRD_PARTY_LICENSES.md
```

確認すること。

- FFmpeg / ffprobe の手動 staging 前提が記録されていること
- `FFmpeg\bin\` 配置前提が記録されていること
- PyInstaller onefile bundling 前提が記録されていること
- 現在 staged されている FFmpeg build が記録されていること
- `--enable-gpl --enable-version3` が配布前確認事項として記録されていること
- 第三者ライセンス通知が未確定の場合、それが残課題として扱われていること

### 9.7 Step 7: Release_Package_Manifest の確認

確認対象。

```text
docs/Release_Package_Manifest.md
```

確認すること。

- 実行用ZIPに含めるものが記録されていること
- 実行用ZIPに含めないものが記録されていること
- `cache/` が除外対象に含まれていること
- FFmpeg 同梱時の version / build configuration / license 表記確認がチェック項目に含まれていること
- `--enable-gpl --enable-version3` 等に関する第三者ライセンス通知同梱がチェック項目に含まれていること
- GitHub Release 本文で Source code と実行用ZIPの違いを説明する方針が記録されていること

### 9.8 Step 8: repo_milestone / Version_Control の確認

確認対象。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

確認すること。

- MS17-B9 closeout が記録されていること
- cache追跡対象外化の追補が記録されていること
- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留が残課題として記録されていること
- 実MMDでの MMD用WAV 読み込み・再生確認が未実施で、リリース前確認へ引き継がれていること
- FFmpeg build の `--enable-gpl --enable-version3` に関する第三者ライセンス通知確認が残課題として記録されていること
- MS18へ進む前提が矛盾なく記録されていること

### 9.9 Step 9: MS18関連新規文書の確認

確認対象。

```text
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
```

確認すること。

- MS18が Release Readiness / Refactor / Security Hardening として定義されていること
- MS18が新機能追加ではないこと
- MS19が Voice-only Input として定義されていること
- MS20が Per-Event Lip Morph Editing として定義されていること
- MS20のモーフ編集対象が `あ / い / う / え / お` の既存リップモーフ範囲に限定されていること
- 旧 `Ver0_4_Expansion_Roadmap_for_Antigravity.md` を MS18以降の正本として扱わないことが明記されていること

### 9.10 Step 10: リスク分類

確認結果を以下の観点で分類する。

```text
P1:
  リリース前に必ず解消すべき重大問題。

P2:
  MS18内で解消または扱いを確定すべき問題。

P3:
  記録・表現・将来改善として扱える軽微な問題。
```

MS18-B1時点で想定される初期分類は以下。

```text
P1候補:
  - FFmpeg同梱配布時の第三者ライセンス通知が確定しないまま公開へ進むこと
  - 実MMDで VMD / MMD用WAV が読み込めない重大問題が見つかること
  - package に不要な開発用ファイルや cache が混入すること

P2候補:
  - build.ps1 -SmokeLaunch の PyInstaller プロセス残留原因が未確定であること
  - Security Preflight で subprocess / temp / cache / path 処理に改善対象が見つかること
  - 重複コード整理や処理効率化の対象範囲が未定義であること

P3候補:
  - README / docs の軽微な表現不足
  - Release note の説明不足
  - cache / temp 管理の将来改善
  - sample/ 同梱方針の補足不足
```

### 9.11 Step 11: MS18-B2以降への引き継ぎ整理

MS18-B1の結果を、以下の形で整理する。

```text
MS18-B2へ:
  Security Preflight で重点確認すべき箇所

MS18-B3へ:
  Refactor Scope Definition で確認すべき重複・非効率候補

MS18-B5へ:
  SmokeLaunch / Process Residual Investigation で確認すべき事項

MS18-B6へ:
  Release / Packaging / License Preflight で確認すべき事項

MS18-B7へ:
  Actual MMD Manual Verification Closeout で確認すべき事項
```

## 10. 状態遷移 / データ契約

MS18-B1では、アプリケーションの実装上の状態遷移やデータ契約は変更しない。

変更しない対象は以下。

- TEXT入力状態
- 音声入力状態
- 解析用WAV状態
- MMD用WAV出力状態
- Preview状態
- waveform状態
- VMD保存状態
- Busy状態
- worker状態
- settings状態
- cache管理仕様
- FFmpeg / ffprobe 実行仕様
- VMD writer仕様

MS18-B1で行うのは、これらが MS17 closeout 状態として維持されているかを、文書・git状態・残課題の観点から確認することである。

## 11. テスト方針

MS18-B1では、実装変更を行わないため、原則として自動テストは実行しない。

ただし、AI agent が repo 状態確認の過程で必要と判断した場合、以下のような軽量確認は許可する。

```powershell
.\.venv\Scripts\python.exe -m pytest --version
.\.venv\Scripts\python.exe -m pytest --collect-only
```

ただし、MS18-B1の主目的は repo状態確認とリスク棚卸しであり、テスト実行は必須ではない。

テストを実行した場合は、以下を報告する。

- 実行したコマンド
- 結果
- 終了コード
- 表示上の pass / fail / error
- 未実行テスト
- 未実行理由

MS18-B1では、以下は行わない。

- 全体 pytest の実行を完了条件にすること
- wx teardown 由来の既知不安定性の詳細調査
- テスト修正
- テスト追加

## 12. 受け入れ条件

MS18-B1の完了条件は以下。

- `main / origin/main` を正本として確認している
- local main と origin/main の同期状態が確認されている
- `feature/MS17` を正本として見ていないことが確認されている
- working tree / staged 差分の有無が確認されている
- MS17-B9 closeout が main に反映済みであることが確認されている
- `cache/` の Git 追跡対象外化が確認されている
- `README.md` が MS17状態に同期されていることが確認されている
- `NOTICE` が MS17状態に同期されていることが確認されている
- `THIRD_PARTY_LICENSES.md` が MS17状態に同期されていることが確認されている
- `docs/Release_Package_Manifest.md` が MS17状態に同期されていることが確認されている
- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留が残課題として確認されている
- 実MMD確認がリリース前確認へ引き継がれていることが確認されている
- FFmpeg build の `--enable-gpl --enable-version3` に関する第三者ライセンス通知確認が残課題として確認されている
- MS18で扱うリスクが P1 / P2 / P3 に分類されている
- MS18-B2以降への引き継ぎ事項が整理されている
- 実装変更が行われていない

## 13. リスクと対策

### 13.1 古いブランチを正本として見てしまう

#### リスク

`feature/MS17` が残っている場合、古い状態を見て MS18計画を誤る可能性がある。

#### 対策

- 作業開始時に `git branch` を確認する
- `git fetch origin` 後に `origin/main` を確認する
- `feature/MS17` は非正本として扱う
- MS18-B1の報告に、現在見ているブランチと最新コミットを必ず含める

### 13.2 実装変更が混入する

#### リスク

MS18-B1は確認のみのBlockだが、誤ってコードやdocsを修正してしまう可能性がある。

#### 対策

- MS18-B1では実装変更禁止と明記する
- `git diff --stat` / `git diff --name-only` を作業前後で確認する
- 変更が発生した場合は、意図したものかどうかを報告し、原則として作業範囲違反として扱う

### 13.3 リスク分類が抽象的になりすぎる

#### リスク

一般論のセキュリティ・リリース確認に寄りすぎ、MMD_AutoLipTool 固有の問題を見落とす可能性がある。

#### 対策

確認対象を以下に絞る。

- FFmpeg / ffprobe
- subprocess
- temp / cache
- PyInstaller onefile
- 外部音声ファイル読み込み
- MMD用WAV出力
- Release package 同梱物
- FFmpeg ライセンス通知
- 実MMD確認

### 13.4 MS18-B2以降の作業範囲が曖昧になる

#### リスク

MS18-B1で棚卸しした内容が曖昧だと、B2以降で作業が広がる。

#### 対策

- P1 / P2 / P3 の分類を必ず行う
- 各リスクについて、どのBlockへ引き継ぐかを記録する
- MS18で扱わないものは明示的に除外する

## 14. AI agent 作業時の注意

MS18-B1をAI agentに依頼する場合は、以下を明示する。

```text
今回は MS18-B1: Repo / Release Readiness / Risk Inventory の作業です。

このBlockでは、実装変更を行わないでください。
コード変更、ドキュメント変更、リファクタリング、テスト修正、新機能追加は禁止です。

main / origin/main を正本として扱ってください。
feature/MS17 は古い状態として扱い、正本にしないでください。

まず以下を順に実行してください。

git status
git branch
git log --oneline -n 10
git remote -v
git fetch origin
git status
git log --oneline -n 10 origin/main
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
git ls-files cache

確認対象は以下です。

README.md
readme_mmdautolip.txt
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
.gitignore
build.ps1
MMD_AutoLipTool.spec
pyproject.toml

確認してください。

- local main が origin/main と同期しているか
- feature/MS17 に残った古い状態を見ていないか
- MS17-B9 closeout が main に反映されているか
- cache/ が Git 追跡対象外になっているか
- README / NOTICE / THIRD_PARTY_LICENSES.md / docs/Release_Package_Manifest.md が MS17 状態に同期されているか
- build.ps1 -SmokeLaunch の PyInstaller プロセス残留が残課題として記録されているか
- 実MMD確認がリリース前確認へ引き継がれているか
- FFmpeg build の --enable-gpl --enable-version3 に関する第三者ライセンス通知確認が残課題として記録されているか
- MS18-B2以降へ引き継ぐべきリスクが何か

完了報告では、以下を必ず記載してください。

1. 現在ブランチ
2. local main / origin/main の同期状態
3. 最新コミット
4. working tree / staged 差分の有無
5. git ls-files cache の結果
6. 確認したファイル
7. MS17 closeout 反映確認
8. cache追跡対象外化確認
9. release readiness 上の残課題
10. P1 / P2 / P3 リスク分類
11. MS18-B2以降への引き継ぎ
12. 実装変更を行っていないこと
```

## 15. MS18-B1 Completion Report

実施日: 2026-06-28

MS18-B1 は、実装変更を行わず、repo 状態確認、MS17 closeout 反映確認、release readiness 棚卸し、risk inventory を実施した。

## 1. Git状態

- Current branch: `feature/MS18`
- Latest local commit: `51ecfe2 Document sandbox command constraints`
- Latest local main commit: `1099a79 Exclude generated cache files from tracking`
- Latest origin/main commit after `git fetch origin`: `1099a79 Exclude generated cache files from tracking`
- local main / origin/main: 一致
- Working tree: 既存の `.gitignore` 差分あり
- Staged diff: なし

既存の `.gitignore` 差分は以下のみ。

```diff
+.codex/config.toml
```

これは repo-local Codex 設定を Git 追跡対象から外すためのローカル運用差分であり、MS18-B1 の製品実装変更ではない。

## 2. 実行コマンド

```powershell
git status
git branch
git log --oneline -n 10
git remote -v
git fetch origin
git status
git log --oneline -n 10 origin/main
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
git ls-files cache
```

追加確認:

```powershell
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
rg -n "MS17|MS18|WAV / MP3 / M4A|MMD用WAV|LICENSE|NOTICE|THIRD_PARTY|SmokeLaunch|実MMD|FFmpeg|cache|Release" README.md readme_mmdautolip.txt NOTICE THIRD_PARTY_LICENSES.md docs\Release_Package_Manifest.md docs\repo_milestone.md docs\Version_Control.md
```

## 3. 確認ファイル

- `README.md`
- `readme_mmdautolip.txt`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`
- `docs/Release_Package_Manifest.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS18_Block_Breakdown.md`
- `.gitignore`
- `build.ps1`
- `MMD_AutoLipTool.spec`
- `pyproject.toml`
- `requirements.txt`

## 4. 確認結果

### 4.1 MS17 closeout

- 判定: OK
- 根拠:
  - `origin/main` 直近履歴に `bf93a42 Complete MS17 B9 closeout` と `1099a79 Exclude generated cache files from tracking` が含まれる。
  - `docs/repo_milestone.md` 先頭に MS17-B9 closeout と cache追跡対象外化の追補が記録されている。
  - `docs/Version_Control.md` の上位エントリに `ms17-b9-closeout-doc-sync` と `ms17-cache-untrack` が記録されている。
  - `README.md` は `Ver. 0.4.0.0` / MS17 closeout 完了状態を示している。

### 4.2 cache追跡対象外化

- 判定: OK
- `git ls-files cache` 結果: 出力なし
- 根拠:
  - `cache/` は Git 追跡対象外。
  - `docs/Release_Package_Manifest.md` でも `cache/` は配布ZIP除外対象に含まれている。

### 4.3 README / 配布関連文書

- README: OK。wav / mp3 / m4a 入力、解析用WAV、専用の MMD用WAV出力、FFmpeg配置、配布時の `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` 参照が記録されている。
- `readme_mmdautolip.txt`: OK。配布用案内として WAV / MP3 / M4A、MMD用WAV出力、ライセンス同梱物が記録されている。
- NOTICE: OK。FFmpeg手動配置、MS17時点の staged build、配布時の同梱文書が記録されている。
- THIRD_PARTY_LICENSES.md: OK。ただし FFmpeg build configuration が `--enable-gpl --enable-version3` を含むため、配布前に該当license noticeの最終確認が必要。
- Release_Package_Manifest: OK。`LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` の同梱、`cache/` 除外、FFmpeg license確認条件が記録されている。

### 4.4 残課題

- SmokeLaunch: `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留は未解決。MS18-B5へ引き継ぐ。
- 実MMD確認: Codex側の実MMD読み込み・再生確認は未実施。MS18-B7へ引き継ぐ。
- FFmpeg license notice: 現在配置済みの FFmpeg / ffprobe は `N-123549-g70537ec8e6-20260318` で、`--enable-gpl --enable-version3` を含む。MS18-B6へ引き継ぐ。
- package同梱物: Manifest上の対象/除外は記録済み。実際のrelease package確認はMS18-B6へ引き継ぐ。

## 5. Risk Inventory

### P1

- なし。

### P2

- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留原因が未確定。
  - 引き継ぎ先: MS18-B5
- FFmpeg / ffprobe の配布時license noticeが、現在配置済みbuild configurationに対して未確定。
  - 引き継ぎ先: MS18-B6
- 実MMD上での VMD / MMD用WAV 読み込み・再生確認が未完了。
  - 引き継ぎ先: MS18-B7
- 外部ファイル入力、subprocess、temp / cache、GUI worker、PyInstaller onefile のセキュリティ事前確認が未実施。
  - 引き継ぎ先: MS18-B2

### P3

- `.gitignore` に `.codex/config.toml` を追加する既存差分がある。
  - 製品実装には影響しないが、B1完了後のコミット範囲確認時に混入有無を明記する。
- MS18関連ドキュメントは Draft 表記を維持している。
  - B1完了状態は本完了報告と関連ドキュメントの進行状況欄で同期する。

## 6. MS18-B2以降への引き継ぎ

### MS18-B2 Security Preflight Review

- 外部ファイル入力、ffprobe / ffmpeg 実行経路、subprocess引数、shell injection相当リスク、temp / cache / 出力ファイル処理、GUI worker / Busy状態、PyInstaller onefile展開先、エラーメッセージ情報露出を確認する。

### MS18-B3 Refactor Scope Definition

- MS18-B2のP1/P2/P3結果をもとに、MS18-B4で変更してよいファイル・変更禁止範囲・挙動非変更の確認方法を固定する。

### MS18-B5 SmokeLaunch / Process Residual Investigation

- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留について、原因調査、修正可否、または保留判断を記録する。

### MS18-B6 Release / Packaging / License Preflight

- `MMD_AutoLipTool.spec`、`build.ps1`、`docs/Release_Package_Manifest.md`、`NOTICE`、`THIRD_PARTY_LICENSES.md` を、実際に配布するFFmpeg buildとrelease package構成に対して確認する。

### MS18-B7 Actual MMD Manual Verification Closeout

- 実際の MikuMikuDance 上で、VMD と MMD用WAV の読み込み・再生を確認し、MS18 closeout判定へ反映する。

## 7. 変更有無

- Code changes: なし
- Docs changes: あり。本完了報告、および関連進行状況文書へ MS18-B1 closeout を反映する。
- Other changes: B1実施前から `.gitignore` に既存差分あり。B1ではこの差分を戻していない。

## 8. 判定

- MS18-B1 closeout: OK
- 次に進むBlock: `MS18-B2: Security Preflight Review`

## 16. 次作業

MS18-B1は完了した。

MS18-B1完了後は、確認結果に基づいて MS18-B2 へ進む。

次作業は以下とする。

```text
MS18-B2: Security Preflight Review
```

MS18-B2では、MS18-B1で棚卸ししたリスクをもとに、MMD_AutoLipTool 固有のセキュリティ観点を確認する。

MS18-B2でも原則として実装変更は行わず、セキュリティ上の問題を P1 / P2 / P3 に分類し、必要な修正を MS18-B3 / B4 へ引き継ぐ。
