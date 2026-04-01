# MS11-9D Implementation Plan

## Speech-internal micro-gap bridging

## 0. 位置づけ

MS11-9D は、MS11-9C までで整理された final closing semantics とは別に、
**発話中のごく狭い zero 区間**による不自然な完全閉口を抑えるための計画である。

本タスクは、以下を主対象とする。

- same-vowel 連続中の狭い micro-gap
- Preview / export の semantics alignment を崩さない範囲での bridge 導入

初回実装の固定方針:

- **same-vowel のみを初回対象**とする
- `micro-gap` は **1 frame まで**を対象とする
- `peak_value == 0.0` の reason は、初回は
  - `no_peak_in_window`
  - `below_rel_threshold`
  のみを bridgeable 候補側として扱う
- GUI への新規 parameter 追加は行わず、固定 policy として扱う

本タスクは、以下とは切り分ける。

- MS11-9B / MS11-9C の final closing hold / softness
- 無音区間全般の再設計
- RMS 定数再調整そのもの
- MS12 の GUI responsiveness / splash / packaging

---

## 1. 背景

MS11-9C までの current workspace では、
writer / Preview の closing semantics は final closing 系について概ね揃っている。

一方で、発話中には以下の見え方が残りうる。

- 別母音遷移時に、一度完全閉口してから次モーフを開くように見える
- 狭い `peak_value == 0.0` event や狭い zero 区間のため、MMD 上で口が早くパカパカ見える

現状の `closing_hold_frames` / `closing_softness_frames` は、
**shape の final tail**を調整する仕組みであり、
発話中の micro-gap を bridge するための仕組みではない。

したがって MS11-9D では、
「zero event を平均値で直接救済する」のではなく、
**speech-internal micro-gap bridging** として別責務で整理する。

---

## 2. 目的

MS11-9D の目的は、発話中のごく狭い zero 区間により
不自然な完全閉口が見えるケースを最小限に抑えることである。

本タスクの目的は次のとおり。

- 発話中 micro-gap に限定した bridge semantics を導入する
- `peak_value == 0.0` の全救済にはしない
- bridgeable な候補だけを対象にする
- same-vowel を初回対象とし、cross-vowel は後続課題として切り分ける
- Preview と export を同じ semantics で揃える
- final closing 系とは混ぜない

---

## 3. スコープ

### 3-1. 含める対象

- 発話中の micro-gap bridging 方針の導入
- bridgeable 候補の最小判定
- same-vowel bridge の shape semantics
- Preview と writer の family boundary / bridge boundary alignment
- 必要最小限の pipeline-side candidate 判定導線

### 3-2. 含めない対象

- final closing hold / softness の意味変更
- 無音区間全般の扱い変更
- `peak_value == 0.0` 全体の一律救済
- RMS reason 分類そのものの再定義
- GUI responsiveness / startup / splash / packaging

---

## 4. 非目標

今回やらないことを明確にする。

- `closing_hold_frames` / `closing_softness_frames` の再定義
- final closing family の再設計
- pipeline 上で zero-peak event を一律削除すること
- `global_peak_zero` / `rms_unavailable` を bridge 対象へ広げること
- 「無音に見える区間」全般を新ルールで落とすこと
- 微小 gap 以外の大きい silent interval を bridge すること
- GUI に新しい常設パラメータを増やすことを前提化すること
- Preview だけ先行して独自 bridge 表示を入れること
- cross-vowel bridge を初回実装へ含めること

---

## 5. 基本方針

### 5-1. bridge の考え方

MS11-9D では、bridge 対象を
**発話内部にある bridgeable な微小ギャップ**に限定する。

重要なのは次の点である。

- zero event を独立 peak event として持ち上げない
- zero event の `peak_value` を単純平均で直接上書きしない
- bridge は前後 shape の橋渡しとして表現する
- bridge のための補助値が必要でも、それは shape 生成補助としてのみ使う

### 5-2. same-vowel を初回対象とする

same-vowel と cross-vowel は、既存構造上も自然な扱いが異なるため、
初回実装では同時に扱わない。

- same-vowel
  - 既存 MS11-3 valley 思想に近い bridge を優先する
  - 「連続発話なのに途中で完全閉口する」見え方を抑える
- cross-vowel
  - 問題意識としては維持する
  - ただし初回 MS11-9D では対象外とし、後続候補として切り分ける

### 5-3. final closing との切り分け

MS11-9D は final closing を対象にしない。

したがって、少なくとも以下は除外する。

- 末尾 event の closing tail
- final closing hold / softness の再定義
- 先頭 / 末尾 / 発話終端の挙動を bridge で上書きすること

---

## 6. 既存構造との整合

### 6-1. current workspace の前提

現時点で確認できる前提は次のとおりである。

- pipeline は event を残したまま `peak_value` と reason を決める
- `VowelTimingPlan` / `PipelineResult` には optional な `observations` 契約が既にある
- writer は `peak_value <= 0.0` event を shape 非生成として扱う
- Preview は writer helper を再利用して family / clamp semantics を再構成している
- `closing_hold_frames` / `closing_softness_frames` は final tail だけを扱う

### 6-2. 現行仕様と衝突しやすい点

MS11-9D で最も衝突しやすいのは、次の2点である。

1. `peak_value == 0.0` を不具合扱いして全救済する方向
2. final closing semantics と speech-internal bridge semantics を混ぜる方向

したがって本計画では、
zero-peak を全面救済しないこと、
および final closing 系と speech-internal bridge 系を別責務として保つことを固定する。

### 6-3. MS11-9D 初回で採用する契約方針

初回 MS11-9D では、
**timeline は canonical writer input として維持し、bridge 候補の正本は observations 側に置く**。

採用方針:

- `timeline point に持たせる` は採用しない
- `writer / preview に渡す最小 metadata を別で持つ` も初回は採用しない
- **`observations 側で持たせる` を採用する**

理由:

- `VowelTimingPlan` / `PipelineResult` には既に optional な `observations` 契約がある
- bridgeable 判定は `peak_value == 0.0` の reason と前後文脈に依存し、pipeline observation の意味領域に近い
- 初回 MS11-9D は same-vowel / 1 frame / fixed policy に限定されるため、observations 最小拡張で十分と考えられる
- `VowelTimelinePoint` 自体へ bridge 用意味を増やすと、canonical input の責務が濁りやすい
- cross-vowel まで広げる段階までは、新規 metadata 契約を増やさないほうが自然である

---

## 7. 責務分割

## 7-1. pipeline

主責務:

- `peak_value == 0.0` event のうち、bridgeable 候補になりうるものを判定する
- 既存 reason 分類を破壊せず、bridge 判定に必要な最小情報を持たせる
- 「発話中の狭い gap かどうか」を event 文脈として判断する

想定方針:

- bridgeable 判定は、event の reason、前後 event の存在、位置、狭さに基づく
- zero-peak 自体を non-zero event に書き換えない
- canonical writer input である timeline を大きく再設計しない

初回固定:

- 最大 gap 幅は `1 frame` とする
- reason は `no_peak_in_window` / `below_rel_threshold` のみを候補側とする

初回実装の具体方針:

- `PeakValueObservation` に、MS11-9D 用の最小 bridge candidate 情報を追加する
- 追加情報は「same-vowel micro-gap bridge の候補かどうか」を判断できる最小限に留める
- `timeline` 自体の `peak_value` は書き換えない

未確認事項:

- bridge 候補フラグを `VowelTimingPlan` / `observations` / timeline point のどこに持たせるのが最小かは未確認

## 7-2. writer

主責務:

- bridgeable 候補を独立 peak event として立てず、前後 shape の橋渡しとして扱う
- same-vowel bridge を初回対象とする
- final closing family とは別の speech-internal bridge semantics を持つ

想定方針:

- same-vowel bridge は、MS11-3 envelope に近い valley / non-zero continuity を利用する
- bridge の結果、zero-only shape や不自然な extra peak を新規生成しない

初回実装の具体方針:

- writer は `timeline + observations` を同時に見て、event index 対応で bridgeable 候補を参照する
- observations が無い経路では、MS11-9D bridge は無効として現行互換とする

## 7-3. Preview

主責務:

- writer と同じ family boundary / bridge boundary で shape を表示する
- same-vowel bridge semantics を writer と同様に再構成する
- Preview だけ独自の bridge 補間を発明しない

想定方針:

- 既存どおり writer helper 再利用を優先する
- shape semantics は frame basis、描画 API は seconds basis を維持する

初回実装の具体方針:

- Preview も `timeline + observations` を参照し、writer と同じ event index 対応で bridgeable 候補を解決する
- observations が無い経路では、現行 Preview semantics を維持する

## 7-4. GUI

主責務:

- 原則として追加 GUI を前提化しない
- 既存 `current_timing_plan.timeline -> build_preview_data(...) -> Preview` handoff を維持する
- export では Preview と同じ semantics を使う

現時点の固定方針:

- MS11-9D 初回では GUI 追加なしでも成立する形を優先する
- 初回は fixed policy とし、tuning parameter を追加しない

---

## 8. bridgeable 候補の考え方

### 8-1. bridgeable 候補の基本条件

少なくとも次を満たすものを候補とする方向で整理する。

- 1 frame 以内の狭い gap に限る
- 前後に有効 non-zero shape 候補が存在する
- 先頭 / 末尾 / final closing ではない
- 発話内部の event 文脈である

### 8-2. reason 別の優先解釈

初回固定方針:

- 原則対象外寄り
  - `global_peak_zero`
  - `below_abs_threshold`
  - `rms_unavailable`
- 候補になりうる
  - `no_peak_in_window`
  - `below_rel_threshold`

### 8-3. 除外条件

少なくとも以下は bridge 対象から外す方向が自然である。

- 前後どちらかに non-zero shape がない event
- 先頭 event
- 末尾 event
- final closing に相当する末端区間
- 狭い gap と言えない長さの区間

### 8-4. 初回実装時点の残未確認事項

以下は plan 時点でまだ未確認である。

- `PeakValueObservation` に追加する field の最小セット
- same-vowel bridge の補助値を observation 側のどの field まで持たせるか

### 8-5. 初回 observation 拡張の最小イメージ

初回で想定する最小候補情報の例:

- `is_bridgeable_micro_gap_candidate: bool`
- `bridge_candidate_reason: str | None`
- 必要なら
  - `previous_non_zero_event_index`
  - `next_non_zero_event_index`
  または同等の最小参照情報

ただし、初回は metadata を肥大化させず、
**pipeline で候補判定済みであることが writer / Preview に伝わる最小構成**を優先する。

---

## 9. same-vowel / cross-vowel の扱い

## 9-1. same-vowel

same-vowel では、既存 MS11-3 の valley 思想に近い扱いを優先する。

方向性:

- 途中の狭い zero を、独立 peak としては扱わない
- 前後 top の間に完全閉口を入れず、non-zero valley 相当の橋渡しを許す
- 既存 multi-point family を壊さずに拡張できる形を優先する

狙い:

- same-vowel 連続発話での不自然な「パカッ」とした完全閉口を減らす

## 9-2. cross-vowel

cross-vowel では、same-vowel と同じ valley 発想だけでは不十分である。
問題意識としては維持するが、**初回 MS11-9D では対象外**とする。

後続候補としての方向性:

- 前母音が完全 0 に落ちる前に、次母音の rise 開始を許容する
- 「前母音の fall 完了 -> 完全閉口 -> 次母音の rise」の固定順を前提にしない
- ただし cross-vowel bridge を新しい独立 peak event 化しない

狙い:

- 母音交代中の狭い zero による過剰な完全閉口を抑える

### 9-3. 現時点で固定しないこと

以下は未確認のため、この計画書では確定しない。

- cross-vowel bridge の具体 shape family 名
- cross-vowel bridge を writer 内で overlap 風に表すか、boundary shift 風に表すか
- same-vowel bridge の補助値の具体算出式

---

## 10. Preview / export 整合方針

MS11-9D でも、Preview と export は同じ semantics を維持する。

固定方針:

- Preview だけ先に micro-gap を埋めない
- writer だけ bridge して Preview が完全閉口表示を残す不整合を許容しない
- family boundary と clamp boundary は writer / Preview で共有する
- `build_preview_data(...)` は、既存どおり writer-side semantics を再構成する方向を維持する

重要点:

- 初回 same-vowel bridge で、Preview と export の表現が一致する必要がある
- MS11-9C と同様、shape semantics は frame basis で揃え、表示 API は seconds basis のままとする

---

## 11. 想定実装フェーズ

## Phase 1. bridgeable 候補の定義固定

作業:

- micro-gap の対象条件を fixed policy として整理
- reason 別の対象 / 非対象を整理
- final closing 除外条件を固定

完了条件:

- bridgeable 候補の対象範囲が明文化される
- zero-peak 全救済ではないことが明確になる

## Phase 2. pipeline-side candidate 判定の導入

作業:

- bridgeable 候補を main flow から参照できる最小導線を検討
- `PeakValueObservation` の最小拡張で bridgeable 候補を保持する
- 観測値を壊さず、writer / Preview が event index 対応で bridge 文脈を読める形を整える

完了条件:

- writer / Preview が `timeline + observations` から bridgeable 候補を判定可能になる

## Phase 3. writer-side same-vowel bridge

作業:

- same-vowel micro-gap の橋渡し形状を導入
- MS11-3 / MS11-2 / legacy fallback との境界を整理

完了条件:

- same-vowel micro-gap で完全閉口を必須にしない shape が定義される

## Phase 4. Preview alignment

作業:

- writer と同じ bridge family / boundary を Preview に反映
- 既存 viewport / playback / clipping を壊さない

完了条件:

- Preview / export の見え方が一致する

## Phase 5. 最小 handoff / regression 整理

作業:

- GUI handoff が既存のままで足りるか確認
- 必要なら最小 handoff だけ追加
- ドキュメント同期とテスト観点整理

完了条件:

- MS11-9D の責務境界が既存構造に収まる

---

## 12. 最低限のテスト観点

### 12-1. pipeline

- bridgeable 候補 / 非候補が reason と文脈に応じて分かれる
- `global_peak_zero` / `rms_unavailable` は原則 bridge 対象にならない
- `no_peak_in_window` / `below_rel_threshold` のみが候補化対象になる
- 先頭 / 末尾 / final closing は除外される
- `PeakValueObservation` の最小拡張で候補情報を保持できる

### 12-2. writer

- same-vowel micro-gap で不要な完全閉口を避けられる
- bridge 対象外ケースは現行互換を維持する
- zero-only shape や独立の人工 peak event を新規生成しない
- final closing hold / softness semantics を壊さない
- observations が無い経路では bridge 無効で現行互換になる

### 12-3. Preview

- same-vowel bridge が writer と同じ family で表示される
- Preview だけ先に完全閉口を埋める不整合が起きない
- observations が無い経路では現行 Preview semantics を維持する

### 12-4. pipeline + writer + Preview 統合

- bridgeable micro-gap は export と Preview の両方で同じ見え方になる
- non-bridgeable gap は現行どおり閉口する
- MS11-9B / MS11-9C handoff と競合しない

---

## 13. スコープ外

- RMS 定数の再調整
- `peak_value == 0.0` reason 分類の全面変更
- 無音区間全体の再設計
- final closing family の再設計
- cross-vowel bridge の本実装
- GUI responsiveness / splash / packaging
- 大規模リファクタリング

---

## 14. 実装前に再確認すべき未確認事項

- `PeakValueObservation` にどの field を最低限追加するか
- same-vowel bridge の補助値を writer / Preview でどう解釈共有するか
- `no_peak_in_window` と `below_rel_threshold` のどちらを同一 family で扱えるか

---

## 15. Codex への要約指示

- MS11-9D は final closing ではなく speech-internal micro-gap bridging として扱う
- zero-peak 全救済にはしない
- bridgeable 候補だけを対象にする
- 初回は same-vowel のみを対象にする
- micro-gap は 1 frame までに固定する
- reason は `no_peak_in_window` / `below_rel_threshold` に限定する
- timeline はそのまま維持し、bridge 候補の正本は observations 側に置く
- pipeline は candidate 判定、writer は bridge shape、Preview は同 semantics 表示を担当する
- Preview / export は同じ semantics を維持する
- GUI 追加は行わず fixed policy とする
- MS12 へ広げない
