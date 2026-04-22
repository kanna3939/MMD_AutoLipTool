# MS15-B2_Implementation_Plan

## 1. Document Control

- Document Name: `MS15-B2_Implementation_Plan.md`
- Milestone: `MS15`
- Block: `MS15-B2`
- Title: `Preview 表示基盤`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS15-B2 では、MS14 時点で placeholder に留められている Preview 領域を、**wx 主系で実 Preview を表示できる基盤**へ置き換える。

本 block の目的は、再生 UX 全体を一気に完成させることではない。  
MS15-B2 は、後続 block である再生位置同期とオートスクロールを安全に載せられるように、以下を最小範囲で成立させるための block とする。

- 解析結果が有効なときに Preview が実表示されること
- Preview の時間軸が MS15-B1 の波形時間軸規約と矛盾しないこと
- 母音イベント / 区間が確認用可視化として読めること
- 現在位置ハイライトの最小受け口があること
- MS14 の core workflow を壊さないこと

B2 は、**Preview 表示基盤**に限定する。  
再生 start/stop、本格的な再生位置同期、オートスクロール、shared viewport、Zoom / Pan、編集 UI、複雑なインタラクションは本 block に含めない。

---

## 3. Fixed Decisions

### 3.1 Preview 表示表現
B2 の Preview 表示は、**`gui.preview_transform.build_preview_data(...)` を再利用した shape / segment ベースの確認用表示**を基本とする。

すなわち、B2 では単なる区間バーだけでなく、既存 writer / preview semantics と整合する Preview 用データを表示に用いる。  
ただし、Qt 側 widget 構造や描画クラスを丸移植することは行わない。

### 3.2 レイアウト単位
B2 の Preview は、**5母音固定の 5 段レーン（あ / い / う / え / お）**で表示する。

- 各レーンは 1 母音に対応する
- 表示順は既存 `preview_transform` の row order と整合する
- 1 つのタイムライン上へ全母音を重ねる構成は採らない
- 可変段数や複合レイアウトは B2 に含めない

### 3.3 `analysis_result_valid == False` 時の扱い
B2 の Preview 表示は、**valid な `current_timing_plan` を前提**とする。  
したがって、`analysis_result_valid == False` の間は、

- Preview 本表示を行わない
- Preview 領域をクリアする
- 未解析 / 再解析待ちの placeholder 表示へ戻す

を基本とする。

直前結果の灰色残しや保持継続は行わない。

### 3.4 現在位置ハイライト API
B2 では、後続 block から再利用できる最小形として、**縦線カーソル 1 本の表示受け口**を用意する。  
B3 との契約として、少なくとも以下の API を固定する。

- `set_playback_position_sec(position_sec: float) -> None`
- `clear_playback_cursor() -> None`

補助的に内部で `playback_position_sec: float | None` を保持してよい。  
B2 単体で再生更新ループは持たない。  
現在母音レーンの強調や複雑なアニメーションは行わない。

### 3.5 Preview データ生成の正本
Preview データ生成の正本は、**既存 `gui.preview_transform.build_preview_data(...)`** とする。

B2 では、

- wx 側で独自の簡易変換を新規実装しない
- timeline を view 側が直接解釈する構造にしない
- writer / preview 意味整合を壊さない

ことを優先する。

### 3.6 `build_preview_data(...)` への入力方針
B2 では、`build_preview_data(...)` へは以下を基本方針で渡す。

- `timeline`: **必須**
- `observations`: **存在する場合は渡す / 無い場合は `None` または省略でよい**
- `closing_hold_frames`: 現在 UI 上で保持している値を渡してよい
- `closing_softness_frames`: 現在 UI 上で保持している値を渡してよい

すなわち、B2 の Preview 表示成立において **`observations` を必須前提にはしない**。  
ただし、存在する場合は既存意味論を活かすために渡す。

### 3.7 正本 duration の参照元
B2 における Preview 右端の `duration_sec` は、**`selected_wav_analysis.duration_sec` を正本**とする。

- `current_timing_plan` 自体は Preview 表示データの生成元ではあるが、**右端 duration の正本にはしない**
- Preview の描画範囲右端は、常に `selected_wav_analysis.duration_sec` により決定する
- B1 waveform 側も同じ `selected_wav_analysis.duration_sec` を正本にしている前提で扱う
- 将来 B1/B4 で canonical viewport provider が導入される場合も、その基底 duration は同一の `selected_wav_analysis.duration_sec` から解決されることを前提にする

### 3.8 duration 不一致時の扱い
`current_timing_plan.timeline` 内の時刻や `build_preview_data(...)` の出力が、正本 duration である `selected_wav_analysis.duration_sec` と微小にずれる場合、B2 では以下で扱う。

- 描画右端の正本は **常に `selected_wav_analysis.duration_sec`**
- Preview 要素の描画は `0.0 sec` から `duration_sec` の範囲へ **必ず clamp する**
- `current_timing_plan` 側の長さ推定を右端決定に使わない
- 微小差の吸収は表示側の境界処理で行い、pipeline / preview_transform の意味変更は行わない
- clamp の結果、可視幅が 0 以下になった要素は非描画としてよい

### 3.9 B1 との時間軸関係
B2 は、**MS15-B1 で確定済みの波形時間軸規約**と矛盾しない Preview 時間軸を持つ。  
少なくとも以下を満たす。

- 左端は `0.0 sec`
- 右端は `selected_wav_analysis.duration_sec`
- 任意の `time_sec` を x 座標へ一意に写像できる
- B1 の waveform と同一再生位置に対して、同一時刻を示す表示位置が大きくずれない

### 3.10 B2 着手条件
B2 の実装着手条件として、以下を要求する。

- **MS15-B1 の時間軸規約が確定済みであること**
- **B1 側で正本 duration の扱いが固定済みであること**
- **B2 側が参照すべき waveform 時間軸規約が実装者にとって既知であること**

これらが未確定の場合、B2 は**実装開始せず、検証・準備で停止**する。  
B1 規約が「成立予定」の段階では、B2 の静的 Preview 描画実装に入らない。

### 3.11 Zoom / Pan / viewport との境界
B2 では、**full-range 固定表示**を前提とする。

- 可視範囲は `0.0 sec` から `selected_wav_analysis.duration_sec` の全域固定
- B2 単体では viewport 可変・shared viewport・Zoom / Pan を持たない
- B2 の完了判定は **full-range 固定表示の下での時間軸整合**のみを対象とする
- B1 側に将来 viewport 概念が入ることを妨げないが、**B2 時点ではそれへの追従を要求しない**
- waveform と Preview の可変 viewport 同期は B3/B4 以降の責務であり、B2 の完了条件には含めない

### 3.12 Preview 表示成立条件
本文書における **`Preview 表示可能`** とは、少なくとも以下を満たす状態を指す。

- `analysis_result_valid == True`
- `current_timing_plan` が存在する
- `current_timing_plan.timeline` が存在し、空でない
- `selected_wav_analysis` が存在し、その `duration_sec` が利用可能である
- `preview_transform.build_preview_data(...)` に渡せる最低限の情報が揃っている

### 3.13 Preview の役割
B2 の Preview は、**確認用可視化**である。  
したがって以下を役割外とする。

- 編集 UI
- 区間ドラッグ編集
- キーフレーム編集
- VMD 編集機能
- 表示上の高度な演出

---

## 4. Goal

本節の項目群を、**MS15-B2 の canonical completion criteria** とする。  
後続の `13. Acceptance Criteria` および `16. Definition of Done` は意味差なしで本節を再掲する。

1. `analysis_result_valid == True` かつ valid な `current_timing_plan` がある状態で preview placeholder が実 Preview 表示へ置き換わる
2. Preview は 5母音固定の 5 段レーンで表示される
3. Preview 表示は `preview_transform.build_preview_data(...)` を正本として生成される
4. 母音イベント / 区間が確認用可視化として読み取れる
5. Preview の時間軸は `0.0 sec` と `selected_wav_analysis.duration_sec` を両端基準とし、B1 の波形時間軸規約と矛盾しない
6. 後続 block から `set_playback_position_sec(position_sec: float) -> None` と `clear_playback_cursor() -> None` を通じて現在位置縦線カーソルを更新できる
7. `analysis_result_valid == False` 時は Preview 本表示を行わず、未解析 / 再解析待ちの placeholder 表示へ戻る
8. B2 の完了判定は full-range 固定表示を前提とし、可変 viewport 同期を要求しない
9. Preview 要素は描画時に `0.0 sec` から `selected_wav_analysis.duration_sec` の範囲へ clamp される
10. MS14 の入力・解析・保存導線を壊していない
11. playback start/stop、オートスクロール、shared viewport、Zoom / Pan、編集 UI を流入させていない
12. B3/B4 が依存できる Preview 表示基盤と現在位置ハイライト受け口が定義されている

---

## 5. In Scope

MS15-B2 に含めるものは以下とする。

- preview placeholder の置換
- Preview 描画用 widget / panel の導入
- `current_timing_plan` からの Preview 表示データ生成導線
- `preview_transform.build_preview_data(...)` の再利用
- 5母音固定 5 段レーン表示
- 母音イベント / 区間の確認用可視化
- B1 と矛盾しない full-range 時間軸規約
- 現在位置縦線カーソルの受け口 API
- `analysis_result_valid == False` 時の placeholder 復帰
- 描画範囲の clamp を含む最小境界処理
- 表示更新用の view helper
- B2 に必要な軽量テストの追加または更新

---

## 6. Out of Scope

MS15-B2 では以下を行わない。

- WAV 再生 start/stop 実装
- 再生位置の実時間更新ループ
- auto scroll
- shared viewport 本実装
- 可変 viewport 同期
- Zoom / Pan
- 手動スクロール高度化
- 編集 UI
- 直接ドラッグ編集
- 複雑なアニメーション
- 現在母音レーン強調
- Preview 表示の複雑なレイアウト可変化
- Qt 側 widget 構造の丸移植
- writer / pipeline の意味変更
- mp3 対応
- 音声のみ入力対応

---

## 7. Expected Functional Boundary

B2 は「Preview を見えるようにする block」であり、「再生と追従を成立させる block」ではない。  
責務分離は以下のとおり。

- **B1:** 波形表示基盤
- **B2:** Preview 表示基盤
- **B3:** 再生 start/stop と再生位置同期
- **B4:** オートスクロールと可変 viewport 追従
- **B5:** 表示・再生状態統合
- **B6:** closeout

したがって B2 では、

- `current_timing_plan` を Preview 表示へ変換する
- Preview を時間軸上へ描く
- 現在位置縦線の**受け口**は作る
- ただし現在位置を**誰が更新するか**は B3 に送る
- placeholder 復帰規則は持つ
- ただし再生 state 解釈や action state 整理は B5 に送る
- full-range 固定表示の時間軸整合は持つ
- ただし可視範囲共有や自動追従は B4 に送る

という境界を守る。

---

## 8. Current Recognition for B2 Entry

現時点の B2 着手前認識は以下とする。

### 8.1 実装側
- `src/gui_wx/main_frame.py` に preview placeholder の置き場が存在する
- `PlaceholderContainer` が waveform / preview の右側上下 2 段配置を持っている
- 解析成功時に preview placeholder 文言は更新されるが、実 Preview 描画はない
- `UiState.current_timing_plan` が解析成功時に保持される
- `analysis_result_valid` が Preview 表示可能条件に使える
- `selected_wav_analysis.duration_sec` が Preview 右端 duration の正本として使える
- Qt 側には widget と分離された `preview_transform.build_preview_data(...)` が存在する
- **B1 により waveform 側の時間軸規約は確定済みであることを前提にする**

### 8.2 B2 で再確認すべき領域
- `current_timing_plan` のどの情報をそのまま `preview_transform` へ渡せるか
- observations を B2 時点で必須にしない前提で接着できるか
- 5 段レーン描画の最小表現を wx 側でどう持つか
- B1 の時間軸規約と Preview の x 座標写像をどう一致させるか
- `analysis_result_valid == False` 時の placeholder 復帰導線が既存 invalidate と衝突しないか
- 現在位置縦線カーソル API を B3 へ渡せる形で接着できるか
- 正本 duration から外れた Preview 要素の clamp をどこで行うか

### 8.3 B2 の主眼
B2 の主眼は、**placeholder を実 Preview へ置換し、以後の再生同期・追従 block が依存できる確認用可視化基盤を作ること**にある。  
再生 UX そのものの成立は B2 の主眼ではない。

---

## 9. Design Axes

### 9.1 Data Axis
- 入力は既存解析導線を前提にする
- Preview 表示データ生成は `preview_transform.build_preview_data(...)` を正本とする
- writer / preview の意味整合を壊さない
- wx 側独自の簡易変換意味論は増やさない
- 右端 duration の正本は `selected_wav_analysis.duration_sec` とする

### 9.2 Rendering Axis
- 5母音固定 5 段レーン表示
- 確認用可視化として区間 / shape / segment を描く
- B1 と矛盾しない full-range 時間軸規約
- 現在位置縦線カーソルは受け口のみ持つ
- Preview 要素は `0.0 sec` から `duration_sec` の範囲へ必ず clamp する

### 9.3 State Axis
- B2 単体では playback state を作らない
- `analysis_result_valid == True` で表示成立
- `analysis_result_valid == False` では placeholder へ戻る
- `current_timing_plan` の invalidate と表示 invalidate を整合させる

### 9.4 Boundary Axis
- playback 実動を扱わない
- auto scroll を扱わない
- shared viewport を扱わない
- Zoom / Pan を扱わない
- 編集操作を扱わない
- B5 の action state 統合を先取りしない

---

## 10. Candidate File Touch Areas

B2 で変更対象になり得るファイルは、以下を主候補とする。

### コード
- `src/gui_wx/main_frame.py`
- `src/gui_wx/placeholder_panels.py`

### 新規追加候補と最小責務
- `src/gui_wx/preview_panel.py`
  - Preview 用 widget / panel
  - paint event の受け口
  - 外部公開 API  
    例: Preview データ設定、現在位置線設定、placeholder / clear 設定
- `src/gui_wx/preview_renderer.py`
  - 5 段レーン描画
  - 時間軸に基づく座標計算
  - segment / control point の最小可視化
  - 現在位置縦線描画
  - full-range 表示前提の clamp 処理
- `src/gui_wx/preview_model.py`
  - 表示用 Preview データ保持
  - `preview_transform` 出力の wx 側描画用整理
  - 正本 duration を持つ最小表示コンテナ

上記 3 分割は固定ではない。  
ただし、**widget / renderer / model の責務を 1 ファイルへ密結合させない**方針を優先する。  
2 ファイル構成や同等分割に変更する場合も、上記責務境界は維持すること。

### 既存再利用候補
- `src/gui/preview_transform.py`
  - Preview データ生成の正本
  - Qt widget 依存ではなくデータ変換責務として再利用する
- 必要に応じて `src/core/pipeline.py`
  - `current_timing_plan` / observations の構造確認用

### テスト
- B2 用の軽量表示テスト
- 既存 wx テストの必要最小限更新

---

## 11. Execution Policy

### 11.1 まず既存 Preview 変換 contract を確認する
最初に `preview_transform.build_preview_data(...)` が、wx 側 B2 の表示に必要な最小情報を既に満たしているか確認する。

確認結果が以下であれば、B2 はそのまま進めてよい。

- Qt widget 非依存である
- B2 が必要とする入力 contract を満たせる
- writer / preview semantics の再利用が可能である

逆に、以下のいずれかが判明した場合は、**B2 を実装開始せず停止して報告する**。

- Qt 依存が残っており、そのまま再利用できない
- `timeline` / `observations` / parameter 入力 contract が B2 想定と大きく異なる
- wx 側で意味論を再実装しないと成立しない

この場合、wx 側で独自変換を追加して進めることはしない。  
**停止して差分を報告し、判断待ちにする**。

### 11.2 duration 正本を先に固定する
描画前に、Preview 右端 duration の正本を `selected_wav_analysis.duration_sec` として固定する。  
`current_timing_plan` や Preview データから右端 duration を逆算しない。

### 11.3 placeholder 置換は段階的に行う
先に Preview widget の置き場と表示入口を作り、その後に `current_timing_plan` からの静的 Preview 表示を接続する。  
現在位置縦線は最後に「受け口のみ」整える。

### 11.4 Preview 表示を過剰に理想化しない
B2 では、見栄えやインタラクションの理想化よりも、**確認用として読める Preview 基盤**を優先する。

### 11.5 main_frame を肥大化させない
main_frame は配置と接続に留め、Preview データ整形・描画計算を集中させない。

### 11.6 後続 block の境界を守る
B3/B4/B5 の責務に踏み込むコードや仕様を混入させない。

---

## 12. Step Breakdown

### Step 0. Confirm Entry Gate
- MS15-B1 の時間軸規約が確定済みか確認する
- B1 側で正本 duration の扱いが固定済みか確認する
- B2 側が参照すべき waveform 時間軸規約が明確か確認する

#### Exit Condition
- B2 実装開始条件が満たされている  
  **または**
- 条件未充足のため、B2 を実装開始せず検証・準備で停止すべきことが明確になっている

---

### Step 1. Confirm Existing Preview Data Contract
- `current_timing_plan` の構造を確認する
- `preview_transform.build_preview_data(...)` へ渡せる情報を確認する
- observations を B2 時点で必須扱いにしない前提で接着できるか確認する
- Preview 表示に必要な最小 contract を固定する

#### Exit Condition
- B2 が依存する Preview データ contract が明確になっている
- wx 側で意味論重複実装が不要であることが確認できている  
  **または**
- `build_preview_data(...)` 再利用前提が成立せず、B2 を実装開始せず停止・報告すべきことが明確になっている

---

### Step 2. Define Preview Display Data Boundary
- 表示用 Preview データの保持責務を定義する
- 5 段レーンに渡す単位を整理する
- 右端 duration の正本を `selected_wav_analysis.duration_sec` で固定する
- view が直接 `current_timing_plan` を解釈しすぎない境界を固定する

#### Exit Condition
- preview widget が受け取る表示データ形式が最小限定義されている
- 正本 duration が固定されている

---

### Step 3. Introduce Preview Widget / Panel
- preview placeholder を置換する widget を導入する
- 既存 right-side layout に組み込む
- waveform 側 B1 基盤と共存できるように接続する

#### Exit Condition
- preview 専用 panel/widget が main_frame 上に存在する
- placeholder 固定文言依存が外れている

---

### Step 4. Implement Static Preview Rendering
- 5母音固定 5 段レーン描画を実装する
- `preview_transform.build_preview_data(...)` の出力を元に segment / shape を確認用可視化として描く
- `selected_wav_analysis.duration_sec` を右端とする full-range 固定時間軸を実装する
- B1 の時間軸規約と矛盾しない x 座標写像を実装する
- clamp 処理を必須で入れる
- 初期表示と再描画を成立させる

#### Exit Condition
- `Preview 表示可能` な状態で静的 Preview が描画される
- 5 段レーン構成が視認できる
- 時間軸規約が B1 と整合している

---

### Step 5. Add Current Position Cursor Entry Point
- 現在位置縦線を描くための内部状態を用意する
- `set_playback_position_sec(position_sec: float) -> None` を用意する
- `clear_playback_cursor() -> None` を用意する
- B2 単体では更新ループを持たない

#### Exit Condition
- B3 から現在位置縦線を更新できる API 契約が存在する

---

### Step 6. Wire MainFrame Update Path and Invalidate Recovery
- 解析成功時に Preview 表示データを widget へ渡す
- `analysis_result_valid == False` 時に Preview をクリアし placeholder 表示へ戻す
- B1 waveform 表示と混線しないように更新導線を配線する
- 既存の再解析 / 入力変更 invalidate と衝突しないように整理する

#### Exit Condition
- main_frame から preview widget への更新導線が成立している
- invalidate 時に Preview が古い結果を残さず適切に戻る
- MS14 core workflow を壊さない

---

### Step 7. Add / Update Lightweight Tests
- preview widget 存在確認
- `analysis_result_valid == True` での Preview 表示確認
- `analysis_result_valid == False` での placeholder 復帰確認
- 5 段レーン構成確認
- `preview_transform` 再利用導線確認
- 正本 duration が `selected_wav_analysis.duration_sec` であることの確認
- clamp が必須で適用されていることの確認
- 現在位置縦線 API 確認
- waveform 側 B1 と共存していることの確認
- full-range 固定表示前提で時間軸整合が取れていることの確認

#### Exit Condition
- B2 の接着点が最低限テストで担保されている

---

### Step 8. Re-check Scope Guard
- playback 実装が流入していないか
- auto scroll が流入していないか
- shared viewport が流入していないか
- Zoom / Pan が流入していないか
- 編集 UI が流入していないか
- `preview_transform` の意味論を wx 側で重複実装していないか
- main_frame 肥大化が進んでいないか

#### Exit Condition
- B2 が B2 の責務範囲に収まっている

---

## 13. Acceptance Criteria

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. `analysis_result_valid == True` かつ valid な `current_timing_plan` がある状態で preview placeholder が実 Preview 表示へ置き換わる
2. Preview は 5母音固定の 5 段レーンで表示される
3. Preview 表示は `preview_transform.build_preview_data(...)` を正本として生成される
4. 母音イベント / 区間が確認用可視化として読み取れる
5. Preview の時間軸は `0.0 sec` と `selected_wav_analysis.duration_sec` を両端基準とし、B1 の波形時間軸規約と矛盾しない
6. 後続 block から `set_playback_position_sec(position_sec: float) -> None` と `clear_playback_cursor() -> None` を通じて現在位置縦線カーソルを更新できる
7. `analysis_result_valid == False` 時は Preview 本表示を行わず、未解析 / 再解析待ちの placeholder 表示へ戻る
8. B2 の完了判定は full-range 固定表示を前提とし、可変 viewport 同期を要求しない
9. Preview 要素は描画時に `0.0 sec` から `selected_wav_analysis.duration_sec` の範囲へ clamp される
10. MS14 の入力・解析・保存導線を壊していない
11. playback start/stop、オートスクロール、shared viewport、Zoom / Pan、編集 UI を流入させていない
12. B3/B4 が依存できる Preview 表示基盤と現在位置ハイライト受け口が定義されている

---

## 14. Verification Plan

### 14.1 Runtime / Integration Checks

#### 14.1.1 Display Startup
**自動化対象**
- preview widget が存在する
- placeholder 固定文言に依存しない

**手動確認対象**
- UI 配置が既存右側領域で破綻していない
- waveform 側 B1 と上下配置が崩れていない

#### 14.1.2 Analysis Result to Preview Display
**自動化対象**
- `analysis_result_valid == True` で Preview が表示される
- `current_timing_plan` が空または invalid の場合に本表示しない
- 5 段レーン表示が成立する

**手動確認対象**
- 母音イベント / 区間が確認用可視化として読める
- 極端に見づらいレーン崩れがない

#### 14.1.3 Time Axis Contract
**自動化対象**
- `0.0 sec` → 左端
- `selected_wav_analysis.duration_sec` → 右端
- 中間時刻が一意に写像される
- B1 と同一時刻の x 座標規約が full-range 固定表示前提で矛盾しない
- `current_timing_plan` 側の微小差が右端決定に影響しない
- Preview 要素が描画時に clamp される

**手動確認対象**
- Preview と waveform の時間対応が視覚的に大きくずれていない
- full-range 固定表示として理解可能である

#### 14.1.4 Current Position Cursor Entry
**自動化対象**
- `set_playback_position_sec(position_sec: float) -> None` が呼べる
- `clear_playback_cursor() -> None` が呼べる
- 現在位置縦線が範囲内で描画される

**手動確認対象**
- 縦線が Preview 上で認識できる

#### 14.1.5 Invalidate Recovery
**自動化対象**
- `analysis_result_valid == False` で Preview がクリアされる
- placeholder 表示へ戻る
- 古い Preview が残存しない

**手動確認対象**
- 再読込 / 再解析前後で表示状態が破綻しない

### 14.2 Review / Audit Checks

#### 14.2.1 Scope Review
**レビュー対象**
- playback ロジックが流入していない
- auto scroll が流入していない
- shared viewport が流入していない
- Zoom / Pan が流入していない
- 編集 UI が流入していない
- 現在母音レーン強調が先行実装されていない

#### 14.2.2 Architecture Review
**レビュー対象**
- Preview データ生成責務を wx 側で重複実装していない
- 描画責務が main_frame に集中しすぎていない
- Qt 構造を丸写ししていない
- widget / renderer / model の責務境界が崩れていない
- 右端 duration の正本が `selected_wav_analysis.duration_sec` で固定されている
- clamp が表示側の責務として固定されている

---

## 15. Risks and Control

### Risk 1. Preview Semantics Duplication
wx 側で簡易変換を新規実装し、`preview_transform` と意味がズレる危険がある。  
**Control:** `build_preview_data(...)` を正本として再利用する。

### Risk 2. Invalid State Leakage
`analysis_result_valid == False` でも古い Preview が残り、状態整合が崩れる危険がある。  
**Control:** invalidate 時は clear + placeholder 復帰で固定する。

### Risk 3. Rendering Complexity Expansion
Preview 表現を凝りすぎて B2 が肥大化する危険がある。  
**Control:** 5 段レーンの確認用可視化に固定する。

### Risk 4. Implicit Playback Leakage
現在位置縦線の受け口を作る過程で再生ロジックまで流入する危険がある。  
**Control:** API 受け口のみ作り、更新主体は B3 に送る。

### Risk 5. Time Axis Mismatch with B1
Preview と waveform の時間軸規約がずれ、後続同期で破綻する危険がある。  
**Control:** `selected_wav_analysis.duration_sec` を共通の正本 duration とし、B2 の完了判定は full-range 固定表示前提で定義する。

### Risk 6. MainFrame Overgrowth
Preview 描画責務が main_frame に集中し、B3/B5 の接着が悪化する危険がある。  
**Control:** widget / renderer / model 分離を優先する。

### Risk 7. Duration Source Divergence
`current_timing_plan` と WAV duration の参照元が混在し、右端決定が実装者依存になる危険がある。  
**Control:** 右端 duration の正本を `selected_wav_analysis.duration_sec` に固定し、Preview 側で必ず clamp する。

### Risk 8. B1 Gate Ambiguity
B1 の時間軸規約が未確定のまま B2 に着手し、後で座標規約が崩れる危険がある。  
**Control:** B2 着手条件として B1 規約確定を要求し、未確定なら実装開始せず停止する。

---

## 16. Definition of Done

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. `analysis_result_valid == True` かつ valid な `current_timing_plan` がある状態で preview placeholder が実 Preview 表示へ置き換わる
2. Preview は 5母音固定の 5 段レーンで表示される
3. Preview 表示は `preview_transform.build_preview_data(...)` を正本として生成される
4. 母音イベント / 区間が確認用可視化として読み取れる
5. Preview の時間軸は `0.0 sec` と `selected_wav_analysis.duration_sec` を両端基準とし、B1 の波形時間軸規約と矛盾しない
6. 後続 block から `set_playback_position_sec(position_sec: float) -> None` と `clear_playback_cursor() -> None` を通じて現在位置縦線カーソルを更新できる
7. `analysis_result_valid == False` 時は Preview 本表示を行わず、未解析 / 再解析待ちの placeholder 表示へ戻る
8. B2 の完了判定は full-range 固定表示を前提とし、可変 viewport 同期を要求しない
9. Preview 要素は描画時に `0.0 sec` から `selected_wav_analysis.duration_sec` の範囲へ clamp される
10. MS14 の入力・解析・保存導線を壊していない
11. playback start/stop、オートスクロール、shared viewport、Zoom / Pan、編集 UI を流入させていない
12. B3/B4 が依存できる Preview 表示基盤と現在位置ハイライト受け口が定義されている

---

## 17. Handoff Notes for Implementation

- B2 は Preview 表示基盤 block であり、再生 block ではない
- Preview データ生成の正本は `preview_transform.build_preview_data(...)` とすること
- wx 側で簡易変換意味論を重複実装しないこと
- レイアウトは 5母音固定 5 段レーンで固定すること
- `analysis_result_valid == False` 時は clear + placeholder 復帰で固定すること
- 現在位置ハイライト API は  
  - `set_playback_position_sec(position_sec: float) -> None`  
  - `clear_playback_cursor() -> None`  
  を最低契約として用意すること
- 右端 duration の正本は `selected_wav_analysis.duration_sec` とすること
- `current_timing_plan` は右端 duration の決定に使わないこと
- Preview 要素は描画時に必ず clamp すること
- B2 の完了判定は full-range 固定表示前提であり、可変 viewport 同期を要求しないこと
- B1 の時間軸規約が未確定なら B2 実装を開始しないこと
- playback、auto scroll、shared viewport、Zoom / Pan、編集 UI を流入させないこと
- main_frame へ描画処理を密結合させないこと
- B2 完了時点で B3/B4 が依存できる Preview 表示基盤条件を明示的に残すこと

---

## 18. Status Note

- **2026-04-22**: Revised draft for MS15-B2.  
  Preview 表示表現を `preview_transform` 再利用前提で固定し、5母音固定 5 段レーン、invalidate 時 placeholder 復帰、現在位置縦線カーソル API 契約、`selected_wav_analysis.duration_sec` を正本とする duration 規約、full-range 固定表示前提での B1 時間軸整合、B1 着手条件、clamp 必須化を明示した。
- **2026-04-22**: MS15-B2 Implementation Complete.
  指定された仕様に則り `src/gui_wx/preview_panel.py` を実装し、`main_frame.py` からの連携処理と `tests/test_wx_ms15_b2_preview.py` による検証を完了した。B2 の責務範囲（静的表示基盤）を守り、再生やスクロール処理等の越境は行っていない。
  