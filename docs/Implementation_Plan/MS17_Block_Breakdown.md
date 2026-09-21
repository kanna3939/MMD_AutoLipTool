# MS17 Block Breakdown for Codex

> [!IMPORTANT]
> **AI Coding Assistant Directives (for Codex):**
> 本ドキュメントや `repo_milestone.md` などの巨大ドキュメントを解析する前に、まず [MS17_and_Beyond_Index.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/MS17_and_Beyond_Index.md) を最優先で読み込んでください。必要な情報がそちらにある場合は、不要な全行読み込み（トークンの浪費）を避けてください。

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Draft status: Draft
- Target branch: feature/MS17 または repo 現行方針に従う
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Codex
- Coding AI: Codex
- Shell: Windows PowerShell

## 2. MS17の位置づけ

MS17 は、MS16 closeout 後に開始する音声入力・音声変換拡張マイルストーンである。

MS16では、以下を完了済み前提として扱う。

- wxPython 主系への一本化
- Qt / PySide6 系の排除
- Preview 変形台形表示復元
- Preview shape data contract 固定
- RightPane / Info / Warning / 選択イベント等のGUI拡張基盤
- 母音イベント選択の下地
- MS16 closeout docs 更新

ただし、MS17開始時点では、過去の会話内容だけで完了状態を断定しない。必ず repo 状態、README、docs、tests を確認する。

## 3. MS17の目的

MS17の目的は、既存の TEXT + WAV 入力から VMD を生成する基本機能を壊さずに、音声入力・音声変換・MMD用WAV出力の基盤を追加することである。

主な目的は以下。

- wav / mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 入力音声の検査
- 解析用WAV生成
- 解析用WAVを波形表示・解析の正本にする
- MMD用WAV出力
- MMD互換WAV検証
- 音声変換系エラー分類
- 長時間処理確認ダイアログ
- FFmpeg / ffprobe プロセス終了方針
- 失敗時の不完全ファイル削除
- FFmpeg同梱有無、ライセンス、NOTICE、THIRD_PARTY_LICENSES 方針整理

## 4. MS17での重要な正本分離

MS17では、以下のデータを混同しない。

### 4.1 入力音声

ユーザーが選択した元ファイル。

例:

- `.wav`
- `.mp3`
- `.m4a`

入力音声はユーザー指定元ファイルであり、解析処理やMMD読み込みに直接使えるとは限らない。

### 4.2 解析用WAV

ツール内部の波形表示・解析・timing plan生成に使う正本。

- ffmpeg変換後の一時または管理対象WAV
- 波形表示の入力
- Whisper / 解析処理の入力
- timing plan生成の音声基準

### 4.3 MMD用WAV

MMDに読み込ませるための出力物。

- MMD互換性を優先
- 解析用WAVと同一仕様になる可能性はあるが、役割としては別物
- 専用導線から保存・出力される候補

### 4.4 VMD出力

引き続き、出力対象はリップモーフキーフレームのみ。

- ボーンを出力しない
- カメラを出力しない
- 照明を出力しない
- IKを出力しない
- 表示制御を出力しない

## 5. MS17全体のIn Scope

- wav / mp3 / m4a 入力対応
- ffprobe による入力音声情報取得
- ffmpeg による解析用WAV生成
- 解析用WAVを既存波形表示・解析処理へ接続
- MMD用WAV出力
- MMD互換WAVの最小検証
- 入力ファイルサイズ上限 500MB
- 音声長上限 15分
- 300秒超相当の長時間処理確認ダイアログ
- FFmpeg / ffprobe の terminate / kill 方針
- 失敗時の不完全ファイル削除
- 音声変換系エラー分類
- README / docs / repo_milestone / Version_Control 更新
- FFmpeg同梱または外部導入の方針整理
- LICENSE / NOTICE / THIRD_PARTY_LICENSES / Release Package Manifest の整合確認

## 6. MS17全体のOut of Scope

- 音量正規化
- 無音トリム
- 自動フェード
- 自動ノイズ除去
- ピッチ補正
- テンポ補正
- 複数音声ファイルの同時入力
- 複数トラック合成
- VMDのボーン / カメラ / 照明 / IK / 表示制御出力
- Qt / PySide6 系GUIの再導入
- wxPython以外のGUI主系追加
- Preview shape contract の再設計
- 母音イベント本格編集
- MMDモデルプロファイル保存機能の本格実装
- プリセット保存機能の本格実装
- FFmpegライセンス条件を未確認のまま配布仕様として確定すること

## 7. MS17 Block一覧

MS17は、以下の9 Blocksに分割する。

```text
MS17-B1: Repo / MS16 closeout 後状態確認 + MS17開始条件整理
MS17-B2: FFmpeg / ffprobe 接続方式・ライセンス・配布方針整理
MS17-B3: 音声入力拡張の前提基盤
MS17-B4: ffprobe検査 + 入力制限 + エラー分類基盤
MS17-B5: 解析用WAV生成基盤 (完了)
MS17-B6: wav / mp3 / m4a 入力導線統合 (完了)
MS17-B7: MMD用WAV出力基盤 (完了)
MS17-B8: GUI状態・Busy・長時間処理確認・worker結果破棄統合 (完了)
MS17-B9: 統合テスト・docs補正・MS17 closeout (完了)
```

---

# MS17-B1: Repo / MS16 closeout 後状態確認 + MS17開始条件整理

## 目的

MS17実装に入る前に、MS16 closeout後のrepo状態を確認し、MS17の開始条件を整理する。

このBlockでは原則として実装を行わない。

## In Scope

* 現在branch確認
* 最新commit確認
* MS16-B1〜B7のコミット状況確認
* README / docs / repo_milestone / Version_Control の整合確認
* Qt / PySide6 / 旧 src/gui 参照が戻っていないか確認
* `src/core/preview_transform.py` が存在するか確認
* RightPane / Preview shape / 選択下地関連テストの存在確認
* MS17送り項目がMS16実装済み扱いされていないか確認
* FFmpeg関連記述が現状実装と矛盾していないか確認
* `.agent/skills/build-packaging-verification/SKILL.md` の文字化け修正状況確認

## Out of Scope

* 音声変換機能の実装
* FFmpeg呼び出し実装
* GUI変更
* README修正
* docs修正
* テスト修正

ただし、明らかな記録不整合がある場合は、B1の報告で修正対象として列挙する。

## Codex 指示

```text
今回は MS17-B1 です。
repo状態確認のみを行い、実装・修正・ファイル変更は行わないでください。

まず以下を実行してください。

git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only

次に、以下を確認してください。

README.md
docs/Version_Control.md
docs/repo_milestone.md
docs/MS16_Block_Breakdown_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/VMD_Output_Specification.md
.agent/skills/build-packaging-verification/SKILL.md

確認観点は以下です。

- MS16-B1〜B7が完了扱いとして記録されているか
- READMEがMS16 closeout後の状態と矛盾していないか
- MS17対象である音声拡張がMS16実装済み扱いされていないか
- PySide6 / Qt / shiboken6 / 旧 src/gui 参照が戻っていないか
- preview_transform.py が src/core/preview_transform.py にあるか
- RightPane / Preview shape / 選択下地関連のテストが存在するか
- FFmpeg同梱有無が未確定なのに断定されていないか
- .agent/skills/build-packaging-verification/SKILL.md に文字化けが残っていないか

完了報告では、以下を必ず分けてください。

1. 確認したbranch / commit
2. 作業ツリー状態
3. MS16 closeoutの記録状態
4. README / docs の矛盾
5. PySide6 / Qt 再混入有無
6. MS17開始前に補正すべき項目
7. MS17-B2へ進めるかどうか
```

## 受け入れ条件

* repo状態が確認されている
* MS16 closeout後の整合状態が報告されている
* MS17開始前に補正が必要な項目が分類されている
* 実装変更が行われていない

---

# MS17-B2: FFmpeg / ffprobe 接続方式・ライセンス・配布方針整理

## 目的

MS17で使用する FFmpeg / ffprobe の接続方式、探索方式、配布方針、ライセンス記録方針を決める。

このBlockでは、原則として実装本体には入らない。必要最小限の調査コードまたは設計メモ作成に留める。

## In Scope

* FFmpeg / ffprobe の利用目的整理
* 同梱方式と外部導入方式の比較
* `FFmpeg\bin\ffmpeg.exe`
* `FFmpeg\bin\ffprobe.exe`
* PATH検索を許可するかどうかの整理
* PyInstaller onefile / onedir での配置方針確認
* LICENSE / NOTICE / THIRD_PARTY_LICENSES の追記方針
* Release Package Manifest への記録方針
* FFmpeg version表記の扱い
* FFmpegが見つからない場合のエラー方針

## Out of Scope

* ffmpeg変換実装
* ffprobe実装
* mp3 / m4a入力UI実装
* MMD用WAV出力実装
* FFmpeg本体のリポジトリ追加
* FFmpegバイナリの自動ダウンロード
* ライセンス条件未確認のままの配布確定

## 推奨方針

初期実装では、次の方針を推奨する。

```text
- 開発時は repo直下 FFmpeg\bin\ffmpeg.exe / ffprobe.exe を優先探索
- なければ PATH 探索を検討
- 配布時同梱の有無は B2で明示的に記録
- 自動ダウンロードはMS17では行わない
- FFmpeg同梱時は THIRD_PARTY_LICENSES.md / NOTICE / Release Package Manifest を必ず更新
```

理由:

* Windows個人ユーザー向けには同梱が使いやすい
* ただしFFmpegの配布条件を軽視できない
* 自動ダウンロードは実装・セキュリティ・ライセンス説明が増えるためMS17では避ける方が安全

## Codex 指示

```text
今回は MS17-B2 です。
FFmpeg / ffprobe の接続方式・ライセンス・配布方針を整理してください。

原則として実装は行わないでください。
ただし、既存docsの矛盾確認と、設計メモの作成・更新は行ってよいです。

確認対象:

README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Security_Safety_Specification.md
docs/Error_Handling_Specification.md
MMD_AutoLipTool.spec
build.ps1
requirements.txt
pyproject.toml

確認観点:

- FFmpeg / ffprobe を同梱する前提になっているか
- 外部導入前提になっているか
- READMEとdocsで矛盾していないか
- onefile / onedir の記述が矛盾していないか
- THIRD_PARTY_LICENSES.md にFFmpeg配布時の注意があるか
- NOTICE にユーザー向けの注意があるか
- Release Package Manifest にFFmpeg配置が記録されているか
- 自動ダウンロードを行う記述がないか

完了報告では、次を必ず分けてください。

1. 現状のFFmpeg関連記述
2. 同梱方式 / 外部導入方式のどちらに見えるか
3. 矛盾している記述
4. MS17で採用すべき推奨方針
5. B3以降で実装すべき対象
6. 未確定事項
```

## 受け入れ条件

* FFmpeg / ffprobe の探索・配布方針が整理されている
* ライセンス・NOTICE・THIRD_PARTY_LICENSESの更新必要性が明確である
* 未確定事項が断定されていない
* 自動ダウンロードをMS17で行う前提になっていない

---

# MS17-B3: 音声入力拡張の前提基盤 (完了)

## 目的

既存のWAV入力前提を壊さずに、音声入力を抽象化する前提基盤を作る。

このBlockでは、まだ本格的なffmpeg変換やm4a対応を完成扱いしない。

## In Scope

* 入力音声ファイル情報を表すデータ構造追加
* 入力音声種別の判定
* 拡張子 `.wav` / `.mp3` / `.m4a` の受け入れ準備
* GUI上の「WAV読み込み」表記見直し候補整理
* 既存WAV入力経路の互換維持
* TEXT / 音声 / パラメータ変更時の無効化規則維持
* timing plan / Preview / VMD保存可能状態 / 選択状態の無効化確認

## Out of Scope

* ffmpeg変換実行
* ffprobe実行
* MMD用WAV出力
* mp3 / m4a の完全動作保証
* 音声長検査
* ファイルサイズ検査
* 300秒確認ダイアログ

## 想定対象ファイル

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/core/audio_input.py
src/core/pipeline_contract.py
tests/test_ms17_b3_audio_input_foundation.py
```

既存構成に合わせて、ファイル名はCodex側で確認して調整する。

## 受け入れ条件

* 既存WAV入力が壊れていない
* 入力音声の拡張子判定ができる
* mp3 / m4a は受け入れ準備段階として扱われ、変換済み扱いされていない
* 音声変更時に古い timing plan / Preview / VMD保存可能状態 / 選択状態が無効化される
* Qt / PySide6 再導入がない

---

# MS17-B4: ffprobe検査 + 入力制限 + エラー分類基盤 (完了)

## 目的

ffprobeを使って入力音声の基本情報を取得し、MS17で必要な入力制限とエラー分類の基盤を作る。

## In Scope

* ffprobe実行ラッパー
* ffprobeパス解決
* ffprobe timeout方針
* ffprobe失敗時エラー分類
* 入力ファイルサイズ上限 500MB
* 音声長上限 15分
* 音声streamなしエラー
* 非対応形式エラー
* 壊れた音声ファイルエラー
* エラーメッセージのGUI表示準備
* Error_Handling_Specification との整合

## Out of Scope

* ffmpeg変換
* 解析用WAV生成
* MMD用WAV生成
* 長時間処理確認ダイアログ本体
* FFmpegバイナリ同梱作業
* 音声内容の正規化

## 想定対象ファイル

```text
src/core/ffmpeg_locator.py
src/core/ffprobe_runner.py
src/core/audio_probe.py
src/core/audio_errors.py
src/gui_wx/app_controller.py
src/gui_wx/main_frame.py
tests/test_ms17_b4_ffprobe_audio_probe.py
tests/test_ms17_b4_audio_input_limits.py
```

## 受け入れ条件

* ffprobeで音声長・codec・sample rate・channel等の基本情報が取得できる
* 500MB超過を明確に拒否できる
* 15分超過を明確に拒否できる
* ffprobe未検出、ffprobe失敗、音声streamなし、非対応形式を区別できる
* ユーザー向けエラーメッセージが過度に技術寄りになっていない
* ffprobe失敗時に古い解析結果が有効扱いされない

---

# MS17-B5: 解析用WAV生成基盤 (完了)

## 目的

ffmpegを使って、入力音声から解析用WAVを生成する。

解析用WAVは、波形表示・解析・timing plan生成の正本として扱う。

## In Scope

* ffmpeg実行ラッパー
* ffmpegパス解決
* 解析用WAV出力先管理
* 一時ファイル命名方針
* 失敗時の不完全ファイル削除
* terminate / kill 方針
* ffmpeg stderr の安全な取り扱い
* 既存WAV入力でも必要に応じて解析用WAVへ正規化
* 解析用WAVの仕様整理
* Pipeline data contract への接続

## Out of Scope

* MMD用WAV出力
* GUIファイル選択拡張の完成
* 300秒確認ダイアログ
* 音量正規化
* 無音トリム
* 自動フェード
* ノイズ除去

## 解析用WAVの推奨仕様

初期案:

```text
container: WAV
codec: PCM signed 16-bit little-endian
sample rate: 44100 Hz
channels: mono
```

最終仕様は `docs/MMD_Audio_WAV_Compatibility_Specification.md` と既存解析処理の要件を確認して決める。

## 想定対象ファイル

```text
src/core/ffmpeg_runner.py
src/core/audio_convert.py
src/core/audio_cache.py
src/gui_wx/app_controller.py
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b5_audio_cache.py
tests/test_ms17_b5_ffmpeg_runner.py
```

## 受け入れ条件

* wav / mp3 / m4a から解析用WAVを生成できる基盤がある
* 解析用WAVの出力先が管理されている
* 変換失敗時に不完全ファイルが残らない
* ffmpeg未検出時に明確なエラーになる
* ffmpeg失敗時に古い解析結果が有効扱いされない
* 解析用WAVとMMD用WAVが混同されていない

---

# MS17-B6: wav / mp3 / m4a 入力導線統合

## 目的

GUIから wav / mp3 / m4a を選択できるようにし、解析用WAV生成から既存の波形表示・解析処理へ接続する。

## In Scope

* ファイル選択dialogの拡張
* GUI文言の見直し
* 入力音声パス表示
* 入力形式表示
* ffprobe検査との接続
* 解析用WAV生成との接続
* 解析用WAVを波形表示の入力にする
* 解析用WAVを既存解析処理の入力にする
* TEXT / 音声 / パラメータ変更時の無効化規則確認
* 最近使ったファイル履歴の音声拡張対応

## Out of Scope

* MMD用WAV保存
* MMD用WAV出力
* 音声編集機能
* 変換プリセットUI
* 複数音声入力

## GUI文言候補

```text
旧: WAV読み込み
新: 音声読み込み

旧: WAVファイル
新: 音声ファイル（wav / mp3 / m4a）
```

ただし、READMEやdocsと整合させること。

## 想定対象ファイル

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/recent_files.py
src/core/audio_input.py
src/core/audio_convert.py
tests/test_wx_ms14_b3_input.py
```

## 受け入れ条件

* GUIから wav / mp3 / m4a を選択できる
* 既存WAV入力が引き続き動作する
* mp3 / m4a は解析用WAVへ変換されてから波形表示・解析へ渡る
* 入力音声と解析用WAVの区別が内部状態で保持される
* 音声変更時に古い timing plan / Preview / VMD保存可能状態 / 選択状態が無効化される
* 変換失敗時にVMD保存可能状態にならない

---

# MS17-B7: MMD用WAV出力基盤 (完了)

## 目的

専用の「MMD用WAV出力」導線で、MMD用WAVを明示的に保存できるようにする。

MMD用WAVは、MMDで読み込ませるための出力物であり、解析用WAVと役割を分ける。

## In Scope

* MMD用WAV出力仕様の確定
* MMD互換WAV検証
* 専用の「MMD用WAV出力」導線
* 出力ファイル名規則
* 上書き確認
* 不完全ファイル削除
* 保存成功 / 失敗メッセージ
* README / docs 用説明整理
* VMD出力との整合

## Out of Scope

* 音量正規化
* 無音トリム
* フェード処理
* ノイズ除去
* MMDプロジェクトファイル生成
* VMD以外のMMDデータ出力
* 複数WAV出力プリセット

## MMD用WAV仕様の初期候補

```text
container: WAV
codec: PCM signed 16-bit little-endian
sample rate: 44100 Hz
channels: stereo
chunk: RIFF/WAVE -> fmt(size 16) -> data
```

MMD互換性を優先し、実装前に仕様書と照合する。

実装結果:

```text
- MMD用WAVは元音声ファイルから生成する
- 解析用WAVは内部正本として分離する
- mono入力は ch1 を stereo へ複製する
- stereo入力は ch1/ch2 を維持する
- 3ch以上の入力は ch1/ch2 のみを残す
- FFmpeg出力は -bitexact を指定し、LIST等のmetadata chunk混入を避ける
- 実FFmpeg出力で fmt -> data の単純chunk構造と検証通過を確認済み
```

## 想定対象ファイル

```text
src/core/mmd_wav_export.py
src/core/ffmpeg_runner.py
src/core/audio_errors.py
src/gui_wx/app_controller.py
src/gui_wx/main_frame.py
src/gui_wx/ui_state.py
tests/test_ms17_b7_mmd_wav_export.py
tests/test_ms17_b7_mmd_wav_save_dialog.py
tests/test_ms17_b7_mmd_wav_button_state.py
tests/test_ms17_b7_mmd_wav_failure_cleanup.py
tests/test_ms17_b7_mmd_wav_overwrite_confirm.py
```

## 受け入れ条件

* 専用の「MMD用WAV出力」導線からMMD用WAVを出力できる
* MMD用WAVと解析用WAVの役割が分離されている
* MMD用WAVの仕様がdocsに記録されている
* 出力失敗時に不完全ファイルが残らない
* VMD保存成功とWAV保存成功 / 失敗がユーザーに分かる
* VMD出力は引き続きリップモーフキーフレームのみである

確認結果:

```text
- B7関連pytest: 14 passed
- 関連回帰pytest: 25 passed
- 実FFmpeg出力確認: MMD用WAV検証通過
- ユーザー手動テスト: 問題なし
- git diff --check: 空白エラーなし（CRLF警告のみ）
```

---

# MS17-B8: GUI状態・Busy・長時間処理確認・worker結果破棄統合 (完了)

## 目的

音声変換処理が入ることで長時間処理・キャンセル・古いworker結果の問題が増えるため、GUI状態管理とworker結果破棄を統合する。

## In Scope

* 変換中Busy状態
* ffprobe中Busy状態
* 解析用WAV生成中Busy状態
* 300秒確認ダイアログ
* キャンセル要求
* ffmpeg / ffprobe terminate / kill
* Whisperなど即時停止できない処理のlate callback破棄
* 古いworker結果を現在結果として扱わない
* TEXT / 音声 / パラメータ変更時の無効化
* RightPane / Warning / Info 表示との整合

## Out of Scope

* 完全な強制停止保証
* OSプロセス管理の大規模抽象化
* 複数ジョブキュー
* バックグラウンドバッチ処理
* 300秒での強制停止

## 重要仕様

```text
300秒は強制停止ではなく、長時間処理確認の閾値である。
```

```text
ffmpeg / ffprobe は可能なら terminate し、必要な場合のみ kill する。
```

```text
Whisperなど即時停止できない処理は、完了後の late callback を破棄する。
```

## 想定対象ファイル

```text
src/gui_wx/app_controller.py
src/gui_wx/main_frame.py
src/gui_wx/ui_state.py
src/gui_wx/right_pane.py
src/gui_wx/worker_state.py
src/core/ffmpeg_runner.py
src/core/ffprobe_runner.py
tests/test_ms17_b8_busy_state.py
tests/test_ms17_b8_late_worker_result_discard.py
tests/test_ms17_b8_long_processing_confirmation.py
```

## 受け入れ条件

* 変換中・解析中に二重実行できない
* キャンセル要求時にffmpeg / ffprobe終了が試行される
* 300秒確認は強制停止ではなく確認として扱われる
* 古いworker結果でPreview / timing plan / VMD保存可能状態が更新されない
* 音声変更時に古い選択状態が残らない
* GUIが処理失敗後に復旧可能である

確認結果:

```text
- B8追加pytest: 11 passed
- B7関連回帰pytest: 14 passed
- B4/B5 runner関連回帰pytest: 13 passed
- 既存入力導線pytest: 2 passed
- ユーザー手動テスト: 通過
- wx複数テスト同時実行では、表示上 22 passed だがプロセス終了コード 1 となる既存tearDown由来と見られる挙動を確認。B9で必要に応じて整理する。
```

---

# MS17-B9: 統合テスト・docs補正・MS17 closeout

## 目的

MS17全体の統合確認を行い、README / docs / milestone / changelog / packaging関連文書をMS17完了状態へ同期する。

## In Scope

* wav入力確認
* mp3入力確認
* m4a入力確認
* ffprobe失敗確認
* ffmpeg失敗確認
* 入力サイズ上限確認
* 音声長上限確認
* 解析用WAV生成確認
* 波形表示・Preview・VMD保存確認
* MMD用WAV出力確認
* MMDでのWAV読み込み手動確認
* VMDとWAVの同時利用確認
* README更新
* repo_milestone更新
* Version_Control更新
* MS17 Block Breakdown更新
* FFmpeg / third-party license docs更新
* Release Package Manifest更新
* 配布用 `readme_mmdautolip.txt` 更新
* 同梱対象の `pyproject.toml` description同期
* MS18送り項目整理

## Out of Scope

* MS18実装
* 新規音声編集機能
* 母音イベント本格編集
* モデルプロファイル保存
* プリセット保存
* FFmpeg自動ダウンロード

## 確認対象docs

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Version_Control.md
docs/repo_milestone.md
docs/Implementation_Plan/MS17_Block_Breakdown.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/VMD_Output_Specification.md
```

## 受け入れ条件

* MS17-B1〜B8の成果が確認されている
* READMEがエンドユーザー向けにMS17状態へ更新されている
* docsが開発者・Codex向けにMS17状態へ更新されている
* FFmpeg / ffprobe の扱いが明確である
* MIT License本体とFFmpeg等の第三者ライセンスが混同されていない
* wav / mp3 / m4a 入力対応が実装済み範囲として正しく記録されている
* 解析用WAVとMMD用WAVの区別がdocsに記録されている
* MS18送り項目が整理されている
* Qt / PySide6 再導入がない
* MS17 closeoutとしてコミット可能な状態である

確認結果:

```text
- B3〜B8限定テストは表示上 69 passed。
- まとめ実行では既知の wx teardown 由来と見られる終了コード 1 を確認したため、分割実行で終了コード 0 を確認した。
- 非GUI寄り限定テスト: 55 passed
- wx入力導線: 2 passed
- B7ダイアログ/ボタン/上書き確認: 6 passed
- B8状態系: 6 passed
- 既存GUI回帰: 6 passed
- 実FFmpeg / ffprobe version確認済み。
- 実音声からMMD用WAV生成確認済み。
- 生成済みexeの5秒起動スモーク確認済み。
- ユーザー手動テスト: 通過、問題なし。
- 実MMD読み込み確認は未実施のため、リリース前確認へ送る。
- MS17 closeout判定: B. MS17 closeout OK。ただしリリース前確認の残課題あり。
```

---

# 8. MS17のBlock依存関係

```text
B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 → B9
```

ただし、B8のGUI状態・worker結果破棄はB4〜B7の実装中にも影響するため、B8で後追い確認するだけでなく、B4以降の各Blockで最低限の無効化・失敗時復旧を守ること。

## 依存関係の要点

* B1が未完了の場合、B2以降に進まない
* B2でFFmpeg方針が未整理の場合、B5以降に進まない
* B4のffprobe検査が未完了の場合、B6のGUI導線を完成扱いしない
* B5の解析用WAV生成が未完了の場合、mp3 / m4a入力対応を完成扱いしない
* B7のMMD用WAV出力は、B5の解析用WAVとは別責務として扱う
* B9でdocs補正が終わるまで、MS17 closeout扱いしない

# 9. MS17で保持する禁止事項

MS17では以下を行わない。

```text
- Qt / PySide6 を再導入しない
- 旧 src/gui 系を復活させない
- FFmpeg同梱有無を未確定のまま断定しない
- FFmpeg / ffprobe のライセンスと配布条件を軽視しない
- MIT Licenseの本体とFFmpeg等の第三者ライセンスを混同しない
- 音量正規化、無音トリム、自動フェード、自動ノイズ除去を行わない
- 解析用WAVとMMD用WAVを混同しない
- Preview shapeをtiming planの正本にしない
- 古いworker結果を現在結果として扱わない
- 300秒を強制停止として扱わない
- VMD出力にボーン / カメラ / 照明 / IK / 表示制御を追加しない
```

# 10. MS17完了時の期待状態

MS17完了時点で、ユーザー視点では以下が成立していることを目標とする。

```text
- TEXTファイルと音声ファイルを選択できる
- 音声ファイルとして wav / mp3 / m4a を扱える
- 内部で解析用WAVが生成され、波形表示・Preview・VMD生成に使われる
- 専用の「MMD用WAV出力」導線でMMD用WAVも出力できる
- 変換失敗時に原因がある程度分かる
- 長時間処理時に確認が出る
- キャンセルや失敗後にGUIが復旧できる
- READMEに使い方と注意が書かれている
- 配布物に必要なライセンス・NOTICE・第三者ライセンス情報が整理されている
```

# 11. MS17後に残す可能性がある課題

以下はMS17完了後のMS18以降送り候補とする。

```text
- 音声変換詳細設定UI
- 変換キャッシュ管理
- MMD用WAVの複数プリセット
- より詳細なWarning判定
- 母音イベント編集
- Previewクリック選択の本格化
- モデルプロファイル保存
- プリセット保存
- 配布パッケージ自動検証の強化
- FFmpeg自動ダウンロード
```

# 12. 変更履歴

## 2026-05-13 / MS17-B1 完了反映

* `MS17-B1: Repo / MS16 closeout 後状態確認 + MS17開始条件整理` を実施した。
* MS16 の Closeout が正常に完了していることを確認。
* `src/main.py` の古い Qt 関連コメントを削除し、実態と同期させた。

## 2026-06-03 / MS17-B9 closeout反映

* `MS17-B9: 統合テスト・docs補正・MS17 closeout` を実施した。
* README、配布用readme、pyproject、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifest をMS17状態へ同期した。
* 現在配置済み FFmpeg / ffprobe 実体のversionと `--enable-gpl --enable-version3` 構成を記録した。
* B3〜B8限定テストと既存GUI回帰を確認した。
* 生成済みexeの起動スモークとユーザー手動テスト通過を記録した。
* Codex側の実MMD確認とFFmpeg第三者ライセンス通知の最終確定はMS18/リリース前確認へ引き継ぐ。
