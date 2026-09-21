# MS27-B3 Implementation Plan

## 1. 文書情報

- 対象: MS27-B3 依存・license・package manifest確定
- 作成日: 2026-09-13
- リポジトリ: `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity`
- 計画作成時ブランチ: `feature/MS27-implementation`
- 計画作成時HEAD: `df51948a7e973e6b37a0f1da7bbacdda7354971b`（`Implement MS27-B2 version alignment`）
- 開始時working tree: clean。現行ブランチのupstream表示なし。remoteの通信確認はしていない。
- 状態: **Implemented / B3の台帳・関連文書同期・入力identity確認を実施。ユーザー確認済み方針に基づきG-LICENSE Pass。B4固有の開始ゲートと実行権限は別途確認する。**
- 前提: MS26 CloseOut A、MS27-B1 Pass、MS27-B2実装済み・直接検証Passを継承する。正式版数は`1.0.0`で固定済み。
- 今回の実装変更対象: 本文書、`THIRD_PARTY_LICENSES.md`、`NOTICE`、`README.md`、`readme_mmdautolip.txt`、`docs/Release_Package_Manifest.md`。コード、spec、tests、依存関係、runtime JSON/INI、FFmpeg binaryは変更していない。

### 1.1 根拠の優先関係

ユーザーの確定事項、ライブのGit・ファイル、個別計画の最終証拠、現行routing、過去の計画時記録を区別する。[MS27 Block Breakdown](MS27_Block_Breakdown.md)の先頭・一覧に残るB1/B2未実施、旧版数、旧版数解決順は作成時履歴であり、現在状態へ転記しない。他文書の古い欄は今回変更しない。

B2のFileVersion / ProductVersionは**version resource入力へ設定済み**である。最終EXEに格納された値の実物確認はB4、実スプラッシュ表示とZIPの確認はB5に残る。

## 2. 背景

[Roadmap §14](../MS20_and_Beyond_Roadmap.md)は、MS26の機能受入とMS27のbuild・配布・license確認を分けている。B2では版数更新と直接検証が完了したが、第三者文書は依然として概要中心であり、実環境から同梱候補へ入る各componentの対応と、原文・通知・必要対応物は未確定である。

### 2.1 参照資料と現在の到達状態

| 根拠 | 本計画で採用する内容 |
| --- | --- |
| [MS17 Index](../MS17_and_Beyond_Index.md)、[MS20 Index](../MS20_and_Beyond_Index.md)、Roadmap §14 | MS17 Indexは履歴routing。MS26 CloseOut AとMS27配布工程の境界を継承 |
| Block Breakdown §8.2〜§8.4、MS27-B3節、§10〜§12 | G-LICENSE、G-ARTIFACT、G-PACKAGE、Block依存、証拠失効、終了コード規則 |
| [B1計画](MS27-B1_Implementation_Plan.md) §8.3〜§8.5、§15.4、§17.1 | B1 Pass。Windows 11 Pro / build 26200 / 64bit、Python 3.14.3、FFmpeg入力証拠。B4隔離cwd・PythonExe絶対path契約 |
| [B2計画](MS27-B2_Implementation_Plan.md) §15.4〜§17 | B2 Pass。版数解決10件、Windows resource2件の最終再試行は各exit code 0。初回resource test失敗の履歴は保持。今回は再実行していない |
| `pyproject.toml`、`src/app_version.py`、`MMD_AutoLipTool.version.txt`、spec | project `1.0.0`、自アプリresourceのTOML優先、FileVersion / ProductVersion文字列`1.0.0`、固定数値`(1, 0, 0, 0)`、`EXE(version=...)`接続をライブのファイルで確認 |
| `README.md`、`readme_mmdautolip.txt`、[Release Package Manifest](../Release_Package_Manifest.md) | 表示・対象版数`1.0.0`、固定EXE名、ZIP名`MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`。version resourceはbuild-only |
| `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` | 本体MIT本文あり。第三者概要、FFmpegのGPL / version3確認事項、公式Download / legal参照、取得経路方針を記録。最終frozen/ZIP配置は後続確認 |
| `requirements.txt`、`.venv/Lib/site-packages`のMETADATA | 宣言値と実環境の差分を確認。ディレクトリ名だけでなくName / Versionを読み取り、runtimeでのimport成功や最終同梱とは区別 |
| `build.ps1`、spec、`src/resource_utils.py`、`src/core/ffmpeg_locator.py` | onefileの収集・resource解決・FFmpeg配置・相対cwd依存を静的確認。buildやアプリは起動していない |

### 2.2 宣言値・実環境の初期対応

次表は計画作成時の静的観測であり、完全な依存台帳や候補採用判定ではない。宣言欄は`==`の値を記す。実環境値は同日のトップレベルdist-info METADATAで確認した。

| component | pyprojectの宣言 | requirements.txt | 実環境METADATA | B3での扱い |
| --- | --- | --- | --- | --- |
| wxPython | 4.2.5 | 4.2.5 | 4.2.5 | 直接依存、GUI / nativeも調査 |
| matplotlib | 3.10.8 | 3.10.8 | 3.10.8 | 直接依存、backends / fonts / nativeも調査 |
| numpy | 2.4.3 | 2.4.3 | 2.4.3 | 直接依存、同梱nativeの原文も調査 |
| openai-whisper | 20250625 | 20250625 | 20250625 | 直接依存。推移依存、assets、weightsを分離 |
| pyopenjtalk | 0.4.1 | 0.4.1 | 0.4.1 | 直接依存。native / 辞書 / upstreamを分離 |
| PyInstaller | なし | 6.19.0 | 6.19.0 | build toolと配布bootloaderを分ける |
| pyinstaller-hooks-contrib | なし | 2026.3 | 2026.3 | build入力。hookが収集するcomponentは別行 |
| setuptools | build-systemで`>=82.0.0` | 82.0.1 | 84.0.0 | requirementsのpinとは不一致。build-system下限を満たすことだけで差分解消にしない |
| fonttools | なし | 4.62.1 | 4.64.0 | 宣言・実環境差分 |
| kiwisolver | なし | 1.5.0 | 1.5.1 | 宣言・実環境差分 |
| packaging | なし | 26.0 | 26.3 | 宣言・実環境差分。vendored別実体と混ぜない |
| pillow | なし | 12.1.1 | 12.3.0 | 宣言・実環境差分 |
| tiktoken | なし | なし | 0.14.0 | WhisperのRequires-Distあり。直接宣言欠落と即断しない |
| mmd-autolip-tool | project `1.0.0` | なし | 0.4.0.0 | B2で既知の古い自アプリmetadata。第三者依存差分とは別。実表示経路はB2で検証済み |

同じ読み取りで`torch 2.14.0`、`numba 0.67.0`、`llvmlite 0.49.0`等のMETADATAを確認した。WhisperのRequires-Distにはmore-itertools、numba、numpy、tiktoken、torch、tqdmがあり、tritonにはLinux条件がある。extrasやenvironment markerを無視して全項目をWindows必須へ格上げしない。

`PySide6`、`PySide6_Addons`、`PySide6_Essentials`、`shiboken6`のMETADATAは各`6.10.2`で存在する。これは実環境への存在の証拠であり、必要性や最終EXE同梱の証拠ではない。旧xref記録とも別欄で扱う。

`setuptools/_vendor/packaging`のMETADATAは`26.0`であり、トップレベル`packaging 26.3`と同名別実体である。component identityには親・実pathを含め、名前だけの重複排除をしない。`tiktoken_ext`は引継ぎのmodule spec probeでnamespaceとして確認されている。独立distributionや独立versionがあると仮定せず、実施時にRECORD等から所有distributionへ対応付ける。

### 2.3 FFmpegの入力と不足証拠

- `FFmpeg/bin/`には`ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe`、`avcodec-62.dll`、`avdevice-62.dll`、`avfilter-11.dll`、`avformat-62.dll`、`avutil-60.dll`、`swresample-6.dll`、`swscale-9.dll`の10実体と`.gitkeep`がある。今回の列挙と`git ls-files FFmpeg/bin`で確認した。
- B1のC09 / C10とユーザーからの直前引継ぎは、FFmpeg / ffprobe `N-123549-g70537ec8e6-20260318`、configurationに`--enable-gpl --enable-version3`を記録している。B1 §8.3には10実体のSHA-256がある。B3実施で同じ版数・configurationを再確認し、10実体のサイズ・SHA-256を再取得した（§15.4）。
- 現行specは`FFmpeg/bin`直下の`.gitkeep`以外の通常ファイルをすべて内部`FFmpeg`へ収集する。ffplayと7 DLLも収集予定であり、最終内部の内容は未確認である。
- 今回の`FFmpeg/`再帰列挙にはlicense / COPYING / source archiveはなかった。通常のrepoファイル検索では`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`のみが該当した。ignore対象、外部保存先、元の配布archive全体の不存在を証明したわけではない。
- 正確なWindows配布archive identity、archive hash、外部componentの完全なbinary対応、対応source archiveの実体はローカル照合だけでは未確定である。ユーザー確認済み方針により、これらはG-LICENSEの阻害条件ではなくprovenance limitationとして保持する。ネット照合による追加結果は次項に記録する。

### 2.3.1 FFmpeg network research supplement (2026-09-14)

- FFmpeg FATEの公開履歴は、`N-123549-g70537ec8e6`を2026-03-18のupstream revisionとして記録している。これはローカルの`ffmpeg -version` / `ffprobe -version`出力とrevision部分が一致するが、Windows配布元を証明する記録ではない。
  - <https://fatebeta.ffmpeg.org/history/x86_64-archlinux-gcc-threads-misc?begin=350>
- upstream source treeはrevision `70537ec8e6`で参照でき、revision固定のlicense entry pointは次のとおりである。
  - source tree: <https://github.com/FFmpeg/FFmpeg/tree/70537ec8e6>
  - `LICENSE.md`: <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/LICENSE.md>
  - `COPYING.LGPLv2.1`: <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.LGPLv2.1>
  - `COPYING.LGPLv3`: <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.LGPLv3>
  - `COPYING.GPLv2`: <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.GPLv2>
  - `COPYING.GPLv3`: <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.GPLv3>
- upstream `LICENSE.md` / legal guidanceに照らすと、`--enable-gpl`はGPL対象部分を有効化し、`--enable-version3`はv3ライセンス選択肢を有効化する。したがって本入力は**GPL-enabled / version3-enabled**として記録する。単純な`GPLv3`の一語へ短縮せず、外部ライブラリの個別条件も別途対応付ける。
  - <https://ffmpeg.org/legal.html>
- ローカルの`x86_64-w64-mingw32`、`--enable-gpl`、`--enable-shared`、DLL構成はBtbNの`win64` / `gpl-shared` build familyと強く整合する。BtbNのREADME / build scriptは、variantの意味、FFmpeg source clone、日付ベースの`--extra-version`を公開している。
  - <https://github.com/BtbN/FFmpeg-Builds/blob/master/README.md>
  - <https://github.com/BtbN/FFmpeg-Builds/blob/master/build.sh>
- ただし、これはbuild signatureからの推論であり、正確なBtbN release tag / assetとローカル10実体のhash対応は確認できていない。現行releaseの保持規則上、同日のdaily assetが現行一覧にないことは、過去に存在しなかったことの証明ではない。
  - <https://github.com/BtbN/FFmpeg-Builds/releases>
- FFmpeg公式のlegal guidanceは、配布時のsource、build configuration、license text、外部libraryの確認事項を示している。本リポジトリでは、ユーザー確認済み方針に基づき、現行公式license / legal情報と公式Downloadページを起点とした取得経路を採用し、license revisionとbinary revisionの厳密一致を要求しない。exact provider archive、archive hash、complete corresponding source packageは未確認のprovenance limitationとして残す。

### 2.4 B3実施結果のスナップショット

- 実施日2026-09-14、HEADは`df51948a7e973e6b37a0f1da7bbacdda7354971b`。`.venv`のMETADATAで主要直接・推移・build候補を照合し、`pip check`はexit code 0（`No broken requirements found.`）だった。
- `requirements.txt`との差分は、`setuptools` 82.0.1 / 84.0.0、`fonttools` 4.62.1 / 4.64.0、`kiwisolver` 1.5.0 / 1.5.1、`packaging` 26.0 / 26.3、`pillow` 12.1.1 / 12.3.0である。更新・再インストールは行わず、候補差分として台帳に保持した。
- `openai-whisper`、`pyopenjtalk`、`tiktoken`、PyInstallerおよびmatplotlib等のRequires-Distを読み取り、marker・extras・vendorをruntime必須へ無条件に格上げしない分類を採用した。`tiktoken_ext`はnamespaceのため独立distributionとは扱っていない。
- 実環境には主要Python packageのlicense原文候補があるが、最終frozen fileとの対応とZIP配置は未確定である。FFmpegはrevision固定のupstream `LICENSE.md`参照、公式Downloadページ、取得経路、現行legal方針を記録した。全`COPYING`本文の最終配置、元archive identity、外部component対応、対応source archiveの実体は未確認のprovenance limitationとして保持するが、ユーザー確認済み方針によりG-LICENSEはPassとする。

## 3. 目的

1. 宣言・実環境・収集予定・原文・配布先を結ぶ台帳を作り、B4が同じ入力を扱える状態にする。
2. FFmpegを含む第三者の本文、copyright、NOTICE、必要対応物を選択実体に対応付け、G-LICENSEを根拠付きで判定する。
3. 実行用ZIPの必須5ファイルに、必要な第三者文書・対応物の具体的な許可一覧を加え、除外境界を固定する。
4. README等をB3で確認できた事実へ同期し、最終artifact・配布動作・readinessの未確認をB4〜B6へ引き継ぐ。

## 4. In Scope

以下はB3実施時の範囲である。

- 既存環境を変更しない宣言値・metadata・Requires-Dist / marker・module所有者・native / dataの棚卸し
- 直接・推移・build-only・vendored・optional・native・dataの分類と、候補に採用する入力identityの固定
- FFmpeg / ffprobeのversion・全configuration、10実体と必要な外部componentの由来・hash・原文・通知・必要対応物の確認
- 現行license原本の確認・保存先決定と、取得元が確定した正確な第三者文書の整備
- 本文書内の依存・ファイル・証拠・finding台帳の実施結果追記
- `README.md`、`readme_mmdautolip.txt`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md`の必要最小限の事実同期
- 収集対象の欠落・意図しない混入が根拠付きで確認された場合の限定spec変更案と、その変更に必要な静的・直接検証
- G-LICENSE判定、B4 build入力一覧、B5 ZIP許可一覧、B6未確認事項の固定

## 5. Out of Scope

- 今回の計画作成からの実装・検証移行、本文書以外の作成・編集
- B3を理由とする新規依存、依存のupdate / downgrade / reinstall、lock生成、FFmpeg取得・差替え、DLLの独断削除
- onefile build、SmokeLaunch、EXE / ZIP生成・展開、GUI起動・操作、実MMD確認。これらのB4/B5作業をB3へ取り込まない
- VMD / WAV、GUI状態、Whisper identity / download、モデル管理、installed namespace全体の改修
- runtime JSON / INIの直接編集・コピー・削除・fixture化・stage、weights / sample / ユーザー素材の同梱
- ソースコードや依存のライセンス変更、概要文や自作翻訳を原文とみなすこと
- Source code archiveの実生成・公開、installer、wheel / sdist、新しい配布方式の追加
- stage、commit、push、merge、tag、release、ブランチ変更、外部書き込み、追加サブエージェント

必要な原文・対応物の配置はB3の予定成果物である。一方、原本を確定できずbinary変更や別の配布方式が必要になる場合は、具体的な変更を別途判断する。通常の開発source除外を、確認されたライセンス上の必要対応ソースまで禁止する規則に拡張しない。

## 6. 前提条件

- B1 / B2の最終証拠と今回のライブHEADを基準にする。実施時にbranch・HEAD・tree・関連入力が変化していれば、内容と影響を照合する。既存の無関係な変更は保護する。
- B3はG-LICENSE未充足でも調査・台帳・不足記録を進められる。Passが必要なのはB3完了と依存するB4開始であり、原文不足だけで計画作成を停止しない。
- Python 3.14.3等のOS / toolchainはB1の実施記録である。実施時に実path・version・architectureを記録し直す。Python 3.11 / 3.12互換性は未検証のまま保持する。
- `requirements.txt`を現在環境の完全なlockと扱わない。差分の来歴を推測せず、候補の実入力と再現上の制限を記録する。既存値を書き換えて一致を作らない。
- B4の隔離source / logs / ZIP領域はB1の契約を継承する。`C:\tmp\MMD_AutoLipTool_MS27\B4\<run-id>\`は候補であり、実runの絶対pathはB4開始時に固定する。B3ではcopy・build領域を作らない。
- MS26の実MMD結果はユーザー報告、生成artifact確認はCodexのread-only結果である。B2-R05は原因・影響未確定、PMX hashは独立取得不可の制限を保持し、B3の新たな受入条件にしない。

## 7. 対象ファイル

| 区分 | 対象 | B3実施時の変更・確認責務 |
| --- | --- | --- |
| 主記録 | 本文書 | 依存・入力file・license対応・証拠・Hold・handoffを追記。別の独立台帳文書を必須にしない |
| 文書 | `THIRD_PARTY_LICENSES.md`、`NOTICE` | 概要と実候補を区別し、実version・由来・適用原文・通知・配置を対応付ける。独自MIT本文・copyrightを維持 |
| 文書 | `docs/Release_Package_Manifest.md` | 外側5ファイルと確定license一式、内部必要物、build-only、除外対象を具体化 |
| 文書 | `README.md`、`readme_mmdautolip.txt` | `1.0.0`、onefile、license閲覧先、初回モデル・依存条件を事実同期。旧版履歴を保持 |
| 正確な第三者文書の追加先候補 | `licenses/<component>/<version-or-build>/<original-relative-path>` | 現時点では未作成。実施時に確認した原本名を維持して具体pathを台帳へ固定。全文・複数copyright・例外条項を省略しない |
| 条件付き変更 | `MMD_AutoLipTool.spec` | §8.4の限定条件を満たす変更だけ。B2版数接続と既存resource配置を維持 |
| 関連確認 | `build.ps1` | cwd、build入力、隔離契約を確認。現状からwrapper変更の必要性は確認できておらず、通常のB3変更対象にはしない |
| 読み取り | `LICENSE`、`pyproject.toml`、`requirements.txt`、`MMD_AutoLipTool.version.txt` | 本体MIT、依存・版数・build入力を確認。B3でversion・依存値は変更しない |
| 読み取り | `.venv`のMETADATA / RECORD / WHEEL / 原文、`FFmpeg/bin/` | 宣言・実体・由来・配置の対応。環境更新、binary削除・置換はしない |
| 読み取り | `src/resource_utils.py`、`src/app_version.py`、`src/core/ffmpeg_locator.py`、`src/core/whisper_models.json`、`assets/` | resource / version / FFmpegの実行時配置を維持し、必要dataをweightsと誤分類しない |
| 既存検証 | `tests/test_app_version.py`、`tests/test_ms27_b2_windows_version_resource.py`、`tests/test_whisper_model_catalog.py`、`tests/test_whisper_model_loader.py`、`tests/test_ms17_b3_ffmpeg_locator.py` | 実在確認済み。§11の変更別条件に合う対象だけ実施時に使用 |
| 新規検証候補 | `tests/test_ms27_b3_packaging_contract.py` | 未作成。spec変更が既存テストで保護されない実際の収集境界を作る場合だけ追加候補とする |

`licenses/`へ保存する文字資料はbuildで自動収集される`FFmpeg/bin/`に置かない。原文の追加だけで`binaries`へ紛れ込むことを防ぐ。大型の対応ソース等は取得・配布方法を確定するまで上記候補へ機械的に格納しない。

## 8. 実装方針

### 8.1 依存台帳の作り方

1. `pyproject.toml`のruntime / build-systemと`requirements.txt`を別の宣言集合として記録する。
2. 同じ実行環境のinstalled distributions、Requires-Dist、marker、extras、RECORD、module所有者を採取する。vendor配下は親componentの子行とし、トップレベルdistributionと同一視しない。
3. runtimeからの参照、specの明示収集、hookの収集候補、native import、package dataを重ねる。環境にあるだけのpackageを全同梱と判定しない。
4. 各行を`runtime-direct / runtime-transitive / build-only / native / data / vendored / optional / unrelated`で分類する。複数の役割は別欄へ残す。PyInstaller本体のbuild用途とEXEに入るbootloaderを分ける。
5. 差分ごとに、宣言値、observed値、候補使用値、理由、整合確認、未確認、ownerを記す。現在環境を使用する場合もrequirements再現済みとは書かない。候補採用理由が確定できない差分はHoldとする。
6. Python runtime、wx、NumPy、Matplotlib、Pillow、torch / numba / llvmlite、pyopenjtalk等のDLL・拡張・同梱第三者コード・辞書・fontsを調べる。名前からライセンスを推定せず、各distributionの原本とファイル対応を確認する。

棚卸しに新規のlicense scanner依存を追加しない。既存のmetadata読み取りとfile列挙を基本とし、packageをimportしてdownloadや辞書初期化を誘発しない。network関連libraryの存在とアプリによる通信の実行も別の事実として扱う。

### 8.2 FFmpegとライセンス原本

1. 選択中の10実体にpath・size・SHA-256を付け、FFmpeg / ffprobeのversion・全configurationを別コマンドで取得する。B1のhashとの一致・相違を記録する。ffplayは収集予定の独立行を作り、そのversionの由来を明示する。起動しなくても特定できる原archive証拠があれば使う。
2. 元の配布archive、配布元・該当buildの公開資料、source revision、build recipe等を対応付ける。version suffixから配布元URLやsource archiveの名前を推測しない。
3. GPL / version3を含む構成を前提に、FFmpeg本体、組込み外部component、7 DLLとその依存について適用本文、例外、copyright、NOTICE、必要対応物を確認する。DLL import一覧だけでは静的に取り込まれたcomponentを網羅できないため、configuration / build資料とも照合する。
4. 原文の所在・取得日・対象version / hash、通知・対応ソース等の該当性、充足方法、実際に用意できた資料を記す。一般的なGPL URLやlicense名だけを充足証拠にしない。原文を翻訳・要約して差し替えない。
5. 資料不足時は§13のHoldへ進む。ユーザーが保持する元archive等の提供、特定の取得先利用、配布方法変更等が必要になった時点で、既存の許可で解決できるか確認する。binary差替えを先行して実施しない。

適用範囲や配布条件は選択実体の一次資料に基づき確認する。本計画の作成時点で、GPLの波及範囲や配布適法性を独自に確定していない。第三者ソースの提供が必要と判明した場合は、対象・提供方式・必要な配置を具体化し、その履行方法が確定するまでPassにしない。

### 8.3 packageの三つの一覧

| 層 | 許可・必須内容 | B3で固定すること |
| --- | --- | --- |
| B4 build入力 | source / spec / build.ps1 / assets / pyproject、`MMD_AutoLipTool.version.txt`、3 license文書、選択FFmpeg、実環境 | 絶対originと相対配置、hash、収集理由。isolated sourceにversion resourceを含める |
| onefile内部予定 | Python実行modules / native、FFmpeg群、必要data、icon / toolbar / splash、`src/core/whisper_models.json`、`pyproject.toml`、`LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` | specからのsource→destination、原文との対応。実同梱はB4で判定 |
| ZIP外側 | `MMD_AutoLipTool.exe`、`readme_mmdautolip.txt`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、確定した第三者原文・通知・必要対応物 | ZIP root相対の全file一覧、origin、hash、owner。固定名`MMD_AutoLipTool_v1.0.0_Windows_onefile.zip` |

現行のFFmpeg内部配置は`FFmpeg/<filename>`であり、repoの`FFmpeg/bin/<filename>`とは異なる。locatorはrepo / app側`FFmpeg/bin`、`_MEIPASS/FFmpeg`、PATHの順で探索する。この配置と探索契約を変えない。

第三者原文の外側配置は`licenses/<component>/<version-or-build>/<original-relative-path>`を基本候補とし、実施時に実在する全fileへ展開してManifestへ記す。必須5ファイルは最小集合であり、5件だけでlicense一式を省略しない。空の予定path、リンクだけ、exe内の概要のみで「原文あり」と判定しない。

除外はZIP外側と該当する内部dataの双方へ適用する。

- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`およびbackup・一時コピー・利用者pathを含む状態データ
- runtime `models/`、Whisper weights / checkpoint / `.part`、sample、検証用音声・TEXT・PMX / PMD・MMD本体・生成VMD / WAV / report
- 生の開発`src/`、`tests/`、`docs/`、`.git/`、`.venv/`、`.agent/`、`.agents/`、`.codex/`、`AGENTS.md`、build残骸、cache / temp、logs、台帳
- 外側ZIPの`MMD_AutoLipTool.version.txt`、spec / build設定、生の`*.pyc`等

onefileの実行用module archive、manifest、辞書、tokenizer assetsは生の開発sourceとは区別する。拡張子`.bin`だけで除外しない。ライセンス上必要と確認された第三者対応ソースは、開発source除外の例外として明示的なManifest行を作る。sampleは今回の確定方針で除外し、出典判明を理由に追加しない。

### 8.4 spec変更の条件とPySide6

現状は`collect_submodules("matplotlib.backends")`、Whisper / tiktoken_ext収集、`excludes=[]`である。過去xrefと現在METADATAの存在だけでQt全除外を追加しない。

変更候補は、根拠付きで必要と判明した収集先訂正、必要原文の明示data追加、意図しないcomponentの限定除外に絞る。各変更の前にfindingへ「現在の収集経路、対象file / component、必要性、変更理由、変更前後の配置、失う機能、直接検証、B4/B5再検証」を記録する。ffplay / DLLについても未使用らしいという理由だけで除外しない。

新規テストが必要ならspecを無制限に実行せず、静的解析または収集helperを制御したテストで既存入力保持・選択対象・欠落時の挙動を確認する。文字列の存在確認だけを最終非混入の証明にしない。実際の内部module / DLL、wx / matplotlib起動、resource利用はB4/B5へ引き継ぐ。

B4でPySide6 / Qt / shiboken実体を検出した場合は、そのcandidate hashと収集経路をB3へ戻す。必要性・通知が未確定ならHold。必要性と配布条件を根拠付きで確定できた場合だけ台帳・Manifestへ反映し、不要なら限定除外と再build・内部確認へつなぐ。旧GUI復活やnamespace改修へ広げない。

## 9. 詳細ステップ

| 順序 | 作業 | 完了証拠・停止条件 |
| --- | --- | --- |
| B3-01 | B1/B2最終証拠、live Git、入力差分、今回の権限と実環境を固定 | baselineと入力一覧。無関係な変更は保護、未評価の候補入力変更は該当gate Hold |
| B3-02 | 宣言2系統、installed / vendored metadata、Requires-Dist、marker / extras、module所有者を列挙 | §10.1の依存行と§2.2差分の分類。環境を更新しない |
| B3-03 | specとhookから予定収集を対応付け、native / data / binaryごとのoriginとhashを記録 | B4入力一覧と予定内部一覧。静的取り込みや辞書等が未特定なら該当行Hold |
| B3-04 | FFmpeg 10実体と版数・config・出所・原archive・必要資料を照合 | B1との差分、原文・copyright / notice・対応物の一覧。資料不足はFxx / Uxxへ |
| B3-05 | Python / 直接・推移・native / data / bootloader等の原文を実fileへ対応付け、確定資料を配置 | componentごとの充足証拠。出所不明・必要本文不足はHold。原文を捏造しない |
| B3-06 | build / 内部 / ZIPの一覧を固定し、README等5文書を事実同期。必要なspec変更だけ§8.4で限定 | exact file配置、履歴保持、版数・dependency非更新、関連文書の一致 |
| B3-07 | §11の変更に近い確認を実施し、件数・終了コード・差分・入力hashを記録 | 失敗と再試行を別IDで保存。必要検証失敗はHold、対象外を自動修正しない |
| B3-08 | §12を照合し、G-LICENSE / B3 PassまたはHoldを記録してB4〜B6へhandoff | Passなら具体的なbuild入力が揃う。Holdなら不足・owner・解除条件を特定。後続を自動開始しない |

原文不足でB3-04がHoldになっても、依存しないB3-02 / 03や資料確認は進められる。欠けた原文を前提にManifestを確定扱いせず、未確定行を保持する。

## 10. 状態遷移 / データ契約

### 10.1 依存台帳schema

本書の実施記録内に次の列を持つ行を作る。componentが多い場合は表を分割し、安定したcomponent IDで結合する。JSONや新しいruntime schemaを追加しない。

| 列 | 記録内容 |
| --- | --- |
| component ID / parent / role | 親子、direct / transitive / native / data / build / vendored、使用目的 |
| declared | 宣言file・項目・pin / constraint、Requires-Distの親・marker / extras |
| observed / selected | 実version、metadata path、採用予定値、差分分類と採用理由。未決定はunknown |
| provenance | 配布元、versioned原本、取得元・確認日時、archive / source revision / build configuration。未取得を明記 |
| collection | spec / hook / import経路、予定同梱・非同梱理由。環境存在と最終同梱は別欄 |
| binary / data identity | source path、size、SHA-256、親archive、内部destination、native / data別 |
| license | 正確な名称・version・例外、本文 / copyright / noticeのfile、hash、適用対象、確認者 |
| obligations / fulfillment | 必要対応物・提供方法の根拠、現物 / 案内の配置、充足状態、未確定事項 |
| package placement | ZIP相対path、onefile内部path、repoでの保存path、build-only区分 |
| evidence / owner / state | Cxx / Mxx / Fxx / Uxx、担当Block、not run / observed / planned / Pass / Hold / stale |
| artifact actual | B4 EXE hash・実内部file、B5 ZIP hash・外側実file。B3時点はnot run |

同名の別version / vendored別実体を一行へ潰さない。Python runtimeやnative等、独立METADATAがない対象は`N/A（理由）`と出所で特定する。`.venv`や非配布台帳の絶対pathを利用者向け文書へ転記しない。

### 10.2 状態と証拠失効

```text
B1 Pass + B2 Pass
  → B3 棚卸し / 原文照合 / package一覧
      → ユーザー確認済み方針 + 公式参照・取得経路・入力identity: G-LICENSE Pass
          → B4 最終EXE監査 → B5 ZIP / 配布確認 → B6 readiness
              不一致・新規component → B3へ戻して影響証拠を更新
```

G-LICENSE Passは**固定した予定入力に対する原文・条件充足の判定**であり、まだ存在しないB4 EXEの内部証明を前提に要求しない。一方、未確定の入力componentを「B4で確認予定」だけでPassに含めない。B4で予定にない要素が判明すれば該当行を再開し、後続Passを止める。

- `HEAD + 対象差分 + 入力file/hash + 実環境 + 公式参照・取得経路`をB3証拠単位とする。実EXE / ZIP hashは生成を担当するBlockから後で結ぶ。
- pyproject、実module / native / data、FFmpeg、spec、埋込み`LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md`が変われば、影響するB4 build・内部・smokeとB5のEXE / ZIP証拠をstaleにする。
- 外側だけのlicense / readme変更はZIP hashを失効させる。B4再利用には埋込み対象・入力bytes不変の根拠を残す。現行のNOTICE等は外側と内部の両方なので外側だけと誤分類しない。
- 本書など非配布の記録のみの変更は候補bytes不変と影響なしを確認して証拠を再利用する。commitの有無だけで有効・無効を決めない。
- 不足資料の到着後は対応するUxxを証拠ID付きで解消する。元の失敗・未確認記録やMS26受入記録を書き換えて消さない。

## 11. テスト方針

### 11.1 B3実施時の確認と拡大条件

| 変更・確認内容 | 最小の検証 | 後続・拡大条件 |
| --- | --- | --- |
| 台帳・原文・文書のみ | 宣言 / metadata / 原本 / hash / 配置の照合、参照先確認、scope / whitespace確認 | pytest / compileall / buildを一律追加しない。license充足はテスト成功で代替しない |
| specの収集を変更 | 変更前後の収集対象と配置を静的確認。必要なら制御した収集契約testを追加 | 実配置・非混入の最終判定はB4。既存version / manifest境界に触れるなら下記既存testを実施 |
| specの版数・TOML入力周辺へ影響 | `tests/test_ms27_b2_windows_version_resource.py`、`tests/test_app_version.py` | B2 resource / resolver入力不変ならB2成功記録を再利用できる理由を残す |
| Whisper manifest / data収集へ影響 | `tests/test_whisper_model_catalog.py`。loader収集にも影響すれば`tests/test_whisper_model_loader.py` | frozen assets、モデル未配置、実解析はB4/B5。モデルdownloadは行わない |
| FFmpeg収集・配置へ影響 | `tests/test_ms17_b3_ffmpeg_locator.py`と収集対象の静的照合 | 実EXEでのbundled解決・音声処理はB4/B5。locator単体だけでDLL充足を証明しない |
| Qt等のoptional除外 | 収集契約、wx / matplotlib維持の経路確認 | B4内部監査、B5 GUI / waveform / 正常終了。除外指定だけで成功にしない |

full pytestやcompileallは本計画のB3必須条件にしない。広い回帰が必要な具体的変更・失敗が現れた場合だけ対象と理由を決める。必須に選択した確認を非ゼロやskipのままPassにしない。既存testを弱めて収集不備を隠さない。

### 11.2 実施時のコマンド候補

各例は単独で実行する候補であり、**今回実行していない**。実施時に対象pathとログ所在を固定する。

- FFmpeg: `.\FFmpeg\bin\ffmpeg.exe -version`
- ffprobe: `.\FFmpeg\bin\ffprobe.exe -version`
- 必要な場合のconfiguration補足: `.\FFmpeg\bin\ffmpeg.exe -buildconf`
- 1 fileの入力identity: `Get-FileHash -LiteralPath FFmpeg\bin\ffmpeg.exe -Algorithm SHA256`。他の9実体や原本もfileごとに記録
- 環境整合照会: `.\.venv\Scripts\python.exe -B -m pip check`。インストールを伴わず、metadata整合だけを確認。license / 最終artifactの証明ではない
- 条件付き直接test例: `.\.venv\Scripts\python.exe -m pytest tests/test_ms27_b2_windows_version_resource.py`
- tracked文書のwhitespace: `git diff --check`
- 未追跡の本書: `git diff --no-index --check -- NUL docs/Implementation_Plan/MS27-B3_Implementation_Plan.md`

metadata列挙はstdlib `importlib.metadata`等の読み取りを使う場合も、アプリや依存の実moduleをimportしない。Pythonを使うならbytecode抑止を設定する。必要な原本・構成の照会失敗は出力と実終了値を記録し、自動更新で解消しない。

### 11.3 終了コード

runnerが返した最終process exit codeを記録する。手動の原文照合・判断は`N/A（文書照合）`、未実行は`not run`、終了未取得は`unknown`とする。cmdletの成功を直前のnative `$LASTEXITCODE`で代用しない。passed表示でも非ゼロなら両方を残して該当検証はHoldにする。

`rg`の該当なしや`git diff --no-index --check`の終了値は診断と併記する。後者の`1`は、新規差分由来でwhitespace診断がない場合に限り正常な検査結果と扱う。再試行は新しいCxxを割り当て、元IDとの対応を残す。

## 12. 受け入れ条件

| ID | B3実施の必須条件 | 主証拠 |
| --- | --- | --- |
| MS27-B3-AC01 | live基準、B1/B2 Pass、`1.0.0`、最終EXE未確認の境界を保持 | baseline、B1/B2最終証拠 |
| MS27-B3-AC02 | 直接・推移・build・vendored・native・dataを分類し、宣言 / observed / selected / collectionを対応付けている | 依存台帳。§2.2を含む差分の理由・影響・採用値 |
| MS27-B3-AC03 | FFmpeg 10実体のidentity、version / config、公式Downloadページを起点とした取得経路、upstream source / legal参照が特定されている。exact archive/hash対応はユーザー確認済み方針により非阻害 | hash / config / 公式参照 / 取得経路 / ユーザー方針 |
| MS27-B3-AC04 | 採用予定componentのlicense参照、copyright / notice案内、必要な対応物の方針が確認され、G-LICENSEがPass | 公式legal参照、NOTICE、関連文書、適用判断、確認者 |
| MS27-B3-AC05 | build入力、内部予定、ZIP外側のexact一覧があり、必須5ファイル＋必要一式と除外境界が固定されている | Manifestとfile台帳。version resourceはbuild-only |
| MS27-B3-AC06 | README等5文書が事実と一致し、旧履歴・MS26ユーザー報告とMS27未検証を保持 | 文書照合。概要だけのlicense完了宣言なし |
| MS27-B3-AC07 | spec変更の有無・理由・影響・必要直接検証が記録され、必要検証が成功している | diff、Cxx / Mxx。未変更ならN/Aの理由 |
| MS27-B3-AC08 | PySide6過去xref、環境存在、予定収集、実同梱未確認を区別し、B4へ具体的監査を渡す | 依存行、B4照合対象と戻し条件 |
| MS27-B3-AC09 | Git追跡FFmpegが将来のSource code archiveへ入る前提で、公式参照、必要文書、対応物の保存と案内に欠落がない | 追跡確認、repo保存path・配布対応の照合。実archive生成は不要 |
| MS27-B3-AC10 | 証拠・入力hash・終了コード・失効条件・ownerが揃い、B3範囲の未解消P1/P2がない | §15〜§16、finding判定 |

**Pass:** AC01〜AC10を満たし、固定入力に対するG-LICENSEがPass、B4へ渡す具体的な入力file一覧がある。B4/B5未実施そのものはB3の失敗にしない。

**Hold:** 現行binaryのidentity、公式source / legal参照、取得経路、NOTICE案内、入力componentや差分の採否、必要直接検証等が未充足、または一次資料がユーザー確認済み方針と矛盾する場合。exact archive/hash対応とlicense revision / binary revisionの厳密一致は、同方針ではG-LICENSEの必須条件としない。B4/B5の候補build・最終artifact・実配置未確認は、各Blockの判定へ残す。

## 13. リスク・例外・Hold解除条件

| 未確認ID | 問題・影響 | 解除に必要な証拠 / owner |
| --- | --- | --- |
| MS27-B3-U01 | FFmpeg exact archive、archive hash、binaryとsourceの暗号学的対応は未確認 | ユーザー確認済みM08によりG-LICENSEの非阻害provenance limitationとして受容。現行identity、公式Download/legal参照、取得経路、NOTICE案内は記録済み |
| MS27-B3-U02 | requirementsとsetuptools / fonttools / kiwisolver / packaging / pillowが不一致 | declared / observed / selectedと差分の扱い、候補環境の整合、再現制限を記録。環境更新が必要なら理由・対象・影響を示す。B3 |
| MS27-B3-U03 | 推移・vendor・Python runtime・native / 辞書 / fonts等の原文とfile対応が未完了 | 予定同梱の親子関係・全file・原文・充足方法の台帳。B3 |
| MS27-B3-U04 | ffplay / DLLの同梱必要性、外部componentの静的組込み範囲が未確定 | build資料・役割・収集理由・原文対応。不要と判定するなら限定変更と回帰。B3、実内部照合B4 |
| MS27-B3-U05 | Qt / PySide6 / shibokenの最終同梱が不明 | 新しいwarn / xref / Analysis TOCと再帰内部archive、必要性・license・非混入証拠。B4→B3 |
| MS27-B3-U06 | 最終frozen resource、版数、EXE / ZIP、通常起動・終了、配布独立性が未確認 | B4/B5の同一candidate hashに結び付いた実物・process・手動証拠。B3ではPassにしない |
| MS27-B3-U07 | Git追跡FFmpegを含む将来Source code archiveの実生成・内容は未確認 | 追跡対象配置と対応案内はB3文書へ記録済み。archive生成・公開・最終内容はB6または公開工程の別範囲 |
| MS27-B3-U08 | B4時点の絶対cwd / PythonExe / source許可一覧がまだ実体化していない | B1契約にB2 version resource・B3入力を加えた具体path、root非接触確認。B4 |

各Uxxは現時点で未確認の追跡項目であり、全件を実行失敗として扱わない。実施中に不一致や違反を確認した場合はFxxへP1 / P2 / P3、影響、対処、根拠、ownerを記録する。

資料が読めない、原文のversionが異なる、hashが変化した、metadata所有者が解決できない場合は、その行をHoldにする。一般名称や近いversionの原文で穴埋めしない。今回のM08方針で非阻害としたexact archive対応は除き、必要資料の不足、spec限定修正、環境更新、binary変更を別の対処として記録する。

古いP2クリア判断を今回candidateのlicense充足に転用しない。逆に、未実施のB4内部検証をB3の原文収集の前提にして循環待ちにもならないよう、予定入力の確定と最終実物との差分戻しを分ける。

## 14. Codex実装時の注意

- commandは1つずつ実行して終了を確認する。shell連結・pipeline・並列実行をしない。
- 今回の計画担当は本文書だけを保存し、追加サブエージェントを起動しない。メインが成果物の採否・統合を判断する。
- 実施時も、資料読み取りや許可範囲の文書整備に一律の再承認工程を設けない。結果を変える未解決の選択だけを具体化する。
- 新規依存・binary差替え・配布方式変更の自動採用をしない。既存runtimeや利用者素材をlicense確認の入力へ流用しない。
- `.venv`・repoの丸ごとcopyや`dist`全体のZIP化を手順に含めない。必要原文やdataは許可一覧から選ぶ。
- 版数は既決の`1.0.0`を維持。第三者version、schema、fingerprint、既存fixture値、過去履歴へ版数置換を波及させない。
- 出力の成功表示、静的spec確認、原文概要をそれぞれprocess成功、最終artifact確認、条件充足へ格上げしない。
- B4/B5で実行する検証は各Blockの責務として残し、B3完了をMS27 readinessや公開実績と書かない。

## 15. Evidence ledger / 実施記録

### 15.1 IDと記録欄

- `MS27-B3-Cxx`: 実行コマンド。計画時のread-onlyにもphaseを付け、B3実装の証拠と混ぜない。
- `MS27-B3-Mxx`: 原文・file・文書の手動照合、採否判断。processがなければN/A。
- `MS27-B3-Fxx`: 確認されたfinding。P1/P2/P3、影響するAC、対処、owner、解消証拠を持つ。
- `MS27-B3-Uxx`: 未確認・不足入力。§13を初期台帳とし、解消証拠を追記する。

各記録には次を残す。

```text
ID / phase（planning・implementation・revalidation）/ owner / gate・AC:
日時・実施者 / branch・HEAD / working tree差分:
cwd / 単独commandまたは照合対象 / OS・Python path・version・architecture / tool versions:
入力origin・相対配置・size・SHA-256 / 原本version・取得元・確認日時:
期待結果 / 実結果 / 件数・skip理由 / process exit codeまたはN/A理由:
ログ・原本・台帳行の所在 / 判定・不足証拠 / Fxx・Uxx:
再試行元ID / 失効対象 / 非失効理由 / B4 EXE・B5 ZIP対応（未生成はnot run）:
```

### 15.2 計画作成時のread-only証拠

実施日2026-09-13、cwdは§1のrepository、HEADは`df51948a7e973e6b37a0f1da7bbacdda7354971b`。以下は本計画策定の観測であり、B3原文整備・実行検証の合格実績ではない。

| ID | command / 照合 | 結果 | 終了コード |
| --- | --- | --- | --- |
| MS27-B3-C01 | `git status --short --branch` | 開始時clean、MS27 branch | 0 |
| MS27-B3-C02 | `git branch -vv` | HEAD短縮`df51948`、current upstream表示なし | 0 |
| MS27-B3-C03 | `git log --oneline -n 10` | B2実装、B2計画、B1記録の履歴を確認 | 0 |
| MS27-B3-C04 | `git rev-parse HEAD` | §1の完全HEAD | 0 |
| MS27-B3-C05 | `Get-ChildItem -LiteralPath .venv\Lib\site-packages -Directory -Filter '*dist-info' -Name` | metadata directory存在。§2.2の入口 | 0 |
| MS27-B3-C06 | `rg -n "^(Name|Version):" .venv\Lib\site-packages -g METADATA --no-ignore` | §2.2の値、vendor別実体、PySide6系を静的確認 | 0 |
| MS27-B3-C07 | `Get-ChildItem -LiteralPath FFmpeg -Recurse -File -Name` | 10実体と`.gitkeep`、当該配下に原文・archiveなし | 0 |
| MS27-B3-C08 | `git ls-files FFmpeg/bin` | 11 entriesが追跡対象 | 0 |
| MS27-B3-M01 | §2 / §7の資料・コード・testsの限定読み取りと照合 | B2最終証拠を現在状態として採用、依存差分と原文不足を計画へ反映 | N/A（静的照合） |

上記以外に、指針・索引・個別計画・設定・文書・対象tests・metadataの`Get-Content` / `rg`読み取りを行った。これは計画作成時の記録であり、B3実施時のversion・hash・Python probe・pip checkは§15.4へ別IDで記録する。テスト、compileall、build、GUI、原文取得はB3実施でも行っていない。B1/B2からの実行結果は元ID・元HEADの証拠を参照する。

### 15.3 B3実施台帳の構成

次の各表を§10.1のschemaで具体化した。最終EXE/ZIPに依存する行はB4/B5未実施として残す。

| 記録群 | 初期状態 | B3で必要な内容 |
| --- | --- | --- |
| dependency ledger | §2.2、§2.4、`THIRD_PARTY_LICENSES.md`へ反映 | 全予定component、親子・役割・宣言 / observed / selected・原文・差分採否。最終frozen setはB4 |
| build / internal / ZIP file ledger | FFmpeg入力identityを確定、exact archive対応と最終artifactはnot run | 全fileの取得経路・destination・size・hash・license対応・build-only・除外理由。exact archiveはprovenance limitation |
| license decisions | Python package原文候補とFFmpeg公式参照・ユーザー確認済み方針を記録、G-LICENSE Pass | 公式原本・適用対象・必要対応物・充足方法・確認者・Mxx。最終配置はB4/B5 |
| command records | C09〜C22を実施順に記録 | phase、単独command、最終exit code、失敗 / retry、影響AC |
| findings | U01〜U08を継続、B3実施で新規P1/P2なし | 実施中のFxx、severity、原因の確度、対処と再確認 |
| B3判定 | **Pass** | AC01〜10、G-LICENSE、非阻害provenance limitation、残るUxx、B4入力identity |

### 15.4 B3実施結果（2026-09-14）

#### 実施コマンド

| ID | phase | command / 照合 | 結果 | 終了コード |
| --- | --- | --- | --- | --- |
| MS27-B3-C09 | implementation | `.venv`のdistribution metadata内license / COPYING候補をファイル名検索 | wxPython、matplotlib、NumPy、Whisper、pyopenjtalk、tiktoken、PyInstaller等の原文候補を確認。FFmpeg原文は確認できず | 0 |
| MS27-B3-C10 | implementation | `.\.venv\Scripts\python.exe -B -c`による主要distributionのName / Version / metadata path照会 | direct、transitive、build、PySide6 observed候補の実測値を取得。`mmd-autolip-tool`のinstalled metadata 0.4.0.0は自アプリ旧metadataとして分離 | 0 |
| MS27-B3-C11 | implementation | `.\.venv\Scripts\python.exe -B -m pip check` | `No broken requirements found.` | 0 |
| MS27-B3-C12 | implementation | direct packageのRequires-Dist照会 | marker / extrasを含む依存条件を取得。Linux限定のtriton等をWindows必須へ格上げしていない | 0 |
| MS27-B3-C13 | implementation | 標準ライブラリによるFFmpeg 10実体のsize / SHA-256照会 | 本節の全file identityを取得 | 0 |
| MS27-B3-C14 | implementation | `.\FFmpeg\bin\ffmpeg.exe -version` | `N-123549-g70537ec8e6-20260318`、`--enable-gpl --enable-version3`を確認 | 0 |
| MS27-B3-C15 | implementation | `.\FFmpeg\bin\ffprobe.exe -version` | ffmpegと同じversion / configurationを確認 | 0 |
| MS27-B3-C16 | implementation | `git ls-files FFmpeg/bin` | `.gitkeep`を含む11 entries。10実体がGit追跡対象であることを確認 | 0 |

上表の採用証拠の前に、照会コマンドの組み立てミスによる非ゼロ終了を複数回確認した。これらは環境・対象file・依存関係の失敗ではなく、後続の修正版照会で再取得した。修正版の終了コードと結果だけをPass判定へ使用し、失敗履歴を成功へ書き換えていない。B3ではテスト、compileall、build、GUI、実MMD、runtime data操作、原文取得を実施していない。

#### FFmpeg入力identity

以下はB3実施時点のrepo入力であり、B4のEXE内部やB5のZIP実体ではない。originは`FFmpeg/bin/`、destination予定は現行specの`FFmpeg/`である。

| File | Size (bytes) | SHA-256 | license/source status |
| --- | ---: | --- | --- |
| `ffmpeg.exe` | 542208 | `25F9F739794E20C7EBA08DD2E6C9165F79CA5C6D4423E07E9575DA0EA957E6D5` | selected build; exact origin / text Hold |
| `ffprobe.exe` | 228864 | `29221ACCA37F2BFB30CC17F1F9F219CEE0636383DFE48B4A8292B895AF988980` | selected build; exact origin / text Hold |
| `ffplay.exe` | 17744896 | `EDA12E438A5D509B0BE4D05292D58DB916C9049544A03A49BCF6B7F10A8C20F3` | collected by current spec; use/notice mapping Hold |
| `avcodec-62.dll` | 97590784 | `BE77A6E1872DF4591F090D948CD19FE3A1D0C02EF2642BF8A3307C33898F4E50` | selected build; external component mapping Hold |
| `avdevice-62.dll` | 3683840 | `663A69109279A8A1C49AAA85FF18613C31C0FD9FE9F2DD87371C068B36B20858` | selected build; external component mapping Hold |
| `avfilter-11.dll` | 94227456 | `59A7058E977D70C9B3A126303C44D691562CFF61080E8C89B9CD5D5168B3E847` | selected build; external component mapping Hold |
| `avformat-62.dll` | 22062592 | `4B7E2144962F7851B828169BA162146CE77F99ED3AEBACD10959E6E4E619BD2B` | selected build; external component mapping Hold |
| `avutil-60.dll` | 2930688 | `1B37A5835A1D895FB24A5DD0CAA84231B9EDFB753A76B5231748CE069E656259` | selected build; external component mapping Hold |
| `swresample-6.dll` | 722944 | `C003F7911D0C160C0387D74F54A55BAF40C003405F7B322B46545988C2D76775` | selected build; external component mapping Hold |
| `swscale-9.dll` | 12434432 | `E4089B3487534BAE9D4CAB56D694A738787C69201CB891BDE2DC3D0CC45267F9` | selected build; external component mapping Hold |

FFmpeg / ffprobe reported version `N-123549-g70537ec8e6-20260318`, GCC
`15.2.0`, target `x86_64-w64-mingw32`, and configuration including
`--enable-gpl --enable-version3`, `--enable-shared`, and `--enable-whisper`.
The full command output is represented by C14 / C15; the long configuration is
not shortened into a different configuration value.

#### License and package decisions

| Decision ID | Decision / evidence | State |
| --- | --- | --- |
| MS27-B3-M02 | Direct package metadata and package-provided license paths were mapped in `THIRD_PARTY_LICENSES.md` | observed; final frozen correspondence not run |
| MS27-B3-M03 | `requirements.txt` and observed values for setuptools, fonttools, kiwisolver, packaging, and pillow differ; no update/reinstall was performed | recorded difference; selected build input requires B4 reproducibility review |
| MS27-B3-M04 | Current spec collects the FFmpeg/bin regular files into internal `FFmpeg`, including ffplay and DLLs; no need-based exclusion was introduced | unchanged spec; final internal set not run |
| MS27-B3-M05 | ZIP root required files remain `MMD_AutoLipTool.exe`, `readme_mmdautolip.txt`, `LICENSE`, `NOTICE`, and `THIRD_PARTY_LICENSES.md`; version resource remains build-only | documented candidate; actual ZIP not run |
| MS27-B3-M06 | README, simplified readme, NOTICE, third-party license summary, and package Manifest were synchronized to the B3 status and exact FFmpeg input identity | implemented; release readiness not implied |
| MS27-B3-M07 | FFmpeg revision-pinned upstream `LICENSE.md` reference、公式Downloadページ、取得経路、現行legal方針を記録。exact selected-build `COPYING` placement、distribution archive、corresponding source、external-component mappingはprovenance limitationとして残る | **G-LICENSE Passの前提資料 / U01, U03, U04, U07は非阻害の未確認事項** |
| MS27-B3-M08 | ユーザー確認: 現行FFmpeg versionは変更せず、取得元は取得時点のFFmpeg公式Downloadページ、licenseは現行公式情報を参照し、license revisionとbinary revisionの厳密一致は要求しない | **採用方針 / G-LICENSE Pass** |

#### AC / gate result

| Condition | B3 implementation result |
| --- | --- |
| AC01 | Pass for live baseline, B1/B2 boundary, and fixed `1.0.0`; final EXE remains not run |
| AC02 | Pass for B3 scope: direct/transitive/build/vendored/native/data candidates and declared/observed differences are recorded; final frozen selected set remains B4 evidence |
| AC03 | Pass under the user-confirmed policy: all 10 FFmpeg file hashes, version, configuration, official Download-page acquisition route, and upstream source/legal references are recorded; exact archive/hash correspondence remains a non-gating provenance limitation |
| AC04 | Pass for B3 reference policy: current official FFmpeg license/legal references and repository notice guidance are recorded; final frozen/ZIP placement remains B4/B5 evidence |
| AC05 | Pass for B3 candidate scope: build/internal/ZIP boundaries and required five files are fixed; final artifact and actual additional placement remain B4/B5 evidence |
| AC06 | Pass for the six B3-synchronized documents; no public release completion is claimed |
| AC07 | N/A: no spec change was needed from the evidence available; build-dependent verification remains B4 |
| AC08 | Pass for B3 boundary: PySide6 environment/xref distinction is recorded; final inclusion remains B4 |
| AC09 | Pass for the repository notice and source-archive guidance recorded in `NOTICE`, `README.md`, `readme_mmdautolip.txt`, `THIRD_PARTY_LICENSES.md`, and the Manifest; actual generated source archive remains not run |
| AC10 | Pass for B3 scope: U01/U03/U04/U07 remain as non-gating provenance or later artifact correspondence items, U05/U06/U08 remain later B4/B5 execution items, and no unresolved B3 P1/P2 remains |

**B3 result: Pass.** The documentation, dependency inventory, input hashes,
package boundaries, official FFmpeg references, acquisition route, and the
user-confirmed license policy were recorded. G-LICENSE is Pass without changing
the selected FFmpeg binaries. Exact provider archive/hash correspondence and
the final frozen/ZIP placement remain provenance or later artifact evidence;
they are not silently represented as independently verified. B4 may perform its
own input/path/process gates, but B4, B5, and B6 are not thereby completed.

### 15.5 ネット照合の追加実施結果（2026-09-14）

| ID | phase | command / source | 結果 | 状態 |
| --- | --- | --- | --- | --- |
| MS27-B3-W01 | external research | FFmpeg FATE history | `N-123549-g70537ec8e6`が2026-03-18のupstream revisionとして記録され、local versionのrevision部分と一致 | upstream revision identityを補足 |
| MS27-B3-W02 | external research | `https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/LICENSE.md` | revision固定のFFmpeg `LICENSE.md`原文を一時取得し、LGPL baseline、`--enable-gpl`、`--enable-version3`、external libraryの注意を確認。取得bytesのSHA-256は`2E1D16C72FD74E12063776371DA757322F8B77589386532F4FD8634BDE7DE1AF` | official text referenceを補足。repo / release ZIPへ未配置 |
| MS27-B3-W03 | external research | BtbN `README.md`、`build.sh`、release index / API | `win64`、`gpl-shared`、FFmpeg source clone、date-based `--extra-version`、release retention policyを確認。local signatureとの整合は強いが、exact 2026-03-18 assetは現行保持一覧で特定できず | providerは推論。exact archive identityは非阻害のprovenance limitation |
| MS27-B3-W04 | decision | FFmpeg official legal guidance | distributed binaryに対応するsource、build configuration、license text、external libraryの確認事項を把握。プロジェクトのユーザー確認済み方針ではlicense revisionとbinary revisionの厳密一致を要求しない | G-LICENSE判定方針へ反映 |
| MS27-B3-W05 | user decision | ユーザー確認（2026-09-14） | 現行FFmpeg versionは変更しない。取得元は取得時点のFFmpeg公式Downloadページ。licenseは現行公式情報を参照し、license revisionとbinary revisionの厳密一致は要求しない | **G-LICENSE Pass / exact archive対応は非阻害のprovenance limitation** |

W02の原文は`C:\tmp\ffmpeg-70537ec8e6-LICENSE.md`へ一時保存した。W01〜W04の外部資料、local version/configuration、既存10実体hash、W05のユーザー確認を組み合わせ、公式Downloadページを起点とした取得経路と現行official legal referenceをB3の採用方針として固定する。exact Windows release archive、全external libraryとbinaryの完全な対応、最終ZIPの相対pathは未確認として残すが、license revisionとbinary revisionの厳密一致を要求しないためG-LICENSEはPassとする。最終frozen/ZIPの実配置・同梱はB4/B5で別途確認する。

## 16. B4 / B5 / B6への引継ぎ

| owner | B3から渡すもの | 後続で確認すること / 戻す条件 |
| --- | --- | --- |
| B4 | B1/B2証拠、固定版数、G-LICENSE判定、実環境と宣言差分、build許可一覧・全入力hash、spec変更、内部予定一覧、原文対応 | G-LICENSE Passを開始条件に、隔離source絶対cwd・PythonExe絶対pathでbuild。version resource・埋込み文書・FFmpeg配置を含める。warn / xref / TOCと最終再帰archiveを照合し、新規component・Qt・欠落・weights混入はB3へ戻す |
| B5 | 必須5＋正確なlicense / notice / 必要対応物のZIP相対全file一覧、除外一覧、固定ZIP名、B4から受け取るべきEXE identity | 同一EXE hashから組立・展開し原文も照合。検証起動後のruntimeを再圧縮しない。配布環境のresource、FFmpeg、辞書・tokenizer、モデル未配置、スプラッシュ、通常終了は実証拠を取る |
| B6 | B3 Pass / Hold、AC証拠、全Fxx / Uxx、候補使用値・再現制限、source archive配慮、失効規則、更新文書 | B4/B5実同梱との差分を反映した最終台帳と候補bytesを照合。Index / Roadmap等の古い現在状態はB6で同期。必要本文・対応物不足をreadiness Passへ繰り越さない |

B4のWindows FileVersion / ProductVersion文字列は両方`1.0.0`、固定数値は`(1, 0, 0, 0)`をB2から維持する。アプリ表示だけ一致していても古いinstalled metadataが内部に入っていれば、その値・出所・採用経路を記録する。B2 / B3で未確認のmetadataを無差別削除しない。

## 17. ユーザー確認と完了条件

今回のB3実装では、FFmpegの取得経路・license参照・revision対応に関するユーザー確認を追加で受けた。現行FFmpeg versionは変更せず、公式Downloadページを起点とした取得経路と現行official legal referenceを採用し、license revisionとbinary revisionの厳密一致は要求しない方針を固定した。

B3実施時に、現在資料と既存許可では決められないbinary差替え、依存更新、配布範囲変更、原archiveやライセンス原本の取得・提供方法などが実装結果を左右する場合だけ、対象・根拠・影響・必要入力を明示して具体的に質問する。回答が必要な作業は止め、独立した許可済みの資料確認は継続できる。今回のユーザー確認により、exact archive対応は非阻害のprovenance limitationとして扱う。

- **今回の完了:** B3計画、依存・license台帳、NOTICE、README、簡易説明書、Release Package Manifestを現行観測へ同期し、FFmpeg入力identity、公式参照、取得経路、ユーザー確認済み方針を記録した。G-LICENSEはPassである。
- **B3実施の完了:** AC01〜10とG-LICENSEを充足し、実施台帳・必要な公式参照・関連文書・B4入力一覧が揃った状態。最終frozen/ZIP実体、exact archive hash、Python 3.11 / 3.12互換性は後続確認である。
- 報告後、追加依頼のない実装、後続Block、Git変更、公開へ進まない。
