# MS11-7 Real Data Observation Review

## 0. 文書情報

- 文書名: `docs/MS11-7_Real_Data_Observation_Review.md`
- 対象マイルストーン: `MS11-7`
- 用途:
  - 実データ observation review の正本
  - `peak_value = 0.0` 事例の reason 別整理
  - RMS 定数再調整要否判断の根拠記録

---

## 1. 運用方針

- この文書は、**実データ review の主記録**として用いる。
- `peak_value = 0.0` を一律に不具合扱いしない。
- 問題視するのは、**同種の不自然な zero case が複数回確認された場合**のみとする。
- この段階では、`_RMS_THRESHOLD_RATIO`、`_RMS_ABS_MIN_THRESHOLD`、`_PEAK_WINDOW_HALO_SEC` などの**定数変更そのものは記録対象外**とする。
- review の主対象は main flow 由来の `observations` とし、provided timing plan 経路は原則として主記録対象にしない。

---

## 2. 最終判断サマリ

- 現時点の最終判断: `保留`
- 判断日: `YYYY-MM-DD`
- 判断者:
- 対象データ範囲:
- 根拠要約:
  - reason 別件数:
  - 不自然 zero case の累積状況:
  - 再調整候補として数えた事例数:
- 結論:
  - `再調整不要`
  - `再調整候補あり`
  - `保留`

---

## 3. review 手順メモ

1. 通常 main flow で `build_vowel_timing_plan()` または `generate_vmd_from_text_wav()` を通す。
2. `observations` から `peak_value = 0.0` の event を抽出する。
3. 各 event を本書の個別記録テンプレートへ転記する。
4. 人手所見として、妥当 / 不自然 / 保留を記録する。
5. 同種事例の累積状況を更新する。
6. 単発ではなく、**同種の不自然 zero case が複数回あるか**を見て最終判断を更新する。

---

## 4. reason 別集計

| reason | 件数 | 不自然 zero case 件数 | 再調整候補として数えた件数 | 備考 |
| --- | ---: | ---: | ---: | --- |
| `rms_unavailable` | 0 | 0 | 0 |  |
| `global_peak_zero` | 0 | 0 | 0 |  |
| `no_peak_in_window` | 0 | 0 | 0 |  |
| `below_abs_threshold` | 0 | 0 | 0 |  |
| `below_rel_threshold` | 0 | 0 | 0 |  |

---

## 5. 同種事例の累積状況

| 類型ID | reason / 傾向 | 累積件数 | 不自然判定件数 | 再調整候補として数えるか | 備考 |
| --- | --- | ---: | ---: | --- | --- |
|  |  | 0 | 0 | `未判定` |  |

---

## 6. 個別記録テンプレート

### Case Template

- 対象データ識別子:
- event index:
- vowel:
- `time_sec`:
- initial interval:
  - start:
  - end:
- refined interval:
  - start:
  - end:
- peak window:
  - start:
  - end:
- local peak:
- global peak:
- `peak_value`:
- `reason`:
- `fallback_reason`:
- `window_sample_count`:

#### 人手所見

- 妥当な zero case か:
- 不自然な zero case か:
- 再調整候補として数えるか:
- 所見メモ:

#### 同種事例の累積状況

- 類型ID:
- 同種累積件数:
- 同種の不自然 zero case 累積件数:
- 現時点の傾向:

#### 最終判断

- `再調整不要`
- `再調整候補あり`
- `保留`
- 判断理由:

---

## 7. 個別記録

### Case 001

- 対象データ識別子:
- event index:
- vowel:
- `time_sec`:
- initial interval:
  - start:
  - end:
- refined interval:
  - start:
  - end:
- peak window:
  - start:
  - end:
- local peak:
- global peak:
- `peak_value`:
- `reason`:
- `fallback_reason`:
- `window_sample_count`:

#### 人手所見

- 妥当な zero case か:
- 不自然な zero case か:
- 再調整候補として数えるか:
- 所見メモ:

#### 同種事例の累積状況

- 類型ID:
- 同種累積件数:
- 同種の不自然 zero case 累積件数:
- 現時点の傾向:

#### 最終判断

- `再調整不要`
- `再調整候補あり`
- `保留`
- 判断理由:

---

## 8. 判断更新ログ

| 日付 | 更新内容 | 判定への影響 | 記録者 |
| --- | --- | --- | --- |
|  |  |  |  |
