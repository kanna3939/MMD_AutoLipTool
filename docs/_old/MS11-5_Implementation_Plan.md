# MS11-5_Implementation_Plan.md

## 0. 文書情報

- 文書名: `docs/MS11-5_Implementation_Plan.md`
- 作成日: 2026-03-30
- 対象マイルストーン: `MS11-5`
- 対象リポジトリ: `MMD_AutoLipTool`
- 前提到達版: `Ver 0.3.6.2`
- 前提完了マイルストーン:
  - MS10
  - GUIFIX 系
  - MS11-1
  - MS11-2
  - MS11-2_FIX01
  - MS11-2_FIX02
  - MS11-3
  - MS11-3 後の `writer.py` 局所修正
  - MS11-4

### 0.1 実装反映注記（2026-03-30）

- MS11-5 は 2026-03-30 時点で第一段階を反映済みとする。
- 反映済み:
  - `PeakValueEvaluation` を維持したまま、上位観測レコード `PeakValueObservation` を追加
  - `pipeline.py` に event 単位の internal observation helper を追加
  - `tests/test_pipeline_peak_values.py` に観測値整合テストを追加
- 未反映:
  - 実データ観測結果の整理
  - RMS 定数再調整要否の判断整理
  - 必要に応じた複合ケース観測テストの追加整理

---

## 1. MS11-5 の位置づけ

MS11-5 は、`pipeline.py` 側で導入済みの MS11-4 構造を、**実データで説明可能な状態にするための観測支援マイルストーン**とする。

本マイルストーンの主目的は、出力仕様をさらに大きく変更することではない。  
MS11-4 で導入した以下の構造を、internal helper / test 観測点を通じて追跡・説明できる状態に整理することを主目的とする。

- RMS 補正後 interval を正本にした peak 評価
- halo `±0.03 sec` と隣接 interval 中点クリップによる peak window
- `load_rms_series()` 失敗時の低い固定値 fallback
- `global_peak <= 0.0` 時の全 event `peak_value = 0.0`
- `peak_value = 0.0` 理由分類
  - `rms_unavailable`
  - `global_peak_zero`
  - `no_peak_in_window`
  - `below_abs_threshold`
  - `below_rel_threshold`

MS11-5 は、**「実装を増やす段階」ではなく、「観測し、次の判断材料を揃える段階」**として扱う。

---

## 2. MS11-5 の目的

MS11-5 の目的は、次の3点に整理する。

1. 任意 event について、なぜその interval / peak window / peak_value / reason になったかを追跡可能にする。
2. 実データ上で `peak_value = 0.0` になった event の理由を再現可能にする。
3. 上記観測結果を根拠に、RMS 定数の必要最小限の再調整が必要か不要かを判断できる状態にする。

---

## 3. スコープ

### 3.1 対象

- `src/core/pipeline.py`
- `tests/test_pipeline_peak_values.py`
- 必要に応じて pipeline 系の追加テスト
- 必要に応じて観測結果整理用の md 文書

### 3.2 主対象

- event / interval / peak / RMS の観測支援
- internal helper の整理
- test 観測点の拡張
- 実データ観測結果を判断材料へ落とすための整理

### 3.3 非対象

以下は MS11-5 の対象外とする。

- `writer.py` の再設計
- GUI 常設 debug 表示
- Preview Area への debug 表示
- GUI / Preview の multi-point 表示対応
- より高度な平滑化
- 出力仕様全体の再設計
- MS11-4 で確定した peak 評価構造の大規模再変更
- 大幅な RMS 定数チューニング

---

## 4. MS11-5 の完了条件

MS11-5 は、次の条件を満たしたとき完了扱いとする。

1. 任意 event について、少なくとも以下を internal helper または test から取得できる。
   - 元 interval
   - RMS 補正後 interval
   - peak window
   - local peak
   - global peak
   - 最終 `peak_value`
   - `reason`
2. `peak_value = 0.0` の主要理由を、実データ上で再現確認できる。
3. halo と隣接中点クリップの挙動を、単体テストまたは観測 helper により説明できる。
4. `rms_unavailable / global_peak_zero / no_peak_in_window / below_abs_threshold / below_rel_threshold` を区別して追跡できる。
5. 実データ観測結果を踏まえ、RMS 定数の再調整が必要か不要かを判断できる。
6. GUI / Preview / writer へのスコープ外変更を持ち込まない。

---

## 5. 実装方針

### 5.1 基本方針

MS11-5 では、**本処理ロジックと観測導線を分離**する。  
既存の peak 判定構造に対して、本番処理の分岐を増やすのではなく、途中結果を安全に取り出せる internal helper を整備する。

### 5.2 変更方針

- `pipeline.py` の正本ロジックは可能な限り維持する。
- 観測のために、途中結果を保持・返却できる helper を追加する。
- 既存 GUI 導線には直接つながない。
- test から再利用できる内部契約を優先する。
- 実データ観測は、常設 UI ではなく helper / test / 文書整理で扱う。

### 5.3 期待する効果

- `peak_value = 0.0` の event を「何となく」ではなく理由付きで説明できる。
- peak window が halo / 隣接中点クリップでどう変化したかを追える。
- 構造問題か定数問題かを切り分けられる。
- RMS 定数を触るべきかどうかを、実データ観測に基づいて判断できる。

---

## 6. 実装対象の詳細

### 6.1 internal observation helper の導入

MS11-5 では、event 単位の観測値を返せる internal helper を導入する。

観測対象は最低限、以下を含むこと。

- event index
- vowel
- representative `time_sec`
- 元 interval
- RMS 補正後 interval
- peak window
- local peak
- global peak
- 最終 `peak_value`
- `reason`
- fallback 使用有無
- 隣接 event による中点クリップ結果

実装方法は任意だが、以下の原則を守ること。

- GUI 向けの public API にしない
- 本処理ロジックと観測用整形を分離する
- test から利用可能な単位で安定した契約を持つ
- `None` / 空系列 / fallback ケースでも安全に返せる

### 6.2 観測契約の整理

MS11-4 時点で `PeakValueEvaluation` は存在する。  
MS11-5 では、これを破壊的に置き換えず維持したまま、**`PeakValueEvaluation` を含む上位観測レコード `PeakValueObservation` を追加する方針**とする。

重要なのは、**実データ観測時に「その event がどう判定されたか」を一つの観測単位で扱えること**である。

2026-03-30 時点で、少なくとも以下は `PeakValueObservation` 側で保持する到達状態とする。

- event index
- vowel
- representative `time_sec`
- 元 interval
- RMS 補正後 interval
- peak window
- `local_peak`
- `global_peak`
- 最終 `peak_value`
- `reason`
- fallback 情報
- window 内 sample 数
- 既存 `PeakValueEvaluation`

### 6.3 peak 判定途中結果の可視化

最低限追えるようにすべき途中結果は次のとおり。

- `_event_interval()` により解決された interval
- `_build_peak_window()` により解決された window
- `_rms_samples_in_window()` により抽出された window 内サンプルの有無
- `local_peak`
- `global_peak`
- `_classify_peak_zero_reason()` の判定結果

本処理が複雑化しすぎる場合は、**観測用 helper が内部関数を組み合わせて結果を再構成する形**でもよい。  
ただし、本処理結果と観測結果の意味が乖離しないようにすること。

---

## 7. テスト方針

### 7.1 既存テストの維持

既存の以下観点は維持する。

- upper limit クランプ
- RMS 不可時 fallback
- `global_peak_zero`
- `upper_limit == 0.0`
- halo により interval 外ピークを拾えること
- `no_peak_in_window`
- `below_abs_threshold`
- `below_rel_threshold`
- `rms_unavailable` 優先
- `global_peak_zero` 優先

### 7.2 MS11-5 で追加する観点

MS11-5 では、単体理由判定だけでなく、**観測値の整合**を確認するテストを追加する。

追加候補は次のとおり。

1. 元 interval と RMS 補正後 interval を同時に確認できるケース
2. 隣接 event により peak window が左右でクリップされるケース
3. `peak_value = 0.0` が複数 event で連続するケース
4. `local_peak` は存在するが `below_abs_threshold` になるケース
5. `local_peak` は存在し abs threshold は超えるが `below_rel_threshold` になるケース
6. fallback 使用時に global peak 系の分岐へ入らないこと
7. 実データに近い複数 event 並列ケースで、各 event の観測結果が期待どおりになること

### 7.3 テストの目的

MS11-5 のテストは、出力 shape を直接変えるためではなく、**peak 判定過程の説明可能性を保証するため**に追加する。

---

## 8. 実データ観測の整理方針

### 8.1 目的

実データ観測では、`peak_value = 0.0` 事例を理由別に収集し、次の判断材料とする。

### 8.2 観測時に整理するべき項目

- 対象 WAV / TEXT
- event index / vowel / `time_sec`
- 元 interval
- RMS 補正後 interval
- peak window
- local peak
- global peak
- `peak_value`
- `reason`
- 備考
  - 無音に見える event か
  - 隣接強ピークの近傍か
  - 閾値境界に近いか
  - fallback ケースか

### 8.3 観測結果の使い道

観測結果は、次の判断に使う。

1. MS11-4 構造で十分か
2. RMS 定数の必要最小限の再調整が必要か
3. 次に進むべきは定数調整か、GUI / Preview 側整備か、それともより高度な平滑化か

---

## 9. RMS 定数再調整の扱い

MS11-5 では、大幅な RMS 定数チューニングは行わない。  
扱うのは、**観測結果に基づく必要最小限の再調整判断**までとする。

判断対象となる主な定数は以下。

- `_RMS_THRESHOLD_RATIO`
- `_RMS_ABS_MIN_THRESHOLD`
- `_PEAK_WINDOW_HALO_SEC`
- その他、MS11-4 で使用中の RMS 関連定数

ただし、原則は以下とする。

- 初手は定数調整ではなく観測性強化
- 観測結果に根拠がない段階で定数を動かさない
- 調整が必要な場合でも、最小差分に限定する
- 大幅チューニングや仕様再設計には広げない

---

## 10. 想定フェーズ分解

### フェーズ1: 観測対象の固定

- event ごとに何を観測値として扱うかを固定する
- 既存 `PeakValueEvaluation` の拡張方針または上位観測レコード追加方針を決める

### フェーズ2: helper 導線の整理

- `pipeline.py` 内で観測結果を返せる internal helper を追加する
- 本処理ロジックとの責務境界を整理する

達成状況（2026-03-30）:

- `pipeline.py` に `PeakValueObservation` と `_build_peak_value_observations()` を追加済み
- 既存 peak 評価結果を再利用して観測値を組み立てる構造で、本処理正本を置き換えない方針を維持済み

### フェーズ3: 単体テストの拡張

- 観測 helper を使ったテストを追加する
- 既存の理由分類テストを維持しつつ、途中結果整合テストを拡張する

達成状況（2026-03-30）:

- `tests/test_pipeline_peak_values.py` に、元 interval / RMS 補正後 interval、halo 窓と sample 数、`rms_unavailable` fallback 観測、initial timeline 長不一致のテストを追加済み

### フェーズ4: 複合ケースの検証

- 複数 event / 隣接 clip / 閾値境界ケースを追加する
- 実データに近いケースを test 観測点として整理する

残課題（2026-03-30）:

- 複数 event 並列ケースに対する観測 helper 主体の複合観点は、必要に応じて追加整理する

### フェーズ5: 実データ観測整理

- 実データ上の `peak_value = 0.0` 事例を理由別に整理する
- 必要最小限の RMS 定数再調整要否を判断する

### フェーズ6: 文書反映

- 到達状態
- 残課題
- RMS 定数再調整判断
- 次段階接続
を md 文書へ反映する

---

## 11. 実装時の注意

- `writer.py` の責務へ寄せないこと
- GUI 常設 debug 表示に広げないこと
- 既存の `build_vowel_timing_plan()` / `generate_vmd_from_text_wav()` の主要導線を壊さないこと
- 本処理の正本と観測 helper の意味が乖離しないようにすること
- テストしやすさのために helper を分けるのは可だが、観測専用コードが本処理を置き換えないこと
- 実データ観測前に定数調整へ進まないこと

---

## 12. 到達時に期待する成果物

MS11-5 完了時の成果物は、最低限次を想定する。

- `pipeline.py` 周辺の internal observation helper
- pipeline 系テストの拡張
- 実データ観測結果の整理
- RMS 定数再調整要否の判断整理
- 関連 md 文書の更新

---

## 13. MS11-5 完了後の接続整理

MS11-5 完了後の分岐先は、次のいずれかとする。

1. RMS 定数を必要最小限だけ再調整する
2. 定数再調整は不要と判断し、GUI / Preview の multi-point 表示対応へ進む
3. さらに高度な平滑化や出力仕様再設計の検討へ進む

ただし、MS11-5 自体は上記後続実装を含まない。  
MS11-5 は、**MS11-4 の構造修正を実データで説明可能にし、次の一手を判断可能にすること**をもって完了とする。
