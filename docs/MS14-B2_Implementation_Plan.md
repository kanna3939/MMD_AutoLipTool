# MS14-B2 Implementation Plan

## 1. Document Control

- Document Name: `MS14-B2_Implementation_Plan.md`
- Milestone: `MS14`
- Block: `MS14-B2`
- Title: `状態管理と action state 回復`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS14-B2 では、MS14-B1 で拡張した実用 UI 骨格の上に、**実用コア導線を後続 block で安全に接続するための最小状態管理契約** を導入する。

本 block の目的は、実読込・実解析・実保存を行うことではない。  
**wx 側で保持すべき state、busy 中 lock、action enable / disable、status 更新、解析結果 invalidation のルール** を固定し、B3 以降が場当たり的に属性や状態判定を増やさずに実装できるようにすることが目的である。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 state の保持場所
- `MainFrame` にすべて直接持たせず、`gui_wx` 配下に **軽量な state holder** を新設する
- 想定名称は `UiState` または `AppState` 相当とする
- ただし、大規模 MVC / store / reducer 化は行わない
- `MainFrame` はこの state holder を参照し、UI 反映を行う

### 3.2 action state の判定主体
- action enable / disable 判定の主体は **`MainFrame` 側** とする
- B2 では `AppController` に判定責務を寄せない
- `MainFrame` は state holder を参照して UI 状態を反映する
- `AppController` は引き続き action sink / 将来接続点として扱う

### 3.3 B2 で導入する state の粒度
- ブール最小集合だけではなく、**後続 block が使う実用最小セット** を state 契約として持つ
- 少なくとも以下を正式に扱う
  - `selected_text_path`
  - `selected_wav_path`
  - `selected_text_content`
  - `selected_hiragana_content`
  - `selected_vowel_content`
  - `selected_wav_analysis`
  - `current_timing_plan`
  - `is_busy`
  - `status_key` または同等の status 状態
  - 解析結果の有効 / 無効を示す最小状態

### 3.4 `current_timing_plan` の扱い
- B2 の時点で、`current_timing_plan` を正式な state として位置づける
- B2 では実体は基本 `None` 前提でよい
- ただし、**invalidate / available 判定** はこの段で整理する

### 3.5 status 文言の扱い
- B2 から **status key / helper** を導入する
- 直接文字列ベタ書きには寄せない
- ただし、i18n 本格対応までは行わない
- B2 の主眼は「status の意味状態」を整理することにある

### 3.6 busy 中 lock の範囲
- busy 中は、以下を lock 対象に含める
  - `TEXT 読込`
  - `WAV 読込`
  - `解析実行`
  - `VMD 保存`
  - パラメータ入力
  - recent menu
  - 将来の再生系主要ボタン置き場
- 未実装項目は disabled のままでよいが、busy 契約上は lock 対象に含める

### 3.7 invalidation の扱い
- `current_timing_plan` の invalidate だけでなく、**解析結果有効 / 無効状態** も整理する
- 再解析待ち相当の状態も、B2 の state 契約として整理する
- B3 で入力が変わった時、B4 で解析成功 / 失敗した時、B5 で保存可否を判断する時の土台とする

### 3.8 テスト方針
- B2 では、state 初期値確認だけでなく、
  - action enable / disable
  - busy 遷移
  - invalidation
  - status 遷移
  の軽量テストも導入してよい

---

## 4. Goal

MS14-B2 の完了条件は、以下を満たすこととする。

1. wx 側に実用最小 state holder が存在する
2. `MainFrame` がその state holder を参照して action state を反映できる
3. file / run / save / パラメータ / recent / 再生置き場に対する busy lock 契約が存在する
4. `current_timing_plan` を含む解析結果 state の有効 / 無効判定が存在する
5. status 更新が status key / helper 経由で扱える
6. B3 以降が state 追加を場当たりで行わずに実装できる
7. 実読込 / 実解析 / 実保存はまだ流入していない
8. 軽量テストで state / action / busy / invalidation の基本遷移が確認できる

---

## 5. In Scope

MS14-B2 に含めるものは以下とする。

- `gui_wx` 配下への軽量 state holder 導入
- state 初期値定義
- state 更新 helper の最小導入
- `MainFrame` 側 action state 判定ロジック
- busy lock 判定ロジック
- invalidation ルールの導入
- status key / helper の導入
- `MainFrame` の UI 反映メソッド整理
- 軽量 state / action / busy / invalidation テスト

---

## 6. Out of Scope

MS14-B2 では以下を行わない。

- TEXT open dialog 実装
- WAV open dialog 実装
- 実ファイル読込
- text → hiragana → vowel 実変換
- WAV analyze
- 解析 worker 実装
- VMD save 実装
- recent files 実データ更新
- settings save 実装
- waveform / Preview 実描画
- playback 実装
- Zoom / Pan / shared viewport
- テーマ再現
- i18n 本格対応
- `AppController` の大規模責務増加
- 大規模 MVC / store / event bus 化

---

## 7. Expected Functional Boundary

B2 は **状態契約を作る block** である。  
ここでやるべきことは、「後続 block が何を state として持ち、どの条件で UI を有効 / 無効にするか」を整理することである。

責務の切り分けは以下のとおり。

- **B1:** 実用 UI 骨格拡張
- **B2:** 状態管理と action state 回復
- **B3:** 入力導線 parity 回復
- **B4:** 解析実行 parity 回復
- **B5:** 出力・履歴・settings save parity 回復
- **B6:** 統合整理と parity closeout

したがって B2 では、B3 以降の実処理を持ち込まず、**「どういう state があるべきか」「UI はそれにどう反応するか」** の契約に限定する。

---

## 8. State Policy

## 8.1 State Holder の位置づけ
- `gui_wx` 配下に軽量な state holder を置く
- これはアプリ全体の大規模状態管理機構ではない
- MS14 の core workflow に必要な最小状態だけを持つ
- `MainFrame` は表示反映の主体として、それを読む

## 8.2 想定 state 項目
少なくとも以下を state として持つことを想定する。

### Input Related
- `selected_text_path`
- `selected_wav_path`
- `selected_text_content`
- `selected_hiragana_content`
- `selected_vowel_content`
- `selected_wav_analysis`

### Analysis Related
- `current_timing_plan`
- `analysis_result_valid` または同等概念
- `analysis_pending_rebuild` または同等概念

### UI / Application Related
- `is_busy`
- `status_key`
- 必要なら `status_detail` 相当の最小補助情報

## 8.3 初期状態
B2 時点では、基本的に以下が初期状態となる。

- 各 path は未設定
- 各 content は空
- `selected_wav_analysis` は未設定
- `current_timing_plan` は未設定
- `analysis_result_valid` は false
- `analysis_pending_rebuild` は false
- `is_busy` は false
- `status_key` は初期状態

## 8.4 State の正本性
B2 以降、実用導線に関する状態は原則として state holder を正本とする。  
`MainFrame` に同義の重複属性を乱立させない。

---

## 9. Action State Policy

## 9.1 判定主体
- action state 判定は `MainFrame` が行う
- 判定元は state holder とする
- `AppController` はまだ判定主体にしない

## 9.2 判定対象
少なくとも以下を判定対象とする。

- `TEXT 読込`
- `WAV 読込`
- `解析実行`
- `VMD 保存`
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`
- recent TEXT / WAV
- 再生系主要ボタン置き場

## 9.3 B2 時点の意味
B2 の時点では、これらをすべて実動化しない。  
ただし、「どの条件なら有効にできるか」「busy 中はどう扱うか」を決める。

## 9.4 判定観点
- 必要入力が揃っているか
- 解析結果が有効か
- 解析結果が無効化されているか
- busy 中か
- 未実装のため常時 disabled か

---

## 10. Busy Policy

## 10.1 busy の意味
B2 における `is_busy` は、後続 block で
- 解析実行中
- 必要なら保存中
- 将来の重い処理中

に UI 操作を制御するための最小状態とする。

## 10.2 busy 中 lock 対象
busy 中は、以下を lock 対象とする。

- TEXT 読込
- WAV 読込
- 解析実行
- VMD 保存
- パラメータ入力
- recent menu
- 再生系主要ボタン置き場

## 10.3 busy 中でも変えないもの
B2 の時点では、busy 中 lock の実運用はまだ B4 / B5 側で具体化される。  
B2 では「契約だけ」先に持つ。

---

## 11. Invalidation Policy

## 11.1 invalidation の必要性
MS14 では、入力変更により解析結果が古くなる。  
そのため、B2 の時点で **解析結果が今有効かどうか** を state として持つ必要がある。

## 11.2 invalidation 対象
- `current_timing_plan`
- 解析結果有効フラグ
- 再解析待ち状態

## 11.3 invalidation を引き起こす典型例
B2 では実処理を入れないが、後続 block で以下が起こる前提を整理する。

- TEXT が変わる
- WAV が変わる
- `morph_upper_limit` が変わる
- その他、解析結果に依存する入力が変わる

## 11.4 B2 でやること
- invalidation helper を定義する
- invalidation 後の action state がどう変わるか決める
- status がどう遷移するか決める

---

## 12. Status Policy

## 12.1 B2 の status の位置づけ
B2 では、表示文言を完成させることよりも、**状態意味としての status** を整理する。

## 12.2 status key / helper
- 直接文字列ではなく status key / helper を導入する
- 例:
  - `idle`
  - `input_missing`
  - `ready_for_analysis`
  - `analysis_invalidated`
  - `busy`
  - `analysis_ready`
- 実際の key 名は repo 既存構造に合わせて決めてよい

## 12.3 文言の範囲
- i18n 本格対応はまだ行わない
- B2 では「表示に使う意味状態」を固定する
- 文言実体は最小の英日固定でもよいが、直書き乱立は避ける

---

## 13. Design Policy

## 13.1 Introduce State Before Logic
実ロジックより先に、state 契約を導入する。  
B3 以降はその state 契約の上に乗せる。

## 13.2 Keep Controller Light
`AppController` に action state 判定まで持ち込まない。  
B2 では `MainFrame + state holder` の範囲で閉じる。

## 13.3 Preserve Passive View Direction
`MainFrame` は UI 表示反映の主体ではあるが、ビジネスロジック本体にはしない。  
B2 で入れるのは UI state 判定までに留める。

## 13.4 Make Invalidation Explicit
`current_timing_plan = None` だけの暗黙契約にせず、解析結果有効 / 無効状態を明示する。

## 13.5 Prepare for Tests Early
B2 はロジック block なので、軽量でも遷移テストを入れる。

---

## 14. Step Breakdown

## Step 1. Confirm B1 UI Surface and Current State Locations
- B1 で増えた UI 骨格を確認する
- 現在 `MainFrame` に残っている属性のうち、B2 で state 化すべきものを洗い出す
- 重複 state 候補を整理する

### Exit Condition
- B2 で正本化する state 項目が明確になっている

---

## Step 2. Introduce Minimal State Holder
- `gui_wx` 配下に軽量 state holder を追加する
- 初期状態を定義する
- 必要最小限の更新 helper を用意する

### Exit Condition
- 実用最小 state を保持できる箱が存在する

---

## Step 3. Connect MainFrame to State Holder
- `MainFrame` が state holder を保持 / 参照できるようにする
- 表示反映の入口を整理する
- 既存属性と state holder の責務を切り分ける

### Exit Condition
- `MainFrame` が state 正本を参照する構造になっている

---

## Step 4. Build Action State Evaluation
- state を元に action enable / disable を判定する
- file / run / save / parameter / recent / playback slot の状態を整理する
- 未実装項目の disabled と、状態に応じた disabled を区別できる形にする

### Exit Condition
- action state 判定が一元化されている

---

## Step 5. Build Busy Lock Policy
- `is_busy` を導入する
- busy 中 lock の対象を UI 反映へ落とし込む
- B4 / B5 で busy 運用を載せられる形にする

### Exit Condition
- busy lock 契約が UI へ反映できる

---

## Step 6. Build Invalidation Helpers
- `current_timing_plan` invalidation helper を用意する
- 解析結果有効 / 無効の状態遷移を定義する
- 再解析待ち相当の状態を整理する

### Exit Condition
- 入力変更時や解析失敗時の「結果無効」状態を表現できる

---

## Step 7. Build Status Key / Helper
- status key / helper を導入する
- `MainFrame` が status key から表示更新できるようにする
- ベタ文字列直打ちを減らす

### Exit Condition
- status が意味状態として整理されている

---

## Step 8. Add Light Tests
- state 初期値
- action state
- busy
- invalidation
- status 遷移

の軽量テストを追加または更新する

### Exit Condition
- B2 の状態契約が最小限テストで担保されている

---

## 15. Candidate File Touch Areas

repo 実態に応じて調整してよいが、変更対象は以下の範囲に留める。

- `src/gui_wx/main_frame.py`
  - state 参照
  - action state 判定
  - status 反映
- `src/gui_wx/` 配下の新規 state holder / helper
  - `ui_state.py`
  - `state_helpers.py`
  - 同等の軽量ファイル
- 必要最小限のテスト
  - wx state / action / invalidation 系

B2 では `core/`、`vmd_writer/`、`gui/settings_store.py` の意味変更を原則行わない。

---

## 16. Acceptance Criteria

以下をすべて満たしたら B2 完了とみなす。

1. `gui_wx` 配下に軽量 state holder が存在する
2. `MainFrame` が state holder を参照して action state を反映できる
3. 実用最小 state 項目が正式に定義されている
4. `current_timing_plan` と解析結果有効 / 無効状態が整理されている
5. busy lock 契約が定義されている
6. status key / helper が存在する
7. B3〜B5 が state の正本を迷わず参照できる
8. 実読込 / 実解析 / 実保存がまだ流入していない
9. 軽量テストで state / action / busy / invalidation / status の基本遷移を確認できる

---

## 17. Test Plan

## 17.1 State Initialization Check
- state holder が作れる
- 初期状態が想定どおりである
- `current_timing_plan` は未設定
- `is_busy` は false
- 解析結果有効状態は false

## 17.2 Action State Check
- 初期状態で file / run / save / parameter / recent / playback slot の状態が想定どおりである
- 未実装 UI の disabled が維持される
- 将来有効化対象の判定ロジックが存在する

## 17.3 Busy Lock Check
- `is_busy = true` で lock 対象 UI が無効化される
- `is_busy = false` で元の状態へ戻る

## 17.4 Invalidation Check
- 解析結果有効状態から invalidate できる
- invalidate 後に `current_timing_plan` と関連状態が整合する
- 再解析待ち相当の状態へ入れる

## 17.5 Status Check
- status key を設定できる
- `MainFrame` が status 表示へ反映できる
- 文字列直打ちに依存しすぎていない

## 17.6 Scope Guard Check
- file dialog が入っていない
- 実解析 worker が入っていない
- VMD save が入っていない
- settings save が入っていない
- waveform / Preview / playback 実装が入っていない

---

## 18. Risks and Control

## Risk 1. MainFrame Re-Bloating
state や判定を全部 `MainFrame` に積むと、再び肥大化する。  
**Control:** 軽量 state holder を導入する。

## Risk 2. Controller Taking Too Much Too Early
`AppController` に action 判定まで寄せると、B5 以降の責務と混線しやすい。  
**Control:** B2 では `MainFrame` 判定主体を維持する。

## Risk 3. Hidden Invalidation Semantics
`current_timing_plan = None` だけで済ませると、解析結果無効状態が曖昧になる。  
**Control:** 有効 / 無効 / 再解析待ちの意味状態を明示する。

## Risk 4. Status Becoming String Soup
ベタ文字列直打ちで増やすと、後続で整理しにくい。  
**Control:** status key / helper を導入する。

## Risk 5. B2 Slipping into B3/B4
state を作るついでに file dialog や worker を入れたくなる。  
**Control:** B2 は state 契約と UI 反映に限定する。

---

## 19. Definition of Done

MS14-B2 は、以下の状態になった時点で完了とする。

- wx 側で実用最小 state の正本がある
- `MainFrame` がその state を読んで UI action state を反映できる
- busy lock の基本契約がある
- `current_timing_plan` を含む解析結果 state が整理されている
- invalidation と再解析待ちの意味状態が存在する
- status key / helper が整理されている
- 実処理はまだ入っていない
- 軽量テストで基本遷移が確認できる

---

## 20. Handoff Notes for Implementation

- B2 は「状態契約を作る」block であり、「機能を動かす」block ではない
- `MainFrame` へ全部積まず、軽量 state holder を使うこと
- `AppController` に責務を寄せすぎないこと
- `current_timing_plan` はこの段で正式な state として位置づけること
- invalidation は明示的に扱うこと
- busy lock 範囲は広めに固定してよい
- status は key / helper ベースに寄せること
- B3 以降が state を迷わず利用できる状態を残すこと

---

## 21. Status Note

- **2026-04-10**: 実装反映、完了確認済み。`UiState` および `StatusKey` の導入、Busyロックとアクションステートの整理・テストが完了し、`Definition of Done` の要件をすべて満たして完了とした。
