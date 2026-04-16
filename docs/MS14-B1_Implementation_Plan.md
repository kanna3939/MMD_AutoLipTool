# MS14-B1 Implementation Plan

## 1. Document Control

- Document Name: `MS14-B1_Implementation_Plan.md`
- Milestone: `MS14`
- Block: `MS14-B1`
- Title: `実用 UI 骨格拡張`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS14-B1 では、MS13 で構築した wxPython 最小基盤を、**MS14 の実用コア導線を後続 block で安全に実装できる UI 骨格** へ拡張する。

本 block の目的は、実読込・実解析・実保存を行うことではない。  
**TEXT / WAV 読込結果、変換結果、WAV 情報、口パラメータ入力、将来の波形 / Preview の置き場** を wx 側に明示し、後続 block が流し込む先を固定することが目的である。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 B1 の到達点
- レイアウト追加だけで終わらせず、後続 block から UI を更新するための **setter / view helper** も用意する
- ただし、実データ処理や実状態管理は導入しない
- 「表示の受け皿」と「更新入口」までを B1 の責務とする

### 3.2 情報表示領域の基本構成
- 左側に情報パネルを作る
- この情報パネルに以下をまとめる
  - TEXT path
  - WAV path
  - text preview
  - hiragana preview
  - vowel preview
  - WAV info
- タブ構成は採用しない
- 単純な 1 列縦積みではなく、後続 block で使いやすいまとまりを持った情報パネルとして整理する

### 3.3 右側主領域の placeholder 構成
- 右側主領域は 1 枚 placeholder ではなく、**上下 2 段** に分ける
- 上段を `波形 placeholder`
- 下段を `Preview placeholder`
- どちらも B1 では描画機能を持たない

### 3.4 B1 で置くパラメータ入力
- 以下 3 項目を B1 で配置する
  - `morph_upper_limit`
  - `closing_hold_frames`
  - `closing_softness_frames`
- B1 では入力 widget と label / unit 表示までを整える
- 値変更時の実動作はまだ接続しない

### 3.5 未実装 UI の扱い
- file / run / save は **見た目の実用配置のみ** 行う
- B1 時点では有効化しない
- 再生系主要ボタンも、必要なら置き場だけ確保するが disabled のままとする

### 3.6 レイアウト分割方針
- `MainFrame` へ直接すべて書き足さず、**最小の subpanel / helper class** に分け始める
- ただし、大規模再編はしない
- 分離対象は次の最小単位に留める
  - 情報パネル
  - 右側 placeholder コンテナ
  - パラメータ入力行

### 3.7 `wx.SplitterWindow` の扱い
- B1 では導入しない
- 通常 panel + sizer で構成する
- splitter 導入判断は後続で必要になった時に行う

---

## 4. Goal

MS14-B1 の完了条件は、以下を満たすこととする。

1. MS14 で必要な情報表示領域が wx 側に存在する
2. 左側に情報パネルがあり、path / preview / WAV info の置き場が明確である
3. 右側に波形 / Preview の上下 2 段 placeholder が存在する
4. `morph_upper_limit` / `closing_hold_frames` / `closing_softness_frames` の入力部が存在する
5. 後続 block が UI を更新するための setter / view helper が存在する
6. file / run / save の実用配置はできているが、実機能は未接続のままである
7. `wx.SplitterWindow` を使わずに、通常 panel + sizer で骨格が成立している
8. B2 以降がこの UI 骨格の上で進められる状態になっている

---

## 5. In Scope

MS14-B1 に含めるものは以下とする。

- `MainFrame` の実用 UI 骨格拡張
- 左側情報パネルの追加
- 右側 2 段 placeholder コンテナの追加
- 口パラメータ入力行の追加
- path / preview / info 表示 widget の配置
- 後続 block 用 setter / view helper の追加
- disabled 前提の主要操作 UI の実用配置
- 最小の subpanel / helper class 分離
- レイアウト崩れ防止の最小調整

---

## 6. Out of Scope

MS14-B1 では以下を行わない。

- TEXT open dialog 実装
- WAV open dialog 実装
- 実ファイル読込
- text → hiragana → vowel 実変換
- WAV analyze
- 解析 worker
- `current_timing_plan` 管理
- VMD save
- recent files 実装
- settings save
- warning / status 実ロジックの拡張
- 波形描画
- Preview 描画
- 再生実装
- Zoom / Pan / shared viewport
- テーマ再現
- i18n 本格対応
- 大規模 MVC / presenter / event bus 導入

---

## 7. Expected Functional Boundary

B1 は **表示の受け皿を作る block** である。  
ここでやるべきことは、「後続 block が流し込む先を固定する」ことであり、「動く機能を先に入れること」ではない。

責務の切り分けは以下のとおり。

- **B1:** 実用 UI 骨格拡張
- **B2:** 状態管理と action state 回復
- **B3:** 入力導線 parity 回復
- **B4:** 解析実行 parity 回復
- **B5:** 出力・履歴・settings save parity 回復
- **B6:** 統合整理と parity closeout

したがって B1 では、B2 以降の実ロジックを持ち込まず、**「見えるがまだ動かない受け皿」** に限定する。

---

## 8. Layout Policy

## 8.1 全体構成
B1 の UI 骨格は、以下の構成を基本とする。

1. 上部: 主要操作列
2. その下: 口パラメータ入力行
3. 中央主領域:
   - 左: 情報パネル
   - 右: 表示 placeholder コンテナ
4. 下部: ステータス域

### 意図
- 上部は操作
- 中央左は情報確認
- 中央右は将来の波形 / Preview
- 下部は状態表示

という役割を明確にする。

## 8.2 左側情報パネル
左側情報パネルには、少なくとも以下を含める。

- TEXT path 表示
- WAV path 表示
- text preview
- hiragana preview
- vowel preview
- WAV info 表示

### 意図
B3 で読込が実装されたとき、結果の流し込み先が明確になるようにする。

## 8.3 右側表示 placeholder
右側は上下 2 段構成とする。

- 上段: 波形 placeholder
- 下段: Preview placeholder

### 意図
MS15 の実装受け皿を先に可視化しておく。  
B1 では描画ロジックを持たせない。

## 8.4 パラメータ入力行
パラメータ入力行には、少なくとも以下を置く。

- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`

必要に応じて単位表示を付ける。  
値変更の意味づけや再解析導線は B1 では持たせない。

## 8.5 主要操作 UI
- `TEXT 読込`
- `WAV 読込`
- `解析実行`
- `VMD 保存`

を実用配置で置く。  
ただし、B1 では **disabled のまま** とする。

再生系主要ボタンがある場合も、B1 では **置き場確保まで** に留める。

---

## 9. Design Policy

## 9.1 Build the Surface First
実データ処理より先に、結果を置く面を作る。  
B1 は「表面」を作る block である。

## 9.2 Keep the View Passive
B1 で作る widget は、基本的に受動的な view に留める。  
自ら状態遷移を持たせない。

## 9.3 Add View Helpers Early
後続 block が `FindWindow` 的に widget を探し回らずに済むよう、setter / accessor / helper を早めに置く。

## 9.4 Do Not Rebuild the App Architecture Yet
`MainFrame` 肥大化を避けるため最小分離は行うが、アーキテクチャ全面刷新はしない。

## 9.5 Preserve MS15 Space
波形 / Preview は、今は placeholder に留める。  
ここで実描画へ進まない。

---

## 10. Step Breakdown

## Step 1. Confirm Current MainFrame Structure
- 既存 `MainFrame` の構造を確認する
- MS13 の top / center / bottom 構成を壊さずに、どこへ B1 の UI を差し込むか整理する
- 将来の B2〜B5 が依存する表示位置を把握する

### Exit Condition
- B1 の差し込み位置が明確になっている

---

## Step 2. Introduce Minimal Subpanel / Helper Classes
- 情報パネル
- 右側 placeholder コンテナ
- パラメータ入力行

を必要最小限の subpanel / helper class として切り出す

### Exit Condition
- `MainFrame` に全部ベタ書きせず、最小分離で UI 骨格を組める状態になっている

---

## Step 3. Build Left Information Panel
- TEXT path
- WAV path
- text preview
- hiragana preview
- vowel preview
- WAV info

の表示領域を持つ左側情報パネルを構築する

### Exit Condition
- 読込結果の流し込み先が左側に確定している

---

## Step 4. Build Right Two-Stage Placeholder Container
- 上段波形 placeholder
- 下段 Preview placeholder

を持つ右側コンテナを構築する

### Exit Condition
- 将来の MS15 向け表示領域が上下 2 段で存在する

---

## Step 5. Build Parameter Input Row
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`

の入力行を追加する

### Exit Condition
- MS14 コア導線で使う口パラメータ入力部が存在する

---

## Step 6. Reorganize MainFrame Layout
- 既存の top / center / bottom の枠組みを維持しつつ、
  - 上部操作列
  - パラメータ入力行
  - 中央左右領域
  - 下部ステータス域
  の形へ組み替える
- `wx.SplitterWindow` は使わない
- panel + sizer だけで成立させる

### Exit Condition
- B1 方針どおりの全体骨格が成立している

---

## Step 7. Add View Setters / Helpers
後続 block 用に、最低限の view helper を追加する。  
例えば以下のような責務を想定する。

- TEXT path を表示する
- WAV path を表示する
- text preview を更新する
- hiragana preview を更新する
- vowel preview を更新する
- WAV info 表示を更新する
- 波形 placeholder 文言を変更する
- Preview placeholder 文言を変更する
- パラメータ widget を取得 / 設定する

### Exit Condition
- B2〜B5 が widget を直接掘りに行かずに利用できる

---

## Step 8. Preserve Disabled Policy
- file / run / save の主要操作 UI は disabled のまま維持する
- B1 での有効化は行わない
- 再生系主要ボタンも未実装のまま維持する

### Exit Condition
- B1 が B3 / B4 / B5 を先食いしていない

---

## Step 9. Perform Light Layout Check
- 起動確認
- widget 存在確認
- レイアウト崩れ確認
- placeholder / disabled 状態確認

を行う

### Exit Condition
- B1 の UI 骨格が最低限安定している

---

## 11. Candidate File Touch Areas

repo 実態に応じて調整してよいが、変更対象は以下の範囲に留める。

- `src/gui_wx/main_frame.py`
  - 全体レイアウト更新
  - view helper 追加
- `src/gui_wx/` 配下の新規最小 subpanel / helper class
  - 情報パネル
  - 右側 placeholder コンテナ
  - パラメータ入力行
- 必要最小限のテストファイル
  - widget existence / disabled state / helper existence 確認

B1 では `core/` や `gui/settings_store.py` の意味変更を原則行わない。

---

## 12. Acceptance Criteria

以下をすべて満たしたら B1 完了とみなす。

1. 左側に情報パネルが存在する
2. 情報パネルに TEXT path / WAV path / text / hiragana / vowel / WAV info の表示領域がある
3. 右側に波形 placeholder / Preview placeholder の上下 2 段がある
4. `morph_upper_limit` / `closing_hold_frames` / `closing_softness_frames` の入力部が存在する
5. 主要操作 UI は実用配置だが disabled のまま維持されている
6. `wx.SplitterWindow` を使っていない
7. 最小の subpanel / helper class 分離が行われている
8. 後続 block 用 setter / view helper が存在する
9. 実読込 / 実解析 / 実保存 / 実再生が流入していない
10. 起動してレイアウトが大きく崩れない

---

## 13. Test Plan

## 13.1 Boot Smoke Test
- `src/main.py` から起動する
- frame が表示される
- 例外で即落ちしない

## 13.2 Widget Existence Check
- 情報パネルが存在する
- path / preview / info widget が存在する
- 右側 2 段 placeholder が存在する
- パラメータ入力部が存在する

## 13.3 Disabled Policy Check
- `TEXT 読込`
- `WAV 読込`
- `解析実行`
- `VMD 保存`

が B1 時点では disabled のままであることを確認する

## 13.4 View Helper Check
- path / preview / info を更新する setter / helper が存在する
- helper 呼出でクラッシュしない
- B1 の時点で実データ依存がない

## 13.5 Scope Guard Check
- file dialog が入っていない
- 解析 worker が入っていない
- VMD save が入っていない
- waveform / Preview 実描画が入っていない
- playback 実装が入っていない

---

## 14. Risks and Control

## Risk 1. B1 Becoming B3 Early
「表示先があるならついでに読込まで」と流れ込みやすい。  
**Control:** B1 は view skeleton と helper のみ。

## Risk 2. MainFrame Growing Too Fast
`MainFrame` へ全部積み増すと、MS14 中盤で再び巨大化する。  
**Control:** 最小 subpanel / helper class 分離を許可する。

## Risk 3. Placeholder Turning into Real Feature
右側 placeholder に波形 / Preview の実装を入れ始める危険がある。  
**Control:** 表示枠だけ作り、描画ロジックは持たせない。

## Risk 4. Premature Enablement
操作 UI を先に有効化すると、B2 / B3 / B4 / B5 の境界が崩れる。  
**Control:** B1 では disabled 維持。

## Risk 5. Overengineering the Layout
B1 のために splitter や大規模 view framework を導入すると過剰になる。  
**Control:** panel + sizer に限定する。

---

## 15. Definition of Done

MS14-B1 は、以下の状態になった時点で完了とする。

- wx 側で MS14 用実用 UI 骨格が見える
- 左側情報パネルが存在する
- 右側 2 段 placeholder が存在する
- 口パラメータ入力部が存在する
- 後続 block から更新するための setter / helper が存在する
- 主要操作 UI は未接続・disabled のまま維持されている
- `wx.SplitterWindow` を使わずに layout が成立している
- 実読込 / 実解析 / 実保存 / 実再生はまだ入っていない

---

## 16. Handoff Notes for Implementation

- B1 は「使える機能」ではなく「使える骨格」を作る block である
- 見た目の整形よりも、後続 block の差し込み先を安定化することを優先する
- setter / helper は早めに置いてよいが、state はまだ持ち込まないこと
- 右側は必ず波形 / Preview の上下 2 段で切ること
- 口パラメータ 3 項目はこの段で置き場を確定すること
- `wx.SplitterWindow` は導入しないこと
- file / run / save を勝手に有効化しないこと
- B1 終了時点で、B2 が「状態を流し込む場所」、B3 が「入力結果を流し込む場所」を迷わない状態を残すこと

---

## 17. Status Note

- **2026-04-10**: 実装反映、完了確認済み。`InfoPanel`, `PlaceholderContainer`, `ParameterPanel` への分割と主要 View Helper の整備が完了し、要求（Definition of Done）を満たした状態で終了とした。
