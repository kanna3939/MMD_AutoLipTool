# MS20-B5 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B5 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md`
- 対象Block: MS20-B5
- Block名: Warning Panel / VMD Save Policy
- 実施予定ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `14c8d3f Implement MS20-B4 live playback context`
- 作成日: 2026-07-16
- 文書ステータス: Complete / Automated Verification Complete / Manual GUI Check Complete
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 直接の前提契約:
  - `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B4_Implementation_Plan.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B5は、B2で実装した `OutputDiagnosticsSnapshot` をRightPane Warningタブ、VMD保存UI、VMD保存controller guardへ接続するBlockである。B5は `INFO / WARNING / ERROR` の全診断を表示し、`ERROR` が1件でもある場合はVMD保存を禁止する。`WARNING` だけがある保存可能状態では、同一 `save_state_fingerprint` につき一度だけYes / No確認を行う。

### 1.1 計画作成時の確認結果

- 2026-07-16にbranch、HEAD、worktree、MS20 routing、B1からB4契約、現行diagnostics core、UiState、RightPane、解析callback、VMD保存入口、関連テストを照合した。
- branchは `feature/MS20-implementation`、HEADは `14c8d3f`、worktreeは計画作成前にcleanだった。
- B2の `OutputDiagnosticsSnapshot` はseverity順の `items`、`saveability.vmd_save_allowed`、`blocking_codes`、`warning_codes`、canonical `save_state_fingerprint` を実装済みである。
- B3 / B4はInfoとlive playbackを実装済みである。再生位置、frame、現在母音はfingerprintから除外済みである。
- `build_output_diagnostics_snapshot_from_ui_state()` は現状 `failure=None`、`analysis_cancelled=False` を固定しており、解析失敗をsnapshotへ渡していない。
- `UiState` は `current_diagnostic_failure`、現在snapshot、確認済みfingerprintを保持していない。
- `MainFrame.sync_ui_state()` はsnapshot生成より先に `update_action_states()` を呼び、保存ボタン／メニューは現行 `UiState.vmd_save_ready` だけで判定している。
- `AppController.request_save_vmd()` のcontroller guardも `UiState.vmd_save_ready` だけを参照し、diagnostic severityとWARNING確認は未接続である。
- RightPane Warningは単一 `wx.StaticText` のplaceholderで、縦scroll、severity別表示、snapshot接続を実装していない。
- VMD保存失敗時は現行でも `current_timing_plan` と解析有効性を変更せずreturnしており、結果保持契約の基盤は成立している。
- B4後の全体テストは430件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1である。B5計画作成時にはコード・テストを実行または変更していない。

### 1.2 計画作成時に固定した補正

- 上位roadmapはWarningタブに `INFO / WARNING / ERROR` の全severityを表示すると定義している。タブ名だけから `WARNING / ERROR` 限定とは解釈しない。
- B1の所有権を、B5実装時点の状態追加に合わせて次の粒度へ具体化する。B5は新規workspace stateを導入するため、既存 `invalidate_analysis()`、`reset_workspace()`、解析開始／成功へfailure、current snapshot、確認済みfingerprintの最小clearを同時実装し、既存reset / invalidation契約を退行させない。B7はこの基本clearを初めて実装するBlockではなく、input change、parameter change、cancel、reset、late callbackを含む全入口の到達確認、欠落補修、横断回帰固定、docs closeoutを所有する。この責務具体化をB7機能の先行実装とは扱わない。
- 現行 `update_action_states()` は先頭で `UiState.refresh_input_mode()` を呼ぶ。B5でsnapshot生成をaction state更新より前へ移す際は、`sync_ui_state()` のsnapshot生成前に `refresh_input_mode()` を移動し、staleなinput modeからdiagnosticsと保存policyを導出しない。`update_action_states()` 内の重複呼出しへ依存しない。
- UIの有効／無効だけを保存policyの正本にしない。controllerは保存ダイアログを開く前に最新snapshotを再生成し、直接呼出しでもERROR保存を拒否する。
- WARNING確認済み状態はfingerprint文字列だけを保持する。diagnostic code、表示文言、dialog開閉状態を別の確認identityとして追加しない。
- WARNING確認でYesを選んだ後に保存先dialogをキャンセルした場合も、そのfingerprintの確認自体は成立済みとする。Noまたはdialog closeでは確認済み状態を更新しない。
- VMD書き込み失敗はwriter入力や診断状態を変更しないため、同一fingerprintの確認済み状態を保持する。保存先変更による再試行で同じWARNINGを再確認しない。
- `DiagnosticFailureInput.summary / detail` は現行coreで `analysis_failure` の表示へ十分に伝播していない。B5ではidentityとfingerprintを変えず、表示専用summary / detailを `DiagnosticItem` へ反映する最小core補正を行う。

### 1.3 実装前チェック結果（2026-07-16）

- 初回チェックでP1なし、P2 2件、P3 1件を検出した。
- P2は、snapshot生成を前倒しした際にstaleな `input_mode` を参照し得る順序問題と、B5の基本clear／B7の横断破棄責務が曖昧だった問題である。前者はsnapshot生成前の `refresh_input_mode()` を必須化し、後者はB5で既存invalidation / reset経路への最小clear、B7で全入口の到達監査・欠落補修・横断回帰を所有する形へ補正した。
- P3はBlock BreakdownのB5成果物候補にdiagnostics core、GUI adapter、theme、関連既存testが不足していた問題であり、実装計画の対象一覧と整合させた。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。production codeとtest codeは変更していない。
- diagnostics core / adapter限定回帰24件、RightPane / playback / VMD保存限定回帰47件、state / failure / reset / late result限定回帰28件とsubtest 7件は、いずれもpass表示・process exit code 0だった。
- MS20-B5は本書の範囲で実装着手可能である。

### 1.4 実装開始前の再チェック結果（2026-07-17）

- P1なし、P2 2件、P3 1件を検出した。
- P2はBlock Breakdownの旧作業ブランチ指定と、theme / AppController回帰testの対象漏れ・wx初期化順序依存である。作業ブランチを `feature/MS20-implementation` へ修正し、既存theme回帰を対象testへ追加して単独実行可能なwx初期化へ補修する。
- P3はIndexの自己参照的な「現在HEAD」表記である。B5実装コード基準HEADとB5計画コミットを分離して記録する。
- P2 / P3補正後に限定回帰を再実行し、production実装へ移行する。

### 1.5 実装・自動検証結果（2026-07-17）

- P2 / P3補正後、`feature/MS20-implementation` 上でB5 production実装を完了した。
- `UiState` にfailure、current snapshot、確認済みfingerprintを追加し、invalidation、analysis start / success、workspace resetへ基本clearを接続した。
- analysis errorを安定した `DiagnosticFailureInput` へ変換し、summary / detailを表示へ伝播しつつfingerprint identityから除外した。
- `MainFrame.sync_ui_state()` はinput mode再判定後にsnapshotを一度だけ生成・保持し、Info、Warning、button / menuへ共有する。
- Warningタブを縦scrollの全severity表示へ置き換え、ERROR / WARNING / INFOのbold labelとtheme別色、long detail wrap、同一内容再構築抑止を実装した。
- controller保存入口で最新snapshotを再評価し、ERROR禁止、WARNINGの同一fingerprint一回確認、No / close、path cancel、writer failureの保持契約を実装した。
- B5 / theme限定17件、diagnostics / RightPane限定64件、state / save / failure限定35件＋subtest 7件、pipeline / VMD 12件はpass表示・process exit code 0だった。
- 全体442件＋subtest 7件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。`compileall src tests` はprocess exit code 0だった。
- 2026-07-17にユーザーGUI確認13項目がすべて通過し、問題なしと報告された。B5はproduction実装、自動検証、ユーザーGUI確認まで完了した。

### 1.6 ユーザーGUI確認結果（2026-07-17）

- Warningタブの未解析ERROR、解析成功INFO、fallback WARNING、全severity表示、長文scroll、Light / Dark / System theme表示を確認し、すべて問題なしと報告された。
- ERROR時のVMD保存禁止、WARNING時のYes / No確認、同一fingerprintでの再確認抑止、状態変更後の再確認を確認し、すべて問題なしと報告された。
- 解析失敗、保存先cancel、VMD保存失敗後の状態保持と再試行、B3の再解析attention、B4 playbackを含む関連GUI回帰を確認し、すべて問題なしと報告された。
- 以上により、MS20-B5の手動GUI確認13項目は完了した。実MMD、build、SmokeLaunch、package確認はB5範囲外のため実施していない。

## 2. 背景

MS20-B2からB4により、diagnosticsの正本とInfo表示は実装済みである。

```text
UiState + writer parameter
  -> DiagnosticSnapshotInput
  -> OutputDiagnosticsSnapshot
       - items
       - saveability
       - save_state_fingerprint
  -> RightPane Info
```

ただし現状、VMD保存操作はこのsnapshotを参照していない。

```text
UiState.vmd_save_ready
  -> button / menu enable
  -> AppController.request_save_vmd() guard
  -> save dialog
  -> writer
```

このままでは、B2 snapshotに `ERROR` があってもlegacy保存条件だけがtrueなら保存入口が開き得る。また、fallbackを示す `WARNING` はInfoの件数に現れるだけで、詳細確認と同一状態一回の保存確認が成立しない。解析失敗もダイアログ表示後に構造化状態として残らない。

B5ではsnapshotを表示・action state・controller guardの共通入力にする。ただし、`UiState.vmd_save_ready` は削除せず、snapshot builder内のexisting contractとして維持する。MS20 severityはlegacy保存条件を置換するのではなく、追加のfail-closed policyとして扱う。

## 3. 目的

- RightPane WarningをB2 snapshotの全diagnostic item表示へ置き換える。
- `INFO / WARNING / ERROR` を安定順、明示ラベル、theme追従色で表示する。
- 解析失敗を `DiagnosticFailureInput` としてworkspace内へ保持し、snapshotへ接続する。
- `ERROR` 存在時にVMD保存ボタン、メニュー、controller入口の全てを禁止する。
- `WARNING` 存在時に同一fingerprint一回のYes / No確認を行う。
- No / close、fingerprint変更、解析開始／成功／無効化、workspace resetの確認済み状態を決定的に扱う。
- VMD保存失敗時に解析結果、Preview、Waveform、failure、確認済みfingerprintを失わない。
- TEXTあり／voice_only、B3 Info、B4 playback、既存VMD writer出力を維持する。

## 4. In Scope

- `UiState` へのworkspace内diagnostics state追加
  - `current_diagnostic_failure: DiagnosticFailureInput | None`
  - `current_output_diagnostics_snapshot: OutputDiagnosticsSnapshot | None`
  - `confirmed_warning_save_state_fingerprint: str | None`
- 解析例外から `DiagnosticFailureInput` へのGUI adapter
- analysis start / success / error、analysis invalidation、workspace resetの基本clear規則
- `DiagnosticFailureInput.summary / detail` の表示専用伝播
- `MainFrame.sync_ui_state()` におけるsnapshot一回生成と共有
- Warningタブの縦scroll化
- 全severityの安定順表示、empty表示、long detail wrap
- Light / Dark / Systemにおけるseverity表示
- snapshotによるVMD保存ボタン／メニュー有効化
- controllerでの最新snapshot再評価
- WARNING確認dialog、同一fingerprint確認済み保持
- No / close / Yes / 保存先cancel / writer失敗の状態契約
- B5専用test、関連回帰、計画・routing文書同期

## 5. Out of Scope

- diagnostic code、severity、canonical payload、hash algorithm、schema versionの再設計
- `VowelTimingPlan`、timing source、fallback生成ロジックの変更
- VMD writerのshape、keyframe、encoding、出力形式変更
- report formatter、`<base>_report.txt`、report保存導線（B6）
- B7が所有する全input / parameter / cancel / reset / late callback event matrixのcloseout
- 診断項目の非表示、恒久無視、設定永続化
- 確認済みfingerprintの設定ファイル保存
- Warningタブからの修正操作、再解析操作、diagnostic item選択
- MMD用WAV出力policyの変更
- custom warning dialog frameworkの新設
- Preview、Waveform、MCI playback、viewportの挙動変更
- 固定モーフ `あ / い / う / え / お` の変更
- 外部cloud ASR、他ASR backend、外部送信、background通信
- Whisper / FFmpegの自動download
- 新規dependency、build、package、release、tag、push
- Qt / PySide6 GUIの復活

## 6. 前提条件

- `feature/MS20-implementation` 上で実装する。
- 実装開始前にworktreeとHEADを再確認する。
- B4実装コミット `14c8d3f` を基準とし、未コミット変更がある場合はユーザー所有変更として保護する。
- B1のseverity、diagnostic code、fingerprint、failure ownership契約を維持する。
- B2の `OutputDiagnosticsSnapshot` を診断正本とし、RightPane表示文字列をpolicy入力へ戻さない。
- B3 InfoとB4 playback contextの表示・theme・scroll契約を維持する。
- legacy `UiState.vmd_save_ready` とdiagnostics policyの両方を満たす場合だけ保存可能とする。
- コマンドは一つずつ実行し、parallel、pipeline、chainを使用しない。

## 7. 対象ファイル

### 7.1 主変更

- `src/core/output_diagnostics.py`
  - failure DTOの表示用summary / detail伝播だけを補正する。
  - identity、severity、code、fingerprint payloadは変更しない。
- `src/gui_wx/ui_state.py`
  - failure、current snapshot、confirmed fingerprintをworkspace stateとして追加する。
  - 基本clear methodと既存reset / invalidation / successへ接続する。
- `src/gui_wx/output_diagnostics_adapter.py`
  - `UiState.current_diagnostic_failure` をsnapshot inputへ渡す。
  - analysis errorを安定code / phase / recoverabilityへ変換する。
- `src/gui_wx/right_pane.py`
  - Warningを `wx.ScrolledWindow` とseverity別item表示へ置き換える。
  - snapshot setter、clear、test取得helperを追加する。
- `src/gui_wx/theme.py`
  - WARNINGは既存 `attention_text`、ERRORはtheme別 `error_text`、INFOは通常 `text_fg` を使用できるようにする。
- `src/gui_wx/main_frame.py`
  - snapshotを同期内で一回生成・保持・共有する。
  - analysis callbackとwarning confirmation view helperを接続する。
- `src/gui_wx/app_controller.py`
  - severity連動save guard、WARNING確認、fingerprint reuseを実装する。

### 7.2 関連確認

- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/voice_only_errors.py`
- `src/gui_wx/parameter_panel.py`
- `src/gui_wx/playback_context.py`
- `src/core/pipeline.py`
- `src/vmd_writer/writer.py`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`

### 7.3 テスト

- 新規 `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b4_playback_context.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms15_b5_state_theme.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_pipeline_and_vmd.py`

### 7.4 文書

- `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

`README.md`、配布用readme、`repo_milestone.md`、`Version_Control.md` はB5実装時点では変更しない。B7 closeoutで現行到達状態とユーザー向け説明の更新要否を判定する。

## 8. 実装方針

### 8.1 snapshotを一つのpolicy正本として共有する

`MainFrame.sync_ui_state()` は同一同期内でsnapshotを一度だけ生成する。

```text
UiState.refresh_input_mode()
snapshot = build current diagnostics
UiState.current_output_diagnostics_snapshot = snapshot
update_action_states(snapshot)
RightPane.set_info_snapshot(snapshot)
RightPane.set_warning_snapshot(snapshot)
playback / Preview / selection sync
```

Info、Warning、button/menuが別々にsnapshotを生成しない。再生timer経路はB4どおりsnapshotを生成しない。

`refresh_input_mode()` はsnapshot buildより前の同期前処理として一度だけ実行する。`update_action_states(snapshot)` は渡されたsnapshotと既に解決済みのinput modeを使用し、内部の `refresh_input_mode()` 実行順へpolicyの正しさを依存させない。

Controller保存入口では、UI表示後の状態変更や直接呼出しへfail closedに対応するため、保存直前にMainFrameの共通builder helperから最新snapshotを再生成・保持する。表示済み文字列や古いcached snapshotだけを信用しない。

### 8.2 failure adapter

analysis errorをexception instanceのままUiStateへ保持しない。次の値だけを `DiagnosticFailureInput` へ格納する。

- `code`: input modeと例外分類から決める安定code
- `source_severity`: `error`
- `phase`: `whisper_transcribe`、`text_convert`、`pipeline_build` のいずれか
- `recoverability`: 原則 `retry_possible`
- `identity_context`: categoryとexception typeの安定文字列。exception messageを含めない
- `summary`: 利用者向け要約
- `detail`: actionと、必要ならexception type / messageの表示用文字列

voice_onlyは `classify_voice_only_analysis_error()` のcategory、summary、actionを再利用する。TEXTありは `TextProcessingError`、`WhisperTimingError`、`PipelineError`、unknownを安定分類する。exception messageはsummary / detailにだけ含め、fingerprint identityへ含めない。

`_on_analysis_error()` はjob ID一致とcancel判定を先に行う。late resultとcancelからfailureを作成しない。現在jobの非cancel errorだけをinvalid化後に `current_diagnostic_failure` へ設定してsyncする。

### 8.3 failure表示伝播

B2 coreの `analysis_failure` code、ERROR severity、identity contextは維持する。単一failureではDTOのsummary / detailを `DiagnosticItem` の表示値へ反映する。複数failureではstable sort後に表示情報を決定的に結合する。

- summary / detail変更だけではfingerprintを変更しない。
- failure code、phase、recoverability、identity context変更ではfingerprintが変わる。
- raw exception instance、traceback、object reprをsnapshotへ入れない。

### 8.4 Warningタブ表示

Warningタブは `wx.ScrolledWindow` と縦sizerを使用する。snapshot `items` の順序を維持し、各itemを次の構成で表示する。

```text
[ERROR] <summary>
<detail>              # 空なら省略

[WARNING] <summary>
<detail>

[INFO] <summary>
<detail>
```

- ERROR label: bold + `ThemePalette.error_text`
- WARNING label: bold +既存 `ThemePalette.attention_text`
- INFO label: bold +通常 `text_fg`
- detail: normal weight +通常 `text_fg`
- itemがない場合: `現在の診断はありません。`

row生成時に現在paletteを適用する。theme切替では `ThemeManager.apply_theme()` の再帰処理が全 `wx.StaticText` を通常 `text_fg` へ戻すため、その直後に `RightPane.refresh_warning_styles()` を呼び、severity labelだけをERROR / WARNING / INFO色へ再適用する。B3 `refresh_info_attention_style()` と同じ責務境界を使用する。

全severityを表示し、ERROR / WARNINGだけを抽出しない。表示はsnapshot projectionであり、RightPaneでseverityやsaveabilityを再計算しない。

同一表示内容の再syncでは不要な子widget再生成、scroll位置reset、Layout連打を避ける。内容変更時だけsizerを更新し、Wrap、Layout、FitInside、Refreshを行う。B4 playback timerはWarning tabを更新しない。

### 8.5 VMD保存action state

保存ボタンとメニューの有効条件を次へ変更する。

```text
not UiState.is_busy
and snapshot.saveability.vmd_save_allowed
```

`snapshot.saveability.vmd_save_allowed` はlegacy `UiState.vmd_save_ready` とERRORなしの両方を含む。WARNINGは保存可能であるためbutton/menuを無効化しない。

### 8.6 controller save guard

`AppController.request_save_vmd()` は保存先dialogより前に次を実施する。

```text
1. viewとBusyを確認
2. 最新snapshotを再生成
3. vmd_save_allowedがfalseならstatusをVMD保存不可としてreturn
4. WARNINGなしなら保存先dialogへ進む
5. WARNINGあり、confirmed fingerprint一致なら再確認せず保存先dialogへ進む
6. WARNINGあり、未確認fingerprintならYes / No確認
7. Yesならfingerprintを保持して保存先dialogへ進む
8. No / closeなら保持せずreturn
9. 既存TEXTあり／voice_only writer入口へ進む
```

defensive rule:

- WARNINGがあるのにfingerprintが `None` の場合は確認済みにせず保存不可として扱う。
- UI buttonが誤って有効でもcontroller guardが必ず拒否する。
- 保存先dialogやwriterへ進んだ後にdiagnostic stateを再計算しない。

### 8.7 WARNING確認dialog

MainFrameに確認用view helperを追加し、OS標準 `wx.MessageBox` を使用する。

- title: `VMD保存前の確認`
- style: `wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING`
- 本文:
  - fallback等の警告があること
  - RightPane Warningで詳細を確認できること
  - 保存を続行するか
  - 対象WARNINGのsummaryを安定順で列挙
- Yesだけをtrueとし、Noとwindow closeはfalseとする。

独自dialog frameworkは追加しない。OS標準dialogの制御不能なtheme範囲は手動確認結果へ明記する。

### 8.8 確認済みfingerprint lifecycle

| event | confirmed fingerprint |
| --- | --- |
| 初期状態 | `None` |
| WARNING確認Yes | 現在snapshot fingerprintを保持 |
| WARNING確認No / close | 更新しない |
| 同一fingerprint再保存 | 再確認しない |
| 保存先dialog cancel | Yes済みfingerprintを保持 |
| VMD保存成功 | 保持 |
| VMD保存失敗 | 保持 |
| playback位置／frame／母音更新 | 保持 |
| analysis start | clear |
| analysis success | clear |
| analysis invalidation | clear |
| workspace reset | clear |
| fingerprint不一致 | old値を確認済みとして使わない |
| late callback | 更新しない |

input / parameter / transcription editは既存 `invalidate_analysis()` を経由する範囲でclearする。B7で全入口とlate callbackを横断監査する。

### 8.9 VMD保存失敗保持

writer例外時は次を変更しない。

- `current_timing_plan`
- `analysis_result_valid`
- `analysis_pending_rebuild`
- `current_diagnostic_failure`
- `current_output_diagnostics_snapshot`
- `confirmed_warning_save_state_fingerprint`
- Preview / Waveform

現行error dialogとstatus更新を維持し、保存先を変更して再試行できる状態にする。VMD保存失敗をanalysis failureへ変換しない。出力失敗診断のreport保持拡張はB6 / B7の計画で再評価する。

## 9. 詳細ステップ

### Step 1: 実装前基準線確認

- branch、HEAD、worktreeを一つずつ確認する。
- B1 / B2 / B3 / B4 planとB5本書を再読する。
- 対象code / testが計画作成時から変わっていないか確認する。
- P1 / P2 / P3を記録し、P1 / P2があれば実装前にplanを補正する。

### Step 2: core failure表示の最小補正

- `_build_failure_items()` のidentity構築とsortを維持する。
- DTO summary / detailを表示専用fieldへ決定的に反映する。
- summary / detail変更でfingerprintが変わらないtestを維持・追加する。
- code、severity、phase、identity context、schema versionを変更しない。

### Step 3: UiState diagnostics state追加

- 3つのworkspace fieldを追加する。
- clear helperを小さく分け、analysis invalidation、success、resetへ接続する。
- `has_workspace_user_data` はdiagnostics派生stateだけをreset確認理由にしない。
- settings / recent filesへ永続化しない。

### Step 4: analysis failure adapter接続

- exception classとinput modeを安定分類するpure helperを追加する。
- voice_only既存presentationを再利用する。
- `_on_analysis_error()` でcurrent noncancel jobだけを保持する。
- analysis start / successでold failureをclearする。
- late jobとcancelがfailureを上書きしないtestを追加する。

### Step 5: snapshot共有経路

- MainFrameにcurrent snapshot build / store helperを追加する。
- `sync_ui_state()` のsnapshot build前に `state.refresh_input_mode()` を実行し、現行 `update_action_states()` 内の再判定責務を前倒しする。
- `sync_ui_state()` で一回だけbuildする。
- action state、Info、Warningへ同一objectを渡す。
- controller保存入口から最新buildを要求できる契約を追加する。
- playback timerがbuilderを呼ばないB4回帰を維持する。

### Step 6: Warning UI

- Warning panelを縦scrollへ変更する。
- snapshot item rowの生成、clear、同一内容skip、wrap、theme refreshを実装する。
- MainFrame theme適用後にInfo attentionとWarning severity styleを再適用する。
- 全severity、順序、detail、empty状態をtestする。
- B3 Info、B4 playback、他4タブを変更しない。

### Step 7: save action stateとcontroller guard

- button / menu enableをsnapshot saveabilityへ接続する。
- controllerで最新snapshotを再評価する。
- ERROR時はdialog / writerを呼ばない。
- WARNING時はfingerprint確認を行う。
- WARNINGなしは従来どおり保存する。
- TEXTあり／voice_only writer引数を変更しない。

### Step 8: lifecycleと失敗保持

- Yes / No / close / path cancel / writer success / writer failureを固定する。
- playback更新で再確認しない。
- invalidation / reset / analysis start / successでclearする。
- late callbackが状態を更新しないことをB5対象範囲で確認する。

### Step 9: 回帰・文書同期

- B5専用testから実行する。
- diagnostics、RightPane、state、save、voice_only、reset、late result、pipeline/VMD回帰へ広げる。
- 全testsはリスクに比例して実行する。
- pass表示とprocess exit codeを分けて記録する。
- 実装結果とユーザー確認結果をB5 plan、Index、Roadmap、Block Breakdownへ同期する。

## 10. 状態遷移 / データ契約

### 10.1 保存policy

```text
snapshotにERRORあり
  -> button / menu disabled
  -> controller guardで拒否
  -> save dialogを開かない

ERRORなし、WARNINGあり
  -> button / menu enabled
  -> fingerprint未確認ならYes / No
     -> Yes: fingerprint保持、save dialogへ
     -> No / close: 保存せず、次回再確認
  -> fingerprint確認済みならsave dialogへ

ERROR / WARNINGなし
  -> legacy保存条件成立時にsave dialogへ
```

### 10.2 snapshotと表示の境界

- Info: summariesとsaveabilityの概要
- Warning: `snapshot.items` の全severity
- Controller: `snapshot.saveability` と `save_state_fingerprint`
- Report: B6で同じsnapshotを使用
- playback context: snapshot外、fingerprint外

Warning表示文字列、label color、notebook選択tabはpolicy入力にしない。

### 10.3 failure state

```text
analysis start
  -> old failure clear
  -> confirmed fingerprint clear

current job success
  -> timing plan更新
  -> failure clear
  -> confirmed fingerprint clear
  -> snapshot再生成

current job noncancel error
  -> analysis invalidation
  -> classified failure保持
  -> snapshot再生成
  -> analysis_failure ERROR表示

cancel / late job
  -> failureを新規作成しない
  -> late jobはstateを更新しない
```

### 10.4 不変条件

- `OutputDiagnosticsSnapshot` がdiagnosticsとsave policyの正本である。
- `UiState.vmd_save_ready` を削除・無視しない。
- ERRORがある状態を保存可能側へ倒さない。
- WARNINGは保存可能だが未確認fingerprintではwriterへ進まない。
- summary / detail変更だけで確認を再要求しない。
- writer入力が変わればfingerprintが変わり、再確認が必要になる。
- playbackだけの変更でfingerprintと確認済み状態を変えない。
- 保存失敗で解析結果を破棄しない。

## 11. テスト方針

### 11.1 core / adapter

- failure summary / detailが `analysis_failure` 表示へ伝播する。
- failure summary / detailだけを変えてもfingerprintが同一である。
- failure identity変更でfingerprintが変わる。
- voice_only categoryとTEXTあり例外が安定DTOへ変換される。
- exception instance、traceback、object reprを保持しない。
- UiState failureがsnapshotへ入り、ERRORで保存不可になる。

### 11.2 UiState lifecycle

- 初期値はfailure / snapshot / confirmed fingerprint全て `None`。
- analysis invalidation、success、resetでold stateをclearする。
- analysis error後はfailureを保持する。
- diagnostics派生stateだけでworkspace reset確認を要求しない。
- recent files、theme、last directoryへ永続化しない。
- `input_mode` が保持fieldと不一致の状態からsyncしても、snapshot build前にTEXTあり／voice_onlyへ再判定される。

### 11.3 Warning UI

- constructor直後のplaceholder契約を確認する。
- MainFrame初回sync後に現行ERROR診断が表示される。
- valid resultではINFOが表示される。
- fallback resultではWARNINGとINFOがsnapshot順で表示される。
- analysis failureではERROR summary / detailが表示される。
- long detailで横幅を押し広げず、縦scrollできる。
- 同一snapshot再設定でscroll位置を不要にresetしない。
- Light / Dark / SystemでERROR / WARNING / INFO / detailが読める。
- Info、playback、他タブの表示を壊さない。

### 11.4 save policy

- ERROR時はbutton / menuがdisabled。
- controller直接呼出しでもsave dialogとwriterを呼ばない。
- WARNING時はbutton / menuがenabled。
- 初回WARNINGで確認dialogを1回表示する。
- Yesで保存へ進み、同一fingerprintでは再確認しない。
- No / closeで保存へ進まず、次回は再確認する。
- fingerprint変更で再確認する。
- playback位置だけの変更では再確認しない。
- WARNINGなしでは確認dialogを表示しない。
- WARNINGありでfingerprint `None` はfail closedにする。
- 保存先dialog cancel後もYes済みfingerprintを保持する。
- staleな `input_mode` でcontroller保存を要求しても、最新入力状態から再判定したsnapshot policyを使用する。

### 11.5 VMD保存失敗

- TEXTあり保存失敗後にplanと解析有効性を保持する。
- voice_only保存失敗後にplan、書き起こし、解析有効性を保持する。
- confirmed fingerprintを保持する。
- 再試行可能である。
- success statusを表示しない。

### 11.6 対象testコマンド

最小:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py -q
```

diagnostics / RightPane:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b3_output_diagnostics_adapter.py tests/test_ms20_b3_right_pane_info.py tests/test_ms20_b4_playback_context.py tests/test_wx_ms16_b3_right_pane.py -q
```

state / save / failure:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py tests/test_wx_ms14_b5_export.py tests/test_ms19_b4_voice_only_gui_state.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py tests/test_ms17_b8_late_worker_result_discard.py -q
```

pipeline / VMD:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py -q
```

theme / AppController単独回帰:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b5_state_theme.py -q
```

このtestは他のwx testが先に `wx.App` を生成する順序へ依存させず、単独実行できるfixture契約を維持する。

全体:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

各実行は一つずつ行う。GUI runnerがpass表示後に既知wx終了処理でnonzeroとなる場合も、pass数とprocess exit codeを分けて記録する。

### 11.7 手動GUI確認

1. 起動直後にWarningタブへ未解析ERRORが表示される。
2. 解析成功後にINFO診断が表示される。
3. fallbackを含む結果でWARNINGが表示され、VMD保存ボタン／メニューは有効である。
4. WARNING状態の初回保存で確認dialogが表示される。
5. Noまたはdialog closeでは保存先dialogへ進まず、次回も再確認される。
6. Yes後は保存先dialogへ進み、同一状態の再保存では再確認されない。
7. parameter変更／再解析後は古い確認済み状態を引き継がない。
8. ERROR状態ではVMD保存ボタン／メニューが無効である。
9. 解析失敗後にWarningタブへfailure ERRORが残り、入力とWaveformは復帰操作に利用できる。
10. VMD保存失敗後もPreview、Waveform、解析結果が残り、別保存先へ再試行できる。
11. 長い診断detailでもRightPane幅が崩れず縦scrollできる。
12. Light / Dark / Systemでseverity label、detail、標準確認dialogが判読できる。
13. B3の「再解析が必要」bold／orange、B4 playback表示、他タブに回帰がない。

手動GUI確認を実施していない場合は未実施と報告する。実MMD、build、SmokeLaunch、package確認はB5範囲外とする。

### 11.8 文書・差分検証

```powershell
git diff --check
```

```powershell
git status --short --branch
```

## 12. 受け入れ条件

- Warningタブにsnapshotの `INFO / WARNING / ERROR` が安定順で表示される。
- Warningタブが縦scroll、wrap、Light / Dark / Systemへ対応する。
- RightPaneは診断severity、code、saveability、fingerprintを再計算しない。
- snapshot生成前に `UiState.refresh_input_mode()` が完了し、action state、Info、Warning、controller guardが同じ解決済みinput modeを使用する。
- current analysis errorが構造化failureとしてworkspace内に保持される。
- exception instance、traceback、表示文言をfingerprint identityに含めない。
- failure summary / detailの表示改善でfingerprint schemaが変わらない。
- ERRORがある間はbutton、menu、controllerの全入口からVMD保存できない。
- WARNINGだけの状態では保存操作が有効で、未確認fingerprintにYes / No確認が表示される。
- Yes後は同一fingerprintで再確認しない。
- No / closeでは保存せず、次回同一fingerprintでも再確認する。
- writer入力またはdiagnostic identityが変われば再確認する。
- playback位置だけでは再確認しない。
- VMD保存失敗後も解析結果と再試行可能状態を保持する。
- TEXTあり／voice_onlyの既存writer入口と引数を変更していない。
- B3 Info、B4 playback、Preview、Waveform、MCI、MMD用WAV出力を変更していない。
- 固定モーフ、外部通信禁止、Whisper非自動download、wxPython主系を維持する。
- 新規dependency、package、license影響がない。
- 対象test結果とprocess exit codeが分けて記録される。
- ユーザーGUI確認の実施／未実施と結果が記録される。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| Warningタブ名からWARNINGだけを表示してINFOを失う | roadmap正本どおり全severityを表示し、専用testで固定する |
| action stateとcontrollerが異なるsnapshotを参照する | sync内一回共有と、保存直前の最新再評価を分けて契約化する |
| button無効化だけでERROR保存を防いだつもりになる | controller直接呼出しtestでdialog / writer非呼出しを固定する |
| summary文言変更でWARNING確認が毎回復活する | fingerprintはidentityだけを使用し、summary / detail除外testを維持する |
| playback timerごとにsnapshot生成やwarning再描画が走る | B4軽量経路を変更せず、builder / Layout非呼出し回帰を維持する |
| save dialogのcancelでWARNING確認が不必要に復活する | Yes時点でfingerprintを保持し、保存先選択と分離する |
| writer失敗をanalysis failureとして保持し、再保存できなくなる | VMD出力失敗は解析stateへ反映せず、現行結果を保持する |
| raw exceptionをUiStateへ保持してidentityが不安定になる | 安定DTOへ変換し、messageは表示fieldだけへ入れる |
| input変更後も古いfailureや確認済みfingerprintが残る | invalidation / reset primitiveでclearし、B7で全入口を横断監査する |
| dynamic Warning rowsでscroll位置や幅が跳ねる | 同一表示skip、縦scroll、wrap、内容変更時だけLayout / FitInsideを行う |
| severity色がtheme未追従または判別不能になる | paletteへ集約し、Light / Dark / Systemで色とboldをtestする |
| core failure表示補正がfingerprintを変える | identity構築を変更せず、payload / hash同一性testを追加する |
| 既存MockViewが新しいview helper不足で壊れる | save test fixtureへsnapshot build / warning confirm helperを明示追加する |

## 14. Codex 実装時の注意

```text
- 本書の実装前にpre-implementation checkを行い、P1 / P2 / P3を記録する。
- production実装はpre-implementation checkのP1 / P2解消後に開始する。
- コマンドは一つずつ実行し、parallel、pipeline、chainを使用しない。
- WarningタブにはINFO / WARNING / ERRORの全diagnostic itemを表示する。
- UiState.vmd_save_readyを削除せず、snapshot saveabilityと二重に満たす。
- UI文字列やlabel色からsave policyを導出しない。
- ERROR拒否はbutton / menuだけでなくcontroller入口でも行う。
- WARNING確認identityはsave_state_fingerprintだけとする。
- summary / detail、exception message、dialog状態をfingerprintへ加えない。
- playback位置、frame、母音で確認済み状態を無効化しない。
- analysis late callbackとcancelからfailureを作成しない。
- VMD保存失敗でcurrent timing plan、Preview、Waveformを破棄しない。
- B6 reportとB7横断closeoutを先行実装しない。
- 固定モーフ あ / い / う / え / お を変更しない。
- 外部cloud ASR、他ASR backend、音声外部送信、background通信を追加しない。
- Whisper / FFmpegの自動downloadを追加しない。
- wxPython主系を維持し、Qt / PySide6を復活させない。
- dependency、build、package、release、tag、pushを変更しない。
- 実行していないtestや手動GUI確認を通過と報告しない。
- pass表示とprocess exit codeを分けて報告する。
```

B5実装完了報告は次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
```
