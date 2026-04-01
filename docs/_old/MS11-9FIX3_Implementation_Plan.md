# MS11-9FIX3 Implementation Plan

## 目的

MS11-9FIX1 / FIX2 で `closing_hold_frames` / `closing_softness_frames` の適用範囲を
「後続 shape が無い場合のみ有効」に絞った結果、
実質的に発話全体の最後の closing でしか効かなくなった。

本 FIX では、この gating を撤回し、
**各 shape が持つ closing tail に対して hold / softness を適用しつつ、
後続 shape 前では clamp する**
という元の intended semantics に戻す。

## 問題整理

- 現状の `_resolve_effective_final_closing_hold_frames(...)` /
  `_resolve_effective_final_closing_softness_frames(...)` は、
  `next_shape_start_frame is not None` のとき 0 を返している
- しかし writer / Preview にはもともと
  `next_shape_start_frame` を使って tail を clamp する仕組みがある
- そのため gating と clamp が二重化し、結果として GUI parameter がほぼ死んでいる

## 修正方針

1. hold / softness の effective helper から
   `next_shape_start_frame is not None -> 0` の gating を外す
2. 後続 shape 前での制限は
   `_resolve_closing_tail_frames(...)` 側の clamp に一元化する
3. writer / Preview の期待値テストを、
   FIX1/FIX2 以前の intended semantics に合わせて戻す

## 対象

- `src/vmd_writer/writer.py`
- `src/gui/preview_transform.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_preview_transform.py`

## 完了条件

- `closing_hold_frames` / `closing_softness_frames` が
  再び shape-local closing tail に効く
- 後続 shape がある場合でも、後続開始前で clamp される
- Preview と export の挙動が一致する
