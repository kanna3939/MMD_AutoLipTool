# MS11-9D-4 Implementation Plan

## Bridge-aware top-end shaping

## 0. 位置づけ

MS11-9D-4 は、MS11-9D / MS11-9D-2 / MS11-9D-3 で導入した
speech-internal bridge / transition semantics の後続として、
**flat top の 3 点目を時点音量ベースで減衰させる**ための計画である。

本タスクは、bridge 導入後に残る見た目の不自然さ、
特に「2点目と3点目が同値のまま維持される」ことによる
口形状の静止感を改善対象とする。

本タスクは、以下を主対象とする。

- trapezoid 系 shape の `peak_end` 側値の見直し
- bridge / transition が関与した shape に対する top-end shaping
- cross-vowel に見えるが前後 morph とも `peak_value == 0.0` となる区間での、完全閉口回避方針
- Preview / export の semantics alignment を崩さない範囲での top-end 減衰導入

本タスクは、以下とは切り分ける。

- MS11-9D の same-vowel bridge 判定そのもの
- MS11-9D-2 の cross-vowel transition 判定そのもの
- MS11-9D-3 の zero-run span 判定そのもの
- MS11-9B / MS11-9C の final closing hold / softness
- 無音区間全般の再設計
- RMS 定数再調整そのもの
- MS12 の GUI responsiveness / splash / packaging

初回 MS11-9D-4 の固定方針:

- `2点目` と `3点目` を常に同値にしない
- `3点目` の morph 値は、**3点目フレーム時点の local RMS 比に応じた値**で決める
- ただし `3点目値` は `2点目値` を超えない
- 初回は **bridge / transition が関与した shape を優先対象**としつつ、通常 trapezoid にも順次適用可能な形で設計する
- cross-vowel に見えるが前後 morph とも zero-peak の場合は、**speech-internal continuity floor** を導入対象に含める
- `continuity floor` の初回固定値は `0.1` morph 値とする
- `timeline` は canonical writer input のまま維持する
- 正本は引き続き `observations` と現在の shape 再構成結果に置く
- GUI への新規 parameter 追加は行わず、固定 policy として扱う

---

## 1. 背景

現行 writer / Preview では、
trapezoid 系 shape の `peak_start_frame` と `peak_end_frame` は
基本的に **同じ morph 値**で書き出される。

その結果、次の見え方が起きやすい。

- 開口は維持される
- しかし 3 点目で音量変化が見えない
- そのため、口形状だけが同じ開きで静止しているように見える

特に bridge / transition 後は、
音量上は既に次の変化に向かっているのに、
shape 上は `flat top` が残ることで違和感が強く見えやすい。

実際に生成済み VMD でも、
各母音で non-zero plateau が多数確認できる。

さらに、VMD 上では
「cross-vowel に見える並びなのに、前後 morph とも zero-peak 扱いとなり、
発話中にもかかわらず完全閉口している」箇所が散見される。

この case では、flat top の問題だけでなく、
**bridge 候補に乗らなかった結果として speech-internal continuity 自体が消えている**
可能性がある。

したがって MS11-9D-4 では、
`peak_end` 側を固定値で維持するのではなく、
**3点目時点の音量を反映した decayed value** を導入しつつ、
必要に応じて zero-peak cross-vowel case に対する continuity floor も併用対象として整理する。

---

## 2. 目的

MS11-9D-4 の目的は、
bridge / transition 後に残る flat top の不自然さを減らし、
音量変化に追従した top-end shaping を導入することである。

本タスクの目的は次のとおり。

- 3 点目を 2 点目の単純コピーにしない
- 3 点目フレーム時点の local RMS 比に応じた morph 値を導入する
- ただし peak を増幅させず、安全側に clamp する
- bridge 候補に乗らなかった zero-peak cross-vowel case や zero-run cross-vowel span でも、speech-internal 完全閉口を減らす余地を持たせる
- Preview と export を同じ semantics で揃える
- final closing 系とは混ぜない

---

## 3. スコープ

### 3-1. 含める対象

- bridge-aware top-end shaping の導入
- `peak_end` 側 decayed value の定義
- bridge / transition が関与した shape での優先適用
- 通常 trapezoid 系 shape への段階的適用方針
- zero-peak cross-vowel case と zero-run cross-vowel span に対する continuity floor の導入
- Preview と writer の top-end semantics alignment
- 必要最小限の writer-side shape contract 拡張

### 3-2. 含めない対象

- bridge candidate 判定条件の再設計
- final closing hold / softness の意味変更
- 無音区間全般の扱い変更
- `peak_value == 0.0` 全体の一律救済
- RMS reason 分類そのものの再定義
- GUI responsiveness / startup / splash / packaging
- GUI パラメータ追加

---

## 4. 非目標

今回やらないことを明確にする。

- `closing_hold_frames` / `closing_softness_frames` の再定義
- final closing family の再設計
- pipeline 上で zero-peak event を一律削除すること
- bridge 判定そのものを別方式へ変えること
- plateau を完全になくすことだけを目標化すること
- Preview だけ先行して独自 smoothing を入れること

---

## 5. 基本方針

### 5-1. 3 点目は「時点音量ベース」で決める

MS11-9D-4 では、
flat top の 3 点目を 2 点目のコピーにしない。

重要なのは次の点である。

- 3点目フレーム時点の local RMS 比を使う
- 2点目より上げない
- 0 に急落させず、top-end の減衰として扱う

### 5-2. zero-peak cross-vowel case には continuity floor を検討する

VMD 上で確認される
「cross-vowel に見えるが、前後 morph とも zero-peak になって完全閉口している case」は、
top-end shaping だけでは改善しきれない可能性がある。

そのため MS11-9D-4 では、補助方針として次を検討対象に含める。

- 発話内部であることが明確な区間では、完全 0 へ落とし切る前に最小開口を残す
- その最小開口は `continuity floor` として扱い、peak の代替とはみなさない
- 初回固定値は `0.1` morph 値とする
- continuity floor は bridge / transition semantics の補助であり、zero-peak 全救済ではない

continuity floor の初回適用対象:

- zero-peak cross-vowel case
- zero-run cross-vowel span
### 5-3. 初回は bridge-aware shape を優先する

初回 MS11-9D-4 では、
全 trapezoid 系を一気に変更するより、
**bridge / transition が関与した shape** を優先対象とする。

理由:

- 影響範囲を絞れる
- 見た目改善が大きい箇所に集中できる
- 既存 shape 全体への副作用を抑えやすい

zero-peak cross-vowel case への continuity floor も、
まずは bridge / transition に近い箇所へ限定しつつ、
通常 trapezoid 系 shape へも順次拡張できる形で扱うのが安全である。

### 5-4. 3 点目値は安全側に clamp する

初回では次を固定する。

- `point3_value <= point2_value`
- `point3_value > 0` を原則維持する
- same-vowel valley や cross-vowel transition を壊さない
- continuity floor を入れる場合も、peak 値を超えず、speech-internal 補助値として扱う

### 5-5. Preview / export は同じ top-end semantics を使う

MS11-9D-4 でも、次の方針は維持する。

- Preview だけ独自 decayed top を表示しない
- writer と Preview は同じ 3 点目値計算を使う
- continuity floor を導入する場合も Preview / export で共通に扱う
- observations 無し経路では、必要なら現行互換に寄せる

---

## 6. 既存構造との整合

### 6-1. current workspace の前提

現時点で確認できる前提は次のとおりである。

- `AsymmetricTrapezoidSpec` は `peak_start_frame` / `peak_end_frame` を持つ
- 現行 trapezoid 展開では `peak_start` と `peak_end` の値は同一 `peak_value` で出力される
- Preview も同じ spec を再構成している
- MS11-9D / 9D-2 / 9D-3 で bridge / transition 導線は既にある

### 6-2. 現行仕様と衝突しやすい点

MS11-9D-4 で衝突しやすいのは、次の点である。

1. 3点目値変更が peak そのものの意味変更に広がること
2. final closing slope と top-end shaping を混ぜること
3. Preview と export が別の減衰値を使うこと
4. zero-peak cross-vowel case の continuity floor が zero-peak 全救済へ広がること

したがって本計画では、
`top-end shaping` を peak 定義や final closing から分離し、
Preview / export の共通 semantics として扱う。

### 6-3. 契約方針

MS11-9D-4 では、
**writer-side shape spec に 3 点目値を持てる余地を追加する**方向を採る。

初回固定:

- `AsymmetricTrapezoidSpec` に `peak_end_value` を追加する
- `peak_end_value` 未指定時は現行互換で `peak_value` を使う

理由:

- 3点目値の導入箇所が明確になる
- Preview 側でも同じ spec を再利用しやすい
- bridge-aware shaping を局所的に適用しやすい

---

## 7. 責務分割

## 7-1. pipeline

主責務:

- bridge 判定の正本を維持する
- 必要なら 3点目時点音量参照に必要な observation 情報を補助的に持たせる

想定方針:

- 3点目値の主計算は writer 側
- pipeline は候補判定の責務を超えて shape 本体を持たない

未確認事項:

- zero-peak cross-vowel case を observation からどう識別するか
- zero-run cross-vowel span を continuity floor 適用対象としてどう識別するか

## 7-2. writer

主責務:

- 3点目時点の decayed value を計算する
- bridge / transition が関与した shape に対して優先適用する
- same-vowel / cross-vowel それぞれの top-end を自然に減衰させる

想定方針:

- trapezoid spec に `peak_end_value` を導入する
- `peak_end_value` は `peak_value` 以下に clamp する
- bridge-aware shape では decayed value を優先適用する
- 通常 trapezoid にも段階的に `peak_end_value` を適用できるようにする
- 非対象 shape は現行互換を維持できるようにする
- zero-peak cross-vowel case では、必要なら `continuity floor` を top-end 補助値または transition 補助値として使う

## 7-3. Preview

主責務:

- writer と同じ `peak_end_value` semantics を表示する
- flat top が減衰 top に変わることを export と同じ形で示す

想定方針:

- spec 再利用を優先する
- 3点目値も writer spec から読む

## 7-4. GUI

主責務:

- 原則として追加 GUI を前提化しない
- 既存 `current_timing_plan -> build_preview_data(...)` handoff を維持する

初回固定:

- GUI 追加なし
- fixed policy

---

## 8. 3点目値の考え方

### 8-1. 基本式の方向性

3点目値は、
**3点目時点の音量に応じた morph 値**として扱う。

候補例:

- 3点目フレーム時点の local RMS 比

### 8-2. 安全条件

少なくとも次を満たすようにする。

- `point3_value <= point2_value`
- `point3_value >= valley_value` が必要な shape ではそれを下回らない
- `point3_value > 0` を基本とする

### 8-3. same-vowel / cross-vowel の違い

- same-vowel:
  - continuity を壊さない範囲で、3点目を減衰させる
  - valley へ入る直前の値として扱う
- cross-vowel:
  - 次母音遷移前の減衰値として扱う
  - 前母音が張り付いて見えないようにする

### 8-4. zero-peak cross-vowel case への補助方針

前後 morph とも zero-peak 扱いで、
しかも発話内部と見なせる cross-vowel case では、
3点目減衰だけでは完全閉口を避けられない可能性がある。

このため、補助方針として次を検討する。

- `continuity floor` を導入し、完全 0 ではなく最小開口を残す
- continuity floor は peak の代替ではなく、speech-internal continuity の補助値として扱う
- same-vowel / cross-vowel の通常 bridge を優先し、それでも拾えない case に限定して適用する
- 初回固定値は `0.1` morph 値とする

---

## 9. 添付 VMD から見た改善意図

生成済み VMD では、
各母音で non-zero plateau が多数確認できる。

代表的な傾向:

- `point2` と `point3` が同値のまま数 frame 続く
- その直後に slope または zero へ落ちる
- 音量変化よりも shape の平坦さが目立つ箇所がある

したがって MS11-9D-4 では、次の改善を狙う。

- top-end の静止感を減らす
- bridge 後 shape の不自然な張り付きを減らす
- 3点目時点の音量に追従した見え方を作る
- bridge 候補に乗らなかった zero-peak cross-vowel case でも、speech-internal 完全閉口を減らす

---

## 10. Preview / export 整合方針

MS11-9D-4 でも、Preview と export は同じ semantics を維持する。

固定方針:

- Preview だけ独自 smoothing を表示しない
- writer と Preview は同じ `peak_end_value` を使う
- observations 無し経路では、必要なら現行互換にする

---

## 11. 最低限のテスト観点

### 11-1. writer

- bridge-aware trapezoid で 3点目値が 2点目値より下がる
- 3点目値が 2点目値を超えない
- same-vowel bridge の valley / continuity を壊さない
- cross-vowel transition の overlap を壊さない
- zero-peak cross-vowel case に continuity floor を入れる場合、peak の代替にならない

### 11-2. Preview

- Preview が writer と同じ 3点目値を表示する
- flat top が decayed top として再構成される

### 11-3. real-data

- 添付 VMD と同種の plateau が減る
- `sample_input2` 由来の bridge shape で見た目改善が確認できる
- MMD 上の見え方と Preview の整合が保たれる
- VMD 上で完全閉口していた zero-peak cross-vowel case が減る

---

## 12. スコープ外

今回の MS11-9D-4 では次をスコープ外とする。

- bridge candidate 判定条件の再設計
- GUI パラメータ化
- RMS 定数再調整
- 無音判定ロジック全体の再設計
- MS12

---

## 13. 未確認事項

現時点で未固定の項目は次のとおり。

- 3点目値の最小下限を valley / overlap とどう整合させるか
- zero-peak cross-vowel case の continuity floor を何条件で有効化するか
- zero-run cross-vowel span に continuity floor を置く具体 point 配置
- `peak_end_value` と `continuity floor` が同時に効く場合の優先順位
- 通常 trapezoid への展開順序

---

## 14. 到達イメージ

MS11-9D-4 完了時の到達イメージは次のとおり。

- 2点目と3点目の同値 plateau が減る
- 3点目が時点音量に追従した減衰値になる
- bridge / transition 後の shape が自然に見える
- zero-peak cross-vowel case の speech-internal 完全閉口が減る
- Preview / export が同じ top-end semantics を使う

---

## 15. 要約

MS11-9D-4 は、
**bridge 後に残る flat top の 3 点目を、時点音量ベースの decayed value へ置き換える**
ための計画である。

初回固定方針は次のとおり。

- 3点目を 2点目の単純コピーにしない
- 3点目値は 3点目フレーム時点の local RMS 比で決める
- ただし 2点目値を超えない
- bridge-aware shape を優先対象にしつつ、通常 trapezoid にも順次適用する
- zero-peak cross-vowel case と zero-run cross-vowel span には `0.1` の continuity floor を補助導入対象に含める
- `AsymmetricTrapezoidSpec` に `peak_end_value` を追加し、未指定時は現行互換にする
- GUI 追加なし
- Preview / export 整合を維持する
