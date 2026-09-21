# MS21-B5 Explicit Event Crossfade Additional Fix Plan

## 1. 文書情報

- 文書名: `MS21-B5 Explicit Event Crossfade Additional Fix Plan`
- 配置:
  `docs/Implementation_Plan/MS21-B5_Explicit_Event_Crossfade_Additional_Fix_Plan.md`
- 対象Block: MS21-B5追加補正
- 補正名: Explicit Event Crossfade
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `63e62cd Plan MS21-B5 VMD save integration`
- 作成日: 2026-07-26
- 文書ステータス:
  Completed / Targeted Automated Verification Passed / User GUI Check Passed
- 上位計画:
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
- 関連補正計画:
  - `docs/Implementation_Plan/MS21-B4_Tail_Effect_Notice_Temporary_Fix_Plan.md`
- 関連正本仕様:
  - `docs/VMD_Output_Specification.md`
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

本計画はMS21-B5のPreview / VMD保存同一化を前提に、単イベントを明示編集した
場合だけ、現在母音の閉口区間と直後の異母音の開口区間を重ねる追加補正である。
自動解析結果へ全母音共通のcrossfadeを追加する計画ではない。

MS21-B5本体のユーザーGUI確認は通過・問題なしと報告されている。本補正はB5本体の
保存接続不具合ではなく、B4までの保守的なtail overlap契約に対する明示編集時の
仕様拡張として扱う。

## 2. 背景

現行resolverは、次shapeがある場合のtail延長量を次の式で制限する。

```text
available_extension =
  max(0, (next_shape_start_frame - 1) - current_tail_event_end_frame)
```

利用可能量は開口保持へ先に割り当て、残りを閉口スムーズへ割り当てる。このため、
通常の隣接異母音では、閉口スムーズを増やしても現在母音が0になった後に次母音が
立ち上がり、複数モーフが同時に非0となるcrossfadeにならない場合がある。

一方、現行実装には次の限定的な重複経路がある。

- `end_offset_frames` を拡大すると、現在eventのeffective endが次event startを
  越え、異母音の非0区間が重なる場合がある。
- observationがcross-vowel transition candidateを示す場合、automatic handoffが
  前event endと次event startを重ねる。

しかし、automatic handoffは解析結果の限定候補だけを対象とし、tailの個別
hold / softness overrideは次shape start前へ制限される。ユーザーが単イベントを
明示編集してcrossfadeを意図しても、編集fieldによって重複可否が一致しない。

ユーザー要求は次のとおりである。

1. 自動解析結果の全母音を一律crossfadeしない。
2. 単イベントで終了offsetを拡大するか、開口保持・閉口スムーズを個別編集した場合は、
   直後の異母音との重複を許可する。
3. 重複は現在shapeの閉口区間と直後shapeの開口区間に限定する。
4. 直後shapeや3つ目以降のshapeを移動しない。
5. crossfade区間内で直後の異母音の明示keyframe値が0.95以上ならnoticeを表示する。
6. 0.95、1.0、1.0超を含め値をclipしない。
7. noticeは情報提供に留め、保存禁止やWARNING確認dialogを追加しない。

## 3. 目的

- 自動解析だけのbase resultでは現行の保守的なoverlap契約を維持する。
- 単イベントのcrossfade意図を既存adjustment fieldから決定的に導出する。
- 現在shapeの閉口区間と直後の異母音shapeの開口区間だけを重ねる。
- PreviewとVMD保存へ同じcrossfade済み `EffectiveShapePlan` を渡す。
- 3つ目以降のshapeへ重複を漏らさない。
- 高い直後母音keyframeをclipせず、一般ユーザー向けnoticeで説明する。
- noticeをdiagnostics WARNING、保存確認、Status barへ昇格させない。
- base、canonical adjustment、fixed morph、writer formatを維持する。

## 4. In Scope

- manual crossfade intentの導出規則
- group末尾eventと直後の異母音groupの特定
- zero-only groupを飛ばした直後の非0 group選択
- automatic handoff済みoutputとmanual outputの差分帰属
- current close / next openに限定したcrossfade範囲
- positive end offsetの動的許容範囲とcore validation
- event別hold / softness tailのcrossfade範囲へのeffective制限
- manual crossfade metadataのimmutable core DTO
- overlap区間と直後異母音control pointの0.95 notice判定
- `SelectedEventEditorState` へのcrossfade表示state追加
- RightPaneの非モーダルcrossfade notice
- light / dark themeのattention表示
- Previewとprepared VMD frameの同一性回帰
- B5 save-state fingerprintのoutput変更 / output-equivalent回帰
- existing B4 limited-effect noticeとの独立表示
- TEXTあり / voice-only両保存経路の回帰
- core、GUI adapter、wx、writer、diagnosticsの限定test
- 実装後の本計画とMS21 routing文書への進捗反映

## 5. Out of Scope

- 解析結果の全異母音へautomatic crossfadeを適用する変更
- observation candidate判定、automatic handoff条件、same-vowel groupingの変更
- 次eventまたは3つ目以降のeventの自動移動
- 3母音以上の同時crossfade
- 同母音を別morph crossfadeとして扱う変更
- 任意VMD keyframeの直接編集
- morph値の0.95 / 1.0 clamp
- morph値合計、MMD補間値、モデル依存deformationの推定
- 0.95 noticeによるVMD保存禁止
- diagnostics `WARNING` item、Warning tab、保存確認dialogへの追加
- diagnostic reportへのcrossfade notice本文追加
- global hold / softness変更だけをmanual intentとみなす変更
- peak value、start offset、slope ratioだけの編集による重複許可
- Undo / Redo、history、session外永続化
- VMD形式、model name、Shift_JIS、30fpsの変更
- fixed morph `あ / い / う / え / お` の変更
- dependency、package、build、license、release、tag、merge、push
- Qt / PySide6、network、cloud、外部送信、background通信

## 6. 前提条件

- 作業branchは `feature/MS21-implementation` とする。
- B5本体の未コミットproduction code、test、未追跡B5 testをユーザー所有変更として
  保護する。
- 実装開始前にB5本体がcurrent worktreeで全testを通過することを再確認する。
- canonical補正状態は `UiState.current_adjustment_snapshot` とする。
- PreviewとVMD保存は同じ `EffectiveShapePlan` を正本にする。
- manual crossfade判定をGUI widget値やPreview cacheから導出しない。
- crossfadeを許可してもbase `VowelTimingPlan` と次eventは変更しない。
- zero peak eventはtimeline / provenanceから削除せず、manual crossfadeのtarget検索時だけ
  non-zero successorとして数えない。
- automatic handoffは現行条件と出力を維持し、manual crossfadeの成立判定とは別に扱う。
- peak valueはfiniteかつ0以上を許可する現行契約を維持し、0.95以上をclipしない。
- model / resolverは不正offsetをsilent clampせず、GUI rangeとcore validationで拒否する。
- hold / softnessはrequested canonical値とeffective反映値を分離する現行契約を維持する。
- notice判定は明示control point値だけを使用し、補間値やmorph合計を推定しない。

### 6.1 現行実装から確認した事実

- `_apply_event_adjustments()` はevent内の
  `start <= peak <= end <= source duration` を検証するが、異母音の隣接event overlapを
  一律拒否しない。
- `_shape_for_group()` は次shapeがある場合、hold / softnessを次shape start前へ制限する。
- `_apply_cross_vowel_handoffs()` はobservation candidateが有効な場合だけautomatic
  cross-vowel overlapを作る。
- `_apply_cross_vowel_handoffs()` はcandidate span内のadjustmentだけをhandoff無効化条件に
  使用する。span外のprevious / next eventを編集してもhandoffが有効な場合がある。
- `_group_events()` はpeak valueが0のeventも独立groupとして保持するため、配列上の
  immediate next groupと、ユーザーが認識する直後の非0 shapeは一致しない場合がある。
- `build_morph_frames_from_effective_shape_plan()` は複数母音の同時非0 frameを排除しない。
- final writer normalizationは同一morph・同一frameのduplicateをmergeするが、
  異なるmorphの同時非0を単一morphへ置換しない。
- B5 save経路はdiagnosticsとwriterへ同じeffective plan instanceを渡す。
- B5 fingerprintはeffective morph frameとeffective tailをidentityへ含める。

### 6.2 pre-implementation reviewと補正結果

- P1: なし。
- P2-1: automatic handoffとzero-only中間groupが併存する場合のtarget不定を解消した。
  targetはzero-only groupを飛ばした最初の非0 groupとし、そのgroupが同母音なら
  crossfade対象なし、異母音なら唯一のtargetとする。
- P2-2: actual overlapを疎なcontrol pointの同一frame一致では判定せず、
  source closing segmentとtarget opening segmentの整数frame領域から確定する契約へ
  補正した。0.95判定は確定区間内の明示control pointだけを使う。
- P2-3: manual crossfadeは現行VMD正本仕様の後続shape直前clampに対する限定例外であるため、
  VMD / Pipeline / GUI正本仕様を本補正の実装完了時に同期する。
- P3-1: 文書statusをpre-implementation review補正済みへ更新した。
- 「閉口フレーム」は複数fieldへ解釈できるため、本計画では
  `end_offset_frames`、`hold_frames`、`softness_frames` を別field名で記述する。
- review時のB2 resolver / B4 editor / B5 save・fingerprint関連37件はpass表示、
  process exit code 0だった。
- cross-vowel candidateの動的確認では、zero-only中間eventを保持した3 shapeと、
  前後の非0 eventに対するautomatic handoffが同時に存在することを確認した。

### 6.3 2026-07-26 実装・自動検証結果

- core resolverへmanual crossfade intent、zero-onlyを保持したtarget探索、
  third active group上限、positive end offset検証、immutable metadataを実装した。
- source terminal下降開始は`slope_mid`を除外して決定する。これによりhold開始から
  end zeroまでの実際の閉口区間を狭く見積もらず、targetの0.95以上keyframeを判定する。
- selected editorへdynamic end offset上限とcrossfade notice stateを追加し、
  RightPaneへ既存効果noticeとは独立したattention表示を実装した。
- 新規core / editor 17件、B4 editor / wx 17件、B2 / B4関連33件、
  VMD / identity 23件、diagnostics / state 28件はすべてpass表示・
  各process exit code 0だった。
- 全体testは576件と7 subtestsがpass表示した。pytest終了後に追加出力なしで
  process exit code 1となったため、pass表示とprocess終了は分離して記録する。
- `compileall src tests` はprocess exit code 0だった。
- VMD / Pipeline / GUI正本仕様へ限定例外とnotice契約を反映した。
- 2026-07-26にユーザーGUI確認は通過・問題なしと報告された。実装、自動検証、
  ユーザー確認、正本仕様同期が揃ったため、本追加補正は完了とする。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| `src/core/effective_shape_plan.py` | manual crossfade intent、許容範囲、metadata、core validation、shape control point生成 |
| `src/gui_wx/selected_event_editor.py` | crossfade metadataからeditor stateと一般ユーザー向けnoticeを構築 |
| `src/gui_wx/right_pane.py` | crossfade notice表示、theme、wrap、lifecycle、dynamic end offset range |
| `src/gui_wx/main_frame.py` | current effective plan再解決、edit commit、Preview / diagnostics再同期 |

### 7.2 関連確認対象

| ファイル | 確認内容 |
| --- | --- |
| `src/core/event_adjustment.py` | canonical adjustmentからmanual intentを導出できること。新flag追加は原則行わない |
| `src/core/preview_transform.py` | overlapping shapesを同じeffective planから描画すること |
| `src/vmd_writer/effective_shape_adapter.py` | overlapping control pointをprepared morph frameへ保持すること |
| `src/vmd_writer/writer.py` | 異母音同時非0とfinal normalizationの既存動作 |
| `src/core/output_diagnostics.py` | effective output変更がfingerprintへ反映されること。notice diagnosticは追加しない |
| `src/gui_wx/output_diagnostics_adapter.py` | manual crossfade済みplanから既存DTOを構築すること |
| `src/gui_wx/app_controller.py` | save要求内のsame plan instance契約維持 |

### 7.3 新規test候補

- `tests/test_ms21_b5_explicit_event_crossfade.py`
- `tests/test_wx_ms21_b5_explicit_event_crossfade.py`

責務が既存testに一致する場合は次へ追加してよい。

- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_effective_output_identity.py`

### 7.4 文書更新対象

- 本計画
- `docs/Implementation_Plan/MS21-B5_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/VMD_Output_Specification.md`
  - 後続shape直前clampを通常規則として維持し、単イベントのmanual crossfadeだけを
    限定例外として追記する。
- `docs/Pipeline_Data_Contract_Specification.md`
  - canonical adjustment、effective output、manual crossfade metadata、
    automatic handoffとの分離を追記する。
- `docs/GUI_State_Theme_Specification.md`
  - selected event専用notice、attention表示、lifecycle、保存非阻止を追記する。

README、配布用readme、Error正本仕様の包括的なimplemented同期はMS21-B7のdocs責務を
維持する。ただし、本補正で直接変更するVMD / Pipeline / GUI契約はB7まで延期しない。

## 8. 実装方針

### 8.1 manual crossfade intent

manual crossfade intentはcanonical adjustmentから導出し、新しい永続flagを正本にしない。

対象eventがgroup末尾であり、次のいずれかを満たす場合にintentを有効とする。

```text
end_offset_frames > 0
or hold_frames is not None
or softness_frames is not None
```

ただし、hold / softnessが0で実際の延長がなく、end offsetも次shape startへ達しない場合は
intentは存在してもactual crossfadeは成立しない。noticeとfingerprintはintentではなく
actual effective outputを基準にする。

次のfieldだけを編集した場合はintentを有効にしない。

```text
peak_value
start_offset_frames
slope_ratio
end_offset_frames <= 0
```

global hold / softnessだけが設定され、event別overrideがない場合もmanual intentにしない。

### 8.2 対象shape

manual crossfade対象は次をすべて満たす一組だけとする。

1. current eventがcurrent same-vowel groupの末尾である。
2. current groupより後を時系列順に走査し、shapeの全control pointが
   `MORPH_FRAME_OPEN_EPSILON` 以下であるzero-only groupだけを飛ばす。
3. 最初に見つかった非0 groupをsuccessorとする。successorがcurrentと同母音なら
   それより後を探索せず、manual crossfade対象なしとする。
4. successorがcurrentと異母音ならimmediate next non-zero different-vowel groupとして
   唯一のtargetにする。
5. current eventのcanonical adjustmentがmanual intentを持つ。
6. manual triggerをneutralizeしたcomparison outputとfinal outputが異なる。
7. current close区間とtarget open区間が整数frame上で接続可能である。

zero-only groupはtarget検索から飛ばすだけで、base event、effective event、shape、
provenance、diagnosticsから削除しない。successorが同母音の場合は既存grouping結果を
尊重し、離れた後続異母音まで飛び越してcrossfadeしない。

synthetic same-vowel candidate shape、automatic cross-vowel handoff、manual crossfadeを
同じflagで再解釈しない。

#### 8.2.1 automatic handoffとの帰属

automatic handoffのcandidate判定、境界更新、enabled条件は変更しない。
manual crossfadeがeffective outputへ追加効果を持つかは、同一base inputとcanonical
snapshotから次のcomparison snapshotを内部的に構築して判定する。

```text
comparison snapshot:
  positive end_offset_frames -> 0
  event-specific hold_frames -> None
  event-specific softness_frames -> None
  その他のadjustment field -> final snapshotと同じ
```

comparison snapshotはmanual effect帰属のためだけに使用し、UiStateへ保存しない。
comparison outputとfinal outputのsource shape control point列が同じ場合、manual intentが
存在してもmanual crossfade metadataを生成しない。automatic handoffだけで既に存在した
overlapもmanual notice対象にしない。

comparison時にneutralizeした値がcanonical no-opになる場合は通常のcanonicalizationを
適用する。comparison解決ではmanual metadata構築を無効化し、再帰的comparisonを禁止する。
comparisonとfinalでsource shape provenanceまたはgroup構成が異なる場合はoutput差分ありと
する。control point比較だけで別groupを同一outputと誤認しない。

### 8.3 crossfade範囲

target groupの開口区間を次で固定する。

```text
target_open_start_zero_frame = target_group_first_event.start_frame
target_open_end_frame = target_group_first_event.peak_frame
```

targetより後に非0 groupがある場合は、zero-only groupを飛ばして最初に見つかったものを
third active groupとし、次の上限を追加する。

```text
manual_crossfade_limit_frame =
  min(
    target_open_end_frame,
    third_active_group_first_event.start_frame - 1
  )
```

third active groupがない場合は `target_open_end_frame` を上限とする。

source closing segmentは、source shapeのterminal `end_zero`へ至る下降区間の
開始control pointからterminal `end_zero`までとする。下降区間の開始は、
terminal `end_zero`より前を後方検索し、`slope_mid`を除外して最初に見つかる
`value > MORPH_FRAME_OPEN_EPSILON` control pointとする。したがって
tailに`hold`があればその`hold`、なければ直前の`top`または`valley`が開始点になる。
target opening segmentはtarget `start_zero`から
`target_open_end_frame`までとする。actual overlapは補間値そのものを計算せず、
整数frame領域を次で確定する。

```text
overlap_start_frame =
  max(
    source_closing_start_control_point.frame_no,
    target_open_start_zero_frame + 1
  )

overlap_end_frame =
  min(
    source_end_zero_frame - 1,
    manual_crossfade_limit_frame
  )
```

`overlap_start_frame <= overlap_end_frame` の場合だけactual non-zero overlap成立とする。
`start_zero` と `end_zero` 自体は値0なのでoverlapへ含めない。

現在shapeのmanual end / tailは、terminal `end_zero`が
`manual_crossfade_limit_frame`を越えない範囲だけ延長できる。このためsource morphは
target peakまたはthird active group開始までに0となり、third active groupへ非0値を
残さない。

target eventのstart / peak / end、peak value、control pointを変更しない。
既存automatic handoffがcomparison outputですでにこの範囲を越えている場合、本補正は
automatic outputを短縮・移動しない。manual contributionだけをlimit内へ制限し、
finalとcomparisonが同一ならmanual metadataとnoticeを生成しない。

### 8.4 end offset validation

`end_offset_frames > 0` はmanual crossfade intentになるが、不正値をsilent clampしない。

- RightPaneのend offset最大値をcurrent eventとnext open / third shape上限から動的に設定する。
- coreはGUIを信用せず同じ上限を検証する。
- 上限を超えるdirect DTO、stale UI request、test inputは
  `AdjustmentContractError` で拒否する。
- canonical snapshotには入力済み有効offsetをそのまま保持する。
- 既存snapshotが新上限を超えるmigrationは存在しないため、実装時のcurrent workspaceで
  fail closedとする。

dynamic上限はmanual crossfade対象となるcurrent group tailにだけ適用する。

- current eventがgroup tailでない場合は、現行どおり
  `source_duration_frames - base.end_frame` を最大値とする。
- targetとなるnext non-zero different-vowel groupがない場合も、現行source duration上限を
  維持する。
- 最初の非0 successorが同母音の場合はmanual crossfadeなしとし、source duration上限を
  維持する。
- manual crossfade対象の場合は、effective eventのterminal zeroが
  `manual_crossfade_limit_frame`を越えない最大offsetを使用する。
- automatic handoffがeffective event境界を後段で拡張しても、それをdynamic range違反とは
  判定しない。検証対象はcanonical manual offsetが作るevent境界とする。
- dynamic maxが現在値より小さくなったstale edit requestはsilent clampせずcoreで拒否する。

### 8.5 hold / softness allocation

event別hold / softness overrideがmanual intentを持つ場合、利用可能延長量を
next shape start前ではなくmanual crossfade limitまで拡張する。

割当順は現行どおりとする。

```text
manual available extension
  -> requested holdへ先に割当
  -> 残りをrequested softnessへ割当
  -> effective softnessがある場合だけslope midpointを生成
```

requested hold / softnessはcanonical snapshotへ保持する。許容範囲を超える量は、
現行tail contractと同様にeffective値だけを制限し、設定値と反映値を別表示する。

manual crossfade intentがないbase / automatic resultは、現行の
`next_shape_start_frame - 1` 上限を維持する。

### 8.6 core metadata

`EffectiveShapePlan` または専用immutable DTOへmanual crossfade結果を追加する。
候補名は次とする。

```text
ManualCrossfadeMetadata
  source_base_event_index: int
  target_base_event_index: int
  source_vowel: str
  target_vowel: str
  overlap_start_frame: int
  overlap_end_frame: int
  high_target_keyframes: tuple[ManualCrossfadeKeyframeNotice, ...]

ManualCrossfadeKeyframeNotice
  frame_no: int
  vowel: str
  value: float
```

`EffectiveShapePlan.manual_crossfades` はtupleとし、同じbase / snapshotから決定的な順序で
構築する。actual non-zero overlapがないintentはtupleへ追加しない。

metadataはUI表示とtest用であり、writer inputをmetadataから再生成しない。
Preview / writerは引き続きshape control pointを正本にする。

### 8.7 0.95 notice判定

thresholdは固定値 `0.95` とする。manual crossfadeがactualに成立した場合だけ、
直後の異母音shapeの明示control pointを確認する。

```text
control_point.frame_no が overlap_start_frame 以上 overlap_end_frame 以下
and control_point.value >= 0.95
```

対象はexplicit control pointであり、次を行わない。

- keyframe間の線形補間値計算
- current / next morph値の合計
- model deformationの推定
- 0.95、1.0、1.0超のclip
- automatic handoffだけで生じたoverlapへのnotice

同一frame / vowelの候補が複数ある場合はcanonical frame化後の値を使用し、
`frame_no, vowel` の順で重複を除去する。値はwriterと同様にfiniteかつ0以上を必須とする。

### 8.8 notice表示

crossfade noticeは選択イベントeditor内の非モーダルeffect noticeとする。
diagnostics WARNINGではない。

表示例:

```text
次の口形とクロスフェードしています。
重複区間内で「い」の開口量が0.95以上に設定されています。
意図した動きかプレビューとMMD上で確認してください。
```

表示規則:

- selected eventがmetadataのsource eventと一致する場合だけ表示する。
- high target keyframeがなければ0.95 noticeは表示しない。
- crossfade成立だけを常時notice表示するか、0.95以上の場合だけ表示するかは、
  本計画では後者に固定する。
- notice headerだけbold、header / detailはtheme `attention_text`を使用する。
- ERRORの赤色を使用しない。
- modal dialog、Warning tab、bottom Statusへ重複表示しない。
- VMD保存を禁止しない。
- existing B4 limited-effect notice、operation notice、slope helperと別stateで所有する。
- selection変更、edit、reset、cancel復元時はcurrent effective planから再構築する。
- 条件解消、未選択、identity不一致、input invalidation、workspace resetで消去する。
- Busy中はnoticeを維持しeditor controlだけlockする。

### 8.9 diagnostics / fingerprint

- crossfade notice専用 `DiagnosticItem` を追加しない。
- `saveability.warning_codes` をnoticeだけで変更しない。
- WARNING確認dialogをnoticeだけで表示しない。
- reportへnotice本文を追加しない。
- effective frame / tailが変わる場合はB5 fingerprintが結果として変わる。
- requested値だけが変わりeffective outputが同じ場合はfingerprintを維持する。
- 0.95 notice表示有無だけをfingerprint sourceへ追加しない。
- base identity、selection、editor revision、notice textをfingerprintへ含めない。

## 9. 詳細ステップ

### Step 1: 実装前再チェック

1. branch、HEAD、worktree、未追跡B5 testを確認する。
2. B5本体の実装diffと全test結果を再確認する。
3. B1 / B2 / B4 / B5計画、本追加計画、current codeを照合する。
4. current automatic handoff、manual end overlap、tail clampのframe例を固定する。
5. findingsをP1 / P2 / P3で分類する。

### Step 2: manual intentとrange helper

1. canonical adjustmentからmanual intentを導出するpure helperを追加する。
2. group tailを決定し、zero-only groupを飛ばして最初の非0 successorを求める。
3. successorが同母音なら停止し、異母音ならtargetとする。
4. targetより後の最初の非0 groupをthird active groupとして求める。
5. target open start / endとmanual crossfade limitを算出する。
6. manual triggerをneutralizeしたcomparison outputを再帰なしで構築する。
7. automatic result、comparison result、manual resultを別stateで保持する。
8. invalid group / range / stale indexをfail closedにする。

### Step 3: end offset validation

1. coreにmanual positive end offset上限を追加する。
2. selected editor stateへdynamic min / maxを渡す。
3. RightPane rangeをstateから設定する。
4. GUI外の範囲外requestをcoreで拒否する。
5. negative / zero offsetの既存動作を維持する。

### Step 4: manual tail crossfade

1. `_build_shapes()` からnext open / third limitをshape生成へ渡す。
2. event別hold / softness overrideだけmanual available extensionを使う。
3. current closeとnext openの非0区間を重ねる。
4. next shape control pointを変更しないことを検証する。
5. third shapeとの非0重複がないことを検証する。

### Step 5: metadataと0.95判定

1. source terminal下降開始point、source end zero、target start zero、target peakから
   inclusiveな整数frame overlapを確定する。`slope_mid`は下降開始候補から除外する。
2. start / end zeroをoverlapから除外する。
3. comparison outputとfinal outputが同じ場合はmanual metadataを生成しない。
4. immediate next non-zero different-vowel targetのcontrol pointだけを調べる。
5. overlap内で値が0.95以上のexplicit pointをmetadataへ記録する。
6. 0.949999、0.95、1.0、1.2の境界testを追加する。
7. 値をclipしていないことをwriter frameで確認する。

### Step 6: editor / RightPane notice

1. selected editor stateへcrossfade notice primitiveを追加する。
2. pure adapterで日本語文を構築する。
3. RightPaneへ専用notice controlを追加する。
4. attention色、header bold、detail normal、wrap / scrollを適用する。
5. B4 limited-effect / operation / slope helperとの同時表示を確認する。

### Step 7: Preview / VMD / fingerprint統合

1. Preview segmentにmanual overlapが現れることを確認する。
2. prepared VMD frameで異母音が同時に非0となることを確認する。
3. Previewとwriterが同じplanを参照することを確認する。
4. effective output変更でfingerprintが変わることを確認する。
5. output-equivalent requested変更でfingerprintが変わらないことを確認する。

### Step 8: failure / lifecycle回帰

1. resetでmanual crossfadeとnoticeが消えることを確認する。
2. selection変更で対象eventのnoticeだけを表示する。
3. cancelで保持planからnoticeを再構築する。
4. analysis failure / input invalidation / workspace resetで消去する。
5. stale edit / late callbackがmetadataやnoticeを変更しないことを確認する。
6. save cancel / writer failure / save successでadjustmentを保持する。

### Step 9: 検証と文書同期

1. 新規core testを実行する。
2. wx notice testを実行する。
3. B2 / B4 / B5関連回帰を実行する。
4. full `pytest tests` を実行する。
5. `git diff --check` と旧文言 / temporary field残存検索を実行する。
6. VMD / Pipeline / GUI正本仕様を限定例外と実装済みcontractへ同期する。
7. ユーザーGUI確認後に本計画とrouting文書へ結果を反映する。

## 10. 状態遷移 / データ契約

### 10.1 intent / output matrix

| adjustment | group tail | next異母音 | manual intent | overlap policy |
| --- | --- | --- | --- | --- |
| なし | 任意 | 任意 | no | 現行automatic policy |
| peakのみ | yes | yes | no | 現行automatic policy |
| startのみ | yes | yes | no | 現行automatic policy |
| slopeのみ | yes | yes | no | 現行automatic policy |
| end offset `<= 0` | yes | yes | no | 現行automatic policy |
| end offset `> 0` | yes | yes | yes | next open内だけ許可 |
| hold override | yes | yes | yes | next open内だけ許可 |
| softness override | yes | yes | yes | next open内だけ許可 |
| tail edit | no | 任意 | invalid | 既存group-tail ERROR |
| tail edit | yes | nextなし | yes / no | 最終shapeの現行tail policy |
| tail edit | yes | same vowel | grouping | 別crossfadeを作らない |
| tail edit | yes | zero-only groupの後に異母音 | yes | zero-onlyを保持したまま次の非0異母音をtargetにする |
| tail edit | yes | zero-only groupの後に同母音 | yes / no | 後続異母音を探索せずmanual crossfadeなし |

### 10.2 notice matrix

| actual overlap | target explicit point | notice | clip | save |
| --- | --- | --- | --- | --- |
| なし | 任意 | なし | なし | 通常どおり |
| あり | `< 0.95` | なし | なし | 通常どおり |
| あり | `== 0.95` | 表示 | なし | 許可 |
| あり | `> 0.95` | 表示 | なし | 許可 |
| automatic overlapのみ | `>= 0.95` | なし | なし | 通常どおり |
| manual intentあり、comparisonとfinalが同一 | `>= 0.95` | なし | なし | 通常どおり |

### 10.3 ownership

| state | owner | fingerprint対象 |
| --- | --- | --- |
| canonical adjustment | `UiState.current_adjustment_snapshot` | 直接は含めない |
| manual intent | resolver導出値 | 直接は含めない |
| crossfade control point | `EffectiveShapePlan` | effective frameとして含む |
| crossfade metadata | `EffectiveShapePlan` | 含めない |
| 0.95 notice text | selected editor adapter | 含めない |
| warning confirmation | 既存diagnostics policy | noticeでは変更しない |

## 11. テスト方針

### 11.1 core単体

- adjustmentなしではmanual crossfadeを生成しない。
- global hold / softnessだけではmanual crossfadeを生成しない。
- peak、start、slopeだけではmanual crossfadeを生成しない。
- positive end offset、hold override、softness overrideでintentを生成する。
- group中間eventのtail overrideは既存どおり拒否する。
- immediate next different vowelだけと重なる。
- zero-only groupをprovenanceへ残しながらtarget検索では飛ばす。
- zero-only groupの後の最初の非0 successorが同母音なら、それ以後の異母音をtargetにしない。
- same vowelは既存groupingへ入る。
- third shapeと重ならない。
- next shapeのstart / peak / end / valueを変更しない。
- automatic handoffだけで成立済みのoverlapをmanual metadataへ記録しない。
- manual triggerをneutralizeしたcomparisonとfinalが同一ならmetadataを生成しない。
- comparisonに存在するautomatic handoff境界をmanual limitで短縮しない。
- end offset上限超過をsilent clampせず拒否する。
- non-tail、targetなし、successor同母音では現行source duration上限を維持する。
- hold / softness requested値とeffective値を分離する。
- automatic handoff metadataとmanual metadataを混同しない。

### 11.2 0.95境界

- overlap内のtarget point `0.949999` ではnoticeなし。
- `0.95` でnoticeあり。
- `1.0` でnoticeあり、値維持。
- `1.2` でnoticeあり、値維持。
- overlap外のtarget pointが0.95以上でもnoticeなし。
- target `start_zero` / source `end_zero` frameをoverlapへ含めない。
- 1 integer frameだけのoverlapを包含境界どおり判定する。
- interpolated値だけが0.95以上でもexplicit pointが未到達ならnoticeなし。
- current morph値や2 morph合計は判定に使用しない。
- automatic overlapだけではnoticeなし。

### 11.3 Preview / writer

- manual crossfade区間で異なる2 morphが同時に非0となる。
- Preview control pointとprepared VMD frameのsource planが一致する。
- final normalization後もtarget 0.95 / 1.0超をclipしない。
- fixed morph以外を生成しない。
- base-only legacy outputは変更しない。
- TEXTあり / voice-onlyの保存結果が同じpolicyを使う。

### 11.4 GUI

- dynamic end offset rangeがnext open / third limitへ追従する。
- non-tail、targetなし、successor同母音のend offset rangeはsource duration上限を維持する。
- edit直後にPreviewとnoticeを更新する。
- 0.95 noticeはオレンジ系、headerだけboldである。
- noticeは非モーダルで、editor操作を妨げない。
- existing limited-effect noticeと独立表示できる。
- selection変更、reset、cancel、workspace resetのlifecycleを満たす。
- Busy中は表示を保持しcontrolだけ無効化する。
- Warning tab、bottom Statusへnoticeを重複表示しない。

### 11.5 diagnostics / state保持

- noticeだけではdiagnostic WARNINGを追加しない。
- noticeだけではsave confirmationを表示しない。
- output変更時はeffective fingerprintが変わる。
- output-equivalent editではfingerprintが変わらない。
- save dialog cancel / failure / successでadjustmentとselectionを保持する。
- report formatを変更しない。

### 11.6 回帰

最小test後、次を順に実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b5_explicit_event_crossfade.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms21_b5_explicit_event_crossfade.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b2_effective_shape_plan.py tests/test_ms21_b4_selected_event_editor.py tests/test_wx_ms21_b4_selected_event_editor.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms21_b5_effective_output_identity.py tests/test_ms21_b5_adjusted_vmd_save.py tests/test_pipeline_and_vmd.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b5_warning_save_policy.py tests/test_ms20_b7_diagnostics_state_integration.py tests/test_ms19_b4_voice_only_gui_state.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
git diff --check
```

test結果はpass表示とprocess exit codeを分けて報告する。

### 11.7 手動GUI確認

1. 自動解析直後に全母音が一律overlapしないこと。
2. peak / start / slopeだけの個別編集でoverlap policyが変わらないこと。
3. positive end offset、hold、softnessの個別編集で直後異母音とcrossfadeすること。
4. Previewで現在母音の閉口と次母音の開口が同時進行すること。
5. VMDをMMDへ読み込み、Previewと同方向の遷移になること。
6. 次母音のoverlap内keyframeを0.94にしてnoticeが出ないこと。
7. 0.95、1.0、1.0超でnoticeが出ること。
8. 1.0超の値がclipされず保存されること。
9. noticeが保存禁止やmodal確認にならないこと。
10. 3つ目の母音へcurrent morphが残らないこと。
11. zero-only中間eventを含むautomatic handoffで、中間eventを保持しながら
    直後の非0異母音だけがmanual targetになること。
12. automatic handoffだけで既に同じoverlapがある場合はmanual noticeが出ないこと。
13. resetでcrossfadeとnoticeが消えること。
14. TEXTあり / voice-onlyの両方で同じ結果になること。

## 12. 受け入れ条件

- 自動解析resultの全母音へ一律crossfadeを追加していない。
- manual intentはpositive end offset、event hold、event softnessだけから導出される。
- peak、start、slopeだけではmanual overlapが有効にならない。
- current group tailとimmediate next non-zero different-vowel groupだけが対象である。
- zero-only groupはデータから削除せず、manual target検索時だけ飛ばす。
- zero-only group後の最初の非0 successorが同母音なら、後続異母音まで飛び越さない。
- current closeとnext openだけが重なる。
- next eventとthird groupを変更しない。
- automatic handoffだけのoverlapをmanual crossfadeとして記録しない。
- automatic handoffの既存境界をmanual crossfade limitで短縮しない。
- manual trigger neutralize後のcomparison outputとfinal outputが同じ場合はnoticeを出さない。
- end offset範囲外をsilent clampしない。
- non-tail、targetなし、successor同母音では現行source duration上限を維持する。
- hold / softness requested値をcanonical snapshotへ保持する。
- actual overlapがないintentをcrossfade成立として表示しない。
- overlap内explicit target pointが0.95以上の場合だけnoticeを表示する。
- 0.95、1.0、1.0超をclipしない。
- noticeは非モーダルで保存を禁止しない。
- noticeをdiagnostics WARNING、Warning tab、reportへ追加しない。
- PreviewとVMDが同じeffective planを使用する。
- effective output変更がB5 fingerprintへ反映される。
- output-equivalent editではfingerprintを維持する。
- fixed morph、30fps、VMD binary契約を変更しない。
- 新規限定test、関連回帰、full testがpass表示かつprocess exit code 0である。
- `git diff --check` がprocess exit code 0である。
- VMD / Pipeline / GUI正本仕様がmanual crossfade限定例外と実装状態へ同期されている。
- ユーザーGUI確認結果を文書へ反映するまでcloseoutとしない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 単なるpeak編集で出力shapeが変わる | intent triggerをend拡大、hold、softnessへ限定する |
| global設定だけで全母音がoverlapする | event別canonical overrideを必須にする |
| current tailが3つ目へ漏れる | next open endとthird startで上限を固定する |
| next eventを暗黙移動する | next shape DTOを不変とするtestを置く |
| end offsetをsilent clampする | dynamic GUI rangeとcore rejectを併用する |
| requested tail値が失われる | canonical requestedとeffective反映を分離する |
| automatic handoffとmanual intentが混ざる | metadataとtriggerを別契約にする |
| automatic handoff済みoutputをmanual効果と誤認する | manual triggerをneutralizeしたcomparison outputとの差分を必須にする |
| zero-only中間groupをtargetにして次の非0母音へ届かない | zero-onlyを保持したままtarget検索時だけ飛ばす |
| zero-onlyの後に同母音があるのに離れた異母音まで飛び越す | 最初の非0 successorが同母音なら探索を停止する |
| start / end zeroを非0 overlapへ含める | `start_zero + 1` と `end_zero - 1` で整数frame境界を固定する |
| 0.95 noticeで値がclipされる | notice-only、writer frame値維持testを置く |
| 補間値まで判定して仕様が複雑化する | explicit control pointだけを判定する |
| noticeが保存WARNINGへ昇格する | DiagnosticItemを追加せず専用editor noticeに限定する |
| Previewだけoverlapする | B5 effective planからPreview / writer両adapterをtestする |
| writer normalizationが高い値を変える | prepared frameとbinary recordの値回帰を追加する |
| notice textがfingerprintを変える | metadata / textをpayloadへ含めない |
| B5未コミット変更を上書きする | implementation前にdiffを読み、同一箇所を統合編集する |
| 実装後も正本仕様が後続shape直前clampだけを要求する | VMD / Pipeline / GUI仕様を本補正と同時に同期する |

## 14. Codex 実装時の注意

- 本計画は文書作成時点でコード実装を許可しない。
- implementation開始の明示指示後にproduction code / testを変更する。
- B5本体のcurrent uncommitted changesとuntracked testを保護する。
- current codeから再導出し、古いB4の「overlap禁止」だけを絶対条件にしない。
- manual crossfadeとautomatic cross-vowel handoffを同一処理へ潰さない。
- GUIでframe補間やkeyframe列を再構築しない。
- core resolverからwriter private helperをimportしない。
- noticeのためにmorph値をclip、reject、roundしない。
- 0.95判定を合計値や補間値へ無断拡張しない。
- noticeをERROR、diagnostics WARNING、modal dialogへ変更しない。
- next eventやthird eventを自動移動しない。
- fixed morph `あ / い / う / え / お` を変更しない。
- wxPython主系を維持し、Qt / PySide6を復活させない。
- network、cloud、外部送信、background通信を追加しない。
- dependency、package、release、tag、pushを行わない。
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
