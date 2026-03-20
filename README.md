# MMD AutoLip Tool

## Version

Ver 0.3.4.1

## 概要

MMD 向けの自動リップ生成ツールです。  
UTF-8 のテキスト 1 ファイルと PCM WAV 1 ファイルを入力し、母音モーフ（あ/い/う/え/お）の VMD を生成します。

## 現在の主な機能

- テキストから母音列を抽出
- TEXT 読み込み時に、ひらがな化・母音変換を即時実行
- WAV 読み込み時は、基本情報読込と波形プレビュー表示のみ実行
- 「処理実行」ボタン押下時に、Whisper/RMS/タイミング計算を実行
- WAV 解析（長さ、発話区間、波形プレビュー）
- Whisper の時間アンカー（失敗時は均等配分フォールバック）
- 最終母音イベントの区間表現（`time_sec / duration_sec / start_sec / end_sec`）
- RMS 系列による `start_sec / end_sec` の簡易補正
- RMS 系列を使ったイベント別 `peak_value` 算出（`0.0`〜`upper_limit` にクランプ）
- 区間ベース（台形寄り）での VMD モーフキー生成
- 台形モーフの立ち上がり前ゼロ保証（同一フレーム衝突時はゼロを 1 フレーム前へ退避）
- GUI 波形表示と VMD 出力で同一イベント列を共有
- GUI で「モーフ上限値」を指定可能（初期値 `0.5`、小数4桁）
- 上限値変更時は即時再解析せず、次回「処理実行」で反映
- 未解析状態では出力時に暗黙再解析せず、警告して中断
- トップメニュー（File / Run / Help）を追加
- メニュー操作とボタン操作が同じ共通入口メソッドを通る構成へ整理
- Run/Save 系のメニュー状態を既存ガードと整合するよう同期（最小制御）
- File 配下の最近使った TEXT/WAV（各10件）を実装し、履歴から再読込可能
- Run 配下の「再解析」を処理実行と整合する入口へ接続
- View メニュー（30fps縦線/母音ラベル/イベント区間/表示初期化）を実装し、表示フラグと同期
- Help のバージョン情報に `pyopenjtalk` / `whisper` の実環境バージョン表示を追加
- 処理実行中は不定進捗の処理中ダイアログを表示（キャンセルなし）
- 処理実行中は再入防止を行い、二重実行を抑止
- 処理実行中は、読込/再実行/出力/最近使ったファイル/モーフ上限値入力を一時ロック
- 処理終了時は成功/失敗を問わず、処理中ダイアログと一時ロックを解除して通常状態へ復帰
- 出力状態表示は処理開始時に「解析中」へ遷移し、成功時は既存成功表示、失敗時は既存失敗表示へ復帰
- MS7 として、TEXT/WAV 読込前の最小パス検証（空/非存在/ディレクトリ）を導入
- MS7 として、VMD 保存前パス検証（`.vmd` 補完後の最終パス検証、保存先妥当性確認）を導入
- MS7 として、履歴再読込の危険値チェック（空/非存在/ディレクトリ/拡張子不一致）を導入
- MS7 として、想定外例外時も GUI 警告へフォールバックし、状態復帰を崩さない経路を補強
- MS5 として、TEXT/WAV 読込ダイアログの直前ディレクトリ記憶を導入（用途別に分離管理）
- MS5 として、通常読込・履歴再読込の成功時のみ、各保持値を「選択ファイルの親ディレクトリ」へ更新
- MS5 として、保持値が無効（未設定/空/非存在/非ディレクトリ）な場合は警告を増やさずフォールバックで起動
- MS6 として、TEXT/WAV の最近使ったファイル履歴を各10件で保持し、重複時は先頭へ再配置
- MS6 として、履歴再読込失敗時は該当項目のみ除去し、対応メニューを即時更新
- MS6 として、TEXT 履歴系と WAV 履歴系の更新先・再読込導線・メニュー接続を分離して非混線を固定

## 直近更新（2026-03-19）

- 母音イベントを区間ベース（`time_sec / duration_sec / start_sec / end_sec`）へ統一し、VMD台形出力とGUI表示で同一イベント列を再利用
- RMSベースの `peak_value` を導入し、固定 `0.5` ではなくイベント別モーフ値で出力
- 立ち上がり前ゼロ保証（同一フレーム衝突時の `frame-1` 退避）を維持
- GUIに「モーフ上限値」を追加（初期値 `0.5`、`0.0` 未満不可）
- UI起動タイミングを分離し、WAV読込時は軽処理のみ、重処理は「処理実行」押下時のみ実施
- フェーズA 段取り0〜4として、トップメニュー最小構成を導入
- File/Run/Help の QAction を既存共通入口へ配線
- `処理実行` と `VMDを保存` の有効/無効をボタンとメニューで同期
- フェーズB 段取り8で、最近使った TEXT/WAV 履歴（各10件・重複先頭移動・失敗時非更新）を実装
- フェーズB 段取り9で、Run/View/履歴を含む複数入口整合を確認し、最小修正を反映
- Help → バージョン情報に `pyopenjtalk` / `whisper` バージョン表示を追加
- MS4 フェーズ1〜6として、処理中状態フラグ/処理中ダイアログ/再入防止/操作ロック/状態表示遷移を最小差分で接続
- 復帰整合確認として、成功時・失敗時ともに「ダイアログ終了」「busy解除」「状態表示復帰」が成立することを確認
- MS7 フェーズ2〜6として、TEXT/WAV/保存/履歴再読込の失敗経路を点検し、最小防御と状態復帰を補強
- MS7 フェーズ7〜8として、修正範囲を `src/gui/main_window.py` の局所修正に固定し、完了判定観点を最終整理

## 直近更新（2026-03-20）

- MS5 フェーズ2〜8として、`src/gui/main_window.py` に読込ダイアログ用の直前ディレクトリ保持（TEXT/WAV分離）を導入
- `_select_text_file` / `_select_wav_file` で、初期ディレクトリ解決結果を使ってダイアログを起動する導線へ接続
- 通常読込成功時と履歴再読込成功時のみ、保持値を親ディレクトリで更新するよう整理
- 初期ディレクトリ解決で、未設定/空/非存在/非ディレクトリを安全にフォールバックする防御を適用
- MS5 フェーズ9として、確認観点（9-1〜9-5）を整理し、モックベースの最小実行確認で PASS を確認
- MS6 フェーズ1〜8として、履歴追加・履歴メニュー更新・履歴再読込・失敗時除去・更新タイミング・非混線を `src/gui/main_window.py` の局所修正で整理
- MS6 フェーズ9として、確認観点（10件上限/重複先頭移動/再読込導線/壊れた履歴値除去/非混線）をコード読解と最小スモーク確認で整理

## MS7 入出力安全性点検（2026-03-19）

- 対象:
  - TEXT 読込入口
  - WAV 読込入口
  - VMD 保存入口
  - 履歴再読込入口
- 実装方針:
  - GUI 側で事前に弾けるものは最小限で弾く
  - 実書込・下位処理でしか判定できない失敗は既存処理へ委譲する
  - 失敗時に UI 状態と内部状態が半端に残らないよう復帰を統一する
- 完了観点:
  - 不正入力/不正パスでクラッシュせず警告表示に戻る
  - 保存失敗後も再試行可能な状態を維持する
  - 履歴再読込失敗時に該当履歴を除去し、メニュー表示を更新する
  - 想定外例外時でも警告表示にフォールバックし、次操作で破綻しない

## トップメニュー導入状況（フェーズA/B）

- 完了:
  - 段取り0: 既存導線の確認（TEXT/WAV/処理実行/VMD出力）
  - 段取り1: メニュー骨格追加（File / Run / Help）
  - 段取り2: 共通入口化（ボタン/メニュー共通で再利用可能化）
  - 段取り3: 最小構成 QAction の配線
  - 段取り4: 最小の状態整合（Run/Save 系の有効状態同期）
  - 段取り5: 拡張メニュー土台（Recent / 再解析 / View）追加
  - 段取り6: 表示切替の内部フラグ化（波形表示側）
  - 段取り7: 拡張メニュー（Run/View）の配線
  - 段取り8: 最近使った TEXT/WAV 履歴の実装（各10件）
  - 段取り9: 複数入口の整合確認と最小修正（Run/View/履歴連携）
- 未対応（次フェーズ）:
  - 履歴や View 表示設定の永続化（セッション外保持）
  - View 表示仕様の詳細化（目盛り/ラベル/ズーム等）

## 現在の非対応/未実装

- 強制アライメントによる厳密音素境界
- 高度な音響特徴量ベース最適化
- 音量連動の詳細チューニングUI（マッピング調整・プリセット等）

## 開発環境セットアップ（Windows PowerShell）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 実行方法

```powershell
.\.venv\Scripts\python.exe .\src\main.py
```

## テスト実行

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## EXEビルド（PyInstaller）

```powershell
.\build.ps1
```

実行ポリシーでブロックされる場合:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

- ビルド定義: `MMD_AutoLipTool.spec`
- ビルド方式: `onedir`（`dist\MMD_AutoLipTool\` 配下に展開）
- 出力先: `dist\MMD_AutoLipTool\MMD_AutoLipTool.exe`
- クリーンビルド: `.\build.ps1 -Clean`
- 起動スモーク確認付きビルド: `.\build.ps1 -Clean -SmokeLaunch`

### onedir同梱方針（現行）

- Pythonモジュール: `src` 配下で参照する `core / gui / vmd_writer` と依存パッケージ
- GUI関連: `PySide6` 一式
- 描画関連: `matplotlib` backend サブモジュール
- 音声タイミング関連: `whisper` サブモジュールと assets
- 日本語読み変換関連: `pyopenjtalk` のデータ/動的ライブラリ
- tokenizer関連: `tiktoken` / `tiktoken_ext` のデータ/サブモジュール

### onedir動作確認（第1段階）

手動確認（`dist\MMD_AutoLipTool\MMD_AutoLipTool.exe` 起動後）:

1. `TEXT読み込み` で `sample\sample_input.txt` を選択
2. `WAV読み込み` で `sample\sample_voice.wav` を選択
3. `処理実行` を押下
4. `出力` から `.vmd` を保存

補助確認（自動）:

- `.\build.ps1 -Clean -SmokeLaunch` で exe 起動スモークまで実行
- `generate_vmd_from_text_wav` のE2Eで `dist\_smoke\smoke_output.vmd` 生成を確認

## リポジトリ運用ファイル

- `pyproject.toml`: プロジェクト定義（メタデータ・依存・パッケージ探索）
- `.gitignore`: 仮想環境、キャッシュ、ビルド成果物の除外設定
- `build.ps1`: Windows用の標準ビルドコマンド
- `MMD_AutoLipTool.spec`: PyInstallerの固定ビルド設定

## 現状整理（2026-03-19）

1. 現在のフォルダ構成（要点）
    - `src/`, `tests/`, `sample/`, `build/`, `dist/`
    - ルート主要ファイル: `README.md`, `Specification_Prompt_v2.md`, `repo_milestone.md`, `Version_Control.md`, `requirements.txt`, `pyproject.toml`, `build.ps1`, `MMD_AutoLipTool.spec`

2. エントリーポイント候補
    - 本命: `src/main.py`（PySide6 GUI起動）
    - 補助: `src/test_gui.py`（最小GUI動作確認）

3. GUI関連ファイル候補
    - `src/gui/main_window.py`
    - `src/gui/waveform_view.py`
    - `src/gui/__init__.py`

4. 今の状態で不足している主要ファイル（運用観点）
    - `LICENSE`（配布時の明示）
    - `src/app_io/` 系の責務分離（現状は `core` と `gui` に集約）
    - 配布物向けチェックリスト/リリースノート雛形（任意）

5. 最小構成で進める場合の推奨ディレクトリ構成
    - `src/main.py`
    - `src/core/`（処理ロジック）
    - `src/gui/`（UI）
    - `src/vmd_writer/`（VMD出力）
    - `src/app_io/`（I/O責務、段階導入）
    - `tests/`, `sample/`

6. 未実装の内容（現時点）
    - 強制アライメントによる厳密音素境界
    - 高度な音響特徴量ベース最適化
    - 音量連動の詳細チューニングUI（マッピング調整・プリセット等）
