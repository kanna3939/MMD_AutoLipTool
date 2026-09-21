# MS22-B7 Implementation Plan

## 1. 文書情報

- 文書名: `MS22-B7 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS22-B7_Implementation_Plan.md`
- 対象Block: `MS22-B7 MS22 Closeout`
- 基準ブランチ: `feature/MS21-implementation`
- 計画作成基準HEAD: `25301c4 Implement MS22-B6 lifecycle regression and docs`
- 作成日: 2026-08-11
- 文書ステータス: **Implemented / Closeout Audit Passed / A / MS26 Actual-MMD Verification Deferred (2026-08-12)**
- 上位正本:
  - `docs/Implementation_Plan/MS22_Block_Breakdown.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
- 監査対象計画:
  - `docs/Implementation_Plan/MS22-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS22-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS22-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS22-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS22-B5_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS22-B6_Implementation_Plan.md`
- 次工程: MS23 Model Profiles Implementation Plan策定。実MMD確認はMS26へdeferred

本Blockは新機能を実装するBlockではない。MS22-B1からB6の要求、実装、テスト、
ユーザー確認、文書、runtime data、依存関係・配布境界を総合監査し、MS22 Closeoutを
A / B / Cで判定する。

## 2. 背景

MS22は、明示された`ー`を起点とする長音metadata、`hold / decay`、Preview / writer共通resolver、
生成設定、組み込み／ユーザーpreset、`presets.json`、output history、diagnostics、RightPane導線、
lifecycle回帰をB1からB6へ分割して実装した。

- B1: Long-Vowel / Generation-Preset Contract Pre-check
- B2: Long-Vowel Data Contract / Shared Resolver / Same-Vowel Audit
- B3: Generation Preset Store / Settings Contract
- B4: Generation State / History / Diagnostics Integration
- B5: Preset UI / Event Override Flow
- B6: Lifecycle Regression / Documentation

2026-08-11時点でB6まで実装・自動検証済みであり、B4、B5、B6のユーザー手動GUI確認は
通過・問題なしと報告されている。Codex自身の手動GUI実行とは扱わない。B7計画作成baselineでは、
MS22 B2〜B6とsplashの93件、full suite 713件、`compileall src tests`、`git diff --check`を
pass表示・process exit code 0で確認した。

計画作成時点では、MS22全体として次のCloseout作業が未実施であった。

- B1からB6の受け入れ条件と証拠を一つの台帳へ統合する
- Roadmap §9.4の完了条件とcurrent implementationを再照合する
- P1 / P2 / P3の残存を分類する
- dependency / package / runtime user data境界を監査する
- A / B / C判定を確定し、routing・履歴文書を同期する
- MS23開始条件とMS26の実MMD未検証事項を分離して引き継ぐ

計画作成時のcurrent repositoryでは、repo rootの`presets.json`がtrackedであり、二つの
ユーザープリセット値を保持していた。計画レビューでは、product contractとtemporary storeを使うtestを照合し、
B3 / B5で固定したruntime user file境界との衝突をB7-PRE-001のP2として確定した。local fileを保護したまま
Git追跡を解除し、`/presets.json`と`/MMD_AutoLipTool.ini`をdurable ignoreへ追加して解消した。

B5計画とBlock一覧に残っていた「splash P3 pending」は、B6のsplash 3件、known組合せ18件、full suite 713件が
pass表示・process exit code 0だった証拠と一致しないため、B7-PRE-002のP3として確定した。B5時点の失敗記録を
履歴として保持し、current statusをB6解消済みへ同期して解消した。

2026-08-12にB7 Closeout監査を実施した。MS22 direct regression 93件、基盤回帰185件、MS21回帰138件、
MS17 / MS19 / MS20回帰158件、B4 / B5 / splash組合せ18件、full suite 713件、`compileall src tests`、
`git diff --check`をすべてpass表示・process exit code 0で確認した。P1 / P2 / P3はなく、CloseoutをAと判定した。
ユーザー報告によるB4 / B5 / B6手動GUI確認は報告範囲に限定して再利用し、Codex自身のGUI実行とは扱わない。
実MMDでのVMD / WAV読み込み・リップ同期はMS26へdeferredのまま維持する。

## 3. 目的

- B1からB6の目的、受け入れ条件、実装commit、test、ユーザー確認、文書同期を一つの証拠台帳へ統合する。
- 長音token / timeline / identity、hold / decay、mode precedence、preset persistence、history、
  Preview / VMD / diagnostics、lifecycleの横断契約に未評価の穴がないことを確認する。
- Roadmap §9.4の三つの完了条件をcurrent implementationと実測へ対応付ける。
- runtime user data、dependency、package、build、license、fixed morph、VMD、30fps、network境界を監査する。
- pass表示、failure / error、process exit codeを分けて再検証する。
- P1 / P2 / P3を分類し、残存事項と所有者を明記する。
- A / B / C判定を根拠付きで確定し、MS23への進行条件とMS26への未検証事項を引き継ぐ。

## 4. In Scope

### 4.1 B1〜B6実装・契約監査

- 正規化済み読み列の`ー`由来token、timeline metadata、copy / repair / identity保持
- explicit long-vowel run、source / terminal event ownership、same-vowel非長音との分離
- `hold`の終端維持と`decay`のterminal end exact `0.0`
- Preview / writer / diagnostics / fingerprintの共通effective output
- terminal event override > active generation settings > application default `hold`の優先順位
- built-in preset、上限100件のuser preset、schema version 1の`presets.json`
- INI active generation settings / active preset ID、Custom fallback、restart復元
- preset Apply、direct generation setting、event override、Undo / Redo、history最大50件
- TEXTあり／voice-only、analysis success / failure / cancel、late callback、workspace reset、app restart / close
- invalid JSON / INI、atomic save failure、VMD / report cancel・failure時の状態保持
- wx startup splash、coalesced save timer、pending callbackのteardown

### 4.2 Closeout検証

- B2〜B6専用testとMS22 direct regression
- MS17 / MS19 / MS20 / MS21のinput、lifecycle、diagnostics、save、Preview / writer回帰
- known B4 / B5 / splash組合せ
- full suite、`compileall src tests`、`git diff --check`
- pass表示、failure / error、fatal、process exit codeの分離記録
- B4 / B5 / B6のユーザー手動GUI確認証拠と範囲

### 4.3 文書・repository境界監査

- README、配布用readme、Pipeline / GUI / Error仕様
- MS22 B1〜B6計画、Block Breakdown、Index、Roadmap
- `docs/repo_milestone.md`、`docs/Version_Control.md`のMS22追記位置
- `presets.json`と`MMD_AutoLipTool.ini`のruntime user data扱い
- `.gitignore`とtracked file一覧
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`

### 4.4 Closeout判定・引き継ぎ

- P1 / P2 / P3分類
- A / B / C判定
- MS22 Closeout文書同期
- 次MSとしてMS23 Model Profilesの計画策定へ進める条件
- 実MMDでのVMD / WAV読み込み・リップ同期をMS26へ維持する引き継ぎ

## 5. Out of Scope

- 新機能、production code変更、test code変更、GUI変更
- test期待値やfixtureを弱めてfailureを消す変更
- B1〜B6の広範な再設計・リファクタリング
- MS23 Model Profiles、MS24 Whisper Model Selection、MS25 Batch Outputの実装
- MS26 Actual MMD Verificationの実施または完了宣言
- package生成、release、version bump、tag、merge、push、branch削除
- dependency追加、binary追加、license方針変更
- Qt / PySide6復活、cloud ASR、外部音声送信、telemetry、background通信
- Whisper model / FFmpegの自動download
- fixed morph `あ / い / う / え / お`、VMD形式、30fps、既存audio契約の変更

B7監査でP1 / P2を発見した場合、無断で機能修正してCloseout扱いにしない。Closeoutを停止し、
原因、影響、推奨修正、再検証条件を記録してrepairへ分離する。文書表現のP3は、実測を根拠に
B7内で最小修正できる。runtime user fileの追跡解除が必要な場合も、local fileを削除せず、
tracked状態とignore契約だけを扱うrepairへ分離する。

## 6. 前提条件

### 6.1 Git / environment

- branchは`feature/MS21-implementation`とする。
- B7計画作成基準HEADは`25301c4`とする。
- B1からB6の実装・自動検証・文書・ユーザー報告はcommit済みである。
- 計画作成・レビュー中は本計画とrouting文書だけを変更してよい。
- Closeout監査開始前に、B7計画・routing文書をbaseline commitへ固定し、worktree cleanを確認する。
- Python 3.11以上、repo-local `.venv`、wxPython主系を維持する。
- コマンドは並列・連結せず、一つずつ実行する。

### 6.2 判定境界

- ユーザーの手動GUI通過報告は、報告された項目だけの証拠とする。
- Codexが実行した自動testとユーザー報告を混同しない。
- 実MMD未確認はMS22の未検証事項として残し、MS26へ引き継ぐ。
- AはP1 / P2がなく、主要要求・自動検証・ユーザー確認・文書・repository境界が揃う場合だけ許可する。
- Bは残存事項の影響と引き継ぎ先を記録し、ユーザーが明示的に受け入れた場合だけ許可する。
- CはP1、未解決P2、主要要求の未実装・未検証、監査不能がある場合とする。
- P3はAを自動的に妨げないが、影響と解消または引き継ぎ先を記録する。

### 6.3 計画作成baseline

2026-08-11、HEAD `25301c4`、worktree clean、`.venv`のPython 3.14.3で確認した。

| 対象 | 表示結果 | process exit code |
| --- | --- | --- |
| MS22 B2〜B6専用 + splash 13 file | 93 passed | 0 |
| `tests`全体 | 713 passed | 0 |
| `compileall src tests` | 成功 | 0 |
| `git diff --check` | 成功 | 0 |
| MS21 Closeout基準からdependency / package / build / license file差分 | なし | 0 |

これは計画作成baselineであり、B7 Closeout監査の実施結果ではない。Closeout時に同じ境界を
current HEADで再実行し、実数とprocess exit codeを記録する。

### 6.4 pre-closeout findingとrepair結果

| ID | 確認した事実 | 確定分類 | repair結果 |
| --- | --- | --- | --- |
| B7-PRE-001 | repo rootのtracked `presets.json`が二つのuser preset値を保持していた。B5 commit `525ac1e`で追加され、testはtemporary storeを使用する | P2 | local fileを保護したままGit追跡を解除し、`/presets.json`と`/MMD_AutoLipTool.ini`を`.gitignore`へ追加。再追跡防止とlocal file保持を再確認する |
| B7-PRE-002 | B5 plan statusとBlock一覧にsplash P3 pendingが残っていたが、B6でsplash 3件、known組合せ18件、full suiteをexit 0で確認済み | P3 | 過去のB5時点記録を保持し、B5 plan、Block、Index、Roadmapのcurrent statusをB6解消済みへ同期 |

両findingはB7 Closeout監査と分離したrepairで解消した。実装前チェックではrepair後の追跡・ignore状態と
文書整合を再確認し、未解決P2を再導入していない場合だけCloseout監査へ進む。

## 7. 対象ファイル

### 7.1 主監査対象コード

| 分類 | ファイル | 監査内容 |
| --- | --- | --- |
| token / pipeline | `src/core/text_processing.py`、`src/core/pipeline.py` | `ー` token、timeline metadata、voice-only / TEXTあり経路 |
| effective output | `src/core/effective_shape_plan.py`、`src/core/event_adjustment.py` | long run、hold / decay、override、validation、identity |
| preset / settings | `src/core/generation_presets.py`、`src/core/settings_store.py` | built-in / user preset、JSON / INI、failure isolation |
| state / history | `src/core/output_edit_state.py`、`src/core/event_adjustment_history.py` | atomic generation state、Undo / Redo、base identity |
| diagnostics | `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py` | generation summary、mode override、report identity |
| Preview / writer | `src/core/preview_transform.py`、`src/vmd_writer/writer.py`、`src/vmd_writer/effective_shape_adapter.py` | metadata保持、effective shape共有、terminal zero |
| GUI / lifecycle | `src/gui_wx/main_frame.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/app.py`、`src/gui_wx/ui_state.py` | commit flow、rollback、reset、restart、teardown |
| GUI presentation | `src/gui_wx/right_pane.py`、`src/gui_wx/selected_event_editor.py`、`src/gui_wx/output_diagnostics_adapter.py`、`src/gui_wx/ui_sync_context.py` | Select / Apply、event override、Info / Warning同期 |

B7では上記production codeを変更しない。差異を検出した場合はfindingとして記録し、repairへ分離する。

### 7.2 MS22直接テスト

- `tests/test_ms22_b2_long_vowel_tokens.py`
- `tests/test_ms22_b2_timeline_metadata.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms22_b2_import_boundaries.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_wx_ms22_b4_generation_state.py`
- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_wx_ms22_b5_long_vowel_override.py`
- `tests/test_ms22_b6_lifecycle_regression.py`
- `tests/test_wx_ms22_b6_lifecycle_regression.py`
- `tests/test_wx_startup_splash.py`

B7専用testは新設しない。Closeout証拠は本書§15へ統合し、testを追加しなければ証明できない
契約差異を見つけた場合はP2としてrepairへ戻す。

### 7.3 文書・repository対象

- `docs/Implementation_Plan/MS22-B1_Implementation_Plan.md`〜`MS22-B6_Implementation_Plan.md`
- `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `README.md`、`readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/repo_milestone.md`、`docs/Version_Control.md`
- `presets.json`、`.gitignore`、tracked file一覧
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`

### 7.4 B7で変更してよい文書

- 本書
- `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`、`docs/Version_Control.md`
- README / 配布用readme / Pipeline / GUI / Error仕様はcurrent implementationとの差異がある場合だけ

`presets.json`、`.gitignore`、production code、test codeは通常のB7変更対象ではない。
B7-PRE-001では、Closeout監査と分離したrepairとして`.gitignore`とGit追跡状態だけを変更し、
local `presets.json`本体、production code、test codeは変更していない。

## 8. 実装方針

### 8.1 Evidence-first

各Blockの「計画」「実装」「自動検証」「ユーザー報告」「文書同期」を別の証拠列へ置く。
後続Blockのtest通過だけで、前段Blockの契約や当時の未実施記録を上書きしない。

### 8.2 Roadmap完了条件との直接対応

| Roadmap §9.4 | 主証拠 |
| --- | --- |
| 長音表現の維持 / 減衰方針がPreviewとVMDで一致 | B2 resolver / adapter、B4 effective state、B5/B6 GUI・lifecycle、Preview / writer回帰 |
| 組み込みpresetと上限内user presetを選択・適用可能 | B3 store / schema、B5 UI、B6 persistence / restart、ユーザーGUI確認 |
| presetと個別event補正の優先順位が説明済み | Pipeline / GUI仕様、selected event editor、diagnostics、README / 配布用readme |

### 8.3 Finding分類

- P1: データ破壊、security、主要出力誤り、Closeoutを直ちに停止すべき問題
- P2: A判定または次MS開始前に解消すべき契約・実装・証拠・repository境界の問題
- P3: 主要挙動を変えない記録・表現・軽微な保守性問題

同じ根因を複数findingへ重複計上しない。過去時点の既知問題とcurrent unresolvedを区別する。

### 8.4 Repair分離

P1 / P2のproduction / test / repository修正は、Closeout文書同期と同時に実施しない。
修正範囲、受け入れ条件、再検証groupを固定し、repair後にStep 0から監査を再開する。
文書だけのP3はB7内で最小修正できる。

### 8.5 Closeout判定

| 判定 | 条件 | 次の扱い |
| --- | --- | --- |
| A | P1 / P2なし、主要要求・自動検証・ユーザー確認・文書・repository境界が完了 | MS22完了。MS23計画策定へ進める。MS26未検証を維持 |
| B | 残存事項をユーザーが影響込みで明示受け入れ | 残存事項・owner・再確認条件を明記して条件付きCloseout |
| C | P1、未解決P2、主要未実装・未検証、監査不能 | Closeout延期。repairまたは追加証拠へ戻す |

## 9. 詳細ステップ

### Step 0: Closeout開始条件

- branch、HEAD、upstream、worktreeを確認する。
- B7計画とrouting文書がbaseline commitへ固定され、worktree cleanであることを確認する。
- B6実装commit `25301c4`とB1〜B5の実装commitを確認する。
- dependency / package / build / licenseの未承認差分がないことを確認する。
- B7-PRE-001 / PRE-002の状態を確認し、未解決P2がある場合はCloseout監査を開始しない。

### Step 1: B1〜B6証拠台帳

- 各Blockの目的、受け入れ条件、実装commit、test、ユーザー確認、文書同期を§15へ記録する。
- B1はcontract固定、B2 / B3はcore中心、B4〜B6はGUI / lifecycle確認を含むことを区別する。
- current revalidation値とBlock完了時の値を混同しない。

### Step 2: 横断契約監査

- token -> timeline -> base identity -> adjustment -> effective shape -> Preview / writerの連鎖を確認する。
- preset JSON -> INI -> GenerationState -> OutputEditState -> history -> diagnosticsの連鎖を確認する。
- TEXTあり／voice-only、success / failure / cancel、reset / restart / closeで保持・破棄規則を確認する。
- Roadmap §9.4の各完了条件へcode、test、user、docsの複数証拠を紐付ける。

### Step 3: Runtime data / repository監査

- `git ls-files`でruntime INI / JSON、cache、temporary fileが追跡されていないか確認する。
- B7-PRE-001 repair後に`presets.json`が追跡対象外かつignore対象で、local fileが保持され、package対象外のままか確認する。
- runtime user fileならlocal fileを削除しないrepair方針を固定する。
- `.gitignore`がdevelopment時のINI / preset生成をdurableに保護するか確認する。

### Step 4: 自動検証

- §11.1のgroupを小さい順に、一つずつ実行する。
- pass表示、failure / error、fatal、process exit codeを別々に記録する。
- wx teardownのexit code 1が再発した場合、全pass表示だけで合格にしない。
- full suite、compileall、diff checkを最後に実行する。

### Step 5: ユーザー確認証拠

- B4、B5、B6のユーザー確認項目、報告日、追加補正有無を台帳化する。
- B2 / B3はcore契約中心で単独manual対象外だったことを明記し、後続GUI確認で過大に置換しない。
- 実MMD確認は未実施としてMS26へ維持する。

### Step 6: 文書・配布境界監査

- README / 配布用readme / Pipeline / GUI / Error仕様とcurrent behaviorを照合する。
- B5 splash P3のcurrent statusがB6解消証拠へ同期済みであることを確認する。
- `repo_milestone.md`と`Version_Control.md`はMS22 Closeout判定後だけ追記する。
- dependency / build / package / license差分を確認する。差分がなければbuildは実行しない。

### Step 7: Finding分類と判定gate

- P1 / P2 / P3を重複なく分類する。
- P1 / P2があればCloseoutを停止し、repair / 再検証条件を記録する。
- P3は影響と解消または引き継ぎ先を記録する。
- 全gateを満たした場合だけA候補とする。

### Step 8: Closeout文書同期

- 本書§15へ実測値、finding、判定を記録する。
- Block Breakdown、Index、Roadmapへ同じ判定、日付、test値、未検証事項を同期する。
- A / Bの場合だけ`repo_milestone.md`と`Version_Control.md`へMS22 Closeoutを追記する。
- README / 正本仕様は挙動差がある場合だけ変更する。

### Step 9: 最終整合確認

- 文書間の判定、次工程、test数、日付、実施者、MS26 deferredを再照合する。
- `git diff --check`、未追跡fileの末尾空白・EOF、変更file一覧を確認する。
- production / test / dependency / packageへ意図しない差分がないことを確認する。

## 10. 状態遷移 / データ契約

```text
B6 Implemented / Automated Verified / User Manual Test Passed
  -> B7 Plan Created
  -> B7 Pre-implementation Check
      -> plan / routing baseline commit
      -> clean worktree gate
      -> known P2 resolved or audit stops
  -> Closeout Audit
      -> A: MS22 Closeout / MS23 planning handoff / MS26 deferred
      -> B: user-accepted residual / conditional handoff
      -> C: closeout deferred / repair or evidence required
```

### 10.1 Closeout不変条件

- B7はlong-vowel shape、preset state、history、GUI state、VMD出力を変更しない。
- B7はruntime user fileを削除しない。
- B7はユーザー報告をCodex自身の手動GUI実行と表現しない。
- testのpass表示だけで合格扱いにせずprocess exit codeを確認する。
- planned、implemented、automated verified、user-reported、deferredを区別する。
- 実MMD未確認をMS22全機能確認済みと表現しない。
- MS23以降の実装をMS22 Closeoutへ含めない。

### 10.2 Persistence / repository境界

| 対象 | product contract | Closeout確認 |
| --- | --- | --- |
| built-in preset | code内read-only定義 | runtime JSONへ複製・編集されない |
| user preset | `presets.json`の`user_presets` | runtime user dataとしてsource tracking / test fixtureと分離される |
| active settings / active preset ID | `MMD_AutoLipTool.ini` | runtime user dataとしてsource trackingと分離される |
| base / history / selection | session内のみ | JSON / INIへ保存されない |
| tests | temporary directoryのstore | repo rootのruntime JSON / INIを変更しない |

## 11. テスト方針

### 11.1 実行順

各コマンドを一つずつ実行し、表示結果とprocess exit codeを記録する。

1. MS22 direct regression 13 file（計画作成baseline: 93 passed / exit 0）
2. text / pipeline / Preview / writer / settings回帰
3. MS21 effective output / history / lifecycle回帰
4. MS17 / MS19 / MS20 input / diagnostics / save回帰
5. known B4 / B5 / splash組合せ
6. `tests`全体
7. `compileall src tests`
8. `git diff --check`

### 11.2 実行コマンド

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b2_long_vowel_tokens.py tests/test_ms22_b2_timeline_metadata.py tests/test_ms22_b2_long_vowel_resolver.py tests/test_ms22_b2_long_vowel_adapters.py tests/test_ms22_b2_import_boundaries.py tests/test_ms22_b3_generation_presets.py tests/test_ms22_b4_generation_history.py tests/test_wx_ms22_b4_generation_state.py tests/test_wx_ms22_b5_preset_ui.py tests/test_wx_ms22_b5_long_vowel_override.py tests/test_ms22_b6_lifecycle_regression.py tests/test_wx_ms22_b6_lifecycle_regression.py tests/test_wx_startup_splash.py
.\.venv\Scripts\python.exe -m pytest tests/test_text_processing.py tests/test_pipeline_and_vmd.py tests/test_pipeline_peak_values.py tests/test_preview_transform.py tests/test_vmd_writer_grouping.py tests/test_vmd_writer_intervals.py tests/test_vmd_writer_multipoint_shape.py tests/test_vmd_writer_peak_value.py tests/test_vmd_writer_zero_guard.py tests/test_settings_store.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_effective_shape_plan.py tests/test_ms21_b2_event_adjustment.py tests/test_ms21_b2_shape_adapters.py tests/test_ms21_b3_pipeline_preview_integration.py tests/test_ms21_b3_preview_hit_test.py tests/test_ms21_b3_selection_commit.py tests/test_ms21_b4_selected_event_editor.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms21_b5_effective_output_identity.py tests/test_ms21_b5_explicit_event_crossfade.py tests/test_ms21_b6_adjustment_history.py tests/test_ms21_b7_analysis_rollback.py tests/test_ms21_b7_audio_worker_terminal.py tests/test_ms21_b7_import_boundaries.py tests/test_ms21_b7_ui_sync_context.py tests/test_wx_ms21_b3_preview_selection.py tests/test_wx_ms21_b4_selected_event_editor.py tests/test_wx_ms21_b6_undo_redo.py tests/test_wx_ms21_b7_state_integration.py tests/test_wx_ms21_b7_sync_efficiency.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_late_worker_result_discard.py tests/test_ms19_b4_voice_only_gui_state.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b3_output_diagnostics_adapter.py tests/test_ms20_b3_right_pane_info.py tests/test_ms20_b4_playback_context.py tests/test_ms20_b5_warning_save_policy.py tests/test_ms20_b6_diagnostic_report.py tests/test_ms20_b6_report_save_flow.py tests/test_ms20_b7_diagnostics_state_integration.py tests/test_wx_ms14_b4_analysis.py tests/test_wx_ms14_b5_export.py tests/test_wx_ms15_b3_playback.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms22_b4_generation_state.py tests/test_wx_ms22_b5_preset_ui.py tests/test_wx_startup_splash.py
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
git ls-files presets.json MMD_AutoLipTool.ini
git log --oneline -- presets.json
git diff --name-only a18de64..HEAD -- pyproject.toml MMD_AutoLipTool.spec build.ps1 LICENSE NOTICE THIRD_PARTY_LICENSES.md
```

Closeout前のdependency / package / build / license差分確認は、MS21 Closeout基準`a18de64`から
current HEADまでを対象にする。差分がなければbuild / packageは実行しない。

### 11.3 Manual evidence

| Block | 手動確認の扱い |
| --- | --- |
| B1 | contract固定のみ。GUI確認対象外 |
| B2 | UI非依存core中心。単独manual evidenceなし |
| B3 | UI非依存store中心。単独manual evidenceなし |
| B4 | 2026-08-09、母音Preview補修後の対象GUI確認通過・問題なし |
| B5 | 2026-08-10、preset UI / event override確認通過・問題なし |
| B6 | 2026-08-11、Section 11.7のlifecycle / persistence GUI確認通過・問題なし |

上記B4〜B6はユーザー報告であり、Codex自身の手動GUI実行ではない。B7で機能変更がなければ
範囲限定で再利用し、同じ確認を再要求しない。repairが対象挙動へ影響した場合だけ再確認範囲を提示する。

## 12. 受け入れ条件

- B1からB6の主要受け入れ条件が§15の証拠台帳へ統合される。
- Roadmap §9.4の三条件へcode、test、user、docsの証拠が対応付く。
- token / timeline / identity / effective shape / Preview / writerの横断契約に未評価の穴がない。
- preset JSON / INI / GenerationState / history / diagnosticsの横断契約に未評価の穴がない。
- TEXTあり／voice-only、failure / cancel、reset / restart / closeの保持・破棄境界が再検証される。
- MS22 direct regression、指定回帰、full suiteがpass表示・process exit code 0で終了する。
- `compileall src tests`と`git diff --check`がprocess exit code 0で終了する。
- B4 / B5 / B6のユーザー確認範囲、日付、実施者が正確に記録される。
- B7-PRE-001を含むruntime user dataのtracked / ignore境界がA判定前に解消または明示判断される。
- B7-PRE-002を含むcurrent statusの文書ずれが解消される。
- P1 / P2 / P3が分類され、残存事項のownerと再確認条件が記録される。
- A / B / C判定が条件どおりに確定される。
- dependency、package、build、license、fixed morph、VMD、30fps、audio、network契約に逸脱がない。
- B7 Closeout監査でproduction code / test code / GUIを変更していない。必要なrepairは別作業として記録される。
- Closeout判定後、Block Breakdown、Index、Roadmap、milestone / version historyが同じ状態へ同期される。
- 実MMD未確認がMS26に維持され、A判定の証拠へ誤って含まれない。
- A / Bの場合、次工程はMS23 Implementation Plan策定であり、MS23実装は開始しない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| runtime user dataを再びGit追跡する | `/presets.json`と`/MMD_AutoLipTool.ini`のroot限定ignore、追跡対象外、local file保持をCloseout前に確認する |
| local user fileをCloseoutで削除する | filesystem削除を禁止し、必要なら`git rm --cached`相当のrepository操作だけを明示対象にする |
| B5時点のP3をcurrent unresolvedと誤認する | B5履歴とB6解消証拠を両方保持し、current statusだけを同期する |
| 後続Blockのtestで前段契約を代替する | Block完了時証拠とcurrent revalidationを別列にする |
| pass件数だけでwx終了失敗を見落とす | process exit code、fatal、access violationを別記録する |
| ユーザー確認をCodex実行と誤記する | 実施者、日付、項目範囲を台帳へ明記する |
| 実MMD未確認を隠す | MS26 deferredを計画、判定、routing、報告へ必ず記載する |
| Closeout中に機能修正を混ぜる | P1 / P2修正はrepairへ分離し、Step 0から再監査する |
| historical記録をcurrent statusへ書き換える | 日付付き履歴は保持し、current status欄だけを更新する |
| package検証を不必要に拡大する | dependency / package差分なしならbuildを実行しない |

## 14. Codex実装時の注意

- B7はCloseout監査であり、新機能実装ではない。
- 最初にGit状態、HEAD、B7計画baseline commit、B6実装commitを確認する。
- コマンドは一つずつ実行し、並列・pipeline・連結実行をしない。
- production code、test code、GUIを変更しない。
- failureをtest期待値やfixture変更で隠さない。
- B7-PRE-001が未解決ならA判定へ進まない。
- `presets.json`やINIのlocal fileを削除・上書きしない。
- B4〜B6のユーザー報告をCodex自身の手動GUI実行と表現しない。
- 実MMD未確認をMS22完了条件から隠さない。
- fixed morph `あ / い / う / え / お`、wxPython、30fps、VMD、audio、network禁止を維持する。
- dependency、package、release、tag、merge、push、branch削除を行わない。
- A / B / C判定前にmilestone / version historyを完了扱いへ更新しない。
- plan / routing文書の作成・レビュー変更は、Closeout実装前に別commitへ固定する。

## 15. Closeout証拠台帳

B7実装時に、次の表をcurrent HEADの証拠へ更新する。ユーザー確認欄は報告された範囲だけを記録し、
Codex自身の手動GUI実行とは扱わない。

| Block | 主要契約 | 実装 / commit | Block完了時の自動証拠 | ユーザー確認 | 文書同期 | current finding / owner |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | normalized reading、decay終端zero、preset / INI、history、diagnostics、lifecycleのcontract固定 | `01a836a Complete MS22-B1 contract fixed` | 指定回帰336件、compileall、diff check / exit 0 | N/A。contract固定のみ | B1 plan、Block、Index、Roadmap | 完了。B7 current auditで再確認、P1 / P2 / P3なし |
| B2 | long-vowel token / timeline metadata、shared resolver、hold / decay、same-vowel分離 | `d8b78cc Implement MS22-B2 long-vowel core` | B2専用26件、full 644件＋7 subtests、compileall、diff check / exit 0 | 単独GUI対象外 | B2 plan、Pipeline、Block、Index、Roadmap | 完了。B7 current auditで再確認、P1 / P2 / P3なし |
| B3 | immutable GenerationSettings、built-in / user preset、JSON / INI、Custom fallback | `4ee67af Implement MS22-B3 preset store and settings contract`、`53308a1 Sync MS22-B3 documentation status` | B3専用23件＋19 subtests、full 667件＋26 subtests、compileall、diff check / exit 0 | 単独GUI対象外 | B3 plan、Pipeline / Error、Block、Index、Roadmap | B7-PRE-001のruntime file境界を分離repairで解消し、B7 auditで追跡対象外・ignore・local保持を確認 |
| B4 | GenerationState / OutputEditState、history、diagnostics、rollback、Preview integration | `624a9a8 Implement MS22-B4 output state and preview repair` | 関連33件、full 686件＋26 subtests、compileall、diff check / exit 0 | 2026-08-09通過・問題なし | B4 plan、README、仕様、routing | 完了。B7 current auditで再確認、P1 / P2 / P3なし |
| B5 | preset Select / Apply、create / update / rename / delete、terminal event override | `525ac1e Implement MS22-B5 preset UI and event overrides` | B5専用10件、splash除外full 694件、compileall、diff check / exit 0 | 2026-08-10通過・問題なし | B5 plan、README、仕様、routing | splashはB6で解消。B7-PRE-002のcurrent status同期済み、B7 auditで再確認 |
| B6 | lifecycle、persistence failure、splash / teardown、docs、manual evidence | `25301c4 Implement MS22-B6 lifecycle regression and docs` | B6 non-wx 7件、wx 9件、splash 3件、full 713件、compileall、diff check / exit 0 | 2026-08-11通過・問題なし | B6 plan、README、仕様、routing | 完了。B7 current auditで再確認、実MMDはMS26 |

### 15.1 B7計画作成baseline

- HEAD: `25301c4`
- branch: `feature/MS21-implementation`
- worktree: clean
- MS22 direct regression: 93 passed / process exit code 0
- full suite: 713 passed / process exit code 0
- `compileall src tests`: process exit code 0
- `git diff --check`: process exit code 0
- MS21 Closeout基準からdependency / package / build / license file差分: なし
- Plan creation baseline時点のCloseout判定: 未実施
- pre-closeout findings: B7-PRE-001 P2、B7-PRE-002 P3は分離repairで解消済み
- actual MMD verification: 未実施。MS26へdeferred

### 15.2 B7 Closeout監査結果（2026-08-12）

- current HEAD: `0dea6db Finalize MS22-B7 closeout plan`
- branch: `feature/MS21-implementation`
- audit開始時worktree: clean（監査後は本Closeout記録の文書変更が未コミット）
- MS22 direct regression: 93 passed / process exit code 0
- text / pipeline / Preview / writer / settings regression: 185 passed / process exit code 0
- MS21 effective output / history / lifecycle regression: 138 passed / process exit code 0
- MS17 / MS19 / MS20 input / diagnostics / save regression: 158 passed / process exit code 0
- B4 / B5 / splash combination: 18 passed / process exit code 0
- full suite: 713 passed / process exit code 0
- `compileall src tests`: process exit code 0
- `git diff --check`: process exit code 0
- runtime user data: `presets.json` / `MMD_AutoLipTool.ini` are untracked, root-ignored, and local `presets.json` is retained
- dependency / package / build / license files: `a18de64..HEAD` has no diff
- user GUI evidence: B4 / B5 / B6 reported checks passed; Codex did not execute GUI manually
- P1 / P2 / P3: none
- Closeout判定: **A**
- MS23: Implementation Plan策定へ進行可能。MS23実装は開始しない
- MS26: 実MMDでのVMD / WAV読み込み・リップ同期確認をdeferred

## 16. 実施後の報告形式

1. 確認したファイル
2. 変更したファイル
3. Closeout監査内容
4. 実行したテスト
5. テスト結果（pass表示 / failure / error / process exit code）
6. P1 / P2 / P3
7. Closeout判定（A / B / C）
8. 仕様からの逸脱
9. 未検証事項
10. MS23 / MS26への引き継ぎ
