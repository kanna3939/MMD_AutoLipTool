# MS22-B2 Implementation Plan

## 1. 文書情報

- 対象Block: `MS22-B2`
- 名称: Long-Vowel Data Contract / Shared Resolver / Same-Vowel Audit
- 作成日: 2026-08-01
- 基準branch: `feature/MS21-implementation`
- 基準HEAD: `01a836a Complete MS22-B1 contract fixed`
- 文書状態: **Implemented / Code Check Passed / No P1-P3 (2026-08-06)**
- 直接依存: MS22-B1 Completed / Contract Fixed、MS21 Closeout A
- 次工程: MS22-B3 Implementation Plan策定。B2の実MMD確認はMS26へ維持する

本書はMS22-B1で固定した長音契約を、現行codeとtestへ実装可能な単位で割り当てる計画書である。
本書作成時点ではproduction code、test code、GUI、INI、JSON、dependency、build設定を変更しない。

## 2. 背景

B2実装前の`hiragana_to_vowel_sequence()`は`ー`を直前母音の複製として`list[str]`へ展開するため、
timeline以降では通常の同音母音と明示長音continuationを区別できなかった。MS21時点の
`EffectiveShapePlan`もsame-vowel candidate、grouping、manual crossfadeを共通resolverで処理するが、
長音run専用のsource / continuation / terminal provenanceと`hold / decay`を持たなかった。
B2実装後は、`VowelToken`、timeline metadata、shared resolverがこの区別と`hold / decay`を担う。

MS22-B1は、正規化済み読み列に実在する`ー`だけを長音markerとし、同音母音や音響から長音を
推測しない契約を固定した。また、ユーザー判断として`decay`はsource peakから長音区間終端の
exact `0.0`まで単一線形segmentとする。B2はこの契約をUI非依存coreへ実装し、Previewとwriterが
同じeffective planを消費できる状態までを所有する。

現行の通常shapeはtail値が0の場合にevent endをzero control pointにする。一方、長音`hold`は
terminal endまでpeakを維持し、その後にだけclosing edgeを置く必要がある。この差は長音shape固有の
resolverで扱い、通常shapeの既存tail、grouping、cross-vowel出力は変更しない。

## 3. 目的

- normalized readingからimmutableな長音token provenanceを生成する。
- timelineの全生成・再構築経路で長音metadataを保持する。
- metadataをbase identityへ含め、MS21 schemaとの混在をfail closedにする。
- explicit long runを通常same-vowel candidate / grouping / manual crossfadeから隔離する。
- `hold`と`decay`を一つのshared resolverで決定的に生成する。
- run memberごとのadjustment所有権とmode優先順位をmodel境界で検証する。
- Preview adapterとwriter adapterで同じcontrol point、特にdecay終端exact `0.0`を維持する。
- `ー`を含まない既存same-vowel / cross-vowel出力を回帰で保護する。

## 4. In Scope

- `VowelToken`とadditive token API
- 既存vowel list / string APIのtoken API派生化と出力互換
- `VowelTimelinePoint`へのprimitive long-vowel metadata追加
- even / anchor allocation、fallback、RMS refine、peak反映、interval repair、Preview / writer copyでのmetadata保持
- strict primitive `hold | decay` validation
- `ShapeParameters.long_vowel_mode`のadditive追加、既定`hold`
- `EventAdjustment.long_vowel_mode`のadditive追加
- `ms22-base-plan-v1`と`ms22-adjustment-snapshot-v1`へのschema更新
- explicit long runの検証・構築とeffective provenance
- long source / intermediate continuation / terminal continuation / non-long / syntheticの所有権検証
- `hold` plateauとclosing edge、`decay` single linear-to-zero
- decay中のtail override無効化とsnapshot内latent保持
- source start / peak同一frameと、同一morph・同一frameのrequired zero / positive競合に対する決定的処理
- hold / decay双方で既存adapterが消費できるnon-`None` resolved tail metadata
- long runとautomatic candidate / grouping / manual crossfadeの隔離
- Preview / writer adapterの構造互換とexact-zero検証
- `src.*` / top-level / mixed importの循環・class identity非依存確認
- 現行same-vowel / cross-vowelの監査と、長音metadataとの衝突が再現した場合だけの限定補修

## 5. Out of Scope

- `GenerationSettings` DTO、built-in preset、user preset、`presets.json`、INI key
- preset選択・適用・作成・更新・削除
- output edit history、UiState、analysis rollback、diagnostics、fingerprint、report
- RightPane、Preview panel、event editorを含むGUI変更
- hold / softnessをanalysis-affecting parameterからoutput-onlyへ移す変更
- 音響、RMS、observation、同音母音間隔による長音推定
- `ー`を含まないsame-vowelアルゴリズムの一般調整や閾値変更
- VMD形式、30fps、固定モーフ`あ / い / う / え / お`の変更
- Qt / PySide6、外部cloud ASR、外部音声送信、background通信、Whisper自動download
- dependency、package、release、tag、merge、push
- 実MMDでのVMD / WAV読み込み・リップ同期確認。MS26へ維持する

## 6. 前提条件

- MS21 Closeout Aを維持し、既存MS21 adjustment / Preview / writer契約を後方互換の基準とする。
- MS22-B1のP1 / P2 / P3は残存せず、`01a836a`で契約固定済みである。
- normalized readingは`text_to_hiragana()`またはvoice-onlyから同じ変換へ入る読み列を指す。
- raw入力由来とG2P生成の`ー`を区別しない。
- `VowelTimingPlan.vowels`は`list[str]`のまま維持し、long metadataはtimelineを正本とする。
- 新規mode contractはprimitive stringを正本とし、Enumまたはclass identityへ依存しない。
- legacy timeline tuple arityは拡張せず、metadataなしのnon-long入力として扱う。
- 現行packageは`src.core`とtop-level `core`、`src.vmd_writer`とtop-level `vmd_writer`が別moduleとして
  loadされ得るため、structural boundaryとprimitive fieldで互換を維持する。
- 新しい依存関係は不要であり、`pyproject.toml`、build、license文書を変更しない。

### 6.1 計画作成時の現行回帰基準

2026-08-01に次の4 commandを一つずつ実行した。

| 対象 | 結果 | process exit code |
| --- | --- | --- |
| text / pipeline / VMD 51件 | 51 passed | 0 |
| MS21 core / Preview / grouping / intervals 102件 | 102 passed | 0 |
| zero guard / multipoint / Preview identity / adjusted save 65件 | 65 passed | 0 |
| output identity / import / voice-only 9件 | 9 passed | 0 |

合計227件はすべてpass表示・process exit code 0である。これはB2実装前の非変更baselineであり、
B2実装後の検証済み結果を意味しない。

実装状態整合レビューでは、直接影響を受けるhistory / selected editor / UI sync回帰24件も追加実行し、
pass表示・process exit code 0を確認した。レビュー時の合計251件は非変更baselineであり、B2実装後の
検証結果ではない。

### 6.2 2026-08-06 実装前チェック再確認

文書修正後、前回と同じ対象範囲を一つずつ再実行した。

| 対象 | 結果 | process exit code |
| --- | --- | --- |
| text / pipeline / VMD | 51 passed | 0 |
| MS21 core / Preview / grouping / intervals | 102 passed | 0 |
| zero guard / multipoint / Preview identity / adjusted save | 65 passed | 0 |
| output identity / import / voice-only | 9 passed | 0 |
| history / selected editor / UI sync context | 24 passed | 0 |
| full suite | 618 passed、7 subtests passed | 0 |
| `compileall src tests` | completed | 0 |
| `git diff --check` | clean | 0 |

合計251件の対象回帰とfull suiteはすべてpass表示・process exit code 0だった。duration境界をevent frameと
generated final closing zeroへ分離し、source peak frameをbase timing固定・peak value調整だけとする契約へ
統一した。Block Breakdownへの既存3回帰追加も確認した。P1 / P2 / P3の残存はない。
この再確認でもproduction code、test code、GUI、dependency、build設定は変更していない。

### 6.3 2026-08-06 B2実装後コードチェック

MS22-B2を実装し、B2専用26件、MS21 core / Preview / grouping / interval回帰102件、
text / pipeline / VMD回帰51件、full suite 644件・7 subtestsを一つずつ実行した。
すべてpass表示・process exit code 0で、`compileall src tests`もexit code 0だった。
実装対象はtoken、timeline metadata、mode / schema、shared effective-shape resolver、
Preview / writer adapter、B2専用testに限定した。GUI、preset / INI、state / history、diagnostics、
dependency、package、実MMD確認は変更・実施していない。

## 7. 対象ファイル

### 7.1 production code変更対象

| file | 変更責務 |
| --- | --- |
| `src/core/text_processing.py` | `VowelToken`、tokenizer、legacy API派生化 |
| `src/core/pipeline.py` | tokenをtimelineへ1対1投影し、全再構築経路でmetadataをcopy |
| `src/vmd_writer/writer.py` | `VowelTimelinePoint` additive field、normalization / interval copyでmetadata保持 |
| `src/core/event_adjustment.py` | primitive mode validation、adjustment field、MS22 snapshot schema、canonicalization |
| `src/core/effective_shape_plan.py` | long metadata検証、run DTO / provenance、ownership、hold / decay resolver、隔離処理 |
| `src/core/preview_transform.py` | Preview timeline normalizationでmetadata保持 |
| `src/core/__init__.py` | 新規core public token / mode APIの最小export。循環を起こす場合はexportせず明示module pathを正本化 |

### 7.2 条件付き変更対象

| file | 条件 |
| --- | --- |
| `src/vmd_writer/effective_shape_adapter.py` | existing generic変換がexact zeroまたは新規provenanceを欠落させる再現testがある場合だけ最小修正 |
| `src/vmd_writer/__init__.py` | 原則変更しない。既存`VowelTimelinePoint`exportがfield追加だけで維持できない場合に限り検討 |

新規`src/core/long_vowel_contract.py`は作成しないことを初期案とする。primitive mode validationと
adjustment schemaは`event_adjustment.py`、token contractは`text_processing.py`、run resolverは
`effective_shape_plan.py`へ置けば現行責務境界に収まる。pre-implementation checkで循環または責務肥大が
実証された場合だけ、新規module案をP2として再評価する。

### 7.3 B2で必須作成する新規test

- `tests/test_ms22_b2_long_vowel_tokens.py`
- `tests/test_ms22_b2_timeline_metadata.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms22_b2_import_boundaries.py`

### 7.4 既存testの変更・回帰対象

- `tests/test_text_processing.py`
- `tests/test_pipeline_peak_values.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_preview_transform.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_zero_guard.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_ms21_b4_selected_event_editor.py`
- `tests/test_ms21_b7_ui_sync_context.py`
- `tests/test_ms21_b7_import_boundaries.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`

### 7.5 B2で変更しないファイル

- `src/gui_wx/**`
- `src/core/settings_store.py`
- `src/core/event_adjustment_history.py`
- `README.md`、`readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/repo_milestone.md`、`docs/Version_Control.md`
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`

正本仕様と利用者文書のimplemented同期はMS22-B6が所有する。B2ではplan、Block Breakdown、Index、
Roadmapの進捗記録だけを同期する。

## 8. 実装方針

### 8.1 単一の構造データ経路

```text
normalized reading
  -> VowelToken sequence
  -> VowelTimelinePoint primitive metadata
  -> BaseShapeEvent long provenance
  -> validated EffectiveLongVowelRun
  -> EffectiveShapePlan
  -> Preview adapter / writer adapter
```

同音母音関係、observation、shape grouping、表示文字列からlong metadataを再構築しない。

### 8.2 additive compatibility

- `VowelToken`は`frozen=True`のimmutable DTOとする。
- `VowelTimelinePoint`の新fieldは末尾にdefault付きで追加し、既存positional constructorを壊さない。
- `build_even_vowel_timeline()`と`build_anchor_based_vowel_timeline()`の既存`vowels` positional inputを維持し、
  optional keyword-only token inputを追加する。
- legacy callerがtoken inputを省略した場合は`None / False / None`のnon-long metadataを生成する。
- pipeline自身はtoken inputを必ず渡し、pipeline生成pointのtoken index欠落を許可しない。
- writerのlegacy tuple arity 2 / 3 / 4 / 6は変更しない。

### 8.3 fail-closed validation

- primitive modeはexact lowercase `hold`または`decay`だけを受理する。trim、casefold、別名変換をしない。
- boolをintとして受理せず、token indexは0以上のintだけを受理する。
- metadataなし入力と完全metadata入力は受理し、部分metadata混在は拒否する。
- continuationは自身より前のnon-continuation sourceを参照し、vowel一致とrun連続性を必須とする。
- sourceと1件以上のcontinuationだけをlong runとする。
- forward reference、cycle、欠損source、別vowel source、run境界越え、duplicate / 非連続token indexを拒否する。
- `terminal_end_frame <= source_peak_frame`を拒否する。
- 同じmorph / frameで、long shapeのrequired zeroと別shapeのpositive control pointが競合する入力を
  normalization前に拒否する。zero / positiveのどちらかをsilent mergeで失わない。
- invalid adjustment requestは既存snapshotとeffective planを変更しない。

### 8.4 long shapeと通常shapeの分離

- long run memberをautomatic candidate handoff、通常grouping、manual crossfadeの入力から除外する。
- long run前後で通常event列を分割し、残ったnon-long eventだけを既存処理へ渡す。
- candidate spanまたはprevious / next referenceがlong memberへ触れる場合は、そのcandidateだけをdisabledにする。
- synthetic point / tokenへlong provenanceを継承しない。
- `ー`を含まないinputは既存shape種類、control point、provenance、normalizationを維持する。

### 8.5 hold / decayの共有解決

- modeはterminal eventの明示override、`ShapeParameters.long_vowel_mode`、既定`hold`の順で解決する。
- source peak frameはbase timelineのsource event frameを正本として固定し、source adjustmentで変化するのは
  peak valueだけとする。terminal adjustment後のend frameをshape入力にする。B2ではpeak frame adjustmentを
  新設せず、MS21の30fps整数frame契約を維持する。
- source startがsource peakより前ならopening zeroを置く。両frameが同じならzero-length opening edgeとして
  start zeroを省略し、source peak valueだけを置く。positive source peakと同じframeへrequired zeroを登録しない。
- `hold`はsource peakからterminal endまでpeak valueを維持する。
- `hold`のterminal endにはpeak control pointを置き、closing zeroを同一frameで上書きしない。
- closing hold / softnessはterminal endより後にだけ適用する。requested tailが0 / 0でも、terminal plateauを
  保持するためzero control pointは原則`terminal_end + 1`に置く。
- source / terminal eventの実効frameは`0 <= start <= peak <= terminal_end <= source_duration`を満たす。
  shapeへ生成するfinal closing zeroは、既存final tailと同じくresolved closing tailの分だけsource durationを
  超過し得る。この超過は最終shapeの生成edgeに限って許容し、次shapeがある場合だけ既存保護境界へclampする。
- 同一morphの次shapeがterminal end以前に開始し、terminal plateauと次openingを両立できない場合は
  silent clampせずfail closedにする。次shapeが後にある場合は既存保護境界内へtailをclampする。
- `decay`はsource peak valueからterminal endのexact `0.0`まで単一線形segmentとし、continuation peak、
  hold、softness、slope、post-terminal tailをcontrol pointへ反映しない。
- normalizerはdecay terminalをrequired zeroとして保持し、epsilonへ変換しない。
- decay terminalまたはhold closing zeroが、別shapeの同一morph positive control pointと同じframeになる場合は、
  terminal / next peakを移動せず`AdjustmentContractError`でfail closedにする。異なるmorphの同一frame値は
  競合ではない。even fallbackの`あーあ`のように長音終端と次の同母音peakが一致する配置はこの拒否対象とする。
- required zero / positive競合はshape mergeとnormalizationの前に検証し、writerのduplicate merge順へ委ねない。
- `ResolvedTailParameters`はhold / decay双方のreal long shapeへnon-`None`で付与する。decayではrequested
  hold / softness / slopeと利用可能範囲をlatent情報として保持しつつ、effective hold / softnessを`0`、
  `has_slope_midpoint=False`とし、control pointへ作用させない。mode-awareな無効理由表示はB5が所有する。

### 8.6 adjustment / canonicalization

- `EventAdjustment.long_vowel_mode`はoptional primitive fieldとする。
- DTO単体ではmode syntaxを検証し、event role依存の所有権はbase inputを持つresolver / update境界で検証する。
- sourceはpeak / start、terminal continuationはend / tail / modeだけを所有する。
- intermediate continuationは全fieldを所有しない。
- non-long eventはMS21 field所有権を維持するがlong modeを拒否する。
- synthetic tokenは全adjustmentを拒否する。
- explicit non-`None`のhold / softness / modeはglobal値と同じでもcanonical snapshotから削除しない。
- decay中のterminal tail / slope値はsnapshotにlatent保持し、shape出力だけで無効化する。
- modeをholdへ戻した際にlatent tailを再び適用する。
- peakがbase値と同じ、offset 0等、preset変更で意味が変わらない既存no-op規則は維持する。

### 8.7 schema更新

- base identity schemaを`ms22-base-plan-v1`へ更新し、各timeline pointのprimitive long metadataをpayloadへ含める。
- adjustment snapshot schemaを`ms22-adjustment-snapshot-v1`へ更新し、optional modeをcanonical payloadへ含める。
- MS21 schemaのidentity / snapshotを暗黙migrationせず拒否する。
- frame / vowelが同じでもlong metadataが異なるbase planは異なるidentityとする。

### 8.8 import boundary

- token / mode / effective planの新規public APIは`src.core.*`を正本とする。
- writer module初期化中にcore packageへmodule-level逆importを追加しない。
- adapterはclass identityではなくattribute protocol、tuple、primitive valueを使用する。
- fresh processで`src.core`、`core`、`src.vmd_writer`、`vmd_writer`のimport順を変えて検証する。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- `git status --short --branch`、branch、logを一つずつ再確認する。
- 本planとBlock Breakdown、B1 contractを現行HEADへ再照合する。
- 未コミット変更があればユーザー所有として保護し、B2対象との重複を確認する。
- pre-implementation checkのP1 / P2が残る場合は実装しない。

### Step 2: primitive mode contract

- `LONG_VOWEL_MODE_HOLD = "hold"`、`LONG_VOWEL_MODE_DECAY = "decay"`、閉じたsupported tupleを定義する。
- `validate_long_vowel_mode(value: object) -> str`を追加し、exact stringだけを返す。
- `ShapeParameters`末尾へ`long_vowel_mode: str = "hold"`を追加して既存2引数constructorを維持する。
- invalid type / valueを`AdjustmentContractError`で拒否する。

### Step 3: token API

- `VowelToken`を追加する。
- `hiragana_to_vowel_tokens(text)`と`text_to_vowel_tokens(text)`をadditiveに追加する。
- non-continuationを作るたびにactive sourceを自身のtoken indexへ更新する。
- `ー`はactive sourceがある場合だけcontinuationを追加する。
- 連続`ーー`はactive sourceを更新せず、同じsourceを参照する。
- 次の通常tokenは同じvowelでも新しいsourceとなる。
- legacy list / string APIをtoken列の`vowel`投影から生成し、既存出力を維持する。

### Step 4: timeline metadataの追加とcopy

- `VowelTimelinePoint`末尾に次を追加する。
  - `vowel_token_index: int | None = None`
  - `is_long_vowel_continuation: bool = False`
  - `long_vowel_source_token_index: int | None = None`
- even / anchor builderにkeyword-only token inputを追加し、length、vowel、token index順を検証する。
- `build_vowel_timing_plan()`はnormalized readingからtokenを一度だけ生成し、legacy vowel listとtimelineへ投影する。
- anchor fallbackでも同じtoken inputをeven builderへ渡す。
- pipelineのRMS refine、observation refine、peak value copy、adjacent conflict、midpoint repair、writer timing repairで
  3 fieldを必ずcopyする。
- writer normalization / interval copy / peak copy、Preview normalizationでも3 fieldをcopyする。
- synthetic bridge pointはdefault metadataを明示してnon-longのままにする。

### Step 5: metadata validationとbase identity

- structural timeline inputからmetadata modeを判定する。
- all-defaultはlegacy non-longとして受理する。
- explicit modeでは全pointに`vowel_token_index`を要求し、base event ordinalとの1対1対応を検証する。
- continuation source、vowel、順序、連続runを検証し、long roleをbase eventへ投影する。
- identity payloadへ3 primitive fieldを追加し、schemaを`ms22-base-plan-v1`へ更新する。
- old schema snapshotがidentity比較を通らないことをtestで固定する。

### Step 6: adjustment schemaとownership

- `EventAdjustment`末尾へoptional `long_vowel_mode`を追加し、`is_empty`とcanonical payloadへ含める。
- adjustment schemaを`ms22-adjustment-snapshot-v1`へ更新する。
- canonicalizerからglobal hold / softness同値による削除を外し、明示値を保持する。
- resolverと`apply_adjustment_update()`のmutation前にrun role別所有権を検証する。
- B1所有権表に反するrequestはclean-up扱いで黙って削除せず、request全体を拒否する。
- non-long eventに対する既存MS21 tail / slope cleanupは維持し、long role rejectionと混同しない。
- reject時にcurrent snapshot、selection、history相当のcaller stateが変化しないpure failureをtestする。

### Step 7: long run DTO / effective provenance

次のadditive DTOを`effective_shape_plan.py`へ置く候補とする。

```text
EffectiveLongVowelRun
  source_base_event_index: int
  continuation_base_event_indices: tuple[int, ...]
  terminal_base_event_index: int
  vowel: str
  resolved_mode: hold | decay
  source_peak_frame: int
  terminal_end_frame: int
  source_peak_value: float
```

- `BaseShapeEvent`と`EffectiveShapeEvent`へprimitive long role / source / terminal indexをadditiveに保持する。
- role値候補は`source`、`intermediate_continuation`、`terminal_continuation`、`None`とする。
- `EffectiveShapePlan.long_vowel_runs`へvalidated runを固定順で保持する。
- `EffectiveShape.real_base_event_indices`にはsourceと全continuationを順番どおり含める。
- `shape_kind`は`long_vowel_hold`または`long_vowel_decay`とし、adapter側で再推測しない。

### Step 8: candidate / grouping分割

- metadata検証後にlong member index集合を作る。
- observation candidateがlong memberをspanまたはreferenceに含む場合はdisabled handoffを記録する。
- non-long event列をlong boundaryごとのsegmentへ分割し、各segmentで既存`_group_events()`を使う。
- long runは専用shape builderへ渡す。
- 通常shapeとlong shapeをbase event順にmergeする。
- manual crossfade comparison / extensionはlong shapeを対象外にし、残存non-long shapeだけで既存規則を維持する。

### Step 9: hold / decay shape

- source start、base timeline由来のsource peak frame、terminal endを30fps整数frameで検証する。
  source / terminal event frameは`0 <= start <= peak <= terminal_end <= source_duration`を満たし、生成された
  final closing zeroだけはresolved tailによりsource durationを超過し得る。次shapeがある場合のclampは既存保護境界を維持する。
- `source_start_frame < source_peak_frame`の場合だけsource start zeroを生成する。同一frameならsource peakを優先し、
  start zeroとrequired zero登録を省略する。
- hold shapeはsource peakとterminal peak anchorを同値で置く。
- terminal end後のtailはterminal adjustmentのexplicit値、global値の順で解決する。
- zero frameはterminal endより後とし、次shape保護時のclampと最小1 frame closing edgeを決定的に扱う。
- decay shapeはsource peakとterminal exact zeroの2端点を基本とし、source openingに必要なstart zeroだけを前置する。
- decay shapeにcontinuation peak、tail midpoint、hold pointを追加しない。
- `ResolvedTailParameters`をhold / decay双方へ付ける。decayではrequested値をlatent metadataとして保持し、
  effective hold / softnessを`0`、`has_slope_midpoint=False`として既存consumerのnon-`None`前提を維持する。
- normalization contractへ、source startがpeakより前の場合だけshape start zeroを登録し、closing zeroと
  decay terminal zeroを明示的に保護する。
- required zeroと別shapeの同一morph positive control pointが同じframeなら、normalization前にplan全体を拒否する。

### Step 10: adapter整合

- Preview adapterとwriter adapterがlong shapeをgeneric control point列として消費できることを先にtestする。
- adapterがshape kindから別resolverを呼ばないことを維持する。
- writer normalization後もdecay terminal frame / valueがexact一致することを検証する。
- Preview point列とwriter prepared morph frameを同一effective planから比較する。
- decay shapeのnon-`None` resolved tail metadataで既存selected editor stateを例外なく構築できることを、
  GUIを変更せず既存のUI非依存adapter testで確認する。
- legacy facadeはmetadataなし入力の現行出力を維持する。

### Step 11: same-vowel限定監査

- micro-gap、same-vowel burst、representative span、grouped multipoint、cross-vowel continuityを実測比較する。
- long metadataなしのfixtureはcontrol point列、candidate flag、group provenanceを既存期待値どおり維持する。
- long runを通常groupへ吸収する失敗だけを新規再現testにする。
- 既存same-vowelの一般閾値、valley比、epsilon、crossfade規則を変更しない。

### Step 12: 検証と進捗同期

- B2専用test、関連回帰、full suite、`compileall src tests`、`git diff --check`を一つずつ実行する。
- pass表示とprocess exit codeを分けて記録する。
- diffをproduction / test / docsへ分類し、GUI、preset、state、dependencyの混入がないことを監査する。
- Block Breakdown、Index、Roadmapを実測状態へ同期する。
- 手動GUIはB2の必須gateにしない。GUI出力導線の受け入れはB5 / B6で実施する。

## 10. 状態遷移 / データ契約

### 10.1 token contract

```text
VowelToken
  vowel: あ | い | う | え | お
  token_index: int >= 0
  is_long_vowel_continuation: bool = False
  long_vowel_source_token_index: int | None = None
```

| normalized reading | token概要 |
| --- | --- |
| `ーあ` | leading markerを無視し、通常`あ`だけ |
| `あー` | source 0、continuation 1 -> source 0 |
| `あーー` | continuation 1 / 2はいずれもsource 0 |
| `あーあー` | continuation 1 -> source 0、continuation 3 -> source 2 |
| `ああ` | 2件ともnon-long。長音runなし |

### 10.2 timeline metadata contract

```text
VowelTimelinePoint additive fields
  vowel_token_index: int | None = None
  is_long_vowel_continuation: bool = False
  long_vowel_source_token_index: int | None = None
```

- pipeline explicit mode: `vowel_token_index == base_event_index`を必須とする。
- legacy mode: 全pointが`None / False / None`。
- partial mode: 1件でもexplicit metadataがあるのに他pointがdefaultならrejectする。
- continuationだけがsource indexを持ち、source自身は`None`とする。
- timelineのframe repairはmetadataを変更しない。

### 10.3 mode contract

```text
LongVowelMode primitive values
  hold
  decay
```

`"Hold"`、`" hold"`、`"decay "`、空文字、bool、数値、Enum instanceは拒否する。API境界で
既知文字列へ変換せず、callerがprimitive contractを満たすことを必須とする。

### 10.4 run / mode resolution

```text
terminal EventAdjustment.long_vowel_mode
  > ShapeParameters.long_vowel_mode
  > default hold
```

```text
source event
  + contiguous continuation event(s) referencing source
  -> one EffectiveLongVowelRun
```

terminalはrun内最後のcontinuationである。次のnon-continuation eventは同じvowelでも別runまたはnon-long eventとする。

### 10.5 run member ownership

| event role | peak | start | end | hold / softness / slope | long mode |
| --- | --- | --- | --- | --- | --- |
| long source | 許可 | 許可 | 拒否 | 拒否 | 拒否 |
| intermediate continuation | 拒否 | 拒否 | 拒否 | 拒否 | 拒否 |
| terminal continuation | 拒否 | 拒否 | 許可 | hold時作用、decay時latent | 許可 |
| non-long real | MS21維持 | MS21維持 | MS21維持 | MS21 group tail維持 | 拒否 |
| synthetic | 拒否 | 拒否 | 拒否 | 拒否 | 拒否 |

### 10.6 shape contract

#### hold

```text
source start: source start < source peak の場合だけ0.0。同一frameなら省略
source peak: adjusted source peak value
terminal end: same source peak value
post-terminal tail: terminal explicit tail > global tail
closing zero: strictly after terminal end
```

#### decay

```text
source start: source start < source peak の場合だけ0.0。同一frameなら省略
source peak: adjusted source peak value
terminal end: exact 0.0
post-terminal tail: none
```

continuation peakはどちらのmodeでも中間control pointにしない。decay terminalの`0.0`は浮動小数の
近似比較ではなくexact値としてDTOとadapter出力へ保持する。

```text
ResolvedTailParameters
  hold: requested値とeffective値を既存規則で解決
  decay: requested値はlatent保持、effective hold / softness = 0、has_slope_midpoint = False
```

hold / decayのreal long shapeはいずれもnon-`None`のresolved tail metadataを持つ。同一morph・同一frameで
required zeroと別shapeのpositive control pointが競合する場合は、normalizerまたはwriterへ渡す前に
fail closedとする。source start / peak同一frameはこの競合へ含めず、opening zeroを省略してsource peakを残す。

### 10.7 schema / canonicalization

```text
BasePlanIdentity.schema = ms22-base-plan-v1
AdjustmentLayerSnapshot.schema = ms22-adjustment-snapshot-v1
```

- identityはtimeline metadataを含む。
- adjustmentはoptional modeを含む。
- non-`None` tail / modeはexplicit overrideであり、active global値との同値比較で消さない。
- decayはtailを出力へ適用しないがsnapshotから削除しない。
- MS21 schemaはfail closedであり、自動migrationしない。

### 10.8 resolver transaction

```text
validate base metadata
  -> build long roles / runs
  -> validate current snapshot and requested ownership
  -> apply source / terminal adjustments
  -> resolve explicit mode
  -> isolate long members from candidates / grouping / crossfade
  -> build long and non-long shapes
  -> normalize once
  -> return immutable EffectiveShapePlan
```

いずれかで失敗した場合はplanを部分返却せず、callerが保持するlast-valid snapshot / planを変更しない。

## 11. テスト方針

### 11.1 B2専用test

#### token / text

- raw / G2P / voice-only normalized readingの`ー`が同じtoken規則になる。
- leading `ー`、連続`ーー`、`あーあー`、`ああ`を固定する。
- legacy vowel sequence / string出力が不変である。
- token DTOがimmutableである。

#### timeline / identity

- even / anchor / fallback / RMS / peak / interval repairがmetadataを保持する。
- writer / Preview copyがmetadataを保持する。
- legacy positional / keyword `VowelTimelinePoint`とtuple入力をnon-longとして受理する。
- explicit / partial / invalid source / forward / vowel mismatchを検証する。
- metadata差だけでbase identityが変わる。
- MS21 identity / adjustment schemaを拒否する。

#### resolver

- default hold、global decay、terminal explicit overrideの優先順位を固定する。
- `あー`、`あーーい`、`あーあ`、`あーあー`を検証する。
- hold terminal peak、post-terminal zero、tail clampを検証する。
- source / terminal event frameのduration境界と、最終shapeだけに許容されるclosing zeroのduration超過を検証する。
- decay terminal exact zero、tailなし、continuation peakなしを検証する。
- source start / peak同一frameではstart zeroを生成・登録せず、source peak valueだけを保持する。
- decay terminalまたはhold closing zeroと次shapeの同一morph positive pointが同一frameならnormalization前に
  拒否し、異なるmorphの同一frame配置は受理する。
- even fallbackの`あーあ`はterminal zeroと次の`あ` peakが同一frameになるためfail closedになり、
  frameが分離したanchor配置では受理できる。
- terminal end <= source peak、次same-morph shapeとの解決不能競合を拒否する。
- source duration端のhold closing edgeとdecay terminalを検証する。
- long runをcandidate / grouping / manual crossfadeが使用しないことを検証する。

#### adjustment

- run member所有権表の許可 / 拒否をfieldごとに検証する。
- non-long modeとsynthetic adjustmentを拒否する。
- active global値と同じexplicit hold / softness / modeを保持する。
- decay中にtail / slopeをlatent保持し、hold復帰で再適用する。
- decay shapeもnon-`None`のresolved tail metadataを持ち、requested値、effective 0、midpointなしを区別する。
- reject後にcurrent snapshotが不変である。

#### adapter / import

- 同一effective planからPreviewとwriterのlong control pointが一致する。
- writer zero guard後もdecay terminalがexact `0.0`である。
- decay planから既存selected editor stateを構築しても例外にならず、mode-aware表示をB5へ残す。
- legacy writer outputがmetadataなしで不変である。
- fresh process import順とmixed class inputで循環せず、class identityへ依存しない。

### 11.2 既存回帰command

各commandは一つずつ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b2_long_vowel_tokens.py tests\test_ms22_b2_timeline_metadata.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b2_long_vowel_resolver.py tests\test_ms22_b2_long_vowel_adapters.py tests\test_ms22_b2_import_boundaries.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py tests\test_pipeline_peak_values.py tests\test_pipeline_and_vmd.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b2_event_adjustment.py tests\test_ms21_b2_effective_shape_plan.py tests\test_ms21_b2_shape_adapters.py tests\test_preview_transform.py tests\test_vmd_writer_grouping.py tests\test_vmd_writer_intervals.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_vmd_writer_zero_guard.py tests\test_vmd_writer_multipoint_shape.py tests\test_ms21_b3_pipeline_preview_integration.py tests\test_ms21_b5_adjusted_vmd_save.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b5_effective_output_identity.py tests\test_ms21_b7_import_boundaries.py tests\test_ms19_b3_textless_pipeline.py tests\test_ms19_b4_analysis_worker_voice_only.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b6_adjustment_history.py tests\test_ms21_b4_selected_event_editor.py tests\test_ms21_b7_ui_sync_context.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
rg -n "[ \t]+$" docs\Implementation_Plan\MS22-B2_Implementation_Plan.md docs\Implementation_Plan\MS22_Block_Breakdown.md docs\MS20_and_Beyond_Index.md docs\MS20_and_Beyond_Roadmap.md
```

末尾空白`rg`はmatchなしのexit code 1を正常とする。pytestはpass件数、failure / error、process exit codeを
分けて記録する。full suiteでwxを含む環境固有終了が出た場合も表示結果とprocess exit codeを分離し、
自動的にpass扱いしない。

### 11.3 diff監査

- production変更が§7.1 / 7.2へ収まる。
- GUI、settings store、history、diagnostics、package、dependencyへ変更がない。
- 既存testを削除・skip・期待値弱化していない。
- same-vowel一般閾値、fixed morph、30fps、VMD formatを変更していない。
- token / metadata / identity / adapterのcopy漏れがない。

### 11.4 手動確認

- B2では新規GUIを実装しないため、手動GUI確認を必須受け入れ条件にしない。
- Preview / writerの構造整合は自動testで検証する。
- 実MMD確認はMS26へ維持し、B2完了証拠に含めない。

## 12. 受け入れ条件

- normalized reading上の`ー`だけがlong continuationとなり、`ああ`はlong runにならない。
- leading `ー`、連続`ーー`、`あーあー`がB1 source参照契約どおりである。
- legacy vowel API、timeline constructor、tuple inputが後方互換である。
- pipeline生成timelineは完全metadataを持ち、全refine / repair / adapter経路で保持される。
- metadata差が`ms22-base-plan-v1` identityへ反映され、MS21 schemaをfail closedで拒否する。
- primitive modeはexact `hold | decay`だけを受理する。
- long source / continuation / terminalのroleとadjustment所有権がmodel境界で強制される。
- explicit terminal modeがglobal modeより優先される。
- holdはterminal endまでpeakを維持し、closing zeroはterminal end後にある。
- decayはsource peakからterminal endのexact `0.0`まで単一線形segmentである。
- source startとpeakが同一frameならopening zeroを省略してpeak valueを保持する。
- long required zeroと別shapeのpositive pointが同一morph・同一frameで競合する場合は、silent mergeせず
  normalization前にfail closedとし、異なるmorphの同一frame配置は受理する。
- hold / decay双方のreal long shapeがnon-`None`のresolved tail metadataを持ち、decayのeffective tailは0、
  latent requested値はsnapshot / metadataへ保持される。
- decay中のtail / slope overrideは出力へ作用せずlatent保持され、hold復帰時に再び作用する。
- long run memberがautomatic candidate、通常grouping、manual crossfadeへ混入しない。
- `ー`なしのsame-vowel / cross-vowel既存回帰が維持される。
- Previewとwriterが同一effective planから同じlong shapeを得る。
- B2専用test、指定回帰、full suite、compileall、diff checkの結果とexit codeが記録される。
- production / test変更がB2 scope内に限定され、GUI、preset、state、dependency、packageを変更しない。
- P1 / P2が残存しない。P3は記録し、B3へ影響する場合はB3計画前に解消する。

## 13. リスクと対策

| リスク | 影響 | 対策 |
| --- | --- | --- |
| timeline copy漏れ | Preview / writerでlong provenance消失 | constructor全箇所を`rg`で列挙し、copy-path testを個別化 |
| partial metadataの黙認 | 同音母音を誤って長音化 | all-default / all-explicitだけを受理して混在を拒否 |
| class identity依存 | `src.*` / top-level mixed importで拒否 | primitive fieldとstructural protocol、fresh-process import test |
| long runが既存groupへ混入 | decay途中にvalley / continuation peakが入る | long member集合でcandidate / grouping / crossfade入力を分割 |
| hold終端がzeroに上書きされる | B1のterminal plateau違反 | terminal peak anchorとpost-terminal closing zeroを別frameにする |
| decay zeroがepsilon化される | Preview / VMD終端不一致 | required zeroとadapter exact-value testを追加 |
| source startとpeakが同一frame | start zeroがpositive peakを上書きする | zero-length opening edgeとしてstart zeroを省略しpeakを優先 |
| long required zeroと次の同母音peakが同一frame | exact zeroか次event振幅の一方がsilent mergeで消える | normalization前に同一morph競合を拒否し、異なるmorphは許可 |
| decayでresolved tailが`None` | 既存selected editor consumerが例外になる | requested latent / effective 0を持つnon-`None` metadataを付与 |
| tail同値canonicalization | preset変更後にexplicit intent消失 | non-`None` hold / softness / modeを保持 |
| non-owner editの黙示cleanup | ユーザーrequestが別意味でcommit | long role違反はtransaction全体をfail closed |
| B2でGUI/stateまで拡張 | Block責務逸脱と回帰増大 | GUI、history、settings、diagnosticsをOut of Scopeに固定 |
| same-vowel一般修正への拡大 | 既存出力の意図しない変化 | 再現済みlong衝突だけ修正し、閾値・valley規則を維持 |
| schema更新漏れ | stale snapshotが誤適用 | identity / adjustment schemaを同Blockで更新し旧schema reject test |
| source duration端のhold | terminal plateauとclosing zeroが同frame競合 | final tailの既存duration超過許容を長音closing edgeへ限定適用 |

## 14. Codex 実装時の注意

- commandは並列・連結・pipelineにせず、一つずつ実行して結果を確認する。
- 実装開始前にGit状態、branch、HEAD、本plan、B1 contract、対象code / testを再読する。
- 未コミット変更はユーザー所有として保護し、restoreや上書きをしない。
- production実装より先にB2専用失敗testを小さい単位で追加し、契約違反を再現する。
- public behaviorを推測で拡張せず、B1の明示契約と現行互換に限定する。
- `VowelTimelinePoint`の既存positional field順、legacy tuple arity、`VowelTimingPlan.vowels`を変更しない。
- long metadataをsame-vowel関係や音響から補完しない。
- decay terminal zeroをepsilonまたはpost-tailへ変換しない。
- invalid mode / metadata / ownershipをsilent fallbackやcleanupで受理しない。
- writerだけ、Previewだけのlong resolverを追加しない。
- GUI、preset JSON、INI、history、diagnostics、fingerprintを先行実装しない。
- fixed morph、30fps、VMD形式、音声契約、wxPythonを維持し、Qt / PySide6を復活させない。
- dependency、license、package、release、tag、merge、pushを変更・実行しない。
- 実MMD確認を実施したと記録しない。未検証事項はMS26へ維持する。
- 実装後はdiffを検証前にも自己監査し、scope creep、copy漏れ、contrary evidenceを確認する。
- 完了時は変更file、実装内容、test件数、各exit code、逸脱、残課題、B3へのhandoffを分けて報告する。
