# MS18 Block Breakdown

## 1. 文書情報

- 文書名: MS18 Block Breakdown
- 想定配置先: `docs/Implementation_Plan/MS18_Block_Breakdown.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 基準ブランチ: `main`
- 正本:
  - `main / origin/main`
- 非正本:
  - `feature/MS17`
- 関連ロードマップ:
  - `docs/MS18_and_Beyond_Roadmap.md`
- 作成日: 2026-06-03
- 文書ステータス: Draft
- 現在ステータス:
  - MS18-B1 Repo / Release Readiness / Risk Inventory 完了
  - MS18-B2 Security Preflight Review 完了
  - MS18-B3 Refactor Scope Definition 完了
  - MS18-B4 Safe Refactor Implementation 完了
  - MS18-B5 SmokeLaunch / Process Residual Investigation 完了
  - MS18-B6 Release / Packaging / License Preflight 完了
  - MS18-B7 Actual MMD Manual Verification Closeout 完了。ユーザー確認通過・問題なし
  - MS18 closeout判定はA。MS18 CloseOut完了。

## 2. 背景

MS17では、wxPython 主系上での音声入力拡張、解析用WAV生成、MMD用WAV出力、音声処理 worker 化、Busy制御、キャンセル導線、MS17-B9 closeout まで完了した。

MS17 closeout 後の追補として、`cache/` は Git 追跡対象外となり、`cache/analysis_wav/` 配下の解析用WAVは Git 管理から外された。

MS18では、すぐに新機能追加へ進まず、リリース / package 化前の安定化を行う。

MS18の主眼は以下である。

- リリース前リスク棚卸し
- セキュリティチェック
- 処理効率化
- 重複コード整理
- 挙動非変更の安全なリファクタリング
- `build.ps1 -SmokeLaunch` のプロセス残留調査
- FFmpeg 同梱配布時のライセンス通知確認
- 実MMD確認
- package 化へ進めるかの判断材料整理

## 3. MS18の位置づけ

MS18は、新機能追加マイルストーンではない。

MS18は、MS17 closeout 済みの実装を、公開・配布に進める前に安全化・安定化するためのマイルストーンである。

MS18では、挙動非変更を原則とする。  
ただし、セキュリティ上必要な修正、明確な重複整理、処理効率上の小規模改善、配布前に必要な修正は対象に含める。

## 4. MS18で扱うもの

MS18で扱うものは以下とする。

- `main / origin/main` の正本確認
- MS17 closeout 状態の確認
- `cache/` 追跡対象外化の確認
- リリース前残課題の棚卸し
- セキュリティ観点の事前確認
- subprocess / ffmpeg / ffprobe 実行経路の確認
- temp / cache / 出力ファイル処理の確認
- 重複コード・非効率処理の確認
- 挙動非変更の安全なリファクタリング
- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留原因調査
- Release package の同梱物・除外物確認
- FFmpeg build configuration と第三者ライセンス通知確認
- 実MMDでの VMD / MMD用WAV 読み込み確認
- MS18 closeout 記録

## 5. MS18で扱わないもの

MS18では、以下を扱わない。

- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- 英語対応
- VMD writer の全面再設計
- pipeline の意味論変更
- Preview / waveform の仕様変更
- GUI レイアウト刷新
- 音声解析品質の大幅変更
- Whisper / pyopenjtalk 周辺の機能追加
- installer 導入
- CI/CD workflow の大規模追加
- FFmpeg build の変更
- 新しい配布方式への全面移行

## 6. MS18全体の受け入れ条件

MS18全体の完了条件は以下とする。

- `main / origin/main` を正本として確認している
- MS17 closeout 状態が維持されている
- `cache/` の Git 追跡対象外化が維持されている
- セキュリティ観点の確認結果が記録されている
- 必要なリファクタリングが挙動非変更の範囲で完了している
- `build.ps1 -SmokeLaunch` のプロセス残留について、原因・修正・保留判断のいずれかが記録されている
- FFmpeg 同梱配布時のライセンス通知方針が整理されている
- Release package の同梱物・除外物が整理されている
- 実MMD確認結果が記録されている
- package 化へ進めるかどうかを判断できる状態になっている
- MS19へ進む前提条件が整理されている

## 7. MS18 Block 一覧

```text
MS18-B1: Repo / Release Readiness / Risk Inventory
MS18-B2: Security Preflight Review
MS18-B3: Refactor Scope Definition
MS18-B4: Safe Refactor Implementation
MS18-B5: SmokeLaunch / Process Residual Investigation
MS18-B6: Release / Packaging / License Preflight
MS18-B7: Actual MMD Manual Verification Closeout
````

## 8. Block依存関係

```text
MS18-B1
  ↓
MS18-B2
  ↓
MS18-B3
  ↓
MS18-B4
  ↓
MS18-B5
  ↓
MS18-B6
  ↓
MS18-B7
```

原則として、上記順に進める。

ただし、MS18-B5 の `SmokeLaunch` 調査は、MS18-B4 のリファクタリング結果に影響を受ける可能性があるため、B4完了後に行う。

MS18-B6 の packaging / license preflight は、B4の差分とB5の調査結果を反映した状態で行う。

MS18-B7 の実MMD確認は、B6で release package 前提が整理された後に行う。

## 9. MS18-B1: Repo / Release Readiness / Risk Inventory

### 9.0 ステータス

完了。

2026-06-28 に `feature/MS18` 上で、`main / origin/main` の同期、MS17-B9 closeout反映、`cache/` 追跡対象外化、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の同期状態、release readiness risk inventory を確認した。

P1は検出していない。B1時点でMS18-B2以降へ送るP2として、Security Preflight未実施、`build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因未確定、FFmpeg license notice最終確認未完了、実MMD確認未完了を記録した。Security Preflight未実施はMS18-B2で解消済み。

### 9.1 目的

MS18開始時点の `main / origin/main` を正本として、現在状態・残課題・リリース前リスクを棚卸しする。

このBlockでは、実装変更を行わない。

### 9.2 In Scope

* `main / origin/main` の同期確認
* `feature/MS17` を参照していないことの確認
* 最新コミット確認
* MS17-B9 closeout 反映確認
* MS17 closeout 後追補の `cache/` Git追跡対象外化確認
* `README.md` の MS17 状態確認
* `NOTICE` の MS17 状態確認
* `THIRD_PARTY_LICENSES.md` の MS17 状態確認
* `docs/Release_Package_Manifest.md` の MS17 状態確認
* `docs/repo_milestone.md` の残課題確認
* `docs/Version_Control.md` の残課題確認
* MS18で扱うリスクの P1 / P2 / P3 分類
* MS18-B2以降で扱う対象の整理

### 9.3 Out of Scope

* コード変更
* ドキュメント変更
* リファクタリング
* セキュリティ修正
* packaging 実作業
* 実MMD確認
* 新機能実装

### 9.4 主な確認コマンド

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

### 9.5 主な確認ファイル

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
docs/MS18_and_Beyond_Roadmap.md
```

### 9.6 成果物

* MS18開始時点の repo 状態確認結果
* リリース前リスク一覧
* MS18内で扱う項目 / 扱わない項目の分類
* MS18-B2以降の作業前提

### 9.7 受け入れ条件

* `main / origin/main` を正本として確認している
* `feature/MS17` が古い状態であることを確認している
* MS17-B9 closeout が main に反映済みであることを確認している
* `cache/` が Git 追跡対象外であることを確認している
* MS18で扱うべきリスクが分類されている
* 実装変更が行われていない

## 10. MS18-B2: Security Preflight Review

### 10.0 ステータス

完了。

2026-06-28 に `feature/MS18` 上で、外部ファイル入力、ffprobe / ffmpeg 実行経路、subprocess引数、shell injection相当リスク、FFmpeg / ffprobe探索順、自動ダウンロード禁止、temp / cache / 出力ファイル処理、GUI worker / Busy状態、PyInstaller onefile、エラーメッセージ / 情報露出、FFmpeg license / release readinessを確認した。

Security PreflightとしてP1は検出していない。対象テスト42件は通過した。P2として、FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定、`build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因未確定、実MMD確認未完了を後続Blockへ引き継いだ。P3として、PATH fallback時の説明改善、`error.log` / 開発コンソールのローカル診断情報、cacheファイル名のstem、`build.ps1 -Clean` の旧onefile成果物明示削除なしを記録した。

### 10.1 目的

リリース / package 化前に、MMD_AutoLipTool 固有のセキュリティ観点を確認する。

一般的な抽象チェックではなく、Windows ローカルGUIアプリ、音声ファイル入力、FFmpeg / ffprobe 実行、PyInstaller onefile 配布という実態に即して確認する。

このBlockでは、原則として調査・分類を行い、実装修正は行わない。
ただし、P1相当の重大問題が見つかった場合は、MS18-B3 / B4 の修正対象として記録する。

### 10.2 In Scope

* 外部ファイル読み込みの確認
* wav / mp3 / m4a 入力時の制限確認
* ファイルサイズ上限の確認
* 音声長さ上限の確認
* ffprobe 実行経路の確認
* ffmpeg 実行経路の確認
* subprocess 実行時の引数渡し確認
* shell injection 相当の危険がないかの確認
* 自動ダウンロードを行っていないことの確認
* `FFmpeg\bin\` 優先探索と `PATH` fallback の確認
* temp / cache / 出力ファイル処理の確認
* 上書き確認処理の確認
* 失敗時 cleanup の確認
* ローカルパスや不要情報をエラー表示しすぎていないかの確認
* PyInstaller onefile 展開・同梱物の確認
* 配布ZIPに不要ファイルが混入するリスク確認

### 10.3 Out of Scope

* 暗号化機能追加
* ネットワーク通信機能追加
* sandbox 化
* 外部セキュリティ監査
* 依存関係の全面入れ替え
* FFmpeg build の変更
* 実装修正
* 新機能実装

### 10.4 主な確認ファイル

```text
src/core/ffmpeg_locator.py
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/audio_errors.py
src/core/mmd_wav_export.py
src/gui_wx/app_controller.py
src/gui_wx/audio_worker.py
build.ps1
MMD_AutoLipTool.spec
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/Release_Package_Manifest.md
THIRD_PARTY_LICENSES.md
NOTICE
```

### 10.5 リスク分類

Security Preflight の結果は、以下に分類する。

```text
P1:
  リリース前に必ず修正すべき重大問題。
  例: shell=True 相当の危険な実行、任意パス上書き、不要な自動ダウンロード、cleanup不備による破損など。

P2:
  MS18内で修正することが望ましい問題。
  例: エラー時 cleanup の不足、表示メッセージの過剰情報、例外分類不足、重複処理による保守リスクなど。

P3:
  記録・表現・将来改善でよい問題。
  例: コメント不足、docs表現の不足、将来の管理UI候補など。
```

### 10.6 成果物

* Security Preflight 結果
* P1 / P2 / P3 分類
* MS18-B3 / B4 へ渡す修正候補
* 修正不要と判断した項目の理由

### 10.7 受け入れ条件

* MMD_AutoLipTool 固有のセキュリティ観点が確認されている
* 結果が P1 / P2 / P3 に分類されている
* MS18-B4で修正する候補が整理されている
* 実装変更が行われていない

## 11. MS18-B3: Refactor Scope Definition

### 11.0 ステータス

完了。

2026-06-29 に `feature/MS18` 上で、MS18-B2のP2/P3をMS18-B4で扱う項目・扱わない項目へ分類した。B2でP1は検出されておらず、B4へ必須投入すべきP2もない。

B4で扱ってよい候補は、PATH fallback時の探索元説明性改善、および `error.log` / 開発コンソールの診断情報扱いの小規模整理に限定した。`build.ps1 -SmokeLaunch` と `build.ps1 -Clean` はMS18-B5、FFmpeg license / package確認とcache配布除外確認はMS18-B6、実MMD確認はMS18-B7へ送る。

### 11.1 目的

MS18で行うリファクタリング範囲を、挙動非変更・処理効率化・セキュリティ上必要な最小修正に限定して定義する。

このBlockでは、実装変更を行わない。

### 11.2 In Scope

* MS18-B2で見つかった修正候補の確認
* 重複コードの確認
* 明確に非効率な処理の確認
* ffmpeg / ffprobe runner 周辺の責務確認
* audio worker 周辺の責務確認
* GUI controller 内の肥大化箇所確認
* temp / cache / 出力ファイル処理の重複確認
* エラー分類・例外処理の重複確認
* テスト対象の確認
* MS18-B4で変更してよいファイルの確定
* MS18-B4で変更してはいけない範囲の確定

### 11.3 Out of Scope

* 実装変更
* ドキュメント変更
* 大規模再設計
* pipeline 契約変更
* VMD writer 再設計
* GUI レイアウト刷新
* 新機能追加
* 音声のみ入力対応
* モーフ編集機能

### 11.4 主な確認ファイル

```text
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/mmd_wav_export.py
src/gui_wx/app_controller.py
src/gui_wx/audio_worker.py
src/gui_wx/ui_state.py
src/core/audio_errors.py
tests/
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
```

### 11.5 MS18で許可するリファクタリング

```text
- 重複コードの整理
- 明確に無駄な処理の削減
- 例外処理の整理
- エラー分類の整理
- subprocess / ffmpeg / ffprobe 実行まわりの安全性改善
- temp / cache / 出力ファイル処理の安全化
- パス処理の小規模整理
- テストしやすさを高めるための小規模責務分離
- docs と実装状態の同期
```

### 11.6 MS18で禁止するリファクタリング

```text
- pipeline の意味論変更
- VMD writer の再設計
- GUI 状態遷移の大幅変更
- Preview / waveform の仕様変更
- 音声解析アルゴリズムの品質変更
- 設定 schema の大幅変更
- ディレクトリ構造の大規模再編
- 任意モーフ対応への先行実装
- 音声のみ入力対応への先行実装
```

### 11.7 成果物

* MS18-B4 の実装対象一覧
* 変更許可ファイル一覧
* 変更禁止範囲
* テスト方針
* リファクタリング時の注意事項

### 11.8 受け入れ条件

* MS18-B4で実施する作業範囲が固定されている
* 変更禁止範囲が明記されている
* 挙動非変更の確認方法が定義されている
* 実装変更が行われていない

## 12. MS18-B4: Safe Refactor Implementation

### 12.0 ステータス

完了。

2026-06-30 に `feature/MS18` 上で、MS18-B3で許可された範囲に限定して、FFmpeg / ffprobe探索元説明性改善を実装した。

`src/core/ffmpeg_locator.py` に探索結果をユーザー向け診断文へ整形する補助関数を追加し、`src/gui_wx/app_controller.py` のFFmpeg / ffprobe未検出メッセージへ反映した。探索順、PATH fallback可否、自動ダウンロード禁止方針、GUI状態遷移、worker起動順は変更していない。

ユーザーチェックで発生した解析用WAV再生エラーは、Windows MCIが長い解析用WAVファイル名を拒否することが原因だった。`src/gui_wx/playback_controller.py` で、MCI再生時のみ短い一時ファイル名 `p.wav` のコピーを使うよう修正した。

対象テストは `tests/test_ms17_b3_ffmpeg_locator.py` 8件、`tests/test_wx_ms14_b3_input.py` 2件、`tests/test_wx_ms15_b3_playback.py` 10件が通過した。ユーザーチェックでも、解析後のWAVファイル再生エラーが解消し、ユーザーテスト通過が報告された。

### 12.1 目的

MS18-B3で確定した範囲に限定して、挙動非変更の安全なリファクタリングを実施する。

### 12.2 In Scope

* MS18-B3で許可されたファイルの変更
* PATH fallback時の探索元説明性改善
* `error.log` / 開発コンソールの診断情報扱いの小規模整理
* 上記に直接必要な限定テスト追加・更新
* B4実施内容に直接関係する履歴文書同期
* 差分レビュー

### 12.3 Out of Scope

* MS18-B3で定義していない変更
* `build.ps1` / SmokeLaunch / Clean手順変更
* FFmpeg license / package manifest / release package同梱物確定
* cache命名規則変更
* pipeline の意味論変更
* VMD 出力仕様変更
* GUI 操作仕様変更
* Preview / waveform 仕様変更
* 新機能追加
* 音声のみ入力対応
* モーフ編集機能
* 英語対応
* 任意モーフ対応

### 12.4 想定対象ファイル

MS18-B3で確定したB4変更許可候補は以下とする。

```text
src/core/ffmpeg_locator.py
src/main.py
src/gui_wx/app_controller.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_wx_ms14_b3_input.py
docs/Error_Handling_Specification.md
docs/repo_milestone.md
docs/Version_Control.md
```

### 12.5 テスト方針

MS18-B4では、変更範囲に応じて限定テストを実行する。

候補は以下。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
```

診断/通知導線に触れる場合は、関連GUIテストも実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
```

全体テストを実行する場合は、既知の wx teardown 由来の終了コード不安定性があるため、表示上の pass 数と終了コードを分けて記録する。

### 12.6 成果物

* リファクタリング差分
* 必要なテスト更新
* 実行テスト結果
* docs 同期差分
* MS18-B4 実施結果記録

### 12.7 受け入れ条件

* 差分が MS18-B3 の定義範囲内である
* 既存機能の挙動変更がない
* 関連テストが通過している
* MS17で実装済みの音声入力・解析用WAV・MMD用WAV出力・worker状態管理が壊れていない
* 実行したテストと未実行テストが報告されている
* 残課題が記録されている

## 13. MS18-B5: SmokeLaunch / Process Residual Investigation

### 13.1 目的

`build.ps1 -SmokeLaunch` における PyInstaller プロセス残留・タイムアウト原因を調査し、release / package 化前に扱いを確定する。

### 13.2 In Scope

* `build.ps1` の現行処理確認
* `-SmokeLaunch` の処理確認
* PyInstaller 実行後のプロセス状態確認
* 生成済み `dist\MMD_AutoLipTool.exe` の起動スモーク確認
* `Start-Process` / `Stop-Process` の挙動確認
* 5秒起動スモーク確認の妥当性確認
* 残留プロセスが PyInstaller 由来か、アプリ由来か、wx event loop 由来かの切り分け
* build script 側の最小修正検討
* 修正しない場合のリリース前手順化

### 13.3 Out of Scope

* build system の全面置き換え
* installer 導入
* CI/CD workflow の大規模追加
* PyInstaller 以外の配布方式への移行
* GUI 起動設計の大規模変更
* アプリ終了処理の全面再設計

### 13.4 主な確認ファイル

```text
build.ps1
MMD_AutoLipTool.spec
src/main.py
src/gui_wx/app.py
src/gui_wx/main_frame.py
docs/Release_Package_Manifest.md
docs/Version_Control.md
```

### 13.5 主な確認コマンド候補

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
Get-Process -Name MMD_AutoLipTool -ErrorAction SilentlyContinue
Get-Process -Name pyinstaller -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue
```

必要に応じて、生成済み exe の単独起動確認を行う。

```powershell
Start-Process -FilePath .\dist\MMD_AutoLipTool.exe -PassThru
```

### 13.6 成果物

* SmokeLaunch 残留原因の調査結果
* 修正有無の判断
* 修正した場合の差分
* 修正しない場合のリリース前手順
* build / smoke 確認結果

### 13.7 受け入れ条件

* `build.ps1 -SmokeLaunch` の残留原因が説明されている
* MS18内で修正するか、保留するかが判断されている
* 修正する場合は最小差分である
* 修正しない場合は release preflight に手順として反映されている
* package 化前に使う起動確認手順が整理されている

### 13.8 実施結果

2026-07-01 に `feature/MS18` 上で実施した。

* 初回観測では、既存 `build.ps1 -Clean -SmokeLaunch` は成功表示し、直後の `MMD_AutoLipTool` / `pyinstaller` / `python` 残留は確認されなかった。
* 停止待機を追加した検証中に、`Stop-Process` 後10秒では `MMD_AutoLipTool.exe` が終了しきらないケースを確認した。確認後にはプロセスが消えていたため、恒久残留ではなく、onefile起動後の外部停止完了待ち不足と分類した。
* `build.ps1` を最小修正し、`-Clean` 時に旧 `dist\MMD_AutoLipTool.exe` を明示削除するようにした。
* SmokeLaunchでは、起動前の同一exeパス既存PIDを記録し、起動したPIDを停止後、最大30秒まで終了をポーリングするようにした。
* 同一 `dist\MMD_AutoLipTool.exe` パスに限定して残留PIDを確認し、既存PIDは停止対象から除外するようにした。
* `powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch` は通過した。
* `powershell -ExecutionPolicy Bypass -File .\build.ps1` は通過した。
* SmokeLaunch後の `MMD_AutoLipTool` / `pyinstaller` / `python` 残留は確認時点でなし。
* ユーザーテスト通過が報告された。
* PyInstallerログ上、Matplotlib backend収集で `PySide6` hook が選択されている。B5範囲外のため、MS18-B6で配布内容・依存関係確認として扱う。

## 14. MS18-B6: Release / Packaging / License Preflight

### 14.1 目的

実行用ZIPまたは GitHub Release 向け配布物を作成する前に、同梱物・除外物・ライセンス通知・FFmpeg配布条件を確認する。

### 14.2 In Scope

* `README.md` の配布前同期確認
* `readme_mmdautolip.txt` の配布前同期確認
* `LICENSE` の存在確認
* `NOTICE` の内容確認
* `THIRD_PARTY_LICENSES.md` の内容確認
* `docs/Release_Package_Manifest.md` の内容確認
* FFmpeg / ffprobe の version 確認
* FFmpeg / ffprobe の build configuration 確認
* `--enable-gpl --enable-version3` を含む build への第三者ライセンス通知確認
* 実行用ZIPに含めるものの確認
* 実行用ZIPに含めないものの確認
* `cache/`、`build/`、`src/`、`tests/`、`.venv/` などが混入しないことの確認
* GitHub Release 本文に必要な注意事項の整理
* Windows Defender 等で不審に見えにくい配布説明の確認
* package 化へ進めるかどうかの判定

### 14.3 Out of Scope

* 実際の GitHub Release 公開
* installer 作成
* FFmpeg build の変更
* ライセンス解釈の法的断定
* 自動 release workflow の新規構築
* 有償コード署名導入
* 配布方式の全面変更

### 14.4 主な確認ファイル

```text
README.md
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
pyproject.toml
.gitignore
```

### 14.5 実行用ZIPの想定同梱物

```text
MMD_AutoLipTool.exe
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
FFmpeg 関連 license texts
```

`sample/` を含めるかどうかは、MS18-B6で確認する。
含める場合は、サンプルデータのライセンス・出典・用途説明を確認する。

### 14.6 実行用ZIPから除外するもの

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
```

### 14.7 成果物

* Release / Packaging / License Preflight 結果
* 同梱物一覧
* 除外物一覧
* FFmpeg license notice 確認結果
* 未確定事項一覧
* package 化可否判定

### 14.8 受け入れ条件

* 配布前チェックリストが確認されている
* 同梱必須ファイルが明確である
* 除外対象が明確である
* FFmpeg build configuration と license notice の扱いが明確である
* package 化へ進めるかどうか判断できる
* 実公開は行っていない

### 14.9 実施結果

2026-07-02 に `feature/MS18` 上で実施した。

* `README.md` / `readme_mmdautolip.txt` / `NOTICE` / `THIRD_PARTY_LICENSES.md` / `docs/Release_Package_Manifest.md` の配布前記述を確認した。
* `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe` は `N-123549-g70537ec8e6-20260318` として実行可能で、configurationに `--enable-gpl --enable-version3` を含むことを確認した。
* `git ls-files FFmpeg/bin` により、FFmpeg実体ファイルがGit追跡対象であることを確認した。GitHub自動生成 Source code ZIP / tar.gz にもFFmpegバイナリが含まれる前提でlicense notice確認が必要である。
* リポジトリ内にFFmpeg本体に対応する個別license texts / COPYING類は未確認。
* PyInstaller xrefに `PySide6` / `PySide6.QtCore` / `PySide6.QtGui` / `PySide6.QtWidgets` 参照が存在することを確認した。Qt / PySide GUI復活ではなく、配布内容・依存関係・license notice確認項目として扱う。
* `sample/` には音声・テキスト・pipeline生成用ディレクトリが存在する。出典・ライセンス・用途説明が未確定のため、実行用ZIPから除外する方針とした。
* package化可否判定は、2026-07-02時点では追加確認が必要とした。2026-07-03のMS18 CloseOut時点で、FFmpeg license texts / notice、FFmpeg実体をGit追跡に残すかどうか、PySide6関連モジュールの最終成果物混入有無はユーザー判断によりクリア扱いとした。

## 15. MS18-B7: Actual MMD Manual Verification Closeout

### 15.1 目的

リリース前確認として、実際の MikuMikuDance 上で VMD と MMD用WAV の読み込み・再生確認を行い、MS18を closeout する。

### 15.2 In Scope

* 実MMDでの VMD 読み込み確認
* 実MMDでの MMD用WAV 読み込み確認
* MMD上での音声再生確認
* リップモーション同期の目視確認
* 生成ファイル配置手順の確認
* README / readme_mmdautolip.txt への反映要否確認
* MS18 closeout 記録
* MS19へ進む前提条件整理

### 15.3 Out of Scope

* MMD本体の不具合調査
* モデル固有のモーフ差異対応
* VMD writer の品質改善
* 音声解析品質改善
* 音声のみ入力対応
* モーフ編集機能
* 任意モーフ対応

### 15.4 確認対象

```text
生成済み VMD
生成済み MMD用WAV
MikuMikuDance 本体
テスト用 MMDモデル
README.md
readme_mmdautolip.txt
docs/repo_milestone.md
docs/Version_Control.md
```

### 15.5 確認観点

```text
- VMDをMMDに読み込めるか
- MMD用WAVをMMDに読み込めるか
- 音声が再生されるか
- リップモーションが再生されるか
- 音声とリップモーションの大きなズレがないか
- MMD側で扱いにくいファイル名・出力形式になっていないか
- ユーザー向け手順に不足がないか
```

### 15.6 成果物

* 実MMD確認結果
* 確認に使った VMD / WAV の条件
* 問題有無
* README / readme 反映要否
* MS18 closeout 判定
* MS19開始前の残課題

### 15.7 受け入れ条件

* 実MMD確認結果が記録されている
* VMD / MMD用WAV の読み込み可否が明確である
* リリース前に残す課題が明確である
* MS18 closeout 判定が記録されている
* MS19へ進めるかどうか判断できる

### 15.8 実施結果

2026-07-03 に実施した。

* Codex側でB7確認用の一時生成物を用意した。
  * VMD: `C:\tmp\autolip_ms18_b7\ms18_b7_sample_input2.vmd`
  * MMD用WAV: `C:\tmp\autolip_ms18_b7\ms18_b7_sample_input2_mmd.wav`
  * MMD用WAV仕様: `pcm_s16le / 44100Hz / 2ch`
* MMD用WAV出力関連テストを実行し、`10 passed` で通過した。
* ユーザーから「ユーザー確認通過。問題無し。」との報告を受けた。
* 実MMDでのVMD読み込み、MMD用WAV読み込み、音声再生、リップ同期目視確認は通過として扱う。
* B7内でREADME / readme_mmdautolip.txtへ追加修正が必要な手順不足やエラーは報告されていない。
* `sample/` 由来の生成物はローカル確認用であり、release証跡や同梱可否判断の根拠にはしない。
* B6由来のpackage化前P2は、B7結果とは分離して扱ったうえで、2026-07-03のユーザー判断によりクリア扱いとする。

## 16. MS18全体のテスト方針

MS18では、新機能追加を行わないため、テストは変更範囲に応じた限定テストを優先する。

ただし、リファクタリングやセキュリティ修正を行った場合は、関連する MS17 テストを必ず実行する。

### 16.1 基本方針

* 変更範囲に応じて限定テストを実行する
* GUI / wx 関連テストは既知の終了コード不安定性を考慮する
* 表示上の pass 数とプロセス終了コードを分けて記録する
* 全体 pytest を実行する場合は、ハングや終了コード不安定性を記録する
* テスト未実行の場合は、理由を明記する

### 16.2 非GUI寄りテスト候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
```

### 16.3 GUI / wx 関連テスト候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

### 16.4 build / smoke 確認候補

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

## 17. MS18で更新する可能性があるドキュメント

MS18では、実装差分や確認結果に応じて以下を更新する可能性がある。

```text
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-Bx_Implementation_Plan.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Release_Package_Manifest.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
README.md
readme_mmdautolip.txt
NOTICE
THIRD_PARTY_LICENSES.md
```

README はエンドユーザー向け文書であるため、開発者向けの詳細な MS18 内部計画は記載しない。
README には、実際の利用・配布・注意事項に関係する内容だけを反映する。

## 18. AI agent 作業時の共通指示

AI agent に MS18 作業を依頼する場合は、以下を共通指示とする。

```text
- main / origin/main を正本として扱うこと。
- feature/MS17 は古い状態として扱い、正本にしないこと。
- 作業開始時に git status / git branch / git log / git fetch origin を確認すること。
- 実装するBlockと、確認のみのBlockを混同しないこと。
- 新機能を追加しないこと。
- 音声のみ入力対応を先行実装しないこと。
- モーフ編集機能を先行実装しないこと。
- pipeline の意味論を変更しないこと。
- VMD writer を再設計しないこと。
- GUI レイアウトを刷新しないこと。
- リファクタリングは挙動非変更を原則とすること。
- セキュリティ修正は必要最小限に限定すること。
- 変更したファイル、確認したファイル、実行したテスト、未実行テスト、残課題を報告すること。
```

## 19. Block別の実装可否

```text
MS18-B1:
  実装変更なし。
  repo状態確認とリスク棚卸しのみ。

MS18-B2:
  実装変更なし。
  セキュリティ確認と分類のみ。

MS18-B3:
  実装変更なし。
  リファクタリング範囲定義のみ。

MS18-B4:
  実装変更あり。
  ただし、MS18-B3で定義した範囲に限定する。

MS18-B5:
  必要に応じて実装変更あり。
  build.ps1 などの最小修正に限定する。

MS18-B6:
  原則として確認と文書同期。
  package 化そのものや GitHub Release 公開は行わない。

MS18-B7:
  実MMD確認と closeout 記録。
  実装変更は原則なし。
  ユーザー向け手順不足が見つかった場合のみ docs / README / readme の小修正を検討する。
```

## 20. MS18 closeout 判定

MS18 closeout では、以下のいずれかで判定する。

```text
A. MS18 closeout OK。package 化へ進める。
B. MS18 closeout OK。ただし package 化前に軽微な確認事項あり。
C. MS18 closeout 保留。P1 / P2 の未解決課題あり。
D. MS18 closeout 不可。MS17実装または配布前提に重大な問題あり。
```

推奨判定基準は以下。

### A 判定

* セキュリティ P1 / P2 が残っていない
* SmokeLaunch の扱いが確定している
* FFmpeg ライセンス通知方針が確定している
* 実MMD確認が完了している
* package 化前チェックが通っている

### B 判定

* package 化前の軽微な文書確認のみ残っている
* 実装上の重大問題はない
* リリース作業に進めるが、手順上の注意が残っている

### 2026-07-03 時点の判定

```text
A. MS18 closeout OK。package 化へ進める。
```

判定理由:

* MS18-B7の実MMD確認は、ユーザー確認通過・問題なしとして記録済み。
* B7内でP1 / P2の実MMD問題は報告されていない。
* MS18-B6由来のpackage化前P2は、2026-07-03のユーザー判断によりクリア扱いとした。
* package化を止める未解決P1 / P2は残っていない。

CloseOut時点でクリア扱いとした項目:

* FFmpeg関連license texts / noticeを、実行用ZIPおよびGitHub Source code ZIP / tar.gzの両方の前提で確定する。
* `FFmpeg\bin\` の実体をGit追跡に残すか、配布用ビルド入力として別管理にするかを判断する。
* PyInstaller xref上の `PySide6` 関連モジュールが最終成果物へ入るか、license noticeが必要か、除外できるかを確認する。

`sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する方針を維持する。

### C 判定

* セキュリティ P2 が残っている
* SmokeLaunch の扱いが未確定
* FFmpeg license notice の確認が未完了
* 実MMD確認が未完了

### D 判定

* セキュリティ P1 が残っている
* VMD / MMD用WAV の実MMD読み込みに重大問題がある
* package 化に進むと誤配布・ライセンス不備・重大な利用不能につながる

## 21. MS19への引き継ぎ条件

MS19へ進む前提条件は以下。

* MS18 closeout が A または B である
* MS18で見つかった P1 / P2 が解消または明確に保留判断されている
* package 化へ進める状態、または package 化作業を別セッションで実行できる状態である
* 音声のみ入力対応に入る前に、TEXTあり既存導線が安定している
* MS19で扱う機能追加と、MS18の安定化作業が混ざっていない

## 22. 次作業

次作業は、MS19-B4 GUI Entry Point and State Handling の実装前チェック / 実装、またはMS18成果を前提にしたpackage / release作業である。

MS18-B6で検出したpackage化前追加確認事項は、2026-07-03のユーザー判断によりクリア扱いとした。
`sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する。

参照する計画文書は以下。

```text
docs/Implementation_Plan/MS18-B7_Implementation_Plan.md
docs/Implementation_Plan/MS18-B6_Implementation_Plan.md
docs/Implementation_Plan/MS18-B5_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS19-B1_Implementation_Plan.md
docs/Implementation_Plan/MS19_Block_Breakdown.md
docs/Release_Package_Manifest.md
```
