# MS25-B1 Implementation Plan

## 1. 文書情報

- 文書名: MS25-B1 出力契約・現在状態gate Implementation Plan
- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B1 出力契約・現在状態gate
- 作成日: 2026-08-28
- 状態: B1実装・自動検証済み。B1のproduction code / test codeを実装し、可視GUI action、runtime user data、設定、依存関係は変更していない
- 対象ブランチ: `feature/MS25-implementation`
- 計画作成時HEAD: `61a2182 Finalize MS24 Closeout A`
- 前提: MS24 Closeout A、`docs/Implementation_Plan/MS25_Block_Breakdown.md`
- 本文書の変更権限: 本文書の新規作成だけ。既存文書、production code、test code、GUI、設定、依存関係は変更しない
- ユーザー判断待ち: なし。固定命名、WARNING確認、ERROR拒否、source identity、fingerprint、`projection_generation`の契約は現行資料から確定できる
- ユーザー判断済み: 既存の長時間処理確認を採用する。300秒超入力ではdestination選択後・Busy / worker開始前に一度だけ確認し、経過時間timerとworker開始後の再確認は追加しない
- 2026-08-30実装前チェック補正: `prepare_current_effective_output()`の戻り値3要素を同一capture内で保持し、snapshot builderへ明示注入して再prepareを防ぐ手順・テストを追加した。MS20以降IndexのMS25現在地・routingと、長時間確認テストの実行順も同期した
- 実施済み: B1専用pytest、関連回帰、全pytest、`compileall`、`git diff --check`。実装コミット: `a41f0a0 Implement MS25-B1 delivery state gate`
- 未実施: 手動GUI確認、実MMD確認、Python 3.11 / 3.12確認、package / release確認

## 2. 背景

MS25は、現在の編集結果からVMD、入力音声からMMD用WAV、同じ時点の診断snapshotからレポートを再生成し、一つの専用directoryへ確定する機能である。B1はfilesystem transactionやGUI導線を実装する前に、どの状態を一括出力の正本として固定し、どの状態では開始またはcommitを拒否するかを実装可能なcore契約へ落とし込む。

現行実装には次の境界がある。

- `MainFrame._build_current_ui_sync_context()`は、現在のbase入力とcanonical adjustmentから一つの`UiSyncContext`を構築し、同一output stateではcacheを再利用する。
- `MainFrame.prepare_current_effective_output()`は、解析中、解析結果無効、再解析待ち、VMD保存準備未成立を`not_applicable`とし、解決失敗を`invalid`、成功時を`ready`として現在の`EffectiveShapePlan`を返す。
- `MainFrame.build_and_store_output_diagnostics_snapshot()`は、渡された同じ`EffectiveShapePlan`から`OutputDiagnosticsSnapshot`を構築し、呼出しごとに`projection_generation`を増分する。
- `OutputDiagnosticsSnapshot.saveability.vmd_save_allowed`は、既存VMD保存条件とdiagnostics ERRORの両方を反映する。WARNINGは`warning_codes`へ保持し、保存自体は直ちに禁止しない。
- `request_save_vmd()`は、WARNINGがある場合に`save_state_fingerprint`単位で確認し、`UiState.confirmed_warning_save_state_fingerprint`へ承認済みidentityを保持する。拒否時は保存dialogとwriterへ進まない。
- standalone診断レポート保存はVMD saveabilityから独立し、ERROR snapshotでも保存できる。MS25一括出力のERROR拒否を、この既存導線へ波及させてはならない。
- `ms21-effective-output-v1` fingerprintは、effective morph frames、effective tails、VMD model name、安定したdiagnostic identity等から構築される。Whisper management状態、表示文、`projection_generation`はfingerprintへ含まれない。
- `EffectiveShapePlan`と`OutputDiagnosticsSnapshot`はfrozen DTOとtupleを中心に構成される。一方、`VowelTimingPlan`はfrozen dataclassだが内部fieldがlistであるため、immutable開始contextへそのまま保持する正本にはしない。
- `AudioInputInfo.source_path`と`AudioProbeResult.source_path`は元の入力音声を示す。MMD用WAVは`probe_result.source_path`から生成し、`selected_analysis_wav`を入力にしない。
- `AudioProbeResult`はsize、duration、format、audio streamを持つが、`mtime_ns`とfile identityを持たない。B1で開始時source identityを別DTOとして取得する必要がある。
- `MMD_WAV_SPEC`は`pcm_s16le / 44100Hz / stereo`で固定されている。`locate_ffmpeg_tools()`はrepo-local、bundled、PATHの順でFFmpegを解決する。
- B1時点では一括出力action、delivery worker、staging、VMD read-back validator、no-clobber commitは存在しない。

## 3. 目的

MS25-B1では、次をproduction codeで表現可能な契約として固定する。

1. 承認済みの3成果物名と既定directory名を、入力音声stemから決定的に構築する。
2. 現在の`EffectiveShapePlan`、同じplanから構築した`OutputDiagnosticsSnapshot`、元音声probe / source identity、MMD WAV仕様、解決済みFFmpeg、writer parameters、resolved ordered morph names、開始fingerprintを一つのimmutable開始contextへ束ねる。
3. diagnostics ERROR、無効な解析状態、pending / rebuild、source不整合、FFmpeg未解決、fingerprint欠落をfail-closedで拒否する。
4. diagnostics WARNINGを既存のVMD保存と同じfingerprint単位で確認対象とし、確認前にdestination選択、Busy、worker開始へ進ませない契約を返す。
5. `save_state_fingerprint`をfilesystem commit guardのsemantic identityとし、`projection_generation`をUI投影 / late-result discard専用に維持する。
6. B2以降が可変`UiState`や表示文字列を再読せず、B1の開始contextだけを入力にできる境界を用意する。

B1完了は一括出力機能の利用可能化を意味しない。B1はcontract、current-state capture、pure gate、pure fingerprint recheckまでを所有し、filesystem transactionとGUI実行導線は後続Blockへ残す。

## 4. In Scope

- `src/core/delivery_package.py`の新規作成
- delivery成果物名のimmutable DTOと決定的な命名helper
- 生成順序`VMD -> MMD用WAV -> 診断レポート`の固定contract
- 元音声のresolved path、size、`mtime_ns`、取得可能なfile identityを保持するimmutable DTO
- source identity取得と、`AudioInputInfo` / `AudioProbeResult` / 実fileの整合検証
- B1 current-state candidate、start gate result、immutable start contextのDTO
- B1 start gateのpure evaluator
- diagnostics ERROR / WARNINGとfingerprintのgate
- 同一fingerprintの既存WARNING確認identity再利用
- commit前に再構築したsnapshotと開始fingerprintを比較するpure evaluator
- `projection_generation`をcontextへ記録しつつcommit判定へ使用しない契約
- 既存の長時間処理確認をB5へ接続する契約。入力音声が300秒を超える場合は、destination選択後かつBusy / worker開始前に一度だけ確認し、経過時間timerは新設しない
- `MainFrame`で一つの`UiSyncContext`、一つの`EffectiveShapePlan`、一つの`OutputDiagnosticsSnapshot`を同じcapture内で作る非表示adapter
- B1専用core / adapter tests
- 直接影響する既存diagnostics、fingerprint、VMD save、report save、MMD WAV source roleの回帰確認

## 5. Out of Scope

- 一括出力button、menu、folder dialog、進捗dialog、ユーザー向け文言
- Busy遷移、delivery worker、cancel、late callback、window close統合
- 親directory / folder名の完全なWindows validation
- component 255 / absolute path 240 UTF-16 code unit制限の実装
- staging directory作成、成果物生成、成果物validation、cleanup
- no-clobber rename、commit線形化点、TOCTOU対策
- VMD writer / VMD read-back validatorの実装
- MMD用WAV生成前後のsource identity再確認
- diagnostic report形式の拡張、profile未使用・既定morph set欄の必須化
- delivery terminal result
- 個別保存履歴またはbatch parent directoryの保存
- `UiState`へのdelivery専用永続field追加
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読書き・変更
- README、配布用readme、Pipeline / GUI / Error / VMD仕様の実装済み同期
- 実MMD確認（MS26）
- PyInstaller onefile、ZIP、artifact、release readiness（MS27）
- 新規依存関係、cloud ASR、background通信、Qt / PySide6

## 6. 前提条件

### 6.1 確定済み命名

元音声のcase-preservingな`Path.stem`を`audio_stem`とし、次を固定する。

```text
既定directory名: <audio_stem>_MMD
VMD:             <audio_stem>_lip.vmd
MMD用WAV:        <audio_stem>_mmd.wav
診断レポート:    <audio_stem>_report.txt
```

B1は文字列の決定性、suffix、拡張子、Unicode保持を実装する。Windows予約名、不正文字、path separator、末尾dot / space、component長、絶対path長、既存destination collisionはB2のvalidation責務とする。B1で暗黙ASCII化、切詰め、置換、連番suffix付与を行わない。

ユーザーが編集できるのはdelivery directory名であり、3成果物名は編集後directory名から再計算しない。生成順序は`VMD -> MMD用WAV -> 診断レポート`へ固定する。B3は各段階で生成・validationを完了してから次へ進み、3件完了後だけB2のcommit工程へ渡す。

### 6.2 audio role

- source audio: `AudioInputInfo.source_path`および`AudioProbeResult.source_path`
- internal analysis WAV: `selected_analysis_wav.analysis_wav_path`
- MMD-use WAV: source audioを`MMD_WAV_SPEC`へ変換したdelivery成果物

B1 gateでは元音声とprobeの存在・identityを確認する。`UiState.mmd_wav_export_ready`はstandalone MMD WAV button用であり、delivery sourceの正本判定へ流用しない。内部解析WAVはMMD用WAVのsource identityにしない。

### 6.3 WARNING / ERROR

- `snapshot.saveability.vmd_save_allowed == False`、`blocking_codes`非空、effective output不成立のいずれかは一括出力をblockする。
- `warning_codes`非空かつ`confirmed_warning_save_state_fingerprint`が現在fingerprintと不一致の場合、結果は`warning_confirmation_required`とする。
- WARNING承認済みfingerprintが一致する場合だけ次gateへ進める。
- WARNING拒否は承認済みfingerprintを新規設定せず、destination dialog、Busy、worker、filesystem mutationを開始しない。
- 一括出力のERROR拒否は`request_save_diagnostic_report()`、diagnostics snapshot、個別保存履歴を変更しない。
- package専用WARNING確認dialogの文面とcontroller接続はB5で実装する。B1は確認要否をstructured resultで返す。

### 6.4 fingerprint / projection generation

- schema `ms21-effective-output-v1`を変更しない。
- Whisper management / availability / progress等をfingerprintへ追加しない。
- `DeliveryStartContext.current_state.start_fingerprint`は開始snapshotの`save_state_fingerprint`と完全一致させる。
- `projection_generation`は開始snapshotからcontextへ記録するが、commit guardの一致条件にしない。
- commit前snapshotのfingerprint欠落、saveability ERROR、開始fingerprintとの不一致はfail-closedとする。
- active job ID、worker kind、cancel / close状態を含む最終authorizationはB5が所有する。B1のcommit evaluatorはsemantic fingerprint一致だけを判定する。

### 6.5 source identity

`SourceAudioIdentity`は少なくとも次を保持する。

- `resolved_path: Path`
- `size_bytes: int`
- `mtime_ns: int`
- `device_id: int | None`
- `file_id: int | None`
- `file_attributes: int | None`

標準ライブラリの`Path.resolve(strict=True)`と`os.stat()`を使う。`st_dev` / `st_ino` / `st_file_attributes`が利用可能な場合はfile identityとして保持し、取得できない値は`None`とする。source audioのsymlink / junction等をB1で新たに一律禁止せず、現行入力受理を維持して解決先のregular fileをidentity正本とする。

B1開始時は次をfail-closedで確認する。

- `AudioInputInfo.source_path`と`AudioProbeResult.source_path`が同じfileを指す。
- 解決先が存在するregular fileである。
- 実file sizeと`AudioProbeResult.file_size_bytes`が一致する。
- identity captureに失敗した場合、部分contextを返さない。

content hashは計算しない。同一size、同一`mtime_ns`、同一file identityを意図的に維持したbyte置換を検出保証しない。MMD用WAV生成直前と検証後の再確認はB3で実装する。

### 6.6 immutableの意味

- DTOは`@dataclass(frozen=True)`を使う。
- sequenceはtupleへ正規化する。
- 可変`UiState`、view、controller、dialog、worker、cancel tokenをcontextへ保持しない。
- list fieldを持つ現行`VowelTimingPlan`を開始contextへ直接保持しない。timing planの成立はgateで確認し、成果物正本はimmutable `EffectiveShapePlan`と`OutputDiagnosticsSnapshot`へ固定する。
- `Path`、frozen `AudioProbeResult`、frozen `MmdWavSpec`、validated morph-name tupleを保持する。

## 7. 対象ファイル

### 7.1 B1実装時の主変更対象

| 種別 | ファイル | B1責務 |
| --- | --- | --- |
| 新規 | `src/core/delivery_package.py` | 命名DTO、source identity、current-state candidate、start gate、immutable start context、semantic commit fingerprint evaluator |
| 既存変更候補 | `src/core/__init__.py` | GUI側が`src.core`公開namespaceからB1 APIを使う場合だけexportを追加する |
| 既存変更 | `src/gui_wx/main_frame.py` | 可視UIを追加せず、同一`UiSyncContext`からeffective plan、snapshot、ordered morph namesを一回でcaptureするB1 adapterを追加する。source identityのstatとFFmpeg解決は担当しない |
| 新規 | `tests/test_ms25_b1_delivery_contract.py` | 命名、source identity、DTO不変性、pure gate、commit fingerprint契約 |
| 新規 | `tests/test_ms25_b1_current_state_gate.py` | `MainFrame` adapter、同一plan / snapshot、WARNING / ERROR、再投影、既存確認identityとの接続 |

### 7.2 関連確認対象。B1では原則変更しない

- `src/core/effective_shape_plan.py`
- `src/core/output_diagnostics.py`
- `src/core/audio_input.py`
- `src/core/audio_probe.py`
- `src/core/mmd_wav_export.py`
- `src/core/ffmpeg_locator.py`
- `src/core/pipeline.py`
- `src/core/diagnostic_report.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/worker_state.py`
- `src/vmd_writer/writer.py`

`output_diagnostics_adapter.py`の現行APIだけで同一planからsnapshotを作れるため、B1では原則変更しない。変更が必要になった場合は、delivery固有stateを既存diagnostics schemaへ追加せず、B1 adapterの明示入力不足を補う最小変更に限定する。

### 7.3 B1では変更しないファイル

- `src/gui_wx/app_controller.py`: package action、WARNING dialog接続、destination dialog、worker開始はB5
- `src/gui_wx/ui_state.py`: delivery専用state、保存先履歴、INI keyは追加しない
- `src/gui_wx/audio_worker.py` / `worker_state.py`: delivery kindとterminal contractはB5
- `src/core/diagnostic_report.py`: identity必須欄の拡張はB4
- `src/core/mmd_wav_export.py`: source再確認とstaging adapterはB3
- `src/vmd_writer/writer.py`: VMD生成・validationはB3
- `README.md`、`readme_mmdautolip.txt`、正文仕様、routing文書: 実装・検証後のB7
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`
- `pyproject.toml`、PyInstaller spec、build script、license文書

## 8. 実装方針

### 8.1 B1 core API

`src/core/delivery_package.py`へ、少なくとも次のplanned APIを置く。実装時に同等の名前へ変更する場合も、fieldと責務を弱めない。

```python
@dataclass(frozen=True)
class DeliveryArtifactNames:
    audio_stem: str
    default_directory_name: str
    vmd_file_name: str
    mmd_wav_file_name: str
    report_file_name: str

@dataclass(frozen=True)
class SourceAudioIdentity:
    resolved_path: Path
    size_bytes: int
    mtime_ns: int
    device_id: int | None
    file_id: int | None
    file_attributes: int | None

@dataclass(frozen=True)
class DeliveryCurrentState:
    effective_shape_plan: EffectiveShapePlan
    diagnostics_snapshot: OutputDiagnosticsSnapshot
    audio_probe: AudioProbeResult
    source_identity: SourceAudioIdentity
    mmd_wav_spec: MmdWavSpec
    ffmpeg_path: Path
    writer_parameters: VmdWriterParameters
    output_morph_names: tuple[str, ...]
    artifact_names: DeliveryArtifactNames
    start_fingerprint: str
    projection_generation: int
    artifact_order: tuple[Literal["vmd", "mmd_wav", "report"], ...]
    gate_status: Literal["ready", "warning_confirmation_required"] = "ready"

@dataclass(frozen=True)
class DeliveryStartGateResult:
    status: Literal["ready", "warning_confirmation_required", "blocked"]
    blocking_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    fingerprint: str | None
    candidate_state: DeliveryCurrentState | None

@dataclass(frozen=True)
class DeliveryStartContext:
    current_state: DeliveryCurrentState
    parent_directory: Path
    folder_name: str
    report_generated_at: datetime

@dataclass(frozen=True)
class DeliveryCommitFingerprintResult:
    allowed: bool
    reason_code: str | None
    current_fingerprint: str | None
```

planned function責務:

- `build_delivery_artifact_names(source_path)`は固定4名を構築する。3成果物の生成順序は定数`("vmd", "mmd_wav", "report")`として別に固定する。
- `capture_source_audio_identity(source_path)`はregular fileのresolved identityを取得する。
- `evaluate_delivery_start_gate(...)`は明示入力だけからstructured resultを返し、GUIやfilesystem出力を変更しない。`candidate_state`は`ready`と`warning_confirmation_required`で保持し、`blocked`では`None`とする。
- `build_delivery_start_context(...)`は`ready`なcurrent stateと、B5が取得しB2 core validatorが承認したdestination selection、timezone-awareなreport時刻だけを束ねる。
- `evaluate_delivery_commit_fingerprint(start_context, current_snapshot)`はsaveabilityとfingerprintだけを再確認し、`projection_generation`を比較しない。

`DeliveryStartContext`はstaging path、final path、cancel token、job ID、commit authorization、terminal resultを持たない。これらはB2 / B5の責務である。

### 8.2 deterministic start gate

gateは、単一の表示文ではなく固定順のcode tupleを返す。最低限、次を区別する。

| code | 条件 | status |
| --- | --- | --- |
| `delivery_busy` | capture時にapplicationがBusy | `blocked` |
| `delivery_analysis_unavailable` | 解析中、解析結果無効、pending rebuild、timing plan欠落 / empty | `blocked` |
| `delivery_effective_output_unavailable` | writer stateが`ready`でない、またはeffective planなし | `blocked` |
| `delivery_source_audio_unavailable` | original audio input / probe欠落 | `blocked` |
| `delivery_source_audio_invalid` | regular fileでない、stat失敗、input / probe path不一致、probe size不一致 | `blocked` |
| `delivery_ffmpeg_unavailable` | resolved FFmpeg pathなし、またはregular fileでない | `blocked` |
| `delivery_diagnostics_blocked` | VMD saveability falseまたはdiagnostics ERROR | `blocked` |
| `delivery_fingerprint_unavailable` | ready状態なのにfingerprintがない | `blocked` |
| `delivery_warning_confirmation_required` | WARNINGあり、同fingerprintの確認記録なし | `warning_confirmation_required` |

snapshot固有の`blocking_codes`と`warning_codes`は失わず、package側codeと別にresultへ保持する。raw exception text、絶対FFmpeg path、credential、URL、tracebackをuser-facing codeへ埋め込まない。

### 8.3 同一captureの保証

`MainFrame`へ非表示のB1 adapterを追加し、次の順を一つのmethod内で行う。

1. 現在の`UiState`を参照し、Busy / analysis stateを確認する。
2. `_build_current_ui_sync_context()`を最大1回呼ぶ。
3. そのsync contextを`prepare_current_effective_output(sync_context=...)`へ渡し、戻り値の`effective_writer_input_state`、`effective_shape_plan`、`effective_writer_input_failure_reason`を同一captureのローカル値として保持する。以後このcaptureでは`prepare_current_effective_output()`を再度呼ばない。
4. 得た同一`EffectiveShapePlan`から、ordered output morph namesを一度だけ解決する。
5. 同じplan、3で保持したwriter state / failure reason、4で得た同じmorph-name tupleを、`build_and_store_output_diagnostics_snapshot(effective_shape_plan=..., effective_writer_input_state=..., effective_writer_input_failure_reason=..., output_morph_names=...)`へ明示的に渡す。snapshot builderは内部で`prepare_current_effective_output()`、effective plan resolver、morph-name resolverを再実行しない契約にする。
6. source audio input / probe、`MMD_WAV_SPEC`、`VmdWriterParameters`、FFmpeg pathを明示値としてB1 coreへ渡す。source identityのstat取得は`delivery_package.py`のcore helper、FFmpeg解決はB5/AppController側のcallerが担当し、MainFrame adapterでは行わない。
7. gateが`ready`または`warning_confirmation_required`の場合だけimmutable `DeliveryCurrentState`をcandidateとして返す。`blocked`では返さない。

adapterは`RightPane`表示文字列、保存済みVMD、保存済みWAV、保存済みreport、last output directoryを読み取らない。current stateとsnapshotの整合防御として、少なくとも次を検証する。

- `effective_shape_plan.base_plan_identity.digest == snapshot.adjustment_summary.base_plan_identity_digest`
- snapshotのeffective shape count / morph frame countがplanから導出した値と一致する。
- `snapshot.generation_summary.vmd_model_name`と`writer_parameters.vmd_model_name`が一致する。
- snapshotへ渡したordered morph-name tupleが`DeliveryCurrentState.output_morph_names`と一致し、morph-name resolverがcaptureごとに一度だけ呼ばれる。
- `prepare_current_effective_output()`の戻り値3要素がsnapshot builderへ同じcaptureのまま渡され、builder内部の再prepareでplan / writer stateが置き換えられない。
- `snapshot.save_state_fingerprint == DeliveryCurrentState.start_fingerprint`
- source audio path / probeが同じfileを指す。

full frame/value identityは、同じplan objectをsnapshot builderへ明示的に渡すadapter call graphで保証する。snapshot表示文字列からplanを再構築しない。

### 8.4 二段階capture

実際のB5導線では、B1 APIを次の二段階で使う。

1. destination dialog前にcurrent stateをcaptureし、ERROR / WARNING gateを評価する。
2. WARNING確認はgate result内のcandidate snapshotを表示正本とする。承認後にdestinationを選択し、current stateを再captureする。

再captureしたfingerprintが承認済みfingerprintと異なる場合、古い承認を使わず`warning_confirmation_required`へ戻す。fingerprintが同じで`projection_generation`だけが変化した場合は承認を再要求しない。2回目のgateが`ready`になった時点でだけ、destination selectionとtimezone-awareな生成時刻を加えた`DeliveryStartContext`を作る。

B1実装ではdialogやworkerを開始しない。二段階の呼出し順、Busy設定、job ID発行はB5で接続する。

### 8.5 commit fingerprint evaluator

B1のpure evaluatorは、B2 / B5が全成果物検証後に使用できるsemantic checkだけを提供する。

```text
current snapshotなし
  -> blocked: delivery_commit_snapshot_unavailable
current VMD saveability false / blocking codeあり
  -> blocked: delivery_commit_state_blocked
current fingerprintなし
  -> blocked: delivery_fingerprint_unavailable
current fingerprint != start fingerprint
  -> blocked: delivery_state_stale
otherwise
  -> allowed
```

`projection_generation`、Whisper management progress、panel revision、Busy表示の再投影だけでは拒否しない。active job ID、worker kind、cancel / closeを含むauthorizationはB5がこの結果へ追加する。source identity再確認はB3、destination no-clobberはB2 / B6が追加する。

### 8.6 個別保存との分離

- B1 APIは`last_vmd_output_dir`、`last_mmd_wav_export_dir`、`last_mmd_wav_output_path`を参照・更新しない。
- `confirmed_warning_save_state_fingerprint`は既存VMD保存と共有する。新しいpackage専用confirmed fieldやINI keyを追加しない。
- gate拒否、WARNING拒否、context構築失敗で`current_timing_plan`、adjustment history、diagnostics failure、standalone report可否を変更しない。
- B1 adapterによるsnapshot再構築と`projection_generation`増分はUI投影更新であり、save identityや個別保存履歴の更新として扱わない。

## 9. 詳細ステップ

### Step 0: 実装開始前gate

- live Git status、branch、HEADを一コマンドずつ再確認する。
- `MS25_Block_Breakdown`、本plan、Roadmap §12、現行diagnostics / effective output / audio source codeを再読する。
- user-ownedのRoadmap変更と未追跡Block Breakdownを保持する。
- runtime user dataを直接読まない。
- B1外の判断が必要になった場合は実装を止め、ユーザーへ一問一答で確認する。

### Step 1: 命名とsource identity DTO

- `delivery_package.py`を新規作成する。
- fixed artifact naming helperを実装する。
- `SourceAudioIdentity`とcapture helperを実装する。
- file不存在、directory、stat失敗、probe path / size不一致をstructured failureへ正規化する。
- content hash、source file lock、source copyは追加しない。

### Step 2: gate DTOとpure evaluator

- `DeliveryStartGateResult`、`DeliveryCurrentState`、`DeliveryStartContext`、commit fingerprint resultを追加する。
- statusとcodeのvalidationを`__post_init__`でfail-closedにする。
- WARNING確認済みfingerprintは明示入力とし、coreから`UiState`を読まない。
- ERROR、fingerprint欠落、FFmpeg未解決、source不整合ではpartial current stateを返さない。WARNING確認待ちは出力開始可能状態ではないが、確認表示用のexact snapshotを持つcandidate stateは返す。

### Step 3: MainFrame current-state adapter

- visible controlを追加せず、current effective outputとsnapshotを同じsync contextからcaptureするmethodを追加する。
- `prepare_current_effective_output()`、`build_and_store_output_diagnostics_snapshot()`、`resolve_source_audio_path_from_ui_state()`、`_resolved_output_morph_names()`の既存責務を再利用する。`prepare_current_effective_output()`の戻り値3要素を保持してsnapshot builderへ渡し、同一capture中の再prepareを禁止する。morph namesも一度だけ解決し、snapshot builderへ明示注入する。
- source path / probeとFFmpeg pathはcallerから明示注入する。MainFrame adapterは`locate_ffmpeg_tools()`を呼ばず、source identityのstatも行わない。B5/AppControllerの既存責務からB1 coreへ渡し、coreのsource identity helperが入力fileを検証する。
- exceptionをdialog表示せず、B1 structured blocking codeへ変換する。B5がuser-facing mappingを所有する。

### Step 4: B1 core tests

- 固定命名とUnicode stem保持を確認する。
- source identityの正常系、missing、directory、probe path不一致、probe size不一致を確認する。
- DTOのfrozen性とtuple正規化を確認する。
- ERROR / invalid / pending / empty plan / source不足 / FFmpeg不足 / fingerprint欠落を確認する。
- WARNINGの未確認、同fingerprint確認済み、fingerprint変更を確認する。
- projection generationだけの変更ではcommit fingerprint evaluatorが通り、effective frame / tail / diagnostic identity変更ではstaleになることを確認する。

### Step 5: B1 adapter tests

- resolver / snapshot builderをspyし、1回のcaptureで同じeffective planが使われることを確認する。
- `prepare_current_effective_output()`をspyし、1回のcaptureで一度だけ呼ばれること、戻り値のwriter state / failure reasonがsnapshot builderへそのまま渡されること、builder内部で再prepareされないことを確認する。
- ordered morph-name resolverがcaptureごとに一度だけ呼ばれ、その同じtupleがsnapshotと`DeliveryCurrentState`へ渡されることを確認する。
- capture後に可変`UiState`を変更しても、作成済みcontextのplan / snapshot / source identity / namesが変わらないことを確認する。
- WARNING拒否相当のgate結果ではdialog / Busy / worker seamが呼ばれないことはB1 pure contractとして確認し、実GUI actionの統合証拠とは扱わない。
- standalone report saveがERROR snapshotでも独立する既存testを回帰する。

### Step 6: 実装後境界監査

- B2のpath validation、staging、transaction、B3のwriter / source recheck、B4のreport拡張、B5のGUI / workerが先行実装されていないことをdiffで確認する。
- runtime INI / JSON、個別保存履歴、dependency、build / package fileに差分がないことを確認する。
- targeted tests、関連回帰、`compileall`、`git diff --check`を実行し、pass表示とprocess exit codeを別々に記録する。

## 10. 状態遷移 / データ契約

### 10.1 B1 logical state

```text
Current UiState
  -> one UiSyncContext
  -> current EffectiveShapePlan
  -> ordered morph names resolved once
  -> OutputDiagnosticsSnapshot built from that exact plan
  -> source / probe / source identity / FFmpeg / names capture
  -> evaluate start gate
       blocked
         -> no DeliveryCurrentState candidate
         -> no destination dialog / Busy / worker / filesystem mutation
       warning_confirmation_required
         -> expose candidate snapshot + current fingerprint + warning codes
         -> no destination dialog / Busy / worker / filesystem mutation
       ready
         -> immutable DeliveryCurrentState
  -> after destination selection, repeat current capture and gate
       fingerprint changed
         -> old WARNING confirmation is not reusable
       fingerprint unchanged and ready
         -> immutable DeliveryStartContext
```

### 10.2 成果物source mapping

| 成果物 | B1 contextの正本 | B1で禁止する代替 |
| --- | --- | --- |
| VMD | `EffectiveShapePlan`、writer parameters、ordered output morph names | 個別保存済みVMD、RightPane表示、古いplan |
| MMD用WAV | `AudioProbeResult.source_path`、`SourceAudioIdentity`、`MMD_WAV_SPEC`、FFmpeg path | internal analysis WAV、個別保存済みMMD WAV |
| report | 同じcaptureの`OutputDiagnosticsSnapshot`、timezone-aware generated time | 既存report、別captureのsnapshot、表示文字列再構成 |

### 10.3 start context不変条件

- gate statusが`ready`である。
- effective planとsnapshotのbase identityが一致する。
- snapshotは同じcaptureでeffective planを明示入力として構築されている。
- VMD saveabilityがtrueでblocking codeがない。
- start fingerprintが非空でsnapshot fingerprintと一致する。
- contextの`projection_generation`が開始snapshotの値と一致する。
- artifact orderが`("vmd", "mmd_wav", "report")`である。
- ordered morph namesがbuilt-in JapaneseまたはLatin setとして既存validatorを通る。
- source path、probe path、resolved file identityが整合する。
- FFmpeg pathが開始時点でresolved regular fileである。
- report timestampがtimezone-awareである。
- contextは可変`UiState`、worker、dialog、cancel tokenを参照しない。

### 10.4 commit fingerprint不変条件

- 比較対象は開始fingerprintとcurrent fingerprintだけである。
- current snapshotがERROR、save不可、fingerprint欠落なら一致比較前に拒否する。
- `projection_generation`の差は拒否理由にならない。
- management diagnosticsだけの変化は、既存fingerprint契約が不変である限り拒否理由にならない。
- effective frames、tails、model name、stable diagnostic identityの変更は既存fingerprint差としてstaleになる。

## 11. テスト方針

### 11.1 新規B1 tests

`tests/test_ms25_b1_delivery_contract.py`:

- `<audio_stem>_MMD`、`_lip.vmd`、`_mmd.wav`、`_report.txt`のexact naming
- directory名を編集しても3成果物名が変わらず、artifact orderがVMD、MMD用WAV、reportの順であること
- 日本語、Latin、spaceを含むvalid stemのcase / Unicode保持
- empty stem / source不存在でのfail-closed
- source identityのresolved path、size、`mtime_ns`、optional file identity
- sourceがdirectory、probe path不一致、probe size不一致、stat失敗
- DTOのfrozen性、tuple field、timezone-aware timestamp要求
- gate statusと固定code順
- diagnostics ERROR、WARNING、fingerprint欠落
- same-fingerprint WARNING確認再利用とchanged-fingerprint再確認
- commit fingerprintのmatch / stale / missing / blocked
- projection generationだけを変えたsnapshotのcommit許可
- effective outputまたはstable diagnostic identityを変えたsnapshotのstale拒否

`tests/test_ms25_b1_current_state_gate.py`:

- single `UiSyncContext` / single effective resolver / same-plan snapshot
- ready contextのbase identity、shape count、morph frame count、writer parameters、morph names一致
- analysis invalid、pending rebuild、timing plan missing / empty
- original audio / probe不足、FFmpeg unresolved
- ERROR時のB1 blockとstandalone report state非変更
- WARNING resultで確認前にdestination / Busy / worker seamを呼ばないこと
- capture後の`UiState`変更が既存contextを変えないこと
- repeated diagnostics projectionでfingerprintが同じならWARNING再確認を要求しないこと

### 11.2 既存test。存在確認済みでB1回帰に使う

- `tests/test_ms20_b5_warning_save_policy.py`
  - ERROR時dialog前拒否
  - WARNING fingerprint確認、同identity再利用、変更時再確認
  - fingerprintなしのfail-closed
- `tests/test_ms20_b2_output_diagnostics.py`
  - saveability、fingerprint payload、ERROR / WARNINGのcore契約
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
  - UI stateからdiagnostics snapshotへの変換
- `tests/test_ms21_b5_effective_output_identity.py`
  - effective frame / tail変更時のfingerprint変更
  - raw writer parameterだけの非semantic変更をidentityへ混入させない契約
- `tests/test_ms21_b5_adjusted_vmd_save.py`
  - prepared effective planがwriter sourceである契約
- `tests/test_ms24_whisper_diagnostics.py`
  - exact projection generation保持
  - Whisper candidate / management状態をfingerprintへ混入させない契約
- `tests/test_ms20_b6_report_save_flow.py`
  - original source audio優先
  - standalone reportがVMD saveability / WARNING確認から独立する契約
- `tests/test_ms17_b8_long_audio_confirmation.py`
  - 300秒超入力の既存の開始前一回確認と、拒否時のworker未開始
- `tests/test_ms17_b4_audio_probe.py`
  - source path、size、duration、audio stream probe
- `tests/test_ms17_b7_mmd_wav_export.py`
  - original source audioと`MMD_WAV_SPEC`
- `tests/test_ms17_b8_late_worker_result_discard.py`、`tests/test_ms21_b7_audio_worker_terminal.py`
  - B1で変更しない既存worker terminal境界の回帰

### 11.3 実行順

実装後は一コマンドずつ、次の順で実行する。

1. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py`
2. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_current_state_gate.py`
3. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py`
4. `.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b3_output_diagnostics_adapter.py`
5. `.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b5_effective_output_identity.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms24_whisper_diagnostics.py`
6. `.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b6_report_save_flow.py tests/test_ms17_b4_audio_probe.py tests/test_ms17_b7_mmd_wav_export.py`
7. `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms21_b7_audio_worker_terminal.py`
8. `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_long_audio_confirmation.py`
9. `.\.venv\Scripts\python.exe -m compileall -q src tests`
10. `git diff --check`

各pytestはpass件数とprocess exit code `0`を別々に記録する。B1の変更が`MainFrame`へ入るため、wx test終了時のprocess exit codeも省略しない。full pytestは実装後の影響範囲とtargeted regression結果から必要性を判断し、未実施なら未実施と記録する。
8の長時間確認回帰では、300秒超入力の一回確認と拒否時のworker未開始を確認する。

### 11.4 手動確認境界

B1は可視actionを追加しないため、manual GUI確認は受け入れ必須にしない。B1実装時にGUIを起動していない場合は「未実施」と報告する。一括出力button、folder dialog、WARNING文面、Busy、cancel、closeの手動確認はB5以降で行う。実MMD確認はMS26、onefile / package確認はMS27へ維持する。

## 12. 受け入れ条件

### 12.1 core contract

- [ ] 承認済みのdirectory / 3成果物名が元音声stemから決定的に構築される。
- [ ] 3成果物の生成順序がVMD、MMD用WAV、診断レポートへ固定される。
- [ ] Unicode stemを暗黙変換しない。
- [ ] source identityがresolved path、size、`mtime_ns`、取得可能なfile identityを保持する。
- [ ] input source path、probe source path、実file sizeが不一致ならcontextを作らない。
- [ ] `DeliveryCurrentState`と`DeliveryStartContext`がfrozenで、可変`UiState`や`VowelTimingPlan` listを保持しない。
- [ ] current stateに`EffectiveShapePlan`、同じplanからのsnapshot、probe / source identity、MMD spec、FFmpeg path、writer parameters、ordered morph names、fixed names、fingerprintが含まれる。
- [ ] ordered morph namesはcaptureごとに一度だけ解決され、その同じtupleがsnapshotと`DeliveryCurrentState`へ渡される。
- [ ] report generated timeがtimezone-awareである。

### 12.2 start gate

- [ ] invalid analysis、pending rebuild、missing / empty timing plan、effective output不成立をfail-closedで拒否する。
- [ ] diagnostics ERRORとVMD saveability falseを一括出力開始不可にする。
- [ ] WARNINGは同じsave-state fingerprint単位で確認対象となる。
- [ ] WARNING拒否またはfingerprint欠落ではready contextを返さない。
- [ ] WARNING確認待ちresultは、確認表示用に同じimmutable snapshotを含むcandidate stateを返すが、start contextは作れない。
- [ ] `DeliveryCurrentState.gate_status`をcandidateへ保持し、`warning_confirmation_required`のcandidateからは`DeliveryStartContext`を構築できない。確認済みで`ready`になったcandidateだけをcontextへ昇格する。
- [ ] 同fingerprintの既存確認identityを再利用し、新しいpackage専用confirmed stateを追加しない。
- [ ] ERROR拒否がstandalone report保存可否や個別保存履歴を変更しない。
- [ ] source audio / probe / FFmpeg不足をstructured codeで拒否し、raw exceptionや不要な絶対pathを通常表示用codeへ含めない。

### 12.3 fingerprint separation

- [ ] schema `ms21-effective-output-v1`を変更しない。
- [ ] `projection_generation`を開始snapshotとcontextに記録する。
- [ ] `projection_generation`だけの変化ではWARNING再確認とcommit拒否を発生させない。
- [ ] effective frame / tailまたはstable diagnostic identityの変化は既存fingerprint差としてstaleになる。
- [ ] Whisper management / candidate / progress情報をfingerprintへ追加しない。
- [ ] B1 commit evaluatorはsemantic fingerprintだけを判定し、job / worker / cancel / close authorizationを先行実装しない。
- [ ] 300秒超の入力音声は、destination選択後・Busy / worker開始前に既存の長時間確認を一度だけ行い、経過時間timerやworker開始後の再確認を追加しない。

### 12.4 scope / verification

- [ ] B2のstaging / path validation / no-clobber、B3の生成 / validation、B4のreport拡張、B5のGUI / worker、B6のrecovery、B7のdocsを実装していない。
- [ ] 個別保存履歴、INI / JSON、dependency、build / package fileに差分がない。
- [ ] B1新規testsと指定回帰がpass表示かつprocess exit code `0`である。
- [ ] `compileall -q src tests`と`git diff --check`がprocess exit code `0`である。
- [ ] 新規・未追跡ファイルの末尾空白を`rg -n "[ \t]+$" <対象ファイル>`等で別途検査し、no-matchのexit code `1`を該当なしとして扱う。
- [ ] 未実施のmanual GUI、実MMD、Python 3.11 / 3.12、onefile / release確認を未検証として報告する。

## 13. リスクと対策

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS25-B1-R1 | plan、morph names、snapshotを別resolver / 別時点から取得し、VMDとreportの正本がずれる | P1候補 | 一つの`UiSyncContext`と同じeffective plan object、captureごとに一度だけ解決したmorph-name tupleからsnapshotを構築し、base identity / count / morph names / fingerprint整合を検証する |
| MS25-B1-R2 | `projection_generation`をcommit guardにして、単なる再投影で自己失効する | P1候補 | commit evaluatorはsave-state fingerprintだけを比較し、projection generationは記録 / late-result用途に限定する |
| MS25-B1-R3 | ERROR snapshotでもpartial contextを作り、後続Blockが誤って出力する | P1候補 | blocked resultでは`candidate_state=None`とし、`ready`以外からstart contextを構築できないvalidationを入れる。WARNING candidateは表示専用で、開始contextへ昇格させない |
| MS25-B1-R4 | WARNING確認前にdialog、Busy、workerへ進む | P2候補 | `warning_confirmation_required`をterminal gate resultとして返し、B1ではactionを実装しない。B5接続testへ引き継ぐ |
| MS25-B1-R5 | package ERROR gateがstandalone report保存まで禁止する | P2候補 | package gateを新しいpure evaluatorへ限定し、`request_save_diagnostic_report()`とreport menu stateを変更しない |
| MS25-B1-R6 | analysis WAVをMMD WAV sourceとして固定する | P1候補 | `AudioInputInfo` / `AudioProbeResult.source_path`だけをsource identityへ使い、analysis WAVをcontextのMMD sourceにしない |
| MS25-B1-R7 | probe後にsource fileが差し替わり、開始contextと実fileがずれる | P1候補 | B1でprobe sizeと実statを照合しidentityを固定する。B3でWAV生成前後の再確認を必須化する |
| MS25-B1-R8 | frozen dataclass内へmutable `VowelTimingPlan` listを保持し、contextが後から変化する | P2候補 | timing成立はgateで確認し、context正本をtuple-based effective plan / snapshotへ限定する |
| MS25-B1-R9 | B1でWindows path validationやtransactionまで実装し責務が混ざる | P2候補 | B1はfixed namingとstructural contextまで。path validation / staging / no-clobberはB2へ残す |
| MS25-B1-R10 | B1で新しいINI keyや個別保存履歴を更新する | P2候補 | delivery destinationはcontext引数だけとし、`UiState`保存履歴とSettingsStoreを変更しない |
| MS25-B1-R11 | source identityを完全byte保証として説明する | P3候補 | content hash非採用とsame-size / same-mtime / same-file-id置換の検出限界を文書・reportへ過大表示しない |
| MS25-B1-R12 | raw stat / FFmpeg例外や絶対pathをuser-facing codeへ漏らす | P2候補 | structured codeとsafe summaryを分け、技術詳細の表示は既存Error Handling契約に従う |
| MS25-B1-R13 | 一括出力だけ長時間確認のタイミングが変わり、確認なしにBusy / workerへ進む | P2候補 | 既存の`_confirm_long_audio_if_needed()`をB5で再利用し、destination選択後・Busy / worker開始前に一度だけ確認する。経過時間timerは新設しない |

## 14. Codex実装時の注意

- コマンドは一つずつ実行し、並列・pipeline・command chainを使わない。
- 実装開始時にlive Gitとユーザー所有変更を再確認し、RoadmapとBlock Breakdownを上書きしない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読書き・stageしない。
- B1ではvisible GUI action、worker kind、staging、writer、report形式を実装しない。
- `EffectiveShapePlan`とsnapshotを表示値から再構築しない。現行resolver / adapterの明示入力を使い、ordered morph namesは一度だけ解決してsnapshotへ明示注入する。
- MainFrame adapterで`locate_ffmpeg_tools()`やsource identityのstatを行わない。FFmpeg pathはB5/AppControllerから注入し、source identityはB1 core helperで取得する。
- `UiState.mmd_wav_export_ready`を元音声source gateとして流用しない。
- existing `confirmed_warning_save_state_fingerprint`を共有し、package専用confirmation stateを追加しない。
- diagnostics snapshot再投影で増える`projection_generation`をfingerprintへ混入させない。
- source identity helperはprivate Whisper model helperを直接importせず、delivery source向けの小さい標準ライブラリ実装とする。
- test helperをproduction codeからimportしない。
- exceptionを握りつぶさず、structured block codeと必要な内部詳細を分離する。
- 300秒超の入力音声は既存の開始前一回確認をB5へ接続する。確認はdestination選択後、Busy / worker開始前に行い、拒否時はworkerを開始しない。経過時間timerやworker開始後の再確認は追加しない。
- testを削除・skip・弱化して合格させない。
- pytestのpass表示とprocess exit code、`compileall`、`git diff --check`を別々に記録する。
- manual GUI確認を実施していない場合は、実施済みと記録しない。
- stage、commit、merge、pushは別の明示承認まで行わない。

## 15. 後続Blockへの引き継ぎ

### MS25-B2

- `DeliveryStartContext`へ含まれるparent / folder selectionのWindows validation
- component / absolute path長、collision、staging、no-clobber commit
- injected pre-commit guardとdelivery terminal result

### MS25-B3

- contextのeffective planからVMD生成
- original source audioからMMD WAV生成
- context snapshotからreport生成
- VMD / WAV / report validation
- source identityのWAV生成前後再確認

### MS25-B4

- profile未使用、既定morph setを含むreport identity必須化
- Whisper semantic / runtime identityの既存形式維持

### MS25-B5

- package action、WARNING dialog、destination dialog、Busy、worker
- 既存の`_confirm_long_audio_if_needed()`を再利用し、300秒超入力ではdestination選択後・Busy / worker開始前に一度だけ確認する。確認拒否時はworkerを開始せず、経過時間timerやworker開始後の再確認は追加しない
- dialog後のB1再captureとWARNING再確認
- job ID / worker kind / cancel / closeを加えたcommit authorization
- individual save history非変更

### MS25-B6 / B7 / MS26 / MS27

- B6: transaction、TOCTOU、cancel / cleanup / shutdown recovery
- B7: regression、README / 配布説明 / 正文仕様 / routing同期
- MS26: Windows 11と実MMDでのVMD / WAV / lip sync確認
- MS27: onefile、ZIP、artifact、package / release readiness
