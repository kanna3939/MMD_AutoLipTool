# MS11-9FIX1 Implementation Plan

## 0. 文書目的

MS11-9FIX1 は、
**`開口保持 (closing_hold_frames)` が final closing 専用ではなく通常母音 shape にも適用されてしまう不具合**
を修正するための計画書である。

本タスクは新機能追加ではなく、
**MS11-9C で意図していた適用範囲へ semantics を戻す不具合修正**
として扱う。

---

## 1. 現象

実 GUI 観測では、次の症状が確認されている。

- `開口保持 = 0` / `閉口スムーズ = 0` のときは、通常の母音開口幅で表示される
- `開口保持 >= 1` にすると、speech-internal な母音でも top 幅や終端形状が変わる
- 結果として、Preview 上で母音開口の幅が狭まったように見える
- Preview だけでなく writer/export も同じ helper を使っているため、根本原因は Preview 単独ではない

---

## 2. 確認済み原因

### 2.1 writer 側

`src/vmd_writer/writer.py` では、
各 interval / grouped event に対して `closing_hold_frames` がそのまま流され、
`_apply_closing_hold_to_trapezoid_spec()` と
`_apply_closing_hold_to_multi_point_envelope_spec()` が無条件で適用されている。

この helper は `closing_start_frame=spec.peak_end_frame` を起点に
top 終端を後ろへ動かすため、
本来 final closing だけに使うべき hold が
speech-internal な通常母音 shape にも掛かっている。

### 2.2 Preview 側

`src/gui/preview_transform.py` でも、
writer と同じ hold helper を各 preview segment に適用しているため、
GUI 上の見え方も同じ誤った semantics を再現している。

### 2.3 テスト側

既存テストには、
単発 interval や peak fallback に対して `closing_hold_frames` が直接効くことを
前提にしたケースが存在する。

そのため現状は、
**誤った適用範囲がテストで固定されている**
状態とみなせる。

---

## 3. あるべき仕様

MS11-9FIX1 では、`closing_hold_frames` の意味を次へ戻す。

- `closing_hold_frames` は **final closing 専用**
- speech-internal な通常母音 shape には適用しない
- `closing_softness_frames` も同様に、final closing 系にのみ効く前提を維持するかは別途確認対象だが、
  初回 FIX では少なくとも `closing_hold_frames` の適用範囲を正す
- Preview / export は同一 semantics を維持する

---

## 4. 目的

MS11-9FIX1 の目的は次のとおり。

- `開口保持` によって speech-internal な母音開口幅が変形しないようにする
- `closing_hold_frames` を final closing にのみ適用する
- Preview / export の整合を維持したまま直す
- 誤った前提で固定されている既存テストを正しい仕様へ更新する

---

## 5. 主対象

- `src/vmd_writer/writer.py`
- `src/gui/preview_transform.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_preview_transform.py`

必要なら次も確認対象とする。

- `tests/test_main_window_closing_softness.py`
- `tests/test_pipeline_and_vmd.py`

---

## 6. 非対象

- same-vowel / cross-vowel / zero-run / burst / top-end shaping の再調整
- RMS 系ロジック
- GUI 入力部品の追加変更
- `closing_hold_frames` の値そのものの見直し
- MS12 系タスク

---

## 7. 修正方針

### 7.1 初回方針

初回 FIX では、
**hold 適用箇所を final closing だけに限定する**
ことに絞る。

具体的には、

- 通常 interval の trapezoid / fallback / multi-point envelope には
  `closing_hold_frames` を直接適用しない
- final closing を構成する明示的な closing tail に対してのみ hold を適用する
- Preview も同じ境界で揃える

### 7.2 重要な考え方

今回の問題は「hold 値が強すぎる」ではなく、
**適用範囲が誤っている**
ことにある。

そのため、初回はパラメータ調整ではなく
**適用条件の修正**
を優先する。

---

## 8. 実装フェーズ

## Phase 1. 現仕様固定テストの見直し

作業:

- 既存の `closing_hold_frames` テストのうち、
  通常母音 shape に hold が掛かることを前提にしているケースを洗い出す
- 「最終閉口のみ hold が掛かる」仕様へ期待値を置き換える方針を決める

完了条件:

- 誤仕様を固定しているテストが明確になる

## Phase 2. writer 側の適用範囲修正

作業:

- `closing_hold_frames` を通常 shape へ直接適用している経路を外す
- final closing 系のみに限定する

完了条件:

- `開口保持 >= 1` でも speech-internal な母音開口幅が変形しない

## Phase 3. Preview 整合修正

作業:

- Preview でも writer と同じ境界で hold を適用する

完了条件:

- Preview / export の semantics が一致する

## Phase 4. regression 確認

作業:

- final closing hold がまだ正しく効くか確認する
- closing softness / same-vowel / cross-vowel 系に副作用がないか確認する

完了条件:

- MS11-9C の本来意図を維持しつつ、不具合だけを除去できる

---

## 9. 想定テスト観点

- `closing_hold_frames=0` と `>0` で、通常母音 shape の幅が変わらない
- final closing に対しては hold が引き続き有効
- Preview でも同じ変化だけが見える
- `closing_softness_frames` 単独ケースを壊さない
- same-vowel / cross-vowel の speech-internal bridge 系を壊さない

---

## 10. ユーザー判断が必要な点

### Q1. 初回 FIX は `closing_hold_frames` の適用範囲修正だけに絞るか

- 推奨案: **はい**
- 理由:
  - 現象の主因は適用範囲の誤りであり、ここを直せば最小差分で問題を潰せる

### Q2. `closing_softness_frames` も同時に final closing 限定へ戻すか

- 推奨案: **いいえ（初回は保留）**
- 理由:
  - 今回ユーザーが検知した直接原因は `開口保持`
  - `closing_softness_frames` まで同時に触ると差分範囲が広がる

### Q3. 既存テストの期待値変更を伴っても、正しい仕様へ揃えるか

- 推奨案: **はい**
- 理由:
  - 現在の一部テストは誤仕様を固定している可能性が高い

---

## 11. 内容検証メモ

現時点で、この FIX プランに大きな論理矛盾は見当たらない。

- ユーザー観測と Preview 表示が一致している
- Preview と writer が同じ helper を使っているため、片側だけの問題ではない
- `closing_hold_frames` は MS11-9C 文脈では final closing のための parameter であり、
  speech-internal な通常母音へ掛かるのは意図とズレている
- 不具合の本体は値調整ではなく適用範囲である

したがって、
**MS11-9FIX1 を「開口保持の適用範囲を final closing に戻す修正」として切ることは妥当**
と判断できる。

---

## 12. 要約

MS11-9FIX1 は、
**`closing_hold_frames` が通常母音 shape に掛かってしまう不具合を修正し、final closing 専用 parameter としての意味へ戻す**
ための修正プランである。
