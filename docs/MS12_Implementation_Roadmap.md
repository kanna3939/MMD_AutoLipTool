# MS12 Implementation Roadmap

## 0. 文書目的

本書は、`Ver 0.3.7.1` 時点の repo 現状を前提に、
**MS12 をどの順で、どの責務境界で、どの未確定事項を抱えたまま進めるか**
を整理するための実装ロードマップである。

本書の役割は次のとおり。

- MS12 の実装着手順を固定する
- 各段の主対象ファイルと非対象を明示する
- 既存の MS11 / GUI / packaging との衝突点を先に見える化する
- ユーザー判断が必要になりうる項目を、現時点では問い合わせず「保留課題」として記録する

本書は詳細実装の正本ではなく、
**MS12 全体の進め方を固定するための親ロードマップ**
として扱う。

---

## 1. 基準時点

- Repository Baseline: `Ver 0.3.7.1`
- 現在の主前提:
  - MS11 系は closeout 済み前提
  - MS12 は未着手前提
  - `VMD保存先フォルダの記憶と永続化` を MS12 の最初の着手候補として追加済み
  - 既存の processing responsiveness / splash / packaging は、その後段に配置済み

関連文書:

- `docs/MS11_MS12_Roadmap_and_Scope_Split.md`
- `docs/Specification_Prompt_v3.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

---

## 2. 現在の repo 前提

### 2.1 既存コード上の現在地

- `src/gui/main_window.py`
  - GUI 全体の司令塔
  - 処理実行、保存、状態遷移、設定保存、Preview 更新の正本
- `src/gui/settings_store.py`
  - ini ベースの設定保存 / 読込
  - 言語、テーマ、splitter 比率、ウィンドウサイズ、モーフ値、recent TEXT/WAV を扱う
- `src/main.py`
  - `QApplication` 生成
  - splash 表示
  - settings load
  - `MainWindow` 起動
- `build.ps1` / `MMD_AutoLipTool.spec`
  - PyInstaller `onedir` の build 正本

### 2.2 既にある土台

- TEXT / WAV 読込ダイアログ用の直前ディレクトリ保持は存在する
- 設定永続化の基本導線は存在する
- splash 表示自体は存在する
- busy dialog と二重実行防止は存在する

### 2.3 まだ無いもの

- VMD 保存先フォルダの記憶と永続化
- 重処理を UI スレッドから分離する実装
- splash 上への version 表示
- FFmpeg bundling 契約
- MS12 専用テスト群

---

## 3. MS12 の固定スコープ

MS12 は、次の 5 段で扱う。

1. MS12-1: VMD 保存先フォルダの記憶と永続化
2. MS12-2: processing-time UI responsiveness improvement
3. MS12-3: splash timing improvement
4. MS12-4: splash version display
5. MS12-5: distribution dependency bundling cleanup

MS12 では次を行わない。

- pipeline 観測契約の整理
- writer 出力 shape の再設計
- Preview shape semantics の再設計
- MS11 の same-vowel / observation / closing smoothing 調整

---

## 4. 推奨実装順

### 4.1 MS12-1

#### 目的

VMD 保存ダイアログの初期フォルダを、最後に正常保存した出力先フォルダへ寄せる。

#### 主対象

- `src/gui/main_window.py`
- `src/gui/settings_store.py`
- `tests/test_settings_store.py`
- 必要なら `tests/test_main_window_*`

#### この段でやること

- 保存成功時のみ、VMD 出力先親フォルダを記憶する
- 次回保存ダイアログの初期ディレクトリへ反映する
- settings 永続化へ組み込む
- cancel / save失敗 / path validation failure では更新しない

#### この段でやらないこと

- 保存ファイル名の自動提案変更
- recent VMD file 一覧追加
- 出力履歴 UI 追加
- splash / responsiveness / packaging 変更

#### 完了条件

- 同一セッション内で保存先フォルダが再利用される
- 再起動後も復元される
- 既存の overwrite confirm と save validation が崩れない

---

### 4.2 MS12-2

#### 目的

処理実行中に UI が完全停止して見える状態を減らす。

#### 主対象

- `src/gui/main_window.py`
- 必要なら新規 GUI-side helper module
- 必要なら最小の worker / signal 受け皿

#### この段でやること

- 重処理の実行責務を UI スレッドから分離する
- 処理開始 / 成功 / 失敗 / 復帰を signal ベースで main window へ返す
- 既存の `_is_processing` ガード、操作ロック、status 復帰を維持する
- Preview / waveform / status 更新は UI スレッド側でのみ適用する

#### この段でやらないこと

- pipeline / writer のアルゴリズム変更
- progress の精密化
- キャンセル機能追加
- splash / packaging 変更

#### 完了条件

- 通常の処理実行中でもウィンドウ移動・再描画・ダイアログ表示が極端に止まらない
- 二重実行防止と終了後復帰が崩れない
- 既存の未解析保存禁止や失敗時警告導線が崩れない

---

### 4.3 MS12-3

#### 目的

splash を、起動体感上の待ち時間に対してより早く見せる。

#### 主対象

- `src/main.py`
- 必要なら resource helper の最小変更

#### この段でやること

- splash 表示順を点検する
- 設定読込や `MainWindow` 構築前後の順序を見直す
- 現行の icon 設定や startup language 解決を壊さずに早期表示へ寄せる

#### この段でやらないこと

- splash デザインの全面変更
- version 表示追加
- packaging 変更

#### 完了条件

- splash が main window 構築待ちより前に十分見える
- 起動失敗やリソース未存在時の安全動作が維持される

---

### 4.4 MS12-4

#### 目的

splash に現在 version を表示する。

#### 主対象

- `src/main.py`
- version source 解決経路
- 必要なら splash 描画 helper

#### この段でやること

- version source を 1 か所に寄せる
- splash 上に version 文字列を重ねる
- Help ダイアログ側の version 表示と矛盾しない状態を保つ

#### この段でやらないこと

- version 定数の多重化
- splash 画像アセットの全面差し替え
- packaging 変更

#### 完了条件

- splash に current version が表示される
- 版数ソースの不整合が増えない

---

### 4.5 MS12-5

#### 目的

配布時依存関係の扱いを固定し、必要なら FFmpeg bundling を最小構成で導入する。

#### 主対象

- `build.ps1`
- `MMD_AutoLipTool.spec`
- `README.md`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`
- 必要なら追加の release-side documentation

#### この段でやること

- FFmpeg bundling を採用するか否かを文書化前提で整理する
- 採用時は最小構成の同梱方法を固定する
- 実行時に PATH 前提を持たない解決方法を用意する
- ライセンス / notice を必要範囲だけ更新する

#### この段でやらないこと

- 無関係な外部ツールの同梱
- release artifact の拡大を伴う先回り bundling
- GUI / pipeline 変更

#### 完了条件

- release build の依存解決方針が再現可能になる
- bundling 採用時は、最小構成とライセンス同梱方針が明文化される

---

## 5. 責務境界

### 5.1 `main_window.py`

MS12 で持たせてよい責務:

- VMD save dialog の初期フォルダ決定
- 保存成功後の current setting 更新
- worker 開始 / 終了 signal の受け取り
- busy state と action state の制御

MS12 で持たせない責務:

- pipeline / writer の重ロジック本体
- splash 描画専用ロジック
- packaging 固有ロジック

### 5.2 `settings_store.py`

MS12 で持たせてよい責務:

- `last_vmd_output_dir` の保存 / 読込 / 正規化
- 既存 settings schema への最小追加

MS12 で持たせない責務:

- 保存ダイアログ制御
- business rule 付き保存成功判定

### 5.3 `main.py`

MS12 で持たせてよい責務:

- splash の表示順制御
- version source の起動時解決
- splash finish のタイミング制御

MS12 で持たせない責務:

- settings schema の詳細処理
- GUI 状態遷移本体

### 5.4 build / packaging files

MS12-5 でのみ変更対象とし、それ以前では触らない。

---

## 6. 想定ファイル影響範囲

### 6.1 高確率で触る

- `src/gui/main_window.py`
- `src/gui/settings_store.py`
- `src/main.py`
- `docs/MS11_MS12_Roadmap_and_Scope_Split.md`
- `docs/Specification_Prompt_v3.md`

### 6.2 可能性あり

- `tests/test_settings_store.py`
- `tests/test_main_window_closing_softness.py` に近い GUI テストファイル
- `build.ps1`
- `MMD_AutoLipTool.spec`
- `README.md`

### 6.3 できるだけ触らない

- `src/core/pipeline.py`
- `src/vmd_writer/writer.py`
- `src/gui/preview_transform.py`
- `src/gui/preview_area.py`
- `src/gui/waveform_view.py`

---

## 7. 段ごとのリスク

### MS12-1

- save success 判定前に保存先を更新すると、失敗時に汚染される
- settings schema 追加時に既存 load 互換を壊す可能性がある

### MS12-2

- worker 化で UI 更新を worker 側から触ると Qt スレッド境界を壊す
- 例外復帰導線が二重化すると `_is_processing` が残留する
- playback / preview / status の更新順が崩れる可能性がある

### MS12-3

- splash の早期表示で resource 解決や app icon 設定順を壊す可能性がある
- settings load 失敗時の安全フォールバックと順序が衝突する可能性がある

### MS12-4

- version source を複数箇所で持つと表示不一致が起きる
- splash 描画追加で画像スケーリングや文字視認性が崩れる可能性がある

### MS12-5

- bundling 対象を広げすぎると配布物が肥大化する
- ライセンス / notice 更新漏れのリスクがある
- runtime resolution の検証不足で配布後に起動差異が出る可能性がある

---

## 8. 未確定事項と保留課題

### 8.1 今は未確定だが文書化しておく項目

- `last_vmd_output_dir` を settings のどの section / key 名で持つか
- VMD save dialog の初期ファイル名を空にするか、前回ファイル名まで寄せるか
- responsiveness を `QThread` / `QRunnable` / 別 helper class のどれで実装するか
- worker から返す payload を `VowelTimingPlan` / warning / exception detail のどこまで含めるか
- splash version 表示を画像直描きにするか、別 widget overlay にするか
- FFmpeg bundling を採用するか否か
- bundling 採用時の配布元、同梱ライセンス、exe 隣配置ルール

### 8.2 ユーザー判断が必要になりうるが、今は保留課題として置く項目

- FFmpeg bundling の採否
- splash 上の version 表示位置と視認性優先度
- responsiveness 改修で cancel 機能まで欲しいか
- 保存先記憶を「フォルダのみ」に留めるか、「直近ファイル名」まで広げるか

### 8.3 現時点の推奨仮置き

- 保存先記憶は「フォルダのみ」
- responsiveness は最小 worker 化
- splash version は最小文字重ね
- FFmpeg は MS12-5 まで実装保留

---

## 9. テスト方針

MS12 で追加したい観点:

- 保存先フォルダ記憶の save/load round-trip
- 保存成功時のみ更新されること
- cancel / save failure で更新されないこと
- responsiveness 改修後も二重実行防止が維持されること
- 処理成功 / 失敗後に action state が復帰すること
- splash version source が単一であること
- packaging 採用時の build 再現性

テスト追加の優先順:

1. `settings_store` と `main_window` の保存先記憶
2. responsiveness の guard / 復帰
3. startup / splash の最小検証
4. packaging の手動確認手順文書化

---

## 10. まず最初に着手すべき最小単位

最初の自然な最小単位は **MS12-1: VMD保存先フォルダの記憶と永続化** である。

理由:

- 既存の settings 永続化構造に素直に乗る
- `main_window.py` と `settings_store.py` の局所変更で完結しやすい
- responsiveness / splash / packaging と責務が混ざらない
- MS12 の開始点として review しやすい

次点は **MS12-2: processing-time UI responsiveness improvement** とする。

---

## 11. 要約

MS12 は、

- 保存先記憶
- responsiveness
- splash timing
- splash version
- packaging

の 5 段で進めるのが自然である。

この順序なら、

- settings 永続化の小変更
- UI スレッド分離
- 起動 UX 整理
- 配布整理

と、影響範囲を段階的に広げられる。

現時点では、未確定事項は問い合わせ待ちにせず保留課題として文書化し、
まずは MS12-1 から狭く着手する方針が最も安全である。
