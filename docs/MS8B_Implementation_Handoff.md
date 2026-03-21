# MS8B Implementation Handoff

## 1. 文書目的

本書は、次セッションで MS8B 実装を開始する際の最優先参照資料である。  
MS8B の固定仕様、責務分割、境界条件、禁止事項を再確認し、実装判断のブレを防ぐことを目的とする。  
本書は実装前引継ぎとして作成した文書だが、2026-03-21 に実装反映済み注記を追記している。

---

## 2. 現在位置

- MS8A は完了済み。
- MS8B（Preview Area 静止表示導入）は完了済み。
- 本書の固定事項は、MS8B 実装結果と整合している。
- 次段階は MS8C 以降（再生同期系）であり、本書の対象外条件を維持する。

---

## 3. MS8B の目的

- Preview Area の静止表示導入。
- 処理実行後に `current_timing_plan.timeline` 由来データを使って表示する。
- Preview は右カラム下段に組み込む。
- 5段固定（`あ / い / う / え / お`）で表示する。
- 波形とは別ウィジェットとして扱う。
- MS8B では静止表示のみを対象とする。

---

## 4. 主対象ファイル

実装対象（MS8B 主対象）:

- `src/gui/main_window.py`
- `src/gui/preview_area.py`（新規追加）
- `src/gui/preview_transform.py`（新規追加）

必要に応じて参照する既存ファイル:

- `src/gui/waveform_view.py`
- `src/core/pipeline.py`
- `src/core/audio_processing.py`
- `src/core/__init__.py`
- `src/vmd_writer/writer.py`

---

## 5. 責務分割

### 5.1 `main_window.py`

持たせる責務:

- `current_timing_plan` の受け取り・保持・受け渡し
- `current_timing_plan.timeline` の取得
- Preview 用整形層への受け渡し
- 整形済みデータの Preview 表示側への受け渡し
- クリア / 無効化時の Preview 更新判断

持たせない責務:

- Preview 用重整形
- Preview 描画
- Preview 表示キャッシュの独立管理
- 再生同期管理

### 5.2 `preview_transform.py`

持たせる責務:

- `timeline` の受け取り
- Preview 用中間契約への変換
- 5段固定表示向け整形
- 空入力 / 不正入力 / 不正区間時にも契約を壊さない安全な空データ返却

持たせない責務:

- GUI 描画
- 状態判定
- 再生管理
- `pipeline.py` の既存ロジック変更

### 5.3 `preview_area.py`

持たせる責務:

- 5段固定表示
- 整形済みデータ受け取り
- 静止表示
- 空状態表示
- クリア表示

持たせない責務:

- `timeline` の直接解釈
- 重い整形
- `pipeline.py` 直接依存
- 状態判定
- 再生同期
- 共通カーソル
- Zoom
- スクラブ

### 5.4 `waveform_view.py`

- 既存の波形表示責務のまま維持する。
- Preview 表示責務は持たせない。

---

## 6. Preview 用データ契約

### 6.1 元データの正本

- Preview の元データは `current_timing_plan.timeline`。
- Waveform 用と Preview 用で別々のタイミング計画は作らない。
- `current_timing_plan` を Preview 側の唯一の正本として扱う。

### 6.2 中間契約（固定）

- `PreviewData`
  - `rows: list[PreviewRow]`
- `PreviewRow`
  - `vowel: str`
  - `segments: list[PreviewSegment]`
- `PreviewSegment`
  - `start_sec: float`
  - `end_sec: float`
  - `duration_sec: float`
  - `intensity: float`

固定条件:

- `rows` は常に 5 件固定
- 行順は `あ / い / う / え / お`
- 空行も保持する
- 座標系は秒ベース絶対値
- 0..1 正規化座標は使わない
- `duration_sec` は `end_sec - start_sec` と整合
- 強度値は `peak_value` → `value` → `0.0` の順で解釈
- `intensity` の上限は `1.0` 固定
- 空入力 / 不正入力 / データなし時は 5行固定の空データを返す

---

## 7. Preview クリア / 無効化方針

Preview クリア対象は「失敗時」だけでなく、**既存解析結果が無効になる全入口**とする。  
判断基準は「失敗したかどうか」ではなく、**解析結果が有効かどうか**とする。

少なくとも対象に含める入口:

- `_reset_text_analysis_state()` 相当
- `_reset_wav_load_state()` 相当
- `_refresh_waveform_morph_labels()` 相当の失敗 / 不成立分岐
- `_on_morph_upper_limit_changed()` 相当
- `current_timing_plan = None` に戻す既存経路
- 処理失敗時
- 入力不足時
- 再解析待ち状態へ戻す時
- TEXT 再読込時
- WAV 再読込時
- モーフ上限変更時

---

## 8. `suppress_warning=True` 復元方針

- Preview 表示キャッシュを独立保存 / 独立復元しない。
- `current_timing_plan` を復元後、その復元後状態を正本として Preview を再構成する。
- silent restore は通常の破壊的クリア導線と同一扱いにしない。
- 共通クリア導線を導入する場合でも、silent restore 途中で無条件に先行破壊しない。

---

## 9. UI 組み込み方針

- Preview Area は右カラム下段の既存プレースホルダ領域を組み込み先とする。
- 5段固定表示として成立させる。
- 処理成功後は `current_timing_plan.timeline` → Preview 用整形 → 静止表示 の流れとする。
- 未解析 / 失敗 / 入力不足 / 再解析待ち時は空状態 / クリア状態へ戻す。
- Preview Area を追加しても既存導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）を崩さない。

---

## 10. MS8B の対象外

- 再生同期
- 再生中カーソル
- 共通カーソル線
- Play / Stop 実機能
- Zoom
- スクラブ
- フレーム単位同期制御
- 30fps 本格表記対応
- 多言語化
- 設定永続化
- 出力品質拡張
- `pipeline.py` の既存タイミング計画ロジック変更
- `WaveformView` の責務変更
- Preview 独立状態キャッシュの導入
- 将来フェーズ向けの先回り設計

---

## 11. MS8B 完了条件

- 右カラム下段に Preview Area が組み込まれる
- Preview Area は 5段固定である
- 処理実行後に `timeline` 由来の整形済みデータが静止表示される
- `main_window.py` は整形責務を持たない
- `preview_transform.py` が整形責務を持つ
- `preview_area.py` が描画責務を持つ
- 未解析時・失敗時・再解析待ち時に Preview がクリアされる
- 既存導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）は崩れない
- Preview と Waveform が同じ `current_timing_plan.timeline` を元データとして使う
- `suppress_warning=True` の復元時にも Preview 表示整合が崩れない

---

## 11.1 実装反映状況（2026-03-21）

- 右カラム下段に `PreviewArea` を組み込み済み。
- `preview_transform.py` に `timeline -> PreviewData` 整形責務を集約済み。
- `main_window.py` は `current_timing_plan.timeline` を正本にした受け取り・受け渡し制御のみを保持。
- 解析結果無効化入口での Preview クリア導線を接続済み（失敗時限定ではない）。
- `suppress_warning=True` 導線で、復元後 `current_timing_plan` 正本から Preview 再構成する整合を反映済み。
- Preview 独立キャッシュは導入していない。
- `waveform_view.py` / `pipeline.py` の責務変更は行っていない。

---

## 12. 次セッション開始時の手順

1. 本書 `docs/MS8B_Implementation_Handoff.md` を最初に読む。  
2. 次に `docs/Specification_Prompt_v3.md`、`docs/repo_milestone.md`、`docs/Version_Control.md` を確認する。  
3. MS8C 以降へ進む場合は、MS8B 固定条件（責務分離・対象外）を維持する。  
4. 将来機能は持ち込まない。  
5. 実装判断で迷った場合は、本書の固定事項を優先する。  

---

## 13. 実装判断の優先順位

1. MS8B 追加固定指示  
2. MS8B 説明プロンプト  
3. 実装リスト8B  
4. `docs/Specification_Prompt_v3.md` のうち MS8B と矛盾しない部分  
5. 実コード確認結果  

---

## 14. 禁止事項

- `WaveformView` の責務変更を前提にしない
- `pipeline.py` の既存ロジック変更を前提にしない
- Preview の独立キャッシュを導入しない
- 将来機能を MS8B に持ち込まない
- MS8C 相当の要素を先取りしない
