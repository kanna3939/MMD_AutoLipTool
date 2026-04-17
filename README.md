# MMD AutoLip Tool

Windows 向けの MikuMikuDance 用リップモーション生成ツールです。  
UTF-8 のテキストファイル 1 件と PCM WAV ファイル 1 件を読み込み、母音モーフ `あ / い / う / え / お` を使った VMD を生成します。

現在、GUI を wxPython へ移行中です（MS14 B1〜B6 の移行基盤完了時点）。
現在のバージョン: `Ver. 0.4.0.0`（MS14 主系実装完了）

※ このツールはAIコーディングで作成されています。AIコーディング製ツールに不安がある方の使用は推奨しません。

## できること

- TEXT からひらがな列・母音列を生成
- WAV の基本情報読み込み (波形とPreview描画は現在 Placeholder / MS15予定)
- 処理実行時に音声タイミングを解析して母音イベント列を生成
- MMD 用の VMD リップモーションを書き出し
- 波形表示と Preview の同期表示 (MS15にて本格実装予定)
- 処理実行中の二重実行防止 / 分析中止 / 長時間解析警告
- TEXT / WAV の最近使ったファイル履歴
- VMD 保存先フォルダの記憶と設定の保存・復元

## 動作環境

- OS: Windows 11
- Python: 3.11 以上
- GUI: wxPython (旧 PySide6 系は凍結)

開発・ビルドは Windows PowerShell を前提にしています。

## 入力と出力

### 入力

- TEXT: UTF-8 テキストファイル
- WAV: PCM WAV ファイル

### 出力

- VMD: MikuMikuDance 用リップモーションファイル

### 現在の前提

- 1 回の処理で扱う入力は TEXT 1 件、WAV 1 件です
- リップモーフ対象は `あ / い / う / え / お` 固定です
- 生成結果は自動処理による補助出力です。最終的な見え方は MMD 側で確認してください

## 使い方

1. アプリを起動します。
2. `TEXT読み込み` で台詞テキストを選択します。
3. `WAV読み込み` で音声ファイルを選択します。
4. `処理実行` を押して解析を行います。
5. 波形表示と Preview を確認します。
6. 必要であれば `開口維持` と `閉口スムーズ` を調整します。
7. `VMD保存` から `.vmd` ファイルを書き出します。

補足:

- 処理実行前は VMD 保存できません
- 保存時は最後に正常保存したフォルダが初期フォルダとして再利用されます
- 処理中は操作の一部がロックされます

## 実行方法

仮想環境を作成して依存関係をインストールします。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

アプリを起動します。

```powershell
.\.venv\Scripts\python.exe .\src\main.py
```

## ビルド方法

PyInstaller の `onedir` 構成で Windows 実行ファイルを作成します。

### 事前準備

公式配布ビルド `FFmpeg v8.1` の `bin` 内容を、リポジトリ直下の `FFmpeg\bin\` に手動配置してください。

最低限、次の実行ファイルが必要です。

- `FFmpeg\bin\ffmpeg.exe`
- `FFmpeg\bin\ffprobe.exe`

### ビルド実行

```powershell
.\build.ps1
```

クリーンビルド:

```powershell
.\build.ps1 -Clean
```

起動スモーク確認付きビルド:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

### ビルド出力

- ビルド定義: `MMD_AutoLipTool.spec`
- 出力形式: `onedir`
- 出力先: `dist\MMD_AutoLipTool\MMD_AutoLipTool.exe`
- FFmpeg 配置先: `dist\MMD_AutoLipTool\FFmpeg\`

## テスト

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

または必要なテストだけを個別に実行できます。

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

## 配布とライセンス

このリポジトリのソースコードは [MIT License](LICENSE) で提供します。

配布時は、少なくとも次のファイルを同梱してください。

- [LICENSE](LICENSE)
- [NOTICE](NOTICE)
- [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)

FFmpeg を含むサードパーティライブラリの概要と配布時の確認先は [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) を参照してください。  
平易な免責と配布時注意事項は [NOTICE](NOTICE) を参照してください。

## 免責

本ソフトウェアは `AS IS` で提供されます。  
作者は、本ソフトウェアの使用または使用不能から生じる損害について責任を負いません。  
重要な制作データに使う場合は、生成結果の確認とバックアップを行ってください。

## リポジトリ内の主なファイル

- `src/main.py`: アプリ起動エントリーポイント
- `build.ps1`: Windows 向けビルドスクリプト
- `MMD_AutoLipTool.spec`: PyInstaller 設定
- `FFmpeg\bin\`: 手動配置する FFmpeg v8.1 の `bin` 内容
- `docs/`: 仕様・マイルストーン・変更履歴文書

## 開発状況

本 README はエンドユーザー向けの案内を優先しています。  
実装マイルストーン、詳細仕様、開発ログは `docs/` 配下の文書を参照してください。

- `docs/Specification_Prompt_v3.md`
- `docs/MS12_Implementation_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
