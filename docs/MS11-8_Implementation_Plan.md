# MS11-8_Implementation_Plan.md

## 0. 文書情報

- 文書名: `docs/MS11-8_Implementation_Plan.md`
- 対象マイルストーン: `MS11-8`
- 対象リポジトリ: `MMD_AutoLipTool`
- 前提到達版: `Ver 0.3.6.4` 系
- 主対象: `src/vmd_writer/writer.py`
- 関連テスト:
  - `tests/test_vmd_writer_peak_value.py`
  - `tests/test_vmd_writer_intervals.py`
  - `tests/test_vmd_writer_multipoint_shape.py`
  - `tests/test_vmd_writer_zero_guard.py`
  - `tests/test_vmd_writer_grouping.py`
  - 必要時のみ `tests/test_pipeline_and_vmd.py`

### 0.1 実装反映注記（2026-04-01）

- MS11-8 は 2026-04-01 時点で、**writer 主体の closing softness 実装と最小 handoff / 最小回帰テスト更新まで**を反映済みとする。
- 反映済み:
  - `src/vmd_writer/writer.py` に `closing_softness_frames: int = 0` を追加
  - `closing_softness_frames < 0` を不許可化
  - MS11-2 closing に対する `peak_end_frame` 固定 / `end_frame` 延長
  - `legacy_triangle` / `legacy_symmetric_trapezoid` に対する final closing 延長
  - MS11-3 multi-point shape に対する final `end_zero` のみの延長
  - 後続 shape 開始直前での clamp
  - 延長後 shape に追従した `protected_envelope_ranges` / `allowed_non_zero_ranges` / `required_zero_frames` の整合維持
  - `src/core/pipeline.py` から `write_morph_vmd()` への最小 `closing_softness_frames` handoff
  - writer 系テストと `tests/test_pipeline_and_vmd.py` の最小回帰追加
- 未反映:
  - GUI 入力導線
  - Preview 表示整合
  - release sync / 版数更新
  - MS11-9 以降の後続整理

---

## 1. MS11-8 の位置づけ

MS11-8 は **mouth-closing softness control** を扱うマイルストーンである。

目的は、**口の閉じ始めから 0 へ落ちる区間の傾き**を、既存の morph max value とは独立した別パラメータで制御できるようにすることにある。

このタスクは GUI 専用ではなく、**writer 側の shape-generation 課題**として扱う。  
主責務は `writer.py` に置き、必要な場合のみ最小限の parameter handoff を追加する。

---

## 2. 現時点の前提整理

### 2.1 writer 側の現行 shape 系

現行 `writer.py` では、少なくとも以下の shape 系が存在する。

1. **MS11-2 系**
   - 4点の非対称・単一上辺台形
   - `start_frame`
   - `peak_start_frame`
   - `peak_end_frame`
   - `end_frame`

2. **legacy fallback 系**
   - legacy triangle
   - legacy symmetric trapezoid

3. **MS11-3 系**
   - multi-point envelope
   - `start_zero`
   - `top`
   - `valley`
   - `top`
   - `end_zero`
   - 必要に応じて top / valley が増える

### 2.2 現行の保護・cleanup 前提

現行 `writer.py` では、少なくとも以下が既に成立している。

- `peak_value <= epsilon` の場合、zero-only shape を出力しない
- 正規な short / legacy fallback shape は current normalization flow で不必要に消さない
- MS11-2 正規形状には保護導線がある
- MS11-3 成功 shape には envelope 単位の保護導線がある
- `allowed_non_zero_ranges`
- `protected_envelope_ranges`
- `required_zero_frames`
  などの metadata を使って後段整合を維持している

### 2.3 pipeline 側の前提

現行 `pipeline.py` では、`timeline` が canonical writer input のまま維持されている。  
したがって、MS11-8 の主変更点は pipeline ではなく writer に置く。  
ただし、softness 値を外部入力として使う場合は、parameter handoff を最小限で追加する余地がある。

---

## 3. MS11-8 で新規導入する設定概念

### 3.1 設定名

実装上の設定名:

- `closing_softness_frames`

最終的な変数名や引数名は、既存命名規則に沿って統一する。

### 3.2 値の意味

`mouth_closing_softness_frames` は、**closing 区間に追加するフレーム数**として扱う。

これは倍率ではなく、**frame units の加算値**である。

### 3.3 初期値

- 初期値は `0`

### 3.4 後方互換方針

- `0` 指定時は **無効**
- 指定なし、または `0` の場合は **現行出力と同等**にする

---

## 4. 適用対象の固定方針

### 4.1 対象に含めるもの

MS11-8 では、以下を対象に含める。

1. **MS11-2 / legacy fallback 系の closing 区間**
2. **MS11-3 multi-point shape の最終 closing 区間**

### 4.2 対象に含めないもの

今回の MS11-8 では、以下は対象外とする。

- rise 側の立ち上がり変更
- `peak_value` 算出の変更
- RMS 定数の変更
- Preview 表示変更
- GUI 応答性改善
- MS11-3 の中間 valley 周辺の各下降辺すべての再設計
- 出力仕様全体の再設計

---

## 5. closing softness の反映規則

### 5.1 基本規則

closing softness は、**fall-start を固定したまま、zero 到達位置を後ろへ延ばす**形で反映する。

つまり、現在の closing 区間が

- `fall_start_frame -> zero_frame`

である場合、softness 適用後は

- `fall_start_frame` は維持
- `zero_frame` を後方へ延長

する。

### 5.2 MS11-2 / legacy 系での解釈

#### MS11-2 / legacy trapezoid 系

現在の closing は、実質的に

- `peak_end_frame -> end_frame`

の区間で表現されている。

したがって、softness は原則として

- `peak_end_frame` は固定
- `end_frame` を延長

として扱う。

#### legacy triangle 系

triangle では closing は実質的に

- `peak_frame -> end_frame`

の区間である。

したがって、softness は原則として

- `peak_frame` は固定
- `end_frame` を延長

として扱う。

### 5.3 MS11-3 系での解釈

MS11-3 multi-point shape では、今回の softness 対象は **最終 closing 区間のみ**とする。

すなわち、最後の non-zero control point から `end_zero` までの区間に対して

- 最後の non-zero point は固定
- `end_zero` を後ろへ延長

する。

中間 valley 後の各下降辺は、今回の MS11-8 では変更対象にしない。

---

## 6. 境界条件とクランプ方針

### 6.1 基本方針

追加した closing は、**後続イベントや後続グループにぶつかる前でクランプ**する。

softness 指定値を常に優先して重なりを発生させる方針は採らない。

### 6.2 クランプ対象

少なくとも以下に対して、後方延長を制限する。

- 後続の単発イベント
- 後続の同一母音グループ
- 後続の別母音イベント
- 現行保護範囲・許容範囲の整合を崩す境界

### 6.3 クランプ結果

- 指定 softness をすべて反映できない場合があってよい
- ただし、その場合でも shape は破綻しないこと
- event / group 境界より先へ無制限に非ゼロを伸ばさないこと

---

## 7. 実装責務の分割方針

### 7.1 writer 側で扱うもの

`writer.py` 側で扱うもの:

- softness 設定値の解釈
- closing 区間の frame 延長
- MS11-2 / legacy / MS11-3 final closing への適用
- metadata との整合
- 後段 normalization と両立する frame 配置

### 7.2 pipeline 側で扱うもの

必要な場合のみ、pipeline 側では次を扱う。

- softness 値の writer への最小 handoff

それ以外の以下は扱わない。

- peak 評価ロジック変更
- observation 仕様変更
- RMS 再調整
- writer shape 生成の主責務移動

### 7.3 GUI 側で扱わないもの

この段階では GUI 側の以下は対象外とする。

- Preview 表示形状の変更
- multi-point Preview 表示
- 応答性改善
- splash / startup
- GUI 常設 debug 表示

---

## 8. 既存保護との整合方針

### 8.1 壊してはいけない既存保証

MS11-8 でも、少なくとも以下は維持する。

1. `peak_value == 0.0` 由来の zero-only shape を出力しない
2. 正規な short / legacy fallback shape を current normalization flow で不必要に消さない
3. MS11-2 正規形状の保護を壊さない
4. MS11-3 成功 envelope の保護を壊さない
5. `required_zero_frames` の境界ゼロ保証を壊さない

### 8.2 整合上の注意点

softness により `end_frame` または `end_zero` を動かす場合、少なくとも以下を同時に再確認する必要がある。

- protected range の終端
- allowed non-zero range の終端
- required zero frame の終端
- isolated short open suppression との相互作用
- short morph pulse suppression との相互作用
- duplicate merge / zero prune の最終結果

---

## 9. 変更対象候補

### 9.1 主変更対象

- `src/vmd_writer/writer.py`

### 9.2 主テスト更新対象

- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_peak_value.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_vmd_writer_zero_guard.py`

### 9.3 条件付き変更対象

- `src/core/pipeline.py`
- `tests/test_pipeline_and_vmd.py`

条件:
- softness を external parameter として pipeline から渡す場合のみ

---

## 10. テスト方針

### 10.1 最低限追加・更新すべき観点

#### A. MS11-2 / legacy 系

1. `softness=0` で現行 shape と完全同等
2. `softness>0` で `fall-start` は固定、`zero` 側だけ延長される
3. 後続イベントが近い場合、後続にぶつかる前でクランプされる
4. zero-only shape は引き続き出力されない
5. short fallback / legacy fallback が current normalization flow で消えない

#### B. MS11-3 系

1. `softness=0` で現行 multi-point shape と同等
2. 最後の non-zero point から `end_zero` までだけ延長される
3. 中間 valley / top は不変
4. 後続 group や別イベントにぶつかる前でクランプされる
5. envelope 保護が維持される

#### C. pipeline handoff 系（必要時のみ）

1. pipeline → writer に softness が渡る
2. 指定なし時は 0 と同等
3. provided timing plan 系の observation 方針を壊さない

### 10.2 既存テストの維持観点

- `test_peak_value_zero_does_not_emit_zero_only_shape`
- MS11-2 四点台形の基礎期待値
- MS11-3 valid / invalid / fallback 切替
- current normalization metadata flow
- short fallback 保護
- required zero / allowed range / protected range の整合

---

## 11. 非対象

MS11-8 の非対象は以下とする。

- Preview 側の trapezoid / multi-point 表示整合
- GUI での最終入力 UI 設計
- RMS 定数再調整
- pipeline observation 拡張
- GUI 応答性改善
- startup / splash 改善
- FFmpeg bundling
- 出力仕様全体の再設計

---

## 12. 完了条件

MS11-8 は、少なくとも以下を満たした時に完了扱いとする。

1. `mouth_closing_softness_frames` の設定概念が明文化されている
2. `softness=0` で現行出力と同等である
3. MS11-2 / legacy 系の closing に softness が適用できる
4. MS11-3 の最終 closing に softness が適用できる
5. 後続イベント / 後続グループ前で適切にクランプされる
6. zero-only shape 抑止を壊さない
7. short / legacy fallback 保護を壊さない
8. normalization metadata flow と整合する
9. writer 関連回帰テストが更新され、既存保証を維持できる
10. GUI / Preview / MS12 領域へスコープ逸脱していない

---

## 13. 実装時の固定判断メモ

本セッションで固定した判断は以下の通り。

- 適用範囲:
  - **MS11-2 / legacy fallback + MS11-3 の最終 closing**
- 値の意味:
  - **追加フレーム数**
- 反映位置:
  - **fall-start 固定 / zero 到達側を後ろへ延ばす**
- 境界条件:
  - **後続イベントや後続グループにぶつかる前でクランプ**
- 初期値:
  - **0 frame**
- 後方互換:
  - **指定なし / 0 では現行出力と同等**

---

## 14. 補足

現時点では、MS11-7 の文書同期は review 実施前段階の記述が残っている可能性がある。  
ただし、MS11-8 の責務整理自体は writer 中心で独立しており、この文書は **MS11-8 の事前整理と実装範囲固定**を目的とする。
