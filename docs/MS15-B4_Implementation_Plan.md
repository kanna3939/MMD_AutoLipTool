# MS15-B4_Implementation_Plan

## 1. Document Control

- Document Name: `MS15-B4_Implementation_Plan.md`
- Milestone: `MS15`
- Block: `MS15-B4`
- Title: `オートスクロールと再生中追従 UX`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS15-B4 では、MS15-B3 で成立した再生位置同期の上に、**再生位置が可視範囲の右端近傍へ到達したときの最小追従表示**を導入し、waveform / Preview の確認 UX を実用水準へ近づける。

本 block の目的は、DAW レベルの高度なスクロール UX を一気に完成させることではない。  
MS15-B4 は、以下を最小範囲で成立させるための block とする。

- waveform / Preview に最小 viewport API を追加すること
- 再生位置が右端近傍へ到達したときに可視範囲が追従すること
- waveform / Preview が同じ可視範囲で同時更新されること
- 最小の **X 軸 Zoom** を導入し、ユーザー側で追従挙動を確認できること
- 追従と Zoom が共通 viewport 規約の上で成立すること
- 将来の手動スクロール / Pan / 高度共存制御を壊さないこと

B4 は、**最小 viewport API 追加、オートスクロール、最小 Zoom を含む再生中追従 UX** に限定する。  
Pause、任意シーク、ループ再生、Y 軸 Zoom、DAW レベルの追従最適化、手動スクロール高度共存制御は本 block に含めない。

---

## 3. Fixed Decisions

### 3.1 B4 における viewport API 追加の扱い
現 repo 現在地で waveform / Preview に `set_viewport_sec(...)` が存在しない場合でも、B4 は停止せず、**B4 の最初の実装責務として最小 viewport API を追加する**。

ただし、追加範囲は以下に限定する。

- `waveform_panel.py` への `set_viewport_sec(start_sec: float, end_sec: float) -> None`
- `preview_panel.py` への `set_viewport_sec(start_sec: float, end_sec: float) -> None`
- 必要に応じた `clear_viewport_sec() -> None`
- viewport 範囲に基づく x 座標変換
- full-range / partial-range 描画の切り替え
- 既存 B1/B2 描画意味論を壊さない最小修正

この追加は、B1/B2 の手戻りではなく、B4 の **shared viewport / Zoom / follow を成立させるための直接前提整備**として扱う。

### 3.2 オートスクロール発火位置
オートスクロールは、**再生位置が可視範囲の右端近傍に到達したとき**に発火する。  
中央超過発火や常時中央維持は採らない。

### 3.3 発火閾値
右端近傍の閾値は、**可視幅の 80% 到達**で固定する。  
すなわち、以下を満たした時に追従判定対象とする。

- `playback_position_sec >= viewport_start_sec + viewport_span_sec * 0.8`

### 3.4 追従後の再生位置配置
追従発火後は、再生位置を**新しい可視範囲の 60% 位置付近**へ戻す。

- 新 viewport は、再生位置が `viewport_span_sec * 0.6` の位置に来るように計算する
- 追従後に毎回中央へ寄せない
- 発火 80% / 再配置 60% とすることで、可視幅の 20% 分のヒステリシスを確保する
- これにより、微小・高頻度な追従連発を避ける

### 3.5 viewport 解決の優先順位
viewport 解決時に以下の制約が衝突した場合、優先順位は次のとおりとする。

1. **viewport が `0.0 sec` ～ `duration_sec` の合法範囲に収まること**
2. **有効 span が最小可視幅制約を満たすこと**
3. **follow 時は playback position を 60% 位置へ置くこと**
4. **停止中 Zoom 時は center を維持すること**

すなわち、端部で clamp が必要な場合は、

- まず viewport の合法範囲を優先する
- その結果として 60% 配置や center 維持が厳密に成立しなくてもよい
- 60% / center は **best-effort** とする

### 3.6 waveform / Preview の更新基準
waveform / Preview は、**常に完全同時に同じ可視範囲へ更新する**。  
片方を正本にして 1 フレーム遅れで追従させる構成は採らない。

### 3.7 B4 に含める Zoom の位置づけ
B4 では、**オートスクロールをユーザーが確認できるようにするための最小 X 軸 Zoom** を実装対象に含める。

この Zoom は、

- viewport 概念を成立させる
- オートスクロール挙動を確認できるようにする
- waveform / Preview の同一可視範囲更新を実現する

ための最小機能であり、  
フル機能の Zoom / Pan system を導入するものではない。

### 3.8 Zoom の対象軸
B4 で扱う Zoom は、**X 軸（時間軸）のみ**とする。

- Y 軸方向の拡大縮小は行わない
- waveform / Preview ともに時間軸の可視幅のみを変更対象とする

### 3.9 Zoom 操作の最小セット
B4 で実装する Zoom 操作は、少なくとも以下とする。

- `Zoom In`
- `Zoom Out`
- `Reset Zoom`（全域表示へ戻す）

これにより、ユーザーは再生中追従の確認に必要な最小操作が行える。

### 3.10 Zoom UI の配置
B4 の Zoom UI は、既存の操作ボタン群 / operation area に **`Zoom In / Zoom Out / Reset Zoom` の最小ボタン**として追加する。

- メニュー深層のみに置かない
- アイコンや最終デザインは B4 の必須要件にしない
- ボタン文言や配置の細部は既存 UI に合わせた最小実装でよい
- enable / disable 規則の最終整理は B5 に送る

### 3.11 Zoom 段階
Zoom は、**離散段階の固定レベル**で扱う。  
B4 の基準レベルは以下とする。

- `1x`（全域表示）
- `2x`
- `4x`
- `8x`

ここでの `Nx` は、**可視幅 = `duration_sec / N`** を意味する。  
B4 では連続ズームやホイール倍率制御は導入しない。

### 3.12 duration の正本
B4 における `duration_sec` の正本は、**`selected_wav_analysis.duration_sec`** とする。

- Zoom 段階計算
- full-range 表示
- viewport clamp
- auto-follow の右端判定
- 最小可視幅判定

は、すべてこの正本 duration を基準に解決する。

### 3.13 最小可視幅
B4 では、極端に短い音声に対する不安定な過拡大を避けるため、**最小可視幅 `min_viewport_span_sec = min(duration_sec, 0.25)`** を導入する。

- 各 zoom 段階の要求 span は `duration_sec / zoom_factor`
- 実効 span は  
  `effective_span_sec = max(requested_span_sec, min_viewport_span_sec)`
- `duration_sec <= 0.25` の短尺音声では、高倍率 zoom でも実効 span は full-range に一致してよい
- その結果、高倍率 zoom が実質 no-op でも許容する

### 3.14 Reset Zoom の意味
`Reset Zoom` は、以下を意味する。

- B4 側の canonical shared viewport state を  
  - `viewport_start_sec = 0.0`
  - `viewport_end_sec = duration_sec`
  - `zoom_factor = 1x`
  に更新する
- その canonical state を waveform / Preview の両方へ **`set_viewport_sec(0.0, duration_sec)`** として適用する

`Reset Zoom` の正本は B4 側 state であり、`clear_viewport_sec()` は Reset の成立条件に使わない。  
`clear_viewport_sec()` は teardown / 補助用途に留めてよい。

### 3.15 再生中 Zoom のアンカー規則
再生中 Zoom では、**`playback_position_sec` を時間基準のアンカー**として扱う。  
ここでいうアンカーは、「新 viewport をどの時刻を基準に解くか」という意味であり、**画面上の x 位置を維持する意味ではない**。

したがって、再生中 Zoom 時は以下で解く。

- 基準時刻は `playback_position_sec`
- 新 viewport は、`playback_position_sec` が新可視範囲の **60% 位置**に来るように解決する
- これは auto-follow 後の再配置位置と同じ比率を用いる

### 3.16 停止中 Zoom のアンカー規則
停止中 Zoom では、**現在の canonical shared viewport center** をアンカーとする。

- 停止中は B4 側 canonical viewport state から center を計算する
- view 側から現在 viewport を問い合わせて anchor を決める構造は必須にしない
- 停止中 Zoom でも waveform / Preview は同じ新 viewport を受ける

### 3.17 full-range 時のオートスクロール
`1x` の全域表示では、可視幅が `duration_sec` 全体を覆う。  
この場合、オートスクロールは**発火しても viewport 更新が実質 no-op でよい**。

すなわち、

- 全域表示中に追従が必要でも、clamp 後に可視範囲が変わらないことを許容する
- B4 のユーザー側確認は、主に `2x` 以上の拡大状態で行う

### 3.18 Viewport 適用 API 契約
B4 では、waveform / Preview の両方が少なくとも以下の API を持つ状態へ整備する。

- `set_viewport_sec(start_sec: float, end_sec: float) -> None`

加えて、補助 API として以下を持ってよい。

- `clear_viewport_sec() -> None`

ただし、B4 の canonical reset や follow 解決は `set_viewport_sec(...)` を正本とする。  
B4 は reset / follow / zoom の成立に `clear_viewport_sec()` を必須依存しない。

### 3.19 canonical shared viewport の正本
B4 では、waveform / Preview 個別の viewport を独立管理せず、**B4 側で解決した canonical shared viewport** を両 view へ同時配布する。

- canonical state は B4 controller / helper 側に置く
- view 側は描画責務を持ち、viewport 決定責務は持たない
- waveform / Preview 側で追従判定を重複実装しない

### 3.20 手動 viewport 変更時の逆方向同期
手動スクロール UI または手動 viewport 変更 UI が存在する場合、**view 側で起きた viewport 変更は B4 の canonical state へ逆方向に通知する**。

少なくとも B4 は以下の入力を受けられる設計にする。

- `begin_user_viewport_interaction() -> None`
- `update_user_viewport_sec(start_sec: float, end_sec: float) -> None`
- `end_user_viewport_interaction() -> None`

これにより、

- B4 canonical state と view 表示の乖離を残さない
- 停止中 Zoom で古い viewport へ巻き戻ることを防ぐ
- 手動操作後も B4 正本を最新状態に保てる

ただし、現 repo 時点で手動スクロール UI が存在しない場合、この経路は dormant でよい。

### 3.21 手動変更時の zoom_factor 整合
手動 viewport 変更 UI が存在する場合、B4 で受ける手動変更は **現在の span を維持した位置変更のみ** を対象とする。

- すなわち `update_user_viewport_sec(start_sec, end_sec)` で受ける span は、原則として現在の canonical span と一致していることを前提とする
- span が許容誤差を超えて異なる場合、B4 はその変更を **位置変更としては受理せず、canonical span を維持するよう正規化してよい**
- したがって、手動変更によって任意の新可視幅を導入しない
- `zoom_factor` は離散段階 `1x / 2x / 4x / 8x` のまま維持する

これにより、手動逆方向同期と zoom factor の整合を保つ。

### 3.22 手動操作中の自動追従抑止
**手動スクロール UI が存在する場合に限り**、ユーザーが連続スクロール / ドラッグ操作中は自動追従を一時抑止する。

- 抑止開始は `begin_user_viewport_interaction()`
- 抑止中の viewport 正本更新は `update_user_viewport_sec(...)`
- 抑止解除は `end_user_viewport_interaction()`
- 手動スクロール UI が未実装なら、この抑止機構は dormant でよい
- B4 では最小の競合回避のみ入れる
- 一定時間停止や高度な共存制御は行わない

### 3.23 抑止解除直後の追従判定
`end_user_viewport_interaction()` の直後は、**その場で即 follow を発火しない**。  
抑止解除後の follow 判定は、**次の playback position 更新タイミング**で通常どおり行う。

これにより、

- 手動操作終了直後の即ジャンプを避ける
- follow 判定の基準を B3 の playback tick に統一する

### 3.24 `viewport_sec()` getter の位置づけ
B4 では、canonical shared viewport は controller 側が保持するため、**view 側の `viewport_sec()` getter を必須契約にはしない**。

- 停止中 Zoom の anchor は B4 canonical state から解く
- 手動操作が存在する場合は、getter ではなく **逆方向通知 API** によって canonical state を更新する
- したがって、`viewport_sec()` が無くても B4 は成立してよい

### 3.25 duration 更新時の再初期化
`selected_wav_analysis.duration_sec` が新しい音声読み込み等で更新された場合、B4 は canonical shared viewport state を**再初期化**する。

少なくとも以下を行う。

- `viewport_start_sec = 0.0`
- `viewport_end_sec = new_duration_sec`
- `zoom_factor = 1x`
- 手動 interaction / suppression 状態を解除
- waveform / Preview へ新 full-range viewport を適用

duration 更新後に旧 viewport を持ち越さない。

### 3.26 B3 / B5 との責務境界
B4 は、**B3 が供給する playback position を使って viewport を更新する block**である。  
したがって以下は B4 の責務外とする。

- playback state の生成
- Play / Stop の enable/disable 規則整理
- busy / playback / analysis の総合 state 統合
- status 文言の最終整理

これらは B3 / B5 に送る。

---

## 4. Goal

本節の項目群を、**MS15-B4 の canonical completion criteria** とする。  
後続の `13. Acceptance Criteria` および `16. Definition of Done` は意味差なしで本節を再掲する。

1. waveform / Preview の両方に `set_viewport_sec(start_sec, end_sec)` が存在する
2. Zoom が `1x / 2x / 4x / 8x` の離散段階で成立する
3. `Zoom In / Zoom Out / Reset Zoom` の最小操作が operation area から行える
4. `duration_sec` の正本は `selected_wav_analysis.duration_sec` に固定されている
5. waveform / Preview が同じ canonical shared viewport へ完全同時更新される
6. 再生位置が可視幅の 80% 到達時に追従判定される
7. 追従後、再生位置は新 viewport の 60% 位置付近へ解決される
8. viewport clamp とアンカー制約が衝突する場合は、合法 viewport を優先し、配置制約は best-effort で扱われる
9. `1x` 全域表示では、追従が実質 no-op でもよい
10. `2x` 以上の拡大状態でオートスクロールが視認可能である
11. `Reset Zoom` は B4 canonical state を full-range + `1x` に戻し、その状態を両 view へ適用する
12. 手動スクロール UI が存在する場合のみ、連続手動操作中は自動追従を一時抑止し、手動変更後の viewport を B4 正本へ逆方向同期する
13. 抑止解除直後は即 follow せず、次の playback position 更新タイミングで通常判定する
14. 手動 viewport 変更 UI が存在する場合でも、zoom factor は離散段階整合を維持する
15. `duration_sec` 更新時には B4 canonical state が再初期化される
16. B4 は playback position の供給側を作らず、B3 の供給に依存する
17. waveform / Preview の追従ロジックを view 側へ重複実装していない
18. Pause / Seek / Loop / shared viewport 高度化 / Zoom continuous control / Pan を流入させていない
19. B5/B6 が依存できる canonical shared viewport と最小 Zoom / follow 導線が定義されている

---

## 5. In Scope

MS15-B4 に含めるものは以下とする。

- waveform / Preview への最小 viewport API 追加
- `set_viewport_sec(start_sec, end_sec)` の実装
- viewport 範囲に基づく部分描画対応
- canonical shared viewport 概念の導入
- waveform / Preview 同時 viewport 更新
- 右端 80% 基準の追従判定
- 追従後 60% 位置解決
- clamp 優先順位の固定
- `Zoom In / Zoom Out / Reset Zoom`
- operation area への最小 Zoom UI 追加
- 離散段階 `1x / 2x / 4x / 8x`
- 再生中 Zoom 時の playback anchor 解決
- 停止中 Zoom 時の center anchor 解決
- `selected_wav_analysis.duration_sec` を正本とする viewport 解決
- 最小可視幅 0.25 sec ルール
- full-range 表示での no-op 許容
- 手動 viewport 変更 UI が存在する場合の逆方向同期
- 手動スクロール UI が存在する場合の最小抑止
- duration 更新時の canonical state 再初期化
- B4 に必要な軽量テストの追加または更新

---

## 6. Out of Scope

MS15-B4 では以下を行わない。

- Pause
- 任意シーク
- ループ再生
- 再生速度変更
- mp3 対応
- 音声のみ入力対応
- Y 軸 Zoom
- Zoom continuous control
- マウスホイール倍率制御
- Pan / drag scroll の全面実装
- 手動スクロール共存の高度制御
- 常時中央固定追従
- DAW レベルの滑らかさ最適化
- Play / Stop / busy / invalidate の総合 state 整理
- status 文言の全面整理
- B1/B2 の描画意味論の再設計

---

## 7. Expected Functional Boundary

B4 は「表示対象の時間範囲をどう決めるか」と「再生位置に対して viewport をどう動かすか」と「ユーザーがその追従を確認できる最小 Zoom をどう与えるか」を扱う block である。

責務分離は以下のとおり。

- **B1:** 波形表示基盤
- **B2:** Preview 表示基盤
- **B3:** 再生開始 / 停止と再生位置同期
- **B4:** viewport API / canonical shared viewport / Zoom / オートスクロール
- **B5:** 表示・再生状態統合
- **B6:** closeout

したがって B4 では、

- waveform / Preview に最小 viewport API を追加する
- B3 の playback position を受ける
- canonical shared viewport を計算する
- waveform / Preview へ同じ viewport を渡す
- Zoom 操作を最小限実動化する
- 手動 viewport 変更 UI が存在する場合のみ逆方向同期を受ける
- 手動スクロール UI が存在する場合のみ最小抑止を入れる
- duration 更新時に canonical state を再初期化する

が対象であり、

- 再生位置そのものを生成する
- B1/B2 の描画意味論を再設計する
- busy / action state を全面整理する
- DAW 的なスクロール最適化を行う
- Pan / 高度スクロール編集 UI を提供する

ことは行わない。

---

## 8. Current Recognition for B4 Entry

現時点の B4 着手前認識は以下とする。

### 8.1 実装側
- B1 により waveform 側の表示基盤が成立済みである
- B2 により Preview 側の表示基盤が成立済みである
- B3 により playback position の供給導線が成立済みである
- 現 repo では waveform / Preview の両方に `set_viewport_sec(...)` が存在しない可能性がある
- その場合でも、B4 の最初の実装責務として最小 viewport API を追加してよい
- 既存 wx 側では Zoom / canonical shared viewport / auto-follow は未整理の可能性が高い
- 手動スクロール UI が未実装である可能性がある
- duration 更新時の viewport reset 導線は未整理の可能性がある

### 8.2 B4 で再確認すべき領域
- waveform / Preview の現在の描画座標変換が viewport 化に最小修正で対応できるか
- B3 の playback position 更新が B4 の追従判定に十分安定しているか
- operation area へ Zoom UI を最小追加できるか
- waveform / Preview の同時更新が flicker や順序差なしで扱えるか
- `selected_wav_analysis.duration_sec` を B4 でも正本として使えるか
- 手動 viewport 変更 UI が現時点で存在するか
- 手動 UI が存在する場合、逆方向同期入力をどこで受けるか
- full-range 時の no-op 許容が UI 上違和感にならないか
- duration 更新時の reset トリガーをどこで受けるか

### 8.3 B4 の主眼
B4 の主眼は、**最小 viewport API、最小 Zoom、canonical shared viewport を導入し、再生中追従をユーザーが確認できる状態を作ること**にある。  
高度なスクロール UX や総合状態整理は B4 の主眼ではない。

---

## 9. Design Axes

### 9.1 Viewport Axis
- waveform / Preview に最小 viewport API を追加する
- canonical shared viewport を正本化する
- waveform / Preview へ同時配布する
- view 側へ追従判定を持たせない
- 手動 UI が存在する場合のみ逆方向同期を受ける

### 9.2 Trigger Axis
- 発火は右端 80%
- 追従後は 60% 位置解決
- full-range では no-op を許容する
- `duration_sec` clamp は正本 duration に従う
- 端部では合法 viewport を優先する

### 9.3 Zoom Axis
- X 軸のみ
- 離散段階 `1x / 2x / 4x / 8x`
- `Zoom In / Zoom Out / Reset Zoom`
- operation area に最小 UI を置く
- 再生中は playback position を時間アンカーにする
- 停止中は canonical viewport center をアンカーにする
- 最小可視幅は 0.25 sec（ただし duration 未満に clamp）

### 9.4 Sync Axis
- waveform / Preview 完全同時更新
- 片側正本 / 次フレーム追従は採らない
- B3 が位置供給源、B4 が viewport 供給源
- duration 更新時は canonical state を reset する

### 9.5 Conflict Axis
- 手動スクロール UI が存在する場合のみ最小抑止
- 手動 viewport 変更 UI が存在する場合のみ逆方向同期
- 高度な手動共存は導入しない
- B5 の state 統合を先食いしない

---

## 10. Candidate File Touch Areas

B4 で変更対象になり得るファイルは、以下を主候補とする。

### コード
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/waveform_panel.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/ui_state.py`（必要最小限）

### 新規追加候補と最小責務
- `src/gui_wx/viewport_controller.py`
  - canonical shared viewport の正本
  - auto-follow 判定
  - Zoom in/out/reset
  - anchor 解決
  - 手動変更の逆方向同期受け口
  - duration 更新時 reset
- `src/gui_wx/viewport_state.py`
  - `viewport_start_sec`
  - `viewport_end_sec`
  - `zoom_factor`
  - 手動操作抑止状態（必要最小限）
  - ただし `ui_state.py` へ小さく追加する方が自然なら分離必須ではない
- `src/gui_wx/zoom_actions.py`
  - Zoom 操作の最小整理
  - ただし責務が薄い場合は controller 内包でよい

### テスト
- B4 用の viewport / zoom テスト
- viewport API 追加テスト
- auto-follow 判定テスト
- waveform / Preview 同時更新テスト
- Reset Zoom canonical sync テスト
- full-range no-op テスト
- 手動操作抑止の条件付きテスト
- 手動変更逆方向同期の条件付きテスト
- duration 更新時 reset テスト
- clamp 優先順位テスト
- 最小可視幅テスト

---

## 11. Execution Policy

### 11.1 まず既存描画構造を確認する
最初に、waveform / Preview の現在の描画構造を確認し、最小修正で viewport 範囲に基づく描画へ拡張できるか確認する。

確認結果が以下であれば、B4 を進めてよい。

- `set_viewport_sec(start_sec, end_sec)` を追加できる
- view 側が viewport に従って描画更新できる
- B1/B2 の描画意味論を再設計せずに済む
- B3 からの playback position と併用できる

逆に、以下のいずれかが判明した場合は、**B4 を実装開始せず停止して報告する**。

- viewport API 追加に B1/B2 の描画意味論再設計が必要
- 両 view の同期更新が構造上成立しない
- B4 実装に B1/B2 の大規模改修が不可避

### 11.2 最小 viewport API を先に追加する
auto-follow / Zoom より先に、waveform / Preview の両方へ `set_viewport_sec(...)` を追加する。  
これを B4 の最初の実装 step とする。

### 11.3 canonical shared viewport を固定する
viewport API 追加後に、canonical shared viewport state とその配布導線を固定する。  
追従判定や Zoom は、その canonical state の上に載せる。

### 11.4 duration 正本を先に固定する
B4 の全 viewport 計算は、`selected_wav_analysis.duration_sec` を正本として行う。  
view 側や playback 側から duration を逆算しない。

### 11.5 clamp 優先順位を先に固定する
viewport 解決時は、

1. 合法範囲
2. 最小可視幅
3. 配置制約

の順に解く。  
端部では 60% 配置や center 維持が崩れてもよい。

### 11.6 Zoom をユーザー検証用の最小範囲に留める
B4 で導入する Zoom は、  
**オートスクロール確認に必要な最小セット**に留める。

- 離散段階のみ
- X 軸のみ
- reset あり
- Pan なし
- operation area への最小 UI 追加のみ

### 11.7 follow と Zoom の規約を分離する
auto-follow の再配置規則は **80% 発火 / 60% 再配置** で固定する。  
再生中 Zoom は **playback time を時間アンカーにしつつ、表示位置は 60% 基準で解く** と明記し、計算責務を混線させない。

### 11.8 手動系は存在時のみ接続する
手動 viewport 変更 UI が存在する場合のみ、逆方向同期 API を接続する。  
手動スクロール UI が存在する場合のみ、抑止 API を接続する。  
存在しない場合はこれらの経路を dormant でよい。

### 11.9 抑止解除直後は即 follow しない
`end_user_viewport_interaction()` 直後は viewport を保持し、次の playback tick で通常判定する。  
解除イベント単体では follow を発火しない。

### 11.10 duration 更新時は full-range reset する
新しい音声が入ったら、B4 canonical state は full-range + `1x` に reset する。  
旧 duration 前提の viewport は持ち越さない。

### 11.11 B5 の責務を先食いしない
Zoom ボタンや follow 状態に関する enable/disable の最終整理、status 文言統合は B5 に送る。

---

## 12. Step Breakdown

### Step 0. Confirm Entry Gate
- B3 の playback position 供給が成立済みか確認する
- waveform / Preview の現在の描画構造を確認する
- `selected_wav_analysis.duration_sec` が B4 から参照可能か確認する
- operation area へ Zoom UI を最小追加できるか確認する

#### Exit Condition
- B4 実装開始条件が満たされている  
  **または**
- B4 実装に B1/B2 の描画意味論再設計や大規模改修が必要であることが明確になっている

---

### Step 1. Add Minimal Viewport API to Views
- `waveform_panel.py` に `set_viewport_sec(start_sec, end_sec)` を追加する
- `preview_panel.py` に `set_viewport_sec(start_sec, end_sec)` を追加する
- 必要に応じて `clear_viewport_sec()` を追加する
- viewport 範囲に基づく x 座標変換へ最小対応する
- full-range / partial-range 描画を切り替えられるようにする

#### Exit Condition
- waveform / Preview の両方が viewport 指定を受けて描画できる
- B1/B2 の描画意味論を壊していない

---

### Step 2. Define Canonical Shared Viewport Contract
- canonical shared viewport state を定義する
- `viewport_start_sec / viewport_end_sec / zoom_factor` の最小境界を決める
- `duration_sec` 正本を固定する
- clamp 優先順位を固定する
- waveform / Preview へ同時配布する導線を決める

#### Exit Condition
- B4 の canonical shared viewport 契約が定義されている

---

### Step 3. Implement Viewport Application Path
- waveform / Preview へ同一 viewport を適用する
- full-range / zoomed-range の両方で更新できるようにする
- `Reset Zoom` が canonical state → view 適用の順で動くようにする

#### Exit Condition
- waveform / Preview が canonical shared viewport で同期描画される
- Reset 時の state / view 同期が明確に成立している

---

### Step 4. Implement Minimal Zoom
- `Zoom In / Zoom Out / Reset Zoom` を実装する
- operation area へ最小 Zoom UI を追加する
- 離散段階 `1x / 2x / 4x / 8x` を実装する
- 再生中は playback time anchor + 60% 配置で解決する
- 停止中は canonical viewport center anchor で解決する
- 最小可視幅 0.25 sec ルールを入れる

#### Exit Condition
- Zoom が canonical shared viewport 上で成立している
- `1x` full-range と `2x+` zoomed-range を切り替えられる
- ユーザーが Zoom UI を操作できる

---

### Step 5. Implement Auto-follow Trigger
- 右端 80% 判定を実装する
- 発火時に playback position が 60% 位置へ来るよう viewport を更新する
- duration clamp を入れる
- full-range では no-op を許容する

#### Exit Condition
- 再生中追従が最小ルールで成立している
- 微小・高頻度の追従連発が抑えられる

---

### Step 6. Add Conditional Reverse Sync and Suppression
- 手動 viewport 変更 UI が存在する場合のみ  
  - `begin_user_viewport_interaction()`
  - `update_user_viewport_sec(...)`
  - `end_user_viewport_interaction()`
  を接続する
- 手動更新は現在 span 維持の位置変更のみ受理する
- 手動スクロール UI が存在する場合のみ、操作中の自動追従抑止を接続する
- 抑止解除直後は即 follow せず、次 playback tick で通常判定する
- UI 未実装なら、この step を no-op としてよい

#### Exit Condition
- 手動 UI 存在時のみ条件付き逆方向同期 / 抑止が成立している  
  **または**
- 手動 UI 未実装のため、B4 がその前提で破綻しないことが確認されている

---

### Step 7. Add Duration-change Reset Path
- `selected_wav_analysis.duration_sec` 更新時の reset トリガーを接続する
- canonical state を full-range + `1x` へ戻す
- waveform / Preview へ新 viewport を適用する
- 抑止状態を解除する

#### Exit Condition
- duration 更新時に旧 viewport を持ち越さない

---

### Step 8. Wire Playback Loop
- B3 の playback position 更新から follow 判定へ接続する
- waveform / Preview の同時更新導線を確定する

#### Exit Condition
- ユーザーが Zoom を操作でき、再生中追従を確認できる

---

### Step 9. Add / Update Lightweight Tests
- viewport API 追加確認
- canonical shared viewport 同時更新確認
- Zoom In / Out / Reset 確認
- `1x / 2x / 4x / 8x` 確認
- 80% 発火確認
- 60% 再配置確認
- full-range no-op 確認
- waveform / Preview 同時更新確認
- Reset 時 state / view 同期確認
- clamp 優先順位確認
- 最小可視幅確認
- 手動 UI が存在する場合のみ逆方向同期確認
- 手動 UI が存在する場合のみ抑止確認
- duration 更新時 reset 確認

#### Exit Condition
- B4 の接着点が最低限テストで担保されている

---

### Step 10. Re-check Scope Guard
- Pause が流入していないか
- Seek が流入していないか
- Loop が流入していないか
- Y 軸 Zoom が流入していないか
- continuous Zoom が流入していないか
- Pan が流入していないか
- B5 の state 統合を先食いしていないか
- B1/B2 の描画意味論を再設計していないか

#### Exit Condition
- B4 が B4 の責務範囲に収まっている

---

## 13. Acceptance Criteria

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. waveform / Preview の両方に `set_viewport_sec(start_sec, end_sec)` が存在する
2. Zoom が `1x / 2x / 4x / 8x` の離散段階で成立する
3. `Zoom In / Zoom Out / Reset Zoom` の最小操作が operation area から行える
4. `duration_sec` の正本は `selected_wav_analysis.duration_sec` に固定されている
5. waveform / Preview が同じ canonical shared viewport へ完全同時更新される
6. 再生位置が可視幅の 80% 到達時に追従判定される
7. 追従後、再生位置は新 viewport の 60% 位置付近へ解決される
8. viewport clamp とアンカー制約が衝突する場合は、合法 viewport を優先し、配置制約は best-effort で扱われる
9. `1x` 全域表示では、追従が実質 no-op でもよい
10. `2x` 以上の拡大状態でオートスクロールが視認可能である
11. `Reset Zoom` は B4 canonical state を full-range + `1x` に戻し、その状態を両 view へ適用する
12. 手動スクロール UI が存在する場合のみ、連続手動操作中は自動追従を一時抑止し、手動変更後の viewport を B4 正本へ逆方向同期する
13. 抑止解除直後は即 follow せず、次の playback position 更新タイミングで通常判定する
14. 手動 viewport 変更 UI が存在する場合でも、zoom factor は離散段階整合を維持する
15. `duration_sec` 更新時には B4 canonical state が再初期化される
16. B4 は playback position の供給側を作らず、B3 の供給に依存する
17. waveform / Preview の追従ロジックを view 側へ重複実装していない
18. Pause / Seek / Loop / shared viewport 高度化 / Zoom continuous control / Pan を流入させていない
19. B5/B6 が依存できる canonical shared viewport と最小 Zoom / follow 導線が定義されている

---

## 14. Verification Plan

### 14.1 Runtime / Integration Checks

#### 14.1.1 Viewport API
**自動化対象**
- waveform に `set_viewport_sec(...)` が存在する
- Preview に `set_viewport_sec(...)` が存在する
- full-range / partial-range の両方で描画できる

**手動確認対象**
- viewport 指定後に waveform / Preview の表示範囲が変わる
- B1/B2 の基本表示が壊れていない

#### 14.1.2 Zoom Startup
**自動化対象**
- `Zoom In / Zoom Out / Reset Zoom` が呼べる
- `1x / 2x / 4x / 8x` が解決できる

**手動確認対象**
- operation area から Zoom 操作できる
- 実際に拡大・縮小表示が変わる
- waveform / Preview の可視範囲が同時に変わる

#### 14.1.3 Canonical Shared Viewport Sync
**自動化対象**
- waveform / Preview が同一 viewport 値を受ける
- 同じ可視範囲へ更新される
- `duration_sec` 正本に基づいて clamp される

**手動確認対象**
- 片方だけ遅れる / ずれる現象がない

#### 14.1.4 Auto-follow Trigger
**自動化対象**
- 80% 到達で追従判定が発火する
- 発火前は不要に動かない
- 発火後に 60% 位置へ再配置される
- 端部では合法 viewport 優先で解決される

**手動確認対象**
- 追従が急すぎず、かつ高頻度連発にならない

#### 14.1.5 Full-range No-op
**自動化対象**
- `1x` 全域表示時に follow が必要でも viewport 更新が no-op で許容される
- 例外や破綻が起きない

**手動確認対象**
- 全域表示で不自然なジャンプがない

#### 14.1.6 Zoomed Follow
**自動化対象**
- `2x` 以上の拡大状態で follow が視認可能
- waveform / Preview が同じ追従結果になる

**手動確認対象**
- ユーザーが追従挙動を確認できる

#### 14.1.7 Reset Canonical Sync
**自動化対象**
- `Reset Zoom` で B4 canonical state が full-range + `1x` に戻る
- 両 view がその状態へ同期する
- `clear_viewport_sec()` の有無に依存せず成立する

**手動確認対象**
- Reset 後に内部状態と表示状態がズレない

#### 14.1.8 Conditional Reverse Sync and Suppression
**自動化対象**
- 手動 viewport 変更 UI が存在する場合のみ、逆方向同期が働く
- 手動スクロール UI が存在する場合のみ、抑止が働く
- 抑止解除直後は即 follow せず、次 tick で通常判定する
- UI 未実装なら B4 がその前提で破綻しない

**手動確認対象**
- 手動操作後に Zoom / follow で古い viewport へ巻き戻らない
- 手動操作中に追従が競合し続けない

#### 14.1.9 Duration-change Reset
**自動化対象**
- duration 更新時に canonical state が full-range + `1x` に戻る
- waveform / Preview が新 duration 前提の viewport を受ける
- 抑止状態が解除される

**手動確認対象**
- 新しい音声読み込み後に旧 viewport を引きずらない

### 14.2 Review / Audit Checks

#### 14.2.1 Scope Review
**レビュー対象**
- Pause が流入していない
- Seek が流入していない
- Loop が流入していない
- Y 軸 Zoom が流入していない
- continuous Zoom が流入していない
- Pan が流入していない
- 手動スクロール高度共存が流入していない

#### 14.2.2 Architecture Review
**レビュー対象**
- canonical shared viewport の正本が一元化されている
- waveform / Preview 側へ追従判定が漏れていない
- Zoom と follow の計算責務が混線していない
- B5 の state 整理を先食いしていない
- B1/B2 の描画意味論を再設計していない
- 手動 UI 存在時の逆方向同期経路が明確である
- duration 更新時 reset 経路が明確である

---

## 15. Risks and Control

### Risk 1. No User-checkable Follow
Zoom が無いと、オートスクロールが内部実装だけで終わり、ユーザー確認ができない危険がある。  
**Control:** B4 に最小 X 軸 Zoom を含める。

### Risk 2. Viewport API Missing
現 repo では waveform / Preview に viewport API が無く、B4 の前提が不足する危険がある。  
**Control:** B4 の最初の実装責務として最小 `set_viewport_sec(...)` を追加する。

### Risk 3. View Desync
waveform / Preview の viewport 更新順がずれ、視覚的不整合が出る危険がある。  
**Control:** canonical shared viewport を正本化し、同時配布する。

### Risk 4. Over-frequent Follow
追従閾値と再配置差が小さすぎると微小更新が連発する危険がある。  
**Control:** 発火 80%、再配置 60% でヒステリシスを確保する。

### Risk 5. Full-range Ambiguity
全域表示では follow が見えず、実装が誤解される危険がある。  
**Control:** full-range no-op を明示し、確認は `2x` 以上を前提にする。

### Risk 6. Scope Creep into Full Zoom/Pan System
Zoom を導入した結果、Pan や continuous zoom まで流入する危険がある。  
**Control:** 離散 X 軸 Zoom のみ、Pan なしで固定する。

### Risk 7. Canonical/View State Drift
Reset や手動操作後に B4 正本と view 表示がずれる危険がある。  
**Control:** canonical shared viewport を正本化し、Reset は state→view の順で同期し、手動 UI 存在時は逆方向同期を必須化する。

### Risk 8. Manual Interaction Conflict
手動操作と自動追従が競合し、UX が破綻する危険がある。  
**Control:** 手動スクロール UI が存在する場合のみ条件付き最小抑止を入れる。

### Risk 9. B3/B5 Responsibility Mixing
B4 が playback state 生成や action state 整理へ踏み込む危険がある。  
**Control:** B4 は viewport 供給側に限定し、B3/B5 の責務を先食いしない。

### Risk 10. Short-duration Overzoom
短尺音声で高倍率 zoom が不安定になる危険がある。  
**Control:** 最小可視幅 0.25 sec ルールを導入し、必要なら no-op を許容する。

### Risk 11. Clamp/Anchor Conflict
端部で clamp と配置制約が衝突し、解が不安定になる危険がある。  
**Control:** 合法 viewport を優先し、配置制約は best-effort とする。

---

## 16. Definition of Done

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. waveform / Preview の両方に `set_viewport_sec(start_sec, end_sec)` が存在する
2. Zoom が `1x / 2x / 4x / 8x` の離散段階で成立する
3. `Zoom In / Zoom Out / Reset Zoom` の最小操作が operation area から行える
4. `duration_sec` の正本は `selected_wav_analysis.duration_sec` に固定されている
5. waveform / Preview が同じ canonical shared viewport へ完全同時更新される
6. 再生位置が可視幅の 80% 到達時に追従判定される
7. 追従後、再生位置は新 viewport の 60% 位置付近へ解決される
8. viewport clamp とアンカー制約が衝突する場合は、合法 viewport を優先し、配置制約は best-effort で扱われる
9. `1x` 全域表示では、追従が実質 no-op でもよい
10. `2x` 以上の拡大状態でオートスクロールが視認可能である
11. `Reset Zoom` は B4 canonical state を full-range + `1x` に戻し、その状態を両 view へ適用する
12. 手動スクロール UI が存在する場合のみ、連続手動操作中は自動追従を一時抑止し、手動変更後の viewport を B4 正本へ逆方向同期する
13. 抑止解除直後は即 follow せず、次の playback position 更新タイミングで通常判定する
14. 手動 viewport 変更 UI が存在する場合でも、zoom factor は離散段階整合を維持する
15. `duration_sec` 更新時には B4 canonical state が再初期化される
16. B4 は playback position の供給側を作らず、B3 の供給に依存する
17. waveform / Preview の追従ロジックを view 側へ重複実装していない
18. Pause / Seek / Loop / shared viewport 高度化 / Zoom continuous control / Pan を流入させていない
19. B5/B6 が依存できる canonical shared viewport と最小 Zoom / follow 導線が定義されている

---

## 17. Handoff Notes for Implementation

- B4 はオートスクロールと再生中追従 UX block であり、最小 Zoom と最小 viewport API 追加を含む
- 現 repo に viewport API が無い場合でも、B4 の最初の責務として `set_viewport_sec(...)` を waveform / Preview に追加すること
- B1/B2 の描画意味論を再設計しないこと
- オートスクロール発火位置は右端 80% 固定とすること
- 追従後の再生位置は 60% 付近へ戻すこと
- waveform / Preview は完全同時に同じ viewport を受けること
- canonical shared viewport の正本は B4 側に置くこと
- B4 で実装する Zoom は X 軸のみ、離散 `1x / 2x / 4x / 8x` とすること
- `Zoom In / Zoom Out / Reset Zoom` の最小操作を operation area に導入すること
- `duration_sec` の正本は `selected_wav_analysis.duration_sec` とすること
- clamp と配置制約が衝突したら合法 viewport を優先すること
- 再生中 Zoom は playback time を時間アンカーとしつつ、表示位置は 60% 基準で解くこと
- 停止中 Zoom は canonical viewport center をアンカーにすること
- `Reset Zoom` は canonical state を full-range + `1x` に戻し、その後 view へ適用すること
- `1x` 全域表示では follow が no-op でよいこと
- ユーザー側確認は主に `2x` 以上で成立させること
- 手動 viewport 変更 UI が存在する場合のみ逆方向同期 API を接続すること
- 手動変更は span 維持の位置変更のみ受理すること
- 手動スクロール UI が存在する場合のみ条件付き最小抑止を入れること
- 抑止解除直後は即 follow せず、次 playback tick で通常判定すること
- duration 更新時は canonical state を full-range + `1x` に reset すること
- Pause / Seek / Loop / continuous zoom / Pan を流入させないこと
- playback state や action state 整理を B4 に流入させないこと

---

## 18. Status Note

- **2026-04-22**: Revised draft for MS15-B4.  
  現 repo で waveform / Preview に viewport API が未実装であることを前提に、B4 の最初の実装責務として `set_viewport_sec(...)` を両 view に追加する方針へ修正した。あわせて、operation area への最小 Zoom UI、オートスクロール発火位置 80%、追従後再配置 60%、`selected_wav_analysis.duration_sec` を正本とする canonical shared viewport、Reset 時の state→view 同期、手動 UI 存在時の逆方向同期 / 条件付き抑止、clamp 優先順位、最小可視幅 0.25 sec、duration 更新時 reset を B4 scope として明示した。
