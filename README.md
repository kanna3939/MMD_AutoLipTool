# MMD AutoLip Tool

## Version

Ver 0.3.5.0

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

## 直近更新（2026-03-19）

- 母音イベントを区間ベース（`time_sec / duration_sec / start_sec / end_sec`）へ統一し、VMD台形出力とGUI表示で同一イベント列を再利用
- RMSベースの `peak_value` を導入し、固定 `0.5` ではなくイベント別モーフ値で出力
- 立ち上がり前ゼロ保証（同一フレーム衝突時の `frame-1` 退避）を維持
- GUIに「モーフ上限値」を追加（初期値 `0.5`、`0.0` 未満不可）
- UI起動タイミングを分離し、WAV読込時は軽処理のみ、重処理は「処理実行」押下時のみ実施

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

- ビルド定義: `MMD_AutoLipTool.spec`
- 出力先: `dist\`（`MMD_AutoLipTool.exe` または `MMD_AutoLipTool\`）
- クリーンビルド: `.\build.ps1 -Clean`
- 現時点（2026-03-19）のビルド定義は `onedir` 未対応（次タスクで対応予定）

## リポジトリ運用ファイル

- `pyproject.toml`: プロジェクト定義（メタデータ・依存・パッケージ探索）
- `.gitignore`: 仮想環境、キャッシュ、ビルド成果物の除外設定
- `build.ps1`: Windows用の標準ビルドコマンド
- `MMD_AutoLipTool.spec`: PyInstallerの固定ビルド設定
