# MS11-9 Remaining Issues

## 0. 文書目的

本書は、MS11-9 系で追加実装された以下の内容を一度区切ったうえで、
**現時点で残っている課題**を整理するための正本である。

- MS11-9 Preview trapezoid / multi-point display alignment
- MS11-9B Closing Softness GUI exposure
- MS11-9C Lip Hold GUI exposure and final-closing hold semantics alignment
- MS11-9D same-vowel micro-gap bridging
- MS11-9D-2 cross-vowel transition bridging
- MS11-9D-3 zero-run span bridging
- MS11-9D-4 peak-end decayed value / continuity-floor 補助
- MS11-9D-5 cross-vowel zero-run continuity-floor refinement
- MS11-9D-6 same-vowel burst smoothing

本書は「未解決の見た目課題」「設計上の混雑」「今後の切り分け」を整理する。

---

## 1. 現在地

現ワークスペースでは、MS11-9 系の主目的であった以下は概ね反映済みである。

- Preview は writer-side shape semantics に近い polygon / control-point 表示へ移行済み
- final closing の hold / softness は GUI / Preview / export handoff を含めて導線化済み
- same-vowel micro-gap は `observations` 正本で bridge 候補化済み
- cross-vowel transition は最小 overlap で橋渡し済み
- zero-run span は `2 event / 2 frame` まで bridge 候補化済み
- bridge / transition 周辺の 3 点目値は `peak_end_value` により decayed top-end を持てる
- cross-vowel zero-run には continuity floor が導入済み
- same-vowel short zero / low-positive short trapezoid には burst smoothing が導入済み

一方で、実データ VMD 観測ではまだ「完全に自然」とは言えず、以下の残課題がある。

---

## 2. 残課題

### 2.1 same-vowel 連音でも急な開閉が残る箇所がある

- same-vowel burst smoothing により大幅に緩和されたが、まだ short burst が独立台形寄りに見える箇所が残る
- 特に `positive -> zero -> positive` だけでなく、`positive -> low-positive -> zero -> positive` のような複合 short burst では急な肩が残ることがある
- multi-valley envelope と same-vowel floor の組み合わせが、常に自然な valley depth を作るとは限らない

### 2.2 cross-vowel でも発話中の完全閉口が残る箇所がある

- continuity floor を追加しても、候補 classification に乗らない speech-internal cross-vowel case は残りうる
- 特に「見た目上は cross-vowel continuity を期待したいが、前後とも zero-peak として落ちている」ケースでは、まだ完全閉口が出る可能性がある
- current policy は安全側であり、zero-peak 全救済にはしていないため、取りこぼしは構造上残る

### 2.3 top-end shaping は改善したが、まだ flat-top / 急減衰が残る

- `peak_end_value` により 3 点目を 2 点目の単純コピーから外せるようになった
- ただし RMS サンプル配置によっては十分に下がらない、または逆に下がり方が急に見えるケースが残る
- `peak_end_frame` 以降で最初に取れる RMS を使う方式は現状妥当だが、最終形として固定されたわけではない

### 2.4 閾値が暫定値のままである

現時点では、次の値は安全側の初回値として固定されている。

- `cross-vowel continuity floor = 0.1`
- `same-vowel floor = 0.1`
- `same-vowel burst low-positive threshold = 0.2`
- `zero-run span upper bound = 2 event / 2 frame`

これらは実データに対する最終確定値ではなく、今後の観測で見直し余地がある。

### 2.5 `observations` 契約が混雑してきている

- MS11-9D 以降で candidate bool や span 情報を `PeakValueObservation` へ段階的に追加してきた
- 現状の利点は `timeline` を canonical writer input のまま保てている点にある
- 一方で same-vowel / cross-vowel / zero-run / burst / continuity-floor の判定が observation に集まり、見通しは悪化している
- 将来的には candidate 種別の整理、補助 dataclass 化、または observation-layer 再編が必要になる可能性がある

### 2.6 Preview / export は整合していても、MMD 上の見え方確認は継続が必要

- 現在の設計は Preview / export の semantics を揃えることを優先している
- ただし、実際の MMD 再生で「自然に見えるか」は別の検証軸である
- `sample_input2` や `Test11_9g.vmd` 系の実データ観測は、今後も継続が必要である

---

## 3. 現時点で壊してはいけない前提

今後の改善でも、少なくとも次は維持する。

- `timeline` は canonical writer input のまま維持する
- bridge / floor / burst 候補の正本は `observations` 側に置く
- Preview 独自近似を入れず、writer と同じ semantics を使う
- final closing 系と speech-internal gap / burst 系を混ぜない
- MS12 の GUI responsiveness / splash / packaging とは混ぜない

---

## 4. 次段候補

次段の候補は、現時点では以下が有力である。

### 4.1 residual same-vowel burst の追加緩和

- same-vowel burst の valley depth / shoulder をさらに緩和する
- multi-valley と floor の優先順位や値配分を再調整する

### 4.2 residual cross-vowel zero-peak case の追加分類

- continuity-floor candidate に乗らない speech-internal cross-vowel case を、別 classification として扱う
- ただし zero-peak 全救済には広げない

### 4.3 observation-layer の整理

- `PeakValueObservation` に積み上がった candidate 群を再整理する
- 実装を広げる前に、責務分割を軽く整える余地がある

---

## 5. 備考

- 本書は「残課題の整理」が目的であり、新規実装プラン本文ではない
- 実装計画そのものは、各 `MS11-9D*_Implementation_Plan.md` を正本とする
