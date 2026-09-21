# MS20 and Beyond Index

## 1. 役割

本書は、MS20以降の現在地と正本文書へ誘導するrouting正本である。MS16からMS19のIndex・ロードマップは完了履歴の参照に限り、MS20以降の番号と依存順は本書と [MS20 and Beyond Roadmap](MS20_and_Beyond_Roadmap.md) を使用する。

## 2. 現在地

- 現在ブランチ: `feature/MS28-B1-implementation`
- MS25実装ブランチ分岐元HEAD: `61a2182 Finalize MS24 Closeout A`
- MS26実装ブランチ分岐元HEAD: `c881264 Record MS25-B7 closeout A`
- MS16からMS19: 完了済みの履歴領域
- MS27: **完了**。Ver.1.0の実装到達状態と既存のpackage/readiness証跡を確定し、追加のリリースパッケージ整備・GitHub Release・tag・push・merge・公開用source archive生成は完了条件に含めない。
- Active repair MS: **MS28: Ver.1.0不具合修正実装**。MS20〜MS27の全体マイルストーン系列とは切り離した、報告済み不具合の原因確認・限定修正・回帰検証を主目的とする。
- 現在フェーズ: **MS27 CloseOut完了、MS28-B4B実装済み、MS28-B5 Help/About実装計画作成済み・実装未着手。MS28-B4Bの実Whisper再解析、native GUI、実MMD、EXE、build、手動Debug ON/OFF比較、およびMS28-B5の実装・検証は未実施。**
- 2026-09-19にMS28-B2として、隣接long sourceの4分岐補修、同一frame handoff、R06/R07/R13/R14回帰を実装した。B2 resolverは39 passed、pipeline / Previewは4 passed、adapter・specは9 passed・21 subtests、全suiteは1100 passed・4 skipped・88 subtests・process exit code `0`、`git diff --check`もexit code `0`だった。版数、依存関係、spec / build設定、runtime JSON / INI、配布成果物は変更していない。実Whisper、GUI、実MMD、EXE、buildは未実施である。
- 2026-09-14にMS27-B4のfix-03候補を再ビルドし、`7 passed`、build / SmokeLaunch exit `0`、425758214 bytes、SHA-256 `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`、FileVersion / ProductVersion `1.0.0`を確認した。matplotlib package/data、sample_data、旧Qt、Torch test/TensorBoard、Numba TBB任意backendは成果物内0件で、Whisper / Torch / Numba主要moduleは保持されている。ユーザー手動確認と実MMD確認はユーザー報告であり、Codex自身のGUI / MMD操作とは扱わない。
- 2026-09-09に[MS26-B2個別Implementation Plan](Implementation_Plan/MS26-B2_Implementation_Plan.md)に従い、test-only duration helper / unit / 実FFmpeg integrationと既存横断回帰を実施し、main統合レビュー指摘6件を限定補修した。duration差0.05秒以内は実ファイル測定の自動回帰合格条件に限定し、保存時validator・エラー契約・個別保存・一括出力の動作は変更していない。初回・中間失敗を保持した補修後unitは25件、実FFmpeg matrixは20通常runner + 4 cancellable runner = 24測定caseである。MS17-B7、MS25、MS19〜MS24、pipeline/VMD、vmd_writer、full、compileall、diff checkの固有command IDとprocess exitはB2計画§15.2 / §15.5、実行者・HEAD・skip・未検証境界はB1計画§16.4に記録する。4 skipはsymlink生成のWindows `WinError 1314`に限定され、MS25 B6 fault gateと新規duration testにはskipがない。STEREO固定、B3素材未確定、MS27 deferredを維持し、B2は補修後の実装・自動回帰・実装内の計画 / 契約照合を完了した。
- 補修は、RIFF data tailのmono/stereo負例、probe前後source SHA-256、normal/cancellable両runner、既存FFmpeg locatorのsource/path/version、Curie Agent IDとwait設定、7対象pathのhash・command・diff証拠・B1 ledger cross-referenceを対象とした。このB2補修時点の次工程はメインの最終diffレビューであり、B3 / B4 / MS27へ自動移行しない。
- 2026-09-10に[MS26-B3個別Implementation Plan](Implementation_Plan/MS26-B3_Implementation_Plan.md)を作成し、現行Block Breakdown、GUI状態・Whisper runtime、既存profile / preset、指定MMD / PMX / audio / TEXT素材と照合した。再チェックで確認したP2（B3手動GUI gateの操作対象不足・cancel / failure / close経路の曖昧さ）とP3（正本code path列挙、routing状態の不足）を文書上で解消した。B3 material / environment gate、GUI・実MMD確認は未実施で、production code、test code、runtime JSON / INI、素材は変更していない。B3実施、B4、MS26 Closeout、MS27、stage / commit / pushへは進んでいない。次工程は、別途実行依頼を受けた後のB3-01 material / environment gateである。
- 2026-09-11にユーザーからMS26-B3手動GUIテスト通過・問題なしとの報告を受領した。これはユーザー報告としてMS26-B3-002へ記録し、Codex自身のGUI実行結果とは扱わない。実MMDのVMD / WAV読み込み・再生・morph対応・時間同期・見た目は未検証で、B3 actual-MMD Verification Pending、B4、MS26 Closeout、MS27は継続して未実施・deferredとする。
- 2026-09-12にユーザーから手動テスト通過・問題なし、AC03 / AC04確認済みとの報告を受領した。`MS26-B3-001` / `MS26-B3-002`へ追記したが、ケース別ログ・artifact・GUI / 実MMDの内訳は未提示であるため、AC03 / AC04はユーザー報告として通過扱いとし、詳細な追跡可能性とMS26 Closeout Aへは格上げしない。B4は部分実施、MS27はdeferredのままとする。
- 2026-09-12にメインがHEAD `fe4c95c`でB3承認素材5件のSHA-256を再確認し、Whisper availability worker / runtime / no-download / local-storeを25 passed・2 skipped（`WinError 1314`）、controllerを3 passed、Whisper UIを4 passedとして単独実行した。全コマンドのprocess exit codeは`0`。B2-R05 daemon headerは再現せず、原因・影響は未確定でコード補修は行っていない。`MS26-B4-002`として台帳へ記録した。AC03 / AC04のユーザー報告を保持しつつ、ケース別追跡可能性、B4全面再検証 / Closeout判定は未実施で、MS27へ移行しない。
- 2026-09-12にユーザーからMMD `Ver 9.32`、model path `D:\Visual Works\MMD Folder\MikuMikuDance64\UserFile\Model\Kanna\Mobco\_V4B\Mobco\_v2\_2024B3\_edit2.pmx`、入力音声 `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1.wav`、出力MMD用WAV `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD\MMD_AutoLipTool説明1_mmd.wav`を受領した。日本語・ラテンおよび`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`はユーザー確認済み・問題なしとして記録する。生成物一組はread-onlyで確認済みだが、4ケース別artifact対応、PMX hash / morph一覧、B4全面再検証 / Closeout判定は未実施で、MS27へ移行しない。
- 2026-09-12にユーザーから、GUI再生、voice-only編集・再解析、状態・保存可否、delivery保護・復旧、Whisper未配置・no-download、profile / preset適用と復帰をすべて確認し、主な不具合なし・正常作動との報告を受領した。`MS26-B3-004`として記録する。4ケース別artifact対応もユーザー確認済みとして扱うが、詳細操作ログ・PMX hash / morph一覧の台帳転記、B4全面再検証 / Closeout判定は未実施で、MS27へ移行しない。
- 2026-09-12にユーザーから、GUI再生、voice-only編集・再解析、状態・保存可否、delivery保護・復旧、Whisper未配置・no-download、profile / preset適用と復帰、実MMD上の音声・モーフ同期をすべて確認し、主な不具合なし・正常作動との報告を受領した。`MS26-B3-004`およびB4最終監査へ反映し、MS26 CloseOut Aを確定した。PMX hashの独立取得不可は補助identityの制限として記録し、MS27のpackage / release readinessはdeferredとする。
- 同日付で先に記録されたB3 / B4の「未実施・未確定」は最終受入前の中間記録であり、現在状態は本節の先頭行および上記の最終受入記録を正とする。
- 2026-09-07にメインがB1実装後チェックを実施し、B1成果物を受け入れ可能と判定した。P1 / P2 / P3残存なし。受入条件と実施記録の対応、証拠台帳21行の13列構造、回帰入口12ファイルの実在、STEREO固定、B1 / B2 / B3の証拠境界を確認し、`git diff --check`はprocess exit code `0`だった。詳細はMS26-B1計画§16.2。pytest・GUI・実MMDは未実行で、duration検証はB2所有課題、実MMD素材・環境はB3開始条件として維持する。次工程はB2個別計画・実装前チェックであり、B2実装・回帰、B4、MS27には進んでいない。
- 2026-09-06に承認済みMS26-B1 planに従い、live HEAD `e2d63ad1d1469f6a74ee09d508c26c1c4b47ba08`でB1-01〜07を実施した。開始時working treeはcleanで、`c881264..HEAD`のruntime code / test / dependency / lock差分はなく、docs-only差分によるruntime contractの失効はない。B1はbaseline、ledger、blocking contractを固定したためbaseline / contract gateをpassedとしたが、これはB2自動test成功を意味しない。旧HEAD `0b25c5c`のMS25 test totals（B6 required `26 passed`、aggregate `160 passed, 2 skipped`、cross-boundary `322 passed`、full `1041 passed, 4 skipped`）は歴史証拠として保持し、現行HEADのpassへ転用していない。B2必須自動test、duration差`<= 0.05秒`の取得 / 比較 / 超過 / 取得不能gate、B3のWindows 11 / MMD / model / audio / TEXT / Whisper / preset / profile素材確定、GUI / actual MMD操作、B4再検証は未実施である。duration差の未証明はB2所有findingとして記録し、MS27 package / release readinessはdeferredのままとする。
- 2026-09-04にMS25 Closeout Aを基準として`feature/MS26-implementation`を作成し、MS26 Block Breakdownを作成した。MS26-B1以降の実装、自動横断回帰、Windows 11実機確認、実MMD確認、Closeout判定は未実施である。MS25の既存履歴、Python 3.11 / 3.12の未検証扱い、MS27 package / release readinessのdeferredは維持する。
- 2026-09-04にMS26-B1個別Implementation Planを作成し、現行コード・テスト・仕様・MS25契約を照合した。B1ではproduction code、test code、GUI、runtime user dataを変更していない。B2 full pytest・横断回帰は未実施だが、文書修正の契約確認としてSTEREO固定対象テスト8件をprocess exit code `0`で確認した。実MMD受入素材・環境は未確定のためB3開始条件として記録した。MMD用WAVは現行コード・validator・正文仕様をchannel count 2（stereo固定）へ同期済みであり、mono許容への変更は行わない。今回の文書再確認でP1 / P2 / P3の残存はない。
- 2026-08-28にMS24 Closeout Aを判定した。P1 / P2はなく、B7-F-001 / B7-F-002は解消済みとして記録した。Python 3.11 / 3.12は今回の受入対象外として未検証扱いを維持し、実MMD確認はMS26、package / release readinessはMS27へ引き継ぐ。
- 2026-08-30にMS25-B1実装前チェックのP2（同一capture内のwriter state / failure reason再利用手順不足）とP3（MS25 routing・長時間確認テスト実行順の記載不足）を文書上で補正した。MS25-B1のproduction code、test code、GUI、runtime user data、設定、依存関係は未変更である。
- 2026-08-30にMS25-B1を実装し、B1専用17件、関連回帰162件、全pytest 898 passed・2 skipped、`compileall`、`git diff --check`をprocess exit code 0で確認した。実装コミットは`a41f0a0`で、手動GUI確認はB1の可視actionがないため未実施・不要とした。MS25-B2 Implementation Planを作成済みで、B2 production code / test codeは未実装である。
- 2026-08-31にMS25-B2を`0f018cd Implement MS25-B2 delivery package orchestration`として実装し、B1/B2のstaging、cancel、cleanup、pre-commit guard、no-clobber commitの契約を確定した。同日にMS25-B3 Implementation Planを`901de91 Document MS25-B3 implementation plan`として作成した。2026-09-01の実装前チェックで、B3計画へWAV result pathの解決済みidentity比較を補正し、MS25 routing状態を同期した。今回の実装前チェックで確認したP1/P2/P3の未解消はなく、B3 production code / test code、GUI、runtime user data、依存関係は未変更である。
- 2026-09-01にMS25-B3を`904ccae Implement MS25-B3 delivery artifact adapters`として実装した。B3のVMD、MMD用WAV、診断レポート生成アダプターとB2 transaction境界を現行コードへ反映済みである。
- 2026-09-02のMS25-B4実装前チェックでは、B1 current stateのmorph namesとsnapshot resolved set IDのcross-field invariant、およびstandalone report writerの安全な外向けエラー表示とError仕様の詳細表示範囲を確認した。前者はB1のfail-closed guardと回帰testを追加し、後者はB4で詳細表示UIを実装済みと主張しない範囲境界をB4計画へ明記した。Index、B3計画、B4計画の現行状態記述を同期し、B4 production implementationは未着手のまま維持する。
- 2026-09-03にMS25-B5を`bb9c60d Complete MS25-B5 delivery package GUI integration`としてcommitした。一括出力menu、destination dialog、delivery専用worker、Busy / cancel / close lifecycle、pre-commit UI bridgeを接続し、B1〜B4のcore契約と個別保存導線を維持した。false `delivery_busy` を起こすworker state / reference不整合をP3修正した。B5および関連worker / GUI回帰は`29 passed`、全pytestは`1015 passed, 4 skipped`でprocess exit code `0`、`compileall -q src tests`と`git diff --check`もexit code `0`だった。ユーザーから提示したB5手動GUIテスト通過の報告を受領したが、これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。B6 fault matrix、B7 full cross-boundary regression / closeout、実MMD確認は未完了で、Python 3.11 / 3.12とMS27 package / release readinessも未検証・deferredである。今回のB5変更についてpush / merge / tag / releaseは未実施である。
- 2026-09-04にMS25-B6 Implementation Planを`9841de4 Document MS25-B6 implementation plan`として作成済みである。実装前チェックで確認したB6専用testの責務・ファイル名、MS25 routing、`output_path_inspection_failed`のError code一覧欠落を文書上補正した。B6 fault matrix、B7 full cross-boundary regression / closeout、実MMD確認は未完了で、stage / push / merge / tag / releaseは未実施である。
- 2026-09-04にMS25-B6をworking treeへ実装し、その後`5300905 Implement MS25-B6 delivery recovery hardening`としてcommitした。staging identity再確認、OS fault分類、collision優先のno-clobber commit、cleanup failureのterminal化、delivery close状態のreconciliationを反映した。B6専用testは`26 passed`、B6直接回帰は`134 passed, 2 skipped`、指定cross-boundary回帰は`94 passed`、全pytestは`1041 passed, 4 skipped`で、いずれもprocess exit code `0`である。Windows実filesystemのjunction collisionとsharing violationはskipなしで通過した。ユーザーから提示したB6手動GUI確認通過・問題なしの報告を受領したが、これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。B6のstage / commitは完了済みで、B7のfull regression / closeout、README等の最終同期、実MMD確認、MS27 package / release readinessは未実施または後続である。
- 2026-09-04にMS25-B7を検証HEAD `0b25c5c Document MS25-B7 implementation plan`で実施した。B6 required gateは`26 passed`、MS25-B1〜B6 aggregateは`160 passed, 2 skipped`、cross-boundary 4群は合計`322 passed`、全pytestは`1041 passed, 4 skipped`で、各process exit codeは`0`だった。4 skipはWindows symlink作成権限不足（WinError 1314）に限定され、B6 required Windows fault gateにはない。`compileall -q src tests`と文書差分の`git diff --check`もexit code `0`である。README、配布用readme、Pipeline / GUI State / Error Handling / VMD Output正文仕様を照合し、必要事項が反映済みのため変更不要と判定した。B7文書同期、P1 / P2 / P3 finding再確認、MS25 Closeout A判定を完了した。B7実施でproduction code、test code、GUI、dependency、build設定、runtime user dataは変更していない。実MMD確認はMS26、Python 3.11 / 3.12は未検証、MS27 package / release readinessはdeferredであり、push / merge / tag / releaseは未実施である。
- MS20はCloseOut済み（A）。MS21はB1からB7まで実装・自動検証・対象ユーザーGUI確認を完了し、2026-07-31にB8 Closeout監査を完了した。B7ではState Integration / Regression / DocsとUndo / Redo同期効率化に加え、Preview event選択時のRightPane「選択イベント」tab自動切替を追加補正として実装した。B7専用15件、B2〜B6回帰123件（B5専用再確認28件を含む）、MS17 / MS19 / MS20・既存回帰154件＋7 subtests、full suite 618件＋7 subtestsはすべてpass表示・process exit code 0で、`compileall` と `git diff --check`もexit code 0だった。B1からB7のユーザー確認報告を範囲限定で再利用し、P1 / P2 / P3なしのCloseout Aを確定した。実MMDでのVMD / WAV読み込み・リップ同期はMS26へ引き継ぐ。MS22-B1はContract Fixedまで完了した。MS22-B2は2026-08-06にproduction code、B2専用test、Preview / writer adapterを実装し、B2専用26件、full suite 644件＋7 subtests、`compileall`、`git diff --check`をpass・exit code 0で確認した。MS22-B3は2026-08-08に`generation_presets.py`、SettingsStoreのgeneration key、B3専用testを実装し、B3専用23件＋19 subtests、指定回帰、full suite 667件＋26 subtests、`compileall`、`git diff --check`をpass・exit code 0で確認した。実装後レビューのP2（routing文書の未同期）とP3（表示名境界・atomic write失敗経路のテスト証拠不足）を解消した。MS22-B4 Implementation Planは同日に作成し、state / history / diagnostics / lifecycle統合の責務を固定した。2026-08-09にB4 production code、B4専用test、MS20 / MS21 / MS22回帰を実装した。手動確認で判明した母音Preview非表示を限定補修した後、関連33件、full suite 686件＋26 subtests、`compileall`、`git diff --check`をpass・exit code 0で確認した。同日にユーザーから問題解消とMS22-B4手動テスト通過が報告された。MS22-B5 Implementation Planを作成済みで、B5のproduction code、test code、GUIは未実装である。B4のpreset selector UIはB5、実MMDでのVMD / WAV読み込み・リップ同期はMS26へ引き継ぐ。
- MS22-B5は2026-08-10にproduction code、B5専用test、GUI導線を実装し、B5専用test 10件、スプラッシュテストを除く
  既存全体回帰694件、`compileall src tests`、`git diff --check`をprocess exit code 0で確認した。ユーザーによるB5手動GUI確認も通過した。
  全体実行で発生した既存`tests/test_wx_startup_splash.py`の起動時間依存1件失敗はP3としてMS22-B6へ引き継ぎ、実MMD確認はMS26へ維持する。
- 直前のMS22-B5未実装記述は2026-08-09の計画作成時点を示す履歴であり、現在状態は上記の実装済み記録を正とする。
- MS22-B6 Implementation Planは2026-08-11に作成・再レビューし、plan本文のP2 4件・P3 2件と、計画策定状態を
  routing正本へ未反映だったP2 1件を文書上で解消した。これは実装前の計画段階の記録であり、次の実装記録で状態を更新した。
- 2026-08-11にMS22-B6を実装した。non-wx lifecycle 7件、wx lifecycle 9件、splash 3件を追加・決定論化し、
  wx終了時のcoalesced save timer停止、`AutoLipToolApp`の遅延Layout / Refresh callback guard、
  test teardown helperを限定補修した。B2専用29件、B3〜B5専用45件、
  settings / export 13件、B4 / B5 / splash組合せ18件、MS17〜MS21 lifecycle 36件、save / diagnostics 33件、
  full suite 713件、`compileall src tests`、`git diff --check`はすべてprocess exit code 0だった。
  自動検証は完了した。2026-08-11にユーザーから手動GUI確認通過・問題なしの報告を受領したが、
  Codex自身のGUI実行結果とは扱わない。MS22 Closeout判定はB7、実MMD確認はMS26へ維持する。
- 2026-08-12にMS23 Block Breakdownを作成し、現行code、test、Roadmap、MS22完了契約へ再照合した。初回案の
  P2 7件、P3 2件は計画文書上で解消し、P1はなかった。`morph_upper_limit`のanalysis境界とoutput-only history、
  profile / preset failure matrix、fingerprint identity、`/profiles.json`のruntime ignore、event adjustmentのfield ownership、
  B2〜B4責務、MS25非先行実装を固定した。production code、test code、GUIは変更していない。
- 同日にユーザーはD1を採用した。`default_preset_id`はstable reference、参照先presetはbaseline、profileのnon-null fieldは
  override、nullable fieldはpreset継承とする。MS23-B1 Implementation Planを作成し、次工程を参照中user presetのdelete guard、
  active profile mutation、startup unresolved fallback、fingerprint schemaの一問一答確認とした。B1 contract pre-checkとMS23実装は未開始である。
- 2026-08-13にMS23-B1 plan再チェックのP2 5件を文書上で補正した。writer / coreのimportとmixed namespace、
  semantic final normalization後のmorph-name mapping、別preset Apply後のruntime baseline、commit前failureとcommit後INI save failure、
  pytestのpass表示とprocess exit code gateを固定した。D1Aとして、profile Apply直後は`default_preset_id`、以後の別preset Applyは
  専用INIキー`active_profile_baseline_preset_id`をruntime baselineとして再起動でも優先する。active profile中は既存
  `active_preset_id=None`とし、preset単独時のCustom正規化は変更しない。
  初回19件のexit code 1は関数単位、全8件、元の19件commandをtest変更なしで再実行し、exit code 0を確認した。
  production code、test code、GUIは変更していない。
- 同日、ユーザーはD2〜D5をすべて推奨案Aで採用した。参照中user presetは参照変更までdelete拒否、active user profileの
  value / set updateとdeleteはinactive化まで拒否、startup unresolved profileはno-profile + JapaneseとINI数値保持へ正規化、
  valid profileのruntime baselineだけがunresolvedならprofile defaultへfallback、fingerprintはcanonical payload構造と
  `ms21-effective-output-v1`を維持する。全decision gateは解消済みで、次工程はread-only B1 contract pre-checkである。
  production code、test code、GUIは変更しておらず、B1はまだContract Fixedではない。
- 同日のB1実装前チェックでは、active runtime baseline presetのvalue mutationと、active profile中global direct editで
  baseline identityとcurrent effective値が不一致になり得るP2 2件を検出した。ユーザーの解消指示に基づき、D6として
  active runtime baseline presetのvalue update / deleteをprofile inactive化または別baseline選択まで拒否し、settings同値Renameだけを
  metadata mutationとして許可する。D7としてactive profile中のglobal generation settings / `morph_upper_limit` direct editは
  exact no-op以外をcommit前に拒否する。event adjustment、別preset Apply、no-profile時のMS22 direct edit、preset単独時の
  Custom正規化は変更しない。P2は文書上で補正済みで、次工程は補正後B1 contract pre-checkのread-only再チェックである。
- 2026-08-15の再チェックでは、startup seam testが実スプラッシュを生成してaccess violationによるexit code 1を起こすP2を確認した。
  splash専用testとの責務を分離するtest isolationを補正し、同一19件commandをpass表示・exit code 0へ復帰させた。live Git記述、
  read-only code対象、P1/P2/P3 gate表記のP3も同期して解消した。その後、現行preset schemaとの照合でB1 planに残っていた
  profile schemaのunknown key、display name、ID、`default_preset_id`の未確定表現をS1として補正し、文書上のP2を解消した。
  MS23 featureのproduction code、test code、GUI実装は開始していない。次工程は補正後B1 contract pre-checkのread-only再チェックである。
- 同日の一問一答で、built-in ID（`builtin:japanese-vowels` / `builtin:latin-vowels`）、専用core profile state、
  `GenerationState`のresolved morph-name set ID、B4のcross-store resolution / mutation guard、workspace reset時のprofile保持、
  profile nullable `morph_upper_limit`、startup補正後IDのINI保存を採用した。B1 / Block Breakdown / Index / Roadmapの計画記述を同期し、
  exact class名、private helper名、error code名だけをB4 planへ明示的にdeferした。MS23実装は開始しておらず、当時の次工程はfresh read-only
  B1 contract pre-checkである。
- 2026-08-15にfresh read-only B1 contract pre-checkを実施した。現行Git、B1関連計画、MS22完了契約、profile未実装の現行code境界、
  関連test、dependency / package境界を再照合し、249件がpass表示・全command process exit code 0、`git diff --check`もexit code 0、
  P1 / P2 / P3なしを確認した。B1をCompleted / Contract Fixedと判定し、B2 / B3 Implementation Plan策定へ進める状態へ同期した。
  これは契約・計画段階の完了であり、MS23 featureのproduction code、test code、GUI実装完了ではない。profile実装、`profiles.json`生成、
  `/profiles.json` ignore追加、実MMD確認はそれぞれB3以降またはMS26へ維持する。
- 2026-08-16にMS23-B2 Implementation Planを作成した。built-in setの正本、semantic keyとdisplay / output nameの分離、
  final normalization後の一回mapping、writerのprimitive output-name boundary、Preview / diagnosticsの明示入力、
  fresh-process / mixed-namespace import検証を固定した。B2のproduction code、test code、GUI実装、profile store、INI、runtime user dataは
  変更していない。MS23-B2実装開始は本planのレビュー後とし、B3 Implementation Plan策定とMS26 Actual-MMD Verification Deferredは維持する。
- 同日、MS23-B2 Implementation Planの再チェックでP2 4件（writer / coreのvalidation authority、diagnostics DTOのallowed-name入力、
  Preview display nameのDTO契約、B2 / B4 fingerprintテスト責務）を計画文書上で補正した。既存引数・既存DTO構築・semantic hit-testを
  維持する互換境界、`None`と省略の区別、`EffectiveWriterInput.allowed_morph_names`、B4所有のprofile identity不変性を明記した。
  関連回帰162件はpass表示・process exit code 0、`git diff --check`もexit code 0で、production code、test code、GUI、runtime user dataは
  変更していない。B2実装は未開始であり、次は別途実装開始承認後の着手とする。
- 同日、MS23-B2実装前チェックで追加確認されたP2（Previewのempty / empty timeline / clear時の表示名保持、
  `MorphNameSet`のbuilt-in display name DTO契約）を、B2 planとBlock Breakdownへ補正した。`empty_preview_data`と
  `PreviewModel.clear`は明示的なordered output-name tupleを受け、既存の省略経路は日本語defaultを維持する。B4 diagnosticsの
  display nameは`MorphNameSet`から取得し、ID別の表示名表を再構築しない。production code、test code、GUI、runtime user dataは
  変更しておらず、B2実装は未開始のまま、P2解消後のfresh read-only再確認へ進める状態である。
- 同日、MS23-B2を実装した。`MorphNameSet`とJapanese / Latinのbuilt-in mapping、writer / effective-shape adapterの
  normalize-before-map境界、Previewのsemantic key / display name分離、diagnosticsのresolved output-name境界、
  fresh-process import boundaryを追加した。B2専用24件、関連回帰228件、full suite 738件、`compileall src tests`、
  `git diff --check`はすべてprocess exit code 0だった。既存省略経路の日本語default、VMD 30fps、frame number / value / count /
  sort order、Preview hit-test、fingerprint schemaは維持している。手動GUI確認は未実施で、profile store、INI、runtime user data、
  B3 / B4 / B5、MS25以降の実装は行っていない。実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。
- 同日、ユーザーからMS23-B2の手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、
  Codex自身のGUI実行結果とは扱わない。実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。
- 同日、MS23-B3 Model Profile Store / Persistence Implementation Planを作成した。B1のschemaとB4責務境界に従い、
  immutable profile DTO、strict versioned `profiles.json`、最大100件、atomic Create / Update / Delete、structured failure、
  INIの`active_model_profile_id` / `active_profile_baseline_preset_id`、旧caller省略時の保存値維持、root限定`/profiles.json`を固定した。
  structurally validなmissing preset reference、active profile mutation guard、startup resolutionはB4へ残す。計画作成時のread-only baselineは
  B2 + preset / settings 53件＋19 subtests、SettingsStore consumer群67件＋19 subtestsがpass表示・各process exit code 0だった。
  production code、test code、GUI、runtime user dataは変更していない。次工程はB3 planレビューとfresh read-only pre-implementation checkである。
- 同日のB3 planレビューではP1なし、P2 3件、P3 1件を確認した。P2は`morph_upper_limit`がB1のfinite floatより
  広いJSON intを受理していたこと、constructor直後のload前mutationが未定義だったこと、INI同一directoryのtarget pathを
  直接検証するtestがなかったことである。P3はB4の将来都合による`src/core/__init__.py`変更余地である。
  B1 strict floatへの復帰、unloaded / `store_not_loaded` gate、load前lookup / mutation非変更、settings path / store注入 / explicit override /
  引数排他testを固定し、package root export判断をB4へ延期した。production code、test code、GUI、runtime user dataは変更していない。
  補正後のread-only回帰は53件＋19 subtests、67件＋19 subtestsがpass表示・各process exit code 0だった。
  次工程は補正後B3 planのfresh read-only再チェックである。
- 2026-08-17にB3を実装した。`ModelProfile` / nullable overrides、strict versioned `profiles.json`、load前拒否、fail-closed load、atomic
  Create / Update / Delete、SettingsStoreのactive profile identity 2種、旧caller保存互換、root限定ignoreを追加した。B3専用21件＋31 subtests、
  関連回帰、full suite 759件＋57 subtests、`compileall src tests`、`git diff --check`はすべてprocess exit code 0だった。B3はUI非依存のstore / persistence
  blockでありmanual GUI確認は必須でない。cross-store resolution、active guard、GUI、実MMD確認はB4 / B5 / MS26へdeferredである。
- 同日、[MS23-B4 Implementation Plan](Implementation_Plan/MS23-B4_Implementation_Plan.md)を作成した。B1で採用済みのD1〜D7・S1〜S7に従い、
  exact profile state / resolution status / reason / error code、profile-aware history、startup identity-only save、cross-store mutation guard、
  `AppController -> core.pipeline -> writer`とPreview / diagnostics / reportへのresolved output-name伝播を固定した。計画作成baselineは
  core / store / history / rollback 74件＋50 subtests、wx / lifecycle / diagnostics / pipeline 99件がpass表示・各process exit code 0だった。
  planning document以外のproduction code、test code、GUI、runtime user dataは変更していない。次工程はB4 planレビューとfresh read-only実装前チェックである。
- 続くplan reviewではP1なし、P2 5件、P3 1件を確認した。推奨修正方針に従い、profile-aware Undo / Redo後のfull save、active profile下の
  history初期endpoint、`full > identity_only > none`のsave pending priority、guard overlap時のcode優先順位、exact DTO / API、pending coalescingの
  local candidate settleをplanとBlock Breakdownへ反映した。MS22 Closeout AとD1〜D7・S1〜S7は変更していない。B4 production implementationは未開始で、
  次工程は修正後planのread-only再チェックである。
- その後のfresh read-only再チェックでは、B1 / B3のstrict float・0.0〜10.0契約に対する`ResolvedModelProfile.morph_upper_limit`の型・上限記載不足をP2として確認した。
  ユーザー採用の推奨修正としてstrict float、有限、0.0〜10.0、bool / int / string拒否をB4 planとBlock Breakdownへ反映した。production code、test code、GUI、runtime user dataは変更していない。
  追加修正後のfresh read-only再チェックが次工程である。
- 2026-08-18にMS23-B4を実装した。専用profile state / resolver、startup ID補正、profile-aware history、cross-store mutation guard、active profile中のglobal direct-edit拒否、
  pipeline / Preview / diagnostics / reportへのresolved output-name伝播、rollback consistencyを接続した。B4専用12件、MS21 / MS22 / MS20関連回帰52件、full suite 771件＋57 subtests、
  `compileall src tests`、`git diff --check`を確認した。full suiteはsummary完走・failure / error表示なしだがprocess exit code 1であり、B4追加wxテスト除外でも同じ既存wx終了処理系の終了コード1を再現した。既存日本語default、preset単独Custom、VMD 30fps、fingerprint schema、runtime user data境界は維持した。
  B4は自動検証済みで、profile UIの手動確認はB5、実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。
- 同日、full suiteの`-X faulthandler`再実行で、全テスト終了後のGarbage Collection中に`Windows fatal exception: access violation`を確認した。`-k "not wx"`はprocess exit code 0、`-k "wx"`は同じnative exceptionでexit code 1だった。legacy wx testsにApp ownership不明、重複`wx.App()`生成、frame-only teardown、GC依存が残るため、これはB4のP2としてMS23-B4Bへ切り出した。
  B4Bは既存`tests/helpers.py`の`destroy_wx_app()`を正本候補とするtest-harness firstの修正計画であり、production code変更、test変更、GUI変更は未開始である。次工程はB4B fresh read-only pre-checkで、B5 UI実装へは進めない。
- B4B plan reviewでP2 4件、P3 1件を確認した。active Appは「同時に複数存在しない」と定義し、teardown後の順次生成を許可した。MS16 / MS21 / MS22のdirect App / Frame teardownを監査対象へ追加し、Controllerのpending saveをtemporary storeへ隔離してroot runtime user dataを保護する契約を追加した。production code変更はB4B内で行わず、必要時は別planまたは明示承認へ戻す。既知再現commandもplanへ固定した。これは実装前の計画レビュー記録である。
- 同日、MS23-B4Bを実装した。`tests/helpers.py`とMS14〜MS23の対象wx test teardownを共通契約へ移行し、owned / reused App、Frame identity単位のidempotence、Controller / timer / pending callback、temporary store、teardown済みAppのsingleton解除、native pending-delete処理を固定した。production code、GUI、runtime user dataは変更していない。既知再現10件、wx aggregate `129 passed` 2回、non-wx `644 passed`＋57 subtests、full suite `773 passed`＋57 subtests 2回、B4/B4B専用14件、`compileall src tests`はprocess exit code 0だった。B4Bの手動GUI確認は不要であり、B5 profile UIとMS26 actual-MMD確認は未完了のまま維持する。B4B変更は`cc23666 Implement MS23-B4B wx teardown repair`としてcommit済みで、pushは未実施である。
- 同日、[MS23-B5 Implementation Plan](Implementation_Plan/MS23-B5_Implementation_Plan.md)を作成した。現行RightPane placeholder、MS22-B5 preset UI、B3 profile store、B4 resolver / state / history / mutation guard、B4B wx teardownを照合し、stable IDによるSelect / Apply分離、nullable override / inherit dialog、active Rename-only、Controller-side candidate UUID生成、Busy / dirty / stale guard、profile / preset panel cross-syncを固定した。plan reviewではP1なし、P2 2件、P3 2件を確認した。Create初期値はD1準拠のinherit-firstとし、inactive CRUDでcurrent output / profile identityを変更しない契約、mutation前後のstable ID集合差によるcreated ID取得、実在B4 test名へ補正した。計画作成baselineは`41 passed, 31 subtests passed`、process exit code 0である。B5 production code、test code、GUI、runtime user dataは未変更で、次工程はfresh read-only実装前チェックである。
- 2026-08-19にMS23-B5を実装した。RightPane / MainFrame / AppControllerのprofile UI接続、Select / Apply分離、CRUD、Busy / stale guard、profile / preset cross-syncを接続し、削除確認結果の`wx.ID_YES`比較修正と削除後のリスト再投影を回帰テストへ固定した。連続する同一母音の長音境界も補正し、`long_vowel_mode=decay`でPreview形状計画が失敗する共通経路を解消した。関連回帰31件、全体785件＋57 subtests、`compileall src tests`、`git diff --check`はprocess exit code 0だった。同日、ユーザーから手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。旧ユーザーモデルプロファイルのruntime削除とactive profile参照のクリアはlocal data整理として実施し、`presets.json`は変更していない。実MMD確認はMS26へdeferredであり、次工程はMS23-B6である。
- 2026-08-20にMS23-B7 Closeout監査を実施した。MS23 direct 82件＋31 subtests、MS21 / MS22関連90件、diagnostics / report / Preview / writer / VMD174件、lifecycle54件＋7 subtests、wx aggregate136件×2、full suite797件＋57 subtests×2、`compileall src tests`、`git diff --check`はすべてprocess exit code 0だった。runtime user data 3 pathのroot限定ignore・Git非追跡、package / dependency / license / network / Qt境界の差分なしを確認した。B2 / B5 / B6のGUI確認はユーザー報告の範囲だけを再利用し、Codex自身のGUI実行とactual-MMD確認は行っていない。P1 / P2 / P3なし、MS23 CloseoutはAと判定し、次工程をMS24 Implementation Plan策定へhandoffする。実MMD確認はMS26へdeferredである。
- 同日、MS24 Block Breakdownを作成した。公式Whisperの公開版・モデル・loader契約を再調査し、`small` / `medium` / `turbo`、既定値small、versioned manifest、exe隣接`models`、明示確認後のforeground download、SHA256 / exact size、全Whisper timing経路へのmodel伝播、専用diagnostics、配布影響確認についてB1〜B7のBlock分割と実装前確認ゲートを定義した。レビュー後、TEXT + 音声 / voice-onlyの両経路適用、verified local checkpoint専用のnetwork-unreachable loader、v20250625 alignment heads / private API version gate、retained timing identity / rebuild reason、model-aware rollback禁止class、single-active cache / 明示unload、専用`WhisperDiagnosticsSummary`、Python 3.14.3 classifier外記録とPython 3.13系列の公式互換性確認を計画へ反映した。`openai-whisper==20250625`は初期計画で維持し、GitHub `main`直採用や無条件の依存更新は行わない。MS24-B1 Implementation Plan、production code、test code、GUI、依存関係、runtime user dataは未変更である。MS22 / MS23 Closeout Aは維持し、実MMD確認はMS26、package / release最終判定はMS27へdeferredである。
- 2026-08-21にMS24-B1 Implementation Planを作成・補正した。source / frozenの`src.core` manifest resource runtime解決、installed packageの`core/whisper_models.json` package-data配置マッピング、検証済みbytes loader、network-unreachable境界を固定した。現行`core/__init__.py`と`src.core.*`の混在importによりinstalled `core.whisper_models` runtime importは成立しないため、B1のinstalled package gateは静的配置確認に限定し、既存アプリ全体のinstalled namespace補修はpackage工程へ分離した。MS24-B1のproduction code、test code、GUI、依存関係、runtime user dataは未変更で、次工程は補正後のread-only pre-implementation checkである。実MMD確認はMS26、package / release最終判定はMS27へdeferredである。
- 2026-08-21にMS24-B1を`eafdc16 Implement MS24-B1 Whisper model contract`で実装した。versioned manifest、catalog、verified-local bytes loader、v20250625 version / alignment-head gate、package/spec境界、B1専用testとword / segment fallback回帰を反映した。B2〜B6の実装、Python 3.13互換性確認、GUI、実モデル、実MMD確認は未完了であり、実MMD確認はMS26、package / release最終判定はMS27へdeferredである。
- 2026-08-22にMS24-B2 Implementation Planを作成し、レビューで確認されたP2（B5発行・B2検証のmodel-bound単回permit、canonical `.part`専用cleanup API、artifact statusとfailure codeの写像、B2/B3/B4/B5責務、preflight順序）を計画書へ反映した。関連するBlock Breakdown、B1 plan、Roadmapの状態・責務・全Whisper timing経路の記述も同期した。次工程は補正後MS24-B2 planのread-only pre-implementation recheckである。production code、test code、GUI、依存関係、runtime user dataはこの文書補正で変更していない。
- 同日、メインエージェントでMS24-B2 Implementation Planを再チェックし、P2（caller-supplied promote path、permit issuerの実装境界、root reparse/junctionのlocal-only境界）とP3（B2 failure codeのB4/B5/B6 handoff）を推奨案で計画書へ補正した。promoteはmodel keyから解決したcanonical `.part`だけを扱い、permitはB5専用issuer boundaryのopaque capabilityとし、failure codeは上位投影後もdiagnostic detailとして保持する契約を固定した。P1 / P2 / P3の残存はない。production code、test code、GUI、依存関係、runtime user dataは変更しておらず、次工程はMS24-B2実装前チェックである。
- 2026-08-23にMS24-B3 Implementation Planを作成し、main-agent recheckで確認されたP2（canonical identity fieldの対応、B2実装済み状態とrouting文書の不一致）を計画書へ反映した。Index、Block Breakdown、MS24-B2 plan、Roadmapの現行状態をB2実装済み・B3 plan作成済みへ同期した。B3のproduction code、test code、GUI、依存関係、runtime user dataは未変更で、次工程はMS24-B3のfresh read-only pre-implementation checkである。実MMD確認はMS26、package / release最終判定はMS27へdeferredである。
- 2026-08-23のMS24-B3実装前チェックで確認したP2（B3 availability / startup testがtemporary SettingsStoreだけではrepository既定の`models` rootを隔離できない）を、B3 plan / Block Breakdownへ反映した。startup resolver / availability worker testではtemporaryな`whisper_models_dir`またはtemporary B2 store/rootを明示注入し、repository既定の`models` rootとroot runtime user dataを読まない契約を固定した。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。
- 続くMS24-B3実装前チェックで確認したP2（明示設定された不正rootの`StorageRootResolution`失敗時の既定root fallback・worker起動・root作成禁止契約の不足）とP3（関連回帰一覧から`test_whisper_timing.py` / `test_ms19_b3_textless_pipeline.py`が欠落）を、B3 plan / Block Breakdownへ反映した。解決失敗時はB2 failure code / detailをfailed stateへ投影し、selected / active identityを保持する。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。
- 2026-08-23にMS24-B3を実装した。`SettingsStore`のselected / active identity、`UiState`のWhisper selection state、RightPane専用Whisperモデルtab、startup projection、local-only availability scan worker、Busy / stale / shutdown guard、safe failure noticeを追加した。B3追加・関連の限定検証、full suite `846 passed, 2 skipped`、`compileall src tests`、`git diff --check`はprocess exit code `0`で完了した。ユーザーから、計画指定範囲の手動GUI確認が完了し問題なしとの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。実network、実model、実Whisper解析、実MMD確認は未実施で、B4、B5、MS26へ引き継ぐ。現在はworking tree状態で、stage / commit / push / merge / tag / releaseは未実施である。次工程はMS24-B4 Implementation Plan策定である。
- 2026-08-23にMS24-B4 Implementation PlanのP2/P3を補正した。B4へWhisper管理UIからのlocal-only保存先変更、B2 resolve・設定保存・new-root scan・no-fallback、management worker内のownership provider / B2 delete、controllerの再利用可能な`start_whisper_availability_rescan()`によるpost-operation scan、HTTP redirect全面拒否を追加した。B4 standaloneのblocked / test-only Delete seamと、B5連携後のproduction Delete成功を受け入れ境界として分離した。MS24-B4計画を索引へ追加し、Block BreakdownのB3 commit待ち表記を`a27a26f`へ同期した。production code、test code、GUI実装、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B4 planのfresh read-only checkである。
- 2026-08-23のMS24-B4再チェックで確認したP2（保存先変更時のpartial saveによる既存設定上書きリスク）とP3（B2内部scanとcontroller rescanの表現混在）を、B4 planへ反映した。保存先変更は現在の全設定を保持する安全なmerge保存とし、B2内部の対象model verification scanとcontrollerの再利用可能な`start_whisper_availability_rescan()`による全体projectionを分離した。Index、Roadmap、repo milestone、Version Control、B3 plan、Block Breakdownの現在地をB3コミット済み・B4 plan作成済み・fresh read-only check待ちへ同期した。production code、test code、GUI実装、依存関係、runtime user dataは変更していない。
- 2026-08-23のMS24-B4実装プラン再チェックで、現行`SettingsStore`の`system` theme非対応と、runtime INIの直接編集禁止・SettingsStore managed persistenceの境界不明確さをP2として確認した。また、promote後の全体availability projection表現の残存曖昧さとPython 3.13互換性gateの具体化不足をP3として確認した。B4 planへ`src/core/settings_store.py` / `tests/test_settings_store.py`のtheme round-trip・managed merge回帰、controllerの再利用可能rescan唯一入口、Python 3.13.xの実行ファイルpath・version・exit code記録を追加した。runtime user dataの直接編集・stageは禁止し、通常アプリのSettingsStore経由保存とtemporary test pathを分離した。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B4 planのfresh read-only pre-implementation checkである。

## 3.47 MS24-B4実装・ユーザー手動GUI確認記録

- 2026-08-24にMS24-B4をworking treeへ実装した。公式manifest URL限定downloader、exact size / Content-Length / redirect / stream failure / cancel / cleanup、専用model management worker、Whisper管理UI、保存先変更のSettingsStore managed merge、再利用可能な`start_whisper_availability_rescan()`、B5 permit未接続時のDelete blocked境界を追加した。
- B4専用・関連回帰、MS23回帰を含む全pytestは`860 passed, 2 skipped, 77 subtests passed`、`compileall src tests`と`git diff --check`はprocess exit code `0`だった。
- ユーザーからB4手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- Python 3.13.x互換性確認、B5 ownership provider接続後の実production Delete、実MMD確認、MS27 package / release readinessは未完了である。stage、commit、push、merge、tag、releaseは未実施である。

## 3.48 MS24-B5実装・ユーザー手動GUI確認記録

- 2026-08-25にMS24-B5をworking treeへ実装した。verified-local model request、single-active runtime、Apply / candidate commit-reject、TEXT + 音声・voice-onlyのmodel identity伝播、model-aware rollback、B5 production ownership permit、delete / storage root change / shutdown lifecycleを接続した。解析時の暗黙downloadを禁止し、word timestamp / segment fallbackとMS23の固定morph・Latin profile・preset・diagnostics・fingerprint契約を維持した。
- B5専用・関連回帰を含む全pytestは`872 passed, 2 skipped`、`compileall -q src`、`git diff --check`はprocess exit code `0`だった。
- ユーザーからB5手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- Python 3.13.x互換性確認、実MMD確認、MS27 package / release readinessは未確認または別工程である。stage、commit、push、merge、tag、releaseは未実施である。次工程はB5のPython 3.13.x compatibility gate確認後、MS24-B6 Implementation Planへ進む。

## 3.49 MS24-B6実装・ユーザー手動GUI確認記録

- 2026-08-26にMS24-B6を実装した。`WhisperDiagnosticsSummary`、selected / active / loaded / analysis identityの分離、package version / gate status、safe failure分類、projection generation、Info / report / RightPaneの同一snapshot投影、model-aware rollbackの診断連携を追加した。MS23の固定morph・Latin profile・preset・diagnostics・fingerprint契約、暗黙download禁止、依存値、runtime user data境界は維持した。
- B6専用・MS20 diagnostics / save policy回帰を含む全pytestは`881 passed, 2 skipped`、process exit code `0`だった。`compileall -q src tests`と`git diff --check`もprocess exit code `0`だった。
- ユーザーからB6手動GUI確認通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- Python 3.14.3をMS24の開発・受入環境として確認済みである。Python 3.11 / 3.12は今回の受入対象外で、互換性を検証済みとは扱わない。実MMDでのVMD / WAV読み込み・リップ同期はMS26、MS27 package / release readinessはMS27へ引き継ぐ。B6のproduction code・test code変更は`1f1aff2 Implement MS24-B6 diagnostics and recovery`としてcommit済みであり、B6のstage / commitは完了している。MS24-B7はintegration regression、static package audit、Python 3.14.3 development gateを実施済みで、Closeout判定は未実施である。

## 3. 正本文書

| 役割 | 文書 |
| --- | --- |
| MS20以降の番号、採否、依存関係 | [MS20 and Beyond Roadmap](MS20_and_Beyond_Roadmap.md) |
| pipelineデータ契約 | [Pipeline Data Contract Specification](Pipeline_Data_Contract_Specification.md) |
| GUI状態・theme契約 | [GUI State Theme Specification](GUI_State_Theme_Specification.md) |
| error / warning契約 | [Error Handling Specification](Error_Handling_Specification.md) |
| 各MSの実装指示 | `docs/Implementation_Plan/MSxx-Bx_Implementation_Plan.md`（各Block開始前に作成） |
| MS20 Block分割 | [MS20 Block Breakdown](Implementation_Plan/MS20_Block_Breakdown.md) |
| MS20-B1実装前計画 | [MS20-B1 Implementation Plan](Implementation_Plan/MS20-B1_Implementation_Plan.md) |
| MS20-B2実装計画 | [MS20-B2 Implementation Plan](Implementation_Plan/MS20-B2_Implementation_Plan.md) |
| MS20-B3実装計画 | [MS20-B3 Implementation Plan](Implementation_Plan/MS20-B3_Implementation_Plan.md) |
| MS20-B4実装計画 | [MS20-B4 Implementation Plan](Implementation_Plan/MS20-B4_Implementation_Plan.md) |
| MS20-B5実装計画 | [MS20-B5 Implementation Plan](Implementation_Plan/MS20-B5_Implementation_Plan.md) |
| MS20-B6実装計画 | [MS20-B6 Implementation Plan](Implementation_Plan/MS20-B6_Implementation_Plan.md) |
| MS20-B7実装計画 | [MS20-B7 Implementation Plan](Implementation_Plan/MS20-B7_Implementation_Plan.md) |
| MS20-B8 closeout計画 | [MS20-B8 Implementation Plan](Implementation_Plan/MS20-B8_Implementation_Plan.md) |
| MS21 Block分割 | [MS21 Block Breakdown](Implementation_Plan/MS21_Block_Breakdown.md) |
| MS21-B1実装前計画 | [MS21-B1 Implementation Plan](Implementation_Plan/MS21-B1_Implementation_Plan.md) |
| MS21-B2実装計画 | [MS21-B2 Implementation Plan](Implementation_Plan/MS21-B2_Implementation_Plan.md) |
| MS21-B3実装計画 | [MS21-B3 Implementation Plan](Implementation_Plan/MS21-B3_Implementation_Plan.md) |
| MS21-B4実装計画 | [MS21-B4 Implementation Plan](Implementation_Plan/MS21-B4_Implementation_Plan.md) |
| MS21-B5実装計画 | [MS21-B5 Implementation Plan](Implementation_Plan/MS21-B5_Implementation_Plan.md) |
| MS21-B5追加補正計画 | [MS21-B5 Explicit Event Crossfade Additional Fix Plan](Implementation_Plan/MS21-B5_Explicit_Event_Crossfade_Additional_Fix_Plan.md) |
| MS21-B6実装計画 | [MS21-B6 Implementation Plan](Implementation_Plan/MS21-B6_Implementation_Plan.md) |
| MS21-B7実装計画 | [MS21-B7 Implementation Plan](Implementation_Plan/MS21-B7_Implementation_Plan.md) |
| MS21-B7追加tab補正計画 | [MS21-B7 Selected Event Tab Auto-Switch Additional Fix Plan](Implementation_Plan/MS21-B7_Selected_Event_Tab_Auto_Switch_Additional_Fix_Plan.md) |
| MS21-B8 closeout計画 | [MS21-B8 Implementation Plan](Implementation_Plan/MS21-B8_Implementation_Plan.md) |
| MS22 Block分割 | [MS22 Block Breakdown](Implementation_Plan/MS22_Block_Breakdown.md) |
| MS22-B1実装前計画 | [MS22-B1 Implementation Plan](Implementation_Plan/MS22-B1_Implementation_Plan.md) |
| MS22-B2実装計画 | [MS22-B2 Implementation Plan](Implementation_Plan/MS22-B2_Implementation_Plan.md) |
| MS22-B3実装計画 | [MS22-B3 Implementation Plan](Implementation_Plan/MS22-B3_Implementation_Plan.md) |
| MS22-B4実装計画 | [MS22-B4 Implementation Plan](Implementation_Plan/MS22-B4_Implementation_Plan.md) |
| MS22-B5実装計画 | [MS22-B5 Implementation Plan](Implementation_Plan/MS22-B5_Implementation_Plan.md) |
| MS22-B6実装計画 | [MS22-B6 Implementation Plan](Implementation_Plan/MS22-B6_Implementation_Plan.md) |
| MS22-B7 closeout計画 | [MS22-B7 Implementation Plan](Implementation_Plan/MS22-B7_Implementation_Plan.md) |
| MS23 Block分割 | [MS23 Block Breakdown](Implementation_Plan/MS23_Block_Breakdown.md) |
| MS23-B1実装前計画 | [MS23-B1 Implementation Plan](Implementation_Plan/MS23-B1_Implementation_Plan.md) |
| MS23-B2実装計画 | [MS23-B2 Implementation Plan](Implementation_Plan/MS23-B2_Implementation_Plan.md) |
| MS23-B3実装計画 | [MS23-B3 Implementation Plan](Implementation_Plan/MS23-B3_Implementation_Plan.md) |
| MS23-B4実装計画 | [MS23-B4 Implementation Plan](Implementation_Plan/MS23-B4_Implementation_Plan.md) |
| MS23-B4B修正用実装計画 | [MS23-B4B Implementation Plan](Implementation_Plan/MS23-B4B_Implementation_Plan.md) |
| MS23-B5実装計画 | [MS23-B5 Implementation Plan](Implementation_Plan/MS23-B5_Implementation_Plan.md) |
| MS23-B6実装計画 | [MS23-B6 Implementation Plan](Implementation_Plan/MS23-B6_Implementation_Plan.md) |
| MS23-B7 closeout計画 | [MS23-B7 Implementation Plan](Implementation_Plan/MS23-B7_Implementation_Plan.md) |
| MS24 Block分割 | [MS24 Block Breakdown](Implementation_Plan/MS24_Block_Breakdown.md) |
| MS24-B1実装計画 | [MS24-B1 Implementation Plan](Implementation_Plan/MS24-B1_Implementation_Plan.md) |
| MS24-B2実装計画 | [MS24-B2 Implementation Plan](Implementation_Plan/MS24-B2_Implementation_Plan.md) |
| MS24-B3実装計画 | [MS24-B3 Implementation Plan](Implementation_Plan/MS24-B3_Implementation_Plan.md) |
| MS24-B4実装計画 | [MS24-B4 Implementation Plan](Implementation_Plan/MS24-B4_Implementation_Plan.md) |
| MS24-B5実装計画 | [MS24-B5 Implementation Plan](Implementation_Plan/MS24-B5_Implementation_Plan.md) |
| MS24-B6実装計画 | [MS24-B6 Implementation Plan](Implementation_Plan/MS24-B6_Implementation_Plan.md) |
| MS24-B7実装計画 | [MS24-B7 Implementation Plan](Implementation_Plan/MS24-B7_Implementation_Plan.md) |
| MS25 Block分割 | [MS25 Block Breakdown](Implementation_Plan/MS25_Block_Breakdown.md) |
| MS25-B1実装前計画 | [MS25-B1 Implementation Plan](Implementation_Plan/MS25-B1_Implementation_Plan.md) |
| MS25-B2実装計画 | [MS25-B2 Implementation Plan](Implementation_Plan/MS25-B2_Implementation_Plan.md) |
| MS25-B3実装計画 | [MS25-B3 Implementation Plan](Implementation_Plan/MS25-B3_Implementation_Plan.md) |
| MS25-B4実装計画 | [MS25-B4 Implementation Plan](Implementation_Plan/MS25-B4_Implementation_Plan.md) |
| MS25-B5実装計画 | [MS25-B5 Implementation Plan](Implementation_Plan/MS25-B5_Implementation_Plan.md) |
| MS25-B6実装計画 | [MS25-B6 Implementation Plan](Implementation_Plan/MS25-B6_Implementation_Plan.md) |
| MS25-B7実装計画 | [MS25-B7 Implementation Plan](Implementation_Plan/MS25-B7_Implementation_Plan.md) |
| MS26 Block分割 | [MS26 Block Breakdown](Implementation_Plan/MS26_Block_Breakdown.md) |
| MS26-B1実装計画 | [MS26-B1 Implementation Plan](Implementation_Plan/MS26-B1_Implementation_Plan.md) |
| MS26-B3実装計画 | [MS26-B3 Implementation Plan](Implementation_Plan/MS26-B3_Implementation_Plan.md) |
| MS28-B1修正実装計画 | [MS28-B1 Implementation Plan](Implementation_Plan/MS28-B1_Implementation_Plan.md) |
| MS28-B2修正実装計画 | [MS28-B2 Implementation Plan](Implementation_Plan/MS28-B2_Implementation_Plan.md) |
| MS28-B3デバッグ機構実装計画 | [MS28-B3 Implementation Plan](Implementation_Plan/MS28-B3_Implementation_Plan.md) |
| MS28-B4無音handoff契約修正計画 | [MS28-B4 Implementation Plan](Implementation_Plan/MS28-B4_Implementation_Plan.md) |
| MS28-B5 Help/About実装計画 | [MS28-B5 Implementation Plan](Implementation_Plan/MS28-B5_Implementation_Plan.md) |

`AGENTS.md` の固定モーフ契約とネットワーク禁止契約は現行実装に対して有効である。MS23・MS24の実装開始時に、承認済み計画契約と実装範囲を照合して必要箇所だけを更新する。

## 3.1 MS20-B1 実施記録

- 2026-07-14に、現行コード・正本文書・指定回帰テストを読み取り照合した。
- 診断参照元、severity正規化、diagnostic code、canonical writer fingerprint、report契約、failure保持のBlock所有権を `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md` に固定した。
- production code、GUI、テスト、依存関係、build設定は変更していない。

## 3.2 MS20-B2 実施記録

- 2026-07-15に `b6f4254` でUI非依存diagnostics core、canonical fingerprint、writer timing plan共有helper、core testを実装した。
- B2単体12件、非正duration回帰1件、限定回帰24件はpass表示・終了コード0だった。
- 全体380件はpass表示まで完走し、既知wx終了処理由来のprocess exit code 1を別記録した。
- GUI、UiState、Warning、save policy、report、依存関係、packageは変更していない。
- B3はGUI adapterとRightPane Info表示を所有し、failure保持、Warning、save policy、live playback、reportは先行実装しない。

## 3.3 MS20-B3 実装前チェック記録

- B3実装前チェックでは、`clear_info()` 契約、analysis error / cancelのInfo回帰、parameter変更時の二重Preview更新を補正した。2026-07-16の再チェックでは指定限定回帰56件がpass表示、failure / error表示なし、process exit code 1だった。MS14-B6 closeout単独3件とRightPane単独2件はpass表示・終了コード0だった。
- pre-implementation check時点ではproduction code、GUI、テストコード、依存関係、packageを変更していない。

## 3.4 MS20-B3 実施記録

- 2026-07-16に、wx非依存GUI adapter、RightPane Infoの縦scroll表示、MainFrame同期、解析中maskを実装した。
- InfoはB2 snapshotから入力・解析・生成・保存可否の4セクションを固定順で表示し、RightPane自身では診断値を再計算しない。
- B3 adapter単体12件、B3 RightPaneとMS16 RightPane回帰16件、workspace reset回帰8件はpass表示・終了コード0だった。
- 指定限定回帰56件と全体406件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- 2026-07-16にユーザー手動GUI確認10項目がすべて通過し、問題なしと報告された。同日の微修正で「再解析が必要」の文字列だけをボールド＋theme別オレンジ系文字色にし、微修正後のユーザーチェックも通過・問題なしと報告された。
- Warning、failure保持、save policy、live playback、report、依存関係、packageは変更していない。live playbackはB4へ引き継いだ。

## 3.5 MS20-B4 計画・実施記録

- 2026-07-16に、B3 live playback引き継ぎ、現行MCI timer、UiState、MainFrame cursor更新、timing plan intervalを照合し、B4 Implementation Planを作成した。
- B4はB3静的Infoと分離した `[再生]` セクションを所有し、秒、30fps表示frame、現在母音だけを軽量更新する。
- timer callbackではB2 snapshot、fingerprint、B3 formatterを再生成しない。Pause、MCI、Preview cursor、Warning、save policy、reportは変更しない。
- 同日にpre-implementation checkを実施し、P1なし、P2 1件、P3 2件を検出した。B3の空表示契約との衝突を、RightPane単体構築／`clear_info()` 直後はstatic / live双方を空にし、MainFrame初回同期でdefault `[再生]` を表示する契約へ修正した。非有限位置で0秒eventを誤表示しない規則と、停止後の遅延位置callback回帰testも追加した。
- 現行前提の限定回帰は34件と21件の2段階で全件pass表示、process exit code 0だった。
- 同日、wx非依存playback context、RightPaneの独立 `[再生]` label、MainFrame軽量同期を実装した。半開区間、gap、overlap、0長event、非有限位置、lifecycle、停止後遅延callback、theme追従を自動testへ固定した。
- B4新規24件、RightPane / playback / Preview回帰28件、diagnostics / state回帰29件、viewport回帰8件は全件pass表示・終了コード0だった。全体430件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- 2026-07-16にユーザーからGUI確認完了・問題なしと報告された。B4は実装、自動検証、ユーザーGUI確認まで完了した。

## 3.6 MS20-B5 計画・実施記録

- 2026-07-16に、B2 diagnostics snapshot / fingerprint、B3 / B4 RightPane、UiState、analysis callback、VMD保存action stateとcontroller guardを照合し、B5 Implementation Planを作成した。
- B5はWarningタブへ `INFO / WARNING / ERROR` の全診断を表示し、ERROR時の保存禁止、WARNING時の同一fingerprint一回確認、解析failure保持を接続する。
- save policyはUI表示文字列から導出せず、最新 `OutputDiagnosticsSnapshot` をbutton / menuとcontroller guardの共通正本にする。
- VMD保存失敗では解析結果と確認済みfingerprintを保持し、同一状態の再試行を可能にする。
- 初回実装前チェックでP1なし、P2 2件、P3 1件を検出し、input mode再判定順序、B5基本clearとB7横断監査の責務境界、Block Breakdownの成果物候補一覧を補正した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。限定回帰24件、47件、28件＋subtest 7件はpass表示・終了コード0だった。
- 実装前チェック完了時点ではproduction codeとtest codeは未変更・未実装だった。
- 2026-07-17にworkspace diagnostics state、analysis failure保持、snapshot共有、Warning全severity表示、ERROR保存禁止、WARNING同一fingerprint一回確認を実装した。
- B5 / theme限定17件、diagnostics / RightPane限定64件、state / save / failure限定35件＋subtest 7件、pipeline / VMD 12件はpass表示・終了コード0だった。全体442件＋subtest 7件はpass表示、failure / error表示なし、既知wx終了処理由来の終了コード1だった。
- 2026-07-17にユーザーGUI確認13項目がすべて通過し、問題なしと報告された。B5はproduction実装、自動検証、ユーザーGUI確認まで完了した。

## 3.7 MS20-B6 計画・実装記録

- 2026-07-17にB1 report契約、B2 snapshot、B3 / B5表示・保存policy、現行File menu、AppController、atomic保存既存パターンを照合し、B6 Implementation Planを作成した。
- B6は同一 `OutputDiagnosticsSnapshot` から固定section順のplain-text reportを生成し、`ファイル > 診断レポート保存...` から `<base>_report.txt` を保存する。
- reportはtimezone付きGenerated At、LF、UTF-8 BOMなし、単一空値表現、全diagnostic itemを持つ。RightPane表示文字列をreport入力にしない。
- report保存はsource audio pathだけを前提とし、VMD保存不可のERROR snapshotでも許可する。
- same-directory temporary file、byte検証、atomic replace、failure cleanupにより既存正常fileを保護する。
- 初回実装前チェックでP1なし、P2 2件、P3なしを検出した。元source audio pathとsnapshot正規化pathの責務分離、共有adapter resolver、Windows temporary handle close順序をplanへ補正した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。MS20 diagnostics回帰50件、state / export / reset回帰28件＋subtest 7件、既存output dialog回帰6件、pipeline / VMD回帰12件はpass表示・終了コード0だった。
- 計画・実装前チェック時点ではproduction code、GUI、test code、dependency、build設定を変更していなかった。
- 2026-07-18にUI非依存diagnostic report formatter / atomic writer、共有source audio path resolver、File menu、report固有save guard、dialog / controller flowを実装した。
- B6 core 13件、B6 GUI flow 10件、MS20 diagnostics回帰50件、state / export / reset回帰28件＋subtest 7件、既存output dialog回帰6件、pipeline / VMD回帰12件はpass表示・終了コード0だった。
- 全体465件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。compileallと `git diff --check` は終了コード0だった。
- dependency、package、license、Qt、network、固定モーフは変更していない。
- 2026-07-18にユーザーから、手動GUI確認14項目はすべて通過し、問題なしと報告された。B6はproduction実装、自動検証、ユーザーGUI確認まで完了した。

## 3.8 MS20-B7 計画・実装記録

- 2026-07-18にB1のB7所有権、B5 / B6 diagnostics state、UiState、MainFrame、AppController、analysis / audio job ID、既存回帰、README、配布用readme、3正本仕様を照合し、B7 Implementation Planを作成した。
- B7はinput / parameter / analysis / cancel / late callback / reset / save failureのclear・rebuild・retain規則を横断監査し、欠落だけを限定補修する。
- parameter変更時のfailure snapshot clearと、既存core `analysis_cancelled` INFOのUiState / adapter接続を補修候補として固定した。
- README、`readme_mmdautolip.txt`、Pipeline / GUI / Error仕様をMS20-B6完了状態へ同期し、B8 closeout文書は先行更新しない。
- 計画作成baselineのstate / analysis / late / failure / reset / B5 / B6関連48件＋subtest 7件はpass表示・終了コード0だった。
- 初回実装前チェックでP1なし、P2 2件、P3 1件を検出した。input failureをdialog cancel、TEXT commit前失敗、音声選択確定後失敗へ分離し、analysis cancelをcurrent jobのterminal callbackでだけ確定する契約へ補正した。audio worker state / Busy actionの既存testも指定回帰へ追加した。
- 補正後の再チェックではP1 / P2 / P3の残存なしと判定した。P3で指定回帰へ追加したaudio worker state / Busy action 3件はpass表示・process exit code 0だった。補正後のstate / analysis / late / failure / reset指定回帰は48件＋subtest 7件がpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- 2026-07-19の再チェックでP1なし、P2 2件、P3 1件を検出し、audio正常cancel terminalとlate / duplicate callbackの分離、analysis cancel後の非Busy Statusを計画へ補正した。補正後はP1 / P2 / P3の残存なしと判定した。
- 同日、`UiState.analysis_cancelled`、adapter接続、analysis cancel terminal Status、parameter変更時のdiagnostics clear、audio cancelled callback guardを実装した。
- B7専用11件、MS20 diagnostics 97件、pipeline / VMD 12件はpass表示・終了コード0だった。
- state / analysis / late / failure / reset 48件＋subtest 7件と全体476件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。compileallは終了コード0だった。
- README、配布用readme、Pipeline / GUI / Error仕様を同期した。dependency、package、license、Qt、network、固定モーフは変更していない。
- 2026-07-19にユーザーから、手動GUI確認は通過し問題なしと報告された。
- B7はproduction実装、自動検証、ユーザー手動GUI確認まで完了した。B8 closeoutは未実施である。

## 3.9 MS20-B8 計画・実施記録

- 2026-07-19にB1からB7の計画・実装・自動検証・ユーザー確認、MS20受け入れ条件、現行code / test / docs、dependency / package / license差分を照合し、B8 Implementation Planを作成した。
- B8は新機能Blockではなく、code、test、user、docsの4系統を総合監査し、findingsをP1 / P2 / P3へ分類してMS20 CloseoutをA / B / Cで判定する。
- B8の主変更対象はplan、Block Breakdown、Index、Roadmap、repo milestone、Version Controlであり、production code、test code、dependency、build設定は原則変更しない。
- B7完了baselineは全体476件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1である。B8でMS20固有、関連回帰、全体testを再実行し、表示結果とexit codeを分けて記録する。
- B3からB7のユーザーGUI確認記録は、B8で機能変更や証拠不足がなければ再利用する。
- package、release、merge、push、tag、MS21実装はB8対象外である。
- 計画作成時点でproduction codeとtest codeは変更していない。次はB8 pre-implementation checkである。
- 2026-07-20の実装前チェックではP1 / P2なし、P3 1件を検出した。P3はBlock Breakdownの古い成果物候補表記であり、B8文書同期で解消した。
- MS20固有108件とpipeline / VMD 12件はpass表示・process exit code 0だった。
- state / GUI / worker / voice_only回帰は65件＋subtest 7件、全体回帰は476件がpass表示まで完走した。failure / error / fatal stack traceはなく、process exit codeはB7 baselineと同じ1だった。
- `compileall src tests` と `git diff --check` はprocess exit code 0だった。
- B3からB7の通過済みユーザーGUI確認を再利用した。Closeout監査後、2026-07-20にユーザーからB8チェック通過・問題なしと報告された。
- dependency、package、build、license、固定モーフ、network、Qtに変更はない。
- 残存findingはP1 / P2 / P3なし。自動検証とユーザー確認が揃い、MS20 CloseoutはA判定で完了した。
- 2026-07-20に `feature/MS20-implementation` を `main` へfast-forward mergeし、`origin/main` へpushした。`main / origin/main` は `6cd8233` で同期している。tag、release、branch削除は未実施である。

## 3.10 MS21 Block Breakdown作成記録

- 2026-07-20に同期済み `main / origin/main` の `6cd8233` から `feature/MS21-implementation` を作成した。
- MS21をB1契約固定、B2 adjustment core、B3 Preview selection、B4 RightPane editor、B5 VMD / diagnostics統合、B6 Undo / Redo、B7 state / regression / docs、B8 Closeoutの8 Blockへ分割した。
- base timing planを直接変更せず、user adjustment layerと共通resolverをPreview / writerの正本にする。
- multi-source grouped shape、save-state fingerprint、WARNING確認、diagnostic report、workspace lifecycleをMS21の横断契約へ含めた。
- selection foundation 4件、Preview / writer / diagnostics回帰71件はpass表示・process exit code 0だった。state / reset / analysis / playback回帰32件はpass表示、failure / errorなし、process exit code 1だった。
- production code、test code、dependency、build設定は変更していない。次はMS21-B1 Implementation Plan策定である。

## 3.11 MS21-B1 Implementation Plan作成記録

- 2026-07-20にMS21-B1 Adjustment Contract / Current-State Pre-checkの実装計画を作成した。
- plan-local event indexとbase plan identity、base / adjustment / effective境界、grouping前後のresolver順序、history transaction、diagnostics handoffをB1の調査・契約固定対象とした。
- ユーザー判断により、slopeは閉口途中の強度比 `0.0〜1.0`、既定 `0.7` とした。
- grouped shapeでは開口量・開始・終了を各base eventで編集可能とし、hold / softness / slopeはgroup末尾eventだけを編集可能とした。
- 解析開始時は旧編集をrollback候補として保持し、current job成功時に破棄、failure / cancel時は旧base再利用可能な場合だけ復元する。
- B1はproduction code、GUI、test code、dependency、build設定を変更しない。計画作成時点の次工程はMS21-B1 pre-implementation checkだった。
- 計画作成baselineは4件、52件、24件、15件の全コマンドがpass表示・process exit code 0だった。

## 3.12 MS21-B1 pre-implementation review修正記録

- 2026-07-20の初回レビューでP1なし、P2 4件、P3 2件を検出し、MS21-B1 Implementation PlanとBlock Breakdownを補正した。
- P2は、real base eventとnegative synthetic shape tokenの混同、automatic candidateとユーザー補正の優先順位、Preview / writer共通resolverのB2所有不足、midpointなしslopeのlatent overrideを解消した。
- P3は、既存render-only selection setterの範囲外index許容とB3 canonical commit validationを分離し、hold / softnessを現行GUIと同じ0から100の整数範囲へ固定した。
- B2がshape provenanceとgroup-aware shared resolverを所有し、B3はhit-test、B4はlive Preview adapter、B5はwriter / diagnostics adapterを所有する。
- 修正後再チェックではP1 / P2 / P3の残存なしと判定した。4件、52件、24件、15件の限定回帰はすべてpass表示、各process exit code 0だった。`git diff --check` もprocess exit code 0だった。
- production code、GUI、test code、dependency、build設定は変更していない。次はMS21-B1 pre-implementation checkである。

## 3.13 MS21-B1実施記録

- 2026-07-21にMS21-B1 Adjustment Contract / Current-State Pre-checkを実施した。production code、GUI、test code、dependency、build設定は変更していない。
- pre-implementation checkのP2 2件とP3 1件を解消した。observationsなしのevent identity、present時の対応検証、commit済み計画基準を固定した。
- canonical編集単位を30fps整数frame、real event intervalの上限をsource duration frameとし、peak overrideをanalysis upper limitから分離した。
- B2はwriter非依存の `EffectiveShapePlan`、shape provenance、candidate再評価、group-aware shared resolverを所有し、writer / Previewは同じcore resultを消費する。
- analysis failure時の条件付きrollbackを現行正本仕様からの意図的なMS21将来変更とした。failure時はERRORと保存禁止を維持し、cancel時はcancel INFO付きfingerprintを再構築する。正本仕様同期はB7の責務とした。
- 文書補正後の限定回帰は指定95件と補完72件、合計167件がすべてpass表示、各process exit code 0だった。`git diff --check` もprocess exit code 0だった。
- B1実施後の残存P1 / P2 / P3はなし。次はMS21-B2 Implementation Plan策定である。

## 3.14 MS21-B2 Implementation Plan作成記録

- 2026-07-21にMS21-B2 Adjustment Core / Shared Shape Resolverの実装計画を作成した。
- B2はimmutable adjustment model、base identity、canonical snapshot、real / synthetic provenance、candidate再評価、group-aware `EffectiveShapePlan` をUI非依存coreへ実装する。
- 現行Previewがwriter private helperを直接importしているため、shape preparationをcoreへ抽出し、Preview / writerが同じeffective planをconsumeする一方向依存へ移行する。
- 現行GUI PreviewとVMD保存のadjustment付き導線、UiState、RightPane、Undo / Redo、fingerprint統合はB3以降の責務として先行実装しない。
- 計画作成baselineはPreview / writer / pipeline / diagnostics関連152件がすべてpass表示、各process exit code 0だった。
- plan作成時点でproduction code、GUI、test code、dependency、build設定は未変更であり、次工程はMS21-B2 planの実装状態整合チェックだった。

## 3.15 MS21-B2 plan整合レビュー修正記録

- 2026-07-21にMS21-B2 planを現行package import順、writer validation、tail計算、shape定数の利用箇所へ照合した。P1なし、P2 4件、P3 1件を検出し、計画文書とBlock Breakdownを補正した。
- writerからcoreへのmodule-level direct import案を廃止し、`src.vmd_writer` / `writer.py` 初期化後に専用 `effective_shape_adapter.py` がcoreへ委譲する境界と、fresh-process import smokeを固定した。adapterは `src/vmd_writer/__init__.py` から初期化時exportせず、明示module pathで読む。両packageの `__init__.py` はexport変更対象ではなく読み取り確認対象である。
- MS21 adjustment model / `ShapeParameters` のhold / softness 0から100 rejectと、現行legacy writer / Previewの非負値・100超受理を分離した。動的確認では101 / 250を受理し、process exit code 0だった。
- source duration上限はreal / effective event intervalに限定した。最終shapeのtail control pointはdurationを超過可能とし、次shapeがある場合だけ既存clampを維持する。動的確認例はreal end 10、hold 3、softness 2で `(12, 14, 15)`、process exit code 0だった。
- candidate / grouping等の内部定数はcoreへ移し、既存callerが参照する `VMD_FPS`、`SUPPORTED_MORPHS`、`MORPH_FRAME_OPEN_EPSILON` はwriter互換名を維持する。循環回避のためcore側にも置く3値はdrift-guard testで一致を固定する。
- production code、GUI、test code、dependency、build設定は変更していない。次は補正済みB2 planの再チェックである。

## 3.16 MS21-B2 pre-implementation check修正記録

- 2026-07-22にB2 Implementation Planを現行code、既存testのimport方式、setuptools package設定、candidate observation参照処理へ再照合した。P1なし、P2 2件、P3 1件を検出し、B2 planとBlock Breakdownを補正した。
- P2は、`src.vmd_writer.writer` とtop-level `vmd_writer.writer` の二重loadとmixed import互換、およびcandidate observationの4種の参照indexに対するlookup前validation不足である。
- 新規public APIは `src.core.*` に固定し、legacy top-level writer helperはpackage-relative adapterとstructural boundaryで維持する。src / top-level / mixed importをfresh processで検証する。
- candidate参照indexはbool拒否、非負int、timeline範囲内、span包含、previous / next bracketing順序を必須とし、不正値はlookup前に `AdjustmentContractError` で拒否する。
- P3として、B2回帰対象に列挙済みだったselection foundation 4件を実行コマンドへ追加した。
- 補正後再チェックでは残存P1 / P2 / P3なし。関連回帰156件はすべてpassし、4コマンドともprocess exit code 0だった。`src.*` / top-level import smokeも各process exit code 0、両writer moduleと `VowelTimelinePoint` が別objectとなる現行事実も再確認した。`git diff --check` はprocess exit code 0だった。
- production code、GUI、test code、dependency、build設定は変更していない。B2 planは実装着手可能であり、次はB2実装である。

## 3.17 MS21-B2実装記録

- 2026-07-22にimmutable adjustment model、canonical base identity / snapshot、strict resolver、candidate handoff、real / synthetic provenance、group-aware effective shape、tail update transactionをcoreへ実装した。
- Preview / writerは同じ `EffectiveShapePlan` を変換するpure adapterを持つ。既存Preview互換は専用facadeへ隔離し、`preview_transform.py` からwriter private helperの直接importを除去した。
- B2専用35件と指定回帰156件はすべてpass表示、各process exit code 0。全体は511件と7 subtestsがpass表示、failure / error表示なし、process exit code 1。`compileall` はprocess exit code 0だった。
- 2026-07-22にユーザーから既存GUI回帰確認は通過・問題なしと報告された。event選択・個別補正・RightPane編集・Undo / RedoはB2で未接続のため、この確認結果には含めない。
- GUI state、選択、編集control、保存、history、fingerprintは未接続である。次はMS21-B3 Implementation Plan策定である。

## 3.18 MS21-B3 Implementation Plan作成記録

- 2026-07-22にMS21-B3 Preview Hit-Test / Event Selectionの実装計画を作成した。
- B2のreal base provenanceとeffective event rangeを使い、vowel lane、event range、base peak距離、base index tie-breakによるUI非依存hit-testを固定した。
- click / pan dragは4 DIP thresholdで分離し、mouse capture lost、Busy、stale base identity、invalid / synthetic indexではselectionを変更しない。
- existing permissive selection setterは維持し、mouse clickだけをstrict canonical commitへ接続する。grouped shapeは全体highlightとしながら、個別real base event identityをUiStateとRightPane summaryへ伝搬する。
- B3ではbase-only full resolverをGUI Previewへ接続するが、adjustment state、RightPane編集control、VMD保存、fingerprint、historyは先行実装しない。
- 計画作成baselineはselection foundation 4件、Preview / viewport回帰16件、B2 adapter 6件がすべてpass表示・各process exit code 0だった。次はB3 planの実装状態整合チェックである。

## 3.19 MS21-B3 plan整合レビュー修正記録

- 2026-07-22にB3 planを現行 `BasePlanIdentity`、grouped Preview metadata、selection setter、MainFrame / RightPane testへ照合した。P1なし、P2 3件、P3 2件を検出し、B3 planとBlock Breakdownを補正した。
- base identityはshape parameterやadjustmentによる描画差を識別しないため、panel-local render revisionを分離した。selection requestはmouse-down時のbase identityとrender revisionを保持し、commit時に両方を再照合する。
- event hit regionへevent固有のbase peak frameとpeak valueを追加し、grouped segmentの先頭indexや最大intensityをselected event summaryへ流用しない。
- existing permissive setterは未知index許容を維持する一方、canonical base identity digestをclearする。strict commitだけがindexとdigestを同時更新する。
- baseline commandのrepository-local path表記を修正し、RightPane Info回帰を限定対象へ追加した。
- 修正後再チェックでは残存P1 / P2 / P3なし。selection 4件、Preview / viewport 16件、B2 adapter 6件、RightPane / playback / reset / late callback 50件はすべてpass表示・各process exit code 0、`git diff --check` もprocess exit code 0だった。次はB3 pre-implementation checkである。

## 3.20 MS21-B3実装・ユーザーGUI確認記録

- 2026-07-23にB2 full resolverをGUI Previewへ接続し、UI非依存hit-test、strict canonical selection commit、grouped event summary、4 DIP click / drag分離、stale base identity / render revision拒否、selection lifecycleを実装した。
- 手動確認中にselection outline描画で未定義 `palette` を参照する `NameError` を検出し、current theme palette取得とrenderer回帰testを追加して修正した。
- 修正後はB3新規22件、Preview / selection / viewport回帰50件、全体533件と7 subtestsがすべてpass表示、各process exit code 0だった。`compileall src tests` と `git diff --check` もprocess exit code 0だった。
- 同日に修正後のユーザーGUI確認は通過・問題なしと報告された。開口維持・閉口スムーズ変更による「再解析が必要」表示は現行global parameter invalidation契約どおりで、B3のselection不具合ではないことを確認した。
- B3はproduction実装、自動検証、ユーザーGUI確認まで完了した。event補正control、adjustment付きlive Preview、VMD保存 / diagnostics統合、Undo / RedoはB4以降の責務である。次はMS21-B4 Implementation Plan策定である。

## 3.21 MS21-B4 Implementation Plan作成記録

- 2026-07-23にMS21-B4 RightPane Event Editor / Live Previewの実装計画を作成した。
- B4は選択eventのbase / adjustment / effective表示、peak / start / end / hold / softness / slope編集、selected reset、B2 shared resolverによるlive Previewを所有する。
- `AdjustmentLayerSnapshot` をUiStateのcanonical編集状態とし、RightPane control値やPreviewDataを正本にしない。group tailとactual slope midpointの可否はcurrent effective resultから導出する。
- 現行B2 DTOに不足するbase event列とresolved tail metadataはadditiveに公開し、RightPaneでcandidate / grouping / tail計算を再実装しない。
- B5でadjusted writer / fingerprint統合が完了するまで、non-empty adjustmentを一時diagnostic ERRORとして単一snapshotへ接続し、Info / Warning / report / bottom Status / button / menu / controllerを同じsaveabilityでfail closedにする。Undo / Redo、adjustment値のfingerprint / report統合、failure rollback完成は先行実装しない。
- 計画作成baselineはB2 core 29件、B3 selection 22件、RightPane / Info / theme 21件の計72件がpass表示・各process exit code 0だった。
- 実装状態整合レビューではP1なし、P2 2件、P3 2件を検出した。保存可否の単一diagnostics snapshot統合、current job cancel時のadjustment / selection保持、selected reset後の保存復帰条件、wx commit event重複抑止をplanへ反映した。レビュー時のB2 / B3 / RightPane / save / lifecycle回帰は29件、22件、28件、19件、15件がpass表示・各process exit code 0だった。この時点の次工程をB4 pre-implementation checkとした。
- 2026-07-24のpre-implementation checkではP1なし、P2 2件、P3 2件を検出した。一時diagnostic ERRORも既存ERROR規則に従ってcancel INFOを抑止する契約へ統一し、cancel Statusと開始前state保持は維持した。bottom Statusも同じdiagnostics snapshotから導出して保存禁止中の「VMD出力可能」を除く。Enter commit対象controlへ `wx.TE_PROCESS_ENTER` を明記し、actual midpoint消失時のslope cleanupをtail cleanupと別result fieldへ記録して通知する契約を追加した。
- pre-implementation checkでは関連168件がpass表示となり、成功した各test processのexit codeは0だった。RightPane / Info / theme群の初回実行だけ環境側のPowerShell runtime読込失敗でtest開始前にexit code `-2147450726` となり、同一commandの再実行では21件pass・exit code 0だった。P2 / P3はplanとrouting文書へ反映し、その後の再チェックを経てB4実装へ進んだ。
- 2026-07-24にB4 production実装と一時修正を実施した。structured editor、canonical adjustment commit、live Preview、selected reset、一時保存禁止diagnosticsに加え、次の口形によるhold / softness反映制限とslope非作用を説明する効果noticeを追加した。操作noticeと効果noticeは別control・別入力チャネルとし、headerだけをbold、theme別attention色で表示する。
- B4限定16件、B2 resolver関連35件、B3 selection / Preview関連22件、RightPane / theme関連21件、diagnostics関連37件、pipeline / VMD関連12件はpass表示・各process exit code 0だった。全体550件と7 subtestsもpass表示・process exit code 0、`compileall src tests` もprocess exit code 0だった。同日にユーザーGUI再確認が通過し、問題なしと報告された。B4は実装、自動検証、ユーザーGUI確認まで完了し、次はMS21-B5 Implementation Plan策定である。

## 3.22 MS21-B5 Implementation Plan作成記録

- 2026-07-25にMS21-B5 VMD Save / Diagnostics Integrationの実装計画を作成した。
- B2 `EffectiveShapePlan` をPreview、VMD writer、diagnosticsの共通派生元とし、save要求内では同じplan instanceをsnapshotとmode別pipelineへ渡す。
- prepared morph frame writer、TEXTあり / voice-onlyのeffective plan接続、`ms21-effective-output-v1` fingerprint、effective per-shape tail、固定Adjustment report sectionをB5範囲とした。
- raw adjustment、base identity、selection、history、playbackはfingerprintへ含めず、effective outputが同じeditではWARNING確認を再利用し、output変更時だけ再確認する。
- B4の一時 `adjustment_vmd_integration_pending` ERRORとB5待ち表示を、adjusted writer統合と同時に撤去する。
- 計画作成baselineのB2 / B4 / pipeline / VMD / MS20 diagnostics / report関連134件はpass表示、process exit code 0だった。production code、test code、dependency、build設定は変更していない。次はB5 planの実装状態整合チェックである。
- 2026-07-26の実装状態整合レビューではP1なし、P2 2件、P3 2件を検出した。B5とB7の文書同期責務重複を解消し、README、配布用readme、Pipeline / GUI / Error仕様をB7へ戻した。
- effective writer inputを `not_applicable / ready / invalid` の3状態へ固定し、通常の未解析状態を追加ERRORにせず、保存対象planのresolver / adapter失敗だけを `effective_writer_input_unavailable` ERRORとfingerprintなしでfail closedにする。
- MS14 / MS19の直接保存回帰を追加し、adjustment summaryのentry count、optional effective count、`N/A` 表現を固定した。レビュー時の関連134件はpass表示・process exit code 0、`git diff --check` もprocess exit code 0だった。P2 / P3解消後の次工程はplan再チェックである。

## 3.23 MS21-B5実装・Explicit Event Crossfade追加補正記録

- 2026-07-26にprepared writer、TEXTあり / voice-only保存、effective output fingerprint、
  Adjustment report sectionを実装し、B4の一時保存禁止diagnosticを撤去した。
- B5本体の自動検証とユーザーGUI確認は通過・問題なしと報告された。
- 追加要求として、自動解析結果には一律適用せず、group末尾eventのpositive end offset、
  event hold、event softnessだけで直後の非0・異母音shapeとのcrossfadeを許可した。
- zero-only group保持、同母音での探索停止、third active group上限、範囲外offset拒否、
  comparison outputとの差分帰属をcore契約にした。
- overlap内のtarget明示control pointが0.95以上の場合、値をclipせずRightPaneへ
  非モーダルnoticeを表示する。diagnostics、Warning tab、保存可否には影響させない。
- 新規core / editor 17件を含む限定回帰はすべてpass表示・各process exit code 0だった。
  全体は576件と7 subtestsがpass表示したが、pytest終了後のprocess exit codeは1だった。
  `compileall src tests` はprocess exit code 0である。
- 2026-07-26に追加補正のユーザーGUI確認は通過・問題なしと報告された。
  B5は追加補正を含め完了した。

## 3.24 MS21-B6 Implementation Plan作成記録

- 2026-07-26にMS21-B6 In-Memory Undo / Redoの実装計画を作成した。
- canonical adjustment snapshot全体のbefore / afterをtransactionとして保持し、
  history currentを唯一のcurrent snapshot所有者にする。
- undo可能transactionは最大50件とし、canonical no-opは履歴を増やさずredoを保持する。
  requested snapshotが変わるoutput-equivalent editは履歴へ記録する。
- 同一event・field・明示gesture token内だけをcoalesceし、mouse / key release、Enter、
  focus loss、selection変更、reset、Undo / Redoを境界にする。mouse wheelとtokenなし
  spinはdiscrete fallbackとし、stale token boundaryはstateを変更しない。timerは使用しない。
- Edit menu、Ctrl+Z / Ctrl+Y、reset selected / all、Busy / stale guard、
  Preview / RightPane / diagnostics / fingerprint / 保存可否の再同期をB6範囲とした。
- Undo / Redo時のoperation noticeは汎用文言へ置き換え、restored snapshotからeffect /
  crossfade noticeだけを再導出する。cleanup operation noticeは履歴へ保存・再現しない。
- historyのdisk保存、selection / viewport / playback履歴、analysis failure / cancel rollback完成、
  READMEと正本仕様closeoutは対象外とし、後二者はB7へ残した。
- 計画作成baselineはB2 / B4 / B5関連56件、wx state / reset関連20件、
  effective identity / save policy関連23件がすべてpass表示・各process exit code 0だった。
  production code、test code、dependency、build設定は変更していない。
- 2026-07-26の現行実装との整合レビューではP1なし、P2 2件、P3 1件を検出した。
  cleanup operation noticeの再現規則、SpinCtrl gesture / stale token境界、
  identity引数名を補正した。
- 修正後の再照合では残存P1 / P2 / P3なしとした。
- 同日の実装前チェックではP1なし、P2 2件、P3 1件を検出した。selected event editorの
  dirty入力と他editable text controlを区別するshortcut routing、RightPane-local
  gesture stateの維持・破棄、pending確定とhistory clear時破棄の境界を補正した。
- 補正後の再照合では残存P1 / P2 / P3なし。関連119件はすべてpass表示・
  各process exit code 0であり、B6実装へ着手可能である。

## 3.25 MS21-B6実装・ユーザーGUI確認記録

- 2026-07-26にcanonical adjustment snapshot全体を対象とするセッション内Undo / Redoを
  実装した。immutable history state、最大50 transaction、redo管理、no-op、
  output-equivalent requested edit、gesture coalescing、identity validationを追加した。
- UiStateへhistory state所有権を移し、RightPaneのmouse / key gesture、
  wheel / tokenなしdiscrete fallback、MainFrameのEdit menu、Ctrl+Z / Ctrl+Y、
  action state、reset selected / all、dirty入力guardを接続した。
- Undo / Redo後は既存shared resolverと `sync_ui_state()` からPreview、RightPane、
  diagnostics、fingerprint、保存可否を再同期する。他editable text controlのnative
  Undo / Redo、selection、viewport、playbackはadjustment historyへ含めない。
- B6 core 12件、B6 wx 9件、関連回帰99件はすべてpass表示・各process exit code 0だった。
  最終全体602件と7 subtestsもpass表示・process exit code 0、
  `compileall src tests` と `git diff --check` もprocess exit code 0だった。
- 同日にユーザー手動GUI確認は全項目通過・問題なしと報告された。
- B6は実装、自動検証、ユーザーGUI確認まで完了した。B7所有のanalysis failure /
  cancel rollback完成、全lifecycle横断監査、README / 配布用readme / 正本仕様同期は
  未実施であり、次工程はMS21-B7である。

## 3.26 MS21-B7 Implementation Plan作成記録

- 2026-07-26にMS21-B7 State Integration / Regression / Docs /
  Adjustment Sync Efficiencyの実装計画を作成した。
- B1で固定したanalysis rollback契約を具体化し、analysis開始時のold base /
  adjustment / history / selection capture、current success時破棄、failure / cancel時の
  identity一致による条件付き復元、late / duplicate callback完全不変を実装対象とした。
- failure rollback後は旧Previewと編集を復元してもdiagnostic ERRORを保持しVMD保存禁止とする。
  cancel rollback後はprior failureがなければcancel INFO付きfingerprintを再構築して
  WARNINGを再確認し、prior failureがあれば既存ERRORを復元してINFOを抑止する。
- ユーザー報告に基づきB6 Undo / Redo効率化を追加In Scopeとした。現行は選択eventありの
  1操作でbase input最大5回、base identity最大6回、effective resolver 3回の構築経路がある。
  1同期限定contextでresolverを最大1回へ集約し、valid edit result hintを再利用する。
- adjustment-only同期ではplayback、waveform、parameter control、container全体の
  不要な再同期・再描画を省き、Preview / RightPane / diagnostics / saveabilityは
  同じeffective planから更新する。persistent cache、timer、threadは追加しない。
- 計画作成baselineはB6 / analysis / late callback / workspace / diagnostics関連47件、
  voice_only / save / report / playback関連62件と7 subtestsがすべてpass表示し、
  各process exit code 0だった。
- production code、test code、dependency、build設定は変更していない。
  計画作成時点の次工程はMS21-B7 planの実装状態整合レビューだった。
- 同日の初回整合レビューではP1なし、P2 3件、P3 1件を検出し、計画とrouting文書を
  補正した。
- history未初期化時はresolverをsnapshotなしで1回実行し、そのcanonical snapshotから
  historyを初期化する。これにより1同期1identity / 1resolver契約と初期化を両立する。
- audio worker success / errorはcurrent job ID、expected kind、RUNNING statusを必須とし、
  terminal後のduplicate callbackとPROBEからANALYSIS_WAV移行後の旧kind callbackを拒否する。
- analysis failureのrollback identityは、`invalidate_analysis()` 前にsnapshot old timing planと
  current audio durationから検証し、3 parameterはidentityとは別のsnapshotで完全一致を検証する。
- failure rollbackのbottom Statusは
  `StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK` と固定文言へ統一した。
- 補正後の再照合では残存P1 / P2 / P3なしとした。production code、test code、
  dependency、build設定は未変更であり、この時点の次工程はB7 pre-implementation checkだった。

## 3.27 MS21-B7実装前チェック補正記録

- 2026-07-27にB7 Implementation Planを現行code、test、B1 rollback契約、B2 import境界、
  B6 dirty入力保護へ再照合した。P1なし、P2 4件、P3 1件を検出した。
- P2は、failure rollback後のprior ERROR喪失、analysis開始時のdirty editor入力上書き、
  base identityに含まれないmorph upper limit / hold / softnessの一致判定不足、
  aggregate wx testとfull suiteのpass表示後のprocess exit code 1である。
- rollback payloadへprior failureとimmutable parameter snapshotを追加し、dirty guardを
  job ID更新・diagnostics clear・Busy移行より前へ固定した。parameterはbase identityと
  別に完全一致を検証し、mismatch terminalをcommit / restoreしない。
- B2の循環参照回避方針を継承し、B7 helperは`MainFrame`所有の一方向依存とする。
  core / writerからGUIへの逆import、`UiState`との相互import、package `__init__`からの
  aggregate exportを禁止し、fresh-processでhelper先行 / MainFrame先行を検証する。
- P3の実装開始基準は`3ccf630`へ更新した。P2 / P3のplan契約は解消済みである。
  ただしwx終了コードは受け入れ条件を弱めず、B7 Step 0でtest teardownを原因分離・
  最小補修し、wx aggregateとfull suiteのprocess exit code 0を確認するまでproduction
  codeを変更しない。
- full suite 602件と7 subtestsは2回ともpass表示・process exit code 1、wx抽出91件は
  pass表示・511件deselected・process exit code 1だった。直接原因は未確定である。

## 3.28 MS21-B7実装・自動検証記録

- 2026-07-27にjob-local analysis rollback、prior failure保持、dirty入力guard、
  parameter snapshot、active terminal guard、audio worker kind / status guardを実装した。
- failureでは同一base / parameterの旧plan、adjustment history、selectionを確認用に復元し、
  current ERRORとVMD保存禁止を維持する。prior failureありのretry / cancelでは既存ERRORを
  復元してcancel INFOを抑止する。
- 1同期限定contextでdiagnostics、Preview、selected editor、action stateへ同じ
  `EffectiveShapePlan`を渡す。edit / reset selectedはvalidated hintを再利用し、Undo / Redo等の
  adjustment-only同期ではplayback、ParameterPanel、PlaceholderContainer全体の不要更新を省く。
- B7 helperはMainFrame所有の一方向依存とし、package `__init__` export、core / writerから
  GUIへの逆import、UiStateとの相互importを追加していない。fresh-processの両import順を確認した。
- startup splash testが実SplashScreenを残したまま終了することをwx access violationの
  原因として特定し、SplashScreen test doubleとApp / Frame明示teardownへ限定補修した。
- B7専用15件、B3からB6回帰61件、lifecycle回帰47件と7 subtests、
  wx aggregate 97件、full suite 617件と7 subtestsはpass表示・process exit code 0だった。
- README、配布用readme、Pipeline / GUI / Error仕様をimplemented状態へ同期した。
  後続のユーザー手動GUI確認で追加tab補正要望が提示された。

## 3.29 MS21-B7 Selected Event Tab Auto-Switch追加補正記録

- ユーザーはB7手動GUI確認を実施し、Previewタイムラインで単母音eventを選択した場合に
  RightPaneの「選択イベント」タブへ自動切替する補正を要望した。
- 追加補正計画を作成して現行selection / Notebook / lifecycleへ照合し、
  残存P1 / P2 / P3なしと判定した。
- `RightPane.show_selected_event_tab()`は固定page indexを使わず、
  `FindPage(panel_selected_event)`で解決し、current pageと異なる場合だけ
  `ChangeSelection()`する。
- `MainFrame`はPreview user clickのcanonical commit成功・editor表示更新後だけhelperを
  呼ぶ。same-event再clickでは切り替え、stale / Busy request、通常sync、Undo / Redo、
  rollbackではcurrent tabを維持する。
- RightPane 3件、Preview selection 6件、Undo / Redo・B7 lifecycle 12件、
  wx aggregate 90件、full suite 618件と7 subtestsはpass表示・各process exit code 0だった。
- 自動test中にanalysis failure callbackが実`wx.MessageBox`を開く問題は、productionの
  通知契約を変えず、該当test内でMessageBoxをmockして呼び出しを検証する形へ補修した。
  補修後のfull suiteも618件と7 subtestsがpass表示・process exit code 0だった。
- 2026-07-27にユーザーから、追加補正を含むMS21-B7範囲の手動GUI確認は通過し、
  問題なしと報告された。B7は完了し、次工程はMS21-B8 Closeout計画である。

## 3.30 MS21-B8 Closeout実施記録

- 2026-07-31にMS21-B1からB7の要求、実装、test、ユーザー確認、文書、依存・配布境界を
  総合監査するMS21-B8 Closeout Implementation Planを作成した。
- B8は新機能やproduction code / test code変更を行わず、受け入れ条件台帳、回帰検証、
  ユーザー確認証拠、文書・依存・配布境界を監査し、A / B / CでCloseoutを判定する。
- 計画と現行実装の整合確認ではP1 / P2はなく、B7計画に残っていたB7-PRE-004の
  「実装前gate」表記を、実測済みの `closed (2026-07-27)` へ補正した。その他の
  production code、test、dependency、build設定とのP3相当の齟齬は確認されなかった。
- B8 pre-implementation checkで指摘した文書境界のP2 / P3は、計画作成・レビュー段階と
  Closeout監査開始段階のclean gate分離、明示的な回帰test file群、証拠台帳（B8計画§15）を
  追加して修正した。Closeout監査開始には文書baseline commit後のclean確認が必要である。
- full suite 618件と7 subtests、`compileall src tests`、`git diff --check` はいずれも
  process exit code 0を確認した。B7専用15件、B2〜B6回帰123件、MS17 / MS19 / MS20・既存回帰
  154件＋7 subtestsもすべてpass表示・process exit code 0だった。
- B1からB7のユーザー手動GUI確認は、各Blockで報告された範囲だけを証拠として再利用した。
  Codexによる手動GUI実行とは扱わない。実MMDでのVMD / WAV読み込み・リップ同期はMS26へ
  引き継ぐ。
- P1 / P2 / P3は残存せず、MS21-B8 CloseoutをAで確定した。B8ではproduction code、test code、
  dependency、build / package / license、固定モーフ、VMD形式、network契約を変更していない。
  次工程はMS22のImplementation Plan策定であり、merge、push、tag、releaseは未実施である。

## 3.31 MS22 Block Breakdown・B1計画記録

- 2026-08-01にMS22 Block BreakdownとMS22-B1 Implementation Planを作成した。
- B1 planの実装状態整合レビューでP1なし、P2 5件、P3 1件を検出した。long run source参照、
  baseなしgeneration state、B2 / B3 mode契約依存、preset / INI recovery、MS21 fingerprint入力、
  diagnostics field、B1回帰gate、Index routingを文書上で補正した。
- 計画指定193件と補完78件の合計271件はすべてpass表示・process exit code 0だった。
- 続くBlock Breakdown / B1整合再チェックでP1なし、P2 2件、P3 1件を検出した。B1 planへ
  `presets.json`のINI同一directory、UTF-8、保存失敗時temporary cleanupを継承し、B2の直接回帰として
  writer zero guard / multipoint、pipeline Preview identity、prepared VMD saveの既存65件を追加した。
  Block BreakdownのB1状態と次工程表示も現行状態へ補正した。
- MS22-B1は未実施であり、production code、test code、GUI、INI、JSON、dependency、build設定は
  変更していない。追加補正後の関連回帰336件はすべてpass表示・各process exit code 0で、
  残存P1 / P2 / P3なしと判定した。B1はcontract-only pre-checkとして着手可能である。

## 3.32 MS22-B1 Contract Fixed実施記録

- 2026-08-01にB1契約監査を実施し、MS21 Closeout A、現行code、test、Roadmap、Block Breakdown、
  B1計画、package設定を照合した。
- 正規化済み読み列を長音検出正本とし、token / timeline metadata、`ms22-base-plan-v1`、
  `ms22-adjustment-snapshot-v1`、long runのsource / continuation / terminal、hold / decay、
  decay終端exact `0.0`、補正所有権、preset / INI / `presets.json`、atomic history、diagnostics /
  fingerprint / lifecycleの契約を固定した。
- ユーザーが選択した「decayは長音終端で0へ減衰する」を採用案として記録した。
- B1ではproduction code、test code、GUI、INI、JSON、dependency、build設定を変更していない。
  336件の指定回帰、`compileall src tests`、`git diff --check`はすべてexit code 0だった。
- P1 / P2 / P3は残存せず、MS22-B1をCompleted / Contract Fixedと判定した。次工程はB2
  Implementation Plan策定であり、B3のproduction実装はB2 primitive mode契約の実装・検証後とする。

## 3.33 MS22-B2 Implementation Plan作成記録

- 2026-08-01にMS22-B2 Long-Vowel Data Contract / Shared Resolver / Same-Vowel Auditの
  Implementation Planを作成した。
- normalized readingからimmutable token、timeline metadata、`ms22-base-plan-v1`、
  `ms22-adjustment-snapshot-v1`、run role / ownership、hold / decay shape、Preview / writer adapterまでを
  B2のUI非依存実装範囲へ固定した。
- long run memberをautomatic same-vowel candidate、通常grouping、manual crossfadeから隔離し、
  `ー`を含まない既存処理を変更しない計画とした。decayはユーザー判断どおりterminal endでexact `0.0`、
  holdはterminal endまでpeakを維持してclosing edgeを終端後へ置く。
- preset JSON / INI、GenerationSettings、history、UiState、diagnostics、fingerprint、RightPaneはB3以降へ維持した。
- 計画作成baselineの関連回帰227件はすべてpass表示・各process exit code 0だった。
- plan作成時点でproduction code、test code、GUI、dependency、build設定は変更していない。
  次工程はB2 pre-implementation checkである。

## 3.34 MS22-B2 plan実装状態整合レビュー修正記録

- 2026-08-01にB2 planを現行even fallback frame、writer duplicate merge、selected editorの
  resolved tail前提、関連testへ照合した。P1なし、P2 2件、P3 2件を検出した。
- source startとsource peakが同一frameの場合はopening zeroを省略してpositive peakを優先する。
  long required zeroと別shapeのpositive pointが同一morph・同一frameで競合する場合は、writer mergeへ
  委ねずnormalization前にfail closedとする。異なるmorphの同一frame配置は受理する。even fallbackの
  `あーあ`でdecay terminalと次の`あ` peakが一致する配置は決定的な拒否対象とした。
- hold / decay双方のreal long shapeへnon-`None`のresolved tail metadataを持たせる。decayではrequested
  tail / slopeをlatent情報として保持し、effective hold / softnessを0、slope midpointなしとする。
  これによりB2でGUIを変更せず、既存selected editor consumerの構造前提を維持する。
- B2新規test file 5件を候補ではなく必須作成対象へ固定し、直接影響するadjustment history、selected editor、
  UI sync contextの既存3 fileを指定回帰commandへ追加した。
- 計画作成baseline 227件に補完回帰24件を加えた合計251件はpass表示・各process exit code 0だった。
  production code、test code、GUI、dependency、build設定は変更していない。P2 / P3は文書上で解消し、
  当時の次工程はB2 plan再チェックだった。

## 3.35 MS22-B2 実装前チェック再確認記録

- 2026-08-06にB2 plan、Block Breakdown、B1 contract、現行code / testを再照合した。
- duration契約はsource / terminal event frameをsource duration内へ制限し、最終shapeのgenerated closing zeroだけを
  既存resolved final tailによりduration超過可能とする契約へ統一した。次shapeがある場合の既存clampは維持する。
- source peak frameはbase timeline frameで固定し、B2 adjustmentはpeak valueだけを変更する契約へ統一した。
- Block Breakdownへ、直接影響するMS21-B6 adjustment history、MS21-B4 selected event editor、
  MS21-B7 UI sync contextの3回帰を追加した。
- 対象回帰251件、full suite 618件＋7 subtests、`compileall src tests`、`git diff --check`はすべて
  pass表示・process exit code 0だった。production code、test code、GUI、dependency、build設定は変更していない。
- P1 / P2 / P3の残存はなく、MS22-B2は実装着手可能と判定した。実MMD確認はMS26へ維持する。

## 3.36 MS22-B2実装・コードチェック記録

- 2026-08-06にMS22-B2を実装した。`VowelToken`、timeline long-vowel metadata、MS22 identity / adjustment
  schema、long runのrole / ownership、hold / decay shared resolver、Preview / writer adapter整合を追加した。
- `ー`を含まない既存same-vowel / cross-vowel処理、legacy timeline tuple、固定モーフ、30fps、VMD形式は維持した。
- B2専用test 26件、MS21 core / Preview回帰102件、text / pipeline / VMD回帰51件、full suite 644件＋7 subtests、
  `compileall src tests`、`git diff --check`はすべてpass表示・process exit code 0だった。
- GUI、preset / INI、state / history、diagnostics、dependency、package、実MMD確認は変更・実施していない。P1 / P2 / P3は残存せず、
  次工程はMS22-B3 Generation Preset Store / Settings ContractのImplementation Plan策定である。

## 3.37 MS22-B3 Implementation Plan作成記録

- 2026-08-08にMS22-B3 Generation Preset Store / Settings ContractのImplementation Planを作成した。
- B3はB2のprimitive `LongVowelMode` validationを入力として、immutable `GenerationSettings`、built-in /
  user preset、schema version 1の`presets.json`、INI active settings / active preset id、strict validation、
  atomic save、invalid JSON時のread-only unavailable、Custom fallbackをUI非依存coreへ実装する計画である。
- 既存`SettingsStore`の旧callerが新generation keyを省略しても、保存済みactive settingsをdefaultで上書きしない
  互換条件をB3の受け入れ条件へ追加した。B4のstate / history / diagnostics、B5のUIは先行実装しない。
- B3のproduction code、test code、GUIは未実装であり、plan作成時の次工程は実装状態再チェックである。

## 3.38 MS22-B3 plan修正・再チェック記録

- 同日の実装状態再チェックではP1なし、P2 3件、P3 3件を検出した。P2は外部修復後の次回`load()`での
  read-only状態復帰、load / mutation / active resolutionのstructured result DTO、既存INI設定を壊さない
  additive保存表現である。P3は既存INIとの責務表現、update対象自身の同名判定、B2直接回帰commandの列挙である。
- B3 planへ、再load時のcollection / mutation availability置換、固定error codeと`PresetMutationResult`、
  active resolution DTO、既存`[ui]`への空文字active id encoding、update自己除外、B2の直接回帰3件を追加した。
- 修正後の再チェックではP1 / P2 / P3の残存なしと判定した。コード、test、GUI、依存関係、INI / JSON本体は変更せず、
  次工程はMS22-B3実装前チェックである。

## 3.39 MS22-B3実装・P2/P3修正・コードチェック記録

- 2026-08-08にMS22-B3を実装した。実装コミットは`4ee67af Implement MS22-B3 preset store and settings contract`である。
  `src/core/generation_presets.py`へimmutable `GenerationSettings`、built-in / user
  preset、strict schema version 1の`presets.json`、atomic mutation、failure isolation、active resolutionを追加し、
  `src/core/settings_store.py`へ`long_vowel_mode`、`active_preset_id`、0〜100値域、旧callerの保存値保持を追加した。
- B3専用testでは、表示名1 / 100 / 101文字境界、JSON 101件上限、write / replace failure、temporary cleanup、
  same-directory・close-before-replaceを検証した。B3専用23件＋19 subtests、SettingsStoreを含む29件、指定回帰21件、
  13件、35件、17件、full suite 667件＋26 subtests、`compileall`、`git diff --check`はすべてpass表示・exit code 0だった。
- 実装後コードレビューで検出したP2（Index / Block Breakdown / B3 planのB3未実装表記）とP3（表示名境界、atomic write
  failure経路のテスト証拠不足）を文書・test補正で解消した。B3の選択UI、state / history / diagnostics統合、実MMD確認は
  未実施であり、次工程はMS22-B4 Implementation Plan策定である。

## 3.40 MS22-B4 Implementation Plan作成記録

- 2026-08-08にMS22-B4 Generation State / History / Diagnostics IntegrationのImplementation Planを作成した。
- B4はbaseなしでも有効な`GenerationState`、base-bound `OutputEditState`、adjustment / generation settings /
  active preset idのatomic history、resolve-before-commit、output-only parameter、startup / rollback / diagnostics統合を
  所有する。B5のRightPane preset / mode UIは先行実装しない。
- `BasePlanIdentity`がgeneration settingsを含まない現行契約を踏まえ、effective plan hintへ`ShapeParameters`
  provenance guardを追加し、resolver 1回とstale generation hint拒否を両立させる計画とした。
- active mode / preset、effective hold / decay run数、mode override数はstructured diagnostics summaryへadditiveに
  追加する。一方、MS21 canonical fingerprint payloadとschema `ms21-effective-output-v1`は維持する。
- 計画作成baselineはB2 / B3 / history 53件＋19 subtests、wx state / lifecycle 22件、diagnostics / VMD 62件、
  RightPane / warning / save 43件の合計180件＋19 subtestsがpass表示・failure / error表示なし、
  各process exit code 0だった。production code、test code、GUIは変更していない。
- 自己回帰チェックではP1なし、P2 5件、P3 3件を検出した。shape-parameter provenanceの唯一owner、
  settings同値direct no-op、canonical control投影、startup store注入、出力編集のUndo / Redo文言、明示回帰test、
  workspace確認境界、save-disabled後の非再試行をplanとBlock Breakdownへ反映した。追加回帰19件を含む
  関連199件＋19 subtestsはpass表示・各process exit code 0、`git diff --check`もexit code 0だった。
- P2 / P3は文書上で解消済みで、次工程は修正後plan再チェックとB4実装前チェックである。
  実MMD確認はMS26へ維持する。

- 2026-08-09のB4実装前チェックでは新規P2 3件（deleted presetのUndo / Redo endpoint整合、`AutoLipToolApp`から
  `AppController`へのstartup store注入経路、candidate `None` adjustmentに対するstale hint wildcard）とP3 2件
  （diagnostics DTO不変条件、selected event editor / pipeline-preview回帰の列挙漏れ）を検出した。production code、
  test code、GUIは変更せず、B4 planとBlock Breakdownへ限定反映した。以前解消したP2 / P3の契約は変更していない。
  修正後の再チェックを経て、次工程はB4実装前チェックの再実行である。

- 2026-08-09にB4を実装し、active preset IDを含む`OutputEditState`全体を同期context cacheの整合対象へ追加した。
  id-only Undo / Redo後のresolver再実行回帰、morph upperのみの`AnalysisParameterSnapshot`、startup / state / history /
  diagnostics統合を反映した。手動確認で判明した母音Preview非表示は、RMS補正後の別母音を挟む同一モーフ境界
  競合をpipelineで限定補修した。修正後の関連33件、full suite 686件＋26 subtests、`compileall`、
  `git diff --check`はpass表示・各process exit code 0だった。P2 / P3は解消済みで、同日にユーザーから
  MS22-B4手動テスト通過が報告された。preset UIはB5、実MMD確認はMS26へ引き継ぐ。

## 3.41 MS22-B5 Implementation Plan作成記録

- 2026-08-09に、現行B4の`commit_generation_settings`、`apply_preset_generation`、startup store seam、
  B3の`GenerationPresetStore`、selected event editor、long-vowel resolver、関連testを照合して、
  MS22-B5 Preset UI / Event Override FlowのImplementation Planを作成した。
- B5はRightPaneの`プリセット` tab、built-in / user / Customの一覧と明示的なApply、create / update /
  rename / delete、mutation failure notice、active presetのupdate / delete後のCustom正規化を対象とする。
  terminal continuation eventだけにinherit / hold / decay modeを許可し、decay時はterminal zeroを説明しつつ
  latent tailを保持してhold復帰時に再利用する。選択とApply、preset mutationとoutput stateを別transaction
  として扱い、B4のresolver・history・diagnostics・JSON schemaを再実装しない。
- 計画作成時点でB5のproduction code、test code、GUI、INI / JSON本体、依存関係、build設定は変更していない。
  関連回帰53件はpass表示・process exit code 0だった。
- 同日の実装状態整合レビューではP1なし、P2 3件、P3 2件を検出した。active preset mutation後の
  base-bound history / baseなしstate正規化、load / mutation別error matrix、immutable request DTO、
  B4 history直接回帰、selector fallbackをplanへ反映して解消した。B3 / B4 state・history関連35件、
  B2 resolver / selected editor関連32件はpass表示・各process exit code 0だった。
- 次工程は修正後plan再チェックとB5実装前チェックである。B6の横断docs / lifecycle、MS26の実MMD確認は
  B5の範囲外として維持する。

## 3.42 MS22-B5実装・ユーザー確認記録

- 2026-08-10にMS22-B5を実装した。RightPaneのpreset tab、stable ID選択、明示Apply、user presetのcreate / update /
  rename / delete、load / mutation error notice、active presetのCustom正規化、terminal long-vowel mode overrideを接続した。
- B5専用test 10件、スプラッシュテストを除く既存全体回帰694件、`compileall src tests`、`git diff --check`を確認し、
  ユーザーから手動GUI確認通過の報告を受けた。
- 全体実行で発生した既存スプラッシュテストの起動時間依存失敗はP3としてMS22-B6の横断回帰へ、実MMDのVMD / WAV確認はMS26へ引き継ぐ。

## 3.43 MS22-B6 Implementation Plan作成・レビュー記録

- 2026-08-11にMS22-B6 Lifecycle Regression / DocumentationのImplementation Planを作成した。B6はMS22-B2からB5の
  lifecycle横断回帰、startup splash / wx teardown安定化、利用者文書・Pipeline / GUI / Error仕様・routing文書の同期、
  manual GUI確認範囲の記録を所有する。MS22 Closeout判定はB7、実MMD確認はMS26へ維持する。
- plan再チェックで検出したP2 4件・P3 2件はplan本文で解消した。その後の再チェックで、Block BreakdownのB6状態、
  Indexのlink・現在地・策定記録、Roadmapの策定記録が未同期であるP2 1件を確認し、本同期で解消した。
- 計画作成baselineはstartup splash単独2件、MS22 / lifecycle関連122件、full suite 696件がpass表示・process exit code 0だった。
  一方、B4 / B5 / splashの既知17件組合せは17件pass表示・process exit code 1であり、B6の原因分離対象として残る。
  これらはB6実装完了の証拠ではない。次工程はMS22-B6実装前チェックである。

## 3.44 MS22-B6実装・ユーザー確認記録

- 2026-08-11にB6専用non-wx lifecycle 7件、wx lifecycle 9件、splash 3件、指定回帰、full suite 713件、
  `compileall src tests`、`git diff --check`を終了コード0で確認した。
- wx終了時のcoalesced save timer停止、`AutoLipToolApp`の遅延Layout / Refresh callback guard、test teardown helperを
  限定補修した。
- 同日にユーザーからSection 11.7の手動GUI確認項目をすべて通過し問題なしとの報告を受領した。
  これはCodex自身のGUI実行結果とは扱わない。実MMDでのVMD / WAV読み込み・リップ同期はMS26へ維持する。
- 次工程はMS22-B7 Closeoutであり、MS22 Closeout判定はB7の責務とする。

## 3.45 MS22-B7 Implementation Plan作成記録

- 2026-08-11にMS22-B7 MS22 CloseoutのImplementation Planを作成した。B7はB1〜B6の要求、実装、test、
  user evidence、docs、runtime data、dependency / package境界を監査し、A / B / Cで判定する。
- 計画作成baselineはMS22 B2〜B6専用＋splash 93件、full suite 713件、`compileall src tests`、
  `git diff --check`がpass表示・process exit code 0だった。MS21 Closeout基準からdependency / package /
  build / license fileの差分はなかった。
- 計画作成時点ではrepo rootでtrackedの`presets.json`をruntime user data境界のP2候補、B5のsplash P3 current
  status未同期をP3候補としてpre-closeout gateへ固定した。
- その後の計画レビューでP2 / P3として確定し、local `presets.json`を保護したGit追跡解除、
  `/presets.json`と`/MMD_AutoLipTool.ini`のroot限定ignore追加、B5 / Block / routing文書のsplash current status同期を
  分離repairとして実施し、両findingを解消した。production code、test code、GUIは変更していない。
- B7計画策定ではproduction code、test code、GUI、dependency、packageを変更していない。
  次工程はMS22-B7実装前チェックで、Closeout判定は未実施である。実MMD確認はMS26へ維持する。

## 3.46 MS22-B7 Closeout実施記録

- 2026-08-12にMS22-B7 Closeout監査を実施した。MS22 direct regression 93件、基盤回帰185件、
  MS21回帰138件、MS17 / MS19 / MS20回帰158件、B4 / B5 / splash組合せ18件、full suite 713件を
  pass表示・process exit code 0で確認した。`compileall src tests`と`git diff --check`もexit code 0だった。
- P1 / P2 / P3はなく、MS22 CloseoutはAと判定した。B4 / B5 / B6の手動GUI確認はユーザー報告の範囲に限定して再利用し、
  Codex自身のGUI実行結果とは扱わない。
- `presets.json` / `MMD_AutoLipTool.ini`はGit追跡対象外・root限定ignoreであり、local `presets.json`保持を確認した。
  dependency / package / build / license差分はなく、production code、test code、GUIも変更していない。
- 実MMDでのVMD / WAV読み込み・リップ同期確認はMS26へdeferredのまま維持する。次工程はMS23 Implementation Plan策定であり、
  MS23実装は開始していない。

## 3.47 MS27-B4実装・内部artifact監査・ユーザー確認記録

- 2026-09-14にMS27-B4の残存findingを解消した。`MMD_AutoLipTool.spec`の除外設定と`build_hooks/hook-torch.py`により、matplotlib package/data、sample_data、旧Qt、Torch test/TensorBoard、Numba TBB任意backendの過剰同梱を防止した。Whisper / Torch / Numba主要moduleは保持した。
- `tests/test_whisper_model_catalog.py`は`7 passed`、process exit code `0`。新規隔離sourceのfix-03 onefile build / SmokeLaunchもprocess exit code `0`で成功した。
- fix-03候補は425758214 bytes、SHA-256 `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`、FileVersion / ProductVersion `1.0.0`。G-ARTIFACTをPassとした。
- ユーザーから手動確認通過、実MMDでも問題なしとの報告を受領した。これはユーザー報告であり、Codex自身のGUI / 実MMD操作結果とは扱わない。
- B5のZIP組立・展開・配布環境からの独立性、Python 3.11 / 3.12互換性、B6の最終release readiness判定、GitHub公開は未実施である。

## 3.48 MS27-B5実装・配布候補確認記録

- 2026-09-15から2026-09-16にかけて、候補#07で判明した過剰なmodule除外を限定補修し、候補#08を隔離再buildした。候補#08 EXEは425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、FileVersion / ProductVersionはともに`1.0.0`である。
- `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`は423274681 bytes、SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`。必須5ファイルと`licenses/`を含む157 filesについて、組立・展開・実行先のhash一致、安全なentry、runtime data / weights / sample等の非同梱を確認した。
- Codexはrepo外cwd、Windows標準PATHのみ、Python環境変数なしの配布実行でM01〜M07を実施した。WAV / MP3 / M4A、model未配置時の安全な停止、既存検証済みsmallモデルでのvoice_onlyとTEXT＋音声、Preview、VMD保存、通常終了・再起動・残留なしを確認した。スプラッシュ`Ver. 1.0.0`のみはユーザー目視確認として記録し、Codex自身の画面取得結果とは扱わない。
- 対象回帰は`8 passed, 21 subtests passed`、process exit code `0`。B5のG-PACKAGEをPassとした。実MMDはB5で再操作しておらず、既存のMS26ユーザー報告を再判定しない。
- Python 3.11 / 3.12互換性、FFmpegのexact archive provenance・公開時の対応ソース提供方式、MS27 release readinessと公開はB6へ残る。Index / Roadmap / milestone / Version ControlのB5状態は2026-09-17に同期済みで、B6では後続変更を含め最終再照合する。B5 PassをMS27全体の完了や公開許可と扱わない。

## 3.49 MS27-B6 release readiness監査記録

- 2026-09-18に候補#08のEXE / ZIPとB5保存証跡をread-onlyで再照合した。EXEは425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、ZIPは423274681 bytes、SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`で、記録と一致した。ZIPの157 files、B5のCodex実行証跡、スプラッシュのユーザー目視確認を候補別に継承した。
- 候補sourceの`MMD_AutoLipTool.spec`は現HEADと同一bytesである。候補embedded版の`THIRD_PARTY_LICENSES.md`はB5後の状態追記を含まないため現HEADとhashが異なるが、追記を候補bytesへ遡及させず、license / component対応を変えない状態記録として分離した。配布bytesを更新する場合はB4/B5の再実施が必要である。
- Python 3.11 / 3.12のsource / build互換性は未検証だが、ユーザー決定によりWindows onefile公開判定の条件から外した。FFmpegについては、`origin/main`が`2151d7b`を指し、FFmpeg 10 entriesとLICENSE / NOTICE / THIRD_PARTY_LICENSES / Manifestを追跡し、候補branchの`FFmpeg/bin`に差分がないことを確認した。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexは法的適合を独自に保証しない。
- このためG-READYは**Pass**である。B5のG-PACKAGE PassおよびMS26 CloseOut Aを取り消さない。B6監査時点ではMS27 CloseOutと公開は未実施だったが、同日のユーザー明示決定によりMS27 CloseOutを確定した。GitHub Release、tag、push、merge、公開用source archive生成は引き続き未実施であり、詳細は[MS27-B6 Implementation Plan](Implementation_Plan/MS27-B6_Implementation_Plan.md) §15.2を正本とする。

## 3.50 MS27 CloseOut確定記録

- 2026-09-18にユーザーが、B1〜B6のPass記録、候補#08のidentity、B6のG-READY Pass、および残る未検証事項・公開境界を前提として、MS27 CloseOutを確定した。
- Python 3.11 / 3.12のsource / build互換性は未検証の別support policyとして残る。FFmpegのexact provider archive identityは既存B3方針上の非阻害provenance limitationであり、GitHub上の既存公開の規約適合はユーザー判断である。Codexは法的適合を独自に保証しない。
- GitHub Release、tag、push、merge、公開用source archive生成はMS27 CloseOutに含めず、未実施の別工程として維持する。今回CloseOutの確定に伴う新たなbuild、テスト、GUI、実MMD操作は行っていない。

## 3.51 MS28 独立修正実装マイルストーン

- MS28は、MS20〜MS27で構成したVer.1.0全体マイルストーン系列・依存関係・リリース判定から切り離した修正実装用マイルストーンである。
- 主目的は、Ver.1実装後に報告された「TEXT＋音声解析後の母音タイムライン非表示」と「音声のみ解析後の生成設定が反映されず0へ戻る」不具合の原因確認、限定修正、回帰防止である。
- MS28-B1は、長音後続境界の欠落とrequired-zero conflictによるPreview / generation settings失敗経路を対象とする初期修正実装計画として策定した。
- MS28-B1は、長音後続境界の欠落とrequired-zero conflictによるPreview / generation settings失敗経路を対象とする修正Blockであり、計画・production code・test codeの実装と自動回帰を完了済みである。Git公開操作は別工程として未実施である。
- MS28-B2は、B1の契約および回帰条件を実装へ反映した修正Blockであり、production code・test codeの実装と自動回帰は完了済みである。
- MS28-B3は、解析後の中間状態・debug artifact・Preview/Writer比較・無音観測を記録するデバッグ機構の実装Blockであり、`03f5e2c`で実装済みである。
- MS28-B4は、B3ログで確認した無音core内の開口残存とcross-vowel handoffの契約を修正するBlockである。長いzero-runの全区間判定、silence core／boundary fringe、handoff拒否、通常base event admission、`EventSilenceAdmission`、required-zero、同一projection revisionのprovenance伝播、B4 debug artifact schema、runtime契約identityを実装し、全pytest `1124 passed, 4 skipped`を終了コード`0`で確認した。実Whisper再解析、native GUI、実MMD、EXE、build、手動Debug ON/OFF比較は未検証である。
- MS28の修正内容・検証結果・残課題は、MS27の完了状態や既存のpackage/readiness証跡を変更しない。

## 3.52 MS28-B4 Implementation Plan作成・P2/P3解消記録

- 2026-09-20にB3ログ、`pipeline.py`、`effective_shape_plan.py`、`main_frame.py`、既存のpipeline / Preview / VMD writer回帰を照合し、無音coreをまたぐcross-vowel handoffを修正するMS28-B4計画を作成した。
- 再チェックで確認したP2（代表ピーク基準を期待する既存回帰テストの列挙不足、B3旧reason codeとB4新分類の対応不足、`PeakValueObservation`／`ObservationHandoff`／debug record間の伝播項目不足）を、B4計画の対象テスト・固定mapping表・データ責任境界へ反映した。
- P3（routing索引の参照先不整合）は、旧MS17索引ではなくMS20以降の正本である本書へMS28-B1〜B4を追加し、現在地をMS28-B4計画補正済みへ同期して解消した。
- 追加の再チェックで確認したP2（`result`と`classification`の正本名、Writer provenanceの責任箇所）について、B4では`result`を新規artifactの正本、旧`classification`を読み取り互換とし、既存Writer adapterのtuple APIを維持したまま`main_frame.py`のdebug専用builderがraw/normalized実データとEffectiveShapePlan provenanceを結合する契約へ補正した。
- 上記補正に伴い、B4-AC12〜AC14と、代表ピーク基準の既存pipeline回帰・短いhandoffのWriter/Preview回帰を具体化した。
- 再チェックで確認したP2（`boundary_overlap_only`とresult列挙の矛盾、silence core内正値の分類結果未固定、right-gap／floor residualの全区間上限未固定、RMSからdebug artifactまでの正本経路未固定）とP3（frame cell境界式、suspiciousを含む固定reason／ON-OFF比較条件、回帰fixture列挙の不足）をB4計画へ反映した。`boundary_overlap_only`は`result=clear`＋reason code、core内の契約違反は`contract_violation`、帰属未解決は`suspicious`とし、RMS→PeakValueObservation→ObservationHandoff→debug builderの受け渡し・型・artifact境界、residual試験の期待値を固定した。
- 再々チェックで確認したP2（B3の`schema_version=1`とB4追加payloadの識別・旧artifact互換方針、RMS source `classification`とB4 `candidate_classification`のproducer/consumer境界）を、`contract_version="ms28-b4-silence-v1"`、旧artifactの保持・runtime read非追加、source labelからcanonical fieldへの明示写像として固定した。P3はAC17/AC18と14.1の再発防止ゲートへ反映した。
- 再チェックで確認したP2（canonical artifactへ`schema_version`が保存されるJSON pathの未固定、B4 runtime契約フィールドと既存save-state fingerprintの境界未定義）を、stage envelope／payload／root canonical／projection canonicalの配置表、`output_diagnostics._observations_canonical()`へのruntimeフィールド包含、debug専用フィールド除外、AC19/AC20、14.1の再発防止ゲートへ反映した。Indexは「計画レビュー上のP1/P2/P3指摘なし、AC01〜AC20と実装・テストは未検証」という状態へ更新した。
- 上記補正後、B4計画の文書レビュー上のP1/P2/P3指摘はない。ただしAC01〜AC20は未検証であり、production code、test code、runtime user data、依存関係、build設定も変更していない。次工程は、別途承認されたMS28-B4実装前チェックおよび修正実装である。

## 3.53 MS28-B4修正実装・自動回帰記録

- 2026-09-20にMS28-B4を実装した。`pipeline.py`でzero-run全体のframe spanとsilence core／boundary fringe、coverage／provenance、拒否理由を確定し、`effective_shape_plan.py`でsilence core交差・全区間上限超過・不足証拠のhandoffを`enabled=False`として伝播した。
- `main_frame.py`のB4 debug builderは、B3の既存処理を置換せず、core／fringe、result、reason code、evaluation status、handoff情報をB4 payloadへ記録する。canonical artifactのrootにも`schema_version=1`と`contract_version="ms28-b4-silence-v1"`を保持する。B3既存artifactのruntime read・上書きは追加していない。
- `PeakValueObservation`のB4実行時契約フィールドは`output_diagnostics._observations_canonical()`とBasePlanIdentityの入力へ指定順序で追加し、debug専用のresult／reason／provenance説明情報はidentityへ含めない回帰を追加した。
- B4関連・既存契約回帰は71件、Preview／Writer関連回帰は107件、全pytestは`1118 passed, 4 skipped`で、実行したpytestの終了コードはすべて`0`だった。`git diff --check`も終了コード`0`である。`.venv`にruffがないためruffチェックは未実施である。
- 実Whisper、native GUI、EXE、実MMD、正式版build、手動Debug ON/OFF比較は未実施であり、MS28-B4の自動検証済み範囲と分離して扱う。MS27の完了状態、バージョン、依存関係、runtime user data、spec／build設定、公開境界は変更していない。

## 3.54 MS28-B4計画改善・状態境界補正記録

- 2026-09-20のB4計画再チェックで、P2（IndexのB4完了表記と追加改善pendingの不一致、`EventSilenceAdmission`の追跡項目・保存先・identity境界の不足、manual adjustment／required-zeroのproducerと評価時点の未固定、AC01〜AC26の状態区分不足、runtime canonical field順序の不一致）とP3（identity境界段落の重複）を確認した。
- B4計画へ、`EffectiveShapePlan.event_silence_admissions`、`origin_shape_id`、`positive_point_kinds`、`source_event_indices`、`effective_frame_range`、`required_zero_frame_ranges`を追加し、candidate shapeをdebugへ出さずadmission拒否後にfinal shapeを再構築する二段階、canonical `AdjustmentLayerSnapshot.adjustments`とfinal `NormalizationContract.required_zero_frames`のproducer境界を固定した。
- AC状態は、B4 baselineの実装・自動回帰、追加改善AC21〜AC26の未実装、実Whisper／GUI／EXE／MMD／Debug ON/OFFの未検証を分離して記録する。MS28-B4はbaseline完了・追加改善pendingであり、B4全体の最終受入完了とは扱わない。
- Index、B4計画§12、§14.1の状態語彙を同期し、次工程は追加改善の実装前チェック・実装・回帰検証である。今回の補正ではproduction code、test code、runtime user data、依存関係、build設定を変更していない。

## 3.55 MS28-B4追加改善実装・自動回帰記録

- 2026-09-20にB4追加改善を実装した。`EventSilenceAdmission`をeffective shape planへ追加し、通常母音のsilence core内positive shapeをadmission段階で拒否してcandidate shapeをfinal outputへ流さない二段階再構築を接続した。拒否eventは`origin_shape_id=None`、候補範囲とrequired-zeroを保持し、final `NormalizationContract.required_zero_frames`へ展開する。
- long-vowel roleとcanonical adjustment snapshotの非no-op entryを許可理由として分離し、debug resultを`explained_long_vowel_decay`／`explained_manual_adjustment`へ分類した。handoffとbase event admissionはdebug artifact内の別配列で保持する。
- `main_frame`のdebug builderへ同一projection revisionのprovenance rowsを渡し、Writer point／interpolationのnormalized keyとprovenanceの対応を検証する。不足時は`provenance_unavailable`／`not_evaluable`へfail-closedする。
- 追加専用回帰6件、B4関連・既存契約回帰70件、全pytest `1124 passed, 4 skipped`を終了コード`0`で確認した。実Whisper、GUI、EXE、MMD、正式版build、Debug ON/OFF実run比較は未検証である。

## 3.56 MS28-B4B境界admission修正実装・自動回帰記録

- 2026-09-21にMS28-B4Bを実装した。ゼロ幅候補を通常の半開区間へ拡張せず、`end_zero`のみを持ち、前後eventとの境界関係とshape provenanceを検証できる候補だけを`boundary_only` admissionとして受理する契約を追加した。正値point、正値core、end-zero不一致、関係不明、provenance不足は`admission_boundary_invalid`でfail-closedとする。
- `boundary_frame`は`NormalizationContract.required_zero_frames`へ単一frameとして伝播し、`same_vowel_same_frame`、`different_vowel_boundary`、`silence_gap`の固定優先順位を保持する。これにより、同一点同母音のクローズzeroを残しつつ、後続shapeの前倒し・無音越しの延長を行わない。
- `PeakValueObservation`の`boundary_only`、`boundary_frame`、`boundary_point_kind`をruntime canonical identityへ固定順序で追加した。`boundary_relation`、`boundary_action`、未所属境界配列、contract version、自由文はdebug専用としてidentityから除外した。
- B4 debug artifactの新規producerは`schema_version=1`＋`contract_version="ms28-b4-silence-v2"`とし、所属intervalの`base_event_admissions`へ境界rowを記録する。所属intervalがない場合はrootの`unassigned_boundary_admissions`へ固定reason `boundary_interval_unassigned`で保存する。B4 v1 artifact、v1回帰、完了記録は変更していない。
- B4B専用回帰として、境界受理・required-zero、同母音／別母音／無音gap分類、fail-closed、所属／未所属debug row、stage／canonical／projection同一性を追加した。B3C、B4、Preview／Writer、runtime identityの既存回帰も維持する。
- source自動検証は、B4B対象・関連回帰28件を終了コード`0`で通過し、全pytestは`1153 passed, 4 skipped`、終了コード`0`、`git diff --check`も終了コード`0`だった。`.venv`内にruff実行ファイルがないためruffは未実施である。
- 実Whisper再解析、native GUI、EXE、実MMD、正式版build、手動Debug ON/OFF比較は未実施である。B4Bはsource／決定的fixtureの自動検証完了、外部実行確認未完了として記録し、MS27の完了状態・版数・依存関係・runtime user data・spec／build設定・公開境界は変更していない。

## 3.57 MS28-B5 Help/About実装計画作成・P2/P3解消記録

- 2026-09-21にMS28-B5として、既存の「使い方」「About」メニューを有効化し、Help専用文書をポップアップ表示する計画を作成した。Aboutにはアプリversion、読み込み済みWhisper version、FFmpeg version、CPU、物理メモリ、GPU製品名を表示し、最下部に作者連絡用リンク `https://x.com/kanna3939` を配置する。
- Aboutの情報取得は、既存のversion resolver、FFmpeg locator、Windows標準の固定CIM照会、専用worker、固定状態値 `not_available` / `not_loaded` を用いる。モデル取得、音声解析、通常のFFmpeg処理、About表示時のネットワーク通信は行わず、作者リンクはクリック時だけ既定ブラウザへ遷移する。
- 実装前チェックで確認したP2（AboutのFFmpeg実行表現の曖昧さ、SystemInfoSnapshot／workerの状態契約不足、timeout・外部process設定の未固定、Help必須見出しの未固定）とP3（system_info.pyの候補表記、routing索引の未同期、snapshot時刻の未定義）を、B5計画へ反映して解消した。`collected_at`はsnapshotから除外し、timeout、出力上限、`CREATE_NO_WINDOW`、worker状態、必須Help見出し、作者リンクを固定した。
- MS28-B5のproduction code、Help文書本体、テスト、spec、buildは未実装・未検証である。MS27の完了状態、版数、依存関係、公開境界は変更していない。

## 4. 確定マイルストーン

| MS | 名称 | 直接依存 |
| --- | --- | --- |
| MS20 | RightPane Information / Warning / Output Diagnostics | MS19 closeout |
| MS21 | Per-Event Lip Adjustment / In-Memory Edit History | MS20 |
| MS22 | Long-Vowel Expression / Generation Presets | MS21 |
| MS23 | Model Profiles / Built-in Morph Name Sets | MS22 |
| MS24 | Whisper Model Selection | MS20、MS23設定基盤 |
| MS25 | MMD Delivery Package Export | MS20、MS21、MS23、MS24 |
| MS26 | Final Feature Integration / Actual MMD Closeout | MS20からMS25 |
| MS27 | Ver.1.0 Closeout / Release Boundary | MS26 |

MS28はこの確定マイルストーン系列には含めず、MS27完了後の独立した修正実装トラックとして扱う。MS28の正本は、同BlockのImplementation Planと本節のrouting記録である。

## 5. 主要コード・テスト入口

### 5.1 MS20着手時

- RightPane / Info: `src/gui_wx/right_pane.py`, `src/gui_wx/info_panel.py`
- 主画面と状態: `src/gui_wx/main_frame.py`, `src/gui_wx/ui_state.py`
- 再生位置とPreview: `src/gui_wx/playback_controller.py`, `src/gui_wx/preview_panel.py`
- 解析・診断元: `src/core/pipeline.py`, `src/gui_wx/analysis_worker.py`
- 既存RightPaneテスト: `tests/test_wx_ms16_b3_right_pane.py`
- 関連状態・回帰: `tests/test_wx_ms14_b2_state.py`, `tests/test_wx_ms14_b5_export.py`, `tests/test_ms19_b8_workspace_reset.py`

### 5.2 横断入口

- 設定永続化: `src/core/settings_store.py`, `tests/test_settings_store.py`
- Whisper timing: `src/core/whisper_timing.py`, `tests/test_whisper_timing.py`
- MMD用WAV: `src/core/mmd_wav_export.py`, `tests/test_ms17_b7_mmd_wav_export.py`
- VMD writer回帰: `tests/test_pipeline_and_vmd.py`, `tests/test_vmd_writer_intervals.py`
- build: `MMD_AutoLipTool.spec`, `build.ps1`

## 6. 作業開始時の確認

コマンドは並列実行や連結をせず、必ず一つずつ実行して結果を確認する。

```powershell
git status
git branch
git log --oneline -n 10
```

続けて本Index、正本ロードマップ、対象Implementation Plan、関連コード・テストを読む。`docs/repo_milestone.md` と `docs/Version_Control.md` は必要箇所だけを検索・範囲読みする。

## 7. Legacy / Historical文書

以下は完了済み仕様・判断・履歴の参照用である。旧MS番号と完了記録は保持し、MS20以降の計画には転用しない。

- [Ver0.4 Expansion Roadmap](Ver0_4_Expansion_Roadmap_for_Antigravity.md)
- [MS16 and Beyond Milestone Map](MS16_and_Beyond_Milestone_Map_for_Antigravity.md)
- [MS16 GUI Layout Specification](MS16_GUI_Layout_Spec_for_Antigravity.md)
- [MS18 and Beyond Roadmap](MS18_and_Beyond_Roadmap.md)
- [MS17 and Beyond Index](MS17_and_Beyond_Index.md)

MS16からMS19のImplementation Plan本文は完了履歴として変更しない。`docs/repo_milestone.md` と `docs/Version_Control.md` は、このロードマップ整理を正式記録する別作業まで更新しない。
