# MS11-9E-3 Implementation Plan

## Same-vowel-like zero/low-energy event の interval refinement と candidate 判定の整合化

## 0. 位置づけ

MS11-9E-3 は、MS11-9E および MS11-9E-2 の実装後確認で明らかになった
**「same-vowel candidate 判定の前段で使われる refined interval が、same-vowel continuity 判定の想定より長すぎる」**
という不整合に対する調整計画である。

MS11-9E は writer 側 burst smoothing の refinement、
MS11-9E-2 は pipeline 側 candidate 条件の最小拡張を扱った。

しかし実データ確認では、same-vowel-like な `below_rel_threshold / no_peak_in_window` event が存在しても、
候補化条件に入る前提となる interval 自体がすでに長く、
結果として same-vowel smoothing へ到達していなかった。

したがって MS11-9E-3 では、
**candidate 条件をさらに広げる前に、interval refinement と candidate 判定の基準面を揃える**
ことを主目的とする。

---

## 1. 背景

現行 pipeline では、概ね次の順で処理が進む。

1. 初期 timeline を構築する
2. RMS により event interval を refine する
3. refined interval 上で peak value を評価する
4. observation を構築する
5. observation 上で same-vowel / cross-vowel / zero-run candidate を判定する

この構造自体は妥当だが、same-vowel-like zero/low-energy event に関しては次のズレがある。

- interval refinement は「その event 自体の base interval」をかなり保持しやすい
- same-vowel candidate 判定は「短い gap / 短い span / 軽微 overlap」を前提にしている

このため、実データでは:

- `below_rel_threshold` や `no_peak_in_window` の event が same-vowel continuity に見える
- しかし refined interval は `7〜8 frame` 級に残る
- candidate 判定では `span_gt_2` / `gap_gt_2` で落ちる
- writer / Preview の same-vowel smoothing が発火しない

という状態になっている。

---

## 2. 確認できた事実

実データ確認で、少なくとも次は確認済みである。

- `sample_input2` と `MMD_AutoLipTool説明1` では、observation 集計が同一だった
- 現行 workspace では:
  - `same_bridge = 0`
  - `same_burst = 0`
- same-vowel-like flagged case は存在する
- それらの主な fail reason は:
  - `span_gt_2`
  - `gap_gt_2`
- 実例では same-vowel-like zero/low-energy event の refined interval が長い
  - 例: `90-98`, `164-171`, `416-423`, `757-764`

したがって、現在の主要ボトルネックは
**candidate 条件が少し狭いこと自体ではなく、candidate 判定対象として見る interval が長すぎること**
だと整理できる。

---

## 3. 問題整理

### 3-1. 現状の不一致

現在の same-vowel 系では、

- interval refinement
- candidate classification
- writer smoothing

の 3 層が存在する。

このうち writer smoothing 自体は既存構造で動作可能だが、
前段 2 層の間に次の不一致がある。

- refinement 層:
  zero/low-energy event でも base interval を比較的広く残す
- classification 層:
  micro-gap / short span として見える短さを前提にする

### 3-2. 実害

この不一致により、ユーザー意図としては
「同母音の連続なので閉じ切らずに continuity として扱いたい」
case でも、system 上は
「長い zero span / 長い low-energy span」
と見なされる。

結果:

- same-vowel candidate が立たない
- writer の smoothing が効かない
- VMD は旧出力と一致する

---

## 4. 目的

MS11-9E-3 の目的は次のとおり。

- same-vowel-like zero/low-energy event に対して、
  interval refinement と candidate 判定の基準を揃える
- same-vowel continuity に見える実データ case を、過剰に広げずに拾えるようにする
- writer / Preview の既存 same-vowel smoothing を、実データまで届かせる
- `timeline` canonical / `observations` 正本の原則を維持する

---

## 5. スコープ

### 5-1. 含める対象

- same-vowel-like zero/low-energy event の interval 解釈見直し
- candidate 判定用 span の representative range 見直し
- pipeline test の追加
- 必要最小限の writer / Preview handoff 確認

### 5-2. 含めない対象

- cross-vowel family の全面再設計
- peak threshold 値の全面見直し
- GUI parameter 追加
- `PeakValueObservation` の全面 dataclass 再編
- MS12 系の課題

---

## 6. 非目標

- zero-peak 全ケースを救済すること
- same-vowel と cross-vowel を同じ rule へ統合すること
- RMS refinement 全体を別アルゴリズムへ置き換えること
- writer 形状 family を大きく作り直すこと

---

## 7. 主原因の仮説

MS11-9E-3 でまず採るべき主仮説は次のとおり。

### 仮説A. zero/low-energy event は「見た目の span」と「event interval」が一致しない

same-vowel continuity に見える実データ case では、
zero/low-energy event の base interval が広くても、
見た目上の閉口感はその全幅に対応していない可能性が高い。

つまり candidate 判定で使うべきなのは、
event の base/refined interval 全体ではなく、
**same-vowel continuity 判定用に絞った representative span**
かもしれない。

### 仮説B. current refinement は zero/low-energy event に対して safe すぎる

`local_peak <= abs threshold` の event では、
refined interval がほぼ base interval のまま残るため、
continuity 判定の材料としては粗すぎる可能性がある。

### 仮説C. candidate 判定は refined interval をそのまま使いすぎている

candidate classification は現在、
refined interval の frame 幅・gap・overlap に強く依存している。

しかし same-vowel-like zero/low-energy case だけは、
**classification 用の短い解釈層**を別に持った方が自然かもしれない。

---

## 8. 取りうる方針

### 案A. refinement 側で zero/low-energy event の interval を短くする

- `below_rel_threshold / no_peak_in_window` かつ same-vowel-like な event では、
  refined interval を短い代表幅に寄せる

利点:

- candidate 判定側をあまり複雑にしなくてよい
- same-vowel として自然な幅がそのまま downstream に渡る

懸念:

- refinement 自体の意味が変わる
- cross-vowel や一般 case への副作用が読みづらい

### 案B. candidate 判定専用の representative span を導入する

- event の refined interval 自体は維持する
- ただし same-vowel-like zero/low-energy case では、
  classification のときだけ短い representative span を計算して使う

利点:

- interval refinement の既存契約を壊しにくい
- same-vowel candidate 問題にだけ局所対応しやすい

懸念:

- `observation` 上に「本来 interval」と「candidate 用 span」の二重概念が増える
- 設計の見通しは少し悪くなる

### 案C. observation に same-vowel candidate 用補助 range を持たせる

- `candidate_interval_start_sec / candidate_interval_end_sec` のような補助情報を持たせる
- same-vowel classification はそれを使う

利点:

- 後続ロジックが明示的になる
- 実データ調査がしやすい

懸念:

- `PeakValueObservation` の混雑が進む
- 初回としてはやや大きい

---

## 9. 初回推奨方針

MS11-9E-3 初回は、
**案B を中心に、必要なら最小限の案C を補助として採る**
のが推奨である。

推奨内容:

- refined interval 自体は原則そのまま維持する
- same-vowel-like zero/low-energy event だけ、
  candidate 判定用の short representative span を pipeline 内部で計算する
- まずは helper 内部の局所計算で始め、
  observation field 追加は初回では避ける

理由:

- 現行の refinement 契約を壊さず進めやすい
- 問題の中心である same-vowel candidate 判定にだけ効かせやすい
- 失敗しても rollback 範囲が小さい

---

## 10. 具体的な見直し案

### 10-1. candidate 判定用 representative span の導入

same-vowel-like zero/low-energy event に対して、
candidate 判定時だけ次のような representative span を計算する。

- center は event `time_sec`
- 幅は `1〜2 frame` 相当を上限とする
- 前後 same-vowel non-zero event の end/start と矛盾しないよう clip する

これにより、
「event interval は長いが、continuity 判定としては短く見たい」
case を扱えるようにする。

### 10-2. zero-run span 判定と burst span 判定の入力統一

現行では:

- zero-run span classification
- same-vowel burst span classification

がどちらも refined interval を直接見ている。

MS11-9E-3 では、
same-vowel-like zero/low-energy member が含まれる span についてだけ、
共通の representative frame range を使う方向を検討する。

### 10-3. `below_rel_threshold` と `no_peak_in_window` の扱い分離は後回し

初回では、
reason ごとの別 rule 追加は避ける。

まずは:

- same-vowel-like
- zero/low-energy
- span が短く見えるべき case

という構造で揃える。

---

## 11. 責務分割

### 11-1. pipeline

主責務:

- representative span 計算
- same-vowel candidate classification の整合化
- 実データ再現テストの追加

初回方針:

- 変更の中心は pipeline
- helper 追加は可
- observation bool は原則増やさない

### 11-2. writer

主責務:

- pipeline で candidate が立った case を既存 smoothing に渡す

初回方針:

- writer は原則変更なし
- 既存 MS11-9E smoothing が届くかを確認する

### 11-3. Preview

主責務:

- writer と同じ semantics を表示する

初回方針:

- Preview 側の固有変更は極力避ける
- pipeline candidate が立つことで自然に差分が出るかを見る

---

## 12. 実装フェーズ

## Phase 1. 実データ fail case の固定

作業:

- `sample_input2` 相当で same-vowel-like だが落ちる event を 2〜3 件固定する
- `tests/test_pipeline_peak_values.py` とは別に、
  representative span 観点のテスト追加方針を決める

完了条件:

- 「落ちる理由」が frame 単位で再現される

## Phase 2. representative span helper の最小導入

作業:

- same-vowel-like zero/low-energy event 用 helper を追加する
- zero-run / burst の same-vowel classification でその helper を使用する

完了条件:

- 少なくとも一部の実データ same-vowel-like case が candidate 化される

## Phase 3. handoff 確認

作業:

- writer / Preview へ既存 path のまま渡るか確認する
- VMD 差分が出るか確認する

完了条件:

- same-vowel smoothing が実データで初めて発火する

## Phase 4. regression 確認

作業:

- cross-vowel / final closing / existing same-vowel tests の回帰確認

完了条件:

- 対象外 family を壊していない

---

## 13. 最低限のテスト観点

### 13-1. pipeline

- same-vowel-like `below_rel_threshold` single event で、
  長い refined interval でも representative span により candidate 化される
- same-vowel-like `no_peak_in_window` / `below_rel_threshold` mixed span が candidate 化される
- cross-vowel case は巻き込まれない
- truly long silence-like case は引き続き除外される

### 13-2. writer

- 新規 candidate が既存 same-vowel smoothing に届く
- zero-peak 全救済には広がらない

### 13-3. Preview

- Preview と export の差分が一致する

---

## 14. ユーザー判断が必要な点

現時点で、実装前に固定しておくと安全な点は次の 3 つである。

### Q1. MS11-9E-3 初回は refinement 本体を変えず、candidate 判定専用 span の導入を優先するか

- 推奨案: **はい**
- 理由:
  - 差分が小さい
  - rollback しやすい
  - 問題の中心に直接効く

### Q2. representative span の初回上限を `1〜2 frame` 相当に留めるか

- 推奨案: **はい**
- 理由:
  - zero-peak 全救済へ広がりにくい
  - current same-vowel family の見え方と整合しやすい

### Q3. 初回は observation への新 field 追加を避け、helper 内局所計算で進めるか

- 推奨案: **はい**
- 理由:
  - `PeakValueObservation` の混雑を抑えられる
  - plan の焦点を interval/candidate 整合化に絞れる

---

## 15. スコープ外

- cross-vowel candidate family の再設計
- peak threshold 値の最終確定
- observation-layer の全面整理
- MS12

---

## 16. 到達イメージ

MS11-9E-3 完了時の到達イメージは次のとおり。

- same-vowel-like zero/low-energy event が、
  長い refined interval のせいで機械的に落ちなくなる
- same-vowel candidate 判定が実データに届く
- 既存 MS11-9E smoothing が、初めて実データ VMD に差分を出せる
- `timeline` canonical / `observations` 正本の原則は維持される

---

## 17. 要約

MS11-9E-3 は、
**same-vowel-like zero/low-energy event で、
interval refinement が作る幅と candidate 判定が期待する幅の不一致を整合させる**
ための計画である。

初回推奨は次のとおり。

- refinement 本体は大きく変えない
- candidate 判定専用の short representative span を導入する
- writer / Preview より先に pipeline 整合化を主対象にする
- observation field 追加は後回しにする
