# MS16 and Beyond Milestone Map for Codex

> [!WARNING]
> **Legacy / Historical Document**
> 本書はMS16以降の旧計画・履歴参照用である。MS20以降の番号と計画は [MS20 and Beyond Roadmap](MS20_and_Beyond_Roadmap.md) と [MS20 and Beyond Index](MS20_and_Beyond_Index.md) を使用する。本書の旧MS番号と完了記録は置換しない。

> [!IMPORTANT]
> **AI Coding Assistant Directives (for Codex):**
> 本ドキュメントや `repo_milestone.md` などの巨大ドキュメントを解析する前に、まず [MS17_and_Beyond_Index.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/MS17_and_Beyond_Index.md) を最優先で読み込んでください。必要な情報がそちらにある場合は、不要な全行読み込み（トークンの浪費）を避けてください。

## 1. 文書情報

- 文書名: `MS16 and Beyond Milestone Map for Codex`
- 推奨ファイル名: `docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象系列: `Ver 0.4.x`
- 対象範囲: `MS16` 以降の上位マイルストーン方針
- 主対象読者: `Codex`
- 記述言語: 日本語
- 文書種別: 上位マイルストーンマップ
- 作成日: 2026-05-01
- 更新方針:
  - 本書は MS16 以降の上位方針を整理する文書である。
  - 個別実装時には、本書を参照しつつ、別途 `MSxx-Bx_Implementation_Plan.md` を作成する。
  - 実装済み / 予定 / 検討課題 / 非対象を混同しない。
  - MS16 では、wxPython 主系への一本化を明確にし、Qt / PySide6 系依存を完全排除する。

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` における **MS16以降の開発方針とマイルストーン構成**を固定するための上位文書である。

MS15 までで、wxPython 主系における波形表示、Preview、再生、Viewport、Theme / State 統合は closeout 済みである。

MS16以降では、以下の方向へ段階的に進む。

- Qt / PySide6 系依存を完全排除し、wxPython 主系へ一本化する
- Preview の表現を、現在のリボン型表示から変形台形表示へ戻す
- 将来の母音単位編集に必要な GUI / データ契約の土台を作る
- 将来拡張を見据えた右ペイン型の情報タブ UI を MS16 時点で確保する
- wav / mp3 / m4a 入力と MMD 用 WAV 出力へ対応する
- 音声のみ入力と ASR 抽象化へ対応する
- 歌唱・楽曲利用は品質保証対象外としつつ、下書き生成として使える余地を残す
- 連続同音母音・長音処理などの品質改善を行う
- 母音イベント単位の軽微編集、発音単位スロープ調整へ段階的に進む
- 認識テキスト / ひらがな / 母音列の確認・編集導線を整備する
- 生成前 / 保存前の出力診断レポートと Warning Panel を整備する
- プリセット、モデル別プロファイル、セッション保存、MMD持ち込み用パッケージ出力を段階的に導入する
- 英語・他ASR・多言語対応は後段の設計課題として扱う
- 最終的に配布・ライセンス・ビルド・Defender対策を closeout する

本書は、個別マイルストーンの詳細実装計画ではない。  
個別実装時には、本書を上位方針として参照し、別途 `MSxx-Bx_Implementation_Plan.md` を作成する。

---

## 3. 前提環境

### 3.1 開発環境

- OS: Windows 11
- CPU: Intel Core i5-9600K
- Memory: 16GB
- Memory clock: 2.4GHz DIMM
- IDE: Codex
- Coding AI: Codex
- Python: 既存 repo の要件に従う
- 主な利用者:
  - Windows ユーザー
  - MMD ユーザー
  - Python / GitHub / AI 開発に詳しくない個人ユーザーも含む

### 3.2 Codex 利用上の注意

本プロジェクトでは、実装・調査・ドキュメント整備の作業を **Codex** に渡す。

注意:

- プロンプトの宛先は Codex
- Coding AI は Codex を対象とする
- 実装前に必ず repo 状態を確認する
- 実装を行う場合と、内容把握のみの場合を明確に分ける
- 変更後は、確認したファイル、変更したファイル、実行したテスト、残課題を報告する

---

## 4. 現在の到達点

### 4.1 MS16 までの完了範囲

MS16 は closeout 済みである。

MS16までに、wxPython 主系で以下が成立している。

- Qt / PySide6 系依存の完全排除
- wxPython への完全移行と RightPane 基盤の実装
- Preview 変形台形表示の復元とデータ契約の固定
- 母音イベント選択基盤の導入
- TEXT 読込
- WAV 読込
- 解析実行
- VMD保存
- recent files
- settings save / load
- busy / cancel / timeout warning / late callback discard
- 波形表示
- Preview表示
- WAV再生
- 再生位置同期
- Zoom
- Viewport
- Auto-follow
- Theme / UiState 統合

### 4.2 MS16後に残る主要課題

MS16 closeout後、次の課題が残っている。

- MS17-B6にて wav / mp3 / m4a 入力導線は対応済み
- 音声のみ入力には未対応
- ASRバックエンドは Whisper 前提が強く、将来のモデルサイズ選択や他ASR接続の抽象化が必要
- 歌唱・楽曲音声の扱いが仕様として十分に整理されていない
- 連続同音母音・長音処理は将来課題
- 母音イベント単位のGUI編集は未実装
- 発音単位の個別スロープ調整は未実装
- 認識テキスト / ひらがな / 母音列の編集導線は未整理
- 出力診断レポート / Warning Panel は未実装
- プリセット、モデル別プロファイル、セッション保存は未実装
- 英語・多言語対応は設計未着手
- リリース配布物、ビルド形式、ライセンス同梱、Defender対策は最終 closeout が必要

---

## 5. MS16以降の全体方針

MS16以降は、以下の順で進める。

| MS | 名称 | 主目的 |
| ---: | --- | --- |
| MS16 | wx一本化 / Qt・PySide6排除 + Preview変形台形表示復元とGUI拡張基盤 | 依存を整理し、リボン表示を修正し、将来の情報ペイン・編集基盤を作る |
| MS17 | wav/mp3/m4a対応 + MMD用WAV出力 | 入力形式を拡張し、MMD持ち込み用WAVを出力する |
| MS18 | 音声のみ入力対応 + ASR抽象化 | TEXTなし運用とASR差し替え基盤を作る |
| MS19 | 長尺・歌唱利用UX / Info・Warning・診断整理 | 歌唱・楽曲利用の扱い、安全上限、診断表示を整理する |
| MS20 | 連続同音母音・長音処理 + プリセット基盤 | 日本語リップ生成品質を改善し、生成設定プリセットを導入する |
| MS21 | 母音イベント単位の軽微編集 | Preview上で小さな補正を可能にする |
| MS22 | 発音単位スロープ / 個別調整拡張 + セッション保存 | イベント単位カーブ制御と作業再開性を強化する |
| MS23 | 英語・他ASR・多言語対応の設計 | 将来拡張の調査・設計を行う |
| MS24 | リリース配布 closeout | 配布物・ライセンス・ビルド・Defender対策を整える |

---

## 6. 依存ライブラリ方針

### 6.1 基本方針

MS16〜MS22 の範囲では、原則として新規の外部ライブラリを追加しない。

現行の主要依存のうち、今後も使うものは以下とする。

- `wxPython`
- `matplotlib`
- `numpy`
- `openai-whisper`
- `pyopenjtalk`
- `PyInstaller`
- FFmpeg 実行ファイル

MS16で排除するもの:

- `PySide6`
- `PySide6_Addons`
- `PySide6_Essentials`
- `shiboken6`
- Qt / PySide6 に依存する旧 GUI 実装
- Qt backend 前提の matplotlib 利用
- PyInstaller 出力に混入する Qt 系 DLL / resource

### 6.2 新規ライブラリを原則追加しない理由

- Windows個人ユーザー向けツールとして、導入・配布を軽く保つため
- ライセンス確認対象を増やさないため
- PyInstaller配布時の同梱物を複雑化させないため
- Python + ASR + GUI の時点で既に処理負荷があるため
- MMD本体やDCCツールの代替へ寄せないため

### 6.3 追加しない方がよい候補

以下は、現時点では追加しない。

- `pydub`
  - FFmpegを直接呼べば足りるため不要
- `librosa`
  - 音楽解析には便利だが、依存が重く今回の主目的には過剰
- forced aligner 系ライブラリ
  - Windows配布、ライセンス、実装負荷、検証負荷が大きい
- PMX / MMDモデル読み込み系
  - 本ツールの責務外
- 3D描画系
  - PyOpenGL / pyglet / moderngl 等は不要
- DAW / 波形編集系
  - 本ツールの責務外
- 外部ASR SDK
  - MS23 の調査前に追加しない
- schema validation 系ライブラリ
  - 初期は自前バリデーションで十分

### 6.4 将来検討に留めるもの

以下は MS23 以降の調査対象とし、現時点では導入しない。

- 他ASR backend
- 英語G2P / 発音辞書
- 高精度アライメント補助
- 歌唱専用ASR / alignment 系
- 外部クラウドASR連携

---

## 7. MS16: wx一本化 / Qt・PySide6排除 + Preview変形台形表示復元とGUI拡張基盤

### 7.1 目的

MS16では、以下を同時に行う。

1. Qt / PySide6 系依存を完全排除し、wxPython 主系へ一本化する。
2. 現在の wx 版 Preview を、旧Qt/PySide版に存在した変形台形表示へ戻す。
3. 将来の Info / Warning / 選択イベント / プリセット / モデルプロファイルに備えた GUI 拡張基盤を整える。
4. 将来の母音イベント選択・軽微編集に必要な shape metadata / selection metadata を整える。

MS16 は、単なる Preview 表示補修ではなく、**依存整理・GUI土台・将来編集基盤をまとめて整えるマイルストーン**である。

### 7.2 Qt / PySide6 排除方針

MS16では、Qt / PySide6 系を完全に排除する。

理由:

- ライセンス確認・配布条件が複雑になるため
- 最終的な主系は wxPython であり、Qt / PySide6 を残す必要がないため
- PyInstaller配布物に Qt DLL 等が混入すると、配布サイズ・ライセンス説明・誤検知リスクが増えるため
- 旧 GUI が残ると、Codex の実装時に誤参照する可能性があるため

### 7.3 Qt / PySide6 排除の対象

MS16で確認・修正する対象は以下である。

```text
pyproject.toml:
  - PySide6 を dependencies から削除する
  - setuptools package include から旧 gui パッケージを外す

requirements.txt:
  - PySide6 を削除する
  - PySide6_Addons を削除する
  - PySide6_Essentials を削除する
  - shiboken6 を削除する

source tree:
  - src/gui/ 旧Qt系コードの扱いを決める
    - 削除
    - archiveへ移動
    - repoには残すが配布・import対象から外す
  - import PySide6 が残っていないか確認する
  - Qt backend 前提の matplotlib 設定が残っていないか確認する

build:
  - MMD_AutoLipTool.spec に PySide6 / Qt 系収集が残っていないか確認する
  - build.ps1 の出力物に Qt 関連ファイルが混入していないか確認する
  - PyInstaller 出力に PySide6 系 DLL / resource が混入しないことを確認する

tests:
  - PySide6 前提のテストが残っていないか確認する
  - wxPython 主系のテストへ寄せる
````

### 7.4 旧 `src/gui/` の扱い

MS16では、旧Qt/PySide版の `src/gui/` をどう扱うかを明確にする。

推奨方針:

```text
旧Qt/PySide版コードは、実行対象・配布対象・import対象から外す。
必要な表示仕様やロジックだけを wx側へ移植する。
```

選択肢:

| 方針 | 内容 | 推奨度 |
| -- | ------------------------------- | --- |
| A | `src/gui/` を削除し、必要な知見は docs に移す | 高 |
| B | `docs/archive/` 等へ参考資料として移す | 中 |
| C | repo内に残すが package include から外す | 低 |
| D | そのまま残す | 非推奨 |

MS16では、Codex に誤参照させないため、A または B を推奨する。

ただし、旧Qt版 Preview の変形台形表示ロジックに参考価値がある場合、必要な範囲を読んでから、仕様化・移植・削除の順で進める。

### 7.5 GUI Layout Policy

MS16 では、以下のレイアウト方針を基本とする。

```text
上部:
  ファイル読込 / 解析 / 保存 / 再生 / Zoom / プリセット選択

左:
  入力情報
  TEXT / ひらがな / 母音列の概要

中央:
  波形表示
  Preview変形台形表示

右:
  情報系タブペイン
    - Info
    - Warning
    - 選択イベント
    - プリセット
    - モデルプロファイル

下部:
  ステータス / 処理状況
```

右ペインは、MMD / DCC 系ツールにおける情報・設定・選択対象詳細の配置慣習に合わせる。

将来、診断情報、Warning、選択母音イベント情報、プリセット、モデルプロファイルが増えても、主要な波形 / Preview 領域を大きく作り直さずに拡張できる構成とする。

### 7.6 参照モックアップ

MS16 GUI の参照モックアップ画像は以下に配置済みである。

```text
.assets\Mockup\MMA_AutoLipTool_Mockup_M16.png
```

Codex は MS16 GUI 関連作業を行う際、この画像を必ず参照すること。

ただし、モックアップは最終ピクセル一致を求めるものではない。
目的は、以下の構造・配置・責務を共有することである。

* 上部ツールバー
* 左ペインの入力情報
* 中央上部の波形表示
* 中央下部のリッププレビュー
* 右ペインの情報タブ
* 下部ステータスバー
* 波形表示とリッププレビューの時間軸同期
* Preview の変形台形表示
* 将来拡張を見据えた GUI の安定構造

### 7.7 MS16時点の右ペイン扱い

#### Info

* 最初のタブ名は `Info` とする
* 解析結果、基本情報、現在位置、選択中イベント情報の概要を表示できる場所とする
* 本格的な出力診断レポートは MS19 以降

#### Warning

* Warning 表示用の枠を用意する
* MS16時点では placeholder または最小警告表示でよい
* 本格的な Warning 判定は MS19 以降

#### 選択イベント

* 選択中の母音イベント情報を表示するための枠を用意する
* MS16では選択対象情報を表示できる下地まで
* 本格的な編集は MS21 以降

#### プリセット

* プリセット情報表示用の枠を用意する
* MS16では枠のみ、または現在値表示まで
* プリセット編集本体は MS20 以降

#### モデルプロファイル

* モデル別プロファイル表示用の枠を用意する
* MS16では枠のみ、または将来予定表示まで
* モデル別プロファイル本体は MS22 以降

### 7.8 In Scope

* Qt / PySide6 系依存の完全排除
* 旧Qt/PySide版 GUI コードの扱い整理
* `pyproject.toml` / `requirements.txt` / package include の依存整理
* PyInstaller 出力から Qt / PySide6 系が混入しないことの確認
* 現在の `preview_transform` / `preview_panel` / `writer` の形状契約調査
* リボン表示を、変形台形・三角形・多点エンベロープ形状表示へ戻す
* 波形表示とリッププレビューの横軸・時間軸・再生カーソルを揃える
* Preview と波形の縦ガイド線が一致するようにする
* `start_zero`
* `top`
* `hold`
* `slope_mid`
* `end_zero`
* `valley`
* `shape_kind`
* `control_points`
* `source_event_index`
* `frame_range`
* `value_range`
* 将来の hit-test / selection 用 metadata の整備
* Zoom / Viewport / playback cursor との整合維持
* 選択イベント情報表示、またはテスト用 accessor の最小整備
* Preview と writer の shape 解釈の差分確認
* 右ペイン型の情報タブ UI の枠を確保する
* Info / Warning / 選択イベント / プリセット / モデルプロファイル用の view helper を用意する
* GUIの基本構成を、ベータ版リリース後も大きく変えずに済むよう整える

### 7.9 Out of Scope

* mp3対応
* 音声のみ入力
* ASR抽象化
* 外部ASR連携
* マウスドラッグによる編集
* 母音イベント補正値の保存
* VMD読み戻し編集
* DAW的タイムライン編集
* MMD表情キーフレーム編集の再実装
* 連続同音母音・長音処理の品質改善本体
* Warning判定本体
* 出力診断レポート本体
* プリセット編集本体
* モデルプロファイル保存本体
* Undo / Redo
* セッション保存

### 7.10 ひらがな編集の扱い

MS16時点では、メイン画面にひらがな全文編集 UI を常設しない。

メイン画面には以下を置く。

* 原文TEXTの概要表示
* ひらがな概要表示
* 母音列概要表示
* 将来の編集ダイアログ起動ボタン、または導線

長文のひらがな入力・修正は、将来的にポップアップウィンドウで行う。

理由:

* メイン画面の責務を、確認・可視化・情報表示に保つため
* 左ペインを長文編集UIで圧迫しないため
* 音声のみ入力やASR結果確認時に、集中的な編集作業を別ウィンドウで扱いやすくするため

将来の編集フローは以下を想定する。

```text
原文テキスト
  ↓
自動変換ひらがな
  ↓
ユーザー修正ひらがな
  ↓
母音列再生成
  ↓
Preview / Info / Warning 更新
```

### 7.11 推奨ブロック分割

#### MS16-B1: Repo / Dependency / Preview Shape Contract 現状調査

* 実装は行わない
* repo 状態を確認する
* Qt / PySide6 依存の残存箇所を洗い出す
* 旧Qt/PySide版 GUI コードの扱いを提案する
* 現在のリボン表示生成箇所を確認する
* `preview_transform` と `preview_panel` の責務を把握する
* writer 側の shape / morph frame 契約を確認する
* 旧Qt/PySide版表示との違いを整理する
* 将来の GUI 右ペイン構成に必要な view helper を洗い出す

#### MS16-B2: Qt / PySide6 Removal

* `pyproject.toml` から PySide6 を削除する
* `requirements.txt` から PySide6 系を削除する
* package include から旧 `gui` パッケージを外す
* 旧Qt/PySideコードの削除または archive 化を行う
* import 残存を確認する
* build / spec / PyInstaller 出力に Qt 系が混入しないことを確認する
* README / docs の Qt / PySide6 関連記述を更新する

#### MS16-B3: GUI Layout Foundation

* 上部 / 左 / 中央 / 右 / 下部の基本レイアウトを整える
* 右ペインに `Info` / `Warning` / `選択イベント` / `プリセット` / `モデルプロファイル` タブを用意する
* 各タブには placeholder または最小表示を置く
* 後続MSで情報を流し込める view helper を用意する
* 既存操作導線を壊さない

#### MS16-B4: 変形台形 Preview 表示復元

* リボン表示を変形台形 / 三角形 / エンベロープ表示へ戻す
* 編集機能は入れない
* 波形表示と Preview の時間軸・再生カーソルを揃える
* Zoom / Viewport / playback cursor と整合させる

#### MS16-B5: Preview Shape Data Contract 固定

* `control_points`
* `shape_kind`
* `source_event_index`
* `frame_range`
* `value_range`
* hit-test 用 metadata
* Preview と writer の形状解釈差を縮める

#### MS16-B6: 母音イベント選択の下地

* Preview 上の描画図形と母音イベントを対応づける
* 選択状態を内部保持できるようにする
* 選択中イベントの情報表示、またはテスト用 accessor を用意する
* 実編集はまだ行わない

#### MS16-B7: 統合整理 / closeout

* MS16-B1〜B6 の統合確認
* PySide6 / Qt 系が依存・import・配布物から排除されていることを確認する
* MS17に進める状態か確認する
* README / docs / Version_Control / repo_milestone を更新する

### 7.12 MS16の完了条件

* Qt / PySide6 系依存が `pyproject.toml` / `requirements.txt` から削除されている
* 旧Qt/PySide GUI が配布・import対象から外れている
* PyInstaller 出力に PySide6 / Qt 系ファイルが混入していない
* wxPython 主系のみでアプリが起動する
* wx版 Preview がリボン型表示ではなく、変形台形 / 三角形 / エンベロープ形状として表示される
* 波形表示と Preview の時間軸・再生カーソルが揃っている
* Preview の形状が VMD 出力の概念と大きく矛盾しない
* `source_event_index` 等により、描画図形と母音イベントの対応が取れる
* 将来の母音イベント選択・軽微編集に進める下地がある
* 右ペインに Info / Warning / 選択イベント / プリセット / モデルプロファイルの枠がある
* 既存の波形表示、再生、Zoom、Viewport、Auto-follow が壊れていない
* ベータ版リリース後に GUI 構成を大きく変えずに機能追加できる土台がある

---

## 8. MS17: wav/mp3/m4a対応 + MMD用WAV出力

### 8.1 目的

wav / mp3 / m4a 音源を入力として受け付け、解析用WAVを介して既存の処理フローへ接続する。
さらに、MMD で読み込むための WAV を専用導線から出力できるようにする。

MS17では、後段の MMD持ち込み用パッケージ出力の下地も意識する。

### 8.2 In Scope

* wav / mp3 / m4a ファイル選択導線
* FFmpeg による入力音声 → 解析用WAV変換
* 変換後 WAV を既存 WAV 処理フローへ接続
* MMD用WAVの保存先ルール定義
* 一時WAVとユーザー保存WAVの区別
* 15分音声尺上限の維持
* 生成モーフ数上限の維持
* 音声入力時のエラー文言整理
* README / docs への wav / mp3 / m4a 対応範囲反映
* 将来の MMD持ち込み用パッケージ出力に必要な出力パス整理

### 8.3 Out of Scope

* 音声のみ入力
* 歌詞自動生成
* 歌唱品質保証
* ASRバックエンド切替
* 母音生成品質改善
* VMD writer の大規模変更
* 本格的なパッケージ出力
* セッション保存
* 新規Python音声処理ライブラリ導入

### 8.4 ライブラリ方針

MS17では、mp3処理のために `pydub` 等の新規Pythonライブラリは追加しない。

FFmpeg 実行ファイルを `subprocess` 等で直接呼び出し、WAV変換を行う。

理由:

* 依存を増やさないため
* FFmpeg は既に配布設計上の対象であるため
* 余計なライセンス確認対象を増やさないため

### 8.5 完了条件

* wav / mp3 / m4a を選択できる
* 入力音声から解析用 WAV を生成できる
* 生成した WAV を既存処理に渡せる
* VMD 出力まで既存導線で完了できる
* MMD 用 WAV がユーザーに分かる場所へ保存される
* 15分超の音声は拒否される
* モーフ数上限超過時は VMD 保存を中止する
* 後続の持ち込み用パッケージ出力へ進めるパス整理ができている

---

## 9. MS18: 音声のみ入力対応 + ASR抽象化

### 9.1 目的

TEXT を用意しなくても、音声から文字起こしを生成し、リップモーション作成の下書きに使えるようにする。

同時に、Whisper 固定ではなく、将来的なモデルサイズ選択や他ASR接続に備えた抽象化を行う。

### 9.2 In Scope

* 音声のみ入力モード
* Whisper Small による文字起こし
* 文字起こし結果の GUI 表示
* ユーザーが認識テキストを確認・修正できる導線
* ひらがな変換結果の確認
* ひらがな編集ポップアップの設計または初期実装
* 確定テキスト / 確定ひらがなから既存の母音化へ接続
* ASR結果を共通形式へ正規化
* `AsrResult` / `AsrSegment` 契約の定義
* `WhisperAsrBackend` を初期バックエンドとして実装
* `model_name` を内部的に設定可能にする
* pipeline が Whisper 固有型へ直接依存しないようにする
* メイン画面では概要表示、詳細編集はポップアップで行う方針の整理

### 9.3 推奨 ASR 契約

```text
AsrSegment:
  start_sec
  end_sec
  text
  confidence optional

AsrResult:
  backend_name
  model_name
  language
  full_text
  segments
  warning
```

### 9.4 Out of Scope

* 外部ASRの実装
* クラウド送信
* 歌唱品質保証
* word-level / phoneme-level alignment 必須化
* 複数話者分離
* 英語発音変換
* 本格的なテキストエディタ機能
* 母音列の手動直接編集
* Whisper 以外のASRライブラリ導入

### 9.5 ライブラリ方針

MS18では、既存の `openai-whisper` と `pyopenjtalk` を使用する。
他ASR backend や外部ASR SDKは導入しない。

### 9.6 完了条件

* 音声のみ入力で文字起こしが生成される
* 文字起こし結果をユーザーが確認できる
* 必要に応じて認識テキストまたはひらがなを修正できる導線がある
* 確定テキスト / ひらがなから既存のリップ生成処理へ進める
* ASR結果が共通データ形式に正規化される
* 将来のモデルサイズ選択・他ASR接続を妨げない構成になっている

---

## 10. MS19: 長尺・歌唱利用UX / Info・Warning・診断整理

### 10.1 目的

MMDユーザーが楽曲・歌唱音声を使う可能性を考慮しつつ、品質保証範囲を明確にする。

歌唱・楽曲音声を正式サポート対象にはしないが、ボーカルが明瞭な場合は下書き生成として使える余地を残す。

また、MS16で確保した右ペインを活用し、Info / Warning / 出力診断レポートの実装を進める。

### 10.2 In Scope

* 15分音声尺上限の仕様明文化
* モーフ数上限の仕様明文化
* 長尺音声読み込み時の注意文言
* 歌唱・楽曲音声は品質保証対象外であることの README / UI 明記
* ボーカルが明瞭な場合はタイミング下書きとして利用できる場合がある、という説明
* Whisper失敗時や認識不良時の fallback 表示整理
* 処理時間が長くなる場合の警告
* サポート対象 / 条件付き利用 / 非対象の文書分離
* Info タブの情報表示強化
* Warning Panel の本実装
* 生成前 / 保存前の出力診断レポート
* VMD保存前に、モーフ数・最大フレーム・fallback有無などを確認できる診断情報表示
* 診断結果を必要に応じて `report.txt` 形式で出力できる下地

### 10.3 出力診断レポートに含める情報

```text
入力情報:
  - TEXT / 音声ファイル / 解析用WAV パス
  - 音声尺
  - 発話区間
  - サンプルレート

解析情報:
  - Whisper 使用有無
  - ASR backend / model
  - anchor 数
  - fallback 有無
  - timing source

生成情報:
  - 母音数
  - 生成予定モーフ数
  - 最大フレーム番号
  - モーフ数上限への接近度

警告:
  - 長尺
  - 歌唱・楽曲の可能性
  - 認識結果不足
  - TEXT と音声長の不一致
  - モーフ数上限接近
```

### 10.4 Out of Scope

* ボーカル抽出
* 歌唱専用アルゴリズム
* 高精度な歌詞同期
* 外部ASR連携
* DAW的編集機能
* VMD出力前の厳密な差分比較
* 音楽解析ライブラリ導入

### 10.5 推奨文言

```text
歌唱・楽曲音声は正式な品質保証対象外です。
ただし、ボーカルが明瞭な音声では、発話・歌唱タイミングの下書きとして利用できる場合があります。
生成結果は必ず MMD 側で確認・調整してください。
```

### 10.6 完了条件

* 歌唱・楽曲音声の扱いが README / docs / GUI で一貫している
* 品質保証対象外であることが明確
* 入力自体は安全上限内で許可される
* 15分上限とモーフ数上限が別の安全制限として説明されている
* Info / Warning / 診断表示が右ペイン上で機能している
* VMD保存前に、危険な出力や注意点をユーザーが確認できる

---

## 11. MS20: 連続同音母音・長音処理 + プリセット基盤

### 11.1 目的

`ああ`、`いい`、`あー` のような、現在の処理では不自然になりやすい箇所を改善する。

同時に、ユーザーが用途に応じて生成傾向を選べるように、生成設定プリセットの基盤を導入する。

### 11.2 In Scope

* 連続同音母音の検出
* 同音母音間に軽い戻し・谷・閉口を入れる設計
* 長音区間の検出
* 長音時の口形維持 / 自然減衰の方針決定
* Preview と writer の出力整合確認
* MS16で整備した変形台形表示への反映
* テストケース追加
* 生成設定プリセットの導入
* プリセット保存形式の決定
* 標準プリセットの用意
* プリセットを右ペインまたは上部プリセット選択から参照できるようにする

### 11.3 生成設定プリセット案

プリセットは `MMD_AutoLipTool.ini` とは分離し、専用の JSON または INI として扱う。

推奨は JSON である。
理由は、将来以下のような階層構造を持たせやすいためである。

```json
{
  "name": "標準台詞",
  "morph_upper_limit": 0.5,
  "closing_hold_frames": 0,
  "closing_softness_frames": 2,
  "long_vowel_mode": "hold",
  "same_vowel_bridge_strength": 0.5
}
```

初期段階では、既存 GUI パラメータ中心でよい。

### 11.4 Out of Scope

* GUIでの手動編集
* 発音単位の個別スロープ編集
* 英語対応
* 歌唱専用処理
* writer 全面再設計
* モデル別プロファイル本体
* セッション保存
* 外部 schema validation ライブラリ導入

### 11.5 推奨ブロック分割

#### MS20-B1: 連続同音母音・長音の現状調査とテスト固定

* 現行挙動を確認する
* 不自然になりやすいケースをテスト化する
* 実装はまだ行わない

#### MS20-B2: 連続同音母音の再発声表現

* 同じ母音が連続する場合の軽い戻し・谷・再発声表現を導入する

#### MS20-B3: 長音検出と持続 / 減衰表現

* 長音区間を検出し、口形維持または自然減衰を表現する

#### MS20-B4: 生成設定プリセット基盤

* プリセット形式を決める
* 標準プリセットを用意する
* 現在のパラメータへ反映する

#### MS20-B5: Preview / writer 整合確認

* Preview と VMD 出力の形状が矛盾しないか確認する

#### MS20-B6: closeout

* 文書更新
* テスト確認
* 次段への引継ぎ整理

### 11.6 完了条件

* 連続同音母音の不自然な無変化・急変が軽減されている
* 長音区間の口形維持または減衰方針が実装されている
* Preview と VMD 出力の意味が一致している
* 既存の通常台詞処理を壊していない
* 生成設定プリセットを選択・適用できる
* プリセット保存形式が後続拡張に耐える

---

## 12. MS21: 母音イベント単位の軽微編集

### 12.1 目的

MS16で整備した Preview shape / selection metadata を使い、母音イベント単位の小さな補正を可能にする。

この段階で、元分析結果を壊さずにユーザー編集を重ねるための **調整レイヤー** と **Undo / Redo** を導入する。

### 12.2 In Scope

* Preview 上で母音イベントを選択
* 選択イベントの情報表示
* 選択イベントの開口値補正
* 開始 / 終了の小幅なフレーム補正
* 開口維持の小幅補正
* 閉口スムーズの小幅補正
* 補正内容を event-level adjustment として保持
* 補正後 Preview を再描画
* 補正後 VMD 出力へ反映
* raw analysis result と user adjustment layer の分離
* Undo / Redo の導入
* 編集操作履歴の最小実装

### 12.3 調整レイヤー方針

VMDキーフレームを直接編集しない。
自動生成イベントに対する補正値として保持する。

推奨データ流れ:

```text
raw analysis result
  ↓
base timing plan
  ↓
user adjustment layer
  ↓
preview shape
  ↓
writer output
```

推奨概念:

```text
event_index
vowel
time_offset_frames
value_scale
hold_delta_frames
softness_delta_frames
enabled
```

元分析結果は破壊しない。
ユーザー操作は補正レイヤーとして重ねる。

場合によっては、元分析結果を一時的またはセッション内に保持する。

### 12.4 Undo / Redo 対象

対象:

* 母音イベント補正
* プリセット適用
* パラメータ変更
* テキスト / ひらがな編集の確定操作

非対象:

* ファイル読み込み
* ASR再実行そのもの
* VMD保存
* MMD側の編集

### 12.5 Out of Scope

* ドラッグで任意キーフレーム編集
* VMD読み戻し編集
* 複数イベント一括編集
* MMD表情編集機能の再実装
* 完全自由なカーブエディタ
* Undo / Redo 用外部ライブラリ導入

### 12.6 完了条件

* Preview 上で母音イベントを選択できる
* 選択イベントの情報を確認できる
* 小さな補正を行える
* 補正結果が Preview に反映される
* 補正結果が VMD 出力に反映される
* raw VMD 直接編集に依存していない
* 元分析結果とユーザー補正が分離されている
* Undo / Redo が基本的な編集操作に対して機能する

---

## 13. MS22: 発音単位スロープ / 個別調整拡張 + セッション保存

### 13.1 目的

MS21の軽微編集を拡張し、発音イベントごとのスロープ・ホールド・柔らかさをより細かく制御できるようにする。

同時に、繰り返し作業を楽にするため、セッション保存ファイルとモデル別プロファイルの基盤を導入する。

### 13.2 In Scope

* イベント単位 slope / hold / softness metadata の正式化
* adjustment と writer shape の契約整理
* Preview 上で個別カーブを確認
* 複数 control point を持つ envelope への対応整理
* グローバル設定と個別設定の優先順位を定義
* 再解析時に補正を維持するか破棄するかの方針決定
* セッション保存ファイルの導入
* モデル別プロファイルの導入
* プリセットとモデルプロファイルの関係整理

### 13.3 セッション保存ファイル

セッション保存ファイルは、MMDモーションそのものではなく、AutoLipTool側の作業状態を保存する。

推奨拡張子例:

```text
.autolip
```

保存対象候補:

```text
- 入力ファイルパス
- 変換済みWAVパス
- ASR結果
- 確定テキスト
- ひらがな
- 母音列
- timing plan
- 元分析結果
- ユーザー補正レイヤー
- 使用プリセット
- モデルプロファイル
- Warning / report 情報
- Preview viewport
```

重要方針:

* 元分析結果を壊さず保存する
* ユーザー補正は adjustment layer として保存する
* 再解析時の補正維持・破棄方針を明確にする

### 13.4 モデル別プロファイル

MMDモデルごとに口の開き方は異なる。
ただし、PMX読み込みや3D表示は行わない。

モデル別プロファイルは、数値設定の再利用を目的とする。

保存対象候補:

```text
profile_name
morph_upper_limit
closing_hold_frames
closing_softness_frames
default_preset
notes
```

初期段階では、PMXパスやモデルファイル解析は扱わない。
ユーザー定義の「モデルA向け」「口が大きいモデル向け」程度のプロファイルでよい。

### 13.5 Out of Scope

* DAW的タイムライン編集
* 完全自由なカーブエディタ
* 英語対応
* 外部ASR実装
* MMD表情タイムラインの再実装
* PMX読み込み
* 3Dプレビュー
* セッション保存用DBライブラリ導入
* モデル解析ライブラリ導入

### 13.6 注意点

ここでは、補正情報をどこへ持たせるかが重要である。

候補:

* timeline point
* observations
* writer metadata
* event-level adjustment layer

実装前に設計レビューを行い、責務境界を固定すること。

### 13.7 完了条件

* イベント単位のスロープ・ホールド・柔らかさを表現できる
* Preview と writer が同じ補正契約を参照できる
* グローバル設定と個別設定の優先順位が定義されている
* 再解析時の補正維持・破棄方針が明確である
* セッション保存と再読込が成立する
* モデル別プロファイルを保存・再利用できる

---

## 14. MS23: 英語・他ASR・多言語対応の設計

### 14.1 目的

英語音声・英語テキスト、将来的な他ASR連携、多言語対応の入口を設計する。

MS23は、実装よりも調査・設計を優先する。

### 14.2 In Scope

* 英語入力の扱い方針決定
* 英語の発音を日本語5母音へ近似する設計
* Whisper model size selection の正式設定化
* `small`
* `medium`
* `turbo`
* `large`
* 他ASR候補の調査
* 外部ASR利用時のプライバシー / APIキー / ライセンス整理
* ASR backend capability matrix 作成
* 日本語 / 英語混在時の扱い検討
* 必要になり得る外部ライブラリ候補の比較

### 14.3 ASR 方針

標準ASRはローカル Whisper Small とする。

理由:

* 既存実装との互換性が高い
* Windows個人ユーザーでも比較的扱いやすい
* 中程度の精度と処理負荷のバランスがよい

将来的には以下のモデルサイズ選択を検討する。

```text
small:
  標準・軽量

medium:
  精度優先・低速

turbo:
  高速高精度候補・環境依存

large:
  高精度・非常に重い
```

上位モデルを標準にはしない。
ユーザーが明示的に選択する高負荷オプションとして扱う。

他ASR接続は後段の設計・調査課題とする。

外部ASRを使う場合は、以下を必ず確認する。

* オフラインで動くか
* APIキーが必要か
* 音声データを外部送信するか
* 商用・配布ライセンス上問題ないか
* 個人制作ユーザーに説明できるか
* タイムスタンプ粒度が十分か
* 日本語台詞・歌唱にどの程度強いか
* Windows配布に組み込めるか

### 14.4 Out of Scope

* いきなり完全な英語リップ対応を実装すること
* 外部クラウドASRを標準にすること
* ライセンス不明な辞書・音素ライブラリ導入
* 多言語一括対応
* 歌唱品質保証
* 外部ASRの本実装

### 14.5 推奨位置づけ

MS23は実装マイルストーンではなく、まず **設計・調査マイルストーン**として開始する。

### 14.6 完了条件

* 英語対応の実装方針が決まっている
* 他ASR候補の比較表がある
* 外部ASRを使う場合のプライバシー・ライセンス注意点が整理されている
* Whisperモデルサイズ選択のUI / 設定方針が決まっている
* MS24以降で実装するか、将来課題として残すか判断できる
* 新規ライブラリを導入する場合の判断基準が整理されている

---

## 15. MS24: リリース配布 closeout

### 15.1 目的

公開配布に向けて、ビルド形式、同梱物、ライセンス、README、GitHub Releases 文面、Windows Defender 対策を整える。

同時に、MS17以降で下地を作った MMD持ち込み用パッケージ出力、診断レポート、ライセンス同梱の最終整理を行う。

### 15.2 In Scope

* onefile / onedir 方針の最終整理
* `build.ps1` と `MMD_AutoLipTool.spec` の整合
* README のビルド出力説明更新
* `LICENSE`
* `NOTICE`
* `THIRD_PARTY_LICENSES.md`
* FFmpeg 同梱時の upstream license texts 整理
* 配布 ZIP 構成の決定
* GitHub Releases 用説明文作成
* Windows Defender 誤検知を減らすための配布手順整理
* 初回起動・導入手順の明確化
* MMD持ち込み用パッケージ出力の最終整理
* `report.txt` 等の診断レポート出力整理
* PySide6 / Qt 系が配布物に混入していないことの最終確認

### 15.3 MMD持ち込み用パッケージ出力

MMD側に持ち込むファイルを分かりやすくまとめる。

例:

```text
output/
  sample_lip.vmd
  sample_for_mmd.wav
  sample_report.txt
```

将来的には、セッション保存ファイルも含める可能性がある。

```text
output/
  sample_lip.vmd
  sample_for_mmd.wav
  sample.autolip
  sample_report.txt
```

これは MMD本体の責務を侵食せず、MMDに持ち込む前の整理を助ける機能である。

### 15.4 Out of Scope

* 新機能追加
* 解析品質改善
* GUI大改修
* 多言語対応
* ASR追加実装
* MMDプロジェクト管理
* MMD側ファイル構成の管理
* Qt / PySide6 の再導入

### 15.5 完了条件

* 配布形式が確定している
* ビルド手順と README が一致している
* ライセンス同梱物が整理されている
* FFmpeg を含むサードパーティ配布条件が文書化されている
* GitHub Releases に載せる説明文がある
* Windows Defender 誤検知を減らすための配布方針が整理されている
* MMD持ち込み用パッケージ出力の内容が明確である
* 診断レポートと配布物の関係が整理されている
* PySide6 / Qt 系ファイルが配布物に含まれていない

---

## 16. 採用する追加機能方針

以下は、MS16以降で採用する追加機能方針である。

### 16.1 出力診断レポート

採用する。

目的:

* VMD保存前に、生成結果が安全か確認できるようにする
* 長尺・歌唱・fallback・モーフ数上限接近などをユーザーへ明示する

主な実装タイミング:

* MS19

### 16.2 生成設定プリセット

採用する。

目的:

* ユーザーが数値を直接調整しなくても、生成傾向を選べるようにする
* MMDモデルや用途に応じた設定再利用を容易にする

主な実装タイミング:

* MS20

### 16.3 セッション保存ファイル

採用する。

目的:

* 作業途中の状態を保存し、再開できるようにする
* 調整レイヤーやASR結果を保持し、繰り返し作業を楽にする

主な実装タイミング:

* MS22

### 16.4 調整レイヤー

採用する。

目的:

* 元分析結果を壊さずにユーザー補正を重ねる
* Undo / Redo やセッション保存と整合する編集基盤を作る

主な実装タイミング:

* MS21

### 16.5 Undo / Redo

採用する。

目的:

* 母音イベント編集やプリセット適用後に、安全に戻せるようにする

主な実装タイミング:

* MS21

### 16.6 MMD持ち込み用パッケージ出力

採用する。

目的:

* VMD、MMD用WAV、診断レポート等を分かりやすくまとめる
* mp3 → WAV 変換出力時のユーザービリティを上げる

主な実装タイミング:

* MS17で下地
* MS24で整理

### 16.7 認識テキスト / ひらがな / 母音列の確認・編集

採用する。

目的:

* 音声のみ入力やASR結果をユーザーが確認できるようにする
* ひらがな部分は編集可能にする余地を残す
* 母音列は原則機械生成だが、表示確認できるようにする

主な実装タイミング:

* MS18

### 16.8 Warning Panel

採用する。

目的:

* ステータスバーだけでは不足する警告を一覧表示する
* 長尺・歌唱・fallback・認識不足・モーフ数上限接近などを明示する

主な実装タイミング:

* MS19

### 16.9 モデル別プロファイル

採用する。

目的:

* MMDモデルごとの口の開き方に合わせて数値設定を再利用する
* PMXや3D表示を扱わず、プロファイル設定のみ保存する

主な実装タイミング:

* MS22

---

## 17. 明確に非採用とする機能

以下は、少なくとも Ver0.4 系の主対象にしない。

### 17.1 VMD出力前の簡易比較

非採用。

理由:

* MMDユーザー層ではニッチになりやすい
* 厳密な差分比較より、Preview / Warning / 診断レポートの方が実用的
* 機能複雑度に対する効果が小さい

### 17.2 バッチ処理

非採用。

理由:

* 本ツールは一発大量変換ではなく、Preview確認・調整・MMD持ち込みを前提にする
* バッチ処理は別ツール向き
* ASR、変換、診断、警告、出力管理が複雑化しやすい

---

## 18. 明確に入れない要素

本ツールは MMD本体のフォローツールではない。
そのため、以下は明確に対象外とする。

* PMXモデル読み込み
* 3Dプレビュー
* MMD風の表情タイムライン編集
* カメラ / ボーン / 表情全般のVMD編集
* VMD読み込み後の汎用編集
* DAW的な波形編集
* ボーカル抽出の本格実装
* MMDプロジェクト管理
* MMD本体の操作代替
* DCC統合ツール化
* Qt / PySide6 の再導入

理由:

* Whisper 等のASR処理だけでもリソースを消費する
* Pythonベースで3Dモデルビューを導入すると、処理負荷・依存・配布が重くなる
* DirectX 12 等への対応は導入コストが大きい
* MMD_AutoLipTool の責務は、リップVMDの下書き生成、確認、軽微調整、出力補助に留めるべきである
* Qt / PySide6 を再導入すると、MS16で行う依存整理とライセンス簡素化が崩れる

---

## 19. サポート範囲の基本方針

### 19.1 正式サポート対象

* 日本語の台詞音声
* TEXT + WAV 入力
* TEXT + wav / mp3 / m4a 入力
* 15分以内の音声
* MMD用5母音モーフ `あ / い / う / え / お`
* VMD リップモーション出力
* wxPython 主系 GUI

### 19.2 条件付き利用 / 品質保証外

* 歌唱音声
* BGM入り楽曲
* ボーカル抽出済み音声
* 長尺音声
* 音声のみ入力による自動文字起こし
* Whisper の誤認識を含む自動生成結果

### 19.3 将来検討

* 英語対応
* 多言語対応
* 他ASR連携
* 歌唱専用最適化
* 発音単位の詳細編集
* VMD読み戻し編集

---

## 20. 安全制限の基本方針

### 20.1 入力音声尺

現行仕様では、入力音声尺の上限は 15分を維持する。

この上限は、処理時間・メモリ使用量・GUI応答性・ユーザー環境でのフリーズ回避のための安全制限である。

### 20.2 モーフ数上限

生成モーフ数上限は現状維持する。

これは MMD側で扱いづらい過大出力を防ぐための安全制限である。

入力音声尺上限とモーフ数上限は別の制限として扱う。

```text
入力音声尺:
  処理対象として受け付ける音声の長さ

モーフ数上限:
  VMDとして出力するモーフキーフレーム数の上限
```

### 20.3 上限超過時の扱い

* 入力音声尺上限を超えた場合は入力拒否
* モーフ数上限を超えた場合は VMD 出力を中止
* いずれも、ユーザーに理由が分かるエラーメッセージを表示する

---

## 21. ASR方針

### 21.1 標準ASR

標準ASRはローカル Whisper Small とする。

理由:

* 既存実装との互換性が高い
* Windows個人ユーザーでも比較的扱いやすい
* 中程度の精度と処理負荷のバランスがよい

### 21.2 将来のモデルサイズ選択

将来的には、以下のモデルサイズ選択を検討する。

* `small`: 標準・軽量
* `medium`: 精度優先・低速
* `turbo`: 高速高精度候補・環境依存
* `large`: 高精度・非常に重い

ただし、上位モデルを標準にはしない。
ユーザーが明示的に選択する高負荷オプションとして扱う。

### 21.3 他ASR接続

他ASR接続は、MS23以降の設計・調査課題とする。

外部ASRを使う場合は、以下を必ず確認する。

* オフラインで動くか
* APIキーが必要か
* 音声データを外部送信するか
* 商用・配布ライセンス上問題ないか
* 個人制作ユーザーに説明できるか
* タイムスタンプ粒度が十分か
* 日本語台詞・歌唱にどの程度強いか
* Windows配布に組み込めるか

---

## 22. Preview / Writer / Editing の責務境界

### 22.1 基本方針

Preview は、VMD 出力の概念に近い形で表示する。
ただし、MMD の表情キーフレーム編集機能を再実装しない。

### 22.2 推奨データ流れ

```text
自動生成 timing plan
  ↓
event-level adjustment
  ↓
preview shape
  ↓
writer
  ↓
VMD
```

### 22.3 避けること

* Preview 側だけが独自に形状を推測する
* VMD キーフレームを直接GUI編集する
* MMD の表情タイムラインを再実装する
* DAW 的な自由編集へ急拡大する

### 22.4 目指すこと

* 母音イベント単位の意味を保つ
* Preview と writer の形状解釈を揃える
* 小さな補正を安全に VMD 出力へ反映する
* MMD側では最終確認・最終微調整を行う

---

## 23. Codex 実装時の共通注意

各MSの作業開始時は、必ず以下を確認する。

```powershell
git status
git branch
git log --oneline -n 10
```

必要に応じて、以下を確認する。

```text
README.md
pyproject.toml
requirements.txt
MMD_AutoLipTool.spec
build.ps1
docs/repo_milestone.md
docs/Version_Control.md
docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MS16_GUI_Layout_Spec_for_Antigravity.md
.assets\Mockup\MMA_AutoLipTool_Mockup_M16.png

src/main.py
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/preview_panel.py
src/gui_wx/placeholder_panels.py
src/gui_wx/ui_state.py
src/gui_wx/viewport_controller.py
src/core/pipeline.py
src/vmd_writer/writer.py
src/gui/
```

実装後の報告には、最低限以下を含める。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容の要約
4. 依存関係変更の有無
5. Qt / PySide6 残存確認結果
6. 実行したテスト
7. 受け入れ条件との対応
8. 残課題
9. 次に進むべき作業
```

---

## 24. 文書更新ルール

各マイルストーン完了時には、以下を更新する。

* `docs/repo_milestone.md`
* `docs/Version_Control.md`
* 必要に応じて `README.md`
* 必要に応じて本書

ただし、本書は上位マップであるため、個別実装の細部を過度に追記しない。
詳細は各 `MSxx-Bx_Implementation_Plan.md` に分離する。

MS16 では、Qt / PySide6 排除を行うため、以下の文書更新も必要になる可能性が高い。

* README の GUI / 依存説明
* THIRD_PARTY_LICENSES.md の PySide6 / Qt 関連記述
* NOTICE の配布物説明
* Version_Control の依存削減記録
* repo_milestone の MS16 closeout 記録

---

## 25. 今後の最初の作業

本書作成後、次に行うべき作業は `MS16` の開始である。

推奨される最初の作業:

```text
MS16-B1:
  Repo / Dependency / Preview Shape Contract 現状調査
```

この作業では、まず実装は行わず、以下を確認する。

* 現在の PySide6 / Qt 系依存がどこに残っているか
* `pyproject.toml` / `requirements.txt` / `MMD_AutoLipTool.spec` / `build.ps1` の依存状況
* 旧 `src/gui/` の参照状況
* 現在のリボン表示がどこで生成されているか
* 旧Qt/PySide版に近い変形台形表示を復元するには、どのデータ契約が必要か
* writer 側の shape / morph frame 契約と Preview 側の表示契約がどの程度ズレているか
* 将来の母音イベント選択・軽微編集に必要な metadata は何か
* 右ペイン型の Info / Warning / 選択イベント / プリセット / モデルプロファイルタブを実装する際に、既存レイアウトと競合しないか
* 波形表示と Preview の時間軸・カーソルを完全に同期するには、どの viewport 契約を使うべきか

その後、MS16-B2 以降で Qt / PySide6 排除、GUI レイアウト基盤、Preview 表示復元へ進む。

---

## 26. 要約

MS16以降の開発は、次の軸で進める。

```text
MS16:
  wxPython一本化、Qt / PySide6排除、見える化の正規化、GUI拡張基盤

MS17〜MS19:
  入力と利用範囲の拡張、診断・Warningの整備

MS20〜MS22:
  生成品質と編集性の拡張、プリセット・セッション保存・モデルプロファイル

MS23:
  言語・ASR拡張の設計

MS24:
  公開配布の安定化
```

この順序により、MMD_AutoLipTool は、単なる自動VMD生成ツールから、MMDユーザーが実用的なリップモーション下書きを作り、必要に応じて軽微調整できるツールへ段階的に拡張できる。

ただし、本ツールは MMD本体の代替やフォローツールではない。
責務はあくまで、リップVMD生成前の下書き生成、確認、軽微調整、出力補助に留める。

MS16で Qt / PySide6 を完全排除し、wxPython 主系へ一本化することで、ライセンス・配布・保守の複雑さを下げ、以後の MS17〜MS24 を安定して進められる状態にする。
