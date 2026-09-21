# MS21-B4 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B4 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
- 対象Block: MS21-B4
- Block名: RightPane Event Editor / Live Preview
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `07c3717 Implement MS21-B3 preview event selection`
- 作成日: 2026-07-23
- 文書ステータス: Completed / Automated Verification Complete / User GUI Verification Complete
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
- 関連正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/MS16_GUI_Layout_Spec_for_Antigravity.md`

### 1.1 完了記録

- 2026-07-24にMS21-B4 production実装と、反映量制限を一般ユーザーへ説明する一時修正を完了した。
- B4限定16件、B2 resolver関連35件、B3 selection / Preview関連22件、RightPane / theme関連21件、diagnostics関連37件、pipeline / VMD関連12件はpass表示・各process exit code 0だった。
- 全体testは550件と7 subtestsがpass表示・process exit code 0、`compileall src tests` と `git diff --check` もprocess exit code 0だった。
- 同日にユーザーGUI再確認が完了し、問題なしと報告された。
- B4は実装、自動検証、ユーザーGUI確認まで完了した。次はMS21-B5 Implementation Plan策定である。

MS21-B4は、B3でcanonical event selectionへ接続したRightPaneの「選択イベント」タブを、発音イベント単位の補正editorへ拡張するBlockである。B2のimmutable adjustment snapshotとshared resolverを唯一の計算正本とし、補正確定後のPreviewを即時更新する。一方、adjusted VMD保存、diagnostics fingerprint、Undo / Redo、再解析rollbackの完成は後続Blockへ残す。

## 2. 背景

現行実装はB3完了時点で次の状態にある。

- `UiState` はcanonical selection indexとbase plan identity digestを保持する。
- Preview clickはreal base eventへhit-testされ、grouped shapeの任意memberを選択できる。
- `RightPane` の「選択イベント」タブは、選択event固有のindex、shape、time、peak、frameを1個の `wx.StaticText` へ表示する読み取り専用UIである。
- `MainFrame._update_preview_display()` はcurrent timing plan、observations、source duration、global hold / softness、empty adjustment snapshotからB2 full resolverを実行する。
- `EventAdjustment` はpeak absolute override、start / end frame offset、hold / softness absolute override、slope ratioをimmutableに保持する。
- `apply_adjustment_update()` はsnapshotを更新し、group再計算後にtailでなくなったeventのhold / softness / slopeを同一transactionで除去する。
- `EffectiveShapePlan` はeffective event、shape control point、group provenanceを持つが、RightPaneがbase / override / effectiveを直接表示するためのbase event列とresolved tail値は公開していない。
- `apply_adjustment_update()` はgroup末尾でなくなったeventのtail overrideを除去するが、requested softnessが正でも次shape clampによりactual midpointが消える場合のlatent slope overrideを除去しない。
- adjustment snapshotはまだ `UiState` に接続されていない。
- VMD保存、MS20 diagnostics、fingerprint、reportはadjustmentを参照しない。

B4でPreviewだけをadjustment対応にして既存VMD保存をそのまま許可すると、画面で確認したshapeと保存内容が一致しない。B5で保存統合が完了するまで、non-empty adjustment中のVMD保存はfail closedで一時禁止する必要がある。

## 3. 目的

- 選択eventのbase、adjustment、effective値をRightPaneで区別して表示する。
- peak、start、end、hold、softness、slopeをB1契約の単位と範囲で編集できるようにする。
- UI値を正本にせず、`AdjustmentLayerSnapshot` をworkspace内のcanonical編集状態とする。
- validな補正確定ごとにB2 shared resolverを一度実行し、Previewへ即時反映する。
- grouped shapeのtail可否とslope midpoint可否をcurrent effective resultから判定する。
- invalid、stale、Busy中の編集をfail closedで拒否し、snapshotとPreviewを変更しない。
- selected eventの補正を1操作でresetできるようにする。
- B5までadjusted Previewとunadjusted VMD保存が混在しないよう、一時保存guardを設ける。
- B6が履歴を追加できる単一commit境界を作るが、B4ではhistoryを実装しない。

## 4. In Scope

- RightPane「選択イベント」タブのstructured editor化
- base / adjustment / effectiveの3区分表示
- event index、母音、group member / tail状態表示
- `peak_value` absolute override入力
- `start_offset_frames` / `end_offset_frames` 入力
- `hold_frames` / `softness_frames` absolute override入力
- `slope_ratio` 入力
- field単位のoverride有無表示
- current group tailでないeventのtail control無効化
- actual resolved shapeに `slope_mid` がない場合のslope control無効化
- actual midpoint消失時のlatent slope override canonical removal
- actual midpoint消失時のslope cleanup resultとnon-modal notice
- non-modalなvalidation error / canonical cleanup通知
- selected event reset
- `UiState` へのcurrent canonical adjustment snapshot追加
- adjustment snapshot付きB2 resolverからのlive Preview更新
- selection、base identity、editor revisionを使うstale edit拒否
- Busy中のeditor lock
- 現行lifecycleに必要な最小clear / initialize
- non-empty adjustment中の一時diagnostic ERRORと、同一snapshotによるStatus / VMD button / menu / controller save guard
- B4専用pure adapter test、wx GUI test、関連回帰
- 実装結果とユーザー手動GUI確認項目の記録

## 5. Out of Scope

- adjusted resultのVMD writer接続
- save-state fingerprint schema更新
- WARNING確認済みfingerprintのadjustment連携
- diagnostics snapshot / reportへのadjustment値summary追加（B4の一時保存禁止diagnostic itemは除く）
- VMD保存可能状態でのadjustment維持
- Undo / Redo stack、50操作上限、coalescing
- reset all adjustments
- analysis failure時の旧編集rollback完成（current-job cancelで現行stateを保持するB4契約は対象内）
- input / parameter / late callbackを含むMS21 lifecycle全体監査
- session外へのadjustment永続化
- 複数event一括編集
- 母音変更、任意keyframe編集、dragによるshape直接編集
- preset、profile、long-vowel機能
- README、配布用readme、3正本仕様のMS21 implemented更新
- VMD形式、model name、Shift_JIS、固定モーフの変更
- dependency、package、release、version bump、tag、merge、push
- Qt / PySide6、network、cloud ASR、他ASR backend、外部送信、background通信、Whisper自動download

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- B3完了commit `07c3717` を実装baselineとする。
- 作業開始時に未コミット変更と未追跡fileを確認し、ユーザー所有変更を保護する。
- Python 3.11以上、Windows 11、wxPython主系、30fps、固定モーフ `あ / い / う / え / お` を維持する。
- base `VowelTimingPlan` とobservationsは変更しない。
- adjustment modelとshape resolverの正本は `src.core.event_adjustment` / `src.core.effective_shape_plan` とする。
- legacy `build_preview_data()` と既存VMD保存経路は互換入口として残す。
- B4開始前に本planを現行code / testへ再照合し、findingsをP1 / P2 / P3で分類する。

### 6.1 計画作成baseline

2026-07-23、HEAD `07c3717` で次を実行した。

- B2 adjustment / effective resolver: 29件pass表示、process exit code 0。
- B3 hit-test / selection / integration / wx: 22件pass表示、process exit code 0。
- RightPane / diagnostics Info / theme: 21件pass表示、process exit code 0。
- 合計72件、failure / error / fatal表示なし。
- 計画作成時点で作業ツリーはcleanであり、production code、test code、dependency、build設定は変更していない。

### 6.2 現行実装から判明したB4の補完点

- `EffectiveShapePlan` はeffective eventとshapeを持つが、editor用base event列を公開していない。
- `EffectiveShape` はtail control pointを持つが、global / override採用値と次shape clamp後のeffective hold / softnessを構造化して公開していない。
- `RightPane` はevent summary文字列だけを受け取り、typed edit callbackやeditor revisionを持たない。
- `UiState` はadjustment snapshotを持たず、MainFrameは毎回empty snapshotをresolverへ渡している。
- 現行VMD保存guardはMS20 diagnostics snapshotだけを参照し、Preview-only adjustmentを識別できない。

### 6.3 実装状態整合レビューとP2 / P3解消

2026-07-23の実装状態整合レビューではP1なし、P2 2件、P3 2件を検出し、本planへ次のように反映した。

- P2: non-empty adjustmentをbutton / menu / controllerで別判定すると、Info / reportのsaveabilityと矛盾する。B4の一時保存禁止をstructured diagnostic ERRORとして単一snapshotへ統合した。
- P2: analysis cancel時のadjustment保持が未定義だった。analysis開始ではstateを保持してlockし、current job cancelではbase / adjustment / selection / Previewを保持、failureだけは現行どおりclearすると固定した。
- P3: selected reset後の保存復帰条件を、snapshot全体がemptyになった場合だけに限定した。
- P3: wx controlのcommit event ownershipと同値no-opを固定し、Enter / focus / spin eventによるtyped request重複を禁止した。

再照合に使用した既存testは、B2 core 29件、B3 selection 22件、RightPane / diagnostics / save policy 28件、VMD export / save policy 19件、analysis lifecycle / late result / reset 15件がpass表示、各process exit code 0だった。`git diff --check` もprocess exit code 0だった。文書補正後はpre-implementation checkで残存findingを再判定する。

### 6.4 2026-07-24 pre-implementation checkとP2 / P3解消

commit `c098def` に対するpre-implementation checkではP1なし、P2 2件、P3 2件を検出し、本planへ次のように反映した。

- P2: 一時ERRORだけをcancel INFO抑止の例外にする記載が、B1契約、現行core、GUI正本仕様と競合していた。一時ERRORも通常のERRORとしてcancel INFOを抑止し、cancel時のbase / adjustment / selection / Preview保持と `StatusKey.ANALYSIS_CANCELLED` は維持すると固定した。
- P2: non-empty adjustment中もbottom Statusが「解析完了 (VMD出力可能)」を表示する欠落があった。Statusも同一diagnostics snapshotを受け取り、B5対応待ち表示へ切り替える対象に追加した。
- P3: `EVT_TEXT_ENTER` を発生させる `wx.TE_PROCESS_ENTER` styleをTextCtrl / SpinCtrl / SpinCtrlDoubleへ明記した。
- P3: actual midpoint消失時のslope自動除去をUIへ通知するresult契約がなかった。`removed_slope_override_event_indices` をtransaction resultへ追加し、tail cleanupとは分離してnoticeへ投影すると固定した。

既存回帰はB2 35件、B3 22件、RightPane / Info / theme 21件、diagnostics / report 37件、save / export / lifecycle / playback 41件、pipeline / VMD 12件の計168件がpass表示、各process exit code 0だった。RightPane回帰の初回起動だけはpytest開始前のPowerShell runtime参照失敗で終了コード `-2147450726` となり、同一commandの一度の再実行で21件pass・終了コード0を確認した。`git diff --check` は終了コード0だった。文書補正後に残存findingを再チェックする。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| `src/core/effective_shape_plan.py` | editorが再計算せず使えるbase event列とresolved tail metadataのadditive DTO公開、actual midpoint消失時のslope cleanup result |
| 新規候補 `src/gui_wx/selected_event_editor.py` | wx非依存のeditor view model、typed edit request、表示値・有効条件・merge helper |
| `src/gui_wx/right_pane.py` | 選択イベントtabのscrollable structured editor、callback、validation / notice表示、theme対応 |
| `src/gui_wx/ui_state.py` | canonical adjustment snapshot、identity付きcommit / clear、non-empty判定 |
| `src/core/output_diagnostics.py` | B5前のnon-empty adjustmentを表す一時diagnostic ERRORとsaveability統合 |
| `src/gui_wx/output_diagnostics_adapter.py` | canonical adjustment snapshotのempty / non-emptyをdiagnostics inputへ接続 |
| `src/gui_wx/main_frame.py` | editor state同期、edit commit、reset selected、adjusted live Preview、Busy lock、同一diagnostics snapshotによるStatus / action state |
| `src/gui_wx/app_controller.py` | 同一diagnostics snapshotによる既存controller save guardの維持 |

`src/core/preview_transform.py` は現行adapterで必要metadataを保持できる見込みのため、計画時点では関連確認対象とする。実装前再照合で不足が確認された場合だけ主変更へ昇格する。

### 7.2 新規test候補

- `tests/test_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_ms21_b4_live_preview.py`
- `tests/test_ms21_b4_vmd_save_guard.py`

test責務が重複する場合はfile数を減らしてよいが、pure契約、wx control、MainFrame統合、controller guardは分離して検証する。

### 7.3 回帰確認対象

- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_ms21_b3_preview_hit_test.py`
- `tests/test_ms21_b3_selection_commit.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_wx_ms21_b3_preview_selection.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_wx_ms15_b5_state_theme.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/test_wx_ms15_b3_playback.py`
- `tests/test_pipeline_and_vmd.py`

### 7.4 読み取り確認対象

- `src/core/pipeline.py`
- `src/core/event_adjustment.py`
- `src/core/preview_transform.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/parameter_panel.py`
- `src/vmd_writer/writer.py`
- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`

### 7.5 文書更新

- 実装前は本plan、Block Breakdown、Index、Roadmapだけを計画状態へ同期する。
- 実装後は本planへ実装file、test結果、findings、ユーザー確認対象を追記する。
- README、配布用readme、Pipeline / GUI / Error正本仕様のimplemented表示はB7まで先行更新しない。

## 8. 実装方針

### 8.1 canonical stateとderived state

- canonical編集状態は `UiState.current_adjustment_snapshot` のimmutable `AdjustmentLayerSnapshot` とする。
- RightPane control値、summary文字列、PreviewData、EffectiveShapePlan cacheを正本にしない。
- `EffectiveShapePlan` はbase input、global shape parameter、canonical snapshotから都度決定的に導出する。
- snapshot commitはexpected base identityを検証し、identity mismatchではcurrent stateを変更しない。

### 8.2 editor用core metadata

RightPaneがprivate helperやcontrol point形状を再解釈しないよう、B2 DTOへadditive metadataを追加する。

```text
EffectiveShapePlan
  - base_events: tuple[BaseShapeEvent, ...]
  - effective_events
  - shapes
  - canonical_adjustment_snapshot

EffectiveShape
  - real_base_event_indices
  - resolved_tail: ResolvedTailParameters

ResolvedTailParameters
  - tail_base_event_index
  - requested_hold_frames
  - requested_softness_frames
  - effective_hold_frames
  - effective_softness_frames
  - slope_ratio
  - has_slope_midpoint

AdjustmentUpdateResult
  - removed_tail_override_event_indices
  - removed_slope_override_event_indices
```

- requested値はglobalまたはoverrideを解決した値とする。
- effective hold / softnessは次shape開始によるclamp後の実値とする。
- `has_slope_midpoint` は実際のcontrol pointに `slope_mid` が生成された時だけtrueとする。
- `removed_tail_override_event_indices` はgroup末尾でなくなりtail field一式を除去したevent、`removed_slope_override_event_indices` はgroup末尾のままactual midpointだけが消えてslopeを除去したeventとし、同じindexを両方へ入れない。
- writer / Preview output意味、既存control point、grouping、normalizationを変更しない。

### 8.3 wx非依存editor adapter

新規候補 `selected_event_editor.py` はwx objectをimportせず、次を提供する。

```text
SelectedEventEditorState
  - base_event_index / vowel / base_identity_digest
  - base start / peak / end / peak value
  - current adjustment values and override flags
  - effective start / peak / end / peak value
  - requested / effective tail values
  - is_group_tail
  - slope_enabled
  - reset_enabled

SelectedEventEditRequest
  - base_event_index
  - base_identity_digest
  - editor_revision
  - field
  - typed value
```

- adapterはselected indexからbase event、effective event、group、snapshot entryを一意に対応付ける。
- unknown / duplicate / stale index、identity mismatch、metadata不整合はfail closedで例外にする。
- field mergeは既存event adjustmentの他fieldを保持し、変更fieldだけを置換する。
- UI向け日本語error文言はcore exceptionへ入れず、adapterまたはRightPane境界で変換する。

### 8.4 RightPane editor layout

「選択イベント」tabは `wx.ScrolledWindow` とし、狭い右paneでも縦scrollで全fieldへ到達できるようにする。

表示順:

1. event index、母音、group member数、group tail可否
2. base / adjustment / effectiveの列見出し
3. 開口量
4. 開始offset / effective start frame
5. 終了offset / effective end frame
6. 開口保持
7. 閉口スムーズ
8. 閉口傾斜比
9. validation / cleanup notice
10. `選択イベントの補正をリセット` button

control方針:

- peakは上限を捏造しないため、finiteな0以上を受理する `wx.TextCtrl(style=wx.TE_PROCESS_ENTER)` とする。valid入力だけをcommitする。
- start / end offsetは `wx.SpinCtrl` とし、`wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER` style、selected base eventとsource durationからlegal rangeを設定する。
- hold / softnessは `wx.SpinCtrl`、`wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER` style、0から100、単位はframeとする。
- slopeは `wx.SpinCtrlDouble`、`wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER` style、0.0から1.0、increment 0.05、表示2桁を初期値とする。
- controlは現在のrequested値を表示し、隣接labelで「補正なし」または「補正あり」を明示する。
- baseとeffectiveはread-only labelとし、user入力値と混同しない。
- 明示的な「適用」buttonは置かない。spin操作、Enter、focus確定でvalid値をcommitし、Previewへ反映する。
- partial / invalid textはsnapshotへcommitせず、inline errorを表示する。modal dialogを連打しない。
- `EVT_TEXT` はparse / inline validationだけに使用し、snapshot commitを発火しない。
- spin操作は `EVT_SPINCTRL` / `EVT_SPINCTRLDOUBLE`、typed入力は `EVT_TEXT_ENTER` または `EVT_KILL_FOCUS` をcommit入口とする。
- Enter確定直後のfocus移動など複数wx eventが連続しても、current requested値と同値ならcallback前にno-op化し、1回のユーザー確定操作からtyped requestを重複送信しない。

### 8.5 grouped tailとslope

- peak / start / endは全real base eventで編集可能とする。
- hold / softness / slopeはcurrent resolved groupの末尾eventだけで編集可能とする。
- tailでないeventでは3controlをdisableし、「group末尾イベントでのみ編集できます」と表示する。
- slopeはtailかつ `resolved_tail.has_slope_midpoint=True` の時だけenableする。
- softness変更または次shape clampによりmidpointが消えた場合、B4で補修するupdate transactionがslope overrideをcanonical removalし、indexを `removed_slope_override_event_indices` へ記録する。UIはdisabled / default 0.70へ戻し、non-modal noticeを表示する。
- direct resolverへactual midpointを持てないslope overrideが渡された場合は `AdjustmentContractError` とし、silentなlatent overrideを許可しない。
- start / end変更でgroup構成が変わり、別eventのtail overrideが除去された場合、`removed_tail_override_event_indices` をnon-modal noticeへ表示する。

### 8.6 atomic live Preview update

valid editのcommit順序:

```text
typed edit request
  -> selection / base identity / editor revision / Busy validation
  -> merge current EventAdjustment
  -> apply_adjustment_update(base, current snapshot, requested change)
  -> resultを最後まで検証
  -> UiState snapshotをatomic replace
  -> same EffectiveShapePlanからPreviewDataを生成
  -> selectionを保持してPreviewをreplace
  -> editor stateをresultから再構築
```

- `apply_adjustment_update()` またはadapterが失敗した場合、snapshot、Preview、selectionを変更しない。
- commit成功時だけPreview render revisionを更新する。
- base identityはadjustmentで変えない。B3 canonical selection identityを維持する。
- selectionはhistory対象外であり、B4 editでもclearしない。
- Preview更新後もRightPaneのselected eventとhighlightが同じindexを示す。

### 8.7 selected reset

- reset buttonはselected indexのempty `EventAdjustment` を同じupdate経路へ渡す。
- selected eventの全overrideを同時に除去する。
- snapshotが変わらないresetはno-opとし、不必要なrender revision更新を行わない。
- resetによる再groupingで他eventのstale tail overrideが除去された場合もnoticeへ表示する。
- reset allはB6まで追加しない。

### 8.8 minimal lifecycleとBusy

- analysis resultがvalidでsnapshot未作成なら、current base identityのempty snapshotを初期化する。
- analysis開始時はcurrent base、snapshot、selectionを保持したままeditorだけをlockする。rollback用の別copyはB4で追加しない。
- current job successでは新しいbase identityのempty snapshotへ置換し、selectionをclearする。
- current job cancelでは、開始時から保持しているcurrent base、snapshot、selectionをそのまま維持し、diagnostics snapshotを再構築する。snapshotがemptyで他ERRORがなければ `analysis_cancelled` INFOを含める。snapshotがnon-emptyなら一時ERRORを優先してcancel INFOを抑止するが、`StatusKey.ANALYSIS_CANCELLED` とbottom Statusの「解析をキャンセルしました」は維持する。
- current job failureでは現行 `invalidate_analysis()` に従ってbase、snapshot、selectionをclearする。旧baseの条件付き復元はB7で実装する。
- `invalidate_analysis()` とworkspace resetではsnapshotをclearする。
- analysis failure時の旧base / adjustment条件付きrollback完成はB7の責務であり、B4は現行failure clear semanticsを越えて先行実装しない。
- analysis中は既存表示を維持してもeditor controlとresetをdisableする。
- Busy中に届いたedit requestはno-opとし、snapshot / Preview / noticeを変更しない。
- late / duplicate analysis callbackは既存job guardより前にadjustmentを変更しない。

### 8.9 B5までのVMD保存guard

- `DiagnosticSnapshotInput` へdefault `False` の `adjustment_vmd_integration_pending` をadditiveに追加し、canonical adjustment snapshotがnon-emptyの時だけtrueを渡す。
- trueの場合、`build_output_diagnostics_snapshot()` はcode `adjustment_vmd_integration_pending`、severity `ERROR`、phase `vmd_write`、identity context `adjustment_present=True` の一時diagnostic itemを生成する。
- `_CODE_ORDER` と `_SUMMARY` に同codeを登録し、表示順と日本語summaryを決定的にする。
- この一時ERRORも既存ERROR規則へ従い、current job cancel時の `analysis_cancelled` INFOを抑止する。B4専用のseverity / cancel allowlist例外を追加しない。
- 一時ERRORを含む単一の `OutputDiagnosticsSnapshot.saveability` を、Info、Warning、diagnostic report、bottom Status、VMD保存button / menu、controllerの全てで共有する。各consumerでadjustment有無や保存可否を再計算しない。
- snapshotがnon-emptyの間、共有saveabilityによりVMD保存buttonとmenuをdisableし、controller直接呼び出しでもdialog、Warning確認、writerへ進まない。
- `sync_ui_state()` が生成した同じsnapshotを `update_status_display()` または同等のStatus formatterへ渡す。`StatusKey.ANALYSIS_READY` かつblocking codeが一時ERRORだけの場合は、bottom Statusを「解析完了（個別補正あり・VMD保存はB5対応待ち）」とし、「VMD出力可能」を残さない。Status側でadjustment snapshotを直接参照しない。
- editor noticeにも「個別補正はPreviewへ反映済みです。VMD保存連携はMS21-B5で対応します」と表示する。
- B4はadjustmentのfield値、effective writer payload、adjustment summaryをfingerprint / report schemaへ追加しない。ただし一時ERROR itemは既存diagnostics item / saveability / fingerprint / report projectionへ通常どおり反映し、表示と保存判定を矛盾させない。
- selected reset後も他eventのadjustmentが残る場合は一時ERRORと保存禁止を維持する。snapshot全体がemptyになった場合だけ現行diagnostics saveabilityへ戻る。
- B5はこのtemporary input / diagnostic itemを除去し、adjusted writer payload / fingerprint / report統合へ置き換える。

### 8.10 compatibilityと文書境界

- existing RightPane Info / Warning / playback tabのAPIと表示を変更しない。
- `set_selected_event_summary()` はMS16 / B3互換test用に残してよいが、canonical B4 pathはtyped editor stateを使用する。
- B3 permissive selection setterの互換性を維持し、canonical editorはidentity付きselectionだけを編集可能とする。
- theme変更時はeditor label、control、error / notice色をcurrent paletteへ追従させる。
- dependency、build、package、licenseに変更を加えない。

## 9. 詳細ステップ

### Step 1: repositoryと契約の再確認

- Git状態、branch、HEAD、untrackedを一つずつ確認する。
- B1 field契約、B2 update API、B3 selection / revision契約を再読する。
- RightPane、MainFrame、UiState、AppControllerの実callerとtestを確認する。
- P1 / P2 / P3を分類し、P1 / P2があればproduction変更前にplanを補正する。

### Step 2: core metadataをadditiveに公開

- `EffectiveShapePlan.base_events` を追加する。
- resolved tail DTOを追加し、各shapeへ付与する。
- requested値とclamp後effective値をshape生成時に一度だけ確定する。
- actual midpointが消えたslope overrideをupdate transactionで除去し、`removed_slope_override_event_indices` へ記録する。direct resolverでは拒否する。
- existing plan / shape equalityとadapter outputが意味変更しないことをtestする。

### Step 3: pure editor state builder

- selected eventのbase / override / effective / group情報を構築する。
- field有効条件とlegal offset rangeをprimitive値で返す。
- invalid selection、stale identity、missing metadataをrejectする。
- request mergeが他fieldを失わないことを固定する。

### Step 4: UiState snapshot contract

- current snapshot fieldとidentity付きset / clear helperを追加する。
- non-empty propertyを追加する。
- mutable dict / control objectをstateへ格納しない。
- invalidate / reset / analysis successの最小clear規則を追加する。

### Step 5: RightPane editor UI

- selected event panelをscrollable構成へ変更する。
- structured labels、controls、override marker、notice、reset buttonを追加する。
- Enter commit対象controlは生成時に `wx.TE_PROCESS_ENTER` を指定する。
- typed callback bindingとcallback抑制flagを実装し、programmatic control更新がedit eventを再送しないようにする。
- `EVT_TEXT` はvalidation専用、spin event / Enter / focus lossはcommit専用とし、current requested値との同値比較をcallback前に行う。
- editor revisionを更新し、old focus / text eventをstale requestとして拒否できるようにする。

### Step 6: MainFrame editor sync

- current base input、snapshot、effective plan、selectionからeditor stateを構築する。
- no selection / legacy-only selection / invalid identityではeditorをempty disabled表示にする。
- B3 click selection後にeditorを同じeventへ同期する。
- selection変更時のold edit eventをrejectする。

### Step 7: edit commitとlive Preview

- valid requestをcurrent snapshotへmergeし、B2 update APIを呼ぶ。
- success resultをatomic commitし、同じplanをPreviewとeditorへ渡す。
- no-opではPreviewを再生成しない。
- error時はlast valid controlsへ戻し、inline errorを表示する。
- removed tail overrideとremoved slope overrideを別理由のnoticeとして表示する。

### Step 8: reset selected

- selected eventのempty adjustmentをcommitする。
- all fields、override marker、Previewをbase / global値へ戻す。
- no selection、Busy、stale identity、already emptyでは無効またはno-opにする。

### Step 9: temporary VMD save guard

- diagnostics inputへnon-empty snapshotを接続し、一時ERRORを単一snapshotへ生成する。
- Info、Warning、report、bottom Status、button / menu、controllerが同じsnapshot / saveabilityを使うことを固定する。
- 一時ERROR時のbottom Statusから「VMD出力可能」を除き、B5対応待ちを表示する。
- save dialog、Warning確認、writer callへ到達しないことをtestする。
- reset selected後も別eventのadjustmentが残れば保存禁止を維持し、snapshot全体がemptyになった時だけ現行saveabilityへ戻す。

### Step 10: theme、resize、lifecycle

- light / dark / system themeでeditorを再styleする。
- right pane幅変更時にlabel wrapとscroll rangeを再計算する。
- Busy、analysis success / failure / cancel、input invalidation、workspace resetのB4範囲を確認する。
- playback、pan、zoom、tab切替ではsnapshotを変更しない。

### Step 11: testと回帰

- pure metadata / adapter testを最初に実行する。
- wx editor、MainFrame live Preview、save guardを分けて実行する。
- B2、B3、RightPane、theme、save policy、state回帰を実行する。
- 全体test、compileall、diff checkへ拡張する。

### Step 12: documentation closeout

- 本planへ実装file、test結果、P1 / P2 / P3、ユーザー確認結果を追記する。
- Block Breakdown、Index、Roadmapを実際の到達状態へ同期する。
- B5へtemporary save guard、snapshot、effective plan、fingerprint未接続を引き継ぐ。

## 10. 状態遷移 / データ契約

### 10.1 canonical editor flow

```text
UiState.current_timing_plan
  + selected WAV duration
  + global ShapeParameters
    -> BaseTimingPlanInput
    -> BasePlanIdentity

UiState.current_adjustment_snapshot
    -> resolve / apply_adjustment_update
    -> EffectiveShapePlan
         -> PreviewData
         -> SelectedEventEditorState
```

- base plan identityとsnapshot identityは一致必須とする。
- editor stateとPreviewは同じeffective plan instanceまたは同一transaction resultから生成する。
- RightPaneからbase timeline、group、tailを再計算しない。

### 10.2 field表示契約

| field | Base表示 | Adjustment control | Effective表示 |
| --- | --- | --- | --- |
| 開口量 | base peak value | absolute peak value | effective peak value |
| 開始 | base start frame | signed frame offset | effective start frame |
| 終了 | base end frame | signed frame offset | effective end frame |
| 開口保持 | global hold | absolute override | clamp後hold |
| 閉口スムーズ | global softness | absolute override | clamp後softness |
| 閉口傾斜比 | default 0.70 | absolute ratio | midpoint時のratio、なければ `—` |

- canonical no-opはsnapshotから除去されるため、override markerはcanonical snapshotのfield有無から決める。
- requested値とeffective値が次shape clampで異なる場合、両方を別列で表示する。
- peak描画clampとwriter値を混同しない。

### 10.3 request validation

request commit条件:

- `not is_busy`
- analysis result valid
- current base inputを構築可能
- current selectionがcanonical identity付き
- request event indexがcurrent selectionと一致
- request base digestがcurrent digestと一致
- request editor revisionがcurrent revisionと一致
- field名がallowlist内
- typed値がB1 / B2範囲内

1つでも満たさない場合はsnapshot、Preview、selectionを変更しない。

### 10.4 lifecycle matrix

| event | adjustment snapshot | editor | Preview | 備考 |
| --- | --- | --- | --- | --- |
| analysis success | new baseのempty snapshot | no selection | base-only | B4では旧編集を引き継がない |
| canonical event selection | 保持 | selected state表示 | selection highlight | adjustmentは変更しない |
| valid edit | atomic replace | result再表示 | 即時更新 | same base identity |
| invalid edit | 保持 | error + last valid値 | 保持 | fail closed |
| reset selected | selected entry除去 | base / globalへ戻る | 即時更新 | reset allではない |
| Busy start | 保持 | lock | 表示保持 | edit request拒否 |
| current job cancel | 保持 | 同じselectionを再表示 | adjusted表示を保持 | empty snapshotではcancel INFO。non-emptyでは一時ERROR優先・cancel INFO抑止。cancel Statusは維持 |
| current job failure | clear | empty | placeholder | 現行invalidate契約。条件付きrollbackはB7 |
| input / global parameter invalidation | clear | empty | placeholder | 現行契約を維持 |
| workspace reset | clear | empty | placeholder | session外保存なし |
| playback / pan / zoom / theme | 保持 | 保持 |表示だけ更新 | identity不変 |

failure時の旧base / adjustment条件付きrollbackはB7でこのmatrixを拡張する。B4のcancelは開始時stateをclearしないことで保持し、復元用copyは作らない。

## 11. テスト方針

### 11.1 pure core / adapter test

- planがbase event列を公開し、base inputを変更しない。
- resolved tailのrequested / effective値とnext-shape clampが一致する。
- actual midpoint有無がcontrol pointと一致する。
- apply updateでactual midpointが消えたslope overrideを同一transactionから除去する。
- actual midpoint cleanupはevent indexを `removed_slope_override_event_indices` へ記録し、tail cleanup listと重複しない。
- direct resolverはactual midpointを持てないslope overrideを拒否する。
- editor stateがbase / override / effectiveを正しく区別する。
- grouped middle / tail判定が全memberで正しい。
- current adjustment mergeが他fieldを保持する。
- invalid index、stale identity、不正metadataを拒否する。
- no-op fieldがcanonical snapshotから除去される。

### 11.2 RightPane wx test

- 未選択時はempty message、全control disabled、reset disabledとなる。
- 選択時にevent / vowel / base / effectiveが表示される。
- group中間eventではtail controlがdisabledとなる。
- tail eventでhold / softnessがenabledとなる。
- midpointなしではslope disabled、midpointありではenabledとなる。
- programmatic refreshがedit callbackを発生させない。
- valid control eventがtyped requestを1件だけ送る。
- peak / offset / hold / softness / slope controlが `wx.TE_PROCESS_ENTER` を持ち、Enterでcommit eventを送る。
- `EVT_TEXT` はvalidationだけを行い、Enter確定後のfocus lossやspin由来の重複eventが2件目のrequestを送らない。
- invalid peak textはrequestを送らずinline errorを表示する。
- theme変更、resize、scrollでcontrolが判読・到達可能である。

### 11.3 MainFrame live Preview test

- edit前はempty adjustment snapshotである。
- peak / start / endの各editでsnapshotとPreview shapeが同じtransaction resultへ更新される。
- hold / softness / slopeがtail shapeへ反映される。
- selected grouped memberとRightPane stateが一致する。
- edit後もselection indexとbase identityを保持する。
- Preview render revisionを更新し、old requestを拒否する。
- invalid / stale / Busy requestでstateが完全に不変である。
- group変更時のtail override removalとnoticeを検証する。
- reset selectedでentryとPreviewがbaseへ戻る。
- no-op edit / resetで不必要なrender revisionを増やさない。

### 11.4 VMD save guard test

- non-empty snapshotでbutton / menuがdisabledになる。
- controller直接呼び出しでもsave dialog、Warning確認、writerへ進まない。
- Info / Warning / report / bottom Status / action state / controllerが同じsnapshotを参照し、`adjustment_vmd_integration_pending` ERRORとVMD保存不可を一致して表示する。
- `StatusKey.ANALYSIS_READY` かつ一時ERROR時はbottom StatusがB5対応待ちを示し、「VMD出力可能」を含まない。
- non-empty adjustmentを保持したanalysis cancelでは一時ERRORを含め、`analysis_cancelled` INFOを抑止する。base / snapshot / selection / adjusted Previewとcancel Statusは保持する。
- selected reset後も他eventのadjustmentが残れば保存不可を維持し、snapshot全体がemptyならMS20 diagnostics saveabilityへ戻る。
- B4中にadjusted writer callやadjustment値summaryをfingerprint / report schemaへ追加しない。一時diagnostic itemの既存projectionは検証対象とする。

### 11.5 lifecycle test

- analysis開始ではsnapshot / selectionを保持し、editorだけをlockする。
- current job cancelではsnapshot / selection / adjusted Previewを保持する。empty snapshotではcancel INFOを再構築し、non-empty snapshotでは一時ERRORによりcancel INFOを抑止する。どちらもcancel Statusを維持する。
- current job successではnew baseのempty snapshotへ置換してselectionをclearする。
- current job failure、input invalidation、workspace resetではsnapshotをclearする。
- late / duplicate callbackはsnapshotを変更しない。

### 11.6 実行順

最小順に一つずつ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b4_selected_event_editor.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b4_selected_event_editor.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b4_live_preview.py tests/test_ms21_b4_vmd_save_guard.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_event_adjustment.py tests/test_ms21_b2_effective_shape_plan.py tests/test_ms21_b2_shape_adapters.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b3_preview_hit_test.py tests/test_ms21_b3_selection_commit.py tests/test_ms21_b3_pipeline_preview_integration.py tests/test_wx_ms21_b3_preview_selection.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b3_right_pane.py tests/test_ms20_b3_right_pane_info.py tests/test_wx_ms15_b5_state_theme.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b3_output_diagnostics_adapter.py tests/test_ms20_b6_diagnostic_report.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_wx_ms14_b5_export.py tests/test_ms19_b8_workspace_reset.py tests/test_ms17_b8_late_worker_result_discard.py tests/test_wx_ms15_b3_playback.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

pass表示、failure / error / fatal、process exit codeを分離して記録する。既知問題を理由に新しいfailureを成功扱いしない。

### 11.7 手動GUI確認候補

- Previewでeventを選択するとstructured editorが同じeventを表示する。
- peak、開始、終了の補正がcontrol確定直後にPreviewへ反映される。
- group末尾eventだけでhold / softness / slopeを編集できる。
- softnessがmidpointを作らない場合はslopeが無効になる。
- grouped shapeの構成変更後も選択、highlight、editorが一致する。
- invalid入力でPreviewが壊れず、inline errorから修正できる。
- controlへの直接入力をEnterで確定でき、直後のfocus移動で同じeditが重複commitされない。
- reset selectedで選択eventだけがbaseへ戻る。
- non-empty adjustment中はInfo / Warning / bottom Statusと保存操作が同じ理由でVMD保存不可を示し、bottom Statusに「VMD出力可能」が残らない。
- selected reset後に別eventの補正が残る間は保存不可を維持し、全snapshotがemptyになった時だけ元のsaveabilityへ戻る。
- 解析cancel後は補正、selection、adjusted Preview、cancel Statusが保持される。補正がnon-emptyの場合、Warningには一時ERRORを表示しcancel INFOは表示しない。
- Busy中はeditorがlockされる。
- pan / zoom / Play / Stopで補正とselectionが保持される。
- dark / light theme、右pane縦scrollで全controlが判読・操作可能である。

実MMD確認はB5のadjusted VMD保存接続後に行う。build / SmokeLaunchはdependency / package変更がない限りB4の必須条件にしない。

## 12. 受け入れ条件

- RightPaneで選択eventのbase / adjustment / effective値を区別できる。
- canonical adjustment snapshotがUiStateに保持され、control値を正本にしない。
- peak、start、end、hold、softness、slopeがB1範囲で編集できる。
- peakに存在しない上限を追加せず、non-finite / 負値を拒否する。
- grouped middle eventではtail fieldを編集できない。
- actual slope midpointがない場合にslopeを編集できず、latent overrideが残らない。
- actual midpoint消失によるslope自動除去が専用result fieldに記録され、non-modal noticeへ表示される。
- valid edit後のPreviewがB2 shared resolver resultを即時表示する。
- Previewとeditorが同じeffective planから生成される。
- invalid、stale、Busy editでsnapshot / Preview / selectionが変わらない。
- group変更によるstale tail override除去がユーザーへ通知される。
- selected resetで全fieldがbase / global値へ戻る。
- edit後もcanonical selectionとhighlightが維持される。
- B5前にnon-empty adjustmentを無視したVMD保存が実行されない。
- 一時diagnostic ERRORを含む同一snapshotからInfo / Warning / report / bottom Status / button / menu / controllerの保存不可が導出される。
- 一時ERROR時のbottom StatusがB5対応待ちを示し、「VMD出力可能」を表示しない。
- selected reset後にsnapshot全体がemptyになった場合だけ既存MS20 saveabilityへ復帰し、他eventの補正が残る場合は保存禁止を維持する。
- analysis cancel後は開始前のbase、adjustment、selection、adjusted Previewとcancel Statusを保持する。non-empty adjustmentの一時ERRORがある場合は現行ERROR規則に従ってcancel INFOを抑止する。
- 1回のuser commitから同一fieldのtyped requestを重複送信しない。
- Enter commit対象controlが `wx.TE_PROCESS_ENTER` を持つ。
- VMD writer、adjustment値のfingerprint / diagnostic report schema、Undo / Redoを先行実装しない。
- RightPane Info / Warning / playback、theme、viewport、workspace resetに回帰がない。
- fixed morph、Qt禁止、network禁止、dependency / package不変を維持する。
- 指定testの表示結果とprocess exit codeを記録する。
- 実装後のP1 / P2が残らず、B5 Implementation Plan策定可否を明示する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| RightPaneがbase / groupingを再計算してresolverとずれる | base eventとresolved tail metadataをcore resultからadditiveに公開する |
| control値がcanonical stateになる | immutable snapshotだけをUiState正本とし、UIは毎回derived stateから再表示する |
| live edit途中のinvalid textでstateが壊れる | valid typed requestだけをcommitし、invalid / partial textはinline errorで保持する |
| programmatic refreshやEnter後focus lossが重複edit eventを発生させる | callback suppressionに加え、`EVT_TEXT` をvalidation専用とし、current requested値との同値比較をcallback前に行う |
| old focus eventが別selectionを編集する | event index、base digest、editor revisionをcommit時に再照合する |
| grouped middleへtail overrideを保存する | current effective group tailだけをenableし、core updateでもfail closed / cleanupする |
| next shape clampをUIが見落とす | requested値とeffective tail値を別表示する |
| slope controlが見かけ上有効でもmidpointがない | actual resolved `has_slope_midpoint` を有効条件にする |
| clamp後に作用しないslope overrideがsnapshotへ残る | update transactionでcanonical removalし、`removed_slope_override_event_indices` へ記録して通知する。direct resolverではfail closedにする |
| editごとにselectionがclearされる | base identityを維持し、same-base Preview replacementでselectionを保持する |
| Previewだけ補正されVMDがbaseのまま保存される | B5完了までnon-empty snapshotを一時diagnostic ERRORへ変換し、全consumerが同じsaveabilityでfail closedにする |
| 一時ERRORがあるcancelでINFOも表示し、既存severity規則と競合する | 一時ERRORも通常のERRORとして `analysis_cancelled` INFOを抑止し、cancel Statusと開始前stateの保持は別契約として維持する |
| 保存禁止中もbottom Statusが「VMD出力可能」と表示する | diagnostics snapshotをStatus formatterにも渡し、一時ERRORだけがblockerならB5対応待ち表示へ切り替える |
| `EVT_TEXT_ENTER` をbindしてもEnter commitが発火しない | 対象TextCtrl / SpinCtrl / SpinCtrlDoubleへ `wx.TE_PROCESS_ENTER` を明示する |
| B4でhistory設計を先行実装する | single commit境界だけ作り、stack / coalescingはB6へ残す |
| cancel時に開始前adjustmentを失う | analysis開始でstateをclearせず、current job cancelでは保持したbase / snapshot / selectionをそのまま再表示する |
| B4でrollback全体へscopeが拡大する | failureは現行clearを維持し、旧baseの条件付きrollbackだけをB7へ残す |
| 狭い右paneでfieldが見えない | ScrolledWindow、縦配置、wrap / FitInside回帰を使う |

## 14. Codex 実装時の注意

```text
- 最初にGit状態、MS21 routing、B1からB3のplan、B4 planを確認する。
- production変更前にplanと現行code / testの齟齬をP1 / P2 / P3で分類する。
- shell commandは一つずつ実行し、parallel、pipeline、chained commandを使用しない。
- user-owned差分をrestore、上書き、無断stageしない。
- base VowelTimingPlan / observationsを変更しない。
- B2 shared resolver以外にcandidate / grouping / tail計算を複製しない。
- RightPane文字列、control値、PreviewDataをadjustment正本にしない。
- base_event_indexとnegative synthetic tokenを混同しない。
- peak adjustmentをmorph_upper_limitでclampしない。
- hold / softnessは0から100、slopeは0.0から1.0をmodel側でもrejectする。
- actual midpointなしのslope overrideを保持しない。
- tail cleanupとslope cleanupを別result fieldで返し、同じevent indexを重複記録しない。
- no-op editでsnapshotやrender revisionを不必要に変更しない。
- non-empty adjustmentを一時diagnostic ERRORへ接続し、diagnosticsとは別の保存可否truthを作らない。
- 一時ERRORは既存ERROR規則どおりcancel INFOを抑止し、cancel Statusとstate保持を失わない。
- bottom Statusを同じdiagnostics snapshotから導出し、保存禁止中に「VMD出力可能」を表示しない。
- Enter commit対象controlへ `wx.TE_PROCESS_ENTER` を指定する。
- B5のwriter / adjustment値fingerprint / report summary、B6のhistory、B7のfailure rollbackを先行実装しない。
- existing RightPane Info / Warning / playback、B3 selection、viewport、themeを維持する。
- fixed morph、wxPython主系、local-only / no-network、Qt禁止を維持する。
- 実行していないtest、build、手動GUI確認を通過と報告しない。
```

実装完了報告は次を含める。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. ユーザーGUI確認
7. P1 / P2 / P3
8. 仕様から逸脱した点
9. 残課題
10. B5 Implementation Plan策定可否
```
