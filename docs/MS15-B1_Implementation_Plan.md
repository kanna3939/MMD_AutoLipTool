# MS15-B1_Implementation_Plan

## 1. Document Control

- Document Name: `MS15-B1_Implementation_Plan.md`
- Milestone: `MS15`
- Block: `MS15-B1`
- Title: `波形表示基盤`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS15-B1 では、MS14 時点で placeholder に留められている waveform 領域を、**wx 主系で実波形を表示できる基盤**へ置き換える。

本 block の目的は、再生 UX 全体を一気に完成させることではない。  
MS15-B1 は、後続 block である再生位置同期とオートスクロールを安全に載せられるように、以下を最小範囲で成立させるための block とする。

- WAV 読込後に波形が実表示されること
- 波形表示に必要な時間軸規約が存在すること
- 再生位置線を後続 block から反映できること
- 将来の Zoom / Pan を壊さない最小構造であること
- MS14 の core workflow を壊さないこと

B1 は、**波形表示基盤**に限定する。  
再生 start/stop、本格的な再生位置同期、オートスクロール、Zoom / Pan、イベント境界表示は本 block には含めない。

---

## 3. Fixed Decisions

### 3.1 波形データの取得方針
B1 では、既存の `analyze_wav_file(...)` / `WavAnalysisResult` を尊重する。  
その上で、波形表示に必要な情報が不足する場合に限り、**B1 の責務内で最小の表示用取得を追加**してよい。

この追加は以下の境界で行う。

- 既存の音声解析意味論を変えない
- MS15-B1 の表示責務に必要な範囲へ限定する
- Qt 側の構造をそのまま持ち込まない
- 再生機構や Preview 機構を先行実装しない

### 3.2 描画粒度
B1 の波形描画は、**可視幅に応じた列単位 min/max 圧縮表示**を基本とする。

すなわち、表示幅の各列に対し、対応する音声区間の最小値・最大値を算出し、それを縦線または等価表現で描く。  
生サンプルに近い細線描画や高密度折れ線描画は、B1 の主方式にはしない。

### 3.3 表示チャンネル方針
B1 では、音源が mono / stereo であっても、**表示は 1 本のモノラル統合波形**とする。

統合方式は、B1 の可視確認責務を満たす最小でよい。  
左右別 2 段表示や自動切替は本 block に含めない。

### 3.4 補助表示
B1 では、波形本体に加えて、**最低限の時間目盛り**を含める。  
ここでいう「最低限の時間目盛り」とは、少なくとも以下を満たすものを指す。

- 左端に `0.0 sec`
- 右端に `duration_sec`
- 左右ラベルの位置関係が時間軸規約と矛盾しない

中間目盛りは、描画幅が十分ある場合に自動追加してよいが、B1 の完了要件には含めない。  
イベント境界線、母音ラベル、Preview 的情報表示は含めない。

### 3.5 表示更新方針
B1 では、WAV 読込時に静的な波形表示データを準備し、後続 block から再生位置線だけを軽量に更新できる構造を作る。  
再生中に波形そのものを都度再構成する方針は採らない。

### 3.6 `WAV が有効` の定義
本文書における **`WAV が有効`** とは、少なくとも以下を満たす状態を指す。

- `selected_wav_path` が存在する
- `analyze_wav_file(...)` が成功している
- `selected_wav_analysis` またはそれと等価な `WavAnalysisResult` が利用可能である

単にパスが設定されているだけの状態は `WAV が有効` には含めない。

### 3.7 `analysis_result_valid` との関係
B1 の波形表示は、**`WAV が有効` であれば成立してよく、`analysis_result_valid` には依存しない**。  
解析未実行・再解析前であっても、WAV が有効なら波形表示自体は維持してよい。

### 3.8 Zoom / Pan との境界
B1 では、Zoom / Pan を実装しない。  
ただし、将来の拡張を阻害しないように、

- 時間軸規約
- 可視範囲の概念
- 描画データの保持単位
- 再描画入口

は、固定座標直書きに閉じず、最小限の拡張余地を残す。

---

## 4. Goal

本節の項目群を、**MS15-B1 の canonical completion criteria** とする。  
後続の `13. Acceptance Criteria` および `16. Definition of Done` は意味差なしで本節を再掲する。

1. `WAV が有効` な状態で waveform placeholder が実波形表示へ置き換わる
2. `0.0 sec` と `duration_sec` を両端基準とする時間軸規約が存在し、任意の時刻を x 座標へ一意に写像できる
3. 波形描画は可視幅に応じた列単位 min/max 圧縮方式で成立している
4. 表示は mono / stereo を問わず 1 本のモノラル統合波形として成立している
5. 左端に `0.0 sec`、右端に `duration_sec` の時刻ラベルが表示される
6. 後続 block から再生位置線を更新できる受け口 API が存在する
7. 波形表示は `analysis_result_valid` に依存せず、`WAV が有効` なら成立する
8. MS14 の入力・解析・保存導線を壊していない
9. Zoom / Pan、Preview、再生 start/stop、イベント境界表示を流入させていない
10. B3/B4 が依存できる時間軸規約と再生位置線受け口 API が定義されている

---

## 5. In Scope

MS15-B1 に含めるものは以下とする。

- waveform placeholder の置換
- 波形描画用 widget / panel の導入
- `WAV が有効` な状態での静的波形表示
- 列単位 min/max 圧縮方式による軽量描画
- モノラル統合表示
- 最低限の時間目盛り表示
- 時間軸規約の導入
- 再生位置線の受け口 API
- 表示更新用の view helper
- 必要最小限の表示用データ取得追加
- B1 に必要な軽量テストの追加または更新

---

## 6. Out of Scope

MS15-B1 では以下を行わない。

- WAV 再生 start/stop 実装
- 再生位置の実時間更新ロジック
- Preview 実装
- イベント境界線表示
- 母音ラベル表示
- オートスクロール
- Zoom / Pan
- 手動スクロール高度化
- Pause / Seek / Loop
- mp3 対応
- 音声のみ入力対応
- 音声解析ロジックの意味変更
- Qt 側構造の丸移植
- 大規模描画最適化

---

## 7. Expected Functional Boundary

B1 は「波形を見えるようにする block」であり、「再生できるようにする block」ではない。  
責務分離は以下のとおり。

- **B1:** 波形表示基盤
- **B2:** Preview 表示基盤
- **B3:** 再生 start/stop と再生位置同期
- **B4:** オートスクロール
- **B5:** 表示・再生状態統合
- **B6:** closeout

したがって B1 では、

- 再生位置線の**受け口**は作る
- ただし再生位置を**誰が更新するか**は B3 に送る
- 時間軸規約は作る
- ただし可視範囲の動的移動は B4 に送る
- 波形本体は描く
- ただし Preview やイベント可視化は B2 に送る

という境界を守る。

---

## 8. Current Recognition for B1 Entry

現時点の B1 着手前認識は以下とする。

### 8.1 実装側
- `src/gui_wx/main_frame.py` に waveform placeholder の置き場が存在する
- `PlaceholderContainer` が waveform / preview の右側上下 2 段配置を持っている
- WAV 読込時に placeholder 文言は更新されるが、実波形描画はない
- `analyze_wav_file(...)` により WAV の基本解析は行われている
- `WavAnalysisResult` は少なくとも sample rate / channel count / duration を保持している
- 再生位置同期はまだ未実装である

### 8.2 B1 で再確認すべき領域
- 波形表示に必要な最小データが既存 `WavAnalysisResult` で足りるか
- 足りない場合、どの層で最小追加するか
- waveform widget の配置が既存 main_frame / placeholder 構造と自然に接続できるか
- 時間目盛りをどの程度まで最小表示にするか
- 再生位置線受け口 API を B3 に渡せる形で定義できるか

### 8.3 B1 の主眼
B1 の主眼は、**placeholder を実波形へ置換し、以後の再生・追従 block が依存できる基盤を作ること**にある。  
再生 UX そのものの成立は B1 の主眼ではない。

---

## 9. Design Axes

### 9.1 Data Axis
- 入力は既存 WAV 読込導線を前提にする
- 波形表示に必要な最小データだけを扱う
- 音声解析意味論は変えない
- 表示データは静的準備を基本とする

### 9.2 Rendering Axis
- 可視幅ベースの min/max 圧縮描画
- 1 本のモノラル統合波形
- 左右端の時刻ラベル
- 再生位置線は描画受け口のみ

### 9.3 State Axis
- B1 単体では playback state を作らない
- `WAV が有効` な時に表示成立
- `analysis_result_valid` には依存しない
- 再描画トリガは最小限にする

### 9.4 Boundary Axis
- Preview 情報を描かない
- 再生進行を扱わない
- viewport 移動を扱わない
- Zoom / Pan を扱わない

---

## 10. Candidate File Touch Areas

B1 で変更対象になり得るファイルは、以下を主候補とする。

### コード
- `src/gui_wx/main_frame.py`
- `src/gui_wx/placeholder_panels.py`

### 新規追加候補と最小責務
- `src/gui_wx/waveform_panel.py`
  - waveform 用 widget / panel
  - paint event の受け口
  - 外部公開 API  
    例: 波形データ設定、再生位置線設定、エラー状態設定
- `src/gui_wx/waveform_renderer.py`
  - 時間軸規約に基づく座標計算
  - min/max 圧縮済み表示データの描画
  - 目盛り描画
  - 再生位置線描画
- `src/gui_wx/waveform_model.py`
  - 波形表示用データ保持
  - mono 統合済みまたは表示用正規化済みデータ
  - 可視幅描画へ渡すための前処理済み構造

上記 3 分割は固定ではない。  
ただし、**widget / renderer / model の責務を 1 ファイルへ密結合させない**方針を優先する。  
2 ファイル構成や同等分割に変更する場合も、上記責務境界は維持すること。

### 条件付き候補
- WAV 表示用データ取得が既存結果だけでは不足する場合の最小追加先
  - `src/core/audio_processing.py`
  - ただし意味変更ではなく、表示用取得に限る

### テスト
- B1 用の軽量表示テスト
- 既存 wx テストの必要最小限更新

---

## 11. Execution Policy

### 11.1 まず既存データで足りるか確認する
最初に `analyze_wav_file(...)` / `WavAnalysisResult` で、波形表示に必要な最小情報が足りるかを確認する。  
不足時のみ、表示用取得を最小追加する。

### 11.2 placeholder 置換は段階的に行う
先に波形 widget の置き場と表示入口を作り、その後に静的波形表示を接続する。  
再生位置線は最後に「受け口のみ」整える。

### 11.3 描画最適化を目的化しない
B1 では、滑らかさや高密度描画の理想化よりも、**軽量で破綻しない描画基盤**を優先する。

### 11.4 main_frame を肥大化させない
main_frame は配置と接続に留め、描画計算・描画責務を集中させない。

### 11.5 後続 block の境界を守る
B3/B4/B5 の責務に踏み込むコードや仕様を混入させない。

---

## 12. Step Breakdown

### Step 1. Confirm Existing Data Contract
- `WavAnalysisResult` に保持されている情報を確認する
- 波形表示に必要な最小情報を定義する
- 既存 contract で足りるか / 足りないかを分離する

#### Exit Condition
- 既存 contract のまま進めるか、最小追加が必要かが明確になっている

---

### Step 2. Define Waveform Display Data Boundary
- 表示用データの責務を定義する
- 生サンプル保持なのか、圧縮済み表示データなのかを整理する
- 1 本モノラル統合表示の入力形式を固定する

#### Exit Condition
- waveform widget が受け取る表示データ形式が最小限定義されている

---

### Step 3. Introduce Waveform Widget / Panel
- waveform placeholder を置換する widget を導入する
- 既存 right-side layout に組み込む
- placeholder から新 widget へ接続を切り替える

#### Exit Condition
- waveform 専用 panel/widget が main_frame 上に存在する
- placeholder 固定文言依存が外れている

---

### Step 4. Implement Static Waveform Rendering
- 可視幅ベースの min/max 圧縮描画を実装する
- 1 本モノラル統合波形を描く
- 左右端の時刻ラベルを描く
- 初期表示と再描画を成立させる

#### Exit Condition
- `WAV が有効` な状態で静的波形が描画される
- 時間軸規約が見える形で成立している

---

### Step 5. Add Playback Cursor Entry Point
- 再生位置線を描くための内部状態を用意する
- 外部から `playback_position_sec` を受け取る最小 API を用意する
- B1 単体では更新ループを持たない

#### Exit Condition
- B3 から再生位置線を更新できる受け口 API が存在する

---

### Step 6. Wire MainFrame Update Path and Failure Recovery
- `WAV が有効` になった時に波形表示データを widget へ渡す
- **ここでいう失敗**は、B1 の責務範囲に属する以下を指す
  - 波形表示用データ生成失敗
  - waveform widget への初期設定失敗
- **復帰**は、以下の最小方針とする
  - アプリ全体をクラッシュさせない
  - MS14 の `selected_wav_path` / `selected_wav_analysis` / 入力導線を破壊しない
  - waveform 領域は「空表示または波形表示エラー状態」のいずれかへ遷移してよい
  - placeholder 文言へ巻き戻すことは必須としない
- Preview 側や再生系 stub と混線しないように配線する

#### Exit Condition
- main_frame から waveform widget への更新導線が成立している
- B1 範囲内の表示失敗時に、アプリ全体や MS14 core workflow を壊さない最小復帰方針が定義されている

---

### Step 7. Add / Update Lightweight Tests
- 波形 widget 存在確認
- `WAV が有効` な状態での表示確認
- 時間軸規約確認
- 左右端時刻ラベル確認
- 再生位置線 API 確認
- placeholder 置換確認

#### Exit Condition
- B1 の接着点が最低限テストで担保されている

---

### Step 8. Re-check Scope Guard
- Preview が流入していないか
- 再生 start/stop が流入していないか
- オートスクロールが流入していないか
- Zoom / Pan が流入していないか
- main_frame 肥大化が進んでいないか

#### Exit Condition
- B1 が B1 の責務範囲に収まっている

---

## 13. Acceptance Criteria

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. `WAV が有効` な状態で waveform placeholder が実波形表示へ置き換わる
2. `0.0 sec` と `duration_sec` を両端基準とする時間軸規約が存在し、任意の時刻を x 座標へ一意に写像できる
3. 波形描画は可視幅に応じた列単位 min/max 圧縮方式で成立している
4. 表示は mono / stereo を問わず 1 本のモノラル統合波形として成立している
5. 左端に `0.0 sec`、右端に `duration_sec` の時刻ラベルが表示される
6. 後続 block から再生位置線を更新できる受け口 API が存在する
7. 波形表示は `analysis_result_valid` に依存せず、`WAV が有効` なら成立する
8. MS14 の入力・解析・保存導線を壊していない
9. Zoom / Pan、Preview、再生 start/stop、イベント境界表示を流入させていない
10. B3/B4 が依存できる時間軸規約と再生位置線受け口 API が定義されている

---

## 14. Verification Plan

### 14.1 Runtime / Integration Checks

#### 14.1.1 Display Startup
**自動化対象**
- waveform widget が存在する
- placeholder 固定文言に依存しない

**手動確認対象**
- UI 配置が既存右側領域で破綻していない

#### 14.1.2 WAV Load to Waveform Display
**自動化対象**
- `WAV が有効` な状態で波形が表示される
- mono / stereo の別に関わらず 1 本表示が成立する

**手動確認対象**
- 波形表示が極端に潰れていない

#### 14.1.3 Time Axis Contract
**自動化対象**
- `0.0 sec` → 左端
- `duration_sec` → 右端
- 中間時刻が一意に写像される
- 左右端ラベルが表示される

**手動確認対象**
- 左右端ラベル位置が時間軸と大きく矛盾しない

#### 14.1.4 Playback Cursor Entry
**自動化対象**
- 外部から再生位置をセットできる
- 再生位置線が範囲内で描画される

**手動確認対象**
- 位置線の見え方が波形上で認識できる

### 14.2 Review / Audit Checks

#### 14.2.1 Scope Review
**レビュー対象**
- Preview 表示が流入していない
- 再生ロジックが流入していない
- オートスクロールが流入していない
- Zoom / Pan が流入していない

#### 14.2.2 Architecture Review
**レビュー対象**
- 描画責務が main_frame に集中しすぎていない
- 表示用データ取得が最小である
- Qt 構造を丸写ししていない
- widget / renderer / model の責務境界が崩れていない

---

## 15. Risks and Control

### Risk 1. Existing Audio Contract Expansion Becoming Too Large
表示用データ追加が音声処理の再設計へ膨らむ危険がある。  
**Control:** 表示用最小追加に限定する。

### Risk 2. Drawing Logic Accumulating in MainFrame
波形描画責務が main_frame に集中し、後続 block の接着が悪化する危険がある。  
**Control:** widget / renderer / model 分離を優先する。

### Risk 3. Performance Collapse on Large WAV
高密度描画で描画負荷が高くなる危険がある。  
**Control:** 可視幅ベース min/max 圧縮を採用する。

### Risk 4. Stereo Handling Expanding Scope
左右別表示へ広がり、B1 が肥大化する危険がある。  
**Control:** 1 本モノラル統合表示で固定する。

### Risk 5. Implicit Preview Leakage
イベント線やラベル表示が流入し、B2 の責務を侵食する危険がある。  
**Control:** B1 では左右端時刻ラベルまでに限定する。

### Risk 6. Premature Playback Coupling
再生位置線受け口を作る過程で再生ロジックまで流入する危険がある。  
**Control:** 受け口のみ作り、更新主体は B3 に送る。

---

## 16. Definition of Done

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. `WAV が有効` な状態で waveform placeholder が実波形表示へ置き換わる
2. `0.0 sec` と `duration_sec` を両端基準とする時間軸規約が存在し、任意の時刻を x 座標へ一意に写像できる
3. 波形描画は可視幅に応じた列単位 min/max 圧縮方式で成立している
4. 表示は mono / stereo を問わず 1 本のモノラル統合波形として成立している
5. 左端に `0.0 sec`、右端に `duration_sec` の時刻ラベルが表示される
6. 後続 block から再生位置線を更新できる受け口 API が存在する
7. 波形表示は `analysis_result_valid` に依存せず、`WAV が有効` なら成立する
8. MS14 の入力・解析・保存導線を壊していない
9. Zoom / Pan、Preview、再生 start/stop、イベント境界表示を流入させていない
10. B3/B4 が依存できる時間軸規約と再生位置線受け口 API が定義されている

---

## 17. Handoff Notes for Implementation

- B1 は波形表示基盤 block であり、再生 block ではない
- まず既存 `WavAnalysisResult` で足りるか確認すること
- 足りない場合でも表示用最小追加に留めること
- 描画粒度は可視幅ベース min/max 圧縮で固定すること
- 表示は 1 本モノラル統合波形で固定すること
- 補助表示は左右端時刻ラベルまでを必須とすること
- 再生位置線は受け口 API のみ作り、更新主体は B3 へ送ること
- Preview、イベント線、オートスクロール、Zoom/Pan を流入させないこと
- main_frame へ描画処理を密結合させないこと
- B1 完了時点で B3/B4 が依存できる構造条件を明示的に残すこと

---

## 18. Status Note

- **2026-04-17**: Revised draft for MS15-B1.  
  Done 条件の検証可能性を強化し、`WAV が有効` の定義、左右端時刻ラベルの成立基準、候補ファイルの責務分担、B1 範囲内失敗時の最小復帰方針、B3/B4 依存構造条件を明示した。
  