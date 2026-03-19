# MMD AutoLip Tool 仕様書 v2

## 0. 文書情報

- 文書名: `Specification_Prompt_v2.md`
- 作成日: 2026-03-19
- 対応リリース: `Ver 0.3.3.8`
- 対象リポジトリ: `MMD_AutoLipTool`
- 旧版: `_old/Specifications_Prompt_v1.md`（本書で置き換え）
- 文書方針: 旧版の意図を引き継ぎつつ、現行実装と運用実態に合わせて再構成する

---

## 1. 目的

本ツールは、MikuMikuDance（MMD）向けに、`UTF-8` テキスト1ファイルと `PCM WAV` 1ファイルから、母音モーフ（`あ/い/う/え/お`）の VMD を生成する Windows デスクトップユーティリティである。

---

## 2. スコープ

### 2.1 対象

- Windows 11 上で動作する Python 製 GUI アプリ
- 単発利用（1回の入力に対して1回の出力）を想定
- 入力:
  - `TEXT`（UTF-8）
  - `WAV`（非圧縮 PCM）
- 出力:
  - モーフキーフレームのみを含む VMD

### 2.2 非対象（現時点）

- 強制アライメントによる厳密音素境界
- 高度な音響特徴量ベース最適化
- 音量連動の詳細チューニングUI（細かなマッピング調整やプリセット）
- Web機能やネットワーク依存の追加機能

---

## 3. 前提環境

- OS: Windows 11
- Python: 3.11 以上
- GUI: PySide6
- 主な依存:
  - `PySide6`
  - `matplotlib`
  - `numpy`
  - `openai-whisper`
  - `pyopenjtalk`
- 開発環境: ローカル `.venv`
- 配布形式: PyInstaller `onedir`

---

## 4. 現行ディレクトリ構成

```text
.
├─ src/
│  ├─ core/
│  ├─ gui/
│  ├─ vmd_writer/
│  ├─ main.py
│  └─ test_gui.py
├─ tests/
├─ sample/
├─ build/
├─ dist/
├─ README.md
├─ repo_milestone.md
├─ pyproject.toml
├─ requirements.txt
├─ build.ps1
├─ MMD_AutoLipTool.spec
└─ Specification_Prompt_v2.md
```

---

## 5. アーキテクチャ（現行実装準拠）

### 5.1 エントリーポイント

- 正式入口: `src/main.py`（`main()`）
- 補助入口: `src/test_gui.py`（簡易GUI起動）
- パッケージスクリプト: `mmd-autolip-tool = "main:main"`

### 5.2 モジュール責務

- `src/gui/main_window.py`
  - メインウィンドウ
  - ファイル選択、処理実行、出力操作、メニュー操作
  - UI状態遷移とガード（実行可否・保存可否）
- `src/gui/waveform_view.py`
  - 波形表示
  - 30fps縦線、母音ラベル、イベント区間のオーバーレイ制御
- `src/core/text_processing.py`
  - テキスト正規化、かな化、母音列抽出
- `src/core/audio_processing.py`
  - WAV基本解析
  - 波形プレビュー取得
  - RMS系列生成
- `src/core/whisper_timing.py`
  - Whisperによる時間アンカー取得（単語優先、セグメントフォールバック）
- `src/core/pipeline.py`
  - タイミング計画構築
  - Whisperアンカー配分と均等配分フォールバック
  - RMSで区間補正・peak値算出
  - VMD出力呼び出し
- `src/vmd_writer/writer.py`
  - VMDモーフ書き出し
  - 区間ベース（台形寄り）のキー生成
  - 立ち上がり前ゼロ保証（同一フレーム衝突時 `frame-1` 退避）

---

## 6. 機能仕様（v2時点）

### 6.1 入力

- TEXT読込:
  - UTF-8で読込
  - ひらがな変換と母音変換を即時実行
  - プレビュー表示（原文/ひらがな/母音）
- WAV読込:
  - 軽量処理のみ実行（基本解析＋波形プレビュー）
  - 重処理（Whisper/RMS/タイミング）は未実行のまま保持

### 6.2 処理実行

- 「処理実行」操作時に以下を実行:
  - 母音列抽出
  - 発話区間に対するタイミング計画作成
  - Whisperアンカー取得（失敗時は均等配分）
  - RMS系列による区間補正
  - イベント別 `peak_value` 算出（`0.0`～`upper_limit`）

### 6.3 出力

- 「出力」操作で `.vmd` 保存
- 解析未実行状態では出力を中断し警告
- 出力時は、処理実行で構築済みのタイミング計画を利用

### 6.4 GUI

- ボタン:
  - TEXT読み込み
  - WAV読み込み
  - 処理実行
  - 出力
- メニュー:
  - `File`: TEXT/WAV読込, 最近使ったTEXT/WAV, VMD保存, 終了
  - `Run`: 処理実行, 再解析
  - `View`: 30fps縦線, 母音ラベル, イベント区間, 表示初期化
  - `Help`: バージョン情報（`pyopenjtalk` / `whisper` 実環境バージョン表示）
- 追加UI:
  - モーフ上限値（`QDoubleSpinBox`）
  - 初期値 `0.5`、`0.0` 未満不可

### 6.5 状態制御

- 実行可否:
  - TEXT・WAVともに有効入力があるときのみ「処理実行」有効
- 出力可否:
  - 処理実行完了（タイミング計画あり）のときのみ「出力」有効
- ボタンとメニューの有効/無効を同期

### 6.6 最近使ったファイル

- TEXT/WAVそれぞれ最大10件
- 重複時は先頭へ移動
- 読込失敗時は履歴から除外
- 現状はセッション内保持（永続化未実装）

### 6.7 実行中状態の可視化（MS4）

- 処理開始時:
  - 処理中フラグを有効化
  - 出力状態表示を「解析中」へ更新
  - 不定進捗の処理中ダイアログを表示（キャンセルなし）
- 処理中:
  - 処理実行系入口の再入を防止
  - 読込/再実行/出力/最近使ったファイル/モーフ上限値入力を一時無効化
- 処理終了時（成功/失敗共通）:
  - 処理中ダイアログを閉じる
  - 処理中フラグを解除
  - 一時ロックを解除し、通常条件の有効/無効へ復帰
- 状態表示:
  - 成功時は既存の成功表示経路（`_set_ready_status()`）へ復帰
  - 失敗時は既存の警告経路（`_show_warning(..., status=...)`）で失敗表示へ復帰
  - 例外経路でも「解析中」のまま取り残されないよう終了側でフォールバック

---

## 7. データ仕様（主要）

### 7.1 タイミングイベント

- 主要属性:
  - `time_sec`
  - `duration_sec`
  - `start_sec`
  - `end_sec`
  - `peak_value`
- GUI描画とVMD出力で同一イベント列を共有

### 7.2 VMD出力

- 対象モーフ: `あ/い/う/え/お`
- フレーム基準: `30fps`
- モーフ値:
  - イベント別 `peak_value` を使用
  - 末端書込時に必要最小限の丸め処理

---

## 8. エラーハンドリング方針

- 入力不備（TEXT/WAV未選択）時は処理開始しない
- TEXTのUTF-8読込失敗時は警告して中断
- WAV解析失敗時は警告し、波形表示をプレースホルダへ戻す
- Whisper失敗時は均等配分フォールバックで継続可能な設計
- 予期しない例外はGUIで通知し、状態更新を明示する

---

## 9. テスト方針

`tests/` に以下観点のユニットテストを配置済み:

- text処理
- audio処理
- whisper timing
- pipeline統合
- vmd writer（区間・peak・ゼロ保証）

実行コマンド（PowerShell）:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

---

## 10. ビルド・配布方針

- PyInstaller `onedir` を採用
- ビルド定義: `MMD_AutoLipTool.spec`
- 実行スクリプト: `build.ps1`
- 出力先: `dist\MMD_AutoLipTool\MMD_AutoLipTool.exe`

---

## 11. 残課題（v2時点）

### 11.1 機能面

- 読込ダイアログのカレントディレクトリ記憶
- 履歴/表示設定のセッション外永続化
- View表示仕様の詳細化（目盛り/ラベル/ズーム）
- 入出力安全性点検（パス検証、保存系の安全確認）
- モーフスムージング拡張（既存台形出力との比較評価）

### 11.2 構造面

- `src/app_io/` の段階導入（I/O責務分離）
- `LICENSE` の追加

---

## 12. 最小構成での推奨ディレクトリ

```text
src/
├─ main.py
├─ core/        # 処理ロジック
├─ gui/         # UI
├─ vmd_writer/  # VMD出力
└─ app_io/      # I/O責務分離（段階導入）
tests/
sample/
```

---

## 13. 更新ルール

- 本仕様書は「現行実装に追随」する一次資料とする
- 実装先行で仕様が変わった場合は、同タスク内で本書を更新する
- 大規模変更時は、先に最小マイルストーンを定義してから拡張する
