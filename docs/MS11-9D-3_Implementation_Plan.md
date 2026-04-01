# MS11-9D-3 Implementation Plan

## Zero-run span bridging for real-data speech gaps

## 0. 位置づけ

MS11-9D-3 は、MS11-9D の same-vowel micro-gap bridging と
MS11-9D-2 の cross-vowel transition bridging の後続として、
**実データ上で連続して現れる zero event 群**を bridge span として扱うための計画である。

本タスクは、`sample_input2` を実データ前提として、
「single zero event 前提では拾いきれない speech-internal gap」を扱う。

本タスクは、以下を主対象とする。

- 連続する `peak_value == 0.0` event 群を 1 つの `zero-run span` として扱うこと
- same-vowel / cross-vowel の両方で、span 単位の bridge 判定を導入すること
- Preview / export の semantics alignment を崩さない範囲で、real-data 寄りの bridge を導入すること

本タスクは、以下とは切り分ける。

- MS11-9D の single-event same-vowel bridge そのもの
- MS11-9D-2 の single-event cross-vowel transition そのもの
- MS11-9B / MS11-9C の final closing hold / softness
- 無音区間全般の再設計
- RMS 定数再調整そのもの
- MS12 の GUI responsiveness / splash / packaging

初回 MS11-9D-3 の固定方針:

- `single zero event` ではなく、**連続 zero event 群を bridge span として扱う**
- bridge span の初回対象は **短い zero-run** に限定する
- 判定基準は zero event 単体幅より、**前後 non-zero 間の実効 gap**を優先する
- `peak_value == 0.0` の reason は、初回は
  - `below_rel_threshold`
  - `no_peak_in_window`
  のみを候補側とする
- `timeline` は canonical writer input のまま維持する
- bridge span 候補の正本は引き続き `observations` 側に置く
- GUI への新規 parameter 追加は行わず、固定 policy として扱う
- zero-run span の最大 event 数は **2件まで**とする
- zero-run span の最大実効 gap 幅は **2 frame まで**とする
- observation には **`span_start_index / span_end_index`** を持たせる
- same-vowel span は、**zero event 数に応じて valley を複数置く**
- cross-vowel span は、**span 開始で次母音 rise 開始 / span 終了で前母音 zero 到達**を基本形とする
- `below_rel_threshold` と `no_peak_in_window` は、**同一 span family**で扱う

---

## 1. 背景

MS11-9D / MS11-9D-2 の初回実装は、
`1 frame` の `single zero event` を対象にした保守的な導入である。

この方針は安全だが、`sample_input2` のような実データでは、
改善効果が限定的になりやすい。

実データ確認から読み取れる傾向は次のとおりである。

- `peak_value == 0.0` の多くが `below_rel_threshold` である
- zero event が単発ではなく、**連続して現れることがある**
- zero event 自体の interval は広く見えても、前後発話の実効 gap は bridge したいことがある
- 現行の single-event candidate では、same-vowel / cross-vowel とも拾える数が少ない

したがって MS11-9D-3 では、
`peak_value == 0.0` event を 1 件ずつ見るのではなく、
**連続 zero event 群を 1 つの bridge span として評価する**方向へ進める。

---

## 2. 目的

MS11-9D-3 の目的は、
実データで現れる speech-internal zero-run に対して、
single-event 前提より自然な bridge 判定と shape 再構成を導入することである。

本タスクの目的は次のとおり。

- zero-run span を pipeline 側で認識できるようにする
- same-vowel / cross-vowel の両方を、span 単位で bridge 判定できるようにする
- `below_rel_threshold` 主体の実データに対して実用的な改善余地を持たせる
- Preview と export を同じ semantics で揃える
- final closing 系とは混ぜない

---

## 3. スコープ

### 3-1. 含める対象

- zero-run span 概念の導入
- span 単位の bridgeable candidate 判定
- same-vowel span bridge の shape semantics
- cross-vowel span transition の shape semantics
- Preview と writer の span boundary / transition boundary alignment
- 必要最小限の pipeline-side candidate 判定導線

### 3-2. 含めない対象

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
- `global_peak_zero` / `rms_unavailable` / `below_abs_threshold` を bridge 対象へ広げること
- 長い silence interval 全体を bridge すること
- Preview だけ先行して独自 bridge 表示を入れること
- same-vowel / cross-vowel / silence を 1 つの大ルールへ潰すこと

---

## 5. 基本方針

### 5-1. `single zero event` ではなく `zero-run span` を見る

MS11-9D-3 では、
bridge 対象を 1 件の zero event で見ない。

重要なのは次の点である。

- 連続 zero event 群を 1 つの bridge span として扱う
- span 判定では、前後 non-zero event と実効 gap を重視する
- event 単体幅が広く見えても、span として短ければ bridge 候補になりうる

### 5-2. 判定基準を `実効 gap` へ寄せる

MS11-9D / 9D-2 初回では、
zero event 自身の幅が判定に強く効いていた。

MS11-9D-3 では次の方向へ寄せる。

- `previous non-zero end -> next non-zero start` の gap を優先して見る
- zero-run の event 数と実効 gap の両方を安全条件に使う
- candidate は span 単位で決める

### 5-3. `below_rel_threshold` 主体の実データを正面から扱う

`sample_input2` では zero case の大半が `below_rel_threshold` である。

したがって初回 MS11-9D-3 では、
`below_rel_threshold` を主対象に据えて、
必要なら `no_peak_in_window` は同系統として併用する。

### 5-4. shape は span bridge として表現する

MS11-9D-3 でも、次の方針は維持する。

- zero event / zero-run の `peak_value` を直接書き換えない
- zero-run 自体を独立 peak 群として持ち上げない
- same-vowel は continuity / valley 系 bridge
- cross-vowel は minimal transition overlap
- Preview と export は同じ span semantics を使う

---

## 6. 既存構造との整合

### 6-1. current workspace の前提

現時点で確認できる前提は次のとおりである。

- pipeline は event を残したまま `peak_value` と reason を決める
- `VowelTimingPlan` / `PipelineResult` には optional な `observations` 契約がある
- MS11-9D / 9D-2 初回では `observations` が bridge 候補の正本になっている
- writer は `peak_value <= 0.0` event を shape 非生成として扱う
- Preview は writer helper を再利用して family / bridge semantics を再構成している
- `closing_hold_frames` / `closing_softness_frames` は final tail だけを扱う

### 6-2. 現行仕様と衝突しやすい点

MS11-9D-3 で衝突しやすいのは、次の点である。

1. zero-run span をそのまま silence 扱い変更へ広げること
2. `peak_value == 0.0` を不具合扱いして全救済へ広げること
3. final closing semantics と speech-internal span bridging を混ぜること

したがって本計画では、
zero-run span を speech-internal bridge の範囲だけで扱い、
silence redesign や final closing redesign とは分離する。

### 6-3. 契約方針

MS11-9D-3 でも、
**timeline は canonical writer input として維持し、bridge span 候補の正本は observations 側に置く**。

採用方針:

- `timeline point に持たせる` は採用しない
- `writer / preview に渡す別 metadata 契約を新設する` は初回では採用しない
- **`observations 側で span 候補を持たせる` を採用する**

理由:

- MS11-9D / 9D-2 初回ですでに `observations` を正本として使っている
- span 判定も `peak_value == 0.0` の reason と前後文脈に依存し、pipeline observation の意味領域に近い
- 初回 MS11-9D-3 は zero-run / real-data 改善に限定されるため、observations 最小拡張で十分と考えられる

---

## 7. 責務分割

## 7-1. pipeline

主責務:

- 連続 zero event を `zero-run span` として集約的に判定する
- same-vowel / cross-vowel の span candidate を observation 上で識別できるようにする
- 実効 gap、reason、前後 non-zero event、span 長を使って candidate を決める

想定方針:

- candidate 判定は event 単体ではなく span 単位
- zero-peak 自体を non-zero event に書き換えない
- canonical writer input である timeline を再設計しない

初回実装の具体方針:

- `PeakValueObservation` に、span candidate 判定済みであることを伝える最小情報を追加する
- 同一 span に属する zero event 群を、`span_start_index / span_end_index` で辿れるようにする
- same-vowel / cross-vowel は引き続き別系統として扱う

未確認事項:

- same-vowel / cross-vowel の span candidate bool 名
- `span_start_index / span_end_index` だけで十分か

## 7-2. writer

主責務:

- span candidate を独立 peak 群として立てず、前後 shape の橋渡しとして扱う
- same-vowel span は continuity / valley 系で扱う
- cross-vowel span は minimal transition overlap で扱う

想定方針:

- zero-run 全体を 1 つの遷移区間として扱う
- same-vowel は span をまたいでも同一 morph continuity を優先し、zero event 数に応じて valley を複数置く
- cross-vowel は span 開始で次母音の rise を始め、span 終了で前母音が zero に到達する

初回実装の具体方針:

- writer は `timeline + observations` を同時に見て、span 候補を event index 対応で解決する
- single-event bridge helper を span 対応へ拡張する
- observations が無い経路では、MS11-9D-3 bridge は無効として現行互換とする

未確認事項:

- same-vowel span multi-valley の具体 control point 配置
- cross-vowel span transition の具体 control point 値配分
- span 長に応じた fallback 条件

## 7-3. Preview

主責務:

- writer と同じ span boundary / transition boundary で shape を表示する
- span bridge semantics を writer と同様に再構成する
- Preview だけ独自の span 補間を発明しない

想定方針:

- 既存どおり writer helper 再利用を優先する
- shape semantics は frame basis、描画 API は seconds basis を維持する

初回実装の具体方針:

- Preview も `timeline + observations` を参照し、writer と同じ span 解決を行う
- observations が無い経路では、現行 Preview semantics を維持する

## 7-4. GUI

主責務:

- 原則として追加 GUI を前提化しない
- 既存 `current_timing_plan.timeline / observations -> build_preview_data(...) -> Preview` handoff を維持する

初回固定:

- GUI 追加なし
- fixed policy

---

## 8. bridgeable span 候補の考え方

### 8-1. 候補化の方向性

bridge 対象は、
**短い zero-run span だけ**を対象にする。

候補側とする方向:

- `below_rel_threshold`
- `no_peak_in_window`

原則として候補外寄り:

- `global_peak_zero`
- `below_abs_threshold`
- `rms_unavailable`

### 8-2. 最低条件

少なくとも次を満たす場合に限る。

- 対象 span が `peak_value == 0.0` event 群から成る
- span の前後に non-zero event がある
- span が発話先頭 / 発話末尾 / final closing ではない
- span の event 数と実効 gap が初回上限内である
- span の event 数は `2件まで`
- span の最大実効 gap 幅は `2 frame まで`

### 8-3. same-vowel / cross-vowel の分岐

- 前後母音が同一なら same-vowel span bridge 候補
- 前後母音が異なるなら cross-vowel span transition 候補

### 8-4. 除外方針

次は初回では除外寄りとする。

- span が長すぎるケース
- 実効 gap が広すぎるケース
- 前後どちらかの non-zero event が極端に短いケース
- 無音寄りと判断しやすいケース

---

## 9. `sample_input2` を前提にした改善意図

`sample_input2` では、zero case が単発よりも
**連続 zero event 群**として現れる箇所がある。

また、candidate 化される zero case の多くを阻んでいるのは、
event 単体幅基準の厳しさである。

したがって MS11-9D-3 では、次の改善を狙う。

- `single zero event` しか拾えない制約を外す
- `below_rel_threshold` 主体の実データでも bridge span を拾えるようにする
- same-vowel / cross-vowel の両方で、event 単体ではなく span 全体で判断する

---

## 10. Preview / export 整合方針

MS11-9D-3 でも、Preview と export は同じ semantics を維持する。

固定方針:

- Preview だけ独自 span bridge を表示しない
- writer と Preview は同じ span candidate 情報を参照する
- span 解決は event index 対応で揃える
- observations 無し経路では、両方とも bridge 無効で現行互換にする

---

## 11. 最低限のテスト観点

### 11-1. pipeline

- 連続 zero event 群が same-vowel span candidate として認識される
- 連続 zero event 群が cross-vowel span candidate として認識される
- `below_rel_threshold` 主体の zero-run が candidate 化される
- `below_abs_threshold` / `global_peak_zero` / `rms_unavailable` は candidate 化されない
- 先頭 / 末尾 / final closing 相当 span は candidate 化されない

### 11-2. writer

- same-vowel span bridge で不必要な完全閉口が減る
- cross-vowel span transition で前母音の完全閉口前に次母音の rise が始まる
- zero-run 自体を独立 peak 群として生成しない
- observations 無し経路では現行互換

### 11-3. Preview

- Preview が writer と同じ span boundary / transition boundary を表示する
- Preview / export の event index 対応が一致する
- observations 無し経路では現行 Preview と同じになる

### 11-4. real-data

- `sample_input2` で same-vowel / cross-vowel ともに改善対象が増える
- 既存 MS11-9D / 9D-2 の single-event 改善と干渉しない
- MMD 上の見え方と Preview の整合が保たれる

---

## 12. スコープ外

今回の MS11-9D-3 では次をスコープ外とする。

- 長い silence interval 全体の再設計
- GUI パラメータ化
- RMS 定数再調整
- `below_abs_threshold` / `global_peak_zero` / `rms_unavailable` の救済拡張
- MS12

---

## 13. 未確認事項

現時点で未固定の項目は次のとおり。

- same-vowel / cross-vowel の span candidate bool 名
- same-vowel span multi-valley の具体 control point 配置
- cross-vowel span transition の具体 control point 値配分
- span 長に応じた fallback 条件

---

## 14. 到達イメージ

MS11-9D-3 完了時の到達イメージは次のとおり。

- `sample_input2` のような実データで、bridge 対象が single-event 前提より増える
- same-vowel / cross-vowel の両方で、zero-run span を自然に bridge できる
- Preview / export が同じ span semantics を使う
- timeline を汚さず、observations を正本としたまま拡張できる

---

## 15. 要約

MS11-9D-3 は、
**single zero event 前提では拾いきれない実データ上の speech-internal gap を、zero-run span bridging として扱う**
ための計画である。

初回固定方針は次のとおり。

- zero-run span を bridge 単位とする
- 判定は event 幅より実効 gap を優先する
- `below_rel_threshold` / `no_peak_in_window` を候補対象にする
- 最大 event 数は `2件`
- 最大実効 gap は `2 frame`
- timeline はそのまま維持
- bridge 候補の正本は observations 側
- observation には `span_start_index / span_end_index` を持たせる
- same-vowel span は multi-valley
- cross-vowel span は span 開始で次母音 rise / span 終了で前母音 zero
- reason family は同一 span family とする
- GUI 追加なし
- Preview / export 整合を維持
