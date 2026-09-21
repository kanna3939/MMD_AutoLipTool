# MS28-B1 Implementation Plan

## 1. 文書情報

- 対象Block: `MS28-B1`
- 名称: Long-Vowel Successor Boundary / Generation Settings Repair
- 作成日: 2026-09-19
- 対象branch: `feature/MS28-B1-implementation`（ユーザー指定）
- MS28位置づけ: MS20〜MS27の全体マイルストーン系列とは切り離した、Ver.1実装後の独立修正実装トラック
- 基準HEAD: `0bb85a96e2fdca3b4a382f607ad53f6260570148`
- 文書状態: **Implemented / Automated Verification Recorded / GUI and Distribution Verification Pending**
- 種別: Ver1実装後に報告されたPreview非表示・生成設定反映失敗に対する限定修正計画
- 関連契約: MS21 shared resolver / event adjustment / tail effect notice / manual crossfade、
  MS22 long-vowel resolver / generation state / output history
- 次工程: B1の実装結果を維持し、後続の長音境界契約はMS28-B2で扱う。GUI・実入力・実MMD・EXE・buildの確認は別途の検証範囲とする。

本書は、前回提示したMS28-B1計画を、現行code、test、MS21 / MS22関連計画へ照合して保存したものである。
MS28-B1の実装対象はproduction code / test codeの限定変更であり、設定、runtime data、README、AGENTS.mdは変更しない。
MS27完了・MS28独立トラックのrouting状態は、別途status文書へ同期済みであり、これは本修正実装の開始やscope拡張を意味しない。
stage、commit、push、branch操作を行わない。

## 2. 背景

### 2.1 報告された症状

- TEXT + 音声を読み込み、解析しても母音タイムラインが表示されない。
- 音声のみを読み込み、解析した後、開口保持 / 閉口スムーズ等を操作しても値が0へ戻る。

前回調査では非ゼロtail設定によるrequired-zero conflictが報告された。本書ではその件数や特定frameを
新しい実測結果として転記せず、現行実装の因果経路と、再発防止に必要な再現条件を固定する。

### 2.2 主因と症状の対応

主因は、`src/core/effective_shape_plan.py`の通常group後続探索が長音sourceを除外し、非ゼロの
hold / softnessの延長先として後続長音を認識できないことである。

`resolve_effective_shape_plan()`は長音sourceとcontinuationのindexを`long_indices`へ集め、
`_build_shapes()`へ`excluded_indices`として渡す。`_build_shapes()`はそれらを除いた
`filtered_events`から通常groupを作り、次の通常groupだけから`next_shape_start_frame`を求める。
長音memberを通常groupingから除くことは正しいが、後続形状の境界まで除外することは別問題である。

このため、通常母音の直後が長音の場合、通常shapeのhold / softnessが長音へ入り込む。
同一モーフ・同一frameでrequired zeroと別shapeのpositive control pointまたはevent peakが衝突すると、
`_validate_required_zero_conflicts()`が`AdjustmentContractError`を送出する。

| 段階 | 現行処理 | 症状との対応 |
| --- | --- | --- |
| shape生成 | 後続探索が長音sourceを見落とし、tailを過剰延長 | 有効な設定変更から人工的な衝突を作る |
| resolver検証 | required zero / positive競合をfail closedで拒否 | 不整合なPreview / Writer出力を防止する |
| 解析後のUI同期 | `_build_current_ui_sync_context()`が失敗理由を保持し、Contextを返さない | `_update_preview_display()`が形状生成失敗のplaceholderを表示する |
| 設定変更 | `commit_generation_settings()`が候補resolve失敗時に`_project_generation_controls()`を呼ぶ | 変更前のcanonical設定が入力欄へ再投影される |

旧値再投影は「必ず0へ設定する処理」ではない。変更前の確定設定が0の場合に0へ戻る。
fail-closedと旧値復帰は保護処理として維持し、その前段で正当な設定を拒否させる境界計算を修正する。

長音側の後続探索も`long_indices`全体を除外しているため、長音runが連続する場合に次runのsourceを
見落とす。これは同じ欠落の関連確認・修正対象とし、独立した再現fixtureで挙動を固定する。

### 2.3 現行code / test / 文書の根拠

行番号は基準HEADでの参照目安であり、実装時は関数名・test名を正本にする。

| 根拠 | 現行箇所 | 確認内容 |
| --- | --- | --- |
| E01 | `src/core/effective_shape_plan.py` `_build_shapes()`（988行付近） | `filtered_events`による長音除外と、次通常groupだけを見る後続探索 |
| E02 | 同ファイル `_shape_for_group()`（752行付近） | next startによる延長上限、hold優先、softness残余割当、requested / effective metadata |
| E03 | 同ファイル `resolve_effective_shape_plan()`（1464行付近） | 長音run生成、長音側後続探索の除外、通常 / comparison経路のshape構築 |
| E04 | 同ファイル `_validate_required_zero_conflicts()`（1434行付近） | 同一モーフ・同一frameの別shape間衝突を拒否 |
| E05 | `src/gui_wx/main_frame.py` `_build_current_ui_sync_context()` / `_update_preview_display()` | resolver失敗とPreview placeholderの接続 |
| E06 | 同ファイル `commit_generation_settings()` / `_project_generation_controls()` | 候補resolve失敗時の旧設定復帰、成功時のoutput history commit |
| E07 | `src/gui_wx/analysis_worker.py` `AnalysisWorker.run()` | TEXT + 音声と音声のみの双方が`build_vowel_timing_plan()`を使用 |
| E08 | `tests/test_ms22_b2_long_vowel_resolver.py` `test_pipeline_repairs_regular_same_vowel_before_long_source` / `test_pipeline_repairs_consecutive_same_vowel_long_runs_for_preview` | 既存境界補修をhold / decayで確認するが、hold / softnessは既定値 |
| E09 | `tests/test_ms21_b4_selected_event_editor.py` global / event overrideの制限notice test | requestedを保持したままeffectiveを制限する既存期待値 |
| E10 | `tests/test_wx_ms22_b4_generation_state.py` `test_output_only_generation_edit_preserves_analysis_and_is_undoable` | generation変更時のbase保持とUndo契約 |
| E11 | `docs/Implementation_Plan/MS22-B2_Implementation_Plan.md` §8.3〜8.6 | 長音の隔離、hold / decay、exact zero、所有権、fail-closed |
| E12 | `docs/Implementation_Plan/MS21-B4_Tail_Effect_Notice_Temporary_Fix_Plan.md` §8.3〜8.6 | requested / effective表示、制限notice、配分順序 |
| E13 | `docs/Implementation_Plan/MS22-B4_Implementation_Plan.md` §11.6 | 過去のRMS後境界衝突補修。今回の非ゼロtail設定の検証済み証拠とは区別する |

既存testの境界補修成功だけでは、非ゼロtailによる再衝突を防げない。再発防止では同じ配置に
global設定・event overrideを組み合わせ、shape生成からUI commitまで検証する。

保持0 / スムーズ0でもPreviewが表示されない場合は、今回の主因で説明できたとみなさない。
別原因として未解決扱いにし、§6.2の情報で切り分ける。

## 3. 目的

- 長音の通常groupingからの分離を維持し、後続形状の境界として長音sourceを認識する。
- 正当な非ゼロhold / softness設定が人工的なrequired-zero conflictで拒否される問題を解消する。
- TEXT + 音声 / 音声のみの双方で、修正対象の解析結果をPreviewへ同期できるようにする。
- global設定とevent overrideのrequested値を保持し、空き区間に応じたeffective制限を維持する。
- Preview、Writer、selected editor、diagnosticsが同じEffectiveShapePlanを使用する契約を維持する。
- output-only編集、Undo / Redo、長音hold / decay、fail-closedの回帰を防ぐ。

## 4. In Scope

- 通常母音groupから後続長音sourceへの境界探索とtail延長制限
- 長音runから後続長音runへの境界探索とtail延長制限
- 通常 → 長音、長音 → 通常、長音 → 長音、通常 → 長音 → 通常の配置
- global hold / softnessと通常group末尾 / 長音terminalのevent override
- effective eventのstart / end offsetを反映した後続境界
- 通常解決とmanual comparison解決の境界規則の整合
- automatic handoff、synthetic shape再生成、manual crossfadeの後段処理に対する関連回帰確認
- 解析成功後のPreview同期、解析前 / 解析後の非ゼロgeneration設定、旧値再投影との対応確認
- requested / effective表示、制限notice、Undo / Redo、Preview / Writer整合
- 主因に近いcore回帰、wx統合回帰、実入力・Windows GUI確認

## 5. Out of Scope

- Whisper認識方式、長音推定、RMS分析、timeline自動補修の広範な変更
- resolverエラーを無視してPreview / VMDを生成する処理
- required zeroの削除、positiveへの置換、衝突のsilent merge、fail-closed緩和
- resolver内でbase peakやterminalを移動して衝突を隠す処理
- requested値をeffective値で上書きする処理、反映量0だけを理由としたoverride削除
- モデルプロファイルのglobal編集ロック解除
- GUI全面変更、新しい診断画面、通知基盤、汎用history framework
- identity / persistence schema、dependency、package、license、VMD形式、30fps契約の変更
- runtime dataの直接編集、旧Qt / PySide6、network、Whisper自動download
- B1修正実装に伴うREADME、Index、AGENTS.md、他計画・状態文書の変更（MS27完了・MS28独立トラックの別途status同期を除く）
- stage、commit、push、merge、branch操作、release作業
- 保持0 / スムーズ0でも生じる別原因のPreview非表示に対する、原因未確認の修正

## 6. 前提条件

### 6.1 実装開始条件

- 本書保存と修正実装を区別し、実装依頼の範囲を確認する。
- 実装開始時に対象branch、HEAD、作業ツリーをread-onlyで確認し、既存変更を保護する。
- `GenerationSettings`のhold / softness `0..100`、long mode `hold | decay`を再利用する。
- ローカル`.venv`と既存Windows / wx環境を使用し、本修正のための新規依存を追加しない。
- GUI / persistence testは一時領域のstoreを使用する。実INI / JSON、preset / profileを直接変更しない。
- 実Whisper確認は既存の検証済みローカルモデルで行い、モデル未準備なら未実施理由を記録する。
- 過去文書のpass件数・実入力frame・ユーザー確認を今回の検証結果として再利用しない。

### 6.2 未確定事項と実装前の確認

| 未確定事項 | 確認する証拠 / 扱い |
| --- | --- |
| TEXT + 音声のPreview非表示時の設定 | hold / softness / long mode、解析前後どちらで設定したかを確認する |
| 保持0 / スムーズ0でも発生するか | 発生する場合は別原因として未解決扱いにし、本修正だけで解消済みとしない |
| 実際の同期失敗理由 | `_current_ui_sync_failure_reason`、timeline件数、音声duration、model identityを確認する |
| 0へ戻る対象 | global入力、選択イベント入力、effective表示を区別し、変更前canonical値とcommit結果を確認する |
| profile lockの関与 | active model profileの有無を確認し、正当な編集禁止と区別する |
| offset後の後続順序 | peak / base index順とstart frame順が異なる配置を確認し、単純なstart順sortで意味を変えない |
| synthetic / manual後段の再延長 | 長音境界を再び越えるfixtureがあるか確認する。別の欠陥なら再現・変更範囲を明示してから限定対処する |
| 実入力との対応 | sampleと発生入力が同一かは未確認。fixture再現と実Whisper / ネイティブGUI再現を分けて記録する |

## 7. 対象ファイル

### 7.1 主変更候補

| ファイル | B1で担当する責務 |
| --- | --- |
| `src/core/effective_shape_plan.py` | 長音sourceを後続境界へ含める。既存tail計算、所有権、fail-closedを維持する |

最小案ではproduction codeの変更を上記1ファイルへ限定する。公開DTOや新しい永続状態を追加しない。

### 7.2 関連確認対象

| ファイル | 確認内容 |
| --- | --- |
| `src/core/pipeline.py` | 既存の同一モーフ境界補修との責務分離。今回のtail設定をpipelineへ混入させない |
| `src/core/event_adjustment.py` | 明示override、canonical snapshot、no-opの契約 |
| `src/core/model_profile_state.py` | active profileによる正当なglobal編集拒否 |
| `src/gui_wx/analysis_worker.py` | TEXT + 音声 / 音声のみが共通pipelineへ到達する経路 |
| `src/gui_wx/main_frame.py` | 解析成功、Preview同期、設定commit、event編集、旧値復帰、Undo / Redo |
| `src/gui_wx/ui_sync_context.py` | 同じeffective planの共有、identity / snapshot / parameter hint整合性 |
| `src/gui_wx/selected_event_editor.py` | requested / effective、制限notice、decay潜在値の表示 |
| `src/gui_wx/right_pane.py` | 入力値とeffective表示の区別、projection guard |
| `src/core/preview_transform.py` | shared planのPreview変換 |
| `src/vmd_writer/effective_shape_adapter.py` | shared planのWriter変換、required zeroの保持 |

関連確認対象は一律に編集しない。独立した欠陥を再現した場合だけ、必要な変更候補を明示する。

### 7.3 test対象

以下は実在する既存testである。core / GUIの新しい再現条件は責務が近い既存ファイルへ追加する方針とし、
新規testファイルが必要な場合は追加時に名称と役割を明記する。

| ファイル | 追加・回帰の観点 |
| --- | --- |
| `tests/test_ms22_b2_long_vowel_resolver.py` | 通常 → 長音 / 長音 → 長音の非ゼロtail、hold / decay、所有権、衝突拒否 |
| `tests/test_ms22_b2_long_vowel_adapters.py` | Preview / Writerの同一control point、exact zero |
| `tests/test_ms21_b2_effective_shape_plan.py` | 通常group、handoff、最終tail、base保持 |
| `tests/test_ms21_b5_explicit_event_crossfade.py` | global / manual intentの分離、後段延長、長音の隔離 |
| `tests/test_ms21_b4_selected_event_editor.py` | global / overrideのrequested保持、effective制限、notice、slope cleanup |
| `tests/test_wx_ms22_b5_long_vowel_override.py` | terminal override、decay潜在値、hold復帰、stale拒否 |
| `tests/test_wx_ms22_b4_generation_state.py` | 非ゼロ設定commit、旧値復帰、base保持、Undo / Redo |
| `tests/test_ms22_b4_generation_history.py` | generation / adjustmentのatomic history |
| `tests/test_wx_ms22_b6_lifecycle_regression.py` | 両入力モードの成功callback、出力状態、Preview |
| `tests/test_ms20_b3_right_pane_info.py` | 解析後Preview、duration不足とshape失敗の区別 |
| `tests/test_ms19_b4_analysis_worker_voice_only.py` | 音声のみの認識結果再利用と共通pipeline呼出し |
| `tests/test_ms21_b7_ui_sync_context.py` | shared context、hint整合性 |
| `tests/test_ms21_b5_effective_output_identity.py` | 実効出力変更とfingerprintの関係 |
| `tests/test_vmd_writer_zero_guard.py` | 最終正規化後のzero保護 |

### 7.4 文書対象・参照

修正実装計画の成果物は本書だけとする。MS27完了・MS28独立トラックのstatus同期はrouting文書側で別管理する。
次の実在文書を参照し、過去の実装前記述や完了記録を現行codeと照合する。

- `docs/Implementation_Plan/MS21-B4_Tail_Effect_Notice_Temporary_Fix_Plan.md`
- `docs/Implementation_Plan/MS21-B5_Explicit_Event_Crossfade_Additional_Fix_Plan.md`
- `docs/Implementation_Plan/MS22-B2_Implementation_Plan.md`
- `docs/Implementation_Plan/MS22-B4_Implementation_Plan.md`
- `docs/Pipeline_Data_Contract_Specification.md` §21.7
- `docs/GUI_State_Theme_Specification.md` shared context / generation state契約

## 8. 実装方針

### 8.1 grouping対象と後続境界候補の分離

- 長音source / continuationを通常groupingへ戻さない。
- 通常groupの後続探索では、従来の次通常groupに加え、その手前の長音sourceを考慮する。
- 長音側では後続runのsourceを境界候補に含め、continuationを独立した次shapeとして数えない。
- adjustmentと有効なhandoffを反映したeffective eventのstartを使い、source start overrideを無視しない。
- 既存event / group順序に長音sourceを対応付ける。開始frameだけで全eventを再sortする変更はしない。
- 後続通常groupより先にある長音を飛び越したり、run内部のcontinuationで自分自身を制限したりしない。
- 必要なら同一moduleのprivate helperへ限定共通化する。新しい公開DTOや汎用shape graphを導入しない。

### 8.2 tail配分と例外条件の維持

通常shapeは、正しい後続startを既存計算へ渡す。

```text
available = max(0, next_start - 1 - current_end)
effective_hold = min(requested_hold, available)
effective_softness = min(requested_softness, available - effective_hold)
```

これは追加tailの制限であり、元のbase区間を短縮する式ではない。base由来の真の衝突は引き続き拒否する。
requestedはcanonical値として保持し、effectiveが0でも自動削除しない。

長音holdはterminal plateauの後にclosing zeroを持つ。requested 0 / 0でも原則terminal end + 1へzeroを
置く既存規則を維持する。この最小edgeを通常shapeの配分式だけで消さず、次の同母音shapeのstart zeroと
同一frameになる現行の許容条件も維持する。両立不能な入力はfail closedとする。

長音decayはsource peakからterminal endのexact `0.0`へ単一線形segmentを作る。tail / slopeはlatentに
保持し、effective hold / softnessは0のままとする。最終shapeのclosing tailがsource durationを超え得る
既存契約を一律のduration clampへ置き換えない。

### 8.3 comparison / handoff / manual crossfade

- `_build_shapes()`の通常解決とmanual comparison解決に同じ後続境界規則を適用する。
- 長音に触れるautomatic handoffの無効化と、通常groupのprovenanceを維持する。
- synthetic shapeの再生成箇所にある`next_shape_start_frame=None`を確認し、今回の配置で長音境界が
  失われる場合だけ同じ境界規則へ接続する。長音なしのsynthetic semanticsを無条件に変えない。
- 長音shapeをmanual crossfadeのsource / targetへ新規参加させない。
- manual後段が補正した境界を再び越える場合は、衝突するfixtureと責務を確認する。
  本修正を理由にmanual intent、zero-only探索、第三shape制限の全体仕様を変更しない。

### 8.4 UI / Preview / Writerへの適用

最小案ではMainFrameの成功・失敗transactionや描画fallbackを変更しない。
resolverが有効な候補を解決できれば、既存commit経路がrequested値を保存し、既存shared contextが
Preview / editor / diagnosticsへ同じplanを投影する。Writerも同じplanを消費する。

`_project_generation_controls()`の削除、commitの無条件成功化、失敗時の旧Preview流用によって症状を
隠さない。GUI独自のtail計算やWriterだけの衝突補正を追加しない。

## 9. 詳細ステップ

### Step 1: 開始条件と再現情報の確認

- §6を確認し、実装対象branch / HEAD / 既存変更を照合する。
- 発生時の入力モード、設定、profile、duration、同期失敗理由を可能な範囲で取得する。
- 保持0 / スムーズ0の別原因は独立した未解決事項として記録する。

### Step 2: 最小失敗fixtureの固定

- 実音声・Whisperに依存しない明示長音metadata付きtimelineを作る。
- 通常eventのend=6、後続長音sourceのstart=6 / peak=7とし、保持1またはスムーズ1で旧実装の
  衝突を確認する。その他のframe / duration / valueは入力契約を満たすよう明示する。
- このframe例は新設するtest設計であり、過去の実入力ログとして記載しない。
- 長音 → 長音にも非ゼロtailの独立fixtureを置き、次run sourceを見落とす失敗を確認する。
- 十分な間隔がある対照fixtureを作り、修正が単にすべてのtailを0にする処理でないことを検証する。

### Step 3: 後続探索の限定修正

- 通常groupと長音runの生成責務を分離したまま、長音sourceを後続境界へ含める。
- effective start、通常 / comparison経路、run内部continuation除外を確認する。
- `_shape_for_group()` / `_shape_for_long_run()`の既存配分・closing規則へ境界を渡す。

### Step 4: overrideと後段処理の照合

- global / event override、source start / terminal end offsetで同じ規則が使われることを確認する。
- requested保持、effective制限、slope cleanup、decay潜在値を確認する。
- handoff、synthetic、manual crossfadeによる再延長を検証し、再現のない周辺変更は追加しない。

### Step 5: UI / 出力統合の確認

- TEXT + 音声 / 音声のみの解析成功callbackで対象planを同期する。
- 解析前の非ゼロ設定、解析後のglobal変更、選択イベント編集を確認する。
- Preview有効性、requested入力値、effective表示、history、Undo / Redo、Writerを照合する。
- 真の不正入力とprofile lockでは既存の拒否・旧値復帰が残ることを確認する。

### Step 6: 回帰・手動確認と報告

- coreから関連統合へ順に検証し、共有resolver変更の最終回帰として全suiteを1回実行する。
- §11の実入力・Windows GUI確認を実施し、自動testと分けて記録する。
- 変更範囲、process exit code、未実施事項、別原因の残件を報告する。

## 10. 状態遷移 / データ契約

| 操作 / 結果 | 維持する状態 |
| --- | --- |
| 解析成功 + resolve成功 | timing planを保持し、同じEffectiveShapePlanでPreview / editor / diagnosticsを同期 |
| global設定変更成功 | baseを再解析せず、generation stateとoutput historyをatomicに確定 |
| event override成功 | requested snapshotを保持し、effective値とnoticeを再計算 |
| 空き不足によるclamp | requested非ゼロを保持したままeffective=0を許容。入力欄をeffectiveで上書きしない |
| 真の不正入力 / 衝突 | fail closed。既存canonical設定 / snapshot / historyを保持し、候補を成功扱いしない |
| Undo / Redo | generationとadjustmentを一体で復元し、同じresolverで再解決 |
| decay → hold | latent tailを保持したまま、hold復帰時に現在の境界で再配分 |

- hold / softness / long modeはoutput-only。morph upper limitのanalysis-affecting契約を変えない。
- 明示hold / softness / mode overrideはglobalと同値でも保持する。
- sourceはpeak / start、terminalはend / tail / modeを所有し、中間continuationへ編集権を追加しない。
- `apply_adjustment_update()`の既存slope cleanupと、直接resolverへ不正slopeを渡した場合の拒否を区別する。
- real event index、長音metadata、synthetic provenance、base identity / snapshot schemaを維持する。
- UI同期は同一Contextを共有し、identity / snapshot / shape parameterが不一致のhintを再利用しない。
- 修正でeffective出力が変わる場合は既存規則でfingerprintが変わる。requestedだけが変わり出力が
  同じ場合に、noticeやrequested値を新たにfingerprintへ混入させない。設定履歴と出力同一性は区別する。

## 11. テスト方針

### 11.1 core再発防止matrix

| 軸 | 必須条件 |
| --- | --- |
| 配置 | 通常 → 長音、長音 → 通常、長音 → 長音、通常 → 長音 → 通常 |
| 母音 / mode | 同母音・異母音、hold・decay、単一・複数continuation |
| tail | 0 / 0、保持のみ、スムーズのみ、両方。1frameと上限100を含む |
| 空き | 空きなし、1frame、十分な空き、最終shape |
| 設定元 | global、通常group末尾override、長音terminal override |
| offset | 後続source start変更、terminal end変更、既存範囲内と拒否すべき範囲 |
| 既存経路 | 長音なし、automatic handoff、synthetic shape、manual comparison / crossfade |

成功 / 例外の有無だけでなく、control point、requested / effective、available extension、source index、
required zero、変更前base不変をassertする。空きが十分なfixtureではhold / softnessの非ゼロ効果を確認し、
空きなしではrequested保持とeffective制限を確認する。

### 11.2 fail-closed回帰

- 同一モーフ・同一frameの真のrequired zero / positive競合を引き続き拒否する。
- 別モーフの同一frame値を、同一モーフ衝突として一律拒否しない。
- 不正frame順序、stale identity、長音所有権違反、partial metadataを引き続き拒否する。
- 長音holdの最小closing edge、decay exact zero、最終tailの既存duration超過条件を確認する。
- midpointのない直接slope overrideは拒否し、update経路の既存cleanupは維持する。
- 拒否時にgeneration state / adjustment / history / 保存済みruntime dataを変更しない。

### 11.3 GUI / Worker / history回帰

- 両入力モードで有効な`AnalysisWorkerResult`からcallbackを通し、Preview valid、segmentsあり、
  sync failureなしを確認する。model / job identity guardを迂回するfixtureにしない。
- 解析前の非ゼロ設定と解析後の設定変更を双方確認する。
- global入力値とcanonical設定が一致し、shapeのeffective=0だけを理由に入力値が旧値へ戻らない。
- 選択イベントではrequested / effectiveとnoticeを別々にassertする。
- global変更とevent overrideが適切なhistory transactionを作り、Undo / Redoで設定・Previewが整合する。
- 真のresolver失敗では変更前の非ゼロ設定も正しく復元されることを確認し、「0へ戻す実装」にしない。
- profile lock、Busy、stale edit / callbackの既存拒否を維持する。
- voice-only Worker testはpipelineをmockしているため、それ単独を実形状解決の検証としない。
  core resolverの決定的fixtureと、両モードのcallback統合で役割を補完する。

### 11.4 Preview / Writer整合

- 同じEffectiveShapePlanのPreview control pointと、最終正規化前のWriter control pointを照合する。
- 最終正規化後は、全点の単純一致ではなくrequired zero / 非0許容区間 / provenance等の契約を確認する。
- 長音hold / decay、clampされた通常tail、override後、Undo / Redo後を対象にする。
- effective出力が変わる場合と、requestedだけが変わる場合のidentity期待値を区別する。

### 11.5 実入力・Windows GUI確認

実在する入力候補は`sample/sample_input2.txt`、`sample/sample_input2.wav`、`sample/sample_voice.wav`とする。
発生入力との同一性は別途確認する。音声のみでは認識テキストに明示長音が含まれるかも記録し、
音響や同音母音だけから長音runがあると推定しない。

1. TEXT + 音声、音声のみの双方で解析し、設定・同期失敗理由・Preview表示を記録する。
2. 0 / 0と非ゼロ設定を分け、解析前設定と解析後変更を確認する。
3. 上部global設定と選択イベント設定について、SpinCtrl矢印、数値入力、フォーカス移動を確認する。
4. requested値、effective値、制限notice、Undo / Redo、Preview更新を確認する。
5. 実Writer出力確認は一時出力先で行い、既存VMD / WAVを上書きしない。

programmatic handler呼出しだけをネイティブ操作確認としない。実MMDでの見た目確認は自動testと区別し、
実施した場合だけ記録する。パッケージ定義を変更しないため、配布再ビルドは本修正の必須検証にしない。

### 11.6 実行順序と終了条件

- 最初に長音resolver回帰を実行し、次に通常resolver / editor / adapter / crossfadeへ広げる。
- 続いてwx generation / lifecycle / Preview / history / shared contextを検証する。
- 共有resolver変更の最終回帰として、全suiteを1回実行する。
- コマンドは1つずつ実行し、pass表示だけでなくprocess exit codeを記録する。
- 例: `.\.venv\Scripts\python.exe -m pytest tests/test_ms22_b2_long_vowel_resolver.py`
- 全体回帰の例: `.\.venv\Scripts\python.exe -m pytest tests`
- 成功済みtestの再実行は、新しい変更・失敗・未解決リスクがある場合に限る。
- 手動確認や実モデル確認が未実施なら理由を残し、fixture成功を利用者症状全体の解消へ拡張しない。

本書保存時にはtestを実行しない。上記は修正実装後の検証計画である。

## 12. 受け入れ条件

- [ ] AC01: 通常groupの後続境界が長音sourceを認識し、非ゼロtailが誤って侵入しない。
- [ ] AC02: 長音runが次runのsourceを認識し、continuationを独立した後続shapeとして扱わない。
- [ ] AC03: global / event overrideの有効な非ゼロrequestedがcommitされ、旧値へ戻らない。
- [ ] AC04: 十分な空きでは非ゼロ効果が生じ、空き不足ではrequestedを保持したままeffectiveだけを制限する。
- [ ] AC05: TEXT + 音声 / 音声のみの対象fixtureで解析後Previewが有効になり、必要なsegmentsを持つ。
- [ ] AC06: output-only変更でbase / analysis結果 / 明示overrideが消失せず、Undo / Redoが整合する。
- [ ] AC07: 長音hold plateau、最小closing edge、decay exact zero、latent tail、所有権を維持する。
- [ ] AC08: 真のrequired-zero競合と不正入力を引き続きfail closedで拒否し、失敗時stateを保護する。
- [ ] AC09: 長音なし、handoff、synthetic、manual crossfadeに意図しない意味変更がない。
- [ ] AC10: Preview / Writer共通resolverを維持し、最終正規化とeffective output identityが整合する。
- [ ] AC11: 関連回帰と全suiteのprocess exit codeを確認し、GUI・実入力の実施範囲を記録する。
- [ ] AC12: 保持0 / スムーズ0でもPreview非表示が残る場合は別原因の未解決事項として報告し、
  今回の原因だけですべて解消したと宣言しない。

### B1実装後の状態（2026-09-19）

- B1のproduction code / test codeの限定変更は実装済みであり、B1の変更を維持したままMS28-B2へ移行した。
- B2では、B1で未捕捉だった隣接long sourceのpeak境界、同一frame handoff、R06/R07/R13/R14の回帰条件を追加実装した。現在の受け入れ判定は、更新済みの`MS28-B2_Implementation_Plan.md` §12を正本とする。
- B2 resolverは**39 passed**、pipeline / Previewは**4 passed**、adapter・specは**9 passed・21 subtests**、全suiteは**1100 passed、4 skipped、88 subtests、process exit code 0**である。`git diff --check`もprocess exit code `0`だった。
- 実Whisperによるユーザー提供ファイルの再解析、native GUI、実MMD、EXE、buildは未実施・未検証である。保持0 / スムーズ0、別のPreview失敗、EXE固有問題はB2計画のAC12に従って分離する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 長音memberを通常groupへ戻して所有権・形状を変える | grouping対象と後続境界候補を分離する |
| continuationを後続として自runをclampする | 長音runにつきsourceだけを独立境界候補にする |
| offset適用前の位置を見る | effective eventのstartを使用する |
| start順sortで後続関係を変える | 既存event / group順序を照合し、offset配置の回帰を固定する |
| comparison経路だけ旧計算が残る | `_build_shapes()`の全呼出箇所を確認する |
| synthetic / manual後段が境界を越える | 独立fixtureで確認し、再現した責務にだけ限定対処する |
| effective=0を設定保存失敗と誤認する | requested保存、effective制限、notice、十分な空きでの実効果を別々に検証する |
| 長音holdの最小edgeやdecay終端を壊す | 0 / 0、次startとの一致、最終shape、hold / decay切替を固定testにする |
| fail-closedを弱めてPreviewだけ表示する | 真の衝突拒否と旧値復帰をnegative testで維持する |
| 別原因のPreview非表示を解消済みとする | 0 / 0、duration、identity、profile、同期失敗理由を切り分ける |
| 実runtime dataを検証で変更する | temporary store / output pathを使用し、永続化の副作用を隔離する |

## 14. Codex 実装時の注意

- 最初のproduction修正案は`src/core/effective_shape_plan.py`に限定し、失敗fixtureを先に固定する。
- `_validate_required_zero_conflicts()`を無効化しない。例外の握り潰しを成功へ変換しない。
- `commit_generation_settings()`を無条件成功にせず、旧値再投影を削除しない。
- base時刻、認識テキスト、source / terminal provenanceを変更して再現を消さない。
- 既存testの削除、skip追加、期待値弱化によって通過させない。
- code / test修正が必要な範囲と、閲覧だけの関連確認対象を分けて報告する。
- 依存、配布、schema変更を本修正へ混在させない。実INI / JSONを直接編集・copy・stageしない。
- 自動検証、programmatic wx、ネイティブGUI、ユーザー実MMD確認を区別し、未実施を完了扱いしない。
- 実装報告では変更ファイル、再現条件、修正内容、test結果と終了コード、仕様逸脱、未解決事項を示す。
- 本書の計画保存時点ではコード実装・Git変更・次Blockへの自動移行を行わない。実装後の到達状態とB2への移行は、上記「B1実装後の状態」および関連status文書へ記録する。
