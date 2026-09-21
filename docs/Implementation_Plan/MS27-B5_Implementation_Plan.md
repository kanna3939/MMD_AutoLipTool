# MS27-B5 Implementation Plan

## 1. 文書情報

- 対象: MS27-B5 ZIP候補組立・展開・配布環境確認
- 作成日: 2026-09-14
- 計画作成時ブランチ / HEAD: `feature/MS27-implementation` / `ee056d4 Resolve MS27-B4 artifact packaging findings`
- 開始時作業ツリー: clean。current branchのupstream表示なし。remoteへの照会は行っていない。
- 計画時状態: **Planned / 計画作成。B4は完了・G-ARTIFACT Pass。B5実施・G-PACKAGE判定は未着手。**
- 実装後状態: **Implemented / Verified / G-PACKAGE Pass（2026-09-16）。候補#07の過剰なmodule除外を補修し、候補#08の静的・GUI検証を完了。スプラッシュ版数はユーザー目視確認。現在状態は§15.4を優先する。B6・公開判定は未実施。**
- 計画作成時の変更範囲: 本ファイルのみ。以下のZIP生成、Windows実行、文書配置、検証は計画作成時点では未実施であり、実装時の結果は§15.1へ追記する。
- 正式版数: `1.0.0`。FileVersion / ProductVersion文字列も`1.0.0`。
- 固定EXE名: `MMD_AutoLipTool.exe`
- 固定ZIP名: `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`。Block Breakdown §8.1の確定値を継承し、RC suffix等を追加しない。
- 最終検証・採否・統合の責任: メインエージェント。追加サブエージェントは起動しない。計画作成担当のクローズ操作は行わない。

## 2. 背景

MS26 CloseOut Aを機能基準として継承し、MS27-B1〜B4は実施済みである。B4はfix-03候補のbuild / SmokeLaunch、内部archive監査、版数照合と不要component排除を完了した。ユーザーから手動確認通過・実MMDでも問題なしとの報告を受領している。これはユーザー報告であり、Codex自身のGUI / MMD操作結果ではない。

B5は、同じ候補を利用者へ渡すZIPとして組み立て、展開後の実物と動作を確認する工程である。B4のSmokeLaunchは5秒の生存確認と強制停止・残留処理であり、通常GUI終了や開発環境からの独立性の証拠を代替しない。

### 2.1 参照した現行根拠

| 根拠 | B5へ対応付けた内容 |
| --- | --- |
| [MS17 Index](../MS17_and_Beyond_Index.md) | 履歴routing。現在地はMS20以降のIndex / Roadmapへ進む |
| [MS20 Index](../MS20_and_Beyond_Index.md) §2、見出し「MS27-B5実装・配布候補確認記録」 | MS27 active、B5 G-PACKAGE Pass、B6未実施。B4の同番号ではない履歴見出しと区別し、B5実施前の「B5/B6未実施」は過去記録として扱う |
| [Roadmap](../MS20_and_Beyond_Roadmap.md) §14、§14.5 | onefile / 配布確認とB6 readinessの境界 |
| [MS27 Block Breakdown](MS27_Block_Breakdown.md) §1、§8.1、§8.4、§9 B5、§10〜12 | 固定ZIP名、必須5ファイル、同梱・除外、失効、G-PACKAGE |
| [B1計画](MS27-B1_Implementation_Plan.md) §8のpath契約、§17.1、§18.1.1 | Windows 11 Pro / build 26200 / 64bitの記録、Python 3.14.3の開発環境、配布環境はB5未取得、所有作業領域 |
| [B3計画](MS27-B3_Implementation_Plan.md) §15〜17 | G-LICENSE Passのユーザー決定、公式参照、原文候補、ZIP実配置・provenance limitation |
| [B4計画](MS27-B4_Implementation_Plan.md) §15〜17 | C22〜C25、M07〜M09、F06〜F08解消、fix-03 identity、B5 handoff |
| [Release Package Manifest](../Release_Package_Manifest.md) §2.1、§3〜5 | EXEを含む必須5ファイル、追加license原文・必要対応物、weights非同梱 |
| [NOTICE](../../NOTICE)、[THIRD_PARTY_LICENSES](../../THIRD_PARTY_LICENSES.md)、[LICENSE](../../LICENSE) | G-LICENSE採用方針、実配置の未確定、本文保持、埋込み入力との照合 |
| [README](../../README.md)、[配布readme](../../readme_mmdautolip.txt) | 現行操作、モデル未配置・明示取得、出力、Python不要の配布形態 |
| [build.ps1](../../build.ps1)、[spec](../../MMD_AutoLipTool.spec)、[pyproject](../../pyproject.toml)、[Torch hook](../../build_hooks/hook-torch.py) | build / smokeにZIP組立機能はない。onefile内3通知文書、FFmpeg配置、resources、version、除外の実設定 |
| `src/resource_utils.py`、`src/app_version.py` | frozen resourceは`sys._MEIPASS`。現行版数解決はproject resourceを優先し、installed metadataへfallback |
| `src/core/ffmpeg_locator.py`、`settings_store.py`、`whisper_model_store.py`、`whisper_model_loader.py` | FFmpeg探索、EXE隣接設定・models、検証済みbytesからのモデル読込境界 |
| `tests/test_app_version.py`、`test_ms27_b2_windows_version_resource.py`、`test_whisper_model_catalog.py`、`test_ms17_b3_ffmpeg_locator.py`、`test_whisper_model_loader.py` | version / resource / 同梱設定 / locator / no-downloadに関連する既存テスト。今回未実行 |

Block Breakdownの初期調査表やB1/B3の旧「未実施」は作成当時の履歴とする。現行`pyproject.toml`は`1.0.0`、specには旧Qt・matplotlib・Torch test/TensorBoard・TBB任意backendの除外がある。`THIRD_PARTY_LICENSES.md`のmatplotlib同梱想定・Qt未確定の記述は、B4の最終内部監査より優先しない。B5では実際の同梱物との文書差分として扱う。

### 2.2 計画作成時に独立確認した候補と差分

| 項目 | 現在確認した値 / 証拠の限界 |
| --- | --- |
| B4候補EXE | `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260914-fix-03\source\dist\MMD_AutoLipTool.exe`。`Get-Item`で実在・425758214 bytesを再確認 |
| EXE SHA-256 | `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`。今回`Get-FileHash`で再取得しB4 C24と一致 |
| PE版数、build / SmokeLaunch、内部archive | B4 C22〜C25 / M07等の記録を継承。今回はPE照会、archive展開、EXE実行をしていない |
| fix-03 sourceの`NOTICE` SHA-256 | `AEF4C21E60D17FC5C75BEBF64CC1767D7779BB66C5BDF7E3F71F7D736C345A43` |
| 現在repoの`NOTICE` SHA-256 | `4C8279CB4B6169CE5B4F9A0D28C83F2FABE4D965BA24F73E80DA8E08B44A864D` |
| NOTICE差分 | `git diff --no-index`でB4結果・ユーザー報告12行の追記を確認。exit 1は差分ありを意味し、アプリ実行失敗ではない |
| LICENSE / THIRD_PARTY_LICENSES | repoとfix-03 source間のSHA-256はそれぞれ一致。`B8F2522DC6C050ED79F624CE5849A5E1C135504307B4C982A5BD7750A3277523` / `B65413AB4F91DFE84E1CA941AA8A1A32A4E36CB9EDA06536E2D68F3369874CC4` |

この差分はB4完了記録を取り消すものではない。ただし、現行文書から組むB5候補とfix-03 build入力は同一ではない。specがNOTICEをEXEへ埋め込むため、Block Breakdown §10の失効規則に照らした候補採用ゲートを§6に設ける。source間の比較を、fix-03内部bytesの今回独立照合済みとは記録しない。

## 3. 目的

1. B4合格EXEと付属文書のidentityを保持したZIP候補を、許可一覧だけから作成する。
2. ZIP・展開後全ファイル・EXE内部・原文対応を結び付け、欠落と混入を検出する。
3. Windows 11でPython / repo / PATH上のFFmpegに依存せず、起動・必要resources利用・通常終了できることを確認する。
4. 同一候補に結び付くG-PACKAGE判定と、B6へ渡す証拠・残事項を残す。

## 4. In Scope

以下はB5実装依頼後の範囲である。

- 候補EXE、B4証拠、現行埋込み入力の差分確認と、失効・非失効の採否記録
- 必須5ファイルと実同梱componentに対応する原文・通知・必要対応物の許可一覧確定
- 新規のローカル領域でのZIP組立、別領域への展開、全ファイル照合
- Windows配布検証環境、独立性、素材、モデル、実行者、process観測方法の固定
- 通常GUI、版数、resources、FFmpeg / ffprobe、辞書・tokenizer、モデル未配置と既存検証済みモデル使用の最小ケース
- license / 配布readme / Manifestの必要な同期案と、許可されたB5実装時の同期。埋込み入力を変更する場合は§10の失効処理を先行する
- B5台帳、G-PACKAGE Pass / Hold、B6 handoff

## 5. Out of Scope

- 今回の計画作成でのコード修正、test / build / compileall実行、ZIP・EXE生成、GUI / MMD操作
- B6最終release readiness、MS27全体closeout、公開、tag、stage / commit / push / merge、ブランチ変更
- B5からの自動再ビルド、spec / hook / production code補修、依存追加・更新、FFmpeg差し替え。必要ならowner=B4または別の限定補修として返す
- installerや新たな配布方式、公開先の決定・外部へのupload、Source code archiveの実生成
- runtime JSON / INIの直接編集・コピー・削除・fixture化、既存ユーザーデータの破棄
- weights / sample / ユーザー素材 / 生成物の同梱、実download、ネットワーク設定やOS featureの無断変更
- MS26 / B4の実MMD受入の再判定・4ケース再提出。B5の必須確認へ実MMD操作を追加しない
- Python 3.11 / 3.12のsource / build互換性matrix。外部Python不要のEXE確認と区別し、未検証としてB6へ渡す

## 6. 前提条件

| Gate | 開始・解除条件 | 未充足時の扱い |
| --- | --- | --- |
| B5-G-INPUT | live Git、EXE path/size/hash、B4 Pass、input差分・失効の採否が対応する | 内容調査は継続可。配布候補として固定・Passにしない |
| B5-G-DOCS | 必須5＋必要原文・通知の具体的な全相対path、由来・hash・適用対象が決まる | 原文候補収集・不足記録まで。仮ZIPは未完成と明記 |
| B5-G-PATH | 組立・ZIP・展開・実行・evidenceの新規所有絶対pathを固定し、既存物と分離 | copy / 圧縮 / 起動に進まない |
| B5-G-ENV | Windows 11環境、非開発実行条件、素材・モデルの利用範囲、実行権限と観測方法を固定 | 静的ZIP確認は可。独立性・GUI gateは未確認 |

**既知の入力差分:** 現行NOTICEを採用する場合、既存規則では影響するB4/B5証拠をstaleとし、文書を最終化してからB4 ownerへ再build・内部監査・SmokeLaunchを返し、新identityを受領する。B5担当がfix-03を現在入力からのbuildとして扱わない。fix-03をそのまま最終候補にしたいという別判断がある場合は、埋込み版と外側版の採用・差分・失効規則の例外を明示して判断を受ける。本文書だけで例外を新設しない。計画作成や独立したlicense・path調査の完了を妨げる条件ではない。

B3のG-LICENSE Passは継承する。元Windows archiveの厳密identity、binary revisionとlicense revisionの一致は非阻害の制限として保持し、再びB3 Holdにしない。一方、Manifestで要求される原文のZIP実配置はB5の条件である。リンクだけの配置や未確定の対応物を実配置済みにしない。

## 7. 対象ファイル

| 分類 | 対象 | B5での扱い |
| --- | --- | --- |
| 今回作成 | `docs/Implementation_Plan/MS27-B5_Implementation_Plan.md` | 唯一の編集対象。実施時にも台帳・結果を追記する正本 |
| B5入力 | §2.2のEXE、B4 plan、`build.ps1`、spec、hook、version resource、pyproject、FFmpeg / resource入力 | read-onlyで有効性を照合。rootのdist / EXEを代用品にしない |
| 配布文書 | `readme_mmdautolip.txt`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` | 全文bytesを採用・照合。LICENSE本文を変更しない。今回編集しない |
| 後続同期候補 | `docs/Release_Package_Manifest.md`、`README.md`、上記配布文書 | B5実施に必要な配置・操作・実同梱の差分だけ。埋込み文書変更はB4へ返す |
| 原文入力 | B3に記録された`.venv`配下license / COPYING、FFmpeg公式参照資料 | 実環境・version・原文との対応を再確認。環境全体をコピーしない |
| 後続出力候補 | 新規作業領域の`zip-input/licenses/<component>/<version-or-build>/<original-relative-path>` | 未作成。必要原文を省略せず配置し、実pathを一覧化する。repoに新しいlicenses treeを作ることを必須にしない |
| 関連テスト | §11の実在テスト | 今回閲覧のみ。将来のコード等の補修時にownerが対応検証を選ぶ |
| B6担当 | Index / Roadmap / milestone / Version Control | 最終状態同期はB6。本計画作成では編集しない |

必須5ファイルは「EXE 1件＋付属文書4件」であり、5文書と解釈してREADME等を独断追加しない。

## 8. 実装方針

### 8.1 所有pathと組立

作業root候補は`C:\tmp\MMD_AutoLipTool_MS27\B5\<run-id>\`。これは今回作成・存在確認したpathではない。実装時に一意なrun-idと空き容量を確認して新規作成し、絶対pathを記録する。

| 子領域 | 用途 |
| --- | --- |
| `zip-input/` | 許可ファイルだけの未起動の組立元 |
| `zip-output/` | 固定名ZIPの保存先。組立元の外側 |
| `zip-extracted/` | ZIPを展開し、起動前一覧と全hashを検査する領域 |
| `distribution-run/` | 同じZIPを改めて展開して動作を確認する領域 |
| `evidence/` | 入出力一覧、hash、ログ、環境、process、手動結果。ZIP対象外 |
| `inspection/` / `temp/` | 必要な内部照合・実行一時領域。ZIP対象外 |

Windowsの大文字小文字、相対成分、reparse pointを考慮して所有root内へ解決することを確認する。既存pathの上書き、利用者directoryとのmerge、`dist`全体やrepo全体の圧縮をしない。中断後の再試行は新規領域と新証拠IDを使用し、旧候補とログを保持する。

### 8.2 ZIP許可・除外契約

ZIP root直下は次の5ファイルと確定した`licenses/`等の必要対応物だけとする。親の`zip-input/` directoryをZIP entryへ含めない。

```text
MMD_AutoLipTool.exe
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
licenses/<確定したcomponent・原文の相対path>
```

追加licenseはB3の候補一覧とB4最終componentを突き合わせる。Python runtime、wx、NumPy/native、Whisper、pyopenjtalkと辞書、tiktoken、Torch、Numba/llvmlite、その他実際の推移・vendored/native component、bootloaderの必要通知を対象にする。`.venv`に存在するだけのpackageを同梱済みとしない。matplotlib / 旧Qtの不要な原文追加を理由に、除外済み実体を再導入しない。

FFmpegはB3の公式参照・取得経路の決定を保持し、原文候補`LICENSE.md`、`COPYING.LGPLv2.1`、`COPYING.LGPLv3`、`COPYING.GPLv2`、`COPYING.GPLv3`と追加通知・必要対応物を確認して配置する。参照資料の既取得hashはTHIRD_PARTY_LICENSES §3.8.1から継承できるが、ファイルの現存・内容は実装時に確認する。原文取得にネットワークが必要なら公式一次資料と取得日時・URL・hashを記録し、環境の権限申請に従う。正確な配布元archive不明を埋めるための推測URLや自作ライセンス本文を使わない。

配置と延期の判定は次の表に従う。B3の非阻害決定を、B5の必須ファイル省略へ拡張しない。

| 区分 | B5で必要な内容 | G-PACKAGE / B6への影響 |
| --- | --- | --- |
| 必須の候補・ZIP構造 | §6の入力gateを満たすB4候補EXEと上記4付属文書を固定名ZIPのroot直下に置く。全entryを許可一覧へ対応付け、展開後もEXEのsize/hashと全ファイルの一致を確認する | 欠落、別EXE、構造・hash不一致はB5 Hold。B6への延期でPassにしない |
| 必須の原文・通知・ZIP同梱対応物 | 実同梱componentに必要なlicense/COPYING本文、copyright/NOTICE、およびZIP同梱が必要と確認された対応物を、具体的な相対path・由来・size/hash付きで配置する | 未取得・欠落・対象不明で配置の充足を判断できない場合はB5-G-DOCS / AC02 / G-PACKAGE Hold。概要・URLだけで原文配置を代替しない |
| B3決定による非阻害のprovenance制限 | exact Windows archive identity、license revisionとbinary revisionの厳密一致、完全なexternal-library対応の未確認は、B3の採用根拠・制限として記録する | これらの制限そのものではB3 Passを取り消さず、B5 Holdにも直結させない。ただし調査で具体的な必須通知・配置不足が判明した場合は上段で判定する |
| 対応ソースの提供方式・B6公開前確認 | ZIP外での提供方式・提供先の確定や実提供の確認は、B5必須配置の充足を確認でき、未確定の方式がZIP内容に影響しない根拠、担当、解消条件を台帳へ残せる場合に限りB6へ延期できる | この条件を満たす延期はB5 Passを妨げないが、提供方式・必要な履行が未確認のままB6の公開Readyにしない。ZIPへの同梱・案内追加が必要か判断できない場合や、必要と判明した内容が欠ける場合はB5 Hold。B6でZIP変更が必要になれば§10に従いB5証拠を更新する |

除外はruntime `presets.json` / `profiles.json` / `MMD_AutoLipTool.ini`とbackup、`models/`・weights・`.part`、sample、音声・TEXT・PMX/PMD・MMD本体・VMD/WAV/report、開発src/tests/docs/.git/.venv/.agents/.codex、AGENTS、build/spec/hook/version resource入力、inspection/temp/cache、`*.log` / `*.tmp` / `*.bak` / 開発`*.pyc`とする。ライセンス条件に必要な確定した対応ソースは、開発src除外を理由に排除せず別途採用表へ明示する。onefile内部の実行modules、manifest、辞書、tokenizer等は拡張子だけで排除しない。

### 8.3 配布環境と証拠の強さ

Windows 11 / architecture / buildを実行時に採取する。B1のWindows 11 Pro build 26200は既存記録であり、未提供の別端末やVMの値へ転用しない。

第一候補は、repo・開発Python・FFmpegを配置していない利用可能なWindows 11環境である。利用可能性は未確認。既存環境で実施する場合は新規展開先、repo外cwd、子processだけの環境設定でPython / repo / FFmpeg pathを除外し、Python関連環境変数を継承しない。必要なWindows標準pathとTEMPを保ち、ユーザー / machine環境変数を変更しない。観測用Pythonの使用とEXEがPythonを必要とすることは区別する。

PATH除去だけで独立性をPassにしない。実processのEXE path / 子process / 読込module / FFmpegの起動path等、利用可能な観測からrepo・`.venv`・外部FFmpegによる補完がないことを示す。観測不能なら制限を残し、独立環境またはユーザーの対応する証拠で補完するまで当該gateをHoldとする。OS標準DLLを開発環境依存と誤判定しない。

通常起動では明示されたユーザー対話用ウィンドウを表示する。観測helperは非表示とする。管理者・GUI・process照会等の権限が必要な場合は対象操作を具体化して申請し、AV無効化、恒久PATH変更、既存repoの移動・アクセス禁止変更を代替手段にしない。

## 9. 詳細ステップ

### Step 1: 候補入力を再確認する

live HEAD / treeと§2.2のEXE size/hashを再取得し、B4 C22〜C25 / M07〜M09を結ぶ。spec、hook、pyproject、resources、FFmpeg、埋込み3文書を選択候補の入力と照合する。NOTICE差分を含むB5-G-INPUTの判定を記録する。欠落・差替えは旧identityを上書きせずfinding化する。

### Step 2: 原文・付属文書を最終化する

必須4付属文書と追加原文の`source絶対path → ZIP相対path → size/hash → component → 根拠`を全件確定する。THIRD_PARTY_LICENSESの古い同梱想定等は最終componentに合わせた同期対象として列挙する。埋込み文書を同期する場合は最終化後にB4 ownerへ返し、新候補と有効証拠を受領してからStep 3へ進む。原文ファイルが未取得なら取得または提供条件を記録する。

### Step 3: 空の領域へ組み立てる

§8.1の絶対pathを固定し、所有・既存物非接触を確認する。EXEと採用一覧のファイルを一件ずつ対応付けてコピーする。runtime設定や利用者素材を参照先から一括copyしない。組立後の全相対path、size、SHA-256を取得し、採用一覧との完全一致を確認する。再帰的に列挙し、hidden filesも検査する。

### Step 4: ZIPを生成して内容検査する

Windows標準の圧縮手段を使用し、実施時に採用する手段・version・commandを記録する。組立root内容のみを固定名ZIPへ格納する。圧縮手段がhidden entriesを省略する等の差を、採用一覧とZIP entryの一致検査で検出する。

ZIP size/hash、entry一覧、entry数、全fileの非圧縮sizeを取得する。rootの5ファイル、全追加原文、除外対象0件、不要な親directoryなしを確認する。絶対path、`..`、重複名・Windows大小文字衝突、所有root外へ解決するentryを受け入れない。ZIP自体とevidenceをZIPへ含めない。

### Step 5: 新規領域へ展開し全件照合する

Step 4のZIP hashを照合してから`zip-extracted/`へ展開する。展開前にentryの安全性を検査し、既存directoryへ上書きしない。展開した全fileの相対path、size/hashを組立表へ一対一照合する。EXEはB4採用identityと一致、FileVersion / ProductVersion文字列はともに`1.0.0`であることを確認する。ZIPの文字文書を実際に開き、読めること・原文保持を確認する。

### Step 6: モデル未配置の通常GUIを確認する

同じZIPを未使用の`distribution-run/`へ展開し、起動前一覧を固定する。設定・モデル・cacheを既存環境から移植しない。SettingsStoreはfrozen時にEXE隣接INIを使い、modelsも同隣接が既定である。検証後の生成データはこの領域に留める。

子process用の独立条件で絶対EXEを起動し、§11のM01〜M04を確認する。モデル未配置時の起動・候補一覧・案内・安全な失敗と、暗黙downloadがないことを確認する。ネットワークが到達不能であることだけを、downloadを試みなかった証拠にしない。既存loader契約・実行時案内・ファイル差分・利用可能な通信観測を組み合わせ、観測限界は残す。

### Step 7: 必要resourcesの実利用と正常終了を確認する

非配布の検証素材と、manifest size/hash確認済みの既存ローカルモデルを固定し、§11のM05〜M07を行う。モデル保存先はGUIのmanaged操作で非配布領域を指定する。実downloadは含めない。既存モデルが使えない場合は素材・モデル提供または別途実downloadの明示依頼が必要と記録し、モデルあり検証を省略してPassにしない。

通常終了操作は実装時に画面と実行者に合わせて記録する。起動process handleを保持して終了codeを採取し、同一EXE絶対pathの親・子processと当該runのFFmpeg / ffprobe残留を確認する。別の利用者processを名前一致だけで停止しない。強制停止は異常時の別記録とし、通常終了Passの証拠には使わない。

### Step 8: G-PACKAGE判定とhandoff

起動後に配布対象のEXE / 文書が不変であることを確認し、runtime生成物の所在を記録する。未起動組立元と元ZIPを保持し、実行directoryを再圧縮しない。§12のACを証拠IDへ対応付け、Pass / Hold、未確認、B6担当事項を記す。

## 10. 状態遷移 / データ契約

```text
B4完了・候補あり
  → input / docs / path確認
  → ZIP組立 → ZIP entry監査 → 展開後全hash一致
  → 配布環境・通常GUI・resources・正常終了
  → G-PACKAGE Pass → B6へhandoff
各段階の不一致・未取得 → 対応gate Hold（独立する確認は継続可）
```

| 変更・観測 | 失効と再確認 |
| --- | --- |
| code、依存、spec/hook、FFmpeg、resource、pyproject、埋込み3文書の変更 | 影響するB4証拠とそのEXEを含むB5証拠をstale化。owner=B4から新候補・監査・smokeを受領 |
| ZIP外側だけのreadmeや追加原文配置・内容変更 | ZIP hash / 一覧 / 展開照合を更新。EXE不変とB4非失効理由を記録。GUI再確認は変更の影響に応じる |
| EXE bytesの不一致・消失 | コピー済み候補も含め使用停止。勝手な別dist選択・旧hash付替えをしない |
| OS / 環境 / 起動path / モデル条件の変更 | 対応する実行証拠を新条件で再取得。静的一覧・EXE hashが不変ならその証拠は再利用 |
| 非配布の状態文書だけの追記 | 配布bytesと実行条件に影響しない根拠を残し、既存証拠を再利用 |

証拠単位は`HEAD + 対象差分/入力hash + EXE hash + ZIP hash + 環境/実行条件`とする。commit日時やファイル名だけで候補を識別しない。B4 fix-03の生成は現HEADのcommitより前であり、現HEADからそのままビルドしたと記載しない。

## 11. テスト方針

### 11.1 自動・静的検証

B5の基本作業は組立と実物照合である。候補EXEと採用build入力のidentityが対応し、§10のB4証拠失効条件に該当しないことを確認できる場合に限り、既存B4証拠を再利用して再buildを省略する。コード不変でも埋込み文書・依存・spec/hook・resource等の変更は同節に従い、影響するB4再build・内部監査・SmokeLaunchとB5再確認を必要とする。ZIP外側だけの変更はB4非失効の根拠を記録してZIP・展開照合を更新する。full pytest / compileallは一律に追加せず、補修ownerが変更・失敗・未解決リスクに対応する検証を選ぶ。必須はinput hash、全file許可一覧、ZIP entry、展開後全hash、PE版数、文書閲覧、実行processと環境の証拠である。実行するPowerShell / 検査processの終了コードを取得する。

補修が別途必要になった場合の関連入口は次のとおり。既存テストを実ZIP検証の代用にはしない。

| 対象 | 既存テスト | 追加・再実行の条件 |
| --- | --- | --- |
| 版数 / frozen resource | `tests/test_app_version.py`、`tests/test_ms27_b2_windows_version_resource.py` | ownerがversion/resourceへ影響する補修を行った場合 |
| spec / custom hook / manifest | `tests/test_whisper_model_catalog.py` | B4収集設定を補修した場合。修正後EXE内部の再監査も必要 |
| FFmpeg探索 | `tests/test_ms17_b3_ffmpeg_locator.py` | locator挙動を補修した場合 |
| verified-local / no-download | `tests/test_whisper_model_loader.py` | loader契約を補修した場合 |

### 11.2 Windows実行・ユーザー確認matrix

| ID | 条件と操作 | 期待結果 / 必須証拠 |
| --- | --- | --- |
| M01 | 新規展開・repo外cwd・独立環境で通常起動 | スプラッシュ`Ver. 1.0.0`、wx主要画面、icon / toolbar / splash表示。実EXE path/hash・実施者を記録 |
| M02 | 初回モデル未配置で候補一覧と案内確認 | small / medium / turbo表示。候補選択のみでdownload・解析・active変更なし。未配置からの解析は案内・安全な失敗 |
| M03 | 外側のreadme / LICENSE / NOTICE / 第三者原文閲覧 | 日本語と原文を読める。entryと原文hashに対応し欠落なし |
| M04 | 子processの環境・resource/FFmpeg解決観測 | external Python / repo / PATH FFmpegの補完なし。同梱FFmpeg/ffprobe解決を実動作とpath等の観測で裏付ける |
| M05 | ZIP外の短い対応音声WAV / MP3 / M4Aを読込・変換 | 各形式でprobe / 解析用WAV / 波形、MMD用WAV出力が成立。使用素材・実path・出力を非配布証拠へ記録 |
| M06 | 検証済みローカルモデルでTEXT＋音声とvoice_onlyの短い各1ケース | pyopenjtalk辞書、Whisper assets / tokenizer / Torch経路、解析・Preview・VMD保存が成立。モデルのsize/hash、素材、出力を記録。MMDでの見た目再受入ではない |
| M07 | アイドル状態から通常終了し、同じ展開先で再起動・通常終了 | 設定保存と再起動が成立。app通常終了code、観測した親子process終了、残留なし。強制停止ではPassにしない |

M05/M06素材の具体的pathと使用権限、モデルpath、M07の具体的な終了操作は今回未確定。既存資料から架空のテスト操作を補わず、実行前に固定する。必要な操作が現行GUI上で可能か確認し、結果に応じて項目を細分化する。

ユーザーが行う場合は各Mxxについて実施者、日時、ZIP / EXE hash、環境、操作・実結果、通常終了codeの取得有無を記録する。B4の「手動確認通過、実MMD問題なし」という包括報告を、このmatrixの全項目・独立環境・通常終了codeまで実施済みとはしない。通常終了code未取得は`unknown`であり、B4 wrapper exit 0で補完しない。

## 12. 受け入れ条件

| ID | 条件 |
| --- | --- |
| B5-AC01 | B4 Passと採用EXEのpath/size/hash、live baseline、入力差分・失効判定が対応し、B5-G-INPUTを満たす |
| B5-AC02 | §8.2の必須5ファイル、必要な全原文・通知・ZIP同梱対応物を実配置し、許可一覧・由来・size/hash・実ZIP相対pathと照合した。必須配置欠落・充足判断不能はHold。非阻害のprovenance制限とB6延期事項を別記し、延期は同節の条件を満たすことを確認した |
| B5-AC03 | 新規所有作業領域を分離し、既存build/dist/exe・既存成果物を上書き・削除せず、既存runtimeデータを直接編集・コピー・削除していない。§7で許可された文書編集、新規作業領域への採用EXE・付属文書のコピー、同領域での生成・managed persistenceは区別して記録した |
| B5-AC04 | 固定ZIP名、root配置、全entryと許可一覧の一致、除外対象非混入、安全なentryを確認した |
| B5-AC05 | ZIP hashと全展開ファイルhashが入力表へ対応し、EXEは採用B4候補と一致、PE両文字列は`1.0.0` |
| B5-AC06 | ZIP内文書が読め、license / NOTICEと実同梱物の対応、埋込みと外側の差分採否を記録した |
| B5-AC07 | Windows 11の環境情報とrepo / Python / 外部FFmpegからの独立性を証拠で確認した |
| B5-AC08 | M01〜M06で通常GUI・必要resources・モデル未配置・検証済みローカルモデルの利用が成立した |
| B5-AC09 | M07の通常終了・再起動、取得したapp exit code、対象process残留なしが記録され、必須processの非ゼロ・unknownが残らない |
| B5-AC10 | 起動後runtime / cache / 素材 / 生成物をZIPへ戻さず、候補bytesと証拠が一致している |
| B5-AC11 | 各AC、P1/P2/P3、未確認、B6引継ぎを対応付け、ユーザー報告・Codex実行・未実行を区別した |

G-PACKAGE PassはAC01〜11を満たし、B5受入に関係する未解消P1/P2・必須未確認がない場合に限る。静的ZIP検査済みでも通常GUIや独立性が未確認なら該当gateはHoldとする。B3が非阻害としたprovenance limitationは保持するが、B5の実配置不足や実行失敗を同分類へ移さない。G-PACKAGE PassはB6 readiness判定・公開許可ではない。

## 13. リスクと対策 / 未確定事項

| ID | 現在状態 / リスク | 解消条件・owner |
| --- | --- | --- |
| B5-U01 | 解消。現行`NOTICE`とB5採用候補を同じ再build入力へ固定し、埋込みhashも一致 | 後続で`NOTICE`またはspecを変更した場合は、同じ失効規則でB4/B5を再検証 |
| B5-U02 | 静的範囲は解消。実凍結PYZの主要runtime packageとZIP外側原文の対応を固定。FFmpeg provider/archive correspondenceはB3由来の非阻害provenance limitationとして保持 | 公開前に必要ならFFmpegの選択バイナリと対応ソース・外部ライブラリの追加確認をB6で行う。B5の必須ZIP配置欠落は確認されていない |
| B5-U03 | 解消。候補#08のWindows-only PATH / Python環境変数なしの子process、実ロードmodule、同梱FFmpeg pathと実動作を確認 | §15.4の観測範囲でPass。clean OS・完全なprocess/network traceではない制限を保持 |
| B5-U04 | 解消。候補#08のM01〜M07、Codexによる通常終了・再起動とexit 0を確認。スプラッシュ版数だけはユーザー目視確認 | §15.4参照。旧runの終了操作者不明をCodex通常終了証拠へ転用しない |
| B5-U05 | 解消。必須runtime moduleを限定復元し、import回帰・再build・内部監査・frozen解析が成功 | PySide6/Matplotlib本体等の除外を維持。新規PYZ top-level packageなし、原文対応を再照合 |
| B5-U06 | FFmpeg provenance制限と対応ソース提供方式が未確認。必須配置の充足とは分けて扱う | §8.2の分類表に従う。B3が採用した非阻害制限は保持。ZIP必須配置の欠落・充足判断不能はB5 Hold。ZIP内容に影響しない根拠・担当・解消条件を記録できる提供方式の確定・実提供確認だけをB6へ延期し、その延期自体はB5 Passを妨げない。B6は必要な公開前確認を満たすまで公開Readyにしない |
| B5-U07 | Python 3.11 / 3.12互換性は未検証 | 外部Python不要の配布確認とは別欄でB6へ継承。今回matrix実行やPython導入をしない |

現在、計画ファイルを完成させるためのユーザー回答は不要である。B5実行時に既存権限・実物調査で解消できなかった場合だけ、次の具体的事項を質問する。

- fix-03をそのまま採用する指定がある場合: 現行NOTICEとの不一致について、既存失効規則に従うB4再検証とするか、埋込み版・外側版の扱いを明示して候補採用規則を変更するか。
- 独立環境をエージェント側で用意・観測できない場合: 利用可能なWindows 11確認環境と実施者、M01〜M07の結果を提供可能か。
- モデル・素材が既存許可で特定できない場合: 使用してよい既存のローカルモデルと短い検証素材のpath。

これらを理由に、計画作成や依存しない調査を中断しない。追加のdownload・OS変更・再build・binary変更が必要なら、対象・理由・既存許可との差を示して実行環境の申請手段を使う。

## 14. Codex 実装時の注意

- 1 commandずつ実行し、結果を待つ。連結・パイプライン・並列シェル実行を行わない。
- 計画の作成権限をB5実装・B4再実装・Git変更の許可と読み替えない。
- 部分的な成功表示だけでPassにせず、runnerの最終exit codeを確認する。PowerShell cmdlet結果を直前の`$LASTEXITCODE`で代用しない。
- GUIとprocess観測を分け、user report / Codex observed / inherited / plannedを台帳で明示する。
- 権限失敗は対象操作に絞って申請する。タイムアウトだけで失敗や通常終了と判定しない。
- 既存runtimeデータを持ち込まず、アプリによるmanaged persistenceを新規実行領域で使う。ユーザーのmodelsを削除・改変しない。
- 新規failureが見つかった場合は具体的なownerへ返す。テスト弱体化、手動項目削除、未取得を0扱いする方法で合格にしない。
- 作業前の仮説・権限と、完了前の現行差分・反証・証拠を再照合する。今回のNOTICE差分は未解消のまま明記する。
- 計画作成後にサブエージェントをクローズする操作は行わない。追加エージェントを起動しない。

## 15. Evidence ledger

実装時のcommandは`MS27-B5-Cxx`、手動・静的照合は`MS27-B5-Mxx`、findingは`MS27-B5-Fxx`とする。§11のM01〜M07は検証項目IDであり、実施証拠IDと関連付けて記録する。

```text
ID / phase(planning, implementation, user report) / owner / 対応AC:
日時 / 実施者 / HEAD / tree差分 / 入力hash:
cwd / 単独command / OS・環境条件 / 素材・モデルidentity:
期待 / 実結果 / process exit codeと取得元:
親子process / 通常終了・強制停止 / 観測不能・未取得の理由:
EXE・ZIP・全付属fileのpath / size / SHA-256 / entry:
log・一覧の所在 / Pass・Hold / Fxx・Uxx:
継承元 / stale対象 / 非失効理由 / 次owner:
```

今回の計画段階で取得した主な証拠は以下。全件read-onlyである。

| ID | 操作 | 結果 | exit |
| --- | --- | --- | --- |
| MS27-B5-C01 | `git status --short --branch` | `feature/MS27-implementation`、開始時clean | 0 |
| MS27-B5-C02 | `git branch -vv` | current HEAD ee056d4、upstream表示なし | 0 |
| MS27-B5-C03 | `git log --oneline -n 10` | B4 commitとB1〜B3履歴を確認 | 0 |
| MS27-B5-C04 | fix-03 EXEへの`Get-Item` | §2.2の実在・size | 0 |
| MS27-B5-C05 | fix-03 EXEへの`Get-FileHash -Algorithm SHA256` | §2.2のhash一致 | 0 |
| MS27-B5-C06 | repo / fix-03 sourceのNOTICE hash比較 | §2.2の不一致 | 0 |
| MS27-B5-C07 | NOTICEの`git diff --no-index` | B4結果・ユーザー報告12行追記。差分あり | 1 |
| MS27-B5-C08 | repo / fix-03 sourceのLICENSE・THIRD_PARTY_LICENSES hash比較 | 各組一致。EXE内部を今回比較した結果ではない | 0 |

計画段階の記録として、後続は新IDを採番し、上記を実装結果へ上書きしない。本文・リンク・whitespaceの最終確認は計画作成報告へ記す。test / build / ZIP / GUI / MMDの実施台帳はこの時点ではまだない。実装時の結果は次項へ追記する。

### 15.1 B5実装時取得証拠

実装run: `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-input-prep-01\`

- 実行HEAD: `c091d56 Add MS27-B5 implementation plan`。作業ツリーにはユーザー提供入力 `sample/MMD_AutoLipTool説明1.wav` の未追跡状態がある。入力として保護し、stage・編集・ZIP同梱は行っていない。
- B4再検証候補: `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-notice-canonical-01\source\dist\MMD_AutoLipTool.exe`、425760033 bytes、SHA-256 `40AFB930DB8B49F3D3A69B5C175375C7E336D16CB4936E151E251ECDF5F4D6E5`。現行`NOTICE`を埋込み入力として再buildし、build / SmokeLaunch / 内部archive監査を完了した候補を採用した。
- 音声入力: `sample/MMD_AutoLipTool説明1.wav`。ffprobeでPCM signed 16-bit little-endian、44100 Hz、mono、40.458639秒、3568546 bytesを確認。SHA-256 `191068007D9674AE9DAE5C2817D3D0355010559ED2B03AA5937073AC52F7510D`。これは素材の形式確認であり、frozen GUIによるM05/M06の解析成功を意味しない。
- モデル入力: repo管理の`models/small.pt`、483617219 bytes、SHA-256 `9ECF779972D90BA49C06D968637D720DD632C55BBF19D441FB42BF17A411E794`。`whisper_models.json`のsmall定義と一致する。weightsはZIPへ含めていない。
- ZIP: `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-input-prep-01\zip-output\MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`、423168779 bytes、SHA-256 `5F221F07827BEF1C66CD9DF168633DB17D2EC4CDC916A736CFF11007B62FBEBB`。`Compress-Archive`はエラーなしで完了し、PowerShell cmdletのためnative process exit codeはN/A。
- ZIP root: `MMD_AutoLipTool.exe`、`readme_mmdautolip.txt`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`の5ファイルと`licenses/`だけを含む。不要なroot親directoryはない。
- 展開照合: `zip-extracted/`へ展開し、input 135 files / extracted 135 files、missing 0、extra 0、mismatch 0。展開後EXEのFileVersion / ProductVersionはともに`1.0.0`。
- 除外監査: `licenses/`配下の原文に含まれる`src`等の文字列は除外対象と誤認しないよう分離して判定し、license外の禁止path / runtime設定 / model / sample / 音声 / 開発ファイルは0件。
- 配布run: 同一ZIPを`distribution-run/`へ展開し、135 filesを展開後と全hash一致させた。起動時に作成したPID `9224`はメインウィンドウハンドル0、`Responding=True`、`HasExited=False`だった。`CloseMainWindow()`は`False`で通常終了できず、当該runのPIDだけを強制終了した。実行後directoryにはZIP対象135 files以外のruntime生成物はない。
- GUI / 配布環境: `cua.getState()`で利用可能なappsは空で、`cua.getApp()`操作も利用できなかった。配布EXEのGUI画面、通常終了code、外部Python / repo / PATH FFmpeg非依存性、M01〜M07は未確認。強制終了はM07 Passの証拠にしない。
- build時の既知観測: SymPyの`return` in `finally` SyntaxWarningと、PyInstallerがTorch由来の`/usr/lib64/libgomp.so.1`をbasename制約で無視したwarningがあった。build / SmokeLaunchは終了0だが、これらの原因・影響を今回のB5で修正済みとは扱わない。

実装時の暫定判定:

- `B5-G-INPUT`: 現行NOTICEを反映した新B4候補、音声、smallモデルを確認済み。台帳上は候補固定可能だが、上記untracked入力は配布対象外として保持する。
- `B5-G-DOCS`: 必須5ファイルと追加license原文を組立・展開できた。実同梱componentとの原文対応および提供方式の最終採否は、静的ZIP結果とともに継続確認する。
- `B5-G-PATH`: 新規B5作業root、ZIP、展開root、配布runを分離し、既存repoのbuild / dist / runtimeを変更していない。
- `B5-G-ENV`: **Hold**。GUI面・独立性・通常終了・M01〜M07が未確認。入力とモデルの存在確認だけでは解除しない。
- `G-PACKAGE`: **Hold**。静的ZIPとhash照合は完了したが、B5-AC07〜AC11に必要な配布GUI・独立性・通常終了・証拠対応が未完了である。

### 15.2 P2/P3補修後の再検証証拠

補修run: `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-07\`

- `MMD_AutoLipTool.spec`へ、PyTorch / NumPy / Numba / SymPy / pytest等の
  開発・テスト系に加え、`pylab`、`mpl_toolkits`、NetworkXのpylab連携、
  SymPy Matplotlib backendを除外対象として追加した。PyTorch全体やTorch
  `_inductor`は除外していない。
- B4採用候補は
  `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-final-candidate-07\source\dist\MMD_AutoLipTool.exe`、
  424433218 bytes、SHA-256
  `3E22E8EA35D0B2850ED99DFD462CD8C566F6C2E1D13AEE69642FBC1665DF99F6`。
  buildとSmokeLaunchはexit 0。PEの`FileVersion` / `ProductVersion`はともに
  `1.0.0`。PYZのtest / pytest / Matplotlib系禁止項目は0件、FFmpeg entryは
  10件だった。埋込み`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、
  `pyproject.toml`は現行repo入力とhash一致した。
- B5 ZIPは
  `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-07\zip-output\MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`、
  421906070 bytes、SHA-256
  `04590E7636980FBECB13F45E07D1778113F2C037C04953F7FBA70649C3EB3873`。
  157 filesを組立・展開し、missing 0 / extra 0 / mismatch 0、ZIP rootの
  非license禁止entry 0件だった。主要runtime packageのライセンス原文を
  `licenses/`へ追加し、対応表を`THIRD_PARTY_LICENSES.md`へ固定した。
- 配布runは同じZIPを`distribution-run/`へ展開した。PID `29452`は起動時に
  `Responding=True`、`HasExited=False`だったが、`MainWindowHandle=0`で、
  `CloseMainWindow()`は`False`だったため、通常終了ではなく当該PIDだけを
  強制終了した。起動後のdistribution treeは157 filesで展開前hashと一致し、
  追加runtime fileはなかった。GUI接続面は`cua.getState()`でapps / browsers
  とも空だった。このためM01〜M07、独立性、通常終了codeはPassへ変更しない。
- `libgomp`警告は再buildでも再現した。PyTorch
  `torch/_inductor/codecache.py`がLinux専用の
  `/usr/lib64/libgomp.so.1`を条件付きで参照し、PyInstallerのctypes解析が
  Windows上でbasename制約により無視したものだった。Windows build /
  SmokeLaunchはexit 0で、候補にLinux absolute pathのDLLを追加した事実は
  ない。これは第三者依存の既知non-fatal warningとして記録し、Torch runtime
  全体を除外する修正は行っていない。
- 以前のbuildで観測されたSymPyの`return` in `finally` SyntaxWarningは、
  test系除外後の今回の再buildログでは再現しなかった。元の警告の正確な発生元
  は独立特定できていないため、「原因修正済み」ではなく「今回未再現」と扱う。

再検証後の暫定判定:

- `B5-G-INPUT`: **Pass (static)**。候補、現行NOTICE、版数、モデル・音声の
  入力identityを固定した。ユーザー提供音声は未追跡のまま保護し、ZIPへ含めていない。
- `B5-G-DOCS`: **Pass (static)**。必須5ファイル、主要runtime license原文、
  FFmpeg原文、実凍結内容との対応表を組立・展開照合した。
- `B5-G-PATH`: **Pass (static)**。B4/B5の新規作業rootを分離し、repoの
  build / dist / runtime dataは変更していない。
- `B5-G-ENV`: **Hold**。GUI-capable接続面がなく、M01〜M07、独立性、
  通常終了codeを確認できない。
- `G-PACKAGE`: **Hold**。静的なP2 license/package混入は解消し、P3 warningの
  原因・影響も記録したが、GUI・独立性・通常終了のP2相当の必須確認が残る。

### 15.3 Computer Useによる候補#07検証と除外設定の補修

この項は§15.2の後続証拠であり、以前の「GUI接続面なし」やtest名の一括除外を
現在の結論として継承しない。HEADは`c091d56`のまま。Git変更操作は未実施。

- `computer-use`のWindows APIで対象EXEを操作。実MMDは操作していない。
  GUI素材・model・観測記録は
  `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-07\gui-verification-01\`。
  `input.wav`と`model-input/small.pt`は§15.1のsize/hashに一致する既存入力の
  隔離コピー。MP3/M4Aは同WAVからFFmpegで作成した検証素材であり、配布物ではない。
- 初回起動は音声cache directory作成に失敗し、GUIへエラー表示後に操作可能状態へ
  復帰。起動cwdは独立取得できておらず、具体的な失敗先は断定しない。
  CodexがAlt+F4で通常終了を実施し、`initial-process.json`ではPID 13248/11640が
  ともにexit 0。これは後述の隔離環境runの終了証拠とは分ける。
- `isolated-restart-process.json`のrunはcwdを`distribution-run`へ固定し、子環境を
  Windows-only PATH / Python環境変数なしに設定。メイン画面・icon・toolbarを観測。
  small/medium/turbo候補と、候補選択だけではactive modelが変わらないことを確認。
  Download & Verifyは実行していない。モデル未配置での解析は`model_unavailable / model_missing`
  として安全に失敗した。splashの版数表示は時間内に捕捉できていない。
- WAVとMP3をそれぞれGUIで読込み、約40.46秒の波形表示とMMD用WAV出力成功を確認。
  出力は`input_mmd.wav`、`from_mp3_mmd.wav`。M4Aは選択前にrunが終了したため未実施。
  使用されたffprobe/ffmpeg 6 processは同runの`_MEI.../FFmpeg/`下を指し、全exit 0。
- GUIの保存先選択で隔離smallを指定し「確認済み」を観測したが、音声のみ解析は
  「Whisperモデルの読み込みに失敗しました」で失敗。M06は不合格であり、上記音声
  読込・出力の成功をWhisper解析成功へ読み替えない。raw inner tracebackは未取得。
- 同runでは188 moduleを標本採取。repo / `.venv`由来のロードは見つからず、
  Python/wxはonefile展開先を指した。OS以外にはIME、Adobe/OneDrive shell extensionも
  観測されており、clean OSではない。100ms polling間の短命processは捕捉できない可能性がある。
  PID 8548/20764はexit 0、先行isolated runの25112/30216もexit 0だが、ユーザーによる
  中断・再開の間の終了操作者は未確認。CodexによるM07通常終了操作の証拠にはしない。
- 確認された補修対象: specの`numpy._pytesttester`、`jinja2.tests`、`torch.testing`、
  `torch._inductor.test_operators`、SymPy Matplotlib adapterの除外。
  fresh subprocessでspecの除外を再現する回帰テストにより、順にNumPy初期化、
  Torch autograd/checkpoint、SymPy初期化、Torch Dynamoの直接import失敗を確認した。
  `torch.testing._internal`へ除外を狭める案もcheckpointのlogging_tensor importを
  阻害したため採用しない。外部Matplotlib/PySide6本体の除外は維持する。
- 補修後command: `.\.venv\Scripts\python.exe -m pytest tests/test_ms27_runtime_exclusions.py tests/test_whisper_model_catalog.py -q`
  はexit 0、8 passed / 21 subtests passed。補修前の新規回帰テストはexit 1で失敗を検出した。
  ソース環境でのimport回帰結果であり、frozen解析合格の代替ではない。
- 候補#07は静的監査時点の履歴として保持し、現在の採用候補とはしない。
  specと埋込みTHIRD_PARTY_LICENSES変更により、候補#08でbuild/SmokeLaunch、
  PYZ/原文対応、ZIP照合、M01〜M07を再検証する。G-PACKAGEはHoldを継続する。

### 15.4 候補#08 最終検証・G-PACKAGE Pass（2026-09-16）

§15.1〜15.3は過去候補の履歴として保持する。採用対象は以下の#08だけである。
実行HEADは`c091d56`、branchは`feature/MS27-implementation`。
補修差分はspec、THIRD_PARTY_LICENSES、catalogテスト、新規runtime除外テストと本台帳。
ユーザー音声は未追跡のまま保護し、stage / commit / pushはしていない。

#### 採用identityと静的証拠

- B4 root: `C:\tmp\MMD_AutoLipTool_MS27\B4\run-20260915-final-candidate-08\`。
  `source-manifest.json`の109入力からbuild。`source\dist\MMD_AutoLipTool.exe`は
  425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`。
- B5 root: `C:\tmp\MMD_AutoLipTool_MS27\B5\run-20260915-final-package-08\`。
  `zip-output\MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`は423274681 bytes、
  SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`。
  実行EXEは同rootの`distribution-run\MMD_AutoLipTool.exe`で、上記EXEと一致。
- Windows 11 build 26200、Python 3.14.3、PyInstaller 6.19.0 / hooks 2026.3で
  `build.ps1 -PythonExe <repo>\.venv\Scripts\python.exe -SmokeLaunch`を実行しexit 0。
  build / SmokeLaunchを再実施し、§15.3の変更による旧候補失効を解消した。
- `C:\tmp\MMD_AutoLipTool_MS27\package-candidate-08.py`はexit 0。
  root必須5ファイル＋licenses、157 filesの組立・展開・実行先hash一致、
  安全かつ重複のないZIP entryとCRC、内部FFmpeg 10 entriesのrepo bytes一致を確認。
  FileVersion / ProductVersion文字列はともに`1.0.0`。
  内部LICENSE / NOTICE / THIRD_PARTY_LICENSES / pyprojectは採用入力と一致する。
- PYZは4364 modules。外部Matplotlib、PySide6、pytest / _pytestは除外を維持。
  NumPy/Jinja2/Torch/SymPyの必須runtime helperは保持した。testという名称だけでは
  開発専用と判定しない。#07比で新規top-level packageはなく、license対応表を継承可能。
  同梱文書はUTF-8で読め、NOTICEはユーザー指定の正本bytesを変更していない。
  NOTICE中のB3/B4日付付き記述は履歴であり、現行の同梱対応はTHIRD_PARTY_LICENSESと本項で判断する。
- `evidence/static-summary.json`、`package-manifest.json`、`pyz-modules.txt`、
  `archive-entries.txt`に内部構成、全相対path・size・hashを保存。
  `C:\tmp\MMD_AutoLipTool_MS27\verify-candidate-08-results.py`はexit 0で、
  `evidence/final-verification.json`に起動後の157 files・ZIP不変、入出力、process、
  文書・PYZ差分の最終照合を保存した。

#### Windows実行証拠

M01〜M07は原則CodexのComputer Useによる対象EXE操作。M01スプラッシュの
`Ver. 1.0.0`だけは2026-09-16のユーザー目視確認として受領した。
Codexは短時間のスプラッシュ画面を取得できておらず、ユーザー結果へ帰属させる。
実MMDは操作していない。

| 項目 | 実結果 |
| --- | --- |
| M01 | 同一EXEのwxメイン画面・icon・toolbarをCodex確認。スプラッシュ版数は上記ユーザー確認でPass |
| M02 | 未配置時small/medium/turbo候補を確認。medium選択だけでactive smallは変わらず、解析・downloadは開始しない。解析要求は`model_unavailable / model_missing`で安全に停止。Download & Verify未実行。GUI保存先変更で既存smallを指定後「確認済み」を確認 |
| M03 | 外側readme / LICENSE / NOTICE / THIRD_PARTY_LICENSESと原文配置を閲覧・hash照合。必須配置欠落なし |
| M04 | repo外cwd、子process PATHをWindows標準3箇所のみ、Python環境変数なしで実行。ロードmoduleにrepo / .venv由来なし。同runのonefile展開先FFmpeg/ffprobeを観測し、音声処理とWhisper解析が成立 |
| M05 | WAV / MP3 / M4A各入力でprobe、解析WAV、波形、MMD用WAV保存成功。出力形式は下表で独立確認 |
| M06 | 既存smallでvoice_only、TEXT＋音声の両方が解析完了・VMD保存成功。Preview Playでカーソル進行、Stopで復帰を観測。音声の聴取品質や実MMDでの見た目を確認した意味ではない |
| M07 | CodexがidleからAlt+F4で通常終了、同展開先を再起動。small候補・現モデル・保存先の保持を確認し、再度Alt+F4。親子ともexit 0、最終プロセス照会でapp/ffmpeg/ffprobe残留なし |

音声・small入力は§15.3の`final-package-07\gui-verification-01`下にある既存の
隔離素材を使用（旧EXEは使っていない）。WAV / smallのhashは§15.1と一致。
MP3 hashは`5474757A2A939088F3B2E72A4EE0911E572B807E55DD8E8704E470DDA7E798C4`、
M4A hashは`1252BF6CFE4B16F89726717FE0DC4675F9C0C3942048C516E0E90E3737599CD9`。
TEXTはrepo `sample/sample_input2.txt`の本文をUTF-8/LFにした#08の
`gui-verification/input_text.txt`、752 bytes、hash
`B5448374333F23DB42FDF1C7A38670FAC72E005E8F73CC1A51881BE4EAAA150A`。
素材・weights・出力はZIP外に保持。runtime設定はGUIのmanaged persistenceだけを使用した。

出力は#08の`gui-verification/`下。各WAVは2ch / 44100Hz / 16bit PCM。

| 出力 | bytes / 結果 | SHA-256 |
| --- | --- | --- |
| input_mmd.wav | 7136948 / 40.458639秒 | `3CB803D89D475087D955BE1E484AA0D0C7E95F96585284DC8A45EAC0219227D0` |
| from_mp3_verified.wav | 7136948 / 40.458639秒 | `3073483BE252D77023431E4529BFBF0C4FDD555318830E17236F4D4E6AFC3B42` |
| from_m4a_verified.wav | 7139372 / 40.472381秒 | `F32270ADB0133ECCED3B5848014F0C8ECADA8AE65D9F74C4CE545FEF01C680A7` |
| voice_only.vmd / text_audio.vmd | 各16128 / VMD 0002、698 morph frames、あいうえお、max frame 1184 | 各`F5EE4ADC66E641166299FD36ED749F8A8625C7AB132F97F28ADF3843C614EA2B` |

TEXT＋音声のGUI Infoは`whisper_words`、188 anchors、272 vowel events、
fallback 0、warningなし、save-block 0、review-warning 0。
同じ発話本文と音声を使った両ケースのVMD bytesは一致した。GUI上で両modeの解析・保存を
それぞれ観測しており、hash一致だけを両mode検証の根拠にはしない。
再開時に発見した`input_mmd_2.wav`は生成操作者未確認のため受入証拠に使わず、
MP3出力をCodexが`from_mp3_verified.wav`へ再実施した。

process証拠は同`gui-verification/`の`resume-0916-process.json`、
`resume-0916-b-process.json`、`normal-restart-0916-process.json`。
M07には後二者を使い、app親子PID 25648/9988、17544/20096が全exit 0。
resume-bで捕捉したFFmpeg/ffprobe PID 6432/27576/22916/5488も全exit 0。
両observer commandもexit 0。最終`Get-CimInstance`はsandbox内でアクセス拒否後、
許可された昇格照会でexit 0・対象process 0件を確認した。

観測限界: 100ms pollingで短命processを完全捕捉する保証はなく、一部parent/pathを
取得できなかった履歴はunknownのまま保持する。M07対象appのcodeにunknownはない。
IME、Adobe、OneDriveのshell integration DLLを含む既存Windows環境でありclean OSではない。
network全通信の監視はしていない。PATH除去だけでなく実行・ロード元・同梱FFmpegの
証拠を合わせた範囲で独立性Passとする。旧runの終了操作者不明はM07へ転用しない。

#### 受入・handoff

| AC | 判定と根拠 |
| --- | --- |
| AC01 | Pass: #08再build / SmokeLaunch / 内部監査、HEAD・差分・identityを固定 |
| AC02 | Pass: 原文・通知の157 filesとcomponent対応。B3由来provenance制限、公開時対応ソース提供は下記B6事項 |
| AC03 | Pass: 新規#08領域、旧候補保持、runtime直接編集・コピーなし、ユーザー素材非同梱 |
| AC04 | Pass: 固定名、root、許可一覧、安全entry、除外照合 |
| AC05 | Pass: 全file/EXE/ZIP hash、PE両文字列1.0.0 |
| AC06 | Pass: 文書可読、原文対応、埋込み・外側bytes一致 |
| AC07 | Pass: M04とprocess/module証拠。clean OS等の観測限界は保持 |
| AC08 | Pass: M01〜M06。スプラッシュのみユーザー確認と区別 |
| AC09 | Pass: M07、親子exit 0、残留なし |
| AC10 | Pass: 起動後も157 files / ZIP不変。追加INIと解析cache 3件は実行先だけに存在 |
| AC11 | Pass: 本項のAC・実行者・履歴失効・制限・B6引継ぎ対応 |

**B5-G-INPUT / DOCS / PATH / ENVおよびG-PACKAGE: Pass。B5実装・検証完了。**
B5受入を阻害する未解消P1/P2なし。§15.3の回帰テストはexit 0、8 passed /
21 subtests passedであり、その後production設定の追加変更はない。
libgompの既知warningは保持し、すべての警告原因を修正済みとはしない。

B6へ渡す未確認・延期事項:

- FFmpeg exact archive provenance、完全なexternal-library対応、対応ソース提供方式と
  実提供の公開前確認。B3決定の非阻害制限とB5必須配置の充足は分離する。
  現在のZIP必須原文・通知に具体的な欠落は確認されておらず、ZIP外提供先・方式の
  決定をB6 ownerへ渡す。B6で案内・同梱変更が必要と判明したら§10により再検証する。
- Python 3.11 / 3.12のsource/build互換性、clean Windowsでの追加確認は未実施。
- 2026-09-17にユーザー明示依頼により、Index / Roadmap / milestone / Version Control、
  Block Breakdown、B4計画、Release Package Manifest、THIRD_PARTY_LICENSESへB5到達状態を同期した。
  これはB6のreadiness判定ではなく、後続変更があればB6で最終再照合する。本項と同様、文書のみの追記はEXE/ZIP入力ではなく候補hashを失効させない。
- 実MMDは従来のユーザー報告を継承するだけで、B5で再操作していない。
  PMX hash未取得、B2-R05原因・影響未確定も勝手に解消しない。
- G-PACKAGE Passは法的適合性全体・公開Ready・MS27全体closeoutを意味しない。
  B6、stage、commit、push、tag、releaseには自動移行しない。

## 16. B6へのhandoffと完了条件

B5実施後、以下をB6へ渡す。

- 採用したB4 EXEとB5 ZIPの絶対path・size・SHA-256、version、HEAD / 差分・入力identity
- 原文・通知・必要対応物の全相対path / hashと実component対応、B3の採用方針と残る制限
- ZIP一覧、展開後全hash、許可・除外の照合、起動前後の配布bytes不変とruntime隔離
- Windows環境、独立性の証拠、M01〜M07の実施者・実結果・通常終了code・残留結果
- AC対応表、G-PACKAGE Pass / Hold、P1/P2/P3、未確認、失効した証拠と再検証・非失効理由
- Python互換性未確認、FFmpeg provenance / 対応物の制限、B6文書同期対象、未公開の事実

**今回の計画作成完了:** 本ファイルだけに範囲・現行根拠・入力差分・具体手順・検証・AC・未確定とhandoffを記載し、静的に内容と変更範囲を確認した時点。

**B5実装完了:** 採用候補についてAC01〜11を満たしG-PACKAGE Passとなった時点。Holdなら作業報告の完了と実装・検証の未完了を区別する。B5完了後もB6・公開・Git変更へ自動移行しない。
