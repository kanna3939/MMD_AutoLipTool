# MS25-B7 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B7 回帰・利用者向け文書・Closeout準備
- 作成日: 2026-09-04
- 対象ブランチ: `feature/MS25-implementation`
- 計画作成時HEAD: `5300905 Implement MS25-B6 delivery recovery hardening`
- 計画作成前Git状態: clean、未追跡ファイルなし
- B7実施時検証HEAD: `0b25c5c Document MS25-B7 implementation plan`。このHEAD以降の変更はB7文書だけであり、production code / test codeの検証対象は変わっていない
- 文書状態: B7の自動検証、文書同期、finding判定を完了し、MS25 Closeout Aと判定した。B7実施で更新した文書は未commitのworking treeにある
- 初回計画策定で変更したファイル: `docs/Implementation_Plan/MS25-B7_Implementation_Plan.md`のみ。計画監査後、current-state P2 / P3解消のため、対象を限定して関連文書も補正した。
- B7実施時の原則: production code、test code、GUI、dependency、build設定を変更せず、既存実装の横断回帰、文書同期、Closeout準備を行う
- 後続境界:
  - MS26: 実MMDでのVMD / WAV読込・再生・リップ同期確認
  - MS27: PyInstaller onefile、ZIP、最終artifact、package / release readiness

### 1.1 正本と現行状態の優先順位

判断は次の順で行う。

1. live Git、現行production code、現行test、実行したcommandのprocess exit code
2. `docs/Implementation_Plan/MS25_Block_Breakdown.md`
3. `docs/MS20_and_Beyond_Roadmap.md` §12〜§15
4. Pipeline / Error / GUI State / VMD Outputの各正文仕様
5. MS25-B1〜B6 Implementation Plan
6. `README.md`、`readme_mmdautolip.txt`、routing / milestone履歴文書

過去計画の「未実装」「未commit」「後続で実施」は、live Gitと後続commitが反証する場合は履歴記述として扱う。B7では履歴そのものを消さず、現在状態を示す箇所だけを実測結果へ同期する。

### 1.2 計画作成時に確認したcurrent driftとメイン側補正

- 初回確認時、live GitではB6実装が`5300905`としてcommit済みである一方、MS25 Block Breakdown、MS25-B6 plan、Index、RoadmapにはB6をworking tree反映済み・未commitとする2026-09-04時点の記述が残っていた。メイン側でcurrent-state欄を`5300905`へ同期し、過去時点の履歴記述は保持したため、このP3候補は解消済みである。
- `README.md`と`readme_mmdautolip.txt`には、既に一括出力導線、3成果物名、既定folder名、再生成、collision、merge / replace禁止、実MMD確認留保が記載されている。B7は追記ありきではなく、現行挙動との最終照合を行い、不足または誤記がある場合だけ変更する。
- `docs/GUI_State_Theme_Specification.md`には同じ`8.4`番号が二つ存在した。メイン側でMS25節を`8.6`へ補正し、参照先と本文意味を変えずに番号を一意化したため、このP3候補は解消済みである。
- Error仕様には`output_path_too_long`が代表codeとして残る一方、現行MS25 coreはpath長超過を`output_path_invalid`へ正規化する。これは現行coreの実行codeと既存UI互換aliasの区別を明記すべきP2候補だったため、Error仕様へその関係を注記し、B7ではcode変更ではなく一覧・safe message・利用者文言の最終整合だけを確認する。
- 再チェックでは、Block Breakdownの`§11.4`回帰ゲートをB7実測前に`[x]`としていたため、B6履歴baselineとB7実測を混同するP2を確認した。メイン側で`[ ]`へ戻し、B7同一HEADの実測が必要であることを明記したため解消済みである。
- 再チェックでは、Indexのcurrent phaseとrouting tableにB7計画書の作成状態・リンクがなかったためP3を確認した。メイン側で`MS25-B7 Implementation Plan Created`と計画書リンクを追加し、B6のrouting名も実装計画へ補正したため解消済みである。
- 再チェックでは、`git diff --check`が未追跡のB7計画書を検査対象にしないためP3を確認した。stageせずに`git diff --no-index --check -- NUL <path>`を個別実行し、exit code `1`を正常差分、診断出力なしを合格とする手順を§11.5 / Step 13へ追加したため解消済みである。
- B7実装前チェックでは、Block Breakdownがcross-boundary回帰の追加を許容するように読める一方、B7計画はtest code変更を禁止していたためP2を確認した。Block Breakdownを「既存回帰を実行し、coverage不足はfinding化して別repairへ分離」と補正し、B7内のtest code変更禁止と一致させたため解消済みである。
- B7計画再検証では、Block Breakdownのfull pytestが「必要に応じて」となっていたため、B7計画の必須automated gateと不一致になるP2を確認した。Block Breakdownを必須へ補正し、B7計画の要求と一致させたため解消済みである。
- 同再検証では、Block Breakdownのstatic gateに未追跡文書のwhitespace検査が明記されていないP3を確認した。tracked差分と未追跡文書の個別検査、および`--no-index`のexit code `1` / 空出力判定をBlock Breakdownへ追加したため解消済みである。

## 2. 背景

MS25は、現在の編集済み`EffectiveShapePlan`から再生成したVMD、入力音声から再生成したMMD用WAV、同じ開始snapshotから生成した診断レポートを、一つの専用directoryへtransactionalに確定する機能である。

B1〜B6で次の境界が実装済みである。

- B1: `DeliveryCurrentState`、`DeliveryStartContext`、source audio identity、固定成果物名、start gate、WARNING確認単位、semantic fingerprint
- B2: parent / folder / Windows path検証、同一親directory staging、固定順生成、pre-commit authorization、no-clobber rename、cancel / terminal DTO
- B3: current effective VMD、入力音声由来MMD WAV、同一snapshot reportの生成adapter、production VMD read-back validator、source identity再確認
- B4: preset、model profile、resolved morph-name set、Whisper selected / active / loaded / analysis identityを省略しないreport表現
- B5: `ファイル > MMD一括出力...`、destination dialog、delivery worker、Busy、cancel、close、late-result discard、UI thread上のcommit guard
- B6: actual Windows junction / sharing violation gate、staging identity再確認、OS fault分類、TOCTOU / no-clobber hardening、cleanup failure terminal化、close state reconciliation

B6実装時の記録では、B6専用`26 passed`、B6直接回帰`134 passed, 2 skipped`、指定cross-boundary`94 passed`、全pytest`1041 passed, 4 skipped`、`compileall -q src tests`、`git diff --check`がprocess exit code `0`である。Windows actual junction collisionとsharing violationもskipなしで通過し、ユーザーからB6手動GUI確認通過・問題なしの報告を受領している。

ただし、これらはB6実装時の履歴証拠であり、B7の同一HEAD full cross-boundary regressionを代替しない。B7では`5300905`またはB7開始時の最新承認済みHEADに対して、B1〜B6の要求、source、test、文書、手動証拠を一つのevidence ledgerへ対応付け、MS25のCloseout可否を判断できる状態にする。

## 3. 目的

1. B1〜B6の要求、実装commit、source、test、文書、manual evidenceを同一HEADへ対応付ける。
2. delivery transactionとMS20〜MS24のdiagnostics、effective output、VMD、MMD WAV、worker、voice-only、profile、Whisper identity、個別保存導線を横断回帰する。
3. B6のactual Windows fault gateをB7でも独立再確認し、skipや環境差を履歴値で隠さない。
4. `README.md`と`readme_mmdautolip.txt`を、現行利用手順、3成果物、collision、失敗保護、個別保存との共存、実MMD留保へ同期する。
5. Pipeline / GUI State / Error Handling / VMD Outputの正文仕様を、B1〜B6の確定契約と現行codeへ同期する。
6. Index、Roadmap、Block Breakdown、milestone / version-control記録へ、実装済み、検証済み、ユーザー報告、未検証、deferredを区別して反映する。
7. P1 / P2 / P3、未検証事項、次工程を記録し、MS25 Closeout A / 条件付き / 不合格を根拠付きで判定できる状態にする。

## 4. In Scope

- B1〜B6のrequirement-to-evidence ledger作成
- MS25-B1〜B6専用testの同一HEAD再実行
- MS20〜MS24とのfull cross-boundary regression
- VMD writer、diagnostic report、MMD WAV、worker terminal、GUI state、voice-only、workspace reset、individual save flowの回帰
- actual Windows filesystem上のjunction / reparse collisionとpermission deniedまたはsharing violationのB6 gate再確認
- full pytestの実行
- `compileall -q src tests`、`git diff --check`、MS25差分scope監査
- pass数、fail数、skip数、skip理由、process exit code、実行HEADの記録
- B5 / B6で受領したユーザー手動GUI証拠のcurrent HEADへの対応付け
- README / 配布用readmeの最終照合と必要最小限の同期
- Pipeline / GUI State / Error Handling / VMD Output正文仕様の最終照合と必要最小限の同期
- Index、Roadmap、Block Breakdown、B6 plan、B7 plan、`repo_milestone.md`、`Version_Control.md`のcurrent-state / closeout記録同期
- finding ledger、Closeout判定、MS26 / MS27へのhandoff

## 5. Out of Scope

- production code、test code、GUI実装の変更
- failing test、coverage gap、contract gapのB7内修正。必要な修正はfinding化し、別のrepair plan / repair implementationへ分離する
- testの削除、skip追加、assertion緩和、対象縮小による合格化
- MS25-B1〜B6のpublic contract、成果物名、transaction、terminal DTO、fingerprint schema、error codeの再設計
- 個別VMD保存、個別MMD WAV出力、個別report保存の仕様変更
- `.autolip`等のsession file、MMD project管理、MMD本体directory管理
- ZIP生成、ZIP必須化、保存後のMMD自動起動
- 実MMDでのVMD / WAV読込・再生・リップ同期確認。MS26へ延期する
- Python 3.11 / 3.12 compatibilityの新規環境構築・受入判定
- PyInstaller onefile、SmokeLaunch、ZIP、最終artifact、package manifest、release readiness。MS27へ延期する
- dependency、lock file、PyInstaller spec、build script、license文書の変更
- MS24 Whisper model selection、download、runtime identity契約の再実装
- cloud ASR、音声外部送信、telemetry、background通信
- Qt / PySide6の復活
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接読取り・変更・コピー・fixture化・stage
- push、merge、tag、release、branch削除

## 6. 前提条件

### 6.1 B1〜B6 commit baseline

| Block | 実装commit | 到達状態 |
| --- | --- | --- |
| MS25-B1 | `a41f0a0 Implement MS25-B1 delivery state gate` | 実装・自動検証済み。可視GUI actionがないためmanual GUI不要と記録 |
| MS25-B2 | `0f018cd Implement MS25-B2 delivery package orchestration` | core transaction実装済み |
| MS25-B3 | `904ccae Implement MS25-B3 delivery artifact adapters` | 3成果物adapterとVMD read-back実装済み |
| MS25-B4 | `01b4d4f Implement MS25-B4 diagnostic report identity` | report identity実装済み |
| MS25-B5 | `bb9c60d Complete MS25-B5 delivery package GUI integration` | GUI / worker実装・自動検証済み。ユーザー報告のmanual GUI通過 |
| MS25-B6 | `5300905 Implement MS25-B6 delivery recovery hardening` | fault / recovery hardening実装・自動検証・Windows gate済み。ユーザー報告のmanual GUI通過 |

### 6.2 B7開始条件

- B7開始時にbranch、HEAD、working treeを再確認する。
- B7が検証するsource / test baselineは、一つの明示的なHEADへ固定する。
- working treeに既存変更がある場合はownerとscopeを確認し、B7証拠へ混入させない。意図不明またはcode / test変更を含む場合はfull regressionとCloseout判定を開始しない。
- B7実施中にrepair commitが追加された場合、repair後の新HEADに対してMS25 aggregate、影響cross-boundary、full pytest、`compileall`、diff監査を最初から再実行する。repair前の合格値を新HEADへ転用しない。
- pytestはpass表示だけでなくprocess exit code `0`を必須とする。
- skipは件数と理由を記録する。B6必須actual Windows caseのskipはB7合格に含めない。
- B6時点のtest値は比較用baselineであり、B7実測値ではない。

### 6.3 固定済み互換境界

- 成果物名は`<audio_stem>_lip.vmd`、`<audio_stem>_mmd.wav`、`<audio_stem>_report.txt`、既定folder名は`<audio_stem>_MMD`。
- VMDはcurrent effective output、WAVはoriginal input audio、reportは同一開始snapshotから再生成する。個別保存済み成果物を流用しない。
- finalと同じ親directory内のowned stagingへ3成果物を生成・検証し、全成功時だけno-clobber renameで公開する。
- 同名entryはempty / non-empty directory、file、symlink、broken symlink、reparse pointを問わずcollisionとし、merge / replace / delete / automatic renameを行わない。
- commit線形化点前のcancel / failureはowned stagingだけをcleanupし、commit開始後のcancelはrename結果を上書きしない。
- cleanup failureはprimary resultを保持し、`partial_output_cleanup_failed`を別fieldで返す。
- semantic save-state fingerprintをcommit guardに使い、`projection_generation`はUI late-result discardへ限定する。
- `ms21-effective-output-v1` fingerprint schema / payloadへWhisper management情報を追加しない。
- reportはpreset、profile、resolved morph set、Whisper selected / active / loaded / analysis identityを省略しない。
- batch parent / folderはsession-onlyで、INIや個別保存履歴へ保存しない。

## 7. 対象ファイル

以下は計画作成時に実在を確認した。B7実施で変更可能なのは文書分類のファイルだけであり、source / test分類はread-only証拠である。

### 7.1 主変更候補。文書のみ

| ファイル | B7での責務 |
| --- | --- |
| `docs/Implementation_Plan/MS25-B7_Implementation_Plan.md` | 実行HEAD、command、result、finding、manual evidence、Closeout判定の実績追記 |
| `docs/Implementation_Plan/MS25_Block_Breakdown.md` | B6 commit済み、B7検証結果、受入条件、次工程をcurrent stateへ同期 |
| `docs/MS20_and_Beyond_Index.md` | 現在フェーズ、B7結果、MS25 Closeout状態、MS26 / MS27 boundaryを同期 |
| `docs/MS20_and_Beyond_Roadmap.md` | §12のMS25到達状態、§13〜§15へのhandoffを同期 |
| `docs/repo_milestone.md` | MS25 B1〜B7成果とCloseout判定の履歴記録。必要箇所だけを対象にする |
| `docs/Version_Control.md` | B7文書同期・Closeout変更の履歴記録。必要箇所だけを対象にする |

### 7.2 利用者向け文書

| ファイル | 最終照合項目 |
| --- | --- |
| `README.md` | 起動導線、親directory、editable folder、既定名、3成果物、再生成、collision、失敗保護、個別保存共存、実MMD留保 |
| `readme_mmdautolip.txt` | 配布利用者向けにREADMEと同じ意味を平易に説明し、MMDでの確認を自動検証済みと誤記しない |

既に必要事項が記載済みなら、無意味な言い換えや重複追記は行わない。「確認した結果、変更不要」もB7 evidenceとして記録する。

### 7.3 正文仕様

| ファイル | 最終照合項目 |
| --- | --- |
| `docs/Pipeline_Data_Contract_Specification.md` | `DeliveryStartContext`、audio role、same snapshot、source identity、fingerprint guard、terminal result、individual save非変更 |
| `docs/GUI_State_Theme_Specification.md` | action state、dialog、Busy、cancel、close reconciliation、late / duplicate result、session-only parent、見出し番号整合 |
| `docs/Error_Handling_Specification.md` | current error code、OS fault優先順位、collision、stale、cleanup status、safe message、raw path / exception非表示 |
| `docs/VMD_Output_Specification.md` | current effective plan、resolved morph names、production read-back検証、固定成果物名、staging / no-clobber、実MMD留保 |

### 7.4 current-state補正候補

- `docs/Implementation_Plan/MS25-B6_Implementation_Plan.md`: B6のcurrent-stateが`5300905`を示すことを確認する。計画時点の履歴記述は保持する。
- `docs/Implementation_Plan/MS25-B5_Implementation_Plan.md`: 後続B6 / B7状態をcurrent-state欄が明示している場合だけ同期する。B5完了時点の履歴を改変しない。
- MS25-B1〜B4 planは原則read-only。現在状態の正本ではない履歴的なfuture表現だけを理由に書き換えない。
- `docs/MS17_and_Beyond_Index.md`はlegacy routingのため変更しない。

### 7.5 read-only production evidence

- `src/core/delivery_package.py`
- `src/core/delivery_artifacts.py`
- `src/core/diagnostic_report.py`
- `src/core/output_diagnostics.py`
- `src/core/mmd_wav_export.py`
- `src/core/pipeline.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/worker_state.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/vmd_writer/writer.py`
- `src/vmd_writer/validator.py`

### 7.6 MS25 direct tests

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
- `tests/test_ms25_b6_windows_collision_faults.py`
- `tests/test_ms25_b6_delivery_failure_recovery.py`
- `tests/test_ms25_b6_delivery_gui_recovery.py`

### 7.7 cross-boundary tests

#### diagnostics / report / fingerprint

- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_ms24_whisper_error_recovery.py`

#### VMD / effective output / preset / profile

- `tests/test_pipeline_and_vmd.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_vmd_writer_peak_value.py`
- `tests/test_vmd_writer_zero_guard.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_ms22_b6_lifecycle_regression.py`
- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b4_model_profile_state.py`
- `tests/test_ms23_b5_model_profile_controller.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`

#### MMD WAV / individual save

- `tests/test_ms17_b7_mmd_wav_export.py`
- `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
- `tests/test_ms17_b7_mmd_wav_save_dialog.py`
- `tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`
- `tests/test_ms17_b7_mmd_wav_button_state.py`
- `tests/test_wx_ms14_b5_export.py`

#### worker / GUI lifecycle / textless

- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms24_no_implicit_download.py`
- `tests/test_ms24_whisper_model_runtime.py`

上記のtargeted cross-boundary集合とfull pytestは別gateである。full pytestの成功だけで、各境界を意図的に選んだtargeted gateの記録を省略しない。

### 7.8 関連確認対象。原則read-only

- `docs/MS17_and_Beyond_Index.md`: legacy / current routing境界の確認
- `docs/MS20_and_Beyond_Index.md`: current phaseと正本文書routingの確認。B7結果同期時だけ変更候補
- `docs/MS20_and_Beyond_Roadmap.md` §12〜§15: MS25〜MS27のscope / dependency境界
- `docs/Implementation_Plan/MS25_Block_Breakdown.md`: B7責務、回帰gate、受入条件
- `docs/Implementation_Plan/MS25-B1_Implementation_Plan.md`〜`MS25-B6_Implementation_Plan.md`: Block別contract / evidence
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `pyproject.toml`、`requirements.txt`: dependency差分がないことのscope確認。変更しない
- `MMD_AutoLipTool.spec`、`build.ps1`: MS25でpackage / build変更がないことのscope確認。buildは実行しない
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md`: dependency / 配布内容変更がないことだけを確認し、release readinessはMS27へ残す

`docs/repo_milestone.md`と`docs/Version_Control.md`は全体を読み込まず、MS25記録の追加先だけをtargeted search / bounded readする。

## 8. 実装方針

### 8.1 B7は監査・検証・文書同期Blockとする

B7では新しいruntime behaviorを実装しない。現行B1〜B6が満たす契約をcodeとtestから再導出し、同一HEAD上の実測証拠を得た後、利用者文書と正文仕様を到達状態へ同期する。

test failure、contract gap、coverage gap、production / test変更が必要な不一致を見つけた場合は、B7を合格扱いにせずfindingへ記録する。修正はユーザー承認を得た別repairで行い、修正後にB7 gateを新HEADで再実行する。

### 8.2 requirement-to-evidence ledger

少なくとも次の列を持つledgerをB7実施記録へ残す。

| 項目 | 内容 |
| --- | --- |
| Requirement ID | B1〜B6または横断契約の安定ID |
| Requirement | 検証可能な不変条件 |
| Implementation evidence | class / function / field / call path |
| Test evidence | test file、必要ならtest名 |
| Manual evidence | 実施者、日付、対象。不要なら理由 |
| Result | proved / contradicted / insufficient / deferred-by-design |
| Finding | P1 / P2 / P3 IDまたはnone |

「testが存在する」だけではprovedにしない。実行したcommandが対象testを収集し、pass表示とprocess exit code `0`を返したことを確認する。

### 8.3 B1〜B6横断不変条件

| 境界 | 維持する契約 | 主な証拠 |
| --- | --- | --- |
| current state | 一回のcaptureでeffective plan、snapshot、resolved morph names、source identityを固定する | B1 state gate、B3 adapter、B4 report tests |
| artifact naming | Unicodeを保持した固定3名とeditable folder、Windows不正名 / path長は暗黙renameせず拒否 | B1 contract、B2 paths tests |
| audio role | input audio、analysis WAV、MMD WAVを分離し、MMD WAVはoriginal inputから生成 | B3 artifact、MS17 WAV tests |
| VMD output | current effective plan、resolved Japanese / Latin names、30fps、writer sections、EOFをread-back検証 | B3 validator、pipeline / writer tests |
| diagnostics | VMDとreportが同じsnapshot。preset / profile / morph set / Whisper identitiesを省略しない | B4 report、MS20 / MS23 / MS24 tests |
| fingerprint | semantic output identityだけをcommit guardに使い、projection generationやWhisper management表示を混入させない | B1 fingerprint、MS20 / MS21 / MS24 tests |
| filesystem transaction | owned stagingへ固定順生成し、全成功後にno-clobber rename。既存entryを変更しない | B2 orchestration / commit、B6 Windows / recovery tests |
| cancel / cleanup | commit前cancelはcommit禁止、commit開始後cancelは結果を上書きせず、cleanup failureはprimaryと分離 | B2 commit、B5 worker、B6 recovery tests |
| GUI lifecycle | Busy、job / kind / generation binding、commit guard、close待機、late / duplicate discard、retry可能状態 | B5 GUI、B6 GUI recovery、worker tests |
| individual saves | batch success / failure / cancelが個別VMD / WAV / report導線と保存履歴を変更しない | MS20 report、MS17 WAV、MS21 / wx VMD tests |
| Whisper boundary | selected / active / loaded / analysis identityを分離し、暗黙download・外部送信を追加しない | MS24 diagnostics / runtime / no implicit download tests |
| runtime data | batch parent / folderをINIへ保存せず、preset / profile storeを直接操作しない | B5 GUI、diff scope、runtime data非接触確認 |

### 8.4 文書同期の原則

- testとscope auditが合格する前に、MS25を完了済みまたはCloseout Aと記載しない。
- 実装済み、automated verified、manual verified（ユーザー報告）、未検証、deferred-by-designを区別する。
- test件数はcommand、実行HEAD、日付、pass / skip、process exit codeと一組で記録する。
- B6履歴値とB7実測値を混在させない。
- README / readmeは利用者が必要な操作と保護動作を説明し、内部DTOやprivate helperを過剰に露出させない。
- 正文仕様はcodeレベルの不変条件、error code、state / output contractを記録する。
- Index / Roadmapはcurrent stateと後続routingを記録し、履歴節を上書きしない。
- `repo_milestone.md` / `Version_Control.md`は必要箇所だけを読み、MS25 Closeout結果だけを追記する。

## 9. 詳細ステップ

### Step 1: live baseline固定

1. `git status --short --branch`
2. `git branch --show-current`
3. `git log --oneline -n 10`
4. `git branch -vv`
5. `git rev-parse HEAD`

各commandは一つずつ実行する。branch / HEAD / working treeが本計画の前提と異なる場合は、差分を調査してledgerのbaselineを更新する。

### Step 2: scope / runtime-data監査

- `61a2182..HEAD`またはB7開始時のMS25分岐元からのdiff name-statusを取得する。
- production、test、docsの変更をB1〜B6責務へ対応付ける。
- dependency、lock file、PyInstaller spec、build script、licenseへMS25由来の意図しない差分がないことを確認する。
- root runtime data三点を直接開かず、Git inventory / status上で追跡・stage対象になっていないことだけを確認する。
- `.pt`、ZIP、session file、MMD project等がMS25成果へ追加されていないことを確認する。

scope逸脱があればP1〜P3へ分類し、Closeout同期へ進まない。

### Step 3: B1〜B6 evidence ledger

- Block Breakdown、B1〜B6 plan、commit diff、production symbol、direct testを対応付ける。
- 計画に書かれているがcodeにない契約、codeにあるがtestで証明されない契約、testが現行code pathを通らない契約を区別する。
- B6 commit後のcurrent-state文書が`5300905`へ同期済みであることを確認し、過去時点の履歴記述とは分離する。

### Step 4: B6 actual fault gate

- B6専用3ファイルを独立実行する。
- Windows actual junction / reparse collisionとsharing violationまたはpermission deniedが収集・実行され、skipなしでpassしたことをtest outputから確認する。
- B6専用gateがskipされた場合、injection testやB6時点の履歴passで代用しない。

### Step 5: MS25 aggregate

- §7.6の13ファイルを一つの明示commandで実行する。
- artifact name、start context、path、orchestration、commit、adapter、read-back、report identity、GUI / worker、fault recoveryを一括確認する。
- B6専用gateとの重複実行は、B7 aggregateの独立証拠として許容する。

### Step 6: full cross-boundary regression

- §7.7を責務群ごとに実行する。
- diagnostics / report / fingerprint、VMD / effective output / profile、MMD WAV / individual save、worker / lifecycle / textlessの各groupを別commandとして記録する。
- pytest collection数が想定より少ない、または対象ファイルが収集されない場合は合格扱いにしない。
- MS20〜MS24の不変条件がMS25 delivery追加後も維持されることをledgerへ対応付ける。

### Step 7: full suite / static gate

1. 全pytest
2. `compileall -q src tests`
3. 文書同期前の`git diff --check`

full pytestはtargeted regressionを代替せず、targeted regressionもfull pytestを代替しない。

### Step 8: manual evidence audit

- B5 / B6のユーザー報告を、実施Block、対象、実施者、結果、current HEADまでのintervening code changeへ対応付ける。
- B6後にGUI / delivery behavior変更がなければ、B7はdocs-onlyのためfresh manual GUIを必須としない。
- GUI / worker repairが入った場合、影響範囲のfresh manual GUI項目を提示し、結果受領前にmanual verifiedと記録しない。
- CodexがGUIを実行していない場合、ユーザー報告をCodex実行結果と記載しない。

### Step 9: finding判定

- §13の基準でP1 / P2 / P3へ分類する。
- P1またはP2がある場合はCloseout Aを停止し、再現証拠、影響、repair owner、再検証commandを記録する。
- P3は文書scope内で安全に解消できるcurrent-state / wording / heading不一致ならB7文書同期で修正する。code / test変更が必要なら別repairへ分離する。
- findingを「候補」「確定」「解消」「ユーザー判断で受容」に分け、未解消を暗黙に消さない。

### Step 10: 利用者文書同期

自動gate合格後、README / readmeを次へ照合する。

- `ファイル > MMD一括出力...`
- parent directoryとeditable folder名
- 既定`<audio_stem>_MMD`
- 固定3成果物名と役割
- current stateからの再生成と個別保存済み成果物の非流用
- stagingで全件生成・検証後だけ確定
- 同名entryの種類・空否を問わないcollision、別名要求、merge / replace / overwrite / automatic rename禁止
- failure / cancel時の既存出力保護
- individual VMD / MMD WAV / report保存との共存
- reportにpreset / profile / morph set / Whisper identityを記録すること
- 実MMDでの読み込み・再生・リップ同期は別確認であること

内部staging path、private error、raw exceptionは利用者文書へ記載しない。

### Step 11: 正文仕様同期

- Pipeline: start context、3 input role、same snapshot、source identity、commit fingerprint、terminal result、session-only pathを明記する。
- GUI State: start gate、WARNING / ERROR、dialog、Busy、cancel、close reconciliation、terminal、retry、individual actionsを明記する。
- Error Handling: collision優先、OS fault分類、artifact phase、commit / cleanup、safe message、actual code setを一致させる。
- VMD Output: current effective plan、resolved morph names、production read-backのheader / model / frame / tail / EOF検証、staging transactionを明記する。
- 仕様追加は現行codeで実装・test済みの事実に限定する。B7で新しいruntime requirementを発明しない。

### Step 12: routing / Closeout同期

- Index、Roadmap、Block Breakdown、B6 planのB6 commit状態を`5300905`または実行時HEADへ同期する。
- B7 planへ実測結果、finding ledger、manual evidence、未検証、Closeout判定を追記する。
- `repo_milestone.md` / `Version_Control.md`へ必要最小限の履歴を追加する。
- MS26実MMDとMS27package / release readinessを未検証のまま保持する。

### Step 13: final audit

1. 変更ファイルがB7文書scopeだけであることを確認する。
2. README / readme /正文仕様 / routing / B7実績の成果物名、test値、HEAD、日付、manual主体、deferred範囲を相互照合する。
3. `git diff --check`を再実行する。
4. 未追跡のB7文書が残る場合は、stageせず各ファイルに対して`git diff --no-index --check -- NUL <path>`を実行する。`--no-index`は空デバイスとの差分のためexit code `1`が正常であり、whitespace診断出力がないことを合格条件とする。複数の未追跡文書は個別に確認する。
5. `git status --short --branch`を記録する。
6. stage / commitはユーザーの別途明示承認まで行わない。

## 10. 状態遷移 / データ契約

### 10.1 B7作業状態

```text
Baseline identified
  -> Scope audit
     -> scope finding: record and stop closeout
  -> B6 actual fault gate
     -> fail / required skip: record and stop closeout
  -> MS25 aggregate
     -> fail: record and stop closeout
  -> Cross-boundary groups
     -> fail / insufficient coverage: record and stop closeout
  -> Full pytest + compileall
     -> fail: record and stop closeout
  -> Manual evidence audit
  -> Finding classification
     -> open P1 / P2: separate repair, no closeout A
  -> User docs + canonical specs + routing sync
  -> Final diff audit
  -> MS25 Closeout decision
```

### 10.2 runtime state非変更

B7の検証・文書同期は、アプリのruntime state、output files、individual save history、session-only delivery parent、INI、preset / profile storeを変更しない。pytestはtemporary path、fixture、injected storeを使う既存testに限定する。

### 10.3 evidence identity

一つの検証結果は次のtupleとして扱う。

```text
(date/time, branch, exact HEAD, command, collected count,
 passed, failed, skipped, skip reason, process exit code, notes)
```

HEADが変わった場合、旧tupleは履歴になり、新HEADの合格証拠にはならない。docs-only変更だけの場合はcode test結果を維持できるが、文書差分については最終`git diff --check`と相互整合監査を別途行う。

### 10.4 Closeout状態

| 判定 | 条件 |
| --- | --- |
| Closeout A | required gateがすべてprocess exit code `0`、required Windows caseがskipなし、open P1 / P2 / P3なし、文書同期完了、deferred範囲明記 |
| 条件付き | 実装契約を壊さない環境依存またはP3が残り、影響・owner・ユーザー判断が明示されている。Aとは記載しない |
| 不合格 / repair required | P1 / P2、required test failure、required Windows skip、scope逸脱、証拠不足のいずれかがある |

MS26 / MS27へ意図的にdeferした項目は、MS25のfindingではなく`deferred-by-design`として別欄へ記録する。

## 11. テスト方針

### 11.1 実行順

各commandは一つずつ実行し、完了とexit codeを確認してから次へ進む。以下のパスは一つのpytest commandへ列挙してよいが、shell pipelineやcommand連結は使用しない。

1. B6 actual fault / recovery gate
2. MS25-B1〜B6 aggregate
3. diagnostics / report / fingerprint cross-boundary
4. VMD / effective output / preset / profile cross-boundary
5. MMD WAV / individual save cross-boundary
6. worker / GUI lifecycle / textless / Whisper identity cross-boundary
7. full pytest
8. `compileall -q src tests`
9. 文書同期後の`git diff --check`

### 11.2 B6 required gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b6_windows_collision_faults.py tests/test_ms25_b6_delivery_failure_recovery.py tests/test_ms25_b6_delivery_gui_recovery.py
```

合格には、pytest全体exit code `0`に加え、actual junction / reparse collisionとpermission deniedまたはsharing violationの該当testがskipなしでpassした証拠が必要である。

### 11.3 MS25 aggregate

§7.6の13ファイルをすべて明示して実行する。個別fileの省略、`-k`による一部選択、既存skipの追加は禁止する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py tests/test_ms25_b2_windows_paths.py tests/test_ms25_b2_delivery_orchestration.py tests/test_ms25_b2_delivery_commit.py tests/test_ms25_b3_delivery_artifacts.py tests/test_ms25_b3_vmd_readback_validation.py tests/test_ms25_b4_delivery_report_identity.py tests/test_ms25_b5_delivery_worker.py tests/test_ms25_b5_delivery_gui.py tests/test_ms25_b6_windows_collision_faults.py tests/test_ms25_b6_delivery_failure_recovery.py tests/test_ms25_b6_delivery_gui_recovery.py
```

### 11.4 cross-boundary groups

§7.7の各groupを別々に実行し、次を証明する。

- diagnostics / report / fingerprint: WARNING gate、standalone report、identity、fingerprint非汚染
- VMD / effective output / preset / profile: current effective output、Japanese / Latin、long-vowel、history、writer binary contract
- MMD WAV / individual save: original input、WAV仕様、failure cleanup、個別dialog / overwrite、VMD個別保存
- worker / lifecycle / textless / Whisper: terminal one-shot、late result、rollback、voice-only、workspace reset、no implicit download、runtime identity

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_ms20_b6_diagnostic_report.py tests/test_ms20_b6_report_save_flow.py tests/test_ms20_b7_diagnostics_state_integration.py tests/test_ms21_b5_effective_output_identity.py tests/test_ms24_whisper_diagnostics.py tests/test_ms24_whisper_error_recovery.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py tests/test_vmd_writer_intervals.py tests/test_vmd_writer_grouping.py tests/test_vmd_writer_multipoint_shape.py tests/test_vmd_writer_peak_value.py tests/test_vmd_writer_zero_guard.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms22_b2_long_vowel_adapters.py tests/test_ms22_b3_generation_presets.py tests/test_ms22_b4_generation_history.py tests/test_ms22_b6_lifecycle_regression.py tests/test_ms23_b2_morph_name_sets.py tests/test_ms23_b2_morph_name_adapters.py tests/test_ms23_b4_model_profile_state.py tests/test_ms23_b5_model_profile_controller.py tests/test_ms23_b6_model_profile_lifecycle.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py tests/test_ms17_b7_mmd_wav_button_state.py tests/test_wx_ms14_b5_export.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms21_b7_audio_worker_terminal.py tests/test_ms21_b7_analysis_rollback.py tests/test_ms19_b3_textless_pipeline.py tests/test_ms19_b4_analysis_worker_voice_only.py tests/test_ms19_b5_transcription_edit_state.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py tests/test_ms24_no_implicit_download.py tests/test_ms24_whisper_model_runtime.py
```

### 11.5 full suite / static

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
```

```powershell
git diff --check
```

未追跡のB7文書がある場合は、stageせずにファイルごとに次を実行する。

```powershell
git diff --no-index --check -- NUL docs\Implementation_Plan\MS25-B7_Implementation_Plan.md
```

`--no-index`は`NUL`との比較になるため、対象ファイルに問題がなくてもexit code `1`になる。標準出力にwhitespace診断がないことを合格条件とし、診断が出た場合は不合格とする。未追跡文書が複数ある場合は各ファイルを個別に確認する。明示的なユーザー承認によりstage済みとなった後は`git diff --cached --check`も利用できるが、stage自体はB7実行手順に含めない。

full pytestのskipは全件についてtest名と理由を確認する。B6時点の4 skippedと件数が同じでも、同じ理由とは仮定しない。

### 11.6 failure時の扱い

- 初回failureを自動でflaky扱いにしない。
- 同じcommandを無変更で再実行する場合は、初回failureと再実行結果の両方を記録する。
- test isolationやOS timingが疑われても、原因証拠なしにCloseout Aへ進まない。
- test修正が必要ならP2以上として別repairへ分離する。
- process exit code非0は、pass表示が含まれていてもgate不合格である。

## 12. 受け入れ条件

### 12.1 baseline / evidence

- [x] branch、exact HEAD、working tree、MS25分岐元を記録した。
- [x] B1〜B6のcommit、requirement、source、test、documentをledgerへ対応付けた。
- [x] B6時点の履歴値とB7実測値を区別した。
- [x] MS25差分にruntime data、dependency、build、package、licenseの意図しない変更がない。

### 12.2 output / transaction contract

- [x] final成功directoryに固定3成果物がちょうど一つずつ存在する契約が回帰していない。
- [x] VMD、MMD WAV、reportがそれぞれcurrent effective state、original input audio、same diagnostics snapshotから再生成される。
- [x] 個別保存済み成果物を流用せず、individual save flowとhistoryを変更しない。
- [x] existing destinationを種類・空否を問わず変更せず、merge / replace / delete / automatic renameを行わない。
- [x] pre-commit failure / cancelでpartial finalを公開せず、owned stagingだけをcleanupする。
- [x] commit / cancel線形化、source identity、staging identity、cleanup failure terminalが一貫している。

### 12.3 state / diagnostics / identity

- [x] start contextとcommit直前current fingerprintが同じsemantic contractを使う。
- [x] `projection_generation`がfilesystem commit identityへ混入していない。
- [x] `ms21-effective-output-v1` schema / payloadが変更されていない。
- [x] preset、profile、resolved morph names、Whisper selected / active / loaded / analysis identityがreportへ省略なく記録される。
- [x] Whisper management表示がfingerprintを変えず、暗黙download、cloud ASR、音声外部送信、background通信が追加されていない。
- [x] Busy、cancel、close、late / duplicate terminal、retry可能状態が回帰していない。

### 12.4 automated gates

- [x] B6専用3ファイルがprocess exit code `0`で、required actual Windows caseがskipなしでpassした。
- [x] MS25-B1〜B6 aggregateがprocess exit code `0`である。
- [x] §7.7の全cross-boundary groupがprocess exit code `0`である。
- [x] full pytestがprocess exit code `0`である。
- [x] `compileall -q src tests`がprocess exit code `0`である。
- [x] 最終のtracked差分に対する`git diff --check`がprocess exit code `0`である。
- [x] 未追跡文書がある場合も、各ファイルを`git diff --no-index --check -- NUL <path>`で確認し、exit code `1`を正常差分として扱い、whitespace診断出力がないことを確認した。
- [x] skip数、対象、理由、受入影響を記録した。

### 12.5 documentation / manual / closeout

- [x] README / readmeの利用手順、成果物、保護動作、個別保存、実MMD留保が現行挙動と一致する。
- [x] Pipeline / GUI State / Error Handling / VMD Output正文仕様がB1〜B6契約と一致する。
- [x] Index、Roadmap、Block Breakdown、B6 planがB6 commit済みとB7結果を示す。
- [x] manual GUI結果は実施者、対象、日付、current HEADとの関係を限定して記録した。
- [x] open P1 / P2 / P3がなく、Closeout A判定と次工程が明記されている。
- [x] 実MMDをMS26、Python 3.11 / 3.12を未検証、PyInstaller onefile / ZIP / package / release readinessをMS27へ維持した。
- [x] stage / commit / push / merge / tag / releaseを別途明示承認なしに実施していない。

## 13. P1 / P2 / P3判定基準と証拠

### 13.1 判定基準

| 分類 | MS25-B7での基準 | 例 |
| --- | --- | --- |
| P1 | 既存出力破壊、partial final公開、不正成果物commit、commit済みfinal削除、暗黙通信等、利用者データやprivacyを直ちに損なう | collision先のreplace、cleanupが既存treeを辿る、VMD validation failure後のcommit、音声外部送信 |
| P2 | 次工程前に解消すべきcontract / regression / evidence gap。Closeout Aを止める | required test failure / skip、same snapshot不一致、Whisper identity混同、individual save回帰、正文仕様の挙動不一致、test coverage不足 |
| P3 | runtime契約を変えない記録・表現・routingの軽微な不一致 | B6未commit表記、見出し番号重複、historical / current test値の混同、用語揺れ |

### 13.2 findingに必要な証拠

各findingは次を含む。

- ID: `MS25-B7-F-001`形式
- 分類: P1 / P2 / P3
- 状態: candidate / confirmed / resolved / accepted / deferred-by-design
- requirementと期待値
- 反証または不足を示すfile / line、test名、command、exit code
- 利用者影響と既存出力への影響
- root causeが確認済みか、推論か、不明か
- repair ownerと許可が必要な変更範囲
- 解消条件と再実行するgate
- 解消commitまたは文書差分

「疑わしい」だけでP1へ上げず、再現またはcode pathの直接証拠を示す。一方、evidence不足をpassと推定しない。

### 13.3 計画策定時の候補

| ID | 候補分類 | 内容 | B7での処理 |
| --- | --- | --- | --- |
| MS25-B7-PRE-001 | resolved | B6 commit済みのlive Gitと、未commitとするcurrent-state文書の不一致 | `5300905`へcurrent-state欄を同期済み。履歴文は保持 |
| MS25-B7-PRE-002 | resolved | GUI State仕様の`8.4`見出し番号重複 | MS25節を`8.6`へ補正し、本文意味と参照先を維持 |
| MS25-B7-PRE-003 | resolved-by-contract | Error仕様の`output_path_too_long`と現行coreの`output_path_invalid`正規化の差 | Error仕様へ現行core codeと既存UI互換aliasの関係を注記し、B7はcode変更を行わない |
| MS25-B7-PRE-004 | resolved | Block BreakdownのB7 `§11.4`回帰ゲートがB7実測前に`[x]`だった | `[ ]`へ戻し、B6履歴baselineとB7同一HEAD実測を分離 |
| MS25-B7-PRE-005 | resolved | IndexのB7計画書routingとcurrent phaseの作成状態が未同期 | `MS25-B7 Implementation Plan Created`と計画書リンクを追加し、B6 routing名を補正 |
| MS25-B7-PRE-006 | resolved | `git diff --check`だけでは未追跡のB7計画書を検査できない | `git diff --no-index --check -- NUL <path>`によるstage不要の個別確認と、exit code `1` / 空出力の判定を§11.5 / Step 13へ追加 |
| MS25-B7-PRE-007 | resolved | Block BreakdownがB7内のcross-boundary test追加を許容するように読め、B7計画のtest code変更禁止と責務が不一致 | 既存回帰の実行に限定し、coverage不足はfinding化して別repairへ分離する記述へ補正 |
| MS25-B7-PRE-008 | resolved | Block Breakdownのfull pytestが「必要に応じて」となっており、B7計画の必須automated gateと不一致 | Block Breakdown §11.4を`全pytest（必須）`へ補正 |
| MS25-B7-PRE-009 | resolved | Block Breakdownのstatic gateに未追跡文書のwhitespace検査が明記されていない | tracked差分の`git diff --check`と未追跡文書ごとの`git diff --no-index --check -- NUL <path>`を記載し、exit code `1` / 空出力の判定を固定 |

上記は計画策定時に抽出した候補と、その後のメイン側補正結果である。B7実施時には、これらの解消状態を実行HEADと最終文書差分で再確認する。候補の存在だけでB6実装を未完了とは判定しない。

再チェックで確認した未追跡文書のwhitespace gate不足はMS25-B7-PRE-006として解消した。B7実装前チェックで確認したcross-boundary test追加の責務不一致はMS25-B7-PRE-007として解消した。B7計画再検証で確認したfull pytest必須性の不一致はMS25-B7-PRE-008、上位文書の未追跡文書gate記載不足はMS25-B7-PRE-009として解消した。メイン側の修正後時点で、計画策定に関するopen P1 / P2 / P3はない。B7実施中に新しいfindingが発生した場合は、既定の分類・停止・別repair分離手順へ従う。

## 14. リスクと対策

| ID | リスク | 重要度候補 | 対策 |
| --- | --- | --- | --- |
| MS25-B7-R1 | B6履歴testをB7実測として再利用する | P2 | exact HEADで全required gateを独立再実行する |
| MS25-B7-R2 | full pytestだけでcross-boundary intentを証明したことにする | P2 | §7.7 groupとfull suiteを別gateにする |
| MS25-B7-R3 | Windows required caseがskipされてもinjection testで代用する | P2 | actual caseのskipなしpassを必須にする |
| MS25-B7-R4 | failing testをB7内のtest変更で通す | P1 / P2 | code / test変更を禁止し、別repairとfresh rerunへ分離する |
| MS25-B7-R5 | docsを先に完了表記し、後でtest failureが出る | P2 | automated gate後だけCloseout文書同期を行う |
| MS25-B7-R6 | READMEへ内部用語を並べ、利用者がcollision / recoveryを誤解する | P3 | 操作、成果物、保護、次行動を中心に記載する |
| MS25-B7-R7 | report identity追加がfingerprintへ入ったと誤認する | P2 | B1 / MS20 / MS21 / MS24 fingerprint testを横断実行する |
| MS25-B7-R8 | individual saveとbatchの履歴・audio roleを混同する | P2 | standalone report / WAV / VMD flowを明示回帰する |
| MS25-B7-R9 | manual GUI報告をCodex自身の実行と記録する | P3 | 実施者と対象を限定し、未実施は未実施と書く |
| MS25-B7-R10 | 実MMD、Python 3.11 / 3.12、onefileをMS25検証済みと誤記する | P2 / P3 | deferred / unverified ledgerを独立させる |
| MS25-B7-R11 | runtime dataをcloseout資料として直接読み、stageへ混入する | P2 | Git inventoryだけを使い、root三点を直接開かない |
| MS25-B7-R12 | docs-only変更後にcode testを再実行し、結果を混乱させる | P3 | code HEADとdocs diffを分け、docs-onlyなら最終diff / consistency gateを記録する |

## 15. 手動GUI・実MMD・MS27の境界

### 15.1 manual GUI

B7はruntime behaviorを変更しないため、次を満たせばfresh manual GUIは原則不要とする。

- B5 / B6のユーザー報告が確認できる。
- B6 commit後にGUI / worker / delivery coreの追加変更がない。
- B7の変更が文書だけである。
- B5 / B6 manual対象を自動testと現行call pathへ対応付けられる。

既存manual evidenceとして、少なくとも次を記録する。

- 成功時の3成果物出力
- 同名destinationで別名要求となり既存entryを変更しない
- cancel後にBusyが解除され再試行できる
- close時にterminal / cleanupを待つ
- success / failure / cancel後も個別VMD / MMD WAV / report導線が利用できる

coverage不足またはGUI repairが入った場合だけ限定再確認を依頼する。fault injection、TOCTOU、commit瞬間、cleanup exceptionはmanual偶然再現ではなく自動testを正本とする。

### 15.2 MS26

次はMS25 Closeoutの不合格理由にせず、MS26の必須確認として引き継ぐ。

- 実MMDでのVMD読込
- MMD用WAV読込・再生
- VMDとWAVのリップ同期
- Japanese / Latin morph setと対象モデルの実動作
- delivery directoryの3成果物を使ったMMD持ち込み手順

### 15.3 MS27

次はMS27へ引き継ぐ。

- PyInstaller onefile build
- SmokeLaunch
- ZIP生成とZIP内容
- 最終artifactのdependency / binary / runtime data混入確認
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、Release Package Manifestのrelease readiness
- Ver.1.0 version / release candidate判定
- push、tag、release公開の別承認

## 16. B7実施結果と未検証事項

### 16.1 実行結果

実行環境はWindows `win32`、Python `3.14.3`、pytest `9.0.3`、検証HEADは`0b25c5c`である。各commandは一つずつ実行し、表示結果とprocess exit codeを確認した。

| Gate | 実行command / 対象 | 結果 |
| --- | --- | --- |
| B6 required fault / recovery | §11.2の3ファイル明示command | `26 passed`、exit code `0`。required actual Windows caseのskipなし |
| MS25 aggregate | §11.3の13ファイル明示command | `160 passed, 2 skipped`、exit code `0` |
| diagnostics / report / fingerprint | §11.4 第1group | `60 passed`、exit code `0` |
| VMD / effective output / preset / profile | §11.4 第2group | `200 passed`、exit code `0` |
| MMD WAV / individual save | §11.4 第3group | `21 passed`、exit code `0` |
| worker / lifecycle / textless / Whisper | §11.4 第4group | `41 passed`、exit code `0` |
| full pytest | `.\.venv\Scripts\python.exe -m pytest tests` | `1041 passed, 4 skipped`、exit code `0` |
| compileall | `.\.venv\Scripts\python.exe -m compileall -q src tests` | exit code `0` |

MS25 aggregateの2 skipは、`tests/test_ms25_b2_windows_paths.py`のsymlink作成ケースで、Windows `WinError 1314`（symlink作成権限なし）による環境依存skipである。full pytestの追加2 skipは、`tests/test_whisper_model_store.py`のsymlink作成ケースで同じ理由である。全skip確認用の`-rs`再実行でも、対象47件は`47 passed, 4 skipped`、exit code `0`だった。B6 required fault gateにこのskipはなく、junction / reparse collisionとsharing violationはskipなしで通過した。

### 16.2 scope / 文書同期

- B7実施中のproduction code、test code、GUI、dependency、build設定、license、runtime user dataの変更はない。
- `README.md`、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD Output正文仕様は現行コードと照合し、必要事項が反映済みのため変更しなかった。
- `MS25-B7_Implementation_Plan.md`、`MS25_Block_Breakdown.md`、`MS20_and_Beyond_Index.md`、`MS20_and_Beyond_Roadmap.md`、`docs/repo_milestone.md`、`docs/Version_Control.md`へ、B7実測値、skip理由、手動証拠、Closeout判定、未検証境界を同期した。
- B7で変更した文書のworking tree差分に対する`git diff --check`はexit code `0`である。B7計画書はこの実施記録により追跡対象となるため、未追跡文書向け`--no-index`検査の未stage条件は該当しない。

### 16.3 manual evidence / finding / Closeout

- B5 / B6の手動GUI確認は、ユーザーから受領した「通過・問題なし」の報告を、実施者をユーザーに限定して再利用した。B6 commit後のproduction code / GUI変更はなく、B7は文書同期のみのためfresh manual GUIは不要と判定した。Codex自身のGUI実行結果とは扱わない。
- 計画策定時の`MS25-B7-PRE-001`〜`PRE-009`はすべてresolvedまたはresolved-by-contractであり、B7実施で新たなP1 / P2 / P3は確認されなかった。
- required gate、文書同期、手動証拠の範囲限定、deferred境界を確認したため、MS25 Closeoutは`A`と判定する。

### 16.4 未検証・deferred

- Python 3.11 / 3.12 compatibility
- 実MMDでのVMD / WAV読込・再生・リップ同期、Japanese / Latin morph setの実動作
- PyInstaller onefile、SmokeLaunch、ZIP、最終artifact、package / release readiness
- push、tag、release公開

B6時点の`1041 passed, 4 skipped`は履歴baselineとして保持し、B7実測値と混同しない。B7実測のfull pytestも同じ件数だが、検証HEAD、skip理由、実行時点が異なるため、B7の独立evidenceとして記録する。

## 17. 完了報告形式

B7完了報告は次の順で行う。

1. 確認したファイル
2. 変更したファイル
3. B1〜B6 requirement-to-evidence ledgerの要約
4. 実行したcommand、pass / fail / skip、skip理由、process exit code
5. Windows actual fault gate結果
6. ユーザー手動GUI証拠とCodex自身の実施有無
7. P1 / P2 / P3 finding ledgerと解消状態
8. 仕様からの逸脱
9. 未検証・deferred
10. MS25 Closeout判定
11. MS26 / MS27への引き継ぎ
12. Git status、stage / commit / push / merge / tag / release実施有無

## 18. Codex実施時の注意

- コマンドは一つずつ実行し、shell pipelineや連結を使用しない。
- B7は新機能実装またはrepairではない。code / testの変更が必要なら停止して別作業へ分離する。
- user-owned差分をrestore、上書き、stageしない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読まない、変更しない、stageしない。
- testを削除・弱化・skip追加してfailureを回避しない。
- required Windows caseを過去passやmockで代用しない。
- pass表示とprocess exit codeを別々に確認する。
- 文書にtest結果を書くときはexact HEADとB6履歴 / B7実測を区別する。
- current-state欄だけを更新し、過去計画時点の事実を後知恵で書き換えない。
- README / readmeは日本語利用者向け説明、正文仕様はcode contract、routingは現在地という役割を維持する。
- actual MMDをMS26、package / release readinessをMS27から前倒ししない。
- stage、commit、push、merge、tag、releaseはそれぞれ別の明示承認を必要とする。

## 19. 計画策定時自己監査

### 19.1 要求対応

- full cross-boundary regression、MS25全体Closeout準備、README / readme同期、正文仕様同期を明示した。
- B1〜B6のstate、output、error、GUI、Whisper identity、individual save invariantをevidenceへ対応付けた。
- test順、acceptance、manual GUI、実MMD、MS27、未検証を分離した。
- P1 / P2 / P3の判定基準、必要証拠、report形式を定義した。
- code / test実装をB7のOut of Scopeとし、必要時は別repairへ戻す条件を固定した。

### 19.2 反証確認

- README / readmeは既にMS25説明を含むため、「未同期」と決めつけず、現行挙動との最終照合をB7責務とした。
- B6 plan / routingの未commit表記はlive HEADと矛盾していたため、`5300905`へのcurrent-state同期で解消した。過去時点の履歴記述は残した。
- GUI State仕様の見出し番号重複はMS25節を`8.6`へ補正して解消した。
- Error仕様の`output_path_too_long`は、現行coreがpath長超過を`output_path_invalid`へ正規化する一方、既存UI互換aliasとして残る関係を注記し、runtime codeの変更を要する不一致ではないと判定した。
- Block BreakdownのB7 `§11.4`受け入れチェックがB7実測前に完了扱いだったため、B6履歴baselineとB7実測を分離する`[ ]`へ補正した。
- IndexにB7計画書のroutingがなかったため、current phaseへ作成済みを追加し、routing tableへ計画書リンクを追加した。B6の「実装前計画」表記も実装計画へ補正した。
- 未追跡のB7計画書が通常の`git diff --check`では検査されない点をP3として確認し、stage不要の`git diff --no-index --check -- NUL <path>`個別確認とexit code `1` / 空出力の判定を追加した。
- Block Breakdownの「B7で追加が必要と判定したcross-boundary回帰を補足する」とB7計画のtest code変更禁止の差をP2として確認し、既存回帰の実行、coverage不足のfinding化、別repair分離へ統一した。
- Block Breakdownの「必要に応じて全pytest」とB7計画のfull pytest必須gateの差をP2として確認し、全pytestを必須へ統一した。
- Block Breakdownのstatic gateに未追跡文書のwhitespace検査がなかったためP3として確認し、tracked / untrackedの検査手順と判定規則を統一した。
- B6のfull pytest成功はB7 full cross-boundary gateの代替にならないと明記した。
- full pytest成功もtargeted cross-boundary evidenceの代替にならないと明記した。
- actual MMDとpackage確認をCloseout証拠へ混入させず、MS26 / MS27へ維持した。

### 19.3 判断事項

計画作成を止める未解決のユーザー判断事項はない。B7は既存testを実行し、文書だけを同期する。production / test repairが必要なfindingが出た場合は、その時点でB7 Closeoutを停止し、修正範囲と再検証条件を提示してユーザー判断を求める。
