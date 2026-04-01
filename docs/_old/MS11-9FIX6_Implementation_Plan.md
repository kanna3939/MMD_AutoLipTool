# MS11-9FIX6 Implementation Plan

## 背景

- `MS11-9FIX5` までで `peak_end_value` の破壊と tail 長の一律短縮は一部改善した。
- ただし、後続 shape が近いケースでは `closing_hold_frames` または `closing_softness_frames` を有効にした瞬間、
  元の closing tail を保ったまま延長できないにもかかわらず、shape を再構成してしまう経路が残っていた。
- その結果、Preview / VMD の両方で「後半スロープが 1 フレーム短く見える」症状が発生していた。

## 原因

- smoothing の契約が shape family ごとに揃っていなかった。
- `multi-point envelope` は「既存 tail を残しつつ末尾に hold / slope_mid を追加する」方式だった一方、
  `AsymmetricTrapezoidSpec` は `peak_end_frame` 自体を動かして closing tail を作り直していた。
- そのため、`closing_hold_frames >= 1` または `closing_softness_frames >= 1` で、
  特に trapezoid 系の 3 点目が右へ移動し、見た目上「後半スロープが一律 1 フレーム短くなる」症状が起きていた。
- `_resolve_closing_tail_frames(...)` の clamp / extension 解決もこの差異を助長していた。

## 修正方針

1. `trapezoid` 側も `multi-point` と同じく、**既存 tail を保持して追加点を足す**方式へ揃える。
2. `hold / softness` は、元の 3 点目を動かさず、`closing_hold_frame` / `closing_mid_frame` を後段に追加する。
3. clamp は extension 可能量の範囲内で解決し、元の tail を短縮しない。
4. Preview / writer で同じ spec を共有し、export と表示の semantics を揃える。

## 実装対象

- `src/vmd_writer/writer.py`
  - `AsymmetricTrapezoidSpec` に closing hold 用 field を追加
  - `_resolve_closing_tail_frames(...)` の clamp / extension 解決ロジック修正
  - trapezoid hold / softness を「既存点移動」から「追加点方式」へ変更
- `src/gui/preview_transform.py`
  - trapezoid preview に hold point 表示を追加
- `tests/test_vmd_writer_intervals.py`
  - trapezoid / fallback / mixed case の新 smoothing 契約へ期待値更新
- `tests/test_preview_transform.py`
  - Preview 側の hold / slope_mid 表示と frame 配置を同契約へ更新

## 完了条件

- `closing_hold_frames >= 1` または `closing_softness_frames >= 1` でも、
  後続 shape が近いだけで元の fall が短縮しない。
- 孤立 shape では従来どおり hold / softness が効く。
- `writer / preview / pipeline_and_vmd / main_window_closing_softness` の関連テストが通る。
