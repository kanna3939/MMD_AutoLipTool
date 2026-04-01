# MS11-9FIX7 Implementation Plan

## 目的

- `closing_hold_frames` / `closing_softness_frames` の smoothing 処理を、
  場当たりの family 別実装から整理し直す。
- `legacy_triangle / legacy_symmetric_trapezoid / ms11_2_asymmetric_trapezoid / peak_fallback / multi-point`
  の間で意味がずれないよう、**共通の tail post-process 契約**を定義する。
- Preview と export の両方で、同じ smoothing semantics を安定して再現できる状態へ戻す。

## 現在の問題整理

### 1. smoothing の契約が family ごとに分裂している

- `peak_fallback` は frame 列を直接組み立てる。
- `trapezoid` は spec を持ち、hold / midpoint / end を再構成している。
- `multi-point` は control point の末尾だけを差し替えている。

このため、同じ `closing_hold_frames=1` / `closing_softness_frames=1` でも、
family によって

- 3 点目を動かす
- hold 点を追加する
- midpoint を 3 点目直後に置く
- midpoint を tail 中央に置く

が混在している。

加えて、現行コードでは `closing_hold_frames` / `closing_softness_frames` の有効範囲を調整する
`_resolve_effective_final_closing_hold_frames(...)` /
`_resolve_effective_final_closing_softness_frames(...)`
が実質 no-op であり、`next_shape_start_frame` を見ていない。
そのため smoothing の適用可否は family ごとの downstream helper に分散している。

### 2. trapezoid 系が最も不安定

- `legacy_triangle` は `peak_start_frame == peak_end_frame` のため、
  Preview 側で top を二重描画しやすかった。
- `ms11_2_asymmetric_trapezoid` は `peak_end_value` を保持する必要があるため、
  3 点目を動かすか残すかで見た目が大きく変わる。
- `legacy_symmetric_trapezoid` は短い fall を持つため、
  hold / midpoint を押し込むだけで shape が崩れやすい。

### 3. 最終 VMD 正規化は主犯ではない

- 代表ケースの確認では、raw 生成フレームと
  `_apply_final_morph_frame_normalization(...)` 後のフレームは一致した。
- したがって「1 フレーム短縮」は、最終の VMD 正規化や zero pruning ではなく、
  `_build_interval_morph_frames_with_normalization_metadata(...)` の時点で
  既に入っている。
- FIX7 の主対象は `write_morph_vmd(...)` の後段ではなく、
  shape family ごとの raw frame 生成経路である。

### 4. 現行 FIX 群は局所改善の積み上げになっている

- `peak_end_value` 保持
- final closing 限定の試行
- tail 長保持の試行
- trapezoid への hold 点追加

などを段階的に入れてきたが、family ごとの契約差が残ったままのため、
局所修正が別経路で再発要因になっている。

### 5. 既存テストは現行の分裂契約を固定している

- `tests/test_vmd_writer_intervals.py`
- `tests/test_preview_transform.py`

には、family ごとに異なる hold / softness の効き方を期待しているケースが残っている。
そのため FIX7 はコード修正だけでなく、**テスト契約の整理**を同時に行う必要がある。

## FIX7 の基本方針

### 方針A: smoothing は shape 生成の後段で一元化する

- まず各 family は **base shape** を決めるだけにする。
- smoothing はその後、共通の tail post-process として適用する。
- これにより「family ごとに hold / softness の意味が違う」状態をなくす。

### 方針B: smoothing 対象は末尾 tail のみ

- smoothing が触ってよいのは、各 shape の
  - 最後の non-zero point
  - 最後の zero point
  のみとする。
- `peak_start_frame` や `peak_end_frame` の意味は変えない。
- `peak_end_value` は smoothing で破壊しない。

### 方針C: hold と softness を役割分担する

- `closing_hold_frames`
  - 最後の non-zero point の後ろへ plateau を追加する
- `closing_softness_frames`
  - 最後の non-zero point と end-zero の間に slope midpoint を追加する
- 両方同時のときは
  - hold を先に解決
  - その後 hold 後 tail に softness を適用

### 方針D: 延長できないときは「壊さない」を優先する

- 後続 shape が近く、追加点を安全に置けない場合は、
  - tail を短縮して押し込むのではなく
  - 置ける範囲だけ置く
  - 置けない点は作らない
- 元の tail を短くする実装は避ける。

### 方針E: final-normalization 層は原則触らない

- FIX7 の目的は tail smoothing 契約の統一であり、
  `_apply_final_morph_frame_normalization(...)` のルール追加ではない。
- final-normalization 側の変更は、共通 tail post-process 導入後にも
  なお症状が残る場合だけ別論点として扱う。

## 実装イメージ

### Phase 1. 共通 tail モデルを定義する

- writer 内部で、family 非依存の tail 断面を扱う軽量構造を定義する。
- 想定メンバー:
  - `tail_anchor_frame`
  - `tail_anchor_value`
  - `tail_end_frame`
  - `tail_end_value`
  - `max_end_frame`
  - `base_tail_span`

※ これは dataclass でも tuple helper でもよいが、最初は writer ローカル helper で十分。  
※ `base_tail_span` は「0 設定時の tail 長」を保持するために必要。

### Phase 2. 各 family から共通 tail へ変換する

- `peak_fallback`
  - top -> end_zero を tail として切り出す
- `legacy_triangle`
  - 単一 top -> end_zero を tail として切り出す
- `legacy_symmetric_trapezoid`
  - 3 点目 -> end_zero を tail として切り出す
- `ms11_2_asymmetric_trapezoid`
  - `peak_end_frame / peak_end_value` -> end_zero を tail として切り出す
- `multi-point`
  - 最終 non-zero control point -> 最終 zero point を tail として切り出す

### Phase 3. 共通 smoothing helper を適用する

- 入力:
  - tail 定義
  - `closing_hold_frames`
  - `closing_softness_frames`
  - `next_shape_start_frame`
- 出力:
  - hold point の追加有無
  - midpoint の追加有無
  - end_zero の延長先

この helper は、

- 既存 tail を短縮しない
- 安全に置けない点は追加しない
- midpoint は `tail_anchor_frame` 直後を第一候補とし、
  置けない場合だけ後退させる
- `max_end_frame` を超えない範囲で hold / softness を部分適用する

を保証する。

### Phase 4. family へ戻して frame/control point を生成する

- `trapezoid` では base の 3 点目を残し、追加点だけを後段に足す
- `multi-point` では末尾だけ差し替える
- `peak_fallback` でも同じ tail helper を使う
- Preview は writer と同じ post-process 結果を描画する

### Phase 5. テスト契約を共通 tail semantics へ載せ替える

- family ごとの差ではなく、
  - 0 設定時の tail が保持されること
  - hold は tail の短縮を起こさないこと
  - softness は末尾 slope の追加だけを行うこと
  - hold + softness の併用でも 3 点目 / last non-zero が移動しないこと
  を共通観点として再定義する。

## Preview 側の明示ルール

- `legacy_triangle` で `peak_start_frame == peak_end_frame` の場合、
  top 点は 1 つだけ描画する。
- `hold` / `slope_mid` は、writer 側の post-process 結果そのままを描く。
- Preview 独自の補正は追加しない。
- なお、top 二重描画の局所修正は既に入っているため、
  FIX7 本体の主対象は preview polygon ではなく writer の raw frame 契約である。

## テスト方針

### 固定すべき代表ケース

1. `legacy_triangle`
   - hold=0, softness=0
   - hold=1
   - softness=1

2. `legacy_symmetric_trapezoid`
   - hold=0, softness=0
   - hold=1
   - softness=1

3. `ms11_2_asymmetric_trapezoid`
   - decayed `peak_end_value` あり
   - hold=1
   - softness=1

4. `peak_fallback`
   - 単発
   - 後続 shape が近いケース

5. `multi-point`
   - hold=1
   - softness=1

### 回帰観点

- `hold / softness >= 1` で 3 点目が消えたり移動したりしない
- 元の tail が 1 フレーム短縮しない
- `legacy_triangle` に top の二重描画が出ない
- Preview / writer の frame 列が整合する
- raw 生成フレームと final-normalization 後フレームの差が
  smoothing バグの主因になっていないことを確認する

## 実装順の提案

1. writer で共通 tail helper を導入する
2. `trapezoid` を新 helper に載せ替える
3. `peak_fallback` を新 helper に載せ替える
4. `multi-point` を新 helper に揃える
5. Preview を writer の最終 shape へ合わせる
6. family 別テストを共通 tail 契約ベースへ更新する

## 今回まだ行わないこと

- 既存 FIX 群のドキュメント同期
- VMD 実データ再比較
- final-normalization 層の仕様変更

## このプランのゴール

- smoothing を「family ごとに別物」ではなく「末尾 tail の共通後処理」として定義し直す。
- 次の実装で、raw frame 生成時点の再発原因を追いやすい構造へ戻す。

---

## 実装反映メモ（2026-04-02）

今回の FIX7 では、`writer / preview / tests` をまとめて更新し、
closing smoothing を **family 非依存の tail 後処理** へ寄せた。

### 反映したこと

- `src/vmd_writer/writer.py`
  - `_resolve_closing_tail_frames(...)` を、元 tail の内部を作り直す方式から、
    **元の end-zero 以降にだけ hold / softness を追加する** 方式へ変更した
  - `peak_fallback / trapezoid / multi-point` は同じ tail 解決 helper を共有する形へ整理した
- `src/gui/preview_transform.py`
  - writer 側 post-process 結果をそのまま描画する方針を維持し、
    FIX7 後の frame 列と整合するようにした
- `tests/test_vmd_writer_intervals.py`
  - family 別の旧局所仕様ではなく、
    「元 tail を短縮しない」「末尾に点を追加する」観点へ期待値を更新した
- `tests/test_preview_transform.py`
  - Preview も writer と同じ共通 tail semantics を前提に期待値を更新した

### repo 内確認

- `PYTHONPATH=src;tests`
  `.\.venv\Scripts\python.exe -m pytest tests\test_vmd_writer_intervals.py tests\test_preview_transform.py tests\test_pipeline_and_vmd.py tests\test_main_window_closing_softness.py -q`
  で `78 passed`

### 実出力確認

- `Test11_9S1.vmd` と `Test11_9S2.vmd` の比較では、
  `開口維持=1` により **既存 tail が短縮されるのではなく、末尾に non-zero / zero が追加される** ことを確認した
- `Test11_9S3.vmd` でも、
  `閉口スムーズ=1` は **末尾へ slope を追加する** 作用として出ており、
  一括短縮には戻っていない
- `Test11_9S4.vmd` でも、
  `開口維持=2 + 閉口スムーズ=2` は **hold + slope の段階的 tail 追加** として出ており、
  旧不具合だった「全音の後半スロープが一律 1 フレーム短くなる」形は確認されなかった

### 現在地

- FIX7 により、closing smoothing の主因だった family 別 tail 契約の不一致は
  少なくとも実出力 VMD 差分上では抑制できている
- 今後の確認対象は「短縮再発の有無」より、
  `開口維持` / `閉口スムーズ` の **効き方の自然さ** と
  `final closing` 文脈での体感評価へ移る
