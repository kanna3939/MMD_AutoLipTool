# MS20-B3 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B3 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`
- 対象Block: MS20-B3
- Block名: RightPane Analysis Information
- 実施予定ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `b6f4254 Implement MS20-B2 diagnostics core foundation`
- 作成日: 2026-07-15
- 文書ステータス: Implemented / Automated and User Verification Complete
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 直接の前提契約:
  - `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B3は、B2で実装したUI非依存の `OutputDiagnosticsSnapshot` を、現在の `UiState` とVMD writer parameterから組み立て、RightPane Infoタブへ表示するBlockである。B3ではInfoの入力・解析・生成・保存可否セクションだけを実装し、再生位置、現在frame、現在母音はB4、Warning表示と保存policyはB5、failure保持はB5、report出力はB6へ残す。

### 1.1 実装前チェック結果

- 2026-07-15に現行コード、テスト、仕様、B1 / B2契約との照合を実施した。
- P1は検出されなかった。
- P2として、`clear_info()` のB3後契約とanalysis error / cancel時のInfo回帰不足を検出し、本書へ反映した。
- P3として、parameter変更時のPreview二重更新につながる曖昧な手順を検出し、`sync_ui_state()` への置換として明確化した。
- 2026-07-16の再チェックでは、指定限定回帰56件がpass表示、failure / error表示なし、process exit code 1だった。MS14-B6 closeout単独3件とRightPane単独2件はpass表示・終了コード0だった。
- production code、GUI、テストコード、依存関係、packageは変更していない。

### 1.2 実施結果

- 2026-07-16に、wx非依存GUI adapter、RightPane Infoの縦scroll表示、MainFrame同期を実装した。
- `OutputDiagnosticsSnapshot` から入力・解析・生成・保存可否の4セクションを固定順で表示し、解析中は保存済みplanを表示専用snapshotから一時的にmaskするようにした。
- `RightPane` constructorと `clear_info()` は空表示を維持し、初期4セクションはMainFrameの初回 `sync_ui_state()` から設定する契約に統一した。
- parameter変更handlerの直接Preview更新を `sync_ui_state()` へ置換し、PreviewとInfoを1回の同期で更新するようにした。
- B3 adapter単体12件、B3 RightPaneとMS16 RightPane回帰16件、workspace reset回帰8件はpass表示・終了コード0だった。
- 指定限定回帰56件と全体406件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- `tests/test_wx_ms15_b5_state_theme.py` 単独では4件pass、1件が `wx.App` 未生成でfailure、終了コード1だった。同じ5件は全体実行内ではすべてpassしており、B3表示変更ではなく既存テストの単独実行時初期化依存として記録する。
- GUI同期を通る既存success fixtureをproduction契約の `VowelTimingPlan` へ補正した。実装中に同じ不整合を検出した `tests/test_ms19_b8_workspace_reset.py` も追加で補正したが、assertionの削除、skip、期待値緩和は行っていない。
- 2026-07-16にユーザー手動GUI確認10項目がすべて通過し、問題なしと報告された。
- ユーザー確認後の微修正として、「再解析が必要」の文字列だけをボールドかつtheme別のオレンジ系文字色にした。通常状態では強調用labelを非表示にし、theme変更後もattention色を再適用する。
- 同日、微修正後のユーザーチェックも通過し、問題なしと報告された。
- 実MMD確認、build、SmokeLaunch、package確認は実施していない。
- Warning詳細、failure保持、severity連動save policy、live playback context、report出力は未実装であり、後続Blockの責務を維持した。

## 2. 背景

MS20-B2では、次のcore契約が `b6f4254` で実装された。

- `DiagnosticSnapshotInput` と不変なsummary / item / snapshot DTO
- `build_output_diagnostics_snapshot()`
- canonical writer inputとSHA-256 save-state fingerprint
- `resolve_vmd_writer_timing_plan()` による保存直前duration正規化の共有
- 12 diagnostic codeの順序、抑制、severity、fail-closed契約
- core単体テスト12件と既存pipeline / wx回帰

一方、現行GUIには次の未接続が残る。

- `src/gui_wx/right_pane.py` のInfoタブは、単一の `wx.StaticText` に将来実装用placeholderを表示している。
- `MainFrame.sync_ui_state()` はaction、status、Preview、選択イベントを同期するが、output diagnosticsを生成しない。
- `UiState`、`current_timing_plan`、解析用WAV、closing parameterから `DiagnosticSnapshotInput` を組み立てるGUI adapterが存在しない。
- Infoタブはscroll領域ではなく、長いpathや複数セクションでRightPane全体を押し広げる可能性がある。
- 現行テストの一部は、成功済みtiming planを `MagicMock` / `SimpleNamespace` で代用している。B3でsnapshotを生成するcallback回帰では、production契約である `VowelTimingPlan` fixtureへ置換する必要がある。

B3では、RightPaneやMainFrameが `UiState` から独自にanchor数、event数、fallback、保存可否を再計算しないようにする。GUI層は現在状態をB2入力DTOへ写像し、表示はB2 snapshotのsummaryだけを参照する。

## 3. 目的

- `UiState` と現在のwriter parameterからB2 snapshotを生成する、wx非依存のGUI adapterを追加する。
- RightPane Infoのplaceholderを、入力・解析・生成・保存可否の4セクション表示へ置き換える。
- 初期、入力済み、未解析、再解析待ち、解析済み、保存可、保存不可を区別する。
- 解析開始時に、旧解析結果を保存可能なInfoとして表示し続けない。
- 長いpathと複数行情報を縦scrollで閲覧でき、RightPaneの横幅を押し広げないようにする。
- input変更、parameter変更、解析開始、解析成功、解析失敗、cancel、workspace resetの既存同期点からInfoを再生成する。
- B4からB7が、表示文字列を読み戻さず同じsnapshot契約へ接続できる状態を作る。

## 4. In Scope

- `UiState` から `DiagnosticSnapshotInput` を組み立てるGUI adapter
- source audio path / effective WAV pathの既存状態からの選択
- `current_timing_plan` のwriter直前正規化と `DiagnosticTimingPlanInput` へのtuple copy
- `VmdWriterParameters` への現行VMD model name、closing parameterの写像
- B3では `failure=None`、`analysis_cancelled=False` とするsnapshot生成
- 解析中だけ旧planをInfo用snapshotから除外する一時的な表示入力
- RightPane Infoの4セクション表示
- Infoタブの縦scroll
- `MainFrame.sync_ui_state()` からのInfo更新
- parameter変更とsettings適用後のInfo再同期
- 初期／TEXTあり／voice_only／未解析／再解析待ち／解析済み／保存可否の表示テスト
- 既存callbackテストのtiming plan fixtureをproduction型へ補正
- B3実施結果に限定した計画・routing文書の更新

## 5. Out of Scope

- `UiState` へのsnapshot永続保持field追加
- `UiState.current_diagnostic_failure` の追加
- analysis errorの `DiagnosticFailureInput` 変換・保持
- Warningタブのseverity別表示
- `ERROR` によるVMD保存ボタン／メニューpolicy変更
- `WARNING` 保存確認ダイアログ、確認済みfingerprint保持
- 再生位置、現在frame、現在母音のlive更新
- 再生timerごとのsnapshot再生成
- report formatting、report保存メニュー、ファイル出力
- 選択イベント、preset、model profileタブの本実装
- `VowelTimingPlan`、`OutputDiagnosticsSnapshot`、B2 fingerprint schemaの変更
- pipeline timing、Preview shape、VMD writer出力の変更
- 固定モーフ `あ / い / う / え / お` の変更
- README、配布用readme、package、release、tag、push
- 新規依存関係、外部通信、外部クラウドASR、他ASR backend、Whisper自動download
- Qt / PySide6の復活

## 6. 前提条件

- 作業開始時に `feature/MS20-implementation`、HEAD、未コミット差分を再確認する。
- 未コミット差分がある場合はユーザー所有変更として保護する。
- B1の診断契約とB2の公開API・12 code・fingerprint schemaを変更しない。
- B2実装コミットは `b6f4254` であり、B3はその公開APIを利用する。
- B2検証では、B2単体12件、非正duration回帰1件、限定回帰24件がpass表示・終了コード0、全体380件がpass表示・既知wx終了処理由来の終了コード1であった。
- 現行 `UiState.current_timing_plan` のproduction値は `VowelTimingPlan` である。B3のsnapshot生成を通るテストfixtureも同じ契約へ合わせる。
- `MainFrame.update_action_states()` が `UiState.refresh_input_mode()` を先に実行する現行順序を維持し、adapterは `UiState` を変更しない。
- VMD model nameはWhisper modelではなく、現行pipeline / writerの既定値 `AutoLipTool` とする。
- B3 snapshotは表示のため都度生成し、B5以前はworkspace状態として保持しない。

## 7. 対象ファイル

### 7.1 主変更

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/gui_wx/output_diagnostics_adapter.py` | `UiState` からB2 snapshotを生成するadapterと、Info表示用の決定的formatter |
| `src/gui_wx/right_pane.py` | Infoタブを縦scroll化し、snapshot表示helper、再wrap / virtual size更新、再解析注意表示専用labelを追加 |
| `src/gui_wx/main_frame.py` | `sync_ui_state()`、解析開始／終了、parameter変更、settings適用をInfo snapshot更新へ接続し、theme変更後に注意表示色を再適用 |
| `src/gui_wx/theme.py` | light / dark用の再解析注意表示色 `attention_text` を追加 |

### 7.2 テスト

| ファイル | 変更内容 |
| --- | --- |
| 新規 `tests/test_ms20_b3_output_diagnostics_adapter.py` | UiState写像、path優先順位、timing plan正規化、formatterのwx非依存単体テスト |
| 新規 `tests/test_ms20_b3_right_pane_info.py` | MainFrame / RightPaneの初期、入力済み、解析済み、解析中、reset、scroll、再解析時だけのbold / attention色とtheme再適用テスト |
| `tests/test_wx_ms16_b3_right_pane.py` | RightPane単体構築直後と `clear_info()` 後の空表示へ期待値を更新し、既存5タブと他helperの回帰を維持 |
| `tests/test_wx_ms14_b4_analysis.py` | analysis success fixtureを実在 `VowelTimingPlan` 契約へ補正 |
| `tests/test_wx_ms14_b6_closeout.py` | analysis開始、soft cancel、timeout、late callbackの既存回帰を再実行。fixture変更は予定しない |
| `tests/test_ms19_b4_voice_only_gui_state.py` | voice_only analysis success callback fixtureを実在 `VowelTimingPlan` 契約へ補正 |
| `tests/test_ms19_b8_workspace_reset.py` | MainFrame同期を通るworkspace fixtureを実在 `VowelTimingPlan` 契約へ補正 |

既存fixtureの補正は、B3で新たに参照する `vowels / timeline / anchors / source / warning / observations` を実値で表すために限る。assertionの削除、skip追加、期待値緩和は行わない。

### 7.3 関連確認のみ

- `src/gui_wx/ui_state.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/parameter_panel.py`
- `src/core/output_diagnostics.py`
- `src/core/pipeline.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_wx_ms15_b5_state_theme.py`

`UiState` と `AnalysisWorkerResult` のfield追加は予定しない。pre-implementation checkで現行codeから不可避と判明した場合だけ、B3責務との整合を再判定する。

### 7.4 計画・実施結果の文書

- 新規 `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`
- B2完了状態とB3 routingに限定した `docs/MS20_and_Beyond_Index.md`
- 次作業同期に限定した `docs/MS20_and_Beyond_Roadmap.md`
- B2 / B3状態同期に限定した `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- B2実施結果の記録に限定した `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`

B3実装中にREADME、配布用readme、`docs/repo_milestone.md`、`docs/Version_Control.md`、正本仕様を変更しない。MS20全体の仕様・ユーザー文書同期はB7が所有する。

## 8. 実装方針

### 8.1 GUI adapter境界

新規 `src/gui_wx/output_diagnostics_adapter.py` はwx widgetをimportせず、次の公開関数を持つ。

```text
build_output_diagnostics_snapshot_from_ui_state(
    state: UiState,
    *,
    vmd_model_name: str = "AutoLipTool",
    closing_hold_frames: int = 0,
    closing_softness_frames: int = 0,
    analysis_in_progress: bool = False,
) -> OutputDiagnosticsSnapshot

format_output_diagnostics_info(
    snapshot: OutputDiagnosticsSnapshot,
    *,
    analysis_in_progress: bool = False,
) -> str
```

adapterは次だけをimportしてよい。

- Python標準ライブラリの `pathlib` とtypingに必要な最小要素
- `gui_wx.ui_state.UiState`
- `src.core` からB2公開DTO / builder / timing helper
- production plan型のruntime検証に必要な `VowelTimingPlan`

adapterはwx、RightPane、MainFrame、AppController、filesystem I/Oをimportしない。`exists()`、`resolve()`、`stat()`、file read / writeを行わない。

### 8.2 UiStateからsnapshot inputへの写像

| B2 input | B3参照元 / 規則 |
| --- | --- |
| `input_mode` | `state.input_mode`。adapter内で `refresh_input_mode()` を呼ばない |
| `text_path` | `Path(state.selected_text_path)`。未設定は `None` |
| `text_content_present` | `bool(state.selected_text_content)` |
| `source_audio_path` | `state.selected_audio_input.source_path` を優先し、なければ `state.selected_wav_path` |
| `effective_wav_path` | `state.selected_analysis_wav.analysis_wav_path` を優先し、なければ `state.selected_wav_path` |
| `analysis_text_present` | `bool(state.analysis_text_content or state.transcription_text)` |
| analysis flags | 通常は `state.analysis_result_valid` / `state.analysis_pending_rebuild` |
| timing plan | `state.current_timing_plan` をwriter正規化後、`DiagnosticTimingPlanInput.from_timing_plan()` でcopy |
| existing save ready | 通常は `state.vmd_save_ready` |
| writer parameters | MainFrameのclosing値と `AutoLipTool` |
| failure | B3では常に `None` |
| cancelled | B3では常に `False` |

pathはB2 builderがWindows規則で正規化する。B3 adapterはpath文字列を表示用に独自変換せず、snapshotの `InputDiagnosticsSummary` をInfoへ渡す。

### 8.3 timing planのwriter境界

- `state.current_timing_plan` が `None` なら `DiagnosticSnapshotInput.timing_plan=None` とする。
- planがある場合はproduction型 `VowelTimingPlan` であることを確認する。duck-typed `MagicMock` や任意の `SimpleNamespace` を通常値として受け入れない。
- timelineがすべて正durationなら、`resolve_vmd_writer_timing_plan()` は同じplanを返すため、その結果をtuple copyする。
- 非正durationを含む場合は、`state.selected_wav_analysis.speech_start_sec / speech_end_sec` を使ってB2 helperを呼ぶ。
- 非正durationなのに解析区間がない状態は、writer実入力を正しく再現できない構造不整合として `ValueError` とする。推測した音声区間やtimeline端点を代用しない。
- adapterとformatterはplan、timeline、observations、UiStateを変更しない。

### 8.4 解析中の一時snapshot

再解析開始時に現行 `UiState` の有効planを即時破棄すると、cancel時の現行再利用契約まで変更する。一方、そのplanをそのままInfoへ出すと、B1の「旧解析snapshotを保存可能として残さない」契約に反する。

B3では、workspace状態を変更せず、`analysis_in_progress=True` の呼出しだけ次の入力へ一時的にmaskする。

```text
timing_plan = None
analysis_result_valid = False
analysis_pending_rebuild = state.analysis_result_valid or state.analysis_pending_rebuild
existing_vmd_save_ready = False
```

- 初回解析中はInfoの解析状態を「解析中」、保存可否を「不可」とする。
- 有効planからの再解析中も「解析中」「保存不可」とし、旧event数や旧最大frameを表示しない。
- この一時snapshotとfingerprintはUiStateへ保存しない。
- success時は新planから通常snapshotを生成する。
- error時は既存 `invalidate_analysis()` 後の再解析待ちsnapshotを生成する。failure詳細保持はB5まで行わない。
- cancel時は現行UiStateを再評価し、旧planが現行契約で有効なら通常表示へ戻す。

MainFrameは表示専用の `_analysis_info_in_progress` boolを持ち、解析worker開始直前にtrue、`_cleanup_analysis_job()` でfalseにする。job id不一致のlate callbackは現行どおりreturnし、このflag、Info、UiStateを更新しない。

### 8.5 Info表示契約

Infoは次の固定順で表示する。値はsnapshot summaryからのみ取得し、UiStateやtiming planをRightPaneで再参照しない。

```text
[入力]
入力モード
TEXT
入力音声
解析用WAV
TEXT内容
解析テキスト

[解析]
状態
タイミング元
アンカー数
母音イベント数
最大フレーム
タイミング警告
音量fallback数

[生成]
VMDモデル名
開口保持
閉口スムース
診断schema

[保存可否]
VMD保存
保存禁止診断数
要確認警告数
```

表示値は次で固定する。

| 値 | 表示 |
| --- | --- |
| `text_audio` | `TEXT + 音声` |
| `voice_only` | `音声のみ` |
| path `None` | `(未設定)` |
| timing source `None` | `(未解析)` |
| max frame `None` | `(未算出)` |
| bool true / false | `あり` / `なし` |
| analysis in progress | `解析中` |
| pending rebuild | `再解析が必要` |
| validかつeventあり | `解析済み` |
| その他 | `未解析` |
| save allowed true / false | `可能` / `不可` |
| closing parameter | `<n> フレーム` |
| diagnostic count | `<n> 件` |

Infoではdiagnostic itemのsummary / detail、raw warning本文、exception messageを列挙しない。Warningの詳細はB5が同じsnapshotから表示する。save-state fingerprint自体もB3 Infoへ表示しない。

### 8.6 RightPaneのscroll / wrap

- Info tabのcontainerを `wx.ScrolledWindow` へ置き換える。
- `wx.VSCROLL` と `SetScrollRate(0, 10)` を使用し、横scrollは追加しない。
- 既存 `st_info`、`panel_info`、`set_info_text()` を互換helperとして保持する。
- `RightPane` 単体構築直後と `clear_info()` 後の `st_info` は空文字列とする。RightPane単体で初期snapshotや固定4セクション文言を生成しない。
- アプリ起動時の4セクション初期表示は、`MainFrame._init_ui()` 末尾の初回 `sync_ui_state()` が初期UiStateから生成したsnapshotを設定する。
- 新規 `set_info_snapshot(snapshot, *, analysis_in_progress=False)` がformatter結果を表示し、「再解析が必要」の状態だけを専用labelへ分離する。
- `set_info_text()` とsize eventは、現在のInfo client幅から余白を引いた正値で `Wrap()` を行う。
- label更新後はInfo sizer / panelの `Layout()` と `FitInside()` を行い、virtual heightを再計算する。
- RightPane自身へcontent由来の最小横幅を設定しない。center sizerの既存比率 `1 : 3 : 1` を維持する。
- Warning、選択イベント、preset、model profileのtab数、順序、label、helperを変更しない。
- `wx.ScrolledWindow` は `wx.Panel` 派生であり、既存 `ThemeManager` の再帰適用を利用する。初回実装ではThemePaletteを追加しなかったが、ユーザー確認後の明示依頼により、再解析注意表示専用の `attention_text` をlight / dark paletteへ追加した。

### 8.7 MainFrame更新点

`MainFrame.sync_ui_state()` は、既存の `update_action_states()` によるinput mode更新後、次を行う。

1. 現在のclosing parameterを取得する。
2. `_analysis_info_in_progress` をadapterへ渡してsnapshotを生成する。
3. 同じflagとsnapshotを `right_pane.set_info_snapshot()` へ渡す。
4. 既存Preview、選択イベント、Refresh処理を継続する。

追加同期点:

- `_run_analysis()`: worker開始前に `_analysis_info_in_progress=True` とし、Busy同期で旧planをmaskする。
- `_cleanup_analysis_job()`: flagをfalseへ戻す。success / error / cancelの既存syncで現在状態を再表示する。
- `_on_param_changed()`: 既存の直接 `_update_preview_display()` 呼出しを `sync_ui_state()` に置き換え、Preview、generation、saveabilityを一度の同期で更新する。
- `apply_settings()`: parameter設定とevent bindの完了後に `sync_ui_state()` を呼び、起動時のgeneration表示を復元値へ合わせる。
- workspace reset: 既存 `reset_workspace()` と `sync_ui_state()` を利用し、Infoを初期snapshotへ戻す。`reset_workspace_display()` に固定文言を重複実装しない。

input選択、audio worker成功／失敗、transcription適用／復元、analysis成功／失敗、playback終了は既に `sync_ui_state()` を呼ぶ経路を維持する。B3では再生timer callbackごとのInfo更新を追加しない。

### 8.8 compatibility

- `UiState` のfield・property・reset契約を変更しない。
- `AnalysisWorkerResult` とcallback signatureを変更しない。
- `UiState.vmd_save_ready` をB3で置換しない。
- VMD保存ボタン／メニューの有効条件をB3診断severityへ接続しない。
- RightPaneの5タブ構成とInfo以外の既存view helperを維持する。
- B2 core snapshot、fingerprint、diagnostic orderを変更しない。
- Preview、waveform、selection、playback、VMD生成結果を変更しない。

## 9. 詳細ステップ

### Step 1: adapterのUiState写像を実装する

- optional pathの取得helperを実装する。
- source audio / effective WAVの優先順位を固定する。
- B2 `VmdWriterParameters` と `DiagnosticSnapshotInput` を構築する。
- B3ではfailure / cancelledを接続しない。
- 同じUiState内容とparameterから同じsnapshotを得ることを単体テストする。

### Step 2: timing plan境界を接続する

- `VowelTimingPlan` のruntime型を確認する。
- 正duration planをcopyする。
- 非正duration planをB2 helperで補完し、observationsが現行どおり `None` になることを確認する。
- speech interval不足時に推測せず `ValueError` とする。
- adapter後のfingerprintがB2 writer境界と一致することをテストする。

### Step 3: 解析中snapshotを実装する

- adapterの `analysis_in_progress` maskを実装する。
- MainFrameへ表示専用flagを追加する。
- 解析開始、success、error、cancel、late callbackでflag更新順を固定する。
- 解析開始時に旧event数と保存可能表示が残らないことをテストする。
- analysis error後に再解析待ち・保存不可となり、旧event数と旧最大frameが残らないことをテストする。
- cancel完了後にflagが解除され、現行契約で再利用可能な旧planのInfoへ戻ることをテストする。

### Step 4: Info formatterを実装する

- 固定4セクション、固定field順、固定empty表現を実装する。
- formatterがsnapshot以外のUiState / planを参照しないようにする。
- path、count、bool、analysis state、saveabilityの表示を単体テストする。
- Warning item本文とfingerprintをInfoへ含めないことを確認する。

### Step 5: RightPane Infoをscroll化する

- Info panelだけを `wx.ScrolledWindow` へ変更する。
- `st_info` と既存helper互換を維持する。
- constructorと `clear_info()` は空表示とし、初期4セクション生成をRightPaneへ重複実装しない。
- snapshot helper、wrap、Layout、FitInsideを追加する。
- 長いpathでvirtual heightが増え、5タブ構成と横レイアウトが維持されることをテストする。

### Step 6: MainFrame同期へ接続する

- `sync_ui_state()` にsnapshot生成とInfo反映を追加する。
- parameter変更handlerの直接Preview更新を削除し、`sync_ui_state()` へ置き換える。
- settings適用完了後にInfoを再同期する。
- input mode更新後にadapterを呼ぶ順序をテストする。

### Step 7: 既存fixtureをproduction契約へ補正する

- analysis success callbackを直接呼ぶ既存テストだけを対象にする。
- `VowelTimingPlan`、`SpeechTimingAnchor`、`VowelTimelinePoint` を使う局所fixtureへ置き換える。
- 既存assertionと回帰意図を維持する。

### Step 8: 対象回帰を実行する

- adapter単体を最初に実行する。
- RightPane B3 testとMS16 RightPane回帰を実行する。
- analysis / cancel / timeout / late callback / state / voice_only / resetの限定回帰を実行する。
- B2 core testを再実行する。
- 最後に全testsを実行し、pass表示とprocess exit codeを分けて記録する。

### Step 9: B3実施結果を記録する

- 実際の公開adapter API、Info field、変更ファイル、テスト結果を本書へ記録する。
- 計画との差分と未検証事項を記録する。
- B4へ、Info scroll基盤、snapshot表示helper、live contextをfingerprintから除外する契約を引き継ぐ。
- B5のWarning / failure / save policyを先行実装しない。

## 10. 状態遷移 / データ契約

### 10.1 B3データフロー

```text
UiState + current ParameterPanel values
  ↓ GUI adapter（状態変更なし）
DiagnosticSnapshotInput
  ↓ B2 core builder
OutputDiagnosticsSnapshot
  ├─ MainFrame action stateには未接続（B5）
  └─ B3 formatter
       ↓
     RightPane Info StaticText / ScrolledWindow
```

RightPaneのlabelは派生表示であり、snapshotの正本ではない。labelをparseしてsnapshot、timing plan、saveabilityを復元しない。

### 10.2 状態別期待値

| 状態 | Info解析状態 | event / max frame | VMD保存表示 |
| --- | --- | --- | --- |
| 初期 | 未解析 | 0 / 未算出 | 不可 |
| TEXTのみ | 未解析 | 0 / 未算出 | 不可 |
| 音声のみ読込 | 未解析 | 0 / 未算出 | 不可 |
| TEXT + 音声読込 | 未解析 | 0 / 未算出 | 不可 |
| input / morph parameter変更後 | 再解析が必要 | 0 / 未算出 | 不可 |
| 解析中 | 解析中 | 0 / 未算出 | 不可 |
| text_audio解析成功 | 解析済み | snapshot値 | snapshot値 |
| voice_only解析成功 | 解析済み | snapshot値 | snapshot値 |
| fallbackあり解析成功 | 解析済み | snapshot値 | 可能。要確認警告数を表示 |
| 解析失敗 | 再解析が必要 | 0 / 未算出 | 不可 |
| cancel | 現在UiStateを再評価 | 現在snapshot値 | 現在snapshot値 |
| workspace reset | 未解析 | 0 / 未算出 | 不可 |
| late callback | 変更なし | 変更なし | 変更なし |
| 再生位置更新 | 変更なし | 変更なし | 変更なし |

closing parameter変更はgeneration表示を即時更新する。morph upper limit、closing hold、closing softnessは現行どおり同じparameter変更handlerを通り、解析済みplanをinvalidateするため、Infoは再解析待ちへ更新する。このB3ではparameter別の無効化policyを変更しない。

### 10.3 B3のsnapshot ownership

- B3はsnapshotを `UiState`、MainFrame、RightPaneへ永続保持しない。
- `sync_ui_state()` ごとに現在値から再生成する。
- RightPaneはformatted labelだけを保持する。
- B5がfailureと現在snapshotのworkspace内保持を追加するまでは、analysis error詳細はダイアログ表示後に残らない現行契約を維持する。
- B3の一時解析中snapshotはWARNING確認やreportへ利用しない。

### 10.4 B4以降への引き継ぎ

- B4はB3 Info scroll基盤を利用し、再生位置、frame、現在母音だけを軽量更新する。
- B4 live contextはsnapshot fingerprintを変更しない。
- B5はB3 adapterを拡張し、retained failure、現在snapshot、Warning、save policyを接続する。
- B6 reportはB2 snapshotから生成し、B3 formatterやRightPane labelを読み戻さない。
- B7はinput / parameter / reset / late callbackのsnapshot破棄と表示整合を横断回帰する。

## 11. テスト方針

### 11.1 adapter単体テスト

`tests/test_ms20_b3_output_diagnostics_adapter.py` で少なくとも次を検証する。

- import時にwx widget、RightPane、MainFrameを必要としない。
- 初期UiStateから未解析・保存不可snapshotを生成する。
- `selected_audio_input.source_path` がsource audio pathとして優先される。
- `selected_analysis_wav.analysis_wav_path` がeffective WAV pathとして優先される。
- fallbackとして `selected_wav_path` を使用する。
- text_audio / voice_onlyのmodeとtext presenceを正しく写像する。
- closing hold / softnessとVMD model nameをgeneration summaryへ渡す。
- 正durationの `VowelTimingPlan` をtuple DTOへcopyする。
- 非正durationをB2 helperで補完し、writer実入力と同じfingerprintを得る。
- 非正durationでspeech intervalがない場合は `ValueError` となる。
- `analysis_in_progress=True` で旧plan、旧event数、保存可をmaskする。
- adapterがUiState、plan、timeline、observationsを変更しない。
- formatterの4セクション、field順、empty表現、mode表示を固定する。
- formatterがdiagnostic summary / detail、fingerprint、raw warning文を表示しない。

### 11.2 RightPane / MainFrameテスト

`tests/test_ms20_b3_right_pane_info.py` で少なくとも次を検証する。

- Info tabが `wx.ScrolledWindow` であり、5タブの順序が変わらない。
- RightPane単体構築直後と `clear_info()` 後は空表示であり、snapshotを独自生成しない。
- MainFrame初回同期後の初期表示に4セクションがあり、将来placeholderがない。
- TEXTあり入力済み・未解析を表示する。
- voice_only解析済みでinput mode、timing source、anchor数、event数、最大frameを表示する。
- fallback snapshotで要確認警告数を表示するが、Warning tab内容を変更しない。
- analysis開始で旧解析値と保存可表示を残さない。
- successで新snapshotを表示する。
- analysis errorで再解析待ち・保存不可となり、旧event数と旧最大frameを残さない。
- cancel完了で解析中表示を解除し、再利用可能な旧planの通常snapshotへ戻る。
- input変更 / transcription edit / parameter変更で再解析待ちへ更新する。
- settings適用後にclosing parameter表示が更新される。
- workspace resetで初期Infoへ戻る。
- job id不一致のlate callbackでInfoが変化しない。
- playback positionだけの変更でInfoのsnapshot部分が変化しない。
- 長いpathでvertical virtual sizeが更新され、RightPaneの横比率を変更しない。

### 11.3 既存回帰

- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_wx_ms14_b6_closeout.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`

### 11.4 実行順

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b3_output_diagnostics_adapter.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b3_right_pane_info.py tests/test_wx_ms16_b3_right_pane.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_wx_ms14_b2_state.py tests/test_wx_ms14_b4_analysis.py tests/test_wx_ms14_b5_export.py tests/test_wx_ms14_b6_closeout.py tests/test_ms19_b4_voice_only_gui_state.py tests/test_ms19_b5_transcription_edit_state.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py
.\.venv\Scripts\python.exe -m pytest tests
```

各コマンドは一つずつ実行し、完了を待ってから次へ進む。pass表示とprocess exit codeを別々に報告する。全体テストの既知wx終了コード1を自動的に成功扱いせず、pass件数、failure / error表示、終了コードを分けて記録する。

### 11.5 手動GUI確認

B3実装後に次を確認する。

1. 起動直後のInfoに4セクションが表示される。
2. TEXTと音声を読み込むと、長いpathが横幅を押し広げずwrap / scrollできる。
3. text_audio解析成功後にsource、anchor数、event数、最大frame、保存可否が更新される。
4. voice_only解析成功後に入力モードと解析テキスト有無が正しい。
5. parameter変更でgeneration値と再解析状態が更新される。
6. 再解析中は旧event数と「VMD保存: 可能」が残らない。
7. 解析失敗後は再解析待ち・保存不可となり、旧解析値が残らない。
8. 再解析cancel後は「解析中」が解除され、再利用可能な旧解析結果へ戻る。
9. workspace resetで前作業のInfoが残らない。
10. Warning、選択イベント、preset、model profileタブが従来どおり操作できる。

手動GUI確認を実施していない場合は未実施と報告する。B3では実MMD確認、build、SmokeLaunchを実施しない。

### 11.6 文書・差分検証

```powershell
git diff --check
```

実装後はstaged / unstaged / untrackedを確認し、B3範囲外のWarning、save policy、report、core schema、設定永続化、package変更がないことを監査する。

## 12. 受け入れ条件

- `src/gui_wx/output_diagnostics_adapter.py` が追加されている。
- adapterがUiStateを変更せず、B2公開APIからsnapshotを生成する。
- source audio / effective WAV / timing plan / writer parameterの写像が本計画どおりである。
- B3 snapshot生成にwx widget、filesystem I/O、networkを必要としない。
- Infoに入力、解析、生成、保存可否の4セクションが固定順で表示される。
- RightPane単体構築直後と `clear_info()` 後は空表示で、初期4セクションはMainFrameの初回同期から設定される。
- initial / text_audio / voice_only、未解析 / 解析中 / 再解析待ち / 解析済み、保存可 / 不可が区別される。
- analysis開始時に旧event数、旧最大frame、旧保存可表示が残らない。
- analysis success、input変更、parameter変更、analysis error、cancel、resetで現在状態へ更新される。
- late callbackとplayback positionだけの変更でInfo snapshot部分を上書きしない。
- 長いpathを縦scrollで閲覧でき、RightPaneの横幅をcontentに合わせて拡張しない。
- RightPaneの5タブ、Info以外のhelper、theme追従が維持される。
- RightPaneがUiStateやtiming planから診断値を再計算しない。
- 表示文字列からsnapshot、timing plan、saveabilityを復元しない。
- `UiState`、`AnalysisWorkerResult`、B2 core DTO / fingerprint schemaを変更していない。
- Warning、save policy、failure保持、live playback、reportを先行実装していない。
- B3新規test、指定回帰、全testsのpass表示とprocess exit codeが記録されている。
- 新規依存関係、network、build、package変更がない。
- B4開始前に解消が必要な未記名の判断事項が残っていない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| RightPaneがUiStateを直接読み、core snapshotと別の判定を持つ | UiState写像をadapterへ集約し、RightPaneはsnapshot summaryだけをformatする |
| 有効planの再解析中に旧保存可能表示が残る | 表示専用 `analysis_in_progress` maskでplanとsaveabilityを一時的に除外する |
| 解析開始時にplanを破棄し、cancel時の現行契約を変える | UiStateは変更せず一時snapshotだけをmaskする |
| 非正durationのfingerprintがwriter実入力とずれる | B2 `resolve_vmd_writer_timing_plan()` とspeech intervalを共用する |
| speech interval不足をtimeline端点で推測する | 構造不整合として `ValueError` とし、推測値を使わない |
| 既存testのMagicMock planをproduction契約と誤認する | syncを通るsuccess fixtureだけ実在 `VowelTimingPlan` へ補正する |
| 長いpathでcenter layoutが横へ拡張する | 縦 `wx.ScrolledWindow`、固定wrap幅、FitInside、既存sizer比率を使う |
| label更新後にscroll範囲が古い | set / sizeごとにLayoutとFitInsideを実行する |
| `clear_info()` が旧placeholderを復元する、またはRightPaneが初期snapshotを独自生成する | constructorと `clear_info()` は空表示に限定し、初期4セクションはMainFrame同期だけが設定する |
| B3 formatterをB6 reportへ流用し契約が混ざる | B3は画面表示専用。B6はsnapshotから独立report formatterを実装する |
| Warning詳細をInfoへ先行実装する | B3は診断件数だけを表示し、item本文はB5へ残す |
| snapshotをMainFrameやRightPaneへ保持しB5 ownershipと衝突する | B3はsyncごとに生成し、label以外を永続保持しない |
| parameter変更後にInfoだけ古い | `_on_param_changed()` を `sync_ui_state()` へ接続する |
| parameter変更時にPreviewを二重更新する | 直接 `_update_preview_display()` を削除し、`sync_ui_state()` に置き換える |
| settings復元値が初期Infoへ反映されない | `apply_settings()` 完了後に再同期する |
| theme用の独自色が増え不整合になる | 標準Panel / StaticTextと既存ThemeManager再帰適用を使用する |
| 全体testの終了コード1を新規failureと混同する | pass表示、failure / error、終了コードを分けて記録する |

## 14. Codex 実装時の注意

```text
- コマンドは必ず一つずつ実行し、並列・パイプ・連結実行をしない。
- 実装前にbranch、HEAD、worktree、B2公開API、RightPane、MainFrame同期点を再確認する。
- 未コミット差分はユーザー所有変更として保護する。
- B1 / B2のdiagnostic code、severity、fingerprint schemaを変更しない。
- UiState、timing plan、observationsをadapter内で変更しない。
- path.exists / resolve / stat、file read / writeをadapterへ追加しない。
- RightPaneでanchor、event、fallback、saveabilityを再計算しない。
- RightPane constructor / `clear_info()` で初期snapshotや固定4セクション文言を生成しない。
- labelや表示文言をsnapshotの正本として読み戻さない。
- B3 snapshotをUiState、MainFrame、RightPaneへ永続保持しない。
- 解析中maskをWARNING確認やreportへ使用しない。
- playback timerごとのsnapshot再生成を追加しない。
- parameter変更handlerで直接Preview更新と `sync_ui_state()` を重ねて呼ばない。
- Warning、failure保持、VMD保存確認、reportを先行実装しない。
- Info以外のRightPaneタブ、Preview、VMD writer、固定モーフを変更しない。
- 新規依存関係、外部通信、Whisper download、Qt / PySide6を追加しない。
- 既存テストを削除・skip・期待値緩和してpassさせない。
- test fixture補正はproduction `VowelTimingPlan` 契約への置換に限定する。
- 実施していないGUI、MMD、build、package確認を通過と報告しない。
- pass表示とprocess exit codeを分けて報告する。
```

B3完了報告は次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
```
