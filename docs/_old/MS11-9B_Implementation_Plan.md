# MS11-9B Implementation Plan

## Closing Softness GUI exposure and preview/output handoff alignment

## 0. 目的

MS11-9B の目的は、MS11-8 で内部実装済みの `closing_softness_frames` を
GUI から操作可能にし、Preview 表示と export handoff の両方で
同じ現在値を使って一貫反映させることである。

本タスクは MS12 の一般 GUI 改善ではなく、
writer-side output semantics に接続する MS11 系の整合タスクとして扱う。

---

## 1. 固定事項

### 1-1. GUI 配置
- `モーフ最大値` の右横に配置する
- 同列・同系統の数値入力として見せる

### 1-2. GUI 名称
- 日本語: `閉口スムース`
- 英語: `Closing Smooth`

### 1-3. 単位表示
- 入力欄の右横に単位ラベルを常時表示する
- 日本語: `フレーム`
- 英語: `Frame`
- 単位はツールチップではなく通常表示で判別可能にする

### 1-4. 値仕様
- `int`
- `0` 以上
- default `0`
- 単位解釈は GUI / settings / Preview / export handoff のすべてで frame count に固定する

### 1-5. 値参照経路
- Preview 更新と export handoff は同じ単一の現在値参照経路を使う
- Preview 側と出力側で別々に値解決しない

### 1-6. 変更時挙動
- `閉口スムース` 変更時に `current_timing_plan` を破棄しない
- 再解析を走らせない
- Preview 再描画と settings 保存更新に留める

### 1-7. shape semantics 安全条件
- MS11-8 の意味を崩さない
- 開始側は固定し、終端 0 側のみ延長する
- zero-only closing shape を GUI 導入後も新規生成しない

### 1-8. 処理中ロック
- `モーフ最大値` と同等以上の一貫性を持たせる
- spinbox 本体だけでなく、必要なら `-` / `+` ボタンも含めて処理中変更不可にする

---

## 2. 主対象

### 2-1. 主変更対象
- `src/gui/main_window.py`
- `src/gui/central_panels.py`
- `src/gui/settings_store.py`
- `src/gui/i18n_strings.py`

### 2-2. 参照対象
- `src/gui/preview_transform.py`
- `src/gui/preview_area.py`
- `src/core/pipeline.py`
- `src/vmd_writer/writer.py`

### 2-3. テスト対象
- `tests/test_pipeline_and_vmd.py`
- `tests/test_preview_transform.py`
- GUI settings / main window 周辺の追加または更新テスト

---

## 3. 想定実装骨子

### A. GUI
- `MorphUpperLimitRow` を拡張するか、同責務 row 内で `閉口スムース` を追加する
- `閉口スムース [input] 単位` の並びを常時表示する
- `モーフ最大値` 側と視覚的整合を保つ

### B. settings
- UI settings key に `closing_softness_frames` を追加する
- startup restore / current settings / save / normalize / format を一式揃える

### C. Preview
- `build_preview_data(...)` への `closing_softness_frames` handoff を `main_window.py` から追加する
- 変更時は `current_timing_plan.timeline` を再利用し、再解析せず Preview のみ更新する

### D. export
- GUI の現在値を `generate_vmd_from_text_wav(..., closing_softness_frames=...)` に渡す
- pipeline / writer の意味自体は変更しない

### E. action lock
- 処理中は `閉口スムース` 入力一式を無効化する

---

## 4. 最低限のテスト観点

- `閉口スムース = 0` で現行互換
- 値変更で再解析が走らない
- Preview に GUI 値が反映される
- export 時に同じ GUI 値が `generate_vmd_from_text_wav(..., closing_softness_frames=...)` に渡る
- settings save / restore の round-trip
- 日本語 / 英語で単位表示が期待どおり出る

---

## 5. スコープ外

- MS12 領域
- writer semantics の再設計
- `preview_transform.py` / writer の不要な意味変更
- RMS 再調整
- より高度な smoothing 設計
