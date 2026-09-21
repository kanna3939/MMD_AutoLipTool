# MS22 Block Breakdown

## 1. 文書情報

- 文書名: `MS22 Block Breakdown`
- 配置: `docs/Implementation_Plan/MS22_Block_Breakdown.md`
- 対象MS: MS22
- MS名: Long-Vowel Expression / Generation Presets
- 基準ブランチ: `feature/MS21-implementation`
- 計画作成基準commit: `a18de64 Record MS21 closeout`
- 作成日: 2026-07-31
- 最終更新日: 2026-08-12
- B3実装コミット: `4ee67af Implement MS22-B3 preset store and settings contract`
- 文書ステータス: B1 Contract Fixed / B2 Implemented / B3 Implemented / Code Check Passed /
  B4 Implemented / Code Check Passed / User Manual Test Passed / P2-P3 Resolved /
  B5 Implemented / Code Check Passed / User Manual Test Passed /
  B6 Implemented / Automated Verification Passed / User Manual Test Passed /
  B7 Implemented / Closeout Audit Passed / A / MS26 Actual-MMD Verification Deferred (2026-08-12)
- 上位正本:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/MS20_and_Beyond_Index.md`
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS21-B8_Implementation_Plan.md`

本書はMS22を実装可能なBlockへ分割する計画文書である。本書の作成ではproduction code、
test code、GUI、依存関係、package設定を変更しない。各Blockの開始前には、別途
`MS22-Bx_Implementation_Plan.md` を作成し、現行code・test・正本文書との整合を確認する。

## 2. 現在状態

- MS21はB8 Closeout Aで完了している。MS21のbase timing plan、adjustment layer、
  `EffectiveShapePlan`、Preview / VMD共通resolver、in-memory Undo / Redo、
  diagnostics / saveability、workspace lifecycleを基準線として維持する。
- B2で`ー`由来の`VowelToken`とtimeline metadataを追加し、
  `EffectiveShapePlan`へ長音runのprovenanceを保持する。既存のlist[str]母音列は互換維持する。
- 既存の同音母音処理は、pipeline observationにおける最大2frameの
  same-vowel micro-gap / burst候補と、resolverの近接同母音groupingである。これは
  明示的な長音区間の検出・表現ではない。
- `ShapeParameters`はclosing tailに加えて`long_vowel_mode`を持ち、Previewとwriterは同じ
  `EffectiveShapePlan`から長音shapeを消費する。preset / INIの設定保存はB3で実装済みである。
- MS22-B2 Implementation Planは作成後の実装状態整合レビューで検出したP2 / P3を文書上で解消し、
  再チェックでP1 / P2 / P3の残存なしを確認した。B2はnormalized reading token、timeline metadata、
  shared effective-shape resolver、hold / decay、Preview / writer adapterまで実装し、コードチェックを完了した。
- MS22-B3 Implementation Planを2026-08-08に作成し、その後`GenerationSettings`、built-in / user preset、
  versioned `presets.json`、INI active settings / active preset id、strict validation、atomic save、
  Custom fallbackをUI非依存coreへ実装した。B3専用test、既存SettingsStore回帰、MS21 / B2直接回帰、
  full suite、compileall、diff checkを実行し、P2 / P3の修正も反映した。
- MS22-B4 Implementation Planを2026-08-08に作成した。always-valid `GenerationState`、base-bound
  `OutputEditState`、atomic output history、resolve-before-commit、output-only generation settings、
  startup / rollback / diagnostics / fingerprint統合を実装対象として固定した。計画作成baselineは
  関連180件＋19 subtestsがpass表示・各process exit code 0だった。当時はproduction実装前であり、自己回帰
  チェックで検出したP2 5件とP3 3件をplanと本書へ反映した。
- 2026-08-09のMS22-B4実装前チェックでは新規P2 3件（Undo / Redoのdeleted preset endpoint整合、`AutoLipToolApp`から
  controllerへのstartup store注入経路、empty adjustmentに対するstale hint wildcard）とP3 2件（diagnostics DTO
  不変条件、selected event editor / pipeline-preview回帰の列挙漏れ）を検出した。production code、test code、GUIは
  変更せず、B4 planと本Blockへ限定反映した。これはB4実装前時点の記録であり、後続の実装・検証で解消した。
- 2026-08-09にMS22-B4を実装した。`GenerationState` / `OutputEditState`、atomic output history、output-only設定変更、
  startup store seam、analysis rollback、diagnostics統合、stale hint guardを追加した。active preset IDを含む
  `OutputEditState`全体を同期context cacheの整合対象とし、id-only Undo / Redo後もresolverを再実行する回帰を追加した。
  B4専用test、MS20 / MS21 / MS22回帰、full suite、compileall、diff checkを確認し、P2 / P3を解消した。
- B4手動確認で判明した母音Preview非表示は、RMS補正後の別母音を挟む同一モーフ境界競合に限定して
  pipelineを補修した。修正後は関連33件、full suite 686件＋26 subtests、compileall、diff checkがpass・
  process exit code 0だった。2026-08-09にユーザーから問題解消とMS22-B4手動テスト通過が報告された。
  preset selector UIはB5、実MMD確認はMS26へ引き継ぐ。
- 2026-08-09にMS22-B5 Implementation Planを作成した。B4の既存APIを利用してRightPaneのpreset tab、
  明示的な選択とApplyの分離、built-in / user / Customの管理、preset mutation failureとoutput stateの
  分離、active presetのupdate / delete後のCustom正規化、terminal event限定のinherit / hold / decay UI、
  decay時のlatent tail保持を固定した。B5のproduction code、test code、GUI、INI / JSON本体は未変更である。
- 同日の実装状態整合レビューでP1なし、P2 3件、P3 2件を検出し、計画へ限定反映して解消した。active preset
  mutation後はeffective resolverを使わずbase-bound history全endpointまたはbaseなしGenerationStateをCustomへ
  正規化し、load / mutation別error matrix、immutable request DTO、selector fallback、B4 history直接回帰を固定した。
  B3 / B4 state・history関連35件、B2 resolver / selected editor関連32件はpass表示・各process exit code 0だった。
- B5実装前のRightPaneの`プリセット`タブはプレースホルダーだった。B5でcoreのpreset store、長音mode、active
  preset resolution、`presets.json`、INI保存を既存GUIへ接続し、選択UI、preset適用のhistory、state / diagnostics
  統合、terminal event限定のmode overrideを実装した。
- 2026-08-10にB5専用test 10件、スプラッシュテストを除く既存全体回帰694件、`compileall src tests`、
  `git diff --check`を確認し、ユーザーからB5手動GUI確認通過が報告された。全体実行で発生した既存
  `tests/test_wx_startup_splash.py`の起動時間依存1件失敗はP3としてMS22-B6の横断回帰へ引き継ぐ。実MMD確認はMS26へ残す。
- 2026-08-11にMS22-B6を実装した。non-wx lifecycle 7件、wx lifecycle 9件、splash 3件を追加・決定論化し、
  wx終了時のcoalesced save timer停止、`AutoLipToolApp`の遅延Layout / Refresh callback guard、
  test teardown helperを限定補修した。B2専用29件、B3〜B5専用45件、
  settings / export 13件、B4 / B5 / splash組合せ18件、MS17〜MS21 lifecycle 36件、save / diagnostics 33件、
  full suite 713件、compileall、diff checkはすべてprocess exit code 0だった。2026-08-11にユーザーから
  手動GUI確認通過・問題なしの報告を受領した。これはCodex自身のGUI実行結果とは扱わない。実MMDでのVMD /
  WAV読み込み・リップ同期はMS26へ維持する。
- 現在の`SettingsStore`は`MMD_AutoLipTool.ini`を実行ファイル（開発時はrepo）と同じ
  場所に置き、temporary fileをcloseしてから`os.replace()`する。MS22のJSON保存も
  同じWindows安全性を満たす必要がある。

## 3. 背景

MS22は、同じ母音が偶然近接した既存補正を長音と誤認せず、TEXT／voice-only共通変換後の
正規化済み読み列に明示された`ー`だけを長音表現の根拠にする。これにより、普通の同音母音列、zero-run候補、
cross-vowel transitionの既存semanticsを広げずに、長音を口形維持または減衰として表現する。

また、生成設定を再利用可能にする。ただしMS22で保存するのは生成設定と選択状態だけであり、
入力ファイル、timing plan、個別event adjustment、Undo / Redo履歴をsession外へ保存しない。
モデル別profile、モーフ名切替、Whisper model選択、一括出力は後続MSの責務である。

## 4. 目的

1. `ー`由来の長音区間を、既存の母音列・observation互換性を維持して識別できるようにする。
2. 選択された`hold / decay`方針を、同じresolver結果からPreviewとVMD writerへ反映する。
3. 個別event補正、active generation settings、application defaultの優先順位を明文化し、
   output identity・diagnostics・WARNING確認と矛盾させない。
4. 組み込みpresetと上限100件のユーザープリセットを安全に保存・選択・適用・復元できるようにする。
5. preset適用を既存のsession内Undo / Redoと一貫して扱い、MS21のlifecycleと回帰を維持する。

## 5. In Scope

- 共通変換後の正規化済み読み列に明示された`ー`を起点とする長音token／timeline／
  effective-shapeのデータ契約
- 長音runに対する`hold`と`decay`のshared resolver semantics
- `decay`を長音区間の終端で`0.0`へ線形減衰させるユーザー決定
- 長音modeのevent別overrideと、既存のpeak／start／end／tail補正との優先順位
- 既存同音母音micro-gap／burst／groupingの監査と、長音と衝突する残存問題だけの限定改善
- `long_vowel_mode`、closing hold、closing softnessから成る生成設定と、組み込み／ユーザーpreset
- schema versionを持つ単一`presets.json`、初期上限100件、読み込み・保存失敗時の保護
- presetの選択・適用・復元、active presetが消失した場合の`カスタム`復帰
- preset適用およびgeneration setting変更のUndo / Redo連携
- Preview、VMD、fingerprint、Warning確認、diagnostic report、TEXTあり／voice-onlyの整合
- RightPane `プリセット`タブの本実装、必要最小限のmanual GUI確認、関連正本文書同期、Closeout

## 6. Out of Scope

- 歌唱専用アルゴリズム、音響的な長音推定、`ー`を含まない同音母音列からの長音推論
- 任意キーフレーム編集、VMD読み戻し、複数event一括編集、adjustmentのdisk保存
- モデルprofile本体、`A / I / U / E / O`モーフ、任意モーフ名mapping（MS23）
- Whisper model選択・自動download・外部ASR・音声の外部送信（MS24以降または対象外）
- VMD形式、30fps、固定モーフ`あ / い / う / え / お`、入力音声／解析用WAV／MMD用WAV契約の変更
- package、release、tag、merge、push、branch削除、依存関係追加
- 実MMDでのVMD／WAV読み込み・リップ同期確認（MS26）

## 7. MS22共通設計契約

### 7.1 長音の正本と識別

- 長音metadataの検出正本は、TEXTあり／voice-onlyとも、`text_to_hiragana()`または同等の共通変換が
  返した**正規化済み読み列**とし、`hiragana_to_vowel_sequence()`が既存`list[str]`へ縮退する直前に
  token化する。この読み列に実在するUnicode `ー`だけをexplicit markerとする。raw入力に元から
  存在した`ー`とG2Pが生成した`ー`は区別せず、どちらも正規化済み読み列で明示された長音として扱う。
  raw input文字列、ASR raw result、observationから別経路で長音を推定しない。
- `ー`のない隣接同母音、same-vowel micro-gap、burst、zero-run、groupingを長音へ自動昇格させない。
- 既存の`list[str]`母音列と固定モーフ契約は互換維持する。追加のimmutable token metadataは、少なくとも
  token index、`is_long_vowel_continuation`、continuationが属するrun先頭のsource token index、または
  同等の意味を持つfieldを備える。sourceは同一runを開始した直前の非continuation tokenとし、連続する
  複数の`ー`はそのsourceを共有する。同じvowelでも別runのsourceへ遡らない。
- 有効な長音runは、先行する通常母音と、同じ母音を複製した1個以上のcontinuation eventから成る。
  先行母音のない`ー`は現行同様に母音eventを作らず、長音runにもならない。
- token metadataはtimeline生成、RMS refine、peak反映、duration／boundary repair、Preview／writer adapterを
  通るすべての`VowelTimelinePoint`または同等DTO再構築で明示copyし、resolverがbase eventへ投影する。
  observationは補助情報のままであり、長音有無の正本・timeline eventの代替正本にしない。
- `BasePlanIdentity`のcanonical payloadへ長音metadataを含め、identity schemaを
  `ms22-base-plan-v1`へ更新する。
  frame／母音が同じでも長音metadataが異なるbase planは別identityとし、旧schemaまたはmetadata不一致の
  adjustment snapshotは既存どおりfail closedで拒否する。

### 7.2 長音shape semantics

- `hold`は、長音runの先頭peakからterminal continuation eventのend frameまでpeak valueを維持し、
  その後だけ既存のclosing tail規則を適用する。
- `decay`は、長音runの先頭peakからterminal continuation eventのend frameまで、peak valueから
  `0.0`へ線形減衰する。**長音区間の終端で必ず0.0に到達する**。decay modeへglobalまたは
  event別closing hold / softnessを追加して終端zeroを後ろへ移動させない。
- source start frameとsource peak frameが同じ場合はzero-length opening edgeとしてstart zeroを省略し、
  source peak valueを正本とする。positive peakと同じframeへrequired zeroを登録しない。
- decay terminal zeroまたはhold closing zeroと、別shapeのpositive control pointが同一morph・同一frameで
  競合する場合は、どちらかをsilent mergeせずnormalization前にfail closedとする。異なるmorphの同一frame値は
  競合ではない。even fallbackの`あーあ`でdecay terminalと次の`あ` peakが一致する配置も拒否対象とする。
- source / terminal eventの実効frameは、既存どおり30fpsの整数frameを唯一のevent正本とし、
  `0 <= start <= peak <= terminal_end <= duration`を満たす。shapeへ生成するfinal closing zeroは
  既存final tailと同じくresolved closing tailの分だけdurationを超過し得る。この超過は最終shapeの生成edgeに
  限って許容し、次shapeがある場合だけ既存保護境界へclampする。重複、0長区間、event frameのduration超過、
  次shapeとの競合はresolverで決定的に処理する。
- 長音のshape kind、real base event provenance、event ranges、terminal frameは
  `EffectiveShapePlan`に残し、Preview / writer / diagnosticsが文字列やcacheから再構成しない。

### 7.3 優先順位と個別補正

有効な長音runのmodeは、次の順序で解決する。

```text
terminal long-vowel event の明示mode override
  > active generation settings（選択presetを適用した値、またはCustom値）
  > application default（hold）
```

- event別mode overrideは長音runのterminal continuation eventだけに許可する。非長音event、
  run先頭、synthetic token、stale base identityへの指定はfail closedで拒否する。
- 長音runの振幅正本は、run先頭source eventへ適用済みの実効peak valueだけとする。`decay`の線形性を
  破るため、continuation eventのpeak補正を中間control pointへ変換しない。長音shapeの終端正本は、
  terminal continuation eventへ適用済みの実効end frameとする。
- B1でsource／intermediate continuation／terminal continuationごとのpeak／start／end／tail／modeの
  所有権表を固定する。source peak frameはbase timelineのframeで固定し、source adjustmentはpeak valueだけを
  変更する。長音shapeへ影響しない補正を黙って無視してはならず、編集入口で無効化またはfail-closed拒否し、
  理由をUIへ渡せる構造化結果を返す。補正後にframe逆転、source peak以前のterminal、source / terminal event
  frameのduration超過、次shapeとの未解決競合が生じる操作はcommitせず、MS21のlast-valid rollbackを保つ。
  生成されたfinal closing zeroのduration超過はこのevent frame検証とは別の既存final-tail規則として扱う。
- `hold`では、terminal continuation eventの明示hold／softness／slopeがactive generation settingsの
  tail値より優先する。
  `decay`では長音終端zeroを守るためtail controlを無効化し、UIは理由を表示する。ユーザーがtailを
  使用したい場合は、そのeventのmode overrideを`hold`へ明示変更する。
- event別hold／softness／modeの`None`はinherit、非`None`は明示overrideとする。明示値が現在のactive
  generation settingsと同値でもcanonicalizationで削除しない。`decay`中に無効となる明示tail値も
  latent overrideとしてsnapshotへ保持し、同じeventを`hold`へ戻したとき再び有効にする。
- preset適用は個別adjustment、selection、viewport、playbackを消去・上書きしない。mode overrideを
  含む個別adjustmentは、presetより常に優先する。

### 7.4 生成設定・preset・永続化

- `LongVowelMode`のruntime境界はclass / Enum identityに依存しないprimitive string `hold | decay`とする。
  B2がvalidation正本を実装し、B3はその契約へ依存してpreset DTOを構築する。
- MS22の`GenerationSettings`は`closing_hold_frames`、`closing_softness_frames`、
  `long_vowel_mode`を持つ。`morph_upper_limit`は解析時のpeak生成に関与する既存parameterであり、
  MS22 presetには含めない。これによりpreset適用は再解析なしで同じbase planから再解決できる。
- application defaultは`long_vowel_mode=hold`、既存のhold / softness既定値0とする。既存INIへ
  active generation settingsとactive preset識別子を追加する場合も、INI自体をpreset本体にしない。
- 組み込みpresetはcode内の読み取り専用定義とし、少なくとも既定`標準（長音維持）`と、同じ既定tailで
  modeだけを`decay`へ変える`長音減衰`を提供する。組み込みpresetを`presets.json`へ複製・編集しない。
- ユーザープリセットは単一`presets.json`の`schema_version: 1`と`user_presets`に保存する。
  各entryはstable id、表示名、上記`GenerationSettings`だけを持ち、初期上限100件とする。
- `presets.json`は`SettingsStore`のINIと同じdirectoryに置く。読み込み失敗、unsupported version、
  schema不正、保存失敗では既存fileを自動上書きしない。組み込みpresetは利用可能に保ち、
  user preset storeをそのsessionではread-only unavailableとしてcreate / update / deleteを拒否し、原因を
  ユーザーへ通知する。外部修復後の次回loadまで旧fileを保持する。
- startupではINIのactive generation settingsを出力正本とする。active preset idがmissing、または
  definitionのsettingsとINI settingsが不一致なら、INI settingsを保持して`Custom`へ正規化する。
  invalid user JSONでもbuilt-in idは独立に解決し、settings一致時だけactive idを保持する。
- 保存はUTF-8、temporary fileの明示close、同一directory、`os.replace()`、失敗時temporary cleanupを
  必須とする。新規依存は追加しない。

### 7.5 history・diagnostics・lifecycle

- baseなしでもapp-level `GenerationState`としてsettingsとactive preset idを保持する。base確定時だけ、
  base identity、adjustment snapshot、GenerationStateを一体化した`OutputEditState`をhistory正本にする。
- preset適用とgeneration settingの直接変更は、MS21の最大50件・redo破棄・pending gesture境界を
  維持したsession内output edit historyへ1 transactionとして記録する。transactionのbefore／afterは
  `GenerationSettings`、active preset idまたは`Custom`状態、明示overrideを保持したadjustment snapshotを
  一体で持つ。これらを別々に復元して一時的なPreview / writer不一致を作らない。
- direct入口はrequested settingsを先に比較し、settings同値eventではactive preset idを保持してresolver、
  history、INI保存要求を発生させない。settingsが実際に変わった場合だけ`Custom`へ移る。preset applyは
  settings同値でもvalid idが異なればid-only transactionとし、同じsettings / idの再適用だけをno-opとする。
- historyはアプリ終了、新規作業、新base plan確定、input変更で破棄する。preset JSONとINIへの
  保存はhistoryを復元しない。
- preset適用、Undo / Redo、mode overrideは同一`EffectiveShapePlan`を再構築し、Preview、
  selected editor、diagnostics、save-state fingerprint、VMD保存可否へ同じcontextを渡す。
- resolver入力`ShapeParameters` provenanceは`EffectiveShapePlan`だけが保持し、hint受理時にcandidate
  base inputとの一致を検証する。UiSyncContext側のcandidate値をhint由来provenanceの代用にしない。
- startup、preset適用、direct変更、Undo / Redo、rollback後はcanonical generation stateを既存parameter
  controlへguard付きで投影し、投影eventによる再commitを禁止する。candidate拒否時は旧canonical値へ戻す。
- preset適用、direct generation setting変更、Undo / Redoは、検証済みtransactionをin-memoryへcommitし、
  shared resolverと表示を同期した後、active generation settingsとactive preset idを既存のcoalesced
  `SettingsStore`経路でINI保存要求する。INI保存失敗はcommit済みin-memory stateやhistoryをrollbackせず、
  既存のsave-disabled／ユーザー通知契約に従う。同一sessionの後続要求／close flushは`attempted=False`で
  再保存せず、再起動時は最後に保存成功したINI値だけを復元する。
- MS21 fingerprintのinput mode、normalized TEXT / WAV path、effective writer input state、VMD model name、
  effective morph frame / tail、diagnostic identityを維持する。選択presetの表示名・id、notice、history順序
  だけをfingerprint入力にせず、既存canonical入力が変化した場合だけWARNING確認を無効化する。
- generation summaryへactive long-vowel mode、active preset id / display name、effective hold / decay run count、
  adjustment summaryへmode override件数をadditiveに追加し、Infoとreportで同じstructured fieldを使用する。
  effective run countは未確定を`None`、確定済み0件を`0`として区別する。
- input、analysis、audio worker、failure / cancel rollback、late / duplicate callbackのMS21 guardは
  generation settingsとhistoryを古いjobから上書きさせない。presetのdisk保存失敗だけで現在の
  in-memory generation setting、base、adjustment、historyを破棄しない。
- app-level generation state単独はworkspace user dataへ数えず、startupまたはbaseなし設定変更だけで
  新規作業確認を表示しない。

## 8. Block一覧

| Block | 名称 | 主責務 | 直接依存 | 状態 |
| --- | --- | --- | --- | --- |
| MS22-B1 | Long-Vowel / Generation-Preset Contract Pre-check | 契約・現状・受け入れ境界を固定 | MS21 Closeout A | Completed / Contract Fixed (2026-08-01) |
| MS22-B2 | Long-Vowel Data Contract / Shared Resolver / Same-Vowel Audit | 明示長音metadata、hold / decay、既存同音母音の限定監査 | B1 | Implemented / Code Check Passed (2026-08-06) |
| MS22-B3 | Generation Preset Store / Settings Contract | preset DTO、built-in、versioned JSON、INI境界 | B2 | Implemented / Code Check Passed (2026-08-08) |
| MS22-B4 | Generation State / History / Diagnostics Integration | settings・history・effective output・lifecycle統合 | B2、B3 | Implemented / Code Check Passed / User Manual Test Passed / P2-P3 Resolved (2026-08-09) |
| MS22-B5 | Preset UI / Event Override Flow | RightPane導線、選択・適用・管理、mode override UI | B4 | Implemented / Code Check Passed / User Manual Test Passed / B6でP3解消済み (2026-08-11) |
| MS22-B6 | Lifecycle Regression / Documentation | 横断回帰、error / docs同期、manual GUI確認 | B5 | Implemented / Automated Verification Passed / User Manual Test Passed (2026-08-11) |
| MS22-B7 | MS22 Closeout | 証拠監査、P分類、A / B / C判定 | B1〜B6 | Implemented / Closeout Audit Passed / A / MS26 Actual-MMD Verification Deferred (2026-08-12) |

## 9. Block依存関係

```text
MS21 Closeout A
  ↓
MS22-B1 Contract Pre-check
  ↓
MS22-B2 Long-Vowel Core / Primitive Mode Contract
  ↓
MS22-B3 Preset Store / GenerationSettings
  ↓
MS22-B4 State / History / Diagnostics
  ↓
MS22-B5 Preset UI / Event Override
  ↓
MS22-B6 Lifecycle / Regression / Docs
  ↓
MS22-B7 Closeout
```

B2はprimitive `LongVowelMode` validationを含むresolver契約を先に固定し、B3はその契約を入力として
`GenerationSettings`とpreset storeを実装する。同一worktreeでは既存変更を保護し、各Blockをcommit・
検証してから次へ進める。B4以降はB2・B3の確定DTOとfailure契約を前提とする。

## 10. MS22-B1: Long-Vowel / Generation-Preset Contract Pre-check

### 10.1 目的

長音metadata、shape semantics、mode precedence、preset schema、history拡張、既存同音母音の
監査対象を、現行codeとtestへ対応付けて固定する。B1は契約固定のみであり実装しない。

### 10.2 In Scope

- `ー`を持つTEXTあり／voice-onlyの入力経路、母音列、timeline、observation、resolverの確認
- 正規化済み読み列を長音検出正本とする段階、token metadata、全DTO再構築経路、
  `BasePlanIdentity` schema更新の固定
- §7.2のhold / decayと、ユーザー決定したdecay終端zeroのcontract固定
- §7.3の長音run member別補正所有権、mode override、tail control、preset、Customの優先順位と
  UI禁止／fail-closed状態の固定
- `GenerationSettings`、preset JSON schema v1、built-in preset、INIとの責務分離
- baseなしGenerationState、base確定時OutputEditState、INI / preset definition不一致時のCustom復帰
- 明示tail overrideをactive generation settingsとの同値比較で消さないcanonicalization契約と、MS21
  adjustment historyをoutput edit historyへ拡張する最小境界、Undo / Redo後のINI保存順の確認
- existing same-vowel / cross-vowel testsを監査baselineとして列挙

### 10.3 Out of Scope

- production code、test code、GUI、INI、JSONの変更
- preset値・modeを推測して既存project設定を移行する処理

### 10.4 主な成果物

- `docs/Implementation_Plan/MS22-B1_Implementation_Plan.md`
- B2〜B6の入力／出力／failure／test ownership表

### 10.5 受け入れ条件

- 長音検出段階、tokenからbase eventまでのmetadata copy、identity schema更新が明文化され、長音と
  既存same-vowel候補を混同しないデータ経路が固定される。
- `decay`の終端zero、run member別補正所有権、event override、tail無効化／latent保持が明文化される。
- preset適用とUndo / Redoで明示adjustmentを失わず、commit後のINI保存失敗でin-memory stateを
  rollbackしないatomic state契約が固定される。
- B2〜B6で変更してよい既存API、新規候補file、回帰file、docsが実在確認済みである。
- P1 / P2がなければB2へ進め、B2のprimitive mode契約確定後にB3へ進める。B1自体はGUI確認対象外である。

## 11. MS22-B2: Long-Vowel Data Contract / Shared Resolver / Same-Vowel Audit

### 11.1 目的

`ー`の由来をbase eventまで安全に保持し、shared resolverが長音runを`hold`または`decay`として
決定的に出力できるようにする。同時に既存same-vowel処理を監査し、長音metadataとの衝突だけを
限定補修する。

### 11.2 In Scope

- text / transcriptionからのimmutable vowel token metadata
- class identityに依存しないprimitive `LongVowelMode` validation正本
- additiveなtimeline / base event metadata、全`VowelTimelinePoint`再構築経路でのcopy、
  `BasePlanIdentity` payload／schema更新と既存caller互換
- explicit long-vowel runの構築、terminal event決定、invalid / zero-lengthのfail-closed処理
- `ShapeParameters`または同等のresolver inputへの`long_vowel_mode`追加
- `hold` plateau、`decay` linear-to-zero control point、source / terminal event frameのduration境界、
  final closing edgeの既存duration超過許容、次shape保護
- source start / peak同一frameでのopening zero省略と、同一morph required zero / positive競合のfail-closed検証
- source peak／terminal endの所有権、非所有member補正の拒否、terminal eventだけに許可するmode override、
  hold時だけのexisting tail適用
- `EventAdjustment`／snapshot schema更新と、明示override・decay中latent tailを保持するcanonicalization
- hold / decay双方で既存consumerが利用できるnon-`None` resolved tail metadata。decayはrequested値をlatent保持し、
  effective hold / softnessを0、slope midpointなしとする
- shared `EffectiveShapePlan` provenance、normalization、writer adapter、Preview adapterの整合
- current micro-gap / burst / grouping / cross-vowel regressionsの監査と最小修正

### 11.3 Out of Scope

- preset JSON、INI、RightPaneのpreset管理、history UI
- `ー`を含まない同音母音の長音推定、音響からの長音判定、writerだけの特別分岐

### 11.4 主な成果物候補

- `src/core/text_processing.py`
- `src/core/pipeline.py`
- `src/core/effective_shape_plan.py`
- `src/core/event_adjustment.py`
- 必要時のみ新規候補 `src/core/long_vowel_contract.py`
- `src/vmd_writer/writer.py`
- 必要時のみ `src/core/preview_transform.py`、`src/vmd_writer/effective_shape_adapter.py`
- B2で必須作成 `tests/test_ms22_b2_long_vowel_tokens.py`
- B2で必須作成 `tests/test_ms22_b2_timeline_metadata.py`
- B2で必須作成 `tests/test_ms22_b2_long_vowel_resolver.py`
- B2で必須作成 `tests/test_ms22_b2_long_vowel_adapters.py`
- B2で必須作成 `tests/test_ms22_b2_import_boundaries.py`
- `tests/test_text_processing.py`、`tests/test_pipeline_and_vmd.py`
- `tests/test_pipeline_peak_values.py`
- `tests/test_ms21_b2_effective_shape_plan.py`、`tests/test_vmd_writer_intervals.py`、
  `tests/test_vmd_writer_grouping.py`、`tests/test_preview_transform.py`
- `tests/test_vmd_writer_zero_guard.py`、`tests/test_vmd_writer_multipoint_shape.py`、
  `tests/test_ms21_b3_pipeline_preview_integration.py`、`tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b6_adjustment_history.py`、`tests/test_ms21_b4_selected_event_editor.py`、
  `tests/test_ms21_b7_ui_sync_context.py`

### 11.5 受け入れ条件

- `ー`由来のeventだけが長音runになり、通常の同音母音とexisting candidate処理は同じ入力で不変である。
- `あーあー`の各continuationは同一run直前のsourceを参照し、別runへ誤結合しない。
- metadataあり／なしのbase planはframe／母音が同じでも別identityになり、refine／repair／adapter後も
  source／continuation関係が保持される。
- default `hold`とselected `decay`が同じcore resultからPreview / writerへ渡る。
- `decay`のterminal control pointは長音区間終端で値`0.0`であり、tail extensionで後ろへ移動しない。
- source start / peak同一frameではopening zeroを省略し、required zeroと別shapeのpositive pointが
  同一morph・同一frameで競合する場合はnormalization前に拒否する。異なるmorphの同一frame配置は受理する。
- hold / decay双方のreal long shapeがnon-`None` resolved tail metadataを持ち、decayはrequested latent値と
  effective tail 0を区別する。
- source / terminal event frameはsource duration内に収まり、最終shapeのgenerated closing zeroだけは
  resolved final tailによりdurationを超過し得る。次shapeがある場合は既存保護境界へclampする。
- source peak／terminal end、非所有member補正拒否、event mode override、hold時tail、decay時tail無効化が
  決定的であり、continuation peakから減衰途中のcontrol pointを生成しない。
- invalid metadata、stale／synthetic event、非有限値、frame逆転をfail closedで拒否する。
- 既存same-vowel／cross-vowel regressionが通り、改善は長音と衝突する再現済み問題だけである。

## 12. MS22-B3: Generation Preset Store / Settings Contract

### 12.1 目的

UIに依存しないgeneration settingsとpreset storeを実装し、組み込みpreset、ユーザーpreset、
`presets.json`、INIに残す選択状態の責務を分離する。

### 12.2 In Scope

- B2のprimitive `LongVowelMode` validation契約を使用するimmutable `GenerationSettings`と
  `GenerationPreset` DTO、値検証、stable id、display name規則
- 読み取り専用`標準（長音維持）`と`長音減衰`のbuilt-in definitions
- `schema_version: 1`、`user_presets`、初期上限100件のread / validate / write contract
- SettingsStoreと同一directoryへの`presets.json`配置、UTF-8、atomic write、failure cleanup
- JSON破損、unsupported version、entry不正、IO failure時のread-only unavailable recovery contract
- INIに保存するactive generation settingsとactive preset id、およびmissing / settings不一致時のCustom復帰

### 12.3 Out of Scope

- wx control、selection dialog、event adjustment、Undo / Redo action wiring
- profile JSON、モデル別morph名、presetのnetwork同期、JSON自動migrationによるデータ破棄

### 12.4 主な成果物

- `src/core/generation_presets.py`
- `src/core/settings_store.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_settings_store.py`

### 12.5 受け入れ条件

- built-in presetはJSONがなくても使用でき、編集・削除・JSONへの重複保存はできない。
- user presetは100件目までは保存でき、101件目を破壊的変更なしで拒否する。
- 保存成功は同一directory temporary fileをcloseしてからreplaceし、失敗時は旧fileを保持する。
- 壊れた／未来versionのJSONを自動上書きせず、session内user mutationを拒否する。
- active idがmissing、またはdefinitionとINI settingsが不一致の場合は、INI settingsを出力正本として
  `Custom`表示へ復帰する。invalid user JSONでも一致するbuilt-in idは保持する。
- JSON、INI、DTOにtiming plan、input path、adjustment、historyを保存しない。

## 13. MS22-B4: Generation State / History / Diagnostics Integration

### 13.1 目的

generation settingsとindividual adjustmentを一つのsession内output stateとして扱い、preset適用・
direct parameter変更・Undo / Redo・Preview・writer・diagnosticsの不一致を防ぐ。

### 13.2 In Scope

- baseなしでも有効な`GenerationState`と、base確定時だけ存在する`OutputEditState`の所有権・不変条件
- existing adjustment historyを、generation settingsを含むatomic transactionへ最小拡張
- B2で固定したcanonical snapshotを、active generation settingsとの同値比較で明示overrideを失わず、
  decay中のlatent tailを保持したままatomic output stateへ統合
- 最大50操作、redo破棄、event edit gesture coalescing、preset applyのdiscrete transaction維持
- non-no-op preset適用・Undo / Redo後のshared resolver 1回、Preview / editor / diagnostics / saveability同期
- `EffectiveShapePlan`を唯一のshape-parameter provenanceとするstale hint拒否
- candidate adjustment `None`を`empty_adjustment_snapshot(identity)`へcanonicalizeし、non-empty hintをwildcardとして
  受理しないstale hint guard
- deleted / mismatched presetをUndo / Redoする際のhistory before / after endpointのatomic正規化、同値transactionの除去、
  反対方向navigationのinvariant維持
- canonical generation stateから既存hold / softness controlへのguard付き投影と、拒否時の値復元
- preset適用・direct変更・Undo / Redo commit後のcoalesced INI保存要求と、保存失敗時のin-memory非rollback
- `closing_hold`、`closing_softness`、long-vowel modeを、base timing planを再解析せず再解決する
  output-only parameterとして分離
- `morph_upper_limit`は既存どおりanalysis-affecting parameterとして維持し、MS22 preset適用では変更しない
- MS21 canonical fingerprint入力を維持したWARNING確認、active mode / preset / effective run countを持つ
  diagnostic report generation summaryとmode override countの更新
- input／reset／new base／analysis success／failure／cancel／late callbackでのstate・history guard
- injectable storeとI/Oなしcontroller constructorによるstartup testのrepository設定file分離
- `AutoLipToolApp`の`settings_store` / `preset_store` keyword引数から同じtemporary storeを`AppController`へ渡すstartup seamと、
  既存`AutoLipToolApp(False)`のcaller互換、default repository path不変の検証
- generation / adjustment diagnostics DTOのmode、run count、active id / display name pair、override count不変条件
- generation変更も含むEdit menu、tooltip、noticeの「出力編集」表現

### 13.3 Out of Scope

- presetタブの見た目、user presetの作成／削除dialog、model profile
- persistent history、historyのsession外復元、morph upper limitのpreset化

### 13.4 主な成果物候補

- `src/core/output_edit_state.py`
- `src/core/event_adjustment_history.py`
- `src/core/effective_shape_plan.py`
- `src/core/__init__.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/ui_sync_context.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/app.py`
- `src/gui_wx/analysis_rollback.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- 新規必須 `tests/test_ms22_b4_generation_history.py`
- 新規必須 `tests/test_wx_ms22_b4_generation_state.py`
- MS21-B4 selected event editor、MS21-B3 pipeline-preview integration、MS21-B5 / B6 / B7 diagnostics・history・lifecycle regression

### 13.5 受け入れ条件

- non-no-op preset適用は1回のUndo可能transactionで、event adjustment、generation settings、active preset
  id／`Custom`を整合して復元する。同じsettings / idの再適用はhistory / resolver / INI保存要求なしとする。
- active preset中のsettings同値direct eventはidを保持する完全no-opとし、settings変更時だけCustomへ移る。
  settings同値・id異値のpreset applyはid-only transactionとして復元できる。
- active generation settingsと同値の明示tail overrideもpreset適用前後に保持され、decayからholdへ戻すと
  再び有効になる。
- direct output-only parameter変更はbase planを破棄せず、current effective outputだけを再構築する。
- preset適用前後、Undo / Redo、save-disabled後の後続保存要求でPreview、VMD、diagnostics、fingerprintが同じ
  `EffectiveShapePlan`を使用する。
- Undo / Redo後の設定はINI保存要求へ渡り、保存失敗でもcurrent outputとhistoryはlast-valid stateを保つ。
- preset表示idやnoticeだけではfingerprintを変えず、effective frameが変わる場合は既存WARNING確認を
  再利用しない。
- startup / direct変更 / preset / Undo / Redo / rollback後のhold / softness controlがcanonical stateと一致し、
  candidate拒否時も旧値へ戻り、投影eventが再commitされない。
- startup testはtemporary storeだけを使用し、repository既定INI / `presets.json`を変更しない。
- `AutoLipToolApp`から`AppController`へ同じtemporary storeが渡され、production default pathは引数省略時だけ使用する。
- candidate adjustment `None`はempty snapshotとしてhint比較され、non-empty stale hintを受理しない。
- deleted / mismatched presetのUndo / Redoはhistory endpointをatomicに正規化し、同値transactionを追加履歴なしで除去し、
  反対方向navigationのinvariantを維持する。
- diagnostics DTOはmode、run count、active id / display name pair、override countの不変条件を保証する。
- selected event editorのcore / wx回帰とMS21-B3 pipeline-preview integration回帰を指定commandで実行する。
- generation state単独ではworkspace reset確認を発生させず、Undo / Redoの表示は「出力編集」とする。
- input変更、新規作業、新base成功、invalid rollback、late callbackでhistoryとgeneration stateが
  MS21 lifecycle契約どおりclear／retainされる。

## 14. MS22-B5: Preset UI / Event Override Flow

### 14.1 目的

RightPaneの`プリセット`タブを、現在のactive generation settingsとpreset storeを表示・操作する
wxPython UIへ置き換える。長音terminal eventのmode overrideも選択イベントUIへ最小追加する。

### 14.2 In Scope

- preset selector、current / Custom状態、built-inとuser presetの区別
- user presetの作成、更新、名前変更、削除、上限・保存エラー表示、busy時lock
- preset適用、Undo / Redo、selection restore、missing presetのCustom表示
- selected long-vowel terminal eventだけで有効になるhold / decay override、reset、decay時tail説明
- existing ParameterPanelのhold / softness変更時にCustomへ移る表示とB4 state API接続
- theme、tab order、dirty input、Busy、stale request、event selection変更、layout / scrollの維持

### 14.3 Out of Scope

- generic preset editor framework、drag reorder、import / export、cloud sharing、profile UI
- non-long eventへのmode control表示、mode overrideによるtail end zero規則の緩和

### 14.4 主な成果物候補

- `src/gui_wx/right_pane.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/selected_event_editor.py`
- `src/gui_wx/ui_state.py`
- 新規候補 `tests/test_wx_ms22_b5_preset_ui.py`
- 新規候補 `tests/test_wx_ms22_b5_long_vowel_override.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b6_undo_redo.py`、`tests/test_wx_ms21_b7_state_integration.py`

### 14.5 受け入れ条件

- UIはbuilt-in / user / Customを混同せず、invalid JSON・保存失敗・100件上限を回復可能に表示する。
- preset適用は同じeffective outputをPreviewへ即時反映し、Undo / Redoで戻せる。
- long-vowel terminal event以外ではmode overrideを操作できず、stale / Busy requestはstateを変更しない。
- decay modeのtail control無効化と、holdへ切替える回復手段が日本語で説明される。
- non-long event editor、Info / Warning、tab auto-switch、other editable text controlsの既存挙動を壊さない。

## 15. MS22-B6: Lifecycle Regression / Documentation

### 15.1 目的

MS22の長音・preset・historyをMS20 diagnostics、MS21 lifecycle、TEXTあり／voice-only、失敗状態、
documentationへ統合し、未確認境界を限定して検証する。

### 15.2 In Scope

- TEXTあり／voice-onlyの`ー`、連続`ー`、先行母音なし、同音非長音、observationなし
- input change、new workspace、analysis success / failure / cancel、rollback、late / duplicate callback
- VMD save / cancel / failure、diagnostic report、WARNING再確認、preset JSON read / save failure
- existing same-vowel / cross-vowel、Preview / writer、Undo / Redo、Busy、wx teardown回帰
- README、`readme_mmdautolip.txt`、Pipeline / GUI / Error仕様、Roadmap / Index / Block Breakdownの同期
- ユーザー手動GUI確認の範囲と、実MMDをMS26へ残す境界の記録

### 15.3 Out of Scope

- 新しい長音algorithm、preset field、UI flowの追加
- package / release検証、実MMD受け入れ、MS23先行実装

### 15.4 主な成果物候補

- `README.md`、`readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md`
- MS22 B2〜B5のtest群およびMS17 / MS19 / MS20 / MS21回帰群

### 15.5 受け入れ条件

- planned / implemented / verified / user-reported / MS26 deferredが文書間で区別される。
- TEXTありとvoice-onlyの双方で長音metadataとpreset stateが現行job guardを迂回しない。
- JSON／INI失敗、VMD保存失敗、dialog cancelで正常なin-memory output stateを失わない。
- manual GUI確認は実施者と範囲を正確に記録し、実MMD未確認を完了扱いにしない。

### 15.6 実装・自動検証結果

- B6専用non-wx 7件、wx 9件、splash 3件をpass・終了コード0で確認した。
- B4 / B5 / splash組合せ18件、MS22専用回帰、MS17〜MS21 lifecycle / save回帰、full suite 713件を
  pass・終了コード0で確認した。
- `compileall src tests`、`git diff --check`を終了コード0で確認した。
- wx終了問題はproductionのcoalesced save timer停止と遅延Layout / Refresh callback guard、test teardown helperへ限定修正し、1500ms splash、
  fixed morph、VMD / audio、dependency、package、network、Qt契約は変更していない。
- B6は自動検証済みで、ユーザー報告によるmanual GUI確認も通過した。Codex自身のGUI実行ではない。
  MS22 Closeout A / B / CはB7の責務とする。

## 16. MS22-B7: MS22 Closeout

### 16.1 目的

B1からB6の要求、code、test、ユーザー確認、docs、dependency / package境界を総合監査し、
MS22 CloseoutをA / B / Cで判定する。

### 16.2 In Scope

- 長音contract、hold / decay、precedence、preset JSON、history、Preview / VMD / reportの受け入れ監査
- B2〜B6専用test、MS17〜MS21回帰、full suite、compileall、git diff check
- user GUI evidence、P1 / P2 / P3分類、A / B / C判定、Closeout文書同期

### 16.3 Out of Scope

- 新機能、testを弱める変更、MS23実装、release / tag / merge / push
- 実MMDでの最終リップ同期判定

### 16.4 受け入れ条件

- P1 / P2がなく、主要契約・自動検証・範囲限定ユーザー確認・文書同期が揃う場合だけAとする。
- testのpass表示、failure / error、process exit codeを別記録する。
- 実MMDのVMD / WAV確認をMS26の未検証事項として維持する。

### 16.5 Implementation Plan策定状態

- `docs/Implementation_Plan/MS22-B7_Implementation_Plan.md`を2026-08-11に作成した。
- 計画作成baselineはMS22 B2〜B6専用＋splash 93件、full suite 713件、compileall、diff checkが
  pass表示・process exit code 0だった。
- 計画作成時点ではtracked `presets.json`のruntime user data境界をP2候補、B5のsplash P3 current status未同期を
  P3候補として、A判定前のpre-closeout gateへ固定した。
- 計画レビューでP2 / P3として確定し、local `presets.json`を保護した追跡解除とroot限定ignore追加、
  B5 / Block / routing文書のsplash current status同期を分離repairとして実施し、両findingを解消した。
- B7計画策定ではproduction code、test code、GUI、dependency、packageを変更しない。
- 上記は計画作成時点の状態であり、Closeout監査前の記録である。

### 16.6 MS22-B7 Closeout実施結果

- 2026-08-12にB7 Closeout監査を実施した。MS22 direct regression 93件、基盤回帰185件、MS21回帰138件、
  MS17 / MS19 / MS20回帰158件、B4 / B5 / splash組合せ18件、full suite 713件をpass表示・process exit code 0で確認した。
- `compileall src tests`、`git diff --check`もprocess exit code 0だった。
- `presets.json` / `MMD_AutoLipTool.ini`はGit追跡対象外・root限定ignore、local `presets.json`保持を確認した。
- dependency / package / build / license差分はなく、production code、test code、GUIは変更していない。
- B4 / B5 / B6の手動GUI確認はユーザー報告の範囲に限定して再利用し、Codex自身のGUI実行とは扱わない。
- P1 / P2 / P3なし。MS22 CloseoutはAと判定した。次工程はMS23 Implementation Plan策定である。
- 実MMDでのVMD / WAV読み込み・リップ同期確認はMS26の未検証事項として維持する。

## 17. 対象ファイル整理

### 17.1 主変更候補

| 分類 | ファイル | 所有Block | 変更理由 |
| --- | --- | --- | --- |
| token / pipeline | `src/core/text_processing.py`、`src/core/pipeline.py` | B2 | `ー`由来metadataを互換的にtimelineへ渡す |
| timeline DTO | `src/vmd_writer/writer.py` | B2 | `VowelTimelinePoint`へadditive metadataを持たせ、normalize／repair時も保持する |
| effective core | `src/core/effective_shape_plan.py`、`src/core/event_adjustment.py` | B2 / B4 | B2のlong run、mode override、hold / decayを維持し、B4でresolver入力`ShapeParameters`のstale-hint guard用provenanceだけをadditiveに追加 |
| preset core | `src/core/generation_presets.py`、`src/core/settings_store.py` | B3 | preset schema、JSON、INIの選択復元 |
| history / state | `src/core/output_edit_state.py`、`src/core/event_adjustment_history.py`、`src/gui_wx/ui_state.py`、`src/gui_wx/ui_sync_context.py`、`src/gui_wx/main_frame.py` | B4 | atomic output state、history、resolver同期、stale generation hint拒否 |
| startup / persistence接続 | `src/gui_wx/app.py`、`src/gui_wx/app_controller.py`、`src/gui_wx/analysis_rollback.py` | B4 | single store ownership、INI保存、analysis lifecycle |
| diagnostics | `src/gui_wx/output_diagnostics_adapter.py`、`src/core/output_diagnostics.py`、`src/core/diagnostic_report.py` | B4 | effective long outputとgeneration summaryの同一正本化 |
| UI | `src/gui_wx/right_pane.py`、`src/gui_wx/selected_event_editor.py` | B5 | preset tabとterminal event mode override |

### 17.2 関連確認

- `src/core/preview_transform.py`
- `src/vmd_writer/effective_shape_adapter.py`
- `src/gui_wx/parameter_panel.py`
- `tests/test_vmd_writer_zero_guard.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_ms21_b3_pipeline_preview_integration.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `README.md`、`readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`

### 17.3 新規test（B2 / B3 / B4確定、B5以降候補）

- B2必須 `tests/test_ms22_b2_long_vowel_tokens.py`
- B2必須 `tests/test_ms22_b2_timeline_metadata.py`
- B2必須 `tests/test_ms22_b2_long_vowel_resolver.py`
- B2必須 `tests/test_ms22_b2_long_vowel_adapters.py`
- B2必須 `tests/test_ms22_b2_import_boundaries.py`
- B3必須 `tests/test_ms22_b3_generation_presets.py`
- B4必須 `tests/test_ms22_b4_generation_history.py`
- B4必須 `tests/test_wx_ms22_b4_generation_state.py`
- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_wx_ms22_b5_long_vowel_override.py`

B2の5 file、B3の1 file、B4の2 fileは各Implementation Planで確定済みである。B5以降のfile名は各Blockの
Implementation Planで実在するtest配置とimport境界へ再照合してから確定する。

## 18. テスト方針

### 18.1 実行順

各コマンドを一つずつ実行し、pass表示とprocess exit codeを分けて記録する。

1. B2 core: normalized reading token、timeline metadata copy、base identity、adjustment schema / canonicalization、
   hold / decay frames、run member ownership、same-vowel regressions、writer zero guard / multipoint、
   pipeline Preview identity、prepared VMD save
2. B3 core: JSON schema、100件境界、broken / future file、atomic save / cleanup、INI selection restore
3. B4 state: B2 canonical snapshotの保持、atomic history transaction、Undo / Redo後INI保存、
   fingerprint、WARNING、diagnostics、lifecycle guard
4. B5 wx: preset tab、Busy、dirty input、event override、theme、selection / tab behavior
5. B6 cross-regression: TEXTあり、voice-only、reset、analysis failure / cancel、save / report、workers
6. `tests`全体、`compileall src tests`、`git diff --check`

### 18.2 必須境界

- raw入力由来`ー`、G2P生成`ー`、voice-only正規化後`ー`、連続`ーー`、`あーあー`、先行母音なし`ー`、
  同音非長音、異母音、observationなし
- frame／母音が同一でmetadataだけ異なるidentity、RMS refine／peak反映／duration repair／adapter後のmetadata保持
- holdとdecayのcontrol point、decay終端zero、次shape隣接、source duration端、0長interval
- source peak／terminal end所有、continuation peak補正拒否、terminal event override、
  non-terminal / non-long / stale / synthetic拒否、decay時tail無効化
- built-in編集拒否、user preset 0 / 100 / 101件、duplicate id、invalid name、broken / future JSON
- active settingsと同値の明示tail override、decay中latent保持、preset apply、Custom変更、Undo / Redo、
  preset削除後history restore、missing / settings不一致idのCustom復帰、invalid JSON後user mutation拒否、
  Undo / Redo後INI保存失敗、restart後のsettings復元とhistory非復元
- effective output同一時のfingerprint不変、output変更時のWARNING再確認、VMD / report保存失敗時保持
- writer zero guard、same-vowel multipoint、pipeline Preview canonical identity、prepared writerのlegacy binary／
  invalid frame拒否
- MS21 failure rollback、late / duplicate callback、Busy、TEXTあり / voice-only、startup teardown

### 18.3 手動GUI確認

- built-in / user / Customの選択表示と、user presetの作成・更新・削除・上限表示
- hold / decayのPreview差、terminal event mode override、decay時tail control説明、
  long run memberの非所有control無効化と理由表示
- Preview選択、選択イベントtab、Undo / Redo、VMD保存、Warning、diagnostic report
- Busy、dialog cancel、JSON保存失敗を可能な範囲で確認する。

Codexは実施していないGUI確認を実施済みと表現しない。実MMDでのVMD / WAV読み込み・
リップ同期はMS26の手動受け入れまで保留する。

## 19. MS22全体の受け入れ条件

- 共通変換後の正規化済み読み列に明示された`ー`由来の長音だけが長音shapeとなり、
  既存same-vowel補正と混同しない。
- 長音metadataは全timeline再構築経路とbase identityへ保持され、metadataが異なるplanのadjustmentを
  誤適用しない。
- `hold`はpeak維持、`decay`は長音終端`0.0`への線形減衰としてPreviewとVMDで一致する。
- event mode override > active generation settings > application defaultの優先順位が実装・説明・testで一致する。
- source peakとterminal endの所有権が一意で、非所有member補正を黙って無視しない。
- tail補正はholdでのみ既存契約を保ち、decay中も明示overrideを失わず、decayの終端zeroを破らない。
- built-in presetと100件以内のuser presetを選択・適用・復元でき、壊れたJSONで既存データを自動破壊しない。
- preset適用とgeneration setting変更はsession内Undo / Redoで原子的に戻せ、再起動後にhistoryを復元しない。
- Preview、writer、diagnostics、fingerprint、report、WARNING確認が同じeffective outputを基準にする。
- TEXTあり／voice-only、lifecycle、fixed morph、30fps、VMD、audio三権分立、network禁止の回帰がない。
- docsは実装・検証・ユーザー報告・MS26未検証を区別し、Closeoutが根拠付きで判定される。

## 20. リスクと対策

| リスク | 対策 |
| --- | --- |
| 同音母音を長音として誤検出する | `ー`由来metadataだけを長音の正本とし、same-vowel候補を推論根拠にしない |
| DTO再構築で長音metadataを失い、stale adjustmentを誤適用する | 全copy経路を列挙し、metadataをidentity payloadへ含めてMS22 schemaへ更新する |
| Previewとwriterでlong shapeが分岐する | B2 resolverの`EffectiveShapePlan`だけを両adapterの入力とする |
| decayの終端zeroがtailで崩れる | decay時はtail controlを無効化し、event overrideでholdへ切替える明示導線を用意する |
| continuation補正を黙って無視してユーザー表示と出力がずれる | source／terminal所有権を固定し、非所有controlを編集入口で拒否して理由を表示する |
| presetがanalysis結果や個別補正を破棄する | preset fieldをoutput-only generation settingsに限定し、adjustmentとbaseを保持する |
| preset同値比較で明示tail overrideを消失する | `None=inherit`を正本とし、非`None`値はactive settingsと同値でもsnapshotへ保持する |
| history拡張でMS21 Undo / Redoが壊れる | B4でatomic state transaction、50件、gesture境界、legacy editor shortcut回帰を固定する |
| Undo / Redo後のINI保存失敗で再起動状態が不明瞭になる | in-memory commitをrollbackせず通知し、最後に保存成功したINIだけを再起動時に復元する |
| JSON破損時にuser presetを失う | automatic overwriteを禁止し、built-inのみのrecovery表示と明示操作を分離する |
| preset表示だけで保存確認が再要求される | fingerprintへ表示名・id・noticeを含めず、effective morph frameだけを正本にする |
| scopeがMS23 profileへ膨らむ | presetは3 field、fixed morph・profile JSON・morph upper limit preset化をMS22外に固定する |
| 実MMD未確認をCloseoutへ混入する | MS26の未検証事項としてB6 / B7に必ず残す |

## 21. Codex実装時の共通指示

- 各Block開始時に`git status`、branch、HEAD、対象plan、current code / testsを読み、既存変更を保護する。
- commandは一つずつ実行する。production code、test code、GUIをB1やpre-check段階で先行変更しない。
- 新規long-vowel metadataはadditiveにし、既存timeline caller、fixed morph、30fps、voice-onlyを壊さない。
- JSON read / write、event override、history mutation、diagnostic / save guardはfail closedを優先する。
- UI表示文字列・Notebook page index・Preview cacheをデータ正本にしない。
- testを弱めず、pass表示と終了コードの双方を記録する。失敗が同じ原因で2回続いた場合は反復せず、
  原因を分離して最小repairを計画・承認する。
- 依存関係、package、license、release、tag、merge、push、network、Qt / PySide6を変更しない。
- B7 Closeout前にMS22を実装済み・実MMD確認済みと記載しない。

## 22. 次のImplementation Planへの引き継ぎ

MS22-B1はCompleted / Contract Fixed、MS22-B2は2026-08-06にproduction code・B2専用test・
Preview / writer adapterまで実装し、full suite 644件＋7 subtests、compileall、diff checkを通過した。
B2のP1 / P2 / P3残存はない。MS22-B3は2026-08-08に`generation_presets.py`、SettingsStoreのgeneration key、
B3専用testを実装した。B3専用test 23件＋19 subtests、指定回帰、full suite 667件＋26 subtests、
compileall、diff checkを通過し、実装後レビューで検出したP2 / P3も解消した。B3の選択UI、state / history /
diagnostics統合、B5のGUI、実MMD確認は未実施である。MS22-B4 Implementation Planは2026-08-08に作成し、
`GenerationState` / `OutputEditState`、atomic history、resolve-before-commit、output-only parameter、startup /
rollback / diagnostics統合、MS21 fingerprint維持を固定した。計画作成baselineは180件＋19 subtestsがpass表示・
各process exit code 0だった。自己回帰チェックのP2 5件・P3 3件は文書上で解消した。B4 production code、
test code、GUIを実装し、手動確認で判明した母音Preview非表示も限定補修した。修正後のfull suite
686件＋26 subtests、compileall、diff checkを通過し、ユーザーからMS22-B4手動テスト通過が報告された。
MS22-B5 Implementation Planは2026-08-09に作成し、実装状態整合レビューのP2 3件・P3 2件を文書上で解消した。
2026-08-10にB5のproduction code、test code、GUI導線を実装し、B5専用test 10件、スプラッシュテストを除く
既存全体回帰694件、compileall、diff checkを確認した。ユーザーからB5手動GUIテスト通過が報告された。
既存スプラッシュテストの起動時間依存1件失敗はP3としてMS22-B6へ、実MMD確認はMS26へ引き継ぐ。
MS22-B6 Implementation Planは2026-08-11に作成・再レビューし、plan本文のP2 4件・P3 2件を解消した。
その後の再チェックで確認した、Block Breakdown / Index / Roadmapへの計画策定状態未反映P2も文書上で解消した。
同日にB6専用test、wx teardown限定修正、指定回帰、full suite、compileall、diff checkを完了した。
自動検証とユーザー報告によるmanual GUI確認を完了した。Codex自身はGUIを実行していない。
同日にMS22-B7 Implementation Planを作成し、MS22 direct regression 93件、full suite 713件、compileall、
diff checkをpass・exit code 0で確認した。計画作成時点ではtracked `presets.json`をP2候補、B5 splash statusを
P3候補としてpre-closeout gateへ固定した。その後の計画レビューでP2 / P3として確定し、runtime user dataの
追跡解除・ignore追加とsplash current status同期を分離repairで解消した。次工程はMS22-B7実装前チェックである。
