# Implementation plan

## 1. 文書情報

- 文書名: MS24-B4 Implementation Plan
- 対象マイルストーン: MS24-B4
- 状態: implemented（実装済み・自動検証済み・ユーザー手動GUI確認済み、未コミット）
- 作成日: 2026-08-23
- 実装確認日: 2026-08-24
- 依存ブロック: MS24-B1、MS24-B2、MS24-B3
- 後続ブロック: MS24-B5（Apply / Re-analyze / loader propagation / single-active ownership）
- 正本となる関連文書: `docs/Implementation_Plan/MS24_Block_Breakdown.md`
- 実装時の前提ブランチ: `feature/MS23-implementation`

実装結果:

- `src/core/whisper_model_downloader.py`、`src/gui_wx/model_download_worker.py`、B4対象のController / MainFrame / RightPane / UiState / SettingsStoreを実装した。
- B4専用・関連テスト、MS23回帰を含む全pytestは`860 passed, 2 skipped, 77 subtests passed`、process exit code `0`だった。`compileall src tests`と`git diff --check`も成功した。
- 2026-08-24、ユーザーから提示したMS24-B4手動GUI確認項目の通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- Python 3.13.x互換性確認、B5 ownership provider接続後の実production Delete、実MMD確認、MS27 package / release readinessは未完了・別工程である。

この文書は、非エンジニアユーザーがWhisperモデルを安全に取得・中断・削除できるようにするMS24-B4の実装手順を定義する。ここでいう安全性は、ユーザーの明示確認なしに通信・設定変更・解析変更を開始しないこと、不完全または未検証の重みを利用可能状態へ昇格させないこと、Whisperのloader ownershipを無視して削除しないことを含む。

## 2. 背景

MS24-B1で、`small`、`medium`、`turbo`のversioned manifest、`openai-whisper==20250625`とのversion gate、公式URL、filename、exact size、SHA256、v20250625 alignment headsおよびnetwork-unreachableなverified-local loader境界を固定した。MS24-B2では、ローカル保存先のlocal-only解決、availability検査、canonical final path、canonical `.part`、preflight、exact size / SHA256検証、atomic promote、B5発行permitによるdelete primitiveを実装済みである。MS24-B3では、`selected`と`active`を分離したWhisperモデル管理UI、local-only availability scan、`management_busy`、job/generationによるlate result破棄の境界を実装済みである。

実装前のB3 UIはモデル候補を選択して保存するところまでを担当し、Download、Delete、Apply、Re-analyzeは未接続だった。B4では、候補選択だけでは動かず、ユーザーがDownload操作を開始して確認ダイアログを承認した場合だけforegroundで取得する責務を追加した。B4は解析を開始せず、active model・既存解析・loaded ownershipを変更しない。Apply、解析へのmodel identity伝播、single-active cache、明示unload、ownership permitの発行はB5へ残す。

現在のB2契約では、partial downloadのresume、HTTP Range、複数同時downloadは対象外である。ユーザー承認済みの方針として、キャンセル・通信失敗・検証失敗・ユーザーによる終了時はcanonical `.part`をbest-effortでcleanupし、retryは最初から開始する。

## 3. 目的

1. 明示的なDownload操作と確認承認を、ネットワーク通信を開始できる唯一の入口として固定する。
2. 大容量モデルの取得を専用workerで実行し、wx UIスレッドをブロックしない。
3. B2が所有する保存先検査、canonical `.part`、free-space preflight、exact size、SHA256、atomic promotionを必ず通過させる。
4. キャンセル、通信失敗、short read、overrun、timeout、SHA256不一致、size不一致、stale callback、終了中callbackを安全に扱う。
5. B5のactive model / loader ownership契約を侵食せず、B5のopaque `OwnershipReleasePermit`がある場合だけモデル削除をB2へ委譲する。
6. DownloadまたはDeleteの完了後に、selected / active / availability / Info表示を整合した単一projectionへ戻し、候補選択だけでactiveや解析を変更しない。

## 4. In Scope

### 4.1 Download orchestration

- `small`、`medium`、`turbo`をmanifestのmodel keyで解決するforeground download。
- Downloadボタンの明示操作、確認ダイアログの承認、承認後のB2 preflight、取得開始の順序制御。
- 公式manifestに固定されたHTTPS URLだけを使用するHTTP adapter。
- official host、path prefix、manifest filename、manifest SHA256、manifest exact sizeの再検証。
- Content-Lengthの取得・検証、chunk progress、timeout、通信例外、short read、overrunのfail-closed処理。
- B2のcanonical `.part`へのstreaming write、閉じたstaging fileのB2検証、verified checkpointへのatomic promote。
- キャンセル、失敗、ユーザーによるアプリ終了時のcanonical `.part` cleanup。cleanup失敗は記録するが、partialをavailableとは扱わない。
- retryは最初から行い、HTTP Range、resume、複数同時downloadは実装しない。

### 4.2 Dedicated worker and lifecycle

- 既存`AudioWorker`とは別のWhisper model download worker。
- 1回につき1つのdownload/delete management operationだけを許可する。
- progress、phase、success、cancel、failureをUIへ戻すcallback境界。
- job ID、model key、controller shutdown guardによるstale / late callback破棄。
- UI close時のcancel要求とjob失効。UIスレッドからworkerをjoinしない。
- workerがcleanupを完了して結果を通知する順序。異常終了などcleanupできない場合も、next scanでpartialをavailableにしない。

### 4.3 Delete orchestration

- Download済みモデルを対象にした明示削除操作と確認ダイアログ。
- active worker、loaded ownership、active/analysis identityをB5のownership providerへ確認する境界。
- B5が発行したopaque・model-bound・manifest-bound・request-scoped単回`OwnershipReleasePermit`だけをB2の`delete_model()`へ渡す。
- permit issuerが未接続、permitがない、対象が不一致、permitが拒否された場合のfail-closed拒否。
- 削除成功後のcontroller再利用可能`start_whisper_availability_rescan()`とselected / active / Info / availabilityの再projection。

### 4.4 UI and state integration

- 既存WhisperモデルtabへのDownload & Verify、Cancel、Delete、進捗、状態、失敗理由、retry導線。
- 既存設定画面がStubである現状を前提に、Whisper tabから明示的にローカル保存先を選択する操作。`wx.DirDialog`等で選択したpathをB2の`resolve_whisper_models_dir()`で検証し、validなlocal-only pathだけを設定へ保存する。
- 保存先変更のconfirm/cancel、無効pathの拒否、変更後のlocal-only availability rescanを実装する。保存先変更だけではnetwork、download、Whisper load、Apply、Re-analyze、active/analysis identity変更を開始しない。
- B3の`selected_model_key`、`active_model_key`、`active_manifest_identity`を維持し、download完了だけでactive・loaded・analysis identityを変更しない。
- `management_busy`と通常の音声解析Busyの分離を維持する。
- 確認拒否時に、network、file、settings、selected / active、analysis stateを変更しない。
- System / Light / Dark theme、既存Busy、close、stale callback、safe noticeの規約への適合。

### 4.5 Deterministic verification design

- 実ネットワークや実モデル重みを使わないfake HTTP source / responseによるunit test。
- B2 APIの呼び出し順、canonical path制約、progress、cancel、cleanup、promotion、delete guardのテスト。
- wx UIを手動確認するための確認項目の定義。実ネットワーク、実モデル解析、実MMDはこのBlockの自動検証対象にしない。

## 5. Out of Scope

- 起動時、モデル選択時、Info表示時、音声解析開始時、timer、background callback、silent retryによる通信。
- cloud ASR、音声外部送信、telemetry、background通信。
- 任意URL入力、manifestにないURL、任意host、任意filename、redirect。
- HTTP Range、partial resume、複数同時download、download queue、帯域制御。
- B2のlocal-only path policy、availability scan、canonical `.part`、preflight、SHA256 / exact size検証、atomic promote、delete primitiveの再実装または責務変更。
- B1のmanifest、version gate、公式URL、alignment heads、verified-local loader、network-unreachable adapterの変更。
- B5のApply、Re-analyze、`AnalysisWorker -> pipeline -> whisper_timing`へのmodel key伝播。
- B5のsingle-active cache、loaded model ownership、明示unload、device resource cleanup、`OwnershipReleasePermit` issuerの実装。
- active/analysis identity、Preview、diagnostics success、VMD saveabilityのB4側からの暗黙invalid化。必要なownership解除と解析結果invalid化はB5のprovider境界へ委譲する。
- Qt / PySide6の復活またはGUI基盤の変更。
- 新しいPython依存関係、`openai-whisper`のversion変更、`pyproject.toml` / `requirements.txt`の依存値変更。
- PyInstaller package、release、tag、push、merge、実配布用model重量の同梱。これらはMS27の範囲とする。
- 実MMDでのVMD / WAV読み込み、リップ同期、最終画質確認。MS26の範囲とする。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接編集。B4の保存先変更は、通常のアプリ実行時に既存`SettingsStore`を介してだけ行い、runtime fileを直接開いて編集・コピー・stageしない。

## 6. 前提条件

1. B1、B2、B3の実装と既存テストが基準状態にある。現行ブランチではB3実装コミット`a27a26f`を基準とし、Block Breakdown内のcommit待ち表記が残っている場合はlive Git状態を優先する。
2. `openai-whisper==20250625`を維持し、manifestのversion gateをdownload対象のidentity検証に使用する。
3. catalogは`WhisperModelSpec`から公式URL、filename、SHA256、exact sizeを解決し、B4がURLやfilenameをユーザー入力から受け取らない。
4. B2の`WhisperModelStore.preflight_download(model_key)`は、ユーザー確認完了後かつnetwork開始前に呼ぶ。空き容量取得不能または必要量未満の場合、workerを開始しない。
5. B2の`staging_path(model_key)`、`discard_staging(model_key)`、`promote_verified_staging(model_key)`だけでcanonical stagingを扱う。B4はfinal fileへ直接書かない。
6. `promote_verified_staging()`は閉じたcanonical `.part`をexact size / SHA256 / manifest identityで再検証し、成功時だけatomic replaceとB2内部の対象model post-promote verification scanを行う。B4側で検証済みと断定してavailableにしない。全体availabilityの更新はcontrollerの`start_whisper_availability_rescan()`へ委譲する。
7. B2の`delete_model(model_key, permit)`は、B5 issuerが発行したopaque `OwnershipReleasePermit`なしでは削除を拒否する。B4はpermitを生成しない。
8. B3のstateはselected / active / loaded / analysis identityとavailabilityを分離している。download成功はselectedまたはactiveを自動変更しない。
9. 現行Python 3.14.3は実測環境だが公式classifier外であるため、互換性確認の主対象はPython 3.13系列とする。Windows local path、wxPython、既存venvの実行条件を維持する。3.13.xの実行ファイルまたはvenvを明示し、実行ファイルのpath・`--version`・pytest終了コードを記録するまでB4のcompatibility gateを通過扱いにしない。
10. B4の通常UIメッセージにはraw exception、絶対path、secret、内部permit情報を表示しない。stable failure codeをユーザー向け文言へ写像し、詳細はdiagnostic / handoff用に保持する。

## 7. 対象ファイル

### 7.1 新規作成候補

| 区分 | ファイル | 責務 |
|---|---|---|
| 新規 | `src/core/whisper_model_downloader.py` | 公式manifest由来のURLに限定したHTTP streaming、header/redirect/timeout/Content-Length検証、chunk progress、cancel通知、B2 staging APIとの接続。wx依存を持たない |
| 新規 | `src/gui_wx/model_download_worker.py` | dedicated daemon worker、download/delete operationのlifecycle、cancel event、job-bound callback、UI callbackのdispatch |
| 新規 | `tests/test_whisper_model_downloader.py` | fake HTTP sourceを使うcore downloaderのheader、stream、cancel、failure、progress、redirect、no-resume回帰 |
| 新規 | `tests/test_ms24_model_download_worker.py` | workerのjob identity、duplicate start、cancel、close、late callback、B2 API呼び出し順、delete seam |

### 7.2 変更候補

| 区分 | ファイル | 変更責務 |
|---|---|---|
| 変更 | `src/gui_wx/ui_state.py` | download / delete managementのoperation、status、job ID、model key、received bytes、expected bytes、failure code/detail、cleanup状態をartifact availabilityとは別軸で保持 |
| 変更 | `src/gui_wx/right_pane.py` | Download & Verify、Cancel、Delete、progress/status、confirm前の説明、retry導線、Busy/management lock、theme反映。B3のselected / active表示を保持 |
| 変更 | `src/gui_wx/app_controller.py` | 明示操作入口、確認承認後のpreflight、worker start/cancel、再利用可能な`start_whisper_availability_rescan()`、job/generation guard、state projection、B5 ownership providerへのdelete seam、保存先変更の検証・保存・store再構築、shutdown時のworker失効 |
| 変更 | `src/gui_wx/main_frame.py` | RightPane callback接続、wx確認ダイアログ、保存先DirDialog、管理操作と既存audio Busyの相互lock、progress/status同期、close時のcancel接続 |
| 変更 | `src/core/settings_store.py` | B4の保存先変更で使用するmanaged persistence境界を維持し、`system` / `light` / `dark` themeのround-tripを壊さない。partial saveだけでrootを変更するAPIは追加しない |
| 条件付き変更 | `src/gui_wx/worker_state.py` | 既存`AudioWorker`契約にWhisper download stateを混在させない。共有state追加が不可避な場合だけ、download専用型・enumを独立して追加し、AudioWorkerの意味を変更しない |
| 変更候補 | `tests/test_ms24_whisper_model_ui_state.py` | transfer / delete stateの不変条件、selected / active分離、confirm reject、管理Busy、failure recovery |
| 変更候補 | `tests/test_wx_ms24_whisper_model_ui.py` | RightPane/MainFrame/controllerのconfirm、progress、cancel、retry、delete guard、same-turn projection、theme/stale回帰 |
| 変更候補 | `tests/test_settings_store.py` | `system` / `light` / `dark`のtheme round-tripと、保存先rootだけを置換するmanaged mergeで他設定を保持する回帰 |

### 7.3 変更しないファイル・領域

- `src/core/whisper_model_store.py`: B2正本のAPIとownership permit契約は変更しない。B4実装は既存APIを呼び出すだけにする。
- `src/core/whisper_models.py`: versioned manifest、official URL、filename、exact size、SHA256、manifest identityは変更しない。
- `src/core/whisper_model_loader.py`、`src/core/whisper_timing.py`、`src/gui_wx/analysis_worker.py`: B5以降の解析伝播を先取りしない。
- `pyproject.toml`、`requirements.txt`、`MMD_AutoLipTool.spec`、`build.ps1`:依存・package境界を変更しない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`:直接編集・コピー・stageしない。B4の通常アプリ動作では、保存先変更のために`SettingsStore`が管理する読み込み・atomic保存だけを許可し、テストはtemporary settings pathを使用する。
- 既存のAudioWorker、MS23の固定モーフ・Latin profile・preset・diagnostics・fingerprint処理。

### 7.4 推測APIの扱い

本計画の`DownloadRequest`、`DownloadProgress`、`DownloadResult`、`WhisperModelManagementState`、`OwnershipReleaseProvider`等の名称は実装候補であり、現行コードに存在するAPIではない。実装時は、既存のB2 DTO、B3 `WhisperModelSelectionState`、RightPane callback、controllerの命名規約を確認して確定する。候補APIを理由にB2 public API、B3の既存state契約、AudioWorker契約を破壊しない。

HTTP transport factoryは、fake HTTPを使うunit testとGUI確認用harnessからだけ注入できるtest seamとして候補化する。通常のproduction起動では標準ライブラリtransportを固定し、ユーザー設定、runtime user data、任意URLからtransportを差し替えられるAPIを公開しない。

## 8. 実装方針

### 8.1 責務分離

責務は次の4層に分ける。

| 層 | 所有する責務 | 所有しない責務 |
|---|---|---|
| B2 `WhisperModelStore` | local-only path、canonical artifact、preflight、scan、exact size / SHA256、atomic promote、permit検証付きdelete | HTTP、wx、worker、確認ダイアログ、ownership issuer |
| B4 core downloader | manifest由来URLのHTTP stream、header/redirect/timeout、progress、cancel、B2 stagingへの書込み | UI、設定保存、active/analysis、permit発行 |
| B4 GUI worker/controller | foreground操作のlifecycle、job guard、confirm後開始、Busy、callback、retry、delete仲介 | Whisper load、Apply、Re-analyze、ownership解除の実体 |
| B4 RightPane/MainFrame | ユーザーへの確認、progress、safe error、操作可否、theme | network実行、file path解決、SHA256判定、permit生成 |

### 8.2 明示確認を通信の前置条件にする

1. RightPaneは候補選択とは別のDownload操作を発生させる。
2. MainFrameまたは既存UI callback境界で、対象modelのdisplay name、exact size、保存先、ネットワークを使用することを説明する。
3. ユーザーが拒否・閉じるを選択した場合はcontroller、store、worker、HTTP transportを呼ばず、state、settings、file、analysis identityを変更しない。
4. 承認後だけcontrollerが再度state、shutdown、`management_busy`、model key、manifestを検証し、B2 `preflight_download()`を呼ぶ。
5. preflight成功後だけworkerを開始する。確認済みでもpreflightが失敗した場合はnetworkを開始しない。

確認承認は、startup scan、候補選択、Info表示、解析開始、timer、background callbackから暗黙に生成しない。二重クリックや古いcallbackも新しい確認として扱わない。

### 8.3 Official URLとHTTP transport

- URLは`WhisperModelSpec.official_url`からだけ取得し、ユーザー入力、設定値、download履歴から受け取らない。
- B1のURL検証を再利用し、HTTPS、固定official host、固定path prefix、manifest path SHA、manifest filename、query/fragment/authなしを確認する。
- redirectは全面拒否する。HTTP clientの既定redirect追従を無効化し、3xx responseをstructured failureとして扱う。任意host・HTTP scheme・異なるpathへの到達を許可しない。
- 標準ライブラリのHTTP機能を優先し、`requests`などの新規依存は追加しない。
- connect/read timeoutはコード上の定数または注入可能な設定として明示し、無期限待機を許可しない。ユーザー設定へ新しい曖昧なtimeout項目を追加しない。

### 8.4 Content-Length、streaming、検証、promotion

1. response statusを検証し、HTTP errorをstructured failureへ変換する。
2. Content-Lengthが存在し、manifestの`size_bytes`と一致する場合だけwriteを開始する。欠落、非数値、負数、manifestとの不一致はnetwork bodyを保存せずfail closedとする。
3. B2 `preflight_download()`から得たcanonical `.part`以外へ書かない。final pathをopenして直接上書きしない。
4. chunkごとにcancelを確認し、受信バイト数をbounded progress callbackへ渡す。受信がContent-Lengthを超える場合はその場で失敗し、promoteしない。
5. EOF時に受信バイト数がexact sizeと一致しない場合はshort readとして失敗する。
6. responseを閉じ、staging fileをflush/closeした後、B2 `promote_verified_staging(model_key)`を呼ぶ。B4がSHA256結果だけでverifiedを宣言しない。
7. B2のpromote成功結果はmanagement resultへ保持する。availability全体の再投影はcontrollerが再利用可能な`start_whisper_availability_rescan()`を開始し、そのrescan完了callbackで行う。B2内部の対象model post-promote verification scanを全体projectionの入口にしない。失敗結果のstable failure codeは保持する。
8. SHA256不一致、size不一致、atomic replace失敗、cleanup失敗のいずれでも既存verified finalを破壊しない。新しい`.part`は`discard_staging()`でbest-effort cleanupする。

### 8.5 Cancel、failure、retry、終了

- cancel操作は現在のjob IDにだけ作用し、cancel eventをsetする。workerは次のchunk境界またはread timeout境界で停止する。
- cancel、HTTP failure、timeout、short read、overrun、preflight failure、promote failureは、`artifact_status`と別のtransfer failureとして保持する。
- cancel/failure後は必ずcanonical `.part` cleanupを試み、再試行は新しいjob IDで最初から行う。partial resume、Range header、古いjobのstaging再利用は行わない。
- cleanup失敗時はcleanup failureをdiagnostic detailへ保持し、partialをverified/availableにしない。次回scanでもpartialまたはcleanup failureとして表示する。
- retryはユーザーがRetry/Downloadを明示操作した場合だけ開始する。silent retryやtimer retryは行わない。
- `request_exit()`はdownload jobを失効させ、cancelを要求し、workerのlate callbackを受け付けない。UIスレッドからjoinしない。ユーザーが通常のcloseを行った場合、workerのfinallyでbest-effort cleanupを完了する。

### 8.6 DeleteとB5 ownership seam

- Deleteボタンは、対象がcatalog上のmodel keyで、現在のmanagement operationがidleである場合だけ有効にする。確認前にfile operationを開始しない。
- 確認承認後、controllerはB5へownership releaseを要求するprovider seamを呼ぶ。B5が未実装でproviderがない場合は、確認後でも`delete_blocked_ownership`として拒否する。
- providerは、対象modelがactive workerやloader ownershipから解放され、必要なactive/analysis invalidationをB5側で処理済みであることを確認した後にだけopaque permitを返す。B4はproviderやpermitを自作しない。
- permitを受け取ったB4は、model keyと現在のmanifest identityを保持したままB2 `delete_model()`へ渡す。B2が対象不一致・再利用・無効permitを拒否した場合は削除成功と表示しない。
- delete失敗時はselected、active、analysis、settingsを変更しない。
- delete成功時は、B2 `delete_model()`が返す対象modelの検証結果をmanagement resultへ保持する。availability全体、リスト、Info、選択projectionの更新はcontrollerだけが再利用可能な`start_whisper_availability_rescan()`を開始し、そのrescan完了callbackで同じprojection turnへまとめる。catalog上のselected keyは、別モデルへsilent fallbackせず、deleted/missingとして残して再取得導線を表示する。
- B4はactive identity、loaded identity、analysis identity、Preview、diagnostics、VMD saveabilityを直接clearしない。permit発行前に必要な変更はB5のownership providerへ委譲する。

### 8.7 保存先変更

- 保存先変更はWhisper tabの明示操作からだけ開始し、通常の候補選択、startup scan、Info、解析、timerから開始しない。
- MainFrameは`wx.DirDialog`等でユーザーが選択したpathを受け取り、controllerが`resolve_whisper_models_dir()`でlocal-only、absolute、非UNC、非reparse、許可driveを検証する。検証失敗時は設定、store、state、root作成を変更しない。
- validなpathはユーザーの最終確認後に、現在の全設定スナップショットへ`whisper_models_dir`だけを反映する安全なmerge保存で永続化し、controllerの`WhisperModelStore`を新rootへ再構築する。保存先だけを渡す部分保存でtheme、window、recent path等を既定値へ戻さない。既定rootへのsilent fallbackは行わない。
- 保存先変更後はB3と同じlocal-only availability scan workerで新rootを再scanする。scanはUI threadで実行せず、結果はjob ID、scan generation、shutdown guardを通してprojectionする。
- 保存先変更はdownload、network、Whisper load、Apply、Re-analyze、active/analysis identityの変更を開始しない。既存のactive pairが新rootでmissingになっても、別modelへsilent fallbackせずB5の解析可否判定へ引き継ぐ。
- Download/delete management中、音声解析Busy中、shutdown中は保存先変更を無効化する。cancelしたDirDialogは完全なno-opとする。

### 8.8 Management workerとUI projection

- `src/gui_wx/model_download_worker.py`は名称にかかわらず、B4のdownload/delete management workerとして、download、B5 ownership provider呼出し、B2 deleteをUI thread外で実行する。完了後のavailability rescanはcontrollerの再利用可能な`start_whisper_availability_rescan()`へ委譲する。
- B5 ownership providerはworkerから呼び出せるwx非依存・worker-safeな境界とし、provider内部のunload / invalidationがUI操作を直接行わない契約をB5へ引き渡す。
- B2 `delete_model()`とdownload/delete worker処理をcontrollerまたはMainFrameの同期callbackから直接呼ばない。workerのterminal resultを受けたcontrollerだけが`start_whisper_availability_rescan()`を開始し、scan結果をUIへprojectionする。B2のpromote/delete内部で行う対象model単体の検証scanを、全体availability projection用のrescan入口として流用しない。
- workerのcancel、job invalidation、cleanupが完了するまで同一canonical `.part`を使う新しいretryを開始しない。old workerとnew workerが同時に同じmodel keyを扱わない。
- UI threadではconfirm、DirDialog、button state、progress/status projectionだけを行う。

### 8.9 UI projectionとBusy

- B3の`WhisperModelSelectionState`に管理操作の状態を追加する場合は、artifact availability、transfer、ownershipを別軸に保つ。
- 最低限、operation（idle/download/delete）、phase（preflight/downloading/verifying/cancelling/blocked/finished）、job ID、model key、received bytes、expected bytes、failure code/detail、cleanup statusを保持する候補stateを定義する。
- `management_busy=True`の間は候補選択、保存先変更、Download、Delete、B5へ接続されるApplyを適切にlockする。通常音声解析の`busy`とは別に表示し、どちらか一方の結果で他方のstateを消さない。
- 進捗はmanifestのexact sizeを分母とし、未知のContent-Lengthを100%として表示しない。
- successは「取得・検証済み」と表示するが、「active」「適用済み」「再解析済み」とは表示しない。cancel/failureは原因とRetry方法を安全な文言で表示する。
- UI callbackはjob ID、model key、shutdown、現在のmanagement operationを検証し、不一致ならno-opにする。old jobが新しいdownloadやdeleteの表示を上書きしない。

## 9. 詳細ステップ

### Step 1: B2/B3境界と状態軸を固定する

- `WhisperModelStore`のpublic APIを現行のまま使用することを確認する。
- B3の`WhisperModelSelectionState`、RightPaneの`WhisperModelPanelState`、`management_busy`、`panel_revision`、availability scan generationを確認する。
- artifact status、transfer status、ownership/delete statusを一つのenumへ混在させない。
- download job IDとscan job/generation、selection panel revisionを別々のguardとして定義する。
- B3の起動時one-shot `start_whisper_availability_scan()`はwrapperとして残し、再利用可能な`start_whisper_availability_rescan()`をcontrollerの共通入口として定義する。startup-only guardをrescanへ流用しない。
- `selected`、`active`、`loaded`、`analysis` identityをB4処理から変更しない不変条件をtest先行で書く。

### Step 2: Core downloaderとofficial transportを追加する

- manifestから解決した`WhisperModelSpec`だけを入力とするcore downloaderを追加する。
- stdlib HTTP responseをfake可能なtransport boundaryへ抽象化する。production pathがfakeを必要としない構成にする。
- status、redirect、HTTPS/host/path、Content-Length、timeout、read error、short read、overrun、cancelをstructured resultへ写像する。
- preflight後にだけcanonical `.part`へwriteする。任意path、任意filename、caller-supplied final pathを受け取らない。
- write完了後にB2 `promote_verified_staging()`を呼び、その結果を返す。B4 core downloaderでB2のSHA256ロジックを複製しない。

### Step 3: Dedicated model download workerを追加する

- `AudioWorker`と異なるworker class、cancel event、operation stateを追加する。
- worker開始時にcaptureしたjob ID、model key、manifest identityを全callbackへ束縛する。
- progressはUI callbackへ渡し、完了・cancel・failureは一度だけ返す。
- `finally`でcanonical `.part` cleanupを行い、cleanup結果をtransfer resultへ含める。
- UI close時のcancel、daemon lifecycle、joinしないshutdown、late callback破棄を実装する。
- 二重download、download中のdelete、delete中のdownload、新しいjob開始時の旧jobcallbackを拒否する。

### Step 4: Controllerの明示操作入口を追加する

- RightPaneから受けたDownload/Delete requestについて、`is_busy`、`management_busy`、shutdown、model key、panel revision、availability、active/ownership条件を検証する。
- Download requestは確認承認の結果を受け取った場合だけB2 preflightを呼ぶ。確認拒否ではstore、worker、HTTPへ到達しない。
- preflight failureはworkerを起動せず、free-space/write-probe failure codeをsafe noticeへ写像する。
- workerのprogress/resultをstateへ投影し、success後は`start_whisper_availability_rescan()`を呼ぶ。download successでApply/Re-analyzeを開始しない。
- B5 ownership providerを注入可能な境界として定義し、provider未接続時はdelete blockedにする。
- delete success後だけcontrollerが`start_whisper_availability_rescan()`を呼び、rescan完了後にpanel projectionを行う。B2 `delete_model()`の戻り値に含まれる対象model単体scanは、controllerの全体rescanの代替にしない。
- `request_exit()`でdownload/delete jobを失効させ、cancelとlate callback guardを実行する。既存audio close契約を変更しない。

### Step 4a: 保存先変更の明示操作を追加する

- RightPaneから保存先変更requestを発生させ、MainFrameでDirDialogを表示する。候補選択やstartup scanから同じrequestを暗黙生成しない。
- controllerは選択pathをB2 `resolve_whisper_models_dir()`で検証し、invalid path、UNC、network、reparse、許可されないdriveを拒否する。
- valid pathだけを、現在の全設定を読み取って`whisper_models_dir`だけを置換する安全なmerge保存で既存設定へ保存する。`SettingsStore.save({"whisper_models_dir": ...})`だけを渡す実装は禁止し、theme、window、recent path、selected / active identity等の既存値を保持する。
- managed mergeでは、現行`SettingsStore`の全supported keyを正規化済みsnapshotとして保持し、`theme`の`system` / `light` / `dark`を別の値へ暗黙変換しない。保存先root以外の値を既定値へ戻さず、変更対象は`whisper_models_dir`だけに限定する。
- 設定保存成功後だけnew rootに束縛した`WhisperModelStore`を構築して`start_whisper_availability_rescan()`を開始する。保存失敗時はold root、store、state、settingsを変更しない。
- scan完了前は「確認中」と表示し、old rootのavailabilityをnew rootの結果として表示しない。scan失敗時もselected / active identityを保持し、既定rootへfallbackしない。
- 保存先変更のcancel、validation failure、save failureでは、settings、store、selected / active / loaded / analysis identity、既存解析を保持する。保存成功時もtheme、window、recent path、selected / active identity等の保存先以外の設定を保持する。

`start_whisper_availability_rescan()`の契約:

- `view`、shutdown、current `WhisperModelStore`を確認し、開始不能時は`False`を返す。
- `_whisper_scan_job_id`と`_whisper_scan_generation`を単調増加させ、実行中の旧worker結果を失効させる。旧workerはUI threadからjoinしない。
- `availability_scan_status=pending`、current store、new job ID、new generationをstateへ投影し、既存の`WhisperAvailabilityWorker`を新しいjobとして起動する。
- `_whisper_scan_started`のstartup-only guardを参照せず、起動時scan後も保存先変更・Download成功・Delete成功ごとに再利用できる。
- result callbackはjob ID、generation、state、shutdownを検証し、不一致・終了後のresultをno-opにする。

### Step 5: RightPane/MainFrame UIを追加する

- 既存Whisper tabの候補選択・active表示・保存先・availability表示を維持する。
- Download & Verify、Cancel、Delete、progress gauge、phase/status、safe notice、Retry導線を追加する。
- Download/Delete開始前に確認ダイアログを表示し、対象display name、exact size、保存先、通信を行うこと、キャンセル時は再取得が必要なことを明示する。
- confirm reject/closeはcontrollerへstart requestを送らない。承認後もcontroller側でstateとpreflightを再検証する。
- management Busy中は対象外操作を無効化し、音声解析Busy中の管理操作も既存規約に従ってlockする。
- old callback、close後callback、別model callbackで表示が変わらないことをjob guardで確認する。
- theme refresh、wrap、layout、既存profile/preset/Info/Warningの表示を壊さない。

### Step 6: Delete provider seamをB5へ引き継ぐ

- B4側にpermit constructorやtest-only issuerをproduction callerとして持ち込まない。
- B5が「対象modelのsingle-active ownershipを解除し、必要なanalysis identity invalidationを完了した後、単回permitを返す」provider contractを文書化する。
- B4はprovider未接続・拒否・例外をdelete blockedとして処理し、filesystem削除を試みない。
- B5実装時にproviderを接続できるよう、request-scoped callback/protocolの型境界を候補として提示する。

### Step 7: Testsを追加する

- fake HTTP sourceで、実URLへ到達せずに全transfer分岐を検証する。
- B2 storeは既存のfake catalog / temporary root注入を使用し、実ユーザーrootやruntime dataを使わない。
- controller/UI state testsでconfirm reject、management Busy、stale callback、rescan projection、delete provider seamを検証する。
- B1/B2/B3の既存テストとMS23の固定モーフ・profile・preset・diagnostics・fingerprint回帰を変更なしで実行できるようにする。

## 10. 状態遷移 / データ契約

### 10.1 Download lifecycle

```text
idle
  └─[ユーザーがDownloadを押す]
      └─[確認拒否/close]─> idle
      └─[確認承認]
          └─[state/revision/shutdown検証]
              └─[preflight]
                  ├─[root/write/free-space不備]─> failed(preflight)
                  └─[成功]─> downloading
                      ├─[cancel / close]─> cancelling
                      │                    └─[cleanup]─> cancelled
                      ├─[HTTP/timeout/short read/overrun]─> failed(network/stream)
                      │                                      └─[cleanup]
                      ├─[Content-Length不備]─> failed(header)
                      └─[EOF]
                          └─[B2 promote]
                              ├─[size/SHA/path/replace failure]─> failed(verify/promote)
                              │                                  └─[cleanup]
                              └─[success]─> succeeded
                                  └─[local-only rescan/projection]─> idle
```

### 10.2 Delete lifecycle

```text
idle
  └─[ユーザーがDeleteを押す]
      └─[確認拒否/close]─> idle
      └─[確認承認]
          └─[state/model/active/management guard]
              ├─[busy / active worker / providerなし]─> blocked
              └─[B5 ownership provider]
                  ├─[permitなし/拒否]─> blocked
                  └─[opaque permit]
                      └─[B2 delete_model]
                          ├─[failure]─> failed(delete)
                          └─[success]
                              └─[local-only rescan/projection]─> idle
```

### 10.3 Storage root change lifecycle

```text
idle
  └─[ユーザーが保存先変更を押す]
      ├─[DirDialog cancel]─> idle（完全なno-op）
      └─[path選択]
          └─[B2 resolve_whisper_models_dir]
              ├─[invalid/local-only違反]─> failed（old root/state保持）
              └─[valid]
                  └─[ユーザー確認・settings保存]
                      ├─[cancel/save failure]─> failed（old root/state保持）
                      └─[new store + local scan]
                          ├─[scan failure]─> failed（selected/active保持）
                          └─[scan success]─> idle（new root projection）
```

保存先変更はnetwork、download、load、Apply、Re-analyzeを発生させない。selected keyはcatalog上の候補として保持し、active pairは別modelへfallbackしない。

### 10.4 Data contract

| 軸 | 代表状態/field | 契約 |
|---|---|---|
| artifact | `missing` / `partial` / `verified` / invalid系 | B2 `ModelAvailability`が正本。transfer stateをartifact statusへ上書きしない |
| operation | `idle` / `download` / `delete` | 同時に1つだけ。downloadとdeleteを同時実行しない |
| transfer phase | `preflight` / `downloading` / `cancelling` / `verifying` / finished | job IDとmodel keyへ束縛する。UI表示用でありartifact statusではない |
| progress | `received_bytes` / `expected_bytes` | expectedはmanifest exact sizeと一致するContent-Lengthだけ。unknownを成功扱いにしない |
| transfer failure | stable failure code + diagnostic detail | cancel、network、timeout、header、short read、overrun、cleanup、promoteを区別する |
| identity | selected / active / loaded / analysis | B4のdownload/delete成功では暗黙変更しない。B5 producerのみがloaded/analysisを更新する |
| job guard | download job ID + model key + shutdown | 不一致または終了後callbackはno-op。scan generation/panel revisionと混用しない |
| delete capability | B5 opaque `OwnershipReleasePermit` | B4は発行しない。B2がmodel/manifest/artifact/single-useを検証する |
| settings | selected / active identity、storage root | confirm reject、download、cancel、delete failureでは変更しない。download successでもactiveを保存しない |

### 10.5 Invariant

- 確認拒否ではnetwork、preflight、worker、file、settings、analysisに副作用がない。
- `.part`はcanonical pathだけであり、存在してもverified availableではない。
- finalはB2 promote成功前に作成・置換しない。existing verified finalは失敗時に保持する。
- cancel/failure/retry/closeは旧jobの結果を新jobやUIへ反映しない。
- download successは「verified local artifact」だけを示し、active/apply/analysis successを示さない。
- delete successはpermit発行・検証とB2 delete成功の両方が必要であり、B4単独では起こせない。
- delete成功後のselected keyはsilent fallbackせず、catalog上のcandidateとして残し、missing/download必要状態を表示できる。
- MS23の固定morph、Latin profile、preset、diagnostics、fingerprintのstate・保存・failure guardを変更しない。

### 10.6 B4単独とB5連携後の受け入れ境界

| 段階 | B4で確認する契約 | B5連携後に確認する契約 |
|---|---|---|
| Delete provider | provider未接続、permitなし、対象不一致、permit拒否ではfilesystemへ到達せずblockedになる | B5がownership解除・必要なanalysis invalidation後に対象一致の単回permitを発行できる |
| Delete success | test-only fake providerがB2のtest-only issuer境界から得たopaque permitを返す場合、management worker内でB2 deleteを完了し、controllerの`start_whisper_availability_rescan()`後にprojectionできる | 実B5 provider接続後、active worker / loader ownership解除を含む実Deleteを確認する |
| UI manual gate | B5未接続時の安全なblocked表示、confirm reject、download progress/cancel/failure/retry、保存先変更を確認する | B5実装後にpermit発行からDelete成功・再projectionまで確認する |

B4のproduction codeはpermitを生成しない。B4のDelete success testは、公開fieldから作った擬似permitではなく、B2が提供するtest-only issuerをB5 provider test doubleの内部で使用する。

## 11. テスト方針

### 11.1 Core downloader unit tests

fake HTTP response / transportを注入し、実ネットワークへ接続しない。

- manifest由来のofficial HTTPS URLだけを受理する。
- host、scheme、path prefix、filename、SHA path、query/fragment/auth不備を拒否する。
- redirectを全面拒否し、3xx responseでnetwork body保存・promoteへ進まないことを検証する。
- status error、timeout、read exception、Content-Length欠落、非数値、size不一致を検証する。
- exact sizeの正常stream、short read、overrunを検証する。
- chunk progressが0からexact sizeまで単調に進み、Content-Lengthを超えないことを検証する。
- cancel eventが検出された場合、promoteを呼ばず、canonical `.part` cleanupへ進むことを検証する。
- HTTP Range / resume headerを送らず、既存partialを再利用せず最初から書くことを検証する。
- B2 `promote_verified_staging(model_key)`の結果をsuccess/failureへ正しく写像する。
- SHA256不一致、size不一致、atomic replace失敗でexisting verified finalが保持されることを検証する。
- cleanup成功・missing idempotent・cleanup failureを区別し、partialをavailableにしないことを検証する。

### 11.2 Worker/controller tests

- confirm rejectではHTTP transport、B2 preflight、worker startが呼ばれず、state/settings/fileが不変である。
- confirm accept後にだけpreflightが先行し、preflight failure時はHTTPへ進まない。
- 1つのdownload中に二重start、別model start、delete startを拒否する。
- progress、verifying、success、cancel、failureのstate projectionを検証する。
- cancel後にpartialをload/availability successとして扱わない。
- download failure後、restartなしでretry、storage root変更、既存モデル選択へ復帰できる。
- validな保存先変更が、保存先以外のtheme、window、recent path、selected / active identityを保持する安全なmergeで既存設定へ保存され、新rootのstoreとlocal-only scanへ切り替わる。保存先だけを渡すpartial saveによる既定値化を回帰で検出する。cancel、invalid path、save failureではold root/stateを保持する。
- `SettingsStore`の`system` / `light` / `dark` theme round-tripと、保存先rootだけを変更したmanaged mergeの非対象設定保持を検証する。
- stale job ID、別model key、shutdown後、旧scan generation、古いpanel revisionのcallbackをno-opにする。
- `request_exit()`がjobを失効させ、cancelを要求し、late callbackで破棄済みviewを参照しない。
- download successでselected / active / loaded / analysis identity、settings、既存解析が変化しない。

### 11.3 Delete tests

- confirm rejectではB5 providerとB2 deleteを呼ばない。
- management Busy、active worker使用中、provider未接続、permitなし、対象不一致、permit拒否、permit再利用を削除拒否にする。
- B5 providerから対象一致のopaque permitを受けた場合だけB2 `delete_model()`へ渡す。
- B2 delete failure時にsettings、selected、active、analysisを変更しない。
- delete success後にlocal-only rescanを行い、availability/list/Info/selectionが同一projectionで更新される。
- selected deleted modelを別modelへsilent fallbackせず、missing/download必要として表示する。
- B4側がpermitを生成できないことを、公開fieldからのfield-shaped objectを拒否するB2契約と合わせて検証する。
- B4 standaloneではtest-only provider doubleを使用してDelete success seamを検証し、productionのB5 issuer未接続時は必ずblockedになる。
- provider呼出しとB2 deleteはmanagement worker内で実行され、post-delete scanは`start_whisper_availability_rescan()`が起動するavailability worker内で実行される。UI threadはブロックしない。

### 11.4 GUI手動確認項目

実ネットワーク・実モデルを使わず、test harnessからcontroller/worker構築時にfake HTTP transport factoryを注入して確認する。production起動からtransportを差し替えられるようにはしない。通常の手動GUI確認では実通信を発生させない。

- Whisper tabでDownload操作を押し、確認ダイアログを拒否・閉じた場合に、ファイル、保存設定、active、既存解析が変わらない。
- 確認承認後に、UIが固まらず、対象名・exact size・進捗・状態が表示される。
- Cancel操作でcancel中・cancel済みが表示され、partialがverified/availableと表示されない。
- failure時に安全な原因とRetry導線が表示され、再起動なしで再試行可能である。
- management Busy中に候補選択、Download、Delete、保存先変更などの競合操作が適切にlockされる。
- 保存先変更でDirDialogをcancelした場合、またはinvalid/network/reparse pathを選んだ場合、settings、store、active/analysis、既存解析が変化しない。
- validな保存先変更後、再起動なしに新rootのlocal-only availability scanが走り、selected / active identityを維持したまま表示が更新される。
- Delete確認の拒否、B5未接続時のownership guardによるblocked表示、test-only provider seam経由のlist/availability/Info/selection再投影を確認する。実B5 providerによるproduction Delete成功はB5連携後の確認項目とする。
- System / Light / Dark theme、既存profile/preset/Info/Warning、音声解析Busy、close中のlate callback表示が壊れない。

### 11.5 実行範囲外の確認

- 実ネットワークからのWhisper重量取得、実モデルload、実Whisper解析はB4の自動テストに含めない。
- 実MMDでのVMD / WAV読み込み、リップ同期はMS26に延期する。
- PyInstaller package / release readinessはMS27に延期する。
- ただし、計画実装後は既存B1/B2/B3 tests、MS23回帰、Python 3.13.xの対象test群を実行し、実行ファイルpath、`--version`、各コマンドの終了コードと未実施範囲を報告する。3.13.x環境が得られない場合は互換性未検証としてB4 closeoutを完了扱いにしない。

## 12. 受け入れ条件

### 12.1 Network and confirmation

- [x] networkはユーザーがDownloadを明示操作し、確認ダイアログを承認したforeground operationからだけ到達する。
- [x] startup、selection、Info、analysis、timer、silent retry、background callbackからnetworkへ到達しない。
- [x] confirm reject/closeではnetwork、preflight、worker、file、settings、analysis stateに副作用がない。
- [x] official manifest URL以外、任意URL、任意host、redirect、cloud ASR、音声外部送信がない。

### 12.2 Storage and integrity

- [x] preflightがwrite permission、local-only path、free spaceを確認し、unknown/不足時にworkerを開始しない。
- [x] B4はB2のcanonical `.part`へだけ書き、finalへ直接書かない。
- [x] Content-Lengthがmanifest exact sizeと一致しない、または欠落する場合にfail closedする。
- [x] short read、overrun、timeout、通信失敗、cancel時にpromoteしない。
- [x] B2のexact size、SHA256、manifest identity検証、atomic promotion、B2内部の対象model post-promote verification scanを通過した場合だけverifiedになる。全体availabilityの更新はcontrollerの`start_whisper_availability_rescan()`で行う。
- [x] SHA256/size/promote失敗時にexisting verified finalが保持される。
- [x] cancel/failure/close後の`.part`をbest-effort cleanupし、cleanup failureがあってもavailableにしない。
- [x] retryは最初からであり、HTTP Range、resume、複数同時downloadがない。

### 12.3 Worker and UI lifecycle

- [x] download workerはAudioWorkerと分離され、UI threadをブロックしない。
- [x] 1 operation at a time、duplicate start、競合delete、stale/late callbackを拒否する。
- [x] close時にjobを失効させ、cancelとcleanupを要求し、UI threadからjoinしない。
- [x] download success/failure/cancel後に、再起動せずretry・B4の明示保存先変更・既存候補選択へ復帰できる。
- [x] 保存先変更はB2のlocal-only resolve、既存設定保存、new-root store構築、local-only rescanまでを完了し、cancel/invalid/save failureではold root/stateを保持する。
- [x] progress、status、safe error、Retry、theme、既存GUI状態が一貫して表示される。
- [x] 保存先変更のmanaged mergeで`system` / `light` / `dark` theme、window、recent path、selected / active identityその他の非対象設定が保持され、`whisper_models_dir`だけが置換される。
- [ ] Python 3.13.xでB4対象test群と既存関連回帰を実行し、実行ファイルpath・`--version`・process exit code `0`を記録する。Python 3.14.3だけの結果で互換性完了を宣言しない。

### 12.4 Delete and milestone boundary

- [x] Deleteは確認承認後だけ開始する。
- [x] B4は`OwnershipReleasePermit`を発行せず、B5 provider未接続・permitなし・permit拒否時は削除しない。
- [x] active worker / loader ownershipが残るモデルを削除しない。
- [x] B4 standaloneではprovider未接続時のblockedとtest-only provider seamを確認し、B5連携前に実production Delete成功を宣言しない。
- [x] B2 delete成功後だけ`start_whisper_availability_rescan()`がlocal-only rescanを行い、availability/list/Info/selectionを同一projectionで更新する。
- [x] B4がactive/loaded/analysis identity、Preview、diagnostics、VMD saveabilityを暗黙に変更しない。
- [x] B1/B2/B3、MS23固定morph・Latin profile・preset・diagnostics・fingerprint契約を壊さない。
- [x] B5へ、Apply/Re-analyze、single-active/unload、ownership permit発行、analysis invalidationの接続点を引き渡せる。

## 13. リスクと対策

| ID | リスク | 分類 | 対策 |
|---|---|---|---|
| MS24-B4-R1 | 確認拒否や候補選択からnetworkが起動する | P1候補 | confirmation後だけcontrollerがpreflight/workerを呼べる入口にし、no-network回帰を追加する |
| MS24-B4-R2 | HTTP responseが任意URLやredirect先へ到達する | P1候補 | manifest URL再検証、fixed host/path、redirect全面拒否、3xx failureのfake transport testを固定する |
| MS24-B4-R3 | partialや不正重量がavailableになる | P1候補 | canonical `.part`、Content-Length exact、B2 promote、B2内部の対象model post-promote verification scan、partial cleanupを一つの経路へ固定する |
| MS24-B4-R4 | cancel後のold callbackが新しいdownloadを上書きする | P1候補 | job ID、model key、shutdown guardをcallbackごとに検証し、retryごとに新jobを発行する |
| MS24-B4-R5 | finalを直接上書きして既存verified modelを壊す | P1候補 | B2 `staging_path`と`promote_verified_staging`だけを使用し、final pathをB4へ公開しない |
| MS24-B4-R6 | free space不明・不足のまま大容量writeを開始する | P2候補 | confirm後・network前のB2 preflightを必須化し、failure時はworkerを開始しない |
| MS24-B4-R7 | download workerをAudioWorkerへ混在させる | P2候補 | dedicated worker/module/stateを追加し、AudioWorkerのkind/cancel/lifecycleを変更しない |
| MS24-B4-R8 | UI close時のworkerが破棄済みviewへcallbackする | P1候補 | shutdown/job invalidation、cancel、late callback no-op、UI thread non-joinを固定する |
| MS24-B4-R9 | B5未実装時にB4がpermitを自作して削除する | P1候補 | provider未接続時はblocked、opaque permitはB5 issuerだけが発行、B2 verifierへ委譲する |
| MS24-B4-R10 | active/analysis identityを削除成功時にB4が暗黙clearする | P1候補 | B4はdelete orchestrationだけを担当し、active/unload/invalidationをB5境界へ残す |
| MS24-B4-R11 | B4のtransfer statusとB2 artifact statusを一つへ混在させる | P2候補 | artifact / transfer / ownershipを別軸DTOにする |
| MS24-B4-R12 | 大容量downloadをUI threadで実行する | P1候補 | dedicated daemon worker、bounded progress、wx callback、UI non-blocking testを追加する |
| MS24-B4-R13 | retryがpartial resumeやsilent retryになる | P2候補 | `.part` cleanup後に新jobを最初から開始し、Range header・timer retryを禁止する |
| MS24-B4-R14 | download/delete後にRightPaneが古いavailabilityを表示する | P3候補 | local-only rescanを成功後に行い、単一projection turnでlist/Info/selectionを更新する |
| MS24-B4-R15 | new dependencyやWhisper version driftでpackage境界が変わる | P2候補 | stdlib transportを優先し、依存値と`openai-whisper==20250625`を変更しない |
| MS24-B4-R16 | B4 acceptanceに保存先変更があるのに、設定UI・検証・再scanが未定義になる | P2候補 | B4のWhisper tabへ明示DirDialog操作を追加し、B2 resolve・設定保存・new-root scan・no-fallbackを固定する |
| MS24-B4-R17 | Delete provider、B2 delete、post-delete scanをUI threadで実行して画面が停止する | P2候補 | management worker内でownership provider・deleteを実行し、`start_whisper_availability_rescan()`がavailability workerを起動する。UI callbackはprojectionだけにする |
| MS24-B4-R18 | B4単独でB5 permit発行後のDelete成功まで要求し、未実装B5と受け入れ条件が衝突する | P2候補 | B4 standaloneのblocked/test seamと、B5連携後の実Deleteを受け入れ条件として分離する |

## 14. 実装時の注意

1. まずB2/B3のlive APIを読み、計画上の候補名をそのまま新しいpublic APIとして増やさない。既存`WhisperModelStore`のfailure code、DTO、canonical path、permit verifierを正本とする。
2. Download開始の起点は、ユーザーの明示操作と確認承認の二段階である。startup scanや候補選択のcallbackから同じcontroller methodを呼び回して通信を開始できる構造にしない。
3. URL、filename、SHA256、sizeはmanifestから解決し、ユーザーが入力したpath・URL・filenameを受け取らない。HTTP redirectは全面拒否し、transportの既定挙動へ任せない。
4. `Content-Length`とmanifest exact sizeの比較をwrite前に行い、stream終了後にもreceived bytesを比較する。headerだけを信頼してshort readを成功にしない。
5. `.part`を削除できなかった場合でも、既存finalを壊さず、verified availableへ昇格させない。cleanup failureは次回scanとdiagnosticsで追跡できるようにする。
6. cancel、failure、retry、closeにはそれぞれjob IDを付ける。cancel eventだけを共有して、旧workerが新workerへ結果を返す構造にしない。
7. wx callbackはUI threadへ戻してからstateを変更する。workerからRightPaneや`UiState`を直接変更しない。
8. `management_busy`は音声解析Busyと別軸で扱う。モデル管理中にselection、storage root、Delete、将来のApplyが競合しないlockを明示する。
9. B4はDownload済みモデルを「verified local artifact」として扱うだけで、active model、loaded model、analysis model、再解析完了とは扱わない。B5のApply/Re-analyze接続まで状態表示を先取りしない。
10. Deleteのconfirm後でも、B5 ownership providerとB2 permit verifierを通過しなければfilesystemに到達させない。B4やtest helperから公開fieldの組み合わせでpermitを作らない。
11. delete成功後にselected keyを別モデルへ変更しない。candidateがmissingになった状態を表示し、ユーザーが改めてDownloadを明示できるようにする。
12. 保存先変更はB2 `resolve_whisper_models_dir()`と既存設定保存を通し、invalid pathではold rootを保持する。保存先変更後のscanはB3同様workerで行い、networkやactive変更を発生させない。
13. `worker_state.py`を変更する場合も、既存AudioWorkerの`CancelToken`、status、Busy、late-result契約へ意味を混ぜない。専用state moduleが可能ならそちらを優先する。
14. testsでは実ネットワーク、実モデル重量、ユーザーのruntime rootを使用しない。fake transportとtemporary local rootを使用し、process exit code `0`を記録する。
15. 手動GUI確認を実施した場合は、実施した項目だけを報告する。実ネットワーク未実施、実MMD未実施、package未実施を完了扱いにしない。
16. 実装後の文書closeoutでは、B4の実装・自動検証・手動GUI確認の到達範囲を、B5、MS26、MS27の未実施項目と分けて記録する。push、merge、tag、releaseは別承認が必要である。
