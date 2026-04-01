# MS11-9 Implementation Plan
## Preview trapezoid / multi-point display alignment

## 実装反映注記（2026-04-01）

- 本計画書は実装前方針の正本として作成されたが、2026-04-01 時点で current workspace では MS11-9 実装が反映済みである。
- 反映済みの到達状態は以下とする。
  - `src/gui/preview_transform.py` は `rows -> segments` フローを維持したまま、`PreviewControlPoint` と `shape_kind` / `control_points` を追加し、shape-aware な Preview 契約へ拡張済み
  - shape semantics は writer と同じ 30fps frame basis で再構成し、描画用には seconds basis へ再変換する方針を反映済み
  - MS11-2 asymmetric trapezoid、legacy triangle / legacy symmetric trapezoid、MS11-3 representative multi-point envelope、MS11-8 closing softness による final closing-only extension と clamp を Preview 側で表現可能
  - `src/gui/preview_area.py` は矩形塗りつぶし中心描画から polygon / path ベース shape 描画へ更新済み
  - shared viewport / playback cursor / waveform plot area rect 基準整合は維持済み
  - `src/gui/main_window.py` は既存 handoff を維持し、MS11-9 のための追加 wiring は最小化されている
  - `tests/test_preview_transform.py` は、trapezoid / legacy 区別 / multi-point / closing softness / mixed case clamp の確認へ更新済み

---

## 1. 目的

MS11-9 の目的は、Preview 表示を現行の simple filled-area style から、writer 側 actual output-shape semantics により近い表示へ揃えることである。

本マイルストーンは GUI の単なる見た目調整ではない。
writer 側で既に導入されている以下の shape semantics を、Preview 側でも破綻なく反映できるようにする。

- MS11-2 の trapezoid / legacy shape semantics
- MS11-3 の multi-point envelope semantics
- MS11-8 の closing softness semantics

ただし、MS12 の GUI responsiveness / splash / startup / packaging には広げない。

---

## 2. 現状整理

### 2-1. 現行 Preview の制約
現行 `preview_transform.py` は、`timeline` を `PreviewData -> PreviewRow -> PreviewSegment` に変換し、各 event について以下しか保持していない。

- `start_sec`
- `end_sec`
- `duration_sec`
- `intensity`
- `vowel`

このため、shape の折れ点列、shape kind、closing edge の延長情報、multi-point の valley / top 列は保持できない。

### 2-2. 現行 Preview 描画の制約
現行 `preview_area.py` は、各 `PreviewSegment` を矩形の塗りつぶしとして描画している。
したがって、以下は視覚表現できていない。

- trapezoid の rise shoulder / top plateau / fall shoulder
- legacy triangle と legacy symmetric trapezoid の差
- multi-point envelope の中間 valley / 複数 top
- closing softness による final descent の延長

### 2-3. handoff の現状
現行 `main_window.py` は以下の最小 handoff 構成で Preview を更新している。

- `current_timing_plan.timeline`
- `build_preview_data(self.current_timing_plan.timeline)`
- `preview_area.set_preview_data(preview_data)`

このため、MS11-9 の主変更点は `preview_transform.py` / `preview_area.py` に集中させ、`main_window.py` の変更は必要最小限に留める方針とする。

### 2-4. writer 側の前提
writer 側には既に以下が存在する。

- `AsymmetricTrapezoidSpec`
- `EnvelopeControlPoint`
- `MultiPointEnvelopeSpec`
- trapezoid expansion
- multi-point expansion
- `closing_softness_frames` による final closing 延長
- 後続 shape 開始前での clamp

Preview 側は、これらと矛盾しない shape 表示に寄せる必要がある。

---

## 3. 今回固定された方針

### 3-1. Preview 中間契約
既存の `rows -> segments` の流れはできるだけ維持する。
ただし、MS11-9 に必要な最小限の shape 情報追加は許可する。

### 3-2. スコープ
- trapezoid 表示は必須
- multi-point は「無理なく載せられる範囲」で含める
- ただし multi-point を完全に無視する実装にはしない

### 3-3. 時間軸基準
- Preview の表示 API / viewport / playback は秒ベースを維持する
- shape の折れ点算出は writer と同じ 30fps frame basis に寄せる
- つまり「描画入力は秒ベース」「shape semantics は frame basis」で揃える

---

## 4. 非目標

今回やらないことを明確にする。

- MS12 領域（応答性改善、起動高速化、splash、packaging）
- waveform 側 overlay の大規模設計変更
- view_sync / playback_controller の仕様変更
- writer 側 shape logic の意味変更
- pipeline 側の大規模な責務追加
- Preview に対する新しいユーザー操作追加
- Preview shape 編集 UI の導入

---

## 5. 対象ファイル

### 主対象
- `src/gui/preview_transform.py`
- `src/gui/preview_area.py`

### 必要最小限で変更可
- `src/gui/main_window.py`

### 参照専用に近いが整合確認対象
- `src/vmd_writer/writer.py`
- `src/core/pipeline.py`

### テスト対象
- `tests/test_preview_transform.py`
- Preview 関連の追加テスト
- 必要なら viewport / playback sync に関する既存 GUI テスト

---

## 6. 実装方針

## 6-1. Preview 契約の拡張方針
現行の `PreviewSegment` だけでは writer-side shape semantics を表せないため、
Preview 用中間契約に「shape を描画可能な情報」を追加する。

ただし全面差し替えは避け、既存の `rows -> segments` の流れをできるだけ残す。

推奨方針は以下のいずれかである。

### 方針A
`PreviewSegment` を拡張し、以下を保持できるようにする。

- `shape_kind`
- `control_points_sec`
- `peak_value`
- 必要最小限の metadata

### 方針B
`PreviewSegment` は残しつつ、描画専用の polyline / polygon データを別 field として持たせる。

どちらでもよいが、重要なのは以下である。

- trapezoid を 4 点以上で描けること
- multi-point を複数 control point で描けること
- closing softness により final end-zero のみ延長された形を表せること
- 秒ベース描画に使えること

---

## 6-2. writer semantics との整合方針
Preview 側は独自 shape を発明しない。
writer 側で成立している semantics を Preview 用に変換して可視化する。

特に以下は一致対象とする。

### MS11-2 / legacy 系
- `start`
- `peak_start`
- `peak_end`
- `end`

### MS11-3 系
- `start_zero`
- `top`
- `valley`
- `top`
- ...
- `end_zero`

### MS11-8 closing softness
- trapezoid 系: `fall_start` 固定、`end` のみ延長
- multi-point 系: final non-zero 固定、final `end_zero` のみ延長
- 後続 shape 開始前で clamp

Preview は見た目だけ似せるのではなく、
「どの点が固定され、どの点が動くか」を writer semantics と一致させる。

---

## 6-3. frame basis と seconds basis の橋渡し
writer 側 shape は frame basis で意味が確定しているため、
Preview 側では内部的に以下の流れを取る。

1. `timeline` から shape semantic を frame basis で解決
2. 描画用に frame を seconds に再変換
3. `preview_area.py` で seconds ベース描画

これにより、以下の両立を取る。

- writer と同じ shape semantics
- 既存 viewport / playback / waveform alignment との互換

---

## 7. 実装フェーズ

## Phase 1. Preview 契約の再設計
`preview_transform.py` の中間契約を見直す。

### 作業
- 現行 `PreviewSegment` 契約のまま不足している点を整理
- 最小拡張で shape 表現可能な dataclass 群を追加
- 既存 rows/segments フローを壊しすぎない構造にする
- trapezoid / multi-point の両方を扱える形にする

### この段階の完了条件
- Preview 描画に必要な折れ点列を保持できる
- 既存の `PreviewData` 更新経路を維持できる見通しが立つ

---

## Phase 2. trapezoid shape 変換の導入
`timeline` の各 point について、writer 側の single-event shape semantics に近い Preview shape を生成する。

### 作業
- MS11-2 asymmetric trapezoid の shape 生成
- legacy triangle / legacy symmetric trapezoid の shape 生成
- 既存 Preview intensity 依存の単純矩形生成を置き換える
- shape 生成は frame basis で計算し、描画用に seconds 化する

### 注意
- writer の意味を変えない
- Preview 側で勝手な shoulder 幅を発明しない
- interval が短い場合の legacy fallback も表現差を残す

### この段階の完了条件
- 単一 event について、矩形ではなく trapezoid / triangle 相当の形で描ける
- MS11-8 softness=0 の writer shape に視覚的に近い

---

## Phase 3. MS11-8 closing softness 表示反映
closing softness を Preview shape に反映する。

### 作業
- trapezoid 系で final descent のみ延長
- legacy 系でも end-zero 側のみ延長
- 後続 shape 開始前で clamp
- fall-start / top / valley など、動かない点を動かさない

### 注意
- 単純に `end_sec` を広げるだけの実装にしない
- 必ず「final closing edge だけが伸びる」見え方にする

### この段階の完了条件
- softness=0 は現状互換
- softness>0 で final descent のみ長くなる
- 後続 shape が近い場合は clamp される

---

## Phase 4. multi-point compatible 表示の導入
multi-point group が成立するケースでは、Preview 側でも複数 top / valley を表示できるようにする。

### 作業
- 複数 top を持つ shape の描画対応
- valley を 0 に落とさない中間折れ点として描画
- final end-zero のみ softness による延長対象とする
- multi-point 不成立時は既存 fallback shape に戻る

### 注意
- roadmap 上は multi-point も対象だが、無理に全面導入しない
- 「writer が multi-point を採用したケース」を正しく可視化できればよい
- multi-point 不成立時の fallback semantics を壊さない

### この段階の完了条件
- 少なくとも 2-top / 3-top の multi-point shape を Preview で表現できる
- valley が visual 上で確認できる
- final end-zero softness も反映される

---

## Phase 5. preview_area 描画ロジックの更新
新しい shape 契約に対応した描画へ置き換える。

### 作業
- 矩形塗りつぶしから polygon / path ベース描画へ変更
- row clipping / visible range clipping を維持
- viewport 中だけを描く
- playback cursor の既存描画を維持
- waveform plot area rect を使った横軸整合を維持

### 注意
- `set_viewport_sec()`
- `set_playback_position_sec()`
- `set_waveform_plot_area_rect()`

これらの既存導線は壊さない。

### この段階の完了条件
- shared viewport の pan / zoom と共存できる
- playback cursor が従来通り動く
- waveform 横軸との整合が崩れない

---

## Phase 6. main_window の最小調整
必要なら handoff 層だけ最小修正する。

### 作業候補
- `build_preview_data(...)` の新契約への追従
- 必要なら Preview へ渡す付帯情報の最小追加
- それ以外の UI 制御には極力触れない

### 完了条件
- 既存の Preview 更新フローが維持される
- shared viewport / playback sync の wiring を壊さない

---

## Phase 7. テスト追加・更新
MS11-9 の主眼は shape semantics alignment なので、見た目ではなく契約と折れ点結果をテストする。

### 最低限必要なテスト
#### `tests/test_preview_transform.py`
- empty input 互換
- fixed 5 rows 互換
- trapezoid 用 shape データ生成
- legacy triangle / symmetric trapezoid の区別
- multi-point shape データ生成
- closing softness で final end-zero のみ延長されること
- 後続 shape による clamp
- unsupported vowel の無視互換

#### 可能なら追加
#### `tests/test_preview_area_*.py`
- viewport clipping 時に shape が正しく切られる
- playback cursor 描画導線が壊れていない
- waveform_plot_area_rect 使用時の timeline rect が維持される

### 注意
GUI のピクセル完全一致までは不要。
shape 契約と描画に渡る幾何情報が正しいことを優先する。

---

## 8. 完了条件

MS11-9 完了とみなす条件は以下とする。

1. Preview が単一矩形塗りつぶしではなく、writer-side shape semantics に近い形を描ける
2. trapezoid 表示は必ず反映される
3. multi-point は少なくとも代表ケースで表現できる
4. MS11-8 closing softness が Preview にも反映される
5. final closing 延長は後続 shape 前で clamp される
6. shared viewport / playback sync を壊していない
7. waveform の plot area rect 基準整合を壊していない
8. 関連テストが通る

---

## 9. 実装上の注意事項

- writer 側 shape semantics を変更しないこと
- Preview 側だけ独自 shape を導入しないこと
- seconds 表示 API と frame-basis shape 計算を混同しないこと
- multi-point 不成立時の fallback を壊さないこと
- `main_window.py` の変更は必要最小限に留めること
- MS12 領域へ広げないこと
- 実装中に shape 契約の不足が見つかった場合は、無理にねじ込まず、最小契約拡張として整理すること

---

## 10. Codex への実装指示要約

- `preview_transform.py` を中心に、Preview 用 shape 契約を最小拡張する
- trapezoid は必須対応
- multi-point は無理なく載る範囲で対応
- shape 折れ点は writer と同じ 30fps frame basis を基準にする
- 描画 API / viewport / playback は秒ベースのまま維持する
- `preview_area.py` は polygon / path ベース描画へ更新する
- `main_window.py` は handoff 最小変更のみ
- closing softness は final closing edge のみ延長として表現する
- 後続 shape との clamp を再現する
- shared viewport / playback sync を壊さない
- テストを追加・更新して shape semantics alignment を検証する
