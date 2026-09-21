# MS21-B3 Implementation Plan

## 1. 文書情報

- 文書名: `MS21-B3 Implementation Plan`
- 配置: `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
- 対象Block: MS21-B3
- Block名: Preview Hit-Test / Event Selection
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `98dab6d Implement MS21-B2 adjustment core`
- 作成日: 2026-07-22
- 文書ステータス: Completed / Automated Verification Passed / User GUI Verification Passed
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
- 関連正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS21-B3は、B2で追加したreal base provenanceを使い、wxPython Previewのクリックをcanonical base event選択へ接続するBlockである。B3はhit-testと選択状態だけを実装し、event補正control、adjustment snapshot、VMD保存への補正反映、Undo / Redoは有効化しない。

## 2. 背景

現行実装には次の下地がある。

- `UiState.selected_source_event_index` と、値をそのまま保持する既存render-only setterがある。
- `PreviewModel`、選択highlight、RightPaneの読み取り専用「選択イベント」summaryがある。
- `MainFrame.select_event_by_source_index()` は手動・test用の選択伝搬を行うが、Preview mouse eventから呼ばれていない。
- Previewのleft dragは移動量が1 pixelでも直ちにpanし、left upは選択を確定しない。
- `PreviewSegment.source_event_index` はlegacy fieldであり、grouped shapeの先頭eventしか表現しない。
- B2の `PreviewSegment.source_event_indices` と `event_ranges` はfull provenanceを保持できる。
- B2の `EffectiveShapePlan.effective_events` はreal base eventごとの `base_event_index`、vowel、start / peak / end frameを保持する。
- `MainFrame._update_preview_display()` はまだlegacy `build_preview_data()` を使用し、B2 full resolver / provenance adapterをGUIへ接続していない。

B1で固定済みの選択規則は次のとおりである。

1. cursorが属するvowel laneだけを対象にする。
2. event別frame range内のreal base eventを候補にする。
3. 複数候補ではcursor frameとbase peak frameの距離が短いeventを優先する。
4. 同距離では小さい `base_event_index` を優先する。
5. event range外、空lane、viewport外ではselectionを変更しない。
6. negative synthetic shape tokenは選択候補にしない。
7. 既存setterのpermissive契約は維持し、canonical selection commitだけがinvalid / stale値を拒否する。

## 3. 目的

- Preview座標をviewport time / vowel laneへ決定的に変換する。
- B2 provenanceからreal base eventのhit regionを構築する。
- grouped / overlap / boundary / synthetic置換を含むhit-test優先順位を固定する。
- clickとpan dragをDPI対応thresholdで分離する。
- canonical selection commitでinvalid、stale、synthetic indexを拒否する。
- UiState、Preview highlight、RightPane summaryを同じ選択へ同期する。
- theme、viewport、playback、legacy selection helperの既存挙動を維持する。

## 4. In Scope

- UI非依存hit-test DTO / pure function
- viewport x座標から30fps cursor frameへの変換
- y座標から固定5母音laneへの変換
- B2 `EffectiveShapePlan` 由来のevent hit region
- grouped shape内の複数real event選択
- overlap時のbase peak距離・base index優先
- 4 DIPのclick / drag threshold
- mouse capture lost / leaveを含むgesture取消
- PreviewPanelからPlaceholderContainer、MainFrameへのselection callback
- canonical selection commitとbase identity照合
- Busy中のselection commit抑止
- multi-source selection highlightとevent固有summary
- analysis結果更新、input / parameter invalidation、placeholder、workspace reset時のselection破棄
- theme、viewport、playbackだけの再描画時のselection保持
- B3専用testと既存selection / Preview / viewport / playback回帰
- B3実装後の計画・routing文書更新

## 5. Out of Scope

- RightPaneのevent補正control
- peak / start / end / hold / softness / slope編集
- adjustment snapshotのUiState接続
- adjustment付きlive Preview
- VMD保存へのeffective plan接続
- fingerprint、Warning確認、diagnostic reportのadjustment対応
- Undo / Redo、coalescing、reset selected / all
- VMD writer出力変更
- analysis pipeline変更
- 空laneクリックによるselection解除
- keyboard selection、複数選択、範囲選択
- arbitrary morph、固定モーフ `あ / い / う / え / お` の変更
- dependency、package、release、version、tag、merge、push
- Qt / PySide6、network、cloud、外部ASR、background通信、自動download

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- MS20 Closeout Aを未完了へ戻さない。
- B1のcanonical `base_event_index` とhit-test優先規則を変更しない。
- B2の `BasePlanIdentity`、`EffectiveShapePlan`、`source_event_indices`、`event_ranges` を正本として再利用する。
- `PreviewSegment.source_event_index` はlegacy表示互換fieldであり、canonical keyには使わない。
- canonical selectionはreal base eventだけを対象とする。
- 現行のpermissive `UiState.set_selected_source_event_index()` と `PreviewPanel.set_selected_source_event_index()` は既存test互換のため残す。
- B3のGUI接続ではadjustmentなしのempty canonical snapshotをresolverへ渡す。adjustment付き再解決はB4の責務である。
- current timing planとsource durationが揃わない場合、full resolverを推測値で呼ばずPreview placeholderへfail closedする。
- 追加のユーザー判断を要する未解決仕様は、計画作成時点ではない。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/core/preview_hit_test.py` | hit region DTO、座標変換、候補抽出、優先順位を持つpure helper |
| `src/core/preview_transform.py` | event hit regionをPreviewDataへ渡すimmutable metadata追加 |
| `src/gui_wx/preview_panel.py` | gesture state、4 DIP threshold、hit-test、multi-source highlight、event summary |
| `src/gui_wx/placeholder_panels.py` | selection callbackの中継 |
| `src/gui_wx/ui_state.py` | canonical selection identityとstrict commit / clear境界 |
| `src/gui_wx/main_frame.py` | B2 resolver接続、selection callback validation、UiState / Preview / RightPane同期 |

### 7.2 新規test

- `tests/test_ms21_b3_preview_hit_test.py`
- `tests/test_ms21_b3_selection_commit.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_wx_ms21_b3_preview_selection.py`

### 7.3 回帰確認対象

- `tests/test_wx_ms16_b6_event_selection_foundation.py`
- `tests/test_wx_ms16_b5_preview_contract.py`
- `tests/test_wx_ms16_b4_preview_shape.py`
- `tests/test_wx_ms15_b2_preview.py`
- `tests/test_preview_transform.py`
- `tests/gui_wx/test_viewport_controller.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b4_playback_context.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`

### 7.4 読み取り確認対象

- `src/core/effective_shape_plan.py`
- `src/core/event_adjustment.py`
- `src/core/pipeline.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/parameter_panel.py`
- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`

### 7.5 文書更新

- 実装後に本planへ実装結果、test結果、findings、ユーザー確認対象を追記する。
- Block Breakdown、Index、RoadmapをB3の実際の到達状態へ同期する。
- README、配布用readme、3正本仕様のimplemented表示はB7まで先行更新しない。

## 8. 実装方針

### 8.1 UI非依存の選択判定

wx event object、panel、colour、fontをcore helperへ渡さない。pure helperはprimitiveなpanel geometry、viewport、Preview provenanceから `base_event_index` または `None` を返す。pixel geometryとcanonical event identityを分離し、wxなしでboundaryと優先順位をtestする。

### 8.2 canonical data path

GUI PreviewはB3から次のbase-only経路を使用する。

```text
current VowelTimingPlan + observations
  + selected WAV duration
  + current global shape parameters
  + empty AdjustmentLayerSnapshot
    -> resolve_effective_shape_plan()
    -> build_preview_data_from_effective_shape_plan()
    -> PreviewData + base identity + event hit regions
```

legacy `build_preview_data()` はpublic互換入口として残す。B3はadjustment stateを作らず、B4が同じ接続へactual snapshotを追加できる形にする。

### 8.3 strict commitとlegacy setterの分離

- 既存 `set_selected_source_event_index()` はrender / compatibility APIとして挙動を変えない。
- mouse clickは新規canonical commit APIだけを通る。
- strict commitはcurrent base identity、rendered preview identity、event count、real provenance、Busy状態を検証する。
- validation failureは例外をUI loopへ漏らさずno-opとし、現在selectionを維持する。
- `bool`、非int、負数、範囲外index、Previewに存在しないindex、identity mismatchを拒否する。
- canonical selectionのbase identityと、描画datasetのrender revisionを別identityとして扱う。base identityだけでstale gestureを判定しない。

### 8.4 clickとdragの分離

- mouse-down原点、直近pan位置、最大累積移動、capture状態、base identity、`render_revision` をgesture stateとして保持する。
- thresholdはlogical 4 DIPを `FromDIP()` でdevice pixelへ変換して比較する。
- threshold未満はpanしない。
- threshold以上になったgestureはdragとしてpanし、mouse-upでselectionをcommitしない。
- threshold判定はmouse-downからの最大2次元距離とし、直近位置へ原点を更新しない。
- leave / capture lost / invalid data replacementはgestureをcancelし、selectionを変更しない。

## 9. 詳細ステップ

### Step 1: hit region DTOを追加

`src/core/preview_hit_test.py` に少なくとも次のimmutable DTOを置く。

```text
PreviewEventHitRegion
  - base_event_index: non-negative int
  - vowel: one of あ / い / う / え / お
  - start_frame: int
  - base_peak_frame: int
  - end_frame: int
  - peak_value: finite non-negative float

PreviewHitTestInput
  - x / y
  - width / height
  - viewport_start_sec / viewport_end_sec
  - event hit regions
```

- `0 <= start_frame <= base_peak_frame <= end_frame` とfiniteかつ0以上の `peak_value` を必須とする。
- B2 `effective_events` をbase indexで参照し、shapeの `real_base_event_indices` と `event_ranges` の対応を検証してregionを構築する。
- provenance tupleの長さ不一致、vowel不一致、重複矛盾、negative indexはfail closedにする。
- synthetic tokenをDTOへ変換しない。

### Step 2: 座標変換とlane境界を固定

- valid client areaは `0 <= x < width`、`0 <= y < height` とする。
- xは現在viewportの半開区間へ写像し、`cursor_frame = int(round(cursor_sec * 30))` とする。
- yは表示順 `あ / い / う / え / お` の5等分laneへ写像する。
- lane境界は上側inclusive、下側exclusiveとし、panel最下端はviewport外扱いにする。
- width / heightが0以下、非finite viewport、`end <= start` はhitなしとする。

### Step 3: hit-test優先順位を実装

- clicked laneと同じvowelのregionだけを見る。
- `start_frame <= cursor_frame <= end_frame` の候補だけを見る。
- 候補keyを `(abs(cursor_frame - base_peak_frame), base_event_index)` として最小値を選ぶ。
- zero-span eventは `start == peak == end` の1 frame regionとして選択可能にする。描画幅を広げるだけのhit paddingは追加しない。
- event range外、空lane、viewport外は `None` を返し、callerはselectionを変更しない。

### Step 4: PreviewDataへselection metadataを渡す

- `PreviewSegment` にimmutable `event_hit_regions` を既定空tupleで追加し、既存constructionを壊さない。
- `build_preview_data_from_effective_shape_plan()` はB2 effective eventからregionを構築して対応segmentへ渡す。event固有の `peak_value` をsegment全体の `intensity` へ置換しない。
- legacy `build_preview_data()` は既存 `source_event_index` と表示出力を維持し、新fieldを必須にしない。
- `find_shape_by_source_event_index()`、highlight、summaryは `source_event_indices` / `event_hit_regions` を優先し、legacy fieldへfallbackする。
- grouped segmentで任意memberが選択された場合はgroup shape全体をhighlightする。event固有のindex / frame range / peak frame / peak valueはregionからsummaryへ表示し、先頭indexやsegment最大intensityへ置換しない。

### Step 5: MainFrameをbase-only full resolverへ接続

- current timing plan、observations、selected WAV duration、global hold / softnessを `BaseTimingPlanInput` と `ShapeParameters` へ明示変換する。
- current base identityに対応するempty `AdjustmentLayerSnapshot` を生成する。
- full resolver resultとPreviewDataを一つのrender transactionとして更新する。
- resolver / adapter failureではplaceholderを表示し、rendered base identity、event hit regions、Preview selectionをclearして `render_revision` を更新する。旧datasetを残さない。
- legacy Previewとbase-only full resolverのrepresentative output equivalenceを回帰testで固定する。
- B3ではUiStateへadjustment snapshotを追加しない。

### Step 6: identity-aware PreviewModel更新

- PreviewModelはrendered base identity digest、event hit regions、単調増加するpanel-local `render_revision` を保持する。
- `render_revision` はPreview datasetの置換、identity-aware再構築、placeholder化のたびに更新し、base identity、adjustment identity、save-state fingerprintの代用にしない。
- different identity、placeholder、analysis invalidation、workspace resetではselectionをclearする。
- same identityのtheme、viewport、playback、layout、単純な再同期ではselectionを保持する。
- same base identityでshape parameterまたはB4以降のadjustmentにより描画datasetが変わった場合も `render_revision` は変える。base identityが同じことをdataset同一の根拠にしない。
- `set_preview_data()` の既存「常にclear」は互換caller向け既定動作として維持するか、新しいidentity-aware入口を別に設ける。既存MS16 testを黙って書き換えない。

### Step 7: gesture state machineを実装

```text
Idle
  -> left down on valid Preview: Pressed(origin, last, identity)

Pressed
  -> movement < 4 DIP: Pressed
  -> movement >= 4 DIP: Dragging + pan
  -> left up: hit-test + callback
  -> leave / capture lost / data replacement: Idle, no commit

Dragging
  -> motion: incremental pan
  -> left up / leave / capture lost: Idle, no commit
```

- `wx.EVT_MOUSE_CAPTURE_LOST` を明示処理する。
- callbackは `base_event_index`、mouse-down時base identity、mouse-down時 `render_revision` を含むrequest DTOまたは同等のprimitive値を渡す。
- callbackがない場合もcapture解放とstate resetを行う。

### Step 8: callbackをMainFrameへ中継

- PreviewPanelのselection requestをPlaceholderContainerが一方向に中継する。
- MainFrameはrequest受信時にBusy、current timing plan、current base identity、current `render_revision`、event count、Preview provenanceを再検証する。
- valid requestだけをUiState canonical commitへ渡す。
- `None` hit、invalid request、Busy、stale callbackでは現selectionを維持する。
- valid commit後だけPreview highlightとRightPane summaryを更新する。

### Step 9: UiState canonical selectionを追加

UiStateへ少なくとも次を追加する。

```text
selected_source_event_index: int | None       # existing
selected_base_plan_identity_digest: str | None

commit_selected_source_event_index(...)
  -> validならindex / digestを同時更新
  -> invalidならFalse、状態不変
```

- `clear_selection()` はindexとdigestを同時にclearする。
- 既存permissive setterは範囲外を含むindexの受理を維持するが、呼び出すたびに `selected_base_plan_identity_digest` をclearする。legacy render stateをcanonical selectionとして残さない。
- canonical click pathは既存permissive setterを呼ばず、indexとbase identity digestを同時に更新するstrict commitだけを使用する。
- analysis成功、input / parameter invalidation、workspace resetの既存clear入口を再利用する。

### Step 10: testを追加

pure test:

- 5 laneと上下境界
- viewport start / endとx境界
- single event hit
- event range外 / empty lane / viewport外
- overlapでpeak距離優先
- peak距離tieで小index優先
- grouped shapeの各member
- zero-span event
- synthetic token除外
- malformed provenance reject

pipeline / resolver / Preview統合test:

- test fixtureの代替DTOだけで完結させず、実pipelineが生成する `VowelTimingPlan` と実 `PeakValueObservation` を入力する。
- empty canonical `AdjustmentLayerSnapshot` を使って `resolve_effective_shape_plan()` を実行し、`build_preview_data_from_effective_shape_plan()` まで接続する。
- base event数、effective event数、Preview provenance、base identityが同じcanonical planを参照することを検証する。
- pipeline型またはB2 resolver契約の変更でGUI接続だけが遅れて壊れる回帰を検出する。

state / GUI test:

- click commitとUiState / highlight / RightPane同期
- 4 DIP未満click、4 DIP以上drag
- cumulative movementとincremental pan
- leave / capture lostでno commit
- Busy中no-op
- stale identity no-op
- stale render revision no-op
- permissive legacy setterの未知index許容維持
- canonical selection後にpermissive setterを呼ぶとcanonical digestだけがclearされる
- different identity / placeholder / resetでclear
- same identityのviewport / playback / theme更新で保持
- grouped segmentの非先頭event highlight / summary

### Step 11: 実装後記録

- 実際の変更fileとAPI名
- full resolver GUI接続の範囲
- thresholdのDIP / device pixel変換
- selection lifecycle matrix
- 実行testのpass表示とprocess exit code
- GUI手動確認項目と実施有無
- P1 / P2 / P3とB4着手可否

## 10. 状態遷移 / データ契約

### 10.1 selection request

```text
Preview render
  - base identity digest D
  - render revision G
  - real event hit regions R

left click below drag threshold
  -> hit_test(position, viewport, R)
  -> SelectionRequest(base_event_index, D, G)
  -> MainFrame revalidates current base identity == D
     and current render revision == G
     and Busy == false
  -> UiState strict commit(index, D)
  -> Preview highlight + RightPane summary
```

### 10.2 no-op条件

次はselectionを変更しない。

- event range外
- empty lane
- viewport外
- drag gesture
- mouse leave / capture lost
- Busy
- current base identity mismatch
- stale render revision
- invalid / negative / bool / out-of-range index
- synthetic token
- current timing planまたはduration不足

### 10.3 clear条件

次はselectionをclearする。

- new analysis success / different base identity
- input変更
- parameter変更によるanalysis invalidation
- Preview placeholder / resolver failure
- workspace reset

次はselectionを保持する。

- same base identityの再同期
- theme変更
- viewport pan / zoom / reset
- playback position更新 / stop

### 10.4 grouped shape

- selected identityは常に個別real `base_event_index` である。
- shape全体highlightは視覚表現であり、groupを単一eventへ変換しない。
- RightPane summaryはselected event固有rangeを表示する。
- B4の補正controlはこの個別identityを引き継ぐ。

## 11. テスト方針

### 11.1 計画作成baseline

2026-07-22に次を実行した。

1. `.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b6_event_selection_foundation.py -q`
   - 4件pass表示
   - process exit code 0
2. `.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms16_b5_preview_contract.py tests/test_wx_ms16_b4_preview_shape.py tests/test_wx_ms15_b2_preview.py tests/gui_wx/test_viewport_controller.py -q`
   - 16件pass表示
   - process exit code 0
3. `.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_shape_adapters.py -q`
   - 6件pass表示
   - process exit code 0

### 11.2 実装時の順序

1. B3 pure hit-test / selection commit test
2. B3 wx selection test
3. MS16 selection / Preview / viewport回帰
4. 実pipeline生成型からB2 full resolver、Preview adapterまでの統合test
5. B2 effective plan / event adjustment / adapter回帰
6. pipeline / VMD回帰
7. playback / reset / late callback回帰
8. 全体test
9. `compileall src tests`
10. `git diff --check`

pass表示とprocess exit codeを分けて記録する。既知wx終了処理由来のnonzero exitも成功と読み替えない。

### 11.3 手動GUI確認候補

- 単一eventをクリックするとhighlightとRightPane summaryが一致する。
- grouped shapeの先頭以外のeventを選べる。
- 空lane、event外、Preview外ではselectionが変わらない。
- 小さな手ぶれはclick、明確なdragはpanとなり選択されない。
- pan / zoom / Reset Zoom / Play / Stop後も同じevent選択が維持される。
- 再解析、input / parameter変更、新規作業でselectionがclearされる。
- Busy中のクリックでselectionが変わらない。
- dark / light themeでhighlightと文字が判読可能である。

## 12. 受け入れ条件

- clickでcanonical real base eventを選択できる。
- B1のlane、range、peak距離、index tie-break規則を満たす。
- grouped shapeの全real memberを個別に選択できる。
- grouped shapeの各memberについてevent固有のframe range、peak frame、peak valueを表示できる。
- negative synthetic tokenを選択しない。
- 4 DIP未満のclickと4 DIP以上のdragを区別する。
- drag、empty lane、event外、viewport外、Busy、stale requestでselectionを変更しない。
- invalid canonical commitをfail closedで拒否する。
- base identityが同じでもrender revisionが異なるstale requestを拒否する。
- existing permissive setterとMS16 selection foundation testを維持する。
- permissive setter経由のselectionへcanonical base identityを残さない。
- UiState、Preview highlight、RightPane summaryが同じindexを表示する。
- identity変更 / placeholder / resetでclearし、theme / viewport / playback更新で保持する。
- B2 full provenanceを使い、legacy first indexをcanonical keyにしない。
- B4の編集control、B5の保存 / diagnostics、B6のhistoryを先行実装しない。
- dependency、package、license、network、Qt、固定モーフに変更がない。
- 指定test結果とprocess exit codeが記録される。
- 実装後のP1 / P2が残らず、B4着手可否が明示される。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| grouped shapeの先頭eventしか選べない | `source_event_indices` とevent別regionを正本とし、legacy fieldはfallbackだけに使う |
| synthetic tokenをbase indexと誤認する | negative tokenはinternal metadataに限定し、hit region生成時にrejectする |
| clickの微小移動でpanになる | mouse-downからの累積距離と4 DIP thresholdを使う |
| high DPIでgesture感度が変わる | `FromDIP(4)` でdevice pixelへ変換する |
| incremental panでdrag判定原点を失う | threshold原点と直近pan位置を別fieldにする |
| stale clickが新解析結果または同一baseの別描画datasetを選択する | mouse-down時のbase identityとpanel-local render revisionをcommit時に再照合する |
| sync_ui_stateでselectionが毎回消える | same identityのrender更新とdifferent identity更新を分離する |
| empty clickで意図せず解除される | B1どおりhitなしをno-opに固定する |
| full resolver接続でlegacy Preview shapeが変わる | adjustmentなしのadapter equivalenceと既存Preview回帰を実行する |
| B3がadjustment lifecycleへ拡大する | empty snapshotだけを使い、UiState adjustment所有はB4以降へ残す |
| RightPane summaryがgroup先頭またはgroup最大値を表示する | selected event固有regionをlookupしてindex / frame / peak valueを表示する |
| wx capture lostでgestureが残る | capture-lostとleaveを明示的なcancel遷移にする |

## 14. Codex 実装時の注意

- 最初にGit状態、Index、Block Breakdown、B1、B2、本planを再確認する。
- pre-implementation checkではproduction / testを変更せず、P1 / P2 / P3を報告する。
- shell commandは一つずつ実行し、parallel、pipeline、chained commandを使わない。
- existing user-owned差分をrestore、上書き、無断stageしない。
- legacy `source_event_index` をcanonical keyへ昇格させない。
- permissive setterをstrict化して既存testを壊さず、新しいcommit境界を追加する。
- mouse event handler内でresolverを再実行しない。render済みimmutable metadataを使う。
- wx objectをcore hit-test helperへ渡さない。
- Busy、late callback、capture lost、placeholderをnormal pathとしてtestする。
- empty clickでselectionをclearしない。
- test expectationを弱めてpassさせない。
- manual GUI確認を実施していない段階でverifiedと記載しない。
- 実装完了後は7項目形式で確認file、変更file、実装、test、結果、逸脱、残課題を報告する。

### 14.1 2026-07-22 plan整合レビュー修正

- 初回レビューではP1なし、P2 3件、P3 2件を検出した。
- P2として、base identityとrender revisionの混同、grouped event固有summaryに必要なpeak value不足、permissive setter後にcanonical digestが残り得る状態契約を補正した。
- base identityとpanel-local `render_revision` を分離し、same base identityでも描画dataset更新時はrevisionを更新する。selection requestは両方を保持し、commit時に再照合する。
- `PreviewEventHitRegion` はevent固有のbase peak frameとpeak valueを保持する。grouped segment最大intensityを選択eventの値として表示しない。
- existing permissive setterは未知index許容を維持しつつcanonical digestをclearする。strict commitだけがindexとbase identityを同時更新する。
- P3として、baseline commandのrepository-local path表記を修正し、`tests/test_ms20_b3_right_pane_info.py` を限定回帰対象へ追加した。
- 修正後の再チェックではP1 / P2 / P3の残存なしと判定した。selection 4件、Preview / viewport 16件、B2 adapter 6件、RightPane / playback / reset / late callback 50件はすべてpass表示、各process exit code 0だった。`git diff --check` もprocess exit code 0だった。

### 14.2 2026-07-23 pre-implementation check修正

- pre-implementation checkではP1 / P2なし、P3 2件を検出した。
- B3が直接利用するB2 full resolverとempty adjustment契約を保護するため、`tests/test_ms21_b2_effective_shape_plan.py` と `tests/test_ms21_b2_event_adjustment.py` を限定回帰対象へ追加した。
- B3が初めて実pipeline生成型をGUI Previewのfull resolver経路へ接続するため、実 `VowelTimingPlan` と実 `PeakValueObservation` を `resolve_effective_shape_plan()`、`build_preview_data_from_effective_shape_plan()` へ通す専用統合testを追加要件として固定した。
- `tests/test_pipeline_and_vmd.py` も限定回帰対象へ追加し、pipeline入力契約からの回帰を直接確認する。
- 修正前の動的確認では、実pipelineからB2 resolver、Preview adapterまでの補助スモークが正常完了しprocess exit code 0だった。B2 effective plan / shape adapter 22件、event adjustment 13件、pipeline / VMD 12件はすべてpass表示、各process exit code 0だった。
- 上記追記によりpre-implementation checkのP3は解消済みとし、MS21-B3は実装着手可能と判定する。

## 15. 2026-07-23 実装結果

### 15.1 実装内容

- `src/core/preview_hit_test.py` を追加し、5母音lane、viewport座標、30fps frame変換、event range、base peak距離、base index tie-breakを使うpure hit-testを実装した。
- `PreviewEventHitRegion` はreal base eventのindex、vowel、start / base peak / end frame、peak valueを保持し、negative / bool / 非finite / frame順序不正を拒否する。
- B2 full resolverの `effective_events` と `shapes` を照合し、Preview segmentへevent別hit regionを渡す。未知index、range不一致、重複shape参照をfail closedにした。
- MainFrameのGUI Preview経路を、current `VowelTimingPlan`、実observations、解析用WAV duration、global shape parameter、empty canonical adjustment snapshotを使うB2 full resolverへ切り替えた。
- PreviewModelへbase identity digestとpanel-local `render_revision` を追加した。同一baseのviewport / playback / theme再描画ではselectionを保持し、data置換時はrevisionを更新する。
- Preview gestureを4 DIP未満のclickと4 DIP以上のdragへ分離し、leave / capture lost / data replacementではcommitせずcancelする。
- `PreviewSelectionRequest` はbase event index、mouse-down時base identity、render revisionを保持し、MainFrameとUiStateのstrict commitでBusy、stale identity、stale revision、未知indexを拒否する。
- legacy permissive setterは未知index許容を維持する一方、canonical base identity digestをclearする。
- grouped shapeでは任意のreal memberを選択でき、shape全体をhighlightしながらRightPane summaryへ選択event固有のrange、base peak frame、peak valueを表示する。
- selected outlineはtheme paletteのtext colourを使用し、dark / light theme双方でcontrastを確保する。

### 15.2 変更ファイル

- 新規 `src/core/preview_hit_test.py`
- `src/core/preview_transform.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- 新規 `tests/test_ms21_b3_preview_hit_test.py`
- 新規 `tests/test_ms21_b3_selection_commit.py`
- 新規 `tests/test_ms21_b3_pipeline_preview_integration.py`
- 新規 `tests/test_wx_ms21_b3_preview_selection.py`
- `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`

### 15.3 自動検証

- B3新規test: 22件pass表示、process exit code 0。
- B2 effective plan / shape adapter: 22件pass表示、process exit code 0。
- B2 event adjustment: 13件pass表示、process exit code 0。
- MS16 selection / Preview / viewport / Preview transform回帰: 50件pass表示、process exit code 0。
- RightPane / playback / workspace reset / late callback回帰: 50件pass表示、process exit code 0。
- pipeline / VMD回帰: 12件pass表示、process exit code 0。
- 全体test: 533件pass、7 subtests pass表示、process exit code 0。
- `compileall src tests`: process exit code 0。
- dependency、package、license、network、Qt、固定モーフに変更なし。

### 15.4 ユーザーGUI確認・次段階

- 2026-07-23に、修正後のB3ユーザーGUI確認は通過・問題なしと報告された。
- click選択、drag panとの分離、選択highlight、RightPane summary、viewport / playback操作、theme表示を含むB3確認項目を完了扱いとする。
- 開口維持・閉口スムーズ変更で「再解析が必要」へ遷移する挙動は、現行のglobal parameter invalidation契約どおりであり、B3のselection不具合ではないことを確認した。B4のevent補正controlによるlive Previewとは区別する。
- B3のproduction実装、自動検証、ユーザーGUI確認は完了した。次はMS21-B4 Implementation Plan策定である。
- B4のevent補正control、adjustment付きlive Preview、B5以降の保存 / diagnostics、Undo / Redoは未実装であり、B3の範囲外として維持した。

### 15.5 手動GUI確認中の描画例外修正

- event選択後のpaintで、`PreviewRenderer._draw_lanes()` が未定義の `palette` をselection outline生成時だけ参照し、`NameError` となる問題をユーザー確認で検出した。
- `_draw_lanes()` の入口でcurrent theme paletteを取得するよう修正した。
- selected rendererを直接実行する回帰testを追加し、修正前に同じ `NameError` とprocess exit code 1、修正後に1件pass表示とprocess exit code 0を確認した。
- 修正後はB3新規22件、Preview / selection / viewport回帰50件、全体533件と7 subtestsがすべてpass表示、各process exit code 0だった。
- 修正後のユーザーGUI再確認は2026-07-23に通過し、問題なしと報告された。
