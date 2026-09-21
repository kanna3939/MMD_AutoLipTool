# MS23-B4B Implementation Plan

## 1. 文書情報

- 文書名: MS23-B4B wx Test Teardown / Full Pytest Exit Stability Repair Implementation Plan
- 作成日: 2026-08-18
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時のbranch: `feature/MS23-implementation`
- 計画作成時の基準HEAD: `005c57b Document MS23-B4 implementation plan`
- 親Block: MS23-B4 Resolution / State / Diagnostics
- 依存: MS23-B4実装、既存`tests/helpers.py`の`destroy_wx_app()`、MS22-B6のlifecycle補修契約
- 文書ステータス: Implemented / P2-P3 Corrections Applied / Automated Verification Passed
- レビュー補正日: 2026-08-18
- 実装完了日: 2026-08-18
- 実装結果: test-harness / wx test lifecycleを修正。production code、GUI、runtime user dataは変更していない。stage、commit、pushは今回未実施

本BlockはMS23-B4の機能仕様を変更するBlockではなく、全体Pytest終了時のwxPython native teardown不安定性を修正するための補正Blockである。MS22 Closeout A、MS23-B1の採用済み契約、MS23-B4のprofile resolution契約は変更しない。

## 2. 背景

MS23-B4実装後、関連する専用・回帰テストは終了コード0で完了した。一方、全体実行は次の状態になった。

- `771 passed, 57 subtests passed`までsummaryは完走した。
- assertion failure / test errorの表示はなかった。
- process exit codeは1だった。
- `-X faulthandler`付き再実行では、全テスト終了後のGarbage Collection中に`Windows fatal exception: access violation`が発生した。
- `-k "not wx"`は終了コード0、`-k "wx"`は同じaccess violationで終了コード1になった。
- wxテストを明示的なファイル群へ分割すると終了コード0になる組合せがあり、テスト順序とnative object lifetimeに依存する。

現行コード上、次の具体的なteardown不統一を確認している。

- `tests/helpers.py`にはcontroller、pending callback、frame、appを順序付きでcleanupする`destroy_wx_app()`があるが、利用範囲は新しい一部wxテストに限られる。
- `tests/test_wx_ms14_b5_export.py`には既存Appを確認せず別の`wx.App()`を生成するテスト経路がある。
- MS14〜MS20の複数テストは`frame.Destroy()`だけで終了し、App、controller、timer、pending callbackの所有と終了順を固定していない。
- MS15の一部テストはApp破棄をGCへ任せるコメントと実装を持つ。
- 一部fixtureは`wx.App.Get() or wx.App(False)`でAppを共有するが、fixture終了時のApp所有権と破棄責務を記録していない。

したがって、直接確認できた原因は「Garbage Collection中のnative access violation」であり、単一のwx objectまでの原因特定は未完了である。ただし、Appの重複生成、controller / timer / callbackの未解放、frame-only teardown、テスト順序依存が強い寄与要因として確認できる。B4Bではこの範囲をP2修正対象とする。

## 3. 目的

1. wxテストのApp、Frame、Controller、Timer、pending callbackの終了順と所有権を一つの契約へ統一する。
2. `-k "wx"`と全体Pytestを、summaryだけでなくprocess exit code 0まで安定させる。
3. テスト順序を変えてもnative objectの寿命が変わらないようにし、GC任せのteardownをなくす。
4. MS23-B4のprofile resolution、state、history、diagnostics、writer、Preview、reportの製品挙動を変更しない。
5. テスト失敗を隠すskip、assertion弱化、テスト削除で終了コードを合わせない。

## 4. In Scope

- `tests/helpers.py`のwx teardown契約の補正
- Appを新規生成したか既存Appを再利用したかを記録するfixture / helperの整備
- Frame / Controller / timer / worker / pending callbackのcleanup順序の統一
- `frame.Destroy()`だけ、またはGC任せになっているwxテストの限定修正
- 既存Appがある状態で`wx.App()`を重複生成するテストの修正
- MS14〜MS23およびstartup splashのwxテストを、同一契約で監査すること
- 既知の再現経路であるMS14-B1 + MS14-B5の組合せを最初のrepair gateとすること
- wx aggregate、non-wx回帰、full suite、faulthandler、compileall、diff checkによる再検証
- B4B実装結果をBlock Breakdown、Index、Roadmap、本planへ同期すること

## 5. Out of Scope

- MS23-B4のprofile resolution、precedence、history、diagnostics、fingerprintの仕様変更
- MS23-B5のモデルプロファイルUI実装
- PMX / PMD解析、任意モーフ名mapping、ユーザー定義モーフセット、追加表情モーフ
- VMD形式、30fps、既存音声契約、固定日本語モーフ`あ / い / う / え / お`の変更
- Qt / PySide6復活、network、external ASR、Whisper download、依存追加
- Pytest設定の広域変更。`pyproject.toml`にpytest addoptsがないことは確認対象だが、設定変更は第一選択にしない
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`の生成、変更、stage
- 実MMDでのVMD / WAV読み込み・リップ同期確認。これはMS26のまま維持する
- package、release、tag、merge、push、branch削除

## 6. 前提条件

- MS23-B4の既存production code、test code、docs差分はユーザー所有の変更として保持する。B4B実装時にrevert、reset、無関係な整形を行わない。
- B4のB4専用12件と関連回帰52件が終了コード0だった事実は維持し、B4Bの修正で機能テストの期待値を変えない。
- ユーザーによるB4手動GUI確認は「問題なし」の範囲で記録済みだが、B4Bの自動teardown修正をCodexの手動GUI実行結果とは扱わない。
- `tests/helpers.py`の`destroy_wx_app()`は、controllerの`request_exit()`、pending event処理、frame cleanup、App破棄を行う既存基盤であり、B4Bの初期修正方針の正本候補である。
- Appを共有する場合は、テストが生成したAppか、外部fixtureが所有するAppかを明示する。再利用Appを無条件に破棄しない。
- 実装開始前に、このplanと現行test / helper / source lifecycleをfresh read-onlyで再照合し、P1 / P2 / P3の未解消がないことを確認する。

## 7. 対象ファイル

### 7.1 第一候補のtest infrastructure / test files

| ファイル | B4Bでの確認・修正対象 |
|---|---|
| `tests/helpers.py` | App所有権、idempotent teardown、controller / pending event / frame / Appの終了順を共通化 |
| `tests/test_wx_ms14_b1_ui.py` | `AutoLipToolApp`のMainLoop終了とframe-only teardownを共通helperへ統一 |
| `tests/test_wx_ms14_b3_input.py` | class teardownのApp / Frame / pending event処理を統一 |
| `tests/test_wx_ms14_b4_analysis.py` | analysis controller、timer、MainLoop終了を統一 |
| `tests/test_wx_ms14_b5_export.py` | module fixtureの所有権、重複`wx.App()`生成、frame-only teardownを修正 |
| `tests/test_wx_ms15_b1_waveform.py` | per-test App生成とGC任せのteardownを修正 |
| `tests/test_wx_ms15_b2_preview.py` | per-test App生成とframe-only teardownを修正 |
| `tests/test_wx_ms15_b3_playback.py` | per-test App / Frame / App teardownを監査し、必要時に共通helperへ移行 |
| `tests/test_wx_ms16_b3_right_pane.py` | direct App / Frame teardownを監査し、必要時に共通helperへ移行 |
| `tests/test_wx_ms16_b6_event_selection_foundation.py` | direct App / Frame teardownを監査し、必要時に共通helperへ移行 |
| `tests/test_ms19_b4_voice_only_gui_state.py` | class App / Frameの終了責務を統一 |
| `tests/test_ms20_b3_right_pane_info.py` | class fixtureと各testのFrame teardownを統一 |
| `tests/test_ms20_b5_warning_save_policy.py` | module App fixtureと各Frame teardownを統一 |
| `tests/test_ms20_b6_report_save_flow.py` | module App fixtureとFrame teardownを統一 |
| `tests/test_wx_ms21_b3_preview_selection.py` | direct App / Frame teardownを共通契約へ移行 |
| `tests/test_wx_ms21_b4_selected_event_editor.py` | direct App / Frame teardownを共通契約へ移行 |
| `tests/test_wx_ms21_b6_undo_redo.py` | direct App / Frame teardownを共通契約へ移行 |
| `tests/test_wx_ms21_b7_state_integration.py` | direct App / Frame teardownを共通契約へ移行 |
| `tests/test_wx_ms21_b7_sync_efficiency.py` | direct App / Frame teardownを共通契約へ移行 |
| `tests/test_wx_ms22_b5_long_vowel_override.py` | direct App / Frame teardownを共通契約へ移行 |
| `tests/test_ms23_b4b_wx_teardown.py`（新規候補） | owned / reused App、helperのidempotence、root save防止を直接検証 |

上記以外にも、`wx.App`、`Destroy()`、`ProcessPendingEvents()`、`MainLoop()`、`CallAfter()`、`CallLater()`を持つMS13〜MS23およびstartup splashのテストを監査対象とする。既に`destroy_wx_app()`を正しく使用している経路は、不要な書き換えをせず回帰対象として保持する。MS21〜MS22で`app.Destroy()` / `frame.Destroy()`を直接行う経路は、helper使用済みとはみなさず、個別に変更要否を判定する。

### 7.2 production codeの扱い

- 初期実装では`src/gui_wx/app.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/main_frame.py`をread-onlyで照合する。
- B4Bの実装範囲ではproduction codeを変更しない。test teardownを統一しても同じnative access violationが再現した場合は、実装を停止して原因・再現順・参照経路を報告する。
- `src/gui_wx`の補正が必要になった場合は、B4Bの範囲を自動拡張せず、別のrepair planまたは明示承認を得てから着手する。B4Bの受け入れ条件だけでproduction変更を許可しない。

### 7.3 文書

- `docs/Implementation_Plan/MS23-B4B_Implementation_Plan.md`
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

## 8. 実装方針

### 8.1 推奨方針: test-harness first

最初に、既存の製品コードへ変更を加えず、test infrastructureと既存wxテストの終了処理を統一する。理由は、現在の直接証拠がテスト終了後のGarbage Collection中access violationであり、`-k "not wx"`が終了コード0、wxテスト集合だけが非zeroであるためである。製品のprofile resolutionが原因だと先に仮定してproduction codeを変更すると、B4の機能回帰を招く可能性がある。

### 8.2 共通teardown契約

各wxテストは次の契約を満たす。

1. 同時に複数のactiveな`wx.App`を作らない。`wx.App.Get()`が既存Appを返す場合は新規Appを作らず、既存Appを再利用する。
2. Appを生成したfixtureは`owns_app=True`、既存Appを再利用したfixtureは`owns_app=False`を保持する。前のowned Appがteardown済みでactive Appが存在しない場合の順次生成は許可し、共有App化を強制しない。
3. Frame、Controller、analysis job、timer、pending callbackを、Frame破棄より前に停止・解放する。
4. `CallAfter` / `CallLater`などのpending eventを、対象Frameが生きている間に処理する。
5. Frameを破棄した後にpending eventを無条件で対象へ送らない。
6. fixtureが所有するAppだけを最後に明示破棄し、再利用Appは所有者へ返す。
7. 部分初期化、既に破棄済み、二重teardownでも例外を増やさない。
8. teardownはGCのタイミングやpytestの終了処理に依存しない。

### 8.3 既存helperの扱いとruntime user data保護

`destroy_wx_app()`を共通入口として再利用する。必要なら、再利用Appを破棄しないための明示的なownership引数と、部分初期化・二重呼出しに対する安全性を追加する。ただし、helperの変更は全既存呼出し元の契約を確認してから行い、既存のcontroller `request_exit()`、pending event drain、analysis cleanupの順序を弱めない。

`controller.request_exit()`はpending saveをflushし得るため、`AutoLipToolApp` / Controllerを使用するtestではSettingsStore、PresetStore、ProfileStoreをtemporary pathへ注入するか、root runtime user dataへ書き込まないteardown seamを使用する。`profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`のroot実体をtest終了処理で生成・更新しない。reused AppのteardownではFrame / Controllerのcleanupだけを行い、Appを破棄せず所有者へ返す。

### 8.4 production変更の停止条件

test-harness修正後も`-k "wx"`とfull suiteで同一access violationが再現する場合は、faulthandler、再現順、controller / timer / callbackの参照経路を記録して停止する。B4Bの実装中に証拠だけを理由として`src/gui_wx`へ変更を広げず、別planまたは明示承認へ戻す。

## 9. 詳細ステップ

### Step 0: 実装開始前のfresh gate

- live Git、B4差分、B4 plan、B4B plan、Block Breakdown、Index、Roadmapを確認する。
- root runtime user dataとpre-existing diffを記録する。
- B4専用、関連回帰、full suite、wx / non-wx分割の現行結果を一つずつ再確認する。
- P1 / P2 / P3の残存と、B4BがB5 UIへ拡大していないことを確認する。

### Step 1: lifecycle inventory

- `wx.App`生成箇所、App再利用箇所、App所有者を一覧化する。
- `frame.Destroy()`だけの経路、GC任せのコメント、MainLoop終了、pending callback、controller / timerを分類する。
- MS14-B1 + MS14-B5の既知再現を最小commandとして固定する。

### Step 2: helper contract repair

- `destroy_wx_app()`の引数・ownership・idempotenceを最小限補正する。
- controllerがある場合はcontroller終了を先行し、Frameが生きている間にpending eventを処理する。
- plain Frameの場合もanalysis cleanup、Frame破棄、pending event、所有App破棄の順を統一する。
- helper単体または直接呼出しテストで、owned Appとreused Appの双方を検証する。

### Step 3: known reproducerから段階移行

- `test_wx_ms14_b5_export.py`の重複App生成を除去し、fixtureの既存Appを使う。
- `test_wx_ms14_b1_ui.py`、MS14-B3、MS14-B4のclass teardownを共通helperへ移行する。
- MS15のper-test AppとGC任せのteardownを、所有権付きfixtureへ移行する。
- MS19 / MS20のmodule / class fixtureを同じ契約へ移行する。
- MS16、MS21、MS22の`app.Destroy()` / `frame.Destroy()`直接経路を監査し、必要なものを共通helperへ移行する。既に正しいhelperを使う経路は変更せず、aggregate回帰へ含める。
- `tests/test_ms23_b4b_wx_teardown.py`でowned App / reused App、二重teardown、pending save時のroot save防止を直接検証する。

### Step 4: incremental verification

- 既知reproducer、MS14〜MS15、MS19〜MS20、全wx集合、non-wx集合の順で実行する。
- すべてのcommandでpass表示とprocess exit codeを別々に記録する。
- 途中でaccess violationが消えた場合も、テスト順序を変えたaggregateとfull suiteを追加実行する。

### Step 5: unresolved failureの停止・引き継ぎ

- test側修正後も同じfatal traceが出る場合は、`app.py`の遅延callback / splash、`app_controller.py`のtimer / controller、`main_frame.py`のcleanup所有をread-onlyで再照合する。
- 原因とproduction ownershipの証拠を報告し、B4B実装を完了扱いにしない。production修正は別planまたは明示承認後の別作業へ引き継ぐ。

### Step 6: 最終監査と文書同期

- diffでtest lifecycle以外のproduction機能、schema、dependency、package、runtime dataが混入していないことを確認する。
- B4Bの状態を「実装済み」にするのは、全受け入れ条件とprocess exit code 0を確認した後だけにする。
- B4の手動GUI確認とMS26の実MMD未確認を維持して文書へ反映する。

## 10. 状態遷移 / データ契約

### 10.1 App / Frame ownership

| 状態 | 所有 | 許可される終了処理 |
|---|---|---|
| Appなし | test fixture | `wx.App.Get() is None`を確認して`wx.App(False)`を生成し`owns_app=True`。teardown後の順次生成は許可 |
| 既存Appあり | 外部fixtureまたは先行test | `wx.App()`を追加生成せず、`owns_app=False`で再利用 |
| App + Frame + Controller | test / AppController | job・timer・callbackを停止し、Frameが生きている間にpending eventを処理 |
| Frame終了要求後 | test fixture | controller終了またはplain Frame cleanupを完了してFrameを破棄 |
| Frame破棄後 | test fixture | pending eventを安全に処理し、`owns_app=True`のときだけAppを破棄 |

### 10.2 B4 product state invariants

- B4Bは`ModelProfileState`、`GenerationState`、history、diagnostics、fingerprint、resolved morph-name setのデータ契約を変更しない。
- teardown修正でprofile、preset、INI、analysis result、VMD frame、Preview semantic keyを変更しない。
- save failure、rollback、stale worker、workspace resetのB4契約は、既存testのassertionを維持したまま回帰する。
- root runtime user dataはテスト対象から隔離し、temporary directoryのみを使う。
- Controllerを持つtestではpending saveの保存先もtemporary pathとし、teardownでroot `profiles.json` / `presets.json` / `MMD_AutoLipTool.ini`を生成・更新しない。

## 11. テスト方針

### 11.1 最小再現・段階検証

各commandを個別に実行し、結果と終了コードを記録する。

1. `.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_wx_ms14_b1_ui.py tests\test_wx_ms14_b5_export.py`
2. MS14-B1〜B5、MS15、MS16、MS19、MS20、MS21、MS22のlifecycle対象
3. `.\.venv\Scripts\python.exe -X faulthandler -m pytest -q -k "wx"`
4. `.\.venv\Scripts\python.exe -m pytest -q -k "not wx"`
5. B4専用testと関連52件
6. full suite（`.\.venv\Scripts\python.exe -X faulthandler -m pytest -q`）
7. `compileall src tests`
8. `git diff --check`

### 11.2 必須の安定性確認

- `-k "wx"` aggregateを少なくとも2回連続でprocess exit code 0にする。
- full suiteを少なくとも2回連続でprocess exit code 0にする。
- full suiteでは`Windows fatal exception`、`access violation`、未処理native tracebackがないことを確認する。
- testのskip追加、assertion削除、期待値緩和、特定testの無条件除外を行わない。
- B4専用12件、関連回帰52件、non-wx集合が修正前の機能結果を維持する。

### 11.3 GUI / actual-MMDの扱い

- B4Bはtest teardownの修正であり、新しい製品GUI機能を追加しないため、B4B自体の手動GUI確認は自動検証の代用にしない。
- ユーザーが実施済みのB4手動GUI確認は、B4の範囲に限定して記録する。
- 実MMDによるVMD / WAV読み込み・リップ同期はMS26へdeferredのままとする。

### 11.4 実装後の検証結果

2026-08-18にB4Bを実装し、以下を各コマンド個別に実行した。すべてprocess exit code 0である。

- 既知MS14-B1 + MS14-B5: `10 passed`
- MS14〜MS16 lifecycle対象: `53 passed`
- MS19〜MS20 lifecycle対象: `101 passed, 7 subtests passed`
- MS21〜MS23 lifecycle対象: `58 passed`
- B4 / B4B専用対象: `14 passed`
- wx aggregate 1回目: `129 passed, 644 deselected`
- wx aggregate 2回目: `129 passed, 644 deselected`
- non-wx aggregate: `644 passed, 129 deselected, 57 subtests passed`
- full suite 1回目: `773 passed, 57 subtests passed`
- full suite 2回目: `773 passed, 57 subtests passed`
- `compileall src tests`: exit code 0

実装中に、teardown済みAppのsingleton残留、session scopeで保持されたApp、Frame破棄後のpending native deletionというtest-harness上の追加問題を検出し、`tests/helpers.py`と対象wx testの範囲で補正した。production codeのaccess violationは再現していない。

## 12. 受け入れ条件

- 既知のMS14-B1 + MS14-B5再現commandがprocess exit code 0で終了する。
- wx aggregate `-k "wx"`が2回連続でprocess exit code 0になる。
- full suiteが2回連続でsummary完走・failure / errorなし・process exit code 0になる。
- full suite終了時にGarbage Collection中のaccess violationやfatal native exceptionがない。
- owned Appとreused Appが混同されず、active Appが存在する間に重複`wx.App()`を生成しない。teardown済みAppの順次生成は既存testの独立性を維持する。
- Frame破棄前にcontroller、timer、worker、pending callbackを処理し、GC任せのteardownを残さない。
- B4専用12件、関連回帰52件、non-wx回帰、compileall、diff checkがprocess exit code 0である。
- root runtime user dataがtest前後で変更されず、Controllerのpending saveはtemporary storeへ隔離される。
- testの削除、skip、assertion弱化、機能契約の変更がない。
- MS23-B4の日本語default、preset単独Custom、VMD 30fps、fingerprint schema、runtime user data境界が維持される。
- production codeのaccess violationが残った場合はB4Bを停止し、別planまたは明示承認へ引き継ぐ。B4B内でproduction codeを変更しない。
- B4B実装完了を、B5 profile UI完了またはMS26 actual-MMD確認済みと表現しない。

上記受け入れ条件は、既知再現、wx aggregate 2回、full suite 2回、non-wx回帰、専用回帰、compileallの結果により確認済みである。B4Bの手動GUI確認は不要であり、B4のユーザー報告による手動GUI確認とMS26 actual-MMD未確認は維持する。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| 再利用中のAppを誤って破棄し、後続testを壊す | `owns_app`を記録し、所有Appだけを破棄する |
| Frame破棄後にCallAfter / CallLaterが実行される | Frameが生きている間にpending eventを処理し、controller / timerを先に停止する |
| active Appとの重複生成でnative object lifetimeが分岐する | `wx.App.Get()`を確認し、active Appがある間は再利用する。owned Appをteardownした後の順次生成は許可する |
| test順序変更で一時的に問題が隠れる | wx aggregateとfull suiteを複数回実行し、明示的なファイル群でも確認する |
| helper変更が既存の正しいMS22 / MS23 teardownを壊す | 既存helper利用テストを変更せず、対象回帰を先に実行する |
| P2修正がB4 production機能へ拡大する | B4B内のproduction変更を禁止し、必要時は別planまたは明示承認へ停止する |
| teardownがpending saveでroot user dataを書き換える | Controller依存testへtemporary storeを注入し、root fileの前後不変を確認する |
| B4の未コミット差分を誤って上書きする | 実装前後にGit diffと変更ファイルを確認し、B4差分を保持する |
| pass表示だけで終了コード1を見逃す | pass表示、fatal trace、process exit codeを別々に記録する |

## 14. Codex実装時の注意

- 実装前に本planのfresh read-only pre-checkを実施し、P1 / P2 / P3の未解消がないことを確認する。
- shell commandは一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`を使わない。
- production code、test code、GUIを変更する実装段階でも、最初はtest infrastructureだけを変更する。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`をrepo root test fixtureにせず、stageしない。
- B4のstate / resolver / writer / Preview / diagnostics契約を変更しない。
- `destroy_wx_app()`の順序を弱めず、App ownershipを無条件に推定しない。
- テストを削除、skip、弱化して終了コードを合わせない。
- 変更後はdiffをscope監査し、test lifecycle以外への拡大、B4回帰、Windows native teardown、既存ユーザー変更を再確認する。
- B4B実装完了後のユーザー報告では、確認ファイル、変更ファイル、修正内容、各testのpass表示とexit code、仕様逸脱、残課題、B5 / MS26 handoffを分ける。
- commit、push、merge、tag、release、branch削除は別途明示承認まで行わない。
