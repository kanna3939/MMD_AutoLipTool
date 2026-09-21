# MS25-B5 GUI・worker・状態統合 Implementation Plan

## 1. 文書情報

- 文書名: MS25-B5 GUI・worker・状態統合 Implementation Plan
- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B5
- 作成日: 2026-09-02
- 対象ブランチ: `feature/MS25-implementation`
- 計画作成時HEAD: `01b4d4f Implement MS25-B4 diagnostic report identity`
- 状態: B5実装済み・自動検証済み。ユーザー報告の手動GUI確認も通過済み。B5 production code、test code、GUI変更は`bb9c60d Complete MS25-B5 delivery package GUI integration`としてcommit済み
- 直接依存:
  - MS25-B1: `DeliveryCurrentState`、`DeliveryStartContext`、WARNING / ERROR start gate、semantic commit fingerprint evaluator
  - MS25-B2: destination validation、staging、pre-commit authorization、cancel / commit線形化、`DeliveryTerminalResult`
  - MS25-B3: `build_delivery_artifact_operations()`とVMD / MMD用WAV / reportのgenerate-and-validate operation
  - MS25-B4: report identity必須化とsafe `DiagnosticReportError`契約
- 計画作成時の変更権限: `docs/Implementation_Plan/MS25-B5_Implementation_Plan.md`の新規作成だけ
- 計画作成時の変更禁止: production code、test code、GUI、設定、runtime user data、依存関係、README、`readme_mmdautolip.txt`、Index、Roadmap、stage、commit、push
- ユーザー判断待ち: なし。§6で採用するmenu導線、destination dialog、session-only parent、delivery専用worker、UI handoff timeoutは、現行資料と実装からB5内の最小構成として確定する
- 実装結果（2026-09-03）: `ファイル > MMD一括出力...`、destination dialog、delivery専用worker、Busy / cancel / close lifecycle、pre-commit UI bridgeを実装した。false `delivery_busy` を起こすworker state / reference不整合をP3修正した。
- 自動検証結果: B5および関連worker / GUI回帰 `29 passed`、全pytest `1015 passed, 4 skipped`、いずれもprocess exit code `0`。`compileall -q src tests`と`git diff --check`もprocess exit code `0`。
- 手動GUI確認: ユーザーから、提示したB5手動GUIテスト通過の報告を受領した。これはユーザー確認として記録し、Codex自身のGUI実行結果とは扱わない。
- 未検証・後続: B6のWindows fault matrix、MS25-B7のfull cross-boundary regression / closeout、実MMD、Python 3.11 / 3.12、PyInstaller onefile、package / release確認

### 1.1 正本と現行状態

本計画は、次の優先順位で現行状態を判断する。

1. live Git状態と現行production code / test
2. `docs/MS20_and_Beyond_Roadmap.md` §12
3. `docs/Implementation_Plan/MS25_Block_Breakdown.md`のMS25-B5契約
4. MS25-B1〜B4 Implementation Planと実装済みcode / test
5. Pipeline / Error / GUI正文仕様
6. README / `readme_mmdautolip.txt`の既存個別保存説明

`docs/MS20_and_Beyond_Index.md`や過去planに残る計画時点の未実装表現は、live Git状態のB1〜B5実装済み事実を上書きしない。計画作成時には関連文書を同期しなかったが、B5実装後の現在状態としてMS25関連文書へ結果を反映する。

### 1.2 監査反映

Sol Highの独立監査で、P1なし、P2 3件、P3 2件を確認した。メインエージェントは、worker errorを含むsingle completion gateとB2-owned cleanup済みterminal、post-dialog最終candidateからのcontext固定、pureなcommit snapshot、WARNING後のB1再gate、個別保存の重点回帰と双方向WARNING回帰を本計画へ反映した。メイン側の再チェックで、各指摘に対応する実装方針・テスト・受入条件を確認し、未解決のP1/P2/P3はない。

## 2. 背景

MS25-B1〜B4により、GUI非依存のdelivery package契約は実装済みである。

- `MainFrame.capture_current_delivery_state()`は、同一captureのeffective plan、diagnostics snapshot、source audio identity、FFmpeg path、writer parameters、resolved ordered morph names、start fingerprintをB1 gateへ渡す。
- `build_delivery_start_context()`は、`ready`な`DeliveryCurrentState`へparent directory、folder name、timezone-aware report timestampを束ねる。
- `validate_delivery_destination()`は、Windows名・path長・既存entry collisionをfilesystem mutation前に検証する。
- `orchestrate_delivery_package()`は、同一親directoryのstagingへ3成果物を生成し、`awaiting_commit_guard`でjob IDとstart fingerprintにbindingされたauthorizationを要求し、Windows no-clobber renameをcommit線形化点として一つの`DeliveryTerminalResult`を返す。
- `DeliveryCancelToken.request_cancel()`はcommit開始前だけcancelを受理し、commit開始後は`False`を返す。成功済みfinalをcleanup対象へ戻さない。
- `build_delivery_artifact_operations()`は、B1開始contextからVMD、元入力音声からMMD用WAV、同じsnapshot / timestampからreportを生成・検証する。
- B4 report formatterは、preset、profile、morph-name set / ordered names、Whisper selected / active / loaded / analysis identityを省略せず記録する。

B5実装前のGUI / workerには次のB5未接続境界があった。

- `AudioWorkerKind`は`PROBE / ANALYSIS_WAV / MMD_WAV`だけで、delivery専用kindがない。
- `AudioWorker.run()`はtaskが正常returnした後でもcancel flagが立っていればcancel callbackへ変換する。このままdeliveryへ使うと、commit済みsuccessをcancel表示へ上書きできる。
- `AppController`にはdelivery action、active delivery worker、job-bound commit authorization、delivery terminal projectionがない。
- `MainFrame`には一括出力menu、親directoryとfolder名を同時に確認するdialog、delivery action stateがない。
- 現行`MainFrame._on_close()`と`AppController.request_exit()`は、audio workerへcancelを要求した後、terminal / cleanupを待たずwindowを破棄する。これはdeliveryのfinal commitとcloseを競合させる。
- `capture_current_delivery_state()`はBusy中を開始不可として正しく拒否するため、delivery workerがBusyを維持したまま行うpre-commit再評価にはそのまま使えない。
- 既存の個別VMD、個別MMD用WAV、standalone reportはそれぞれ独立したdialogと保存履歴を持つ。一括出力がこれらのpath historyやINI保存を流用・更新してはならない。

B5は、B1〜B4のcore契約を変更せず、上記のGUI / worker / lifecycle seamを接続するBlockである。transaction failure matrixの追加hardeningはB6へ残し、READMEと正文仕様の同期はB5実装・検証後に実施した。

## 3. 目的

1. `ファイル`menuからMMD一括出力を起動できるようにする。
2. 親directoryと編集可能なfolder名を指定し、B1既定名`<audio_stem>_MMD`を提示する。
3. ERROR / WARNING、destination dialog、post-dialog recapture、300秒超確認、Busy、worker開始を固定順で接続する。
4. `AudioWorkerKind.DELIVERY_PACKAGE`とdelivery専用workerを追加し、B2 terminal resultをfilesystem結果の唯一の正本として扱う。
5. `awaiting_commit_guard`でworker threadをGUI stateから隔離し、UI threadがcurrent fingerprintとactive jobを確認した場合だけauthorizationを返す。
6. success / failure / cancel / cleanup failureをBusy終了まで一貫して投影し、late / duplicate resultを破棄する。
7. close要求時にterminal / cleanup完了までwindow破棄を延期し、commit済みfinalをcancel cleanupしない。
8. 個別保存導線、個別保存履歴、WARNING確認identity、runtime設定を既存契約どおり維持する。

B5完了はWindows failure matrixのcloseout、MS25-B7のfull cross-boundary regression、実MMD確認、package / release readinessの完了を意味しない。READMEと正文仕様の同期は実装・検証後の今回の文書更新で反映済みである。

## 4. In Scope

- `ファイル > MMD一括出力...`menu action
- 親directoryとfolder名を一つのmodal dialogで指定するwxPython UI
- folder名のB1既定値`<audio_stem>_MMD`とUnicode保持
- parent browse用`wx.DirDialog`、folder name編集用`wx.TextCtrl`
- session-onlyのbatch parent directory保持
- controllerによるFFmpeg解決とB1 start gate呼出し
- diagnostics ERRORのdialog前拒否
- diagnostics WARNINGの既存fingerprint単位確認とshared confirmation identity
- destination dialog終了後のcurrent-state recapture / gate再評価
- source / artifact identity変化時のdestination選択やり直し
- B2 destination validationによるinvalid name / path / collisionのdialog再入力
- 300秒超入力の、destination確定後・Busy / worker開始前の一回確認
- `AudioWorkerKind.DELIVERY_PACKAGE`
- delivery専用`DeliveryPackageWorker`と`DeliveryCancelToken`
- delivery workerのsingle terminal callback
- Busy開始、競合action lock、cancel、success / failure / cancel投影
- active `(job_id, worker_kind, start_projection_generation)` binding
- `wx.CallAfter`とthread-safe replyを使うpre-commit UI bridge
- UI thread上のnon-storing current diagnostics snapshot再構築
- B1 `evaluate_delivery_commit_fingerprint()`とB2 `DeliveryCommitAuthorization`の接続
- commit guard timeout時のfail-closed cleanup
- late / duplicate / invalid job / invalid kind / invalid projection result discard
- commit前close cancel、commit開始後close wait、terminal後deferred destroy
- individual VMD / MMD WAV / report path history非変更
- B5専用unit / wx integration testと直接関連する既存回帰
- B5 visible GUIの手動確認項目定義

## 5. Out of Scope

- B1のartifact naming、source identity、start gate、fingerprint schema / payloadの変更
- B2のWindows validation、staging、no-clobber rename、terminal result、cancel線形化の変更
- B3のVMD / WAV / report writer・validator変更
- B4のreport field、formatter、safe error message、exception chain変更
- `OutputDiagnosticsSnapshot`、`DeliveryStartContext`、`DeliveryTerminalResult`へのfield追加
- final directoryへの直接write、merge、replace、copy fallback
- package専用manifest、hash、ZIP、session file、MMD自動起動
- B6のactual reparse / junction、locked / readonly、cleanup race、OS shutdown横断hardening
- README、`readme_mmdautolip.txt`、Pipeline / GUI / Error / VMD仕様、Index、Roadmapの同期（B5実装後に完了。残る差分はB7で監査）
- standalone reportのdetail / copy UI
- progress percentage、経過時間timer、worker開始後の長時間再確認
- 新規INI key、batch parentの永続化、設定migration
- 個別保存dialog / writer / overwrite policyの変更
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接読書き、コピー、stage
- dependency、PyInstaller spec、build script、license文書の変更
- Qt / PySide6
- 実MMD確認、MS26 / MS27作業
- stage、commit、merge、push、tag、release

## 6. 前提条件

### 6.1 B1〜B4契約を入力として使用する

B5は次を再実装しない。

- 命名: `DeliveryCurrentState.artifact_names`
- 開始可否: `evaluate_delivery_start_gate()`
- context: `build_delivery_start_context()`
- destination validation: `validate_delivery_destination()`
- semantic commit判定: `evaluate_delivery_commit_fingerprint()`
- orchestration: `orchestrate_delivery_package()`
- artifact operations: `build_delivery_artifact_operations()`
- terminal / cleanup正本: `DeliveryTerminalResult`

B5でcore API不足が判明した場合、GUI都合でB1〜B4の意味を変更しない。additive helperが本当に必要な場合はB5 planのscopeへ戻って再確認する。

### 6.2 起動導線とdestination dialog

起動導線は`ファイル > MMD一括出力...`の一つとする。既存top panelは既に主要buttonが多く、Roadmap / Block Breakdownはbuttonを必須にしていないため、B5では新しいtoolbar buttonやiconを追加しない。

`MainFrame`内に`DeliveryDestinationDialog(wx.Dialog)`を追加し、次を同時に表示する。

- 親directoryのread-only表示
- `参照...`button。`wx.DirDialog`で親directoryを選ぶ
- folder名のeditable `wx.TextCtrl`
- final path preview
- `出力` / `キャンセル`button

dialogはdirectoryやfileを作らない。UI側で文字列をsanitize、短縮、ASCII化、suffix付与しない。authoritative validationはB2 `validate_delivery_destination()`とし、invalid / collision時はsafe messageを表示して同じparent / folder入力を保ったまま再入力させる。

### 6.3 既定parentとsession-only保持

初回のparent既定値は、現行MMD用WAV導出規則を再利用し、次の順とする。

1. `UiState.last_mmd_wav_export_dir`
2. `UiState.last_vmd_output_dir`
3. original source audioの親directory

一度dialogで確定したparentは`AppController._delivery_parent_directory_session`へsession-onlyで保持し、同一sessionの次回起動時は最優先にする。folder名は毎回B1の`default_folder_name`から開始し、前回のcustom folder名を永続化・自動再利用しない。

session parentは`UiState`の個別保存history、SettingsStore、INIへ書かない。dialog cancel、worker failure、worker cancel後もsession内では選択済みparentを再利用してよいが、application再起動後には復元しない。

### 6.4 WARNING / ERROR / 長時間確認

順序は固定する。

1. Busyでないことを確認する。
2. FFmpegを解決し、`capture_current_delivery_state()`を呼ぶ。
3. `blocked`ならdestination dialogを開かない。
4. `warning_confirmation_required`ならcandidate snapshotを既存`confirm_vmd_save_warnings()`へ渡す。
5. WARNING拒否時はconfirmation field、dialog、Busy、job ID、worker、filesystemを変更しない。
6. WARNING承認時は既存`confirmed_warning_save_state_fingerprint`へcandidate fingerprintを保存し、同じ共有identityを個別VMD保存でも再利用する。
7. `ready`になった後だけdestination dialogを開く。
8. dialog終了後に同じFFmpeg pathでcurrent stateを再captureする。
9. post-dialog captureが`warning_confirmation_required`なら、保存済みfingerprintを使って既存確認を行い、承認後にB1 capture / gateをもう一度実行して、新しい`ready` candidateを取得する。candidate DTOを直接`ready`へ変更しない。拒否時はworkerを開始しない。
10. source identity、audio stem、artifact namesがdialog前candidateから変化した場合、古いdestination選択を流用せず、最新defaultでdialog前gateへ戻る。
11. post-dialogの最終`ready` candidate、destination入力、duration、FFmpeg path、report timestampから`DeliveryStartContext`を一度だけ構築し、同じimmutable contextをdestination validation、artifact operations、B2 orchestrationへ渡す。invalid / collisionなら同じ入力を保持してdialogへ戻る。
12. `duration_sec > 300.0`の場合だけ、最終candidateの固定durationを使って既存`_confirm_long_audio_if_needed()`を一度呼ぶ。
13. 長時間確認拒否時はBusy、job、worker、stagingを開始しない。
14. 承認後ただちにjobを登録し、Busyへ遷移してworkerを開始する。

300秒ちょうどは現行`duration_sec <= threshold`契約に従い確認不要とする。経過時間timer、worker開始後の再確認、強制timeoutは追加しない。

### 6.5 delivery専用worker

既存`AudioWorker`は変更せず、同じ`src/gui_wx/audio_worker.py`へ`DeliveryPackageWorker`を追加する。

```python
class DeliveryPackageWorker(threading.Thread):
    def __init__(
        self,
        *,
        audio_job_id: int,
        projection_generation: int,
        task: Callable[[DeliveryCancelToken], DeliveryTerminalResult],
        terminal_callback: Callable[
            [int, AudioWorkerKind, int, DeliveryTerminalResult], None
        ],
        error_callback: Callable[
            [int, AudioWorkerKind, int, Exception], None
        ],
        call_after: Callable[..., None] = wx.CallAfter,
    ): ...

    def cancel(self) -> bool: ...
```

- `kind`は常に`AudioWorkerKind.DELIVERY_PACKAGE`とする。
- worker自身が`DeliveryCancelToken`を所有し、B2 orchestrationへ同じinstanceを渡す。
- task正常return後はcancel flagで結果を再分類せず、必ず`DeliveryTerminalResult`をsingle terminal callbackへ渡す。
- `cancel()`は`DeliveryCancelToken.request_cancel()`のboolを返す。
- terminal callbackとerror callbackは、worker内のone-shot `DeliveryCompletionGate`を共有する。最初にcompletion claimを取得した経路だけがcontrollerへ通知し、後続のterminal / error / duplicate callbackは捨てる。error callbackはterminalの別経路ではない。
- B2 orchestrationの開始前に発生したworker harness failureだけをerror callbackへ渡し、controllerはstagingを所有していないfailed `DeliveryTerminalResult`へ変換して同じterminal受理経路へ渡す。B2 ownership開始後のartifact / validation / commit / cancelおよび予期された例外は、B2がcleanup済みの`DeliveryTerminalResult`へ変換して返す。ownership開始後に例外がworker境界から漏れる場合は、raw errorをterminalとして投影せず、B2-owned cleanupを完了させたfailed terminalへ変換する境界を置く。
- callbackは必ず`wx.CallAfter`経由とし、worker threadからwx control、`MainFrame`、`UiState`を読まない。

`AudioWorkerKind`へ`DELIVERY_PACKAGE = "delivery_package"`を追加する。commit開始後のcancel拒否を表示するため、delivery専用に`AudioWorkerStatus.FINALIZING = "finalizing"`をadditiveに追加し、active状態として扱う。既存3 kindの遷移は変更しない。

### 6.6 pre-commit authorization bridge

B2の同期`pre_commit_guard(request, cancel_token)`をworker threadから呼べるよう、controllerにthread-safe bridgeを追加する。

1. worker threadでone-shot reply holderと`threading.Event`を作る。
2. `wx.CallAfter()`でUI thread callbackを予約する。
3. worker threadはeventを短周期で待ち、cancel token、reply、timeoutを確認する。
4. UI thread callbackはactive `(job_id, DELIVERY_PACKAGE, projection_generation)`、close pending、cancel、request bindingを検証する。
5. `MainFrame.build_current_delivery_commit_snapshot()`でcurrent semantic stateをnon-storing再構築する。
6. `evaluate_delivery_commit_fingerprint(start_context, current_snapshot)`を呼ぶ。
7. match時だけ同じjob ID / start fingerprintをechoした`decision="authorized"`を返す。
8. fingerprint mismatch / saveability failureは`stale`、active job / kind / projection mismatchは`invalid_job`、cancelは`cancelled`、close pendingは`closing`を返す。
9. replyはlockで一回だけ確定し、timeout / cancel後に到着したlate UI callbackは上書きしない。

UI callback handoff timeoutは`DELIVERY_COMMIT_GUARD_UI_TIMEOUT_SEC = 30.0`とする。通常のUI callbackは即時処理であり、30秒応答しない状態はGUI lifecycle異常とみなす。timeoutではbridgeが例外を返し、B2既存`delivery_commit_guard_failed` terminalとowned staging cleanupへfail closedする。timeoutをcommit許可へ変換しない。

### 6.7 Busy中のcurrent snapshot再構築

pre-commit guardは、delivery自身が設定したBusyを理由に自己拒否してはならない。そのため、`capture_current_delivery_state()`の開始gateを緩めず、`MainFrame`へB5専用のprivate / internal methodを追加する。

```python
def build_current_delivery_commit_snapshot(
    self,
) -> OutputDiagnosticsSnapshot | None:
    ...
```

- UI thread上でだけ呼ぶ。
- history初期化、cache更新、failure state更新を行わないpure/read-only経路でcurrent `UiSyncContext`を一度構築する。現行の可変な`_build_current_ui_sync_context()`しか利用できない場合はauthorizationをfail closedにする。
- `prepare_current_effective_output()`とmorph-name resolutionを一度ずつ行う。
- existing diagnostics builderと同じ入力からsnapshotを作る。
- `_diagnostics_projection_generation`を増分しない。
- `UiState.current_output_diagnostics_snapshot`へ保存しない。
- `confirmed_warning_save_state_fingerprint`、failure、history、selection、Previewを変更しない。
- snapshotの`application_busy=True`はそのまま記録するが、Busy自体をfingerprintへ混入させない既存契約を維持する。

commit snapshotの成功・失敗を問わず、`UiState`、adjustment history、stored diagnostics snapshot、projection generation、WARNING fingerprintを変更しない。non-storing builderは、保存用projectionの副作用を経由しないことを専用testで確認する。

実装時は既存`build_and_store_output_diagnostics_snapshot()`のpublic behaviorを維持したまま、共通private builderへ抽出する。通常projectionは従来どおりgenerationを増分してstoreし、commit snapshotだけをnon-storingにする。

### 6.8 active projection bindingとlate result

worker開始時に、controllerは次を一つのactive bindingとして保持する。

```text
(audio_job_id, AudioWorkerKind.DELIVERY_PACKAGE,
 start_context.current_state.projection_generation)
```

worker callbackは同じ3値を返す。terminal受理時は、current audio job ID、worker state job ID / kind、active binding、callback projection generation、未terminalであることをすべて確認する。

このprojection generationはcallbackを開始jobへbindingするUI投影tokenであり、pre-commit authorizationのsemantic条件には使わない。Busy開始時の再描画やnon-storing commit snapshotとcurrent stored snapshotのgeneration差だけでcommitを拒否しない。

late / duplicate callbackは、Busy、Status、snapshot、fingerprint、WARNING confirmation、path history、final filesystem resultを変更しない。

### 6.9 cancelとFINALIZING

- commit開始前に`DeliveryPackageWorker.cancel()`が`True`を返した場合、worker stateを`CANCELLING`へし、Busyを維持する。
- commit開始後に`False`を返した場合、worker stateを`FINALIZING`へし、「出力先を確定中です。完了を待っています。」と表示する。cancelledとは表示しない。
- `FINALIZING`中はcancel buttonを無効化するが、Busyと他action lockは維持する。
- cancel requestだけでBusyを解除しない。B2 terminal / cleanup完了を受理したcallbackだけが解除する。
- terminalが`committed=True`なら、現在のworker stateが`CANCELLING`または`FINALIZING`でもsuccessとして投影する。

### 6.10 window close

delivery active時のcloseは既存即時destroy経路へ入れない。

- `MainFrame._on_close()`はdelivery activeをgeneric audio / analysisより先に判定する。
- 初回closeで、処理を中止または確定完了まで待って終了する旨を確認する。
- No / dialog closeではeventをvetoし、stateを変更しない。
- Yesではeventをvetoし、controllerへ`delivery_close_pending`を設定してcancelを要求する。
- cancelが受理された場合は`CANCELLING`でterminal / cleanupを待つ。
- commit開始済みでcancelが拒否された場合は`FINALIZING`でrename terminalを待つ。
- close pending中の重複closeは再確認dialogを出さずvetoする。
- `_is_shutting_down`はdelivery terminal受理前に`True`へせず、terminal callbackをlate resultとして捨てない。
- terminal受理後にactive delivery bindingをclearし、既存`request_exit()`のtimer停止、settings flush、他worker shutdown、`view.Destroy()`へ進む。
- close pending中はsuccessと通常のfailure modalを新規表示しない。ただし`cleanup_status == "partial_output_cleanup_failed"`なら、残存一時出力を黙って見落とさないようsafe cleanup warningを1回表示し、利用者の確認後にwindowを破棄する。staging pathは表示せず、詳細表示・残存staging recovery hardeningはB6で追加確認する。B5でもcleanup完了前に破棄しない。

### 6.11 terminal projectionとsafe message

terminal callbackはB2 resultを次のように投影する。

| terminal | UI status | modal | Busy解除 |
| --- | --- | --- | --- |
| `committed=True`, success | `MMD一括出力成功` | 通常はなし | terminal受理後 |
| cancelled, cleanup normal | `MMD一括出力をキャンセルしました` | なし | cleanup後 |
| failed | safe error summary | error dialog | cleanup後 |
| primary cancel / failure + cleanup failure | primary summary + 一時出力cleanup警告 | error dialog | terminal受理後 |
| late / duplicate / binding mismatch | 変更なし | なし | 変更なし |

通常表示はallowlist化したerror codeから構築し、raw exception、traceback、stderr全文、opaque staging pathを連結しない。代表写像は次とする。

- `output_destination_collision`: 同名の出力先があるため、別のfolder名で再実行する
- `output_path_invalid` / `output_path_too_long`: parent / folder名を確認する
- `source_audio_changed`: 音声が処理中に変更されたため、読み込み直して再実行する
- `delivery_state_stale`: 作業状態が変わったため確定しなかった。現在状態を確認して再実行する
- VMD / WAV / report write / validation failure: 該当成果物を生成・検証できなかった
- `delivery_commit_guard_failed` / `delivery_commit_failed`: 出力を安全に確定できなかった
- 未知code: 一括出力を完了できなかった

success時は`final_path`をstatus detailまたは利用者が要求したfinal destinationとして表示してよい。staging pathは通常表示しない。

### 6.12 個別保存との共存

B5 actionは次を更新しない。

- `last_vmd_output_dir`
- `last_mmd_wav_export_dir`
- `last_mmd_wav_output_path`
- standalone reportのdefault directory契約
- recent files
- generation / profile / Whisper settings
- SettingsStore / INI

共有してよいstateは、B1で確定済みの`confirmed_warning_save_state_fingerprint`だけである。一括出力で同fingerprintのWARNINGを承認した後、個別VMD保存が同じ確認を再要求しないことは既存契約として維持する。

一括出力のERROR block中もstandalone report menuは、元音声がありBusyでなければ従来どおり利用できる。一括出力workerのBusy中だけは競合操作として一時lockする。

## 7. 対象ファイル

### 7.1 B5実装で変更するproduction code候補

| 種別 | ファイル | B5責務 |
| --- | --- | --- |
| 既存変更 | `src/gui_wx/worker_state.py` | `DELIVERY_PACKAGE` kind、delivery用`FINALIZING` status、active判定 |
| 既存変更 | `src/gui_wx/audio_worker.py` | `DeliveryPackageWorker`、core cancel token、single terminal callback、commit後result非再分類 |
| 既存変更 | `src/gui_wx/app_controller.py` | start flow、session parent、delivery worker lifecycle、commit guard bridge、terminal projection、cancel / deferred close |
| 既存変更 | `src/gui_wx/main_frame.py` | File menu action、destination dialog、action state、non-storing commit snapshot、delivery close分岐 |
| 既存変更 | `src/gui_wx/ui_state.py` | `FINALIZING`を含むactive派生判定、cancel可否の派生判定 |

`src/gui_wx/ui_state.py`の保存field、WARNING confirmation、個別保存historyは変更しない。一方、現行`audio_worker_active`は`RUNNING / CANCELLING`を直接列挙しているため、`FINALIZING`をactiveとしてBusy / closeへ反映する最小変更が必要である。`audio_worker_active`を`AudioWorkerState.is_active`へ委譲し、`FINALIZING`だけcancel不可とする`audio_worker_cancel_available`相当のderived propertyを追加する。新しい永続fieldやsession historyは追加しない。`right_pane.py`は変更しない。

### 7.2 B5で新規作成するtest候補

| ファイル | 主な証拠 |
| --- | --- |
| `tests/test_ms25_b5_delivery_worker.py` | delivery kind、single terminal、late cancel後committed success、uncaught error、cancel bool、projection callback binding |
| `tests/test_ms25_b5_delivery_gui.py` | gate順序、dialog、WARNING、long audio、Busy、authorization、late result、terminal、individual history、deferred close |

### 7.3 回帰確認のみ。原則変更しない

- `src/core/delivery_package.py`
- `src/core/delivery_artifacts.py`
- `src/core/diagnostic_report.py`
- `src/vmd_writer/validator.py`
- `tests/test_ms25_b1_delivery_contract.py`
- `tests/test_ms25_b1_current_state_gate.py`
- `tests/test_ms25_b2_windows_paths.py`
- `tests/test_ms25_b2_delivery_orchestration.py`
- `tests/test_ms25_b2_delivery_commit.py`
- `tests/test_ms25_b3_delivery_artifacts.py`
- `tests/test_ms25_b3_vmd_readback_validation.py`
- `tests/test_ms25_b4_delivery_report_identity.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms17_b8_long_audio_confirmation.py`
- `tests/test_ms17_b8_audio_worker_state.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_wx_ms14_b5_export.py`

### 7.4 B5では変更しない文書・設定

- `README.md`
- `readme_mmdautolip.txt`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- Pipeline / Error / GUI / VMD正文仕様
- `pyproject.toml`
- `MMD_AutoLipTool.spec`
- `build.ps1`
- runtime `presets.json` / `profiles.json` / `MMD_AutoLipTool.ini`

## 8. 実装方針

### 8.1 controllerをorchestration ownerにする

`MainFrame`はviewとUI-thread snapshot構築を担当し、`AppController`がaction順序、job、worker、authorization、terminal、closeを所有する。workerはcore orchestrationだけを実行し、GUI stateを参照しない。

```text
MainFrame menu event
  -> AppController.request_export_delivery_package()
       -> locate FFmpeg
       -> B1 pre-dialog capture / WARNING gate
       -> MainFrame destination dialog
       -> B1 post-dialog recapture / WARNING recheck
       -> build context / B2 destination validation
       -> long-audio confirmation
       -> register active binding / Busy
       -> DeliveryPackageWorker
            -> B2 orchestration + B3 operations
            -> pre-commit bridge
                 -> wx.CallAfter(UI thread)
                 -> non-storing current snapshot
                 -> B1 commit evaluator
                 -> B2 authorization
            -> one DeliveryTerminalResult
       -> AppController terminal projection / deferred close
```

### 8.2 dialog loopはfilesystem mutation前に完結する

dialog cancel、WARNING拒否、invalid destination、collision、long-audio拒否ではjob IDを発行せず、Busyを設定せず、workerとstagingを開始しない。B2 orchestrationはworker内でdestinationを再検査し、dialog時点の検査をTOCTOU排他とみなさない。

### 8.3 active workerは一つに限定する

既存Busyとaudio job IDを共有し、delivery専用の第二並列job namespaceを作らない。start直前に`next_audio_job_id()`を一度だけ呼び、`AudioWorkerState(kind=DELIVERY_PACKAGE, RUNNING)`を設定する。

`_audio_worker`と`_delivery_worker`は別fieldにし、generic audio workerのtask / callback意味を変更しない。同時activeはBusy gateで禁止し、矛盾が検出された場合はdelivery開始をfail closedにする。

### 8.4 projectionとcommit identityを分離する

- start fingerprint: filesystem commitのsemantic identity
- job ID / worker kind / start projection generation: UI callback / terminal binding
- current non-storing snapshot: pre-commit semantic fingerprint再構築
- `projection_generation`差だけ: commit拒否理由にしない
- B2 request / authorization: job ID + start fingerprint exact binding

この区別をtest名とassertionへ明示し、projection tokenをB2 authorization fieldへ追加しない。

### 8.5 terminalを一回だけ受理する

delivery completion gateは、正常な`DeliveryTerminalResult`とworker harness errorの両方を同じone-shot claimへ通す。errorはownership開始前の例外ならstagingなしのfailed terminalへ変換し、ownership開始後の例外はB2-owned cleanup済みterminalへ変換してから同じvalidatorへ渡す。error callbackをterminal callbackと別の受理経路にしない。

delivery terminal validatorは`RUNNING / CANCELLING / FINALIZING`のいずれかで、active bindingが完全一致する最初のcallbackだけを受理する。`AudioWorkerState.is_active`と`UiState.audio_worker_active`は同じ判定を共有し、cancel buttonは別のderived cancel可否で`FINALIZING`時だけ無効化する。受理前にresult型、result.job_id、committed / path / status invariantをB2 DTO constructorに加えて再確認する。late error、late terminal、duplicate error、duplicate terminalはいずれもUI・Busy・filesystem結果を変更しない。

受理後は、worker referenceとactive bindingをclearし、stateをterminal statusへ変更し、Busyを解除する。UI notificationの途中で例外が起きても、Busy解除とbinding clearが`finally`相当で保証される構造にする。

### 8.6 closeはterminal pathを再利用する

close専用にfilesystem結果を推測しない。close pendingでも通常と同じB2 terminalを受理し、その後だけdestroyする。close callbackがworker thread、staging、finalを直接cleanupしない。

### 8.7 user-facing textを固定する

少なくとも次の短い状態文を固定する。

- 開始: `MMD一括出力中...`
- cancel request accepted: `MMD一括出力をキャンセル中...`
- commit started: `MMD一括出力を確定中...`
- success: `MMD一括出力成功`
- cancelled: `MMD一括出力をキャンセルしました`
- failed: `MMD一括出力失敗`

raw exception textはsafe allowlist messageへ連結しない。Error仕様のdetail / copy UI gapはB4から引き継いだ別課題であり、B5で暗黙に解消済みとしない。

## 9. 詳細ステップ

### Step 0: 実装前baseline固定

- live Git status、branch、HEADを確認する。
- B1〜B4 direct testsとworker / warning / close関連回帰を実行する。
- runtime user dataがGit差分へ出ていないことを確認する。
- B5対象5 production filesと新規2 test files以外の変更が必要なら、実装前にscopeを再判定する。

### Step 1: worker state拡張

- `AudioWorkerKind.DELIVERY_PACKAGE`を追加する。
- `AudioWorkerStatus.FINALIZING`を追加し、active状態へ含める。
- 既存kindのenum valueとterminal条件を変更しない。
- state単体testへdelivery / finalizingを追加する。

### Step 2: DeliveryPackageWorker

- `DeliveryCancelToken`と`DeliveryTerminalResult`をcoreからimportする。
- worker task / callback signatureを固定する。
- normal returnをcancel flagで再分類しない。
- task invocationのownership境界とworker-local one-shot completion gateを実装する。B2 ownership開始前のharness exceptionだけをerror callbackへ送り、B2 ownership開始後の例外はB2のcleanup済みterminalへ変換する。
- cancel前、task中cancel、commit後late cancel、unexpected exceptionをunit testする。
- callbackのjob / kind / projection値をexactに確認する。

### Step 2A: `UiState`のactive / cancel派生判定を同期する

- `audio_worker_active`を`AudioWorkerState.is_active`へ委譲し、`FINALIZING`をBusy / close待機対象へ含める。
- `audio_worker_cancel_available`相当のderived propertyを追加し、activeでも`FINALIZING`ならcancel buttonを無効化する。
- `is_busy`、job ID、WARNING fingerprint、個別保存history、SettingsStoreへ新規fieldを追加しない。

### Step 3: MainFrame destination UI

- File menuへ`MMD一括出力...`を追加し、controller actionへbindする。
- `DeliveryDestinationDialog`を追加する。
- parent browse、folder編集、final preview、OK / Cancelを実装する。
- current themeをdialogへ適用し、`Layout()` / `Fit()` / minimum sizeを確認する。
- OS `wx.DirDialog`で制御できないtheme範囲をmanual reportへ残す。
- action stateはBusyでなく、source audioがあり、current diagnosticsがVMD saveableな場合に候補有効とする。click後のB1 gateをauthoritativeとする。

### Step 4: commit snapshot seam

- existing snapshot builderを、stored projectionとnon-storing commit snapshotの共通private helperへ抽出する。
- `build_and_store_output_diagnostics_snapshot()`のgeneration増分、store、戻り値を維持する。
- `build_current_delivery_commit_snapshot()`はpure/read-only `UiSyncContext` builderを使い、generation、UiState、adjustment history、stored diagnostics、WARNING fingerprintを変更しない。pure builderを利用できない状態はfail closedにする。
- B1 current-state captureのone prepare / one morph resolution回帰を維持する。

### Step 5: AppController start flow

- controller fieldを初期化する。
  - `_delivery_worker`
  - `_delivery_parent_directory_session`
  - `_active_delivery_binding`
  - `_delivery_close_pending`
  - `_delivery_terminal_received`
- FFmpeg解決、pre-dialog gate、WARNING、dialog、post-dialog gate、destination validation、long confirmationを§6.4順に実装する。
- post-dialog最終`ready` candidateから`DeliveryStartContext`を一度だけ作り、`build_delivery_artifact_operations()`を一回作る。context object/value、operations、duration、report timestamp、job bindingはworker開始前にlocal immutable値へ固定し、worker closureからUiState / MainFrameを再参照しない。
- B2 orchestration、3つのartifact operation、long-audio確認が同じpost-dialog capture由来のsource identity、effective plan、diagnostics snapshot、FFmpeg path、morph names、timestampを使うことをspyで検証する。既存個別保存pathがあってもwriterを3回再実行する。

### Step 6: pre-commit bridge

- one-shot reply holderと30秒timeoutを実装する。
- worker側waitがUI threadをblockしないことを確認する。
- UI callbackでactive binding / close / cancelを先に確認する。
- non-storing snapshotとB1 evaluatorからauthorizationを構築する。
- callback中cancel、close、timeout、late callback、duplicate replyをdeterministic test seamで確認する。

### Step 7: Busy / cancel / terminal

- worker登録前にprevious statusを保持し、BusyとRUNNING stateを投影する。
- start失敗時はworker reference / active binding / Busyをrollbackする。
- cancel accepted / refusedをCANCELLING / FINALIZINGへ分ける。
- terminal resultとownership前harness errorをcompletion gate経由のsingle pathでsuccess / failed / cancelledへ投影する。ownership後の例外はB2 cleanup済みterminal以外として扱わない。
- cleanup failureをprimary statusと別に表示する。
- individual historyとSettingsStore saveが呼ばれないことをspyする。

### Step 8: deferred close

- MainFrame closeにdelivery優先分岐を追加する。
- pre-commit cancel受理、guard wait、commit started、committed terminalの各phaseをtestする。
- close pending中のduplicate closeをvetoする。
- terminal前に`Destroy()`、`view=None`、job invalidationを行わない。
- terminal後に既存exit cleanupを一度だけ実行する。

### Step 9: error / notification

- terminal code allowlist formatterをcontroller private helperとして追加する。
- final pathとstaging pathを区別する。
- worker error callbackはpre-staging harness failureだけを受け、raw exceptionを表示せず、valid failed terminalへ変換する。B2-owned stagingがある状態の例外はB2 terminal以外のUI pathへ流さない。
- close pending時はsuccessと通常failure modalを抑制する。ただしcleanup失敗だけはsafe warningを1回表示し、確認後にdeferred exitする。
- notification例外でもBusy / binding clearが漏れないことを確認する。

### Step 10: diff / regression監査

- B1〜B4 core、RightPane、runtime data、dependency、README / specsに差分がないことを確認する。
- individual saveのdialog / history / settings saveを回帰する。
- targeted、cross-boundary、full pytest、compileall、diff checkを一コマンドずつ実行する。
- 実装開始前はmanual GUIを「未実施」と記録し、実装後はユーザー報告の確認範囲だけを検証済みとして記録する。

## 10. 状態遷移 / データ契約

### 10.1 start state machine

```text
idle
  -> preflight_capture
       blocked -> idle, no dialog/job/Busy/filesystem
       warning_required
         -> rejected -> idle
         -> confirmed -> recapture
       ready
  -> destination_dialog
       cancelled -> idle
       selected -> post_dialog_capture
  -> post_dialog_gate
       blocked -> idle or dialog retry
       warning_required -> confirm -> recapture
       source/artifact identity changed -> restart preflight/dialog
       ready -> build context
  -> validate_destination
       invalid/collision -> destination_dialog with retained inputs
       valid -> long_audio_confirmation_if_needed
  -> long_audio_confirmation
       rejected -> idle
       accepted/not-needed -> register job
  -> busy/running
```

pre-Busy経路ではfilesystem mutation、audio job ID発行、worker state変更を行わない。

### 10.2 worker / commit state machine

```text
RUNNING
  -> B2 validating/staging/artifacts
  -> awaiting_commit_guard
       UI reply authorized -> commit arbitration
       stale/invalid/timeout -> cleanup -> failed terminal
       cancel/close -> cleanup -> cancelled terminal
  -> commit_started
       cancel request -> rejected, FINALIZING
       rename success -> committed success terminal
       rename failure -> cleanup -> failed terminal

RUNNING --cancel accepted--> CANCELLING
CANCELLING --terminal committed--> COMPLETED
CANCELLING --terminal cancelled--> CANCELLED
FINALIZING --terminal committed--> COMPLETED
FINALIZING --terminal failed--> FAILED
```

UI state名はfilesystem phaseの正本にしない。`DeliveryCancelToken.phase`と`DeliveryTerminalResult`がcommit結果の正本である。

### 10.3 commit authorization matrix

| 条件 | decision | commit |
| --- | --- | --- |
| active job / kind / projection一致、closeなし、cancelなし、fingerprint match | `authorized` | 可 |
| current snapshot missing / save不可 / fingerprint mismatch | `stale` | 不可 |
| job、kind、active projection binding不一致 | `invalid_job` | 不可 |
| cancel受理済み | `cancelled` | 不可 |
| close pending | `closing` | 不可 |
| UI callback timeout / exception / malformed reply | guard failure | 不可 |

authorizationのjob IDとstart fingerprintはB2 requestをexact echoする。projection generation、final path、display textをauthorization identityへ追加しない。

### 10.4 terminal invariant

| result | UI terminal | final path | history / settings |
| --- | --- | --- | --- |
| committed success | completed | resultのfinal pathだけ採用 | 変更なし |
| cancelled | cancelled | なし | 変更なし |
| failed | failed | なし | 変更なし |
| cleanup failure | primary statusを保持 | なし。stagingはinternal detail | 通常時とclose pending時の双方でsafe warning。close pending時は確認後にexit |
| late / duplicate | 反映しない | 参照しない | 変更なし |

### 10.5 close invariant

- close pendingだけではterminalを作らない。
- commit前cancel受理時はB2 cleanup terminalを待つ。
- commit開始後はrename terminalを待つ。
- committed finalをclose cleanupしない。
- terminal前にwindowをdestroyしない。
- terminal後のexit処理は一度だけ行う。

### 10.6 state ownership

| state | owner | persistence |
| --- | --- | --- |
| start context / fingerprint | B1 immutable DTO | job lifetime |
| staging / commit / terminal | B2 core | job lifetime / filesystem final |
| artifact generation | B3 operation | job lifetime |
| report identity | B4 snapshot / formatter | report file |
| active job / worker / close pending | AppController | session memory |
| Busy / current audio job / worker state | UiState | session memory |
| batch parent | AppController | session memory only |
| individual output histories | existing UiState / SettingsStore | B5では読取のみ |

## 11. テスト方針

### 11.1 B5 worker unit test

`tests/test_ms25_b5_delivery_worker.py`:

- `DELIVERY_PACKAGE` kindと`FINALIZING` active state
- `UiState.audio_worker_active`が`AudioWorkerState.is_active`と一致し、`FINALIZING`をactiveとして扱うこと
- `FINALIZING`ではBusy / close待機を維持しつつcancel可否だけfalseになること
- workerがcore `DeliveryCancelToken`をtaskへ渡す
- success terminalを一回だけCallAfterする
- task return直後のlate cancelでも`committed=True` resultをcancel callbackへ変換しない
- cancel accepted / commit-started cancel rejectedのbool
- callbackへjob ID / kind / projection generationをexact伝播する
- ownership前のunexpected exceptionだけがerror callbackへ行き、同じcompletion gateで一度だけfailed terminalへ変換される
- B2 artifact / guard / commit exceptionがcleanup済み`DeliveryTerminalResult`になる
- error callback、terminal callback、late / duplicate callbackが相互に二重投影されない
- generic `AudioWorker`のPROBE / ANALYSIS_WAV / MMD_WAV semanticsが変わらない

### 11.2 B5 GUI / controller integration test

`tests/test_ms25_b5_delivery_gui.py`:

- ERROR / invalid state / FFmpeg unavailableではdestination dialog、job、Busy、workerなし
- WARNING dialogがdestination dialogより前に一度だけ出る
- WARNING Noでconfirmation / destination / worker / history不変
- WARNING Yesでshared fingerprintを保存し、same fingerprintを再確認しない
- destination dialog cancelでjob / Busy / filesystemなし
- default folder `<audio_stem>_MMD`
- default parent優先順位とsession-only parent再利用
- invalid folder / path / collisionで入力保持・再入力
- dialog後fingerprint変更で新しいWARNING確認を要求し、承認後にB1 gateを再実行してready candidateを得る
- dialog後source / artifact identity変更で古いdestinationを流用しない
- post-dialog ready candidateから同じ`DeliveryStartContext`がB2、VMD、MMD WAV、reportへ渡る
- 既存の個別保存pathがあっても3成果物を個別pathから流用せず再生成する
- 300秒以下は確認なし、300秒超はvalid destination後・Busy前に一度だけ確認
- long-audio Noでworker / stagingなし
- worker開始時にactive bindingとBusy / RUNNINGが同時に投影される
- Busy中にpackage、VMD、MMD WAV、report、workspace reset、input / analysis開始がlockされる
- cancel request後もterminalまでBusyを維持する
- commit-started cancel拒否でFINALIZINGとなり、cancel buttonを無効化する
- success / failure / cancel / cleanup failureのsafe projection
- committed successがCANCELLING / FINALIZING表示を上書きしてcompletedになる
- late / duplicate / job-kind-projection mismatchがcurrent UIを変更しない
- success / failure / cancelで個別path historyとSettingsStore saveが不変
- ERROR block中もBusyでなければstandalone report actionが既存条件で有効

### 11.3 commit guard / close test

同じB5 GUI test fileでthread/event seamを使い、次をdeterministicに確認する。

- worker threadからGUI stateを直接読まない
- `wx.CallAfter`後、UI thread callbackでだけsnapshotを再構築する
- commit snapshotがprojection generation、UiState、adjustment history、stored diagnostics snapshot、WARNING fingerprintを変更しない
- active job / kind / projection / fingerprint matchだけがauthorized
- stale / invalid job / cancel / close / timeoutのdecision
- timeout後のlate UI replyを破棄する
- guard wait中closeがdeadlockせずcancel terminalへ進む
- close pre-commitではterminal / cleanup前にDestroyしない
- close commit-startedではcancel成功と表示せずterminalを待つ
- committed terminal後だけDestroyする
- duplicate close / duplicate terminalでDestroyを重複しない
- duplicate / late error callbackでBusy解除、status上書き、Destroyを重複しない
- close pending中のcleanup失敗はsafe warningを1回表示し、確認後にDestroyする

### 11.4 既存回帰

最低限、次を一コマンドずつ実行する。

1. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b5_delivery_worker.py`
2. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b5_delivery_gui.py`
3. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b5_delivery_worker.py tests/test_ms25_b5_delivery_gui.py`
4. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py tests/test_ms25_b2_windows_paths.py tests/test_ms25_b2_delivery_orchestration.py tests/test_ms25_b2_delivery_commit.py`
5. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b3_delivery_artifacts.py tests/test_ms25_b3_vmd_readback_validation.py tests/test_ms25_b4_delivery_report_identity.py`
6. `.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_ms17_b8_long_audio_confirmation.py tests/test_ms17_b8_audio_worker_state.py tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms21_b7_audio_worker_terminal.py`
7. `.\.venv\Scripts\python.exe -m pytest tests/test_ms19_b8_workspace_reset.py tests/test_wx_ms14_b5_export.py tests/test_ms20_b6_report_save_flow.py tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
8. `.\.venv\Scripts\python.exe -m pytest tests`
9. `.\.venv\Scripts\python.exe -m compileall -q src tests`
10. `git diff --check`

個別保存導線の重点回帰として、`tests/test_ms17_b7_mmd_wav_button_state.py`、`tests/test_ms17_b7_mmd_wav_save_dialog.py`、`tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`、`tests/test_ms21_b5_adjusted_vmd_save.py`も実行する。さらに、個別VMD承認後→一括出力、および一括出力承認後→個別VMDの両方向で、同一fingerprintのWARNINGを再要求しないことを確認する。

各pytestはpass表示とprocess exit codeを別々に記録する。wx testは終了後のnative exception有無も確認する。testを削除、skip、期待値弱化して合格させない。

### 11.5 manual GUI確認境界

B5はvisible menu、dialog、Busy、cancel、closeを追加するため、manual GUI確認を受け入れ必須とする。自動test通過だけでmanual GUI確認済みとしない。

確認項目:

1. `ファイル > MMD一括出力...`の表示と有効 / 無効状態
2. parent / folder dialogの既定値、編集、Cancel、final preview
3. Unicode folder名、invalid名、同名destination時の再入力
4. WARNING確認がdestination dialogより前に出て、Noで何も開始しないこと
5. 300秒超確認がdestination確定後・Busy前に一度だけ出ること
6. worker中に一括出力、VMD、MMD WAV、report、新規作業、入力変更、解析がlockされること
7. cancel中にBusyが残り、terminal後に解除されること
8. success時に3成果物がfinal directoryへ現れ、個別保存historyが変わらないこと
9. failure / cancel時にpartial finalが現れず再実行できること
10. delivery中closeでwindowが直ちに消えず、terminal後に終了すること
11. Light / Dark / Systemでcustom dialogの文字、TextCtrl、buttonが読めること
12. `wx.DirDialog`のOS管理部分でtheme制御できない範囲の記録
13. 個別VMD、個別MMD WAV、standalone reportが引き続き利用できること

commit開始の瞬間やTOCTOU、actual reparse / junction、cleanup failureの再現はmanual GUIへ依存させず、自動testとB6のWindows fault matrixで確認する。実MMDでのVMD / WAV読込・再生・リップ同期はMS26、onefile / ZIP / releaseはMS27へ維持する。

## 12. 受け入れ条件

### 12.1 GUI / start gate

- [x] `ファイル > MMD一括出力...`から起動できる。
- [x] parent directoryとeditable folder名を指定できる。
- [x] default folderがB1の`<audio_stem>_MMD`である。
- [x] default parentとsession-only parentが§6.3順で決まり、INIへ保存されない。
- [x] diagnostics ERROR、invalid current state、FFmpeg不足ではdialog / job / Busy / worker / filesystemを開始しない。
- [x] WARNING確認がdestination dialogより前に行われ、Noでは状態を変更しない。
- [x] post-dialog fingerprint変更時は新しいWARNING確認なしにworkerを開始しない。
- [x] source / artifact identity変更時は古いdestination選択を流用しない。
- [x] invalid path / collisionを暗黙renameせず、同じ入力を保持して別名を要求する。
- [x] 300秒超確認はvalid destination後・Busy / worker前に一度だけ行われる。

### 12.2 worker / Busy / late result

- [x] `AudioWorkerKind.DELIVERY_PACKAGE`が既存kindと分離される。
- [x] delivery taskはUI threadで実行されない。
- [x] task正常return後のcancel flagだけでcommitted resultをcancelへ変換しない。
- [x] terminal callbackとerror callbackが同じone-shot completion gateを通り、ownership前harness errorだけがfailed terminalへ変換される。
- [x] Busy中は競合actionがlockされ、cancel / close確認だけが利用できる。
- [x] cancel request後もterminal / cleanupまでBusyを維持する。
- [x] commit開始後のcancel拒否をFINALIZINGとして表示し、cancelledと誤表示しない。
- [x] job ID / worker kind / active projection bindingが一致する最初のterminalだけを反映する。
- [x] late / duplicate callbackがUI、history、filesystem結果を変更しない。

### 12.3 pre-commit authorization

- [x] worker threadからMainFrame / UiStateを直接読まない。
- [x] UI thread上でcurrent semantic snapshotを再構築する。
- [x] commit snapshot構築がUiState、adjustment history、stored snapshot、WARNING fingerprint、projection generationを変更しないpure経路で行われる。
- [x] start / current fingerprint、active job、kind、close、cancelを確認する。
- [x] exact match時だけjob ID / start fingerprintにbindingされたauthorized responseを返す。
- [x] projection generation差だけをsemantic stale理由にしない。
- [x] stale / invalid / cancel / close / timeoutではcommitせずB2 cleanupへ進む。

### 12.4 terminal / close

- [x] B2 `DeliveryTerminalResult`がsuccess / failure / cancelの正本である。
- [x] ownership開始後のworker例外はB2 cleanup済みterminalへ集約され、error callbackが別のfilesystem結果を作らない。
- [x] committed successをlate cancelでcancelledへ上書きしない。
- [x] cleanup failureをprimary resultと別に表示し、success扱いしない。close pending中もsafe warningを1回表示してからexitする。
- [x] raw exception、traceback、staging pathを通常表示へ漏らさない。
- [x] close pre-commitではcancel terminal / cleanupまでwindowを破棄しない。
- [x] close commit-startedではrename terminalを待ち、committed finalを削除しない。
- [x] terminal後だけdeferred exitを一度実行する。
- [x] window破棄後に新しいfinal commitが発生しない。

### 12.5 coexistence / scope

- [x] individual VMD / MMD WAV / report導線が従来どおり使用できる。
- [x] 個別保存pathの有無にかかわらず、一括出力は現在状態からVMD / MMD WAV / reportを再生成する。
- [x] success / failure / cancelで個別保存historyを更新しない。
- [x] SettingsStore / INIへbatch parent / folderを保存しない。
- [x] shared WARNING fingerprintだけをB1契約どおり再利用する。
- [x] 個別VMD承認後→一括出力、および一括出力承認後→個別VMDの両方向で、同一fingerprintのWARNINGを再要求しない。
- [x] B1〜B4 core / report契約、runtime data、dependencyを維持した。README / specsの同期はB5実装後に実施した。
- [x] B5 targeted / related / full pytest、compileall、diff checkがpass表示かつprocess exit code `0`である。
- [x] manual GUI結果をユーザー報告として、実施者と範囲の確度を限定して記録した。
- [x] 実MMD、Python 3.11 / 3.12、PyInstaller / releaseは未実施・未検証として報告する。

## 13. リスクと対策

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS25-B5-R1 | generic `AudioWorker`がcommitted successをlate cancelでcancel callbackへ変換する | P1候補 | dedicated workerはB2 terminalを再分類せずsingle terminal callbackへ渡す |
| MS25-B5-R2 | worker threadがMainFrame / UiStateを直接読みwx raceを起こす | P1候補 | `wx.CallAfter` bridgeとone-shot replyだけを使い、UI thread callbackでsnapshotを再構築する |
| MS25-B5-R3 | Busy中のB1 start gateをpre-commitへ流用し、deliveryが自己失効する | P1候補 | start gateは維持し、non-storing commit snapshot seamを別に追加する |
| MS25-B5-R4 | projection generationをcommit条件へ加えて再描画だけでstaleになる | P1候補 | projectionはactive callback bindingだけに使い、semantic evaluatorはfingerprintだけを使う |
| MS25-B5-R5 | pre-commit UI callbackが失われworkerが永久待機する | P1候補 | 30秒timeoutでguard failureへfail closedし、late replyを破棄する |
| MS25-B5-R6 | closeがterminal前にviewを破棄し、後からfinal commitされる | P1候補 | close eventをvetoし、cancel / commit terminal受理後だけ既存exitへ進む |
| MS25-B5-R7 | commit開始後cancelをcancelled表示し、成功finalとUIが矛盾する | P1候補 | tokenのboolを使い、拒否時はFINALIZING、terminal committedをsuccess正本にする |
| MS25-B5-R8 | WARNING確認前にdestination dialogやfilesystem処理を始める | P2候補 | §6.4順序をcontroller testでspyし、Noで全seam未呼出を確認する |
| MS25-B5-R9 | dialog中にfingerprint / sourceが変わり、古い承認やfolder defaultを使う | P2候補 | post-dialog recapture、新fingerprint再確認、source / artifact変化時のdialogやり直し |
| MS25-B5-R10 | collisionをGUI側sanitize / 連番renameしてユーザー指定とずれる | P2候補 | B2 validatorをauthoritativeにし、入力保持・別名要求だけを行う |
| MS25-B5-R11 | long-audio確認がdialog前またはBusy後になり、拒否時にworkerが残る | P2候補 | valid destination後・Busy前の一回確認を固定し、call order testを追加する |
| MS25-B5-R12 | delivery successが個別VMD / WAV historyやINIを更新する | P2候補 | controller-local session parentだけを保持し、SettingsStore spyとhistory snapshotで検証する |
| MS25-B5-R13 | close pending中のmodalでshutdownが再度blockする、またはcleanup失敗を黙って見落とす | P2候補 | success / 通常failure modalは抑制するが、cleanup失敗だけはsafe warningを1回表示し、確認後にdeferred exitへ進む |
| MS25-B5-R14 | cleanup failureのstaging pathを通常dialogへ表示する | P2候補 | safe cleanup warningだけを表示し、pathはinternal detailへ限定する |
| MS25-B5-R15 | custom dialogだけtheme / Layoutが崩れる | P3候補 | ThemeManager、Fit / minimum size、自動component test、Light / Dark / System manual確認 |
| MS25-B5-R16 | menu-only導線がREADMEと一時的に不一致になる | P3（解消） | B5実装後、README / 配布readme / specsへ実装済み導線を同期した |

## 14. 実装時の注意

- コマンドは一つずつ実行し、shell pipeline、chain、parallel executionを使わない。
- 実装開始時にlive Git statusとuser-owned差分を確認する。
- B5追加差分を§7.1の5 production filesと§7.2の2 test filesへ限定する。
- `src/core/delivery_package.py`、`delivery_artifacts.py`、`diagnostic_report.py`、VMD validatorを変更しない。
- `capture_current_delivery_state()`のBusy拒否を緩めない。
- `build_and_store_output_diagnostics_snapshot()`の既存generation増分とstore behaviorを変えない。
- non-storing commit snapshotをcurrent displayed snapshotへ代入しない。
- worker threadからwx API、MainFrame、UiState、SettingsStoreを呼ばない。
- `DeliveryCancelToken`をGUI generic `CancelToken`へ置換・継承しない。
- committed resultをcancel flag、close flag、worker statusから再推測しない。
- pre-commit authorizationへprojection generationを追加しない。
- timeout、exception、malformed responseをauthorizedへfallbackしない。
- close pending中に`_is_shutting_down=True`、job invalidation、`view=None`、`Destroy()`をterminal前に行わない。
- final path、parent、既存package、個別出力をGUI cleanup対象にしない。
- invalid folder名をsanitize、truncate、連番化しない。
- success / failure / cancelで`request_settings_save()`を呼ばない。
- standalone reportのERROR時保存可能契約を一括出力ERROR gateへ巻き込まない。
- B4 report fieldとsafe error契約を変更しない。
- runtime `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読書き、コピー、stageしない。
- B5実装時にはREADME / Index / Roadmap /正文仕様の同期を先行せず、実装後の結果として関連文書へ反映した。
- manual GUIはユーザー報告で通過した範囲を記録し、Codex自身のGUI実行結果とは扱わない。
- actual MMDはMS26、package / releaseはMS27へ維持する。
- stage、commit、merge、push、tag、releaseは別の明示承認まで行わない。

### 14.1 実装後報告

1. 確認したファイル
2. 変更したファイル
3. B5実装内容
4. 実行したtestとprocess exit code
5. manual GUI確認結果
6. 仕様からの逸脱
7. 残課題
8. B6への引き継ぎ

### 14.2 後続Blockへの引き継ぎ

- MS25-B6:
  - actual Windows reparse / junction、locked / readonly、TOCTOU、cleanup failure、OS shutdownの横断matrix
  - pre-commit / commit中 / commit後closeの追加fault injection
  - cleanup failure時の利用者向けrecovery detail
- MS25-B7:
  - full cross-boundary regression
  - B5実装結果を反映済みのREADME、`readme_mmdautolip.txt`、Pipeline / GUI / Error / VMD仕様、Index、Roadmapを基準に、残る状態差分を監査
  - manual GUI結果、未検証境界、MS26 / MS27 handoff

### 14.3 ユーザー判断事項

未解決のユーザー判断事項はない。

- 起動導線は、既存top panelを拡張せず`ファイル > MMD一括出力...`へ置く。
- parentとfolder名は一つのcustom dialogで扱う。理由は、別々のOS dialogよりfinal destinationを確認しやすく、collision再入力時に値を保持できるためである。
- batch parentはsession-onlyで保持し、既存MMD WAV / VMD / source directory順を初期値に使う。
- pre-commit UI handoffは30秒でfail closedにする。理由は、正常時は即時のUI callbackであり、無期限waitではclose / cleanup保証を失うためである。

これらはB1〜B4の出力・transaction・report契約を変更せず、B5のGUI / worker接続内で完結する判断である。
