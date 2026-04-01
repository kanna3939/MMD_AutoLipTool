# MS11-9G Implementation Plan

## Top-end shaping residual refinement

## 0. 位置づけ

MS11-9G は、`docs/MS11-9_Remaining_Issues.md` の
**「top-end shaping は改善したが、まだ flat-top / 急減衰が残る」**
に対する実装前プランである。

same-vowel / cross-vowel の speech-internal continuity 系は、
MS11-9E〜F-4 により、

- candidate が立たない
- writer に届かない
- 実出力へ反映されない

という段階をかなり越えた。

そのため次段の主題は、
**candidate 分類よりも、writer 側の top-end 値配分の自然さ**
へ移るのが自然である。

---

## 1. 背景

現行 top-end shaping は、概ね次の構造で動いている。

- `AsymmetricTrapezoidSpec` は `peak_start_frame` / `peak_end_frame` / `peak_end_value` を持つ
- `peak_end_value` は observation の `rms_window_times_sec / rms_window_values` を使って決める
- 現在は **`peak_end_frame` 以降で最初に取れる RMS を優先** する
- 取得した RMS を `local_peak` で正規化し、`peak_value` に掛け戻して decayed top-end を作る
- Preview は writer helper 再利用で同じ semantics を使う

この方式により、`peak_end_value` 未導入時より flat-top は減った。

一方で residual として、次が残る。

- `peak_end` が十分に下がらず flat-top に見える
- 逆に 3 点目だけ急に下がり、急減衰に見える
- RMS サンプル配置が sparse なとき、1 点依存の癖が強く出る

---

## 2. 現在の問題整理

### 2.1 既に解決できていること

- `peak_end_value` により、3 点目が 2 点目の単純コピーで固定されない
- writer / Preview の top-end semantics は一致している
- `pipeline` の observation 契約は、少なくとも top-end shaping に必要な RMS 窓情報を渡せている

### 2.2 まだ残っていること

- RMS 1 点選択が flat-top / 急減衰の両方を生みうる
- bridge / floor / transition が絡む shape で、top-end の減衰量が見た目に対して過敏または鈍感になることがある
- `peak_end_value` の算出方式は「現状妥当」だが、「最終仕様」としてはまだ固定し切れていない

### 2.3 今回の主仮説

主仮説は次のとおり。

- 主ボトルネックは `pipeline` ではなく `writer` の `peak_end_value` 解決ロジックにある
- 初回は candidate family を増やさず、**top-end 値の取り方だけを改善**するのが安全
- 特に「RMS 1 点依存」を少し和らげるだけでも、flat-top / 急減衰の両方に効く可能性がある

---

## 3. 目的

MS11-9G の目的は次のとおり。

- flat-top / 急減衰 residual を writer 側の top-end shaping で緩和する
- `peak_end_value` の算出を、現行より少し安定したものへ寄せる
- Preview / export の semantics 一致を維持する
- same-vowel / cross-vowel の candidate family には極力触らない

---

## 4. スコープ

### 4-1. 含める対象

- `peak_end_value` 算出方式の見直し
- top-end residual 再現テストの追加
- Preview / export の整合確認

### 4-2. 含めない対象

- same-vowel / cross-vowel candidate の再分類
- writer 新 family の追加
- GUI parameter 追加
- closing 系の再設計
- observation dataclass の field 追加

---

## 5. 取りうる方針

### 案A. `peak_end_frame` 以降の最初の RMS 1 点を維持しつつ clamp だけ追加する

- 急減衰しすぎる場合に下限 clamp を置く

利点:

- 実装が小さい

懸念:

- flat-top 側には効きにくい
- 根本的には 1 点依存が残る

### 案B. `peak_end_frame` 周辺の複数サンプルから `peak_end_value` を決める

- 例:
  - `peak_end` 以降の最初の RMS を主値とする
  - その前後 1 点も参照し、最小 / 補間 / 加重平均などで安定化する

利点:

- flat-top / 急減衰の両方に効きやすい
- candidate family を変えずに writer 側だけで改善できる

懸念:

- 補間ルールを決めないと挙動説明が曖昧になる

### 案C. bridge / floor candidate だけ別 top-end rule を持つ

- continuity 系だけ `peak_end_value` の算出を変える

利点:

- 症状に直接効かせやすい

懸念:

- family ごとの暗黙仕様が増える
- 契約整理をまた複雑にしやすい

---

## 6. 推奨方針

MS11-9G 初回は、
**案B を推奨し、案C は避ける**
のが自然である。

推奨内容:

- `peak_end_frame` 以降の最初の RMS を主値とする方針は維持する
- ただしその 1 点だけに決め打たず、周辺 1 点を補助参照して安定化する
- 初回は family 分岐を増やさず、通常 trapezoid と bridge-aware trapezoid の両方に同じ算出方針を適用する

理由:

- top-end residual は値の取り方に起因する可能性が高い
- same-vowel / cross-vowel の分類レイヤを再び触る必要がない
- Preview / export 一致も維持しやすい

---

## 7. 具体的な見直し候補

### 7-1. `peak_end_value` の局所安定化

候補:

- `peak_end_frame` 以降の最初の RMS を主値とする
- その直前または直後の 1 点を補助参照する
- 次のいずれかで決める
  - 最小値寄り
  - 線形補間
  - 主値優先の加重平均

初回推奨:

- **主値優先の加重平均**

理由:

- flat-top を少し下げやすい
- 急減衰も和らげやすい
- min 固定より過剰に下がりにくい

### 7-2. 下限 / 上限の扱い

現行どおり次を維持する。

- `0.0 <= peak_end_value <= peak_value`
- `peak_end_value <= 0` なら現行 fallback を維持

初回では、family 固有の floor 値と強く結びつけない。

### 7-3. 実データ確認対象

初回で固定したい観測対象:

- flat-top に見える residual case
- 急減衰に見える residual case
- bridge-aware trapezoid で 3 点目が不自然な case

まずは 2〜3 ケースを固定すれば十分である。

---

## 8. 責務分割

### 8-1. pipeline

主責務:

- RMS 窓情報と observation を writer へ渡す

初回方針:

- `pipeline` は非改変または最小変更に留める

### 8-2. writer

主責務:

- `peak_end_value` をどう解決し、top-end の 3 点目値へ落とすかを決める

初回方針:

- 主変更点は writer
- `peak_end_value` 解決 helper のみを中心に見直す

### 8-3. Preview

主責務:

- writer と同じ top-end semantics を表示する

初回方針:

- writer helper 再利用を維持する
- Preview 固有ロジックは増やさない

---

## 9. 実装フェーズ

## Phase 1. residual top-end case の固定

作業:

- flat-top residual と急減衰 residual を 2〜3 ケース固定する
- 可能なら `tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` に再現ケースを追加する

完了条件:

- 「今は不自然だが改善したい top-end case」が明文化される

## Phase 2. `peak_end_value` 解決ロジックの最小見直し

作業:

- 1 点依存を和らげる補助参照ロジックを追加する
- clamp 方針は現行互換を維持する

完了条件:

- 少なくとも synthetic case で flat-top / 急減衰のどちらかが改善する

## Phase 3. Preview / export 確認

作業:

- Preview と export の一致確認
- 必要なら実データ VMD 比較

完了条件:

- top-end shaping の差分が実出力へ届く

## Phase 4. regression 確認

作業:

- same-vowel / cross-vowel continuity 系
- closing 系
- zero-only shape 抑止

への副作用を確認する

完了条件:

- 対象外 family を壊していない

---

## 10. ユーザー判断が必要な点

### Q1. 初回は `peak_end_value` の算出方式だけに絞るか

- 推奨案: **はい**
- 理由:
  - candidate family を再び広げず、top-end residual に集中できる

### Q2. 初回は family 別 rule を増やさず、共通 top-end rule で進めるか

- 推奨案: **はい**
- 理由:
  - same-vowel / cross-vowel で暗黙仕様を増やしにくい

### Q3. 初回は主値優先の加重平均を候補として検討するか

- 推奨案: **はい**
- 理由:
  - flat-top と急減衰の両方に穏やかに効かせやすい

---

## 11. 内容検証メモ

このプランが現状と矛盾していないかの検証結果は次のとおり。

- `MS11-9_Remaining_Issues.md` では、top-end shaping は「改善済みだが残課題あり」と整理されている
- 現行 `writer.py` の `_resolve_peak_end_value_from_observation(...)` は、`peak_end_frame` 以降の最初の RMS 1 点に依存している
- Preview は writer helper 再利用なので、writer 主変更で semantics 一致を維持しやすい
- same-vowel / cross-vowel の continuity 系は一段区切れたため、次段で writer 主体へ移る流れは自然

現時点では、
**MS11-9G を top-end shaping residual の writer 主体改善として切ることに大きな論理矛盾は見当たらない**
と判断できる。

---

## 12. 要約

MS11-9G は、
**`peak_end_value` の 1 点依存を和らげ、flat-top / 急減衰の residual を writer 側の top-end shaping で緩和する**
ための実装前プランである。

---

## 13. 実装・確認結果

### 13.1 実装反映

- `src/vmd_writer/writer.py` の `_resolve_peak_end_value_from_observation(...)` を更新し、
  `peak_end_frame` 以降の最初の RMS を主値にしつつ、その直後の 1 点を補助参照する
  局所安定化ロジックを追加した
- `tests/test_vmd_writer_intervals.py` に、
  - top-end がやや下がる case
  - 急減衰が少し和らぐ case
  を追加した
- `tests/test_preview_transform.py` に同等の Preview 回帰を追加した

### 13.2 回帰確認

- `tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` は通過
- `tests/test_pipeline_peak_values.py` と `tests/test_pipeline_and_vmd.py` も通過
- 確認時点で、same-vowel / cross-vowel / Preview / export の既存主要導線は維持された

### 13.3 実出力確認

- ローカル再生成した
  [dist/_tmp_ms11_9g_sample_input2_upper1.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9g_sample_input2_upper1.vmd)
  は、[Test11_9o.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9o.vmd) と不一致であり、
  top-end shaping の差分が実出力へ届くことを確認した
- その後、ユーザー側生成の
  [Test11_9p.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9p.vmd)
  はローカル再生成結果と完全一致した
- したがって、MS11-9G の今回変更はユーザー側 export にも反映済みである

### 13.4 現在地メモ

- 今回の差分は frame 配置の全面変更ではなく、既存 frame 上の top-end 値配分の再調整として現れている
- したがって MS11-9G は、candidate family を増やさずに top-end residual へ効かせるという初回方針と整合している
- 次の論点は「差分が出たか」ではなく、「MMD 上で flat-top / 急減衰の見え方がどこまで自然になったか」の実観察である

### 13.5 クローズ判断

- ユーザー側で MMD 上の確認が取れたため、MS11-9G は現時点で一旦クローズ扱いとする
- 今後は、新しい実データで top-end residual の再発が見えた場合のみ再オープン対象とする
