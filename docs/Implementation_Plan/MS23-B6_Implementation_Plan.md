# MS23-B6 Cross Regression / Documentation Implementation Plan

## 1. 文書情報

- 文書名: MS23-B6 Cross Regression / Documentation Implementation Plan
- 作成日: 2026-08-19
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時branch: `feature/MS23-implementation`
- 計画作成時HEAD: `4947dfe Implement MS23-B5 model profile UI`
- 直接依存: MS23-B1 Completed / Contract Fixed、MS23-B2〜B4 Implemented、MS23-B4B Implemented / Automated Verification Passed、MS23-B5 Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report)
- 実装着手時点HEAD: `229ad3d Document MS23-B6 implementation plan`
- 文書ステータス: Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) / Actual-MMD Verification Deferred
- 次工程: MS23-B7 Closeout Audit
- Actual-MMD Verification: MS26へdeferred

本plan作成時は本ファイルだけを変更した。実装では、B6専用test、既存ownerの最小repair、利用者文書・正本仕様・routing文書を変更した。
`profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`はroot runtime user dataであり、内容の読み取り、fixture化、stageを行っていない。

## 2. 背景

MS23-B1〜B5では、次の責務を分割して実装した。

- B1: profile / preset / application defaultの優先順位、failure matrix、runtime baseline、mutation guard、fingerprint境界を契約固定した。
- B2: semantic vowel `あ / い / う / え / お`を維持したまま、最終normalization後に日本語または英字のresolved output nameへ一度だけmappingする境界を実装した。
- B3: strict versioned `profiles.json`、最大100件、atomic CRUD、fail-closed load、INIのactive profile identityを実装した。
- B4: profile-aware resolution、state、history、startup、rollback、diagnostics / report / fingerprint、cross-store mutation guardを接続した。
- B4B: wx test teardownとfull pytestのprocess exit安定性を補修した。
- B5: RightPaneのprofile Select / Apply / CRUD、preset panelとのcross-sync、Busy / stale guardを実装した。

現行HEAD `4947dfe`では、B5のUIに加えて次の回帰補修が入っている。

- Delete確認結果を`wx.ID_YES`と比較する。
- Delete成功後に`wx.Choice`の候補一覧と選択状態をcanonical collectionから再投影する。
- 連続する同一母音のlong-vowel runで、前run終端zeroと次run peakが同一frameへ衝突しないよう境界を補正する。
- `long_vowel_mode=hold / decay`の双方でPreview shapeを構築できることを回帰テストへ固定する。

B5実装記録では、関連31件、full suite 785件＋57 subtests、`compileall src tests`、`git diff --check`がpass表示・process exit code 0である。ユーザーによるB5手動GUI確認も通過・問題なしと記録されている。この記録はB5完了時の証拠であり、B6検証では置き換えず再確認した。

B6では、利用者文書と正本仕様をMS23到達状態へ同期し、`UiState`のRedo profile state再投影欠落をB6専用testで再現したため、既存ownerへ最小repairを追加した。profile Apply後のUndo / Redoは自動検証済みだが、production codeを変更したため限定手動GUI確認を残している。

また、live repositoryでは次を確認した。

- `.gitignore`はroot限定で`/profiles.json`、`/presets.json`、`/MMD_AutoLipTool.ini`をignoreする。
- 3ファイルはGit追跡対象ではない。
- `MMD_AutoLipTool.spec`、`build.ps1`、`docs/Release_Package_Manifest.md`は`profiles.json`をbundled default dataとして扱っていない。
- MS23分岐元`4e85682`から現行HEADまで、`pyproject.toml`、spec、build、LICENSE、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestに差分はない。
- `src/`にはPySide / PyQt、HTTP client、socketを導入した現行コードは確認されない。

## 3. 目的

1. MS23-B1〜B5の成果を新機能追加なしで横断し、writer、Preview、diagnostics、diagnostic report、save-state fingerprintが同じresolved morph-name contractを使用することを固定する。
2. profileなし日本語、Japanese profile、Latin profile、profile解除、preset単独、TEXTあり、voice-only、empty、failure、cancel、rollback、reset、startup、stale worker、Undo / Redoを代表matrixで検証する。
3. profile CRUDとpreset CRUDの相互作用、参照中preset guard、active profile / active runtime baseline guard、missing preset、broken `profiles.json`のfail-closed動作を検証する。
4. B5で補修したDelete後Choice再投影、`wx.ID_YES`確認、連続同一母音long-vowel Preview回帰を維持する。
5. 既存日本語5母音、`A / I / U / E / O`、VMD 30fps、TEXTあり／voice-only、WAV / MP3 / M4Aと既存音声三役の後方互換性を確認する。
6. README、配布用readme、Pipeline / VMD / GUI / Error仕様を、B6で実際に検証できた到達状態へ同期する。
7. runtime user data、package非同梱、dependency、license、network、Qt凍結の境界を静的に監査する。
8. B6完了証拠をB7 Closeout Auditが再利用できる形で記録する。MS23 Closeout判定そのものは行わない。

## 4. In Scope

- MS23 direct cross-regression testの追加または既存testの限定補強
- resolved output-name tupleのwriter / Preview / diagnostics / report / fingerprint一致
- no-profile Japanese default、Japanese profile、Latin profile、no-profile復帰
- profile Apply直後のdefault baseline、active profile中の別preset Apply、preset単独Custom reconciliation
- TEXTありとvoice-onlyの解析成功・VMD保存経路
- empty / clear / invalid effective outputでのPreview label、diagnostics、fingerprint可否
- analysis failure / cancelのrollback可否とprofile-aware state保持
- workspace reset、startup、restart相当、stale analysis / audio callback、Undo / Redo
- profile Create / Update / Rename / Deleteとpreset Create / Update / Rename / Deleteのguard matrix
- missing profile、missing default preset、missing runtime baseline、broken / unsupported `profiles.json`のfail-closed
- commit前failureの完全不変と、commit後INI save failureでcommitted in-memory state / historyをrollbackしない契約
- B5のDelete確認、Choice一覧再投影、連続同一母音long-vowel hold / decay回帰
- `UiState`単体およびMainFrame履歴操作経路のUndo / Redo profile state再投影を、B6専用testで固定し、現行ownerの不一致が再現した場合は`src/gui_wx/ui_state.py`を最小repairする
- README、`readme_mmdautolip.txt`、Pipeline / VMD / GUI / Error仕様のimplemented同期
- Index / Roadmap / Block Breakdown / 本planのB6 status同期。ただし自動検証と必要なGUI確認の条件を満たした後に限る
- root ignore / non-tracked / non-stageとpackage非同梱のread-only確認
- B6で確認された契約違反に対する、既存owner内の最小repair。新仕様、schema変更、UI再設計は含めない

## 5. Out of Scope

- 新しいprofile field、preset field、JSON schema version、上限、ID形式の追加・変更
- built-in以外のmorph-name set、任意morph mapping、ユーザー定義set、追加表情
- PMX / PMD読込、model file解析、model名自動取得
- 英語音声認識、英語音素処理、MS24 Whisper Model Selection
- MS25 MMD Delivery Package Export、一括出力用DTO / adapter
- 実MMDでのVMD / WAV読込・再生・リップ同期確認。MS26の責務として残す
- PyInstaller build、SmokeLaunch、ZIP、installer、version bump、release readiness、MS27 packaging / release
- dependency追加・更新、license変更、FFmpeg配布方針変更
- network処理、cloud処理、telemetry、background通信
- Qt / PySide6の復活、wxPython以外へのGUI移行
- VMD format、30fps、音声入力形式、MMD用WAV契約の変更
- branch作成・切替・削除、stage、commit、push、merge、tag、release公開
- runtime `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`の内容確認、削除、初期化、stage
- MS23 Closeout A / B / C判定。これはB7 Closeout Auditで行う

## 6. 前提条件

### 6.1 実装開始gate

- branchが`feature/MS23-implementation`であることを確認する。
- B6着手時のHEADを記録し、計画作成時HEAD `4947dfe`との差分を確認する。
- worktreeの既存変更を確認し、ユーザー所有変更を上書きしない。
- 本plan、Block BreakdownのB6 / B7、Index、Roadmap、B5 planと現行code / testsを再読する。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`は内容を読まず、`git check-ignore -v`と`git ls-files --`によるpath-level境界だけを確認する。
- B6専用testは`tests/test_ms23_b6_model_profile_lifecycle.py`の1ファイルへ固定する。non-wx / wxを同一file内のテスト群として分離し、temporary storeとB4B teardown helperを共有する。別fileへの分割は、実装中にteardown責務または実行安定性の問題が実測された場合に限り、別途理由を記録して行う。
- 現行`UiState.redo_output_edit_state()`のprofile state再投影は、B6専用testの最初の必須確認とする。不一致が再現した場合は`src/gui_wx/ui_state.py`の既存ownerへ限定repairし、再現test・B6 direct regression・関連回帰を再実行する。補完経路が確認できた場合だけproduction codeを変更しない。
- 実装開始時点でP1 / P2 / P3があれば、分類と解消方針を先に記録する。materialな仕様判断はB6へ暗黙追加しない。

### 6.2 固定済み互換契約

- semantic vowelは`あ / い / う / え / お`のまま保持する。
- built-in output-name setは日本語`あ / い / う / え / お`と英字`A / I / U / E / O`の2種だけである。
- profileなしはJapanese setを使用する。
- 優先順位は`event adjustment > model profile > preset > application default`である。
- `morph_upper_limit`差分はanalysis invalidationとbase-bound history clearを行う。
- hold / softness / long-vowel mode / morph-name setはoutput-onlyで、upper差分がなければbase planを再利用する。
- active profile中は`active_preset_id=None`、runtime baselineは`active_profile_baseline_preset_id`で表す。
- profile identity / display nameだけの変更はeffective writer outputとfingerprintを変えない。
- mapped frame nameが日本語から英字へ変わる場合はeffective writer outputが変わるためfingerprintも変わる。
- VMDは30fps、frame number / value / count / sort orderをmorph-name mappingで変えない。
- TEXTありとvoice-onlyは同じresolved output-name tupleをwriterへ渡す。

### 6.3 B6の完了と文書状態語

- B5完了記録はcurrent baselineとして利用するが、B6 pass証拠へ読み替えない。
- B6のmandatory matrix、関連回帰、full suite、compileall、diff checkがpass表示・process exit code 0になるまで、B6を`Implemented / Automated Verification Passed`へ変更しない。
- `src/gui_wx/ui_state.py`のRedo repairを実施した場合はuser-visibleなUndo / Redo挙動が変わるため、ユーザーへprofile Apply後のUndo / Redoを含む限定manual GUI確認を依頼し、結果を受領するまで該当状態語を同期しない。
- B6がdocs / testsだけで、production codeを変更しない場合は新規manual GUI確認を必須とはしない。その場合は`Manual GUI Not Required`とし、B5のユーザー確認証拠を分けて記録する。
- package manifestは現行baselineで`profiles.json`非同梱を静的確認し、原則変更しない。もし実ファイルとの差異が見つかった場合は、B6の状態同期を止めてP2として報告し、release方針を追加判断なしに変更しない。
- B6完了後もMS23全体は`B7 Closeout Audit Pending`であり、Closeout済みとは記載しない。

## 7. 対象ファイル

以下は将来のB6実装時に変更する可能性があるファイルである。本plan作成時点では本ファイル以外を変更しない。

### 7.1 主変更

| ファイル | 現在の存在 | 変更条件 / 責務 |
|---|---|---|
| `tests/test_ms23_b6_model_profile_lifecycle.py` | 未作成。B6専用testとして作成予定 | B1〜B5のcross matrixを一か所に固定する。non-wx / wxのfixtureを同一file内で分離し、wxを利用する場合はB4B helperとtemporary storeを必須とする |
| `src/gui_wx/ui_state.py` | 存在確認済み。条件付き最小repair候補 | B6開始時にUndo / Redoのprofile state再投影をdirect testで確認する。欠落が再現した場合だけ、この既存ownerへ最小repairを行う。再現しない場合は関連確認として変更しない |

新機能用production fileは作成しない。ほかのproduction code変更は、B6 testが既存契約違反を再現し、既存ownerが明確な場合だけに限定する。

### 7.2 関連確認

| 責務 | 確認対象 | 確認内容 |
|---|---|---|
| morph-name正本 | `src/core/morph_name_sets.py` | built-in ID、display name、ordered output names、default Japanese |
| profile store / resolver | `src/core/model_profiles.py`、`src/core/model_profile_state.py`、`src/core/settings_store.py` | strict load、startup fallback、guard、runtime identity、commit前後failure |
| preset store | `src/core/generation_presets.py` | built-in / user CRUD、Custom resolution、profile referenceとの相互作用 |
| output state / history | `src/core/output_edit_state.py`、`src/core/event_adjustment_history.py`、`src/gui_wx/ui_state.py` | profile-aware state、Undo / Redo、normalization、fingerprint identityと無関係なmetadata |
| writer | `src/core/pipeline.py`、`src/vmd_writer/writer.py`、`src/vmd_writer/effective_shape_adapter.py` | final normalization後の一回mapping、TEXTあり / voice-only、30fps |
| Preview | `src/core/preview_transform.py`、`src/gui_wx/preview_panel.py`、`src/gui_wx/placeholder_panels.py` | analyzed / empty / clear / errorで同じordered output namesを保持 |
| diagnostics / report / fingerprint | `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、`src/gui_wx/output_diagnostics_adapter.py` | allowed names、profile summary、report field、effective frames由来fingerprint |
| lifecycle | `src/gui_wx/app.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/main_frame.py`、`src/gui_wx/analysis_rollback.py` | startup、save、failure、cancel、rollback、reset、stale worker、VMD保存 |
| B5 UI regression | `src/gui_wx/right_pane.py`、`src/gui_wx/main_frame.py` | `wx.ID_YES`、Delete後Choice再投影、profile / preset panel cross-sync |
| B5 long-vowel regression | `src/core/pipeline.py` | 連続同一母音long runのhold / decay境界 |
| runtime / package境界 | `.gitignore`、`MMD_AutoLipTool.spec`、`build.ps1`、`docs/Release_Package_Manifest.md`、`pyproject.toml`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` | root ignore、non-stage、`profiles.json`非同梱、dependency / license / Qt / network不変 |

### 7.3 テスト

既存の主な直接回帰対象は次のとおりである。

- `tests/test_ms23_b6_model_profile_lifecycle.py`（B6専用、12件）

- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b2_import_boundaries.py`
- `tests/test_ms23_b3_model_profiles.py`
- `tests/test_ms23_b4_model_profile_state.py`
- `tests/test_ms23_b4_profile_history.py`
- `tests/test_ms23_b4_settings_save.py`
- `tests/test_wx_ms23_b4_profile_runtime.py`
- `tests/test_ms23_b4b_wx_teardown.py`
- `tests/test_ms23_b5_model_profile_controller.py`
- `tests/test_wx_ms23_b5_model_profile_ui.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_wx_ms22_b6_lifecycle_regression.py`
- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_preview_transform.py`

既存testを変更する場合は、元の責務に直接属するassertion補強だけとする。B6専用の複合scenarioを古いMS testへ分散させない。skip / xfail、assertion弱化、fixtureによるproduction contract回避は禁止する。B6専用testは12件がpassし、最初のRedo不一致はproduction repair前に再現記録した。

### 7.4 文書

| 文書 | B6実装時の扱い |
|---|---|
| `docs/Implementation_Plan/MS23-B6_Implementation_Plan.md` | 実際の対象file、検証結果、manual境界、statusを同期する |
| `README.md` | profileなし／Japanese／Latin、Select / Apply、inherit / override、runtime file、既存presetとの関係を利用者向けに追記する。version bumpやrelease済み表現は追加しない |
| `readme_mmdautolip.txt` | 配布利用者向けにprofileの作成・適用・解除、対応morph、failure時の案内を同期する |
| `docs/Pipeline_Data_Contract_Specification.md` | MS22 generation stateの後へMS23 profile state / precedence / lifecycle / resolved-name flowを追加する |
| `docs/VMD_Output_Specification.md` | Section 7の英字非対象記述を、built-in Japanese / Latin対応へ更新する。任意mapping等はOut of Scopeのまま維持する |
| `docs/GUI_State_Theme_Specification.md` | MS23 profile panelのSelect / Apply、Busy / stale、control lock、reset / rollback / startup projectionを追加する |
| `docs/Error_Handling_Specification.md` | broken profile file、missing preset、active guard、write / replace / INI save failureのfail-closed契約を追加する |
| `docs/MS20_and_Beyond_Index.md` | B6の実際の到達状態と次工程B7を同期する |
| `docs/MS20_and_Beyond_Roadmap.md` | B6実装・検証記録を追記し、実MMDはMS26、closeoutはB7へ残す |
| `docs/Implementation_Plan/MS23_Block_Breakdown.md` | B6 statusと検証証拠、B7 handoffを同期する |
| `docs/Release_Package_Manifest.md` | 原則は関連確認のみ。`profiles.json`をdefault dataとして追加しない。package/release方針の改定はB6で行わない |

## 8. 実装方針

### 8.1 matrix-first

B6は「full suiteが通った」だけで完了させない。B1〜B5の境界を代表scenarioへ対応付け、各scenarioで次の観測値を同じcanonical stateから比較する。

- active profile ID / display name
- active runtime baseline preset ID / display name
- resolved generation settings / morph upper limit
- resolved morph-name set ID / ordered output names
- writer morph frames
- Preview row display names / control points
- diagnostics generation summary / allowed morph names
- diagnostic reportのprofile / morph-name set field
- save-state fingerprint
- output historyのcurrent / undo / redo endpoint
- VMD saveability、analysis invalidation、rollback可否

### 8.2 single resolved morph-name contract

`GenerationState.resolved_morph_name_set_id`から`get_builtin_morph_name_set()`で得たordered output-name tupleを、次のconsumerへ明示的に渡す現行境界を維持する。

```text
ModelProfileState / GenerationState
  -> built-in MorphNameSet
  -> ordered output names
       -> Preview display projection
       -> effective writer adapter / VMD writer
       -> diagnostics allowed_morph_names
            -> diagnostic report
            -> save-state fingerprint effective_morph_frames
```

consumerごとにID表、英字変換、fallbackを再実装しない。reportはdiagnostics snapshotから生成し、fingerprintはprofile ID / display nameではなくeffective writer framesを正本とする。

### 8.3 repair boundary

- testが既存契約違反を再現しない場合、production codeを変更しない。
- testが違反を再現した場合、原因ownerの既存functionへ限定repairする。
- schema、public format、dependency、UI layoutを変える必要が出た場合はB6の範囲を超えるため、実装を止めて判断を戻す。
- repair後は再現test、MS23 direct regression、関連回帰、full suiteを順に再実行する。

### 8.4 docs sync boundary

- 利用者文書は操作と結果を説明し、内部class / error codeを羅列しない。
- 仕様文書はstate、precedence、failure、consumer境界を記録する。
- routing文書は実装・検証・manual evidence・未確認事項のstatusだけを記録する。
- `planned`から`implemented`への変更は、対応する自動testがpass表示かつprocess exit code 0になった後だけ行う。
- 実MMD、MS24、MS25、MS27は実装済みと記載しない。

## 9. 詳細ステップ

### Step 1: fresh implementation pre-check

- live Git、B5 commit差分、B6 / B7責務、現行test名を再確認する。
- B6 dedicated testは固定済みの`tests/test_ms23_b6_model_profile_lifecycle.py`へ作成する。non-wx / wxのfixtureとteardownは同一file内で責務を分ける。
- `UiState.undo_output_edit_state()` / `redo_output_edit_state()`の両方について、`output_edit_history_state.current_model_profile_state`が`UiState.model_profile_state`へ再投影されることをdirect testで確認する。特にRedoは、現行コード上で`generation_state`だけを更新してprofile stateを明示代入していないため、MainFrameの履歴操作経路も含めて確認対象とする。
- Redo経路でprofile stateの不一致が再現した場合は、`src/gui_wx/ui_state.py`の既存ownerへ最小repairを行い、同じdirect testとB6回帰を再実行する。不一致が再現しない場合は補完経路の根拠をtestへ固定し、production codeは変更しない。いずれの場合も、B6のdirect regressionと受け入れ条件が通るまでB6完了状態へ同期しない。
- existing docsの矛盾箇所をline単位でinventory化する。
- runtime / package / dependency境界のbaselineを記録する。

### Step 2: B6 dedicated cross-regression scaffold

- temporary `SettingsStore`、`GenerationPresetStore`、`ModelProfileStore`を使うfixtureを作る。
- wxを使う場合は`get_or_create_wx_app()` / `destroy_wx_app()`と`workspace_tempdir()`を使う。
- root runtime file pathをfixtureへ渡さない。
- Japanese / Latin、TEXTあり / voice-only、rollback可 / 不可を小さなbuilderで明示し、scenario間でmutable stateを共有しない。

### Step 3: output consumer一致

- 同じeffective shape planからwriter frame、Preview control point、diagnostics effective frameを生成する。
- frame number / value / count / orderが同一で、nameだけがresolved setに従うことを確認する。
- reportがactive profile / baseline / resolution / morph setをdiagnostics snapshotどおり表示することを確認する。
- metadata-only Renameでfingerprint不変、日本語から英字へのmapped output変更でfingerprint変化を確認する。
- empty / clear / invalid outputでは、Preview row labelをactive setのまま保持し、writer / fingerprintを無理にready扱いしない。

### Step 4: input / lifecycle matrix

- TEXTありsuccessとvoice-only successが同じresolved tupleをVMD writerへ渡すことを確認する。
- failure / cancelでrollback可能なら、plan、generation state、profile state、history、Previewを同じsnapshotから復元する。
- rollback不能ならold outputをcurrent扱いせず、saveabilityとfingerprintをfail closedにする。
- workspace resetでinput / plan / history / diagnosticsをclearし、profile / runtime baseline / resolved settingを保持する。
- startupでvalid profile、missing runtime baseline、missing active profile、missing default preset、broken profile fileを確認する。
- stale / duplicate worker resultがprofile / output / diagnostics / history / panel stateを変更しないことを確認する。

### Step 5: profile / preset CRUD matrix

- inactive profile CRUDがcurrent outputを暗黙変更しないことを確認する。
- active profileはRename-only、value / set / default reference UpdateとDeleteを拒否する。
- profileから参照中のuser preset Deleteを`preset_referenced_by_profile`で拒否する。
- active runtime baseline presetのvalue Update / Deleteを拒否し、同値Renameだけを許可する。
- profile load failureでpreset reference check不能なら、preset mutationをfail closedにする。
- missing default preset profileは一覧に保持し、Apply拒否とinactive Update修復を分ける。
- commit前failureはstate / store / file / history不変、commit後INI save failureはcommitted in-memory state / history保持を確認する。

### Step 6: B5回帰

- Delete確認No / closeで完全不変、`wx.ID_YES`でだけDelete requestが進むことを維持する。
- Delete成功後にChoiceのstring / stable ID / selectionがcanonical profile tupleへ同期することを確認する。
- 連続同一母音long runをhold / decayで解決し、Preview / writerのsource event集合とframe contractを確認する。

### Step 7: documentation sync

- README / readmeへprofile操作、Japanese / Latin、presetとの関係、runtime persistence、failure時の利用者行動を反映する。
- Pipelineへprofile state、runtime baseline、precedence、analysis / output-only分類、lifecycleを反映する。
- VMD仕様の英字非対象記述を修正し、built-in 2セットと30fps不変を記録する。
- GUI仕様へSelect / Apply、CRUD lock、Busy / stale、workspace reset、startup / rollback projectionを反映する。
- Error仕様へload / reference / mutation / persistence failure matrixを反映する。
- 各仕様の変更履歴へMS23-B6同期を追記する。

### Step 8: validation and status sync

- dedicatedからfull suiteまで一つずつ実行する。
- test summaryとprocess exit codeを別に記録する。
- diffをproduction / test / docs / runtime dataへ分類して監査する。
- mandatory gate通過後にだけB6 statusと文書状態語を同期する。
- B7 Closeout Auditへ、確認済み証拠、未確認事項、manual主体、実MMD deferredを引き継ぐ。

## 10. 状態遷移 / データ契約

### 10.1 profile / preset resolution

| 状態 / 操作 | profile identity | preset identity | morph-name set | expected behavior |
|---|---|---|---|---|
| startup no-profile | `None` | exact-match presetまたはCustom | Japanese | INI数値を保持し、既存MS22挙動を維持 |
| Japanese profile Apply | profile ID | active presetは`None`、baselineはprofile default | Japanese | profile overrideをfield単位で適用 |
| Latin profile Apply | profile ID | active presetは`None`、baselineはprofile default | Latin | output nameだけ`A / I / U / E / O`へ解決 |
| active profile中preset Apply | profile ID維持 | runtime baselineだけ変更 | profile required set維持 | nullable fieldだけ新baselineから継承 |
| no-profile Apply | profile / baselineをclear | exact-match reconciliation | Japanese | current generation settingsを保持 |
| missing runtime baseline startup | profile ID維持 | profile defaultへfallback | profile required set | `fallback_profile_default`とidentity correction save |
| missing active profile / default preset / broken file startup | profileなしへfallback | INI数値のexact-matchまたはCustom | Japanese | fail-closed、user profile mutation停止 |

### 10.2 cross-regression matrix

| ID | 入力 / lifecycle | profile / operation | 主な期待値 |
|---|---|---|---|
| M1 | empty startup | no-profile | Japanese rows、writer unavailable、diagnostics not-ready、profile identityなし |
| M2 | TEXTありsuccess | no-profile + preset単独 | writer / Preview / diagnosticsが日本語5母音、30fps、既存preset Custom規則維持 |
| M3 | TEXTありsuccess | Latin profile Apply | `A / I / U / E / O`がwriter / Preview / diagnostics / reportで一致し、mapped frame名によりfingerprint変化 |
| M4 | TEXTありsuccess | Japanese profile Apply | profile metadataはreportへ出るが、effective output同値ならidentity / Renameだけでfingerprintを変えない |
| M5 | analyzed | profile解除 | profile / baseline clear、Japanese復帰、exact preset reconciliation、history transaction整合 |
| M6 | voice-only success | Latin profile | TEXT pathなしVMD保存でもLatin tupleをwriterへ渡し、existing voice-only saveabilityを維持 |
| M7 | failure / cancel、rollback可 | active profile | plan、profile、baseline、generation、history、Previewをatomic復元し、ERROR / cancel優先規則を維持 |
| M8 | failure / cancel、rollback不可 | active Latin profile | stale outputをready扱いせず、empty / clear Preview labelはLatinを維持し、fingerprintはfail closed |
| M9 | workspace reset | active profile | input / plan / history / diagnosticsをclearし、active profile / baseline / resolved settingsを保持 |
| M10 | restart相当 | valid / missing / broken profile | valid復元、runtime baseline fallback、no-profile fallback、identity-only saveをfailure matrixどおり分離 |
| M11 | stale / duplicate worker callback | any active profile | profile / output / history / diagnostics / panel revisionを完全不変 |
| M12 | Undo / Redo | profile Apply / preset Apply / event edit | profile state、baseline、generation、mapped names、report / fingerprintをendpointどおり往復 |
| M13 | CRUD | profile / preset相互参照 | inactive CRUD非Apply、active lock、referenced preset guard、baseline guard、missing reference repair |
| M14 | persistence failure | profile mutation / settings save | commit前は完全不変、commit後INI failureはin-memory commit保持とsave-disabled |
| M15 | B5 regressions | Delete / long-vowel | `wx.ID_YES`だけDelete、Choice再投影、連続同一母音hold / decay Preview成功 |

すべての組合せを直積で増やさない。上表で各境界を最低1回は通し、Japanese default、Latin mapping、profile解除、preset単独、TEXTあり、voice-onlyを別々の代表caseで固定する。

### 10.3 CRUD / guard contract

| 操作 | 許可条件 | 拒否時 |
|---|---|---|
| profile Create | store available、valid preset reference、上限内 | store / state / history不変 |
| inactive profile Update / Delete | target存在、reference valid | current output不変 |
| active profile Rename | ID・set・values・reference同値 | metadataだけ同期、fingerprint不変 |
| active profile value / set / reference Update / Delete | 許可しない | `active_profile_locked`、全不変 |
| referenced user preset Delete | 許可しない | `preset_referenced_by_profile`、全不変 |
| active runtime baseline value Update / Delete | 許可しない | `active_profile_baseline_locked`、全不変 |
| active runtime baseline same-settings Rename | 許可 | metadataだけ同期 |
| broken profiles store中のpreset mutation | profile referenceを安全に確認できないため拒否 | `profile_reference_check_unavailable`、全不変 |

### 10.4 history / rollback

- output history endpointは`OutputEditState`と`ModelProfileState`を同じtransactionとして扱う。
- Undo / Redo後にgeneration settingsだけを更新してprofile stateを古いendpointへ残してはならない。
- event adjustment transactionはactive profile contextを保持する。
- profile / preset deletion後のhistory normalizationはunresolvable endpointを除去するが、current outputを暗黙Applyしない。
- analysis rollback snapshotはgeneration stateとmodel profile stateを同時にcapture / validate / restoreする。
- profile変更後に到着した古いanalysis resultはrollback対象にもcurrent resultにも採用しない。

### 10.5 report / fingerprint

- diagnosticsの`resolved_morph_name_set_id`とdisplay nameはbuilt-in setのpairである。
- reportはactive profile、baseline、resolution status / reason、resolved morph-name setを同じsnapshotから表示する。
- no-profile Japanese defaultでprofile-specific linesを省略できるが、事実と矛盾するprofile / Latin表示をしてはならない。
- fingerprint schemaは現行`ms21-effective-output-v1`を維持する。
- profile ID、profile display name、preset display name、panel selectionはfingerprintへ追加しない。
- effective writer morph frame nameの変更はfingerprintへ反映する。

## 11. テスト方針

### 11.1 B6 dedicated test

B6専用`tests/test_ms23_b6_model_profile_lifecycle.py`で、少なくとも次を直接検証する。

- M2〜M15の代表scenario
- writer / Preview / diagnostics frame tupleの直接比較
- diagnostic reportのprofile / baseline / morph-name set field
- Japanese / Latinとmetadata-only Renameのfingerprint差分規則
- TEXTあり / voice-onlyのVMD save callへ渡る`output_morph_names`
- workspace resetでprofile保持、history clear
- startup valid / missing baseline / missing profile / broken `profiles.json`
- stale worker / duplicate callback不変
- profile-aware UndoとRedoの往復
- profile / preset guard error codeと完全不変
- commit前failure / commit後INI save failureの分離
- `UiState`単体およびMainFrame履歴操作経路でのUndo / Redo profile state再投影。Redo不一致を再現した場合は`src/gui_wx/ui_state.py`の最小repair後に同じdirect testを再実行する

### 11.2 実行順

実装時に実在pathを再確認し、次を一つずつ実行する。

1. B6 dedicated test
2. B2 morph-name / writer / Preview / diagnostics / import tests
3. B3 profile store / settings tests
4. B4 resolution / history / save / runtime tests
5. B4B teardown、B5 controller / wx UI、B5 long-vowel tests
6. report / fingerprint / VMD / Preview tests
7. startup / rollback / reset / stale / failure / voice-only tests
8. MS17〜MS22の関連回帰
9. wx aggregateを連続2回
10. full suiteを連続2回
11. `compileall src tests`
12. `git diff --check`
13. runtime ignore / tracking / package / dependency / license境界のread-only確認

代表commandは次のとおりである。B6 dedicated pathは実装前チェックで確定したpathへ置き換える。

```powershell
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms23_b6_model_profile_lifecycle.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms23_b2_morph_name_sets.py tests\test_ms23_b2_morph_name_adapters.py tests\test_ms23_b2_import_boundaries.py tests\test_ms23_b3_model_profiles.py tests\test_ms23_b4_model_profile_state.py tests\test_ms23_b4_profile_history.py tests\test_ms23_b4_settings_save.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_wx_ms23_b4_profile_runtime.py tests\test_ms23_b4b_wx_teardown.py tests\test_ms23_b5_model_profile_controller.py tests\test_wx_ms23_b5_model_profile_ui.py tests\test_ms22_b2_long_vowel_resolver.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms20_b2_output_diagnostics.py tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b6_diagnostic_report.py tests\test_ms20_b6_report_save_flow.py tests\test_pipeline_and_vmd.py tests\test_preview_transform.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_wx_ms22_b6_lifecycle_regression.py tests\test_ms21_b7_analysis_rollback.py tests\test_ms20_b7_diagnostics_state_integration.py tests\test_ms19_b4_voice_only_gui_state.py tests\test_ms19_b7_voice_only_error_handling.py tests\test_ms19_b8_workspace_reset.py tests\test_ms17_b8_late_worker_result_discard.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q -k "wx"
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
git check-ignore -v profiles.json presets.json MMD_AutoLipTool.ini
git ls-files -- profiles.json presets.json MMD_AutoLipTool.ini
```

`git ls-files --`は3 pathについて出力なしを期待する。runtime fileの有無や内容は確認しない。package境界はspec / build / manifestの静的確認とdiff確認に限定し、B6ではbuild / SmokeLaunchを実行しない。

### 11.3 pass表示とprocess exit code

- 各commandについて、test summaryとprocess exit codeを別々に記録する。
- `N passed`と表示されてもprocess exit codeがnon-zeroなら未合格とする。
- non-zero時は、関数単位、関連file単位、元command再実行の順で切り分ける。
- access violation、native teardown exception、runner異常をtest passへ読み替えない。
- 同じ失敗をtest削除、skip / xfail、assertion弱化で回避しない。
- full suite 2回のいずれかがnon-zeroなら、安定性未確認としてB6完了状態へ同期しない。

### 11.4 manual GUI確認の主体境界

- B5でユーザーが実施済みのmanual GUI確認は、B5 UI範囲の証拠としてだけ再利用する。
- CodexがGUIを実行していない場合、Codex manual verificationとは記録しない。
- B6でGUI / production behaviorをrepairした場合、ユーザーへ影響箇所に限定した確認項目を提示する。
- 最低候補は、no-profile Japanese、Latin Apply、active profile中preset Apply、profile解除、再起動、新規作業、Delete後Choice、連続同一母音long-vowel Previewである。
- ユーザー報告を受領した場合は、実施者、対象項目、結果を自動testと分離して記録する。
- 実MMD確認はmanual GUI確認へ混ぜず、MS26未確認のまま残す。

## 12. 受け入れ条件

- B6が新機能追加ではなく、MS23-B1〜B5の横断回帰と文書同期として完了している。
- writer、Preview、diagnostics、report、fingerprintが同じresolved output-name contractを利用する。
- profileなし日本語、Japanese profile、Latin profile、profile解除、preset単独の代表caseが通る。
- TEXTありとvoice-onlyの両VMD保存経路がresolved output namesを使う。
- empty、analysis failure、cancel、rollback、workspace reset、startup、stale workerのstate contractが通る。
- profile-aware Undo / Redoがprofile state、baseline、generation state、mapped outputをatomicに往復する。
- `UiState`単体およびMainFrame履歴操作経路でUndo / Redo後の`model_profile_state`がhistory endpointと一致する。Redo不一致を再現した場合は、`src/gui_wx/ui_state.py`の限定repairと再回帰を完了している。
- profile CRUDとpreset CRUDの相互作用がguard matrixどおりである。
- 参照中preset Delete、active profile value mutation / Delete、active runtime baseline value Update / Delete、active profile direct editがcommit前に拒否される。
- missing presetとbroken `profiles.json`がfail closedで、current valid in-memory outputを不正に変更しない。
- commit前failureとcommit後INI save failureが分離されている。
- B5のDelete確認が`wx.ID_YES`でだけ進み、成功後Choice一覧とselectionが更新される。
- 連続同一母音long-vowelのhold / decay Preview回帰が通り、writerとのframe contractを壊さない。
- no-profileの既存日本語5母音、built-in Latin `A / I / U / E / O`、VMD 30fps、既存frame / value / count / orderが維持される。
- WAV / MP3 / M4A入力、入力音声 / 解析用WAV / MMD用WAVの三役、既存voice-only error / save contractを変更しない。
- `/profiles.json`、`/presets.json`、`/MMD_AutoLipTool.ini`がroot限定ignoreで、Git追跡・stage対象ではない。
- `profiles.json`をspec、build、release packageへdefault dataとして含めない。
- dependency、package、license、network、FFmpeg、Qt / PySide6境界に変更がない。
- README、配布用readme、Pipeline / VMD / GUI / Error仕様が検証済みMS23 behaviorへ同期している。
- planned / implemented / verified / user-reported / deferredの状態語が実際の証拠と一致する。
- B6 dedicated、MS23 direct、関連回帰、wx aggregate 2回、full suite 2回、compileall、diff checkがpass表示・process exit code 0である。
- manual GUI確認の要否、実施者、範囲が明記されている。
- 実MMD未確認がMS26へ残り、MS24 / MS25 / MS27を実装済みと記載していない。
- MS23全体をcloseout済みとせず、次工程をMS23-B7 Closeout Auditとしている。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| full suiteだけでconsumer不一致を見逃す | writer / Preview / diagnostics / report / fingerprintを同一scenarioで直接比較する |
| Japanese / Latinをsemantic vowelへ混入する | semantic keyを保持し、final normalization後のordered output namesだけをconsumerへ渡す |
| metadataだけでfingerprintが変わる | effective morph framesを正本とし、ID / display nameをpayloadへ追加しない |
| reportだけ古いprofile / setを表示する | diagnostics snapshotを唯一のreport入力とし、別lookup表を作らない |
| voice-onlyだけ日本語defaultへ戻る | TEXTあり / voice-only save callの両方で`output_morph_names`をassertする |
| empty / clearでLatin labelが日本語へ戻る | explicit output namesをempty / clear / error Previewへ渡すtestを維持する |
| Undoはprofileを戻すがRedoが戻さない | `UiState`のcurrent profile stateをUndo / Redo両方向でdirect assertする |
| rollbackでgenerationだけ戻りprofileがずれる | rollback snapshotのgeneration / model profile / historyを一組で比較する |
| workspace resetでprofileまで消す | workspace dataとpersistent generation/profile stateを分離assertする |
| stale workerがold outputを再commitする | job ID / active state mismatch後の全canonical state不変を比較する |
| profile / preset guard順序がconsumerごとに違う | core guard error codeと完全不変をdirect testし、UIはresultを投影するだけにする |
| broken profiles file中にpreset Deleteして参照を壊す | profile reference check不能時はpreset mutationをfail closedにする |
| B5 Delete修正が再退行する | `wx.ID_YES`、actual Choice strings、selection fallbackをdedicated UI testで維持する |
| B5 long-vowel補修が別modeで退行する | hold / decay双方でPreview / writer source eventとframe境界を確認する |
| runtime dataをtest / commitへ混入する | temporary store、root ignore、`git ls-files`出力なし、内容非読取をgateにする |
| docsが未検証behaviorをimplementedとする | mandatory gate後にだけ状態語を同期し、失敗時はPending / findingを残す |
| B6がrelease作業へ拡大する | package非同梱は静的確認だけとし、build / version / ZIP / releaseはMS27へ残す |
| B6で実MMD確認済みと誤記する | manual GUIとactual-MMDを分離し、後者をMS26へ明記する |

## 14. Codex実装時の注意

### 14.1 実行規則

- commandは必ず一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`を使わない。
- live repositoryを再確認し、過去のtest件数や文書記録だけでcurrent passを断定しない。
- pre-existing変更を保存し、unrelated fileを編集・stageしない。
- B6 dedicated testはtemporary directoryだけを使う。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`の内容を読まず、作成・削除・stageしない。
- stage、commit、push、merge、branch操作、package / release操作を行わない。
- production repair前にdiff scopeを再監査し、B6の既存契約違反だけに限定する。
- docs同期後にcode / test / docsを再照合し、実装済み／検証済み／user report／未確認を分ける。

### 14.2 実装後報告

完了報告は次を分ける。

1. 確認したファイル
2. 変更したファイル
3. B6で追加・補強したcross regression
4. repairの有無と理由
5. 実行したcommand、pass表示、process exit code
6. runtime / package / dependency / license境界
7. docsの状態語同期
8. manual GUI確認の要否・主体・範囲
9. 仕様から逸脱した点
10. 未確認事項とMS23-B7への引き継ぎ

### 14.3 固定した実装前判断

- B6専用testは`tests/test_ms23_b6_model_profile_lifecycle.py`の1ファイルへ固定し、non-wx / wxのfixtureとteardown責務はテスト内で分離する。別file分割は、実測したteardownまたは安定性問題を理由として記録した場合だけ許可する。
- Redo profile state再投影はB6最初の必須direct testで確認する。不一致が再現した場合は`src/gui_wx/ui_state.py`を既存ownerとして最小repairし、再現test・direct regression・関連回帰を通過させる。不一致が再現しない場合は補完経路をtestへ記録し、production codeを変更しない。
- `ui_state.py`をrepairした場合は、profile Apply後のUndo / Redoを含む限定manual GUI確認をユーザーへ依頼する。production codeを変更しない場合は、B5のユーザーGUI確認を再利用し、新規manual GUIは要求しない。
- `docs/Release_Package_Manifest.md`はprofiles.json非同梱の現行baselineを静的確認し、B6では変更しない。差異を検出した場合はB6状態同期を止め、P2として報告する。

### 14.4 実装結果（2026-08-20）

- `tests/test_ms23_b6_model_profile_lifecycle.py`を追加し、profile resolution、writer / Preview / diagnostics / reportの名前契約、TEXT / voice-only、empty / failure、startup、guard、atomic failure、reset、長音を横断検証した。
- 最初の必須direct testで、`UiState.redo_output_edit_state()`が履歴の`current_model_profile_state`を再投影しない不一致を再現した。`src/gui_wx/ui_state.py`へUndo側と同じprofile state投影を2行だけ追加し、専用test、関連回帰、full suiteを再実行した。
- B6専用は12件、B2〜B5基盤は56件＋31 subtests、wx / B4B / B5 / 長音は30件、diagnostics / writer / VMD / Previewは93件、lifecycle関連は46件＋7 subtestsがprocess exit code 0だった。
- wx aggregateは136件を2回、full suiteは797件＋57 subtestsを2回、`compileall src tests`と`git diff --check`もprocess exit code 0だった。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`はroot ignoreかつGit未追跡のままで、package manifest / spec / buildへの`profiles.json`記載はなく、Qt / HTTP / socket系依存の追加もない。
- README、配布用readme、Pipeline / VMD / GUI / Error仕様、Index、Roadmap、Block Breakdownの到達状態を同期した。2026-08-20にユーザーからprofile Apply後のUndo / Redoを含む限定手動GUI確認通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。実MMDのVMD / WAV読込・リップ同期はMS26へdeferredである。

B6のmandatory gateを満たした後は、MS23-B7 Closeout Auditへ進む。B7ではB1〜B6の要求、実装、test、ユーザーGUI証拠、文書、runtime data、package非同梱を総合監査し、P1 / P2 / P3とA / B / Cを判定する。実MMDによるVMD / WAV読込・リップ同期確認は引き続きMS26へ残す。
