# MS18-B2 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B2 Implementation Plan
- 想定配置先: `docs/Implementation_Plan/MS18-B2_Implementation_Plan.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 対象マイルストーン: MS18
- 対象Block: MS18-B2
- Block名: Security Preflight Review
- 基準ブランチ: `main`
- 正本:
  - `main / origin/main`
- 非正本:
  - `feature/MS17`
- 関連文書:
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/Release_Package_Manifest.md`
  - `README.md`
  - `NOTICE`
  - `THIRD_PARTY_LICENSES.md`
- 作成日: 2026-06-03
- 文書ステータス: Completed
- 作業種別:
  - security preflight
  - release readiness check
  - 実装前リスク分類
- 実装変更:
  - なし

## 2. 背景

MS17では、wav / mp3 / m4a 入力、ffprobe による音声検査、ffmpeg による解析用WAV生成、MMD用WAV出力、音声処理 worker 化、Busy制御、キャンセル導線、MS17-B9 closeout まで完了した。

MS17 closeout 後の追補として、`cache/` は Git 追跡対象外となり、`cache/analysis_wav/` 配下の解析用WAVは Git 管理から外された。

MS18では、リリース / package 化へ進む前に、リリース前安定化、処理効率化、重複コード整理、セキュリティ確認、SmokeLaunch残留調査、FFmpeg同梱配布時のライセンス通知確認、実MMD確認を行う。

MS18-B1では、repo状態、MS17 closeout反映、cache追跡対象外化、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の同期、MS18で扱うリスクの棚卸しを行う。

MS18-B2では、その次段として、MMD_AutoLipTool 固有のセキュリティ観点を確認する。

このBlockでは、原則として実装変更を行わない。  
問題が見つかった場合は、P1 / P2 / P3 に分類し、MS18-B3 Refactor Scope Definition および MS18-B4 Safe Refactor Implementation へ引き継ぐ。

## 3. 目的

MS18-B2の目的は、リリース / package 化前に、MMD_AutoLipTool 固有のセキュリティ上・安全運用上のリスクを確認し、修正要否を分類することである。

一般的な抽象セキュリティ論ではなく、次の実装実態に即して確認する。

- Windows 11 向けローカルGUIアプリ
- ユーザー指定の TEXT / 音声ファイル読み込み
- wav / mp3 / m4a 入力
- ffprobe / ffmpeg の外部プロセス実行
- 解析用WAVの cache 生成
- MMD用WAVのユーザー指定パス保存
- PyInstaller onefile 配布
- FFmpeg / ffprobe 同梱
- GitHub Release 向け実行用ZIP配布
- MMDユーザーが扱う個人制作向けツール

MS18-B2では、確認したリスクを P1 / P2 / P3 に分類し、次Block以降で修正・保留・文書化すべき内容を明確にする。

## 4. In Scope

MS18-B2では、以下を対象とする。

### 4.1 外部ファイル入力

- TEXTファイル読み込み
- 音声ファイル読み込み
- wav / mp3 / m4a 入力
- ファイルサイズ上限
- 音声長さ上限
- 拡張子判定
- ffprobe による実体確認
- 壊れた音声ファイルへのエラー処理
- 音声ストリームなしファイルへのエラー処理
- ユーザー指定パスの扱い

### 4.2 ffprobe / ffmpeg 実行経路

- `ffprobe` 実行箇所
- `ffmpeg` 実行箇所
- subprocess 実行方法
- `shell=True` 相当の危険がないこと
- 引数が list 形式で渡されていること
- ユーザー入力値が shell 文字列連結されていないこと
- timeout / cancel / terminate / kill の扱い
- stderr / stdout の扱い
- エラー時の例外分類
- 実行バイナリ探索順

### 4.3 FFmpeg / ffprobe 探索と同梱

- `FFmpeg\bin\ffmpeg.exe`
- `FFmpeg\bin\ffprobe.exe`
- アプリ実行パス下の `FFmpeg\bin\` 優先探索
- `PATH` fallback
- 未検出時のユーザー通知
- 自動ダウンロードを行っていないこと
- PyInstaller onefile 実行時の展開先探索
- 同梱バイナリのライセンス通知との関係

### 4.4 temp / cache / 出力ファイル処理

- `cache/analysis_wav/` の生成
- 解析用WAVの命名
- 入力ファイルパスハッシュの扱い
- 一時ファイル生成
- 成功時のファイル移動
- 失敗時 cleanup
- 不完全ファイル削除
- 上書き確認
- ユーザー指定パスへの MMD用WAV 保存
- 既存ファイル上書き時の確認
- `cache/` が Git / release package に混入しないこと

### 4.5 GUI / worker / Busy 状態

- 音声処理中の二重実行防止
- worker中キャンセル導線
- late callback 破棄
- アプリ終了時の worker 結果破棄
- Busy 状態中の操作制限
- 例外時にGUI状態が戻ること
- エラー表示が過度に技術的すぎないこと
- ユーザーが復旧しやすいこと

### 4.6 エラーメッセージ / ログ / 情報露出

- エラー表示に不要なローカルパスを出しすぎていないか
- 例外tracebackをユーザーにそのまま出していないか
- FFmpeg stderr の扱い
- 技術詳細とユーザー向け説明の分離
- 個人情報に該当し得るファイルパスの扱い
- docs / README の注意書き不足

### 4.7 PyInstaller / package / release 安全性

- `MMD_AutoLipTool.spec`
- `build.ps1`
- onefile bundling
- 同梱物
- 除外物
- `src/`、`tests/`、`docs/`、`.venv/`、`cache/`、`build/` の混入リスク
- `FFmpeg\bin\` の扱い
- `LICENSE`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`
- Release package manifest

### 4.8 依存関係・ライセンス面のセキュリティ隣接確認

MS18-B2では、法的判断は行わない。  
ただし、release readiness の安全確認として、以下を確認対象に含める。

- FFmpeg build configuration の記録
- `--enable-gpl --enable-version3` に関する注意
- 第三者ライセンス通知の未確定点
- 自動ダウンロード禁止方針
- 有償OSSや配布困難な依存の混入有無
- `requirements.txt` / `pyproject.toml` の依存確認

## 5. Out of Scope

MS18-B2では、以下を行わない。

- コード変更
- ドキュメント変更
- リファクタリング
- セキュリティ修正
- package 実作業
- GitHub Release 作成
- 実MMD確認
- `build.ps1` 修正
- FFmpeg build の変更
- 依存関係更新
- ライセンス解釈の法的断定
- 外部セキュリティ監査
- 暗号化機能追加
- sandbox 化
- ネットワーク通信機能追加
- 自動アップデート機能追加
- 自動ダウンロード機能追加
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- 英語対応
- VMD writer 再設計
- pipeline の意味論変更
- Preview / waveform の仕様変更
- GUI レイアウト刷新

## 6. 前提条件

MS18-B2を開始する前提は以下とする。

- MS18-B1が完了している
- `main / origin/main` を正本として確認済みである
- `feature/MS17` を正本として扱わない方針が確認済みである
- MS17-B9 closeout が main に反映済みである
- `cache/` が Git 追跡対象外である
- MS18のロードマップと Block Breakdown が作成済みである
- MS18-B2では実装変更を行わない
- 問題が見つかった場合は、このBlockでは修正せず P1 / P2 / P3 に分類する
- 修正候補は MS18-B3 / MS18-B4 へ引き継ぐ

## 7. 対象ファイル

MS18-B2では、以下を主な確認対象とする。

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
docs/Release_Package_Manifest.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-B1_Implementation_Plan.md
docs/repo_milestone.md
docs/Version_Control.md
```

必要に応じて、以下の tests も確認対象に含める。

```text
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_audio_cache.py
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_late_worker_result_discard.py
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_busy_action_states.py
tests/test_wx_ms14_b3_input.py
```

ただし、MS18-B2ではテスト修正・テスト追加は行わない。

## 8. 実装方針

MS18-B2では、実装変更を行わない。

作業方針は以下とする。

1. Git 状態を確認する
2. MS18-B1の完了結果を確認する
3. 外部ファイル入力の安全性を確認する
4. ffprobe / ffmpeg 実行経路を確認する
5. subprocess 実行方法を確認する
6. temp / cache / 出力ファイル処理を確認する
7. GUI / worker / Busy 状態の安全性を確認する
8. エラーメッセージ・ログ・情報露出を確認する
9. PyInstaller / release package の混入リスクを確認する
10. FFmpeg / ライセンス通知に関する release readiness 上のリスクを確認する
11. 確認結果を P1 / P2 / P3 に分類する
12. MS18-B3 / B4 / B5 / B6 / B7 への引き継ぎを整理する
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
- MS18-B1以降の差分有無
- working tree の未コミット差分
- staged 差分
- 想定外の変更がないこと

### 9.2 Step 2: MS18-B1結果の確認

確認対象。

```text
docs/Implementation_Plan/MS18-B1_Implementation_Plan.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/repo_milestone.md
docs/Version_Control.md
```

確認すること。

- MS18-B1で main / origin/main を正本として確認していること
- MS18-B2が Security Preflight Review として定義されていること
- MS18-B2では実装変更しないこと
- MS18-B2で見つかった問題は P1 / P2 / P3 に分類すること
- 修正候補は MS18-B3 / B4 へ引き継ぐこと

### 9.3 Step 3: 外部ファイル入力の確認

確認対象。

```text
src/core/audio_input.py
src/core/audio_probe.py
src/core/audio_errors.py
src/gui_wx/app_controller.py
src/gui_wx/main_frame.py
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
README.md
```

確認すること。

- TEXT 入力パスがユーザー指定ファイルとして扱われていること
- 音声入力パスがユーザー指定ファイルとして扱われていること
- wav / mp3 / m4a の対象拡張子が明確であること
- 拡張子だけに依存せず、ffprobe による実体確認があること
- ファイルサイズ上限が存在すること
- 音声長さ上限が存在すること
- 音声ストリームなしファイルが拒否されること
- 壊れた音声ファイルに対してエラー分類があること
- エラー時に既存の有効状態を不用意に壊さない方針があること
- TEXT / 音声入力の状態遷移が docs と矛盾していないこと

確認観点。

```text
- 任意ファイル読み込みを許す箇所があるか
- 拡張子偽装時に ffprobe 側で拒否できるか
- サイズ制限前に重い処理へ入っていないか
- 長大ファイルでGUIを固める可能性がないか
- ユーザー向けエラーが復旧可能な表現になっているか
```

### 9.4 Step 4: ffprobe 実行経路の確認

確認対象。

```text
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/audio_convert.py
src/core/audio_errors.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
```

確認すること。

- ffprobe 実行が subprocess 経由で行われていること
- shell 文字列連結がないこと
- ユーザー入力パスが shell に渡されていないこと
- 引数が list で渡されていること
- timeout / cancel 対応が整理されていること
- ffprobe 失敗時のエラー分類があること
- stdout / stderr の扱いが適切であること
- 長時間処理や異常停止時にGUIが固まり続けないこと
- ffprobe 未検出時に明確なエラーになること

### 9.5 Step 5: ffmpeg 実行経路の確認

確認対象。

```text
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/mmd_wav_export.py
src/core/audio_errors.py
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
```

確認すること。

- ffmpeg 実行が subprocess 経由で行われていること
- shell 文字列連結がないこと
- 引数が list で渡されていること
- 入力パス / 出力パスが安全に引数として扱われていること
- 解析用WAV生成と MMD用WAV生成の責務が分離されていること
- 失敗時 cleanup があること
- 不完全ファイルが残りにくいこと
- 上書き時の確認があること
- cancel 時に terminate / kill が適切に扱われていること
- ffmpeg stderr をユーザーにそのまま過剰表示していないこと
- ffmpeg 未検出時に明確なエラーになること

### 9.6 Step 6: FFmpeg / ffprobe 探索経路の確認

確認対象。

```text
src/core/ffmpeg_locator.py
MMD_AutoLipTool.spec
build.ps1
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
```

確認すること。

- `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe` を優先探索すること
- PATH fallback の仕様が明確であること
- 未検出時に自動ダウンロードしないこと
- PyInstaller onefile 時の同梱先が仕様と矛盾しないこと
- build 前に `FFmpeg\bin\` の必須 exe 存在確認があること
- 同梱バイナリのライセンス通知が docs に記録されていること
- `--enable-gpl --enable-version3` が release readiness のリスクとして扱われていること

確認観点。

```text
- PATH fallback によって意図しない ffmpeg を拾うリスクを、仕様として許容しているか
- 同梱版とPATH版の違いがエラー調査時に分かるか
- 自動ダウンロード禁止が維持されているか
- バンドル前提とドキュメントが矛盾していないか
```

### 9.7 Step 7: temp / cache 処理の確認

確認対象。

```text
src/core/audio_cache.py
src/core/audio_convert.py
src/core/mmd_wav_export.py
.gitignore
docs/Release_Package_Manifest.md
docs/Pipeline_Data_Contract_Specification.md
docs/Version_Control.md
```

確認すること。

- `cache/analysis_wav/` が内部生成物として扱われていること
- cache ファイル名が入力パスから決定される場合、衝突や過剰情報露出がないこと
- 入力ファイルパスの生文字列がファイル名にそのまま出ていないこと
- cache が Git 追跡対象外であること
- cache が release package から除外されること
- 一時ファイル生成と最終ファイル移動が安全であること
- 失敗時 cleanup があること
- 不完全ファイルが残った場合の扱いが整理されていること
- MMD用WAV保存時に既存ファイル上書き確認があること

確認観点。

```text
- ユーザー指定パスへの意図しない上書きがないか
- temp ファイル名が予測可能すぎて衝突しないか
- エラー時に破損ファイルを残さないか
- cache を配布物に混入させる可能性がないか
```

### 9.8 Step 8: GUI / worker / Busy 状態の確認

確認対象。

```text
src/gui_wx/app_controller.py
src/gui_wx/audio_worker.py
src/gui_wx/ui_state.py
src/gui_wx/main_frame.py
tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py
docs/GUI_State_Theme_Specification.md
```

確認すること。

- 音声処理中の二重実行が防止されていること
- Busy 中に危険な操作が無効化されること
- worker 結果が late callback として破棄されること
- cancel 時の状態復帰が整理されていること
- アプリ終了時の worker 結果破棄が整理されていること
- エラー時にGUIが操作不能状態へ残らないこと
- 長時間処理確認が機能仕様と一致していること

確認観点。

```text
- ユーザー操作の連打で状態が壊れないか
- worker結果が古い入力に対して反映されないか
- cancel後に古い結果が復活しないか
- Busy解除漏れがないか
```

### 9.9 Step 9: エラーメッセージ / 情報露出の確認

確認対象。

```text
src/core/audio_errors.py
src/gui_wx/app_controller.py
docs/Error_Handling_Specification.md
README.md
readme_mmdautolip.txt
```

確認すること。

- エラー分類がユーザーに理解可能な粒度になっていること
- traceback をそのままユーザーに見せていないこと
- FFmpeg stderr を過剰に表示していないこと
- ローカルパスを必要以上に表示していないこと
- 復旧方法が推測できるメッセージになっていること
- セキュリティ上、不要な内部情報を出していないこと
- ただし、問題解決に必要な情報まで隠しすぎていないこと

確認観点。

```text
- ユーザー向けメッセージと開発者向け詳細が混ざっていないか
- エラーコードや分類が追跡可能か
- ローカルパス露出が許容範囲か
```

### 9.10 Step 10: PyInstaller / package 混入リスク確認

確認対象。

```text
MMD_AutoLipTool.spec
build.ps1
docs/Release_Package_Manifest.md
.gitignore
README.md
NOTICE
THIRD_PARTY_LICENSES.md
```

確認すること。

- onefile 前提が docs と一致していること
- `dist\MMD_AutoLipTool.exe` が想定成果物であること
- `FFmpeg\bin\` 内容が bundle 対象になっていること
- `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` が配布物に含まれる前提であること
- `src/`、`tests/`、`docs/`、`.venv/`、`build/`、`cache/` などが実行用ZIPから除外されること
- package 手順で不要ファイルが混入するリスクがないか
- Windows Defender 等で不審に見えやすい要素について、説明不足がないか

### 9.11 Step 11: 依存関係・ライセンス隣接確認

確認対象。

```text
requirements.txt
pyproject.toml
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
```

確認すること。

- 現在の主要依存が docs に記載されていること
- wxPython / matplotlib / numpy / openai-whisper / pyopenjtalk / PyInstaller / FFmpeg などの扱いが記録されていること
- FFmpeg `--enable-gpl --enable-version3` が release readiness の確認事項として扱われていること
- license text 同梱の未確定点が残課題として扱われていること
- 自動ダウンロードやクラウド依存前提の機能が入っていないこと
- MS18-B6へ引き継ぐべき license / package 確認事項が明確であること

### 9.12 Step 12: テスト存在確認

MS18-B2では、テスト実行は必須ではない。  
ただし、セキュリティ確認に関係する既存テストが存在するかを確認する。

確認対象。

```text
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_audio_cache.py
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_late_worker_result_discard.py
tests/test_ms17_b8_busy_action_states.py
```

確認すること。

- 失敗時 cleanup のテストがあるか
- cancel のテストがあるか
- late callback 破棄のテストがあるか
- ffmpeg / ffprobe runner のテストがあるか
- cache 生成のテストがあるか
- 上書き確認のテストがあるか
- MS18-B4で修正する場合に再実行すべきテストが特定できるか

### 9.13 Step 13: リスク分類

確認結果を P1 / P2 / P3 に分類する。

```text
P1:
  リリース前に必ず修正すべき重大問題。
  例:
  - shell=True 相当の危険な実行
  - ユーザー入力を shell 文字列へ連結している
  - 任意パスへ意図せず上書き可能
  - cleanup 不備により破損ファイルを正常出力として扱う
  - 自動ダウンロードや不明バイナリ実行がある
  - package に cache / 個人情報 / 開発用ファイルが混入する高リスク

P2:
  MS18内で修正または扱いを確定すべき問題。
  例:
  - エラー時 cleanup が不十分
  - ffmpeg / ffprobe 探索結果の説明不足
  - timeout / cancel / kill の扱いが不明瞭
  - 例外分類不足
  - エラー表示が過度に内部情報を含む
  - 重複コードにより安全性確認がしづらい

P3:
  記録・表現・将来改善でよい問題。
  例:
  - docs 表現の軽微な不足
  - README の補足不足
  - cache / temp 管理の将来改善
  - package 手順の説明改善
```

### 9.14 Step 14: MS18-B3以降への引き継ぎ整理

確認結果を、以下の形で整理する。

```text
MS18-B3へ:
  - Refactor Scope Definition で扱うべき重複・非効率・安全性改善候補

MS18-B4へ:
  - 実装修正候補
  - 追加・更新すべきテスト候補

MS18-B5へ:
  - SmokeLaunch / Process Residual Investigation に関係する確認事項

MS18-B6へ:
  - Release / Packaging / License Preflight へ渡す license / package / 同梱物確認事項

MS18-B7へ:
  - Actual MMD Manual Verification Closeout へ渡す実MMD確認観点
```

### 9.15 Step 15: 実装変更がないことの確認

作業終了時に以下を実行する。

```powershell
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

- MS18-B2作業によりコード差分が発生していないこと
- docs差分が発生していないこと
- staged差分が発生していないこと

差分が存在する場合は、MS18-B2の範囲違反として報告する。  
ただし、ユーザーが明示的に文書作成を同時依頼した場合のみ、対象文書差分を別扱いで報告する。

## 10. 状態遷移 / データ契約

MS18-B2では、アプリケーションの実装上の状態遷移やデータ契約は変更しない。

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

MS18-B2で行うのは、これらに対するセキュリティ・安全運用上のリスク確認である。  
仕様変更が必要に見える場合でも、このBlockでは変更せず、P1 / P2 / P3 として分類して MS18-B3以降へ引き継ぐ。

## 11. テスト方針

MS18-B2では、実装変更を行わないため、自動テスト実行は必須ではない。

ただし、必要に応じて、既存テストの存在確認や collect-only は許可する。

```powershell
.\.venv\Scripts\python.exe -m pytest --version
.\.venv\Scripts\python.exe -m pytest --collect-only
```

実際のテスト実行は、原則として MS18-B4 で修正を行う場合に実施する。

MS18-B2でテストを実行した場合は、以下を報告する。

- 実行コマンド
- 結果
- 終了コード
- pass / fail / error
- 未実行テスト
- 未実行理由

MS18-B2では、以下は行わない。

- テスト修正
- テスト追加
- 全体 pytest を完了条件にすること
- wx teardown 由来の既知不安定性の詳細調査

## 12. 受け入れ条件

MS18-B2の完了条件は以下。

- `main / origin/main` を正本として確認している
- 実装変更が行われていない
- docs変更が行われていない
- 外部ファイル入力のセキュリティ観点を確認している
- ffprobe 実行経路を確認している
- ffmpeg 実行経路を確認している
- subprocess 引数処理を確認している
- shell injection 相当リスクを確認している
- FFmpeg / ffprobe 探索順を確認している
- 自動ダウンロード禁止が維持されているか確認している
- temp / cache / 出力ファイル処理を確認している
- 上書き確認と失敗時 cleanup を確認している
- GUI / worker / Busy 状態の安全性を確認している
- エラーメッセージ / 情報露出を確認している
- PyInstaller / package 混入リスクを確認している
- FFmpeg build configuration とライセンス通知上のリスクを確認している
- 確認結果が P1 / P2 / P3 に分類されている
- MS18-B3 / B4 / B5 / B6 / B7 への引き継ぎ事項が整理されている

## 13. リスクと対策

### 13.1 抽象的なセキュリティ論に寄りすぎる

#### リスク

一般的なセキュリティチェック項目に寄りすぎ、MMD_AutoLipTool 固有の危険箇所を見落とす。

#### 対策

確認対象を以下に限定する。

- 外部音声ファイル
- ffmpeg / ffprobe
- subprocess
- temp / cache
- MMD用WAV出力
- GUI worker
- PyInstaller onefile
- release package
- FFmpeg license notice

### 13.2 調査Blockなのに修正してしまう

#### リスク

P1 / P2 を見つけた時点で、このBlock内で修正してしまい、作業範囲が崩れる。

#### 対策

MS18-B2では、問題を分類するだけに留める。  
修正候補は MS18-B3 / MS18-B4 へ引き継ぐ。

### 13.3 ライセンス確認を法的断定として扱う

#### リスク

FFmpeg の `--enable-gpl --enable-version3` に関する確認を、法的判断として断定してしまう。

#### 対策

MS18-B2では、法的判断を行わない。  
Release readiness 上の確認項目として、MS18-B6へ引き継ぐ。

### 13.4 PATH fallback の扱いを過剰に問題視する

#### リスク

PATH fallback は仕様として存在する可能性があるため、存在だけで P1 と判定してしまう。

#### 対策

PATH fallback は、仕様・ユーザー通知・トラブルシュート観点で評価する。  
意図しないバイナリ実行につながる実装上の問題がある場合のみ P1 / P2 として扱う。

### 13.5 情報露出を過剰に隠しすぎる

#### リスク

ローカルパスや FFmpeg エラーを一切出さない方針に寄せると、ユーザーが問題解決できなくなる。

#### 対策

ユーザー向け表示と開発者向け詳細を分ける観点で評価する。  
「必要な復旧情報」と「不要な内部情報」を区別する。

## 14. AI agent 作業時の注意

MS18-B2をAI agentに依頼する場合は、以下を明示する。

```text
今回は MS18-B2: Security Preflight Review の作業です。

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

確認対象は以下です。

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
docs/Release_Package_Manifest.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/MS18_and_Beyond_Roadmap.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/Implementation_Plan/MS18-B1_Implementation_Plan.md
docs/repo_milestone.md
docs/Version_Control.md

以下を確認してください。

1. 外部ファイル入力の安全性
2. wav / mp3 / m4a 入力制限
3. ffprobe / ffmpeg 実行経路
4. subprocess 引数処理
5. shell injection 相当リスク
6. FFmpeg / ffprobe 探索順
7. 自動ダウンロード禁止が維持されているか
8. temp / cache / 出力ファイル処理
9. 上書き確認と失敗時 cleanup
10. GUI / worker / Busy 状態の安全性
11. エラーメッセージ / 情報露出
12. PyInstaller / package 混入リスク
13. FFmpeg build configuration とライセンス通知上のリスク
14. MS18-B3以降へ引き継ぐべき項目

確認結果は、P1 / P2 / P3 に分類してください。

P1:
  リリース前に必ず修正すべき重大問題。

P2:
  MS18内で修正または扱いを確定すべき問題。

P3:
  記録・表現・将来改善でよい問題。

完了報告では、以下を必ず記載してください。

1. 現在ブランチ
2. local main / origin/main の同期状態
3. working tree / staged 差分の有無
4. 確認したファイル
5. 確認した観点
6. P1 / P2 / P3 リスク分類
7. MS18-B3への引き継ぎ
8. MS18-B4への引き継ぎ
9. MS18-B5への引き継ぎ
10. MS18-B6への引き継ぎ
11. MS18-B7への引き継ぎ
12. 実装変更を行っていないこと
```

## 15. MS18-B2 Completion Report

# MS18-B2 Completion Report

## 1. Git状態

- Current branch: `feature/MS18`
- Latest local commit: `51ecfe2 Document sandbox command constraints`
- Latest `main` commit: `1099a79a683aa87a98902a0dd653d9a4681560b4`
- Latest `origin/main` commit: `1099a79a683aa87a98902a0dd653d9a4681560b4`
- local `main` / `origin/main`: 同一コミットで同期済み
- Working tree: MS18-B1文書更新と `.gitignore` の既存差分に加え、MS18-B2文書更新を追加
- Staged diff: なし

## 2. 実行コマンド

```powershell
git status --short --branch
git branch
git log --oneline -n 10
git remote -v
git fetch origin
git rev-parse main
git rev-parse origin/main
git log --oneline -n 10 origin/main
git diff --stat
git diff --cached --stat
git ls-files cache
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py tests\test_ms17_b4_ffprobe_runner.py tests\test_ms17_b5_ffmpeg_runner.py tests\test_ms17_b5_audio_cache.py tests\test_ms17_b5_audio_convert.py tests\test_ms17_b7_mmd_wav_export.py tests\test_ms17_b7_mmd_wav_failure_cleanup.py tests\test_ms17_b7_mmd_wav_overwrite_confirm.py tests\test_ms17_b8_cancel_ffmpeg_ffprobe.py tests\test_ms17_b8_late_worker_result_discard.py tests\test_ms17_b8_busy_action_states.py
```

## 3. 確認ファイル

- `src/core/audio_input.py`
- `src/core/audio_probe.py`
- `src/core/audio_convert.py`
- `src/core/audio_cache.py`
- `src/core/audio_errors.py`
- `src/core/ffmpeg_locator.py`
- `src/core/ffmpeg_runner.py`
- `src/core/ffprobe_runner.py`
- `src/core/mmd_wav_export.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/main.py`
- `build.ps1`
- `MMD_AutoLipTool.spec`
- `requirements.txt`
- `pyproject.toml`
- `.gitignore`
- `README.md`
- `readme_mmdautolip.txt`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`
- `docs/Release_Package_Manifest.md`
- `docs/Error_Handling_Specification.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS18_Block_Breakdown.md`
- `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
- `tests/test_ms17_b3_ffmpeg_locator.py`
- `tests/test_ms17_b4_ffprobe_runner.py`
- `tests/test_ms17_b5_ffmpeg_runner.py`
- `tests/test_ms17_b5_audio_cache.py`
- `tests/test_ms17_b5_audio_convert.py`
- `tests/test_ms17_b7_mmd_wav_export.py`
- `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
- `tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`
- `tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms17_b8_busy_action_states.py`

## 4. Security Preflight Findings

### 4.1 外部ファイル入力

- 判定: P1なし。MS18-B2通過。
- 根拠: 音声入力は拡張子判定後、存在・ディレクトリ・ファイルサイズ上限・ffprobeによる音声ストリーム確認・音声長上限を通る。TEXT入力はGUIのFileDialogで既存ファイルを選択し、UTF-8系読み込み失敗時はユーザー向けエラーになる。
- リスク: 拡張子判定自体は簡易だが、音声実体確認はffprobe側に委ねられているため、現状ではP1/P2扱いにしない。

### 4.2 ffprobe 実行経路

- 判定: P1なし。MS18-B2通過。
- 根拠: `src/core/ffprobe_runner.py` は引数list、`shell=False`、timeout、FileNotFound/PermissionError分類、cancellable runnerではPopenとCancelTokenを使用する。
- リスク: なし。関連テスト `test_ms17_b4_ffprobe_runner.py` と `test_ms17_b8_cancel_ffmpeg_ffprobe.py` が通過。

### 4.3 ffmpeg 実行経路

- 判定: P1なし。MS18-B2通過。
- 根拠: `src/core/ffmpeg_runner.py` は解析用WAVとMMD用WAVを別関数で構成し、いずれも引数list、`shell=False`、timeoutを使用する。MMD用WAVでは `-bitexact` を指定し、出力後にWAV仕様検証を行う。
- リスク: なし。関連テスト `test_ms17_b5_ffmpeg_runner.py`、`test_ms17_b5_audio_convert.py`、`test_ms17_b7_mmd_wav_export.py`、`test_ms17_b7_mmd_wav_failure_cleanup.py` が通過。

### 4.4 subprocess / shell injection

- 判定: P1なし。MS18-B2通過。
- 根拠: ffprobe/ffmpeg呼び出しはshell文字列連結ではなくlist引数で行われ、`shell=False` が使われている。ユーザー指定パスはコマンド文字列へ連結されていない。
- リスク: なし。PATH fallbackは探索仕様として存在するため、存在のみではshell injection相当リスクとは判定しない。

### 4.5 FFmpeg / ffprobe 探索順

- 判定: P1なし。MS18-B2通過。
- 根拠: 探索順は repo local `FFmpeg\bin`、PyInstaller展開先、PATH fallback、未検出の順。自動ダウンロードは実装されていない。`build.ps1` はビルド前に `FFmpeg\bin\ffmpeg.exe` / `ffprobe.exe` の存在を確認する。
- リスク: PATH fallbackでユーザー環境側のffmpeg/ffprobeを拾う可能性は仕様上許容されている。トラブルシュート時に探索元の説明を増やす余地はP3。

### 4.6 temp / cache / 出力ファイル処理

- 判定: P1なし。MS18-B2通過。
- 根拠: 解析用WAVは `cache/analysis_wav` 配下に生成され、ファイル名はsafe stemと短縮hashで構成される。`cache/` はGit追跡対象外で、Release Package Manifestでも除外対象。MMD用WAVは一時ファイルへ出力し、検証後に `os.replace` で保存する。既存ファイルはGUI側で上書き確認する。
- リスク: cacheファイル名には元音声のstemが残るため、ローカル生成物として扱う必要がある。現状はGit/release除外済みのためP3。

### 4.7 GUI / worker / Busy 状態

- 判定: P1なし。MS18-B2通過。
- 根拠: 音声処理は `AudioWorker` と `AudioWorkerState` で管理され、Busy中の主要操作制限、キャンセル、late callback破棄、shutdown時の結果破棄がある。
- リスク: なし。`test_ms17_b8_late_worker_result_discard.py` と `test_ms17_b8_busy_action_states.py` が通過。

### 4.8 エラーメッセージ / 情報露出

- 判定: P1なし。P3あり。
- 根拠: GUIの主要エラー表示は `str(error)` 中心で、FFmpeg/ffprobe stderrは要約扱い。`src/main.py` の `error.log` と一部 `traceback.print_exc()` はローカル診断用として残っている。
- リスク: `error.log` や開発コンソールにはローカルパスやtracebackが出る可能性がある。実行用ZIPでは `*.log` を配布物から除外する前提であり、現状はP3の記録・運用確認に留める。

### 4.9 PyInstaller / package 混入リスク

- 判定: P1なし。P3あり。
- 根拠: `MMD_AutoLipTool.spec` は `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` をdatasに含め、`FFmpeg\bin` の通常ファイルを `FFmpeg` 配下へバンドルする。Release Package Manifestは `src/`、`tests/`、`docs/`、`.venv/`、`build/`、`cache/` 等を実行用ZIPから除外する。
- リスク: `build.ps1 -Clean` は `dist\MMD_AutoLipTool.exe` の旧onefile成果物を明示削除していない。ただしPyInstaller失敗時は終了コードで止まり、成功時は成果物確認を行うため、現状はP3の手順改善候補。

### 4.10 FFmpeg license / release readiness

- 判定: Security上のP1なし。Release readiness上のP2あり。
- 根拠: 実配置の `ffmpeg.exe` / `ffprobe.exe` は `N-123549-g70537ec8e6-20260318` で、configurationに `--enable-gpl --enable-version3` を含む。NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestは、この構成をリリース前確認事項として記録している。
- リスク: 実配布前にFFmpeg関連license texts / noticeの最終確定が必要。MS18-B6へ引き継ぐ。

## 5. Risk Classification

### P1

- なし。

### P2

- FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定が未完了。MS18-B6で扱う。
- `build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因は未確定。Security PreflightではP1ではないが、release readiness上はMS18-B5で扱う。
- 実MMDでのVMD / MMD用WAV読み込み・再生確認は未完了。Security PreflightではP1ではないが、release readiness上はMS18-B7で扱う。

### P3

- PATH fallback時に、ユーザーが実際にどのffmpeg/ffprobeを使っているかを把握しやすくする説明改善余地がある。
- `error.log` / 開発コンソールにはローカルパスやtracebackが出る可能性がある。配布物から `*.log` は除外する前提を維持する。
- cacheファイル名には元音声のstemが残るため、Git/release除外を維持する。
- `build.ps1 -Clean` は旧 `dist\MMD_AutoLipTool.exe` を明示削除しないため、将来の手順改善候補とする。
- `.codex/config.toml` を `.gitignore` に追加する既存差分がある。製品実装差分ではないが、コミット時の範囲確認対象とする。

## 6. MS18-B3以降への引き継ぎ

### MS18-B3 Refactor Scope Definition

- B2でP1は検出していないため、MS18-B3では挙動非変更の範囲定義を中心にする。
- PATH fallback表示、error.logの扱い、cache説明、build clean手順のどれをMS18-B4の安全化対象に含めるかを分類する。

### MS18-B4 Safe Refactor Implementation

- MS18-B3で許可された場合のみ、探索元表示や軽微な診断表示改善、build clean手順改善を実装候補にする。
- ffmpeg/ffprobe実行仕様、MMD用WAV生成仕様、GUI状態遷移はB3で許可されない限り変更しない。

### MS18-B5 SmokeLaunch / Process Residual Investigation

- `build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因を調査する。
- B2時点ではSecurity P1とは判定しないが、release readiness上は解消または明示が必要。

### MS18-B6 Release / Packaging / License Preflight

- 現在配置済みFFmpeg/ffprobe `N-123549-g70537ec8e6-20260318`、`--enable-gpl --enable-version3` 構成に対して、配布ZIPへ同梱すべきlicense texts / noticeを確定する。
- `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` / `readme_mmdautolip.txt` / `Release_Package_Manifest` の最終同期を確認する。

### MS18-B7 Actual MMD Manual Verification Closeout

- 実MMD上で、生成VMDとMMD用WAVを読み込み、再生・リップモーフ・音声同期の実運用確認を行う。

## 7. テスト

- 実行したテスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py tests\test_ms17_b4_ffprobe_runner.py tests\test_ms17_b5_ffmpeg_runner.py tests\test_ms17_b5_audio_cache.py tests\test_ms17_b5_audio_convert.py tests\test_ms17_b7_mmd_wav_export.py tests\test_ms17_b7_mmd_wav_failure_cleanup.py tests\test_ms17_b7_mmd_wav_overwrite_confirm.py tests\test_ms17_b8_cancel_ffmpeg_ffprobe.py tests\test_ms17_b8_late_worker_result_discard.py tests\test_ms17_b8_busy_action_states.py`
- 結果:
  - `42 passed`
- 未実行テスト:
  - 全体pytest
- 未実行理由:
  - MS18-B2は実装変更なしのSecurity Preflightであり、対象リスクに直結する既存テストを限定実行したため。

## 8. 変更有無

- Code changes: なし。
- Docs changes: あり。ユーザー指示により、MS18-B2完了結果を本計画書と関連ドキュメントへ反映。
- Other changes: なし。

## 9. 判定

- MS18-B2 closeout: OK。Security PreflightとしてP1なし。
- 次に進むBlock: `MS18-B3: Refactor Scope Definition`

## 16. 次作業

MS18-B2完了後は、確認結果に基づいて MS18-B3 へ進む。

次作業は以下とする。

```text
MS18-B3: Refactor Scope Definition
```

MS18-B3では、MS18-B2で分類した P1 / P2 / P3 をもとに、MS18-B4で実装してよいリファクタリング・安全化修正の範囲を定義する。

MS18-B3でも原則として実装変更は行わず、以下を明確化する。

- 変更してよいファイル
- 変更してはいけない範囲
- 挙動非変更の確認方法
- MS18-B4で実施する修正候補
- MS18-B4で実施しない修正候補
- 必要なテスト方針
