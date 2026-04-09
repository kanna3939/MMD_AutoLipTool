# MS11-9 Observation / Handoff Contract Memo

## 0. 文書目的

本メモは、MS11-9 系で増えてきた

- `pipeline` の observation 判定
- `writer` の shape 生成
- `preview` の表示再現
- GUI / export handoff

の責務と契約を、**全面リファクタ前の整理メモ**として可視化するためのひな型である。

目的は次の 3 点。

- 残課題を解決しながらも、契約の混雑を見失わないようにする
- same-vowel / cross-vowel / zero-run / burst / floor の責務境界を明示する
- 次段の最小実装時に「どこを直すべきか」を判断しやすくする

本書は設計正本ではなく、
**現状把握・差分整理・次段判断のための補助文書**
として扱う。

---

## 1. 現在の前提

### 1.1 壊さない前提

- `timeline` は canonical writer input のまま維持する
- candidate / span / continuity 判定の正本は `observations` 側に置く
- Preview 独自近似を増やさず、writer helper 再利用を優先する
- final closing 系と speech-internal continuity 系を混ぜない

### 1.2 このメモで見たいこと

- どの判定が `pipeline` で確定しているか
- どの解釈が `writer` に委ねられているか
- どの情報が GUI / Preview / export に handoff されるか
- どこに契約の混雑や重複があるか

---

## 2. レイヤ別責務

### 2.1 pipeline

主責務:

- [ ] initial timeline の構築
- [ ] RMS による interval refinement
- [ ] peak value 評価
- [ ] observation 構築
- [ ] same-vowel / cross-vowel / zero-run / burst / floor candidate 判定

現状メモ:

- `build_vowel_timing_plan(...)` が入口となり、初期 timeline 構築、RMS による interval refinement、peak value 評価、observation 構築までを担う
- same-vowel 系では、`_annotate_micro_gap_bridge_candidates(...)` が
  - zero-run span candidate
  - same-vowel burst span candidate
  を observation へ注入する
- MS11-9E-3 以降、same-vowel-like zero/low-energy case では refined interval をそのまま見るのではなく、candidate 判定専用の representative span を内部 helper で解釈している
- 現時点の役割は「shape を決めること」ではなく、「writer が continuity として扱ってよい候補を observation 契約へ落とすこと」である

未確認事項:

- cross-vowel family と same-vowel family で representative span 的な補助解釈を今後そろえるべきかは未確定
- `reason` と candidate 種別の関係を observation field へ明示的に昇格させるべきかは未確定

### 2.2 writer

主責務:

- [ ] observation-aware な grouping 入力の再構成
- [ ] same-vowel / cross-vowel continuity の shape 化
- [ ] top-end / valley / floor / bridge の値配分
- [ ] morph frame 列の正規化

現状メモ:

- `observations` を受け取ったうえで、grouping 前の points を observation-aware に再構成する
- same-vowel 系では、
  - `_collect_same_vowel_burst_spans(...)`
  - `_build_same_vowel_span_adjusted_points(...)`
  - `_build_same_vowel_span_synthetic_points(...)`
  が中核である
- MS11-9E-4 以降、single-event same-vowel zero/low-energy span に対しても synthetic bridge point を生成し、shape 差分へ変換できるようになった
- writer の主責務は「candidate をそのまま採用すること」ではなく、「candidate を最終 shape family に翻訳すること」である
- FIX7 以降、closing smoothing は family ごとに別 helper で意味を変えるのではなく、
  末尾 tail の共通後処理として扱う方向へ整理した

未確認事項:

- single-event same-vowel synthetic bridge の値配分が実データ上で十分自然かは継続確認が必要
- same-vowel multi-event と single-event を今後どこまで共通 rule に寄せるかは未確定

### 2.3 preview

主責務:

- [ ] writer と同じ semantics の表示
- [ ] control point / polygon の再現

現状メモ:

- Preview は writer helper を再利用しており、same-vowel / cross-vowel の shape semantics を独自再設計していない
- same-vowel span 調整も writer helper の結果に追随する形で表示される
- 現時点では「表示の独自最適化」より「export との一致」が優先されている
- FIX7 以降、closing smoothing でも writer の post-process 結果に追随し、
  Preview 独自補正を増やさない方針をより明示的にした

未確認事項:

- MMD 上の見え方と Preview の体感差を今後どこまで縮める必要があるかは未確定

### 2.4 GUI / export handoff

主責務:

- [ ] current parameter の保持
- [ ] timing plan / observations / GUI 値の preview 反映
- [ ] export 時の同値 handoff

現状メモ:

- GUI は current timing plan と current parameter を保持し、Preview / export の双方へ同じ値を handoff する
- current upper limit、closing hold、closing softness は Preview と export で同一路線の handoff になっている
- same-vowel 系の改善は GUI 追加ではなく、既存 handoff の先で pipeline / writer が解釈する構造を維持している

未確認事項:

- same-vowel / cross-vowel 系の将来的な GUI 調整項目を持つかどうかは未確定

---

## 3. Observation 契約一覧

### 3.1 現在使っている主要 field

- `reason`
- `peak_value`
- `previous_non_zero_event_index`
- `next_non_zero_event_index`
- `span_start_index`
- `span_end_index`
- `is_bridgeable_same_vowel_micro_gap_candidate`
- `is_same_vowel_burst_candidate`
- `is_bridgeable_cross_vowel_transition_candidate`
- `is_cross_vowel_zero_run_continuity_floor_candidate`
- `bridge_candidate_reason`

### 3.2 field ごとの責務

| field | 決定レイヤ | 主用途 | 主要消費先 | 備考 |
|---|---|---|---|---|
| `reason` | pipeline | zero/low-energy の由来分類 | pipeline candidate helper, 調査メモ | `no_peak_in_window` / `below_rel_threshold` などの基礎情報 |
| `peak_value` | pipeline | morph 値の基礎、zero 判定 | writer, preview, candidate helper | 0 か low-positive かで same-vowel burst 判定が分かれる |
| `previous_non_zero_event_index` | pipeline | 前側 continuity 接続先 | writer same-vowel helper, cross-vowel helper | writer 側の bridge 構築に直接使う |
| `next_non_zero_event_index` | pipeline | 後側 continuity 接続先 | writer same-vowel helper, cross-vowel helper | 前項と対で使う |
| `span_start_index` | pipeline | candidate span 範囲 | writer same-vowel helper, preview | zero-run と burst の span 境界を共有する |
| `span_end_index` | pipeline | candidate span 範囲 | writer same-vowel helper, preview | 同上 |
| `is_bridgeable_same_vowel_micro_gap_candidate` | pipeline | same-vowel zero-run continuity 候補 | writer same-vowel helper, preview | `is_bridgeable_micro_gap_candidate` と実質同系統 |
| `is_same_vowel_burst_candidate` | pipeline | same-vowel low-positive / zero 混在 continuity 候補 | writer same-vowel helper, preview | same-vowel burst span として収集される |
| `is_bridgeable_cross_vowel_transition_candidate` | pipeline | cross-vowel transition 候補 | writer cross-vowel interval 調整, preview | same-vowel とは別 family |
| `is_cross_vowel_zero_run_continuity_floor_candidate` | pipeline | cross-vowel zero-run floor 候補 | writer continuity-floor 補助 | zero-run 全救済ではない |
| `bridge_candidate_reason` | pipeline | candidate の由来ラベル | 調査, ログ的確認, writer の一部判断補助 | same_vowel_burst などの二次ラベルを含む |

---

## 4. ルール別整理

### 4.1 same-vowel

pipeline で確定すること:

- zero/low-energy / low-positive event が same-vowel continuity 候補に入るか
- candidate span の境界
- previous / next non-zero event の接続先
- same-vowel micro-gap candidate と same-vowel burst candidate のどちらへ寄せるか
- MS11-9E-3 以降は representative span による candidate 判定

writer で解釈すること:

- candidate span を grouping 入力へどう翻訳するか
- zero-run / low-positive / single-event / multi-event の各 case で synthetic bridge を置くか
- continuity peak / floor / valley をどう配分するか
- 最終 morph frame 列でどの程度 continuity に見せるか

Preview で再利用すること:

- writer helper の same-vowel span 調整結果
- synthetic bridge を含む control point 列
- shape_kind と control point 表示

混雑点:

- `is_bridgeable_same_vowel_micro_gap_candidate` と `is_same_vowel_burst_candidate` の境界が helper 実装に依存しやすい
- same-vowel candidate 判定と writer-side synthetic bridge policy が別レイヤに分かれており、片方だけ直しても出力差分にならないことがある
- single-event / multi-event の扱い差が暗黙仕様になりやすい

### 4.2 cross-vowel

pipeline で確定すること:

- `is_bridgeable_cross_vowel_transition_candidate`
- `is_cross_vowel_zero_run_continuity_floor_candidate`
- `span_start_index / span_end_index`
- `previous_non_zero_event_index / next_non_zero_event_index`
- representative span による transition / floor family の入口判定
- F / F-2 / F-3 を通じた residual helper による限定的な追加分類

writer で解釈すること:

- transition candidate を前後 interval 調整へ変換すること
- floor candidate を continuity-floor 補助 shape へ変換すること
- candidate 自体を増やすのではなく、pipeline から来た family を既存 shape へ翻訳すること

Preview で再利用すること:

- writer helper の cross-vowel transition 適用結果
- floor candidate が writer で shape 化された結果
- export と同じ cross-vowel semantics

混雑点:

- representative span と residual helper の役割分担が helper 内に寄っている
- `transition` と `floor` の境界が bool ではなく局所判定の積み上げで決まる
- F-2 までは transition 延長、F-3 では floor 側再利用と、同じ残課題でも family が分かれる
- F-4 では `172/193` を非対象候補、`6` を境界 case として閉じる判断が入り、「何を救済しないか」の基準も契約の一部になった

### 4.3 zero-run / floor

pipeline で確定すること:

- zero-run span の境界
- same-vowel / cross-vowel の分岐
- `cross_vowel_floor` へ届く residual helper の入口条件
- F-3 時点では `122/123`, `229/230` を floor 候補として拾えること

writer で解釈すること:

- `is_cross_vowel_zero_run_continuity_floor_candidate` を continuity-floor shape へ変換すること
- floor candidate の span を既存 shape family に翻訳すること

Preview で再利用すること:

- writer helper 再利用による floor candidate の表示
- export と同じ floor semantics

混雑点:

- floor residual helper は transition residual helper と隣接しており、family 境界が helper 内局所判定に依存する
- F-4 で「floor にも transition にも入れないものを非対象とする」基準が新たに見えた

### 4.4 top-end shaping

pipeline で確定すること:

- `PeakValueObservation` の `rms_window_times_sec / rms_window_values`
- `local_peak` に対して top-end の正規化元になる RMS 窓情報を保持すること
- top-end candidate family 自体は追加せず、既存 observation 契約で writer へ渡すこと

writer で解釈すること:

- `peak_end_frame` 以降のどの RMS を主値として採用するか
- 必要なら直後 1 点を補助参照し、`peak_end_value` を局所安定化すること
- flat-top を少し下げつつ、急減衰を少し和らげる値配分を family 非依存で決めること

Preview で再利用すること:

- writer と同じ `peak_end_value` 解決 helper を再利用すること
- trapezoid / multipoint の top-end semantics を export と一致させること

混雑点:

- top-end の責務は observation field 追加なしで解ける一方、writer helper 側の暗黙仕様として蓄積しやすい
- same-vowel / cross-vowel と違い candidate family を増やさないため、値配分変更の意図が文書なしでは追いにくい
- 「差分が出たか」と「MMD 上で自然に見えるか」が別段階である点を見失いやすい

---

## 5. 契約の混雑ポイント

### 5.1 現在の混雑

- [ ] same-vowel candidate と burst candidate の境界
- [ ] zero-run と cross-vowel floor の境界
- [ ] interval refinement と candidate 判定の基準面の違い
- [ ] observation field と helper 内局所計算の責務分散
- [ ] writer helper 側に寄った暗黙仕様
- [ ] closing smoothing の tail 契約が family 非依存で維持できているか

現状メモ:

- 現時点で最も混雑しているのは same-vowel family である
- E2/E3 では pipeline 側の candidate 判定、E4 では writer 側の shape 変換と、ボトルネックが段階的に異なる場所へ現れた
- つまり「candidate が立つか」「shape 差分になるか」「実見た目が自然か」が別問題として存在している
- cross-vowel でも F / F-2 / F-3 を通じて residual helper が増えたが、observation field 追加は避けている
- その代わり helper 内局所判定の比重が上がっており、`transition / floor / non-target` の境界整理が次の設計論点になっている
- closing smoothing では FIX7 により raw frame 生成段階の共通 tail 契約を導入したため、
  今後は family 別例外より tail post-process の一貫性を優先して追う

### 5.2 まだ許容できる混雑

- Preview が writer helper 再利用を維持している点
- observation field を増やさず helper 内局所計算で進めている点
- same-vowel と cross-vowel の family をまだ分けて扱っている点

### 5.3 次に整理対象へ昇格しそうな混雑

- same-vowel と cross-vowel で candidate helper の考え方が乖離し始めること
- writer helper 側に same-vowel 専用暗黙仕様が蓄積すること
- `bridge_candidate_reason` と bool 群の責務が重なり始めること
- cross-vowel residual を `transition` と `floor` のどちらで扱うかが helper 追加のたびに局所化すること

---

## 6. 変更判断メモ

### 6.1 pipeline で直すべき症状

- candidate が立たない
- interval / span 解釈が実データに届かない
- same-vowel / cross-vowel 判定境界が不自然

補足:

- E2/E3 で見えたように、実データで same-vowel continuity に見えるのに candidate が立たない症状は pipeline を見るべきである
- cross-vowel residual zero-peak case も次段では主に pipeline 側から入る可能性が高い

### 6.2 writer で直すべき症状

- candidate は立つが shape 差分にならない
- valley / bridge / top-end の配分が不自然
- single-event / multi-event の扱い差で出力が消える

補足:

- E4 で確認したように、candidate が立っても single-event span policy によって shape 差分が消える症状は writer を見るべきである
- top-end / valley / bridge の値配分も writer で判断される
- G で見えたように、candidate family を増やさず `peak_end_value` の取り方だけで見た目が変わる症状も writer を見るべきである

### 6.3 Preview / handoff で直すべき症状

- export との差分
- GUI 値と preview のずれ
- helper 再利用漏れ

補足:

- 現時点では Preview / export の semantics 一致は比較的保たれている
- 今後の主対象は GUI 追加よりも downstream shape の自然さ確認になる見込み

---

## 7. 次段候補メモ

### 候補A

- テーマ: cross-vowel residual zero-peak / full closure の追加分類
- 主対象レイヤ: pipeline
- 最小差分: cross-vowel same-family の candidate helper 追加または floor candidate 条件の補強
- 想定テスト: `test_pipeline_peak_values.py`, `test_vmd_writer_intervals.py`, 実データ VMD 比較
- リスク: zero-peak 全救済へ広がると副作用が大きい

現在地メモ:

- F / F-2 / F-3 により、cross-vowel residual は `23 -> 10 -> 7 -> 3` まで圧縮した
- `9n`, `9m`, `9o` がそれぞれ F / F-2 / F-3 のローカル再生成と一致しており、実出力差分まで確認済み
- F-4 により「残件 3 件を救済対象に含めるかの最終整理」まで完了し、cross-vowel はいったん閉じたテーマとして扱える

### 候補B

- テーマ: same-vowel single-event synthetic bridge の値配分微調整
- 主対象レイヤ: writer
- 最小差分: floor / ratio / bridge time の微調整
- 想定テスト: same-vowel writer / preview shape tests, 実データ `9k -> 9l` 差分観察
- リスク: 効きすぎると不自然な開口維持になる

### 候補C

- テーマ: observation / handoff 契約の補助 dataclass 化または整理メモの正式化
- 主対象レイヤ: 設計整理
- 最小差分: field 一覧と helper 責務の固定、必要なら read-only 補助 dataclass
- 想定テスト: コード変更を伴うなら最小の import / handoff 回帰
- リスク: 先に大きくやりすぎると残課題解消の速度が落ちる

### 候補D

- テーマ: top-end shaping の見え方評価と必要時の微調整
- 主対象レイヤ: writer
- 最小差分: `peak_end_value` 解決 helper の係数調整、または共通 top-end rule の微修正
- 想定テスト: `test_vmd_writer_intervals.py`, `test_preview_transform.py`, 実データ `9o -> 9p` 比較
- リスク: 数値調整だけで形が変わるため、体感評価なしで詰めると過剰補正になりやすい

現在地メモ:

- MS11-9G で `peak_end_value` の 1 点依存を和らげる writer-side refinement を追加済み
- `Test11_9p.vmd` が MS11-9G のローカル再生成結果と一致しており、top-end 値配分変更は実 export へ届いている
- MMD 側確認まで完了したため、現時点では保留テーマとして扱える
- 再開する場合も、新 family 追加ではなく writer-side 微調整から始めるのが自然である

### 候補E

- テーマ: closing smoothing の自然さ確認と必要時の微調整
- 主対象レイヤ: writer / preview
- 最小差分: 共通 tail post-process の係数や追加点配置の軽微調整
- 想定テスト: `test_vmd_writer_intervals.py`, `test_preview_transform.py`, 実データ `S1 -> S2 -> S3 -> S4` 比較
- リスク: 契約再分裂を避けるため、family 別例外を増やしすぎないことが重要

現在地メモ:

- FIX7 により、`開口維持` / `閉口スムーズ` の旧不具合だった tail 短縮は実出力 VMD 差分上では再現していない
- `Test11_9S2.vmd`, `Test11_9S3.vmd`, `Test11_9S4.vmd` の比較では、いずれも短縮ではなく末尾追加として出ている
- 次段は「壊れているか」ではなく、「効き方が自然か」を評価する段階とみなせる

---

## 8. ユーザー確認が必要になりやすい点

以下は、整理を進める中で必要になりやすい確認事項のひな型である。

### Q1. 契約整理の優先対象は same-vowel / cross-vowel のどちらか

- 推奨案: same-vowel
- 理由: 直近の E2〜E4 の流れでボトルネックがかなり見えており、整理内容を具体化しやすい

### Q2. observation field を増やす前に helper 内整理を優先するか

- 推奨案: はい
- 理由: 現時点では field 増殖よりも helper の責務可視化で十分追跡可能だから

### Q3. 契約整理と残課題解消を並走させるか、先に整理だけ固めるか

- 推奨案: 並走
- 理由: 今回の same-vowel 系のように、実際の残課題追跡が最も契約整理の材料になるから

---

## 9. 更新ログ

 - 2026-04-01:
  - 初版ひな型を追加
 - same-vowel 優先で、pipeline / writer / preview / handoff の現状メモを初回記入
- 2026-04-01:
  - cross-vowel F / F-2 / F-3 / F-4 の整理を反映
  - top-end shaping の契約メモを追記し、MS11-9G と `Test11_9p.vmd` 一致確認までを現在地へ反映
- 2026-04-01:
  - MS11-9G を MMD 側確認込みで一旦クローズ扱いとし、top-end shaping を保留テーマへ移行
- 2026-04-02:
  - MS11-9FIX7 の closing smoothing tail-contract 整理を反映
  - `Test11_9S2.vmd` / `Test11_9S3.vmd` / `Test11_9S4.vmd` 比較により、tail 短縮ではなく末尾追加として出ている現在地を追記
