# MS21-B7 Selected Event Tab Auto-Switch Additional Fix Plan

## 1. 文書情報

- 文書名: `MS21-B7 Selected Event Tab Auto-Switch Additional Fix Plan`
- 配置:
  `docs/Implementation_Plan/MS21-B7_Selected_Event_Tab_Auto_Switch_Additional_Fix_Plan.md`
- 対象Block: MS21-B7追加補正
- 補正名: Selected Event Tab Auto-Switch
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `3ccf630 Plan MS21-B7 state integration and sync efficiency`
- 作成日: 2026-07-27
- 文書ステータス:
  Complete / Automated Verification Passed /
  User Manual GUI Verification Passed
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B7_Implementation_Plan.md`
- 関連正本仕様:
  - `docs/GUI_State_Theme_Specification.md`

本計画は、MS21-B7のユーザー手動GUI確認で提示された小規模な操作性補正を扱う。
Previewタイムラインで単母音eventを明示選択した場合、RightPaneの表示タブを
「選択イベント」へ自動的に切り替える。

ユーザーはMS21-B7の手動GUI確認を実施し、その結果として本補正を要望した。
MS21-B7全体の手動確認完了と本補正の完了は同一視せず、本補正の実装・自動検証・
再確認結果が揃った後に関連文書の最終状態を判定する。

MS21のcanonical selection、adjustment、Undo / Redo、解析rollback、diagnostics、
VMD保存契約は変更しない。

## 2. 背景

現行GUIは、Previewタイムラインのevent clickを
`MainFrame._on_preview_selection_request()` で検証し、current base identity、
Preview render revision、Busy状態、選択可能event indexが一致した場合だけ
`UiState.commit_selected_source_event_index()` へ確定する。

確定後は次を同期する。

- `UiState.selected_source_event_index`
- selected base plan identity digest
- Preview highlight
- RightPaneの選択event editor内容

一方、RightPaneの`wx.Notebook`で現在表示しているタブは変更しない。このため、
InfoまたはWarningタブを表示中にタイムラインからeventを選択しても、ユーザーは
編集内容を見るために「選択イベント」タブをもう一度クリックする必要がある。

RightPaneには既に次の5タブがあり、「選択イベント」は既存pageである。

1. Info
2. Warning
3. 選択イベント
4. プリセット
5. モデルプロファイル

新しい編集画面やselection stateを追加する必要はなく、有効なユーザー選択に対する
Notebook表示制御だけで要望を満たせる。

## 3. 目的

- Previewタイムラインで有効な単母音eventを選択した直後に、RightPaneの
  「選択イベント」タブを表示する。
- 既に同じeventが選択されていても、タイムライン上で再クリックした場合は
  「選択イベント」タブを表示する。
- stale、Busy、不正index、empty click、drag panではタブを切り替えない。
- Undo / Redo、解析rollback、通常のUI再同期ではユーザーが閲覧中のタブを変更しない。
- selection、adjustment、history、diagnostics、save-state fingerprintを変更しない。

## 4. In Scope

- `RightPane`へ既存の「選択イベント」pageを表示する小さなview helperを追加する。
- page番号を固定値で指定せず、既存panelからNotebook pageを解決する。
- `MainFrame._on_preview_selection_request()` のcanonical commit成功後だけhelperを呼ぶ。
- 同一eventの再クリック時のタブ切替。
- valid / stale / Busy / same-event各経路のwx test。
- RightPane helper単体test。
- 実装完了後の本計画、B7計画、Block Breakdown、routing文書、
  GUI正本仕様への状態反映。
- ユーザー手動GUI再確認。

## 5. Out of Scope

- event選択state、base identity、hit-test、render revision契約の変更
- `UiState`へのselected tab state追加
- tab切替をUndo / Redo履歴へ含める変更
- Undo / Redo、解析failure / cancel rollback、通常同期による自動タブ切替
- selection clear時にInfoタブへ自動復帰する変更
- Warning発生時のWarningタブ自動表示
- selected editor control、adjustment、Preview shape、VMD出力の変更
- Notebookのタブ順、ラベル、レイアウト、themeの変更
- focusの強制移動、選択editor controlへの自動focus
- modal dialog、notice、Status表示の追加
- READMEや配布用readmeへの操作説明追加
- dependency、package、build、license、release、tag、merge、push
- fixed morph `あ / い / う / え / お` の変更
- Qt / PySide6、network、cloud、外部送信、background通信

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- current worktreeの未コミットB7実装と未追跡testをユーザー所有変更として保護する。
- Previewからのcanonical selection入口は
  `MainFrame._on_preview_selection_request()` を維持する。
- `UiState.commit_selected_source_event_index()` が`True`を返した場合だけ、
  user clickによるcurrent selection確定として扱う。
- `RightPane`は既存`panel_selected_event`をNotebook pageとして所有する。
- `wx.Notebook.FindPage()`、`GetSelection()`、`ChangeSelection()` はcurrent wxPythonで
  利用できる。
- tab表示はview stateであり、adjustment identity、history、fingerprint、
  diagnosticsの入力にはしない。

### 6.1 現行実装から確認した事実

- `RightPane.__init__()` は`wx.Notebook`を作成し、
  `_init_selected_event_tab()`で既存「選択イベント」pageを追加する。
- current production codeとtestには、Notebookの`SetSelection()`、
  `ChangeSelection()`、`GetSelection()`を使うタブ切替処理がない。
- current production codeには`EVT_NOTEBOOK_PAGE_CHANGED`等のNotebook page-change
  handlerがなく、tab変更を状態正本へ反映する経路もない。
- `_on_preview_selection_request()` はBusy、Preview validity、base identity、
  render revision、valid event indexを確認してからcanonical commitする。
- canonical commit成功後はPreview selectionとselected editor内容を更新するが、
  Notebook pageは変更しない。
- `commit_selected_source_event_index()` は、同一event indexの再選択も、有効なcurrent
  requestであれば成功として扱う。
- `update_selected_event_display()` はselection click以外に、event edit、reset、
  Undo / Redo、解析rollbackを含む同期経路からも呼ばれる。

### 6.2 計画作成時レビュー

- P1: なし。
- P2: なし。
- P3: なし。
- 初回自己監査で、本補正要望とB7全体のmanual verification完了を混同しない記録、
  current Notebook page-change handler不在の根拠を明記した。補正後の残存findingはない。
- `update_selected_event_display()`または`sync_ui_state()`へ自動切替を追加すると、
  Undo / Redoや解析rollbackでInfo / Warning閲覧を中断するため採用しない。
- page indexの固定値`2`は将来のタブ順変更に弱いため採用しない。
- `SetSelection()`によるNotebook change event発火は不要であるため、
  current pageと異なる場合だけ`ChangeSelection()`を使う。
- 既存selection / RightPane関連8件はpass表示、process exit code 0だった。

### 6.3 2026-07-27実装・自動検証結果

- `RightPane.show_selected_event_tab()`を追加し、`FindPage()`で既存pageを解決して、
  current pageと異なる場合だけ`ChangeSelection()`するようにした。
- `MainFrame._on_preview_selection_request()`のcanonical commit成功・selected editor
  表示更新後だけhelperを呼ぶ。共通の`sync_ui_state()`、
  `update_selected_event_display()`にはtab切替を追加していない。
- valid selection、same-event再click、stale request、Busy request、通常syncのtab保持を
  wx testへ追加した。
- RightPane helper testは、前方に追加pageを挿入して「選択イベント」のindexを変え、
  magic indexへ依存せずpageを解決することとNotebook page-change eventを発火しないことを
  確認した。
- RightPane限定3件、Preview selection限定6件、Undo / Redo・B7 lifecycle 12件、
  wx aggregate 90件、full suite 618件と7 subtestsはすべてpass表示・
  各process exit code 0だった。
- `compileall src tests`と`git diff --check`はprocess exit code 0だった。
- dependency、package、build、license、fixed morph、network、Qt、VMD出力に変更はない。
- 2026-07-27にユーザーから、追加補正を含むMS21-B7範囲の手動GUI確認は通過し、
  問題なしと報告された。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| `src/gui_wx/right_pane.py` | 既存「選択イベント」pageを安全に表示するview helper |
| `src/gui_wx/main_frame.py` | canonical Preview selection commit成功後のhelper呼び出し |

### 7.2 test変更対象

| ファイル | 確認内容 |
| --- | --- |
| `tests/test_wx_ms16_b3_right_pane.py` | helperが既存pageを解決し、重複切替を安全に扱う |
| `tests/test_wx_ms21_b3_preview_selection.py` | valid / same-event / stale / Busy requestとタブ状態 |

新規test fileは作らず、既存責務に一致する上記2 fileへ追加する。

### 7.3 関連確認対象

| ファイル | 確認内容 |
| --- | --- |
| `src/gui_wx/ui_state.py` | canonical commitの成功 / 拒否条件を変更しない |
| `src/gui_wx/preview_panel.py` | empty click / dragがselection requestを送らない現行契約 |
| `tests/test_wx_ms21_b6_undo_redo.py` | history navigationで閲覧中tabを変更しない |
| `tests/test_wx_ms21_b7_state_integration.py` | rollback / lifecycleでselection復元とtab表示を混同しない |
| `docs/GUI_State_Theme_Specification.md` | user click限定のタブ切替を実装後に記録する |

### 7.4 実装後の文書更新対象

- 本計画
- `docs/Implementation_Plan/MS21-B7_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/GUI_State_Theme_Specification.md`

READMEと配布用readmeは、既存のevent選択・編集説明を変更する機能追加ではないため、
原則更新しない。実装後の再チェックで説明上の齟齬が見つかった場合だけ対象へ追加する。

## 8. 実装方針

### 8.1 RightPane helper

`RightPane`へ、既存の`panel_selected_event`を表示するview helperを追加する。

処理規則:

1. `self.notebook.FindPage(self.panel_selected_event)` でpage indexを求める。
2. pageが見つからない場合はfail closedで何もしない。
3. current selectionが同じpageなら何もしない。
4. 異なる場合だけ`self.notebook.ChangeSelection(page_index)`を呼ぶ。
5. focusをeditor controlへ移さない。
6. selection、editor state、notice、scroll位置を変更しない。

helper名は、既存view helperの命名に合わせ
`show_selected_event_tab()`とする。

### 8.2 MainFrame接続

`MainFrame._on_preview_selection_request()`の次の順序を維持する。

1. request型とBusyを検証する。
2. Preview validity、render revision、base identityを検証する。
3. current base identityとvalid event indicesを構築する。
4. `UiState.commit_selected_source_event_index()`を呼ぶ。
5. commit失敗なら既存どおり何もしない。
6. commit成功後、Preview highlightとselected editor表示をcurrent selectionへ更新する。
7. 最後にRightPaneの「選択イベント」タブを表示する。

tab helperを`update_selected_event_display()`の内部へ置かない。
これにより、同関数を共有する次の経路ではtabを維持する。

- event edit / reset
- Undo / Redo
- adjustment-only sync
- analysis failure / cancel rollback
- full `sync_ui_state()`
- theme / playback / viewport再同期

### 8.3 同一event再クリック

current selectionとrequestのevent indexが同じ場合でも、canonical commitが成功すれば
tab helperを呼ぶ。

これにより、event選択後にInfo / Warningタブへ移動し、同じeventをタイムラインで
再クリックした場合も「選択イベント」へ戻れる。

同一event再クリックはselection変更ではないため、adjustment gesture、history、
editor revisionをタブ切替のために追加変更しない。現行canonical commitが行うrevision
更新は本補正で変更しない。

### 8.4 無効要求

次の場合は既存の早期returnまたはcommit失敗を維持し、tabを切り替えない。

- Busy中
- Preview invalid
- stale render revision
- stale / mismatch base identity
- valid event indices外
- bool、負数、非int index
- empty click
- drag pan
- mouse capture lost

## 9. 詳細ステップ

### Step 1: 実装前状態確認

1. branch、HEAD、worktree、未追跡fileを確認する。
2. B7 current diffを確認し、同一箇所のユーザー変更を保護する。
3. RightPane、MainFrame、UiState、PreviewPanel、関連testを再照合する。
4. selection / RightPane限定testを実行する。

### Step 2: RightPane helper

1. `show_selected_event_tab()`を追加する。
2. `FindPage()`で既存pageを解決する。
3. 未登録pageとalready-selected pageをno-opにする。
4. 異なるpageだけ`ChangeSelection()`する。
5. helper単体testを追加する。

### Step 3: Preview selection接続

1. `_on_preview_selection_request()`のcommit成功後へhelper呼び出しを追加する。
2. editor表示更新後にtabを切り替える。
3. same-event再クリックでも切り替える。
4. reject経路ではtabが変わらないtestを追加する。

### Step 4: lifecycle回帰

1. Undo / Redoでcurrent tabが変わらないことを確認する。
2. analysis rollbackでcurrent tabが変わらないことを確認する。
3. selection clearでInfoへ強制復帰しないことを確認する。
4. selected editor値、Preview highlight、diagnostics、saveabilityが変わらないことを確認する。

### Step 5: 検証と文書同期

1. RightPane / Preview selection限定testを実行する。
2. Undo / Redo / B7 lifecycle回帰を実行する。
3. wx aggregateとfull testを実行する。
4. `compileall src tests`と`git diff --check`を実行する。
5. 本計画と関連B7 / routing / GUI仕様を実装状態へ更新する。
6. ユーザー手動GUI確認後に完了状態を反映する。

## 10. 状態遷移 / データ契約

### 10.1 tab切替matrix

| 操作 | canonical commit | selection | RightPane tab |
| --- | --- | --- | --- |
| 未選択eventを有効click | success | clicked event | 選択イベントへ切替 |
| 別eventを有効click | success | clicked event | 選択イベントへ切替 |
| 同じeventを再click | success | 維持 | 選択イベントへ切替 |
| stale request | reject | 維持 | current tab維持 |
| Busy中click | reject | 維持 | current tab維持 |
| invalid index | reject | 維持 | current tab維持 |
| empty click | requestなし | 維持 | current tab維持 |
| drag pan | requestなし | 維持 | current tab維持 |
| Undo / Redo | 対象外 | current history規則 | current tab維持 |
| failure / cancel rollback | 対象外 | rollback規則 | current tab維持 |
| selection clear | 対象外 | clear | current tab維持 |

### 10.2 ownership

| state | owner | 本補正での変更 |
| --- | --- | --- |
| selected base event | `UiState` | なし |
| selected base identity | `UiState` | なし |
| Preview highlight | `PreviewModel` | なし |
| selected editor state | `RightPane` | なし |
| current Notebook page | `RightPane.notebook` | user click成功時だけ変更 |
| adjustment / history | `UiState` / history helper | なし |
| diagnostics / fingerprint | existing B7 sync | なし |

Notebook pageはsession内の一時的なview stateであり、workspace state、rollback snapshot、
Undo / Redo snapshot、report、settingsへ保存しない。

## 11. テスト方針

### 11.1 RightPane helper

- 初期Info表示から「選択イベント」へ切り替わる。
- 既に「選択イベント」表示中ならselectionを維持する。
- helperがpage順の固定値`2`へ依存しない。
- helper実行でselected editor stateやlabelを変更しない。

### 11.2 MainFrame selection

- valid current requestで「選択イベント」へ切り替わる。
- 別eventのvalid requestで切り替わる。
- 同じeventを再クリックしても切り替わる。
- stale render revisionでは現在のtabを維持する。
- base identity mismatchでは現在のtabを維持する。
- Busy中では現在のtabを維持する。
- invalid event indexでは現在のtabを維持する。
- reject時にselection、editor revision、adjustment、historyを変更しない。

### 11.3 interaction回帰

- empty clickとdrag panではtabを変更しない。
- Undo / Redoではtabを変更しない。
- event edit / resetではtabを変更しない。
- analysis failure / cancel rollbackではtabを変更しない。
- full / adjustment-only syncではtabを変更しない。
- selection clearでInfo tabへ強制移動しない。

### 11.4 実行候補

最小testから順に、一つずつ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b3_right_pane.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b3_preview_selection.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b6_undo_redo.py tests/test_wx_ms21_b7_state_integration.py -q
.\.venv\Scripts\python.exe -m pytest tests -k "wx_" -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

各test commandはpass表示とprocess exit codeを分けて報告する。

### 11.5 手動GUI確認

1. Infoタブ表示中に単母音eventをクリックし、「選択イベント」へ切り替わること。
2. Warningタブ表示中に別eventをクリックし、「選択イベント」へ切り替わること。
3. eventを選択後にInfoへ移動し、同じeventを再クリックして戻れること。
4. drag pan、empty lane、event外clickでは表示中tabが変わらないこと。
5. Busy中のclickでは表示中tabが変わらないこと。
6. Undo / RedoでInfo / Warning閲覧が中断されないこと。
7. 再解析failure / cancel rollbackで表示中tabが強制変更されないこと。
8. tab切替後も選択event、editor値、Preview highlightが一致すること。
9. keyboard focusがeditor controlへ強制移動しないこと。

## 12. 受け入れ条件

- valid current Preview selection requestのcommit成功後だけ「選択イベント」へ切り替わる。
- 同じeventの再クリックでも「選択イベント」へ切り替わる。
- stale、Busy、invalid requestではtabを変更しない。
- empty click、drag panではtabを変更しない。
- page indexの固定値へ依存しない。
- Notebook change eventを不要に発火しない。
- editor controlへfocusを強制移動しない。
- Undo / Redo、event edit / reset、analysis rollback、full sync、
  adjustment-only syncではtabを変更しない。
- selection clear時にInfo tabへ強制復帰しない。
- selection、base identity、adjustment、history、diagnostics、fingerprint、
  saveabilityを変更しない。
- fixed morph、VMD形式、30fps、wxPython主系を維持する。
- dependency、package、build、license、network契約に変更がない。
- 限定test、関連回帰、wx aggregate、full testがpass表示かつprocess exit code 0である。
- `compileall src tests`と`git diff --check`がprocess exit code 0である。
- 関連B7文書とGUI正本仕様が実装・検証状態へ同期される。
- ユーザー手動GUI確認は通過し、問題なしと報告されている。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| Undo / Redoで閲覧中tabを奪う | click handlerのcommit成功後だけhelperを呼ぶ |
| rollback復元でtabを奪う | display / sync共通関数へhelperを入れない |
| tab順変更で誤pageを表示する | `FindPage(panel_selected_event)`を使う |
| same-event再クリックで戻れない | index変更有無ではなくcommit成功を条件にする |
| stale requestでtabだけ切り替わる | 全validationとcanonical commit成功後に呼ぶ |
| Notebook event handlerへ不要な副作用を与える | `SetSelection()`ではなく`ChangeSelection()`を使う |
| editorへfocusが移りkeyboard操作が変わる | `SetFocus()`を呼ばずpage表示だけ変更する |
| tab stateをUndo / rollbackへ混入する | Notebook pageをview-only stateとして維持する |
| 小規模変更のためreject経路testが省略される | validとrejectのtab不変を同じwx testで固定する |
| current B7未コミット変更を上書きする | implementation前にcurrent diffを再確認して局所編集する |

## 14. Codex 実装時の注意

- 本計画作成時点ではproduction codeとtest codeを変更しない。
- 実装開始の明示指示後にだけコードを変更する。
- current B7未コミット変更と未追跡fileを保護する。
- tab切替を`sync_ui_state()`、`update_selected_event_display()`、
  adjustment resolverへ入れない。
- magic page indexを追加しない。
- tab表示のためにselectionを再commitしない。
- editor controlへfocusを強制移動しない。
- selection clear時の自動Info復帰を追加しない。
- tab stateをUiState、history、rollback snapshot、settingsへ追加しない。
- test expectationを弱めてpassさせない。
- wxPython主系を維持し、Qt / PySide6を復活させない。
- fixed morph `あ / い / う / え / お` を変更しない。
- network、cloud、外部送信、background通信を追加しない。
- dependency、package、release、tag、merge、pushを行わない。
- test結果はpass表示とprocess exit codeを分けて報告する。
- 実装完了時は次の形式で報告する。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
```
