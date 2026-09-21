# MS27 Block Breakdown

## 1. 文書情報

- 対象: MS27 Ver.1.0 Packaging / Release Readiness Closeout
- 作成日: 2026-09-12
- 対象リポジトリ: `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity`
- 計画作成時ブランチ: `feature/MS27-implementation`
- 計画作成時HEAD: `2151d7bac46069901eed5773fe1bd86f679a1a3d`（`Document MS26 Closeout A`）
- 開始時Git状態: working tree clean。本文書は新規ファイルである。
- 状態: **CloseOut confirmed / B1〜B5は実施済み。B5は候補#08のG-PACKAGE Passまで完了。B6監査報告は完了し、2026-09-18のユーザー受容方針によりrelease readinessはG-READY Pass。同日のユーザー明示決定によりMS27 CloseOutを確定した。公開は未実施。MS26の手動GUI・実MMD結果はユーザー報告として区別する。**
- 前提となるユーザー決定: MS26はCloseOut Aとして扱う。MS27に現在の`0.4.0.0`から正式版数`1.0.0`への版数更新を含める。GitHub Release公開、tag、push、installer新規導入は含めない。
- 今回の書き込み範囲: `docs/Implementation_Plan/MS27_Block_Breakdown.md`だけ。以下の変更・検証・成果物は、MS27実施時の計画であり、今回の実施記録や実行許可ではない。

### 1.1 根拠の扱い

ユーザー決定、現行資料の現在状態、実コード・設定の静的確認、過去の検証記録、今後の計画を区別する。古い検証HEADの成功を、新しいrelease candidateの成功として転用しない。

現行Indexのブランチ欄は、今回の文書同期でlive Gitの`feature/MS27-implementation`へ更新する。MS26 CloseOut Aは機能受入の完了状態として保持し、MS27のpackage / release readinessとは別に扱う。

## 2. 背景と確認した現行資料

MS26は機能統合と実MMD受け入れをCloseOut Aで完了した。Roadmap §14は、その機能基準をonefile build、配布物、依存関係、ライセンスの面から確認する工程をMS27へ分離している。版数は現行`pyproject.toml`とREADMEでなお`0.4.0.0`であり、今回のユーザー決定によりMS27の更新対象となる。

### 2.1 指定資料と事実・未確認の対応

| 資料 | 今回確認した事実 | MS27で確認・確定する事項 |
| --- | --- | --- |
| [MS20 and Beyond Roadmap](../MS20_and_Beyond_Roadmap.md) §13.5 / §14 | §13.5は2026-09-12のMS26 CloseOut A。§14はonefile、SmokeLaunch、配布・license・文書同期・readinessを定義 | 版数更新を加えた具体的な作業と合格証拠 |
| [MS20 and Beyond Index](../MS20_and_Beyond_Index.md) §2 | MS26 CloseOut Aの最終受入記録と、B5 G-PACKAGE Passまでの現在フェーズを記録する。中間のPending / deferred記録も履歴として残る | B6最終照合時のrouting同期。過去記録は改変しない |
| [MS26 Block Breakdown](MS26_Block_Breakdown.md) §1 / §16 / §18末尾 | MS26の最終状態はCloseOut A、MS27 package / release readinessは引き継ぎ事項 | 機能受入とpackage証拠を分けて継承する |
| [Release Package Manifest](../Release_Package_Manifest.md) §3〜§5 / §8〜§9 | 必須5ファイル、sample除外、weights非同梱、FFmpeg / PySide6追加確認を定義。ZIP名は`v0.4.x`の例 | 正確なZIP名、実物一覧、license texts、runtimeデータ除外を確定 |
| [README](../../README.md) | `Ver. 0.4.0.0`、Windows 11、Python 3.11以上、wxPython、onefile手順、weights非同梱を案内 | 正式版数`1.0.0`、配布候補の到達状態・実際の確認環境を同期 |
| [配布用readme](../../readme_mmdautolip.txt) | ZIP展開、通常Python不要、モデルの明示取得を説明。版数履歴は`v0.4.x`と旧版 | 今回の正確な版数と配布構成・初回起動条件を案内。旧版履歴は保持 |
| [pyproject.toml](../../pyproject.toml) | project versionは`0.4.0.0`、`requires-python = ">=3.11"`、直接依存5件、`core = ["whisper_models.json"]` | 版数、実解決依存、metadataとfrozenでのresource利用 |
| [build.ps1](../../build.ps1) | FFmpeg / ffprobe存在確認、PyInstaller起動、exe存在確認、任意のClean / SmokeLaunch | 実行環境、終了コード、出力identity、起動と残留processの実結果 |
| [MMD_AutoLipTool.spec](../../MMD_AutoLipTool.spec) | onefile。`FFmpeg/bin`直下の通常ファイルを`.gitkeep`以外すべて内部`FFmpeg`へ収集。`excludes=[]` | 収集対象の必要性、内部archive、意図しない依存・データ混入 |
| [LICENSE](../../LICENSE) | 本プロジェクトのMIT本文 | 本文・copyright保持と配布内の存在。第三者binaryのライセンスを代替しない |
| [NOTICE](../../NOTICE) | MIT案内、第三者通知、MS17時点のFFmpeg version / GPL・version3記録 | 採用する実binaryと通知を照合 |
| [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md) | major componentsの概要。正確な解決versionと実license textsの最終確認を要求 | 実依存・内部binaryに対応した通知、全文、出所の確定 |

### 2.2 計画の具体化に必要な限定追加確認

- `src/app_version.py`: アプリ版数はinstalled package metadataを優先し、見つからない場合に`pyproject.toml`へfallbackする。単なるTOML更新で実表示も更新されたとは断定できない。
- `src/gui_wx/app.py`: スプラッシュは`format_app_version_display(resolve_app_version())`を描画する。現行表示形式は`Ver. <version>`。
- `tests/test_app_version.py`: 実project versionを`0.4.0.0`と比較する既存テストがある。`0.3.8.0`は別テストのmock値であり、一括置換の対象ではない。
- `requirements.txt`: PyInstaller `6.19.0`、hooks-contrib `2026.3`等を列挙する。これは設定上の値であり、今回の`.venv`の実インストール値は確認していない。
- `FFmpeg/`のファイル名列挙とGit追跡確認: `ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe`、7件のDLL、`.gitkeep`が存在し、追跡されている。列挙した`FFmpeg/`内にはlicense texts / COPYING類がない。他の保存場所や配布元原本は未調査であり、正確な文書がリポジトリ全体に存在しないとまでは断定しない。

### 2.3 履歴として保持する証拠

- MS26の実MMD受入は、MMD Ver 9.32、日本語・Latin、TEXTあり・voice_onlyの4主要ケース、音声・モーフ同期を含む**ユーザー報告**として記録されている。Codexのread-only artifact確認と実MMD操作は同一の証拠ではない。
- MS26に残るPMX hash独立取得不可は補助identityの制限、B2-R05 daemon候補は再現なし・機能影響未観測の非確定観測である。これらをMS27着手時にMS26の未受入へ読み替えない。
- Manifest §9 / NOTICEの`N-123549-g70537ec8e6-20260318`、`--enable-gpl --enable-version3`、PySide6 xref出現は過去の確認記録である。今回binaryを実行して再確認した結果ではない。
- Manifest §8.1の2026-08-28 Whisper assets 4件・weightsなしは静的監査履歴であり、MS27の新しいonefile / ZIP内部の非混入証明ではない。
- 過去文書の「MS27 deferred」は当時のpackage工程未実施を意味する。MS26 CloseOut Aを否定せず、今回MS27計画を作成しただけでrelease readiness達成にもならない。

## 3. 目的

1. MS26 CloseOut Aの機能基準を維持したまま、正式版数`1.0.0`と配布候補identityを固定する。
2. Windows 11向けonefileと実行用ZIPを、内容・起動・依存・licenseの証拠により評価可能にする。
3. 宣言依存、実解決依存、実際の同梱物、通知文書の対応を確認し、不明点をHoldとして追跡する。
4. 同一候補に結び付いたprocess exit codeと手動確認結果から、Pass / Holdのrelease readinessを判定する。

## 4. In Scope

以下はMS27実施時の範囲であり、今回の文書作成では実行しない。

- 正式版数`1.0.0`の表示、ZIP名の確定と必要箇所の更新
- 現行Windows / Python / packaging tool環境、直接・推移依存、package data、DLLの棚卸し
- FFmpeg同梱、実version / configuration、GPL / version3を含む正確なlicense確認
- PyInstaller onefile clean build、SmokeLaunch、warn / xref / TOCと最終exe内部の確認
- 必須ファイルだけを集めたローカル実行用ZIP候補の作成、展開、内容・hash照合
- 開発環境に依存しない配布先での起動、版数、resource、FFmpeg、モデル未配置時の導線確認
- README、配布用readme、package manifest、license通知、変更履歴・状態文書の必要な同期
- 版数・package変更に対応する最小検証、確認済み配布不具合の限定補修と影響再検証の計画
- Pass / Hold判定と、残課題・未検証事項・後続公開工程への引き継ぎ

## 5. Out of Scope

- GitHub Release公開、tag、push、merge、deploy、publish、外部サービスへの書き込み
- 本計画を根拠とするstage、commit、ブランチ操作
- installer、wheel / sdist等の新たな配布方式の導入、実際のGitHub自動生成Source code archive作成・公開
- MS26の実MMD受入の再判定、4ケースの再提出、PMX hash取得を新たなMS27必須条件とすること
- VMD / WAV形式、音声制限、生成品質、モーフ命名、Whisper identity / download契約の再設計
- 旧Qt / PySide6 GUIの復活、包括的なnamespace統一、無関係なUI変更、Ver.1以降の機能追加
- 新規依存、FFmpegの取得元・構成変更、toolchain一括更新を自動採用すること
- Whisper weights、runtime JSON / INI、`models/`、`sample/`、ユーザー素材を配布へ同梱すること
- runtimeの`presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接編集・コピー・fixture化・stage
- 暗黙download、バックグラウンド通信、クラウドASR、音声外部送信
- テスト削除・弱体化・理由のないskipによる合格化

将来のSource code archiveについては、現行Git追跡内容からFFmpegを含む前提を確認し、通知・対応文書の配置を検討する範囲に限定する。Manifestの公開手順は今回の公開許可ではない。

## 6. 前提条件とMS26との境界

- MS26 CloseOut Aを機能受入の基準とする。MS27開始のために再承認を求めない。
- B1でlive HEADとworking treeを確認し、MS26完了基準からの差分を分類する。version / package以外の未評価変更があればその影響を記録する。
- Python `>=3.11`はmetadataの下限である。既存資料のPython 3.14.3開発・受入記録と区別し、今回使うPythonの実path・version・architectureをB1で確認する。Python 3.11 / 3.12の未検証を検証済みへ変更しない。
- 配布先確認はWindows 11の具体的なbuild / architectureを記録する。利用者のPython、開発用`.venv`、repo、PATH上のFFmpeg、既存モデルが偶然不足を補う環境を、独立した配布動作の証明に使わない。
- 版数の決定は済んでいるが各対象への反映結果とライセンスの採否が未確認でも計画作成は完了できる。実施時は未充足ゲートに依存するBlockをHoldとする。
- MS27で新たに配布由来の不具合が見つかった場合、MS27のfindingとする。機能コードや出力契約の変更が必要なら影響と別途必要な修正範囲を示し、該当candidateをHoldにする。MS26の過去のCloseOut Aは書き換えない。
- onefile / ZIPの確認やアプリ内の入出力確認は、MS26の実MMD受入の再実施ではない。ユーザーが今後別途求める実MMD確認は、この計画の必須gateへ自動追加しない。

## 7. 対象ファイルと後続成果物

### 7.1 版数更新の対象

| 対象 | 現在の責務 | B1〜B2で確定・実施する内容 |
| --- | --- | --- |
| `pyproject.toml` | project versionの宣言。specでexeにも同梱 | 正確なversionへ更新。依存値や`requires-python`は版数更新だけで変更しない |
| `README.md` | 冒頭`Ver. 0.4.0.0`と利用・build・配布案内 | `Ver. 1.0.0`、到達状態、配布案内を同期。MS17等の履歴と現在状態を区別 |
| `readme_mmdautolip.txt` | 利用者向け操作・制限・旧version履歴 | 正確な現行versionと今回の履歴を追加・同期。既存`v0.4.x`履歴は保持 |
| `src/app_version.py` | installed metadata優先、TOML fallback | version解決を確認。必要な場合だけ古いmetadata採用等を限定補修する候補 |
| `src/gui_wx/app.py` | スプラッシュ版数表示 | `Ver. <確定version>`のsource / frozen一致を確認。新たな表示機能は必須としない |
| `tests/test_app_version.py` | 現行TOML値・解決順・表示形式の検証 | 実versionの固定期待値を更新。mock値・fallback・解決順の検証を維持 |
| `MMD_AutoLipTool.spec` / `build.ps1` | 固定exe名、resource収集、build / smoke | version付きexeへの改名は予定しない。Windows FileVersion / ProductVersionとも正式版数`1.0.0`を設定する要件は確定済み。実際のspec/version resource反映方法はB2が決めて反映し、B4が最終exeで検証する |
| `docs/Release_Package_Manifest.md` | ZIP名・同梱内容の正本 | 例示`v0.4.x`から今回の正確なZIP名と内容へ同期 |
| `docs/Version_Control.md`、Index / Roadmap / `docs/repo_milestone.md` | 変更・到達状態の記録 | MS27で実施した更新・確認だけを追記。旧versionと過去のdeferredは履歴として保持 |
| build環境の当該project metadata、実exe内metadata | アプリ版数解決へ影響し得る | 存在・versionを確認。古い値が優先される場合の再生成・解決方法はB2の個別計画で限定する |

正式版数`1.0.0`への変更を、JSON schema version、fingerprint、Whisper manifest version、第三者package version、過去の履歴、テストの独立したfixture値へ波及させない。

### 7.2 配布確認・同期対象

- `requirements.txt`、`pyproject.toml`、使用環境のpackage metadata。lockファイルはB1で有無と使用実態を確認し、未確認の固定パスを必須としない。
- `MMD_AutoLipTool.spec`、`build.ps1`、`FFmpeg/bin/`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`。
- `src/core/whisper_models.json`、Whisper / pyopenjtalk / tiktoken等のpackage data、app icon・toolbar・splash resources。B3以降で実在・解決・同梱先を照合する。
- B2の直接テスト、既存のpackage / resource / FFmpeg locator / Whisper no-download / startup関連テスト。正確な対象は各Blockの個別計画で現行構成と変更に対応付ける。
- FFmpeg等の正確なlicense textsの追加先・名前はB3で確定する。存在や名前が未確認のファイルを作成済みとして列挙しない。

### 7.3 後続成果物の保存方針

各Blockの詳細手順と実施記録は、後続作業で作成する`docs/Implementation_Plan/MS27-Bx_Implementation_Plan.md`を候補とする。B1の個別計画内に共通evidence ledgerを設け、B2〜B6は証拠IDで対応付ける。これらは今回作成しない。

B1でbuild / 検証用領域、ログ保存先、ZIP組立先、展開確認先を具体的なローカルpathとして固定する。検証記録は利用者向けZIPへ混入させない。stage / commitを証拠固定の前提とせず、HEADと対象差分・入力hashで追跡する。

## 8. 実装・配布方針と判断ゲート

### 8.1 G-VERSION: 正確な版数文字列の確定

正式版数はユーザー決定により**`1.0.0`に確定済み**である。

B1では、正式版数`1.0.0`をユーザー決定としてversion表へ記録し、既存4要素表記からの更新対象、Windows FileVersion / ProductVersionの設定要件、package metadataでの実値、表示、ZIP命名を対応付ける。B2ではこの確定値を対象箇所へ反映し、spec/version resourceの実装方法を決める。公開準備用のcandidateという呼称によるsuffix追加は行わない。

| 項目 | 確定する値・規則 |
| --- | --- |
| Project version | `1.0.0` |
| アプリ・README表示 | `Ver. 1.0.0`。metadataが異なる表記を返す場合は対応を確認し、意図しない差を残さない |
| 配布用readme | `1.0.0`を現行版として明記 |
| 実行ファイル名 | 現行の`MMD_AutoLipTool.exe`を維持 |
| ZIP名 | `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`。大文字小文字・suffix・配置先まで固定 |
| Windows FileVersion / ProductVersion | 現状specには指定がないが、両方を正式版数`1.0.0`に設定する要件は確定済み。実際のspec/version resource反映方法はB2が決めて反映し、B4が最終exeで検証する。現時点で設定済み・検証済みとは記載しない |

G-VERSIONは、正式値`1.0.0`、FileVersion / ProductVersionを含む更新対象と反映責務がversion表へ記録され、残存旧版表記が「更新対象」「保持する履歴・fixture」「第三者等の別version」に分類された時点で要件固定のPassとする。B2でsource側とversion resourceを反映し、B4〜B5で実exe・展開ZIP側の一致を確認する。

### 8.2 G-LICENSE: 依存・FFmpeg・正確な文書の確定

依存台帳には、component名、役割、宣言version、実解決version、取得元・配布元、同梱file / hash、license名・version、正確な本文・copyright / notice、ZIP内配置、確認根拠、担当Block、未解決事項を記録する。

直接依存の宣言値は`wxPython==4.2.5`、`matplotlib==3.10.8`、`numpy==2.4.3`、`openai-whisper==20250625`、`pyopenjtalk==0.4.1`である。推移依存、Python runtime、native DLL、辞書・データ、PyInstaller bootloader等は、実環境と最終artifactから追加して照合する。宣言一覧だけで同梱物一覧を代替しない。

FFmpegについては次をゲート化する。

1. 採用する`ffmpeg.exe`、`ffprobe.exe`とDLLの実path・SHA-256・version・build configurationを採取する。`ffplay.exe`も現行specでは収集対象であるため、同梱要否とライセンスを明示する。未確認のまま必要とも除外可能とも断定しない。
2. 過去の`N-123549-g70537ec8e6-20260318`と実物の一致・相違を記録する。`--enable-gpl --enable-version3`がある構成をLGPL-onlyと読み替えず、選択binaryに適用されるGPL / version3を含む正確な本文と通知を配布元原本・公式資料で確認する。
3. FFmpeg本体だけでなく、そのbuildが含む外部component、DLL、追加条件を確認する。必要な対応ソース・提供方法・再配布条件等は、選択binaryと正確な一次資料に基づき該当性と満たし方を確定する。一般名やURLだけで充足済みにしない。
4. 確認した本文・通知・必要な対応物を、実行用ZIPから利用者が読める配置としてmanifestへ明記する。exe内部のMIT / NOTICE / 概要文書があることだけを、FFmpegの配布条件充足の証拠にしない。
5. Git追跡中のFFmpegが将来のSource code archiveにも含まれる前提で、関連文書の追跡対象配置・案内に欠落がないかを確認する。実archiveの生成・公開は実施しない。

#### ユーザー確認済みのFFmpeg取扱方針（2026-09-14）

- 現行リポジトリのFFmpeg実体・version・configuration・hashは変更しない。
- 配布元は、取得時点でユーザーがFFmpeg公式Downloadページを起点として取得したものとして記録する。公式ページ自体はsource codeを提供し、Windowsのcompiled buildは外部提供元へのリンクであるため、`ffmpeg.org`が10実体を直接build・配布したとは記録しない。
- licenseの参照は、FFmpeg公式サイトの現行license / legal情報を採用する。これは本リポジトリの配布・記録方針であり、法的助言や特定地域の法的判断を意味しない。
- license revisionとbinary revisionの厳密な一致は、本プロジェクトのG-LICENSE判定条件としない。現行binaryのidentity、公式source / legal参照、取得経路、build configuration、NOTICE案内を対応付ける。
- exact provider archive、archive hash、binaryとsourceの暗号学的な一致は未確認のprovenance limitationとして残す。ただし、上記方針に基づくG-LICENSEの阻害条件からは除外する。

**Hold条件:** 現行binaryのversion / configuration / identity、公式source / legal参照、取得経路、必要なNOTICE案内のいずれかが記録できない、または実測・一次資料が上記方針と矛盾する場合。exact provider archive、archive hash、license revisionとbinary revisionの厳密一致は、ユーザー確認済み方針ではG-LICENSEの必須条件とせず、provenance limitationとして記録する。

本計画はGPLの適用範囲や配布適法性を独自に断定しない。具体的な確認根拠が不足する場合は、その不足と必要な資料を残す。FFmpeg差し替え・依存追加・配布方式変更が解決に必要なら、その実質的な変更は別途明示された範囲で扱う。

### 8.3 G-ARTIFACT: onefile内部とPySide6混入確認

- 現行specは`collect_submodules("matplotlib.backends")`等を使い、`excludes=[]`である。PySide6が解析に現れる可能性と、実際に最終exeへ入ることは別判定とする。
- B4で新しいbuildのwarn / xref、Analysis TOC、最終exeの再帰的なarchive一覧を照合し、必要なら所有する一時展開領域の実DLLも確認する。古いbuildログやZIP外側の5ファイルだけから、内部非混入を判定しない。
- PySide6 / shiboken / Qt関連の実module・DLLがある場合、取り込み経路、必要性、サイズ、正確なversion、license / noticesをB3台帳へ戻す。不要な同梱は限定的な除外候補とし、採用後はwx / matplotlib等の起動・resource回帰を行う。
- 意図しない混入が残る場合、同梱の必要性・licenseが未確定の場合、最終artifactを調べられない場合はHold。必要性と配布条件が明示確認された同梱を許容する場合も、wxPython主系を変えず、根拠と採否を残す。
- 除外指定があるだけで除外成功としない。修正後に作った最終exe内部で確認する。

### 8.4 G-PACKAGE: 必須ファイルと除外ファイル

ZIPの基本構成は、展開先直下に次の必須5ファイルと、G-LICENSEで確定した第三者文書・対応物を置く形とする。

```text
MMD_AutoLipTool.exe
readme_mmdautolip.txt
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
<G-LICENSEで確定したlicense texts / notices等>
```

| 層 | 必須・確認対象 | 除外・注意 |
| --- | --- | --- |
| ZIP外側 | 上記5ファイル、実同梱componentに必要な文書・対応物 | `dist/`全体を無条件に圧縮しない。許可一覧から組み立てる |
| onefile内部 | 実行用modules / DLL、FFmpeg / ffprobeと必要DLL、icon / toolbar / splash、`pyproject.toml`、現行3 license文書 | 内部にもruntime user data、weights、sampleを混入させない |
| Whisper resource | `src/core/whisper_models.json`と必要なWhisper package assets | versioned manifestは同梱する。`small.pt`、`medium.pt`、`large-v3-turbo.pt`等のweightsは同梱しない |
| source / package-data | 現行`core = ["whisper_models.json"]`とfrozen側配置の対応を確認 | 実行用ZIPへの生の開発`src/`コピーとは区別する。installed namespace全体の補修を自動追加しない |

実行用ZIPの除外対象は次とする。各除外はZIP一覧だけでなく、該当するonefile内部にも適用する。

- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`とそのbackup・一時コピー、利用者の最近使ったファイルや絶対pathを含むデータ
- runtimeの`models/`（空directoryも組立対象外）、Whisper model weights、checkpoint、download途中の`.part`
- `sample/`、受入音声・TEXT、PMX / PMD、MMD本体、生成したVMD / WAV / report
- 開発用`src/`、`tests/`、`docs/`、`.git/`、`.venv/`、`.agent/`、`.agents/`、`.codex/`、`AGENTS.md`
- build作業directory、cache / temp、`__pycache__/`、`.pytest_cache/`、`*.pyc`、`*.log`、`*.tmp`、`*.bak`、検証ログ・台帳

生のsource / `*.pyc`除外はZIPへの開発ツリー同梱を禁止する意味であり、onefileが実行に必要とするmodule archiveや`src/core/whisper_models.json`を削除する意味ではない。辞書・tokenizer・通常package dataは由来と用途で分類し、`.bin`等の拡張子だけで必要なデータまで除去しない。

sampleは今回のユーザー指定により除外を固定する。出典調査を理由にMS27で同梱へ変更しない。既存runtimeデータは削除せず、組立対象へ選ばない。展開後の起動でアプリが生成した設定等は検証用directoryに留め、そのdirectoryを再圧縮しない。

## 9. Block分割と詳細ステップ

| Block | 名称・責務 | 依存 | 主な成果物 | 現在状態 |
| --- | --- | --- | --- | --- |
| MS27-B1 | 基準・版数・検証環境gate固定 | MS26 CloseOut A、本計画 | baseline、確定version表（FileVersion / ProductVersion要件を含む）、検証範囲・台帳schema | Passed |
| MS27-B2 | `1.0.0`版数更新・表示整合・version resource実装方法決定 | B1 / G-VERSION Pass | version差分、直接検証、表示経路・version resource実装の対応 | Implemented / Passed |
| MS27-B3 | 依存・license・package manifest確定 | B1、B2のversion表・差分 | 依存台帳、正確なlicense一式、同梱許可・除外一覧 | Implemented / G-LICENSE Pass |
| MS27-B4 | onefile build・SmokeLaunch・内部artifact監査（Windows version resourceを含む） | B1の隔離実行契約Pass、B2完了、B3 / G-LICENSE Pass | exe、build / smoke記録、内部一覧・hash、FileVersion / ProductVersion検証 | Implemented / G-ARTIFACT Pass |
| MS27-B5 | ZIP候補組立・展開・配布環境確認 | B3、B4 / G-ARTIFACT Pass | ZIP候補、内容・hash、配布先確認記録 | Implemented / G-PACKAGE Pass |
| MS27-B6 | 最終照合・文書同期・readiness判定 | B1〜B5の最終証拠 | Pass / Hold記録、残課題、handoff | Implemented / G-READY Pass |

### MS27-B1: 基準・版数・検証環境gate固定

**責務:** ユーザー決定とlive状態を対応付け、後続で判断を再発明しない基準を作る。

1. MS26完了HEAD、実施時HEAD / 差分、branch、既存変更を記録する。
2. 正式版数`1.0.0`と、Windows FileVersion / ProductVersionとも`1.0.0`に設定する要件をG-VERSIONの表へ記録し、B2のspec/version resource実装とB4の最終exe検証の責務を固定する。更新対象・保持する旧版表記・第三者等の別versionも分類する。
3. Windows / Python / PyInstaller / hooks / 依存環境、build入力、FFmpegの所在、作業用領域を記録する。設定値と実インストール値を分離する。
4. 配布用Windows確認環境と独立性、正常終了の取得方法、必要な非配布検証素材、モデル未配置ケース、必要時の既存検証済みモデルの利用方法を決める。
5. 共通evidence ledger、必須検証と条件付き回帰、所有Block、失効規則を固定する。

**成果物:** B1個別計画・baseline記録・version表・環境表・共通台帳。

**受入条件:** 正式版数`1.0.0`とWindows FileVersion / ProductVersionの設定要件がG-VERSIONの表へ固定され、G-VERSIONの要件固定判定がPass。B2がspec/version resourceの実装方法を決めて反映し、B4が最終exeで検証する責務を含め、B2〜B5の対象と保存先、実行者、必須検証が決まっている。未提供環境やlicense資料があれば所有BlockとHoldゲートを示し、後続を実施済みにしない。

**終了コード記録:** 環境・Git・version確認commandを`MS27-B1-Cxx`で記録する。ユーザーの版数決定はprocess実行ではなく`N/A（ユーザー決定）`とする。

### MS27-B2: `1.0.0`版数更新・表示整合

**責務:** 確定versionを現行の版数解決経路と文書へ反映し、Windows FileVersion / ProductVersionのspec/version resource実装方法を決定して反映する。

1. §7.1の変更対象だけを更新する。新versionの宣言、readmeの現行版、ZIP名を一致させる。Windows FileVersion / ProductVersionは正式版数`1.0.0`へ反映し、spec/version resourceの具体的な実装方法を記録する。
2. installed metadata優先とTOML fallbackの双方を確認し、旧metadataが新versionを隠す場合は原因と限定した対処を個別計画へ記録する。無関係なpackage配置やnamespaceは変更しない。
3. 既存`tests/test_app_version.py`の実version期待値を更新し、同テストを実行する。保持すべきmock・fallback検証は維持する。
4. sourceでの解決値と表示形式を記録する。source側GUIの実表示確認が必要なら隔離した設定先を用いる。frozenの実表示はB4〜B5の受入とする。

**成果物:** version関連差分、旧版表記の分類結果、直接テスト・source版数解決の証拠。

**受入条件:** 宣言とsource解決値が`1.0.0`で一致し、直接テストが成功終了する。アプリ・README・配布用readme・ZIP名の対応と、Windows FileVersion / ProductVersionの実装方法がG-VERSIONの確定値と一致する。B2の反映結果はB4の最終exe検証へ引き継ぎ、実exe表示・resource値はB2で検証済みとは記録しない。

**終了コード記録:** `MS27-B2-Cxx`にテスト結果・失敗・skip・process exit codeを記録。実行していないGUI項目へ`0`を記入しない。

### MS27-B3: 依存・license・package manifest確定

**責務:** 宣言・実環境・予定同梱内容・license原本を対応付ける。

1. G-LICENSEの依存台帳を作り、直接依存だけでなく実環境の推移依存・native data / DLLを確認する。
2. 実FFmpeg / ffprobeのversion・configuration・hashを取得し、GPL / version3構成と正確な本文・通知・必要な対応物を確認する。
3. `ffplay.exe`等の収集対象を含むFFmpeg一覧、specのpackage assets、weights / runtime / sample非同梱方針を照合する。
4. README、配布用readme、NOTICE、THIRD_PARTY_LICENSES、Release Package Manifestを予定する候補の事実へ同期し、G-PACKAGEの具体的なfile一覧とlicense配置を固定する。
5. spec / build設定への修正が必要なら理由・変更対象・検証を限定して個別計画に含める。新規依存やbinary差し替えは自動採用しない。

**成果物:** 依存台帳、正確なlicense文書と出所、package許可・除外一覧、関連文書差分、G-LICENSE判定。

**受入条件:** G-LICENSEがPassで、B4が扱うbuild入力が特定されている。license不足時は本BlockとB4以降をHoldにし、不足資料・入手先・必要な判断を具体化する。最終artifactとの一致判定はB4〜B5に残す。

**終了コード記録:** `MS27-B3-Cxx`に依存列挙、FFmpeg確認、hash等を記録。license本文の照合は使用原本・対象binary・判定者を残し、processがない判断は`N/A（文書照合）`とする。

### MS27-B4: onefile build・SmokeLaunch・内部artifact監査

**責務:** 確定した入力からonefileを作り、実出力でbuild・起動・同梱内容とWindows FileVersion / ProductVersionを確認する。

**B4実行契約（開始条件）:** B1で固定した隔離sourceの絶対pathを実行cwdに設定してから、その隔離source内の`.\build.ps1`を呼ぶ。`-PythonExe`には、B1で固定した使用Python実行ファイルの絶対pathを渡す。`build.ps1`およびspecの相対`FFmpeg`、`build`、`dist`、spec入力pathは、この隔離source cwd内に解決される。repo rootの`build`、`dist`、`MMD_AutoLipTool.exe`には触れない。実際の絶対pathはB1実施時に確定する。

1. `-Clean`が削除する`build`、`dist/MMD_AutoLipTool`、`dist/MMD_AutoLipTool.exe`の絶対pathと所有範囲を事前に確認する。既存成果物を破棄してよいと推定せず、B1で固定した隔離領域または明示された対象だけを使う。
2. 現行の`build.ps1 -Clean -SmokeLaunch`を使う一回のbuildを基本とする。実行コマンドと入力hash、Python / PyInstaller、開始・終了、出力hashを記録する。build成功後にsmokeのためだけに同じbuildを重ねない。
3. build wrapperの結果とPyInstallerの結果、SmokeLaunchの生存・停止・残留確認を記録する。現行SmokeLaunchの5秒生存と強制停止は、GUI表示・操作・正常終了の証明ではない。
4. 新しいwarn / xref / TOCと最終exe内部をG-ARTIFACTに従い照合する。FFmpeg / DLL、Whisper manifest・assets、pyproject、icon類、license文書を確認する。
5. source / frozenの版数、Windows FileVersion / ProductVersion、resource path、同梱FFmpegの解決元を照合する。PySide6混入、新たな未通知依存、weights / runtime / sample混入はfindingとしてB3またはB2へ戻す。

**成果物:** `MMD_AutoLipTool.exe`候補、SHA-256 / size、build・smokeログ、内部file一覧、依存台帳との差異、G-ARTIFACT判定。

**受入条件:** B1で固定した隔離sourceの絶対pathを実行cwdに設定し、`-PythonExe`へ使用Python実行ファイルの絶対pathを渡した記録がある。相対`FFmpeg`、`build`、`dist`、spec入力pathが隔離source内へ解決され、repo rootの`build`、`dist`、exeへ触れていない。build / SmokeLaunchのwrapperがprocess exit code `0`、必要な成功結果が存在し、早期終了や対象process残留がない。必須resourcesがあり、最終exeのWindows FileVersion / ProductVersionがともに`1.0.0`であることを確認し、G-ARTIFACTがPass。GUI通常操作・正常終了はB5に残す。

**終了コード記録:** `MS27-B4-Cxx`に実行全体のexit codeを記録する。buildとsmokeが一つのcommandなら、両gateが同じcommand IDを参照する。独立に取得していないexit codeを二つの`0`として作らない。強制停止されたapp子processのcodeとwrapperの成功を区別する。

### MS27-B5: ZIP候補組立・展開・配布環境確認

**責務:** 確認済みexeと確定した付属文書から、利用者に渡す単位を検証する。

1. 空の所有作業領域へG-PACKAGEの許可fileだけを配置し、B4のexe hash、文書・license一式を照合する。
2. G-VERSIONで確定した名前のZIPをローカルに作成し、内容一覧・size・SHA-256を記録する。既存ZIPや利用者directoryの上書きを前提としない。
3. 別の所有directoryへ展開し、ZIPの必須・除外一覧、展開後file hash、B4 exeとの一致を確認する。外側が正しくても内部監査の代替にはしない。
4. B1で定めたWindows 11環境で、起動・スプラッシュ版数・主要画面・resource・license文書の閲覧・通常終了・残留なしを確認する。開発repo / Python / PATH上のFFmpegに依存しない根拠を残す。
5. 同梱FFmpeg / ffprobeの解決と対応音声の読込・変換、pyopenjtalk等のデータ解決を確認する。検証素材・生成物はZIP組立領域へ戻さない。
6. モデル未配置の初回状態で起動・候補表示・案内が成立し、解析が暗黙downloadしないことを確認する。必要なモデルありのfrozen解析は、B1で範囲と素材を固定した検証済みローカルモデルで行い、weightsを候補へ含めない。実download確認は個別に明示された場合だけ扱う。

**成果物:** 実行用ZIP候補、ZIP / 展開後の一覧・hash、配布先環境・操作・結果、G-PACKAGE判定。

**受入条件:** ZIP名と全versionが一致し、必須5ファイルと正確なlicense一式が存在する。全除外対象が非同梱。配布環境で起動・必要resource利用・正常終了が成立する。環境や機能の確認不足が残れば該当gateをHoldとする。MMD自体の操作は要求しない。

**終了コード記録:** `MS27-B5-Cxx`にZIP作成・展開・検査processの結果を記録する。GUIは実施者・操作・期待 / 実結果と、取得したappの通常終了codeを分ける。通常終了codeを取得できなければ未確認とし、SmokeLaunchのcodeで補わない。

**実施状態（2026-09-16）:** 候補#07の過剰なmodule除外を補修後、候補#08で再build、SmokeLaunch、内部監査、ZIP組立・展開・配布実行を行った。EXE SHA-256は`AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、ZIP SHA-256は`D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`。157 filesのhash、通常終了・再起動・残留なし、対象回帰`8 passed, 21 subtests passed`（exit `0`）を確認し、G-PACKAGEをPassとした。スプラッシュ`Ver. 1.0.0`はユーザー目視確認であり、Codex観測と区別する。詳細、観測限界、B6への未確認事項はB5計画§15.4を正本とする。

### MS27-B6: 最終照合・文書同期・readiness判定

**責務:** 最終candidateと証拠・文書・残課題を照合し、公開準備状態を判定する。

1. B1〜B5の必須条件、実行HEAD / 差分、build入力、exe / ZIP hash、各process結果、手動証拠を対応付ける。
2. P1 / P2 / P3、未確認、Hold、既知制限を再分類し、MS26受入とMS27 package判定を分ける。
3. Index / Roadmap / milestone / version-control等を実施状態へ同期する。配布文書はB3までに内容を整え、B6で変更が必要なら§10の失効規則に従う。
4. §12のPass / Holdを記録し、candidateの所在・hash・残課題・後続で必要な判断をhandoffする。公開実績を記入しない。

**成果物:** readiness判定、最終evidence ledger、状態文書差分、残課題・handoff。

**受入条件:** 全判定に証拠が対応し、未実施を合格にしていない。Pass条件を満たす場合のみMS27 readiness完了とする。Holdでも判定報告は完了できるが、MS27を検証済み完了にしない。

**終了コード記録:** `MS27-B6-Cxx`に最終diff / scope等の結果を記録する。readinessの採否そのものは`N/A（証拠に基づく判定）`とし、実コマンドのcodeと混同しない。

**実施状態（2026-09-18）:** 候補#08のEXE / ZIPとB5保存証跡をread-onlyで再照合し、記録済みのEXE SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、ZIP SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`、157 filesを確認した。候補sourceのspecは現HEADと同一bytesである。候補embedded版の`THIRD_PARTY_LICENSES.md`は、B5後の状態追記を含まない候補時点のbytesとして分離した。Python 3.11 / 3.12のsource / build互換性は未検証だが、ユーザー決定によりWindows onefile公開判定から外した。`origin/main`は`2151d7b`を指し、FFmpeg 10 entriesと通知文書を追跡し、候補branchの`FFmpeg/bin`に差分がないことを確認した。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexは法的適合を独自に保証しない。このためB6監査報告は完了、G-READYはPassとする。B6監査後、同日のユーザー明示決定によりMS27 CloseOutを確定した。GitHub Release、tag、push、merge、公開用source archive生成は実施していない。詳細はB6計画§15.2を正本とする。

## 10. 状態遷移・データ契約・証拠失効

```text
MS26 CloseOut A
  → B1 基準・G-VERSION Pass
  → B2 版数整合
  → B3 G-LICENSE Pass / package一覧固定
  → B4 build・SmokeLaunch / G-ARTIFACT Pass
  → B5 ZIP・配布確認 / G-PACKAGE Pass
  → B6 Pass または Hold
```

- 失敗・未取得・不一致は、担当BlockのfindingとHold理由へ戻す。依存しない資料確認は継続できるが、ゲートを省略して候補完成へ進めない。
- 証拠単位は`実行HEAD + 対象差分・入力hash + 実環境 + exe hash + ZIP hash`とする。Git commitを新規作成しない状態でも対象を一意に追跡する。
- pyproject、実コード、依存、FFmpeg、spec、exeへ埋め込むLICENSE / NOTICE / THIRD_PARTY_LICENSES等を変更した場合、影響するB4証拠とそのexeを含むB5証拠をstaleとし、build・内部監査・smoke・ZIP確認を更新する。
- ZIP外側だけのreadme / license配置を変更した場合も、ZIP hashは失効する。B5で再組立・内容照合を行い、exe非変更ならB4の非失効根拠を記録する。
- 非配布の状態文書だけの変更は、candidate bytes不変と検証対象への影響なしを確認して既存証拠を再利用する。理由のない全再実行は行わない。
- 内部分析WAV / MMD用WAV、個別保存 / MMD一括出力、runtime JSON schema、Whisper identity、fingerprintはMS26の受入契約を維持する。duration差`<= 0.05秒`は既存test-only契約であり、MS27で保存時validatorへ追加しない。

## 11. テスト・検証とprocess exit codeの記録方法

### 11.1 実施時の最小入口

以下は**後続Blockで使う候補commandの例**であり、今回実行しない。各commandは単独で実行し、結果・終了を確認してから次を選ぶ。

- B2: `.\.venv\Scripts\python.exe -m pytest tests/test_app_version.py`
- B3: `.\FFmpeg\bin\ffmpeg.exe -version`、別実行で`.\FFmpeg\bin\ffprobe.exe -version`。configuration等に不足があれば採用binaryに対応する追加照会を個別計画で固定する。
- B4（隔離sourceで、以下を別commandとして順番に実行）:
  ```powershell
  Set-Location -LiteralPath <absolute-isolated-source>
  powershell -ExecutionPolicy Bypass -File .\build.ps1 -PythonExe <absolute-python-exe> -Clean -SmokeLaunch
  ```
  実際の絶対pathはB1で確定する。隔離sourceをcwdに設定せず、root相対で`build.ps1`を呼ぶ候補は採用しない。
- 差分確認: `git diff --check`
- 未追跡文書: `git diff --no-index --check -- NUL docs/Implementation_Plan/MS27_Block_Breakdown.md`

B1で確定した実行環境・対象に合わせて具体化し、例示commandのために環境を変更しない。新しいテストは既存検証で証明できない実際の挙動に必要な場合だけ追加する。

full pytest / compileallをMS26再受入のためだけに再実行しない。production / GUI / 依存 / spec等の変更により広い影響がある場合、個別計画に直接回帰・影響回帰・必要なfull pytest / compileallを定めて実行する。必須に決めた検証は省略せず、成功後の追加実行には新たな失敗・変更・未解決リスクを根拠とする。

### 11.2 共通記録様式

各Blockは`MS27-Bn-Cxx`のcommand ID、手動確認は`MS27-Bn-Mxx`、findingは`MS27-Bn-Fxx`を付ける。再試行には新しいIDを付け、元の失敗を消さない。

```text
証拠ID / 所有Block / 対応するgate・受入条件:
実行日時 / 実施者:
HEAD / working tree差分 / 対象入力hash:
OS / Python executable・version / tool versions:
cwd / 単独で実行したcommand:
期待結果 / 実結果 / pass・skip・failure・error件数:
process exit code（未取得・実行中・N/Aはその理由）:
wrapper / 子processの区別 / 正常終了か強制停止か:
ログ・TOC・archive一覧等の所在:
exe / ZIP / 付属fileのpath・size・SHA-256:
判定 Pass・Hold / finding / 次の確認:
再試行元ID / staleにした証拠ID / 非失効の根拠:
```

- process exit codeはrunnerが返す最終終了値を記録する。出力の`passed`や`Build completed`だけで`0`を推定しない。
- 手動PowerShellで取得する場合は、native process終了後、次のnative commandで上書きされる前に`$LASTEXITCODE`を別操作で読み取る。PowerShell関数・cmdletの成功を、直前のnative codeで代用しない。
- build scriptは独立したPowerShell processとして実行し、その最終exit codeを取得する。現行scriptが伝播するPyInstallerの非ゼロ値、例外、SmokeLaunch失敗を記録し、未取得の子process codeは未取得のままにする。
- pass表示でもprocess exit codeが非ゼロなら両方を報告し、その検証gateはHold。起動・残留・内容の条件が不合格なら、wrapperが`0`でもPassにしない。
- SmokeLaunchによる強制停止はその検査手順の一部であり、appの通常終了code `0`の代替証拠ではない。
- 未実行は`not run`、手動の文書照合・ユーザー決定は`N/A（理由）`、process終了未確認は`running / unknown`とする。いずれも便宜的に`0`へ置換しない。
- `rg`の該当なしや`git diff --no-index --check`は一般のテストと終了値の意味が異なる。codeと診断内容を併記し、未追跡文書の後者の`1`は新規差分由来かつwhitespace診断なしの場合に限り正常な検査結果として扱う。
- skipは理由と受入条件への影響を記録する。build、license、最終artifact、配布環境の必須確認をskip扱いで通過させない。

## 12. 受け入れ条件・release readiness判定・完了条件

| ID | MS27の必須条件 | 主担当 |
| --- | --- | --- |
| MS27-AC01 | MS26 CloseOut Aの継承、live基準、証拠境界、G-VERSIONの正式版数`1.0.0`が固定されている | B1 |
| MS27-AC02 | pyproject、アプリ版数解決・表示、README、配布readme、ZIP名、Windows FileVersion / ProductVersionが正式版数`1.0.0`と一致する | B2 / B4 / B5 |
| MS27-AC03 | 宣言・実解決依存・native component・package data・manifest・実同梱物が対応付いている | B3 / B4 |
| MS27-AC04 | FFmpegの実version / build source / configurationと正確なlicense文書・必要な対応物が確認され、G-LICENSEがPass | B3 / B5 |
| MS27-AC05 | B1で固定した隔離sourceを絶対pathで実行cwdに設定し、`-PythonExe`へ絶対pathを渡したうえで、onefile clean buildとSmokeLaunchの結果・最終process exit codeが記録され、相対pathが隔離source内へ解決され、rootのbuild / dist / exeに触れておらず、対象processの残留がない | B4 |
| MS27-AC06 | 最終exe内部まで確認し、PySide6等の未解決な意図しない混入・未通知依存がない | B4 |
| MS27-AC07 | ZIP必須5ファイル・必要なlicense一式があり、weights・runtime JSON / INI・models・sample・開発残骸が非同梱 | B5 |
| MS27-AC08 | 展開した候補が配布環境で起動・必要resource利用・正常終了し、開発環境への偶然の依存がない | B5 |
| MS27-AC09 | 候補bytesと最終証拠・文書が対応し、未解消P1 / P2がない。P3・既知制限の影響が明記されている | B6 |
| MS27-AC10 | MS26の実MMD受入を再判定せず、未実施・未公開・out of scopeを正しく報告している | 全Block / B6 |

### 12.1 判定

| 判定 | 条件 | 意味 |
| --- | --- | --- |
| **Pass** | AC01〜AC10を充足し、必須gateがすべてPass。未解消P1 / P2なし。残るP3があれば配布機能・同梱条件・license・版数の充足に影響しない根拠と扱いを明記 | 特定hashのVer.1.0.0候補について公開準備の技術確認が完了。公開許可・公開済みを意味しない |
| **Hold** | 必須gate未通過、版数の反映不一致、license不足、未確認artifact、非ゼロの必須process結果、配布動作不良、証拠失効、未解消P1 / P2等 | 公開準備完了とは扱わず、担当Block・不足証拠・解除条件・必要な判断を記録 |

MS27ではこのPass / Holdを用い、MS26のCloseOut Aと同じ欄へ混在させない。計画作成時点は未実施・未判定であり、Passや実検証失敗のHoldを先に確定しない。

### 12.2 二つの完了条件

- **今回の文書作成完了:** 指定1ファイルに範囲、現行根拠、Block・依存・成果物・受入条件、検証gate、未確定事項を記載し、内容・whitespace・変更範囲を静的確認した時点。
- **MS27実施の完了:** B1〜B6の必要な作業・証拠・文書同期が揃い、最終candidateでPass条件を満たした時点。Holdの場合は監査報告の完了と、未完了のrelease readinessを区別する。

Pass後もGitHub Release、tag、push、merge、installer導入へ自動移行しない。

## 13. 未確認事項・残課題・リスクと対策

| ID | 計画作成時点の未確定・未確認 | 所有Block / 解除条件 |
| --- | --- | --- |
| MS27-U01 | 正式版数`1.0.0`の各対象への反映結果、実exeのWindows FileVersion / ProductVersion値 | B2: spec/version resourceを含む各対象への反映結果を記録。B4: 最終exeの値を検証。ユーザー決定と設定要件は確定済みだが、反映未実施・最終artifact未確認を保持 |
| MS27-U02 | 現行`.venv`の実Python / PyInstaller / hooks / 推移依存、使用lockの有無 | B1 / B3: 実環境・宣言値・build入力を記録 |
| MS27-U03 | 実FFmpegのversion / configuration再確認、正確なlicense原本、配布元・必要な対応物 | B3: 過去記録から推測せずG-LICENSEを充足。不足時Hold |
| MS27-U04 | `ffplay.exe`と各DLLの必要性、実同梱量、通知範囲 | B3 / B4: 現行の全file収集と最終artifactを照合 |
| MS27-U05 | PySide6 / Qt / shibokenが新しい最終exeに入るか | B4: 新しい解析資料と最終内部archiveを確認。意図・必要性・license未確定ならHold |
| MS27-U06 | Whisper manifest / package assets、辞書等、版数resourceのfrozen解決とweights等の非混入 | B4 / B5: 内部一覧、実resource利用、初回モデル未配置確認 |
| MS27-U07 | build / SmokeLaunchの成功、通常GUI終了、ZIP内容、配布環境での動作 | B4 / B5: 実process・手動結果・hashを取得。今回未実行 |
| MS27-U08 | 古いinstalled metadataがアプリ表示に影響するか、README / manifest等の現行版同期 | B2 / B6: 解決経路と最終表示を照合。旧履歴は保持 |
| MS27-U09 | 将来のSource code archiveに必要なFFmpeg通知の追跡対象配置 | B3 / B6: 現行Git追跡を基に文書配置を確認。実archive生成・公開は対象外 |
| MS27-U10 | B4実行時の隔離source cwd、`-PythonExe`絶対path、相対path解決、repo root非接触の実行証拠 | B1: 実行契約と絶対pathを固定。B4: 実cwd、command、path解決、root非接触、process exit codeを記録。未確認のままB4を開始しない |

MS24に由来するinstalled `core` / `src.core` namespace課題は、onefile実行経路に影響するかをB3〜B5で区別する。wheel / installed package全体の修復を、現行onefileの検証と無関係に必須化しない。実際のfrozen起動を阻害する場合は具体的なfailureとしてHoldにする。

主なリスクは、過去の静的監査を最終artifact検証へ格上げすること、概要licenseを正確な本文と同一視すること、SmokeLaunchを通常終了確認とみなすこと、検証で作られたruntimeデータをZIPへ戻すこと、B6文書更新後に古いexe / ZIPを採用することである。§8〜§11の実物照合、隔離組立、証拠失効規則で扱う。

## 14. Codex実施時の注意と今回の作業境界

- メインエージェントが範囲・結果・最終判定を追跡する。本文書はサブエージェント起動の許可を含まない。
- commandは1つずつ実行し、結果を確認してから次を選ぶ。パイプライン・連結・並列シェル実行を行わない。
- 後続の個別計画で、実行するBlock、対象file、変更権限、検証・成果物pathを具体化する。今回の計画依頼から実装・成果物作成へ移行しない。
- runtime user dataや外部素材を直接編集・コピー・削除せず、必要な起動・テストは隔離先とmanaged persistenceで扱う。
- 依存追加、binary差し替え、破壊的削除、公開等の範囲変更が必要なら、その具体的な理由・対象・影響を示す。許可済みの範囲内作業には同じ許可を再要求しない。
- 正確なlicense・version・artifact証拠がない箇所を推測で埋めない。確認済み、ユーザー報告、計画、未実行、Hold、out of scopeを分ける。
- 今回は本文書以外を変更せず、build、SmokeLaunch、pytest、compileall、exe / ZIP / その他検証成果物の生成を行わない。
- 今回はstage、commit、push、merge、tag、releaseを行わない。
- 完了報告は、作成file、Block一覧、未確定点、静的確認結果、実行していない操作を示して終了する。
