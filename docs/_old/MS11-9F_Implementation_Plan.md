# MS11-9F Implementation Plan

## Cross-vowel residual zero-peak / full closure refinement

## 0. 位置づけ

MS11-9F は、`docs/MS11-9_Remaining_Issues.md` の
**「cross-vowel でも発話中の完全閉口が残る箇所がある」**
に対する実装前プランである。

same-vowel 系は MS11-9E〜E-4 により、

- candidate が立たない
- writer に届かない
- 実データ VMD に差分が出ない

という段階を越え、少なくとも実出力へ反映するところまで到達した。

一方、cross-vowel 側は現時点で

- transition candidate
- zero-run continuity-floor candidate

までの family はあるが、
**speech-internal なのに classification に乗らず full closure が残る residual case**
が課題として残っている。

MS11-9F では、この residual case を
**zero-peak 全救済には広げず、cross-vowel continuity を期待したい case だけ追加分類する**
ことを主目的とする。

---

## 1. 背景

現行 cross-vowel 系は、概ね次の family に分かれている。

- `cross_vowel_transition`
  - 単発 zero gap を最小 overlap で橋渡しする
- `cross_vowel_floor`
  - zero-run span に continuity floor を与える

これにより、cross-vowel の基本ケースはある程度緩和されている。

しかし残課題として、次のような case が残る。

- speech-internal に見える
- 前後は cross-vowel continuity を期待したい
- しかし `below_rel_threshold / no_peak_in_window` の落ち方や span 条件の都合で
  transition / floor のどちらにも入らない
- 結果として full closure がそのまま残る

つまり current policy は安全側だが、
**cross-vowel residual case の取りこぼし**
が構造上残っている。

---

## 2. 確認できている前提

少なくとも現在の repo では、次が確認済みである。

- `pipeline` は cross-vowel transition と cross-vowel zero-run floor を observation へ載せられる
- `writer` は
  - transition candidate なら前後 interval 調整
  - floor candidate なら continuity-floor 補助
  を行える
- Preview は writer helper 再利用で cross-vowel semantics に追随する
- same-vowel 側で見えた主問題は一段落しており、cross-vowel を次段主題にしやすい

一方で、未確認または未解決の点は次のとおり。

- residual cross-vowel full closure が、主に pipeline classification 起因なのか
  writer-side floor policy 起因なのかは、まだ確定していない
- zero-peak residual case に対して、新しい classification を増やすべきか、
  既存 `cross_vowel_floor` の条件補強で足りるかは未確定である

Phase 1 観測メモ:

- `sample_input2` 観測では、cross-vowel residual zero-peak / full closure 候補として少なくとも `23件` の flagged case が見つかった
- 現時点の aggregate fail reason は主に次のとおりである
  - `overlap_left`
  - `gap_gt_2`
  - `overlap_right`
- same-vowel 側のような「candidate 自体が立たない」だけではなく、
  cross-vowel 側では `speech-internal` に見えるのに overlap / gap 条件で既存 family に乗らない case が多い
- 代表例としては `idx 67, 93, 97, 104, 118, 166, 214` などがあり、
  いずれも `below_rel_threshold` を伴う residual speech-internal case として観測されている

---

## 3. 問題整理

### 3.1 現在の不足

現行 cross-vowel 系で不足している可能性が高いのは、次のいずれかである。

1. `pipeline` が residual cross-vowel zero-peak case を candidate 化できていない
2. candidate 化はされているが、writer の continuity-floor が十分弱く、見た目上 full closure に見える
3. span / interval 解釈が current rule と合っておらず、speech-internal case が silence 寄りに扱われている

### 3.2 今回の主仮説

初回仮説としては、
**主ボトルネックは pipeline classification の取りこぼし**
に置くのが自然である。

理由:

- same-vowel 側でも、まず「candidate が立たない」ことがボトルネックになった
- cross-vowel 残課題文言も「候補 classification に乗らない case が残る」と整理されている
- writer には既存 transition / floor family がすでに存在する

---

## 4. 目的

MS11-9F の目的は次のとおり。

- speech-internal cross-vowel residual zero-peak / full closure case を最小範囲で追加分類する
- 既存 transition / continuity-floor の downstream 実装を再利用する
- zero-peak 全救済には広げない
- Preview / export の semantics 一致を維持する

---

## 5. スコープ

### 5-1. 含める対象

- cross-vowel residual zero-peak case の再分類
- pipeline candidate 条件の最小補強
- 必要最小限の writer / Preview handoff 確認
- テスト追加

### 5-2. 含めない対象

- same-vowel family の再調整
- top-end shaping の再設計
- threshold 値の全面見直し
- GUI parameter 追加
- observation-layer の全面再編

---

## 6. 非目標

- `peak_value == 0.0` の cross-vowel case を全面救済すること
- silence / pause 系と speech-internal continuity 系を統合すること
- same-vowel と cross-vowel を同一 rule へまとめること
- writer family を大きく増やすこと

---

## 7. 取りうる方針

### 案A. 既存 `cross_vowel_floor` の candidate 条件を補強する

- 既存 zero-run continuity-floor family に乗る条件を少し広げる
- 新しい bool は増やさず、既存 family の入力条件を実データに届く範囲で補強する

利点:

- downstream を再利用しやすい
- 差分が小さい

懸念:

- どこまで広げると副作用が出るかの線引きが難しい

### 案B. residual cross-vowel speech-internal case を別 classification として切り出す

- `cross_vowel_floor` とは別に、
  residual full closure 専用の candidate family を追加する

利点:

- 責務が明確になる
- 実データで何を拾いたいかを切り出しやすい

懸念:

- observation bool / helper が増える
- 契約の混雑が進みやすい

### 案C. writer 側 floor 値配分だけを増強する

- classification は現状維持し、
  既存 floor candidate の見た目だけを強くする

利点:

- 実装点が少ない

懸念:

- candidate に乗らない residual case は解決できない
- 今回の残課題文言とは少しずれる

---

## 8. 初回推奨方針

MS11-9F 初回は、
**案A を優先し、案B は必要になったときだけ導入する**
のが推奨である。

推奨内容:

- まず residual case を `cross_vowel_floor` family へ乗せる条件補強を検討する
- 既存 writer / Preview downstream を使って、最小差分で実データへ届くか確認する
- 条件補強だけで表現しきれない場合に限り、別 classification を検討する

理由:

- same-vowel 側でも、まずは既存 family を downstream 再利用する方が安全だった
- cross-vowel 側で先に bool を増やすと、契約整理の負債が増えやすい

---

## 9. 具体的な見直し候補

### 9-1. speech-internal cross-vowel residual case の最小再現固定

作業:

- 実データ上で full closure に見える cross-vowel case を 1〜2 箇所特定する
- 可能なら observation 集計で
- `reason`
- 前後 non-zero event
- span 幅
- floor candidate 落ち理由
  を固定する

現時点での固定候補:

- `idx 67`: `overlap_left + overlap_right + gap_gt_2`
- `idx 93`: `overlap_left + overlap_right`
- `idx 97`: `overlap_left + overlap_right`
- `idx 104`: `overlap_left + overlap_right + gap_gt_2`
- `idx 118`: `overlap_left + overlap_right`

### 9-2. `cross_vowel_floor` 入力条件の補強

候補:

- zero-run span の幅条件の見直し
- overlap / gap の許容条件見直し
- speech-internal と見なせる前後関係の補助判定追加

初回で特に有力な論点:

- same-vowel のように representative span を導入すべきか
- それとも cross-vowel では overlap / gap 許容の見直しだけで足りるか
- `cross_vowel_floor` と `cross_vowel_transition` の境界をどこまで共有するか

注意:

- same-vowel と違い、cross-vowel は vowels が異なること自体が前提なので、
  “連続性があるから救う” の定義を明確にする必要がある

### 9-3. writer 側はまず既存 floor family を再利用

初回では、
writer に新しい shape family を足すよりも、
既存 continuity-floor が residual case に届くかを先に見る。

---

## 10. 責務分割

### 10-1. pipeline

主責務:

- residual cross-vowel zero-peak case を candidate 化する
- existing `cross_vowel_floor` または `cross_vowel_transition` family に橋渡しする

初回方針:

- 主変更点は pipeline
- field 追加は後回し
- helper 内局所判定を優先

### 10-2. writer

主責務:

- pipeline から来た cross-vowel candidate を既存 continuity-floor / transition shape に変換する

初回方針:

- まずは downstream 再利用
- writer 側の新 family 追加は後回し

### 10-3. Preview

主責務:

- writer と同じ cross-vowel semantics を表示する

初回方針:

- helper 再利用継続
- Preview 固有ロジックは増やさない

---

## 11. 実装フェーズ

## Phase 1. residual cross-vowel case の固定

作業:

- 実データで full closure に見える cross-vowel case を固定する
- `test_pipeline_peak_values.py` に再現ケースを追加できる形へ落とす

完了条件:

- 「今は落ちるが拾いたい cross-vowel case」が明文化される

現在地メモ:

- 完了
- `sample_input2` 観測で residual cross-vowel zero-peak / full closure 候補を少なくとも `23件` 固定済み
- 主な落ち理由は
  - `overlap_left`
  - `gap_gt_2`
  - `overlap_right`
- 固定代表 index:
  - `67`
  - `93`
  - `97`
  - `104`
  - `118`

## Phase 2. pipeline candidate 条件の最小補強

作業:

- 既存 `cross_vowel_floor` family へ乗せる条件を補強する
- 必要なら helper を追加する

完了条件:

- 少なくとも一部の residual cross-vowel case が candidate 化される

現在地メモ:

- 実装済み
- `pipeline` に cross-vowel representative span helper を追加し、
  long zero interval / short zero-run span を既存 `cross_vowel_transition` / `cross_vowel_floor`
  family へ届きやすくした
- `tests/test_pipeline_peak_values.py` に次を追加して通過確認済み
  - `test_observation_marks_cross_vowel_long_zero_interval_as_transition_candidate_via_representative_span`
  - `test_observation_marks_cross_vowel_long_two_zero_span_as_floor_candidate_via_representative_span`
- `sample_input2` 再観測では
  - `cross_transition = 14`
  - `cross_floor = 0`
  - `residual_cross = 10`
  となり、Phase 1 の `23件` から residual が減少した
- 現時点で残る主因は、ほぼ `gap_gt_2_right` に寄っている
  - 一部 `gap_gt_2_left` も残る
  - overlap 起因は大きく減った

## Phase 3. writer / Preview handoff 確認

作業:

- 新しく立った candidate が既存 continuity-floor shape へ届くか確認する
- Preview と export の一致を確認する

完了条件:

- VMD / Preview に差分が出る

現在地メモ:

- ローカル再生成では [dist/_tmp_ms11_9f_sample_input2.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9f_sample_input2.vmd)
  が出力され、[Test11_9l.vmd](d:/Visual Works/Kanna Work/Voice/Test11_9l.vmd) とは不一致を確認した
- SHA256:
  - `_tmp_ms11_9f_sample_input2.vmd`: `6DA8BCF55339F6DE7AD6F1D32BFB823253A4622618FB5E6AF91D064159561AFD`
  - `Test11_9l.vmd`: `81CE16E7D4C97F4DBC4C0DE5B881F1B1C7DC9829E384C7B31D2ADFC704EC6219`
- したがって、MS11-9F の classification 補強は少なくとも export VMD 差分まで到達している
- ただし、ユーザー側再生成 VMD との一致確認と、見た目上の改善確認は未実施

## Phase 4. regression 確認

作業:

- same-vowel family への副作用確認
- closing 系への副作用確認

完了条件:

- 対象外 family を壊していない

現在地メモ:

- `tests/test_pipeline_peak_values.py`: `26 passed`
- `tests/test_vmd_writer_intervals.py`, `tests/test_preview_transform.py`, `tests/test_pipeline_and_vmd.py`: `61 passed`
- pytest cache の `PytestCacheWarning` は継続しているが、テスト自体は通過

---

## 12. 最低限のテスト観点

### 12-1. pipeline

- residual cross-vowel zero-peak case が candidate 化される
- same-vowel case は巻き込まれない
- silence 寄り case は引き続き除外される

### 12-2. writer

- 新しく立った cross-vowel residual case が continuity-floor shape へ届く
- full closure が緩和される

### 12-3. Preview

- Preview / export が一致する

---

## 13. ユーザー判断が必要な点

現時点では、実装前に固定しておくと安全な点は次の 3 つである。

### Q1. 初回は既存 `cross_vowel_floor` family の条件補強を優先するか

- 推奨案: **はい**
- 理由:
  - downstream 再利用ができる
  - 差分が小さい
  - 契約混雑を抑えやすい

### Q2. 初回は新しい observation bool を増やさず進めるか

- 推奨案: **はい**
- 理由:
  - same-vowel 側と同様に、まず helper 内整理で十分かを見たい
  - observation 契約の混雑を抑えられる

### Q3. 初回は floor 値そのものを触らず、まず classification 側を優先するか

- 推奨案: **はい**
- 理由:
  - 残課題の主文は「候補に乗らない case が残る」であり、先に分類側を見る方が筋が通る

---

## 14. スコープ外

- same-vowel family の再設計
- top-end shaping の再調整
- threshold 値の全面再確定
- observation dataclass の全面再編
- MS12

---

## 15. 到達イメージ

MS11-9F 完了時の到達イメージは次のとおり。

- speech-internal cross-vowel residual zero-peak / full closure case が、最低限 continuity-floor family に届く
- same-vowel 系で達成した「実出力に届く」状態を cross-vowel 側にも広げる
- Preview / export は同じ semantics を維持する

---

## 16. 要約

MS11-9F は、
**cross-vowel residual zero-peak / full closure case を、
zero-peak 全救済には広げず、既存 continuity-floor family へ最小追加分類する**
ための計画である。

初回推奨は次のとおり。

- まず residual case を固定する
- 既存 `cross_vowel_floor` family の入力条件補強を優先する
- observation bool は増やさず、pipeline helper 内整理で進める
- writer / Preview downstream は既存実装を再利用する
