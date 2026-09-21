# MS25-B4 Implementation Plan

## 1. 文書情報

- 文書名: MS25-B4 診断・identity・レポート契約 Implementation Plan
- 対象マイルストーン: MS25 MMD Delivery Package Export
- 対象Block: MS25-B4 診断・identity・レポート契約
- 作成日: 2026-09-01
- 対象ブランチ: `feature/MS25-implementation`
- 計画作成時HEAD: `904ccae Implement MS25-B3 delivery artifact adapters`
- 状態: B4実装済み・自動検証済み。production code / test codeは`01b4d4f Implement MS25-B4 diagnostic report identity`でコミット済み。GUI、README、Roadmap、runtime user data、設定、依存関係はB4実装で変更していない
- 直接依存:
  - MS25-B1: 同一captureの`EffectiveShapePlan`、`OutputDiagnosticsSnapshot`、resolved ordered morph names、Whisper summary、fingerprintを保持する`DeliveryCurrentState` / `DeliveryStartContext`
  - MS25-B2: staging、固定3成果物、pre-commit guard、no-clobber commit、cancel / cleanup / terminal result
  - MS25-B3: 同じ開始snapshot / timestampを共有formatterとwriterへ渡し、report bytesを同じformatter結果と完全一致検証するproduction adapter
- 本文書作成時の変更権限: 本文書の新規作成だけ。production code、test code、README、Index、Roadmap、runtime user data、設定、依存関係、stage、commit、pushは対象外
- ユーザー判断待ち: なし。必須identity、既存placeholder、Whisper semantic / runtime identity、組み込みmorph set、shared formatter利用は現行資料と実装から確定できる
- 計画作成時の関連回帰baseline:
  - `tests/test_ms20_b6_diagnostic_report.py`
  - `tests/test_ms23_b6_model_profile_lifecycle.py`
  - `tests/test_ms24_whisper_diagnostics.py`
  - `tests/test_ms25_b3_delivery_artifacts.py`
  - 合計`46 passed`、process exit code `0`、Python `3.14.3`
- 実装結果: report identity必須化、safe `DiagnosticReportError`、profile未使用・既定morph setを含むreport fieldを実装し、B4専用testを追加した。B4は可視GUI actionを追加しないため、手動GUI確認は受け入れ必須ではない。
- 未検証・後続: 実FFmpeg、実MMD、Python 3.11 / 3.12、PyInstaller onefile、package / release確認。MS25-B5のGUI・worker・状態統合は後続Blockとして実装済みである。

### 1.1 正本と現行状態の優先順位

B4の判断には次の順を使う。

1. live Git、現行production code、現行test
2. `docs/Implementation_Plan/MS25_Block_Breakdown.md`
3. 実装済みMS25-B1 / B2 / B3のpublic contractと専用test
4. `docs/MS20_and_Beyond_Roadmap.md` §12〜§15、MS23 / MS24の完了契約、現行仕様書
5. Indexと既存Implementation Planの過去時点記録

現行HEADにはB1 / B2 / B3のproduction codeとtestが存在する。MS25 IndexとB3計画の状態欄は、B3実装済み状態へ同期済みである。B1前提guard / regression testとこれらの文書同期はB4 production implementationに先行する作業ツリー変更であり、B4の対象差分には含めず、B4実装中も保護する。B4ではlive codeとこの同期済み状態を正とする。

## 2. 背景

MS25は、現在の編集済み状態からVMD、元の入力音声からMMD用WAV、同じ開始時点の診断snapshotからreportを生成し、一つの専用directoryへtransactionalに確定する。

B1からB3までに、次の境界が実装済みである。

- B1の`DeliveryCurrentState`は、同じcaptureの`EffectiveShapePlan`、`OutputDiagnosticsSnapshot`、resolved ordered morph names、開始fingerprint、`projection_generation`を保持する。
- `build_output_diagnostics_snapshot_from_ui_state()`は、渡された`output_morph_names`を組み込み日本語 / Latin setへ解決し、そのset ID / display nameを`GenerationDiagnosticsSummary`へ格納する。
- `OutputDiagnosticsSnapshot`は、active preset、model profile、resolved morph-name set、`WhisperDiagnosticsSummary`、generation / adjustment / saveability / diagnostics、fingerprint、`projection_generation`をimmutableに保持する。
- B3のreport operationは、`DeliveryStartContext.current_state.diagnostics_snapshot`と`report_generated_at`を`format_diagnostic_report()`と`write_diagnostic_report()`へ渡し、書込み後のbytesが同じformatterの期待bytesと完全一致することを確認する。
- `write_diagnostic_report()`はUTF-8、LF、BOMなし、same-directory temporary file、byte検証、`os.replace()`、失敗時temporary cleanupを所有する。
- B2はB3 operationが正常終了したreportだけをstagingの一成果物として受け入れ、3成果物すべての成功後にだけfinal directoryへcommitする。

現行`format_diagnostic_report()`には、B4契約に対して次の不足がある。

1. model profileが`no_profile`かつmorph setが既定日本語の場合、profile / morph identity行全体を省略する。
2. resolved morph-name setのID / display nameは条件付きで出力するが、ordered morph namesを出力しない。
3. `WhisperDiagnosticsSummary`はloaded / analysis modelのdisplay nameを保持するが、reportはkey / manifest identityだけを出力している。
4. `write_diagnostic_report()`は内部例外文字列を`DiagnosticReportError`のmessageへ連結するため、standalone保存失敗時に不要なabsolute path等が通常dialogへ表示され得る。

加えて、B4の前提として、VMDとreportのmorph identityが同じcapture由来であることを確認する必要がある。現行`DeliveryCurrentState.__post_init__()`は`output_morph_names`を組み込みsetへ正規化し、effective frame countを確認するが、snapshotの`resolved_morph_name_set_id`とのcross-field一致までは拒否していない。B4はB1 DTO / gateを再設計しないため、実装開始前にこの整合性が現行B1経路とtestで証明できることを必須前提とする。証明できない場合は、B4へ混ぜず、別B1補修を先に完了させる。

active preset ID / display name、Whisper selected / activeのkey / display name / manifest identity、loaded / analysisのkey / manifest identity、package version / gate status、failure分類、`projection_generation`は既に常時出力されている。B4はこれらを作り直さず、不足行を共有formatterへ加算的に補う。

## 3. 目的

MS25-B4では、次を実装可能な契約として固定する。

1. profile未使用、fallback、既定日本語morph setを含む全snapshotで、preset / profile / morph set / Whisper identityの行を省略しない。
2. profile未使用時に架空のprofile IDやdisplay nameを生成せず、既存の`N/A` / `(not available)` placeholderと、正本である`model_profile_resolution_status=no_profile`または`fallback_no_profile`を同時に記録する。
3. resolved morph-name set IDから現行の組み込みsetを解決し、ID / display nameに加えてordered morph namesを決定的に記録する。
4. Whisper selected / active / loaded / analysisについて、key、display name、manifest identityをそれぞれ独立した行として記録し、semantic identityとruntime identityを混同しない。
5. package version / gate status、failure分類、safe notice、`projection_generation`等の既存Whisper記録を維持する。
6. B3のsame-snapshot / same-timestamp / exact-bytes契約と、standalone reportの共有formatter契約を維持する。
7. report writer失敗の外向け`DiagnosticReportError`を固定safe messageにし、元例外はexception chainへ保持して通常表示へ連結しない。
8. VMDとreportのmorph identityが同じresolved setに対応するB1 current-state前提を、B4着手前のfresh checkで証明する。証明できない場合はB4を開始せず、別B1補修へ戻す。
9. report表現とsafe error境界の変更だけに限定し、snapshot DTO、fingerprint schema、B1 gate、B2 transaction、B3 adapter、GUI、runtime user dataを変更しない。

B4完了は一括出力GUIの利用可能化を意味しない。GUI / worker接続はB5、transaction / shutdown hardeningはB6、利用者文書とcloseout準備はB7、実MMD確認はMS26、package / release readinessはMS27の責務である。

## 4. In Scope

- `src/core/diagnostic_report.py`の共有formatterを加算的に補正する。
- `[Generation]` sectionでprofile / morph identity行を常時出力する。
- active preset ID / display nameの既存常時出力を維持し、未選択時の`N/A` / `Custom`表現を回帰固定する。
- profile ID / name / baseline ID / baseline name / resolution status / resolution reasonを常時出力する。
- profile未使用時はID / name / baselineを既存placeholderで出し、resolution statusの`no_profile`を正本として出す。
- `fallback_no_profile`では既存placeholderとfallback status / reason codeを同時に出す。
- resolved morph-name set ID / display nameを既定日本語setでも常時出力する。
- resolved morph-name set IDから`get_builtin_morph_name_set()`でordered namesを取得し、次の固定表現で出力する。

```text
Resolved Morph Names (Ordered): あ / い / う / え / お
Resolved Morph Names (Ordered): A / I / U / E / O
```

- `[Whisper]` sectionへ次の不足行を追加する。

```text
Loaded Model Display Name: <snapshot value or (not available)>
Analysis Model Display Name: <snapshot value or (not available)>
```

- selected / active / loaded / analysisのkey / display name / manifest identity、analysis / runtime identity statusを同じ`WhisperDiagnosticsSummary`から出力する。
- package name / version、package gate status、manifest schema version、failure class / detail code、safe notice、recoverability、`projection_generation`の既存出力を維持する。
- `_single_line()`によるcontrol character / CR / LF / tab / backslash escapeを、新規表示値にも適用する。
- `DiagnosticReportError`の通常表示用messageからraw exception textとabsolute pathを除き、元例外を`raise ... from error`のcauseへ保持する。
- B4専用のreport identity testを追加する計画。
- MS20 report golden testを新しい固定構造へ更新する計画。
- MS23 profile、MS24 Whisper、MS25 B1 / B3 report境界の関連回帰を実行する計画。

## 5. Out of Scope

- `OutputDiagnosticsSnapshot`、`GenerationDiagnosticsSummary`、`WhisperDiagnosticsSummary`へのfield追加・変更
- `DiagnosticSnapshotInput`、`build_output_diagnostics_snapshot()`、`build_output_diagnostics_snapshot_from_ui_state()`の変更
- `DeliveryCurrentState.output_morph_names`、B1 capture / gate / fingerprint contractの変更
- `ms21-effective-output-v1` schema、payload、canonical order、digestの変更
- Whisper selected / active / loaded / analysis identityの再計算
- Whisper model selection、download、verify、loader、runtime cache、analysis、rollbackの変更
- preset / profile / morph setのstore、resolution、mutation、UIの変更
- B2 staging / no-clobber commit / cancel / cleanup / terminal resultの変更
- B3 VMD / WAV / report adapter、VMD validator、source audio identityの変更
- delivery専用report schema、formatter flag、manifest、hash、追加成果物
- reportへのfinal directory、staging directory、package pathの追加
- reportへのraw exception、traceback、credential、URL、Whisper storage absolute path、temporary pathの追加
- standalone reportとdelivery reportを別formatterへ分岐すること
- GUI menu、button、folder dialog、WARNING確認、Busy、worker、late callback、window close
- README、`readme_mmdautolip.txt`、Index、Roadmap、Block Breakdown、正文仕様の同期
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読書き、コピー、stage
- dependency、`pyproject.toml`、lock file、PyInstaller spec、build script、license文書の変更
- 実MMD確認（MS26）
- onefile、ZIP、最終artifact、package / release readiness（MS27）
- stage、commit、merge、push、tag、release

## 6. 前提条件

### 6.1 snapshotを唯一のreport正本とする

B4 formatterは`OutputDiagnosticsSnapshot`とtimezone-awareな`generated_at`以外を参照しない。`UiState`、GUI control、preset / profile store、Whisper runtime、`DeliveryCurrentState`、filesystem destinationを再参照しない。

reportへ記録するidentity sourceは次のとおりとする。

| report identity | 正本field | B4で禁止する代替 |
| --- | --- | --- |
| active preset | `generation_summary.active_preset_id` / `active_preset_display_name` | profile baselineからの推測、store再lookup |
| model profile | `active_model_profile_*`、`active_profile_baseline_preset_id`、`baseline_preset_display_name`、resolution status / reason | GUI選択値、current store再lookup |
| morph-name set | `resolved_morph_name_set_id` / `resolved_morph_name_set_display_name` | Preview表示、VMD読戻し、profile store再lookup |
| ordered morph names | snapshotのresolved set IDに対応する組み込み`MorphNameSet.output_names` | 日本語固定、任意custom mapping、別captureの`DeliveryCurrentState` |
| Whisper | `snapshot.whisper_summary` | `UiState.whisper_model_selection`やruntime loaderの再参照 |
| projection generation | `snapshot.projection_generation` | formatter呼出回数、worker job ID |

B1のproduction captureでは、一度だけ解決したordered morph namesをdiagnostics adapterと`DeliveryCurrentState`の双方へ渡している。B4はこの既存境界をtestで確認するが、B1 DTOやgateを再実装しない。

B4実装前の必須前提として、`DeliveryCurrentState.output_morph_names`が
`diagnostics_snapshot.generation_summary.resolved_morph_name_set_id`に対応する組み込みtupleと一致することを、live B1 code / testから確認する。現行DTOにこの拒否guardがない場合、B4のformatterだけではmalformed contextを救済できないため、B4実装を開始せず、B1補修の別planまたは明示承認へ戻す。B4はこの補修を暗黙に取り込まない。

### 6.2 preset / profileの明示値

- active presetがない既存Custom状態は、現行どおり`Active Preset ID: N/A`と`Active Preset Display Name: Custom`とする。
- active presetがある場合はsnapshotのID / display nameをそのまま出す。
- profile未使用時に`active_model_profile_id=None`を文字列`no_profile`へ置換しない。架空のstable IDを作るとsnapshot semanticsと異なるためである。
- profile未使用時はID / display name / baselineを既存placeholderで出し、`Model Profile Resolution Status: no_profile`を明示する。
- `fallback_no_profile`はstatusとreason codeを明示し、意図したprofile未使用とfallbackを区別する。
- `resolved` / `fallback_profile_default`はsnapshotのprofile / baseline identityをそのまま出す。
- profile使用中のactive presetとprofile baselineは別identityであり、一つの欄へ統合しない。

### 6.3 morph-name set

- 現行contractは組み込み日本語`あ / い / う / え / お`とLatin`A / I / U / E / O`の2 setである。
- `GenerationDiagnosticsSummary`のvalidationはset IDが組み込みsetであり、display nameがそのsetと一致することを保証する。
- formatterはIDから同じ組み込みsetを取得し、`output_names`のtuple順を維持して` / `で連結する。
- sort、deduplicate、case変換、Unicode normalization、翻訳、暗黙fallbackを行わない。
- lookupが成立しない異常snapshotを日本語defaultへ置換しない。formatter failureとしてfail closedにする。

### 6.4 Whisper identity

- selectedは候補選択、activeは解析要求のsemantic正本、loadedはruntime resident model、analysisは現在の成功解析結果のprovenanceである。
- selected / active / loaded / analysisを、一つの「現在モデル」へ統合しない。
- `analysis_identity_status`はactive対analysis、`runtime_identity_status`はactive対loadedの既存評価結果を表示する。B4 formatterで再比較しない。
- loaded / analysisのdisplay nameはsummaryに既に存在するため、DTO追加なしでreportへ出す。
- availability / management表示専用状態をfingerprintへ追加せず、B4のreport表示変更によってsnapshotやdigestを変えない。
- package versionはsummaryの要求版、package gate statusは別fieldであり、両者を「実行成功版」として統合しない。

### 6.5 shared formatterと互換性

`format_diagnostic_report()`はstandalone reportとdelivery reportの共有正本である。B4はdelivery専用flagや二つ目のformatterを追加せず、両導線へ同じ加算的identity行を適用する。

- 既存section名、既存field名、既存field順を削除・改名しない。
- 新しいprofile / morph行は`[Generation]`内のactive preset / long-vowel情報の後、空行の前に置く。
- loaded / analysis display nameは各keyとmanifest identityの間に置く。
- UTF-8、LF、BOMなし、末尾LF、timezone付きGenerated Atを維持する。
- package専用version numberやreport schema versionを追加しない。

### 6.6 Error Handling契約

`docs/Error_Handling_Specification.md` §26.4と§30の保存保護・通常表示の安全境界を適用する。§5.4 / §31が求める利用者向けの詳細表示・copy導線は、既存`AppController`に対する別のGUI/error-detail契約であり、B4の実装対象へ拡張しない。B4はこの詳細表示・copy導線を実装済みとは記録しない。

- report保存失敗時もtiming plan、failure、diagnostics snapshot、save-state fingerprint、WARNING確認済み状態を保持する。
- temporary fileをcleanupし、既存の正常reportを変更しない。
- full path、ユーザー名を含むpath、traceback全文は通常表示へ出さない。
- 原因調査用の元例外はexception chainへ保持できるが、B4では新しい詳細表示UIやcopy導線を追加しない。cause保持は、利用者向けの詳細表示・copy導線の完了を意味しない。
- `DiagnosticReportError`の外向けmessageは、正確に`診断レポートを安全に保存できませんでした。`とする。元例外のpath、OS message、detailはmessageへ連結しない。既存`AppController`が`str(error)`をdialogへ投影しても、表示されるdetailはこの固定safe messageだけになる。
- exception detailの表示・copy対応は、safe通常表示と分離した別UI契約として、B4の後続工程または別途承認されたGUI/error-detail planへ引き継ぐ。

## 7. 対象ファイル

### 7.1 B4実装時の主変更対象

| 種別 | ファイル | B4責務 |
| --- | --- | --- |
| 既存変更 | `src/core/diagnostic_report.py` | profile / morph行の常時出力、ordered morph names、loaded / analysis Whisper display nameの加算的出力、writer failureのsafe message |
| 既存変更 | `tests/test_ms20_b6_diagnostic_report.py` | exact fixed structureの更新、共有formatter / writerの既存契約回帰 |
| 既存変更 | `tests/test_ms20_b6_report_save_flow.py` | 既存AppControllerのreport save error投影が固定safe messageだけを表示する契約の回帰 |
| 新規 | `tests/test_ms25_b4_delivery_report_identity.py` | no-profile、fallback、resolved profile、Japanese / Latin morph、preset、Whisper 4 identity、B3 delivery reportのsame-snapshot検証 |

### 7.2 関連確認対象。B4では変更しない

B4実装の差分監査は、実装開始時点の作業ツリーをbaselineとして行う。現在のbaselineに含まれるB1前提guard / regression test、MS25 Index、B3計画、B4計画のP2/P3補正は、B4の事前変更として保護し、B4実装の変更件数・対象ファイルへ二重計上しない。

- `src/core/output_diagnostics.py`
- `src/core/morph_name_sets.py`
- `src/core/delivery_package.py`
- `src/core/delivery_artifacts.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `tests/test_ms25_b1_delivery_contract.py`
- `tests/test_ms25_b1_current_state_gate.py`
- `tests/test_ms25_b3_delivery_artifacts.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_ms21_b5_effective_output_identity.py`

### 7.3 B4では変更しない対象

以下はB4実装による追加変更の対象外である。B4着手前に存在する同期済み差分の有無と、B4実装後に新たな差分が発生していないことを分けて監査する。

- `src/core/output_diagnostics.py`のDTO、validation、fingerprint builder
- `src/core/morph_name_sets.py`のset定義
- `src/core/delivery_package.py`のB1 / B2契約
- `src/core/delivery_artifacts.py`のB3 operation
- `src/gui_wx/`配下すべて
- B1 / B2 / B3の既存test期待を、B4を通すために弱化する変更
- README、配布用readme、Index、Roadmap、Block Breakdown、既存Implementation Plan、正文仕様
- runtime user data、設定、dependency、build / package / license file

## 8. 実装方針

### 8.1 formatterを単一変更点とする

`format_diagnostic_report()`の入力と戻り値signatureを変更しない。`snapshot.generation_summary`と`snapshot.whisper_summary`から、次をpureに導出する。

1. `resolved_morph_name_set_id`を`get_builtin_morph_name_set()`へ渡す。
2. 返された`output_names`をtuple順のまま`_single_line()`へ通し、` / `で連結する。
3. 現行のconditional `profile_lines`を常時構築へ変更する。
4. profile行末にresolved set ID / display name / ordered namesを置く。
5. Whisper loaded / analysis keyの直後へ各display nameを置く。

必要なら`diagnostic_report.py`内部に、小さいprivate helperを追加してよい。

```python
def _display_ordered_morph_names(values: tuple[str, ...]) -> str:
    return " / ".join(_single_line(value) for value in values)
```

public API、`src/core/__init__.py`、snapshot schemaは変更しない。

### 8.2 exact report field contract

`[Generation]`のidentity部分は、全snapshotで次の行を同じ順に持つ。

```text
Active Preset ID: ...
Active Preset Display Name: ...
Effective Long Vowel Hold Run Count: ...
Effective Long Vowel Decay Run Count: ...
Active Model Profile ID: ...
Active Model Profile Display Name: ...
Active Profile Baseline Preset ID: ...
Baseline Preset Display Name: ...
Model Profile Resolution Status: ...
Model Profile Resolution Reason: ...
Resolved Morph Name Set ID: ...
Resolved Morph Name Set Display Name: ...
Resolved Morph Names (Ordered): ...
```

profile未使用・既定日本語setの最小表現は次とする。

```text
Active Model Profile ID: N/A
Active Model Profile Display Name: (not available)
Active Profile Baseline Preset ID: N/A
Baseline Preset Display Name: (not available)
Model Profile Resolution Status: no_profile
Model Profile Resolution Reason: (not available)
Resolved Morph Name Set ID: builtin:japanese-vowels
Resolved Morph Name Set Display Name: 日本語5母音
Resolved Morph Names (Ordered): あ / い / う / え / お
```

`[Whisper]`は少なくとも次の4組を持つ。

```text
Selected Model Key / Display Name / Manifest Identity
Active Model Key / Display Name / Manifest Identity
Loaded Model Key / Display Name / Manifest Identity
Analysis Model Key / Display Name / Manifest Identity
```

実際のlabelは現行labelを維持し、loaded / analysisのDisplay Name行だけを加算する。

### 8.3 B3 contractの再利用

B3はformatterとwriterへ同じsnapshot / timestampを渡しているため、B4で`delivery_artifacts.py`を変更しない。formatter変更後も次が自動的に成立する。

- expected bytesとwriter bytesが同じB4 formatterから生成される。
- report read-backが新しいidentity行を含むbytesと完全一致しなければ`report_validation_failed`になる。
- formatter / writer failureは`report_write_failed`へ正規化される。
- report failure時はB2がfinal commitを行わず、owned staging cleanupを担当する。

B4 testでは、この既存operationへB4 snapshotを渡し、出力reportが同じsnapshotとordered namesを記録することを確認する。

### 8.4 privacy / failure contract

- 新規行は既存snapshotのsafe fieldと組み込みmorph namesだけを使う。
- raw exception、traceback、credential、URL、environment variable、Whisper storage absolute path、temporary pathをformatterへ追加しない。
- display name等は`_single_line()`を通し、改行やcontrol characterでreport構造を注入させない。
- invalid morph identityを日本語defaultへfallbackさせない。formatterが例外を返し、standalone writerでは`DiagnosticReportError`、deliveryでは`report_write_failed`となる既存fail-closed経路を使う。
- `write_diagnostic_report()`の外向け例外messageは、正確に`診断レポートを安全に保存できませんでした。`とする。内部の`PermissionError`、path、OS message等は文字列連結せず、`__cause__`へ保持する。既存`AppController`が`str(error)`をdialogへ投影しても、表示されるdetailはこの固定safe messageだけになる。
- `DiagnosticReportError`のtypeとcatch境界は維持し、GUI側に新しいerror DTOや表示分岐を追加しない。Error仕様§5.4 / §31の利用者向けdetail/copy UIはB4外の明示的な残課題であり、B4の受け入れ条件へ混在させない。
- formatter / writerはsnapshot、workspace diagnostics、WARNING確認済みfingerprint、preset / profile storeを変更しない。
- report表現だけの変化で`save_state_fingerprint`を再計算しない。

## 9. 詳細ステップ

### Step 1: 実装開始前再確認

- live Git、branch、HEAD、user-owned差分を確認する。
- B1 / B2 / B3 production moduleと関連testが現行HEADに存在することを確認する。
- `diagnostic_report.py`のconditional profile行、Whisper行、writer contractを再確認する。
- `GenerationDiagnosticsSummary`と`WhisperDiagnosticsSummary`の現行field / validationを再確認する。
- `DeliveryCurrentState.output_morph_names`とsnapshotの`resolved_morph_name_set_id`のcross-field一致が現行B1 code / testで拒否されるかを確認する。拒否guardが確認できなければ、B4実装を開始せず、別B1補修の必要性を記録してユーザー判断へ戻す。
- 本plan以外の既存文書driftをB4実装へ混ぜない。

### Step 2: profile / morph identityの常時出力

1. `get_builtin_morph_name_set`を`diagnostic_report.py`から直接importする。
2. generation summaryのresolved set IDから組み込みsetを解決する。
3. conditional `profile_lines`を常時構築へ変更する。
4. existing profile / baseline / resolution / morph set ID / display name行のlabelと値変換を維持する。
5. ordered names行を固定位置へ追加する。
6. no-profile / fallback / resolved profileの値をformatter側で推測せず、snapshot fieldと既存placeholderだけで表現する。

### Step 3: Whisper 4 identityの表示完成

1. `Loaded Model Key`の直後に`Loaded Model Display Name`を追加する。
2. `Analysis Model Key`の直後に`Analysis Model Display Name`を追加する。
3. selected / activeの既存3行を変更しない。
4. identity status、manifest / package / failure / management / storage / projection行を変更しない。
5. summary外のWhisper stateを参照しない。

### Step 4: writer failureのsafe化

1. `write_diagnostic_report()`のcatchで、元例外文字列を外向けmessageへ連結しない。
2. fixed safe messageで`DiagnosticReportError`をraiseし、`from error`でcauseを保持する。
3. missing parent、permission / replace failure、temporary validation failureでraw path / OS messageが`str(error)`へ出ないことをtestする。
4. existing target保護、temporary cleanup、error typeを変更しない。

### Step 5: existing golden test更新

- `tests/test_ms20_b6_diagnostic_report.py`のexact fixed structureへ、default no-profile / Japanese morph行とWhisper placeholder display行を追加する。
- 既存section順、UTF-8、LF、BOMなし、末尾LF、determinism、timestamp差分、atomic writer failure cleanupの期待を維持する。
- writer failure testはraw文字列matchをやめ、fixed safe message、raw detail不在、`__cause__`保持、既存file保護をexactに確認する。
- exact testを部分一致へ弱化しない。

### Step 6: B4専用test追加

`tests/test_ms25_b4_delivery_report_identity.py`で少なくとも次を確認する。

- no active presetでは`N/A` / `Custom`が常時存在する。
- active presetではexact ID / display nameが出る。
- no-profile / Japanese defaultでもprofile / baseline / resolution / morph行が全て存在する。
- `fallback_no_profile`ではstatusとreason codeが省略されない。
- resolved profile / Latin setではprofile ID / name / baseline / resolutionと`A / I / U / E / O`が一致する。
- reportのordered morph namesが、production B1 captureの`DeliveryCurrentState.output_morph_names`と同じ順である。
- Whisper selected / active / loaded / analysisのkey / display name / manifest identityが別々のsnapshot fieldから出る。
- `analysis_identity_status`と`runtime_identity_status`を入れ替えない。
- package version / gate status、failure class / detail、projection generationを維持する。
- control characterを含むdisplay fieldが単一行へescapeされる。
- raw secret / storage path等を新規行へ混入させない。
- writer failureの通常messageへraw exception / absolute pathを含めず、causeへ内部例外を保持する。
- B3 report operationが同じsnapshot / timestampを使い、B4必須行を含むexact bytesを生成する。
- report generation failureがsnapshot、fingerprint、WARNING確認identityを変更しない。

### Step 7: scope / diff監査

- 変更が§7.1の3 filesだけであることを確認する。
- `output_diagnostics.py`、`delivery_package.py`、`delivery_artifacts.py`、`src/gui_wx/`、runtime data、dependency、build fileに差分がないことを確認する。
- fingerprint schema / payload / digestを変更していないことを確認する。
- B5以降のGUI、worker、transaction hardening、文書closeoutを先行実装していないことを確認する。

### Step 8: 自動検証

§11の順でtargeted、cross-boundary、full、static checksを一コマンドずつ実行し、pass表示とprocess exit codeを別々に記録する。

## 10. 状態遷移 / データ契約

### 10.1 B4 formatting flow

```text
immutable OutputDiagnosticsSnapshot + timezone-aware generated_at
  -> format_diagnostic_report
       preset identity: existing fields / placeholders
       profile identity: always present
       morph identity: built-in set ID -> ordered output names
       Whisper identity: selected / active / loaded / analysis kept separate
       existing generation / adjustment / saveability / diagnostics retained
  -> deterministic UTF-8 text with LF and trailing LF
  -> write_diagnostic_report
       same-directory temporary write
       exact byte read-back
       BOM / UTF-8 validation
       atomic file replace
  -> B3 delivery report read-back
       same formatter expected bytes == actual bytes
  -> B2 staging validation / commit guard / no-clobber commit
```

B4は新しいworkspace state、worker state、delivery terminal stateを追加しない。

### 10.2 identity不変条件

- formatterが受け取るsnapshotは一つであり、途中で再buildしない。
- active presetとprofile baselineを混同しない。
- profile IDが`None`のとき架空IDを生成しない。
- profile未使用でもresolution statusとmorph set identityを省略しない。
- ordered morph namesはresolved set IDに対応する組み込みtupleと一致する。
- Japanese / Latin namesの順序はsemantic vowel order `a / i / u / e / o`に対応する現行tuple順を維持する。
- Whisper selected / active / loaded / analysis identityは独立したfieldから出す。
- loaded / analysis display nameをselected / active display nameから推測しない。
- `projection_generation`は表示するが、fingerprintやfilesystem commit guardへ追加しない。
- B4 report表現変更の前後でsnapshot object、fingerprint payload、digestは不変である。

### 10.3 profile状態別表示

| snapshot状態 | ID / name / baseline | status / reason | morph identity |
| --- | --- | --- | --- |
| `no_profile` | existing placeholder | `no_profile` / reasonなしplaceholder | Japanese defaultを明示 |
| `fallback_no_profile` | existing placeholder | exact fallback status / reason | resolved fallback setを明示 |
| `resolved` | exact profile / baseline identity | `resolved` / reasonなしplaceholder | exact resolved setを明示 |
| `fallback_profile_default` | exact profile / fallback baseline identity | exact status / reason | exact resolved setを明示 |

### 10.4 例外・失敗契約

| failure | standalone report | delivery report | state / filesystem結果 |
| --- | --- | --- | --- |
| naive timestamp | direct formatterはexisting `ValueError`、writerはfixed safe `DiagnosticReportError` | B3 `report_write_failed` | final package commitなし |
| morph set lookup不成立 | direct formatterは`ValueError`、writerはfixed safe `DiagnosticReportError`、元例外はcause | B3 `report_write_failed` | silent Japanese fallbackなし |
| formatter / encoding失敗 | direct formatter error、writerはfixed safe `DiagnosticReportError`、元例外はcause | B3 `report_write_failed` | snapshot不変、B2 cleanup |
| write / replace失敗 | fixed safe `DiagnosticReportError`、existing target保護、temporary cleanup | B3 `report_write_failed` | raw detail通常表示なし、final package commitなし |
| final bytes不一致 | writer failureまたはB3 `report_validation_failed` | B3 `report_validation_failed` | final package commitなし |
| cancel | B4対象外 | B3 / B2の既存`output_cancelled` | committed finalをcancelへ上書きしない |

raw exception messageをreport本文と外向け`DiagnosticReportError` messageへ書かない。B4はexception typeとB3 error-code mappingを変更しない。

## 11. テスト方針

### 11.1 B4専用test

`tests/test_ms25_b4_delivery_report_identity.py`:

- default no-profile / Japanese setの全必須行とexact order
- no-profileで架空profile IDを出さず、status `no_profile`を出すこと
- fallback no-profileのreason保持
- active presetとprofile baselineの分離
- resolved profile / Latin setのID / name / baseline / ordered names
- production captureの`output_morph_names`とreport ordered namesの一致
- Whisper 4 identityのkey / display / manifestの独立表示
- semantic / runtime identity status、package / gate、failure、projectionの保持
- placeholdersとcontrol character escape
- formatter determinism、snapshot / fingerprint不変
- fixed safe writer error message、raw detail不在、cause保持、既存file保護
- `DiagnosticReportError`の`str(error)`が固定safe messageだけを返し、元例外のabsolute path / OS messageが通常表示へ流れないこと。既存AppControllerの`詳細: {error}`投影を含め、raw detailが表示されないこと
- B3 operationのsame-snapshot / same-timestamp / exact bytes
- report failure時のworkspace / fingerprint不変とB2 no-commit
- B4実装前のB1前提として、`DeliveryCurrentState.output_morph_names`とsnapshotのresolved morph set IDが同じ組み込みtupleを示すこと。拒否guardまたは同等の証拠がなければB4を開始しない

### 11.2 既存関連回帰

- `tests/test_ms20_b6_diagnostic_report.py`
  - fixed structure、UTF-8 / LF / BOMなし、atomic write、既存file保護、cleanup
- `tests/test_ms20_b6_report_save_flow.py`
  - standalone reportがVMD saveabilityから独立する契約
- `tests/test_ms23_b6_model_profile_lifecycle.py`
  - profile / Latin morph identity、fingerprint非変更
- `tests/test_ms24_whisper_diagnostics.py`
  - exact `WhisperDiagnosticsSummary`、safe projection、fingerprint非変更
- `tests/test_ms25_b1_delivery_contract.py`
  - immutable start state、ordered morph names、same snapshot / fingerprint
- `tests/test_ms25_b1_current_state_gate.py`
  - one capture / one morph resolution / same-plan snapshot
- `tests/test_ms25_b3_delivery_artifacts.py`
  - report same snapshot / timestamp、exact bytes、B2 orchestration
- `tests/test_ms21_b5_effective_output_identity.py`
  - existing fingerprint schema / semantic identity

### 11.3 実装後の実行順

各commandは一つずつ実行し、pass件数とprocess exit codeを記録する。

1. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b4_delivery_report_identity.py`
2. `.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b6_diagnostic_report.py`
3. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b3_delivery_artifacts.py`
4. `.\.venv\Scripts\python.exe -m pytest tests/test_ms23_b6_model_profile_lifecycle.py tests/test_ms24_whisper_diagnostics.py`
5. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py tests/test_ms20_b6_report_save_flow.py tests/test_ms21_b5_effective_output_identity.py`
6. `.\.venv\Scripts\python.exe -m pytest tests/test_ms25_b4_delivery_report_identity.py tests/test_ms20_b6_diagnostic_report.py tests/test_ms23_b6_model_profile_lifecycle.py tests/test_ms24_whisper_diagnostics.py tests/test_ms25_b1_delivery_contract.py tests/test_ms25_b1_current_state_gate.py tests/test_ms25_b3_delivery_artifacts.py`
7. `.\.venv\Scripts\python.exe -m pytest tests`
8. `.\.venv\Scripts\python.exe -m compileall -q src tests`
9. `rg -n "[ \t]+$" src/core/diagnostic_report.py tests/test_ms20_b6_diagnostic_report.py tests/test_ms25_b4_delivery_report_identity.py`
10. `git diff --check`

9の`rg`はno-matchのprocess exit code `1`を「末尾空白なし」として扱う。test failureをskip、削除、期待弱化で回避しない。

### 11.4 manual GUI / 実MMD / package境界

- B4はGUI action、dialog、worker、Busy、cancel、closeを追加しないため、manual GUI確認を受け入れ必須にしない。
- standalone report保存dialogとdelivery GUIは変更しない。GUI上のdelivery report確認はB5接続後に行う。
- 必要に応じて生成txtの目視確認を補助証拠として実施してよいが、自動testの代替やGUI検証済みとは扱わない。
- B4はVMD / WAV bytesを変更しない。実MMDでのVMD / WAV読込、再生、リップ同期はMS26へ維持する。
- B4はdependency、spec、build script、bundled fileを変更しない。PyInstaller onefile、ZIP、最終artifact、package / release readinessはMS27へ維持し、B4受け入れのためにbuildを要求しない。
- 実FFmpeg、Python 3.11 / 3.12を実施していない場合は未検証と記録する。Python 3.14.3のtest結果で代替しない。

## 12. 受け入れ条件

### 12.1 report identity

- [ ] active preset ID / display nameが全reportに存在し、未選択時は既存`N/A` / `Custom`を維持する。
- [ ] profile ID / name / baseline / resolution status / reasonが全reportに存在する。
- [ ] no-profileで架空IDを生成せず、placeholderと`no_profile` statusを明示する。
- [ ] fallback no-profileのstatus / reasonが意図したno-profileと区別できる。
- [ ] resolved profileではexact profile / baseline identityが出る。
- [ ] morph set ID / display name / ordered namesが全reportに存在する。
- [ ] Japaneseは`あ / い / う / え / お`、Latinは`A / I / U / E / O`の順で出る。
- [ ] Whisper selected / active / loaded / analysisのkey / display name / manifest identityが別々に出る。
- [ ] semantic / runtime identity status、manifest schema、package version / gate、failure分類、projection generationを維持する。

### 12.2 snapshot / formatter / B3整合

- [ ] formatterが一つの`OutputDiagnosticsSnapshot`とtimezone-aware timestampだけを使う。
- [ ] B1 production captureのordered namesとreportのordered namesが一致する。
- [ ] B4着手前のfresh checkで、`DeliveryCurrentState.output_morph_names`とsnapshotの`resolved_morph_name_set_id`が同じ組み込みtupleを示すことを証明する。現行B1に拒否guardまたは同等の証拠がなければ、B4実装を開始せず別B1補修へ戻す。
- [ ] B3が同じsnapshot / timestampをformatterとwriterへ渡し、actual bytesをexpected bytesと完全一致検証する。
- [ ] standalone reportとdelivery reportが同じ共有formatterを使う。
- [ ] formatter変更でsnapshot、workspace state、WARNING確認identity、fingerprint payload / digestが変化しない。
- [ ] `ms21-effective-output-v1` schema / payload / canonical orderを変更していない。
- [ ] UTF-8、LF、BOMなし、末尾LF、fixed section orderを維持する。

### 12.3 failure / privacy

- [ ] invalid morph identityを暗黙日本語fallbackせずfail closedにする。
- [ ] formatter / writer / validation failureでfinal packageがcommitされない。
- [ ] report failureでworkspace diagnostics stateが壊れない。
- [ ] raw exception、traceback、credential、URL、Whisper storage / temporary absolute pathをreportへ追加しない。
- [ ] standalone writer failureの`DiagnosticReportError` messageへraw exception / absolute pathを含めず、元例外をcauseへ保持する。
- [ ] standalone writer failureの外向けmessageが正確に`診断レポートを安全に保存できませんでした。`であり、既存AppControllerの`詳細: {error}`投影にもraw exception / absolute pathが現れない。
- [ ] B4はError仕様§5.4 / §31の利用者向けdetail/copy UIを実装済みとは主張せず、safe通常表示・cause保持との境界を文書化する。
- [ ] 新規display値にもsingle-line escapeを適用する。
- [ ] standalone writerの既存file保護とtemporary cleanupを維持する。

### 12.4 scope / verification

- [ ] B4実装開始時baselineからのproduction code追加差分が`src/core/diagnostic_report.py`だけである。
- [ ] B4実装開始時baselineからのtest追加差分が`tests/test_ms20_b6_diagnostic_report.py`、`tests/test_ms20_b6_report_save_flow.py`、新規B4 testだけである。
- [ ] B4実装開始時baselineに存在するB1前提guard / regression test、MS25 Index、B3計画、B4計画のP2/P3補正を除き、snapshot DTO、B1 / B2 / B3、GUI、runtime data、設定、dependency、build / package fileへ追加差分がない。
- [ ] B4専用test、指定回帰、full pytestがpass表示かつprocess exit code `0`である。
- [ ] `compileall -q src tests`と`git diff --check`がprocess exit code `0`である。
- [ ] 未実施のmanual GUI、実FFmpeg、実MMD、Python 3.11 / 3.12、onefile / release確認を未検証と報告する。

## 13. リスクと対策

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS25-B4-R1 | formatterがcurrent GUI / storeを再参照し、VMDとreportが別snapshotになる | P1候補 | immutable snapshotだけを入力にし、B3 same-object / timestamp testを維持する |
| MS25-B4-R2 | no-profile / default morphでidentity行が省略される | P2候補 | conditional profile linesを撤去し、placeholder + resolution status + resolved setを常時出力する |
| MS25-B4-R3 | no-profileを架空のprofile IDへ変換し、snapshot semanticsと異なる | P2候補 | ID / nameは既存placeholder、正本statusは`no_profile` / `fallback_no_profile`として分離する |
| MS25-B4-R4 | ordered namesを日本語固定にし、Latin VMDとreportが不一致になる | P1候補 | snapshotのvalidated set IDから組み込みtupleを解決し、B1 contextとの一致をtestする |
| MS25-B4-R5 | morph set lookup失敗を日本語へfallbackし、誤ったreportをcommitする | P1候補 | silent fallback禁止。formatter failureからB3 `report_write_failed`、B2 no-commitへ進む |
| MS25-B4-R6 | loaded / analysis display nameをselected / activeから流用し、Whisper identityを混同する | P2候補 | summaryの4つの独立fieldをそのまま出し、異なる値のtestを置く |
| MS25-B4-R7 | report項目追加のためsnapshot / fingerprint schemaを変更する | P1候補 | existing summary fieldとbuilt-in resolverだけを使い、DTO / fingerprint fileを変更禁止にする |
| MS25-B4-R8 | delivery専用formatterを追加してstandalone reportと意味が分岐する | P2候補 | shared formatter一つを加算的に更新し、両導線を回帰する |
| MS25-B4-R9 | display nameの改行等でreport field構造が壊れる | P2候補 | 全新規表示値を`_single_line()`へ通し、control文字testを追加する |
| MS25-B4-R10 | Whisper management値やraw pathをfingerprint / report identityへ混入する | P2候補 | existing safe summaryだけを表示し、fingerprint builderとraw stateを変更しない |
| MS25-B4-R11 | writerがraw OS error / pathを外向け例外messageへ連結する | P2候補 | fixed safe message + exception chainに分離し、既存cleanup / target保護を維持する |
| MS25-B4-R12 | exact golden testを部分一致へ弱化し、field欠落や順序変更を見逃す | P3候補 | MS20 exact structure testを更新し、B4 dedicated exact order testを追加する |
| MS25-B4-R13 | Index / B3 planの実装状態driftをcurrent事実と誤認する | P3・外部文書drift | live HEADを優先し、Index / B3 plan / B4 planの現行状態記述を同期する |
| MS25-B4-R14 | B1 current stateのmorph namesとsnapshotのresolved set IDが不一致でも、report formatter単独ではVMDとの矛盾を救済できない | P2候補 | B1 `DeliveryCurrentState`へcross-field reject guardと回帰testを追加し、B4開始前提を実装上でもfail-closedにする |
| MS25-B4-R15 | AppControllerの`詳細: {error}`投影へwriterのraw OS message / absolute pathが流入する | P2候補 | 外向けmessageを`診断レポートを安全に保存できませんでした。`へ固定し、cause保持と既存GUI投影のraw detail不在をtestする |
| MS25-B4-R16 | Error仕様§5.4 / §31のdetail/copy UI要求と、B4のGUI変更なし境界が混在する | P2候補 | B4はsafe通常表示・cause保持までとし、利用者向けdetail/copy UIを後続の別GUI/error-detail契約へ明示的に分離する |

### 13.1 P1 / P2 / P3自己監査

初期案を現行Roadmap、Block Breakdown、B1 / B2 / B3 code、MS23 / MS24 identity契約、report testsへ再照合し、次を本文へ反映した。

| finding | 初期の曖昧さ | 本文での修正 | 状態 |
| --- | --- | --- | --- |
| P1-1 | delivery report向けにcurrent stateを再captureする余地があった | shared formatterは開始snapshotだけを入力とし、B3 same-object契約を再利用 | 解消 |
| P1-2 | ordered namesをformatter引数やDTOへ追加するとB1 / B3境界が変わる | validated resolved set IDから組み込みtupleをpure導出し、B1 production capture一致testを置く | 解消 |
| P2-1 | profile未使用時の「明示値」が架空IDかplaceholderか未固定だった | ID / nameは既存placeholder、statusは`no_profile`等の正本値と固定 | 解消 |
| P2-2 | morph set ID / nameだけでordered namesが不足していた | exact labelとJapanese / Latinの固定出力を追加 | 解消 |
| P2-3 | Whisper loaded / analysis display nameがsummaryにあるがreportにない | 既存fieldから2行を加算し、4 identityを独立test | 解消 |
| P2-4 | B4都合でsnapshot / fingerprintを拡張する余地があった | production変更をformatter一件へ限定し、DTO / fingerprintを変更禁止 | 解消 |
| P2-5 | standaloneとdeliveryでreport意味が分岐し得た | shared formatterへ加算し、両導線を同じ受け入れ条件にする | 解消 |
| P2-6 | standalone writerがraw internal error / pathを通常dialogへ露出し得た | fixed safe `DiagnosticReportError` messageとexception causeを分離 | 解消 |
| P3-1 | exact structure test更新とB4固有のdelivery evidenceが不足していた | MS20 golden更新 + B4専用test新設へ固定 | 解消 |
| P3-2 | Index / B3 planがlive B3実装済み状態と不一致 | Index / B3 plan / B4 planの状態欄とactive registryを現行状態へ同期 | 解消 |
| P2-7 | B1 current stateのmorph namesとsnapshot resolved set IDの整合性をB4 scope内で暗黙に保証する余地があった | `DeliveryCurrentState`のcross-field guardとB1回帰testを追加し、B4着手前提を実装上でも固定 | 解消 |
| P2-8 | AppControllerの既存`詳細: {error}`投影とwriterのraw例外messageの境界がexactでなかった | safe messageを固定し、cause保持・raw detail不在を既存投影込みでtest対象へ追加 | 解消 |
| P2-9 | Error仕様§5.4 / §31のdetail/copy UI要求と、B4のGUI変更なし境界が混在していた | B4の受け入れ範囲をsafe通常表示・cause保持までに限定し、detail/copy UIを別の後続契約へ分離 | 解消（スコープ境界を固定） |

B4 plan本文に未解消のP1 / P2はない。detail/copy UIはB4外の明示的な後続課題であり、B4の安全な通常表示・cause保持の受け入れ条件とは混同しない。Index / B3 planの状態driftも現行状態へ同期した。B4で追加質問が必要な未確定分岐はない。

## 14. Codex実装時の注意

- 実装開始前にlive Git、branch、HEAD、user-owned差分を再確認する。
- コマンドは一つずつ実行し、shell pipeline、chain、parallel executionを使わない。
- B4 production変更を`src/core/diagnostic_report.py`一件へ限定する。
- 実装開始前にB1 current-stateのcross-field invariantを確認する。`output_morph_names`とsnapshotのresolved morph set IDが一致するguardまたは同等の証拠がなければ、B4へ補修を混ぜず、別B1補修の完了まで開始しない。
- `OutputDiagnosticsSnapshot`、`GenerationDiagnosticsSummary`、`WhisperDiagnosticsSummary`へfieldを追加しない。
- `DeliveryCurrentState`や`DeliveryStartContext`をformatter引数へ追加しない。
- profile未使用時に架空のID / display nameを作らない。
- active presetとprofile baselineを同じidentityとして表示しない。
- morph namesを日本語固定、alphabet sort、Unicode normalize、trim、case変換しない。
- unknown morph IDを日本語defaultへsilent fallbackしない。
- Whisper 4 identityを一つのcurrent modelへ統合しない。
- `UiState`、preset / profile store、Whisper runtimeをformatterから再参照しない。
- existing section / fieldを削除・renameせず、加算的な行追加に限定する。
- raw exception、storage path、temporary pathをreport本文へ追加しない。
- `DiagnosticReportError`の外向けmessageは`診断レポートを安全に保存できませんでした。`に固定し、元例外はcauseだけへ保持する。
- Error仕様§5.4 / §31のdetail/copy UIをB4実装済みとは記録しない。必要になった場合はsafe通常表示・cause保持と独立したGUI/error-detail planで扱う。
- fingerprint schema / payload / digest、diagnostic item identityを変更しない。
- B3 exact-bytes validationを弱めず、delivery adapterへB4専用分岐を追加しない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`を直接読書き、コピー、stageしない。
- testを削除、skip、部分一致化してfailureを回避しない。
- manual GUI、実MMD、onefileを実施していなければ未検証と記録する。
- diff自己監査でB5 / B6 / B7、MS26 / MS27の先行実装がないことを確認する。
- stage、commit、merge、push、tag、releaseは各々の明示承認まで行わない。

### 14.1 実装完了報告

実装担当は少なくとも次を報告する。

1. 確認したファイル
2. 変更したファイル
3. 実装した必須identity行と維持した既存契約
4. 実行した各test / static check
5. pass件数とprocess exit code
6. fingerprint、dependency、runtime data、GUI、packageへの差分有無
7. manual GUI / 実FFmpeg / 実MMD / Python 3.11 / 3.12 / onefileの実施・未実施
8. P1 / P2 / P3自己監査結果と残課題

### 14.2 次工程への引き継ぎ

1. 本planのreview後、fresh read-only pre-implementation checkで現行HEADと対象3 filesを再照合する。
2. 明示的なB4実装承認後に、§7.1の3 filesだけを変更して§11の検証を行う。
3. B4実装後reviewで、same-snapshot、identity必須化、fingerprint非変更、privacy、scopeを再監査する。
4. B5で一括出力action、destination dialog、WARNING、long-audio confirmation、Busy、delivery worker、job-bound commit authorization、close待機を接続する。B4 formatterをGUI側で再実装しない。
5. B6でactual Windows collision / reparse / locked / cleanup / cancel / shutdown matrixをhardeningする。
6. B7でfull / cross-boundary回帰、README、配布用readme、Pipeline / GUI / Error / VMD / WAV仕様、Index、Roadmap、既存plan状態driftを実装済み状態へ同期する。
7. MS26で実MMDへdelivery VMD / WAVを読み込み、再生とリップ同期を確認する。
8. MS27でPyInstaller onefile、ZIP、最終artifact、package / release readinessを別工程として判定する。
