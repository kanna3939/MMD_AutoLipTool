# MMD AutoLip Tool

## Version

Ver 0.3.5.6

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
- 波形表示の横軸をフレーム表記で表示（内部正本は秒ベース維持）
- Preview Area にフレーム目盛りを表示し、波形とフレーム原点を一致
- `ViewSync` の共有可視範囲を使い、波形表示と Preview Area の表示範囲を同期
- Zoom In / Zoom Out を操作パネルと View メニューの両方から実行可能化（WAV 読込後のみ有効）
- 波形表示と Preview Area の Pan 操作で、共通ビューポートを左右移動可能
- TEXT / WAV パス表示を中間省略表示し、tooltip でフルパスを表示
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
- GUIFIX06 として、波形表示（Matplotlib）の描画領域と Preview Area の描画領域（グリッド）の横軸基準を動的に一致し、リサイズや操作後も整合を維持
- GUIFIX06 として、母音プレビューのラベル（あ、い...）を右寄せに変更し、常に表部分に隣接するよう視認性を改善

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

## 直近更新（2026-03-21）

- MS5 フェーズ2〜8として、`src/gui/main_window.py` に読込ダイアログ用の直前ディレクトリ保持（TEXT/WAV分離）を導入
- `_select_text_file` / `_select_wav_file` で、初期ディレクトリ解決結果を使ってダイアログを起動する導線へ接続
- 通常読込成功時と履歴再読込成功時のみ、保持値を親ディレクトリで更新するよう整理
- 初期ディレクトリ解決で、未設定/空/非存在/非ディレクトリを安全にフォールバックする防御を適用
- MS5 フェーズ9として、確認観点（9-1〜9-5）を整理し、モックベースの最小実行確認で PASS を確認
- MS6 フェーズ1〜8として、履歴追加・履歴メニュー更新・履歴再読込・失敗時除去・更新タイミング・非混線を `src/gui/main_window.py` の局所修正で整理
- MS6 フェーズ9として、確認観点（10件上限/重複先頭移動/再読込導線/壊れた履歴値除去/非混線）をコード読解と最小スモーク確認で整理
- MS8A フェーズ1〜10として、GUI再構成基盤を反映（上部操作列 `OperationPanel` 化 / モーフ上限値UIの操作列直下再配置 / 中央2カラム化 / 最下部 `StatusPanel` 化）
- `main_window.py` を司令塔のまま維持し、`OperationPanel` / `StatusPanel` は表示専用の責務で固定
- `_update_action_states()` の判定ロジックは `main_window.py` に維持し、Play/Stop/Zoom は MS8A 時点で無効表示のまま据え置き
- 既存主要導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）と既存安全動作（処理中ダイアログ / 二重実行防止 / 未解析時保存禁止 / モーフ上限値変更後の再解析待ち復帰）を維持
- MS8B フェーズ3〜9として、`PreviewArea`（右カラム下段）・`preview_transform.py`・`main_window.py` 受け渡し/クリア/復元整合導線を反映
- Preview は 5段固定（あ/い/う/え/お）の静止表示として導入し、正本を `current_timing_plan.timeline` に統一
- 解析結果無効化時クリア（失敗時限定ではない）と `suppress_warning=True` 復元時の再構成整合を最小変更で反映
- MS8C フェーズ1〜10として、`PlaybackController` / `ViewSync` を導入し、実 WAV 再生を秒ベース正本で同期する導線を追加
- Play/Stop の有効無効を action state へ統合（Play=処理実行後のみ有効、Stop=再生中のみ有効）
- 再生開始は常に 0.0 秒起点、再生停止/再生終了/解析結果無効化時は共有位置を 0.0 秒へ戻す動作で統一
- `controller -> view_sync -> waveform/preview/status` の経路で共通位置同期を接続し、波形カーソル/Previewカーソル/ステータス表示を同一位置へ反映
- TEXT/WAV 再読込、読込失敗、入力不足、再解析待ち、`suppress_warning=True` 復元を含む既存入口で、再生状態取り残しが起きないよう無効化導線へ集約
- 実装引き継ぎメモを `docs/MS8C_Implementation_Handoff.md` に追加

## 直近更新（2026-03-22 / MS8D-2）

- 共有ビューポート基盤を `view_sync.py` へ拡張し、共有秒位置と独立に可視範囲（開始秒/終了秒）を同期可能化
- `main_window.py` に Zoom/Pan/viewport 初期化の司令塔制御を集約し、WAV 読込成功・失敗・無効化導線で表示範囲リセットを統合
- `waveform_view.py` を可視範囲ベース描画へ拡張し、横軸をフレーム表記（30fps）へ変更
- `preview_area.py` を可視範囲ベース描画へ拡張し、可視範囲クリップ表示とフレーム目盛り描画を追加
- Operation Panel の Zoom ボタンと View メニューの Zoom action を同一導線へ接続し、有効/無効状態を同期
- Pan 操作を導入し、波形表示と Preview Area の共通ビューポートを同期移動可能化（境界クランプあり）
- TEXT/WAV パス表示を中間省略 + tooltip フルパスへ更新
- `pipeline.py` / `writer.py` / `whisper_timing.py` / `preview_transform.py` の責務は拡張せず維持

## 直近更新（2026-03-22 / MS9）

- `main_window.py` の GUI 構築責務を、`central_panels.py` を含むパネル / コンテナ構造へ分散
- 左情報表示領域を独立パネル化し、右表示領域を `WaveformView + PreviewArea` の独立コンテナとして整理
- 中央領域を `QSplitter` ベースへ再編し、初期比率を `左35 : 右65` として扱う構造へ移行
- `OperationPanel` を 3 グループ構造・アイコン + 文字・折り返し配置対応へ整理
- `StatusPanel` を「状態表示 + メッセージ表示」の 2 領域構成へ整理
- `i18n_strings.py` を追加し、主要 GUI 文言の受け皿を整備
- View メニューにテーマ切替導線を追加し、初期テーマをダークとして整理
- Qt 側テーマ適用と、`WaveformView` / `PreviewArea` 側のテーマ追従を追加
- 波形表示上の `Amp` 表示を削除
- 左右分割比率 / テーマ状態の取得・適用受け皿を追加
- 分析終了時の Windows 標準通知音を追加

## 直近更新（2026-03-22 / MS9 追加改修: 右表示領域共通横スクロールバー）

- 右表示領域下部に、`WaveformView` / `PreviewArea` 共通の横スクロールバーを追加
- スクロールバーは shared viewport の開始位置を動かす補助手段として実装し、既存のドラッグ Pan は維持
- Zoom 後も scrollbar の `value / range / pageStep` が shared viewport に追従するよう調整
- WAV 未読込時および横移動余地なし時は、スクロールバーを表示したまま無効化
- `PreviewArea` は母音データ終端ではなく WAV 全長基準で viewport を解釈するよう修正し、末尾側での伸びを防止
- 端部クランプ時は、shared viewport の中心保持を壊さずに scrollbar 表示値を端へ寄せ、体感上の違和感を軽減
- `PreviewArea` の `QRect.contains(QPointF)` 例外を解消

## 直近更新（2026-03-22 / MS9-2）

- 初期ウィンドウサイズを `1270x714`、最小サイズを `720x405` とし、中央領域の初期比率を `左3 : 右7` へ調整
- GUI 主要部へ `11pt` 基準フォントと 4〜6px 基準の余白を反映し、操作パネル・左情報領域・右表示領域の密度を整理
- 操作ボタンは assets アイコンへ差し替え、`TXT読込` / `WAV読込` / `処理実行` を 1 行表示へ整理
- 操作パネルは、広いウィンドウでは各ボタングループが左詰めで並び、最小幅付近では 2 行左詰めになるよう再配置
- `処理実行` / `VMD保存` ボタンの高さを揃え、操作群の見た目を統一
- モーフ上限値入力は短幅固定の `QDoubleSpinBox` を維持しつつ、内蔵スピンボタンを廃止して独立した `-` / `+` ボタンへ置換
- モーフ上限値入力まわりはダーク / ライト両テーマで視認できる局所スタイルへ整理し、既存の値範囲・step・signal 接続は維持

## 直近更新（2026-03-23 / SEC01・SEC02）

- セキュリティおよび安全性向上を目的とする SEC01 / SEC02 の実装完了（Ver 0.3.5.6 同期維持）
- TEXT文字数（5000字）、WAV再生時間（15分）、VMDフレーム数（22000フレーム）の絶対上限制御を追加
- TEXTの異常文字、規定長超過行のエラー検証およびZWJ等を含む絵文字のホワイトリスト例外化を追加
- TEXT読込時の文字コードフォールバック（UTF-8 → Shift_JIS → UTF-16）を追加
- VMD保存時のファイル同名上書き確認ダイアログ制御を追加

## MS8A 完了時点メモ（2026-03-20）

- ※以下は MS8A 完了時点の履歴メモ。

- 実装済み:
  - 上部操作列: `src/gui/operation_panel.py` の `OperationPanel` を `main_window.py` に組み込み
  - モーフ上限値UI: 操作列直下へ再配置（既存ウィジェット再利用）
  - 中央レイアウト: 左右2カラム化（左: テキスト/ファイル状態、右上: `WaveformView`、右下: `PreviewArea`）
  - 最下部ステータス欄: `src/gui/status_panel.py` の `StatusPanel` へ置換
- 未実装（後続マイルストーン対象）:
  - 再生詳細機能（スクラブ/手動シーク/クリック移動）
  - Zoom 機能
  - 多言語化
  - 設定永続化
  - 出力品質拡張（MS8 本体）

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
  - View 表示仕様の微調整（目盛り密度・ラベル可読性・操作ヘルプ等）

## 現在の非対応/未実装

- 強制アライメントによる厳密音素境界
- 高度な音響特徴量ベース最適化
- 音量連動の詳細チューニングUI（マッピング調整・プリセット等）
- 再生詳細機能（スクラブ / 手動シーク / クリック移動）
- 多言語化（日本語/EN 切替）
- 設定永続化

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

## 文書の参照先

- 全体仕様: `docs/Specification_Prompt_v3.md`
- マイルストーン管理: `docs/repo_milestone.md`
- 変更履歴ログ: `docs/Version_Control.md`
- MS9 詳細要件: `docs/MS9_GUI_Requirements.md`

## 現状整理（2026-03-23）

1. 現在のフォルダ構成（要点）
    - `src/`, `tests/`, `sample/`, `build/`, `dist/`, `docs/`, `assets/`
    - 主要文書は `docs/` 配下で管理する

2. エントリーポイント
    - 本命: `src/main.py`（PySide6 GUI起動）
    - 補助: `src/test_gui.py`（最小GUI動作確認）

3. GUI関連の実装中心
    - `src/gui/main_window.py`
    - `src/gui/operation_panel.py`
    - `src/gui/status_panel.py`
    - `src/gui/waveform_view.py`
    - `src/gui/preview_area.py`
    - `src/gui/view_sync.py`
    - `src/gui/playback_controller.py`
    - `src/gui/preview_transform.py`

4. 未実装の予定ファイル
    - `src/gui/frame_utils.py`
    - `src/gui/settings_store.py`
    - `src/gui/layout_helpers.py`
    - `src/gui/i18n_strings.py` は作成済み
    - 上記 3 件は将来導入予定であり、2026-03-22 時点では未作成

5. 今の状態で不足している主要ファイル（運用観点）
    - `LICENSE`（配布時の明示）
    - `src/app_io/` 系の責務分離（現状は `core` と `gui` に集約、必要時に段階導入）
    - 配布物向けチェックリスト/リリースノート雛形（任意）

6. 未実装の内容（現時点）
    - 強制アライメントによる厳密音素境界
    - 高度な音響特徴量ベース最適化
    - 音量連動の詳細チューニングUI（マッピング調整・プリセット等）
    - 多言語化（MS10）
    - 設定永続化（MS10）
    - ※セキュリティ・安全性仕様（SEC01/SEC02）は Ver 0.3.5.6 にて実装済み
