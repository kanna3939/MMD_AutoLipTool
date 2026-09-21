# MS25-B6 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B6 transaction・衝突・失敗復旧
- 作成日: 2026-09-03
- 作成時ベースライン: `feature/MS25-implementation` / `bb9c60d Complete MS25-B5 delivery package GUI integration`
- 状態: 実装済み・自動検証済み・ユーザー報告の手動GUI確認済み。B7のfull cross-boundary regression / closeoutは未完了
- 成果物: B6 production code、B6専用test、既存回帰の契約同期、および本計画書の実装結果記録
- 前提到達状態:
  - MS25-B1〜B5は実装済み
  - B5の対象自動回帰と全pytestは完了済み
  - B5の手動GUI確認はユーザー報告の範囲で通過済み
  - B6のWindows fault matrixとrecovery hardeningは実装・検証済み
- 後続:
  - MS25-B7: full cross-boundary regression、利用者文書・正本同期、MS25 closeout準備
  - MS26: 実MMDでのVMD / WAV読込・再生・リップ同期確認
  - MS27: PyInstaller onefile、ZIP、最終artifact、package / release readiness

### 1.1 正本と現行実装の優先順位

判断は次の順で行う。

1. live Gitと現行production code / test
2. `docs/Implementation_Plan/MS25_Block_Breakdown.md`
3. `docs/MS20_and_Beyond_Roadmap.md` §12〜§15
4. Pipeline / Error / GUI State / VMD Outputの各正文仕様
5. MS25-B1〜B5 Implementation Plan

過去計画に存在する「後続で実装」等の記述は、その後のlive codeで実装済みなら履歴として扱う。B6で既存APIを再設計せず、現行APIへ不足するhardeningを追加する。

## 2. 背景

MS25は、現在の編集済みVMD状態、入力音声から再生成したMMD用WAV、同じ診断snapshotから生成したreportを、一つの専用directoryへall-or-nothingで確定する機能である。

B1〜B5で、次のproduction境界が実装済みである。

- `DeliveryCurrentState` / `DeliveryStartContext`による同一captureの固定
- `evaluate_delivery_start_gate()`と`evaluate_delivery_commit_fingerprint()`による開始時・commit直前のsemantic fingerprint gate
- `validate_delivery_destination()`によるWindows名・path長・親directory・既存entry検査
- `orchestrate_delivery_package()`によるVMD -> MMD WAV -> reportの固定順staging transaction
- `DeliveryArtifactOperations`と`build_delivery_artifact_operations()`による3成果物生成・validation
- `DeliveryCancelToken`、`DeliveryCommitAuthorization`、`DeliveryTerminalResult`によるcancel / commit / cleanup結果の分離
- `os.rename(staging, final)`をcommit線形化点とするno-clobber確定
- `DeliveryPackageWorker`、`AudioWorkerKind.DELIVERY_PACKAGE`、active `(job_id, worker kind, projection generation)` binding
- UI thread上のpre-commit authorization、Busy、cancel、close待機、late / duplicate terminal discard

現行実装はminimum production transactionを持つ一方、Block BreakdownがB6へ残した次の実環境・競合条件を網羅していない。

- actual Windows junction / reparse pointを含むdestination collision
- permission denied、locked、readonly、invalid path、antivirus等によるcommit / cleanup fault
- dialog後・最終存在検査後・rename直前のTOCTOU
- staging rootやartifact entryの外部差替え
- 各生成・validation phaseとcancelの競合
- cleanup処理自体の例外と残存stagingの正確なterminal化
- staging、commit直前、commit中、commit後のwindow close

B6はB2のtransaction設計やB5のGUI導線を作り直すBlockではない。既存の線形化点、terminal DTO、semantic fingerprint、worker bindingを維持し、fault injectionとactual Windows filesystem証拠によって不足を補強する。

## 3. 目的

1. final pathに既存filesystem entryが一つでもあれば、種類・空否を問わずcollisionとして拒否することを実証する。
2. dialog後に同名destinationが作成されても、no-clobber commitで既存entryを変更しないことを保証する。
3. VMD / WAV / reportの生成・validation、source identity、commit guard、commit、cleanupの各failureを決定的に分類する。
4. commit線形化点前のfailure / cancelではowned stagingだけをcleanupし、partial finalを公開しない。
5. cleanup failureをprimary failure / cancelと分離し、`partial_output_cleanup_failed`を成功扱いにしない。
6. current semantic fingerprintだけをfilesystem commit guardとし、`projection_generation`をlate-result投影用途へ限定する。
7. cancelとcommitの順序を一つの線形化規則で固定し、commit済みfinalをcancel cleanupで削除しない。
8. B5のBusy / worker / close / terminal projectionがB6 fault下でも復旧可能であることを確認する。

## 4. In Scope

- final destinationのcollision matrix:
  - empty directory
  - non-empty directory
  - regular file
  - valid symlink
  - broken symlink
  - Windows junction / mount point等のreparse point
- `os.lstat()`を使う`lexists`相当の検査と、`st_file_attributes`のreparse bitを使うfail-closed判定
- destination dialog完了後からcommit開始までのTOCTOU fault injection
- `os.rename()`によるWindows no-clobber commitのactual filesystem検証
- parent / staging作成、成果物生成、read-back validation、source identity再確認、commit guard、commit、cleanupのfailure分類
- VMD / MMD WAV / report各phaseのwrite failureとvalidation failure
- permission denied、locked / sharing violation、invalid path、inspection failure、final commit failure
- owned staging identityとdirect-child境界の再確認、および外部差替え時のfail-closed
- cleanup success / missing / permission denied / locked / reparse差替え / unexpected exception
- commit前、commit lock競合中、commit開始後、commit成功後のcancel
- `DeliveryTerminalResult`の全field不変条件
- B5のdelivery worker、Busy、cancel、close、late / duplicate result、safe error projectionとの接続
- 自動testで再現できないOS dialog表示・window close操作のmanual GUI確認境界
- B6実装後の対象回帰、`compileall`、diff監査

## 5. Out of Scope

- MS25-B1のartifact命名、開始gate、fingerprint schema / payload / digestの再設計
- `projection_generation`をfilesystem commit identityへ昇格する変更
- MS25-B3のVMD binary形式、MMD WAV仕様、report形式の再設計
- B5のmenu、destination dialog、Busy UIの再設計
- 個別VMD保存、個別MMD WAV出力、個別report保存の仕様変更
- 既存packageのmerge、replace、overwrite、automatic rename、suffix付与
- final directory作成後に成果物を一件ずつcopyする方式
- package manifest、hash、ZIP、session file、MMD project管理、MMD自動起動
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読取り・変更・stage
- 新規依存関係、PyInstaller spec、build script、license文書の変更
- cloud ASR、外部送信、background通信、Qt / PySide6
- MS25-B7のfull cross-boundary closeoutと利用者文書の最終同期
- MS26の実MMD確認
- MS27のpackage / release readiness

## 6. 前提条件

### 6.1 固定済みtransaction契約

- stagingはresolved parent directoryのdirect childかつfinalと同一volumeに置く。
- 生成順はVMD -> MMD WAV -> reportとする。
- final directoryには成功時だけ固定3成果物を公開する。
- commit前の既存entry検査だけを排他制御とみなさない。
- commit線形化点は、commit lock内で`commit_started`へ遷移し、no-clobber renameを開始する時点とする。
- commit成功後は`committed=True`、`final_path`あり、cleanup不要のsuccess terminalだけを許す。
- commit失敗時は`committed=False`とし、owned staging cleanup後にfailure terminalを返す。

### 6.2 final entryの不存在判定

現行`_inspect_delivery_absence()`は`os.lstat()`が`FileNotFoundError`を返した場合だけ不存在とする。通常directory、file、symlink、broken symlink、reparse pointはすべて`lstat`成功となるためcollisionである。この`lexists`相当の意味を維持する。

Windows reparse判定は、entryを辿る存在判定ではなく、`lstat`結果の`stat.S_ISLNK()`または`st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT`を使う。検査不能は不存在へfallbackせず`output_path_inspection_failed`とする。

### 6.3 semantic fingerprintとUI generation

- commit guardは`start_context.current_state.start_fingerprint`と、UI threadでpureに再構築したcurrent snapshotのfingerprintを比較する。
- effective outputまたはstable diagnostics identityが変われば`delivery_state_stale`とする。
- Busy表示、diagnostics再投影、theme、panel refresh等による`projection_generation`差だけではcommitを拒否しない。
- `projection_generation`はjob ID / worker kindと組み合わせたlate / duplicate UI callback破棄だけに使用する。

### 6.4 source identityの保証範囲

入力音声はMMD WAV生成直前と生成・validation後に、resolved path、size、`mtime_ns`、取得可能なdevice / file / attribute identityを開始contextと比較する。content hashは追加しない。同一identityを意図的に維持したbyte置換は検出保証外であり、B6で完全byte identity保証へ拡張しない。

### 6.5 OS fault分類の原則

現行error codeと`artifact_phase`を正本として維持する。実装時にprivate分類helperが必要な場合は候補として追加してよいが、public API追加を前提にしない。

- 成果物の形式・内容validation failureは、`artifact_phase`と既存の`vmd_validation_failed`、`mmd_wav_validation_failed`、`report_validation_failed`を維持する。
- 成果物生成中のfilesystem failureは、`artifact_phase`で対象を示し、`primary_error_code`を次の優先順位で固定する。artifact以外のstaging / commit I/Oにも同じ分類を適用する。
  1. commit時にdestination entryが存在する場合は、原因にかかわらず`output_destination_collision`。
  2. Windows `winerror` 32 / 33または`errno.EBUSY`など、OSが使用中と示す場合は`output_file_locked`。
  3. `PermissionError`、Windows `winerror` 5、`errno.EACCES` / `errno.EPERM`など、権限拒否と示す場合は`output_permission_denied`。
  4. Windows `winerror` 123（invalid name）、206（path too long）、267（invalid directory）または`errno.ENAMETOOLONG` / `errno.ENOTDIR`など、パス不正と示す場合は`output_path_invalid`。入力音声の不存在・変更はこの規則で上書きせず、既存のsource identity codeを維持する。
  5. 上記以外のartifact filesystem failureは既存phase固有write code、commit I/O failureは`delivery_commit_failed`へfail closedする。
- 分類はraw exception messageやlocaleに依存せず、例外型・`winerror`・`errno`とcause chainを使う。collision判定をOSエラー分類より先に行う。
- `app_controller.py`には、少なくとも`output_permission_denied`、`output_file_locked`、`output_path_invalid`、`output_path_inspection_failed`、`output_destination_collision`、`partial_output_cleanup_failed`のsafe messageを必須追加・確認する。raw exception、traceback、絶対staging pathは通常表示しない。
- DTOは増やさず、`artifact_phase`と`primary_error_code`で対象と原因を分離する。既存fieldで原因を表現できないことが実装前チェックで証明された場合だけ、互換性確認後に追加案を提示し、独断でpublic contractを拡張しない。

## 7. 対象ファイル

### 7.1 B6 production変更候補

| ファイル | 変更候補 | 境界 |
| --- | --- | --- |
| `src/core/delivery_package.py` | collision / OS error正規化、staging identity再確認、cleanup例外terminal化、commit / cancel race hardening | B1 DTOとB2 public orchestration signatureを原則維持 |
| `src/core/delivery_artifacts.py` | fault cause保持、cancel起因例外と独立failureの順序整理が必要な場合のみ限定変更 | VMD / WAV / report形式を変更しない |
| `src/gui_wx/audio_worker.py` | ownership後例外やterminal one-shotに不足が確認された場合のみ補修 | generic `AudioWorker`の契約を広げない |
| `src/gui_wx/app_controller.py` | B6 faultのsafe表示、cleanup warning、close / terminal raceの限定補修 | B5のdialog・Busy・binding設計を維持 |
| `src/gui_wx/main_frame.py` | actual close lifecycleで不足が確認された場合のみ限定補修 | UI再設計をしない |
| `src/gui_wx/worker_state.py` | 現行stateで表現不能な場合のみ候補 | 新kindは追加済みのため通常は変更不要 |
| `src/gui_wx/ui_state.py` | 現行Busy / worker stateで表現不能な場合のみ候補 | delivery専用永続stateを追加しない |

private helper名の例として、OS error分類、owned staging identity確認、no-clobber commit wrapperが考えられる。ただし、これらは現行関数へ局所統合できるなら新APIにしない。

### 7.1.1 既存契約の検証とB6追加実装の境界

| 分類 | 対象 | B6での扱い |
| --- | --- | --- |
| 現行実装済み・B6では証拠化 | `lstat`によるfinal entry collision、同一親directory staging、VMD -> WAV -> report順、commit lockと`os.rename()`、cancel線形化、`DeliveryTerminalResult`のcleanup field | 既存契約を再実装せず、actual Windows / fault injection / race testで検証する |
| B6でgapが確認されれば必須修正 | OS error分類とsafe message、owned staging lifetime全体の例外封じ込め、phase境界のstaging identity再確認、cleanupの非追跡削除、状態不整合時のclose fail-closed | focused testが失敗した箇所だけを局所修正する |
| 条件付き変更 | `delivery_artifacts.py`、`audio_worker.py`、`main_frame.py`、`worker_state.py`、`ui_state.py`の追加変更 | 既存契約またはB6受入条件の不足が実証された場合だけ変更し、変更理由を実装後報告へ記録する |

この境界により、既にB2 / B5で実装済みのtransactionやUI lifecycleをB6で無目的に再設計しない。B6の実装完了は、検証だけで足りる項目とproduction hardeningが必要な項目を実行結果で区別して判定する。

### 7.2 B6 testファイル（必須）

| ファイル | 主な責務 |
| --- | --- |
| `tests/test_ms25_b6_windows_collision_faults.py` | actual / injected symlink・junction・reparse、permission、locked、invalid path、TOCTOU、no-clobber |
| `tests/test_ms25_b6_delivery_failure_recovery.py` | 3成果物fault matrix、staging差替え、cleanup、terminal invariants、cancel / commit線形化 |
| `tests/test_ms25_b6_delivery_gui_recovery.py` | Busy、safe projection、commit guard、close、late / duplicate terminal |

上記3ファイルをB6専用testとして作成し、§11.6の必須gateで実行する。既存B2 / B3 / B5 testへの補足は許可するが、B6専用の3ファイルを省略・統合して必須gateを曖昧にしない。テスト観点は削らない。

### 7.3 回帰確認対象。原則変更しない（契約同期例外を含む）

B6でOS fault分類を詳細化するため、`tests/test_ms25_b2_delivery_commit.py::test_rename_failure_without_destination_is_failed_and_cleaned`の`primary_error_code`期待値は、B6実装時に`delivery_commit_failed`から`output_permission_denied`へ同期する。これはテストを弱める変更ではなく、Error Handling仕様§15.2および本計画§6.5の分類契約を既存回帰へ反映する契約同期である。分類対象外のrename I/Oでは`delivery_commit_failed`を維持する回帰を、B6専用の`tests/test_ms25_b6_delivery_failure_recovery.py`へ追加する。

- `tests/test_ms25_b1_delivery_contract.py`
- `tests/test_ms25_b1_current_state_gate.py`
- `tests/test_ms25_b2_windows_paths.py`
- `tests/test_ms25_b2_delivery_orchestration.py`
- `tests/test_ms25_b2_delivery_commit.py`
- `tests/test_ms25_b3_delivery_artifacts.py`
- `tests/test_ms25_b3_vmd_readback_validation.py`
- `tests/test_ms25_b4_delivery_report_identity.py`
- `tests/test_ms25_b5_delivery_worker.py`
- `tests/test_ms25_b5_delivery_gui.py`
- `tests/test_ms17_b7_mmd_wav_export.py`
- `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms19_b8_workspace_reset.py`

### 7.4 B6実装時に変更しない文書・データ

- README、`readme_mmdautolip.txt`、Pipeline / GUI / VMD正文仕様の最終同期はB7で扱う。Error Handling仕様の`output_path_inspection_failed`一覧補正だけは、今回のP3解消として先行して反映する。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`は直接読取り・変更・stageしない。
- dependency、lock file、PyInstaller spec、build script、license文書は変更しない。

## 8. 実装方針

### 8.1 既存DTOと線形化点を維持する

`DeliveryTerminalResult`、`DeliveryCancelToken`、`DeliveryCommitAuthorization`、`orchestrate_delivery_package()`をB6の基礎とする。B6のために別transaction manager、別cancel token、別terminal callbackを作らない。

### 8.2 collisionをentry種別から独立させる

- final pathへの`lstat`成功は常にcollisionとする。
- `Path.exists()`、`Path.is_dir()`、directory empty判定をcollision許可条件に使わない。
- broken symlinkとreparse pointを「不存在」と扱わない。
- inspection permission / I/O failureはcollisionではなくinspection failureとしてfail closedにする。
- GUIではcollision時に同名entryの種類を推測せず、別名指定を要求する。

### 8.3 TOCTOUとno-clobber commit

次の各時点でdestinationを作成するfaultを注入する。

1. destination dialog後・worker開始前
2. staging作成後
3. 各artifact生成後
4. pre-commit authorization後
5. commit lock取得直前
6. rename開始直前

1はGUI validation loopで拒否し、2〜6はcore terminalで拒否する。最終防衛線はWindows no-clobber renameであり、既存entryを事前削除してrenameを再試行しない。rename failure後にdestinationが存在する場合はcollisionへ正規化し、既存bytes / treeを保持する。

### 8.4 owned staging identityと差替え防御

現行のdirect-child、same-device、non-reparse directory検証に加え、staging作成直後の`lstat` identityを保持し、少なくとも各artifact callback前後、最終contents検証前、commit lock内で同一entryであることを再確認する。

identityはresolved pathだけでなく、取得可能な`st_dev`、`st_ino`、`st_file_attributes`、directory / reparse種別を比較する。取得不能または差替えを検出した場合はcommitしない。cleanupは差替え先targetを再帰追跡せず、現在のentry自身だけを安全に扱う。identity DTO / helperの正確なprivate名は実装前チェックで決める。

これはpathベースwriterの`lstat`確認から次のopenまでをWindows handleで不可分にする保証ではない。既存writer APIが`Path`を受け取る以上、B6の保証範囲はphase境界・最終commit前での差替え検出、commit拒否、cleanup時の外部target非追跡に限定する。任意の瞬間の差替えによる書込みを完全防止するとは記載せず、必要なら将来のhandle-relative / no-follow設計として別スコープへ残す。

### 8.5 fault matrixとprimary result

| Phase | 代表fault | Primary result | Cleanup | Final |
| --- | --- | --- | --- | --- |
| destination gate | existing entry | `output_destination_collision` | `not_required` | 既存entry不変 |
| destination inspection | permission | `output_permission_denied` | `not_required` | 不変 |
| destination inspection | other I/O / invalid path | `output_path_inspection_failed`または`output_path_invalid` | `not_required` | 不変 |
| staging create | permission / invalid / locked | `output_permission_denied` / `output_path_invalid` / `output_file_locked`または`output_staging_create_failed` | 作成済みowned stagingだけcleanup | 作らない |
| VMD generate | logical writer failure | `vmd_write_failed`, `artifact_phase=vmd` | staging cleanup | 作らない |
| VMD generate | permission / locked | `output_permission_denied` / `output_file_locked`, `artifact_phase=vmd` | staging cleanup | 作らない |
| VMD validate | malformed / truncation / read failure | `vmd_validation_failed`, `artifact_phase=vmd` | staging cleanup | 作らない |
| WAV pre-identity | changed / inaccessible | `source_audio_changed`, `artifact_phase=mmd_wav` | staging cleanup | 作らない |
| WAV generate | FFmpeg / logical failure | `mmd_wav_write_failed`, `artifact_phase=mmd_wav` | staging cleanup | 作らない |
| WAV generate | permission / locked | `output_permission_denied` / `output_file_locked`, `artifact_phase=mmd_wav` | staging cleanup | 作らない |
| WAV validate / post-identity | format不一致 / source変更 | `mmd_wav_validation_failed`または`source_audio_changed` | staging cleanup | 作らない |
| report generate | format / writer failure | `report_write_failed`, `artifact_phase=report` | staging cleanup | 作らない |
| report generate | permission / locked | `output_permission_denied` / `output_file_locked`, `artifact_phase=report` | staging cleanup | 作らない |
| report validate | bytes / UTF-8 / BOM / LF不一致 | `report_validation_failed`, `artifact_phase=report` | staging cleanup | 作らない |
| commit guard | stale / invalid / timeout | `delivery_state_stale`等 | staging cleanup | 作らない |
| final rename | collision | `output_destination_collision`, `commit_failed` | staging cleanup | 既存entry不変 |
| final rename | permission / locked | `output_permission_denied` / `output_file_locked` | staging cleanup | 作らない |
| final rename | other I/O | `delivery_commit_failed` | staging cleanup | 作らない |
| cleanup | delete / inspection failure | primaryを保持し`partial_output_cleanup_failed`併記 | staging pathをinternal保持 | 既存final不変 |

生成・validation failureのphaseは`artifact_phase`で保持する。OS causeをuser-facing messageへraw展開せず、既存codeで十分に区別できないことが実装前チェックで確認された場合だけ、互換的な加算fieldまたはinternal diagnostics候補を提示する。

### 8.6 cancelとcommitのlinearization

- commit lockより先にcancelが受理された場合、`request_cancel()`は`True`を返し、renameを呼ばない。
- commit lock内で`commit_started`へ遷移した後のcancelは`False`を返し、rename結果を待つ。
- rename成功後はcancel requestの有無にかかわらずsuccess terminalを返し、finalを保持する。
- rename失敗後はfailure terminalとcleanup resultを返す。後着cancelで`cancelled`へ上書きしない。
- commit guard待機中のcancel / closeはauthorizationを発行せずcancel terminalへ進む。
- cancelを原因としてactive FFmpegが停止し例外終了した場合はcancel terminalを許す。一方、先に確定した独立primary failureを後着cancelで消さない。必要ならtokenの受理phaseを利用し、raw task終了時のflagだけで再分類しない。

### 8.7 cleanup契約

- cleanup対象は、そのinvocationが作成し、まだcommitされていないexact owned stagingだけとする。
- final path、親directory、prefixが似た別directory、個別保存出力、既存packageを削除しない。
- cleanupはbest effortで実行するが、例外をterminal喪失へつなげない。
- 通常directoryだけを再帰削除する。symlink / reparseへ差し替わっていた場合はtargetを辿らずentry自身の削除だけを試みる。
- cleanup後に`lstat`でabsenceを確認する。
- cleanup成功は`completed`か、cleanup対象なしなら`not_required`とする。
- cleanup失敗はprimary status / code / artifact phase / commit phaseを保持し、`partial_output_cleanup_failed`と残存staging pathをinternal fieldへ保持する。
- staging ownership取得後の通常`Exception`は、artifact、guard、contents inspection、commit、cleanupを含むowned staging lifetime全体でterminal resultへ収束させる。cleanup helper自身の`OSError`以外の例外も、primary resultを失わず、再度の存在確認を経て`partial_output_cleanup_failed`へ収束させる。workerのownership後fallbackが`staging_path=None`へ情報を落とす経路を残さない。
- GUI通常通知にraw exception、traceback、credential、絶対staging pathを表示しない。

### 8.8 B5 GUI / worker / diagnostics接続

- BusyはB6 terminalと必要なcleanup結果の受理まで解除しない。
- delivery workerのone-shot completion gateを通らない別filesystem結果を作らない。
- active job ID / worker kind / projection generation不一致のlate / duplicate callbackはUIへ投影しない。
- late-result discardをfilesystem cancellationの代用にしない。
- close pending時はpre-commitならcancelを要求し、terminalまでwindowを破棄しない。
- commit開始後は「finalizing」としてterminalを待ち、成功済みfinalをcleanupしない。
- close判定は`is_delivery_active()`の完全一致だけに依存しない。delivery worker参照、active binding、UiStateのdelivery worker state、delivery close pendingのいずれかが残る場合を`delivery_may_be_active`として扱い、workerが存在する・aliveである・terminal未受理である間はgeneric audio closeへ流さずDestroyしない。完全binding不一致時はcommit authorizationを拒否し、安全なreconciliationまたはdelivery terminal受理まで待つ。
- workerが既に存在しない状態でdelivery bindingまたはUiStateだけが残った場合も、通常の音声worker終了へ流さず、delivery専用のfailed reconciliationとして一回だけ状態を収束させてからcloseを許可する。close中に新しいfinal commitを開始できないことを受入条件にする。
- cleanup failureだけはclose pending中もsafe warningを1回表示し、確認後にexitする。staging pathは表示しない。
- B6 faultによってindividual save history、WARNING確認済みfingerprint、diagnostics snapshot、Preview、runtime INIを変更しない。

## 9. 詳細ステップ

### Step 1: fresh pre-implementation check

- live Git、B6 plan、Block Breakdown、B1〜B5 code / testを再確認する。
- B2 testが既に保証する条件とB6で不足するactual Windows / race条件を重複なく整理する。
- current `os.rename()`のWindows no-clobber挙動、Python 3.11以上で利用可能な標準API、テスト環境のsymlink / junction作成可否を確認する。
- production変更前にP1 / P2 / P3を分類し、未解消P1 / P2があれば実装を開始しない。

### Step 2: deterministic fault seams

- destination inspection、staging作成、artifact callback、contents validation、commit guard、rename、cleanupを既存monkeypatch seamで再現できるか確認する。
- global hookやproduction debug modeは追加しない。
- 不足する場合だけprivate callable / helper分離を追加する。

### Step 3: Windows collision / no-clobber hardening

- empty / non-empty directory、file、valid / broken symlinkをactual temporary pathで検証する。
- Windowsではjunction / reparse pointをtemporary fixture内に作成し、既存targetを保持したままcollisionになることを確認する。
- actual reparse作成が権限・OS設定で不能な場合でも、B6の完了扱いにはしない。`lstat` / reparse attribute injection testは必須だが、injectionはactual Windows証拠の代用ではない。少なくともWindows 11の実filesystem上でjunctionまたはreparse point collisionを1件実行し、skipされた場合はB6を条件付き・未完了としてB7へ持ち越す。
- locked / sharing violationもdeterministic injectionを必須とし、Windows actualのpermission deniedまたはsharing violationを少なくとも1件実行する。実行できずskipされた場合も、B6の完了判定を出さず未検証として記録する。
- rename直前に各種類のdestinationを作り、no-clobberとbyte-for-byte / tree不変を確認する。

### Step 4: staging ownership / cleanup hardening

- staging identityを作成直後とphase境界で再確認する。
- file、symlink、junction、別directoryへの差替えをcommit前に拒否する。
- path-based writerのopen前に任意の差替えを完全に防ぐことはB6の保証にしない。phase境界・commit前の差替え検出と、cleanup時に外部targetを辿らないことを検証する。
- cleanup helper自身が`OSError`または予期しない通常例外を返しても、owned staging pathを保持したまま再存在確認し、一つのterminal resultへ収束させる。ownership取得後にworker fallbackへ漏らさない。

### Step 5: artifact fault matrix

- VMD / WAV / reportについて、write failureとvalidation failureを別々に注入する。
- WAVのsource identity前後変更を分ける。
- operation正常return後のmissing / empty / directory / symlink / reparse artifactを拒否する。
- 各caseで固定順の後続operationを呼ばず、final不在、staging cleanup、terminal fieldsを確認する。

### Step 6: cancel / commit race

- deterministic `Event` / barrierを用い、commit lock取得前、取得中、rename開始後、rename成功後を制御する。
- timing依存sleepだけでrace testを成立させない。
- cancel先行時はrename未呼出し、commit先行時はcancel拒否とrename結果優先を確認する。
- commit失敗と後着cancelが競合してもfailureをcancelへ上書きしない。

### Step 7: GUI close / terminal recovery

- staging中close、guard待機中close、commit lock後close、commit成功後closeをfake worker / controlled coreで再現する。
- terminal / cleanup前のDestroy禁止、terminal後の一回だけのexitを確認する。
- cleanup failure warning、late / duplicate terminal、job / kind / projection mismatchを確認する。
- worker参照のみ、active bindingのみ、UiState delivery stateのみ、複数が不一致の各状態を作り、`delivery_may_be_active`がgeneric closeへ流さず、authorization拒否またはfailed reconciliation後だけDestroyを許すことを確認する。

### Step 8: scope / diff audit

- 変更をB6 hardeningと専用testへ限定する。
- runtime data、dependency、package、build、license、個別保存historyに差分がないことを確認する。
- fingerprint schema、VMD format、WAV spec、report identityを変更していないことを確認する。

### Step 9: automated verification and handoff

- §11の順でtestを実行し、pass表示とprocess exit codeを記録する。
- manual GUIは実施者と範囲を限定して記録する。
- B7へfull regression、利用者文書同期、closeout判定を引き継ぐ。

## 10. 状態遷移 / データ契約

### 10.1 transaction state

```text
Ready candidate
  -> Destination validated
     -> collision / invalid / inspection failure: no staging, safe failure
  -> Owned staging created and identity captured
  -> VMD generate -> validate -> staging identity recheck
  -> source identity pre-check
  -> MMD WAV generate -> validate -> source identity post-check
  -> staging identity recheck
  -> report generate -> validate
  -> exact staging contents + identity recheck
  -> Awaiting commit guard
     -> stale / invalid / cancel / close / timeout: cleanup -> terminal
  -> final absence recheck
  -> commit lock
     -> accepted prior cancel: cleanup -> cancelled terminal
     -> commit_started: later cancel cannot alter result
  -> no-clobber rename
     -> success: committed terminal, final retained
     -> collision / I/O failure: staging cleanup -> failed terminal
```

任意のpre-commit failureでは後続phaseを実行しない。final directoryはrename成功時にのみ現れる。

### 10.2 terminal invariants

| Result | committed | final_path | staging_path | cleanup_status | commit_phase |
| --- | --- | --- | --- | --- | --- |
| success | `True` | exact final | `None` | `not_required` | `committed` |
| safe failure before staging | `False` | `None` | `None` | `not_required` | `before_commit`等 |
| failure / cancel + cleanup success | `False` | `None` | `None` | `completed` | actual phase |
| failure / cancel + cleanup failure | `False` | `None` | residual staging candidate | `partial_output_cleanup_failed` | actual phase |
| commit failure | `False` | `None` | cleanup結果に従う | `completed`またはcleanup failure | `commit_failed` |

`primary_status`、`primary_error_code`、`artifact_phase`はcleanup成否によって置換しない。`committed=True`と`cancelled`を同時に表現しない。

### 10.3 cancel acceptance

| cancel時点 | 受理 | rename | terminal |
| --- | --- | --- | --- |
| staging前 / artifact間 | Yes | 禁止 | cancelled + cleanup結果 |
| guard待機中 | Yes | 禁止 | cancelled + cleanup結果 |
| commit lock取得前 | 先にlock取得した側に従う | cancel先行なら禁止 | 線形化順に従う |
| `commit_started`後 | No | 継続 | rename結果を正本化 |
| `committed`後 | No | 完了済み | success、final保持 |
| `commit_failed`後 | Noまたはterminal済み | 失敗済み | failure、staging cleanup結果 |

### 10.4 B5 binding

filesystem authorizationはjob ID + start fingerprintで行う。UI callbackのcurrent判定はjob ID + `DELIVERY_PACKAGE` + projection generationを使う。この二つのidentityを混同しない。

## 11. テスト方針

### 11.1 Windows collision / filesystem matrix

- empty / non-empty directory、file、valid symlink、broken symlink、junction / reparse point
- preflight、artifact後、authorization後、rename直前のTOCTOU
- collision targetのbyte / tree / link target不変
- `lstat` permission / inspection failure
- Windows sharing violation / access denied / invalid name / readonly parentの正規化
- no-clobber rename成功がfinalを一度だけ公開すること

actual symlink / junction testはtemporary rootだけを対象とし、teardownはlink / junction entry自身を削除してtargetを再帰削除しない。`lstat` / reparse attribute injectionは全環境で必須とする。B6の完了gateでは、Windows 11の実filesystem上のjunctionまたはreparse point collisionを少なくとも1件、permission deniedまたはsharing violationを少なくとも1件、skipなしで実行する。環境制約でいずれかをskipした場合は理由をtest resultへ残すが、injection testの成功で代用せず、B6は条件付き・未完了とする。

### 11.2 artifact fault matrix

VMD / WAV / reportごとに次を確認する。

- write exception
- permission / locked cause
- validation exception
- missing / empty / non-regular / reparse output
- cancel before / during / after operation
- 後続artifact未実行
- final不在
- primary code、artifact phase、cleanup statusの整合

WAVはsource identityのpre / post change、FFmpeg cancel bridge、既存temporary cleanupも確認する。

### 11.3 cleanup / terminal matrix

- staging未作成
- normal cleanup成功
- stagingが既に消失
- delete permission denied / locked
- `shutil.rmtree` failure
- staging rootのsymlink / reparse差替え
- cleanup中の通常例外
- primary failure中のcleanup failure
- cancel中のcleanup failure
- commit failure中のcleanup failure
- `DeliveryTerminalResult` constructor invariants

### 11.4 cancel / commit / close matrix

- commit前cancel
- guard callback待機中cancel / close
- commit lock競合でcancel先行
- commit lock競合でcommit先行
- rename中cancel
- rename成功直後cancel
- rename failureと後着cancel
- staging中window close
- commit直前window close
- commit中window close
- commit後window close
- terminal前Destroy禁止、terminal後一回だけDestroy
- committed successのcancel再分類禁止
- late / duplicate / wrong job / wrong kind / wrong projection resultのUI非投影

### 11.5 semantic guard / state preservation

- current fingerprint一致でauthorization
- effective output変更でstale
- `projection_generation`だけの変更でauthorization維持
- cancel / close / invalid jobでauthorization拒否
- failure / cancel / cleanup failure後もdiagnostics snapshot、WARNING確認fingerprint、individual save history、Preview、runtime settingが不変

### 11.6 実行順

B6の必須gateは次の順で固定する。B6専用testは下記3ファイルへ分離して保持し、既存B2 / B5 fileへの補足testを追加してもこの必須集合を省略しない。

1. `tests/test_ms25_b6_windows_collision_faults.py`、`tests/test_ms25_b6_delivery_failure_recovery.py`、`tests/test_ms25_b6_delivery_gui_recovery.py`のB6専用test
2. `tests/test_ms25_b2_windows_paths.py`、`tests/test_ms25_b2_delivery_orchestration.py`、`tests/test_ms25_b2_delivery_commit.py`、`tests/test_ms25_b3_delivery_artifacts.py`、`tests/test_ms25_b3_vmd_readback_validation.py`、`tests/test_ms25_b4_delivery_report_identity.py`、`tests/test_ms25_b5_delivery_worker.py`、`tests/test_ms25_b5_delivery_gui.py`の直接回帰
3. `tests/test_ms25_b1_delivery_contract.py`、`tests/test_ms25_b1_current_state_gate.py`、`tests/test_ms20_b5_warning_save_policy.py`、`tests/test_ms20_b6_diagnostic_report.py`、`tests/test_ms20_b6_report_save_flow.py`、`tests/test_ms21_b5_adjusted_vmd_save.py`、`tests/test_ms21_b5_effective_output_identity.py`、`tests/test_ms21_b7_audio_worker_terminal.py`、`tests/test_ms17_b7_mmd_wav_export.py`、`tests/test_ms17_b7_mmd_wav_failure_cleanup.py`、`tests/test_ms17_b8_late_worker_result_discard.py`、`tests/test_ms19_b8_workspace_reset.py`、`tests/test_ms23_b6_model_profile_lifecycle.py`、`tests/test_ms24_whisper_diagnostics.py`、`tests/test_wx_ms14_b5_export.py`のsemantic / report / cross-boundary回帰
4. `.\.venv\Scripts\python.exe -m compileall -q src tests`
5. `git diff --check`

各commandは一つずつ実行し、pass件数、skip理由、process exit codeを記録する。full pytestはB6の必須gateではないが、可能なら追加実行して結果を記録する。B7ではfull pytestとfull cross-boundary suiteを必須として独立再実行する。B6の必須actual Windows junction / reparseまたはpermission / locked caseがskipされた場合は、B6の完了判定を出さず未検証事項として明記する。

### 11.7 手動GUI確認境界

B6の自動test後、次をmanual GUI候補とする。

- empty / non-empty同名directoryまたはfileを選んだ場合、別名要求となり既存entryが変化しない
- 一括出力中cancelでBusyがterminalまで維持され、終了後に再試行できる
- 一括出力中closeで即時破棄されず、terminal後に終了する
- cleanup failureをfault injection buildで可視化する必要はない。通常buildへdebug fault UIを追加しない
- success / failure / cancel後も個別VMD / MMD WAV / report保存導線が利用可能

TOCTOU、commit開始瞬間、permission / locked、actual reparse、cleanup failureはmanual GUIの偶然再現に依存せず、自動fault injectionとWindows filesystem testを受け入れ証拠とする。実MMD確認はMS26、onefile / package確認はMS27で行う。

### 11.8 B6実装後検証結果（2026-09-04）

- B6専用test 3ファイルは`26 passed`、process exit code `0`で完了した。
- B6直接回帰は`134 passed, 2 skipped`、process exit code `0`で完了した。skipは既存B2のsymlink作成権限依存であり、B6必須ケースではない。
- 指定cross-boundary回帰は`94 passed`、process exit code `0`で完了した。
- 全pytestは`1041 passed, 4 skipped`、process exit code `0`で完了した。
- Windows実filesystemのjunction collisionと、delete sharingなしのstaging directory handleによるsharing violationを各1件、skipなしで確認した。
- `compileall -q src tests`と`git diff --check`はprocess exit code `0`で完了した。
- ユーザーから、提示したB6手動GUI確認の通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。
- B6のproduction code、test code、GUI変更は`5300905 Implement MS25-B6 delivery recovery hardening`としてcommit済みである。B7のfull cross-boundary closeout、README等の最終文書同期、実MMD確認、MS27 package / release readinessは後続またはdeferredである。

## 12. 受け入れ条件

### 12.1 collision / existing output protection

- [x] empty / non-empty directory、file、valid / broken symlink、Windows reparse pointを同名destinationとして拒否する。
- [x] `Path.exists()`だけに依存せず、`lstat` / lexists相当でbroken linkを検出する。
- [x] dialog後・preflight後・rename直前のTOCTOUでも既存destinationを変更しない。
- [x] collision時にmerge、replace、delete、automatic renameを行わない。
- [x] intentional failureの全caseで既存packageと個別保存出力が不変である。

### 12.2 transaction / recovery

- [x] 成功前に承認済みfinal directory名でpartial outputを公開しない。
- [x] VMD / WAV / reportの各write / validation failureで後続phaseを停止し、finalを作らない。
- [x] source identity change、stale fingerprint、invalid authorization、commit failureでcommitしない。
- [x] pre-commit failure / cancelではowned stagingだけをcleanupする。
- [x] staging差替えをphase境界・commit前に検出してfail closedとし、reparse targetをcleanupで辿らない。path-based writerのopen前を含む任意時点の差替え完全防止はB6の保証外とする。
- [x] cleanup failureはprimary resultと分離して`partial_output_cleanup_failed`を返す。
- [x] cleanup例外とowned staging取得後の予期しない通常例外がworker terminalを失わせず、primary resultを保持したfailureへ収束し、successへ変換されない。

### 12.3 cancel / commit / GUI lifecycle

- [x] commit前cancelはrenameを禁止する。
- [x] commit開始後cancelはrename結果を上書きしない。
- [x] commit成功時はfinalを保持し`committed=True`のsuccess terminalを返す。
- [x] commit失敗と後着cancelの競合でfailureをcancelへ上書きしない。
- [x] Busyはterminal / cleanup結果受理まで維持される。
- [x] closeはterminal前にwindowを破棄せず、window破棄後にfinal commitが発生しない。
- [x] worker参照、active binding、UiState delivery stateのいずれかだけが残る不整合でもgeneric closeへ流れず、delivery専用のauthorization拒否またはfailed reconciliation後だけwindowを破棄する。
- [x] late / duplicate terminalはcurrent UI stateを変更しない。
- [x] cleanup failureはsafe warningへ投影し、raw exceptionやstaging absolute pathを表示しない。

### 12.4 identity / compatibility / scope

- [x] commit guardはcurrent semantic fingerprintを使い、`projection_generation`だけの差で拒否しない。
- [x] worker threadは可変GUI stateを直接読まない。
- [x] B1〜B5のpublic contract、VMD形式、MMD WAV仕様、report identity、individual save historyを維持する。
- [x] runtime data、dependency、build、package、licenseに差分がない。
- [x] 対象test、`compileall`、`git diff --check`がprocess exit code 0である。
- [x] manual GUI結果は実施者と範囲を限定して記録する。
- [x] Windows 11のactual junction / reparse collisionとpermission deniedまたはsharing violationを各1件実行し、skipなしで記録する。
- [x] 実MMD確認をMS26、package / release readinessをMS27へ延期したまま維持する。

## 13. リスクと対策

| ID | リスク | 重要度 | 対策 |
| --- | --- | --- | --- |
| MS25-B6-R1 | `Path.exists()`がbroken symlinkを不存在と誤認する | P1候補 | `os.lstat()`の`FileNotFoundError`だけを不存在とする |
| MS25-B6-R2 | TOCTOUで既存destinationを置換する | P1候補 | 最終再検査 + Windows no-clobber rename。削除後retry禁止 |
| MS25-B6-R3 | POSIXとWindowsのrename意味差を見落とす | P2候補 | product targetのWindows actual filesystem testを必須化し、他OS結果を代用しない |
| MS25-B6-R4 | stagingがjunctionへ差し替えられ、外部treeへ書込み・cleanupする | P1候補 | owned identity再確認、reparse拒否、cleanupでtarget非追跡 |
| MS25-B6-R5 | cleanup exceptionでterminal callbackが消失しBusy / closeが停止する | P1候補 | cleanup例外を結果化し、one-shot terminalへ必ず収束 |
| MS25-B6-R6 | cleanup failureがprimary failure / cancelを上書きする | P2候補 | primary fields不変 + cleanup status分離 |
| MS25-B6-R7 | commit後cancelで成功済みfinalを削除する | P1候補 | commit lockと`commit_started`以後のcancel拒否 |
| MS25-B6-R8 | commit failureを後着cancelがcancelledへ変換する | P2候補 | rename結果を正本とし、raw cancel flagでterminal再分類しない |
| MS25-B6-R9 | `projection_generation`差で正当なcommitを自己失効する | P1候補 | semantic fingerprintとUI callback identityを分離 |
| MS25-B6-R10 | OS errorをraw message文字列で分類しlocale依存になる | P2候補 | exception type / errno / winerrorのpure mappingとparameterized test |
| MS25-B6-R11 | actual junction / locked testがskipされても通過扱いにする | P2候補 | skip理由を記録し、B6を条件付き・未完了としてB7へ持ち越す |
| MS25-B6-R12 | B6でGUIやtransaction APIを広範再設計する | P2候補 | existing DTO / linearization / bindingを維持し、差分監査する |
| MS25-B6-R13 | cleanup warningにstaging pathやraw exceptionを表示する | P2候補 | safe fixed messageのみ。詳細はinternal diagnostics |
| MS25-B6-R14 | fault testのteardownがjunction targetを再帰削除する | P1候補 | temporary targetとentryを分離し、entry自身だけを明示削除 |

### 13.1 草案自己監査

| 分類 | 確認結果 |
| --- | --- |
| P1 | 未解消なし。existing output保護、TOCTOU、staging差替え、cleanup terminal、cancel / commit / closeを受入条件へ対応付けた |
| P2 | Sol High指摘6件と、再チェックで検出した§7.3 / §11.6の回帰gate不一致1件を反映済み。OS error分類、実装・検証境界、owned staging例外、保証範囲、Windows skip時の未完了条件、状態不整合時のclose、report save flow回帰を固定した |
| P3 | Sol High指摘1件を反映済み。B6必須test 3ファイル、直接回帰、compileall、diff check、B7 full suiteの境界を固定した |

メイン側の再照合では、現行`delivery_package.py`の既存lstat / rename / cancel / terminal契約をB6で無目的に再実装しないこと、現行`audio_worker.py`のownership後fallbackがstaging情報を失う経路をhardening対象とすること、現行`app_controller.py`のsafe messageと`is_delivery_active()`の完全一致依存を補修確認対象とすることを確認した。さらに、§7.3に列挙済みだった`tests/test_ms20_b6_report_save_flow.py`を§11.6項目3へ追加し、Block Breakdown・回帰対象一覧・必須実行順を一致させた。P1 / P2 / P3の未解消事項はない。

自己監査では、Block BreakdownのB6責務、現行B2 / B3 / B5実装、Pipeline / Error / GUI / VMD正文仕様へ再照合した。実装時に結果を大きく変える判断不能事項は確認されていない。

### 13.2 2026-09-04実装前チェック補正記録

- P2として確認したB6専用testの担当・ファイル名不一致は、Block Breakdown §7、§11.4、§15.2をB6計画書の3ファイルへ統一し、B6をtest作成・B7をfull cross-boundary回帰担当と明記して解消した。
- P3として確認したMS25 routingの未同期は、MS25-B5 / B6計画書のIndex導線、B5のcommit済み状態、B6計画書の現行状態へ反映した。
- P3として確認した`output_path_inspection_failed`のError code一覧欠落は、Error Handling仕様へ既存codeの意味を追加し、B6のsafe message対象にも明記して解消した。
- 補正後のP1 / P2 / P3未解消事項はない。これは実装前チェック時点の記録であり、実装後の状態と確認結果は§11.8および§12へ反映した。

### 13.3 2026-09-04 B6再チェックP2補正

- B6の`PermissionError`分類（`output_permission_denied`）と、既存B2 commit回帰が保持する`delivery_commit_failed`期待値の不一致を確認した。
- B6の詳細分類契約を採用し、既存B2回帰の期待値をB6実装時に`output_permission_denied`へ同期する例外を§7.3へ明記した。分類対象外のrename I/Oで`delivery_commit_failed`を維持する回帰は、B6専用failure recovery testへ追加する。
- これはテストを弱める変更ではなく、Error Handling仕様とB6分類契約を既存回帰へ同期する変更である。production code、B6専用test、GUI変更は本補正では実施していない。
- 本補正後、計画上のP1 / P2 / P3未解消事項はない。B6実装時に、上記の既存B2期待値同期と分類対象外I/Oの回帰追加を実施・検証する。

## 14. Codex実装時の注意

- 実装開始前にlive Gitとuser-owned差分を確認する。
- コマンドは一つずつ実行する。
- B6は既存transactionのhardeningであり、別orchestratorや別terminal DTOを増やさない。
- final destinationを削除、空化、merge、replaceしてはならない。
- cleanupはexact owned staging以外へ広げない。
- `os.replace()`をfinal directory commitに使用しない。
- `Path.exists()`をbroken symlink / reparse collisionの唯一判定にしない。
- worker task完了後のcancel flagだけでcommitted resultをcancelへ変換しない。
- `projection_generation`をsemantic fingerprintへ追加しない。
- raw exception messageからOS error codeを推測しない。
- fault injectionのためのproduction debug option、環境変数、hidden settingを追加しない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読取り・変更・stageしない。
- testを弱めたりskipへ変えてfailureを回避しない。
- manual GUIを実行していない場合は未実施と報告する。
- actual reparse / locked testがskipなら、その保証を未検証として報告し、B6完了を宣言しない。
- stage、commit、push、merge、tag、releaseは別の明示承認まで行わない。

実装完了報告では、確認ファイル、変更ファイル、fault matrix、実行testとexit code、actual Windows caseの実施 / skip、manual GUI結果、仕様逸脱、残課題、B7 / MS26 / MS27への引き継ぎを分けて記載する。
