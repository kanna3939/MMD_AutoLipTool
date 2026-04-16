# MS14_Block_Breakdown

## 1. 文書情報

- 文書名: `MS14_Block_Breakdown.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象系列: `Ver 0.4.x`
- 対象マイルストーン: `MS14`
- 主対象読者: `Antigravity`
- 記述言語: `日本語`
- 目的: `MS14 を block 単位へ分解し、責務境界・依存関係・完了条件・流入禁止範囲を明確化する`

---

## 2. この文書の目的

本書は、MS14 を安全に実装するために、MS14 全体を block 単位へ分解し、各 block が何を担当し、何を担当しないかを固定するための文書である。

MS14 の主目的は、**wx 主系で TEXT読込 → WAV読込 → 解析実行 → VMD保存 の実用コア導線を回復すること** にある。  
したがって、MS14 は UI polish や再生 UX 再構築を行う段ではなく、**Ver 0.4 系の実用入口を成立させる段** として扱う。

この目的を崩さないため、MS14 は以下の 6 block に分解する。

- MS14-B1: 実用 UI 骨格拡張
- MS14-B2: 状態管理と action state 回復
- MS14-B3: 入力導線 parity 回復
- MS14-B4: 解析実行 parity 回復
- MS14-B5: 出力・履歴・settings save parity 回復
- MS14-B6: 統合整理と parity closeout

---

## 3. MS14 の全体位置づけ

### 3.1 前段との関係
MS13 により、以下は成立済みである。

- wx 主系起動入口
- 最小メインフレーム
- 最小メニュー / 操作列 / ステータス
- settings load / apply の最小導線
- controller / actions / worker stub / status 受け口
- 軽量統合チェック

MS14 は、この最小基盤の上に、**実用コア導線だけを戻す** 段である。

### 3.2 後段との関係
MS15 では、波形 / Preview / 再生系再構築を扱う。  
そのため MS14 では、これらを本格実装しない。

MS14 の出口は、**見た目は最小でも、実務上の主要操作が回る wx 主系** である。

---

## 4. MS14 の到達目標

MS14 全体の到達目標は、以下とする。

1. wx 主系で TEXT を読める
2. wx 主系で WAV を読める
3. text / hiragana / vowel / wav info が表示される
4. 解析実行を wx 側から行える
5. 解析中の busy / lock / status が最低限整合する
6. VMD 保存を wx 側から行える
7. recent TEXT / WAV と last output dir が使える
8. `morph_upper_limit` / `closing_hold_frames` / `closing_softness_frames` を扱える
9. 波形 / Preview / 再生は未実装でも placeholder / disabled として整理されている
10. 依存・配布・文書整合が MS14 出口として最低限揃っている

---

## 5. MS14 全体の設計原則

### 5.1 コア導線優先
MS14 では、波形 / Preview / playback よりも、file open / analyze / save の成立を優先する。

### 5.2 Qt 側の丸移植をしない
Qt 側の `main_window.py` を丸ごと wx へ移植しない。  
必要な導線を切り出して、wx 側に再接続する。

### 5.3 settings の既存 key を壊さない
MS14 で save を回復するが、未使用 key を default で潰さない。  
保存導線は **load 済み設定を基礎とした merge-save** を前提とする。

### 5.4 MS15 以降を先取りしない
波形描画、Preview 描画、再生同期、Zoom、shared viewport は MS15 範囲とする。  
MS14 では placeholder / disabled / 最小受け口に留める。

### 5.5 block 単位で閉じる
各 block は、後続 block の責務を前倒しで取り込まない。  
block 内で責務が閉じていることを優先する。

---

## 6. block 一覧

| Block | 名称 | 主目的 |
| --- | --- | --- |
| MS14-B1 | 実用 UI 骨格拡張 | コア導線を置ける wx UI 骨格へ拡張する |
| MS14-B2 | 状態管理と action state 回復 | 実用動作に必要な state / enable-disable / status 契約を回復する |
| MS14-B3 | 入力導線 parity 回復 | TEXT / WAV 読込と変換結果反映を実動化する |
| MS14-B4 | 解析実行 parity 回復 | 解析 worker と実行中状態遷移を実動化する |
| MS14-B5 | 出力・履歴・settings save parity 回復 | VMD 保存、履歴、設定保存の実用出口を回復する |
| MS14-B6 | 統合整理と parity closeout | MS14 全体を統合し、最小整合・依存整合・文書整合を閉じる |

---

## 7. 各 block の詳細

## 7.1 MS14-B1 実用 UI 骨格拡張

### 目的
MS13 の最小骨格を、MS14 のコア導線を実装できる UI 骨格へ拡張する。

### 主対象
- TEXT path 表示
- WAV path 表示
- text preview
- hiragana preview
- vowel preview
- WAV info 表示
- 口パラメータ入力部
- file / run / save の実用前提配置
- 中央 placeholder の実用配置見直し
- status 領域の最小整理

### In Scope
- path / preview / info の表示領域追加
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`
- file / run / save ボタン配置の現実化
- placeholder ラベルの整理
- 最小レイアウトの崩れ修正

### Out of Scope
- file dialog 実装
- 実読込
- 実解析
- 実保存
- 波形描画
- Preview 描画
- 再生ボタン実動化
- Zoom / Pan
- テーマ polish

### 完了条件
1. MS14 で必要な表示領域が wx 側に存在する
2. 口パラメータ入力部が存在する
3. file / run / save の置き場が確定している
4. 波形 / Preview / 再生は未実装でも位置づけが明確
5. B2 以降がこの UI 骨格の上で進められる

---

## 7.2 MS14-B2 状態管理と action state 回復

### 目的
wx 側に、実用 GUI として必要な状態管理と action state 契約を導入する。

### 主対象
- `selected_text_path`
- `selected_wav_path`
- `selected_text_content`
- `selected_hiragana_content`
- `selected_vowel_content`
- `selected_wav_analysis`
- `current_timing_plan`
- busy state
- status 更新ルール
- enable / disable ルール
- invalidate 導線

### In Scope
- state の保持場所整理
- `MainFrame` と controller 間の責務整理
- action state の判定ルール
- busy 中 lock ルール
- warning / status の共通入口整理
- read / analyze / save 前提の前提条件判定

### Out of Scope
- 実ダイアログ
- 実ファイル読込
- 実解析 worker
- 実保存
- settings save
- 再生 state
- 波形 / Preview の高度 state

### 完了条件
1. 実用に必要な state の骨格が定義されている
2. file / run / save の enable / disable ルールがある
3. busy 中 lock の基本契約がある
4. invalidate 導線が定義されている
5. B3 以降がこの state 契約に依存できる

---

## 7.3 MS14-B3 入力導線 parity 回復

### 目的
wx 側で TEXT / WAV の実読込導線を回復し、必要な変換結果を UI へ反映できる状態にする。

### 主対象
- TEXT open dialog
- WAV open dialog
- input validation
- text → hiragana → vowel
- WAV analyze
- path / preview / info 反映
- counterpart auto load
- 読込失敗時復帰
- recent 候補更新前提の接続

### In Scope
- TEXT 読込成功 / 失敗導線
- WAV 読込成功 / 失敗導線
- text processing 反映
- WAV analysis 反映
- counterpart 自動補完読込
- state 更新
- 読込成功後の status 更新
- 読込失敗時の rollback / invalidate

### Out of Scope
- 解析 worker
- VMD save
- settings save 本体
- recent menu の完全実装
- 波形描画本格化
- Preview 本格化
- playback

### 完了条件
1. TEXT 読込が wx 側で動く
2. WAV 読込が wx 側で動く
3. 変換結果が表示へ反映される
4. WAV info が表示へ反映される
5. 失敗時に state 不整合が残らない
6. B4 / B5 がこの入力導線を前提に進められる

---

## 7.4 MS14-B4 解析実行 parity 回復

### 目的
wx 側で解析実行を実動化し、処理中状態と完了 / 失敗遷移を成立させる。

### 主対象
- `build_vowel_timing_plan(...)`
- 実 worker
- 実行中 lock
- 完了 / 失敗復帰
- `current_timing_plan`
- 最小 status 更新
- 将来の MS15 handoff を壊さない結果保持

### In Scope
- 解析実行入口
- worker 起動
- busy 開始 / busy 終了
- 二重実行防止
- 成功時の結果保持
- 失敗時の復帰
- status / warning 更新
- B2 で定義した state 契約への接続

### Out of Scope
- Preview 描画本格化
- 波形イベント描画
- playback start/stop
- progress bar 高度化
- Zoom / viewport
- VMD save
- settings save

### 完了条件
1. wx 側から解析を実行できる
2. 二重実行防止が効く
3. busy 中 lock が成立する
4. 成功時に `current_timing_plan` が保持される
5. 失敗時に復帰できる
6. B5 が解析済み状態を前提に保存できる

---

## 7.5 MS14-B5 出力・履歴・settings save parity 回復

### 目的
wx 側で VMD 保存、recent files、last output dir、settings save を回復し、実用出口を成立させる。

### 主対象
- VMD save dialog
- `.vmd` suffix 補完
- overwrite confirm
- `generate_vmd_from_text_wav(...)`
- recent TEXT / WAV 更新
- last VMD output dir 更新
- wx 側利用設定の save
- merge-save による既存 key 保全

### In Scope
- 保存ダイアログ
- 保存前パス確認
- overwrite confirm
- VMD 生成呼出
- 保存成功 / 失敗導線
- recent files の更新
- last output dir の保存
- settings save 導線
- load 済み設定を基礎にした merge-save
- B2 / B3 / B4 で更新された状態の保存反映

### Out of Scope
- settings dialog
- migration
- 新設定形式
- theme / language の本格保存活用
- splitter / viewport 系高度保存
- 波形 / Preview / playback の保存契約

### 完了条件
1. wx 側から VMD 保存できる
2. recent TEXT / WAV が使える
3. last output dir が記憶される
4. settings save が動く
5. 未使用 key を壊さない保存方針が成立している
6. 実用出口としての MS14 コア導線が閉じる

---

## 7.6 MS14-B6 統合整理と parity closeout

### 目的
MS14-B1〜B5 を統合し、MS14 全体として破綻がないことを確認し、依存・配布・文書整合を最小限閉じる。

### 主対象
- B1〜B5 統合確認
- 起動確認
- 入力 → 解析 → 保存の最小手動確認
- 軽量統合チェック
- requirements / pyproject / packaging 最小整合
- README / docs 同期
- MS15 送り事項整理

### In Scope
- MS14 全体の結合確認
- 競合・接着不良の最小修正
- fresh 環境想定での依存整合確認
- `gui_wx` を含む package / build 整合
- README と docs の現在地同期
- 未実装事項の引継ぎ整理

### Out of Scope
- 新機能追加
- 波形 / Preview / playback 実装
- 大規模リファクタ
- UI polish
- i18n 本格化
- MS15 内容の先取り

### 完了条件
1. B1〜B5 が統合されている
2. TEXT → WAV → 解析 → VMD保存 の最小導線が通る
3. recent / settings save が壊れていない
4. requirements / pyproject / packaging の最小整合が取れている
5. README / docs の現在地が一致している
6. MS15 へ安全に引き継げる

---

## 8. block 間の依存関係

### 8.1 基本依存
- B1 は先頭 block
- B2 は B1 に依存
- B3 は B1 / B2 に依存
- B4 は B2 / B3 に依存
- B5 は B2 / B3 / B4 に依存
- B6 は B1〜B5 全体に依存

### 8.2 依存の意味
- B1 は UI の受け皿を作る
- B2 は状態契約を作る
- B3 は入力を入れる
- B4 は入力済み状態の上に解析を乗せる
- B5 は解析済み状態の上に保存と永続化を乗せる
- B6 は全体を閉じる

---

## 9. flow 概要

MS14 全体の流れは、以下とする。

1. **B1** で実用 UI の置き場を作る
2. **B2** で状態と action state の契約を作る
3. **B3** で TEXT / WAV 読込を動かす
4. **B4** で解析を動かす
5. **B5** で保存・履歴・settings save を戻す
6. **B6** で統合し、依存・文書・配布整合を閉じる

---

## 10. block ごとの流入禁止ルール

### 10.1 MS14-B1 への流入禁止
- 実読込
- 実解析
- 実保存
- settings save
- playback 実装
- 波形 / Preview 実装

### 10.2 MS14-B2 への流入禁止
- file dialog 本実装
- worker 実装
- VMD 保存
- settings save
- package / docs 更新

### 10.3 MS14-B3 への流入禁止
- 解析 worker
- VMD save
- settings save 本体
- recent menu full 実装
- playback
- Preview / waveform 本格化

### 10.4 MS14-B4 への流入禁止
- VMD save
- recent files save
- settings save
- playback start/stop
- Zoom / Pan / viewport
- 波形 / Preview port

### 10.5 MS14-B5 への流入禁止
- settings dialog
- migration
- テーマ再構築
- i18n 本格化
- playback / waveform / Preview の実装
- 依存整合の全処理

### 10.6 MS14-B6 への流入禁止
- 新規実機能追加
- UI 大改造
- 波形 / Preview / playback 本格移植
- 英語対応
- MS15 内容の前倒し

---

## 11. テスト方針

## 11.1 B1
- UI 骨格存在確認
- 必要 widget 存在確認
- placeholder / disabled 状態確認

## 11.2 B2
- state 初期値確認
- action state 判定確認
- invalidate / busy 契約確認

## 11.3 B3
- TEXT 読込成功 / 失敗
- WAV 読込成功 / 失敗
- text → hiragana → vowel 反映
- WAV info 反映
- counterpart auto load
- rollback 確認

## 11.4 B4
- 解析実行成功 / 失敗
- busy lock
- 二重実行防止
- 結果保持
- status 復帰

## 11.5 B5
- VMD save 成功 / 失敗
- overwrite confirm
- recent files 更新
- output dir 記憶
- settings save
- merge-save 契約確認

## 11.6 B6
- 起動確認
- TEXT → WAV → 解析 → 保存 の手動導線確認
- 軽量統合チェック
- requirements / pyproject / README / docs 整合確認

---

## 12. 主要リスク

### Risk 1. Qt 側の責務を丸ごと持ち込む
MS14 が肥大化し、MS15 境界が壊れる。  
**Control:** block scope を厳守する。

### Risk 2. settings save で既存 key を破壊する
wx 側未使用領域が default で上書きされる危険がある。  
**Control:** merge-save を前提にする。

### Risk 3. 入力・解析・保存の責務が 1 箇所に集中する
`MainFrame` や controller が再び巨大化する。  
**Control:** B2 で state / action / status 契約を先に整理する。

### Risk 4. 波形 / Preview / playback が早期流入する
MS15 が先食いされ、移行作業が混線する。  
**Control:** placeholder / disabled に留める。

### Risk 5. コードだけ進み配布整合が崩れる
fresh 環境で動かない wx 主系になる。  
**Control:** B6 で依存・package・README・docs の最小整合を閉じる。

---

## 13. MS14 の Done 判定

MS14 は、以下をすべて満たしたら完了とみなす。

1. wx 主系で TEXT 読込ができる
2. wx 主系で WAV 読込ができる
3. 解析実行ができる
4. VMD 保存ができる
5. recent TEXT / WAV が使える
6. last output dir が保存される
7. settings save が成立する
8. `morph_upper_limit` / `closing_hold_frames` / `closing_softness_frames` が使える
9. 波形 / Preview / playback は未実装でも整理されている
10. requirements / pyproject / packaging / README / docs の最小整合が取れている
11. MS15 へ引き継ぐ未実装事項が整理されている

---

## 14. Antigravity への実装指針

- まず B1〜B6 の責務を崩さないこと
- block scope を逸脱しそうなら、その内容は後続へ送ること
- Qt 側は参照元であり、wx 側へ丸転写しないこと
- コア導線 parity を優先し、見た目改善を目的化しないこと
- settings save は常に既存 key 保全を意識すること
- B6 で依存整合・文書整合まで閉じること

---

## 15. まとめ

MS14 は、Ver 0.4 系における **実用品への橋渡し** である。  
MS13 が「起動できる最小基盤」だったのに対し、MS14 は「最低限使える wx 主系」を成立させる段である。

そのため、MS14 では次を守ることが重要である。

- コア導線 parity を回復する
- MS15 を先取りしない
- settings と配布整合を壊さない
- block 単位で責務を閉じる

この block breakdown を、MS14 実装の正本方針として扱う。
