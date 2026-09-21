# MS23-B1 Implementation Plan

## 1. 文書情報

- 文書名: MS23-B1 Contract / Schema / Pre-check Implementation Plan
- 作成日: 2026-08-12
- P2補正日: 2026-08-13
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時点のbranch: `main`
- 計画作成時点のHEAD: `4e85682 Finalize MS22-B7 closeout audit`
- 依存: MS22-B7 Closeout A、reviewed `MS23_Block_Breakdown.md`
- 文書ステータス: Completed / Decision Gates Adopted / Content Sync Applied / Contract Fixed
- fresh read-only contract pre-check: 2026-08-15 / P1 0件 / P2 0件 / P3 0件 / 249 passed / 全command process exit code 0
- B1の作業種別: documentation / read-only contract pre-check
- production code、test code、GUIの実装権限: なし

2026-08-12に、ユーザーは次のD1を採用した。

> profileの`default_preset_id`はpreset値の複製ではなくstable referenceとして保存する。profile Apply時は参照先presetをbaseline、profileのnon-null fieldをoverrideとして解決する。以後に別presetをApplyした場合もactive profileのnon-null overrideは維持し、nullable fieldだけが新しいpresetを継承する。

2026-08-13のP2解消指示に基づき、D1から派生するruntime baseline契約D1Aを採用した。

> `default_preset_id`はprofileを明示Applyしたときの既定baselineであり、active profile中に別presetをApplyした後のcurrent runtime baselineは専用INIキー`active_profile_baseline_preset_id`へ保存する。active profile中は既存`active_preset_id`をbaseline identityへ流用せず`None`とし、再起動時はvalidな専用runtime baselineへprofileのnon-null overrideを再適用する。preset単独時のCustom正規化は変更しない。

同日、ユーザーは残るdecision gate D2〜D5について、いずれも推奨案Aを採用した。

> D2: profileから参照中のuser presetは、参照を変更または解除するまでdeleteを拒否する。
>
> D3: active user profileのvalue / morph-name set updateとdeleteは、profileをinactive化するまで拒否する。Renameはoutput identityを変えないmetadata mutationとして分離する。
>
> D4: startupでactive profileがunresolvedならno-profile + Japaneseへ正規化し、INIの数値設定を保持する。profileはvalidだが専用runtime baseline presetだけがunresolvedなら、validなprofile `default_preset_id`へfallbackする。
>
> D5: canonical fingerprint payload構造を変更せず、schema ID `ms21-effective-output-v1`を維持する。Japanese / Latin差分はmapped effective frame名によるpayload値とfingerprint値の差として表す。

同日のB1実装前チェックで検出したpreset identityと直接編集のP2について、ユーザーの解消指示に基づき、既存MS22契約を維持するD6 / D7を採用した。

> D6: active profileのcurrent runtime baselineであるuser presetは、generation settingsのvalue updateとdeleteを、profileをinactive化するか別baselineへ切り替えるまで拒否する。同値settingsのRenameだけはmetadata mutationとして許可する。
>
> D7: active profile中のglobal generation settingsと`morph_upper_limit`のnon-no-op direct editは拒否する。exact no-opは完全不変とし、event adjustment、active profile中の別preset Apply、no-profile時の既存direct edit契約は変更しない。

2026-08-15の一問一答確認により、次のB1 material decisionを採用した。

- built-in IDは`builtin:japanese-vowels`と`builtin:latin-vowels`に固定する。mappingはそれぞれ`あ / い / う / え / お`と`A / I / U / E / O`とし、日本語を既定とする。
- active profile ID、runtime baseline preset ID、resolution statusはcore側の専用immutable profile stateが所有する。`GenerationState`はresolved morph-name set IDを含むoutput-only projectionを所有し、profile IDを直接所有しない。
- cross-storeの参照解決、missing reference、runtime mutation guard、startup fallbackはB4が所有する。B3は構造検証と永続化だけを担当する。
- workspace resetはactive profile、runtime baseline、resolved settings、resolved morph-name setを保持し、input、audio、base、output history、event selection、failure、playbackをclearする。
- `morph_upper_limit`はprofileのnullable overrideとし、`null`時はapplication default / INIを継承する。resolved値はanalysis parameterとして扱い、`GenerationState`やevent adjustmentには混在させない。
- startupのID正規化またはruntime baseline fallbackで補正が発生した場合は、補正後のactive ID / baseline IDをINIへ保存する。数値設定は保持し、補正がない場合は保存しない。

上記のexact class名、private helper名、error code名は、採用したownershipとfailure分類を変更しない範囲でB4 Implementation Planへ委譲する。

B1はD1 / D1A / D2〜D7を前提に、B2 / B3で実装者が再判断しなくてよいschema、state ownership、failure matrix、test ownershipを固定するBlockである。B1完了まではMS23 production code、test code、GUIを変更しない。

2026-08-15のread-only再チェックで、MS22 wx startup seamの19件はpass表示後にexit code 1となった。実スプラッシュをwx main loopなしで生成・破棄する最小経路でもaccess violationを再現できたため、production codeを変更せず、startup seam testだけがsplash専用テストと重複して実スプラッシュを生成しないようtest isolationを補正した。splashの表示・CallLater契約は`tests/test_wx_startup_splash.py`で維持する。補正後の同一19件commandはpass表示・exit code 0である。

2026-08-15にfresh read-only B1 contract pre-checkを実施した。現行Git状態、MS22 Closeout A、B1 plan / Block Breakdown / Index / Roadmap、profile未実装の現行code境界、関連test、依存関係、package境界を再照合し、import / identity 15件、preset / settings 29件、output state / history / preset UI 19件、lifecycle / rollback / reset 27件、Preview / diagnostics / writer 156件、splash 3件の合計249件がpass表示・process exit code 0となった。`git diff --check`もprocess exit code 0であり、P1 / P2 / P3は残存しなかった。MS23 featureのproduction code、test code、GUI、runtime user data、dependency、packageは変更していない。この結果によりB1をCompleted / Contract Fixedと判定し、B2 / B3 Implementation Plan策定へ進める条件を満たした。

## 2. 背景

MS22は、長音、`GenerationSettings`、built-in / user preset、output-only state、base-bound history、diagnostics、startup / reset lifecycleを実装・検証し、Closeout Aで完了した。

MS23 Roadmapは、モデル用途ごとの`morph_upper_limit`、hold、softness、preset、built-in morph-name setを`profiles.json`へ保存・再利用し、優先順位を`event adjustment > model profile > preset > application default`とする。一方、現行実装には次の異なる責務がある。

- `morph_upper_limit`はanalysis-affecting parameterであり、変更時にtiming plan、Preview、VMD保存可能状態を無効化する。
- hold、softness、long-vowel modeは`GenerationState`に属するoutput-only設定であり、base timing planを再解析せずeffective outputを再解決できる。
- event adjustmentはbase-boundで、peak、start / end、hold、softness、slope、long-vowel modeをevent単位にoverrideする。
- presetは`GenerationSettings`だけを保存し、`morph_upper_limit`やmorph-name setを所有しない。
- morph-nameはsemantic vowel、Preview label、writer frame、diagnostics validationに日本語5種として分散している。
- output fingerprintは実際のeffective writer frame名を既にcanonical payloadへ含める。

profile IDをそのまま`GenerationState`や`OutputEditState`へ入れるだけでは、analysis parameterとoutput historyが混在する。profileとpresetの参照関係も、missing / update / delete時の扱いを決めなければ暗黙fallbackや出力変化を起こす。B1でこれらを文書契約として先に解消する。

## 3. 目的

1. D1をexactなprofile / preset layering契約へ変換する。
2. `profiles.json` schema v1、validation、100件上限、atomic save、runtime user data境界を固定する。
3. application settings、preset、profile、event adjustmentのfield ownershipと優先順位を固定する。
4. active profile selection、analysis parameter、output-only state、history、INI、diagnosticsの責務を分離する。
5. Apply、Create / Update / Delete、preset reference mutation、startup / reset、failure時の状態遷移を固定する。
6. morph-name setとeffective output fingerprintのidentity境界を固定する。
7. B2〜B6の変更可能範囲、test ownership、受け入れ条件を確定する。
8. B1実施後のP1 / P2 / P3とB2 / B3計画策定可否を判定する。

## 4. In Scope

- user profile用`profiles.json` schema v1契約の確定
- stable profile ID、display name、built-in morph-name set ID、nullable override、`default_preset_id` reference契約
- profile上限100件、duplicate、型、範囲、future schema、broken JSON、atomic replace契約
- `default_preset_id`のlookup、参照整合性、missing / update / delete契約
- `morph_upper_limit`、hold、softness、long-vowel mode、morph-name set、event adjustmentのfield ownership
- active profile selection、resolved profile、`GenerationState`、`OutputEditState`、`AnalysisParameterSnapshot`、INIのownership
- profile Select / Apply / Create / Update / Delete、no-profile Apply、別preset Applyの状態遷移
- startup、workspace reset、analysis failure / cancel / rollback、stale worker resultのprofile境界
- Japanese / Latin built-in morph-name set IDとsemantic-to-output mapping契約
- writer、Preview、diagnostics、save-state fingerprintのidentity契約
- `/profiles.json`のroot限定ignore、local保持、非stage、package非同梱方針
- B2〜B6のfile / test ownershipと実装順
- B1で必要な文書修正と、既存testのread-only baseline確認

## 5. Out of Scope

- MS23 featureのproduction code、test code、GUIの実装
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`本体の作成・変更・stage
- model profile UIの作成
- writer / Preview / diagnosticsへのmorph mapping実装
- PMX / PMD読込、model file解析、model name自動取得
- 任意morph mapping、user-defined morph-name set、追加表情morph
- 英語音声認識、英語音素処理、Whisper model selection（MS24）
- batch output専用DTO / adapter / UI / package生成（MS25）
- 実MMDによるVMD / WAV読み込み・リップ同期確認（MS26）
- packaging / release readiness（MS27）
- dependency追加、VMD format、30fps、WAV contract、network、Qt / PySide6の変更
- branch作成・削除、stage、commit、merge、tag、push

## 6. 前提条件

### 6.1 repository baseline

- B1 pre-check実施時点（2026-08-15）のGitは`feature/MS23-implementation`、HEADは`16740b6 Document MS23-B1 contract decisions`であった。分岐元は`main`の`4e85682`である。これはB1実施時点の履歴であり、現在のGit状態を示す記載ではない。
- MS22-B7 CloseoutはA判定であり、未完了へ戻さない。
- MS22 direct regression 93件、基盤185件、MS21 138件、MS17 / MS19 / MS20 158件、B4 / B5 / splash 18件、full suite 713件、`compileall`、`git diff --check`はMS22 closeout時点でpass / exit code 0である。
- B4〜B6 GUI確認はユーザー報告であり、Codex自身のmanual GUI実行とは扱わない。
- 実MMD確認はMS26へdeferredである。

### 6.2 current worktree protection

- 現在のworktreeにはMS23計画・P2/P3補正による文書差分と、startup seam testのtest isolation補正がある。
- これらはユーザー所有の作業として保持し、restore、stage、commitしない。
- `presets.json`と`MMD_AutoLipTool.ini`はlocal runtime user dataとして存在し、root限定ignore対象である。内容を読替え・上書きしない。

### 6.3 current implementation facts

- `GenerationSettings`はclosing hold、closing softness、long-vowel modeを所有する。
- `GenerationState`は`GenerationSettings`とactive preset IDを所有し、baseなしでも有効である。
- `OutputEditState`はbase identity、adjustment snapshot、`GenerationState`をbase-bound history transactionとして保持する。
- `morph_upper_limit`は`AnalysisParameterSnapshot`とGUI parameterに属し、変更時はanalysisを無効化する。
- `GenerationPresetStore.resolve_active()`はunknown / mismatched preset IDを、現在の3設定値を保持したCustomへ正規化する。
- workspace resetはgeneration settingsとactive presetを保持し、input、base、history、selection、failureをclearする。
- output fingerprintは`effective_morph_frames[].morph_name`を含み、active preset ID / display nameを直接含まない。
- `src/core/__init__.py -> src/core/pipeline.py -> src/vmd_writer/__init__.py -> writer.py`のimport経路があり、writerからcoreへのmodule-level逆importは循環を生じ得る。
- repositoryでは`src.vmd_writer.writer`とtop-level `vmd_writer.writer`が別moduleとしてloadされ得るため、shared DTOのclass identity一致を前提にできない。
- final morph normalizationはsemanticな日本語5母音key、protected range、required zero、全5母音open-stateを同じkey空間で処理する。
- generation / preset Apply後のINI保存はin-memory commit後に行われ、保存失敗時はcurrent stateとhistoryをrollbackしない。

## 7. 対象ファイル

### 7.1 B1で変更可能な文書

- `docs/Implementation_Plan/MS23-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

B1実施中に正本仕様のplanned contractを同期する必要が判明した場合だけ、次を文書変更候補に追加する。B1でimplemented表現へ変更しない。

- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`

### 7.2 read-only code確認対象

- `src/core/__init__.py`
- `src/core/generation_presets.py`
- `src/core/settings_store.py`
- `src/core/output_edit_state.py`
- `src/core/event_adjustment.py`
- `src/core/event_adjustment_history.py`
- `src/core/effective_shape_plan.py`
- `src/core/output_diagnostics.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/core/diagnostic_report.py`
- `src/core/preview_transform.py`
- `src/core/preview_hit_test.py`
- `src/vmd_writer/writer.py`
- `src/vmd_writer/effective_shape_adapter.py`
- `src/vmd_writer/__init__.py`
- `src/gui_wx/app.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/ui_sync_context.py`
- `src/gui_wx/analysis_rollback.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/preview_panel.py`
- `.gitignore`

### 7.3 read-only test確認対象

- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b7_import_boundaries.py`
- `tests/test_ms22_b2_import_boundaries.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_settings_store.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_wx_ms22_b4_generation_state.py`
- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_ms22_b6_lifecycle_regression.py`
- `tests/test_wx_ms22_b6_lifecycle_regression.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_preview_transform.py`
- `tests/test_ms21_b3_preview_hit_test.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_zero_guard.py`

### 7.4 package / distribution関連確認

- `MMD_AutoLipTool.spec`
- `build.ps1`
- `docs/Release_Package_Manifest.md`
- `README.md`
- `readme_mmdautolip.txt`

これらはB1で原則変更しない。`profiles.json`をbundled default dataにしない境界の確認だけを行う。

## 8. 実装方針

B1はコード実装ではなく、次の順序で契約を固定する。

1. live Git、current plan差分、MS22 Closeout Aを再確認する。
2. D1をadopted decisionとして文書間で同じ表現へ統一する。
3. profile schema v1のfield、型、nullable、range、stable ID、referenceを固定する。
4. field ownershipとprecedenceを現行class / DTOへ対応付ける。
5. analysis-affecting stateとoutput-only stateを分離する。
6. Apply、mutation、reference、startup、reset、failure matrixを固定する。
7. morph-name mappingとfingerprint identityを固定する。
8. import方向、mixed namespace、structural input境界を固定する。
9. B2〜B6 ownershipと新規test候補を確定する。
10. 既存testをread-only baselineとして必要最小限実行する。
11. diffとruntime user data境界を監査する。
12. P1 / P2 / P3を分類し、B1のCompleted / Contract Fixed可否を判定する。

未確定の設計判断は一問一答で確認する。未回答のdecision gateを暗黙採用せず、B1をContract Fixedにしない。

## 9. 詳細ステップ

### Step 1: repository基準線の固定

- `git status --short --branch`、branch、HEAD、直近履歴を一コマンドずつ確認する。
- pre-existing MS23計画差分を記録し、production / test / GUI差分がないことを確認する。
- `presets.json`、`MMD_AutoLipTool.ini`のlocal保持・root限定ignoreを確認する。

### Step 2: D1 / D1A採用状態の同期

- `default_preset_id`をstable referenceとする。
- referenced presetをbaselineとする。
- profileのnon-null overrideをpresetより優先する。
- active profile中に別presetをApplyした場合、profile overrideを維持し、nullable fieldだけ新presetを継承する。
- profile Apply時は`active_profile_baseline_preset_id=default_preset_id`としてruntime baselineを初期化する。
- active profile中に別presetをApplyした場合は、`active_model_profile_id`を維持して`active_profile_baseline_preset_id`だけを更新し、INIへcurrent runtime baselineとして保存する。
- active profile中の既存`active_preset_id`は`None`とし、profile baseline identityとして流用しない。
- no-profile Applyでは`active_profile_baseline_preset_id`をclearし、既存preset identityはeffective settingsがpreset本体とexact一致する場合だけ`active_preset_id`へ復元する。
- 再起動時はvalidな`active_profile_baseline_preset_id`をbaselineとしてprofile overrideを再適用し、`default_preset_id`へ暗黙に巻き戻さない。
- Block Breakdown、Index、Roadmap、B1 planで表現差がないことを確認する。

### Step 3: profile schema v1の固定

- root object、schema version、`user_profiles`、100件上限を固定する。
- profile ID、display name、morph-name set ID、nullable upper limit、nullable generation override、required `default_preset_id`を型表へする。
- current preset schemaと同じdisplay name長・duplicate・UUID・unknown key・bool-as-int・non-finite number・range・unknown morph setの検証契約を固定する。
- structurally validだがpreset referenceがmissingなprofileはresolution errorとして扱い、profileを編集可能な状態で残す。

### Step 4: preset reference integrityの固定

- built-in / user presetのstable ID lookupを既存store APIへ対応付ける。
- profile create / update時のmissing reference拒否を固定する。
- profileから参照中のuser presetは、参照profileの`default_preset_id`を先に変更またはprofileを削除するまでdeleteを拒否する。拒否時はpreset store、profile store、current state、INIを変更しない。
- active profileのcurrent runtime baselineではないreferenced user presetのvalue updateはcurrent outputへ自動適用せず、次の明示profile / preset Applyまたはstartup resolutionで使用する。
- active profileのcurrent runtime baselineであるuser presetは、generation settingsのvalue updateとdeleteを、profileをinactive化するか別baselineへ切り替えるまで拒否する。拒否時はpreset store、profile store、current state、history、INIを完全不変とする。
- current runtime baseline presetのsettingsが既存値とexact一致するRenameはmetadata mutationとして許可し、profile ID、baseline ID、effective output、history、fingerprint、INIを変更しない。
- external JSON編集や起動順によるdangling referenceのfallbackを固定する。
- cross-store検証はB4 resolver / mutation guardが所有し、B3 storeは構造検証、load / save、atomic replaceだけを提供する。B3はmissing referenceをapplication defaultへ黙って置換しない。

### Step 5: field ownership / precedenceの固定

- `morph_upper_limit`、hold、softness、long-vowel mode、morph-name set、event adjustment全7 fieldをownership表へ対応付ける。
- profileとevent adjustmentが重なるのはhold、softness、long-vowel modeだけであることを固定する。
- presetが`morph_upper_limit`とmorph-name setを所有しないことを固定する。

### Step 6: state ownershipの固定

- active profile selectionを、baseなしで保持するpersistent selectionとして定義し、core側の専用immutable profile stateへ置く。planned moduleは`src/core/model_profile_state.py`とし、B4 planではprivate helper名だけを確定する。
- active profile ID、runtime baseline preset ID、resolution statusを同じprofile stateのownershipとして扱う。
- resolved upper limitをanalysis parameterとして扱う。
- resolved hold / softness / long-vowel modeとmorph-name setを`GenerationState`のoutput-only projectionとして扱う。
- profile ID全体を無条件で`OutputEditState`へ入れない。
- output-only Undo / Redoとprofile identity reconciliationの責務を固定する。
- profile-aware resolverより前に既存`GenerationPresetStore.resolve_active()`をeffective settingsへ適用し、profile overrideをpreset mismatchと誤判定してruntime baseline IDを消さない。

### Step 7: Select / Apply / mutation状態遷移の固定

- candidate selectionはstateを変更しない。
- Apply前にimmutable resolutionを完成させ、validation / resolution / commit前failureでは完全不変とする。
- upper limit差分ありApplyはanalysis invalidation / base-bound history clearとする。
- upper limit差分なしApplyはoutput-only transaction候補とする。
- Create / Update / DeleteはApplyと分離する。
- active user profileのvalue / morph-name set updateとdeleteはinactive化まで拒否し、current state、history、profile store、INIを変更しない。Renameはcurrent effective outputを変えないmetadata mutationとして扱う。
- active profile中のglobal generation settingsと`morph_upper_limit`のnon-no-op direct editはcommit前に拒否し、analysis invalidation、history transaction、store / INI saveを発生させない。exact no-opは完全不変とする。
- D7はevent adjustment編集、active profile中の別preset Apply、no-profile時の既存direct editを禁止しない。no-profile時はMS22のpreset identity正規化、output-only history、`morph_upper_limit`変更時のanalysis invalidationを維持する。
- commit後のINI保存failureでは、MS22契約どおりin-memory state / historyをrollbackせず、初回通知、同一sessionのsave停止、次回起動時のlast successful INI復元を維持する。

### Step 8: startup / reset / failure matrixの固定

- missing file、broken JSON、future schema、unknown active ID、missing preset reference、invalid set IDを分類する。
- startup時に保持するINI数値設定、active preset、active profile、morph-name setを表にする。
- no-profileはJapanese setであることを全failure経路で維持する。
- active profile自体がunresolvedならno-profile + Japaneseへ正規化してINI数値設定を保持する。profileがvalidで専用runtime baselineだけがunresolvedなら、validなprofile `default_preset_id`へfallbackする。
- startupの正規化またはruntime baseline fallbackでactive ID / baseline IDが補正された場合は、補正後のIDだけをINIへ保存する。数値設定は保持し、補正がないstartupでは保存しない。
- workspace resetはactive profile、runtime baseline、resolved settings、resolved morph-name setを保持し、input、audio、base、output history、event selection、failure、playbackをclearする。
- analysis failure / cancel / rollback / stale worker resultがprofile selectionを勝手に変更しないことを固定する。

### Step 9: morph-name / fingerprint契約の固定

- semantic vowelを日本語5母音のまま維持する。
- built-in set IDとexact mappingを固定する。`builtin:japanese-vowels`は`あ / い / う / え / お`、`builtin:latin-vowels`は`A / I / U / E / O`とする。
- Preview label、writer frame、diagnostics effective outputが同じresolverを使うことを固定する。
- final normalizationはsemantic keyのまま完了し、その後にだけresolved output nameへmappingする順序を固定する。
- writer module-levelから`src.core` / `core`を逆importせず、明示adapterとstructural / primitive inputで`src.*` / top-level両namespaceを扱う。
- profile / preset / setの説明identityだけをfingerprintへ入れない。
- mapped effective frame名が変わると既存payloadでfingerprintが変わることを確認する。
- canonical payload構造を変更せず`ms21-effective-output-v1`を維持する。構造変更が必要と判明した場合はB1契約からの逸脱として実装を止め、schema更新を再判断する。

### Step 10: runtime user data / package境界の固定

- B3で`.gitignore`へroot限定`/profiles.json`を追加する計画を確定する。
- repository rootのruntime fileをtest fixtureに使わない。
- `profiles.json`をPyInstaller datas、release package default、tracked sampleへ入れない。
- sampleが必要になった場合は別名のschema exampleとしてdocs内に置き、runtime filenameを使用しない。

### Step 11: B2〜B6 ownershipとtest handoff

- B2: built-in morph-name setとexplicit adapter入力
- B3: profile DTO / JSON store / INI key / root ignore / structural validation
- B4: cross-store resolution / startup normalization / state / history / diagnostics / mutation guard
- B5: RightPane profile UI
- B6: lifecycle / regression / docs
- 各Blockの主変更、関連確認、新規test候補、禁止範囲を表にする。
- B2へfresh-process import順序、mixed namespace、normalize-before-mapの回帰testを必須handoffする。

### Step 12: B1判定

- adopted、pending、rejected decisionを台帳化する。
- findingsをP1 / P2 / P3へ分類する。
- P1 / P2または未回答のmaterial decisionがあればContract Fixedとしない。
- P1 / P2 / P3なし、必要なdecision確定、read-only baseline確認済みの場合だけB1をCompleted / Contract Fixedとし、B2 / B3 Implementation Plan策定可とする。

2026-08-15のfresh read-only contract pre-checkでは、P1 0件、P2 0件、P3 0件を確認した。採用済みdecisionと明示的deferを含むmaterial decisionも残っていないため、B1をCompleted / Contract Fixedと判定する。これは契約・計画段階の完了であり、MS23 featureのproduction code、test code、GUI実装完了を意味しない。

## 10. 状態遷移 / データ契約

### 10.1 用語

| 用語 | 意味 |
|---|---|
| selected profile | UIで候補選択しただけのprofile。stateへ未適用 |
| active profile | 明示Apply済みで、current resolved stateのsourceとして一致するprofile |
| unresolved profile | schema上は読めるがpreset reference等を解決できないprofile |
| no-profile | active profileなし。morph-name setはglobal Japanese |
| application layer | INIから復元したcurrent application setting。missing時はhardcoded default |
| preset layer | active / referenced presetの`GenerationSettings` |
| profile layer | profileのnon-null overrideとrequired morph-name set |
| event layer | base-bound `EventAdjustment` |

### 10.2 D1 adopted contract

```text
application layer
  -> referenced / selected preset layer
  -> active profile non-null override
  -> event adjustment（overlap fieldのみ）
```

- `default_preset_id`はrequired stable referenceとし、profile JSONへpreset値を複製しない。
- profile Apply時は`default_preset_id`をbaseline presetとして使う。
- active profile中に別presetをApplyした場合、preset baselineだけを置換し、profile non-null overrideを維持する。
- profile Apply直後のruntime baseline IDは`default_preset_id`とするが、別preset Apply後は選択preset IDを`active_profile_baseline_preset_id`としてINIへ保存する。
- startupではvalidな`active_model_profile_id + active_profile_baseline_preset_id`を一組として優先解決し、validなruntime baselineをprofile defaultへ暗黙に戻さない。runtime baselineだけがunresolvedな場合に限りD4の明示fallbackを使う。
- active profile中は`GenerationState.active_preset_id=None`を維持する。no-profileへ移る場合だけ、既存`resolve_active()`のexact-match規則で`active_preset_id`を再計算する。
- profile nullable fieldは新しいpreset / application layerから再解決する。
- profileにないevent-specific peak / offset / slopeはevent layerだけが所有する。

### 10.3 schema v1契約（B1採用）

```json
{
  "schema_version": 1,
  "user_profiles": [
    {
      "id": "uuid",
      "display_name": "Profile name",
      "morph_name_set_id": "builtin:japanese-vowels",
      "morph_upper_limit": null,
      "generation_overrides": {
        "closing_hold_frames": null,
        "closing_softness_frames": null,
        "long_vowel_mode": null
      },
      "default_preset_id": "builtin:standard-hold"
    }
  ]
}
```

| field | 型 | null | ownership / validation |
|---|---|---|---|
| `schema_version` | int exact `1` | 不可 | bool拒否、future version拒否、root unknown key拒否 |
| `user_profiles` | list | 不可 | 0〜100件 |
| `id` | canonical lowercase UUID string | 不可 | stable、duplicate拒否 |
| `display_name` | trimmed string | 不可 | trim後1〜100文字、制御文字・改行拒否、duplicate拒否 |
| `morph_name_set_id` | built-in set ID | 不可 | Japanese / Latinの2種のみ |
| `morph_upper_limit` | finite float | 可 | nullはapplication layer継承、値は現行0.0〜10.0 |
| hold / softness override | int | 可 | nullはpreset継承、値は現行0〜100 |
| long-vowel mode override | `hold` / `decay` | 可 | nullはpreset継承 |
| `default_preset_id` | non-empty stable ID | 不可 | built-in / user preset reference、missingはresolution error |

root object、profile entry、`generation_overrides`は許可key集合の完全一致を要求し、unknown keyを拒否する。`display_name`は既存presetと同じtrim後1〜100文字、制御文字・改行拒否、duplicate拒否とする。`default_preset_id`は必須のnon-empty stable referenceとし、構造上有効でも参照先がmissingの場合はschema errorではなくresolution errorとしてprofileを保持する。この契約は現行`src/core/generation_presets.py`のschema version、key set、display name、ID検証を根拠にB1で採用したplanned schemaであり、未実装である。

### 10.4 field ownership

| field | application | preset | profile | event adjustment |
|---|---|---|---|---|
| `morph_upper_limit` | current / default | なし | nullable override | なし |
| closing hold | default | baseline | nullable override | event override |
| closing softness | default | baseline | nullable override | event override |
| long-vowel mode | `hold` | baseline | nullable override | terminal event override |
| morph-name set | Japanese | なし | required Japanese / Latin | なし |
| peak value | base plan | なし | なし | event override |
| start / end offset | base plan | なし | なし | event override |
| slope ratio | base plan | なし | なし | event override |

### 10.5 state ownership

| state / identity | 所有内容 | base依存 | persistence | history |
|---|---|---|---|---|
| profile selection / resolution state | active profile ID、runtime baseline preset ID、resolution status | なし | INI (`active_model_profile_id`、`active_profile_baseline_preset_id`) | output historyへ無条件に入れない |
| application parameter | resolved `morph_upper_limit` | analysis入力 | INI | 変更時にbase history clear |
| `GenerationState`拡張 | resolved generation settings、active preset ID、resolved morph-name set ID | なし | INI projection | baseあり時はoutput history候補 |
| `OutputEditState` | base identity、adjustment snapshot、output-only generation projection | あり | なし | 最大50件 |
| diagnostics summary | profile / preset / set display identity、fallback | current snapshot | reportのみ | なし |

profile selection / resolution stateはcore側の専用immutable stateとして扱う。planned moduleは`src/core/model_profile_state.py`であり、B4 planではprivate helper名とerror code名を確定する。B1では`morph_upper_limit`を`GenerationState`へ入れないこと、resolved morph-name set IDは`GenerationState`のoutput-only projectionへ入れること、profile display nameをoutput identityにしないことを固定する。既存`active_preset_id`と`GenerationPresetStore.resolve_active()`はpreset単独時の互換契約として維持する。profile-aware resolutionはactive profile、専用runtime baseline preset、profile overrideをまとめて検証した後にeffective settingsを返す別責務とする。

### 10.6 Apply matrix

| 操作 | upper差分 | output差分 | analysis / history | commit前failure時 |
|---|---:|---:|---|---|
| candidate Select | 不問 | 不問 | 完全不変 | noticeのみ |
| valid profile Apply | なし | なし | resolved identity / settings / outputが全て不変ならno-op、それ以外はidentity reconciliation | 完全不変 |
| valid profile Apply | なし | あり | base再利用、output transaction候補 | 完全不変 |
| valid profile Apply | あり | 不問 | analysis invalidation、base-bound history clear | 完全不変 |
| no-profile Apply | 差分で分類 | Japanese setへ解決 | 同じ分類規則 | 完全不変 |
| active profile中のpreset Apply | なし | 差分で分類 | profile non-null override維持、nullableだけ再解決 | 完全不変 |
| active profile中のglobal direct edit | 不問 | exact no-op | 完全不変 | 完全不変 |
| active profile中のglobal direct edit | 不問 | non-no-op | commit前拒否。analysis / history / identity不変 | 完全不変 |

全Applyに共通して、commit後のINI保存failureは上表の「commit前failure」に含めない。in-memory commitとhistoryは維持し、初回だけ通知して同一sessionの後続saveを停止する。disk上はlast successful INIのままであり、次回起動時はその値から復元する。保存失敗を理由にprofile / preset identityやeffective outputを部分的に巻き戻さない。

### 10.7 mutation / reference matrix

| 操作 | current output | active identity | B1推奨 |
|---|---|---|---|
| profile Create | 不変 | 不変 | 作成後はcandidate選択のみ |
| inactive profile Update | 不変 | 不変 | 明示Applyまで未反映 |
| active profile Rename | 不変 | 維持 | output identityにdisplay nameを含めない |
| active profile value / set Update | 不変 | 維持 | inactive化まで拒否。store / history / INIも不変 |
| inactive profile Delete | 不変 | 不変 | selector fallbackのみ |
| active profile Delete | 不変 | 維持 | inactive化まで拒否。Japaneseへ暗黙変更しない |
| inactive baseline / referenceのuser preset Update | current outputへ未適用 | active profile維持 | 次回明示Applyまたはstartup resolutionまで未反映 |
| active runtime baseline preset Rename | 不変 | profile / baseline ID維持 | settings exact一致時だけmetadata update。history / fingerprint / INI不変 |
| active runtime baseline preset value Update | 不変 | 維持 | profile inactive化または別baseline選択まで拒否。全state / store不変 |
| active runtime baseline preset Delete | 不変 | 維持 | profile inactive化または別baseline選択まで拒否。fallbackしない |
| referenced user preset Delete | 不変 | 不変 | 参照profileが1件でもあれば拒否。参照変更後だけ削除可 |
| active profile中のglobal direct edit | 不変 | profile / baseline ID維持 | exact no-op以外をcommit前拒否。event adjustmentは対象外 |

D2 / D3 / D6 / D7により、通常UI操作ではdangling preset reference、active profile mutation、runtime baseline mutation、global direct editによるcurrent stateとの不一致を作らない。拒否はcommit前failureとして扱い、永続化要求も発生させない。

### 10.8 startup / failure matrix

| 状態 | profile store | active profile | morph set | 数値設定 | mutation |
|---|---|---|---|---|---|
| `profiles.json` missing | empty / valid | none | Japanese | INI current | available |
| invalid / unreadable / future JSON | unavailable | noneへ正規化 | Japanese | INI current保持 | disabled |
| active profile ID missing | valid | noneへ正規化 | Japanese | INI current保持 | available |
| active profile + valid runtime preset ID | valid / resolved | 維持 | profile set | runtime preset baseline + profile overrideで再解決 | available |
| active profile valid + runtime baseline missing | valid / resolved | 維持 | profile set | validなprofile default preset + profile overrideで再解決 | available |
| active profileのdefault preset ref missing | valid / unresolved | noneへ正規化 | Japanese | INI current保持 | available、修正可能 |
| inactive profileのpreset ref missing | valid / unresolved | current維持 | current維持 | current維持 | profile編集可能 |
| unknown morph-name set ID | schema / resolution error | noneへ正規化 | Japanese | INI current保持 | failure分類による |

inactive unresolved profile Applyは拒否し、current stateを完全不変とする。startup時にunresolved profileを部分適用しない。D4により、profile自体またはrequired default presetがunresolvedならno-profile + JapaneseとINI数値保持へ正規化し、profileがvalidで専用runtime baselineだけがunresolvedならprofile default presetへfallbackする。正規化後のin-memory active ID / baseline IDはresolved stateと一致させる。ID正規化またはruntime baseline fallbackで補正が発生した場合は、補正後のIDだけをINIへ保存する。数値設定は保持し、補正がないstartupでは保存しない。exactなerror code名とprivate helper名はB4 planで固定する。

### 10.9 morph-name / fingerprint identity

- semantic keyは`あ / い / う / え / お`を維持する。
- output setはJapaneseまたはLatinのbuilt-in 2種だけである。
- `EffectiveShapePlan`、normalization contract、protected range、required zero、open-stateはsemantic keyだけを扱う。
- writer adapterはsemantic frameのfinal normalization完了後に、各frameのnameだけをresolved output setへ一回mappingする。mapping後のframeへsemantic normalizationを再適用しない。
- writer file-I/O境界へLatin名を許可するときはcore DTOをimportせず、adapterからprimitiveなallowed output namesまたは構造的に同等なvalidated frame contractを明示入力する。既存引数省略時は日本語5母音だけを許可する。
- Japanese setではframe number、value、count、sort order、VMD bytes上のmorph名が既存出力と一致する。Latin setではframe number、value、count、sort orderを維持し、morph名だけを`A / I / U / E / O`へ置換する。
- `effective_morph_frames[].morph_name`はresolved output名を持つ。
- profile ID、display name、preset ID、morph-name set IDはdiagnostics summaryへ表示できるが、それだけでfingerprintを変えない。
- Japanese / Latin切替はeffective frame名が変わるため、既存canonical payloadでfingerprintが変わる。
- canonical payload構造を変えない限り`ms21-effective-output-v1`を維持する。

### 10.10 import / namespace互換契約

- `src/core/morph_name_sets.py`はwriter、wxPython、diagnosticsをimportしないleaf寄りのcore moduleとする。
- `src/vmd_writer/writer.py`はmodule-levelで`src.core`またはtop-level `core`をimportしない。
- `src/vmd_writer/__init__.py`から、import時にcoreを読むadapterやresolverをre-exportしない。adapterは明示module pathから読み込む。
- writer / adapter境界はProtocol、属性、primitive tuple、immutable valueを用い、`src.vmd_writer.writer`と`vmd_writer.writer`のclass identity一致を要求しない。
- fresh processでcore-first、writer-first、adapter-first、`src.*` / top-level mixed順序を検証する。既存日本語writer APIとprivate helper互換を同じprocessで確認する。
- `SUPPORTED_MORPHS`をruntime可変globalへ変更せず、既存日本語default callerのcompatibility constantとして維持する。

### 10.11 Block ownership

| Block | ownership | B1から渡す契約 |
|---|---|---|
| B2 | `MorphNameSet`、normalize-before-map順序、explicit writer / Preview / diagnostics adapter入力、import boundary | stable set ID、semantic key、default Japanese、fingerprint identity、fresh-process / mixed namespace互換 |
| B3 | `ModelProfile` DTO、JSON store、active profile / profile baseline用INI key、`/profiles.json` ignore | exact schema、mutation、atomic save、structural error、既存`active_preset_id`非変更 |
| B4 | resolver、startup、state、history、diagnostics | precedence、Apply / failure / identity reconciliation matrix |
| B5 | RightPane profile Select / Apply / CRUD | immutable request、Busy / revision、mutation非Apply |
| B6 | lifecycle、cross regression、docs | reset / rollback / stale result、package非同梱 |
| B7 | closeout | evidence、runtime data、MS26 deferral |

## 11. テスト方針

### 11.1 B1 plan作成時

- production codeとtest codeを変更しない。
- plan作成だけではpytest / GUI / buildを実行しない。
- Markdown構造、target path実在、`git diff --check`、runtime user data ignore、Git状態を確認する。

### 11.2 B1 contract pre-check実施時のread-only baseline

コマンドは一つずつ実行し、pass表示とprocess exit codeを別々に記録する。

1. import / mixed namespace / effective output identity

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b2_shape_adapters.py tests\test_ms21_b5_effective_output_identity.py tests\test_ms21_b7_import_boundaries.py tests\test_ms22_b2_import_boundaries.py
```

2. preset / settings contract

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b3_generation_presets.py tests\test_settings_store.py
```

3. output state / history / preset UI contract

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b4_generation_history.py tests\test_wx_ms22_b4_generation_state.py tests\test_wx_ms22_b5_preset_ui.py
```

4. lifecycle / rollback / reset contract

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b6_lifecycle_regression.py tests\test_wx_ms22_b6_lifecycle_regression.py tests\test_ms21_b7_analysis_rollback.py tests\test_ms19_b8_workspace_reset.py
```

5. Preview / diagnostics / writer contract

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_ms21_b3_preview_hit_test.py tests\test_ms20_b2_output_diagnostics.py tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b6_diagnostic_report.py tests\test_vmd_writer_grouping.py tests\test_vmd_writer_intervals.py tests\test_vmd_writer_zero_guard.py
```

6. document / runtime data gate

```powershell
git diff --check
```

`profiles.json`はB3未実装のためB1時点では生成しない。`/profiles.json` ignoreの実動確認はB3の実装・testへ渡す。

2026-08-12の初回実測では3番の19件がすべてpass表示後にprocess exit code 1となった。2026-08-13に対象8件を関数単位で各exit code 0まで切り分け、8件同時で`8 passed / exit code 0`、元の3ファイル同時で`19 passed / exit code 0`を再確認した。test code、production code、GUIは変更していない。固定再現しない非zero終了をpassへ読み替えず、今後同一commandで非zeroが再現して切り分け後も解消しない場合は、B1をContract Fixedにしない。

2026-08-15のP2/P3補正後baselineは次のとおりである。

| group | pass表示 | process exit code |
|---|---:|---:|
| import / mixed namespace / effective output identity | 15 passed | 0 |
| preset / settings | 29 passed | 0 |
| output state / history / preset UI | 19 passed | 0 |
| lifecycle / rollback / reset | 27 passed | 0 |
| Preview / diagnostics / writer | 156 passed | 0 |
| 合計 | 246 passed | 全command 0 |
| `git diff --check` | 問題なし | 0 |

2026-08-15の再チェックでは、3番commandの19件がpass表示後にexit code 1となった。実スプラッシュをwx main loopなしで生成・破棄する最小経路でもaccess violationを再現できたため、startup seam testだけにsplash asset missingのisolationを追加した。splashの表示・CallLater契約は専用testで維持している。補正後の同一19件commandは19 passed / exit code 0、`tests\test_wx_startup_splash.py`は3 passed / exit code 0となった。

fresh read-only B1 contract pre-checkでは、上記の関連baselineを現行worktreeで再実行し、合計249 passed、各process exit code 0を確認した。MS23 feature実装は開始していないため、`profiles.json`の生成やroot ignore追加はB3へ引き継ぐ。これはB1の未実装境界であり、今回のpre-checkの未解消問題ではない。

### 11.3 B2以降の新規test handoff

- schema v1、0 / 100 / 101件、duplicate、bool、non-finite、future schema
- `default_preset_id` lookupとdangling reference
- D1のbaseline / override /別preset Apply
- profile Apply直後のdefault baseline、別preset Apply後のruntime baseline ID保存、restart復元、Undo / Redo
- active profile中の既存`active_preset_id=None`と、no-profile復帰時のexact-match reconciliation
- profile-aware resolverがeffective settingsとpreset本体の不一致だけでruntime baseline IDをCustom化しないこと
- active profile mutation / delete guard
- active runtime baseline presetのvalue update / delete guardと、settings同値Renameのmetadata-only契約
- active profile中のglobal direct edit exact no-op / non-no-op拒否と、no-profile direct edit回帰
- upper limit差分によるanalysis invalidation / history clear
- output-only Apply / Undo / Redo identity reconciliation
- Japanese / Latin exact mappingとdefault Japanese
- semantic final normalization後に一回だけoutput nameをmappingし、frame number / value / count / orderを変えないこと
- writer既存引数省略時の日本語allow-list互換と、明示Latin allow-list以外の拒否
- writer / Preview / diagnosticsの同一resolved set
- core-first / writer-first / adapter-first / mixed namespaceのfresh-process importとclass identity非依存
- profile identity-only不変とmapped frame変更時のfingerprint差分
- startup / reset / broken JSON / stale worker / rollback
- commit前failureの完全不変と、commit後INI save failureのin-memory state / history保持
- root限定ignore、runtime file非stage、package非同梱

### 11.4 manual GUI / build

- B1はmanual GUI確認対象外である。
- B1はbuild対象外である。
- B5でprofile UI、B6でcross-lifecycle、B7でcloseout証拠を確認する。
- 実MMD確認はMS26へ維持する。

## 12. 受け入れ条件

- D1がadopted decisionとして全MS23文書で一致する。
- profile schema v1のfield、型、nullable、range、stable ID、reference、100件上限が表で確定する。
- built-in IDが`builtin:japanese-vowels` / `builtin:latin-vowels`に固定され、mappingがそれぞれ日本語5母音 / `A / I / U / E / O`として一致する。
- preset reference integrityとactive profile mutationの未回答decisionが残らない。
- `event adjustment > profile > preset > application`がoverlap field単位で説明される。
- `morph_upper_limit`がanalysis parameter、generation settings / morph-name setがoutput projectionとして分離される。
- active profile ID、runtime baseline ID、resolution statusの専用core state ownershipと、`GenerationState`のresolved morph-name set ID ownershipが一致する。
- cross-store検証とruntime mutation guardがB4、構造検証と永続化がB3に分離される。
- Apply、mutation、startup、reset、failure、Undo / Redoの状態遷移表が完成する。
- profile Applyは`default_preset_id`をruntime baselineへ初期化し、別preset Apply後はINIの`active_profile_baseline_preset_id`を再起動でも優先してprofile non-null overrideを再適用する。既存`active_preset_id`の意味を変えない。
- profileから参照中のuser preset deleteと、active user profileのvalue / set update・deleteがcommit前に拒否され、current state、history、store、INIを変更しない。
- active runtime baseline presetのvalue update / deleteがcommit前に拒否され、settings同値Renameだけがprofile / baseline identity、effective output、history、fingerprint、INIを変えないmetadata mutationとして成功する。
- active profile中のglobal generation settings / `morph_upper_limit` direct editはexact no-op以外をcommit前に拒否する。event adjustment、別preset Apply、no-profile時の既存direct edit契約を変更しない。
- startup unresolved profileはno-profile + JapaneseとINI数値保持へ正規化し、valid profileのruntime baselineだけがunresolvedな場合はprofile default presetへfallbackする。
- startupのID正規化またはruntime baseline fallbackで補正したIDをINIへ保存し、補正がないstartupでは保存しない。
- workspace resetはprofile、runtime baseline、resolved settings、resolved morph-name setを保持し、workspace固有状態だけをclearする。
- validation / resolution / commit前failureではcurrent stateを部分変更しない。commit後INI保存failureではin-memory state / historyをrollbackせず、既存save-disabled契約を維持する。
- no-profile時のJapanese defaultが全経路で維持される。
- semantic final normalization後にだけoutput nameをmappingし、日本語defaultのframe / VMD出力、長音、event adjustment、Preview hit-testを変えない。
- writer module-levelからcoreへ逆importせず、fresh-process import順序とmixed namespaceで循環・class identity依存がない。
- profile / preset / set説明identityだけではfingerprintが変わらず、mapped frame名変更では変わる。
- canonical payload構造とschema ID `ms21-effective-output-v1`を維持する。
- `/profiles.json`のroot限定ignore、非stage、package非同梱がB3 / B7契約へ割り当てられる。
- B2〜B6のcode / test / docs ownershipが重複なく割り当てられる。
- MS23 featureのproduction code、test code、GUI、dependency、packageをB1で変更していない。MS22 startup seam testのisolation補正は、実スプラッシュをsplash専用テストへ分離する回帰修正として別記録する。
- read-only baselineを実行した場合、pass表示とprocess exit codeを正確に記録する。
- baseline commandに非zero終了がある場合は切り分け、同一commandのexit code 0再確認または未解消記録なしにpass判定しない。
- B1実施後のP1 / P2 / P3がなく、material decisionがすべて採用または明示的にdeferされている。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| profile IDをoutput historyへ直接入れてanalysis stateと混ざる | selection、analysis parameter、output projectionを別ownershipにする |
| preset値をprofileへ複製して更新差分が不明になる | D1どおりstable referenceとoverrideだけを保存する |
| referenced preset削除でdangling referenceが生じる | D2どおり参照中deleteを拒否し、全store / stateを不変にする |
| active profile mutationで英字出力が暗黙に日本語へ戻る | D3どおりvalue / set updateとdeleteをinactive化まで拒否する |
| active runtime baseline preset更新後にIDとeffective値が不一致になる | D6どおりvalue update / deleteを拒否し、同値Renameだけmetadata mutationとして許可する |
| active profile中のdirect editでbaseline identityが実値を表さなくなる | D7どおりnon-no-op global direct editをcommit前拒否し、event adjustmentと別preset Applyを変更経路として維持する |
| missing referenceをapplication defaultへ黙って置換する | D4どおりApply拒否、startup no-profile + Japanese / INI数値保持、runtime baseline限定fallbackを使う |
| nullable継承がcurrent UI値へ依存して非決定論になる | application layer、preset layer、profile layerの入力をimmutable resolutionへ明示する |
| morph-name setをsemantic vowelへ混ぜる | semantic keyを維持し、output boundaryだけでmappingする |
| mapping後の英字keyをsemantic normalizationへ戻してprotected range / zero / open-stateを壊す | semantic final normalizationを先に完了し、output name mappingはwriter直前の一回だけにする |
| writerからcoreへ逆importして循環する | writer module-level core importを禁止し、明示adapter、fresh-process import順序testで固定する |
| `src.*` / top-level二重loadでDTO identityが分岐する | structural / primitive inputを使い、mixed namespace testでclass identity非依存を固定する |
| 別preset Apply後の再起動でprofile defaultへ戻る | current runtime baselineを専用INI `active_profile_baseline_preset_id`へ保存し、profile-aware resolverで優先する |
| profile override付きsettingsを既存preset resolverがCustom化する | preset単独resolverを変更せず、profile-aware resolverでbaseline identityとeffective settingsを別管理する |
| INI保存失敗をcommit前failureと同じrollback対象にする | in-memory commit / history保持とsave-disabled契約をMS22どおり維持する |
| profile identityやschema名変更でfingerprintが不要に変わる | D5どおりeffective writer frame名をcanonical identityにし、payload構造と`ms21-effective-output-v1`を維持する |
| `profiles.json`を追跡・bundleする | root限定ignore、temporary test store、package非同梱をB3 / B7へ固定する |
| B1でfuture MS25 abstractionを作る | shared resolver contractだけを記録し、batch専用実装を禁止する |
| 実MMD未確認をMS23完了へ混入する | MS26 deferredをB1 / B7で維持する |

## 14. Codex 実装時の注意

- commandは一つずつ実行し、parallel / pipeline / chained commandを使わない。
- B1はread-only pre-checkであり、MS23 featureのproduction code、test code、GUIを変更しない。既存MS22回帰のtest isolation補正は別修正として記録する。
- D1〜D7は採用済み事実として扱い、再度未確定へ戻さない。
- D1Aのruntime baselineとprofile defaultを混同せず、既存`active_preset_id`とpreset単独時のCustom正規化を変更しない。
- writer module-level core import、mapping後のsemantic normalization、runtime `SUPPORTED_MORPHS`書換えを行わない。
- pending decisionは一問一答で確認し、推奨案と理由を併記する。
- current code、test、live Gitを古い文書より優先する。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`をrepo root test fixtureにしない。
- user-owned diffをrestore、stage、commitしない。
- dependency、package、release、tag、merge、push、branch削除を行わない。
- passしていないtestをpassと記録しない。pass表示とprocess exit codeを分ける。
- GUIを実行していない場合、manual GUI verifiedと記録しない。
- P1 / P2 / P3を事実、推論、未確認に分けて記録する。

B1完了時は次の形式で報告する。

1. 確認したファイル
2. 変更したファイル
3. 固定したcontract / schema / state transition
4. ユーザー判断・採用案
5. 実行した検証
6. 検証結果とprocess exit code
7. P1 / P2 / P3
8. 仕様からの逸脱
9. 残課題
10. B2 / B3 Implementation Planへの引き継ぎ

## 15. 決定台帳と次工程

| ID | 決定事項 | 状態 | 根拠 / 次の確認 |
|---|---|---|---|
| D1 | `default_preset_id`をstable referenceとし、preset baseline + profile non-null overrideとする | Adopted 2026-08-12 | ユーザー承認済み |
| D1A | profile Apply時はdefault baseline、別preset Apply後は専用INI `active_profile_baseline_preset_id`をruntime baselineとして再起動でも優先する | Adopted 2026-08-13 | active profile中は既存`active_preset_id=None`。preset単独resolverは変更しない |
| D2 | profileから参照中のuser preset deleteを拒否する | Adopted 2026-08-13 | dangling referenceを通常UI操作で作らないため |
| D3 | active profileのvalue / set updateとdeleteを、inactive化まで拒否する | Adopted 2026-08-13 | current English outputの暗黙Japanese化を避けるため |
| D4 | startup unresolved profileはno-profile + Japanese / INI数値保持。valid profileのruntime baselineだけがunresolvedならprofile defaultへfallbackする | Adopted 2026-08-13 | partial profile applyと不要な数値初期化を避けるため |
| D5 | fingerprint payload構造を変えず`ms21-effective-output-v1`を維持する | Adopted 2026-08-13 | mapped frame名が既にidentityへ入るため |
| D6 | active runtime baseline presetのvalue update / deleteを拒否し、settings同値Renameだけ許可する | Adopted 2026-08-13 | baseline IDとcurrent effective settingsの不一致を作らないため |
| D7 | active profile中のnon-no-op global direct editを拒否する | Adopted 2026-08-13 | profile / baseline identityを暗黙解除せず、no-profile時のMS22 direct edit契約を維持するため |
| S1 | profile schema v1はexact key set、既存preset準拠のdisplay name / ID validation、nullable inheritance、required `default_preset_id`とする | Adopted 2026-08-15 | 現行`src/core/generation_presets.py`の実装済み契約とD1を基準にした推奨案 |
| S2 | built-in IDを`builtin:japanese-vowels` / `builtin:latin-vowels`に固定し、mappingを日本語5母音 / `A / I / U / E / O`とする | Adopted 2026-08-15 | persisted schemaのstable referenceと既存日本語defaultを両立するため |
| S3 | active profile ID、runtime baseline ID、resolution statusは専用core state、resolved morph-name set IDは`GenerationState`が所有する | Adopted 2026-08-15 | profile identityをbase-bound historyへ混在させず、output-only projectionを保持するため |
| S4 | cross-store resolutionとruntime mutation guardはB4、構造検証と永続化はB3が所有する | Adopted 2026-08-15 | persistence層とruntime resolverの責務を分離するため |
| S5 | workspace resetではprofile、runtime baseline、resolved settings、resolved morph-name setを保持する | Adopted 2026-08-15 | MS22のgeneration settings / active preset保持契約を維持するため |
| S6 | `morph_upper_limit`はprofileのnullable overrideとし、resolved値をanalysis parameterへ渡す | Adopted 2026-08-15 | Roadmapのmodel-specific設定を実現しつつoutput-only stateへ混在させないため |
| S7 | startupでID補正が発生した場合だけ補正後IDをINIへ保存し、数値設定を保持する | Adopted 2026-08-15 | invalid stateの再発を防ぎ、既存数値設定を壊さないため |

2026-08-15の一問一答でS2〜S7を採用した。これにより、built-in ID、state ownership、cross-store責務、workspace reset、`morph_upper_limit`のprofile ownership、startup補正保存のmaterial decisionは解消済みである。exact class名、private helper名、error code名はB4 Implementation Planで固定する実装詳細として明示的にdeferする。

2026-08-13に、import / namespace、normalize-before-map、runtime preset baseline、commit前後failure、baseline非zero終了のP2 5件を計画上で補正した。対象wx baselineは切り分け後に元の19件commandでもexit code 0を再確認し、test codeは変更していない。同日、ユーザーはD2〜D5をすべて推奨案Aで採用した。その後のB1実装前チェックで、active runtime baseline preset mutationとactive profile中global direct editのP2 2件を検出し、ユーザーの解消指示に基づくD6 / D7で補正した。2026-08-15の再チェックではstartup seam testが実スプラッシュを生成していたためaccess violationによるexit code 1を再現し、splash専用testとの責務分離としてtest isolationを補正した。同一19件commandはexit code 0へ復帰し、P3のlive Git記述、read-only code対象、P1/P2/P3 gate表記も同期した。D1〜D7とMS22のpreset単独時Custom正規化、no-profile direct edit、history / analysis invalidation契約は維持している。続くfresh read-only B1 contract pre-checkでschema、state ownership、failure matrixを現行code / testへ再照合し、249 passed、全command process exit code 0、P1 / P2 / P3なしを確認したため、B1をCompleted / Contract Fixedと判定した。B2 / B3のproduction implementationは、それぞれのImplementation Plan作成・レビュー後に別途開始する。

2026-08-15に、現行`src/core/generation_presets.py`との照合で判明したschema表の未確定表現を補正した。profile root / entry / `generation_overrides`のunknown key拒否、display nameのtrim後1〜100文字・制御文字 / 改行拒否、canonical lowercase UUID、required `default_preset_id`、missing referenceのresolution errorをS1として採用した。これはP2の文書上の未確定契約を解消するための計画修正であり、production code、test code、GUI、runtime user dataは変更していない。続くfresh read-only contract pre-checkで現行code / testとの整合、249 passed、全command process exit code 0、P1 / P2 / P3なしを確認したため、B1をCompleted / Contract Fixedへ同期した。
