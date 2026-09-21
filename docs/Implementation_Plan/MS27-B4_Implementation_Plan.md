# MS27-B4 Implementation Plan

## 1. 文書情報

- 対象: MS27-B4 onefile build・SmokeLaunch・最終EXE内部監査
- 作成日: 2026-09-14
- リポジトリ: `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity`
- 計画作成時branch: `feature/MS27-implementation`
- 計画作成時HEAD: `c3e077349af7606eb8ba0872498ea6dad868bbd8`（`Implement MS27-B3 license and package audit`）
- 開始時working tree: clean。current branchのupstream表示なし。remote通信・同期確認はしていない。
- 計画状態: **Implemented / G-ARTIFACT Pass。限定補修後のbuild・SmokeLaunch・再監査を完了し、sample_data・torchテスト系・tbb12.dll由来の残存findingを解消した。B5は候補#08でG-PACKAGE Pass。B6とMS27全体のrelease readiness判定は未実施。MS26の手動確認・実MMD確認はユーザー報告として区別する。**
- 今回の成果物: 本文書へのB4実施記録と、隔離runに生成した調査用onefile EXE。B5採用候補は、B5のruntime除外補修後に再buildした`C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-final-candidate-08\source\dist\MMD_AutoLipTool.exe`、425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`である。fix-03候補はB4履歴として保持し、B5 ZIP候補はB5計画§15.4で確認済みである。
- 直近実施確認HEAD: `fbf0ce8d05774222fa38f8bced74a0aada99343a`。spec、custom hook、回帰テストはworking treeの変更としてbuild入力へ反映した。
- 正式版数: `1.0.0`。B2の実装を再実装せず、最終EXEの文字列FileVersion / ProductVersionと固定数値`(1, 0, 0, 0)`を検証する。

### 1.1 現在状態と証拠の優先関係

ユーザーの確定事項、live Git・対象file、B1/B2/B3の最終実施記録を基準にする。MS26はCloseOut A、B1はPass、B2は実装済み・直接検証Passである。B3は文書・依存台帳・入力identityを実装し、ユーザー確認済み方針に基づきG-LICENSE Passとした。B4では隔離onefile EXEの生成、SmokeLaunch、内部監査、限定補修後の再ビルドを完了し、G-ARTIFACTをPassとした。ユーザーによる手動確認と実MMD確認は、ユーザー報告として記録し、Codex自身のGUI/MMD操作とは区別する。

Block BreakdownやIndexの古いPlanned、B1/B2未実施、MS27 deferredを現在状態として転記しない。B3のG-LICENSE Passはユーザー確認済みの取得経路・license参照方針に基づく判定であり、B4のartifact Passとは別のgateである。計画策定時点の「B4未実施」およびfix-01時点のHoldは履歴として保持する。fix-03の再監査でF06〜F08を解消し、現在はG-ARTIFACT Passである。ユーザーの手動確認・実MMD確認はユーザー報告として現在状態へ反映する。

## 2. 背景と参照根拠

| 現行根拠 | 本計画で継承・照合すること |
| --- | --- |
| [MS17 Index](../MS17_and_Beyond_Index.md)、[MS20 Index](../MS20_and_Beyond_Index.md)、[Roadmap §14](../MS20_and_Beyond_Roadmap.md) | 履歴routingと現行routingを区別。MS26機能受入とMS27配布検証を分離 |
| [Block Breakdown §8〜§12](MS27_Block_Breakdown.md) | B3: G-LICENSE Pass → B4: G-ARTIFACT Pass → B5: G-PACKAGE Pass → B6、候補identity、失効規則 |
| [B1計画 §8.2〜§8.5、§15.4、§17.1](MS27-B1_Implementation_Plan.md) | Windows 11 Pro / build 26200 / 64bit、Python 3.14.3、隔離sourceの絶対cwdとPythonExe絶対path、root非接触 |
| [B2計画 §15.4〜§17](MS27-B2_Implementation_Plan.md) | project/resource優先resolver、Windows resource、直接test最終10件・2件各exit 0。最終EXEは未確認 |
| [B3計画 §15.4〜§17](MS27-B3_Implementation_Plan.md) | 10 FFmpeg実体のsize/hash、C11のpip check exit 0、M07/M08のG-LICENSE Pass、宣言/実環境差分、provenance limitationと後続責務 |
| [Release Package Manifest](../Release_Package_Manifest.md)、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、README、配布用readme | B3同期済み。必須5ファイル、追加原文、source archiveへの配慮、weights/runtime/sample除外 |
| `MMD_AutoLipTool.spec`、`build.ps1`、`pyproject.toml`、`requirements.txt`、`MMD_AutoLipTool.version.txt` | 現行onefile入力、cwd依存、収集、version接続、宣言値 |
| `src/main.py`、`src/resource_utils.py`、`src/app_version.py`、`src/core/ffmpeg_locator.py` | GUI主入口、resource・版数解決とFFmpeg探索。専用検証CLIはない |
| `src/core/whisper_models.json`、model catalog / loader関連tests | manifestは必要data、weightsは外部。package-relative resourceと静的spec testは最終EXEの代替証明ではない |
| `src/core/settings_store.py`、`generation_presets.py`、`model_profiles.py`、`whisper_model_store.py` | frozenのINIはEXE隣接、preset/profileは設定配置に従う。利用者runtimeをcopyせず隔離実行する |
| installed PyInstallerの`utils/cliutils/archive_viewer.py`、`archive/readers.py` | `-l` / `-r`、CArchiveReader、embedded PYZ閲覧の入口を確認し、今回の最終EXE監査で実行 |

`df51948..c3e0773`の変更はB3計画と関連文書の6件だけである。先行レビューで確認したcode/tests/build設定はこの差分で変更されていない。環境値やhashの過去成功は、B4実施時の入力照合を省略する根拠にはしない。

## 3. 目的

1. G-LICENSE Passで固定された入力から、既存root成果物を保護してonefile候補を作る。
2. buildとSmokeLaunchの実結果・process終了・残留を取得し、同じEXEの内部内容とWindows版数を検証する。
3. 予定入力と実同梱を対応付け、欠落・意図しない依存・未通知component・禁止dataを検出する。
4. EXE絶対path・size・SHA-256と有効な証拠をB5へ渡す。ZIP完成・通常GUI終了・MS27 readinessは後続の判定として残す。

## 4. In Scope

以下はB4の実施範囲であり、今回の隔離runで実行した。未解消findingはB3へ戻し、B4のPassには進めない。

- B1/B2証拠とB3 G-LICENSE Pass・許可入力・原文対応の再照合
- 新規所有領域への許可file単位のsource copy、copy元/先hash、絶対cwd/PythonExe、削除対象・所有者・reparse pointの確認
- 現行`build.ps1 -Clean -SmokeLaunch`による一回のonefile buildと短時間起動確認
- wrapper/取得可能な子processの終了値・終了形態、同一EXE pathの残留確認
- 新しいwarn/xref/Analysis TOCと最終EXEのCArchive/PYZ/内包ZIP等の再帰監査
- Windows version resource、内部TOML/module/metadata、resource path契約、FFmpeg/DLL、Whisper/pyopenjtalk/tiktoken/画像/license dataの照合
- Qt等の意図しない混入、新規未通知依存、weights/runtime/sample/開発tree/cache混入の判定。ユーザー指示に基づく旧Qt binding排除と、matplotlib全backend収集の限定補修を含む
- 本文書への実施記録、隔離領域の検証証拠、EXE size/hash、G-ARTIFACT判定、B5/B6 handoff

## 5. Out of Scope

- B5向けのZIP組立・展開・配布検証への移行
- version再実装、production code、依存/lock、FFmpeg binaryの変更。`MMD_AutoLipTool.spec`の変更は、今回ユーザーが明示した旧Qt binding排除とmatplotlib全backend収集の限定補修に限り対象とし、それ以外のspec/build.ps1変更は行わない。残る不備はfindingとして担当Blockへ戻す
- 新規依存・scanner・計測toolの導入、環境のupdate/reinstall、binary取得・差替え、原文不足の独自解消
- rootの`build`、`dist`、`MMD_AutoLipTool.exe`および既存ユーザー成果物の変更・削除
- runtime JSON/INIの直接作成・編集・コピー・fixture化・stage、既存weightsや利用者素材の流用
- ZIP組立・展開・配布環境の通常GUI操作・スプラッシュ目視・音声解析・正常終了確認（B5）、実MMD操作、MS26の再受入
- README等の他文書同期、license方針変更、source archive生成、B6 readiness確定、公開
- stage/commit/push/merge/tag/release、ブランチ変更、追加サブエージェント

SmokeLaunchに伴うアプリ自身の隔離先runtime生成と、runtimeを人為的に用意する操作は区別する。生成物は隔離先に留め、B5へ渡すファイル集合へ混ぜない。今回もこの境界を維持し、runtimeの配布可否はB5で別途確認する。

## 6. 前提条件とB4開始ゲート

| ゲート | 開始前の必須条件 | 現在 |
| --- | --- | --- |
| B4-G-INPUT | live branch/HEAD/差分、B1/B2の有効な証拠、B3採用component・宣言差分・具体的file許可一覧を特定 | **Pass**。B3許可入力を隔離sourceへfile単位でcopyし、runtime JSON/INI・weights・音声/MMD・tests/docsをcopyしていない |
| G-LICENSE | 選択予定componentの公式source / legal参照、取得経路、適用対象、NOTICE案内がB3で確認され、証拠IDと入力identity付きPassがある | **Pass**。B3-M07/M08を継承。exact archive/hash対応は非阻害のprovenance limitation |
| B4-G-PATH | 新規所有run、source絶対cwd、PythonExe絶対path、copy/削除対象の正規化とroot非接触が確認できる | **Pass**。初回は`run-20260914-prep-01\`、修正版再検証は`run-20260914-fix-01\`と`run-20260914-fix-03\`を使用。repo rootのbuild/distを変更・削除していない |
| B4-G-ENV | Windows/Python/PyInstaller/hooksと実環境が特定され、B3採用値との差分が評価されている | **Pass**。Windows 11 Pro build 26200 / 64bit、Python 3.14.3、PyInstaller 6.19.0を実runで確認 |
| B4-G-PROCESS | 対象processのpath/PIDと終了・残留を取得でき、既存同一候補processがない | **Pass**。wrapperのSmokeLaunch成功、5秒早期終了なし、強制停止完了、終了後同一候補の残留なしを確認 |
| 実施権限 | 別途のB4実施依頼、必要な実行権限、既存物を削除する場合は対象を特定した許可 | **確保済み**。ユーザーのB4実装依頼に基づき、既存root成果物を触らない隔離runで実施 |

G-LICENSEはB3のユーザー確認済み方針に基づきPassである。B4-G-INPUT、B4-G-PATH、B4-G-ENV、B4-G-PROCESSと実施権限を確認したうえでbuild/SmokeLaunchへ進行した。初回の内部監査で予定外componentと未解決native警告が見つかったが、fix-03で収集設定とcustom hookを限定補修し、再監査でG-ARTIFACT Passとした。任意・遅延経路に関するwarningは既知の非阻害事項として記録し、B5へ境界を渡す。

B3が要求するのは固定予定入力のlicense充足である。B4のまだ存在しない最終EXE一致証拠をB3開始条件へ逆輸入しない。B4で予定外componentが判明したら該当候補をHoldに戻す。

`requirements.txt`とB3実環境にはsetuptools/fonttools/kiwisolver/packaging/pillowの差分がある。採用値・理由・環境整合・再現制限を継承し、requirementsの再現済みとは記述しない。候補採用が未決定ならB3へ戻す。B4で値を自動的に揃えない。

## 7. 対象ファイル・入力・保存先

### 7.1 入力と責務

| 区分 | 対象 | B4で行うこと |
| --- | --- | --- |
| 唯一のrepo成果物 | 本文書 | B4の実施台帳・判定を追記。今回の限定補修以外のコード・build設定・依存・FFmpegは変更しない |
| build入力 | `build.ps1`、`MMD_AutoLipTool.spec`、`pyproject.toml`、`MMD_AutoLipTool.version.txt` | 限定補修済みspecを隔離sourceへ相対配置を保持してcopy・hash照合 |
| アプリsource | `src/main.py`と現行runtime modules、`src/core/whisper_models.json` | 実runの許可一覧をfile単位に展開。tests/cache/runtime/旧GUIの不要dataを丸ごとcopyしない。必要性不明のsourceは勝手に削らずB3と照合 |
| 画像data | `assets/icons/MMD_AutoLipTool.ico`、`assets/icons/toolbar/`の現行8 PNG、`assets/MMD_AutoLipTool_splash.png` | spec収集対象を列挙してcopy。`assets/Mockup/`等の非収集物を混ぜない |
| 埋込み文書 | `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` | G-LICENSE Pass時のbytesをcopy。B3の概要・公式参照をB4最終artifactの実配置確認と混同しない |
| FFmpeg | §7.2の10実体 | `source/FFmpeg/bin/<file>`へcopy、最終内部予定は`FFmpeg/<file>` |
| 追加license等 | B3が確定した具体的path一覧 | 内部に必要なものは承認済みspecとの対応が必要。ZIP外側だけの原文はB5入力として保持し、B4で無断収集しない |
| 実環境 | B1固定Python、PyInstaller/hooks、B3採用modules/native/data | `.venv`はcopyしない。絶対Pythonから同じ環境を利用し、入力version/path/hashを記録 |
| 関連tests | `test_app_version.py`、`test_ms27_b2_windows_version_resource.py`、`test_whisper_model_catalog.py`、`test_whisper_model_loader.py`、`test_ms17_b3_ffmpeg_locator.py` | 既存直接証拠の参照。今回も、無変更のB4標準手順でも一律再実行しない |

表のsourceカテゴリはcopy実行用のglobではない。開始前にB3一覧から各origin/destinationを具体化し、一覧にないファイルを自動追加しない。`src/`やrepo/`.venv`全体の再帰copyを代用にしない。版数resourceはbuild-onlyであり最終EXE内部data/ZIP外側の必須物ではない。

### 7.2 B3固定FFmpeg入力identity

以下は[B3計画 §15.4](MS27-B3_Implementation_Plan.md)のC13〜C15からの継承値である。今回はbinary照会・hash再取得をしていない。G-LICENSEはPass済みだが、実施開始前のcopy元、copy先、最終内部との対応を改めて取る。

| File | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| ffmpeg.exe | 542208 | `25F9F739794E20C7EBA08DD2E6C9165F79CA5C6D4423E07E9575DA0EA957E6D5` |
| ffprobe.exe | 228864 | `29221ACCA37F2BFB30CC17F1F9F219CEE0636383DFE48B4A8292B895AF988980` |
| ffplay.exe | 17744896 | `EDA12E438A5D509B0BE4D05292D58DB916C9049544A03A49BCF6B7F10A8C20F3` |
| avcodec-62.dll | 97590784 | `BE77A6E1872DF4591F090D948CD19FE3A1D0C02EF2642BF8A3307C33898F4E50` |
| avdevice-62.dll | 3683840 | `663A69109279A8A1C49AAA85FF18613C31C0FD9FE9F2DD87371C068B36B20858` |
| avfilter-11.dll | 94227456 | `59A7058E977D70C9B3A126303C44D691562CFF61080E8C89B9CD5D5168B3E847` |
| avformat-62.dll | 22062592 | `4B7E2144962F7851B828169BA162146CE77F99ED3AEBACD10959E6E4E619BD2B` |
| avutil-60.dll | 2930688 | `1B37A5835A1D895FB24A5DD0CAA84231B9EDFB753A76B5231748CE069E656259` |
| swresample-6.dll | 722944 | `C003F7911D0C160C0387D74F54A55BAF40C003405F7B322B46545988C2D76775` |
| swscale-9.dll | 12434432 | `E4089B3487534BAE9D4CAB56D694A738787C69201CB891BDE2DC3D0CC45267F9` |

FFmpeg/ffprobe versionは`N-123549-g70537ec8e6-20260318`、GCC `15.2.0`、configurationは`--enable-gpl --enable-version3 --enable-shared --enable-whisper`を含む。これは全configurationの代わりではなく、全出力の証拠元はB3-C14/C15とする。参照できない場合はB4開始前に同じ入力へversion照会を単独実行して全出力を保存し、取得不能ならHold。ffplayやDLLのversion・出所をファイル名だけから推定しない。

### 7.3 隔離path契約

`<run-root>`は初回の`C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-prep-01\`、限定補修後の`C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-fix-01\`、およびfix-03の`C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-fix-03\`を使用した。いずれも実施日時と一意な識別子を含む新規pathであり、各修正版runは前runのbuild/distを再利用していない。

| 予定path | 役割・所有境界 |
| --- | --- |
| `<run-root>\source\` | buildの絶対cwd。許可fileだけのcopy |
| `source\build\` | PyInstallerの生成Analysis/warn/xref/TOC等 |
| `source\dist\MMD_AutoLipTool.exe` | 今回runの候補EXE。固定名を維持 |
| `<run-root>\evidence\` | stdout/stderr、入力一覧、hash、process/版数/内部監査の記録。配布対象外 |
| `<run-root>\inspection\` | 必要な内部data/DLL等だけを安全に抽出して照合する領域。配布対象外 |
| `<run-root>\temp\`、`tool-cache\` | 実行単位の一時領域・tool cache。使用先を記録し既存cacheを削除しない |
| B5の別run領域 | ZIP組立・展開・配布実行用。B4では作成しない |

PythonExeは`D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity\.venv\Scripts\python.exe`を使用し、存在・絶対path・Python 3.14.3を確認した。build commandのcwdは隔離sourceの絶対pathで実行した。

## 8. 実装・監査方針

### 8.1 pathと-Cleanの前提

1. repo rootとrun-rootの絶対正規化path、既存root成果物の存在状態をread-onlyで記録する。rootのruntime本文を検査用に読み出したりcopyしたりしない。
2. sourceとその祖先・copy対象・削除対象にreparse point/junction/symlink/UNC/remoteがないことを確認する。解決後の対象がrun-root外へ出る場合はHold。
3. 標準手順は毎回新規runを作り、`source\build`、`source\dist\MMD_AutoLipTool`、`source\dist\MMD_AutoLipTool.exe`が存在しないことを確認して`-Clean`を使用する。rootの同名pathは対象にしない。
4. 既存成果物があれば自動削除・再利用しない。新しいrunへ移るか、再利用が必要なら所有者・内容・具体的な3対象と削除許可を確認する。先行runの失敗証拠も消さない。
5. `build.ps1`の相対`FFmpeg\bin`、`build`、`dist`、specとspec内相対dataが隔離source内を指すことを、copy後・実行直前に照合する。

### 8.2 buildとSmokeLaunchの証拠

現行wrapperはPyInstallerを`--noconfirm --clean`で実行し、その非ゼロexitを返す。`-Clean`のfilesystem削除とPyInstallerの`--clean`は別の動作なので、tool cacheの使用先も隔離する。run単位のTEMP/TMP、PYINSTALLER_CONFIG_DIR、必要なMPLCONFIGDIR等は値と利用先を記録し、永続環境設定を変更しない。Pythonのbytecode書込み抑止もrun環境に設定する。

SmokeLaunchは`Start-Process`→5秒待機→早期終了確認→`Stop-Process -Force`→最大30秒待機→同じEXE絶対pathの残留停止/確認である。main window到達・resource全利用・GUI通常終了・利用者による操作を証明しない。

- buildとsmokeは一回のwrapper実行を基本にし、同じCxxを両gateから参照する。成功後にsmokeだけのために同じbuildを繰り返さない。
- runnerが観測するwrapper processの最終exit code、stdout/stderr、開始/終了、cwd、PythonExe、生成EXEを記録する。成功表示だけではPassにしない。
- PyInstaller子process、onefile親/子processは区別し、PID・親PID・EXE path・観測可能な開始/終了時刻・終了形態・取得できたcodeを別欄にする。独立に採取していないPyInstaller codeをwrapperの0から複製しない。
- 強制停止されたappのcodeは取得できれば実値、取得できなければ`unknown（wrapperは強制停止codeを返さない）`とする。正常終了0を捏造しない。この強制停止code未取得だけでGUI通常終了を合格扱いすることも、正常終了失敗と断定することもしない。B4にはwrapper成功・停止完了・残留なしの証拠が必要である。
- 現行wrapperのCIM照会は`-ErrorAction SilentlyContinue`である。空結果を残留0と誤認しないよう、開始前と終了後にアクセス可否が判定できるread-only照会を行う。権限不足・path取得不可ならB4-G-PROCESS Holdとし、必要権限を申請する。
- 既存の同一候補EXE processがあれば開始しない。別pathの同名アプリを停止しない。残留停止が失敗したらPID/pathを特定して報告し、無限定のprocess killへ広げない。
- 長時間buildの待機yieldは失敗ではない。既存processを完了または明確な失敗まで追跡する。wrapperが定める5秒/30秒の検査条件とは区別する。

### 8.3 再帰内部監査

新しい`source\build\MMD_AutoLipTool\`を列挙し、実在するwarn/xref/Analysis TOC/PYZ/PKG等へ証拠pathを付ける。これらの名前は候補であり、存在しないログを取得済みと記録しない。過去build資料を同じ候補の証拠にしない。

1. EXEのsize/SHA-256を先に取得し、同じfileをCArchive readerまたはarchive viewerで全件列挙する。
2. 全embedded PYZへ降りてmodule一覧を取得する。`base_library.zip`等の内部ZIPも必要に応じて標準zip readerで確認し、外側のfile名だけで再帰監査を完了にしない。
3. TOCは`ast.literal_eval`等のデータ読取りを使い、`eval`で実行しない。抽出コードをimport/実行しない。archive entryの絶対path、`..`、重複、case衝突、展開先逸脱を検査し、必要fileだけをinspectionへ抽出する。読めないarchive/entryを無視しない。
4. B3台帳→収集経路→Analysis TOC→実内部pathをcomponent IDで対応付ける。内部fileについてsource、type、size/hash、原文/notice、採否を記録する。生成PYZ等のhashはB4で取得し、未生成のB3入力hashと同じ値を要求しない。
5. byte同梱dataは入力と比較する。binary処理によるhash差があれば、変換経路と同じoriginである根拠を確認し、説明できない差はHold。名前一致だけでB3 binaryの同一性を認めない。
6. `PySide6`/`Qt`/`shiboken`、Qt plugins/DLL、他のoptional backendをmoduleとnativeの両方で確認する。warn/xrefへの出現だけで実同梱と判定しない。実同梱で必要性/通知未確定ならB3へ戻す。B3で同梱採用と条件充足が確定したものは根拠付きで扱い、一律除外もしない。
7. 新規推移依存、vendored別実体、Python runtime、bootloader、native/dataの未対応行を残さない。未通知componentや未評価DLLがあれば候補Hold。

修正前specの`collect_submodules("matplotlib.backends")`と`excludes=[]`は、PySide6/Qt系混入の監査起点だった。修正後はmatplotlib全backend収集を削除し、旧Qt bindingの除外を明示したが、Whisper/tiktoken_ext収集とPyInstaller標準フックによる追加収集は残る。実内部を調べずにG-ARTIFACT Passへ進めない。

### 8.4 必須resourceと非同梱の照合

| 対象 | 最終EXEで必要なB4証拠 | 境界 |
| --- | --- | --- |
| 版数 | Windows resourceの文字列FileVersion/ProductVersion=`1.0.0`、FixedFileInfo両値=`(1,0,0,0)`。実PEから取得 | source resourceの再読みだけでは不可 |
| app version/resource | 内部`pyproject.toml`のname/versionと入力bytes、app_version/resource_utilsの実module、`_MEIPASS`基準の解決契約との対応 | 古いinstalled metadata `0.4.0.0`が入れば値/出所/参照経路を記録し、影響があればB2/B3へ戻す |
| FFmpeg | 内部`FFmpeg/`の10実体と追加nativeの有無、size/hash/収集元、DLL import依存の解決対応 | `FFmpeg/bin`→`FFmpeg`の配置差を維持。ffplay/7 DLLを勝手に削らない |
| FFmpeg path契約 | 最終moduleと配置がrepo-local、`_MEIPASS/FFmpeg`、PATHの探索契約に一致すること | 開発repo/PATH由来binaryのversion実行をbundled解決証拠にしない |
| Whisper | `src/core/whisper_models.json`の入力bytes/schema/3モデル、Whisper packageの実assets一覧とhash、必要modules | `.pt` weights/`.part`は除外。manifestをruntime JSONと誤分類しない |
| pyopenjtalk | 実package data、辞書/COPYING、拡張module/DLLと原文対応 | 辞書の存在だけを実変換成功にしない。buildのための自動downloadを解決策にしない |
| tiktoken | tokenizer関連module/data、tiktoken_ext namespaceの所有distributionと収集先 | 独立distribution/versionを仮定しない |
| 画像 | ICO、toolbar 8 PNG、splash PNGの内部pathと入力bytes | 表示・目視品質はB5 |
| license docs | 内部rootのLICENSE/NOTICE/THIRD_PARTY_LICENSESと、B3が内部配置を要求した追加原文 | ZIP外側の必須5/追加一式の実配置はB5 |

必要に応じて検証済みEXEからFFmpeg群をinspection内の専用フォルダへ揃えて抽出し、絶対pathを指定したffmpeg/ffprobeの`-version`を別々に実行する。これは「EXE内にあったbinaryの起動」の証拠であり、アプリの実行時locatorがそれを選択した証拠とは区別する。DLLの欠落・アーキテクチャ不一致はHold。音声やGUI操作を伴う実際の利用経路はB5へ渡す。

`src/main.py`には`--version`や`--self-test`の検証CLIはない。架空のオプションを起動検証に使わない。B4のresource path証拠は最終内部配置・内包コードの契約・同一EXEのsmokeを対応付けるもので、全resource利用や実スプラッシュ表示まで確認済みとしない。実測できない実行時pathは未確認欄でB5へ渡す。B4必須の内部path/内容が不明な場合はB5へ繰り越してPassにしない。

禁止内容はCArchive、PYZ、内部ZIP、datas/binariesの全対象から確認する。

- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`、backup/一時コピー、利用者pathを含む保存状態
- runtime `models/`、Whisper weights/checkpoint/`.part`、sample、テスト音声/TEXT/PMX/PMD/MMD、生成VMD/WAV/report
- 生の開発source tree、tests/docs/.git/.venv/.agent/.agents/.codex/AGENTS.md、cache/temp/logs/台帳/旧build残骸
- build-only version resource/spec/build設定の意図しないdata同梱

実行用module archive、必要manifest、辞書、tokenizer assetsは生の開発treeと区別する。`*.bin`や`*.json`全除外、module名中の`models`だけの判定はしない。必要な第三者対応ソース/本文はB3の明示許可行に従い、一般のsource除外でライセンス上必要な資料を落とさない。bytecodeの`co_filename`等の文字列と実source file同梱も区別し、絶対path情報の扱いは別findingとして評価する。

## 9. 詳細ステップ

| 順序 | 実施内容 | 完了証拠・停止条件 |
| --- | --- | --- |
| B4-01 | live Git、B1/B2/B3、G-LICENSE、採用値/原文/許可一覧を再照合 | G-LICENSEがPassでない場合はここで候補実行を止め、計画/不足報告のみ |
| B4-02 | Windows/Python/PyInstaller/hooks、process観測権限、入力hash、root成果物の非接触baselineを固定 | 実行環境不明、未評価差分、必要権限不足はHold |
| B4-03 | 新規runを作り許可sourceをfile単位でcopy、両側hash、絶対cwd/PythonExe、3削除対象・所有境界を確認 | 意図しないcopy/reparse/既存物はHold。無断削除しない |
| B4-04 | 一回の`build.ps1 -Clean -SmokeLaunch`を実行しwrapperの終了まで追跡 | 最終exitと成功結果の両方を取得。失敗と途中出力を保持 |
| B4-05 | 同一EXE process残留の信頼できる照会、生成EXE size/hash、root非接触を確認 | 残留不明/残留あり、rootへの副作用、候補特定不可はHold |
| B4-06 | 新warn/xref/TOCと最終EXEを再帰監査しB3台帳へ対応 | 欠落/未知依存/未通知/禁止data/監査不能はHold。B3等へfindingを渡す |
| B4-07 | 実PE版数、内部TOML/resource/FFmpeg/辞書/tokenizer/画像/licenseを照合 | 文字列・数値・bytes・配置・必要DLLを別証拠化。§8.4境界を維持 |
| B4-08 | 監査後EXE hash、入力変更の有無、全gate/AC/finding/staleを判定 | 同一candidateの有効な証拠だけを採用。別EXEの成功を混ぜない |
| B4-09 | 本書へPass/Holdと証拠を記録しB5/B6へhandoff | 許可file・EXE identity・未検証を渡す。B5を自動開始しない |

以下は実施したコマンド形と、後続検証で使用するコマンド形である。今回のbuild/SmokeLaunch、archive viewer、EXE hashはC06〜C09として実行した。stdout/stderrは実行時consoleで確認し、永続logは作成していない。山括弧部分を使う場合も解決済み絶対pathへ置き換え、一つずつ実行する。pipelineやコマンド連結を使わない。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -PythonExe "<absolute-python-exe>" -Clean -SmokeLaunch
```

このコマンドのrunner cwdは必ず`<absolute-isolated-source>`とする。`-PythonExe`を省略しない。起動/実行権限が必要なら、解決済みcwd・対象・操作で申請する。

```powershell
& "<absolute-python-exe>" -B -m PyInstaller.utils.cliutils.archive_viewer -r "<absolute-candidate-exe>"
```

```powershell
Get-FileHash -LiteralPath "<absolute-candidate-exe>" -Algorithm SHA256
```

VersionInfoのOS照会と既存`pefile`等によるPE resource読取りを使い、FileVersion/ProductVersion文字列と固定数値を別々に記録する。PyInstallerのtext resource readerだけで最終EXEを検証したとしない。使用する既存readerの入口/実行コマンドは実施台帳へ残し、追加tool導入で穴埋めしない。

## 10. 状態遷移 / データ契約

```text
Planned / G-LICENSE Pass（ユーザー確認済み方針）
  → B4入力・path・environment・process gate Pass
  → onefile build + SmokeLaunch
  → 同一EXE内部・版数・非混入監査
  → B4 Pass / G-ARTIFACT Pass → B5 → B6

必須失敗・不足・入力不一致 → B4 Hold → 原因に応じB1/B2/B3/限定補修へ
補修や入力変更 → 影響証拠stale → 再照合・新runで必要検証
```

### 10.1 候補とfile契約

- candidate ID = run-id + 実行HEAD/対象差分 + 入力集合identity + EXE SHA-256。別runを同じ候補と仮定しない。
- input行 = component ID、origin絶対path、source相対path、size/hash、役割、B3許可/原文証拠、copy先hash、採用version、owner。
- internal行 = 親archive/entry path、種別、実size/hash、origin/収集経路、B3 component/原文、required/excluded/採否、Cxx/Mxx、未確認。
- process行 = wrapper/PyInstaller/onefile親/子の役割、PID/親PID、path、開始/終了、exitの取得方法、終了形態、残留照会の成否。
- Windows version行 = EXE hash、reader、全取得言語テーブル、文字列2値、固定数値2組、Translation、実結果/判定。複数テーブルに不一致があれば見逃さない。
- final handoff行 = EXE path/size/hash、B3 G-LICENSE、G-ARTIFACT、全証拠、P1/P2/P3/Uxx、B5 required/除外/実施結果、B6未確認事項。

### 10.2 hashと失効規則

code、pyproject、spec、version resource、Python/runtime/native/data、FFmpeg、埋込みlicense文書・原文が変われば、影響するbuild/内部/版数/smokeをstaleにし、そのEXEを使うB5 ZIP/配布証拠も再判定する。単に同じfilename/versionでは再利用できない。

外側readme/licenseだけの変更はB5 ZIP証拠を失効させる。B4を再利用する場合は、その文書が埋込み対象ではなく、候補/入力bytesとbuild条件が不変である根拠が必要である。現行NOTICE/THIRD_PARTY_LICENSESは内部にも入るので外側のみと扱わない。

非配布の計画/台帳だけの変更は、candidate bytesへの影響なしを確認して証拠を再利用できる。Git commitの有無だけで失効を決めない。bit単位の再build再現性はこの計画の必須条件に追加しないが、各runの実入力と実出力hashは必須とする。

## 11. 最小検証と終了コード

B4実施では以下を必須確認として扱った。今回のbuild/SmokeLaunch・archive・PE版数の実結果は§15.2へ追記し、B5以降の検証は当時の後続責務として残した。B5の後続実施結果はB5計画§15.4を正本とする。

| 検証 | 最小要件 |
| --- | --- |
| 入力/隔離 | G-LICENSE Pass、copy許可一覧、origin/copy hash、環境/path/削除所有境界 |
| build/smoke | 一回のwrapper、最終exit 0、成功結果、実EXE、早期終了なし、停止完了、信頼できる残留0 |
| 内部監査 | 最新warn/xref/TOCとEXE/PYZ/必要な内包ZIP全体、必須/除外/原文対応 |
| 版数/resource | 最終PEの文字列/固定数値、TOML、実moduleとdata配置、FFmpeg/DLL等の§8.4照合 |
| 同一性 | build後と監査後EXE hash、入力失効なし、B5へ渡す実fileの特定 |

full pytest/compileall、同じ成功済み検証の反復、MS26再受入は標準手順へ追加しない。今回も実行しない。変更・失敗が生じた場合は、その原因に近い補修と検証を担当範囲へ戻す。修正が必要という理由だけでB4の権限をcode/test変更へ拡張しない。

実process exitはrunnerの最終値を使う。未実行=`not run`、取得不能=`unknown`、processを伴わない照合=`N/A（照合理由）`。PowerShell cmdletを直前のnative `$LASTEXITCODE`で判定しない。wrapperの0を全子processの0へ複製しない。失敗と再試行は別Cxxで残す。

必須検査processの非ゼロ、必要結果の欠落、監査不能はHold。`rg`該当なしや`git diff --no-index --check`の終了値は診断と合わせて判定し、差分由来の1を無条件の失敗/成功へ変換しない。強制停止app codeの未取得は§8.2の限定扱いとし、wrapper exitや残留確認の未取得とは区別する。

## 12. 受け入れ条件

| ID | 必須条件 | 主証拠 |
| --- | --- | --- |
| MS27-B4-AC01 | B1/B2とlive入力が対応し、B3予定入力にG-LICENSE Passがある | baseline、B3 gate/許可/原文ID |
| MS27-B4-AC02 | source絶対cwd/PythonExe絶対path、copyと3削除対象の所有・正規化・root非接触が確認済み | input/path ledger、前後照会 |
| MS27-B4-AC03 | 固定onefile EXEが生成されwrapper exit 0とbuild成功結果が揃う | Cxx、EXE path/size/hash |
| MS27-B4-AC04 | 5秒早期終了なし、強制停止完了、照会成功に基づく残留0、wrapper/子processの区別がある | process ledger。通常終了はB5 |
| MS27-B4-AC05 | 最新warn/xref/TOCと最終EXE再帰内部の対応が取れる | archive/internal ledger、未解決の監査欠落なし |
| MS27-B4-AC06 | 最終EXEのFileVersion/ProductVersion文字列がともに1.0.0、固定数値が両方1,0,0,0 | 実PE読取り、候補hash |
| MS27-B4-AC07 | 内部TOML/name/version、version modules、resource pathと必要dataが§8.4契約に一致 | internal行、入力bytes、B2との対応 |
| MS27-B4-AC08 | B3 FFmpeg10実体/DLLとWhisper/pyopenjtalk/tiktoken/画像/licenseが対応し、必要nativeに未評価欠落がない | 原文/収集元/internal bytes・配置の照合 |
| MS27-B4-AC09 | Qt等の意図しない混入、新規未通知依存、weights/runtime/sample/開発tree/cache混入が未解決で残らない | 全archive/native/分類行、B3採否 |
| MS27-B4-AC10 | 監査前後の同一EXE identityと有効証拠が揃い、未解消P1/P2なし、P3/Uxxの担当・影響が明確 | gate/finding/stale ledger |
| MS27-B4-AC11 | B5へEXE identity・必要文書一覧・除外・通常終了等の未検証を渡し、B6にreadiness未実施を残す | §16 handoff |

**Pass:** 全ACを満たし、G-ARTIFACT Passを根拠付きで記録する。B5のZIP/通常GUI確認がB4実施時に未実施であったことは、B4の必須内部監査不足の代替にも、B4失敗の理由にも使わない。

**Hold:** 開始gate未充足、必須process/結果の失敗・未取得、未確認内部、版数不一致、必要data欠落、未評価依存、禁止data混入、root副作用、失効、未解消P1/P2がある場合。今回のfix-03候補では、これらの条件に該当する未解消P1/P2は確認されなかった。

実施判定: **AC01〜AC10はfix-03候補について充足。AC04のPID/path/残留判定はwrapper内で実行されたが、個別PIDの永続ledgerは保存していない。AC11は当時B5/B6へ候補identity、内部監査結果、ユーザー報告、未確認事項をhandoffした。その後B5は候補#08でZIP・配布環境確認を完了しG-PACKAGE Pass。B6の公開readinessは未着手。**

## 13. リスク・P1/P2/P3・Hold

| ID | 未確認・リスク | 解消根拠 / owner |
| --- | --- | --- |
| MS27-B4-U01 | B3 G-LICENSEはPass済み。exact archive/source correspondenceと追加配置は未確認 | B3-M08のユーザー確認済み方針を継承。最終artifactの実配置・新規componentはB4監査で確認し、矛盾時はB3へ戻す |
| MS27-B4-U02 | 解消。実run絶対path、環境、copy境界、process照会を実施 | C06〜C08、§6〜§8.2 / B4 |
| MS27-B4-U03 | 解消。build/SmokeLaunch/残留/EXE size/hashを取得 | C06〜C09 / B4 |
| MS27-B4-U04 | **F01〜F04として顕在化。PySide6/Qt/shiboken、sample_data、torchテスト系、native警告が最終同梱/出力に現れた** | F01〜F04をB3へ戻し、採否・収集・依存を確定 / B3 |
| MS27-B4-U05 | 解消。最終PEの文字列版数とFixedFileInfoを実読取り | C10〜C12 / B4 |
| MS27-B4-U06 | B4時点ではユーザーから手動確認通過・実MMD問題なしの報告を受領し、詳細操作ログ、開発環境からの独立性、ZIPは未確認だった | ユーザー報告は手動証拠として記録。ZIP単体性・配布環境・processの詳細は後続B5候補#08で確認済み |
| MS27-B4-U07 | Python 3.11/3.12互換性、MS27 readiness・公開未確認 | B1実環境3.14.3と区別。追加互換性検証をB4へ自動追加しない / B6 |
| MS27-B4-U08 | fix-03でもmatplotlib/TBB等の任意・遅延経路に関する静的解析warningは残る | 成果物内の禁止対象は0件、主要runtime moduleは存在し、SmokeLaunchとユーザー確認は通過。warningは非阻害の既知記録として保持し、B5では除外補修後の候補#08を再検証 |

Fxxは実際に確認した問題に割り当てる。P1は既存データ破棄や重大な情報混入等、P2は必須監査/版数/依存/停止確認の欠陥等、P3は証拠の意味を変えない軽微な記録不整合等とする。gateを満たせない問題をP3へ下げて通過させない。

各findingには対象candidate、発見条件、確度、影響AC、severity、owner、解消条件を持たせる。新規未通知componentはB3、版数はB2、隔離/環境契約はB1/B4、実機能の補修は別途限定範囲へ戻す。MS26 CloseOut Aやユーザー実MMD報告を書き換えない。B2-R05の原因・影響未確定、PMX hash独立取得不可もB4の新たな合格条件にしない。

## 14. Codex実施時の注意

- 今回はB4の隔離build、SmokeLaunch、内部監査を実施し、結果を本書へ追記した。追加サブエージェントは起動していない。
- 将来もshellは1 commandずつ。並列/連結/pipelineで終了値・cwd・所有境界を曖昧にしない。
- 新規runを基本にし、古いbuild/distを消すことで失敗を隠さない。長い処理のyieldだけで停止・再起動・重複buildを指示しない。
- GUI利用者操作や専用診断CLIを存在すると仮定しない。観測手段が不足する場合は不足証拠とownerを記録する。
- 実施のために必要な計測方法を具体化しても、runtime変更・tool導入・code/spec修正を黙って採用しない。
- B4の証拠をB5の通常終了・配布独立性・MS27公開準備完了へ拡張しない。

## 15. Evidence ledger / 実施記録

### 15.1 IDと共通schema

- `MS27-B4-Cxx`: 単独commandと最終process結果。planning/implementation/revalidationを明示。
- `MS27-B4-Mxx`: gate採否、file/原文/内部/配置の照合。processがない判断はN/A。
- `MS27-B4-Fxx`: P1/P2/P3 finding。再試行・解消証拠を結び付ける。
- `MS27-B4-Uxx`: §13の未確認/不足。未実施を実行失敗と混同しない。

```text
ID / phase / owner / gate・AC:
日時・実施者 / branch・HEAD・working tree差分 / run-id:
cwd絶対path / 単独commandまたは照合対象 / 権限 / 親子processの役割:
OS / PythonExe絶対path・version・architecture / PyInstaller・hooks / run環境:
入力origin・copy相対path・size・SHA-256 / B3採用・license証拠:
開始・終了 / stdout・stderr所在 / 実件数・期待結果・実結果:
最終exit codeと取得元 / 子processの終了形態 / N/A・unknown・not runの理由:
EXE絶対path・size・SHA-256 / 親archive・内部entry / 原文対応:
判定 / Fxx・Uxx / 再試行元ID / stale対象・非失効根拠 / B5・B6引継ぎ:
```

### 15.2 今回の計画作成記録

| ID | phase / 操作 | 結果 | exit |
| --- | --- | --- | --- |
| MS27-B4-C01 | planning / `git status --short --branch` | §1のbranch、開始時clean | 0 |
| MS27-B4-C02 | planning / `git branch -vv` | c3e0773、current upstream表示なし | 0 |
| MS27-B4-C03 | planning / `git log --oneline -n 10` | B3文書実装commit、先行B1/B2履歴 | 0 |
| MS27-B4-C04 | planning / `git rev-parse HEAD` | §1の完全HEAD | 0 |
| MS27-B4-C05 | planning / `git diff --name-status df51948..HEAD` | B3計画/NOTICE/README/THIRD_PARTY_LICENSES/Manifest/配布readmeの6件 | 0 |
| MS27-B4-M01 | planning / 本書§2の資料と現行コード・先行確認の照合 | G-LICENSE Pass済み入力と、B4固有の実施許可・開始ゲートを前提とする計画を策定 | N/A（静的照合） |
| MS27-B4-C06 | implementation / 隔離source cwdで`powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -PythonExe "D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity\.venv\Scripts\python.exe" -Clean -SmokeLaunch` | PyInstaller onefile build成功。`Smoke launch passed: dist\MMD_AutoLipTool.exe`。wrapper最終exit 0。wrapper内で5秒監視、PIDによる強制停止、同一絶対pathの残留確認まで成功。stdout/stderrは実行時consoleのみで永続logは作成していない | 0 |
| MS27-B4-C07 | implementation / `Get-Item`で隔離候補EXEを照合 | `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-prep-01\source\dist\MMD_AutoLipTool.exe`、480646351 bytes、2026-09-14 12:10 | 0 |
| MS27-B4-C08 | implementation / `Get-FileHash -Algorithm SHA256`で隔離候補EXEを照合 | `72D14CFD388D07BC5D5BC7772A4D5A79C5578C89C43582A4EB855F4A30803571` | 0 |
| MS27-B4-C09 | implementation / PyInstaller archive viewer `-r`で候補EXEを再帰列挙 | CArchive/PYZを含む再帰列挙に成功。PKG内にFFmpeg 10実体、license 3文書、manifest/resource、PySide6/Qt、sample_data、torchテスト系を確認 | 0 |
| MS27-B4-C10 | implementation / `(Get-Item ...).VersionInfo.FileVersion` | 最終EXE文字列 `1.0.0` | 0 |
| MS27-B4-C11 | implementation / `(Get-Item ...).VersionInfo.ProductVersion` | 最終EXE文字列 `1.0.0` | 0 |
| MS27-B4-C12 | implementation / `VersionInfo.FileVersionRaw` と `ProductVersionRaw` | FileVersion/ProductVersionともにMajor=1、Minor=0、Build=0、Revision=0 | 0 |
| MS27-B4-M02 | implementation / CArchiveReaderでlicense 3文書の内部bytesと隔離sourceをSHA-256照合 | `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`の3件が全て一致 | N/A（静的照合） |
| MS27-B4-M03 | implementation / CArchiveReaderでFFmpeg 10実体の内部bytesと隔離sourceをSHA-256照合 | FFmpeg 10件が全て一致。内部配置は`FFmpeg/<file>`、sourceは`FFmpeg/bin/<file>` | N/A（静的照合） |
| MS27-B4-M04 | implementation / PKG-00.tocとPYZ-00.tocの対象path照合 | PySide6/shiboken6 148件、`matplotlib\\mpl-data\\sample_data` 15件、`torch\\testing` 216件、`torch\\fx\\passes\\tests` 6件。`tbb12.dll`はPKG内に該当なし | N/A（静的照合） |
| MS27-B4-F01 | implementation / 最終PKG/PYZでPySide6・Qt6・shiboken6を確認 | **P2 Hold**。現行sourceにPySide6実装importはなく、wxPython構成に対する必要性・通知・採否が未確定。owner=B3/spec収集設定 | N/A |
| MS27-B4-F02 | implementation / 最終PKGでmatplotlib sample_data 15件を確認 | **P2 Hold**。B4のsample data除外境界に反する候補。owner=B3/spec収集設定 | N/A |
| MS27-B4-F03 | implementation / 最終PKG/PYZでtorch testing 216件、torch.fx.passes.tests 6件を確認 | **P2 Hold**。アプリ実行に必要な開発・テストtreeか未分類。owner=B3/spec収集設定 | N/A |
| MS27-B4-F04 | implementation / build console warningで`numba`の`tbb12.dll`未解決を確認。PKG内にも該当なし | **P2 Hold**。必要nativeかoptional経路か、実音声処理への影響が未確認。owner=B3/依存・native台帳 | N/A |
| MS27-B4-C13 | repair / `MMD_AutoLipTool.spec`の限定補修 | `collect_submodules("matplotlib.backends")`を削除し、PySide6/PySide6_Addons/PySide6_Essentials/shiboken6/PySide2/PyQt5/PyQt6を`excludes`へ追加。ユーザー指定の旧Qt binding排除に限定 | N/A（apply_patch） |
| MS27-B4-C14 | repair / `tests/test_whisper_model_catalog.py`のspec静的契約テスト | 限定補修を検査するテストを追加。7 tests passed | 0 |
| MS27-B4-C15 | repair / 新規隔離sourceで`build.ps1 -Clean -SmokeLaunch`を再実行 | `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-fix-01\source\dist\MMD_AutoLipTool.exe`を生成。`Smoke launch passed`、Build completed | 0 |
| MS27-B4-C16 | repair / `Get-Item`で修正版候補EXEを照合 | 修正版候補、440432572 bytes、2026-09-14 12:57 | 0 |
| MS27-B4-C17 | repair / `Get-FileHash -Algorithm SHA256`で修正版候補EXEを照合 | `86963AD5042907CCB894DD05B96EE3420F8B7EDAEA8B234FA6C67051ED4FD044` | 0 |
| MS27-B4-C18 | repair / PE `FileVersion` / `ProductVersion`文字列を照合 | 両方とも`1.0.0` | 0 |
| MS27-B4-C19 | repair / PE `FileVersionRaw` / `ProductVersionRaw`を照合 | 両方ともMajor=1、Minor=0、Build=0、Revision=0 | 0 |
| MS27-B4-C20 | repair / `MMD_AutoLipTool.spec`へ`build_hooks`を接続し、Torch標準hookの過剰な全サブモジュール収集を置換 | `build_hooks/hook-torch.py`を追加。Torch data/native libraryを維持し、`collect_submodules("torch")`を使用しない | N/A（apply_patch） |
| MS27-B4-C21 | repair / `tests/test_whisper_model_catalog.py`を再実行 | specとcustom hookの契約を含む`7 passed` | 0 |
| MS27-B4-C22 | repair / 新規隔離sourceで`build.ps1 -Clean -SmokeLaunch`を再実行 | `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-fix-03\source\dist\MMD_AutoLipTool.exe`を生成。PyInstaller onefile build成功、SmokeLaunch成功。wrapper最終exit 0 | 0 |
| MS27-B4-C23 | repair / `Get-Item`でfix-03候補EXEを照合 | 425758214 bytes、2026-09-14 13:34 | 0 |
| MS27-B4-C24 | repair / `Get-FileHash -Algorithm SHA256`でfix-03候補EXEを照合 | `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C` | 0 |
| MS27-B4-C25 | repair / PE `FileVersion` / `ProductVersion`をfix-03候補で照合 | 両方とも`1.0.0` | 0 |
| MS27-B4-M07 | repair / CArchiveReaderでfix-03候補のPKG/PYZを再帰監査 | matplotlib package/mpl-data/sample_data、旧Qt、Torch test/TensorBoard、Numba tbbpool/tbb12の対象件数はすべて0。Whisper、Torch主要module、Numbaは存在 | N/A（静的照合） |
| MS27-B4-M08 | repair / fix-03 build warningとarchive結果を照合 | TorchのTensorBoard収集warningは消失。任意・遅延経路のmatplotlib/TBB参照warningとWindows外部path由来の`libgomp`照会は残るが、成果物内同梱は確認されず、非阻害warningとして分類 | N/A（静的照合） |
| MS27-B4-M09 | user report / B4候補の手動確認・実MMD確認 | ユーザーから手動確認通過、実MMDでも問題なしとの報告を受領。Codex自身のGUI/MMD操作ではない | N/A（ユーザー報告） |
| MS27-B4-M05 | repair / 修正版候補のPKG/PYZとbuild warningを再照合 | PySide6/shiboken6/Qt6/PySide2/PyQt5/PyQt6は該当なし。`sample_data` 15件、`torch\\testing`系、`torch\\fx\\passes\\tests`系は残存。`tbb12.dll`はPKG内に該当なし。 | N/A（静的照合） |
| MS27-B4-M06 | repair / installed hook・source・xrefを原因照合 | sample_dataはPyInstallerの`hook-matplotlib.py`がmatplotlibのデータディレクトリ全体をdatas収集するため残る。torchテスト系は`hook-torch.py`の`collect_submodules("torch")`が原因。tbb12.dllはWhisper `timing.py`のnumba経路にある`numba\\np\\ufunc\\tbbpool.cp314-win_amd64.pyd`の未解決依存として出力された。 | N/A（静的照合） |
| MS27-B4-F05 | repair / 修正版候補で旧F01を再検査 | **Resolved for fix-01 candidate**。PKG/PYZの対象文字列に該当なし。旧F01はprep-01候補に紐付く履歴として保持し、修正版候補へ持ち越さない | N/A |
| MS27-B4-F06 | repair / 修正版候補でsample_dataを再検査 | **Resolved in fix-03**。matplotlib package、mpl-data、sample_dataの成果物内対象件数は0。specの`matplotlib`除外とcustom hookの採用を確認 | N/A |
| MS27-B4-F07 | repair / 修正版候補でtorch testing系を再検査 | **Resolved in fix-03**。Torch test/TensorBoard対象件数は0。custom `hook-torch.py`で`collect_submodules("torch")`を使用せず、主要Torch moduleは保持 | N/A |
| MS27-B4-F08 | repair / 修正版候補で`tbb12.dll`を再検査 | **Resolved in fix-03**。`numba.np.ufunc.tbbpool`、`tbb12`の成果物内対象件数は0。Numba主要moduleを保持し、TBBは任意backendとして除外 | N/A |

上記のほかに資料のGet-Content/rg読み取りを実施した。runtime関連sourceの初回検索で存在しない`preset_store.py`/`model_profile_store.py`を指定してexit 1となり、`rg --files`で実在する`generation_presets.py`/`model_profiles.py`を特定して照合した。これはアプリの実行失敗ではない。

FFmpeg version、B2直接test、B3 pip checkの値は先行IDの継承であり、今回FFmpeg version照会・B2直接test・pip checkを再実行していない。FFmpeg 10実体の内部bytesはfix-03候補でも再照合していないため、B3/B4先行記録を有効な入力identityとして継承する。fix-03 build consoleには任意・遅延経路のmatplotlib/TBB参照warningとWindows外部path由来の`libgomp`照会が残ったが、対象依存の成果物内同梱は確認されず、主要runtime module、SmokeLaunch、ユーザー手動確認、実MMD確認は通過報告済みである。

### 15.3 将来のB4実施台帳

| 記録群 | 現在 | 将来必要な内容 |
| --- | --- | --- |
| B3 gate / input / environment | G-LICENSE Pass、B4-G-INPUT/PATH/ENV Pass | B5で候補#08の有効性を確認済み。B6でrelease readinessを照合 |
| path ownership / process | Pass | B5で新規領域へのZIP組立・展開と独立性を確認済み |
| build / EXE | fix-03のwrapper/build Pass、B4履歴identity取得済み | spec / 埋込み文書変更によりB5は候補#08を別途再build・再監査。B5の採用identityは§15.4 |
| archive / version / resources | fix-03候補のarchive再列挙・PE版数照合済み。除外対象非混入、主要runtime module保持、G-ARTIFACT Pass | B5候補#08のZIP側配置・展開内容・配布環境からの独立性を確認済み |
| findings / stale / handoff | 旧findingは候補別履歴として保持。F06〜F08はfix-03でResolved。B5は候補#08でG-PACKAGE Pass | fix-03候補の履歴、候補#08のB5証拠、B6の未確認事項をhandoff |

Cxxは既存IDの続きに実施順で割り当てた。失敗・修正版・再検査を同じIDへ上書きしない。旧F01〜F04はprep-01候補、F05〜F08はfix-01候補の再監査結果である。F06〜F08はfix-03の再監査でResolvedとし、fix-03候補を当時のB5入力候補へ更新した。後続B5ではspec / 埋込み文書変更により候補#08を再buildし、ZIP・配布環境確認を完了した。公開readinessは未確認である。

## 16. B5 / B6へのhandoff

| owner | B4から渡すもの | 後続の責務 |
| --- | --- | --- |
| B5 | G-LICENSE/G-ARTIFACT、候補EXE絶対path/size/hash、内部/版数/FFmpeg/data/原文対応、全finding、入力失効状態 | B4時点のhandoff後、B5はspec / 埋込み文書の変更により候補#08を新規領域で再build・再監査し、起動後runtimeを再圧縮せずにZIP組立・展開を完了 |
| B5 | 必須5ファイルとB3の具体的追加license/対応物一覧、除外一覧、`MMD_AutoLipTool_v1.0.0_Windows_onefile.zip` | 実ZIP内容/hash、実スプラッシュ、GUI/resource/FFmpeg/辞書/tokenizer利用、モデル未配置、正常終了code、残留、開発repo/Python/PATHからの独立性を確認済み |
| B6 | B4 Pass/HoldとAC、B3へ戻した差異/最終採否、P1/P2/P3/Uxx、未確認・再現制限 | B1〜B5の候補#08・有効証拠・最終license/readinessを照合。routing等の最終状態同期と公開は別工程 |

B5へ渡すのは`source/dist`全体ではなく、特定hashのEXEとB3許可文書である。B4 inspection/temp/cache/error.log/生成runtime/台帳は配布しない。prep-01とfix-01の候補は旧finding付きの履歴として保持し、fix-03のSHA-256 `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`は当時のB5再確認対象としてhandoffした。B5はその後のspec / 埋込み文書変更に応じて候補#08を再buildし、ZIP単体性、配置、配布環境、正常終了codeを確認した。

## 17. ユーザー確認境界と完了条件

今回のB4実施では、正式版数、基本配布方式、FFmpeg選択入力に加え、ユーザー確認済みのG-LICENSE取扱方針を継承した。B4固有の実行権限・絶対path・環境・入力copyを確認し、binary選択をやり直さずに隔離buildを行った。旧Qt binding排除に続くfix-03でmatplotlib data、Torch test系、TBB任意backendの過剰同梱・未解決警告を限定補修し、G-ARTIFACTをPassとした。ユーザーから手動確認通過と実MMD問題なしの報告を受領したが、これはユーザー報告でありCodex自身のGUI/MMD操作ではない。

将来、必要なOS/processアクセス権、既存成果物の削除、依存更新/binary差替え、収集設定やcode補修、原archive提供/配布方法変更が必要になった場合は、既存許可を確認し、対象・根拠・影響・不足する選択を具体化する。必要な承認がない操作へ進まず、独立したread-only照合は継続する。

- **今回の完了:** 旧Qt binding排除、custom Torch hookによる過剰収集抑制、対象test、fix-03隔離build、SmokeLaunch、EXE size/hash、PE版数、archive内部のread-only再監査、F06〜F08の原因解消を実施し、本書へ結果を追記した。ユーザーから手動確認通過・実MMD問題なしの報告も受領した。G-ARTIFACTはPassである。
- **B4実施の完了:** §12のAC01〜AC10とG-ARTIFACT Pass、fix-03候補の有効identity、B5への入力handoffが揃った。B5は後続の候補#08でZIP・配布環境確認を完了した。公開readinessはB6で未実施である。
- 完了報告後に候補build、後続Block、Git変更、公開へ自動移行しない。
