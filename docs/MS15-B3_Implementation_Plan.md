# MS15-B3_Implementation_Plan

## 1. Document Control

- Document Name: `MS15-B3_Implementation_Plan.md`
- Milestone: `MS15`
- Block: `MS15-B3`
- Title: `再生基盤と再生位置同期`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS15-B3 では、MS14 時点で stub に留められている再生操作を、**wx 主系での最小再生基盤**へ置き換え、再生位置を waveform / Preview へ同期反映できる状態を成立させる。

本 block の目的は、再生 UX 全体を一気に完成させることではない。  
MS15-B3 は、後続 block であるオートスクロールと状態統合を安全に載せられるように、以下を最小範囲で成立させるための block とする。

- WAV の再生開始 / 停止が実動すること
- 再生位置を取得し、waveform / Preview に反映できること
- 最小の playback state が存在すること
- 再生終了時と Stop 時の挙動が固定されていること
- MS14 の core workflow を壊さないこと

B3 は、**再生基盤と再生位置同期**に限定する。  
オートスクロール、shared viewport、Zoom / Pan、Pause、任意シーク、ループ再生、再生中 GUI の大規模最適化は本 block に含めない。

---

## 3. Fixed Decisions

### 3.1 再生バックエンド方針
B3 では、**wx 主系で扱いやすい標準寄りの仕組みを優先し、追加依存を増やさない**方針とする。

- B3 時点では mp3 や高度拡張は対象外
- 再生対象は既存入力導線上の WAV に限定する
- 外部再生専用ライブラリの導入を前提にしない
- ただし、実装候補の比較の結果、wx / 標準寄りの構成だけで B3 の成立条件を満たせないことが判明した場合は、独断で依存追加せず停止して報告する

### 3.2 再生位置更新周期
B3 の再生位置更新周期は、**約 50ms（20fps 相当）**を基本とする。

- 位置同期はこの周期で waveform / Preview へ通知する
- 50ms は B3 の最小同期周期として固定する
- より高頻度な滑らかさ改善は B3 の責務に含めない
- 後続 block で調整余地を残すが、B3 plan 上の基準周期は 50ms とする

### 3.3 位置更新タイマーのスレッドモデル
B3 の位置更新タイマーは、**wx のメインスレッド（イベントループ）上で動作するタイマー**を使用する。

- waveform / Preview への UI 更新はメインスレッドから行う
- `threading.Timer` や任意 worker thread から UI 更新を直接行わない
- B3 における位置同期ループは、wx UI thread 上の timer/event を正本とする

### 3.4 再生終了時の挙動
再生終了時は、

- 再生を停止状態へ遷移させる
- 表示カーソルを **`0.0 sec`** に戻す
- playback state も「停止・先頭位置」へ戻す

とする。

終端位置で止める挙動は採らない。

### 3.5 再生開始位置
B3 における再生開始位置は、**常に `0.0 sec`** とする。

- 直前位置からの再開は行わない
- 任意シークや可変開始位置は導入しない
- Play 操作は毎回「先頭から再生」を意味する

### 3.6 再生中の Play 再押下
**再生中に Play が再押しされた場合は、要求を無視する。**

- 既存再生を継続する
- 停止して先頭再開は行わない
- playback state と表示カーソルは変更しない
- B5 で Play ボタン活性規則が整理されるまでは、B3 側ロジックで無害化する

### 3.7 busy との衝突ルール
B3 における busy との衝突ルールは、以下で固定する。

- **busy 中は再生禁止**
- **再生中に解析開始が必要な場合は、先に再生を停止してから進める**
- 解析と再生を同時に走らせない

このルールは B3 時点での最小安全策として採用する。  
B5 ではこのルールを action state / status 表示へ統合するが、B3 ではまず実行事実として守る。

### 3.8 busy ガードの責務範囲
B3 が担当する busy ガードは、**ロジックレベルの再生拒否 / 停止処理**である。

- Play ボタンの enable/disable 規則の最終整理は B5 に送る
- B3 時点では、ボタン状態が未整理でも、ロジック上再生開始を拒否できればよい
- したがって B3 の必須責務は **早期リターン / 停止処理** であり、UI 活性制御の最終形ではない

### 3.9 再生可能条件
B3 における **`再生可能`** の定義は、少なくとも以下を満たす状態とする。

- `selected_wav_path` が存在する
- 再生バックエンドがその WAV を開ける
- busy ではない

すなわち、B3 の再生可能条件は **`analysis_result_valid == True` を要求しない**。  
Preview の valid 状態と再生可能条件は切り分ける。

### 3.10 再生開始失敗時の最小処理
`selected_wav_path` が存在しても、再生バックエンドがその WAV を開けない、または再生開始に失敗した場合は、以下で扱う。

- 再生は開始しない
- `is_playing` を `True` にしない
- `playback_position_sec` を進めない
- waveform / Preview のカーソルを進めない
- 既存の status / error 通知導線へ、**最小の失敗メッセージ**を渡す
- モーダルダイアログは B3 必須要件には含めない

### 3.11 playback state の最小構成
B3 では、**再生の事実そのもの**を表す最小 playback state を導入する。  
少なくとも以下を持つ前提で整理する。

- `is_playing: bool`
- `playback_position_sec: float`
- `loaded_playback_path` またはそれと等価な再生対象識別
- 必要なら `playback_timer_running: bool` 相当の内部状態

B3 ではこれ以上の複雑な state machine を導入しない。

### 3.12 再生対象変更時の扱い
**再生中に `selected_wav_path` が変更された場合は、再生を停止し、`0.0 sec` へ戻す。**

- `loaded_playback_path` と `selected_wav_path` の乖離を残したまま再生継続しない
- 新しい `selected_wav_path` は、次回 Play 要求時の対象として扱う
- 入力 WAV 差し替えは B3 では「再生継続」ではなく「停止して基準状態へ戻る」で統一する

### 3.13 waveform / Preview への同期 API
B3 は、B1 / B2 で用意された現在位置反映 API を利用して同期する。  
少なくとも以下を前提とする。

- waveform 側: `set_playback_position_sec(position_sec: float) -> None`
- waveform 側: `clear_playback_cursor() -> None`
- Preview 側: `set_playback_position_sec(position_sec: float) -> None`
- Preview 側: `clear_playback_cursor() -> None`

B3 自身は再生位置の**供給側**であり、描画ロジックそのものは持たない。

### 3.14 Stop 操作の意味
Stop 操作は、以下をまとめて行うものとする。

1. 再生を停止する
2. 再生位置更新を止める
3. playback state を停止状態へ戻す
4. waveform / Preview の表示カーソルを `0.0 sec` に戻す

Stop は「一時停止」ではない。

### 3.15 B4 / B5 との責務境界
B3 は、**再生の事実と位置同期を成立させる block**である。  
したがって以下は B3 の責務外とする。

- 右端接近時の追従表示
- 可視範囲の自動移動
- Play / Stop の enable/disable 規則の全体整理
- 再解析・再読込時の invalidate ルールの全体整理
- status 文言の統合

これらは B4 / B5 に送る。

---

## 4. Goal

本節の項目群を、**MS15-B3 の canonical completion criteria** とする。  
後続の `13. Acceptance Criteria` および `16. Definition of Done` は意味差なしで本節を再掲する。

1. `selected_wav_path` が存在し、再生バックエンドがその WAV を開ける場合に再生開始できる
2. Stop 操作により再生停止できる
3. 再生位置を約 50ms 周期で取得できる
4. 再生位置が waveform / Preview の両方へ同期反映される
5. 再生開始位置は常に `0.0 sec` である
6. 再生終了時は停止し、表示カーソルと playback state が `0.0 sec` に戻る
7. 再生中の Play 再押下は無視され、再生状態は維持される
8. busy 中は再生禁止であり、再生中に解析開始が必要な場合は先に停止する
9. B3 の再生可能条件は `analysis_result_valid` に依存しない
10. 再生開始失敗時は playing 状態へ遷移せず、最小の失敗通知が行われる
11. 再生中に `selected_wav_path` が変更された場合は停止し、`0.0 sec` へ戻る
12. MS14 で残されていた再生関連 stub が最小実装導線へ置換される
13. オートスクロール、shared viewport、Zoom / Pan、Pause、Seek、Loop を流入させていない
14. B4/B5 が依存できる playback state と同期導線が定義されている

---

## 5. In Scope

MS15-B3 に含めるものは以下とする。

- Play / Stop の実動化
- WAV 再生開始
- WAV 再生停止
- 再生終了検知
- 再生位置取得
- wx メインスレッド上の約 50ms 周期位置更新
- waveform / Preview への位置同期
- 最小 playback state の導入
- Stop / 終了時の `0.0 sec` 復帰
- 再生中 Play 再押下の無害化
- busy 中再生禁止
- 再生中解析開始前の停止処理
- 再生開始失敗時の最小エラー処理
- 再生中の入力 WAV 変更時停止
- B3 に必要な軽量テストの追加または更新

---

## 6. Out of Scope

MS15-B3 では以下を行わない。

- Pause
- 任意シーク
- ループ再生
- 再生速度変更
- mp3 対応
- 音声のみ入力対応
- auto scroll
- shared viewport 本実装
- 可変 viewport 同期
- Zoom / Pan
- 再生中 GUI の大規模滑らか化
- action state 全体整理
- status 文言の全面整理
- i18n
- 再生履歴
- 大規模 state machine 再設計

---

## 7. Expected Functional Boundary

B3 は「音が鳴ること」と「再生位置が見えること」を成立させる block である。  
ただし、再生 UX の完成までは担当しない。

責務分離は以下のとおり。

- **B1:** 波形表示基盤
- **B2:** Preview 表示基盤
- **B3:** 再生開始 / 停止と再生位置同期
- **B4:** オートスクロールと可視範囲追従
- **B5:** 表示・再生状態統合
- **B6:** closeout

したがって B3 では、

- 再生開始 / 停止を実動化する
- 再生位置を取得して表示へ流す
- waveform / Preview の描画 API を呼ぶ
- Stop / 終了時の位置リセットを行う
- 再生中 Play 再押下を無害化する
- busy / 入力変更との最小衝突回避を行う
- 再生開始失敗時の最小エラー処理を行う

が対象であり、

- 可視範囲を動かす
- ボタン活性規則を全面整理する
- status 表示を最終形にする
- Pause / Seek を提供する

ことは行わない。

---

## 8. Current Recognition for B3 Entry

現時点の B3 着手前認識は以下とする。

### 8.1 実装側
- B1 により waveform 側の表示基盤と再生位置線 API が成立済みである
- B2 により Preview 側の表示基盤と現在位置縦線 API が成立済みである
- `MainFrame` には Play / Stop の UI 置き場がある
- `app_controller.py` 側には playback request の stub が存在する
- `selected_wav_path` は既存入力導線で保持される
- busy / analysis 導線は MS14 で成立済みである

### 8.2 B3 で再確認すべき領域
- wx 主系で採れる再生バックエンドが、追加依存なしで B3 要件を満たせるか
- 再生位置取得 API が約 50ms 周期で十分安定するか
- 再生終了検知をどの層で受けるか
- playback state の保持場所をどこに置くか
- Stop と自然終了の双方で `0.0 sec` 復帰を一貫して実装できるか
- busy 開始前停止が既存解析導線と自然に接続できるか
- 再生開始失敗時の最小通知をどの既存導線で流すか
- `selected_wav_path` 変更時の停止導線が既存入力変更処理と自然に接続できるか
- B1/B2 のカーソル API が plan 上の契約と一致しているか

### 8.3 B3 の主眼
B3 の主眼は、**再生 stub を実再生と位置同期へ置換し、B4/B5 が依存できる再生事実導線を作ること**にある。  
再生 UX の追従感や状態統合の最終形は B3 の主眼ではない。

---

## 9. Design Axes

### 9.1 Backend Axis
- 追加依存を増やさない
- WAV 限定の最小再生基盤を優先する
- B3 で mp3 や高度拡張を先取りしない

### 9.2 Timing Axis
- 再生開始位置は `0.0 sec`
- 更新周期は約 50ms
- Stop / 終了時は `0.0 sec` に戻す
- Seek を前提にしない
- 再生中 Play 再押下は無視する

### 9.3 State Axis
- `is_playing`
- `playback_position_sec`
- 再生対象の識別情報
- 必要最小限のタイマー稼働状態

までに留める。

### 9.4 Sync Axis
- waveform / Preview へ同じ `playback_position_sec` を流す
- B3 は同期の供給側であり、描画責務は持たない
- 可視範囲移動は行わない
- UI 更新は wx メインスレッドからのみ行う

### 9.5 Conflict Axis
- busy 中は再生禁止
- 再生中に解析開始が必要なら先に停止
- 再生中に `selected_wav_path` が変わったら停止
- action state の最終整理は B5 に送る

### 9.6 Error Axis
- 再生開始失敗時は playing 化しない
- 表示カーソルを進めない
- 既存の status / error 通知導線へ最小通知を流す
- モーダル UI を必須化しない

---

## 10. Candidate File Touch Areas

B3 で変更対象になり得るファイルは、以下を主候補とする。

### コード
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`（必要最小限）
- `src/gui_wx/waveform_panel.py`（API 接続確認の範囲）
- `src/gui_wx/preview_panel.py`（API 接続確認の範囲）

### 新規追加候補と最小責務
- `src/gui_wx/playback_controller.py`
  - 再生バックエンドのラップ
  - 再生開始 / 停止
  - 再生位置取得
  - 終了検知
  - 開始失敗時の戻り値 / 例外整理
- `src/gui_wx/playback_timer.py`
  - wx メインスレッド上の約 50ms 周期更新タイミング管理
  - ただし責務が薄い場合は playback_controller 内包でよい
- `src/gui_wx/playback_state.py`
  - playback state の最小保持
  - ただし `ui_state.py` へ小さく追加する方が自然なら分離必須ではない

### テスト
- B3 用の再生導線テスト
- Stop / 終了時リセット確認
- waveform / Preview 同期確認
- busy 競合確認
- 再生失敗時の非遷移確認
- 再生中 Play 再押下無害化確認
- 再生中パス変更時停止確認

---

## 11. Execution Policy

### 11.1 まずバックエンド成立性を確認する
最初に、追加依存なしで B3 の最小再生要件が満たせるか確認する。

確認結果が以下であれば、B3 を進めてよい。

- WAV を開ける
- 再生開始 / 停止ができる
- 再生位置が取得できる
- 終了検知ができる

逆に、以下のいずれかが判明した場合は、**B3 を実装開始せず停止して報告する**。

- WAV 再生が成立しない
- 再生位置取得ができない
- 終了検知が取れない
- 追加依存なしでは B3 完了条件を満たせない

この場合、独断で新依存を追加して進めることはしない。  
**停止して差分を報告し、判断待ちにする**。

### 11.2 Stop / 終了 / 再押下規約を先に固定する
controller 実装より先に、以下を規約として固定する。

- Play は `0.0 sec` 開始
- Stop は `0.0 sec` 復帰
- 自然終了も `0.0 sec` 復帰
- 再生中 Play 再押下は無視
- 再生中の入力 WAV 変更は停止 + `0.0 sec` 復帰

### 11.3 再生位置同期は供給側に集中させる
B3 は再生位置の供給側であり、waveform / Preview 側に独自時計を持たせない。  
再生位置更新は B3 側で一元化して通知する。

### 11.4 busy 競合は安全側で処理する
B3 では、再生と解析の同時実行を許可しない。  
busy 開始前には必要なら再生を停止し、安全側で処理する。

### 11.5 エラー時は最小通知で止める
再生開始失敗時は、無理に復旧継続を試みず、

- playing 化しない
- 位置を進めない
- 最小通知を出す

で止める。

### 11.6 B4/B5 の責務を先食いしない
可視範囲移動、ボタン活性規則の全面整理、status 文言統合は B3 に流入させない。

---

## 12. Step Breakdown

### Step 0. Confirm Entry Gate
- B1 / B2 のカーソル API が存在するか確認する
- B1 / B2 の表示基盤が B3 受け口として成立済みか確認する
- 既存 Play / Stop UI と controller stub の位置を確認する

#### Exit Condition
- B3 実装開始条件が満たされている  
  **または**
- 受け口不足のため、B3 を実装開始せず停止すべきことが明確になっている

---

### Step 1. Confirm Playback Backend Feasibility
- 追加依存なしでの再生候補を確認する
- WAV 再生可否を確認する
- 再生位置取得可否を確認する
- 終了検知可否を確認する

#### Exit Condition
- B3 の最小再生要件を満たせるバックエンドが確認できている  
  **または**
- 追加依存なしでは成立せず、B3 を実装開始せず停止・報告すべきことが明確になっている

---

### Step 2. Define Playback Rules and State Boundary
- `is_playing`
- `playback_position_sec`
- 再生対象識別
- 更新タイマー状態

の最小境界を定義する。  
あわせて以下の規約を固定する。

- Play は `0.0 sec` 開始
- Stop は `0.0 sec` 復帰
- 自然終了も `0.0 sec` 復帰
- 再生中 Play 再押下は無視
- 再生中の入力 WAV 変更は停止 + `0.0 sec` 復帰
- 再生開始失敗時は playing 化しない

#### Exit Condition
- B3 が持つ playback state の最小構成が定義されている
- 開始 / 終了 / 再押下 / 失敗 / パス変更時の規約が固定されている

---

### Step 3. Introduce Playback Controller
- 再生開始
- 再生停止
- 再生位置取得
- 終了検知
- 開始失敗時の非遷移

を行う最小 controller を導入する。

#### Exit Condition
- 再生 controller が Play / Stop / Position / End / Failure を扱える

---

### Step 4. Implement Position Update Loop
- wx メインスレッド上の約 50ms 周期で再生位置を取得する
- playback state を更新する
- waveform / Preview へ同一位置を通知する

#### Exit Condition
- 再生位置更新が 50ms 基準で成立している
- waveform / Preview の両方へ同期反映できる
- UI 更新が wx メインスレッドで行われている

---

### Step 5. Wire MainFrame and Stub Replacement
- Play / Stop UI から controller を呼ぶ
- 既存 stub を最小実装導線へ置換する
- waveform / Preview の位置反映 API と接続する
- 再生開始失敗時の最小通知導線を接続する

#### Exit Condition
- MS14 の playback stub が B3 範囲で置換されている

---

### Step 6. Add Busy / Path-Change Guards
- busy 中は再生禁止にする
- 再生中に解析開始が必要なら先に停止する
- 再生中に `selected_wav_path` が変更されたら停止する
- 既存解析導線 / 入力変更導線と衝突しないように接続する

#### Exit Condition
- busy 競合ルールが実行事実として成立している
- 入力 WAV 変更時の停止規則が成立している

---

### Step 7. Add / Update Lightweight Tests
- Play 実行確認
- Stop 実行確認
- 再生位置更新確認
- waveform / Preview 同期確認
- 終了時 `0.0 sec` 復帰確認
- Stop 時 `0.0 sec` 復帰確認
- busy 中再生禁止確認
- 解析開始前停止確認
- 再生中 Play 再押下無視確認
- 再生開始失敗時非遷移確認
- 再生中パス変更時停止確認
- wx メインスレッド timer 前提の接着確認

#### Exit Condition
- B3 の接着点が最低限テストで担保されている

---

### Step 8. Re-check Scope Guard
- Pause が流入していないか
- Seek が流入していないか
- Loop が流入していないか
- auto scroll が流入していないか
- shared viewport が流入していないか
- Zoom / Pan が流入していないか
- B5 の state 統合を先食いしていないか

#### Exit Condition
- B3 が B3 の責務範囲に収まっている

---

## 13. Acceptance Criteria

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. `selected_wav_path` が存在し、再生バックエンドがその WAV を開ける場合に再生開始できる
2. Stop 操作により再生停止できる
3. 再生位置を約 50ms 周期で取得できる
4. 再生位置が waveform / Preview の両方へ同期反映される
5. 再生開始位置は常に `0.0 sec` である
6. 再生終了時は停止し、表示カーソルと playback state が `0.0 sec` に戻る
7. 再生中の Play 再押下は無視され、再生状態は維持される
8. busy 中は再生禁止であり、再生中に解析開始が必要な場合は先に停止する
9. B3 の再生可能条件は `analysis_result_valid` に依存しない
10. 再生開始失敗時は playing 状態へ遷移せず、最小の失敗通知が行われる
11. 再生中に `selected_wav_path` が変更された場合は停止し、`0.0 sec` へ戻る
12. MS14 で残されていた再生関連 stub が最小実装導線へ置換される
13. オートスクロール、shared viewport、Zoom / Pan、Pause、Seek、Loop を流入させていない
14. B4/B5 が依存できる playback state と同期導線が定義されている

---

## 14. Verification Plan

### 14.1 Runtime / Integration Checks

#### 14.1.1 Playback Startup
**自動化対象**
- 再生可能条件を満たすと Play できる
- 再生開始位置が `0.0 sec` である

**手動確認対象**
- 実際に音が出る
- 開始直後に waveform / Preview の位置が先頭から動く

#### 14.1.2 Stop Behavior
**自動化対象**
- Stop で再生停止する
- Stop 後 `playback_position_sec == 0.0` になる
- waveform / Preview のカーソルが `0.0 sec` に戻る

**手動確認対象**
- Stop 後に終端残りや途中残りがない

#### 14.1.3 End-of-Playback Behavior
**自動化対象**
- 自然終了を検知できる
- 自然終了後に停止状態へ戻る
- 自然終了後に `0.0 sec` へ戻る

**手動確認対象**
- 再生終了時の表示が Stop と整合している

#### 14.1.4 Position Sync
**自動化対象**
- 約 50ms 周期で位置取得が行われる
- waveform / Preview の両方へ同じ位置が通知される
- UI 更新が wx メインスレッド側で行われる

**手動確認対象**
- 表示追従が極端にぎこちなくない
- B3 範囲として十分確認できる

#### 14.1.5 Busy Conflict
**自動化対象**
- busy 中は Play できない
- 再生中に解析開始が必要なら先に停止する

**手動確認対象**
- 解析導線と再生導線が競合で破綻しない

#### 14.1.6 Play Re-press
**自動化対象**
- 再生中の Play 再押下が無視される
- 再押下で位置が `0.0 sec` にリセットされない
- 再押下で再生対象が切り替わらない

**手動確認対象**
- 再押下で不自然な restart が起きない

#### 14.1.7 Playback Failure
**自動化対象**
- 再生開始失敗時に playing 化しない
- 再生位置が進まない
- 最小通知導線が呼ばれる

**手動確認対象**
- 失敗時に無反応で終わらない

#### 14.1.8 Path Change While Playing
**自動化対象**
- 再生中に `selected_wav_path` が変更されたら停止する
- 停止後 `0.0 sec` に戻る

**手動確認対象**
- 古い再生対象を引きずらない

### 14.2 Review / Audit Checks

#### 14.2.1 Scope Review
**レビュー対象**
- Pause が流入していない
- Seek が流入していない
- Loop が流入していない
- auto scroll が流入していない
- shared viewport が流入していない
- Zoom / Pan が流入していない

#### 14.2.2 Architecture Review
**レビュー対象**
- playback state が過剰に複雑化していない
- waveform / Preview 側へ時計責務が漏れていない
- stub 置換が最小範囲に収まっている
- B5 の状態解釈を先食いしていない
- UI 更新が wx メインスレッドに固定されている

---

## 15. Risks and Control

### Risk 1. Backend Insufficiency
追加依存なしでは再生開始 / 位置取得 / 終了検知が揃わない危険がある。  
**Control:** Step 1 で成立性を先に確認し、満たせなければ停止して報告する。

### Risk 2. Playback and UI State Mixing
再生事実と UI 状態解釈が混線し、B5 の責務を侵食する危険がある。  
**Control:** B3 は再生事実のみを扱い、UI 統合は B5 に送る。

### Risk 3. Position Drift Between Views
waveform と Preview へ別時計で更新が流れ、表示位置がずれる危険がある。  
**Control:** B3 を唯一の位置供給源とする。

### Risk 4. End-State Inconsistency
Stop と自然終了で位置や状態が異なる危険がある。  
**Control:** どちらも `0.0 sec` 復帰で固定する。

### Risk 5. Busy Conflict
再生と解析が衝突して不安定になる危険がある。  
**Control:** busy 中再生禁止、解析開始前停止を固定する。

### Risk 6. Scope Creep into B4/B5
追従表示や action state 整理が B3 に流入する危険がある。  
**Control:** B3 は start/stop/position sync のみに限定する。

### Risk 7. Re-press Ambiguity
再生中 Play 再押下時の挙動が揺れ、実装差が出る危険がある。  
**Control:** 再生中 Play 再押下は無視と固定する。

### Risk 8. Runtime Playback Failure
再生可能条件が見かけ上満たされていても、実行時に再生開始へ失敗する危険がある。  
**Control:** 失敗時は playing 化せず、最小通知を出して止める。

### Risk 9. Playback Source Drift
再生中に `selected_wav_path` が変わり、loaded source と UI 上の選択が乖離する危険がある。  
**Control:** パス変更時は停止して `0.0 sec` へ戻す。

### Risk 10. Wrong Thread UI Update
UI 更新を worker thread から行い、wx スレッド境界違反になる危険がある。  
**Control:** 位置更新は wx メインスレッド timer に固定する。

---

## 16. Definition of Done

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. `selected_wav_path` が存在し、再生バックエンドがその WAV を開ける場合に再生開始できる
2. Stop 操作により再生停止できる
3. 再生位置を約 50ms 周期で取得できる
4. 再生位置が waveform / Preview の両方へ同期反映される
5. 再生開始位置は常に `0.0 sec` である
6. 再生終了時は停止し、表示カーソルと playback state が `0.0 sec` に戻る
7. 再生中の Play 再押下は無視され、再生状態は維持される
8. busy 中は再生禁止であり、再生中に解析開始が必要な場合は先に停止する
9. B3 の再生可能条件は `analysis_result_valid` に依存しない
10. 再生開始失敗時は playing 状態へ遷移せず、最小の失敗通知が行われる
11. 再生中に `selected_wav_path` が変更された場合は停止し、`0.0 sec` へ戻る
12. MS14 で残されていた再生関連 stub が最小実装導線へ置換される
13. オートスクロール、shared viewport、Zoom / Pan、Pause、Seek、Loop を流入させていない
14. B4/B5 が依存できる playback state と同期導線が定義されている

---

## 17. Handoff Notes for Implementation

- B3 は再生基盤と再生位置同期 block であり、追従 UX block ではない
- 再生バックエンドは追加依存なし優先で選ぶこと
- 追加依存なしで成立しない場合は独断で依存追加せず停止して報告すること
- 位置更新は wx メインスレッド timer を使うこと
- 更新周期は約 50ms を基準にすること
- Play は常に `0.0 sec` 開始に固定すること
- Stop と自然終了はどちらも `0.0 sec` 復帰に固定すること
- 再生中 Play 再押下は無視すること
- `analysis_result_valid` を再生可能条件に入れないこと
- busy 中は再生禁止とすること
- 再生中に解析開始が必要なら先に停止すること
- 再生開始失敗時は playing 化せず、最小通知だけ行うこと
- 再生中に `selected_wav_path` が変わったら停止して `0.0 sec` に戻すこと
- waveform / Preview の位置同期は B3 を唯一の供給源とすること
- auto scroll、shared viewport、Zoom / Pan、Pause、Seek、Loop を流入させないこと
- B5 の UI / action state 統合を先食いしないこと

---

## 18. Status Note

- **2026-04-22**: Revised draft for MS15-B3.  
  再生バックエンドは追加依存を増やさない方針、更新周期は約 50ms、再生開始位置は `0.0 sec` 固定、Stop / 自然終了時は `0.0 sec` 復帰、再生中 Play 再押下は無視、busy 中再生禁止、`analysis_result_valid` 非依存の再生可能条件、再生開始失敗時の最小通知、再生中パス変更時停止、wx メインスレッド timer 前提を明示した。
  