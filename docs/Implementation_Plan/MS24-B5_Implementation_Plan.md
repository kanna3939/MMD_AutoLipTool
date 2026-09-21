# MS24-B5 Implementation Plan

## 1. 文書情報

| 項目 | 内容 |
|---|---|
| 文書名 | MS24-B5 Implementation Plan |
| 対象ブロック | MS24-B5 Model Runtime / Analysis Integration |
| 文書状態 | Implementation Plan（実装済み・自動検証済み・ユーザー手動GUI確認済み・未コミット） |
| 正本 | `docs/Implementation_Plan/MS24_Block_Breakdown.md` の MS24-B5 定義 |
| 前提ブロック | MS24-B1 versioned manifest / verified-local loader、MS24-B2 model storage / availability、MS24-B3 user-facing model selection、MS24-B4 foreground model management |
| 実装対象 | 選択済みモデルの解析利用、単一モデルruntime cache、解析・rollback・削除境界 |
| 対象外ブロック | MS24-B6 diagnostics summary、MS24-B7 user documentation / closeout、MS26 実MMD確認、MS27 package / release |
| 変更権限 | 実装時に本計画の対象ファイルと必要な新規テストを変更する。本計画策定時は本ファイルだけを作成する |

本計画は、計画策定時点で確認できた現行コードと既存文書を根拠にする。既存のMS24文書には過去時点のworking tree状態を記載した箇所があるが、実装時の基準は実際のリポジトリ状態と実装済みB4コードを優先する。実装前に対象ファイルの差分が存在する場合は、ユーザー所有の変更を保持してから着手する。

本計画に基づく実装状態（2026-08-25）:

- B5のproduction code、test code、GUI接続をworking treeへ実装した。verified-local model request、single-active runtime、Apply / candidate commit-reject、TEXT + 音声・voice-only伝播、model-aware rollback、production ownership permit、delete / root change / shutdown境界を接続した。
- `openai-whisper==20250625`、verified local checkpoint専用loader、解析時の暗黙download禁止、word / segment fallback、MS23の固定morph・Latin profile・preset・diagnostics・fingerprint契約を維持した。
- `.\\.venv\\Scripts\\python.exe -m pytest tests` は `872 passed, 2 skipped`、process exit code `0`。`compileall -q src` と `git diff --check` もprocess exit code `0`で完了した。
- ユーザーから提示したB5手動GUI確認項目の通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- Python 3.13.x互換性確認、実MMDによるVMD / WAV読み込み・リップ同期確認、MS27 package / release readinessは未確認または別工程であり、stage、commit、push、merge、tag、releaseは未実施である。

## 2. 背景

### 2.1 計画策定時点の確認済み現行事実

- `src/core/whisper_timing.py` は現在 `recognize_audio()` からモデル名を受け取り、`@lru_cache(maxsize=2)` の `_load_whisper_model()` 経由で `whisper.load_model(model_name)` を呼び出している。
- `src/core/whisper_model_loader.py` には、manifest検証済みの `VerifiedWhisperCheckpoint` を受け取り、`openai-whisper==20250625`、alignment heads、private API、サイズ、SHA256、TOCTOUを検証してローカルcheckpointをロードする処理がある。B5はこのloaderを解析時の唯一のモデルロード経路として利用する。
- `src/core/whisper_model_store.py` には、model key、manifest、artifact pathを基にした削除処理と、B4から注入される `OwnershipReleasePermit` のopaque verifierがある。現状はtest-only issuerしかなく、B5でproduction issuerの内部接続を追加する必要がある。
- `src/core/pipeline.py` はTEXT + 音声のtiming処理を担い、`src/gui_wx/analysis_worker.py` はTEXT + 音声とvoice-onlyの両方からpipelineを呼ぶ。voice-onlyではWhisper認識結果を先に得て、pipelineには既存timingを渡す経路がある。
- 現行pipelineにはWhisper timing errorを警告・fallbackとして扱う箇所がある。モデルの未配置、integrity mismatch、load failure、memory failureは「結果不足」と区別し、成功扱いにしない必要がある。
- `src/gui_wx/main_frame.py` は現在、選択modelの設定、解析開始、成功・失敗・cancel、rollback、VMD saveabilityを調整するが、解析workerへ選択modelの完全なidentityを伝えていない。
- `src/gui_wx/ui_state.py` にはselected / active / loaded / analysisに対応する先行フィールドがあるが、manifest identity、storage root、retained identityの完全な契約は未実装である。
- `src/gui_wx/analysis_rollback.py` の `AnalysisParameterSnapshot` はmodel key / manifest identityをまだ保持していない。
- `src/gui_wx/app_controller.py` とB4のdownload/delete workerには、foreground management、storage root、ownership providerの接続点がある。B5はこの境界を維持し、B4がpermitを発行しないようにする。
- `pyproject.toml` と `requirements.txt` は `openai-whisper==20250625` を同期している。B5で依存値を変更しない。

### 2.2 B5で解消する問題

モデル選択状態と解析で実際に使ったモデルが一致しないまま、解析時に公式model keyで暗黙downloadする余地がある。また、複数モデルを保持する現在のcacheは、モデル切替・削除・終了時のGPU/CPU資源解放とfile deletionの順序を保証しない。B5では、verified local checkpoint、完全なmodel identity、解析workerの全経路、rollback、single-active ownershipを一つの契約に統合する。

## 3. 目的

次の動作を実装可能な状態まで具体化する。

1. MainFrameからAnalysisWorker、pipeline、whisper_timingまで、TEXT + 音声およびvoice-onlyの全Whisper timing経路にactive model keyとmanifest identityを伝播する。
2. 解析開始前にactive modelのverified availabilityを確認し、B2の `VerifiedWhisperCheckpoint` DTOだけをB1のverified-local loaderへ渡す。
3. 解析時の暗黙download、ネットワークアクセス、公式key + `download_root`、checkpoint pathの再open、直接の `whisper.load_model()` を禁止する。
4. `word timestamp` 優先、`segment` fallback、既存timing、voice-only、FFmpeg PATH補正、30fps VMD、MS23の生成物契約を維持する。
5. selected / active / loaded / analysis / retained identityを区別し、model変更とtranscription editの再解析・rollback境界を明示する。
6. `lru_cache(maxsize=2)` をsingle-active cacheへ置き換え、model key、storage root、manifest identityをcache identityに含め、明示eviction/unloadとdevice resource cleanupを保証する。
7. B4のownership provider / opaque `OwnershipReleasePermit` 接続点を維持し、productionでのpermit issuerをB5だけにする。

## 4. In Scope

- Whisper model identity DTO、failure class、解析要求の定義。
- `VerifiedWhisperCheckpoint` を使うverified-local loaderの解析runtime統合。
- single-activeのthread-safe runtime cacheとlease、明示unload、device cleanup。
- TEXT + 音声およびvoice-onlyのactive model伝播。
- model availability確認、manifest整合性確認、network-unreachable fail-closed。
- Applyによるcandidate modelのload、active設定更新、full re-analysisの境界。
- `model_changed` と `transcription_edit` の再利用判定。
- `AnalysisParameterSnapshot` または同等rollback identityへのmodel key / manifest identity追加。
- unavailable、integrity mismatch、load failure、memory failure、cancelの状態契約。
- active modelのdelete前unload、B4 permit provider、analysis / retained identity invalidation。
- storage root変更、model切替、アプリ終了時のruntime lifecycle。
- 既存Whisper、voice-only、pipeline、rollback、diagnostics、wx lifecycle回帰テストの拡張とB5専用テストの追加。
- Python 3.13.x compatibility gateの実装・検証準備。Python 3.14.3は現行実測環境であるが、公式classifier外の補助情報として扱う。

## 5. Out of Scope

- cloud ASR、音声外部送信、telemetry、background network、解析時の自動download。
- Qt / PySide6の復活またはGUI toolkit変更。
- B6が所有する `WhisperDiagnosticsSummary` の詳細設計、diagnostics report文面、診断分類の全面変更。B5はB6が消費できるfailure sourceとidentityを提供する。
- MS23の固定morph `あ / い / う / え / お`、Latin profile、preset、diagnostics、fingerprint、VMD 30fpsの仕様変更。
- FFmpeg binaryのdownload、FFmpeg探索順の変更、音声形式・音声上限の変更。
- 実MMDによるVMD / WAV読み込みとリップ同期確認。これはMS26で実施する。
- package、release、tag、push、merge、配布依存関係の変更。これはMS27および別途承認された工程で扱う。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` の直接編集、既存runtime user dataへのfixture投入。
- B7のREADME、closeout文書、リリース文書の更新。必要な利用者向け説明はB7へ引き渡す。

## 6. 前提条件

1. B1のloader契約が正本であり、解析側はcheckpoint pathやdownload rootを解釈しない。解析側が扱うのは、B2 availabilityが生成した検証済みDTOと、そのimmutable identityだけとする。
2. `openai-whisper==20250625` を `pyproject.toml` と `requirements.txt` で同期維持する。loaderはversion gate、v20250625 alignment heads、private API不一致をfail-closedにする。
3. model availabilityがverifiedでない場合、解析は開始しない。partial、size mismatch、SHA256 mismatch、manifest mismatch、artifact欠損、scan pendingは成功扱いにしない。
4. UI threadはモデルロード、transcribe、unload待機、hash計算を実行しない。workerまたはruntime管理threadが担当する。
5. `SettingsStore` を通じたmerge保存を正本とし、`MMD_AutoLipTool.ini` を直接読み書きしない。B4が保持している他設定を失わない。
6. model切替はstorage root、model key、manifest identityを一組として扱う。same keyでもmanifest identityが異なるものを同じモデルとみなさない。
7. single-active cacheの「active」は、runtimeが保持するstrong model ownerが一件であることを意味する。candidate準備中も二つのmodel objectを同時にstrong保持しない。
8. B4の `OwnershipReleasePermit` はopaque one-shot tokenであり、B4 workerはpermitを要求するだけである。B5 runtime/controller boundaryだけがproduction issuerになる。
9. 現行のword / segment結果、supplied timing、voice-onlyの既存動作を回帰基準とする。結果不足fallbackとmodel infrastructure failureを同一視しない。
10. Python 3.13.xをWhisper compatibility gateとする。実装時には実行ファイルを明示してloader、runtime、全関連テストを確認する。Python 3.14.3の現行環境結果を3.13の代替合格証拠にしない。

## 7. 対象ファイル

### 7.1 主変更対象（実在確認済み）

| ファイル | B5での責務 |
|---|---|
| `src/core/whisper_timing.py` | model keyでの直接loadを廃止し、runtime sessionまたは検証済みloader経路だけでword / segment timingを行う。解析結果へmodel identityを付与する |
| `src/core/whisper_model_loader.py` | B1契約の再利用。version / alignment heads / private API / size / SHA / TOCTOU / local-onlyを維持し、failureの区別に必要な例外情報を公開する |
| `src/core/whisper_model_store.py` | B4 delete契約、manifest、artifact identity、permitのopaque verifier / 互換importを維持する。B5 runtimeだけが使う内部issuer seamを追加する場合も、公開constructorやB4向けfactoryは追加しない |
| `src/core/pipeline.py` | active model request / runtime sessionをTEXT + 音声経路へ伝播し、infra failureをfallback成功に変換しない。`PipelineError`のoptional `error_code` / `detail_code`を追加し、writerのmissing timing planを安定codeで伝える。supplied timingとword / segment優先順を維持する |
| `src/gui_wx/analysis_worker.py` | model requestを受け、全Whisper認識をruntime session経由にする。TEXT + 音声とvoice-onlyで同一identityを記録する |
| `src/gui_wx/analysis_rollback.py` | rollback snapshotにmodel key / manifest identity / rebuild reasonを追加し、blocked failureでは旧結果を復元しない |
| `src/gui_wx/main_frame.py` | availability確認、Apply、analysis request生成、model_changed / transcription_edit、success/error/cancel、delete/root/close境界をUI状態へ反映する |
| `src/gui_wx/app_controller.py` | runtimeの寿命、storage root変更、B4 management worker、ownership provider、終了時unloadを接続する |
| `src/gui_wx/ui_state.py` | selected / active / loaded / analysis / retainedのidentityを区別して保持し、invalidatingと成功commitの契約を実装する |
| `src/gui_wx/right_pane.py` | candidate verified状態とBusy状態に応じたApply操作、active/loaded/analysis表示、失敗時の安全な通知を既存wx theme / lifecycleに沿って追加する |

### 7.2 新規候補（実装時に追加。現在は未作成）

| ファイル | 想定責務 |
|---|---|
| `src/core/whisper_model_runtime.py` | single-active cache、cache identity、runtime lease、明示unload、device cleanup、B5専用production permit issuer接続、delete/close境界 |
| `src/core/whisper_model_contracts.py` | identity、analysis request、failure class等をruntimeとGUIが共有する必要がある場合のDTO置き場。runtime module内で十分なら作成しない |

新規module名は実装時に既存のimport循環を確認して確定する。少なくともB5がissuerであること、B4がissuerを呼び出せないこと、既存の `whisper_model_store` からのpermit型importを壊さないことを満たす。

### 7.3 関連確認対象（必要な場合だけ最小変更）

- `src/gui_wx/model_download_worker.py`: `OwnershipPermitProvider` のcallable境界を維持する。B5実装で型やエラー経路の変更が必要な場合だけ修正する。
- `src/gui_wx/whisper_availability_worker.py`: B4 scan結果のverified DTOをB5 requestへ渡す境界を確認する。
- `src/core/settings_store.py`、`src/gui_wx/app.py`: managed settings merge、root change、startup / shutdown接続を確認する。直接ini操作は追加しない。
- `src/gui_wx/output_diagnostics_adapter.py`、`src/gui_wx/voice_only_errors.py`: B6の詳細分類を先取りせず、B5 failure sourceを既存error lifecycleに接続するための最小確認対象とする。
- `src/core/__init__.py`: 新DTOを公開する必要がある場合だけ更新する。

### 7.4 テスト対象（実在確認済み）

既存回帰として `tests/test_whisper_timing.py`、`tests/test_whisper_model_loader.py`、`tests/test_whisper_model_store.py`、`tests/test_whisper_model_catalog.py`、`tests/test_ms19_b3_textless_pipeline.py`、`tests/test_ms19_b4_analysis_worker_voice_only.py`、`tests/test_ms19_b4_voice_only_gui_state.py`、`tests/test_ms19_b7_voice_only_error_handling.py`、`tests/test_pipeline_and_vmd.py`、`tests/test_pipeline_peak_values.py`、`tests/test_ms21_b7_analysis_rollback.py`、`tests/test_ms20_b3_output_diagnostics_adapter.py`、`tests/test_ms20_b6_diagnostic_report.py`、`tests/test_ms20_b7_diagnostics_state_integration.py`、`tests/test_ms22_b6_lifecycle_regression.py`、`tests/test_wx_ms22_b6_lifecycle_regression.py`、`tests/test_ms23_b6_model_profile_lifecycle.py`、`tests/test_ms24_whisper_model_ui_state.py`、`tests/test_ms24_whisper_model_availability_worker.py`、`tests/test_ms24_b4_controller.py`、`tests/test_ms24_model_download_worker.py`、`tests/test_wx_ms24_whisper_model_ui.py`を使用する。

新規テスト候補は `tests/test_ms24_whisper_model_runtime.py`、`tests/test_ms24_whisper_model_propagation.py`、`tests/test_ms24_no_implicit_download.py`、`tests/test_ms24_whisper_model_apply.py` とする。既存テストで同等の境界を表現できる場合は重複fixtureを増やさず、既存テストを拡張する。

### 7.5 文書（実装時は確認のみ。完了後の状態同期は別工程）

`docs/Implementation_Plan/MS24_Block_Breakdown.md`、`docs/Implementation_Plan/MS24-B4_Implementation_Plan.md`、`docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md`、`docs/Pipeline_Data_Contract_Specification.md`、`docs/GUI_State_Theme_Specification.md`、`docs/Error_Handling_Specification.md`、`README.md`、`pyproject.toml`、`requirements.txt` を実装根拠とする。B5実装時はこれらを確認対象とし、実装後の到達状態はB5計画書、Block Breakdown、Index、Roadmap、`repo_milestone.md`、`Version_Control.md`へ別工程で同期する。利用者向けの詳細説明はB7へ残す。

## 8. 実装方針

### 8.1 Model identityとfailure contract

次のidentityを導入または既存DTOへ追加する。名前は既存命名と衝突しない範囲で調整してよいが、意味は固定する。

```text
ModelIdentity
  model_key: str
  manifest_identity: str

RuntimeCacheIdentity
  model_key: str
  canonical_storage_root: str
  manifest_identity: str

VerifiedAnalysisModelRequest
  identity: ModelIdentity
  cache_identity: RuntimeCacheIdentity
  verified_checkpoint: VerifiedWhisperCheckpoint
```

`verified_checkpoint` はB2 availabilityが生成したDTOをそのまま渡し、B5がmodel keyからpathを再構成しない。runtimeはloaderにDTOを一度渡し、loaderがcheckpointを一度openする。`whisper.load_model()`、公式keyと`download_root`、外部network、解析時のpath再openを使用しない。

`whisper_failure_class` はMS24 Block Breakdownの正本どおり、`none | model_unavailable | integrity_mismatch | load_failure | memory_failure | transcribe_failure | cancelled` に固定する。B1 loader内部の`whisper_version_mismatch`等はfailure detailとして保持し、Whisper結果不足は既存の`whisper_no_words` / `whisper_no_segments` / `whisper_result_invalid`等のfallback reasonで表現する。`analysis_request_missing`は`whisper_failure_class`へ追加せず、解析requestまたはwriter入口の内部failure detail codeとして扱い、既存Error Handlingの`timing_plan_build_failed`へ写像する。B5が責任を持つのはsource identity、安全な状態遷移、failure detailの受け渡しであり、詳細な診断summaryや表示分類はB6へ渡す。

#### 8.1.1 Failure codeから上位failure classへの固定写像

B1 / B2のdetail codeとB5の`whisper_failure_class`の対応は、実装者が個別判断しないよう次で固定する。B2のdownload・delete専用結果は解析failure classへ変換せず、解析開始前にverified requestを作れない場合だけ`model_unavailable`として投影する。

| source / detail | `whisper_failure_class` | 扱い |
| --- | --- | --- |
| B2のscan pending、`model_missing`、`model_partial`、`model_key_unsupported`、`model_invalid_path`、`model_read_failed`、`storage_path_invalid`、`storage_path_remote`、verified requestなし | `model_unavailable` | 解析を開始せず、暗黙load・旧model fallbackを行わない |
| B2のstatus `invalid_size` / `invalid_sha256`、failure code `model_size_mismatch` / `model_sha256_mismatch` / `model_changed_during_verification`、B1の`checkpoint_integrity_mismatch` / `checkpoint_changed_during_revalidation` | `integrity_mismatch` | active解析をfail-closedにし、rollbackしない |
| B5 runtimeが正規化したload failure detail `load_failed`、verified request後のB1 `checkpoint_path_invalid`、`checkpoint_read_failed`、`checkpoint_not_verified`、`manifest_invalid`、`whisper_package_missing`、`torch_package_missing`、`whisper_version_mismatch`、`alignment_heads_api_missing`、`alignment_heads_key_missing`、`alignment_heads_format_invalid`、`alignment_heads_apply_failed`、`checkpoint_bytes_load_failed`、既存error code `whisper_model_load_failed` | `load_failure` | B2のartifact statusは変更せず、解析を成功扱いにせず、旧解析へrollbackしない |
| bytes load、device準備、またはtranscribe中の`MemoryError` / torchのout-of-memory相当 | `memory_failure` | `checkpoint_bytes_load_failed`等のwrapper codeより優先して分類する |
| verified runtime sessionのtranscribe実行中に発生した上記以外の例外、既存error code `whisper_transcribe_failed` | `transcribe_failure` | 結果不足fallbackへ変換しない |
| active commit後の明示cancel、shutdown、またはgeneration失効による解析結果破棄 | `cancelled` | late resultを適用せず、active解析のsaveabilityを復元しない。Apply準備中candidateのcancelは旧active状態を変更しない |
| 正常解析、既存のword / segment不足fallback、`analysis_request_missing`、candidate準備中の失敗 | `none` | 前者はfallback reasonまたは`timing_plan_build_failed`へ、後者はactive状態を保持する |

`checkpoint_changed_during_revalidation` はB1の`checkpoint_integrity_mismatch`と同じ`integrity_mismatch`へ、B2の`model_promote_failed`やdelete / cleanup専用failureはB4管理結果として扱う。分類順序は、(1) active解析のgeneration / cancel guard、(2) `MemoryError` / torch OOM、(3) integrity mismatch、(4) model unavailable、(5) load failure、(6) transcribe failureとする。loaderがwrapper errorを返しても、`__cause__`を含む原因がmemory failureなら`memory_failure`を優先する。B5はdetail codeを失わず、上位classと併記してB6へ渡す。

`load_failed`はB2の`ModelAvailability.artifact_status`へ追加しない。B2は物理artifact状態とその`failure_code`を保持し、B5 runtimeがverified checkpointのload / device準備結果を解析failure detailとして正規化する。`load_failed`、`memory_failure`、`transcribe_failure`はB5/B6の解析failure軸であり、B2のartifact / transfer / ownership軸とは混在させない。

Whisper timingのfallback境界は次で固定する。word timestamp試行が例外なく有効なresult dictを返した場合だけ、word anchorがない・不足する結果に対してsegment timestampを同じresultから使用し、必要なsegment-only再試行も結果不足の場合だけ許可する。loader、device準備、memory、transcribe、FFmpegまたはnetwork境界の例外はsegment-only再試行へ進まず、元のdetail codeと原因chainを保持してfatal failureとして返す。segment-only再試行自体が例外になった場合も同様に扱う。結果が正常に返ったがword / segment anchorを持たない場合だけ、既存の`whisper_no_words` / `whisper_no_segments` / `whisper_result_invalid`等のfallback reasonを使用する。

`WhisperModelSelectionState.whisper_failure_class`および`WhisperDiagnosticsSummary.failure_class`の初期値・成功時・明示clear時は常に`none`とする。`None`はB5の状態契約およびdiagnostics出力では使用しない。candidate準備中の失敗・cancelはactive解析のfailure classを上書きせず、active commit後の解析failure / cancelだけが上位classを更新する。同一active modelで既存解析を復元できる通常cancelでは`none`へ戻す。

### 8.2 Verified-local loaderとversion gate

解析開始前に次の順序で確認する。

1. active keyが存在し、availability scanが完了している。
2. availabilityがverifiedで、key、manifest identity、size、SHA256、artifact pathが一致している。
3. B2 DTOを含むrequestをAnalysisWorkerへ渡す。
4. workerがruntimeを通じてB1 loaderを呼ぶ。
5. loader内で`openai-whisper==20250625`、v20250625 alignment heads、private API、bytes、TOCTOUを再検証する。

version不一致、alignment heads取得不能、private API不一致、検証済みDTOとcatalogの不一致はfail-closedにする。検証を弱めてlegacy loaderへfallbackしない。

### 8.3 Single-active runtime cache

新規runtime managerを推奨案とする。managerだけがloaded model objectをstrong ownershipし、leaseはraw modelを保持せずmanager経由でtranscribeする。cache identityは次の三つを必須とする。

- `model_key`
- canonicalized `storage_root`
- `manifest_identity`

既存の`lru_cache(maxsize=2)`は廃止する。model切替、storage root変更、delete前、アプリ終了では、対象leaseがないことを確認し、cache recordを明示的にevictする。その後、modelをCPUへ戻せる場合は戻し、device resourceを解放し、CUDA等のcache cleanupを行い、strong referenceを削除する。GCだけをunload契約にしない。

candidate準備時はsingle-active制約を守るため、旧modelをruntime cacheから明示evictしてからcandidateをloadする。旧analysis resultとactive設定は、candidateがloadできるまでUI state上で保持してよい。candidateのloadまたはsettings保存が失敗した場合、candidateをunloadし、旧active identityと旧analysis resultを残す。旧modelの即時再loadは行わない。

#### 8.3.1 B5 production permit issuerの固定境界

`OwnershipReleasePermit`の型、private issuer token、`_consume_for()`によるmodel key / manifest identity / artifact identity / single-use検証は、B2の正本である`src/core/whisper_model_store.py`に残す。B5では同ファイルに、公開APIや公開constructorではない、次の厳密なシグネチャを持つruntime専用の内部issuer seamを追加する。

```python
def _issue_ownership_release_permit_for_runtime(
    *,
    model_key: str,
    manifest_identity: str,
    artifact_id: str,
) -> OwnershipReleasePermit:
```

この内部seamは`__all__`へ追加せず、caller-supplied path、既存permit、公開constructorを受け取らない。production call siteを`src/core/whisper_model_runtime.py`の一箇所に限定し、runtimeがownership確認済みの値だけを渡す。B4のworker・controller・UIからprivate token、permit constructor、内部seamを直接importまたは呼出ししない。

B5 runtime managerは、対象modelのlease、pending Apply、active / analysis identity、expected manifest、artifact identityを確認した後にだけ、上記内部seamを呼び出す`OwnershipPermitProvider` callableを自分自身に束縛して生成する。`app_controller.py`は起動時に現在のstoreをruntime managerへ渡し、そのcallableをB4の既存`OwnershipPermitProvider`へ注入する。storage root変更時は新storeと新runtime managerを確定してからproviderを差し替える。B4側は受け取ったcallableを呼ぶだけでpermitを生成・再構成しない。既存の`_issue_ownership_release_permit_for_testing()`はtest-only helperとして残し、production codeから使用しない。これにより、B4のprovider shapeとB2のopaque verifierを維持したまま、production issuerの責務をB5 runtimeに限定する。

transcribe中のleaseがある場合、delete / switch / closeはunloadを完了できるまで論理的に保留し、UI threadをブロックしない。cancelはtranscribe自体を強制中断できない場合でも、戻った結果をjob generationで破棄し、lease解放後にdeferred unloadを完了する。

### 8.4 Analysis propagation

MainFrameがactive identityとverified DTOを解決し、AnalysisWorkerへ`VerifiedAnalysisModelRequest`を渡す。AnalysisWorkerは同じrequestまたはruntime sessionをpipelineへ渡し、pipelineはwhisper_timingへsessionを渡す。

- TEXT + 音声: `pipeline -> whisper_timing` の認識でactive sessionを使用する。
- voice-only: workerがactive sessionで一度認識し、そのtiming resultをpipelineへ渡す。pipelineで再認識しない。
- supplied timing: 既存の有効なtimingを使う場合は再認識を行わないが、analysis identityがrequestのmodel identityと一致していることを記録する。

`generate_vmd_from_text_wav()`はVMD writer入口であり、production GUI経路では必ず既にverified runtimeで生成された`timing_plan`を渡す。writer入口にverified analysis requestを追加する別経路は設けない。`timing_plan`なしでWhisperを起動する現行の`model_name="small"` fallbackはB5で廃止し、production callerには既存Error Handlingの`timing_plan_build_failed`をraiseし、内部failure detailとして`analysis_request_missing`を保持する。現行APIが`PipelineError`をraiseする契約は維持し、B5では次の後方互換コンストラクターでoptional codeを例外へ付与して、GUI側が安定codeを参照できるようにする。

```python
PipelineError(
    message: str,
    *,
    error_code: str | None = None,
    detail_code: str | None = None,
)
```

既存callerがmessageだけで生成・catchできることを維持する。既存の純粋pipelineテストやwriterテストは、明示的なtiming planまたは注入したtiming resultを使い、Whisperの直接load経路を温存する理由にしない。

word timestampを先に要求し、利用できない場合だけsegment timestampへfallbackする。結果が空、短い、または期待形式でない場合は既存のresult-shortage / fallback reasonへ写像し、既存fallbackの範囲に限る。model availability、integrity、load、memory、version、private APIのfailureはfallbackで成功扱いにしない。

### 8.5 Applyとactive commit

技術に詳しくないユーザーでも安全に切替できるよう、verifiedなcandidateだけをApply対象にする二段階方式を採用する。

1. selected modelがverifiedで、analysis / managementがBusyでない場合だけApplyを有効にする。
2. workerがcandidateをruntimeへloadする。旧modelはsingle-activeのため先にevictするが、旧active / analysisのUI stateはcommitまで保持する。workerはcandidateをready状態としてmanagerへ返して終了し、UIの判断を待ってブロックしない。
3. runtime managerだけがcandidate sessionをstrong保持し、opaqueな`candidate_session_id`、job generation、candidate identity、availabilityを含む`candidate_ready` payloadをcallbackへ渡す。MainFrameはUI threadを待機させず、`commit_candidate(candidate_session_id, expected_generation)`または`reject_candidate(candidate_session_id, reason)`のどちらか一方をcallback内で一度だけ呼ぶ。stale callback、cancel、window closeの場合も同じreject経路を呼び、managerがcandidateをunloadする。
4. MainFrameはjob generation、cancel、candidate identity、availabilityを再確認する。coalescedな`request_settings_save()` / `flush_pending_save()`はApply commitに使用せず、現在の全設定を読み込んだmerge candidateへactive keyとmanifest identityだけを反映し、専用commit経路から一回の`SettingsStore.save()`を実行する。`SettingsSaveResult.succeeded`が返るまでactive / analysis identityを変更しない。candidateをruntimeが保持している場合の`loaded`はpending candidateとして扱い、activeと同一視しない。
5. 保存成功後にactive / loadedをcandidateへ更新し、旧analysis、Preview、diagnostics success、VMD saveabilityを無効化して`model_changed`としてfull re-analysisを開始する。
6. 保存失敗、candidate load failure、integrity failure、memory failure、cancel、window close、stale callbackではactiveを更新しない。reject経路はcandidate sessionを一度だけunloadし、loadedをNoneへ戻し、旧active / analysis / Preview / diagnostics / VMDを保持する。duplicate callbackは状態を変更しない。
7. active commit後の再解析failureまたはcancelは旧modelの解析結果へrollbackしない。新modelでの解析が成功するまでanalysis / Preview / VMDを無効にする。

Apply candidateの状態は `loading -> ready_pending_commit -> committed | rejected` とし、terminal transitionは一回だけ許可する。`candidate_session_id`はmodel objectやpermitではなく、候補commit判定を一意に照合するopaque identifierとする。`begin_shutdown()`、cancel、stale generation、window closeは保留candidateをrejectへ遷移させ、workerやUI callbackの無期限待機を残さない。UI threadはmodel load、unload、hash計算、worker完了待機を行わない。

このcommit pointにより、準備前の失敗は旧状態を保持し、active確定後の失敗は新しいactive identityに対してfail-closedにする。専用commit経路が既存の保留中saveをcandidateへ統合し、古いtimer callbackがcandidateのactive設定を上書きしないよう、成功・失敗のいずれでもpending save flagとgenerationを整理する。Applyはモデルload、transcribe、hash、unloadをUI threadで実行せず、stale workerがactive設定を上書きできないようgeneration tokenを必須とする。

### 8.6 Retained timingとrollback

retained identityは少なくともmodel keyとmanifest identityを保持する。storage rootはcache identityには含めるが、同一manifestの解析意味を変えないためretained semantic identityには含めない。

- `transcription_edit`: active identityとretained identityが完全一致し、音声・timing入力が同一契約を満たす場合だけ既存timingを再利用する。
- `model_changed`: selected / active keyまたはmanifestが変わった場合、必ずfull Whisper analysisを行う。
- input変更、profile変更、morph変更、workspace resetは既存契約に従ってretainedを無効化する。
- `AnalysisParameterSnapshot`または同等snapshotにmodel key、manifest identity、rebuild reasonを記録する。
- model unavailable、integrity mismatch、load failure、memory failure、model_changed後のfailureでは旧analysisをrollbackしない。
- 同一active modelの通常cancelなど、既存契約で復元可能なケースだけ旧analysisを復元する。復元後もdiagnostics successとVMD saveabilityはidentityが一致する場合だけ有効にする。

### 8.7 Delete、root change、exit

B4のdelete workerへ渡すprovider callableのshapeは維持する。B5側はdelete requestを事前登録し、key、expected manifest identity、artifact identity、job / generation、active leaseの状態をworker-safeに保持する。providerは次の順序で処理する。

1. 対象モデルのactive analysis、runtime lease、pending Applyがないことを確認する。
2. 対象cacheを明示evictし、device resource cleanupを完了する。
3. 対象active / analysis / retained identityをfail-closedでinvalidにする要求を登録する。
4. B5 runtimeだけが、storeのruntime専用内部issuer seamを通じてmodel-bound・manifest-bound・artifact-boundのone-shot `OwnershipReleasePermit` を発行する。
5. B4 workerがpermitをstoreへ渡してdeleteする。

permit発行前にUI stateを直接操作しない。worker完了のterminal callbackで、delete成功・失敗・cancelの結果をjob generationに照合してUI thread側のstateへ反映する。active modelのdelete後はactive設定を別modelへ暗黙fallbackせず、selectedは保持し、active availabilityは未配置として扱う。旧analysis、Preview、diagnostics success、VMD saveabilityは無効にする。

storage root変更はB5の専用lifecycle入口から次の順序で行う。新規解析、Apply、Deleteを拒否し、保留中candidateをrejectへ遷移させ、active leaseを解放できることを確認して旧runtimeを明示unloadする。旧runtime解放後に、B2のroot解決、新`WhisperModelStore`、新runtime managerをtemporary candidateとして生成し、現在の設定を壊さないmerge candidateを専用の`SettingsStore.save()`で一回だけ保存する。root保存またはcandidate store / runtime生成に失敗した場合は、旧active / analysis / Preview / diagnostics / VMD identityを維持し、loadedだけは`None`になり得るものとして表示し、旧modelを暗黙再loadしない。保存成功後にstore/runtime/providerを新rootへ切り替え、`start_whisper_availability_rescan()`を一回開始する。同一key・同一manifestがverifiedなら既存のsemantic analysis identityは直ちに`model_changed`とはしないが、次の解析では新rootのverified DTOを必ず使用する。新rootでactive artifactがunavailableまたはintegrity mismatchなら、scan結果を受けて旧analysisをfail-closed invalidationする。保存成功後にrescan開始だけが失敗した場合は、新root設定と新store/runtimeを保持したままscan pending / fail-closedとし、verified確認が終わるまで新規解析を開始しない。旧rootへの暗黙rollbackは行わない。

アプリ終了では、AppControllerが所有するB5 runtime managerへ先に`begin_shutdown()`を通知し、新規解析・Apply・Deleteを拒否する。job / generationを失効させてcallbackを破棄し、view破棄後もruntime managerがlease完了後のdeferred unloadを継続できるようにする。UI threadはleaseやunloadの完了を同期待機しない。runtime managerのshutdown完了前に新しいmodel objectやproviderを生成してはならない。

## 9. 詳細ステップ

### Step 1: 共有DTOとfailure境界を定義する

- `ModelIdentity`、`RuntimeCacheIdentity`、`VerifiedAnalysisModelRequest`、rebuild reason、failure classを既存型と衝突しない場所へ追加する。
- `VerifiedWhisperCheckpoint` をrequestへそのまま含め、model keyからpathを再構成しない。
- failure classは8.1.1の固定写像を共有し、detail code、上位class、rollback可否を同じ結果DTOへ保持する。`none`を通常・成功・明示clearの値とし、B5の状態契約で`None`を使用しない。
- `WhisperTimingResult`、pipeline result、AnalysisWorker result、rollback snapshotへidentityを渡せるようにする。
- default引数は既存の純粋timingテストを壊さないために限定的に残してよいが、production GUI経路ではrequestなしのWhisper認識を許可しない。

### Step 2: B5 runtime managerを作成する

- `lru_cache(maxsize=2)`を置き換え、single-active recordとgenerationを持つ。
- managerだけがloaded model objectをstrong保持し、leaseがtranscribe中のunloadを防ぐ。
- cache identityの三要素を比較し、keyだけ一致するmodelを再利用しない。
- switch、root change、delete、exit、failed Applyの各explicit evictionを実装する。
- CPU移動、device cleanup、strong reference解放、deferred unloadを順序化する。
- B5-only permit issuerをruntime ownership boundaryへ実装する。`WhisperModelStore._issue_ownership_release_permit_for_runtime(*, model_key, manifest_identity, artifact_id) -> OwnershipReleasePermit`をproductionの唯一のissuer seamとし、store側のpermit型・verifier・B4からの既存importを互換維持する。productionの公開constructor / 公開factory / test-only issuer呼出しは追加しない。

### Step 3: loaderとruntimeのエラーを接続する

- B1 loaderのversion gate、alignment heads、private API、SHA256、size、TOCTOUを変更しない。
- 8.1.1の固定写像に従い、B1 / B2 detail code、`__cause__`を含むmemory例外、transcribe例外を上位failure classへ写像する。wrapper codeよりmemory failureを優先し、写像後も元detail codeを失わない。
- loaderが失敗した際、official keyのloaderやnetworkへfallbackしない。
- pathのopen回数がloader契約を超えないことをテストで固定する。

### Step 4: whisper_timingのload経路を置き換える

- `recognize_audio()`がmodel nameだけでruntime modelを取得しないようにする。
- runtime sessionを受け取り、sessionのtranscribeを使用する。
- word timestampを優先し、正常な結果不足の場合だけsegment fallbackを行う。loader / device / memory / transcribe / FFmpeg / network例外ではsegment-only再試行を行わず、`WhisperModelLoaderError.code`または原因chainを保持して8.1.1のfatal failureへ伝播する。既存のword / segment不足fallbackは`whisper_no_words` / `whisper_no_segments` / `whisper_result_invalid`等として維持する。
- FFmpeg PATH補正、音声入力の一時ファイル、結果整形を変更しない。
- モデルを認識しない単体timing helperと、verified runtimeを必須とするproduction entry pointを混同しない。

### Step 5: pipelineへidentityとfatal failureを伝播する

- TEXT + 音声のpipeline requestにverified model request / sessionを追加する。
- supplied timingがあるvoice-only経路は同一resultを再利用し、二重認識しない。
- Whisper結果不足のみ既存のword / segment / warning fallback reasonの対象にする。
- unavailable、integrity mismatch、load failure、memory failure、version / private API failureはfatal analysis failureとしてworkerへ返す。
- `PipelineError`は既存の例外継承とcatch互換を維持したまま、optional `error_code` / `detail_code`を保持できるようにし、writer入口のmissing timing planを`timing_plan_build_failed` / `analysis_request_missing`として伝播する。
- vowel generation、fixed morph、Latin profile、preset、diagnostics observation、fingerprint、30fps VMDの既存契約を維持する。

### Step 6: AnalysisWorkerで全経路を統合する

- constructor / job DTOにmodel requestを追加する。
- worker開始時にavailability snapshotとgenerationを確認する。
- runtime leaseを取得し、TEXT + 音声とvoice-onlyの認識で共有する。
- voice-onlyでは一回のrecognize結果をpipelineへ供給する。
- cancel時はlate result discardを維持し、leaseをfinally相当の経路で解放する。
- worker resultにanalysis model identity、failure class、rebuild reasonを付ける。

### Step 7: UI stateとrollbackを更新する

- selected、active、loaded、analysis、retainedの各identityを独立して更新する。
- loadedはruntimeが実際にstrong ownershipしているidentityと一致させる。Apply準備中はpending candidateを明示し、activeと混同しない。
- success commitでanalysis / retained identityを更新し、invalidatingでanalysis / retained / diagnostics success / VMD saveabilityを明確に消す。
- `whisper_failure_class`は初期化・成功・明示clearで`none`、active commit後のfatal failure / cancelで8.1.1のclassとする。candidate準備中のfailure / cancelでは旧activeのclassを保持する。
- `model_changed` と `transcription_edit` を別reasonとして保持する。
- rollback snapshotにmodel key / manifest identityを入れ、blocked failureはrestore対象外とする。
- model-aware stateをworkspace reset、analysis cancel、transcription edit、delete、root rescanで個別に処理する。

### Step 8: MainFrame / RightPaneにApplyと安全な状態遷移を追加する

- verified candidateだけをApply可能にする。analysis Busy、management Busy、scan pending、cancel中は無効にする。
- MainFrameがrequestを生成し、workerへ完全なidentityとDTOを渡す。
- loader成功後はworkerを終了させ、candidate runtimeの所有権をcommit判定が終わるまでB5 managerが保持する。UI callbackはopaque session IDとgenerationを照合してcommit/rejectを一度だけ返し、stale callback、cancel、close、shutdownではreject経路を必ず実行する。workerやUI threadをcommit decision待ちにしない。
- `request_settings_save()` / `flush_pending_save()`とは別のApply専用commit経路で、全設定をmergeしたcandidateを一回保存し、`SettingsSaveResult.succeeded`確認後だけactiveを更新する。失敗時はpending saveとgenerationを整理してcandidateをunloadする。
- precommit failureは旧active / analysisを保持し、postcommit failureは旧analysisへrollbackしない。
- stale callback、close、cancelがcandidateをactiveにできないことを固定する。
- wx theme、Busy lock、late-result discard、既存のDownload / Delete操作の表示を壊さない。

### Step 9: B4 providerとlifecycleを接続する

- `OwnershipPermitProvider` の呼出し形を保ち、B4がpermitを発行しないことを確認する。
- delete前のactive lease確認、unload、identity invalidation登録、B5 runtimeの内部issuer seamによるpermit発行、B4 workerへの受け渡しの順序を実装する。
- delete workerのcancel / failure時に、permit再利用や二重invalidateを許さない。
- storage root変更、startup scan、window closeをruntime lifecycleに接続する。root変更は旧runtime解放、candidate store / runtime生成、managed settings保存、store/runtime/provider差し替え、`start_whisper_availability_rescan()`の順序を固定する。
- close時はAppControllerがruntime managerの`begin_shutdown()`を呼び、workerが保持したmodel objectやfuture callbackを新しいUI stateへ反映させない。runtime managerのlease完了後にstrong ownerを解放する。

### Step 10: 回帰テストとPython 3.13 gateを実装する

- 既存Whisper / pipeline / voice-only / rollback / diagnostics / wx lifecycleテストを拡張する。
- single-active、no implicit download、propagation、Apply、delete permitを新規または既存テストで固定する。
- temporary pathだけを使用し、runtime user dataを触らない。
- Python 3.13.xでloader、runtime、analysis、lifecycleの対象テストを実行し、実行ファイルと終了コードを記録する。

## 10. 状態遷移 / データ契約

### 10.1 Identityの意味

| identity | 意味 | 変更時の扱い |
|---|---|---|
| selected | ユーザーがUIで選択したmodel key | Apply候補。未verifiedなら解析不可 |
| active | 次の解析で使うことを確定したkey + manifest | SettingsStoreのmanaged stateと一致 |
| loaded | runtimeが実際に保持するkey + root + manifest | strong owner一件と一致。activeと異なるのはApply準備中だけ許容 |
| analysis | 現在の解析結果を生成したkey + manifest | Preview / diagnostics / VMD saveabilityと同一世代 |
| retained | transcription editで再利用可能なtimingのkey + manifest | activeと完全一致する場合だけ再利用 |

`storage_root` はloadedのcache identityに含めるが、同一manifestのanalysis / retained semantic identityには含めない。ただしroot変更後のscanがunavailableまたはintegrity mismatchを返した場合は、分析結果を有効な現行結果として扱わない。

### 10.2 正常なApply

```text
selected(candidate, verified)
  -> preparation_busy
  -> old runtime evicted
  -> candidate loaded / loaded=candidate
  -> SettingsStore merge success
  -> active=candidate, analysis invalidated, reason=model_changed
  -> full analysis
  -> analysis=candidate, retained=candidate, Preview/diagnostics/VMD enabled if success
```

### 10.3 Apply準備失敗

```text
candidate unavailable / integrity / load / memory / cancel / close
  -> candidate not active
  -> candidate runtime unloaded
  -> loaded=None
  -> old active, analysis, Preview, diagnostics, VMD remain unchanged
```

candidate loadのために旧runtimeをevict済みでも、旧analysis resultのidentityは失わない。旧modelの再loadは次回解析時に行う。

### 10.4 Active modelでの解析failure

```text
active model unavailable / integrity / load / memory
  -> analysis invalid
  -> retained invalid
  -> Preview invalid
  -> diagnostics success cleared / failure source retained for B6
  -> VMD saveability false
  -> active setting remains; no silent fallback
```

同一active modelの通常cancelなど、既存契約で入力・parameter・identityが復元可能な場合だけold analysisをrollbackする。`model_changed` commit後のcancel / failureにはこのrollbackを適用しない。

### 10.5 Transcription edit

```text
transcription_edit
  -> if active identity == retained identity and timing input is reusable
       reuse timing, rebuild downstream plan only
  -> otherwise full analysis
```

model keyまたはmanifest identityが変わった場合は、理由がtranscription editに見えてもreuseしない。

### 10.6 Delete / root change / shutdown

- delete対象がactiveまたはanalysis identityに関係する場合、lease確認、explicit unload、identity invalidation登録、B5 permit発行、B4 deleteの順序を守る。
- delete対象が別modelであっても、loaded cacheが対象ならexplicit unloadしてからpermitを発行する。
- root changeは新規jobを拒否し、保留中candidateをrejectへ遷移させ、lease確認、旧runtime unload、candidate store / runtime生成、managed settings保存、store/runtime/provider差し替え、rescanの順で行う。保存失敗時は旧active / analysisを維持し、loadedだけをNoneとして扱う。新rootがsame manifestでverifiedならanalysis semantic identityを保ち、unavailable / integrity mismatchならfail-closed invalidationする。保存成功後にrescan開始だけが失敗した場合は、新root設定と新store/runtimeを保持してscan pending / fail-closedとし、verified確認まで新規解析を拒否する。
- shutdownはAppControllerがruntime managerの`begin_shutdown()`を呼んで新規jobを拒否し、late callbackを破棄し、lease完了後に明示shutdownする。UI threadで同期unload待ちをしない。

## 11. テスト方針

実装時に次の順で、対象を絞って実行する。計画策定時には実行しない。

### 11.1 Loader / runtime単体

- verified DTOのみでloadでき、公式 `whisper.load_model()` が呼ばれない。
- openai-whisper version gate、alignment heads、private API不一致がfail-closedになる。
- exact size / SHA256 / manifest mismatch、path欠損、TOCTOUを拒否する。
- network unreachable環境でもsocket、HTTP、Whisper downloadへ進まない。
- `model_key + storage_root + manifest_identity` がcache identityになり、same keyのmanifest違いを再利用しない。
- load成功時のstrong ownerが一件で、switch / root change / delete / closeで明示evictionとdevice cleanupが行われる。
- active lease中はunload / delete permitが発行されず、lease解放後にdeferred cleanupが完了する。
- memory failureと一般load failureが別failure classになる。
- B1 / B2の各detail code、wrapper exceptionの`__cause__`、transcribe exception、cancel / stale generationが8.1.1の上位classへ一意に写像され、detail codeが保持される。`checkpoint_bytes_load_failed`に包まれたOOMは`memory_failure`になる。
- word timestamp試行が正常なresult shortageを返した場合だけsegment fallback / segment-only再試行を行い、loader / device / memory / transcribe / FFmpeg / network例外では再試行せず、元detail codeと原因chainを保持する。

### 11.2 Propagation / timing / pipeline

- MainFrame相当のrequestがAnalysisWorker、pipeline、whisper_timingまで同一model key / manifestで届く。
- TEXT + 音声が同一sessionでword-first / segment-fallbackを行う。
- word timestampが正常に不足した場合のsegment fallbackは維持し、loader / transcribe / memory failureではsegment-only再試行へ進まない。既存の「例外時segment retry」テストは、結果不足時の再試行とinfra failure非再試行へ分離して更新する。
- voice-onlyが一回だけ認識し、supplied timingをpipelineで再認識しない。
- model requestなしのproduction解析が拒否される。既存の純粋なfallback / deterministic test helperは必要最小限の互換を保つ。
- Whisper結果不足だけが既存fallback対象で、`whisper_no_words` / `whisper_no_segments` / `whisper_result_invalid`等の既存fallback reasonへ写像される。unavailable / integrity / load / memory / transcribe failureが警告成功に変換されず、loader内部failure codeとB5上位failure classの写像も固定する。
- `generate_vmd_from_text_wav()`にtiming planがないproduction呼出しが`PipelineError(error_code="timing_plan_build_failed", detail_code="analysis_request_missing")`をraiseし、暗黙の`small` loadへ進まない。既存writerテストはexplicit timing planを使用する。
- FFmpeg PATH補正、fixed morph、Latin profile、preset、diagnostics observations、fingerprint、30fps VMDが回帰しない。

### 11.3 UI / Apply / rollback

- selectedとactiveが異なる間、Apply対象はverified candidateに限定される。
- 初期状態、成功、明示clear、同一active modelの復元可能な通常cancelでは`whisper_failure_class=none`となり、candidate準備中のfailure / cancelが旧activeのfailure classを上書きしない。
- candidate load前・load失敗・settings save失敗・cancel・closeではold active / analysis / Preview / diagnostics / VMDが変わらない。
- Apply専用のmerge saveが成功した後だけactiveがcandidateになり、保留中のcoalesced saveや古いtimer callbackがcandidateのactive設定を上書きしない。
- settings保存成功後にfull re-analysisが行われ、`SettingsSaveResult.succeeded == False`ではcandidateをactiveにしない。
- post-commit model_changed failure / cancelではold analysisへrollbackしない。VMD saveabilityもfalseになる。
- same-model ordinary cancelは既存契約に従って復元できる。
- transcription editは同一active key + manifestのretained timingだけを再利用する。
- selected / active / loaded / analysis / retained表示が相互に混同されない。
- workerはopaque `candidate_session_id`を含む`candidate_ready`通知後に終了し、UI callbackのcommit/reject待ちでworkerを保持しない。ready candidateのsession ID / generation照合、terminal transition、duplicate callback、cancel、close、shutdown、stale callbackのrejectとunloadが一回だけ実行される。
- Busy、late callback、stale generation、wx close、theme stateの既存回帰がない。

### 11.4 Delete / root / lifecycle

- B4 providerの呼出し形が維持され、B4側からpermitを発行できない。
- production issuerのcall siteがB5 runtimeの内部issuer seamだけであり、シグネチャが`(*, model_key, manifest_identity, artifact_id) -> OwnershipReleasePermit`に固定され、B4 worker / controller / UIがprivate token、permit constructor、test-only issuerを参照しない。
- active lease、pending Apply、analysis中のdeleteはpermit発行前に拒否される。
- permitは一回だけ消費でき、delete失敗やcancelで再利用できない。
- active model delete後にsilent fallbackせず、old analysis / Preview / diagnostics success / VMD saveabilityがinvalidになる。
- root changeで旧runtime unload、candidate store / runtime生成、managed settings保存、store/runtime/provider差し替え、rescanの順序が固定され、保存失敗時はold active / analysisを維持する。same manifest verifiedならsemantic resultを保てるが、新rootのunavailable / integrity mismatchではinvalidになる。保存成功後にrescan開始だけが失敗した場合は、新root設定と新store/runtimeを保持したままscan pending / fail-closedとし、verified確認が終わるまで新規解析を開始しない。旧rootへの暗黙rollbackは行わない。
- root変更後のrescan開始失敗は、設定・新root・新runtimeを旧rootへ戻さず、scan pending / fail-closedとして明示的に再試行可能な状態へ戻す。
- close時にAppControllerがruntime managerをshutdown状態へ遷移させ、late resultがstateを再活性化せず、lease完了後にruntime strong ownerが残らない。

### 11.5 Compatibility gate

- Python 3.13.x executableを明示し、loader / runtime / selected analysis / voice-only / rollback / wx lifecycleの対象テストを実行する。
- `pyproject.toml` と `requirements.txt` がともに `openai-whisper==20250625` を維持していることを確認する。
- Python 3.14.3での補助実測結果があっても、3.13 gateの代用にしない。

### 11.6 手動GUI確認（実装後に実施）

temporary model storeを使い、verified small / medium / turbo相当のfixtureを用意する。Download、Apply、model切替、TEXT + 音声、voice-only、transcription edit、cancel、delete、storage root変更、window closeを確認する。network切断時に解析がdownloadへ進まないこと、old resultのsaveabilityがfail-closedになること、wx themeとBusy表示が維持されることを確認する。実MMDによるVMD / WAV同期はMS26へ残す。

## 12. 受け入れ条件

- [x] TEXT + 音声およびvoice-onlyの全Whisper timing経路が、MainFrameからwhisper_timingまで同一active model key / manifest identityを受け取る。
- [x] 解析前にverified availability、manifest、size、SHA256が確認され、B2 `VerifiedWhisperCheckpoint` だけがB1 loaderへ渡る。
- [x] `openai-whisper==20250625`、version gate、v20250625 alignment heads / private API fail-closedが維持される。
- [x] 解析時の暗黙download、network、official key + `download_root`、path再open、直接 `whisper.load_model()` が存在しない。
- [x] word timestamp優先、segment fallback、voice-only一回認識、existing timing regressionが維持される。
- [x] selected / active / loaded / analysis / retained identityと、`model_changed` / `transcription_edit` の境界がテストで固定される。
- [x] `whisper_failure_class`がMS24 Block Breakdownの列挙値から逸脱せず、結果不足は既存fallback reason、`analysis_request_missing`は内部detailと`timing_plan_build_failed`へ分離される。
- [x] B1 / B2のdetail code、memory wrapper、transcribe exception、cancel / stale generationが8.1.1の固定写像へ従い、detail codeを保持する。初期値・成功時・明示clear時は`none`であり、B5状態契約に`None`を残さない。
- [x] Whisper timingは正常なresult shortageだけをsegment fallback対象とし、loader / device / memory / transcribe / FFmpeg / network failureを再試行または警告成功へ変換せず、detail codeと原因chainを保持する。
- [x] rollback identityにmodel key / manifest identityが含まれ、model unavailable、integrity mismatch、load failure、memory failure、model_changed後のcancel / failureで旧analysisへrollbackしない。
- [x] 上記blocked failureでは旧analysis、Preview、diagnostics success、VMD saveabilityが適切にfail-closedとなり、activeを別modelへ暗黙fallbackしない。
- [x] 同一active modelで契約上復元可能な通常cancelと、transcription editのretained reuseが既存仕様どおりに動く。
- [x] 現行`lru_cache(maxsize=2)`がsingle-active cacheに置き換わり、cache identityにmodel key、canonical storage root、manifest identityが含まれる。
- [x] strong ownerが一件で、switch、root change、delete、exitにexplicit eviction / unload / device cleanupがある。GCだけに依存しない。
- [x] B4のownership provider / opaque permit接続点を壊さず、production permit issuerがB5だけである。
- [x] active deleteはlease確認、unload、identity invalidation、permit発行、B4 deleteの順で行われる。
- [x] Applyはcoalesced saveとは別の専用merge commitを使い、`SettingsSaveResult.succeeded`確認前にactive identityを変更しない。
- [x] Apply workerはopaque `candidate_session_id`とgenerationを含むcandidate ready通知後に終了し、runtime managerが候補を保持する。commit/reject、cancel、close、shutdown、stale callbackの照合・terminal transition・unloadが一回だけ実行され、無期限待機を残さない。
- [x] `generate_vmd_from_text_wav()`のproduction direct pathはtiming planなしにWhisperを起動せず、`PipelineError(error_code="timing_plan_build_failed", detail_code="analysis_request_missing")`をraiseしてfail closedする。
- [x] MS23固定morph、Latin profile、preset、diagnostics、fingerprint、VMD 30fps、FFmpeg PATH補正、既存voice-onlyが回帰しない。
- [ ] Python 3.13.x compatibility gateを満たす。Python 3.14.3だけを根拠に合格宣言しない。
- [x] 実MMD検証、package、releaseはそれぞれMS26、MS27へ先取りされない。

### 12.1 実装後の到達状態

- [x] B5のruntime / analysis integration、Apply、rollback、delete ownership、root change、shutdownを実装した。
- [x] B5専用テストと既存回帰を実行し、Python 3.14.3環境でfull pytest `872 passed, 2 skipped`、exit code `0`を確認した。
- [x] `compileall -q src`、`git diff --check`を確認した。
- [x] ユーザー報告による手動GUI確認を受領した。確認主体はユーザーであり、CodexのGUI実行結果ではない。
- [ ] Python 3.13.x compatibility gate。3.14.3の結果を代替証拠にしない。
- [ ] 実MMDによるVMD / WAV読み込み・リップ同期確認。MS26へ引き継ぐ。
- [ ] package / release readiness。MS27へ引き継ぐ。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| 旧`lru_cache`と新runtimeが併存し、暗黙loadが残る | `whisper_timing`のproduction entry pointをsession必須にし、`whisper.load_model` / download呼出しをテストで禁止する |
| model keyだけでmanifest違いを再利用する | analysis identityとcache identityの両方にmanifest identityを必須化する |
| candidate load中に旧modelとcandidateを同時保持してmemory failureになる | 旧runtimeを先に明示evictし、managerだけが一件のstrong ownerを持つ。旧結果はmodel objectではなくimmutable resultとして保持する |
| candidate準備失敗で旧結果まで消える | active commit pointをsettings merge成功後に置き、precommit failureとpostcommit failureを分離する |
| active commit後に旧analysisをrollbackしてmodel identityが混ざる | `model_changed`をblocked rollback reasonにし、analysis / Preview / VMDを明示invalidateする |
| pipelineの既存fallbackがmodel infrastructure failureを成功に変える | result-shortage / fallback reasonとinfra failureを別detailにし、`load_failure` / `memory_failure` / `transcribe_failure`はfatal failureとしてfallback層を通過させない |
| B1 / B2のdetail codeが実装者ごとに異なるfailure classへ写像され、rollback / saveabilityが揺れる | 8.1.1のcode・例外・優先順位表を唯一の写像契約とし、detail codeを保持したまま上位classを付与する。OOMはwrapper codeより`memory_failure`を優先する |
| Whisperのloader / transcribe例外が既存のsegment-only retryへ入り、infra failureが結果不足fallbackへ変換される | 正常なresult shortageだけをsegment fallback対象とし、例外時はretryせずdetail code・原因chainをfatal failureへ伝播する。例外時retry回帰を非再試行へ補正する |
| `whisper_failure_class`の`None`と正本の`none`が混在し、diagnosticsやclear後の状態が不定になる | 初期化・成功・明示clear・復元可能な通常cancelは`none`へ統一し、candidate準備中のfailure / cancelはactive状態を変更しない |
| UIまたはworkerがApply判断を待ち続けてcandidateを保持する | workerはready callback後に終了し、managerがcandidate sessionを保持する。commit/rejectは一回だけ許可し、cancel / close / shutdown / stale callbackはrejectへ遷移させる |
| delete前にactive modelまたはdevice resourceが残る | leaseを確認し、explicit cleanup後にB5だけがone-shot permitを発行する |
| B4がpermitを直接作れるようになる | `WhisperModelStore._issue_ownership_release_permit_for_runtime(*, model_key, manifest_identity, artifact_id)`をB5 runtimeだけが呼び、permit typeの互換importは維持する。B4テスト用issuerはproduction codeから分離する |
| storage root変更で結果identityを不必要に壊す、または欠損結果を残す | 旧runtime解放、candidate store / runtime生成、managed settings保存、store/runtime/provider差し替え、rescanの順序を固定する。保存失敗時はold active / analysisを保持し、same manifestのverified結果だけsemantic identityを保つ。rescan開始失敗後は新rootを保持してscan pending / fail-closedにする |
| coalesced settings saveがApplyのactive commitを後から上書きする | Apply専用merge saveを使い、成功・失敗時にpending save flagとgenerationを整理して古いtimer callbackを無効化する |
| `generate_vmd_from_text_wav()`がtiming planなしでsmallを暗黙loadする | production direct pathでは`PipelineError(error_code="timing_plan_build_failed", detail_code="analysis_request_missing")`をraiseし、GUIはverified timing planを必須化する。writer testはexplicit timing planを使う |
| B6のdiagnostics責務をB5が先取りする | B5はfailure source、identity、state invalidationを担当し、summary / report mappingはB6へ渡す |
| Python 3.14.3で動いたため3.13互換を誤認する | 3.13.xを独立gateとし、実行ファイル、終了コード、対象テストを記録する |
| runtime user dataや実モデルをテストが変更する | temporary path、fixture、mock loaderを使用し、指定されたuser dataを参照・変更・stageしない |

### 13.1 実装時に確認が必要だが、ユーザー判断を要しない点

- DTOを`whisper_model_runtime.py`へ置くか、共有契約moduleへ分離するかはimport循環と既存公開APIで決める。
- permit型は`whisper_model_store.py`に残し、B4互換importを維持する。正確な内部issuer seamを`_issue_ownership_release_permit_for_runtime(*, model_key, manifest_identity, artifact_id) -> OwnershipReleasePermit`として同ファイルに追加し、production call siteは`whisper_model_runtime.py`だけにする。公開constructor / 公開factory / test-only issuerのproduction利用は行わない。
- loaderがdevice cleanupで返す例外の詳細は、実際のtorch / device APIに合わせてfailure classへ写像する。
- B1 / B2のdetail codeと上位failure classは8.1.1の対応表を変更せず、実装時に新しいcodeが必要になった場合は先に同表・テスト・受け入れ条件を更新する。
- apply準備中に旧runtimeをevictするため、candidate failure後に旧modelを即時再loadしない。旧解析結果は保持し、次の解析時にverified DTOから再loadする。
- root変更では旧runtime解放後のsettings save失敗を、old active / analysis保持・loaded=None・旧model暗黙再loadなしとして扱う。新rootのrescanが終わるまで新規解析を開始しない。
- `loader_failure` / `transcription_failure`ではなく、B5上位failure classは`load_failure` / `transcribe_failure`を使用する。B1の詳細failure codeは別フィールドへ保持する。

これらは実装上の配置・API詳細であり、B5の受け入れ境界を変えない。別方式が必要になった場合は、single-active、B5-only issuer、precommit preservation、postcommit fail-closedを維持できることを確認してから変更する。

## 14. Codex 実装時の注意

- 本計画の対象はMS24-B5だけとし、B6 diagnostics summary、B7 documentation closeout、MS26 actual MMD、MS27 package / releaseを実装へ混ぜない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を読み取り、変更、stageしない。テストfixtureはtemporary pathに限定する。
- Qt / PySide6、cloud ASR、network access、Whisper auto-downloadを追加しない。
- `pyproject.toml` / `requirements.txt`の`openai-whisper==20250625`を同期維持し、依存追加が必要になった場合は実装を止めて理由、license、package影響、NOTICE影響を別途確認する。
- B4が作った`start_whisper_availability_rescan()`とsettings merge、foreground management、cancel / Busy境界を壊さない。B4のdownload scanとB2 post-promote scanの役割を混同しない。
- B4の`OwnershipPermitProvider`を残し、B4 workerにpermit発行責務を戻さない。permitは対象manifest、artifact identity、active leaseと照合して一度だけ発行する。Apply専用settings commitとroot変更専用lifecycleを、通常のcoalesced saveやB4のrescan callbackへ委譲しない。
- MainFrame、AnalysisWorker、pipeline、whisper_timingの全経路を一部だけ修正して終わらせない。TEXT + 音声とvoice-onlyの両方で同じmodel identityを確認する。
- `recognize_audio()`のword-first / segment-fallbackを維持し、結果不足fallbackとmodel infrastructure failureを同じwarning処理に入れない。
- analysis result、Preview、diagnostics success、VMD saveabilityは同じanalysis identityの世代として扱う。failure後に旧fingerprintだけを残してsave可能にしない。
- runtime manager以外がraw loaded modelをstrong保持しない。sessionはmanagerのleaseとして扱い、delete / switch / exitを妨げる処理をworker-safeにする。
- Applyのactive commitはcandidate load成功とApply専用managed settings merge成功の後に置く。workerはUI判断を待たずready callback後に終了し、managerがcandidate sessionを保持する。保存前のfailureでは旧activeを保持し、保存後のmodel_changed failureでは旧analysisをrollbackしない。`generate_vmd_from_text_wav()`のtiming planなしproduction pathは`PipelineError(error_code="timing_plan_build_failed", detail_code="analysis_request_missing")`をraiseして拒否する。
- late callback、job generation、window close、cancel、management Busyの組み合わせをテストする。UI threadでworker完了を同期待機しない。
- 既存MS23の固定morph、Latin profile、preset、diagnostics、fingerprint、VMD 30fps、FFmpeg PATH補正、voice-only behaviorを変更しない。
- Python 3.13.x compatibility gateを実装完了条件に含める。現行Python 3.14.3の結果を代替証拠にしない。
- 実装後の検証は、まずB5のloader/runtime/propagation/rollback単体、次にpipeline・voice-only・wx lifecycle、最後に必要な手動GUIの順で行う。実MMD確認はMS26、package/release readinessはMS27へ引き継ぐ。
- 完了報告では、変更ファイル、実装内容、実行テストと終了コード、未実行のPython 3.13 / GUI / 実MMD / package確認、仕様逸脱、残課題を分けて記録する。
