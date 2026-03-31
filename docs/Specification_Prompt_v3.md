# MMD AutoLip Tool 仕様書 v3

## 0. 文書情報

- 文書名: `docs/Specification_Prompt_v3.md`
- 作成日: 2026-03-20
- 最終更新日: 2026-03-31
- 対応リリース: `Ver 0.3.6.3`
- 対象リポジトリ: `MMD_AutoLipTool`
- 旧版: `docs/Specification_Prompt_v2.md`（本書で置き換え）
- 文書方針: v2 の意図を引き継ぎつつ、現行実装・確定済み追加仕様・責務分割方針に合わせて更新する

### 0.1 実装同期注記（2026-03-31 / MS11-6反映）

- 本書は v3 の目標仕様を含むが、2026-03-31 時点でコード反映済みなのは MS8A / MS8B / MS8C / MS8D-2 / MS9 / MS9-2 / MS10 / MS11-1 / MS11-2 / MS11-2_FIX01 / MS11-2_FIX02 / MS11-3 / MS11-4 / MS11-5 / MS11-6 までとする。
- 反映済み（コード実体）:
  - 上部操作列 `OperationPanel`・最下部 `StatusPanel` を含む GUI 再構成
  - `PreviewArea` / `preview_transform.py` による 5 段固定 Preview 表示
  - `PlaybackController` / `ViewSync` による秒ベース再生同期（Play/Stop/共有現在位置）
  - `ViewSync` の共有可視範囲（viewport）同期
  - `waveform_view.py` の可視範囲ベース描画 + 横軸フレーム表記
  - `preview_area.py` の可視範囲ベース描画 + フレーム目盛り
  - Zoom（操作パネルボタン + View メニュー action）と Pan の導線統合
  - TEXT/WAV パスの中間省略表示 + tooltip フルパス
  - 初期ウィンドウサイズ `1270x714`、最小サイズ `720x405`、中央領域 `左3 : 右7` の初期表示調整
  - GUI 主要部の `11pt` 基準フォント、4〜6px 基準の余白、操作ボタンの横長化抑制
  - 操作ボタンの assets アイコン差し替え、主要ボタンの 1 行表示、広い幅での左詰めグループ配置
  - モーフ上限値入力欄の短幅化と、独立した `-` / `+` ボタンへの置換
  - 日本語 / EN の実行中切替と設定永続化（MS10）
  - `writer.py` の最終正規化層による `(morph_name, frame_no)` 重複統合
  - 母音全体の `open_value = max(あ, い, う, え, お)` に基づく開口状態内部表現
  - 前後閉口に挟まれた孤立短開口の検出と 0 化による抑制
  - 母音全体の開口列を変えない範囲に限定した、最小限の個別モーフ短パルス整理
  - `writer.py` における 4点の非対称・単一上辺台形生成
  - `time_sec` を上辺中央基準として扱う frame ベース判定
  - 4 frame 以上での変形台形適用と、4 frame 未満での既存短区間フォールバック維持
  - 正規な MS11-2 由来形状に対する MS11-1 最終正規化側の部分保護
  - FIX01 による、許容外非ゼロ除去と不要ゼロ prune
  - FIX02 による、発話イベント範囲保護を用いたゼロ縮退抑止
  - 同一母音近接イベント群に対する MS11-3 multi-point shape
  - 秒ベース grouping と frame ベース成立判定
  - 谷を非ゼロで維持する multi-point envelope 生成
  - MS11-3 不成立時の MS11-2 / legacy fallback
  - MS11-3 成功 shape に対する envelope 全体保護
  - `peak_value == 0.0` 由来の zero-only trapezoid / zero-only shape を最終出力へ残さない writer 局所修正
  - 正規な short / legacy fallback shape を current normalization flow で不必要に消さない writer 局所保護
  - `pipeline.py` における、RMS 補正後 interval を正本とした peak 評価
  - halo `±0.03 sec` と隣接 interval 端点中点クリップを用いた peak window
  - `load_rms_series()` 失敗時の `upper_limit * 0.25` fallback
  - `global_peak <= 0.0` 時に全 event を `peak_value = 0.0` とする保守的分岐
  - `rms_unavailable / global_peak_zero / no_peak_in_window / below_abs_threshold / below_rel_threshold` の理由分類追跡
  - `PeakValueEvaluation` を維持したまま、event 単位の上位観測レコード `PeakValueObservation` を追加
  - 元 interval / RMS 補正後 interval / peak window / local peak / global peak / fallback / window sample 数をまとめて追跡できる internal observation helper の追加
  - pipeline 系テストにおける、観測値整合の確認拡張
  - `VowelTimingPlan` に optional な `observations` を追加し、main-flow-connected に observation を参照可能化
  - initial timeline と refined timeline を main flow 内で対として追跡し、`timeline` は canonical writer input のまま維持
  - `PipelineResult` へ optional な observation 受け渡しを追加
  - provided timing plan をそのまま再利用する経路では observation を保持し、duration 補完を行う provided timing plan 経路では observation を `None` に落とす方針をテストで明文化
- 未反映（後続対象）:
  - より高度な平滑化と出力仕様全体の再設計
  - GUI / Preview の multi-point 表示対応
  - 実データ観測を踏まえた RMS 定数の必要最小限の再調整
  - MS11-7 として扱う、実データ観測結果の整理と RMS 定数再調整要否の判断整理
- MS8D-2 の改訂要件差分は `docs/MS8D-2_Requirements_and_Spec_Update.md` を参照する。

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
- GUI:
  - PySide6
- 波形確認:
  - 30fps 基準の確認表示
- プレビュー:
  - 波形とは別の Preview Area を持つ
  - 処理実行後の静止表示
  - 再生中の同期表示
- 多言語:
  - 日本語 / EN の実行中切替
  - 次回起動用の設定永続化

### 2.2 非対象（現時点）

- 強制アライメントによる厳密音素境界
- 高度な音響特徴量ベース最適化
- Web機能やネットワーク依存の追加機能
- テキスト直接入力機能
  - v3 時点では対象外
  - Original Text 欄は将来拡張を見越した UI 枠として扱うが、現時点では txt ファイル内容表示に留める

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

## 4. 想定ディレクトリ構成（v3）

```text
.
├─ src/
│  ├─ core/
│  ├─ gui/
│  │  ├─ main_window.py
│  │  ├─ waveform_view.py
│  │  ├─ preview_area.py
│  │  ├─ operation_panel.py
│  │  ├─ status_panel.py
│  │  ├─ playback_controller.py
│  │  ├─ view_sync.py
│  │  ├─ preview_transform.py
│  │  ├─ frame_utils.py           # 未実装の予定ファイル
│  │  ├─ i18n_strings.py
│  │  ├─ settings_store.py        # 未実装の予定ファイル
│  │  └─ layout_helpers.py        # 未実装の予定ファイル / 必要時のみ
│  ├─ vmd_writer/
│  ├─ main.py
│  └─ test_gui.py
├─ tests/
├─ sample/
├─ build/
├─ dist/
├─ README.md
├─ docs/repo_milestone.md
├─ pyproject.toml
├─ requirements.txt
├─ build.ps1
├─ MMD_AutoLipTool.spec
└─ docs/Specification_Prompt_v3.md
````

---

## 5. アーキテクチャ（v3 方針）

### 5.1 エントリーポイント

* 正式入口: `src/main.py`（`main()`）
* 補助入口: `src/test_gui.py`（簡易GUI起動）
* パッケージスクリプト: `mmd-autolip-tool = "main:main"`

### 5.2 モジュール責務

#### 既存責務

* `src/gui/main_window.py`

  * メインウィンドウ
  * ファイル選択、処理実行、出力操作、メニュー操作
  * UI状態遷移とガード（実行可否・保存可否）
  * 画面全体の司令塔
  * 状態判定の正本
  * 各部品への反映指示
  * 言語切替の起点
  * ステータス優先順位判定
  * Preview Area 用データの受け取り・保持・渡し先制御
  * 上限値変更時の再解析待ち状態管理
  * 可変レイアウト全体の統括

* `src/gui/waveform_view.py`

  * 波形表示
  * 30fps縦線、母音ラベル、イベント区間のオーバーレイ制御
  * 波形側の描画責務のみを持つ
  * Preview Area の責務は持たない

* `src/core/text_processing.py`

  * テキスト正規化、かな化、母音列抽出

* `src/core/audio_processing.py`

  * WAV基本解析
  * 波形プレビュー取得
  * RMS系列生成

* `src/core/whisper_timing.py`

  * Whisperによる時間アンカー取得（単語優先、セグメントフォールバック）

* `src/core/pipeline.py`

  * タイミング計画構築
  * Whisperアンカー配分と均等配分フォールバック
  * RMSで区間補正・peak値算出
  * VMD出力呼び出し

* `src/vmd_writer/writer.py`

  * VMDモーフ書き出し
  * 区間ベースのキー生成
  * 4点の非対称・単一上辺台形生成
  * 同一母音近接イベント群の multi-point shape 生成
  * MS11-3 → MS11-2 → legacy fallback
  * 4 frame 未満での既存短区間フォールバック
  * 立ち上がり前ゼロ保証（同一フレーム衝突時 `frame-1` 退避）
  * 最終モーフフレーム正規化層
  * `(morph_name, frame_no)` 単位の重複統合
  * 母音全体開口状態の内部表現構築
  * 孤立短開口の抑制と、最小限の個別モーフ短パルス整理
  * 正規な MS11-2 由来形状に対する部分保護
  * MS11-3 成功 shape に対する envelope 全体保護

#### 実装済みの追加責務（2026-03-22 時点）

* `src/gui/preview_area.py`

  * Preview Area 専用描画ウィジェット
  * 5段固定（あ・い・う・え・お）の描画
  * 整形済み表示データの受け取り
  * 再生カーソル線表示
  * 静止表示 / 再生中表示の更新
  * 重い整形処理は持たない

* `src/gui/operation_panel.py`

  * 上部操作列専用パネル
  * ボタン配置
  * 幅不足時の折り返しレイアウト
  * 表示文言更新
  * tooltip や表示状態の反映
  * `main_window.py` から渡された有効/無効状態の反映
  * 業務判断は持たない

* `src/gui/status_panel.py`

  * 最下部ステータス表示部品
  * 固定高ステータス枠の表示責務
  * 状態表示とメッセージ表示の表示責務
  * 状態種別に応じた軽い整形・見た目切替の受け皿
  * 業務判断や優先順位判定は持たない

* `src/gui/playback_controller.py`

  * 再生状態の専用管理
  * 再生開始・停止・終了
  * 現在位置の保持
  * 現在位置変更通知
  * 再生開始は常にゼロフレームから

* `src/gui/view_sync.py`

  * 波形表示と Preview Area の同期補助
  * 共通カーソル位置の配布
  * 共通フレーム原点の扱い
  * 共有可視範囲（Zoom/Pan）の同期制御

* `src/gui/preview_transform.py`

  * `timeline` から Preview Area 用の整形済み表示データを生成
  * 現行台形ベースの表示用整形
  * MS8 後の変形台形・複数上辺点への拡張受け皿

#### 未実装の予定責務（MS9 / MS10 以降の受け皿）

* `src/gui/frame_utils.py`

  * 秒 ↔ フレームの変換補助
  * カーソル位置計算補助
  * 波形表示と Preview Area で共通利用する補助関数群

* `src/gui/i18n_strings.py`

  * 日本語 UI 文字列の受け皿
  * キーによる GUI 文言取得
  * MS10 の本格多言語化に向けた暫定的な文字列整理先

* `src/gui/settings_store.py`

  * 言語設定の永続化
  * 履歴の永続化
  * 将来の表示設定保存の受け皿
  * ini 等による保存 / 読込 I/O
  * MS9 では全面導入は必須ではないが、テーマ切替や分割比率の受け皿候補として扱う

* `src/gui/layout_helpers.py`

  * 可変レイアウト生成の補助
  * 分割比や共通レイアウト設定の補助
  * 必須ではなく必要時のみ導入

### 5.3 責務分割の原則

* `main_window.py` は判断と統括の正本を持つ
* 個別描画は各描画ウィジェットへ分離する
* 重い整形処理は GUI 部品に持たせない
* 再生状態は専用管理単位へ分離する
* 永続化I/Oは GUI 主窓口に直書きしない
* GUI描画とVMD出力は、可能な限り同じ内部イベント列を再利用する
* GUI用と内部処理用でロジックを二重化しない

---

## 6. 機能仕様（v3時点）

### 6.1 基本導線

* 基本導線は維持する:

  1. TEXT 読込
  2. WAV 読込
  3. 処理実行
  4. 出力
* TEXT読込時:

  * かな化・母音変換を即時実行
* WAV読込時:

  * 軽量解析と波形プレビューのみ実行
* Whisper / RMS / タイミング計画 / Preview 用整形の更新は、処理実行時にまとめて行う
* 出力は `.vmd` 保存
* 未解析状態では出力を中断し、警告する

### 6.2 入力

* TEXT:

  * `UTF-8`（読込失敗時は `Shift_JIS` → `UTF-16` へ自動フォールバック試行）
  * ファイル入力のみ
  * 絶対文字数上限（5000文字）、制御文字異常、規定長超過行などのセキュリティガードを適用
* WAV:

  * 非圧縮 PCM
  * 絶対再生時間上限（15分）のセキュリティガードを適用
  * 非対応フォーマット（PCM以外等）や破損時は明瞭にエラー表示
* 主読込成功時のみ、同一フォルダ・同一 stem の相方ファイルを探索する

  * `.txt` 読込時は `.wav` を探す
  * `.wav` 読込時は `.txt` を探す
  * 対象拡張子は `.txt / .wav`
  * 拡張子の大小文字は区別しない
  * 通常読込で発動する
  * 最近使ったファイルからの再読込でも発動する
  * セッション外復元時には発動しない
  * 反対側の現在パスが設定済みなら自動補完しない
  * 相方未存在時は完全サイレント
  * 相方存在でも読込失敗時は自動補完経路では警告しない
  * 自動補完で成功した相方も履歴更新対象
  * 補完側からさらに連鎖させない
  * 主読込失敗時は補完判定を行わない

### 6.3 出力

* 対象モーフ:

  * `あ / い / う / え / お`
* フレーム基準:

  * `30fps`
* モーフ値:

  * イベント別 `peak_value` を使用
  * 末端書込時に必要最小限の丸め処理
* 立ち上がり前ゼロ保証を維持
* 開始 / 終了のゼロ点は維持する
* 最終書込前に `(morph_name, frame_no)` 単位の重複正規化を行い、非ゼロ優先 / 最大値採用 / 全ゼロ1件化で一意化する
* 母音全体の `open_value = max(あ, い, う, え, お)` を使い、前後閉口に挟まれた孤立短開口のみを後段で抑制する
* 個別モーフ短パルス整理は、除去しても母音全体の開口 / 閉口列が変わらない場合に限る
* 生成フレーム数上限（約12分相当: 22000フレーム）の出力前セキュリティガードを適用
* 同名ファイルへの上書き保存時は前段で確認ダイアログ（Yes/No）を表示する

### 6.4 GUI 全体構成

* 起動時・全体装飾:

  * アプリ起動時にスプラッシュスクリーンを表示する
  * ウィンドウおよびタスクバーに専用のアプリアイコンを適用する
* 画面上部:

  * 操作ボタン列
  * 幅不足時は折り返す
* 操作列直下:

  * モーフ上限値 UI を配置
* 中央領域:

  * 左カラム: TEXT / 変換結果 / ファイル状態
  * 右カラム上段: 波形表示
  * 右カラム下段: Preview Area
* 最下部:

  * 固定高のステータス表示枠
* 左右幅比:

  * 可変
* 波形表示と Preview Area の高さ比:

  * 可変

### 6.5 GUI 詳細

#### 操作パネル

* 上部ボタンは専用パネル部品とする
* 想定ボタン:

  * TEXT 読込
  * WAV 読込
  * 処理実行
  * 出力
  * Play Preview
  * Stop Preview
  * Zoom In
  * Zoom Out
* 判定の正本は `main_window.py`
* パネルは反映のみを担当する

#### TEXT 関連表示

* Original Text:

  * 現時点では txt ファイル内容表示
  * 将来拡張を見越した UI 枠として配置する
* Hiragana
* Vowel
* いずれも日本語 / EN 切替の対象

#### 波形表示

* 波形表示は既存 `WaveformView` を中心に扱う
* 内部データは秒ベースのまま保持する
* 横軸表示はフレーム表記とする
* Preview Area と同じフレーム原点を使う
* 30fps 縦線表示を維持する
* Zoom は WAV 読込前は無効

#### Preview Area

* 波形とは別の新規描画ウィジェット
* 5段固定:

  * あ
  * い
  * う
  * え
  * お
* 存在しない母音も空行表示する
* 母音色は固定色（同色系統の濃淡）
* 処理実行後は静止表示可能
* Play 中は波形表示と同期して動作
* 再生カーソル線は波形表示と共通位置で表示
* Preview Area 自体は上限値UIを直接参照しない
* `timeline` / 整形済み表示データのみを見る

#### ステータス欄

* 既存 `output_status_label` は置換対象とする
* 新ステータス欄は表示専用部品
* 表示対象:

  * TEXT/WAV 読込状態
  * 解析未実行状態
  * 処理完了 / 失敗
  * 短期通知
  * 再生中の現在フレーム表示
* 優先順位判定は `main_window.py` が行う
* ステータス文は短文主義とする

### 6.6 プレビュー再生

* Play は処理実行後のみ有効
* Stop は停止中は無効
* Play 時は波形表示と Preview Area を同期させる
* 再生は常にゼロフレームから開始する
* 現在位置は共有状態として扱う
* 再生位置変更は波形 / Preview Area / ステータス欄へ反映する

### 6.7 多言語対応

* 日本語 / EN の切替をサポートする
* 言語切替は実行中切替とする
* 起動後の切替指示の起点は `main_window.py`
* 各ウィジェットは、指示を受けて自分の文言を更新する
* 文字列定義の正本は1か所に集約する
* 各ウィジェットが独自に翻訳定義を持たない
* 英語表記は簡略化し、ボタン列で収まる短さを優先する
* 切替状態は次回起動用に永続化する

### 6.8 最近使ったファイル

* TEXT/WAV それぞれ最大10件
* 重複時は先頭へ移動
* 読込失敗時は履歴から除外
* v2 時点のセッション内保持から拡張し、永続化対象とする
* 履歴メニューは再構築時に既存 action をクリアし、TEXT/WAV それぞれの履歴配列を表示元にする
* TEXT/WAV の履歴更新先・表示元・再読込導線は分離し、相互に混線しない

### 6.9 パス表示

* 長いパスは中間省略表示する
* ラベル表示は中間省略、tooltip はフルパス表示とする
* 自動補完で読み込まれた相方ファイルも通常読込と同じ見せ方にする
* 主読込 / 自動補完の違いを専用通知で見せ分けない

### 6.10 モーフ上限値

* UI 部品として保持する
* 配置は操作列の直下とする
* 値変更時は既存方針どおり再解析待ち状態へ戻す
* 値変更時に自動再解析はしない
* Preview Area は UI の現在値を直接参照せず、処理結果のみを見る

### 6.11 実行可否 / 有効無効制御

* 処理実行:

  * TEXT・WAV ともに有効入力があるときのみ有効
* 出力:

  * 処理実行完了（タイミング計画あり）のときのみ有効
* Play:

  * 処理実行後のみ有効
* Stop:

  * 再生中のみ有効
* Zoom In / Zoom Out:

  * WAV 読込後のみ有効
  * 通常の Zoom 操作では現在 viewport の中心を保持したまま拡大縮小する
* ボタンとメニューの有効/無効は同期する
* 判定の正本は `main_window.py`

### 6.12 実行中状態の可視化

* 処理中ダイアログを表示する
* 不定進捗または進捗表示を持つ
* 二重実行を防止する
* 終了後の復帰整合を維持する

---

## 7. データ仕様（主要）

### 7.1 タイミングイベント

* 主要属性:

  * `time_sec`
  * `duration_sec`
  * `start_sec`
  * `end_sec`
  * `peak_value`
* GUI描画とVMD出力で同一イベント列を共有する

### 7.2 Preview Area 用整形データ

* `timeline` を元に生成する
* Preview Area 専用の描画向け整形データとする
* `main_window.py` は整形ロジックを持たず、整形済みデータを受け取って Preview Area に渡す
* 現行は台形ベースの表示を前提とする
* MS8 後は以下の拡張を受けられる構造とする:

  * 変形台形
  * rise 後のピークと slope 側ピークの差異
  * 音量変化に同期した上辺変動
  * 同一母音連続時の複数上辺ポイント

### 7.3 フレーム表示

* 内部保持は秒ベースとする
* 表示は 30fps フレームベースとする
* 波形表示と Preview Area は同じフレーム原点を使う

### 7.4 VMD出力

* 対象モーフ: `あ/い/う/え/お`
* フレーム基準: `30fps`
* モーフ値:

  * イベント別 `peak_value` を使用
  * 必要最小限の丸め処理
* 最終書込前に、フレーム整数化後の morph frame 列に対して重複統合と後段正規化を適用する
* `write_dummy_morph_vmd()` は既存の最小形状確認を維持するため、最終正規化をバイパスできる

---

## 8. エラーハンドリング方針

* 入力不備（TEXT/WAV未選択）時は処理開始しない
* TEXTの指定文字コード（UTF-8/Shift_JIS/UTF-16）読込失敗時や、仕様外の制御文字・長大行超過時はエラーとして中断
* WAV解析失敗時（非PCM・破損等）は明瞭に警告し、波形表示をプレースホルダへ戻す
* Whisper失敗時は均等配分フォールバックで継続可能な設計
* 予期しない例外はGUIで通知し、状態更新を明示する
* 自動補完経路では、相方未存在 / 補完側読込失敗を専用警告しない
* 永続化設定読込失敗時は、警告を追加せず安全なデフォルトへフォールバックする

---

## 9. テスト方針

`tests/` に以下観点のユニットテストを配置する:

* text処理
* audio処理
* whisper timing
* pipeline統合
* vmd writer（変形台形・peak・ゼロ保証・重複統合・瞬間開閉抑制・30fps丸め衝突・短区間フォールバック）
* Preview Area 用整形データ
* 秒 ↔ フレーム変換
* 再生状態管理
* 言語切替文言反映
* 設定永続化（言語 / 履歴）

実行コマンド（PowerShell）:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

---

## 10. ビルド・配布方針

* PyInstaller `onedir` を採用
* ビルド定義: `MMD_AutoLipTool.spec`
* 実行スクリプト: `build.ps1`
* 出力先: `dist\MMD_AutoLipTool\MMD_AutoLipTool.exe`
* 言語設定 / 履歴設定の保存先は exe 配布形態に応じて安全な書込先を使う
* アプリアイコン（`.ico`）およびスプラッシュスクリーン画像（`.png`）のアセットをビルドに同梱する

---

## 11. 残課題（v3時点）

### 11.1 機能面

* MS8 モーフスムージング拡張

  * 現行台形ベースから変形台形へ拡張
  * 音量変化との同期
  * 同一母音連続時の上辺複数点対応
* MS11 は MS11-4 まで反映済みとし、残課題は GUI / Preview の multi-point 表示対応、実データ観測を踏まえた RMS 定数の必要最小限の再調整、MS11-5 の観測支援拡張、より高度な平滑化とする
* 再生詳細機能（スクラブ / 手動シーク / クリック移動）の仕様化
* ステータス表示内容の最終文言調整
* 英語表記短文化の最終調整

### 11.2 構造面

* `src/app_io/` の段階導入（必要時）
* `LICENSE` の追加

---

## 12. 実装順の前提整理（v3）

* 既存の基本導線（TEXT読込 → WAV読込 → 処理実行 → 出力）は崩さない
* `main_window.py` に状態判断の正本を残す
* 新規 GUI 部品は、描画責務 / 状態責務 / 永続化責務を分ける
* Preview Area は波形表示と分離した新規描画ウィジェットとする
* Preview Area の重い整形処理は別責務へ出す
* 再生状態は専用管理単位で扱う
* 言語設定と履歴永続化は同系統の設定保存責務で扱う

---

## 13. 更新ルール

* 本仕様書は「現行実装 + 確定済み追加仕様」に追随する一次資料とする
* 実装先行で仕様が変わった場合は、同タスク内で本書を更新する
* 大規模変更時は、先に最小マイルストーンを定義してから拡張する
* GUI の見た目変更だけでなく、責務分割変更がある場合は本書 5章も更新対象とする

---

## 14. MS8B 固定仕様（Preview Area 静止表示）

### 14.1 位置づけと優先順位

- 本章は MS8B で実装した範囲の固定仕様である。
- v3 全体仕様に将来機能記述が含まれる場合でも、MS8B 実装判断では以下を優先する:
  1. MS8B 追加固定指示
  2. MS8B 説明プロンプト
  3. 実装リスト8B
  4. 本書のうち MS8B と矛盾しない部分

### 14.2 MS8B の目的

- Preview Area の静止表示導入を目的とする。
- 処理実行後に `current_timing_plan.timeline` 由来データを使って表示する。
- Preview は右カラム下段に配置し、波形とは別ウィジェットとする。
- 表示は 5 段固定（`あ / い / う / え / お`）とし、MS8B では静止表示のみを扱う。

### 14.3 主対象ファイル（実装対象）

- `src/gui/preview_area.py`（新規追加）
- `src/gui/preview_transform.py`（新規追加）
- `src/gui/main_window.py`（Preview 受け渡し制御の追加対象）

### 14.4 責務分割（MS8B 固定）

- `main_window.py`
  - 持たせる: `current_timing_plan` の受け取り・保持・受け渡し、`timeline` 取得、整形層への受け渡し、整形済み結果の表示側受け渡し、クリア/無効化時の更新判断。
  - 持たせない: Preview 用重整形、Preview 描画、Preview 表示キャッシュ独立管理、再生同期管理。
- `preview_transform.py`
  - 持たせる: `timeline` 受け取り、Preview 中間契約への変換、5段固定向け整形、安全な空データ返却。
  - 持たせない: GUI 描画、`main_window.py` の状態判定、再生管理、`pipeline.py` の既存ロジック変更。
- `preview_area.py`
  - 持たせる: 5段固定表示、整形済みデータ受け取り、静止表示、空状態表示、クリア表示。
  - 持たせない: `timeline` 直接解釈、重い整形、`pipeline.py` 直接依存、状態判定、再生同期、共通カーソル、Zoom、スクラブ。
- `waveform_view.py`
  - 既存の波形表示責務を維持し、Preview 表示責務は持たせない。

### 14.5 Preview 元データと正本

- Preview 元データは `current_timing_plan.timeline` を使う。
- Waveform 用と Preview 用で別々のタイミング計画は作らない。
- `current_timing_plan` を Preview 側の唯一の正本として扱う。

### 14.6 Preview 用中間契約（固定）

- `PreviewData`
  - `rows: list[PreviewRow]`
- `PreviewRow`
  - `vowel: str`
  - `segments: list[PreviewSegment]`
- `PreviewSegment`
  - `start_sec: float`
  - `end_sec: float`
  - `duration_sec: float`
  - `intensity: float`

固定条件:
- `rows` は常に 5 件固定
- 行順は `あ / い / う / え / お`
- 空行も保持する
- 座標系は秒ベース絶対値
- 0..1 正規化座標は使わない
- `duration_sec` は `end_sec - start_sec` と整合
- 強度値は `peak_value` → `value` → `0.0` の順で解釈
- `intensity` の上限は `1.0` 固定
- 空入力 / 不正入力 / データなし時は 5 行固定の空データを返す

### 14.7 復元方針とクリア/無効化方針

- `suppress_warning=True` の silent restore では、Preview 表示キャッシュを独立保存/復元しない。
- 復元後の `current_timing_plan` を正本として Preview を再構成する。
- silent restore は通常の破壊的クリア導線と同一扱いにしない。
- 共通クリア導線を導入する場合でも、silent restore 途中で無条件先行クリアしない。

Preview クリア対象は「失敗時」だけでなく、解析結果無効化時全体とする。少なくとも以下を対象に含める:
- `_reset_text_analysis_state()` 相当
- `_reset_wav_load_state()` 相当
- `_refresh_waveform_morph_labels()` 相当の失敗/不成立分岐
- `_on_morph_upper_limit_changed()` 相当
- `current_timing_plan = None` に戻す既存経路
- 処理失敗時
- 入力不足時
- 再解析待ち状態へ戻す時
- TEXT 再読込時
- WAV 再読込時
- モーフ上限変更時

判断基準は「失敗したか」ではなく「解析結果が有効かどうか」とする。

### 14.8 UI 組み込み方針（MS8B）

- 右カラム下段の既存プレースホルダ領域を Preview Area の組み込み先とする。
- 処理成功後は `current_timing_plan.timeline` → Preview 用整形 → 静止表示の流れとする。
- 未解析 / 失敗 / 入力不足 / 再解析待ち時は空状態/クリア状態へ戻す。
- Preview Area を追加しても既存導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）を崩さない。

### 14.9 MS8B 対象外（実装しない範囲）

- 再生同期
- 再生中カーソル
- 共通カーソル線
- Play / Stop 実機能
- Zoom
- スクラブ
- フレーム単位同期制御
- 30fps 本格表記対応
- 多言語化
- 設定永続化
- 出力品質拡張
- `pipeline.py` の既存タイミング計画ロジック変更
- `WaveformView` の責務変更
- Preview 独立状態キャッシュの導入
- 将来フェーズ向け先回り設計

### 14.10 MS8B 完了条件（実装判定用）

- 右カラム下段に Preview Area が組み込まれる
- Preview Area が 5 段固定で表示される
- 処理実行後に `timeline` 由来整形済みデータが静止表示される
- `main_window.py` が整形責務を持たない
- `preview_transform.py` が整形責務を持つ
- `preview_area.py` が描画責務を持つ
- 未解析時 / 失敗時 / 再解析待ち時に Preview がクリアされる
- 既存導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）が崩れない
- Preview と Waveform が同じ `current_timing_plan.timeline` を元データとして使う
- `suppress_warning=True` 復元時にも Preview 表示整合が崩れない

## MS9 GUI整備（新設）

MS9 では、既存の処理導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）を維持したまま、GUI 全体の視認性・操作理解性・レイアウト柔軟性を向上させる。  
主目的は、モックアップに近いレイアウトと主要外観を導入しつつ、後続の多言語化・設定永続化に耐えられる GUI 基盤を整備することである。

本マイルストーンでは、実装最小化よりもユーザーフレンドリーな画面設計を優先する。  
ただし、処理ロジック正本や既存の出力仕様には踏み込まず、GUI 層・表示層を中心とした整備に限定する。

### 対象概要

- 上部操作ボタン群のアイコン＋文字化
- ボタンの機能グループ単位サイズ統一
- ボタン群のグループ単位折り返し
- 英語表記時の省略記号 `…` 対応
- 余白＋縦区切り線によるボタン群グルーピング
- 左右領域の可変分割導入
- 左側テキスト領域幅の再調整
- セクション見出しと情報構造の明確化
- Preview 行ラベル帯の固定表示化
- 波形表示エリア / Preview エリアの背景・配色見直し
- 波形表示エリアの `Amp` 削除
- ステータスバーの2領域整理
- 分析終了時の Windows 標準通知音追加
- 多言語化を見据えた文言長耐性の整備
- ボタン2段折り返し前提の最小ウィンドウサイズ制約整理

### 後続マイルストーンの繰り下げ

- 従来の MS8E（多言語化・設定永続化）は MS10 として扱う
- 従来の MS8F（出力品質拡張）は MS11 として扱う

詳細要件は別紙 `MS9_GUI_Requirements.md` を正本とする。

### 実装前提の補足（2026-03-22 時点）

- `docs/MS9_GUI_Requirements.md` を MS9 詳細要件の正本として扱う。
- MS9 は GUI 層・表示層の整備を対象とし、処理ロジック正本の変更は行わない。
- MS9 の詳細責務・構造分散・GUI 要件の解釈は `docs/MS9_GUI_Requirements.md` を優先する。
- `OperationPanel` / `StatusPanel` / GUI 分散 / 受け皿整理の詳細判断は、MS9 章だけでなく `docs/MS9_GUI_Requirements.md` を基準に行う。
- `settings_store.py` / `layout_helpers.py` / `frame_utils.py` は、本書では予定ファイルとして扱う。
- `i18n_strings.py` は 2026-03-22 時点で実体があり、GUI 文字列整理の受け皿として利用済み。
- MS9 では上記ファイルの全面導入は必須ではないが、テーマ切替・左右分割比率・文字列管理の受け皿の置き場整理は対象に含む。
## 追記（2026-03-22） / MS9 実装反映と MS9-2 への接続

### MS9 実装反映済み事項

- `main_window.py` は GUI 司令塔として維持しつつ、GUI 構築詳細を `central_panels.py` を含むパネル / コンテナへ分散済み。
- 左情報表示領域は独立パネル化済み。
- 右表示領域は `WaveformView + PreviewArea` を束ねる独立コンテナ化済み。
- 中央領域は `QSplitter` による左右分割へ再編済み。
- `OperationPanel` は 3 グループ構造・アイコン + 文字・折り返し配置へ整理済み。
- `StatusPanel` は状態表示 + メッセージ表示の 2 領域構成へ整理済み。
- 文字列管理 / テーマ状態 / 分割比率の受け皿は GUI 側へ整備済み。
- View メニューのテーマ切替導線、Qt 側テーマ適用、`WaveformView` / `PreviewArea` 側テーマ追従は実装済み。
- 波形表示上の `Amp` は削除済み。
- 分析終了時の Windows 標準通知音は追加済み。

### MS9 追加改修（右表示領域共通の横スクロールバー）

- 右表示領域下部に、`WaveformView` / `PreviewArea` 共通の横スクロールバーを追加済み。
- 本スクロールバーは shared viewport の開始位置を動かす UI であり、再生位置 UI ではない。
- 既存のドラッグ Pan は維持し、ドラッグ操作とスクロールバー操作の双方が shared viewport 更新へ合流する構造を維持する。
- Zoom 時の scrollbar `value / range / pageStep` 追従、未読込時 / 横移動余地なし時の disabled 表示、PreviewArea 側の viewport 全長整合、端部クランプ時の体感改善までを現時点の到達範囲とする。

### MS9-2 実装反映済み事項

- 初期ウィンドウサイズは `1270x714`、最小サイズは `720x405` に調整済み。
- 中央 `QSplitter` は `左3 : 右7` の初期比率となるよう、表示確定後の再適用を含めて安定化済み。
- GUI 主要部へ `11pt` 基準フォントと 4〜6px 基準の余白を反映済み。
- 操作ボタンは assets アイコン差し替え済みで、`TXT読込` / `WAV読込` / `処理実行` は 1 行表示へ整理済み。
- 操作パネルは、広い幅ではボタングループが左詰めで並び、最小幅付近では 2 行左詰めとなるよう調整済み。
- `処理実行` / `VMD保存` ボタンの高さは統一済み。
- モーフ上限値入力欄は短幅固定を維持しつつ、内蔵スピンボタンを廃止して独立した `-` / `+` ボタンへ置換済み。
- モーフ上限値入力まわりは、ダーク / ライト両テーマで視認できる局所スタイルへ調整済み。
