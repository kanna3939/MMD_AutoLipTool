# MS11-9E-4 Implementation Plan

## Single-event same-vowel zero/low-energy span の writer-side synthetic bridge policy

## 0. 位置づけ

MS11-9E-4 は、MS11-9E-3 実装後の追跡で明らかになった
**「pipeline で same-vowel candidate は立つが、writer の single-event span 分岐で shape 差分が消える」**
というボトルネックに対する最小実装計画である。

MS11-9E は writer 側の residual same-vowel burst smoothing refinement、
MS11-9E-2 は same-vowel candidate 条件の最小拡張、
MS11-9E-3 は representative span による pipeline 整合化を扱った。

しかし現時点では、

- `pipeline` で same-vowel candidate が新たに立つ
- `writer` へ candidate は渡っている
- それでも最終 VMD は旧出力と一致する

という状態が確認されている。

このため MS11-9E-4 では、
**single-event same-vowel zero/low-energy span に対して、
writer が synthetic bridge point を置けるようにする**
ことを主目的とする。

---

## 1. 背景

現行 writer では、same-vowel candidate は
`_collect_same_vowel_burst_spans(...)` により span として収集される。

その後、`_build_same_vowel_span_synthetic_points(...)` が
same-vowel span を grouped input へ変換する。

ただし現行実装には次の分岐がある。

- `positive span point を含む multi-event span`:
  synthetic sub-peak を構築する
- `all-zero multi-event span`:
  synthetic bridge point を構築する
- `single-event span`:
  `[]` を返し、synthetic point を作らない

この結果、
single-event same-vowel zero/low-energy span は candidate 化されても、
writer shape 上は新しい橋渡し点が追加されない。

---

## 2. 確認できた事実

追跡確認で、少なくとも次は確認済みである。

- MS11-9E-3 後、実データ `sample_input2` では same-vowel candidate が `0 -> 5` に増えた
- 対象 index は `19, 42, 102, 152, 179`
- これらは writer 側まで渡っている
- しかし、その 5 件だけ candidate を無効化しても
  `_build_interval_morph_frames(...)` の結果は完全一致だった
- grouped input を見ると、current path と patched path で grouping の見え方は変わっている
- それでも最終フレームが同じなのは、
  single-event zero/low-energy same-vowel span で synthetic point を作らないためと整合する

したがって現在のボトルネックは、
candidate 判定ではなく
**writer の single-event span policy**
にあると整理できる。

---

## 3. 問題整理

### 3-1. 現状の不一致

現在の same-vowel 系では、

- pipeline:
  same-vowel continuity に見える event を candidate 化できるようになってきた
- writer:
  same-vowel span を grouped input へ変換する

一方で writer は、
single-event same-vowel zero/low-energy span を
「grouping から外すだけ」で、
新しい continuity bridge を明示的には作っていない。

このため、

- candidate は立つ
- span 収集もされる
- しかし grouped shape は旧出力と実質同じになる

というズレが残っている。

### 3-2. 実害

ユーザー意図としては、
single-event same-vowel zero/low-energy span も
「閉口ではなく continuity」として見せたい。

しかし現状では、
single-event span が最終 shape に寄与しないため、

- 実データ VMD に差分が出ない
- MS11-9E-3 の改善が見た目へ届かない

という状態になっている。

---

## 4. 目的

MS11-9E-4 の目的は次のとおり。

- single-event same-vowel zero/low-energy span を writer shape に反映させる
- same-vowel continuity を見た目上も連続的にする
- multi-event span の既存挙動はできるだけ維持する
- Preview / export の semantics 一致を維持する

---

## 5. スコープ

### 5-1. 含める対象

- writer の same-vowel single-event span synthetic bridge 追加
- Preview 側の同一 helper 反映確認
- writer / Preview test の追加
- pipeline handoff の回帰確認

### 5-2. 含めない対象

- same-vowel candidate classification の再設計
- cross-vowel continuity-floor 再設計
- peak threshold の再調整
- GUI parameter 追加
- observation-layer 再編

---

## 6. 非目標

- single-event span をすべて flatten すること
- same-vowel zero event を全面救済すること
- cross-vowel family に同じ policy を広げること
- writer multi-point shape family を作り直すこと

---

## 7. 取りうる方針

### 案A. single zero event に midpoint synthetic bridge を追加する

- same-vowel single-event zero span の場合、
  previous / next non-zero point の中間近辺に bridge point を置く
- bridge peak は continuity peak を基準にする

利点:

- 現行 multi-event zero span policy と整合しやすい
- 差分が小さい

懸念:

- bridge 値が高すぎると過剰に開いて見える

### 案B. single low-positive event を sub-peak として残し、その前後に浅い valley を作る

- single-event でも low-positive 値を活かしつつ continuity に寄せる

利点:

- low-positive case には自然

懸念:

- zero case と low-positive case で rule が分かれる
- 初回としては少し複雑

### 案C. single-event same-vowel candidate を grouped merge のみで処理する

- synthetic point は置かず、grouping 条件だけで continuity に見せる

利点:

- 実装差分が小さい

懸念:

- すでに実データ追跡で、これだけでは最終フレーム差分にならないことが確認済み

---

## 8. 初回推奨方針

MS11-9E-4 初回は、
**案A を主軸に、single low-positive case は案B を必要最小限だけ併用する**
のが推奨である。

推奨内容:

- single-event zero span:
  midpoint synthetic bridge を追加
- single-event low-positive span:
  原値を上限に continuity 寄り synthetic bridge を追加
- bridge peak は
  `continuity_peak_value` と既存 floor の間に収める

理由:

- 現在不足しているのは「single-event span が shape に何も足さないこと」
- その解消には synthetic point 追加が最短
- existing helper の延長で実装できる

---

## 9. 具体的な見直し案

### 9-1. `_build_same_vowel_span_synthetic_points(...)` の single-event 分岐追加

現行:

- `span_event_count <= 1` で `[]` を返す

見直し案:

- `span_event_count == 1` かつ same-vowel candidate のとき、
  synthetic bridge point を 1 点生成する

### 9-2. zero event と low-positive event の値配分

初回案:

- zero event:
  `continuity_peak_value * ratio` を基準にする
- low-positive event:
  `min(original_peak_value, continuity_peak_value * ratio)` を基準にする

どちらも:

- 下限は `SAME_VOWEL_BURST_FLOOR_MORPH_VALUE`
- 上限は `continuity_peak_value`

### 9-3. bridge 時刻の決め方

初回案:

- 基本は current event `time_sec`
- 前後 event の midpoint と大きく矛盾しないようにする

理由:

- E3 で representative span を `time_sec` 中心に寄せており、整合しやすい

---

## 10. 責務分割

### 10-1. writer

主責務:

- single-event same-vowel zero/low-energy span を shape 差分に変換する

初回方針:

- 変更の中心は writer helper
- 既存 multi-event logic は極力維持する

### 10-2. Preview

主責務:

- writer helper 再利用により同じ shape を表示する

初回方針:

- Preview 固有ロジックは増やさない
- 既存 helper 再利用を維持する

### 10-3. pipeline

主責務:

- 既存 candidate handoff を維持する

初回方針:

- E3 までの結果をそのまま使う
- 追加の candidate 拡張はしない

---

## 11. 実装フェーズ

## Phase 1. single-event same-vowel span の最小再現固定

作業:

- writer / Preview test に
  - single zero same-vowel span
  - single low-positive same-vowel span
  の再現ケースを追加する

完了条件:

- 現状では差分にならない case がテストで明示される

## Phase 2. writer helper の single-event 分岐追加

作業:

- `_build_same_vowel_span_synthetic_points(...)` に single-event policy を追加する
- zero / low-positive の両 case で既存 floor / continuity を使って値配分する

完了条件:

- single-event same-vowel span が最終フレーム差分になる

## Phase 3. Preview alignment

作業:

- Preview 側の shape が export と一致することを確認する

完了条件:

- Preview / export の semantics 一致が維持される

## Phase 4. 実データ確認

作業:

- `sample_input2` などで VMD 再生成差分を確認する
- candidate が立っていた `19, 42, 102, 152, 179` 付近に差分が出るか確認する

完了条件:

- MS11-9E-4 の差分が初めて実データ VMD に現れる

---

## 12. 最低限のテスト観点

### 12-1. writer

- single zero same-vowel span で synthetic bridge が追加される
- single low-positive same-vowel span で synthetic bridge が追加される
- multi-event span の既存期待値を壊さない

### 12-2. Preview

- writer と同じ single-event shape が表示される

### 12-3. pipeline / handoff

- E3 までで立つ candidate がそのまま使われる
- candidate が立たない case は旧挙動のまま

---

## 13. ユーザー判断が必要な点

現時点で、実装前に固定しておくと安全な点は次の 3 つである。

### Q1. 初回は single-event zero span と single-event low-positive span を同時に扱うか

- 推奨案: **はい**
- 理由:
  - 実装点が同じ helper に集約される
  - 片方だけだと実データ差分が限定される可能性がある

### Q2. synthetic bridge は 1 点追加に留めるか

- 推奨案: **はい**
- 理由:
  - 差分が小さい
  - Preview / export 同期を保ちやすい

### Q3. 初回は新しい GUI parameter を追加せず、既存 floor / ratio の範囲で解くか

- 推奨案: **はい**
- 理由:
  - MS11-9 family の最小差分方針に合う
  - 調整点を増やさず因果を追いやすい

---

## 14. スコープ外

- same-vowel candidate family の再分類
- cross-vowel family の再設計
- observation dataclass の再編
- MS12

---

## 15. 到達イメージ

MS11-9E-4 完了時の到達イメージは次のとおり。

- pipeline で立った single-event same-vowel candidate が、
  初めて writer shape 差分になる
- `sample_input2` / 実データ VMD で差分が出始める
- same-vowel continuity の見え方が一段自然になる
- Preview / export は同じ semantics を維持する

---

## 16. 要約

MS11-9E-4 は、
**single-event same-vowel zero/low-energy span が
writer で shape 差分に変換されない欠落を埋める**
ための計画である。

初回推奨は次のとおり。

- `_build_same_vowel_span_synthetic_points(...)` に single-event 分岐を追加する
- zero / low-positive の両 case を同じ helper で扱う
- synthetic bridge は 1 点追加に留める
- pipeline ではなく writer を主対象にする
