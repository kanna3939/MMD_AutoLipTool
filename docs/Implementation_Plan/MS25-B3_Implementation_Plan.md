# MS25-B3 Implementation Plan

## 1. 文書情報

- 文書名: MS25-B3 3成果物生成アダプター Implementation Plan
- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B3 3成果物生成アダプター
- 作成日: 2026-08-31
- 状態: 実装済み。2026-09-01実装前チェックのP2/P3補正を反映した計画に基づき、production code / test codeを`904ccae Implement MS25-B3 delivery artifact adapters`で実装済み。GUI、設定、runtime user data、依存関係は変更していない
- 対象ブランチ: `feature/MS25-implementation`
- 計画作成時HEAD: `0f018cd Implement MS25-B2 delivery package orchestration`
- 実装コミット: `904ccae Implement MS25-B3 delivery artifact adapters`
- 直接依存:
  - MS25-B1: `DeliveryCurrentState` / `DeliveryStartContext` / source identity / current-state gate
  - MS25-B2: `DeliveryArtifactOperations` / staging / injected operation / pre-commit guard / no-clobber commit / terminal result
- 計画作成時の変更権限: 本文書のP2/P3補正と`docs/MS20_and_Beyond_Index.md`のMS25状態同期だけ。production code、test code、設定、runtime user data、依存関係は変更しない
- ユーザー判断待ち: なし。B3の成果物source、固定名、生成順、検証項目、source identity、B2 transactionとの境界は現行Roadmap、Block Breakdown、B1 / B2実装から確定できる
- 計画作成時の検証: 文書・コード・テストの読み取り照合のみ。pytest、`compileall`、build、実FFmpeg、GUI、実MMD確認は実行していない
- 2026-09-01実装前チェック: B1/B2直接回帰70 passed・2 skipped、VMD関連17 passed、MMD WAV関連11 passed、diagnostics/profile/Whisper関連32 passed、全pytest951 passed・4 skipped、`compileall`、`git diff --check`、`pip check`を終了コード0で確認した

### 1.1 正本と現行状態の優先順位

B3の判断には次の順を使う。

1. live Git、現行production code、現行test
2. `docs/Implementation_Plan/MS25_Block_Breakdown.md`
3. 実装済みB1 / B2のpublic contractと専用test
4. `docs/MS20_and_Beyond_Roadmap.md` §12、現行Pipeline / Error / VMD / WAV仕様
5. Index、B1 / B2 planの過去時点・状態欄

現行HEADにはB1 / B2 / B3 codeと専用testが存在し、B3の実装は`904ccae`で確定している。`docs/Implementation_Plan/MS25-B2_Implementation_Plan.md`の状態欄に残るB2未実装表現は計画作成時点の記録であり、現在のB2実装済み状態はIndexとcommit履歴を正とする。B3ではlive codeを正とし、B2のtransactional delivery contractを変更しない。B3実装済み状態とB4へのroutingは、現在のIndexおよび本計画書の状態欄へ同期済みである。MS25-B4は`01b4d4f`で実装済み、MS25-B5も後続Blockとして実装済みである。

## 2. 背景

MS25は、現在の編集済み出力からVMD、元の入力音声からMMD用WAV、同じ開始時点の診断snapshotからレポートを再生成し、一つの専用directoryとして確定する機能である。

B1は、次を一つのimmutable `DeliveryStartContext`へ固定した。

- 現在の`EffectiveShapePlan`
- 同じplanから作成した`OutputDiagnosticsSnapshot`
- `AudioProbeResult`と`SourceAudioIdentity`
- `MMD_WAV_SPEC`
- 解決済みFFmpeg path
- `VmdWriterParameters`
- resolved ordered morph names
- 固定成果物名
- start fingerprintと`projection_generation`
- timezone-awareなreport生成時刻

B2は、`DeliveryArtifactOperations`へ注入された次の3 callableを固定順で呼び、staging全体をtransactionとして扱うcore orchestrationを実装した。

1. `generate_and_validate_vmd`
2. `generate_and_validate_mmd_wav`
3. `generate_and_validate_report`

B2は、各callableが指定されたstaging pathへ1成果物を生成し、成果物固有のvalidationまで完了した場合だけ正常returnすることを前提にする。B2自身は、各operation後のregular / non-reparse / non-empty検査、staging exact-content検査、pre-commit authorization、Windowsのno-clobber directory rename、cancel / cleanup / terminal resultを所有する。実際のVMD / WAV / report writerは呼ばない。

現行writer境界は次のとおりである。

- `build_morph_frames_from_effective_shape_plan()`は、resolved `EffectiveShapePlan`から最終モーフframe列を生成し、resolved output morph-name tupleを明示入力できる。
- `write_morph_frames_vmd()`はprepared frame列を指定pathへ直接書く。header、model field、bone count 0、morph records、camera / light / self-shadow / IK count 0を出力するが、production用read-back validationは存在しない。
- `export_mmd_wav()`は`AudioProbeResult.source_path`を入力にし、staging file内ではtemporary fileと`os.replace()`を用い、`MMD_WAV_SPEC`に従うWAV validationを実施する。cancellable実行には既存`run_ffmpeg_mmd_wav_cancellable()`をrunnerとして注入できる。
- `write_diagnostic_report()`は指定snapshotとtimezone-aware timestampからUTF-8 / LF / BOMなしのreportを作り、same-directory temporary fileをbyte検証後に`os.replace()`する。
- 現行`format_diagnostic_report()`はactive presetとWhisper identityを常に記録し、profile / morph set欄はprofile使用時または非既定morph set時だけ記録する。profile未使用・既定日本語morph setでもidentity欄を必須化する変更はMS25-B4の責務である。

B3は、この未接続の3 callableをproduction adapterとして実装し、B2のtransactionを変更せず、各artifactが開始contextと一致することをcommit前に検証できる状態へする。

## 3. 目的

MS25-B3では、次を実装可能な契約として固定する。

1. B1の`DeliveryStartContext.current_state.effective_shape_plan`とresolved ordered morph namesから、編集反映済みVMDをstagingへ生成する。
2. VMDをproduction用read-back validatorで再読込し、header、model field、section count、全morph record、EOFを開始context由来の期待値と照合する。
3. `AudioProbeResult.source_path`だけをMMD用WAV sourceとし、internal analysis WAVや個別保存済みWAVを使用しない。
4. MMD用WAV生成の直前と既存WAV validation完了後にsource identityを再取得し、B1で固定したidentityとの差をfail-closedにする。
5. 同じ開始contextの`OutputDiagnosticsSnapshot`と`report_generated_at`からreportを生成し、最終bytesを同じformatterの期待bytesと照合する。
6. 成果物ごとの失敗をB2が解釈できるsafeなstructured error codeへ正規化し、raw exception、traceback、不要なabsolute pathをterminal codeへ混入させない。
7. 3 adapterを`DeliveryArtifactOperations`として構築するGUI非依存factoryを提供し、B5が既存B2 orchestrationへそのまま注入できるようにする。

B3完了は利用者向け一括出力導線の完成を意味しない。B4のreport identity必須化、B5のGUI / worker接続、B6のWindows recovery hardening、B7の横断回帰・文書同期は後続Blockに残す。

## 4. In Scope

- UI非依存のdelivery artifact adapter module新設
- B2 `DeliveryArtifactOperations`を構築するproduction factory
- 現在の`EffectiveShapePlan`からのprepared morph frame生成
- resolved Japanese / Latin ordered morph namesの明示伝播
- `write_morph_frames_vmd()`によるstaging VMD生成
- production VMD read-back validator新設
- VMD header / model field / bone count / morph count / morph records / camera / light / self-shadow / IK count / exact EOF検証
- VMD truncated data、過大count、余分な末尾bytesの拒否
- `export_mmd_wav()`と`run_ffmpeg_mmd_wav_cancellable()`の接続
- MMD用WAV生成直前・検証後の`SourceAudioIdentity`再取得と完全DTO比較
- MMD WAV export resultのsource path、output path、`MMD_WAV_SPEC`、non-empty size整合確認
- 同じsnapshot / timestampによるdiagnostic report生成
- report final bytesのUTF-8 strict decode、BOMなし、LF、formatter期待bytesとの完全一致確認
- VMD / WAV / reportのwrite failureとvalidation failureのstructured code分離
- B3専用core tests
- B1 / B2 orchestration、既存VMD writer、MMD WAV、diagnostic report、profile / Whisper diagnosticsの関連回帰確認

## 5. Out of Scope

- B1のcurrent-state capture、WARNING / ERROR gate、fingerprint schemaの変更
- B2のpath validation、staging作成、artifact順、exact-content検査、pre-commit guard、no-clobber rename、cancel線形化、cleanup、terminal resultの再設計
- final directoryへの直接書込み
- final directory、既存package、個別保存済み成果物のmerge / replace / reuse
- B4のdiagnostic report項目追加
- profile未使用・既定日本語morph set時のprofile / morph set欄必須化
- package専用manifest、hash、session file、ZIP、追加成果物
- B5のbutton、menu、folder dialog、WARNING確認、Busy、worker kind、late callback、window close
- B6のactual junction / reparse / locked / antivirus / shutdown横断matrix
- 個別VMD保存、個別MMD用WAV出力、個別診断レポート保存の実装変更
- 個別保存履歴、recent directory、batch parent directory、INI keyの更新
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読書き、コピー、stage
- `README.md`、`readme_mmdautolip.txt`、Roadmap、Index、Block Breakdown、正文仕様の同期
- VMD format、30fps、morph value、frame order、model nameの仕様変更
- MMD WAV codec / sample rate / channel count / chunk方針の変更
- source audio content hashの追加
- dependency追加・更新
- network、cloud ASR、telemetry、background通信
- Qt / PySide6の復活
- 実MMD確認（MS26）
- PyInstaller onefile、ZIP、artifact、package / release readiness（MS27）

## 6. 前提条件

### 6.1 B1 contextを成果物正本とする

B3は可変`UiState`、GUI表示、個別保存済みfile、現在のdialog値を再参照しない。3成果物は、渡された一つの`DeliveryStartContext`だけから派生させる。

| 成果物 | 正本 | 禁止する代替 |
| --- | --- | --- |
| VMD | `effective_shape_plan`、`writer_parameters.vmd_model_name`、`output_morph_names` | Preview表示、古いtiming plan、個別保存済みVMD |
| MMD用WAV | `audio_probe.source_path`、`source_identity`、`mmd_wav_spec`、`ffmpeg_path` | internal analysis WAV、個別出力済みWAV |
| report | `diagnostics_snapshot`、`report_generated_at` | current GUI表示、別captureのsnapshot、既存report |

`writer_parameters.closing_hold_frames` / `closing_softness_frames`は、B1が同じcaptureでdiagnosticsとfingerprintへ記録した値である。VMD生成時は既に解決済みの`EffectiveShapePlan`をprepared frameへ変換するため、adapter側でhold / softnessを再適用しない。

`docs/Pipeline_Data_Contract_Specification.md` §19.4にはmorph nameを日本語5母音へ限定する旧表現が残るが、同書§15.8、現行`VMD_Output_Specification.md`、MS23実装、B1 contextはJapanese / Latinの組み込み2 setを現行契約とする。B3は後者を採用し、旧表現の同期はB7へ残す。

### 6.2 B2 injected operation contract

各operationは次を守る。

- signatureは`(DeliveryStartContext, Path, DeliveryCancelToken) -> None`
- 渡されたpath以外をfinal outputとして選ばない
- 成果物固有validation完了後だけ正常returnする
- user confirmation、destination選択、Busy、commitを行わない
- cancel tokenをFFmpeg processへ伝播する
- failure時はsafeな`code`を持つ例外を送出し、B2にcleanupとterminal resultを委ねる
- 成果物別codeをB2へ渡す場合は、既存`DeliveryContractError(code, safe_message)`へ正規化する。B2の`_delivery_exception_code()`は例外の文字列`code`属性だけを採用するため、`AudioConvertError.info.code`やvalidator固有例外をそのまま送出しない
- operation内部のtemporary fileは既存writerのcleanup契約に従う
- `export_mmd_wav()`の注入runner呼び出しは`cancel_token`を受け取らないため、MMD WAV adapterは`run_ffmpeg_mmd_wav_cancellable()`を同じ`DeliveryCancelToken`へ束縛したclosureまたは`functools.partial`としてrunnerへ渡す。`export_mmd_wav()`本体の既存signatureは変更しない
- B2が所有するstaging rootやfinal directoryを削除・renameしない

### 6.3 VMD binary baseline

現行`write_morph_frames_vmd()`が出力するB3対象VMD layoutを次の順で検証する。

| offset / size | 内容 | B3 validatorの条件 |
| --- | --- | --- |
| 0 / 30 | VMD header | `Vocaloid Motion Data 0002`のNUL paddingを含めbyte一致 |
| 30 / 20 | model field | `vmd_model_name`の現行Shift_JIS fixed-field encodingとbyte一致 |
| 50 / 4 | bone frame count | `0` |
| 54 / 4 | morph frame count | 期待record件数と一致し、`MAX_MORPH_FRAMES`以下 |
| 58 / 23 × N | morph records | 15-byte name、uint32 frame、float32 valueを順序込みで期待値と一致 |
| record終端 / 4 | camera count | `0` |
| +4 / 4 | light count | `0` |
| +8 / 4 | self-shadow count | `0` |
| +12 / 4 | IK count | `0` |
| 末尾 | EOF | 追加byteなし |

validatorはcountを信頼して無制限にloopせず、期待countと最大file sizeから先に境界を確定する。morph valueは広い近似許容を使わず、現行writerの一回だけの4桁finalization後にIEEE 754 little-endian float32へ変換した期待bytesと比較する。期待値のfinalizationとfixed-field encodingは同じ`src.vmd_writer` package内の既存writer helperを期待bytes算出に限って再利用し、binary parser自体は独立させる。これによりnumeric / encoding規則を複製せず、serialization上の正当な変換を受け入れつつ、file上の別値を許容しない。これらpackage-private helperをpublic exportへ昇格させない。

### 6.4 MMD WAV baseline

delivery MMD WAVは現行`MMD_WAV_SPEC`に固定する。

```text
RIFF / WAVE
fmt chunk size 16
audio format 1 = PCM
PCM signed 16-bit little-endian
44100 Hz
channels: 2
data chunkあり、data size > 0
```

`export_mmd_wav()`は既に、source audioの使用、temporary file、`-bitexact`、WAV read-back validation、失敗時temporary cleanupを所有する。B3はこの処理を複製せず、cancellable runnerを注入して使用する。

`docs/MMD_Audio_WAV_Compatibility_Specification.md` §10.3にはchannel count 1または2という一般記述が残るが、§7.2、現行`MMD_WAV_SPEC`、現行code / testはdelivery出力をstereo 2chへ固定している。B3はlive codeの2ch契約を採用し、仕様文書同期はB7へ残す。

### 6.5 diagnostic report baselineとB4境界

B3 report adapterは次だけを保証する。

- `current_state.diagnostics_snapshot`と`report_generated_at`をそのままwriterへ渡す
- formatterの期待bytesとfinal file bytesが一致する
- UTF-8 strict、BOMなし、LF終端を維持する
- snapshot、workspace state、WARNING確認identityを変更しない

profile未使用・既定日本語morph setでもprofile / morph set identity欄を必須表示する変更はB4が`src/core/diagnostic_report.py`へ行う。B3 adapterはformatterを再実装せず、B4のformatter変更後も同じsnapshot / timestampから期待bytesを再計算できる構造にする。

### 6.6 source identity保証範囲

WAV operationは、生成直前と既存exporterのformat validation完了後に`capture_source_audio_identity()`を実行し、各結果を開始contextの`SourceAudioIdentity`と全fieldで比較する。

- `resolved_path`
- `size_bytes`
- `mtime_ns`
- `device_id`
- `file_id`
- `file_attributes`

不一致または再取得失敗は`source_audio_changed`とする。content hashは計算しないため、同一size、同一`mtime_ns`、同一file identityを意図的に維持したbyte置換は検出保証外である。この限界をB3で拡張しない。

### 6.7 error code

B3 operationは少なくとも次のcodeへ正規化する。

| phase | code | 条件 |
| --- | --- | --- |
| VMD | `vmd_write_failed` | frame構築、Shift_JIS encode、writer I/O等の生成失敗 |
| VMD | `vmd_validation_failed` | header、model、count、record、tail section、EOF不一致 |
| WAV | `source_audio_changed` | 生成前・検証後identity不一致または再取得不能 |
| WAV | `mmd_wav_write_failed` | FFmpeg、権限、temporary replace等の生成失敗 |
| WAV | `mmd_wav_validation_failed` | 既存WAV validator不合格、result spec / path / size不一致 |
| report | `report_write_failed` | formatter、temporary write、replace等の生成失敗 |
| report | `report_validation_failed` | final bytes、UTF-8、BOM、改行、expected bytes不一致 |
| 共通 | `output_cancelled` | B2がcancel tokenを受理した場合。operationは成功へ変換しない |

`AudioConvertError.info.code`はB2の`error.code`直接参照と形が異なるため、B3 WAV adapterで上表へ明示的に写像し、既存`DeliveryContractError`として送出する。VMD validator固有例外とreportのwriter / read-back例外も同じ境界で正規化する。raw exception messageからcodeを推測しない。

## 7. 対象ファイル

### 7.1 B3実装時の主変更対象

| 種別 | ファイル | B3責務 |
| --- | --- | --- |
| 新規 | `src/core/delivery_artifacts.py` | 3つのgenerate-and-validate adapter、error正規化、cancellable WAV runner接続、`DeliveryArtifactOperations` factory |
| 新規 | `src/vmd_writer/validator.py` | production VMD read-back parser / validator、truncation / extra-tail拒否 |
| 新規 | `tests/test_ms25_b3_delivery_artifacts.py` | VMD / WAV / report adapter、source identity、cancel、error mapping、B2 orchestration接続 |
| 新規 | `tests/test_ms25_b3_vmd_readback_validation.py` | VMD binary正常系とheader / model / count / record / tail / EOF異常系 |

`src/core/delivery_package.py`にはB2 operation seamが実装済みである。B3は新規moduleから既存DTOをimportし、B2 orchestrationへactual operationを追加・直書きしない。`src/core/__init__.py`と`src/vmd_writer/__init__.py`もB3で変更せず、B5は明示moduleからfactoryをimportする。

### 7.2 関連確認対象。B3では原則変更しない

- `src/core/delivery_package.py`
- `src/core/mmd_wav_export.py`
- `src/core/ffmpeg_runner.py`
- `src/core/diagnostic_report.py`
- `src/core/output_diagnostics.py`
- `src/core/audio_probe.py`
- `src/core/audio_errors.py`
- `src/vmd_writer/writer.py`
- `src/vmd_writer/effective_shape_adapter.py`
- `src/gui_wx/main_frame.py`
- `tests/test_ms25_b1_delivery_contract.py`
- `tests/test_ms25_b1_current_state_gate.py`
- `tests/test_ms25_b2_delivery_orchestration.py`
- `tests/test_ms25_b2_delivery_commit.py`
- `tests/test_ms25_b2_windows_paths.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms17_b7_mmd_wav_export.py`
- `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_ms24_whisper_diagnostics.py`

### 7.3 B3では変更しない対象

- `src/core/delivery_package.py`のB1 / B2 DTO、path validation、staging、commit、cancel、cleanup、terminal semantics
- `src/gui_wx/`配下すべて
- 個別保存処理を所有する`src/core/pipeline.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/main_frame.py`
- `src/core/diagnostic_report.py`のformat field構成
- `src/core/mmd_wav_export.py`のWAV spec / chunk validation
- `src/vmd_writer/writer.py`のbinary layout / value finalization
- README、配布用readme、Roadmap、Index、Block Breakdown、B1 / B2 plan、正文仕様
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`
- `pyproject.toml`、lock file、PyInstaller spec、build script、license文書

## 8. 実装方針

### 8.1 B3 production API

`src/core/delivery_artifacts.py`へ、少なくとも次と同等のfactoryを置く。private helper名は調整してよいが、operation signatureと責務を弱めない。

```python
def build_delivery_artifact_operations() -> DeliveryArtifactOperations:
    return DeliveryArtifactOperations(
        generate_and_validate_vmd=_generate_and_validate_vmd,
        generate_and_validate_mmd_wav=_generate_and_validate_mmd_wav,
        generate_and_validate_report=_generate_and_validate_report,
    )
```

factoryはGUI、SettingsStore、worker、destination dialogをcaptureしない。B5がworkerへ渡すimmutable callable holderとして使用する。

`src/vmd_writer/validator.py`へ、少なくとも次と同等のAPIを置く。

```python
class VmdReadbackValidationError(ValueError):
    pass

def validate_morph_vmd_readback(
    path: str | Path,
    *,
    expected_model_name: str,
    expected_morph_frames: Sequence[tuple[int, str, float]],
    expected_output_morph_names: Sequence[str],
) -> None:
    ...
```

validatorはtest helperをimportせず、production moduleだけで完結する。成功時は`None`を返し、不一致は`VmdReadbackValidationError`を送出する。adapterがこれを`vmd_validation_failed`へ変換する。

### 8.2 VMD operation

処理順を固定する。

1. cancel済みならwriterを呼ばず、B2がcancelを確定できる例外または早期終了へ進む。
2. `build_morph_frames_from_effective_shape_plan()`へ、開始contextの`effective_shape_plan`と`output_morph_names`を明示的に渡す。
3. `current_state.diagnostics_snapshot.adjustment_summary.effective_morph_frame_count`が`None`でない場合は、frame列の件数と一致することを防御的に再確認する。不一致は`vmd_write_failed`とする。`None`自体は、現行B1 DTOが許容しているためB3で新たな拒否条件にしない。
4. `write_morph_frames_vmd()`へstaging path、prepared frame列、`vmd_model_name`、同じordered output namesを渡す。
5. production read-back validatorへ同じmodel name、同じframe列、同じordered output namesを渡す。
6. validator成功後だけ正常returnする。

`closing_hold_frames` / `closing_softness_frames`をwriterへ再適用しない。これらは`EffectiveShapePlan`解決時に反映済みであり、二重適用すると個別保存とdelivery VMDが不一致になる。

### 8.3 VMD read-back validator

validatorは次を順に行う。

1. expected morph namesを既存built-in validatorと同じ日本語 / Latin 5件へ限定する。
2. expected recordを非負uint32 frame、allowed morph name、有限・非負valueとして検査する。
3. expected countが`MAX_MORPH_FRAMES`以下であることを確認する。
4. expected countからexact file size `74 + 23 * count` bytesを計算する。
5. file sizeがexact値でなければ、短い場合はtruncated、長い場合はunexpected trailing dataとして拒否する。
6. header、model field、bone countを検査する。
7. morph countをexpected countと照合する。
8. 全recordを入力順のまま照合する。name fieldはNUL padding込み、frameはuint32 exact、valueはwriter finalization後のfloat32 bytes exactとする。
9. camera / light / self-shadow / IK countがすべて0であることを確認する。
10. cursorがEOFとexact一致することを確認する。

countやoffsetから範囲外`struct.unpack_from()`を起こさず、境界不足をvalidation errorへ正規化する。model nameまたはmorph nameのShift_JIS encode失敗、NUL混入、固定field超過による曖昧な一致もfail-closedにする。現行B1ではmodel nameは`AutoLipTool`、morph namesは組み込み5母音に限定されるが、validator単体でも入力を信頼しない。

### 8.4 MMD用WAV operation

処理順を固定する。

1. `capture_source_audio_identity(audio_probe.source_path)`を実行し、開始contextのidentityと全field一致を確認する。
2. identity不一致ならFFmpegを開始せず`source_audio_changed`にする。
3. `export_mmd_wav()`へ開始contextの`audio_probe`、`ffmpeg_path`、staging output pathを渡す。
4. `run_ffmpeg_mmd_wav_cancellable()`を同じ`DeliveryCancelToken`へ束縛したclosureまたは`functools.partial`を作り、`export_mmd_wav()`の`runner`へ注入する。既存`export_mmd_wav()`はrunnerへ`cancel_token`を渡さないため、adapter側の束縛を省略しない。
5. exporterが既存WAV validationを完了してreturnした後、`Path(result.source_path).resolve(strict=False)`を開始contextの`source_identity.resolved_path`と比較する。relative path、symlink、junctionを含む入力でも、B1が採用した解決先regular file identityと同じ場合は正常とする。resultのoutput pathも`Path(...).resolve(strict=False)`でstaging output pathと比較し、spec、file sizeを開始contextと実fileへ照合する。path正規化または照合に失敗したresultは`mmd_wav_validation_failed`とする。
6. source identityを再取得し、開始contextと全field一致を確認する。
7. post identity一致後だけ正常returnする。

source identity再取得は、exporterのformat validation後に必ず行う。生成前だけの確認では、FFmpeg実行中の差し替えを検出できない。post identity不一致時は生成済みstaging WAVを成功扱いせず、B2のstaging cleanupへ渡す。

### 8.5 diagnostic report operation

処理順を固定する。

1. `format_diagnostic_report(snapshot, generated_at=report_generated_at)`からexpected text / bytesを作る。
2. `write_diagnostic_report()`へ同じsnapshot、同じtimestamp、staging pathを渡す。
3. final staging reportをbytesで読み直す。
4. expected bytesとの完全一致、UTF-8 strict decode、BOMなし、CR byteなし、末尾LFを確認する。
5. validation成功後だけ正常returnする。

expected bytesを表示文字列や別snapshotから組み立てない。B4がformatterへidentity必須欄を追加した場合も、B3 adapterを変更せず自動的に同じformatを検証できる。

### 8.6 cancelと例外境界

- VMD / reportは通常短時間処理だが、operation開始前・writer return後・validation return後にcancel状態を確認し、cancel済み成果物をsuccessとしてB2へ返さない。
- MMD WAVはcancellable FFmpeg runnerへtokenを登録し、B2のprocess bridgeを再利用する。
- FFmpegがcancelによりnon-zero returnまたは例外になった場合、tokenがcancel済みならB2が`output_cancelled`をprimary resultとする。adapterはcancelを`mmd_wav_write_failed`へ固定しない。
- cancel以外の成果物固有failureは`DeliveryContractError`へ変換し、B2の既存fallback codeへ偶然依存しない。
- operationは`Exception`をsafe codeへwrapしてよいが、`KeyboardInterrupt`、`SystemExit`等の`BaseException`を握りつぶさない。
- exception chainingは内部診断用に保持してよい。通常terminalへ渡すのは固定codeだけとし、raw pathやstderr全文をcodeへ含めない。

### 8.7 transactional deliveryと個別保存の共存

B3は既存の個別保存methodを呼び替えない。delivery adapterは同じlow-level writerを別のstaging pathへ呼ぶだけとする。

- 個別VMD保存のdialog、WARNING確認、保存履歴を変更しない。
- 個別MMD用WAV出力の上書き確認、保存履歴を変更しない。
- standalone診断レポート保存はERROR snapshotでも利用できる既存契約を変更しない。
- delivery failureはworkspaceのtiming plan、Preview、Waveform、snapshot、fingerprint、WARNING確認済みidentityを変更しない。
- B3 operationはfinal pathを知らず、B2以外のcommit手段を持たない。

## 9. 詳細ステップ

### Step 0: 実装開始前gate

- live `git status`、branch、直近logを一コマンドずつ確認する。
- user-owned差分がある場合は、B3対象との重なりを確認して保持する。
- B1 / B2 public API、専用test、current `delivery_package.py`を再確認する。
- B2 plan / Indexの状態欄ではなく、live HEADのB2実装を基準にする。
- target 4 files以外へ変更が必要になった場合は、B3の責務不足か単なる実装都合かを再監査する。B2 contract、GUI、report formatの変更が必要ならB3を進めずscope逸脱として報告する。

### Step 1: production VMD validator

- `src/vmd_writer/validator.py`を追加する。
- fixed layout、bounded count、exact size、all-record comparison、zero tail sections、EOFを実装する。
- malformed countで大きなallocationやunbounded loopを行わない。
- test helperやGUI moduleへ依存させない。

### Step 2: VMD adapter

- `src/core/delivery_artifacts.py`へVMD operationを追加する。
- effective planからresolved name付きframeを一回だけ構築する。
- current snapshotのmorph frame countと照合する。
- stagingへwrite後、Step 1のvalidatorでread-backする。
- write / validation errorを別codeへ正規化する。

### Step 3: MMD用WAV adapter

- source identity pre-checkを追加する。
- cancellable runnerを`export_mmd_wav()`へ注入する。
- exporter resultと`MMD_WAV_SPEC`を照合する。
- source identity post-checkを追加する。
- cancel、write failure、validation failure、source changeを区別する。

### Step 4: diagnostic report adapter

- 同一snapshot / timestampからexpected bytesを構築する。
- existing atomic report writerをstaging pathへ呼ぶ。
- final bytesをstrictに再検証する。
- B4のfield追加を先行実装しない。

### Step 5: production operation factory

- 3 operationを`DeliveryArtifactOperations`へ固定順で束ねるfactoryを追加する。
- factory生成物が可変GUI / settings / destination stateをcaptureしないことをtestする。
- `delivery_package.py`のB2 orchestrationを変更せず、fake operationとactual operationのどちらも同じseamへ入ることを確認する。

### Step 6: B3 tests

- validator単体で正常VMDと全破損matrixを確認する。
- adapter単体で正本source、identity、format、error mapping、cancel token伝播を確認する。
- actual operationsをB2 orchestrationへ注入し、成功時に固定3成果物だけがfinalへcommitされることを一時test directoryで確認する。
- いずれか1成果物のwrite / validation失敗、source changeではfinalが作成されず、B2 cleanupが働くことを確認する。

### Step 7: diff / boundary監査

- B2 transaction、GUI、individual save、report format、WAV spec、runtime dataへ差分がないことを確認する。
- `src/core/__init__.py` / `src/vmd_writer/__init__.py`へ不要なexportが追加されていないことを確認する。
- dependency、build、package、license、networkに差分がないことを確認する。
- B3 target tests、指定回帰、`compileall`、`git diff --check`を一コマンドずつ実行する。
- pass表示とprocess exit codeを別々に記録する。

## 10. 状態遷移 / データ契約

### 10.1 B3 operation flow

```text
DeliveryStartContext (ready, immutable)
  -> B2 creates owned staging directory
  -> VMD operation
       EffectiveShapePlan + ordered output names
       -> prepared morph frames
       -> write staging VMD
       -> production read-back validation
  -> MMD WAV operation
       source identity pre-check
       -> original source audio + MMD_WAV_SPEC + cancellable FFmpeg
       -> existing WAV validation
       -> source identity post-check
  -> report operation
       same OutputDiagnosticsSnapshot + same generated_at
       -> existing atomic report writer
       -> exact final-byte validation
  -> all 3 operations returned normally
       -> B2 exact staging-content validation
       -> B2 awaiting_commit_guard
       -> B2 no-clobber commit or cleanup
```

B3は`awaiting_commit_guard`以降の状態を変更しない。B3 operationの正常returnは「この成果物の生成・形式検証完了」を意味し、「package commit済み」を意味しない。

### 10.2 artifact input / output

| kind | input | output | B3 terminal success condition |
| --- | --- | --- | --- |
| `vmd` | effective plan、model name、ordered morph names | fixed staging `_lip.vmd` | read-back全項目一致 |
| `mmd_wav` | original probe source、source identity、FFmpeg、MMD spec | fixed staging `_mmd.wav` | existing WAV validation + pre/post identity一致 |
| `report` | same diagnostics snapshot、timezone-aware timestamp | fixed staging `_report.txt` | expected bytes完全一致 |

### 10.3 VMD record不変条件

- expected frame列は一回だけ構築し、writerとvalidatorへ同じtupleを渡す。
- morph nameはresolved JapaneseまたはLatin ordered setの要素だけである。
- record countとorderはexpected tupleと一致する。
- frame indexは非負uint32でexact一致する。
- valueはwriter finalization後のfloat32 bytesでexact一致する。
- bone、camera、light、self-shadow、IKのcountは0である。
- header / model fieldが一致し、truncated / extra-tailがない。

### 10.4 source audio identity不変条件

```text
start_context.source_identity
  == identity immediately before FFmpeg
  == identity after exporter format validation
```

いずれかが成立しなければWAV operationは正常returnしない。生成済みstaging WAVが存在してもB2 commitへ進めない。

### 10.5 report snapshot不変条件

- writer inputとexpected formatter inputは同一snapshot object / valueである。
- writer timestampとexpected formatter timestampは同一`report_generated_at`である。
- `projection_generation`を再採番しない。
- report operation中にcurrent GUI snapshotを再構築しない。
- formatterが現在省略するdefault profile / morph欄をB3独自に追記しない。

### 10.6 failure / cancel handoff

| B3結果 | B2で期待する扱い |
| --- | --- |
| operation正常return | 次artifactまたはcommit guardへ進む |
| safe code付きfailure | `primary_status=failed`、staging cleanup、finalなし |
| token cancel済み中のoperation例外 / return | `primary_status=cancelled`、staging cleanup、finalなし |
| VMD / WAV / report validation failure | 対応するvalidation code、commit禁止 |
| source identity change | `source_audio_changed`、commit禁止 |

B3はcleanup status、commit phase、final pathを独自生成しない。これらはB2 `DeliveryTerminalResult`の責務である。

## 11. テスト方針

### 11.1 新規B3 tests

`tests/test_ms25_b3_vmd_readback_validation.py`:

- Japanese / Latinの正常VMD
- empty morph record列の正常VMD
- model fieldとrecord order / frame / valueのexact一致
- header 1 byte破損
- model field不一致
- bone count非0
- morph count不足 / 過大 / `MAX_MORPH_FRAMES`超過
- record途中truncation
- morph name field不一致、不正padding、Shift_JIS decode不能
- frame index不一致
- float32 value不一致、NaN / infinity
- camera / light / self-shadow / IK countの各非0
- tail count途中truncation
- 余分な末尾1 byte
- expected record入力のnegative frame、unsupported name、non-finite / negative value拒否
- expected countからのbounded file-size判定によりmalformed countで過大allocationしないこと

`tests/test_ms25_b3_delivery_artifacts.py`:

- factoryが3 callableを返し、GUI / SettingsStoreへ依存しない
- VMD adapterがeffective planとresolved namesからframeを一回だけ構築する
- VMD adapterが同じframe tupleをwriter / validatorへ渡す
- Japanese / Latin names、model name、snapshot morph countの一致
- VMD write failure / validation failureのcode分離
- WAV adapterがinternal analysis WAVではなく`audio_probe.source_path`をrunner入力にする
- WAV adapterが同じdelivery cancel tokenをcancellable runnerへ渡す
- WAV resultのsource pathを解決済み`SourceAudioIdentity.resolved_path`と比較し、relative path / symlink / junctionの正常系を誤拒否しない
- source identityが生成前に変わった場合、runner未開始で`source_audio_changed`
- fake runner中にsourceを変更した場合、post-checkで`source_audio_changed`
- valid stereo 16-bit / 44100Hz simple WAVの成功
- mono、invalid chunk、empty output、result spec / output path / size不一致の`mmd_wav_validation_failed`
- FFmpeg / permission / replace failureの`mmd_wav_write_failed`
- cancel中のFFmpeg failureがB2で`output_cancelled`になる
- report writerがcontextのsame snapshot / timestampを受ける
- report UTF-8 / LF / BOMなし / expected bytes一致
- report write failure / final byte corruptionのcode分離
- active preset、active profile、Latin morph set、Whisper selected / active / loaded / analysis identityを持つsnapshotで、生成reportが同じsnapshot由来になる
- profile未使用・既定morph set欄の必須化はB4未実装として先取りしない
- actual operationsをB2 orchestrationへ注入したsuccessで固定3 filesだけがcommitされる
- VMD / WAV / report各failureとsource changeでfinalなし、owned staging cleanup
- success / failure / cancelで個別保存履歴とruntime user dataを変更しない

### 11.2 既存回帰

B3実装後に少なくとも次を回帰する。

- B1 / B2:
  - `tests/test_ms25_b1_delivery_contract.py`
  - `tests/test_ms25_b1_current_state_gate.py`
  - `tests/test_ms25_b2_windows_paths.py`
  - `tests/test_ms25_b2_delivery_orchestration.py`
  - `tests/test_ms25_b2_delivery_commit.py`
- VMD:
  - `tests/test_ms21_b5_adjusted_vmd_save.py`
  - `tests/test_ms21_b5_effective_output_identity.py`
  - `tests/test_ms23_b2_morph_name_adapters.py`
  - `tests/test_vmd_writer_intervals.py`
  - `tests/test_vmd_writer_zero_guard.py`
  - `tests/test_pipeline_and_vmd.py`
- MMD用WAV:
  - `tests/test_ms17_b7_mmd_wav_export.py`
  - `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
  - `tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py`
- diagnostic report / identity:
  - `tests/test_ms20_b6_diagnostic_report.py`
  - `tests/test_ms23_b6_model_profile_lifecycle.py`
  - `tests/test_ms24_whisper_diagnostics.py`

### 11.3 実装後の実行順

各commandは一つずつ実行し、pass表示とprocess exit codeを別々に記録する。

1. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b3_vmd_readback_validation.py`
2. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b3_delivery_artifacts.py`
3. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b3_vmd_readback_validation.py tests/test_ms25_b3_delivery_artifacts.py`
4. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py tests/test_ms25_b2_windows_paths.py tests/test_ms25_b2_delivery_orchestration.py tests/test_ms25_b2_delivery_commit.py`
5. `.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms21_b5_effective_output_identity.py tests/test_ms23_b2_morph_name_adapters.py`
6. `.\.venv\Scripts\python.exe -m pytest tests/test_vmd_writer_intervals.py tests/test_vmd_writer_zero_guard.py tests/test_pipeline_and_vmd.py`
7. `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py`
8. `.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b6_diagnostic_report.py tests/test_ms23_b6_model_profile_lifecycle.py tests/test_ms24_whisper_diagnostics.py`
9. `.\.venv\Scripts\python.exe -m compileall -q src tests`
10. `rg -n "[ \t]+$" src/core/delivery_artifacts.py src/vmd_writer/validator.py tests/test_ms25_b3_delivery_artifacts.py tests/test_ms25_b3_vmd_readback_validation.py`
11. `git diff --check`

10の`rg`はno-matchのprocess exit code `1`を「末尾空白なし」として扱う。全commandはPowerShellで個別に実行し、shell pipelineやcommand chainを使わない。

full pytestはB7の横断回帰責務とする。B3実装中に共通writerや既存moduleへ想定外の変更が必要になった場合、影響範囲に比例して追加実行するが、未実施なら未実施と報告する。test fixtureのfake runner通過を実FFmpeg / 実MMD確認済みとは扱わない。

### 11.4 手動確認境界

- B3はvisible GUI actionを追加しないため、manual GUI確認を受け入れ必須にしない。
- B3自動testはtemporary directoryとfake FFmpeg runnerを使用してよい。
- repo-local実FFmpegによる実音声変換を実施した場合は、fixture testと分けて記録する。未実施なら未検証とする。
- folder dialog、Busy、progress、cancel button、window closeはB5 / B6。
- profile未使用・既定morph setのreport表示はB4。
- MMDでのVMD / WAV読込・再生・リップ同期はMS26。
- onefile / package / releaseはMS27。

## 12. 受け入れ条件

### 12.1 production operation

- [ ] `build_delivery_artifact_operations()`がB2のexact 3 callableを返す。
- [ ] operationはGUI / SettingsStore / individual save historyへ依存しない。
- [ ] operationはstaging pathへだけ成果物を生成し、final commitを行わない。
- [ ] fixed artifact namingとVMD -> WAV -> report順をB2から変更しない。

### 12.2 VMD

- [ ] VMDは開始contextの同じ`EffectiveShapePlan`から再生成される。
- [ ] resolved Japanese / Latin ordered morph namesをframe adapterとwriterへ明示的に渡す。
- [ ] hold / softness / adjustmentをeffective planへ二重適用しない。
- [ ] production validatorがheader、model field、bone count 0、morph count、全record、camera / light / self-shadow / IK count 0、EOFを確認する。
- [ ] recordのname / frame / serialized float32 value / orderがexpected frame tupleと一致する。
- [ ] truncated data、過大count、余分な末尾byteでoperationが失敗し、B2 commitへ進まない。
- [ ] validatorはtest helperへ依存しない。

### 12.3 MMD用WAV

- [ ] MMD WAVは`audio_probe.source_path`から生成され、internal analysis WAVを使わない。
- [ ] existing `export_mmd_wav()`と`MMD_WAV_SPEC`を再利用する。
- [ ] cancellable runnerへ同じdelivery cancel tokenを渡す。
- [ ] source identityを生成直前と既存WAV validation後に再取得し、開始contextと全field比較する。
- [ ] source identity不一致または再取得失敗は`source_audio_changed`となり、commitされない。
- [ ] WAV resultがPCM 16-bit / 44100Hz / stereo 2ch / simple RIFF-WAVE契約に一致する。

### 12.4 diagnostic report

- [ ] reportは開始contextの同じ`OutputDiagnosticsSnapshot`と`report_generated_at`から生成される。
- [ ] writer後のbytesが同じformatterのexpected bytesと完全一致する。
- [ ] UTF-8 strict、BOMなし、LF、末尾LFを確認する。
- [ ] active preset、profile使用時のprofile / morph set、Whisper identityが開始snapshotと一致する。
- [ ] profile未使用・既定morph set欄の必須化をB3で先行実装しない。
- [ ] report failureでworkspace diagnostics state、fingerprint、WARNING確認済みidentityを変更しない。

### 12.5 error / transaction / coexistence

- [ ] write failureとvalidation failureを成果物別structured codeで区別する。
- [ ] raw exception、traceback、credential、stderr全文、不要なabsolute pathをterminal codeへ含めない。
- [ ] cancel済みoperationをsuccessとして返さない。
- [ ] B2 `DeliveryTerminalResult`、cleanup、commit phase、no-clobber semanticsを変更しない。
- [ ] VMD / WAV / reportのどれかが失敗した場合、final directoryが作成されない。
- [ ] 個別VMD、個別MMD WAV、standalone reportの既存導線と保存履歴を変更しない。
- [ ] runtime INI / JSON、dependency、build / package fileに差分がない。

### 12.6 verification

- [ ] B3新規testsがpass表示かつprocess exit code `0`である。
- [ ] §11.2の指定回帰がpass表示かつprocess exit code `0`である。
- [ ] `compileall -q src tests`と`git diff --check`がprocess exit code `0`である。
- [ ] manual GUI、実FFmpeg、実MMD、Python 3.11 / 3.12、onefile / releaseを実施していない場合は未検証と報告する。
- [ ] 変更fileが§7.1の4 filesだけである。追加変更が必要な場合はscope根拠を示し、B3外の変更を自動で行わない。

## 13. リスクと対策

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS25-B3-R1 | effective planではなく個別保存済みVMDやPreview表示からVMDを作る | P1候補 | B1 contextのeffective planだけを入力にし、prepared frame tupleをwriter / validatorへ共有する |
| MS25-B3-R2 | output morph namesを省略し、Latin profileを日本語名で出力または拒否する | P1候補 | contextのordered namesをadapterとwriterへ明示し、日本語 / Latin双方を直接testする |
| MS25-B3-R3 | hold / softnessをeffective planとwriterで二重適用する | P1候補 | prepared effective plan経路ではwriterへraw tail parameterを渡さない |
| MS25-B3-R4 | writer returnだけでVMDを成功扱いし、truncationや末尾破損をcommitする | P1候補 | production read-back validatorと全binary section / exact EOF testを必須化する |
| MS25-B3-R5 | validatorがcountを信頼して過大read / allocationを行う | P1候補 | expected count / `MAX_MORPH_FRAMES` / exact file sizeを先に検証し、bounded parserにする |
| MS25-B3-R6 | analysis WAVや個別WAVをMMD用sourceとして使う | P1候補 | `audio_probe.source_path`だけをexporterへ渡し、runner引数をtestする |
| MS25-B3-R7 | sourceがFFmpeg中に差し替わり、VMDとWAVの素材identityがずれる | P1候補 | source identityのpre / post比較。content hash非採用の限界を明記する |
| MS25-B3-R8 | non-cancellable runnerを使い、delivery cancelがFFmpeg processへ届かない | P1候補 | `run_ffmpeg_mmd_wav_cancellable()`とB2 tokenのexact伝播を固定testする |
| MS25-B3-R9 | `AudioConvertError.info.code`をB2が読めず、validation failureがwrite failureへ潰れる | P2候補 | B3 adapterでenumを明示的なdelivery codeへ写像する |
| MS25-B3-R10 | reportを別snapshot / 別timestampから再構成する | P1候補 | writer / expected formatterへ同じcontext fieldを渡し、object / value一致をtestする |
| MS25-B3-R11 | B3でdefault profile / morph欄を独自追記し、B4とformatter責務が重複する | P2候補 | B3はexisting formatterのbyte一致だけを所有し、field必須化をB4へ維持する |
| MS25-B3-R12 | operationがfinal directoryを作る、B2 stagingをrename / cleanupする | P1候補 | operationは渡されたfile pathだけを扱い、commit / directory cleanup APIをimportしない |
| MS25-B3-R13 | B3 failureが個別保存履歴やworkspace diagnosticsを変更する | P2候補 | GUI / SettingsStore非依存のpure adapterにし、state不変回帰を追加する |
| MS25-B3-R14 | float比較の広いtoleranceが別値を受理する | P2候補 | writer finalization後のexpected float32 bytes exact比較を使う |
| MS25-B3-R15 | B2未実装という既存文書記述へ引っ張られ、実装済みseamを再実装する | P2候補 | live HEAD / code / testを優先し、B2 fileをB3変更対象外に固定する |
| MS25-B3-R16 | Index / B2 planの状態欄がlive B2実装と不一致 | 後続文書同期 | 本planでlive優先順位を明記し、他文書変更禁止を守る。B7または別文書同期で解消する |
| MS25-B3-R17 | Pipelineの日本語morph限定表記、WAV仕様の1ch許容表記が、現行Japanese / Latin・delivery stereo 2ch実装と局所的に不一致 | 後続文書同期 | 現行code / testと新しいMS23・WAV固定仕様をB3正本とし、B7で正文仕様を同期する |
| MS25-B3-R18 | `export_mmd_wav()`へcancellable runnerを渡しても、runner引数にtokenを束縛しなければFFmpegへcancelが届かない | P2候補 | adapterが`run_ffmpeg_mmd_wav_cancellable()`を同一`DeliveryCancelToken`へ束縛して注入し、同一tokenの伝播をtestする |
| MS25-B3-R19 | `MmdWavExportResult.source_path`は入力時の未解決pathだが、開始contextは解決済みidentityを持つため、直接比較するとsymlink / junction / relative pathを誤拒否する | P2候補 | result source / output pathを`Path.resolve(strict=False)`で正規化して比較し、path形式の違いを含む回帰を追加する |

### 13.1 P1 / P2 / P3自己監査

初回案を現行code / test / docへ再照合し、次を計画本文へ反映した。

| finding | 初期の曖昧さ | 本文での修正 | 状態 |
| --- | --- | --- | --- |
| P1-1 | B3がB2 orchestrationへactual writerを直書きし得た | 新規`delivery_artifacts.py`のfactoryだけを追加し、B2 fileを変更対象外へ固定 | 解消 |
| P1-2 | VMD value比較が一般的なfloat toleranceだけだった | writer finalization後のfloat32 bytes exact比較へ固定 | 解消 |
| P1-3 | WAV生成前だけのsource identity確認だった | exporter validation後のpost identity確認を必須化 | 解消 |
| P1-4 | generic non-cancellable WAV runnerを使う余地があった | existing cancellable runnerとsame token伝播へ固定 | 解消 |
| P2-1 | `AudioConvertError`とB2 `error.code`の形が違い、codeが潰れ得た | adapterのexplicit error mapping表を追加 | 解消 |
| P2-2 | report format validationとB4 field拡張が混在していた | B3はsame formatter bytes、B4はfield必須化へ分離 | 解消 |
| P2-3 | writer parametersのhold / softnessを再適用する余地があった | effective planは解決済みとして二重適用禁止を明記 | 解消 |
| P2-4 | malformed VMD countに対するresource boundが未定義だった | exact expected sizeと`MAX_MORPH_FRAMES`をparser前gateへ追加 | 解消 |
| P2-5 | 成果物別codeを持たない固有例外がB2 fallbackへ潰れる余地があった | 全成果物のadapter境界で既存`DeliveryContractError`へ変換すると明記 | 解消 |
| P2-6 | snapshotのmorph frame count参照先と`None`時の扱いが現行B1 DTOより厳しかった | `adjustment_summary.effective_morph_frame_count`を正しく参照し、`None`をB3独自拒否条件にしない | 解消 |
| P2-7 | `export_mmd_wav()`の注入runnerへcancel tokenを渡す方法が未指定で、cancellable契約が実装上抜け得た | adapter側でcancellable runnerを同一tokenへ束縛するclosure / `partial`を明記し、exporter signatureを変更しない | 解消 |
| P2-8 | `MmdWavExportResult.source_path`の未解決pathと`SourceAudioIdentity.resolved_path`の比較方法が未指定で、symlink / junction / relative pathの正常入力を誤拒否し得た | result source / output pathを`Path.resolve(strict=False)`で正規化し、解決先identityとの比較と回帰条件を追加 | 解消 |
| P3-1 | B2未実装という既存文書状態をcurrent事実と誤認し得た | live HEAD優先と既存文書driftを§1.1へ明記 | 本plan内は解消。外部文書はB7同期事項 |
| P3-2 | Pipeline / WAV仕様の局所的な旧表現が現行code / testとずれていた | §6.1 / §6.4で採用する現行契約を固定し、B7同期対象へ明記 | 本plan内は解消。外部文書はB7同期事項 |
| P3-3 | 標準14節に対して要判断・引き継ぎが独立した第15節になっていた | 第14節のsubsectionへ統合 | 解消 |

本plan本文に未解消のP1 / P2 / P3は残っていない。Pipeline / WAV正文仕様の局所的な旧表現は、採用する現行契約をcode / testと本planで確定した上で、変更権限外のB7文書同期事項として残す。

## 14. Codex実装時の注意

- コマンドは必ず一つずつ実行し、shell pipeline、chain、parallel executionを使わない。
- 実装開始時にlive Gitとuser-owned差分を再確認する。
- B3は§7.1の4 filesに限定する。B2 transaction、GUI、report format、individual saveを変更しない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読書き、コピー、stageしない。
- `EffectiveShapePlan`をGUI表示やtiming planから再解決しない。contextに固定済みのplanを使う。
- resolved output morph namesを省略せず、Japanese / Latinの両経路をtestする。
- VMD validatorをtest codeからcopy / importしない。production parserとして新設する。
- VMD count / offsetを検証せず`struct.unpack_from()`しない。
- broad float tolerance、trailing byte無視、未知section無視でvalidatorを通さない。
- prepared effective planへhold / softnessを再適用しない。
- MMD WAV sourceへanalysis WAVを使わない。
- `run_ffmpeg_mmd_wav()`の非cancellable経路をdeliveryへ使わない。
- source identityのpost-checkをexporter validationより前へ移動しない。
- content hashを暗黙追加せず、現行identity保証を過大説明しない。
- `format_diagnostic_report()`のfield構成をB3で変更しない。
- report expected bytesを別snapshotや現在GUI表示から構築しない。
- raw exception message、full path、stderr全文をdelivery error codeへ連結しない。
- operation failure時にfinal、parent、B2 staging rootを独自削除しない。
- B2の`DeliveryTerminalResult`をB3独自resultで置き換えない。
- 個別VMD / WAV / reportのmethod、dialog、保存履歴を変更しない。
- testを削除、skip、期待値弱化して合格させない。
- actual symlink / reparse、実FFmpeg、GUI、実MMD、onefileを実施していなければ未検証と記録する。
- pytestのpass表示とprocess exit code、`compileall`、`git diff --check`を別々に記録する。
- stage、commit、merge、push、tag、releaseは別の明示承認まで行わない。

### 14.1 要ユーザー判断

現時点で要ユーザー判断はない。

- VMD read-backはexact binary layout / record / EOF検証を推奨案として採用する。理由はBlock Breakdownの明示契約であり、広いfloat toleranceやheaderだけの検査では破損を見逃すためである。
- adapterは新規`src/core/delivery_artifacts.py`へ分離する。理由はB2 transactionを変更せず、B3のformat-specific責務を独立させるためである。影響は新規production module 1件に限定され、既存public APIを壊さない。
- report default identity欄の追加はB4へ維持する。理由はBlock BreakdownでB4責務として分離済みであり、B3で実装するとformat contractが重複するためである。

### 14.2 後続Blockへの引き継ぎ

- MS25-B4:
  - profile未使用・既定日本語morph setを含むpreset / profile / morph set / Whisper identity欄をreportへ必須化する。
  - B3 report adapterのsame-snapshot / exact-bytes contractはそのまま再利用する。
- MS25-B5:
  - `build_delivery_artifact_operations()`をB2 orchestrationへ注入する。
  - delivery worker、Busy、WARNING、destination dialog、long-audio confirmation、job-bound commit authorization、close待機を接続する。
- MS25-B6:
  - actual Windows collision / reparse / locked / cleanup / shutdown matrixでB2 / B3をhardeningする。
- MS25-B7:
  - full / cross-boundary regressionを実行する。
  - README、配布用readme、Pipeline / GUI / Error / VMD / WAV仕様、Index、Roadmapの実装済み状態を同期する。
  - Index / B2 planのlive B2実装との状態不一致を文書同期対象として確認する。
  - Pipelineのmorph name旧表現とWAV validationのchannel count旧表現を、Japanese / Latin・delivery stereo 2chの現行契約へ同期する。
- MS26:
  - 実MMDでdelivery VMD / WAVの読込、再生、リップ同期を確認する。
- MS27:
  - onefile、ZIP、最終artifact、package / release readinessを確認する。
