# MS23-B3 Implementation Plan

## 1. 文書情報

- 対象: MS23-B3 Model Profile Store / Persistence
- 作成日: 2026-08-16
- 対象リポジトリ: `MMD_AutoLipTool_Antigravity`
- 計画作成時点のbranch: `feature/MS23-implementation`
- 計画作成時点のHEAD: `cb86aaa Implement MS23-B2 morph name mapping`
- 依存: MS22-B7 Closeout A、MS23-B1 Completed / Contract Fixed、MS23-B2 Implemented / Automated Verification Passed / Manual GUI Verification Passed (User Report)
- 文書ステータス: Implementation Plan Repaired / P2 Resolved / Fresh Read-only Recheck Passed / Implemented / Automated Verification Passed / Manual GUI Not Required
- B3の作業種別: UI非依存core persistence、INI additive extension、runtime user data保護
- 計画策定時の実装権限: production code、test code、GUI、runtime user dataを変更しない

B1で採用済みのD1〜D7、S1〜S7をB3の正本契約とする。B3で新たなユーザー判断は追加しない。特に、cross-store preset参照解決、active profile / runtime baselineの正規化、active profile mutation guardはB4へ残し、B3はprofile構造と永続化だけを担当する。

2026-08-16のplanレビューではP1なし、P2 3件、P3 1件を確認した。P2は`morph_upper_limit`のB1 strict-float契約への復帰、load前mutationによる既存file上書き防止、INI同一directory解決の直接test不足である。P3はB4都合の`src/core/__init__.py`変更余地である。本補正でstrict float、明示unloaded gate、path resolution testを固定し、package root export判断をB4へ完全延期した。補正後のread-only回帰はB2 + preset / settings 53件＋19 subtests、SettingsStore consumer群67件＋19 subtestsがpass表示・各process exit code 0だった。production code、test code、GUI、runtime user dataは変更していない。

## 2. 背景

MS22は、versioned `presets.json`、immutable `GenerationPreset`、atomic mutation、INIのgeneration settings / active preset ID、旧callerの保存互換を実装済みである。MS23-B2は、日本語・英字のbuilt-in morph-name setをcoreのleaf moduleへ固定し、既存省略経路の日本語defaultを維持した。

MS23-B3では、この既存基盤へモデル別profileを追加する。ただし、profileにはpresetの値を複製せず`default_preset_id`をstable referenceとして保存する。profileのApply、presetとの優先順位、startup fallback、history、diagnostics、GUIはB4以降の責務である。

現行`SettingsStore.save()`は、新しいgeneration keyを旧callerが省略した場合に既存INI値を保持するmerge契約を持つ。B3で追加するactive profile ID 2種にも同じ互換境界を適用しないと、themeやrecent fileだけを保存する既存経路がprofile identityを意図せず消去し得る。そのため、JSON storeとINI additive extensionを同じBlockで計画する。

## 3. 目的

1. B1 schema v1に従うimmutable model profile DTOを実装可能な形へ固定する。
2. INIと同じdirectoryのversioned `profiles.json`をstrictにloadし、最大100件をatomicにCreate / Update / Deleteできるstoreを追加する。
3. broken / future / unreadable JSONをpartial importせず、built-in morph-name set、既存INI、既存preset、日本語defaultを利用可能なままprofile mutationだけを停止する。
4. INIへ`active_model_profile_id`と`active_profile_baseline_preset_id`をadditiveに保存し、未知値の解釈はB4へ委譲する。
5. `/profiles.json`をrepository root限定のruntime user dataとしてignoreし、testがroot実データを生成・変更しないようにする。
6. preset、morph-name set、日本語出力、VMD 30fps、audio、wx GUI、package、networkの既存契約を維持する。

## 4. In Scope

- `ProfileGenerationOverrides`と`ModelProfile`のimmutable DTO
- profile ID、display name、morph-name set ID、nullable upper limit、nullable generation overrides、preset referenceの構造validation
- `profiles.json` schema version 1、exact key set、UTF-8 encode / decode
- 0〜100件上限、duplicate ID / display name、future schema、broken JSON、read failureの分類
- `ModelProfileStore`のload、lookup、Create / Update / Delete、structured result
- same-directory temporary file、close-before-replace、`os.replace()`、failure時cleanup / old file保持
- explicit reloadによるstore availability回復
- INI `[ui]`の`active_model_profile_id`と`active_profile_baseline_preset_id`
- IDの欠落 / 空文字 / 明示`None`、未知ID保持、旧caller省略時の既存値保持
- `.gitignore`のroot限定`/profiles.json`
- B3専用test、SettingsStore回帰、MS22 preset store回帰、MS23-B2 morph-name set回帰
- 実装後のBlock Breakdown、Index、RoadmapへのB3状態同期

## 5. Out of Scope

- profile Apply、Select、current runtime state、precedence解決
- `default_preset_id`の参照先存在確認、missing preset fallback、参照中presetのupdate / delete guard
- active profile / runtime baselineの未知・削除済みID正規化、startup補正保存
- active profileのvalue / set update・delete拒否、Rename判定、global direct edit guard
- `GenerationState`、`OutputEditState`、`AnalysisParameterSnapshot`、history、fingerprintの変更
- diagnostics、report、saveability、Preview、writerの追加変更
- wxPython GUI、profile selector / editor、Busy / stale revision処理
- PMX / PMD読込、モデル解析、任意morph mapping、user-defined morph-name set
- MS24 Whisperモデル選択、MS25一括出力、MS26実MMD確認、MS27 packaging / release readiness
- Qt / PySide6、外部クラウドASR、外部音声送信、background通信、Whisper自動download
- dependency、build、package、license、VMD形式、30fps、audio contractの変更
- merge、push、tag、release、branch削除

## 6. 前提条件

- branchは`feature/MS23-implementation`、計画作成時HEADは`cb86aaa`である。
- MS22 Closeout Aを維持し、実MMD未確認はMS26へdeferredのままとする。
- `src/core/generation_presets.py`はschema version 1、100件上限、canonical lowercase UUID、trim後1〜100文字のdisplay name、strict generation settings、structured load / mutation result、atomic replaceを実装済みである。
- `src/core/settings_store.py`はdev時repository root、frozen時exe parentのINI pathを正本とし、既存INI sectionをmergeして保存する。
- `src/core/morph_name_sets.py`は`builtin:japanese-vowels`と`builtin:latin-vowels`の2 IDだけを受理し、日本語をdefaultとする。
- `presets.json`と`MMD_AutoLipTool.ini`はroot限定ignore対象のruntime user dataであり、B3でも変更・stageしない。
- B3実装開始には、本planのレビューとfresh read-only pre-implementation checkが別途必要である。

## 7. 対象ファイル

### 7.1 production code変更対象

| ファイル | B3で担当する責務 |
|---|---|
| `src/core/model_profiles.py` | profile DTO、schema codec、store、structured load / mutation result、atomic persistence |
| `src/core/settings_store.py` | active profile ID 2種のdefault、normalization、INI load / save、旧caller省略時の保存互換 |
| `.gitignore` | repository root限定の`/profiles.json`追加 |

### 7.2 B3で必須作成するtest

- `tests/test_ms23_b3_model_profiles.py`

### 7.3 既存testの変更・回帰対象

- `tests/test_settings_store.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b2_import_boundaries.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_wx_ms22_b4_generation_state.py`
- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_ms22_b6_lifecycle_regression.py`
- `tests/test_wx_ms22_b6_lifecycle_regression.py`

### 7.4 B3で変更しないファイル

- `src/core/generation_presets.py`。B3は既存private helperをimportせず、preset storeの挙動を変更しない。
- `src/core/morph_name_sets.py`。B2のbuilt-in registryを構造validationに利用するだけとする。
- `src/core/__init__.py`。現行どおりleaf module直接importを使い、package root exportの要否はruntime consumerが具体化するB4で判断する。
- `src/core/generation_state.py`、`src/core/output_edit_history.py`、diagnostics / fingerprint関連
- `src/gui_wx/`全体
- `src/vmd_writer/`全体
- `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、license文書
- repository rootの`profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`

### 7.5 文書変更対象

- `docs/Implementation_Plan/MS23-B3_Implementation_Plan.md`
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

## 8. 実装方針

### 8.1 immutable DTO

- `ProfileGenerationOverrides`をfrozen dataclassとし、`closing_hold_frames`、`closing_softness_frames`、`long_vowel_mode`を各nullableで保持する。
- hold / softnessのnon-null値はboolを拒否するstrict int 0〜100とする。
- long-vowel modeのnon-null値は既存`validate_long_vowel_mode()`を使い、exact `hold` / `decay`だけを受理する。
- `ModelProfile`をfrozen dataclassとし、`id`、`display_name`、`morph_name_set_id`、`morph_upper_limit`、`generation_overrides`、`default_preset_id`を保持する。
- `morph_upper_limit`はB1どおり`null`またはstrict `float`だけを受理する。bool、int、string、非有限値を拒否し、0.0〜10.0を範囲検証する。範囲外値をclampせず拒否する。
- DTO constructor、JSON decode、mutation inputで同じvalidationを使う。

### 8.2 IDとdisplay name

- user profile IDはcanonical lowercase UUID stringとし、create時は`uuid.uuid4()`で生成する。test用に明示ID seamを持てるようにする。
- display nameは既存presetと同じくtrim後1〜100文字、single-line、control characterなしとする。比較と保存にはtrim後の値を使う。
- duplicate display nameはuser profile間でcase-sensitive exact比較し、Unicode case foldingや追加normalizationを導入しない。
- `morph_name_set_id`はB2 registryを使い、exact `builtin:japanese-vowels` / `builtin:latin-vowels`だけを受理する。built-in set本体はprofile JSONへ保存しない。
- `default_preset_id`は構造上、non-empty stable stringとする。canonical lowercase user UUID、または`builtin:`にnon-empty suffixを持つbuilt-in形式を受理する。空白・control character・trimが必要な値は拒否し、暗黙補正しない。
- B3は`default_preset_id`の参照先をlookupしない。構造上validだが存在しないIDもprofileとして保持し、B4のresolution / mutation guardでerrorにする。

### 8.3 strict `profiles.json` schema

- rootは`schema_version`と`user_profiles`のexact 2 keysとする。
- profile entryはDTOの6 fieldsと完全一致させる。
- `generation_overrides`は3 nullable fieldsと完全一致させる。
- `schema_version`はboolを拒否するexact int `1`とし、type不正またはversion不一致を`unsupported_schema`とする。
- unknown key、missing key、field型不正、範囲外値、invalid set ID、invalid reference形式を`invalid_schema`とする。
- 100件超を`limit_exceeded`、duplicate profile IDを`duplicate_id`、trim後duplicate display nameを`duplicate_display_name`とする。
- 1件でも不正ならfile全体をfail closedにし、partial importしない。
- serializationはUTF-8、`ensure_ascii=False`、stable field order、indent 2、末尾改行とする。

### 8.4 store locationとconstructor seam

- `PROFILES_FILE_NAME = "profiles.json"`、`PROFILES_SCHEMA_VERSION = 1`、`MAX_USER_PROFILES = 100`を定義する。
- default pathは`SettingsStore.settings_path.parent / PROFILES_FILE_NAME`とする。これによりdevはrepository root、frozenはexe parentになる。
- constructorは既存`GenerationPresetStore`と同様に`settings_path`または`settings_store`を受け、testでは明示`profiles_path`を注入できるようにする。
- `settings_path`と`settings_store`の同時指定は拒否する。
- constructor直後は`load_completed=False`、空collection、`mutation_available=False`のunloaded状態とする。既存fileの有無を未確認のままmutation可能にしない。
- B3 testは必ずtemporary directoryを注入し、default pathへ実fileを作らない。

### 8.5 loadとfailure isolation

- `load()`がmissing / success / failureの結果を返した時点で`load_completed=True`とする。file不存在またはvalid fileでは`mutation_available=True`、invalid / unreadable fileでは`mutation_available=False`とする。
- file不存在は空`user_profiles`、`mutation_available=True`、errorなしとする。
- directory等の非regular file、read IO / Unicode failureは`read_failed`とする。
- JSON decode failureは`invalid_json`とする。
- schema / version / limit / duplicate failureは対応するfixed error codeを返す。
- load failure時は`user_profiles=()`、`mutation_available=False`とし、B2 built-in morph-name set、既存preset store、INIを変更しない。
- unavailable中のCreate / Update / Deleteはfileへ触れず、`store_unavailable`を返す。
- 初回`load()`前のCreate / Update / Deleteはfileへ触れず、`store_not_loaded`を返す。missing targetの場合もload前に新規fileを作らない。
- 外部修復またはfile削除後に明示`load()`を再実行した場合、collection、error、availabilityを新しい結果で完全に置換する。過去のunavailableを引き継がない。

### 8.6 lookupとmutation

- storeはimmutable tupleの`user_profiles`と、IDによるread-only `get_profile()`を公開する。
- `get_profile()`は初回`load()`前には`ProfileContractError`を送出し、未loadをunknown / deleted IDと混同しない。load完了後はexact ID一致を返し、unknown / deleted / malformed stringには`None`を返してfileとcollectionを変更しない。
- Createは上限、ID、name、全fieldを検証し、valid candidateを末尾へ追加する。
- Updateはstable IDを変更せず、対象自身をduplicate name判定から除外し、collection内の順序を維持する。
- Deleteは指定IDだけを除去し、不明IDは`profile_not_found`とする。
- structural input failureは`invalid_input`、重複は`duplicate_id` / `duplicate_display_name`、101件目は`limit_exceeded`とする。
- `ProfileMutationResult.operation`は`create | update | delete`、成功時errorなし、失敗時error code必須とする。
- B3 store単体のUpdate / Deleteはactive stateを知らないため実行可能である。B4はstore mutation前にD3のactive profile guardとRename判定を適用する。
- Create / Update時のmissing preset参照拒否、preset mutation guardはB4がstore commit前に実施する。B3のraw store APIをGUIから直接呼ばない。
- profile mutationだけでINIのactive ID、current generation settings、analysis、output、historyを変更しない。

### 8.7 atomic write

- candidate tupleを先に完全検証し、current collectionを変更しないままtemporary JSONを作る。
- temporary fileはtargetと同じdirectoryへ作成し、UTF-8 writeを完了してhandleをcloseした後に`os.replace()`する。
- write failureは`write_failed`、replace failureは`replace_failed`とする。
- failure時はtemporary fileをcleanupし、旧`profiles.json`とin-memory collectionを維持する。
- replace成功後だけin-memory collectionをcandidateへ更新する。
- write / replace failure後はsession内mutationをunavailableへし、同じ失敗操作を繰り返さない。明示`load()`でのみ再評価する。

### 8.8 INI additive extension

- `[ui]`へ`active_model_profile_id`と`active_profile_baseline_preset_id`を追加する。
- defaultは両方`None`、INI encodeは空文字、欠落・空文字・whitespace-only decodeは`None`とする。
- non-empty stringはtrim後の値を保持する。SettingsStoreはprofile / preset storeを参照せず、unknown / deleted IDも値として保持する。
- `active_profile_baseline_preset_id`だけが存在する不整合もB3では消去しない。B4がactive profile IDとの組を解決し、必要時だけ補正後IDを保存する。
- `SettingsStore.save()`へkeyが明示された場合は値または`None`を保存する。旧callerがkeyを省略した場合は既存INI値を保持し、fileにkeyがない場合だけdefaultを使う。
- 既存`active_preset_id`の意味、section、empty encodingを変更しない。active profile時に`active_preset_id=None`へする処理はB4で行う。
- `SettingsLoadResult`、`SettingsSaveResult`、save-disabled / first-notification契約を変更しない。

### 8.9 runtime user dataとignore

- `.gitignore`のRuntime user data節へ`/profiles.json`を追加する。
- root限定ruleとし、subdirectoryのfixture名`profiles.json`を過剰にignoreしない。
- 実装・testでrepository rootの`profiles.json`を生成しない。既にlocal fileが存在しても読取・変更・stageしない。
- package、build、sample dataへ`profiles.json`を同梱しない。

### 8.10 B4 handoff境界

- B3はprofile DTO、store、INI raw identityを提供して完了とする。
- B4はprofile ID、runtime baseline ID、preset referenceを一つのimmutable resolutionへ統合する。
- B4はD1 / D1A precedence、D2 / D6 preset mutation guard、D3 profile mutation guard、D4 startup fallback、D7 direct edit guardを実装する。
- B3 errorとB4 resolution errorを混在させない。broken profile fileとdangling preset referenceは別分類とする。

## 9. 詳細ステップ

### Step 1: 実装開始gate

- 本plan、Block Breakdown、B1 contract、B2実装をfresh read-onlyで再確認する。
- `git status --short --branch`、branch、HEAD、diffを一コマンドずつ確認する。
- pre-existing変更とruntime user dataを記録し、scope外変更を取り込まない。
- P1 / P2 / P3なし、または指摘解消済みであることをB3着手条件とする。

### Step 2: DTOとvalidation

- `ProfileGenerationOverrides`、`ModelProfile`、contract errorを追加する。
- exact key set、nullable field、UUID、display name、morph set ID、upper limit、preset referenceを同じvalidatorへ集約する。
- built-in morph-name setの正本はB2 moduleから参照し、ID表を複製しない。

### Step 3: JSON codecとload result

- schema v1 decoder / encoderを追加する。
- `ProfileLoadResult`へprofiles、path、file existence、mutation availability、error code / messageを持たせる。
- missing、valid、broken、future、IO failure、100件境界をfail-closedに実装する。
- `settings_path`、`settings_store`、明示`profiles_path`ごとのtarget pathと同時指定拒否を直接testする。

### Step 4: store lookup / mutation

- path resolution、load、`get_profile()`、Create / Update / Deleteを追加する。
- constructor直後をunloaded / mutation unavailableとし、初回load前のlookupとmutationをfail closedにする。
- mutation candidateをcurrent collectionと分離し、validation failureでfileを触らない。
- missing preset referenceやactive stateをB3で解決しないことをtestへ固定する。

### Step 5: atomic persistence

- same-directory temporary、UTF-8 JSON、close-before-replace、cleanupを実装する。
- replace成功後だけcollectionをcommitする。
- write / replace failureでold fileとold collectionを保持し、mutation unavailableへ遷移させる。

### Step 6: SettingsStore拡張

- default、parse、normalize、format、merge対象へactive profile ID 2種をadditiveに追加する。
- missing / empty / unknown / explicit clearのround-tripを固定する。
- 旧callerが2 keyを省略したsaveで既存値が保持されるよう、既存generation key互換と同じmerge経路へ含める。

### Step 7: root ignore

- `.gitignore`へ`/profiles.json`を追加する。
- root pathがignoreされ、subdirectory同名pathはignoreされないことを一コマンドずつ確認する。
- local runtime fileを作成・stageしない。

### Step 8: B3専用test

- temporary directoryだけを使うDTO、schema、load、mutation、atomicity、reload、INI round-trip testを追加する。
- 0 / 1 / 100 / 101件、strict float、bool / int / string / non-finite / range、duplicate、unknown keyを直接検証する。
- load前lookup / mutation、INI同一directory、constructor引数排他、explicit path overrideを直接検証する。
- B3 raw storeとB4 guardの責務境界をnegative testで固定する。

### Step 9: 回帰とscope監査

- B3専用、SettingsStore、preset store、B2 morph-name setの順に最小回帰を実行する。
- SettingsStoreを使うwx / lifecycle回帰、full suite、`compileall src tests`、`git diff --check`を実行する。
- diffでGUI、state、history、writer、dependency、package、runtime file変更がないことを確認する。

### Step 10: 文書同期とhandoff

- 実装・検証結果をBlock Breakdown、Index、Roadmapへ同期する。
- manual GUI確認はB3の必須gateにしない。実行していないGUI / actual-MMD確認をpass扱いしない。
- B3完了後の次工程をMS23-B4 Implementation Plan策定・レビューとする。

## 10. 状態遷移 / データ契約

### 10.1 DTO

```text
ProfileGenerationOverrides
  closing_hold_frames: int | None
  closing_softness_frames: int | None
  long_vowel_mode: "hold" | "decay" | None

ModelProfile
  id: canonical lowercase UUID
  display_name: trimmed 1..100 chars
  morph_name_set_id: builtin:japanese-vowels | builtin:latin-vowels
  morph_upper_limit: float 0.0..10.0 | None
  generation_overrides: ProfileGenerationOverrides
  default_preset_id: structurally valid stable preset ID
```

`None`は値の欠落ではなく下位layer継承を表す。B3は継承値を解決せず、JSON表現をそのままimmutable DTOへ保持する。

### 10.2 `profiles.json` schema v1

```json
{
  "schema_version": 1,
  "user_profiles": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "display_name": "標準モデル",
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

root、entry、`generation_overrides`はexact key setとする。built-in morph-name set本体、preset値、active ID、resolved値は保存しない。

### 10.3 structured result

```text
ProfileLoadResult
  user_profiles: tuple[ModelProfile, ...]
  profiles_path: Path
  file_exists: bool
  mutation_available: bool
  error_code: str | None
  error_message: str | None

ProfileMutationResult
  operation: create | update | delete
  succeeded: bool
  user_profiles: tuple[ModelProfile, ...]
  mutation_available: bool
  error_code: str | None
  error_message: str | None
```

成功時はerrorを`None`、失敗時はerror code必須とする。resultはfrozen dataclass相当とし、profile collectionをtupleへ固定する。

### 10.4 load matrix

| 入力 | user profiles | mutation | error | 他機能への影響 |
|---|---|---|---|---|
| constructor直後 / load未実施 | empty | 不可 | mutation時`store_not_loaded` | fileへ触れない |
| file不存在 | empty | 可 | なし | なし |
| valid 0〜100件 | file内容 | 可 | なし | なし |
| broken JSON | empty | 不可 | `invalid_json` | B2 set / preset / INIは利用可 |
| schema不正 | empty | 不可 | `invalid_schema`等 | 同上 |
| future / type不正version | empty | 不可 | `unsupported_schema` | 同上 |
| read failure / non-file | empty | 不可 | `read_failed` | 同上 |
| 外部修復後のvalid reload | 新file内容 | 可 | clear | 過去errorを引き継がない |
| 外部削除後のreload | empty | 可 | clear | missing file通常状態 |

### 10.5 mutation transaction

```text
require completed load and mutation availability
  -> validate input
  -> build immutable candidate tuple
  -> write same-directory temporary JSON
  -> close temporary handle
  -> os.replace(temp, profiles.json)
  -> replace in-memory tuple
```

load未実施、validation、write、replaceのどこかで失敗した場合、current tupleと旧JSONを変更しない。load未実施ではtemporary自体を作らず、write / replace failureではtemporaryをcleanupしてsession mutationを停止する。

### 10.6 INI契約

```ini
[ui]
active_model_profile_id =
active_profile_baseline_preset_id =
```

| 入力状態 | load値 | save表現 | B3の扱い |
|---|---|---|---|
| key欠落 | `None` | default時は空文字 | validationしない |
| 空 / whitespace | `None` | 空文字 | inactive候補 |
| non-empty unknown ID | trim後string | string | 保持。B4が解決 |
| saveで明示`None` | `None` | 空文字 | 明示clear |
| save引数でkey省略、既存値あり | 既存値 | 既存値維持 | legacy caller保護 |

### 10.7 responsibility matrix

| 操作 | B3 | B4以降 |
|---|---|---|
| profile schema validation | 実施 | 再実装しない |
| morph-name set ID validation | B2 registryで実施 | resolved DTOへ投影 |
| preset IDの構造validation | 実施 | 参照先lookup / fallback |
| raw profile Create / Update / Delete | atomicに実施 | commit前guardを適用 |
| active profile / baseline IDのINI保存 | raw値をload / save | 組として正規化、必要時補正保存 |
| precedence / effective settings | 実施しない | B4 resolver |
| analysis / output / history | 変更しない | B4 transaction |
| GUI選択・編集 | 実施しない | B5 |

## 11. テスト方針

### 11.1 DTO / schema

- valid Japanese / Latin profileと全nullable / 全non-null境界を検証する。
- frozen DTO、deterministic `to_json_dict()`、round-trip equalityを検証する。
- profile IDのuppercase、noncanonical、built-in prefix、empty、duplicateを拒否する。
- display nameのtrim、1 / 100 / 101文字、empty、改行、control character、trim後duplicateを検証する。
- morph set IDはexact 2種だけを受理し、unknown、wrong type、whitespace付与を拒否する。
- upper limitは`None`、0.0、10.0のfloatを受理し、bool、int、string、NaN、infinity、範囲外を拒否する。
- hold / softnessは`None`、0、100を受理し、bool、float、-1、101を拒否する。
- modeは`None`、`hold`、`decay`だけを受理する。
- preset referenceはcanonical UUIDとnon-empty `builtin:`形式を受理し、空、trim必要値、control character、invalid UUID、空suffixを拒否する。
- root / profile / overrideのmissing key、unknown key、wrong container typeを拒否する。

### 11.2 load / limit / recovery

- `settings_path.parent / "profiles.json"`、`SettingsStore`注入時の同一directory、明示`profiles_path` overrideを直接検証する。
- `settings_path`と`settings_store`の同時指定を拒否し、default pathへtest fileを作らないことを検証する。
- file不存在、0件、1件、100件がmutation availableでloadできる。
- 101件を`limit_exceeded`で拒否する。
- malformed JSON、UTF-8 failure、non-file、read failure、schema version bool / 0 / 2、duplicate ID / nameを分類する。
- 途中entryだけvalidなfileをpartial importしない。
- failure後のvalid reloadとfile削除reloadでcollection / availability / errorが置換される。
- broken profile fileでもB2 built-in setと既存preset storeが独立して利用可能である。

### 11.3 mutation / atomicity

- constructor直後はmutation unavailableであり、load前Create / Update / Deleteが`store_not_loaded`を返すことを検証する。
- load前mutationが既存JSON、missing target、in-memory tuple、temporary fileを変更しないことを検証する。
- load前`get_profile()`が`ProfileContractError`、load完了後のunknown / malformed IDが`None`になることを検証する。
- CreateがUUIDを生成し、明示ID seamでもdeterministicに保存できる。
- Updateがstable IDとlist orderを維持し、同じdisplay nameの自己更新を許可する。
- Deleteが対象だけを除去し、不明IDを`profile_not_found`とする。
- duplicate、101件目、invalid inputでfileとcollectionを変更しない。
- structurally validなmissing preset IDをB3 storeが保持し、暗黙fallbackしない。
- raw store mutationがINI active ID、preset file、runtime stateを変更しない。
- temporary fileがsame directoryに作られ、replace前にclose済みである。
- write / replace failureでold JSON、old tuple、temporary cleanup、mutation unavailableを検証する。

### 11.4 SettingsStore

- default settingsでactive profile ID 2種が`None`である。
- valid / unknown string、empty、whitespace、explicit `None`をround-tripする。
- invalid non-string inputはdefaultへ戻し、`invalid_keys` / `used_default_keys`へ記録する。
- `[ui]`へadditiveに保存し、既存section / unknown key / recent settingsを維持する。
- old INIのkey欠落をdefaultへ読む。
- 旧callerが2 keyを省略した`save({"theme": ...})`と`save(None)`で既存IDを保持する。
- 明示`None`では2 keyを個別にclearできる。
- existing `active_preset_id`、generation settings、save-disabled契約を変更しない。

### 11.5 runtime user data / ignore

- testは`tmp_path`または`TemporaryDirectory`だけへINI / JSONを作る。
- repository rootの`profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`がtest前後で変更されない。
- `git check-ignore -v profiles.json`がroot ruleを示す。
- subdirectoryの`profiles.json`は同ruleでignoreされない。no-matchのexit code 1は期待結果として区別する。

### 11.6 実行順

最小から順に、一つのcommandごとに結果とprocess exit codeを確認する。

1. `tests/test_ms23_b3_model_profiles.py`
2. `tests/test_settings_store.py`と`tests/test_ms22_b3_generation_presets.py`
3. MS23-B2 morph-name set / adapter / import boundary
4. SettingsStoreを使うwx export / generation state / preset UI / lifecycle回帰
5. full suite
6. `compileall src tests`
7. `git diff --check`
8. root / subdirectoryの`git check-ignore`確認

計画作成時のread-only baselineは次のとおりである。

- B2 + preset / settings: 53 passed、19 subtests passed、process exit code 0
- SettingsStore consumer群: 67 passed、19 subtests passed、process exit code 0

両commandには重複testがあるため、合計件数として加算しない。

### 11.7 manual / actual-MMD

- B3はUI非依存のstore / settings blockであり、manual GUI確認を必須受け入れ条件にしない。
- GUIへprofileを接続するB5でmanual pathを定義する。
- 実MMDでのVMD / WAV読み込み・リップ同期はMS26へdeferredのままとする。

## 12. 受け入れ条件

- `ModelProfile`とnullable override DTOがimmutableで、B1 schemaと一致する。
- `profiles.json`のroot / entry / overridesがexact key setで、schema version 1、0〜100件を扱う。
- 101件、型不正、範囲外、unknown key、duplicate ID / name、invalid set ID、invalid reference形式をfail closedにする。
- `morph_upper_limit`はstrict finite float 0.0〜10.0とし、bool / int / stringを拒否する。hold / softnessはstrict int 0〜100、modeは`hold | decay`に限定される。
- Japanese / Latin set IDをB2 registryから検証し、built-in set本体をJSONへ保存しない。
- `default_preset_id`はstable referenceとして保存し、preset値を複製しない。
- structurally validなmissing preset referenceをB3が暗黙fallbackせず、B4 resolutionへ渡す。
- file不存在はempty / writable、broken / future / unreadable fileはempty / mutation unavailableとして安全に処理される。
- constructor直後はunloaded / mutation unavailableで、初回load前のlookup / Create / Update / Deleteが既存file、missing target、memory、temporary fileを変更しない。
- valid reloadまたはfile削除reloadでstore availabilityが回復する。
- Create / Update / Deleteがdeterministicに動き、mutationだけでcurrent runtime stateやINIを変更しない。
- save / replace failure後に旧JSONとin-memory tupleが保持され、temporaryがcleanupされる。
- JSON保存がUTF-8、same-directory temporary、close-before-replace、`os.replace()`である。
- INIの`active_model_profile_id`と`active_profile_baseline_preset_id`が独立してround-tripし、unknown IDをB3が消去しない。
- default `profiles.json` pathがINIと同じdirectoryで、`SettingsStore`注入、明示path override、constructor引数排他が直接testされる。
- 旧callerが新2 keyを省略したsaveで既存IDが保持され、明示`None`ではclearできる。
- existing `active_preset_id`、generation settings、SettingsStore result / save-disabled契約を変更しない。
- `/profiles.json`がroot限定ignoreされ、subdirectory同名fileは過剰ignoreされない。
- repository rootのruntime user dataをtest・実装が生成、変更、stageしない。
- B3専用、関連回帰、full suite、`compileall src tests`、`git diff --check`がpass表示だけでなくprocess exit code 0である。
- GUI、state、history、diagnostics、writer、VMD、30fps、audio、dependency、package、networkへscope外変更がない。
- B3完了を実MMD確認済みと表現しない。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| B3がpreset参照を解決し、startup fallbackを先行実装する | B3はreference構造だけを検証し、lookup / fallback / guardをB4へ固定する |
| raw store Updateでactive profile契約を破る | raw storeはcontext-free persistenceと明記し、B4がcommit前guardを必ず通す。GUIから直接呼ばない |
| display name / UUID規則がpresetとずれる | 現行preset contractと同じ境界を専用testで固定し、private helper importやpreset実装変更は行わない |
| upper limitがB1より広いint / string / bool / non-finiteを受理する | strict floatだけを受理し、finite / 0.0〜10.0をDTOで検証する |
| built-in morph setをprofile JSONへ複製する | profileはstable set IDだけを保存し、B2 registryを唯一の正本にする |
| profile JSON破損でpresetや日本語defaultまで停止する | profile store failureを独立させ、B2 set / preset / INIへ副作用を出さない |
| theme等の旧save経路がactive profile IDを消去する | 新2 keyをSettingsStore merge-preserve対象へ追加し、省略save回帰を必須化する |
| baseline IDだけ存在する不整合をB3が勝手に修復する | raw IDを保持し、B4だけが組の正規化と必要時保存を行う |
| Windowsでopen tempをreplaceして失敗する | same-directory tempを明示closeし、close-before-replaceをmock / observation testで確認する |
| write failure後も同じmutationを反復してfileを危険にする | session mutationをunavailableにし、明示reloadでだけ回復する |
| load前mutationが既存profileを空collectionで上書きする | constructor直後をunloaded / mutation unavailableとし、`store_not_loaded`でfile access前に拒否する |
| target path実装を誤ってもexplicit test pathだけで検証が通る | settings path、SettingsStore注入、explicit override、引数排他を直接testする |
| testがrepository rootのruntime fileを作る | 全store / settings testへtemporary pathを注入し、root file非変更をscope監査する |
| `/profiles.json`がfixtureまでignoreする | leading slash ruleとsubdirectory no-matchを別々に検証する |
| B3でGUI / state / packageへscope creepする | 対象ファイル、Out of Scope、diff監査をgateにする |

## 14. Codex実装時の注意

- 実装開始前に本planをfresh read-onlyで再チェックし、レビュー未完了のままproduction codeへ着手しない。
- shell commandは必ず一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`を使用しない。
- 編集は小さなpatchに分け、既存worktree変更を保持する。
- `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini`を作成・変更・stageしない。
- testはtemporary directoryだけを使い、default pathを実書込みしない。
- ModelProfileStoreは明示`load()`完了前にlookup結果やmutationを利用せず、load前拒否testを弱めない。
- B3 storeへpreset storeやGUI stateを注入してcross-store resolver化しない。
- `src/core/generation_presets.py`のprivate helperをimportせず、既存preset behaviorを変更しない。
- `src/core/__init__.py`をB4の将来都合で変更せず、B3では`src.core.model_profiles`のleaf importを使う。
- B2のJapanese / Latin mapping、日本語default、writer / Preview / diagnostics契約を変更しない。
- Qt / PySide6、network、cloud、telemetry、auto-download、新dependencyを追加しない。
- fixed Japanese morph default、VMD形式、30fps、audio role / limitを変更しない。
- validation / write / replace failureを成功扱いせず、pass表示とprocess exit codeを分けて記録する。
- 実装diffを少なくとも一度scope監査し、検証後に要求、plan、diff、test、repository stateを再監査する。
- commit、push、merge、tag、release、branch削除は別途明示承認があるまで行わない。
- 完了報告では、確認ファイル、変更ファイル、実装内容、test command / result / exit code、仕様逸脱、残課題、B4 handoffを分ける。

## 15. 実装・検証記録（2026-08-17）

- `src/core/model_profiles.py`へimmutable DTO、strict schema v1 codec、load前gate、fail-closed load、lookup、Create / Update / Delete、same-directory temporaryとclose-before-`os.replace()`のatomic persistenceを実装した。
- `src/core/settings_store.py`へ`active_model_profile_id`と`active_profile_baseline_preset_id`をadditiveに追加し、空値・未知値の保持、明示`None`によるclear、旧caller省略時の既存値保持を実装した。
- `.gitignore`へroot限定`/profiles.json`を追加し、`tests/test_ms23_b3_model_profiles.py`へDTO、schema、path seam、load / reload、mutation、atomic failure、SettingsStore回帰を追加した。
- B3専用は`21 passed, 31 subtests passed`、B2 / preset / SettingsStore関連は`74 passed, 50 subtests passed`、wx / lifecycle関連は`38 passed`、全体は`759 passed, 57 subtests passed`で、各process exit code 0だった。
- `compileall src tests`と`git diff --check`はprocess exit code 0だった。root `profiles.json`はignoreされ、subdirectoryの同名fileはignoreされなかった。
- manual GUI確認はB3の必須gateではなく、今回実施していない。実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままである。
- B4 handoff: `default_preset_id`の参照解決、active profile / runtime baselineの正規化、precedence、mutation guard、runtime state統合は未実装であり、B4の責務として引き継ぐ。
