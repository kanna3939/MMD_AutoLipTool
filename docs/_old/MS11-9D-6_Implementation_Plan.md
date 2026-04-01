# MS11-9D-6 Implementation Plan

## Same-vowel burst smoothing

## 0. 位置づけ

MS11-9D-6 は、MS11-9D / MS11-9D-3 の same-vowel micro-gap / zero-run bridge を、
実データ上の **same-vowel short re-segmentation** に対して拡張するための後続計画である。

本タスクは、生成 VMD 上で確認された次のような現象を対象とする。

- 同一母音が短区間で `positive -> zero -> positive` と分断される
- 同一母音の短い trapezoid が連続し、見た目として急な開閉が連打される
- 発話継続中であるにもかかわらず、同一母音内で独立閉口に見える

典型例:

- 24f で「お」が 0 に落ち、その前後で同じ母音の開口が続く
- 28f-35f で「う」が短い台形列として分断され、3 点以上の急な開閉に見える

MS11-9D-6 は、これらを
**same-vowel burst**
として扱い、独立閉口ではなく同一母音連続内の valley / continuity として再解釈することを主題とする。

初回 MS11-9D-6 の固定方針:

- burst の最大幅は `2 event / 2 frame` まで
- 対象は `zero` と `low-positive short trapezoid` を含める
- same-vowel floor は初回から補助導入する
- observation 契約は `bool` 追加で持つ

本タスクは以下と切り分ける。

- MS11-9D-2 / 9D-5 の cross-vowel transition / continuity floor
- final closing hold / softness
- GUI parameter 追加
- RMS 全体閾値の全面見直し
- MS12

---

## 1. 背景

現状の MS11-9D 系では、

- same-vowel 1 event / 2 event zero-run
- cross-vowel short gap
- cross-vowel zero-run continuity floor

までは扱えるようになっている。

一方で、実データ VMD では次の課題が残る。

- same-vowel の短い再分節が、bridge 候補に乗らず独立台形として残る
- その結果、1-2 frame 単位で急閉口・急開口が連続する
- 見た目として「同じ母音を引いている」のではなく「パカパカしている」印象になる

この問題は、cross-vowel continuity floor だけでは解けない。
理由は、対象が **同一母音の連続性** にあるためである。

したがって MS11-9D-6 では、
same-vowel 内の短周期な再分節を
**same-vowel burst smoothing**
として独立に扱う。

---

## 2. 目的

MS11-9D-6 の目的は次のとおり。

- same-vowel の短 zero / short trapezoid 連打を、独立閉口ではなく同一母音 continuity として扱う
- same-vowel 内の急な開閉を減らす
- Preview / export の semantics を維持する
- cross-vowel 側の既存ロジックと責務を混ぜない

---

## 3. スコープ

### 3-1. 含める対象

- same-vowel short zero
- same-vowel short zero-run
- same-vowel short trapezoid burst
- writer / Preview での same-vowel burst smoothing
- observation による candidate 識別

### 3-2. 含めない対象

- cross-vowel transition の再設計
- cross-vowel continuity floor の再設計
- final closing
- GUI parameter 追加
- RMS threshold 全体見直し

---

## 4. 非目標

- same-vowel の全イベントを一律連結すること
- same-vowel の valley を完全に消すこと
- 無音区間全般の救済
- Preview 側だけの smoothing

---

## 5. 基本方針

### 5-1. same-vowel burst は独立閉口として扱わない

対象となる short zero / short trapezoid は、
可能な限り same-vowel 内の valley / sub-peak として再構成する。

### 5-2. 第一候補は multi-valley envelope への吸収

MS11-9D-6 の本筋は smoothing ではなく、
**same-vowel burst を multi-point envelope として再解釈すること**
である。

理由:

- 見た目改善が最も自然
- 既存 MS11-3 / MS11-9D-3 の same-vowel valley 思想と整合しやすい
- Preview / export を揃えやすい

### 5-3. 必要なら same-vowel floor を補助導入する

burst の valley が深すぎて 0 に落ちる場合だけ、
same-vowel 専用の continuity floor を補助的に使う余地を残す。

初回固定:

- multi-valley envelope への吸収を優先する
- それでも 0 に落ちる case に対して same-vowel floor を補助導入する

### 5-4. smoothing よりも再解釈を優先する

単純な delta limiter や slope smoothing は補助策として有効だが、
初回では「同一母音の再分節をどう見るか」の解決を優先する。

---

## 6. 責務分割

### 6-1. pipeline

主責務:

- `same-vowel burst candidate` を observation で識別する
- 前後 non-zero の same-vowel 文脈を保持する

方向性:

- `timeline` は不変
- 正本は `observations`

### 6-2. writer

主責務:

- same-vowel burst candidate を独立台形として立てず、同一 vowel-run 内の valley / sub-peak として再構成する
- 必要なら same-vowel floor を補助的に入れる

### 6-3. Preview

主責務:

- writer と同じ same-vowel burst semantics を表示する

### 6-4. GUI

固定:

- GUI 追加なし
- fixed policy

---

## 7. candidate の考え方

same-vowel burst candidate の方向性:

- 前後が同一母音の non-zero
- 間に short zero または short trapezoid 群がある
- 発話継続中とみなせる
- final closing ではない

初回固定:

- burst の最大幅は `2 event / 2 frame`
- `low-positive short trapezoid` も candidate に含める

対象例:

- `positive -> zero -> positive`
- `positive -> low positive -> zero -> positive`
- `positive -> zero -> low positive -> zero -> positive`

非対象例:

- 明確な長無音
- cross-vowel 遷移
- final closing

---

## 8. 形状方針

### 8-1. 第一候補: multi-valley envelope

same-vowel burst は、前後の same-vowel peak を主峰として残しつつ、
その間の short segment を valley / sub-peak に置く。

例:

- main peak
- shallow valley
- sub-peak
- shallow valley
- next peak

### 8-2. 第二候補: same-vowel continuity floor

burst 区間の valley が 0 に落ち切る場合だけ、
same-vowel floor を補助値として置く。

初回では optional 方針とし、
まずは multi-valley envelope で足りるかを優先確認する。

### 8-3. 第三候補: delta limiter

補助的な smoothing として、

- minimum shoulder
- max delta per frame

を導入する余地はあるが、
初回の主目的にはしない。

---

## 9. Preview / export 整合方針

MS11-9D-6 でも、次を維持する。

- Preview 独自 smoothing を入れない
- writer と Preview は同じ candidate を見る
- same-vowel burst の valley / sub-peak 配置を共通にする

---

## 10. 最低限のテスト観点

### 10-1. pipeline

- same-vowel short zero / short trapezoid が burst candidate として識別される

### 10-2. writer

- same-vowel burst が独立閉口の連打にならず multi-valley 化される
- same-vowel burst の急な 0 落ちが減る
- cross-vowel の既存 transition / floor を壊さない

### 10-3. Preview

- Preview が writer と同じ burst control point を表示する

### 10-4. real-data

- 24f の「お」のような単発 zero が same-vowel continuity として扱われる
- 28f-35f の「う」のような短台形列が burst smoothing される
- MMD 上の急開閉感が減る

---

## 11. スコープ外

- same-vowel floor 値の GUI 化
- delta limiter の一般化
- 無音区間全体の再設計
- MS12

---

## 12. 未確認事項

現時点で未固定の項目は次のとおり。

- `low-positive` の具体閾値
- same-vowel floor の固定値
- multi-valley の control point 配置をどこまで細かくするか

---

## 13. 実装可能性の判断

現時点では、**実装開始可能**である。

理由:

- burst 最大幅は固定済み
- `zero / low-positive short trapezoid` を含める方針が固定済み
- same-vowel floor 導入方針が固定済み
- observation 契約は bool 追加で固定済み

残るのは、実装詳細の調整項目である。

---

## 14. ユーザー判断が必要な点

現時点で必須のユーザー判断は解消済みである。

残るのは次の実装詳細であり、通常は実装側で安全に決められる範囲である。

1. `low-positive` の具体閾値
2. same-vowel floor の固定値
3. multi-valley control point の細部

---

## 15. 要約

MS11-9D-6 は、
**same-vowel の短い再分節による急開閉を、独立閉口ではなく同一母音 continuity として再解釈する**
ための後続計画である。

本筋は、same-vowel burst を multi-valley envelope に吸収することにある。

現時点では実装候補として十分成立しており、
主要条件は固定済みである。
