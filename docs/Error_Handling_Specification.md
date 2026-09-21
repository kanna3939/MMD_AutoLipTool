# MMD_AutoLipTool エラーハンドリング仕様書

## 1. 文書情報

- 文書名: `docs/Error_Handling_Specification.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象バージョン系: Ver0.4.x 以降
- 現行基準: MS15 closeout 後 / MS16 以降の拡張準備
- 主対象GUI: wxPython
- 主実装領域:
  - `src/gui_wx/`
  - `src/core/`
  - `src/vmd_writer/`
- 関連外部処理:
  - Whisper
  - FFmpeg
  - ffprobe
- 主対象環境: Windows 11
- 主開発環境: Codex
- Coding AI 前提: Codex
- 関連文書:
  - `docs/Specification_Prompt_v4.md`
  - `docs/Security_Safety_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/MMD_Audio_WAV_Compatibility_Specification.md`
  - `docs/VMD_Output_Specification.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` におけるエラーハンドリングの仕様を定義する。

本書の目的は、単に例外を捕捉することではない。

本書では、以下を明確にする。

- 何をエラーとして扱うか
- どの処理レイヤーで失敗したか
- どのエラー分類を使うか
- ユーザーにどのような要約を表示するか
- 開発・問い合わせ用にどの詳細情報を残すか
- Python例外種別とエラーメッセージをどのように保持するか
- Whisper / FFmpeg / ffprobe の失敗をどう扱うか
- 長時間処理をどう扱うか
- エラー後にGUI状態をどう復帰するか
- 不完全なVMD / WAV / 一時ファイルをどう扱うか
- worker / callback / timer 内例外をどう扱うか

本書の基本方針は、以下である。

```text
不正確な成功より、安全で説明可能な失敗を優先する。
```

---

## 3. 適用範囲

本書は、以下に適用する。

- アプリ起動
- 設定読込
- TEXT読込
- 音声ファイル読込
- wav / mp3 / m4a 入力
- ffprobe による音声情報取得
- FFmpeg による解析用WAV変換
- FFmpeg によるMMD用WAV出力
- 解析用WAV検証
- MMD用WAV検証
- Whisperモデル読込
- Whisper transcribe
- RMS解析
- pipeline / timing plan 生成
- observation生成
- Preview生成
- Waveform生成
- GUI表示更新
- テーマ適用
- ダイアログ表示
- VMD出力
- MMD用WAV出力
- 設定保存
- アプリ終了処理
- worker / callback / timer 内例外
- 予期しない例外

---

## 4. 非対象

本書では、以下を主対象としない。

- OS全体のエラー処理
- Windows Defender 等の判定
- MMD本体のエラー処理
- 外部音声素材の権利確認
- GitHub Releases 運用エラー
- ネットワークサービスとしての障害対応
- クラッシュレポート自動送信
- サーバー側ログ収集
- 完全な障害復旧システム

ただし、これらが本ツールのGUI表示や利用者向け案内に関わる場合は、必要に応じて本書の方針を参照する。

---

## 5. 基本方針

### 5.1 無言失敗禁止

エラー発生時に、無言で失敗してはならない。

少なくとも以下のいずれかを行う。

- GUI上で要約メッセージを表示する
- Statusに失敗状態を表示する
- エラーダイアログを表示する
- 詳細情報を確認可能にする
- ログまたはコピー可能な詳細情報に例外情報を残す

### 5.2 成功扱い禁止

失敗した処理を成功扱いしてはならない。

禁止例:

- 解析失敗後に「解析完了」と表示する
- VMD保存失敗後に「保存しました」と表示する
- MMD用WAV変換失敗後に出力成功として扱う
- Whisper失敗後に古い解析結果を保存可能状態にする
- Preview生成失敗後に古いPreviewを現在結果として残す

### 5.3 例外情報保持

予期しない例外や未定義エラーが発生した場合、少なくとも以下を保持する。

- Python例外種別
- エラーメッセージ
- 処理フェーズ

可能であれば以下も保持する。

- traceback
- 対象ファイル
- worker job id
- ffmpeg exit code
- ffmpeg stderr 要約
- input state
- analysis state
- playback state

### 5.4 ユーザー向け表示と詳細情報の分離

エラー表示は、以下の2層に分ける。

| 層 | 対象 | 内容 |
| --- | --- | --- |
| ユーザー向け要約 | 一般利用者 | 何が失敗したか、次に何をすればよいか |
| 詳細情報 | 開発・問い合わせ用 | 例外種別、メッセージ、フェーズ、traceback等 |

通常表示では、長大な内部例外やtracebackを直接全面表示しない。

ただし、詳細表示またはコピー可能な情報として確認できるようにする。

### 5.5 エラー後の復帰

エラー後は、可能な限り以下を満たす。

- Busy状態を解除する
- 処理中ダイアログを閉じる
- 関連ボタン・メニューの有効/無効を再計算する
- 古い成功結果を現在結果として扱わない
- Preview / Waveform / Status を適切に更新またはクリアする
- 不完全な出力ファイルを可能な限り削除する
- 再選択・再実行・再保存が可能な状態へ戻す

---

## 6. エラー情報モデル

### 6.1 基本モデル

エラー情報は、少なくとも以下の項目を持つことが望ましい。

```text
error_layer:
error_code:
phase:
severity:
user_message:
detail_message:
exception_type:
exception_message:
traceback:
target_path:
job_id:
recoverability:
```

### 6.2 error_layer

`error_layer` は、失敗が発生したレイヤーを表す。

レイヤーは本書 7章で定義する。

例:

```text
L2_AUDIO_PROBE_CONVERT
L4_WHISPER_ANALYSIS
L7_OUTPUT
```

### 6.3 error_code

`error_code` は、失敗内容を分類する安定した識別子である。

例:

```text
ffmpeg_execution_failed
whisper_transcribe_failed
vmd_write_failed
```

### 6.4 phase

`phase` は、処理フェーズを表す。

例:

```text
audio_convert_for_analysis
whisper_transcribe
vmd_write
```

### 6.5 severity

`severity` は、エラーの重大度を表す。

| 値 | 意味 |
| --- | --- |
| `info` | 情報 |
| `warning` | 警告。fallback等で継続可能 |
| `error` | 処理失敗。ただしアプリ継続可能 |
| `fatal` | アプリ継続困難 |
| `cancelled` | ユーザーキャンセル |

### 6.6 recoverability

`recoverability` は、復帰可能性を表す。

| 値 | 意味 |
| --- | --- |
| `retry_possible` | 再実行可能 |
| `select_file_again` | ファイル再選択が必要 |
| `fallback_used` | fallback使用により継続 |
| `restart_recommended` | 再起動推奨 |
| `cannot_continue` | 現在処理は継続不可 |
| `cancelled_by_user` | ユーザー操作により中止 |

### 6.7 最低限保持する情報

詳細情報として最低限保持する項目は以下とする。

```text
エラー分類:
処理フェーズ:
例外種別:
エラーメッセージ:
```

対象ファイルがある場合は、ファイル名またはパスも保持する。

---

## 7. エラーレイヤー分類

本ツールでは、エラーを以下のレイヤーに分類する。

```text
L0: 環境・起動レイヤー
L1: 入力ファイル選択レイヤー
L2: 音声プローブ・変換レイヤー
L3: 解析用データ生成レイヤー
L4: Whisper / 音声解析レイヤー
L5: Pipeline / Timing Plan レイヤー
L6: Preview / Waveform / GUI表示レイヤー
L7: VMD / MMD用WAV 出力レイヤー
L8: 設定保存・終了処理レイヤー
L9: 予期しない例外・未定義エラーレイヤー
```

---

## 8. L0: 環境・起動レイヤー

### 8.1 対象

L0 は、アプリ起動や実行環境に関する問題を扱う。

対象:

- アプリ起動
- PyInstaller onefile 起動
- 依存ライブラリ読込
- 設定ファイル読込
- FFmpeg / ffprobe の存在確認
- Whisperモデル読込準備
- assets読込
- 初期テーマ復元

### 8.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `app_startup_failed` | アプリ起動失敗 |
| `dependency_missing` | 必要ライブラリ不足 |
| `settings_load_failed` | 設定読込失敗 |
| `settings_corrupted` | 設定ファイル破損 |
| `ffmpeg_not_found` | FFmpegが見つからない |
| `ffprobe_not_found` | ffprobeが見つからない |
| `whisper_model_load_failed` | Whisperモデル読込失敗 |
| `asset_load_failed` | アイコン等のasset読込失敗 |
| `theme_restore_failed` | テーマ復元失敗 |

### 8.3 扱い

- 設定破損時は安全なデフォルトで起動する
- assets読込失敗は可能なら代替表示で起動する
- FFmpeg未検出時は、音声変換系機能のみ無効化して起動継続できるなら継続する
- Whisperモデル読込失敗は、解析実行時エラーとして遅延扱いしてよい
- 起動不能な場合は、Python例外種別とエラーメッセージを確認可能にする

---

## 9. L1: 入力ファイル選択レイヤー

### 9.1 対象

L1 は、ユーザーが選択した入力ファイルに関する問題を扱う。

対象:

- TEXTファイル
- wav / mp3 / m4a ファイル
- Recent Files
- counterpart auto-load
- ファイル存在確認
- 拡張子確認
- ファイルサイズ確認

### 9.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `input_file_not_found` | 入力ファイルが存在しない |
| `audio_file_not_found` | 音声ファイルが存在しない |
| `audio_path_is_directory` | フォルダが指定されている |
| `audio_file_too_large` | 入力ファイルサイズ上限超過 |
| `unsupported_audio_extension` | 対応外拡張子 |
| `text_file_not_found` | TEXTファイルが存在しない |
| `text_decode_failed` | TEXT文字コード読込失敗 |
| `text_validation_failed` | TEXT安全性検証失敗 |
| `counterpart_load_failed` | 相方ファイル自動読込失敗 |

### 9.3 状態復帰

入力ファイル選択で失敗した場合は以下を行う。

- 失敗した入力側を無効化する
- 解析結果を無効化する
- Previewをクリアする
- VMD保存を無効化する
- 必要に応じてWaveformをクリアする
- Busy状態を解除する
- 再選択可能にする

### 9.4 counterpart auto-load

counterpart auto-load の失敗は、主読込の失敗とは分ける。

- 主読込が成功し、相方読込だけ失敗した場合、主読込まで失敗扱いにしない
- 相方未存在は原則としてエラーにしない
- 相方読込失敗を警告するかサイレントにするかは、現行仕様に従う
- ただし、内部詳細では `counterpart_load_failed` として記録してよい

---

## 10. L2: 音声プローブ・変換レイヤー

### 10.1 対象

L2 は、ffprobe / FFmpeg を使った音声情報取得・変換を扱う。

対象:

- ffprobe実行
- 入力音声メタ情報取得
- 音声ストリーム確認
- 音声長確認
- 解析用WAV生成
- MMD用WAV生成
- FFmpeg実行
- 解析用WAV検証

### 10.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `ffprobe_not_found` | ffprobeが見つからない |
| `ffprobe_permission_error` | ffprobe実行権限不足 |
| `ffprobe_timeout` | ffprobe実行タイムアウト |
| `ffprobe_execution_failed` | ffprobe実行失敗 |
| `ffprobe_invalid_json` | ffprobe結果(JSON)不正 |
| `audio_stream_not_found` | 音声ストリームが存在しない |
| `audio_duration_missing` | 音声長が取得できない |
| `audio_duration_too_long` | 音声長上限超過 |
| `ffmpeg_not_found` | FFmpegが見つからない |
| `ffmpeg_timeout` | FFmpegが強制停止条件に到達 |
| `ffmpeg_long_running` | FFmpeg処理が長時間化している |
| `ffmpeg_cancelled` | ユーザーがFFmpeg処理を中止した |
| `ffmpeg_execution_failed` | FFmpeg変換失敗 |
| `analysis_wav_generation_failed` | 解析用WAV生成失敗 |
| `analysis_wav_cache_dir_failed` | キャッシュディレクトリ作成失敗 |
| `analysis_wav_output_failed` | 解析用WAVが出力されていない |
| `analysis_wav_cleanup_failed` | 不完全な解析用WAVの削除失敗 |
| `mmd_wav_validation_failed` | MMD用WAV検証失敗 |
| `output_permission_denied` | 出力先権限不足 |

MS18-B4以降、FFmpeg / ffprobe未検出時の通常表示では、探索結果を以下の粒度で示す。

- `アプリ内 FFmpeg フォルダから検出`
- `同梱 FFmpeg から検出`
- `PATH から検出`
- `未検出`

この表示ではローカル絶対パスを常時表示しない。確認対象は、アプリ内 `FFmpeg` フォルダ、PyInstaller同梱FFmpeg、環境変数 `PATH` とする。

### 10.3 FFmpeg失敗と検証失敗の分離

以下は別のエラーとして扱う。

```text
ffmpeg_execution_failed
→ FFmpeg実行自体が失敗した

analysis_wav_output_failed
→ FFmpegは終了したが、解析用WAVとして仕様不適合だった

mmd_wav_validation_failed
→ FFmpegは終了したが、MMD用WAVとして仕様不適合だった
```

### 10.4 状態復帰

解析用WAV変換失敗時:

- 音声入力は保持してよい
- 解析用WAVは破棄する
- Waveformはクリアする
- Previewはクリアする
- 解析結果は無効化する
- VMD保存を無効化する
- Busy状態を解除する
- 再変換または再読込可能にする

MMD用WAV変換失敗時:

- VMD出力とは分けて扱う
- VMDが成功している場合は、その状態を正確に表示する
- MMD用WAVは失敗として表示する
- 不完全なMMD用WAVは可能な限り削除する
- 再出力可能にする

---

## 11. L3: 解析用データ生成レイヤー

### 11.1 対象

L3 は、変換済み解析用WAVから、AutoLipTool内部の解析データを生成する処理を扱う。

対象:

- 解析用WAV読込
- 波形データ生成
- RMS系列生成
- 音声長確認
- mono波形作成
- timing plan 前処理

### 11.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `analysis_wav_load_failed` | 解析用WAV読込失敗 |
| `waveform_build_failed` | 波形データ生成失敗 |
| `rms_series_failed` | RMS系列生成失敗 |
| `audio_duration_invalid` | 音声長が不正 |
| `analysis_audio_invalid` | 解析用音声が不正 |

### 11.3 RMS失敗の扱い

RMS系列生成に失敗しても、fallback可能な場合は致命的エラーにしない。

扱い:

```text
rms_series_failed
→ fallback可能なら warning
→ fallback不可なら error
```

fallbackした場合は、詳細情報または observation に記録する。

### 11.4 状態復帰

L3で致命的エラーが発生した場合:

- 音声入力は保持してよい
- Waveformは生成失敗ならクリアする
- Previewはクリアする
- 解析結果は無効化する
- VMD保存を無効化する
- Busy状態を解除する
- 再実行可能にする

---

## 12. L4: Whisper / 音声解析レイヤー

### 12.1 対象

L4 は、Whisperによる音声解析を扱う。

対象:

- Whisperモデル読込
- Whisper transcribe
- segment取得
- word取得
- Whisper結果解析
- Whisper処理の長時間化
- Whisperキャンセル

### 12.2 代表エラー

| error_code | 意味 | 基本扱い |
| --- | --- | --- |
| `whisper_model_load_failed` | Whisperモデル読込失敗 | error |
| `whisper_audio_load_failed` | Whisperへ渡す音声の読込失敗 | error |
| `whisper_transcribe_failed` | transcribe実行中の失敗 | error |
| `whisper_result_invalid` | 結果形式が期待と異なる | fallback可なら warning |
| `whisper_no_segments` | segment情報が得られない | fallback可なら warning |
| `whisper_no_words` | word情報が得られない | segment fallback可なら warning |
| `voice_only_transcription_empty` | 音声のみ入力で有効な書き起こし本文がない | error |
| `voice_only_timing_anchor_failed` | 音声のみ入力でtiming anchorを取得できない | error |
| `whisper_long_running` | Whisper処理が長時間化 | warning |
| `whisper_timeout` | Whisper処理が停止条件に到達 | error |
| `whisper_cancelled` | ユーザーが中止した | cancelled |
| `analysis_cancelled` | 分析全体が中止された | cancelled |

### 12.3 致命的Whisperエラー

以下は原則として解析停止扱いとする。

- `whisper_model_load_failed`
- `whisper_audio_load_failed`
- `whisper_transcribe_failed`
- `whisper_timeout`

状態復帰:

- TEXT入力は保持する
- 音声入力は保持する
- Waveformは保持してよい
- 解析結果は無効化する
- Previewはクリアする
- VMD保存を無効化する
- Busy状態を解除する
- 再実行可能にする
- Python例外種別とエラーメッセージを詳細表示に残す

音声のみ入力では、書き起こし本文またはtiming anchorを取得できない場合も解析停止扱いとする。入力音声と、既に適用済みの編集済み書き起こしは保持してよいが、`current_timing_plan` を破棄し、再解析が完了するまでVMD保存を無効化する。

### 12.4 fallback可能なWhisper結果不足

以下は、fallback可能な場合は警告扱いとする。

- `whisper_result_invalid`
- `whisper_no_segments`
- `whisper_no_words`

例:

```text
word情報なし
→ segment fallback
→ segmentも不十分なら均等配分fallback
→ 処理継続可能なら warning
```

fallbackを使用した場合は、Statusまたは詳細情報に記録してよい。

---

## 13. L5: Pipeline / Timing Plan レイヤー

### 13.1 対象

L5 は、TEXTと音声解析結果を統合し、VMD出力用 timing plan を生成する処理を扱う。

対象:

- かな化
- 母音列生成
- Whisper anchor 配分
- 均等配分fallback
- RMS補正
- peak_value評価
- observation生成
- bridge / smoothing 判断
- timing plan 構築

### 13.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `text_to_vowel_failed` | 母音列生成失敗 |
| `timing_plan_build_failed` | timing plan構築失敗 |
| `no_vowel_events` | 母音イベントが存在しない |
| `anchor_assignment_failed` | anchor配分失敗 |
| `peak_evaluation_failed` | peak評価失敗 |
| `observation_build_failed` | observation生成失敗 |
| `pipeline_result_invalid` | pipeline結果不正 |
| `voice_only_text_conversion_failed` | 書き起こしの日本語読み変換失敗 |
| `voice_only_vowel_empty` | 書き起こしから母音列を生成できない |
| `voice_only_edited_text_empty` | 編集済み書き起こしが空 |
| `voice_only_timing_plan_invalid` | 音声のみ入力の再解析情報が不足 |

### 13.3 fallback方針

Pipeline内では、fallback可能な失敗を致命的エラーにしない。

例:

```text
anchor_assignment_failed
→ 均等配分fallback可能なら warning
→ fallback不可なら error
```

### 13.4 状態復帰

L5で致命的エラーが発生した場合:

- 入力TEXTは保持する
- 音声入力は保持する
- Waveformは保持してよい
- 解析結果は無効化する
- Previewはクリアする
- VMD保存を無効化する
- Busy状態を解除する
- 再実行可能にする

---

## 14. L6: Preview / Waveform / GUI表示レイヤー

### 14.1 対象

L6 は、内部データは存在するが、GUI表示で問題が発生した場合を扱う。

対象:

- Preview変換
- Preview描画
- Waveform描画
- Viewport更新
- 再生カーソル更新
- テーマ適用
- ダイアログ生成
- Status更新
- InfoPanel更新

### 14.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `preview_build_failed` | Previewデータ生成失敗 |
| `preview_render_failed` | Preview描画失敗 |
| `waveform_render_failed` | Waveform描画失敗 |
| `viewport_update_failed` | Viewport更新失敗 |
| `playback_cursor_update_failed` | 再生カーソル更新失敗 |
| `theme_apply_failed` | テーマ適用失敗 |
| `dialog_open_failed` | ダイアログ生成失敗 |
| `status_update_failed` | Status更新失敗 |

### 14.3 扱い

L6の失敗では、内部解析結果が正常な場合がある。

そのため、必ずしもVMD保存不可にする必要はない。

ただし、以下を守る。

- 表示が失敗したことを通知する
- GUIが不安定な場合は安全側で操作を制限する
- callback / timer 例外を握りつぶさない
- Python例外種別とメッセージを詳細情報に残す
- テーマ適用失敗時は視認不能な状態を放置しない

### 14.4 状態復帰

表示エラー時:

- 可能なら内部解析結果は保持する
- Preview生成失敗時はPreviewを無効表示にする
- Waveform描画失敗時はWaveformを無効表示にする
- VMD保存可否は解析結果の有効性に基づいて判断する
- GUI全体が不安定なら安全側で保存不可にする
- Busy状態が関係する場合は解除する

---

## 15. L7: VMD / MMD用WAV 出力レイヤー

### 15.1 対象

L7 は、ユーザー向け出力ファイルの保存処理を扱う。

対象:

- VMD保存
- MMD用WAV保存
- MMD一括出力
- 上書き確認
- 一時ファイル
- 保存先権限
- 出力後検証
- 不完全ファイル削除

### 15.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `vmd_write_failed` | VMD書き出し失敗 |
| `vmd_validation_failed` | VMD出力検証失敗 |
| `mmd_wav_write_failed` | MMD用WAV出力失敗 |
| `mmd_wav_validation_failed` | MMD用WAV検証失敗 |
| `output_permission_denied` | 出力先権限不足 |
| `output_path_invalid` | 出力パス不正 |
| `output_path_inspection_failed` | 一括出力先の存在・属性検査に失敗 |
| `output_file_locked` | 出力ファイルが使用中 |
| `output_cancelled` | ユーザーが保存をキャンセル |
| `partial_output_cleanup_failed` | 不完全ファイル削除失敗 |
| `output_destination_collision` | 一括出力先に同名entryが存在 |
| `output_path_too_long` | 一括出力のpath長が上限超過 |
| `delivery_current_state_invalid` | 一括出力に必要な現在状態が不正 |
| `delivery_ffmpeg_unavailable` | 一括出力に必要なFFmpegを解決できない |
| `source_audio_changed` | 一括出力中に入力音声identityが変化 |
| `delivery_state_stale` | 一括出力開始時とcommit直前の状態が不一致 |
| `delivery_commit_guard_failed` | commit前の状態確認に失敗 |
| `delivery_commit_failed` | final directoryへの確定に失敗 |
| `delivery_worker_failed` | 一括出力workerの実行に失敗 |

MS25の現行coreでは、Windowsのcomponent / absolute path長超過を含む入力パス検証エラーを`output_path_invalid`へ正規化する。`output_path_too_long`は既存のerror taxonomyおよびGUI safe-message互換キーとして保持するが、現行coreのpath検証が返すterminal codeとは区別する。B7ではこの対応関係を変更せず、code一覧・safe message・利用者向け文言の整合だけを確認する。

### 15.3 VMD保存失敗

VMD保存失敗時:

- 解析結果は保持する
- Previewは保持してよい
- Waveformは保持する
- 保存成功扱いにしない
- 不完全VMDを可能な限り削除する
- 再保存可能にする
- Python例外種別またはエラーメッセージを確認可能にする

### 15.4 MMD用WAV保存失敗

MMD用WAV保存失敗時:

- VMD保存と分けて扱う
- VMDが成功している場合、その状態を正確に表示する
- MMD用WAVは失敗として表示する
- 不完全WAVを可能な限り削除する
- 再出力可能にする

### 15.5 VMDとMMD用WAVの両方を出力する場合の4パターン

MS17以降でVMDとMMD用WAVの両方を出力する場合、以下を区別する。

| VMD | MMD用WAV | 扱い |
| --- | --- | --- |
| 成功 | 成功 | 両方成功 |
| 成功 | 失敗 | VMD成功、WAV失敗を明示 |
| 失敗 | 成功 | VMD失敗、WAV成功を明示 |
| 失敗 | 失敗 | 両方失敗 |

どちらか片方だけ成功した場合、ユーザーが次に何をすればよいかを表示する。

### 15.6 MS25 MMD一括出力

MMD一括出力は、VMD、MMD用WAV、診断レポートを同一の専用directoryへまとめるtransactionとして扱う。

- 3成果物はfinal directoryへ直接書き込まず、temporary / staging directoryで生成・検証する。
- 同名のdirectory、file、symlink、reparse pointがある場合はcollisionとして拒否し、merge・置換・上書きを行わない。
- 生成、validation、source identity、commit guard、commitのいずれかが失敗した場合は、既存final directoryと個別保存出力を変更しない。
- commit線形化点前のcancel / failureではstagingだけをcleanupする。cleanup失敗はprimary failureまたはcancelと併記し、成功扱いにしない。
- commit開始後にcancelが到着しても、既にcommitされたfinal directoryをcancel cleanupで削除せず、terminal resultのcommit成否を正本とする。
- 通常UIにはraw exception、traceback、staging pathを表示しない。collision、stale、source変更、commit失敗は安全な案内へ写像する。

---

## 16. L8: 設定保存・終了処理レイヤー

### 16.1 対象

L8 は、設定保存やアプリ終了時の処理を扱う。

対象:

- 設定読込
- 設定保存
- Recent Files保存
- テーマ保存
- ウィンドウ位置保存
- splitter比率保存
- 終了時処理
- 一時ファイル掃除

### 16.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `settings_load_failed` | 設定読込失敗 |
| `settings_corrupted` | 設定ファイル破損 |
| `settings_save_failed` | 設定保存失敗 |
| `recent_files_save_failed` | 最近使ったファイル保存失敗 |
| `theme_save_failed` | テーマ保存失敗 |
| `shutdown_cleanup_failed` | 終了時掃除失敗 |

### 16.3 扱い

- 設定読込失敗時は、安全なデフォルトで起動する
- 設定保存失敗時は警告する
- 設定保存失敗を理由に解析やVMD出力まで失敗扱いにしない
- 保存できなかった設定は次回復元されないことを必要に応じて示す
- 終了時掃除失敗は、必要に応じて詳細情報に残す

### 16.4 MS22 INI / preset persistence

- missingまたはinvalidなINIは安全なdefault generation stateで起動し、sessionのbase、history、selectionを生成しない。
- foregroundのINI save failureはin-memory stateを保持し、同一sessionでは初回だけ警告して後続saveを停止する。
- close-onlyのINI save failureはblocking警告なしで終了し、次回起動ではlast successful settingsを復元する。
- `presets.json`のmissingはbuilt-inとuser mutation可能状態で開始する。invalid / unsupported / read failureはbuilt-inを
  継続し、現在のgeneration / output stateを変更せず、同一sessionのuser mutationを停止する。
- JSONのwrite / replace failureは旧JSON、generation、output history、Preview、diagnosticsを保持し、失敗を成功扱いにしない。

### 16.5 MS23 model profile persistence / guard

- `profiles.json`のmissingはno-profile（日本語5母音）で開始する。`invalid_json`、`unsupported_schema`、
  `invalid_schema`、`read_failed`、`duplicate_id`、`duplicate_display_name`、`limit_exceeded`はpartial importせず、
  no-profileへfail closedし、profileのcreate / update / deleteを停止する。
- active profileの値・set・default reference変更とDeleteは`active_profile_locked`または
  `active_profile_direct_edit_locked`で拒否する。active profileのbaseline値更新・Deleteは
  `active_profile_baseline_locked`で拒否する。profile参照中のuser preset Deleteは
  `preset_referenced_by_profile`、参照不在を安全に確認できない場合は`profile_reference_check_unavailable`で拒否する。
- profileのmissing profile / missing default presetはfallback reasonを保持し、解決可能なno-profileまたはprofile defaultへ
  正規化する。失敗した操作では旧profile一覧、旧JSON、旧state、output history、Preview、diagnosticsを変更しない。
- `write_failed` / `replace_failed`では一時ファイルを残さず、旧JSONとin-memory stateを保持する。INI保存失敗も同一sessionの
  profile / generation / output stateを巻き戻さず、警告と次回未復元の可能性だけを示す。
- profile適用後に名前 tupleが不正、空出力、または解析失敗となった場合、Previewは選択中setの表示名を保持したまま空状態またはERRORを表示し、
  writer / fingerprintはready扱いにしない。例外をGUIへ漏らさない。

---

## 17. L9: 予期しない例外・未定義エラーレイヤー

### 17.1 対象

L9 は、分類済みのどれにも当てはまらない例外を扱う。

代表例:

- 未分類のPython例外
- 内部状態不整合
- 想定外のNone
- 予期しない型
- callback内の未処理例外
- GUI破棄後の参照
- 不明な外部ライブラリ例外

### 17.2 代表エラー

| error_code | 意味 |
| --- | --- |
| `unexpected_error` | 予期しないエラー |
| `unhandled_exception` | 未処理例外 |
| `internal_state_error` | 内部状態不整合 |
| `unknown_error` | 不明なエラー |

### 17.3 扱い

L9では以下を必ず守る。

- 無言で失敗しない
- Python例外種別を保持する
- エラーメッセージを保持する
- 処理フェーズを可能な限り保持する
- tracebackを詳細表示またはコピー可能情報として保持する
- Busy状態を解除する
- 古い結果を成功扱いにしない
- 再実行可能状態へ戻す

---

## 18. 処理フェーズ分類

エラー情報には、可能な限り処理フェーズを含める。

代表フェーズ:

| phase | 意味 |
| --- | --- |
| `startup` | アプリ起動 |
| `settings_load` | 設定読込 |
| `settings_save` | 設定保存 |
| `text_load` | TEXT読込 |
| `text_validate` | TEXT検証 |
| `audio_select` | 音声ファイル選択 |
| `audio_probe` | ffprobeによる音声情報取得 |
| `audio_convert_for_analysis` | 解析用WAV変換 |
| `audio_convert_for_mmd` | MMD用WAV変換 |
| `analysis_wav_validate` | 解析用WAV検証 |
| `mmd_wav_validate` | MMD用WAV検証 |
| `waveform_build` | 波形データ生成 |
| `rms_build` | RMS系列生成 |
| `whisper_model_load` | Whisperモデル読込 |
| `whisper_transcribe` | Whisper transcribe |
| `pipeline_build` | timing plan生成 |
| `preview_build` | Previewデータ生成 |
| `preview_render` | Preview描画 |
| `waveform_render` | Waveform描画 |
| `viewport_update` | Viewport更新 |
| `playback` | 再生 |
| `theme_apply` | テーマ適用 |
| `dialog_open` | ダイアログ表示 |
| `vmd_write` | VMD保存 |
| `mmd_wav_write` | MMD用WAV保存 |
| `shutdown` | 終了処理 |

---

## 19. 長時間処理・300秒確認方針

### 19.1 基本方針

Whisper / FFmpeg / ffprobe などの外部ライブラリ・外部ツール系処理では、処理が長時間化する可能性がある。

本ツールでは、初期閾値として 300秒を設定する。

ただし、300秒は強制停止タイムアウトではなく、長時間処理確認の閾値である。

### 19.2 確認ダイアログ

300秒を超えて処理が継続している場合、GUI上でユーザー確認ダイアログを表示する。

確認ダイアログでは、少なくとも以下を表示する。

- 処理名
- 処理フェーズ
- 経過時間
- 継続ボタン
- 中止ボタン

### 19.3 継続

ユーザーが継続を選んだ場合、処理を継続する。

継続後、さらに300秒経過した場合は再度確認してよい。

初期実装では、選択肢は以下に絞る。

```text
継続
中止
```

### 19.4 中止

ユーザーが中止を選んだ場合、可能な範囲で処理停止を要求し、キャンセル扱いとして状態復帰する。

中止は通常エラーではなく、ユーザーキャンセルとして扱う。

代表分類:

| error_code | 意味 |
| --- | --- |
| `external_process_cancelled` | 外部処理キャンセル |
| `ffprobe_cancelled` | ffprobeキャンセル |
| `ffmpeg_cancelled` | FFmpegキャンセル |
| `whisper_cancelled` | Whisperキャンセル |
| `analysis_cancelled` | 分析キャンセル |

### 19.5 FFmpeg / ffprobe の停止

FFmpeg / ffprobe のような subprocess は、可能であれば terminate / kill により停止する。

中止時は以下を行う。

- subprocess停止要求
- 不完全ファイル削除
- Busy解除
- 処理中ダイアログを閉じる
- Status更新
- 再実行可能状態へ復帰

### 19.6 Whisper の停止

Whisper の `transcribe()` は、実装方式によっては即時停止が難しい。

そのため、Whisperでは以下を許容する。

- 中止要求を記録する
- 即時停止できる場合は停止する
- 即時停止できない場合、完了後に返ってきた結果を破棄する
- 中止後に返った結果を現在状態へ反映しない
- job id または cancellation flag により late callback を破棄する

Whisperについて、「必ず即時killできる」とは仕様上断定しない。

### 19.7 GUIスレッド非ブロック

長時間処理はGUIスレッドで直接実行しない。

対象:

- Whisper transcribe
- ffprobe
- FFmpeg
- 音声変換
- 長い解析処理

300秒経過通知や確認ダイアログ表示は、GUIスレッドへ安全に通知する。

### 19.8 ダイアログのテーマ追従

長時間処理確認ダイアログは、`docs/GUI_State_Theme_Specification.md` に従い、Light / Dark / System テーマに追従する。

---

## 20. ユーザー向け表示

### 20.1 基本方針

ユーザー向け表示は、短く分かりやすくする。

表示すべき内容:

- 何が失敗したか
- 何を確認すればよいか
- 再試行できるか
- ファイルを選び直す必要があるか

### 20.2 表示例

#### TEXT読込失敗

```text
テキストファイルを読み込めませんでした。
文字コードまたは内容が対応外の可能性があります。
```

#### 音声変換失敗

```text
音声ファイルを変換できませんでした。
対応外の形式、またはファイルが破損している可能性があります。
```

#### Whisper失敗

```text
音声解析に失敗しました。
入力音声を確認してから、もう一度実行してください。
```

#### VMD保存失敗

```text
VMDファイルを保存できませんでした。
保存先の権限、ファイル名、または同名ファイルの使用状況を確認してください。
```

#### 長時間処理確認

```text
処理に時間がかかっています。
このまま処理を継続しますか？
```

### 20.3 避ける表示

通常表示では、以下を避ける。

- 長大なtraceback全文
- 入力テキスト全文
- ffmpeg stderr全文
- ユーザー名を含むフルパスの常時表示
- 開発者向け専門用語だけの表示

---

## 21. 詳細情報・問い合わせ用情報

### 21.1 詳細情報の目的

詳細情報は、開発・問い合わせ・原因切り分けのために用いる。

### 21.2 最低限含める項目

詳細情報には、少なくとも以下を含める。

```text
エラー分類:
処理フェーズ:
例外種別:
エラーメッセージ:
```

対象ファイルがある場合:

```text
対象ファイル:
```

外部ツールの場合:

```text
exit code:
stderr summary:
```

worker処理の場合:

```text
job id:
```

### 21.3 traceback

予期しない例外では、tracebackを詳細表示またはコピー可能情報として含めることが望ましい。

ただし、通常表示に常時展開しない。

### 21.4 コピー可能情報

問い合わせ用に、詳細情報をコピーできることが望ましい。

含める候補:

- アプリバージョン
- 処理フェーズ
- エラー分類
- 例外種別
- エラーメッセージ
- 対象ファイル名
- traceback
- ffmpeg exit code
- ffmpeg stderr要約

---

## 22. worker / callback / timer 例外

### 22.1 基本方針

GUIスレッド外、worker、timer、callback 内で発生した例外も、無言で失敗させてはならない。

対象例:

- 解析worker
- Whisper解析
- RMS計算
- mp3 / m4a 変換worker
- FFmpeg / ffprobe 実行
- 再生位置更新timer
- wx.CallAfter 経由のcallback
- Preview更新
- Waveform更新
- テーマ適用処理
- ダイアログ生成処理

### 22.2 worker例外

worker内例外は、成功/失敗を明示する結果としてメインスレッドへ戻す。

推奨構造:

```text
success: bool
result: optional result payload
error_type: optional exception class name
error_message: optional exception message
traceback: optional traceback text
phase: operation phase
job_id: worker job id
```

### 22.3 callback例外

callback内例外は可能な限り捕捉し、GUI上で通知する。

callback例外でアプリが不安定な状態のまま残らないようにする。

### 22.4 timer例外

timer内例外では、同じ例外が無限に繰り返されないようにする。

方針:

- 対象timerを停止する
- 状態を安全に戻す
- 例外情報を詳細表示へ渡す
- 再生中なら再生状態を解除する

### 22.5 late callback

キャンセル後または新しい処理開始後に、古いworker結果が返る場合がある。

方針:

- job id を確認する
- 古い job id の結果は破棄する
- 破棄した結果を現在状態へ反映しない
- 破棄した結果でPreviewや保存状態を更新しない

---

## 23. 入力エラー時の状態復帰

### 23.1 TEXT読込失敗

TEXT読込失敗時:

- TEXT状態は無効
- 解析結果は無効化
- Previewはクリア
- VMD保存不可
- Busy解除
- 再読込可能
- エラー詳細に例外種別・メッセージを残す

### 23.2 音声読込失敗

音声読込失敗時:

- 音声状態は無効
- 解析用WAVは破棄
- Waveformはクリア
- Previewはクリア
- 解析結果は無効化
- VMD保存不可
- MMD用WAV出力不可
- Busy解除
- 再読込可能

### 23.3 Recent Files失敗

Recent Filesからの読込失敗時:

- 該当履歴の扱いを見直す
- 既存の有効入力を破壊しない
- 必要に応じて履歴から除外する
- エラー表示する

---

## 24. 音声変換エラー時の状態復帰

### 24.1 解析用WAV変換失敗

解析用WAV変換失敗時:

- 音声入力は保持してよい
- 解析用WAVは破棄
- Waveformはクリア
- Previewはクリア
- 解析結果は無効
- VMD保存不可
- Busy解除
- 不完全ファイル削除
- 再変換または再読込可能

### 24.2 MMD用WAV変換失敗

MMD用WAV変換失敗時:

- VMD出力結果と分けて扱う
- VMDが成功している場合は成功として残す
- MMD用WAVだけ失敗として通知する
- 不完全WAVを削除する
- 再出力可能にする

### 24.3 長時間処理中止

ユーザーが長時間処理確認で中止を選んだ場合:

- キャンセル扱いにする
- Busy解除
- 処理中ダイアログを閉じる
- 不完全ファイル削除
- Previewは必要に応じてクリア
- VMD保存不可
- 再実行可能

---

## 25. 解析エラー時の状態復帰

### 25.1 Whisper致命的エラー

Whisper致命的エラー時:

- TEXT入力は保持
- 音声入力は保持
- Waveformは保持してよい
- 同一base / parameterの旧結果を再利用できる場合は旧Preview、個別補正、履歴を確認用に復元
- 旧結果を再利用できない場合は解析結果を無効化し、Previewをクリア
- VMD保存不可
- diagnostic ERRORを保持
- Busy解除
- 再実行可能

### 25.2 Pipeline致命的エラー

Pipeline致命的エラー時:

- TEXT入力は保持
- 音声入力は保持
- Waveformは保持してよい
- 同一base / parameterの旧結果を再利用できる場合は旧Preview、個別補正、履歴を確認用に復元
- 旧結果を再利用できない場合は解析結果を無効化し、Previewをクリア
- VMD保存不可
- diagnostic ERRORを保持
- Busy解除
- 再実行可能

### 25.3 fallback使用時

fallback使用時:

- 処理継続可能ならwarning扱い
- fallback使用を詳細情報に記録する
- 必要に応じてStatusに短く表示する
- VMD保存は可能としてよい
- ただし、fallback結果が妥当であることを確認する

### 25.4 解析キャンセル

- cancel要求時点ではBusyを解除せず、current jobのterminal callbackを待つ。
- terminal callbackでBusyを解除し、Statusを「解析をキャンセルしました」へ確定する。
- inputとparameterが変わっておらず、有効な旧解析結果を再利用できる場合は、その結果、
  個別補正、Undo / Redo履歴、selectionを復元する。
- prior failureがある場合は既存ERRORを復元してcancel INFOを抑止し、VMD保存禁止を維持する。
- prior failureがない場合だけ`analysis_cancelled` INFOを生成する。
- prior failureがないcancelだけを解析failureへ変換せず、`analysis_cancelled` INFOとして扱う。
- job ID不一致、非active、既にterminalのlate / duplicate callbackはfailure、snapshot、
  確認済みfingerprint、cancel状態、GUIを変更しない。

### 25.5 解析terminal parameter mismatch

解析開始時の`morph_upper_limit`とterminal時の値が一致しない場合:

- success resultをcommitしない
- failure / cancelでも旧結果をrollbackしない
- Busyを解除する
- 再解析待ち・VMD保存不可へ移行する
- 通常success、failure rollback、cancel rollbackとして表示しない

`closing_hold_frames`、`closing_softness_frames`、`long_vowel_mode`はoutput-only設定であり、terminal
parameter mismatchの比較対象にしない。これらの変更は現在のbaseへeffective outputを再解決する。

---

## 26. 出力エラー時の状態復帰

### 26.1 VMD保存失敗

VMD保存失敗時:

- 解析結果は保持
- Previewは保持
- Waveformは保持
- 不完全VMDは削除
- 保存成功扱いにしない
- 再保存可能
- 例外種別とメッセージを詳細表示に残す

### 26.2 MMD用WAV保存失敗

MMD用WAV保存失敗時:

- VMD保存と分けて扱う
- 不完全WAVは削除
- 成功した出力があれば正確に表示する
- 失敗した出力を成功扱いしない
- 再出力可能

### 26.3 出力キャンセル

ユーザーが保存キャンセルした場合:

- errorではなくcancelled扱いでよい
- 成功扱いしない
- 既存解析結果は保持
- 再保存可能

### 26.4 診断レポート保存失敗

- 現在のtiming plan、failure、diagnostics snapshot、save-state fingerprint、WARNING確認済み状態を保持する。
- 同じworkspace状態で再保存できる。
- 一時ファイルを削除し、既存の正常なreport fileを変更しない。
- 保存dialog cancelと上書き拒否はworkspace stateを変更しない。

---

## 27. 設定読込・保存エラー

### 27.1 設定読込失敗

設定読込失敗時:

- 安全なデフォルトで起動する
- 起動不能にしない
- 必要に応じて警告する
- 破損設定を無理に採用しない

### 27.2 設定保存失敗

設定保存失敗時:

- 警告する
- アプリ本体は継続利用可能にする
- 保存できなかった設定は次回復元されないことを示す
- 解析やVMD保存の成功状態とは分けて扱う

### 27.3 Recent Files保存失敗

Recent Files保存失敗時:

- 警告または詳細情報に記録する
- 入力処理そのものを失敗扱いにしない
- 次回起動時に履歴が復元されない可能性を許容する

---

## 28. GUI / テーマ / ダイアログエラー

### 28.1 テーマ適用失敗

テーマ適用失敗時:

- `theme_apply_failed` として扱う
- 可能なら直前テーマまたは安全なテーマに戻す
- 一部UIが視認不能な状態を放置しない
- 詳細情報に例外種別とメッセージを残す

### 28.2 ダイアログ生成失敗

ダイアログ生成失敗時:

- `dialog_open_failed` として扱う
- 可能ならStatusまたは代替表示で通知する
- エラーを無言で握りつぶさない
- 親画面の状態を復帰する

### 28.3 Preview / Waveform表示失敗

Preview / Waveform表示失敗時:

- 内部解析結果が正常なら保持してよい
- 表示失敗を通知する
- GUIが不安定な場合は保存不可にする
- 必要なら該当Panelを無効表示へ戻す

---

## 29. 不完全ファイル・一時ファイルの扱い

### 29.1 基本方針

出力途中や変換途中で失敗したファイルを、成功出力として残してはならない。

### 29.2 対象

対象:

- 解析用WAV
- MMD用WAV
- VMD
- FFmpeg一時出力
- 将来追加される中間ファイル

### 29.3 方針

- 内部一時ファイルは失敗時に削除する
- 不完全なVMDは可能な限り削除する
- 不完全なMMD用WAVは可能な限り削除する
- 既存の正常ファイルを破壊しない
- 一時ファイルへ書き出し、成功後に置換する方式を優先する
- 削除失敗時は `partial_output_cleanup_failed` として記録する

---

## 30. ログ・個人情報・詳細表示

### 30.1 表示してよい情報

詳細情報に含めてよい情報:

- エラー分類
- 処理フェーズ
- Python例外種別
- エラーメッセージ
- ファイル名
- 拡張子
- ffmpeg exit code
- ffmpeg stderr要約
- traceback

### 30.2 注意して扱う情報

注意して扱う情報:

- フルパス
- ユーザー名を含むパス
- traceback全文
- ffmpeg stderr全文
- 設定ファイル内容

これらは通常表示ではなく、詳細表示またはコピー用情報として扱う。

### 30.3 表示しない情報

原則として通常表示しない情報:

- 入力テキスト全文
- 音声内容
- 著作物の内容
- 個人情報
- 長大ログ全文

### 30.4 問い合わせ用情報

問い合わせ用には、以下をコピー可能にすることが望ましい。

```text
アプリバージョン:
処理フェーズ:
エラー分類:
例外種別:
エラーメッセージ:
対象ファイル名:
traceback:
```

---

## 31. GUIエラーダイアログ要件

### 31.1 基本方針

エラーダイアログは、`docs/GUI_State_Theme_Specification.md` に従う。

### 31.2 必須要件

エラーダイアログは以下を満たす。

- Light / Dark / System テーマに追従する
- 利用者向け要約を表示する
- 詳細情報を開ける
- Python例外種別を確認できる
- エラーメッセージを確認できる
- 詳細情報をコピーできることが望ましい
- 長文tracebackでレイアウトが破綻しない
- 閉じた後に親画面の状態が破綻しない

### 31.3 長時間処理確認ダイアログ

300秒長時間処理確認ダイアログは以下を満たす。

- 処理名を表示する
- 処理フェーズを表示する
- 経過時間を表示する
- 継続ボタンを持つ
- 中止ボタンを持つ
- 現在テーマに追従する
- 中止時にキャンセル扱いへ移行する

---

## 32. テスト観点

### 32.1 入力エラー

- 存在しないTEXT
- 文字コード不正TEXT
- 5000文字超TEXT
- 存在しない音声
- 対応外拡張子
- 500MB超音声
- 15分超音声

### 32.2 音声変換エラー

- ffprobe失敗
- 音声ストリームなし
- FFmpeg未検出
- FFmpeg失敗
- FFmpeg長時間処理
- 300秒確認
- ユーザー継続
- ユーザー中止
- 解析用WAV不正
- MMD用WAV検証失敗

### 32.3 Whisperエラー

- モデル読込失敗
- 音声読込失敗
- transcribe失敗
- word情報なし
- segment情報なし
- fallback使用
- Whisper長時間処理
- Whisper中止
- 中止後のlate callback破棄

### 32.4 Pipelineエラー

- 母音列生成失敗
- timing plan生成失敗
- peak評価失敗
- observation生成失敗
- fallback可能時のwarning

### 32.5 GUIエラー

- Preview生成失敗
- Waveform描画失敗
- テーマ適用失敗
- ダイアログ生成失敗
- callback例外
- timer例外

### 32.6 出力エラー

- VMD保存権限不足
- VMDファイルロック
- MMD用WAV保存失敗
- 不完全ファイル削除
- 上書きキャンセル
- VMD成功 / WAV失敗
- VMD失敗 / WAV成功

### 32.7 設定エラー

- 設定ファイル破損
- 設定保存失敗
- Recent Files保存失敗
- テーマ保存失敗

---

## 33. 実装報告の必須項目

エラーハンドリングを追加・変更した場合、実装報告には以下を含める。

### 33.1 基本項目

- 確認したファイル
- 変更したファイル
- 追加・変更した error_code
- 追加・変更した phase
- 追加・変更した user_message
- 追加・変更した詳細情報

### 33.2 状態復帰

- エラー後に無効化する状態
- エラー後に保持する状態
- Previewの扱い
- Waveformの扱い
- VMD保存可否
- Busy解除の有無
- 一時ファイル削除の有無

### 33.3 GUI表示

- エラーダイアログの有無
- Status表示の有無
- 詳細情報表示の有無
- Python例外種別の表示有無
- エラーメッセージの表示有無
- テーマ追従確認

### 33.4 テスト

- 実行した自動テスト
- 実行した手動確認
- 未確認のエラー経路
- fallback確認の有無
- 300秒確認の扱い

---

## 34. 禁止事項

以下は禁止する。

### 34.1 例外処理

- 例外を捕捉して何も表示しない
- `pass` だけで例外を無視する
- `except Exception:` で捕捉した後、例外種別とメッセージを破棄する
- tracebackが必要な場面で完全に失う
- エラー分類なしで全て `unknown_error` にする

### 34.2 状態管理

- エラー後も成功ステータスを表示する
- 解析失敗後に古い解析結果を保存可能状態にする
- worker失敗後にBusy状態を解除しない
- identity / parameter検証なしにキャンセル後の古い結果を反映する
- 入力再読込後に古いPreviewを残す

### 34.3 出力

- 不完全VMDを成功扱いする
- 不完全MMD用WAVを成功扱いする
- 失敗時に既存正常ファイルを破壊する
- 上書き確認なしにユーザー出力を上書きする

### 34.4 GUI

- エラーダイアログをテーマ未対応で追加する
- ダイアログ生成失敗を無視する
- callback例外でアプリが不安定な状態のまま残る
- timer例外で同じエラーを無限に繰り返す

### 34.5 長時間処理

- Whisper / FFmpeg / ffprobe をGUIスレッドで直接長時間実行する
- 300秒を超えても何も表示しない
- 中止後に結果を現在状態へ反映する
- FFmpeg中止時に不完全ファイルを残す

---

## 35. 関連文書

### 35.1 `docs/Specification_Prompt_v4.md`

アプリ全体仕様を定義する。

本書は、エラーハンドリングの詳細を補完する。

### 35.2 `docs/Security_Safety_Specification.md`

安全性基準を定義する。

入力安全性、出力安全性、例外情報の扱いは本書と併せて参照する。

### 35.3 `docs/GUI_State_Theme_Specification.md`

GUI状態、再描画、テーマ追従、ダイアログ運用を定義する。

エラーダイアログや長時間処理確認ダイアログは、この文書の規則に従う。

### 35.4 `docs/MMD_Audio_WAV_Compatibility_Specification.md`

音声入力、解析用WAV、MMD用WAV互換仕様を定義する。

FFmpeg / ffprobe 系エラーは、本書の L2 として扱う。

### 35.5 `docs/VMD_Output_Specification.md`

VMD出力仕様を定義する。

VMD保存失敗、不完全ファイル、出力検証は本書の L7 として扱う。

### 35.6 `docs/repo_milestone.md`

マイルストーン履歴と現在地を記録する。

エラーハンドリングの大きな変更は必要に応じて記録する。

### 35.7 `docs/Version_Control.md`

変更履歴を記録する。

本書の更新やエラーハンドリング変更も記録対象とする。

---

## 36. 変更履歴

### 2026-08-20 / MS23-B6 cross regression同期

- `profiles.json`のload / mutation / persistence failure、active guard、preset reference guardのerror contractを追加。
- profile failure時のpartial import禁止、旧state保持、no-profile fallback、Preview / writerのfail-closedを明記。

### 2026-07-19 / MS20-B7

- analysis cancelのrequest / terminal分離、旧plan保持、ERROR優先を追加。
- late / duplicate callbackとdiagnostic report保存失敗のstate保持を固定。

### 2026-05-01 / 初版

- `MMD_AutoLipTool` のエラーハンドリング仕様を独立文書化。
- エラーを L0〜L9 のレイヤーに分類。
- エラー情報モデルとして `error_layer` / `error_code` / `phase` / `severity` / `recoverability` 等を定義。
- Whisper系エラーを分類し、致命的エラーとfallback可能な警告を分離。
- FFmpeg / ffprobe 系エラーを分類し、実行失敗と解析用WAV検証失敗を分離。
- 300秒を強制停止ではなく長時間処理確認の閾値として定義。
- 継続 / 中止確認ダイアログの方針を定義。
- FFmpeg / ffprobe は可能なら停止、Whisperは即時停止できない場合にlate callbackを破棄する方針を定義。
- 入力、音声変換、解析、出力、設定、GUI表示ごとの状態復帰を整理。
- Python例外種別とエラーメッセージを詳細情報として保持する方針を明記。
- 不完全VMD / MMD用WAV / 一時ファイルの扱いを定義。
- GUIエラーダイアログのテーマ追従、詳細表示、コピー可能情報の方針を整理。
