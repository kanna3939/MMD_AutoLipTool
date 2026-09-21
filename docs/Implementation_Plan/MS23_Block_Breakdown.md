# MS23 Block Breakdown

## 1. 文書情報

- 文書名: MS23 Model Profiles / Built-in Morph Name Sets Block Breakdown
- 作成日: 2026-08-12
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時点のbranch: `main`
- 計画作成時点のHEAD: `4e85682 Finalize MS22-B7 closeout audit`
- 現在のbranch: `feature/MS23-implementation`
- 実装開始時点のHEAD: `229ad3d Document MS23-B6 implementation plan`
- B5計画作成時HEAD: `cc23666 Implement MS23-B4B wx teardown repair`
- 現在の前提: 分岐元は`main`の`4e85682`。MS23-B1はCompleted / Contract Fixed、MS23-B2〜B4は実装・自動検証済み、MS23-B4Bはwx test teardown修正と自動検証を完了した。MS23-B5は実装、自動検証、ユーザー報告による手動GUI確認を完了した。MS23-B6は実装・自動検証・ユーザー報告による限定手動GUI確認を完了した。2026-08-20にMS23-B7 Closeout監査を実施し、P1 / P2 / P3なしのA判定へ同期した。実MMD確認はMS26へdeferredである。
- 前提となる完了状態: MS22-B7 Closeout Audit A
- 文書ステータス: Reviewed / Completed / Decision Gates Adopted / Content Sync Applied / Contract Fixed / MS23-B4 Implemented・Dedicated・Related Automated Verification Passed / MS23-B4B Implemented・P2-P3 Corrections Applied・Automated Verification Passed / MS23-B5 Implemented・Automated Verification Passed・Manual GUI Verification Passed (User Report) / MS23-B6 Implemented・Automated Verification Passed・Manual GUI Verification Passed (User Report) / MS23-B7 Closeout Audit Executed・A
- レビュー日: 2026-08-12、P2補正日: 2026-08-13、P2/P3再補正日: 2026-08-15
- 実装開始条件: MS23-B1の契約ゲート確定、および各Block開始時のImplementation Planレビュー完了

この文書はMS23全体の責務、依存順、契約、候補ファイル、テスト境界を固定する。各Blockの実装開始時には、現在のGit状態と実コードを再確認したうえで、必要な`MS23-Bx_Implementation_Plan.md`を別途作成する。

## 2. 現在状態と根拠

### 2.1 MS22の完了契約

- MS22-B1〜B6は実装・関連検証済み、MS22-B7はCloseout監査済みでA判定である。
- MS22の自動検証結果は、direct regression 93件、基盤回帰185件、MS21回帰138件、MS17 / MS19 / MS20回帰158件、B4 / B5 / splash組合せ18件、全体713件である。
- `compileall src tests` と `git diff --check` はprocess exit code 0である。
- B4〜B6のGUI確認はユーザー報告の範囲で通過している。Codex自身の手動GUI実行結果とは扱わない。
- 実MMDによるVMD / WAV読み込みとリップ同期は未確認であり、MS26に残る。
- `presets.json` と `MMD_AutoLipTool.ini` はrootのruntime user dataであり、計画・実装・検証でステージしない。

### 2.2 Roadmapで確認できるMS23の定義

`docs/MS20_and_Beyond_Roadmap.md`では、MS23をMS22依存の「モデル別数値設定と組み込みモーフ名セット」の導入としている。確認できる範囲は次のとおりである。

- `profiles.json`はversionedな単一JSONで、既存INIと同じ保存場所に置き、初期上限を100件とする。
- `morph_upper_limit`、hold、softness、標準プリセットなど、既存の設定契約をモデル用途ごとに再利用する。
- presetとmodel profileの責務を分離する。
- 組み込みセットとして日本語`あ / い / う / え / お`と英字`A / I / U / E / O`を持つ。
- writer、Preview、診断、一括出力で同じモーフ名契約を使用する。ただし一括出力の実装自体はMS25であり、MS23ではwriter、Preview、diagnosticsの共有resolver契約までを用意する。
- 優先順位は`イベント補正 > model profile > preset > application default`である。
- profile未選択時は、既存どおり日本語モーフ名を使用する。
- 英字セットは英語音声認識・英語音素処理ではなく、既存の日本語5母音イベントの出力名を切り替える機能である。

`docs/MS20_and_Beyond_Index.md`およびMS22文書には、過去のbranch名やMS22-B7実装前のHEADが残る箇所がある。現行branchとHEADについては、この文書の冒頭に記載したlive Git状態を正本とする。過去の記録をMS22未完了の根拠にはしない。

### 2.3 計画レビュー結果

2026-08-12に本Block Breakdownを現行code、test、Roadmap、MS22完了契約へ再照合した。判定は、初回案のままでは要修正、以下の文書修正後はMS23-B1計画作成へ条件付き着手可である。MS23 production code、test code、GUIの実装着手はまだ許可しない。

- P1: 0件
- P2: 7件。analysis parameterとoutput historyの責務混在、missing preset / deleted profileのfallback未確定、fingerprintへの設定identity混入候補、`profiles.json`のruntime ignore不足、event adjustmentの実フィールドとの対応不足、B2〜B4 ownershipとMS25先行抽象化、routing未同期を本改訂で解消した。
- P3: 2件。JSON例とnullable契約の不一致、UIへの過剰なfield-source表示要求を本改訂で解消した。
- 2026-08-12にユーザーはD1を採用した。`default_preset_id`はpreset値の複製ではなくstable referenceとし、参照先presetをbaseline、profileのnon-null fieldをoverrideとして解決する。別preset Apply後もnon-null overrideを維持し、nullable fieldだけが新presetを継承する。
- MS23-B1 Implementation Planを同日に作成した。2026-08-13の再チェックでP2 5件を検出し、import / mixed namespace、normalize-before-map、別preset Apply後のruntime baseline、commit前後failure、baseline非zero終了の計画を補正した。
- D1Aとして、profile Apply直後は`default_preset_id`、別preset Apply後は専用INIキー`active_profile_baseline_preset_id`をcurrent runtime baselineとして再起動でも優先する。active profile中は既存`active_preset_id=None`とし、preset単独時のCustom正規化は変更しない。
- 初回のwx baselineは19件pass表示後にexit code 1だったが、関数単位の切り分け、全8件、元の19件commandをtest変更なしで再実行し、いずれもexit code 0を確認した。非zeroが再現して未解消ならB1をContract Fixedにしない。
- 同日、ユーザーはD2〜D5をすべて推奨案Aで採用した。参照中presetのdelete guard、active profile mutation guard、startup unresolved fallback、fingerprint schemaのdecision gateは解消済みである。
- 同日のB1実装前チェックでactive runtime baseline preset mutationとactive profile中global direct editのP2 2件を検出した。ユーザーの解消指示に基づき、D6としてactive runtime baseline presetのvalue update / deleteを拒否してsettings同値Renameだけ許可し、D7としてactive profile中のnon-no-op global direct editを拒否する契約を採用した。no-profile時のMS22 preset / direct edit契約、event adjustment、別preset Applyは変更しない。
- 2026-08-15の再チェックでは、startup seam testが実スプラッシュを生成してaccess violationによるexit code 1を起こすP2を確認した。splash専用testとの責務を分離するtest isolationを補正し、同一19件commandをpass表示・exit code 0へ復帰させた。あわせてlive Git記述、read-only code対象、P1/P2/P3 gate表記のP3を文書同期で解消した。MS23 featureのproduction code、test code、GUI実装は開始していない。

### 2.4 現行コードで確認した主な境界

- `src/core/effective_shape_plan.py`、`src/core/text_processing.py`、`src/core/preview_transform.py`は、既存の日本語5母音を内部の意味・順序として扱う。
- `src/vmd_writer/writer.py`は、出力可能なモーフ名を日本語5種に固定し、Shift-JIS VMD出力を行う。
- `src/vmd_writer/effective_shape_adapter.py`は`EffectiveShapePlan`からwriter用frameを作る。
- `src/core/__init__.py -> pipeline -> src/vmd_writer -> writer`の依存があるため、writerからcoreへのmodule-level逆importは循環候補になる。
- `src.vmd_writer.writer`とtop-level `vmd_writer.writer`は別moduleとしてloadされ得るため、class identity一致を前提にしない。
- `src/core/output_diagnostics.py`と`src/gui_wx/output_diagnostics_adapter.py`は、診断・fingerprint用のモーフ名を日本語5種として検証する。
- `src/gui_wx/preview_panel.py`とPreview関連transform / hit-testは、日本語5母音をlaneの意味と表示ラベルに使用する。
- `src/core/generation_presets.py`は`presets.json`、schema version、上限100件、built-in preset、atomic replace、壊れたJSON時のfailure方針を既に持つ。
- `src/core/settings_store.py`はINIを既定の保存先とし、`morph_upper_limit`とgeneration settings、active preset IDを保存する。
- `src/core/output_edit_state.py`、`src/gui_wx/ui_state.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/main_frame.py`は、generation settingsとactive presetをstate、history、startup、save、diagnosticsへ渡す。
- INI保存はin-memory state commit後であり、save failure時もcurrent state / historyをrollbackしないMS22契約がある。
- `src/gui_wx/right_pane.py`にはモデルプロファイルtabのplaceholderがあるが、profileの保存・選択・適用は未実装である。

## 3. 背景

MS22で長音、generation settings、preset、output state、history、diagnostics、lifecycleが整理された。MS23はその出力契約をモデル用途単位で再利用する段階である。一方、現在のモーフ名はcore、Preview、writer、診断に個別の日本語固定として存在するため、文字列を一括置換すると次の問題が起こる。

- 長音・母音の内部意味と、MMDへ書き出す名前が混ざる。
- Previewのlane / hit-testとwriterの出力が別の命名判断を持つ。
- 診断fingerprintが実際のVMD出力名を表さなくなる。
- 既存日本語出力の後方互換性を、不要なcore変更で壊す。

そのため、MS23では内部の母音意味を維持し、出力・表示時に明示的な組み込みモーフ名セットを解決する境界を設ける。

## 4. 目的

次の状態を、MS24以降が利用できる検証可能な契約として実現する。

1. モデル用途ごとの数値設定とモーフ名セットを、versioned `profiles.json`で保存・再利用できる。
2. presetは汎用的な生成設定、profileはモデル用途に固有の設定・出力名セットという責務分離を保つ。
3. 日本語セットを既定としたまま、英字セットへ明示的に切り替えられる。
4. Preview、writer、診断、将来の一括出力が、同じresolved morph-name contractを使用する。
5. `morph_upper_limit`変更時の再解析境界、hold / softness / long-vowel mode変更時のoutput-only境界、イベント補正の優先順位をMS22と矛盾なく維持する。

## 5. In Scope

- `profiles.json`のschema version、100件上限、atomic save、broken / future schema failure方針
- model profileの作成、選択、適用、更新、削除、startup復元
- profileの保存先を既存INIと同じディレクトリにすること
- profileの数値設定としての`morph_upper_limit`、closing hold、closing softness、long-vowel modeの再利用
- profileから参照するpresetの扱いと、presetとの責務分離
- 組み込みモーフ名セットの固定定義
  - 日本語: `あ / い / う / え / お`
  - 英字: `A / I / U / E / O`
- semantic vowelとoutput morph nameのmapping DTO / resolver
- writer、Preview、診断、fingerprintが共有するresolved morph-name contract
- active profile selection、analysis parameter、output-only generation state、history、startup / save、diagnosticsの責務分離
- 既存日本語VMD出力と既存preset動作の回帰確認
- MS23関連のREADME、データ契約、GUI仕様、VMD仕様、エラー仕様の同期

## 6. Out of Scope

- PMX / PMD読込、モデルファイル解析、モデル名の自動取得
- 任意モーフ名mapping、ユーザー定義モーフセット、追加表情モーフ
- 英語音声認識、英語音素処理、Whisperモデル選択（MS24）
- 一括出力機能そのもの（MS25）
- MS25だけを目的とするbatch DTO、adapter、package生成処理の先行実装
- 実MMDによるVMD / WAV読み込みとリップ同期確認（MS26）
- packaging / release readiness（MS27）
- VMD形式、30fps、WAV契約の変更
- Qt / PySide6の復活、外部ASR、外部音声送信、background通信、Whisper自動download
- 既存の長音resolver、event adjustment、history機構の広範な再設計

## 7. MS23共通設計契約

### 7.1 semantic vowelと出力名の分離

既存の`EffectiveShapePlan`、長音resolver、event adjustment、Preview hit-testが扱う母音意味は、MS23で英字へ置換しない。現在の日本語5母音をsemantic keyとして保持し、出力境界でのみ次のimmutableな名前セットを解決する。

| semantic key | 日本語セット | 英字セット |
|---|---|---|
| `あ` | `あ` | `A` |
| `い` | `い` | `I` |
| `う` | `う` | `U` |
| `え` | `え` | `E` |
| `お` | `お` | `O` |

セットはコード内のbuilt-in定義として管理し、globalな`SUPPORTED_MORPHS`を実行時に書き換えない。`EffectiveShapePlan`、protected range、required zero、5母音open-stateをsemantic keyのままfinal normalizationし、その完了後にframe名だけをresolved `MorphNameSet`へ一回mappingする。mapping後のframeをsemantic normalizationへ戻さない。writerへ渡すframe、Previewの表示名、診断のeffective outputは、同じresolved setから生成する。laneの順序、色、hit-testの意味は既存semantic keyを基準に保つ。

### 7.2 built-in morph-name set

stable IDはB1で採用済みである。名称は英語音声を意味しないことが分かるものとし、次のIDを使用する。

- `builtin:japanese-vowels` — 表示名「日本語5母音」
- `builtin:latin-vowels` — 表示名「英字5母音」

profileにはこのIDだけを保存する。`MorphNameSet`はID、表示名、immutableなordered output namesを正本として持ち、表示名は日本語setが`日本語5母音`、Latin setが`英字5母音`で固定する。mappingは日本語側を`あ / い / う / え / お`、Latin側を`A / I / U / E / O`とする。built-in setそのものは`profiles.json`へ複製しない。未知ID、欠落名、重複名、空文字は安全側で拒否する。

### 7.3 profile JSON schema（B1採用契約）

MS23-B1でexact schema contractを採用した。D1によりnullable fieldは下位layerを継承し、`default_preset_id`はrequired stable referenceとする。次のJSONは採用したplanned schema形であり、まだ実装済み仕様ではない。

```json
{
  "schema_version": 1,
  "user_profiles": [
    {
      "id": "uuid",
      "display_name": "Profile name",
      "morph_name_set_id": "builtin:japanese-vowels",
      "morph_upper_limit": null,
      "generation_overrides": {
        "closing_hold_frames": null,
        "closing_softness_frames": null,
        "long_vowel_mode": null
      },
      "default_preset_id": "builtin:standard-hold"
    }
  ]
}
```

- `schema_version`は整数1から開始する。
- `user_profiles`の初期上限は100件。0件は許可し、101件目は拒否する。
- root object、profile entry、`generation_overrides`は許可key集合の完全一致とし、unknown keyを拒否する。
- `id`は既存presetと同じcanonical lowercase UUID、`display_name`はtrim後1〜100文字、制御文字・改行拒否、duplicate拒否とする。
- `morph_name_set_id`は必須で、profile作成時の既定値は日本語セットとする。
- `morph_upper_limit`と`generation_overrides`の`null`は下位layer継承として扱う。値の型・範囲は現行settings / preset契約へ合わせる。
- `default_preset_id`はpreset設定値の複製ではなく、built-inまたはuser presetへのstable referenceとする。これはD1として採用済みである。
- `default_preset_id`が構造上有効でも参照先missingの場合はresolution errorとしてprofileを保持し、通常のschema errorとは分離する。
- D2により、profileから参照中のuser presetは参照変更までdeleteを拒否する。D3により、active user profileのvalue / set updateとdeleteはinactive化まで拒否する。D6により、active runtime baseline presetのvalue update / deleteもprofile inactive化または別baseline選択まで拒否し、settings同値Renameだけmetadata mutationとして許可する。
- D7により、active profile中のglobal generation settings / `morph_upper_limit` direct editはexact no-op以外をcommit前に拒否する。event adjustment、active profile中の別preset Apply、no-profile時の既存direct editは維持する。
- inactive profileの参照先がmissingな場合は現在状態を変えずApplyを拒否する。D4により、startupでactive profile自体がunresolvedならno-profile + Japaneseへ正規化してINI数値を保持し、valid profileの専用runtime baselineだけがunresolvedならprofile default presetへfallbackする。ID補正が発生した場合は補正後のIDだけをINIへ保存し、補正がないstartupでは保存しない。
- notes、PMX/PMD path、任意mapping、モデルファイル情報は保存しない。
- 壊れたJSON、未対応schema、重複ID / 表示名、型不正、範囲外値はuser mutationを無効にする。built-in morph set、日本語既定、既存preset、現在のINIは利用可能なままにする。
- 保存は既存presetと同様に一時ファイルを同一ディレクトリへ作成し、flush / close後にatomic replaceする。

### 7.4 設定解決と優先順位

Roadmapの`event adjustment > model profile > preset > application default`は、全layerが全fieldを所有するという意味ではない。現行実装の所有権へ対応付け、重なるfieldだけに優先順位を適用する。

| 設定・状態 | application default / INI | preset | model profile | event adjustment |
|---|---|---|---|---|
| `morph_upper_limit` | 既定値・現在値 | 所有しない | nullable override | 所有しない |
| closing hold / softness | 既定値 | baseline | non-null override | event単位override |
| long-vowel mode | `hold` | baseline | non-null override | terminal continuation event単位override |
| morph-name set | global日本語 | 所有しない | 日本語／英字set | 所有しない |
| peak / start / end / slope | base plan | 所有しない | 所有しない | event単位override |

- `morph_upper_limit`はanalysis-affecting parameterであり、`GenerationState`やevent adjustmentへ混在させない。
- morph-name setはmodel profileの責務であり、presetやevent adjustmentから変更できない。
- D1により、profileのnullable overrideは`null`のfieldだけpresetを継承し、presetが所有しないfieldはapplication default / INIを継承する。
- `EventAdjustment`の既存fieldは`peak_value`、`start_offset_frames`、`end_offset_frames`、`hold_frames`、`softness_frames`、`slope_ratio`、`long_vowel_mode`である。profileとの優先関係が生じるのはhold、softness、long-vowel modeだけであり、その他のfieldをprofileへ追加しない。
- profileのCreate / Update / Deleteと、current stateへのApplyを別transactionとする。mutationだけでanalysis、output、historyを暗黙変更しない。
- D1により、profile Applyは`default_preset_id`のpresetをbaselineとし、profileのnon-null overrideを上位layerとして解決する。別preset Apply後もnon-null overrideを維持する。missing reference、参照中preset mutation、startup復元はD2〜D4のadopted contractをB1 failure matrixへ反映する。
- D1Aにより、profile Apply直後は`active_profile_baseline_preset_id=default_preset_id`とし、active profile中に別presetをApplyした後は選択preset IDを専用runtime baselineとしてINIへ保存する。再起動時はvalidなruntime baselineを優先し、validなIDをprofile defaultへ暗黙に巻き戻さない。runtime baselineだけがunresolvedな場合に限りD4の明示fallbackを使う。active profile中は既存`active_preset_id=None`とし、no-profile復帰時だけ既存exact-match規則で再計算する。

### 7.5 state、analysis、outputの境界

- `AnalysisParameterSnapshot`は現行どおりresolved `morph_upper_limit`だけをanalysis terminal parameterとして扱う。
- `GenerationState`はbaseがなくても有効なoutput-only設定を保持する責務を維持し、resolved morph-name set identityを保持する。analysis-affecting `morph_upper_limit`は入れない。
- `active_model_profile_id`、`active_profile_baseline_preset_id`、resolution statusはcore側の専用immutable profile stateが所有する。planned moduleは`src/core/model_profile_state.py`とし、profile IDを`GenerationState`やbase-bound `OutputEditState`へ無条件に入れない。
- profile Apply前に、profile ID、preset reference、resolved upper limit、resolved `GenerationSettings`、resolved morph-name set、field source、fallback / errorを一つのimmutable resolutionとして検証する。検証失敗時はcurrent stateを変更しない。
- 既存`active_preset_id`と`GenerationPresetStore.resolve_active()`はpreset単独時のCustom正規化として維持する。active profile時はこのAPIをeffective settingsへ先行適用せず、profile-aware resolverが専用runtime baseline identityとprofile overrideを別に保持する。
- resolved `morph_upper_limit`が変わる場合、通常のparameter変更と同じくanalysisを無効化し、base-bound output historyをclearする。この操作をoutput-only Undo / Redoで元に戻せるとは扱わない。
- upper limitが変わらず、hold、softness、long-vowel mode、morph-name setだけが変わる場合は、base timing planを再解析せず、B4のprofile-aware output transactionへ統合する。Undo / Redoはoutputとprofile endpointをatomicに復元し、event-only navigationではactive profile / baselineを維持する。profile identityを変更するのはprofile transition自体のUndo / Redoだけとし、resolved値だけを理由にCustom / no-profileへ正規化しない。
- morph-name setだけが変わる場合は、semantic timing planを再解析せず、writer / Preview / diagnosticsを同じresolved setで再構築する。
- profileの表示名、profile ID、preset ID、morph-name set IDだけを理由にoutput fingerprintを変えない。実際のwriter frame、tail、writer parameter、saveability diagnosticが変わる場合だけfingerprintが変わる。
- 現行fingerprint payloadは`effective_morph_frames[].morph_name`を既に含むため、日本語から英字への変更はmapped frame名だけでfingerprintへ反映できる。D5によりcanonical payload構造を変えず、`ms21-effective-output-v1`を維持する。構造変更が必要ならB1契約からの逸脱として再判断する。
- `BasePlanIdentity`はsemantic timingのidentityとして維持し、モーフ表示名やprofile表示名を理由に不要なbase-plan invalidationを起こさない。
- workspace resetはactive profile、runtime baseline、resolved settings、resolved morph-name setを保持し、input、audio、base、output history、event selection、failure、playbackをclearする。
- validation / resolution / commit前failureは完全不変とする。commit後のINI save failureはcurrent in-memory state / historyをrollbackせず、初回通知、同一session save停止、次回起動でlast successful INIを使う既存契約を維持する。

### 7.6 writer、Preview、diagnostics、一括出力の共通契約

- writer adapterはresolved `MorphNameSet.output_names`から得た検証済みordered output namesを明示入力として受け、`EffectiveShapePlan`のsemantic final normalization後にnameだけをmappingした出力frameを作る。core DTOそのものをwriterへ越境させず、consumer境界ではtupleのshape・duplicate・frame membershipを再検証する。既存APIの既定引数は日本語セットにして、既存呼び出し元の後方互換性を保つ。
- writerはresolved set以外の名前を拒否し、英字セットを選んだときは`A / I / U / E / O`をShift-JISでVMDへ書く。VMDのheader model name（現在の`AutoLipTool`）とmodel profile名は別概念として維持する。
- writer file-I/OへLatin名を許可する場合はcore DTOをimportせず、primitiveなallowed output namesまたはvalidated frame contractをadapterから明示入力する。既存引数省略時は日本語5母音だけを許可する。
- writer module-levelから`src.core` / `core`を逆importせず、`src.vmd_writer.writer`とtop-level `vmd_writer.writer`のclass identity一致を要求しないstructural / primitive adapter境界を使う。`src/vmd_writer/__init__.py`からcore依存adapterをre-exportしない。
- Previewはsemantic laneを維持し、lane label、選択イベントの表示、表示用summaryだけをresolved setから得る。hit-testは既存semantic keyで動かす。
- diagnosticsはactive profile ID / display name、morph-name set ID / display name、resolved morph names、preset、fallback理由を同一snapshotから表示する。ただしprofileやsetの説明identityをsave-state fingerprintへ混入させない。
- MS23ではwriter、Preview、diagnosticsが共有するresolverを確定する。MS25はこのresolverを再利用する契約だけを文書化し、batch専用DTO、adapter、UI、package生成を先行実装しない。

## 8. Block一覧

| Block | 名称 | 責務 | 依存 | 実装境界 |
|---|---|---|---|---|
| MS23-B1 | Contract / Schema / Pre-check | precedence、schema、stable ID、failure、fingerprint方針を固定 | MS22 Closeout A | Completed / Decision Gates Adopted / Content Sync Applied / Contract Fixed |
| MS23-B2 | Built-in Morph Name Set / Output Mapping | built-in 2セット、semantic-to-output mapping、default日本語のadapter境界 | B1 | Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) |
| MS23-B3 | Model Profile Store / Persistence | `profiles.json`、profile DTO、INI active ID、atomic mutation、root ignore、構造検証 | B1、MS22 preset | Implemented / Automated Verification Passed。storeと永続化のみ。実MMDはMS26 |
| MS23-B4 | Resolution / State / Diagnostics | cross-store precedence、analysis / output分類、startup、history reconciliation、diagnostics、fingerprint、mutation guard | B2、B3 | Implemented / Dedicated・Related Automated Verification Passed。full Pytest終了時のwx native teardown P2はB4Bへ切り出し。profile UIはB5、実MMDはMS26 |
| MS23-B4B | wx Test Teardown / Full Pytest Exit Stability Repair | App / Frame / Controller / timer / pending callbackのtest teardown統一、active Appとの重複生成排除、full suite終了コード安定化 | B4、既存`tests/helpers.py` | Implemented / P2-P3 Corrections Applied / Automated Verification Passed。production codeは変更せず |
| MS23-B5 | Model Profile UI | RightPane選択・適用・作成・更新・削除、Busy / stale guard | B4B | Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) |
| MS23-B6 | Cross Regression / Documentation | 全経路整合、error/docs同期、回帰監査 | B5 | Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report)。次工程はB7 closeout |
| MS23-B7 | Closeout Audit | 証拠、P分類、A / B / C判定、MS24以降へのhandoff | B1〜B6 | Closeout Audit Executed / A |

## 9. Block依存関係

```text
MS23-B1 Contract / Schema / Pre-check
       ├── MS23-B2 Built-in Morph Name Set / Output Mapping
       └── MS23-B3 Model Profile Store / Persistence
                    └──────────────┐
MS23-B2 ────────────────────────────┴── MS23-B4 Resolution / State / Diagnostics
                                             └── MS23-B4B wx Test Teardown / Full Pytest Exit Stability Repair
                                                       └── MS23-B5 Model Profile UI
                                                                 └── MS23-B6 Cross Regression / Documentation
                                                                           └── MS23-B7 Closeout Audit
```

B2とB3はB1でstable ID、profile schema、failure matrix、state ownershipを固定した後に着手できる。B2は明示的な`MorphNameSet`入力と日本語default compatibilityを作るが、active profileのruntime解決は行わない。B3はstoreとINI / ignore境界を作るが、startup時のprofile / preset解決は行わない。B4が両者を統合し、B4Bがwx検証基盤の終了契約を安定化する。実際のリポジトリ作業はAGENTS.mdの方針どおり一コマンドずつ行う。B5はB4のresolutionを呼び、独自にprecedenceを再計算せず、B4Bのaggregate exit gateを通過した後に着手する。

## 10. MS23-B1: Contract / Schema / Pre-check

### 10.1 目的

MS22の完了契約を壊さず、MS23のprofile schema、built-in set ID、解決順、invalid状態、fingerprint互換方針を固定する。B1ではproduction code、test code、GUIを先行変更しない。

`docs/Implementation_Plan/MS23-B1_Implementation_Plan.md`は2026-08-12に作成済みである。D1〜D7とS2〜S7はAdopted、内容同期済みである。2026-08-15のfresh read-only B1 contract pre-checkで249件をpass表示・全command process exit code 0、P1 / P2 / P3なしと確認し、B1をCompleted / Contract Fixedへ同期した。

### 10.2 確認対象

- RoadmapのMS23 In / Out、MS22 Closeout A、MS22のpreset / state / diagnostics契約
- `generation_presets.py`のschema、上限、atomic save、broken JSON方針
- `settings_store.py`の保存先とINI additive load / save
- `effective_shape_plan.py`、writer、Preview、diagnosticsの日本語固定箇所
- `Pipeline_Data_Contract_Specification.md`、`VMD_Output_Specification.md`、`GUI_State_Theme_Specification.md`、`Error_Handling_Specification.md`

### 10.3 B1で確定する事項

- `MorphNameSet`のimmutable DTOとstable ID
- profile JSONのexact schema、nullによる継承表現、`default_preset_id`の適用動作
- active profileの選択と適用の分離
- Create / Update / Deleteがcurrent stateを暗黙変更しないmutation matrix
- `morph_upper_limit`変更時のanalysis invalidation / history clearと、output-only変更時のstate transaction
- active profile selection、resolved profile、`GenerationState`、`OutputEditState`、INIのownership表
- fingerprintへ含めるeffective outputと、含めないprofile / presetの説明identity
- broken / future / missing preset / deleted profile / startup restoreのfailure表示とfallback matrix
- MS25が再利用するresolver境界。MS25専用DTOは作成しない

### 10.4 受け入れ条件

- 各設定値について、application default、preset、profile、event adjustmentのsourceが表で説明できる。
- profile Applyの前後状態、upper limit差分、output-only差分、failure、mutation、Undo / Redoについて状態遷移表がある。
- profile未選択時に日本語出力となることが明記される。
- 英字セットが英語音声対応ではないことが明記される。
- PMX / PMD解析、任意mapping、ユーザーセット、MS24〜MS27の境界が明記される。
- B2〜B6の対象ファイル、failure、test ownershipが実在コードに対応付けられる。
- `/profiles.json`をroot runtime user dataとしてignoreし、packageへ同梱しない方針が明記される。

## 11. MS23-B2: Built-in Morph Name Set / Output Mapping

- Status: Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report) / Real-MMD Verification Deferred
- Plan: [MS23-B2 Implementation Plan](MS23-B2_Implementation_Plan.md)
- 2026-08-16に、B1で固定済みの2つのbuilt-in set、semantic key維持、normalize-before-map、writerからcore逆import禁止に従って、
  core DTO、writer / effective-shape adapter、Preview、diagnostics、import boundaryを実装した。検証済みordered output-name tupleを
  明示入力とし、既存省略時の日本語defaultを維持している。B2専用24件、関連回帰228件、full suite 738件、`compileall src tests`、
  `git diff --check`はprocess exit code 0だった。手動GUI確認はユーザー報告の範囲で通過しており、Codex自身のGUI実行結果とは扱わない。実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferred。

### 11.1 目的

既存のsemantic vowelを変更せず、writer・Preview・diagnosticsが同じ組み込みセットを使えるmapping境界を実装する。

### 11.2 主な変更候補

- 新規候補: `src/core/morph_name_sets.py`
- `src/core/__init__.py`（原則変更せずimport境界確認）
- `src/vmd_writer/writer.py`
- `src/vmd_writer/effective_shape_adapter.py`
- `src/vmd_writer/__init__.py`（core依存adapterをre-exportしない）
- `src/core/preview_transform.py`、`src/core/preview_hit_test.py`
- `src/gui_wx/preview_panel.py`
- `src/core/output_diagnostics.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- 必要最小限の`src/core/effective_shape_plan.py` / `src/core/text_processing.py`の型境界確認

### 11.3 実装契約

- built-in setは正確に2種類のみとする。
- semantic keyの順序と意味は既存の5母音から変えない。
- writer、Preview、diagnosticsがそれぞれ独自のmapping表を持たない。
- built-in setのdisplay nameをB4がIDから再構築せず、B2の`MorphNameSet`から取得する。
- invalid setや未対応名前はfail closedする。
- Previewのempty row、empty timeline、clear後もresolved setのdisplay nameを維持し、省略時は日本語defaultへ戻る。
- semantic keyでfinal normalizationを完了してからoutput nameを一回だけmappingする。mapping後にsemantic normalizationを実行しない。
- writer module-levelからcoreを逆importせず、fresh-processのimport順序と`src.*` / top-level mixed namespaceで循環・class identity依存を生じさせない。
- writerの既定呼び出しは日本語セットで、既存VMD frameの文字列と30fpsを変えない。
- Previewのlane / hit-test semanticsを壊さず、表示名のみsetに応じて変える。

### 11.4 受け入れ条件

- 日本語セットで既存のwriter / Preview / diagnostics回帰が通る。
- 英字セットで5つの出力名が正確に`A / I / U / E / O`となる。
- Japanese / Latinの切替でframe number、value、count、sort orderを変えず、output nameだけを変更する。
- writerへの未解決名、重複名、順序欠落を拒否する。
- mappingを変えても長音resolver、event adjustment、frame値、30fpsが変わらない。
- core-first、writer-first、adapter-first、mixed namespaceのfresh-process importがexit code 0である。
- model profileやUIを介さず、core adapter単体で同じmapping結果を得られる。

## 12. MS23-B3: Model Profile Store / Persistence

- Status: Implemented / Automated Verification Passed / Manual GUI Not Required / Actual-MMD Deferred to MS26
- Plan: [MS23-B3 Implementation Plan](MS23-B3_Implementation_Plan.md)

### 12.1 状態

- Status: Implemented / Automated Verification Passed / Manual GUI Not Required / Actual-MMD Deferred to MS26
- B3専用 `21 passed, 31 subtests passed`、関連回帰、full suite、`compileall src tests`、`git diff --check`をprocess exit code 0で確認した。

### 12.2 目的

profile DTO、`profiles.json`、INIのactive profile IDを、既存presetの責務と保存契約を壊さずに追加する。

### 12.3 主な変更候補

- 新規候補: `src/core/model_profiles.py`
- `src/core/settings_store.py`
- `.gitignore`
- `src/core/generation_presets.py`との共有validation境界確認

### 12.4 実装契約

- `profiles.json`はINIと同じdirectoryに置く。dev実行時のrepo root、frozen実行時のexe parentという既存の保存先解決を踏襲する。
- `.gitignore`へroot限定の`/profiles.json`を追加し、既存`/presets.json`、`/MMD_AutoLipTool.ini`と同じruntime user dataとして扱う。local fileを作成した場合もstageしない。
- 100件上限、schema version、atomic replace、broken JSON時のbuilt-in / read-only fallbackを固定する。
- `morph_upper_limit`はB1どおりstrict finite float 0.0〜10.0または`null`とし、bool / int / stringを拒否する。
- built-in morph setはstoreに保存しない。
- profileの保存・更新・削除はimmutable DTOとし、失敗時に既存ファイルを壊さない。
- constructor直後はunloaded / mutation unavailableとし、初回`load()`前のlookup / Create / Update / Deleteをfile access前に拒否する。
- active profile IDはINIの追加キーとする。未知・削除済みIDのruntime正規化はB4が所有し、B3は構造validationと値のload / saveだけを提供する。
- `active_profile_baseline_preset_id`もINIの追加キーとし、既存`active_preset_id`をprofile baseline用途へ流用しない。active profile IDなしでは無効な補助identityとしてB4が正規化する。補正後のIDはB4が必要時だけINIへ保存する。
- user profileが存在しなくても、既存INI、既存preset、日本語既定で起動できる。

### 12.5 受け入れ条件

- 0、1、100、101件の境界が検証できる。
- schema version不一致、型不正、範囲外値、重複ID、profile名不正を安全に処理できる。
- load前mutationで既存JSON、missing target、memory、temporary fileを変更しない。
- save failure / replace failure後に旧JSONが保持される。
- settings path、SettingsStore注入、明示profiles path、constructor引数排他を直接testし、default `profiles.json`がINIと同じdirectoryになる。
- 新規profile、update、delete、active IDのINI round-tripが決定論的に動く。startup時のeffective resolutionはB4で検証する。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`のrepository root runtime user dataをテストが変更・stageしない。
- `git check-ignore -v profiles.json`でroot限定ruleを確認でき、subdirectoryの同名fixtureを過剰にignoreしない。

## 13. MS23-B4: Resolution / State / Diagnostics

### 13.1 目的

profile、preset、application default、event adjustmentの解決結果を一つのstate transactionと診断snapshotに統合する。

2026-08-17に[MS23-B4 Implementation Plan](MS23-B4_Implementation_Plan.md)を作成した。exact runtime state、resolution status / reason / error code、profile-aware history、startup identity-only save、mutation guard、writer / Preview / diagnostics接続を計画上で固定した。同日のplan reviewでP1なし、P2 5件、P3 1件を確認し、推奨案により、profile-aware Undo / Redo後のfull save、active profile下のhistory初期endpoint、`full > identity_only > none`のsave pending priority、guard code優先順位、exact DTO / API、local immutable candidate上のcoalescing settleをplanへ反映した。続くfresh read-only再チェックで、B1 / B3のstrict float・0.0〜10.0契約に対する`ResolvedModelProfile.morph_upper_limit`の型・上限記載不足をP2として確認したため、strict float、有限、0.0〜10.0、bool / int / string拒否をB4 planへ反映した。B4は2026-08-18に実装され、専用state / resolver、startup、history、guard、pipeline / Preview / diagnostics / report接続を自動検証済みである。B4のprofile UIはB5、実MMD確認はMS26へdeferredとする。

### 13.2 主な変更候補

- `src/core/output_edit_state.py`
- 新規候補: `src/core/model_profile_state.py`
- `src/core/event_adjustment_history.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/ui_sync_context.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/analysis_rollback.py`
- `src/core/pipeline.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/placeholder_panels.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/gui_wx/output_diagnostics_adapter.py`

`src/gui_wx/ui_sync_context.py`、`src/vmd_writer/effective_shape_adapter.py`、`src/vmd_writer/writer.py`、`src/core/preview_transform.py`はB4で再設計せず、B2 / MS22の既存契約を直接回帰する。

### 13.3 実装契約

- precedenceをUI、writer、diagnosticsで再実装せず、coreのimmutable resolved resultを共有する。
- 新規`src/core/model_profile_state.py`へ`ModelProfileResolutionStatus`、`ModelProfileState`、`ResolvedModelProfile`、`ModelProfileResolutionResult`、`StartupModelProfileResolution`、`RuntimeMutationGuardResult`を置く。statusは`no_profile / resolved / fallback_profile_default / fallback_no_profile`に固定し、fallback reasonとguard errorはB4 plan Section 8.2のcodeを正とする。
- `ResolvedModelProfile.morph_upper_limit`とresolver入力のapplication / current upperは、B1 / B3どおり`type(value) is float`、有限、`0.0 <= value <= 10.0`を満たすものだけを受理し、bool / int / stringを拒否する。
- active profile selection、active preset ID、resolved upper limit、resolved output-only settings、morph-name set identityを、B1で定めた別責務のstateへ保持する。
- profile Apply時は`default_preset_id`をruntime baselineへ初期化し、別preset Apply時はactive profileを維持して`active_profile_baseline_preset_id`だけを更新・保存する。active profile中は既存`active_preset_id=None`とし、no-profile Applyで専用baselineをclearした後に既存exact-match規則でpreset identityを再計算する。
- startupではvalidなactive profileとruntime baseline presetを一組として優先解決し、profile override付きeffective settingsを理由に既存preset resolverでCustom化しない。runtime baselineだけがunresolvedならD4どおりprofile default presetへfallbackする。補正後のbaseline IDはINIへ保存し、数値設定は保持する。
- profile Create / inactive Update / inactive Deleteはcurrent outputを暗黙変更しない。active profileのvalue / set UpdateとDeleteはinactive化まで拒否し、Renameだけをoutput identity非変更のmetadata mutationとして分離する。
- active runtime baseline presetのvalue UpdateとDeleteはprofile inactive化または別baseline選択まで拒否する。settings exact一致のRenameだけmetadata mutationとして許可し、profile / baseline ID、effective output、history、fingerprint、INIを変更しない。
- active profile中のglobal generation settings / `morph_upper_limit` direct editはexact no-op以外をcommit前に拒否する。event adjustment、別preset Apply、no-profile時のMS22 direct edit / preset identity正規化 / analysis invalidationは維持する。
- profile Applyで`morph_upper_limit`が変わる場合はanalysis guardとbase-bound history clearを使う。output-only差分だけの場合はMS22のoutput state transactionを使う。
- `OutputEditState`へprofile IDを追加せず、output history endpointへoptional `ModelProfileState` contextをpairで保持する。output-only / identity-only Undo / Redoでprofileとruntime baselineをatomicに復元し、store mutationで解決不能になったhistorical endpointは別outputへfallbackせずchainからcompactする。candidate collectionとnormalized-history candidateをraw store commit前にpreflightし、store成功後だけhistoryへ反映する。analysisを跨ぐprofile Applyをoutput historyへ混入させない。
- active profile適用済みでanalysisからhistoryを初期化する場合は初期endpointへcurrent profile stateを渡す。profile / baseline / generation identityが変わるUndo / Redo後だけMS22契約どおりfull INI saveを要求し、event-only navigationでは要求しない。save failureでも復元済みstate / historyをrollbackしない。
- stale worker result、cancel、analysis failure、rollback、reset後のactive profileを既存lifecycleと同じfailure方針で扱う。
- diagnosticsとsave-state fingerprintが、実際にwriterへ渡るresolved morph namesを使う。
- VMD保存は`AppController -> src/core/pipeline.py -> writer`のTEXTあり / voice-only、legacy / effective shape全経路へ同じexplicit output-name tupleを渡す。Preview placeholder / clearもcurrent setを保持する。
- startup ID補正はidentity keyだけをpartial saveし、同時にnumeric keyを保存しない。通常のuser operation後のfull saveとはpending stateを分離し、`full > identity_only > none`でfullをdowngradeしない。
- mutation guardは既存B3 / MS22 precondition、active lock、reference-check unavailable、referenced presetの順にcodeを決定する。pending output coalescingはlocal immutable history candidateだけでsettleし、guard / store failure時はlive pending historyを変更しない。
- Applyのcommit前failureは完全不変とし、commit後INI save failureではin-memory state / historyをrollbackしない。

### 13.4 受け入れ条件

- 各フィールドのsourceがprecedenceどおりになる。
- profileのupper limit変更で古いanalysis / Preview / outputを再利用しない。
- upper limit変更後はbase-bound Undo / Redoを利用可能と表示しない。
- profileのhold / softness / long-vowel mode変更で不要な再解析をしない。
- morph-name set変更でsemantic planを壊さず、writer / Preview / diagnosticsが同じ名前を示す。
- Latin profile中の未解析、analysis invalidation、workspace reset、error placeholderでもPreview row名が日本語へ戻らない。
- 別preset Apply後のruntime baselineとprofile non-null overrideがrestart、Undo / Redoで維持・復元される。
- startupでprofileまたはruntime baselineのID補正が発生した場合、補正後のIDがINIへ保存され、数値設定が保持される。補正がないstartupでは保存しない。
- INI save failure後もcommitted state / historyを保持し、既存の初回通知・save-disabled契約を維持する。
- profile表示名だけの変更でoutput fingerprintを不必要に変えない。
- active runtime baseline presetのvalue Update / Delete拒否でcurrent baseline identityとeffective settingsが一致し続ける。settings同値Renameはoutput historyとfingerprintを変えない。
- active profile中のnon-no-op global direct editを拒否しても、event adjustment、別preset Apply、no-profile時のdirect editは既存契約どおり動作する。
- missing preset、active profileへのupdate / delete要求、broken profile JSONがB1のfailure matrixどおりcurrent stateを保持またはApplyを拒否し、診断に理由を残す。
- profile store unavailable時は参照不在を証明できないためuser preset Deleteをfail closedにし、built-in preset利用と既存current outputは維持する。

2026-08-18にB4を実装した。B4専用12件、関連回帰52件はprocess exit code 0である。full suiteは771件・57 subtestsがsummaryまで完走し、B4追加wxテストを除外してもexit code 1を再現したため、既存wx終了処理系のknown baselineとしてpass表示とprocess exit codeを分離記録した。`compileall src tests`と`git diff --check`はprocess exit code 0である。profile UIの手動確認はB5、実MMD確認はMS26へdeferredとする。これはB4B実装前の履歴である。

## 13.5 MS23-B4B: wx Test Teardown / Full Pytest Exit Stability Repair

### 13.5.1 目的

MS23-B4の機能検証結果を変更せず、wxテスト終了時のnative object lifetimeを決定論化し、pass表示だけでなくwx aggregateとfull suiteのprocess exit code 0を回復する。B4Bはtest-harness firstとし、production codeは変更しない。同じaccess violationがtest teardown統一後も再現した場合は原因を記録して停止し、別planまたは明示承認へ引き継ぐ。

### 13.5.2 現在確認できるP2

- full suiteは`771 passed, 57 subtests passed`まで完走したがprocess exit code 1である。
- `-X faulthandler`ではGarbage Collection中の`Windows fatal exception: access violation`を確認した。
- `-k "not wx"`はexit code 0、`-k "wx"`は同じnative exceptionでexit code 1である。
- `tests/helpers.py`の`destroy_wx_app()`を使わないlegacy wx testsに、frame-only teardown、GC依存、App所有権不明、重複`wx.App()`生成が残る。

### 13.5.3 実装契約

- 同時に複数のactiveな`wx.App`を生成しない。`wx.App.Get()`が既存Appを返す場合は再利用し、前のowned Appをteardownした後の順次生成は許可する。
- 既存Appを再利用した場合はownershipをfalseとして保持し、Appを無条件に破棄しない。
- controller、analysis job、timer、pending callbackをFrame破棄前に停止・処理する。
- pending eventを対象Frameが生きている間に処理し、Frame破棄後に対象へ送らない。
- 所有Appだけを明示破棄し、再利用Appを無条件に破棄しない。
- Controllerのpending saveはtemporary storeへ隔離し、root `profiles.json` / `presets.json` / `MMD_AutoLipTool.ini`を更新しない。
- MS21〜MS22のdirect `app.Destroy()` / `frame.Destroy()`経路も監査対象とし、既存helper利用済みとは仮定しない。
- `destroy_wx_app()`を共通入口とし、必要なhelper補正はidempotent・部分初期化安全に限定する。
- B4のproduction state、profile precedence、VMD、Preview、diagnostics、fingerprint、runtime user dataを変更しない。

### 13.5.4 受け入れ条件

- 既知MS14-B1 + MS14-B5再現command、`-k "wx"`、full suiteがそれぞれprocess exit code 0になる。
- wx aggregateとfull suiteを2回連続で実行してもaccess violationが発生しない。
- B4専用12件、関連52件、non-wx回帰、`compileall`、`git diff --check`がexit code 0である。
- test削除、skip追加、assertion弱化、B4機能契約変更がない。
- 既知再現commandは`.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_wx_ms14_b1_ui.py tests\test_wx_ms14_b5_export.py`として固定する。

### 13.5.5 状態

2026-08-18のB4B plan reviewでP2 4件、P3 1件を確認した。active Appの定義を同時存在禁止へ限定し、MS16 / MS21 / MS22 direct teardown、temporary storeによるroot save防止、production code変更時の停止・別plan境界、既知再現commandをplanへ補正した。これは実装前の履歴である。

同日、B4Bを実装した。`tests/helpers.py`へowned / reused Appの判別、Frame identity単位のidempotent teardown、Controller / timer / playback / pending saveの終了処理、temporary store隔離、teardown済みAppのsingleton解除、Frame破棄後のnative pending-delete処理を追加した。MS14〜MS23の対象wx testsを共通helperへ移行し、MS15-B3のsession Appをmodule scopeへ補正した。production code、GUI、runtime user dataは変更していない。既知再現10件、wx aggregate 129件×2、non-wx 644件＋57 subtests、full suite 773件＋57 subtests×2、B4/B4B専用14件、`compileall src tests`はすべてprocess exit code 0である。B4Bの手動GUI確認は不要であり、B5 profile UIとMS26 actual-MMD確認の境界は維持する。

## 14. MS23-B5: Model Profile UI

`docs/Implementation_Plan/MS23-B5_Implementation_Plan.md`を2026-08-18に作成した。現行RightPane placeholder、MS22-B5 preset UI、B3 profile store、B4 resolver / state / history / mutation guard、B4B wx teardownを再照合し、stable IDによるSelect / Apply分離、nullable override / inherit dialog、active Rename-only、Controller-side candidate ID生成、Busy / dirty / stale guard、profile / preset panel cross-syncを実装境界として固定した。計画作成baselineは41件＋31 subtestsがpass表示・process exit code 0である。同日のplan reviewでP1なし、P2 2件、P3 2件を検出し、CreateをD1準拠のinherit-first初期値へ補正した。inactive CRUDではcurrent output / profile identityを不変とし、active mutationは拒否する契約へ統一した。Create後のselected IDは既存preset UIと同じmutation前後stable ID集合差で取得し、B4 test候補名を実在ファイルへ同期した。

2026-08-19にB5を実装した。RightPane / MainFrame / AppControllerのprofile UI接続、Select / Apply分離、CRUD、Busy / stale guard、profile / preset cross-syncを実装し、削除確認結果の`wx.ID_YES`比較修正と削除後の実プルダウン再投影を回帰テストへ固定した。さらに、連続する同一母音の長音境界を補正し、`long_vowel_mode=decay`のPreview形状計画失敗を解消した。関連回帰31件、全体785件＋57 subtests、`compileall src tests`、`git diff --check`はprocess exit code 0だった。同日、ユーザーから手動GUI確認完了・問題なしの報告を受領した。Codex自身のGUI実行結果とは扱わない。旧ユーザーモデルプロファイルのruntime削除とactive profile参照のクリアは、ユーザー依頼に基づくlocal data整理として実施し、`presets.json`は変更していない。実MMD確認はMS26へdeferred、次工程はMS23-B6である。

### 14.1 目的

既存RightPaneのモデルプロファイルplaceholderを、profileの選択・適用・管理に置き換える。UIはcoreのresolved stateを表示し、独自の解決ロジックを持たない。

### 14.2 主な変更候補

- `src/gui_wx/right_pane.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/ui_sync_context.py`
- 必要に応じて`src/gui_wx/parameter_panel.py`

### 14.3 UI契約

- profileの候補選択とApplyを分離する。選択だけではoutput、analysis、historyを変更しない。
- Apply時はprofile IDとexpected revisionをimmutable requestとして送り、preset reference、override、morph-name setの解決はcore / controller側で行う。
- profile作成・更新・削除はBusy、dirty input、stale revision、store failureを既存preset UIと同じように扱う。
- panel summaryにはactive profile、active preset、morph-name set、継承／overrideの状態を表示する。全fieldへ常時source labelを追加することは必須にしない。
- morph-name setは2つのbuilt-inからのみ選ぶ。任意の文字列入力欄は追加しない。
- profileがactiveでも、profileのoverrideがpresetを上書きしていることを表示できる。
- `morph_upper_limit`が変わるprofile適用では、再解析が必要であることを既存UI契約に沿って示す。

### 14.4 受け入れ条件

- 未適用のprofile選択でcurrent outputが変わらない。
- profile Createとinactive profileのUpdate / Deleteだけではcurrent outputとactive profile identityを変更しない。active profileのvalue / set / reference UpdateとDeleteはcommit前に拒否し、必要なhistorical endpoint normalizationだけをController内部で行う。
- upper limit不変のApplyではB4のoutput-only history契約、upper limit変更時はanalysis invalidation / history clear契約に従う。
- workspace reset、startup restoreでprofile、preset、resolved settingsがB1の状態遷移表と一致する。
- broken JSONや削除済みprofileでUIがクラッシュせず、no-profile / read-only状態を説明する。
- ユーザーによるGUI確認を記録する場合、Codex自身の手動実行結果と混同しない。

## 15. MS23-B6: Cross Regression / Documentation

### 15.1 目的

writer、Preview、diagnostics、startup、save、history、preset、analysis、voice-only、resetの横断経路を同じresolved morph-name contractで監査し、仕様文書を実装状態へ同期する。

### 15.2 文書変更候補

- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md`、本Block Breakdownのstatus同期

Roadmap本文のB6状態は、自動検証とユーザー報告による限定手動GUI確認の通過を反映した`implemented`へ同期した。MS23全体のcloseout判定はB7へ残す。

### 15.3 横断確認

- TEXTあり、voice-only、empty input、analysis failure、cancel、rollback、reset
- presetの選択・適用・更新・削除とprofileの選択・適用・更新・削除の組合せ
- 日本語既定、英字profile、profile未選択への復帰
- Preview表示、writer VMD、diagnostic report、save-state fingerprint
- root runtime user dataのignore / unstaged境界
- `MMD_AutoLipTool.spec`、`build.ps1`、`docs/Release_Package_Manifest.md`が`profiles.json`をbundled default dataに含めないこと
- dependency、package、license、FFmpeg、Qt / PySide6、network境界に変更がないこと

### 15.4 実装・検証結果（2026-08-20）

- B6専用`tests/test_ms23_b6_model_profile_lifecycle.py` 12件を追加し、profile適用後のUndo / Redo、resolved morph-name contract、startup / failure / reset / guard / 長音を横断検証した。
- `UiState.redo_output_edit_state()`のprofile state再投影欠落を再現し、既存Undo側と同じ投影を既存ownerへ最小追加した。
- B6専用12件、B2〜B5基盤56件＋31 subtests、wx / B4B / B5 / 長音30件、diagnostics / writer / VMD / Preview93件、lifecycle46件＋7 subtestsはprocess exit code 0。wx aggregate136件×2、full suite797件＋57 subtests×2、`compileall src tests`、`git diff --check`もprocess exit code 0だった。
- runtime user dataはroot ignore・未追跡、package非同梱、dependency / Qt / network境界に差分なし。2026-08-20にユーザーからprofile Apply後のUndo / Redoを含む限定手動GUI確認通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。実MMD確認はMS26へdeferredである。

## 16. MS23-B7: Closeout Audit

### 16.1 目的

B1〜B6の要求、コード、テスト、ユーザーGUI確認、文書、runtime data境界を総合監査し、P1 / P2 / P3とA / B / C判定を記録する。

### 16.2 Closeout必須証拠

- MS23 direct regressionと、MS17〜MS22の関連回帰
- profile JSON境界、morph mapping、writer / Preview / diagnostics一致
- startup / save / history / stale worker / failure fallback
- `compileall src tests`、`git diff --check`
- GUI確認の実施者と範囲。Codex未実施ならそのまま記録する。
- 実MMD未確認をMS26へ残す。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のruntime user dataを誤ってcommitしていないこと。local fileが存在する場合は保持され、`git check-ignore -v`でroot限定ruleを確認できること。
- `profiles.json`をbuild成果物へ初期データとして同梱していないこと。

### 16.3 CloseoutのOut of Scope

- 実MMDでのVMD / WAV読込・同期確認
- PMX / PMD解析、任意mapping、英語音声対応
- MS24 Whisper、MS25一括出力、MS27 packaging / release

### 16.4 B7実施結果（2026-08-20）

- 監査時HEADは`b843d24 Document MS23-B7 closeout plan`、branchは`feature/MS23-implementation`、開始時worktreeはcleanだった。
- MS23 direct `82 passed, 31 subtests passed`、MS21 / MS22関連`90 passed`、diagnostics / report / Preview / writer / VMD `174 passed`、lifecycle `54 passed, 7 subtests passed`を各process exit code 0で確認した。
- wx aggregate `136 passed`を2回、full suite `797 passed, 57 subtests passed`を2回、いずれもfatalなし・process exit code 0で確認した。`compileall src tests`と`git diff --check`もexit code 0だった。
- runtime user data 3 pathはroot限定ignore・Git非追跡、package非同梱であり、dependency / package / license / network / Qt境界にMS23由来の差分はなかった。
- B2 / B5 / B6のGUI確認はユーザー報告の範囲だけを再利用し、Codex自身のmanual GUI実行は行っていない。実MMD確認はMS26へdeferredである。
- P1 / P2 / P3はいずれも0件。MS23-B7 CloseoutはAとし、次工程をMS24 Implementation Plan策定へhandoffする。MS24実装は開始しない。

## 17. 対象ファイル整理

| 責務 | 現行 / 新規候補 | 主Block | 変更理由 |
|---|---|---|---|
| morph set core / import境界 | 新規`src/core/morph_name_sets.py`、`src/core/__init__.py`、`src/vmd_writer/__init__.py` | B2 | built-in 2セットとmappingの正本。package初期化時のcore / writer循環を避ける |
| profile store / runtime ignore | 新規`src/core/model_profiles.py`、`src/core/settings_store.py`、`.gitignore` | B3 | DTO、schema、mutation、active ID round-trip、root限定ignore |
| preset reference | `src/core/generation_presets.py` | B1 / B4 | 既存stable ID lookupとCustom正規化を再利用。preset schemaは原則変更しない |
| semantic plan（関連確認） | `src/core/effective_shape_plan.py`、`src/core/text_processing.py` | B2 / B4 | semantic vowelを維持し、変更は型境界上必要な場合だけに限定する |
| writer | `src/vmd_writer/writer.py`、`src/vmd_writer/effective_shape_adapter.py` | B2 / B4 | semantic final normalization後にresolved morph namesへ一回mappingして出力。mixed namespace class identity非依存 |
| Preview | `src/core/preview_transform.py`、`src/core/preview_hit_test.py`、`src/gui_wx/preview_panel.py` | B2 / B4 | explicit set入力とruntime projectionを分け、labelのみ切替、hit-test semantics維持 |
| state / history | `src/core/output_edit_state.py`、`src/core/event_adjustment_history.py`、`src/gui_wx/ui_state.py`、`src/gui_wx/ui_sync_context.py`、`src/gui_wx/main_frame.py` | B4 | analysis-affecting selectionとoutput-only stateを分離し、必要なidentityだけをatomic統合する |
| startup | `src/gui_wx/app.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/analysis_rollback.py` | B4 | profile store ownership、startup resolution、lifecycle |
| diagnostics | `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、`src/gui_wx/output_diagnostics_adapter.py` | B2 / B4 | output名、profile、fallbackの同一snapshot化 |
| wx test lifecycle | `tests/helpers.py`、MS14〜MS20のlegacy wx tests、startup / MS21〜MS23 wx tests | B4B | App ownership、Frame / Controller / timer / pending callbackのteardown統一。既存helper利用済み経路は変更せず回帰する |
| UI | `src/gui_wx/right_pane.py`、`src/gui_wx/main_frame.py`、`src/gui_wx/app_controller.py` | B5 | placeholderからprofile flowへ。candidate UUID生成と既存B4 guard接続はControllerが所有 |
| docs | README、readme、Pipeline / VMD / GUI / Error仕様 | B6 | planned / implemented境界と出力契約同期 |
| package境界（関連確認） | `MMD_AutoLipTool.spec`、`build.ps1`、`docs/Release_Package_Manifest.md` | B6 / B7 | `profiles.json`をbundled default dataにしないことの確認。変更は原則不要 |

候補ファイルは実装開始時に再確認する。MS23の計画段階で、存在しないproduction codeやtest codeを作成しない。

## 18. テスト方針

### 18.1 テストファイル

既存のB2〜B5テストを再利用し、B6専用横断テストは次の1ファイルへ固定した。

- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b2_import_boundaries.py`
- `tests/test_ms23_b3_model_profiles.py`
- `tests/test_ms23_b4_model_profile_state.py`
- `tests/test_ms23_b4_profile_history.py`
- `tests/test_ms23_b4_settings_save.py`
- `tests/test_wx_ms23_b4_profile_runtime.py`
- `tests/test_wx_ms23_b5_model_profile_ui.py`
- `tests/test_ms23_b5_model_profile_controller.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`（B6専用。non-wx / wx fixtureを同一file内で分離）

### 18.2 必須テスト内容

- built-in setのexact mapping、stable ID、invalid input拒否
- semantic final normalization後の一回mappingと、frame number / value / count / order不変
- writer既存引数省略時の日本語allow-list互換、明示Latin allow-list、set外name拒否
- writer / Preview / diagnostics / fingerprintの同一resolved name
- built-in set display nameのstable契約と、Preview empty / clear経路のLatin表示維持
- core-first / writer-first / adapter-first / `src.*`・top-level mixed namespaceのfresh-process import、class identity非依存
- profile / preset / setの説明identityだけではfingerprintが変わらず、実際のmapped frame名変更ではfingerprintが変わること（profile identity単独の不変性はB4のresolved stateテストで所有）
- JSON schema version、0 / 100 / 101件、broken / future file、duplicate / range / type failure
- atomic saveと保存失敗後の旧ファイル保持
- profileとpresetの責務分離、参照中preset delete guard、active profile mutation guard、default preset reference欠落時のApply拒否 / startup正規化matrix
- profile Apply直後のdefault baseline、別preset Apply後のruntime baseline ID、restart、Undo / Redo
- active profile中の既存`active_preset_id=None`、no-profile復帰時のexact-match reconciliation
- profile-aware resolutionがprofile override付きsettingsをpreset mismatchとしてCustom化しないこと
- precedenceの全フィールド組合せ、event adjustment全7 fieldの既存挙動、profileによるmorph set固定
- upper limit変更のanalysis invalidationとbase-bound history clear、output-only変更のplan再利用とUndo / Redo identity正規化
- profile Create / Update / Deleteがcurrent outputを暗黙変更しないこと
- state / history / reset / startup / stale worker / cancel / analysis failure
- commit前failureの完全不変、commit後INI save failureのin-memory state / history保持とsave-disabled
- UIのselectionとApply分離、Busy、stale request、CRUD、broken JSON fallback
- `/profiles.json`のroot限定ignore、temporary store使用、runtime file非stage、package非同梱
- 既存日本語出力、既存preset、既存MS17〜MS22 regression

### 18.3 実行順

1. B2 core mapping
2. B3 profile store / settings
3. B4 resolution / state / diagnostics
4. B4B wx teardown / aggregate exit stability
5. B5 wx profile UI
6. B6 MS23 direct regression
7. MS17〜MS22関連回帰
8. full suite、`compileall src tests`、`git diff --check`

テストは一つずつ実行し、pass表示とprocess exit codeを別々に記録する。pass表示後にprocess exit codeが非zeroなら、関数単位と元command再実行で切り分け、未解消のままpass判定しない。GUI手動確認は、実際に実施した主体と範囲を明示する。

## 19. MS23全体の受け入れ条件

- `profiles.json`がversioned、同一保存場所、初期上限100件、atomic mutation、safe failureである。
- profile未選択時の既存日本語5母音出力と既存VMD / 30fps / WAV契約が保たれる。
- profile選択時に、日本語または英字のbuilt-in setだけを明示的に選択できる。
- writer、Preview、診断が同一のresolved morph-name contractを利用し、MS25が再利用できる文書化済み境界を持つ。MS23ではbatch専用adapterを作らない。
- semantic final normalization後にだけoutput nameをmappingし、既存日本語frame、長音、event adjustment、Preview hit-testを変えない。
- writer / coreの循環importと`src.*` / top-level class identity依存がなく、fresh-process import回帰が通る。
- `event adjustment > model profile > preset > application default`がフィールド単位でテストされる。
- upper limit変更はanalysis invalidation / history clear、output-only generation settingsとmorph-name set変更はbase plan再利用として分離される。
- profile ID、preset ID、resolved setting、morph set、fallback理由がstate / diagnosticsに追跡可能である。
- 別preset Apply後のruntime baselineがINIから再起動時に復元され、profile defaultへ暗黙に戻らない。
- commit前failureとcommit後INI save failureを分離し、後者でcommitted state / historyをrollbackしない。
- profile mutationだけではcurrent outputを変えず、broken profile file、missing preset、active profileへのupdate / delete要求、stale requestでB1のfailure matrixどおりcurrent stateを保持またはApplyを拒否する。
- output fingerprintはeffective writer outputを表し、profile表示名・IDだけの変更では変わらない。
- `profiles.json`はroot限定ignore、local保持、非stage、package非同梱である。
- PMX / PMD、任意mapping、ユーザーセット、英語音声、MS24〜MS27を実装済みと記載しない。
- MS22 Closeout Aを未完了へ戻さず、実MMD未確認をMS26へ残す。
- MS23実装によるdependency、package、license、network、Qt復活がない。

## 20. リスクと対策

| リスク | 対策 |
|---|---|
| semantic vowelを英字へ置換して長音・event adjustmentを壊す | semantic keyを保持し、output boundaryだけでmappingする |
| mapping後にsemantic normalizationしてprotected range / required zero / open-stateを壊す | semantic final normalization完了後にnameだけを一回mappingし、frame値・順序不変testを固定する |
| writerからcoreへ逆importしてpackage初期化を循環させる | writer module-level core importとcore依存adapter re-exportを禁止し、fresh-process import順序を検証する |
| `src.*` / top-level二重loadでclass identityが分岐する | structural / primitive inputを使い、mixed namespaceでidentity一致を要求しない |
| writerとPreviewが別々のmappingを持つ | `MorphNameSet`を共有し、adapter単体テストで同一結果を固定する |
| profile適用でanalysisを不要に捨てる／古いoutputを再利用する | upper limit、output-only、morph-name setを変更分類し、state guardを分ける |
| analysis parameterをoutput historyへ入れてUndo / Redoがstaleになる | upper limit差分はanalysis invalidation / history clear、output-only差分だけをbase-bound historyへ入れる |
| profileとpresetの優先順位がUIごとに異なる | core resolverを唯一の正本にし、UIはresolved stateだけを表示する |
| `profiles.json`破損で起動不能になる | built-in set、日本語既定、既存INI / presetをread-only fallbackとして残す |
| profileのdefault preset削除で設定が暗黙変化する | inactive Applyは拒否、startupはINI current値保持を優先するfailure matrixをB1で固定する |
| 別preset Apply後のrestartでprofile defaultへ戻る | runtime baselineを専用INI `active_profile_baseline_preset_id`へ保存し、profile-aware resolverで優先する |
| profile override付きsettingsをpreset mismatchとしてCustom化する | preset単独resolverを変更せず、profile-aware resolverがbaseline identityとeffective settingsを分離する |
| active runtime baseline preset更新後にIDとcurrent effective値が不一致になる | value Update / Deleteをinactive化または別baseline選択まで拒否し、settings同値Renameだけmetadata mutationとして許可する |
| active profile中のglobal direct editでprofile / baseline identityが実値を表さなくなる | non-no-op direct editをcommit前拒否し、event adjustment、別preset Apply、no-profile direct editを既存どおり維持する |
| INI save failureでcommitted profile stateをrollbackする | commit前failureと分離し、MS22のin-memory state / history保持、初回通知、save-disabledを維持する |
| fingerprintにprofile / set identityを混ぜて不要な差分が出る | effective writer frame名を正本とし、説明identityをpayloadへ入れない |
| 英字モーフ名を英語音声対応と誤認する | UI、README、VMD仕様、診断で「既存日本語5母音イベントの出力名」と明記する |
| root runtime user dataを誤って追跡・bundleする | `/profiles.json`をroot限定ignoreし、専用testはtemporary store、B7で非stage・非同梱を確認する |
| 実MMD未確認をMS23完了条件に混ぜる | MS26の未検証事項としてB7で再確認する |

## 21. Codex実装時の共通指示

- 各Block開始時に`git status --short --branch`、branch、HEAD、対象plan、関連code / testsを確認する。
- commandは一つずつ実行し、production code、test code、GUIを計画・pre-check段階で変更しない。
- 既存のユーザー変更、`profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`を上書き・stageしない。
- `profiles.json`をrepo rootのruntime dataとして生成するテストを避け、temporary directoryを使う。
- `SUPPORTED_MORPHS`をglobal mutable stateへ変更しない。
- writer module-levelからcoreへ逆importせず、mapping後のframeへsemantic normalizationを再適用しない。
- 既存日本語出力、VMD format、30fps、音声契約、Qt凍結、network禁止を維持する。
- 依存関係、package、license、release、tag、merge、push、branch削除は別途明示承認がない限り行わない。
- 実MMDを実行していない場合、実行済みとは報告しない。
- 実装後はdiffをscope監査し、production code、test、GUI、docs、runtime dataを区別して検証する。

## 22. 次のImplementation Planへの引き継ぎ

MS23-B1 Implementation Planは作成済みである。D1と、P2補正で追加したD1Aに加え、D2〜D7も2026-08-13に採用済みである。import / mixed namespace、normalize-before-map、runtime baseline、commit前後failure、baseline exit codeのP2 5件に続き、B1実装前チェックで検出したactive runtime baseline preset mutationとactive profile中global direct editのP2 2件もD6 / D7で補正した。2026-08-15にはstartup seam testのtest isolation補正でP2を解消し、live Git記述、read-only code対象、P1/P2/P3 gate表記も同期してP3を解消した。続くfresh read-only B1 contract pre-checkで249件をpass表示・全command process exit code 0、P1 / P2 / P3なしと確認し、B1をCompleted / Contract Fixedへ同期した。

> 採用済みD1: profileの`default_preset_id`はpreset値の複製ではなくstable referenceとして保存し、profile Apply時に参照先presetをbaseline、profileのnon-null fieldをoverrideとして解決する。以後に別presetをApplyした場合も、active profileのnon-null overrideは維持し、nullable fieldだけが新しいpresetを継承する。

> 採用済みD1A: profile Apply直後は`default_preset_id`をruntime baselineとし、active profile中に別presetをApplyした後は専用INIキー`active_profile_baseline_preset_id`をcurrent runtime baselineとして再起動でも優先する。active profile中は既存`active_preset_id=None`とし、preset単独時のCustom正規化は変更しない。

> 採用済みD2: profileから参照中のuser presetは、参照を変更または解除するまでdeleteを拒否する。
>
> 採用済みD3: active user profileのvalue / set updateとdeleteはinactive化まで拒否し、Renameはoutput identity非変更のmetadata mutationとして分離する。
>
> 採用済みD4: startup unresolved profileはno-profile + Japaneseへ正規化してINI数値を保持し、valid profileの専用runtime baselineだけがunresolvedならprofile default presetへfallbackする。
>
> 採用済みD5: canonical fingerprint payload構造と`ms21-effective-output-v1`を維持し、Japanese / Latin差分はmapped frame名でfingerprintへ反映する。

> 採用済みD6: active profileのcurrent runtime baselineであるuser presetは、generation settingsのvalue updateとdeleteを、profile inactive化または別baseline選択まで拒否する。settings同値Renameだけmetadata mutationとして許可する。

> 採用済みD7: active profile中のglobal generation settingsと`morph_upper_limit`のnon-no-op direct editはcommit前に拒否する。exact no-op、event adjustment、別preset Apply、no-profile時の既存direct edit契約は変更しない。

> 採用済みS2: built-in IDは`builtin:japanese-vowels` / `builtin:latin-vowels`とし、mappingは日本語5母音 / `A / I / U / E / O`とする。
>
> 採用済みS3: active profile ID、runtime baseline ID、resolution statusは専用core stateが所有し、resolved morph-name set IDは`GenerationState`が所有する。
>
> 採用済みS4: cross-store resolutionとruntime mutation guardはB4、構造検証と永続化はB3が所有する。
>
> 採用済みS5: workspace resetではprofile、runtime baseline、resolved settings、resolved morph-name setを保持し、workspace固有状態だけをclearする。
>
> 採用済みS6: `morph_upper_limit`はprofileのnullable overrideとし、resolved値をanalysis parameterへ渡す。
>
> 採用済みS7: startupでID補正が発生した場合だけ補正後IDをINIへ保存し、数値設定を保持する。

B1 contract pre-checkの補正後再チェックでschema、state ownership、failure matrixを現行code / testへ再照合し、249件をpass表示・全command process exit code 0、P1 / P2 / P3なしと確認したため、B1をCompleted / Contract Fixedと判定した。B2は実装・自動検証・ユーザー報告による手動GUI確認まで完了した。2026-08-16にB3 Implementation Planを作成し、profile DTO、strict `profiles.json`、atomic mutation、INI active identity 2種、legacy caller保護、root限定ignoreを具体化した。続くplanレビューでP2 3件・P3 1件を確認し、B1 strict floatへの復帰、load前mutation拒否、INI同一directory path test、`src/core/__init__.py`のB4延期を文書へ反映した。補正後のread-only回帰は53件＋19 subtests、67件＋19 subtestsがpass表示・各process exit code 0だった。2026-08-17にfresh read-only再チェック後、B3のDTO、store、SettingsStore additive extension、root ignore、専用testを実装し、B3専用21件＋31 subtests、関連回帰、全体759件＋57 subtests、`compileall`、`git diff --check`をprocess exit code 0で確認した。B3はstore / persistenceとして実装・自動検証済みであり、cross-store resolution、runtime guard、GUI、実MMD確認はB4以降 / MS26へdeferredである。S2〜S7のうちruntime resolverに属するexact class名、private helper名、error code名はB4 Implementation Planで固定する実装詳細として扱う。
