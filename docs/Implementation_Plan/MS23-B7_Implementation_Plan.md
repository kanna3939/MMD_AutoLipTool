# MS23-B7 Implementation Plan

## 1. 文書情報

- 対象Milestone: `MS23 Model Profiles / Built-in Morph Name Sets`
- 対象Block: `MS23-B7 Closeout Audit`
- 作成日: 2026-08-20
- 計画作成時branch: `feature/MS23-implementation`
- 計画作成前HEAD: `5349ea4 Implement MS23-B6 cross regression`
- 直接依存: MS23-B1からB6までの完了証拠。B4後のwx teardown修正であるMS23-B4Bを含む
- 文書ステータス: **Closeout Audit Executed / A**
- 監査実施日: 2026-08-20
- 監査時HEAD: `b843d24 Document MS23-B7 closeout plan`
- 本Blockの性質: 新機能実装ではなく、B1からB6の到達状態をcurrent repositoryへ再照合するCloseout監査
- 次の正規handoff候補: MS23をAまたは明示的なBでcloseoutした後のMS24 Implementation Plan策定
- 継続する未検証事項: 実MMDでのVMD / WAV読込・再生・リップ同期はMS26へdeferred

本書作成時に変更してよいファイルは本書だけである。production code、test code、GUI、runtime user data、
package / build設定、他文書は変更しない。stage、commit、push、merge、tag、branch操作も行わない。

## 2. 背景

MS22はCloseout Aで完了している。MS23は、既存の日本語5母音イベントを維持したまま、モデル別の数値設定と
組み込みモーフ名セットを再利用できるようにするMilestoneである。英字セットは英語音声対応ではなく、既存の
semantic vowel `あ / い / う / え / お`をVMD出力境界で`A / I / U / E / O`へ対応付ける命名セットである。

current repositoryで確認したMS23の到達状態は次のとおりである。

| Block | current state | 主な完了内容 |
| --- | --- | --- |
| B1 | Completed / Contract Fixed | D1〜D7、S1〜S7、schema、precedence、failure、history、startup、mutation guardを固定 |
| B2 | Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) | built-in morph-name set、normalize後の一回mapping、writer / Preview / diagnostics境界 |
| B3 | Implemented / Automated Verification Passed / Manual GUI Not Required | strict version 1 `profiles.json`、最大100件、atomic CRUD、INI identity |
| B4 | Implemented / Dedicated・Related Automated Verification Passed | profile resolver、state、history、startup、guard、diagnostics / report。B4終了時full suiteのwx teardown非zero終了はB4Bへ分離 |
| B4B | Implemented / Automated Verification Passed / Manual GUI Not Required | wx test ownership / teardownを修正し、wx aggregateとfull suiteを連続exit code 0へ復帰 |
| B5 | Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) | profile Select / Apply、CRUD、Busy / stale、profile / preset cross-sync |
| B6 | Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) | 横断回帰、Redo profile再投影repair、利用者文書・仕様・routing同期 |

HEAD `5349ea4`のB6記録では、B6専用12件、B2〜B5基盤56件＋31 subtests、wx / B4B / B5 / 長音30件、
diagnostics / writer / VMD / Preview 93件、lifecycle 46件＋7 subtests、wx aggregate 136件を2回、
full suite 797件＋57 subtestsを2回、`compileall src tests`、`git diff --check`がprocess exit code 0である。
2026-08-20には、profile Apply後のUndo / Redoを含む限定GUI確認が通過し問題なしとユーザーから報告されている。
これはユーザー報告であり、Codex自身のmanual GUI実行ではない。

B4実装時のfull suiteは`771 passed, 57 subtests passed`まで完走した一方、process exit code 1だった。
この反証は履歴から消さない。B4Bで原因をwx test lifecycleへ切り分け、wx aggregate 129件を2回、full suite
773件＋57 subtestsを2回、それぞれprocess exit code 0で確認した。その後のB5 / B6 full suiteもexit code 0である。
B7では「当時のBlock完了証拠」と「current HEADでの再検証」を別々に台帳化し、後続の成功で過去の事実を上書きしない。

実MMDでのVMD / WAV読込・再生・リップ同期はまだ確認されていない。これは既定どおりMS26の責務であり、
MS23 Closeout Aを妨げる未実装ではないが、MS23で検証済みと誤記してはならない。

## 3. 目的

1. B1からB6およびB4Bの要求、採用済みdecision、実装commit、コード、test、ユーザー報告、文書を一つの証拠台帳へ統合する。
2. profile persistence、built-in morph mapping、resolution、state / history、guard、failure、GUI、lifecycleの横断契約をcurrent HEADで再検証する。
3. 自動testのpass表示、failure / error、fatal trace、process exit codeを分離して記録する。
4. GUI evidenceの実施主体、対象、日付を記録し、ユーザー報告とCodex実行を混同しない。
5. runtime user data、dependency、package、license、network、Qt凍結の境界を監査する。
6. findingをP1 / P2 / P3へ分類し、A / B / CのCloseout判定を根拠付きで確定する。
7. MS24への次Milestone handoff条件と、MS26へ残すactual-MMD未検証事項を明確にする。

## 4. In Scope

### 4.1 要求・実装証拠監査

- B1で固定したD1〜D7、S1〜S7、precedence、failure matrix、history / persistence契約
- `MorphNameSet`のstable ID、表示名、ordered output names、Japanese default、Latin built-in set
- semantic final normalization後に一度だけoutput nameをmappingするwriter / Preview境界
- strict version 1 `profiles.json`、初期上限100件、load-before-mutation、fail-closed load、atomic replace
- profile `default_preset_id`のstable reference、nullable override、runtime baseline preset
- `event adjustment > model profile > preset > application default`のfield単位resolution
- `morph_upper_limit`変更とoutput-only変更のanalysis / history分類
- startup fallback、workspace reset、analysis rollback、stale / duplicate callback、Undo / Redo
- active profile、active runtime baseline、参照中preset、global direct editのcommit前guard
- commit前failureの完全不変と、commit後INI save failureのin-memory commit / history保持
- profile Select / Apply分離、Create / Update / Rename / Delete、Busy / dirty / stale guard
- writer、Preview、diagnostics、diagnostic report、fingerprintのresolved morph-name contract一致
- TEXTあり / voice-only、empty、invalid、long-vowel hold / decay、既存日本語defaultの回帰
- B4Bのwx App / Frame / Controller / timer / pending callback teardownとprocess exit stability

### 4.2 自動検証・manual evidence監査

- B1からB6およびB4BのBlock完了時test evidence
- MS23 direct regression
- MS21 / MS22のstate、history、preset、long-vowel、Preview / writer回帰
- MS17 / MS19 / MS20のinput、voice-only、diagnostics、save、reset、late worker回帰
- wx aggregate連続2回、full suite連続2回
- `compileall src tests`、`git diff --check`
- B2、B5、B6のユーザー報告によるGUI evidence
- B1、B3、B4Bのmanual GUI非対象、B4のGUI確認をB5へ委譲した境界

### 4.3 文書・repository境界監査

- B1〜B6 / B4B Implementation PlanとMS23 Block Breakdown
- `docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md`
- `README.md`、`readme_mmdautolip.txt`
- Pipeline / VMD / GUI / Error仕様
- `docs/repo_milestone.md`、`docs/Version_Control.md`のCloseout追記位置
- `.gitignore`、tracked file一覧、runtime pathのroot限定ignore
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、Release Package Manifest
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`

### 4.4 Closeout判定・handoff

- P1 / P2 / P3分類とfinding ledger
- A / B / C判定
- A / Bの場合のCloseout文書同期
- Cの場合のCloseout延期、repair / evidence追加条件
- MS24 Implementation Plan策定へ進める条件
- MS26 Actual-MMD Verificationへの明示的handoff

## 5. Out of Scope

- 新機能、production code、test code、GUI、schema、public formatの追加・変更
- test削除、skip / xfail追加、assertionやfixtureの弱化によるfailure回避
- PMX / PMD import、モデルファイル解析
- 任意モーフ名mapping、ユーザー定義モーフセット、追加表情モーフ
- 英語ASR、英語phoneme処理、他ASR backend
- MS24 Whisper Model Selectionの実装
- MS25 MMD Delivery Package Exportの実装、batch専用DTO / adapterの先行追加
- MS26 Actual MMD Closeoutの実施または完了宣言
- MS27 packaging / release readinessの実施
- PyInstaller build、SmokeLaunch、ZIP / installer作成、package生成、version変更、release公開
- dependency追加・更新、binary追加、license方針変更
- stage、commit、push、merge、tag、branch作成・切替・削除
- network / cloud ASR、外部音声送信、telemetry、background通信
- Whisper model、FFmpegその他binaryの暗黙または自動download
- Qt / PySide6 / PyQtの復活、wxPython以外へのGUI移行
- root runtime user dataの内容確認、fixture化、作成、変更、初期化、削除、stage、package同梱

B7監査でproduction / test修正が必要なP1 / P2を発見しても、その場で修正してCloseoutへ混ぜない。
原因、影響、owner、推奨repair、再検証条件を記録し、別途承認されたrepairへ分離する。

## 6. 前提条件

### 6.1 Git / environment

- B7 plan作成前のlive stateはbranch `feature/MS23-implementation`、HEAD `5349ea4`、worktree cleanである。
- 本書作成後は本書だけがuncommitted changeとなる想定であり、Closeout実施結果ではない。
- B7実施前に本planがレビュー済みのbaselineとして固定され、監査開始時のbranch、HEAD、worktree、upstreamを再確認する。
- Closeout監査中の変更対象は、別途B7実施権限で許可されたcloseout文書だけとする。
- Python 3.11以上、repo-local `.venv`、Windows PowerShell、wxPython主系を維持する。
- repository commandは並列化・pipeline・連結をせず、一つずつ実行して結果を確認する。

### 6.2 既存完了証拠の扱い

- B6 automated validationとユーザーGUI報告は、committed plan / routingに記録されたBlock完了時証拠である。
- 本plan作成ではpytest、GUI、buildを再実行していない。B7 Closeout判定は§11のcurrent revalidation後にだけ行う。
- B4 full suiteのhistorical exit code 1と、B4B以後のexit code 0を別証拠として保持する。
- ユーザーGUI報告は報告された範囲に限定し、Codex自身のmanual executionへ読み替えない。
- B7でproduct behaviorを変更しない限り、B2 / B5 / B6のユーザー報告を範囲限定で再利用できる。
- repairがGUIまたはuser-visible behaviorへ影響した場合は、repair後に対象限定の再確認が必要である。
- 実MMD未確認は`Deferred-by-design: MS26`であり、GUI確認済みへ統合しない。

### 6.3 計画作成時のread-only baseline

本plan作成時にcurrent repositoryをread-onlyで確認した結果は次のとおりである。

| 対象 | 確認結果 | Closeout上の意味 |
| --- | --- | --- |
| Git | `feature/MS23-implementation` / `5349ea4` / plan作成前worktree clean | B7 plan作成基準 |
| runtime ignore | `/profiles.json`、`/presets.json`、`/MMD_AutoLipTool.ini`のroot限定ruleを確認 | path-level境界のみ。内容・存在は監査していない |
| tracked runtime paths | 3 pathとも`git ls-files --`出力なし | source tracking対象外 |
| package / dependency / license diff | MS22 Closeout Aの`4e85682`からHEADまで対象file差分なし | B7でbuildを実行しない根拠。B7実施時に再確認する |
| package static search | spec / build / manifestに3 runtime filenameの記載なし | package default data非同梱のplan baseline |
| network / Qt static search | `src`と`pyproject.toml`にPySide / PyQt、HTTP client、socket、auto-download該当なし | MS23追加による境界逸脱なしのplan baseline |

`rg`のno-matchによるexit code 1は、上表の静的検索では期待結果である。pytestやbuildのexit code 1と同じ意味で扱わない。

## 7. 対象ファイル・証拠

### 7.1 source-of-truth documents

| 優先 | 正本 / evidence | 用途 |
| --- | --- | --- |
| 1 | live Git state、current code、current tests、current command results | current behaviorとrepository状態の最終根拠 |
| 2 | `MS23-B1`〜`MS23-B6`、`MS23-B4B` Implementation Plan | 採用済み契約、Block scope、Block完了時証拠 |
| 3 | `MS23_Block_Breakdown.md`、Index、Roadmap | current milestone status、依存順、MS24 / MS26境界 |
| 4 | README、配布用readme、Pipeline / VMD / GUI / Error仕様 | user-visible behaviorとデータ・失敗契約 |
| 5 | Git commit / diff | 実装範囲、dependency / package / license差分 |
| 6 | 日付と範囲が記録されたユーザー報告 | user-performed manual GUI evidenceのみ |
| 7 | `repo_milestone.md`、`Version_Control.md` | Closeout後の履歴。current stateの単独根拠にしない |

文書とcurrent code / testが矛盾する場合は、矛盾をfinding化する。historical記録をcurrent wordingへ無言で書き換えず、
時点を保持したままcurrent statusだけを同期する。

### 7.2 read-only implementation evidence

- morph set: `src/core/morph_name_sets.py`
- profile persistence: `src/core/model_profiles.py`、`src/core/settings_store.py`
- resolution / guard: `src/core/model_profile_state.py`
- state / history: `src/core/output_edit_state.py`、`src/core/event_adjustment_history.py`、`src/gui_wx/ui_state.py`
- semantic / writer: `src/core/pipeline.py`、`src/vmd_writer/effective_shape_adapter.py`、`src/vmd_writer/writer.py`
- Preview: `src/core/preview_transform.py`、`src/gui_wx/preview_panel.py`
- diagnostics / report: `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、`src/gui_wx/output_diagnostics_adapter.py`
- startup / rollback / lifecycle: `src/gui_wx/app.py`、`src/gui_wx/analysis_rollback.py`、`src/gui_wx/app_controller.py`
- GUI: `src/gui_wx/main_frame.py`、`src/gui_wx/right_pane.py`
- wx test lifecycle: `tests/helpers.py`

### 7.3 direct test evidence

- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b2_import_boundaries.py`
- `tests/test_ms23_b3_model_profiles.py`
- `tests/test_ms23_b4_model_profile_state.py`
- `tests/test_ms23_b4_profile_history.py`
- `tests/test_ms23_b4_settings_save.py`
- `tests/test_ms23_b4b_wx_teardown.py`
- `tests/test_ms23_b5_model_profile_controller.py`
- `tests/test_wx_ms23_b4_profile_runtime.py`
- `tests/test_wx_ms23_b5_model_profile_ui.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`

B7専用testは新設しない。既存testだけでは証明できないmaterial contract gapを発見した場合はP2としてrepairへ戻す。

### 7.4 documentation / repository / package evidence

- `README.md`、`readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `.gitignore`
- `pyproject.toml`
- `MMD_AutoLipTool.spec`
- `build.ps1`
- `docs/Release_Package_Manifest.md`
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`

### 7.5 B7実施時の文書変更候補

B7 Closeoutの実施が別途承認された場合に限り、次を結果同期対象とする。

- 本書のevidence ledger、finding、実測、判定
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`、`docs/Version_Control.md`
- README / 配布用readme / Pipeline / VMD / GUI / Error仕様はcurrent behaviorとの差異が見つかった場合だけ

A / B / C判定前にmilestone historyを完了扱いへ変更しない。production code、test code、GUI、runtime data、
package / build設定はB7の変更対象にしない。

## 8. 監査方針

### 8.1 Evidence-first ledger

各Blockについて、次を別列で記録する。

1. 要求・契約
2. 実装またはcontract固定commit
3. Block完了時の自動証拠
4. manual evidenceの主体・日付・範囲
5. 文書同期
6. B7 current revalidation
7. current finding、owner、再確認条件

後続Blockのfull suite成功だけで前段Block固有契約を証明済みとしない。逆に、B4当時のwx teardown exit 1だけで、
B4B以後もcurrent failureが残るとは扱わない。両方の時点と解消chainを記録する。

### 8.2 Evidence status

次のstatus語を厳密に使い分ける。

- `Contract Fixed`: 契約・decision・pre-checkを固定したが、feature実装を意味しない
- `Implemented`: current codeに実装が存在する
- `Automated Verification Passed`: 記録対象commandがpass表示かつprocess exit code 0
- `Manual GUI Verification Passed (User Report)`: ユーザーが報告した項目だけが通過
- `Manual GUI Not Required`: 当該BlockがUI非依存またはtest infrastructureのみ
- `Manual GUI Deferred`: 後続Blockのuser-facing flowへ委譲
- `Actual-MMD Verification Deferred to MS26`: 実MMD未確認
- `Unknown / Not Revalidated`: current auditで再確認していない

### 8.3 Finding分類

- P1: データ破壊、security、主要VMD出力誤り、runtime user data破壊、Closeoutを直ちに停止すべき問題
- P2: A判定または次Milestone開始前に解消すべき要求・実装・test・文書・repository・package境界の問題
- P3: user-visible behaviorを変えない記録・表現・軽微な保守性問題

同じ根因を複数findingへ重複計上しない。historical resolved findingとcurrent unresolved findingを分離する。
finding IDは`MS23-B7-F-001`から連番とし、severity、status、evidence、影響、owner、措置、再検証条件を持たせる。

### 8.4 unresolved findingの扱い

- P1 / P2を検出した時点でA判定作業を停止する。
- production / test / repository repairをB7文書同期へ混ぜない。
- repair scope、変更権限、acceptance、対象回帰、full suite要否を別作業で固定する。
- repair後はStep 0から再開し、影響groupとfull suiteを再実行する。
- 文書だけのP3は、B7実施権限の範囲で最小同期できる。未解消なら影響、owner、期限または再確認条件を記録する。
- 既定どおりMS26へdeferredされたactual-MMD確認はfindingではない。ただしdeferred記録の欠落はP2またはP3として分類する。

### 8.5 A / B / C Closeout判定

| 判定 | 条件 | handoff |
| --- | --- | --- |
| A | open P1 / P2なし。主要要求、current automated verification、manual evidence境界、文書、runtime / package / dependency / network / Qt境界が揃う。P3は解消済み、または影響・owner・再確認条件が明記されている | MS23完了。MS24 Implementation Plan策定へ進行可能。MS24実装は開始しない。MS26 actual-MMD deferredを維持 |
| B | P1なし。残存事項と影響、owner、再検証条件を提示し、ユーザーが影響込みで明示的に条件付きCloseoutを受け入れた場合だけ | 条件付きhandoff。残存事項がMS24前提を壊す場合はMS24へ進めずrepairを優先。MS26 deferredを維持 |
| C | P1、未受入れP2、主要要求の未実装・未検証、mandatory command failure / non-zero、runtime data追跡・同梱、監査不能のいずれか | Closeout延期。repairまたは追加証拠へ戻す。MS24を開始しない |

actual-MMD未確認だけを理由にB / Cへ落とさない。これはMS23の事前定義済みOut of Scopeであり、MS26の受け入れ条件である。

## 9. 詳細ステップ

### Step 0: Closeout開始gate

- `git status`、`git branch`、`git log --oneline -n 10`を一つずつ実行する。
- branch、HEAD、B7 plan baseline、B1〜B6 / B4B commit chain、worktreeを確認する。
- pre-existing user changeがあれば、対象とscopeを記録して保護する。
- B7 plan未レビュー、未解決P1 / P2、意図不明のcode / test / runtime差分があれば監査を開始しない。
- MS22 Closeout Aをcurrent MS23 auditの都合で未完了へ戻さない。

### Step 1: source-of-truth mapとevidence ledger

- §7の正本をcurrent pathで再確認する。
- §15の各Block行へ要求、commit、Block完了時証拠、manual evidence、docsを記録する。
- Git commitとplanのstatusが一致するか確認する。
- B4 -> B4B -> B5 -> B6のwx exit stability解消chainを時系列で保持する。
- plan creation evidenceとB7 current audit evidenceを別欄に置く。

### Step 2: requirement crosswalk

- Roadmap MS23 §10.2〜10.5とBlock Breakdownの受け入れ条件を列挙する。
- 各要求へcode owner、direct test、user-facing docs、manual evidenceまたはmanual非対象理由を対応付ける。
- PMX / PMD、任意mapping、user-defined set、英語ASR、MS24〜MS27を実装済みと誤記していないか確認する。
- MS25が再利用するresolver境界だけが文書化され、batch実装を先行していないことを確認する。

### Step 3: implementation / data-flow監査

- semantic vowel -> final normalized effective frames -> resolved output name -> writer / Previewの順序を確認する。
- `profiles.json` -> profile resolution -> `GenerationState` / `ModelProfileState` -> history -> diagnostics / reportの連鎖を確認する。
- profile / preset / event adjustmentのfield ownershipとprecedenceを確認する。
- upper差分、output-only差分、identity-only差分のanalysis / history / save分類を確認する。
- startup、restart、Undo / Redo、reset、rollback、stale result、failureの保持・破棄規則を確認する。
- fingerprintに説明identityを混ぜず、effective writer morph frame name差分だけが反映されることを確認する。

### Step 4: automated revalidation

- §11のcommandを小さいgroupから一つずつ実行する。
- command、開始時HEAD、表示summary、failure / error、fatal trace、process exit codeを記録する。
- wx aggregateとfull suiteは各2回連続でexit code 0を要求する。
- `N passed`表示でもprocess exit codeがnon-zeroなら未合格とする。
- B7専用test追加が必要になった場合はP2としてrepairへ戻す。

### Step 5: manual evidence監査

- B2、B5、B6のユーザー報告について、日付、対象Block、確認範囲、結果を台帳へ記録する。
- B1、B3、B4Bがmanual GUI非対象である理由を維持する。
- B4のprofile UI manual確認がB5へ委譲され、B5でuser-facing flowとして確認されたことを記録する。
- B6の報告はprofile Apply後のUndo / Redoを含む限定範囲であり、actual-MMD evidenceではないと明記する。
- CodexがGUIを実行していない場合は`Codex manual GUI: not executed`と記録する。

### Step 6: runtime user data / repository監査

- `git check-ignore -v -- profiles.json presets.json MMD_AutoLipTool.ini`でroot限定ignoreを確認する。
- `git ls-files -- profiles.json presets.json MMD_AutoLipTool.ini`が出力なしであることを確認する。
- 3 fileの内容を読まない。fixture化、hash比較、修復、作成、変更、削除、stageをしない。
- testがtemporary directoryのstoreを使い、repo root runtime fileへ書かないことをtest codeと結果で確認する。
- `profiles.json`をspec、build、manifest、配布物のdefault dataへ含めていないことを静的確認する。

### Step 7: dependency / package / network / Qt監査

- MS22 Closeout Aの`4e85682`からB7 audit HEADまで、dependency / package / build / license file差分を確認する。
- `pyproject.toml`にMS23由来のdependency追加がないことを確認する。
- `src`にPySide / PyQt、HTTP client、socket、cloud処理、auto-downloadを導入していないことを確認する。
- 差分や該当を見つけた場合はP2以上として停止し、B7内でdependency、build、license方針を変更しない。
- 対象差分がない場合、build / SmokeLaunch / package生成を実行しない。

### Step 8: documents監査

- README / 配布用readmeのprofile操作、日本語 / Latin、上限、active mutation lock、failure説明をcurrent behaviorと照合する。
- Pipeline / VMD / GUI / Error仕様のpersistence、mapping、state、guard、fallbackをcode / testsと照合する。
- Block Breakdown、Index、RoadmapのB1〜B6 / B4B status、test値、manual主体、MS26 deferredを照合する。
- historical時点の記録を保持し、current statusだけを同期する。
- A / B / C判定前に`repo_milestone.md`と`Version_Control.md`をMS23完了へ更新しない。

### Step 9: finding gateとCloseout判定

- findingをP1 / P2 / P3へ重複なく分類する。
- P1 / P2があれば影響、owner、repair、再検証条件を記録し、A判定を停止する。
- P3は解消または明示handoffする。
- mandatory evidenceが揃った場合だけA候補とする。
- Bはユーザーの明示受入れを記録した場合だけ確定する。
- CではMS24へ進行可能と記載しない。

### Step 10: Closeout文書同期

- 本書§15へcurrent実測、finding、A / B / C判定を記録する。
- Block Breakdown、Index、Roadmapへ同一の日付、HEAD、test結果、manual主体、判定、次工程を同期する。
- A / Bの場合だけmilestone / version historyへCloseout記録を追記する。
- Cの場合はCloseout延期とrepair / evidence条件だけをcurrent statusへ反映し、完了履歴を作らない。
- README / 仕様はcurrent behaviorとの差異がある場合だけ同期し、挙動変更は行わない。

### Step 11: 最終自己監査

- user request、current Git、contrary evidence、test結果、finding、判定、未検証事項を再照合する。
- 変更fileが承認済みcloseout文書だけであることを確認する。
- `git diff --check`、変更file一覧、最終`git status`を確認する。
- production / test / GUI / runtime / package / dependencyへ意図しない差分がないことを確認する。
- stage / commit / push等は行わず、別途明示承認へ残す。

## 10. 状態遷移 / データ契約

### 10.1 Closeout状態遷移

```text
B1 Contract Fixed
  + B2-B6 Implemented / Automated Evidence
  + B4B wx teardown repair / exit stability
  + User GUI Reports for B2 / B5 / B6
  -> B7 Plan Created
  -> B7 Start Gate
      -> gate failure: audit not started / repair or clarification
      -> gate pass: evidence collection
  -> Current Revalidation
  -> Finding Gate
      -> A: MS23 Closeout / MS24 planning handoff / MS26 actual-MMD deferred
      -> B: user-accepted residual / conditional handoff / MS26 deferred
      -> C: closeout deferred / repair or additional evidence / no MS24 start
```

### 10.2 Evidence record contract

各実行記録は少なくとも次を持つ。

| field | contract |
| --- | --- |
| `source_commit` | 実行時HEAD |
| `command` | 実際に一つずつ実行したcommand |
| `display_summary` | passed / failed / errors / subtests / deselected |
| `fatal_evidence` | access violation、fatal trace、異常終了の有無 |
| `process_exit_code` | summaryとは別に記録 |
| `executor` | Codex、test runner、user reportの別 |
| `scope` | 何を証明し、何を証明しないか |
| `timestamp` | 実行日または報告日 |

### 10.3 product data contract不変条件

- semantic vowelは`あ / い / う / え / お`のまま保持し、final normalization後にoutput nameだけを一回mappingする。
- no-profileはJapanese built-in set、profileはJapaneseまたはLatin built-in setだけを使う。
- arbitrary mapping、user-defined set、additional expressionsは存在しない。
- profile precedenceは`event adjustment > model profile > preset > application default`である。
- profile `default_preset_id`はstable referenceであり、preset値をprofileへ複製しない。
- active profile中は`active_preset_id=None`を維持し、runtime baselineは専用INI identityで復元する。
- `morph_upper_limit`はanalysis-affecting、hold / softness / long-vowel mode / morph-name setはoutput分類に従う。
- commit前failureは完全不変、commit後INI save failureはcommitted in-memory state / historyをrollbackしない。
- VMD format、30fps、frame number / value / count / order、既存audio三役を変更しない。

### 10.4 root runtime user-data contract

| file | runtime role | B7で許可する確認 | 禁止事項 |
| --- | --- | --- | --- |
| `profiles.json` | user model profiles、schema version 1、最大100件 | root ignore、Git非追跡、package非同梱のpath-level確認 | 内容読取、fixture化、作成、変更、削除、stage、package同梱 |
| `presets.json` | user generation presets | root ignore、Git非追跡、package非同梱のpath-level確認 | 内容読取、fixture化、作成、変更、削除、stage、package同梱 |
| `MMD_AutoLipTool.ini` | active IDsとuser settings | root ignore、Git非追跡、package非同梱のpath-level確認 | 内容読取、fixture化、作成、変更、削除、stage、package同梱 |

local fileの有無や値をCloseout証拠に使わない。B7はGit / package境界だけを確認し、ユーザー所有データを操作しない。

### 10.5 milestone boundary

- MS24: B7 A / B後にImplementation Plan策定候補。Whisper model選択をB7で実装しない。
- MS25: B7ではresolver再利用境界の存在だけを確認し、一括出力を実装しない。
- MS26: actual MMDでVMD / WAV読込・再生・リップ同期を確認する唯一の現行owner。
- MS27: build、package、license、release readinessのowner。B7では静的な非変更監査だけを行う。

## 11. テスト・検証方針

### 11.1 実行原則

- 最小direct groupから関連回帰、wx aggregate、full suiteへ進む。
- commandは一つずつ実行し、同時実行、pipeline、command連結をしない。
- pass表示、failure / error、fatal trace、process exit codeを分離する。
- pytestでpass表示後にexit codeがnon-zeroなら未合格とし、B4時点のknown historyで自動的に免責しない。
- wx aggregateとfull suiteは2回連続でprocess exit code 0を要求する。
- full suite件数がB6 baselineの797件＋57 subtestsと異なる場合、実行HEADとintervening diffから理由を説明する。
- test codeを変更せず、root runtime user dataを使わず、temporary directoryだけを使用する。

### 11.2 実行順

1. MS23 direct regression
2. MS21 / MS22 state・history・preset・long-vowel回帰
3. diagnostics / report / Preview / writer / VMD回帰
4. MS17 / MS19 / MS20 lifecycle・voice-only・reset・stale回帰
5. wx aggregate 1回目
6. wx aggregate 2回目
7. full suite 1回目
8. full suite 2回目
9. `compileall src tests`
10. runtime ignore / tracked / package / dependency / network / Qtのread-only確認
11. `git diff --check`

### 11.3 代表command

実行前に全pathの存在を再確認する。各行は独立したcommandとして実行する。

```powershell
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms23_b2_morph_name_sets.py tests\test_ms23_b2_morph_name_adapters.py tests\test_ms23_b2_import_boundaries.py tests\test_ms23_b3_model_profiles.py tests\test_ms23_b4_model_profile_state.py tests\test_ms23_b4_profile_history.py tests\test_ms23_b4_settings_save.py tests\test_ms23_b4b_wx_teardown.py tests\test_ms23_b5_model_profile_controller.py tests\test_wx_ms23_b4_profile_runtime.py tests\test_wx_ms23_b5_model_profile_ui.py tests\test_ms23_b6_model_profile_lifecycle.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms22_b2_long_vowel_resolver.py tests\test_ms22_b4_generation_history.py tests\test_wx_ms22_b4_generation_state.py tests\test_wx_ms22_b5_preset_ui.py tests\test_wx_ms22_b5_long_vowel_override.py tests\test_ms22_b6_lifecycle_regression.py tests\test_wx_ms22_b6_lifecycle_regression.py tests\test_ms21_b5_effective_output_identity.py tests\test_ms21_b6_adjustment_history.py tests\test_ms21_b7_analysis_rollback.py tests\test_ms21_b7_ui_sync_context.py tests\test_wx_ms21_b6_undo_redo.py tests\test_wx_ms21_b7_state_integration.py tests\test_wx_ms21_b7_sync_efficiency.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms20_b2_output_diagnostics.py tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b6_diagnostic_report.py tests\test_ms20_b6_report_save_flow.py tests\test_pipeline_and_vmd.py tests\test_preview_transform.py tests\test_vmd_writer_grouping.py tests\test_vmd_writer_intervals.py tests\test_vmd_writer_peak_value.py tests\test_vmd_writer_zero_guard.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_ms17_b8_late_worker_result_discard.py tests\test_ms19_b4_voice_only_gui_state.py tests\test_ms19_b7_voice_only_error_handling.py tests\test_ms19_b8_workspace_reset.py tests\test_ms20_b7_diagnostics_state_integration.py tests\test_wx_ms14_b4_analysis.py tests\test_wx_ms14_b5_export.py tests\test_wx_ms15_b3_playback.py
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q -k "wx"
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q -k "wx"
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q
.\.venv\Scripts\python.exe -X faulthandler -m pytest -q
.\.venv\Scripts\python.exe -m compileall src tests
git check-ignore -v -- profiles.json presets.json MMD_AutoLipTool.ini
git ls-files -- profiles.json presets.json MMD_AutoLipTool.ini
git diff --name-only 4e85682..HEAD -- pyproject.toml MMD_AutoLipTool.spec build.ps1 LICENSE NOTICE THIRD_PARTY_LICENSES.md docs/Release_Package_Manifest.md
rg -n "profiles\.json|presets\.json|MMD_AutoLipTool\.ini" MMD_AutoLipTool.spec build.ps1 docs\Release_Package_Manifest.md
rg -n "PySide6|PyQt6|PyQt5|requests|httpx|urllib|aiohttp|socket|cloud ASR|auto.?download" src pyproject.toml
git diff --check
```

期待結果は次のとおりである。

- pytest / compileall / `git diff --check`: process exit code 0
- `git check-ignore`: 3 pathすべてにroot限定ruleを表示しexit code 0
- `git ls-files --`: 出力なし、exit code 0
- dependency / package / license diff: 出力なし、exit code 0
- package filename検索とnetwork / Qt検索: 該当なし、`rg`のno-match exit code 1を期待結果として記録

検索該当を見つけた場合は内容とMS23差分を確認してfinding化する。no-matchを得るためにsourceを変更しない。

### 11.4 Block完了時automated baseline

次はB7実行結果ではなく、B7 plan作成時にcommitted docsから確認した既存証拠である。

| Block | automated baseline |
| --- | --- |
| B1 | 249 passed、全command exit 0、`git diff --check` exit 0、P1 / P2 / P3なし |
| B2 | 専用24件、関連228件、full 738件、compileall、diff checkがexit 0 |
| B3 | 専用21件＋31 subtests、full 759件＋57 subtests、compileall、diff checkがexit 0 |
| B4 | 専用12件、関連52件はexit 0。full 771件＋57 subtestsはpass表示だがexit 1。B4Bへ分離 |
| B4B | 既知10件、wx 129件×2、non-wx 644件＋57 subtests、full 773件＋57 subtests×2、compileallがexit 0 |
| B5 | 関連31件、full 785件＋57 subtests、compileall、diff checkがexit 0 |
| B6 | 専用12件、複数回帰group、wx 136件×2、full 797件＋57 subtests×2、compileall、diff checkがexit 0 |

### 11.5 manual GUI evidence

| Block | evidence | B7での扱い |
| --- | --- | --- |
| B1 | contract固定のみ | manual GUI対象外 |
| B2 | 2026-08-16、ユーザーから確認通過・問題なしの報告 | ユーザー報告の範囲だけ再利用。Codex実行ではない |
| B3 | store / persistenceのみ | Manual GUI Not Required |
| B4 | profile UIはB5へdeferred | B4単独のmanual passを捏造しない |
| B4B | test-harness / teardownのみ | Manual GUI Not Required |
| B5 | 2026-08-19、ユーザーから確認通過・問題なしの報告 | profile UI範囲だけ再利用。Codex実行ではない |
| B6 | 2026-08-20、profile Apply後のUndo / Redoを含む限定確認通過・問題なしの報告 | B6限定範囲だけ再利用。Codex実行でもactual-MMDでもない |

B7が文書監査だけでproduct behaviorを変更しない場合、新しいmanual GUI確認を必須にしない。別repairが対象挙動を
変更した場合は、そのrepair完了後に影響範囲だけを再確認し、B7をStep 0から再開する。

### 11.6 build / actual-MMD境界

- B7ではbuild、SmokeLaunch、package生成を行わない。
- package / dependency / license差分がないことを静的に確認する。
- 差分が見つかった場合はbuildへ進まずP2として報告する。
- 実MMDでのVMD / WAV読込・再生・リップ同期は実行しない。MS26未確認として報告する。

## 12. 受け入れ条件

- B1〜B6およびB4Bの要求、commit、Block完了時test、manual evidence、docsが§15へ統合される。
- B4時点のfull suite exit 1とB4B以後の解消証拠を時点別に保持する。
- Roadmap MS23の目的・完了条件へcode、direct test、docs、manual evidenceまたはmanual非対象理由が対応付く。
- strict version 1 `profiles.json`、最大100件、atomic mutation、safe failure、INI同一保存場所契約が確認される。
- no-profile Japanese defaultとJapanese / Latin built-in setだけが利用可能である。
- semantic final normalization後の一回mappingとframe number / value / count / order不変が確認される。
- writer、Preview、diagnostics、report、fingerprintが同一resolved output contractを使う。
- precedence、runtime baseline、startup fallback、mutation guard、direct edit guardがdirect testで確認される。
- upper差分とoutput-only差分のanalysis / history分類、profile-aware Undo / Redo、reset / rollback / stale結果が確認される。
- commit前failureとcommit後INI save failureが分離される。
- TEXTあり / voice-only、empty / invalid、long-vowel、既存日本語出力、VMD 30fps、audio三役の回帰が通る。
- MS23 direct、指定回帰、wx aggregate 2回、full suite 2回がpass表示・fatalなし・process exit code 0である。
- `compileall src tests`と`git diff --check`がprocess exit code 0である。
- manual evidenceの主体、日付、範囲が記録され、Codex manual executionやactual-MMDへ拡大されていない。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`はroot限定ignore、Git非追跡、非stage、package非同梱である。
- 3 runtime fileの内容を読まず、fixture化・変更・削除していない。
- MS23由来のdependency / package / build / license / network / Qt変更がない。
- PMX / PMD、任意mapping、user-defined set、additional expressions、英語ASR、MS24 / MS25 / MS27を実装済みと記載しない。
- 実MMD未確認がMS26へ明示的に残る。
- findingにseverity、evidence、影響、owner、措置、再検証条件があり、A / B / C判定が§8.5に従う。
- B7監査でproduction code、test code、GUI、runtime data、package / build設定を変更していない。
- Closeout文書間の判定、日付、HEAD、test値、manual主体、次工程が一致する。
- A / Bの場合、次工程をMS24 Implementation Plan策定とし、MS24実装を開始しない。
- Cの場合、Closeout延期とrepair / evidence条件を記録し、MS24へ進めると表現しない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| B4のpass表示だけを見てexit 1を隠す | Block完了時summary、fatal、exit code、B4B解消chainを別列にする |
| B4のhistorical exit 1をcurrent failureと誤認する | B4B、B5、B6、B7 current revalidationを時点別に記録する |
| 後続full suiteだけで前段contractを証明する | direct testとrequirement crosswalkをBlock単位で持つ |
| ユーザーGUI報告をCodex実行と誤記する | executor、日付、範囲を必須fieldにする |
| B6限定GUI確認をactual-MMDへ拡大する | actual-MMDを独立したMS26 deferred fieldとして維持する |
| runtime user dataを監査中に読む・fixture化する | `check-ignore`と`ls-files`のpath-level確認だけを許可する |
| runtime fileを誤ってtracking / packageへ含める | root限定ignore、tracked出力なし、spec / build / manifest no-matchをA gateにする |
| local user dataを修復名目で変更・削除する | B7で一切操作せず、必要なrepository repairも別承認へ停止する |
| docのplanned / implemented / verifiedが混ざる | status語を§8.2へ固定し、current code / testsと再照合する |
| P1 / P2をCloseout文書修正へ混ぜる | repairを分離し、完了後Step 0から再監査する |
| test件数差を無視する | 実行HEADとintervening diffへ対応付け、理由不明ならP2にする |
| package差分がないのにbuildへscope拡大する | 静的差分監査に限定し、buildはMS27へ残す |
| MS24 / MS25 / MS27を先行実装する | B7はhandoff条件だけを記録し、code / test / GUIを追加しない |
| network / Qtを依存経由で復活させる | `pyproject.toml`、source、MS22 baseline diffを静的監査する |
| arbitrary mappingをLatin set実装と混同する | built-in 2セットのexact ID / namesだけをacceptanceにする |
| MS22 Closeout Aを過去のMS23 findingで巻き戻す | milestone ownershipを分離し、MS23 findingとして扱う |

## 14. Codex監査時の注意

- B7はCloseout Auditであり、feature implementationではない。
- `agent_nesting_depth`が1以上ならsub-agentを起動しない。
- 最初にlive Git、routing正本、B7 plan、関連code / testsを再確認する。
- commandは必ず一つずつ実行し、並列、pipeline、`&&`、`||`、`;`で連結しない。
- production code、test code、GUI、runtime data、package / build設定を変更しない。
- B7専用testを新設しない。material evidence gapはP2としてrepairへ分離する。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`の内容を読まない。fixture化、変更、削除、stage、package同梱をしない。
- user-owned diffをrestore、上書き、stageしない。
- testのpass表示とprocess exit codeを分け、fatal / access violationを見落とさない。
- GUIを実行していない場合はmanual GUI verifiedと記録しない。
- actual-MMDを実行していない場合は確認済みと記録しない。
- PMX / PMD、arbitrary mapping、user-defined set、additional expression、英語ASRを計画へ追加しない。
- MS24 / MS25 / MS27 implementation、build、release、dependency変更、network、Qt revivalへ拡大しない。
- stage、commit、push、merge、tag、branch作成・切替・削除は別途明示承認まで行わない。
- A / B / C判定前にhistory文書をMS23完了へ更新しない。
- 最終報告では事実、推論、未確認を分け、findingとresidual uncertaintyを隠さない。

## 15. Closeout証拠台帳

B7実施時に`B7 current revalidation`と`current finding / owner`をcurrent HEADの実測へ更新する。
Block完了時証拠はhistorical evidenceとして保持する。

| Block | 主要要求 / 契約 | 実装・契約commit | Block完了時の自動証拠 | manual evidence | 主文書 | B7 current revalidation | current finding / owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | D1〜D7、S1〜S7、schema、precedence、failure、history、startup、guard | `54256d0 Finalize MS23-B1 contract status sync`（contract固定） | 249 passed、全command exit 0、diff check exit 0、P1 / P2 / P3なし | N/A。contract固定 | B1 plan、Block、Index、Roadmap | current direct 82 passed＋31 subtests、full 797 passed＋57 subtests×2、process exit 0 | current findingなし。MS22 Closeout Aは維持 |
| B2 | built-in Japanese / Latin、normalize後一回mapping、writer / Preview / diagnostics、import境界 | `cb86aaa Implement MS23-B2 morph name mapping` | 専用24件、関連228件、full 738件、compileall、diff check / exit 0 | 2026-08-16 User Report: 通過・問題なし | B2 plan、Pipeline / VMD、Block、Index、Roadmap | current direct 82 passed＋31 subtests、writer / Preview / diagnostics / VMD group 174 passed、process exit 0 | current findingなし |
| B3 | immutable profile DTO、strict v1 JSON、最大100件、atomic CRUD、INI identity、root ignore | `3d9f936 Implement MS23-B3 model profile persistence` | 専用21件＋31 subtests、full 759件＋57 subtests、compileall、diff check / exit 0 | Manual GUI Not Required | B3 plan、Pipeline / Error、Block、Index、Roadmap | current direct 82 passed＋31 subtests、runtime path / package boundary再確認、process exit 0 | current findingなし。runtime user dataはGit非追跡・root ignore |
| B4 | resolver、state、history、startup、guard、writer / Preview / diagnostics / report接続 | `c17aeda Implement MS23-B4 and document B4B repair plan` | 専用12件、関連52件 / exit 0。full 771件＋57 subtestsはpass表示・exit 1 | Manual GUI Deferred to B5 | B4 plan、Block、Index、Roadmap | current direct 82 passed＋31 subtests、lifecycle 54 passed＋7 subtests、wx 136 passed×2、process exit 0 | historical wx teardown P2はB4Bで解消。current残存なし |
| B4B | wx App ownership、Frame / Controller / timer / callback teardown、exit stability | `cc23666 Implement MS23-B4B wx teardown repair` | 既知10件、wx 129件×2、non-wx 644件＋57 subtests、full 773件＋57 subtests×2、compileall / exit 0 | Manual GUI Not Required | B4B plan、Block、Index、Roadmap | current wx aggregate 136 passed×2、full 797 passed＋57 subtests×2、fatalなし・process exit 0 | current findingなし |
| B5 | Select / Apply、CRUD、active Rename-only、Busy / stale、profile / preset cross-sync | `4947dfe Implement MS23-B5 model profile UI` | 関連31件、full 785件＋57 subtests、compileall、diff check / exit 0 | 2026-08-19 User Report: 通過・問題なし | B5 plan、GUI仕様、Block、Index、Roadmap | current direct 82 passed＋31 subtests、wx aggregate 136 passed×2、process exit 0 | current findingなし。GUI evidenceはユーザー報告の範囲に限定 |
| B6 | cross regression、Redo profile再投影、docs、runtime / package / dependency境界 | `5349ea4 Implement MS23-B6 cross regression` | 専用12件、指定group、wx 136件×2、full 797件＋57 subtests×2、compileall、diff check / exit 0 | 2026-08-20 User Report: profile Apply後Undo / Redoを含む限定確認通過・問題なし | B6 plan、README、仕様、Block、Index、Roadmap | current dedicated 82 passed＋31 subtests、関連group 318 passed＋7 subtests、wx 136 passed×2、full 797 passed＋57 subtests×2、compileall / diff check exit 0 | current findingなし。actual-MMDはMS26へdeferred |

### 15.1 B7 current audit record（2026-08-20）

- audit date: 2026-08-20
- branch / HEAD: `feature/MS23-implementation` / `b843d24 Document MS23-B7 closeout plan`
- audit開始時worktree: clean。pre-existing user changesなし
- MS23 direct regression: `82 passed, 31 subtests passed` / process exit code 0
- MS21 / MS22 related regression: `90 passed` / process exit code 0
- diagnostics / report / Preview / writer / VMD regression: `174 passed` / process exit code 0
- MS17 / MS19 / MS20 lifecycle regression: `54 passed, 7 subtests passed` / process exit code 0
- wx aggregate run 1 / run 2: `136 passed, 661 deselected`を2回 / 各process exit code 0
- full suite run 1 / run 2: `797 passed, 57 subtests passed`を2回 / 各process exit code 0
- `compileall src tests`: process exit code 0
- `git diff --check`: process exit code 0
- runtime user-data path boundary: 3 pathすべてroot限定ignoreを表示。`git ls-files --`は出力なし。内容は読取・変更・stageしていない
- package / dependency / license boundary: MS22 Closeout Aの`4e85682`から監査時HEADまで対象差分なし。runtime filenameのpackage static searchも該当なし
- network / Qt boundary: `src` / `pyproject.toml`の対象静的検索は該当なし。Qt / network / auto-downloadを追加していない
- user GUI evidence: B2 / B5 / B6の既存ユーザー報告を、報告された範囲だけ再利用。B1 / B3 / B4Bはmanual GUI非対象、B4はB5へ委譲
- Codex manual GUI execution: not executed
- actual-MMD verification: not executed。VMD / WAV読込・再生・リップ同期はMS26へdeferred
- P1 / P2 / P3: 0 / 0 / 0。historical B4 wx teardown P2はB4Bで解消済み
- Closeout decision A / B / C: **A**
- MS24 handoff: MS23完了。MS24 Implementation Plan策定へ進行可能。MS24実装は開始しない
- MS26 handoff: actual-MMD確認をMS26の責務として維持

### 15.2 finding ledger（2026-08-20）

P1 / P2 / P3のcurrent findingはない。B4実装時のwx teardownによるhistorical P2はB4Bで解消され、今回のwx aggregate・full suite再検証でも残存しなかった。actual-MMD未確認は事前定義済みの`Deferred-by-design: MS26`であり、findingには分類しない。

## 16. 実施後の報告形式

1. 確認したファイル
2. 変更したファイル
3. Closeout監査内容
4. 実行したcommand
5. 自動検証結果（pass表示 / failure / error / fatal / process exit code）
6. manual GUI evidence（実施者 / 日付 / 範囲 / 結果）
7. runtime user data / package / dependency / license / network / Qt境界
8. P1 / P2 / P3
9. Closeout判定（A / B / C）と根拠
10. 仕様から逸脱した点
11. 未検証事項。実MMDはMS26 deferredと明記する
12. MS24 / MS26へのhandoff
13. final Git status。stage / commit / push等の未実施も明記する
