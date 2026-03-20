# MS8A 実装用: 実ファイル配置提案

## 目的

MS8A（GUI再構成基盤）を実装するにあたり、既存導線を崩さず、後続の MS8B〜MS8F を載せやすい形で、実ファイル配置を整理する。

MS8A の中心対象は以下とする。

- `main_window.py` のレイアウト再編
- `operation_panel.py` の新設
- `status_panel.py` の新設

MS8A の目的は、以下の GUI 骨格を安定させること。

- 上部操作列
- 操作列直下のモーフ上限値 UI
- 中央の左カラム / 右カラム構成
- 最下部の固定高ステータス欄

---

## 前提

- すでに提示済みのファイル群は同一リポジトリ内に存在する
- 最小変更を優先する
- 既存導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）は維持する
- `main_window.py` は引き続き全体司令塔とする
- `waveform_view.py` は既存波形表示部品として継続利用する
- MS8A では Preview / 再生 / 多言語 / 設定永続化までは実装対象に含めない

---

## 提案する正規配置

MS8A 時点では、少なくとも以下の配置を正規とする。

```text
.
├─ src/
│  ├─ core/
│  │  ├─ audio_processing.py
│  │  ├─ pipeline.py
│  │  ├─ text_processing.py
│  │  └─ whisper_timing.py
│  ├─ gui/
│  │  ├─ main_window.py
│  │  ├─ waveform_view.py
│  │  ├─ operation_panel.py      # MS8A で新規追加
│  │  └─ status_panel.py         # MS8A で新規追加
│  ├─ vmd_writer/
│  │  └─ writer.py
│  ├─ main.py
│  └─ test_gui.py
├─ tests/
├─ repo_milestone.md
├─ Specification_Prompt_v3.md
└─ Version_Control.md
````

---

## MS8A で新規追加する実ファイル

### 1. `src/gui/operation_panel.py`

役割:

* 上部の操作ボタン列をまとめる専用 GUI 部品
* 表示と有効/無効反映のみを担当する
* 実行可否判定の正本は持たない

MS8A で持たせる範囲:

* TEXT 読込
* WAV 読込
* 処理実行
* VMD 出力
* Play Preview
* Stop Preview
* Zoom In
* Zoom Out

注意:

* MS8A では、Play / Stop / Zoom の内部機能実装は不要
* 先行してボタン枠だけ配置してよい
* 有効/無効の最終判定は `main_window.py` 側で行う

---

### 2. `src/gui/status_panel.py`

役割:

* 最下部の固定高ステータス表示枠の専用 GUI 部品
* 表示専用
* 文言の優先順位判定は持たない

MS8A で持たせる範囲:

* 単一の表示更新 API
* 通常状態文の表示
* 後続マイルストーンで短期通知や再生フレーム表示を受けられる最低限の土台

注意:

* 既存 `output_status_label` は段階的置換対象
* 優先順位判定や状態管理は `main_window.py` に残す

---

## 既存ファイルの配置方針

### 1. `src/gui/main_window.py`

方針:

* 引き続き GUI 全体の司令塔
* 状態判定の正本
* 各部品への反映指示
* 既存の読込 / 処理 / 出力導線を維持

MS8A での扱い:

* レイアウト骨格の再編を担当
* 既存の縦積み構成を分解し、以下へ再配置する

再配置先:

* 上部: `OperationPanel`
* その直下: モーフ上限値 UI
* 中央左: テキスト / 変換結果 / ファイル状態
* 中央右上: `WaveformView`
* 中央右下: まだ空枠または将来用コンテナ
* 最下部: `StatusPanel`

注意:

* `main_window.py` から業務ロジックを大量移設しない
* 既存シグナル接続・処理導線は保持する
* 既存メニューや履歴まわりは `main_window.py` に残してよい

---

### 2. `src/gui/waveform_view.py`

方針:

* 既存ファイルをそのまま GUI 専用部品として継続利用する
* MS8A では大きな責務追加は行わない

MS8A での扱い:

* 新レイアウトの右カラム上段へ配置する
* 波形描画責務以外は追加しない

---

### 3. `src/core/audio_processing.py`

### 4. `src/core/pipeline.py`

### 5. `src/core/text_processing.py`

### 6. `src/core/whisper_timing.py`

### 7. `src/vmd_writer/writer.py`

方針:

* MS8A では配置確認のみ
* 原則として新規分割や責務変更は行わない

注意:

* GUI 再構成が主目的のため、core / writer 層は巻き込まない
* import 修正が必要な場合でも最小限に留める

---

## 追加しないファイル

MS8A では、以下は新規作成しないこと。

* `src/gui/preview_area.py`
* `src/gui/preview_transform.py`
* `src/gui/playback_controller.py`
* `src/gui/view_sync.py`
* `src/gui/frame_utils.py`
* `src/gui/i18n_strings.py`
* `src/gui/settings_store.py`
* `src/gui/layout_helpers.py`

これらは後続マイルストーンの対象であり、MS8A の時点では未追加のままでよい。

---

## 既存リポジトリへの適用ルール

### ケース A: すでに `src/gui` / `src/core` / `src/vmd_writer` 構成で存在する場合

対応:

* 新規追加は `src/gui/operation_panel.py` と `src/gui/status_panel.py` のみ
* 既存ファイル移動は行わない
* `main_window.py` の import だけ必要最小限で更新する

### ケース B: 現在、同名ファイルがリポジトリ直下に存在する場合

対応:

* 正規配置は `src/...` 配下へ寄せる
* ただし、広範囲な移動は import 崩れを起こしやすいため、MS8A 実装と同時に無理な一括移動はしない
* 既存起動導線が root 前提なら、まず現状配置を確認してから移動有無を決める
* 重複ファイル（root と `src/` の二重化）は作らない

---

## Codex への作業指示上の配置ルール

* 既存実ファイルが `src/...` 配下にあるなら、その配置を正とする
* `operation_panel.py` と `status_panel.py` は `src/gui/` 配下へ追加する
* `main_window.py` は `src/gui/` 配下の既存ファイルを修正対象とする
* `waveform_view.py` は `src/gui/` 配下の既存ファイルを参照対象とする
* `core` / `vmd_writer` 側は原則そのままとする
* root と `src/` の二重配置は作らない
* `__init__.py` は、既存リポジトリで必要な場合のみ追加する
* 不明な場合は、まず実在するファイル配置を確認し、その配置に合わせて最小修正で実装する

---

## MS8A 実装時の最低限の到達状態

* `src/gui/operation_panel.py` が追加されている
* `src/gui/status_panel.py` が追加されている
* `src/gui/main_window.py` が新レイアウト骨格を持つ
* `src/gui/waveform_view.py` は右上表示として組み込まれる
* モーフ上限値 UI は操作列直下へ移動している
* 既存 `output_status_label` は新しいステータス部品へ置換される
* TEXT読込 / WAV読込 / 処理実行 / VMD出力の既存導線は維持される

---

## 備考

* この提案は、MS8A の実装に必要な実ファイル配置の整理に限定する
* Preview / 再生 / 多言語 / 永続化の実装詳細は含めない
* 後続マイルストーンを見越しても、MS8A 時点では GUI 骨格の分離だけに留める
