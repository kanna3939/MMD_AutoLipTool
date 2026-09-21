# MS17-B9 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B9
- Block name: 統合テスト・docs補正・MS17 closeout
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B9_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE / AI agent: VSCode + Codex
- Shell: Windows PowerShell
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作業種別: 統合確認 / docs補正 / closeout
- 実装変更: 原則なし
- 許可するコード変更:
  - B3〜B8の統合確認で見つかった明確な不具合の最小修正のみ
- 禁止する変更:
  - 新機能追加
  - 大規模リファクタ
  - GUI大規模再設計
  - 仕様変更
- AIエージェント:
  - Codex

---

## 2. 背景

MS17では、MS16 closeout後の音声入力・音声変換・MMD用WAV出力拡張を段階的に実装してきた。

MS17-B3では、FFmpeg / ffprobe locator と入力音声種別判定基盤を追加した。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
```

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
- MMD用WAV仕様:
  PCM signed 16-bit little-endian / 44100 Hz / stereo

- 出力導線:
  専用の「MMD用WAV出力」ボタン

- 入力元:
  ユーザーが選択した元音声ファイル
```

MS17-B8では、GUI状態・Busy・長時間処理確認・worker結果破棄を統合した。

```text
- ffprobe検査 worker化
- 解析用WAV生成 worker化
- MMD用WAV出力 worker化
- Busy状態
- キャンセルボタン
- terminate → kill
- audio_job_id による古いworker結果破棄
- 300秒確認ダイアログ
```

MS17-B9では、B3〜B8までの成果を統合確認し、README / docs / ライセンス・配布関連文書を現在状態へ同期し、MS17 closeout を行う。

---

## 3. 目的

MS17-B9の目的は、MS17で追加した音声入力・音声変換・MMD用WAV出力・GUI状態管理の実装と文書を整合させ、MS17を完了状態として記録することである。

具体的には、以下を達成する。

1. B3〜B8の限定テスト群を確認する。
2. 既存GUI回帰テストを確認する。
3. 全体pytestは完了条件に含めない。
4. 実 `ffmpeg.exe` / `ffprobe.exe` を使った手動または任意統合確認を行う。
5. 実MMD上でのMMD用WAV読み込み確認を手動確認項目として扱う。
6. READMEにMS17で実装済みになったユーザー向け機能を反映する。
7. 配布用 `readme_mmdautolip.txt` と同梱対象の `pyproject.toml` description をMS17状態へ同期する。
8. NOTICE / THIRD_PARTY_LICENSES.md / Release Package Manifest の整合確認と必要最小限の更新を行う。
9. docs/repo_milestone.md と docs/Version_Control.md をMS17 closeout状態へ更新する。
10. MS17 Block Breakdown や関連docsに古い記述があれば補正する。
11. MS17で実装済みの範囲と、MS18以降へ送る範囲を明確に分ける。
12. 解析用WAVとMMD用WAVの役割差をdocs上で明確にする。
13. MS17完了後に次へ進める状態か判定する。

---

## 4. In Scope

MS17-B9で行う作業は以下に限定する。

### 4.1 B3〜B8限定テスト確認

以下のMS17限定テスト群を確認する。

```text
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b3_audio_input_foundation.py

tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b4_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py

tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b5_audio_cache.py

tests/test_wx_ms14_b3_input.py

tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py

tests/test_ms17_b8_audio_worker_state.py
tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
tests/test_ms17_b8_long_audio_confirmation.py
tests/test_ms17_b8_busy_action_states.py
tests/test_ms17_b8_late_worker_result_discard.py
```

実際のrepoでテストファイル名が異なる場合は、存在するテスト名を確認し、対応する限定テストを実行する。

### 4.2 既存GUI回帰テスト確認

既存GUI関連の回帰確認として、必要に応じて以下を実行する。

```text
tests/test_wx_ms15_b1_waveform.py
tests/test_wx_ms16_b6_event_selection_foundation.py
```

repo上に該当テストが存在しない場合は、存在しないことを報告し、代替の既存GUIテストを確認する。

### 4.3 実 ffmpeg / ffprobe 任意確認

実 `ffmpeg.exe` / `ffprobe.exe` を使った確認を行う。

ただし、自動テストの必須条件にはしない。

確認対象。

```text
- repo直下 FFmpeg\bin\ffmpeg.exe
- repo直下 FFmpeg\bin\ffprobe.exe
- bundled配置の想定
- PATH fallback
```

確認方針。

```text
- FFmpeg\bin\ffmpeg.exe / ffprobe.exe が存在する場合は、version確認または短い実ファイルで手動確認する
- versionは現在 `FFmpeg\bin\` に配置されている実体を正本として記録する
- 存在しない場合は、未実施理由を記録する
- PATH fallbackを使った場合は、実体パスを記録する
- 自動テストの合否条件には含めない
```

### 4.4 実MMD上でのMMD用WAV読み込み確認

実MMD上で、B7で出力したMMD用WAVを読み込めるか確認する。

ただし、自動テストではなく手動確認項目として扱う。

確認項目。

```text
- MMD用WAVがMMDで読み込めるか
- 音声ファイルとして再生できるか
- 出力WAV仕様が想定どおりか
- VMDと同じ制作フォルダに置いた場合に扱いやすいか
```

MMD環境が手元にない場合は、未実施理由を記録する。

### 4.5 README更新

MS17で実装済みになったユーザー向け機能をREADMEに反映する。

主な更新対象。

```text
- 入力音声:
  旧: PCM WAV
  新: wav / mp3 / m4a

- GUI:
  旧: WAV読み込み
  新: 音声読み込み

- 解析用WAV:
  内部処理用のWAVとして説明

- MMD用WAV:
  専用の「MMD用WAV出力」ボタンで出力可能

- Busy / キャンセル:
  音声変換系処理中の状態管理として説明

- FFmpeg / ffprobe:
  配置・同梱・PATH fallback方針を現在実装に合わせる
```

READMEは全面改稿しない。
MS17差分に必要な範囲へ留める。

### 4.6 ライセンス・配布関連文書の整合確認と最小更新

以下の文書を確認し、必要最小限で更新する。

```text
README.md
readme_mmdautolip.txt
pyproject.toml
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
```

確認観点。

```text
- MIT License本体とFFmpeg等の第三者ライセンスを混同していないか
- FFmpeg / ffprobe を同梱する場合の記録があるか
- FFmpeg / ffprobe の配置がREADME / build / spec / manifestで矛盾していないか
- Release Package ManifestにFFmpeg関連の記録があるか
- NOTICE / THIRD_PARTY_LICENSES.md に必要な第三者ライセンス記録があるか
- 自動ダウンロードを行うかのような記述が残っていないか
```

B9では、MS17に必要な最小更新を行う。
ライセンス全文や配布物整理の全面改稿が必要な場合は、リリース前検証またはMS18以降の残課題として記録する。

### 4.7 docs closeout

以下のdocsを確認・更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Implementation_Plan/MS17-B3_Implementation_Plan.md
docs/Implementation_Plan/MS17-B4_Implementation_Plan.md
docs/Implementation_Plan/MS17-B5_Implementation_Plan.md
docs/Implementation_Plan/MS17-B6_Implementation_Plan.md
docs/Implementation_Plan/MS17-B7_Implementation_Plan.md
docs/Implementation_Plan/MS17-B8_Implementation_Plan.md
```

注記。

```text
MS17-B9ではAIエージェントをCodexとして扱う。
既存文書名に Antigravity が含まれていても、過去文書名として存在する場合は無理に改名しない。
ただし、B9以降の作業指示・完了報告・実装プロンプトではCodex向けであることを明記する。
```

docsで確認すること。

```text
- MS17-B1〜B8の完了状態が正しく記録されているか
- MS17-B9 closeoutが記録されているか
- MS16の完了範囲とMS17の実装範囲が混同されていないか
- 音声拡張がMS16実装済み扱いになっていないか
- 解析用WAVとMMD用WAVが混同されていないか
- VMD出力対象がリップモーフキーフレームのみであることが維持されているか
```

### 4.8 MS17 closeout判定

B9の最後に、MS17をcloseoutできるか判定する。

判定候補。

```text
A. MS17 closeout OK
B. MS17 closeout OK。ただしREADME/docsに軽微な残課題あり
C. MS17 closeout前に補修Blockが必要
D. MS17 closeout前にテストまたは実確認の再実施が必要
E. MS17 closeout前にライセンス・配布関連補修が必要
```

---

## 5. Out of Scope

MS17-B9では以下を行わない。

```text
- 新機能追加
- wav / mp3 / m4a 入力仕様の変更
- 解析用WAV仕様の変更
- MMD用WAV仕様の変更
- VMD保存時のMMD用WAV同時出力への仕様変更
- GUIの大規模再設計
- worker構造の大規模再設計
- Whisper解析本体のworker化
- VMD生成処理のworker化
- VMD writer仕様変更
- VMD出力対象の変更
- ボーン / カメラ / 照明 / IK / 表示制御のVMD出力追加
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
- FFmpegバイナリの新規取得
- PyInstaller spec の大規模変更
- build.ps1 の大規模変更
- .gitignore作成・変更
```

B9で見つかった不具合は、以下のいずれかに分類する。

```text
- MS17 closeout前に直すべきP1/P2
- MS17 closeout後の軽微なP3
- MS18以降へ送る将来課題
- リリース前検証で扱う配布課題
```

---

## 6. 前提条件

MS17-B9は、以下を前提とする。

```text
- 作業branchは feature/MS17 である
- MS17-B1 が完了済みである
- MS17-B2 が完了済みである
- MS17-B3 が完了済みである
- MS17-B4 が完了済みである
- MS17-B5 が完了済みである
- MS17-B6 が完了済みである
- MS17-B7 が完了済みである
- MS17-B8 が完了済みである
```

B3〜B8から引き継ぐ主な仕様。

```text
- ffmpeg / ffprobe locator が存在する
- .wav / .mp3 / .m4a の入力種別判定が存在する
- ffprobe検査が存在する
- 入力ファイルサイズ上限は 500 MiB
- 音声長上限は 15分
- 解析用WAV仕様は PCM signed 16-bit little-endian / 44100 Hz / mono
- 解析用WAV保存先は cache/analysis_wav/
- MMD用WAV仕様は PCM signed 16-bit little-endian / 44100 Hz / stereo
- MMD用WAVは専用ボタンで出力する
- VMD保存時同時出力ではない
- ffprobe検査・解析用WAV生成・MMD用WAV出力はworker化されている
- Busy状態、キャンセル、300秒確認、audio_job_idによる結果破棄が存在する
```

B9で固定する方針。

```text
- 実 ffmpeg / ffprobe 確認は任意・手動確認として含める
- 実MMD確認は手動確認として含める
- 全体pytestは完了条件に含めない
- READMEはMS17実装済み機能を反映する
- ライセンス・配布関連文書は整合確認と必要最小限の更新を行う
- MS17 closeoutをrepo上に記録する
```

---

## 7. 対象ファイル

MS17-B9で確認するファイル。

```text
README.md
readme_mmdautolip.txt
pyproject.toml
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
build.ps1
MMD_AutoLipTool.spec
docs/repo_milestone.md
docs/Version_Control.md
docs/Release_Package_Manifest.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Implementation_Plan/MS17-B3_Implementation_Plan.md
docs/Implementation_Plan/MS17-B4_Implementation_Plan.md
docs/Implementation_Plan/MS17-B5_Implementation_Plan.md
docs/Implementation_Plan/MS17-B6_Implementation_Plan.md
docs/Implementation_Plan/MS17-B7_Implementation_Plan.md
docs/Implementation_Plan/MS17-B8_Implementation_Plan.md
```

MS17-B9で確認する実装ファイル。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/mmd_wav_export.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py
```

MS17-B9で更新する候補。

```text
README.md
readme_mmdautolip.txt
pyproject.toml
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

必要に応じて更新する候補。

```text
docs/Error_Handling_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
```

上記のファイルが存在しない場合は、新規作成せず、存在しないことと必要性を報告する。
B9で新規作成が必要と判断した場合は、ユーザー確認対象または残課題として記録する。

原則として変更しないファイル。

```text
build.ps1
MMD_AutoLipTool.spec
.gitignore
src/
tests/
```

ただし、統合確認で明確な不具合が見つかった場合のみ、最小限のコード・テスト補修を許可する。

---

## 8. 実施方針

### 8.1 全体方針

MS17-B9は、実装追加Blockではなく、closeout Blockである。

基本方針。

```text
- B3〜B8の実装成果を確認する
- テスト結果を確認する
- 実ffmpeg / ffprobe の任意確認を行う
- 実MMD確認を手動項目として扱う
- README / docs / ライセンス・配布関連文書を現在状態へ同期する
- MS17完了状態をrepoへ記録する
```

B9では、新機能追加を行わない。

### 8.2 テスト方針

B9では、全体pytestを完了条件に含めない。

理由。

```text
- これまで全体pytestにはハング可能性がある前提で進めてきたため
- MS17 closeoutをテスト基盤側の既知問題に引っ張られないようにするため
- B3〜B8の限定テスト群と既存GUI回帰テストでMS17範囲を確認するため
```

全体pytestを任意で実行する場合は、以下を守る。

```text
- 実行前にハング可能性を明記する
- タイムアウトや中断方針を決める
- 失敗・ハングした場合は、MS17由来か既存テスト基盤由来かを分類する
- 全体pytestの成功をMS17 closeout必須条件にしない
```

### 8.3 実ffmpeg / ffprobe確認方針

実 `ffmpeg.exe` / `ffprobe.exe` 確認はB9に含める。

ただし、自動テストの必須条件にはしない。

確認候補。

```powershell
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

PATH fallback確認候補。

```powershell
where.exe ffmpeg
where.exe ffprobe
```

実音声確認候補。

```text
- 短い wav
- 短い mp3
- 短い m4a
```

確認内容。

```text
- ffprobeでdurationが取れるか
- 解析用WAVが生成されるか
- MMD用WAVが出力されるか
- エラー時の表示が破綻しないか
```

実ファイルがrepoに存在しない場合は、ユーザー提供ファイルまたは手元の短い検証音声で手動確認する。
検証音声をrepoへ追加しない。

### 8.4 実MMD確認方針

実MMD確認は手動確認項目として扱う。

確認内容。

```text
- MMD用WAVをMMDで読み込めるか
- MMD上で音声再生できるか
- MMD側で極端なエラーが出ないか
- VMDと同じ制作フォルダへ保存した場合に扱いやすいか
```

MMD環境がない場合は、以下のように記録する。

```text
- 実MMD確認: 未実施
- 理由: 手元環境にMMDがないため
- 代替確認: WAV仕様 / ffmpeg出力 / ファイル読み取り確認
- 残課題: リリース前手動確認で実施
```

### 8.5 README更新方針

READMEはエンドユーザー向け文書として更新する。

更新対象。

```text
- 概要
- 対応入力形式
- GUIの使い方
- FFmpeg / ffprobe の扱い
- MMD用WAV出力
- 注意事項
- 既知の制限
```

記述方針。

```text
- 実装済みの機能だけを完了扱いする
- 未実装の機能をできるように書かない
- MS17で実装された範囲をユーザーが理解できるようにする
- 技術詳細はdocsへ寄せる
- READMEを全面改稿しない
```

READMEで明確にすること。

```text
- 入力音声は wav / mp3 / m4a に対応
- 内部では解析用WAVを生成する
- MMD用WAVは専用ボタンで出力する
- MMD用WAVはVMD保存時の自動同時出力ではない
- FFmpeg / ffprobe が必要
- FFmpeg / ffprobe は自動ダウンロードしない
- 配布物に同梱する場合は第三者ライセンスに従う
```

### 8.6 ライセンス・配布関連更新方針

MS17ではFFmpeg / ffprobe連携が重要要素になるため、B9でライセンス・配布関連文書を整合させる。

確認対象。

```text
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
README.md
readme_mmdautolip.txt
pyproject.toml
```

方針。

```text
- MIT License本体と第三者ライセンスを分ける
- FFmpeg / ffprobe の由来・配置・同梱方針を記録する
- FFmpeg / ffprobe のversionは、現在配置済みの実体を確認して記録する
- 自動ダウンロードしないことを明確にする
- onefile / onedir / FFmpeg配置の説明が矛盾しないようにする
- 不明なライセンス条件を断定しない
```

B9では必要最小限の更新に留める。
FFmpeg配布元や具体的なライセンス文面の精査が不足する場合は、リリース前検証の残課題として記録する。

### 8.7 docs更新方針

B9では、MS17の完了状態をdocsへ記録する。

最低限更新する文書。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

必要に応じて更新する文書。

```text
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Release_Package_Manifest.md
docs/Error_Handling_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
```

注記。

```text
現行のMS17ブロック分解文書は `docs/Implementation_Plan/MS17_Block_Breakdown.md` である。
Antigravity名の過去文書が別途存在する場合のみ、過去文書名として維持してよい。
ただし、MS17-B9以降の作業指示ではAIエージェントをCodexとして扱う。
```

### 8.8 closeout記録方針

`docs/repo_milestone.md` には、MS17-B9とMS17全体のcloseoutを記録する。

記録内容。

```text
- MS17-B9実施日
- B3〜B8の統合確認
- 限定テスト結果
- 実ffmpeg / ffprobe確認結果
- 実MMD確認結果または未実施理由
- README更新
- ライセンス・配布関連文書更新
- MS17 closeout判定
- 残課題
- 次マイルストーン候補
```

`docs/Version_Control.md` には、ユーザー向け変更点と開発者向け変更点を分けて記録する。

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
- MS17-B8完了commitまたは記録があるか
- MS17-B8の実装・docs差分が未コミットのまま残っている場合、B9差分と混在していることを明記する
- B9開始前に意図しない差分がないか
```

現在branchが `feature/MS17` ではない場合は、checkoutせず報告する。
MS17-B8の未コミット差分が残っている場合は、勝手にcommit / resetせず、B9実施報告で差分の由来を分けて記録する。

### Step 2: MS17成果ファイル確認

以下を確認する。

```text
src/core/ffmpeg_locator.py
src/core/audio_input.py
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/mmd_wav_export.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py
```

確認観点。

```text
- B3〜B8の実装ファイルが存在するか
- B3〜B8の実装がdocs記録と一致しているか
- 解析用WAVとMMD用WAVの責務が分離されているか
- B8のworker / Busy / cancel / audio_job_id が存在するか
```

### Step 3: B3〜B8限定テスト実行

存在するB3〜B8テストを確認し、限定実行する。

基本コマンド。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py

.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py

.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

存在しないテストがある場合。

```text
- 実際のテスト名を確認する
- リネーム・統合されている場合は対応テストを実行する
- 未作成の場合はMS17 closeout可否に影響するか分類する
```

### Step 4: 既存GUI回帰テスト実行

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

存在しない場合は、代替GUIテストを検索し、実行可能な範囲で確認する。

### Step 5: 全体pytestの扱いを確認

全体pytestは完了条件に含めない。

実行しない場合は、次のように記録する。

```text
全体pytest:
- 実行していない
- 理由: 既知のハング可能性があり、MS17 closeout条件はB3〜B8限定テストと既存GUI回帰テストで確認する方針のため
```

任意で実行する場合は、実行前に理由・中断方針を記録し、結果を分類する。

### Step 6: 実 ffmpeg / ffprobe 確認

まず配置確認を行う。

```powershell
Test-Path .\FFmpeg\bin\ffmpeg.exe
Test-Path .\FFmpeg\bin\ffprobe.exe
```

存在する場合は、以下を実行する。

```powershell
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

PATH fallback確認が必要な場合。

```powershell
where.exe ffmpeg
where.exe ffprobe
```

確認結果として記録する。

```text
- repo直下配置:
- PATH fallback:
- ffmpeg version:
- ffprobe version:
- 実体パス:
- 実行可否:
```

この確認は任意・手動確認であり、自動テスト必須条件ではない。

### Step 7: 実音声ファイルによる手動統合確認

短い検証音声を使い、以下を確認する。

```text
- wav読み込み
- mp3読み込み
- m4a読み込み
- ffprobe検査
- 解析用WAV生成
- 波形表示
- 解析実行
- VMD生成
- MMD用WAV出力
- Busy表示
- キャンセル
- 300秒確認の条件
```

検証音声がない場合は、未実施項目と理由を記録する。

検証音声はrepoへ追加しない。

### Step 8: 実MMD確認

MMD環境がある場合、MMD用WAVを読み込む。

確認項目。

```text
- MMDでMMD用WAVを読み込める
- MMD上で音声が再生できる
- 出力ファイル名・保存導線が使いやすい
```

MMD環境がない場合。

```text
- 実MMD確認は未実施
- 理由を記録
- リリース前確認へ送る
```

### Step 9: README更新

READMEをMS17完了状態へ更新する。

更新候補。

```text
- 現在バージョン / milestone状態
- 入力形式
- GUI操作手順
- 音声読み込み
- 解析用WAV
- MMD用WAV出力
- FFmpeg / ffprobe要件
- 注意事項
- 既知の制限
```

READMEで明示する内容。

```text
- wav / mp3 / m4a 入力対応
- FFmpeg / ffprobe が必要
- 自動ダウンロードはしない
- 解析用WAVは内部処理用
- MMD用WAVは専用ボタンから出力
- VMD保存時のMMD用WAV自動同時出力ではない
- VMD出力対象はリップモーフキーフレームのみ
```

### Step 10: ライセンス・配布関連文書確認・更新

以下を確認する。

```text
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
README.md
```

確認観点。

```text
- FFmpeg / ffprobe の同梱または配置方針が記録されているか
- MIT License本体とFFmpeg等の第三者ライセンスが分離されているか
- 自動ダウンロードしないことが明記されているか
- build.ps1 / spec / README / Manifest の配置説明が矛盾していないか
```

必要最小限で更新する。

B9で確定できない第三者ライセンス詳細がある場合は、断定せず残課題として記録する。

### Step 11: docs closeout更新

以下を更新する。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

必要に応じて以下も更新する。

```text
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Release_Package_Manifest.md
docs/Error_Handling_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
```

記録内容。

```text
- MS17-B9実施
- MS17 closeout
- B3〜B8限定テスト結果
- 実ffmpeg / ffprobe確認結果
- 実MMD確認結果または未実施理由
- README更新
- ライセンス・配布関連文書更新
- 残課題
- 次マイルストーン候補
```

### Step 12: 補修が必要な場合の扱い

B9中に不具合が見つかった場合、以下に分類する。

```text
P1:
MS17 closeout前に直すべき重大な問題

P2:
closeout前に直すべき整合問題

P3:
closeout後でもよい軽微なdocs・表現問題

Future:
MS18以降へ送る機能・設計課題

Release:
リリース前検証で扱う配布・ライセンス課題
```

B9でコード修正してよいのは、P1/P2のうちMS17実装に直接関係する明確な不具合の最小修正のみ。

大規模修正が必要な場合は、B9内で無理に直さず、補修Blockを提案する。

### Step 13: closeout判定

最後に、MS17 closeout可否を判定する。

判定候補。

```text
A. MS17 closeout OK
B. MS17 closeout OK。ただし軽微なdocs残課題あり
C. MS17 closeout前に補修Blockが必要
D. MS17 closeout前にテストまたは手動確認の再実施が必要
E. MS17 closeout前にライセンス・配布関連補修が必要
```

推奨される完了状態はAまたはBである。
ただし、テスト失敗、実装不整合、ライセンス重大未整備がある場合はC〜Eを選ぶ。

### Step 14: 完了前diff確認

以下を実行する。

```powershell
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
git diff -- .gitignore
```

想定される変更ファイル。

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
```

必要に応じて追加・変更される可能性があるファイル。

```text
docs/Error_Handling_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
```

原則として差分が出ないことを確認するファイル。

```text
build.ps1
MMD_AutoLipTool.spec
.gitignore
```

`.gitignore` に差分が出ている場合は、ユーザー側管理対象なので元に戻し、報告する。

---

## 10. 状態遷移 / データ契約

### 10.1 MS17完了時の入力音声契約

MS17完了時点で、入力音声は以下を扱う。

```text
.wav
.mp3
.m4a
```

入力音声は、ユーザーが選択した元ファイルである。

```text
AudioInputInfo.source_path
```

### 10.2 解析用WAV契約

解析用WAVは、波形表示・解析・timing plan生成の内部正本である。

```text
AnalysisWavResult.analysis_wav_path
```

仕様。

```text
PCM signed 16-bit little-endian
44100 Hz
mono
```

保存先。

```text
cache/analysis_wav/
```

B9では、この契約がREADME/docs上で正しく説明されているか確認する。

### 10.3 MMD用WAV契約

MMD用WAVは、MMDに読み込ませるためのユーザー向け出力物である。

```text
MmdWavExportResult.mmd_wav_path
```

仕様。

```text
PCM signed 16-bit little-endian
44100 Hz
stereo
```

出力導線。

```text
専用の「MMD用WAV出力」ボタン
```

B9では、VMD保存時の自動同時出力ではないことをREADME/docsへ明記する。

### 10.4 VMD出力契約

VMD出力対象は引き続きリップモーフキーフレームのみである。

出力しないもの。

```text
- ボーン
- カメラ
- 照明
- IK
- 表示制御
```

B9では、MS17音声拡張によってVMD出力対象が変わったような記述がないか確認する。

### 10.5 Busy / worker契約

MS17完了時点で、以下がworker対象である。

```text
- ffprobe検査
- 解析用WAV生成
- MMD用WAV出力
```

Busy中は主要操作を無効化し、キャンセルボタンを有効にする。

古いworker結果は `audio_job_id` により破棄する。

---

## 11. テスト方針

### 11.1 B9で実行する標準確認

B9では、B3〜B8限定テスト群を中心に実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_ffmpeg_locator.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b3_audio_input_foundation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_probe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_audio_input_limits.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_convert.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_audio_cache.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_busy_action_states.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py
```

### 11.2 既存GUI回帰テスト

必要に応じて以下を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py
```

### 11.3 実ffmpeg / ffprobe確認

任意・手動確認として以下を行う。

```powershell
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

存在しない場合。

```powershell
where.exe ffmpeg
where.exe ffprobe
```

この確認は、MS17 closeoutの参考情報として記録する。
ただし、自動テスト必須条件にはしない。

### 11.4 実MMD確認

手動確認として、MMD用WAVをMMDに読み込ませる。

MMD環境がない場合は未実施理由を記録する。

### 11.5 全体pytest

全体pytestは完了条件に含めない。

原則として、以下は必須実行しない。

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

実行しない理由を完了報告に記録する。

---

## 12. 受け入れ条件

MS17-B9は、以下を満たしたら完了とする。

### 12.1 テスト条件

* B3〜B8の限定テスト群が実行され、結果が報告されている。
* 存在しないテストがある場合、理由と代替確認が記録されている。
* 既存GUI回帰テストが必要に応じて実行されている。
* 全体pytestを完了条件に含めていない。
* 全体pytestを実行しない理由が記録されている。

### 12.2 手動確認条件

* 実 `ffmpeg.exe` / `ffprobe.exe` の確認が行われた、または未実施理由が記録されている。
* 実音声ファイルでの統合確認が行われた、または未実施理由が記録されている。
* 実MMDでのMMD用WAV読み込み確認が行われた、または未実施理由が記録されている。

### 12.3 README条件

READMEがMS17完了状態を反映している。

最低限、以下が正しく記録されている。

```text
- wav / mp3 / m4a 入力対応
- 音声読み込み
- 解析用WAV
- MMD用WAV出力
- FFmpeg / ffprobe 要件
- 自動ダウンロードなし
- VMD出力対象はリップモーフキーフレームのみ
```

### 12.4 ライセンス・配布関連条件

以下が確認され、必要最小限で更新されている。

```text
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
README.md
```

確認観点。

```text
- FFmpeg / ffprobe の扱いが記録されている
- MIT Licenseと第三者ライセンスを混同していない
- FFmpeg自動ダウンロードを行うような記述がない
- build / spec / README / Manifest の配置説明が矛盾していない
```

### 12.5 docs closeout条件

以下が更新されている。

```text
docs/repo_milestone.md
docs/Version_Control.md
```

必要に応じて、以下も更新されている。

```text
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Release_Package_Manifest.md
docs/Error_Handling_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
```

記録上、MS17がcloseoutされたことが分かる。

### 12.6 禁止事項遵守

以下が守られている。

```text
- 新機能追加をしていない
- 解析用WAV仕様を変更していない
- MMD用WAV仕様を変更していない
- VMD保存時同時出力へ仕様変更していない
- VMD出力対象を変更していない
- 音量正規化をしていない
- 無音トリムをしていない
- 自動フェードをしていない
- 自動ノイズ除去をしていない
- Qt / PySide6 を再導入していない
- build.ps1 を大規模変更していない
- MMD_AutoLipTool.spec を大規模変更していない
- .gitignore を変更していない
```

---

## 13. リスクと対策

### Risk 1: 実ffmpeg / ffprobe確認が環境依存になる

対策。

```text
- 自動テスト必須条件にはしない
- 実施できた場合は結果を記録する
- 実施できない場合は理由を記録する
- repo直下配置とPATH fallbackを分けて記録する
```

### Risk 2: 実MMD確認が環境依存になる

対策。

```text
- 自動テストにはしない
- 手動確認項目として扱う
- MMD環境がない場合は未実施理由を記録する
- リリース前確認へ送る
```

### Risk 3: READMEに未実装機能を書いてしまう

対策。

```text
- 実装済みだけを書く
- VMD保存時MMD用WAV同時出力は実装済み扱いしない
- MMD用WAVは専用ボタン出力として説明する
- 音量正規化や無音トリム等は書かない
```

### Risk 4: ライセンス文書で断定しすぎる

対策。

```text
- 確認済みの事実のみ記録する
- 不明なFFmpeg配布条件は断定しない
- MIT License本体と第三者ライセンスを分離する
- 未確認事項はリリース前検証の残課題にする
```

### Risk 5: B9でコード修正が広がる

対策。

```text
- B9はcloseout Blockである
- コード変更は明確なP1/P2不具合の最小修正に限定する
- 大きい修正は補修Blockへ送る
```

### Risk 6: 全体pytestに引っ張られる

対策。

```text
- 全体pytestは完了条件に含めない
- B3〜B8限定テスト群を中心にする
- 既知のハング可能性を完了報告に記録する
```

### Risk 7: 解析用WAVとMMD用WAVの説明が混ざる

対策。

```text
- README/docsで役割を分けて書く
- 解析用WAVは内部正本
- MMD用WAVはユーザー向け出力物
- 保存先と仕様を分けて記録する
```

---

## 14. Codex 実施時の注意

以下のプロンプトを Codex に渡して実施する。

```text
今回は MS17-B9 です。

目的:
統合テスト・docs補正・MS17 closeoutを行ってください。

重要:
- AIエージェントは Codex です。
- 対象branchは feature/MS17 です。
- MS17-B3〜B8 の成果を前提にしてください。
- B9はcloseout Blockです。新機能追加は行わないでください。
- コード変更は、統合確認で見つかった明確なP1/P2不具合の最小修正のみ許可します。
- 大規模リファクタは行わないでください。
- 解析用WAV仕様を変更しないでください。
- MMD用WAV仕様を変更しないでください。
- VMD保存時MMD用WAV同時出力へ仕様変更しないでください。
- VMD保存処理を変更しないでください。
- VMD出力対象はリップモーフキーフレームのみです。
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去は行わないでください。
- Qt / PySide6 は再導入しないでください。
- build.ps1 / MMD_AutoLipTool.spec は大規模変更しないでください。
- .gitignore は作成・変更しないでください。

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

README.md
readme_mmdautolip.txt
pyproject.toml
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
build.ps1
MMD_AutoLipTool.spec
docs/repo_milestone.md
docs/Version_Control.md
docs/Release_Package_Manifest.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/Implementation_Plan/MS17-B3_Implementation_Plan.md
docs/Implementation_Plan/MS17-B4_Implementation_Plan.md
docs/Implementation_Plan/MS17-B5_Implementation_Plan.md
docs/Implementation_Plan/MS17-B6_Implementation_Plan.md
docs/Implementation_Plan/MS17-B7_Implementation_Plan.md
docs/Implementation_Plan/MS17-B8_Implementation_Plan.md

実装ファイル確認対象:

src/core/ffmpeg_locator.py
src/core/audio_input.py
src/core/audio_errors.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/core/mmd_wav_export.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/audio_worker.py
src/gui_wx/worker_state.py

実行する確認:

1. B3〜B8の限定テストを実行してください。
   実際のrepoに存在するテストファイル名を確認し、存在するものを実行してください。

2. 必要に応じて既存GUI回帰テストを実行してください。

3. 全体pytestは完了条件に含めないでください。
   実行しない場合は、既知のハング可能性があるため実行しない、と報告してください。

4. 実 ffmpeg.exe / ffprobe.exe の確認を行ってください。
   ただし自動テスト必須条件にはしないでください。
   repo直下 FFmpeg\bin に存在するか確認し、存在する場合は version確認を行ってください。
   存在しない場合は PATH fallback の確認、または未実施理由を記録してください。

5. 実MMDでのMMD用WAV読み込み確認を手動確認項目として扱ってください。
   MMD環境がない場合は未実施理由を記録してください。

6. READMEをMS17完了状態へ更新してください。
   以下を反映してください。
   - wav / mp3 / m4a 入力対応
   - 音声読み込み
   - 解析用WAV
   - MMD用WAV出力
   - FFmpeg / ffprobe要件
   - 自動ダウンロードなし
   - VMD出力対象はリップモーフキーフレームのみ
   README全面改稿は行わないでください。

6a. 配布用 `readme_mmdautolip.txt` と同梱対象の `pyproject.toml` descriptionを確認してください。
   - `readme_mmdautolip.txt` に旧WAV専用表現が残っていればMS17状態へ補正してください。
   - `pyproject.toml` のdescriptionがPCM WAV専用表現のままなら、wav / mp3 / m4a入力対応へ同期してください。

7. NOTICE / THIRD_PARTY_LICENSES.md / docs/Release_Package_Manifest.md を確認し、必要最小限で更新してください。
   - MIT License本体と第三者ライセンスを混同しないでください。
   - FFmpeg / ffprobe の扱いを記録してください。
   - FFmpeg / ffprobe のversionは現在配置済みの実体を確認して記録してください。
   - 自動ダウンロードを行うような記述を残さないでください。
   - 不明な配布条件は断定せず、残課題にしてください。

8. docs/repo_milestone.md と docs/Version_Control.md を更新してください。
   - MS17-B9実施
   - MS17 closeout
   - テスト結果
   - 実ffmpeg / ffprobe確認結果
   - 実MMD確認結果または未実施理由
   - README更新
   - ライセンス・配布関連文書更新
   - 残課題
   - 次マイルストーン候補
   を記録してください。

9. 必要に応じて docs/Implementation_Plan/MS17_Block_Breakdown.md や関連docsを更新してください。
   Antigravity名の過去文書が別途存在する場合のみ、過去文書名として維持してください。
   B9以降の作業指示ではCodex向けであることを明記してください。

完了前に以下を確認してください。

git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
git diff -- .gitignore

.gitignoreに差分が出ている場合は、ユーザー側管理対象なので元に戻して報告してください。

完了報告では、以下を必ず分けてください。

1. 確認したbranch / commit
2. 作業前の状態
3. 実行したテスト
4. 実行していないテスト
5. 実ffmpeg / ffprobe確認
6. 実MMD確認
7. README更新
8. ライセンス・配布関連文書更新
9. docs更新
10. 変更したファイル
11. 変更していないファイル
12. .gitignoreを変更していないこと
13. 禁止事項の遵守
14. MS17 closeout判定
15. 残課題
16. 次マイルストーン候補
```

---

## 15. 完了報告テンプレート

Codexは、完了時に以下の形式で報告する。

```text
MS17-B9 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業前の状態
- git status:
- staged diff:
- unstaged diff:

3. 実行したテスト
- B3限定テスト:
- B4限定テスト:
- B5限定テスト:
- B6限定テスト:
- B7限定テスト:
- B8限定テスト:
- 既存GUI回帰テスト:
- 結果:

4. 実行していないテスト
- 全体pytest:
- 理由:
- 存在しなかったテスト:
- 代替確認:

5. 実ffmpeg / ffprobe確認
- repo直下 ffmpeg.exe:
- repo直下 ffprobe.exe:
- PATH fallback:
- ffmpeg version:
- ffprobe version:
- 実音声確認:
- 未実施項目と理由:

6. 実MMD確認
- MMD用WAV読み込み:
- 再生確認:
- 未実施の場合の理由:
- リリース前確認への引き継ぎ:

7. README更新
- wav / mp3 / m4a入力:
- 音声読み込み:
- 解析用WAV:
- MMD用WAV出力:
- FFmpeg / ffprobe:
- 自動ダウンロードなし:
- VMD出力対象:

8. ライセンス・配布関連文書更新
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- docs/Release_Package_Manifest.md:
- READMEとの整合:
- 未確認事項:

9. docs更新
- docs/repo_milestone.md:
- docs/Version_Control.md:
- docs/Implementation_Plan/MS17_Block_Breakdown.md:
- その他docs:

10. 変更したファイル
- ...

11. 変更していないファイル
- build.ps1:
- MMD_AutoLipTool.spec:
- .gitignore:
- src:
- tests:

12. .gitignoreの扱い
- 変更していないこと:
- 差分確認結果:

13. 禁止事項の遵守
- 新機能追加:
- 解析用WAV仕様変更:
- MMD用WAV仕様変更:
- VMD保存処理変更:
- VMD出力対象変更:
- 音量正規化:
- 無音トリム:
- 自動フェード:
- 自動ノイズ除去:
- Qt / PySide6再導入:

14. MS17 closeout判定
- 判定:
- 理由:

15. 残課題
- P1:
- P2:
- P3:
- Future:
- Release:

16. 次マイルストーン候補
- ...
```

---

## 16. MS17 closeout後の引き継ぎ条件

MS17 closeout後は、以下を次段へ引き継ぐ。

```text
- wav / mp3 / m4a 入力対応済み
- FFmpeg / ffprobe locator 実装済み
- ffprobe検査・入力制限・エラー分類実装済み
- 解析用WAV生成実装済み
- GUI音声読み込み導線統合済み
- MMD用WAV出力実装済み
- Busy / cancel / 300秒確認 / audio_job_idによる結果破棄実装済み
- README / docs / ライセンス・配布関連文書をMS17状態へ同期済み
```

次段候補。

```text
- MS18: リリース前配布検証
- MS18: FFmpeg同梱配布の最終ライセンス確認
- MS18: installer / zip配布設計
- MS18: 実MMD手動確認の追加記録
- MS18: cache/analysis_wav/ の整理・容量管理
- MS18: README導入手順の改善
- MS18: ユーザー向けエラー表示改善
```

ただし、MS17-B9のcloseout判定でP1/P2が残った場合は、次段へ進まず、MS17補修Blockを先に実施する。
