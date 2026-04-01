# MS11-9F-3 Implementation Plan

## Cross-vowel residual wide right-gap refinement

## 0. 位置づけ

MS11-9F-3 は、`MS11-9F` と `MS11-9F-2` の後に残った
**residual cross-vowel 7 件**
を対象にした追加プランである。

ここまでで確認できていること:

- `MS11-9F` で overlap 起因の取りこぼしをかなり削減した
- `MS11-9F-2` で moderate right-gap residual を追加救済した
- `sample_input2` では `residual_cross = 23 -> 10 -> 7`
- 実出力は
  - `9n` が `MS11-9F`
  - `9m` が `MS11-9F-2`
  に一致している

したがって、F-3 の主題は
**既に効いている transition family をさらに少し延長するか、ここで floor 系へ切り替えるか**
を見極める段階にある。

---

## 1. 現在の残件

`sample_input2` 再観測で残っている residual は次の 7 件である。

- `idx 6`
- `idx 122`
- `idx 123`
- `idx 172`
- `idx 193`
- `idx 229`
- `idx 230`

このうち性質は 2 群に分かれている。

### 1-1. 軽度 left/right gap 混在

- `idx 6`

特徴:

- left 側も少し離れている
- right 側だけの問題とは言い切れない

### 1-2. wide right-gap 系

- `idx 122`, `123`
- `idx 172`
- `idx 193`
- `idx 229`, `230`

特徴:

- `gap_gt_2_right` が大きい
- 中には `right_gap_initial` まで大きいものがある
- F-2 の moderate 緩和では届かない

---

## 2. 現在の解釈

F-2 では、
**moderate right-gap residual を transition family 延長として扱う**
ことで、追加 candidate が実出力差分に届くことを確認した。

一方、今回残っている 7 件は、

- moderate の延長で無理に拾うと過剰救済になりやすい
- ただし speech-internal に見える箇所もまだ残る

という、より境界的なケースである。

そのため F-3 では、
**transition の単純延長を続けるより、残件の種類を分けて扱う**
のが自然である。

---

## 3. 問題整理

### 3.1 現時点のボトルネック

残件の主問題は次のいずれかである。

1. next 側 start が本当に遠く、transition として扱うには距離が大きすぎる
2. 実際は 2-event zero-run span として見た方が自然だが、現行 family に届いていない
3. speech-internal というより pause 寄りで、救済対象から外すべき

### 3.2 今回の中心論点

F-3 の中心論点は、
**残件をすべて transition へ押し込まない**
ことである。

ここで無理に transition 上限をさらに広げると、
silence 寄り case まで巻き込むリスクが上がる。

---

## 4. 目的

MS11-9F-3 の目的は次のとおり。

- 残件 7 件を性質別に切り分ける
- transition 延長で扱うべきものと、そうでないものを分離する
- 必要なら既存 `cross_vowel_floor` family へ届かせる
- 契約混雑を増やさずに進める

---

## 5. スコープ

### 5-1. 含める対象

- residual 7 件の分類見直し
- `pipeline` 側の helper 追加または条件分岐見直し
- 必要最小限の `cross_vowel_floor` 再利用検討
- テスト追加

### 5-2. 含めない対象

- writer 新 family の追加
- GUI parameter 追加
- observation bool の恒久増設
- same-vowel 系の再調整
- top-end shaping 調整

---

## 6. 取りうる方針

### 案A. transition をさらに wide right-gap へ広げる

利点:

- 実装は比較的単純

懸念:

- silence 寄り case を巻き込みやすい
- ここまでの「限定緩和」方針から外れやすい

### 案B. wide right-gap 系の一部を `cross_vowel_floor` へ寄せる

利点:

- full closure 残存への対処としては理屈が通りやすい
- transition より穏やかな救済にできる可能性がある

懸念:

- 現時点で `cross_floor = 0` なので、入口条件の設計が必要

### 案C. residual を 2 群に分ける

- moderate 寄りは transition
- wide right-gap / zero-run 寄りは floor
- pause 寄りは非救済

利点:

- 現実の残件構造に合っている
- 過剰救済を抑えやすい

懸念:

- helper 分岐はやや増える

---

## 7. 推奨方針

MS11-9F-3 初回は、
**案C を推奨**する。

推奨内容:

- residual 7 件を `transition 延長候補 / floor 候補 / 非救済候補` に分ける
- 初回は `cross_vowel_floor` へ届くべき wide right-gap / zero-run 寄り case を 1〜2 パターン固定する
- 新 bool は増やさず、helper 内局所判定で進める

理由:

- F-2 までで transition 延長はすでに十分試せている
- ここから先は family を分けた方が論理がきれい
- `MS11-9F` の当初目的であった continuity-floor family 活用にも戻れる

---

## 8. 具体候補

### 8-1. floor 候補として見直したい対象

有力候補:

- `idx 122/123`
- `idx 229/230`

理由:

- 2-event 的に見た方が自然
- `right_gap_initial` は比較的小さく見える箇所がある
- transition より floor の方が説明しやすい

### 8-2. 追加観測したい対象

- `idx 172`
- `idx 193`

理由:

- right-gap がかなり大きい
- speech-internal なのか pause 寄りなのかの境界を見たい

### 8-3. 非救済の可能性がある対象

- `idx 6`

理由:

- left/right ともに綺麗な continuity とは言いにくい
- 無理に救うと副作用が出やすい

---

## 9. 実装フェーズ

## Phase 1. residual 7 件の再分類

作業:

- 7 件を `transition / floor / non-target` に仮分類する
- 特に `122/123`, `229/230` を floor 候補として固定する

完了条件:

- F-3 の主対象が明文化される

現在地メモ:

- 完了
- residual 7 件は
  - `floor 候補`: `122/123`, `229/230`
  - `追加観測候補`: `172`, `193`
  - `境界 case`: `6`
  として整理済み

## Phase 2. floor 候補の入口条件を最小追加

作業:

- wide right-gap だが speech-internal に見える case を
  `cross_vowel_floor` へ届かせる補助判定を追加する

完了条件:

- `cross_floor` が 0 から増える

現在地メモ:

- 実装済み
- `pipeline` に wide right-gap / 2-event zero-run 寄り case を
  `cross_vowel_floor` へ寄せる residual helper を追加
- `tests/test_pipeline_peak_values.py` に
  `test_observation_marks_cross_vowel_wide_two_event_right_gap_span_as_floor_candidate`
  を追加して通過確認済み
- `sample_input2` 再観測では
  - `cross_transition = 17`
  - `cross_floor = 4`
  - `residual_cross = 3`
  となり、F-2 時点の `7件` からさらに減少した
- floor 化できた実データ span は
  - `122/123`
  - `229/230`
  で確認済み
- 残件は
  - `6`
  - `172`
  - `193`
  に縮小した

## Phase 3. 実出力確認

作業:

- `sample_input2` 再生成
- `9m` との差分確認

完了条件:

- F-3 の新規差分が実出力へ届く

現在地メモ:

- ローカル再生成で [dist/_tmp_ms11_9f3_sample_input2_upper1.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9f3_sample_input2_upper1.vmd)
  を出力済み
- これは [Test11_9m.vmd](d:/Visual Works/Kanna Work/Voice/Test11_9m.vmd) とは不一致
- SHA256:
  - `_tmp_ms11_9f3_sample_input2_upper1.vmd`: `FBCAD01E1CEC3881564B96549F68437CFBFED59929A8A83E0C7B2BFE0D70383F`
  - `Test11_9m.vmd`: `CF21D0473A47E06B3BD09BE9FAEF79FA2690A6F4680056A01CDF6E49DD83713C`
- したがって、F-3 の floor 候補追加も実出力差分へ到達している
- ただし、ユーザー側再生成 VMD との一致確認と見た目評価は未実施

## Phase 4. regression 確認

作業:

- same-vowel
- closing 系
- Preview / export 整合

を確認する

完了条件:

- 対象外 family を壊していない

現在地メモ:

- `tests/test_pipeline_peak_values.py`: `29 passed`
- `tests/test_vmd_writer_intervals.py`, `tests/test_preview_transform.py`, `tests/test_pipeline_and_vmd.py`: `61 passed`
- pytest cache の `PytestCacheWarning` は継続しているが、テスト自体は通過

---

## 10. ユーザー判断が必要な点

### Q1. F-3 初回は transition 延長より floor 候補の整理を優先するか

- 推奨案: **はい**
- 理由:
  - F-2 までで transition 延長は一段効いている
  - 残件は family を分けて見た方が自然

### Q2. 初回は residual 7 件のうち `122/123` と `229/230` を主対象にするか

- 推奨案: **はい**
- 理由:
  - 2-event 的で floor 候補として最も扱いやすい

### Q3. 初回は `idx 6` を救済対象に含めず、境界 case として保留するか

- 推奨案: **はい**
- 理由:
  - 無理に救済すると副作用リスクが高い

---

## 11. 内容検証メモ

このプランが現状と矛盾していないかの検証結果は次のとおり。

- `9m` は `MS11-9F-2` のローカル再生成と一致している
- F-2 で `transition` は `17` まで増え、ここまでは実出力差分へ届いている
- 残件は `7` で、transition 延長だけで無理に取り切る段階ではなくなっている
- `MS11-9F` 本来の課題文言には `cross_vowel_floor` family 活用の余地があり、F-3 でそこへ戻るのは自然
- 新 bool を増やさず helper 内判定で進める方針は、契約整理メモとも矛盾しない

現時点では、
**この F-3 プランに大きな論理矛盾は見当たらない**
と判断できる。

---

## 12. 要約

MS11-9F-3 は、
**残り 7 件を transition 延長だけで押し切らず、
wide right-gap / zero-run 寄り case を `cross_vowel_floor` 候補として再整理する**
ためのプランである。
