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
- MS11-9E / E-2 / E-3 / E-4 same-vowel residual refinement
- MS11-9F / F-2 / F-3 / F-4 cross-vowel residual refinement
- MS11-9G top-end shaping residual refinement
- MS11-9FIX7 closing smoothing tail-contract realignment

本書は「未解決の見た目課題」「設計上の混雑」「今後の切り分け」を整理する。
MS11-9 系全体の横断要約は
[docs/MS11-9_Summary_and_Handoff.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11-9_Summary_and_Handoff.md)
を参照する。

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

現在地更新:

- MS11-9E で residual same-vowel burst smoothing refinement を追加した
- MS11-9E-2 で same-vowel candidate classification の最小拡張を追加した
- MS11-9E-3 で same-vowel-like zero/low-energy event の representative span を導入し、pipeline 上で candidate が立つ状態まで到達した
- MS11-9E-4 で single-event same-vowel zero/low-energy span に writer-side synthetic bridge を追加し、初めて実データ VMD 差分まで到達した
- `Test11_9l.vmd` は現行 repo 再生成結果と一致し、`Test11_9k.vmd` との差分も確認済みである
- 現時点では「same-vowel 改善が実出力へ反映されない」段階は脱した
- 一方で、見た目上どこまで自然化できたかの体感確認はまだ継続が必要である

整理:

- same-vowel 側の残課題は、「candidate が立たない / writer に届かない」段階から、「実データ上での自然さの最終調整」段階へ移行したとみなせる

### 2.2 cross-vowel でも発話中の完全閉口が残る箇所がある

- continuity floor を追加しても、候補 classification に乗らない speech-internal cross-vowel case は残りうる
- 特に「見た目上は cross-vowel continuity を期待したいが、前後とも zero-peak として落ちている」ケースでは、まだ完全閉口が出る可能性がある
- current policy は安全側であり、zero-peak 全救済にはしていないため、取りこぼしは構造上残る

現在地更新:

- MS11-9F / F-2 / F-3 により、cross-vowel residual zero-peak / full closure には段階的な追加分類を入れた
- `sample_input2` 観測での residual cross-vowel は `23 -> 10 -> 7 -> 3` まで減少した
- `cross_vowel_transition` は実出力差分へ届いており、`9n` は MS11-9F、`9m` は MS11-9F-2、`9o` は MS11-9F-3 と一致確認済みである
- `cross_vowel_floor` も F-3 で `122/123`, `229/230` を拾えるようになり、`cross_floor = 4` を確認した
- 現時点で残るのは `idx 6`, `172`, `193` 相当の 3 件であり、うち `172/193` は pause 寄りの非対象候補、`6` は mixed-gap 境界 case とみなす方向が有力である
- したがって本項目は「未着手の根本改善」段階ではなく、「残件 3 件をどこまで救済対象にするかの最終整理」段階へ移行した
- `MS11-9F-4` では、この 3 件をさらに無理に救済せず、`172/193` を非対象候補、`6` を保留境界 case として文書上で確定扱いにした

### 2.3 top-end shaping residual は MS11-9G で一旦クローズ扱いとする

- `peak_end_value` により 3 点目を 2 点目の単純コピーから外せるようになった
- ただし RMS サンプル配置によっては十分に下がらない、または逆に下がり方が急に見えるケースが残る
- `peak_end_frame` 以降で最初に取れる RMS を使う方式は現状妥当だが、最終形として固定されたわけではない

現在地更新:

- 今回の MS11-9G で、`peak_end_value` の 1 点依存を和らげる writer-side top-end refinement を追加した
- `tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` に flat-top / 急減衰 residual の synthetic 回帰を追加し、repo 内回帰は通過済みである
- ローカル再生成の
  [dist/_tmp_ms11_9g_sample_input2_upper1.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9g_sample_input2_upper1.vmd)
  は [Test11_9o.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9o.vmd) と不一致であり、top-end shaping 差分が実出力へ届くことを確認した
- さらに [Test11_9p.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9p.vmd) は上記ローカル再生成結果と一致しており、MS11-9G の export 反映は確認済みである
- MMD 側での確認も取れたため、本項目は現時点で一旦クローズ扱いとする
- 今後は新しい実データで再発が見えた場合のみ、再オープン対象として扱う

### 2.4 閾値が暫定値のままである

現時点では、次の値は安全側の初回値として固定されている。

- `cross-vowel continuity floor = 0.1`
- `same-vowel floor = 0.1`
- `same-vowel burst low-positive threshold = 0.2`
- `zero-run span upper bound = 2 event / 2 frame`

これらは実データに対する最終確定値ではなく、今後の観測で見直し余地がある。

現在地更新:

- 今回の対応では GUI parameter や global threshold の再調整は行っていない
- 既存の threshold / floor 値は引き続き暫定値扱いでよい
- ただし MS11-9E-4 で single-event same-vowel span に bridge を入れる段階まで進んだため、次は値の妥当性を実データ観測で見直せる状態になった

### 2.5 `observations` 契約が混雑してきている

- MS11-9D 以降で candidate bool や span 情報を `PeakValueObservation` へ段階的に追加してきた
- 現状の利点は `timeline` を canonical writer input のまま保てている点にある
- 一方で same-vowel / cross-vowel / zero-run / burst / continuity-floor の判定が observation に集まり、見通しは悪化している
- 将来的には candidate 種別の整理、補助 dataclass 化、または observation-layer 再編が必要になる可能性がある

現在地更新:

- MS11-9E-3 では observation field 追加を避け、pipeline helper 内の representative span 計算で対応した
- そのため observation dataclass 自体の混雑は大きく悪化していない
- 一方で、same-vowel 系の判定と writer handoff のロジックは helper 側で複雑化しており、設計整理の必要性は引き続き残る
- cross-vowel でも F / F-2 / F-3 を通じて `transition residual helper` と `floor residual helper` が追加され、helper 内局所判定の比重は増えた
- 現時点では「observation field を増やさず進めた」ことを抑制策として扱う

### 2.6 Preview / export は整合していても、MMD 上の見え方確認は継続が必要

- 現在の設計は Preview / export の semantics を揃えることを優先している
- ただし、実際の MMD 再生で「自然に見えるか」は別の検証軸である
- `sample_input2` や `Test11_9g.vmd` 系の実データ観測は、今後も継続が必要である

現在地更新:

- Preview / export の semantics 一致は引き続き維持されている
- MS11-9E-4 では writer helper の変更に対し Preview テストも更新し、repo 内テストは通過済みである
- `Test11_9l.vmd` が現行 repo 再生成結果と一致しており、export 反映は確認済みである
- cross-vowel でも `Test11_9n.vmd`, `Test11_9m.vmd`, `Test11_9o.vmd` がそれぞれ F / F-2 / F-3 のローカル再生成結果と一致しており、段階的な export 反映は確認済みである
- top-end shaping でも `Test11_9p.vmd` が MS11-9G のローカル再生成結果と一致しており、writer-side 値配分変更が実 export へ届くことを確認済みである
- closing smoothing でも `Test11_9S1.vmd` / `Test11_9S2.vmd` / `Test11_9S3.vmd` / `Test11_9S4.vmd` の比較により、
  FIX7 後は `開口維持` / `閉口スムーズ` が tail 短縮ではなく末尾追加として出ていることを確認済みである
- top-end shaping については MMD 側確認も取れたため、現時点では一旦クローズ扱いでよい
- 今後の焦点は same-vowel の見え方評価、observation 契約整理、
  および closing smoothing の体感上の自然さ確認へ寄る

---

## 3. 現時点で壊してはいけない前提

今後の改善でも、少なくとも次は維持する。

- `timeline` は canonical writer input のまま維持する
- bridge / floor / burst 候補の正本は `observations` 側に置く
- Preview 独自近似を入れず、writer と同じ semantics を使う
- final closing 系と speech-internal gap / burst 系を混ぜない
- `closing_hold_frames` / `closing_softness_frames` は family ごとに別意味で扱わず、
  末尾 tail の共通後処理として解釈する
- MS12 の GUI responsiveness / splash / packaging とは混ぜない

---

## 4. 次段候補

次段の候補は、現時点では以下が有力である。

### 4.1 residual same-vowel burst の追加緩和

- same-vowel burst の valley depth / shoulder をさらに緩和する
- multi-valley と floor の優先順位や値配分を再調整する

現在地更新:

- MS11-9E〜E-4 により、same-vowel continuity 系は pipeline candidate 化から writer-side shape 反映まで到達した
- 次段では「効かない問題」より、「効き方の評価と微調整」を主題に置くのが自然である

### 4.2 residual cross-vowel zero-peak case の追加分類

- continuity-floor candidate に乗らない speech-internal cross-vowel case を、別 classification として扱う
- ただし zero-peak 全救済には広げない

現在地更新:

- F / F-2 / F-3 により cross-vowel residual zero-peak / full closure は大きく圧縮された
- `MS11-9F-4` により、cross-vowel 側は「境界 case と非対象候補の整理」まで完了した
- したがって cross-vowel は次段の主対象というより、必要時のみ `idx 6` を個別再検討する保留テーマとして扱うのが自然である

### 4.3 observation-layer の整理

- `PeakValueObservation` に積み上がった candidate 群を再整理する
- 実装を広げる前に、責務分割を軽く整える余地がある

現在地更新:

- 今すぐ全面再編が必要な段階ではないが、same-vowel / cross-vowel の residual helper が増えてきたため、中期候補として維持する

### 4.5 closing smoothing の自然さ評価と必要時の微調整

- FIX7 により、`開口維持` / `閉口スムーズ` の旧不具合だった tail 短縮は
  実出力 VMD 差分上では止められている
- 一方で、追加された tail が MMD 上で常に自然に見えるかは、
  実ケースごとの体感確認がまだ必要である

現在地更新:

- `Test11_9S1.vmd` と `Test11_9S2.vmd` の比較では、
  `開口維持=1` は短縮ではなく末尾延長として出ている
- `Test11_9S3.vmd` でも `閉口スムーズ=1` は slope 追加として出ている
- `Test11_9S4.vmd` でも `開口維持=2 + 閉口スムーズ=2` は hold + slope の段階的 tail 追加として出ている
- よって本項目の次段は「不具合再発対応」ではなく、「効き方の自然さの確認と必要時の微調整」である

### 4.4 top-end shaping の見え方評価と必要時の微調整

- `peak_end_value` の局所安定化後も、実際の MMD 再生で flat-top / 急減衰がどの程度改善したかを確認する
- 必要なら、top-end 値配分の微調整または family 別でない範囲の共通 rule 再調整を検討する

現在地更新:

- MS11-9G により writer-side top-end refinement は実出力まで到達した
- MMD 側確認まで完了したため、現時点では保留テーマとして扱うのが自然である
- 再開条件は、新しい実データで flat-top / 急減衰 residual が再発した場合とする

---

## 5. 備考

- 本書は「残課題の整理」が目的であり、新規実装プラン本文ではない
- 実装計画そのものは、各 `MS11-9D*_Implementation_Plan.md` を正本とする
