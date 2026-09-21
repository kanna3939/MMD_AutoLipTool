# MS19-B5 Implementation Plan

## 1. 文書情報

- Milestone: MS19
- Block: B5
- Title: Review / Edit Transcription Result Flow
- Status: Completed
- 作成日: 2026-07-07
- 実装日: 2026-07-08
- ユーザーチェック: 2026-07-08 通過・問題なし
- 前提: MS19-B4 実装およびユーザースモークテスト通過後の状態を前提にする。B4実装とB5計画は `a95269f Implement MS19 B4 and plan B5` でコミット済み。
- 実装結果: B5の書き起こし編集UI、編集状態保持、保持済み `WhisperTimingResult` を使った編集済みテキスト再解析、B5用テストを実装済み。

## 2. 背景

MS19-B4 では、TEXT なし音声のみ入力で Whisper 書き起こしとタイミング解析を実行し、得られた書き起こしテキスト、ひらがな、母音列を InfoPanel に表示できるようにした。

現状の B4 実装では、音声のみ解析で得た書き起こし結果は確認表示までであり、ユーザーが誤認識を修正して以後の解析結果へ反映する導線はまだない。また、音声のみ入力では VMD 保存は引き続き無効であり、MS19-B6 で Preview / VMD 保存連携を扱う予定である。

B5 では、B4 の音声のみ解析結果をユーザーが確認・編集できる最小の wxPython UI と、編集後テキストをセッション内解析状態へ安全に反映するデータ契約を実装対象にする。

2026-07-08 に、InfoPanel上の書き起こし編集UI、`UiState` の編集済みtranscription保持、`AnalysisWorker` の編集済み再解析契約、MainFrameの適用 / 元に戻す / 未適用編集ガードを実装した。B5時点では、音声のみ入力のVMD保存は引き続き無効である。

同日に、ユーザー側のB5確認は通過・問題なしと報告された。B5内で追加のREADME / readme修正が必要な問題は報告されていない。

## 3. 目的

- 音声のみ解析で得た書き起こし結果を、ユーザーが UI 上で確認できる状態から編集可能な状態へ拡張する。
- 編集後テキストから、ひらがな / 母音列プレビューを再生成できるようにする。
- 編集後テキストと既存タイミング解析結果の不一致を明示的に扱い、古い解析結果を誤って VMD / Preview へ流さない。
- 編集後テキストを使った再解析の最小導線を整え、MS19-B6 の Preview / VMD 保存連携へ渡せる状態にする。

## 4. In Scope

- wxPython InfoPanel 上の音声のみ書き起こしテキスト表示欄を、音声のみ解析成功後に編集可能にする。
- TEXT あり入力時の既存テキストプレビューは読み取り専用のまま維持する。
- 音声のみ入力時だけ、書き起こし編集の適用 / 取り消し操作を追加する。
- 編集適用時に既存のテキスト検証・ひらがな変換・母音列変換を再利用する。
- 編集適用後、`UiState` に手動編集済み書き起こしとして保持する。
- 編集適用後、現在のタイミングプランが編集前テキスト由来であれば無効化または再生成待ちとして扱う。
- 編集済みテキストを使った再解析では、可能な限り B4 で取得済みの Whisper timing result を再利用し、Whisper を不要に再実行しない。
- 音声のみ入力の VMD 保存無効状態は維持する。
- B5 の状態遷移を unit test / GUI state test で検証する。

## 5. Out of Scope

- 音声のみ入力からの VMD 保存有効化。
- Preview操作、再生タイムライン操作、VMD保存有効化まで含む最終連携。
- 永続的な書き起こし履歴管理。
- 外部字幕形式や transcript file の出力。
- 高度なテキストエディタ機能。
- 複数候補 transcription の管理。
- Whisper model / language 設定 UI の追加。
- Qt / PySide6 GUI の復活。
- Whisper 自体の認識精度改善。

## 6. 前提条件

- MS19-B4 により、TEXT なし音声のみ入力で解析開始できる。
- MS19-B4 により、音声のみ解析成功時に transcription text / hiragana / vowel preview が InfoPanel に表示される。
- MS19-B4 により、TEXT なし音声のみ入力では VMD 保存が無効のままである。
- B5 実装時点で、B4 の user smoke test 通過報告は受領済みである。
- B5 は wxPython main line のみを対象にする。

## 7. 対象ファイル

主対象:

- `src/gui_wx/info_panel.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/analysis_worker.py`

必要に応じて確認・更新:

- `src/gui_wx/app_controller.py`
- `src/core/text_processing.py`
- `src/core/whisper_timing.py`

テスト候補:

- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_ms19_b5_transcription_edit_state.py`

関連ドキュメント:

- `docs/Implementation_Plan/MS19_Block_Breakdown.md`
- `docs/MS17_and_Beyond_Index.md`
- `docs/MS18_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

## 8. 実装方針

### 8.1 UI 方針

- 既存の InfoPanel を拡張し、別画面や大きな UI 再設計は行わない。
- 書き起こし編集欄は、音声のみ解析成功後だけ編集可能にする。
- TEXT あり入力時、未解析時、音声未選択時は読み取り専用にする。
- 編集操作は明示的な適用操作で反映し、入力中の各キー操作で解析状態を変えない。
- 取り消し操作は、直近の Whisper 書き起こし結果へ戻す最小仕様にする。

想定する最小 UI:

- 書き起こしテキスト欄: 既存 `tc_text_preview` を編集可能化する。
- 適用ボタン: 編集内容を検証し、session state と preview に反映する。
- 元に戻すボタン: B4 で得た元の Whisper 書き起こしへ戻す。

### 8.2 状態管理方針

`UiState` には、B4 で追加済みの transcription 関連 field を基礎として、必要最小限の編集状態を追加する。

候補:

- `transcription_original_text`
- `transcription_text`
- `transcription_is_edited`
- `transcription_edit_dirty`
- `transcription_timing_result`
- `analysis_text_source`

実装時には既存 field 名と重複しないように確認し、意味が重なる field は増やしすぎない。

状態の意味:

- Whisper 結果表示直後: `transcription_is_edited = False`
- ユーザーが編集欄を変更しただけ: UI dirty だが、解析状態には未適用
- 適用成功後: `transcription_is_edited = True`
- 適用失敗後: 解析状態は変更しない
- 元に戻す後: Whisper 結果へ戻し、`transcription_is_edited = False`

### 8.3 解析方針

- 初回の音声のみ解析は、B4 と同じく Whisper を実行する。
- B5 では、初回解析で得た Whisper timing result をセッション内に保持できる形にする。
- 編集済みテキストを使った再解析では、保持済み Whisper timing result が利用可能な場合、それを使って `build_vowel_timing_plan()` を再実行する。
- 保持済み timing result が存在しない場合は、明示的に再解析不能として扱う。黙って Whisper を再実行して編集内容を上書きしない。
- 編集済みテキスト適用直後に古い timing plan を current として扱わない。
- 編集済みテキスト再解析に成功した場合は、`current_timing_plan` を編集済みテキスト由来へ更新してよい。この更新により既存の Preview 表示が再描画される場合は、B5の許容範囲とする。
- ただし、B5では Preview の新規操作導線、再生タイムライン操作、VMD保存有効化、VMD writer接続は行わない。これらの最終連携はMS19-B6で扱う。

### 8.4 Worker 起動契約

B5では、`AnalysisWorker` に編集済みテキスト再解析用の明示的な入力契約を追加する。

候補:

- `transcription_text_override: str | None`
- `retained_whisper_timing_result: WhisperTimingResult | None`
- `reuse_retained_timing: bool`

契約:

- 初回 voice-only 解析では、B4と同じく `recognize_audio_timing()` を実行する。
- 初回 voice-only 解析成功時、`AnalysisWorkerResult` は `whisper_timing_result` を返す。
- 編集済みテキスト再解析では、`transcription_text_override` と `retained_whisper_timing_result` を渡す。
- 編集済みテキスト再解析では `recognize_audio_timing()` を呼ばず、`build_vowel_timing_plan(..., whisper_timing_result=retained_whisper_timing_result)` を呼ぶ。
- `reuse_retained_timing=True` なのに `retained_whisper_timing_result` がない場合は明示的に失敗させる。
- `transcription_text_override` が空、または検証不能な場合は明示的に失敗させる。
- 通常のTEXTあり解析はこの追加契約を使わない。

### 8.5 エラー表示方針

- 空文字、空白のみ、変換不能な編集テキストは適用しない。
- 適用失敗時は既存のエラー表示方針に合わせてユーザーへ通知する。
- 編集済みテキストで再解析できない場合は、原因が「保持済み timing result 不在」なのか「テキスト検証失敗」なのかを区別する。

## 9. 詳細ステップ

1. 現在の B4 実装状態を再確認する。
   - `UiState` の voice-only state
   - `AnalysisWorkerResult`
   - `MainFrame._on_analysis_success()`
   - `InfoPanel` の preview 更新 API

2. `InfoPanel` に最小 API を追加する。
   - text preview editable 切り替え
   - text preview 現在値取得
   - transcription edit controls の enabled / visible 切り替え
   - apply / revert callback を MainFrame から接続できる形にする

3. `UiState` に編集状態を追加する。
   - original transcription と current transcription を区別する
   - 編集済み / dirty / source を区別する
   - 音声や TEXT 入力変更時に transcription edit state を clear する

4. `AnalysisWorkerResult` または `UiState` に timing result 保持を追加する。
   - 初回 voice-only 解析成功時に Whisper timing result をセッション内保持する
   - 保存・永続化はしない
   - `AnalysisWorkerResult` に `whisper_timing_result` を追加するか、同等の受け渡し口を設ける

5. MainFrame の voice-only 成功処理を拡張する。
   - InfoPanel の編集 UI を有効化する
   - original transcription を保持する
   - 初回解析で得た `WhisperTimingResult` を `UiState` へ保持する
   - 適用 / 元に戻す handler を追加する

6. 編集適用処理を実装する。
   - UI から編集テキストを取得する
   - 既存の text validation を通す
   - ひらがな / 母音列を再生成する
   - `UiState` を編集済み状態へ更新する
   - 現在の timing plan を編集前由来のまま使わない状態へ遷移させる

7. 編集済みテキスト再解析の最小導線を実装する。
   - `AnalysisWorker` に `transcription_text_override` と `retained_whisper_timing_result` を渡せるようにする
   - 保持済み timing result がある場合、Whisper を再実行せず `build_vowel_timing_plan()` を再実行する
   - 成功時は current timing plan を編集済みテキスト由来に更新する
   - 既存 Preview が `current_timing_plan` から自動再描画されることは許容する
   - 失敗時は編集済みテキストと旧 timing plan を混同しない

8. TEXT あり入力経路の回帰を確認する。
   - TEXT ありでは編集 UI が有効にならない
   - 既存の VMD 保存可否判定が変わらない

9. テストを追加・更新する。
   - B5 state test
   - voice-only GUI state test
   - analysis worker test
   - 既存 B4 / MS14 系テストの回帰確認

10. 関連ドキュメントを B5 実装結果に合わせて更新する。

## 10. 状態遷移 / データ契約

### 10.1 初回音声のみ解析成功

入力:

- audio path
- no text path
- `input_mode = voice_only`

結果:

- `transcription_original_text = Whisper result text`
- `transcription_text = Whisper result text`
- `transcription_is_edited = False`
- `analysis_text_content = Whisper result text`
- `analysis_text_source = whisper`
- `transcription_timing_result = WhisperTimingResult`
- InfoPanel text / hiragana / vowel preview 更新
- VMD 保存は無効のまま

### 10.2 編集中

入力:

- InfoPanel 上の text preview 内容変更

結果:

- UI 上は dirty として扱う
- `UiState` の解析済みデータは適用操作まで変更しない
- 自動解析は行わない

### 10.3 編集適用成功

入力:

- edited transcription text

結果:

- `transcription_text = edited text`
- `transcription_is_edited = True`
- `analysis_text_content = edited text`
- `analysis_text_source = user_edited_transcription`
- hiragana / vowel preview 再生成
- 旧 timing plan は編集前テキスト由来として current 扱いから外す
- 編集済みテキスト再解析が必要な状態になる
- この時点では `current_timing_plan` を編集済みテキスト由来として扱わない

### 10.4 編集済みテキスト再解析成功

入力:

- edited transcription text
- retained `WhisperTimingResult`

結果:

- `current_timing_plan` が edited transcription 由来へ更新される
- `analysis_text_source = user_edited_transcription`
- 既存 Preview は `current_timing_plan` 更新に追従して再描画されてもよい
- Preview の新規操作導線、再生タイムライン操作、VMD 保存有効化は B6 まで行わない

### 10.5 Worker 入力契約

初回 voice-only 解析:

- `input_mode = voice_only`
- `text_content = ""`
- `transcription_text_override = None`
- `retained_whisper_timing_result = None`
- `reuse_retained_timing = False`

結果:

- Whisper を実行する
- transcription text を抽出する
- `AnalysisWorkerResult.whisper_timing_result` に初回 timing result を含める

編集済みテキスト再解析:

- `input_mode = voice_only`
- `transcription_text_override = edited transcription text`
- `retained_whisper_timing_result = UiState.transcription_timing_result`
- `reuse_retained_timing = True`

結果:

- Whisper を実行しない
- `transcription_text_override` を解析用テキストとして使う
- `retained_whisper_timing_result` を `build_vowel_timing_plan()` へ渡す
- timing result がない場合は失敗する

### 10.6 元に戻す

入力:

- revert action

結果:

- `transcription_text = transcription_original_text`
- `transcription_is_edited = False`
- `analysis_text_content = transcription_original_text`
- InfoPanel text / hiragana / vowel preview を Whisper 結果へ戻す
- 必要なら edited timing plan を current 扱いから外す

## 11. テスト方針

### 11.1 Unit / state tests

- 音声のみ解析成功後、transcription edit state が初期化されること。
- 編集適用で `transcription_is_edited` と `analysis_text_source` が更新されること。
- 空文字編集は拒否され、state が変わらないこと。
- 元に戻す操作で original transcription に戻ること。
- TEXT あり入力では edit state が有効にならないこと。

### 11.2 Worker tests

- 初回 voice-only 解析では Whisper timing result が結果として保持されること。
- 編集済みテキスト再解析では、保持済み timing result を使って timing plan を再生成できること。
- 保持済み timing result がない場合、編集済みテキスト再解析が明示的に失敗すること。
- 編集済みテキスト再解析で Whisper を黙って再実行しないこと。
- 編集済みテキスト再解析時に `transcription_text_override` が `build_vowel_timing_plan()` へ渡されること。

### 11.3 GUI state tests

- 音声のみ解析成功後、InfoPanel text preview が編集可能になること。
- TEXT あり解析成功後、InfoPanel text preview は読み取り専用のままであること。
- 編集適用後、InfoPanel の hiragana / vowel preview が更新されること。
- 編集済みテキスト再解析成功後、既存 Preview が `current_timing_plan` に追従して再描画されても、B5の範囲逸脱として扱わないこと。
- VMD 保存ボタンは B5 後も voice-only では無効のままであること。

### 11.4 実行候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms19_b4_voice_only_gui_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms19_b4_analysis_worker_voice_only.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms19_b5_transcription_edit_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b4_analysis.py
```

実装後に必要であれば、範囲を広げて `.\.venv\Scripts\python.exe -m pytest tests` を実行する。

## 12. 受け入れ条件

- 音声のみ解析成功後、書き起こし結果を UI 上で編集できる。
- 編集適用後、ひらがな / 母音列プレビューが編集後テキストに基づいて更新される。
- 編集適用前のタイミングプランを、編集後テキストの結果として扱わない。
- 編集済みテキスト再解析で、保持済み Whisper timing result を利用できる。
- 編集済みテキスト再解析で、`AnalysisWorker` が Whisper を再実行せず、override text と保持済み timing result を使う。
- 保持済み timing result がない場合、編集済みテキスト再解析は明示的に失敗し、黙って編集内容を破棄しない。
- TEXT あり入力の既存解析・保存導線に回帰がない。
- 音声のみ入力の VMD 保存は B5 時点では引き続き無効である。
- B5で `current_timing_plan` 更新に伴う既存 Preview 再描画は許容するが、Preview操作導線、再生タイムライン操作、VMD保存有効化は行わない。
- Qt / PySide6 依存を追加しない。
- 新規依存を追加しない。
- ユーザー側のB5確認が通過している。

## 13. リスクと対策

### R1. 編集済みテキストとタイミングの不一致

リスク:

- 編集前テキスト由来の timing plan を編集後テキストの結果として使うと、Preview / VMD の内容が不正確になる。

対策:

- 編集適用時に current timing plan を無効化または再生成待ちにする。
- 再解析成功後だけ edited transcription 由来の timing plan として扱う。
- `current_timing_plan` 更新に伴う既存 Preview 再描画は許容し、VMD保存有効化とは別に扱う。

### R2. 編集適用後に Whisper が再実行され、編集内容が上書きされる

リスク:

- ユーザーが修正したテキストが、再解析時に再度 Whisper 結果へ戻る。

対策:

- 編集済みテキスト再解析では保持済み timing result を使う。
- 保持済み timing result がない場合は明示的に失敗させる。

### R3. TEXT あり入力経路への回帰

リスク:

- InfoPanel の text preview editable 化が TEXT あり入力にも影響する。

対策:

- edit controls は `input_mode = voice_only` かつ transcription result ありの場合だけ有効化する。
- TEXT あり入力の read-only 回帰テストを追加する。

### R4. UI の責務拡大

リスク:

- InfoPanel が編集・解析制御を持ちすぎる。

対策:

- InfoPanel は UI 値取得と control enable のみを持つ。
- 状態更新と解析判断は MainFrame / UiState / AnalysisWorker に置く。

## 14. Codex 実装時の注意

- 実装前に `git status --short --branch` と B4 の未コミット差分を確認する。
- B5 実装は B4 の作業ツリー差分を前提にするが、不要な巻き戻しや整形差分を混ぜない。
- wxPython main line のみ変更する。
- Qt / PySide6 関連ファイルには触れない。
- shell command は並列実行しない。
- shell pipeline / chained command は避ける。
- `docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけ読む。
- 実装後レポートでは、音声のみ VMD 保存が B5 で未対応のままかどうかを明示する。
