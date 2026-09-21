# MS21-B7 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B7 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B7_Implementation_Plan.md`
- 対象Block: MS21-B7
- Block名: State Integration / Regression / Docs / Adjustment Sync Efficiency
- 基準ブランチ: `feature/MS21-implementation`
- 実装開始基準コミット: `3ccf630 Plan MS21-B7 state integration and sync efficiency`
- 作成日: 2026-07-26
- 文書ステータス: Complete / Automated Verification Passed /
  User Manual GUI Verification Passed
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
- 前提計画:
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B6_Implementation_Plan.md`
- 追加補正計画:
  - `docs/Implementation_Plan/MS21-B7_Selected_Event_Tab_Auto_Switch_Additional_Fix_Plan.md`

MS21-B7は、B3からB6で実装したselection、adjustment、effective output、
Undo / Redoを既存workspace lifecycleへ統合し、TEXTあり / voice_only、MS20 diagnostics、
保存、再生、late callbackの回帰を固定するBlockである。

ユーザーから、B6段階のUndo / Redo処理が重いとの報告があった。B7ではこの効率化を
追加In Scopeとする。ただし履歴契約やeffective shape計算を簡略化せず、同一UI同期内の
重複計算と無関係な再描画だけを削減する。

## 2. 背景

### 2.1 B6完了状態

B6では次を実装・検証した。

- canonical adjustment snapshot全体のUndo / Redo
- 最大50 transaction、redo管理、no-op、coalescing
- Edit menu、Ctrl+Z / Ctrl+Y、reset selected / all
- Preview、RightPane、diagnostics、fingerprint、保存可否の再同期
- B6 core 12件、B6 wx 9件、最終全体602件と7 subtestsのpass
- ユーザー手動GUI確認通過

### 2.2 lifecycleの未完了点

B1では、解析開始時に旧base、adjustment、history、selectionをrollback候補として保持し、
current job成功時に破棄、failure / cancel時は再利用条件を満たす場合だけ復元する契約を
固定した。

現行実装は解析開始時に旧結果を保持し、cancel時は結果をそのまま再利用できる。一方、
failure時は `UiState.invalidate_analysis()` により旧base、adjustment、history、
selectionを破棄する。これはB1で定義したMS21最終契約と一致していない。

また、current analysis callbackはjob IDだけで判定しており、同じjob IDのterminal callbackが
重複した場合にterminal stateを再適用しない明示guardがない。

### 2.3 Undo / Redo効率の現状

選択eventがある解析済み状態で、現行 `MainFrame.sync_ui_state()` は次を個別に行う。

1. diagnostics用にbase inputとeffective planを構築する。
2. action state判定用にbase inputとbase identityを再構築する。
3. Preview用にbase inputとeffective planを再構築する。
4. selected editor用にbase inputとeffective planを再構築する。
5. 最後にPlaceholderContainer全体とParameterPanelを再描画する。

Undo / Redo handlerの事前guardを含めると、1操作で `BaseTimingPlanInput` は最大5回、
base identityは最大6回、`resolve_effective_shape_plan()` は3回構築される。
resolverはbase event、grouping、manual crossfade、comparison shape、normalizationを
走査するため、event数が多いほど重複コストが増える。

`apply_adjustment_update()` は更新後の `EffectiveShapePlan` を返しているが、現行MainFrameは
それをUI同期へ渡さず、commit後に再度resolverを実行している。

## 3. 目的

- input、parameter、analysis、Busy、reset、save、playbackのlifecycleへMS21状態を統合する。
- analysis開始時rollback snapshotとcurrent terminal callback契約を実装する。
- current job failure / cancel時の旧base再利用条件を実装する。
- late / duplicate callbackがbase、selection、adjustment、historyを変更しないようにする。
- failure rollback後はERRORを保持してVMD保存を禁止する。
- cancel rollback後はprior failureを復元し、存在しない場合だけcancel INFO付き
  diagnostics / fingerprintを再構築する。
- TEXTあり / voice_onlyの既存導線を維持する。
- 1回のUI同期でeffective planを最大1回だけ構築し、全consumerへ共有する。
- edit commit時は検証済み `AdjustmentUpdateResult.effective_plan` を再利用する。
- Undo / Redo時に無関係なplayback、waveform、parameter controlの再同期・再描画を省く。
- README、配布用readme、Pipeline / GUI / Error仕様をimplemented状態へ同期する。

## 4. In Scope

### 4.1 lifecycle

- input dialog cancel時のworkspace完全保持
- input commit、parameter変更、新規作業時のselection / adjustment / history破棄
- analysis開始時のrollback候補capture
- analysis success時の旧rollback候補破棄
- analysis failure / cancel時の条件付きrestore
- failure rollback後の再解析cancelでも既存ERRORと保存禁止を保持
- analysis開始前のselected event editor dirty入力guard
- analysis job開始時parameter snapshotとterminal時一致検証
- late / duplicate analysis callbackの完全不変
- late / duplicate audio worker terminal callbackとkind mismatchの完全不変
- Busy中のedit / reset / Undo / Redo lock
- VMD / report dialog cancelと保存失敗時の編集状態保持
- audio worker Busyとanalysis worker Busyの回帰
- TEXTあり / voice_only双方の状態遷移

### 4.2 Undo / Redo効率化

- 1同期1base input、1base identity、1effective planのderived context
- diagnostics、Preview、selected editor、action state間での同一context共有
- edit / reset selectedで得た検証済みeffective planの同期内再利用
- Undo / Redo / reset allでのeffective plan 1回構築
- adjustment-only同期scope
- adjustment-only時のplayback context再構築省略
- PlaceholderContainer全体とParameterPanelの不要な `Refresh()` 省略
- RightPane Info表示が同一内容の場合のwrap / layout省略
- resolver call countと対象Refresh call countのdeterministic test
- aggregate wx test終了処理の原因分離と最小補修。production実装前にexit code 0を必須とする

### 4.3 regression / docs

- B3 selection、B4 editor、B5 effective save / diagnostics、B6 history回帰
- MS17 late callback、MS19 voice_only / workspace reset、MS20 diagnostics回帰
- fresh-process import smokeによるB7 helperの循環参照防止
- README
- `readme_mmdautolip.txt`
- Pipeline Data Contract Specification
- GUI State Theme Specification
- Error Handling Specification
- MS21 plan / Breakdown / Index / Roadmapの進捗記録

## 5. Out of Scope

- effective shapeアルゴリズム、manual crossfade規則、normalization結果の変更
- resolver計算を省略する近似表示
- app再起動後のadjustment / history / rollback永続化
- process全体で保持する無期限cache
- timer、background thread、networkを使った遅延同期
- selection、viewport、playback、TEXT編集のUndo / Redo
- global parameter変更のUndo / Redo
- B1からB6で定義していない新しい編集field
- package、release、tag、merge、push
- dependency追加
- B7と無関係なtest framework全体の再設計
- MS22 preset / long-vowel先行実装
- fixed morph `あ / い / う / え / お` の変更
- VMD format、model name、Shift_JIS、30fps契約の変更
- Qt / PySide6、cloud、外部送信、telemetry、background通信

## 6. 前提条件

### 6.1 Git / environment

- `feature/MS21-implementation` 上で作業する。
- 実装開始基準は `3ccf630` とする。
- Python 3.11以上、repo-local `.venv`、wxPython主系を維持する。
- dependency、package、build、license変更は不要である。

### 6.2 current contract

- `AdjustmentLayerSnapshot`、`AdjustmentHistoryState`、
  `EffectiveShapePlan` はimmutableである。
- history current snapshotがadjustment currentの唯一の所有者である。
- Preview、VMD、diagnosticsは同じeffective plan semanticsを使う。
- WARNING確認済みfingerprintはhistory位置やselectionを含まない。
- analysis開始時にWARNING確認済みfingerprintをclearし、rollback時も復元しない。
- input / parameterが変化してbase identityを再現できない場合はrollbackしない。
- voice_only書き起こし編集適用後は旧planがinvalidであるためrollback候補を作らない。

### 6.3 計画作成時確認結果

- branch: `feature/MS21-implementation`
- 計画作成時production baseline HEAD: `4596d7e Implement MS21-B6 undo redo history`
- worktree: clean
- B6 history / wx、analysis、late callback、workspace、diagnostics関連47件:
  pass表示、process exit code 0
- voice_only、save、report、playback関連62件と7 subtests:
  pass表示、process exit code 0
- B6完了時の全体602件と7 subtests:
  pass表示、process exit code 0
- 現時点でproduction code、test code、dependency、build設定は変更していない。

### 6.4 実装状態整合レビュー

2026-07-26に本計画を現行production code、test、正本仕様へ再照合した。
初回レビューではP1なし、P2 3件、P3 1件を検出し、本計画内で解消した。

- P2: history未初期化時のempty snapshot生成とresolver内部identity生成が、
  「1同期1identity」制約と競合していた。historyなしではsnapshotなしでresolverを1回実行し、
  resultのcanonical snapshotからhistoryを初期化する順序へ固定した。
- P2: late / duplicate callback契約がanalysis callback中心で、現行audio workerが
  `COMPLETED / FAILED` 後の同一job ID callbackを再処理できる点を対象化していなかった。
  audio job ID、expected kind、RUNNING statusの三条件guardとduplicate terminal testを追加した。
- P2: 現行analysis failure handlerが `invalidate_analysis()` でold timing planを破棄するため、
  rollback identity検証の順序が未定義だった。rollback snapshotのold timing planとcurrent
  audio duration / shape parametersから、invalidate前にidentityを検証する順序へ固定した。
- P3: failure rollback時のbottom Statusを「専用StatusKeyまたは同等」としていたため、
  現行StatusKey mapに合わせて `StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK` へ固定した。

修正後の再照合では残存P1 / P2 / P3なしと判定した。production code、test code、
dependency、build設定は変更していない。この時点の次工程はB7 pre-implementation checkだった。

### 6.5 2026-07-27 pre-implementation check補正

2026-07-27の実装前チェックではP1なし、P2 4件、P3 1件を検出した。セッションログを
遡り、B1のrollback最終契約、B2の循環import回避、B6のdirty入力保護と照合した。
同じ根本原因を別表現で再登録せず、次の固定IDで影響箇所を一括補正する。

| ID | 重要度 | 根本原因 | plan上の閉鎖条件 | 状態 |
| --- | --- | --- | --- | --- |
| B7-PRE-001 | P2 | failure rollback後の既存ERRORをretry / cancelで復元するpayloadがない | rollback DTOへprior failureを保持し、cancel時ERROR優先、success時だけ破棄する | plan上closed |
| B7-PRE-002 | P2 | analysis開始前のselected editor dirty入力guardがない | job ID更新、diagnostics clear、Busy移行より前に既存dirty guardで開始を拒否する | plan上closed |
| B7-PRE-003 | P2 | base identityがoutput-affecting parameterを含まないのにidentity一致へ依存していた | 3 parameterのimmutable snapshotをidentityと別に比較し、mismatch terminalをfail closedにする | plan上closed |
| B7-PRE-004 | P2 | aggregate wx testがpass表示後にexit code 1となる | production変更前にwx aggregateとfull suiteをexit code 0へ戻すStep 0を追加する | closed (2026-07-27) |
| B7-PRE-005 | P3 | 実装開始基準がB7 plan commit前を指していた | 基準を`3ccf630`へ更新する | closed |

B7-PRE-004は受け入れ基準を非zero許容へ弱めて閉じない方針で、実装前にはtest teardownだけを
原因分離・最小補修し、wx aggregateとfull suiteのexit code 0を確認するまでproduction codeを
変更しない、というgateとして運用した。2026-07-27実装前時点の測定値は次のとおりである。

- B6 history / Undo / Redo 21件: pass表示、process exit code 0
- analysis / late / diagnostics / reset 32件と7 subtests: pass表示、process exit code 0
- B3からB5回帰40件: pass表示、process exit code 0
- voice_only / warning / report / playback / viewport 70件: pass表示、process exit code 0
- full suite 602件と7 subtests: 2回ともpass表示、process exit code 1
- wx抽出91件: pass表示、511件deselected、process exit code 1
- `compileall src tests`: process exit code 0
- `git diff --check`: process exit code 0

Pythonは3.14.3、wxPythonは4.2.5、wxWidgetsは3.2.9だった。exit code 1の直接原因は
未確定であり、Python / wx versionだけを原因と断定しない。

### 6.6 2026-07-27実装結果

MS21-B7 production実装と自動検証を完了した。この時点ではユーザー手動GUI確認前であり、
後続の確認で追加tab補正要望が提示された。

- `analysis_rollback.py`へjob-local rollback DTO、prior failure、parameter snapshot、
  identity / parameter別restore判定を追加した。
- `ui_sync_context.py`へ1同期限定のbase input / identity / effective plan共有contextと
  effective plan hint検証を追加した。
- `MainFrame`へdirty入力guard、active terminal guard、success / failure / cancelの分離、
  failure / cancel rollback、parameter mismatch fail-closed、adjustment-only同期を接続した。
- `AppController`のaudio terminal受理条件をcurrent job ID、expected kind、
  `RUNNING`状態の三条件へ固定した。
- RightPane Infoは同一内容時のwrap / layoutを省略する。
- startup splash testが実SplashScreenを破棄せずinterpreter shutdown時のwx access
  violationを起こすことを特定した。SplashScreenをtest doubleへ置換し、App / Frameの
  teardown所有権を明示してwx aggregateのprocess exit code 0を回復した。
- B7 helperはpackage `__init__`からexportせず、core / writerからGUIへの逆importを追加していない。
- B7専用15件、B3からB6回帰61件、lifecycle回帰47件と7 subtests、
  wx aggregate 97件、full suite 617件と7 subtestsはすべてpass表示・process exit code 0だった。
- `compileall src tests`と`git diff --check`はprocess exit code 0だった。
- dependency、package、build、license、fixed morph、VMD format、network契約は変更していない。

### 6.7 2026-07-27 Selected Event Tab Auto-Switch追加補正

ユーザーはB7手動GUI確認を実施し、Previewタイムラインで単母音eventを選択した場合に
RightPaneの「選択イベント」タブへ自動切替する小規模補正を要望した。

- 追加補正計画を作成し、現行selection commit、RightPane Notebook、Undo / Redo、
  rollback同期へ照合した。残存P1 / P2 / P3なしと判定した。
- `RightPane.show_selected_event_tab()`を追加し、page indexを固定せず
  `FindPage(panel_selected_event)`で解決する。
- Preview user clickのcanonical commit成功後だけ`ChangeSelection()`し、
  same-event再clickでもeditor tabへ戻る。
- stale、Busy、invalid request、通常syncではcurrent tabを維持する。
- tab切替を`sync_ui_state()`、`update_selected_event_display()`へ入れていないため、
  Undo / Redo、analysis rollback、event edit / resetはInfo / Warning閲覧を中断しない。
- RightPane 3件、Preview selection 6件、Undo / Redo・B7 lifecycle 12件、
  wx aggregate 90件、full suite 618件と7 subtestsはpass表示・各process exit code 0だった。
- 自動テストのanalysis failure経路が実`wx.MessageBox`を開いて自動進行を停止する問題は、
  productionの通知契約を変えず、該当test内でMessageBoxをmockして呼び出しを検証する
  限定補修を行った。補修後もfull suite 618件と7 subtestsはpass表示・process exit code 0だった。
- 2026-07-27にユーザーから、追加補正を含むMS21-B7範囲の手動GUI確認は通過し、
  問題なしと報告された。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/gui_wx/ui_sync_context.py` | wx / UiState / MainFrame非依存のimmutable derived contextとhint validation |
| 新規 `src/gui_wx/analysis_rollback.py` | wx / UiState / MainFrame非依存のrollback DTO、parameter snapshot、pure再利用判定 |
| `src/gui_wx/ui_state.py` | failure / cancel復元後状態、専用StatusKey。B7 helperをimportしない |
| `src/gui_wx/main_frame.py` | rollback snapshot所有、terminal guard、single-pass同期、adjustment-only同期 |
| `src/gui_wx/right_pane.py` | Info snapshot同値時の不要wrap / layout抑止 |
| `src/gui_wx/app_controller.py` | audio worker Busy、input commit、reset、late / duplicate terminal callbackとkind guard |

新規moduleは責務分離が実装時にも有効な場合だけ作成する。同等のpure DTO / helperを既存moduleへ
小さく配置できる場合は、不要なfile追加を避けてよい。

新規helperを作る場合も`gui_wx.__init__`や`src.core.__init__`からre-exportしない。
`MainFrame`だけがconcrete helper moduleをimportし、helperは`UiState`、`MainFrame`、
`AppController`、`RightPane`をimportしない。rollback snapshotは`MainFrame`が所有し、
`UiState`とhelperの相互importを作らない。

### 7.2 関連確認対象

- `src/core/effective_shape_plan.py`
- `src/core/event_adjustment.py`
- `src/core/event_adjustment_history.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/selected_event_editor.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/preview_panel.py`
- `src/vmd_writer/effective_shape_adapter.py`

### 7.3 test

- 新規 `tests/test_ms21_b7_analysis_rollback.py`
- 新規 `tests/test_ms21_b7_ui_sync_context.py`
- 新規 `tests/test_ms21_b7_audio_worker_terminal.py`
- 新規 `tests/test_ms21_b7_import_boundaries.py`
- 新規 `tests/test_wx_ms21_b7_state_integration.py`
- 新規 `tests/test_wx_ms21_b7_sync_efficiency.py`
- `tests/conftest.py` または原因分離で特定した既存wx testの最小teardown補修
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_ms19_b4_voice_only_gui_state.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms20_b6_report_save_flow.py`
- playback / viewport / warning fingerprint関連test

### 7.4 docs

- 新規 `docs/Implementation_Plan/MS21-B7_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`

`docs/repo_milestone.md` と `docs/Version_Control.md` の最終同期は、B7実装結果を確認してから
必要箇所だけtargeted updateする。計画作成時に巨大履歴全文を読み込まない。

## 8. 実装方針

### 8.1 analysis rollback snapshot

analysis rollback snapshotは次だけを保持する。

- analysis job ID
- old `current_timing_plan`
- old base plan identity
- old `AdjustmentHistoryState`
- old selected source event index
- old selected base identity digest
- analysis開始直前の `DiagnosticFailureInput | None`
- immutable analysis parameter snapshot:
  - morph upper limit
  - closing hold frames
  - closing softness frames

保持しないもの:

- wx widget、PreviewData、`OutputDiagnosticsSnapshot`等のdiagnostics表示object
- playback再生中状態
- WARNING確認済みfingerprint
- file dialog、保存dialog、recent history
- analysis worker object

rollback snapshotはcurrent job専用であり、terminal callback完了後またはworkspace破棄後にclearする。
snapshotは`MainFrame`が所有する。`UiState`へjob-local DTOを永続fieldとして追加せず、
`analysis_rollback.py`から`ui_state.py`をimportしない。

### 8.2 capture条件

analysis開始直前に次をすべて満たす場合だけcaptureする。

1. `analysis_result_valid is True`
2. `analysis_pending_rebuild is False`
3. `current_timing_plan` と音声durationからbase inputを構築できる
4. current adjustment historyが存在する場合、そのbase identityが一致する
5. current adjustment historyにpending editが残っていない
6. selectionが存在する場合、そのbase identityが一致する
7. capture job IDが開始するcurrent analysis job IDと一致する
8. morph upper limitがfiniteかつ0以上、hold / softnessが0から100の整数である

条件を満たさない場合はrollback snapshotを `None` とする。invalidな旧planや
voice_only編集適用前planを復元候補へ昇格させない。

selected event editorにdirty直接入力がある場合はcapture可否判定へ進まない。
job ID更新、diagnostics clear、parameter読取、Busy移行より前に解析開始を拒否し、
既存の「Enterで値を確定するか、入力内容を修正してください。」を表示する。
dirty値を自動commit、暗黙破棄、Busy同期によるcontrol上書きのいずれにも流さない。

### 8.3 terminal callback

- terminal callbackはjob ID一致に加え、analysis jobがactiveかを確認する。
- capture時parameter snapshotとterminal時の3 parameterが完全一致することを確認する。
- success / failure / cancelの最初の1回だけterminal transitionを実行する。
- parameter mismatch:
  - success resultをcommitせず、failure / cancelでもrollbackしない。
  - current analysis jobをterminalへ移し、Busyを解除する。
  - `invalidate_analysis()` 後の再解析待ちを維持し、旧history / selectionを復元しない。
  - mismatchを通常success、failure rollback、cancel rollbackとして表示しない。
- success:
  - 新planをcommitする。
  - old diagnostic failure、adjustment / history / selectionとrollback snapshotを破棄する。
- failure:
  - `invalidate_analysis()` を呼ぶ前にrestore可否を判定する。
  - rollback snapshotのold timing planとcurrent audio durationからcomparison base inputと
    identityを構築する。
  - identity一致に加え、capture時とterminal時の3 parameterが完全一致する場合だけ
    old base / adjustment / history / selectionを復元する。
  - diagnostic failure ERRORを保持し、VMD保存を禁止する。
  - Previewと編集は復元した旧baseに対して再開できる。
  - 不一致またはsnapshotなしの場合だけ `invalidate_analysis()` で破棄し、
    その後にdiagnostic failureを設定する。
- cancel:
  - 同じidentity条件で旧状態を復元する。
  - rollback snapshotにprior diagnostic failureがある場合はそれを復元する。
  - prior failureがない場合だけcancel INFO付きdiagnostics / fingerprintを再構築する。
  - prior failureがある場合はERROR優先によりcancel INFOを抑制し、VMD保存不可を維持する。
  - WARNING確認済みfingerprintは復元しない。
  - snapshotなしでは現在のinvalid / empty状態を維持する。
- late / duplicate analysis callback:
  - base、selection、adjustment、history、diagnostics、Previewを変更しない。

failure rollback用に `StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK` を追加する。
表示文言は「解析に失敗しました（前回結果を表示中・保存不可）」とし、
diagnostic ERRORと矛盾させない。

### 8.4 audio worker terminal guard

audio worker resultは、次をすべて満たす場合だけ処理する。

1. callbackのaudio job IDがcurrent job IDと一致する。
2. current `AudioWorkerState.kind` がcallbackのexpected kindと一致する。
3. current statusが `RUNNING` である。

`COMPLETED / FAILED / CANCELLED / DISCARDED` はterminal statusとし、同じjob IDでも
以後のsuccess / error callbackを拒否する。PROBE successから同一job IDで
ANALYSIS_WAV workerへ移行した後のduplicate PROBE callbackはkind mismatchとして拒否する。
cancel callbackは既存どおり `CANCELLING` とkind一致を要求する。

duplicate callback拒否時はUiState、selection、adjustment、history、waveform、settings、
dialog、status表示を変更しない。

### 8.5 single-pass UI sync context

`sync_ui_state()` の開始時に、current stateから1同期専用のimmutable contextを作る。

```text
UiSyncContext
  base_input
  base_plan_identity
  effective_shape_plan
  effective_writer_input_state
  effective_writer_input_failure_reason
```

- base inputは最大1回構築する。
- base identityは最大1回構築する。
- effective planは最大1回resolveする。
- context構築前にinput modeをrefreshする。
- history未初期化時はidentityやempty snapshotを先に別計算しない。
  `resolve_effective_shape_plan(base_input, None)` を1回実行し、返却された
  `effective_plan.canonical_adjustment_snapshot` からhistoryを初期化する。
- history初期化に使用した同じeffective planを、その同期のdiagnostics、Preview、
  selected editorへ渡す。初期化後にresolverを再実行しない。
- history初期化済みの場合はhistory current snapshotをresolverへ渡し、返却planのidentityを
  context identityとして採用する。
- resolver実行時は返却されたeffective planのidentityを採用し、resolver前後で
  `build_base_plan_identity()` を重複実行しない。
- contextはその `sync_ui_state()` 呼び出し内だけで使用し、UiStateへ永続保存しない。
- diagnostics、action state、Preview、selected editorは同じcontextを受け取る。
- invalid contextではconsumerごとに別々のfallback計算をせず、同じfailure reasonで
  fail closedにする。

### 8.6 effective plan hint

edit / reset selectedでは `apply_adjustment_update()` が返すeffective planをhintとして
同期入口へ渡す。

hintは次をすべて満たす場合だけ再利用する。

- hintのbase identityがcurrent base identityと一致する。
- hintのcanonical snapshotがhistory current snapshotと一致する。
- current analysis job / Busy / pending rebuild状態と矛盾しない。

不一致hintを表示へ使わない。不一致時はcurrent stateから最大1回だけ再計算する。
永続cacheや前回sync contextの使い回しは行わない。

### 8.7 adjustment-only sync

history navigation、event edit、reset selected / allはadjustment-only syncを使う。

同期するもの:

- output diagnostics snapshot
- VMD / report saveabilityとmenu / button action state
- bottom Status
- RightPane Info / Warning / selected editor
- Preview dataとselection

同期しないもの:

- playback context
- waveform data
- viewport
- parameter control値
- `ParameterPanel.Refresh()`
- `PlaceholderContainer.Refresh()` による子window全体再描画

PreviewPanel自身はdata更新時の既存 `Refresh()` を維持する。full syncはinput、analysis、
Busy、theme、playback等の既存入口で使用する。

### 8.8 RightPane layout抑止

- formatted Info text、reanalysis表示状態、suffixが前回と同一ならlabel更新と
  `_update_wrap()` を省略する。
- Warning rowsは既存signature抑止を維持する。
- selected editorはrequested / effective値が変わるため必要な更新を行う。
- theme変更時は同値判定に関係なくstyle refreshを実行する。

### 8.9 docs

- README / 配布用readmeへevent選択、個別補正、Undo / Redo、reset、session内履歴を記載する。
- failure時に旧結果を表示しても保存不可、cancel時は旧結果を再利用できることを記載する。
- Pipeline仕様へbase / adjustment / effective / history / rollback契約を同期する。
- GUI仕様へEdit menu、shortcut、Busy、dirty入力、adjustment-only同期を同期する。
- Error仕様の「analysis failureで常にcurrent plan破棄」という旧記述を、条件付きrollbackへ
  更新する。rollback failureでは従来どおり破棄する。
- implemented、verified、planned、B8 closeout完了（A）を区別する。

### 8.10 import boundary / 循環参照防止

過去セッションで、`src/core/__init__.py -> pipeline -> src.vmd_writer -> writer`へ
core側のdirect importを追加すると循環することを確認済みである。B7では既存の
`src.core` / writer公開境界を変更せず、次の一方向だけを許可する。

```text
gui_wx.main_frame
  -> gui_wx.analysis_rollback
      -> src.core.effective_shape_plan
      -> src.core.event_adjustment_history
      -> src.core.output_diagnostics
  -> gui_wx.ui_sync_context
      -> src.core.effective_shape_plan
  -> gui_wx.ui_state
      -> existing src.core public/domain modules
```

禁止する依存:

- `src.core.*`、`src.vmd_writer.*`からB7の`gui_wx.*` helperをimportする
- `analysis_rollback.py`または`ui_sync_context.py`から`main_frame.py`、
  `ui_state.py`、`app_controller.py`、`right_pane.py`をimportする
- `ui_state.py`からB7 helperをimportして相互参照を作る
- `gui_wx.__init__.py`、`src.core.__init__.py`、`src.vmd_writer.__init__.py`へ
  B7 helperをre-exportする
- `TYPE_CHECKING`以外の遅延importで循環を隠す

新規helperはwx非依存とし、MainFrameがUiStateからprimitive / immutable domain値を取り出して
pure helperへ渡す。fresh-processでhelper先行、MainFrame先行の両import順を検証する。

## 9. 詳細ステップ

### Step 0: aggregate wx test exit gate

production codeへ着手する前に次を実施する。

1. `pytest tests -q -k "wx"`と`pytest tests -q`のpass表示 / exit code 1を再現する。
2. wx test file群を決定的に分割し、終了コード1となる最小の組み合わせと順序を特定する。
3. shared `wx.App`、per-test `wx.App.Destroy()`、Frame破棄、
   `ProcessPendingEvents()`、`ExitMainLoop()`の所有権を確認する。
4. `tests/conftest.py`または原因testのteardownだけを最小補修する。
5. wx aggregateとfull suiteの両方がpass表示・process exit code 0になることを確認する。

test分割実行を最終gateの代替にせず、nonzero終了を既知baselineとして許容しない。
Python / wx version変更、dependency変更、production code変更が必要なら作業を止めて
ユーザーへ確認する。

### Step 1: baselineとcall-path test

1. B6専用testとB7 lifecycle対象testを再実行する。
2. resolver、base input、identity、Refreshの現行call countをtest fixtureで固定する。
3. elapsed timeを自動testの合否条件にせず、構造的な重複回数を基準にする。

### Step 2: rollback DTO / pure validation

1. immutable rollback snapshotを追加する。
2. invalid timing plan、identity mismatch、stale job、invalid selectionをrejectする。
3. WARNING確認済みfingerprintをpayloadへ含めない。
4. pure unit testを追加する。

### Step 3: MainFrame analysis lifecycle

1. selected editor dirty入力を状態変更前に拒否する。
2. analysis開始前にpending gestureを確定する。
3. current valid state、prior failure、3 parameterだけrollback captureする。
4. active terminal guardとparameter snapshot guardを追加する。
5. parameter mismatchはresultをcommit / restoreせず、Busy解除と再解析待ちを確定する。
6. failureではrollback snapshotのold timing planとcurrent audioからidentityを構築し、
   capture済みparameter snapshotとの別比較を含めてinvalidate前にrestore可否を判定する。
7. success / failure / cancelを別handlerへ分ける。
8. cancelではprior failureを復元し、存在しない場合だけcancel INFOを生成する。
9. restore成功時はeditor revisionを更新し、開始前のtyped requestをstaleにする。
10. terminal後にrollback snapshotをclearする。

### Step 4: audio worker terminal guard

1. current audio worker result guardへexpected kindを追加する。
2. success / errorはcurrent statusが `RUNNING` の場合だけ処理する。
3. `COMPLETED / FAILED / CANCELLED / DISCARDED` 後のduplicate callbackを拒否する。
4. PROBEからANALYSIS_WAV移行後のduplicate PROBEをkind mismatchで拒否する。
5. cancelの既存 `CANCELLING` guardを維持する。

### Step 5: diagnostics / status

1. failure rollback後もdiagnostic failureを保持する。
2. VMD保存可否とreport本文のsaveabilityを同じERRORから保存不可へする。
3. cancel rollbackではprior failureを復元し、ない場合だけcancel INFOを生成する。
4. old WARNING確認済みfingerprintを復元しない。
5. `StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK` と固定表示文言を追加する。

### Step 6: single-pass context

1. 1同期専用contextを追加する。
2. historyなしではresolver resultのcanonical snapshotからhistoryを初期化する。
3. diagnosticsへcontextのeffective plan / writer stateを渡す。
4. action stateへbase validityを渡し、base input再構築を除去する。
5. Previewへ同じeffective planを渡す。
6. selected editorへ同じeffective planとbase inputを渡す。
7. invalid contextのfailure reasonを統一する。

### Step 7: hint reuse

1. edit / reset selectedのupdate resultをsyncへ渡す。
2. identity / snapshot完全一致を検証する。
3. stale hint testを追加する。
4. Undo / Redo / reset allはcurrent snapshotから1回resolveする。

### Step 8: adjustment-only render

1. full syncとadjustment-only syncのscopeを分ける。
2. history navigationとevent adjustment入口をadjustment-onlyへ切り替える。
3. playback / waveform / parameterの非更新をtestする。
4. PreviewとRightPaneの必要更新は維持する。

### Step 9: lifecycle regression

1. input dialog cancel / commitを検証する。
2. parameter invalidationを検証する。
3. analysis success / failure / cancelをrollbackあり / なしで検証する。
4. analysisとaudio worker双方のlate / duplicate callbackを検証する。
5. workspace reset、save cancel / failure、Busyを検証する。
6. TEXTあり / voice_onlyを検証する。

### Step 10: docs

1. end-user docsへ操作を追加する。
2. Pipeline / GUI / Error仕様を実装結果へ同期する。
3. Block Breakdown、Index、RoadmapをB7実装結果へ同期する。
4. B8は別計画でCloseout監査を実施し、A判定をrouting文書へ同期する。

### Step 11: validation

1. fresh-process import smokeをhelper先行 / MainFrame先行で実行する。
2. B7専用testを実行する。
3. B3からB6のMS21回帰を実行する。
4. MS17 / MS19 / MS20 lifecycle回帰を実行する。
5. wx aggregate、full test、compileallを実行し、各process exit code 0を確認する。
6. `git diff --check` とdiff scopeを確認する。

## 10. 状態遷移 / データ契約

### 10.1 analysis lifecycle

| event | base / adjustment / history | selection | diagnostics / save |
| --- | --- | --- | --- |
| input dialog cancel | 保持 | 保持 | 保持 |
| input commit | clear | clear | 再解析待ち / 保存不可 |
| parameter変更 | clear | clear | 再解析待ち / 保存不可 |
| analysis開始要求・editor dirty | 完全不変 | 保持 | 開始拒否、確定または修正を案内 |
| analysis開始・rollback可能 | rollback候補として保持、編集lock | 表示のみ保持、lock | Busy、確認済みWARNING clear |
| analysis開始・rollback不可 | 候補なし | 現行invalid状態 | Busy |
| current success | 新base、empty history | clear | 新diagnostics |
| current failure・restore可 | 旧state復元 | 旧selection復元 | failure ERROR保持、保存不可 |
| current failure・restore不可 | clear | clear | failure ERROR、保存不可 |
| current cancel・restore可・prior failureなし | 旧state復元 | 旧selection復元 | cancel INFO、WARNING再確認 |
| current cancel・restore可・prior failureあり | 旧state復元 | 旧selection復元 | prior ERROR復元、cancel INFO抑制、保存不可 |
| current cancel・restore不可 | 現行invalid状態 | 現行状態 | cancel / blocking状態 |
| current terminal・parameter mismatch | clear / restore禁止 | clear | 再解析待ち / 保存不可 |
| late / duplicate callback | 完全不変 | 完全不変 | 完全不変 |
| workspace reset | clear | clear | clear |

### 10.2 sync context validity

| condition | effective plan | writer state |
| --- | --- | --- |
| valid analysis / matching identity | 1回resolveまたはvalid hint | ready |
| valid previewだがfailure rollback ERRORあり | 1回resolve | ready DTOを生成してもdiagnostics ERRORで保存禁止 |
| Busy | 表示維持に必要ならcurrent stateから共有 | not_applicable |
| analysis pending / no plan | none | not_applicable |
| base input / identity mismatch | none | invalid |
| stale hint | 使用禁止、currentから最大1回再計算 | current stateに従う |

### 10.3 performance invariant

- 1回の `sync_ui_state()` 内でbase input構築は最大1回。
- 1回の `sync_ui_state()` 内でbase identity構築は最大1回。
- 1回の `sync_ui_state()` 内でeffective resolver実行は最大1回。
- valid edit result hint使用時、commit後syncでresolverを追加実行しない。
- adjustment-only syncはplayback context更新、ParameterPanel全体Refresh、
  PlaceholderContainer全体Refreshを呼ばない。
- fingerprint、Preview、selected editorが異なるeffective planを参照しない。

## 11. テスト方針

### 11.1 rollback core

- valid snapshot capture
- invalid analysis / pending rebuildではcaptureなし
- base identity mismatch reject
- stale job reject
- selection identity mismatch reject
- WARNING確認済みfingerprint非保持
- prior `DiagnosticFailureInput`の保持と表示snapshot非保持
- morph upper limit / hold / softness parameter snapshot validation
- restore identityはsnapshot old timing planとcurrent audioからinvalidate前に判定し、
  parameter snapshotはidentityと別に完全一致を検証

### 11.2 analysis integration

- valid old resultからのsuccessでold history破棄
- valid old resultからのfailureでbase / history / selection復元
- failure ERROR保持とVMD保存禁止
- valid old resultかつprior failureなしのcancelで復元とcancel INFO
- failure rollback後のretry / cancelでprior ERROR保持、cancel INFO抑制、保存不可
- cancel後のWARNING再確認
- selected editor valid / invalid dirty入力では解析開始完全不変
- success / failure / cancelの各parameter mismatchでcommit / restore禁止、Busy解除
- rollback候補なしfailure / cancel
- same job duplicate terminal callback完全不変
- old job late callback完全不変
- editor revision更新によるold request reject
- failure rollback StatusKeyと固定文言

### 11.3 audio worker terminal

- current job ID / expected kind / RUNNINGの正常受理
- COMPLETED後のduplicate success reject
- FAILED後のduplicate error reject
- PROBEからANALYSIS_WAV移行後のduplicate PROBE reject
- MMD_WAV duplicate success reject
- kind mismatch callback完全不変
- cancel callbackのCANCELLING / kind guard維持

### 11.4 efficiency

mockのelapsed時間ではなくcall countを検証する。

- selected eventありfull syncでresolver 1回
- history未初期化syncでresolver 1回、identity 1回、同resultからhistory初期化
- Undoでhistory navigation後resolver 1回
- Redoでhistory navigation後resolver 1回
- edit result hintでsync追加resolver 0回
- stale hintで最大1回recompute
- diagnostics / Preview / editorのsnapshot identity一致
- adjustment-only syncでplayback同期0回
- adjustment-only syncでcontainer / parameter broad Refresh 0回
- PreviewPanel自身のRefreshは維持
- unchanged Info textでwrap / layout 0回

任意の非gating計測として、長いsynthetic timelineでUndo / Redo前後のelapsed timeを記録してよい。
OS負荷に左右される固定millisecond値をCI acceptanceには使わない。

### 11.5 lifecycle / regression

- input cancel / commit
- parameter invalidation
- Busy action state
- workspace reset
- save dialog cancel / save failure
- report cancel / failure
- playback / pan / zoom
- TEXTあり / voice_only
- B3 selection、B4 editor、B5 save / diagnostics、B6 history

### 11.6 実行候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q -k "wx"
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -c "import gui_wx.analysis_rollback; import gui_wx.ui_sync_context; import gui_wx.main_frame"
.\.venv\Scripts\python.exe -c "import gui_wx.main_frame; import gui_wx.analysis_rollback; import gui_wx.ui_sync_context"
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b7_analysis_rollback.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b7_ui_sync_context.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b7_audio_worker_terminal.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b7_import_boundaries.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b7_state_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b7_sync_efficiency.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b6_adjustment_history.py tests/test_wx_ms21_b6_undo_redo.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b4_analysis.py tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py tests/test_ms20_b7_diagnostics_state_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b3_preview_hit_test.py tests/test_wx_ms21_b3_preview_selection.py tests/test_ms21_b4_selected_event_editor.py tests/test_wx_ms21_b4_selected_event_editor.py tests/test_ms21_b5_adjusted_vmd_save.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

各test commandはpass表示とprocess exit codeを分けて報告する。

### 11.7 ユーザー手動GUI確認

1. 長めの解析結果で複数回Undo / Redoし、B6時点より操作待ちが軽減していること。
2. Undo / RedoでPreview、editor値、diagnostics、保存可否が同時に切り替わること。
3. 再解析をcancelすると旧補正と履歴が復元し、Undo / Redoできること。
4. 再解析が失敗すると旧Previewと編集は復元するが、VMD保存はできないこと。
5. failure rollback表示中に再解析してcancelしても、既存ERRORとVMD保存禁止が残ること。
6. selected event editorへ未確定値がある状態では解析を開始せず、入力を消さないこと。
7. 再解析成功では旧補正と履歴を持ち越さないこと。
8. TEXT / 音声dialog cancelで現行編集が消えないこと。
9. input commit、parameter変更、新規作業で旧履歴をUndoできないこと。
10. voice_only書き起こし編集後の再解析失敗でinvalidな旧planを復元しないこと。
11. playback、pan、zoomがUndo対象にならず、Undo後もviewportを維持すること。
12. VMD / report保存cancelまたは失敗後も編集と履歴が残ること。

## 12. 受け入れ条件

- current job success / failure / cancelが別transactionとして扱われる。
- restore可能なfailure / cancelでold base、adjustment、history、selectionが復元する。
- failure rollback後はERRORが残り、VMD保存できない。
- cancel rollback後はprior failureを復元し、存在しない場合だけcancel INFOを含む
  fingerprintを再構築してWARNINGを再確認する。
- failure rollback後のretry / cancelではprior ERRORを保持し、cancel INFOだけで保存可能にしない。
- selected editor dirty入力ではanalysis jobを開始せず、入力を暗黙破棄しない。
- analysis parameter mismatch後のsuccess / failure / cancel resultをcommit / restoreしない。
- restore不能時はinvalidな旧stateを復元しない。
- late / duplicate callbackはMS21 stateを変更しない。
- audio workerのduplicate success / errorとkind mismatchはstateを変更しない。
- input commit、parameter変更、workspace resetでhistoryをclearする。
- save cancel / failureだけではhistoryをclearしない。
- TEXTあり / voice_only双方の既存導線が維持される。
- 1同期内のeffective resolver callは最大1回である。
- valid edit result hintではcommit後の追加resolver callが0回である。
- adjustment-only syncが無関係なplayback / broad Refreshを実行しない。
- Preview、RightPane、diagnostics、fingerprint、writerが同じeffective plan semanticsを使う。
- fixed morph、VMD format、network禁止、wxPython主系を維持する。
- dependency、package、build、licenseに変更がない。
- B7 helperがwx、UiState、MainFrameを逆importせず、fresh-processの両import順が成功する。
- production変更前の再実行でwx aggregateとfull suiteがpass表示・process exit code 0になり、
  実装中に再発したstartup splash testのaccess violationも補修後にexit code 0へ戻る。
- README、配布用readme、Pipeline / GUI / Error仕様がimplemented状態と一致する。
- B7専用、関連回帰、full test、compileall、diff checkが成功する。
- B7手動GUI確認と、そこで見つかったSelected Event Tab Auto-Switch追加補正後の
  ユーザーGUI再確認が実施され、いずれも問題なしと報告されている。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| persistent cacheがstale planを表示する | contextを1同期内限定にし、UiStateへ保存しない |
| edit result hintがcurrent historyとずれる | base identityとcanonical snapshotの完全一致を検証する |
| 効率化でdiagnosticsだけ古くなる | diagnostics / Preview / editorへ同じcontextを渡す |
| adjustment-only同期で必要なUIまで止める | 同期対象と非対象をtestで固定する |
| time-based testが不安定 | resolver / Refresh call countをacceptanceにする |
| failure rollbackで保存可能と誤表示する | failure ERRORと専用Statusを保持しsaveabilityをtestする |
| cancelで旧WARNING確認を誤復元する | fingerprintをrollback payloadへ含めない |
| retry / cancelでprior failureを失い保存可能になる | immutable prior failureだけをrollback payloadへ含め、ERROR優先を維持する |
| dirty直接入力をBusy同期が上書きする | analysis開始の最初に既存dirty guardで拒否し、job / diagnosticsを変更しない |
| parameter変更をbase identity一致が見逃す | 3 parameterをidentityと別snapshotで比較し、mismatch terminalをfail closedにする |
| duplicate terminal callbackが新stateを上書きする | job IDとactive terminal guardを併用する |
| audio workerの同一job duplicateが再処理される | expected kindとRUNNING statusをsuccess / error guardへ追加する |
| failure判定前のinvalidateでold planを失う | snapshot old planからidentityを先に検証し、restore不能時だけinvalidateする |
| history初期化でidentityを二重生成する | resolver resultのcanonical snapshotからhistoryを初期化する |
| B7 helper追加でGUI / core間の循環参照を作る | MainFrame所有、一方向leaf import、aggregate export禁止、fresh-process import smokeで固定する |
| wx aggregateのnonzero終了をpass件数だけで見逃す | Step 0で原因を最小補修し、wx aggregate / full suiteのexit code 0をproduction着手gateにする |
| voice_only invalid planを復元する | capture時にanalysis valid / pending / identityを検証する |
| old editor requestがrestore後に通る | restore時にeditor revisionを進める |
| rollback DTOへwidgetを保持してリークする | immutable domain stateだけを保持する |
| docsがplanned / implementedを混同する | B7実装後の実測結果だけを完了記録へ反映する |

## 14. Codex 実装時の注意

- 最初にrepo状態と本計画を再確認する。
- 最初にStep 0を完了し、wx aggregate / full suiteのexit code 0までproduction codeを変更しない。
- 実装前チェックではコードを変更しない。
- performance問題の原因をresolverだけと断定せず、call-count testで再確認する。
- effective shape計算結果を簡略化して速度を作らない。
- process全体cache、timer、thread、networkを追加しない。
- user input、internal analysis WAV、MMD-use WAVを混同しない。
- fixed morph `あ / い / う / え / お` を変更しない。
- Qt / PySide6を復活させない。
- existing testを弱めて旧failure契約との競合を隠さない。B1の最終契約へ期待値を更新する。
- pass件数だけを根拠にprocess exit code 1を成功扱いしない。
- B7 helperをpackage `__init__.py`からexportせず、core / writerからGUIへ逆依存させない。
- dependency変更が必要になった場合は実装を止め、ユーザーへ確認する。
- 実行したtestはpass表示とprocess exit codeを分けて報告する。
- manual GUI確認を実施済みと捏造しない。
- commit、merge、push、tagは明示依頼があるまで行わない。

実装完了時の報告形式:

1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
