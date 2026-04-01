# MS11-9C Implementation Plan

## Lip Hold GUI exposure and final-closing hold semantics alignment

## 0-1. 実装反映注記（2026-04-01）

- current workspace では、MS11-9C は実装済みとして扱う。
- 反映済みの要点:
  - GUI に `開口保持` / `Lip Hold` を追加し、`モーフ最大値` → `開口保持` → `閉口スムース` の順で配置
  - `closing_hold_frames` を settings / Preview / export handoff に接続
  - writer 側で final closing を `hold -> 70% midpoint -> zero` として再構成
  - Preview 側でも同じ family 境界で hold / midpoint / zero を表示
  - `peak == 0.0` 相当のイベントは shape 非生成であり、clamp blocker にも使わない
  - clamp 上限は次の有効 non-zero shape 開始直前までに統一
- したがって、本書は「計画書」であると同時に、2026-04-01 時点の到達仕様メモとしても扱う。

## 0. 目的

MS11-9C の目的は、無音区間が長い場合に口がすぐ閉じるのを緩和するための
新規 parameter `closing_hold_frames` を導入し、
writer-side output semantics と Preview 表示を同じ意味で揃えることである。

本タスクでは、既存 `closing_softness_frames` の意味は維持する。

- `closing_hold_frames`
  - 無音区間に入っても、closing slope の開始値を一定フレーム保持する
- `closing_softness_frames`
  - hold 後の closing slope の長さを決める

---

## 1. 基本方針

### 1-1. parameter 分離
- `closing_softness_frames` は再定義しない
- 新たに `closing_hold_frames` を追加する
- 両者は独立 parameter とする

### 1-2. 適用順
1. final closing 対象 shape を決定
2. `closing_hold_frames` によって closing slope start の値を保持
3. hold 終了後に、最後の non-zero 値の 70% を持つ中間点を追加する
4. `closing_softness_frames` によって、その中間点から zero 到達までの slope 長を決める
5. 後続 shape 開始前で clamp

### 1-3. 安全条件
- 開始側は固定
- hold 区間は closing slope start の値を維持する
- 中間点の値は常に最後の non-zero 値の 70% とする
- zero 到達は `closing_softness_frames` の範囲で行う
- zero-only shape を新規生成しない
- 後続 shape 開始前で clamp する
- final closing shape の再設計に限定し、無関係な rise 側には広げない

### 1-4. clamp 判定の固定方針
- `peak == 0.0` 相当で shape を生成しないイベントは、clamp 対象から完全に外す
- 除外対象は、まず `peak == 0.0` 相当だけに限定する
- hold / 70% midpoint / zero の伸長上限は、次の有効 non-zero shape 開始直前までとする
- 「shape を出さない zero-peak イベントが、前 shape だけを早く閉じさせる」不整合は許容しない
- writer と Preview は、同じ clamp 境界規則を共有する

---

## 2. 対象 shape family

### 2-1. 含める対象
- MS11-2 asymmetric trapezoid
- legacy symmetric trapezoid
- legacy triangle
- peak fallback
- MS11-3 multi-point envelope

### 2-2. 適用条件
- final closing が実在するもの
- closing slope start の後に end-zero があるもの
- hold と中間点を入れても zero-only shape にならないもの
- 次の clamp 対象は、実際に non-zero shape を生成する後続イベント / 後続 group に限る

### 2-3. family ごとのイメージ
- MS11-2 / legacy symmetric trapezoid
  - `peak_end_frame` を hold し、その後 70% 中間点を経由して end-zero へ落とす
- legacy triangle / peak fallback
  - peak frame を closing slope start とみなし、その後 70% 中間点を経由して zero へ落とす
- MS11-3 multi-point
  - 最後の non-zero control point を hold し、その後 70% 中間点 control point を追加してから end-zero を置く

### 2-4. 現時点の固定解釈
- `closing_hold_frames` は hold 区間だけの長さとする
- 70% 中間点は、常に最後の non-zero 値の 70% とする
- この 70% は morph upper limit 適用後の最終値を基準とする
- hold 区間の後に closing slope を開始する
- `closing_softness_frames=0` の場合は、hold 後ただちに zero 到達する現行互換を基本とする
- `peak == 0.0` 相当のイベントは shape 非生成であり、clamp blocker にも使わない

---

## 3. GUI 方針

### 3-1. 新規項目
- 日本語: `開口保持`
- 英語: `Lip Hold`

### 3-2. 単位
- 常時表示
- 日本語: `フレーム`
- 英語: `Frame`

### 3-3. 値仕様
- `int`
- `0` 以上
- default `0`

### 3-4. 保存と handoff
- GUI / settings / Preview / export handoff のすべてで frame count として統一する
- Preview と export は同じ単一の現在値参照経路を使う

### 3-5. GUI 配置
- 同一 row 内で `モーフ最大値` の右隣に配置する
- 並び順は `モーフ最大値` → `開口保持` → `閉口スムース` とする
- `開口保持` も `[input] フレーム` / `[input] Frame` の形で単位を常時表示する

---

## 4. 主変更対象

### 4-1. writer
- `src/vmd_writer/writer.py`

想定主対象:
- hold frame 正規化 helper
- trapezoid / legacy / peak fallback / multi-point への hold 適用 helper
- 70% 中間点を伴う final closing 再構成 helper
- `hold -> 70% midpoint -> zero` を family ごとに展開する helper
- 次の有効 non-zero shape 開始だけを clamp 対象に選ぶ helper / 判定整理

### 4-2. Preview
- `src/gui/preview_transform.py`

想定主対象:
- writer と同じ family 境界で hold / 70% midpoint / zero を再構成する部分
- writer と同じ「有効 non-zero shape だけを blocker にする」clamp 境界へ揃える部分

### 4-3. GUI / settings / handoff
- `src/gui/main_window.py`
- `src/gui/central_panels.py`
- `src/gui/settings_store.py`
- `src/gui/i18n_strings.py`
- 必要なら `src/core/pipeline.py`

---

## 5. 即時反映方針

- 現時点では、`current_timing_plan.timeline` と `build_preview_data(...)` の再構成だけで済んでいる
- WAV 再解析や Whisper 再実行は不要
- したがって、MS11-9C でも原則として即時反映を維持する
- deferred 反映は、実装後に体感遅延が確認された場合のみ再検討する
- ただし今回は final closing shape の再定義を伴うため、実装後は体感遅延の有無を重点確認する

---

## 6. テスト観点

### 6-1. writer
- `closing_hold_frames=0` で現行互換
- hold のみで closing slope start の値が一定時間維持される
- hold 後に 70% 中間点が生成される
- softness のみで 70% 中間点から zero までの slope 長だけが変わる
- hold + softness の併用で `hold -> 70% -> zero` が形成される
- clamp
- zero-only shape 非生成
- `non-zero -> zero-peak -> long silence` で、zero-peak イベントが前 shape の clamp blocker にならない
- 次の有効 non-zero shape が来る直前では正しく clamp される

### 6-2. Preview
- hold と 70% 中間点を含む final closing を writer と同じ family 境界で表現できる
- Preview と export の見え方が矛盾しない
- zero-peak 非表示イベントによって Preview だけ早く閉じる不整合を起こさない

### 6-3. GUI / settings
- current value 単一路線を維持
- settings round-trip
- 日本語 / 英語の単位表示

---

## 7. 非目標

- `closing_softness_frames` の意味変更
- Preview 全体の大規模描画再設計
- deferred 反映への切り替え
- MS12 領域への拡張
- 大規模リファクタリング
- 無音判定ロジックそのものの全面再設計
