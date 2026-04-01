# MS11-9E Implementation Plan

## Residual same-vowel burst smoothing refinement

## 0. 位置づけ

MS11-9E は、`docs/MS11-9_Remaining_Issues.md` に整理された残課題のうち、
**same-vowel 連音内にまだ残っている急な開閉感**を最小単位で追加緩和するための計画である。

本タスクは、MS11-9D-6 までで導入済みの

- same-vowel micro-gap bridging
- zero-run span bridging
- same-vowel burst smoothing
- same-vowel floor
- multi-valley envelope

の延長として扱う。

MS11-9E では、次を主対象とする。

- `positive -> zero -> positive`
- `positive -> low-positive -> zero -> positive`
- `positive -> zero -> low-positive -> zero -> positive`

のような **same-vowel short re-segmentation** のうち、
MS11-9D-6 実装後も独立 burst 寄りに見える residual case

本タスクは、以下とは切り分ける。

- cross-vowel residual zero-peak case の追加分類
- final closing hold / softness の再設計
- RMS 閾値全体の再調整
- MS12

---

## 1. 背景

現行 workspace では、same-vowel burst candidate は `observations` 側で識別され、
writer / Preview はそれを same-vowel continuity として再解釈できる構造になっている。

一方、現状の生成物観測と `docs/MS11-9_Remaining_Issues.md` では、
次の問題がまだ残っている。

- same-vowel short burst が独立台形寄りに見える箇所がある
- valley depth が深すぎて、視覚上は「一度閉じた」ように見える箇所がある
- low-positive short trapezoid を含む複合 burst では shoulder が急に見える箇所がある
- multi-valley envelope と same-vowel floor の組み合わせが常に十分自然とは限らない

したがって MS11-9E では、
same-vowel burst smoothing の根本方針は維持したまま、
**valley depth / shoulder 配分の refinement** に限定して進める。

---

## 2. 目的

MS11-9E の目的は次のとおり。

- same-vowel burst の residual sharp shoulder を減らす
- same-vowel continuity は維持しつつ、valley を深く落としすぎない
- Preview / export の semantics 一致を維持する
- `timeline` 非改変 / `observations` 正本の原則を維持する

---

## 3. スコープ

### 3-1. 含める対象

- same-vowel burst candidate の追加緩和
- burst 区間の valley depth 再配分
- low-positive short trapezoid を含む複合 burst の shoulder 緩和
- writer / Preview 共通 helper の最小 refinement
- 必要最小限の追加テスト

### 3-2. 含めない対象

- cross-vowel transition / continuity-floor の再設計
- final closing 系
- GUI parameter 追加
- `PeakValueObservation` の全面再編
- RMS 定数再調整

---

## 4. 非目標

- same-vowel の全ケースを一律 flatten すること
- valley を完全に消すこと
- same-vowel floor を GUI 化すること
- cross-vowel の問題を同時解決すること
- timeline 契約を変えること

---

## 5. 基本方針

### 5-1. 既存構造を崩さず、burst 解釈だけを refinement する

MS11-9E では、新しい大分類を増やすより、
既存の `is_same_vowel_burst_candidate` と span 情報を利用して、
writer / Preview が作る same-vowel envelope の値配分を調整する。

### 5-2. 調整対象は `valley depth` と `shoulder` に限定する

優先するのは次の 2 点である。

- burst 区間 valley が深すぎる場合の引き上げ
- low-positive short trapezoid が sub-peak として残る場合の肩の急さの緩和

### 5-3. `timeline` は canonical input のまま維持する

MS11-9E でも次を維持する。

- `timeline` は canonical writer input
- candidate / span / burst 判定の正本は `observations`
- Preview は writer helper 再利用を優先

### 5-4. 初回は same-vowel floor の値そのものは変えない

初回ではまず、
**floor 値を変える前に配分ロジックを見直す**。

理由:

- 現状の残課題は「発火していない」より「発火しても見え方が硬い」寄り
- 値の再調整より、既存値の使い方の見直しが先の方が差分を小さくできる

---

## 6. 想定アプローチ

MS11-9E で有力な実装方針は次の 2 系統である。

### 案A. valley floor priority の再調整

- same-vowel burst / multi-valley 生成時に、valley 値の下限適用をやや強める
- zero burst と low-positive burst を同じ continuity 系として寄せる
- 既存 floor 値は維持しつつ、burst 区間では valley が floor に寄りやすいよう再配分する

利点:

- 差分が小さい
- Preview / export 共通化しやすい
- `observations` 契約追加なしでも進めやすい

懸念:

- shoulder の急さが十分に消えない可能性がある

### 案B. burst sub-peak weight の減衰

- low-positive short trapezoid を valley に寄せた sub-peak として扱い、
  main peak に比べて弱く残す
- burst 区間内の top / sub-peak / valley の配分を明示的に調整する

利点:

- `positive -> low-positive -> zero -> positive` には効きやすい

懸念:

- control point 配分が複雑になりやすい
- same-vowel burst helper のロジックが少し重くなる

### 初回推奨

MS11-9E 初回は **案Aを優先**する。

理由:

- 現在の構造と最も整合する
- 実装差分を writer / Preview の共通 helper に限定しやすい
- 次段で案Bを追加する余地を残せる

---

## 7. 責務分割

### 7-1. pipeline

主責務:

- 既存 burst candidate 識別を維持する
- 必要なら span / burst candidate 判定の既存条件を軽く補強する

初回方針:

- pipeline 側は原則変更最小
- 新しい大分類 bool は増やさない方向を優先

### 7-2. writer

主責務:

- same-vowel burst が multi-valley として再構成されるときの
  valley depth / shoulder 配分を refinement する
- zero / low-positive の複合 burst を独立閉口連打に見せない

主対象候補:

- same-vowel span 調整 helper
- burst candidate を envelope へ吸収する helper
- valley 値計算部

### 7-3. Preview

主責務:

- writer と同じ burst smoothing 結果を表示する
- Preview 独自補間は入れない

初回方針:

- writer helper 再利用を維持
- Preview 固有の近似は追加しない

### 7-4. GUI

固定:

- GUI 追加なし
- current value handoff 変更なし

---

## 8. 実装フェーズ

## Phase 1. residual burst の再現ケース固定

作業:

- 既存 VMD / 既存テストから residual same-vowel burst 例を 1〜2 パターン固定する
- 可能なら `tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` に最小再現を追加する

完了条件:

- 「今回消したい不自然さ」がテストで明示される

## Phase 2. writer 側 valley depth / shoulder 配分 refinement

作業:

- same-vowel burst helper の値配分を見直す
- zero burst と low-positive burst を continuity 系として寄せる
- valley が深すぎる case を緩和する

完了条件:

- same-vowel burst の独立閉口感が減る

## Phase 3. Preview alignment

作業:

- Preview が writer と同じ control point 配分になることを確認
- Preview test を更新する

完了条件:

- Preview / export が同じ burst semantics を維持する

## Phase 4. regression 確認

作業:

- 既存 same-vowel / cross-vowel / closing 系の回帰確認
- floor / transition 系に副作用が出ていないことを確認

完了条件:

- MS11-9E 対象外の family を壊していない

---

## 9. 最低限のテスト観点

### 9-1. writer

- same-vowel `positive -> zero -> positive` が急閉口に見えにくくなる
- same-vowel `positive -> low-positive -> zero -> positive` が独立台形連打に見えにくくなる
- same-vowel burst の valley が必要以上に 0 へ寄らない
- cross-vowel transition / continuity-floor を壊さない

### 9-2. Preview

- Preview が writer と同じ control point 配分を表示する
- same-vowel burst smoothing の結果が Preview / export で一致する

### 9-3. pipeline

- 既存 burst candidate 判定を壊さない
- span 情報の前提が維持される

---

## 10. ユーザー判断が必要な点

現時点で実装開始に必須の判断は多くないが、
次の 3 点は先に合わせておくと安全である。

### Q1. MS11-9E 初回は residual same-vowel burst に絞るか

- 推奨案: **はい**
- 理由:
  - 現在の残課題の中で最小単位として自然
  - 既存構造に一番乗せやすい
  - cross-vowel を同時に触ると observation 契約の混雑が進みやすい

### Q2. 初回は same-vowel floor の固定値を変えず、配分ロジック優先で進めるか

- 推奨案: **はい**
- 理由:
  - 値変更より差分が小さい
  - 現状の問題は値そのものより使い方の可能性が高い
  - 既存テストへの影響を限定しやすい

### Q3. 初回は新しい observation bool を追加せず、既存 burst candidate を再利用するか

- 推奨案: **はい**
- 理由:
  - `PeakValueObservation` の混雑をこれ以上増やしにくい
  - MS11-9E の目的は classification 追加より smoothing refinement にある

---

## 11. スコープ外

- residual cross-vowel full closure の追加分類
- threshold 値の再確定
- observation-layer の全面再編
- MS12

---

## 12. 到達イメージ

MS11-9E 完了時の到達イメージは次のとおり。

- same-vowel burst の residual sharp shoulder が減る
- low-positive short trapezoid を含む same-vowel 連音がより連続的に見える
- Preview / export は同じ semantics を維持する
- `timeline` canonical / `observations` 正本の原則を崩さない

---

## 13. 要約

MS11-9E は、
**MS11-9D-6 後にも残っている same-vowel burst の不自然さを、
最小差分で追加緩和する refinement step**
として扱う。

初回推奨方針は次のとおり。

- 対象は residual same-vowel burst に限定する
- same-vowel floor 値は据え置き、まず配分ロジックを見直す
- observation bool は増やさず、既存 burst candidate を再利用する
- writer / Preview 共通 helper の refinement を主対象にする
