# MS14-B3 Implementation Plan

## 1. Document Control

- Document Name: `MS14-B3_Implementation_Plan.md`
- Milestone: `MS14`
- Block: `MS14-B3`
- Title: `入力導線 parity 回復`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS14-B3 では、MS14-B1 で拡張した実用 UI 骨格と、MS14-B2 で整理した state / action state 契約の上に、**TEXT / WAV の入力導線を wx 側で実動化**する。

本 block の目的は、入力成功時に必要な state と UI を正しく更新し、後続 block が解析実行や保存導線を自然に接続できる状態を作ることである。

本 block では、以下を回復対象とする。

- TEXT 読込
- WAV 読込
- text / hiragana / vowel の反映
- WAV info の反映
- 読込成功 / 失敗に応じた state 遷移
- 読込成功後の action state 変化
- recent files の**メモリ上更新**
- dialog dir の**メモリ上更新**
- counterpart auto load
- silent restore / suppress_warning 的な最小静音導線

一方で、本 block の目的は解析や保存を行うことではない。  
**B4 の解析実行、B5 の VMD 保存・settings save 永続化には踏み込まない**。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 recent files の扱い
- B3 では、TEXT / WAV 読込成功時に **recent リストのメモリ上更新** まで含める
- ただし、settings save や永続化は B5 に送る
- B3 では「入力成功導線の一部として recent を更新する」が、「保存はしない」

### 3.2 counterpart auto load
- B3 に含める
- 主読込成功後に、同一フォルダ・同一 stem の相方を 1 回だけ試行する
- 対象は `.txt` と `.wav` の相補関係とする
- 既読込側は上書きしない
- 再連鎖させない

### 3.3 読込失敗時の warning 粒度
- 失敗種別ごとに最小限の個別メッセージを持つ
- 少なくとも以下は分けてよい
  - 空パス
  - 非存在
  - ディレクトリ選択
  - テキスト変換不能
  - WAV 解析不能
  - WAV プレビュー不能
  - 想定外例外
- ただし、過剰に細分化しすぎない

### 3.4 TEXT 読込時の preview 反映範囲
- `text`
- `hiragana`
- `vowel`

の 3 つすべてを更新対象に含める  
- `text → hiragana → vowel` を B3 で成立させる

### 3.5 WAV 読込時の表示反映範囲
- `WAV path`
- `WAV info`
- 右側波形 placeholder 文言更新

を含める  
- 実波形描画は入れない
- 波形表示予定領域に、状態を示す最小反映だけ行う

### 3.6 読込成功時の action state
- B2 で作成した state 契約に従い、読込成功時に action state を変化させる
- 例えば、必要入力が揃ったときに `解析実行` が有効条件を満たすような遷移を行う
- ただし、B4 / B5 の実処理にはまだ踏み込まない

### 3.7 dialog dir の扱い
- B3 では
  - `last_text_dialog_dir`
  - `last_wav_dialog_dir`

の **メモリ上更新** を行う  
- 永続化は行わない

### 3.8 silent restore / suppress_warning
- B3 で最小限含める
- auto load や内部再読込相当で、失敗時に過剰 warning を出さない経路を持つ
- 通常の明示的読込では warning を出す
- silent 経路は B3 の範囲内で最小に留める

---

## 4. Goal

MS14-B3 の完了条件は、以下を満たすこととする。

1. wx 側で TEXT 読込が動く
2. wx 側で WAV 読込が動く
3. TEXT 読込成功時に `text / hiragana / vowel` が更新される
4. WAV 読込成功時に `WAV path / WAV info / 波形 placeholder 文言` が更新される
5. 読込成功 / 失敗に応じて state が整合する
6. 読込成功時に action state が想定どおり変化する
7. recent files がメモリ上で更新される
8. dialog dir がメモリ上で更新される
9. counterpart auto load が 1 回だけ安全に動作する
10. silent restore / suppress_warning 的な最小静音経路がある
11. 実解析 / 実保存 / settings save 永続化が流入していない

---

## 5. In Scope

MS14-B3 に含めるものは以下とする。

- TEXT open dialog
- WAV open dialog
- TEXT 読込成功 / 失敗導線
- WAV 読込成功 / 失敗導線
- text → hiragana → vowel の反映
- WAV analysis 結果の反映
- 右側波形 placeholder 文言更新
- state 更新
- action state 再評価
- recent files のメモリ上更新
- dialog dir のメモリ上更新
- counterpart auto load
- silent restore / suppress_warning 相当の最小静音経路
- warning / status の最小更新
- 失敗時 rollback / invalidate の整理
- 必要最小限の入力導線テスト

---

## 6. Out of Scope

MS14-B3 では以下を行わない。

- 解析 worker 実装
- `build_vowel_timing_plan(...)` 実行
- `current_timing_plan` の実生成
- VMD save dialog 実装
- `generate_vmd_from_text_wav(...)` 実行
- recent files の settings save 永続化
- `last_vmd_output_dir` 保存
- settings save
- waveform 実描画
- Preview 実描画
- playback 実装
- Zoom / Pan / shared viewport
- theme / i18n 本格対応
- 大規模 state 管理再編

---

## 7. Expected Functional Boundary

B3 は **入力導線を回復する block** である。  
ここでやるべきことは、「TEXT / WAV を選んだ結果が state と UI にどう流れ込むか」を回復することであり、「解析や保存を行うこと」ではない。

責務の切り分けは以下のとおり。

- **B1:** 実用 UI 骨格拡張
- **B2:** 状態管理と action state 回復
- **B3:** 入力導線 parity 回復
- **B4:** 解析実行 parity 回復
- **B5:** 出力・履歴・settings save parity 回復
- **B6:** 統合整理と parity closeout

したがって B3 では、B4 / B5 の内容を前倒しで入れず、**入力成功 / 失敗とその反映** に限定する。

---

## 8. Input Policy

## 8.1 TEXT 読込の位置づけ
TEXT 読込は、以下を一連の入力成功導線として扱う。

- path 確定
- 内容読込
- `text` 表示更新
- `hiragana` 生成と表示更新
- `vowel` 生成と表示更新
- 必要 state 更新
- action state 再評価
- recent 更新
- dialog dir 更新

## 8.2 WAV 読込の位置づけ
WAV 読込は、以下を一連の入力成功導線として扱う。

- path 確定
- WAV analysis
- `WAV info` 更新
- 波形 placeholder 文言更新
- 必要 state 更新
- action state 再評価
- recent 更新
- dialog dir 更新

## 8.3 既存入力の扱い
- 主読込成功時に、その種別の state は上書きしてよい
- 相方の state は、counterpart auto load でのみ追加読込される
- 既読込の相方を auto load で勝手に上書きしない

---

## 9. Error / Warning Policy

## 9.1 基本方針
- 明示的な通常読込では、失敗時に warning を出す
- auto load や内部読込では、失敗時に warning を抑制できる経路を持つ
- 失敗時に state を壊したまま残さない

## 9.2 粒度
以下は個別 warning 対象として扱ってよい。

### TEXT
- 空パス
- 非存在
- ディレクトリ選択
- 読込エラー
- 未対応エンコード / 変換不能
- 変換結果が空に近いケース
- 想定外例外

### WAV
- 空パス
- 非存在
- ディレクトリ選択
- 解析エラー
- プレビュー用読み込み失敗
- 想定外例外

## 9.3 silent restore / suppress_warning
- counterpart auto load 失敗では、通常 warning を出さない
- 内部再読込や静音経路では、必要以上に UI を荒らさない
- ただし、state 不整合を残さないことを優先する

---

## 10. State Transition Policy

## 10.1 読込成功時
読込成功時には、B2 で整理した state を正本として更新する。

### TEXT 読込成功時
- `selected_text_path`
- `selected_text_content`
- `selected_hiragana_content`
- `selected_vowel_content`

を更新する  
- 必要に応じて解析結果を invalidate する
- action state を再評価する

### WAV 読込成功時
- `selected_wav_path`
- `selected_wav_analysis`

を更新する  
- 必要に応じて解析結果を invalidate する
- action state を再評価する

## 10.2 読込失敗時
- 半端な state を残さない
- silent restore 経路では、既存状態を壊さず戻す判断を持ってよい
- 通常 warning 経路では、失敗状態が UI に明示されるようにする

## 10.3 invalidate
TEXT または WAV の変更は、既存 `current_timing_plan` を無効化しうる。  
B3 では、B2 の invalidation helper を使って、解析結果有効 / 無効状態を正しく更新する。

---

## 11. Recent / Dialog Directory Policy

## 11.1 recent files
- 読込成功時に recent リストをメモリ上で更新する
- 重複時は先頭寄せなど既存方針に沿ってよい
- 上限や表示メニュー反映は B3 で扱ってよい
- **永続化はしない**

## 11.2 dialog dir
- TEXT 読込成功時に `last_text_dialog_dir` をメモリ上更新する
- WAV 読込成功時に `last_wav_dialog_dir` をメモリ上更新する
- **永続化はしない**

---

## 12. Counterpart Auto Load Policy

## 12.1 基本方針
- 主読込成功後に、同一フォルダ・同一 stem の相方を 1 回だけ試行する
- `.txt` ↔ `.wav` の相補を対象とする
- 主導線の読込成功を邪魔しない

## 12.2 制約
- 既読込の相方を上書きしない
- 失敗時に warning を出しすぎない
- 再連鎖しない
- auto load 成功時も、通常成功導線に準じて state / UI を更新してよい

## 12.3 B3 での位置づけ
counterpart auto load は、利便性の一部として B3 に含める。  
ただし、複雑な探索や複数候補解決には進まない。

---

## 13. Display Update Policy

## 13.1 TEXT 側
B3 で更新対象に含める。

- TEXT path
- text preview
- hiragana preview
- vowel preview

## 13.2 WAV 側
B3 で更新対象に含める。

- WAV path
- WAV info
- 波形 placeholder 文言

## 13.3 Preview 側
Preview 実描画はまだ行わない。  
必要なら placeholder 文言更新程度に留める。

---

## 14. Action State Policy

## 14.1 B3 でやること
B2 で整理した action state 契約を、読込成功 / 失敗によって実際に動かす。

### 例
- TEXT だけ読込済み
- WAV だけ読込済み
- TEXT / WAV 両方読込済み
- 解析結果無効化済み
- busy 中

などに応じて UI 状態を再評価する

## 14.2 B3 でやらないこと
- 解析実行そのもの
- 保存そのもの
- 再生そのもの

---

## 15. Design Policy

## 15.1 Recover Input First, Not Processing
B3 は入力導線の回復に集中する。  
解析や保存を混ぜない。

## 15.2 Reflect Success Immediately
読込成功時は、対応する UI / state / recent / dialog dir を即時更新する。

## 15.3 Keep Silent Paths Minimal
counterpart auto load のための静音経路は入れるが、複雑化しない。

## 15.4 Use B2 Contracts
B2 の state / action / invalidation 契約を流用し、独自ルールを増やさない。

## 15.5 Preserve MS15 Scope
波形 / Preview の実描画は入れない。  
placeholder 文言更新に留める。

---

## 16. Step Breakdown

## Step 1. Confirm B1/B2 Surfaces and Contracts
- B1 で増えた UI 骨格を確認する
- B2 の state holder / invalidation / action state 契約を確認する
- B3 で更新すべき setter / helper を把握する

### Exit Condition
- B3 の入力成功 / 失敗導線がどこへ反映されるか明確になっている

---

## Step 2. Build TEXT Open Flow
- TEXT open dialog を接続する
- path 妥当性確認を行う
- ファイル内容を読み込む
- 読込失敗時 warning を処理する

### Exit Condition
- TEXT 選択から読込成功 / 失敗までの最小導線がある

---

## Step 3. Build TEXT Conversion Reflection
- `text`
- `hiragana`
- `vowel`

を更新する  
- state を更新する
- invalidation を反映する
- action state を再評価する

### Exit Condition
- TEXT 読込成功時に text 系表示と state が整合して更新される

---

## Step 4. Build WAV Open Flow
- WAV open dialog を接続する
- path 妥当性確認を行う
- WAV analyze を行う
- 必要な preview 用取得があるなら最小に留める
- 失敗時 warning を処理する

### Exit Condition
- WAV 選択から読込成功 / 失敗までの最小導線がある

---

## Step 5. Build WAV Reflection
- `WAV path`
- `WAV info`
- 波形 placeholder 文言

を更新する  
- state を更新する
- invalidation を反映する
- action state を再評価する

### Exit Condition
- WAV 読込成功時に audio 系表示と state が整合して更新される

---

## Step 6. Build Recent and Dialog Dir Memory Update
- TEXT / WAV 読込成功時に recent を更新する
- `last_text_dialog_dir` / `last_wav_dialog_dir` をメモリ上更新する
- 永続化は行わない

### Exit Condition
- 読込成功導線として recent / dialog dir のメモリ反映がある

---

## Step 7. Build Counterpart Auto Load
- 主読込成功後に相方候補を 1 回だけ試行する
- suppress_warning 的静音経路で失敗を吸収する
- 既読込相方の上書きを防ぐ
- 再連鎖を防ぐ

### Exit Condition
- counterpart auto load が最小安全形で成立している

---

## Step 8. Add Light Tests
- TEXT 読込成功 / 失敗
- WAV 読込成功 / 失敗
- text / hiragana / vowel 反映
- WAV info / placeholder 文言更新
- recent / dialog dir メモリ更新
- action state 遷移
- silent path

の軽量テストを追加または更新する

### Exit Condition
- B3 の入力導線が最小限テストで担保されている

---

## 17. Candidate File Touch Areas

repo 実態に応じて調整してよいが、変更対象は以下の範囲に留める。

- `src/gui_wx/main_frame.py`
  - file dialog 接続
  - 表示更新
  - action state 再評価
- `src/gui_wx/` 配下の state / helper
  - B2 で追加した state holder / status helper
- 必要なら `src/gui_wx/` 配下の入力補助ファイル
- 必要最小限のテスト
  - 読込成功 / 失敗
  - 反映
  - silent path

B3 では `core/` を意味変更せず、既存関数呼出に留める。

---

## 18. Acceptance Criteria

以下をすべて満たしたら B3 完了とみなす。

1. wx 側で TEXT 読込が動く
2. wx 側で WAV 読込が動く
3. TEXT 読込成功時に `text / hiragana / vowel` が反映される
4. WAV 読込成功時に `WAV info` と波形 placeholder 文言が反映される
5. 読込成功 / 失敗時に state が整合する
6. 読込成功時に action state が再評価される
7. recent files がメモリ上更新される
8. dialog dir がメモリ上更新される
9. counterpart auto load が 1 回だけ安全に試行される
10. suppress_warning 的な静音経路がある
11. 実解析 / 実保存 / settings save 永続化が流入していない

---

## 19. Test Plan

## 19.1 TEXT Load Success
- TEXT を選べる
- 内容が読める
- `text / hiragana / vowel` が更新される
- recent / dialog dir がメモリ更新される
- action state が更新される

## 19.2 TEXT Load Failure
- 空パス
- 非存在
- ディレクトリ
- 読込不能
- 変換不能
- 想定外例外

に対して warning と state 整合が保たれる

## 19.3 WAV Load Success
- WAV を選べる
- WAV analyze が通る
- `WAV info` が更新される
- 波形 placeholder 文言が更新される
- recent / dialog dir がメモリ更新される
- action state が更新される

## 19.4 WAV Load Failure
- 空パス
- 非存在
- ディレクトリ
- 解析不能
- プレビュー取得不能
- 想定外例外

に対して warning と state 整合が保たれる

## 19.5 Counterpart Auto Load
- 主読込成功後に相方を 1 回だけ試行する
- 既読込相方を上書きしない
- 失敗時に warning を出しすぎない
- 再連鎖しない

## 19.6 Scope Guard Check
- 実解析が入っていない
- VMD save が入っていない
- settings save 永続化が入っていない
- waveform / Preview 実描画が入っていない
- playback 実装が入っていない

---

## 20. Risks and Control

## Risk 1. B3 Slipping into B4
読込後にそのまま解析まで行きたくなる。  
**Control:** B3 は入力反映まで。解析実行は B4。

## Risk 2. B3 Slipping into B5
recent や dialog dir をそのまま保存したくなる。  
**Control:** B3 はメモリ更新のみ。永続化は B5。

## Risk 3. Warning Noise Explosion
counterpart auto load 失敗で毎回 warning が出ると UX が悪い。  
**Control:** 最小静音経路を導入する。

## Risk 4. State Half-Update
一部 UI だけ更新され、state が中途半端に残る危険がある。  
**Control:** 成功 / 失敗ごとの state 遷移を明示する。

## Risk 5. Preview / Waveform Scope Leakage
波形 placeholder 更新のついでに実描画へ行きたくなる。  
**Control:** 文言更新だけに留める。

---

## 21. Definition of Done

MS14-B3 は、以下の状態になった時点で完了とする。

- wx 側で TEXT / WAV の入力導線が動く
- TEXT 読込成功時に `text / hiragana / vowel` が反映される
- WAV 読込成功時に `WAV info` と波形 placeholder 文言が反映される
- state / action / invalidation 契約が読込導線と結びつく
- recent / dialog dir がメモリ上更新される
- counterpart auto load と静音経路が最小形で成立する
- 実解析 / 実保存 / 永続化はまだ入っていない

---

## 22. Handoff Notes for Implementation

- B3 は「入力導線の回復」block であり、「解析 block」ではない
- recent 更新は入れてよいが、保存はしないこと
- dialog dir 更新は入れてよいが、保存はしないこと
- counterpart auto load は 1 回だけ、安全に実装すること
- 静音経路は最小に留めること
- `text / hiragana / vowel` は B3 の時点で揃えること
- WAV 側は info と placeholder 文言更新までに留めること
- B4 が解析実行、B5 が保存と永続化を受け取れるように境界を守ること

---

## 23. Status Note

- **2026-04-10**: 実装反映、完了確認済み。TEXT/WAVのファイルダイアログ、抽出処理の接続、`UiState` と各種プレビューへの反映、および Counterpart Auto Load （メモリ上Recent更新含む）を完了し、`Definition of Done` を全て満たした。
