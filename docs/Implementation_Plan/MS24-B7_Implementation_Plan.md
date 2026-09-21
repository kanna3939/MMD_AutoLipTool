# MS24-B7 Implementation Plan

## 1. 文書情報

- 対象Milestone: MS24 Whisper Model Selection
- 対象Block: MS24-B7 統合回帰・配布影響確認・Closeout準備
- 更新日: 2026-08-28（P2/P3レビュー補正）
- 対象ブランチ: `feature/MS23-implementation`
- 計画作成時HEAD: `1f1aff2 Implement MS24-B6 diagnostics and recovery`
- 計画作成前のbaseline Git状態: clean
- 計画作成後の状態: 本書と関連routing文書のレビュー補正済み（`12ec286`としてコミット済み）
- 文書状態: Implementation Plan / B7実施記録。統合回帰・静的監査の実施結果を追記済み。Python 3.14.3開発・受入ゲート合格。MS24 Closeout A判定済み（2026-08-28）
- 計画作成時に変更したファイル: 本書のみ。今回のP2/P3補正では関連routing文書も変更対象とする

## 2. 背景

MS24-B1からB6は、versioned manifest、verified-local loader、保存先とavailability、モデル選択UI、明示的なforeground download、解析runtime、identity伝播、diagnosticsとerror recoveryまで実装済みである。B6実装後の全pytestは `881 passed, 2 skipped`、`compileall -q src tests` と `git diff --check` はprocess exit code `0`で、ユーザーから手動GUI確認通過・問題なしの報告を受領している。

計画作成時点では、次が未完了であった。

- Python 3.14.3でのWhisper互換性確認。現行 `.venv` を本リポジトリの開発・受入環境とし、Python 3.13.xは必須ゲートとしない。
- B1からB6を同一HEADで再確認するcross-boundary回帰。
- PyInstaller spec、package-data、license、利用者向け文書のMS24影響監査。
- MS24のfinding ledgerとCloseout判定。

actual MMDでのVMD / WAV読み込み・リップ同期はMS26、onefile build、SmokeLaunch、ZIP内容、公開可否を含むpackage / release readinessはMS27の責務である。

## 3. 目的

1. B1からB6の要求、現行実装、テスト、設定、文書を同一HEADへ対応付ける。
2. state、semantic/runtime identity、fingerprint、rollback、network、GUI、workerの境界を横断回帰する。
3. manifestだけがpackage対象で、model weightsがsource、Git、onefile指定へ入らないことを静的に確認する。
4. Python 3.14.3をWhisper互換性の開発・受け入れgateとして実行・記録する。
5. dependency、license、利用者向け取得手順、配布影響を文書へ同期する。
6. P1 / P2 / P3、未確認事項、ユーザーGUI証拠を記録し、MS24 Closeout可否を判定できる状態にする。

## 4. In Scope

- B1からB6のrequirement-to-evidence ledger作成。
- MS24専用test、Whisper timing、TEXT + 音声、voice-only、settings、diagnostics、rollback、wx lifecycleの再実行。
- `small / medium / turbo`、既定 `small`、manifest identity、exact size、SHA256、公式URL、filenameの整合確認。
- verified-local checkpoint専用loader、v20250625 version / alignment-head gate、word timestamp / segment fallbackの回帰。
- selected / active / loaded / analysis / retained identityと、semantic identity / runtime identityの分離確認。
- `WhisperDiagnosticsSummary`、`projection_generation`、safe failure、model-aware rollback、VMD saveabilityの横断確認。
- `ms21-effective-output-v1` fingerprint schema / payload非変更の確認。
- 明示確認後のforeground downloadだけを許し、解析時の暗黙download、cloud ASR、音声送信、background通信がないことの確認。
- availability、management、apply、analysis workerの分離、Busy、cancel、job / generation、late result、shutdownの確認。
- PyInstaller / setuptoolsのmanifest配置とmodel weights非同梱の静的監査。
- `openai-whisper==20250625`の依存値同期、license文書、README、配布説明の確認と必要な文書同期。
- Python 3.14.3 development / acceptance compatibility gate。
- ユーザー手動GUI証拠の監査と、証拠不足箇所だけの限定再確認。
- finding分類、Closeout文書同期、次工程handoff。

## 5. Out of Scope

- production code、test code、GUI、依存関係の変更。
- failing testやcontract gapのB7内修正。必要な修正は別のrepair plan / repair implementationへ分離する。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読み取り、変更、作成、削除、fixture化、stage。
- 実モデル重みのrepo配置、Git追跡、onefile同梱。
- 起動時・解析時・候補選択時の自動download。
- Qt / PySide6復活、cloud ASR、音声外部送信、telemetry、background通信。
- 実MMDでのVMD / WAV読み込み・リップ同期。MS26へ延期する。
- onefile build、SmokeLaunch、配布ZIP生成、成果物内容の最終確認、version決定、release readiness。MS27へ延期する。
- push、merge、tag、release、branch削除。
- MS22 Closeout A、MS23 Closeout A、MS24-B1からB6の完了状態の巻き戻し。

## 6. 前提条件

- B1実装commit: `eafdc16 Implement MS24-B1 Whisper model contract`
- B2実装commit: `b011b37 Implement MS24-B2 model storage core`
- B3実装commit: `a27a26f Implement MS24-B3 model selection UI`
- B4実装commit: `0a119cb Implement MS24-B4 model management`
- B5実装commit: `78172d9 Implement MS24-B5 model runtime integration`
- B6実装commit: `1f1aff2 Implement MS24-B6 diagnostics and recovery`
- 現行実測環境: Python 3.14.3、openai-whisper 20250625、torch 2.13.0+cpu、PyInstaller 6.19.0、wxPython 4.2.5。
- Python 3.14.3 executable、環境、実行結果はB7実施時に確認済みである。Python 3.13.xは本リポジトリ開発の必須ゲートとしない。
- `pyproject.toml`の`requires-python = ">=3.11"`は配布メタデータの下限であり、Python 3.11 / 3.12の互換性を検証済みとするものではない。MS24の開発・受入対象はPython 3.14.3とする。
- Python 3.14.3 gateとpackage static auditはB7実施時に確認済みであり、MS24 Closeout判定は別途行う。
- Python 3.14.3環境は現行のrepo内`.venv`を使用した。別環境の導入やnetwork取得は行わない。
- B7開始時にworking treeがcleanでない場合、既存変更のownerとscopeを確認し、意図不明の変更があれば監査を開始しない。
- pytestはpass表示とprocess exit code `0`の両方を合格条件とする。

## 7. 対象ファイル

### 7.1 実在確認済み・read-only実装証拠

- B1: `src/core/whisper_models.py`、`src/core/whisper_models.json`、`src/core/whisper_model_loader.py`
- B2: `src/core/whisper_model_store.py`、`src/core/settings_store.py`
- B3: `src/gui_wx/ui_state.py`、`src/gui_wx/right_pane.py`、`src/gui_wx/main_frame.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/whisper_availability_worker.py`
- B4: `src/core/whisper_model_downloader.py`、`src/gui_wx/model_download_worker.py`
- B5: `src/core/whisper_model_runtime.py`、`src/core/whisper_timing.py`、`src/core/pipeline.py`、`src/gui_wx/analysis_worker.py`、`src/gui_wx/model_apply_worker.py`、`src/gui_wx/analysis_rollback.py`
- B6: `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、`src/gui_wx/output_diagnostics_adapter.py`、`src/gui_wx/voice_only_errors.py`

### 7.2 実在確認済み・direct test証拠

- `tests/test_whisper_model_catalog.py`
- `tests/test_whisper_model_loader.py`
- `tests/test_whisper_model_store.py`
- `tests/test_whisper_model_downloader.py`
- `tests/test_whisper_timing.py`
- `tests/test_ms24_no_implicit_download.py`
- `tests/test_ms24_whisper_model_ui_state.py`
- `tests/test_ms24_whisper_model_availability_worker.py`
- `tests/test_ms24_b4_controller.py`
- `tests/test_ms24_model_download_worker.py`
- `tests/test_ms24_whisper_model_runtime.py`
- `tests/test_ms24_whisper_model_apply.py`
- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_ms24_whisper_error_recovery.py`
- `tests/test_wx_ms24_whisper_model_ui.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_import_boundaries.py`
- `tests/test_ms23_b3_model_profiles.py`
- `tests/test_ms23_b4_model_profile_state.py`
- `tests/test_ms23_b4_settings_save.py`
- `tests/test_ms23_b4_profile_history.py`
- `tests/test_ms23_b4b_wx_teardown.py`
- `tests/test_wx_ms23_b4_profile_runtime.py`
- `tests/test_ms23_b5_model_profile_controller.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_wx_ms23_b5_model_profile_ui.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms17_b7_mmd_wav_export.py`
- `tests/test_ms17_b7_mmd_wav_save_dialog.py`
- `tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`
- `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
- `tests/test_ms17_b7_mmd_wav_button_state.py`

### 7.3 実在確認済み・設定 / package / license証拠

- `pyproject.toml`
- `requirements.txt`
- `MMD_AutoLipTool.spec`
- `build.ps1`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/Release_Package_Manifest.md`
- `LICENSE`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`

### 7.4 B7実施時の文書変更候補

次はB7実施権限が別途与えられ、監査結果が確定した場合だけ変更する。現時点では候補である。なお、今回のP2/P3レビュー補正で行うB6 commit状態、B7 plan link、責務表現のrouting同期は、このB7実施時の文書変更とは分離して扱う。

- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS24_Block_Breakdown.md`
- `docs/Implementation_Plan/MS24-B6_Implementation_Plan.md`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/Release_Package_Manifest.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
- `THIRD_PARTY_LICENSES.md`、`NOTICE`は確認対象。現在の記載で十分なら変更しない。

B7専用test fileは作成候補にしない。既存testでmaterial contractを証明できない場合はP2としてrepairへ戻す。

## 8. B1からB6のcross-boundary契約

| 境界 | 不変条件 | 主な証拠 |
| --- | --- | --- |
| catalog / manifest | `small / medium / turbo`だけを許可し、既定は`small`。version、URL、filename、size、SHA256はversioned manifestが正本 | B1 catalog / loader tests |
| loader / network | B2が生成した`VerifiedWhisperCheckpoint`をB1 loaderへ渡し、loader自身が同一open handleでsize / SHA256を再検証して得たbytesだけをloadする。解析経路はnetwork-unreachableで暗黙downloadしない | loader、store、no-implicit-download tests |
| alignment / timing | openai-whisper 20250625とprivate alignment-head契約が一致しない場合はfail closed。word timestampとsegment fallbackを維持 | loader、timing tests |
| state | selected candidateはactive modelを変更しない。Apply成功時だけactiveをcommitし、旧analysisの再利用可否をidentityで決める | UI state、apply tests |
| identity | semanticなactive / analysis identityとruntimeのactive / loaded identityを分離する。runtime unloadだけでsemantic結果を無効化しないが、新規解析はruntime mismatchでfail closed | runtime、diagnostics tests |
| fingerprint | `WhisperDiagnosticsSummary`、candidate、management、loaded表示、`projection_generation`を`ms21-effective-output-v1`へ追加しない。semantic mismatch / blocking ERRORだけは既存DiagnosticItem経路へ反映 | diagnostics、save-policy tests |
| rollback | model unavailable、integrity mismatch、load、memory、transcribe failureでは旧analysisを復元しない。同一modelの通常cancelだけB5条件で復元可能 | rollback、error-recovery tests |
| management | downloadは明示確認後のforeground処理。cancel / partial cleanup / exact size / SHA256 / redirect拒否をB4 workerで処理し、deleteはB5 ownership permitを必要とする | downloader、worker、controller tests |
| GUI / worker | availability、management、apply、analysisを分離し、Busy、job ID、scan / projection generation、shutdown、late callback discardを維持 | wx UI、availability、controller tests |
| existing product | 固定モーフ、Latin profile、preset / profile guard、30fps VMD、MMD用WAV、Preview、diagnosticsを変更しない | MS19からMS23回帰、pipeline / VMD tests |

## 9. 実装・検証順序

1. Git branch、HEAD、working tree、B1からB6 commitを確認する。
2. Roadmap、Block Breakdown、B1からB6 planと現行実装をrequirement-to-evidence ledgerへ対応付ける。
3. B1 / B2のcatalog、manifest、loader、store、download境界を限定testで確認する。
4. B3 / B4のsettings、state、availability、management worker、wx UI境界を確認する。
5. B5 / B6のruntime、TEXT + 音声、voice-only、identity、rollback、diagnostics、report、fingerprintを確認する。
6. MS23 profile / preset / fixed morph、MS21 rollback / fingerprint、MS19 voice-only、wx lifecycleの回帰を確認する。
7. 現行Python 3.14.3でMS24 aggregate、関連回帰、full pytest、`compileall -q src tests`、`git diff --check`を実行する。
8. Python 3.14.3 executableを明示し、version、dependency version、command、pass数、skip数、process exit codeを記録する。少なくともMS24 aggregate、Whisper timing、pipeline / voice-only、rollback、diagnostics、wx MS24を実行し、full pytestも実行する。
9. package / spec / licenseを静的監査する。
10. 既存のユーザーGUI証拠をcurrent HEADへ対応付ける。未被覆またはintervening behavior changeがある場合だけ限定GUI再確認事項を提示する。
11. findingをP1 / P2 / P3へ分類する。P1 / P2があればCloseout Aを停止し、repair条件を記録する。
12. 合格時だけ候補文書へ実績、manual確認主体、未検証、MS26 / MS27 boundary、次工程を同期する。
13. 最終diff、文書間の日付・HEAD・test値・Closeout判定を再確認する。

## 10. Package / spec / license確認

### 10.1 manifest-only / model weights非同梱

- `MMD_AutoLipTool.spec`のrepo固有datasは `src/core/whisper_models.json -> src/core`であることを確認する。
- `pyproject.toml`のpackage-dataは `core = ["whisper_models.json"]`であることを確認する。
- spec、package-data、tracked file、配布manifest候補に `models/`、`.pt`、`.bin`、`.part`等のmodel weightが追加されていないことを静的に確認する。
- `collect_data_files("whisper")`の列挙結果にmodel weightがないことを確認する。見つかった場合はP2以上として停止する。
- `collect_data_files("whisper")`の静的列挙はB7で実行する必須gateであり、生成onefile / Analysis TOC / ZIPの実内容確認はMS27へ延期する。B7文書補正だけではこのgateを合格扱いにしない。

### 10.2 dependency / license / user documentation

- `pyproject.toml`と`requirements.txt`がともに `openai-whisper==20250625`であることを確認する。
- 実行環境のopenai-whisper、torch、PyInstaller、wxPython versionを記録する。B7で更新しない。
- `THIRD_PARTY_LICENSES.md`のopenai-whisper MIT記載と、外部取得するmodel weightsをonefileへ含めない説明を照合する。
- READMEと配布用readmeへ、モデル候補選択、Download & Verify、Apply and Re-analyze、保存先、削除、通信範囲、解析時自動download禁止、安全な失敗表示を同期する。
- `docs/Release_Package_Manifest.md`へmanifest同梱、weights非同梱、外部`models`管理を反映する。ただしbuild / ZIP / release readinessの合格はMS27へ残す。
- PySide6の既存xref記録はMS24でQtを復活させた証拠とみなさない。actual artifactへの混入可否はMS27で確認する。

## 11. テスト・GUI方針

### 11.1 automated gate

- 最小単体: catalog、loader、store、downloader、runtime、timing。
- cross-boundary: no implicit download、UI state、availability、management worker、Apply、diagnostics、error recovery。
- product regression: TEXT + 音声、voice-only、profile / preset、rollback、fingerprint、Preview、VMD save policy、wx lifecycle。
- MS23 direct regressionは`tests/test_ms23_b2_morph_name_adapters.py`、`tests/test_ms23_b2_morph_name_sets.py`、`tests/test_ms23_b2_import_boundaries.py`、`tests/test_ms23_b3_model_profiles.py`、`tests/test_ms23_b4_model_profile_state.py`、`tests/test_ms23_b4_settings_save.py`、`tests/test_ms23_b4_profile_history.py`、`tests/test_ms23_b4b_wx_teardown.py`、`tests/test_wx_ms23_b4_profile_runtime.py`、`tests/test_ms23_b5_model_profile_controller.py`、`tests/test_ms23_b6_model_profile_lifecycle.py`、`tests/test_wx_ms23_b5_model_profile_ui.py`を対象とする。保持すべき既存timing経路は`tests/test_ms19_b3_textless_pipeline.py`と`tests/test_ms19_b5_transcription_edit_state.py`で確認する。
- product回帰では`tests/test_pipeline_and_vmd.py`、`tests/test_ms21_b3_pipeline_preview_integration.py`、`tests/test_ms21_b5_adjusted_vmd_save.py`、`tests/test_ms17_b7_mmd_wav_export.py`、`tests/test_ms17_b7_mmd_wav_save_dialog.py`、`tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`、`tests/test_ms17_b7_mmd_wav_failure_cleanup.py`、`tests/test_ms17_b7_mmd_wav_button_state.py`を明示的に実行する。
- full pytestはpass表示とprocess exit code `0`を必須とし、skipは理由を記録する。
- Python 3.14.3の成功を、本リポジトリの開発・受入compatibility evidenceとする。Python 3.11 / 3.12は今回の受入対象外で、互換性を検証済みとは扱わない。

### 11.2 user manual GUI evidence

B3、B4、B5、B6で受領済みのユーザー報告を証拠台帳へ対応付ける。Codex自身のGUI実行結果とは記録しない。次のどれかが未被覆なら、ユーザーへ限定再確認を依頼する。

1. 起動時にsmall / medium / turbo、selected / active、availabilityが整合して表示される。
2. 候補選択だけではdownload、active変更、既存Preview / VMD saveability変更が起きない。
3. Download & Verify、cancel、delete、保存先変更後のrescanが安全に完了する。
4. Apply and Re-analyzeでTEXT + 音声とvoice-onlyが同じmodel identityを使う。
5. network unavailable、missing / invalid model、load / memory / transcribe failureが自動downloadせずsafe failureになる。
6. cancel / failure後のrollback、Preview、diagnostics、report、VMD saveabilityが同じsemantic identityを示す。
7. worker実行中のcloseでlate resultやUI更新が残らない。

実MMDへのVMD / WAV読み込みはこのGUI確認に含めない。

## 12. 受け入れ条件

- [x] B1からB6のrequirement、commit、source、test、documentの証拠台帳が完成している。
- [x] `small / medium / turbo`、既定small、manifest metadata、verified-local loaderが回帰していない。
- [x] 解析時の暗黙download、cloud ASR、音声外部送信、background通信がない。
- [x] selected / active / loaded / analysis / retained identityとsemantic/runtime identity分離が維持される。
- [x] `WhisperDiagnosticsSummary`と`projection_generation`が全表示へ同じsnapshotとして投影される。
- [x] safe failure、model-aware rollback、VMD saveabilityがTEXT + 音声とvoice-onlyで一致する。
- [x] `ms21-effective-output-v1` schema / payloadが変更されていない。
- [x] availability / management / apply / analysis workerのBusy、cancel、stale、shutdown境界が回帰していない。
- [x] MS23 fixed morph、Latin profile、preset / profile、30fps VMD、MMD用WAVを壊していない。
- [x] 現行Python 3.14.3のaggregate / full regressionがprocess exit code `0`である。
- [x] 開発・受入対象Python 3.14.3のexecutable、version、dependency、対象test、process exit codeが記録され、互換性gateが合格している。
- [x] `pyproject.toml` / `requirements.txt`が `openai-whisper==20250625`で一致する。
- [x] spec / package-dataはmanifestだけを追加し、model weightsをsource、Git、onefile指定へ含めない。`collect_data_files("whisper")`の静的列挙にもmodel weightsがない。
- [x] dependency、license、README、配布説明がMS24の実装状態と一致する。
- [x] ユーザーGUI証拠の確認主体、対象、日付、未被覆項目が記録されている。
- [x] actual MMDをMS26、package / release readinessをMS27へ延期したままにする。
- [x] open P1 / P2がない。P3は解消済み、または影響とownerが記録されている。
- [x] Index、Roadmap、Block Breakdown、B6 planのB6 commit状態とB7結果が一致する。

## 13. P1 / P2 / P3リスクと対策

| ID | 分類 | リスク | 対策 |
| --- | --- | --- | --- |
| B7-R1 | P1 | 解析経路が暗黙downloadまたは外部送信へ到達する | network API未到達testとloader / runtime call pathを確認し、検出時はCloseout停止 |
| B7-R2 | P1 | model変更後に旧analysisをrollbackし、異なるidentityのVMDを保存できる | rollback禁止class、semantic identity、saveabilityのcross-boundary testを実行 |
| B7-R3 | P1 | integrity不一致のcheckpointをloadする | B2 DTO、loader自身の同一open handle再検証、検証済みbytes bindingの契約を再確認 |
| B7-R4 | P3 | Python 3.11 / 3.12の未検証範囲を3.14.3実績と混同する | 開発・受入対象を3.14.3と明記し、3.11 / 3.12互換性は別途未検証として扱う |
| B7-R5 | P2 | specやpackage-dataへmodel weightsが混入する | spec、collect_data_files、Git inventoryを静的監査し、成果物実確認はMS27へhandoff |
| B7-R6 | P2 | diagnostics追加でfingerprintが変わる | `ms21-effective-output-v1` golden / save-policy回帰を実行 |
| B7-R7 | P2 | worker late callbackやclose時処理でwx stateが壊れる | job / generation / shutdown / teardown回帰を現行HEADで実行 |
| B7-R8 | P2 | READMEやrouting文書がB6 working treeの旧状態を示す | `1f1aff2`、test値、manual主体、次工程へ同期する |
| B7-R9 | P2 | model取得・保存・削除・license説明が利用者向け文書にない | README、配布用readme、Release Package ManifestをB7文書同期対象にする |
| B7-R10 | P3 | historical test件数とcurrent件数を混在させる | command、HEAD、日時、pass / skip、exit codeを一組で記録する |
| B7-R11 | P3 | 既存PySide6 xref記録をQt復活と誤認する | source dependencyとartifact xrefを分け、最終artifact判断はMS27へ残す |

## 14. Codex実施時の注意

- B7は新機能実装ではなく、統合回帰、静的配布影響監査、文書同期、Closeout判定である。
- コマンドは一つずつ実行し、pass表示とprocess exit codeを別々に確認する。
- root runtime user data三点は読まない。testはtemporary path / injected storeだけを使う。
- P1 / P2を見つけた場合、production / test修正をB7へ混ぜず、finding、影響、repair範囲、再検証条件を報告する。
- P1 / P2が残る間はMS24 Closeout Aを宣言しない。
- 過去のB3からB6のGUI報告はユーザー確認としてのみ再利用し、Codexの実行結果としない。
- 開発・受入対象Python 3.14.3は既存`.venv`で確認する。Python 3.13.xの新規installやnetwork取得は行わない。
- build、SmokeLaunch、ZIP、release readinessへ進まない。MS27の権限を先取りしない。
- actual MMD確認を未実装findingとして扱わず、MS26 deferred-by-designとして記録する。
- push、merge、tag、releaseは明示承認なしに行わない。

## 15. ユーザー判断事項

現時点で計画書作成を止めるユーザー判断はない。次を推奨既定とする。

- Python compatibility: ユーザー判断により、本リポジトリの開発・受入対象をPython 3.14.3とする。Python 3.13.xは必須gateとせず、Python 3.11 / 3.12は今回の受入対象外として未検証扱いを維持する。
- GUI証拠: B3からB6のユーザー報告をcurrent evidence ledgerへ再利用し、契約未被覆またはintervening code changeがある項目だけ再確認する。
- finding対応: 今回のplan / routing上のP2/P3は文書同期とユーザー判断で解消する。Python 3.14.3 gate、`collect_data_files("whisper")` static audit、cross-boundary regressionなど実測が必要な受入gateは、B7実施結果で確認済みである。production / test変更が必要なP1 / P2は別repairへ分離する。
- Closeout: Python 3.14.3 gate、cross-boundary回帰、package静的監査、manual evidence監査を満たした後だけ判定する。

## 16. 計画作成時点の未確認事項

- Python 3.11 / 3.12 compatibilityは今回の開発・受入対象外であり、検証済みとは扱わない。
- 現行HEADでのB7 aggregate / full pytest再実行結果。B6時点の `881 passed, 2 skipped`はhistorical baselineであり、B7実施結果ではない。
- `collect_data_files("whisper")`の現行列挙内容。
- 本計画とrouting文書の補正だけでは、Python 3.14.3 gate、static package audit、cross-boundary regressionを検証済みとはしない。これらのB7実施結果は§18へ記録する。
- PyInstaller生成物、Analysis TOC、onefile、ZIPの実内容。MS27で確認する。
- actual MMDでのVMD / WAV読み込み・リップ同期。MS26で確認する。
- B7 Closeout判定と、B7実施後に必要となるfresh manual GUI項目の有無。

## 17. P2/P3レビュー補正記録

- 2026-08-28: MS23-B2〜B6の全直接回帰、保持すべきtiming経路、pipeline / VMD / MMD用WAVの既存回帰対象を具体的なtest fileとして明記した。
- 2026-08-28: B6のcommit済み状態（`1f1aff2`）と、計画作成前baselineのclean状態を区別して記録した。
- 2026-08-28: B2の`VerifiedWhisperCheckpoint` DTO、loader自身の同一open handle再検証、検証済みbytesへの束縛という責務境界へ文言を補正した。
- 2026-08-28: `requires-python >=3.11`のmetadata floorと、MS24のPython互換性受入gateを別契約として明記した。
- 計画作成時点ではPython 3.13.x実測、`collect_data_files("whisper")` static audit、列挙した回帰test、B7 Closeout判定が未実施だった。ユーザー判断により開発・受入対象をPython 3.14.3へ変更し、B7実施後の3.14.3 gate、static audit、列挙した回帰testは本書§18へ実績を記録した。

- 2026-08-28: ユーザー判断により、MS24の開発・受入環境をPython 3.14.3とし、Python 3.13.xを必須compatibility gateから外した。`pyproject.toml`の`requires-python >=3.11`は変更せず、Python 3.11 / 3.12は未検証扱いとした。

## 18. MS24-B7実施記録（2026-08-28）

### 18.1 自動検証

- MS24直接回帰（catalog、loader、store、downloader、timing、no implicit download、UI state、availability、management worker、runtime、Apply、diagnostics、error recovery、wx UI）: `76 passed, 2 skipped`、process exit code `0`。
- MS23 direct、MS19 voice-only、MS20 diagnostics、MS21 rollback / pipeline、pipeline / VMD、MS17 MMD用WAV回帰: `163 passed`、process exit code `0`。
- 現行HEADの全pytest: `881 passed, 2 skipped`、process exit code `0`。
- `tests/test_whisper_model_store.py`の2 skippedは、Windowsのsymlink作成権限不足（`WinError 1314`）によるもので、通常ファイルの検証回帰はpassした。
- `compileall -q src tests`: process exit code `0`。
- `git diff --check`: process exit code `0`。

### 18.2 依存・manifest・package静的監査

- 実測version: Python `3.14.3`、`openai-whisper 20250625`、`torch 2.13.0+cpu`、PyInstaller `6.19.0`、wxPython `4.2.5 msw (phoenix) wxWidgets 3.2.9`。
- `small`: `small.pt`、`483617219` bytes、SHA256 `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794`。
- `medium`: `medium.pt`、`1528008539` bytes、SHA256 `345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1`。
- `turbo`: `large-v3-turbo.pt`、`1617941637` bytes、SHA256 `aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a`。
- official URL: `https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt`、`https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt`、`https://openaipublic.azureedge.net/main/whisper/models/aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a/large-v3-turbo.pt`。
- 上記3候補のURL、filename、size、SHA256はversioned manifestとcatalog loaderで一致した。
- `collect_data_files("whisper")`の列挙結果は `mel_filters.npz`、`multilingual.tiktoken`、`english.json`、`gpt2.tiktoken` の4件で、model weightsは含まれなかった。
- spec固有datasは `src/core/whisper_models.json -> src/core`、package-dataは `core = ["whisper_models.json"]`である。
- tracked fileの `*.pt`、`*.bin`、`*.part`、`models/`検索では該当ファイルは見つからなかった。
- `pyproject.toml`と`requirements.txt`はともに `openai-whisper==20250625`である。

### 18.3 ユーザーGUI証拠と文書同期

- B3（2026-08-23）、B4（2026-08-24）、B5（2026-08-25）、B6（2026-08-26）の手動GUI確認は、各Blockで受領したユーザー報告（問題なし）をcurrent HEADの証拠として再利用した。Codex自身のGUI実行結果とは扱わない。
- B7ではproduction code、test code、GUI挙動を変更していないため、追加の手動GUI確認は実施していない。
- READMEと配布用readmeへ、Whisper候補選択、明示 `Download & Verify`、検証済み候補の適用・再解析、重み非同梱、解析時自動download禁止、音声外部送信なしを同期した。
- `docs/Release_Package_Manifest.md`と`THIRD_PARTY_LICENSES.md`へ、manifest同梱、model weights非同梱、公式URL・exact size・SHA256検証、B7静的監査結果を同期した。

### 18.4 Finding ledger

| ID | 分類 | 内容 | 対応・状態 |
| --- | --- | --- | --- |
| B7-F-001 | P2（解消） | 旧方針ではPython 3.13.x executableを現環境で確認できず、互換性gateを実施できなかった。 | ユーザー判断によりPython 3.14.3を開発・受入gateへ採用し、現行実測結果を合格扱いとした。Python 3.13.xの導入は行わない。 |
| B7-F-002 | P3（解消） | B7計画書の「レビュー補正中（未コミット）」表記が、`12ec286`コミット済みの現行状態と不一致だった。 | 計画書の状態表記を現行commitへ補正し、findingを解消済みとして記録した。 |

### 18.5 未完了・延期

- Python 3.14.3 development / acceptance compatibility gateは完了した。
- Python 3.11 / 3.12 compatibilityは今回の開発・受入対象外であり、未検証として記録する。
- PyInstaller onefile生成物、Analysis TOC、ZIP実内容、PySide6最終artifact混入、FFmpeg最終license noticeはMS27のpackage / release readinessで確認する。
- 実MMDでのVMD / WAV読み込み・リップ同期はMS26で確認する。

### 18.6 MS24 Closeout A判定（2026-08-28）

- P1 / P2は残っていない。B7-F-001（旧Python 3.13.x gate）はユーザー判断によりPython 3.14.3の開発・受入gateへ変更して解消し、B7-F-002（計画書状態表記）は`P3（解消）`へ補正した。
- B1〜B6の実装・回帰、B7のintegration regression、Python 3.14.3 gate、package静的監査、ユーザーGUI確認範囲、文書同期を照合し、MS24 Closeout Aを合格と判定する。
- 実MMD確認はMS26、PyInstaller onefile / ZIP / PySide6最終artifact・package / release readinessはMS27へ延期する。これらはMS24 Closeout Aの合格範囲に含めない。
