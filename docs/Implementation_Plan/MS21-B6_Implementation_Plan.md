# MS21-B6 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B6 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B6_Implementation_Plan.md`
- 対象Block: MS21-B6
- Block名: In-Memory Undo / Redo
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `4bff439 Implement explicit event crossfade`
- 作成日: 2026-07-26
- 文書ステータス: Implemented / Automated Verification Passed / User GUI Verification Passed
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
- 前提計画:
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B5_Explicit_Event_Crossfade_Additional_Fix_Plan.md`

MS21-B6は、B2で導入したimmutable `AdjustmentLayerSnapshot` と、B4で作成した
単一event edit commit境界を利用し、現在のworkspace内だけで個別補正を
Undo / RedoできるようにするBlockである。

B6では補正履歴を新しい計算正本にしない。現在のcanonical adjustment snapshotを
履歴のcurrent stateとして保持し、Undo / Redoは過去のcanonical snapshotを復元する
transactionとする。Preview、RightPane、diagnostics、VMD保存は、復元されたsnapshotから
既存shared resolverを再実行して同期する。

## 2. 背景

MS21-B5追加補正完了時点で、発音eventの次のfieldを編集できる。

- 開口量
- 開始offset
- 終了offset
- 開口保持
- 閉口スムーズ
- 閉口傾斜比

各編集は `MainFrame._on_selected_event_edit_request()` から
`apply_adjustment_update()` を呼び、canonical snapshotを1回commitする。
選択eventのresetも同じupdate transactionを使用する。

B6着手前の実装には次の不足があった。

- `UiState.current_adjustment_snapshot` はcurrent値だけを保持し、過去snapshotを持たなかった。
- Undo / Redo stack、最大件数、redo破棄、coalescingは未実装だった。
- MainFrameに「編集」menuとUndo / Redo action stateがなかった。
- reset all adjustmentsの操作入口がなかった。
- `wx.SpinCtrl` / `wx.SpinCtrlDouble` はspin eventごとにcommitしていたため、
  長押しや連続key操作をそのまま履歴化すると1 gestureで履歴が多数増える状態だった。
- Preview / diagnostics / save-state fingerprintの再同期入口は存在するが、
  history navigationから使用する接続がなかった。

B1で次の履歴契約は固定済みである。

- history要素はadjustment layer全体のbefore / after snapshot。
- selection、tab、pan、zoom、playback位置はhistoryへ含めない。
- reset selected / reset allは各1 transaction。
- canonical no-opはhistoryを増やさず、redoも破棄しない。
- effective outputが同じでもrequested canonical snapshotが変わればhistoryへ記録する。
- 新規commit後はredoを破棄する。
- undo可能transactionは最大50件。
- 同一event・同一field・同一gesture内だけをcoalesceする。

## 3. 目的

- canonical adjustment snapshot全体を単位とするUndo / Redoを実装する。
- 51操作目で最古のundo可能transactionだけを破棄する。
- 同一controlの連続spinを1 gesture、1 transactionとして記録する。
- no-op、duplicate event、output-equivalent editを正しく区別する。
- reset selected / reset allをUndo可能な1 transactionにする。
- Undo / Redo後にPreview、RightPane、diagnostics、fingerprint、保存可否を再同期する。
- selection、viewport、playback、WARNING確認identityを不要に履歴化・破棄しない。
- Busy、stale base identity、不正snapshotではfail closedにする。
- 履歴をdisk、設定file、report、VMDへ永続化しない。

## 4. In Scope

- UI非依存のadjustment history DTO / transaction操作
- current snapshot、undo stack、redo stack、pending coalesced edit
- undo stack最大50件
- discrete editとcoalesced editの分離
- no-op判定とredo保持
- 新規edit後のredo破棄
- base identity一致検証
- `UiState` へのhistory state所有権統合
- `current_adjustment_snapshot` 既存参照との互換境界
- editor commit、reset selected、reset allのhistory transaction化
- 「編集」menu
- Ctrl+Z / Ctrl+Y
- Undo / Redo / reset selected / reset allのaction state
- Preview / RightPane / diagnostics / VMD saveability再同期
- B5 manual crossfadeとnoticeのUndo / Redo
- effective output identityとWARNING確認済みfingerprintの回帰
- current実装のworkspace reset / invalidation時history clear
- core、UiState、wx GUI、B2〜B5回帰test
- B6 plan、Block Breakdown、Index、Roadmapの進捗反映

## 5. Out of Scope

- historyのdisk保存
- app再起動後のhistory復元
- settings JSON、recent files、diagnostic reportへのhistory保存
- branch型history、任意位置へのjump、履歴一覧dialog
- history件数上限の設定化
- selection、tab、pan、zoom、playback、themeのUndo / Redo
- TEXT / transcription編集のUndo / Redo
- global parameter変更のUndo / Redo
- 入力file変更、解析実行、VMD保存、report保存のUndo / Redo
- B7所有のanalysis failure / cancel rollback完成
- B7所有の全lifecycle横断監査とREADME / 配布用readme / 正本仕様closeout
- MS22 preset / long-vowel実装
- VMD format、model name、Shift_JIS、30fpsの変更
- fixed morph `あ / い / う / え / お` の変更
- dependency、package、build、license、release、tag、merge、push
- Qt / PySide6、network、cloud、外部送信、background通信

## 6. 前提条件

### 6.1 実装前提

- 作業branchは `feature/MS21-implementation` とする。
- 基準worktreeはcleanである。
- B1からB5追加補正まで実装・自動検証・ユーザーGUI確認を完了している。
- `AdjustmentLayerSnapshot` はimmutableかつcanonicalである。
- `base_plan_identity` が異なるsnapshotを同じhistoryへ混在させない。
- current adjustmentの計算は引き続きB2 `apply_adjustment_update()` と
  `resolve_effective_shape_plan()` を使用する。
- history coreはwx object、widget値、PreviewData、diagnostics snapshotを保持しない。
- history navigation後もshared effective resolverを唯一のshape計算入口とする。
- dependency追加は不要である。

### 6.2 実装前に現行コードから確認した事実

- `UiState.set_current_adjustment_snapshot()` のproduction callerはMainFrameに限定される。
- `UiState.clear_adjustment_snapshot()` はanalysis success、analysis invalidation、
  workspace resetから到達する。
- editor field commitはidentity、selection、editor revisionを検証してから実行される。
- canonical snapshotが同じ場合、MainFrameは現在もstate commitと再同期を行わない。
- selected resetは選択eventのempty `EventAdjustment` を同じupdate transactionへ渡す。
- `sync_ui_state()` はeffective plan、Preview、RightPane、diagnostics、action stateを同期する。
- B5 fingerprintはeffective output identityであり、selection / history位置を含まない。
- WARNING確認済みfingerprintは現在outputと一致する場合だけ再利用される。
- RightPaneのspin controlsはspin eventごとにtyped edit requestを送る。
- Enter、focus loss、mouse release、別field、selection、reset、Undo / Redoは
  coalescing boundaryとして利用できる。

### 6.3 計画作成baseline

- B2 adjustment / resolver、B4 editor、B5 crossfade関連56件:
  pass表示、process exit code 0
- B4 wx editor、MS14 state、workspace reset関連20件:
  pass表示、process exit code 0
- B5 effective identity、adjusted save、Warning policy関連23件:
  pass表示、process exit code 0
- production code、test code、dependency、build設定は本計画作成時点で変更していない。

### 6.4 実装状態整合レビュー

2026-07-26に現行implementationとの再照合を行い、P1なし、P2 2件、P3 1件を
検出して本計画内で解消した。

- P2: cleanup operation noticeはsnapshot単体から再導出できないため、
  Undo / Redo時は汎用operation noticeへ置換し、effect / crossfade noticeだけを
  restored snapshotから再導出する契約へ修正した。
- P2: SpinCtrl gestureの開始・終了とstale boundaryが未確定だったため、
  mouse / key down-up、wheel / tokenなしdiscrete fallback、token完全一致、
  global boundary専用APIを固定した。
- P3: history APIのidentity引数名を既存UiStateと同じ
  `expected_base_plan_identity_digest` へ統一した。

修正後の再照合では残存P1 / P2 / P3なしと判定した。production code、test code、
dependency、build設定は変更していない。

### 6.5 実装前チェック

2026-07-26に実装前チェックを行い、P1なし、P2 2件、P3 1件を検出して
本計画内で解消した。

- P2: selected event editorへfocusがある場合のCtrl+Z / Ctrl+Yと、
  未確定・不正入力、他TEXT controlのnative Undo / Redoとの優先順位を固定した。
- P2: RightPane-local active token / wheel markerの維持・破棄条件を固定した。
- P3: selection / Busy等のpending確定境界と、base identity変更 / history clear時の
  pending破棄を分離した。

補正後の再照合では残存P1 / P2 / P3なしと判定した。計画対象APIとwx event / menu IDは
Python 3.14.3、wxPython 4.2.5 msw上に存在する。関連回帰119件はすべてpass表示・
各process exit code 0であり、production code、test code、dependency、build設定は
変更していない。

### 6.6 実装・検証結果

2026-07-26にMS21-B6を実装した。

- immutable history state、before / after transaction、最大50件、redo管理、
  coalescing、identity validationを `src/core/event_adjustment_history.py` へ追加した。
- `UiState` がhistory stateを所有し、current snapshot互換property、commit、finish、
  Undo、Redo、clearのAPIを提供する構成へ移行した。
- RightPaneでmouse / key gesture token、wheel / tokenなしdiscrete fallback、
  matching boundary、stale boundary無視を接続した。
- MainFrameへ編集menu、選択的なCtrl+Z / Ctrl+Y、action state、reset selected /
  reset all、dirty入力guard、history navigation後の `sync_ui_state()` を接続した。
- selection、Busy、resetではpendingを確定し、analysis success、invalidation、
  workspace resetではhistoryを破棄する現行B6 lifecycleを実装した。
- B6 core testは12件、B6 wx testは最終9件、B2 / B4回帰は46件、B5回帰は28件、
  MS19 / MS20回帰は25件がpass表示し、各process exit codeは0だった。
- 最終全体testは602件と7 subtestsがpass表示し、process exit code 0だった。
  `compileall src tests` と `git diff --check` もprocess exit code 0だった。
- 2026-07-26にユーザー手動GUI確認は全項目通過・問題なしと報告された。
- dependency、package、build、license、fixed morph、network、Qt、VMD formatは
  変更していない。B7所有のanalysis failure / cancel rollback完成と正本仕様closeoutは
  未実施である。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/core/event_adjustment_history.py` | immutable history state、transaction、coalescing、Undo / Redo、50件上限、identity validation |
| `src/core/__init__.py` | B6 public DTO / pure functionのadditive export |
| `src/gui_wx/ui_state.py` | history state所有、current snapshot互換property、commit / finish / undo / redo / clear |
| `src/gui_wx/selected_event_editor.py` | typed edit requestへGUI非依存のcoalescing tokenをadditiveに追加 |
| `src/gui_wx/right_pane.py` | spin gesture開始・更新・終了通知、reset selected既存導線維持 |
| `src/gui_wx/main_frame.py` | 編集menu、shortcut、action state、history commit、Undo / Redo、reset all、再同期 |

### 7.2 関連確認対象

| ファイル | 確認内容 |
| --- | --- |
| `src/core/event_adjustment.py` | canonical snapshot / identity / no-op契約。history責務を混在させない |
| `src/core/effective_shape_plan.py` | restored snapshotから同じeffective planを生成できること |
| `src/gui_wx/app_controller.py` | workspace reset、input commit、save failureでhistoryを誤変更しないこと |
| `src/gui_wx/output_diagnostics_adapter.py` | history位置をfingerprintへ含めないこと |
| `src/core/output_diagnostics.py` | effective output identityとWARNING確認再利用契約 |
| `src/vmd_writer/effective_shape_adapter.py` | Undo / Redo後もPreviewとwriterが同じplanを使うこと |

### 7.3 新規test候補

- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_wx_ms21_b6_undo_redo.py`

責務が既存testに一致する場合は次へ追加してよい。

- `tests/test_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_explicit_event_crossfade.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms19_b8_workspace_reset.py`

### 7.4 文書更新対象

B6実装・ユーザー確認後に次だけを進捗同期する。

- 本計画
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

README、`readme_mmdautolip.txt`、Pipeline / GUI / Error正本仕様の横断同期は
Block BreakdownどおりB7で行う。

## 8. 実装方針

### 8.1 historyの唯一のcurrent state

`AdjustmentHistoryState` は次を保持する。

```text
AdjustmentHistoryState
  current_snapshot: AdjustmentLayerSnapshot
  undo_transactions: tuple[AdjustmentHistoryTransaction, ...]
  redo_transactions: tuple[AdjustmentHistoryTransaction, ...]
  pending_edit: PendingAdjustmentHistoryEdit | None
```

`UiState.current_adjustment_snapshot` はhistory stateの `current_snapshot` を返す
compatibility propertyとする。current snapshotとhistory currentを別fieldとして
二重保持しない。

history未初期化時だけ `current_adjustment_snapshot is None` を許可する。
有効なbase planからempty snapshotを初期化する操作はhistory transactionにしない。

### 8.2 transaction契約

```text
AdjustmentHistoryTransaction
  before_snapshot
  after_snapshot
```

- before / afterは同じ `base_plan_identity` を持つ。
- beforeとafterが等しいtransactionは保持しない。
- transactionはsnapshot全体を保持する。
- event deltaだけを保存し、復元時に再canonicalizeしない。
- Undoは最新transactionのbeforeをcurrentへ戻し、transactionをredo側へ移す。
- Redoはredo transactionのafterをcurrentへ戻し、transactionをundo側へ移す。
- transaction順序はdeterministic tupleとする。
- public functionはinvalid type、identity mismatch、stale currentを
  `AdjustmentContractError` で拒否する。

### 8.3 最大50操作

`MAX_ADJUSTMENT_HISTORY_TRANSACTIONS = 50` をcoreへ固定する。

- discrete transactionまたはcoalesced transaction確定時にundo側へ追加する。
- 51件目ではindex 0の最古transactionだけを破棄する。
- redo側はUndo回数に応じて保持し、独立した50件設定を追加しない。
- pending editは確定前なので50件へ数えない。
- limitをGUI設定やsettings storeへ追加しない。

### 8.4 discrete edit

次は各1 transactionとして即時確定する。

- Enter / focus lossでcommitされたtext edit
- coalescing tokenを持たない単発edit
- reset selected
- reset all

新規discrete editの前にpending coalesced editを確定する。
canonical afterがcurrentと同じ場合はtransactionを作らず、redoも維持する。
afterが異なる場合だけredoを破棄する。

### 8.5 coalesced edit

coalescing keyは少なくとも次を含む。

```text
base identity digest
base_event_index
field
RightPane-local gesture token
```

同一key内の最初のeffective update時にbefore snapshotをpendingへ保存し、
以降はcurrent / latest afterだけを置き換える。undo stackにはまだ追加しない。

次をboundaryとしてpending editを確定する。

- mouse release
- key release
- Enter
- focus loss
- 別fieldのedit
- selection変更
- reset selected / reset all
- Undo / Redo
- Busy開始

確定時にlatest afterがbeforeと同じならtransactionを追加せず、既存redoを維持する。
異なる場合だけ1 transactionを追加してredoを破棄する。

base identity変更、analysis success、input / parameter invalidation、workspace reset、
`clear_adjustment_history()` はtransaction境界ではなくworkspace破棄境界である。
これらではpendingをundoへ確定せず、current、undo、redo、pendingを一括破棄する。

### 8.6 RightPane gesture adapter

RightPaneはwx eventをhistory coreへ直接渡さない。

- `SelectedEventEditRequest` へ
  `coalescing_token: int | None = None` をdefault付きでadditiveに追加し、
  B4 / B5の既存生成箇所とtestを壊さない。
- SpinCtrl / SpinCtrlDoubleの `EVT_LEFT_DOWN` または `EVT_KEY_DOWN` で
  panel-local monotonically increasing tokenを発行する。同一fieldで既にactiveな
  tokenがある場合は再発行せず、key autorepeatを同じgestureに保つ。
- active token中のspin eventへtokenを付ける。
- 対応する `EVT_LEFT_UP` / `EVT_KEY_UP` で、fieldとtokenを含むtyped boundary
  callbackを送る。
- `EVT_MOUSEWHEEL` は次に発生する同一fieldのspinをdiscreteとするone-shot markerだけを
  設定し、wheel handler自体からedit requestを送らない。対応するspinと、
  start eventを取得できずactive tokenがないspinは、
  `coalescing_token=None` のdiscrete editとして扱う。異なる物理操作を推測で結合せず、
  wheelとspinから同じ値を二重commitしない。
- Enter、focus lossではactive tokenがある場合だけ同じfield / tokenのboundaryを
  先に送り、続くtext commitはdiscrete editとして扱う。
- field変更時は以前のtokenを閉じてから新しいtokenを開始する。
- `set_selected_event_editor_state()` によるprogrammatic control更新はgestureを開始しない。
- duplicate `EVT_TEXT` / `EVT_SPINCTRL` はcanonical no-opとして追加履歴を作らない。
- peak text fieldは現在どおりEnterまたはfocus lossで1回commitし、continuous previewを
  新規追加しない。

RightPane-local boundary callbackはfieldとtokenを必須とする。UiState / history coreは
pending keyと完全一致するboundaryだけを確定し、古いtoken、別field、別eventの
boundaryではcurrent、undo、redo、pendingを変更しない。selection変更、reset、
Undo / Redo、Busy開始のようなMainFrame所有のglobal boundaryだけは、明示的な
`finish_current_adjustment_coalescing()` を使用してcurrent pendingを確定する。

RightPane-local gesture stateは次の規則で管理する。

- matching mouse / key releaseを送信した直後は、history callbackの成否にかかわらず
  active field / tokenをclearする。
- 同一base identity・同一selected event・同一fieldのcontinuous spin中に
  `set_selected_event_editor_state()` でprogrammatic refreshしてもactive tokenを保持する。
- wheel one-shot markerは対応する同一fieldの最初のspinで必ずconsumeする。
- selection変更、base identity変更、Busy開始、reset、history clear、editor非表示化、
  control無効化ではactive tokenとwheel markerをclearする。
- selection変更、reset、Undo / Redo、Busy開始ではMainFrameがhistory pendingを
  確定してからRightPane-local stateをclearする。
- base identity変更、analysis success、input / parameter invalidation、workspace reset、
  history clearではhistory pendingを確定せず、historyとRightPane-local stateを破棄する。
- clear後に届いたold release / wheel callbackはstaleとして無視し、新しいgestureを
  終了・開始しない。

wxPython 4.2.5 / Windows上のevent順をRightPane-local adapter testで固定する。
mouse / keyのstart / end eventが得られない経路はdiscrete fallbackとし、
timerベースの曖昧なcoalescing、mouse button状態のpolling、background threadは使わない。

### 8.7 UiState API

UiStateへ責務を分けたAPIを追加する。

```text
initialize_adjustment_history(snapshot, expected_base_plan_identity_digest)
commit_adjustment_snapshot(
    snapshot,
    expected_base_plan_identity_digest,
    coalesce_key=None,
)
finish_adjustment_coalescing(expected_coalesce_key)
finish_current_adjustment_coalescing()
undo_adjustment_snapshot()
redo_adjustment_snapshot()
clear_adjustment_history()
```

- initializeはcurrentを設定するがundo / redoを増やさない。
- commitはhistory core resultを採用し、current変更時だけeditor revisionを増やす。
- finishだけでcurrentが変わらない場合、editor revisionを増やさない。
- `finish_adjustment_coalescing()` はpending keyとの完全一致時だけ確定し、
  stale / mismatch keyでは全stateを変更しない。
- `finish_current_adjustment_coalescing()` はMainFrameが所有するglobal boundary専用とし、
  RightPane-local callbackから呼ばない。
- undo / redo成功時はeditor revisionを増やす。
- clearはcurrent、undo、redo、pendingを一括破棄する。
- `has_event_adjustments` はcurrent snapshotだけから導出する。
- `can_undo_adjustment` / `can_redo_adjustment` はhistory stateから導出する。
- invalid identityではstate全体を変更しない。

### 8.8 Edit menu / shortcut

MainFrameへ「編集(&E)」menuをFile menuとSettings / View menuの間に追加する。

```text
個別補正を元に戻す (Ctrl+Z)
個別補正をやり直す (Ctrl+Y)
----------------------------
選択イベントの補正をリセット
すべての個別補正をリセット
```

- Undoは `wx.ID_UNDO`、Redoは `wx.ID_REDO` を使用できる場合は使用する。
- menu clickはUndo / Redo handlerへ直接routeする。
- Ctrl+Z / Ctrl+YはMainFrame `EVT_CHAR_HOOK` で選択的にrouteし、
  全TextCtrlへ作用するglobal acceleratorとして登録しない。
- focusがselected event editor内にあり、control値が現在のrequested値と一致する
  clean状態ではadjustment Undo / Redoへrouteする。active spin pendingがあれば
  global boundaryとして先に確定する。
- focusがselected event editor内にあり、直接入力値が未確定または不正なdirty状態では、
  Ctrl+Z / Ctrl+Yのhistory navigationを実行しない。control値をcommit・破棄せず、
  `Enterで値を確定するか、入力内容を修正してください。` をinline表示する。
- menu clickによるfocus lossでvalid値が既存commit経路から確定した場合は、
  そのtransactionを含むcurrent historyに対してmenu Undo / Redoを実行する。
  invalid値が残る場合はhistory navigationを実行しない。
- focusがtranscription editor等、selected event editor以外のeditable text control内に
  ある場合、MainFrameはCtrl+Z / Ctrl+Yをconsumeせず `event.Skip()` し、
  control固有のnative Undo / Redoを維持する。TEXT / transcriptionをadjustment historyへ
  混在させない。
- selected event editor外のnon-editable領域ではCtrl+Z / Ctrl+Yをadjustment
  Undo / Redoへrouteする。
- reset selected menuは既存RightPane buttonと同じhandlerへrouteする。
- reset allは確認dialogを追加しない。Undo可能な1 transactionであることを優先する。
- reset allはempty canonical snapshotをcommitし、base planやselectionを変更しない。

### 8.9 action state

| Action | 有効条件 |
| --- | --- |
| Undo | not Busy、current base / history valid、undo可能または確定可能なpending editあり |
| Redo | not Busy、current base / history valid、redoあり、non-no-op pending editなし |
| Reset selected | not Busy、canonical selection valid、選択eventにoverrideあり |
| Reset all | not Busy、current snapshotに1件以上adjustmentあり |

Busy、stale base、未解析、再解析待ちでは4 actionを無効化する。
keyboard shortcutもdisabled menu itemと同じBusy / base / history guardを通し、
selected event editorのdirty guardを追加する。handler単独でもfail closedにする。

### 8.10 Undo / Redo後の再同期

history navigation成功後は次の順で既存入口を使用する。

1. selected operation noticeを更新する。
2. `sync_ui_state()` を1回呼ぶ。
3. restored snapshotからeffective planを解決する。
4. Previewを更新する。
5. selected eventが同じbaseでvalidなら保持し、RightPane editorを更新する。
6. diagnostics snapshot、saveability、fingerprint、button / menu stateを更新する。

selection、viewport、playback位置はhistoryに含めず、同一base内では保持する。
selected eventがcurrent baseに存在しない場合だけ既存strict selection規則でclearする。

operation noticeは少なくとも次を区別する。

- `個別補正を元に戻しました。`
- `個別補正をやり直しました。`
- `選択イベントの補正をリセットしました。`
- `すべての個別補正をリセットしました。`

B4 tail / slope cleanup noticeは `apply_adjustment_update()` の遷移結果から生成される
編集直後だけのoperation noticeであり、snapshot単体から再導出しない。
Undo / Redo時は以前のcleanup operation noticeをclearし、上記のUndo / Redo汎用文言へ
置き換える。Redo時にも過去のcleanup理由を再現しない。

B4 effect noticeとB5 crossfade noticeはrestored snapshotからeffective planと
`SelectedEventEditorState` を再構築して再導出する。operation notice、cleanup理由、
effect / crossfade notice文字列をhistory transactionへ保存しない。

### 8.11 fingerprint / WARNING確認

- history位置、undo件数、redo件数、coalescing tokenをfingerprintへ追加しない。
- Undo / Redoでeffective outputが変われば既存effective output fingerprintが変わる。
- output-equivalentなrequested snapshot変更ではfingerprintを変えない。
- `confirmed_warning_save_state_fingerprint` はhistory navigationだけでは明示clearしない。
- restored outputのfingerprintが確認済み値と同じなら既存確認を再利用する。
- 異なる場合は既存B5保存policyが再確認する。
- history navigation自体をdiagnostics WARNING / ERRORへ追加しない。

### 8.12 B5 manual crossfade

B5 manual crossfadeはcanonical adjustmentから再導出するため、history固有payloadを
追加しない。

- crossfadeを作るtail editのUndoでshapeとnoticeが消える。
- Redoで同じshapeとnoticeが復元する。
- 0.95以上のtarget値をUndo / Redoでclipしない。
- automatic handoffとmanual metadataの差分帰属を変更しない。

### 8.13 lifecycle責務境界

B6ではcurrent実装に必要な安全なclear / lockだけを接続する。

- analysis開始中はBusyによりedit / reset / Undo / Redoをlockし、historyを表示状態と
  一緒に保持する。
- current analysis success、新base commit、input / parameter invalidation、
  workspace resetではcurrent snapshotとhistoryを一括clearする。
- analysis cancelが現在のadjustmentを保持する現行経路ではhistoryも保持する。
- VMD / report save success、cancel、failureではhistoryを変更しない。
- late / stale GUI requestはhistoryを変更しない。

analysis failure / cancel時に旧baseとhistoryを条件付きrollbackするB1将来契約の完成、
audio / analysis job IDを含む横断監査はB7へ残す。B6でB7を先行実装しない。

## 9. 詳細ステップ

### Step 1: pre-implementation check

1. branch、HEAD、worktreeを確認する。
2. B1 history契約とB2 snapshot validationを再読する。
3. B4 edit / reset commitとRightPane wx event順を確認する。
4. B5 fingerprint / save / crossfade契約を確認する。
5. UiState / MainFrame / AppControllerのclear、Busy、cancel、reset経路を照合する。
6. baseline testを再実行し、findingをP1 / P2 / P3へ分類する。

### Step 2: core history

1. immutable history DTOを追加する。
2. snapshot / identity validationを追加する。
3. discrete commit、pending coalescing、finishを実装する。
4. Undo / Redoを実装する。
5. 50件上限を実装する。
6. no-op / redo保持 / redo破棄をtestする。

### Step 3: UiState integration

1. history stateをUiStateへ追加する。
2. current snapshot compatibility propertyを接続する。
3. initialize / commit / finish / undo / redo / clear APIを追加する。
4. editor revisionとaction state derivationを接続する。
5. reset workspace / invalidation / successのclearを一括化する。

### Step 4: RightPane coalescing

1. typed gesture tokenとboundary callbackを追加する。
2. mouse / key spin gestureをdown / upとtokenでdeterministicに区切る。
3. wheel / tokenなしspinをdiscrete fallbackにする。
4. same gestureのprogrammatic refreshではtokenを保持し、それ以外のlifecycleでclearする。
5. programmatic updateをhistory eventから除外する。
6. Enter / focus loss duplicateをno-opにする。
7. stale token boundaryの完全不変とgesture event順のwx testを追加する。

### Step 5: MainFrame menu / transaction

1. Edit menuと4 actionを追加する。
2. existing event editをhistory commitへ変更する。
3. selected resetをhistory transactionへ変更する。
4. reset all handlerを追加する。
5. Undo / Redo handlerを追加する。
6. selected editor dirty判定とselective `EVT_CHAR_HOOK` routingを追加する。
7. Busy / stale / disabled guardを追加する。

### Step 6: resynchronization

1. Undo / Redo後に`sync_ui_state()`を1回呼ぶ。
2. selection保持とeditor revisionを確認する。
3. Preview shapeを確認する。
4. diagnostics、fingerprint、saveabilityを確認する。
5. B5 crossfade noticeを確認する。

### Step 7: lifecycle minimum

1. analysis success / invalidation / resetでhistoryをclearする。
2. Busy中の全history actionをlockする。
3. current cancel保持経路でhistoryを保持する。
4. save cancel / failureでhistoryを保持する。
5. B7 rollback完成を先行実装していないことを確認する。

### Step 8: validation / docs

1. core history testを実行する。
2. UiState / wx history testを実行する。
3. B2〜B5回帰を実行する。
4. lifecycle / diagnostics / save回帰を実行する。
5. full testとcompileallを実行する。
6. `git diff --check` を実行する。
7. ユーザーGUI確認後にB6 planとrouting文書へ結果を反映する。

## 10. 状態遷移 / データ契約

### 10.1 history基本遷移

| 操作 | current | undo | redo | pending |
| --- | --- | --- | --- | --- |
| initialize | base empty / supplied snapshot | empty | empty | none |
| discrete no-op | unchanged | unchanged | unchanged | none |
| discrete change | after | beforeをpush | clear | none |
| coalesced update | latest after | unchanged |一時保持 | before / key |
| finish changed | latest after | before→afterを1件push | clear | none |
| finish no-op | before | unchanged | unchanged | none |
| Undo | transaction.before | 1件pop | transactionをpush | none |
| Redo | transaction.after | transactionをpush | 1件pop | none |
| clear | historyなし | historyなし | historyなし | historyなし |

`clear` はpendingをtransactionへ確定せず破棄する。selection変更、reset、Undo / Redo、
Busy開始で使用する `finish_current_adjustment_coalescing()` と混同しない。

### 10.2 base identity

- current、undo、redo、pendingの全snapshotは同じbase identityを持つ。
- mismatch requestは例外またはfalse resultでfail closedにする。
- mismatch時に一部stackだけを変更しない。
- new base初期化は旧historyを全破棄してから行う。

### 10.3 reset

| 操作 | after snapshot | selection | history |
| --- | --- | --- | --- |
| reset selected | 選択entry除去後のcanonical全体 | 保持 | 1 transaction |
| reset all | current identityのempty snapshot | 保持 | 1 transaction |
| workspace reset | historyなし | clear | Undo不可 |

### 10.4 action / status

Undo / Redo成功は操作noticeとしてRightPaneへ表示してよいが、bottom Statusの
解析・保存可否を独自文字列で上書きしない。bottom Statusは既存diagnostics snapshotから
導出する。

## 11. テスト方針

### 11.1 core history

- initializeではundo / redoなし。
- discrete changeをUndo / Redoできる。
- full snapshotの複数event adjustmentを復元する。
- 51操作目で最古1件だけを破棄する。
- Undo後の新規editでredoを破棄する。
- no-opはundoを増やさずredoを保持する。
- output-equivalent snapshot changeもhistoryへ記録する。
- different base identityを拒否する。
- stale currentを拒否する。
- invalid typeを拒否する。

### 11.2 coalescing

- 同一event / field / tokenの複数updateが1 transactionになる。
- event、field、tokenのいずれかが変わればboundaryになる。
- mouse / key releaseで確定する。
- key autorepeatでは同じtokenを維持する。
- mouse wheelとtokenなしspinは各eventをdiscrete transactionとして扱う。
- stale / mismatch tokenのboundaryはcurrent / undo / redo / pendingを変更しない。
- same eventのprogrammatic refreshではactive tokenを保持する。
- selection / Busy / resetではpending確定後にlocal tokenをclearする。
- base変更 / invalidation / history clearではpendingを確定せずlocal tokenごと破棄する。
- clear後のold releaseは新しいgesture stateを変更しない。
- Enter / focus loss duplicateで履歴を増やさない。
- gesture中にbeforeへ戻った場合、transactionを作らずredoを保持する。
- reset / Undo / Redoがpendingを先に確定する。
- 50件上限はgesture件数で数える。

### 11.3 UiState

- current snapshot compatibility propertyがhistory currentと一致する。
- current変更時だけeditor revisionが増える。
- failed commitでstate / revisionが不変。
- `has_event_adjustments` がcurrentから導出される。
- clearでcurrent / undo / redo / pendingが消える。
- Busy中のhandlerがstateを変更しない。

### 11.4 MainFrame / wx

- Edit menuに4 actionとshortcutがある。
- selected editorがcleanなら、focus中でもCtrl+Z / Ctrl+Yでadjustment historyを移動する。
- selected editorに未確定・不正な直接入力がある場合、Ctrl+Z / Ctrl+Yで値やhistoryを
  変更せずinline案内を表示する。
- selected editor以外のeditable text controlではCtrl+Z / Ctrl+Yをconsumeせず、
  adjustment historyを変更しない。
- 未解析時は全action disabled。
- edit後にUndo enabled、Redo disabled。
- Undo後にRedo enabled。
- new edit後にRedo disabled。
- selected reset buttonとmenuが同じtransactionになる。
- reset allが1 transactionで、Undoで全eventを戻せる。
- 連続spinが1 transactionになる。
- mouse wheelとgesture startを取得できないspinが異なる操作間でcoalesceされない。
- selection変更がhistoryへ入らず、pending boundaryになる。
- stale editor request / tokenを拒否する。

### 11.5 Preview / diagnostics / writer

- Undo / RedoでPreview control pointがbefore / afterへ戻る。
- selected eventとviewportを保持する。
- fingerprintはeffective outputに従って戻る。
- output-equivalent editではfingerprintが同じでもhistoryは移動する。
- confirmed WARNING fingerprintをidentity一致時だけ再利用する。
- VMD saveabilityがrestored diagnosticsへ従う。
- manual crossfade shape / noticeがUndoで消えRedoで戻る。
- target 1.0超をclipしない。

### 11.6 lifecycle回帰

- workspace resetでhistoryをclearする。
- current analysis successで旧historyをclearする。
- parameter / input invalidationでhistoryをclearする。
- current cancel保持経路ではhistoryを保持する。
- save success / cancel / failureでhistoryを保持する。
- late / stale callbackでhistoryが変わらない。
- TEXTあり / voice_onlyで同じhistory契約を使う。

### 11.7 実行コマンド候補

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b6_adjustment_history.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b6_undo_redo.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_event_adjustment.py tests/test_ms21_b2_effective_shape_plan.py tests/test_ms21_b4_selected_event_editor.py tests/test_wx_ms21_b4_selected_event_editor.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b5_effective_output_identity.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_ms21_b5_explicit_event_crossfade.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_ms19_b8_workspace_reset.py tests/test_wx_ms14_b2_state.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

各test commandはpass表示とprocess exit codeを分けて記録する。

### 11.8 ユーザー手動GUI確認候補

1. 解析後、個別補正を1回行うとUndoが有効になること。
2. Ctrl+ZでPreview、editor値、VMD保存内容が編集前へ戻ること。
3. Ctrl+Yで同じ編集結果が復元すること。
4. spin controlを長押しして複数値を通過しても、Ctrl+Z 1回でgesture前へ戻ること。
5. selected editorへ未確定値を直接入力した状態のCtrl+Z / Ctrl+Yでは値とhistoryが
   変わらず、inline案内が表示されること。
6. transcription等の別TEXT editorではnative Ctrl+Z / Ctrl+Yを妨げず、
   adjustment historyが変わらないこと。
7. 別field編集は別のUndo操作になること。
8. event選択、pan、zoom、playbackがUndo対象にならないこと。
9. reset selectedをUndoできること。
10. reset allで全eventがbaseへ戻り、Undo 1回で全補正が戻ること。
11. Undo後の新規editでRedoできなくなること。
12. crossfade editのUndoで重複とnoticeが消え、Redoで戻ること。
13. output-equivalentなrequested tail editもUndoできること。
14. Busy中はmenu、shortcut、resetが無効であること。
15. VMD保存cancel / failure後もUndo / Redoできること。
16. workspace reset後は旧補正をUndoできないこと。
17. TEXTあり / voice_onlyの両方で同じ挙動になること。

## 12. 受け入れ条件

- historyのcurrentはcanonical adjustment snapshotである。
- current snapshotをhistory外へ二重保持しない。
- Undo / Redoがadjustment layer全体を正確に復元する。
- 51操作目で最古のundo可能transactionだけを破棄する。
- Undo後の新規editでredoを破棄する。
- canonical no-opがhistoryを増やさずredoを破棄しない。
- requested snapshot変更はeffective outputが同じでもhistoryへ記録する。
- 同一event・field・gestureだけを1操作へcoalesceする。
- token一致するlocal boundaryだけがpending gestureを確定する。
- mouse wheelとtokenなしspinを推測で連結しない。
- same gestureのprogrammatic refreshではactive tokenを保持する。
- selection / Busy / resetではpending確定後、base変更 / clearではpending破棄後に
  RightPane-local gesture stateをclearする。
- timer依存の不定なcoalescingを使用しない。
- reset selected / reset allが各1 transactionでUndo可能である。
- selection、tab、viewport、playbackをhistoryへ含めない。
- Busy、stale identity、不正snapshotでhistoryを変更しない。
- selected editorのdirty直接入力をCtrl+Z / Ctrl+Yで暗黙commit・破棄しない。
- selected editor以外のeditable text controlのnative Undo / Redoを奪わない。
- Undo / Redo後にPreview、RightPane、diagnostics、fingerprint、saveabilityが同期する。
- history位置だけでfingerprintを変えない。
- confirmed WARNING fingerprintを無条件clearしない。
- B5 manual crossfadeと0.95 noticeを同じsnapshotから復元する。
- current lifecycleのclear / lockを壊さない。
- B7のrollback / docs closeoutを先行実装しない。
- app再起動後にhistoryを復元しない。
- fixed morph、VMD format、30fps、encodingを変更しない。
- dependency、package、license、network、Qtを変更しない。
- 新規test、関連回帰、full testのpass表示とprocess exit codeを記録する。
- `git diff --check` がprocess exit code 0である。
- ユーザーGUI確認結果を実施後に記録する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| current snapshotとhistory currentが分岐する | history stateを唯一のcurrent所有者にし、compatibility propertyで公開する |
| spin eventごとにhistoryが増える | explicit gesture tokenとboundaryでcoalesceする |
| tokenなしspinを長時間pendingにする | wheel / start未取得spinはdiscrete fallbackにする |
| 古いreleaseが新gestureを確定する | field / event / token完全一致時だけlocal boundaryを受理する |
| programmatic refreshでgestureが分割される | same base / event / fieldのactive tokenをrefresh後も保持する |
| selection / base変更後もlocal tokenが残る | global boundaryまたはworkspace破棄と同時にRightPane-local stateをclearする |
| timerによりtestと実動作が不定になる | mouse / key / focus / Enterの明示boundaryを使う |
| no-opでredoが消える | final canonical equalityを確認してからtransaction確定・redo破棄する |
| 51件目でcurrentまたはredoを失う | undo側の最古1 transactionだけを削除する |
| different base snapshotを復元する | history全域のbase identityをcoreで検証する |
| cleanupされたtail overrideが復元できない | full before / after snapshotをtransactionへ保存する |
| reset allが複数操作になる | empty snapshotへの単一discrete transactionにする |
| Undo後にPreviewだけ古い | `sync_ui_state()`を唯一のGUI再同期入口にする |
| history位置でfingerprintが変わる | history DTO / action stateをfingerprint payloadへ含めない |
| WARNING確認を毎回失う | confirmed fingerprintを保持し、output identity比較へ委ねる |
| cleanup operation noticeをsnapshotから誤再現する | Undo / Redoでは汎用operation noticeへ置換し、effect / crossfade noticeだけを再導出する |
| selectionまでUndoされる | history payloadからselectionを除外する |
| Busy shortcutが処理される | menu action stateとhandler guardを両方置く |
| editor dirty値をshortcutが暗黙破棄する | dirty時はhistory移動を停止しinlineで確定・修正を促す |
| transcriptionのnative Undoを奪う | selective `EVT_CHAR_HOOK` でselected editor外のeditable controlへkey eventを渡す |
| B6でfailure rollbackを半実装する | current clear / lockに限定し、B7へ明示引き継ぎする |
| recent file historyと名称が衝突する | `adjustment_history` の名前を一貫使用する |

## 14. Codex 実装時の注意

- 本計画作成だけではproduction code / testを変更しない。
- pre-implementation check後、ユーザーの実装開始指示を待つ。
- B1のbefore / after full snapshot契約をevent delta方式へ変更しない。
- B2 canonicalizationとresolver semanticsをhistory moduleへ複製しない。
- B4 typed requestのstale identity / revision guardを弱めない。
- B5 effective output fingerprintへhistory位置を追加しない。
- coalescingのためにthread、background timer、networkを追加しない。
- historyにwx object、callback、control、PreviewDataを保持しない。
- reset allでbase plan、selection、input、playbackをclearしない。
- workspace resetとreset all adjustmentsを混同しない。
- Undo / Redoでanalysis workerやVMD保存を自動実行しない。
- user-facing labelは一般ユーザー向け日本語とし、canonical / snapshotなどの内部語を
  menuやnoticeへ露出しない。
- fixed morph `あ / い / う / え / お` を変更しない。
- wxPython主系を維持し、Qt / PySide6を復活させない。
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
