# MS11-9E-2 Implementation Plan

## Same-vowel candidate classification minimum expansion

## 0. 位置づけ

MS11-9E-2 は、MS11-9E 実装後の確認で明らかになった
**「writer 側 smoothing に入る前に、same-vowel candidate 自体が立っていない」**
というボトルネックに対する、pipeline 側の最小拡張計画である。

本タスクは、same-vowel burst smoothing そのものを大きく変えるものではなく、
その前段にある candidate classification を
**実データに届く最小範囲だけ広げる**
ための refinement として扱う。

今回の観測で確認できた主な事実:

- same-vowel に見える `below_rel_threshold / no_peak_in_window` case は存在する
- しかし current rule では `same-vowel micro-gap candidate` が 0 件だった
- 主因は:
  - `span_gt_1`
  - `overlap_left`
  - `non_adjacent_prev / non_adjacent_next`
  に集中していた

したがって MS11-9E-2 では、
same-vowel candidate 判定のうち
**1 frame 限定 / strict adjacency / strict non-overlap**
を最小限だけ緩める。

---

## 1. 背景

現行の same-vowel candidate 判定は、
初期 MS11-9D の safety-first 方針を引き継いでおり、かなり保守的である。

少なくとも現在の条件は次に強く依存している。

- `previous_non_zero_event_index == index - 1`
- `next_non_zero_event_index == index + 1`
- current zero event / span が `1 frame` またはごく短いもの
- 前後 interval が実質 overlap しないこと

この方針は安全だが、実データでは次の問題を起こしている。

- same-vowel continuity に見える区間でも candidate へ乗らない
- 結果として writer 側の same-vowel smoothing が発火しない
- VMD 出力上は same-vowel 内の短い閉口感が残る

---

## 2. 目的

MS11-9E-2 の目的は次のとおり。

- 実データで same-vowel continuity に見える case を、candidate として最低限拾えるようにする
- ただし zero-peak 全救済には広げない
- `timeline` canonical / `observations` 正本の原則を維持する
- writer / Preview の semantics には最小 handoff のみでつなぐ

---

## 3. スコープ

### 3-1. 含める対象

- same-vowel candidate 判定条件の最小拡張
- `below_rel_threshold / no_peak_in_window` の same-vowel case の再分類
- same-vowel short span の許容幅見直し
- overlap / adjacency 条件の安全側緩和
- pipeline test の追加

### 3-2. 含めない対象

- cross-vowel candidate 再設計
- continuity-floor 条件の再設計
- writer shape family の全面再設計
- threshold 値の全面再調整
- GUI 追加

---

## 4. 非目標

- `peak_value == 0.0` の全面救済
- same-vowel と cross-vowel の候補ルール統合
- silence redesign
- `PeakValueObservation` の全面再編

---

## 5. 現在のボトルネック整理

今回の実データ観測では、
same-vowel に見える flagged case の aggregate fail reasons は概ね次の順だった。

- `span_gt_1`
- `overlap_left`
- `current_vowel_mismatch`
- `non_adjacent_prev / non_adjacent_next`
- `right_gap_gt_1`
- `left_gap_gt_1`

このうち、MS11-9E-2 で主に触るべきなのは次の 3 つである。

1. `span_gt_1`
2. `overlap_left`
3. `non_adjacent_prev / non_adjacent_next`

`current_vowel_mismatch` は same-vowel ではないので、初回では対象外とする。

---

## 6. 最小拡張案

MS11-9E-2 初回で有力な最小拡張案は次のとおり。

### 案A. same-vowel short span を `2 event / 2 frame` まで許容

- current same-vowel micro-gap candidate の `1 frame` 制限を、
  same-vowel に限って `2 event / 2 frame` まで拡張する
- 既存 zero-run span の枠組みに寄せる

利点:

- 既存 9D-3 と整合しやすい
- 実データの `span_gt_1` に直接効く

懸念:

- 単純に広げるだけでは overlap / adjacency でまだ落ちる

### 案B. same-vowel だけ `strict adjacency` を緩和する

- `previous_non_zero_event_index == index - 1`
- `next_non_zero_event_index == index + 1`

の完全一致をやめ、
span 全体の前後に same-vowel non-zero があることを優先する

利点:

- 実データの `39-40`, `75-76` のような non-adjacent case に効く

懸念:

- 緩めすぎると silence 寄り case を拾う危険がある

### 案C. same-vowel だけ軽微 overlap を許容する

- `current_start_frame < previous_end_frame`
- `next_start_frame < current_end_frame`

を即除外せず、
`1 frame 程度の overlap` は refined interval の揺れとして許容する

利点:

- 実データの `overlap_left` に直接効く

懸念:

- overlap 許容だけでは span 幅問題は解けない

---

## 7. 初回推奨方針

MS11-9E-2 初回は、
**案A + 案C を先に採用し、案B は必要最小限に留める**
のが推奨である。

推奨内容:

- same-vowel candidate の対象幅を `2 event / 2 frame` まで拡張
- same-vowel case に限り `1 frame` までの軽微 overlap を許容
- adjacency は完全撤廃せず、
  `same span の前後に same-vowel non-zero がある` 場合だけ補助的に緩和

理由:

- 差分を小さく保てる
- 実データで多かった `span_gt_1` と `overlap_left` に先に効く
- adjacency 全解放より副作用が読みやすい

---

## 8. 具体的な判定見直し案

### 8-1. same-vowel short span

現行:

- 実質 `1 frame` 前提

見直し案:

- same-vowel に限り `2 event / 2 frame` まで candidate 化対象に含める

### 8-2. overlap 許容

現行:

- current start/end が前後 non-zero interval と overlap した時点で除外寄り

見直し案:

- same-vowel case に限り
  - `prev_end - current_start <= 1 frame`
  - `current_end - next_start <= 1 frame`
  の範囲は refined interval の揺れとして許容

### 8-3. adjacency 条件

現行:

- `previous_non_zero_event_index == index - 1`
- `next_non_zero_event_index == index + 1`

見直し案:

- same-vowel short span では
  - span 前に same-vowel non-zero がある
  - span 後に same-vowel non-zero がある
  を primary にする
- ただし gap が広い case まで広げない

---

## 9. 責務分割

### 9-1. pipeline

主責務:

- same-vowel candidate 判定条件を最小拡張する
- 既存 `PeakValueObservation` の same-vowel 系 bool へ乗せる

初回方針:

- 新しい bool は増やさない方向を優先
- 既存
  - `is_bridgeable_same_vowel_micro_gap_candidate`
  - `is_same_vowel_burst_candidate`
  - `span_start_index / span_end_index`
  を活かす

### 9-2. writer

主責務:

- pipeline から candidate が来たとき、既存 same-vowel smoothing を適用する

初回方針:

- writer 側は極力変更しない
- まず pipeline 側で candidate が立つことを優先確認する

### 9-3. Preview

主責務:

- writer と同じ candidate の結果を表示する

初回方針:

- Preview 側は handoff 維持
- pipeline candidate が増えた結果が自然に反映されるかを見る

---

## 10. 実装フェーズ

## Phase 1. same-vowel candidate 落ちケースの最小再現固定

作業:

- 実データ観測で見つかった same-vowel-like case を 2〜3 件固定
- `tests/test_pipeline_peak_values.py` に再現ケースを追加する

完了条件:

- 「今は落ちるが、MS11-9E-2 では拾いたい」case がテストで表現される

## Phase 2. candidate 判定の最小緩和

作業:

- `2 event / 2 frame` 許容
- `1 frame` overlap 許容
- same-vowel span 前後の非厳密 adjacency を最小導入

完了条件:

- 少なくとも一部の実データ same-vowel-like case が candidate 化される

## Phase 3. writer / Preview handoff 確認

作業:

- 既存 writer / Preview が、新しく立った candidate をそのまま使えているか確認
- 必要なら regression test を追加

完了条件:

- VMD と Preview に差分が出る

---

## 11. 最低限のテスト観点

### 11-1. pipeline

- same-vowel `2 event / 2 frame` case が candidate 化される
- same-vowel で `1 frame` overlap を含む case が candidate 化される
- cross-vowel case は巻き込まれない
- gap が広い case は引き続き除外される

### 11-2. writer

- 新しく立った same-vowel candidate が既存 smoothing へつながる
- zero-peak 全救済には広がらない

### 11-3. Preview

- Preview と export の結果が一致する

---

## 12. ユーザー判断が必要な点

現時点では、実装開始に必須の判断は多くないが、
次の 2 点は先に固定しておくと安全である。

### Q1. same-vowel candidate の最大幅を `2 event / 2 frame` まで広げるか

- 推奨案: **はい**
- 理由:
  - 既存 zero-run span の安全幅と揃う
  - 実データで最も効きそうな最小拡張だから

### Q2. same-vowel case に限り `1 frame` の軽微 overlap を candidate 判定で許容するか

- 推奨案: **はい**
- 理由:
  - 今回の実データでは overlap 由来の取りこぼしが多い
  - 1 frame に限定すれば副作用を抑えやすい

---

## 13. スコープ外

- cross-vowel candidate 再設計
- threshold 値の再確定
- observation-layer の全面整理
- MS12

---

## 14. 到達イメージ

MS11-9E-2 完了時の到達イメージは次のとおり。

- 実データで same-vowel continuity に見える case が candidate として拾われる
- 既存 MS11-9E の smoothing が、初めて実データにも届く
- `9i.vmd` のようなケースでも、same-vowel 内の残存 burst に差分が出る可能性が生まれる

---

## 15. 要約

MS11-9E-2 は、
**same-vowel smoothing が効かない原因となっている pipeline candidate 判定の狭さを、
実データに届く最小範囲だけ広げる**
ための計画である。

初回推奨は次のとおり。

- same-vowel に限り `2 event / 2 frame` まで許容
- same-vowel に限り `1 frame` の軽微 overlap を許容
- adjacency は完全一致から少し緩めるが、全面解放はしない
- writer / Preview より先に pipeline candidate を立てることを主目標にする
