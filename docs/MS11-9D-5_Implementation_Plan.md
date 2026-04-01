# MS11-9D-5 Implementation Plan

## Cross-vowel continuity-floor expansion and peak-end re-evaluation

## 0. 位置づけ

MS11-9D-5 は、MS11-9D-4 の実装後検証で確認された
「flat top 改善が限定的であり、speech-internal な完全閉口も多く残る」
という課題に対する後続計画である。

本タスクは、特に実データ VMD で確認された次の現象を直接対象とする。

- cross-vowel に見える遷移でも、前後 morph がともに zero-peak 扱いとなり完全閉口している
- `continuity floor = 0.1` がほとんど発火していない
- `peak_end_value` が nearest RMS 1点依存では十分に下がらず、flat top が残る

MS11-9D-5 では、次の 3 本を主題とする。

- `continuity floor` 適用条件の拡張
- `peak_end_value` 算出方式の見直し
- `cross-vowel zero-run` の別 classification 導入

初回 MS11-9D-5 の固定方針:

- `peak_end_value` は `peak_end_frame` 以降で最初に取れる RMS を優先して決める
- observation 契約は `cross-vowel zero-run continuity-floor candidate` を `bool` 追加で持つ
- `continuity floor` の対象は `speech-internal short zero-run cross-vowel` のみに限定する
- overlap と floor が両立する場合は **overlap を優先**し、floor は補助に留める
- zero-run 幅上限は **2 event / 2 frame のまま維持**する

本タスクは、以下とは切り分ける。

- final closing hold / softness の再設計
- GUI parameter 追加
- RMS 全体の閾値再設計
- 無音区間全般の再設計
- MS12 の responsiveness / splash / packaging

---

## 1. 背景

MS11-9D-4 では、

- `AsymmetricTrapezoidSpec.peak_end_value`
- `continuity floor = 0.1`
- zero-peak cross-vowel candidate に対する最小開口

を導入した。

しかし実データ VMD の確認では、次が残った。

- all-zero frame が多数残る
- flat top がまだ複数箇所に残る
- floor が実際に使われた形跡がほとんど無い

このことから、問題の中心は
「writer の top-end shaping だけではなく、candidate 化と適用条件が保守的すぎる」
点にあると考えられる。

---

## 2. 目的

MS11-9D-5 の目的は次のとおり。

- speech-internal な cross-vowel zero-run に対して、完全閉口をより確実に減らす
- `continuity floor` を必要な case に届くようにする
- `peak_end_value` を実音量変化に対してより敏感にする
- Preview / export の semantics 整合を維持する

---

## 3. スコープ

### 3-1. 含める対象

- `continuity floor` の適用対象拡張
- `cross-vowel zero-run continuity-floor candidate` の observation 分離
- `peak_end_value` の算出方式見直し
- writer / Preview の同一 semantics 更新
- 実データ VMD 検証に基づく最小テスト追加

### 3-2. 含めない対象

- same-vowel bridge 判定の全面再設計
- final closing 系の仕様変更
- GUI 追加
- RMS threshold 定数の全体再調整
- MS12

---

## 4. 非目標

- `peak_value == 0.0` の全救済
- 無音区間全体への floor 展開
- Preview 独自 smoothing の導入
- morph 全体の大規模 refactor

---

## 5. 基本方針

### 5-1. `continuity floor` は candidate を広げて効かせる

MS11-9D-5 では、floor 自体の値を先に変えるのではなく、
まず `0.1` を維持したまま適用条件を広げる。

理由:

- まず「発火していない」問題を解くべき
- 値の再調整はその後でもできる

### 5-2. `cross-vowel zero-run` は通常 transition と分ける

現状の `is_bridgeable_cross_vowel_transition_candidate` だけでは、

- overlap を作る case
- overlap は作れないが最小開口は残したい case

が混ざる。

MS11-9D-5 では、後者を
**`cross-vowel zero-run continuity-floor candidate`**
として別分類する。

### 5-3. `peak_end_value` は nearest 1点依存をやめる

MS11-9D-4 の nearest RMS 1点方式は、
実データによっては top-end 減衰が弱い。

そのため MS11-9D-5 では、候補を次のどちらかに寄せる。

- `peak_end_frame` 以降で最初に観測される RMS を優先する
- `peak_start -> peak_end` または `peak_end` 周辺で補間値を作る

初回固定:

- **`peak_end 以降で最初に取れる RMS を優先`** する

---

## 6. 責務分割

### 6-1. pipeline

主責務:

- `cross-vowel zero-run continuity-floor candidate` を observation で識別する
- same-vowel / cross-vowel transition / continuity-floor を分けて持つ

方向性:

- `timeline` は不変
- 正本は引き続き `observations`

### 6-2. writer

主責務:

- candidate 種別ごとに
  - overlap
  - floor
  - top-end shaping
  を切り分けて適用する

方向性:

- overlap が作れる case は transition で扱う
- overlap が作りにくい cross-vowel zero-run は floor を補助として使う
- `peak_end_value` は新しい RMS 選択方針で再計算する

### 6-3. Preview

主責務:

- writer と同じ candidate 種別と `peak_end_value` / floor semantics を表示する

### 6-4. GUI

固定:

- GUI 追加なし
- fixed policy

---

## 7. `continuity floor` 拡張方針

MS11-9D-5 での対象拡張案:

- 既存 `cross-vowel transition candidate`
- `zero-run cross-vowel span`
- `speech-internal` と判定できる `cross-vowel zero-run`

ただし次は維持する。

- 前後に non-zero shape がある
- gap 幅は短い
- final closing ではない
- zero-peak 全救済に広げない

初回固定:

- 対象は **`speech-internal short zero-run cross-vowel` のみ**
- same-vowel への floor 拡張は行わない
- zero-run 幅上限は **2 event / 2 frame** を維持する

---

## 8. `peak_end_value` 見直し方針

### 8-1. 問題

nearest RMS 1点方式では、次の問題がある。

- 3点目直前の減衰が見えにくい
- plateau が残る
- 実データで改善量が小さい

### 8-2. 改善候補

候補 A:

- `peak_end_frame` 以降で最初に取れる RMS を優先する

候補 B:

- `peak_end_frame` 周辺の前後 2 点から補間する

初回固定:

- 候補 A

理由:

- 実装差分が小さい
- 3点目の減衰を出しやすい
- Preview 側も合わせやすい

---

## 9. observation 契約の方向性

MS11-9D-5 では、少なくとも次のどちらかが必要になる。

- `is_cross_vowel_zero_run_continuity_floor_candidate: bool`
- もしくは candidate 種別を enum 相当で持つ

初回固定:

- 既存流儀に合わせ、bool を追加する

理由:

- 差分が小さい
- MS11-9D / 9D-2 / 9D-3 / 9D-4 との整合が取りやすい

---

## 10. Preview / export 整合方針

MS11-9D-5 でも、次を維持する。

- Preview 独自補間を入れない
- writer と Preview は同じ candidate 種別を見る
- `peak_end_value` と `continuity floor` は同じ値を使う
- overlap が成立する case では overlap を優先し、floor は補助に留める

---

## 11. 最低限のテスト観点

### 11-1. pipeline

- `cross-vowel transition candidate` と
  `cross-vowel zero-run continuity-floor candidate`
  が分離される

### 11-2. writer

- zero-run cross-vowel case で `0.1` floor が実際に出力される
- floor を入れても peak の代替にならない
- `peak_end_value` が old nearest方式より下がる case を持つ

### 11-3. Preview

- Preview が writer と同じ floor / peak_end_value を表示する

### 11-4. real-data

- 提出 VMD と同種の all-zero frame が減る
- flat top が減る
- speech-internal 完全閉口が減る

---

## 12. スコープ外

- floor 値 `0.1` 自体の再調整
- GUI parameter 化
- RMS 全体定数見直し
- 無音全般の扱い変更
- MS12

---

## 13. 未確認事項

現時点で未固定の項目は次のとおり。

- bool の具体 field 名
- `peak_end 以降で最初に取れる RMS` が存在しない場合の fallback
- floor をどの control point に置くか
- `speech-internal` 判定の最終条件の細部

---

## 14. 到達イメージ

MS11-9D-5 完了時の到達イメージ:

- zero-peak cross-vowel case で完全閉口が減る
- `continuity floor` が実データ上でも発火する
- 3点目がより明確に減衰する
- Preview / export の一致を維持する

---

## 15. 要約

MS11-9D-5 は、
**MS11-9D-4 実装後に残った flat top と speech-internal 完全閉口を減らすため、**

- `continuity floor` の適用条件を広げ
- `cross-vowel zero-run` を別分類し
- `peak_end_value` をより実音量変化に追従させる

ための後続計画である。

初回固定方針は次のとおり。

- `peak_end_value` は `peak_end_frame` 以降で最初に取れる RMS を優先する
- observation 契約は bool 追加で持つ
- floor 対象は `speech-internal short zero-run cross-vowel` のみ
- overlap を優先し、floor は補助に留める
- zero-run 幅上限は `2 event / 2 frame` を維持する
