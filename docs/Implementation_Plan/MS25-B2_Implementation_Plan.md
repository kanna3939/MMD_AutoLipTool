# MS25-B2 Implementation Plan

## 1. 文書情報

- 文書名: MS25-B2 Delivery Package core orchestration Implementation Plan
- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B2 Delivery Package core orchestration
- 作成日: 2026-08-30
- 状態: B2実装・自動検証済み。production code / test codeは`0f018cd Implement MS25-B2 delivery package orchestration`で実装済み。B2の可視GUI actionは追加していない
- 対象ブランチ: `feature/MS25-implementation`
- 計画作成時HEAD: `a41f0a0 Implement MS25-B1 delivery state gate`
- 直接依存: 実装済みのMS25-B1 `DeliveryCurrentState` / `DeliveryStartContext` / fingerprint gate
- 計画作成時の変更権限: `docs/Implementation_Plan/MS25-B2_Implementation_Plan.md`の新規作成だけ。production code、test code、他文書、GUI、runtime user data、設定、依存関係は変更しない
- ユーザー判断待ち: なし。既存destination一律拒否、path長、固定成果物名、生成順、commit guard、cancel線形化点はRoadmap、Block Breakdown、B1契約から確定できる
- 計画作成時に実行した確認:
  - B1専用2ファイル: `17 passed`、process exit code `0`
  - MMD WAV / report / effective VMD / cancel / worker terminal境界6ファイル: `34 passed`、process exit code `0`
- 実装結果: destination validation、staging、pre-commit authorization、cancel / commit線形化、no-clobber commit、`DeliveryTerminalResult`を実装し、B2専用testを追加した。
- 未検証・後続: B2の可視GUI手動確認は対象外。actual Windows junction / reparse / locked / readonly fault matrixはB6、MS25全体のfull cross-boundary regressionはB7、実MMD確認はMS26、Python 3.11 / 3.12とPyInstaller / release確認は後続である。
- 外部仕様確認:
  - MicrosoftのWindows命名規則で禁止文字、予約device名、末尾space / dot、superscript digitを確認した
  - Python 3.11の`os.rename()`はWindowsでdestination既存時に`FileExistsError`となるため、同一親directory内のno-clobber commitに使用できることを確認した
  - `tempfile.mkdtemp()`は競合なしにdirectoryを作成する一方、cleanupはcaller責務であることを確認した
  - `os.path.lexists()` / `os.lstat()`はbroken symlinkを含むentry判定に使用でき、Windowsの`lstat`はname-surrogate reparse pointをfollowしないことを確認した

### 1.1 正本と現行状態の優先順位

B2の判断には次の順を使う。

1. live Gitと現行code / test
2. `docs/Implementation_Plan/MS25_Block_Breakdown.md`
3. `docs/Implementation_Plan/MS25-B1_Implementation_Plan.md`の契約部分
4. Roadmap §12〜§15と現行仕様書
5. Indexや各planの過去時点記録

`docs/MS20_and_Beyond_Index.md`とB1 planの状態欄は、メイン側の文書同期によりB1実装・検証済みのlive状態へ更新済みである。live HEADにはB1 codeと専用testが存在し、対象17件はpassしている。B2では現行codeを前提とし、状態文書の記述をB1未実装とは解釈しない。B2実装自体では他文書を変更せず、以後のrouting同期は別途明示された文書同期またはB7で扱う。

## 2. 背景

MS25は、現在の編集結果からVMD、元の入力音声からMMD用WAV、同じ開始snapshotから診断レポートを再生成し、一つの専用directoryとして確定する機能である。B1は、次の現行APIを`src/core/delivery_package.py`へ実装した。

- `DeliveryArtifactNames`
- `SourceAudioIdentity`
- `DeliveryCurrentState`
- `DeliveryStartGateResult`
- `DeliveryStartContext`
- `DeliveryCommitFingerprintResult`
- `build_delivery_artifact_names()`
- `capture_source_audio_identity()`
- `evaluate_delivery_start_gate()`
- `build_delivery_start_context()`
- `evaluate_delivery_commit_fingerprint()`

B1の`DeliveryStartContext.parent_directory`と`folder_name`は構造的に保持されるだけで、Windows名、長さ、collision、書込み可否はまだ検証しない。B2はこの既存DTOを受け取り、filesystem transactionを実行するcore境界を追加する。

現行の出力処理には次の制約がある。

- `write_morph_frames_vmd()`は指定pathへ直接書くため、final directoryではなくstaging内pathへだけ呼ぶ必要がある。
- `export_mmd_wav()`と`write_diagnostic_report()`は各staging file内ではtemporary + `os.replace()`を使う。このreplaceはstaging内部fileの保護に限り許可し、final directory確定には使用しない。
- 現行`AudioWorker.run()`はtask正常return後でもcancel flagが立っていればcancel callbackへ変換する。この挙動をdeliveryへそのまま使うと、commit済みfinalをcancel扱いにできるため、B2のterminal resultをB5が優先する専用分岐が必要である。
- 現行`request_exit()`はaudio jobを無効化してworkerをcancelした直後にwindowを破棄する。deliveryのclose待機はB5 / B6で接続し、B2 coreからGUIを直接操作しない。
- Error Handling仕様の「VMD成功 / WAV失敗」等は既存の個別保存導線の契約である。delivery packageでは3成果物を一つのtransactionとし、一部成功をfinal directoryへ公開しない。

### 2.1 外部仕様根拠

- [Microsoft: Naming Files, Paths, and Namespaces](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)
  - Win32禁止文字、U+0000〜U+001F、予約名、superscript digit、末尾space / dotの根拠
- [Microsoft: RtlIsDosDeviceName_U](https://learn.microsoft.com/en-us/windows/win32/devnotes/rtlisdosdevicename_u)
  - `CONIN$` / `CONOUT$`を含むDOS device名の補完根拠
- [Python 3.11: `os.rename()`](https://docs.python.org/3.11/library/os.html#os.rename)
  - Windows destination既存時の失敗と、cross-filesystem fallbackを採らない根拠
- [Python 3.11: `tempfile.mkdtemp()`](https://docs.python.org/3.11/library/tempfile.html#tempfile.mkdtemp)
  - staging directoryの競合なし作成とcaller cleanup責務の根拠
- [Python 3.11: `os.path.lexists()`](https://docs.python.org/3.11/library/os.path.html#os.path.lexists) / [`os.lstat()`](https://docs.python.org/3.11/library/os.html#os.lstat)
  - broken symlinkとWindows reparse pointをexisting entryとして検査する根拠
- [Python 3.11: `shutil.rmtree()`](https://docs.python.org/3.11/library/shutil.html#shutil.rmtree)
  - Windows junctionをtarget treeごと削除しない挙動と、cleanup raceの残存注意の根拠

## 3. 目的

MS25-B2では、B1のimmutable開始contextを入力として、次をGUI非依存coreへ実装できる状態にする。

1. 親directory、`audio_stem`、編集可能folder name、全成果物名をWindows規則とMS25固定長で検証する。
2. finalと同じ親directoryへ競合なくstaging directoryを作成する。
3. B3が後から提供する3つの「生成してvalidation完了まで行う」operationを固定順で呼ぶ。
4. 3成果物以外がstagingにないことを確認し、job IDと開始fingerprintに結び付いたpre-commit authorizationを一度だけ要求する。
5. cancelとcommit開始を一つのlockで順序付け、Windowsの`os.rename()`で既存entryを置換しないdirectory単位commitを行う。
6. success、failure、cancel、cleanup failureを一つのimmutable terminal resultで返す。
7. B5がworker threadから呼べる同期core APIとし、wx / GUI state /個別保存履歴 / runtime設定へ依存させない。

B2完了は実成果物writerやGUI一括出力の利用可能化を意味しない。B3のproduction writer、B4 report拡張、B5 GUI / worker接続、B6 recovery hardeningが完了するまで、利用者向け一括出力は未実装である。

## 4. In Scope

- `src/core/delivery_package.py`へのadditiveなB2 API追加
- Windows向けcomponent validation
- UTF-16 code unitによるcomponent 255 / absolute path 240上限
- absoluteな既存parent directoryの検証と解決
- `audio_stem`、folder name、固定3成果物名の検証
- `.`、`..`、separator、禁止文字、control character、末尾space / dot、予約device名の拒否
- final pathの事前collision検査
- directory、file、symlink、broken symlink、junction / reparse pointを含む既存entryの一律拒否
- finalと同じresolved parent直下へのopaque staging作成
- 固定順`VMD -> MMD用WAV -> 診断レポート`
- B3用の3 artifact operation injection境界
- 各operation return後のgeneric staging file postcondition確認
- commit前のstaging exact-content確認
- job ID / start fingerprint結合のpre-commit guard request / authorization DTO
- `awaiting_commit_guard`状態
- delivery専用thread-safe cancel token
- cancel受理とno-clobber rename開始の線形化
- `os.rename(staging, final)`によるWindows no-clobber commit
- owned staging限定のbest-effort cleanup
- primary resultとcleanup resultを分離したimmutable terminal result
- B2専用core単体test
- B1、既存writer境界、cancel / worker terminalの回帰確認

## 5. Out of Scope

- B3の具体的なVMD生成、production VMD read-back validator
- B3の具体的なMMD WAV生成、source identity前後再確認
- B3の具体的なdiagnostic report writer接続
- B4のreport項目追加、profile未使用 / 既定morph setの必須表示
- B5のbutton / menu / destination dialog / WARNING dialog
- B5の`AudioWorkerKind.DELIVERY_PACKAGE`、wx worker、Busy、late callback、close待機接続
- B6の実junctionを含む環境依存reparse test、locked / readonly file、shutdown横断matrix、cleanup race hardening
- 既存`AudioWorker`の一般挙動変更
- 個別VMD保存、個別MMD WAV出力、個別diagnostic report保存の変更
- 個別保存履歴、recent files、設定保存
- 新しいINI keyまたはbatch parent directoryの永続化
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読書き、コピー、stage
- README、Roadmap、Index、仕様書の同期
- ZIP、session file、manifest、hash file、MMD自動起動
- dependency追加・更新
- network、cloud、telemetry、background通信
- 実MMD確認（MS26）
- PyInstaller / package / release readiness（MS27）

## 6. 前提条件

### 6.1 B1 APIの現実

- `DeliveryStartContext.current_state.gate_status`は`ready`である。
- `start_fingerprint`は同じcaptureの`OutputDiagnosticsSnapshot.save_state_fingerprint`と一致する。
- `artifact_order`は`("vmd", "mmd_wav", "report")`である。
- `artifact_names`は元音声stemから固定名を保持するが、B1はWindows名validationを行わない。
- `parent_directory`と`folder_name`もB1ではvalidation済みではない。B2 orchestrationは、B1 DTOを信頼してfilesystem mutationを始めず、必ずB2 validatorを通す。
- `projection_generation`はUI投影 / late-result discard専用であり、B2 authorizationの一致条件にしない。
- B1の`evaluate_delivery_commit_fingerprint()`はsemantic fingerprintだけを判定する。active job、worker kind、cancel、closeを含むauthorizationはB5が構築し、B2はjob / fingerprint bindingを検証する。

B1現行APIにB2を阻害するP1 / P2はない。Index / B1 planの状態欄はメイン側の文書同期でlive B1実装・検証済みへ更新済みである。

### 6.2 Windows component validation

component validatorは文字列をUnicodeのまま保持し、normalize、ASCII化、置換、trim、切詰め、連番付与を行わない。次を拒否する。

- `str`でない値、空文字
- `.`、`..`
- `< > : " / \ | ? *`
- code point U+0000〜U+001FのWin32 control character
- strict UTF-16 encodingに失敗するunpaired surrogate
- 末尾のASCII spaceまたは`.`
- base nameを最初の`.`より前で取り、末尾space / dotを除いてcase-insensitive比較した予約名:
  - `CON`、`PRN`、`AUX`、`NUL`
  - `COM1`〜`COM9`、`LPT1`〜`LPT9`
  - `COM¹` / `COM²` / `COM³`、`LPT¹` / `LPT²` / `LPT³`
  - `CONIN$`、`CONOUT$`、`CLOCK$`
- extension風suffixを付けた予約名。例: `con.txt`、`NUL.tar.gz`
- UTF-16 code unit 255超過

長さは`len(value.encode("utf-16-le", errors="strict")) // 2`相当で数える。Pythonの`len()`だけを使わず、astral characterを2 code unitとして扱う。

### 6.3 parent / path validation

- parentはabsolute pathでなければならない。drive-relative path、相対path、空pathを拒否する。
- `\\?\`、`\\.\`等のdevice / extended namespaceを受け付けず、通常Win32 pathとして扱う。
- parentは`resolve(strict=True)`できる既存directoryでなければならない。file、未存在、解決失敗は拒否する。
- `os.access()`だけをwriteability証拠にしない。実際のstaging作成成功をauthoritativeな書込み可否確認とする。
- resolved parent、final、staging候補、staging内3成果物、final内3成果物のabsolute文字列表現をUTF-16 code unit 240以下にする。NUL終端は数えない。
- final directory名はparent直下の1 componentとして扱い、folder nameから複数階層を作らない。
- parent内の既存componentについてもcomponent 255上限を確認する。ただし選択済みparentのUnicode spellingを変更しない。
- UNC absolute pathは、同じ上限と通常API条件を満たし、実staging作成とrenameが成功する場合は拒否しない。

### 6.4 staging naming

- `tempfile.mkdtemp(dir=validated_parent, prefix=".MMD_AutoLipTool.delivery-", suffix=".staging")`相当を使い、name生成とdirectory作成を分離しない。
- staging名はfolder nameやaudio stemを含めないopaque名とする。
- stagingはresolved parentのdirect childとし、別temp rootや別volumeを使わない。
- 実装定数`STAGING_COMPONENT_UTF16_BUDGET = 64`を置き、作成前に64 UTF-16 code unitの仮componentを使ってstaging / artifact absolute path上限を検証する。作成後も実名を再検証し、64超過またはpath上限超過時はowned stagingだけをcleanupして失敗する。
- `mkdtemp()`が返したpathだけをそのjobのowned stagingとして記録する。似たprefixの既存directoryはcleanupしない。

### 6.5 collision / no-clobber

- final entry検査は`Path.exists()`だけに依存しない。
- `os.lstat(final_path)`が成功したら、種類や空否を問わずcollisionとする。
- `FileNotFoundError`だけをabsentとみなし、permission等の他の`OSError`はinspection failureとしてfail closedにする。
- `st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT`は分類・testに使えるが、判定自体は全`lstat`成功をcollisionにするため、未知のreparse tagでも置換しない。
- preflight、artifact完了後、authorization取得後にfinalを再検査する。
- commitはWindows上の`os.rename(staging_path, final_path)`一回だけとする。`os.replace()`、`Path.replace()`、`shutil.move()`、copy + delete fallbackを使わない。
- rename失敗後にfinal entryが存在する場合はTOCTOU collisionへ正規化する。finalが存在しない場合はpermission / locked / commit failureとして分類する。
- rename成功後にfinalをcancel cleanup対象へ戻さない。
- この契約はprocess crash / power loss時のdurability journalまでは保証しない。MS25は3成果物の通常実行時transactionと既存出力保護を保証範囲とする。

## 7. 対象ファイル

### 7.1 B2実装時の主変更対象

| 種別 | ファイル | B2責務 |
| --- | --- | --- |
| 既存変更 | `src/core/delivery_package.py` | Windows validation、validated paths、staging、artifact operation seam、commit guard、cancel token、terminal result、cleanup、orchestration |
| 新規 | `tests/test_ms25_b2_windows_paths.py` | component / parent / UTF-16 length / collision検証 |
| 新規 | `tests/test_ms25_b2_delivery_orchestration.py` | 固定順、staging、exact contents、success / artifact failure、GUI非依存性 |
| 新規 | `tests/test_ms25_b2_delivery_commit.py` | authorization binding、TOCTOU、cancel線形化、terminal / cleanup不変条件 |

### 7.2 B2では原則変更しない確認対象

- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/worker_state.py`
- `src/core/mmd_wav_export.py`
- `src/core/diagnostic_report.py`
- `src/core/audio_probe.py`
- `src/core/audio_convert.py`
- `src/core/ffmpeg_runner.py`
- `src/core/pipeline.py`
- `src/core/output_diagnostics.py`
- `src/vmd_writer/writer.py`
- `src/vmd_writer/effective_shape_adapter.py`
- `src/core/__init__.py`

B2 APIは現行と同じ`src.core.delivery_package`から直接importする。`src/core/__init__.py`への大量exportやnamespace整理は行わない。

### 7.3 B2では変更しない対象

- B1専用test
- README、`readme_mmdautolip.txt`
- Roadmap、Index、Block Breakdown、B1 plan、正文仕様
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`
- `pyproject.toml`、lock file、PyInstaller spec、build script、license文書
- 個別保存履歴とSettingsStore

## 8. 実装方針

### 8.1 additive core API

`src/core/delivery_package.py`へ、既存B1 DTO / functionを壊さず、少なくとも次と同等のAPIを追加する。実装時にprivate helper名を調整してもfieldと不変条件は弱めない。

```python
@dataclass(frozen=True)
class ValidatedDeliveryDestination:
    parent_directory: Path
    folder_name: str
    final_directory: Path
    final_artifact_paths: tuple[tuple[DeliveryArtifactKind, Path], ...]

@dataclass(frozen=True)
class DeliveryStagingPaths:
    root_directory: Path
    artifact_paths: tuple[tuple[DeliveryArtifactKind, Path], ...]

@dataclass(frozen=True)
class DeliveryCommitGuardRequest:
    job_id: int
    start_fingerprint: str
    final_directory: Path

@dataclass(frozen=True)
class DeliveryCommitAuthorization:
    job_id: int
    start_fingerprint: str
    decision: Literal[
        "authorized",
        "stale",
        "cancelled",
        "invalid_job",
        "closing",
    ]

@dataclass(frozen=True)
class DeliveryTerminalResult:
    job_id: int
    primary_status: Literal["success", "cancelled", "failed"]
    primary_error_code: str | None
    committed: bool
    final_path: Path | None
    staging_path: Path | None
    cleanup_status: Literal[
        "not_required",
        "completed",
        "partial_output_cleanup_failed",
    ]
    commit_phase: Literal[
        "before_commit",
        "awaiting_commit_guard",
        "commit_started",
        "committed",
        "commit_failed",
    ]
    artifact_phase: DeliveryArtifactKind | None
```

B2はartifact operationの実装を追加せず、artifact writerを新たにimportまたは直接呼び出さず、次の3 callableを一つのfrozen holderへ束ねる。既存B1の`effective_shape_adapter`経由の依存は維持し、B2の追加実装による依存追加とは扱わない。

```python
@dataclass(frozen=True)
class DeliveryArtifactOperations:
    generate_and_validate_vmd: Callable[[DeliveryStartContext, Path, DeliveryCancelToken], None]
    generate_and_validate_mmd_wav: Callable[[DeliveryStartContext, Path, DeliveryCancelToken], None]
    generate_and_validate_report: Callable[[DeliveryStartContext, Path, DeliveryCancelToken], None]
```

callableは指定されたstaging pathへ一つの成果物を作り、B3固有validationが完了した場合だけ正常returnする。B2はfake operationを注入してcore単体testを行う。production operationはB3で追加する。

### 8.2 path validation API

planned function:

```python
def validate_delivery_destination(
    start_context: DeliveryStartContext,
) -> ValidatedDeliveryDestination:
    ...
```

実行順は次とする。

1. `DeliveryStartContext`と`current_state.gate_status == "ready"`を確認する。
2. parentのabsolute / namespace / strict resolve / directory条件を確認する。
3. `audio_stem`、folder name、固定3成果物名を同じcomponent validatorへ通す。
4. B1のartifact名がaudio stemから再計算した固定名とexact一致することを再確認する。
5. finalとfinal内3path、最大staging componentとstaging内3pathのUTF-16絶対長を確認する。
6. finalを`lstat`し、既存entryまたはinspection不能を拒否する。
7. side effectのない`ValidatedDeliveryDestination`を返す。

validatorは例外の技術detailとuser-facing codeを分離する。少なくとも`output_parent_invalid`、`output_path_invalid`、`output_destination_collision`、`output_path_inspection_failed`を区別する。

### 8.3 staging / artifact orchestration

planned entrypoint:

```python
def orchestrate_delivery_package(
    *,
    job_id: int,
    start_context: DeliveryStartContext,
    artifact_operations: DeliveryArtifactOperations,
    pre_commit_guard: Callable[
        [DeliveryCommitGuardRequest, DeliveryCancelToken],
        DeliveryCommitAuthorization,
    ],
    cancel_token: DeliveryCancelToken,
) -> DeliveryTerminalResult:
    ...
```

- B2 APIは同期functionとする。B5がworker threadで呼び、UI threadから直接呼ばない。
- validation失敗または開始前cancelではstagingを作らない。
- `mkdtemp()`後、rootがresolved parentのdirect childであり、parentと同じ`st_dev`であることを確認する。確認不能または不一致はcleanup後に失敗する。
- artifact pathはB1固定名から構築し、callbackへ変更不可のexact pathを渡す。
- callback正常return後、B2は`lstat`でexact pathが通常のnon-reparse regular fileかつsize > 0であることを確認する。format / content validationはB3 callableの責務であり、B2で再実装しない。
- 各callbackの前後でcancelを確認する。
- 3件完了後、`os.scandir(staging)`でexact 3名だけが存在し、いずれも通常のnon-reparse regular fileであることを確認する。temporary file、subdirectory、symlink、junction、追加manifestが残る場合はcommitしない。
- artifact callbackが任意のfileをfinalへ直接書かないことは、B2がfinal pathをcallbackへ渡さないAPIと、testでfinal不在を各phaseに確認して保証する。

### 8.4 delivery専用cancel token

`DeliveryCancelToken`は`src/core/delivery_package.py`内のthread-safe core型とし、`gui_wx.worker_state.CancelToken`をimportまたは継承しない。

- lockで`cancel_requested`、current phase、active process bridgeを保護する。
- B2ではphase間cancelを扱う。
- B3が現行`run_ffmpeg_mmd_wav_cancellable()`へ直接渡せるよう、`register_process(process)` / `clear_process(process)`を実装する。別adapter方式は採用しない。
- `register_process()`後または既にprocess登録済みの状態でcancelされた場合、既存`CancelToken`と同じ2秒graceのterminate -> wait -> killをdaemon threadで実行する。B2ではcore内private helperとし、`gui_wx.worker_state`をimportしない。
- `request_cancel()`はcommit開始前ならcancelを受理して`True`を返す。
- commit開始後またはcommit済みなら成功済みcommitを取消不能として`False`を返し、finalを削除しない。
- cancel要求はterminal resultそのものではない。orchestrationがcleanupを完了して一つのterminal resultを返すまで、callerはBusy解除やjob終了を確定しない。

### 8.5 pre-commit guard

- 3成果物とexact staging内容のvalidation後、phaseを`awaiting_commit_guard`へ遷移してguardを一度だけ呼ぶ。
- requestにはpositiveな`job_id`、`start_context.current_state.start_fingerprint`、validated final directoryを入れる。
- authorizationの`job_id`と`start_fingerprint`がrequestとexact一致しなければ、`authorized`でも`delivery_commit_authorization_invalid`として拒否する。
- `decision == "authorized"`だけがcommitへ進める。
- `stale`、`invalid_job`は対応するsafe codeでfailureとし、`cancelled`、`closing`、またはtokenで受理済みcancelは`output_cancelled`のcancel terminalとする。
- guard exception、None、未知decision、型不正はfail closedにする。
- B2はcurrent GUI fingerprintを自分で再構築しない。B5のguard adapterがUI threadへ照会し、B1の`evaluate_delivery_commit_fingerprint()`とactive job / worker kind / close状態を組み合わせる。
- GUI adapterの`wx.CallAfter`、event wait、timeout、close wakeupはB5責務である。B2 core testでは同期fake guardを注入する。

### 8.6 commit線形化

cancel tokenとorchestrationは同じcommit lockを使う。

1. authorization取得後にfinal entryを再検査する。
2. commit lockを取得する。
3. lock内でcancel未受理、authorization有効、staging所有を再確認する。
4. phaseを`commit_started`へ変更する。
5. lockを保持したまま`os.rename(staging, final)`を開始し、成功 / 失敗を記録する。
6. 成功ならphaseを`committed`へ確定してからlockを解放する。
7. 失敗ならphaseを`commit_failed`へ確定してからlockを解放し、staging cleanupへ進む。

このlock取得順をcancelとcommitの唯一の順序付けにする。cancelが先にlockを取得して受理された場合はrenameを呼ばない。commitが先に`commit_started`へ入った場合、後着cancelはrename結果を上書きしない。

### 8.7 cleanup / terminal result

- cleanup対象は、このinvocationが`mkdtemp()`で作成し、まだcommitされていないexact staging pathだけである。
- final path、親directory、prefix一致だけの別directory、既存個別出力を削除しない。
- cleanup前にstored ownership、direct-child boundary、`committed == False`を確認する。
- staging自身がsymlink / reparse pointへ変化している場合はtarget treeを辿らず、directory reparse pointは`os.rmdir()`、file / symlink reparse pointは`os.unlink()`でentry自身の削除だけを試みる。通常directoryだけを`shutil.rmtree()`対象にする。
- `ignore_errors=True`で失敗を隠さず、削除後に`lstat`でabsenceを確認する。
- cleanup失敗時はprimary failure / cancelを保持し、`cleanup_status="partial_output_cleanup_failed"`、`staging_path=<残存候補>`を返す。
- cleanup成功後の`staging_path`は`None`とする。
- commit成功時は`primary_status="success"`、`committed=True`、`final_path`あり、`staging_path=None`、`cleanup_status="not_required"`、`commit_phase="committed"`だけを許す。
- cancel terminalは必ず`committed=False`、`final_path=None`とする。
- failure terminalでcommit成功を表現しない。
- raw traceback、credential、不要なstaging absolute pathを通常のuser-facing messageへ渡さない。cleanup失敗のstaging pathはinternal detailとして保持し、B5表示でそのまま露出しない。

## 9. 詳細ステップ

### Step 1: B1 API回帰固定

- B1の既存public DTO / helperを変更せず、17件のB1専用testを先に実行する。
- `build_delivery_start_context()`がstructural builderでありB2 security gateではないことをcode commentとB2 testで固定する。
- B1のartifact order、start fingerprint、projection generation分離を再確認する。

### Step 2: Windows名・長さhelper

- strict UTF-16 code unit helperを追加する。
- reserved character / control / separator / dot component / trailing / device nameを一つのpure validatorへ集約する。
- parent validationとabsolute path length validationを分離し、pure境界testを可能にする。
- astral character、superscript device name、extension付きreserved nameの境界testを先に追加する。

### Step 3: destination DTOとcollision inspection

- `ValidatedDeliveryDestination`を追加する。
- final / artifact pathを固定順tupleへ格納する。
- `lstat` resultをcollisionへ正規化し、broken symlinkや未知reparseでもabsenceと誤認しない。
- inspection permission errorをcollisionではなくinspection failureとして保持するが、いずれも処理開始は拒否する。

### Step 4: staging作成とownership

- absolute resolved parentを`mkdtemp(dir=...)`へ渡す。
- direct child、same volume、actual path lengthを確認する。
- ownershipは成功した`mkdtemp` return pathだけに付与する。
- staging作成後の全failureが共通cleanup pathへ入る構造にする。

### Step 5: injected artifact operation

- 3 callableの存在とcallabilityをstaging作成前に検証する。
- `DELIVERY_ARTIFACT_ORDER`を唯一のloop順とし、別の並びをcallerから受け付けない。
- callback前後cancel、return後generic file postcondition、最後のexact directory contentを実装する。
- B2 production codeではVMD / WAV / reportのbyte形式を解析しない。

### Step 6: authorizationとcancel state machine

- positive job ID、start fingerprint binding、allowlisted decisionをDTO validationへ入れる。
- `awaiting_commit_guard`をterminal / current phaseへ反映する。
- guard前、guard中cancel、authorization後cancel、commit lock競合をdeterministicにtestできるbarrier / event seamをtest側に用意する。
- generic `AudioWorker`のpost-task cancel判定へ依存しないterminal resultを完成させる。

### Step 7: Windows no-clobber commit

- final再検査後にcommit lock内で`os.rename()`を一度だけ呼ぶ。
- rename直前に別entryを作るtestでTOCTOU collisionを再現する。
- `os.rename`失敗時にcopy fallbackしないことをmockで確認する。
- commit成功後cancelがsuccess resultとfinalを維持することを確認する。

### Step 8: cleanupとterminal invariants

- preflight failure、artifact failure、guard denial、cancel、commit failureごとのcleanup statusを固定する。
- cleanup自体のfailureを注入し、primary statusを上書きしないことを確認する。
- terminal DTOの矛盾する組合せをconstructorで拒否する。

### Step 9: diff / boundary監査

- B3 writer、B4 report、B5 GUI / worker、B6 hardeningを先行実装していないことを確認する。
- `main_frame.py`、`app_controller.py`、`audio_worker.py`、`worker_state.py`、runtime data、dependency、docsに差分がないことを確認する。
- B2専用test、B1 /関連回帰、`compileall`、`git diff --check`を一コマンドずつ実行する。

## 10. 状態遷移 / データ契約

### 10.1 core状態遷移

```text
created
  -> validating_destination
     - invalid / collision / cancelled: terminal, no staging
  -> staging_created
  -> generating_vmd
  -> vmd_validated
  -> generating_mmd_wav
  -> mmd_wav_validated
  -> generating_report
  -> report_validated
  -> staging_contents_validated
  -> awaiting_commit_guard
     - stale / invalid job / closing / cancelled: cleanup -> terminal
     - authorized: final collision recheck
  -> commit lock arbitration
     - cancel wins: cleanup -> cancelled terminal
     - commit wins: cancel acceptance closes
  -> commit_started
     - os.rename success: committed -> success terminal
     - os.rename failure: commit_failed -> cleanup -> failed terminal
```

final directoryは`os.rename()`成功まで存在しない。stagingはExplorer等から見える場合があるが、成功成果物、個別保存履歴、final packageとして扱わない。

### 10.2 artifact operation契約

| kind | B2が渡す値 | B3が正常return前に行うこと | B2のreturn後検証 |
| --- | --- | --- | --- |
| `vmd` | start context、exact staging VMD path、cancel token | effective planから生成、production read-back validation | regular / non-reparse / non-empty / exact path |
| `mmd_wav` | start context、exact staging WAV path、cancel token | original sourceから生成、MMD WAV validation、source identity前後確認 | regular / non-reparse / non-empty / exact path |
| `report` | start context、exact staging report path、cancel token | same snapshot / timestampでUTF-8 report生成・validation | regular / non-reparse / non-empty / exact path |

B2 testのfake operationはこのseamだけを検証し、実writer成功の証拠にはしない。

### 10.3 authorization不変条件

- guard request job IDはorchestration job IDと一致する。
- request fingerprintはB1 start fingerprintと一致する。
- authorizationは同じ2値をechoする。
- `authorized`以外はcommit不可である。
- authorizationは1 invocation内で一回だけ使い、別job / 別fingerprintへ再利用しない。
- `projection_generation`、UI表示文字列、staging pathをauthorization identityにしない。

### 10.4 terminal result不変条件

| 状態 | committed | primary | final_path | staging_path | cleanup |
| --- | --- | --- | --- | --- | --- |
| success | `True` | `success` | exact final | `None` | `not_required` |
| pre-staging failure | `False` | `failed` / `cancelled` | `None` | `None` | `not_required` |
| staging後failure + cleanup成功 | `False` | `failed` / `cancelled` | `None` | `None` | `completed` |
| staging後failure + cleanup失敗 | `False` | 元の`failed` / `cancelled` | `None` | 残存候補 | `partial_output_cleanup_failed` |
| commit成功後late cancel | `True` | `success` | exact final | `None` | `not_required` |

cleanup failureはprimary errorへ置き換えず併記する。commit成功とcancelledを同時に表現しない。

#### 10.4.1 primary error code写像

| failure | primary status | primary error code |
| --- | --- | --- |
| parent不正 / path不正 | `failed` | `output_parent_invalid` / `output_path_invalid` |
| final既存 / rename時TOCTOU | `failed` | `output_destination_collision` |
| `lstat`不能 | `failed` | `output_path_inspection_failed` |
| staging作成 / boundary / volume不成立 | `failed` | `output_staging_create_failed` / `output_staging_invalid` |
| VMD operation | `failed` | B3の`vmd_write_failed` / `vmd_validation_failed` |
| MMD WAV operation | `failed` | B3の`mmd_wav_write_failed` / `mmd_wav_validation_failed` / `source_audio_changed` |
| report operation | `failed` | B3 / B4の`report_write_failed` / `report_validation_failed` |
| staging exact-content不成立 | `failed` | `delivery_staging_contents_invalid` |
| stale fingerprint | `failed` | `delivery_state_stale` |
| job不一致 | `failed` | `delivery_job_invalid` |
| guard exception / malformed authorization | `failed` | `delivery_commit_guard_failed` / `delivery_commit_authorization_invalid` |
| rename失敗かつfinal absent | `failed` | `delivery_commit_failed`。lock / permissionを安全に判別できる場合だけ既存`output_file_locked` / `output_permission_denied`へ細分化 |
| commit前cancel / closing | `cancelled` | `output_cancelled` |

B3 / B4 operationがtyped error codeを返すまでは、B2のfake operation testで上表の伝播契約だけを固定する。raw exception文字列からcodeを推測しない。

### 10.5 B2 / B6責務境界

B2が実装する最低限のproduction責務:

- all-or-nothing staging / no-clobber commit
- final collisionの全entry拒否
- phase間cancelとcommit線形化
- owned staging cleanup
- terminal resultとcleanup status
- fake operationによるdeterministic core test

B6へ残すhardening責務:

- actual symlink / junction / reparse pointを利用できる環境での実filesystem matrix
- locked / readonly / permission / antivirus競合等のWindows fault matrix
- staging entryが外部から差し替えられるraceの追加防御検証
- B5接続後のwindow close、shutdown、late callbackとの横断回復
- cleanup failure表示と診断記録の最終調整
- B2契約で漏れたfailureのrepair

B6はB2のno-clobber、terminal、cancel semanticsを新規発明せず、実環境・横断failureでhardeningする。

## 11. テスト方針

### 11.1 B2新規test

`tests/test_ms25_b2_windows_paths.py`:

- valid Japanese / Latin / space / leading dot / astral Unicodeの保持
- empty、`.`、`..`、separator、`<>:"/\\|?*`、U+0000〜U+001F、unpaired surrogate拒否
- trailing space / dot拒否
- `CON` / `con.txt` / `NUL.tar.gz` / `COM1`〜`COM9` / `LPT1`〜`LPT9`
- `COM¹`〜`COM³` / `LPT¹`〜`LPT³` / `CONIN$` / `CONOUT$` / `CLOCK$`
- UTF-16 component 255受理 / 256拒否
- emojiを2 code unitとして数える境界
- audio stem + `_report.txt`を含む生成file component境界
- absolute path 240受理 / 241拒否
- relative、drive-relative、device namespace、missing parent、parent=file拒否
- final absent受理
- empty / non-empty directory、file、symlink、broken symlinkのcollision
- reparse attributeを持つ`lstat` resultのcollision
- permission / inspection errorのfail-closed

actual symlink作成が権限やDeveloper Modeにより不可能な環境では、そのcaseだけ理由付きskipを許し、`lstat` injection testを必須にする。actual junction / reparse pointの環境依存matrixはB6と手動境界へ記録し、B2で未実施なのに検証済みとしない。

`tests/test_ms25_b2_delivery_orchestration.py`:

- stagingがfinalと同じresolved parent直下に作られる
- staging名がopaqueでfolder / audio stemを含まない
- VMD -> WAV -> reportのexact call order
- 各callbackがexact staging pathだけを受ける
- callback中はfinalが存在しない
- callback正常returnでもmissing / empty / directory / symlink / reparse artifactなら失敗
- extra file / temporary / subdirectoryが残れば失敗
- fake operation successでfinalにexact 3 filesだけが現れる
- B2追加部分がwx / GUI / SettingsStoreに依存せず、artifact writerの新規import / 直接呼出を行わない。既存B1の`effective_shape_adapter`経由の依存は維持する
- `os.replace` / `shutil.move` / copy fallbackがfinal commitに使われない

`tests/test_ms25_b2_delivery_commit.py`:

- guardは3成果物validation後に一度だけ呼ばれる
- requestのjob ID / start fingerprint / final path
- authorization success
- stale / invalid job / closing / cancelled denial
- authorization job mismatch / fingerprint mismatch / unknown decision / exception
- guard待機前cancel、guard中cancel、authorization後cancel
- cancelがcommit lockを先取した場合rename未実行
- commitがlockを先取した場合late cancelがsuccessを上書きしない
- commit開始後rename success / failure
- preflight後とrename直前にdestinationを作るTOCTOU collision
- collision targetのfile bytes / directory contentsが不変
- cleanup success / cleanup failure
- primary status、error code、cleanup status、commit phase、path fieldの全不変条件
- committed finalをcleanupしない

### 11.2 B2実装後の実行順

各commandは一つずつ実行し、pass表示とprocess exit codeを別々に記録する。

1. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b2_windows_paths.py`
2. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b2_delivery_orchestration.py`
3. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b2_delivery_commit.py`
4. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b2_windows_paths.py tests/test_ms25_b2_delivery_orchestration.py tests/test_ms25_b2_delivery_commit.py`
5. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py`
6. `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms20_b6_diagnostic_report.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms21_b5_effective_output_identity.py`
7. `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms21_b7_audio_worker_terminal.py`
8. `.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py`
9. `.\.venv\Scripts\python.exe -m compileall -q src tests`
10. `git diff --check`

full pytestはB2の影響範囲、targeted結果、実装中の変更量から判断する。B2で未実施なら未実施と記録し、B7の全体回帰完了を先取りしない。

### 11.3 手動確認境界

- B2はvisible GUIを追加しないため、manual GUI確認を受け入れ必須にしない。
- Windows実filesystemのfile / empty directory / non-empty directory collisionは自動testで確認する。
- symlink / junction作成が環境権限に依存する場合、実施できた種類とskipした種類を分ける。
- folder dialog、Busy、cancel button、window closeはB5 / B6。
- 生成VMD / WAV / reportの実内容はB3 / B4。
- 実MMDはMS26、onefile / releaseはMS27。

## 12. 受け入れ条件

### 12.1 Windows path / destination

- [ ] parentはabsolute、existing、resolved directoryであり、実staging作成でwriteabilityを確認する。
- [ ] `audio_stem`、folder name、固定成果物名が同一component validatorを通る。
- [ ] 禁止文字、control、separator、`.` / `..`、末尾space / dot、予約device名を暗黙修正せず拒否する。
- [ ] Unicodeを保持し、UTF-16 component 255 / absolute path 240上限をexactに検証する。
- [ ] finalはparent直下1 componentである。
- [ ] empty / non-empty directory、file、symlink、broken symlink、reparse pointを含む既存entryを変更せず拒否する。
- [ ] inspection不能をabsent扱いしない。

### 12.2 staging / artifact boundary

- [ ] stagingはfinalと同じresolved parentのdirect childへ競合なく作成される。
- [ ] stagingは承認済みfinal名を使わず、成功成果物として扱われない。
- [ ] operation順はVMD、MMD用WAV、reportへ固定される。
- [ ] B2はwriterを実装せず、B3のgenerate-and-validate operationを注入できる。
- [ ] 各operation後に通常regular / non-reparse / non-empty fileを確認する。
- [ ] commit前のstagingには固定3 files以外が存在しない。
- [ ] finalへ生成途中のfileを直接書かない。

### 12.3 authorization / commit / cancel

- [ ] 3成果物validation後に`awaiting_commit_guard`へ入る。
- [ ] guard request / authorizationがjob IDと開始fingerprintにexact bindingされる。
- [ ] `projection_generation`をcommit authorization identityに使わない。
- [ ] authorization未取得、stale、invalid job、closing、cancelでrenameを呼ばない。
- [ ] final再検査後も`os.rename()`自体のno-clobber失敗でTOCTOU collisionを保護する。
- [ ] final commitに`os.replace`、`shutil.move`、copy fallbackを使わない。
- [ ] commit前に受理したcancelはrenameせずcleanupへ進む。
- [ ] commit開始後またはcommit成功後のcancelはrename結果を上書きせず、finalを削除しない。

### 12.4 cleanup / terminal

- [ ] cleanupはowned stagingだけを対象とする。
- [ ] final、親directory、既存個別出力、似たstaging名を削除しない。
- [ ] cleanup failureをprimary failure / cancelと別fieldで保持する。
- [ ] success / failure / cancelの全経路が一つの`DeliveryTerminalResult`を返す。
- [ ] `committed`、`final_path`、`staging_path`、primary status / error、cleanup status、commit phaseに矛盾がない。
- [ ] committed successとcancelledを同時に報告しない。

### 12.5 scope / verification

- [ ] B3 writer、B4 report拡張、B5 GUI / worker、B6 hardeningを先行実装していない。
- [ ] 個別保存導線と履歴を変更していない。
- [ ] runtime user data、dependency、build / package file、他文書に差分がない。
- [ ] B2新規testと指定回帰がpass表示かつprocess exit code `0`である。
- [ ] `compileall -q src tests`と`git diff --check`がprocess exit code `0`である。
- [ ] 実施していないmanual GUI、actual reparse matrix、実MMD、Python 3.11 / 3.12、onefile / releaseを未検証と報告する。

## 13. リスクと対策

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS25-B2-R1 | `os.replace`や`shutil.move`で既存finalを置換またはcopy fallbackする | P1候補 | Windows `os.rename`一回、同一resolved parent、fallback禁止をcode / testへ固定 |
| MS25-B2-R2 | `Path.exists()`がbroken symlinkを見落とし、既存entryへcommitする | P1候補 | `os.lstat`成功を全てcollisionとし、FileNotFoundErrorだけをabsentとする |
| MS25-B2-R3 | 事前検査後のTOCTOUで別processのentryを破壊する | P1候補 | commit直前再検査 + Windows no-clobber rename。失敗後final存在ならcollisionへ正規化 |
| MS25-B2-R4 | generic `AudioWorker`がcommit済みresultをcancel callbackへ変換する | P1候補 | B2 terminal resultをfilesystem正本とし、B5へdelivery専用worker terminal分岐を必須引継ぎ |
| MS25-B2-R5 | authorizationが別job / 別fingerprintから再利用される | P1候補 | request / response双方へjob IDとstart fingerprintを入れ、exact mismatchをfail closed |
| MS25-B2-R6 | cancel checkとrenameの間にraceがあり、cancelledとcommittedを同時報告する | P1候補 | 同じcommit lock内でcancel確認、`commit_started`遷移、rename、結果確定を順序付け |
| MS25-B2-R7 | cleanupがfinalや他jobのstagingを削除する | P1候補 | `mkdtemp` return pathのownership、direct-child確認、committed禁止、exact path限定 |
| MS25-B2-R8 | componentをPython文字数で数え、emoji等でWindows上限を超える | P2候補 | strict UTF-16LE code-unit helperと255 / 240境界test |
| MS25-B2-R9 | reserved device nameのextension / case / superscript variantを受理する | P2候補 | base name正規化とMicrosoft列挙値のtable-driven test |
| MS25-B2-R10 | B2がB3 writer validationを再実装し責務が二重化する | P2候補 | generate-and-validate callable + B2 generic file postconditionに分離 |
| MS25-B2-R11 | cleanup failureがcancelまたは元failureへ吸収される | P2候補 | primary / cleanup separate fields、残存staging pathはinternal detailとして保持 |
| MS25-B2-R12 | B2とB6のcleanup / recovery責務が重複する | P2候補 | B2をminimum production transaction、B6をactual Windows / shutdown / race hardeningへ固定 |
| MS25-B2-R13 | parent writeabilityを`os.access`だけで誤判定する | P2候補 | `mkdtemp`の実createをauthoritative gateにする |
| MS25-B2-R14 | staging内temporary / extra artifactをfinalへ含める | P2候補 | commit前exact 3 regular files検査 |
| MS25-B2-R15 | stagingの可視性をfinal成功と誤認させる | P3候補 | opaque staging、UI成功通知はcommitted terminal後だけ。B5 / B7へ説明を引継ぐ |
| MS25-B2-R16 | Index / B1 planの状態欄がlive B1実装と一致しない | P3解消 | メイン側でIndex / B1 planをB1実装・検証済みの状態へ同期済み。B2実装では他文書を変更しない |

### 13.1 P1 / P2 / P3自己監査と修正履歴

初回設計案を現行code / testと再照合し、次を本文へ修正した。

| finding | 初期問題 | 本文での修正 | 状態 |
| --- | --- | --- | --- |
| P1-1 | generic `AudioWorker`のtask後cancelがcommit済みsuccessをcancelへ上書きできる | §8.4、§8.6、§10.4でdelivery terminalとcommit lockをfilesystem正本化 | 解消 |
| P1-2 | pre-commit guardがbooleanだけでは別job / 別fingerprintのauthorizationを誤用できる | §8.1、§8.5、§10.3でrequest / authorization双方をjob ID + start fingerprintへbinding | 解消 |
| P1-3 | rename APIとfallbackが未固定だとexisting destinationを置換し得る | §6.5、§8.6でWindows `os.rename`一回、`os.replace` / move / copy fallback禁止 | 解消 |
| P2-1 | Windows予約名にextension、superscript digit、console device variantの漏れがあり得る | §6.2と§11.1へexact set / table-driven testを追加 | 解消 |
| P2-2 | B1 structural contextをvalidated destinationと誤認し得る | §6.1、§8.2でB2 validatorをauthoritative gate化 | 解消 |
| P2-3 | cleanupがprefix一致だけで他pathを削除する余地があった | §6.4、§8.7で`mkdtemp` ownershipとexact direct-child boundaryを固定 | 解消 |
| P2-4 | B2 / B3 / B6のvalidation・cleanup責務が重複していた | §8.3、§10.2、§10.5でgeneric / format / hardeningを分離 | 解消 |
| P2-5 | delivery tokenのprocess接続がdirect APIとadapterの二択で未確定だった | §8.4で現行cancellable runner互換の`register_process` / `clear_process`へ固定 | 解消 |
| P2-6 | control文字をUnicode category全体へ広げるとWin32正本より過剰拒否になる | §6.2、§11.1をU+0000〜U+001Fへ限定 | 解消 |
| P2-7 | B1現行の`effective_shape_adapter`経由writer依存と、B2追加実装のwriter非依存条件が区別されていなかった | §8.1、§11.1をB2追加部分の新規import / 直接呼出禁止へ限定 | 解消 |
| P3-1 | 実行予定commandの先頭path表記が不正だった | §11.2を`.\.venv`へ修正 | 解消 |
| P3-2 | B1実装済みのlive状態とIndex / B1 plan状態欄が不一致 | メイン側でIndex / B1 planの状態欄をB1実装・検証済みへ同期 | 解消 |
| P3-3 | §6.1に解消済みの状態文書未同期が残っていた | §6.1をIndex / B1 plan同期済みの現行状態へ更新 | 解消 |

計画本文にP1 / P2 / P3の残存はない。B2 core実装判断を変える未解決事項はなく、ユーザー判断が必要な未確定分岐もない。

## 14. Codex実装時の注意

- 実装開始時にlive Git、現行HEAD、user-owned差分を再確認する。
- コマンドは一つずつ実行し、pipeline、chain、parallel shellを使わない。
- B1既存API / testを先に回帰し、B2都合でfingerprint schemaやartifact namingを変更しない。
- `DeliveryStartContext`のraw parent / folderを直接filesystem APIへ渡さず、B2 validatorを必ず通す。
- Windows名をsanitizeしない。無効名はstructured errorで返し、別名はユーザーに選ばせる。
- `os.path.exists()`だけでcollisionを判定しない。
- final commitに`os.replace`、`Path.replace`、`shutil.move`、copytreeを使わない。
- final directoryを先に作成してfileを順次追加しない。
- stagingは必ずfinalと同じresolved parentへ作る。
- artifact callbackへfinal pathを渡さない。
- B2でVMD / WAV / reportのactual writerやformat parserを先行実装しない。
- worker threadからGUI stateを読まない。B2 guardは注入境界だけを提供する。
- commit authorizationはjob ID / start fingerprint exact一致を毎回検証し、一回だけ使用する。
- `projection_generation`をcommit guardへ追加しない。
- commit lock外で「cancelなし」と判定しただけでrenameへ進まない。
- commit成功後にcancel / shutdown cleanupでfinalを削除しない。
- cleanupはowned staging以外へ拡張しない。parent rootやcomputed broad pathをrecursive delete対象にしない。
- cleanup exceptionを握りつぶして`completed`と記録しない。
- generic `AudioWorker`の現行post-task cancel semanticsをB2 success判定へ使わない。
- 個別VMD / WAV / report保存履歴とSettingsStoreを更新しない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読書き、コピー、stageしない。
- dependency、network、Qt / PySide6を追加しない。
- B2 testでfake writerが通っても実VMD / WAV / report生成済みとは報告しない。
- manual GUI、actual junction / reparse、実MMD、Python 3.11 / 3.12、onefile確認を実施していなければ未検証と記録する。
- diff自己監査でB3 / B4 / B5 / B6 / B7の先行実装がないことを確認する。
- stage、commit、merge、push、releaseは別の明示承認まで行わない。

### 14.1 後続Blockへの引き継ぎ

- B3:
  - `DeliveryArtifactOperations`へactual VMD / MMD WAV / report generate-and-validate callableを提供する。
  - VMD read-back validator、source audio identity前後確認、WAV / report形式validationを所有する。
- B4:
  - 同じ開始snapshotを使い、profile未使用・既定morph setを含むidentity欄をreportへ必須化する。
- B5:
  - destination dialog後にB1 stateを再captureし、B2 validatorを通す。
  - UI thread上でcurrent fingerprint、active job ID、worker kind、cancel / closeを確認し、B2 authorization DTOを返す。
  - delivery専用worker terminalを使い、generic task後cancelでcommitted successを上書きしない。
  - Busy解除、個別保存履歴非変更、session-only parent、window close待機を接続する。
- B6:
  - actual Windows collision / reparse / locked / cleanup / close matrixを実行し、B2 transactionをhardeningする。
- B7:
  - full / cross-boundary regressionとREADME / 正文仕様 / routing同期を行う。
- MS26 / MS27:
  - 実MMD確認とpackage / release readinessをそれぞれ別工程で扱う。
