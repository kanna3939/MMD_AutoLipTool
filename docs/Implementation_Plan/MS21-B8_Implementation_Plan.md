# MS21-B8 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B8 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B8_Implementation_Plan.md`
- 対象Block: MS21-B8
- Block名: MS21 Closeout
- 基準ブランチ: `feature/MS21-implementation`
- 計画作成基準コミット: `16266e2 Implement MS21-B7 state integration`
- 作成日: 2026-07-31
- 文書ステータス: Plan Created / Live-State Review Passed /
  Pre-implementation Check: Plan Corrections Applied /
  Closeout Audit Complete / A / MS22 Handoff Recorded
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
- 監査対象計画:
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B6_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B7_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B7_Selected_Event_Tab_Auto_Switch_Additional_Fix_Plan.md`

本Blockは新機能を追加する実装Blockではない。MS21-B1からB7の要求、実装、テスト、
ユーザー確認、文書、依存関係・配布境界を総合監査し、MS21 CloseoutをA / B / Cで判定する。

## 2. 背景

MS21-B7までに、発音イベント単位補正、Preview / VMD共通effective output、diagnostics、
Undo / Redo、analysis rollback、late callback guard、同期効率化、Preview選択時の
「選択イベント」tab自動切替を実装した。

2026-07-27に、追加tab補正を含むMS21-B7範囲のユーザー手動GUI確認は通過・問題なしと
報告されている。HEAD上の全体testは `618 passed, 7 subtests passed`、process exit code 0
であり、`compileall` と `git diff --check` も成功している。

一方、MS21全体としては、B1からB7の各受け入れ条件が一つの監査表へ統合されておらず、
P1 / P2 / P3の残存、文書間の状態表記、MS22開始可否を最終判定していない。

## 3. 目的

- B1からB7の要求、実装、テスト、ユーザー確認を一つの証拠表へ統合する。
- base / adjustment / effective output、selection、history、lifecycle、diagnostics、
  saveabilityの契約に未評価の穴がないことを確認する。
- testのpass表示とprocess exit codeを分離して再検証する。
- README、配布用readme、正本仕様、routing文書、milestone / version historyの状態を
  実際の到達状態へ同期する。
- P1 / P2 / P3を分類し、残存状態とユーザー判断を明示したうえでCloseout判定を行う。
- MS22へ進める条件と、未検証事項を根拠付きで引き継ぐ。

## 4. In Scope

### 4.1 実装・契約監査

- B1 Adjustment Contract / Current-State Pre-check
- B2 Adjustment Core / Shared Shape Resolver
- B3 Preview Hit-Test / Event Selection
- B4 RightPane Event Editor / Live Preview
- B5 VMD Save / Diagnostics Integration
- B6 In-Memory Undo / Redo
- B7 State Integration / Regression / Docs / Adjustment Sync Efficiency
- B7 Selected Event Tab Auto-Switch追加補正
- fixed morph `あ / い / う / え / お`、30fps、VMD形式、network禁止の不変条件

### 4.2 検証監査

- B2からB7専用testと計画指定回帰
- TEXTあり / voice_only、workspace reset、audio / analysis worker、late callback
- Preview、RightPane、diagnostics、fingerprint、VMD保存、report保存
- Undo / Redo、reset、Busy、再解析success / failure / cancel
- full suite、compileall、git diff check
- ユーザー手動GUI確認の証拠と範囲

### 4.3 文書・配布境界監査

- README / `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- MS21計画、Block Breakdown、Index、Roadmap
- `docs/repo_milestone.md`、`docs/Version_Control.md`
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、license / notice関連

## 5. Out of Scope

- 新機能、仕様変更、production codeの先行修正
- B1からB7の機能に対する再設計・広範なリファクタリング
- testを弱める変更、失敗を隠すfixture変更
- 実MMDでの全機能受け入れ（MS26の責務）
- MS22の長音表現・生成preset実装
- package、release、version bump、tag、main merge、push、branch削除
- Qt / PySide6、cloud、外部送信、telemetry、background通信
- fixed morph、VMD format、Shift_JIS、30fps契約の変更

B8監査でP1 / P2を発見した場合、B8内で無断修正してCloseout扱いにしない。原因と
再検証条件を記録し、必要なrepairまたはユーザー判断へ戻す。Closeoutに必要な文書の
表現修正だけは、実測結果を根拠として行う。

## 6. 前提条件

### 6.1 Git / environment

- branchは `feature/MS21-implementation` とする。
- B8計画作成基準は `16266e2` とする。
- 計画作成・レビュー中の文書専用変更は許容する。Closeout監査のStep 0へ進む前に、
  B8対象文書を基準commitへ固定し、worktreeがcleanであることを確認する。
- Python 3.11以上、repo-local `.venv`、wxPython主系を維持する。
- B7実装はcommit済みであり、B8はそのHEADを監査対象とする。

### 6.2 判定境界

- ユーザーからの手動GUI確認通過報告は、報告された範囲の証拠として記録する。
- Codexが実行したtestは、pass表示とprocess exit codeを別々に記録する。
- 実MMD未確認はMS21全体の未検証事項として残し、MS26の責務へ引き継ぐ。
- A判定は、P1 / P2がなく、主要受け入れ条件・自動検証・ユーザー確認・文書同期が
  揃った場合だけ許可する。
- B判定は、残存事項があり、ユーザーが明示的に受け入れた場合だけ許可する。
- C判定は、主要要求の未実装・未検証、P1、または未解決P2がある場合とする。

### 6.3 現時点で確認済みの事実

- B7実装基準: `16266e2 Implement MS21-B7 state integration`
- Closeout監査時点のHEAD: `b8b539c Plan MS21-B8 closeout audit`
- worktree: clean。B8計画・関連文書の作成・レビュー変更は監査開始前にcommit済みで、
  Closeout監査のclean gateを満たした。
- MS21-B7: implementation、automated verification、user manual GUI verification complete
- full suite: `618 passed, 7 subtests passed` / process exit code 0
- `compileall src tests`: process exit code 0
- `git diff --check HEAD`: process exit code 0
- B7基準からHEADまで、dependency / package / build / license関連ファイルの差分なし
- B8専用Implementation Planは本書で初めて作成され、監査実行記録を本書へ追記した

### 6.4 2026-07-31計画内容・実装状態照合結果

- B8の目的、In / Out of Scope、対象ファイル、テスト方針、A / B / C判定契約は、
  `MS21_Block_Breakdown.md` のBlock8定義および現行B7完了状態と整合している。
- B7専用test、B2からB6回帰、MS17 / MS19 / MS20回帰、full suite、compileall、
  diff checkの対象は現行リポジトリに実在する。
- B7-PRE-004の状態がB7計画内だけ「実装前gate」と残っていたため、B7実装時の
  wx aggregate / full suite終了コード0の実測に合わせて `closed (2026-07-27)` へ補正した。
- 上記補正以外に、計画と現行production code、test、dependency、build設定の間の
  P1 / P2相当の齟齬は確認されなかった。precheckで指摘した文書境界のP2は、
  計画作成・レビュー段階とCloseout監査開始段階を分離する記載へ修正した。
- 回帰対象を明示的なtest file群へ固定し、B1〜B7証拠台帳の格納場所を本書の§15へ固定した。
- B8専用のCloseout監査と最終判定は2026-07-31に実施した。文書baselineのcommitと
  clean gateを確認したうえで監査を開始し、P1 / P2 / P3なしのA判定を確定した。

## 7. 対象ファイル

### 7.1 主監査対象

| ファイル | 確認内容 |
| --- | --- |
| `src/core/event_adjustment.py` | adjustment model / validation |
| `src/core/effective_shape_plan.py` | base identity / effective resolver |
| `src/core/event_adjustment_history.py` | snapshot history / Undo / Redo |
| `src/gui_wx/preview_panel.py` | Preview selection / render revision |
| `src/gui_wx/right_pane.py` | editor / notices / tab behavior |
| `src/gui_wx/ui_state.py` | state ownership / lifecycle |
| `src/gui_wx/main_frame.py` | sync / analysis / rollback / save integration |
| `src/gui_wx/app_controller.py` | audio worker lifecycle / terminal guard |
| `src/gui_wx/analysis_rollback.py` | rollback DTO / restore predicate |
| `src/gui_wx/ui_sync_context.py` | single-pass derived context |

### 7.2 テスト対象

- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_ms21_b3_selection_commit.py`
- `tests/test_ms21_b3_preview_hit_test.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_wx_ms21_b3_preview_selection.py`
- `tests/test_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b5_explicit_event_crossfade.py`
- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_ms21_b7_import_boundaries.py`
- `tests/test_ms21_b7_ui_sync_context.py`
- `tests/test_wx_ms21_b7_state_integration.py`
- `tests/test_wx_ms21_b7_sync_efficiency.py`
- §11.1の「MS17 / MS19 / MS20・既存回帰」test file群
- `tests/test_wx_startup_splash.py`

### 7.3 文書対象

- B1からB7のImplementation PlanとB7追加補正計画
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `README.md`、`readme_mmdautolip.txt`
- Pipeline / GUI / Error仕様
- `docs/repo_milestone.md`、`docs/Version_Control.md`
- B1〜B7受け入れ条件・証拠台帳は、本書の§15へ記録する。別ファイルは作成しない。

## 8. 実装方針

B8ではproduction codeとtest codeを変更しない。まず現行HEADとB1からB7の計画・実装・
テスト・文書を照合し、証拠表を作る。実装状態と計画の差異は、次の優先順で扱う。

1. P1 / P2の機能・契約差異はCloseoutを停止し、repairまたはユーザー判断へ戻す。
2. P3の記載差異は、実測結果を根拠に最小限の文書修正を行う。
3. すべての主要条件が揃った場合だけA判定候補とする。
4. A / B / C判定と未検証事項を、B8計画、Block Breakdown、Index、Roadmap、
   milestone / version historyへ同期する。

### 8.1 B7計画の記載差異修正記録

初回のlive-state照合では、B7計画のpre-implementation補正表に
`B7-PRE-004` が「実装前gate」と残っていることを検出した。wx aggregate / full suiteの
process exit code 0を確認済みであるため、照合中に状態を `closed (2026-07-27)` へ補正した。
過去時点の測定値とgate運用の記録は削除せず、履歴として保持する。

## 9. 詳細ステップ

### Step 0: Closeout開始条件

- branch、HEAD、worktree、B8計画、B7完了commitを確認する。
- B7計画の `B7-PRE-004` が現行実測に一致して `closed` であることを確認する。
- Closeout監査開始時点で、計画・routing文書のbaseline commit後にworktreeがcleanであることを確認する。
- dependency、package、build、licenseに未承認差分がないことを確認する。

### Step 1: B1〜B7受け入れ条件台帳

- 各Blockの目的、In / Out of Scope、受け入れ条件、実装ファイル、test、user evidenceを
  本書§15の証拠台帳へ一覧化する。
- implemented、verified、planned、deferred、out of scopeを混同しない。
- MS21横断契約（base / adjustment / effective、identity、selection、history、lifecycle、
  diagnostics、saveability）ごとに証拠を紐付ける。

### Step 2: 自動検証

- B2からB7専用testを段階実行する。
- MS17 / MS19 / MS20 regression、TEXTあり / voice_only、workspace、save / report、
  playback、startup teardownを実行する。
- full suiteを実行し、pass表示、failure / error、fatal、process exit codeを別記録する。
- `compileall src tests` と `git diff --check` を実行する。

### Step 3: ユーザー確認証拠

- B1からB7のユーザー確認範囲と報告日を各Blockへ紐付ける。
- B7追加tab補正を含む「通過・問題なし」報告をB7証拠として扱う。
- 実MMDでの全機能確認は未実施ならMS26へ引き継ぎ、MS21の未検証事項として明記する。

### Step 4: 文書整合

- B7-PRE-004など、完了済み実測と矛盾する現行表記を修正する。
- B8計画、Block Breakdown、Index、Roadmap、milestone / version historyの状態、日付、
  test数、判定を照合する。
- README / 配布用readme / 正本仕様は、機能挙動に差異がある場合だけ更新する。

### Step 5: 判定

- P1 / P2 / P3を重複なく分類する。
- P1なし、P2なし、主要条件・自動検証・ユーザー確認・文書同期が揃えばA候補とする。
- 残存事項がユーザー明示承認済みの場合のみB候補とする。
- 未解決P1 / P2、主要要求の未評価、証拠不足があればCまたはCloseout延期とする。

### Step 6: Closeout文書同期

- 判定をB8計画とMS21 routing文書へ反映する。
- A / Bの場合、MS21の現在フェーズとMS22への引き継ぎ条件を更新する。
- Cまたは延期の場合、未完了項目、所有Block、再開条件を記録する。

## 10. 状態遷移 / データ契約

```text
B7 Complete
  -> B8 Plan Draft
  -> B8 Pre-implementation Check
      -> Closeout Audit
          -> A: MS21 Closeout / MS22 handoff
          -> B: User-accepted residual / conditional handoff
          -> C: Closeout deferred / repair or evidence needed
```

### 10.1 不変条件

- B8はbase timing plan、adjustment、effective shape、history、selectionを変更しない。
- B8はユーザー確認済み事実とCodex実行結果を混同しない。
- testのpass表示だけで合格扱いせず、process exit codeを別判定する。
- 実MMD未確認をMS21の全機能確認済みと表現しない。
- MS22の機能実装をMS21 Closeoutへ含めない。

### 10.2 Closeout判定契約

| 判定 | 条件 | 次の扱い |
| --- | --- | --- |
| A | P1 / P2なし、主要要求・自動検証・ユーザー確認・文書同期が完了 | MS21完了、MS22開始条件を引き継ぐ |
| B | 残存事項があるが、ユーザーが明示受け入れ | 残存事項を明記して条件付き引き継ぎ |
| C | P1 / P2、主要未実装、証拠不足、または監査不能 | Closeout延期、repair / 再検証 |

## 11. テスト方針

### 11.1 自動テスト

1. B7専用test
2. B2からB6のcore / wx test
3. MS17 / MS19 / MS20 lifecycle・diagnostics・save回帰
4. `tests` 全体
5. `compileall src tests`
6. `git diff --check`

各コマンドは一つずつ実行し、pass表示と終了コードを分離して記録する。B8ではtest codeを
変更して失敗を解消しない。

実行対象を次のfile群へ固定する。各グループは個別のpytestコマンドとして実行し、
最後に全体testを実行する。

| グループ | 対象 |
| --- | --- |
| B7専用 | `test_ms21_b7_analysis_rollback.py`、`test_ms21_b7_audio_worker_terminal.py`、`test_ms21_b7_import_boundaries.py`、`test_ms21_b7_ui_sync_context.py`、`test_wx_ms21_b7_state_integration.py`、`test_wx_ms21_b7_sync_efficiency.py` |
| B2〜B6 MS21回帰 | §7.2に列挙した `test_ms21_b2_*`、`test_ms21_b3_*`、`test_ms21_b4_*`、`test_ms21_b5_*`、`test_ms21_b6_*` 全file |
| MS17 / MS19 / MS20・既存回帰 | `test_wx_ms14_b4_analysis.py`、`test_wx_ms14_b5_export.py`、`test_ms17_b8_late_worker_result_discard.py`、`test_ms19_b4_voice_only_gui_state.py`、`test_ms19_b7_voice_only_error_handling.py`、`test_ms19_b8_workspace_reset.py`、`test_ms20_b2_output_diagnostics.py`、`test_ms20_b3_output_diagnostics_adapter.py`、`test_ms20_b4_playback_context.py`、`test_ms20_b5_warning_save_policy.py`、`test_ms20_b6_diagnostic_report.py`、`test_ms20_b6_report_save_flow.py`、`test_ms20_b7_diagnostics_state_integration.py`、`test_pipeline_and_vmd.py`、`test_wx_ms15_b3_playback.py`、`test_wx_startup_splash.py` |
| 全体 | `tests` 全file |

### 11.2 ユーザー手動確認

- B1からB7の確認範囲、結果、報告日、追加補正の有無を台帳化する。
- B7追加tab補正を含む確認通過を記録する。
- 実MMDのVMD / WAV読み込み・リップ同期の全機能確認はMS26へ引き継ぐ。

### 11.3 依存・配布確認

- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、license / noticeを確認する。
- MS21-B7基準からの依存追加、バイナリ追加、package設定変更、license影響がないことを確認する。

## 12. 受け入れ条件

- B1からB7の主要受け入れ条件が台帳化され、implemented / verified / planned / deferredが
  明確に区別されている。
- base / adjustment / effective output、selection、history、lifecycle、diagnostics、
  saveabilityの横断契約に未評価の穴がない。
- B7追加tab補正を含むユーザー手動GUI確認の範囲と結果が記録されている。
- full suite、compileall、git diff checkの表示結果とprocess exit codeが記録されている。
- P1 / P2 / P3が分類され、残存事項の根拠と所有者が明記されている。
- dependency、package、build、license、fixed morph、VMD、network契約の逸脱がない。
- B8でproduction codeとtest codeを変更していない（必要なrepairは別作業へ分離する）。
- B8判定がA / B / Cのいずれかとして根拠付きで確定されている。
- MS22開始可否と未検証事項が明記されている。
- Closeout可能な場合、関連routing文書が判定と一致している。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 過去の未実施記録を現在状態と誤認する | 日付付き履歴と現在状態を分離する |
| pass件数だけで全体testを合格扱いする | process exit codeを必須記録にする |
| B7-PRE-004の古いgate表記が再発する | 現行状態は`closed`、過去の測定値は履歴として保持する |
| ユーザー確認範囲を過大主張する | 報告された範囲だけを証拠化する |
| 実MMD未確認を隠す | MS26への残課題として明記する |
| Closeoutで機能修正を混ぜる | production / test変更を別repairへ分離する |
| B8文書間で判定がずれる | 最終判定後に計画・Index・Roadmap・履歴を同一内容へ同期する |
| MS22を先行実装する | B8 Out of Scopeとbranch作業範囲を固定する |

## 14. Codex実装時の注意

- B8はCloseout監査であり、新機能実装ではない。
- 最初にGit状態、B8計画、B7完了commitを確認する。
- すべてのコマンドを一つずつ実行する。
- testの期待値を弱めない。失敗があればCloseoutを止める。
- B7-PRE-004の状態を実測へ合わせるが、過去のexit code 1記録は削除しない。
- B1からB7のユーザー確認報告をCodex自身の手動確認と表現しない。
- 実MMD未確認をMS21完了条件から隠さない。
- fixed morph `あ / い / う / え / お`、wxPython主系、network禁止を維持する。
- dependency、package、release、tag、merge、push、branch削除は行わない。
- closeout判定前にREADME、正本仕様、milestone履歴を完了扱いへ更新しない。

## 15. Closeout証拠台帳

B8監査のStep 1で、B1〜B7の証拠を次の表へ一元化した。ユーザー確認欄はユーザーから
報告された範囲だけを記録し、Codexによる手動GUI実行とは扱わない。

| Block | 受け入れ条件・横断契約 | 実装対象 / commit | 自動test・pass表示 / exit code | ユーザー確認範囲・日付 | 文書同期 | status / finding / owner |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | base / adjustment / effective境界、identity、grouping、lifecycle、history境界を契約固定 | 計画・契約のみ（production / test変更なし） | 指定95件＋補完72件、計167件 pass表示 / 各 exit 0 | N/A（契約固定のみ、GUI確認対象外） | B1 plan、Block Breakdown、Indexへ反映済み | 完了。findingなし。owner: B8監査 |
| B2 | immutable adjustment、canonical snapshot、real / synthetic provenance、group-aware shared resolver | `98dab6d Implement MS21-B2 adjustment core` | B2専用35件＋指定回帰156件 pass表示 / exit 0 | 既存GUI回帰のみ、2026-07-22。event編集・Undo / RedoはB2対象外 | B2 plan、Pipeline / Indexへ反映済み | 完了。findingなし。owner: B8監査 |
| B3 | Preview hit-test、strict canonical selection、stale / synthetic拒否、shared resolver接続 | `07c3717 Implement MS21-B3 preview selection` | B3 22件、Preview / selection / viewport回帰50件、full 533＋7 subtests pass表示 / 各 exit 0 | Preview event選択・表示確認、2026-07-23。palette補修後に通過 | B3 plan、GUI仕様、README、Indexへ反映済み | 完了。findingなし。owner: B8監査 |
| B4 | RightPane editor、base / adjustment / effective表示、live Preview、reset、notice、saveability | `0aa7fbf Implement MS21-B4 selected event editor` | B4 16件、B2 35件、B3 22件、RightPane / theme 21件、diagnostics 37件、pipeline / VMD 12件、full 550＋7 subtests pass表示 / 各 exit 0 | 開口保持・閉口スムーズ・傾斜比、効果noticeを含むGUI確認、2026-07-24 | B4 plan、Pipeline / GUI / Error仕様、README、Indexへ反映済み | 完了。findingなし。owner: B8監査 |
| B5 | effective planをPreview / writer / diagnosticsで共有、fingerprint、report、明示crossfade notice | `f74777b Implement MS21-B5 effective VMD save` + `4bff439 Add explicit event crossfade` | B5専用28件 pass表示 / exit 0。B8横断回帰で保存・report・crossfadeを再確認 | B5本体および単イベントcrossfade追加補正、2026-07-26。通過・問題なし | B5 plan、B5追加補正 plan、Pipeline / GUI / Error仕様、README、Indexへ反映済み | 完了。findingなし。owner: B8監査 |
| B6 | immutable snapshot history、最大50操作、coalescing、reset、Edit menu、Ctrl+Z / Ctrl+Y | `4596d7e Implement MS21-B6 adjustment history` | B6 core 12件＋wx 9件＋関連回帰99件 pass表示 / 各 exit 0 | Undo / Redo、reset、編集履歴のGUI確認、2026-07-26。通過・問題なし | B6 plan、GUI仕様、README、Indexへ反映済み | 完了。findingなし。owner: B8監査 |
| B7 | rollback、dirty guard、parameter一致、terminal guard、single-pass sync、tab auto-switch、docs sync | `16266e2 Implement MS21-B7 state integration` | B7専用15件、B2〜B6回帰123件、MS17 / MS19 / MS20回帰154件＋7 subtests、full 618＋7 subtests pass表示 / 各 exit 0 | B7本体・tab自動切替追加補正を含む手動GUI確認、2026-07-27。通過・問題なし | B7 plan、追加tab補正 plan、README、Pipeline / GUI / Error仕様、Indexへ反映済み | 完了。findingなし。owner: B8監査 |

### 15.1 Closeout実施記録

- 実施日: 2026-07-31
- Step 0: `feature/MS21-implementation`、B7基準 `16266e2`、監査開始時HEAD
  `b8b539c`、worktree clean、B7-PRE-004 closedを確認した。B7基準からのdependency、
  package、build、license差分はない。
- 自動検証: B7専用15件、B2〜B6 MS21回帰123件（B5専用再確認28件を含む）、
  MS17 / MS19 / MS20・既存回帰154件＋7 subtests、全体618件＋7 subtestsを実行し、
  すべてpass表示・process exit code 0だった。
  `compileall src tests` と `git diff --check` もprocess exit code 0だった。
- ユーザー確認: B1〜B7の通過報告を各行へ紐付けた。これはユーザー報告の再利用であり、
  Codexが手動GUIを実行したことを意味しない。
- 判定: P1なし、P2なし、P3なし。Closeoutは **A** とし、MS22開始条件を引き継ぐ。
- 制約: B8ではproduction code、test code、GUI挙動、dependency、build / package / license、
  固定モーフ、VMD形式、network契約を変更していない。merge、push、tag、releaseは未実施。
- 未検証事項: 実MMDでのVMD / WAV読み込み・リップ同期はMS26で実施する。

## 16. 実施後の報告形式

1. 確認したファイル
2. 変更したファイル
3. Closeout監査内容
4. 実行したテスト
5. テスト結果（pass表示 / process exit code）
6. P1 / P2 / P3
7. Closeout判定（A / B / C）
8. 仕様からの逸脱
9. 未検証事項
10. MS22への引き継ぎ
