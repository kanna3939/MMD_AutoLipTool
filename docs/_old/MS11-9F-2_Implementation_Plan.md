# MS11-9F-2 Implementation Plan

## Cross-vowel residual right-gap refinement

## 0. 位置づけ

MS11-9F-2 は、`docs/MS11-9F_Implementation_Plan.md` の
Phase 2 実装後に残った
**`gap_gt_2_right` 優勢の residual cross-vowel zero-peak / full closure**
を対象にした追加プランである。

MS11-9F 本体では、

- cross-vowel representative span を導入した
- overlap 起因の取りこぼしをかなり削減した
- `sample_input2` で residual cross-vowel を `23件 -> 10件` まで減らした
- `9l -> 9n` の実出力差分が、実際に新規 cross-vowel transition candidate と対応することを確認した

ここまでで、
**「classification 変更が実出力に届く」**
ことは確認済みである。

一方で残った 10 件は、
主に `gap_gt_2_right` に偏っており、
現行 `cross_vowel_transition` の代表 span 解釈だけでは届いていない。

---

## 1. 背景

MS11-9F 後の実データ観測では、`sample_input2` において
cross-vowel candidate の現在地は次のとおりである。

- `cross_transition = 14`
- `cross_floor = 0`
- `residual_cross = 10`

残件の fail reason 集計では、主に次が出ている。

- `gap_gt_2_right`: 9 件
- `gap_gt_2_left`: 4 件

代表例:

- `idx 122`, `123`
- `idx 161`, `162`
- `idx 172`
- `idx 193`
- `idx 214`
- `idx 229`, `230`

これらは、

- `below_rel_threshold / no_peak_in_window`
- 前後 non-zero は cross-vowel
- overlap はかなり減っている
- ただし next 側 start との距離がまだ広い

という形で残っている。

---

## 2. 現在の解釈

今回の残件は、same-vowel のときの
「candidate が全く立たない」
とは少し性質が異なる。

cross-vowel では既に transition candidate が複数立っており、
`9l -> 9n` の差分とも対応している。

そのため、MS11-9F-2 の主題は
**cross-vowel classification 全体の作り直しではなく、right-gap 優勢ケースへの補助解釈追加**
と考えるのが自然である。

---

## 3. 問題整理

### 3.1 現在足りていないもの

現行 rule で届いていないのは、主に次のケースである。

- zero/low-energy event 自体は speech-internal に見える
- previous 側との関係は近い
- しかし next 側 start がやや離れており、
  representative span ベースでは `gap_gt_2_right` で落ちる

つまり、
**「left 側は continuity 寄りだが、right 側だけ少し遠い」**
case の扱いがまだ弱い。

### 3.2 現時点の主仮説

主仮説は次のとおり。

- 残件は完全な silence ではなく、speech-internal continuation に近い
- ただし current rule は right 側 gap を対称的に厳しく見すぎている
- 初回は新しい family を増やすより、
  **cross-vowel transition の right-gap 解釈を限定的に緩和する**
  方が安全

---

## 4. 目的

MS11-9F-2 の目的は次のとおり。

- residual `gap_gt_2_right` 優勢ケースを最小範囲で追加救済する
- 既存 `cross_vowel_transition` downstream を再利用する
- `cross_vowel_floor` family や writer 新規 shape を増やさずに進める
- same-vowel や closing 系への副作用を抑える

---

## 5. スコープ

### 5-1. 含める対象

- cross-vowel right-gap residual case の追加観測固定
- `pipeline` 上の candidate 条件の限定緩和
- `transition` family への最小追加分類
- テスト追加

### 5-2. 含めない対象

- floor 値そのものの再設計
- writer 新 family の追加
- GUI parameter 追加
- observation dataclass の field 追加
- top-end shaping の調整

---

## 6. 取りうる方針

### 案A. cross-vowel transition の right-gap 許容だけ限定緩和する

- `gap_gt_2_right` のみを少し広げる
- left 側や overlap 条件は現状維持に近く保つ

利点:

- 変更範囲が最も小さい
- 今回の残件分布に直接対応する

懸念:

- 非対称ルールになる
- 将来の理解負荷は少し上がる

### 案B. speech-internal continuation 補助判定を追加し、そのときだけ right-gap を緩和する

- `below_rel_threshold / no_peak_in_window`
- previous 側が十分近い
- next 側が少し遠い

という case を helper で補助判定し、
そのときだけ transition 候補に入れる。

利点:

- ただ gap を広げるより意図が明確
- silence 寄り case を巻き込みにくい

懸念:

- helper ロジックは少し増える
- 契約整理メモの更新が必要

### 案C. floor family へ無理に寄せる

- remaining residual を `cross_vowel_floor` 側へ寄せる

利点:

- full closure 抑制の意図には合う

懸念:

- 現時点で `sample_input2` は `cross_floor = 0`
- 実出力へ届いている差分は transition 側と対応しており、
  今回の残件も transition 延長として解く方が自然

---

## 7. 推奨方針

MS11-9F-2 初回は、
**案B を推奨し、案A を実装簡略化の fallback とする**
のが自然である。

推奨内容:

- 新 bool は増やさない
- helper 内で `right-gap residual cross-vowel transition` を補助判定する
- right-gap 緩和は speech-internal continuation に見える case へ限定する
- downstream は既存 `cross_vowel_transition` を再利用する

理由:

- 今回の残件は `gap_gt_2_right` に偏っている
- すでに transition family が実出力へ届くことは確認済み
- floor family を無理に増やすより、現在の差分ラインを延長する方が筋がよい

---

## 8. 具体的な見直し候補

### 8-1. residual right-gap case の固定

候補:

- `idx 122`, `123`
- `idx 161`, `162`
- `idx 172`
- `idx 193`
- `idx 214`
- `idx 229`, `230`

固定したい観測:

- `reason`
- previous / next non-zero event index
- representative span
- left / right gap
- transition に乗らない理由

### 8-2. right-gap 緩和 helper

初回候補:

- previous 側 gap が近い
- overlap が過大でない
- flagged event が short span に収まる
- `reason` が `below_rel_threshold` または `no_peak_in_window`

のとき、
`next_start - representative_end` の許容量だけ限定的に広げる。

### 8-3. 境界の考え方

初回は、

- `left 側は現行より広げない`
- `overlap は維持`
- `right-gap だけを限定緩和`

の方が安全である。

---

## 9. 責務分割

### 9-1. pipeline

主責務:

- residual right-gap case の補助分類
- existing `cross_vowel_transition` family への橋渡し

### 9-2. writer

主責務:

- 既存 transition shape をそのまま適用

### 9-3. Preview

主責務:

- writer helper 再利用により export と一致させる

---

## 10. 実装フェーズ

## Phase 1. right-gap residual case の再固定

作業:

- `sample_input2` の残件 10 件を right-gap 優勢 case として固定する
- うち 2〜3 ケースを再現テストへ落とせる形にする

完了条件:

- 「今は `gap_gt_2_right` で落ちるが拾いたい case」が明文化される

現在地メモ:

- 完了
- residual cross-vowel は `10件` 固定済み
- 主対象は
  - `idx 122`, `123`
  - `idx 161`, `162`
  - `idx 172`
  - `idx 193`
  - `idx 214`
  - `idx 229`, `230`


## Phase 2. transition candidate 補助判定の追加

作業:

- helper 内で speech-internal continuation 補助判定を追加する
- 必要最小限で right-gap 許容を緩和する

完了条件:

- residual right-gap case の一部が `cross_vowel_transition` へ入る

現在地メモ:

- 実装済み
- `pipeline` に moderate right-gap residual を `cross_vowel_transition` として扱う helper を追加
- `tests/test_pipeline_peak_values.py` に次を追加して通過確認済み
  - `test_observation_marks_cross_vowel_single_zero_span_with_moderate_right_gap_as_transition_candidate`
  - `test_observation_marks_cross_vowel_two_event_right_gap_residual_span_as_transition_candidate`
- `sample_input2` 再観測では
  - `cross_transition = 17`
  - `cross_floor = 0`
  - `residual_cross = 7`
  となり、MS11-9F 時点の `10件` からさらに減少した
- 今回の追加で拾えたのは、主に moderate right-gap の transition 延長ケース
- なお `idx 122/123`, `172`, `193`, `229/230` は引き続き residual として残っている

## Phase 3. 実出力確認

作業:

- `sample_input2` 再生成で差分を確認する
- `9n` 系との比較で新規差分帯を確認する

完了条件:

- 追加 candidate が VMD 差分へ届く

現在地メモ:

- ローカル再生成で [dist/_tmp_ms11_9f2_sample_input2_upper1.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9f2_sample_input2_upper1.vmd)
  を出力済み
- これは [Test11_9n.vmd](d:/Visual Works/Kanna Work/Voice/Test11_9n.vmd) とは不一致
- SHA256:
  - `_tmp_ms11_9f2_sample_input2_upper1.vmd`: `CF21D0473A47E06B3BD09BE9FAEF79FA2690A6F4680056A01CDF6E49DD83713C`
  - `Test11_9n.vmd`: `EB56E8EC7BB674EE27D51CB86F14CA3F485C32C0FC84905EEB521E0477CF243E`
- したがって、MS11-9F-2 の追加分類は少なくとも export VMD 差分へ届いている
- ただし、ユーザー側再生成 VMD との一致確認と見た目評価は未実施

## Phase 4. regression 確認

作業:

- same-vowel family
- closing 系
- Preview / export 整合

を確認する

完了条件:

- 対象外 family を壊していない

現在地メモ:

- `tests/test_pipeline_peak_values.py`: `28 passed`
- `tests/test_vmd_writer_intervals.py`, `tests/test_preview_transform.py`, `tests/test_pipeline_and_vmd.py`: `61 passed`
- pytest cache の `PytestCacheWarning` は継続しているが、テスト自体は通過

---

## 11. 最低限のテスト観点

### 11-1. pipeline

- right-gap residual cross-vowel case が transition candidate 化される
- left 側や overlap を広げすぎない
- same-vowel は巻き込まれない

### 11-2. writer

- 新しい candidate が既存 transition shape へ届く
- full closure が緩和される

### 11-3. Preview

- Preview / export が一致する

---

## 12. ユーザー判断が必要な点

### Q1. 初回は `cross_vowel_floor` ではなく `cross_vowel_transition` 延長として扱うか

- 推奨案: **はい**
- 理由:
  - `9l -> 9n` 差分は transition candidate と対応している
  - 現時点で `cross_floor = 0` のままであり、transition 側の延長が自然

### Q2. 初回は right-gap 緩和を speech-internal 補助判定つきに限定するか

- 推奨案: **はい**
- 理由:
  - 単純に gap 上限を広げるより、副作用を抑えやすい

### Q3. 初回は observation bool を増やさず進めるか

- 推奨案: **はい**
- 理由:
  - 現行契約の混雑をこれ以上増やさずに進められる

---

## 13. 内容検証メモ

このプランが現状と矛盾していないかの検証結果は次のとおり。

- `MS11-9F` 後の residual は `23件 -> 10件` で、残件主因が `gap_gt_2_right` に偏っている
- `9l -> 9n` の VMD 差分帯は、現行 `cross_vowel_transition` candidate と対応している
- `sample_input2` 再観測では `cross_floor = 0` のままであり、
  初回追加は floor family より transition family 延長の方が自然
- same-vowel と同じく、まず `pipeline` で候補化し downstream を再利用する流れは、
  直前の成功パターンと整合している
- 新 bool 追加や writer 新 family 追加を避ける方針は、
  `docs/MS11-9_Observation_Handoff_Contract_Memo.md` の契約整理方針とも矛盾しない

現時点では、
**このプランに大きな論理矛盾は見当たらない**
と判断できる。

---

## 14. 要約

MS11-9F-2 は、
**MS11-9F 後に残った `gap_gt_2_right` 優勢の residual cross-vowel case を、
既存 `cross_vowel_transition` family 延長として最小追加分類する**
ためのプランである。

初回推奨は次のとおり。

- right-gap residual case を固定する
- speech-internal 補助判定つきで right-gap を限定緩和する
- observation bool は増やさない
- downstream は既存 transition shape を再利用する
