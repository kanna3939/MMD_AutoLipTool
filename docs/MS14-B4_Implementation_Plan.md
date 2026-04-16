# MS14-B4 Implementation Plan

## 1. Document Control

- Document Name: `MS14-B4_Implementation_Plan.md`
- Milestone: `MS14`
- Block: `MS14-B4`
- Title: `解析実行 parity 回復`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS14-B4 では、MS14-B1 で整備した実用 UI 骨格、MS14-B2 で整理した state / action state 契約、MS14-B3 で回復した入力導線の上に、**wx 側で解析実行を安全に開始・完了・失敗処理できる最小導線** を導入する。

本 block の目的は、解析実行ボタンを押したあとに、

- UI をフリーズさせず
- 二重実行を防ぎ
- 実行中であることを UI に示し
- 成功時に `current_timing_plan` を正本結果として保持し
- 失敗時に入力状態を保ったまま再試行可能に戻す

ことを成立させる点にある。

本 block は「解析結果を表示し尽くす block」ではない。  
**MS15 の Preview / 波形 / 再生再構築を先取りせず、解析実行そのものの成立に集中する**。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 実行方式
- B4 の解析実行は **最小の worker / background thread による非同期実行** とする
- 同期実行にはしない
- UI フリーズを避けることを B4 の基本要件に含める

### 3.2 progress 表現
- B4 では **不定進捗の最小 progress dialog または busy 表示** を導入する
- 段階別の詳細進捗は不要
- 「今処理中である」ことが分かる最小表現でよい

### 3.3 キャンセル
- B4 では **キャンセルを含めない**
- non-cancelable の最小 worker 実行とする
- cancel を入れるための停止契約、途中復帰、部分結果処理は扱わない

### 3.4 解析成功時の UI 反映範囲
- 成功時は `current_timing_plan` を state の正本結果として保持する
- status を更新する
- さらに、**Preview placeholder 文言を「解析結果あり」方向へ最小更新してよい**
- 実 Preview 描画はまだ行わない

### 3.5 解析失敗時の扱い
- 失敗時は `current_timing_plan` を無効化する
- warning / status を更新する
- **TEXT / WAV の入力状態は保持する**
- 失敗で入力まで巻き戻さない

### 3.6 正式な解析結果の保持対象
- B4 で正式な解析結果として保持するのは **`current_timing_plan` のみ** とする
- 解析結果サマリ専用 state は増やさない
- 表示用の件数や短い説明は必要に応じてその場で導出する

### 3.7 busy 中 lock の実運用
- B2 で定義した busy lock 契約を **そのまま全面適用** する
- 解析中は入力変更も許可しない
- 読込、保存、パラメータ変更、recent、再生系主要ボタン置き場を lock 対象に含める

### 3.8 テスト方針
- B4 のテストは、worker 実体を簡易モック化し、
  - 成功
  - 失敗
  - busy 遷移
  - 二重実行防止
  - status 更新
  - `current_timing_plan` 反映 / 無効化
  を中心に確認する
- 重い実解析依存の統合テストは主対象にしない

---

## 4. Goal

MS14-B4 の完了条件は、以下を満たすこととする。

1. wx 側から解析実行を開始できる
2. 解析は background thread / worker で動作する
3. 実行中に UI フリーズを前提としない
4. 実行中であることを示す最小 progress / busy 表示がある
5. busy 中 lock が全面適用される
6. 二重実行防止がある
7. 成功時に `current_timing_plan` が更新される
8. 成功時に status と Preview placeholder 文言が最小更新される
9. 失敗時に `current_timing_plan` が無効化される
10. 失敗時も TEXT / WAV 入力状態は保持される
11. warning / status が成功 / 失敗に応じて整合する
12. VMD save / settings save / Preview 実描画 / 波形実描画 / playback が流入していない

---

## 5. In Scope

MS14-B4 に含めるものは以下とする。

- 解析実行ボタン導線の接続
- 解析 worker / background thread の最小導入
- worker 開始 / 完了 / 失敗の最小イベント導線
- busy state の実運用
- non-cancelable progress / busy 表示
- 二重実行防止
- `current_timing_plan` の成功時反映
- 失敗時 invalidate
- status 更新
- Preview placeholder 文言の最小更新
- 成功 / 失敗 / busy / 二重実行防止の軽量テスト

---

## 6. Out of Scope

MS14-B4 では以下を行わない。

- VMD save dialog 実装
- `generate_vmd_from_text_wav(...)` 実行
- recent files 永続化
- settings save
- `last_vmd_output_dir` 更新 / 保存
- waveform 実描画
- Preview 実描画
- playback 実装
- Zoom / Pan / shared viewport
- キャンセル付き進捗 UI
- 詳細 progress 段階表示
- 解析結果サマリ専用 state 導入
- テーマ / i18n 本格対応
- 大規模 worker 基盤化
- event bus / job queue の導入

---

## 7. Expected Functional Boundary

B4 は **解析実行導線を回復する block** である。  
ここでやるべきことは、「入力が揃った状態から、解析結果が成功 / 失敗として state に戻る」までの導線を成立させることであり、「結果の豊かな表示や保存」ではない。

責務の切り分けは以下のとおり。

- **B1:** 実用 UI 骨格拡張
- **B2:** 状態管理と action state 回復
- **B3:** 入力導線 parity 回復
- **B4:** 解析実行 parity 回復
- **B5:** 出力・履歴・settings save parity 回復
- **B6:** 統合整理と parity closeout

したがって B4 では、B5 の保存責務、MS15 の表示再構築責務を持ち込まない。

---

## 8. Execution Policy

## 8.1 非同期実行の位置づけ
- 解析は UI thread で直接走らせない
- 最小 worker / background thread へ切り出す
- UI への反映は UI thread 側へ戻して処理する
- 実装方式は repo / wx の流儀に合わせてよいが、**UI thread と worker thread の境界を明確に保つ**

## 8.2 worker の責務
worker の責務は以下に限定する。

- 解析関数を実行する
- 成功時に結果を返す
- 失敗時に例外または失敗結果を返す

worker 自身に UI 更新責務を持たせない。

## 8.3 UI 側の責務
UI 側では以下を行う。

- 実行開始前の入力条件確認
- busy 開始
- progress / busy 表示開始
- 二重実行防止
- 完了時の state 反映
- 失敗時の invalidate / warning / status 反映
- progress / busy 表示終了
- action state 再評価

---

## 9. Input Preconditions

B4 では、解析開始前に最低限以下を確認する。

- TEXT が有効に読込済みである
- WAV が有効に読込済みである
- `selected_vowel_content` が利用可能である
- `selected_wav_analysis` が利用可能である
- busy 中でない
- 二重実行状態でない

これらが満たされない場合、worker を起動しない。

---

## 10. Busy / Progress Policy

## 10.1 busy の意味
B4 における busy は「解析実行中」を表す正式状態とする。

## 10.2 progress 表示
- 不定進捗の最小 progress dialog または同等の busy 表示を導入してよい
- キャンセルボタンは不要
- 「処理中である」ことだけを伝えられればよい

## 10.3 busy 開始時
- `is_busy = true`
- lock 対象 UI を無効化
- progress / busy 表示を開始
- status を busy 系へ遷移
- 解析開始要求を 1 回だけ受け付ける

## 10.4 busy 終了時
- `is_busy = false`
- progress / busy 表示を閉じる
- lock を解除
- 成功 / 失敗に応じて status を更新
- action state を再評価する

---

## 11. Success / Failure Policy

## 11.1 成功時
成功時は、以下を行う。

- `current_timing_plan` を更新する
- 解析結果有効状態へ遷移する
- 再解析待ち状態を解除する
- status を成功側へ更新する
- Preview placeholder 文言を「解析結果あり」方向へ最小更新する
- busy を終了する
- action state を再評価する

## 11.2 失敗時
失敗時は、以下を行う。

- `current_timing_plan` を無効化する
- 解析結果有効状態を false にする
- 必要なら再解析待ち状態を適切に整える
- warning を表示する
- status を失敗側へ更新する
- TEXT / WAV の入力状態は保持する
- busy を終了する
- action state を再評価する

## 11.3 入力保持
失敗しても、

- `selected_text_path`
- `selected_wav_path`
- `selected_text_content`
- `selected_hiragana_content`
- `selected_vowel_content`
- `selected_wav_analysis`

は保持する。  
これにより、ユーザーは再読込せず再試行できる。

---

## 12. Result Policy

## 12.1 正本結果
B4 での正本結果は `current_timing_plan` とする。

## 12.2 増やさないもの
B4 では以下を追加しない。

- 解析結果サマリ専用 state
- 件数キャッシュ
- 独自の成功メタデータオブジェクト
- Preview 用別結果キャッシュ

必要な表示文言は `current_timing_plan` からその場で導出してよい。

---

## 13. UI Reflection Policy

## 13.1 成功時に更新してよいもの
- status
- Preview placeholder 文言
- 必要最小限の結果あり表示

## 13.2 成功時に更新しないもの
- waveform 実描画
- Preview 実描画
- playback 位置
- VMD 保存結果
- recent files 永続化

## 13.3 失敗時に更新してよいもの
- status
- warning
- Preview placeholder 文言の失敗 / 未解析方向への戻し
- `current_timing_plan` invalidate

---

## 14. Design Policy

## 14.1 Recover Execution, Not Presentation
B4 は「解析を走らせる」block であり、「解析結果を見せ切る」block ではない。

## 14.2 Keep Worker Minimal
worker は最小に保ち、UI と混ぜない。

## 14.3 Preserve Retryability
失敗時も入力状態を保持し、再試行可能性を優先する。

## 14.4 Use B2 Busy Contract as-Is
B2 の busy lock 契約を広めのまま実運用へ載せる。  
解析中に入力変更を許さない。

## 14.5 Do Not Invent New Result State
正本結果は `current_timing_plan` だけで十分とする。

---

## 15. Step Breakdown

## Step 1. Confirm B2/B3 Contracts
- B2 の state holder / busy / invalidation / status 契約を確認する
- B3 の入力成功状態が B4 の開始条件として十分か確認する
- 解析開始前に必要な state を整理する

### Exit Condition
- B4 の開始条件と終了時反映先が明確になっている

---

## Step 2. Build Run Analysis Entry
- 解析実行ボタンから B4 導線へ入れるようにする
- 開始前前提条件を確認する
- 不足時は worker を起動しない
- 二重実行防止を入れる

### Exit Condition
- 解析開始入口が UI から到達可能になっている

---

## Step 3. Introduce Minimal Worker / Background Thread
- 最小の解析 worker を導入する
- background thread で解析関数を呼ぶ
- 成功 / 失敗の戻り経路を用意する
- UI thread 更新と worker 実行を混在させない

### Exit Condition
- UI フリーズ前提ではない解析導線がある

---

## Step 4. Build Busy / Progress Lifecycle
- 実行開始時に busy を開始する
- 不定進捗の最小 progress / busy 表示を出す
- busy 中 lock を全面適用する
- 実行終了で busy を確実に解除する

### Exit Condition
- busy と progress の開始 / 終了が一貫している

---

## Step 5. Build Success Handling
- `current_timing_plan` を更新する
- 解析結果有効状態へ遷移する
- status を更新する
- Preview placeholder 文言を最小更新する
- action state を再評価する

### Exit Condition
- 解析成功時の正本結果反映と最小 UI 反映がある

---

## Step 6. Build Failure Handling
- `current_timing_plan` を invalidate する
- warning を出す
- status を更新する
- 入力 state を保持したまま戻る
- action state を再評価する

### Exit Condition
- 解析失敗時の再試行可能な戻り方が成立している

---

## Step 7. Add Light Worker/State Tests
- 成功
- 失敗
- busy 遷移
- 二重実行防止
- `current_timing_plan` 反映 / 無効化
- status 更新

を軽量テストで確認する

### Exit Condition
- B4 の worker 契約と状態遷移が最小テストで担保されている

---

## 16. Candidate File Touch Areas

repo 実態に応じて調整してよいが、変更対象は以下の範囲に留める。

- `src/gui_wx/main_frame.py`
  - 解析実行入口
  - busy / progress 表示
  - 成功 / 失敗反映
- `src/gui_wx/app_controller.py`
  - B5 以降へ責務が漏れない範囲で、必要最小限の橋渡しだけ許容
- `src/gui_wx/` 配下の新規 worker 補助ファイル
  - 例: `analysis_worker.py`
- B2 の state / status helper
- 必要最小限のテスト
  - worker / busy / success / failure 系

B4 では `core/` の意味変更を原則行わない。

---

## 17. Acceptance Criteria

以下をすべて満たしたら B4 完了とみなす。

1. wx 側から解析実行を開始できる
2. 解析は background thread / worker で動作する
3. 実行中は不定進捗の最小 progress / busy 表示がある
4. busy 中 lock が全面適用される
5. 二重実行防止がある
6. 成功時に `current_timing_plan` が正本結果として保持される
7. 成功時に status と Preview placeholder 文言が最小更新される
8. 失敗時に `current_timing_plan` が無効化される
9. 失敗時も入力状態は保持される
10. VMD save / settings save / Preview 実描画 / waveform 実描画 / playback が流入していない

---

## 18. Test Plan

## 18.1 Success Path
- 開始条件を満たした状態で解析を開始できる
- busy が始まる
- worker が成功を返す
- `current_timing_plan` が更新される
- busy が解除される
- status が成功側へ更新される

## 18.2 Failure Path
- worker が失敗を返す
- `current_timing_plan` が invalidate される
- warning / status が更新される
- busy が解除される
- TEXT / WAV 入力状態が保持される

## 18.3 Busy Lock
- 解析中に読込 / 保存 / パラメータ / recent / 再生系置き場が lock される
- 終了後に復帰する

## 18.4 Double Start Guard
- 実行中に再度解析開始要求を受けても二重起動しない

## 18.5 Scope Guard
- VMD save が入っていない
- settings save が入っていない
- Preview / waveform 実描画が入っていない
- playback が入っていない
- cancel 契約が入っていない

---

## 19. Risks and Control

## Risk 1. B4 Slipping into MS15
解析成功時に Preview / waveform を実描画したくなる。  
**Control:** placeholder 文言更新までに留める。

## Risk 2. Worker/UI Boundary Blur
worker 側で UI 更新を始めると責務が濁る。  
**Control:** UI 更新は UI thread 側だけで行う。

## Risk 3. Failure Resetting Too Much
失敗時に入力まで消すと再試行性が悪化する。  
**Control:** `current_timing_plan` だけを無効化し、入力 state は保持する。

## Risk 4. Busy Lock Too Narrow
解析中に入力変更を許すと結果反映が衝突しやすい。  
**Control:** B2 の全面 lock 契約をそのまま使う。

## Risk 5. Test Instability
実解析依存の重い統合テストに寄せると不安定になる。  
**Control:** worker 契約と状態遷移はモック中心で確認する。

---

## 20. Definition of Done

MS14-B4 は、以下の状態になった時点で完了とする。

- wx 側で解析実行が開始できる
- worker / background thread で非同期に動く
- 実行中の最小 busy / progress 表示がある
- busy 中 lock が全面適用される
- 成功時に `current_timing_plan` が更新される
- 失敗時に `current_timing_plan` が invalidate される
- 入力 state は失敗でも保持される
- status と Preview placeholder 文言の最小反映がある
- B5 / MS15 の内容はまだ流入していない

---

## 21. Handoff Notes for Implementation

- B4 は「解析を走らせて戻す」block であり、「解析結果を豊かに見せる」block ではない
- 非同期実行は必須、同期実行へ戻さないこと
- progress 表現は不定進捗で十分
- cancel を入れないこと
- 成功時の正本結果は `current_timing_plan` のみとすること
- 失敗時に入力を消さないこと
- Preview placeholder の更新はよいが、実描画しないこと
- B5 が保存導線、MS15 が表示再構築を受け取れるよう境界を守ること

---

## 22. Status Note

- **2026-04-11**: 実装反映、完了確認済み。非同期解析用 `AnalysisWorker` の導入、不定進捗用 `wx.ProgressDialog` の表示とBusy中ロック制御の徹底が行われた。解析成功時の `current_timing_plan` 更新・プレースホルダ最小更新と、失敗時の状況復帰が要件通り実装され、対象スコープ（保存やプレビュー実描画を含めない）を遵守しつつ完了した。
