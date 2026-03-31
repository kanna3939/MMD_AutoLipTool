# MMD_AutoLipTool GUI整備・機能拡張 マイルストーン一覧
## 2026-03-31 / Ver 0.3.6.3 同期メモ

- 対象: MS11-6 実装反映後の版同期
- 同期内容:
  - `pipeline.py` の main-flow-connected observation 接続、provided timing plan 経路の observation 方針、および関連テスト更新の反映状態を関連ドキュメントへ同期
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` の版数表記を `Ver 0.3.6.3` へ更新
  - リポジトリ全体の反映版を `Ver 0.3.6.3` として確定
- 確認状態:
  - `VowelTimingPlan` を正本とした optional observation 保持が main flow に接続済み
  - `timeline` を canonical writer input とする既存導線は維持済み
  - provided timing plan 経路は「そのまま利用時は observation 維持」「duration 補完時は `observations=None`」の方針をテストで明文化済み
- 次段階:
  - MS11-7: 実データ observation review と RMS 定数再調整判断

---

## 2026-03-31 / MS11-6 実装反映メモ

- 対象: MS11-6 `pipeline.py` 側 observation connection cleanup
- 実装反映:
  - `src/core/pipeline.py` で `VowelTimingPlan` に optional な `observations` を追加し、main flow から observation を参照可能化
  - refine 前 initial timeline と refine 後 timeline を main flow 内で対として追跡し、`PeakValueObservation` を構築する内部接続を追加
  - `PipelineResult` には optional な observation の受け渡しのみを追加し、writer handoff は引き続き `timeline` を canonical input として維持
  - provided timing plan をそのまま使う経路では observation を維持し、duration 補完を行った provided timing plan 経路では `observations=None` に落とす方針を整理
  - `tests/test_pipeline_and_vmd.py` に、main-flow-connected observation 取得確認と、provided timing plan 2 経路の observation 挙動確認を追加
- 確認状態:
  - `tests.test_pipeline_peak_values` 14 件が通過
  - `tests.test_pipeline_and_vmd` 8 件が `PYTHONPATH='src;tests'` 付きで通過
  - `tests.test_vmd_writer_peak_value` 4 件が通過
  - 上記の範囲で MS11-6 の主目的と残確認事項が収束している
- スコープ外として維持:
  - `writer.py` 再設計
  - GUI / Preview 改修
  - RMS 定数再調整

---

## 2026-03-30 / Ver 0.3.6.2 同期メモ

- 対象: MS11-5 観測支援反映後の版同期
- 同期内容:
  - `pipeline.py` の observation helper / observation record、および pipeline 系テスト拡張の反映状態を関連ドキュメントへ同期
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11-5_Implementation_Plan.md` の版数表記を `Ver 0.3.6.2` へ更新
  - リポジトリ全体の反映版を `Ver 0.3.6.2` として確定
- 確認状態:
  - MS11-5 第一段階の観測支援実装と関連テスト更新が反映済み
  - `writer.py` 再設計なしで pipeline 側観測性のみを拡張した状態を維持
  - 関連 docs は MS11-5 第一段階反映後の状態へ同期済み
- 残課題:
  - 実データ上の `peak_value = 0.0` 事例の理由別整理
  - RMS 定数再調整要否の判断整理
  - 必要に応じた複合ケース観測テストの追加整理

---

## 2026-03-30 / MS11-5 観測支援 実装反映メモ

- 対象: MS11-5 `pipeline.py` 側 observation helper / observation record / pipeline 系テスト拡張
- 実装反映:
  - `src/core/pipeline.py` に、既存 `PeakValueEvaluation` を維持したまま上位観測レコード `PeakValueObservation` を追加
  - event index / vowel / `time_sec` / 元 interval / RMS 補正後 interval / peak window / `local_peak` / `global_peak` / `peak_value` / `reason` / fallback 情報 / window sample 数をまとめて返せる internal helper を追加
  - 観測 helper は既存 peak 評価結果を再利用して構成し、本処理ロジックの正本を置き換えない方針で接続
  - `tests/test_pipeline_peak_values.py` に、元 interval と補正後 interval の同時確認、halo 窓と sample 数確認、`rms_unavailable` fallback 観測、initial timeline 長不一致の観点を追加
- 確認状態:
  - `tests.test_pipeline_peak_values` 14 件が通過
  - `tests.test_pipeline_and_vmd` 6 件が `PYTHONPATH='src;tests'` 付きで通過
  - `tests.test_vmd_writer_peak_value` 4 件が通過
  - 上記合計 24 件の回帰確認が通過
  - `writer.py` 再設計や GUI / Preview 改修なしで、pipeline 側観測性のみを拡張している
- 残課題:
  - 実データ上の `peak_value = 0.0` 事例の理由別整理
  - RMS 定数再調整要否の判断整理
  - 必要に応じた複合ケース観測テストの追加整理
- スコープ外として維持:
  - `writer.py` 再設計
  - GUI / Preview 改修
  - 大幅な RMS 定数チューニング

---

## 2026-03-29 / Ver 0.3.6.1 同期メモ

- 対象: MS11-4 実装反映、関連ドキュメント更新、周辺差分のリポジトリ同期
- 同期内容:
  - MS11-4 の `pipeline.py` 変更、pipeline 系テスト更新、MS11-4 到達整理を関連ドキュメントへ反映
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` の版数表記を `Ver 0.3.6.1` へ更新
  - ワークスペース内に存在していた関連ドキュメント・設定更新も同一同期に含める
  - リポジトリ全体の反映版を `Ver 0.3.6.1` として確定
- 確認状態:
  - MS11-4 の構造修正とテスト更新が反映済み
  - `writer.py` 再設計なしで pipeline-writer 回帰が通る状態を維持
  - 既存 docs と版管理ログは MS11-4 反映後の状態へ同期済み
- 残課題:
  - 実データ上での `peak_value = 0.0` 事例の観測蓄積
  - 必要最小限に限った RMS 定数の再調整判断
  - internal helper / test 観測点を起点にした MS11-5 の整理

---

## 2026-03-29 / MS11-4 実装反映メモ

- 対象: MS11-4 `pipeline.py` 側 event interval / peak 割当品質改善
- 実装反映:
  - `src/core/pipeline.py` で、正本 interval と peak 探索窓の責務を分離
  - RMS 補正後 interval を `peak_value` 評価の正本とし、halo `±0.03 sec` を隣接 interval 端点中点でクリップする peak window を導入
  - `load_rms_series()` 失敗時の一律 `upper_limit` fallback を廃止し、`upper_limit * 0.25` の保守的 fallback へ変更
  - RMS は取得できたが `global_peak <= 0.0` の場合、全 event を `peak_value = 0.0` とする分岐を追加
  - `peak_value = 0.0` 理由を `rms_unavailable / global_peak_zero / no_peak_in_window / below_abs_threshold / below_rel_threshold` で追跡できる internal helper を追加
  - event は削除せず、interval を維持したまま `peak_value` と理由分類の整合を改善
  - `tests/test_pipeline_peak_values.py` を拡張し、halo 探索・fallback・理由分類優先順を単体で確認できるよう更新
- 確認状態:
  - `tests.test_pipeline_peak_values` 10 件が通過
  - `tests.test_pipeline_and_vmd` と `tests.test_vmd_writer_peak_value` 10 件が通過
  - `tests.test_vmd_writer_zero_guard` と `tests.test_vmd_writer_intervals` 43 件が通過
  - 上記合計 63 件の回帰確認が通過
  - `writer.py` の再設計なしで、`peak_value = 0.0` event を既存 writer 側へ受け渡せる状態を維持
- 残課題:
  - 実データ上での `peak_value = 0.0` 事例の観測蓄積
  - 必要最小限に限った RMS 定数の再調整判断
  - internal helper / test 観測点を起点にした MS11-5 の整理
- スコープ外として維持:
  - `writer.py` 再設計
  - GUI / Preview 改修
  - MS11-5 の全面実装

---

## 2026-03-28 / Ver 0.3.6.0 同期メモ

- 対象: MS11-3 実装完了後の版同期
- 同期内容:
  - `src/vmd_writer/writer.py` の MS11-3 本体、段階 fallback、envelope 保護、FIX01 / FIX02 整合、writer 局所の zero-only shape / short fallback 保護修正を関連ドキュメントへ反映
  - writer 系テスト拡張と回帰確認結果、`pipeline + writer` の参照的確認結果を `docs/Specification_Prompt_v3.md` / `docs/Version_Control.md` に同期
  - リポジトリ全体の反映版を `Ver 0.3.6.0` として確定
- 確認状態:
  - writer 系テスト 67 件が通過している
  - `PYTHONPATH='src;tests'` 付きの `tests.test_pipeline_and_vmd` と `tests.test_pipeline_peak_values` を含む 9 件が通過している
  - `peak_value == 0.0` 由来の意味のない全ゼロ台形は最終出力へ残さない
  - 正規な short / legacy fallback shape は current normalization flow でも不必要に消えない
  - MS11-3 / MS11-2 / legacy fallback の順序と、MS11-2 / FIX01 / FIX02 の到達状態を維持している
- 既知課題として維持:
  - `docs/MS11-2_Known_Issues.md` に整理済みの「無音に見える区間の開口残存」は今回も既知課題のままとし、解決済み扱いにしない
- スコープ外として維持:
  - GUI / Preview の multi-point 表示対応
  - `pipeline.py` 側イベント存在判定ポリシー改善
  - より高度な平滑化
  - 出力仕様全体の再設計

---

## 2026-03-28 / MS11-3 実装完了メモ

- 対象: MS11 出力品質拡張の第3段階
- 実装反映:
  - `src/vmd_writer/writer.py` を主対象として、同一母音近接イベント群を multi-point shape として扱う MS11-3 を実装
  - 秒ベース grouping と frame ベース成立判定を導入し、multi-point shape 生成・`MorphFrame` 展開・採用条件判定を追加
  - 谷値は非ゼロ維持の固定ルールで扱い、`peak_value` を上辺点高さへ反映
  - MS11-3 不成立時は MS11-2 単一上辺台形、さらに不成立時は legacy fallback へ戻る段階フォールバックを接続
  - 後段正規化に対して、MS11-3 成功 shape を envelope 全体単位で保護する導線を追加
  - FIX01 / FIX02 の改善意図を崩さないよう、allowed range / required zero / suppression / zero prune の整合を writer 側で維持
  - writer 系テストを拡張し、grouping / multi-point shape / fallback / protection / FIX01-FIX02 回帰を自動確認できる状態にした
- 到達状態:
  - 同一母音近接イベント群は、条件を満たす場合 multi-point shape として出力される
  - 谷は原則 0.0 へ完全閉口せず、非ゼロで維持される
  - MS11-3 成功時は envelope 全体を allowed non-zero range / protected range の単位として扱う
  - MS11-3 / MS11-2 / legacy fallback の順序が writer 内で成立している
  - writer 系テスト 65 件、および `PYTHONPATH='src;tests'` 付きの `tests.test_pipeline_and_vmd` 6 件が通過している
- 既知課題として維持:
  - `docs/MS11-2_Known_Issues.md` に整理済みの「無音に見える区間の開口残存」は今回も既知課題のままとし、解決済み扱いにしない
- スコープ外として維持:
  - GUI / Preview の multi-point 表示対応
  - `pipeline.py` 側イベント存在判定ポリシー改善
  - より高度な平滑化
  - 出力仕様全体の再設計

---

## 2026-03-27 / Ver 0.3.5.9 同期メモ

- 対象: MS11-2 / MS11-2_FIX01 / MS11-2_FIX02 の反映版同期
- 同期内容:
  - `src/vmd_writer/writer.py` の MS11-2 本体、FIX01、FIX02 の修正内容を関連ドキュメントへ反映
  - writer 系テスト更新内容と到達状態を `docs/Specification_Prompt_v3.md` / 各 Implementation Plan / `docs/Version_Control.md` に同期
  - リポジトリ全体の反映版を `Ver 0.3.5.9` として確定
- 確認状態:
  - writer 系テスト 33 件が通過している
  - MS11-2 は 4点の非対称・単一上辺台形、`time_sec` 上辺中央基準、4 frame 未満 fallback、MS11-1 との部分保護接続を維持
  - FIX01 / FIX02 により、無音区間の非ゼロ除去、不要ゼロ cleanup、発話イベント内部 shape 保護の補正まで反映済み
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - 出力仕様全体の再設計

---

## 2026-03-27 / MS11-2 実装完了メモ

- 対象: MS11-2 出力品質拡張の第2段階
- 実装反映:
  - `src/vmd_writer/writer.py` に、4点の非対称・単一上辺台形を扱う内部仕様 `AsymmetricTrapezoidSpec` を追加
  - 区間処理を「区間 → 台形仕様 → MorphFrame 展開」の二段構造へ整理
  - `start_sec / time_sec / end_sec` を 30fps で frame 化したうえで、`time_sec` を上辺中央基準として扱う変形台形判定を追加
  - `start_frame`〜`end_frame` が 4 frame 以上のときのみ上辺ありの変形台形を生成し、4 frame 未満では既存短区間フォールバックへ戻す接続を整理
  - 開始 / 終了ゼロ保証を維持した 4点展開と、MS11-1 最終正規化層への導線維持を実装
  - 正規な MS11-2 由来形状が孤立短開口抑制 / 個別モーフ短パルス整理で無条件に潰れないよう、必要最小限の部分保護を追加
  - `tests/test_vmd_writer_intervals.py` / `tests/test_vmd_writer_peak_value.py` / `tests/test_vmd_writer_zero_guard.py` を更新し、正常系 / 境界系 / 正規化連携 / 既存保証の観点を反映
- 到達状態:
  - 適用可能区間は旧対称台形ではなく、4点の非対称・単一上辺台形で出力される
  - `time_sec` は上辺中央基準として frame 配置へ反映される
  - 4 frame 未満は既存短区間フォールバックへ落ちる
  - MS11-1 の最終正規化層を維持したまま、正規な MS11-2 由来形状のみを原則維持する構造になった
  - writer 系テスト 29 件が通過している
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---

## 2026-03-26 / MS11-1 実装完了メモ

- 対象: MS11-1 出力品質拡張の第1段階
- 実装反映:
  - `src/vmd_writer/writer.py` に最終モーフフレーム正規化層を追加
  - `(morph_name, frame_no)` 単位の一般重複正規化を実装し、非ゼロ優先 / 複数非ゼロは最大値 / 全ゼロは1件化を適用
  - 母音全体の `open_value = max(あ, い, う, え, お)` を扱う内部表現と `epsilon` ベースの開閉判定を追加
  - 開口区間 / 閉口区間抽出と、前後閉口に挟まれた孤立短開口候補検出を追加
  - 孤立短開口候補の 0 化による抑制と、母音全体の開口列を変えない範囲に限定した個別モーフ短パルス整理を追加
  - `tests/test_vmd_writer_zero_guard.py` に重複統合 / 瞬間開閉 / 30fps 丸め衝突 / 既存仕様維持の確認を追加
- 到達状態:
  - 最終 VMD キー列で同一モーフ・同一フレーム重複が残らない
  - 母音全体ベースで孤立した短開口だけを抑制する構造になった
  - 他モーフ非ゼロ時に単一モーフだけ見て誤って閉口扱いしない
  - 開始 / 終了ゼロ保証、通常台形出力、短区間フォールバック、最大フレーム数ガード、書き出し順安定性を維持する方針で接続した
- スコープ外として維持:
  - 変形台形
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---

## 2026-03-25 / MS10 実装完了メモ

- 対象: MS10 多言語化・設定永続化
- 実装反映:
  - `src/gui/settings_store.py` を追加し、`MMD_AutoLipTool.ini` による設定保存・復元導線を実装
  - `src/main.py` で起動時設定読込と OS 言語フォールバックを接続
  - `src/gui/main_window.py` でテーマ / splitter 比率 / ウィンドウサイズ / 言語 / モーフ最大値 / recent TEXT / recent WAV の保存・復元導線を実装
  - `src/gui/i18n_strings.py` を GUI 文字列正本として整理し、日本語 / 英語の切替基盤を実装
  - `src/gui/operation_panel.py` / `src/gui/central_panels.py` / `src/gui/status_panel.py` / `src/gui/waveform_view.py` / `src/gui/preview_area.py` に実行中言語切替反映を実装
  - recent TEXT / WAV の別管理、起動時無効履歴除去、0 件時プレースホルダ表示を実装
  - 波形表示の空状態文言 / 軸ラベル / 母音表示、および Preview 側母音表示の言語対応を実装
  - 波形表示の日本語プレースホルダと横軸ラベルに対する Matplotlib 和文フォント適用を反映
- 到達状態:
  - 日本語 / EN の実行中切替が成立
  - 言語設定と recent 履歴が次回起動時に復元される
  - 重要 UI 設定とモーフ最大値が永続化される
  - 設定破損時フォールバックと保存失敗時の安全停止が入っている
  - 文字列定義の正本は `i18n_strings.py` に集約された
- リリース同期:
  - リポジトリ全体の反映版を `Ver 0.3.5.8` として確定。

---

## 方針

既存の処理導線（TEXT読込 → WAV読込 → 処理実行 → 出力）を崩さず、  
GUI層・表示層・設定層・処理層が混線しにくい順で段階的に実装する。

---

## マイルストーン一覧

| No. | マイルストーン名 | 対象項目 | 目的 | 完了条件 |
| MS1 | 画面骨格整理 | トップメニュー「ファイル」追加 / ボタン再配置 / 読み込みエリアと表示エリアの区分け | GUIの基本導線を整理し、後続機能の追加先を安定させる | ボタン操作とメニュー操作が同じ処理を呼ぶ。レイアウト変更後も既存導線が崩れない。 |
| MS2 | 読込エラー統一 | 壊れたファイル、不明ファイル読込時の処理 | 入力異常時の挙動を統一し、例外経路の散在を防ぐ | TEXT/WAV読込失敗時の警告表示、内部状態、後続操作禁止条件が一貫する。 |
| MS3 | 波形確認性向上 | 波形表示に30fps縦線区切りを表示 | MMD基準での確認性を上げる | 波形上に30fps基準の縦線が表示され、既存ラベル表示と干渉しない。出力結果には影響しない。 |
| MS4 | 実行中状態の可視化 | 処理中ダイアログ / プログレスバー表示 | 重い処理実行中の状態を明確化する | 処理実行中の状態遷移が明確で、二重実行防止と終了後復帰が整合する。 |
| MS5 | 利便性設定追加① | 読み込み関係のカレントディレクトリ記憶 | 読込操作の手間を減らす | TEXT/WAVそれぞれで直前ディレクトリが保持され、次回読込時に利用される。 |
| MS6 | 利便性設定追加② | ファイル読み込み履歴を各10個記憶し、再呼び出しできるGUI追加 | 再読込の利便性を上げる | 履歴追加・削除・再読込の挙動が一貫し、失敗読込の扱いも定義される。 |
| MS6B | 同名対応ファイルの自動補完読込 | 同一フォルダ・同一 stem の相方（`.txt/.wav`）を主読込成功後に1回試行 | 通常読込/履歴再読込の入力手間を減らしつつ既存導線を維持する | 既読込側は上書きせず、未存在/読込失敗はサイレント、成功時は履歴/表示/開始ディレクトリ保持が既存成功導線で反映され、再連鎖しない。 |
| MS7 | 入出力安全性点検 | セキュリティ関係のチェック | ファイル入力・設定保存まわりの安全性を確認する | 入力・保存・履歴保存・例外処理について危険箇所の確認と修正方針が整理される。 |
| MS8 | 出力品質拡張 | モーフのスムージング | 口の動きの滑らかさを改善する | 既存台形出力との差分を比較でき、現行仕様を壊さず追加評価できる。 |
| MS8A | GUI再構成基盤 | 上部操作列分離 / モーフ上限値UI再配置 / 中央2カラム化 / ステータス欄専用部品化 | 既存導線を維持したまま v3 GUI骨格を最小変更で導入する | `main_window.py` を司令塔のまま、`OperationPanel` / `StatusPanel` を表示専用で組み込み、既存安全動作を維持する。 |
| MS8B | Preview Area 静止表示導入 | `PreviewArea` 追加 / `preview_transform.py` 追加 / `main_window.py` の受け渡し導線整理 / クリア・無効化導線整理 / silent restore 整合 | `current_timing_plan.timeline` を正本とした Preview 静止表示を最小変更で導入する | 5段固定（あ/い/う/え/お）で静止表示でき、解析結果無効化時は Preview をクリアし、`suppress_warning=True` 復元時も Preview 表示整合を維持し、既存導線（TEXT/WAV/処理実行/VMD出力）を維持する。 |
| MS8C | 再生基盤導入 | `playback_controller.py` / `view_sync.py` / Play・Stop・現在地同期 | 波形・Preview Area・ステータスを再生位置で同期させる | Play は処理実行後のみ有効、Stop は再生中のみ有効となり、再生開始は常にゼロフレームからで、波形・Preview Area・ステータス表示が共通位置で同期する。 |
| MS8D-2 | 表示詳細化（改訂） | 横軸フレーム表記 / 共通ビューポート / Zoom / Pan / Preview目盛り / Zoomメニュー導線 / パス中間省略+tooltip | MMD基準での確認性と操作性を高め、波形と Preview Area の表示一貫性を成立させる | 秒内部保持を維持したまま、波形・Preview が同一可視範囲で同期し、Zoom/Pan とパス表示拡張が既存主要導線を壊さず動作する。 |
| MS9 | GUI整備 | アイコン＋文字ボタン化 / ボタン固定サイズ＋折り返し / 英語時の省略記号対応 / ボタン群グルーピング / 状態差の視覚化 / 左右領域の可変分割 / テキスト領域幅調整 / 波形/Preview のテーマ追従配色 / 波形表示配色調整 / `Amp` 削除 / ステータス表示整理 / 分析完了音 / 多言語化を見据えた文言長耐性 | モックアップに近いユーザーフレンドリーな GUI へ整備し、後続の多言語化・設定永続化の前提となる画面構造と外観を安定させる | 主要操作がアイコン＋文字ボタンで視認しやすく整理され、縮小時も折り返しと可変分割で破綻しにくい。波形/Preview は新配色で可読性を維持し、ステータス表示と完了通知を含めて GUI 全体の操作理解性が向上する。日本語/英語の文字長差でもレイアウトが大きく崩れない。 |
| MS10 | 多言語化・設定永続化 | `i18n_strings.py` / `settings_store.py` / 言語切替 / 履歴永続化 | UI多言語化と設定保存を分離責務で導入する | 日本語/EN の実行中切替が成立し、言語設定と履歴が次回起動に復元される。文字列定義の正本は1か所に集約される。 |
| MS11 | 出力品質拡張 | モーフスムージング / 変形台形 / 複数上辺点対応 | 口の動きの滑らかさを改善する | 既存台形出力との差分を比較でき、開始/終了ゼロ点を維持したまま、変形台形や同一母音連続時の複数上辺点を評価できる。 |

---

## 進捗メモ（2026-03-20）

- リリース同期:
  - リポジトリ全体の反映版を `Ver 0.3.5.1` として確定
- 完了:
  - MS1 画面骨格整理
  - MS2 読込エラー統一
  - MS3 波形確認性向上
  - MS4 実行中状態の可視化（フェーズ1〜6）
  - MS5 利便性設定追加①（フェーズ1〜9）
  - MS6 利便性設定追加②（フェーズ1〜9）
  - MS6B 同名対応ファイルの自動補完読込（フェーズ1〜10）
  - MS7 入出力安全性点検（フェーズ1〜8）
  - MS8A GUI再構成基盤（フェーズ1〜10）
  - MS8B Preview Area 静止表示導入（フェーズ1〜9）
- MS4 完了時の確認結果（要点）:
  - 処理中ダイアログ表示（不定進捗、キャンセルなし）
  - 処理中の再入防止
  - 処理中の操作ロック（読込/再実行/出力/履歴/モーフ上限値）
  - 成功/失敗時の復帰整合（ダイアログ終了・busy解除・状態表示復帰）
- MS7 完了時の確認結果（要点）:
  - TEXT/WAV 読込入口で、空・非存在・ディレクトリなどの事前確認を最小導入
  - VMD 保存入口で、`.vmd` 補完後パスの妥当性確認を導入
  - 履歴再読込で、危険値（空/非存在/ディレクトリ/拡張子不一致）を事前確認
  - 履歴再読込失敗時は該当履歴のみ除去し、メニュー更新を維持
  - 想定外例外時も GUI 警告へフォールバックし、状態復帰を統一
- MS5 完了時の確認結果（要点）:
  - TEXT/WAV 読込ダイアログの開始位置を、それぞれ独立した保持値で管理
  - 通常読込成功時のみ、各保持値を「選択ファイルの親ディレクトリ」で更新
  - 履歴再読込成功時にも同様に更新し、失敗時の既存履歴除去ロジックを維持
  - 保持値が無効（未設定/空/非存在/非ディレクトリ）でも警告追加なしで安全フォールバック
  - フェーズ9観点（9-1〜9-5）をコード上で満たし、最小実行確認でも PASS
- MS6 完了時の確認結果（要点）:
  - TEXT/WAV 履歴を別配列で保持し、通常読込成功時のみ対応側履歴へ追加
  - 重複時は先頭再配置、上限10件超過時は末尾削除で統一
  - 履歴メニュー再構築時は古い action をクリアし、各項目を対応する再読込処理へ接続
  - 壊れた履歴値（空/非存在/ディレクトリ/拡張子不一致）と再読込失敗時は、該当履歴のみ除去して即時メニュー更新
  - TEXT/WAV の履歴更新先・メニュー表示元・再読込導線が相互に混線しないことをコード上で固定
  - フェーズ9観点（10件上限/重複先頭移動/再読込導線/壊れた履歴値除去/非混線）を最小スモーク確認で PASS
- MS6B 完了時の確認結果（要点）:
  - 発動対象は通常読込と履歴再読込に限定し、セッション外永続化の復元時発動は対象外のまま維持
  - 同一フォルダ・同一 stem・拡張子相補（`.txt/.wav`、大文字小文字非区別）で相方候補を解決
  - 主読込成功時のみ補完を1回試行し、反対側が既読込なら補完しない
  - 相方未存在/読込失敗はサイレントで終了し、専用通知を追加しない
  - 自動補完成功時は既存読込成功導線を再利用し、履歴更新・表示更新・読込開始ディレクトリ保持を反映
  - 補完側から逆方向補完を起こさない構造で再連鎖を防止
- MS8A 完了時の確認結果（要点）:
  - 上部操作列を `OperationPanel` に置換し、`text/wav/process/output` の既存接続先を維持
  - モーフ上限値UI（`morph_upper_limit_label/input`）を操作列直下へ再配置し、変更時の再解析待ち復帰導線（`current_timing_plan=None` / 波形ラベルクリア / 自動再解析なし）を維持
  - 中央領域を左右2カラム化し、左にテキスト系・ファイル状態系、右上に既存 `WaveformView`、右下に将来用プレースホルダを配置
  - 最下部ステータス表示を `StatusPanel` 化し、`_set_output_status(...)` の表示先を `StatusPanel` へ統一
  - `_update_action_states()` の判定ロジックは `main_window.py` に維持し、Play/Stop/Zoom は未実装ボタンとして無効固定
  - 既存主要導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）と既存安全動作（処理中ダイアログ・二重実行防止・未解析時保存禁止・処理中ロック）を維持
  - MS8A 範囲外（Preview実装 / 再生機能 / Zoom機能 / 多言語化 / 設定永続化 / 出力品質拡張）は未実装のまま後続対象として保持

---

## 進捗メモ（2026-03-21 / リリース同期）

- リポジトリ全体の反映版を `Ver 0.3.5.3` として同期。
- MS8B（Preview Area 静止表示導入）の実装反映状態を含めて、現作業ツリーを確定対象とする。

---

## 進捗メモ（2026-03-24 / Ver 0.3.5.7 リリース同期）

- リポジトリ全体の反映版を `Ver 0.3.5.7` として確定。
- GUIFIX06（波形とプレビューの横軸整合、ラベル右寄せ）の実装を統合。

---

## 進捗メモ（2026-03-23 / セキュリティ実装 SEC01・SEC02 完了）

- リポジトリ全体の反映版は `Ver 0.3.5.6` を維持。
- 対象: 実装リストSEC01（フェーズ1）、実装リストSEC02（フェーズ1〜4）
- 完了内容（要点）:
  - **SEC01**:
    - TEXTの絶対文字数上限（5000文字）制約を導入し、超過時は即時エラー停止
    - WAVの絶対再生時間上限（15分）制約を導入し、超過時は即時エラー停止
    - VMDの生成フレーム数上限（22000フレーム）制約を導入し、超過時は出力前エラー停止
  - **SEC02**:
    - TEXT内の異常制御文字（5文字以上）、規定長超過行（500/2000文字）、記号長大行（300文字）のエラー検証機能を追加
    - 絵文字関連フォーマット文字（ZWJ等）をエラーカウントから除外するホワイトリスト処理を追加（自動テスト済）
    - TEXT読込時の文字コードフォールバック（UTF-8 → Shift_JIS → UTF-16）を追加
    - WAV読み込み時の非対応フォーマット（PCM以外）や破損エラーの表示をユーザー向けへ改善
    - VMD保存時のファイル同名上書き確認ダイアログ（Yes/No）を追加

---

## 進捗メモ（2026-03-23 / GUIFIX06 横軸整合完了）

- 対象: 実装リストGUIFIX06（フェーズ1〜10）
- 完了内容（要点）:
  - **横軸基準の一本化**: Matplotlib の Axes（実プロットエリア）を X軸の正基準に固定し、PreviewArea がその物理座標を動的に模倣する構造を実装。
  - **同期経路の整備**: `draw_event` / `resize_event` / `splitterMoved` / `Pan` 等のあらゆる再レイアウト契機で、最新の基準矩形を伝播・再適用する経路を `MainWindow` に集約。
  - **初期状態の整合**: データ未ロード時でも Axes の枠線位置を正しく取得し、プレビュー側のグリッドと一致させるよう修正（Phase 9）。
  - **視認性向上**: 母音ラベル（あ、い...）を右寄せ表示に変更し、ウィンドウ幅に関わらず常にグリッド（表）のすぐ左隣に隣接するよう改善（Phase 10）。
  - **副作用の抑制**: 既存の秒ベース同期（ViewSync）への影響を最小限に抑え、ピクセル投影の基点のみを波形側へ動的に吸着させる方式を採用。

---

## 進捗メモ（2026-03-22 / リリース同期）

- リポジトリ全体の反映版を `Ver 0.3.5.7` としてリリース同期
- MS8D-2（共有ビューポート / Zoom・Pan / フレーム目盛り / パス表示拡張）反映状態を含めて、現作業ツリーを確定対象とする。
- 追加修正として、通常の Zoom 操作時に viewport 左端が 0.0 秒へ戻る不一致を補正し、現在 viewport の中心を保持した Zoom に統一した。

---

## 進捗メモ（2026-03-21 / MS8B 実装前固定）

- MS8B は実装開始前。ここでは実装前仕様・責務境界・完了条件のみを固定し、完了扱いにはしない。
- 固定済み（実装前）要点:
  - 目的: Preview Area の静止表示導入（右カラム下段、5段固定、波形とは別ウィジェット）
  - 正本: `current_timing_plan.timeline` を Preview の元データとして共用し、二重管理しない
  - 責務: `main_window.py`（司令塔）/ `preview_transform.py`（整形専用）/ `preview_area.py`（描画専用）へ分離
  - クリア基準: 失敗時だけでなく「解析結果無効化時全体」を対象にする
  - silent restore: `suppress_warning=True` は通常破壊的クリア導線と分離し、復元後 `current_timing_plan` から再構成する
- MS8B フェーズ分解（実装前整理）:
  - フェーズ1: 現状導線と組み込み位置の確定
  - フェーズ2: Preview 用データ契約の固定
  - フェーズ3: Preview 整形責務の導入準備
  - フェーズ4: Preview 描画責務の導入準備
  - フェーズ5: `main_window.py` の受け渡し責務整理
  - フェーズ6: Preview クリア / 無効化導線の整理
  - フェーズ7: `suppress_warning=True` 復元導線の扱い固定
  - フェーズ8: UI 組み込み成立条件の確認
  - フェーズ9: スコープ逸脱防止の最終固定

---

## 進捗メモ（2026-03-21 / MS8B 実装完了）

- MS8B フェーズ1〜9を実装・確認し、Preview Area 静止表示導入を完了扱いとした。
- 反映済み（コード実体）:
  - 右カラム下段へ `PreviewArea` を組み込み（波形とは別ウィジェット）
  - `preview_transform.py` で `timeline -> PreviewData` 整形責務を分離
  - `main_window.py` で `current_timing_plan.timeline` を正本にした受け渡し導線を接続
  - 解析結果無効化入口で Preview クリア導線を統一（失敗時限定ではない）
  - `suppress_warning=True` 復元時の Preview 再構成整合を反映（独立キャッシュなし）
- 非対象を維持（MS8B 時点）:
  - 再生同期 / 再生中カーソル / 共通カーソル線 / Play/Stop 実機能 / Zoom / スクラブ / 設定永続化 などは未着手
- 責務境界:
  - `main_window.py`（受け取り・保持・受け渡し制御）
  - `preview_transform.py`（整形）
  - `preview_area.py`（描画）
  - `waveform_view.py` / `pipeline.py` は責務変更なし

---

## MS7 方針固定（フェーズ7）

- 修正優先順位:
  1. 保存前パス確認
  2. 履歴再読込の安全確認
  3. 読込入口の事前パス確認
  4. 例外経路の復帰揃え
- 修正範囲:
  - `src/gui/main_window.py` の局所修正に限定
  - `src/app_io/` 導入や I/O 層の本格分離は MS7 対象外
- 運用原則:
  - 問題がなければ変更しない
  - 新機能追加や大規模設計変更に進まない

---

## MS7 完了判定観点（フェーズ8）

- TEXT:
  - 非存在/UTF-8不可/空内容/有効文字なしで安全に警告中断できる
- WAV:
  - 非存在/解析不能/プレビュー不能で安全に中断し、表示復帰できる
- 保存:
  - `.vmd` 補完と未解析出力禁止を維持し、保存失敗後も再試行可能
- 履歴:
  - 壊れた履歴値でクラッシュせず、失敗時に該当履歴除去とメニュー更新が行われる
- 例外:
  - 想定外例外でも GUI 警告へ落ち、状態が不整合のまま残らない

---

## 推奨実装順

1. MS1 画面骨格整理  
2. MS2 読込エラー統一  
3. MS3 波形確認性向上  
4. MS4 実行中状態の可視化  
5. MS5 利便性設定追加①  
6. MS6 利便性設定追加②  
7. MS6B 同名対応ファイルの自動補完読込  
8. MS7 入出力安全性点検  
9. MS8A GUI再構成基盤（完了）
10. MS8B Preview Area 静止表示導入（完了）
11. MS8C 再生基盤導入（完了）
12. MS8D-2 表示詳細化（改訂）（完了）
13. MS9 GUI整備（次段階）
14. MS10 多言語化・設定永続化
15. MS11 出力品質拡張

---

## 補足整理

### GUI整備フェーズ

- MS1 画面骨格整理
- MS2 読込エラー統一
- MS3 波形確認性向上
- MS4 実行中状態の可視化
- MS5 利便性設定追加①
- MS6 利便性設定追加②
- MS6B 同名対応ファイルの自動補完読込
- MS8A GUI再構成基盤（完了）
- MS8B Preview Area 静止表示導入（完了）
- MS8C 再生基盤導入（完了）
- MS8D-2 表示詳細化（改訂）（完了）
- MS9 GUI整備

### 品質確認フェーズ

- MS7 入出力安全性点検

### 機能拡張フェーズ

- MS10 多言語化・設定永続化
- MS11 出力品質拡張

---

## 段階的実装の意図

- 前半は GUI層・表示層・設定層の整理に限定する
- 処理ロジック変更を伴う項目は後半へ分離する
- 既存の内部データ構造や処理導線への影響を最小化する
- 開発途中でコード責務が混ざらない状態を維持する

---

## 追記メモ（2026-03-21 / MS8C 完了）

- 対象: MS8C フェーズ1〜10
- 完了内容（要点）:
  - `playback_controller.py` / `view_sync.py` を追加し、実 WAV 再生と秒ベース共通位置同期の基盤を導入
  - `main_window.py` で `controller -> view_sync -> waveform/preview/status` の配布経路を接続
  - Play/Stop を action state に統合（Play は処理実行後のみ有効、Stop は再生中のみ有効）
  - 再生開始 0.0 秒起点、停止/終了/無効化で 0.0 秒へ戻す遷移を統一
  - `WaveformView` / `PreviewArea` に再生カーソル表示/クリア導線を接続
  - ステータス欄に再生中フレーム表示（30fps派生）を追加し、既存優先順位を維持
  - 解析結果無効化導線と既存入口（再読込・失敗・入力不足・再解析待ち・silent restore）で再生状態取り残しを解消
- 非対象（MS8C 時点で未実装のまま維持）:
  - Zoom / スクラブ / 手動シーク / クリック移動 / 表示詳細化
  - `pipeline.py` / `writer.py` / `preview_transform.py` / `whisper_timing.py` の仕様変更

---

## 追記メモ（2026-03-22 / MS8D-2 完了）

- 対象: MS8D-2 フェーズ1〜12
- 完了内容（要点）:
  - `view_sync.py` を共有表示状態ハブへ拡張し、共有可視範囲（秒ベース）を導入
  - `main_window.py` に Zoom/Pan/viewport 初期化導線を統合し、WAV 読込成功/失敗/無効化で表示範囲を安全に復帰
  - `waveform_view.py` を可視範囲ベース描画へ移行し、横軸をフレーム表記（30fps）へ変更
  - `preview_area.py` を可視範囲ベース描画へ移行し、可視範囲クリップ表示とフレーム目盛りを追加
  - Zoom を Operation Panel ボタンと View メニュー action の両方へ接続し、有効/無効判定を同期
  - Pan 操作を導入し、波形/Preview を同一可視範囲で同期移動可能化（境界クランプ含む）
  - TEXT/WAV パス表示を中間省略 + tooltip フルパスへ拡張
- 非対象（維持）:
  - `pipeline.py` / `writer.py` / `whisper_timing.py` の仕様変更
  - `preview_transform.py` への UI 状態（Zoom/Pan/viewport）責務追加
---

## 2026-03-22 追記 / MS9 完了状態と MS9-2 への接続

- MS9 本体は、GUI 整備マイルストーンとして実装完了扱いとする。
- 実装済み範囲:
  - `main_window.py` の GUI 構築責務分散
  - 左情報表示パネル化
  - 右表示領域コンテナ化
  - `QSplitter` による左右分割
  - `OperationPanel` の 3 グループ整理
  - `StatusPanel` の 2 領域化
  - 文字列管理受け皿
  - テーマ切替導線と Qt / 描画側テーマ追従
  - `Amp` 削除
  - 分割比率 / テーマ設定受け皿
  - 分析終了時通知音
- MS9 追加改修として、右表示領域共通の横スクロールバーを実装済みとする。
  - 第1段階: バー設置 + shared viewport 基本連動
  - 第2段階: 無効化条件・Zoom 連動・Scrollbar 状態調整
  - 追加修正: PreviewArea の viewport 全長解釈補正、Zoom 端部クランプ時の体感改善、PreviewArea マウス座標型修正
- ただし、見た目最終調整・余白最終調整・実機 UX の微修正は次セッション `MS9-2` で扱う。

## 実装前メモ / MS9-2

- 位置づけ:
  - MS9 本体完了後の外観・UX 微調整セッション
- 主対象:
  - 右表示領域共通スクロールバーの見た目調整
  - 余白 / 高さ / splitter リサイズ時の違和感低減
  - テーマとの見た目馴染ませの微修正
  - 端部近傍 UX の実機確認を踏まえた軽微調整
- 非対象:
  - shared viewport 正本責務の変更
  - 再生制御仕様変更
  - 設定永続化本格実装
- ※上記は実装前整理メモであり、到達点は後続の「MS9-2 完了」節を正とする。

## 2026-03-22 追記 / MS9-2 完了

- MS9-2 は、MS9 本体と右表示領域共通横スクロールバー追加後の見た目・余白・初期表示バランス調整として完了扱いとする。
- 反映済み（コード実体）:
  - 初期ウィンドウサイズを `1270x714`、最小サイズを `720x405` へ調整
  - 中央 `QSplitter` の初期比率を `左3 : 右7` とし、表示確定後の再適用で初期実効比率を安定化
  - GUI 主要部へ `11pt` 基準フォントと 4〜6px 基準の余白を反映
  - 操作ボタンの横長化を抑制し、`TXT読込` / `WAV読込` / `処理実行` の改行を解消
  - 操作ボタンの assets アイコン差し替えを反映し、広い幅ではボタングループが左詰めで並ぶよう再配置
  - `処理実行` / `VMD保存` ボタンの高さを統一
  - モーフ上限値入力欄を短幅固定のまま維持し、内蔵スピンボタンを廃止して独立した `-` / `+` ボタンへ置換
  - モーフ上限値入力まわりはダーク / ライト両テーマで視認できる局所スタイルへ整理
- 非対象を維持:
  - shared viewport / playback / zoom / scrollbar の責務や挙動変更
  - 設定永続化
  - 多言語化本実装
  - 波形 / Preview 描画ロジックの再設計
## 2026-03-27 / MS11-2_FIX02 実装完了メモ

- 対象: MS11-2_FIX02 writer 後段ゼロ縮退抑止
- 実装反映:
  - `src/vmd_writer/writer.py` に、発話イベント範囲ベースの `protected_event_ranges` を追加
  - short open / short morph pulse 抑制に、MS11-2 shape だけでなくイベント全域保護の条件を追加
  - 近接イベントおよび fallback 混在時に、rise / top / fall の有効寄与が suppression で過剰に失われないよう補正
  - FIX01 で導入した許容外非ゼロ除去と不要ゼロ prune の意図を維持したまま、肩消失が起きにくいよう後段条件を調整
  - `tests/test_vmd_writer_zero_guard.py` に、short fallback 維持・近接イベント共存・FIX01 意図維持の回帰テストを追加
- 到達状態:
  - 発話イベント内部で、頂点だけ残して肩が消えるゼロ縮退が起きにくくなった
  - MS11-2 正規 shape と legacy fallback の近接ケースでも、後段 suppression による過剰 0 化を抑制できる構造になった
  - FIX01 の無音区間非ゼロ除去意図は維持されている
  - writer 系テスト 33 件が通過している
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---

## 2026-03-27 / MS11-2_FIX01 実装完了メモ

- 対象: MS11-2_FIX01 writer 正規化整合修正
- 実装反映:
  - `src/vmd_writer/writer.py` に、許容非ゼロ範囲と維持すべき境界ゼロの文脈情報を導入
  - MS11-2 保護範囲を `start_frame`〜`end_frame` 全体へ拡張
  - 許容外区間の非ゼロ除去と、不要な中間 `0.0` キーの prune を追加
  - `tests/test_vmd_writer_zero_guard.py` に、不要ゼロ整理と許容外非ゼロ除去の回帰確認を追加
- 到達状態:
  - 発話区間内に `0.0` キーだけが不自然に残る状態を主要ケースで改善
  - 無音区間に残る不要な非ゼロキーを writer 後段で落とせる構造になった
  - 開始 / 終了ゼロと collision 回避ゼロは維持される
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---
