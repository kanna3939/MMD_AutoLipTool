# MS27-B6 Implementation Plan

## 1. 文書情報

- 対象: MS27-B6「最終照合・文書同期・release readiness判定」
- 作成日: 2026-09-17
- 計画作成時branch: `feature/MS27-implementation`
- 計画作成時HEAD: `61adb556c3c7c1c459438c29938ae422e77e553f`（`61adb55 Complete MS27-B5 package verification`）
- 開始時working tree: clean。本文書は新規作成。
- 状態: **CloseOut confirmed / 2026-09-18にB6監査・必要な状態同期を完了。ユーザー決定とremote確認に基づくrelease readinessはG-READY Pass。同日のユーザー明示決定によりMS27 CloseOutを確定した。** B1〜B5の到達状態は既存記録として継承する。公開は別の未実施工程である。
- 計画策定時の書込み範囲: 本ファイルのみ。後述のB6手順、対象文書更新、追加検証は当時の実行結果や許可ではなかった。2026-09-18の実施記録と状態同期は§15.2に分離する。
- 判定対象: 候補#08の特定EXE / ZIP bytesと、それに対応するB1〜B5の証拠。GitHub Releaseの公開作業は含めない。

### 1.1 根拠と参照の優先関係

1. 今回のユーザー指示と[AGENTS.md](../../AGENTS.md)の作業境界を適用する。
2. [MS17 Index](../MS17_and_Beyond_Index.md)を入口とし、現行routingは[MS20 Index](../MS20_and_Beyond_Index.md) §2と「§3.48 MS27-B5実装・配布候補確認記録」、範囲は[Roadmap](../MS20_and_Beyond_Roadmap.md) §14で確認する。Indexには同じ§3.48番号のMS24記録もあるため、番号だけで参照を決めない。
3. [MS27 Block Breakdown](MS27_Block_Breakdown.md)のB6、§8.2のユーザー確認済み方針、§10の失効規則、§12のAC01〜AC10 / Pass・Holdを維持する。
4. 採用候補の現在証拠は[B5計画](MS27-B5_Implementation_Plan.md) §15.4を正本とする。[B4計画](MS27-B4_Implementation_Plan.md) §10 / §16の証拠境界とhandoffを併用する。fix-03、#01〜#07は候補別履歴であり、#08の代わりに使わない。
5. [Manifest](../Release_Package_Manifest.md)、[THIRD_PARTY_LICENSES](../../THIRD_PARTY_LICENSES.md)、[README](../../README.md)、[配布用readme](../../readme_mmdautolip.txt)、[NOTICE](../../NOTICE)は、現在の説明、日付付き履歴、実際の採用入力を区別して照合する。

実施記録の最新状態を古い計画段階の「未実施」より優先する。ただし、後日の文書追記だけを過去の候補に含まれている証拠にはしない。

## 2. 背景

MS27-B1〜B5は実施済みで、B3 G-LICENSE、B4 G-ARTIFACT、B5 G-PACKAGEはPassである。B5では除外設定の補修に応じて候補#08を再build・再監査し、ZIPと配布環境を確認した。B6はこの結果を受け、候補identity、最終文書、残課題が揃っているかを判定する。

### 2.1 継承する証拠と限界

| 項目 | 計画作成時に確認した記録 | B6での扱い |
| --- | --- | --- |
| B1 | [B1計画](MS27-B1_Implementation_Plan.md) §15.4 / §17.1: baseline、Windows 11 Pro build 26200 / 64bit、版数要件、隔離path契約のPass | 候補#08の実行環境・入力との対応を確認。現在環境を再測定した意味ではない |
| B2 | [B2計画](MS27-B2_Implementation_Plan.md) §15.4〜§15.5: `1.0.0`反映と直接検証Pass | source版数、PE両version、表示、ZIP名をB5証拠へ接続 |
| B3 | [B3計画](MS27-B3_Implementation_Plan.md) M07 / M08: ユーザー確認済み方針によるG-LICENSE Pass | 方針と採用binaryを保持。FFmpegの未確認事項全体を解消済みにしない |
| B4 / B5 | B5 §15.4: #08再build / SmokeLaunch、内部監査、157 files、全hash、配布実行、通常終了・再起動・残留なし | 候補別の実証拠を参照し、変更後の失効有無を再評価 |
| 検証の実施者 | B5 M01〜M07は原則Codex操作。スプラッシュ`Ver. 1.0.0`のみユーザー目視確認 | 今回のCodex再実行とは記録しない。スプラッシュの画面取得はCodex未実施 |
| 実MMD | MS26 CloseOut AのGUI / 実MMDはユーザー報告。B5では実MMDを再操作していない | 過去の受入を継承し、B6で再判定しない |
| 未検証・ユーザー受容 | Python 3.11 / 3.12のsource/build互換性は別support policy、FFmpeg exact archive provenanceはB3の非阻害制限、GitHub上の既存FFmpeg公開はユーザー判断で受容 | §8.3〜§8.4で実測・ユーザー判断・Codexの確認範囲を分離し、未検証を確認済みや法的保証とは表示しない |

B5の`8 passed, 21 subtests passed`・exit `0`、build / SmokeLaunch exit `0`は過去の記録である。Python 3.14.3での成功を3.11 / 3.12へ転用しない。既存Windows環境にはshell integration DLLがあり、clean OSではない。100ms process pollingの捕捉限界、全通信を監視していないこと、libgompの既知warningも保持する。

### 2.2 候補#08の採用identity（B5記録からの継承値）

| 項目 | 値 |
| --- | --- |
| B5実行時HEAD | `c091d56`と当時の補修差分。現HEADから無変更でbuildしたとは記載しない |
| B4 run root | `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-final-candidate-08\` |
| 採用EXE | 上記rootの`source\dist\MMD_AutoLipTool.exe` |
| EXE size / SHA-256 | `425824202` bytes / `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223` |
| B5 run root | `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-08\` |
| 採用ZIP | 上記rootの`zip-output\MMD_AutoLipTool_v1.0.0_Windows_onefile.zip` |
| ZIP size / SHA-256 | `423274681` bytes / `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086` |
| 実行EXE | B5 rootの`distribution-run\MMD_AutoLipTool.exe`。B5時点で採用EXEと一致 |
| 版数 | project / PE FileVersion / ProductVersion `1.0.0`。スプラッシュはユーザー確認 |
| 入力・配布file数 | B4 `source-manifest.json`の109入力、B5の157配布files。数だけで充足を判定しない |
| build環境 | Windows 11 build 26200、Python 3.14.3、PyInstaller 6.19.0 / hooks 2026.3 |

上記pathの現存、現在のsize/hash、証拠ファイルの可読性は、今回再取得していない。B6開始時の確認対象である。

### 2.3 現HEADとの照合で注意する差分

`c091d56..61adb55`にはspec、THIRD_PARTY_LICENSES、テスト2件、状態・計画文書、`sample/MMD_AutoLipTool説明1.wav`の追加がある。これは今回のGit差分確認結果であり、すべてが#08作成後の変更という意味ではない。B5が実行した未commit差分と、検証後の状態追記を入力hashで分ける。

READMEにはB5確認を継続中とする現在状態と、license原文の最終ZIP配置を未確認とする説明が残る。配布用readmeにも最終ZIP配置の未確認表現が残る。NOTICEのB3 / B4記述は日付付き履歴であり、B5はその正本bytesを保持している。THIRD_PARTY_LICENSESには候補作成後のB5到達状態追記がある。文書の差を一律に「候補失効」または「影響なし」とせず、§8.2 / §10で判定する。

## 3. 目的

1. 候補#08のbytes、B1〜B5の採用証拠、current HEADとworking treeを追跡可能に結ぶ。
2. 未確認、既知制限、失効証拠、未解消P1 / P2 / P3を区別する。
3. 必要な文書同期とその配布bytesへの影響を判定する。
4. MS27-AC09 / AC10を含む全ACについて根拠を示し、release readinessをPassまたはHoldとする。
5. Holdの場合も不足証拠、担当、解除条件を揃えた監査報告を完成させる。

## 4. In Scope

以下は、別途B6実施を依頼された場合の基本範囲である。

- live Git / working treeとB5実行時HEAD・差分・入力manifestのread-only照合
- 既存EXE / ZIP / 非runtimeの証拠ファイルの現存、size / SHA-256、記録対応の確認
- B1〜B5のgate / AC / process結果 / 手動証拠の継承可否と失効判定
- README等の同期要否、候補採用文書と監査後文書の差分採否の記録
- 許可された非配布文書への監査・状態同期、最終ledger、Pass / Hold、handoffの記録
- Python互換性とFFmpeg未確認事項について、既存証拠の評価、追加作業の具体化、Hold / handoffの決定

Python matrixの新規実行、FFmpegの追加ネット調査、原文・対応ソースの取得、再build / ZIP再生成は基本監査に含めない。必要時は対象・手段・出力先を具体化し、既存権限に含まれなければ別途実施範囲を確定する。実施できなくても依存しない監査を進め、Hold報告を完成させる。

## 5. Out of Scope

- public GitHub Release、tag、push、merge、deploy、publish、外部サービスへの書込み
- stage、commit、branch変更、リモート状態の照会・取得を自動追加すること
- installer、新規配布方式、新規依存、Python / toolchain導入・更新、FFmpeg差替え
- MS26実MMD受入の再判定、実MMD再操作、PMX hash取得や4ケース再提出の必須化
- runtime JSON / INIの直接編集・コピー・fixture化・stage、既存設定・モデル保存先の変更
- 音声、TEXT、PMX / PMD、MMD、VMD / WAV生成物、sample、weights、modelsの同梱・変更
- コード、テスト、設定、生成品質、データ契約、旧Qt系の補修・再設計
- 既存build / dist / 検証runの上書き・削除、配布実行後directoryの再圧縮
- 法的適合性全体、GPLの適用範囲、特定地域の法的判断をCodexが独自に断定すること

今回の計画作成では、テスト、compileall、build、GUI / MMD、ネットワーク、build・検証用成果物の生成を一切実施しない。後続作業のための例示commandも今回の実行許可ではない。

## 6. 前提条件

- B6の評価開始時点を新たに記録する。今回のHEAD / cleanを後日の状態として転記しない。
- B3のユーザー確認済みG-LICENSE方針は継承する。同じ方針の再承認を求めない。
- `requires-python = ">=3.11"`は宣言下限で、互換性の実測結果ではない。外部Python不要のonefile動作もsource/build互換性の代替ではない。
- B5 Passは#08に対する記録であり、現HEAD全体・新しい候補・将来の公開を包括しない。
- 証拠不足でもB6監査へ着手できる。Passに必要な資料が取得できなければ該当gateをHoldにする。
- 既存のユーザー変更は保護する。評価対象に影響する未分類差分が残れば、差分を無視してPassとしない。

## 7. 対象ファイル

| 区分 | 対象 | 実施時の責務・変更条件 |
| --- | --- | --- |
| 今回の唯一の成果物 | `docs/Implementation_Plan/MS27-B6_Implementation_Plan.md` | 計画のみを新規作成。B6結果は将来の実施記録へ分離 |
| B6主記録 | 本書の将来実施ledger | baseline、候補対応、差分分類、AC、finding、判断、handoffを集約 |
| B6状態同期 | `docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md`、`docs/Implementation_Plan/MS27_Block_Breakdown.md`、`docs/repo_milestone.md`、`docs/Version_Control.md` | B6実施依頼の範囲で必要箇所のみ更新。履歴文書は検索と範囲閲覧。HoldならMS27完了としない |
| 関連文書 | `docs/Release_Package_Manifest.md`、`README.md` | 候補/公開の区別、B5到達状態、実際の確認範囲を同期。実入力に含まれないことを確認して非配布変更に分類 |
| 配布文書 | `readme_mmdautolip.txt`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` | まずread-only比較。配布版修正が必要なら§10の失効・再検証を伴う別作業へ返す。NOTICEの既存正本bytes指定を保持 |
| 継承元 | B1〜B5個別計画、B4/B5の非runtime evidence、source / package manifest | 既存証拠を参照。過去の結果・失敗・実施者を上書きしない |
| 静的入力 | `pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、`MMD_AutoLipTool.version.txt`、`build_hooks/`、`src/`、`assets/`、`FFmpeg/bin/` | manifestに含まれる実入力と差分の対応だけをread-only確認。無関係なコード全読込みはしない |
| 関連テスト | `tests/test_app_version.py`、`tests/test_ms27_b2_windows_version_resource.py`、`tests/test_whisper_model_catalog.py`、`tests/test_ms27_runtime_exclusions.py`、`tests/test_whisper_model_loader.py`、`tests/test_ms17_b3_ffmpeg_locator.py` | 実在確認済みの追加検証入口。今回実行しない。互換性等の補足作業で必要性と副作用を確認して選択 |

本表は今回の書込み許可を拡張しない。将来のB6実施でも指定された変更範囲を優先し、許可が本書だけなら他文書は「同期必要・未実施」と記録する。同期が必須のまま未実施ならreadinessはHold。

## 8. 実装方針

### 8.1 HEADと候補を結ぶ

次の三つを別々の列で管理する。

- **build基準:** `c091d56 + 当時の補修差分 + 109入力のpath/size/hash + build環境`
- **候補基準:** #08 EXE / ZIPのpath/size/hash、157 files、内部archive・配布実行証拠
- **監査基準:** B6実施時のfull HEAD、working tree、今回の計画作成後を含む差分、文書同期後の最終状態

Git差分だけでは未commitだったbuild入力を復元できないため、`source-manifest.json`と保持された隔離sourceを入力の正本として照合する。manifestの実schema、相対path、重複、対象集合を読んでから全109行を分類する。current HEADとの一致、B5補修として既に検証された差分、監査後の非配布追記、未評価の入力変更を区別し、各行に根拠を付ける。

追加・削除されたpathも確認する。manifestの既存行だけをhash照合して、新しく収集されるfileを見落とさない。specのtoolbar / FFmpeg directory収集、hooks、外部package metadata等の入力境界を確認する。テスト差分は候補へ同梱されなくても採用した回帰証拠との対応を確認する。

### 8.2 文書同期とbytesの整合

| 文書・観測 | B6の判断方針 |
| --- | --- |
| READMEのB5継続中・原文最終配置未確認 | B5 §15.4と食い違う現在状態は同期対象。FFmpeg provenance / ソース提供の未確認は残す。READMEを候補入力へ含めていない根拠も確認 |
| 配布用readmeの最終ZIP配置未確認 | B3時点の履歴説明として候補内の他文書と矛盾なく読めるかを確認。現在の案内として誤認を招く場合は修正必要とし、B5再組立・再照合へ返す。hash維持を理由に必要修正を省略しない |
| NOTICEのB3 / B4履歴 | B5が正本bytesを保持した事実を継承。日付付きの過去記録だけを理由に書換えない。現行の通知に具体的不足・矛盾がある場合は正本変更の必要性を示す |
| THIRD_PARTY_LICENSESの候補後追記 | B5 §15.4が「候補入力ではない状態追記」とした差を、実際の隔離source / ZIP版と比較して特定。履歴追記とcomponent・原文・提供案内の変更を分ける |
| Index / Roadmap / milestone / Version Control | 2026-09-17のB5同期を再利用し、B6の新しい監査結果だけを同期。古い中間状態の全消去・全書換えはしない |

候補内の文書hashとcurrent repository文書hashが異なる場合は、`候補採用版 → current版 → 差分内容 → 採否 → bytesへの影響`を記録する。配布に反映しない監査結果の追記は、採用版の原文・通知・component対応がなお有効であり、追記を公開物の新しい入力としないことが確認できる場合に限り非失効とする。これを埋込み文書一般の失効免除にしない。

候補をcurrent版文書へ更新する必要があれば、埋込み対象の`LICENSE / NOTICE / THIRD_PARTY_LICENSES.md`はB4 / B5、外側だけのreadme / 原文はB5へ返す。B6の結果を配布文書へ追記し続けて再buildが循環しないよう、監査結果の正本は本書と非配布状態文書に置く。

### 8.3 Python 3.11 / 3.12の判断

両versionについて`source互換性`と`build互換性`を分けたmatrixを作る。初期状態は4欄とも未確認。Python 3.14.3の#08検証とonefileの外部Python非依存性は別欄で継承する。

| 状況 | 必要な確認・作業 | B6の結論 |
| --- | --- | --- |
| 対応する既存の検証資料がある | 対象HEAD / 差分、Python絶対path・patch version・architecture、依存解決値、実行command・終了コード、source / build別の実結果を確認 | 今回対象への有効性を示せた欄だけ確認済み |
| B6内の追加検証をユーザーが依頼し、既存環境で実施可能 | 下記の限定matrixを隔離領域で実施。#08の生成環境や採用bytesは変更しない | 必須の全欄が満たされれば、この未確認事項を解消できる |
| Python / 依存環境がない、必要な実行が禁止、資料不足、失敗・必須skip | 不足version、工程、環境、担当、解除証拠を記録し、追加作業へhandoff | 2026-09-18のユーザー決定により、Windows onefile公開判定では非阻害。source / build互換性は未検証のまま別のsupport policyへ残す |
| ユーザーがsource対応方針の変更・確認の延期を選ぶ | 対応範囲・README・metadata・配布への影響を別途定義する。`>=3.11`や依存pinを無断変更しない | 2026-09-18のユーザー決定は、Python matrixをWindows onefile公開判定から外すものである。source / build互換性を確認済みとは扱わず、範囲変更として記録する |

追加検証を行う場合は、実行前に以下を固定する。これは今回のテスト・build許可ではない。

1. 各versionの実在するPythonと既存依存環境、読み取り元、隔離cwd、出力先を記録する。依存の`Requires-Python`、宣言pinと実解決値を確認する。適合不能なら、その時点でHoldにして依存を更新しない。
2. source側はwx / NumPy / Whisper / pyopenjtalk / tokenizer等の必要importと、§7の版数・resource・catalog・runtime除外・locator・loaderの直接回帰を選ぶ。各テストの副作用を事前確認し、設定やcacheは隔離先のみ、実download・既存runtimeへの接触を起こさない。互換性の主張は実際に確認した経路に限定する。
3. build側はversionごとに別runを使い、B4の絶対cwd / PythonExe、入力hash、build / SmokeLaunch・内部resource監査を適用する。#08と同じbytesになることは要求せず、互換性検証用artifactとして区別する。通常GUI確認が必要ならB5手順と実施権限へ分離する。
4. 表示の成功、exit、skip、warningを記録する。片方のversionやimport成功だけで両versionのsource/build全体をPassにしない。将来のsupport matrixで必要な確認を実行できなければ、そのsupport matrixをHoldとするが、2026-09-18のWindows onefile G-READY判定へ自動反映しない。

### 8.4 FFmpeg provenance / external-library / source provisionの判断

既存B3決定を維持する。現行10実体のversion・configuration・hashを変えず、取得経路はユーザー報告の「取得当時の公式Downloadページを起点」とする。BtbN系列との整合は推論のまま保持する。license revisionとbinary revisionの厳密一致はG-LICENSEの必須条件へ戻さない。

| 分類 | 必要な記録・判断 | Pass / Holdへの影響 |
| --- | --- | --- |
| exact provider archive / archive hash / 暗号学的なbinary-source一致 | B3 M07 / M08、確認済みidentity、取得経路、公式参照、未確認の範囲を引き継ぐ | 未確認のまま「一致確認Pass」としない。既存方針に基づく非阻害のprovenance limitationとして保持でき、これだけでB3 Passを取り消さない |
| 完全なexternal-library対応 | 実configuration、10 binary / DLL、内部一覧、既存原文・通知と、native / static linkを含む外部component対応を照合。対象、version根拠、原文path/hash、必要対応物、未判明部分を表にする | 2026-09-18のユーザー判断により、GitHub remoteでの既存公開を規約上問題なしとして受容し、G-READYの阻害条件にしない。Codexは法的適合を結論づけない |
| 対応ソース提供方式 | 対象componentと資料、提供物のrevision / 内容 / hash、build configuration等との対応、提供先、提供主体、利用者への案内、提供時期、実提供確認方法を固定 | `origin/main`が到達可能で`2151d7b`を指し、FFmpeg 10 entriesと通知文書が追跡され、候補branchの`FFmpeg/bin`に差分がないことを確認した。これはremote追跡状態の確認であり、法的適合の独自判断ではない |
| ZIP内通知・原文の不足 | 既存157 filesとcomponent対応で具体的な欠落・誤案内を特定 | 欠落が判明した対象はG-PACKAGE等を再開。provenance limitationの語で配布不足を免除しない |
| 将来のGitHub自動source archive | 現HEADの追跡対象からFFmpeg / 素材の含有と通知方針を確認し、公開担当へ渡す | 実archive生成・公開は実施しない。アプリsource archiveをFFmpeg全対応ソースの代替とはしない |

既取得の一次資料とローカル証拠で充足を判断できれば、その範囲と確認者を記録する。追加ネット調査・原文取得が必要なら、既存文書の公式参照を入口に対象を限定した別作業とする。2026-09-18のユーザー判断により、GitHub上の既存公開はG-READYに必要な受容根拠として扱う。公開物・提供方式の変更や別の法的判断が必要になった場合は、対象を限定して再評価する。B6では公開先への書込みを実行しない。

ユーザーに必要な判断は、提供する対象物、ZIP同梱か別提供か、具体的な提供先・管理主体・利用者への案内方法、調査/取得を行うか延期するかである。既存のB3方針の再確認ではない。ユーザー判断の受領だけを、資料の一致・配置・実提供の証明や法的適合の断定へ置換しない。

## 9. 詳細ステップ

| 手順 | 実施内容 | 出力・停止条件 |
| --- | --- | --- |
| B6-01 基準固定 | AGENTSと現行Indexを確認し、cwd、branch、full HEAD、status、必要な履歴・差分を単独commandで取得。開始時と今回追加差分を分ける | baseline行。想定外差分は保護し、未分類なら関連判定をHold |
| B6-02 証拠所在 | §2.2のEXE / ZIP、B4 source manifest、B5 package manifest、static / final verification、archive / PYZ一覧、process証拠を確認 | path、size/hash、読取可否、B5 §15.4の対応。欠落を別候補で補わない |
| B6-03 identity再照合 | EXE / ZIPの実size/hashを§2.2と比較。109入力と現HEAD差分、157 filesの採用表を§8.1に従い照合 | candidate / input / document対応表とstale表。#08不一致は関連gate Hold |
| B6-04 gate統合 | B1/B2、B3 M07/M08、#08のbuild / smoke / 内部 / ZIP / M01〜M07を全ACへ接続 | 有効な継承証拠、実施者、exit、観測限界を記したledger |
| B6-05 未確認評価 | Python matrix、FFmpeg各分類、P1/P2/P3、既知制限を評価。可能な範囲の既存資料確認を進める | 補足実施かHold/handoff。質問があっても独立監査を継続 |
| B6-06 文書同期設計 | §8.2の各文書について変更要否・内容・配布入力への影響を記録 | 非配布同期、候補採用版の保持、B4/B5へ戻す修正を区別 |
| B6-07 許可文書同期 | 非配布状態文書を事実へ合わせる。配布修正が必要なら自動再buildせずowner・必要権限・再確認範囲を記録 | 差分。未同期必須事項や失効が残ればHold |
| B6-08 最終判定 | 同期後のHEAD/tree/候補identityとAC01〜10を再照合し、§12でPass/Holdを記録 | 判定、根拠、候補hash、未確認、解除条件。採否自体のexitはN/A |
| B6-09 handoff | 候補の所在、有効/失効証拠、最終文書版、次owner、必要な判断・権限をまとめる | 監査報告完了。Passでも公開操作へ進まない |

### 9.1 証拠を読む順序と照合の終点

- B4 rootの`source-manifest.json`と保持された`source/`を先に読む。
- B5 §15.4が示す`evidence/static-summary.json`、`package-manifest.json`、`pyz-modules.txt`、`archive-entries.txt`、`evidence/final-verification.json`の実所在を既存run内で確認する。未確定の配置を想像で補わない。
- 通常終了はB5 rootの`gui-verification/resume-0916-b-process.json`と`normal-restart-0916-process.json`をM07へ対応付ける。旧runや終了操作者不明の証拠を採用しない。
- ZIP自体のhash一致とB5の有効な全file証拠が揃えば、展開・GUIを機械的に再実施しない。既存`zip-input/` / `zip-extracted/`が残る場合は配布fileだけを採用表へ照合できる。`distribution-run/`の追加INI・cacheを再配布物に含めない。
- 現存hash、証拠の対象identity、入力差分、実施者・結果、失効判断が揃った時点で照合を終える。証拠を読めない・相互不一致の場合は不足を特定し、全テストの再実行で埋めようとしない。

## 10. 状態遷移 / データ・証拠契約

### 10.1 状態と証拠行

`Planned → Auditing → 判定報告完了（Pass または Hold）`とする。Hold解除の証拠が届いた場合は新しい監査日時・証拠IDで再評価し、旧Hold理由と履歴を保持する。

```text
証拠ID / phase（planning・B6 audit・inherited・user report）/ 対応AC:
日時 / 実施者 / owner / 確認済み・推論・未確認:
current HEAD / tree差分 / build時HEAD・補修差分 / 入力manifest identity:
EXE・ZIP・付属文書の絶対path / size / SHA-256 / candidate ID:
環境 / cwd / 単独command または文書・手動証拠の参照:
期待 / 実結果 / process exit code・取得元 / wrapper・子processの区別:
継承元ID・節・証拠path / 今回の再実行有無:
Pass・Hold・not run・stale・非阻害制限 / 理由 / 影響AC:
旧証拠の失効対象 / 非失効根拠 / 解除条件 / 次owner・必要なユーザー判断:
```

B6の新規commandは`MS27-B6-Cxx`、照合は`MS27-B6-Mxx`、ユーザー判断は`MS27-B6-Dxx`、findingは`MS27-B6-Fxx`、未確認は`MS27-B6-Uxx`とする。本文の手順番号・AC番号とは別に実施順で採番する。計画作成記録は`phase=planning`とし、B6実施件数に含めない。

### 10.2 失効規則

| 変更・不足 | 失効 / 次の所有Block |
| --- | --- |
| 実コード、pyproject、依存・Python runtime、spec/hook、version resource、FFmpeg、埋込みresourceが候補採用入力から変わる | 影響するB4 build / 内部 / 版数 / smokeをstaleとし、新EXEを使うB5 ZIP・配布証拠も更新。B6では補修・buildを自動開始しない |
| 配布へ反映するLICENSE / NOTICE / THIRD_PARTY_LICENSESの変更 | 現specでは内部にも同梱するためB4 / B5が対象。単なる文書変更という理由では免除しない |
| ZIP外側だけのreadme / license原文 / 対応物・配置の変更 | ZIP hash / entry / 全file対応は失効。B5再組立・照合が必要。EXE / 内部入力不変を根拠にB4を再利用し、GUI再確認は影響で選ぶ |
| EXE / ZIPのbytes不一致、消失、必要な入力・証拠を対応付けられない | 対象候補の判定をHold。別dist・別hashへの付替え、同じ版数だから同一という推定をしない |
| OS / 実行条件 / 必要resource利用の前提を変える | その条件のB5実行証拠を再評価。静的一覧・hash不変の証拠まで一律破棄しない |
| 非配布状態文書・本計画のみの変更 | bytesと検証前提への非影響を確認して継承可能。commit増加やclean/dirtyだけで失効を決めない |
| 候補後のTHIRD_PARTY_LICENSES状態追記 | §8.2の限定条件で非配布の監査追記として分離可能。配布入力へ採用する、または通知の充足に必要なら上のB4/B5失効規則を適用 |
| sample等の追跡追加 | #08の入力・ZIPから除外されていることを確認。Git自動source archiveへの影響は別の公開handoff。追跡済みを素材同梱の許可としない |

候補#08を変更する必要が生じたら、新candidate IDとhashでB4/B5を再検証する。#08に別bytesを上書きしない。変更前のPassは過去の候補に対する証拠として保持する。

## 11. テスト / 検証方針

### 11.1 今回の計画作成

必須資料・必要なGit差分の閲覧、本文の内容整合・参照先・whitespace・変更範囲の自己レビューだけを行う。テスト、compileall、build、GUI / MMD、ネットワークは実行しない。スキルの標準構成に従い、コード実装や他文書同期へ移行しない。

### 11.2 将来のB6基本監査

候補hash、入力とHEADの対応、証拠の有効性、文書差分が最小検証である。以下は使用可能な単独command例で、実施時に必要なものを選ぶ。連結・パイプライン・並列実行はしない。

```powershell
git status --short --branch
git rev-parse HEAD
git diff --name-status c091d56..HEAD
git diff --name-status
git diff --cached --name-status
Get-Item -LiteralPath 'C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-final-candidate-08\source\dist\MMD_AutoLipTool.exe'
Get-FileHash -LiteralPath 'C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-final-candidate-08\source\dist\MMD_AutoLipTool.exe' -Algorithm SHA256
Get-Item -LiteralPath 'C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-08\zip-output\MMD_AutoLipTool_v1.0.0_Windows_onefile.zip'
Get-FileHash -LiteralPath 'C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-08\zip-output\MMD_AutoLipTool_v1.0.0_Windows_onefile.zip' -Algorithm SHA256
git diff --check
git diff --no-index --check -- NUL docs/Implementation_Plan/MS27-B6_Implementation_Plan.md
```

manifest / 全file照合は、実schemaを確認してread-only手段を選び、対象と結果をledgerへ記録する。B5の`package-candidate-08.py`や`verify-candidate-08-results.py`は過去の証拠参照であって、自動再実行の入口にしない。書込み・生成のあるhelperをread-only検査と誤認しない。

終了コードはrunnerの実値を記録する。`rg`該当なしの`1`や、新規ファイルに対する`git diff --no-index --check`の`1`は診断内容と併記し、テスト失敗と混同しない。後者はwhitespace診断なし・新規差分由来の場合だけ正常な検査結果として扱う。判定・ユーザー報告・文書照合自体は`N/A（理由）`、未実行は`not run`、未取得は`unknown`とし、`0`を補わない。

### 11.3 追加・再検証の条件

- §8.3のPython matrixは別途実施を依頼された範囲だけ行う。source / buildの未確認を記録するだけならテストを走らせない。
- 配布入力変更は§10に従いB4/B5へ戻し、新候補に必要なbuild / smoke / 内部 / ZIP / 実行確認を行う別作業とする。
- 新しいfailureや具体的な影響がなければ、full pytest / compileall / GUI / 実MMDの再実行をB6の一律条件にしない。
- 必須に選んだ検証の非ゼロ、必要範囲のskip、結果未取得はHold。成功表示だけで通過させない。

## 12. 受け入れ条件

### 12.1 B6監査報告の完成条件

| ID | 条件 | 主な根拠 |
| --- | --- | --- |
| B6-AC01 | 実施時HEAD/treeと#08 build入力・EXE/ZIP identityを対応付け、不一致・不足を明示 | baseline / input / candidate ledger |
| B6-AC02 | B1〜B5の各gateとMS27-AC01〜08を、候補に有効な証拠へ接続 | 継承表と失効表 |
| B6-AC03 | Python両version、FFmpeg各分類、観測限界、findingに結果・owner・解除条件がある | §8.3〜§8.4のmatrix |
| B6-AC04 | 全同期対象に変更要否と配布影響を記録し、許可された必要同期を完了。不許可・未完了は明示 | 文書採否表 / diff |
| B6-AC05 | 全判定に根拠があり、未解消P1/P2・失効・必須未確認をPassへ繰り越していない | §12.2の判定 / MS27-AC09 |
| B6-AC06 | Codex実行、ユーザー報告、継承、未実施・未公開を区別し、MS26を再判定していない | 実施者欄 / MS27-AC10 |
| B6-AC07 | 最終内容・リンク/参照・whitespace・変更範囲を確認し、候補と次ownerをhandoff | 最終自己レビュー / handoff |

上記は報告の完成条件である。不足を明示したHold報告も完成し得るが、未充足のMS27 ACをPassとした意味ではない。

### 12.2 release readinessのPass / Hold

**Passは次をすべて満たす場合だけとする。**

- MS27-AC01〜AC10が候補に有効な証拠で充足され、必須gateがすべてPass。
- 候補bytes、入力、現HEAD差分、採用文書、最終ledgerが対応し、必要な再検証・同期が完了している。
- 未解消P1/P2、必須証拠不足、未解除のstaleがない。P3を残す場合は配布機能・同梱条件・license・版数を妨げない具体的理由と扱いがある。
- Python 3.11 / 3.12のsource / build互換性は、2026-09-18のユーザー決定によりWindows onefile公開判定の必須条件から外している。`requires-python >=3.11`を互換性の実測結果と表示せず、未検証のsupport policyとして保持する。
- FFmpegは、B3で受容したexact archive identityの非阻害制限を維持し、2026-09-18のユーザー判断によりGitHub remoteでの既存公開を規約上問題なしとして採用する。Codexはremoteの到達・追跡状態と候補branchとの差分だけを確認し、法的適合の独自結論は出さない。

**Holdは、上記のいずれかを満たせない場合とする。** 対象AC、候補、確度、不足証拠、担当Block、解除条件、必要なユーザー判断を記録する。PythonやFFmpegについては、ユーザーが公開判定の条件・受容方針を変更した場合、その決定と未検証範囲を記録して再評価する。B3/B5の過去Passを消すことと、B6でreadinessを保留することは別である。

### 12.3 MS27 closeoutと公開の境界

- **計画作成完了（計画策定時の状態）:** 本書1ファイルの作成と静的自己レビューが終了した状態。B6判定は未実施だった。現在のB6監査結果は§15.2を正本とする。
- **B6監査報告完了:** 根拠付きPassまたはHold、文書同期結果、残課題、handoffが揃った状態。
- **MS27 closeout / release-ready:** B6がPassの場合だけ可能。closeoutの確定・状態同期はユーザーの明示決定に従い、HoldをMS27検証済み完了へ変更しない。2026-09-18にこの明示決定を受領し、MS27 CloseOutを確定した。
- **公開済み:** 本計画では到達しない。PassでもGitHub公開、tag、push等は別途の具体的な依頼が必要。

公開操作自体が未実施であることだけはB6のHold理由にしない。公開前に必要なソース提供等については、2026-09-18のユーザー受容方針とremote追跡確認の範囲を超える変更が生じた場合だけ、具体的な不足を理由に再評価する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| B5実行HEADと現在HEADの差をすべて未検証変更と誤認する | 当時の補修差分をsource manifestへ照合し、候補後変更と分ける |
| 後日の状態追記を候補内文書へ含まれるものと誤記する | 候補採用版とcurrent版を別hash・差分で管理 |
| 原文・readmeの必要修正を「文書だけ」として証拠へ無条件継承する | 埋込み/外側/非配布を分け、必要なB4/B5証拠を更新 |
| provenance制限の受容を全通知・対応ソース充足へ拡張する | exact archive制限、external-library対応、ZIP配置、実提供を別の行で判定 |
| Python下限宣言やonefile成功を互換性証明にする | 3.11/3.12別、source/build別の証拠がないことを未検証として残す。2026-09-18のWindows onefile G-READY判定では非阻害 |
| 検証のためruntime・素材・既存成果物へ触れる | 基本監査はread-onlyと文書同期に限定し、追加検証は隔離・具体的権限を定める |
| B5未追跡素材の履歴を現HEADへそのまま転記する | 現HEADにはsample WAV追加がある。#08非同梱と将来のsource archive影響を分ける。素材の移動・削除・再配布をしない |
| Holdを解消するため未確認をP3へ下げる | severity、実測の未検証、ユーザー受容方針、gate充足を別列にし、gateに影響する未確認だけをHoldとする |

P1は重大なデータ破壊・情報混入等、P2は候補・依存・通知・必須証拠や案内の欠陥、P3は受入を妨げない軽微な記録不整合を基本とする。未確認はfailureと断定せずUxxで記録し、影響ACが未充足ならHoldとする。PMX hash独立取得不可、B2-R05の原因・影響未確定は勝手に解消しない。

## 14. Codex 実装時の注意

- commandを一つずつ実行し、結果を見て次を選ぶ。shell連結、パイプライン、並列実行をしない。
- 本計画作成ではimplementation-plan-creationスキルを使用する。指定ファイル以外の変更・テスト・ネットワーク・Git変更へ移行しない。
- 単独で作業し、この計画をサブエージェント起動の許可と解釈しない。
- 証拠の実施者、時点、対象hash、強さを維持する。未取得のPID / exit / 操作ログを補わない。
- 初動後に権限・仮説・例外、最終報告前に要求・差分・反証・残る未確認を自己監査する。
- 必要な証拠が揃えば確認を終える。既に認められたB3方針やMS26受入を、根拠なく再承認事項にしない。
- 将来の追加権限が必要でも、今回の計画完成や独立する監査を止めない。未解決の採否を具体化してhandoffする。
- 完了後に公開や後続実装へ自動移行せず、セッションを閉じる操作は行わない。

## 15. 計画作成記録と実施記録

### 15.1 計画策定時に確認した範囲

- AGENTS、implementation-plan-creationスキルと標準template、§1.1の必須参照資料を閲覧した。
- live Gitで`feature/MS27-implementation`、`61adb55`、開始時cleanを確認した。`c091d56..HEAD`の対象差分、specの埋込み対象、pyprojectの版数・Python下限、関連テストpathを静的確認した。
- B1〜B3の必要なgate / handoffと、B4 / B5の現在証拠・失効境界を参照した。履歴全体の再監査や法的判断はしていない。
- 候補#08のsize/hash、157 files、build / GUI / 回帰結果はB5記録からの継承であり、今回の再測定・再実行ではない。
- 本書以外の文書同期、B6判定、Python matrix、FFmpeg追加調査・提供確認、テスト、compileall、build、GUI / MMD、ネットワーク、stage / commit / push / merge / tag / releaseは未実施。

### 15.2 B6監査・状態同期記録（2026-09-18）

#### 15.2.1 baseline・候補identity

- B6開始時はbranch `feature/MS27-implementation`、full HEAD
  `840fa8bdc4efdcceb2add753c81d6ed9520e1d41`（`840fa8b Document MS27-B6 implementation plan`）、
  `git status --short --branch`はclean（process exit code `0`）だった。
- B5保存証跡の`static-summary.json`、`final-verification.json`、ZIP一覧をread-onlyで再照合した。候補#08 EXEは425824202 bytes、SHA-256
  `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、ZIPは423274681 bytes、SHA-256
  `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`で、保存証跡の値と一致した。
- ZIPは157 filesで、rootの`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`readme_mmdautolip.txt`、`MMD_AutoLipTool.exe`と`licenses/`を含む。B5のCodex実行記録（M01〜M07、通常終了・再起動・残留なし）と、スプラッシュ`Ver. 1.0.0`のユーザー目視確認を継承する。今回GUI / 実MMDは操作していない。
- `MMD_AutoLipTool.spec`は候補#08のbuild sourceと同一bytesである。一方、候補に埋め込まれた`THIRD_PARTY_LICENSES.md`のSHA-256は`FD237F14A9D794BE75E07DC3D3BC5FE8F1190067085D4CD2200AAC6706AA077B`、現HEADは`27A27DED261F6C33766FF029DF2FCF25759B1271C1AAEA4F750DA25DEB0B4A94`である。差分はB5後に追加したGUI・独立環境・通常終了の状態記録だけで、license / component対応の変更ではない。候補#08には後追いの現HEAD文書を含めず、当時のembedded bytesとして保持する。
- `readme_mmdautolip.txt`の現HEAD SHA-256は候補#08の`1FBAA67CD7F4B1EA7E1B67DEEE3DE89CA6BFD39287E2A7BFEB268C70E659F6DA`と一致する。配布用readme、LICENSE、NOTICE、候補採用版の`THIRD_PARTY_LICENSES.md`を変更して候補へ反映する場合は、§10に従いB4/B5を再実施する。今回それらの配布bytesは変更していない。

#### 15.2.2 継承・未確認・文書採否 ledger

| 記録単位 | 結果 | 根拠・影響 |
| --- | --- | --- |
| B1〜B5 / MS27-AC01〜08 | 継承可能 | B1 G-VERSION、B3 G-LICENSE、B4 G-ARTIFACT、B5 G-PACKAGEの既存Passと候補#08 identityを対応付けた。B5のスプラッシュだけはユーザー目視、MS26の実MMDはユーザー報告であり、今回のCodex実行結果ではない。 |
| B6-U01（候補・証跡） | 解消 | EXE / ZIP、static / final verification、ZIP構成が現存し、recorded size / SHA-256と一致した。別候補への付替えはしていない。 |
| B6-U02（Python 3.11 / 3.12） | 未検証・非阻害 | `requires-python >=3.11`、onefile実行、又はPython 3.14.3の既存記録は、3.11 / 3.12のsource / build両方の互換性証明ではない。2026-09-18のユーザー決定により、このmatrixをWindows onefile公開判定から外す。互換性を確認済みとは扱わず、必要時は別のsupport policyとして隔離matrixを実施する。 |
| B6-U03（FFmpeg external library / source provision） | ユーザー方針で受容 | B3で受容したexact provider archive identityの制限は非阻害として維持する。`origin/main`は到達可能で`2151d7b`を指し、FFmpeg 10 entriesとLICENSE / NOTICE / THIRD_PARTY_LICENSES / Manifestを追跡する。候補branchの`FFmpeg/bin`は`origin/main`との差分なしである。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexはこの判断をG-READYへ反映するが、法的適合を独自に保証しない。 |
| B6-U04（配布文書と候補） | 分類完了 | current `THIRD_PARTY_LICENSES.md`の後追い状態記録は候補#08へ遡及しない。候補の配布bytesは変更せず、候補#08の採用入力外である状態文書とroot READMEのみをB6結果へ同期する。候補内の文書を更新して配布する判断はB4/B5再実施が必要である。 |
| B6-U05（clean Windows追加確認） | 追加不要 | B5の独立配布環境証跡に具体的欠陥は確認していない。今回新たなGUI・配布runtime操作は行わない。 |
| B6-U06（closeout / public release） | CloseOut確定 / 公開未実施 | B6 Pass後、2026-09-18のユーザー明示決定によりMS27 CloseOutを確定した。GitHub Release、tag、push、merge、公開用source archive生成は別工程であり、未実施である。公開未実施自体はG-READYの阻害要因ではない。 |

#### 15.2.3 判定・handoff

- **B6監査報告: 完了（Pass）。** B6-AC01〜AC07の監査報告要件は、候補identity、継承根拠、ユーザー決定、remote確認、文書の配布影響、実施者境界、handoffをこの節と同期先文書へ記録して満たした。
- **MS27 release readiness: G-READY Pass（2026-09-18のユーザー受容方針による）。** MS27-AC09は候補#08と最終ledgerが対応し、Python matrixを非必須化、FFmpeg既存公開をユーザー判断で受容したためPassとする。MS27-AC10は、MS26のCloseOut Aを再判定せず、Codex実行・ユーザー報告・継承証跡・未実施公開を区別している。
- P1 / P2 / P3の新規findingは確認していない。Python 3.11 / 3.12のsource / build互換性は未検証のまま別のsupport policyへ残る。FFmpegの法的適合はユーザー判断であり、Codexの法的保証ではない。
- 2026-09-18のユーザー明示決定によりMS27 CloseOutを確定した。candidate#08とB6状態文書をremoteへ反映するかの判断、GitHub Release、tag、push、merge、公開用source archive生成は別工程である。
- 今回はテスト、compileall、build、ZIP再生成、GUI / 実MMD、ネットワーク、stage、commit、push、merge、tag、releaseを実施していない。B6の文書同期は候補#08の採用入力外に限定した。

## 16. 実施前の未確認事項・ユーザー確認が必要になる条件

計画を完成させるための追加回答は不要である。B6実施時に既存資料・許可範囲で解消できない場合だけ、次の具体的事項を確認する。

| ID | 実施前の未確認 | ユーザー確認が必要になる条件と質問内容 | 回答・証拠がない場合 |
| --- | --- | --- | --- |
| B6-U01 | #08 EXE / ZIP / 非runtime証拠の現存とcurrent hash、109入力と現HEADの一致・差分分類 | 記録pathが消失・不一致で保管先も特定できない場合、同じ候補の保管先を確認。新候補が必要なら再build / 再検証の範囲を提示 | 候補identity関連をHold。別distへ切替えない |
| B6-U02 | Python 3.11 / 3.12のsource/build互換性 | 2026-09-18のユーザー決定により、Windows onefile公開判定から外した。将来support policyとして確認する場合だけ、利用可能なPython環境・隔離先とmatrix実施範囲を定める | 未検証として記録するがG-READY非阻害。宣言下限やonefile成功で互換性確認済みとは表示しない |
| B6-U03 | 完全なFFmpeg external-library対応と対応ソースの具体的な提供物・方式・実提供 | 2026-09-18のユーザー判断により、GitHub remoteでの既存公開を規約上問題なしとしてG-READYへ採用した。Codexはremote ref・追跡files・候補branchとの差分を確認し、法的適合を保証しない | ユーザー方針に従いG-READY非阻害。公開物・提供方式を変更する場合は、対象・法的判断者・確認範囲を別途定義する |
| B6-U04 | 配布readmeの表現、候補採用THIRD_PARTY_LICENSESとcurrent追記の採否 | 配布文書の修正が不可欠と判明した場合、修正内容・新候補化・B4/B5再検証を提示。NOTICE正本bytesの変更が必要ならその対象と理由を確認 | 必要文書が未同期のためHold。候補を書換えない |
| B6-U05 | clean Windows追加確認の必要性 | 現在のB5独立性証拠に具体的な欠陥が見つかった、または受入環境の拡大が要求された場合のみ、利用可能環境・実施者・対象操作を確認 | 既存の観測限界だけなら維持。新たな必須不足がある場合は関連gate Hold |
| B6-U06 | MS27 closeoutの明示決定、後続公開の具体的範囲 | B6 Passとなりcloseout同期が未指示なら、その決定を確認。公開は別依頼で、候補hash・提供物・source archiveのFFmpeg/素材扱いを具体化 | 判定報告で止める。公開、tag、push、素材同梱をしない |

exact provider archive identityが未確認であるという既知の制限だけを理由に、B3方針の再承認を求めない。Python / FFmpegについて、2026-09-18のユーザー受容方針とremote確認の範囲を超える変更がなければ、未検証を理由にG-READYをHoldへ戻さない。MS27 closeoutと公開は、B6 Passとは別の明示決定・別工程である。
