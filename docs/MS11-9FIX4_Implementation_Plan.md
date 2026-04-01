# MS11-9FIX4 Implementation Plan

## 目的

`closing_hold_frames` または `closing_softness_frames` を適用したときに、
MS11-2 asymmetric trapezoid の `peak_end_value` が `peak_value` へ丸められ、
いわゆる「3点目問題」が再発する不具合を修正する。

## 原因

- `_apply_closing_hold_to_trapezoid_spec()`
- `_apply_closing_softness_to_trapezoid_spec()`

の両方で、hold / softness 適用後に `AsymmetricTrapezoidSpec` を再構成する際、
`peak_end_value=spec.peak_value` としている。

このため、観測由来の減衰済み `peak_end_value` が失われ、
3 点目が常に peak 値と同一になってしまう。

## 修正方針

1. hold / softness 適用後も `peak_end_value` を保持する
2. `closing_mid_value` は `peak_value` ではなく、
   hold 後の最後の non-zero 値を基準に決める
3. Preview も writer spec を再利用しているため、
   writer 修正 + Preview 回帰テストで整合を確認する

## 対象

- `src/vmd_writer/writer.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_preview_transform.py`

## 完了条件

- `closing_hold_frames > 0` でも台形 3 点目が一律 peak 値にならない
- `closing_softness_frames > 0` でも 70% midpoint が decayed peak-end を基準にする
- Preview / export の差異が出ない
