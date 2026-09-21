# MS24-B6 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: MS24-B6「Info・診断レポート・エラー復帰契約」
- 作成日: 2026-08-25
- 状態: Implementation Plan（B6実装・検証結果追記済み、MS24-B7実施記録あり・MS24 Closeout A判定済み）
- 依存ブロック: MS24-B3、MS24-B5
- 実装基準コミット: `78172d9 Implement MS24-B5 model runtime integration`
- 正本:
  - `docs/Implementation_Plan/MS24_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS24-B5_Implementation_Plan.md`
- 依存値:
  - `pyproject.toml`: `openai-whisper==20250625`
  - `requirements.txt`: `openai-whisper==20250625`
- 実装開始条件:
  - 本計画のレビューが完了していること。
  - live Git状態とB5実装後コードを再確認すること。
  - MS22 / MS23 Closeout Aを未完了へ戻さないこと。

B5 baseline確認時点では、HEADは `78172d9 Implement MS24-B5 model runtime integration` で作業ツリーはcleanだった。B6実装・検証後のproduction code・test code変更は `1f1aff2 Implement MS24-B6 diagnostics and recovery` としてcommit済みである。現在のB7計画作成時点で未追跡なのは `docs/Implementation_Plan/MS24-B7_Implementation_Plan.md` であり、B6のproduction code、test code、依存関係、runtime user dataには未コミット変更がない。本段落は計画作成時点のbaselineと、B6実装後の状態同期を区別して記録する。

## 2. 背景

MS24-B5までに、選択候補、active、loaded、analysis、retainedのWhisper model identityと、verified local checkpoint専用runtime、single-active ownership、model-aware rollbackが実装された。現行 `WhisperModelSelectionState` にはこれらのidentity、availability、再構築理由、failure class、管理処理状態が存在する。

一方、現行の出力診断は `InputDiagnosticsSummary`、`AnalysisDiagnosticsSummary`、`GenerationDiagnosticsSummary`、`SaveabilitySummary` で構成され、Whisper固有状態を一元化するsummaryがない。Infoと診断レポートもselected / active / loaded / analysisの差を表示できず、RightPane、Preview、VMD保存可否、transcription controlsは同一同期処理内でも一部が別々にlive stateを参照している。

また、現行の診断failure detailとvoice-only error messageは例外文字列をそのまま連結する経路を持つ。Whisperのstorage rootやloader例外をそのまま通常UI・レポートへ投影すると、不要な絶対パスやユーザー環境情報を露出する可能性がある。

B6ではB5のruntimeやownershipを再実装せず、B5が確定した状態を単一snapshotへ安全に投影し、Info、RightPane、診断レポート、error notice、VMD保存、Preview、transcription stateを同じ世代で同期する。

## 3. 目的

1. `OutputDiagnosticsSnapshot` に専用 `WhisperDiagnosticsSummary` を追加し、Whisper固有状態を一元化する。
2. selected / active / loaded / analysis identityとavailabilityを区別し、active対analysisのsemantic identityとactive対loadedのruntime identityを別々に診断する。
3. B5のfailure classとrollback契約を、TEXT + 音声とvoice-onlyのerror / recoverabilityへ同じ規則で投影する。
4. model load・integrity・memory等の失敗後に、旧成功情報、Preview、VMD saveabilityを誤って復元しない。
5. 通常UI・レポートへ絶対パス、認証情報、raw exceptionを過剰露出しない。
6. 既存 `ms21-effective-output-v1` fingerprint schema / payload / 値を変更しない。

## 4. In Scope

- immutableな `WhisperDiagnosticsSummary` と、必要なモデル別availability行DTOの追加。
- selected / active / loaded / analysisのmodel key、表示名、manifest identityを明示的に分離した保持。
- manifestが要求する `openai-whisper` package version、loader gate状態、manifest schema version、availability、管理処理状態、rebuild reason、failure class / safe detail codeの保持。
- InfoへWhisper sectionを追加。
- 診断レポートへWhisper sectionを追加。
- RightPaneのWhisper表示を同一snapshot世代から更新。
- Whisper failureを既存 `DiagnosticFailureInput` のseverity / phase / recoverabilityへ写像。
- voice-only noticeのWhisper例外をsafe messageへ置換。
- rollback非許可failure classの判定を一箇所へ集約し、B5とB6で共用。
- analysis identity不一致・欠落のfail-closed検出。
- 同一snapshot世代によるInfo、Warning、RightPane、VMD save action、Preview placeholder、transcription controlsの同期。
- B6専用unit / integration testsと、影響する既存testsの更新。
- 実装後の手動wxPython GUI確認項目の提示。

## 5. Out of Scope

- MS24-B5のruntime、loader、AnalysisWorker、single-active ownership、暗黙download禁止契約の再実装。
- model manifest、公式URL、SHA256、exact size、filenameの変更。
- model download、cancel、delete、Apply処理そのものの変更。
- `openai-whisper==20250625`以外への依存更新。
- `ms21-effective-output-v1` fingerprint schema / payloadの変更。
- MS23固定モーフ、Latin profile、preset、model profile、VMD、voice-only timingの仕様変更。
- README、利用者向け詳細文書、package/spec、release readinessを含むMS24-B7 closeout。
- actual MMDでのVMD / WAV確認。これはMS26で行う。
- package / release / tag / push / merge。これはMS27または明示承認後に行う。
- cloud ASR、音声外部送信、background通信、Whisper自動download、Qt / PySide6。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` の直接読み取り・変更・コピー・stage。

## 6. 前提条件

- B3のselected / active / availability / management stateを正本とする。
- B5のloaded / analysis / retained identity、rebuild reason、failure classを正本とする。B6はこれらを独自再計算しない。
- B5 failure classは次を維持する。
  - `none`
  - `model_unavailable`
  - `integrity_mismatch`
  - `load_failure`
  - `memory_failure`
  - `transcribe_failure`
  - `cancelled`
- live実装のrollback非許可classは `model_unavailable`、`integrity_mismatch`、`load_failure`、`memory_failure`、`transcribe_failure` とする。`cancelled` はmodel commit前後と `analysis_rebuild_reason` / identity条件で判定する。
- selectedとactiveの不一致は候補選択中の正常状態であり、それだけでは既存成功結果を無効化しない。
- active / analysisのsemantic identity不一致は、active変更がcommitされた解析結果を成功扱いにせず、既存saveabilityをfail-closedにする。
- active / loadedのruntime identityはsemantic resultと分離する。loadedが `None` または明示unload済みであることだけでは、identity一致済みの既存analysis / Preview / VMD saveabilityを無効化しない。ただし新規解析開始時はverified requestとruntime identityを再検証し、不一致または不完全ならfail-closedにする。
- 現行Python 3.14.3を本リポジトリの開発・受入環境とする。Python 3.11 / 3.12は今回の受入対象外として未検証扱いを維持し、B6で依存値は変更しない。
- 通常UI・レポート用のstorage表示は次で固定する。
  - 既定保存先: `既定保存先 (models)`
  - ユーザー指定: `ユーザー指定 (<末尾フォルダー名>)`
  - 末尾名を安全に取得できない場合: `ユーザー指定`
  - 解決不能: `保存先を確認できません`
- canonicalな絶対パスはstorage解決、file dialog、設定保存等の内部処理にだけ保持し、Info、Warning、Whisper panel、診断レポートへ渡さない。
- full manifest identityは認証情報ではないためsnapshotと診断レポートへ保持できる。Infoは可読性のためmodel key、manifest schema / package versionを中心に表示し、必要ならidentityを短縮表示する。

## 7. 対象ファイル

### 7.1 主変更対象

- `src/core/output_diagnostics.py`
  - `WhisperModelDiagnosticsItem`、`WhisperDiagnosticsSummary`、snapshot generationを追加する。
  - identity整合性とWhisper failure diagnostic itemを既存saveability計算へ統合する。
  - fingerprint非変更境界を維持する。
- `src/core/diagnostic_report.py`
  - `[Whisper]` sectionを追加する。
  - safe detailだけを出力する。
- `src/core/__init__.py`
  - 新規DTOを既存規約に従ってexportする。
- `src/gui_wx/output_diagnostics_adapter.py`
  - `WhisperModelSelectionState` からsummaryを一度だけ構築する。
  - B5 failure class / detail codeをsafe diagnostic failureへ写像する。
  - InfoのWhisper sectionを追加する。
- `src/gui_wx/analysis_rollback.py`
  - rollback非許可classと判定helperを一元化する。
- `src/gui_wx/voice_only_errors.py`
  - Whisper failureではraw exceptionを表示せずsafe notice / actionを用いる。
- `src/gui_wx/ui_state.py`
  - storage rootの内部pathと通常表示用kindを区別する最小状態を追加する。
  - 既存 `format_whisper_failure_notice()` をsafe messageの正本として再利用・補完する。
- `src/gui_wx/right_pane.py`
  - Whisper panelをsnapshot summaryから描画する。
  - raw storage path / raw failure detailを表示しない。
- `src/gui_wx/main_frame.py`
  - snapshot generationを発行し、同一snapshotを全UI投影へ渡す。
  - rollback判定helperを使用する。
  - Preview / transcription controls / error noticeをsnapshotに同期する。
- `src/gui_wx/app_controller.py`
  - `StorageRootResolution.used_default` を通常表示用kindへ渡す。
  - scan、download、delete、Apply後のsnapshot再構築契約を維持する。

### 7.2 新規テスト

- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_ms24_whisper_error_recovery.py`

### 7.3 更新候補テスト

- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms22_b6_lifecycle_regression.py`
- `tests/test_wx_ms22_b6_lifecycle_regression.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_ms24_whisper_model_apply.py`
- `tests/test_ms24_whisper_model_runtime.py`
- `tests/test_ms24_whisper_model_ui_state.py`
- `tests/test_wx_ms24_whisper_model_ui.py`

既存テストは新規DTOの必須引数追加で無関係なfixtureを大量修正しないよう、legacy caller向けdefaultを設ける。実際に影響したファイルだけを変更対象とする。

## 8. 実装方針

### 8.1 専用summary

`AnalysisDiagnosticsSummary` と `GenerationDiagnosticsSummary` は変更せず、`OutputDiagnosticsSnapshot` に次を追加する。

```text
WhisperModelDiagnosticsItem
  model_key
  display_name
  size_bytes
  vram_hint
  speed_hint
  recommended_use
  expected_manifest_identity
  availability_status
  availability_failure_code

WhisperDiagnosticsSummary
  models
  selected_model_key / display_name / manifest_identity / availability_status
  active_model_key / display_name / manifest_identity / availability_status
  loaded_model_key / display_name / manifest_identity
  analysis_model_key / display_name / manifest_identity
  manifest_schema_version
  package_name
  package_version
  package_gate_status
  availability_scan_status
  availability_scan_failure_code
  management_operation / management_phase
  management_busy / management_job_id
  management_model_key
  management_received_bytes / management_expected_bytes
  management_failure_code / management_cleanup_status
  active_config_status / active_config_reason
  panel_revision
  analysis_rebuild_reason
  failure_class
  failure_detail_code
  safe_failure_notice
  recoverability
  analysis_identity_status
  runtime_identity_status
  storage_location_kind
  storage_location_display
  application_busy
  transcription_text_present
  transcription_edit_available
  preview_projection_status
```

`package_version` は、manifestが要求する `openai-whisper` version `20250625` を意味する。これは `whisper_models.json` / `EXPECTED_WHISPER_VERSION` から得る表示用の要求版であり、実際にimport済みのpackage version、現在loaderが保持するmoduleのversion、またはloader gate通過済みという意味にはしない。`package_gate_status` は `not_checked | passed | failed` を区別し、B5のloaded identityが存在してruntime load成功が確定した場合だけ `passed` とする。loaded identityがなくload未実施なら `not_checked`、`whisper_version_mismatch` / package欠落等のB5 detail codeがある場合は `failed` とする。表示のためにWhisperをimportしたりbackground probeを追加したりしない。

単一の `identity_status` は設けない。`analysis_identity_status` はactive対analysisのsemantic identityを、`runtime_identity_status` はactive対loadedのruntime identityを表す。両fieldは `not_applicable | consistent | incomplete | mismatch` を基本とし、runtime側はloadedが明示的に存在しない状態を `unloaded` として区別できるようにする。manifest identityはselected / active / loaded / analysisを一つのfieldへ潰さず、比較可能なまま保持する。

`OutputDiagnosticsSnapshot` には `projection_generation: int` を追加する。legacy test / callerのdefaultは0とし、wx MainFrameではUI thread上の単調増加値を渡す。この値もfingerprintへ含めない。

現行API境界は次のように拡張する。

```text
WhisperModelSelectionState + UiStateの投影入力
  -> build_output_diagnostics_snapshot_from_ui_state(..., projection_generation=N)
     1. UiStateから一回だけWhisperDiagnosticsSummaryを構築
     2. transcription / Preview同期入力を同じ読取りで確定
  -> DiagnosticSnapshotInput(
       ...,
       whisper_summary=exact_summary,
       projection_generation=N,
     )
  -> build_output_diagnostics_snapshot(snapshot_input)
  -> OutputDiagnosticsSnapshot(
       ...,
       whisper_summary=snapshot_input.whisper_summary,
       projection_generation=snapshot_input.projection_generation,
     )
```

`DiagnosticSnapshotInput` には末尾default fieldとして `whisper_summary: WhisperDiagnosticsSummary = WhisperDiagnosticsSummary()` と `projection_generation: int = 0` を追加し、summary型と、generationがboolではない非負intであることを `__post_init__` で検証する。default summaryは `not_applicable` / 空modelsのimmutable値とする。`build_output_diagnostics_snapshot()` は受け取ったexact summary / generationを再計算せず `OutputDiagnosticsSnapshot` へそのまま渡す。`OutputDiagnosticsSnapshot` 側にも同じimmutable defaultを設けてlegacy direct constructorを壊さない。builder完成後の `dataclasses.replace()`、別builder、二回目のUiState参照による後付けは禁止する。

### 8.2 summary組立とfail-closed

summaryは `output_diagnostics_adapter.py` で `WhisperModelSelectionState` と、同じUiState読取りから得たUI投影入力を一度だけ組み立てる。同じbuild中に再度live stateを読み直さない。RightPaneが現行表示・操作判定に必要とする次のsafe値を不足なくsummaryへ入れる。

- model別のkey、表示名、exact size、VRAM目安、速度目安、推奨用途、expected manifest identity、artifact status、failure code。
- selected / active / loaded / analysisのkey、表示名、manifest identity、selected / active availability。
- availability scan status / failure code、safe notice、storage kind / safe display。
- `panel_revision`、`active_config_status`、safeな `active_config_reason`。
- management busy / operation / phase / job id / model key / received bytes / expected bytes / failure code / cleanup status / safe notice。
- application Busy、transcription text presence、transcription edit availability、Previewの `ready | analysis_required | unavailable` 投影状態。

`main_frame.py` はsummaryだけから `WhisperModelPanelState` を作り、RightPaneへ渡す。panel描画またはbutton enablementのために `self.ui_state.whisper_model_selection` や `self.ui_state.is_busy` を再参照しない。transcription controlsもsummaryの `transcription_text_present` / `transcription_edit_available` を使い、Preview placeholder / 表示可否もsnapshotのanalysis / saveability / semantic identity / `preview_projection_status` と、同じ同期開始時に確定済みの `UiSyncContext` だけを使う。consumerがsnapshot構築後のraw stateを直接再参照して表示を上書きすることを禁止する。

次の条件でidentityを評価する。

- `analysis_identity_status` はactiveとanalysisのmodel key + manifest identityだけを比較する。両方揃って一致すれば `consistent`、必要値が欠ければ `incomplete`、値が異なれば `mismatch` とする。このsemantic identityを既存analysis result / Preview / VMD saveabilityの正本とする。
- `runtime_identity_status` はactiveとloadedのmodel key + manifest identityだけを比較する。loaded key / manifestがともに `None` の明示unload状態は `unloaded`、片方だけ欠ければ `incomplete`、値が異なれば `mismatch` とする。
- `analysis_identity_status=incomplete | mismatch` の成功解析は既存ERRORへ投影し、VMD保存不可にする。旧modelを現在の成功modelとして表示しない。
- `runtime_identity_status=unloaded` だけでは、semantic identityがconsistentな既存analysis、Preview、VMD saveabilityを無効化しない。B5のroot変更等でruntimeがunloadされても、immutableな既存解析結果のprovenanceは変えない。
- `runtime_identity_status=incomplete | mismatch` は診断表示するが、それだけを既存VMDのblocking `DiagnosticItem` にしない。新規解析開始、runtime lease取得、または新規解析成功commit時にverified active requestとの一致を再検証し、不一致なら開始または成功commitをfail-closedにする。
- catalogもactive manifestもないlegacy fixture / callerは `not_applicable` とし、B6追加だけで既存非Whisperテストや呼出しをfailさせない。
- selected != active、selected未配置、candidate download中は候補状態であり、active / analysis identityがconsistentなら既存VMD保存可否を変更しない。
- Apply成功後の `model_changed` では新active modelの解析成功まで `analysis` identityを成功表示せず、Preview placeholderとVMD保存不可を維持する。

### 8.3 failure / recoverability投影

既存detail codeと `format_whisper_failure_notice()` を使い、raw exceptionを通常投影へ渡さない。最低限、次の写像を固定する。

| 状態 | failure class / source | severity | recoverability | 旧成功結果 |
| --- | --- | --- | --- | --- |
| selected model未配置 | candidate availability | warning | `retry_possible` | active identityが有効なら維持 |
| download / verify中 | management state | info | `retry_possible` | 維持 |
| candidate download cancel | management stateだけ。active `failure_class` は変更しない | info / safe notice | `cancelled_by_user` | 維持 |
| active model未配置 | `model_unavailable` | error | `retry_possible` | 復元しない |
| SHA256 / identity不一致 | `integrity_mismatch` | error | `retry_possible` | 復元しない |
| load失敗 | `load_failure` | error | `retry_possible` | 復元しない |
| memory不足 | `memory_failure` | error | `retry_possible` | 復元しない |
| transcribe失敗 | `transcribe_failure` | error | `retry_possible` | B5どおり復元しない |
| model変更commit後のcancel | `cancelled` + `model_changed` | `cancelled`をsummaryへ保持し、既存の`analysis_rebuild_required`をERRORとして投影 | `cancelled_by_user` | 復元しない |
| 同一model通常解析のcancel | rollback可能なら `none`。既存 `analysis_cancelled` INFOで表現 | info | `cancelled_by_user` | B5のidentity一致条件を満たす場合だけrollback可能 |
| storage root書込不可 | management detail code | error | `select_file_again` | candidate処理前の旧結果は維持 |
| settings保存失敗 | management detail code | error | `select_file_again` | 元の保存先・旧結果を維持 |

この表のcandidate / management行にあるseverityは、summary内のsafe notice、Info、Whisper panel、必要な直接 `MessageBox` の表示レベルを意味し、`DiagnosticItem` 追加を意味しない。candidate未配置、download、cancel、storage / settings管理失敗を含むmanagement状態は `snapshot.items` へ追加しない。active解析をblockingするfailureまたはsemantic identity不一致だけを既存ERROR itemへ投影する。

rollback非許可classは `analysis_rollback.py` の公開helper / constantを正本とし、`main_frame.py` と診断adapterで同じ定義を使う。B6で別の文字列集合を作らない。

TEXT + 音声とvoice-onlyは同じWhisper failure class / detail code / recoverabilityを使用する。入力modeによって案内文の導入部分は変えてよいが、rollback可否、saveability、identity表示は変えない。

cancelはB5の状態契約をそのまま投影する。

- 同一active modelの通常解析cancelでB5 rollbackが成立した場合、active `failure_class` は `none` に戻し、cancelの事実は既存 `analysis_cancelled` INFOだけで表す。復元されたsemantic identity、Preview、saveabilityをcancel classで再び無効化しない。
- candidate download / Apply preflightのcancelはmanagement operation / phase / safe noticeだけへ記録し、active `failure_class` を上書きしない。candidate状態だけを `snapshot.items` へ追加しない。
- model変更commit後の非復元cancelだけは `failure_class=cancelled` を保持する。`analysis_rebuild_reason=model_changed` / `analysis_pending_rebuild` を正本として既存 `analysis_rebuild_required` ERROR、Preview placeholder、VMD保存不可を維持し、old success snapshotを復元しない。

### 8.4 privacy境界

- `WhisperDiagnosticsSummary` にはraw storage path、URL、例外文字列、traceback、環境変数、認証情報を格納しない。
- availability / management failureはstable detail codeとsafe noticeを格納する。
- Info、Warning、Whisper panel、diagnostic report、wx `MessageBox` はsummaryまたはstable detail codeから生成したsafe値だけを使用する。
- B5の例外chainや `WhisperModelSelectionState` に原因解析用raw detailを内部保持することは許容する。ただしWhisper / storage / management経路では、そのraw値を `DiagnosticFailureInput.detail`、`DiagnosticItem.detail`、snapshot、Info、Warning、report、voice-only notice、TEXT + 音声の `MessageBox` へコピーしない。通常投影はfailure class + stable detail code + safe noticeへ正規化する。
- file dialogやstorage修復操作では、ユーザーが選択対象を確認するため内部canonical pathを使用できる。ただし診断snapshotへ複製しない。
- 既存Input sectionが扱う入力ファイルpathの契約はB6で変更しない。B6のprivacy修正はWhisper storage / loader / management経路へ限定する。

### 8.5 単一snapshot / 世代同期

`MainFrame.build_and_store_output_diagnostics_snapshot()` がgenerationを一つ進め、その値をadapterの `projection_generation` へ渡し、返したexact snapshotを一回のUI同期で次へ渡す。generation increment、Whisper summary構築、snapshot storeはUI thread上で一つのcommitとして扱う。

- VMD save action state
- Info
- Warning / error notice
- Whisper model panel
- Preview placeholder /表示可否
- transcription edit / revert controls

report saveとVMD saveは各action開始時にsnapshotを一度だけ構築し、そのactionの判定と出力へ同じobjectを使用する。途中で再buildしない。VMD saveはsnapshotのsemantic `analysis_identity_status` と既存 `saveability` を使用し、保存dialogを開いた後にloaded stateだけを再参照して拒否しない。内部file dialog default pathはUiStateのcanonical pathをaction内部で使用できるが、snapshot表示値とは別境界に保つ。

availability scan、download / verify完了、cancel、delete、Apply成功 / 失敗、解析成功 / 失敗 / cancelはUiState更新完了後に一度syncする。job id / generationによってdiscardされたlate callbackはsnapshot generationを進めず、Infoやpanelを更新しない。

### 8.6 fingerprint非変更

現行 `build_save_state_fingerprint_payload()` は、`snapshot.items` の全 `DiagnosticItem` identityを `diagnostic_identities` としてpayloadへ含める。この既存挙動を前提に、candidate unavailable、download / verify / cancel、management operation / progress / cleanup、scan状態、storage表示等を `snapshot.items` へ追加しない。これらは `WhisperDiagnosticsSummary`、safe notice、Info、Whisper panelだけへ限定する。

active analysisをblockingするfailure、またはactive対analysisのsemantic `incomplete | mismatch` は、既存 `analysis_failure` / `analysis_rebuild_required` 等のERRORへ投影できる。この場合は既存 `DiagnosticItem` identityが変化し、payload / digestが変わる、または既存builder条件に従ってfingerprintが `None` になることを意図したfail-closed結果として受け入れる。fingerprintを維持するためにERROR itemを隠さない。

`build_save_state_fingerprint_payload()` は `WhisperDiagnosticsSummary` と `projection_generation` を直接参照しない。schema constantは厳密に `ms21-effective-output-v1` のままとし、schema constant、payload field、canonical順序、builder filterを不要に変更しない。

effective outputとsemantic active / analysis identityが同じ条件では、selected、candidate availability、availability scan、management operation / progress / cancel / cleanup、loaded表示 / runtime unload、safe storage label、safe notice、panel revision、projection generationだけが変わっても、`snapshot.items`、fingerprint payload、digestが変わらないことをテストする。対照としてsemantic mismatchまたはactive blocking failureでは、既存DiagnosticItem経路によるpayload / digest変更またはfingerprint無効化を固定する。

## 9. 詳細ステップ

1. `output_diagnostics.py` に新規DTO、validation、legacy defaultを追加する。`DiagnosticSnapshotInput` と `OutputDiagnosticsSnapshot` の末尾へ `whisper_summary` / `projection_generation` を追加し、core builderがexact値を透過的に受け渡す。
2. active対analysisの `analysis_identity_status` とactive対loadedの `runtime_identity_status` を別helperで評価する。semantic `incomplete` / `mismatch` だけを既存blocking diagnostic itemへ写像し、runtime `unloaded` / mismatchは既存結果のsaveabilityから分離する。
3. candidate / management / loaded表示専用状態を `snapshot.items` へ追加しない。fingerprint builderがsummary / generationを参照しないこと、schema constant / payload builderを変更していないことをcode reviewとgolden testで固定する。
4. `core/__init__.py` へ新規DTOをexportする。
5. `ui_state.py` にstorage location kindを追加し、既存safe notice mapへ不足するload / integrity / memory / cancel案内を追加する。
6. `app_controller.py` で既定・ユーザー指定storageを区別し、raw pathとsafe表示メタデータを分離する。
7. `output_diagnostics_adapter.py` の `build_output_diagnostics_snapshot_from_ui_state(..., projection_generation=0)` で、model specs、availability、selected / active / loaded / analysis identity、B5 failure、panel / management / storage、Busy、transcription、Preview入力を一回だけ読み、immutable summaryを構築して `DiagnosticSnapshotInput` へ渡す。
8. Whisper failureの `DiagnosticFailureInput` をstable code、safe summary / detail、既存recoverabilityで構築する。raw detailは内部state / exception chainへ残せるが通常投影へ渡さない。非Whisper failureの既存挙動は、Whisper / storage / auth情報を漏らす場合を除き変更しない。
9. `analysis_rollback.py` にrollback非許可class / helperを置き、`main_frame.py` の重複literal判定を置換する。
10. `voice_only_errors.py` のWhisper経路をsafe noticeへ接続し、raw exception連結を止める。
11. Info formatterとdiagnostic reportへ `[Whisper]` sectionを追加する。
12. RightPaneがraw UiStateではなく同一generationのsummaryから全model item、panel revision、active config、management / cleanup、safe notice、Busyを取得するよう変更する。
13. MainFrameの一回の同期でgenerationをincrementし、exact snapshotをsave action、Info、Warning、Whisper panel、Preview、transcription controlsへ渡す。Previewは同じ同期開始時の `UiSyncContext` だけを併用し、Whisper raw stateを再参照しない。
14. candidate操作、Apply、解析、cancel、late callback、report / VMD saveの各経路がsnapshotを二重構築していないか監査する。
15. B6専用testsを追加し、`tests/test_ms20_b5_warning_save_policy.py` のraw Whisper detail期待をsafe detail期待へ更新したうえで、影響する既存testsを最小修正する。
16. targeted tests、関連回帰、全pytest、compileall、`git diff --check` を順に実行する。
17. ユーザーへ手動GUI確認事項を提示し、結果確認後に関連文書を実績へ同期する。

## 10. 状態遷移 / データ契約

### 10.1 identity

```text
candidate selection
  selected changes
  active / loaded / analysis unchanged
  existing success remains usable when identities are consistent

Apply preflight failure / cancel
  selected may be restored to active
  active / loaded / analysis unchanged
  existing success remains usable

Apply commit succeeds
  active changes
  analysis_rebuild_reason = model_changed
  old analysis success / Preview / VMD saveability disabled

new analysis succeeds
  active == analysis key and manifest
  analysis_identity_status = consistent
  loaded identity was verified at success commit
  runtime_identity_status = consistent
  Preview / VMD saveability follow existing success contract

runtime unload after successful analysis
  loaded key / manifest = None
  runtime_identity_status = unloaded
  analysis_identity_status remains consistent
  existing Preview / VMD saveability remains unchanged
  next analysis must reacquire and revalidate active runtime before start

runtime identity mismatch
  runtime_identity_status = incomplete or mismatch
  expose safe diagnostic status without changing old semantic provenance
  reject a new analysis start or success commit fail-closed
  do not disable an existing VMD solely because loaded state changed

blocking analysis failure
  failure class retained in summary
  loaded / analysis success identity is not presented as current success
  rollback prohibited

same-model analysis cancel with valid rollback
  restore existing semantic result
  failure_class = none
  expose existing analysis_cancelled INFO

candidate management cancel
  update management phase / safe notice only
  active failure_class and existing semantic result unchanged

post-commit model_changed cancel
  failure_class = cancelled
  analysis_rebuild_required ERROR remains
  Preview / VMD saveability remain disabled
```

### 10.2 snapshot freshness

```text
UiState mutation completed
  -> build snapshot generation N once
  -> store current_output_diagnostics_snapshot = snapshot N
  -> project snapshot N to all consumers

late callback rejected
  -> no UiState commit
  -> no generation increment
  -> no projection
```

consumerは受け取ったsnapshotより新しいlive UiStateを個別参照してWhisper表示やsaveabilityを上書きしない。

### 10.3 saveability

- 既存saveability判定を正本とする。
- active / analysisのsemantic identityがMS24管理状態で `incomplete` / `mismatch` の場合はERROR itemを追加し保存不可にする。
- loadedが `None` の明示unload、またはactive / loadedのruntime identity表示だけでは、semantic identityがconsistentな既存VMDを保存不可にしない。runtime mismatch / incompleteは新規解析開始または成功commitをfail-closedにする。
- candidateだけの未配置、download、cancel、storage write failureは、active / analysis identityがconsistentな旧成功結果の保存可否を変えない。
- rollback非許可failure後は旧snapshotを再storeしない。
- transcription editによるretained timing再利用は、B5のsame-model identityと `transcription_edit` 条件を変更しない。

### 10.4 report / Info

InfoはMMD利用者が現在状態を判断できる簡潔な表示とする。診断レポートは同じsummaryを使い、full manifest identity、stable failure detail code、generationを出力できる。両者のresolved model keyは一致しなければならない。

## 11. テスト方針

### 11.1 `test_ms24_whisper_diagnostics.py`

- summaryのdefault / validation / immutable契約。
- `DiagnosticSnapshotInput -> build_output_diagnostics_snapshot -> OutputDiagnosticsSnapshot` が同じsummary object / generationを透過的に渡し、legacy defaultが既存direct constructorを壊さない。
- small / medium / turboのkey、表示名、exact size、VRAM目安、速度目安、推奨用途、manifest / availability投影。
- `package_version` がmanifest要求版 `20250625` を示し、未loadでは `package_gate_status=not_checked`、loaded identity確定時だけ `passed`、version failure時は `failed` になる。表示目的のimport / loader起動がない。
- selected / active / loaded / analysisの一致、不一致、欠落と、`analysis_identity_status` / `runtime_identity_status` の独立評価。
- loadedが `None` のruntime unload後もsemantic identityがconsistentなら既存saveabilityを維持し、新規解析開始時のruntime mismatch / incompleteはfail-closedになる。
- selected != activeを正常候補状態として扱う。
- candidate unavailable / downloading / cancelledでもconsistentな旧成功saveabilityを維持する。
- Apply後 `model_changed` のold success表示・Preview・保存禁止。
- Info、RightPane、report、VMD save action、Preview、transcription controlsが同じsnapshot / generationから更新され、snapshot構築後にraw Whisper UiStateを変更しても当該投影世代の表示が混在しない。
- RightPaneがsize、VRAM、速度、推奨用途、panel revision、active config、management / cleanup、Busyをsummaryだけから取得する。
- transcription text presence / edit availabilityとPreview projection statusがsnapshot入力として固定される。
- Infoとreportが同じsnapshotから同じresolved keyを出す。
- storage表示が既定・ユーザー指定のsafe labelになり、絶対パスを含まない。
- raw exception、URL query、credentialらしい文字列をInfo / report / Warningへ出さない。
- effective outputとsemantic identityが同じ場合、selected、candidate availability、scan、management operation / progress / cancel / cleanup、loaded表示 / unload、safe storage label / notice、panel revision、generationを変更しても `snapshot.items`、`ms21-effective-output-v1` payload、fingerprintが変わらない。
- semantic active / analysis mismatchまたはactive blocking failureだけは既存ERROR itemへ投影され、既存builderどおりpayload / digestが変化するかfingerprintが無効になる。

### 11.2 `test_ms24_whisper_error_recovery.py`

- missing、download中、cancel、integrity、load、memory、storage write failureのseverity / recoverability / safe notice。
- TEXT + 音声とvoice-onlyでfailure class、rollback可否、saveabilityが一致する。
- `model_unavailable`、`integrity_mismatch`、`load_failure`、`memory_failure`、`transcribe_failure` でrollbackしない。
- precommit candidate cancel / failureは旧成功snapshotを維持する。
- postcommit `model_changed` cancelは旧成功snapshotを復元しない。
- same-model通常cancelはB5条件を満たす場合だけrollbackし、`failure_class=none` と既存 `analysis_cancelled` INFOを両立する。
- candidate cancelはmanagement stateだけを更新し、active `failure_class` とblocking `snapshot.items` を変更しない。
- failure後にold modelをloaded / analysis成功として表示しない。
- TEXT + 音声とvoice-onlyの双方で、内部raw detailを保持してもsnapshot / Info / Warning / report / `MessageBox` へ出さず、stable detail code由来のsafe noticeだけを表示する。

### 11.3 既存回帰

最小順序は次とする。

1. B6新規tests。
2. `tests/test_ms20_b5_warning_save_policy.py`。Whisper / storage / managementのraw detailを表示する旧期待をsafe detail期待へ更新し、DiagnosticItem identityとfingerprintの既存安定性を維持する。
3. MS20 diagnostics / report / save-flow tests。
4. MS19 voice-only error / lifecycle tests。
5. MS21 rollback / fingerprint tests。
6. MS24 model UI / apply / runtime tests。
7. MS23 profile / preset / morph lifecycle tests。
8. 全pytest。
9. `compileall` と `git diff --check`。

`tests/test_ms20_b5_warning_save_policy.py` では、既存の「Whisper raw detailが `DiagnosticFailureInput.detail` に残りWarningへ表示される」という期待を変更する。Whisper / storage / management経路はstable identityとsafe detailだけを通常投影へ渡し、raw detailは内部state / exception chainに保持されていてもsnapshotから到達不能であることをTEXT + 音声・voice-onlyの両方で固定する。非Whisperのlegacy detail表示は、Whisper storage path、auth情報、不要な環境情報を含まない限りB6で一律変更しない。

本リポジトリの開発・受入対象であるPython 3.14.3でWhisper互換性確認を行う。Python 3.11 / 3.12は今回の受入対象外として未検証扱いにする。

### 11.4 手動GUI確認

- 起動直後のInfoとWhisper panelに同じselected / active / loaded状態が出る。
- medium / turboを候補選択しても、Apply前の旧成功結果と保存可否が不必要に消えない。
- download、cancel、verify、delete後にpanelとInfoが同時に更新される。
- Apply and Re-analyze後、新model解析成功までPreviewとVMD保存が無効になる。
- TEXT + 音声とvoice-onlyの双方で成功・cancel・failure表示が整合する。
- integrity / load / memory failureの模擬経路でold successを復元しない。
- 保存先はsafe labelだけ表示され、絶対パスやraw exceptionがInfo / Warning / reportへ出ない。
- report保存内容と画面Infoのmodel keyが一致する。
- close中のlate callback、theme切替、再scanで古い表示へ戻らない。

actual MMD確認は行わずMS26へ引き継ぐ。

## 12. 受け入れ条件

- [ ] `OutputDiagnosticsSnapshot` が専用 `WhisperDiagnosticsSummary` を保持する。
- [ ] Whisper固有fieldを `AnalysisDiagnosticsSummary` / `GenerationDiagnosticsSummary` へ追加していない。
- [ ] selected / active / loaded / analysisのkey、表示名、manifest identityを区別できる。
- [ ] active対analysisのsemantic identityとactive対loadedのruntime identityを別fieldで判定し、単一 `identity_status` へ統合していない。
- [ ] loadedが `None` またはruntime unload済みであることだけでは、semantic identityがconsistentな既存VMDを保存不可にしない。runtime不一致は診断表示され、新規解析をfail-closedにする。
- [ ] `package_version` がmanifest要求版 `20250625` として表示され、実import済みversionやgate通過状態と混同されない。loaded identityが存在する場合だけ別 `package_gate_status` でgate通過を示す。
- [ ] manifest schema versionをInfo / reportで確認できる。
- [ ] Infoとreportのresolved model keyが同一snapshot上で一致する。
- [ ] candidate selection / availability / actual loaded model / analysis resultの不一致を検出できる。
- [ ] blocking failure後にold success summary、Preview、VMD saveabilityを復元しない。
- [ ] candidateだけの失敗・cancelはvalidなactive成功結果を破棄しない。
- [ ] rollback可能な同一model cancelは `failure_class=none` + 既存 `analysis_cancelled` INFO、candidate cancelはmanagement stateだけ、post-commit非復元cancelは `failure_class=cancelled` + `analysis_rebuild_required` ERRORになる。
- [ ] TEXT + 音声とvoice-onlyが同じfailure class / rollback契約を使う。
- [ ] storage write failureが `select_file_again` 相当のsafe actionへ写像される。
- [ ] Info、RightPane、report、error notice、VMD save action、Preview、transcription controlsが同一snapshot / generationから同期される。
- [ ] `DiagnosticSnapshotInput -> build_output_diagnostics_snapshot -> OutputDiagnosticsSnapshot` が同じWhisper summary / generationを透過的に渡し、全consumerがsnapshot構築後のraw Whisper UiStateを再参照しない。
- [ ] RightPaneに必要なsize、VRAM、速度、推奨用途、panel revision、active config、management / cleanup状態と、transcription presence / edit、Preview同期入力がsummaryに揃う。
- [ ] late callbackが古いgenerationを投影しない。
- [ ] 通常UI / reportへWhisper storage絶対パス、認証情報、raw exceptionを出さない。
- [ ] TEXT + 音声・voice-only双方で、内部raw detailが `DiagnosticFailureInput.detail` / snapshot / Info / Warning / report / `MessageBox` へ流出しない。
- [ ] candidate availability / management / cancel状態を `snapshot.items` へ追加せず、表示専用状態だけでは `ms21-effective-output-v1` payload / digestが変わらない。
- [ ] active blocking failure / semantic mismatchだけは既存ERROR item経路へ投影し、その既存fingerprint影響を維持する。schema constant / payload builderを変更していない。
- [ ] MS23固定モーフ、Latin profile、preset、model profile、既存VMD / voice-only契約の回帰がない。
- [ ] `pyproject.toml` / `requirements.txt` がともに `openai-whisper==20250625` のままである。
- [ ] Python 3.14.3を開発・受入環境として確認し、Python 3.11 / 3.12は未検証として記録する。
- [ ] cloud通信、自動download、Qt / PySide6、依存追加がない。

## 13. リスクと対策

- リスク: selectedとactiveの不一致をERROR扱いし、候補選択だけで旧結果が保存不能になる。
  - 対策: candidate状態とcommitted active / analysis identityを分けて判定する。
- リスク: loaded modelの残存値を成功modelとして表示する。
  - 対策: semantic active / analysisとruntime active / loadedを別statusにし、loadedだけでは既存結果のprovenanceやsaveabilityを決めない。
- リスク: rollback判定と診断表示のfailure class集合が乖離する。
  - 対策: `analysis_rollback.py` のhelperを両経路で共用する。
- リスク: summary追加でfingerprintが変わり、既存保存状態を壊す。
  - 対策: summary / generationをfingerprint builderから除外し、candidate / management表示を `snapshot.items` へ追加しない。active blocking ERRORだけは既存DiagnosticItem経路の影響を維持する対照テストを置く。
- リスク: raw exceptionやstorage pathがWarning / reportに残る。
  - 対策: stable detail codeからsafe messageを生成し、summary / `DiagnosticFailureInput.detail` にraw値を格納せず、`tests/test_ms20_b5_warning_save_policy.py` を更新する。
- リスク: manifest要求版を実際のimport済みpackageまたはloader gate成功として誤表示する。
  - 対策: `package_version` を要求版、`package_gate_status` を別fieldとし、loaded identity確定時だけgate通過を表示する。
- リスク: 一回のUI sync内でpanelとInfoが異なるstate世代を読む。
  - 対策: exact snapshot objectを全consumerへ引き回し、generationをテストする。
- リスク: legacy fixtureへMS24 identityを必須化して無関係な回帰を起こす。
  - 対策: catalog / active manifestのないlegacy状態を `not_applicable` として互換維持する。
- リスク: Python 3.11 / 3.12の未検証範囲を、Python 3.14.3の開発・受入実績で検証済みと誤認する。
  - 対策: 開発・受入対象をPython 3.14.3に固定し、3.11 / 3.12は未検証として明記する。

## 14. Codex 実装時の注意

- 実装開始時にlive Git状態、B6 plan、B5実装、対象testsを再確認する。
- B5のruntime / loader / ownershipをB6で作り直さない。
- B5 stateを正本とし、診断側でmodel identityやfailure classを推測しない。
- `WhisperModelSelectionState` のraw failure detailやstorage pathを通常表示へ直接渡さない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` を直接読み取り・変更・stageしない。
- `ms21-effective-output-v1` の文字列、payload field、canonical順序を変更しない。
- MS23の固定morph、Latin profile、preset、diagnostics、fingerprint契約を維持する。
- long operation、cancel、close、late-result discardは既存wx worker契約を維持する。
- testを弱めたり削除したりしてfailureを回避しない。
- 新規依存を追加しない。依存変更が必要になった場合はB6を止め、別途ユーザー判断を得る。
- 実装後にdiffを自己監査し、B6外のproduction behavior、package、runtime dataへ変更がないことを確認する。
- stage、commit、push、merge、tag、releaseは各々の明示承認後に行う。

## 15. 実装・検証結果

- 2026-08-26にB6を実装した。`WhisperDiagnosticsSummary`、selected / active / loaded / analysis identityの分離、package version / gate status、safe failure分類、projection generation、Info / report / RightPaneの同一snapshot投影、model-aware rollbackの診断連携を追加した。
- B6専用・MS20 diagnostics / save policy回帰を含む全pytestは`881 passed, 2 skipped`、process exit code `0`だった。`compileall -q src tests`と`git diff --check`もprocess exit code `0`だった。
- ユーザーからB6手動GUI確認通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- Python 3.14.3の開発・受入ゲートはB7実施記録で確認済みであり、Python 3.11 / 3.12は今回未検証として扱う。実MMDでのVMD / WAV読み込み・リップ同期はMS26、MS27 package / release readinessはMS27へ引き継ぐ。
- B6のproduction code・test code変更は `1f1aff2 Implement MS24-B6 diagnostics and recovery` としてcommit済みであり、B6のstage / commitは完了している。push、merge、tag、releaseは未実施である。依存関係、runtime user data、Qt / PySide6、cloud ASR、音声外部送信、background通信は変更していない。
