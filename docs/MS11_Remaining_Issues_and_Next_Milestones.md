# MS11 Future Milestones Plan

- Project: MMD_AutoLipTool
- Scope: MS11-4 実装反映後の残課題整理と、次期マイルストーン更新
- Date: 2026-03-30
- Status: MS11-5 第一段階反映後の残件整理

---

## 1. 目的

本ドキュメントは、MS11-3 完了後に整理した問題群を起点として、  
2026-03-30 時点の **MS11-5 第一段階反映後の到達状態** と **MS11-5 以降へ残る課題** を整理することを目的とする。

MS11-1 / MS11-2 / FIX01 / FIX02 / MS11-3 により、`writer.py` 側の形状生成・正規化・保護・fallback の整合性は大きく改善された。  
さらに 2026-03-29 時点で MS11-4 を反映し、`pipeline.py` 側でも **RMS 補正後 interval を正本にした peak 評価**、**halo 付き peak window**、**保守的 fallback**、**`peak_value = 0.0` 理由分類** まで導入済みである。  
そのため、現時点の主残課題は、MS11-4 未着手項目ではなく **実データ観測・必要最小限の定数再調整判断・MS11-5 の残り整理** に寄っている。

## 1-1. MS11-4 反映後の要点

- `pipeline.py` の `peak_value` 評価は、RMS 補正後 interval を正本として扱う。
- peak 探索は event interval 自体を変えず、halo `±0.03 sec` を加えた peak window で行う。
- halo は隣接する RMS 補正後 interval 端点の中点でクリップし、隣接 event から peak を借りる設計にはしない。
- `load_rms_series()` 失敗時は `upper_limit * 0.25`、`global_peak <= 0.0` 時は全 event `peak_value = 0.0` とする保守的分岐へ変更済み。
- event 自体は削除せず、interval を維持したまま `peak_value` と理由分類の整合を改善する方針を維持している。
- `peak_value = 0.0` 理由は、`rms_unavailable / global_peak_zero / no_peak_in_window / below_abs_threshold / below_rel_threshold` の優先順で内部追跡可能になっている。

---

## 2. 現時点の到達状態

### 2-1. writer 側で到達済みの内容
現時点で、少なくとも以下は到達済みとみなす。

- MS11-1: writer 後段正規化基盤
- MS11-2: 4点の非対称・単一上辺台形
- MS11-2_FIX01: 許容外非ゼロ除去 / 不要ゼロ prune
- MS11-2_FIX02: 発話イベント内部 shape collapse の主要改善
- MS11-3: 同一母音近接イベント群の multi-point shape、MS11-2 → legacy fallback、envelope 全体保護
- MS11-3 追補修正: 全ゼロ台形残存の抑止、短 fallback shape の不必要消失対策

### 2-2. 現時点の基本評価
`writer.py` 側の主要問題は概ね収束しており、残る主問題は **前段の event / interval / peak 割当品質** にあると整理する。

---

## 3. 現時点で残っている問題

## 3-1. 問題A: halo 導入後もなお、当該母音イベントの `peak_value` が 0.0 になるケース
現行 `pipeline.py` は、RMS 補正後 interval を正本としつつ、halo `±0.03 sec` と隣接中点クリップを適用した peak window 内で local peak を取り、その event の `peak_value` を決定する。  
そのため、MS11-4 以前よりは改善しているが、ユーザー視点では近くに十分高い波形が見えていても、その peak が当該 peak window の外であれば、その event は `peak_value = 0.0` になりうる。

この問題は `writer.py` 局所修正では解決せず、**event interval 割当と peak 抽出の品質問題** として扱う必要がある。

## 3-2. 問題B: 無音に見える区間に開口キーが残るケース
代表例として、`お` の 419〜427 frame 付近のように、ユーザーの聴感上は無音に見える区間でも、内部的には有効母音イベントとして残り、結果として VMD に開口キーが出る場合がある。

この問題は、現時点では `writer.py` 単独の不整合というより、

- テキスト由来の母音イベント割当
- 区間境界調整
- RMS ベース `peak_value` 付与
- 最小区間長の確保

などの前段処理に起因する可能性が高い。

## 3-3. 問題C: 原因切り分けに必要な debug 情報が不足している
現状では、生成時の `timeline` / `timing_plan` / RMS debug / event interval と実波形ピークの対応を、後から追跡しにくい。  
そのため、問題A / 問題B のような現象に対し、

- どの wave peak がどの event に属したか
- どの event が local peak 0.0 になったか
- どの段階で shape が落ちたか

を即座に特定しづらい。

---

## 4. 今後のマイルストーン定義

# MS11-4: Pipeline Event Quality Improvement

## 4-1. 状態
MS11-4 は **2026-03-29 時点で実装反映済み** とする。

## 4-2. 実装済み要点
- `pipeline.py` で、正本 interval と peak 探索窓の責務を分離
- RMS 補正後 interval を正本とし、peak 探索は halo `±0.03 sec` の peak window で実施
- halo は隣接する RMS 補正後 interval 端点の中点でクリップ
- `load_rms_series()` 失敗時は `upper_limit * 0.25`、`global_peak <= 0.0` 時は全 event `peak_value = 0.0`
- event を削除せず、interval を維持したまま `peak_value` と理由分類の整合を改善
- `rms_unavailable / global_peak_zero / no_peak_in_window / below_abs_threshold / below_rel_threshold` の理由分類追跡を internal helper / test 観測点で可能化

## 4-3. 確認済み効果
- 実波形ピークと event interval の見かけ上の不整合を減らす構造へ移行した
- 視覚的に近傍にピークがあるのに 0.0 になるケースに対し、halo 探索で改善余地を入れた
- 無音に見える event は削除せず、`peak_value = 0.0` 側へ倒す方針をコード上で固定した
- `writer.py` は追加再設計なしで既存導線を維持している
- pipeline 単体テストと pipeline-writer 連携回帰で主要ケースを確認済み

## 4-4. 残りの確認項目
- 実データ上で、理由分類ごとの発生傾向を蓄積すること
- halo 導入後もなお残る `peak_value = 0.0` 事例を観測し、必要なら最小限の RMS 定数補正を判断すること
- `no_peak_in_window` / `below_abs_threshold` / `below_rel_threshold` の発生分布を MS11-5 の観測支援と結び付けること

## 4-5. 非対象
- GUI / Preview 改修
- `writer.py` 全面再設計
- MS11-3 multi-point shape 自体の再設計
- 音声解析エンジンの全面刷新

---

# MS11-5: Pipeline Debug / Inspection Support

## 5-1. 目的
MS11-4 以降の品質改善や不具合切り分けを容易にするため、  
**event / interval / peak / RMS の対応を追跡可能にする debug 導線** を整備する。

## 5-2. 主対象
- `src/core/pipeline.py`
- 必要なら debug 出力用補助モジュール
- 必要なら最小限の関連テスト

## 5-3. 主な論点
- 各 event の `start_sec / end_sec / time_sec / peak_value` の確認手段
- 元 interval と RMS 補正後 interval の対応確認手段
- peak window / local peak / global peak / `reason` の確認手段
- 「どの peak がどの event に帰属したか」の説明単位整理
- 問題再現時の最小観測手段

## 5-4. 期待する改善内容
- 問題A / 問題B の個別事例を、推測ではなく具体的に切り分けられる
- 修正前後の event interval / peak 割当差分を比較しやすくなる
- 今後の pipeline 品質改善を、感覚ではなく観測可能な情報で進められる
- ユーザー確認と開発側調査の往復コストを下げられる

## 5-4-1. 2026-03-30 時点の反映済み事項

- `pipeline.py` に、既存 `PeakValueEvaluation` を維持したまま上位観測レコード `PeakValueObservation` を追加済み
- event 単位で、元 interval / RMS 補正後 interval / peak window / `local_peak` / `global_peak` / `peak_value` / `reason` / fallback 情報 / window sample 数を返す internal observation helper を追加済み
- `tests/test_pipeline_peak_values.py` に、観測値整合を確認する単体テストを追加済み
- `tests.test_pipeline_peak_values` 14 件、`tests.test_pipeline_and_vmd` 6 件、`tests.test_vmd_writer_peak_value` 4 件の回帰確認を通過済み

## 5-5. 非対象
- 本番 GUI への大規模常設表示
- VMD 出力仕様そのものの変更
- `writer.py` の shape ロジック変更

## 5-6. なお残る主課題

- 実データ上の `peak_value = 0.0` 事例を理由別に整理すること
- RMS 定数再調整要否の判断整理
- 必要に応じた複合ケース観測テストの追加整理

---

## 6. 優先順位

現時点の優先順位は次の通りとする。

1. **MS11-5**
   - 理由: MS11-4 で導入した理由分類と internal helper を土台に、実データ観測と切り分け効率を上げる次段階だから

2. **MS11-4 残調整**
   - 理由: 構造修正後も必要であれば、RMS 定数の必要最小限の再調整を実データに基づいて判断するため

3. **writer / GUI 側の追加改修**
   - 理由: 現時点では主戦場ではなく、MS11-4 / MS11-5 の確認結果を見てから必要性を判断すべきため

ただし、MS11-5 は GUI 常設表示ではなく、internal helper / test 観測点を起点に最小限で進める前提を維持する。

---

## 7. 現時点で維持する既知課題の扱い

以下は、MS11-4 反映後も **なお観測・再確認が必要な課題** として維持する。

- 実データ上で、halo 導入後もなお残る `peak_value = 0.0` 事例の有無
- 無音に見える区間が、意図どおり `peak_value = 0.0` 側へ寄っているかの観測蓄積
- `no_peak_in_window` / `below_abs_threshold` / `below_rel_threshold` の分布把握
- RMS 定数を据え置いたままで十分か、最小限の再調整が必要かの判断

これらは、MS11-4 が未完了という意味ではなく、  
**MS11-4 実装後の実データ確認と MS11-5 の観測強化で扱う残課題** として整理する。

---

## 8. まとめ

現時点の到達点は、**writer 側の shape / fallback / protection / cleanup は概ね収束済み** であり、  
`pipeline.py` 側でも **MS11-4 の構造修正は反映済み** と整理できる。

そのうえで、次に主に進める対象は以下とする。

- **MS11-5: Pipeline Debug / Inspection Support**
- **MS11-4 の残調整判断（必要時のみ）**

以後は、`writer.py` 再設計へ戻るのではなく、  
前段品質の実データ観測と最小限の微調整を中心に進める。
