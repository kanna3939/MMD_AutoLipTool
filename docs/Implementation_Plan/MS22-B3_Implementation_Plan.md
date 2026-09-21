# MS22-B3 Implementation Plan

## 1. 文書情報

- 対象Block: `MS22-B3`
- 名称: Generation Preset Store / Settings Contract
- 作成日: 2026-08-08
- 基準branch: `feature/MS21-implementation`
- 基準HEAD: `d8b78cc Implement MS22-B2 long-vowel core`
- 実装コミット: `4ee67af Implement MS22-B3 preset store and settings contract`
- 文書状態: **Implemented / Code Check Passed / P1-P2-P3 Resolved (2026-08-08)**
- 直接依存: MS22-B1 Completed / Contract Fixed、MS22-B2 Implemented / Code Check Passed、MS21 Closeout A
- 次工程: MS22-B4 Implementation Plan策定。B3のproduction code・test codeを実装・検証済み、GUIはB4以降の責務

本書は、B1で固定し、B2で実装したprimitive `LongVowelMode`契約を基に、UI非依存の生成設定、
組み込みpreset、ユーザープリセット、`presets.json`、INIの保存責務を実装可能な単位へ分解する。
本書作成段階ではproduction code、test code、GUI、INI、JSON、dependency、build設定を変更しない。

## 2. 背景

MS22-B2で、normalized reading上の明示`ー`、long-vowel provenance、`hold / decay`、Preview / writer
shared resolverが実装された。B3実装前の`ShapeParameters`は既定`hold`とclosing hold / softnessを受け取れたが、
それらを再利用可能な生成設定として保存・選択する責務は存在しなかった。B3でこのcore / persistence責務を実装した。

現行`SettingsStore`は`MMD_AutoLipTool.ini`を実行ファイル（開発時はrepo）と同じ場所へ置き、
same-directory temporary fileを明示closeしてから`os.replace()`する。B3実装前はclosing hold / softnessだけが
INIへ保存され、`long_vowel_mode`とactive preset id、`presets.json`の読み書き契約は未実装だった。B3で追加した。
また、既存のsettings callerは生成設定の新規keyを渡さないため、B3では旧callerが新規設定を既定値へ
意図せず巻き戻さない保存互換を明示的に守る必要がある。

B3はpresetのデータと永続化だけを所有する。RightPaneの操作、event override、output state、Undo / Redo、
diagnostics、fingerprint、lifecycleはB4以降の責務であり、本Blockで先行接続しない。

## 3. 目的

- B2のprimitive `LongVowelMode` validationを利用するimmutable `GenerationSettings`を定義する。
- built-in presetをcode内のread-only registryとして固定する。
- user presetをstrict versioned JSONとして読み込み、検証し、atomicに保存できるようにする。
- `presets.json`の破損・unsupported version・IO失敗で既存fileやbuilt-in利用を失わない。
- INIにはactive generation settingsとactive preset idだけを保存し、preset本体やsession dataを保存しない。
- active idとINI settingsの不一致を`Custom`へ安全に正規化する。
- B4がstate/history/UIへ接続できる、UI非依存で決定的なDTO・result・failure契約を固定する。

## 4. In Scope

- immutable `GenerationSettings`
  - `closing_hold_frames: int 0..100`
  - `closing_softness_frames: int 0..100`
  - `long_vowel_mode: "hold" | "decay"`
- immutable `GenerationPreset`と、built-in / userのsource区分
- built-in preset
  - `builtin:standard-hold` / `標準（長音維持）` / `0, 0, hold`
  - `builtin:long-vowel-decay` / `長音減衰` / `0, 0, decay`
- user presetのstable UUID、display name、generation settingsの検証
- `presets.json` schema version 1、`user_presets` root、strict read / validate / write
- user presetのcreate / update / delete、0 / 100 / 101件境界、duplicate拒否
- `SettingsStore`へのactive settings・active preset idの保存・読み込み契約
- INIと同じdirectoryに置く`presets.json`のpath解決
- UTF-8、same-directory temporary、明示close、`os.replace()`、temporary cleanup
- invalid / unsupported JSON、load IO failure、save failure時のread-only unavailable・old file保持
- active preset resolution、missing / unknown / settings mismatch時の`Custom`復帰
- 既存settings callerが新規generation keyを省略しても、保存済みactive settingsを上書きしない互換処理
- B3専用core testと既存SettingsStore回帰

## 5. Out of Scope

- RightPane `プリセット` tab、selection dialog、preset管理UI、mode override UI
- `GenerationState`、`OutputEditState`、Undo / Redo、history transaction、coalescing
- Preview、VMD writer、diagnostics、report、saveability、fingerprint、lifecycleへの接続
- `EventAdjustment`の作成・編集・適用、個別eventの優先順位実装
- profile JSON、MS23のモデル別morph名、Whisper model選択・自動download、外部ASR、network同期
- JSON自動migration、unknown schemaの部分読み込み、invalid fileの自動修復・破棄
- input path、timing plan、normalized text、VMD、WAV、selection、viewport、playback、historyの保存
- VMD形式、30fps、固定モーフ`あ / い / う / え / お`、既存音声契約の変更
- 新規dependency、package、build、release、tag、merge、push、branch操作
- 実MMDでのVMD / WAV読み込み・リップ同期確認（MS26）

## 6. 前提条件

- MS21 Closeout Aは完了状態を維持する。
- MS22-B1の`GenerationSettings`、built-in id/name、JSON schema、100件上限、Custom fallback、
  INI / JSON責務分離を変更しない。
- MS22-B2の`validate_long_vowel_mode()`とprimitive string契約を再利用し、Enum identityを導入しない。
- B2実装後の直近検証証拠（2026-08-06）は、B2専用26件、full suite 644件＋7 subtests、
  `compileall src tests`、`git diff --check`がすべてprocess exit code 0である。本plan作成時には再実行せず、
  実装前チェックで現行HEADへ再照合する。
- 現行`SettingsStore`の既存public API、`SettingsLoadResult`、`SettingsSaveResult`、同一directory atomic save、
  既存INI keyを後方互換で維持する。
- B3のINI追加keyは既存の保存形式を移動せず、現在のsettings sectionへadditiveに追加する。既存callerの
  欠落keyは保存済み値を保持し、新規keyのdefaultで上書きしない。
- `presets.json`は`SettingsStore.settings_path.parent / "presets.json"`を正本とする。
- invalid user JSONではbuilt-in registryを独立して解決し、user mutationだけをsession内で停止する。

## 7. 対象ファイル

### 7.1 production code変更対象

| ファイル | B3で担当する責務 |
| --- | --- |
| `src/core/generation_presets.py` | `GenerationSettings`、`GenerationPreset`、built-in registry、JSON schema、user store、active resolution、failure result |
| `src/core/settings_store.py` | active generation settings・active preset idのdefault / validation / INI round-trip、legacy callerとの保存互換 |

### 7.2 条件付き変更対象

| ファイル | 条件 |
| --- | --- |
| `src/core/__init__.py` | B3 public APIをpackage rootから公開する必要がコード・import検証で確認された場合だけ変更する。循環importを作らない。 |
| `src/core/settings_store.py` | 既存keyのsection配置を維持したまま、generation keyの欠落・不正・保存失敗境界を最小変更で追加する。 |

### 7.3 B3で必須作成する新規test

- `tests/test_ms22_b3_generation_presets.py`

### 7.4 既存testの変更・回帰対象

- `tests/test_settings_store.py`
- `tests/test_wx_ms14_b5_export.py`（`SettingsSaveResult`互換確認）
- `tests/test_ms22_b2_long_vowel_tokens.py`
- `tests/test_ms22_b2_timeline_metadata.py`
- `tests/test_ms22_b2_long_vowel_resolver.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms22_b2_import_boundaries.py`
- `tests/test_ms21_b2_event_adjustment.py`
- `tests/test_ms21_b2_effective_shape_plan.py`
- `tests/test_ms21_b2_shape_adapters.py`
- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_ms21_b7_ui_sync_context.py`
- `tests/test_ms21_b5_effective_output_identity.py`

### 7.5 B3で変更しないファイル

- `src/gui_wx/` 全体（B4 / B5責務）
- `src/core/effective_shape_plan.py`
- `src/core/event_adjustment.py`
- `src/core/event_adjustment_history.py`
- `src/core/pipeline.py`
- `src/core/preview_transform.py`
- `src/vmd_writer/`
- diagnostics / report / fingerprint関連
- `pyproject.toml`、package / build設定、license文書
- fixed morph、VMD、audio contractの正本文書

### 7.6 文書確認対象

- `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- `docs/Implementation_Plan/MS22-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS22-B2_Implementation_Plan.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`

## 8. 実装方針

### 8.1 immutable DTOとprimitive mode

- `GenerationSettings`と`GenerationPreset`はfrozen dataclass相当のimmutable DTOとする。
- hold / softnessはboolをintとして受理せず、厳密な整数0..100を受理する。
- modeはB2の`validate_long_vowel_mode()`を使い、exact `hold` / `decay`以外を拒否する。
- DTOのconstructor、JSON decode、INI decodeのすべてで同じ値域・型契約を適用する。

### 8.2 built-in registry

- built-inはコード内の固定tuple / mappingとして定義し、`presets.json`へ複製しない。
- built-in idは`builtin:` prefixで識別し、user id生成・update・deleteの対象から除外する。
- built-inの順序、id、表示名、settingsはテストで固定する。
- built-inが常に利用可能であり、user JSONの不正や不存在に依存しない。

### 8.3 strict JSON schema

- rootは`schema_version: 1`と`user_presets`だけを持つ。
- entryは`id`、`display_name`、`generation_settings`だけを持つ。
- `generation_settings`は`closing_hold_frames`、`closing_softness_frames`、`long_vowel_mode`だけを持つ。
- root / entry / fieldの型、必須性、余分なfield、duplicate id、duplicate nameを検証し、1件でも不正なら
  file全体をfail closedにする。partial importしない。
- unsupported versionやJSON decode errorは、原因をstructured resultへ残し、既存fileを上書きしない。

### 8.4 user idとdisplay name

- create時のuser idは`uuid.uuid4()`から生成し、canonical lowercase UUID文字列として保存する。
- built-in prefix、非canonical UUID、空id、duplicate idは拒否する。updateはstable idを変更しない。
- display nameはtrim後1から100文字のsingle-line Unicodeとし、control character、改行、空文字を拒否する。
- trim後の同名とbuilt-in表示名との同名を拒否する。比較はtrim後の値で行い、保存時もtrim後の値を使う。
  updateでは対象自身のidをduplicate判定から除外し、同じdisplay nameの維持を許可する。
- user presetがbuilt-inと同じsettingsを持つことは許可するが、idとsourceは混同しない。

### 8.5 user storeのfailure isolation

- `load()`はbuilt-inを先に確定し、user JSONの結果を分離して返す。
- file不存在は空user store・mutation可能として扱う。
- invalid / unsupported / IO failureはuser presetをpartial importせず、built-inを利用可能にしたまま
  user storeをread-only unavailableとする。
- read-only unavailable中のcreate / update / deleteは、fileを触らず、原因をstructured resultで返す。
- failed mutationではold JSONとin-memory collectionを維持し、temporary fileをcleanupする。
- 外部修復後の明示的な次回`load()`では、valid fileまたはfile不存在を再評価し、user collectionと
  mutation availabilityを新しいload結果へ置き換える。再load成功後にread-only unavailableを引き継がない。

### 8.6 atomic write

- `presets.json`はsettings pathと同一directoryへtemporary fileを作る。
- JSONをUTF-8、`ensure_ascii=False`で書き、file handleを明示的にcloseしてから`os.replace()`する。
- `os.replace()`を含む失敗ではtemporary fileを削除し、旧fileとcurrent collectionを維持する。
- 成功したreplace後だけin-memory user collectionを更新する。
- 書き込み失敗後はsession内mutationをread-only unavailableへ遷移させ、同じ破壊的試行を繰り返さない。

### 8.7 INI責務とlegacy caller保護

- INIには既存のUI / recent設定を残したまま、MS22の生成設定として`GenerationSettings`の3値と
  `active_preset_id`を追加保存する。preset本体はJSONにのみ保存する。
- 既存のclosing hold / softness keyの意味と`[ui]`配置は変えず、`long_vowel_mode`とactive idを同じ
  `[ui]` sectionへadditiveに追加する。`active_preset_id=None`は空文字へ保存し、空文字・欠落はNoneへ読む。
- `SettingsStore.load()`は欠落keyをapplication defaultへ正規化する。active idの存在・一致判定はpreset storeの
  active resolutionへ委譲し、SettingsStore単体でuser JSONを解釈しない。
- `SettingsStore.save()`は、旧callerが新規generation keyを渡さない場合、既存INIの保存値を保持する。
  既存fileがない場合だけdefaultを使用する。これによりB4接続前の既存GUI保存がactive設定をhold / Customへ
  意図せず戻さない。
- INI保存失敗は既存`SettingsSaveResult`とsave-disabled / first-notification契約を維持し、B3 coreの
  in-memory preset collectionや将来のB4 stateをrollbackしない。

### 8.8 active preset resolution

- startupの出力正本はINIのnormalized `GenerationSettings`とする。
- active idがmissing / empty / unknownなら、settingsを保持して`Custom`へ正規化する。
- built-inまたはvalid user presetが存在し、definitionのsettingsとINI settingsが完全一致する場合だけ
  active idとdisplay nameを保持する。
- idが存在してもsettingsが不一致なら、INI settingsを保持し、idを`None`へ戻して`Custom`とする。
- invalid user JSONでもbuilt-in idは独立して解決する。user idは解決不能なのでCustomへ戻す。
- CustomはJSON entryを作らず、`active_preset_id=None`で表現する。
- resolution resultは`generation_settings`、`active_preset_id`、`active_preset_display_name`、
  `source: built_in | user | custom`を持つimmutable DTOとし、Customではid・display nameをNoneとする。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- `d8b78cc`を基準にbranch、worktree、既存変更、対象pathを確認する。
- B1/B2文書、現行`SettingsStore`、既存settings test、package import境界を再照合する。
- P1 / P2 / P3の残存がないこと、B3対象以外の既存変更が保護されていることを確認してから実装する。
- このStepではproduction code、test code、GUIを変更しない。

### Step 2: `GenerationSettings` contract

- B2のprimitive mode validatorを再利用し、3 fieldの型・値域・immutabilityを実装する。
- `to_dict()` / `from_dict()`相当のJSON境界をDTO自身または専用codecへ集約し、JSONとINIで同じvalidationを使う。
- bool、float、文字列数値、NaN / infinity、範囲外をfail closedにする。

### Step 3: built-in registryとpreset DTO

- built-in 2件を固定tupleとして定義し、呼び出し側がmutable mappingを取得できないようにする。
- `GenerationPreset`のid/name/settings/source検証を実装し、built-inとuserのmutation境界を分ける。
- `Custom`をpreset collectionへ追加せず、active resolutionの結果状態として扱う。

### Step 4: JSON codecとread contract

- `presets.json` pathを`SettingsStore.settings_path.parent`から決定する。
- schema version 1をstrict decodeし、rootからentryまで全件検証してからcollectionを確定する。
- invalid / unsupported / IO failureのstructured result、built-in維持、user read-only unavailableを実装する。
- load resultはbuilt-in collection、user collection、`presets_path`、`file_exists`、
  `mutation_available`、`error_code`、`error_message`を持つimmutable DTOとする。
- create / update / deleteも`operation`、`succeeded`、更新後の`user_presets`、
  `mutation_available`、`error_code`、`error_message`を持つimmutable `PresetMutationResult`で返し、
  callerが例外文字列や内部状態を推測しない契約にする。
- partial import、invalid fileの自動修復、unknown versionの上書きを行わない。

### Step 5: user mutationとatomic write

- create / update / deleteの入力検証、100件上限、duplicate、built-in拒否を実装する。
- candidate collectionを作成し、temporary write・close・replaceが成功した後だけcurrent collectionへcommitする。
- write / replace失敗時のold file、current collection、temporary cleanup、session unavailableを固定する。
- delete後に0件となる場合、JSONは空`user_presets`として保存し、built-inは変化させない。
- 外部修復後の次回`load()`は、invalid / unavailable状態をリセットし、valid user collectionまたは空collectionを
  mutation可能状態として返す。

### Step 6: `SettingsStore`のgeneration key統合

- application default `0 / 0 / hold`とactive id `None`を追加する。
- mode、hold / softness、active idのINI decode / encodeを追加し、既存keyと未知keyの扱いを変えない。
- 旧callerのgeneration key欠落を検知し、既存INI値をmergeする。保存成功後のround-tripを固定する。
- hold / softnessのSettingsStore側validationをB1の0..100契約へ揃え、既存GUIの範囲と矛盾させない。

### Step 7: active resolution

- INI settings、active id、built-in registry、valid user collectionを入力とするpure resolutionを実装する。
- missing / unknown / mismatch / invalid user store / valid matchの各結果を明示する。
- resolutionはsettingsを勝手にpreset definitionへ置換せず、INI settingsを正本としてCustom fallbackする。
- resolutionの戻り値は`generation_settings`、`active_preset_id`、`active_preset_display_name`、
  `source`を固定し、B4が別解釈を行わずに利用できるようにする。
- mutation / load / resolutionのerror codeは、少なくとも`invalid_input`、`duplicate_id`、
  `duplicate_display_name`、`limit_exceeded`、`builtin_read_only`、`store_unavailable`、
  `invalid_json`、`unsupported_schema`、`read_failed`、`write_failed`、`replace_failed`を固定する。

### Step 8: import boundaryと既存互換

- 新moduleを`src.core.generation_presets`から直接importできるようにする。
- `src.core.__init__`へのexport追加は必要性を確認してから行い、`src.core -> pipeline -> writer`の既存循環を作らない。
- `SettingsSaveResult`、legacy `SettingsStore` caller、既存INIのround-tripを壊さない。

### Step 9: 専用testと回帰

- §11の専用testを追加し、invalid / failure / boundaryを含む全契約を自動化する。
- B2 long-vowel、MS21 settings caller、history / fingerprint / UI syncの回帰を実行する。
- 各test processのpass表示、failure / error、exit codeを分離して記録する。

### Step 10: plan境界とhandoff

- production / test diffを§7へ照合し、GUI・B4責務の混入を除外する。
- `compileall`、`git diff --check`、docs末尾空白検査を実行する。
- B3実装結果をこのplan、Block Breakdown、Index、Roadmapへ同期し、B4へ確定DTOとfailure契約を引き継ぐ。

## 10. 状態遷移 / データ契約

### 10.1 `GenerationSettings`

```text
GenerationSettings (immutable)
  closing_hold_frames: int 0..100
  closing_softness_frames: int 0..100
  long_vowel_mode: "hold" | "decay"
```

- defaultは`0 / 0 / hold`。
- fieldの並び、JSON key名、INI key名はB1契約から変更しない。
- runtimeでEnumや別名を保存しない。primitive stringを正本とする。

### 10.2 `GenerationPreset`

```text
GenerationPreset (immutable)
  id: str
  display_name: str
  generation_settings: GenerationSettings
  source: built_in | user
```

- `source`はJSONへ保存しない。built-in registryまたはuser collectionとの所属から導出する。
- built-in idは`builtin:` prefix、user idはcanonical lowercase UUIDとする。
- `Custom`はpreset DTOではなく、`active_preset_id=None`のresolution状態とする。

### 10.3 `PresetMutationResult`

```text
PresetMutationResult (immutable)
  operation: create | update | delete
  succeeded: bool
  user_presets: tuple[GenerationPreset, ...]
  mutation_available: bool
  error_code: str | None
  error_message: str | None
```

- 成功時は`user_presets`をcandidateの確定結果として返し、失敗時はcurrent collectionを返す。
- `succeeded=False`では`error_code`を必須とし、成功時は`error_code`と`error_message`をNoneにする。
- `load()`のfailure stateと同じerror code vocabularyを使い、read-only unavailable中のmutation拒否も
  `store_unavailable`で表現する。

### 10.4 `PresetLoadResult`

```text
PresetLoadResult (immutable)
  built_in_presets: tuple[GenerationPreset, ...]
  user_presets: tuple[GenerationPreset, ...]
  presets_path: Path
  file_exists: bool
  mutation_available: bool
  error_code: str | None
  error_message: str | None
```

- `load()`は常にbuilt-inを返し、valid fileでは全件検証済みuser collection、missing fileでは空collectionを返す。
- invalid / unsupported / read failureではuser collectionを空にし、`mutation_available=False`とする。
- 外部修復後の次回`load()`は新しいfile状態からこのDTOを再構築し、前回のerror・collection・read-only状態を
  暗黙に引き継がない。

### 10.5 `presets.json` schema

```json
{
  "schema_version": 1,
  "user_presets": [
    {
      "id": "canonical-lowercase-uuid",
      "display_name": "ユーザー表示名",
      "generation_settings": {
        "closing_hold_frames": 0,
        "closing_softness_frames": 0,
        "long_vowel_mode": "hold"
      }
    }
  ]
}
```

- root / entry / generation settingsはstrict key setとし、unknown fieldを受理しない。
- `user_presets`は0から100件。101件目のcreateはold fileとcollectionを変更せず拒否する。
- invalid fileはpartial importせず、built-inのみ利用可能なread-only unavailable状態にする。

### 10.6 INI責務

```text
INI (SettingsStore)
  existing UI/settings keys
  closing_hold_frames: int 0..100
  closing_softness_frames: int 0..100
  long_vowel_mode: hold | decay
  active_preset_id: str | None

JSON (GenerationPresetStore)
  schema_version
  user_presets[]
```

- INIにpreset display nameやpreset本体を保存しない。display nameはregistry / user JSONから再解決する。
- INIへtiming plan、input path、normalized text、adjustment、history、selectionを保存しない。
- MS22の追加キーは既存`[ui]` sectionへ保存し、`active_preset_id=None`は空文字へencodeし、
  空文字・欠落はNoneへdecodeする。
- 既存callerが`long_vowel_mode` / `active_preset_id`を省略したsaveでは、既存INI値を保持する。

### 10.7 load / failure state

| 入力状態 | built-in | user collection | mutation | active resolution |
| --- | --- | --- | --- | --- |
| `presets.json`なし | 利用可能 | 空 | 可 | INI idの一致時のみ保持、通常はCustom |
| valid schema 1 | 利用可能 | 全件import | 可 | valid definitionとのsettings一致時だけ保持 |
| JSON破損 / unknown version / schema不正 | 利用可能 | importなし | 不可（read-only unavailable） | built-in一致ならbuilt-in、それ以外Custom |
| read IO failure | 利用可能 | importなし | 不可（read-only unavailable） | built-in一致ならbuilt-in、それ以外Custom |
| mutation validation拒否 | 利用可能 | current維持 | 可 | active state不変 |
| temporary / replace failure | 利用可能 | current維持 | 不可（session内unavailable） | active state不変 |
| 外部修復後の次回`load()`がvalid / file不存在 | 利用可能 | valid全件 / 空 | 可 | 新しいcollectionとINIの一致結果を使用 |

### 10.8 `ActivePresetResolution`

```text
ActivePresetResolution (immutable)
  generation_settings: GenerationSettings
  active_preset_id: str | None
  active_preset_display_name: str | None
  source: built_in | user | custom
```

- matching built-in / user definitionだけがid・display nameを持つ。
- Customでは`active_preset_id=None`、`active_preset_display_name=None`とし、INI settingsを保持する。

### 10.9 active preset resolution matrix

| INI active id | definition | settings一致 | 結果 |
| --- | --- | --- | --- |
| missing / empty | なし | - | INI settingsを保持、Custom |
| unknown | なし | - | INI settingsを保持、Custom |
| built-in / user | あり | yes | id・display name・settingsを保持 |
| built-in / user | あり | no | INI settingsを保持、idをNoneへ正規化、Custom |
| built-in | built-in valid / user JSON invalid | yes | built-inを保持 |
| user | user JSON invalid | - | INI settingsを保持、Custom |

### 10.10 mutation transaction

```text
validate request
  ↓
candidate user collection
  ↓
same-directory temporary JSON write
  ↓ close
os.replace()
  ├─ success: commit collection
  └─ failure: cleanup temp, preserve old file/collection, mark unavailable
```

- B3ではhistory transactionを作らない。B4が成功したpreset mutationをoutput stateへ接続する。
- `SettingsStore`のINI保存失敗とJSON保存失敗を混同しない。どちらもin-memory current stateを勝手にrollbackしない。

## 11. テスト方針

### 11.1 B3専用test

#### DTO / built-in

- `GenerationSettings`のdefault、0 / 100、負数、101、bool、float、mode不正を検証する。
- built-inのid、表示名、settings、順序、JSONへ複製されないことを検証する。
- user idのUUID、built-in prefix、stable update、display name trim / 1 / 100 / 101、control / newline、duplicateを検証する。

#### JSON load / validation

- missing file、空user list、valid round-tripを検証する。
- malformed JSON、schema version 0 / 2、root / entry / field不足、unknown field、型不正、partial invalid、
  duplicate id / nameを全体fail closedで検証する。
- invalid user JSON後もbuilt-inが利用可能で、create / update / deleteが拒否されることを検証する。
- invalid / unavailable状態の後に外部修復して次回`load()`を呼ぶと、collectionが置き換わり、
  `mutation_available=True`へ復帰することを検証する。

#### mutation / atomicity

- user preset 0 / 1 / 100件と101件拒否を検証する。
- create / update / deleteの成功、built-in mutation拒否、stable id保持を検証する。
- updateで対象自身のdisplay nameを維持でき、別userのdisplay nameへの変更だけを拒否することを検証する。
- mutation resultのoperation、succeeded、error code、collection、mutation availabilityを検証する。
- temporary fileが同一directoryに作られ、replace前にhandleが閉じられることを検証する。
- write / replace失敗でold JSON、in-memory collection、built-inを維持し、temporaryをcleanupすることを検証する。
- failed mutation後のread-only unavailableと、次のmutation拒否を検証する。

#### active resolution / INI boundary

- missing / unknown / matching / mismatching active idのCustom fallbackを検証する。
- invalid user JSONでもmatching built-in idを保持することを検証する。
- `SettingsStore`のmode / active id round-trip、invalid default、0..100 boundを検証する。
- active resolution resultのsettings、id、display name、sourceと、Custom時のNone値を検証する。
- `active_preset_id=None`のINI空文字round-tripを検証する。
- 既存callerが新generation keyを省略したsaveで、既存INIのactive settingsが保持されることを検証する。
- INI / JSONへtiming plan、input path、adjustment、history、selectionが混入しないことを検証する。

### 11.2 既存回帰command

各commandは一つずつ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b3_generation_presets.py tests\test_settings_store.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b5_export.py tests\test_ms21_b6_adjustment_history.py tests\test_ms21_b7_ui_sync_context.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b5_effective_output_identity.py tests\test_ms22_b2_long_vowel_tokens.py tests\test_ms22_b2_timeline_metadata.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b2_event_adjustment.py tests\test_ms21_b2_effective_shape_plan.py tests\test_ms21_b2_shape_adapters.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms22_b2_long_vowel_resolver.py tests\test_ms22_b2_long_vowel_adapters.py tests\test_ms22_b2_import_boundaries.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

pytestはpass件数、failure / error、process exit codeを分けて記録する。full suiteでwx環境由来の終了コード差が
発生した場合も表示結果とprocess exit codeを分離し、自動的にpass扱いしない。

### 11.3 diff / scope監査

- production変更が`generation_presets.py`と`settings_store.py`、必要最小限のexportへ収まる。
- GUI、history、diagnostics、fingerprint、pipeline、Preview、writer、dependency、packageへ変更がない。
- 既存testを削除・skip・期待値弱化していない。
- existing INI key、legacy caller、fixed morph、30fps、VMD、audio contractを変更していない。
- invalid JSONやsave failureを、built-inまで利用不能にする実装になっていない。
- secrets、absolute user pathのfixture、生成物をtest / JSONへ追加していない。

### 11.4 手動確認・MMD確認

- B3はUI非依存core / persistenceのため、manual GUI確認を必須受け入れ条件にしない。
- `presets.json`のWindows実path確認はtemporary directory testで代替し、実ユーザーprofileへ書き込まない。
- 実MMDでのVMD / WAV読み込み・リップ同期はMS26へ維持し、B3完了証拠へ含めない。

## 12. 受け入れ条件

- `GenerationSettings`がimmutableで、3 fieldのdefault・型・値域・primitive mode契約がB1/B2と一致する。
- built-in 2件がJSONなしで常に利用でき、編集・削除・JSONへの複製保存を拒否する。
- user presetはcanonical UUID、trim済みsingle-line name、settingsを保持し、duplicateと101件目を拒否する。
- `presets.json` schema version 1をstrictに読み書きし、invalid / future / partial invalid fileをpartial importしない。
- invalid / unsupported / IO failureでold fileを上書きせず、built-inを維持し、user mutationをread-only unavailableへ止める。
- invalid / unavailable状態から外部修復後の次回`load()`で、validまたは空user storeへ復帰し、
  staleなread-only unavailableを引き継がない。
- create / update / delete成功時だけin-memory collectionを更新し、失敗時はold file、collection、temporary cleanupを維持する。
- mutation結果とactive resolution結果が固定DTOとerror codeで返り、callerが内部状態を推測しない。
- JSON保存はUTF-8、same-directory temporary、close-before-replace、`os.replace()`である。
- INIはactive generation settingsとactive preset idだけを保持し、preset本体・session dataを保存しない。
- active idのmissing / unknown / mismatchはINI settingsを正本としてCustomへ戻し、matching definitionだけをactiveとして保持する。
- invalid user JSONでもmatching built-in idは独立して保持できる。
- 既存settings callerがgeneration keyを省略しても、保存済みactive settingsを意図せずdefaultへ戻さない。
- existing `SettingsStore` result/APIとB2 long-vowel resolver、MS21の既存回帰を維持する。
- B3専用test、指定回帰、full suite、compileall、diff checkの結果とexit codeが記録される。
- production code、test codeの変更がB3 scopeへ限定され、GUI、B4 state/history、diagnostics、package、dependencyを先行実装しない。
- 実装着手前のP1 / P2 / P3残存はなく、実装中に新たなP3を検出した場合も記録・修正してからB4へ引き継ぐ。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 既存callerが新keyを省略し、active settingsをdefaultで上書きする | save時にprovided keyと既存INIを区別し、generation keyをmergeして保持する回帰を追加する |
| invalid JSONのpartial importや自動上書きでuser presetを失う | strict全体検証、read-only unavailable、old file保持、成功後commitを固定する |
| built-inとuserのid/name衝突 | built-in prefix、canonical UUID、trim後name重複検証、mutation境界を分離する |
| 101件目やduplicate操作で既存fileが壊れる | candidate collectionを先に検証し、replace成功までcurrent collectionを変更しない |
| temp handleを閉じる前にreplaceしWindowsで失敗する | same-directory temp、明示close、replace監視testを追加する |
| active idとsettingsが不一致になり別presetを誤表示する | INI settingsを正本にし、一致時だけidを保持、その他はCustomへ戻す |
| SettingsStore単体がuser JSONを解釈し責務が混ざる | JSON解釈・active resolutionをgeneration preset moduleへ分離する |
| B4のhistory/UI責務がB3へ混入する | 対象ファイルとOut of Scopeを固定し、diff監査でGUI/state/history変更を拒否する |
| 既存import boundaryへ循環を追加する | module-level importを最小化し、fresh-process import testで確認する |

## 14. 実装時の注意

- B3実装前に本planを現行code・test・B1/B2契約へ再照合し、P1 / P2 / P3を解消する。
- B3ではproduction code、test code、GUIを同じ変更で先回りして広げない。特にB4のstate/history、B5のUIを実装しない。
- `Qt / PySide6`を復活させない。外部クラウドASR、外部音声送信、background通信、自動downloadを追加しない。
- 固定モーフ、30fps、VMD形式、既存音声3役契約を変更しない。
- `presets.json`やINIをrepo root、実ユーザーprofile、source audio directoryへ生成するtestを作らない。
- JSON failureでbuilt-inまで使えなくしない。INI failureでin-memory stateをrollbackしない。
- testは一つずつ実行し、pass表示・failure / error・process exit codeを分けて報告する。
- 完了時は、確認したファイル、変更ファイル、実装内容、テスト、仕様逸脱、残課題、B4への引き継ぎを報告する。
