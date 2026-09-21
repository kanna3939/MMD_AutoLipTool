# MS24-B3 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: `MS24 Whisper Model Selection`
- 対象Block: `MS24-B3 設定・UiState・モデル選択UI`
- 作成日: 2026-08-23
- 作成時branch: `feature/MS23-implementation`
- 作成時HEAD: `b011b37 Implement MS24-B2 model storage core`
- 直接依存: `MS24-B1`（`eafdc16`）、`MS24-B2`（`b011b37`）
- 後続依存: `MS24-B4`、`MS24-B5`、`MS24-B6`
- 文書状態: **Implementation Plan / P2-P3 Corrections Applied / Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) / Committed `a27a26f`**
- 本文書の権限: 計画段階では本文書だけを変更対象とし、実装着手後のコード変更は承認済みB3スコープに限定する。依存関係、runtime user dataは変更しない

MS24-B3では、非エンジニアユーザーがモデルを安全に切り替えられるように、モデル候補の選択、現在のactive model、保存済み設定、ローカルavailability表示を分離する。ユーザーが候補を選択しただけでは、network、Whisper load、既存解析の無効化を発生させない。

ユーザー判断が必要な前提は、すでに採用済みの次の方式で固定する。

```text
候補選択
  -> Download & Verify（MS24-B4）
  -> Apply and Re-analyze（MS24-B5）
```

## 2. 背景

MS24-B1で、`small / medium / turbo`のversioned manifest、manifest identity、`VerifiedWhisperCheckpoint`、v20250625のversion / alignment-head gate、network-unreachable loaderが固定された。MS24-B2では、モデル保存先、availability、exact size / SHA256検証、canonical `.part`、atomic promote、ownership permit付きdelete境界が実装された。

現行コードとの照合で確認した事実は次のとおりである。

- `SettingsStore`にはB2所有の`whisper_models_dir`が追加済みであり、空文字を既定保存先へ解決する最終処理は`WhisperModelStore`が所有する。
- `WhisperModelStore.scan_all()`はネットワークやWhisper loadを行わず、manifestに基づくavailabilityを返す。ただし、verified候補の確認ではartifact全体のSHA256を読むため、起動UIスレッドから同期実行してはならない。
- `UiState`にはWhisperのselected / active / loaded / analysis identityはまだ存在しない。
- `AppController.load_startup_state()`は`SettingsStore`、preset store、profile storeを一つのstartup flowで読み込む。B3はこの境界へWhisper設定の読込とavailability scanの初期`pending`投影を追加し、全件scanは専用workerへ渡す。
- `AppController.flush_pending_save()`はcoalesced saveと`full` / `identity_only`の保存優先度を持つ。B3は既存のprofile / preset保存契約を壊さず、Whisper identityを追加する。
- `RightPane`にはモデルプロファイルtabがあり、Select / Apply分離、panel revision、Busy lock、stale request拒否、theme反映の実例がある。ただし、Whisperモデルとモデルプロファイルは別の概念であり、同じUI stateや表示名を流用してはならない。
- `MainFrame.apply_settings()`と`src/gui_wx/app.py`にはstartup settingsをViewへ投影する既存入口がある。
- 設定メニューの設定ダイアログ入口はStubであるため、Whisper管理UIは既存RightPaneへ専用tabまたは専用領域として追加する。

MS24-B2実装後に残っていたrouting文書のB2未着手表記は、B3実装開始前の同期として解消済みである。本planはlive codeと`b011b37`を実装ベースラインとし、Block Breakdown、Index、MS24-B2 plan、RoadmapはB2実装済み・B3 plan作成済みの状態へ同期済みとして扱った。fresh read-only pre-implementation check通過後にB3のproduction code / test code / GUIを実装し、自動検証とユーザー手動GUI確認まで完了した。

## 3. 目的

1. `small / medium / turbo`をGUIで明示的に候補選択できるようにする。
2. selected candidateとactive model identityを別々に保持・永続化する。
3. 旧INIや新キー欠落時も、既定モデル`small`を安全に復元する。
4. active modelが未配置・未検証でも、候補選択や起動時に自動download / fallback / loadを行わない。
5. B2のavailability、保存先、manifest metadataを、ユーザーが判断可能な表示へ投影する。
6. 既存のMS23モデルプロファイル、preset、固定モーフ、diagnostics、fingerprint、workspace reset契約を維持する。
7. B4/B5が後続実装できる明確なUI state、保存、revision、Busy境界を固定する。
8. 起動時の全件SHA256検証でUIを長時間停止させず、非エンジニアユーザーが確認中・確認済み・確認失敗を区別できる状態を提供する。

## 4. In Scope

- `SettingsStore`へのselected / active model identityキーの後方互換追加
- `active_whisper_manifest_identity`のcatalog照合と保存境界
- `UiState`へのWhisper model selection state追加
- selected、active、availability、保存先表示、設定エラーの分離
- B2 `WhisperModelStore.scan_all()`を使った起動時・表示更新時のlocal-only availability投影。全件scanはB3専用の読み取り専用workerで非同期実行する
- 既存RightPaneへのWhisper専用モデル管理tabまたは同等の専用領域
- `small / medium / turbo`の表示名、用途、概算VRAM、概算速度、exact download size、保存状態の表示
- 候補選択とactive表示の分離
- panel revisionによるstale selection request拒否
- 解析中などのBusy状態におけるモデル選択lock
- coalesced settings saveへのselected / active identity追加
- 旧INI、新キー欠落、未知値、identity不一致、設定保存失敗の状態契約
- startup、workspace reset、theme切替、既存model profile tabとの回帰
- B3専用GUI/state/settings testと関連回帰
- B3専用availability scan workerのpending / success / failure / stale / shutdown境界
- B4/B5が後続でDownload、Apply、Re-analyzeを接続できるcallback / DTO境界の準備。ただし、その処理自体は実装しない

## 5. Out of Scope

- HTTP / HTTPS、Content-Length取得、redirect、timeout、progress、download worker、cancel、delete worker（MS24-B4）
- B4のdownload worker、既存`AudioWorker`へのWhisper処理混在、ネットワーク処理。B3のscan workerはlocal-only availability確認だけを担当する
- 実ネットワーク、実モデル重みdownload、実モデルを使った解析
- `Apply and Re-analyze`の解析伝播、`AnalysisWorker`、pipeline、Whisper loader呼出し（MS24-B5）
- loaded model ownership、single-active cache、明示unload、device resource cleanup（MS24-B5）
- `loaded_model_identity`や`analysis_model_identity`のproducer実装。B3ではUI state上の分離境界を予約・定義するだけで、値の更新はB5が所有する
- `WhisperDiagnosticsSummary`、diagnostic report、model-aware rollback、memory failure復帰（MS24-B6）
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のroot runtime実体の読込・変更・生成・stage
- PyInstaller onefile、package、release、tag、push、merge、branch操作（MS27または明示承認時）
- Qt / PySide6、cloud ASR、音声外部送信、background通信、telemetry
- 固定モーフ`あ / い / う / え / お`、MS23 Latin profile、preset、fingerprint schemaの変更
- 実MMDでのVMD / WAV読込・リップ同期確認（MS26）

## 6. 前提条件

### 6.1 モデルidentity

manifest由来のidentityだけを正本とする。UI入力やINIからofficial URL、filename、SHA256、exact size、package versionを上書きしない。

```text
selected_whisper_model_key
active_whisper_model_key
active_whisper_manifest_identity
```

`selected_whisper_model_key`からselected側のmanifest identityを表示時にcatalogから導出する。selected側のidentityを別のユーザー入力値として保存しない。

### 6.2 保存キー

| キー | 既定値 | 所有者 | B3の扱い |
| --- | --- | --- | --- |
| `whisper_models_dir` | `""` | B2 | 読み取り・表示・B2 APIへの受け渡しだけ。B3はpath validationを再実装しない |
| `selected_whisper_model_key` | `"small"` | B3 | 候補選択の正本。選択だけでactiveを変更しない |
| `active_whisper_model_key` | `"small"` | B3/B5境界 | 起動時のlegacy defaultと、B5のApply成功後のactive更新を保存する |
| `active_whisper_manifest_identity` | 空文字（旧INI互換） | B3/B5境界 | catalogから照合し、旧INIではactive keyから補完してidentity-only correction候補にする |

SettingsStore自身はmodel catalogの全責務を持たず、文字列・空値・型の安全な正規化を行う。`small / medium / turbo`の許可集合、manifest identityとの一致、設定不整合の状態化はB3のstartup resolverが行う。

### 6.3 旧INIと不整合設定

- 新キーがない旧INIは、selected / activeを`small`へ補完し、catalogから`small`のmanifest identityを解決する。
- selected keyだけが未知または不正な場合は、selectedだけを`small`へ戻し、activeと既存解析を変更しない。
- active keyとmanifest identityの組み合わせが未知・不一致の場合は、別のavailable modelへ暗黙fallbackしない。`active_config_invalid`として表示し、明示的な候補選択と後続Applyを要求する。
- active artifactが`missing`、`partial`、`invalid_size`、`invalid_sha256`、`read_failed`の場合も、active identityを別モデルへ自動変更しない。availabilityを表示し、解析開始可否はB5が判定する。
- 設定保存失敗時はメモリ上の候補選択を無言で巻き戻さず、保存失敗を表示する。次回起動で復元されない可能性は既存SettingsStoreの保存失敗契約に従って通知する。

### 6.4 B2境界

- 起動時のavailability scanはread-onlyであり、root directoryを暗黙作成しない。
- B2の`StorageRootResolution`、`ModelAvailability`、`resolve_whisper_models_dir()`、`WhisperModelStore.scan_all()`を使用する。
- `scan_all()`の実行はUIスレッドから切り離す。起動時はまず`availability_scan_status=pending`（表示文言は「確認中」）を投影し、B3専用workerの結果だけをcontroller経由で反映する。
- B3専用workerはネットワーク、Whisper loader、model load、analysis、directory作成を呼ばない。既存`AudioWorker`とB4 download workerを再利用・拡張しない。
- scan結果には`availability_scan_job_id`とscan専用の`availability_scan_generation`を束縛し、shutdown状態を検証してから反映する。候補選択用の`panel_revision`はscan結果のguardに流用しない。古い・終了後の結果はUIや設定を変更せず破棄する。
- B3はrelative / UNC / remote / device pathを自分で判定しない。
- `ModelAvailability`のstable failure codeは表示用文言へ変換しても保持し、B4/B6へのhandoffで失わない。B3 stateでは`availability_scan_failure_code`と`availability_scan_failure_detail`を別fieldとして保持する。
- B2の`StorageRootResolution`では`failure_code`と`message`を正本として扱う。`failure_code`からB3が安全なユーザー向け日本語通知を生成し、B2の`message`を含むtechnical detailは診断・handoff用に保持するだけで、通常UIへraw表示しない。未知のfailure codeはgenericな安全通知へfail closedする。

### 6.5 既存MS23契約

- モデルプロファイルとWhisperモデル選択を別tab、別state、別identityとして扱う。
- `ModelProfileState`、profile-aware history、preset resolution、Latin output names、`ms21-effective-output-v1` fingerprintを再実装・変更しない。
- workspace resetは入力、解析、Preview、playbackだけを消し、モデル設定、profile、preset、保存先を消さない。

### 6.6 MS24 canonical identityとの対応

本planのstate表で用いる`loaded_model_identity`と`analysis_model_identity`は、実装時に次のMS24 canonical fieldへ対応付ける。genericな別identityを新設して、B5/B6の正本を二重化してはならない。

| 本planのstate表記 | MS24 canonical field | producer / 更新境界 |
| --- | --- | --- |
| `loaded_model_identity` | `loaded_whisper_model_key` + `model_manifest_identity` | B5のverified-local loader成功結果だけが更新する |
| `analysis_model_identity` | `analysis_whisper_model_key` + `model_manifest_identity` | B5の解析成功結果だけが更新する |
| retained timing identity | `retained_whisper_timing_model_identity` | B5のretained timing / transcription edit境界が所有する |
| rebuild reason | `analysis_rebuild_reason` (`none | transcription_edit | model_changed | input_changed`) | B5が解析状態とともに更新する |
| failure class | `whisper_failure_class` | B5/B6が下位failure codeから投影する |

`model_manifest_identity`はB1 catalog由来のcanonical identityだけを受理する。B3のcandidate selectionは上表のB5/B6 fieldを作成・推測・更新せず、selection-only no-op契約を維持する。B5/B6の実装時は、上表のfield名をそのままhandoffおよび回帰テストの正本として使用する。

## 7. 対象ファイル

### 7.1 主変更対象

| 区分 | ファイル | B3での責務 |
| --- | --- | --- |
| 変更 | `src/core/settings_store.py` | selected / active / manifest identityのdefault、INI load/save、旧callerのpartial save保持 |
| 変更 | `src/gui_wx/ui_state.py` | `WhisperModelSelectionState`相当のselected / active / availability / panel revision / notice state |
| 変更 | `src/gui_wx/right_pane.py` | Whisper専用tab、metadata / availability表示、候補Choice、選択 callback、Busy / theme反映 |
| 変更 | `src/gui_wx/app_controller.py` | startup load、B2 scan、selection request、state projection、coalesced save、設定失敗通知 |
| 変更 | `src/gui_wx/main_frame.py` | RightPane接続、startup state反映、sync、action state、既存解析・profile UIとの境界 |
| 変更 | `src/gui_wx/app.py` | startup stateからMainFrameへWhisper selection stateを渡す |
| 新規 | `src/gui_wx/whisper_availability_worker.py` | B2 `scan_all()`だけを実行するread-only availability scan、結果DTO、例外の安定化、daemon終了契約 |
| 新規 | `tests/test_ms24_whisper_model_settings.py` | SettingsStore、旧INI、identity補完、不整合、保存失敗 |
| 新規 | `tests/test_ms24_whisper_model_ui_state.py` | UiStateのselected / active / availability、selection-only、reset、revision |
| 新規 | `tests/test_ms24_whisper_model_availability_worker.py` | pending、success、failure、stale、shutdown、no-network / no-loader / no-root-create |
| 新規 | `tests/test_wx_ms24_whisper_model_ui.py` | RightPane、MainFrame、AppController、theme、Busy、stale request |

実際のclass名・private helper名は実装開始時に現行命名規約と照合して確定する。ただし、責務と公開境界は本planから変更しない。

### 7.2 関連確認対象

- `src/core/whisper_models.py`: manifest由来のspec、catalog、identity、表示metadata
- `src/core/whisper_model_store.py`: B2のpath resolution、scan、failure code、root作成境界
- `src/core/whisper_model_loader.py`: B1のverified checkpoint / loaded identityをB3が直接呼ばないこと
- `src/gui_wx/worker_state.py`: B4専用download workerを既存AudioWorkerへ混在させない境界
- `src/gui_wx/whisper_availability_worker.py`: B3専用scan workerの結果配信・終了ガードを実装する新規境界
- `src/gui_wx/analysis_worker.py`: B5が後続でanalysis identityを接続する入口。B3では変更しない
- `src/gui_wx/analysis_rollback.py`: model-aware rollbackをB5/B6へ延期する境界
- `tests/test_wx_ms23_b5_model_profile_ui.py`: RightPaneのSelect / Apply、revision、Busy、theme、profile表示回帰
- `tests/test_ms23_b6_model_profile_lifecycle.py`: profile projection、workspace reset、既存identity回帰
- `tests/test_ms19_b4_analysis_worker_voice_only.py`: voice-only入力の既存解析入口をB3で変更しない回帰
- `tests/test_ms19_b8_workspace_reset.py`: model settingsをworkspace resetで消さない回帰
- `docs/GUI_State_Theme_Specification.md`: UiState / Action State / 表示状態、Busy、theme、late callback境界
- `docs/Error_Handling_Specification.md`: 設定読込・保存失敗、GUI通知、recoverability境界
- `docs/Implementation_Plan/MS24_Block_Breakdown.md`: B3責務、B4/B5依存、受け入れ条件
- `docs/Implementation_Plan/MS24-B1_Implementation_Plan.md`: manifest identity、verified loader、B5 handoff
- `docs/Implementation_Plan/MS24-B2_Implementation_Plan.md`: `whisper_models_dir`、availability、B2 API境界

### 7.3 変更禁止対象

- `presets.json`
- `profiles.json`
- `MMD_AutoLipTool.ini`のroot runtime実体
- 実モデル重み、`.part`、runtime `models` directoryの実体
- `src/core/whisper_model_store.py`のB2 filesystem契約（必要な不足が見つかった場合はB2修正へ戻す）
- `src/core/whisper_model_loader.py`、`src/core/whisper_timing.py`、`src/core/pipeline.py`
- `pyproject.toml`、`requirements.txt`、`MMD_AutoLipTool.spec`、依存関係

## 8. 実装方針

### 8.1 Stateの正本とprojection

`UiState`にWhisper専用の状態を追加し、RightPaneはそのprojectionだけを表示する。RightPane内のChoice選択値を正本にしない。

```text
SettingsStore
  -> startup resolver
  -> UiState.whisper_model_selection
  -> RightPane.WhisperModelPanelState
  -> wx controls
```

最低限のstate項目は次のとおりとする。

| State | 内容 | B3で更新するか |
| --- | --- | --- |
| `selected_model_key` | ユーザーが現在選んでいる候補 | する |
| `active_model_key` | 現在適用済みとして保存されたモデル | startup補完以外はB5のApply境界 |
| `active_manifest_identity` | active keyに束縛されたmanifest identity | startup補完以外はB5のApply境界 |
| `availability` | B2 scanの各モデルartifact状態 | B2 scan結果を投影 |
| `availability_scan_status` | `idle | pending | succeeded | failed` | B3のscan lifecycleを投影。audio / download Busyとは別軸 |
| `availability_scan_job_id` | 現在のscan結果へ束縛する単調なjob ID | B3専用worker開始時と結果反映時に検証 |
| `availability_scan_generation` | scan開始時にcaptureする単調なgeneration | 候補選択の`panel_revision`とは独立。scan結果受領の整合性に使用 |
| `availability_scan_failure_code` | stable failure codeまたは`None` | `failed`時に保持し、表示文言と診断情報を分離 |
| `availability_scan_failure_detail` | B2の`message`またはscan workerが安定化したtechnical detail、成功時は`None` | B4/B6 handoff・診断用に保持する。通常UIへ直接表示せず、rawの例外文字列・絶対パスをUI契約にしない |
| `storage_root_display` | B2が解決した保存先の表示値 | する |
| `active_config_status / reason` | identity不一致などの設定状態 | する |
| `loaded_model_identity` | 実際にload済みのidentity | B5所有。B3は推測しない |
| `analysis_model_identity` | 解析結果に束縛されたidentity | B5所有。B3は推測しない |
| `panel_revision` | stale request拒否用の単調増加値 | candidate selection callback専用。scan結果受領には使用しない |
| `management_busy` | B4のdownload/delete等を受ける将来境界 | B3ではUI lockに利用するだけ |

`loaded_model_identity`と`analysis_model_identity`は、上記canonical fieldのprojection名であり、active identityから導出しない。値が未接続の間は`None`または未接続状態として表示し、B3のactive表示をloaded / analysis表示へ流用しない。

### 8.2 Candidate selectionの状態契約

候補選択callbackは次の順序で処理する。

1. `is_busy`、`management_busy`、shutdown、panel revision、model keyを検証する。
2. 不一致・未知key・無効なrequestは状態、設定、表示を変更せず拒否する。
3. selected candidateだけを更新する。
4. active key、active manifest identity、loaded / analysis identity、retained timing identity、`analysis_rebuild_reason`、`whisper_failure_class`、`current_timing_plan`、`analysis_result_valid`、`analysis_pending_rebuild`、Preview、diagnostics、VMD saveabilityを変更しない。
5. network API、Whisper loader、`whisper.load_model()`、B2 preflight、downloadを呼ばない。
6. `panel_revision`を更新し、coalesced settings saveを要求する。`availability_scan_generation`は変更しない。

この段階では、選択候補が`missing`や`invalid_sha256`であっても候補として表示できる。ただし「利用可能」「適用済み」と誤表示せず、Download & Verifyが必要であることを表示する。Download操作そのものはB4で追加する。

### 8.3 Startup resolver

`AppController.load_startup_state()`には設定・catalog metadata・初期state投影だけを追加し、artifact全件scanを同期実行しない。startup flowは次のとおりとする。

1. 既存SettingsStore、preset、profileを読む。
2. `selected_whisper_model_key`、`active_whisper_model_key`、`active_whisper_manifest_identity`を読む。
3. B1 catalogで許可model keyとmanifest identityを照合する。
4. B2の`resolve_whisper_models_dir()`で`StorageRootResolution`を取得する。解決成功時だけ`resolved_path`から`WhisperModelStore`を構築し、catalog metadataと解決済みrootをstateへ渡して`availability_scan_status=pending`、`availability=未確定`を投影する。
5. 明示設定された`whisper_models_dir`の解決が失敗した場合は、既定の`models`へfallbackせず、`WhisperModelStore`を構築せず、availability workerも起動しない。B2の`failure_code`を`availability_scan_failure_code`へ、B2の`message`を`availability_scan_failure_detail`へ写像して`availability_scan_status=failed`をstateへ投影し、selected / active identityを保持する。root directoryは作成しない。空文字・空白だけの場合の既定root解決はB2契約どおりに扱う。
6. 旧INIの欠落キーは`small`へ補完し、catalog identityを解決する。
7. active pairの不一致は`active_config_invalid`としてfail closedし、availableな別modelへのsilent fallbackを行わない。
8. startup stateをMainFrameへ渡し、RightPaneへ初期projectionを行う。UIは確認中または保存先エラー状態を表示し、初期画面の表示をscan完了まで待たせない。
9. `MainFrame.apply_settings()`後の安全なstartup境界で、保存先解決に成功した場合だけ`AppController.start_whisper_availability_scan()`を一度だけ呼び、B3専用workerへ`WhisperModelStore.scan_all()`を渡す。
10. worker結果は`availability_scan_job_id`、capture済み`availability_scan_generation`、controllerのshutdown状態を確認してからUiStateへ反映する。候補選択で`panel_revision`が変わっても、job IDとscan generationが一致する結果は破棄しない。不一致・終了後のlate resultはno-opにする。
11. 旧INI補完またはidentity correctionが必要な場合だけ、既存のcoalesced identity-only save契約に従って保存候補にする。availability scanの成功・失敗と保存先解決失敗は設定保存の成否と混同しない。

startupではdirectory作成、download、model load、解析開始、既存解析の無効化を行わない。scan失敗または保存先解決失敗時は選択・active設定を保持し、`availability_scan_status=failed`とfailure codeから生成した安全なユーザー向け通知を表示する。`availability_scan_failure_detail`は診断・handoff用に保持するが、通常UIへraw表示しない。明示設定された不正rootを既定rootへfallbackせず、retryの自動開始、download開始も行わない。

### 8.4 SettingsStore save契約

- selected candidate変更はfull saveで保存する。active identityだけのstartup correctionはidentity-only saveで保存する。
- 既存の`full > identity_only > none`優先度を壊さない。
- full saveで`whisper_models_dir`を再解決・再正規化しない。B2が保持する保存値を失わない形でSettingsStoreのpartial-save mergeを利用する。
- selected / active keyとmanifest identityは同一save snapshotから書く。keyだけ更新してidentityを古い値のまま残さない。
- save failure時はselection stateを表示上保持し、保存失敗通知と次回起動時の未復元可能性を示す。候補選択を暗黙にactiveへ反映しない。

### 8.5 RightPane UI

既存の「モデルプロファイル」tabと混同しない名称で、専用の「Whisperモデル」tabを追加する。最低限、次を表示する。

- 選択中の候補モデル
- 現在のactive model
- 選択候補の保存状態（missing / partial / verified / size mismatch / SHA mismatch / read failure等）
- `small / medium / turbo`のdisplay name
- exact download size
- VRAM目安、相対速度目安、推奨用途
- B2が解決した保存先
- 「候補を選択しただけでは、downloadや解析は開始されない」旨の説明
- 設定不整合、保存失敗、availability failureのユーザー向け通知

availability failureの通常UI通知は`availability_scan_failure_code`から固定写像する。`availability_scan_failure_detail`に含まれるOS例外、絶対パス、その他のraw technical detailは通常UIへ直接表示せず、診断・handoff境界だけへ渡す。未知のcodeや予期しない例外は、原因を断定しないgenericな安全通知へ写像する。

B3の実装範囲では、Download、Delete、Apply and Re-analyzeの実行処理を追加しない。後続Blockが接続するための状態・callback境界を用意し、未接続の操作を表示する場合は無効状態にする。無効な操作がnetworkやstate mutationへ到達してはならない。

### 8.6 Busy、stale、theme

- TEXT + 音声解析中、voice-only解析中、B4のdownload/delete操作中はモデル選択と保存先変更をlockする。
- 既存profile UIのBusy lockと同じprojection cycleで、Choice、後続action、status、noticeを更新する。
- panel revision不一致のselection requestは状態を変更しない。
- RightPaneの新規control、notice、dialogはSystem / Light / Darkのthemeへ追従する。
- availability scanはaudio解析BusyやB4 download Busyとは別の`availability_scan_status`で管理する。
- scan pending中も設定・候補表示は確認中と明示し、scan結果に依存するDownload / Apply操作は未接続または無効状態にする。候補選択自体はselection-only no-op境界を壊さない範囲で処理する。
- scan完了時の結果反映はjob ID、`availability_scan_generation`、shutdown guardを通す。`panel_revision`はselection callbackだけに使用する。controller終了後、または新しいscanが開始された後のlate resultは破棄する。
- availability workerはdaemonとして起動する。`request_exit()`は現在のscan jobを失効させ、UIスレッドはscan完了をjoinで待たない。close後のworker callbackはno-opにする。
- B3ではB4 download workerを作らず、既存AudioWorkerへWhisper処理を混在させない。追加するworkerはB3専用read-only scanだけとする。

### 8.7 既存契約との境界

- candidate selectionは既存解析をinvalidateしない。
- active identity変更とanalysis result invalidationはB5が所有する。
- diagnostics success / failureへのmodel identity投影はB6が所有する。
- profile / presetのactive guard、history、fingerprintはB3のmodel selection stateから独立して保持する。

## 9. 詳細ステップ

### Step 0: 実装開始前のrouting同期ゲート

MS24-B3のproduction code / test code / GUI実装は、次の文書同期が完了し、fresh read-only pre-implementation checkが通過するまで開始しない。

- `docs/MS20_and_Beyond_Index.md`のMS24現在フェーズを、B2 commit `b011b37`の実装済み状態へ同期する。
- 同Indexへ本planへのリンクを追加し、B3 Implementation Plan作成済み・実装未開始を明記する。
- `docs/Implementation_Plan/MS24_Block_Breakdown.md`のB2状態を実装済みへ同期する。
- `docs/Implementation_Plan/MS24-B2_Implementation_Plan.md`の文書状態を、`b011b37`で実装済み・targeted verification済みへ同期する。
- `docs/MS20_and_Beyond_Roadmap.md`のMS24-B2実装状態と、MS24-B3の次工程を同期する。
- 同期後にbranch / HEAD、対象文書、B2実装、関連テストを再確認し、B3実装前チェックの結果を記録する。

初回plan作成時のrouting同期は完了済みである。今回のP2/P3補正では、起動時scanの非同期・専用worker境界、scan generationの分離、worker終了契約、失敗情報fieldを本plan、Block Breakdown、Index、Roadmapへ同期した。その後fresh read-only pre-implementation checkを通過してB3を実装した。依存関係とruntime user dataは変更していない。

### Step 1: stateと設定契約を固定する

- selected / active / manifest identityのkey、型、default、legacy補完、invalid pairのfailure codeを定義する。
- `WhisperModelSelectionState`相当のimmutable projection / mutable UiState責務を確定する。
- loaded / analysis identityをactiveから導出しないことをtest先行で固定する。

### Step 2: SettingsStoreを拡張する

- default、INI load、normalize、merge saveへ3つのmodel identity keyを追加する。
- 既存callerが新keyを省略したpartial saveで、selected / active identityを既定値へ戻さない。
- bool、数値、空白、未知文字列、identity mismatchをB3 resolverへ安全に渡す。
- `whisper_models_dir`のB2責務とpath validationを変更しない。

### Step 3: startup resolverとavailability projectionを接続する

- `SettingsStore.load()`結果、catalog metadata、B2が解決したrootをstartup stateへ追加し、availabilityを`pending`として投影する。`load_startup_state()`内で`scan_all()`を完了まで待たない。
- `resolve_whisper_models_dir()`の`StorageRootResolution`を先に判定し、明示設定rootの解決失敗時は既定rootへfallbackせず、store構築・worker起動を行わず、B2の`failure_code` / `message`をB3の`availability_scan_failure_code` / `availability_scan_failure_detail`へ写像して`availability_scan_status=failed`へ投影する。通常UIの通知はfailure codeから安全に生成し、message/detailをraw表示しない。selected / active identityは保持し、root作成もしない。
- catalog identityを用いてactive pairを検証する。
- source / frozenともにB2が解決したrootを使い、startup directory作成・network・loadを行わない。
- `src/gui_wx/app.py`で`MainFrame.apply_settings()`後にB3専用scanを開始する。初期frame表示とscan開始順を固定し、worker callbackが未投影のframeへ直接触れないようにする。
- workerは`WhisperModelStore.scan_all()`だけを実行し、`job_id`、capture済み`availability_scan_generation`、snapshotまたは`failure_code` / `failure_detail`を結果DTOとして`wx.CallAfter`等の既存UI callback境界へ渡す。workerはdaemonとし、UIスレッドからjoinしない。controllerはjob ID、scan generation、shutdownを検証してから投影する。
- successはavailability snapshotと`availability_scan_status=succeeded`へ、例外はstable `failure_code` / `failure_detail`付き`failed`へ写像する。成功時はfailure fieldをclearする。いずれもselected / active identityを暗黙変更しない。

### Step 4: UiStateとRightPaneを実装する

- UiStateへWhisper selection stateを追加する。
- RightPaneへ専用tab、model rows、候補Choice、active表示、availability表示、noticeを追加する。
- model profile tabのstate、callback、label、button enable条件を共有しない。
- `Layout()`、`FitInside()`、theme style、panel revisionを既存RightPane規約へ合わせる。

### Step 5: selection requestを実装する

- revision、Busy、shutdown、model keyを検証する。
- selectedだけを変更し、active / loaded / analysis / existing analysisを不変にする。
- coalesced saveを要求し、保存失敗を既存SettingsStore通知へ接続する。
- selection-onlyでnetwork、Whisper、B2 preflight、解析、Preview rebuildへ到達しないことを確認する。

### Step 6: workspace resetと既存MS23契約を回帰する

- workspace reset後もselected / active / availability表示と保存先設定を維持する。
- profile / preset tab、Latin profile、固定モーフ、diagnostics、fingerprintの値・表示・historyを変更しない。
- 既存のstartup identity correction、profile save、preset saveとWhisper saveの優先度を確認する。

### Step 7: B4/B5 handoffを固定する

- B4がDownload & Verify、cancel、delete、transfer stateを追加できるpanel callback境界を明記する。
- B5がApply and Re-analyze、loaded / analysis identity、active update、analysis invalidationを追加できるstate境界を明記する。
- B3でB4/B5のworker、loader、pipeline、rollbackを先行実装しない。

### Step 8: GUIを含む検証を行う

- B3専用settings、UiState、availability worker、RightPane、startup、stale、Busy、shutdown、theme testを実行する。
- 既存MS23 profile UI、preset、workspace reset、voice-only、diagnostics回帰を実行する。
- 全モデルartifactが存在する場合でも、起動UIスレッドが`scan_all()`のSHA256完了を待たないことをworker seamで検証する。
- GUI変更を含むため、実装後にユーザー手動GUI確認を行う。実モデルdownload、network、実解析、実MMDは実施しない。

## 10. 状態遷移 / データ契約

### 10.1 Startup

```text
旧INI / 新INIをload
  ├─ identity keys missing
  │    -> selected=small
  │    -> active=small
  │    -> active identityをcatalogから解決
  │    -> identity-only correction候補
  ├─ selected key invalid
  │    -> selectedだけsmallへ補正
  │    -> active / 既存解析は変更しない
  ├─ active key + identity valid
  │    -> pairを保持
  └─ active pair invalid
       -> active_config_invalid
       -> silent fallback / load / downloadなし

B2 scan_all（local-only、B3専用worker）
  -> job ID / availability scan generation / shutdown guard
  -> UiState availability projection
  -> RightPane projection
```

起動直後は次のpending stateを先に表示する。

```text
load settings / catalog metadata
  -> availability_scan_status=pending
  -> MainFrame / RightPaneを表示
  -> B3専用workerでscan_all()
       ├─ success -> availability_scan_status=succeeded + snapshot + failure fields clear
       └─ failure -> availability_scan_status=failed + stable failure code/detail
```

### 10.2 Selection only

```text
active=A, selected=A, analysis=A
  └─[候補Bを選択]
       -> active=A
       -> selected=B
       -> loaded=A または未接続のまま
       -> analysis=A または未接続のまま
       -> existing timing / Preview / diagnostics / VMD saveability unchanged
       -> network / Whisper load / invalidateなし
```

### 10.3 後続Blockの境界

```text
selected=B
  └─[MS24-B4 Download & Verify]
       -> B2 availability verified
            └─[MS24-B5 Apply and Re-analyze]
                 -> active / loaded / analysis identity transition
                 -> old result invalidation
                 -> new modelで再解析
```

B3は点線部分のrequest / state受け口を定義するが、download、load、analysis result commitは実装しない。

### 10.4 Identity fieldの不変条件

| Field | 不変条件 |
| --- | --- |
| selected key | catalogの許可key、またはstartup補正前のinvalidをerrorへ写像。candidate選択だけでactiveを変更しない |
| active key | active manifest identityとpairで検証される。pair不一致はavailable modelへのfallbackをしない |
| active manifest identity | B1 catalogが生成したidentityだけを受理する。UI入力で作成しない |
| loaded identity | B5 loader成功結果だけが設定する。activeから推測しない |
| analysis identity | B5の解析成功結果だけが設定する。loaded / activeから推測しない |
| availability | B2 scan snapshot。download / load / ownership状態を混ぜない |
| availability scan status / generation | `panel_revision`と独立したscan lifecycle。候補選択だけではscanを失効させない |
| availability scan failure code / detail | `failed`時に保持し、成功時・新scan開始時に明示的にclearする |
| panel revision | candidate selection stale requestを拒否するため単調に更新する。scan結果のacceptance guardには流用しない |

## 11. テスト方針

### 11.1 SettingsStore / startup

`tests/test_ms24_whisper_model_settings.py`へ次を追加する。

- 新規3 keyのdefaultが`small / small / empty identity`であること
- 旧INIで3 keyがない場合のsmall補完とcatalog identity解決
- selected / active / manifest identityのround trip
- selected keyだけのpartial saveでactive pairを壊さないこと
- full saveとidentity-only saveの優先度、既存profile / preset key保持
- unknown key、bool、数値、空白、active pair mismatchのfail-closed result
- B2 `whisper_models_dir`をB3 saveが失わないこと
- settings save failure後のstate保持、通知、save-disabled契約
- root runtime `MMD_AutoLipTool.ini`を使わずtemporary pathだけを使うこと
- startup resolver / availability workerの全テストは、temporary SettingsStoreだけでなく、temporaryな`whisper_models_dir`を設定したtemporary SettingsStore、またはtemporary rootを明示したB2 `WhisperModelStore`を注入すること
- そのテストでは`resolve_whisper_models_dir("")`やrepository既定の`models` rootを使用せず、既定rootへ到達していないことをassertすること
- 明示設定されたrelative / UNC / remote / device pathの保存先解決失敗で、既定rootへのfallback、store構築、worker起動、root作成が起きないこと
- 保存先解決失敗のB2 `failure_code` / `message`が`availability_scan_status=failed`へ保持され、selected / active identityが変化しないこと
- 同じ失敗でfailure codeから安全なユーザー向け通知が生成され、B2 `message`由来のraw例外文字列・絶対パスが通常UIへ表示されないこと。未知のfailure codeはgeneric通知へfail closedすること

### 11.2 UiState / selection

`tests/test_ms24_whisper_model_ui_state.py`へ次を追加する。

- selected / active / loaded / analysis identityが別fieldであること
- candidate selectionがactive、analysis、`current_timing_plan`、`analysis_pending_rebuild`、Preview saveabilityを変更しないこと
- candidate selectionが`loaded_whisper_model_key`、`analysis_whisper_model_key`、`retained_whisper_timing_model_identity`、`analysis_rebuild_reason`、`whisper_failure_class`を変更しないこと
- unavailable candidateを選択してもnetwork / load / fallbackがないこと
- `active_config_invalid`がavailable別modelへ自動変更されないこと
- panel revision不一致、未知model、Busy中のrequestがno-opになること
- workspace resetがselected / active / storage stateを保持すること
- model profile state、generation state、preset、fingerprintがselectionで変化しないこと

### 11.3 wxPython UI / controller

`tests/test_wx_ms24_whisper_model_ui.py`へ次を追加する。

- RightPaneにWhisper専用tabがあり、モデルプロファイルtabと名称・state・callbackが分離されていること
- 3モデルのdisplay name、用途、VRAM目安、速度目安、exact size、availabilityが正しく表示されること
- activeとselectedの表示が異なる状態を表現できること
- selected変更でB2 scanのfailure codeを失わず、選択だけが更新されること
- scan workerがpendingからsuccessへ遷移し、全件SHA256検証をUIスレッドで待たせないこと
- scan failureがselected / active identityを変更せず、stable failure code / detailを保持すること
- scan failureの通常UIがfailure codeから安全な通知を表示し、failure detailのraw例外文字列・絶対パスを表示しないこと
- 新しいjob開始後の旧generation、shutdown後のlate resultがno-opになること
- pending中に候補選択して`panel_revision`が変化しても、job IDとscan generationが一致するscan成功結果を受領すること
- workerがdaemonであり、blocked scan中のcloseがUIスレッドでjoinせず戻り、job失効後のlate callbackがno-opになること
- startup resolver / availability workerのテストがrepository既定の`models` rootやroot runtime user dataへ到達せず、注入したtemporary model rootだけを読み、root作成も行わないこと
- stale selection requestとBusy中requestがUI stateを変更しないこと
- startup projection、再起動相当のtemporary SettingsStore round trip、identity correction
- System / Light / Dark themeで新規controlとnoticeが追従すること
- B4/B5未接続のDownload / Apply操作がnetworkやanalysisへ到達しないこと
- profile / preset / diagnostics / workspace resetの既存GUI回帰

### 11.4 関連回帰

最低限、次を実行対象にする。

- `tests/test_settings_store.py`
- `tests/test_whisper_model_catalog.py`
- `tests/test_whisper_model_loader.py`
- `tests/test_whisper_model_store.py`
- `tests/test_wx_ms23_b5_model_profile_ui.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_whisper_timing.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms21_b7_analysis_rollback.py`

pytestはpass表示だけでなくprocess exit code `0`を合格条件とする。テストでは実ネットワーク、実モデル、root runtime user dataを使用しない。B3のstartup / availability workerテストはtemporaryな`whisper_models_dir`またはtemporary B2 store/rootを明示注入し、temporary SettingsStore pathだけを隔離証拠にしない。

### 11.5 手動GUI確認

B3はRightPane、startup projection、候補選択、theme、Busy表示を変更するため、実装後のユーザー手動GUI確認を必須gateとする。確認範囲は次に限定する。

- 起動時にWhisperモデルtabが表示され、モデルプロファイルtabと混同しないこと
- `small / medium / turbo`の候補選択と、active model表示が別であること
- 候補選択だけでdownload、network、解析、既存Previewの無効化が起きないこと
- 旧INI相当の設定欠落時にsmallが表示され、異常なactive pairではsilent fallbackしないこと
- 保存先とavailabilityが表示され、`verified`以外を適用済みと誤表示しないこと
- 解析中のlock、stale操作、theme切替、workspace reset後の設定保持
- 既存profile / preset / Info / Warning tabが壊れていないこと

実ネットワーク、実モデルdownload、実Whisper解析、VMD / WAVの実MMD確認はこの手動GUI確認に含めず、B4、B5、MS26で実施する。

## 12. 受け入れ条件

### 設定・state

- [x] 旧INIで新keyが欠落していても、selected / activeはsmallとして復元される。
- [x] selected candidateとactive model key / manifest identityが別々に保存・復元される。
- [x] active keyとmanifest identityの不一致はfail closedし、availableな別modelへsilent fallbackしない。
- [x] loaded identityとanalysis identityをactive identityから推測しない。
- [x] B2の`whisper_models_dir`をB3が再検証・上書きしない。
- [x] workspace resetでWhisper設定、selected / active、保存先を消さない。

### UI

- [x] `small / medium / turbo`をWhisper専用UIで選択できる。
- [x] active model、selected candidate、availability、保存先が別表示される。
- [x] exact size、VRAM目安、相対速度目安、推奨用途がmanifest由来で表示される。
- [x] 選択だけではnetwork、Whisper load、analysis invalidation、Preview rebuildが発生しない。
- [x] 起動直後は`availability_scan_status=pending`（表示は「確認中」）を投影し、全モデルartifactのSHA256検証完了までUIスレッドをブロックしない。
- [x] scan成功・失敗を`availability_scan_status`とfailure codeから生成した安全なユーザー向け通知で表示し、失敗時もselected / active identityを保持する。`availability_scan_failure_detail`は診断・handoff用に保持するが、通常UIへraw表示しない。
- [x] 明示設定された保存先の`StorageRootResolution`失敗時は、既定の`models`へfallbackせず、store構築・availability worker起動・root作成を行わず、B2の`failure_code` / `message`をB3のfailure code / detailへ投影する。
- [x] pending中のcandidate selectionだけでscan結果を破棄せず、Busy、stale request、shutdown時に状態破壊が起きない。
- [x] scan中のcloseはUIスレッドでworker完了を待たずに戻り、daemon workerのlate callbackはno-opになる。
- [x] System / Light / Dark themeと既存profile / preset UIが維持される。

### 後続Block境界

- [x] Download / Verify / Deleteの実処理、HTTP、worker、cancelはB4へ残っている。
- [x] Apply / Re-analyze、AnalysisWorker、pipeline、loaded / analysis identity更新はB5へ残っている。
- [x] diagnostics / report / rollback / memory errorはB6へ残っている。
- [x] B3からB2のatomic promote、B1のverified loader、B5のownership / cacheを迂回しない。
- [x] B3専用scan workerは`scan_all()`以外のnetwork、loader、model load、analysis、directory作成を呼ばず、既存AudioWorkerやB4 download workerを使用しない。

### 回帰・検証

- [x] B3専用settings / UiState / wx testsがprocess exit code 0で通る。
- [x] MS23 profile、Latin profile、preset、diagnostics、fingerprint、voice-only、workspace reset回帰がprocess exit code 0で通る。
- [x] `compileall src tests`と`git diff --check`がprocess exit code 0で通る。
- [x] availability worker / startup scan testはtemporaryな`whisper_models_dir`またはtemporary B2 store/rootだけを使い、repository既定の`models` rootとroot runtime user dataを読まないことを確認する。
- [x] 保存先解決失敗、scan failure、モデルartifact failureを区別して表示し、設定保存失敗とavailability failureを混同しない。
- [x] ユーザー手動GUI確認の範囲と未実施のnetwork / model / actual-MMD確認を別々に記録する。

### 実装開始ゲート

- [x] B3実装前にIndex、Block Breakdown、MS24-B2 plan、RoadmapのB2実装済み状態とB3 plan索引を同期し、fresh pre-implementation checkを通過している。

## 13. リスクと対策

| ID | リスク | 重要度 | 対策 |
| --- | --- | --- | --- |
| MS24-B3-R1 | candidate選択だけでactiveや既存解析が変わる | P1候補 | selected / active / analysisを別fieldにし、selection-only no-op境界を直接testする |
| MS24-B3-R2 | active artifact不在時にavailableなsmallへsilent fallbackする | P1候補 | active identityを保持し、missing / invalidを表示して明示Applyを要求する |
| MS24-B3-R3 | active keyとmanifest identityの不一致を受理する | P2候補 | catalog identity照合、`active_config_invalid`、pair単位のsaveを固定する |
| MS24-B3-R4 | `loaded`や`analysis`をactive表示から推測する | P1候補 | loaded / analysis identityをB5 producer専用とし、B3はNone / 未接続を表示する |
| MS24-B3-R5 | SettingsStoreのpartial saveが既存Whisper設定を消す | P2候補 | old caller省略test、full / identity-only save優先度、既存値保持を固定する |
| MS24-B3-R6 | RightPaneのprofile UIとWhisper UIがstateや表示名を混同する | P2候補 | 専用panel DTO、専用callback、専用tab、既存profile回帰を固定する |
| MS24-B3-R7 | Busy中またはstale requestが候補状態を壊す | P2候補 | panel revision、Busy lock、shutdown guard、no-op testを追加する |
| MS24-B3-R8 | B3 UIがB4 downloadやB5 analysisを先行実装する | P2候補 | target file表、callback境界、no-network / no-loader test、Out of Scopeを固定する |
| MS24-B3-R9 | B2のmessageやraw例外・絶対パスを通常UIへ表示し、failure codeと診断detailの境界を壊す | P2候補 | `failure_code`から安全なユーザー向け通知を固定写像し、`availability_scan_failure_detail`は診断・handoff専用としてraw表示しない回帰を追加する |
| MS24-B3-R10 | 起動時scanや選択変更がdirectory作成・通信・Whisper loadを開始する | P1候補 | B2 scanのread-only利用、network seam 0回、loader seam 0回をtestする |
| MS24-B3-R11 | 計画上のB2状態と実装commitがrouting文書でずれる | P2候補 | B2実装状態をBlock Breakdown / Index / MS24-B2 plan / Roadmapへ同期し、IndexへB3 planを追加した後、fresh pre-implementation checkを通過するまでB3実装を開始しない |
| MS24-B3-R12 | artifact全体のSHA256 scanをstartup UI threadで同期実行し、起動が長時間停止する | P2候補 | 初期stateをpendingで即時表示し、B3専用read-only worker、job ID / availability scan generation / shutdown guard、late result破棄を固定する |
| MS24-B3-R13 | 候補選択が共有`panel_revision`を更新すると、実行中scanの正当な結果まで破棄される | P2候補 | scan専用`availability_scan_generation`を分離し、pending中の候補選択後にscan成功を受領する回帰testを追加する |
| MS24-B3-R14 | close時にworker完了待ちをすると、巨大artifactのSHA256 scanでUI終了が遅延する | P2候補 | daemon worker、`request_exit()`でjob失効、UIスレッドjoinなし、blocked-scan close testを固定する |
| MS24-B3-R15 | 明示設定された不正な保存先が既定`models`へfallbackし、ユーザーが意図しないrootをscanする | P2候補 | `StorageRootResolution`失敗時はstore / worker / root作成を行わず、B2 failure code / detailをfailed stateへ投影し、relative / UNC / remote / device path回帰を固定する |

### 13.1 計画段階の判定

- P1: 現時点で確定したP1はない。R1、R2、R4、R10は実装時にP1へ発展し得るため、受け入れ条件とfail-closed testで防ぐ。
- P2: selected / activeの分離、canonical identity fieldの対応、B2/B3/B4/B5責務、SettingsStore partial save、stale / Busy、profile UI境界、routing同期、起動時全件scanのUIスレッド阻塞、共有revisionによるscan結果破棄、close時のworker待機、B3 testのrepository既定`models` root隔離不足、明示設定rootの解決失敗時のfallback防止、B2 `failure_code` / `message`の正本field対応、failure codeから安全なユーザー通知への写像、raw technical detailの通常UI非表示を補正した。scan generation分離、daemon/no-join、job失効、pending中選択回帰test、temporary model root injection test、invalid storage root fail-closed test、raw detail非表示回帰を追加済みで、補正後の再チェックと実装後確認を完了した。計画書内に残るP2はない。
- P3: failure codeと表示文言の分離を、`availability_scan_failure_code` / `availability_scan_failure_detail`という正本fieldと、failure code由来の安全なユーザー通知projectionへ固定し、関連回帰一覧へ`test_whisper_timing.py`と`test_ms19_b3_textless_pipeline.py`を追加した。manual GUIとactual-MMD境界、表示metadataのmanifest正本も維持し、今回の補正後に計画書内へ残るP3はない。

## 14. 実装時の注意

- コマンドは一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`で連結しない。
- 実装開始時にlive Git state、MS20 routing、MS24 Block Breakdown、B1 plan、B2 plan、B2実装、関連testを再確認する。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のroot runtime実体は読み取り・変更・削除・stageしない。テストにはtemporary SettingsStore pathに加えてtemporaryな`whisper_models_dir`またはtemporary B2 store/rootを明示注入する。
- B3のテストで`whisper_models_dir`が空文字のままB2の既定rootへ解決される経路を使わない。repository既定の`models` rootとroot runtime user dataへ到達しないことをassertする。
- 明示設定された`whisper_models_dir`の`StorageRootResolution`失敗時は既定rootへfallbackせず、store / worker / root作成を行わない。B2の`failure_code` / `message`をfailed stateのcode / detailへ投影し、failure codeから安全なユーザー通知を生成する。message/detailのraw内容は通常UIへ表示せず、selected / active identityを保持する。
- `whisper_models_dir`のpath validation、canonical path、availability、atomic promote、permit検証をB3で再実装しない。
- 起動時の全件availability scanを`load_startup_state()`で同期実行しない。初期stateを先に表示し、B3専用workerの結果だけをguard付きで反映する。
- B3専用workerはlocal-only `scan_all()`だけを担当し、daemonとして起動する。既存AudioWorker、B4 download worker、Whisper loader、network、analysisを使用しない。
- `request_exit()`で現在のscan jobを失効させ、UIスレッドからworkerへjoinしない。close後のcallbackは必ずno-opとする。
- scan結果のguardはjob ID、`availability_scan_generation`、shutdownを組み合わせ、candidate selection用の`panel_revision`を流用しない。
- failure stateは`availability_scan_failure_code` / `availability_scan_failure_detail`で保持し、failure codeから安全なユーザー通知を生成する。B2の`message`、OS例外、絶対パスなどのraw detailは通常UIへ表示せず、診断・handoff用に限定する。
- candidate selectionだけで`invalidate_analysis()`、Whisper load、network、download、fallbackを呼ばない。
- active identityの変更、loaded / analysis identityの更新、retained timingの再利用可否、model-aware rollbackはB5へ残す。
- `openai-whisper==20250625`、v20250625 alignment heads、word timestamp / segment fallback、Python 3.13 acceptance target、3.14.3補助環境の扱いを変更しない。
- MS23の固定モーフ、Latin profile、preset、diagnostics、fingerprint、VMD 30fps、MMD用WAV契約を変更しない。
- B3はGUI変更を含むため、実装後にユーザー手動GUI確認を実施する。ただし、実network、実model、実MMDの確認済みとは報告しない。
- 実装後は変更ファイル、設定key、state transition、failure code、Busy / stale guard、test process exit code、manual GUI範囲、未実施のB4/B5/MS26項目を報告する。

## 15. 実装・検証記録

- 2026-08-23にMS24-B3を実装した。`SettingsStore`のselected / active identity、`UiState`のWhisper selection state、RightPane専用Whisperモデルtab、MainFrame / AppControllerのstartup projection・selection guard・coalesced save、local-only availability scan workerを追加した。候補選択だけではactive / loaded / analysis identity、既存解析、Preview、network、Whisper loadを変更しない。
- 自動検証は、B3 settings / state / wxの追加・関連テスト、MS23 profile / preset / diagnostics / fingerprint / voice-only / workspace reset回帰、full suiteを実行した。B3追加・関連の限定検証は `19 passed`、wx専用検証は `4 passed`、関連回帰は `131 passed, 2 skipped`、GUI関連フォローアップは `32 passed`、full suiteは `846 passed, 2 skipped`（process exit code `0`）だった。`compileall src tests`と`git diff --check`もprocess exit code `0`だった。
- ユーザーから、B3計画で指定した起動時Whisperモデルtab、small / medium / turbo表示、selected / active分離、候補選択のno-op、availability、theme、Busy / stale、workspace reset、既存profile / preset / Info / Warning、scan中closeを含む手動GUI確認が完了し、問題なしとの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。
- 実ネットワーク、実モデルdownload、実Whisper解析、実MMDでのVMD / WAV読み込み・リップ同期確認は実施していない。これらはB4、B5、MS26の責務として維持する。
- B3のproduction code / test code / GUIは`a27a26f Implement MS24-B3 model selection UI`へコミット済みである。B3計画書の当時の実装記録は保持し、現在の次工程は作成済みMS24-B4 Implementation Planのfresh read-only pre-implementation checkとする。B4実装、stage / commit / push / merge / tag / releaseは未実施である。
