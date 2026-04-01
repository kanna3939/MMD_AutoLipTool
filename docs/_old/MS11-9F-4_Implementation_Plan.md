# MS11-9F-4 Implementation Plan

## Final residual cross-vowel triage

## 0. 位置づけ

MS11-9F-4 は、`MS11-9F-3` 後に残った
**residual cross-vowel 3 件**
を対象にした最終整理プランである。

ここまでの到達:

- `MS11-9F` で overlap 起因の残件を大きく削減
- `MS11-9F-2` で moderate right-gap transition を追加
- `MS11-9F-3` で wide 2-event zero-run を `cross_vowel_floor` へ接続
- `sample_input2` の residual cross-vowel は `23 -> 10 -> 7 -> 3`
- 実出力は
  - `9n` が `MS11-9F`
  - `9m` が `MS11-9F-2`
  - `9o` が `MS11-9F-3`
  に一致している

この段階では、
**「残件をさらに救済する」こと自体が正しいか**
を見直す必要がある。

---

## 1. 現在の残件

`sample_input2` の residual は現在次の 3 件である。

- `idx 6`
- `idx 172`
- `idx 193`

観測上の特徴は次のとおり。

### 1-1. `idx 6`

- vowels: `あ -> え -> い`
- `reason = below_rel_threshold`
- `left_gap_refined = 3`
- `right_gap_refined = 2`
- left/right の両側に軽い gap がある
- right-gap 単独問題ではない

### 1-2. `idx 172`

- vowels: `い -> い -> お`
- `reason = below_rel_threshold`
- `left_gap_refined = 1`
- `right_gap_refined = 30`
- next 側が非常に遠い
- speech-internal continuation というより pause 寄りの可能性が高い

### 1-3. `idx 193`

- vowels: `え -> お -> お`
- `reason = below_rel_threshold`
- `left_gap_refined = -1`
- `right_gap_refined = 16`
- left 側は近いが next 側はかなり遠い
- transition / floor のどちらで救うにも距離が大きい

---

## 2. 現在の解釈

F-1〜F-3 で残件を減らした結果、
残っている 3 件は
**「救済漏れ」よりも「本当に救済対象か」**
を問うべきケースに近づいている。

特に `172` と `193` は、

- next 側 gap が大きすぎる
- initial / refined の両方で遠い
- speech-internal continuity と断定しにくい

ため、無理に `transition` や `floor` に入れると
過剰救済になるリスクが高い。

---

## 3. 問題整理

### 3.1 いま残っている論点

1. `idx 6` のような mixed-gap case を追加救済する価値があるか
2. `idx 172` / `193` を pause 寄りとして残課題から外すべきか
3. MS11-9 の cross-vowel 残課題を、どの時点で「十分改善」とみなすか

### 3.2 主仮説

現時点の主仮説は次のとおり。

- `idx 172` / `193` は、初回実装対象としては非推奨
- `idx 6` だけは、必要なら small mixed-gap 補助で再検討余地がある
- ただし `idx 6` も無理に救済すると副作用が出やすい

---

## 4. 目的

MS11-9F-4 の目的は次のとおり。

- 残件 3 件を `追加実装候補 / 非対象候補` に最終分類する
- 追加実装するなら最小 1 パターンに限定する
- 追加実装しないなら、その理由を文書上で明示する

---

## 5. 取りうる方針

### 案A. `idx 6` だけを mixed-gap 補助で追加救済する

利点:

- 残件をさらに 1 件減らせる可能性がある

懸念:

- left/right 両側を触るため副作用が出やすい
- ここまでの right-gap 中心整理から少し外れる

### 案B. `172` / `193` を非対象として閉じる

利点:

- 過剰救済を避けられる
- cross-vowel 残課題を実務上ほぼ収束できる

懸念:

- 「未解決 0 件」にはならない

### 案C. `172` / `193` をさらに floor へ寄せる

利点:

- 数字上は残件を減らせる可能性がある

懸念:

- 現観測では距離が大きすぎ、silence 寄り case まで巻き込みやすい

---

## 6. 推奨方針

MS11-9F-4 初回は、
**案B を推奨し、案A は必要時のみ追加検討**
が自然である。

推奨内容:

- `172` / `193` は pause 寄り・非対象候補として整理する
- `idx 6` は mixed-gap 境界 case として保留する
- ここで一度 `MS11-9_Remaining_Issues.md` と契約メモへ現在地を同期する

理由:

- ここまでで cross-vowel は実出力差分まで十分届いている
- 残件 3 件のために rule をさらに広げると、副作用リスクの方が大きい
- 契約整理の観点でも、ここで「非対象にする基準」を明示する価値が高い

---

## 7. 実装フェーズ

## Phase 1. 残件 3 件の最終分類

作業:

- `idx 6` を mixed-gap 境界 case
- `idx 172`, `193` を pause 寄り候補

として固定する

完了条件:

- 追加実装対象と非対象候補が明文化される

## Phase 2. 必要なら `idx 6` のみ最小検討

作業:

- `idx 6` に限定した mixed-gap 補助案を検討する

完了条件:

- 実装するか、見送るかを判断できる

## Phase 3. 文書同期

作業:

- `MS11-9F_Implementation_Plan.md`
- `MS11-9_Remaining_Issues.md`
- `MS11-9_Observation_Handoff_Contract_Memo.md`

へ現在地を同期する

完了条件:

- cross-vowel 残課題の現在地が文書上で整う

---

## 8. ユーザー判断が必要な点

### Q1. F-4 初回は `172` / `193` を非対象候補として整理してよいか

- 推奨案: **はい**
- 理由:
  - next 側 gap が大きく、現時点では speech-internal continuity と言い切りにくい

### Q2. `idx 6` は今すぐ実装せず、境界 case として保留してよいか

- 推奨案: **はい**
- 理由:
  - mixed-gap は副作用リスクが高く、まずは文書整理を優先した方が安全

### Q3. cross-vowel は一度ここで整理優先へ切り替えるか

- 推奨案: **はい**
- 理由:
  - same-vowel/cross-vowel ともに実出力差分までは十分到達しており、
    この段階で契約整理へ戻る価値が高い

---

## 9. 内容検証メモ

このプランが現状と矛盾していないかの検証結果は次のとおり。

- `idx 172` は `right_gap_refined = 30`
- `idx 193` は `right_gap_refined = 16`
- 両者とも moderate / wide right-gap 救済の延長で扱うには距離が大きい
- `idx 6` は left/right 両側が絡む mixed-gap case であり、別問題として切る方が自然
- ここまでの F-1〜F-3 はすべて実出力差分まで到達しており、
  cross-vowel 残課題は実務上かなり圧縮できている

現時点では、
**F-4 は「さらに救済を増やす」より「ここで閉じる基準を決める」ためのプラン**
として整合している。

---

## 10. 要約

MS11-9F-4 は、
**残り 3 件を無理に救済し切るのではなく、
`idx 6` を境界 case、`172/193` を非対象候補として最終整理する**
ためのプランである。

---

## 11. 文書上の確定事項

2026-04-01 時点で、MS11-9F-4 は文書上で次の結論を確定扱いとする。

- `idx 172` / `193` は、現時点では pause 寄りの非対象候補として扱う
- `idx 6` は mixed-gap 境界 case として保留し、cross-vowel 初回完了条件には含めない
- cross-vowel 残課題は `23 -> 10 -> 7 -> 3` まで圧縮され、F / F-2 / F-3 はいずれも実出力差分まで確認済み
- したがって、MS11-9F 系は「さらに救済ルールを増やす」より「ここで閉じる基準を明示する」段階まで到達した
