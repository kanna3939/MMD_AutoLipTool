# MS21 Block Breakdown

## 1. 文書情報

- 文書名: MS21 Block Breakdown
- 配置: `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- 対象マイルストーン: MS21
- Title: Per-Event Lip Adjustment / In-Memory Edit History
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `6cd8233 Close out MS20 diagnostics milestone`
- 作成日: 2026-07-20
- 文書ステータス: Active / MS21-B7 Complete / MS21-B8 Plan Created /
  B8 Plan Corrections Applied / Closeout A / MS22 Handoff Recorded /
  Automated Verification Passed / User Manual GUI Verification Passed
- 上位正本:
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/MS20_and_Beyond_Roadmap.md`
- 関連仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/MS16_GUI_Layout_Spec_for_Antigravity.md`

本書はMS21内の責務、依存順、状態契約、検証境界を定める。各Blockの実装前には個別の `MS21-Bx_Implementation_Plan.md` を作成し、本書だけを直接の実装指示としない。

## 2. 現在状態

- MS20はCloseout A、ユーザーチェック通過・問題なしとして完了した。
- `main / origin/main` は `6cd8233` で同期済みである。
- `feature/MS21-implementation` は同期済み `main` から作成済みで、upstreamは未設定である。
- MS21-B1からB4は実装・自動検証・ユーザー確認まで完了した。MS21-B5は2026-07-26にeffective writer、fingerprint、diagnostic report統合を実装し、ユーザーGUI確認も通過・問題なしと報告された。同日、単イベントの終了offset・hold・softnessだけに直後異母音とのcrossfadeを許可する追加補正を実装した。追加補正の限定回帰はすべてpass表示・process exit code 0、全体は576件と7 subtestsがpass表示したがprocess exit code 1だった。追加補正のユーザーGUI確認も通過・問題なしと報告され、B5は追加補正を含め完了した。
- MS21-B6は実装・自動検証・ユーザーGUI確認まで完了した。
- MS21-B7 Implementation Planは実装状態整合レビューと2026-07-27の実装前チェックを
  反映し、同日にproduction実装と自動検証を完了した。rollback、dirty入力保護、
  parameter一致、terminal guard、single-pass context、adjustment-only同期を実装した。
  startup splash testの実SplashScreen破棄漏れによるwx access violationを最小補修し、
  aggregate wx testのprocess exit code 0を回復した。その後のユーザー手動GUI確認で
  event click時の「選択イベント」タブ自動切替要望が提示され、追加補正を実装・
  自動検証した。2026-07-27に追加補正を含むB7範囲のユーザー手動GUI確認が通過し、
  問題なしと報告された。
- MS21-B8 Closeout Implementation Planは2026-07-31に作成し、現行実装・test・依存・
  build設定との整合を確認した。B7計画に残っていたB7-PRE-004の「実装前gate」表記は
  実測済みの `closed (2026-07-27)` へ補正済みである。B8監査ではB1〜B7の証拠台帳、
  指定回帰、full suite、文書・配布境界を確認し、P1 / P2 / P3なしのCloseout Aを確定した。
- B8 pre-implementation checkで検出した文書境界のP2 / P3は、計画作成・レビュー段階と
  Closeout監査開始段階のclean gate分離、明示的な回帰test file群、B8計画§15の証拠台帳を
  追加して修正した。監査開始時のclean確認と監査結果の文書同期を完了した。
- wxPythonが主系GUIである。
- `VowelTimingPlan` とその `timeline` は自動解析結果の正本であり、ユーザー補正はimmutable canonical adjustment snapshotとして分離される。
- Preview、diagnostics、VMD writerはshared `EffectiveShapePlan` を共通派生元にする。
- Previewは `selected_source_event_index`、選択highlight、RightPane structured editorを持つ。
- Previewは4 DIP thresholdでclick選択とdrag panを分離し、click hit-testからcanonical real base eventを選択できる。
- RightPaneの「選択イベント」タブはevent補正control、反映制限notice、manual crossfade noticeを表示する。
- 近接した同一母音はwriter / Preview生成時にgroup化され、multi-point shapeでは複数のsource event indexが単一segmentへ集約され得る。
- same-vowel candidate変換は元eventをskipし、負数のsynthetic source tokenを持つshape pointへ置換する場合がある。このtokenはbase event identityではない。
- MS20のsave-state fingerprint、Warning確認、diagnostic reportは現行writer入力に接続済みである。MS21の補正がwriter出力を変える場合、同じidentity契約へ接続する必要がある。

### 2.1 計画作成baseline

- `tests/test_wx_ms16_b6_event_selection_foundation.py`: 4件pass表示、process exit code 0
- Preview / writer / pipeline / diagnostics / save policy回帰: 71件pass表示、process exit code 0
- workspace reset / diagnostics lifecycle / analysis / playback回帰: 32件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1
- 計画作成時点でproduction code、test code、dependency、build設定は変更していない。

## 3. 背景

MS21では、自動解析結果を直接書き換えず、発音イベント単位のユーザー補正をPreviewとVMD出力へ同じ意味で反映する。

MS16で選択状態とRightPaneの表示枠は用意されたが、ユーザー操作によるhit-test、編集UI、補正データ、writer接続、Undo / Redoは存在しない。MS20でdiagnostics snapshotとsave-state fingerprintがwriter出力のidentityとして確立したため、MS21の補正はこの契約を迂回してはならない。

また、現在のPreviewはwriter shapeを可視化する過程で近接イベントをgroup化する。単一描画segmentが複数source eventを表す場合があるため、単純にsegment先頭indexだけを選択正本にすると、イベント単位編集と一致しない。B1でbase event、grouped shape、hit-test、adjustment keyの対応を固定してから実装へ進む。

## 4. 目的

- base timing planを不変の解析正本として保持する。
- user adjustment layerを明示的な差分正本として追加する。
- Preview上のイベント選択とRightPane編集を成立させる。
- PreviewとVMD writerが同一resolverのeffective resultを使用する。
- Undo / Redoをセッション内snapshot履歴として提供する。
- MS20 diagnostics、WARNING確認、reportへ編集後identityを接続する。
- input、reanalysis、reset、Busy、save failureで補正・選択・履歴が誤って持ち越されないようにする。

## 5. In Scope

- Preview上のclick hit-testとイベント選択
- click選択とdrag panの競合回避
- RightPane「選択イベント」タブの本実装
- 選択イベントの読み取り専用base値と編集値の表示
- 開口量、開始、終了、hold、softness、slopeの補正契約
- base timing planとuser adjustment layerの分離
- UI非依存adjustment model、validation、resolver
- 選択イベントreset、全編集reset
- セッション内Undo / Redo
- adjustment layer snapshot方式
- 履歴上限50操作
- 連続する数値変更の1操作への集約
- Previewへの即時反映
- effective writer inputへの反映
- save-state fingerprint、Warning確認、diagnostic reportとの整合
- Busy、input変更、解析開始・成功・失敗・cancel、late callback、新規作業の状態遷移
- TEXTあり / voice_only双方の回帰
- README、配布用readme、Pipeline / GUI / Error仕様の同期

## 6. Out of Scope

- adjustment layer、選択、Undo / Redo履歴のセッション外永続化
- VMD読み戻し
- 任意キーフレーム編集
- 汎用タイムライン編集
- 複数イベント一括編集
- 母音種別の変更
- 新しいモーフ名または固定モーフ `あ / い / う / え / お` の変更
- MS22の長音preset、生成preset
- MS23のmodel profile
- MS24のWhisper model選択
- MS25の一括出力
- package、release、version bump、tag
- Qt / PySide6の復活
- network、cloud ASR、音声外部送信、background通信、Whisper自動download

## 7. MS21共通設計契約

### 7.1 baseとadjustmentの分離

- `UiState.current_timing_plan` は解析結果のbase正本として直接変更しない。
- adjustment layerはbase eventを参照するセッション内データであり、表示widgetの値を正本にしない。
- adjustment未指定のeventはbase値をそのまま使用する。
- adjustmentを全削除すると、effective resultはbase timing planと同じ意味へ戻る。
- resolverは同じbaseと同じadjustment snapshotに対して決定的な結果を返す。

### 7.2 event identity

- canonical `base_event_index` はnormalization / sorting前のbase timing plan内の0-based ordinalとする。observations present時だけ、対応するobservation `event_index` との一致を必須とする。
- observationsなしのplanを許可し、observation依存candidate shapingなしでbase eventを補正できる。present時は長さ、event index、vowel対応の不一致をfail closedで拒否する。
- observations present時のcandidate参照indexは、lookup前に型・範囲・span順序・previous / next bracketing順序を検証し、不正参照を `AdjustmentContractError` で拒否する。
- adjustment key、canonical selection、history keyには `base_event_index` だけを使用する。
- writer内部の負数synthetic source indexは `shape_source_token` として分離し、選択・編集対象にしない。
- 単なる描画順、RightPane行番号、group後segment番号をadjustment keyにしない。
- shared shape provenanceはsynthetic pointを含むshape tokenと、それに寄与したreal base event indices / event rangesを別fieldで保持する。
- candidate変換でskip / zero-spanとなったbase eventもprovenanceとevent別hit regionから失わない。
- input変更または新しいbase plan確定時に、旧plan用adjustmentを新planへ自動移植しない。
- indexが範囲外、対応eventが消失、非有限値を含むadjustmentはfail closedで拒否する。

### 7.3 補正値

- 開口量は固定モーフのpeak valueへ作用する。解析時upper limit、writerの非負・有限値契約、Preview表示clampを混同せず、存在しないwriter上限clampを前提にしない。
- 開始 / 終了補正はevent boundaryへ作用し、負frame、start > peak、peak > end、隣接shapeとの不正競合を生成しない。
- hold、softness、slopeは既存writer shape契約へ明示的に接続し、任意キーフレーム編集へ拡張しない。
- hold / softnessは現行global controlと同じ0から100の整数範囲とし、modelは範囲外をclampせず拒否する。
- canonical保存単位はB1で30fps writer境界と秒ベースtimelineを照合して固定する。UI表示単位と内部正本を混同しない。
- B1でcanonical編集単位を整数frameに固定した。base秒値とsource durationは `int(round(seconds * 30))` で一度だけ変換し、`0 <= start <= peak <= end <= source duration` を必須とする。
- slopeは閉口途中の強度比 `0.0〜1.0`、既定 `0.7` とする。effective softnessがmidpointを生成できない場合は編集を無効化してoverrideを拒否し、grouping / clamp変更でmidpointが消えた場合は同一transaction内で既存overrideをcanonical removalする。

### 7.4 resolver

- PreviewとVMD保存は同じUI非依存resolverからeffective resultを取得する。
- B2はautomatic candidate shape、real base provenance、補正優先、candidate再評価、groupingを含むshared shape preparation contractを所有する。
- B2はwriter非依存の専用 `EffectiveShapePlan` DTOを `src/core/effective_shape_plan.py` で所有する。writer / Preview adapterがcore resultをimportする一方向依存とし、core resolverからwriter private helperをimportしない。
- Preview専用変換結果やRightPane表示文字列をwriter入力へ戻さない。
- resolverはbaseを変更せず、新しいimmutable resultを返す。
- resolver順序は、identity / observation検証、provenance付きautomatic candidate準備、real base eventへのpeak / start / end補正、影響candidate span再評価、grouping、group末尾tail補正、shape生成とする。
- ユーザー補正はautomatic candidateより優先し、skip / synthetic置換されたeventを補正した場合は該当spanを補正後eventで再評価する。
- VMD保存時には直前のcurrent adjustment snapshotからeffective writer inputを再構築し、古いPreview cacheを正本にしない。

### 7.5 選択とhit-test

- clickとdrag panを移動距離thresholdで分離する。
- viewport外、空lane、無効Preview、Busy中の入力は選択を変更しない。
- overlap時の優先順位を決定的にする。
- multi-source groupではclick位置をB2 provenanceのreal base event rangeへ対応付ける。候補が重なる場合はbase peak frameへの距離が短いevent、同距離では小さい `base_event_index` を選び、segment先頭indexを暗黙に採用しない。
- visible segmentだけでなくB2 provenanceのeffective base event rangeからhit regionを構築し、synthetic tokenをselectionへcommitしない。
- 既存render-only `PreviewPanel` setterが未知indexを一時保持する互換性は維持し、B3のcanonical commit境界で範囲外・stale・negative tokenを拒否する。
- selectionは編集対象の参照であり、adjustment snapshotやUndo履歴そのものではない。

### 7.6 Undo / Redo

- 履歴要素はadjustment layer全体のimmutable snapshotとする。
- 最大50操作を保持し、上限超過時は最古のundo可能snapshotから破棄する。
- 新しい編集確定時はredo stackを破棄する。
- 連続する同一event・同一fieldの数値変更は、明示的な編集開始 / 更新 / 確定境界により1操作へ集約する。
- selection変更、tab切替、Preview pan / zoom、playback位置変更は履歴操作に含めない。
- reset selected、reset allはUndo可能な1操作として扱う。
- input変更、新base plan確定、新規作業によるworkspace破棄はUndo不能で、adjustmentと履歴をclearする。再解析開始時はrollback候補を一時保持する。

### 7.7 diagnostics / save identity

- effective VMD出力が変わるadjustmentはsave-state fingerprintへ必ず反映する。
- adjustment変更時は同一fingerprintに対するWARNING確認済み状態を再利用しない。
- ERROR / WARNING保存policyはMS20契約を維持する。
- diagnostic reportはRightPane文字列から生成せず、current snapshotから生成する。
- reportへadjustment情報を追加する場合、schema名、section順、空値、fingerprintとの関係をB5で明示する。
- VMD保存失敗とdialog cancelでは有効なbase、adjustment、historyを保持する。

### 7.8 lifecycle

- input commit、新base plan確定、新規作業ではselection、adjustment、Undo / Redoをclearする。
- input dialog cancelのようにworkspaceが変わらない操作では保持する。
- 解析開始時は旧base、adjustment、Undo / Redoをrollback候補として一時保持し、編集をlockする。current job成功時に新baseへ切り替えて旧編集を破棄する。
- analysis failure / cancel時は、旧baseを再利用できる場合だけadjustmentと履歴を復元する。input / parameter変更等で旧baseが無効なら破棄する。
- 旧base再利用は、job開始時に有効なrollback snapshotがあり、開始後にinput / transcription / parameter / reset / 別jobの変更がなく、current job IDとbase identityが一致する場合だけ許可する。
- failure復元時はERRORを保持しVMD保存を禁止する。cancel復元時はcancel INFO付きfingerprintを再構築し、WARNING確認済みfingerprintを復元しない。failure rollbackは現行正本仕様からの意図的なMS21将来変更であり、B7が実装後に仕様を同期する。
- late / duplicate callbackはcurrent selection、adjustment、history、effective previewを変更しない。
- Busy中は編集、reset、Undo / Redoを無効化する。
- playback、pan、zoomはadjustment identityを変更しない。

## 8. Block一覧

| Block | 名称 | 主責務 | 依存 |
| --- | --- | --- | --- |
| MS21-B1 | Adjustment Contract / Current-State Pre-check | **完了**: identity、補正値、grouping順序、lifecycle、history境界の固定 | MS20 Closeout |
| MS21-B2 | Adjustment Core / Shared Shape Resolver | **完了**: UI非依存model、validation、canonical snapshot、shape provenance、group-aware resolver | B1 |
| MS21-B3 | Preview Hit-Test / Event Selection | **完了**: click選択、pan競合回避、group選択、selection同期、ユーザーGUI確認 | B1、B2 |
| MS21-B4 | RightPane Event Editor / Live Preview | **完了**: 編集UI、base/effective表示、即時Preview、reset selected、反映制限notice、自動検証、ユーザーGUI確認 | B2、B3 |
| MS21-B5 | VMD Save / Diagnostics Integration | **完了**: effective保存・diagnostics統合、単イベントcrossfade追加補正、自動検証、ユーザーGUI確認 | B2、B4、MS20 |
| MS21-B6 | In-Memory Undo / Redo | **完了**: snapshot履歴、50操作、coalescing、reset all、自動検証、ユーザーGUI確認 | B2、B4、B5 |
| MS21-B7 | State Integration / Regression / Docs / Adjustment Sync Efficiency | **完了**: lifecycle rollback、late callback、dirty入力保護、parameter一致、Undo / Redo同期効率化、選択event tab自動切替、自動検証、ユーザーGUI確認、文書同期 | B3〜B6 |
| MS21-B8 | MS21 Closeout | 要求・code・test・user・docs監査、A / B / C判定 | B1〜B7 |

## 9. Block依存関係

```text
MS20 Closeout
  -> B1 Contract / Pre-check
      -> B2 Adjustment Core / Shared Shape Resolver
          -> B3 Preview Hit-Test / Selection
              -> B4 RightPane Editor / Live Preview
                  -> B5 VMD / Diagnostics Integration
                      -> B6 Undo / Redo
                          -> B7 State / Regression / Docs
                              -> B8 MS21 Closeout
```

B3のselectionはB2のcanonical event identityとshape provenanceに依存する。B4はB2 shared resolverを使用してlive Previewを構築する。B5は同じresolver resultを保存とdiagnosticsへ接続し、B5で別resolver semanticsを初めて実装しない。B6はB2のimmutable snapshotを再利用し、UI値の複製履歴を作らない。

## 10. MS21-B1: Adjustment Contract / Current-State Pre-check

**Status: 完了 (2026-07-21)**

### 10.1 目的

production codeを変更せず、event identity、grouping、補正値、resolver順序、history、lifecycle、diagnostics引き継ぎを固定する。

### 10.2 In Scope

- `VowelTimingPlan.timeline` とobservationのindex対応
- Preview / writer groupingとmulti-source shape
- hit-test対象とoverlap優先順位
- 開口量、開始 / 終了、hold、softness、slopeの単位・範囲
- slopeは閉口途中の強度比 `0.0〜1.0`、既定 `0.7`
- grouped shapeでは開口量・開始・終了を各event、tail fieldをgroup末尾eventだけに許可
- real base event identityとnegative synthetic shape tokenの分離
- automatic candidateよりユーザー補正を優先し、影響spanを再評価
- hold / softnessは0から100、midpointなしのslopeは編集不可
- observationsなしを許可し、present時だけlength / event index / vowel対応をfail closed検証
- canonical整数frameとreal event intervalのsource duration上限
- writer非依存 `EffectiveShapePlan` とcore -> writer / Previewの一方向依存
- base / adjustment / effective resultの責務
- current job success時のcommitとanalysis failure / cancel時のrollback
- history coalescingの操作境界
- fingerprint / reportへの引き継ぎ
- B2からB7の所有権固定

### 10.3 Out of Scope

- production code、GUI、test codeの変更
- 編集UI実装
- provisional modelの先行追加

### 10.4 主な成果物

- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- 本Block Breakdownの必要補正
- B2以降への契約handoff

### 10.5 受け入れ条件

- multi-source groupを含むcanonical event identityが一意である。
- 全補正fieldの意味、単位、default、範囲、reject / clampが定義される。
- resolver適用順序がPreviewとwriterで共有可能である。
- lifecycle matrixとhistory transaction境界が定義される。
- P1 / P2 / P3が分類され、B2着手可否が明示される。
- 2026-07-21の実施後、残存P1 / P2 / P3なし。B2 Implementation Plan策定へ進行可能である。
- 文書補正後の限定回帰は指定95件と補完72件、合計167件がすべてpass表示、各process exit code 0である。`git diff --check` もprocess exit code 0である。

## 11. MS21-B2: Adjustment Core / Shared Shape Resolver

**Status: 実装完了 / 自動検証完了 / ユーザーGUI回帰確認通過 / B3計画策定可 (2026-07-22)**

### 11.1 目的

UIやwxPythonに依存しないadjustment model、shape provenance、Preview / writer共通のgroup-aware effective resolverを実装する。

### 11.2 In Scope

- immutable event adjustment
- canonical adjustment layer snapshot
- field validation
- base event lookup
- optional observationsとpresent時対応検証
- source duration frame validation
- effective event / plan解決
- automatic candidate shape準備とreal base event provenance
- synthetic shape tokenとcanonical base event indexの分離
- user adjustment優先と影響candidate span再評価
- nearby groupingとgroup末尾tail解決
- deterministic ordering
- empty adjustmentの同値性
- invalid / stale keyのfail-closed処理
- B5 fingerprint用canonical payload入口
- MS21 adjustment / `ShapeParameters` のhold / softness 0から100 rejectと、legacy writer / Previewの100超受理互換の分離
- real event intervalのsource duration上限と、最終tail超過・次shape clampの現行semantics維持
- writer初期化後adapterによる循環import回避
- shared shape定数の所有権とcompatibility mirror drift guard
- `src.core.*` 新規APIとtop-level legacy writer helperのnamespace境界、mixed import互換
- observation candidate参照indexのlookup前validation

### 11.3 Out of Scope

- Preview mouse操作
- RightPane control
- Undo / Redo UI
- VMD保存導線変更

### 11.4 主な成果物候補

- 新規候補 `src/core/event_adjustment.py`
- 新規候補 `src/core/effective_shape_plan.py`
- shared boundary確立に必要な `src/core/preview_transform.py`
- shared boundary確立に必要な `src/vmd_writer/writer.py`
- 新規候補 `src/vmd_writer/effective_shape_adapter.py`
- 新規候補 `tests/test_ms21_b2_event_adjustment.py`
- 新規候補 `tests/test_ms21_b2_effective_shape_plan.py`
- 新規候補 `tests/test_ms21_b2_shape_adapters.py`

### 11.5 受け入れ条件

- base planが変更されない。
- adjustmentなしのeffective resultがbaseと同じ意味になる。
- 同一inputから同一resultが得られる。
- 不正値、非有限値、範囲外keyを拒否する。
- synthetic tokenがcanonical selection / adjustment keyへ漏れない。
- automatic candidateが明示補正を上書きせず、skipされたbase eventも補正可能である。
- Preview / writer adapterが同じprovenance、grouping、tail resultを受け取る。
- writer module-levelと `src/vmd_writer/__init__.py` 初期化時にcoreをimportせず、fresh-process import順序とlegacy callで循環しない。
- top-level writer helperと `src.vmd_writer` DTOのmixed importが別class identityでも成立する。
- observation candidate参照indexの型、範囲、span / bracketing順序をlookup前に検証する。
- MS21の0から100範囲とlegacyの100超受理が混同されない。
- real event intervalだけをsource duration内に制限し、最終tail超過と次shape clampが維持される。
- shared固定定数のwriter互換名・値とcore mirrorが一致する。
- wx importなしで単体testできる。

## 12. MS21-B3: Preview Hit-Test / Event Selection

### 12.1 目的

Preview上のclickからcanonical eventを選択し、既存pan / zoom / playbackを壊さず選択状態を同期する。

### 12.2 In Scope

- viewport座標からtime / laneへの変換
- visible shape hit-test
- click / drag threshold
- overlap、boundary、empty lane
- multi-source group選択
- B2 provenanceからのevent別hit region
- adjustmentなしのB2 full resolver / provenance adapterを現行GUI Previewへ接続
- base identityとpanel-local render revisionを分離したstale gesture拒否
- event固有のframe range、base peak frame、peak valueを保持するselection metadata
- invalid / stale / synthetic tokenを拒否するcanonical selection commit
- selection highlight
- UiState / MainFrame / RightPane同期
- data更新、placeholder、reset時clear

### 12.3 Out of Scope

- 補正control
- writer出力変更
- history

### 12.4 主な成果物候補

- `docs/Implementation_Plan/MS21-B3_Implementation_Plan.md`
- 新規候補 `src/core/preview_hit_test.py`
- `src/core/preview_transform.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`
- 新規候補 `tests/test_ms21_b3_preview_hit_test.py`
- `tests/test_wx_ms16_b6_event_selection_foundation.py`

### 12.5 受け入れ条件

- clickで意図したeventを選択できる。
- drag panは選択確定を発生させない。
- invalid / empty / Busy状態でselectionが壊れない。
- grouped shapeの選択がB1契約どおりである。
- legacy render-only selection setterの範囲外許容を維持しつつcanonical digestをclearし、canonical stateへ不正indexをcommitしない。
- same base identityでもrender revisionが変わったstale requestをcommitしない。
- grouped shapeのsummaryが先頭eventまたはgroup最大peakへ置換されない。
- theme、viewport、playback cursorに回帰がない。

### 12.6 実装・検証結果

- B2 full resolverをGUI Previewへ接続し、UI非依存hit-test、strict selection commit、grouped event summary、4 DIP click / drag分離、stale base identity / render revision拒否、selection lifecycleを実装した。
- 手動確認中にselection outline描画で未定義 `palette` を参照する例外を検出し、current theme palette取得とrenderer回帰testを追加して修正した。
- B3新規22件、Preview / selection / viewport回帰50件、全体533件と7 subtestsはすべてpass表示、各process exit code 0だった。`compileall src tests` と `git diff --check` もprocess exit code 0だった。
- 2026-07-23に修正後のユーザーGUI確認は通過・問題なしと報告された。B3は完了し、次はB4 Implementation Plan策定である。

## 13. MS21-B4: RightPane Event Editor / Live Preview

**Status: 実装完了 / 自動検証完了 / ユーザーGUI確認通過 / B5計画策定可 (2026-07-24)**

### 13.1 目的

選択イベントのbase値とeffective値を表示し、補正を入力してPreviewへ即時反映する。

### 13.2 In Scope

- 選択イベントタブのstructured表示
- 編集controlと単位表示
- base / adjustment / effective値の区別
- value validationとユーザー通知
- adjustment apply / reset selected
- adjustment snapshot付きPreview resolver接続
- midpoint有無に応じたslope controlのdisabled / reject表示
- actual midpoint消失時のlatent slope override canonical removal、専用result field、non-modal notice
- selection変更時のcontrol同期
- Busy時lock
- B5接続までのnon-empty adjustment一時diagnostic ERRORと、Info / Warning / report / bottom Status / 保存操作が共有する単一snapshot
- analysis開始時のstate保持 / editor lock、current job cancel時のadjustment / selection / adjusted Preview / cancel Status保持。一時ERRORがある場合のcancel INFO抑止
- `wx.TE_PROCESS_ENTER` を含むwx commit event ownershipと重複typed request抑止
- 次の口形までの間隔によるhold / softness反映制限とslope非作用を説明する一般ユーザー向け効果notice
- cleanup / B5対応待ちの操作noticeと効果noticeの独立表示

### 13.3 Out of Scope

- adjusted VMD writer / adjustment値・effective output fingerprintへの反映
- Undo / Redo
- preset / profile

### 13.4 主な成果物候補

- `src/gui_wx/right_pane.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/core/output_diagnostics.py`
- `src/core/preview_transform.py`
- 新規候補 `tests/test_ms21_b4_selected_event_editor.py`

### 13.5 受け入れ条件

- 未選択時に編集できない。
- selected eventとcontrol値が一意に対応する。
- 不正入力でbase / adjustmentを壊さない。
- 編集確定後のPreviewがeffective resultを表示する。
- PreviewはB2 shared resolver resultを使用し、独自のcandidate / grouping順序を持たない。
- adjustment resetでbase表示へ戻る。
- non-empty adjustment中はInfo / Warning / report / bottom Status / button / menu / controllerが同じdiagnostics snapshotから保存不可を導出し、Statusに「VMD出力可能」を残さない。
- selected reset後はsnapshot全体がemptyの場合だけ既存saveabilityへ戻る。
- analysis cancel後は開始前のadjustment、selection、adjusted Preview、cancel Statusを保持し、一時ERRORがある場合はcancel INFOを抑止する。
- actual midpoint消失時のslope cleanupをtail cleanupと別result fieldへ記録し、ユーザーへ通知する。
- Enter commit対象controlが `wx.TE_PROCESS_ENTER` を持つ。
- 1回のuser commitから同一fieldのtyped requestを重複送信しない。
- 次の口形による反映制限とslope非作用が一般ユーザー向けnoticeで説明される。
- ユーザーGUI確認は通過し、問題なしと報告された。

## 14. MS21-B5: VMD Save / Diagnostics Integration

**Status: 本体・Additional Crossfade Fixとも実装・自動検証・ユーザーGUI確認完了 (2026-07-26)**

### 14.1 目的

Previewで確認したeffective resultをVMD writerとMS20 diagnostics identityへ接続する。

### 14.2 In Scope

- VMD保存時のeffective writer input
- B2 shared resolver resultのwriter adapter接続
- TEXTあり / voice_only保存分岐
- save-state fingerprint
- WARNING確認済みfingerprint無効化
- ERROR / WARNING policy維持
- diagnostic snapshot / reportのadjustment表現
- effective writer inputの `not_applicable / ready / invalid` 状態
- B4の一時 `adjustment_vmd_integration_pending` diagnosticをadjusted writer / fingerprint統合へ置換
- VMD保存失敗・cancel時のstate保持

### 14.3 Out of Scope

- 新VMD形式
- VMD読み戻し
- report自動同梱
- MMD用WAV内容変更

### 14.4 主な成果物候補

- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/core/pipeline.py`
- `src/vmd_writer/writer.py`
- 新規候補 `tests/test_ms21_b5_adjusted_vmd_save.py`
- MS20 diagnostics / report回帰

### 14.5 受け入れ条件

- Previewと保存VMDが同じeffective補正を使用する。
- B5でresolver semanticsを再定義せず、B2 resultを保存へ接続する。
- outputが変わる編集でfingerprintが変わる。
- 古いWARNING確認済み状態を再利用しない。
- ERROR保存禁止を迂回しない。
- 未解析状態をeffective writer input ERRORにせず、resolver / adapter失敗だけをfail closedにする。
- 保存失敗・cancelで編集と履歴を失わない。

### 14.6 Explicit Event Crossfade追加補正

- automatic解析とglobal tailの保守的clampは維持する。
- group末尾eventのpositive end offset、event hold、event softnessだけをmanual intentとする。
- zero-only groupを保持したまま最初の非0 successorをtarget候補とし、同母音なら探索を停止する。
- current terminal下降とnext openingだけを重ね、third active group開始前にcurrent morphを0へ戻す。
- overlap内のtarget明示control pointが0.95以上の場合だけRightPaneへnoticeを表示し、値をclipしない。
- noticeはdiagnostics、Warning tab、modal確認、保存禁止へ昇格させない。
- 実装と限定自動検証は完了した。全体testはpass表示したがprocess exit code 1だった。
  2026-07-26にユーザーGUI確認は通過・問題なしと報告され、追加補正は完了した。

## 15. MS21-B6: In-Memory Undo / Redo

**Status: Implemented / Automated Verification Passed / User GUI Verification Passed (2026-07-26)**

### 15.1 目的

adjustment layer snapshotを用いたセッション内Undo / Redoを実装する。

### 15.2 In Scope

- undo / redo stack
- 最大50操作
- redo破棄
- continuous edit coalescing
- reset selected / reset all
- menu / shortcut / action state
- Preview、RightPane、fingerprint再同期

### 15.3 Out of Scope

- disk保存
- branch型履歴
- selection / pan / playback履歴
- 50件を超える設定可能化

### 15.4 主な成果物

- `docs/Implementation_Plan/MS21-B6_Implementation_Plan.md`
- `src/core/event_adjustment_history.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_wx_ms21_b6_undo_redo.py`

### 15.5 受け入れ条件

- Undo / Redoでadjustment layer全体が正確に復元される。
- 51操作目で最古履歴だけを破棄する。
- 新規編集後にredoできない。
- 連続数値変更が1操作になる。
- reset selected / allをUndoできる。
- アプリ再起動後に履歴を復元しない。

### 15.6 計画作成結果

- canonical adjustment snapshot全体のbefore / afterを1 transactionとして保持し、
  history currentを唯一のcurrent snapshot所有者にする。
- canonical no-opでは履歴を増やさずredoを保持し、requested snapshotが変わる
  output-equivalent editは履歴へ記録する。
- 同一event・field・明示gesture token内だけをcoalesceし、timer依存の境界判定は使わない。
- mouse / key down-upで取得したtokenだけをcoalesceし、wheel / tokenなしspinは
  discrete fallbackとする。stale tokenの終了通知は現在のpendingを変更しない。
- Undo / Redo後は既存shared resolverと `sync_ui_state()` を使い、Preview、RightPane、
  diagnostics、fingerprint、保存可否を再同期する。
- Undo / Redo時は汎用operation noticeを表示し、restored snapshotからeffect /
  crossfade noticeだけを再導出する。cleanup operation noticeは再現しない。
- 計画作成baselineはB2 / B4 / B5関連56件、wx state / reset関連20件、
  effective identity / save policy関連23件がすべてpass表示・各process exit code 0だった。
- B6 lifecycleは現行clear / lockの接続に限定し、analysis failure / cancel rollback完成と
  正本仕様closeoutはB7へ残す。

### 15.7 実装状態整合レビュー

- 初回レビューでP1なし、P2 2件、P3 1件を検出した。
- cleanup operation noticeとsnapshot由来noticeの責務を分離した。
- mouse / key gesture、wheel / tokenなしfallback、stale token boundaryを固定した。
- identity引数名を既存UiState契約へ統一した。
- 修正後の再照合では残存P1 / P2 / P3なしとし、その後15.8のB6実装前チェックへ進んだ。

### 15.8 実装前チェック

- 初回実装前チェックでP1なし、P2 2件、P3 1件を検出した。
- selected event editorのclean / dirtyと、他editable text controlを区別する
  Ctrl+Z / Ctrl+Y routingを固定した。
- same gesture refresh時のactive token保持と、selection / Busy / reset / base変更 /
  history clear時のRightPane-local state破棄を固定した。
- selection / Busy / resetはpendingを確定し、base変更 / invalidation / history clearは
  pendingをtransaction化せず破棄する契約へ分離した。
- 補正後の再照合では残存P1 / P2 / P3なし。関連119件はすべてpass表示・
  各process exit code 0だった。B6実装へ着手可能である。

### 15.9 実装・検証結果

- immutable history state、最大50件、no-op時redo保持、新規編集時redo破棄、
  output-equivalent requested edit、gesture coalescingを実装した。
- Edit menu、Ctrl+Z / Ctrl+Y、dirty入力guard、他editable text controlのnative
  Undo / Redo維持、reset selected / allを接続した。
- Undo / Redo後は `sync_ui_state()` からPreview、RightPane、diagnostics、
  fingerprint、保存可否を再同期する。
- B6 core 12件、B6 wx 9件、関連回帰99件はすべてpass表示・各process exit code 0だった。
- 最終全体602件と7 subtestsはpass表示・process exit code 0、
  `compileall src tests` と `git diff --check` もprocess exit code 0だった。
- 2026-07-26にユーザー手動GUI確認は全項目通過・問題なしと報告された。
- B6は実装、自動検証、ユーザーGUI確認まで完了した。analysis failure / cancel rollback完成、
  全lifecycle横断監査、README / 配布用readme / 正本仕様同期はB7へ残る。

## 16. MS21-B7: State Integration / Regression / Docs / Adjustment Sync Efficiency

**Status: Complete / Automated Verification Passed /
User Manual GUI Verification Passed (2026-07-27)**

### 16.1 目的

編集・選択・履歴を既存workspace lifecycleへ統合し、TEXTあり / voice_onlyとMS20 diagnosticsの回帰を固定する。

### 16.2 In Scope

- input commit / cancel
- analysis開始・成功・失敗・cancel
- analysis開始前のselected event editor dirty入力拒否
- analysis開始時parameter snapshotとterminal時の別一致検証
- failure rollback後のprior diagnostic failure保持
- analysis / audio workerのlate / duplicate terminal callbackとaudio job kind不一致
- parameter変更
- workspace reset
- Busy action
- VMD / report保存失敗
- playback / pan / zoom
- TEXTあり / voice_only
- README、配布用readme、Pipeline / GUI / Error仕様。analysis failure rollbackはimplemented結果へ同期する
- Undo / Redoを含むadjustment-only同期の重複resolver・不要再描画削減
- aggregate wx test / full suiteのprocess exit code 0復旧gate
- B7 helperの一方向import境界とfresh-process import smoke

### 16.3 Out of Scope

- B1〜B6で未定義の新機能追加
- package / release
- MS22先行実装

### 16.4 主な成果物候補

- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- lifecycle関連test
- `README.md`
- `readme_mmdautolip.txt`
- Pipeline / GUI / Error仕様

### 16.5 受け入れ条件

- 新base planへ旧adjustmentを持ち越さない。
- dialog cancelでは現行workspaceを保持する。
- analysis / audio workerのlate / duplicate terminal callbackとaudio job kind不一致がselection、adjustment、historyを上書きしない。
- Busy中に編集・Undo / Redoできない。
- save failureだけで編集結果を破棄しない。
- TEXTあり / voice_onlyの既存導線を維持する。
- 文書がimplemented / plannedを混同しない。
- 1同期内のeffective resolver実行が最大1回である。
- adjustment-only同期がplayback、waveform、parameter controlを不要に更新しない。

### 16.6 計画作成結果

- analysis開始時にvalidなold base、adjustment history、selectionだけをcurrent job用の
  rollback snapshotへcaptureする。
- current successはold stateを破棄する。failure / cancelは、破棄前にrollback snapshotの
  旧timing planとcurrent audio durationから比較identityを求め、3 parameterはcapture済み
  snapshotと別に完全一致を検証し、両方が一致する場合だけrestoreする。
- failure restore後はdiagnostic ERRORを保持して保存禁止とする。cancel restoreではprior
  failureがある場合は既存ERRORを復元してcancel INFOを抑止し、ない場合だけcancel INFO付き
  fingerprintを再構築する。旧WARNING確認済みfingerprintは復元しない。
- analysis workerはcurrent job ID、audio workerはcurrent job ID・expected kind・
  `RUNNING`状態をterminal callback受理条件とし、late / duplicate / kind不一致を
  完全不変にする。
- history未初期化時はresolver結果の`effective_plan`とcanonical snapshotを再利用し、
  identity計算を重複させない。
- rollback表示中の解析失敗は`StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK`と固定文言
  `解析に失敗しました（前回結果を表示中・保存不可）`で通知する。
- 現行Undo / Redoは選択eventありでeffective resolverを3回実行する経路があるため、
  1同期専用contextからdiagnostics、Preview、selected editor、action stateへ同じplanを渡す。
- edit / reset selectedでは `AdjustmentUpdateResult.effective_plan` をidentity /
  canonical snapshot一致時だけhintとして再利用する。
- adjustment-only同期ではplayback context、PlaceholderContainer全体、
  ParameterPanelの不要な再同期・再描画を省く。persistent cacheやtimerは使わない。
- rollback identityはold timing planとcurrent audio durationから構築し、morph upper limit、
  hold、softnessはidentityへ含まれると仮定せず、capture済みsnapshotと別に完全一致を検証する。
- B7 helperは`MainFrame`からのみ参照し、core / writerからGUIへの逆import、`UiState`との
  相互import、package `__init__`からのaggregate exportを作らない。
- 計画作成baseline 47件と62件・7 subtestsはpass表示、各process exit code 0だった。
- production code、test code、dependency、build設定は未変更である。

### 16.7 実装状態整合レビュー

- 2026-07-26の現行実装照合では、P1は0件、P2は3件、P3は1件だった。
- P2は、history未初期化時のidentity二重計算、audio workerのduplicate terminal callback /
  kind不一致受理、failure rollback判定前の`invalidate_analysis()`による比較元消失だった。
- P3は、rollback表示中の解析失敗status契約が
  「専用StatusKeyまたは同等」と曖昧だった。
- B7 planを、resolver単一実行、audio terminal guard、破棄前rollback identity判定、
  固定StatusKey / 文言へ補正した。
- 補正後のplanと現行実装の間に、計画表現として未解消のP2 / P3はない。
- production codeとtest codeは未変更であり、次作業はB7 Step 0のaggregate wx test
  exit gateである。wx aggregateとfull suiteがprocess exit code 0になるまで
  production実装へ進まない。

### 16.8 2026-07-27実装前チェック補正

- P1なし、P2 4件、P3 1件を検出し、`B7-PRE-001`から`B7-PRE-005`の固定IDで
  B7 Implementation Planへ記録した。
- P2は、failure rollback後の既存ERRORをretry / cancelで失うこと、dirty editor入力を
  analysis開始同期が上書きすること、base identityが3 parameterを含まないこと、
  aggregate wx testがpass表示後にprocess exit code 1となることだった。
- P3は実装開始基準commitの古い記載であり、`3ccf630`へ更新した。
- failure payload、dirty guard、parameter snapshot、循環参照を作らないhelper所有権は
  plan契約として解消した。aggregate wx testの終了コードは受け入れ条件を弱めず、
  production変更前に原因分離・最小補修する実装前gateとして残す。
- full suite 602件と7 subtestsは2回ともpass表示・process exit code 1、wx抽出91件は
  pass表示・511件deselected・process exit code 1だった。直接原因は未確定であり、
  Python / wx versionだけを原因と断定しない。

### 16.9 2026-07-27実装・自動検証結果

- job-local rollback DTO、prior failure、parameter snapshot、active terminal guardを実装した。
- failureでは同一base / parameterの旧plan、adjustment history、selectionを復元しつつ、
  current ERRORと保存禁止を維持する。prior failureありのretry / cancelでは既存ERRORを
  復元し、cancel INFOを抑止する。
- selected editor dirty入力はanalysis開始のstate変更前に拒否し、parameter mismatchは
  success commit / failure rollback / cancel rollbackを行わず再解析待ちへ移行する。
- audio worker terminalはcurrent job ID、expected kind、`RUNNING`状態の三条件でguardする。
- 1同期限定context、validated edit hint、adjustment-only同期、同一Infoのlayout省略を実装した。
- startup splash testの実SplashScreenがmock済み`CallLater`により破棄されないことを
  wx終了時access violationの原因として特定し、test doubleと明示teardownへ限定補修した。
- B7専用15件、B3からB6回帰61件、lifecycle回帰47件と7 subtests、
  wx aggregate 97件、full suite 617件と7 subtestsは各pass表示・process exit code 0だった。
- production code、test、README、配布用readme、Pipeline / GUI / Error仕様を更新した。
  dependency、package、build、licenseは変更していない。
- この時点では本体のユーザー手動GUI確認前であり、後続の確認で追加tab補正要望が
  提示された。

### 16.10 Selected Event Tab Auto-Switch追加補正

- ユーザーはB7手動GUI確認を実施し、Previewタイムラインで単母音eventを選択した場合に
  RightPaneの「選択イベント」タブへ自動切替する補正を要望した。
- 追加補正計画を作成して現行実装へ照合し、残存P1 / P2 / P3なしと判定した。
- `RightPane`は`FindPage(panel_selected_event)`でpageを解決し、Preview user clickの
  canonical commit成功後だけ`ChangeSelection()`する。same-event再clickも対象とする。
- stale / Busy request、通常sync、Undo / Redo、analysis rollback、selection clearでは
  current tabを維持する。
- RightPane 3件、Preview selection 6件、Undo / Redo・B7 lifecycle 12件、
  wx aggregate 90件、full suite 618件と7 subtestsはpass表示・各process exit code 0だった。
- 自動test中にanalysis failure callbackが実`wx.MessageBox`を開く問題は、productionの
  通知契約を維持したまま該当test内でMessageBoxをmockし、通知呼び出しを検証する形へ
  限定補修した。補修後のfull suite 618件と7 subtestsはpass表示・process exit code 0だった。
- 2026-07-27にユーザーから、追加補正を含むB7範囲の手動GUI確認は通過し、
  問題なしと報告された。MS21-B7は完了し、次工程はMS21-B8 Closeout計画である。

## 17. MS21-B8: MS21 Closeout

**Status: Closeout A / Automated Verification Passed / User Evidence Reused / MS22 Handoff (2026-07-31)**

### 17.1 目的

MS21の要求、実装、テスト、ユーザー確認、文書を総合監査し、MS22へ進めるか判定する。

### 17.2 In Scope

- B1からB7の受け入れ条件監査
- MS21固有test、関連回帰、全体test
- selection、editing、Preview、VMD、Undo / Redoのユーザー確認証拠
- TEXTあり / voice_only回帰
- dependency / package / license差分監査
- P1 / P2 / P3分類
- A / B / C Closeout判定
- Closeout可能な場合の正本文書同期

### 17.3 Out of Scope

- MS22実装
- package / release / tag
- main merge / push / branch削除

### 17.4 主な成果物

- `docs/Implementation_Plan/MS21-B8_Implementation_Plan.md`
- 同計画§15のB1〜B7 Closeout証拠台帳
- MS21 Closeout判定
- MS22への引き継ぎ

### 17.5 受け入れ条件

- MS21の主要要求に未評価の穴がない。
- P1 / P2が解消済み、またはユーザー判断で明示処理されている。
- test表示結果とprocess exit codeが分離記録されている。
- ユーザー確認範囲と結果が記録されている。
- MS22開始可否を根拠付きで判定できる。

### 17.6 Closeout実績

- B7専用15件、B2〜B6回帰123件、MS17 / MS19 / MS20・既存回帰154件＋7 subtests、
  full suite 618件＋7 subtestsを実行し、すべてpass表示・process exit code 0だった。
- `compileall src tests` と `git diff --check` はprocess exit code 0だった。
- P1 / P2 / P3はすべてなし。ユーザー手動GUI確認はB1〜B7の報告範囲を再利用し、
  実MMDでのVMD / WAV読み込み・リップ同期はMS26へ引き継ぐ。
- B8はproduction code、test code、依存、build / package / licenseを変更せず、Closeout Aとして
  MS22開始条件を引き継ぐ。merge、push、tag、release、branch削除は未実施。

## 18. 対象ファイル整理

### 18.1 主変更候補

- 新規候補 `src/core/event_adjustment.py`
- 新規候補 `src/core/effective_shape_plan.py`
- 新規候補 `src/core/event_adjustment_history.py`
- `src/core/preview_transform.py`
- 新規候補 `src/vmd_writer/effective_shape_adapter.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`

### 18.2 関連確認

- `src/core/pipeline.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/playback_controller.py`
- `src/vmd_writer/writer.py`
- `src/core/settings_store.py`

### 18.3 テスト候補

- 新規候補 `tests/test_ms21_b2_event_adjustment.py`
- 新規候補 `tests/test_ms21_b2_effective_shape_plan.py`
- 新規候補 `tests/test_ms21_b3_preview_hit_test.py`
- 新規候補 `tests/test_ms21_b4_selected_event_editor.py`
- 新規候補 `tests/test_ms21_b5_adjusted_vmd_save.py`
- 新規候補 `tests/test_ms21_b6_adjustment_history.py`
- `tests/test_wx_ms16_b6_event_selection_foundation.py`
- `tests/test_preview_transform.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_wx_ms14_b4_analysis.py`
- `tests/test_wx_ms15_b3_playback.py`

### 18.4 文書候補

- `README.md`
- `readme_mmdautolip.txt`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- 各 `docs/Implementation_Plan/MS21-Bx_Implementation_Plan.md`

## 19. テスト方針

### 19.1 実行順

1. adjustment model / resolverのUI非依存単体test
2. hit-test / selection / historyの限定test
3. Preview / writer / diagnostics / save回帰
4. state / input / analysis / reset / late callback回帰
5. TEXTあり / voice_only回帰
6. 全体test
7. `compileall` と `git diff --check`

各コマンドは一つずつ実行し、pass表示、failure / error、fatal、process exit codeを分離して報告する。

### 19.2 手動GUI確認

Blockごとに自動化できない操作だけを提示する。少なくとも次を確認対象とする。

- click選択とdrag panの分離
- overlap / grouped shapeの選択
- RightPaneのbase / effective値
- 全補正fieldの入力・reset
- Preview即時反映
- VMD保存後のMMD側確認が必要な項目
- Undo / Redo、50操作境界、redo破棄
- Busy、再解析、新規作業
- Light / Dark theme

実施していない手動確認を通過と報告しない。実MMDでの全機能受け入れはMS26で扱う。

## 20. MS21全体の受け入れ条件

- base timing planを直接変更しない。
- canonical adjustment layerとevent identityが定義されている。
- click選択とpanが競合しない。
- grouped / multi-point shapeでも編集対象が一意である。
- synthetic shape tokenとreal base event identityが混同されない。
- RightPaneから選択イベントを補正できる。
- PreviewとVMDが同じresolver結果を使用する。
- adjustment変更がsave-state fingerprintへ反映される。
- ERROR / WARNING保存policyを維持する。
- selected reset、reset all、Undo / Redoが成立する。
- 履歴は最大50操作、セッション内限定である。
- input、reanalysis、reset、late callbackの状態契約が成立する。
- TEXTあり / voice_onlyの既存導線に回帰がない。
- dependency、package、license、固定モーフ、network方針に未承認変更がない。
- P1 / P2 / P3を分類し、MS21 CloseoutをA / B / Cで判定できる。

## 21. リスクと対策

| リスク | 対策 |
| --- | --- |
| base planを編集して再解析結果と混同する | immutable baseとadjustment layerを分離する |
| PreviewとVMDで補正結果が異なる | 共通resolverを唯一のeffective result入口にする |
| grouped shapeの先頭indexだけを編集して別eventを誤認する | B1でsource indicesとhit-test契約を固定する |
| synthetic source tokenを選択・編集identityにする | B2 provenanceでinternal tokenとreal base event indicesを分離する |
| clickとpanが同時に成立する | drag thresholdとgesture終端を明示する |
| same base identityの別描画datasetへstale clickをcommitする | panel-local render revisionをbase identityと分離し、mouse-downとcommit時に再照合する |
| grouped shapeのsummaryが先頭eventまたは最大peakを表示する | event別hit regionへbase peak frameとpeak valueを保持する |
| 補正で不正frame順序を作る | validationとfail-closed resolverを使用する |
| automatic candidateが補正を上書きする | 補正後に影響candidate spanを再評価し、user adjustmentを優先する |
| B4 PreviewとB5 writerでgrouping semanticsが分岐する | B2 shared shape resolverを両adapterの唯一の入口にする |
| UI値からwriter入力を復元する | adjustment snapshotを正本にする |
| 編集後もWARNING確認済み状態を再利用する | adjustmentをfingerprintへ含める |
| slider / spin連続変更で履歴が急増する | begin / update / commit境界でcoalesceする |
| 旧plan用indexを新planへ適用する | base identity変更時にadjustment / historyをclearする |
| late callbackが編集を上書きする | current job guard後だけworkspaceを更新する |
| scopeが汎用timeline editorへ拡大する | fixed fields、単一event、固定母音に限定する |

## 22. AI agent実装時の共通指示

- 最初に `docs/MS17_and_Beyond_Index.md`、Git状態、本書、MS20 Index / Roadmapを確認する。
- 各Block開始前に専用Implementation Planを作成し、現行code / testと再照合する。
- shell commandは一つずつ実行し、parallel / pipeline / chained commandを使用しない。
- B1完了前にproduction modelやGUIを先行実装しない。
- base plan、Preview表示、adjustment、effective writer inputを混同しない。
- multi-source groupを単一eventと仮定しない。
- test期待値を弱めて回帰を隠さない。
- package、release、merge、push、tag、branch削除は明示依頼なしに行わない。
- wxPython主系を維持し、Qt / PySide6を復活させない。
- 固定モーフ `あ / い / う / え / お` を変更しない。
- network、cloud ASR、他ASR backend、音声外部送信、background通信、Whisper自動downloadを追加しない。

各Block完了報告は次を含める。

1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したtest
5. testの表示結果とprocess exit code
6. ユーザー確認
7. P1 / P2 / P3
8. 仕様からの逸脱
9. 未検証事項
10. 次工程
