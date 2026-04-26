# MS15-B5_Implementation_Plan

## 1. Document Control

- Document Name: `MS15-B5_Implementation_Plan.md`
- Milestone: `MS15`
- Block: `MS15-B5`
- Title: `表示・再生状態統合 / 最小 UI 整理 / テーマカラー復元`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS15-B5 では、MS15-B1〜B4 で段階的に導入された waveform / Preview / playback / viewport / Zoom / auto-follow の各機能を、wx 主系の UI 状態として最小統合する。

加えて、Qt / PySide6 段階で存在していた **Light / Dark / System** のカラー変更モードを wx 主系に復活させ、モックアップを参照しながら、MS15 時点で必要な範囲の UI カラーリングを実装する。

本 block の目的は、MS15 全体の closeout や最終 polish ではない。  
B5 は、B1〜B4 で分散していた状態と操作導線を、ユーザー操作上破綻しにくい形へ整理し、さらにテーマ切替による基本的な見た目一貫性を回復するための block とする。

---

## 3. Fixed Decisions

### 3.1 B5 の主責務

B5 の主責務は、以下の 3 点とする。

1. **UI 状態統合**
2. **最小限のボタン配置 / 見た目整理**
3. **Light / Dark / System テーマカラー復元**

B5 では MS15 全体 closeout までは行わない。  
ただし、テーマ切替は UI 状態と密接に関係するため、B6 送りではなく B5 の対象に含める。

---

### 3.2 B5 着手条件

B5 は、B1〜B4 の成果を統合する block である。  
したがって、B5 着手条件として以下を要求する。

- B1 の waveform 表示基盤が実装済みであること
- B2 の Preview 表示基盤が実装済みであること
- B3 の Play / Stop / playback position sync が実装済みであること
- B4 の viewport / Zoom / auto-follow が実装済みであること
- B4 の `Zoom In / Zoom Out / Reset Zoom` UI が存在すること
- B4 の `selected_wav_analysis.duration_sec` 正本規約が実装済みであること

B4 が未実装または未統合の場合、B5 は実装開始せず、repo 現在地を報告して停止する。

---

### 3.3 状態モデルの基本方針

B5 では、粗い状態分類を **線形 FSM として扱わない**。

状態は以下のように分ける。

#### 基底状態

基底状態は、主に入力・解析・再生可能性を表す。

- `idle`
- `input_loaded`
- `analysis_ready`
- `playback_ready`
- `playing`

これらは完全な 1 本線の FSM ではなく、実装上は `UiState` から導出される粗い状態カテゴリとして扱う。

#### 直交 overlay flag

`busy` は基底状態と排他にしない。  
`busy` は他状態に重なる **直交 overlay flag** として扱う。

例:

- `input_loaded + busy`
- `analysis_ready + busy`
- `playback_ready + busy`

enable / disable 判定では、`busy == True` を優先して参照する。

---

### 3.4 `analysis_ready` と `playback_ready` の区別

`analysis_ready` と `playback_ready` は同義ではない。

#### `analysis_ready`

以下を満たす状態を指す。

- `analysis_result_valid == True`
- valid な `current_timing_plan` が存在する
- Preview / VMD 出力など、解析結果に依存する操作が可能である

#### `playback_ready`

以下を満たす状態を指す。

- `selected_wav_path` が存在する
- WAV 再生対象として扱える
- B3 playback controller が再生対象として扱える見込みがある

`playback_ready` は `analysis_result_valid == True` を要求しない。  
これは B3 の「再生可能条件は analysis result に依存しない」という方針と整合させる。

---

### 3.5 `analysis_result_valid == False` 時の状態退行

`analysis_result_valid == False` になった場合、以下で扱う。

- `analysis_ready == False` とする
- Preview は placeholder へ戻る
- `current_timing_plan` に依存する操作は不可にする
- ただし `selected_wav_path` が残っている場合、`input_loaded` は維持され得る
- `selected_wav_path` が再生対象として有効であれば、`playback_ready` も維持され得る

つまり、解析結果 invalid は **解析系状態のみを退行**させる。  
WAV 入力や再生可能性まで必ず失効させるものではない。

---

### 3.6 状態正本

B5 の状態正本は、既存 `UiState` を拡張して扱う。

`UiState` には必要に応じて以下を持たせる。

- 入力状態
- 解析状態
- busy flag
- playback 状態参照
- viewport / zoom 状態参照
- theme mode
- resolved theme

ただし、新規の大規模 state machine は作らない。

playback controller / viewport controller が内部状態を持つ場合でも、UI 判断に必要な状態は `UiState` から参照または導出できるようにする。

---

### 3.7 テーマモード

B5 では、以下の 3 モードを復活させる。

- `Light`
- `Dark`
- `System`

`System` は OS / wx 側で取得可能な外観情報に従い、判定不能な場合は安全側として `Light` または既存デフォルトへフォールバックしてよい。

---

### 3.8 テーマ状態の正本

テーマ設定では、以下を区別する。

#### user selected theme mode

保存対象となるユーザー選択値。

- `light`
- `dark`
- `system`

#### resolved theme

実際に適用されるテーマ。

- `light`
- `dark`

`system` は保存上の指定値であり、実際に適用される色は resolved theme によって決まる。

---

### 3.9 設定永続化との関係

テーマモードは B5 の保存・復元対象に含める。

- 保存対象は user selected theme mode
- `system` を選んだ場合は `system` として保存する
- resolved theme 自体は保存しない
- 起動時に保存値を読み込み、必要に応じて resolved theme を解決する

既存設定永続化導線がある場合は、それを利用する。  
既存設定永続化導線が無い、または theme mode を扱えない場合は、B5 で **theme mode のみを対象とする最小保存・復元** を実装してよい。

ただし、設定管理全体の再設計は行わない。

---

### 3.10 テーマ適用範囲

B5 のテーマ適用対象は、wx 主系の主要 UI に限定する。

対象候補:

- `MainFrame`
- operation area / 操作ボタン群
- input / parameter 周辺 UI
- waveform panel
- Preview panel
- info / status 周辺の既存表示領域
- background / foreground / border / grid / label / cursor / selection に相当する基本色

ただし、細かい spacing、アイコン最終調整、完全な design polish は B6 に送る。

---

### 3.11 モックアップの扱い

B5 では、モックアップを **色設計・領域分け・視認性の参照元** として扱う。

- モックアップを pixel-perfect 仕様とはしない
- wx の標準 widget 制約に合わせて実装してよい
- Light / Dark 双方で主要領域の視認性が破綻しないことを優先する
- モックアップが repo 内または添付で確認できない場合は、実装開始前に停止して報告する

---

### 3.12 Play / Stop / Zoom の enable / disable

B5 では、Play / Stop / Zoom の enable / disable を最小限整理する。

ただし、

- 詳細な disabled 理由表示
- tooltip の全面整理
- status 文言との完全統合

は B6 に送る。

B5 では、最低限「押せるべきでない状態で押せない、または押してもロジックガードで破綻しない」状態を目標とする。

---

### 3.13 Play / Stop の最小条件

#### Play

Play は以下を満たす場合に enable とする。

- `playback_ready == True`
- `busy == False`
- `playing == False`

`analysis_ready == True` は Play の条件にしない。

#### Stop

Stop は以下を満たす場合に enable とする。

- `playing == True`

busy 中の Stop を許可するかどうかは既存 B3 実装に従う。  
ただし、再生停止が安全側処理として必要な場合は、Stop が実行可能であることを優先してよい。

---

### 3.14 Zoom 系操作の最小条件

Zoom 操作は B4 の viewport / duration 状態に依存する。

#### 共通条件

Zoom In / Zoom Out / Reset Zoom は、少なくとも以下を共通条件とする。

- `selected_wav_analysis.duration_sec` が有効
- viewport / zoom controller が ready
- `busy == False`

#### Zoom In

Zoom In は以下を満たす場合に enable とする。

- 共通条件を満たす
- 現在 zoom factor が最大 `8x` 未満

#### Zoom Out

Zoom Out は以下を満たす場合に enable とする。

- 共通条件を満たす
- 現在 zoom factor が `1x` より大きい

#### Reset Zoom

Reset Zoom は以下を満たす場合に enable とする。

- 共通条件を満たす
- viewport / zoom controller が reset を受けられる

Reset Zoom は、現在 `1x` であっても enable のままでよい。  
ただし、UI 上の最終的な enable / disable polish は B6 に送る。

---

### 3.15 Run Analysis / Load 系操作の扱い

B5 では、Run Analysis / Load 系操作について、既存挙動を壊さない範囲で最小整理する。

基本方針:

- `busy == True` の間、Run Analysis は実行不能またはロジックガードで拒否される
- 入力未選択時、Run Analysis は実行不能またはロジックガードで拒否される
- Load / input 系操作の最終的な disabled 方針は既存実装を優先する
- 再生中に入力変更が発生する場合は、B3 の既存ルールに従い、再生停止が先に行われる

---

### 3.16 status 表示・メッセージ整理

B5 では、status 表示・メッセージ整理は対象外とする。

- status 文言の全面整理は B6 に送る
- B5 では既存 status 導線を壊さない
- テーマ適用によって status 表示が読めなくならないよう、色だけは最低限整える

---

### 3.17 入力変更・再解析・再生中状態の衝突規則

B5 では、B3/B4 までに導入された既存ルールを文書化・接続確認するだけに留める。

既存前提:

- busy 中は再生禁止
- 再生中に解析開始が必要な場合は先に停止
- 再生中に `selected_wav_path` が変更された場合は停止して `0.0 sec` へ戻す
- duration 更新時は viewport state を full-range + `1x` へ reset
- `analysis_result_valid == False` 時は Preview を placeholder へ戻す

B5 はこれらのルールを再設計しない。

---

### 3.18 B6 へ送るもの

以下は B5 では扱わず、B6 closeout へ送る。

- status 文言の全面整理
- disabled 理由の詳細表示
- 操作パネルの最終 polish
- アイコン / spacing / layout の最終調整
- MS15 全体の最終検収
- ドキュメント closeout
- 軽微な UX 表現の最終統一

---

## 4. Goal

本節の項目群を、**MS15-B5 の canonical completion criteria** とする。  
後続の `13. Acceptance Criteria` および `16. Definition of Done` は意味差なしで本節を再掲する。

1. B5 着手時点で B1〜B4 の主要実装が揃っていることを確認している
2. `UiState` が B5 の UI 状態判断の正本として使える
3. 基底状態と `busy` overlay flag の関係が定義されている
4. `analysis_ready` と `playback_ready` の差分が定義されている
5. `analysis_result_valid == False` 時に `analysis_ready` が解除される
6. Play / Stop / Zoom の enable / disable が最小限整理されている
7. Zoom In / Zoom Out / Reset Zoom の最小 enable 条件が定義されている
8. 押せるべきでない主要操作が、UI またはロジックガードで破綻しない
9. `Light / Dark / System` のテーマモードが選択できる
10. `System` 指定時に resolved theme が決定される
11. 主要 UI にテーマカラーが反映される
12. waveform / Preview が light / dark 双方で視認可能である
13. テーマモードが保存・復元される
14. B3/B4 の既存衝突ルールが UI 状態判断と矛盾していない
15. 操作ボタン群の配置・見た目が B5 範囲で最低限整理されている
16. status 文言の全面整理を B5 に流入させていない
17. 新規の大規模 state machine を導入していない
18. B6 が closeout / polish に集中できる状態になっている

---

## 5. In Scope

MS15-B5 に含めるものは以下とする。

- B1〜B4 実装済み状態の確認
- `UiState` の必要最小限の拡張
- 基底状態と overlay flag の整理
- `analysis_ready` / `playback_ready` の区別
- `analysis_result_valid == False` 時の状態退行整理
- Play / Stop / Zoom の enable / disable 最小整理
- Zoom In / Zoom Out / Reset Zoom の最小 enable 条件定義
- B3/B4 のロジックガードと UI 状態判断の整合確認
- busy / playing / input_loaded / analysis_ready / playback_ready の基本判定
- 操作ボタン群の最小レイアウト整理
- ボタン配置の重複・違和感の最小修正
- `Light / Dark / System` テーマモード復活
- theme mode / resolved theme の状態管理
- 主要 UI へのテーマカラー適用
- waveform / Preview の light / dark 対応
- operation area / panel 背景 / label / border / grid / cursor の基本色整理
- 既存設定導線、または B5 最小導線による theme mode 保存・復元
- B5 に必要な軽量テストの追加または更新

---

## 6. Out of Scope

MS15-B5 では以下を行わない。

- status 文言の全面整理
- disabled 理由の詳細表示
- 操作パネルの最終 polish
- アイコンの最終整理
- spacing / margin / visual design の最終調整
- pixel-perfect なモックアップ再現
- MS15 全体 closeout
- B6 相当の最終検収
- 新規の大規模 state machine
- Pause
- Seek
- Loop
- continuous Zoom
- Pan
- mp3 対応
- 音声のみ入力対応
- B1/B2/B3/B4 の主要仕様変更
- OS テーマ変更のリアルタイム監視
  - 起動時または設定変更時の反映まででよい

---

## 7. Expected Functional Boundary

B5 は「B1〜B4 で導入された機能を、ユーザー操作上破綻しにくい UI 状態へまとめ、さらに wx 主系で基本テーマを復活させる block」である。

責務分離は以下のとおり。

- **B1:** 波形表示基盤
- **B2:** Preview 表示基盤
- **B3:** 再生開始 / 停止と再生位置同期
- **B4:** viewport API / canonical shared viewport / Zoom / オートスクロール
- **B5:** 表示・再生状態統合 / 最小 UI 整理 / テーマカラー復元
- **B6:** closeout / polish / 最終確認

B5 では、状態統合と基本テーマ復元を行う。  
ただし、B1〜B4 の主要仕様変更や B6 closeout は行わない。

---

## 8. Current Recognition for B5 Entry

### 8.1 実装側

- B1 により waveform 表示基盤が成立済みである必要がある
- B2 により Preview 表示基盤が成立済みである必要がある
- B3 により Play / Stop と playback position sync が成立済みである必要がある
- B4 により viewport / Zoom / auto-follow が成立済みである必要がある
- `UiState` は既に入力・解析系状態を持っている
- B3/B4 controller が内部状態を持つ可能性がある
- 操作ボタン群は MS15 の段階的実装により増えている可能性がある
- Qt / PySide6 段階ではテーマ切替が存在していた
- wx 主系ではテーマ切替・カラー適用が未整理である可能性が高い

### 8.2 B5 で再確認すべき領域

- B4 が実装済みか
- `UiState` に現在どの状態が存在するか
- `analysis_result_valid` の invalidation 導線
- playback ready を判定する既存情報
- viewport / zoom ready を判定する既存情報
- theme / settings 関連の既存実装があるか
- Qt 側テーマ実装の責務と保存形式
- wx 側でテーマ適用すべき主要 widget
- モックアップの所在と参照範囲
- Play / Stop / Zoom 操作の現在の配置
- button enable / disable の既存実装有無
- busy 中 / playing 中 / input 未選択時の操作挙動
- B3/B4 のロジックガードと UI 側の状態判断が衝突していないか

---

## 9. Design Axes

### 9.1 State Axis

- `UiState` を状態判断の正本にする
- 基底状態と overlay flag を分ける
- `busy` は直交 overlay flag とする
- `analysis_ready` と `playback_ready` を分ける
- controller ごとの状態分散を増やしすぎない
- 新規大規模 state machine は導入しない

### 9.2 Theme Axis

- `Light / Dark / System` を復活させる
- user selected theme と resolved theme を分ける
- 主要 UI にのみテーマカラーを適用する
- OS テーマ変更のリアルタイム監視までは行わない
- モックアップは視認性・配色方針の参照元とする

### 9.3 Action Axis

- Play / Stop / Zoom の最小 enable / disable
- Zoom 系操作は B4 viewport / duration / zoom factor を参照する
- 押せない状態では押せない、または押しても破綻しない
- 詳細な disabled 理由表示は行わない

### 9.4 UI Axis

- 操作ボタン群の最小配置整理を行う
- テーマカラーの基本適用を行う
- 見た目の最終 polish は B6
- status 文言統合は B6

---

## 10. Candidate File Touch Areas

### コード

- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/playback_controller.py`
- `src/gui_wx/viewport_controller.py`
- `src/gui_wx/waveform_panel.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/info_panel.py`
- `src/gui_wx/parameter_panel.py`
- 既存 settings / config 関連ファイルがあればそれ

### 新規追加候補

- `src/gui_wx/theme.py`
  - theme mode
  - resolved theme
  - light / dark palette
  - system theme resolve
- `src/gui_wx/theme_manager.py`
  - theme 適用 helper
  - 各 panel への適用導線
- `src/gui_wx/ui_action_state.py`
  - 主要操作の enable / disable 判定 helper
  - 状態保持ではなく判定関数中心

新規ファイル名は repo 現在地に合わせて調整してよい。  
ただし、新規大規模 state machine は導入しない。

---

## 11. Execution Policy

### 11.1 まず B1〜B4 完了状態を確認する

B5 実装前に、B1〜B4 の主要成果が repo に存在するか確認する。

特に以下を確認する。

- waveform panel
- Preview panel
- playback controller
- viewport / zoom controller
- Zoom UI
- auto-follow
- `selected_wav_analysis.duration_sec` 正本規約

不足している場合、B5 実装を開始せず報告する。

---

### 11.2 既存状態と既存テーマ実装を棚卸しする

実装前に、以下を確認する。

- `UiState`
- playback controller
- viewport controller
- main frame
- 既存 settings / config
- Qt 側テーマ実装
- wx 側 UI の色指定状況
- モックアップの所在

---

### 11.3 `UiState` を中心に寄せる

UI 判断に必要な状態は `UiState` から参照できるように整理する。

- 各 controller の内部状態を完全に移す必要はない
- UI 判断が controller 横断で散らばらないようにする
- `UiState` に過剰な細部を持たせない

---

### 11.4 テーマは最小 palette として扱う

B5 では、テーマを最小 palette として扱う。

最低限、以下の用途色を整理する。

- window background
- panel background
- text foreground
- muted text
- border / separator
- waveform line
- waveform grid
- playback cursor
- Preview lane background
- Preview segment / shape
- button background / foreground
- disabled foreground

---

### 11.5 enable / disable は最小整理に留める

対象候補:

- Load / input 系
- Run Analysis
- Play
- Stop
- Zoom In
- Zoom Out
- Reset Zoom
- Theme mode selector

詳細 tooltip / disabled reason は B6 へ送る。

---

### 11.6 B3/B4 ルールを再設計しない

B5 は、B3/B4 の既存ルールを変更する block ではない。

- busy 中再生禁止
- 再生中解析開始前停止
- 再生中パス変更時停止
- duration 更新時 viewport reset

などは、B5 では整合確認と UI 接続に留める。

---

### 11.7 status 文言整理を流入させない

B5 では status 文言体系を再設計しない。  
テーマ適用による視認性確保に留める。

---

## 12. Step Breakdown

### Step 0. Confirm Entry Gate

- B1〜B4 の主要実装が存在するか確認する
- B4 viewport / Zoom / auto-follow が実装済みか確認する
- `UiState` の現状を確認する
- Play / Stop / Zoom UI の現状を確認する
- B3/B4 のロジックガードが存在するか確認する
- 既存テーマ / settings 実装の有無を確認する
- モックアップが参照可能か確認する

#### Exit Condition

- B5 実装開始条件が満たされている  
  **または**
- B5 が依存する B1〜B4 / モックアップ / テーマ参照情報が不足していることが明確になっている

---

### Step 1. Inventory Current State Sources

- `UiState` の状態を棚卸しする
- playback controller の状態を棚卸しする
- viewport / zoom controller の状態を棚卸しする
- main frame 内の個別フラグを確認する
- settings / theme 関連状態を確認する

---

### Step 2. Define Coarse UI State Model

以下を定義する。

- 基底状態
  - `idle`
  - `input_loaded`
  - `analysis_ready`
  - `playback_ready`
  - `playing`
- overlay flag
  - `busy`

あわせて以下を明記する。

- `busy` は直交 overlay flag
- `analysis_ready` と `playback_ready` は別状態
- `analysis_result_valid == False` で `analysis_ready` は解除される
- `playback_ready` は `analysis_result_valid` に依存しない

---

### Step 3. Define Theme Model

以下を定義する。

- theme mode
  - `light`
  - `dark`
  - `system`
- resolved theme
  - `light`
  - `dark`
- palette
- theme apply target
- settings save / load 方針

---

### Step 4. Extend / Normalize UiState

- 必要最小限で `UiState` を拡張する
- UI 判断に必要な状態を参照可能にする
- theme mode / resolved theme を参照可能にする
- controller 内部状態との二重管理を避ける

---

### Step 5. Implement Theme Apply Path

- `Light` palette を適用する
- `Dark` palette を適用する
- `System` 指定時に resolved theme を解決する
- main frame / panels / waveform / Preview / operation area へ最低限反映する
- テーマ変更時に再描画されるようにする
- theme mode の保存・復元を接続する

---

### Step 6. Define Action Enable / Disable Rules

主要操作について最小条件を定義する。

対象:

- Load / input 系
- Run Analysis
- Play
- Stop
- Zoom In
- Zoom Out
- Reset Zoom
- Theme mode selector

Zoom 系操作については、B4 の zoom factor / viewport ready / duration 有効性を参照して条件を定義する。

---

### Step 7. Wire Action State to UI

- main frame / operation area のボタン状態へ反映する
- Play / Stop / Zoom の最低限の操作可否を反映する
- Theme selector の操作導線を接続する
- 押せない状態で押しても破綻しないことを確認する

---

### Step 8. Minimal Operation Area Layout Cleanup

- B3/B4/B5 で増えたボタン群を最低限整理する
- Theme selector を過剰に目立たせず、操作導線として認識可能にする
- 見た目の最終 polish は行わない

---

### Step 9. Check Conflict Rules Against UI State

以下の既存ルールと UI 状態判断が矛盾しないか確認する。

- busy 中再生禁止
- 再生中解析開始前停止
- 再生中パス変更時停止
- duration 更新時 viewport reset
- `analysis_result_valid == False` 時 Preview placeholder 復帰

---

### Step 10. Add / Update Lightweight Tests

- `UiState` 状態分類テスト
- `busy` overlay flag テスト
- `analysis_ready` / `playback_ready` 差分テスト
- `analysis_result_valid == False` 時の `analysis_ready` 解除テスト
- Play / Stop enable / disable テスト
- Zoom In / Out / Reset enable / disable テスト
- theme mode / resolved theme テスト
- Light / Dark palette 適用テスト
- System fallback テスト
- theme mode 保存・復元テスト
- waveform / Preview theme 適用テスト
- busy 中操作テスト
- input 未選択時操作テスト
- playing 中操作テスト
- B3/B4 ロジックガードとの整合テスト

---

### Step 11. Re-check Scope Guard

- status 文言全面整理が流入していないか
- B6 closeout が流入していないか
- 新規大規模 state machine が流入していないか
- B1〜B4 の主要仕様を変更していないか
- 見た目 polish をやりすぎていないか
- theme 実装が OS リアルタイム監視や大規模設定再設計へ膨らんでいないか

---

## 13. Acceptance Criteria

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. B5 着手時点で B1〜B4 の主要実装が揃っていることを確認している
2. `UiState` が B5 の UI 状態判断の正本として使える
3. 基底状態と `busy` overlay flag の関係が定義されている
4. `analysis_ready` と `playback_ready` の差分が定義されている
5. `analysis_result_valid == False` 時に `analysis_ready` が解除される
6. Play / Stop / Zoom の enable / disable が最小限整理されている
7. Zoom In / Zoom Out / Reset Zoom の最小 enable 条件が定義されている
8. 押せるべきでない主要操作が、UI またはロジックガードで破綻しない
9. `Light / Dark / System` のテーマモードが選択できる
10. `System` 指定時に resolved theme が決定される
11. 主要 UI にテーマカラーが反映される
12. waveform / Preview が light / dark 双方で視認可能である
13. テーマモードが保存・復元される
14. B3/B4 の既存衝突ルールが UI 状態判断と矛盾していない
15. 操作ボタン群の配置・見た目が B5 範囲で最低限整理されている
16. status 文言の全面整理を B5 に流入させていない
17. 新規の大規模 state machine を導入していない
18. B6 が closeout / polish に集中できる状態になっている

---

## 14. Verification Plan

### 14.1 Runtime / Integration Checks

#### 14.1.1 UI State

- 入力前 / 入力後 / 解析後 / 再生中の状態が破綻しない
- `busy` overlay が基底状態と矛盾しない
- `analysis_ready` と `playback_ready` が混同されない
- Play / Stop / Zoom の状態が大きく矛盾しない

#### 14.1.2 Theme Switching

- Light に切り替えられる
- Dark に切り替えられる
- System に切り替えられる
- System が判定不能な場合も破綻しない
- 切替後に主要 UI が再描画される
- 再起動後に theme mode が復元される

#### 14.1.3 Waveform / Preview Theme

- light mode で波形・Preview が読める
- dark mode で波形・Preview が読める
- playback cursor / grid / lane / segment が背景と同化しない

#### 14.1.4 Operation Area

- Play / Stop / Zoom / Theme selector が最低限整理されている
- ボタン追加により著しく操作不能なレイアウトになっていない

---

## 15. Risks and Control

### Risk 1. State Fragmentation
playback / viewport / analysis の状態が各所に分散し、UI 判断が複雑化する危険がある。  
**Control:** `UiState` を UI 状態判断の正本にする。

### Risk 2. Busy State Ambiguity
`busy` を基底状態と混同し、enable / disable 判定が不安定になる危険がある。  
**Control:** `busy` は直交 overlay flag として定義する。

### Risk 3. Analysis/Playback Ready Confusion
`analysis_ready` と `playback_ready` が混同され、Play が解析結果に依存する危険がある。  
**Control:** 両者を明確に分け、Play は `playback_ready` を条件にする。

### Risk 4. Theme Scope Creep
テーマ復元が最終 polish や pixel-perfect 再現へ膨らむ危険がある。  
**Control:** B5 では主要 UI の基本カラー適用に限定する。

### Risk 5. B6 Scope Leakage
status 文言整理や最終 polish が B5 に流入する危険がある。  
**Control:** status と polish は B6 に送る。

### Risk 6. Inconsistent Button Behavior
Play / Stop / Zoom が状態と矛盾し、ユーザー操作で破綻する危険がある。  
**Control:** B5 で enable / disable を最小整理し、押せない状態は UI またはロジックガードで抑止する。

### Risk 7. Poor Theme Visibility
light / dark の一方で waveform や Preview が見づらくなる危険がある。  
**Control:** waveform / Preview 用 palette を明示的に持つ。

### Risk 8. System Theme Instability
OS テーマ判定が環境依存で不安定になる危険がある。  
**Control:** 判定不能時は安全な fallback を許容する。

---

## 16. Definition of Done

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. B5 着手時点で B1〜B4 の主要実装が揃っていることを確認している
2. `UiState` が B5 の UI 状態判断の正本として使える
3. 基底状態と `busy` overlay flag の関係が定義されている
4. `analysis_ready` と `playback_ready` の差分が定義されている
5. `analysis_result_valid == False` 時に `analysis_ready` が解除される
6. Play / Stop / Zoom の enable / disable が最小限整理されている
7. Zoom In / Zoom Out / Reset Zoom の最小 enable 条件が定義されている
8. 押せるべきでない主要操作が、UI またはロジックガードで破綻しない
9. `Light / Dark / System` のテーマモードが選択できる
10. `System` 指定時に resolved theme が決定される
11. 主要 UI にテーマカラーが反映される
12. waveform / Preview が light / dark 双方で視認可能である
13. テーマモードが保存・復元される
14. B3/B4 の既存衝突ルールが UI 状態判断と矛盾していない
15. 操作ボタン群の配置・見た目が B5 範囲で最低限整理されている
16. status 文言の全面整理を B5 に流入させていない
17. 新規の大規模 state machine を導入していない
18. B6 が closeout / polish に集中できる状態になっている

---

## 17. Handoff Notes for Implementation

- B5 は表示・再生状態統合 / 最小 UI 整理 / テーマカラー復元 block である
- B5 実装前に B1〜B4 が揃っていることを確認すること
- `UiState` を UI 状態判断の正本として扱うこと
- `busy` は直交 overlay flag として扱うこと
- `analysis_ready` と `playback_ready` を分けること
- `analysis_result_valid == False` 時は `analysis_ready` を解除すること
- Play / Stop / Zoom の enable / disable を最小整理すること
- Zoom 系操作は duration / viewport ready / zoom factor を条件にすること
- `Light / Dark / System` を復活させること
- user selected theme と resolved theme を分けること
- theme mode を保存・復元すること
- waveform / Preview の色を light / dark 双方で確認すること
- モックアップは参照元であり pixel-perfect 仕様ではない
- status 文言の全面整理は行わないこと
- 操作ボタン群の見た目調整は最低限に留めること
- B6 に送る closeout / polish 項目を明確に残すこと
- B1〜B4 の主要仕様を変更しないこと

---

## 18. Status Note

- **2026-04-22**: Revised draft for MS15-B5.  
  B5 の主責務に、UI 状態統合、最小 UI 整理、Qt / PySide6 段階に存在した `Light / Dark / System` テーマカラー切替の wx 主系復元を含めた。レビュー指摘を反映し、`busy` を直交 overlay flag として定義し、`analysis_ready` / `playback_ready` の差分、`analysis_result_valid == False` 時の状態退行、Zoom 系操作の enable 条件、B4 完了を含む Entry Gate、theme mode の保存・復元方針、Goal / AC / DoD の一致を明示した。
