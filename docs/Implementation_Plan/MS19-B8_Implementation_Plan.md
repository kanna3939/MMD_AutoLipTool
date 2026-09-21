# MS19-B8 Implementation Plan

## 1. 文書情報

- Milestone: MS19
- Block: B8
- Title: Workspace Reset / New Session Flow
- Status: Completed
- 作成日: 2026-07-11
- 前提:
  - MS19-B1からMS19-B7までは完了済み。
  - MS19-B7のユーザー確認は通過・問題なし。
  - MS19 CloseoutはB9で完了済みである。
  - B8は、現在のTEXT・音声・解析結果を安全に破棄し、次の作業へ移れる導線を追加するBlockである。
- 実装方針サマリ:
  - ファイルメニューに `新規作業...\tCtrl+N` を追加し、これをB8の正本導線とする。
  - `UiState` 全交換は行わず、作業データだけを初期化する専用契約を追加する。
  - 最近使ったファイル、テーマ、パラメータ、ダイアログ履歴、保存先履歴は保持する。
  - 元のTEXT・音声、保存済みVMD・MMD用WAV、解析用WAVキャッシュ実体は削除しない。
  - Busy中は新規作業を実行不可とし、workerのキャンセルと初期化を一操作へ混在させない。

## 2. 背景

MS19-B1からB7により、TEXTあり入力と音声のみ入力の双方で、音声読込、解析、書き起こし確認・編集、Preview、VMD保存まで成立した。

一方、現行GUIには、1件の作業完了後にTEXT・音声・書き起こし・解析結果・表示状態をまとめて初期化する導線がない。次の素材へ移る場合、別ファイルを上書き読込することはできるが、TEXTありから音声のみへ切り替える場合や、現在結果を明示的に破棄して空の状態へ戻したい場合に操作が分かりにくい。

現行実装には以下の部分処理が存在する。

- `UiState.clear_transcription_state()` は書き起こし関連だけを消す。
- `UiState.invalidate_analysis()` はtiming planを破棄するが、`analysis_pending_rebuild = True` とするため、新規作業の初期状態とは異なる。
- `AppController._clear_selected_audio_state()` は選択音声関連だけを消す。
- `AppController.request_playback_stop()` は再生状態とカーソルを戻す。
- `ViewportController.set_duration(0.0)` でviewportを空へ戻せる。

これらを利用できるが、現在は作業全体の初期化順序と、保持する設定・履歴の境界が定義されていない。B8では、この境界を明示したうえで、安全な新規作業導線を追加する。

## 3. 目的

- 現在の入力・解析・表示状態を一操作で初期状態へ戻せるようにする。
- TEXTあり / voice_onlyのどちらからでも同じ未入力状態へ戻せるようにする。
- 既存の設定・履歴を失わず、次のTEXT・音声をすぐ選択できるようにする。
- 古いtiming plan、書き起こし、Preview、再生位置、worker callbackが次作業へ混入しないようにする。
- B9 Closeout前に、複数素材を連続処理する基本ワークフローを成立させる。

## 4. In Scope

- ファイルメニューへの `新規作業...\tCtrl+N` 追加。
- 新規作業メニューのBusy連動。
- 作業データ存在時の確認ダイアログ。
- 確認キャンセル時の完全な状態維持。
- `UiState.has_workspace_user_data` 相当の確認要否判定。
- 確認要否にかかわらず、worker失敗状態、表示、job IDを初期状態へ正規化するreset実行契約。
- `UiState.reset_workspace()` 相当の作業データ限定初期化。
- TEXT、ひらがな、母音列、音声、書き起こし、timing plan、選択イベントのクリア。
- 解析・VMD保存・MMD用WAV出力・再生・Zoomの操作可否再計算。
- 再生停止、再生位置、loaded playback path、viewportの初期化。
- InfoPanel、Waveform、Preview、RightPane選択表示の初期表示復帰。
- audio job IDとanalysis job IDの無効化によるlate callback対策。
- TEXTあり / voice_only / 編集適用後 / 解析成功後 / VMD保存後の状態テスト。
- 関連仕様・README・配布用readmeへの新規作業導線反映。
- MS19-B9へのCloseout繰り下げと関連進捗文書同期。

## 5. Out of Scope

- アプリケーション設定の初期化。
- 最近使ったファイル履歴の削除。
- テーマ、モーフ上限、開口維持、閉口スムーズの既定値復元。
- 入力元TEXT・音声ファイルの削除。
- 保存済みVMD・MMD用WAVの削除。
- 解析用WAVキャッシュ実体の即時削除。
- Busy中workerを自動キャンセルして、そのままリセットする複合操作。
- dedicated toolbar / top-panelリセットボタンの追加。
- Undoによるリセット前状態の復元。
- 複数案件・タブ・プロジェクト保存。
- Qt / PySide6 GUIの変更。
- MS19 Closeout判定。

## 6. 前提条件

- `UiState` は作業状態と永続・履歴状態を同じdataclass内に保持している。
- `UiState` の新規インスタンスへの交換は、テーマ、履歴、保存先等を失うため採用しない。
- `invalidate_analysis()` は入力変更後の再解析待ち用であり、新規作業完了後の状態には直接使わない。
- 新規作業完了後は `analysis_pending_rebuild = False`、`status_key = StatusKey.IDLE` とする。
- Busy中はメニューを無効化し、ユーザーは既存の中止導線で処理終了後に新規作業を実行する。
- recent filesとlast directory群は次素材選択を助けるため保持する。
- `last_mmd_wav_output_path` は現在作業に結び付くためクリア対象とするが、`last_mmd_wav_export_dir` は保持する。
- ファイル削除は行わず、sessionからの参照だけを外す。

## 7. 対象ファイル

主対象:

- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/info_panel.py`

表示連携確認対象:

- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/waveform_panel.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/viewport_controller.py`
- `src/gui_wx/playback_controller.py`

テスト候補:

- 新規 `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_wx_ms14_b1_ui.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b3_input.py`
- `tests/test_wx_ms15_b1_waveform.py`
- `tests/test_wx_ms15_b2_preview.py`
- `tests/test_wx_ms15_b3_playback.py`
- `tests/test_wx_ms15_b5_state_theme.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms16_b6_event_selection_foundation.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`

ユーザー向けdocs:

- `README.md`
- `readme_mmdautolip.txt`

関連仕様・進捗docs:

- `docs/GUI_State_Theme_Specification.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

## 8. 実装方針

### 8.1 UI導線

ファイルメニュー先頭に以下を追加する。

```text
新規作業...	Ctrl+N
----------------
TEXT読み込み...
音声読み込み...
```

メニュー項目の説明は「現在の入力と解析結果をクリアして、新しい作業を開始します」とする。

B8ではファイルメニューを正本導線とする。専用ボタンは画面密度とアイコン配置への影響があるため必須範囲に含めない。

### 8.2 実行可否

- Busyでない場合は新規作業メニューを有効にする。
- Busy中は無効にする。
- 確認要否はユーザー作業データの有無で判定し、reset実行そのものとは分離する。
- TEXT、音声、書き起こし、解析結果、再生対象、現在作業の出力参照のいずれかがある場合は確認する。
- ユーザー作業データがない場合は確認を省略するが、reset処理は実行し、残存するworker失敗状態・表示・job IDを正規化する。
- 繰り返し実行後もユーザーから見える作業状態が同じ未入力初期状態へ収束する、意味上のidempotent操作とする。late callback無効化用の単調増加job IDはこの同値判定から除外する。

### 8.3 確認ダイアログ

確認文言案:

```text
現在の入力と解析結果をクリアして、新しい作業を開始します。
元のTEXT・音声ファイルと、保存済みファイルは削除されません。

続行しますか？
```

- `YES_NO | NO_DEFAULT | ICON_QUESTION` を使用する。
- `No` またはダイアログクローズ時は、UiState・表示・再生・job IDを一切変更しない。
- 「未保存変更」という断定はしない。現行実装にはVMD保存済み判定の正本がないためである。

### 8.4 UiState初期化契約

`reset_workspace()` でクリアする項目:

- `selected_text_path`
- `selected_text_content`
- `selected_hiragana_content`
- `selected_vowel_content`
- `selected_audio_input`
- `selected_audio_probe`
- `selected_analysis_wav`
- `selected_wav_path`
- `selected_wav_analysis`
- transcription / analysis text関連全項目
- `current_timing_plan`
- `analysis_result_valid`
- `analysis_pending_rebuild`
- `selected_source_event_index`
- `audio_worker_state`
- `is_playing`
- `playback_position_sec`
- `loaded_playback_path`
- `last_mmd_wav_output_path`
- `input_mode` を `text_audio` へ戻す
- `status_key` を `IDLE` へ戻す

保持する項目:

- `recent_text_files`
- `recent_wav_files`
- `recent_audio_files`
- `last_text_dialog_dir`
- `last_wav_dialog_dir`
- `last_audio_dialog_dir`
- `last_vmd_output_dir`
- `last_mmd_wav_export_dir`
- `theme_mode`
- `resolved_theme`
- controller / ParameterPanelが保持する解析パラメータ
- `current_audio_job_id` の単調増加契約

`audio_worker_state` や失敗表示だけが残っている場合は確認対象としない。ただし、確認を省略したresetでこれらを初期状態へ戻す。

### 8.5 job / worker契約

- 実行前提としてBusyではないため、active workerの強制停止は行わない。
- reset確定時に `invalidate_audio_job()` を呼び、古いaudio callbackを破棄する。
- `current_audio_job_id` はresetごとに進め、古いaudio callbackを反映しない。
- MainFrame側のanalysis job IDも単調に進め、古いanalysis callbackを反映しない。現行の次回解析が `+= 1` で採番するため、`None` や0へ設定しない。
- job IDを巻き戻さない。ID再利用によるlate callback誤受理を避ける。
- `_audio_worker` / `_worker` のactive実体を、Busyでないという前提なしに黙って破棄しない。

### 8.6 playback / viewport契約

- 再生中なら `PlaybackController.stop()` を呼ぶ。
- `is_playing = False`、`playback_position_sec = 0.0`、`loaded_playback_path = None` とする。
- playback cursorをクリアする。
- `ViewportController.set_duration(0.0)` または同等処理でduration、zoom、viewportを初期化する。
- Play / Stop / Zoom操作を無効化する。

### 8.7 表示初期化契約

InfoPanel:

- `TEXT: (未選択)`
- `WAV: (未選択)`
- text / hiragana / vowel / WAV infoを空にする
- 書き起こし編集を不可にする
- 適用 / 元に戻すを無効化する

Waveform / Preview:

- Waveformを「WAVファイルが読み込まれていません」へ戻す
- Previewを未解析状態へ戻す
- playback cursor、viewport、イベント選択をクリアする

RightPane / Status:

- 選択イベント表示をクリアする
- B8で現在作業に由来する警告を追加する場合はクリアする
- Statusを `待機中` へ戻す

### 8.8 設定・ファイル保持契約

- source TEXT / audioは削除しない。
- VMD / MMD用WAV出力は削除しない。
- analysis WAV cacheは現行cache方針に任せ、B8で即時削除しない。
- recent filesとlast directoryを保持する。
- 新規作業実行そのものをsettings変更として保存する必要はない。
- `last_mmd_wav_output_path` のみ現在作業結果参照としてクリアする。

## 9. 詳細ステップ

1. B8実装開始時のrepo状態とB7コミット状態を確認する。
2. `UiState` にユーザー作業データに基づく確認要否判定を追加し、reset実行契約とは分離する。
3. `UiState.reset_workspace()` を追加し、クリア対象と保持対象を単体テストで固定する。
4. `InfoPanel` に初期表示へ戻す最小helperを追加する。
5. `MainFrame` のファイルメニューへ `新規作業...\tCtrl+N` を追加する。
6. Busy連動とイベントbindingを追加する。
7. 作業データ存在時の確認ダイアログを実装する。
8. `AppController.request_reset_workspace()` を追加し、job、playback、viewport、UiStateを順に初期化する。
9. MainFrame側analysis job IDを単調に進め、表示を初期化する。
10. TEXTあり、voice_only、編集適用後、解析成功後、保存後の各状態からリセットするテストを追加する。
11. キャンセル、Busy中、late callback、設定・履歴保持をテストする。
12. README / 配布用readme / 関連仕様docsを同期する。
13. 対象テストと通常全体テストを実行し、表示上のpass数とprocess exit codeを分けて記録する。

## 10. 状態遷移 / データ契約

### 10.1 未入力状態

```text
未入力
  └─ 新規作業
       └─ 未入力 / status=IDLE（確認省略、可視状態は初期状態へ収束。job IDは無効化のため進む場合がある）
```

### 10.2 TEXTあり解析済み

```text
text_audio / analysis_ready / VMD保存可
  └─ 新規作業確認 Yes
       └─ text_audio既定 / status=IDLE / 未入力 / analysisなし / VMD保存不可
```

### 10.3 voice_only解析済み

```text
voice_only / transcriptionあり / analysis_ready
  └─ 新規作業確認 Yes
       └─ transcriptionなし / timing resultなし / analysisなし
```

### 10.4 編集適用後の再解析待ち

```text
voice_only / user edited / analysis_pending_rebuild
  └─ 新規作業確認 Yes
       └─ analysis_pending_rebuild = False / status = IDLE
```

### 10.5 確認キャンセル

```text
任意の作業状態
  └─ 新規作業確認 No
       └─ UiState / 表示 / playback / job IDすべて不変
```

### 10.6 Busy中

```text
analysis worker または audio worker実行中
  └─ 新規作業メニュー無効
       └─ 既存の中止導線を使用
```

## 11. テスト方針

### 11.1 新規B8テスト

新規 `tests/test_ms19_b8_workspace_reset.py` では最低限以下を確認する。

- pristine stateを繰り返しresetしても、job IDを除く可視ワークスペースが同じ未入力初期状態へ収束する
- TEXTあり入力状態を完全にクリア
- voice_only書き起こし・timing resultを完全にクリア
- 解析成功後のtiming planとVMD保存可否をクリア
- 編集適用後の `analysis_pending_rebuild` をFalseへ戻す
- recent files、last directories、themeを保持
- `last_mmd_wav_output_path` をクリア
- audio job IDを単調に進め、0へ戻さない
- analysis job IDを単調に進め、`None` や0へ戻さない
- ユーザー作業データがなくても、残存する `audio_worker_state` と失敗表示を確認なしで初期化
- playback停止、loaded path、cursorをクリア
- viewport duration / zoomを初期化
- InfoPanel / Waveform / Previewを初期表示へ戻す
- confirmation Noで状態不変
- Busy中はメニュー無効
- source / output / cacheファイルを削除しない
- TEXTあり / voice_onlyの次入力が再び可能

### 11.2 Targeted tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b8_workspace_reset.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b1_ui.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b2_preview.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b5_transcription_edit_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b7_voice_only_error_handling.py
```

### 11.3 Full test handling

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

B7時点では360件すべてpass表示まで完走し、既存wx終了処理由来のprocess exit code 1が記録されている。B8でも表示結果と終了コードを分けて報告する。

### 11.4 Manual smoke

- TEXTあり解析後に新規作業を実行し、空状態へ戻る。
- voice_only解析・書き起こし編集後に新規作業を実行し、編集内容が残らない。
- 確認Noで現在作業が保持される。
- 新規作業後に別のTEXT + 音声を読み込んで解析できる。
- 新規作業後にTEXTなしで別音声を読み込んで解析できる。
- recent files、テーマ、パラメータ、保存先履歴が保持される。

## 12. 受け入れ条件

- ファイルメニューから `新規作業... Ctrl+N` を実行できる。
- Busy中は新規作業を実行できない。
- 作業データがある場合は確認ダイアログが表示される。
- 作業データがない場合は確認を省略し、残存するworker失敗状態と表示を初期状態へ戻せる。
- 確認Noで現在状態が一切変わらない。
- 確認YesでTEXT・音声・書き起こし・timing plan・表示・再生状態が初期化される。
- reset後に `analysis_pending_rebuild = False`、`status_key = IDLE` となる。
- reset後は解析、VMD保存、MMD用WAV出力、再生、Zoomが不可になる。
- reset後にTEXTあり / voice_onlyのどちらの次作業も開始できる。
- recent files、last directories、theme、解析パラメータが保持される。
- resetを繰り返しても、job IDを除く可視ワークスペースが同じ未入力初期状態へ収束する。
- audio / analysis job IDはlate callback無効化のため単調に進み、`None` や0へ戻らない。
- source / output / cacheファイルが削除されないことをテストで確認できる。
- late callbackがreset後の状態へ反映されない。
- 既存TEXTあり / voice_only導線を壊していない。
- README / 配布用readme / 関連仕様docsが新規作業導線と矛盾していない。
- 新規依存、packaging、license変更がない。
- Qt / PySide6を復活させていない。

## 13. リスクと対策

### R1. `UiState` 全交換で設定・履歴を失う

対策:

- dataclassを交換せず、作業データ限定の `reset_workspace()` を使う。
- 保持対象をテストで明示する。

### R2. `invalidate_analysis()` の再解析待ちが残る

対策:

- 新規作業では専用reset契約を使い、`analysis_pending_rebuild = False` とする。

### R3. late callbackが新しい作業へ混入する

対策:

- audio / analysis job IDを無効化する。
- 両job IDを単調に進め、`None` や0へ戻さない。
- Busy中resetを禁止する。

### R4. resetがファイル削除と誤解される

対策:

- メニュー名を `新規作業` とする。
- 確認文言で元ファイルと保存済みファイルを削除しないことを明記する。
- cache cleanupをB8へ含めない。

### R5. 表示だけ古い結果が残る

対策:

- UiState resetと表示resetを別々に受け入れ条件化する。
- InfoPanel、Waveform、Preview、RightPane、Status、viewportをテストする。

### R6. Busy中resetとcancelが競合する

対策:

- Busy中はメニューを無効化する。
- cancel完了後に新規作業を実行する単純な導線を維持する。

## 14. Codex 実装時の注意

- 実装前に `git status --short --branch` とB7コミット状態を確認する。
- B8はWorkspace Reset / New Session Flowであり、MS19 CloseoutはB9で完了済みである。
- `UiState()` の差し替えで実装しない。
- `invalidate_analysis()` だけでreset完了扱いにしない。
- recent files、last directories、theme、パラメータを消さない。
- source / output / cacheファイルを削除しない。
- Busy中にworkerを黙って破棄しない。
- audio / analysis job IDを単調に進め、`None` や0へ戻さない。
- wxPython main lineのみ変更する。
- Qt / PySide6関連ファイルへ触れない。
- 新規依存を追加しない。
- shell commandを並列実行しない。
- shell pipeline / chained commandを避ける。
- 実装後レポートでは、クリア対象、保持対象、確認キャンセル、Busy制御、late callback、実行テスト、ユーザー確認項目を明示する。

## 15. 実装・検証結果

- `UiState.has_workspace_user_data` と `UiState.reset_workspace()` を追加し、作業データだけを初期化する契約を実装した。
- `AppController.request_reset_workspace()` でaudio job ID無効化、再生停止、viewport初期化、UiState reset、表示同期を順に実行するようにした。
- MainFrameのファイルメニューに `新規作業...\tCtrl+N` を追加し、Busy中無効、作業データあり時の確認、analysis job ID無効化、InfoPanel / Waveform / Preview / RightPaneの初期表示復帰を実装した。
- `tests/test_ms19_b8_workspace_reset.py` を追加し、状態reset、保持対象、確認Yes / No、Busy拒否、late callback破棄、ファイル非削除を確認した。
- B8専用テストは8件pass、exit code 0。対象・関連回帰は60件すべてpass表示、通常 `pytest tests` は368件すべてpass表示まで完走した。後者2件は既存wx終了処理由来のprocess exit code 1を記録した。
- 2026-07-11 にユーザースモークテスト通過・問題なしを確認した。
