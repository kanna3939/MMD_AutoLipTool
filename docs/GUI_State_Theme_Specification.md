# MMD_AutoLipTool GUI状態・テーマ仕様書

## 1. 文書情報

- 文書名: `docs/GUI_State_Theme_Specification.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象バージョン系: Ver0.4.x 以降
- 現行基準: MS15 closeout 後 / MS16 以降の拡張準備
- 主対象GUI: wxPython
- 主実装領域: `src/gui_wx/`
- 主開発環境: Codex
- Coding AI 前提: Codex
- 関連文書:
  - `docs/Specification_Prompt_v4.md`
  - `docs/Security_Safety_Specification.md`
  - `docs/MMD_Audio_WAV_Compatibility_Specification.md`
  - `docs/VMD_Output_Specification.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` の wxPython GUI における、状態管理・表示更新・再描画・テーマ追従・ダイアログ運用の仕様を定義する。

本書は、GUIの見た目デザイン全体を細かく規定する文書ではない。

本書の主目的は、GUI実装時に起きやすい以下の抜け漏れを防ぐことである。

- GUI部品を追加したが `Layout()` が呼ばれず表示が崩れる
- 状態変更後に `Refresh()` が呼ばれず古い表示が残る
- テーマ切替後に新規部品だけ旧色・既定色のまま残る
- 新規ダイアログが Light / Dark / System テーマに追従しない
- 処理失敗後に Busy 状態が解除されない
- ボタンやメニューの有効/無効が状態と矛盾する
- Preview / Waveform / Status に古い結果が残る
- worker / callback の結果が UI 状態とずれて反映される

特に、Codex に GUI 実装を依頼する場合、本書を GUI 実装時のチェック基準として扱う。

---

## 3. 適用範囲

本書は、以下に適用する。

- wxPython GUI 全体
- MainFrame
- UiState
- AppController
- WaveformPanel
- PreviewPanel
- ViewportController
- ThemeManager
- InfoPanel
- ParameterPanel
- Status表示
- メニュー
- ツールボタン
- 処理中表示
- エラー / 警告 / 確認ダイアログ
- 将来追加される mp3変換関連ダイアログ
- 将来追加される MMD用WAV出力関連ダイアログ
- GUI変更時の受け入れ条件
- GUI変更時の実装報告

---

## 4. 非対象

本書では、以下を主対象としない。

- VMD writer の詳細仕様
- 音声解析アルゴリズム
- FFmpeg / ffprobe の詳細仕様
- MMD用WAVの詳細互換仕様
- TEXT / WAV / mp3 / m4a 入力仕様の詳細
- PyInstaller 配布仕様
- ライセンス文書
- Qt / PySide6 版 GUI の復元
- 旧 `src/gui/` の詳細設計
- MMD本体のGUI仕様
- OS標準ダイアログの完全な外観制御

ただし、上記が wxPython GUI の状態管理・表示更新・テーマ追従に影響する場合は、本書の規則を参照する。

---

## 5. GUI基本方針

### 5.1 wxPython 主系

現行GUI主系は wxPython とする。

旧 Qt / PySide6 系は現行主系ではない。

新規GUI実装は `src/gui_wx/` を対象とし、旧 `src/gui/` を主系として拡張しない。

### 5.2 GUI実装の完了条件

GUI実装では、単に部品を追加して動作するだけでは完了としない。

GUI部品・ダイアログ・表示更新を追加または変更した場合、以下を確認する。

- 必要な `Layout()` が行われている
- 必要な `Refresh()` が行われている
- 必要な `Update()` の要否を確認している
- Light / Dark / System テーマに追従する
- 状態変更後に古い表示が残らない
- 既存 action state と矛盾しない
- disabled 状態でも視認性が保たれる
- エラー時・キャンセル時にも UI が復帰する
- 実装報告に確認内容を記載する

### 5.3 GUI変更時の基本フロー

GUI状態を変更する場合、原則として以下の流れを意識する。

```text
状態変更
↓
action state 更新
↓
status 表示更新
↓
対象 panel / dialog への状態反映
↓
Layout / Refresh / Update の要否確認
↓
テーマ追従確認
```

実装上の関数名は現行コードに従う。

---

## 6. UiState / Action State / 表示状態の分離

### 6.1 UiState

`UiState` は、GUI全体の状態を保持する。

対象例:

- TEXT入力状態
- WAV入力状態
- 解析結果状態
- Busy状態
- 再生可能状態
- 再生中状態
- テーマ設定
- 保存可能状態
- 最近使ったファイル
- current timing plan
- waveform / preview に渡す正本データ

### 6.2 Action State

Action State は、現在どの操作を有効にするかを決める状態である。

対象例:

- TEXT読み込みボタン
- WAV読み込みボタン
- 処理実行ボタン
- VMD保存ボタン
- Playボタン
- Stopボタン
- Zoom In
- Zoom Out
- Reset Zoom
- メニュー項目
- テーマ切替項目

Action State は、UiState から導出される。

### 6.3 表示状態

表示状態は、各GUI部品に何を表示するかを表す。

対象例:

- Status表示文言
- InfoPanel のテキスト情報
- WaveformPanel の波形データ
- PreviewPanel のPreviewデータ
- 再生位置カーソル
- Viewport範囲
- エラー表示
- 処理中表示

### 6.4 分離方針

以下を混同しない。

| 種別 | 役割 |
| --- | --- |
| UiState | 内部状態の正本 |
| Action State | 操作可否 |
| 表示状態 | ユーザーに見える情報 |
| Theme State | 表示色・見た目 |
| Worker State | 処理中・完了・失敗 |

状態を変更した場合、Action State と表示状態の両方を更新する必要がある。

---

## 7. 主要状態の定義

### 7.1 入力状態

入力状態は、TEXT / 音声の読込状態と入力モードを表す。

代表状態:

- TEXT未読込
- TEXT読込済み
- TEXT読込失敗
- WAV未読込
- WAV読込済み
- WAV読込失敗
- 将来の mp3 / m4a 入力読込済み
- 将来の音声変換失敗
- TEXTあり入力 (`text_audio`)
- TEXTなしの音声のみ入力 (`voice_only`)
- 音声のみ書き起こし編集適用後の再解析待ち

### 7.2 解析状態

解析状態は、timing plan の有効性を表す。

代表状態:

- 解析未実行
- 解析可能
- 解析中
- 解析成功
- 解析失敗
- 解析失敗・旧結果表示中（保存不可）
- 解析キャンセル
- 再解析待ち
- 古い解析結果破棄済み

### 7.3 再生状態

再生状態は、音声再生の可否と実行状態を表す。

代表状態:

- 再生不可
- 再生可能
- 再生中
- 停止中
- 再生終了
- 再生エラー

### 7.4 保存状態

保存状態は、VMD保存、個別MMD用WAV保存、MMD一括出力の可否を表す。

代表状態:

- 保存不可
- VMD保存可能
- VMD保存中
- VMD保存成功
- VMD保存失敗
- MMD用WAV保存可能
- MMD用WAV保存失敗
- MMD一括出力可能 / 実行中 / 成功 / 失敗 / キャンセル

### 7.5 Busy状態

Busy状態は、ユーザー操作を一部制限すべき処理中状態を表す。

Busy対象例:

- Whisper解析中
- timing plan 生成中
- VMD出力中
- ffprobe 実行中
- FFmpeg 変換中
- MMD用WAV出力中
- MMD一括出力中

---

## 8. 操作有効・無効制御

### 8.1 基本方針

ボタンとメニューの有効/無効は、同一の状態判断に基づいて更新する。

ボタンだけ有効、メニューだけ無効のような不整合を避ける。

### 8.2 基本操作条件

| 操作 | 有効条件 |
| --- | --- |
| 新規作業 | Busyでない |
| TEXT読み込み | Busyでない |
| WAV読み込み | Busyでない |
| 処理実行 | Busyでなく、TEXT + 音声、またはTEXTなしの音声のみ入力が成立している |
| VMD保存 | Busyでなく、有効かつ空でないtiming planがあり、再解析待ちでなく、diagnostics ERRORがない |
| MMD用WAV出力 | Busyでなく、MMD用WAVを生成できる入力音声がある |
| MMD一括出力 | Busyでなく、一括出力に必要な現在状態、入力音声、FFmpegが有効である |
| Play | Busyでなく、再生可能な音声がある |
| Stop | 再生中である |
| Zoom In | 表示対象データがある |
| Zoom Out | 表示対象データがある |
| Reset Zoom | 表示対象データがある |
| テーマ切替 | 原則として常時可能 |
| アプリ終了 | Busy中は確認を挟む |

音声のみ解析の失敗時は、入力音声と適用済み書き起こしを保持する。同一base /
parameterで旧結果を再利用できる場合はPreview、個別補正、履歴を確認用に復元するが、
diagnostics ERRORによりVMD保存は禁止する。再利用不能なら解析結果を無効化する。
VMD保存だけが失敗した場合は解析結果を保持し、保存先を変更して再試行できる状態を維持する。

### 8.3 Busy中の制限

Busy中は、状態破壊につながる操作を無効化する。

対象例:

- TEXT再読込
- WAV再読込
- 処理再実行
- VMD保存
- 新規作業
- パラメータ変更
- Recent Files 読込
- 将来の mp3 / m4a 再変換
- MMD用WAV出力
- MMD一括出力

ただし、以下は許可してよい。

- キャンセル
- 中止
- エラー詳細表示
- アプリ終了確認
- テーマ切替

テーマ切替をBusy中に許可する場合、処理中ダイアログもテーマ追従する必要がある。

### 8.4 新規作業の状態遷移

`ファイル > 新規作業...` は、現在の入力・書き起こし・解析結果・再生・表示を未入力状態へ戻す導線である。ユーザー作業データがある場合は確認を表示し、Noまたはダイアログクローズ時はUiState、表示、playback、job IDを変更しない。

確認Yes、またはユーザー作業データがない場合は、audio / analysis job IDを無効化してlate callbackを破棄し、`analysis_pending_rebuild = False`、`status_key = IDLE`、`input_mode = text_audio` とする。InfoPanel、Waveform、Preview、RightPane、playback cursor、viewportを初期表示へ戻す。Busy中はメニューを無効化し、resetとworker cancellationを同一操作に混在させない。

### 8.5 状態更新時の必須処理

入力、解析、再生、保存、テーマの状態が変わった場合、以下を確認する。

- action state が更新されたか
- status が更新されたか
- Preview / Waveform の表示が正しいか
- 古い結果が残っていないか
- 必要な再描画が行われたか

---

### 8.6 MS25 MMD一括出力

- 起動導線は`ファイル > MMD一括出力...`とする。
- parent directoryとeditable folder名を同じdialogで指定し、既定folder名は`<audio_stem>_MMD`とする。
- WARNING / ERROR、invalid current state、FFmpeg不足、invalid path、collisionではworkerとfilesystem処理を開始しない。
- 実行中はBusyを維持し、cancel / closeではworker terminalとstaging cleanupの完了を待つ。
- close判定はdelivery worker参照、active binding、UiStateのdelivery state、close pendingのいずれかが残る場合もdelivery中の可能性として扱い、generic closeへ流さない。不整合時はdelivery専用のfailed reconciliationまたはterminal受理後だけ終了を許可する。
- success、failure、cancelのterminal結果は、一括出力のworker bindingと`DeliveryTerminalResult`に基づいて投影する。late / duplicate resultは現在stateへ反映しない。
- cleanup failureはprimary resultを置き換えず、safe warningとして投影する。raw exceptionや絶対staging pathは通常表示しない。
- 一括出力は個別保存の履歴やINIへbatch parent / folderを保存しない。

---

## 9. Busy状態と長時間処理

### 9.1 Busy状態の目的

Busy状態は、長時間処理中の多重実行や状態破壊を防ぐために使う。

### 9.2 Busy開始時

Busy開始時は以下を行う。

- `is_busy` 相当の状態を true にする
- 関連操作を無効化する
- 処理中表示を出す
- 必要に応じて進捗またはフェーズ表示を出す
- キャンセル可能な処理では中止導線を用意する
- Status に処理中であることを表示する

### 9.3 Busy終了時

Busy終了時は、成功・失敗・キャンセルのいずれでも以下を行う。

- Busy状態を解除する
- 関連操作の有効/無効を再計算する
- 処理中表示を閉じる
- Status を更新する
- Preview / Waveform の更新またはクリアを行う
- 必要な再描画を行う

### 9.4 Busy解除漏れ禁止

以下は禁止する。

- worker失敗後にBusy状態が残る
- キャンセル後にBusy状態が残る
- 例外発生後にボタンが無効のまま残る
- 処理中ダイアログが閉じない
- 古いworker結果が後から反映される

### 9.5 job id / late callback

長時間処理では、job id または同等の仕組みにより、古い結果を破棄できるようにする。

方針:

- 新しい処理開始時に job id を発行する
- worker結果に job id を含める
- 現在の job id と一致しない結果は破棄する
- 破棄した結果をUIへ反映しない
- 破棄処理を成功扱いにしない

---

## 10. 表示更新・再描画の基本契約

### 10.1 基本方針

GUI部品の表示内容を変更した場合、必要に応じてレイアウト更新と再描画を行う。

wxPython実装では、以下の要否を確認する。

- `Layout()`
- `Refresh()`
- `Update()`
- `Fit()`
- `SetMinSize()`
- `SendSizeEvent()`

### 10.2 Layout

`Layout()` は、Sizer配下の部品配置を再計算するために使う。

必要になる例:

- 新規部品を追加した
- 部品を表示 / 非表示にした
- ラベル文字列が大きく変わった
- ダイアログ内の説明文が変わった
- パネルの最小サイズが変わった
- 表示内容により高さ・幅が変わる

### 10.3 Refresh

`Refresh()` は、再描画要求を出すために使う。

必要になる例:

- カスタム描画部品の内部データを変更した
- 波形データを更新した
- Previewデータを更新した
- 再生位置カーソルを変更した
- Viewportを変更した
- テーマ色を変更した
- 表示をクリアした

### 10.4 Update

`Update()` は、即時反映が必要な場合に検討する。

必要になる例:

- 処理中ダイアログを即時表示したい
- 長時間処理前にUI更新を確実に反映したい
- Statusの即時反映が必要
- Progress / Gauge の更新を目に見える形で反映したい

ただし、乱用しない。

### 10.5 Fit / SetMinSize / SendSizeEvent

サイズに関係する変更では以下を確認する。

- ダイアログの内容が増えた場合、`Fit()` が必要か
- 最小サイズを更新する必要があるか
- 親Windowへサイズ変更イベントを送る必要があるか
- リサイズ後に表示が破綻しないか

### 10.6 カスタム描画部品

カスタム描画部品では、内部状態を変更しただけでは画面が変わらない場合がある。

以下を守る。

- setter で内部状態を更新したら `Refresh()` を呼ぶ
- clear処理でも `Refresh()` を呼ぶ
- テーマ変更後にも `Refresh()` を呼ぶ
- 可能なら描画処理は現在状態から再構築できるようにする
- 古い描画キャッシュが残らないようにする

---

## 11. Waveform再描画条件

### 11.1 基本方針

WaveformPanel は、解析用音声またはWAV表示データを視覚化する。

波形表示は、リップ解析に使用する音声データと対応している必要がある。

MS16以降で stereo / 3ch以上 / mp3 / m4a 入力を扱う場合でも、波形表示は解析用mono音声を正本とする。

### 11.2 再描画条件

以下の場合、WaveformPanel は再描画する。

- WAV読込成功
- WAV読込失敗
- mp3 / m4a 変換成功
- mp3 / m4a 変換失敗
- 解析用WAVが更新された
- 波形データが更新された
- 波形データがクリアされた
- Viewportが変更された
- Zoom倍率が変更された
- Reset Zoomされた
- 再生位置が変更された
- 再生停止した
- テーマが変更された
- パネルサイズが変わった
- 入力再読込により既存波形を無効化した

### 11.3 クリア条件

以下の場合、WaveformPanel はクリアまたは無効表示へ戻す。

- WAV読込失敗
- 音声変換失敗
- 音声入力が無効になった
- 解析用WAV生成に失敗した
- 現在の波形が現在入力と対応しなくなった

### 11.4 テーマ追従

WaveformPanel の以下はテーマに追従する。

- 背景
- 波形色
- グリッド色
- ラベル色
- カーソル色
- 無効表示色
- 境界線色

テーマ変更時は、ThemeManager または同等の機構から色を取得し、再描画する。

### 11.5 禁止事項

以下は禁止する。

- WAV読込失敗後に古い波形を残す
- テーマ変更後に波形だけ旧色のまま残す
- Viewport変更後に古い表示範囲が残る
- 再生位置更新後にカーソルが動かない
- 解析用音声と対応しない波形を正本として表示する

---

## 12. Preview再描画条件

### 12.1 基本方針

PreviewPanel は、解析結果から生成されるリップモーションの概略を表示する。

Previewは、VMD出力と意味的に整合している必要がある。

### 12.2 再描画条件

以下の場合、PreviewPanel は再描画する。

- 解析成功
- 解析失敗で旧結果を安全にrollbackできない
- 解析キャンセルで旧結果を安全にrollbackできない
- timing plan 更新
- timing plan クリア
- Previewデータ更新
- Previewデータクリア
- TEXT再読込
- WAV再読込
- mp3 / m4a 変換元変更
- パラメータ変更
- morph upper limit 変更
- closing hold 変更
- closing softness 変更
- Viewport変更
- Zoom変更
- 再生位置変更
- Stop
- Reset Zoom
- テーマ変更
- パネルサイズ変更

### 12.3 クリア条件

以下の場合、Previewはクリアまたは無効表示へ戻す。

- TEXT再読込
- WAV再読込
- 音声変換元変更
- 解析失敗
- 解析キャンセル
- パラメータ変更による再解析待ち
- current timing plan が無効化された
- 古いworker結果が破棄された
- timing plan自体が無効でVMD保存可能状態でなくなった

### 12.4 テーマ追従

PreviewPanel の以下はテーマに追従する。

- 背景
- レーン背景
- レーン境界線
- 母音ラベル
- shape描画色
- カーソル色
- 無効表示色
- グリッド色

テーマ変更時は、再描画を行う。

### 12.5 PreviewとVMDの整合

Previewは確認用表示であり、VMD出力の完全なピクセル再現ではない。

ただし、以下の意味的整合は守る。

- VMDに出る発声区間がPreviewに表示される
- closing hold / closing softness がPreviewにも反映される
- bridge / smoothing がPreviewにも反映される
- Previewだけ古いshape仕様のまま残らない
- VMDだけ新仕様でPreviewが旧仕様にならない

### 12.6 禁止事項

以下は禁止する。

- 解析失敗後に旧Previewをcurrent成功結果または保存可能結果として見せる
- パラメータ変更後に古いPreviewを保存可能結果として見せる
- テーマ変更後にPreviewだけ旧色のまま残す
- VMD writer変更時にPreview更新を忘れる
- Viewport変更後にPreviewとWaveformの表示範囲がずれる

---

## 13. Status / InfoPanel 更新条件

### 13.1 Status の役割

Status表示は、現在の操作状態や短期通知を表示する。

表示対象例:

- 未読込
- TEXT読込済み
- WAV読込済み
- 解析可能
- 解析中
- 解析成功
- 解析失敗
- 保存成功
- 保存失敗
- 再生中
- 停止中
- mp3 / m4a 変換中
- MMD用WAV出力中
- MMD一括出力中

### 13.2 Status更新条件

以下の場合、Statusを更新する。

- 入力読込成功
- 入力読込失敗
- 解析開始
- 解析進行中
- 解析成功
- 解析失敗
- 解析キャンセル
- VMD保存成功
- VMD保存失敗
- 再生開始
- 再生停止
- テーマ変更
- パラメータ変更
- Recent Files読込
- 将来の音声変換開始
- 将来の音声変換失敗
- MMD用WAV出力成功 / 失敗
- MMD一括出力成功 / 失敗 / キャンセル

### 13.3 Status優先順位

Statusには優先順位を設ける。

例:

1. エラー
2. Busy中
3. キャンセル
4. 保存結果
5. 解析結果
6. 入力状態
7. 通常待機

短期通知がある場合でも、重大なエラーやBusy状態を隠さない。

### 13.4 InfoPanel更新条件

InfoPanel は入力ファイルや変換結果の情報を表示する。

更新条件:

- TEXT読込成功
- TEXT読込失敗
- WAV読込成功
- WAV読込失敗
- counterpart auto-load 成功
- counterpart auto-load 失敗
- Recent Files読込
- 解析用WAV生成成功
- 解析用WAV生成失敗
- MMD用WAV出力成功
- 入力再読込
- 入力クリア

### 13.5 禁止事項

以下は禁止する。

- エラー後に成功ステータスを残す
- Busy終了後も「処理中」のまま残す
- 入力再読込後に古いファイル情報を残す
- 保存失敗後に保存成功と表示する
- 詳細エラーが必要な場面で何も表示しない

### 13.6 MS20 diagnostics / cancel表示

- `Info` は入力・解析・生成・保存可否を、`Warning` は `INFO / WARNING / ERROR` の診断項目を、同一 `OutputDiagnosticsSnapshot` から表示する。
- input、parameter、解析成功、workspace resetでは旧failure、snapshot、WARNING確認済みfingerprint、cancel表示状態をclearする。解析開始時は表示snapshotと確認済みfingerprintをclearし、prior failureだけをjob-local rollback payloadへ保持してよい。
- 解析中止button押下直後はBusyと `StatusKey.BUSY` を維持する。
- current analysis jobのterminal callback後にBusyを解除する。prior failureなしで旧planを復元したcancelは`analysis_cancelled=True`、`StatusKey.ANALYSIS_CANCELLED`とする。
- prior failureありで旧planを復元したcancelは既存ERRORを復元し、cancel INFOを抑制して`StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK`とVMD保存禁止を維持する。
- current failureで旧planを復元した場合は旧Preview、個別補正、履歴を表示するが、新しいERRORと`StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK`によりVMD保存を禁止する。
- selected event editorに未確定入力がある場合は、job ID、diagnostics、Busyを変更する前に解析開始を拒否し、入力を上書きしない。
- 解析開始時parameter snapshotとterminal時parameterが不一致ならresultをcommit / rollbackせず、再解析待ちへ移行する。
- parameter変更後に解析結果が既に無効でも、旧diagnostics stateをclearする。cancelled Statusからは入力準備状態へ復帰する。
- analysisはcurrent job IDとactive状態、audio workerはcurrent job ID・kind・`RUNNING`状態でterminal受理をguardする。late / duplicate callbackはRightPane、Preview、action、Statusを変更しない。

### 13.7 MS21 adjustment-only同期

- 1回のUI同期でeffective resolverを最大1回だけ実行し、diagnostics、Preview、
  selected editor、action stateへ同じcontextを渡す。
- edit / reset selectedの検証済みeffective planはcurrent identity / snapshot一致時だけ再利用する。
- Undo / Redo、edit、resetのadjustment-only同期ではplayback contextを再構築せず、
  ParameterPanelとPlaceholderContainer全体の`Refresh()`を呼ばない。
- RightPane Infoの内容が同一ならwrap / layoutを繰り返さない。

### 13.8 MS21 Preview event選択時のRightPane tab

- Previewタイムラインのuser clickがcurrent base identity、render revision、Busy状態、
  valid base event indexの検証を通過し、canonical selectionとしてcommitされた場合だけ、
  RightPaneの「選択イベント」tabへ自動切替する。
- 同じeventを再clickした場合も、current canonical requestであれば
  「選択イベント」tabへ切り替える。
- pageは固定indexで指定せず、RightPaneが所有するselected event panelから解決する。
- tab切替はNotebook page-change eventを発火させず、editor controlへfocusを強制移動しない。
- stale / Busy / invalid request、empty click、drag panではcurrent tabを維持する。
- Undo / Redo、event edit / reset、analysis failure / cancel rollback、full sync、
  adjustment-only sync、selection clearではcurrent tabを維持する。
- current tabはview-only stateであり、UiState、adjustment history、rollback snapshot、
  settings、diagnostics、fingerprintへ保存しない。

### 13.9 MS22 generation / preset lifecycle

- RightPaneの「プリセット」はSelectとApplyを分離する。Selectは候補表示だけを変更し、Applyだけが
  `GenerationState`、active preset ID、output history、effective outputを一つのtransactionとして更新する。
- built-in presetは常に利用できる。`presets.json`のinvalid / unsupported / read failure後はbuilt-inと現在の
  in-memory generation stateを保持し、user presetのcreate / update / deleteを停止する。
- active presetがmissingまたは削除された場合は、現在の3設定値を保持したCustomへ正規化する。表示名だけの
  renameはmorph output、fingerprint、WARNING確認済み状態を変更しない。
- 長音modeの優先順位は、terminal eventの明示override > active generation settings > application default `hold`。
  `decay`ではterminal frameが0となり、非terminal eventやstale requestはgeneration stateを変更しない。
- generation settingsの変更はbase再解析を要求しないoutput-only更新であり、Preview、Info / Warning、VMD保存可否を
  同じeffective output contextから再同期する。morph upper limitだけはanalysis parameter guardの対象である。
- workspace resetはinput、base、output history、selection、diagnostics failureをclearするが、generation settings、
  active preset、theme、recent files、保存先履歴を保持する。app close時はcoalesced save timerを停止し、late callbackを破棄する。

### 13.10 MS23 model profile lifecycle

- RightPaneの「モデルプロファイル」は、候補選択と「選択したモデルプロファイルを適用」を分離する。
  未選択時は日本語5母音を使用し、組み込みLatin profileでは `A / I / U / E / O` を使用する。
- 作成・更新・名前変更・削除は `profiles.json`（INIと同じ保存場所、version 1、初期上限100件）へ保存する。
  active profileの値・モーフ名セット・default preset変更と削除はロックし、名前変更だけを許可する。
  active profileのbaseline presetは値更新・削除を禁止し、profileが参照するpresetの削除も禁止する。
- profile Applyだけがprofile state、baseline preset、generation state、output history、effective outputを一つの
  transactionとして更新する。Preview、VMD writer、diagnostics、reportは同じresolved morph-name tupleへ同期する。
- profile fileのinvalid / unsupported / read failure、missing profile、missing baselineはpartial importせず、
  no-profileまたは解決可能なfallbackへfail closedする。Busy、cancel、rollback、stale result discardの既存契約を変えない。
- workspace resetはprofile projection、generation、active presetを保持し、input、base、history、selection、
  diagnostics、failureをclearする。Undo / Redoではprofile stateとoutput stateを同じ履歴取引として再投影する。

---

## 14. Theme管理方針

### 14.1 対象テーマ

本ツールでは、以下のテーマを扱う。

- Light
- Dark
- System

System はOSやwxPythonの取得結果に応じて Light / Dark のいずれかへ解決してよい。

### 14.2 ThemeManager

テーマ管理は、ThemeManager または同等の共通機構に集約する。

方針:

- 色定義を各部品に散らさない
- ThemePalette などの共通定義を利用する
- 新規部品も共通テーマ機構に接続する
- テーマ変更時にウィンドウツリーへ再適用する
- カスタム描画部品はテーマ変更後に再描画する

### 14.3 ThemePalette

ThemePalette には、少なくとも以下を含めることが望ましい。

- window background
- panel background
- text foreground
- disabled foreground
- border
- button background
- button foreground
- input background
- input foreground
- waveform background
- waveform line
- waveform grid
- preview background
- preview lane background
- preview shape colors
- cursor color
- warning color
- error color
- status background
- status foreground

### 14.4 色のハードコード

新規GUI部品では、色のハードコードを避ける。

必要な場合は、以下のいずれかとする。

- ThemePalette に色を追加する
- 既存Paletteの値を利用する
- OS標準に委ねる理由を明記する

### 14.5 テーマ切替時の処理

テーマ切替時は以下を行う。

- 設定値を更新する
- resolved theme を更新する
- MainFrameにテーマを適用する
- 子Windowへ再帰的にテーマを適用する
- カスタム描画部品を再描画する
- 必要に応じて `Layout()` / `Refresh()` を呼ぶ
- Statusへテーマ変更結果を表示してよい

### 14.6 禁止事項

以下は禁止する。

- 新規部品だけテーマ未適用にする
- ダイアログだけ白背景固定にする
- Darkテーマで黒文字を残す
- Lightテーマで白文字を残す
- disabled状態が判別不能になる
- テーマ変更後にPreview / Waveformが旧色のまま残る

---

## 15. 新規GUI部品のテーマ追従

### 15.1 基本方針

新規GUI部品を追加する場合は、テーマ追従を必須条件とする。

対象例:

- 新規Panel
- 新規Button
- 新規Label
- 新規TextCtrl
- 新規Gauge
- 新規List / Menu
- 新規CustomDraw panel
- 新規Toolbar相当部品
- 将来の音声変換設定部品
- MMD用WAV出力部品
- MMD一括出力のdestination dialog

### 15.2 実装時に確認すること

新規部品追加時は以下を確認する。

- 初期表示でテーマが適用される
- テーマ切替後に色が変わる
- disabled状態でも見える
- 文字が背景に埋もれない
- 親Panelと背景色が不自然にずれない
- カスタム描画の場合、Refreshされる
- サイズ変更時に表示が崩れない
- 既存レイアウトを壊さない

### 15.3 実装報告

新規GUI部品を追加した場合、実装報告に以下を含める。

- 追加した部品名
- 親Window / 親Sizer
- テーマ適用方法
- Layout対応
- Refresh対応
- Light / Dark / System の確認結果
- 未確認テーマがある場合はその理由

---

## 16. ダイアログのテーマ追従

### 16.1 基本方針

新規ダイアログを追加する場合は、テーマ追従を必須条件とする。

ダイアログは抜け漏れが起きやすいため、通常のPanel追加よりも明示的に確認する。

### 16.2 対象ダイアログ

対象例:

- エラーダイアログ
- 警告ダイアログ
- 処理中ダイアログ
- 分析中止確認ダイアログ
- 上書き確認ダイアログ
- 設定ダイアログ
- Aboutダイアログ
- Helpダイアログ
- 将来のmp3変換確認ダイアログ
- 将来のm4a変換確認ダイアログ
- MMD用WAV出力確認ダイアログ
- MMD一括出力destination dialog
- 将来のFFmpeg未検出ダイアログ
- 将来の変換失敗詳細ダイアログ

### 16.3 必須確認項目

新規ダイアログでは、少なくとも以下を確認する。

- 背景色が現在テーマに追従する
- 文字色が現在テーマに追従する
- ボタンが視認できる
- TextCtrl / List / Gauge が視認できる
- Darkテーマ時に黒文字が黒背景へ埋もれない
- Lightテーマ時に白文字が白背景へ埋もれない
- disabled状態が判別できる
- ダイアログ生成時点で現在テーマが適用される
- テーマ切替後に再度開いたダイアログにも新テーマが反映される
- 閉じた後に親Windowの状態が破綻しない

### 16.4 OS標準ダイアログ

OS標準ダイアログや wx 標準ダイアログでは、テーマ制御が困難な場合がある。

その場合は、以下を行う。

- 無理に独自描画へ置き換えない
- 制御できない範囲を明記する
- 重要なエラー表示は必要に応じて独自ダイアログ化を検討する
- テーマ未追従が仕様上許容されるか確認する

### 16.5 処理中ダイアログ

処理中ダイアログは、Busy状態と密接に関係する。

確認項目:

- 開いた時点で現在テーマが適用される
- Gauge / Progress 表示が見える
- フェーズ文字列が読める
- Warning表示が読める
- キャンセルボタンが見える
- キャンセル後に閉じる
- エラー後に閉じる
- Busy解除と整合する
- テーマ切替後に再度開いた場合も新テーマで表示される

### 16.6 エラーダイアログ

エラーダイアログは、例外情報表示仕様と連携する。

確認項目:

- 利用者向け要約が読める
- 詳細情報を開ける
- Python例外種別が確認できる
- エラーメッセージが確認できる
- traceback を表示する場合は長文でも破綻しない
- コピー可能であることが望ましい
- Dark / Light テーマで読める

---

## 17. Layout / Refresh / Update の判断基準

### 17.1 判断方針

GUI変更時は、`Layout()` / `Refresh()` / `Update()` を機械的に呼ぶのではなく、要否を確認する。

ただし、確認せずに省略してはならない。

### 17.2 Layout が必要になりやすい変更

- 新規部品追加
- 部品削除
- Show / Hide
- ラベル変更
- 多行メッセージ変更
- ダイアログ内容変更
- Sizer構成変更
- 最小サイズ変更
- フォント変更
- テーマ変更でサイズが変わる場合

### 17.3 Refresh が必要になりやすい変更

- カスタム描画データ変更
- 波形データ変更
- Previewデータ変更
- カーソル位置変更
- Viewport変更
- Zoom変更
- テーマ色変更
- クリア処理
- error / warning の表示切替
- disabled表示の見た目変更

### 17.4 Update が必要になりやすい変更

- 長時間処理直前のUI反映
- 処理中ダイアログ表示
- Gauge更新
- 即時Status表示
- ユーザーにすぐ見せる必要がある警告

### 17.5 実装報告時の記載

GUI変更時は、以下のように報告する。

```text
Layout:
- 対応した / 不要と判断した
- 理由:

Refresh:
- 対応した / 不要と判断した
- 理由:

Update:
- 対応した / 不要と判断した
- 理由:
```

---

## 18. GUI変更時の受け入れ条件

### 18.1 共通受け入れ条件

GUI変更時は、以下を満たすこと。

- 追加したGUI部品が表示される
- 既存レイアウトを壊していない
- リサイズ時に表示が破綻しない
- 必要な `Layout()` / `Refresh()` / `Update()` が行われている
- 状態変更後に古い表示が残らない
- 既存の操作有効/無効ルールと矛盾しない
- Light / Dark / System テーマに追従する
- 新規部品だけテーマ未適用になっていない
- disabled状態が視認できる
- エラー時にUIが復帰する

### 18.2 ダイアログ受け入れ条件

新規ダイアログまたは変更したダイアログでは、以下を満たすこと。

- 現在テーマで表示される
- ダイアログ内の文字が読める
- ボタンの視認性が保たれる
- エラー・警告・確認内容が過不足なく表示される
- 詳細表示がある場合、長文でも破綻しない
- 閉じた後に親画面の状態が破綻しない
- テーマ切替後に再度開いた場合も新テーマで表示される

### 18.3 Preview / Waveform受け入れ条件

Preview / Waveform を変更した場合は、以下を満たすこと。

- 入力変更時にクリアされる
- 解析成功時に更新される
- 解析失敗時に旧結果を復元する場合はERRORと保存禁止を同時表示し、current成功結果と誤認させない
- 再生位置カーソルが更新される
- テーマ変更後に再描画される
- Viewport変更後に表示が更新される
- Zoom変更後に表示が更新される
- PreviewとWaveformのViewportがずれない

### 18.4 Busy受け入れ条件

Busy状態に関わる変更では、以下を満たすこと。

- 処理開始時に関連操作が無効化される
- 処理成功時に解除される
- 処理失敗時に解除される
- キャンセル時に解除される
- 例外時に解除される
- 処理中ダイアログが閉じる
- 古い結果が反映されない

---

## 19. GUI実装報告の必須項目

GUI変更を行った場合、実装報告には以下を含める。

### 19.1 基本項目

- 確認したファイル
- 変更したファイル
- 追加・変更したGUI部品
- 変更した状態管理
- 変更したAction State
- 変更した表示更新処理

### 19.2 再描画・レイアウト

- `Layout()` 対応内容
- `Refresh()` 対応内容
- `Update()` 対応内容
- 不要と判断した場合の理由
- リサイズ確認結果

### 19.3 テーマ

- テーマ適用方法
- Light確認結果
- Dark確認結果
- System確認結果
- 未確認テーマがある場合の理由
- ハードコード色の有無
- ThemePalette追加の有無

### 19.4 ダイアログ

ダイアログを追加・変更した場合は以下を報告する。

- ダイアログ名
- 用途
- テーマ適用方法
- 親Window
- 閉じた後の状態復帰
- Light / Dark / System 確認結果
- OS標準ダイアログで制御できない範囲

### 19.5 手動確認

手動確認した場合は以下を報告する。

- 起動直後
- TEXT読込後
- WAV読込後
- 処理実行中
- 処理成功後
- 処理失敗後
- 再生中
- 停止後
- テーマ切替後
- 入力再読込後
- Preview / Waveform クリア後

---

## 20. テスト・手動確認観点

### 20.1 自動テスト候補

GUI変更時の自動テスト候補:

- MainFrame初期化
- UiStateプロパティ
- Action State
- ThemeManager
- ViewportController
- PreviewPanel setter / clear
- WaveformPanel setter / clear
- Busy状態遷移
- worker成功 / 失敗
- late callback discard
- ダイアログ生成ロジック

### 20.2 手動確認候補

手動確認候補:

- アプリ起動
- TEXT読込
- WAV読込
- 処理実行
- VMD保存
- Play / Stop
- Zoom In / Out / Reset
- テーマ切替
- 解析失敗
- 入力再読込
- Recent Files読込
- 処理中キャンセル
- ダイアログ表示
- リサイズ

### 20.3 テーマ確認

テーマ確認では以下を見る。

- Light
- Dark
- System
- 起動時テーマ復元
- テーマ切替直後
- テーマ切替後に新規ダイアログを開く
- Preview / Waveform の色
- disabled部品の視認性
- エラー表示の視認性

### 20.4 GUI変更時の最小確認

時間が限られる場合でも、GUI変更時は最低限以下を確認する。

- 起動する
- 追加部品が表示される
- Light / Dark で読める
- 対象操作後に表示が更新される
- エラー時に固まらない
- 実装報告に未確認範囲を書く

### 20.5 選択イベントのmanual crossfade notice

選択中のgroup末尾eventにmanual crossfadeが実際に成立し、重複区間内の次母音の
明示control pointが0.95以上の場合、RightPaneの選択イベント領域へ非モーダルnoticeを
表示する。

- headerは「次の口形とクロスフェードしています。」
- detailは対象母音、0.95以上であること、PreviewとMMDでの確認案内を表示する
- headerだけbold、headerとdetailは`ThemePalette.attention_text`を使用する
- B4の反映制限notice、操作notice、slope helperとは別control・別stateで管理する
- 選択source event以外では表示しない
- target高値がない、actual overlapがない、automatic handoffだけの場合は表示しない
- modal dialog、Warning tab、bottom Statusへ重複表示しない
- noticeだけを理由にVMD保存を禁止しない

終了offsetの正方向最大値は選択中eventと直後の非0・異母音shapeからcoreが解決した
dynamic rangeを使う。範囲外入力はGUIで選択不能にし、coreでもfail closedに拒否する。

---

## 21. 禁止事項

以下は禁止する。

### 21.1 状態管理

- UiStateを更新せずに表示だけ変える
- 表示だけ変えてAction Stateを更新しない
- Busy解除を忘れる
- 解析失敗後に保存可能状態を残す
- 古いworker結果を現在状態へ反映する
- 入力再読込後に古いPreviewを残す

### 21.2 再描画

- カスタム描画部品のデータ更新後にRefreshしない
- テーマ変更後にPreview / Waveformを再描画しない
- Viewport変更後に片方の表示だけ更新する
- クリア処理後に古い描画が残る

### 21.3 テーマ

- 新規部品だけテーマ未適用にする
- ダイアログだけ白背景固定にする
- Darkテーマで黒文字を使う
- Lightテーマで白文字を使う
- disabled状態が判別不能になる
- ThemePaletteを使わず色を散らす

### 21.4 ダイアログ

- 新規ダイアログでテーマ追従を確認しない
- エラーダイアログで詳細が確認できない
- 処理中ダイアログがBusy状態とずれる
- ダイアログを閉じた後に親画面が不整合になる

### 21.5 実装報告

- GUI変更なのにテーマ確認を書かない
- GUI変更なのにLayout / Refresh / Update の要否を書かない
- 手動確認していない状態を確認済みと書く
- 未確認範囲を隠す

---

## 22. 関連文書

### 22.1 `docs/Specification_Prompt_v4.md`

GUI全体仕様、画面構成、MS16以降の大枠仕様を定義する。

本書は、GUI状態管理・再描画・テーマ追従の詳細を補完する。

### 22.2 `docs/Security_Safety_Specification.md`

入力安全性、エラー表示、例外情報、設定破損時の扱いなどを定義する。

GUIエラー表示やダイアログの詳細は、本書と併せて参照する。

### 22.3 `docs/MMD_Audio_WAV_Compatibility_Specification.md`

MS16以降の音声入力、解析用WAV、MMD用WAV出力を定義する。

mp3 / m4a 変換中ダイアログや変換失敗表示は、本書のGUI規則に従う。

### 22.4 `docs/VMD_Output_Specification.md`

VMD出力仕様を定義する。

VMD保存成功 / 失敗時のGUI表示は、本書のStatus・Error表示規則に従う。

### 22.5 `docs/repo_milestone.md`

マイルストーン履歴と現在地を記録する。

GUI仕様に関わる大きな変更は、必要に応じて記録する。

### 22.6 `docs/Version_Control.md`

変更履歴を記録する。

本書の更新やGUI仕様変更も記録対象とする。

---

## 23. 変更履歴

### 2026-08-20 / MS23-B6 cross regression同期

- model profileのSelect / Apply、CRUD lock、startup / reset / rollback、Undo / Redo投影境界を追加。
- profile適用後のPreview、writer、diagnostics、report同期と、fail-closed表示契約を明記。

### 2026-07-27 / MS21-B7追加tab補正

- Preview eventのcanonical user click成功後だけRightPaneの「選択イベント」tabへ
  自動切替する契約を追加。
- same-event再clickを対象とし、stale / Busy / lifecycle同期ではcurrent tabを維持する。
- 自動検証は完了し、追加補正を含むMS21-B7範囲のユーザー手動GUI確認は
  通過・問題なしと報告された。

### 2026-07-26 / MS21-B5追加補正

- 単イベントmanual crossfadeの選択event noticeとdynamic終了offset範囲を追加。
- 0.95以上のtarget明示control pointをclipせず、attention表示だけに留める契約を固定。
- ユーザーGUI確認は通過・問題なしと報告された。

### 2026-07-19 / MS20-B7

- output diagnosticsのclear / rebuildとRightPane表示契約を追加。
- analysis cancel要求中とterminal後のBusy / Status遷移を固定。
- parameter変更とlate / duplicate callbackの状態非持越しを明記。

### 2026-05-01 / 初版

- wxPython GUI の状態管理・再描画・テーマ追従・ダイアログ運用を独立文書化。
- UiState / Action State / 表示状態の分離を明記。
- Busy状態、長時間処理、late callback discard の基本方針を整理。
- `Layout()` / `Refresh()` / `Update()` の判断基準を定義。
- Waveform / Preview / Status / InfoPanel の更新条件を整理。
- Light / Dark / System テーマ追従をGUI実装の受け入れ条件として明記。
- 新規GUI部品と新規ダイアログのテーマ追従を必須条件として定義。
- GUI変更時の実装報告必須項目を定義。
- GUI変更時の禁止事項を整理。
