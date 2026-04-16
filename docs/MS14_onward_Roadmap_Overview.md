# MS14_onward_Roadmap_Overview

## 1. 文書情報

- 文書名: `MS14_onward_Roadmap_Overview.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象系列: `Ver 0.4.x`
- 主対象読者: `Antigravity`
- 記述言語: `日本語`
- 目的: `MS14 以降の実装ロードマップ、責務境界、優先順位、流入禁止範囲を整理する`

---

## 2. この文書の目的

本書は、Ver 0.4 系における **wxPython 主系への移行後の実装順序** を、Antigravity 側で安全に追従できるように整理するための概要文書である。

MS13 により、wx 主系の最小基盤はすでに成立している。  
以後の実装では、単に機能を足すのではなく、以下の順序で段階的に成熟させる。

1. wx 主系での実用コア導線回復
2. parity 回復
3. 再生系 UX 再構築
4. mp3 対応と WAV 同時出力
5. 音声のみ入力対応
6. リップ動作品質改善
7. 発音単位スロープ設定
8. 英語対応基礎

本書は、**MS14 以降の親ロードマップ** を固定し、各マイルストーンで何をやるか、何をやらないか、どこで止めるべきかを明文化することを目的とする。

---

## 3. 現在地（MS13 完了時点の前提）

### 3.1 到達済み事項
MS13 により、以下は成立済みである。

- `src/main.py` は wx 主系起動入口へ差し替え済み
- `src/gui_wx/` が新主系 GUI パッケージとして存在する
- `AutoLipToolApp` により `MainFrame` を起動できる
- `MainFrame` に最小 UI 骨格が存在する
- settings load / apply の最小導線が存在する
- controller / actions / worker stub / status 更新導線が存在する
- MS13 用の軽量統合チェックが存在する
- Qt GUI は凍結領域として保持し、新主系としては使わない

### 3.2 現在の制約
MS13 完了時点の wx GUI は、まだ「使えるアプリ」ではなく「起動できる最小骨格」である。  
そのため、以後の作業では **UI を派手に作り直すこと** よりも、**既存 core 処理を wx 側へ安全に接続していくこと** が優先される。

### 3.3 現時点の重要認識
- wx 側は起動と最小接続点までは成立している
- file 操作 / 解析 / 保存 / 再生はまだ本実装ではない
- 中央領域の波形 / Preview は placeholder 段階である
- 設定保存・配布整合・依存整合には未整理要素が残っている
- Qt 側は仕様参照元としては有用だが、主系としては扱わない

---

## 4. Ver 0.4 系の大枠ロードマップ

Ver 0.4 系の実装順は、以下で固定する。

1. **MS13**: wxPython 最小基盤移行
2. **MS14**: wx 版 parity 回復
3. **MS15**: 波形 / Preview / 再生系再構築
4. **MS16**: mp3 対応 + MMD 用 WAV 同時出力
5. **MS17**: 音声のみ入力対応
6. **MS18**: 同音母音谷スムージング改善
7. **MS19**: 発音単位スロープ設定
8. **MS20**: 英語対応基礎

---

## 5. 各マイルストーンの役割概要

## 5.1 MS14: wx 版 parity 回復
### 目的
wx 主系で、**TEXT読込 → WAV読込 → 解析実行 → VMD保存** の実用コア導線を成立させる。

### 主眼
- wx 側 UI を「起動だけできる状態」から「最低限使える状態」へ引き上げる
- Qt 側 main window の全再現ではなく、コア導線 parity を優先する
- 既存 core 処理を wx 側へ安全に接続する
- settings save、履歴、VMD 保存先記憶などの実用必須部分を戻す
- MS15 予定の波形 / Preview / 再生系本格移植は先取りしない

### 回復対象
- TEXT 読込
- WAV 読込
- テキスト変換結果表示
- WAV 基本情報表示
- 解析実行
- VMD 保存
- recent TEXT / WAV
- last VMD output dir
- busy / lock / status の基本整合
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`

### 非対象
- 波形表示の本格 port
- Preview 表示の本格 port
- PlaybackController 相当の本格導入
- Zoom / Pan / shared viewport
- テーマ再現
- i18n 切替本実装
- 大規模 MVC 再編

---

## 5.2 MS15: 波形 / Preview / 再生系再構築
### 目的
MS14 で回復したコア導線の上に、**視覚確認・再生確認・同期表示** の UX 基盤を再構築する。

### 主眼
- wx 側の波形表示
- wx 側の Preview 表示
- 再生位置同期
- オートスクロール
- 再生中の GUI 滑らか化
- 将来の Zoom / Pan / shared viewport の整理

### 非対象
- mp3 対応
- 音声のみ入力
- 英語対応
- リップ品質ロジック改善

---

## 5.3 MS16: mp3 対応 + MMD 用 WAV 同時出力
### 目的
入力音声の柔軟性を上げつつ、MMD 向けの安全な WAV 出力も同時に扱えるようにする。

### 主眼
- mp3 入力対応
- 必要に応じた decode / convert
- MMD 用 WAV の同時出力
- 出力先や命名の最小整理
- FFmpeg 利用前提との整合

### 非対象
- 音声のみ入力 UI の最終整理
- 再生系 UX 全体改善
- 英語対応

---

## 5.4 MS17: 音声のみ入力対応
### 目的
テキスト必須の前提を緩め、音声単体から扱える運用モードを導入する。

### 主眼
- 音声のみ入力導線
- 必要な UI 切替
- state 管理の分岐整理
- VMD 生成契約の見直し
- 既存 text + wav 導線との共存

### 非対象
- 英語対応
- 品質向上ロジックの大規模再設計

---

## 5.5 MS18: 同音母音谷スムージング改善
### 目的
同音母音連続時の谷形状や閉じ方を改善し、より自然なリップ動作へ寄せる。

### 主眼
- same-vowel valley 改善
- speech-internal continuity の自然化
- preview / export の整合維持
- 既存 writer / pipeline 契約の安全拡張

### 非対象
- 発音単位スロープの一般化
- 英語固有処理

---

## 5.6 MS19: 発音単位スロープ設定
### 目的
発音単位ごとの立ち上がり・立ち下がりの表現力を増やす。

### 主眼
- slope parameter の導入
- GUI / settings / writer / preview handoff
- 母音単位または event 単位の適用整理
- 既存 smoothing 系との競合整理

### 非対象
- 英語対応本格化
- 音声のみ入力の追加拡張

---

## 5.7 MS20: 英語対応基礎
### 目的
英語 UI / 文字列 / 将来の英語音声処理拡張へ向けた基礎層を導入する。

### 主眼
- GUI 文字列の英語対応
- settings 上の言語設定整理
- 文言長差への耐性確認
- help / status / warning などの基本文言整合
- 将来の英語音声処理へ向けた足場作り

### 非対象
- 英語音声解析の高度対応
- 発音辞書最適化
- 多言語全般対応

---

## 6. MS14 の位置づけ

MS14 は、Ver 0.4 系の中で最も重要な **橋渡しマイルストーン** である。

MS13 は「起動できる最小基盤」だった。  
MS15 は「視覚・再生 UX の再構築」になる。  
その間にある MS14 は、**実用コア導線を先に成立させる段** である。

したがって MS14 の主目的は、以下に限定される。

- wx 側での file open / analyze / save の parity 回復
- settings save / recent files / output dir 記憶の回復
- state 管理と action state の回復
- 口パラメータ操作導線の回復
- 依存・配布・起動整合の最小修正

MS14 は、**見栄えを整える段ではなく、実用品としての芯を戻す段** である。

---

## 7. MS14 の想定 block 構成

MS14 は、以下の block 構成を基本形とする。

### MS14-B1
* **実用 UI 骨格拡張**

- TEXT / WAV path 表示
- text / hiragana / vowel preview 表示領域
- WAV info 表示
- 口パラメータ入力部
- file / run / save の実用配置
- 中央波形 / Preview / 再生の placeholder 整理

### MS14-B2
* **状態管理と action state 回復**

- 選択状態
- 変換結果状態
- 解析結果状態
- busy state
- status 更新ルール
- enable / disable ルール
- invalidate 導線

### MS14-B3
* **入力導線 parity 回復**

- TEXT 読込
- WAV 読込
- text → hiragana → vowel
- WAV analyze
- counterpart auto load
- 読込失敗時復帰

### MS14-B4
* **解析実行 parity 回復**

- 解析 worker
- 実行中 lock
- 完了 / 失敗復帰
- current timing plan 保持
- 最小 status 反映

### MS14-B5
* **出力・履歴・settings save parity 回復**

- VMD save dialog
- overwrite confirm
- VMD 生成呼出
- recent files 更新
- last output dir 記憶
- wx 側利用設定の save
- merge-save による既存 key 保全

### MS14-B5B
* **Whisper 解析可用性 hardening と処理中 UI 補強**

- 分析中止導線 (soft cancel)
- soft timeout warning (150秒)
- フェーズ表示と warning 領域の確保
- 遅延 callback の UI 破壊防止
- busy 中 close の安全確保
- wx UI の main thread 更新契約

### MS14-B6
* **統合整理と parity closeout**

- B1〜B5 統合確認
- 軽量統合チェック
- requirements / pyproject / packaging 最小整合
- README / docs 同期
- MS15 引継ぎ整理

---

## 8. MS14 の責務境界

### 8.1 MS14 に含めるもの
- file open
- analyze
- save
- recent files
- output dir 記憶
- settings save の最小回復
- action state 回復
- basic status / warning 整理
- 口パラメータの最小操作導線

### 8.2 MS14 に含めないもの
- 波形表示の実装
- Preview 描画の本格 port
- 再生同期基盤
- shared viewport
- Zoom / Pan
- スムーズ再生 UX
- テーマ追従再現
- 言語切替 UI の本格運用
- 英語対応
- 大規模設計変更

### 8.3 MS14 の重要ルール
MS14 では **Qt 側 `main_window.py` を丸ごと wx に移植しない**。  
必要な機能を選別し、コア導線に必要な最小部分だけを wx 側へ移植・接続する。

---

## 9. settings に関する方針

### 9.1 基本方針
- 既存 ini / key 構造は可能な限り維持する
- MS14 では save を再導入する
- ただし、wx 側未使用 key を default で潰さない
- migrate / 新形式導入は行わない

### 9.2 保存方針
MS14 では、**load した既存設定を基礎に、wx 側が変更した key だけを反映して保存する** 形を原則とする。

### 9.3 MS14 時点で扱う想定 key
- `window_width`
- `window_height`
- `recent_text_files`
- `recent_wav_files`
- `last_vmd_output_dir`
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`

### 9.4 MS14 で扱わないもの
- settings dialog
- theme 完全反映
- language 実行時切替
- splitter / viewport 系高度保存
- migration

---

## 10. 依存・配布・整合に関する方針

MS14 closeout では、実装コードだけでなく **実行整合** も最小限そろえる。

対象:
- `requirements.txt`
- `pyproject.toml`
- `tool.setuptools.packages.find`
- README の GUI 記述
- build / packaging の最小整合

目的:
- fresh 環境でも wx 主系で起動できること
- wx 主系 package が build 対象から漏れないこと
- Ver 0.4 系の現在地が README と docs で矛盾しないこと

この整合は MS15 へ送らず、MS14 の出口で最低限閉じる。

---

## 11. Antigravity 向けの実装原則

### 11.1 block scope を厳守する
各 block は、その block の責務だけに限定すること。  
後続 block の内容を前倒し実装しないこと。

### 11.2 Qt 側を仕様参照元として使う
Qt 側コードは、再利用対象ではなく **仕様参照元** として扱う。  
wx 側へそのまま構造転写しないこと。

### 11.3 既存 core を壊さない
`core/`、`vmd_writer/`、既存 settings 契約は、MS14 では **接続側の修正を優先** し、意味変更を行わないこと。

### 11.4 state と表示を混線させない
- UI 表示
- アプリ状態
- core 呼出
- settings save
- status 更新

これらを 1 つのメソッドへ密結合させないこと。

### 11.5 先送りすべきものを明示する
MS15 以降の内容に踏み込みそうな場合は、実装で吸収せず、未実装事項として引継ぎへ残すこと。

---

## 12. マイルストーン間の依存関係

### 12.1 MS14 → MS15
MS15 は、MS14 で core workflow が成立していることを前提にする。  
MS14 が不十分なまま MS15 へ進むと、波形 / Preview / 再生の上に不安定な state 管理が乗るため危険。

### 12.2 MS15 → MS16 / MS17
再生・表示系がある程度落ち着いてからでないと、mp3 や音声のみ入力を加えた際の確認性が低下する。  
そのため、MS16 / MS17 は MS15 後とする。

### 12.3 MS18 / MS19
品質改善ロジックは、入力・表示・出力導線が安定してから着手する。  
先に品質ロジックをいじると、GUI 移行不具合との切り分けが難しくなる。

### 12.4 MS20
英語対応は最後ではないが、少なくとも MS14〜MS17 の導線が落ち着いてから入れる。  
理由は、文言差と状態差を同時に追うと不具合切り分けが悪化するためである。

---

## 13. 流入禁止ルール

### 13.1 MS14 への流入禁止
- 波形 / Preview / 再生本格実装
- Zoom / Pan / shared viewport
- テーマ再構築
- i18n 本格化
- MVC 再編
- 英語対応
- リップ品質改善ロジック

### 13.2 MS15 への流入禁止
- mp3 対応
- 音声のみ入力
- 英語対応
- quality logic 再設計

### 13.3 MS16 への流入禁止
- 音声のみ入力 full redesign
- same-vowel smoothing
- slope parameter
- 英語対応本体

### 13.4 MS17 への流入禁止
- mp3 / wav 変換再設計の再掘り返し
- quality logic 改善
- 英語対応本格化

### 13.5 MS18 / MS19 への流入禁止
- GUI フレームワーク再整理
- large UI redesign
- input modality 再設計
- i18n 本格化

---

## 14. MS14 完了条件（親ロードマップ上の定義）

MS14 は、以下を満たした時点で完了とみなす。

1. wx 主系で TEXT を読める
2. wx 主系で WAV を読める
3. text / hiragana / vowel / wav info が表示される
4. 解析実行が wx 側から行える
5. busy / lock / status が最低限整合する
6. VMD 保存が wx 側から行える
7. recent files と last output dir が使える
8. 口パラメータ入力が解析 / 出力に反映される
9. 波形 / Preview / 再生は未実装でも placeholder / disabled として整理されている
10. Ver 0.4 系の依存・配布・文書整合が最低限揃っている

---

## 15. MS15 以降の完了イメージ（概要）

### MS15 完了イメージ
- 波形と Preview が wx 側で表示される
- 再生位置同期が成立する
- 再生中の見え方と操作感が改善される

### MS16 完了イメージ
- mp3 を扱える
- 必要な WAV を安全に出せる

### MS17 完了イメージ
- 音声のみ入力モードが成立する

### MS18 完了イメージ
- same-vowel valley がより自然になる

### MS19 完了イメージ
- slope の制御が可能になる

### MS20 完了イメージ
- 英語 UI の基礎が成立する

---

## 16. Antigravity への引継ぎ要点

- Ver 0.4 系の主系はすでに wx である
- Qt 側は凍結領域であり、比較参照元としてのみ扱う
- 直近の最優先は MS14 であり、MS15 を先取りしない
- MS14 は「使える core workflow 回復」が主目的である
- settings save は **既存 key 保全** を強く意識する
- requirements / pyproject / docs の整合も MS14 の出口責務に含める
- 後続マイルストーンの価値は、MS14 を過不足なく閉じられるかに大きく依存する

---

## 17. まとめ

Ver 0.4 系は、単なる GUI 置換ではない。  
**wx 主系へ軸足を移したうえで、実用 workflow を回復し、視覚・再生 UX を再構築し、その後に入力形式拡張・品質改善・英語対応へ進む** という段階設計である。

この順序を崩すと、移行不具合、状態管理不整合、表示責務の混線、後続仕様の先食いが起こりやすい。  
そのため、Antigravity 側では以下を最重要ルールとして扱う。

- まず MS14 を、コア導線回復として閉じる
- 次に MS15 で表示・再生 UX を再構築する
- 以後の拡張は、その上に積む

以上を、MS14 以降の親ロードマップ概要として固定する。
