# MS23-B2 Implementation Plan

## 1. 文書情報

- 文書名: MS23-B2 Built-in Morph Name Set / Output Mapping Implementation Plan
- 作成日: 2026-08-16
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 対象ブランチ: `feature/MS23-implementation`
- 計画作成時点のHEAD: `54256d0 Finalize MS23-B1 contract status sync`
- 前提Block: MS23-B1 `Completed / Decision Gates Adopted / Content Sync Applied / Contract Fixed`
- 文書ステータス: Implementation Plan Repaired / P2 Resolved / Fresh Read-only Recheck Passed / Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report)
- 実装状態: B2のproduction code、test code、Preview表示境界を実装済み。手動GUI確認はユーザー報告の範囲で通過しており、Codex自身のGUI実行結果とは扱わない。実MMD確認はMS26へdeferred。B3 / B4 / B5、MS25以降は未実装。
- 計画作成時の権限: 本文書の作成・レビュー時点ではproduction code、test code、GUI、runtime user dataを変更しない。

本書は、既存の日本語5母音semantic keyを維持したまま、built-in morph name setをwriter、Preview、diagnosticsへ明示的に渡すための実装手順を固定する。model profileの保存・起動時解決・active state統合はMS23-B3 / B4の責務であり、本Blockでは実装しない。

## 2. 背景

MS23-B1で、次の契約が確定している。

- built-in setは`builtin:japanese-vowels`と`builtin:latin-vowels`の2種類だけである。
- 日本語setの出力名は`あ / い / う / え / お`、Latin setの出力名は`A / I / U / E / O`である。
- semantic key、`EffectiveShapePlan`、normalization contract、protected range、required zero、open-stateは既存の日本語5母音keyを使用し続ける。
- final normalizationをsemantic key空間で完了した後、output morph nameを一度だけ解決する。mapped nameをsemantic normalizationへ戻さない。
- writerのmodule-levelから`src.core`または`core`を逆importしない。
- `src.vmd_writer.writer`と`vmd_writer.writer`が別moduleとして読み込まれる可能性があるため、adapter境界でclass identityの一致を要求しない。
- writerの既存引数省略時は日本語set、VMD 30fps、既存のframe number・value・count・sort orderを維持する。
- profile ID、preset ID、setの説明identityはfingerprintへ直接追加しない。mapped effective frame nameの差だけを既存payloadへ反映する。

現行実装では、writer、Preview、diagnosticsが日本語名をそれぞれの検証・表示境界で参照している。`effective_shape_adapter.py`はsemantic frameをwriterのprivate final normalizationへ渡した後、日本語名のframeを返している。Previewはsemantic keyをlaneとhit-testの識別子として保持し、wx rendererが日本語名を直接描画している。diagnosticsの`EffectiveMorphFrameInput`は日本語名だけを許可している。B2ではこの境界を、共通のbuilt-in定義と明示的な出力名入力へ置き換える。

## 3. 目的

1. built-in morph name setの正本をcoreのleaf moduleへ集約する。
2. 日本語setとLatin setのexact mapping、stable ID、順序、入力検証を固定する。
3. writer、effective-shape adapter、Preview、diagnosticsが同じ順序付き出力名を使う境界を作る。
4. semantic final normalization後に一回だけmappingする順序をコードとテストで固定する。
5. 既存の日本語呼び出し、VMD形式、30fps、long-vowel resolver、event adjustment、Preview hit-testを回帰させない。
6. core-first、writer-first、adapter-first、`src.*` / top-level mixed namespaceのimportを、core DTOのclass identityに依存せず成立させる。

## 4. In Scope

- `MorphNameSet`相当のimmutableなbuilt-in set定義
- `builtin:japanese-vowels` / `builtin:latin-vowels`のexact mapping
- semantic vowel orderとoutput name orderの検証
- primitiveまたはstructuralな明示出力名入力を使うwriter境界
- `effective_shape_adapter`でのsemantic frame normalization後のmapping
- Previewのlane label・選択summary表示名のmapping
- Preview row / segmentのsemantic keyとdisplay nameの分離
- diagnostics effective frameのoutput name検証、snapshot adapterへの明示入力
- mapped effective frame nameを使う既存fingerprintとの接続確認
- writer、Preview、diagnosticsの日本語既定回帰とLatin mapping専用テスト
- fresh-process import order、mixed namespace、class identity非依存の確認
- B2の対象ファイルと既存文書のstatus / handoff同期

## 5. Out of Scope

- `profiles.json`のschema、load / save、atomic replace、100件上限、root ignore（MS23-B3）
- profileのactive ID、runtime baseline、precedence、startup fallback、mutation guard（MS23-B4）
- `GenerationState`、`OutputEditState`、Undo / Redo、analysis invalidationへのprofile統合（MS23-B4）
- RightPaneのprofile選択・Apply・CRUD UI（MS23-B5）
- MS25一括出力の専用DTO、adapter、UI、実装
- PMX / PMD読込、model file解析、任意morph name mapping、user-defined set、追加表情morph
- 英語音声認識、英語音素処理、Whisper model selection
- VMD形式、Shift-JIS field size、30fps、既存WAV契約の変更
- 実MMDでのVMD / WAV読み込み・リップ同期確認（MS26）
- dependency追加、package、release、tag、merge、push

## 6. 前提条件

### 6.1 既存semantic contract

- semantic orderは`("あ", "い", "う", "え", "お")`で固定する。
- `src.core.text_processing.VOWELS`、`src.core.effective_shape_plan.SUPPORTED_MORPHS`、`src.vmd_writer.writer.SUPPORTED_MORPHS`の意味は変更しない。
- `VowelTimelinePoint.vowel`、`EffectiveShapePlan`のshape vowel、Previewのrow / segment / hit region vowelはsemantic keyのままにする。
- `EffectiveTailInput.vowel`、timing planのvowel列、event adjustmentのvowel参照もsemantic keyのままにする。

### 6.2 set contract

実装時のpublic DTOは、既存Block Breakdownの責務名に合わせて`MorphNameSet`とする。最低限、次のimmutable情報を持つ。

| 項目 | 契約 |
|---|---|
| `set_id` | `builtin:japanese-vowels`または`builtin:latin-vowels` |
| `display_name` | 日本語setは`日本語5母音`、Latin setは`英字5母音` |
| output name order | semantic orderと同じ5要素のtuple |
| Japanese names | `あ / い / う / え / お` |
| Latin names | `A / I / U / E / O` |
| mutability | frozen / immutable。呼び出し側がtupleやset定義を変更できない |
| user-defined | 受け付けない。B2のbuilt-in定義はexactly two |

`MorphNameSet`がbuilt-in ID、表示名、exact mapping、semantic orderを検証する唯一の正本である。consumerへはDTOを越境させず、`MorphNameSet.output_names`から得た順序付き`tuple[str, ...]`を渡す。B4 diagnosticsが表示するset display nameも同じDTOから取得し、IDから別表示名表を再構築しない。consumerはこのprimitive境界を再検証するが、built-in mapping tableを複製せず、writerからcore DTOをimportしない。

実装時の呼び出し契約は次の形で固定する。既存引数の順序を変えず、追加引数はkeyword-onlyとする。

```python
write_morph_vmd(..., *, output_morph_names: Sequence[str] = SUPPORTED_MORPHS)
write_morph_frames_vmd(..., *, output_morph_names: Sequence[str] = SUPPORTED_MORPHS)
build_morph_frames_from_effective_shape_plan(
    effective_plan,
    apply_final_normalization: bool = True,
    *,
    output_morph_names: Sequence[str] = SUPPORTED_MORPHS,
)
build_preview_data(..., *, output_morph_names: Sequence[str] = INTERNAL_VOWEL_ORDER)
build_preview_data_from_effective_shape_plan(
    effective_plan,
    *,
    output_morph_names: Sequence[str] = INTERNAL_VOWEL_ORDER,
)
empty_preview_data(*, output_morph_names: Sequence[str] = INTERNAL_VOWEL_ORDER)
build_output_diagnostics_snapshot_from_ui_state(
    ...,
    *,
    output_morph_names: Sequence[str] = SUPPORTED_MORPHS,
)
```

`output_morph_names`を省略した場合だけ既存の日本語tupleを使う。明示的な`None`は省略扱いにせずrejectする。coreのbuilt-in factoryがexactな5要素・順序・重複・known mappingを検証し、writer / Preview / diagnosticsは受け取ったtupleのshape、重複、各frameのmembershipを境界で検証する。この責務分割により、built-in定義の重複と、未検証tupleの黙認を同時に防ぐ。

### 6.3 default and failure contract

- writer、effective-shape adapter、Preview、diagnosticsのset入力省略時は日本語setとする。
- unknown set ID、`None`、要素数5以外、空文字、制御文字、重複、semantic orderと対応しないtuple、Latin以外の名前は、coreのbuilt-in factoryまたはconsumer境界でfail closedする。consumer境界のexplicit tupleは、factory検証済み`MorphNameSet.output_names`に由来することを契約上の前提とする。
- `bool`を数値や文字列として受け入れない既存validation方針を維持する。
- validation / mapping失敗時、部分的にJapaneseへfallbackして出力しない。呼び出し側が明示的に日本語setを選択した場合だけ日本語出力となる。
- B4のstartup unresolved profile fallbackはB4が所有する。B2のpure mapping APIはunknown setをapplication defaultへ暗黙変換しない。

## 7. 対象ファイル

### 7.1 実装対象候補

| ファイル | B2での責務 |
|---|---|
| `src/core/morph_name_sets.py` | built-in setの正本、immutable DTO、set ID / order / duplicate / unsupported input validation、semantic-to-output mapping |
| `src/vmd_writer/writer.py` | explicit output name tupleの受け口、semantic final normalization後のmapping、serializerのallow-list。既存defaultは不変 |
| `src/vmd_writer/effective_shape_adapter.py` | effective shapeからsemantic framesを作り、final normalization後にexplicit setへmappingするadapter |
| `src/vmd_writer/__init__.py` | existing writer exportsの互換維持。core-dependent adapter / resolverをre-exportしないことの確認 |
| `src/core/preview_transform.py` | `PreviewRow.display_name` / `PreviewSegment.display_name`によるsemantic keyとdisplay nameの分離、explicit output namesを使うPreview projection |
| `src/core/preview_hit_test.py` | semantic lane / hit-test contractの維持確認。必要な変更はdisplay mappingを持ち込まない限定変更だけとする |
| `src/gui_wx/preview_panel.py` | row labelとselected summaryをdisplay nameへ切替し、`PreviewModel.clear`のexplicit output-name境界を追加。hit-test、selection identity、color keyはsemantic keyのまま維持 |
| `src/core/output_diagnostics.py` | mapped effective morph nameの明示allow-list validation。`EffectiveWriterInput.allowed_morph_names`を追加するが、既存3引数構築を壊さず、fingerprint payload構造とschema IDは変更しない |
| `src/gui_wx/output_diagnostics_adapter.py` | effective-shape adapterへexplicit output namesを渡し、diagnostics DTOへmapped framesを渡す境界 |

### 7.2 境界確認のみのファイル

- `src/core/__init__.py`: `morph_name_sets`をre-exportしてimport side effectやcycleを増やさない。必要な公開境界だけを実装時に確認する。
- `src/core/effective_shape_plan.py`: semantic key、normalization contract、frame値、range、zero frameの変更がないことを確認する。
- `src/core/text_processing.py`: `VOWELS`とsemantic token生成の変更がないことを確認する。
- `src/core/diagnostic_report.py`: B2でprofile identityを追加しない。mapped effective outputのsummary/report統合はB4のdiagnostics state planで確定する。
- `src/core/pipeline.py`、`src/gui_wx/main_frame.py`: B2 adapterのexplicit inputを受けられる境界を確認する。active profileのruntime wiringはB4へ残す。

### 7.3 新規・更新テスト候補

実装開始時に既存testの重複と現行pathを再確認し、次の候補を確定する。

- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b2_import_boundaries.py`
- 既存の`tests/test_ms21_b2_shape_adapters.py`
- 既存の`tests/test_ms21_b3_preview_hit_test.py`
- 既存の`tests/test_ms20_b2_output_diagnostics.py`
- 既存の`tests/test_ms20_b3_output_diagnostics_adapter.py`
- 既存のPreview / writer / long-vowel / event-adjustment回帰

計画段階では、ここに挙げたproduction code、test code、GUIを作成・変更しない。

## 8. 実装方針

### 8.1 coreのbuilt-in正本

1. `src/core/morph_name_sets.py`をwriter、wxPython、diagnosticsへ依存しないleaf寄りmoduleとして作成する。
2. `MorphNameSet`をfrozen DTOとして定義し、set ID、built-in display name、ordered output namesを正規化して保持する。
3. Japanese / Latinの2 constantを定義し、unknown set IDと不正shapeを拒否する。表示名はそれぞれ`日本語5母音` / `英字5母音`で固定する。
4. semantic vowelからoutput nameへのmappingは、このmoduleのvalidated orderを使う。個別consumerへmapping tableを複製しない。
5. defaultはJapaneseだが、unknown入力をdefaultへ変換する処理と、明示的なdefault省略は区別する。

### 8.2 writer / adapter境界

1. `writer.py`のfinal normalization helpersはsemantic Japanese keyだけを扱い続ける。
2. `write_morph_vmd`は、timeline正規化、shape生成、final normalizationの後にoutput nameをmapし、serializerへ渡す。
3. `write_morph_frames_vmd`は既にresolved output nameを持つframeを受け付けるserializer境界とし、default Japaneseまたはexplicit Latin allow-listを検証する。ここでsemantic normalizationや再mappingを行わない。
4. writerのexplicit argumentはcore DTOではなく、core adapterが検証した順序付きoutput namesまたは構造的に同等なvalidated primitive contractとする。
5. `SUPPORTED_MORPHS`をruntime可変globalへ変更しない。既存private helper、legacy facade、omitted-argument callerのdefault behaviorを維持する。
6. effective-shape adapterでは、semantic frameを作成してfinal normalizationを完了してから、各frameのnameだけをsetへ置換する。frame number、value、count、sort orderはmapping前後で同一にする。
7. `src/vmd_writer/writer.py`から`src.core` / `core`へのmodule-level importを追加しない。必要なadapter importは既存のlazy boundaryを維持する。

### 8.3 Preview projection

1. `PreviewRow.vowel`、`PreviewSegment.vowel`、`PreviewEventHitRegion.vowel`はsemantic keyとして保持する。
2. `PreviewRow`と`PreviewSegment`へ、それぞれ末尾defaultの`display_name: str | None = None`を追加する。既存のsemantic `vowel`と既存positional構築を維持し、未指定時は`vowel`を表示する。
3. `empty_preview_data`、`build_preview_data`、`build_preview_data_from_effective_shape_plan`はexplicit output namesを受け、空のrowを含むsemantic orderの各row / segmentに対応する`display_name`を設定する。`build_preview_data`のempty / `None` timeline早期returnも指定setを保持し、semantic `vowel`は変更しない。set省略時は日本語nameを設定する。
4. lane順、lane数、色lookup、hit-testのvowel比較、event index、frame range、control point、selection digestは変更しない。
5. `PreviewRenderer`はrow labelに`row.display_name or row.vowel`、selected summaryに`segment.display_name or segment.vowel`を使う。内部検索、hit-test、selection identityは引き続きsemantic keyで行う。
6. `PreviewModel.clear`もkeyword-onlyの`output_morph_names`を受け、既存の省略経路は日本語表示のまま動作する。active profileのset解決とclear / rebuildへのtuple配線はB4 / B5で行い、B2ではpure projectionと既存default互換だけを実装する。

### 8.4 diagnostics / fingerprint

1. diagnosticsへ渡すeffective frameは、writerへ渡るresolved output nameを持つ。
2. `EffectiveMorphFrameInput`はshared validatorでbuilt-in Japanese / Latinのresolved output nameを受け付け、unknown nameは拒否する。`EffectiveWriterInput`には既存3引数の後ろに`allowed_morph_names: tuple[str, ...] = SUPPORTED_MORPHS`を追加し、tupleのshapeと各`EffectiveMorphFrameInput.morph_name`のmembershipをここで検証する。`allowed_morph_names`自体はfingerprint payloadへ含めない。
3. semantic tail vowel、timing plan vowel、event adjustment vowelは日本語semantic keyのままとする。
4. diagnostics adapterはeffective-shape adapterと同じexplicit output namesを、mapped frame生成と`EffectiveWriterInput.allowed_morph_names`の両方へ渡す。diagnosticsだけが別mapping tableを持たない。
5. fingerprint payloadのfield構造、canonicalization、`ms21-effective-output-v1`は変更しない。
6. set ID、profile ID、display name、preset IDをpayloadへ追加しない。B2では、既存payloadに説明identityを追加していないこと、同一mapped frameならfingerprintが変わらないこと、Japanese / Latin切替でmapped frame nameが変わった場合に既存payload値の差としてfingerprintが変わることだけを確認する。profile identityだけでfingerprintが変わらないことの統合テストは、resolved profile stateを持つB4が所有する。
7. diagnostics reportへのactive profile / set summaryの追加はB4のresolved state integrationへ委譲し、B2で未解決のprofile identityを仮表示しない。

### 8.5 import / namespace safety

- `morph_name_sets.py`はwriter、wxPython、diagnosticsをimportしない。
- writerはcoreをmodule-level importしない。
- `src/vmd_writer/__init__.py`はimport時にcoreを読むadapterをre-exportしない。
- adapter入力はprimitive tuple、属性Protocol、またはimmutable structural valueとし、`src.vmd_writer.writer`と`vmd_writer.writer`のclass identityに依存しない。
- fresh processでcore-first、writer-first、adapter-first、mixed namespaceを個別に起動し、各processのexit code 0を確認する。

## 9. 詳細ステップ

### Step 1: 実装開始時のfresh確認

- branch、HEAD、worktree、既存差分を一つずつ確認する。
- B1 plan、Block Breakdown、Roadmap、Indexのstatusを確認する。
- 7章の候補ファイルが存在すること、現行signature、既存testの重複を再確認する。
- `presets.json` / `MMD_AutoLipTool.ini`を読み書き対象にしない。

### Step 2: core set contractを実装

- `MorphNameSet`とbuilt-in two constantsを追加する。
- set ID、exact order、duplicate、empty、unsupported typeのvalidationを実装する。
- semantic keyとの位置対応を検証する。
- direct importで利用できるleaf moduleとし、`src/core/__init__.py`の広域re-exportは避ける。

### Step 3: writer primitive boundaryを実装

- existing Japanese constantsとprivate normalizationの挙動を変更しない。
- `write_morph_vmd`へkeyword-onlyの`output_morph_names`を追加し、normalization後の一回mappingを実装する。既存の`apply_final_normalization`などの引数順は変えない。
- `write_morph_frames_vmd`へkeyword-onlyの`output_morph_names`を追加し、resolved output nameのstructural allow-list境界を実装する。consumerはcore built-in tableを複製せず、検証済みtupleのshape・duplicate・frame membershipだけを再確認する。
- invalid output nameをserializerへ通さず、partial fileを残さない既存のvalidation順序を維持する。
- dummy writer、legacy wrapper、pipelineのomitted pathがJapaneseのままであることを確認する。

### Step 4: effective-shape adapterを実装

- effective planからsemantic framesを組み立てる処理を維持する。
- final normalizationを先に実行し、返却直前にexplicit output namesを一度だけ適用する。
- `build_morph_frames_from_effective_shape_plan`では既存の`apply_final_normalization` positional引数を維持し、`output_morph_names`だけをkeyword-onlyで追加する。
- `apply_final_normalization=False`の既存テストでも、semantic frameを再正規化せず、mappingだけが一度行われることを定義する。
- structural plan、`src.*` / top-level混在の入力でclass identityを参照しない。

### Step 5: Preview display projectionを実装

- `PreviewRow.display_name` / `PreviewSegment.display_name`を追加し、semantic `vowel`との役割を分離する。
- `empty_preview_data`、effective plan path、legacy timeline pathのすべてで日本語default / Latin explicitを検証する。
- wx rendererのlane labelとselected summaryだけをdisplay nameへ切り替える。`PreviewEventHitRegion`はsemantic keyだけを保持し、display mappingを持ち込まない。
- hit-test region、lane calculation、selection identity、frame metadataは既存semantic contractのままにする。

### Step 6: diagnostics adapterを実装

- mapped effective frame nameをDTOへ渡すexplicit pathを追加し、同じtupleを`EffectiveWriterInput.allowed_morph_names`へ渡す。
- Japanese defaultとLatin explicitのvalidationを確認する。`EffectiveMorphFrameInput`はshared built-in-name validator、`EffectiveWriterInput`はallowed tuple membershipを担当し、`EffectiveTailInput.vowel`は日本語semantic validatorのままとする。
- malformed set、duplicate、missing order、unresolved output nameをdiagnostics failureへ閉じ込め、current stateを部分変更しない。
- fingerprintはmapped frame名差分だけで変わることを確認する。

### Step 7: B2専用テストと既存回帰を追加・実行

- 11章の最小テストを追加し、まずB2専用、次に既存Preview / diagnostics / writer、最後にMS22関連回帰を実行する。
- pytestのpass表示だけで判定せず、各commandのprocess exit code 0を確認する。
- `compileall src tests`、`git diff --check`、必要に応じて`git diff --cached --check`を実行する。

### Step 8: diff / scope self-audit

- B2対象外のprofile store、INI、state、UI flow、batch、package、dependencyが混入していないか確認する。
- semantic key、frame value、frame number、30fps、VMD serializationが変わっていないか確認する。
- Japanese omitted pathの差分をbefore / afterで確認する。
- import boundaryをfresh processで再実行し、全process exit codeを記録する。

## 10. 状態遷移 / データ契約

### 10.1 Mapping flow

```text
semantic timing / effective shape
        |
        v
semantic shape expansion
        |
        v
final semantic normalization
        |
        v
validated MorphNameSet / ordered output names
        |
        v
output frame name mapping (exactly once)
        |
        +--> VMD serializer
        +--> Preview display projection
        +--> diagnostics effective writer input
```

mapping前のsemantic frameとmapping後のresolved output frameは、name以外の次の値を同一にする。

- frame number
- value
- frame count
- sort order
- event / shape provenance
- 30fps conversion

### 10.2 Consumer contract

| Consumer | semantic key | output / display name | B2入力 |
|---|---|---|---|
| shape plan / normalization | 日本語5母音 | 持たない | 既存semantic contract |
| writer normalization | 日本語5母音 | normalization後に一回解決 | ordered output names |
| VMD serializer | 直接保持しない | resolved name | Japanese defaultまたはexplicit allow-list |
| Preview row / hit-test | 日本語5母音 | row labelのみset依存 | ordered output names |
| Preview selected summary | semanticでselection | display name | ordered output names |
| diagnostics effective frame | tail / timingはsemantic | `morph_name`はresolved name | ordered output names |
| fingerprint | payload構造不変 | resolved frame nameを既存fieldへ格納 | mapped effective frames |

### 10.3 Failure behavior

| 入力 | 期待結果 |
|---|---|
| omitted set | 日本語setで既存互換 |
| valid Japanese | 日本語frame / label |
| valid Latin | `A / I / U / E / O`へnameだけ置換 |
| unknown set ID | ValueError等でfail closed。implicit Japanese fallbackなし |
| duplicate output names | reject。writer / Preview / diagnosticsへ渡さない |
| missing / wrong-order names | reject |
| unresolved output frame name | serializer / diagnostics validationでreject |
| normalization後の再mapping要求 | 二重mappingとしてrejectまたは内部で発生させない |

## 11. テスト方針

### 11.1 B2専用テスト

`tests/test_ms23_b2_morph_name_sets.py`では次を検証する。

- exact stable IDが2つだけ存在すること
- built-in display nameが日本語`日本語5母音` / Latin`英字5母音`で安定していること
- Japanese mappingが`あ / い / う / え / お`であること
- Latin mappingが`A / I / U / E / O`であること
- default省略時がJapaneseであること
- unknown ID、wrong length、empty、duplicate、missing order、unsupported valueを拒否すること
- mappingがsemantic keyの順序を変更しないこと

`tests/test_ms23_b2_morph_name_adapters.py`では次を検証する。

- writerのJapanese omitted pathが既存VMD frame nameと一致すること
- Latin explicit pathでframe number、value、count、sort orderが不変でnameだけが変わること
- `write_morph_vmd`がfinal normalization後に一度だけmappingすること
- effective-shape adapterのJapanese / Latin出力が同じsemantic planから得られること
- long-vowel resolver、event adjustment、hold、softness、protected range、required zero、open-stateの結果がset切替で不変であること
- Preview row / segmentのsemantic keyとhit regionが不変で、label / selected summaryだけが切り替わること
- `empty_preview_data`、空timelineのearly return、`PreviewModel.clear`でもLatin display nameが日本語へ戻らないこと
- diagnostics effective frameがresolved output nameを持ち、unresolved nameがfail closedすること
- mapped name差分でfingerprintが変わり、B2がprofile / set説明identityをpayloadへ追加しないこと。profile identityだけでfingerprintが変わらないことはB4のresolved stateテストで検証する。
- 30fps、VMD byteのframe count / value / orderが既存契約と一致すること

### 11.2 import boundaryテスト

`tests/test_ms23_b2_import_boundaries.py`で、各々を別processとして検証する。

1. core module first → writer → effective adapter
2. writer first → core module → effective adapter
3. effective adapter first → writer → core module
4. `src.*` / top-level mixed namespace
5. writer / adapter間でDTOのclass identityを共有せず、ordered tuple、属性Protocol、またはimmutable structural inputだけで処理できること

各processのpass表示とexit code 0を記録し、module-level import cycle、duplicate built-in table、class identity依存がないことを確認する。

### 11.3 既存回帰

最小順に次を実行する。実装時の現行pathを確認し、存在しないtest名はそのまま使用しない。

1. B2専用test
2. `tests/test_ms21_b2_shape_adapters.py`
3. Preview transform / hit-test / wx Preview selection関連
4. `tests/test_ms20_b2_output_diagnostics.py`、`tests/test_ms20_b3_output_diagnostics_adapter.py`、`tests/test_ms20_b6_diagnostic_report.py`
5. writer grouping / intervals / zero guard / multipoint / peak value関連
6. MS21 / MS22のlong-vowel、event adjustment、effective output identity関連
7. MS23開始前の基盤回帰、および必要なfull suite

既存日本語回帰がpassすることを前提とし、Latin専用テストの追加で既存期待値を緩めない。

## 12. 受け入れ条件

- built-in setが正確に2種類で、stable IDとexact mappingがB1 / Roadmapと一致する。
- built-in display nameがB1 / Block Breakdownと一致し、B4がIDから別表を再構築せず`MorphNameSet`から取得できる。
- set validationがunknown、duplicate、missing order、wrong length、unsupported inputをfail closedする。
- writer、Preview、diagnosticsがconsumerごとの独自mapping tableを持たず、同じvalidated ordered namesを使う。
- writerの引数省略時は日本語5母音、既存frame文字列、30fps、既存VMD形式が維持される。
- Latin explicit pathでは5つのoutput nameが`A / I / U / E / O`となる。
- Japanese / Latin切替でframe number、value、count、sort order、event provenanceが不変である。
- semantic final normalizationがmappingより先に完了し、mapping後にnormalizationが再実行されない。
- long-vowel resolver、event adjustment、hold、softness、protected range、required zero、open-stateをset切替で変更しない。
- Previewのlane order、hit-test、event selection、semantic vowel、frame metadataを変更せず、表示nameだけをsetに応じて切り替える。
- Previewのempty row、empty timeline、clear後も指定setのdisplay nameを保持し、省略時は既存日本語表示を維持する。
- diagnosticsのeffective frameがwriterのresolved output nameと一致し、`EffectiveWriterInput.allowed_morph_names`が同じtupleを保持する。
- fingerprint payload構造と`ms21-effective-output-v1`を維持し、B2ではmapped frame name変更だけが既存payload値の差になることを表す。profile identity単独の不変性はB4で受け入れる。
- core-first、writer-first、adapter-first、mixed namespaceのfresh-process importがすべてprocess exit code 0である。
- model profile、profiles.json、INI、preset、startup、state、history、batch、packageにB2実装の変更が混入していない。
- B2専用および関連回帰のpass表示とprocess exit codeを別々に記録できる。
- `compileall src tests`と`git diff --check`がprocess exit code 0である。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| Latin nameをsemantic normalizationへ混ぜてopen-stateやzero guardが壊れる | normalizationは日本語semantic keyで完了し、mappingをserializer直前の一回に限定する |
| writerがcoreをimportして循環する | writerへcore DTOを渡さず、ordered primitive namesを明示入力する。module-level逆importを禁止する |
| `src.*` / top-level二重loadでDTO identityが分裂する | Protocol / tuple / immutable structural inputを使い、class identityをassertしない |
| Preview label変更でhit-testが別laneを選ぶ | semantic `vowel`とdisplay nameを別fieldにし、hit-testはsemantic orderだけを参照する |
| Latin set選択後のempty / clear Previewが日本語表示へ戻る | `empty_preview_data`と`PreviewModel.clear`へkeyword-onlyのoutput namesを渡せる境界を追加し、B4 / B5のresolved tuple配線まで日本語defaultを維持する |
| diagnosticsがLatin frameを日本語validatorで拒否する | explicit allow-listをEffectiveWriterInput境界へ渡し、tail / timing semantic keyは別validatorで維持する |
| mapping tableがconsumerへ複製される | built-in正本を`morph_name_sets.py`へ集約し、consumerはvalidated ordered namesだけを受け取る |
| writer direct APIへ未検証の名前tupleが流入する | omitted defaultはJapanese tuple、explicit入力は`MorphNameSet.output_names`由来を契約とし、consumer境界では`None`、5要素以外、duplicate、empty、frame membershipを検証する。built-in ID / exact mappingはcore factoryだけが検証する |
| fingerprintへset IDを直接追加して無用なdirty化を起こす | payload構造を変更せず、resolved effective frame nameだけを既存fieldへ格納する |
| B2でB4のprofile stateまで先行実装する | B2はpure mapping / explicit adaptersだけに限定し、active resolution・startup・historyはB4へ残す |
| 既存日本語回帰をLatin追加のため緩める | 日本語既存testを変更せず、Latinは専用testとして追加し、全回帰を別に実行する |

## 14. Codex実装時の注意

- 実装開始前に本planとBlock Breakdownをfresh read-onlyで再照合し、候補ファイルを現行codeへ合わせる。
- 一つのshell commandを実行して結果を確認してから次へ進む。parallel、pipeline、chained commandは使用しない。
- `presets.json`、`MMD_AutoLipTool.ini`をstage対象にせず、B2では`profiles.json`も作成しない。
- Qt / PySide6、外部クラウドASR、外部音声送信、background通信、Whisper自動downloadを追加しない。
- VMD形式、30fps、既存音声契約、既存固定日本語defaultを変更しない。
- implementation diffをテスト前に監査し、B3 / B4 / B5 / MS25 / MS26 / MS27の作業を混入させない。
- GUIの手動確認は実際に実施した場合だけ記録し、ユーザー報告とCodex自身の実行結果を混同しない。
- 実装後は、変更ファイル、B2実装内容、テスト結果、仕様逸脱、残課題、B3 / B4へのhandoffを日本語で報告する。
