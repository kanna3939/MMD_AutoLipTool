# MS12-1 Implementation Plan

## 0. 文書目的

MS12-1 は、
**VMD 保存先フォルダの記憶と永続化**
を導入するための最小実装タスクである。

本タスクの目的は、
VMD 保存ダイアログを開いたときに、
**直前に正常保存できた出力先フォルダを初期フォルダとして再利用できるようにすること**
である。

ここで重視するのは利便性の改善であり、

- VMD 出力内容
- Preview 表示
- pipeline / writer の挙動
- splash / responsiveness / packaging

は対象外とする。

---

## 1. 現在の前提

MS12-1 着手時点で、repo には次の土台がある。

- `src/gui/main_window.py`
  - 保存ダイアログ起点
  - VMD export 成功 / 失敗の分岐
  - recent TEXT / WAV の保持
- `src/gui/settings_store.py`
  - ini ベースの設定保存 / 読込
  - TEXT / WAV recent history を含む UI 設定永続化

また、現時点で確認できる事実は次のとおり。

- TEXT / WAV の読込ダイアログについては、直前ディレクトリ保持がある
- VMD 保存ダイアログの初期フォルダは現状 `""` 固定である
- VMD 保存成功後に、保存先フォルダを settings へ記憶する契約は未導入である
- close 時には `request_recent_history_save()` により recent 系が保存される

---

## 2. このタスクの目標

MS12-1 の目標は次のとおり。

1. VMD 保存成功時のみ、保存先親フォルダを記憶する
2. 次回の VMD 保存ダイアログ初期フォルダへ反映する
3. アプリ再起動後も復元される
4. cancel / save失敗 / validation failure では保存先記憶を更新しない

完了像は、
**既存の保存フローを壊さずに、保存ダイアログの開始位置だけが賢くなる状態**
である。

---

## 3. 壊さない前提

MS12-1 では、以下を壊さない前提を固定する。

- VMD 出力ファイルの中身は変えない
- 保存ファイル名の提案ロジックは変えない
- overwrite confirm の流れは変えない
- 保存前の入力チェックと warning 導線は変えない
- `current_timing_plan` の扱いは変えない
- recent TEXT / WAV の仕様は変えない
- settings save failure 時の disable 契約は変えない

重要:

- 「最後に選んだフォルダ」ではなく、
  **最後に正常保存できた VMD 出力先フォルダ**
  を記憶対象とする
- cancel や overwrite confirm で No を選んだだけでは更新しない
- path validation に失敗した出力先は記憶しない

---

## 4. スコープ

### 4.1 対象

- `src/gui/main_window.py`
- `src/gui/settings_store.py`
- `tests/test_settings_store.py`
- 必要なら `tests/test_main_window_*`
- 関連文書

### 4.2 非対象

- VMD 最近使ったファイル一覧
- 保存履歴 UI
- 出力ファイル名の自動命名改善
- 出力先の複数候補記憶
- processing responsiveness 改修
- splash / packaging 改修

---

## 5. 現状コード上の整理

### 5.1 `main_window.py`

現状の VMD 保存は `_export_vmd()` が担っている。

確認できている流れ:

1. 入力不足や未解析状態を検証する
2. `QFileDialog.getSaveFileName(...)` を呼ぶ
3. `output_path` を `_resolve_vmd_output_path(...)` で検証する
4. 必要なら overwrite confirm を出す
5. `generate_vmd_from_text_wav(...)` を実行する
6. 成功時に success message と status 更新を行う

このため、保存先記憶の更新点として自然なのは、
**VMD 生成成功後、success message の前後**
である。

### 5.2 `settings_store.py`

現状の settings 永続化は次を扱う。

- theme
- splitter ratio
- window size
- language
- morph upper limit
- closing hold / softness
- recent TEXT files
- recent WAV files

したがって、MS12-1 では
**新しい settings key を最小追加し、既存 normalize/save/load 導線へ乗せる**
のが自然である。

---

## 6. 実装方針

### 6.1 基本方針

MS12-1 は、
**recent TEXT / WAV と同じ「GUI 利便性のための永続設定」レイヤ**
で扱う。

方針は次の順に固定する。

1. settings key と default を追加する
2. startup settings から main window へ流し込む
3. VMD 保存ダイアログ初期フォルダの解決へ接続する
4. 保存成功時だけ記憶更新する
5. 最小テストで契約を固定する

### 6.2 設計原則

- 保存対象は「フォルダのみ」とし、ファイル名までは記憶しない
- `recent` 一覧とは別管理にする
- 文字列として保持しても、利用時には既存の dir validation を通す
- 存在しないフォルダやディレクトリでない path は初期フォルダに使わない
- settings save が無効化されている場合でも、同一セッション内の再利用は壊さない方向を優先する

---

## 7. 想定実装ステップ

### Phase 1

settings 契約追加

- `settings_store.py` に VMD 保存先フォルダ用 key を追加
- default settings に空値を追加
- normalize 対象に追加
- save / load round-trip が通る形を定義する

### Phase 2

main window の状態保持追加

- startup settings から VMD 保存先フォルダを受け取る
- main window 内の保持先を追加する
- 既存の `last_text_dialog_dir` / `last_wav_dialog_dir` と混線しない名前にする

### Phase 3

保存ダイアログ初期フォルダ接続

- VMD 保存ダイアログで、記憶済みフォルダを初期値として使う
- 利用前に既存と同等のディレクトリ妥当性チェックを通す

### Phase 4

成功時のみ記憶更新

- `generate_vmd_from_text_wav(...)` 成功後に親フォルダを記憶する
- overwrite confirm No / cancel / 例外系では更新しない
- 必要なら settings 保存を即時反映する

### Phase 5

最小回帰テスト追加

- settings round-trip
- invalid path fallback
- 保存成功時のみ更新
- cancel / failure では不更新

---

## 8. 実装候補

### 候補A: 専用 key 追加

例:

- `last_vmd_output_dir`

利点:

- recent 系と意味が混ざらない
- 単一責務で分かりやすい

現時点ではこの案を第一候補とする。

### 候補B: recent 出力履歴へ先回り拡張

例:

- recent VMD file list を持ち、その先頭親ディレクトリを初期値に使う

問題点:

- MS12-1 の目的を超える
- UI / menu / pruning 契約が広がる

このため、MS12-1 では採らない。

---

## 9. テスト方針

最低限、次を押さえる。

1. `SettingsStore` で保存先フォルダ key が save / load round-trip する
2. 空文字や不正値は default 扱いに戻る
3. main window が記憶済みフォルダを save dialog 初期フォルダに渡す
4. 保存成功時のみ記憶が更新される
5. cancel / export failure / overwrite No では更新されない

可能なら追加で押さえる。

- 記憶済みフォルダが存在しない場合は空初期値にフォールバックする
- settings save が無効化されていても、同一セッションの再利用だけは維持されるか

---

## 10. 保留課題

### 保留1

settings key 名を `recent` セクションに置くか、`ui` セクションに置くか

現時点の仮置き:

- 既存 recent 系と近い意味だが、
  UI フロー上の初期ディレクトリ設定でもあるため、
  **既存 section 構成との一貫性を見て実装時に最終決定**
  とする

### 保留2

保存成功直後に settings を即時保存するか、close 時保存に寄せるか

論点:

- 即時保存なら異常終了時にも残りやすい
- close 時保存だけだと、保存直後に落ちた場合に残らない

現時点では問い合わせず、
**MS12-1 実装時に既存 recent history save 導線との整合で判断**
する

### 保留3

存在しない remembered dir を load 時に正規化で落とすか、利用時だけ弾くか

現時点の仮置き:

- 保存値自体は保持し、
  **利用時の `_resolve_dialog_initial_dir(...)` 側で弾く**
  案が第一候補

### 保留4

settings save 失敗時の扱い

論点:

- 同一セッションの記憶だけは残すか
- settings 永続化失敗 warning を追加するか

現時点では既存契約を優先し、
**新しい warning 契約は増やさず、既存 save failure handling に従う**
方向を第一候補とする

---

## 11. 完了条件

- VMD 保存成功後、次回 save dialog の初期フォルダが更新される
- 再起動後も記憶済みフォルダが復元される
- cancel / overwrite No / export failure では更新されない
- overwrite confirm と save validation が崩れない
- 既存の recent TEXT / WAV や UI 設定保存が壊れない
- 関連最小テストが通る

---

## 12. リスク

### リスク1

保存先記憶更新のタイミングを誤り、失敗時の path まで記憶してしまう

対策:

- 成功点を `generate_vmd_from_text_wav(...)` 正常終了後に限定する

### リスク2

settings key 追加で load/save の互換性を崩す

対策:

- default / normalize / parser build / parser read の 4 点をセットで更新する

### リスク3

TEXT/WAV 用 remembered dir と混線し、別ダイアログの初期値まで変える

対策:

- VMD 用の専用 state を分離する
- 既存 `last_text_dialog_dir` / `last_wav_dialog_dir` へ流用しない

---

## 13. この段の出口

MS12-1 の出口は、
**VMD 保存ダイアログの使い勝手改善だけを、既存 export 契約を壊さずに導入した状態**
である。

ここまで完了した後に、
次段の `MS12-2: processing-time UI responsiveness improvement`
へ進む。
