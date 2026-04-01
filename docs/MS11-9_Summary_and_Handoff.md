# MS11-9 Summary and Handoff

## 0. 文書目的

本書は、MS11-9 系の実装・検証・文書分岐を一度まとめ直し、
**現在の到達状態と今後の参照先を短時間で把握するための横断サマリ**
として置く。

個別の実装計画や詳細な追跡は各 Implementation Plan を正本とし、
本書は「何が終わり、何が残り、どこを見ればよいか」を整理する。

---

## 1. 対象範囲

MS11-9 系として、少なくとも次を含む。

- MS11-9 Preview trapezoid / multi-point display alignment
- MS11-9B Closing Softness GUI exposure
- MS11-9C Lip Hold GUI exposure and final-closing hold semantics alignment
- MS11-9D same-vowel micro-gap bridging
- MS11-9D-2 cross-vowel transition bridging
- MS11-9D-3 zero-run span bridging
- MS11-9D-4 peak-end decayed value / continuity-floor 補助
- MS11-9D-5 cross-vowel zero-run continuity-floor refinement
- MS11-9D-6 same-vowel burst smoothing
- MS11-9E / E-2 / E-3 / E-4 same-vowel residual refinement chain
- MS11-9F / F-2 / F-3 / F-4 cross-vowel residual refinement chain
- MS11-9G top-end shaping residual refinement
- MS11-9FIX7 closing smoothing tail-contract realignment

---

## 2. 現在の総括

MS11-9 系は、当初の主題だった

- Preview と writer の shape semantics 整合
- final closing の GUI / Preview / export handoff
- same-vowel / cross-vowel の speech-internal continuity 改善
- zero-run span、continuity floor、burst smoothing
- top-end shaping の decayed peak-end 導入
- closing smoothing の family 別 tail 契約整理

までを一通り反映済みである。

さらに後続の E / F / G 系により、

- same-vowel residual は candidate 化から writer-side shape 反映まで到達
- cross-vowel residual は `23 -> 10 -> 7 -> 3` まで圧縮し、停止基準を文書上で確定
- top-end shaping residual は writer-side refinement が実出力に到達
- closing smoothing は FIX7 により、family ごとの別契約ではなく tail 後処理の共通契約へ寄せた

という段階まで進んでいる。

---

## 3. 変遷の要約

### 3.1 基礎整備

- MS11-9:
  Preview を trapezoid / multi-point aware な表示へ揃えた
- MS11-9B:
  `closing_softness_frames` を GUI / Preview / export へ通した
- MS11-9C:
  `closing_hold_frames` を GUI / Preview / export へ通し、final closing semantics を整えた

### 3.2 bridge / continuity 系の拡張

- MS11-9D:
  same-vowel micro-gap bridging
- MS11-9D-2:
  cross-vowel transition bridging
- MS11-9D-3:
  zero-run span bridging
- MS11-9D-4:
  decayed top-end shaping と continuity-floor 補助
- MS11-9D-5:
  cross-vowel zero-run continuity-floor refinement
- MS11-9D-6:
  same-vowel burst smoothing

### 3.3 residual 改善の後段

- MS11-9E 系:
  same-vowel residual を pipeline / writer の両段から詰めた
- MS11-9F 系:
  cross-vowel residual を transition / floor / non-target の整理まで進めた
- MS11-9G:
  top-end shaping residual を writer-side `peak_end_value` 局所安定化で詰めた
- MS11-9FIX7:
  closing hold / softness の smoothing を family 非依存の tail post-process へ寄せた

---

## 4. レイヤ別の現在地

### 4.1 pipeline

- `timeline` は canonical writer input のまま維持
- speech-internal continuity の候補正本は `observations`
- same-vowel / cross-vowel / zero-run / burst / floor の candidate 判定は主に pipeline 起点
- E / F 系で helper 内局所判定は増えたが、observation field の増殖は抑制している

### 4.2 writer

- 最終 shape semantics の主責務を持つ
- same-vowel / cross-vowel / zero-run / floor / burst の形状差分は writer で出る
- G で `peak_end_value` の 1 点依存を和らげ、top-end の値配分を調整した
- FIX7 で `closing_hold_frames` / `closing_softness_frames` の tail 解釈を
  raw frame 生成段階から共通化した

### 4.3 preview

- writer helper 再利用を維持
- Preview 独自近似を増やさず、export と同じ semantics を表示する方針を維持

### 4.4 GUI / handoff

- `closing_softness_frames`
- `closing_hold_frames`
- `upper_limit`

を current 値として Preview / export に同じ意味で渡す構造は維持されている。

---

## 5. 実出力確認の節目

実データ VMD の照合で確認できている節目は次のとおり。

- `Test11_9l.vmd`:
  MS11-9E-4 の same-vowel writer-side bridge が実出力へ到達
- `Test11_9n.vmd`:
  MS11-9F の cross-vowel transition residual 改善が実出力へ到達
- `Test11_9m.vmd`:
  MS11-9F-2 の追加 transition residual 改善が実出力へ到達
- `Test11_9o.vmd`:
  MS11-9F-3 の floor 側追加分類が実出力へ到達
- `Test11_9p.vmd`:
  MS11-9G の top-end shaping refinement が実出力へ到達
- `Test11_9S2.vmd`:
  FIX7 後、`開口維持=1` が tail 短縮ではなく末尾延長として出ることを確認
- `Test11_9S3.vmd`:
  FIX7 後、`閉口スムーズ=1` が tail 短縮ではなく slope 追加として出ることを確認
- `Test11_9S4.vmd`:
  FIX7 後、`開口維持=2 + 閉口スムーズ=2` が hold + slope の段階的 tail 追加として出ることを確認

---

## 6. 現時点のクローズ判断

### 6.1 same-vowel

- 「candidate が立たない」
- 「writer に届かない」

段階は越えており、
現在は見え方の微調整テーマとして扱う。

### 6.2 cross-vowel

- residual は `23 -> 10 -> 7 -> 3`
- `idx 172 / 193` は pause 寄り非対象候補
- `idx 6` は mixed-gap 境界 case

として、MS11-9F-4 で停止基準を文書上確定済み。

### 6.3 top-end shaping

- MS11-9G により writer-side refinement は実出力まで到達
- MMD 側確認も取れたため、現時点では一旦クローズ扱いとする
- 再開は、新しい実データで再発が見えた場合に限る

### 6.4 closing smoothing

- FIX7 により、旧不具合だった「`hold / softness >= 1` で全音の後半スロープが一律短縮する」挙動は
  実出力 VMD 差分上では確認されなくなった
- 現在の主題は不具合修正よりも、tail 追加の見え方が自然かどうかの評価である

---

## 7. 現在の主な残課題

MS11-9 系として今後も残る主題は、次の 2 系統に絞られる。

- same-vowel の見え方微調整
- observation / handoff 契約整理
- closing smoothing の自然さ確認

cross-vowel と top-end shaping は、現時点では主対象から外してよい。

---

## 8. 参照先

用途ごとの正本は次を参照する。

- 現在の残課題:
  [docs/MS11-9_Remaining_Issues.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11-9_Remaining_Issues.md)
- 契約整理:
  [docs/MS11-9_Observation_Handoff_Contract_Memo.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11-9_Observation_Handoff_Contract_Memo.md)
- 個別実装の追跡:
  `docs/MS11-9*_Implementation_Plan.md`
- 全体の同期記録:
  [docs/repo_milestone.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/repo_milestone.md),
  [docs/Version_Control.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/Version_Control.md)

---

## 9. 要約

MS11-9 系は、Preview / GUI / pipeline / writer をまたぐ一連の lip-motion quality 改善として、
same-vowel、cross-vowel、zero-run、continuity floor、burst smoothing、top-end shaping まで段階実装を完了した。

現在は、

- same-vowel 微調整
- observation 契約整理

を残す一方で、

- cross-vowel residual
- top-end shaping residual

は文書上・実出力上ともに一旦区切れる状態まで到達している。
