# MS11-7_Implementation_Plan.md

## 0. 文書情報

- 文書名: `docs/MS11-7_Implementation_Plan.md`
- 対象マイルストーン: `MS11-7`
- 対象リポジトリ: `MMD_AutoLipTool`
- 前提到達版: `Ver 0.3.6.4`

### 0.1 実装反映注記（2026-04-01）

- MS11-7 は 2026-04-01 時点で、**文書整備と最小テスト追加まで**を反映済みとする。
- 反映済み:
  - `docs/MS11-7_Implementation_Plan.md` の固定スコープ化
  - `docs/MS11-7_Real_Data_Observation_Review.md` の追加
  - `tests/test_pipeline_peak_values.py` における `global_peak_zero` observation 境界テストの追加
- 未反映:
  - 実データ事例の記入
  - reason 別の累積整理
  - RMS 定数再調整要否の最終確定

### 0.2 前提完了マイルストーン

- MS10
- GUIFIX 系
- MS11-1
- MS11-2
- MS11-2_FIX01
- MS11-2_FIX02
- MS11-3
- MS11-3 後の `writer.py` 局所修正
- MS11-4
- MS11-5
- MS11-6

### 0.3 本プランの固定方針

- 今回の到達対象は **実データ observation 整理 + RMS 定数再調整の要否判断まで** とする
- **RMS 定数変更そのものは、本プランに含めない**
- この段階では **実データファイルを直接この文書内で固定せず**、観測手順・整理方法・判断基準を先に固定する
- 成果物は **Markdown 文書 + 必要最小限のテスト追加** とする
- 再調整候補とみなす条件は、**同種の不自然な zero case が複数回確認された場合** とする
- `pipeline.py` の新規観測 helper 追加、専用検証スクリプト追加、writer 再設計、GUI 拡張には広げない

---

## 1. MS11-7 の位置づけ

MS11-7 は、MS11-6 までで main flow から取得可能になった observation を用いて、**実データ上の `peak_value = 0.0` 事例を reason 別に整理し、現行 RMS 定数の再調整が必要かどうかを判断する段階**として扱う。

本マイルストーンの主目的は、既存構造を変更することではなく、**現行構造が実データ上でどこまで妥当かを確認し、必要なら次段で最小限の定数変更へ進む判断材料を揃えること**である。

この段階では、以下を維持する。

- `timeline` は引き続き canonical writer input のままとする
- writer 側の既存責務や shape 生成方針は変更しない
- GUI / Preview 側には広げない
- observation 取得経路は既存 main flow を利用し、新規 public API や専用 debug UI は追加しない

---

## 2. 現時点の確認済み前提

### 2.1 pipeline 側

現行 `pipeline.py` では、以下が既に成立している。

- `PeakValueEvaluation` は維持されている
- `PeakValueObservation` は higher-level observation として追加済み
- `_build_peak_value_observations()` が存在する
- `VowelTimingPlan` に optional な `observations` が追加済み
- `PipelineResult` にも `observations` が受け渡される
- `build_vowel_timing_plan()` は initial timeline を保持したうえで、refined timeline と observation を main-flow-connected に取得できる
- `generate_vmd_from_text_wav()` は provided timing plan 経路も含めて observation 方針が整理済みである
  - そのまま利用する provided plan は observation を保持しうる
  - duration 補完が入る provided plan は `observations=None` に落とす

### 2.2 zero case reason 分類

現行 `pipeline.py` では、`peak_value = 0.0` の主理由として少なくとも以下を区別している。

- `rms_unavailable`
- `global_peak_zero`
- `no_peak_in_window`
- `below_abs_threshold`
- `below_rel_threshold`

### 2.3 writer 側

現行 `writer.py` では、`peak_value` を優先使用しつつ、`peak_value == 0.0` の場合は zero-only shape を出さない前提が既にある。  
したがって、MS11-7 の中心は writer 側ではなく、**pipeline observation の整理と判断**に置く。

### 2.4 既存テスト

現行テストでは、少なくとも以下が確認済みである。

- reason 分類単体確認
- halo window の確認
- `rms_unavailable` fallback
- `global_peak_zero`
- main-flow observation 取得
- provided timing plan observation 方針
- writer 側の `peak_value == 0.0` zero-only shape 抑止

---

## 3. MS11-7 の目的

MS11-7 の目的は、次の 3 点に限定する。

1. 実データ上の `peak_value = 0.0` 事例を、既存 reason 分類に沿って整理できる状態にする
2. zero case が「現仕様上妥当な結果」か「RMS 定数再調整候補とみなすべき不自然事例」かを判定できる材料を揃える
3. その結果を根拠に、**RMS 定数再調整の要否だけを判断**する

ここでいう判断は、**変更実施そのものではなく、変更を次段へ持ち込む必要があるかどうかの判定**を指す。

---

## 4. スコープ

### 4.1 対象

- `src/core/pipeline.py` の既存 observation / reason 分類仕様の確認
- `tests/test_pipeline_peak_values.py`
- `tests/test_pipeline_and_vmd.py`
- 必要最小限の pipeline 系テスト追加
- 実データ review を整理する Markdown 文書

### 4.2 主対象

- `peak_value = 0.0` 事例の実データ review 手順の固定
- review 結果の整理形式の固定
- reason 別観測の整理
- 再調整要否判断基準の明文化
- 必要最小限のテスト反映

### 4.3 非対象

以下は MS11-7 の対象外とする。

- `pipeline.py` の新しい観測 helper 追加
- 専用検証スクリプト追加
- RMS 定数の値変更
- writer.py の再設計
- GUI / Preview 改修
- 大幅な RMS チューニング
- 出力仕様再設計
- GUI 常設 debug 表示
- Preview Area 常設 debug 表示

---

## 5. 成果物

MS11-7 の成果物は、最低限次の 2 つとする。

### 5.1 実データ review 文書

候補ファイル名:

- `docs/MS11-7_Real_Data_Observation_Review.md`

この文書には、少なくとも以下を含める。

- 対象データ識別子
- event index / vowel / `time_sec`
- initial interval
- refined interval
- peak window
- local peak
- global peak
- `peak_value`
- `reason`
- `fallback_reason`
- `window_sample_count`
- 人手所見
  - 妥当な zero case か
  - 不自然な zero case か
  - 再調整候補として数えるか
- 同種事例の累積状況
- 最終判断
  - 再調整不要
  - 再調整候補あり
  - 保留

### 5.2 必要最小限のテスト追加

追加する場合は、**実データそのものの記録ではなく、review で判明した境界条件の再発防止**を目的とする。

追加対象は、次の条件を満たすものに限定する。

- review で重要だった境界条件を人工データで安定再現できる
- 既存の reason 分類や main-flow observation 方針を壊さない
- 実データ依存の主観結果ではなく、仕様境界として固定する意味がある

### 5.3 関連文書の最小同期

必要に応じて、以下の文書へ最小限の同期を行う。

- `docs/repo_milestone.md`
- `docs/Version_Control.md`

ただし、今回の同期は **MS11-7 の文書追加と最小テスト追加の記録**に限定し、版数更新や release sync には広げない。

---

## 6. 実装方針

### 6.1 基本方針

MS11-7 では、**既存コードを極力変えずに、既存 observation 基盤を使って review を成立させる**。

主な整理先は Markdown とし、コード側は既存仕様の確認と必要最小限のテスト補強に留める。  
`pipeline.py` には既に reason 分類と observation 保持構造があるため、新規 helper 追加や API 拡張を前提にしない。

### 6.2 zero case の解釈方針

`peak_value = 0.0` は、それ自体を不具合とみなさない。  
少なくとも次のように扱う。

- `rms_unavailable`
  - RMS 非取得時の fallback 経路であり、原則として定数問題ではない
- `global_peak_zero`
  - 全体 RMS が 0.0 系であり、定数変更で解決すべきとは限らない
- `no_peak_in_window`
  - 窓内に RMS サンプルが無いケースであり、window 条件やサンプル配置の影響を含む
- `below_abs_threshold`
  - 絶対閾値未満
- `below_rel_threshold`
  - 相対閾値未満

このうち、**実際の聴感・波形印象に対して不自然な zero case が、同じ reason または同じ傾向で複数回確認された場合のみ、再調整候補**として扱う。

### 6.3 判断の姿勢

判断は次の順序で行う。

1. zero case を reason 別に整理する
2. reason と見た目 / 聴感の整合を見る
3. 単発ではなく、**同種の不自然事例が複数回あるか**を確認する
4. それでも定数問題が疑われる場合のみ、次段で再調整候補ありとする

この段階では、定数変更案そのものを決めない。

---

## 7. フェーズ分解

### フェーズ1: review 観点の固定

#### 目的

実データ review で何を記録し、何を判断材料とするかを固定する。

#### 作業

- review 文書の観測項目テンプレートを固定する
- zero case を
  - 妥当
  - 不自然
  - 保留
  に分ける記録欄を固定する
- 再調整候補に数える条件を固定する

#### 到達条件

- 実データをまだ投入していなくても、観測記録の書式が確定している

---

### フェーズ2: 既存観測基盤の参照手順固定

#### 目的

既存 code path だけで review を進められる手順を固定する。

#### 作業

- `build_vowel_timing_plan()` / `generate_vmd_from_text_wav()` から `observations` を参照する review 手順を整理する
- review の主対象は通常 main flow とする
- provided timing plan 経路は、本マイルストーンの実データ review 主経路には含めない方針を明記する

#### 到達条件

- review の観測元が main flow で一貫する

---

### フェーズ3: real-data review 文書の作成

#### 目的

実データ review を記録する正本文書を作成する。

#### 作業

- `docs/MS11-7_Real_Data_Observation_Review.md` を追加する
- 事例記録表を作る
- reason 集計欄を作る
- 「同種の不自然 zero case が複数あるか」を判断できる欄を作る
- 最終結論欄
  - 再調整不要
  - 再調整候補あり
  - 保留
  を用意する

#### 到達条件

- review を継続記録できる文書雛形が成立している

---

### フェーズ4: review 結果を受けた最小テスト追加

#### 目的

review で判断材料となった境界条件だけを固定する。

#### 作業

- 必要なら `tests/test_pipeline_peak_values.py` に 1～数件追加する
- main flow 観点が必要な場合だけ `tests/test_pipeline_and_vmd.py` に最小追加する
- 追加対象は、既存 reason 分類の延長で表現できるものに限定する

#### 到達条件

- review で重要だった境界条件が回帰しにくくなる

---

### フェーズ5: 要否判断の文書反映

#### 目的

RMS 定数再調整の要否を、Markdown 上で結論化する。

#### 作業

- 再調整不要 / 再調整候補あり / 保留 のいずれかで結論を記載する
- 結論の根拠を、zero case の総数ではなく
  - 同種不自然事例の複数確認有無
  - reason の偏り
  - 閾値近傍の反復
  の観点で整理する
- 必要なら `docs/repo_milestone.md` 等へ最小同期する

#### 到達条件

- MS11-7 の判断結果が文書として読める

---

## 8. 実データ review 手順

MS11-7 では、実データ review を次の流れで行う。

1. 通常 main flow で `build_vowel_timing_plan()` または `generate_vmd_from_text_wav()` を通す
2. `observations` を event 単位で確認する
3. `peak_value = 0.0` の event のみを抽出する
4. 各 event について以下を記録する
   - event index
   - vowel
   - `time_sec`
   - initial interval
   - refined interval
   - peak window
   - local peak
   - global peak
   - `peak_value`
   - `reason`
   - `fallback_reason`
   - `window_sample_count`
   - 人手所見
5. reason ごとに整理する
6. **同種の不自然 zero case が複数あるか**を確認する
7. その結果だけを、再調整候補ありの判断材料にする

---

## 9. 再調整要否の判断基準

### 9.1 再調整不要

次のいずれかに該当する場合。

- zero case は存在するが、reason と波形印象の整合が取れている
- 不自然に見える事例が単発で、再現性・反復性が弱い
- zero case の主因が `rms_unavailable` や `global_peak_zero` など、定数変更で扱うべきでない経路にある

### 9.2 再調整候補あり

次の条件を満たす場合。

- **同種の不自然な zero case が複数回確認される**
- その傾向が、reason・閾値近傍・window 条件などで一定のまとまりを持つ
- 構造問題というより、定数設定の厳しさ / 緩さが疑われる

### 9.3 保留

次のような場合。

- 不自然事例はあるが件数が不足している
- reason は同じでも、実データ条件がばらついている
- 定数問題と構造問題の切り分けがまだ不十分

---

## 10. テスト方針

既存テストの主目的は維持する。

- reason 分類単体確認
- halo window の確認
- `rms_unavailable` fallback
- `global_peak_zero`
- main-flow observation 取得
- provided timing plan observation 方針
- writer 側の `peak_value == 0.0` zero-only shape 抑止

MS11-7 で追加するテストは、次のようなものに限定する。

- review で問題視した境界条件を人工データで再現できるケース
- 「この条件では現仕様の reason でよい」と固定したいケース
- 「この条件は今後も保留扱い」とするための分離確認ケース
- observation 文書で使う主要欄
  - `global_peak`
  - `reason`
  - `fallback_reason`
  - `window_sample_count`
  の整合を最小限で固定したいケース

review 結果の件数集計や主観評価そのものは、テストへ持ち込まない。

---

## 11. 完了条件

MS11-7 は、次の条件を満たしたとき完了扱いとする。

1. 実データ review の記録用 Markdown 文書が作成されている
2. `peak_value = 0.0` 事例を reason 別に整理できる
3. 不自然 zero case の有無と、その反復性を文書上で判断できる
4. RMS 定数再調整の要否が
   - 不要
   - 候補あり
   - 保留
   のいずれかで文書化されている
5. 必要なら、境界条件を固定する最小限のテストが追加されている
6. `pipeline.py` の新規観測導線追加や RMS 定数変更には広がっていない
7. writer.py や GUI 側へスコープ逸脱していない

---

## 12. 実装時の注意

- `peak_value = 0.0` を一律に不具合扱いしないこと
- 単発事例だけで定数再調整判断に進まないこと
- 実データ review の主記録は Markdown に置くこと
- テストは「判断根拠になった境界条件」だけを最小追加すること
- `pipeline.py` の仕様変更を先に始めないこと
- writer / GUI / Preview へ広げないこと
- MS11-7 は **判断段階**であり、**変更段階**ではないことを崩さないこと

---

## 13. Codex への補足指示

- まず既存 `pipeline.py` と関連テストを読み、MS11-6 完了済み前提を崩さないこと
- 実装時は、既存 observation 導線を使い、新規 helper 追加や API 拡張を前提にしないこと
- 追加テストが必要な場合でも、review 結果の主観記録ではなく、人工データで再現可能な境界条件だけを固定すること
- review 文書は、後続の RMS 定数再調整判断にそのまま接続できる構成にすること
- まだこの段階では、RMS 定数変更そのものを実施しないこと
- スコープ外に触れる場合は止まり、ユーザーへ確認すること
