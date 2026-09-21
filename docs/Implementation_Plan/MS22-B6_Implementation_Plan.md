# MS22-B6 Implementation Plan

## 1. 文書情報

- 文書名: `MS22-B6 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS22-B6_Implementation_Plan.md`
- 対象Block: `MS22-B6 Lifecycle Regression / Documentation`
- 基準ブランチ: `feature/MS21-implementation`
- 計画作成基準HEAD: `525ac1e Implement MS22-B5 preset UI and event overrides`
- 作成日: 2026-08-11
- 文書ステータス: **Implemented / Automated Verification Passed / User Manual Test Passed (2026-08-11) / MS26 Actual-MMD Verification Deferred**
- 直接依存:
  - MS21 Closeout A
  - MS22-B1 Contract Fixed
  - MS22-B2 Implemented / Code Check Passed
  - MS22-B3 Implemented / Code Check Passed
  - MS22-B4 Implemented / Code Check Passed / User Manual Test Passed
  - MS22-B5 Implemented / Code Check Passed / User Manual Test Passed
- 次工程: MS22-B7 MS22 Closeout
- 上位正本:
  - `docs/Implementation_Plan/MS22_Block_Breakdown.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

本書は、MS22-B2からB5で実装した長音・generation preset・output history・GUI導線を、
既存のanalysis lifecycle、TEXTあり／voice-only、diagnostics、保存失敗、workspace resetへ
横断的に照合し、利用者向け文書と正本仕様を実装状態へ同期するための実装計画である。

本書の作成段階ではproduction code、test code、GUI、README、仕様書、INI / JSON本体、
依存関係、package設定を変更しない。B6は新機能Blockではなく、既存契約の回帰固定と文書同期を
所有する。横断testで実際のproduction契約違反を確認した場合は、原因・影響・最小修正範囲を
本書へ追記してからrepairする。未再現の可能性だけでproduction codeを変更しない。

2026-08-11のplan再チェックで検出したP2 4件とP3 2件は、本書だけを修正して解消した。JSON / INIの
load / mutation / foreground save / close-only save契約、invalid INI startup、store coreとwx output不変testの
責務分離、全pass表示／wx process exit code 1の既知baseline、利用者文書とrouting文書のMS26表現分離、
untracked file検査を追加した。production code、test code、GUI、既存仕様書は変更していない。

## 2. 背景

### 2.1 B5完了時点の実装状態

MS22-B2からB5では、次が実装済みである。

- 正規化済み読み列の明示的な`ー`を起点とするlong-vowel metadata
- shared `EffectiveShapePlan`によるPreview / writer共通の`hold / decay`
- `decay`が長音終端で`0.0`になる契約
- immutable `GenerationSettings`、built-in / user preset、versioned `presets.json`
- INIのactive generation settings / active preset idとCustom fallback
- adjustment、generation state、active preset idを一体化したsession内Undo / Redo
- generation settingsのoutput-only変更と、morph upper limitだけのanalysis parameter guard
- RightPaneのpreset選択／明示Apply、user preset管理、terminal eventのmode override
- effective outputを正本とするPreview、VMD準備、diagnostics、fingerprint、WARNING同期

B5専用test 10件とユーザーによるB5手動GUI確認は通過済みである。Codex自身が手動GUIを
実行した証拠としては扱わない。実MMDでのVMD / WAV読み込み・リップ同期は未確認であり、
MS26の手動受け入れへ維持する。

### 2.2 B6へ引き継いだ回帰境界

B5実装後の全体実行では、`tests/test_wx_startup_splash.py`の1件が全体負荷時だけ失敗し、
同test単独では2件通過した。`src/gui_wx/app.py`はstartup処理が1500ms未満なら`wx.CallLater`を使い、
1500ms以上ならmain frameを即時表示する。一方、現行testはassetが存在する場合に`CallLater`が
必ず呼ばれると仮定しており、経過時間の分岐を固定していない。

2026-08-11の現行HEAD再確認では、同test単独2件、MS22 / lifecycle関連122件、full suite 696件が
pass表示・process exit code 0だった。このsplash assertion失敗から確認できるのはproduction起動不良ではなく、
testの時間依存性である。B6では両方の正規分岐を決定論的に検証し、この理由だけではproduction挙動を変更しない。

同日のplan再チェックでは、preset persistence / wx generation / preset UI / settings close / splashの
47件と、B4 / B5 wx + splashの縮小17件がすべてpass表示だった一方、process exit code 1を2回確認した。
settings close単独7件はpass表示・process exit code 0だった。pytest failureはなく、native wx teardownの
正確な原因は未確定である。B4 / B5 testがtestごとに`wx.App`を生成・破棄し、splash testだけがframe破棄後に
pending eventを処理する差は原因候補であって確定原因ではない。B6では時間依存assertionとprocess exit問題を
別の既知境界として原因分離し、対象組合せとfull suiteの双方でprocess exit code 0を受け入れ条件とする。

### 2.3 文書と実装の現行差分

利用者文書と三つの正本仕様はMS21時点の説明を中心としており、MS22の実装状態が未同期である。

| 文書 | 現行差分 | B6で同期する内容 |
| --- | --- | --- |
| `README.md` | 長音mode、preset、Custom、preset永続化の利用手順がない | 利用手順、優先順位、Undo / Redo、再起動／新規作業境界 |
| `readme_mmdautolip.txt` | 配布向け説明にMS22機能と失敗時の回復方法がない | GUI操作、`presets.json`、decay終端zero、MMD側での最終確認注意 |
| Pipeline仕様 | long-vowel metadata、generation state、preset identityが未記載 | shared resolver、identity、output-only lifecycle、Preview / writer整合 |
| GUI仕様 | preset tab、terminal override、Custom表示が未記載 | Select / Apply分離、control有効条件、Busy / stale、theme / scroll |
| Error仕様 | preset JSON load / mutation failureの契約が未記載 | built-in継続、user mutation停止、state保持、INI失敗との分離 |
| Pipeline / Error仕様 | closing hold / softnessをanalysis terminal比較対象として記載 | 実装どおりmorph upper limitだけをanalysis parameter guardとする |

Roadmapは計画正本、Indexは現在地正本である。B6実装完了時は、上記仕様・利用者文書に加え、
Roadmap、Index、Block Breakdown、本書の状態記録を同じ検証結果へ同期する。ただしMS22全体の
Closeout A / B / C判定はB7だけが所有する。

## 3. 目的

1. MS22のgeneration stateとoutput historyが、startup、input変更、analysis、rollback、reset、
   app close / restartで既存job guardを迂回しないことを固定する。
2. TEXTあり／voice-onlyの双方で、明示的な`ー`のmetadata、preset state、Preview / writer共通出力が
   同じpipeline契約を使うことを回帰確認する。
3. VMD保存、diagnostic report、dialog cancel、JSON / INI failureが、正常なin-memory output state、
   history、diagnostics、WARNING確認状態を不正に失わせないことを固定する。
4. full suite負荷に依存するstartup splash testを決定論化し、wx teardownの全pass表示／process exit code 1を
   原因分離してexit code 0へ収束させる。
5. 利用者文書と正本仕様を、B2からB5のimplemented / verified状態へ同期する。
6. ユーザー手動GUI確認の実施者・範囲と、実MMDをMS26へ残す未検証境界を正確に記録する。

## 4. In Scope

### 4.1 Lifecycle横断回帰

- app startupでのvalid / missing / invalid INI、active preset id、valid / invalid `presets.json`解決
- baseなし`GenerationState`と、解析成功後のbase-bound `OutputEditState`の接続
- TEXTあり／voice-onlyのanalysis start / success / failure / cancel
- current job rollback、morph upper mismatch、late / duplicate callback
- input change、workspace reset、新しい解析成功時のbase / adjustment / history / selection破棄
- generation settings / active presetはworkspace local outputと分離して保持する契約
- app closeでのcoalesced INI flushと、restart後のlast successful settings復元
- session内output history、adjustment、selectionを再起動後へ復元しない契約
- wx frame / app teardownとshutdown中のlate callbackがtimer、state、保存要求を残さない契約

### 4.2 Long-vowel / preset横断回帰

- TEXTあり／voice-onlyの正規化済み読み列にある`ー`、連続`ー`、先行母音なし
- 同音非長音、same-vowel / cross-vowel、observationなしとの非混同
- preset Apply、direct generation edit、terminal event overrideの優先順位
- Preview / writer / diagnosticsが同じeffective contextを参照すること
- Undo / Redo後のactive preset解決、missing / deleted idのCustom正規化
- invalid JSON、unsupported schema、read / write / replace failure時の状態保持
- repository直下の実`presets.json`をtestから変更しないtemporary store注入

### 4.3 Save / diagnostics回帰

- VMD save dialog cancel、writer failure、再保存
- diagnostic report dialog cancel、overwrite拒否、writer failure、再保存
- effective output変更時のWARNING再確認と、表示名／preset idだけの変更時のfingerprint不変
- 保存失敗後のtiming plan、generation state、output history、Preview、diagnostics保持
- Busy、stale request、late callbackがsave / preset / event editをcommitしないこと

### 4.4 Startup splash / wx teardown安定化

- 1500ms未満の分岐をmock時刻で固定し、`wx.CallLater`のdelay範囲を検証
- 1500ms以上の分岐を別testで固定し、main frame即時表示とsplash破棄を検証
- full suite順序、machine speed、startup負荷をassertionの入力にしない
- `src/gui_wx/app.py`の1500ms最小表示契約は変更しない
- B4 / B5 wx + splashの全pass表示／process exit code 1を再現baselineとして保持する
- wx app / frame lifetime、pending event、controller timer、test順序を分離し、推測で一括fixture変更しない
- 対象組合せとfull suiteのpass表示／process exit code 0を別々に確認する

### 4.5 Documentation同期

- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- 本書の実装・検証・ユーザー確認状態

## 5. Out of Scope

- 新しい長音検出algorithm、音響的な長音推定、歌唱専用処理
- `GenerationSettings`、preset schema、`presets.json`上限・保存場所の変更
- 新しいpreset field、import / export、reorder、sharing、profile連携
- B5で実装済みのUI flow再設計、新しいdialog、generic preset editor
- fixed morph `あ / い / う / え / お`、30fps、VMD形式、既存音声三役の変更
- event mode override、hold / decay、tail、same-vowel / cross-vowel semanticsの変更
- session保存、history / adjustmentのdisk永続化
- モデルprofile・英字モーフ（MS23）、Whisper model選択（MS24）、一括出力（MS25）
- 実MMDでのVMD / WAV読み込み・リップ同期判定（MS26）
- Qt / PySide6、external ASR、音声外部送信、background通信、Whisper自動download
- dependency、package、build、release、tag、merge、push
- MS22 Closeout A / B / C判定（MS22-B7）
- 現行testが通過していることだけを理由にしたproduction refactor

## 6. 前提条件

- MS21 Closeout AとMS22-B1からB5の完了状態を未完了へ戻さない。
- `EffectiveShapePlan`をPreview / writer / diagnosticsの共通正本として維持する。
- `GenerationSettings`の3 fieldと`EventAdjustment.long_vowel_mode`のprimitive契約を変更しない。
- mode優先順位は `terminal event override > active generation settings > application default hold` とする。
- generation settingsはoutput-onlyであり、変更時にbase再解析を要求しない。
- analysis terminal parameter guardはmorph upper limitだけを比較する。
- input変更／workspace resetはgeneration stateを保持し、workspace local base、adjustment、output history、
  selection、diagnosticsをclearする。
- INI / JSON永続化失敗はin-memory output transactionと分離し、失敗を成功扱いしない。
- testはtemporary settings path / preset storeを注入し、rootのINI / `presets.json`を変更しない。
- GUI手動確認は実施者の報告を証拠として記録し、Codexが未実施なら未実施とする。
- 実MMD未確認はMS26へ残し、B6 / B7の完了と混同しない。

## 7. 対象ファイル

### 7.1 計画済み変更

| 分類 | ファイル | 変更内容 |
| --- | --- | --- |
| core / state回帰 | 新規 `tests/test_ms22_b6_lifecycle_regression.py` | non-wxのgeneration、history、persistence、identity境界 |
| wx横断回帰 | 新規 `tests/test_wx_ms22_b6_lifecycle_regression.py` | analysis、rollback、reset、save、Busy / staleのGUI統合 |
| startup test | `tests/test_wx_startup_splash.py` | mock時刻でdelay / immediateの両分岐を決定論化、重複main削除 |
| wx teardown調査／conditional test repair | `tests/test_wx_ms22_b4_generation_state.py`、`tests/test_wx_ms22_b5_preset_ui.py`、`tests/test_wx_startup_splash.py` | App / frame lifetime、pending event、timerを原因分離し、確認したtest fixture原因だけを限定補修 |
| settings close回帰 | `tests/test_wx_ms14_b5_export.py` | foreground / close-only INI failureの通知差とnon-blocking closeを維持 |
| 利用者文書 | `README.md` | MS22機能、利用手順、永続化・失敗、MMD側確認の注意 |
| 配布用文書 | `readme_mmdautolip.txt` | 同上を配布向け表現へ同期 |
| pipeline正本 | `docs/Pipeline_Data_Contract_Specification.md` | metadata、resolver、generation state、identity、lifecycle |
| GUI正本 | `docs/GUI_State_Theme_Specification.md` | preset tab、event override、state / theme / redraw |
| error正本 | `docs/Error_Handling_Specification.md` | JSON / INI / save failure、rollback、stale callback |
| routing / progress | `docs/MS20_and_Beyond_Index.md` | B6のimplemented / verified / manual状態 |
| roadmap履歴 | `docs/MS20_and_Beyond_Roadmap.md` | B6実施記録とB7引き継ぎ |
| Block正本 | `docs/Implementation_Plan/MS22_Block_Breakdown.md` | B6成果・検証・MS26境界 |
| 実装計画 | 本書 | 実績、検証値、残課題の反映 |

### 7.2 読み取り照合対象

- `src/core/effective_shape_plan.py`
- `src/core/output_edit_state.py`
- `src/core/event_adjustment_history.py`
- `src/core/generation_presets.py`
- `src/core/settings_store.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/ui_sync_context.py`
- `src/gui_wx/analysis_rollback.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/app.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/selected_event_editor.py`
- `src/core/preview_transform.py`
- `src/vmd_writer/effective_shape_adapter.py`

### 7.3 Conditional repair境界

B6開始時点ではproduction code変更を計画しない。新規横断testが、文書化済み契約に対する
再現可能なproduction defectを示した場合だけ、次を行う。

1. failing test、実装、B4 / B5契約のどれが誤っているかを切り分ける。
2. test期待値の弱化ではなく、正本契約に基づく最小修正候補を特定する。
3. 変更対象・副作用・追加回帰を本書へ追記する。
4. B6のrepair権限内であることを確認してからproduction codeを変更する。

新algorithm、新UI flow、新schemaが必要な場合はB6へ含めず、ユーザー判断を求める。

### 7.4 実装時の限定修正

既知のB4 / B5 / splash組合せを再実行した結果、pytestのpass表示とは別にprocess exit code 1となる問題を、
wx controllerのcoalesced save timer停止、`AutoLipToolApp`の遅延Layout / Refresh callback guard、
frame / app破棄順・analysis timer cleanup・pending event処理のtest fixture統一という最小対策へ分けて扱った。
`AppController.request_exit()`でcoalesced save timerを停止し、`destroy_wx_app()`を追加してB4 / B5の既存wx testへ限定移行した。
各対策を反映した組合せではexit code 0を
確認したが、各対策の個別寄与までは独立実験していない。1500ms splash契約、wx production API、VMD / audio /
fixed morph契約は変更していない。

## 8. 実装方針

### 8.1 Evidence matrixを先に固定する

各要求を「既存testで証明済み」「B6で追加testが必要」「manual GUIのみ」「MS26 deferred」に分類する。
既存testを無目的に複製せず、B6 testはBlock間の遷移と、従来個別testが同時に保証していない状態保持を
中心にする。

### 8.2 State identityを表示文字列から分離する

回帰assertionは、可能な限り次のimmutable値を使用する。

- `GenerationState`
- `OutputEditState`
- `OutputEditHistoryState`
- `BasePlanIdentity.digest`
- canonical adjustment snapshot
- effective output fingerprint
- diagnostic snapshot / failure identity
- stable preset id

RightPaneの日本語label、selector index、notice文面だけをstate正本としてassertしない。

### 8.3 Test-first、production変更なしを既定とする

B6専用testを追加し、現行production codeに通るべき契約を先に表現する。失敗時は、B6計画の誤り、
既存契約の例外、production defectを区別する。既存testを削除・skip・広いmockで無効化して通さない。

### 8.4 Splash testを時間分岐ごとに分ける

`gui_wx.app.time.time`を明示的な値列でpatchし、fast startupとslow startupを別testにする。
fast branchでは`CallLater`の呼出しとdelay、slow branchでは即時`MainFrame.Show`、TopWindow設定、
splash破棄、`CallLater`非呼出しを確認する。実時計やfull suiteの先行test数に依存させない。

時間assertion修正後も、全test pass表示／process exit code 1は別問題として扱う。既存repo内の安定した
wx teardown例を基準に、次の候補を一つずつ比較する。

1. `wx.App.Get() or wx.App(False)`によるapp lifetime共有
2. frame破棄後の`ProcessPendingEvents()`
3. controller save timer / analysis timerの停止とbinding ownerの破棄順
4. splash callbackのpending状態とtest終了順

最小再現で原因にならない候補は採用しない。test fixtureだけの問題ならproduction codeを変更せず、
該当testのlifecycleだけを補修する。production shutdownの欠陥が再現した場合はSection 7.3へ従う。

### 8.5 Documentationを実装正本から派生させる

- 利用者文書は操作と回復方法を説明し、内部class名を前面に出さない。
- Pipeline仕様はdata ownership、identity、precedence、consumer整合を記載する。
- GUI仕様はcontrol有効条件、Select / Apply分離、state transition、theme / scrollを記載する。
- Error仕様は失敗ごとの保持状態、mutation可否、再試行可能性を記載する。
- 利用者文書にはMMD側での最終確認が必要なことだけを記載し、内部MS番号を持ち込まない。
- routing文書は実装・自動検証・ユーザー報告・未検証を別々に記録する。

### 8.6 B6完了状態を段階的に記録する

自動検証完了時点では`Implemented / Automated Verification Passed / Manual GUI Pending`とする。
ユーザー報告を受領した後だけ`User Manual Test Passed`を追加する。実MMD未確認はどちらの時点でも
MS26 deferredとして残す。B7 Closeout判定は先行記載しない。

## 9. 詳細ステップ

### Step 1: 現行state / persistence / lifecycle matrixの再確認

- B4 lifecycle matrixとB5 GUI request guardをcurrent codeへ再照合する。
- startup load、input invalidation、analysis rollback、workspace reset、app closeのgeneration保持／破棄を列挙する。
- VMD / report / WARNING / diagnosticsの既存testがgeneration stateまで確認しているかを仕分ける。
- `presets.json`とINIを扱うtestがtemporary pathを使うことを確認する。

### Step 2: non-wx lifecycle回帰を追加

`tests/test_ms22_b6_lifecycle_regression.py`へ、少なくとも次を追加する。

- workspace resetでbase / output history / adjustment / selectionがclearされ、generation stateと
  recent file / dialog / theme等のapp設定が保持される。
- app restartを模した新stateではlast successful INI settings / active idだけを復元し、output historyを復元しない。
- invalid / unreadable INIはload errorを保持してdefault generation settingsへfallbackし、historyを生成しない。
- invalid user JSONでbuilt-inを保持し、missing user active idをCustomへ正規化してINI settingsを保持する。
- JSON mutation failureで旧fileと旧preset collectionを保持し、同一sessionのuser mutationを停止する。
- INI save failureはstoreを同一session内save-disabledにし、後続saveが`attempted=False`になる。
- 新しいstoreでのrestartはlast successful INIだけを復元し、失敗時のin-memory stateを永続化しない。
- same effective outputでpreset id / display nameだけが変わってもfingerprintが変わらない。
- generation settings、event override、application defaultの優先順位がlifecycle後も変わらない。

### Step 3: wx lifecycle横断回帰を追加

`tests/test_wx_ms22_b6_lifecycle_regression.py`へ、少なくとも次を追加する。

- TEXTあり／voice-onlyのsuccessでcurrent generationを新baseへ接続し、empty adjustment historyを初期化する。
- analysis startでgeneration + output historyをrollback候補へcaptureする。
- current failure / cancelで条件を満たす旧output history、selection、generationを復元する。
- morph upper mismatchではsuccess / rollbackをcommitせず、current generationを保持してbaseを無効化する。
- input change／workspace resetでbase-bound stateをclearし、generation stateを保持する。
- late / duplicate callbackがgeneration、history、selection、diagnostics、preset panel revisionを変更しない。
- shutdown / teardown後のcallbackがstate再同期や設定保存要求を発生させない。
- Busy / stale preset request、stale event mode requestがstore / output / historyを変更しない。
- Create / Update / DeleteのJSON write / replace failureがcurrent generation、output history、Preview、
  diagnosticsを変更せず、user mutationだけを停止する。
- foreground INI save failureはin-memory generation / historyを保持して初回だけ通知し、後続saveを試行しない。
- close-only INI save failureはblocking通知を出さずcloseを継続し、restart時はlast successful INIを使用する。
- invalid / unreadable INI startupはdefault generation、active Custom、base / historyなしへ安全に収束する。
- VMD cancel / writer failure、report cancel / writer failure後もgeneration、history、Preview、diagnosticsを保持する。
- effective output変更時だけWARNING再確認が必要になり、id / display変更だけでは再確認しない。

### Step 4: startup splash / wx teardownを決定論化

- fast branchの時刻を固定し、既存のdelay assertionを維持する。
- slow branchを追加し、即時表示とsplash破棄を確認する。
- 重複している`if __name__ == '__main__': unittest.main()`を一つへ整理する。
- 既知の17件組合せを起点に、B4、B5、splashの順序とapp lifetimeを縮小して原因を一つに限定する。
- test fixture原因なら、共有app、pending event処理、timer cleanupのうち必要な最小補修だけを行う。
- splash単独、既知17件組合せ、full suiteでpass表示とprocess exit code 0を確認する。

### Step 5: 利用者文書を同期

`README.md`と`readme_mmdautolip.txt`へ、次を実装済み範囲として追記する。

- 明示的な`ー`だけを長音として扱うこと
- `hold`と、長音終端で0へ減衰する`decay`
- built-in / user / Custom、SelectとApplyの違い
- user presetのcreate / update / rename / deleteと最大100件
- preset Applyとevent overrideのUndo / Redo
- terminal long-vowel eventだけの`継承 / hold / decay`
- generation settings / active presetは再起動後に復元し、history / adjustmentはsession外へ保存しないこと
- JSON / INI保存失敗時の利用可能範囲と回復方法
- 新規作業で保持するgeneration設定とclearするcurrent output
- 自動生成結果はMMD側で最終確認が必要であること。内部のMS26 deferred状態は利用者文書へ記載しない

### Step 6: 三つの正本仕様を同期

Pipeline仕様には、long-vowel token / timeline metadata、base identity、shared resolver、mode precedence、
output-only generation、Preview / writer / diagnostics / fingerprint、lifecycle matrixを追加する。

GUI仕様には、preset tab、Custom、stable id、Select / Apply分離、user mutation、terminal event mode control、
decay時tail disableとlatent保持、Busy / stale / dirty guard、theme / tab / scrollを追加する。

Error仕様には、preset JSONのinvalid / unsupported / duplicate / limit / read failure、write / replace failure、
INIのload / foreground save / close-only save failure、VMD / report failure、dialog cancel、late callbackごとの
保持状態、mutation / save availability、restart後の復元元を追加する。JSON write / replace failure後のuser mutationと
INI save failure後のsaveは同一session中停止し、原因解消後のreload / restartを回復境界とする。

Pipeline / Error仕様のanalysis terminal parameter記述は、B4実装どおりmorph upper limitだけへ更新し、
closing hold / softness / long-vowel modeはoutput-only transactionとして説明する。

### Step 7: 自動検証とdiff監査

- B6専用testを先に実行する。
- splash testを単独実行する。
- B2からB5の専用testを実行する。
- MS17 / MS19 / MS20 / MS21のlifecycle、worker、save、diagnostics回帰を実行する。
- full suite、compileall、diff checkを実行する。
- pass表示、failure / error、process exit codeを別々に記録する。
- `git diff --check`が未追跡fileを検査しないため、新規・未追跡fileは末尾空白検索とEOF確認を別に行う。
- 差分がB6 test / docsと、根拠付きconditional repairだけに限定されることを確認する。

### Step 8: Manual GUI確認と文書状態同期

自動検証後に、ユーザーへSection 11.7の確認事項を提示する。ユーザー報告前はmanual pendingとする。
通過報告を受領した後、Index、Roadmap、Block Breakdown、本書へ実施者・範囲・結果を記録する。
B7へ、自動検証値、manual evidence、未検証事項、P1 / P2 / P3残存を引き継ぐ。

#### 実装・自動検証結果

2026-08-11にB6専用non-wx lifecycle test 7件、wx lifecycle test 9件、splash test 3件を追加または更新した。
wx終了時のcoalesced save timer停止、`AutoLipToolApp`の遅延Layout / Refresh callback guard、
test teardown helperを限定補修した。
既知のB4 / B5 / splash組合せは18件がpass表示・process exit code 0となり、full suiteは713件がpass表示・
process exit code 0となった。`compileall src tests`と`git diff --check`もprocess exit code 0である。
自動検証にはユーザーGUI確認を含めない。2026-08-11にユーザーからSection 11.7の手動GUI確認項目を
すべて通過し問題なしとの報告を受領した。これはCodex自身のGUI実行結果とは扱わない。
実MMDでのVMD / WAV読み込み・リップ同期はMS26へ残す。

## 10. 状態遷移 / データ契約

### 10.1 Lifecycle matrix

| transition | generation / preset | base / history / selection | diagnostics / persistence |
| --- | --- | --- | --- |
| startup valid INI / JSON | settingsと解決済みactive id | baseなし、historyなし、selectionなし | last successful INIを表示 |
| startup missing INI | default generation、active idなし | baseなし、historyなし、selectionなし | load errorなし、defaultで起動 |
| startup invalid / unreadable INI | default generation、active idなし | baseなし、historyなし、selectionなし | load error保持、起動継続 |
| startup missing user JSON | INI settingsと解決済みbuilt-in / Custom | baseなし、historyなし | user mutation可能、built-in継続 |
| startup invalid user JSON | INI settings保持、built-inまたはCustom | baseなし、historyなし | user mutation停止、built-in継続。外部修復後のreload / restartで回復 |
| input change | generation保持 | base / output history / selection clear | stale diagnostics clear、old callback拒否 |
| analysis start | generation保持、edit拒否 | current outputをrollback候補へcapture | Busy、current jobだけ有効 |
| current success | current generation保持 | new base + empty adjustmentでhistory初期化 | shared resolverからsnapshot再構築 |
| failure / cancel rollback可 | captured generation復元 | captured history / selection復元 | failure / cancel規則どおり、saveabilityを再判定 |
| morph upper mismatch | current generation保持 | result / rollback非commit、base-bound state clear | 再解析待ち、保存不可 |
| late / duplicate callback | 変更なし | 変更なし | snapshot / fingerprint / save request変更なし |
| preset Apply / output edit | settings / active idをatomic commit | baseありなら1 transaction | resolver 1回、coalesced INI save |
| 別preset idのsame-settings Apply | settings保持、active id変更 | id-only transactionを1件記録 | fingerprint / WARNING確認を維持 |
| active presetのsame-id rename | settings / active id保持 | output history変更なし | 表示／report名だけ同期、fingerprint維持 |
| JSON write / replace failure | generation / active id保持 | history保持 | old JSON保持、failure notice、同一sessionのuser mutation停止 |
| foreground INI save failure | in-memory generation保持 | history保持 | 初回だけ警告、同一sessionのsave停止、次回起動はlast successful INI |
| save-disabled後の後続INI save | in-memory generation保持 | history保持 | `attempted=False`、追加警告なし、disk不変 |
| close-only INI save failure | in-memory generationをdiskへ反映できない | app終了によりhistory破棄 | blocking警告なしでclose、次回起動はlast successful INI |
| VMD / report cancel・failure | generation保持 | base / history / selection保持 | Preview / diagnostics / WARNING状態保持 |
| workspace reset | generation / active id保持 | workspace / base / history / selection clear | INI / JSONと保存済みoutputを削除しない |
| app close / restart | flush成功値だけ復元 | output history / adjustment / selectionは破棄 | session restoreを行わない |

### 10.2 Long-vowel mode resolution

```text
terminal continuation event explicit override
  > active GenerationSettings.long_vowel_mode
  > application default hold
```

- `None`はinheritであり、空文字やdisplay labelではない。
- `decay`はterminal frameでexact `0.0`とし、tailで後ろへ移動しない。
- decay中もlatent tail overrideをsnapshotへ保持し、hold復帰時に再利用する。
- non-terminal / non-long / stale / synthetic eventのmode requestはstateを変更しない。

### 10.3 Persistence ownership

| 保存先 | 保存する | 保存しない |
| --- | --- | --- |
| INI | generation settings、active preset id、theme、既存設定 | base、adjustment、output history、selection |
| `presets.json` | user preset schema version 1、stable id、display name、3 generation fields | built-in、active selection、history、input |
| session memory | current base、adjustment、generation、active id、Undo / Redo、selection | app終了後の復元データ |
| VMD / report | 現行effective outputまたはdiagnostic snapshot | editor history、preset JSON本体 |

### 10.4 Identity / WARNING contract

- base identityはlong-vowel metadataを含み、metadataが異なるplanへ旧adjustmentを適用しない。
- fingerprintはeffective morph frame / tail / diagnostic identityを正本とする。
- preset id、display name、Custom label、notice文面はfingerprintへ含めない。
- save failureやdialog cancelは確認済みfingerprintを無効化しない。
- effective outputが変わった場合だけ、同じ保存操作でWARNING再確認を要求する。

## 11. テスト方針

### 11.1 計画作成baseline

2026-08-11、基準HEAD `525ac1e`、`.venv`のPython 3.14.3で次を実行した。

| 対象 | 表示結果 | process exit code |
| --- | --- | --- |
| `tests/test_wx_startup_splash.py` | 2 passed | 0 |
| MS22 B2〜B5 + rollback / reset / voice-only / save / diagnostics 16 file | 122 passed | 0 |
| `tests`全体 | 696 passed | 0 |
| preset persistence / B4 / B5 / settings close / splash 47件 | 47 passed | 1 |
| B4 / B5 / splash縮小組合せ17件 | 17 passed | 1 |
| settings close単独 | 7 passed | 0 |

これはB6実装前baselineであり、B6専用test・文書同期・manual GUIの完了証拠ではない。
過去の全体負荷時にsplash test 1件が失敗した証拠と、plan再チェック時の全pass表示／exit code 1を、
今回のfull suite通過だけで消去しない。前者は時間assertion、後者はwx teardownとしてSection 9 Step 4で
別々に原因分離する。pass表示とprocess exit codeを混同せず、両方が成功するまで解消扱いにしない。

### 11.2 `tests/test_ms22_b6_lifecycle_regression.py`

- generation保持とworkspace local state破棄
- restart時のsettings復元とhistory非復元
- missing / invalid / unreadable INIのdefault fallback、load error、history非生成
- valid / missing / invalid preset JSONとactive resolution
- JSON write / replace failure後の旧file / collection保持とmutation unavailable
- foreground / close-only INI failure、save-disabled、last successful INI復元の分離
- mode precedence、metadata identity、fingerprint exclusion
- temporary path使用とrepository settings file不変

### 11.3 `tests/test_wx_ms22_b6_lifecycle_regression.py`

- TEXTあり／voice-only success
- analysis start、failure / cancel rollback、morph upper mismatch
- input change、workspace reset、new success
- late / duplicate callback、Busy / stale request
- shutdown / wx teardown、timer / callback後始末
- preset Create / Update / Delete persistence failure後のoutput / history不変
- invalid INI startupとforeground / close-only INI failureのGUI統合
- VMD / report cancel・failure
- Preview / writer / diagnostics同一context
- WARNING確認の再利用／再要求

### 11.4 `tests/test_wx_startup_splash.py`

- missing assetで起動継続
- fast startupで0〜1500msの`CallLater`
- slow startupで即時表示、TopWindow設定、splash破棄、`CallLater`なし
- test実行順と実時間に依存しないこと
- B4 / B5との組合せ終了時にprocess exit code 0となること

### 11.5 既存回帰

- MS22-B2のtoken、timeline metadata、resolver、adapter、import boundary
- MS22-B3のpreset schema、atomic persistence、INI active resolution
- MS22-B4のgeneration history、startup seam、diagnostics、rollback
- MS22-B5のpreset UI、event override
- existing settings close / coalesced save、wx app / frame teardown
- MS21のeffective shape、Preview、selected editor、save、Undo / Redo、state integration、sync efficiency
- MS20のdiagnostics、WARNING、report、lifecycle
- MS19のvoice-only、workspace reset、error handling
- MS17のworker、Busy、late result discard、MMD用WAV
- writer zero guard、same-vowel multipoint、pipeline Preview identity

### 11.6 実装後の検証コマンド

各コマンドを一つずつ実行し、実数と終了コードは実行結果で置き換える。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b6_lifecycle_regression.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms22_b6_lifecycle_regression.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_startup_splash.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b2_long_vowel_tokens.py tests/test_ms22_b2_timeline_metadata.py tests/test_ms22_b2_long_vowel_resolver.py tests/test_ms22_b2_long_vowel_adapters.py tests/test_ms22_b2_import_boundaries.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b3_generation_presets.py tests/test_ms22_b4_generation_history.py tests/test_wx_ms22_b4_generation_state.py tests/test_wx_ms22_b5_preset_ui.py tests/test_wx_ms22_b5_long_vowel_override.py
.\.venv\Scripts\python.exe -m pytest tests/test_settings_store.py tests/test_wx_ms14_b5_export.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms22_b4_generation_state.py tests/test_wx_ms22_b5_preset_ui.py tests/test_wx_startup_splash.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b7_analysis_rollback.py tests/test_wx_ms21_b7_state_integration.py tests/test_ms20_b7_diagnostics_state_integration.py tests/test_ms19_b8_workspace_reset.py tests/test_ms19_b4_voice_only_gui_state.py tests/test_ms19_b7_voice_only_error_handling.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_ms20_b6_report_save_flow.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms17_b8_late_worker_result_discard.py
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

`git diff --check`はtracked差分だけを対象とする。新規・未追跡のB6 test / planは、対象pathを明示した
`rg -n "[ \t]+$"`で末尾空白なしを確認し、`Get-Content -AsByteStream -Tail 1`でEOF byteがLF（10）で
あることを確認する。
`rg`のno-matchによるexit code 1は「末尾空白なし」として結果を明記し、pytestのexit code 1と混同しない。

package / buildはB6の変更対象外であり、dependency / package設定に意図しない差分がない限り実行しない。

### 実装後の実測結果

| 対象 | 表示結果 | process exit code |
| --- | --- | --- |
| `tests/test_ms22_b6_lifecycle_regression.py` | 7 passed | 0 |
| `tests/test_wx_ms22_b6_lifecycle_regression.py` | 9 passed | 0 |
| `tests/test_wx_startup_splash.py` | 3 passed | 0 |
| MS22-B2専用回帰 | 29 passed | 0 |
| MS22-B3〜B5専用回帰 | 45 passed | 0 |
| settings / export回帰 | 13 passed | 0 |
| B4 / B5 / splash組合せ | 18 passed | 0 |
| MS17〜MS21 lifecycle回帰 | 36 passed | 0 |
| save / diagnostics回帰 | 33 passed | 0 |
| `tests`全体 | 713 passed | 0 |
| `compileall src tests` | 成功 | 0 |
| `git diff --check` | 成功 | 0 |

初期baselineにあった17件組合せのexit code 1は、fixture lifecycle、coalesced save timer停止、
遅延Layout / Refresh callback guardの限定修正後、
18件（splash分岐追加を含む）でexit code 0へ収束した。2026-08-11にユーザーからmanual GUI確認通過・問題なしの
報告を受領したが、Codex自身はGUIを実行していない。次工程はMS22-B7 Closeoutである。

### 11.7 Manual GUI確認

自動検証後、ユーザーへ次を一つの確認表として提示する。

1. TEXTありで`ー`を含む素材を解析し、hold / decayのPreview差とdecay終端を確認する。
2. voice-onlyで書き起こしに`ー`を含む状態を確認・必要なら編集して再解析し、同じ導線を確認する。
3. built-in / user / CustomのSelectとApply、create / update / rename / deleteを確認する。
4. terminal long-vowel eventの継承・hold・decay、decay時tail無効化、hold復帰を確認する。
5. preset Applyとevent overrideをUndo / Redoし、Preview、Info / Warning、選択イベントtabを確認する。
6. VMD保存dialog cancel、diagnostic report cancel後に解析結果と編集状態が残ることを確認する。
7. 新規作業後に入力・Preview・historyがclearされ、generation設定／active presetが保持されることを確認する。
8. アプリ再起動後にgeneration設定／active presetが復元され、Undo / Redo historyが復元されないことを確認する。
9. invalid JSON / 保存失敗は自動testを主証拠とする。手動確認する場合は実user fileを破損させず、
   temporary copyまたは再作成可能な専用設定場所でbuilt-in継続とuser mutation停止を確認する。

Codex自身はGUIを起動していないが、2026-08-11にユーザーから上記項目の通過・問題なしとの報告を受領した。
手動確認はwx GUIの範囲に限定し、実MMDでのVMD / WAV読み込み・リップ同期はMS26へ残す。

## 12. 受け入れ条件

- B6専用testがlifecycle transition単位でgeneration、base、history、selection、diagnosticsの保持／破棄を固定する。
- TEXTあり／voice-onlyの双方でlong-vowel metadataとgeneration stateがcurrent job guardを迂回しない。
- input change、workspace reset、new success、app restartでsession stateの保持／破棄境界が契約どおりである。
- failure / cancel rollbackはcurrent job・base identity・morph upper条件を満たす場合だけ復元する。
- late / duplicate callback、Busy / stale requestはoutput、store、history、diagnosticsを変更しない。
- shutdown / wx teardown後にlate callback、timer、設定保存要求を残さない。
- missing / invalid / unreadable INI startupがdefault generation、active Custom、base / historyなしへ安全に収束する。
- preset JSON load / mutation failureとINI load / save failureが区別され、正常なin-memory outputを失わない。
- JSON write / replace failure後は同一sessionのuser mutationを停止し、旧JSONとcurrent outputを保持する。
- foreground INI save failureは初回だけ通知して同一sessionのsaveを停止し、close-only failureはblocking通知を
  出さず、どちらも次回起動でlast successful INIを復元する。
- VMD / report cancel・failureでPreview、generation、history、diagnostics、WARNING確認状態を失わない。
- Preview、writer、diagnostics、fingerprintが同じeffective outputを正本にする。
- splash testがfast / slow両分岐を実時間非依存で通過する。
- B4 / B5 / splashの既知組合せとfull suiteがpass表示・process exit code 0で終了する。
- README、配布用readme、Pipeline / GUI / Error仕様がMS22実装状態と一致する。
- routing文書がplanned / implemented / automated verified / user-reported / MS26 deferredを区別する。
- 新dependency、package、network、Qt、fixed morph、30fps、VMD、audio契約への差分がない。
- B6専用test、指定回帰、full suite、compileall、diff checkの表示結果とprocess exit codeを記録する。
- tracked差分に加え、新規・未追跡fileの末尾空白とEOFを確認する。
- user manual GUI結果は実施者と範囲を明記し、未実施ならpendingとする。
- 実MMD未確認をMS26へ維持し、B6またはMS22 Closeout完了の証拠へ含めない。
- P1 / P2が残る場合はB7へ進まず修正する。P3は影響と引き継ぎ先を明記する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 個別Block testの単純重複になり横断境界を証明しない | transition前後の複数stateを同じtestで比較し、既存testとの差を明記する |
| splash testがmachine speedで再び揺れる | `time.time`を分岐別に固定し、fast / slowを別testにする |
| 全test pass表示でもwx processがexit code 1になる | 既知17件組合せを保持し、app lifetime、pending event、timerを一つずつ分離してexit code 0を確認する |
| splash / save timerがwx teardown後へ残る | 原因確認後だけapp / frame破棄順、pending event、timer cleanupを限定補修する |
| intermittent failureをproduction defectと誤認する | branch conditionと再現条件を先に固定し、current codeの正規分岐を両方検証する |
| broad mockでjob guardやresolverを迂回する | state boundaryだけを注入し、current job / identity / immutable DTOを実経路で通す |
| testがrootのINI / `presets.json`を変更する | temporary directoryのpaired settings / preset storeを必須にする |
| invalid JSON testが既存user presetを破壊する | temporary fileだけにbroken JSONを書き、旧file保持も同じdirectoryで検証する |
| JSON / INI failureを同一sessionで再試行可能と誤記する | mutation / save unavailableとreload / restart回復境界をError仕様・testで一致させる |
| restart testがsession historyを誤って永続化する | 新しいcontroller / state instanceを作り、INI / JSON以外を渡さない |
| workspace resetでgenerationまでclearする | base-bound stateとbase-less `GenerationState`を別assertionにする |
| output-only設定変更をanalysis parameter変更へ戻す | morph upperだけのguardと、再解析不要のPreview更新を対で回帰する |
| preset id / display名変更でWARNING再確認が発生する | fingerprint除外契約とeffective output同一性を直接比較する |
| save failure testが状態を部分的に消す | failure前後のgeneration、history、snapshot、fingerprintをtupleで比較する |
| documentationがplanned機能をimplementedと書く | current code / test証拠がある項目だけ現在形にし、manual / MS26を分離する |
| user readmeと正本仕様で優先順位がずれる | 同じ3段階precedenceとdecay終端zeroを用語だけ変えて同期する |
| B6がB7 closeoutへ膨らむ | B6は回帰・docs・manual evidenceまでとし、A / B / C判定を記載しない |
| manual failure再現が危険または負担になる | JSON / save failureは自動testを主証拠とし、manualは安全に可能な範囲へ限定する |
| 実MMD未確認が完了記録へ混入する | 利用者文書はMMD側確認の必要性だけを維持し、MS26 deferredはrouting文書だけへ記録する |
| untracked新規fileを`git diff --check`だけで見落とす | path指定の末尾空白検索とEOF確認を別gateとして記録する |

## 14. Codex 実装時の注意

- 実装前に`git status`、branch、HEAD、本書、Block Breakdown、Index、Roadmapをcurrent stateへ再照合する。
- commandは一つずつ実行し、parallel / pipeline / chainを使わない。
- 既存変更・未追跡fileはユーザー所有として保護する。
- B6 test追加前に既存testのcoverageを読み、同じassertionを名前だけ変えて複製しない。
- test failure時はproduction、test、文書のどれが契約違反かを切り分け、期待値を弱めない。
- production修正が必要な場合はSection 7.3の手順で本書を更新してから最小repairする。
- `GenerationState`、`OutputEditState`、history、preset resultをmutable GUI dictへ置き換えない。
- repository rootのINI、`presets.json`、user input、保存済みVMD / WAVをtestで変更・削除しない。
- user presetの表示名をidentityにせず、stable idとcurrent store resolutionを使う。
- generation settingsをanalysis-affecting parameterへ戻さず、morph upper limitとの境界を維持する。
- decay exact zero、latent tail、mode precedenceをdocumentation都合で変更しない。
- manual GUIを実施していない場合は実施済みと記載しない。
- Qt / PySide6、network、external ASR、自動download、新dependencyを追加しない。
- fixed morph、30fps、VMD形式、audio三役、B3 JSON schema、MS21 fingerprint schemaを変更しない。
- dependency、package、release、tag、merge、pushを先行実施しない。
- B6完了時は確認ファイル、変更ファイル、実装内容、test結果、仕様逸脱、残課題、B7への引き継ぎを報告する。
