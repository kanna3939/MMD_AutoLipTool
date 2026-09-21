# MS18-B3 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B3 Implementation Plan
- 想定配置先: `docs/Implementation_Plan/MS18-B3_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 対象マイルストーン: MS18
- 対象Block: MS18-B3
- Block名: Refactor Scope Definition
- 基準ブランチ: `main`
- 正本:
  - `main / origin/main`
- 非正本:
  - `feature/MS17`
- 関連文書:
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS18-B2_Implementation_Plan.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Release_Package_Manifest.md`
- 作成日: 2026-06-03
- 文書ステータス: Completed
- 作業種別:
  - refactor scope definition
  - security findings triage
  - safe implementation boundary definition
  - MS18-B4実装前チェック
- 実装変更:
  - なし

## 2. 背景

MS18は、MS17 closeout 済みの実装を、リリース / package 化へ進める前に安全化・安定化するためのマイルストーンである。

MS18では、新機能追加を行わない。  
主対象は、リリース前確認、セキュリティチェック、処理効率化、重複コード整理、挙動非変更の安全なリファクタリング、SmokeLaunch残留調査、FFmpeg同梱配布時のライセンス通知確認、実MMD確認である。

MS18-B1では、repo状態、MS17 closeout反映、cache追跡対象外化、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の同期、MS18で扱うリスクの棚卸しを行う。

MS18-B2では、MMD_AutoLipTool 固有のセキュリティ観点を確認し、外部ファイル入力、ffmpeg / ffprobe 実行、subprocess、temp / cache、MMD用WAV出力、GUI worker、PyInstaller onefile、release package、FFmpeg license notice などのリスクを P1 / P2 / P3 に分類する。

MS18-B3では、MS18-B2の結果を受けて、MS18-B4で実装してよいリファクタリング・安全化修正の範囲を定義する。

このBlockでは、実装変更を行わない。  
コード変更、ドキュメント変更、テスト修正、新機能追加は行わず、MS18-B4の実装境界を固定する。

## 3. 目的

MS18-B3の目的は、MS18-B4で実施する安全なリファクタリング範囲を、挙動非変更・処理効率化・重複コード整理・セキュリティ上必要な最小修正に限定して定義することである。

具体的には、以下を明確化する。

- MS18-B2で見つかった P1 / P2 / P3 の扱い
- MS18-B4で修正してよい項目
- MS18-B4で修正してはいけない項目
- 変更してよいファイル
- 変更してはいけないファイル / 領域
- 挙動非変更とみなせる変更の範囲
- セキュリティ修正として許可する範囲
- 処理効率化として許可する範囲
- 重複コード整理として許可する範囲
- MS18-B4で実行すべきテスト
- MS18-B4では扱わず、MS18-B5 / B6 / B7 または MS19以降へ送る項目

## 4. In Scope

MS18-B3では、以下を対象とする。

### 4.1 MS18-B2結果の整理

- Security Preflight Review の確認結果を読む
- P1 / P2 / P3 の分類を確認する
- 各リスクの対象ファイルを確認する
- 各リスクの根拠を確認する
- 各リスクを MS18-B4で扱うか、別Blockへ送るかを分類する

### 4.2 MS18-B4で実装してよい範囲の定義

- 重複コード整理
- 明確な非効率処理の改善
- 例外処理の整理
- エラー分類の整理
- subprocess / ffmpeg / ffprobe 実行まわりの安全性改善
- temp / cache / 出力ファイル処理の安全化
- パス処理の小規模整理
- テストしやすさを高めるための小規模な責務分離
- セキュリティ上必要な最小修正
- docs と実装状態の同期方針整理

### 4.3 MS18-B4で実装してはいけない範囲の定義

- pipeline の意味論変更
- VMD writer の再設計
- GUI 状態遷移の大幅変更
- Preview / waveform の仕様変更
- 音声解析アルゴリズムの品質変更
- 設定 schema の大幅変更
- ディレクトリ構造の大規模再編
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- 英語対応
- installer 導入
- 配布方式の全面変更

### 4.4 変更対象ファイル候補の分類

MS18-B4で変更してよい候補ファイル、原則変更しないファイル、変更禁止ファイルを分類する。

### 4.5 テスト方針の定義

- MS18-B4で必ず実行すべき限定テストを定義する
- 変更範囲別のテスト候補を整理する
- GUI / wx 関連テストの既知不安定性の扱いを定義する
- 実行したテストと未実行テストの報告形式を定義する

### 4.6 引き継ぎ方針の整理

- MS18-B4へ渡す実装修正候補
- MS18-B5へ渡す SmokeLaunch 関連候補
- MS18-B6へ渡す packaging / license 関連候補
- MS18-B7へ渡す実MMD確認関連候補
- MS19以降へ送る機能追加候補

## 5. Out of Scope

MS18-B3では、以下を行わない。

- コード変更
- ドキュメント変更
- テスト修正
- テスト追加
- リファクタリング実装
- セキュリティ修正実装
- packaging 実作業
- GitHub Release 作成
- 実MMD確認
- `build.ps1` 修正
- FFmpeg build の変更
- 依存関係更新
- ライセンス解釈の法的断定
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- 英語対応
- VMD writer 再設計
- pipeline の意味論変更
- Preview / waveform の仕様変更
- GUI レイアウト刷新
- installer 導入
- CI/CD workflow の大規模追加

## 6. 前提条件

MS18-B3を開始する前提は以下とする。

- MS18-B1が完了している
- MS18-B2が完了している
- `main / origin/main` を正本として確認済みである
- `feature/MS17` を正本として扱わない方針が確認済みである
- MS17-B9 closeout が main に反映済みである
- `cache/` が Git 追跡対象外である
- MS18-B2で Security Preflight Review の結果が P1 / P2 / P3 に分類されている
- MS18-B3では実装変更を行わない
- MS18-B3では、MS18-B4の実装範囲定義のみを行う
- MS18-B4では、MS18-B3で定義した範囲以外の変更を行わない

## 7. 対象ファイル

MS18-B3では、以下を主な確認対象とする。

```text
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-B1_Implementation_Plan.md
docs/Implementation_Plan/MS18-B2_Implementation_Plan.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Release_Package_Manifest.md
```

MS18-B4で変更候補となり得るファイルを確認するため、必要に応じて以下も読む。

```text
src/core/audio_input.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/audio_errors.py
src/core/ffmpeg_locator.py
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
src/core/mmd_wav_export.py
src/gui_wx/app_controller.py
src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py
src/gui_wx/ui_state.py
src/gui_wx/main_frame.py
src/main.py
build.ps1
MMD_AutoLipTool.spec
requirements.txt
pyproject.toml
.gitignore
README.md
readme_mmdautolip.txt
NOTICE
THIRD_PARTY_LICENSES.md
```

必要に応じて、以下の tests も確認対象に含める。

```text
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b4_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py
tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b5_audio_cache.py
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_late_worker_result_discard.py
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_busy_action_states.py
tests/test_wx_ms14_b3_input.py
tests/test_wx_ms15_b1_waveform.py
tests/test_wx_ms16_b6_event_selection_foundation.py
```

ただし、MS18-B3ではテスト修正・テスト追加は行わない。

## 8. 実装方針

MS18-B3では、実装変更を行わない。

作業方針は以下とする。

1. Git 状態を確認する
2. MS18-B2の完了結果を確認する
3. P1 / P2 / P3 の分類結果を整理する
4. 各項目を MS18-B4で扱うかどうか判定する
5. MS18-B4で変更してよいファイル候補を定義する
6. MS18-B4で変更してはいけない範囲を定義する
7. 挙動非変更とみなせる変更を定義する
8. セキュリティ修正として許可する範囲を定義する
9. 処理効率化として許可する範囲を定義する
10. 重複コード整理として許可する範囲を定義する
11. MS18-B4で実行すべきテスト方針を定義する
12. MS18-B5 / B6 / B7 / MS19以降へ送るものを分類する
13. 実装変更を行っていないことを確認する

## 9. 詳細ステップ

### 9.1 Step 1: 作業開始前の Git 状態確認

以下を実行する。

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
```

確認すること。

- 現在の作業ブランチ
- `main / origin/main` の同期状態
- working tree の未コミット差分
- staged 差分
- 想定外の変更がないこと
- MS18-B1 / B2 関連文書が存在すること

### 9.2 Step 2: MS18-B2 Completion Report の確認

確認対象。

```text
docs/Implementation_Plan/MS18-B2_Implementation_Plan.md
MS18-B2 Completion Report
```

確認すること。

- MS18-B2で確認したファイル
- MS18-B2で確認した観点
- P1 / P2 / P3 の分類
- MS18-B3へ引き継がれた項目
- MS18-B4へ引き継がれた項目
- MS18-B5 / B6 / B7へ引き継がれた項目
- 実装変更が行われていないこと

MS18-B2 Completion Report がまだ repo 内に文書化されていない場合は、ユーザー提供の報告内容または直前セッションの結果を参照し、参照元を明記する。

### 9.3 Step 3: P1 / P2 / P3 の扱い定義

MS18-B2で分類された項目を、以下の方針で扱う。

```text
P1:
  リリース前に必ず修正すべき重大問題。
  原則として MS18-B4 の実装修正対象にする。
  ただし、SmokeLaunch / package / 実MMD確認など別Blockが適切なものは、
  MS18-B5 / B6 / B7へ送る。

P2:
  MS18内で修正または扱いを確定すべき問題。
  修正対象・保留対象・別Block対象に分類する。
  挙動非変更の範囲で修正できるものは MS18-B4 候補にする。

P3:
  記録・表現・将来改善でよい問題。
  MS18-B4での実装修正対象には原則含めない。
  docs同期、MS18-B6、MS19以降、または将来課題へ送る。
```

判定時には、以下を記録する。

```text
- 項目ID
- 重大度
- 対象ファイル
- 現象または懸念
- 根拠
- MS18-B4で扱うか
- 別Blockへ送るか
- MS18で扱わないか
- 理由
```

### 9.4 Step 4: MS18-B4対象候補の分類

MS18-B4で扱える候補を、以下に分類する。

```text
A. Security Minimal Fix
  セキュリティ上必要な最小修正。
  例:
  - subprocess 引数処理の明確化
  - cleanup 漏れ修正
  - 意図しない上書き防止
  - 不完全ファイルの扱い修正

B. Safety / Robustness Fix
  利用中の破損・固着・復旧不能を防ぐ修正。
  例:
  - worker終了時の状態復帰
  - cancel時の後始末
  - Busy解除漏れ防止
  - エラー分類の明確化

C. Duplicate Code Cleanup
  同じ処理・同じ判定・同じエラー変換が複数箇所にある場合の整理。
  例:
  - ffmpeg / ffprobe エラー変換の重複整理
  - temp file cleanup の共通化
  - パス検証ロジックの小規模共通化

D. Efficiency Improvement
  明確に無駄な処理を減らす改善。
  例:
  - 同じ ffprobe 情報の不要な再取得回避
  - 同じ状態更新の重複呼び出し削減
  - 不要なファイル存在確認の整理

E. Testability Improvement
  挙動を変えずにテストしやすくする小規模責務分離。
  例:
  - 純粋関数化できる判定の切り出し
  - runner 引数生成部分の小規模分離
  - 状態判定ヘルパーの整理
```

### 9.5 Step 5: MS18-B4で扱わない候補の分類

以下に該当するものは、MS18-B4で扱わない。

```text
A. SmokeLaunch専用調査
  MS18-B5へ送る。

B. Packaging / License Preflight
  MS18-B6へ送る。

C. Actual MMD Manual Verification
  MS18-B7へ送る。

D. 新機能
  MS19以降へ送る。

E. 大規模設計変更
  MS18では扱わず、別マイルストーン候補として記録する。

F. 法的判断
  MS18-B6で確認項目として扱うが、法的断定はしない。
```

### 9.6 Step 6: 変更許可ファイル候補の定義

MS18-B4で変更してよい候補ファイルは、MS18-B2 / B3 の結果に基づいて限定する。

初期候補は以下。

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
src/gui_wx/worker_state.py
src/gui_wx/ui_state.py
tests/
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Version_Control.md
docs/repo_milestone.md
```

ただし、上記は候補であり、MS18-B4で実際に変更してよいファイルは、B3完了報告で明示したものに限定する。

### 9.7 Step 7: 原則変更しないファイルの定義

以下は、MS18-B4では原則変更しない。

```text
README.md
readme_mmdautolip.txt
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
MMD_AutoLipTool.spec
build.ps1
pyproject.toml
requirements.txt
```

例外は以下の場合に限る。

```text
- MS18-B2 / B3でP1またはP2として明確に分類された場合
- release readiness 上、文書同期が必要な場合
- MS18-B5 / B6 の対象として別Blockで扱う場合
```

`build.ps1` は SmokeLaunch 調査に関係するため、MS18-B4では原則変更せず、MS18-B5で扱う。

`NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md` は、packaging / license preflight に関係するため、MS18-B4では原則変更せず、MS18-B6で扱う。

### 9.8 Step 8: 変更禁止範囲の定義

MS18-B4では、以下を変更禁止とする。

```text
- VMD writer の出力意味論
- VMD ファイル構造
- リップモーフ `あ / い / う / え / お` の基本仕様
- timing pipeline の意味論
- Preview shape の意味論
- waveform 表示仕様
- GUI レイアウト構成
- TEXTあり入力の既存導線
- wav / mp3 / m4a 入力対応の仕様
- MMD用WAV出力仕様
  - pcm_s16le
  - 44100 Hz
  - stereo
  - 専用ボタンから出力
- 解析用WAV仕様
- cache の基本方針
- settings schema の大幅変更
- PyInstaller onefile 方針
- FFmpeg build の入れ替え
```

### 9.9 Step 9: 挙動非変更の定義

MS18-B4における「挙動非変更」とは、以下を満たすことをいう。

```text
- ユーザー操作手順が変わらない
- 入力可能ファイル形式が変わらない
- 生成される VMD の意味論が変わらない
- MMD用WAV の仕様が変わらない
- 解析用WAV の仕様が変わらない
- Preview / waveform の見え方を意図的に変えない
- GUI レイアウトを変えない
- 保存先・上書き確認・エラー通知の基本動作を変えない
- 既存テストの期待値を不用意に変えない
- README に記載されたユーザー向け機能範囲を変えない
```

次の変更は、条件付きで挙動非変更とみなせる。

```text
- 内部 helper 関数の切り出し
- 重複した cleanup 処理の共通化
- 同じエラー分類を返す内部処理の整理
- 同じ subprocess 引数を生成する処理の整理
- エラー時に破損ファイルを残しにくくする修正
- Busy解除漏れを防ぐ修正
- ユーザーに見えるメッセージの意味を変えない文言整理
```

次の変更は、挙動変更として扱う。

```text
- VMD出力値が変わる
- MMD用WAVの形式が変わる
- 解析用WAVの形式が変わる
- 入力制限値が変わる
- ファイルダイアログの対象拡張子が変わる
- GUIボタンの有効 / 無効条件が変わる
- エラー時に既存状態を破棄する条件が変わる
- 保存先や初期ファイル名の仕様が変わる
- cache命名規則が変わる
```

挙動変更が必要に見える場合は、MS18-B4に含めず、別途ユーザー確認を必要とする。

### 9.10 Step 10: セキュリティ修正として許可する範囲

MS18-B4で許可するセキュリティ修正は、以下に限定する。

```text
- shell injection 相当リスクを避けるための subprocess 引数整理
- ユーザー指定パスの扱い明確化
- 意図しない上書き防止
- 失敗時 cleanup の補強
- 不完全ファイルを正常成果物として扱わない修正
- ffmpeg / ffprobe 未検出時の安全な失敗
- cancel / terminate / kill 後の後始末改善
- late callback による古い結果反映の防止補強
- エラー表示の過剰な内部情報露出を抑える小修正
```

次は MS18-B4で扱わない。

```text
- サンドボックス化
- 暗号化機能追加
- ネットワーク制御
- 自動アップデート
- 自動ダウンロード
- 外部署名検証機能
- 依存関係の全面更新
- FFmpeg build の変更
```

### 9.11 Step 11: 処理効率化として許可する範囲

MS18-B4で許可する処理効率化は、以下に限定する。

```text
- 同じ情報の重複取得を減らす
- 明確に不要なファイル存在確認を整理する
- 同じGUI状態更新の重複呼び出しを減らす
- 同じエラー変換処理の重複を減らす
- 明確に不要な一時ファイル生成を避ける
- 同じパス解決処理の重複を整理する
```

次は MS18-B4で扱わない。

```text
- Whisper処理の高速化
- 音声解析アルゴリズム変更
- 並列処理方式の大幅変更
- worker設計の全面変更
- cache policy の根本変更
- GUI描画最適化の大規模改修
```

### 9.12 Step 12: 重複コード整理として許可する範囲

MS18-B4で許可する重複コード整理は、以下に限定する。

```text
- ffmpeg / ffprobe runner の共通処理整理
- temp file cleanup の共通化
- path validation の小規模共通化
- error mapping の重複整理
- GUI状態更新 helper の重複整理
- Busy状態判定 helper の重複整理
- テスト内の小規模 helper 整理
```

次は MS18-B4で扱わない。

```text
- src全体のディレクトリ再編
- controller層の全面分割
- core / gui の責務再設計
- VMD writer 周辺の統合整理
- settings schema 再設計
- イベントデータ構造の再設計
```

### 9.13 Step 13: MS18-B4用テスト方針の定義

MS18-B4では、変更範囲に応じて限定テストを実行する。

#### ffmpeg / ffprobe / audio_convert 周辺を変更した場合

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
```

#### cache 周辺を変更した場合

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
```

#### MMD用WAV出力周辺を変更した場合

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

#### worker / Busy / late callback 周辺を変更した場合

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

#### GUI入力導線を変更した場合

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
```

#### waveform / Preview との接続に触れた場合

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

全体テストを実行する場合は、既知の wx teardown 由来の終了コード不安定性があるため、表示上の pass 数と終了コードを分けて記録する。

### 9.14 Step 14: MS18-B5 / B6 / B7へ送る項目の定義

MS18-B3では、MS18-B4で扱わない項目を次のように送る。

```text
MS18-B5へ送る:
  - build.ps1 -SmokeLaunch の PyInstaller プロセス残留
  - build.ps1 の SmokeLaunch 処理
  - 生成済み exe の起動スモーク確認
  - Stop-Process 後の残留確認

MS18-B6へ送る:
  - FFmpeg license notice
  - --enable-gpl --enable-version3
  - THIRD_PARTY_LICENSES.md
  - NOTICE
  - Release_Package_Manifest
  - 実行用ZIP同梱物 / 除外物
  - sample/ 同梱方針

MS18-B7へ送る:
  - 実MMDでの VMD 読み込み確認
  - 実MMDでの MMD用WAV 読み込み確認
  - 音声再生確認
  - リップ同期目視確認
```

### 9.15 Step 15: MS19以降へ送る項目の定義

以下は MS18では扱わず、MS19以降へ送る。

```text
MS19へ送る:
  - 音声のみ入力対応
  - 書き起こし結果の扱い
  - TEXTなし pipeline
  - 日本語読み生成拡張

MS20へ送る:
  - 発音イベント単位のリップモーフ編集
  - あ / い / う / え / お 範囲内の開口量・閉口・スロープ調整
  - Preview / VMD writer への編集反映

MS21以降へ送る:
  - 同音母音連続時の谷スムージング
  - 英語対応
  - installer導入
  - cache管理UI
  - 汎用的な配布方式改善
```

### 9.16 Step 16: MS18-B4実装範囲表の作成

MS18-B3の成果として、次の形式で MS18-B4 実装範囲表を作成する。

```md
## MS18-B4 Implementation Scope Table

| ID | Source | Severity | Category | Target File(s) | Allowed in B4 | Reason | Required Tests |
|---|---|---|---|---|---|---|---|
| B3-SCOPE-001 | MS18-B2 | P2 | Duplicate Code Cleanup | `src/core/...` | Yes | ... | ... |
| B3-SCOPE-002 | MS18-B2 | P3 | Docs Note | `README.md` | No | Send to B6 | ... |
```

分類項目は以下とする。

```text
Source:
  - MS18-B2
  - repo review
  - docs consistency
  - testability

Severity:
  - P1
  - P2
  - P3

Category:
  - Security Minimal Fix
  - Safety / Robustness Fix
  - Duplicate Code Cleanup
  - Efficiency Improvement
  - Testability Improvement
  - Docs Sync
  - Send to B5
  - Send to B6
  - Send to B7
  - Future

Allowed in B4:
  - Yes
  - No
  - Conditional
```

### 9.17 Step 17: 実装変更がないことの確認

作業終了時に以下を実行する。

```powershell
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

- MS18-B3作業によりコード差分が発生していないこと
- docs差分が発生していないこと
- staged差分が発生していないこと

差分が存在する場合は、MS18-B3の範囲違反として報告する。  
ただし、ユーザーが明示的に文書作成を同時依頼した場合のみ、対象文書差分を別扱いで報告する。

## 10. 状態遷移 / データ契約

MS18-B3では、アプリケーションの実装上の状態遷移やデータ契約は変更しない。

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
- PyInstaller build仕様
- release package仕様

MS18-B3で定義するのは、MS18-B4で変更してよい範囲である。  
仕様変更が必要に見える場合でも、MS18-B3では変更せず、MS18-B4対象外またはユーザー確認事項として記録する。

## 11. テスト方針

MS18-B3では、実装変更を行わないため、自動テスト実行は必須ではない。

ただし、MS18-B4のテスト方針を定義するために、既存テストの存在確認や collect-only は許可する。

```powershell
.\.venv\Scripts\python.exe -m pytest --version
.\.venv\Scripts\python.exe -m pytest --collect-only
```

MS18-B3でテストを実行した場合は、以下を報告する。

- 実行コマンド
- 結果
- 終了コード
- pass / fail / error
- 未実行テスト
- 未実行理由

MS18-B3では、以下は行わない。

- テスト修正
- テスト追加
- 全体 pytest を完了条件にすること
- wx teardown 由来の既知不安定性の詳細調査

## 12. 受け入れ条件

MS18-B3の完了条件は以下。

- `main / origin/main` を正本として確認している
- 実装変更が行われていない
- docs変更が行われていない
- MS18-B2の P1 / P2 / P3 結果を確認している
- MS18-B4で扱う項目が定義されている
- MS18-B4で扱わない項目が定義されている
- MS18-B4で変更してよいファイル候補が明記されている
- MS18-B4で変更してはいけない範囲が明記されている
- 挙動非変更の定義が明記されている
- セキュリティ修正として許可する範囲が明記されている
- 処理効率化として許可する範囲が明記されている
- 重複コード整理として許可する範囲が明記されている
- MS18-B4で実行すべきテスト方針が明記されている
- MS18-B5 / B6 / B7へ送る項目が整理されている
- MS19以降へ送る項目が整理されている
- MS18-B4へ進める状態になっている

## 13. リスクと対策

### 13.1 リファクタリング範囲が広がる

#### リスク

「全体リファクタリング」という言葉に引っ張られ、MS18-B4で大規模再設計が始まる。

#### 対策

MS18-B3で変更可能範囲を明示する。  
MS18-B4では、B3で許可された項目以外を変更しない。

### 13.2 挙動非変更の定義が曖昧になる

#### リスク

内部整理のつもりで、VMD出力、MMD用WAV仕様、GUI状態、Preview表示などが変わる。

#### 対策

MS18-B3で挙動非変更の定義を明記する。  
出力仕様・入力仕様・GUI操作仕様が変わる場合は、B4対象外にする。

### 13.3 P1 / P2 をすべて B4 に詰め込む

#### リスク

Security Preflight で見つかった項目をすべて B4 に入れ、B4が肥大化する。

#### 対策

項目ごとに B4 / B5 / B6 / B7 / Future へ振り分ける。  
SmokeLaunch は B5、license / package は B6、実MMD確認は B7へ送る。

### 13.4 ドキュメント変更が混入する

#### リスク

MS18-B3はスコープ定義Blockだが、作業中に docs を更新してしまう。

#### 対策

MS18-B3では実装変更・docs変更を行わない。  
文書化が必要な内容は、完了報告として記録し、MS18-B4以降の対象にする。

### 13.5 テスト方針が過剰または不足する

#### リスク

全体 pytest に依存しすぎる、または限定テストが不足する。

#### 対策

変更範囲別に限定テストを定義する。  
wx teardown 由来の既知不安定性は、表示上の pass 数と終了コードを分けて扱う。

## 14. AI agent 作業時の注意

MS18-B3をAI agentに依頼する場合は、以下を明示する。

```text
今回は MS18-B3: Refactor Scope Definition の作業です。

このBlockでは、実装変更を行わないでください。
コード変更、ドキュメント変更、リファクタリング実装、テスト修正、新機能追加は禁止です。

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

確認対象は以下です。

docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-B1_Implementation_Plan.md
docs/Implementation_Plan/MS18-B2_Implementation_Plan.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Release_Package_Manifest.md

必要に応じて以下も確認してください。

src/core/audio_input.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/audio_errors.py
src/core/ffmpeg_locator.py
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
src/core/mmd_wav_export.py
src/gui_wx/app_controller.py
src/gui_wx/audio_worker.py
src/gui_wx/ui_state.py
src/gui_wx/main_frame.py
src/main.py
build.ps1
MMD_AutoLipTool.spec
requirements.txt
pyproject.toml
.gitignore
README.md
readme_mmdautolip.txt
NOTICE
THIRD_PARTY_LICENSES.md

以下を確認してください。

1. MS18-B2のP1/P2/P3分類
2. MS18-B4で扱うべき項目
3. MS18-B4で扱わない項目
4. MS18-B4で変更してよいファイル候補
5. MS18-B4で変更してはいけない範囲
6. 挙動非変更の定義
7. セキュリティ修正として許可する範囲
8. 処理効率化として許可する範囲
9. 重複コード整理として許可する範囲
10. MS18-B4で実行すべきテスト
11. MS18-B5 / B6 / B7へ送る項目
12. MS19以降へ送る項目

完了報告では、以下を必ず記載してください。

1. 現在ブランチ
2. local main / origin/main の同期状態
3. working tree / staged 差分の有無
4. 確認したファイル
5. MS18-B2結果の要約
6. MS18-B4対象項目
7. MS18-B4対象外項目
8. MS18-B4変更許可ファイル
9. MS18-B4変更禁止範囲
10. MS18-B4テスト方針
11. MS18-B5 / B6 / B7への引き継ぎ
12. MS19以降への引き継ぎ
13. 実装変更を行っていないこと
```

## 15. MS18-B3 Completion Report

# MS18-B3 Completion Report

## 1. Git状態

- Current branch: `feature/MS18`
- Latest local commit: `51ecfe2 Document sandbox command constraints`
- Latest `main` commit: `1099a79a683aa87a98902a0dd653d9a4681560b4`
- Latest `origin/main` commit: `1099a79a683aa87a98902a0dd653d9a4681560b4`
- local `main` / `origin/main`: 同一コミットで同期済み
- Working tree: MS18-B1 / B2 文書反映、`.gitignore` の既存差分に加え、MS18-B3文書更新を追加
- Staged diff: なし

## 2. 実行コマンド

```powershell
git status --short --branch
git branch
git log --oneline -n 10
git fetch origin
git rev-parse main
git rev-parse origin/main
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
rg -n "MS18-B3|Refactor Scope Definition|B3-SCOPE|MS18-B4 Implementation Scope Table|MS18-B3 closeout" docs\MS17_and_Beyond_Index.md docs\MS18_and_Beyond_Roadmap.md docs\Implementation_Plan\MS18_Block_Breakdown.md docs\Implementation_Plan\MS18-B3_Implementation_Plan.md docs\repo_milestone.md docs\Version_Control.md
```

## 3. 確認ファイル

- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS18_Block_Breakdown.md`
- `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS18-B2_Implementation_Plan.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
- `docs/Error_Handling_Specification.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Release_Package_Manifest.md`

## 4. MS18-B2結果の要約

### P1

- なし。

### P2

- FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定が未完了。MS18-B6へ送る。
- `build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因未確定。MS18-B5へ送る。
- 実MMDでのVMD / MMD用WAV読み込み・再生確認が未完了。MS18-B7へ送る。

### P3

- PATH fallback時に、ユーザーが実際にどのffmpeg/ffprobeを使っているかを把握しやすくする説明改善余地がある。
- `error.log` / 開発コンソールにはローカルパスやtracebackが出る可能性がある。
- cacheファイル名には元音声のstemが残るため、Git/release除外を維持する。
- `build.ps1 -Clean` は旧 `dist\MMD_AutoLipTool.exe` を明示削除しない。
- `.codex/config.toml` を `.gitignore` に追加する既存差分がある。

## 5. MS18-B4 Implementation Scope Table

| ID | Source | Severity | Category | Target File(s) | Allowed in B4 | Reason | Required Tests |
|---|---|---|---|---|---|---|---|
| B3-SCOPE-001 | MS18-B2 | P3 | Safety / Robustness Fix | `src/core/ffmpeg_locator.py`, `tests/test_ms17_b3_ffmpeg_locator.py` | Conditional | FFmpeg / ffprobe探索元を把握しやすくする小規模整理は許可。ただし探索順、PATH fallback可否、自動ダウンロード禁止方針は変更しない。 | `tests/test_ms17_b3_ffmpeg_locator.py` |
| B3-SCOPE-002 | MS18-B2 | P3 | Docs Sync / Diagnostics | `src/main.py`, `src/gui_wx/app_controller.py`, `docs/Error_Handling_Specification.md` | Conditional | `error.log` / 開発コンソールの扱いを整理する場合のみ許可。ユーザー向けダイアログの意味、error.log生成方針、復旧情報は変えない。 | 変更箇所に応じた限定テスト。GUI通知に触れる場合は `tests/test_wx_ms14_b3_input.py` |
| B3-SCOPE-003 | MS18-B2 | P3 | Send to B6 | `docs/Release_Package_Manifest.md`, `README.md`, `readme_mmdautolip.txt` | No | cacheファイル名に元音声stemが残る件は、現状Git/release除外済み。B4でcache命名規則は変更しない。必要ならB6の配布前確認で文書確認する。 | なし |
| B3-SCOPE-004 | MS18-B2 | P3 | Send to B5 | `build.ps1` | No | `build.ps1 -Clean` と旧onefile成果物の扱いはSmokeLaunch / build手順調査に近いためB5へ送る。B4では `build.ps1` を変更しない。 | なし |
| B3-SCOPE-005 | MS18-B2 | P3 | Out of Product Scope | `.gitignore`, `.codex/config.toml` | No | `.codex/config.toml` ignoreはローカルCodex設定の既存差分であり、製品挙動・MS18-B4実装対象ではない。 | なし |
| B3-SCOPE-006 | MS18-B2 | P2 | Send to B5/B6/B7 | `build.ps1`, `NOTICE`, `THIRD_PARTY_LICENSES.md`, `docs/Release_Package_Manifest.md`, 実MMD確認記録 | No | B2のP2はそれぞれ専用Blockで扱う。B4へ混ぜない。 | B5/B6/B7で定義 |

## 6. MS18-B4で扱う項目

- 必須のP1/P2修正はない。
- B4で扱ってよいのは、B3-SCOPE-001 または B3-SCOPE-002 のうち、挙動非変更で小規模に完了できるものに限定する。
- B4で実装する場合でも、FFmpeg / ffprobe探索順、PATH fallback仕様、自動ダウンロード禁止、エラー分類、GUI状態遷移、MMD用WAV仕様は変更しない。

## 7. MS18-B4で扱わない項目

- `build.ps1 -SmokeLaunch` / process residual調査。MS18-B5へ送る。
- FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定。MS18-B6へ送る。
- 実MMDでのVMD / MMD用WAV確認。MS18-B7へ送る。
- cache命名規則変更、cache管理UI、cache policyの根本変更。
- `build.ps1 -Clean` の旧onefile成果物明示削除。B5へ送る。
- `.codex/config.toml` ignore差分をB4製品実装として扱うこと。
- pipeline意味論、VMD writer、Preview / waveform、GUIレイアウト、settings schema、音声のみ入力、モーフ編集。

## 8. MS18-B4変更許可ファイル

- `src/core/ffmpeg_locator.py`
- `src/main.py`
- `src/gui_wx/app_controller.py`
- `tests/test_ms17_b3_ffmpeg_locator.py`
- `tests/test_wx_ms14_b3_input.py`
- `docs/Error_Handling_Specification.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

上記は許可候補であり、B4実装時に実際に触るファイルは、B4開始時の実装計画でさらに絞る。

## 9. MS18-B4変更禁止範囲

- VMD writerの出力意味論、VMDファイル構造、リップモーフ `あ / い / う / え / お` の基本仕様。
- timing pipelineの意味論、Preview shapeの意味論、waveform表示仕様。
- GUIレイアウト構成、TEXTあり入力導線、wav / mp3 / m4a入力仕様。
- MMD用WAV出力仕様 (`pcm_s16le`, 44100 Hz, stereo, 専用ボタン、上書き確認)。
- 解析用WAV仕様、cache基本方針、cache命名規則。
- settings schemaの大幅変更、PyInstaller onefile方針、FFmpeg build入れ替え。
- `build.ps1`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md` はB4では原則変更しない。

## 10. 挙動非変更の定義確認

- ユーザー操作手順、入力可能形式、生成VMD意味論、MMD用WAV仕様、解析用WAV仕様が変わらないこと。
- Preview / waveformの見え方、GUIレイアウト、保存先・上書き確認、エラー通知の基本動作が変わらないこと。
- 既存テストの期待値を不用意に変更しないこと。
- 内部helper追加、探索結果の説明補助、診断ログ扱いの整理は、既存挙動を変えない場合のみ許可する。

## 11. MS18-B4テスト方針

### Required Tests

- B4でコード変更を行った場合は、変更ファイルに対応する限定テストを必ず実行する。
- B4でコード変更を行わない場合は、`git diff --check` と差分確認を必須とする。

### Conditional Tests

- `src/core/ffmpeg_locator.py` を変更した場合:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py`
- `src/main.py` または `src/gui_wx/app_controller.py` の診断/通知導線を変更した場合:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py`
- ffmpeg / ffprobe runner、audio_convert、cache、MMD用WAV、worker / Busyに触れた場合:
  - B3計画書 9.13 の該当限定テストを追加実行する。

### Not Required / Reason

- 全体pytestはB4の必須条件にしない。wx teardown由来の既知不安定性があるため、必要時のみ表示上のpass数と終了コードを分けて記録する。
- B4でdocsのみ更新する場合、アプリ挙動テストは必須にしない。

## 12. MS18-B5 / B6 / B7への引き継ぎ

### MS18-B5 SmokeLaunch / Process Residual Investigation

- `build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因調査。
- `build.ps1 -Clean` が旧 `dist\MMD_AutoLipTool.exe` を明示削除しない件の扱い確認。

### MS18-B6 Release / Packaging / License Preflight

- FFmpeg / ffprobe `N-123549-g70537ec8e6-20260318`、`--enable-gpl --enable-version3` 構成に対するlicense texts / notice最終確定。
- cacheファイル名に元音声stemが残る件について、Git/release除外方針が配布文書と矛盾しないか確認。
- `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` / `readme_mmdautolip.txt` / `Release_Package_Manifest` の最終同期。

### MS18-B7 Actual MMD Manual Verification Closeout

- 実MMD上での生成VMD読み込み確認。
- 実MMD上でのMMD用WAV読み込み・再生確認。
- リップモーフと音声同期の目視確認。

## 13. MS19以降への引き継ぎ

- 音声のみ入力対応。
- 発音イベント単位のリップモーフ編集。
- cache管理UI。
- 英語対応、installer導入、配布方式改善。

## 14. 変更有無

- Code changes: なし。
- Docs changes: あり。ユーザー指示により、MS18-B3完了結果を本計画書と関連ドキュメントへ反映。
- Other changes: なし。

## 15. 判定

- MS18-B3 closeout: OK。B4実装範囲は限定済み。
- 次に進むBlock: `MS18-B4: Safe Refactor Implementation`

## 16. 次作業

MS18-B3完了後は、確認結果に基づいて MS18-B4 へ進む。

次作業は以下とする。

```text
MS18-B4: Safe Refactor Implementation
```

MS18-B4では、MS18-B3で定義した範囲に限定して、挙動非変更の安全なリファクタリングを実施する。

MS18-B4では、次を厳守する。

```text
- MS18-B3で許可された項目のみ実装する
- 新機能を追加しない
- 音声のみ入力対応を先行実装しない
- モーフ編集機能を先行実装しない
- pipeline の意味論を変更しない
- VMD writer を再設計しない
- GUI レイアウトを刷新しない
- 変更範囲に応じた限定テストを実行する
- 実行したテストと未実行テストを分けて報告する
```
