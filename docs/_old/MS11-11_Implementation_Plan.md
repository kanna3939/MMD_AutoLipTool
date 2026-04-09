# MS11-11 Implementation Plan

## 0. 文書目的

MS11-11 は、
**MS11-9 系で増えた observation / handoff 契約を整理し、今後の保守性を上げるための設計整備タスク**
である。

本タスクは、ここまでの same-vowel / cross-vowel / top-end / closing smoothing 修正を
**さらに訂正したり、意味を変えたりしない**
ことを前提にする。

目的は「挙動変更」ではなく、

- 契約の見える化
- helper 責務の整理
- downstream handoff の追跡容易化

に限定する。

---

## 1. 現在の前提

本タスク開始時点で、MS11 系では少なくとも次が反映済みである。

- MS11-9D から MS11-9D-6 の speech-internal continuity 系
- MS11-9E から MS11-9E-4 の same-vowel residual refinement
- MS11-9F から MS11-9F-4 の cross-vowel residual refinement
- MS11-9G の top-end shaping residual refinement
- MS11-9FIX7 の closing smoothing tail-contract realignment

また、ユーザー確認により次は完了扱いとする。

- same-vowel の最終見え方
- cross-vowel の残件整理
- top-end shaping の見え方
- closing smoothing の自然さ確認

したがって、MS11-11 の主対象は
**`pipeline / writer / preview / GUI handoff` 周りの observation 契約整理のみ**
とする。

---

## 2. 壊さない前提

MS11-11 では、以下を壊さない前提として固定する。

- `timeline` は canonical writer input のまま維持する
- continuity / bridge / floor / burst の候補正本は `observations` 側に置く
- Preview 独自近似は増やさず、writer helper 再利用を優先する
- final closing 系と speech-internal continuity 系を混ぜない
- MS11-9F-4 の「救済しない残件」の判断は維持する
- MS11-9G の top-end rule は維持する
- MS11-9FIX7 の tail post-process 契約は維持する

重要:

- same-vowel / cross-vowel の candidate 条件は原則として変更しない
- hold / softness / top-end / floor の係数は変更しない
- GUI 表示・入力意味は変更しない
- VMD 出力差分が出るような修正は、MS11-11 の目的外とする

---

## 3. 問題設定

現時点の observation 契約は、実装としては機能しているが、
次の点で見通しが悪くなっている。

### 3.1 pipeline 側

- same-vowel / cross-vowel / zero-run / burst / floor の候補判定が helper に分散している
- representative span などの補助解釈が field ではなく helper 内局所計算に寄っている
- `reason` と candidate bool 群の関係が文書なしでは追いにくい

### 3.2 writer 側

- candidate を最終 shape へ翻訳する責務が helper 群へ分散している
- same-vowel / cross-vowel / top-end / closing smoothing が、別テーマとして増築されている
- 「pipeline で確定したこと」と「writer が解釈すること」の境界が読み取りにくい

### 3.3 preview / handoff 側

- Preview は writer 追随方針で比較的安定しているが、
  どの helper 結果を再利用しているかが一覧しにくい
- GUI / export handoff は単一路線だが、
  observation がどの条件で Preview / export に届くかが見えにくい

---

## 4. MS11-11 の目標

MS11-11 の目標は次のとおり。

1. `observations` 契約の一覧を、コード上でも追いやすくする
2. `pipeline で確定すること` と `writer で解釈すること` を明確に分ける
3. Preview / export handoff の追跡経路を読みやすくする
4. 将来の微調整時に「どこを見るべきか」を迷いにくくする

本タスクの完了像は、
**挙動は維持したまま、契約の読みやすさと保守性だけを上げた状態**
である。

---

## 5. スコープ

### 5.1 対象

- `src/core/pipeline.py`
- `src/vmd_writer/writer.py`
- `src/gui/preview_transform.py`
- 必要最小限の `src/gui/main_window.py`
- 契約整理文書
- 契約整理に対応する最小テスト

### 5.2 非対象

- same-vowel の追加微調整
- cross-vowel の追加救済
- top-end shaping の再調整
- closing smoothing の再調整
- GUI パラメータ追加
- RMS 閾値再調整
- VMD 出力形状そのものの見た目変更

---

## 6. 実装方針

### 6.1 基本方針

MS11-11 は、全面再設計ではなく
**観測契約の明示化と read-path の整理**
を優先する。

方針は次の順に固定する。

1. field / helper / 消費先の一覧化
2. helper 群の責務コメントまたは補助 dataclass 化
3. handoff 経路の見える化
4. 既存テストの意味づけ補強

### 6.2 設計上の原則

- 新しい candidate family は増やさない
- 既存 bool / span field の意味は変えない
- helper の役割名を明確化する
- 読み取り専用の補助 dataclass / typed alias は許容する
- 既存の public-ish 関数シグネチャはできるだけ変えない

---

## 7. 段階案

### Phase 1

契約棚卸し

- `PeakValueObservation` の主要 field と用途をコードコメントまたは補助定義へ整理
- `pipeline -> writer -> preview` で使う field を一覧化
- `writer` 側 helper の責務を same-vowel / cross-vowel / top-end / closing smoothing に分けて明示

### Phase 2

pipeline 契約整理

- candidate 判定 helper の責務境界を明示
- representative span 系 helper の位置づけをコメントか補助関数名で明確化
- `pipeline で確定すること` を追いやすくする

### Phase 3

writer 契約整理

- `writer が解釈すること` を helper 単位で明確化
- same-vowel / cross-vowel / floor / top-end / tail smoothing の責務境界をコメントまたは薄い補助 dataclass で明示
- family ごとの暗黙契約を減らす

### Phase 4

Preview / handoff 契約整理

- Preview が writer 追随であることをコード上でも分かりやすくする
- `main_window -> preview_transform -> writer helper reuse` の経路を追いやすくする
- export と Preview の共通 handoff を補助コメントで固定する

### Phase 5

最小回帰整理

- 既存テストのうち、契約確認として意味の強いものへ補助コメントや補助 assertion を追加
- 挙動差分ではなく「契約が変わっていない」ことを確認する

---

## 8. 具体候補

### 候補A: 補助 dataclass / typed alias の導入

例:

- observation family ごとの read-only view
- same-vowel / cross-vowel candidate read context
- tail smoothing input context

制約:

- 値の再計算や再分類はしない
- 既存 field の意味を包むだけに留める

### 候補B: helper 群の責務コメント強化

例:

- 「この helper は candidate 判定」
- 「この helper は shape translation」
- 「この helper は tail post-process」

制約:

- コメントだけで意味が固定できるなら、無理に型を増やさない

### 候補C: handoff comment / glue の整理

例:

- `main_window.py` の Preview / export handoff に説明追加
- `preview_transform.py` の writer helper 再利用意図を明文化

---

## 9. 完了条件

- `observations` 契約の主要 field / helper / 消費先が追いやすい
- `pipeline` と `writer` の責務境界が今より明確
- Preview / export handoff が今より読解しやすい
- 既存挙動を変えない
- 既存主要テストが通る

---

## 10. リスク

### リスク1

整理のつもりで挙動変更が入る

対策:

- candidate 条件、係数、shape 値配分には触れない
- VMD 差分が出る変更は別タスクへ分離する

### リスク2

補助型や helper 追加で逆に複雑化する

対策:

- まずはコメント整理を優先
- dataclass は本当に読解が改善する箇所だけに限定

### リスク3

大きなリファクタへ広がる

対策:

- public 経路を変えない
- 1 回で全部やらず、Phase 単位で止められる形にする

---

## 11. ユーザー判断が必要になりやすい点

現時点の推奨はすべて次のとおり。

1. 初回は挙動変更なしで進めるか  
推奨案: はい

2. 初回は observation field 追加より、read-only 補助整理を優先するか  
推奨案: はい

3. 初回は writer / preview の family 整理より、pipeline / writer 境界整理を優先するか  
推奨案: はい

---

## 12. 要約

MS11-11 は、
**MS11 の挙動をこれ以上訂正せず、FIX7 までの到達状態を前提に observation / handoff 契約だけを安全に整理するためのタスク**
である。

最初の実装は、
**挙動変更なし・read-path 整理優先・helper 責務の明示化**
で進めるのが最も安全である。
