# MS11-9D-2 Implementation Plan

## Cross-vowel transition bridging

## 0. 位置づけ

MS11-9D-2 は、MS11-9D で導入した same-vowel micro-gap bridging の後続として、
**cross-vowel 遷移時の不自然な完全閉口**を抑えるための計画である。

本タスクは、以下を主対象とする。

- 発話中のごく狭い zero 区間をまたぐ cross-vowel 遷移
- 前母音が完全 0 に落ちる前に次母音の rise を始めるための transition semantics
- Preview / export の semantics alignment を崩さない範囲での cross-vowel bridge 導入

本タスクは、以下とは切り分ける。

- MS11-9D の same-vowel bridge そのもの
- MS11-9B / MS11-9C の final closing hold / softness
- 無音区間全般の再設計
- RMS 定数再調整そのもの
- MS12 の GUI responsiveness / splash / packaging

初回 MS11-9D-2 の固定方針:

- **cross-vowel のみを対象**とする
- `micro-gap` は **1 frame まで**を対象とする
- `peak_value == 0.0` の reason は、初回は
  - `no_peak_in_window`
  - `below_rel_threshold`
  のみを候補側として扱う
- GUI への新規 parameter 追加は行わず、固定 policy として扱う
- `timeline` は canonical writer input のまま維持する
- bridge 候補の正本は引き続き `observations` 側に置く
- observation 契約は same-vowel / cross-vowel を**別 bool**で持つ
- transition overlap は**最小 overlap のみ**を許可する
- overlap 時の値上限は、**次母音側をやや優先**する
- 極端に短い前後 event は**除外して fallback に逃がす**

---

## 1. 背景

MS11-9D 初回では、same-vowel の狭い zero micro-gap を
`timeline + observations` で bridge できるようにした。

一方、cross-vowel では same-vowel と異なり、
単に zero event を grouping から外すだけでは自然な見え方にならない。

理由は次のとおりである。

- same-vowel は「同じモーフの連続性」を保てば自然になりやすい
- cross-vowel は「別モーフへの遷移」そのものを shape として扱う必要がある
- そのため、前母音の fall と次母音の rise を少し重ねる transition semantics が必要になる

現状の `closing_hold_frames` / `closing_softness_frames` は final tail 専用であり、
cross-vowel 遷移のための仕組みではない。

したがって MS11-9D-2 では、
zero event の平均値上書きや zero-peak 全救済ではなく、
**cross-vowel transition bridging** として別責務で整理する。

---

## 2. 目的

MS11-9D-2 の目的は、発話中のごく狭い zero 区間をまたぐ cross-vowel 遷移で、
「一度完全閉口してから次モーフを開く」ように見えるケースを最小限に抑えることである。

本タスクの目的は次のとおり。

- cross-vowel 遷移専用の transition semantics を導入する
- `peak_value == 0.0` の全救済にはしない
- bridgeable な候補だけを対象にする
- same-vowel bridge と cross-vowel bridge を別ルールとして保つ
- Preview と export を同じ semantics で揃える
- final closing 系とは混ぜない

---

## 3. スコープ

### 3-1. 含める対象

- 発話中の cross-vowel micro-gap bridging 方針の導入
- bridgeable な cross-vowel transition candidate の最小判定
- cross-vowel 遷移用 shape semantics の追加
- Preview と writer の transition boundary alignment
- 必要最小限の pipeline-side candidate 判定導線

### 3-2. 含めない対象

- same-vowel bridge ルールの再設計
- final closing hold / softness の意味変更
- 無音区間全般の扱い変更
- `peak_value == 0.0` 全体の一律救済
- RMS reason 分類そのものの再定義
- GUI responsiveness / startup / splash / packaging
- GUI パラメータ追加

---

## 4. 非目標

今回やらないことを明確にする。

- `closing_hold_frames` / `closing_softness_frames` の再定義
- final closing family の再設計
- pipeline 上で zero-peak event を一律削除すること
- `global_peak_zero` / `rms_unavailable` / `below_abs_threshold` を bridge 対象へ広げること
- 2 frame 以上の gap を bridge 対象へ広げること
- Preview だけ先行して独自 transition 表示を入れること
- same-vowel bridge と cross-vowel bridge を同じルールに潰すこと

---

## 5. 基本方針

### 5-1. cross-vowel は same-vowel の単純拡張にしない

MS11-9D-2 では、cross-vowel を same-vowel bridge の延長として扱わない。

重要なのは次の点である。

- same-vowel は「同一モーフ継続」の問題
- cross-vowel は「別モーフへの遷移」の問題
- したがって zero event を外すだけでなく、遷移 shape 自体を再構成する必要がある

### 5-2. zero event を救済せず、transition を作る

MS11-9D-2 では、cross-vowel bridge 対象を
**前後 2 母音間の遷移問題**として扱う。

重要なのは次の点である。

- zero event を独立 peak event として持ち上げない
- zero event の `peak_value` を単純平均で直接上書きしない
- 前母音の fall と次母音の rise を少し重ねる transition shape として扱う
- bridge のための補助値が必要でも、それは transition 生成補助としてのみ使う

### 5-3. fixed policy を維持する

初回 MS11-9D-2 では GUI を増やさず、既存 GUI semantics を維持する。

- 最大 gap 幅は `1 frame`
- reason は `no_peak_in_window` / `below_rel_threshold`
- GUI 追加なし
- observations 無し経路では bridge 無効

---

## 6. 既存構造との整合

### 6-1. current workspace の前提

現時点で確認できる前提は次のとおりである。

- pipeline は event を残したまま `peak_value` と reason を決める
- `VowelTimingPlan` / `PipelineResult` には optional な `observations` 契約がある
- MS11-9D 初回では `observations` が same-vowel bridge 候補の正本になっている
- writer は `peak_value <= 0.0` event を shape 非生成として扱う
- Preview は writer helper を再利用して family / bridge semantics を再構成している
- `closing_hold_frames` / `closing_softness_frames` は final tail だけを扱う

### 6-2. 現行仕様と衝突しやすい点

MS11-9D-2 で衝突しやすいのは、次の点である。

1. cross-vowel でも same-vowel と同じ envelope grouping で済ませようとすること
2. zero-peak を全面救済する方向へ広げること
3. final closing semantics と speech-internal transition semantics を混ぜること

したがって本計画では、
cross-vowel transition を独立ルールとして扱い、
zero-peak 全救済へ広げず、
final closing 系とは別責務で保つことを固定する。

### 6-3. 契約方針

MS11-9D-2 でも、
**timeline は canonical writer input として維持し、bridge 候補の正本は observations 側に置く**。

採用方針:

- `timeline point に持たせる` は採用しない
- `writer / preview に渡す別 metadata 契約を新設する` は初回では採用しない
- **`observations 側で持たせる` を採用する**

理由:

- MS11-9D 初回ですでに `observations` を正本として使っている
- cross-vowel 判定も `peak_value == 0.0` の reason と前後文脈に依存し、pipeline observation の意味領域に近い
- 初回 MS11-9D-2 は `cross-vowel / 1 frame / fixed policy` に限定されるため、observations 最小拡張で十分と考えられる
- 新規 metadata 契約は、より広い transition family を扱う段階まで増やさないほうが自然である

---

## 7. 責務分割

## 7-1. pipeline

主責務:

- `peak_value == 0.0` event のうち、cross-vowel transition candidate になりうるものを判定する
- 既存 reason 分類を破壊せず、transition 判定に必要な最小情報を observation に持たせる
- 「前後に別母音の non-zero event があり、狭い発話内部 gap であること」を event 文脈として判断する

想定方針:

- candidate 判定は、reason、前後 non-zero event、gap 幅、母音差異に基づく
- zero-peak 自体を non-zero event に書き換えない
- canonical writer input である timeline を再設計しない

初回固定:

- 最大 gap 幅は `1 frame`
- reason は `no_peak_in_window` / `below_rel_threshold` のみを候補側とする
- 前後母音が異なることを条件にする
- 先頭 / 末尾 / final closing 相当位置は除外する

初回実装の具体方針:

- `PeakValueObservation` に、cross-vowel transition candidate を識別できる最小情報を追加する
- same-vowel / cross-vowel は別 bool として保持し、初回は最小拡張で済ませる
- `timeline` 自体の `peak_value` は書き換えない

未確認事項:

- 既存の `previous_non_zero_event_index` / `next_non_zero_event_index` だけで十分か

## 7-2. writer

主責務:

- cross-vowel candidate を独立 peak event として立てず、遷移 shape として扱う
- 前母音の fall と次母音の rise を少し重ねる
- same-vowel bridge と別ルールで管理する

想定方針:

- cross-vowel bridge は valley ではなく、cross-fade に近い transition を優先する
- 前母音を 0 に落とし切る前に、次母音の rise 開始を許容する
- ただし overlap は最小に留め、両側を同時に大きく開きすぎる設計は避ける
- overlap 時は前後を対等にせず、次母音側をやや優先する

初回実装の具体方針:

- writer は `timeline + observations` を同時に見て、event index 対応で cross-vowel candidate を参照する
- candidate 区間では、前母音側の終端 control point と次母音側の開始 control point を再配置して transition を作る
- observations が無い経路では、MS11-9D-2 bridge は無効として現行互換とする

未確認事項:

- transition overlap の具体 frame 配置
- fallback へ落とす最短 event 長条件

## 7-3. Preview

主責務:

- writer と同じ transition boundary で shape を表示する
- cross-vowel transition semantics を writer と同様に再構成する
- Preview だけ独自の transition 補間を発明しない

想定方針:

- 既存どおり writer helper 再利用を優先する
- shape semantics は frame basis、描画 API は seconds basis を維持する

初回実装の具体方針:

- Preview も `timeline + observations` を参照し、writer と同じ event index 対応で cross-vowel candidate を解決する
- observations が無い経路では、現行 Preview semantics を維持する

## 7-4. GUI

主責務:

- 原則として追加 GUI を前提化しない
- 既存 `current_timing_plan.timeline / observations -> build_preview_data(...) -> Preview` handoff を維持する

初回固定:

- GUI 追加なし
- fixed policy

---

## 8. bridgeable 候補の考え方

### 8-1. 候補化の方向性

cross-vowel transition candidate は、
**bridgeable な微小ギャップだけ**を対象にする。

候補側とする方向:

- `no_peak_in_window`
- `below_rel_threshold`

原則として候補外寄り:

- `global_peak_zero`
- `below_abs_threshold`
- `rms_unavailable`

### 8-2. 最低条件

少なくとも次を満たす場合に限る。

- 対象 event の `peak_value == 0.0`
- 前後に non-zero event がある
- 前後母音が異なる
- gap が `1 frame` 以内
- 発話先頭 / 発話末尾 / final closing ではない

### 8-3. 除外方針

次は初回では除外寄りとする。

- 前後どちらかの event が極端に短いケース
- gap が 2 frame 以上あるケース
- 無音寄りと判断しやすいケース
- same-vowel と cross-vowel の両条件が曖昧に競合するケース

---

## 9. shape の方向性

### 9-1. same-vowel との違い

same-vowel は valley / continuity を優先したが、
cross-vowel は **transition overlap** を優先する。

したがって、初回 MS11-9D-2 では次の方向を採る。

- 前母音を完全 0 に落とす前に減衰を始める
- 次母音を完全閉口後ではなく、少し前倒しで rise させる
- ただし二重開口が過大に見えないよう、transition は最小限に留める
- overlap 時は次母音側をやや優先し、次の発音へ移る見え方を優先する

### 9-2. 補助値の扱い

必要なら前後 peak から補助値を作ってよいが、
それは **transition shape の補助値**としてのみ使う。

除外する方針:

- zero event の `peak_value` 自体を書き換えること
- zero event を新しい独立 peak として export すること

---

## 10. Preview / export 整合方針

MS11-9D-2 でも、Preview と export は同じ semantics を維持する。

固定方針:

- Preview だけ独自 transition を表示しない
- writer と Preview は同じ candidate 情報を参照する
- candidate 解決は event index 対応で揃える
- observations 無し経路では、両方とも bridge 無効で現行互換にする

---

## 11. 最低限のテスト観点

### 11-1. pipeline

- cross-vowel / `1 frame` / `no_peak_in_window` で candidate 化される
- cross-vowel / `1 frame` / `below_rel_threshold` で candidate 化される
- same-vowel では cross-vowel candidate にならない
- `below_abs_threshold` / `global_peak_zero` / `rms_unavailable` では candidate 化されない
- 先頭 / 末尾 / final closing 相当では candidate 化されない

### 11-2. writer

- cross-vowel candidate があるとき、完全閉口を挟まず transition が作られる
- zero event を独立 peak として生成しない
- observations 無し経路では現行互換
- same-vowel bridge 実装と干渉しない

### 11-3. Preview

- Preview が writer と同じ transition boundary を表示する
- Preview / export の event index 対応が一致する
- observations 無し経路では現行 Preview と同じになる

### 11-4. handoff

- `main_window` から `timeline + observations` が Preview へ一貫して渡る
- pipeline → writer handoff で observations が維持される

---

## 12. スコープ外

今回の MS11-9D-2 では次をスコープ外とする。

- same-vowel bridge ルールの再整理
- 2 frame 以上の cross-vowel gap 対応
- GUI パラメータ化
- RMS 定数再調整
- 無音判定ロジック全体の再設計
- MS12

---

## 13. 未確認事項

現時点で未固定の項目は次のとおり。

- transition overlap の具体 frame 配置
- same-vowel / cross-vowel bool の具体 field 名
- `no_peak_in_window` と `below_rel_threshold` を同一 transition family で扱えるか
- 極端に短い前後 event の fallback 条件

---

## 14. 到達イメージ

MS11-9D-2 完了時の到達イメージは次のとおり。

- cross-vowel の狭い zero micro-gap で、完全閉口してから次モーフを開く見え方が減る
- same-vowel bridge と cross-vowel transition が別責務で整理される
- Preview / export が同じ transition semantics を使う
- timeline を汚さず、observations を正本としたまま拡張できる

---

## 15. 要約

MS11-9D-2 は、
**cross-vowel を same-vowel の単純拡張として扱わず、transition bridging として独立に扱う**
ための計画である。

初回固定方針は次のとおり。

- cross-vowel のみ
- `1 frame` まで
- reason は `no_peak_in_window` / `below_rel_threshold`
- timeline はそのまま維持
- bridge 候補の正本は observations 側
- same-vowel / cross-vowel は別 bool
- overlap は最小のみ
- 値上限は次母音側をやや優先
- 極短 event は除外して fallback
- GUI 追加なし
- Preview / export 整合を維持
