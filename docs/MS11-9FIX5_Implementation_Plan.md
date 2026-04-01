# MS11-9FIX5 Implementation Plan

## 目的

`closing_hold_frames` または `closing_softness_frames` が 1 以上のとき、
各 shape の後半スロープが一律に短くなる不具合を修正する。

## 原因

`_resolve_closing_tail_frames(...)` が hold / softness 適用時に
`original_end_frame` までの元の fall 長を保持せず、
`closing_start_frame` 基準の短い tail を再構成している。

そのため、

- `softness=1` で `zero 到達` が 1 frame 早まる
- `hold>=1` でも hold 後の fall 長が短縮される

という現象が起きる。

## 修正方針

1. `original_end_frame - closing_start_frame` を
   **元の fall 長** として保持する
2. hold を入れても、この元の fall 長は縮めない
3. softness は元の fall 長に対する **追加延長** として扱う
4. clamp は従来どおり `next_shape_start_frame - 1` を上限にする

## 対象

- `src/vmd_writer/writer.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_preview_transform.py`

## 完了条件

- `hold` または `softness` が 1 以上でも後半スロープが短くならない
- Preview / export で同じ tail 長が見える
- 既存 clamp 系の安全性を壊さない
