# MS12-2 Implementation Plan

## 0. 文書目的

MS12-2 は、
**processing-time UI responsiveness improvement**
を導入するための最小実装タスクである。

本タスクの目的は、
解析処理中でも GUI が極端に固まって見えないようにし、
**少なくともウィンドウ移動・再描画・進行中ダイアログ表示が自然に成立する状態**
へ寄せることである。

ここで重視するのは応答性の改善であり、

- pipeline アルゴリズムの改善
- VMD 出力仕様の変更
- Preview semantics の変更
- splash / packaging の変更

は対象外とする。

---

## 1. 現在の前提

MS12-2 着手時点で、repo には次の土台がある。

- `src/gui/main_window.py`
  - 処理開始 / 処理終了 / action state / status 表示の司令塔
  - `_is_processing` による二重実行防止
  - `QProgressDialog` による処理中表示
- `src/gui/waveform_view.py`
  - morph label の UI 反映先
- `src/gui/preview_area.py`
  - preview の UI 反映先
- `src/gui/view_sync.py`
  - shared viewport / shared playback の UI 同期ハブ

また、現時点で確認できる事実は次のとおり。

- `_run_processing()` は `_begin_processing_session()` で busy state へ入る
- `_begin_processing_session()` は `QApplication.processEvents()` を 1 回呼ぶのみである
- 実際の重処理は `_refresh_waveform_morph_labels()` 内から
  `build_vowel_timing_plan(...)` を同期呼び出ししている
- `current_timing_plan` の代入、waveform morph label 反映、preview 更新は同じ経路の中で行われる
- `_end_processing_session()` は dialog を閉じ、completion sound と action state 復帰を担う

したがって、現状の UI 固まり感の主因は、
**重処理と UI 更新責務が 1 本の同期経路に載っていること**
である。

---

## 2. このタスクの目標

MS12-2 の目標は次のとおり。

1. 重処理の実行を UI スレッドから分離する
2. 成功 / 失敗 / 復帰を signal ベースで main window へ返す
3. 既存の `_is_processing` ガードと操作ロックを維持する
4. waveform / preview / status 更新は UI スレッド側でのみ適用する

完了像は、
**既存の分析フローと結果表示は維持したまま、処理中の GUI 応答だけを改善した状態**
である。

---

## 3. 壊さない前提

MS12-2 では、以下を壊さない前提を固定する。

- `build_vowel_timing_plan(...)` の入力と出力意味は変えない
- `current_timing_plan` は UI 側の canonical state のまま維持する
- waveform への morph event 反映契約は変えない
- Preview は current timing plan と GUI 現在値から再構成する契約を変えない
- `_is_processing` による二重実行防止を維持する
- 処理中 dialog の存在は維持する
- 失敗時 warning と status 復帰の導線は維持する
- 保存可否や playback 可否の action state 判定は維持する

重要:

- worker 側から QWidget や matplotlib canvas を直接触らない
- `current_timing_plan` の更新は UI スレッド側でのみ行う
- `QMessageBox` や status 更新は worker 側で行わない
- キャンセル機能は今回追加しない

---

## 4. スコープ

### 4.1 対象

- `src/gui/main_window.py`
- 必要なら新規の GUI-side helper module
- 必要なら最小 worker / signal helper
- GUI 側の最小回帰テスト
- 関連文書

### 4.2 非対象

- pipeline / writer のロジック変更
- whisper model 切替や progress 詳細化
- 処理キャンセル機能
- export 非同期化
- splash / packaging 改修

---

## 5. 現状コード上の整理

### 5.1 `_run_processing()`

現状の `_run_processing()` は次の流れである。

1. 入力不足や未解析前提を検証する
2. `_begin_processing_session()` で `_is_processing = True` にする
3. `_refresh_waveform_morph_labels()` を呼ぶ
4. `current_timing_plan` の有無で成功 / 失敗を分ける
5. `_set_ready_status()` を呼ぶ
6. `finally` で `_end_processing_session()` を呼ぶ

このため、現状は
**処理本体と UI 反映が同一 call stack に載っている**
。

### 5.2 `_refresh_waveform_morph_labels()`

この関数は現在、
単なる UI refresh ではなく、次を同時に担っている。

- 入力妥当性の追加確認
- `build_vowel_timing_plan(...)` の同期実行
- `current_timing_plan` の更新
- waveform morph label の反映
- preview 更新

MS12-2 では、ここをそのまま worker に渡すのではなく、
**計算責務と UI 反映責務へ分ける**
必要がある。

### 5.3 `_begin_processing_session()` / `_end_processing_session()`

この 2 つは現状、

- busy state の開始 / 終了
- dialog show / hide
- status text
- action state 更新
- completion sound

をまとめて扱っている。

MS12-2 ではこの責務を大きく変えず、
**worker 起動前後の共通入口 / 出口**
として再利用するのが自然である。

---

## 6. 実装方針

### 6.1 基本方針

MS12-2 は、
**重処理だけを worker へ逃がし、GUI state 更新は main window に残す**
方針で進める。

方針は次の順に固定する。

1. worker 入力 payload を最小定義する
2. worker は timing plan の生成だけを担う
3. 成功 / 失敗 / 完了 signal を main window へ返す
4. UI 反映は main window の受け口で行う
5. 既存 action state / status / warning 契約を維持する

### 6.2 設計原則

- worker には QWidget を渡さない
- worker には `selected_text_content` / `selected_wav_path` / `selected_wav_analysis` /
  `upper_limit` のような計算に必要な最小値だけを渡す
- worker 成功時は `VowelTimingPlan` またはそれに準じる結果だけを返す
- UI 側で `self.current_timing_plan = result` を行い、
  その後に waveform / preview / status を更新する
- 失敗は UI 側で既存 warning 導線へ寄せる
- worker の寿命管理は main window 側で保持する

---

## 7. 想定実装ステップ

### Phase 1

責務分離の下準備

- `_refresh_waveform_morph_labels()` から「計算」と「UI反映」を分離する
- UI 反映専用の helper を切り出す
- worker に渡す最小入力セットを定義する

### Phase 2

worker / signal 導入

- `QThread` もしくは同等の最小 worker 導線を導入する
- 成功 / 失敗 / 完了 signal を定義する
- main window に active worker / active thread の保持先を追加する

### Phase 3

main window 受け口接続

- `_run_processing()` で worker 起動へ切り替える
- 成功 signal で timing plan を UI state へ反映する
- 失敗 signal で warning と status を復帰する
- 完了 signal で `_end_processing_session()` を通す

### Phase 4

UI 復帰整合

- 二重実行防止が崩れないことを確認する
- 処理中の action state が維持されることを確認する
- playback / save / zoom / input controls の enable state が従来どおり戻ることを確認する

### Phase 5

最小回帰テスト追加

- worker 起動中に `_is_processing` が維持される
- 成功時に timing plan / preview / waveform が反映される
- 失敗時に warning と status 復帰が行われる
- 完了時に `_end_processing_session()` 相当が通る

---

## 8. 実装候補

### 候補A: `QThread` + `QObject` worker

利点:

- signal / slot で成功 / 失敗 / 完了を素直に扱える
- PySide6 で責務境界が明確
- GUI スレッド復帰の流れが読みやすい

現時点ではこの案を第一候補とする。

### 候補B: `QRunnable` / thread pool

利点:

- 軽量

懸念:

- 今回は単発処理であり、成功 / 失敗 / 完了 signal と寿命管理の明示性を優先したい

このため、MS12-2 では第一候補にしない。

### 候補C: `QtConcurrent`

利点:

- 実装量は少ない可能性がある

懸念:

- repo の現在構成では、失敗通知・完了通知・寿命管理の見通しがやや落ちる

このため、MS12-2 では第一候補にしない。

---

## 9. worker 境界の仮置き

現時点の第一候補は次の分離である。

### worker 側に置くもの

- `build_vowel_timing_plan(...)`
- その前提となる最小入力の受け取り
- 例外捕捉と error payload 化

### UI 側に残すもの

- `_begin_processing_session()` / `_end_processing_session()`
- `self.current_timing_plan` の代入
- `self.wav_waveform_view.set_morph_events(...)`
- `_update_preview_from_current_timing_plan()`
- `_set_ready_status()`
- `_show_warning(...)`
- `_update_action_states()`

この境界により、
**worker は pure-ish な計算実行器、main window は状態遷移と描画反映の司令塔**
として整理できる。

---

## 10. テスト方針

最低限、次を押さえる。

1. 処理開始時に `_is_processing` と action lock が入る
2. worker 成功時に `current_timing_plan` が更新される
3. worker 成功時に waveform / preview 更新が UI 側で呼ばれる
4. worker 失敗時に warning 導線が維持される
5. worker 完了時に dialog が閉じ、busy state が解除される

可能なら追加で押さえる。

- 処理中でもメインウィンドウがイベントループ上で生きていることを示す GUI テスト
- 連打時に二重 worker 起動しないこと

---

## 11. 保留課題

### 保留1

worker 用 helper を `main_window.py` 内に置くか、別 module に分けるか

現時点の仮置き:

- 初回実装は差分最小化を優先し、
  **小さければ `main_window.py` 内部、膨らむなら専用 helper module**
  とする

### 保留2

worker 成功時の payload を `VowelTimingPlan` 単体にするか、
補助メタデータ付き object にするか

現時点の仮置き:

- 現行 UI 反映に必要なのは timing plan 本体が中心なので、
  **まずは `VowelTimingPlan` 中心の最小 payload**
  を第一候補とする

### 保留3

`_refresh_waveform_morph_labels()` を残すか、役割名ごとに改名 / 分割するか

現時点の仮置き:

- MS12-2 では必要最小限の責務分離を優先し、
  **全面改名よりも計算 helper と UI apply helper の切り出し**
  を第一候補とする

### 保留4

completion sound を worker 完了ごとに常に鳴らすか、成功時のみへ寄せるか

現時点の仮置き:

- 既存契約維持を優先し、
  **現状どおり `_end_processing_session()` 側の動作に従う**
  ことを第一候補とする

### 保留5

処理中 dialog を application modal のままにするか

論点:

- UI 応答性改善と dialog modality は別問題
- modal のままでも repaint / move が成立すれば今回の目的は達成しうる

現時点では問い合わせず、
**dialog 仕様はできるだけ維持したまま、まず重処理切り離しで体感改善を確認する**
方針とする

---

## 12. 完了条件

- 処理中でも GUI が極端に固まらない
- `_is_processing` による二重実行防止が維持される
- 成功時に waveform / preview / status が従来どおり反映される
- 失敗時の warning / status 復帰が崩れない
- completion 後に dialog / action state / busy flag が復帰する
- 既存の save / playback / zoom / parameter 操作の整合が崩れない

---

## 13. リスク

### リスク1

worker から UI を直接触ってクラッシュや不定動作を起こす

対策:

- QWidget / canvas 操作は UI スレッド側に限定する

### リスク2

成功 / 失敗 / 完了 signal の順序が不安定で、dialog や busy state が壊れる

対策:

- 完了経路を 1 本に寄せる
- `begin -> worker start -> result handling -> end` の順を固定する

### リスク3

処理途中で入力 state が変わり、反映対象が古い結果と競合する

対策:

- 処理中は既存どおり入力操作をロックする
- まずは単一 worker / 単一 in-flight を前提にする

### リスク4

責務分離の過程で `_run_processing()` 周辺が大きくなりすぎる

対策:

- 初回は最小 helper 抽出に留める
- 大きな再設計は MS12-2 の目的外とする

---

## 14. この段の出口

MS12-2 の出口は、
**処理本体が UI スレッドを長時間占有せず、既存の分析フローと UI 結果反映を保ったまま応答性だけを改善した状態**
である。

ここまで完了した後に、
次段の `MS12-3: splash timing improvement`
へ進む。
